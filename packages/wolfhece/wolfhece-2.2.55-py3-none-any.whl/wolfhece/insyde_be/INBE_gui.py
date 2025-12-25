"""
Author: University of Liege, HECE, Damien Sansen
Date: 2025

Copyright (c) 2025 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
import numpy as np
import logging
import shutil
import os
import sys
import glob
from osgeo import gdal, osr
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from pathlib import Path
from scipy.ndimage import label
from gettext import gettext as _
from shapely.geometry import Polygon
from scipy.ndimage import binary_dilation
from itertools import permutations

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from wolfhece.wolf_array import WolfArray, header_wolf
from wolfhece.scenario.config_manager import Config_Manager_2D_GPU
from wolfhece.PyDraw import WolfMapViewer, draw_type
from wolfhece.Results2DGPU import wolfres2DGPU
from wolfhece.PyGui import MapManager
from wolfhece.interpolating_raster import interpolating_raster
from wolfhece.insyde_be.INBE_func import INBE_functions
from wolfhece.PyTranslate import _

BATHYMETRY_FOR_SIMULATION = "__bathymetry_after_scripts.tif"

#Other repository : hece_damage-------------------------------------------------------------
_root_dir = os.path.dirname(os.path.abspath(__file__))
hece_damage_path = os.path.abspath(os.path.join(_root_dir, "..", "..", "..", "hece_damage"))
sys.path.insert(0, hece_damage_path)
try:
    from insyde_be.Py_INBE import PyINBE, INBE_Manager
except Exception as e:
    logging.error(_(f"Problem to import insyde_be.Py_INBE: {e}"))
try:
    from insyde_be.Py_INBE import PyINBE, INBE_Manager
except Exception as e:
    logging.error(_(f"Problem to import insyde_be.Py_INBE: {e}"))
sys.path.pop(0)  # ou sys.path = original_sys_path si tu préfères

def riverbed_trace_dilated(fn_read_simu, fn_output, threshold, type_extraction, id_begin=None, id_end=None, id_step=None):
    """
    Recognizes the riverbed trace based on a simulation, where water depth above a given threshold is considered part of the riverbed.
    Inputs:
        - fn_read_simu: the simulation file to read.
        - fn_output: the location to save the riverbed trace as a .tiff file.
        - threshold: the water depth threshold above which the areas are considered riverbed.
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

    if type_extraction=="danger_map":
        wd = wolfres2DGPU(fn_read_simu) .danger_map_only_h(id_begin,id_end,id_step)
        wd.array[wd.array > 1000] = 0
        wd.array[wd.array > threshold] = 1
        wd.array[wd.array < threshold] = 0
        wd.as_WolfArray()
        wd.nodata=0
        wd.write_all(Path(fn_output))

def dilatation_mask_river(manager_inbe):
    mask_river = Path(manager_inbe.IN_RIVER_MASK_SCEN) / "Masked_River_extent.tiff"
    WA_mask_river = WolfArray(mask_river)
    array = binary_dilation(WA_mask_river.array) 
    WA_mask_river.array[:,:] = array[:,:]
    out = Path(manager_inbe.IN_RIVER_MASK_SCEN_tif)
    WA_mask_river.as_WolfArray()
    WA_mask_river.write_all(out)
    return print(f"Dilated mask river written in {Path(manager_inbe.IN_RIVER_MASK_SCEN_tif)}")

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

def get_transform_and_crs(tif_file):
    """
    For TIFF file manipulation, reads the CRS and the geotransform, and returns them.
    """
    ds = gdal.Open(tif_file)
    transform = ds.GetGeoTransform()
    crs_wkt = ds.GetProjection()
    crs = osr.SpatialReference()
    crs.ImportFromWkt(crs_wkt)
    return transform, crs

def create_shapefile_from_prop_tif(fn_tif, shapefile_path):
    unused, unused, width, height, unused, unused = get_header_info(fn_tif)
    ds = gdal.Open(fn_tif)
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()  

    originX, pixelWidth, unused, originY, unused, pixelHeight = gt

    top_left = (originX, originY)
    top_right = (originX + width * pixelWidth, originY)
    bottom_left = (originX, originY + height * pixelHeight)
    bottom_right = (originX + width * pixelWidth, originY + height * pixelHeight)

    rectangle = Polygon([top_left, top_right, bottom_right, bottom_left, top_left])

    sr = osr.SpatialReference()
    sr.ImportFromWkt(ds.GetProjection())
    crs_wkt = sr.ExportToWkt()

    gdf = gpd.GeoDataFrame({'geometry': [rectangle]}, crs=crs_wkt)
    gdf.to_file(shapefile_path)
    ds = None

def get_header_info(fn):
    """
    Reads the headers from the file at path 'fn'.
    """
    class_header = header_wolf()
    class_header.read_txt_header(fn)
    dx,dy = class_header.dx, class_header.dy
    nbx,nby = class_header.nbx, class_header.nby
    X,Y = class_header.origx, class_header.origy
    return dx,dy,nbx,nby,X,Y

def get_header_comparison(list_fn):
    """
    Reads the headers from the files in list_fn and compares them. The result 'comp' is True if the headers are identical, and False otherwise.
    """

    header_infos = [get_header_info(fn) for fn in list_fn]
    variable_names = ["dx", "dy", "nbx", "nby", "X", "Y"]
    for idx, name in enumerate(variable_names):
        values = [header[idx] for header in header_infos]
        if len(set(values)) > 1:
            comp = False
        else:
            comp = True
    return comp


def display_info_header(self_dx, self_nbxy, self_O, fn):
    """
    Displays the header at the path 'fn', and update the values displayed in the window.
    """
    dx,dy,nbx,nby,X,Y= get_header_info(fn)
    self_dx.SetLabel(f"({dx},{dy})")
    self_nbxy.SetLabel(f"({nbx},{nby})")
    self_O.SetLabel(f"({X},{Y})")
    return dx,dy,nbx,nby,X,Y

def vanish_info_header(self_dx, self_nbxy, self_O):
    self_dx.SetLabel("")
    self_nbxy.SetLabel("")
    self_O.SetLabel("")

def update_info_header(self_dx, self_nbxy, self_O, fn):
    """
    Upate the displayed header values by reading the simulations headers if exist.
    """
    if not os.path.exists(fn):
        os.makedirs(fn)

    tif_files = [f for f in os.listdir(fn) if f.lower().endswith('.tif')]
    tif_list_fn = [os.path.join(fn, tif_file) for tif_file in tif_files]
    if tif_files:
        if get_header_comparison(tif_list_fn) :
            dx,dy,nbx,nby,X,Y = display_info_header(self_dx, self_nbxy, self_O, tif_list_fn[0])
            return dx,dy,nbx,nby,X,Y
        else:
            logging.error(_("The interpolated files have different headers. Please fix it."))
            return False, False, False, False, False, False
    else :
        vanish_info_header(self_dx, self_nbxy, self_O)
        return False, False, False, False, False, False

def search_for_modif_bath_and_copy(main_gpu, from_path, path_vuln):
    """
    When loading gpu simulations for last step extraction, search for modified bath_ topography file, according to
    the structure coded in the scenarios manager. If they exist, their extent is copied to CHANGE_VULNE, called vuln_ and
    MNTmodifs_, to enable the user to modify it later. In addition, returns True if such files exist and False if they do not.
    """
    found_bath = False
    scen_manager = Config_Manager_2D_GPU(main_gpu, create_ui_if_wx=False)
    curtree = scen_manager.get_tree(from_path)
    curdicts = scen_manager.get_dicts(curtree)
    all_tif_bath = [scen_manager._select_tif_partname(curdict, 'bath_') for curdict in curdicts]
    all_tif_bath = [curel for curlist in all_tif_bath if len(curlist)>0 for curel in curlist  if curel.name.startswith('bath_')]
    if len(all_tif_bath) :
        found_bath = True
    for tif_file in all_tif_bath:
        found_bath = True
        src_ds = gdal.Open(str(tif_file))
        driver = gdal.GetDriverByName("GTiff")

        xsize = src_ds.RasterXSize
        ysize = src_ds.RasterYSize
        geotransform = src_ds.GetGeoTransform()
        projection = src_ds.GetProjection()

        # MNTmodifs_ file
        output_file = path_vuln / tif_file.name.replace("bath_", "MNTmodifs_")
        dst_ds = driver.Create(str(output_file), xsize, ysize, 1, gdal.GDT_Float32)
        dst_ds.SetGeoTransform(geotransform)
        dst_ds.SetProjection(projection)
        data = np.ones((ysize, xsize), dtype=np.float32)
        dst_ds.GetRasterBand(1).WriteArray(data)
        dst_ds.GetRasterBand(1).SetNoDataValue(0)
        dst_ds = None

        src_ds = None

        return found_bath

def create_INPUT_OUTPUT_forScenario(maindir, study_area, scenario, simu_gpu=None, danger=None):
    """Creates folder for a new study area or/and scenario. The last argument simu_gpu is used when loading simulation (indicates path to the simulation folder),
    if not used, indicate None to ignore it."""
    study_area = Path(study_area).stem
    base_pathwd = Path(maindir) / "INPUT" / "WATER_DEPTH" / study_area / scenario
    subfolders = ["DEM_FILES", "INTERP_WD", "EXTRACTED_LAST_STEP_WD"]
    os.makedirs(base_pathwd, exist_ok=True)
    for folder in subfolders:
        os.makedirs(os.path.join(base_pathwd, folder), exist_ok=True)
        
    base_change = Path(maindir) / "INPUT" / "CHANGE_DEM" / study_area / scenario
    os.makedirs(base_change, exist_ok=True)
    
    base_CSV =  Path(maindir) / "INPUT" / "CSVs" / study_area / scenario
    os.makedirs(base_CSV, exist_ok=True)
    
    base_river =  Path(maindir) / "INPUT" / "RIVER_MASK" / study_area / scenario
    os.makedirs(base_river, exist_ok=True)
    
    base_velocity =  Path(maindir) / "INPUT" / "VELOCITY" / study_area / scenario
    os.makedirs(base_velocity, exist_ok=True)
    
    if simu_gpu != None:
        path_bat_gpu = Path(simu_gpu) / "bathymetry.tif"
        if path_bat_gpu.exists():
            create_shapefile_from_prop_tif(path_bat_gpu, Path(maindir) / "INPUT" / "STUDY_AREA" / f"{study_area}.shp")
            logging.info(_("Study area file created in INPUT/STUDY_AREA."))
        else :
            logging.error(_(f"Error in the study area creation : no bathymetry.tif file in the given simulation folder {simu_gpu}. Please provide it in this folder and try again."))
    if danger != None:
        if danger.exists():
            create_shapefile_from_prop_tif(danger, Path(maindir) / "INPUT" / "STUDY_AREA" / f"{study_area}.shp")
            logging.info(("Study area file created in INPUT/STUDY_AREA."))
        else :
            logging.error(_(f"Error in the study area creation : no bathymetry.tif file in the given simulation folder {simu_gpu}. Please provide it in this folder and try again."))
        
        

    INBE_Manager(main_dir=maindir, Study_area=Path(study_area).stem, scenario=scenario)
    logging.info((f"Files created in INPUT and OUTPUT for the study area named '{study_area}', and the scenario named '{scenario}'"))
    return

            
class INBEGui(wx.Frame):
    """ The main frame for the damage computation with INSYDE-BE (=INBE) """

    def __init__(self, parent=None, width=1024, height=500):

        super(wx.Frame, self).__init__(parent, title='Damage modelling - INBE manager', size=(width, height))

        self._manager = None
        self._mapviewer = None
        self.InitUI()
        self._func = INBE_functions()
        
        self.df_results_Ti = None

    @property
    def mapviewer(self):
        return self._mapviewer

    @mapviewer.setter
    def mapviewer(self, value):
        from ..PyDraw import WolfMapViewer

        if not isinstance(value, WolfMapViewer):
            raise TypeError("The mapviewer must be a WolfMapViewer")

        self._mapviewer = value

    def layout(self, self_fct):
        """Update the layers for the main buttons"""
        font = self_fct.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self_fct.SetFont(font)
        self_fct.SetBackgroundColour(wx.Colour(222, 209, 209))
        #self_fct.Bind(wx.EVT_ENTER_WINDOW, self.OnHoverEnter)
        #self_fct.Bind(wx.EVT_LEAVE_WINDOW, self.OnHoverLeave)

    def on_button_click(self, event):
        self.PopupMenu(self.menu)
        
    def on_button_click2(self, event2):
        self.PopupMenu(self.menu2)

    def onRiverbed(self, event):
        """Two options for the 'Update Riverbed' button: either the new riverbed trace
        file already exists and the user selects it, or it does not exist, and the user points to
        a no-overflow simulation, allowing the code to create the trace."""
        menu_id = event.GetId()
        if menu_id == 1:
            logging.info(_("Option 1 : the file exists, pointing towards it."))
            dlg = wx.FileDialog(None, "Please select the .tiff file with the NEW trace of the riverbed.",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                    wildcard="TIFF files (*.tiff)|*.tiff")

            if dlg.ShowModal() == wx.ID_OK:
                selected_file = Path(dlg.GetPath())
                copied_file = self._manager.OUT_SCEN_DIR / "copy_file"
                shutil.copy(selected_file, copied_file)
                logging.info(_(f"File copied to: {copied_file}"))
                
                new_name = Path(self._manager.IN_RIVER_MASK_SCEN) / "Masked_River_extent.tiff"

                with wx.MessageDialog(self, f"Modified riverbed imported and called Masked_River_extent_scenarios.tiff.",
                    "File imported.", wx.OK | wx.ICON_INFORMATION) as dlg:
                    dlg.ShowModal()

                if new_name.exists():
                    new_name.unlink()

                copied_file.rename(new_name)
                dilatation_mask_river(self._manager)
                logging.info(_(f"File renamed and dilated to: {new_name}"))
            else:
                logging.info(_('No file selected. Please try again.'))

        elif menu_id == 2: #No file, so need to create
            logging.info(_("Option 2 : pointing to simulation with low discharge (no overflows!)."))

            with wx.DirDialog(self, "Please select a simul_gpu_results folder of a simulation with low discharges (no overflows).", style=wx.DD_DEFAULT_STYLE) as dir_dlg:
                if dir_dlg.ShowModal() == wx.ID_OK:
                    selected_folder = Path(dir_dlg.GetPath())
                    if os.path.basename(selected_folder) == "simul_gpu_results" :
                        logging.info(_(f"Selected folder: {selected_folder}"))
                        fn_output = Path(self._manager.IN_RIVER_MASK_SCEN) / "Masked_River_extent.tiff"
                        dlg = wx.TextEntryDialog(self, "What water depth threshold (in meters) should be used to define the riverbed trace, above which\n"
                                                 "the water depth is considered part of the riverbed? Use a dot as a decimal separator (e.g 0.3).", "Type a water depth threshold in [m] (e.g 0.3)", "")

                        if dlg.ShowModal() == wx.ID_OK:
                            while True:
                                try:
                                    valeur = dlg.GetValue()
                                    threshold = float(valeur)
                                    if threshold < 1e-5 or threshold > 150:
                                        wx.MessageBox(
                                            "Error: The value must be positive > 0 and reasonable. Please, try again.",
                                            "Error", wx.OK | wx.ICON_ERROR
                                        )
                                        break

                                    dialog = wx.SingleChoiceDialog(
                                        parent=None,
                                        message=f"Threshold accepted. Considering riverbed where water depth > {threshold}[m] via",
                                        caption="Choix",
                                        choices=["last step", "danger map"]
                                    )

                                    if dialog.ShowModal() == wx.ID_OK:
                                        choix = dialog.GetStringSelection()
                                        if choix == "last step":
                                            type_extraction = "last step"
                                            id_begin, id_end, id_step =None, None, None
                                        else:
                                            type_extraction = "danger_map"
                                            
                                            dlg_start = wx.TextEntryDialog(None, "From which time step? (integer)", "Start step")
                                            if dlg_start.ShowModal() == wx.ID_OK:
                                                id_begin = int(dlg_start.GetValue())
                                            dlg_start.Destroy()

                                            dlg_end = wx.TextEntryDialog(None, "Until which time step? (integer, enter -1 for last)", "End step")
                                            if dlg_end.ShowModal() == wx.ID_OK:
                                                id_end = int(dlg_end.GetValue())
                                            dlg_end.Destroy()

                                            dlg_step = wx.TextEntryDialog(None, "Extract every how many steps? (integer)", "Step interval")
                                            if dlg_step.ShowModal() == wx.ID_OK:
                                                id_step = int(dlg_step.GetValue())
                                            dlg_step.Destroy()
                                            
                                    dialog.Destroy()
                                    logging.info(_("Detecting riverbed."))
                                    riverbed_trace_dilated(selected_folder, fn_output, threshold, type_extraction, id_begin, id_end, id_step)
                                    dilatation_mask_river(self._manager)
                                    logging.info(_("File created."))
                                    with wx.MessageDialog(
                                        self,
                                        "Masked_River_extent_scenarios.tiff successfully created and dilated.",
                                        "File created.", wx.OK | wx.ICON_INFORMATION
                                    ) as dlg_success:
                                        dlg_success.ShowModal()
                                    break
                                except ValueError:
                                    wx.MessageBox(
                                        "Error: Invalid entry. Please enter a valid number (positive > 0, reasonable, using with DOT as a decimal separator).",
                                        "Error", wx.OK | wx.ICON_ERROR
                                    )
                                    break

                        else:
                            logging.info(_("Cancelled."))
                            dlg.Destroy()
                    else:
                        logging.info(_("No folder (or wrong one) selected. Please try again (must be simul_gpu_results)."))


    def layout_listbox(self, self_fct):
        """Changes the layout for the listbox : light grey."""
        self_fct.SetBackgroundColour(wx.Colour(220, 220, 220))

    def InitUI(self):
        self.gpu_bathy = None
        self.maindir = None

        sizer_hor_main = wx.BoxSizer(wx.HORIZONTAL)
        sizer_vert1 = wx.BoxSizer(wx.VERTICAL)
        sizer_hor_threads = wx.BoxSizer(wx.HORIZONTAL)
        sizer_hor1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_hor2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_hor3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_hor4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_hor5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_hor_scen = wx.BoxSizer(wx.HORIZONTAL)

        # 1st LINE - Loading INBE folder
        panel = wx.Panel(self)
        self._but_maindir = wx.Button(panel, label=_('Main Directory'))
        self._but_maindir.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self._but_maindir.Bind(wx.EVT_BUTTON, self.OnMainDir)

        self._listbox_studyarea = wx.ListBox(panel, choices=[], style=wx.LB_SINGLE)
        self.layout_listbox(self._listbox_studyarea)
        self._listbox_studyarea.Bind(wx.EVT_LISTBOX, self.OnStudyArea)
        self._listbox_studyarea.SetToolTip(_("Choose the study area existed in the folder."))

        self._listbox_scenario = wx.ListBox(panel, choices=[], style=wx.LB_SINGLE)
        self.layout_listbox(self._listbox_scenario)
        self._listbox_scenario.Bind(wx.EVT_LISTBOX, self.OnScenario)
        self._listbox_scenario.SetToolTip(_("Choose the INBE scenario."))

        sizer_ver_small = wx.BoxSizer(wx.VERTICAL)
        self._but_checkfiles = wx.Button(panel, label=_('Check structure'))
        self._but_checkfiles.Bind(wx.EVT_BUTTON, self.OnCheckFiles)
        self._but_checkfiles.SetToolTip(_("Checks if the folder is correctly structured\n with INPUT and OUTPUT."))
        self._but_checksim = wx.Button(panel, label=_('Check simulations'))
        self._but_checksim.SetToolTip(_("Displays the loaded simulations, interpolated in INTERP_WD."))
        self._but_checksim.Bind(wx.EVT_BUTTON, self.OnHydrodynInput)
        self._but_checkpicc = wx.Button(panel, label=_('Check PICC'))
        self._but_checkpicc.Bind(wx.EVT_BUTTON, self.OnCheckPICC)
        self._but_checkpicc.SetToolTip(_("Checks if PICC exists and how much residential building ('Habitations') are read. The process may be slow. Please, be patient."))
        self._but_checkpond= wx.Button(panel, label=_('Check ponderation'))
        self._but_checkpond.Bind(wx.EVT_BUTTON, self.OnCheckPond)
        self._but_checkpond.SetToolTip(_("Displays a graph of the computed weighting coefficient\n of the final INBE computations."))

        # 2nd LINE - Hydrodynamic part
        self._but_loadgpu = wx.ToggleButton(panel, label=_('Working with new\n hydraulic scenarios'))
        self._but_loadgpu.SetToolTip(_("To load or change the hydraulic simulations"))
        self._but_loadgpu.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self._but_loadgpu.Bind(wx.EVT_TOGGLEBUTTON, self.OnLoadingSimu)
        sizer_hor2.Add(self._but_loadgpu, 1, wx.ALL | wx.EXPAND, 0)

        self._check_listbox = wx.CheckListBox(panel, choices=[], style=wx.LB_MULTIPLE | wx.CHK_CHECKED)
        self.layout_listbox(self._check_listbox)
        self.sims = {}
        sizer_hor2.Add(self._check_listbox, 1, wx.ALL | wx.EXPAND, 0)      
        
        self._but_danger = wx.Button(panel, label=_('Extract last step or\n compute danger maps ▼'))
        self._but_danger.SetToolTip(_("To create the danger maps of velocities and water depth. Please be patient."))
        self._but_danger.Bind(wx.EVT_BUTTON, self.on_button_click2)
        self.menu2 = wx.Menu()
        self.menu2.Append(1, _("Extract the last step of the simulation."))
        self.menu2.Append(2, _("Compute the danger maps of the simulation."))
        self.menu2.Bind(wx.EVT_MENU, self.OnDanger)
        sizer_hor2.Add(self._but_danger, 1, wx.ALL | wx.EXPAND, 0)
        
        sizer_ver_small2 = wx.BoxSizer(wx.VERTICAL)
        self._but_DEM = wx.Button(panel, label=_("Check DEM, DTM for interpolation"))
        self._but_DEM.SetToolTip(_("To display the existing DEM input for the interpolation of the simulated free surfaces."))
        self._but_DEM.Bind(wx.EVT_BUTTON, self.OnDEM)
                
        self._but_MNTmodifs = wx.Button(panel, label=_("Check 'MNTmodifs_' scenarios"))
        self._but_MNTmodifs.SetToolTip(_("To display the existing MNTmodifs_ scenario files for the DTM input of interpolation of the simulated free surfaces."))
        self._but_MNTmodifs.Bind(wx.EVT_BUTTON, self.OnCheckMNTmodifs)
        
        sizer_hor2.Add(sizer_ver_small2, 0, wx.ALL | wx.EXPAND, 5)
        
        self._but_extrinterp = wx.Button(panel, label=_('Read and interpolate'))
        self._but_extrinterp.SetToolTip(_("Reads and interpolates the danger maps computed (if not done, use previous buttons) of wolf gpu simulations."))
        self._but_extrinterp.Bind(wx.EVT_BUTTON, self.OnInterpolation)
        sizer_hor2.Add(self._but_extrinterp, 1, wx.ALL | wx.EXPAND, 0)


        sizer_hor1.Add(self._but_maindir, 2, wx.ALL | wx.EXPAND, 0)
        sizer_hor1.Add(self._listbox_studyarea, 1, wx.ALL | wx.EXPAND, 0)
        sizer_hor1.Add(self._listbox_scenario, 1, wx.ALL | wx.EXPAND, 0)
        sizer_hor1.Add(sizer_ver_small, 0, wx.ALL | wx.EXPAND, 5)

        #3rd line
        sizer_hor_threads = wx.BoxSizer(wx.HORIZONTAL)
        text_dx = wx.StaticText(panel, label=_('Resolution (dx,dy) [m]:'))
        self.input_dx = wx.StaticText(panel)
        self.input_dx.SetMinSize((80, -1))
        text_nbxy = wx.StaticText(panel, label=_('(nbx, nby):'))
        self.input_nbxy = wx.StaticText(panel)
        self.input_nbxy.SetMinSize((90, -1))
        text_O = wx.StaticText(panel, label=_('Origin (X,Y):'))
        self.input_O = wx.StaticText(panel)
        self.input_O.SetMinSize((170, -1))
        text_inflation = wx.StaticText(panel, label=_('Inflation factor:'))
        self._inflation = wx.SpinCtrlDouble(panel, value="1.3", min=1.2, max=2.5, inc=0.1)
        self._inflation.SetToolTip(_("Inflation factor from 2020 (corresponding year of the unitary prices), to the year of analysis. Defaults to 1.3[%] (corresponds to 2023)."))

        self._but_toggle_admin = wx.ToggleButton(panel, label=_('Admin mode'))
        self._but_toggle_admin.SetToolTip(_("To activate admin mode. enter password."))
        self.toggle_state_Admin = False
        self._but_toggle_admin.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleAdmin)
        
        sizer_hor_threads.Add(text_dx, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self.input_dx, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(text_nbxy, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self.input_nbxy, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(text_O, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self.input_O, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(text_inflation, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self._inflation, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        #sizer_hor_threads.Add(self._nb_process, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self._but_toggle_admin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)

        # Last lines + scenarios
        #------------------------
        
        self._but_upriverbed = wx.Button(panel, label=_("Update riverbed ▼"))
        self._but_upriverbed.SetToolTip(_("Select one of the two options to create the riverbed mask."))
        self._but_upriverbed.Bind(wx.EVT_BUTTON, self.on_button_click)       
        self.menu = wx.Menu()
        self.menu.Append(1, _("File of riverbed trace exists."))
        self.menu.Append(2, _("Point to a low discharge simulation and calculate the riverbed trace."))
        self.menu.Bind(wx.EVT_MENU, self.onRiverbed)
        sizer_hor_scen.Add(self._but_upriverbed, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)

        self._check_listbox_Ti = wx.CheckListBox(panel, choices=[], style=wx.LB_MULTIPLE | wx.CHK_CHECKED)
        self.layout_listbox(self._check_listbox_Ti)
        self.sims_Ti = {}
        sizer_hor4.Add(self._check_listbox_Ti, 1, wx.ALL | wx.EXPAND, 0) 
        
        self._but_input = wx.Button(panel, label=_('Input table creation\n by reading PICC and WOLF'))
        self.layout(self._but_input)
        self._but_input.Bind(wx.EVT_BUTTON, self.OnInput)
        sizer_hor4.Add(self._but_input, 1, wx.ALL | wx.EXPAND, 0)
        
        text_tri = wx.StaticText(panel, label=_('Select percentil'))
        self._tri = wx.SpinCtrlDouble(panel, value="1", min=0.05, max=1, inc=0.05)
        self._tri.SetToolTip(_("Percentile of the number of results to be represented in the analysis."))
        text_tri.SetMinSize((100,-1))
        self._tri.SetMinSize((50,-1))
        sizer_hor5.Add(text_tri, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor5.Add(self._tri, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        
        self._but_readresults = wx.Button(panel, label=_('Read results'))
        self.layout(self._but_readresults)
        self._but_readresults.Bind(wx.EVT_BUTTON, self.OnReadResults)
        sizer_hor5.Add(self._but_readresults, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        #self._but_readresults.Hide()
        
        #self._listbox_scenario2 = wx.CheckListBox(panel, choices=[], style=wx.LB_MULTIPLE | wx.CHK_CHECKED)
        #self.layout_listbox(self._listbox_scenario2)
        #self.list_scen_output = {}
        #self._listbox_scenario2.SetToolTip("Choose the scenarios to compare.")
        #sizer_hor5.Add(self._but_setcomp, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        
        self._listbox_CompScen = wx.CheckListBox(panel, choices=[], style=wx.LB_MULTIPLE | wx.CHK_CHECKED)
        self.layout_listbox(self._listbox_CompScen)
        self._listbox_CompScen.SetToolTip(_("Choose the INBE scenarios to compare (minimum 2), in the same study area selected at the manager first line."))
        sizer_hor5.Add(self._listbox_CompScen, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        
        
        self._but_setcomp = wx.Button(panel, label=_('Comparison'))
        self.layout(self._but_setcomp)
        self._but_setcomp.Bind(wx.EVT_BUTTON, self.OnSetComp0)
        sizer_hor5.Add(self._but_setcomp, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        #self._but_setcomp.Hide()
        
        
        
        self._but_default_TEMP = wx.Button(panel, label=_('Default values and\n individual damage'))
        self._but_default_TEMP.SetToolTip(_("Impute the default values to the input tables, and compute the individual damage."))
        self.layout(self._but_default_TEMP)
        self._but_default_TEMP.Bind(wx.EVT_BUTTON, self.OnDefault_TEMP)
        sizer_hor4.Add(self._but_default_TEMP, 1, wx.ALL | wx.EXPAND, 0)
        
        self._but_combined_OUTPUT = wx.Button(panel, label=_('Combined damage'))
        self._but_combined_OUTPUT.SetToolTip(_("Compute the combined damage."))
        self.layout(self._but_combined_OUTPUT)
        self._but_combined_OUTPUT.Bind(wx.EVT_BUTTON, self.Oncombined_OUTPUT)
        sizer_hor4.Add(self._but_combined_OUTPUT, 1, wx.ALL | wx.EXPAND, 0)
        
        #Lines order
        sizer_ver_small.Add(self._but_checkfiles, 0, wx.ALL | wx.EXPAND, 1)
        sizer_ver_small.Add(self._but_checksim, 0, wx.ALL | wx.EXPAND, 1)
        sizer_ver_small.Add(self._but_checkpond, 0, wx.ALL | wx.EXPAND, 1)
        sizer_ver_small.Add(self._but_checkpicc, 0, wx.ALL | wx.EXPAND, 1)
    
        sizer_vert1.Add(sizer_hor1, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor2, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor_threads, 0, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor_scen, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor3, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor4, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor5, 1, wx.EXPAND, 0)
        sizer_hor_main.Add(sizer_vert1, proportion=1, flag=wx.EXPAND, border=0)
        
        sizer_ver_small2.Add(self._but_MNTmodifs, 0, wx.ALL | wx.EXPAND, 1)
        sizer_ver_small2.Add(self._but_DEM, 0, wx.ALL | wx.EXPAND, 1)

        #Disabled if Main Directory + SA + Scenario not selected
        self._but_default_TEMP.Enable(False)
        self._but_danger.Enable(False)
        self._but_input.Enable(False)
        self._tri.Enable(False)
        self._but_readresults.Enable(False)
        self._but_checkfiles.Enable(False)
        self._but_DEM.Enable(False)
        self._but_MNTmodifs.Enable(False)
        self._but_extrinterp.Enable(False)
        self._but_combined_OUTPUT.Enable(False)
        self._but_upriverbed.Enable(False)
        self._but_checksim.Enable(False)
        self._but_checkpicc.Enable(False)
        self._but_loadgpu.Enable(False)
        self._but_checkpond.Enable(False)
        self._but_setcomp.Enable(False)

        panel.SetSizer(sizer_hor_main)
        panel.Layout()


    def OnSims(self, e:wx.ListEvent):
        """ Load sim into the mapviewer """
        pass

    def OnSimsDBLClick(self, e:wx.ListEvent):
        """ Load sim into the mapviewer """
        if self.mapviewer is None:
            return

        from ..PyDraw import draw_type

        idx_sim = e.GetSelection()
        tmppath = self._manager.get_filepath_for_return_period(self._manager.get_return_periods()[idx_sim])
        if tmppath.stem not in self.mapviewer.get_list_keys(drawing_type=draw_type.ARRAYS):
            self.mapviewer.add_object('array', filename=str(tmppath), id=tmppath.stem)
            self.mapviewer.Refresh()

    def OnCheckFiles(self, e):
        """ Check the files """        
        if self._manager is None:
            logging.error(_("No main directory selected -- Nothing to check"))
            return

        i=self._manager.check_inputs()

        if i == False :
            logging.error(_(f"Missing files in INPUT. Please provide them by following the right structure."))
            with wx.MessageDialog(self, f"Missing files in INPUT. Inputs can not be created automatically : you must provide them.\nPlease read the logs and terminal to see the missing ones.", "Error", wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
            return
        else :
            if (self._manager._study_area is None) or (self._manager._scenario is None):
                logging.error(_(f"No study area and/or scenario selected, no check of OUTPUT."))
                with wx.MessageDialog(self, f"INPUT is well structured, but OUTPUT has not been checked because there is no study area and scenario selected.", "Checking", wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.ShowModal()
            else:
                logging.info(_(f"The folder is well structured."))
                #t=self._manager.check_temporary()
                o=self._manager.check_outputs()
                with wx.MessageDialog(self, f"Main directory is checked.\nINPUT is well structured, and OUTPUT has been checked. If folders were missing, they have been created\nMain directory at {self.maindir}", "Checking", wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.ShowModal()
        #logging.info(f"scenario {self._manager._scenario} {self._manager.scenario} et SA {self._manager._study_area} {self._manager.Study_area}")

    def OnHydrodynInput(self,e):
        """ A test to check if the FILLED water depths files exist.
            -If YES : the code can go on
            -If NO : either need to be computed, either the code will use the baseline ones
        """

        if self._manager is None:
            logging.error(_("No main directory selected -- Nothing to check"))
            return

        if self._manager.IN_SA_INTERP is None:
            with wx.MessageDialog(self, "No simulation found in the manager. Please select the simulations first.", "Error", wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
            return

        paths_FilledWD = self._manager.get_sims_files_for_scenario()

        if len(paths_FilledWD) == 0 :
            logging.info(_("There are no interpolated free surface files."))
            dialog = wx.MessageDialog(None, "There are no interpolated free surface files. Please choose an action.", "Checking- Choose an option",
                                   wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)

            dialog.SetYesNoLabels("Use the ones in the scenario_baseline (assumption)", "Load other simulations")
            response = dialog.ShowModal()

            if response == wx.ID_YES:
                logging.info(_("Decision of using baseline simulations."))
                paths_FilledWD_base = self._manager.get_sims_files_for_baseline()
                if len(paths_FilledWD_base) == 0 :
                    logging.info(_("Cannot select files in the _baseline folder (no files or no folder!)."))
                else:
                    self._manager.copy_tif_files(paths_FilledWD_base, self._manager.IN_SA_INTERP)

            elif response == wx.ID_NO:
                logging.info(_("Decision of loading simulations."))
                with wx.MessageDialog(self, f"Please use the 'Working with new hydraulic scenarios' button of the manager and follow the instructions.", "Redirecting",
                                      wx.OK | wx.ICON_INFORMATION) as dlg:
                    dlg.ShowModal()
            else:
                logging.info(_("Cancelled"))

            dialog.Destroy()

        else:
            name_paths_FilledWD = []

            for names in paths_FilledWD:
                logging.info(_(f"Interpolated free surface file(s) found: {names.name}. \n Reminder : the names of the simulations MUST be 'T.' or 'Q.' with '.' the return period."))
                name_paths_FilledWD.append(names.name)
            with wx.MessageDialog(self,
                                f"{len(paths_FilledWD)} file(s) of interpolated free surface found in the folder : {name_paths_FilledWD}.",
                                "Information",
                                style=wx.OK | wx.ICON_INFORMATION) as dlg:
                dlg.ShowModal()
            update_info_header(self.input_dx,self.input_nbxy,self.input_O,self._manager.IN_SA_INTERP)


    def OnCheckPond(self,e): #Maybe later ? Idk
        if self._manager is None:
            logging.error(_("No main directory selected -- Nothing to check"))
            return
        if self._manager.IN_SA_INTERP is None:
            logging.error(_("No IN_SA_INTERP attribute found in the manager."))
            with wx.MessageDialog(self, "No simulation found in the manager. Please select the simulations first.", "Error", wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
            return
        ponds = self._manager.get_ponderations()
        if isinstance(ponds, pd.DataFrame):
            logging.info(_(f"Plotting the coefficients graph."))
            ponds.plot(kind='bar', color='gray', edgecolor='black')
            plt.ylabel("Weighting coefficients [-]")
            plt.xlabel("Return period [years]")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.show()
        else:
            with wx.MessageDialog(self,
                                "No coefficients computed, because no return period found in the interpolated simulation folder. Try after loading gpu simulations",
                                "Checking",
                                style=wx.OK | wx.ICON_INFORMATION) as dlg:
                dlg.ShowModal()

    def OnCheckPICC(self, e):
        logging.info(_(f"Checking PICC for study area {self._manager._study_area}, in {self._manager.scenario}."))
        unused, nb, unused = self._func.PICC_read(self._manager)#._study_area, self._manager.scenario)
        if nb != None :
            with wx.MessageDialog(self,
                                    f"PICC Successfully read. There are {nb} residential building(s) ('Habitation') contained in\n the selected study area {self._manager._study_area}, in {self._manager.scenario}.",
                                    "Checking PICC",
                                    style=wx.OK | wx.ICON_INFORMATION) as dlg:
                    dlg.ShowModal()
        else :
            path = Path(self._manager.IN_DATABASE) / "PICC_Vesdre.shp"
            with wx.MessageDialog(self,
                                    f"Error while reading PICC, please ensure the file exists in {path}",
                                    "Error checking PICC",
                                    style=wx.OK | wx.ICON_INFORMATION) as dlg:
                    dlg.ShowModal()
            

    def OnMainDir(self, e):
        """Selects the main directory to be read."""
        vanish_info_header(self.input_dx,self.input_nbxy,self.input_O)

        with wx.DirDialog(self, "Choose the main directory containing the data (folders INPUT and OUTPUT):",
                          style=wx.DD_DEFAULT_STYLE
                          ) as dlg:

            if dlg.ShowModal() == wx.ID_OK:
                self._manager = INBE_Manager(main_dir=dlg.GetPath())#, Study_area="scenario_manager", scenario = "scenario_before2021") 
                self.maindir=dlg.GetPath()

                folders = ["INPUT"]

                for folder in folders:
                    if not os.path.isdir(os.path.join(self.maindir, folder)):
                        logging.error(_("INPUT folder is missing."))
                        wx.MessageBox(
                                f"Missing INPUT folder. Please organize correctly this folder {self.maindir}.",
                                "Error",
                                wx.OK | wx.ICON_ERROR
                                )
                        dlg.Destroy()
                        return

                folders = ['RIVER_MASK', 'DATABASE', 'STUDY_AREA', 'CSVs', 'WATER_DEPTH', 'VELOCITY']
                missing = []
                for folder in folders:
                    if not os.path.isdir(os.path.join(self.maindir, "INPUT", folder)):
                        logging.error(_(f"INPUT/{folder} folder is missing."))
                        missing.append(folder)
                if missing:
                    wx.MessageBox(
                            f"Missing folders : {missing}. Please organize correctly your INPUT folder in {self.maindir}.",
                            "Error",
                            wx.OK | wx.ICON_ERROR
                            )
                    dlg.Destroy()
                    return

                folders = ["OUTPUT"]#TEMP", 
                for folder in folders:
                    if not os.path.isdir(os.path.join(self.maindir, folder)):
                        logging.info(_(f"Creating {folder} folder."))
                        os.makedirs(os.path.join(self.maindir, folder))

                self._but_default_TEMP.Enable(True)
                self._but_input.Enable(True)
                self._but_checkfiles.Enable(True)
                self._but_upriverbed.Enable(True)
                self._tri.Enable(True)
                self._but_readresults.Enable(True)
                self._but_checksim.Enable(True)
                self._but_checkpicc.Enable(True)
                self._but_loadgpu.Enable(True)
                self._but_checkpond.Enable(True)
                self._but_combined_OUTPUT.Enable(True)
                self._but_setcomp.Enable(True)
                
                #Must be False if come back :
                self._but_DEM.Enable(False)
                self._but_MNTmodifs.Enable(False)
                self._but_extrinterp.Enable(False) 

                self._listbox_scenario.Clear()
                studyareas = self._manager.get_list_studyareas()
                if len(studyareas) == 0 :
                    logging.info(_("Folder loaded but no study areas found in the folder (INPUT/STUDY_AREA). Please use the button to load hydraulic simulations in the manager."))
                    return
                self._listbox_studyarea.Clear()
                self._listbox_studyarea.InsertItems(studyareas, 0)

                logging.info(_("All the directories are present"))

    def OnStudyArea(self, e):
        """ Change the study area """
        if self._manager is None:
            return
        vanish_info_header(self.input_dx,self.input_nbxy,self.input_O)
        self._listbox_scenario.Clear()
        self.file_paths = None
        study_area:str = self._manager.get_list_studyareas(with_suffix=True)[e.GetSelection()]

        self._manager.change_studyarea(study_area)
        list_sc, list_SA = self._manager.get_list_scenarios_extended()
        self.items = list(zip(list_SA, list_sc))  # [(SA, Scenario), ...]
        choices = [f"{sa} / {sc}" for sa, sc in self.items]
        self._listbox_CompScen.Set(choices)

        #self._listbox_CompScen.Set(list_sc_extended)#get_list_individual_T())

        sc = self._manager.get_list_scenarios()
        
        if len(sc)!=0:
            self._listbox_scenario.InsertItems(sc, 0)
        else :
            logging.error(_("No scenario available associated with this study area."))

        if self.mapviewer is not None:
            tmp_path = self._manager.IN_STUDY_AREA / study_area

            from ..PyDraw import draw_type
            if not tmp_path.stem in self.mapviewer.get_list_keys(drawing_type=draw_type.VECTORS):
                self.mapviewer.add_object('vector', filename=str(tmp_path), id=tmp_path.stem)
                self.mapviewer.Refresh()
        self._but_DEM.Enable(False)
        self._but_MNTmodifs.Enable(False)
        self._but_extrinterp.Enable(False) 

    def OnScenario(self, e):
        """ Change the scenario """
        if self._manager is None:
            return
        scenario = self._manager.get_list_scenarios()[e.GetSelection()]
        self._but_DEM.Enable(True)
        self._but_MNTmodifs.Enable(True)
        self._but_extrinterp.Enable(True) 
        self._manager.change_scenario(scenario)
        create_INPUT_OUTPUT_forScenario(self.maindir, self._manager.Study_area, self._manager.scenario, None)
        update_info_header(self.input_dx,self.input_nbxy,self.input_O,self._manager.IN_SA_INTERP)
        self._check_listbox_Ti.Set(self._manager.get_list_interp()) #not in accept

    def OnLoadingSimu(self,e):
        """ Link between INBE and simulations
            -Load a hydraulic scenarios from the scenario manager
            -Create scenario and study area if needed.
        """
        #MAde for Vesdre & Daniela, very specific. Maybe to be kept... [xyz]
        #dlg = wx.SingleChoiceDialog(
        #    None,
        #    "What do you want to load?",
        #    "Loading choice",
        #    ["Existing danger maps", "Wolf-GPU simulation"]
        #)
        #if dlg.ShowModal() == wx.ID_OK:
        #    choice = dlg.GetStringSelection()
        #    if choice == "Existing danger maps":
        #        dlg0 = wx.MessageDialog(
        #                None,
        #                "Please follow these steps:\n\n"
        #                "• Create a folder named after your study area (e.g., Theux).\n"
        #                "• Inside this folder, create a subfolder for the scenario (e.g., scenario_example).\n"
        #                "• In this scenario subfolder, include:\n"
        #                "   - A water level danger map in .tif format (e.g., T2021.tif).\n"
        #                "   - Optionally, a velocity danger map named like:\n"
        #                "     v_danger_T2021_scenario_example.tif\n\n"
        #                "Then, select the scenario folder (e.g., Desktop\\Theux\\scenario_example).",
        #                "Information",
        #                wx.OK | wx.ICON_INFORMATION
        #            )
        #        dlg0.ShowModal()
        #        dlg0.Destroy()
        #            
        #        
        #        dlg_path = wx.DirDialog(
        #            None,
        #            "Please point toward the specific scenario folder (e.g Desktop\Theux\scenario_2021)."
        #        )
        #        if dlg_path.ShowModal() == wx.ID_OK:
        #            full_path = dlg_path.GetPath() 
        #    
        #            study_area_folder = os.path.basename(os.path.dirname(full_path))
        #            scenario_folder = os.path.basename(full_path)
        #            
        #            tif_path = None
        #            for file in os.listdir(full_path):
        #                if file.endswith(".tif") and file.startswith("T"):
        #                    tif_path = os.path.join(full_path, file)
        #                    break
        #                
        #            
        #            create_INPUT_TEMP_OUTPUT_forScenario(self.maindir, study_area_folder, scenario_folder, danger=Path(tif_path))
        #    
        #            self._manager.change_studyarea(study_area_folder +'.shp')
        #            self._manager.change_scenario(scenario_folder)
        #            self._listbox_studyarea.Clear()
        #            self._listbox_studyarea.InsertItems(self._manager.get_list_studyareas(), 0)
        #            self._listbox_scenario.Clear()
        #            self._listbox_scenario.InsertItems(self._manager.get_list_scenarios(), 0)
        #                
        #            path_wd = self._manager.IN_SA_EXTRACTED
        #            WA_bin = WolfArray(tif_path)
        #            WA_bin.write_all(os.path.join(path_wd, os.path.splitext(os.path.basename(tif_path))[0] + ".bin"))
        #            
        #            path_v = self._manager.IN_SCEN_DIR_V
        #            logging.info(_(f"Scanning the folder {full_path} to get the danger map(s)."))
        #            for file in os.listdir(full_path):
        #                if file.startswith("v_danger_") and file.endswith(".tif"):
        #                    shutil.copy(os.path.join(full_path, file), path_v)
        #            dlg = wx.MessageDialog(
        #                None,
        #                "Folders created and danger map(s) imported.",
        #                "Information",
        #                wx.OK | wx.ICON_INFORMATION
        #            )
        #            dlg.ShowModal()
        #            dlg.Destroy()
        #            logging.info(_("Folders created and danger map(s) imported."))
        #                    
        dlg = wx.DirDialog(None, "Please select the main scenario manager folder (containing the scenarios, the folder discharge, the scripts.py...), named after the STUDY AREA.\n If you cancel, this button wont be activated or will be desactivated.", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self._but_loadgpu.SetValue(True)
            main_gpu = Path(dlg.GetPath())
            study_area = main_gpu.name
            logging.info(_(f"Selected folder for GPU result such as the STUDY AREA is {study_area}"))
            dlg = wx.DirDialog(None, "Please select the scenarios folder (containing the 'simulations' folder) of the specific HYDRAULIC SCENARIO.", defaultPath=str(main_gpu), style=wx.DD_DEFAULT_STYLE)
            if dlg.ShowModal() == wx.ID_OK:
                scenario = Path(dlg.GetPath())
                hydraulic_scen=scenario.joinpath("simulations")
                scenario=scenario.name
                logging.info(_(f"Selected hydraulic scenario : {scenario}"))
                create_INPUT_OUTPUT_forScenario(self.maindir, study_area, scenario, main_gpu)
                self._manager.change_studyarea(study_area+'.shp')
                self._manager.change_scenario(scenario)

                self._listbox_studyarea.Clear()
                self._listbox_studyarea.InsertItems(self._manager.get_list_studyareas(), 0)
                self._listbox_scenario.Clear()
                self._listbox_scenario.InsertItems(self._manager.get_list_scenarios(), 0)

                #Blue color of selection even if not directly clicked :
                index_to_select = self._listbox_scenario.FindString(scenario)
                if index_to_select != wx.NOT_FOUND:
                    self._listbox_scenario.SetSelection(index_to_select)
                self._listbox_scenario.SetItemBackgroundColour(index_to_select, wx.Colour(0, 120, 215))

                index_to_select = self._listbox_studyarea.FindString(study_area)
                if index_to_select != wx.NOT_FOUND:
                    self._listbox_studyarea.SetSelection(index_to_select)
                self._listbox_studyarea.SetItemBackgroundColour(index_to_select, wx.Colour(0, 120, 215))
                self._listbox_studyarea.Refresh()
                self._listbox_scenario.Refresh()

            else:
                logging.error('No hydraulic scenario selected, toggle button desactivated.')
                self._but_loadgpu.SetValue(False)
                return
        else:
            logging.error('No folder found / selected. Please try again.')
            self._but_loadgpu.SetValue(False)
            return

        self._check_listbox.Clear()
        self.sims = {}
        for subdir in hydraulic_scen.iterdir():
            if subdir.is_dir() and subdir.name.startswith("sim_"):
                self.sims[subdir.name] = subdir
            else:
                logging.info(_('No folder sim_ found / selected. Please try again.'))
        self.datadir_simulations = hydraulic_scen
        self.file_paths = {Path(sim).name: Path(sim) for sim in sorted(self.sims.keys())}
        self._check_listbox.Set(sorted(sim for sim in self.sims.keys()))

        logging.info(_(f"GPU simulations loaded in the checkbox.\n\nPlease select the ones you want to interpolate and use the button 'Reading and interpolating free surface'."))
        message = "GPU simulations loaded in the checkbox\n\nPlease select the ones you want to interpolate and use the button 'Reading and interpolating free surface'."

        found_bath = search_for_modif_bath_and_copy(Path(main_gpu), Path(hydraulic_scen.parent), self._manager.IN_CH_DEM_SC)
        if found_bath :
            message+= "\nIn addition, modification files for bathymetry (bath_) have been found in the gpu simulations, a copy has been made for a change in the vulnerability and DEM (see vuln_ and MNTmodifs_ in CHANGE_VULNE). Please edit them."
            logging.info(_(f"Modification files for bathymetry (bath_) have been found in the gpu simulations, a copy has been made for a change in the vulnerability and DEM (see vuln_ and MNTmodifs_ in CHANGE_VULNE). Please edit them."))

        self.gpu_bathy = hydraulic_scen.parent / BATHYMETRY_FOR_SIMULATION # this is the last bathymetry after the scripts have been run
        self._but_extrinterp.Enable(True)
        self._but_DEM.Enable(True)
        self._but_danger.Enable(True)
        self._but_MNTmodifs.Enable(True)
        with wx.MessageDialog(self,
                                message,
                                "Information",
                                style=wx.OK | wx.ICON_INFORMATION) as dlg:
            dlg.ShowModal()

    def OnDanger(self,e):
        """ Specific button to extract last step or to compute the wd danger map"""
        menu_id = e.GetId()
        param_danger = [0, -1, 1]
        if menu_id == 1:
            type_extraction = "last_step"
            logging.info(_("Option 1 : last step extraction and interpolation."))
        elif menu_id == 2:
            type_extraction = "danger_map"
            logging.info(_("Option 2 : danger map computation and interpolation."))
            dlg = wx.TextEntryDialog(None,
                "Enter parameters as (e.g 0, -1, 1): from which step, until which step (-1 if latest step), by number of step",
                "Parameters", "0, -1, 1")
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    param_danger = [int(x.strip()) for x in dlg.GetValue().split(",")]
                except:
                    wx.MessageBox("Invalid input. Use format: 0, -1, 1", "Error")
                dlg.Destroy()
            
            else :
                return
    
            
        with wx.TextEntryDialog(
            self,
            "What threshold (in meters) do you want to apply to filter the water depth danger map?",
            "Water Depth Threshold",
            "0.01"
            ) as dlg:
            threshold = None
            if dlg.ShowModal() == wx.ID_OK:
                val = dlg.GetValue().strip().replace(',', '.')
                try:
                    threshold = float(val)
                    if threshold <= 0:
                        wx.MessageBox("Please enter a strictly positive number.", "Invalid Value", wx.ICON_ERROR)
                        threshold = None
                        return
                except Exception:
                    wx.MessageBox("Invalid input — please enter a number (e.g., 0.01).", "Error", wx.ICON_ERROR)
                    threshold = None
                    return
            else :
                return
        if not hasattr(self, 'file_paths'):
            with wx.MessageDialog(self,
                                f"Please, first load gpu simulations via the previous button.",
                                "Attention",
                                style=wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
            return
        logging.info(_(f"Threshold for water depth selected : {threshold} [m]"))
        checked_indices = self._check_listbox.GetCheckedItems()
        checked_items = [self._check_listbox.GetString(index) for index in checked_indices]
        selected_paths = [self.file_paths[item] for item in checked_items]
        if not selected_paths:
            wx.MessageBox("No selection detected. Using all items in the list.", "Info", wx.ICON_INFORMATION)
            selected_items = list(self._check_listbox.GetStrings())
            selected_paths = [self.file_paths[item] for item in selected_items]
        path_simulations = self.datadir_simulations

        #dx,dy,nbx,nby,X,Y = False, False, False, False, False, False
        _interpol = interpolating_raster()
        for sim_ in selected_paths:
            if sim_.name.startswith("sim_"):
                self.sims[sim_.name] = sim_
                fn_read = Path(path_simulations/ sim_ / "simul_gpu_results")
                logging.info(_(f"Found simulation folder: {sim_}"))
                parts = sim_.name.split("sim_")
                if len(parts) > 1:
                    logging.info(_("Computing water depth and velocity danger maps"))
                    name = parts[1]
                    # dx,dy,nbx,nby,X,Y = display_info_header(self.input_dx, self.input_nbxy, self.input_O, fn_write.with_suffix(".bin"))
                    _interpol.export_z_or_v_bin(fn_read, self._manager, name, type_hazard="z_v", type_extraction = type_extraction, param_danger = param_danger, threshold=threshold)
                
                else:
                    logging.info(_(f"Please, ensure your simulations are named with the return period, e.g sim_T4"))
            else:
                logging.info(_('No folder found / selected. Please try again...'))
        
        dlg = wx.MessageDialog(self,
                        "Danger maps created in INPUT\WATER_DEPTH\... and INPUT\VELOCITY\...",
                        "Success.",
                        wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        
        
    def OnDEM(self,e):
        """Import and create the inputs for the interpolation routine (name including 'MNT_...' and 'MNT_..._with_mask'.
        See function MTN_And_mask_creation_all"""
        path = self._manager.IN_SA_DEM
        names_inDEM = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        if len(names_inDEM) != 0 :
            dialog = wx.MessageDialog(None, f"The DEM_FILES folder is not empty and contains the files {names_inDEM}. ", "Confirmation", wx.YES_NO | wx.ICON_QUESTION)
            dialog.SetYesNoLabels("Delete and reload", "Keep and leave")
            response = dialog.ShowModal()
            if response == wx.ID_YES:
                for file_name in names_inDEM:
                    file_path = os.path.join(path, file_name)
                    os.remove(file_path)
                logging.info(_("Files in DEM_FILES deleted."))
            else :
                logging.info(_("No update of DEM_FILES."))
                return

        #Avec ajout BATHT_AFTER_SCRIPT
        if self.gpu_bathy == None:
            with wx.FileDialog(self, "Please select the bathymetry file of simulation, with all the modifications (e.g. '__bathymetry_after_scripts.tif') in .tif format.", wildcard="TIFF files (*.tif)|*.tif",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
                if dlg.ShowModal() != wx.ID_OK:
                    return
                self.gpu_bathy = dlg.GetPath()
            
        with wx.FileDialog(self, "Please select the DEM file in .tif format (without modifications, MNTmodifs_ will be used afterwards).", wildcard="TIFF files (*.tif)|*.tif",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            result = dlg.ShowModal()
            if result != wx.ID_OK:
                return

            path_DEM_base = dlg.GetPath()
            logging.info(_("DEM file selected."))

        #DEM and masked DEM creation
        path = self._manager.IN_CH_DEM_SC
        names_inCHVUL_MNTmodifs = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.startswith("MNTmodifs_")]
        #path_MNT_computed is the path to the DEM with the MNTmodifs if exist, or the given true DEM if not
        path_MNT_computed = Path(path_DEM_base)
        if len(names_inCHVUL_MNTmodifs) !=0:
            path_MNT_computed = Path(self._manager.IN_CH_DEM_MNT_tif.with_suffix('.tif'))
            dialog = wx.MessageDialog(None, f"Please modify the 'MNTmodifs_' files in INPUT\CHANGE_VULNE\... as in the hydraulic scenario you want to study. They are: {names_inCHVUL_MNTmodifs}", "Confirmation", wx.YES_NO | wx.ICON_QUESTION)
            dialog.SetYesNoLabels("Done, continue", "Not done, stop")
            response = dialog.ShowModal()

            if response == wx.ID_NO:
                logging.info(_("No modifications done in MNTmodifs_ files, process stopped."))
                return

        if os.path.exists(self._manager.IN_CH_DEM_SC):
            existence=False
            existence, fail = self._func.create_vrtIfExists(Path(path_DEM_base), Path(self._manager.IN_CH_DEM_SC), Path(self._manager.IN_CH_DEM_MNT_VRT), name="MNTmodifs_")
            if existence:
                self._manager.translate_vrt2tif(self._manager.IN_CH_DEM_MNT_VRT, self._manager.IN_CH_DEM_MNT_tif)
                logging.info(_(f"Scenarios have been applied to DEM see {self._manager.IN_CH_DEM_MNT_tif}.tif."))
                WA_mask = WolfArray(self._manager.IN_CH_DEM_MNT_tif.with_suffix('.tif'))
                WA_mask.write_all(Path(self._manager.IN_SA_DEM / "MNT_loaded.bin"))   
                     
            else :
                logging.info(_(f"No MNTmodifs_ files in {self._manager.IN_CH_DEM_SC}. The given file {path_DEM_base} has not been modified"))
                WA_mask = WolfArray(path_DEM_base)
                WA_mask.write_all(Path(self._manager.IN_SA_DEM / "MNT_loaded.bin"))
        else:
            logging.error(_(f"Path {self._manager.IN_CH_DEM_SC} does not exist."))

        
        #self._manager.IN_CH_DEM_MNT_tif   ou fn_mnt_cropped : ground + riverbed
        fn_wherebuildings_buffer = self._manager.IN_CH_DEM_SC/ "buffer_wherebuilding.tif"
        fn_mask = self._manager.IN_SA_DEM / "MNT_computed_with_mask.tif"
        _interpol = interpolating_raster()
        _interpol.MNT_and_mask_creation_all(self.gpu_bathy, path_MNT_computed, fn_wherebuildings_buffer, fn_mask)
        if fn_wherebuildings_buffer.exists():
            fn_wherebuildings_buffer.unlink()
        if fn_mask.exists():
            fn_mask.unlink()
        dlg = wx.MessageDialog(self,
                    "DEM files created in INPUT\WATER_DEPTH\...\DEM_FILES.",
                    "Success.",
                    wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        return
    
    def check_and_convert_rasters(self, manager, prefix, type_file, numpy_type, nodata_value, message_supp=None):
        logging.info(_(f"Checking the scenarios for {prefix}."))

        #tif_paths = self._manager.get_modifiedrasters(name=prefix)
        tif_paths = manager.get_modifiedrasters(name=prefix)
        good, bad, bad_paths = [], [], []

        for f in tif_paths:
            ds = gdal.Open(f)
            if ds:
                file_type = gdal.GetDataTypeName(ds.GetRasterBand(1).DataType)
                ds = None
                if file_type == type_file:
                    good.append(f.stem)
                else:
                    suffix_to_add = f"_{file_type}"
                    new_name = f.parent / f"{f.stem}{suffix_to_add}{f.suffix}"
                    if not f.stem.endswith(suffix_to_add):
                        f.rename(new_name)
                    else:
                        new_name = f
                    bad.append(new_name.stem)
                    bad_paths.append(new_name)

        if bad:
            message_intro = (
                f"Detected {prefix} scenario files:\n"
                f"{', '.join([f.stem for f in tif_paths])}\n\n"
                f"However, wrong type in file(s): {', '.join(bad)}. "
                f"Its/Their type has been added to their name (expected {type_file}).\n\n"
                f"Do you want to try to convert them to {type_file} automatically?"
            )

            dlg = wx.MessageDialog(None, message_intro, "Warning", wx.YES_NO | wx.ICON_WARNING)
            result = dlg.ShowModal()
            dlg.Destroy()

            if result == wx.ID_YES:
                for path in bad_paths:
                    with gdal.Open(path, gdal.GA_ReadOnly) as ds:
                        band = ds.GetRasterBand(1)
                        arr = band.ReadAsArray()
                        nodata = band.GetNoDataValue()
                        geotransform = ds.GetGeoTransform()
                        projection = ds.GetProjection()

                    # SPÉCIAL POUR LE CAS int8
                    if type_file == "Byte":
                        mask_valid = np.ones_like(arr, dtype=bool)
                        if nodata is not None:
                            mask_valid = arr != nodata

                        valid_values = arr[mask_valid]
                        if not np.all((valid_values >= 1) & (valid_values <= 5)):
                            wx.MessageBox(
                                f"Impossible to change the type to int8, there exist other type of data in the raster(s) !\n {message_supp}",
                                "Error", wx.OK | wx.ICON_ERROR
                            )
                            return

                    arr_new = arr.astype(numpy_type)
                    if nodata is not None:
                        arr_new[arr == nodata] = nodata_value
                    else:
                        arr_new[arr_new < 1] = nodata_value #if nodata doesnt exist

                    dirname, filename = os.path.split(path)
                    new_filename = filename.replace(prefix, f"{prefix}AUTO_").replace(".tif", f"_to_{type_file}.tif")
                    old_filename = filename.replace(prefix, f"OLD_{prefix}")
                    new_path = os.path.join(dirname, new_filename)
                    old_path = os.path.join(dirname, old_filename)

                    os.rename(path, old_path)
                    driver = gdal.GetDriverByName("GTiff")
                    out_ds = driver.Create(new_path, arr.shape[1], arr.shape[0], 1,
                                        gdal.GetDataTypeByName(type_file))
                    out_ds.SetGeoTransform(geotransform)
                    out_ds.SetProjection(projection)
                    out_band = out_ds.GetRasterBand(1)
                    out_band.WriteArray(arr_new)
                    out_band.SetNoDataValue(nodata_value)
                    out_band.FlushCache()
                    out_ds = None

                wx.MessageBox(
                    f"Files converted to {type_file}. Previous ones renamed with 'OLD_...'.",
                    "Information", wx.OK | wx.ICON_INFORMATION
                )
        else:
            wx.MessageBox(
                f"Detected {prefix} scenario files:\n{', '.join([f.stem for f in tif_paths])}\n Everything is fine.",
                "Information", wx.OK | wx.ICON_INFORMATION
            )
    
    def OnCheckMNTmodifs(self,e):
        """Checks if scenarios MNTmodifs_ exist in CHANGE_VULNE and test the type (float32)"""
        self.check_and_convert_rasters(self._manager, "MNTmodifs_", "Float32", np.float32, 99999.)
        return

    def OnInterpolation(self,e):
        """Interpolates the last extracted time steps present in LAST_STEP_EXTRACTED using the fast marching
        interpolation routine, by creating a batch file
        while performing multiple checks on the required input files."""               
        _interpol = interpolating_raster()

        if self.file_paths is None:  # Si on n’a pas chargé de simulations : on recrée la structure et ce qu'on aurait eu, mais avec tous les fichiers présents
            iftest = True
            checked_paths = []
        
        else : 
            checked_names = self._check_listbox.GetCheckedStrings()
            if not checked_names:
                logging.info(_("No items selected. Adding all paths."))
                checked_paths = list(self.file_paths.values())
                iftest = False
            else:
                logging.info(_("Adding only the selected simulations."))
                checked_paths = [self.file_paths[name] for name in checked_names]
                iftest = False

            if len(self.file_paths) == 0 :
                return logging.info(_("No files in EXTRACTED_LAST_STEP_WD. Please provide some or use the 'Load gpu simulation' button."))

        #interp_bool, renamed_files = _interpol.batch_creation_and_interpolation_fotran_holes(self._manager, checked_paths, iftest)
        interp_bool, renamed_files = _interpol.batch_creation_and_interpolation_python_eikonal(self._manager, checked_paths, iftest, True)
        
        if interp_bool:
            logging.info(_("Filling completed."))
            with wx.MessageDialog(self, f"Filling completed. Created files : {renamed_files}",
                        "Redirecting", wx.OK | wx.ICON_INFORMATION) as dlg:
                dlg.ShowModal()
            update_info_header(self.input_dx,self.input_nbxy,self.input_O,self._manager.IN_SA_INTERP)
            self._check_listbox_Ti.Set(self._manager.get_list_interp())
        else :
            logging.error(_("Something went wrong for the interpolation."))
            
    def OnToggleAdmin(self, e):
        if self.toggle_state_Admin:
            self.toggle_state_Admin = False
            self._but_toggle_admin.SetBackgroundColour(wx.NullColour)
            #self._but_setcomp.Hide()
            #self._but_readresults.Hide()
            return
        
        dlg = wx.TextEntryDialog(self, "Enter developer password:", "Authentication")
        if dlg.ShowModal() == wx.ID_OK:
            password = dlg.GetValue()
            if password == "LetMeIn#":
                self.toggle_state_Admin = True
                self._but_toggle_admin.SetBackgroundColour(wx.Colour(175, 175, 175))
                #self._but_setcomp.Show()
                #self._but_readresults.Show()
            
                self.mapviewer.Refresh()
            else:
                wx.MessageBox("Wrong password.", "Error")
                self.toggle_state_Admin = False
                self._but_toggle_admin.SetBackgroundColour(wx.NullColour)
        dlg.Destroy()
        
    def OnInput(self, e):
        multiple = 0
        dlg1 = wx.SingleChoiceDialog(
            self,
            message="What hazard variable do you want to read in the GPU simulations?",
            caption="Hazard Variable Choice",
            choices=["only wd", "both wd and v"]
        )

        if dlg1.ShowModal() == wx.ID_OK:
            selection1 = dlg1.GetStringSelection()
            if selection1 == "only wd" :
                hazard_choice = "wd" 
            else :
                hazard_choice = "both"
        else:
            return

        dlg1.Destroy()
        
        if hazard_choice == "both":
            multiple_str = wx.GetTextFromUser(
                message="What buffer size (as the factor of the resolution dx) do you want to use\n (to capture the maximum velocity)? Enter a number between 1 and 10:",
                caption="Buffer size",
                parent=self
            )
            try:
                multiple = int(multiple_str)
                if not (1 <= multiple <= 10):
                    wx.MessageBox("Value must be between 1 and 10.", "Error", wx.ICON_ERROR)
                    return
            except ValueError:
                wx.MessageBox("Invalid number.", "Error", wx.ICON_ERROR)
                return

        dlg2 = wx.SingleChoiceDialog(
            self,
            message="What operator for wd?",
            caption="Operator Choice",
            choices=["mean", "max", "median", "percentil"]
        )
        percentil=None
        if dlg2.ShowModal() == wx.ID_OK:
            operator_choice = dlg2.GetStringSelection()
            if operator_choice == "percentil":
                dlg_percentil = wx.TextEntryDialog(
                    self,
                    message="Enter the desired percentile (0-100):",
                    caption="Percentile Input"
                )
                if dlg_percentil.ShowModal() == wx.ID_OK:
                    try:
                        percentil = float(dlg_percentil.GetValue())
                        if not (0 <= percentil <= 100):
                            wx.MessageBox("Value must be between 0 and 100", "Invalid Input", wx.ICON_ERROR)
                            return
                    except ValueError:
                        wx.MessageBox("Please enter a valid number", "Invalid Input", wx.ICON_ERROR)
                        return
                else:
                    return
        else:
            return
        
        dlg2.Destroy()
        
        Ti_list = [self._check_listbox_Ti.GetString(i) for i in range(self._check_listbox_Ti.GetCount()) if self._check_listbox_Ti.IsChecked(i)]
        if Ti_list ==[]:
            logging.error(_("No scenario selected in the checkbox, all the simulations are selected by default."))
            Ti_list = list(self._check_listbox_Ti.GetStrings())
        logging.info(_(f"Ti_list = {Ti_list}"))
        
        logging.info(_(f"Ti_list = {Ti_list}"))
        resolution = self.input_dx.GetLabel()
        values = resolution.strip("()").split(",")
        dx = float(values[0])

        save_where_output = self._func.pre_processing_auto(Ti_list, self._manager.main_dir, self._manager._study_area, self._manager.scenario, multiple, dx, percentil, operator_wd = operator_choice, hazard = hazard_choice)
        
        if len(save_where_output) == 0 :
            with wx.MessageDialog(self,
                                        f"Something went wrong.",
                                        "Error in preprocessing",
                                        style=wx.OK| wx.ICON_ERROR) as dlg:
                        dlg.ShowModal()
        else :
            with wx.MessageDialog(self,
                                        f"Input tables successfully created in {save_where_output}.",
                                        "Preprocessing finished.",
                                        style=wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.ShowModal()
                    
                    
    def OnDefault_TEMP(self, e):
        """ Impute default values to inputs and run INBE on each Ti"""
        if self._manager is None:
            return
        
        Ti_list = [self._check_listbox_Ti.GetString(i) for i in range(self._check_listbox_Ti.GetCount()) if self._check_listbox_Ti.IsChecked(i)]
        if Ti_list ==[]:
            logging.error(_("No scenario selected in the checkbox, all the simulations are selected by default."))
            Ti_list = list(self._check_listbox_Ti.GetStrings())
        logging.info(_(f"Ti_list = {Ti_list}"))
        
        inflation = float(self._inflation.GetValue())
        type_computation = "from_wolfsimu"
        self.df_results_Ti, save_output_TEMP, save_output_defaultINPUT = self._func.computation_dfesults_forfolder(self._manager, type_computation, Ti_list, inflation)
        
        if len(save_output_defaultINPUT) == 0 :
            with wx.MessageDialog(self,
                                        f"Something went wrong. Nothing created.",
                                        "Error in the computations.",
                                        style=wx.OK| wx.ICON_ERROR) as dlg:
                        dlg.ShowModal()
        else :
            paths_in = "\n".join(str(p) for p in save_output_defaultINPUT)
            paths_temp = "\n".join(str(p) for p in save_output_TEMP)
            
            dlg = wx.MessageDialog(
                self,
                "Do you want to spread the information of damage on a raster?",
                "Damage raster",
                wx.YES_NO | wx.ICON_QUESTION
            )

            ifraster = dlg.ShowModal()
            dlg.Destroy()

            if ifraster == wx.ID_YES:
                self._func.raster_auto(self._manager, "individual_damage", Ti_list)

            with wx.MessageDialog(self,
                                        f"Default values imputed to the input in:\n{paths_in}\n\nAnd individual damage (inflation {inflation}) computed in:\n{paths_temp}.",
                                        "Preprocessing finished.",
                                        style=wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.ShowModal()
                        
    def Oncombined_OUTPUT(self,e):
        """Compute the combined damage"""
        
        #Option de comment combiner, majorer damage ? To do
        
        ponds = self._manager.get_ponderations() 
        logging.info(_("Ponderation coeficients (computed automatically based on available set of damage files):"))
        logging.info(ponds)
        if self._manager is None:
            return

        dlg2 = wx.SingleChoiceDialog(
            self,
            message="What kind of combinaison?",
            caption="Combinaison choice",
            choices=["Weighted sum"]#, "Squared (to code)", "..."]
        )

        if dlg2.ShowModal() == wx.ID_OK:
            operator_choice = dlg2.GetStringSelection()
        else:
            return

        dlg2.Destroy()
        
        if operator_choice != "Weighted sum":
            with wx.MessageDialog(self,
                                        f"Need to be coded :)",
                                        "Be patient.",
                                        style=wx.OK| wx.ICON_ERROR) as dlg:
                        dlg.ShowModal()
            return
        #if df_results_Ti == None :
        #    with wx.MessageDialog(self,
        #                                f"Please use the previous button, or code something to read the indiv damages...",
        #                                "Error in the computations.",
        #                                style=wx.OK| wx.ICON_ERROR) as dlg:
        #                dlg.ShowModal()
        #    return
        
        unused, output_path = self._func.computation_combined_damage(ponds, self._manager)
        
        dlg = wx.MessageDialog(
                self,
                "Do you want to spread the information of combined damage on a raster?",
                "Damage raster",
                wx.YES_NO | wx.ICON_QUESTION
            )

        ifraster = dlg.ShowModal()
        dlg.Destroy()

        if ifraster == wx.ID_YES:
            self._func.raster_auto(self._manager, "combined")
                
        
        with wx.MessageDialog(self,
                                        f"Combined damage computed, and written in {output_path}.",
                                        "Computations finished.",
                                        style=wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.ShowModal()
                        
    def OnReadResults(self, e):
        sort_percentil = float(self._tri.GetValue())
        cols = ["code", "d_cleaning", "d_removal", "d_non_stru", "d_structural", "d_finishing", "d_systems", "d_total"]
        
        if not self._manager.OUT_COMB.exists():
            logging.error(_(f"No file {self._manager.OUT_COMB}. Please, compute it first."))
            wx.MessageBox(_(f"No file {self._manager.OUT_COMB}. Please, compute it first.", "Missing file.", wx.ICON_ERROR))
            return
        df_results = pd.read_excel(self._manager.OUT_COMB, usecols=cols)
        
        
        sums = df_results.sum(numeric_only=True)


        #summary = '\n'.join([f"{col} : {val:,.0f} €" for col, val in sums.items()])
        summary = '\n'.join([f"{col[2:].capitalize()} : {val:,.0f} €" for col, val in sums.items()])
        with wx.MessageDialog(self,
                            f"Sum of damage per categories :\n\n{summary}",
                            "Quick analysis.",
                            style=wx.OK | wx.ICON_INFORMATION) as dlg:
            dlg.ShowModal()
                
        
        dlg = wx.MessageDialog(
                self,
                "Do you want to plot the damage histogram for every residential building ?",
                "Histogram creation.",
                wx.YES_NO | wx.ICON_QUESTION
            )
        ifhisto = dlg.ShowModal()
        dlg.Destroy()

        if ifhisto == wx.ID_YES:
            self._func.plot_damage(df_results, sorted_cond = True)
        
        return
    
    #def OnSetComp0(self, e):
    #    """Analyze two or more scenarios with a baseline"""
    #    with wx.MessageDialog(
    #        self,
    #        "After clicking OK, please select at least two damage scenarios (individual or combined) to compare (of a same study area).\n"
    #        "The first one selected will be used as the reference.\n\n"
    #        "⚠ No tests coded — the user is responsible for the comparison.\n\n"
    #        "The file selection dialog will reopen until you click Cancel, press Escape, or close the window.",
    #        "Instructions.",
    #        style=wx.OK | wx.ICON_INFORMATION
    #    ) as dlg:
    #        dlg.ShowModal()

    #    paths = []

    #    if self._manager is not None and self._manager.main_dir is not None:
    #        defaultDir = self._manager.main_dir
    #    else:
    #        defaultDir = os.getcwd()

    #    while True:
    #        with wx.FileDialog(
    #            self,
    #            "Select a damage scenario file",
    #            defaultDir=defaultDir,
    #            wildcard="Excel files (*.xlsx)|*.xlsx",
    #            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    #        ) as file_dlg:

    #            if file_dlg.ShowModal() == wx.ID_CANCEL:
    #                break

    #            path = file_dlg.GetPath()  

    #            if path:
    #                paths.append(path)
    #                defaultDir = os.path.dirname(path) 
    #    
    #    with wx.MessageDialog(
    #        self,
    #        f"{paths}",
    #        "Scenarios selected:",
    #        style=wx.OK | wx.ICON_INFORMATION
    #    ) as dlg:
    #        dlg.ShowModal()

    #    self._func.histo_total_from_list(paths, float(self._tri.GetValue()))
    #    return
    
    def OnSetComp0(self, e):
        """Analyze two or more scenarios with a baseline"""
        #scenarios = [self._listbox_CompScen.GetString(i) for i in self._listbox_CompScen.GetCheckedItems()]
        checked_idx = self._listbox_CompScen.GetCheckedItems()
        scenarios   = [self.items[i][1] for i in checked_idx]  
        study_areas = [self.items[i][0] for i in checked_idx]  

        if len(scenarios) < 2:
            wx.MessageBox("Please select at least 2 scenarios.", "Not enough scenarios to compare.", wx.ICON_ERROR)
            return
        
        dlg1 = wx.SingleChoiceDialog(
            self,
            message="Which of the selected scenarios is the reference for comparison ?",
            caption="Reference scenario",
            choices=scenarios
        )

        if dlg1.ShowModal() == wx.ID_OK:
            reference = dlg1.GetStringSelection()
        else:
            return
        dlg1.Destroy()
        
        #Reference = the FIRST
        idx_ref = scenarios.index(reference)
        scenarios = [scenarios[idx_ref]] + [sc for i, sc in enumerate(scenarios) if i != idx_ref]
        study_areas = [study_areas[idx_ref]] + [sa for i, sa in enumerate(study_areas) if i != idx_ref]

        instances = [INBE_Manager(main_dir=self.maindir, Study_area=sa, scenario=sc) for sc, sa in zip(scenarios, study_areas)] #zip life
        
        dlg2 = wx.SingleChoiceDialog(
                self,
                message=f"What do you want to compare (selected reference = {reference}) ?",
                caption="Comparison choice",
                choices=["Individual damage (Ti)", "Combined damage"]
            )

        if dlg2.ShowModal() == wx.ID_OK:
                choice = dlg2.GetStringSelection()
        else:
            return
        dlg2.Destroy()
        
        if choice == "Individual damage (Ti)":
            dlg3 = wx.SingleChoiceDialog(
                self,
                message="Which return period do you want to compare ?",
                caption="Comparison Choice",
                choices=instances[0].get_list_individual_T(instances[0])
            )

            if dlg3.ShowModal() == wx.ID_OK:
                    choice_T = dlg3.GetStringSelection()
            else:
                return
            dlg3.Destroy()
            
            paths = [inst.OUT_SCEN_DIR / f"individual_damage_T{choice_T}.xlsx" for inst in instances]
        else: 
            choice_T = None
            paths = [inst.OUT_COMB for inst in instances]

        self._func.histo_total_from_list(paths, float(self._tri.GetValue()))
        #si len scatter_INBE_dtotal > 2 alors deux à deux avec le bon baseline [0]
        
        
        for instB in instances[1:]:
            self._func.scatter_INBE_dtotal(instances[0], instB, max_val=None, Ti = choice_T, quant = float(self._tri.GetValue()))
        