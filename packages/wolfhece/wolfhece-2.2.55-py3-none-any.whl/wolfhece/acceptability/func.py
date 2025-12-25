"""
Author: University of Liege, HECE, LEMA
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from ..wolf_vrt import create_vrt_from_diverged_files_first_based, translate_vrt2tif
from ..wolf_array import WolfArray
from typing import Union, Literal
from ..PyVertexvectors import Zones, zone, vector, wolfvertex, getIfromRGB
from ..PyTranslate import _
from ..scenario. config_manager import Config_Manager_2D_GPU
import subprocess
import geopandas as gpd

import pandas as pd
import numpy as np
from osgeo import gdal, ogr, osr, gdalconst
import os
import glob
from pathlib import Path
import logging
from tqdm import tqdm
from pyogrio import list_layers, read_dataframe
from enum import Enum
import numba as nb
import shutil


ENGINE = 'pyogrio' # or 'Fiona -- Pyogrio is faster
EXTENT = '.gpkg'
class Modif_Type(Enum):
    """
    Enum class for the type of modification
    """

    WALOUS = 'Walous layers changed to PICC buidings'
    POINT2POLY_EPURATION = 'Change BDREF based on AJOUT_PDET sent by Perrine (SPI)'
    POINT2POLY_PICC = 'Convert the points to polygons based on PICC'
    POINT2POLY_CAPAPICC = 'Convert the points to polygons based on PICC and CaPa'
    INHABITED = 'Select only inhabited buildings'
    ROAD = 'Create a buffer around the roads'
    COPY = 'Copy the data'

class GPU_2D_file_extensions(Enum):
    TIF  = '.tif'  # raster
    TIFF = '.tiff' # raster
    PY   = '.py'   # python script
    NPY  = '.npy'  # numpy array
    BIN  = '.bin'  # WOLF binary file
    JSON = '.json' # json file
    TXT  = '.txt'  # hydrographs


class Vulnerability_csv():

    def __init__(self, file:Path) -> None:
        self.file = file
        self.data = pd.read_csv(file, sep=",", encoding='latin-1')

    def get_layers(self) -> list:
        return [a[1] for a in self.data["Path"].str.split('/')]

    def get_vulnerability_level(self, layer:str) -> str:
        idx = self.get_layers().index(layer)
        return self.data.iloc[idx]["Vulne"]

    def get_vulnerability_code(self, layer:str) -> str:
        idx = self.get_layers().index(layer)
        return self.data.iloc[idx]["Code"]


def get_data_type(fname:Path):

    fname = Path(fname)
    """ Get the data type of the input file from extension """
    if fname.name.endswith('.gpkg'):
        return 'GPKG'
    elif fname.name.endswith('.shp'):
        return 'ESRI Shapefile'
    elif fname.name.endswith('.gdb'):
        return 'OpenfileGDB'
    else:
        return None

def cleaning_directory(dir:Path):
    """ Cleaning the directory """

    logging.info("Cleaning the directory {}".format(dir))

    files_in_output = list(dir.iterdir())
    for item in files_in_output:
        if item.is_file():
            os.remove(item)

def empty_folder(folder):
    """
    Empties the content of a directory if it exists.
    """
    if os.path.exists(folder):
        for files in os.listdir(folder):
            fn = os.path.join(folder, files)
            try:
                if os.path.isfile(fn) or os.path.islink(fn):
                    os.unlink(fn)
                elif os.path.isdir(fn):
                    shutil.rmtree(fn)
            except Exception as e:
                print(f"Error when deleting file {fn}: {e}")
    else:
        print("The folder does not exist.")

class Accept_Manager():
    """
    Structure to store the directories and names of the files.

    In the main directory, the following directories are mandatory/created:
        - INPUT : filled by the user - contains the input data
        - TEMP  : created by the script - contains the temporary data for the study area
        - OUTPUT: created by the script - contains the output data for each scenario of the study area

    The INPUT directory contains the following subdirectories:
        - DATABASE: contains the data for the **entire Walloon region**
            - Cadastre_Walloon.gpkg: the Cadastre Walloon file
            - GT_Resilence_dataRisques202010.gdb: the original gdb file from SPW - GT Resilience
            - PICC-vDIFF.gdb: the PICC Walloon file
            - CE_IGN_TOP10V: the IGN top10v shapefile
        - EPU_STATIONS_NEW:
            - AJOUT_PDET_EPU_DG03_STATIONS.shp: the EPU stations shapefile
        - STUDY_AREA: contains the study area shapefiles - one for each study area - e.g. Bassin_Vesdre.shp
        - CSVs: contains the CSV files
            - Intermediate.csv: contains the matrices data for the acceptability computation
            # - Ponderation.csv: contains the ponderation data for the acceptability computation
            - Vulnerability.csv: contains the mapping between layers and vulnerability levels - a code value is also provided
        - WATER_DEPTH: contains the water depth data for each scenario
            - Study_area1:
                - Scenario1
                - Scenario2
                -...
                - ScenarioN
            - Study_area2:
                - Scenario1
                - Scenario2
                -...
                - ScenarioN
            -...
            - Study_areaN:
                - Scenario1
                - Scenario2
                -...
                - ScenarioN

    The TEMP directory contains the following subdirectories:
        - DATABASES: contains the temporary data each study area
            - Study_area1:
                - database.gpkg: the clipped database
                - CaPa.gpkg: the clipped Cadastre Walloon file
                - PICC.gpkg: the clipped PICC Walloon file
                - CE_IGN_TOP10V.tiff: the IGN top10v raster file
                - Maske_River_extent.tiff: the river extent raster file from IGN
                - VULNERABILITY: the vulnerability data
                    - RASTERS:
                        - Code  : one file for each layer
                        - Vulne : one file for each layer
                    - Scenario1:

    """

    def __init__(self,
                 main_dir:str = 'Data',
                 Study_area = None,
                 scenario = None,
                 Original_gdb:str = 'GT_Resilence_dataRisques202010.gdb',
                 CaPa_Walloon:str = 'Cadastre_Walloon.gpkg',
                 PICC_Walloon:str = 'PICC_vDIFF.gdb',
                 CE_IGN_top10v:str = 'CE_IGN_TOP10V/CE_IGN_TOP10V.shp',
                 EPU_Stations:str = 'AJOUT_PDET_EPU_DG03_STATIONS.shp',
                 Ponderation_csv:str = 'Ponderation.csv',
                 Vuln_csv:str = 'Vulnerability.csv',
                 Intermediate_csv:str = 'Intermediate.csv'
                                                         ) -> None:

        self.old_dir:Path    = Path(os.getcwd())

        self.main_dir:Path   = Path(main_dir)

        # If it is a string, concatenate it with the current directory
        if not self.main_dir.is_absolute():
            self.main_dir = Path(os.getcwd()) / self.main_dir
        self._study_area = Study_area
        if Study_area is not None:
            if not str(self._study_area).endswith('.shp'):
                self._study_area += '.shp'

        self._scenario = scenario
        self._original_gdb = Original_gdb
        self._capa_walloon = CaPa_Walloon
        self._picc_walloon = PICC_Walloon
        self._ce_ign_top10v = CE_IGN_top10v

        self.IN_DIR         = self.main_dir / "INPUT"
        self.IN_CH_VULN     = self.IN_DIR / "CHANGE_VULNE"
        self.IN_DATABASE    = self.IN_DIR / "DATABASE"
        self.IN_STUDY_AREA  = self.IN_DIR / "STUDY_AREA"
        self.IN_CSV         = self.IN_DIR / "CSVs"
        self.IN_WATER_DEPTH = self.IN_DIR / "WATER_DEPTH"
        self.IN_EPU_STATIONS= self.IN_DIR / "EPU_STATIONS_NEW"
        self.IN_SA_INTERP   = None

        self.ORIGINAL_GDB   = self.IN_DATABASE / self._original_gdb
        self.CAPA_WALLOON   = self.IN_DATABASE / self._capa_walloon
        self.PICC_WALLOON   = self.IN_DATABASE / self._picc_walloon
        self.CE_IGN_TOP10V  = self.IN_DATABASE / self._ce_ign_top10v
        self.EPU_STATIONS   = self.IN_EPU_STATIONS / EPU_Stations

        self.VULNERABILITY_CSV = self.IN_CSV / Vuln_csv
        self.POINTS_CSV        = self.IN_CSV / Intermediate_csv
        self.PONDERATION_CSV   = self.IN_CSV / Ponderation_csv

        self._CSVs = [self.VULNERABILITY_CSV, self.POINTS_CSV]
        self._GPKGs= [self.CAPA_WALLOON, self.PICC_WALLOON]
        self._GDBs = [self.ORIGINAL_GDB]
        self._SHPs = [self.CE_IGN_TOP10V, self.EPU_STATIONS]
        self._ALLS = self._CSVs + self._GPKGs + self._GDBs + self._SHPs

        self.TMP_DIR            = self.main_dir / "TEMP"

        self.OUT_DIR        = self.main_dir / "OUTPUT"

        self.points2polys = []
        self.lines2polys = []

        self.create_paths()
        self.create_paths_scenario()

    def create_paths(self):
        """ Create the paths for the directories and files """

        self.points2polys = []
        self.lines2polys = []

        if self._study_area is not None:

            self.Study_area:Path = Path(self._study_area)

            self.TMP_STUDYAREA      = self.TMP_DIR / self.Study_area.stem
            self.TMP_DATABASE       = self.TMP_STUDYAREA / "DATABASES"

            self.TMP_CLIPGDB        = self.TMP_DATABASE / "CLIP_GDB"
            self.TMP_CADASTER       = self.TMP_DATABASE / "CLIP_CADASTER"
            self.TMP_PICC           = self.TMP_DATABASE / "CLIP_PICC"
            self.TMP_IGNCE          = self.TMP_DATABASE / "CLIP_IGN_CE"
            self.TMP_WMODIF         = self.TMP_DATABASE / "WITH_MODIF"
            self.TMP_CODEVULNE      = self.TMP_DATABASE / "CODE_VULNE"

            self.TMP_VULN_DIR       = self.TMP_STUDYAREA / "VULNERABILITY"
            self.TMP_SA_SC          = self.TMP_VULN_DIR / str(self._scenario)


            self.TMP_RASTERS        = self.TMP_VULN_DIR / "RASTERS"
            self.TMP_RASTERS_CODE   = self.TMP_RASTERS / "Code"
            self.TMP_RASTERS_VULNE  = self.TMP_RASTERS / "Vulne"

            self.OUT_STUDY_AREA = self.OUT_DIR / self.Study_area.stem

            self.SA                 = self.IN_STUDY_AREA / self.Study_area
            self.SA_MASKED_RIVER    = self.TMP_IGNCE / "CE_IGN_TOP10V.tiff"
            self.SA_VULN            = self.TMP_VULN_DIR / "Vulnerability.tiff"
            self.SA_CODE            = self.TMP_VULN_DIR / "Vulnerability_Code.tiff"

        else:
            self.Study_area = None
            self._scenario = None

            self.TMP_STUDYAREA      = None
            self.TMP_DATABASE       = None
            self.TMP_CADASTER       = None
            self.TMP_PICC           = None
            self.TMP_IGNCE          = None
            self.TMP_WMODIF         = None
            self.TMP_CODEVULNE      = None
            self.TMP_VULN_DIR       = None
            self.TMP_RASTERS        = None
            self.TMP_RASTERS_CODE   = None
            self.TMP_RASTERS_VULNE  = None

            self.OUT_STUDY_AREA = None

            self.SA          = None
            self.SA_MASKED_RIVER = None

            self.SA_VULN    = None
            self.SA_CODE    = None

        self.create_paths_scenario()

        self.check_inputs()
        self.check_temporary()
        self.check_outputs()

    def create_paths_scenario(self):

        if self._scenario is not None:

            self.scenario:str       = str(self._scenario)


            self.IN_SA_BASE         = self.IN_WATER_DEPTH / self.SA.stem / "Scenario_baseline"
            self.IN_SA_BASE_INTERP  = self.IN_SA_BASE / "INTERP_WD"

            self.IN_SCEN_DIR        = self.IN_WATER_DEPTH / self.SA.stem / self.scenario
            self.IN_SA_INTERP       = self.IN_SCEN_DIR / "INTERP_WD"
            self.IN_SA_EXTRACTED    = self.IN_SCEN_DIR / "EXTRACTED_LAST_STEP_WD"
            self.IN_SA_DEM          = self.IN_SCEN_DIR / "DEM_FILES"
            self.IN_CH_SA_SC        = self.IN_CH_VULN /self.SA.stem  / self.scenario
            self.IN_CH_SA_SC_MNT_VRT = self.IN_CH_SA_SC / "__MNT_assembly.vrt"
            self.IN_CH_SA_SC_MNT_tif = self.IN_CH_SA_SC / "MNTassembly"

            self.IN_RM_BUILD_DIR    = self.IN_SCEN_DIR / "REMOVED_BUILDINGS"

            self.TMP_SCEN_DIR       = self.TMP_VULN_DIR / self.scenario
            self.TMP_RM_BUILD_DIR   = self.TMP_SCEN_DIR / "REMOVED_BUILDINGS"
            self.TMP_QFILES         = self.TMP_SCEN_DIR / "Q_FILES"

            self.TMP_VULN           = self.TMP_SCEN_DIR / "Vulnerability_baseline.tiff"
            self.TMP_CODE           = self.TMP_SCEN_DIR / "Vulnerability_Code_baseline.tiff"

            self.OUT_SCEN_DIR       = self.OUT_STUDY_AREA / self.scenario

            self.OUT_WITHVULN       = self.OUT_SCEN_DIR / "vuln_ scenarios"
            self.OUT_VULN_VRT       = self.OUT_WITHVULN / "__vuln_assembly.vrt"
            self.OUT_VULN_S         = self.OUT_WITHVULN / "Vulnerability_scenarios"
            self.OUT_VULN_Stif      = self.OUT_WITHVULN / "Vulnerability_scenarios.tif"
            self.OUT_MASKED_RIVER_S = self.OUT_WITHVULN / "Masked_River_extent_scenarios.tiff"
            self.OUT_ACCEPT_Stif           = self.OUT_WITHVULN / "Acceptability_scenarios.tiff"
            self.OUT_ACCEPT_RESAMP_Stif    = self.OUT_WITHVULN / "Acceptability_scenarios_resampled.tiff"

            self.OUT_BASELINE       = self.OUT_SCEN_DIR / "baseline"
            self.OUT_VULN           = self.OUT_BASELINE / "Vulnerability_baseline.tiff"
            self.OUT_CODE           = self.OUT_BASELINE / "Vulnerability_Code_baseline.tiff"
            self.OUT_MASKED_RIVER   = self.OUT_BASELINE / "Masked_River_extent_baseline.tiff"
            self.OUT_ACCEPT         = self.OUT_BASELINE / "Acceptability_baseline.tiff"
            self.OUT_ACCEPT_RESAMP  = self.OUT_BASELINE / "Acceptability_baseline_resampled.tiff"

        else:
            self.scenario = None

            self.IN_SCEN_DIR       = None
            self.IN_RM_BUILD_DIR   = None

            self.TMP_SCEN_DIR      = None
            self.TMP_RM_BUILD_DIR  = None
            self.TMP_QFILES        = None

            self.TMP_VULN          = None
            self.TMP_CODE          = None

            self.OUT_SCEN_DIR       = None
            self.OUT_WITHVULN       = None
            self.OUT_VULN_VRT       = None
            self.OUT_VULN_S         = None
            self.OUT_VULN_Stif      = None
            self.OUT_MASKED_RIVER_S = None
            self.OUT_ACCEPT_Stif      = None
            self.OUT_ACCEPT_RESAMP_Stif  = None
            self.OUT_BASELINE       = None
            self.OUT_VULN           = None
            self.OUT_CODE           = None
            self.OUT_MASKED_RIVER   = None
            self.OUT_ACCEPT         = None
            self.OUT_ACCEPT_RESAMP  = None

    @property
    def is_valid_inputs(self) -> bool:
        return self.check_inputs()

    @property
    def is_valid_study_area(self) -> bool:
        return self.SA.exists()

    @property
    def is_valid_vulnerability_csv(self) -> bool:
        return self.VULNERABILITY_CSV.exists()

    @property
    def is_valid_points_csv(self) -> bool:
        return self.POINTS_CSV.exists()

    @property
    def is_valid_ponderation_csv(self) -> bool:
        return self.PONDERATION_CSV.exists()

    def check_files(self) -> str:
        """ Check the files in the directories """

        files = ""
        for a in self._ALLS:
            if not a.exists():
                files += str(a) + "\n"

        return files

    def change_studyarea(self, Study_area:str = None) -> None:

        if Study_area is None:
            self._study_area = None
            self._scenario = None
        else:
            if Study_area in self.get_list_studyareas(with_suffix=True) or Study_area+".shp" in self.get_list_studyareas(with_suffix=True):
                self._study_area = Path(Study_area)
            else:
                logging.error(_("The study area does not exist in the study area directory"))

        self.create_paths()

    def change_scenario(self, scenario:str) -> None:

        if scenario in self.get_list_scenarios():
            self._scenario = scenario
            self.create_paths_scenario()
            self.check_temporary()
            self.check_outputs()
        else:
            logging.error(_("The scenario does not exist in the water depth directory"))

    def get_files_in_rm_buildings(self) -> list[Path]:
        return [Path(a) for a in glob.glob(str(self.IN_RM_BUILD_DIR / ("*"+ EXTENT)))]

    def get_files_in_CHANGE_VULNE(self) -> list[Path]:
        return [Path(a) for a in glob.glob(str(self.IN_CH_VULN / "*.tiff"))]

    def get_files_in_rasters_vulne(self) -> list[Path]:
        return [Path(a) for a in glob.glob(str(self.TMP_RASTERS_VULNE / "*.tiff"))]

    def get_layers_in_gdb(self) -> list[str]:
        return [a[0] for a in list_layers(str(self.ORIGINAL_GDB))]

    def get_layer_types_in_gdb(self) -> list[str]:
        return [a[1] for a in list_layers(str(self.ORIGINAL_GDB))]

    def get_layers_in_clipgdb(self) -> list[str]:
        return [Path(a).stem for a in glob.glob(str(self.TMP_CLIPGDB / ("*"+ EXTENT)))]

    def get_layers_in_wmodif(self) -> list[str]:
        return [Path(a).stem for a in glob.glob(str(self.TMP_WMODIF / ("*"+ EXTENT)))]

    def get_layers_in_codevulne(self) -> list[str]:
        return [Path(a).stem for a in glob.glob(str(self.TMP_CODEVULNE / ("*"+ EXTENT)))]

    def get_files_in_rasters_code(self) -> list[Path]:
        return [Path(a) for a in glob.glob(str(self.TMP_RASTERS_CODE / "*.tiff"))]

    def get_q_files(self) -> list[Path]:
        return [Path(a) for a in glob.glob(str(self.TMP_QFILES / "*.tif"))]

    def get_list_scenarios(self) -> list[str]:

        list_sc = [Path(a).stem for a in glob.glob(str(self.IN_WATER_DEPTH / self.SA.stem / "Scenario*"))]
        return list_sc

    def get_list_studyareas(self, with_suffix:bool = False) -> list[str]:

        if with_suffix:
            return [Path(a).name for a in glob.glob(str(self.IN_STUDY_AREA / "*.shp"))]
        else:
            return [Path(a).stem for a in glob.glob(str(self.IN_STUDY_AREA / "*.shp"))]

    def get_sims_files_for_scenario(self) -> list[Path]:
        files = [] #to avoid NoneType
        if self.IN_SA_INTERP.exists() :
            files = [Path(a) for a in glob.glob(str(self.IN_SA_INTERP / "*.tif"))]
        else :
            logging.error(_("No such scenario"))
        return files

    def get_sims_files_for_baseline(self) -> list[Path]:
        files = [] #to avoid NoneType
        if self.IN_SA_BASE_INTERP.exists() :
            logging.info("Getting the _baseline interpolated free surfaces files.")
            track = Path(str(self.IN_SA_BASE_INTERP / "*.tif"))
            files = [Path(a) for a in glob.glob(str(track))]
        else :
            logging.error(_("No _baseline interpolated free surfaces files"))

        return files

    def get_sim_file_for_return_period(self, return_period:int) -> Path:

        sims = self.get_sims_files_for_scenario()

        if len(sims)==0:
            logging.info("No simulations found at this stage")
            return None

        if "_h.tif" in sims[0].name:
            for cursim in sims:
                if cursim.stem.find("_T{}_".format(return_period)) != -1  or cursim.stem.find("_Q{}_".format(return_period))  != -1:
                    return cursim
        else:
            for cursim in sims:
                if cursim.stem.find("T{}".format(return_period)) != -1 or cursim.stem.find("Q{}".format(return_period))  != -1:
                    return cursim
        return None

    def get_types_in_file(self, file:str) -> list[str]:
        """ Get the types of the geometries in the Shape file """

        return [a[1] for a in list_layers(str(file))]

    def is_type_unique(self, file:str) -> bool:
        """ Check if the file contains only one type of geometry """

        types = self.get_types_in_file(file)
        return len(types) == 1

    def is_polygons(self, set2test:set) -> bool:
        """ Check if the set contains only polygons """

        set2test = list(set2test)
        firstone = set2test[0]
        if 'Polygon' in firstone:
            for curtype in set2test:
                if 'Polygon' not in curtype:
                    return False
            return True
        else:
            return False

    def is_same_types(self, file:str) -> tuple[bool, str]:
        """ Check if the file contains only the same type of geometry """

        types = self.get_types_in_file(file)

        if len(types) == 1:
            if 'Point' in types[0]:
                return True, 'Point'
            elif 'Polygon' in types[0]:
                return True, 'Polygon'
            elif 'LineString' in types[0]:
                return True, 'LineString'
            else:
                raise ValueError(f"The type of geometry {types[0]} is not recognized")
        else:
            firstone = types[0]
            if 'Point' in firstone:
                for curtype in types:
                    if 'Point' not in curtype:
                        return False, None
                return True, 'Point'

            elif 'Polygon' in firstone:
                for curtype in types:
                    if 'Polygon' not in curtype:
                        return False, None

                return True, 'Polygon'

            elif 'LineString' in firstone:
                for curtype in types:
                    if 'LineString' not in curtype:
                        return False, None

                return True, 'LineString'
            else:
                raise ValueError(f"The type of geometry {firstone} is not recognized")


    def get_return_periods(self) -> list[int]:
        """
        Get the return periods from the simulations

        :return list[int]: the **sorted list** of return periods
        """

        # List files in directory
        sims = self.get_sims_files_for_scenario()
        sims_modif = [
            os.path.join(os.path.dirname(path), os.path.basename(path).replace("Q", "T").split('_')[0])
            for path in sims
            ]

        if len(sims)==0:
            logging.info("No simulations found at this stage.")
            return []

        # - Return periods are named as T2.tif, T5.tif, T10.tif, ... or with Q instead of T
        # searching for the position of the return period in the name
        idx_T = [Path(cursim).name.find("T") for cursim in sims_modif]
        idx_h = [Path(cursim).name.find(".tif") for cursim in sims_modif]

        # create the list of return periods -- only the numeric part
        sims = [int(Path(cursim).stem[1:]) for i, cursim in enumerate(sims_modif)]
        return sorted(sims)

    def get_modifiedrasters(self, name:str):
        """Returns the name_ files (either vuln_ or MNTmodifs_) in CHANGE_VULNE to analyse later on the type."""
        folder = Path(self.IN_CH_SA_SC) #common folder
        name_paths = [file for file in folder.rglob("*.tif*") if file.name.startswith(name)]
        return name_paths

    def get_ponderations(self) -> pd.DataFrame:
        """ Get the ponderation data from available simulations """
        rt = self.get_return_periods()

        if len(rt)==0:
            logging.info("No simulations found at this stage.")
            return None

        if len(rt)<2:
            logging.info("There is only one simulation! Weigthing coefficient is unique and set to 1.")
            return pd.DataFrame(1, columns=["Ponderation"], index=rt)

        else :
            pond = []

            pond.append(1./float(rt[0]) + (1./float(rt[0]) - 1./float(rt[1]))/2.)
            for i in range(1, len(rt)-1):
                # Full formula
                # pond.append((1./float(rt[i-1]) - 1./float(rt[i]))/2. + (1./float(rt[i]) - 1./float(rt[i+1]))/2.)
                # More compact formula
                pond.append((1./float(rt[i-1]) - 1./float(rt[i+1]))/2.)
            pond.append(1./float(rt[-1]) + (1./float(rt[-2]) - 1./float(rt[-1]))/2.)

            return pd.DataFrame(pond, columns=["Ponderation"], index=rt)

    def get_filepath_for_return_period(self, return_period:int) -> Path:

        return self.get_sim_file_for_return_period(return_period)

    def change_dir(self) -> None:
        os.chdir(self.main_dir)
        logging.info("Current directory: %s", os.getcwd())

    def restore_dir(self) -> None:
        os.chdir(self.old_dir)
        logging.info("Current directory: %s", os.getcwd())

    def check_inputs(self) -> bool:
        """
        Check if the input directories exist.

        Inputs can not be created automatically. The user must provide them.
        """

        err = False
        if not self.IN_DATABASE.exists():
            logging.error(_("INPUT : The database directory does not exist"))
            err = True

        if not self.IN_STUDY_AREA.exists():
            logging.error(_("INPUT : The study area directory does not exist"))
            err = True

        if not self.IN_CSV.exists():
            logging.error(_("INPUT : The CSV directory does not exist"))
            err = True

        if not self.IN_WATER_DEPTH.exists():
            logging.error(_("INPUT : The water depth directory does not exist"))
            err = True

        if not self.IN_EPU_STATIONS.exists():
            logging.error(_("INPUT : The EPU stations directory does not exist"))
            err = True

        if self.Study_area is not None:
            if not self.SA.exists():
                logging.error(_("INPUT : The study area file does not exist"))
                err = True

        if not self.ORIGINAL_GDB.exists():
            logging.error(_("INPUT : The original gdb file does not exist - Please pull it from the SPW-ARNE"))
            err = True

        if not self.CAPA_WALLOON.exists():
            logging.error(_("INPUT : The Cadastre Walloon file does not exist - Please pull it from the SPW"))
            err = True

        if not self.PICC_WALLOON.exists():
            logging.error(_("INPUT : The PICC Walloon file does not exist - Please pull it from the SPW website"))
            err = True

        if not self.CE_IGN_TOP10V.exists():
            logging.error(_("INPUT : The CE IGN top10v file does not exist - Please pull it from the IGN"))
            err = True

        if self.scenario is None:
            logging.debug("The scenario has not been defined")
        else:
            if not self.IN_SCEN_DIR.exists():
                logging.error(_("The wd scenario directory does not exist"))
                err = True

        return not err

    def check_temporary(self) -> bool:
        """
        Check if the temporary directories exist.

        If not, create them.
        """

        self.TMP_DIR.mkdir(parents=True, exist_ok=True)

        if self.Study_area is not None:
            self.TMP_STUDYAREA.mkdir(parents=True, exist_ok=True)
            self.TMP_DATABASE.mkdir(parents=True, exist_ok=True)
            self.TMP_CLIPGDB.mkdir(parents=True, exist_ok=True)
            self.TMP_CADASTER.mkdir(parents=True, exist_ok=True)
            self.TMP_WMODIF.mkdir(parents=True, exist_ok=True)
            self.TMP_CODEVULNE.mkdir(parents=True, exist_ok=True)
            self.TMP_PICC.mkdir(parents=True, exist_ok=True)
            self.TMP_IGNCE.mkdir(parents=True, exist_ok=True)
            self.TMP_VULN_DIR.mkdir(parents=True, exist_ok=True)
            self.TMP_RASTERS.mkdir(parents=True, exist_ok=True)
            self.TMP_RASTERS_CODE.mkdir(parents=True, exist_ok=True)
            self.TMP_RASTERS_VULNE.mkdir(parents=True, exist_ok=True)

        if self.scenario is not None:
            self.TMP_SCEN_DIR.mkdir(parents=True, exist_ok=True)
            self.TMP_RM_BUILD_DIR.mkdir(parents=True, exist_ok=True)
            self.TMP_QFILES.mkdir(parents=True, exist_ok=True)

        return True

    def check_outputs(self) -> bool:
        """
        Check if the output directories exist.

        If not, create them.
        """

        self.OUT_DIR.mkdir(parents=True, exist_ok=True)

        if self.Study_area is not None:
            self.OUT_STUDY_AREA.mkdir(parents=True, exist_ok=True)

        if self.scenario is not None:
            self.OUT_SCEN_DIR.mkdir(parents=True, exist_ok=True)
            self.OUT_WITHVULN.mkdir(parents=True, exist_ok=True)
            self.OUT_BASELINE.mkdir(parents=True, exist_ok=True)


        return True

    def check_before_database_creation(self) -> bool:
        """ Check if the necessary files are present before the database creation"""

        if not self.is_valid_inputs:
            logging.error(_("Theere are missing input directories - Please check carefully the input directories and the logs"))
            return False

        if not self.is_valid_study_area:
            logging.error(_("The study area file does not exist - Please create it"))
            return False

        if not self.is_valid_vulnerability_csv:
            logging.error(_("The vulnerability CSV file does not exist - Please create it"))
            return False

        return True

    def check_before_rasterize(self) -> bool:

        if not self.TMP_CODEVULNE.exists():
            logging.error(_("The final database with vulnerability levels does not exist"))
            return False

        if not self.TMP_WMODIF.exists():
            logging.error(_("The vector data with modifications does not exist"))
            return False

        return True

    def check_before_vulnerability(self) -> bool:

        if self.SA is None:
            logging.error(_("The area of interest does not exist"))
            return False

        if self.IN_WATER_DEPTH is None:
            logging.error(_("The water depth directory does not exist"))
            return False

        if self.IN_SCEN_DIR is None:
            logging.error(_("The wd scenario directory does not exist in the water depth directory"))
            return False

        if self.SA_MASKED_RIVER is None:
            logging.error(_("The IGN raster does not exist"))
            return False

        return True

    def check_vuln_code_sa(self) -> bool:

        if not self.SA_VULN.exists():#SA_VULN
            logging.error(_("The vulnerability raster file does not exist"))
            return False

        if not self.SA_CODE.exists():
            logging.error(_("The vulnerability code raster file does not exist"))
            return False

        return True

    def check_vuln_code_scenario(self) -> bool:

        if not self.TMP_VULN.exists():
            logging.error(_("The vulnerability raster file does not exist"))
            return False

        if not self.TMP_CODE.exists():
            logging.error(_("The vulnerability code raster file does not exist"))
            return False

        return True

    def compare_original_clipped_layers(self) -> str:
        """ Compare the original layers with the clipped ones """

        layers = self.get_layers_in_gdb()
        layers_clip = self.get_layers_in_clipgdb()

        ret = 'These layers have not been clipped:\n'
        for layer in layers:
            if layer not in layers_clip:
                ret += " - {}\n".format(layer)

        ret += '\nThese layers have been clipped but are not present in the GDB:\n'
        for layer in layers_clip:
            if layer not in layers:
                ret += " - {}\n".format(layer)

        ret+='\n'

        return ret

    def compare_clipped_raster_layers(self) -> str:
        """ Compare the clipped layers with the rasterized ones """

        layers = self.get_layers_in_clipgdb()
        layers_rast = self.get_layers_in_codevulne()

        ret = 'These layers {} have not been rasterized:\n'
        for layer in layers:
            if layer not in layers_rast:
                ret += " - {}\n".format(layer)

        ret += '\nThese layers have been rasterized but are not in the orginal GDB:\n'
        for layer in layers_rast:
            if layer not in layers:
                ret += " - {}\n".format(layer)

        ret+='\n'

        return ret

    def get_operand(self, file:str) -> Modif_Type:
        """ Get the operand based on the layer name """
        LAYERS_WALOUS = ["WALOUS_2018_LB72_112",
                        "WALOUS_2018_LB72_31",
                        "WALOUS_2018_LB72_32",
                        "WALOUS_2018_LB72_331",
                        "WALOUS_2018_LB72_332",
                        "WALOUS_2018_LB72_333",
                        "WALOUS_2018_LB72_34"]

        ret, curtype = self.is_same_types(file)
        layer = Path(file).stem

        if not ret:
            raise ValueError("The layer contains different types of geometries")

        if layer in LAYERS_WALOUS:
            return Modif_Type.WALOUS

        elif curtype=="Point":

            self.points2polys.append(layer)

            if layer =="BDREF_DGO3_PASH__SCHEMA_STATIONS_EPU":
                return Modif_Type.POINT2POLY_EPURATION
            elif layer =="INFRASIG_SOINS_SANTE__ETAB_AINES":
                return Modif_Type.POINT2POLY_PICC
            else:
                return Modif_Type.POINT2POLY_CAPAPICC

        elif layer =="Hab_2018_CABU":
            return Modif_Type.INHABITED

        elif layer =="INFRASIG_ROUTE_RES_ROUTIER_TE_AXES":

            self.lines2polys.append(layer)

            return Modif_Type.ROAD

        else:
            return Modif_Type.COPY

    def check_origin_shape(self) -> list[str]:

        code = self.get_files_in_rasters_code()
        vuln = self.get_files_in_rasters_vulne()

        if len(code) == 0:
            logging.error(_("The code rasters do not exist"))
            return False

        if len(vuln) == 0:
            logging.error(_("The vulnerability rasters do not exist"))
            return False

        if len(code) != len(vuln):
            logging.error(_("The number of code and vulnerability rasters do not match"))
            return False

        # we take a reference raster
        ref = gdal.Open(str(code[0]))
        band_ref = ref.GetRasterBand(1)
        proj_ref = ref.GetProjection()
        geo_ref  = ref.GetGeoTransform()
        col_ref, row_ref = band_ref.XSize, band_ref.YSize

        # we compare the reference raster with the others
        diff = []
        for cur in code + vuln + [self.SA_MASKED_RIVER]:
            cur_ = gdal.Open(str(cur))
            band_cur = cur_.GetRasterBand(1)
            proj_cur = cur_.GetProjection()
            geo_cur  = cur_.GetGeoTransform()
            col_cur, row_cur = band_cur.XSize, band_cur.YSize

            if geo_ref != geo_cur:
                logging.error(_("The geotransforms do not match {}".format(cur)))
                diff.append(cur)

            if proj_ref != proj_cur:
                logging.error(_("The projections do not match {}".format(cur)))
                diff.append(cur)

            if col_ref != col_cur or row_ref != row_cur:
                logging.error(_("The dimensions do not match {}".format(cur)))
                diff.append(cur)

        return diff




    # Assembly (FR : agglomération)
    # -----------------------------
    """Basically the same operations as in the config manager to agglomerate several rasters
    The class Config_Manager_2D_GPU is called, however some functions were rewritten to allow
    the search of a more specific word ('vuln', and not 'bath', 'mann', or 'inf').
    """

    def tree_name_tif(folder_path, name):
        """Find all .tiff files starting with 'vuln' in the directory and return paths"""
        folder = Path(folder_path)
        vuln_tiff_files = {file for file in folder.rglob("*.tiff") if file.name.startswith(name)}
        vuln_tif_files = {file for file in folder.rglob("*.tif") if file.name.startswith(name)}

        vuln_files = vuln_tiff_files.union(vuln_tif_files)

        tiff_trees = []
        if len(vuln_files) !=0:
            for tiff in vuln_files:
                    curtree = [tiff]
                    while tiff.parent != folder:
                        tiff = tiff.parent
                        curtree.insert(0, tiff)
                    tiff_trees.append(curtree)
        return tiff_trees

    def select_name_tif(self, path_baseline: Path, folder_path: Path, name, filter_type = False) -> tuple[list[Path], list[Path]]:
        """
        Collects all .tiff files starting with `name` from `folder_path` and appends them to a list.
        Checks each file's data type against the baseline raster and renames files with a mismatched type,
        (allowing it not to be surimposed as it does not begin by "vuln_" anymore).

        :param path_baseline: Path to the baseline raster file.
        :type path_baseline: pathlib.Path
        :param folder_path: Path to the folder containing raster files to check.
        :type folder_path: pathlib.Path
        :param name: Prefix name to filter .tiff files in the folder.
        :type name: str
        :return: A tuple containing two lists:
            - files: List of paths with matching data type.
            - unused_files: List of paths renamed due to type mismatch.
        :rtype: tuple[list[pathlib.Path], list[pathlib.Path]]
        """

        files = []
        unused_files = []

        # Check type of base of assembly
        ds_base = gdal.Open(path_baseline.as_posix())
        type_base = gdal.GetDataTypeName(ds_base.GetRasterBand(1).DataType)
        ds_base = None
        
        files.append(path_baseline.as_posix())

        #any files that begin by 'name'
        tiff_trees = Accept_Manager.tree_name_tif(folder_path, name)
        for tree in tiff_trees:
            file_path = tree[-1]
            ds = gdal.Open(file_path.as_posix())
            file_type = gdal.GetDataTypeName(ds.GetRasterBand(1).DataType)
            ds = None
            #filter if not the same type and renaming
            if filter_type == True :
                if file_type != type_base:
                    suffix_to_add = f"_{file_type}"
                    new_name = file_path.parent / f"{file_path.name}{suffix_to_add}"
                    if not file_path.stem.endswith(suffix_to_add):
                        file_path.rename(new_name)
                        unused_files.append(new_name)
                    else:
                        unused_files.append(file_path)
                else:
                    files.append(file_path.as_posix())
            else:
                files.append(file_path.as_posix())
        return files, unused_files

    def check_nodata(self, name, path_baseline):
            """ Check nodata in a path """
            from ..wolf_array import WOLF_ARRAY_FULL_INTEGER8
            list_tif, unused = Accept_Manager.select_name_tif(self, path_baseline, self.IN_CH_SA_SC, name)
            for cur_lst in list_tif:
                curarray:WolfArray = WolfArray(cur_lst)
                if curarray.wolftype != WOLF_ARRAY_FULL_INTEGER8:
                    if curarray.nullvalue != 99999.:
                        curarray.nullvalue = 99999.
                        curarray.set_nullvalue_in_mask()
                        curarray.write_all()
                        logging.warning(_('nodata changed in favor of 99999. value for file {} !'.format(cur_lst)))
                else:
                    logging.info(_('nodata value is {} for file {} !'.format(curarray.nullvalue, cur_lst)))

    def create_vrtIfExists(self, fn_baseline, fn_scenario, fn_vrt, name):
        """ Create a vrt file from a path """
        logging.info(_('Checking nodata values...'))
        self.check_nodata(name, fn_baseline)
        list_tif, list_fail = Accept_Manager.select_name_tif(self, fn_baseline, fn_scenario, name, filter_type = True)
        if len(list_fail)>0:
                return False, list_fail
        #création du fichier vrt - assembly/agglomération
        if len(list_tif)>1:
            logging.info(_('Creating .vrt from files (first based)...'))
            if name == "vuln_":
                create_vrt_from_diverged_files_first_based(list_tif, fn_vrt, Nodata = 127)
            else :
                create_vrt_from_diverged_files_first_based(list_tif, fn_vrt, Nodata = 99999.)
            return True, list_fail
        else:
            return False, list_fail


    def translate_vrt2tif(self, fn_VRT, fn_vuln_s):
        """ Translate vrt from OUTPUT > ... > Scenario to tif saved in the same folder, and delete the vrt file """
        if (fn_VRT).exists():
            translate_vrt2tif(fn_VRT, fn_vuln_s)
            os.remove(fn_VRT)

    def copy_tif_files(self, files: list[Path], destination_dir: Path) -> None:
        destination_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            destination_file = destination_dir / file.name
            dataset = gdal.Open(str(file))
            if dataset is None:
                logging.warning(f"Could not open {file} with GDAL.")
                continue
            gdal_driver = gdal.GetDriverByName('GTiff')
            gdal_driver.CreateCopy(str(destination_file), dataset, strict=0)

            dataset = None

        logging.info("All the existing .tif files have been copied to the destination directory.")

    def wich_river_trace(self, state_toggle_scen):
        """ Searches for existing riverbed traces: if none ending with '_scenarios' are found, it selects the baseline trace."""
        trace = None
        if state_toggle_scen == True :
            if os.path.exists(self.OUT_MASKED_RIVER_S):
                trace = self.OUT_MASKED_RIVER_S
                logging.info(_(f"Used river mask = {self.OUT_MASKED_RIVER_S}."))
            elif os.path.exists(self.OUT_MASKED_RIVER):
                trace = self.OUT_MASKED_RIVER
                logging.error(_(f"No scenario_ river mask, the used river mask will be the one of the baseline = {self.OUT_MASKED_RIVER}."))
            else :
                logging.error(_("No Masked_River_extent file. Please provide it (button 'Update riverbed trace')."))
        else :
            if os.path.exists(self.OUT_MASKED_RIVER_S):
                trace = self.OUT_MASKED_RIVER_S
                logging.info(_(f"Used river mask = {self.OUT_MASKED_RIVER_S}."))
            else :
                logging.error(_("No Masked_River_extent file. Please provide it (button 'Update riverbed trace')."))
        return trace


def clip_layer(layer:str,
             file_path:str,
             Study_Area:str,
             output_dir:str):
    """
    Clip the input data based on the selected bassin and saves it
    in separate shape files.

    As shape file doen not support DateTime, the columns with DateTime
    are converted to string.

    :param layer: the layer name in the GDB file
    :param file_path: the path to the GDB file
    :param Study_Area: the path to the study area shapefile
    :param output_dir: the path to the output directory
    """

    layer = str(layer)
    file_path = str(file_path)
    Study_Area = str(Study_Area)
    output_dir = Path(output_dir)

    St_Area = gpd.read_file(Study_Area, engine=ENGINE)

    logging.info(layer)

    # The data is clipped during the reading
    # **It is more efficient than reading the entire data and then clipping it**
    #
    # FIXME: "read_dataframe" is used directly rather than "gpd.read_file" cause
    # the "layer" parameter is well transmitted to the "read_dataframe" function...
    df:gpd.GeoDataFrame = read_dataframe(file_path, layer=layer, mask=St_Area['geometry'][0])

    if len(df) == 0:
        logging.warning("No data found for layer " + str(layer))
        return "No data found for layer " + str(layer)

    # Force Lambert72 -> EPSG:31370
    df.to_crs("EPSG:31370", inplace=True)
    try:
        date_columns = df.select_dtypes(include=['datetimetz']).columns.tolist()
        if len(date_columns)>0:
            df[date_columns] = df[date_columns].astype(str)

        df.to_file(str(output_dir / (layer+EXTENT)), mode='w', engine=ENGINE)
    except Exception as e:
        logging.error(_("Error while saving the clipped " + str(layer) + " to file"))
        logging.error(e)
        pass

    logging.info("Saved the clipped " + str(layer) + " to file")
    return "Saved the clipped " +str(layer)+ " to file"


def data_modification(layer:str,
                      manager:Accept_Manager,
                      picc:gpd.GeoDataFrame,
                      capa:gpd.GeoDataFrame ):
    """
    Apply the data modifications as described in the LEMA report

    FIXME : Add more doc in this docstring

    :param input_database: the path to the input database
    :param layer: the layer name in the database
    :param output_database: the path to the output database
    :param picc: the PICC Walloon file -- Preloaded
    :param capa: the Cadastre Walloon file -- Preloaded
    """

    df1:gpd.GeoDataFrame
    df2:gpd.GeoDataFrame

    layer = str(layer)

    dir_input = manager.TMP_CLIPGDB
    dir_output = manager.TMP_WMODIF

    input_file  = str(dir_input  / (layer + EXTENT))
    output_file = str(dir_output / (layer + EXTENT))

    # Read the data
    df:gpd.GeoDataFrame = gpd.read_file(input_file, engine=ENGINE)
    nblines, notused = df.shape

    if nblines>0:
        op = manager.get_operand(input_file)

        if op == Modif_Type.WALOUS:
            # Walous layers changed to PICC buidings

            assert picc.crs == df.crs, "CRS of PICC and input data do not match"

            assert "GEOREF_ID" in picc.columns, "The PICC file does not contain the GEOREF_ID column"
            assert "NATUR_CODE" in picc.columns, "The PICC file does not contain the NATUR_CODE column"

            df1  = gpd.sjoin(picc, df, how="inner", predicate="intersects" )
            cols = df.columns

            cols = np.append(cols, "GEOREF_ID")
            cols = np.append(cols, "NATUR_CODE")

            df1  = df1[cols]

            if df1.shape[0] > 0:
                assert manager.is_polygons(set(df1.geom_type)), f"The layer does not contains polygons - {op}"
                df1.to_file(output_file, engine=ENGINE)
            else:
                logging.warning("No data found for layer " + str(layer))

        elif op == Modif_Type.POINT2POLY_EPURATION:
            # Change BDREF based on AJOUT_PDET sent by Perrine (SPI)

            # The original layer is a point layer.
            # The EPU_STATIONS shape file (from SPI) is a polygon layer.

            df1 = gpd.read_file(str(manager.EPU_STATIONS), engine=ENGINE)

            assert df1.crs == df.crs, "CRS of AJOUT_PDET and input data do not match"

            df2 = gpd.sjoin(picc, df1, how="inner", predicate="intersects" )

            if df2.shape[0] > 0:
                assert manager.is_polygons(set(df2.geom_type)), f"The layer does not contains polygons - {op}"
                df2.to_file(output_file, engine=ENGINE)
            else:
                logging.warning("No data found for layer " + str(layer))

        elif op == Modif_Type.POINT2POLY_PICC:
            # Select the polygons that contains the points
            #  in theCadaster and PICC files

            assert capa.crs == df.crs, "CRS of CaPa and input data do not match"
            assert "CaPaKey" in capa.columns, "The CaPa file does not contain the CaPaKey column"

            df1= gpd.sjoin(capa, df, how="inner", predicate="intersects" )
            cols=df.columns

            cols = np.append(cols, "CaPaKey")
            df1=df1[cols]
            df2=gpd.sjoin(picc, df1, how="inner", predicate="intersects" )

            if df2.shape[0] > 0:
                assert manager.is_polygons(set(df2.geom_type)), f"The layer does not contains polygons - {op}"
                df2.to_file(output_file, engine=ENGINE)
            else:
                logging.warning("No data found for layer " + str(layer))

        elif op == Modif_Type.POINT2POLY_CAPAPICC:

            # Select the polygons that contains the points
            #  in theCadaster and PICC files

            assert capa.crs == df.crs, "CRS of CaPa and input data do not match"
            assert picc.crs == df.crs, "CRS of PICC and input data do not match"

            # Join the Layer and CaPa DataFrames : https://geopandas.org/en/stable/docs/reference/api/geopandas.sjoin.html
            # ‘inner’: use intersection of keys from both dfs; retain only left_df geometry column
            # "intersects" : Binary predicate. Valid values are determined by the spatial index used.
            df1= gpd.sjoin(capa, df, how="inner", predicate="intersects" )

            # Retain only the columns of the input data
            cols = df.columns
            # but add the CaPaKey
            cols = np.append(cols, "CaPaKey")

            df1  = df1[cols]

            # Join the df1 and PICC DataFrames : https://geopandas.org/en/stable/docs/reference/api/geopandas.sjoin.html
            df2  = gpd.sjoin(picc, df1, how="inner", predicate="intersects" )

            # Add only the GEOREF_ID and NATUR_CODE columns from PICC
            cols = np.append(cols, "GEOREF_ID")
            cols = np.append(cols, "NATUR_CODE")

            df2 = df2[cols]

            if df2.shape[0] > 0:
                assert manager.is_polygons(set(df2.geom_type)), f"The layer does not contains polygons - {op}"
                df2.to_file(output_file, engine=ENGINE)
            else:
                logging.warning("No data found for layer " + str(layer))

        elif op == Modif_Type.INHABITED:
            # Select only the buildings with a number of inhabitants > 0
            df1=df[df["NbsHabTOT"]>0]

            if df1.shape[0] > 0:
                assert manager.is_polygons(set(df1.geom_type)), f"The layer does not contains polygons - {op}"
                df1.to_file(output_file, engine=ENGINE)
            else:
                logging.warning("No data found for layer " + str(layer))

        elif op == Modif_Type.ROAD:
            # Create a buffer around the roads
            df1=df.buffer(distance=6, cap_style=2)

            if df1.shape[0] > 0:
                assert set(df1.geom_type) == {'Polygon'}, f"The layer does not contains polygons - {op}"
                df1.to_file(output_file, engine=ENGINE)
            else:
                logging.warning("No data found for layer " + str(layer))

        elif op == Modif_Type.COPY:
            # just copy the data if it is polygons
            if manager.is_polygons(set(df.geom_type)):
                df.to_file(output_file, engine=ENGINE)
            else:
                logging.error(_("The layer does not contains polygons - " + str(layer)))
        else:
            raise ValueError(f"The operand {op} is not recognized")

        return "Data modification done for " + str(layer)
    else:
        # Normally, phase 1 does not create empty files
        # But it is better to check... ;-)
        logging.error(_("skipped" + str(layer) + "due to no polygon in the study area"))
        return "skipped" + str(layer) + "due to no polygon in the study area"

def compute_vulnerability(manager:Accept_Manager):
    """
    Compute the vulnerability for the Study Area

    This function **will not modify** the data by the removed buildings/scenarios.

    :param dirsnames: the Dirs_Names object from the calling function
    """

    vuln_csv = Vulnerability_csv(manager.VULNERABILITY_CSV)

    rasters_vuln = manager.get_files_in_rasters_vulne()

    logging.info("Number of files: {}".format(len(rasters_vuln)))
    ds:gdal.Dataset = gdal.OpenEx(str(rasters_vuln[0]), gdal.GA_ReadOnly, open_options=["SPARSE_OK=TRUE"])

    tmp_vuln = ds.GetRasterBand(1)

    # REMARK: The XSize and YSize are the number of columns and rows
    col, row = tmp_vuln.XSize, tmp_vuln.YSize

    logging.info("Computing Vulnerability")

    array_vuln = np.ones((row, col), dtype=np.int8)

    # Create a JIT function to update the arrays
    # Faster than the classical Python loop or Numpy
    @nb.jit(nopython=True, boundscheck=False, inline='always')
    def update_arrays_jit(tmp_vuln, array_vuln):
        for i in range(tmp_vuln.shape[0]):
            for j in range(tmp_vuln.shape[1]):
                if tmp_vuln[i, j] >= array_vuln[i, j]:
                    array_vuln[i, j] = tmp_vuln[i, j]

        return array_vuln

    @nb.jit(nopython=True, boundscheck=False, inline='always')
    def update_arrays_jit_csr(row, col, locvuln, array_vuln):
        for k in range(len(row)-1):
            i = k
            j1 = row[k]
            j2 = row[k+1]
            for j in col[j1:j2]:
                if locvuln >= array_vuln[i, j]:
                    array_vuln[i, j] = locvuln

        return array_vuln

    for i in tqdm(range(len(rasters_vuln)), 'Computing Vulnerability : '):
        #logging.info("Computing layer {} / {}".format(i, len(rasters_vuln)))

        locvuln = vuln_csv.get_vulnerability_level(rasters_vuln[i].stem)

        if locvuln == 1:
            logging.info("No need to apply the matrice, the vulnerability is 1 which is the lower value")
            continue

        if rasters_vuln[i].with_suffix('.npz').exists():
            ij_npz = np.load(rasters_vuln[i].with_suffix('.npz'))
            ii = ij_npz['row']
            jj = ij_npz['col']
            # We use the jit
            update_arrays_jit_csr(ii, jj, locvuln, array_vuln)

        else:
            ds  = gdal.OpenEx(str(rasters_vuln[i]), open_options=["SPARSE_OK=TRUE"])
            tmp_vuln = ds.GetRasterBand(1).ReadAsArray()
            # We use the jit
            update_arrays_jit(tmp_vuln, array_vuln)
    logging.info("Saving the computed vulnerability")
    dst_filename= str(manager.SA_VULN)
    y_pixels, x_pixels = array_vuln.shape  # number of pixels in x

    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(dst_filename,
                            x_pixels, y_pixels,
                            gdal.GDT_Byte,
                            1,
                            options=["COMPRESS=LZW"])

    dataset.GetRasterBand(1).WriteArray(array_vuln.astype(np.int8))
    # follow code is adding GeoTranform and Projection
    geotrans = ds.GetGeoTransform()  # get GeoTranform from existed 'data0'
    proj = ds.GetProjection()  # you can get from a exsited tif or import
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    dataset = None

    logging.info("Computed Vulnerability for the Study Area - Done")

def compute_code(manager:Accept_Manager):
    """
    Compute the code for the Study Area

    This function **will not modify** the data by the removed buildings/scenarios.

    :param dirsnames: the Dirs_Names object from the calling function
    """

    vuln_csv = Vulnerability_csv(manager.VULNERABILITY_CSV)
    rasters_code = manager.get_files_in_rasters_code()

    logging.info("Number of files: {}".format(len(rasters_code)))

    ds:gdal.Dataset = gdal.OpenEx(str(rasters_code[0]), gdal.GA_ReadOnly, open_options=["SPARSE_OK=TRUE"])

    tmp_code = ds.GetRasterBand(1)

    # REMARK: The XSize and YSize are the number of columns and rows
    col, row = tmp_code.XSize, tmp_code.YSize

    logging.info("Computing Code")

    array_code = np.ones((row, col), dtype=np.int8)

    # Create a JIT function to update the arrays
    # Faster than the classical Python loop or Numpy
    @nb.jit(nopython=True, boundscheck=False, inline='always')
    def update_arrays_jit(tmp_code, loccode, array_code):
        for i in range(tmp_code.shape[0]):
            for j in range(tmp_code.shape[1]):
                if tmp_code[i, j] >= array_code[i, j]:
                    array_code[i, j] = loccode

        return array_code

    @nb.jit(nopython=True, boundscheck=False, inline='always')
    def update_arrays_jit_csr(row, col, loccode, array_code):
        for k in range(len(row)-1):
            i = k
            j1 = row[k]
            j2 = row[k+1]
            for j in col[j1:j2]:
                if loccode >= array_code[i, j]:
                    array_code[i, j] = loccode

        return array_code

    for i in tqdm(range(len(rasters_code)), 'Computing Code : '):
        #logging.info("Computing layer {} / {}".format(i, len(rasters_code)))

        loccode = vuln_csv.get_vulnerability_code(rasters_code[i].stem.removesuffix("_CODE"))

        if rasters_code[i].with_suffix('.npz').exists():
            ij_npz = np.load(rasters_code[i].with_suffix('.npz'))
            ii = ij_npz['row']
            jj = ij_npz['col']
            # We use the jit
            update_arrays_jit_csr(ii, jj, loccode, array_code)

        else:
            ds  = gdal.OpenEx(str(rasters_code[i]), open_options=["SPARSE_OK=TRUE"])
            tmp_code = ds.GetRasterBand(1).ReadAsArray()
            # We use the jit
            update_arrays_jit(tmp_code, loccode, array_code)

    logging.info("Saving the computed codes")
    dst_filename= str(manager.SA_CODE)
    y_pixels, x_pixels = array_code.shape  # number of pixels in x
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(dst_filename,
                            x_pixels, y_pixels,
                            gdal.GDT_Byte,
                            1,
                            options=["COMPRESS=LZW"])

    dataset.GetRasterBand(1).WriteArray(array_code.astype(np.int8))
    # follow code is adding GeoTranform and Projection
    geotrans = ds.GetGeoTransform()  # get GeoTranform from existed 'data0'
    proj = ds.GetProjection()  # you can get from a exsited tif or import
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    dataset = None

    logging.info("Computed Code for the Study Area - Done")

def compute_vulnerability4scenario(manager:Accept_Manager):
    """ Compute the vulnerability for the scenario

    This function **will modify** the data by the removed buildings/scenarios.

    FIXME: It could be interseting to permit the user to provide tiff files for the removed buildings and other scenarios.

    :param dirsnames: the Dirs_Names object from the calling function
    """

    array_vuln = gdal.Open(str(manager.SA_VULN))
    geotrans = array_vuln.GetGeoTransform()  # get GeoTranform from existed 'data0'
    proj = array_vuln.GetProjection()  # you can get from a exsited tif or import

    array_vuln = np.array(array_vuln.GetRasterBand(1).ReadAsArray())

    array_code = gdal.Open(str(manager.SA_CODE))
    array_code = np.array(array_code.GetRasterBand(1).ReadAsArray())

    Rbu = manager.get_files_in_rm_buildings()

    if len(Rbu)>0:
        for curfile in Rbu:
            array_mod = gdal.Open(str(curfile))
            array_mod = np.array(array_mod.GetRasterBand(1).ReadAsArray())

            ij = np.argwhere(array_mod == 1)
            array_vuln[ij[:,0], ij[:,1]] = 1
            array_code[ij[:,0], ij[:,1]] = 1

    dst_filename= str(manager.TMP_VULN)
    y_pixels, x_pixels = array_vuln.shape  # number of pixels in x

    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(dst_filename, x_pixels, y_pixels, gdal.GDT_Byte, 1, options=["COMPRESS=LZW"])
    dataset.GetRasterBand(1).WriteArray(array_vuln.astype(np.int8))
    # follow code is adding GeoTranform and Projection
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    dataset = None


    dst_filename= str(manager.TMP_CODE)
    y_pixels, x_pixels = array_code.shape  # number of pixels in x
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(dst_filename, x_pixels, y_pixels, gdal.GDT_Byte, 1, options=["COMPRESS=LZW"])
    dataset.GetRasterBand(1).WriteArray(array_code.astype(np.int8))
    # follow code is adding GeoTranform and Projection
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    dataset = None

    logging.info("Computed Vulnerability and code for the scenario")

def match_vulnerability2sim(inRas:Path, outRas:Path, MODREC:Path):
    """
    Clip the raster to the MODREC/simulation extent

    :param inRas: the input raster file
    :param outRas: the output raster file
    :param MODREC: the MODREC/simulation extent file

    """

    inRas  = str(inRas)
    outRas = str(outRas)
    MODREC = str(MODREC)

    data = gdal.Open(MODREC, gdalconst.GA_ReadOnly)
    geoTransform = data.GetGeoTransform()
    minx = geoTransform[0]
    maxy = geoTransform[3]
    maxx = minx + geoTransform[1] * data.RasterXSize
    miny = maxy + geoTransform[5] * data.RasterYSize
    ds = gdal.Open(inRas)
    ds = gdal.Translate(outRas, ds, projWin = [minx, maxy, maxx, miny])
    ds = None


@nb.jit(nopython=True, boundscheck=False, inline='always')
def update_accept(accept, model_h, ij, bounds, loc_accept):
    for idx in range(len(bounds)):
        for i,j in ij:
            #lit dans wd vs Ti où on est et associe son score d'accept
            if bounds[idx,0] < model_h[i,j] <= bounds[idx,1]:
                accept[i,j] = loc_accept[idx]

def compute_acceptability(manager:Accept_Manager,
           model_h:np.ndarray,
           vulnerability:np.ndarray,
           interval:int,
           geo_projection:tuple,
           save_to_file:bool=True) -> np.ndarray:

    """
    Compute the local acceptability based on :
        - the vulnerability
        - the water depth
        - the matrices

    :param manager: the Accept_Manager object from the calling function
    :param model_h: the water depth matrix
    :param vulnerability: the vulnerability matrix
    :param interval: the return period
    :param geo_projection: the geotransform and the projection - tuple extracted from another raster file

    """

    #logging.info(interval)

    points_accept = pd.read_csv(manager.POINTS_CSV)    
    
    if interval not in points_accept["Interval"].to_list():
        logging.error(_("The return period {} is not in the intermediate.csv file -- Please update it").format(interval))
        return None

    points_accept = points_accept[points_accept["Interval"]==interval] #les wd vs Ti matrices
    points_accept = points_accept.reset_index()

    accept = np.zeros(vulnerability.shape, dtype=np.float32)

    bounds = np.asarray([[0., 0.02], [0.02, 0.3], [0.3, 1], [1, 2.5], [2.5, 1000]], dtype=np.float32)

    for i in range(1,6):
        ij = np.argwhere(vulnerability == i)

        idx_pts = 5-i
        accept_pts = [points_accept["h-0"][idx_pts],
                      points_accept["h-0.02"][idx_pts],
                      points_accept["h-0.3"][idx_pts],
                      points_accept["h-1"][idx_pts],
                      points_accept["h-2.5"][idx_pts]]

        accept_pts = list(accept_pts).copy()

        update_accept(accept, model_h, ij, bounds, accept_pts)

    if save_to_file:
        #save raster
        dst_filename = str(manager.TMP_QFILES / "Q{}.tif".format(interval)) #les Qi

        y_pixels, x_pixels = accept.shape  # number of pixels in x
        driver = gdal.GetDriverByName('GTiff')
        dataset = driver.Create(dst_filename,
                                x_pixels, y_pixels,
                                1,
                                gdal.GDT_Float32,
                                options=["COMPRESS=LZW"])

        dataset.GetRasterBand(1).WriteArray(accept.astype(np.float32))

        geotrans, proj = geo_projection
        dataset.SetGeoTransform(geotrans)
        dataset.SetProjection(proj)
        dataset.FlushCache()
        dataset = None

    return accept

def shp_to_raster(vector_fn:str | Path, raster_fn:str | Path, pixel_size:float = 1., manager:Accept_Manager = None):
    """
    Convert a vector layer to a raster tiff file.

    The raster will contain only 2 values : 0 and 1

    - 1 : the inside of the vector layer
    - 0 : the rest == NoData/NullValue

    :param vector_fn: the path to the vector file
    :param raster_fn: the path to the raster file
    :param pixel_size: the pixel size of the raster
    """

    vector_path = Path(vector_fn)
    raster_path = Path(raster_fn)

    if not vector_path.exists():
        logging.error(_(f"The vector file {vector_path} does not exist"))
        return

    if raster_path.exists():
        os.remove(raster_path)

    # Force the input to be a string
    vector_fn = str(vector_fn)
    raster_fn = str(raster_fn)

    if manager is None:
        extent_fn = vector_fn
        logging.warning("The extent file is not provided, the extent will be the same as the vector file")
    else:
        extent_fn = str(manager.SA)
        logging.info("The extent file is provided")

    NoData_value = 0 # np.nan is not necessary a good idea

    # Open the data sources and read the extents
    source_ds:ogr.DataSource = ogr.Open(vector_fn)
    source_layer = source_ds.GetLayer()

    extent_ds:ogr.DataSource = ogr.Open(extent_fn)
    extent_layer = extent_ds.GetLayer()
    x_min, x_max, y_min, y_max = extent_layer.GetExtent()

    x_min = float(int(x_min))
    x_max = float(np.ceil(x_max))
    y_min = float(int(y_min))
    y_max = float(np.ceil(y_max))

    # Create the destination data source
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)

    target_ds = gdal.GetDriverByName('GTiff').Create(raster_fn,
                                                     x_res, y_res,
                                                     1,
                                                     gdal.GDT_Byte,
                                                     options=["COMPRESS=LZW",
                                                              'SPARSE_OK=TRUE'])

    target_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31370)
    target_ds.SetProjection(srs.ExportToWkt())
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(NoData_value)
    # Rasterize the areas
    gdal.RasterizeLayer(target_ds,
                        bands = [1],
                        layer = source_layer,
                        burn_values = [1],
                        options=["ALL_TOUCHED=TRUE"])

    target_ds.FlushCache()
    target_ds = None
    vector_fn = raster_fn = None

def vector_to_raster(layer:str,
                     manager:Accept_Manager,
                     attribute:str,
                     pixel_size:float,
                     convert_to_sparse:bool = True):
    """
    Convert a vector layer to a raster tiff file

    FIXME: Test de vulerability value and return immedialty if it is 1 if attribute == "Vulne"

    :param layer: the layer name in the GDB file
    :param vector_input: the path to the vector file
    :param extent: the path to the extent file
    :param attribute: the attribute to rasterize
    :param pixel_size: the pixel size of the raster

    """

    layer = str(layer)

    vector_input = str(manager.TMP_CODEVULNE / (layer + EXTENT))
    extent = str(manager.SA)
    attribute = str(attribute)
    pixel_size = float(pixel_size)

    if attribute == "Code":
        out_file = manager.TMP_RASTERS / attribute / (layer + "_CODE.tiff")
    else :
        out_file = manager.TMP_RASTERS / attribute / (layer + ".tiff")

    if out_file.exists():
        os.remove(out_file)

    out_file = str(out_file)

    NoData_value = 0

    extent_ds:ogr.DataSource = ogr.Open(extent)
    extent_layer = extent_ds.GetLayer()

    x_min, x_max, y_min, y_max = extent_layer.GetExtent()

    x_min = float(int(x_min))
    x_max = float(np.ceil(x_max))
    y_min = float(int(y_min))
    y_max = float(np.ceil(y_max))

    # Open the data sources and read the extents
    source_ds:ogr.DataSource = ogr.Open(vector_input)
    if source_ds is None:
        logging.error(_(f"Could not open the data source {layer}"))
        return
    source_layer = source_ds.GetLayer()

    # Create the destination data source
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)
    target_ds:gdal.Driver = gdal.GetDriverByName('GTiff').Create(out_file,
                                                     x_res, y_res, 1,
                                                     gdal.GDT_Byte,
                                                     options=["COMPRESS=DEFLATE",
                                                              'SPARSE_OK=TRUE',])

    target_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31370)
    target_ds.SetProjection(srs.ExportToWkt())

    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(NoData_value)

    # Rasterize the areas
    gdal.RasterizeLayer(target_ds, [1],
                        source_layer,
                        options=["ATTRIBUTE="+attribute,
                                 "ALL_TOUCHED=TRUE"])

    if convert_to_sparse:
        SPARSITY_THRESHOLD = 0.02
        # Convert the raster to a npz containing the row and col of the non-null values
        array = band.ReadAsArray()
        ij = np.nonzero(array)

        if len(ij[0]) < int(x_res * y_res * SPARSITY_THRESHOLD):
            i,j = convert_to_csr(ij[0], ij[1], y_res)
            np.savez_compressed(Path(out_file).with_suffix('.npz'), row=np.asarray(i, dtype=np.int32), col=np.asarray(j, dtype=np.int32))
        else:
            logging.info("The raster is not sparse enough to be converted to a CSR forma {}".format(layer))

    target_ds = None

    return 0

@nb.jit(nopython=True, boundscheck=False, inline='always')
def convert_to_csr(i_indices, j_indices, num_rows):
    row_ptr = [0] * (num_rows + 1)
    col_idx = []

    for i in range(len(i_indices)):
        row_ptr[i_indices[i] + 1] += 1
        col_idx.append(j_indices[i])

    for i in range(1, len(row_ptr)):
        row_ptr[i] += row_ptr[i - 1]

    return row_ptr, col_idx
