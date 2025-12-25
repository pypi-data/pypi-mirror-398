from pathlib import Path
import pandas as pd
import numpy as np
import math
import logging
import os
import subprocess
import shutil
import rasterio
from scipy.ndimage import label

from .PyTranslate import _
from .wolf_array import WolfArray, header_wolf
from .Results2DGPU import wolfres2DGPU
from .eikonal import inpaint_waterlevel, inpaint_array


class interpolating_raster():
    def __init__(self):
        pass
    
    def nullvalue_for_hole(self, WA):
        """
        Sets the null value for a WolfArray to 0 (as per the convention in the interpolation routine).
        """
        WA.nullvalue = 0.
        WA.set_nullvalue_in_mask()

    def export_z_or_v_bin(self, fn_read, manager, name, type_hazard="z", type_extraction="danger_map", param_danger = [0,-1,1], threshold:float=0.01):
        """
        Reads the free surface altitude from a GPU simulation and exports it in binary format.

        :param str fn_read_simu: The simulation file to read.
        :param str fn_laststep: The folder ``EXTRACTED_LAST_STEP`` defined in acceptability/INBE.
        :param list param_danger: The time step to extract the results gpu (in order :) to start / end / every X
        :param str fn_write: The path to save the output in binary format.
        :param str type_hazard: Either ``'z'`` for water level only, or ``'z_v'`` for water level and velocity.
        """
        where_wd = Path(manager.IN_SA_EXTRACTED)
        fn_write = Path(where_wd / name )
        if type_extraction == "last_step": 
            wolfres2DGPU_test = wolfres2DGPU(fn_read, eps = threshold)
            wolfres2DGPU_test.read_oneresult(-1)
            wd = wolfres2DGPU_test.get_h_for_block(1)
            #wd.array[wd.array < threshold] = wd.nullvalue
            top = wolfres2DGPU_test.get_top_for_block(1)
            #i, j = np.where(wd.array < threshold)
            #top.array[i, j] = top.nullvalue
            self.nullvalue_for_hole(wd)
            self.nullvalue_for_hole(top)
            wd.array = wd.array + top.array
            fn_write = fn_write.with_suffix('.bin')
            wd.write_all(fn_write)
        else:
            if type_hazard == "z" :
                danger_maps = wolfres2DGPU(fn_read, eps = threshold).danger_map_only_h(param_danger[0], param_danger[1], param_danger[2])
                fn_write = fn_write.with_suffix('.bin')
                danger_maps.write_all(fn_write)
            if type_hazard == "z_v" :
                danger_maps = wolfres2DGPU(fn_read, eps = threshold).danger_map(param_danger[0], param_danger[1], param_danger[2])
                fn_write = fn_write.with_suffix('.bin')
                danger_maps[3].write_all(fn_write)

                where_v = manager.IN_SCEN_DIR_V
                where_v = Path(where_v) / f"v_danger_{name}_{manager.scenario}.tif"
                danger_maps[1].write_all(where_v)

    def riverbed_trace(self, fn_read_simu, fn_output, threshold, type_extraction="danger_map"):
        """
        Recognizes the riverbed trace based on a simulation, where water depth above a given threshold is considered part of the riverbed.

        :param str fn_read_simu: The simulation file to read.
        :param str fn_output: The location to save the riverbed trace as a ``.tiff`` file.
        :param float threshold: The water depth threshold above which the areas are considered riverbed.
        """
        
        if type_extraction == "last_step":
            wolfres2DGPU_test = wolfres2DGPU(fn_read_simu)
            wolfres2DGPU_test.read_oneresult(-1)
            wd = wolfres2DGPU_test.get_h_for_block(1)
            wd.array[wd.array > 1000] = 0
            wd.array[wd.array > threshold] = 1
            wd.array[wd.array < threshold] = 0
            wd.as_WolfArray()
            wd.nodata=0
            wd.write_all(Path(fn_output))

        else:
            wd = wolfres2DGPU(fn_read_simu).danger_map_only_h(0,-1,1)
            wd.array[wd.array > 1000] = 0
            wd.array[wd.array > threshold] = 1
            wd.array[wd.array < threshold] = 0
            wd.as_WolfArray()
            wd.nodata=0
            wd.write_all(Path(fn_output))


    def empty_folder(self, folder):
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

    """
    This script performs two main operations:

    1. Subtraction of two raster TIFF files:
    - Identifies areas with building traces by subtracting the `bathymetry.tif` from simulations
        (corresponding to 'MNT_muret_bati') from `MNT` (DEM).

    2. For the identified building areas (from step 1):
    - Replace the values with those from the `MNT` (ground level), ensuring it reflects the terrain, not bathymetry values.

    Final Output:
    - The mask should highlight building traces with corresponding DEM (`MNT`) values ("ground") inside, and its name must start with "MNT_" and include "mask" in it.

    Note: the computations are perfomed with tifs .tif rasters but should be translated to .bin files in the acceptability routine
    """

    #----------------------------------------------------------------------------------------------------------

    #1 - Soustraction bathymetry.tif (from simulations) - DEM (MNT, cfr "projet tuilage") ---------------------

    def soustraction(self, fn_a, fn_b,fn_result):
        with rasterio.open(fn_a) as src_a, rasterio.open(fn_b) as src_b:
            if (
                src_a.width != src_b.width or
                src_a.height != src_b.height or
                src_a.transform != src_b.transform or
                src_a.crs != src_b.crs
            ):
                logging.error(f"{fn_a} and {fn_b} do not have the same properties, please edit them.")


            data_a = src_a.read(1)
            data_b = src_b.read(1)
            
            #(A - B)
            data_diff = data_a - data_b
            nodata_value = src_a.nodata if src_a.nodata == src_b.nodata else None
            if nodata_value is not None:
                data_diff[(data_a == nodata_value) | (data_b == nodata_value)] = nodata_value

            data_diff[data_diff < 0.5] = 0 #sans ce nettoyage supplémentaire, l'interpolation devient non significative, car de petites valeurs de différence peuvent subsister (cfr simus Vesdre sur 2m).
            data_diff[data_diff > 5000] = 0
            labeled, n = label(data_diff)
            # Remove small objects
            threshold = 5
            sizes = np.bincount(labeled.ravel())
            idx_small = np.where(sizes <= threshold)[0]
            data_diff[np.isin(labeled, idx_small)] = 0

            out_meta = src_a.meta.copy()
            out_meta.update({
                "dtype": "float32",
                "driver": "GTiff"
            })

        with rasterio.open(fn_result, "w", **out_meta) as dst:
            dst.write(data_diff, 1)


    #2 - DEM (MNT) value in the buildings traces ------------------------------------------------------------------
    def mask_creation_data(self, mask_file, ground_file, output_file):
        with rasterio.open(mask_file) as mask_src:
            mask = mask_src.read(1).astype('float32')
            mask_meta = mask_src.meta

        indices = np.where(mask > 0)

        with rasterio.open(ground_file) as bathy_src:
            bathy = bathy_src.read(1)

        mask[indices] = bathy[indices]
        mask[mask <= 0] = 99999.

        output_meta = mask_meta.copy()
        output_meta.update({"dtype": 'float32'})

        with rasterio.open(output_file, "w", **output_meta) as dst:
            dst.write(mask, 1)

        WA_mask = WolfArray(output_file)
        WA_mask.write_all(Path(Path(output_file).parent / "MNT_computed_with_mask.bin"))

    def MNT_and_mask_creation_all(self, fn_bathy, fn_mtn_cropped, fn_where_buildings, fn_mask_final):
        #couper_raster()
        self.soustraction(fn_bathy, fn_mtn_cropped, fn_where_buildings)
        self.mask_creation_data(fn_where_buildings, fn_mtn_cropped, fn_mask_final)
        
    def empty_folder(self, folder):
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
    

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #une classe qui lit les routines holes.exe, pour un répertoire d'entrée (on y placera un répertoire de danger maps OU de simu, puis danger) et de sortie (on y placera INPUT....)
    # Interpolation
    # -------------

    def batch_creation_and_interpolation_fotran_holes(self, manager, checked_paths:list[Path], iftest:bool) -> tuple[bool, list[str]]:
        """Creates a batch file to launch holes.exe from the selected simulations and launches it.

        - Every files in EXTRACTED_LAST_STEP are interpolated for tests (iftest==True).
        - Only the check simulations of the windows are interpolated for the GUI (iftest!=True).

        :param checked_paths: list of paths to the checked simulations
        :param iftest: boolean to indicate if the function is called from the tests or not
        """

        path_LastSteps = Path(manager.IN_SA_EXTRACTED)

        # Identifying the DEM and its mask
        C = None # DEM mask
        D = None # DEM
        for file in os.listdir(Path(manager.IN_SA_DEM)):
            file_path = Path(manager.IN_SA_DEM) / file
            if file_path.is_file() and file.startswith("MNT_") and file_path.suffix == ".bin":
                if "mask" not in file:
                    D = file_path
                else:
                    C = file_path

        if D is None:
            return logging.error(_("DEM (.bin) not found in DEM_FILES. The file must begins by 'MNT_' and CANNOT include the word 'mask'"))

        if C is None:
            return logging.error(_("DEM mask (.bin) not found in DEM_FILES. The file must begins by 'MNT_' and MUST include the word 'mask'"))

        path_Interp =  Path(manager.IN_SA_INTERP)
        path_bat_file = os.path.join(manager.IN_SCEN_DIR, "process_files.bat")

        if os.path.exists(path_bat_file):
            logging.info(f"The file {path_bat_file} already exists and will be replaced.")
            os.remove(path_bat_file)

        path_code = os.path.join(manager.IN_WATER_DEPTH, "holes.exe")

        A, B = [], []
        if iftest:
            # no checked box in the tests
            A = [path_LastSteps / f for f in os.listdir(path_LastSteps) if f.endswith('.bin') and not f.endswith('.bin.txt')] 
        else :
            for path in checked_paths:
                parts = path.name.split("sim_")
                A.extend([path_LastSteps / g for g in os.listdir(path_LastSteps) if g.endswith(f"{parts[1]}.bin")])

        B = [path_Interp / f.stem for f in A] 
        
        if not A or not B or not C or not D:
            logging.error(("Missing files."))
            return None, None

        with open(path_bat_file, "w") as bat_file:
            for a, b in zip(A, B):
                line = f'"{path_code}" filling in="{a}" out="{b}" mask="{C}" dem="{D} avoid_last=1"\n'
                bat_file.write(line)

        self.empty_folder(manager.IN_SA_INTERP)
        path_bat_file = manager.IN_SCEN_DIR / "process_files.bat"
        subprocess.run([path_bat_file], check=True)

        renamed_files = []
        path_fichier = manager.IN_SA_INTERP
        for file in path_fichier.glob("*.tif"):
            if "_h" in file.name:
                new_name = file.stem.split("_h")[0].replace(".bin", "") + ".tif"
                file.rename(file.with_name(new_name))
                renamed_files.append(new_name)

        #deleting the other
        for file in path_fichier.glob("*.tif"):
            if "_combl" in file.name or file.name not in renamed_files:
                file.unlink()

        return True, renamed_files

    def batch_creation_and_interpolation_python_eikonal(self, manager, checked_paths:list[Path], iftest:bool, ifwd=False) -> tuple[bool, list[str]]:
        """Creates a batch file to launch holes.exe from the selected simulations and launches it.

        - Every files in EXTRACTED_LAST_STEP are interpolated for tests (iftest==True).
        - Only the check simulations of the windows are interpolated for the GUI (iftest!=True).

        :param checked_paths: list of paths to the checked simulations
        :param iftest: boolean to indicate if the function is called from the tests or not
        """
        path_LastSteps = Path(manager.IN_SA_EXTRACTED)
        # Identifying the DEM and its mask
        C = None # DEM mask
        D = None # DEM
        for file in os.listdir(Path(manager.IN_SA_DEM)):
            file_path = Path(manager.IN_SA_DEM) / file
            if file_path.is_file() and file.startswith("MNT_") and file_path.suffix == ".bin":
                if "mask" not in file:
                    D = file_path
                else:
                    C = file_path

        if D is None:
            return logging.error(_("DTM (.bin) not found in DTM_FILES. The file must begins by 'MNT_' and CANNOT include the word 'mask'"))

        if C is None:
            return logging.error(_("DEM mask (.bin) not found in DEM_FILES. The file must begins by 'MNT_' and MUST include the word 'mask'"))

        path_Interp =  Path(manager.IN_SA_INTERP)
        path_bat_file = os.path.join(manager.IN_SCEN_DIR, "process_files.bat")

        if os.path.exists(path_bat_file):
            logging.info(f"The file {path_bat_file} already exists and will be replaced.")
            os.remove(path_bat_file)

        A, B = [], []
        if iftest:
            # no checked box in the tests
            A = [path_LastSteps / f for f in os.listdir(path_LastSteps) if f.endswith('.bin') and not f.endswith('.bin.txt')]

        else :
            for path in checked_paths:
                parts = path.name.split("sim_")
                A.extend([path_LastSteps / g for g in os.listdir(path_LastSteps) if g.endswith(f"{parts[1]}.bin")])

        B = [path_Interp / f.stem for f in A]
        if not A or not B or not C or not D:
            logging.error(_("Missing files."))
            return None, None
        renamed_files = []
        for a, b in zip(A, B):
            wa_a = WolfArray(a)
            wa_c = WolfArray(C)
            wa_d = WolfArray(D)
            _t, _d, wh = inpaint_array(data = wa_a.array,
                          where_compute = wa_c.array.data != wa_c.array.data[0,0],
                          test = wa_d.array.data,
                          ignore_last_patches= 1)

            new_name = b.with_suffix(".tif")
            if ifwd == True : 
                wa_a = wa_a - wa_d
            wa_a.write_all(new_name)
            renamed_files.append(new_name.name)

        return True, renamed_files