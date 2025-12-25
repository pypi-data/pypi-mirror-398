"""
Author: University of Liege, HECE, LEMA
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.batch_creation_and_interpolation
"""

from .Parallels import parallel_gpd_clip, parallel_v2r, parallel_datamod
from .func import data_modification, compute_vulnerability, compute_vulnerability4scenario
from .func import match_vulnerability2sim, compute_acceptability, shp_to_raster, clip_layer
from .func import Accept_Manager, cleaning_directory, EXTENT, Vulnerability_csv, compute_code

from ..PyTranslate import _
import pandas as pd
import os
from osgeo import gdal
import fiona
import glob
import numpy as np
import geopandas as gpd
from pathlib import Path
import logging
from tqdm import tqdm
from enum import Enum
from pyogrio import read_dataframe

class steps_base_data_creation(Enum):
    """
    Enum for the steps in the base data creation
    """
    CLIP_GDB = 1
    CLIP_CADASTER = 2
    CLIP_PICC = 3
    POINTS2POLYS = 4
    RASTERIZE_IGN = 5
    PREPROCESS_VULNCODE = 6
    DATABASE_TO_RASTER = 7

    @classmethod
    def get_list_names(cls):
        return [f'{cur.name} - {cur.value}' for cur in cls]

class steps_vulnerability(Enum):
    """
    Enum for the steps in the vulnerability computation
    """
    CREATE_RASTERS = 1
    CREATE_RASTERS_VULN = 10
    CREATE_RASTERS_CODE = 11
    APPLY_MODIFS = 2
    MATCH_SIMUL = 3
    APPLY_SCENARIOSVULN = 4
    APPLY_SCENARIOSVULN_BUG = 42

    @classmethod
    def get_list_names(cls):
        return [f'{cur.name} - {cur.value}' for cur in cls]

class steps_acceptability(Enum):
    """
    Enum for the steps in the acceptability computation
    """
    COMPUTE_LOCAL_ACCEPT        = 1
    LOAD_FROM_FILES             = 2
    COMPUTE_MEAN_ACCEPT         = 3
    COMPUTE_BASELINE_WITHOUT_SCENARIOS   = 4
    COMPUTE_WITH_SCENARIOS      = 5
    RESAMPLING                  = 6

    @classmethod
    def get_list_names(cls):
        return [f'{cur.name} - {cur.value}' for cur in cls]

def Base_data_creation(main_dir:str = 'Data',
                       Original_gdb:str = 'GT_Resilence_dataRisques202010.gdb',
                       Study_area:str = 'Bassin_Vesdre.shp',
                       CaPa_Walloon:str = 'Cadastre_Walloon.gpkg',
                       PICC_Walloon:str = 'PICC_vDIFF.gdb',
                       CE_IGN_top10v:str = 'CE_IGN_TOP10V/CE_IGN_TOP10V.shp',
                       resolution:float = 1.,
                       number_procs:int = 8,
                       steps:list[int] | list[steps_base_data_creation] = [1,2,3,4,5,6,7],
                       Vuln_csv:str = 'Vulnerability.csv'):
    """
    Create the databse.

    In this step, the following operations are performed:
        - Clip the original gdb file to the study area
        - Clip the Cadastre Walloon file to the study area
        - Clip the PICC Walloon file to the study area
        - Clip and Rasterize the IGN top10v file
        - Create the study area database with the vulnerability levels


    :param main_dir: The main data directory
    :param Original_gdb: The original gdb file from SPW - GT Resilience
    :param Study_area: The study area shapefile -- Data will be clipped to this area
    :param CaPa_Walloon: The Cadastre Walloon file -- Shapfeile from SPW
    :param PICC_Walloon: The PICC Walloon file -- Shapefile from SPW
    :param CE_IGN_top10v: The CE "Cours d'eau" IGN top10v file -- Shapefile from IGN with river layer
    :param resolution: The output resolution of the raster files
    :param number_procs: The number of processors to use for parallel processing

    """
    LAYER_CABU = "CaBu"
    LAYER_CAPA = "CaPa"
    LAYER_BATIEMPRISE = "CONSTR_BATIEMPRISE"

    manager = Accept_Manager(main_dir,
                            Study_area,
                            Original_gdb=Original_gdb,
                            CaPa_Walloon=CaPa_Walloon,
                            PICC_Walloon=PICC_Walloon,
                            CE_IGN_top10v=CE_IGN_top10v,
                            Vuln_csv=Vuln_csv)

    if not manager.check_before_database_creation():
        logging.error("The necessary files are missing - Verify logs for more information")
        return

    done = []

    if 1 in steps or 6 in steps or steps_base_data_creation.PREPROCESS_VULNCODE in steps or steps_base_data_creation.CLIP_GDB in steps:
        # Load the vulnerability CSV to get the layers
        vulnerability_csv = Vulnerability_csv(manager.VULNERABILITY_CSV)

    if 1 in steps or steps_base_data_creation.CLIP_GDB in steps:
        # Clean the directory to avoid any conflict
        # GPKG driver does not overwrite the existing file but adds new layers
        cleaning_directory(manager.TMP_CLIPGDB)

        # ********************************************************************************************************************
        # Step 1, Clip Original GDB

        # Clip the GDB file and store it in output directory : manager.TMP_CLIPGDB
        parallel_gpd_clip(vulnerability_csv.get_layers(), manager.ORIGINAL_GDB, manager.SA, manager.TMP_CLIPGDB, number_procs)

        done.append(steps_base_data_creation.CLIP_GDB)

    if 2 in steps or steps_base_data_creation.CLIP_CADASTER in steps:
        # ********************************************************************************************************************
        # Step 2, Clip Cadaster data
        cleaning_directory(manager.TMP_CADASTER)

        # Only 2 layers are present in the Cadastre Walloon file
        # Clip the Cadastre Walloon file and store it in output directory : manager.TMP_CADASTER
        parallel_gpd_clip([LAYER_CABU, LAYER_CAPA], manager.CAPA_WALLOON, manager.SA, manager.TMP_CADASTER, min(2, number_procs))

        done.append(steps_base_data_creation.CLIP_CADASTER)

    if 3 in steps or steps_base_data_creation.CLIP_PICC in steps:
        # ********************************************************************************************************************
        # Step 3, Clip PICC data
        cleaning_directory(manager.TMP_PICC)

        # ONly 1 layer is needed from the PICC Walloon file
        # Clip the PICC Walloon file and store it in output dir : manager.TMP_PICC
        parallel_gpd_clip([LAYER_BATIEMPRISE], manager.PICC_WALLOON, manager.SA, manager.TMP_PICC, min(1, number_procs))

        done.append(steps_base_data_creation.CLIP_PICC)

    if 4 in steps or steps_base_data_creation.POINTS2POLYS in steps:
        # ********************************************************************************************************************
        # Step 4, create database based on changes in report

        cleaning_directory(manager.TMP_WMODIF)

        # PreLoad Picc and CaPa from clipped files
        Picc:gpd.GeoDataFrame = read_dataframe(str(manager.TMP_PICC / (LAYER_BATIEMPRISE+EXTENT)), layer=LAYER_BATIEMPRISE)
        CaPa:gpd.GeoDataFrame = read_dataframe(str(manager.TMP_CADASTER / (LAYER_CAPA+EXTENT)), layer=LAYER_CAPA)

        assert Picc.crs == CaPa.crs, "The crs of the two shapefiles are different"

        parallel_datamod(manager=manager, picc=Picc, capa=CaPa, number_procs=number_procs)

        done.append(steps_base_data_creation.POINTS2POLYS)

    if 5 in steps or steps_base_data_creation.RASTERIZE_IGN in steps:
        # ********************************************************************************************************************
        # Step 5 : Rasaterize the IGN data "Course d'eau" to get the riverbed mask
        LAYER_IGN = "CE_IGN_TOP10V"
        clip_layer(layer=LAYER_IGN, file_path=manager.CE_IGN_TOP10V, Study_Area=manager.SA, output_dir=manager.TMP_IGNCE)
        shp_to_raster(manager.TMP_IGNCE / (LAYER_IGN + '.gpkg'), manager.SA_MASKED_RIVER, resolution, manager=manager)

        done.append(steps_base_data_creation.RASTERIZE_IGN)

    if 6 in steps or steps_base_data_creation.PREPROCESS_VULNCODE in steps:
        # ********************************************************************************************************************
        # Step 6 :  Pre-processing for Vulnerability
        #           Save the database with vulnerability levels and codes
        # This database will be rasterized in 'Database_to_raster'

        layers_sa = manager.get_layers_in_wmodif()
        layers_csv = vulnerability_csv.get_layers()

        # Search difference between the two lists of layers
        list_shp = list(set(layers_csv).difference(layers_sa))

        logging.info("Excluded layers due to no features in shapefiles:")
        logging.info(list_shp)

        not_in_csv = [curlayer for curlayer in layers_sa if curlayer not in layers_csv]
        if len(not_in_csv) > 0:
            logging.error("Not treated layers due to no vulnerability level or code:")
            logging.error(not_in_csv)

        logging.info("STEP1: Saving the database for Vulnerability with attributes Vulne and Code")

        for curlayer in layers_sa:
            logging.info(curlayer)

            in_file  = str(manager.TMP_WMODIF    / (curlayer+EXTENT))
            out_file = str(manager.TMP_CODEVULNE / (curlayer+EXTENT))

            shp:gpd.GeoDataFrame = gpd.read_file(in_file)

            nb_lines, unused = shp.shape
            if nb_lines > 0:
                shp["Path"]  = curlayer
                shp["Vulne"] = vulnerability_csv.get_vulnerability_level(curlayer)
                shp["Code"]  = vulnerability_csv.get_vulnerability_code(curlayer)
                shp = shp[["geometry", "Path", "Vulne","Code"]]
                shp.to_file(out_file)
            else:
                # Normally, Phase 1 should have removed the empty shapefiles
                # But, we never know... ;-)
                logging.warning(f"Empty shapefile {curlayer} in {in_file}")

        done.append(steps_base_data_creation.PREPROCESS_VULNCODE)

    if 7 in steps or steps_base_data_creation.DATABASE_TO_RASTER in steps:
        # Rasterize the database
        cleaning_directory(manager.TMP_RASTERS)
        cleaning_directory(manager.TMP_RASTERS_CODE)
        cleaning_directory(manager.TMP_RASTERS_VULNE)

        Database_to_raster(main_dir,
                           Study_area,
                           resolution,
                           number_procs=number_procs,
                           Vuln_csv=Vuln_csv)

        done.append(steps_base_data_creation.DATABASE_TO_RASTER)

    return done

def Database_to_raster(main_dir:str = 'Data',
                       Study_area:str = 'Bassin_Vesdre.shp',
                       resolution:float = 1.,
                       number_procs:int = 16,
                       Vuln_csv:str = 'Vulnerability.csv'):
    """
    Convert the vector database to raster database based on their vulnerability values

    Each leyer is converted to a raster file with the vulnerability values
    and the code values.

    They are stored in the TEMP/DATABASES/*StudyArea*/VULNERABILITY/RASTERS in:
        - Code
        - Vulne

    :param main_dir: The main data directory
    :param Study_area: The study area shapefile
    :param resolution: The resolution of the output raster files - default is 1 meter
    :param number_procs: The number of processors to use for parallel processing

    The parallel processing is safe as each layer is processed independently.
    """

    manager = Accept_Manager(main_dir, Study_area, Vuln_csv=Vuln_csv)

    resolution = float(resolution)

    if not manager.check_before_rasterize():
        logging.error("The necessary files are missing - Verify logs for more information")
        return

    logging.info("Convert vectors to raster based on their vulnerability values")

    attributes = ["Vulne", "Code"]
    for cur_attrib in attributes:
        parallel_v2r(manager, cur_attrib, resolution, number_procs, convert_to_sparse=True)

def Vulnerability(main_dir:str = 'Data',
                  scenario:str = 'Scenario1',
                  Study_area:str = 'Bassin_Vesdre.shp',
                  resolution:float = 1.,
                  steps:list[int] | list[steps_vulnerability] = [1,10,11,2,3,4],
                  Vuln_csv:str = 'Vulnerability.csv',
                  Intermediate_csv:str = 'Intermediate.csv'):
    """
    Compute the vulnerability for the study area and the scenario, if needed.

    The vulnerability is computed in 3 steps:
        1.  Compute the vulnerability for the study area
        2.  Compute the vulnerability for the scenario
        3.  Clip the vulnerability rasters to the simulation area

    During step 3, three matrices are computed and clipped to the simulation area:
        - Vulnerability
        - Code
        - Masked River

    :param main_dir: The main data directory
    :param scenario: The scenario name
    :param Study_area: The study area shapefile
    :param resolution: The resolution of the output raster files - default is 1 meter
    :param steps: The steps to compute the vulnerability - default is [1,2,3]

    To be more rapid, the steps can be computed separately.
        - [1,2,3] : All steps are computed - Necessary for the first time
        - [2,3]   : Only the scenario and clipping steps are computed -- Useful for scenario changes
        - [3]     : Only the clipping step is computed -- Useful if simulation area changes but scenario is the same
        - [4]     : Compute the vulnerability for vuln_ scenarios

    """

    #Call of the Manager Class --> allows structure
    manager = Accept_Manager(main_dir,
                             Study_area,
                             scenario=scenario,
                             Vuln_csv=Vuln_csv,
                             Intermediate_csv=Intermediate_csv)

    if not manager.check_before_vulnerability():
        logging.error("The necessary files are missing - Verify logs for more information")
        return

    logging.info("Starting VULNERABILITY computations at {} m resolution".format(resolution))

    done = []

    if 1 in steps or steps_vulnerability.CREATE_RASTERS in steps:
        # Step 1 :  Compute the vulnerability rasters for the study area
        #           The data **will not** be impacted by the scenario modifications

        logging.info("Generate Vulnerability rasters {}m".format(resolution))

        cleaning_directory(manager.TMP_SCEN_DIR)

        if 10 in steps or steps_vulnerability.CREATE_RASTERS_VULN in steps:
            compute_vulnerability(manager)
            done.append(steps_vulnerability.CREATE_RASTERS_VULN)

        if 11 in steps or steps_vulnerability.CREATE_RASTERS_CODE in steps:
            compute_code(manager)
            done.append(steps_vulnerability.CREATE_RASTERS_CODE)

        done.append(steps_vulnerability.CREATE_RASTERS)

    if 2 in steps or steps_vulnerability.APPLY_MODIFS in steps:
        # Step 2 :  Compute the vulnerability rasters for the scenario
        #           The data **will be** impacted by the scenario modifications

        if not manager.check_vuln_code_sa():
            logging.error("The vulnerability and code files for the study area are missing")
            logging.warning("Force the computation even if not prescribed in the steps")

            Vulnerability(main_dir, scenario, Study_area, resolution, [1])

        bu:list[Path] = manager.get_files_in_rm_buildings()

        if len(bu)>0:
            for curfile in bu:
                tiff_file = manager.TMP_RM_BUILD_DIR / (curfile.stem + ".tiff")
                shp_to_raster(curfile, tiff_file)

            compute_vulnerability4scenario(manager)
        else:
            logging.warning(f"No buildings were removed in water depth analysis OR No shapefiles in {manager.IN_RM_BUILD_DIR}")

        done.append(steps_vulnerability.APPLY_MODIFS)

    if 3 in steps or steps_vulnerability.MATCH_SIMUL in steps:
        # Step 3 :  Clip the vulnerability/code rasters to the **simulation area**
        logging.info("Save Vulnerability files for the area of interest")

        return_periods = manager.get_return_periods()
        TMAX = manager.get_filepath_for_return_period(return_periods[-1])

        if TMAX is None:
            logging.error("The file for the maximum return period is missing")
            return

        match_vulnerability2sim(manager.SA_MASKED_RIVER,    manager.OUT_MASKED_RIVER,   TMAX)
        match_vulnerability2sim(manager.SA_VULN,            manager.OUT_VULN,           TMAX)
        match_vulnerability2sim(manager.SA_CODE,            manager.OUT_CODE,           TMAX)
        done.append(steps_vulnerability.MATCH_SIMUL)

    if 4 in steps or steps_vulnerability.APPLY_SCENARIOSVULN in steps:
        if os.path.exists(manager.OUT_VULN):
            existence=False
            existence, fail = manager.create_vrtIfExists(manager.OUT_VULN, manager.IN_CH_SA_SC, manager.OUT_VULN_VRT, name="vuln")
            if existence == None:
                logging.error(_(f"Error in MNT_ files type : {fail}. Please correct them (int8 and Null value = 127)."))
                return done.append(steps_vulnerability.APPLY_SCENARIOSVULN_BUG)
            
            elif existence == True :
                manager.translate_vrt2tif(manager.OUT_VULN_VRT, manager.OUT_VULN_S)
                logging.info("Scenarios have been applied to the vulnerability matrix see _scenarios")
        else :
            logging.error(f"The baseline vulnerability does not exist ({manager.OUT_VULN}). Please, compute first the vulnerability without scenarios vuln_.")
        done.append(steps_vulnerability.APPLY_SCENARIOSVULN)
        
    #Delete _scenario folder is no scenario
    if os.path.isdir(manager.OUT_WITHVULN) and not os.listdir(manager.OUT_WITHVULN):
            os.rmdir(manager.OUT_WITHVULN)
    return done

def Acceptability(main_dir:str = 'Vesdre',
                  scenario:str = 'Scenario1',
                  Study_area:str = 'Bassin_Vesdre.shp',
                  coeff_auto:bool = True,
                  Ponderation_csv:str = 'Ponderation.csv',
                  resample_size:int = 100,
                  steps:list[int] | list[steps_acceptability] = [1,2,3,4,5,6]):
    """ Compute acceptability for the scenario """

    done = []

    manager = Accept_Manager(main_dir,
                             Study_area,
                             scenario=scenario,
                             Ponderation_csv=Ponderation_csv)

    # Load the vulnerability raster **for the scenario**, and check if an assembly exists and is asked by the user
    # Initialization of lists to read/ write according to the needed steps
    VulneToCompute, PathsToSaveA, PathsToSaveA100 = [], [], []
    if 4 in steps or steps_acceptability.COMPUTE_BASELINE_WITHOUT_SCENARIOS in steps:
        VulneToCompute.append(manager.OUT_VULN)
        PathsToSaveA.append(manager.OUT_ACCEPT)
        PathsToSaveA100.append(manager.OUT_ACCEPT_RESAMP)
        river_trace = manager.OUT_MASKED_RIVER

    if 5 in steps or steps_acceptability.COMPUTE_WITH_SCENARIOS in steps:
        river_trace = manager.wich_river_trace(True)
        change_vuln_files = [Path(a) for a in glob.glob(str(manager.IN_CH_SA_SC / "vuln_*.tif")) + glob.glob(str(manager.IN_CH_SA_SC / "vuln_*.tiff"))]
        if len(change_vuln_files) != 0:
            VulneToCompute.append(manager.OUT_VULN_Stif)
            PathsToSaveA.append(manager.OUT_ACCEPT_Stif)
            PathsToSaveA100.append(manager.OUT_ACCEPT_RESAMP_Stif)
        else :
            logging.info("No vulnerability rasters in CHANGE_VULNE. The code goes on without them.")

    if len(VulneToCompute) == 0:
        logging.error("No vulnerability rasters to compute acceptability. Please, compute the vulnerability first.")
        return done

    for i in range(len(VulneToCompute)) :
        vulne = gdal.Open(str(VulneToCompute[i]))
        saveA = PathsToSaveA[i]
        saveA100 = PathsToSaveA100[i]
        # Load the river mask
        riv = gdal.Open(str(river_trace))

        # Get the geotransform and projection for the output tiff
        geotrans = riv.GetGeoTransform()
        proj = riv.GetProjection()

        assert vulne.GetGeoTransform() == riv.GetGeoTransform(), "The geotransform of the two rasters is different"
        assert vulne.GetProjection() == riv.GetProjection(), "The projection of the two rasters is different"

        # Convert to numpy array
        vulne = vulne.GetRasterBand(1).ReadAsArray()
        riv   = riv.GetRasterBand(1).ReadAsArray()

        # Get the return periods available
        return_periods = manager.get_return_periods()

        # Prepare the river bed filter
        # Useful as we iterate over the return periods
        # and the river bed is the same for all return periods
        ij_riv = np.argwhere(riv == 1)

        # Initialize the dictionary to store the acceptability values
        part_accept = {}

        if 1 in steps or steps_acceptability.COMPUTE_LOCAL_ACCEPT in steps:
            # Compute acceptability for each return period
            message="Some adjustments have been done :"
            message2=""
            for curT in tqdm(return_periods):
                # Load the **FILLED** modelled water depth for the return period
                model_h = gdal.Open(str(manager.get_sim_file_for_return_period(curT)))
                # Convert to numpy array
                model_h = model_h.GetRasterBand(1).ReadAsArray()

                assert model_h.shape == vulne.shape, "The shape of the modelled water depth is different from the vulnerability raster"

                # Set 0. if the water depth is 0.
                model_h[model_h == 0] = 0
                # Set 0. in the river bed
                model_h[ij_riv[:,0], ij_riv[:,1]] = 0

                assert model_h[ij_riv[0][0], ij_riv[0][1]] == 0, "The river bed is not set to 0 in the modelled water depth"
                assert model_h.max() > 0, "The maximum water depth is 0"
                if model_h.min() < 0:
                    message2+= f"\nFor T{curT}, the minimum water depth is negative - {np.count_nonzero(model_h<0)} cells, these values were set to 0."
                    model_h[model_h < 0] = 0
                #logging.info("Return period {}".format(curT))
                # Compute the local acceptability for the return period
                part_accept[curT] = compute_acceptability(manager, model_h, vulne, curT, (geotrans, proj))
            if message2 != "":
                logging.error(message + message2)
            done.append(steps_acceptability.COMPUTE_LOCAL_ACCEPT)

            # At this point, the local acceptability for each return period is computed
            # and stored in tiff files in the TEMP/SutyArea/scenario/Q_FILES directory.
            # The arrays are also stored in the part_accept dictionary.

        if 2 in steps or steps_acceptability.LOAD_FROM_FILES in steps:
            # Load/Reload the acceptability values from files

            if 1 in steps or steps_acceptability.COMPUTE_LOCAL_ACCEPT in steps:
                # We have computed/updted the acceptibility values.
                # We do not need to reload them.
                logging.warning("The acceptability values have been computed in step 1 – reloading is unnecessary. To avoid this, exclude step 1.")
            else:

                # Get the list of Q files
                qs = manager.get_q_files()

                # Iterate over the return periods
                for curT in return_periods:
                    #logging.info(curT)

                    # We set the filename from the return period, not the "qs" list
                    q_filename = manager.TMP_QFILES / "Q{}.tif".format(curT)

                    # Check if the file exists
                    assert q_filename.exists(), "The file {} does not exist".format(q_filename)
                    # Check if the file is in the "qs" list
                    assert q_filename in qs, "The file {} is not in the list of Q files".format(q_filename)

                    # Load the Q file for the return period
                    tmp_data = gdal.Open(str(q_filename))
                    # Convert to numpy array
                    part_accept[curT] = tmp_data.GetRasterBand(1).ReadAsArray()

            done.append(steps_acceptability.LOAD_FROM_FILES)

        if 3 in steps or steps_acceptability.COMPUTE_MEAN_ACCEPT in steps:

            assert len(part_accept) == len(return_periods), "The number of acceptability files is not equal to the number of return periods"

            # Pointing the last return period, maybe 1000 but not always
            array_tmax = part_accept[return_periods[-1]]

            # Get ponderations for the return periods
            if coeff_auto:
                logging.info("Automatic ponderation")
                pond = manager.get_ponderations()
                assert pond["Ponderation"].sum() > 0.999999 and pond["Ponderation"].sum()<1.0000001, "The sum of the ponderations is not equal to 1"

            elif manager.is_valid_ponderation_csv:
                logging.info("Manual ponderation")
                # Load the ponderation file
                pond = pd.read_csv(manager.PONDERATION_CSV)
                # Set the index to the interval, so we can use the interval as a key
                pond.set_index("Interval", inplace=True)

            else:
                logging.error("The ponderation file is missing")
                logging.info("Please provide the ponderation file or set 'coeff_auto' to True")
                return -1

            assert len(pond) == len(return_periods), "The number of ponderations is not equal to the number of return periods"

            # Initialize the combined acceptability matrix -- Ponderate mean of the local acceptability
            comb = np.zeros(part_accept[return_periods[0]].shape, dtype=np.float32)
            
            for curT in return_periods:
                assert part_accept[curT].dtype == np.float32, "The dtype of the acceptability matrix is not np.float32"
                assert part_accept[curT].shape == comb.shape, "The shape of the acceptability matrix is not the right one"

                comb += part_accept[curT] * float(pond["Ponderation"][curT])

            y_pixels, x_pixels = comb.shape

            driver = gdal.GetDriverByName('GTiff')

            dataset = driver.Create(
                str(saveA),
                x_pixels, y_pixels,
                1,
                gdal.GDT_Float32,
                options=["COMPRESS=LZW"]
            )

            assert comb.dtype == np.float32, "The dtype of the combined acceptability matrix is not np.float32"

            dataset.SetGeoTransform(geotrans)
            dataset.SetProjection(proj)
            band = dataset.GetRasterBand(1)
            band.WriteArray(comb)
            band.FlushCache()
            dataset.SetGeoTransform(geotrans)
            dataset.SetProjection(proj)
            dataset = None

            done.append(steps_acceptability.COMPUTE_MEAN_ACCEPT)

        if 6 in steps or steps_acceptability.RESAMPLING in steps:
            if os.path.exists(manager.OUT_ACCEPT):
                Agg = gdal.Warp(str(saveA100),
                                str(saveA),
                                xRes=resample_size,
                                yRes=resample_size,
                                resampleAlg='Average')
                Agg.FlushCache()
                Agg = None
            else :
                logging.error(f"The acceptability without resampling does not exist ({manager.OUT_ACCEPT}). Please, compute it first to agglomerate it afterwards.")
        if os.path.isdir(manager.OUT_WITHVULN) and not os.listdir(manager.OUT_WITHVULN):
            os.rmdir(manager.OUT_WITHVULN)
    return done