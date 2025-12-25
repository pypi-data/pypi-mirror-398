"""Imports et bons paths"""
import os
import sys
_root_dir = os.getcwd()
original_sys_path = sys.path.copy()
sys.path.insert(0, os.path.join(_root_dir, r"..\.."))

from wolfhece.PyVertexvectors import Zones, zone, vector, wolfvertex
from wolfhece.picc import Picc_data, bbox_creation
from wolfhece.wolf_array import WolfArray
from wolfhece.Results2DGPU import wolfres2DGPU
import geopandas as gpd  
import logging
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wolfhece.wolf_vrt import create_vrt_from_diverged_files_first_based, translate_vrt2tif
from wolfhece.wolf_array import WolfArray
from wolfhece.PyTranslate import _
from osgeo import gdal


#Other repository : hece_damage-------------------------------------------------------------
_root_dir = os.path.dirname(os.path.abspath(__file__))
hece_damage_path = os.path.abspath(os.path.join(_root_dir, "..", "..", "..", "hece_damage"))
sys.path.insert(0, hece_damage_path)
try:
    from insyde_be.Py_INBE import PyINBE, INBE_Manager
    print("Import OK")
except Exception as e:
    logging.error(_(f"Problem to import insyde_be.Py_INBE: {e}"))
try:
    from insyde_be.Py_INBE import PyINBE, INBE_Manager
    print("Import OK")
except Exception as e:
    logging.error(_(f"Problem to import insyde_be.Py_INBE: {e}"))
sys.path.pop(0)

class INBE_functions():
    def __init__(self):
        pass
    
    # Assembly (FR : agglomération)
    # -----------------------------
    """Basically the same operations as in the config manager to agglomerate several rasters
    The class Config_Manager_2D_GPU is called, however some functions were rewritten to allow
    the search of a more specific word ('vuln', and not 'bath', 'mann', or 'inf').
    """

    def tree_name_tif(self, folder_path, name):
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
        tiff_trees = self.tree_name_tif(folder_path, name)
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

    def check_nodata(self, name, path_baseline, fn_scenario):
        """ Check nodata in a path """
        from ..wolf_array import WOLF_ARRAY_FULL_INTEGER8
        list_tif, unused = self.select_name_tif(path_baseline, fn_scenario, name)
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
        self.check_nodata(name, fn_baseline, fn_scenario)
        list_tif, list_fail = self.select_name_tif(fn_baseline, fn_scenario, name, filter_type = True)
        if len(list_fail)>0:
                return False, list_fail
        #création du fichier vrt - assembly/agglomération
        if len(list_tif)>1:
            logging.info(_('Creating .vrt from files (first based)...'))
            if name == "vuln_":
                create_vrt_from_diverged_files_first_based(list_tif, fn_vrt, Nodata = 127)
            else:
                create_vrt_from_diverged_files_first_based(list_tif, fn_vrt)
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

        logging.info(_("All the existing .tif files have been copied to the destination directory."))
    
    # Divers
    def name_existence(self, Zones1, key, name):
        names = [str(curzone.get_values(key)[0]) for curzone in Zones1.myzones]
        if (str(name) in names):
            print(f'There exists objects with name {name}.')
        else :
            print(f'No objects with name {name}')
            
    def PICC_read(self, manager_inbe, name:str = "Habitation"):
        study_area_path =  Path(manager_inbe.IN_STUDY_AREA) /  manager_inbe._study_area
        bbox = bbox_creation(study_area_path)
        
        _picc_data = Picc_data(data_dir=Path(),bbox=bbox)
        path_vector = Path(manager_inbe.IN_DATABASE) / "PICC_Vesdre.shp"
        if not path_vector.exists():
            return None, None
        
        zones_hab = _picc_data.create_zone_picc(path_vector = path_vector, path_points = Path(manager_inbe.IN_DATABASE)  / "PICC_Vesdre_points.shp", name=name, column = "GEOREF_ID", bbox=bbox)  
        return zones_hab, zones_hab.nbzones, bbox
        
    def create_table_wolfsimu_INTERPWD(self, manager_inbe, simu, operator_wd:str, ZonesX:Zones, Zones_v:Zones = None, percentil:float=None, title: str = "table_wolfsimu.xlsx"):
        """Creates the minimum inputs needed for INBE based on the simulations. One table per simulations."""
        where_wd = manager_inbe.IN_SA_INTERP 
        where_v = manager_inbe.IN_SCEN_DIR_V
        out= manager_inbe.IN_CSV_SCEN
        out = Path(out) / title.replace(".xlsx", f"_{simu}.xlsx")
        
        colonnes = [
            "code", "he_max", "he_out", "h_gf", "v", "date_arr_base",
            "date_leave_base", "no_s", "no_q", "FA", "NF", "GL", "YY", "Y_renov", "EP"
        ]
        df = pd.DataFrame(columns=colonnes)
        
        where_v = Path(where_v) / f"v_danger_{simu}_{manager_inbe.scenario}.tif" 

        simu_path = simu + ".tif"
        print(f"where_v : {where_v}")
        print(f"where_wd : {Path(where_wd) / simu_path}")
        if not ((Path(where_wd) / simu_path).exists() and (where_v).exists()):
            return print(f"Files of water depths and/or velocities does not exist.")
        
        WA_wd = WolfArray(where_wd / simu_path)
        WA_v = WolfArray(where_v)
        
        #Exclure le mask dilaté (car pas plein bord...) de la rivière !
        WA_river = WolfArray(manager_inbe.IN_RIVER_MASK_SCEN_tif)
        i,j = np.where(WA_river.array.mask == False)    
        WA_wd.array[i,j] = WA_wd.nodata
        WA_v.array[i,j] = WA_v.nodata
        
        i = 0
        val_h = 0
        logging.info(_("Scanning zone for water depth inside buildings."))
        for curzone in tqdm(ZonesX.myzones):
            for curvector in curzone.myvectors:
                if i >= ZonesX.nbzones:
                    break
                wd_values = WA_wd.get_values_insidepoly(curvector)
                
                if np.all(len(wd_values[0]) != 0):#np.all(len(wd_values[0]) != 0): #critère sur WD #statistics WA
                    if operator_wd == "mean":
                        val_h = wd_values[0].mean()
                    elif operator_wd == "max":
                        val_h = wd_values[0].max()
                    elif operator_wd == "median":
                        val_h = np.median(wd_values[0])
                    elif operator_wd == "percentil":
                        if percentil != None:
                            val_h = np.quantile(wd_values[0], percentil / 100)
                        else:
                            logging.error(_(f"Bad value for percentil {percentil}"))
                            return
                    else:
                        logging.error(_("To be coded."))
                        
                    if val_h !=0: 
                        df.loc[i, "code"] = str(curvector)
                        df.loc[i, "he_out"] = val_h
                        df.loc[i, "FA"] = curzone.area
                        curvector.update_lengths()
                        df.loc[i, "EP"] = curvector.length2D#perimeters[0]
                        i += 1
                        
        if Zones_v != None : #Si prise en compte de la vitesse, alors demande de parcourir un objet Zones avec buffer (autre loop necessaire)
            logging.info(_("Scanning zone for velocity along the buffers."))
            for curzone_v in tqdm(Zones_v.myzones):
                for curvector_v in curzone_v.myvectors:
                    if i >= Zones_v.nbzones:
                        break
                    if str(curvector_v) in df['code'].astype(str).values:
                        v_values = WA_v.get_values_insidepoly(curvector_v, usemask=False)
                        v_values[0][v_values[0] == -99999] = 0
                        if len(v_values[0]) != 0:
                            if v_values[0].max() != 0 :
                                df.loc[df['code'] == str(curvector_v), "v"] = v_values[0].max()
                        else :
                            print("No v_values")
        try:    
            df.to_excel(out, index=False)
        except PermissionError:
            logging.error(_(f"Permission denied: please ensure the file '{out.name}' is not open in another program."))
            return
        
    def pre_processing_auto(self, Ti_list, main_dir, Study_area, scenario, multiple, dx, percentil = None, operator_wd = "mean", hazard = "both"):
        manager_inbe = INBE_Manager(main_dir=main_dir, Study_area=Study_area, scenario = scenario)

        """Création bbox par Polygon pour la classe Zone et lecture du PICC"""
        if hazard == "both":
            """Prise en compte de la vitesse, via buffer"""
            """Buffer """
            Zones_reading, unused, unused = self.PICC_read(manager_inbe, "Habitation")
            
            """Buffer creation"""
            dx_buffer = multiple #multiple de la resolution topo
            dx_buffer = multiple*dx
            Zones_v = Zones_reading.buffer(distance = dx_buffer, resolution= 4, inplace = False)
            #Zones_v.saveas(filename = r"C:\Users\damien\Desktop\test_zone_reading.shp")

        elif hazard == "wd":
            """Seulement water_depth, pas de vitesse"""
            Zones_reading, unused, unused = self.PICC_read(manager_inbe, "Habitation")
            Zones_v = None
        
        save_where_output = []
        for curT in Ti_list:
            print(f"----------------------------> Computing input table for {curT}")
            #create_table_wolfsimu_BUFFERWD(manager_inbe = manager_inbe, simu=curT, ZonesX= Zones_reading, Zones_v = Zones_reading2)
            self.create_table_wolfsimu_INTERPWD(manager_inbe = manager_inbe, simu=curT, operator_wd = operator_wd, ZonesX= Zones_reading, Zones_v = Zones_v, percentil=percentil)
            print(f"--Preprocessing table created in {manager_inbe.IN_CSV_SCEN}")
            save_where_output.append(manager_inbe.IN_CSV_SCEN)
        return save_where_output
            
        
    def computation_dfresults(self, input_table,type_computation, inflation):
        Pyinsyde = PyINBE(input_table=input_table)
        df_results,unused,unused,unused,unused,unused,unused,unused,df_input = Pyinsyde.run_R_insyde(type_computation=type_computation, inflation=inflation)
        df_ifvalue = df_results[df_results['d_total'] > 0]
        return df_ifvalue, df_input

    def computation_combined_damage(self, pond: dict, manager_inbe) -> pd.DataFrame:
        """
        ! Première version assez basique

        Compute the weighted sum of damage results across multiple return‑period DataFrames.

        :param df_results_Ti: Dictionary mapping return‑period keys (e.g. "T2", "T5", ...) to pandas DataFrames.
            Each DataFrame must have a "code" column identifying each building and one or more numeric columns representing damage categories.
        :type df_results_Ti: dict
        :param pond: Dictionary mapping the same return‑period keys to their weighting coefficients (e.g. {"T2": 0.65, "T5": 0.216667, ...}).
        :type pond: dict
        :return: A DataFrame with one row per unique building "code" (coordinate of the center of the polygon), containing the column "code"
            plus each damage category column equal to the weighted sum across all Ti.
        :rtype: pd.DataFrame
        """
        df_results_Ti = manager_inbe.get_individualdamage()
        weighted_dfs = []
        for Ti, df in df_results_Ti.items():
            coeff = pond.loc[int(Ti), "Ponderation"]
            df_w = df.copy()
            # Multiplying by the weigting coeff
            numeric_cols = df_w.select_dtypes(include="number").columns
            df_w[numeric_cols] = df_w[numeric_cols].mul(coeff)
            weighted_dfs.append(df_w)

        # Grouping and summing thanks to 'code' whioch
        all_concat = pd.concat(weighted_dfs, ignore_index=True, sort=False)
        final_df = all_concat.groupby("code", as_index=False).sum()
        output_path = manager_inbe.OUT_COMB #Path(manager_inbe.OUT_SCEN_DIR) / f"combined_damage.xlsx"
        try:
            with open(output_path, 'wb') as f:
                pass
            final_df.to_excel(output_path, index=False)
        except PermissionError:
            logging.error(_(f"Permission denied: please ensure the file '{output_path}' is not open in another program."))
            return
                
        return final_df, output_path
        
    def plot_damage(self, df_results, idx=None, cat=None, sorted_cond=None):
        """
        Displays a damage bar chart for a specific index (specific building) or for all entries, and for all
        damage categories or only one.

        :param df_results: DataFrame containing damage computed by INBE.
        :type df_results: pd.DataFrame
        :param idx: Index of a specific row to plot. Defaults to None (every building plotted).
        :type idx: int, optional
        :param cat: Specific damage category to plot if idx is None (global mode). Defaults to None (every category plotted).
        :type cat: str, optional
        """

        with plt.rc_context({'text.usetex': True, 'font.size': 18, 'font.family': 'serif'}):
            plt.rcParams.update({'text.usetex': False})
            labels = ['d_cleaning', 'd_removal', 'd_non_stru', 'd_structural', 'd_finishing', 'd_systems']
            labels_latex = [r'$D_{\mathrm{cleaning}}$',r'$D_{\mathrm{removal}}$',r'$D_{\mathrm{non stru}}$',r'$D_{\mathrm{structural}}$',r'$D_{\mathrm{finishing}}$',r'$D_{\mathrm{systems}}$']

            if cat is not None:
                labels = [cat]

            if sorted_cond == True:
                df_sorted = df_results.sort_values('d_total')
                df_plot = df_sorted
            else:
                df_plot = df_results            

            fig, ax = plt.subplots(figsize=(8,6))

            if idx is not None:
                values = [df_plot[label][idx] / 1e3 for label in labels]

                x = np.arange(len(labels))
                colors = plt.cm.tab10.colors[:len(labels)]
                bars = ax.bar(x, values, color=colors, alpha=0.6)
                ax.set_xticks(x)
                ax.set_xticklabels(labels, rotation=45)
                ax.tick_params(axis='y', labelsize=13)
                ax.set_xlabel("Categories of damage [-]")
                ax.set_ylabel("d_total [10³€]", fontsize=13)
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            else:
                combined = list(zip(labels, labels_latex))
                combined_sorted = sorted(combined, key=lambda x: df_plot[x[0]].sum(), reverse=True)
                labels, labels_latex = zip(*combined_sorted)

                colors = plt.cm.tab10.colors[:len(labels)]
                x = np.arange(len(df_plot.index))
                bottom = np.zeros(len(df_plot.index))
                bars = []
                for i, label in enumerate(labels):
                    values = df_plot[label] / 100
                    bar = ax.bar(x, values, bottom=bottom, color=colors[i], label=labels_latex[i], alpha=0.6)
                    bars.append(bar)
                    bottom += values

                ax.set_xticks([])  # pas de ticks sur x
                ax.set_ylabel("Damage [10³€]")
                ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=3, borderaxespad=0.)
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                # Tooltip setup - gadget... mais sympa
                annot = ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w"),
                                    arrowprops=dict(arrowstyle="->"))
                annot.set_visible(False)

                def update_annot(bar, idx_bar):
                    x_mid_data = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2

                    y_pos = bar.get_height() + bar.get_y()

                    annot.xy = (bar.get_x() + bar.get_width() / 2, y_pos)  
                    code = df_plot['code'].iloc[idx_bar]
                    annot.set_text(f"code: {code}")
                    annot.get_bbox_patch().set_alpha(0.8)
                    annot.set_fontsize(10)

                    arrow_disp = ax.transData.transform(annot.xy)
                    fig_width = fig.bbox.width
                    x_text_disp = fig_width / 2
                    y_text_disp = arrow_disp[1] + 15  # décalage vertical 15 pixels

                    annot.set_position((x_text_disp - arrow_disp[0], y_text_disp - arrow_disp[1]))

                def hover(event):
                    vis = annot.get_visible()
                    for bar_group in bars:
                        for i, bar in enumerate(bar_group):
                            if bar.contains(event)[0]:
                                update_annot(bar, i)
                                annot.set_visible(True)
                                fig.canvas.draw_idle()
                                return
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

                fig.canvas.mpl_connect("motion_notify_event", hover)

            plt.tight_layout()
            plt.show()
                

    type_computation = "from_wolfsimu"
    def computation_dfesults_forfolder(self, manager_inbe, type_computation, Ti_list, inflation): #changer nom "for folder" --> "for selected Ti"
        """
        Process Excel files in the folder INPUT>CSVs matching the pattern 'table_wolfsimu_T<number>.xlsx',
        extracts and sorts the T identifiers numerically, computes results (INBE) for each file using
        computation_dfresults, and returns a dictionary of results keyed by each T identifier.

        :param manager_inbe: Object containing the path to the input CSV scenario folder.
        :type manager_inbe: Any
        :param type_computation: Parameter specifying the type of computation to perform.
        :type type_computation: Any
        :param inflation: Inflation parameter used in the computation.
        :type inflation: Any
        :return: Dictionary with keys as T identifiers (e.g., 'T2') and values as computation results.
        :rtype: dict
        """

        df_results = {} #dictionnaire dont la clé sera les Ti dispo dans CSVs
        df_input = {}
        save_output_TEMP = []
        save_output_defaultINPUT = []

        for curT in Ti_list:
            input_table = manager_inbe.IN_CSV_SCEN / ("table_wolfsimu_" + curT + ".xlsx")
            if not input_table.exists():
                logging.error(_(f"Input table table_wolfsimu_{curT}.xlsx does not exist."))
                continue 
            logging.info(_(f"Computing damage for table_wolfsimu{curT}"))
            df_results[curT], df_input[curT] = self.computation_dfresults(input_table, type_computation, inflation)
            output_path = Path(manager_inbe.OUT_SCEN_DIR) / f"individual_damage_{curT}.xlsx"
            try:
                with open(output_path, 'wb') as f:
                    pass
                df_results[curT].to_excel(output_path, index=False)
            except PermissionError:
                logging.error(_(f"Permission denied: please ensure the file '{output_path}' is not open in another program."))
                return
                
            output_path = Path(*output_path.parts[-5:])
            save_output_TEMP.append(output_path)
            output_path = Path(manager_inbe.OUT_SCEN_DIR_IN) / f"input_with_default_data_{curT}.xlsx"
            try:
                with open(output_path, 'wb') as f:
                    pass
                df_input[curT].to_excel(output_path, index=False)
            except PermissionError:
                logging.error(_(f"Permission denied: please ensure the file '{output_path}' is not open in another program."))
                return
                
            output_path = Path(*output_path.parts[-5:])
            save_output_defaultINPUT.append(output_path)
        return df_results, save_output_TEMP, save_output_defaultINPUT
    
    def adding_INBEresults_toZones(self, manager_inbex, Zones_trix, Ti = None):
        cols = ["code", "d_cleaning", "d_removal", "d_non_stru", "d_structural", "d_finishing", "d_systems", "d_total"]
        cols_d = ["d_cleaning", "d_removal", "d_non_stru", "d_structural", "d_finishing", "d_systems", "d_total"]
        if Ti != None:
            path_to_indiv_damage = manager_inbex.OUT_SCEN_DIR / ("individual_damage_" + str(Ti) + ".xlsx")
            df_results = pd.read_excel(path_to_indiv_damage, usecols=cols)
        if Ti == None :
            Ti = None
            df_results = pd.read_excel(manager_inbex.OUT_COMB, usecols=cols)
            
        Zones_torasterize = Zones_trix

        for curzone in tqdm(Zones_torasterize.myzones):
            for curvector in curzone.myvectors:
                row_match = df_results[df_results['code'].astype(str) == str(curvector)]#donne bool
                if not row_match.empty:
                    row = row_match.iloc[0]
                    for key in cols_d:
                        read_value = []
                        read_value.append(str(row[key]))
                        arr = np.array(read_value, dtype=str)
                        curzone.add_values(key=str(key), values=arr)
                #print(f"E.g : pour l'id {curzone.get_values('GEOREF_ID')} on a d = {curzone.get_values('d_total')}")    
        return Zones_torasterize
    
    def label_0_needed(self, Zones1):
        for curzone in tqdm(Zones1.myzones):
            cols_d = ["d_cleaning", "d_removal", "d_non_stru", "d_structural", "d_finishing", "d_systems", "d_total"]
            id_vals = [curzone.get_values(col) for col in cols_d]
            id_clean = [v[0] if isinstance(v, (list, np.ndarray)) else v for v in id_vals]
            
            if all(v is None for v in id_clean):
                for col in cols_d:
                    curzone.add_values(key=col, values=np.array([0], dtype=int))
    
    def raster_damage_in_zones(self, path_damage_out, path_onedanger, Zones_torasterize, scenario, Ti):
        self.label_0_needed(Zones_torasterize) 
        WA_raster = WolfArray(path_onedanger) 
        WA_raster.unmask
        WA_raster.array[WA_raster.array<=99999] = 99999
        
        WA_raster.rasterize_zones_valuebyid(Zones_torasterize, id="d_total", method="linear")
        
        if Ti != None:
            out_title = Path(path_damage_out) / f"inbe_{scenario}_{Ti}.tif"
        else :
            out_title = Path(path_damage_out) / ("raster_" + str(scenario) + ".tif")
        WA_raster.unmask
        WA_raster.nodata=99999
        WA_raster.write_all(out_title)
        return print(f"WolfArray written at {out_title}")
    
    def select_and_count_in_zones(self, Zones1, name):
        comptage = 0
        Zones2=Zones()
        for curzone in Zones1.myzones:
            if str(curzone.get_values("NATUR_DESC")[0]) == str(name): 
                comptage +=1
                Zones2.add_zone(curzone, forceparent = True)
        #print(f"--> Number of {name} : {comptage}")
        return Zones2, comptage

    def raster_auto(self, manager_inbe, which_result, Ti_list=None):
        #1. Lecture du PICC
        Zones_tri,unused,unused = self.PICC_read(manager_inbe, "Habitation")
        if which_result == "individual_damage":
            for Ti in Ti_list:
                logging.info(_(f"Raster creation for {Ti}."))
                #3. """Calcul damage : individual and combined""" --> déjà calculés et save dans excel
                Zones_torasterize = self.adding_INBEresults_toZones(manager_inbe, Zones_tri, Ti = Ti)
                tif_files = list(manager_inbe.IN_SA_INTERP.glob("T*.tif"))
                if not tif_files:
                    logging.error(_(r"Please provide the water depth input."))
                    return
                one_danger = tif_files[0]
                self.raster_damage_in_zones(manager_inbe.OUT_SCEN_DIR, one_danger, Zones_torasterize, manager_inbe.scenario, Ti)
                
        if which_result == "combined" :
            Zones_tri,unused = self.select_and_count_in_zones(Zones_tri, "Habitation") 
            
            tif_files = list(manager_inbe.IN_SA_INTERP.glob("T*.tif"))
            if not tif_files:
                logging.error(_(r"Please provide the water depth input."))
                return
            one_danger = tif_files[0]
            Zones_torasterize = self.adding_INBEresults_toZones(manager_inbe, Zones_tri, Ti = None)
            self.raster_damage_in_zones(manager_inbe.OUT_SCEN_DIR, one_danger, Zones_torasterize, manager_inbe.scenario, None)
            
    def load_quant_sum(self, path, quant):
        d_total = pd.read_excel(path)['d_total']
        p75 = d_total.quantile(quant)
        return d_total[d_total <= p75].sum()

    def extract_scenario_label(self, path_str):
        p = Path(path_str)
        parts = p.parts
        label = None
        for i, part in enumerate(parts):
            if part == "TEMP" or part == "OUTPUT":
                if i + 1 < len(parts):
                    label = parts[i + 2]
                    break
        return label

    def histo_total_from_list(self, list_path, quant):
        damages = []
        labels = []
        colors = []

        base_color = (212/255, 101/255, 10/255)
        alt_colors = [
            (119/255, 147/255, 60/255),
            (127/255, 127/255, 127/255),
            (91/255, 155/255, 213/255),
            (255/255, 192/255, 0/255),
            (255/255, 0/255, 255/255)
        ]
        for i, path in enumerate(list_path):
            D_tot = self.load_quant_sum(path, quant) / 1000
            damages.append(D_tot)
            labels.append(self.extract_scenario_label(path))
            colors.append(base_color if i == 0 else alt_colors[(i - 1) % len(alt_colors)])

        base_damage = damages[0]
        rel_percents = [0]
        for dmg in damages[1:]:
            rel = round(dmg / base_damage * 100 - 100)
            rel_percents.append(rel)

        with plt.rc_context({'text.usetex': False, 'font.size': 16, 'font.family': 'serif'}):
            labels2 = [str(lab) for lab in labels]
            bars = plt.bar(labels2, damages, color=colors)

            ylim_max = max(damages) * 1.15 

            for i in range(1, len(damages)):
                rel = rel_percents[i]
                label = f"+{rel}%" if rel > 0 else f"{rel}%"
                color_txt = 'red' if rel > 0 else 'green'
                plt.text(i, damages[i] + ylim_max*0.02, label, ha='center', color=color_txt, fontsize=20)

            plt.ylabel('Total damage [10³€]')
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.ylim(0, ylim_max)
            plt.tight_layout()
            plt.show()
    

    def scatter_INBE_dtotal(out, manager1, manager2, max_val=None, Ti=None, quant=None):
        #...2 : baseline (...1 is the scenario we compare to ...2)
        if Ti != None:
            path2 = Path(manager1.OUT_SCEN_DIR) / f"individual_damage_T{Ti}.xlsx"
            path1 = Path(manager2.OUT_SCEN_DIR) / f"individual_damage_T{Ti}.xlsx"
            #title = r"$\textrm{" + Ti[1:] + r"-year flood}$"
            title = rf"{Ti}-year flood"
        else : 
            path2 = Path(manager1.OUT_COMB)
            path1 = Path(manager2.OUT_COMB)
            title = r"Combined damage"
        
        df1 = pd.read_excel(path1)
        df2 = pd.read_excel(path2)

        df1 = df1[['code', 'd_total']].copy()
        df2 = df2[['code', 'd_total']].copy()

        df1.rename(columns={'d_total': 'd_total_sc1'}, inplace=True)
        df2.rename(columns={'d_total': 'd_total_sc2'}, inplace=True)

        merged = pd.merge(df1, df2, on='code', how='outer')
        
        if quant != None :
            percentile_sc1 = merged['d_total_sc1'].quantile(quant)
            percentile_sc2 = merged['d_total_sc2'].quantile(quant)

            # Filtrer les données pour ne garder que les valeurs supérieures ou égales au 90ᵉ percentile
            filtered = merged[(merged['d_total_sc1'] <= percentile_sc1) | (merged['d_total_sc2'] <= percentile_sc2)]
            merged=filtered

        #ENSEMBLES
        common = merged[ merged['d_total_sc1'].notna() & merged['d_total_sc2'].notna() ]
        only_sc1 = merged[ merged['d_total_sc1'].notna() & merged['d_total_sc2'].isna() ]
        only_sc2 = merged[ merged['d_total_sc2'].notna() & merged['d_total_sc1'].isna() ]

        only_sc1_filled = only_sc1.copy()
        only_sc1_filled['d_total_sc2'] = 0

        only_sc2_filled = only_sc2.copy()
        only_sc2_filled['d_total_sc1'] = 0
        
        #COLOUR
        #colors_common = [get_color(x, y) for x, y in zip(common['d_total_sc2'], common['d_total_sc1'])]
        #colors_sc1 = [get_color(x, y) for x, y in zip(only_sc1_filled['d_total_sc2'], only_sc1_filled['d_total_sc1'])]
        #colors_sc2 = [get_color(x, y) for x, y in zip(only_sc2_filled['d_total_sc2'], only_sc2_filled['d_total_sc1'])]
        
        with plt.rc_context({'text.usetex': False, 'font.size': 16, 'font.family': 'serif'}):
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.scatter(common['d_total_sc2'], common['d_total_sc1'], marker = 'x', color='black')#colors_common, label='Both scenarios')
            ax.scatter(only_sc1_filled['d_total_sc2'], only_sc1_filled['d_total_sc1'], marker = 'x', color='black')#colors_common s=45, facecolors='none',  color=colors_sc1, marker='s', label=f'Only in {scenario1}')
            ax.scatter(only_sc2_filled['d_total_sc2'], only_sc2_filled['d_total_sc1'], marker = 'x', color='black')#colors_common s=60, facecolors='none', edgecolors=colors_sc2, label=f'Only in {scenario2}')
            
            label2 = manager1.scenario
            label1 = manager2.scenario
            
            #min_val = merged[['d_total_sc1', 'd_total_sc2']].min().min()
            if max_val ==None :
                max_val = merged[['d_total_sc1', 'd_total_sc2']].max().max()
            #common_marker = mlines.Line2D([], [], marker='x', color='black', linestyle='None', markersize=10, label='Both scenarios')
            #sc1_marker = mlines.Line2D([], [], marker='s', color='black', linestyle='None', markersize=10, markerfacecolor='none', label=f'Only in {scenario1}')
            #sc2_marker = mlines.Line2D([], [], marker='o', linestyle='None', markersize=10, markerfacecolor='none', markeredgecolor='black', label=f'Only in {scenario2}')  
            #ax.legend(handles=[common_marker, sc1_marker, sc2_marker])
            
            #Formatting for latex
            #label2_escaped = label2.replace(' ', r'\ ')
            #label1_escaped = label1.replace(' ', r'\ ')
            #xlabel = r"$\textrm{Total damage [€] for }\mathrm{" + label2_escaped + "}$"
            #ylabel = r"$\textrm{Total damage [€] for }\mathrm{" + label1_escaped + "}$"
            #ylabel = r"$\textrm{Scores [-] in }\mathrm{" + label1_escaped + "}$"
            
            xlabel = rf"Total damage [€] for {label2}"
            ylabel = rf"Total damage [€] for {label1}"
            

            plt.plot([0, max_val], [0, max_val], '--', color='grey')    
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.title(title, loc='left')
            plt.grid(True)
            plt.tight_layout()
            #out = Path(out) / f"scatterD_{Ti}_{label1}VS{label2}.PNG"
            #plt.savefig(out, dpi=900)
            plt.show()