"""
Author: University of Liege, HECE
Date: 2025

Copyright (c) 2025 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx
from matplotlib.figure import Figure
from osgeo import gdal, osr
from pathlib import Path
from scipy.ndimage import label
from shapely.geometry import Polygon
import geopandas as gpd
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import shutil
import textwrap
import wx

from ..interpolating_raster import interpolating_raster
from ..PyDraw import WolfMapViewer, draw_type
from ..PyGui import MapManager
from ..PyTranslate import _
from ..Results2DGPU import wolfres2DGPU
from ..scenario.config_manager import Config_Manager_2D_GPU
from ..wolf_array import WolfArray, header_wolf
from .acceptability import Base_data_creation, Database_to_raster, Vulnerability, Acceptability
from .acceptability import steps_base_data_creation, steps_vulnerability, steps_acceptability
from .func import Accept_Manager


BATHYMETRY_FOR_SIMULATION = "__bathymetry_after_scripts.tif"

def riverbed_trace(fn_read_simu, fn_output, threshold, type_extraction):
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
        wd = wolfres2DGPU(fn_read_simu).danger_map_only_h(0,-1,1)
        wd.array[wd.array > 1000] = 0
        wd.array[wd.array > threshold] = 1
        wd.array[wd.array < threshold] = 0
        wd.as_WolfArray()
        wd.nodata=0
        wd.write_all(Path(fn_output))


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

def create_INPUT_TEMP_OUTPUT_forScenario(maindir, study_area, scenario, simu_gpu):
    """Creates folder for a new study area or/and scenario. The last argument simu_gpu is used when loading simulation (indicates path to the simulation folder),
    if not used, indicate None to ignore it."""
    study_area = Path(study_area).stem
    base_pathwd = Path(maindir) / "INPUT" / "WATER_DEPTH" / study_area / scenario
    subfolders = ["DEM_FILES", "INTERP_WD", "EXTRACTED_LAST_STEP_WD"]
    os.makedirs(base_pathwd, exist_ok=True)
    for folder in subfolders:
        os.makedirs(os.path.join(base_pathwd, folder), exist_ok=True)
    base_pathch = Path(maindir) / "INPUT" / "CHANGE_VULNE" / study_area / scenario
    os.makedirs(base_pathch, exist_ok=True)

    if simu_gpu != None:
        path_bat_gpu = Path(simu_gpu) / "bathymetry.tif"
        if path_bat_gpu.exists():
            create_shapefile_from_prop_tif(path_bat_gpu, Path(maindir) / "INPUT" / "STUDY_AREA" / f"{study_area}.shp")
            logging.info(_("Study area file created in INPUT/STUDY_AREA."))
        else :
            logging.error(_(f"Error in the study area creation : no bathymetry.tif file in the given simulation folder {simu_gpu}. Please provide it in this folder and try again."))

    Accept_Manager(main_dir=maindir, Study_area=study_area, scenario=scenario)
    logging.info(_(f"Files created in INPUT, TEMP and OUTPUT for the study area named '{study_area}', and the scenario named '{scenario}'"))
    return

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
    Displays the header at the path 'fn', and update the values displayed in the acceptability window.
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

def create_vuln_file(tif_file, path_vuln):
    src_ds = gdal.Open(str(tif_file))
    driver = gdal.GetDriverByName("GTiff")

    xsize = src_ds.RasterXSize
    ysize = src_ds.RasterYSize
    geotransform = src_ds.GetGeoTransform()
    projection = src_ds.GetProjection()

    # lire le raster source
    src_band = src_ds.GetRasterBand(1)
    src_data = src_band.ReadAsArray()
    src_nodata = src_band.GetNoDataValue()

    # préparer le tableau de sortie (1 partout)
    data = np.ones((ysize, xsize), dtype=np.uint8)

    # mettre 127 là où le raster source est nodata
    if src_nodata is not None:
        mask = src_data == src_nodata
        data[mask] = 127

    # créer le raster vuln_
    output_file = path_vuln / tif_file.name.replace("bath_", "vuln_")
    dst_ds = driver.Create(str(output_file), xsize, ysize, 1, gdal.GDT_Byte)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(projection)

    band = dst_ds.GetRasterBand(1)
    band.WriteArray(data)
    band.SetNoDataValue(127)

    dst_ds = None
    src_ds = None
    
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

        # vuln_ file
        create_vuln_file(tif_file,path_vuln)

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

def mapviewer_display(list_path, mapviewer=None):
    """ Load the output in the mapviewer on WOLF """
    results = " and ".join(Path(path).name for path in list_path)
    dlg = wx.MessageDialog(None, _(f'Do you want to load {results} in the mapviewer ?'), _('Load file'), wx.YES_NO)
    ret = dlg.ShowModal()
    dlg.Destroy()
    if ret != wx.ID_YES:
        return

    if mapviewer is None:
        mapviewer = WolfMapViewer(title="OUTPUT Acceptability manager")
    for path in list_path:
        myarray = WolfArray(path)
        newid = Path(path).name
        mapviewer.add_object('array', newobj=myarray, id=newid)
    logging.info(_("Press F5 to refresh the mapviewer."))
    mapviewer.Refresh()

class AcceptabilityGui(wx.Frame):
    """ The main frame for the vulnerability/acceptability computation """
    def __init__(self, parent=None, width=1024, height=500):

        super(wx.Frame, self).__init__(parent, title='Acceptability score manager', size=(width, height))

        self._manager = None
        self._mapviewer = None
        self.InitUI()

    @property
    def mapviewer(self):
        return self._mapviewer

    @mapviewer.setter
    def mapviewer(self, value):
        from ..PyDraw import WolfMapViewer

        if not isinstance(value, WolfMapViewer):
            raise TypeError("The mapviewer must be a WolfMapViewer")

        self._mapviewer = value

    def OnHoverEnter(self, event):
        """Dynamic colour layout 1"""
        self._but_creation.SetBackgroundColour(wx.Colour(100,100,100))
        self._but_creation.Refresh()
        event.Skip()

    def OnHoverLeave(self, event):
        """Dynamic colour layout 2"""
        self._but_creation.SetBackgroundColour(wx.Colour(150,150,150))
        self._but_creation.Refresh()
        event.Skip()

    def layout(self, self_fct):
        """Update the layers for the main buttons"""
        font = self_fct.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self_fct.SetFont(font)
        self_fct.SetBackgroundColour(wx.Colour(150,150,150))
        self_fct.Bind(wx.EVT_ENTER_WINDOW, self.OnHoverEnter)
        self_fct.Bind(wx.EVT_LEAVE_WINDOW, self.OnHoverLeave)

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

                new_name = self._manager.OUT_MASKED_RIVER_S

                with wx.MessageDialog(self, f"Modified riverbed imported and called Masked_River_extent_scenarios.tiff.",
                    "File imported.", wx.OK | wx.ICON_INFORMATION) as dlg:
                    dlg.ShowModal()

                if new_name.exists():
                    new_name.unlink()

                copied_file.rename(new_name)
                logging.info(_(f"File renamed to: {new_name}"))
            else:
                logging.info(_('No file selected. Please try again.'))

        elif menu_id == 2: #No file, so need to create
            logging.info(_("Option 2 : pointing to simulation with low discharge (no overflows!)."))

            with wx.DirDialog(self, "Please select a simul_gpu_results folder of a simulation with low discharges (no overflows).", style=wx.DD_DEFAULT_STYLE) as dir_dlg:
                if dir_dlg.ShowModal() == wx.ID_OK:
                    selected_folder = Path(dir_dlg.GetPath())
                    if os.path.basename(selected_folder) == "simul_gpu_results" :
                        logging.info(_(f"Selected folder: {selected_folder}"))
                        fn_output = self._manager.OUT_MASKED_RIVER_S
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
                                        else:
                                            type_extraction = "danger_map"
                                    dialog.Destroy()
                                    logging.info(_("Detecting riverbed."))
                                    riverbed_trace(selected_folder, fn_output, threshold, type_extraction=type_extraction)
                                    logging.info(_("File created."))
                                    with wx.MessageDialog(
                                        self,
                                        "Masked_River_extent_scenarios.tiff successfully created.",
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

        # 1st LINE - Loading acceptability folder
        panel = wx.Panel(self)
        self._but_maindir = wx.Button(panel, label=_('Main Directory'))
        self._but_maindir.SetToolTip(_("To indicate where the main acceptability\n folder is located."))
        self._but_maindir.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self._but_maindir.Bind(wx.EVT_BUTTON, self.OnMainDir)

        self._listbox_studyarea = wx.ListBox(panel, choices=[], style=wx.LB_SINGLE)
        self.layout_listbox(self._listbox_studyarea)
        self._listbox_studyarea.Bind(wx.EVT_LISTBOX, self.OnStudyArea)
        self._listbox_studyarea.SetToolTip(_("Choose the study area existed in the folder."))

        self._listbox_scenario = wx.ListBox(panel, choices=[], style=wx.LB_SINGLE)
        self.layout_listbox(self._listbox_scenario)
        self._listbox_scenario.Bind(wx.EVT_LISTBOX, self.OnScenario)
        self._listbox_scenario.SetToolTip(_("Choose the acceptability scenario."))

        sizer_ver_small = wx.BoxSizer(wx.VERTICAL)
        self._but_checkfiles = wx.Button(panel, label=_('Check structure'))
        self._but_checkfiles.Bind(wx.EVT_BUTTON, self.OnCheckFiles)
        self._but_checkfiles.SetToolTip(_("Checks if the folder is correctly structured\n with INPUT, TEMP, OUTPUT."))
        self._but_checksim = wx.Button(panel, label=_('Check simulations'))
        self._but_checksim.SetToolTip(_("Displays the loaded simulations, interpolated in INTERP_WD."))
        self._but_checksim.Bind(wx.EVT_BUTTON, self.OnHydrodynInput)

        self._but_checkpond= wx.Button(panel, label=_('Check ponderation'))
        self._but_checkpond.Bind(wx.EVT_BUTTON, self.OnCheckPond)
        self._but_checkpond.SetToolTip(_("Displays a graph of the computed weighting coefficient\n of the final acceptability computations."))

        # 2nd LINE - Hydrodynamic part
        self._but_loadgpu = wx.ToggleButton(panel, label=_('Working with new\n hydraulic scenarios'))
        self._but_loadgpu.SetToolTip(_("To load or change the hydraulic simulations"))
        self._but_loadgpu.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self._but_loadgpu.Bind(wx.EVT_TOGGLEBUTTON, self.OnLoadingSimu)
        sizer_hor2.Add(self._but_loadgpu, 1, wx.ALL | wx.EXPAND, 0)

        self._check_listbox = wx.CheckListBox(panel, choices=[], style=wx.LB_MULTIPLE | wx.CHK_CHECKED)
        self.layout_listbox(self._check_listbox)
        self.sims = {}
        sizer_hor2.Add(self._check_listbox, 1, wx.ALL | wx.EXPAND, 0) #ajouter!! sinon s'affiche pas

        self._but_danger = wx.Button(panel, label=_('Extract last step or\n compute danger map ▼'))
        self._but_danger.SetToolTip(_("To create the danger maps of velocities and water depth. Please be patient."))
        self._but_danger.Bind(wx.EVT_BUTTON, self.on_button_click2)
        sizer_hor2.Add(self._but_danger, 1, wx.ALL | wx.EXPAND, 0)
        
        self.menu2 = wx.Menu()
        self.menu2.Append(1, _("Extract the last step of the simulation."))
        self.menu2.Append(2, _("Compute the danger maps of the simulation."))
        self.menu2.Bind(wx.EVT_MENU, self.OnDanger)
        
        sizer_ver_small2 = wx.BoxSizer(wx.VERTICAL)
        self._but_DEM = wx.Button(panel, label=_("Check  DEM, DTM for interpolation"))
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
        text_threads = wx.StaticText(panel, label=_('Number of threads:'))
        self._nb_process = wx.SpinCtrl(panel, value=str(os.cpu_count()), min=1, max=os.cpu_count())
        self._nb_process.SetToolTip("Number of threads to be used in the computations.")
        self._but_toggle_admin = wx.ToggleButton(panel, label=_('Admin mode'))
        self._but_toggle_admin.SetToolTip("To activate admin mode. enter password.")
        self.toggle_state_Admin = False
        self._but_toggle_admin.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleAdmin)
        
        sizer_hor_threads.Add(text_dx, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self.input_dx, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(text_nbxy, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self.input_nbxy, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(text_O, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self.input_O, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(text_threads, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self._nb_process, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_threads.Add(self._but_toggle_admin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)

        # 4,5,6th lines + scenarios
        #--------------------------
        self._but_creation = wx.Button(panel, label=_('DataBase Creation'))
        self.layout(self._but_creation)
        self._but_creation.Bind(wx.EVT_BUTTON, self.OnCreation)

        self._steps_db = wx.CheckListBox(panel, choices=steps_base_data_creation.get_list_names(), style=wx.LB_MULTIPLE | wx.CHK_CHECKED)
        self._steps_db.Hide()
        self._steps_db.SetForegroundColour(wx.Colour(170, 170, 170))
        self._steps_db.SetBackgroundColour(wx.Colour(170, 170, 170)) 

        self._but_vulnerability = wx.Button(panel, label=_('Vulnerability'))
        self.layout(self._but_vulnerability)
        self._but_vulnerability.Bind(wx.EVT_BUTTON, self.OnVulnerability)
        step_Vuln_without_withoutscenarios = [item for item in steps_vulnerability.get_list_names() if item != 'APPLY_SCENARIOSVULN - 4']
        self._steps_vulnerability = wx.CheckListBox(panel, choices=step_Vuln_without_withoutscenarios, style=wx.LB_MULTIPLE | wx.CHK_CHECKED)
        self._steps_vulnerability.Hide()
        self._steps_vulnerability.SetForegroundColour(wx.Colour(170, 170, 170))
        self._steps_vulnerability.SetBackgroundColour(wx.Colour(170, 170, 170)) 
    
        # Scenarios specifics --
        self._but_checkscenario = wx.Button(panel, label=_("Check 'vuln_' scenarios"))
        self._but_checkscenario.SetToolTip(_("To display the scenario to be taken into account in CHANGE_VULNE."))
        self._but_checkscenario.Bind(wx.EVT_BUTTON, self.OnCheckScenario)

        self._but_upriverbed = wx.Button(panel, label=_("Update riverbed ▼"))
        self._but_upriverbed.SetToolTip(_("To create the raster of the riverbed trace."))
        self._but_upriverbed.Bind(wx.EVT_BUTTON, self.on_button_click)

        self.menu = wx.Menu()
        self.menu.Append(1, _("File of riverbed trace exists."))
        self.menu.Append(2, _("Point to a low discharge simulation and calculate the riverbed trace."))
        self.menu.Bind(wx.EVT_MENU, self.onRiverbed)

        self._but_toggle_scen = wx.ToggleButton(panel, label=_("Accounting for scenarios"))
        self._but_toggle_scen.SetToolTip(_("To be activated to surimpose the vuln_ files, \n and so to take into account scenarios"))
        self.toggle_state = False
        self._but_toggle_scen.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggle)

        sizer_hor_scen.Add(self._but_checkscenario, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_scen.Add(self._but_upriverbed, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)
        sizer_hor_scen.Add(self._but_toggle_scen, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)

        self._but_toggle_resamp = wx.ToggleButton(panel, label=_("Resampling [m]:"))
        self._but_toggle_resamp.SetToolTip(_("To compute the final raster with a coarser resolution than the original one."))
        self.toggle_resamp_state = False
        self._but_toggle_resamp.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleResampling)
        sizer_hor_scen.Add(self._but_toggle_resamp, flag=wx.ALIGN_CENTER | wx.TOP)
        self._but_resampling = wx.SpinCtrl(panel, value="100", min=1, max=1000)
        sizer_hor_scen.Add(self._but_resampling, flag=wx.ALIGN_CENTER | wx.TOP)

        #--

        self._but_acceptability = wx.Button(panel, label=_('Acceptability'))
        self.layout(self._but_acceptability)
        self._but_acceptability.Bind(wx.EVT_BUTTON, self.OnAcceptability)

        step_without_withoutscenarios = [item for item in steps_acceptability.get_list_names() if item != 'COMPUTE_WITH_SCENARIOS - 5']
        step_without_withoutscenarios = [item for item in step_without_withoutscenarios if item != 'RESAMPLING - 6']
        self._steps_acceptability = wx.CheckListBox(panel, choices=step_without_withoutscenarios, style=wx.LB_MULTIPLE | wx.CHK_CHECKED)
        self._steps_acceptability.Hide()
        self._steps_acceptability.SetForegroundColour(wx.Colour(170, 170, 170))
        self._steps_acceptability.SetBackgroundColour(wx.Colour(170, 170, 170)) 

        sizer_hor3.Add(self._but_creation, 1, wx.ALL | wx.EXPAND, 0)
        sizer_hor3.Add(self._steps_db, 1, wx.ALL | wx.EXPAND, 0)

        sizer_hor4.Add(self._but_vulnerability, 1, wx.ALL | wx.EXPAND, 0)
        sizer_hor4.Add(self._steps_vulnerability, 1, wx.ALL | wx.EXPAND, 0)

        sizer_hor5.Add(self._but_acceptability, 1, wx.ALL | wx.EXPAND, 0)
        sizer_hor5.Add(self._steps_acceptability, 1, wx.ALL | wx.EXPAND, 0)

        #Lines order
        sizer_ver_small.Add(self._but_checkfiles, 0, wx.ALL | wx.EXPAND, 1)
        sizer_ver_small.Add(self._but_checksim, 0, wx.ALL | wx.EXPAND, 1)
        sizer_ver_small.Add(self._but_checkpond, 0, wx.ALL | wx.EXPAND, 1)

        sizer_vert1.Add(sizer_hor1, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor2, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor_threads, 0, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor3, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor_scen, 1, wx.EXPAND, 0)
         
        sizer_vert1.Add(sizer_hor4, 1, wx.EXPAND, 0)
        sizer_vert1.Add(sizer_hor5, 1, wx.EXPAND, 0)
        
        sizer_ver_small2.Add(self._but_MNTmodifs, 0, wx.ALL | wx.EXPAND, 1)
        sizer_ver_small2.Add(self._but_DEM, 0, wx.ALL | wx.EXPAND, 1)

        sizer_hor_main.Add(sizer_vert1, proportion=1, flag=wx.EXPAND, border=0)

        #Disabled if Main Directory + SA + Scenario not selected
        self._but_acceptability.Enable(False)
        self._but_vulnerability.Enable(False)
        self._but_creation.Enable(False)
        self._but_checkfiles.Enable(False)
        self._but_DEM.Enable(False)
        self._but_MNTmodifs.Enable(False)
        self._but_extrinterp.Enable(False)
        self._but_toggle_scen.Enable(False)
        self._but_toggle_resamp.Enable(False)
        self._but_upriverbed.Enable(False)
        self._but_checkpond.Enable(False)
        self._but_checkscenario.Enable(False)
        self._but_checksim.Enable(False)
        self._but_creation.Enable(False)
        self._but_loadgpu.Enable(False)
        self._but_danger.Enable(False)

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
            with wx.MessageDialog(self, f"Missing files in INPUT. Inputs can not be created automatically : you must provide them.\n Please read the logs and terminal to see the missing ones.", "Error", wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
            return
        else :
            if (self._manager._study_area is None) or (self._manager._scenario is None):
                logging.error(_(f"No study area and/or scenario selected, no check of TEMP and OUTPUT."))
                with wx.MessageDialog(self, f"INPUT is well structured, but TEMP and OUTPUT have not been checked because there is no study area and scenario selected.", "Checking", wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.ShowModal()
            else:
                logging.info(_(f"The folder is well structured."))
                t=self._manager.check_temporary()
                o=self._manager.check_outputs()
                with wx.MessageDialog(self, f"Main directory is checked.\nINPUT is well structured, and TEMP and OUTPUT have been checked. If folders were missing, they have been created\nMain directory at {self.maindir}", "Checking", wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.ShowModal()


    def OnHydrodynInput(self,e):
        """ A test to check if the FILLED water depths files exist.
            -If YES : the code can go on
            -If NO : either need to be computed, either the code will use the baseline ones
        """

        if self._manager is None:
            logging.error(_("No main directory selected -- Nothing to check"))
            return

        if self._manager.IN_SA_INTERP is None:
            logging.error(_("No IN_SA_INTERP attribute found in the manager."))
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

    def OnCheckPond(self,e):

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


    def OnMainDir(self, e):
        """Selects the main directory to be read."""
        vanish_info_header(self.input_dx,self.input_nbxy,self.input_O)

        with wx.DirDialog(self, "Choose the main directory containing the data (folders INPUT, TEMP and OUTPUT):",
                          style=wx.DD_DEFAULT_STYLE
                          ) as dlg:

            if dlg.ShowModal() == wx.ID_OK:
                self._manager = Accept_Manager(dlg.GetPath())
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

                folders = ['CHANGE_VULNE', 'DATABASE', 'STUDY_AREA', 'CSVs', 'WATER_DEPTH', 'EPU_STATIONS_NEW']
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

                folders = ["TEMP", "OUTPUT"]
                for folder in folders:
                    if not os.path.isdir(os.path.join(self.maindir, folder)):
                        logging.info(_(f"Creating {folder} folder."))
                        os.makedirs(os.path.join(self.maindir, folder))

                self._but_acceptability.Enable(True)
                self._but_vulnerability.Enable(True)
                self._but_creation.Enable(True)
                self._but_checkfiles.Enable(True)
                self._but_toggle_resamp.Enable(True)
                self._but_upriverbed.Enable(True)
                self._but_checkscenario.Enable(True)
                self._but_checkpond.Enable(True)
                self._but_checksim.Enable(True)
                self._but_loadgpu.Enable(True)
                
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
        study_area:str = self._manager.get_list_studyareas(with_suffix=True)[e.GetSelection()]

        self._manager.change_studyarea(study_area)

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
        create_INPUT_TEMP_OUTPUT_forScenario(self.maindir, self._manager.Study_area, self._manager.scenario, None)
        update_info_header(self.input_dx,self.input_nbxy,self.input_O,self._manager.IN_SA_INTERP)

    def OnCreation(self, e):
        """ Create the database """
        if self._manager is None:
            logging.error(_("No main directory selected -- Nothing to create"))
            return
        if self._manager.IN_SA_INTERP is None:
            logging.error(_("No IN_SA_INTERP attribute found in the manager."))
            with wx.MessageDialog(self, "No simulation found in the manager. Please select the simulations first.", "Error", wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
            return

        dx,unused,unused,unused,unused,unused = update_info_header(self.input_dx,self.input_nbxy,self.input_O,self._manager.IN_SA_INTERP)
        resolution = dx
        if resolution == '':
            wx.MessageBox(
                        f"There are no files in INTERP_WD lease, use first the buttons at the second line.",
                        "Attention",
                        wx.OK | wx.ICON_ERROR
                        )
        else :
            steps = list(self._steps_db.GetCheckedStrings())
            steps = [int(cur.split('-')[1]) for cur in steps]

            if len(steps) != 0:

                wx.MessageBox(
                        f"The database will now be created, with a resolution of {dx}. This process may take some time, and the window may temporarily stop responding.",
                        "Information",
                        wx.OK | wx.ICON_INFORMATION
                        )
                Base_data_creation(self._manager.main_dir,
                                   Study_area=self._manager.Study_area,
                                   number_procs=self._nb_process.GetValue(),
                                   resolution=dx,
                                   steps=steps)

                wx.MessageBox(
                            "The database is created with the selected steps.",
                            "Information",
                            wx.OK | wx.ICON_INFORMATION
                            )
            else :
                wx.MessageBox(
                            f"Resolution of {dx}. This process may take some time, and the window may temporarily stop responding.",
                            "Information",
                            wx.OK | wx.ICON_INFORMATION
                            )
                Base_data_creation(self._manager.main_dir,
                                Study_area=self._manager.Study_area,
                                number_procs=self._nb_process.GetValue(),
                                resolution=dx)
                wx.MessageBox(
                            "The database is created for every steps.",
                            "Information",
                            wx.OK | wx.ICON_INFORMATION
                            )

    def OnLoadingSimu(self,e):
        """ Link between acceptability and simulations
            -Load a hydraulic scenarios from the scenario manager
            -Create scenario and study area if needed.
        """

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
                create_INPUT_TEMP_OUTPUT_forScenario(self.maindir, study_area, scenario, main_gpu)
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

        found_bath = search_for_modif_bath_and_copy(Path(main_gpu), Path(hydraulic_scen.parent), self._manager.IN_CH_SA_SC)
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
        path = self._manager.IN_CH_SA_SC
        names_inCHVUL_MNTmodifs = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.startswith("MNTmodifs_")]
        #path_MNT_computed is the path to the DEM with the MNTmodifs if exist, or the given true DEM if not
                
        path_MNT_computed = Path(path_DEM_base)
        if len(names_inCHVUL_MNTmodifs) !=0:
            path_MNT_computed = Path(self._manager.IN_CH_SA_SC_MNT_tif.with_suffix('.tif'))
            dialog = wx.MessageDialog(None, f"Please modify the 'MNTmodifs_' files in INPUT\CHANGE_VULNE\... as in the hydraulic scenario you want to study. They are: {names_inCHVUL_MNTmodifs}", "Confirmation", wx.YES_NO | wx.ICON_QUESTION)
            dialog.SetYesNoLabels("Done, continue", "Not done, stop")
            response = dialog.ShowModal()

            if response == wx.ID_NO:
                logging.info(_("No modifications done in MNTmodifs_ files, process stopped."))
                return

        if os.path.exists(self._manager.IN_CH_SA_SC):
            existence=False
            existence, fail = self._manager.create_vrtIfExists(Path(path_DEM_base), self._manager.IN_CH_SA_SC, self._manager.IN_CH_SA_SC_MNT_VRT, name="MNTmodifs_")
            if existence:
                self._manager.translate_vrt2tif(self._manager.IN_CH_SA_SC_MNT_VRT, self._manager.IN_CH_SA_SC_MNT_tif)
                logging.info(_(f"Scenarios have been applied to DEM see {self._manager.IN_CH_SA_SC_MNT_tif}.tif."))
                WA_mask = WolfArray(self._manager.IN_CH_SA_SC_MNT_tif.with_suffix('.tif'))
                WA_mask.write_all(Path(self._manager.IN_SA_DEM / "MNT_loaded.bin"))   
                     
            else :
                logging.info(_(f"No MNTmodifs_ files in {self._manager.IN_CH_SA_SC}. The given file {path_DEM_base} has not been modified"))
                WA_mask = WolfArray(path_DEM_base)
                WA_mask.write_all(Path(self._manager.IN_SA_DEM / "MNT_loaded.bin"))
        else:
            logging.error(_(f"Path {self._manager.IN_CH_SA_SC} does not exist."))

        #self._manager.IN_CH_SA_SC_MNT_tif   ou fn_mnt_cropped : ground + riverbed
        fn_wherebuildings_buffer = self._manager.IN_CH_SA_SC / "buffer_wherebuilding.tif"
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
                    name = parts[1]
                    # dx,dy,nbx,nby,X,Y = display_info_header(self.input_dx, self.input_nbxy, self.input_O, fn_write.with_suffix(".bin"))
                    _interpol.export_z_or_v_bin(fn_read, self._manager, name, type_hazard="z", type_extraction = type_extraction, param_danger = param_danger, threshold=threshold)
                
                else:
                    logging.info(_(f"Please, ensure your simulations are named with the return period, e.g sim_T4"))
            else:
                logging.info(_('No folder found / selected. Please try again...'))
        
        with wx.MessageDialog(self,
                                f"End of the process.",
                                "Information",
                                style=wx.OK | wx.ICON_INFORMATION) as dlg:
                dlg.ShowModal()
    
    def OnInterpolation(self,e):
        """Interpolates the last extracted time steps present in LAST_STEP_EXTRACTED using the fast marching
        interpolation routine, by creating a batch file
        while performing multiple checks on the required input files."""
        if self._but_loadgpu.GetValue(): #if simulations have been loaded :
            checked_names = self._check_listbox.GetCheckedStrings()
            iftest = False
            if not checked_names:
                logging.info(_("No items selected. Adding all paths."))
                checked_paths = list(self.file_paths.values())
            else:
                logging.info(_("Adding only the selected simulations."))
                checked_paths = [self.file_paths[name] for name in checked_names]
                
            if len(self.file_paths) == 0 :
                return logging.info(_("No files in EXTRACTED_LAST_STEP_WD. Please provide some or use the 'Load gpu simulation' button."))
        
        else : #if interpoalting based on existing files :
            checked_paths = None
            iftest = True
        
        _interpol = interpolating_raster()
        #interp_bool, renamed_files = _interpol.batch_creation_and_interpolation_fotran_holes(self._manager, checked_paths, False)
        interp_bool, renamed_files = _interpol.batch_creation_and_interpolation_python_eikonal(self._manager, checked_paths, iftest, True)

        if interp_bool:
            logging.info(_("Filling completed."))
            with wx.MessageDialog(self, f"Filling completed. Created files : {renamed_files}",
                        "Redirecting", wx.OK | wx.ICON_INFORMATION) as dlg:
                dlg.ShowModal()
            update_info_header(self.input_dx,self.input_nbxy,self.input_O,self._manager.IN_SA_INTERP)
        else :
            logging.error(_("Something went wrong for the interpolation."))
            
    def OnToggleAdmin(self, e):
        if self.toggle_state_Admin:
            self.toggle_state_Admin = False
            self._but_toggle_admin.SetBackgroundColour(wx.NullColour)
            self._steps_db.Hide()
            self._steps_vulnerability.Hide()
            self._steps_acceptability.Hide()
            return

        dlg = wx.TextEntryDialog(self, "Enter developer password:", "Authentication")
        if dlg.ShowModal() == wx.ID_OK:
            password = dlg.GetValue()
            if password == "LetMeIn#":
                self.toggle_state_Admin = True
                self._but_toggle_admin.SetBackgroundColour(wx.Colour(175, 175, 175))
                
                self._steps_db.Show()
                self._steps_vulnerability.Show()
                self._steps_acceptability.Show()
                
            else:
                wx.MessageBox("Wrong password.", "Error")
                self.toggle_state_Admin = False
                self._but_toggle_admin.SetBackgroundColour(wx.NullColour)
        dlg.Destroy()
        self.mapviewer.Refresh()
            
    def OnToggle(self,e):
        """Creates a toggle button to be activated if the scenarios vuln_ have to be taken into account."""
        self.toggle_state = False
        if self._but_toggle_scen.GetValue():
            logging.info(_("Activating the scenario button."))
            self._but_toggle_scen.SetBackgroundColour(wx.Colour(175, 175, 175))
            self._but_toggle_scen_state = True
            tif_files = [file for file in Path(self._manager.IN_CH_SA_SC).glob("*.tif") if file.name.startswith("vuln_")]
            if not tif_files:
                wx.MessageBox(
                    "The scenario button cannot be activated because there is no change in vulnerability 'vuln_' in CHANGE_VULNE. Please reload the simulations containing 'bath_' files via 'Load new hydraulic scenario' and edit it, or directly introduce your 'vuln_' files.",
                    "Information",
                    wx.OK | wx.ICON_INFORMATION
                    )
                logging.info(_("Desactivating the scenario button."))
                self._but_toggle_scen.SetValue(False)
                self._but_toggle_scen.SetBackgroundColour(wx.NullColour)
                self._but_toggle_scen_state = False
            else :
                self.toggle_state = True
        else:
            self._but_toggle_scen.SetBackgroundColour(wx.NullColour)
            self.toggle_state = False
            logging.info(_("Desactivating the scenario button."))

    def OnToggleResampling(self,e):
        """Creates a toggle button for the acceptability resampling to be activated."""
        self.toggle_resamp_state = False
        toggle = self._but_toggle_resamp
        if toggle.GetValue():
            self._but_toggle_resamp.SetBackgroundColour(wx.Colour(175, 175, 175))
            self.toggle_resamp_state = True
            logging.info(_("Resampling activated"))
            current_res = self._but_resampling.GetValue()
            resolution = self.input_dx.GetLabel()
            if resolution != '':
                values = resolution.strip("()").split(",")
                dx = float(values[0])
                #selection of size
                if current_res < dx:
                    wx.MessageBox(
                                "The resampling size cannot be inferior to the resolution. Please select another resampling size.",
                                "Attention",
                                wx.OK | wx.ICON_ERROR
                                )
                    self.toggle_resamp_state = False
                    self._but_toggle_resamp.SetValue(False)
                    self._but_toggle_resamp.SetBackgroundColour(wx.NullColour)
                    logging.info(_("Resampling disactivated because of a bad resampling size."))
                else :
                    logging.info(_(f"Allowed resampling value : {current_res}[m]."))
            else:
                self.toggle_resamp_state = False
                self._but_toggle_resamp.SetValue(False)
                self._but_toggle_resamp.SetBackgroundColour(wx.NullColour)
                logging.info(_("No simulations in INTERP_WD."))

        else:
            self.toggle_resamp_state = False
            self._but_toggle_resamp.SetValue(False)
            self._but_toggle_resamp.SetBackgroundColour(wx.NullColour)
            logging.info(_("Resampling disactivated"))
            
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
        
        if prefix == "vuln_":
            self._but_toggle_scen.Enable(True)
    
    def OnCheckMNTmodifs(self,e):
        """Checks if scenarios MNTmodifs_ exist in CHANGE_VULNE and test the type (float32)"""
        self.check_and_convert_rasters(self._manager, "MNTmodifs_", "Float32", np.float32, 99999.)
        return
    
    def OnCheckScenario(self,e):
        """Checks if scenarios vuln_ exist in CHANGE_VULNE and test the type (int8)"""
        message_supp = textwrap.dedent(""" To change the type and null value as needed, via WOLF HECE GUI: 
                                       1. Load the problematic file (File > Add array, and point toward the name indicated above). 
                                       2. Ctrl + double click on the name in the Arrays tree on the left. a window should open. 
                                       3. Click on "Select all nodes" and then go to Operators. If "=99999", replace with "127" and click "Apply math operator". 
                                       4. Go to "Miscellaneous", set "Null value = 127", and click on "Apply Null Value". 
                                       5. Change other values (there exists value outside interval of vulnerability [1,5], change them to int8)!
                                       6. (Optionnal) Go back to the main window, Ctrl + right click on the array to save it. 
                                       7. Right-click on the array > Duplicate > enter new name (with "vuln_...") and change the type to int8 before saving it. 
                                       8. DELETE THE PREVIOUS FILE, and retry the Vulnerability button. 
                                       """)
        self.check_and_convert_rasters(self._manager, "vuln_", "Byte", np.int8, 127, message_supp=message_supp)
        
    def OnVulnerability(self, e):
        """ Run the vulnerability """
        if self._manager is None:
            return
        path = [self._manager.OUT_VULN]
        steps = list(self._steps_vulnerability.GetCheckedStrings())
        steps = [int(cur.split('-')[1]) for cur in steps]
        resolution,unused,unused,unused,unused,unused =update_info_header(self.input_dx,self.input_nbxy,self.input_O,self._manager.IN_SA_INTERP)
        if resolution == '':
            wx.MessageBox(
                        f"There are no files in INTERP_WD lease, use first the buttons at the second line.",
                        "Attention",
                        wx.OK | wx.ICON_ERROR
                        )
        else :
            message_supp = "."
            if len(steps) == 0:
                steps = [1,10,11,2,3]
                if self.toggle_state:
                    message_supp = " with every steps AND scenario(s) vuln_ taken into account"
                    steps = [1,10,11,2,3,4]
                    if self._manager.OUT_VULN.exists:
                        logging.info(_("Attention - The manager ONLY computes Vulnerability_scenario, as Vulnerability_baseline already computed."))
                        steps=[4]
                    else :
                        logging.info(_("Attention - The manager computes also Vulnerability_baseline, as Vulnerability_scenario needs it as input."))
                    path = [self._manager.OUT_VULN_Stif]
                    dialog = wx.MessageDialog(None, f"Please modify the 'vuln_' files in INPUT\CHANGE_VULNE\... as desired. Default value set to one. ", "Confirmation", wx.YES_NO | wx.ICON_QUESTION)
                    dialog.SetYesNoLabels("Done, continue", "Not done, stop")
                    response = dialog.ShowModal()
                    if response == wx.ID_NO:
                        return

                logging.info(_("No steps selected. By default computations will be performed" + message_supp))
                check_fail = Vulnerability(str(self._manager.main_dir),
                            scenario=str(self._manager.scenario),
                            Study_area=str(self._manager.Study_area),
                            resolution=resolution,
                            steps=steps)
            else :
                if self.toggle_state:
                    steps.append(4)
                    message_supp = " with the selected steps AND scenario(s) vuln_ taken into account"
                    if self._manager.OUT_VULN.exists:
                        logging.info(_("Attention - The manager ONLY computes Vulnerability_scenario, as Vulnerability_baseline already computed."))
                        steps=[4]
                    else :
                        logging.info(_("Attention - The manager computes also Vulnerability_baseline, as Vulnerability_scenario needs it as input."))

                    path = [self._manager.OUT_VULN_Stif]
                    dialog = wx.MessageDialog(None, f"Please modify the 'vuln_' files in INPUT\CHANGE_VULNE\... as desired. Default value set to one. ", "Confirmation", wx.YES_NO | wx.ICON_QUESTION)
                    dialog.SetYesNoLabels("Done, continue", "Not done, stop")
                    response = dialog.ShowModal()
                    if response == wx.ID_NO:
                        return

                check_fail = Vulnerability(self._manager.main_dir,
                            scenario=self._manager.scenario,
                            Study_area=self._manager.Study_area,
                            resolution=resolution,
                            steps=steps)
                
        if steps_vulnerability.APPLY_SCENARIOSVULN_BUG in check_fail :
             wx.MessageBox(
                        "Vulnerability NOT computed for scenarios\n Some vuln_ files did not have the required type (int8). They were not taken into account (see renamed files ended by its type (e.g vuln_..._Float32.tif) in CHANGE_VULNE)",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                        )
        else:
            wx.MessageBox(
                        "Vulnerability computed" + message_supp,
                        "Information - Success",
                        wx.OK | wx.ICON_INFORMATION
                        )
            
        mapviewer_display(path, self.mapviewer)

    def OnAcceptability(self, e):
        """ Run the acceptability """
        if self._manager is None:
            return

        river_trace = self._manager.wich_river_trace(self.toggle_state)
        if self.toggle_state == True and not os.path.isfile(str(self._manager.OUT_VULN_Stif)) and not os.path.isfile(str(river_trace)) :
            wx.MessageBox("Necessary files are missing, please ensure the DataBase or Vulnerability or Updating riverbed steps were performed. ","Error",  wx.OK | wx.ICON_ERROR )
            return

        if self.toggle_state == False and not os.path.isfile(str(self._manager.OUT_VULN)) and not os.path.isfile(str(river_trace)) :
            wx.MessageBox("Necessary files are missing, please ensure the DataBase or Vulnerability or Updating riverbed steps were performed. ","Error",  wx.OK | wx.ICON_ERROR )
            return

        steps = list(self._steps_acceptability.GetCheckedStrings())
        steps = [int(cur.split('-')[1]) for cur in steps]
        message_supp = "."
        resampling=100
        path = [self._manager.OUT_ACCEPT]
        if len(steps) == 0:
            steps = [1,2,3,4]
            if self.toggle_state:
                steps = [1,2,3,4,5]
                message_supp = " AND scenario(s) vuln_ taken into account"
                path = [self._manager.OUT_ACCEPT_Stif]
                if self._manager.OUT_ACCEPT.exists:
                    steps = [x for x in steps if x != 4]
                    logging.info(_('Acceptability_baseline not computed because it already exists.'))
                    message_supp = " FOR scenario(s) vuln_ taken into account"

                if river_trace == self._manager.OUT_MASKED_RIVER : message_supp=message_supp +" WITH the _baseline riverbed trace."
                if river_trace == self._manager.OUT_MASKED_RIVER_S :message_supp+= " WITH the _scenarios riverbed trace."
            if self.toggle_resamp_state:
                steps.append(6)
                resampling = self._but_resampling.GetValue()
                resolution = self.input_dx.GetLabel()
                if resolution != '':
                    values = resolution.strip("()").split(",")
                    resolution = float(values[0])

                message_supp+= f" It has been created for the resolution {resolution}m and the resampling size {resampling}m."

            logging.info(_("No steps selected. By default every steps will be performed."))
            done = Acceptability(self._manager.main_dir,
                        scenario=self._manager.scenario,
                        Study_area=self._manager.Study_area,
                        resample_size=resampling,
                        steps=steps)
            if len(done) == 0:
                wx.MessageBox(
                        "No acceptability computed with the selected steps" + message_supp,
                        "Information",
                        wx.OK | wx.ICON_INFORMATION
                        )
            else :
                
                wx.MessageBox(
                            "Acceptability computed with the selected steps" + message_supp,
                            "Information",
                            wx.OK | wx.ICON_INFORMATION
                            )
                mapviewer_display(path, self.mapviewer)
        else :
            if self.toggle_state:
                steps.append(5)
                message_supp = " AND scenario(s) vuln_ taken into account"
                if self._manager.OUT_ACCEPT.exists:
                    steps = [x for x in steps if x != 4]
                    logging.info(_('Acceptability_baseline not computed because it already exists.'))
                    message_supp = "FOR scenario(s) (vuln_taken into account)"
                path = [self._manager.OUT_ACCEPT_Stif]
                river_trace = self._manager.wich_river_trace(self.toggle_state)
                if river_trace == self._manager.OUT_MASKED_RIVER : message_supp =message_supp + " WITH the _baseline riverbed trace."
                if river_trace == self._manager.OUT_MASKED_RIVER_S : message_supp =message_supp + " WITH the _scenarios riverbed trace."
            if self.toggle_resamp_state:
                resampling = self._but_resampling.GetValue()
                steps.append(6)

            done = Acceptability(self._manager.main_dir,
                        scenario=self._manager.scenario,
                        Study_area=self._manager.Study_area,
                        resample_size=resampling,
                        steps=steps)

            if len(done) == 0:
                wx.MessageBox(
                        "No acceptability computed with the selected steps" + message_supp,
                        "Information",
                        wx.OK | wx.ICON_INFORMATION
                        )
            else :
                
                wx.MessageBox(
                            "Acceptability computed with the selected steps" + message_supp,
                            "Information",
                            wx.OK | wx.ICON_INFORMATION
                            )
                mapviewer_display(path, self.mapviewer)