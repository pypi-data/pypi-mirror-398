"""
Author: HECE - University of Liege, Pierre Archambeau, Utashi Ciraane Docile
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

"""
This module contains the scripts that are needed to
create, execute and soon interact with a Wolf-1D model.

Basically, called in Pydraw (the main wolf - interface),
this module will create a new window consisting of different pages
that become visible throughout the modelling process
(creation, execution or interaction) and according to the user's need.
"""

# --- Librairies ---
#___________________
import copy
import enum
import logging
import math
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os, warnings
import pandas as pd
import shutil
import subprocess
import sys
import tempfile
import time
import typing
import wx
import wx.grid as gridlib
import wx.propgrid as pg


from decimal import Decimal
from IPython.display import  HTML
from matplotlib.ticker import MultipleLocator
from matplotlib import animation ,rcParams
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from shapely.ops import substring, split, LineString, Point
from typing import Literal,Union
from tqdm import tqdm
from subprocess import Popen, PIPE
from wx.grid import Grid
from wx.dataview import *


from .GraphProfile import PlotCSAll
from .Model1D import Creator_1D, Wolfresults_1D, MultipleWolfresults_1D
from .PyCrosssections import crosssections, profile, postype, INTERSEC
from .PyHydrographs import Hydrograph
from .pylogging import create_wxlogwindow
from .PyParams import Wolf_Param
from .PyTranslate import _
from .PyVertexvectors import Zones, zone, vector, wolfvertex, CpGrid
from .wolf_array import WolfArray


# --- objects ---
# _______________
class Constants(enum.Enum):
    """
    Constants used by this module.
    """
    # --- Values ---
    # ______________
    BANK_WIDTH = 1
    CENTERED_TEXT = wx.TE_CENTRE|wx.TE_PROCESS_ENTER|wx.TE_RICH
    DPI = 60
    FRAMESIZE = (460,560)
    GENERAL_FONTSIZE = 'small'
    GRAVITATION = 9.81
    GRIDSIZE = (280,540)
    NULL = -99999
    NUMBER_OF_PAGES = 4
    POLYGONE_NUMBER = 1
    PRECISION = ':#.20F'
    SEPARATOR = '\t'
    # --- IN GUI 1D ---
    # _______________

    BATHYMETRY = 'Bathymetry'
    BED_AND_BANKS = 'bank and bed'
    CROSS_SECTIONS = 'cross sections'
    FRICTIONS = 'frictions'
    GUI_ID_BATHYMETRY = _('1D - BATHYMETRY')
    GUI_ID_BED_AND_BANKS = _('1D - BED AND BANKS')
    GUI_ID_CROSS_SECTION = _('1D - CROSS SECTION')
    GUI_ID_FRICTION = _('1D - FRICTION')
    GUI_ID_LANDMARK = _('1D - LANDMARKS')
    LANDMARK ='Landmarks'
    NAME_PREFIX =_('1D_')

    # --- IN MAPVIEWER (.Pydraw) ---
    # ___________
    MAPVIEWER_SELECT_NEAREST_PROFILE = 'Select nearest profile' # Deprecated
    MAPVIEWER_SET_1D_PROFILE = 'Set 1D profile'


    # PRECISION = ':#.20F' FIXME

class Titles(enum.Enum):
    """
    Titles (string names) of buttons, menus, etc,
    used by this module and seen in the interface.

    @ the sign _() enclosing strings is required for translation
    purposes (see .pytranslate).
    """
    ADD = _('Add ...')
    ADD_BATHYMETRY = _('Add bathymetry')
    ADD_BED_AND_BANKS = _('Add bed and banks')
    ADD_CROSS_SECTIONS = _('Add cross sections')
    ADD_FRICTIONS = _('Add frictions')
    ADD_LANDMARKS = _('Add landmarks')
    AVAILABLE_DATA = _('Available data')
    BATHYMETRIC_DATA = _('Bathymetric array')
    BC_CONDITIONS = _('Boundary conditions')
    BC_DISCHARGE_3 = _('Discharge')
    BC_DOWNSTREAM = _("Downstream")
    BC_FREE_5 =_('Free')
    BC_FROUDE_4 = _('Froude')
    BC_IMPERVIOUS_99 =_('Impervious')
    BC_JUNCTION_100 = _('Junction')
    BC_MOBILE_DAM_127 = _('Mobile dam')
    BC_UPSTREAM =_("Upstream")
    BC_VALUE = _('Value')
    BC_WATER_DEPTH_1 = _('Water depth')
    BC_WATER_LEVEL_2 = _('Water level')
    BED_BANKS = _('Bed and banks')
    BETWEEN_PROFILES = _("Between profiles")
    BRANCH = _('')
    COMPUTATION_DATA = _('Computation')
    COMPUTATION_MODE = _('Computation mode')
    CROSS_SECTIONS_CATEGORY = _('Cross sections')
    CROSS_SECTIONS_DATA = _('Cross sections')
    EPSILON = _('Epsilon infiltrations')
    EVOLUTIVE = _('Evolutive domain')
    EXECUTABLE = _("Executable")
    FIXED = _('Fixed')
    FORCE_VALUE =_("Force a value")
    FRICTION_DATA =_("Friction array")
    GUI_GRID_BOUNDARY_CONDITIONS = _("Condition")
    HYDROGRAPH_PREPROCESS = _('Infiltrations')
    INFILTRATIONS = _('Infiltrations')
    LANDMARK_DATA ='Landmarks'
    MAIN = 'Main'
    MAXIMUM = _('Maximum')
    MEAN =_('Mean')
    MEDIAN =_('Median')
    MESSAGE_AGGLOMERATION_FRICTIONS = _("If enabled: Agglomeration formula of 2D frictions.")
    MESSAGE_BUTTON_PARAMETERS = _('Create the simulation parameters if the executable is provided.')
    MESSAGE_BUTTON_SAVE = _('Create the simulation files and\n run the model if the option was selected.')
    MESSAGE_COMPUTATION_MODE =_("How the model should be computed.")
    MESSAGE_DATA = _('To upload -> Left double click | To delete -> Uncheck the Box.')
    MESSAGE_DISCHARGE = _('Initial discharge.')
    MESSAGE_EPSILON =_('Time delta between 2 infiltration values (only for stepwise).')
    MESSAGE_EXECUTABLE = ("Left double click -> To provide the wolf executable.")
    MESSAGE_EXTREMITIES = _("Height of the vertical wall on each extremity of every cross sections.")
    MESSAGE_FILE_FORMAT = _('Format of the initial conditions file: aini - wetted sections, hini: w. depth, zini: w. level')
    MESSAGE_FORCED_VALUE = _("If enabled: Friction value to be forced on all cells.")
    MESSAGE_HYDROGRAPH_PREPROCESS = _('Continuous -> keep the infiltration values as they are | Stepwise -> create steps.')
    MESSAGE_MODE_FRICTIONS = ("The frictions values are forced or collected from the 2D array of frictions.")
    MESSAGE_RUN = _("Select whether the model should be run or not.")
    MESSAGE_STEADINESS = _("Select the flow regime (pattern).")
    MESSAGE_WATER_DEPTH = _('Initial water depth')
    MINIMUM =_('Mininum')
    NO_PRECOMPUTATION = _('No precomputation')
    NO_PREPROCESSING = _('No preprocessing')
    PARAMETERS = _("Simulation parameters")
    PRECOMPUTATION = _('Precomputation')
    PREPROCESS_OPTIONS = _('Preprocessing options')
    RAISE_EXTREMITIES = _('Extremity elevations (m)')
    RUN_SIMULATION = _("Run simulation")
    SAVE = _("Save | Run simulation")
    STEADINESS = 'Steadiness'
    STEADY = _('Steady')
    STEPWISE = _('Stepwise using epsilon')
    UNDER_PROFILES = _("Only under Profiles")
    VERBOSITY = _('Verbosities')
    WOLF_PARAM_WINDOW = _("Wolf1D - Parameters")
    WOLFCLI = "Wolfcli"
    WOLFCLID = "Wolfclid"
    WX = _('Wolf1D')

class Colors(enum.Enum):
    """
    Color names and parameters
    used in this module.
    """
    BED = 'black'
    LEFT_BANK = 'red'
    MATPLOTLIB_CYCLE = rcParams["axes.prop_cycle"]()
    PROPOSED = wx.BLUE
    RIGHT_BANK = 'blue'
    TQDM = 'cyan'
    WX = 'white'

class fileExtensions(enum.Enum):
    """
    File extensions (end of file name after the dot)
    used in this module.
    """
    AINI = '.aini'
    BANKS = '.banks'
    BREADTH = '.breadth'
    CL = '.cl'          # Boundary conditions
    CVG = '.cvg'
    DEPTH ='.depth'
    DIAM = '.diam'
    GTV = '.gtv'
    HELP = '.help'
    HINI = '.hini'
    INF = '.inf'
    INFIL ='.infil'
    LENGHTSVECZ = '_lengths.vecz'
    LENGTHS = '.lengths'
    PARAMETERS = '.param'
    PTV = '.ptv'
    QINI ='.qini'
    ROUGHNESS = '.rough'
    TOP = '.top'
    VECTOR2D = '.vec'
    VECTOR3D = '.vecz'
    WIDTH = ''
    ZINI = '.zini'

class Page(wx.Panel):
    """
    A wx.page format used by the different tabs.

    @ Could be better customized though.
    It means don't refrain your creativity.
    """
    def __init__(self, parent):
        super().__init__(parent= parent)

class GuiNotebook1D( wx.Frame):
    """Notebook frame (GUI in wx) that allow
    a user to interact with a wolf-1D model.

    Interaction means:
    (creation, execution and soon results visualization)
    of wolf-1D models.
    """

    array: WolfArray
    cross_section : crosssections
    zones: Zones
    page_1: Page
    def __init__(self,
                 page_names = [Titles.MAIN.value,
                               Titles.INFILTRATIONS.value,
                               Titles.BC_CONDITIONS.value,
                               Titles.VERBOSITY.value,
                               Titles.PARAMETERS.value],
                               style = wx.DEFAULT_FRAME_STYLE| wx.STAY_ON_TOP,
                               mapviewer = None):
        """Constructor method.

        :param page_names: Names of the notebook pages,
          defaults to [Titles.MAIN.value, Titles.INFILTRATIONS.value,
          Titles.BC_CONDITIONS.value, Titles.VERBOSITY.value,
          Titles.PARAMETERS.value]
        :type page_names: list, optional
        :param style: wx style, defaults to wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP
        :type style: `str`, optional
        :param mapviewer: The interface in which the data are
        visualized and the notebook is triggered (called), defaults to None
        :type mapviewer: :class: `pydraw`, optional

        .. todo:: Implement a page for visualization,
        and exploitation of results.
        """
        super().__init__(parent = None,
                       id = wx.ID_ANY,
                          title = Titles.WX.value,
                          size= Constants.FRAMESIZE.value,
                          style = style)

        # --- PROPERTIES ---
        # ___________________
        # Module used for creating a 1D model.
        self.creator1D = Creator_1D()
        # Pydraw (called by an indirection) FIXME not very clean but best solution currently available.
        self.mapviewer = mapviewer
        # Dictionnary pointing to the data uploaded by this module in the mapviewer. The keys are the data type.
        self.data = {}
        # The cells_name from sorted profile names.
        self.cells_name = []
        self.cells_related_page_names = []
        self.param_exists = False
        self.executable_path = None
        self.executable_selected = None
        self.simulation_name = None
        self.simulation_directory = None
        self.active_profile : profile
        self.active_profile = None
        self.selected_name = None

        # --- BARS ---
        # ____________
        # # Menu Bar
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
        # # Status bar
        self.statusBar = wx.StatusBar(self, name ='status_bar')
        self.SetStatusBar(self.statusBar)
        # FIXME is it useful or should be discussed later.
        self.toolbar = wx.ToolBar(self,  name='Tool_bar')
        self.toolbar.SetToolBitmapSize(size =(0, 0))
        self.SetToolBar(self.toolbar)

        # --- MENU ---
        # ____________
        menu_add = wx.Menu()
        menu_add_cross_section = menu_add.Append(wx.ID_FILE4, Titles.ADD_CROSS_SECTIONS.value,
                                        _('Add a cross section file (.vecz or other formats)'))
        menu_add_bed_and_banks= menu_add.Append(wx.ID_FILE1, Titles.ADD_BED_AND_BANKS.value,
                                        _('Add the bed and bank file (.vec or .vecz formats)'))
        menu_add_bathymetry = menu_add.Append(wx.ID_FILE2, Titles.ADD_BATHYMETRY.value,
                                        _('Add the bathymetry array (.top or .bin formats)'))
        menu_add_friction= menu_add.Append(wx.ID_FILE3, Titles.ADD_FRICTIONS.value,
                                    _('Add friction array (.top or .bin formats)'))
        menu_add_land_mark= menu_add.Append(wx.ID_FILE5, Titles.ADD_LANDMARKS.value,
                                    _('Add land marks (.vec or .vecz formats)'))
        self.menubar.Append(menu_add,Titles.ADD.value)

        ## Other options
        menu_options = wx.Menu()
        # save_option = menu_options.Append(wx.ID_ANY, _('Save as'), _('Create the simulation file'))
        quit_option = menu_options.Append(wx.ID_EXIT, _('Quit'), _('Close safely this window.'))
        self.menubar.Append(menu_options, _('Options'))

        # --- NOTEBOOK ---
        # ________________

        # Setting up the panels
        panel = wx.Panel(self)

        # The Notebook
        self.notebook  = wx.Notebook(panel,style=wx.NB_TOP)
        # The notebook pages (tabs)
        self.notebook_pages = {}
        for name in page_names:
            if name == Titles.MAIN.value:
                page = Page(self.notebook)
                self.notebook.AddPage(page, name)
                self.notebook_pages[name] = page

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.notebook,1, wx.EXPAND)
        panel.SetSizer(sizer)

        # Main page
        self.page_1 = self.notebook_pages[Titles.MAIN.value]
        sizer_page_1 = wx.BoxSizer(wx.VERTICAL)

        # ----------------
        #  PREPROCESSING
        # ---------------
        sizer_inputs = wx.BoxSizer(wx.VERTICAL)
        self.grid_inputs = pg.PropertyGridManager(parent = self.page_1,
                                                 style = pg.PG_BOLD_MODIFIED|
                                                 pg.PG_SPLITTER_AUTO_CENTER|
                                                 pg.PGMAN_DEFAULT_STYLE
                                                 )

        # Data
        self.available_data = pg.PropertyCategory(Titles.AVAILABLE_DATA.value)
        self.grid_inputs.Append(self.available_data)
        self.data_cross_sections = pg.BoolProperty(label= Titles.CROSS_SECTIONS_DATA.value,
                                                   name = 'data_cross_sections')
        self.data_river_banks = pg.BoolProperty(label= Titles.BED_BANKS.value,
                                                name = 'bed_and_banks')
        self.data_bathymetry = pg.BoolProperty(label= Titles.BATHYMETRIC_DATA.value,
                                                name = 'bathymetric_data')
        self.data_frictions = pg.BoolProperty(label= Titles.FRICTION_DATA.value,
                                                name = 'friction_data')
        self.data_landmark = pg.BoolProperty(label= Titles.LANDMARK_DATA.value,
                                                name = 'land_mark_data')


        # Appending
        self.grid_inputs.Append(self.data_cross_sections)
        self.grid_inputs.Append(self.data_river_banks)
        self.grid_inputs.Append(self.data_landmark)
        self.grid_inputs.Append(self.data_bathymetry)
        self.grid_inputs.Append(self.data_frictions)

        # Cross sections
        self.grid_inputs.Append(pg.PropertyCategory(Titles.CROSS_SECTIONS_CATEGORY.value))
        self.extrapolation_of_extremities = pg.FloatProperty(Titles.RAISE_EXTREMITIES.value,
                                                              name= 'extrapolation_extremities',
                                                              value= 100.)

        self.grid_inputs.Append(self.extrapolation_of_extremities)

        # # #  Frictions
        # Group label
        self.friction_group = pg.PropertyCategory(_('Frictions'))
        self.grid_inputs.Append(self.friction_group)

        # selection mode
        # FIXME Titles.BETWEEN_PROFILES.value not available,
        # Due to manual modification of cross sections such as, weirs, bridges discretizations, ...
        self.selection_friction_mode = pg.EnumProperty(label = 'Selection mode',
                                                       name = 'selection_friction',
                                                       labels =  [Titles.FORCE_VALUE.value,
                                                                  Titles.UNDER_PROFILES.value,
                                                                  ],
                                                        values = [1,2],
                                                        value = 1)

        # Agglomeration mode
        self.agglomeration_friction_mode = pg.EnumProperty(label = 'Agglomeration mode from array',
                                                       name = 'agglomeration_friction',
                                                       labels =  [Titles.MEAN.value,
                                                                  Titles.MEDIAN.value,
                                                                  Titles.MAXIMUM.value,
                                                                  Titles.MINIMUM.value],
                                                        values = [1,2,3,4],
                                                        value = 0)

        # Forced value
        self.forced_value = pg.FloatProperty(label= 'Forced value',
                                             name= 'forced_value',
                                             value= 0.04)
        self.grid_inputs.Append(self.selection_friction_mode)
        self.grid_inputs.Append(self.forced_value)
        self.grid_inputs.Append(self.agglomeration_friction_mode)

        # Initial conditions
        self.grid_inputs.Append(pg.PropertyCategory(_('Initial conditions')))
        self.type_ic_file = pg.EnumProperty(label ='File format',
                                            name = 'file_format_ic',
                                            labels= [fileExtensions.AINI.value,
                                                     fileExtensions.HINI.value,
                                                     fileExtensions.ZINI.value
                                                     ],
                                            values = [1,2,3],
                                            value = 1)
        self.water_depth = pg.FloatProperty(label= 'Water depth (m)',
                                            name= 'water_depth',
                                            value = 1.)

        # FIXME Not yet used (the method is still ackward)
        # self.water_level = pg.FloatProperty(label= 'Water level (m)',
        #                                        name = 'water_level')
        self.discharge = pg.FloatProperty(label= 'Discharge',
                                          name = 'discharge',
                                          value= 0.)

        # Appending Initial conditions
        self.grid_inputs.Append(self.type_ic_file)
        self.grid_inputs.Append(self.water_depth)

        # self.grid_inputs.Append( self.water_level)
        self.grid_inputs.Append(self.discharge)

        #  Pre-process
        self.grid_inputs.Append(pg.PropertyCategory(Titles.PREPROCESS_OPTIONS.value))
        self.hydrographs_preprocess = pg.EnumProperty(label = Titles.HYDROGRAPH_PREPROCESS.value,
                                                    name = 'hydrograph preprocess',
                                                    labels = [Titles.NO_PREPROCESSING.value,
                                                                 Titles.STEPWISE.value],
                                                    values = [1,2],
                                                    value = 1)
        self.epsilon = pg.FloatProperty(label= Titles.EPSILON.value,
                                             name= 'epsilon',
                                             value= 0.01)
        self.grid_inputs.Append(self.hydrographs_preprocess)
        self.grid_inputs.Append(self.epsilon)

        # Computation mode
        self.grid_inputs.Append(pg.PropertyCategory(Titles.COMPUTATION_DATA.value))
        self.steadiness_mode =pg.EnumProperty(label = Titles.STEADINESS.value,
                                              name = 'steadiness',
                                              labels = [Titles.NO_PRECOMPUTATION.value,
                                                        Titles.PRECOMPUTATION.value,
                                                        Titles.STEADY.value],
                                              values = [1,2,3],
                                              value = 2)
        self.computation_mode = pg.EnumProperty(label = Titles.COMPUTATION_MODE.value,
                                                name ='computation mode',
                                                labels = [Titles.EVOLUTIVE.value,
                                                          Titles.FIXED.value],
                                                values = [1,2],
                                                value = 1)
        self.executable = pg.EnumProperty(label = Titles.EXECUTABLE.value,
                                          name = "executable",
                                          labels=[Titles.WOLFCLI.value,
                                                  Titles.WOLFCLID.value],
                                          values =[1,2],
                                          value = 0)
        self.run_simulation = pg.BoolProperty(label= Titles.RUN_SIMULATION.value,
                                              name = "run_simulation",
                                              value= True)

        self.grid_inputs.Append(self.steadiness_mode)
        self.grid_inputs.Append(self.computation_mode)
        self.grid_inputs.Append(self.executable)
        self.grid_inputs.Append(self.run_simulation)

        # Buttons
        self.button_parameter = wx.Button(parent = self.page_1,
                                          id = wx.ID_ANY,
                                          label = Titles.PARAMETERS.value,
                                          name = 'parameters')
        self.button_save = wx.Button(parent = self.page_1,
                                          id = wx.ID_ANY,
                                          label = Titles.SAVE.value,
                                          name = 'save')

        # Adding
        sizer_inputs.Add(self.grid_inputs,1, wx.EXPAND)
        sizer_inputs.Add(self.button_parameter,0, wx.EXPAND)
        sizer_inputs.Add(self.button_save, 0, wx.EXPAND)

        # Binding
        self.button_parameter.Bind(wx.EVT_BUTTON, self.click_on_parameters)
        self.button_save.Bind(wx.EVT_BUTTON, self.button_save_clicked)

        # # Organizing  sizers
        sizer_page_1.Add(sizer_inputs,-1, wx.EXPAND)

        # setting the sizer
        self.page_1.SetSizer(sizer_page_1)

        # Setting attributes
        self.data_cross_sections.SetAttribute(pg.PG_BOOL_USE_CHECKBOX, True)
        self.data_river_banks.SetAttribute(pg.PG_BOOL_USE_CHECKBOX, True)
        self.data_bathymetry.SetAttribute(pg.PG_BOOL_USE_CHECKBOX, True)
        self.data_frictions.SetAttribute(pg.PG_BOOL_USE_CHECKBOX, True)
        self.data_landmark.SetAttribute(pg.PG_BOOL_USE_CHECKBOX, True)
        self.run_simulation.SetAttribute(pg.PG_BOOL_USE_CHECKBOX, True)

        # Freezing some commands
        self.freeze_commands()

        # Binding Events
        self.grid_inputs.Bind(pg.EVT_PG_DOUBLE_CLICK, self.double_click_methods)
        self.grid_inputs.Bind(pg.EVT_PG_CHANGED, self.changing_methods)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.tab_changed)

        # self.Bind(TreeListEvent, self.selection_methods)

        # Adding menus
        self.Bind(wx.EVT_MENU, self.add_crossections_from_menu, menu_add_cross_section)
        self.Bind(wx.EVT_MENU, self.add_bed_and_banks_from_menu, menu_add_bed_and_banks)
        self.Bind(wx.EVT_MENU, self.add_bathymetry_from_menu, menu_add_bathymetry)
        self.Bind(wx.EVT_MENU, self.add_friction_from_menu, menu_add_friction)
        self.Bind(wx.EVT_MENU, self.add_landmark_from_menu, menu_add_land_mark)
        self.Bind(wx.EVT_MENU, self.quit, quit_option)
        self.Bind(wx.EVT_CLOSE, self.onclose)

        # --- Tooltip ---
        #________________
        # Data
        self.data_cross_sections.SetHelpString(Titles.MESSAGE_DATA.value)
        self.data_river_banks.SetHelpString(Titles.MESSAGE_DATA.value)
        self.data_bathymetry.SetHelpString(Titles.MESSAGE_DATA.value)
        self.data_frictions.SetHelpString(Titles.MESSAGE_DATA.value)
        self.data_landmark.SetHelpString(Titles.MESSAGE_DATA.value)
        # Cross sections
        self.extrapolation_of_extremities.SetHelpString(Titles.MESSAGE_EXTREMITIES.value)
        # Frictions
        self.selection_friction_mode.SetHelpString(Titles.MESSAGE_MODE_FRICTIONS.value)
        self.forced_value.SetHelpString(Titles.MESSAGE_FORCED_VALUE.value)
        self.agglomeration_friction_mode.SetHelpString(Titles.MESSAGE_AGGLOMERATION_FRICTIONS.value)
        # Initial conditions
        self.type_ic_file.SetHelpString(Titles.MESSAGE_FILE_FORMAT.value)
        self.water_depth.SetHelpString(Titles.MESSAGE_WATER_DEPTH.value)
        self.discharge.SetHelpString(Titles.MESSAGE_DISCHARGE.value)
        # Preprocess
        self.hydrographs_preprocess.SetHelpString(Titles.MESSAGE_HYDROGRAPH_PREPROCESS.value)
        self.epsilon.SetHelpString(Titles.MESSAGE_EPSILON.value)
        # Computation
        self.steadiness_mode.SetHelpString(Titles.MESSAGE_STEADINESS.value)
        self.computation_mode.SetHelpString(Titles.MESSAGE_COMPUTATION_MODE.value)
        self.executable.SetHelpString(Titles.MESSAGE_EXECUTABLE.value)
        self.run_simulation.SetHelpString(Titles.MESSAGE_RUN.value)
        # Buttons
        self.button_parameter.SetToolTip(Titles.MESSAGE_BUTTON_PARAMETERS.value)
        self.button_save.SetToolTip(Titles.MESSAGE_BUTTON_SAVE.value)
        self.Layout()
        self.Show()

    # ---  NOTEBOOK METHODS ---
    #__________________________

    def update_cells_name(self):
        """Update the list of cells name.

        .. note::
            It's basically the list of all
            cross sections minus the last one.
        """
        if Constants.CROSS_SECTIONS.value in self.data and Constants.BED_AND_BANKS.value in self.data:
            self.cells_name = self.creator1D.get_sorted_cells_name([self.data[Constants.CROSS_SECTIONS.value]],
                                                                    self.data[Constants.BED_AND_BANKS.value],
                                                                    id= 1
                                                                    )
            self.update_infiltrations_page()
            self.update_boundary_conditions_page()
            self.unfreeze_crossections_related()
            logging.info('Cross sections sorted.')
            # print(self.cells_name)

    def add_new_page(self,
                     page: wx.Panel,
                     name:str,
                     cells_related_page = True):
        """Add a new page to the notebook.

        :param page: The page panel
        :type page: wx.Panel
        :param name: page name to be  used across the whole notebook
        :type name: str
        :param cells_related_page: The page is visible only when
        cross sections are sorted, defaults to True
        :type cells_related_page: bool, optional
        """
        self.notebook.AddPage(page, name)
        self.notebook_pages[name] = page
        if cells_related_page:
            self.cells_related_page_names.append(name)
        page.Refresh()

    def update_infiltrations_page(self):
        """Create or recreate the infiltration page (tab).
        """
        infiltration_page = MultigridPage(self.notebook)
        infiltration_page.tree_profiles(self.cells_name)
        self.add_new_page(infiltration_page, Titles.INFILTRATIONS.value)

    def update_boundary_conditions_page(self):
        """Create or recreate the page of boundary conditions.
        """
        page_boundary_condtions = Boundary_condition_Page(self.notebook)
        page_boundary_condtions.tree_profiles(self.cells_name)
        self.add_new_page(page_boundary_condtions, Titles.BC_CONDITIONS.value)

    def find_page_number(self, name:str) -> int:
        """Return the page index base on its name.

        :param name: page name used across the whole notebook.
        :type name: str
        :return: the page index
        :rtype: int
        """
        assert name in self.notebook_pages,\
                "Cannot find a fictive page."

        for i in range(self.notebook.GetPageCount()):
            if self.notebook.GetPageText(i) == name:
                break
        return i

    def delete_page(self, name:str):
        """Delete a page based on its name.

        :param name: page name used across the whole notebook.
        :type name: str
        """
        self.notebook.DeletePage(self.find_page_number(name))
        self.notebook_pages.pop(name)
        self.Refresh()

    def delete_cells_related_pages(self):
        """Delete all pages related to  the cells name.
        """
        if self.notebook.GetPageCount() > 1:
            for name in self.cells_related_page_names:
                    self.delete_page(name)
            self.reset_cell_names()
            self.reset_cells_related_page_names()

    def reset_cells_related_page_names(self):
        """Empty the list of pages related to the cells name.
        """
        self.cells_related_page_names.clear()

    def reset_cell_names(self):
        """Delete the  name of cells from the program.
        """
        self.cells_name.clear()

    # --- MAPVIEWER METHODS ----
    #___________________________

    def enable_action_select_profile_in_mapviewer(self):
        """Enable the selection, highlight,  and plot
        of the nearest profile of  the user's click
        (right down) in the mapviewer interface (2D).
        """
        self.mapviewer.action = Constants.MAPVIEWER_SELECT_NEAREST_PROFILE.value

    def enable_action_set_1D_profile_in_mapviewer(self):
        """
        Enable the selection, highlight, and plot
        of a profile in the mapviewer interface if
        the profile was selected in the notebook.
        """
        self.mapviewer.action = Constants.MAPVIEWER_SET_1D_PROFILE.value

    def disable_action_in_mapviewer(self):
        """Disable every action activated
        in the mapviewer interface (2D).
        """
        self.mapviewer.action = None

    def setting_active_profile_in_mapviewer(self):
        """Set the active profile in
        the notebook as the active
        profile in the mapviewer.
        """
        if self.active_profile != None:
            self.mapviewer.set_active_profile(self.active_profile)


    # --- MOUSE METHODS ---
    # _____________________

    def double_click_methods(self, event:pg.EVT_PG_DOUBLE_CLICK):
        """Select the appropriated method
        based on its id
        if the double click event is called
        in the property grid.

        :param event: `wx.Event`
        :type event: pg.EVT_PG_DOUBLE_CLICK
        """
        id = event.PropertyName
        if id == 'data_cross_sections':
            self.add_crossection()
        elif id == 'bed_and_banks':
            self.add_bed_and_banks()
        elif id == 'bathymetric_data':
            self.add_bathymetry()
        elif id == 'friction_data':
            self.add_friction()
        elif id == 'land_mark_data':
            self.add_landmark()
        elif id == 'forced_value':
            self.enable_forced_value()
        elif id == 'agglomeration_friction':
            self.enable_agglomeration_mode()
        elif id == 'discharge':
            self.enable_initial_discharge()
        elif id == "executable":
            self.add_executable()

    def changing_methods(self, event: pg.EVT_PG_CHANGED):
        """Select the appropriated method
        based on its id if a property has
        changed event.

        :param event: `wx.Event`
        :type event: pg.EVT_PG_CHANGED
        """

        id = event.PropertyName
        if id == 'data_cross_sections':
            self.delete_crossection()
        elif id == 'bed_and_banks':
            self.delete_bed_and_banks()
        elif id == 'bathymetric_data':
            self.delete_bathymetry()
        elif id == 'friction_data':
            self.delete_friction()
        elif id == 'land_mark_data':
            self.delete_land_mark()
        elif id == "executable":
            self.lock_executable()
        elif id == 'selection_friction':
            self.selection_friction_mode_changed()
        elif id == 'hydrograph preprocess':
            self.infiltration_preprocess_changed()

    def tab_changed(self, event):
        """Bind the right method
        for locating the selected cell (profile)
        when the page(tab) has changed.

        The selection is based on the cell's name
        displayed on the tree list.

        :param event: `wx.Event`
        :type event: `wx.EVT_NOTEBOOK_PAGE_CHANGED`
        """

        page_hydrographs: MultigridPage
        page_boundary_conditions : Boundary_condition_Page
        id  = self.notebook.GetSelection()
        page_hydrographs = self.get_page_hydrographs()
        page_boundary_conditions = self.get_page_boundary_conditions()

        if  self.notebook.GetPage(id) == page_hydrographs:
            logging.info("Infiltration page")
            try:
                page_hydrographs.Unbind(EVT_TREELIST_SELECTION_CHANGED, self.element_selected_on_bounds_conditions_tree)

            except:
                pass
            page_hydrographs.Bind(EVT_TREELIST_SELECTION_CHANGED, self.element_selected_on_infitltration_tree)

        elif  self.notebook.GetPage(id) == page_boundary_conditions:
            logging.info("Boundary conditions page")
            try:
                page_hydrographs.Unbind(EVT_TREELIST_SELECTION_CHANGED, self.element_selected_on_infitltration_tree)
            except:
                pass
            page_boundary_conditions.Bind(EVT_TREELIST_SELECTION_CHANGED, self.element_selected_on_bounds_conditions_tree)

    def element_selected_on_infitltration_tree(self, event:TreeListEvent):
        """Bind the event tree list changed
        each time the selected cell is changed on
        the infiltration page.

        :param event: `EVT_TREELIST_SELECTION_CHANGED`
        :type event: TreeListEvent
        .. todo::FIXME Not very clean as method.
        """
        page_hydrographs: MultigridPage
        page_hydrographs = self.get_page_hydrographs()
        self.selected_name = page_hydrographs.on_select_item(event)
        self.set_active_profile(self.selected_name)

    def element_selected_on_bounds_conditions_tree(self, event:TreeListEvent):
        """Bind the event tree list changed
        each time the selected cell is changed on
        the boundary condition page.

        :param event: `EVT_TREELIST_SELECTION_CHANGED`
        :type event: TreeListEvent
        .. todo:: FIXME Not very clean as method.
        """

        page_boundary_conditions : Boundary_condition_Page
        page_boundary_conditions = self.get_page_boundary_conditions()
        self.selected_name = page_boundary_conditions.oncheckitem(event)
        self.set_active_profile(self.selected_name)

    def get_page_hydrographs(self):
        """Return the infiltration page
        (page of hydrographs).

        :return: infiltration page
        :rtype: MultigridPage
        """
        return self.notebook.GetPage(self.find_page_number(Titles.INFILTRATIONS.value))

    def get_page_boundary_conditions(self):
        """Return the page of boundary conditions.

        :return: page of boundary conditions
        :rtype: Boundary_condition_Page
        """
        return self.notebook.GetPage(self.find_page_number(Titles.BC_CONDITIONS.value))

    def set_active_profile(self, profile_name: str):
        """In case the profile_name is in the list of sorted cross sections,
        that profile is set as the active profile in both the notebook and
        the mapviewer.
        Simultaneously, the action `Set 1D profile` in mapviewer is enabled.

        :param profile_name: name of the chosen profile.
        :type profile_name: str
        """
        cross_sections : crosssections
        if profile_name != None and profile_name in self.cells_name:
            cross_sections = self.data[Constants.CROSS_SECTIONS.value]
            self.active_profile = cross_sections.sorted['sorted']['sorted'][int(profile_name)-1]
            self.mapviewer.active_cs = cross_sections
            self.setting_active_profile_in_mapviewer()
            self.enable_action_set_1D_profile_in_mapviewer()
        else:
            logging.info(_("The profile's name provided is not in the list of sorted cross sections."))

    # --- ADDING DATA ---
    # ___________________

    def add_object(self, file, id:str):
        """Add the given wolfhece object
        in both the GUI and mapviewer.

        :param file: the object to add
        :type file: every `wolfhece.object`
        :param id: object name displayed in mapviewer
        :type id: str
        :return: a boolean value for checking whether
        the process succeeded or aborted.
        :rtype: bool
        """

        test_object = self.get_object_from_WolfMapViewer(id)

        if test_object == None:
            check_process = self.add_in_WolfMapViewer(file, id)
            if check_process:
                logging.info(f"{id} added.")
        elif test_object != None:
            # FIXME Keep the object if the change aborts.
            self.remove_from_WolfMapViewer(id)
            check_process = self.add_in_WolfMapViewer(file, id)
            if check_process:
                logging.info(f"{id} changed.")
        return check_process

    def add_in_WolfMapViewer(self,
                             file:str,
                             id: str='') -> int:
        """Add a new object in the interface
        by providing its path.

        :param file: object's path (computer's path)
        :type file: str
        :param id: object name displayed in mapviewer, defaults to ''
        :type id: str, optional
        :return: a boolean value for checking whether
        the process succeeded or aborted.
        :rtype: int
        """
        check_process = self.mapviewer.add_object(which= file, id=id)
        if check_process == -1:
            return False
        elif check_process == 0:
            return True

    def select_mapviewer_data(self,data_type: Literal['array','cross_sections','vector'] ):
        """Return the selected data from the mapviewer.

        :param data_type: type of the `wolfhece.object` to add
        but should be among the implemented literals.
        :type data_type: Literal[&#39;array&#39;,&#39;cross_sections&#39;,&#39;vector&#39;]
        :return: _description_
        :rtype: `wolfhece.object`
        """
        if data_type =='array':
            return self.mapviewer.myarrays[-1]
        elif data_type == 'vector':
            return self.mapviewer.myvectors[-1]
        elif data_type =='cross_sections':
            return self.mapviewer.myvectors[-1]

    def get_object_from_WolfMapViewer( self, id:str):
        """Get object from the interface
        (wolf map viewer) based on its id.

        :param id: object name displayed in mapviewer
        :type id: str
        :return: the chosen object
        :rtype: `wolfhece.object`
        """
        return self.mapviewer.getobj_from_id(id)

    def add_crossections_from_menu(self, event: wx.Event):
        """Add a cross section file using the submenu.

        :param event: `wx.EVT_MENU
        :type event: wx.Event
        """
        self.add_crossection()

    def add_bed_and_banks_from_menu(self, event: wx.Event):
        """Add bed and banks using the submenu.

        :param event: `wx.EVT_MENU`
        :type event: wx.Event
        """
        self.add_bed_and_banks()

    def add_bathymetry_from_menu(self, event: wx.Event):
        """Add bathymetric array using the submenu.

        :param event: `wx.EVT_MENU`
        :type event: wx.Event
        """

        self.add_bathymetry()

    def add_friction_from_menu(self, event: wx.Event):
        """Add friction array using the submenu.

        :param event: `wx.EVT_MENU`
        :type event: wx.Event
        """
        self.add_friction()

    def add_landmark_from_menu(self, event: wx.Event):
        """Add land marks from using the submenu.

        :param event: `wx.EVT_MENU`
        :type event: wx.Event
        """
        self.add_landmark()

    def add_crossection(self):
        '''Add or change the cross section.
        '''
        self.delete_cells_related_pages() # to avoid duplication of pages in case of a  change without deletion
        gui_id = Constants.GUI_ID_CROSS_SECTION.value
        check_process = self.add_object(file='cross_sections',id=gui_id)
        if check_process:
            self.update_data(variable_name= Constants.CROSS_SECTIONS.value,
                            new_object_id= gui_id)
            self.chek_cross_sections()
            self.update_cells_name()
            self.data_cross_sections.Enable(enable=True)
            self.Refresh()
        else:
            try:
                self.data.pop(Constants.CROSS_SECTIONS.value)
                self.delete_crossection(False)
            except:
                logging.info(_(f"Adding {Constants.GUI_ID_CROSS_SECTION.value} canceled."))

    def add_bed_and_banks(self):
        """Add or change the river and bank data.
        """
        self.delete_cells_related_pages() # to avoid duplication of pages in case of a  change without deletion
        gui_id = Constants.GUI_ID_BED_AND_BANKS.value
        check_process = self.add_object(file='vector', id=gui_id)
        if check_process:
            self.update_data(variable_name= Constants.BED_AND_BANKS.value,
                            new_object_id= gui_id)
            self.chek_bed_and_banks()
            self.update_cells_name()
            self.data_river_banks.Enable(enable=True)
            self.Refresh()
        else:
            try:
                self.data.pop(Constants.BED_AND_BANKS.value)
                self.delete_bed_and_banks(False)
            except:
                logging.info(_(f"Adding {Constants.GUI_ID_BED_AND_BANKS.value} canceled."))

    def add_bathymetry(self):
        """Add or change the bathymetric data.
        """
        gui_id = Constants.GUI_ID_BATHYMETRY.value
        check_process = self.add_object(file='array', id=gui_id)
        if check_process:
            self.update_data(variable_name= Constants.BATHYMETRY.value,
                            new_object_id= gui_id)
            self.chek_bathymetry()
            self.data_bathymetry.Enable(enable=True)
            self.Refresh()
        else:
            try:
                self.data.pop(Constants.BATHYMETRY.value)
                self.delete_bathymetry(False)
            except:
                logging.info(_(f"Adding {Constants.GUI_ID_BATHYMETRY.value} canceled."))

    def add_friction(self):
        """Add or change the friction data.
        """
        gui_id = Constants.GUI_ID_FRICTION.value
        check_process = self.add_object(file='array', id=gui_id)
        if check_process:
            self.update_data(variable_name= Constants.FRICTIONS.value,
                            new_object_id= gui_id)
            self.chek_friction()
            self.data_frictions.Enable(enable=True)
            self.enable_selection_mode_frictions()
            self.enable_agglomeration_mode()
            self.Refresh()
        else:
            try:
                self.data.pop(Constants.FRICTIONS.value)
                self.delete_friction(False)
            except:
                logging.info(_(f"Adding {Constants.GUI_ID_FRICTION.value} canceled."))

    def add_landmark(self):
        """Add or change the landmarks data.
        """
        gui_id = Constants.GUI_ID_LANDMARK.value
        check_process = self.add_object(file='vector', id=gui_id)
        if check_process:
            self.update_data(variable_name= Constants.LANDMARK.value,
                            new_object_id= gui_id)
            self.chek_land_mark()
            self.data_landmark.Enable(enable=True)
            self.Refresh()
        else:
            try:
                self.data.pop(Constants.LANDMARK.value)
                self.delete_land_mark(False)
            except:
                logging.info(_(f"Adding {Constants.GUI_ID_LANDMARK.value} canceled."))

    def add_executable(self):
        """Add the path of the wolf executable
        which will be used by the GUI.
        """
        if self.executable.IsEnabled():
            dlg = wx.FileDialog(self, 'Select the executable',
                                wildcard='wolfcli or wolfclid (*.exe)|*.exe')
            ret = dlg.ShowModal()
            if ret == wx.ID_OK:
                file_path = dlg.GetPath()
                dlg.Destroy()
            else:
                 dlg.Destroy()
                 return
            executable_type = os.path.split(file_path)[1]
            wolfcli = Titles.WOLFCLI.value.lower()
            wolfclid = Titles.WOLFCLID.value.lower()
            if executable_type[:-4] == wolfcli:
                self.executable_path = file_path
                self.executable_selected = Titles.WOLFCLI.value
                self.executable.SetValueFromString(self.executable_selected)
                self.enable_button_parameters()

            elif executable_type[:-4] == wolfclid:
                self.executable_path = file_path
                self.executable_selected = Titles.WOLFCLID.value
                self.executable.SetValueFromString(self.executable_selected)
                self.enable_button_parameters()

            else:
                self.executable.SetValue(0)
                self.executable_selected = None
                logging.info("This type executable is not recognized")

    # --- REMOVING & UPDATING DATA ---
    # ________________________________

    def delete_data(self,
                    variable_name:str,
                    object_id:str):
        """Delete an object from both
        the notebook and the interface
        (mapviewer).

        :param variable_name: object name used  by the notebook
        :type variable_name: str
        :param object_id: name displayed in the mapviewer
        :type object_id: str
        """
        try:
            self.data.pop(variable_name)
            self.remove_from_WolfMapViewer(object_id)
        except KeyError:
            logging.info("The selected data does not exist")

    def remove_from_WolfMapViewer(self, id: str):
        """Remove an object from the interface
        (mapviewer) based on its id.

        :param id: name displayed in the mapviewer
        :type id: str
        """
        self.mapviewer.removeobj_from_id(id)

    def delete_crossection(self, remove_in_mapviewer = True):
        """Delete the cross section
        from both this GUI and
        the interface.

        :param remove_in_mapviewer: remove the object from the mapviewer
        (this option skips the removal from mapviewer
        in case of unavailable object in the mapviewer), defaults to True
        :type remove_in_mapviewer: bool, optional
        """
        self.data_cross_sections.Enable(enable=False)
        if remove_in_mapviewer:
            self.delete_data(Constants.CROSS_SECTIONS.value,
                                Constants.GUI_ID_CROSS_SECTION.value)
        self.freeze_cross_sections_related()
        self.delete_cells_related_pages()
        self.data_cross_sections.SetValueFromString('False')
        logging.info(_(f"{Constants.GUI_ID_CROSS_SECTION.value} deleted."))

    def delete_bed_and_banks(self, remove_in_mapviewer = True):
        """Delete the bed and banks
        from both this GUI and
        the interface.

        :param remove_in_mapviewer: remove the object from the mapviewer
        (this option skips the removal from mapviewer
        in case of unavailable object in the mapviewer), defaults to True
        :type remove_in_mapviewer: bool, optional
        """
        self.data_cross_sections.Enable(enable=False)
        if remove_in_mapviewer:
            self.delete_data(Constants.BED_AND_BANKS.value,
                                Constants.GUI_ID_BED_AND_BANKS.value)
        self.freeze_cross_sections_related()
        self.delete_cells_related_pages()
        self.data_river_banks.SetValueFromString('False')
        logging.info(_(f"{Constants.GUI_ID_BED_AND_BANKS.value} deleted."))

    def delete_bathymetry(self, remove_in_mapviewer = True):
        """
        Delete the bathymetry
        from both this GUI and
        the interface.

        :param remove_in_mapviewer: remove the object from the mapviewer
        (this option skips the removal from mapviewer
        in case of unavailable object in the mapviewer), defaults to True
        :type remove_in_mapviewer: bool, optional
        """
        self.data_bathymetry.Enable(enable=False)
        if remove_in_mapviewer:
            self.delete_data(Constants.BATHYMETRY.value,
                                Constants.GUI_ID_BATHYMETRY.value)
        self.data_bathymetry.SetValueFromString('False')
        logging.info(_(f"{Constants.GUI_ID_BATHYMETRY.value} deleted."))

    def delete_friction(self, remove_in_mapviewer = True):
        """Delete the friction
        from both this GUI and
        the interface.

        :param remove_in_mapviewer: remove the object from the mapviewer
        (this option skips the removal from mapviewer
        in case of unavailable object in the mapviewer), defaults to True
        :type remove_in_mapviewer: bool, optional
        """
        self.data_frictions.Enable(enable=False)
        if remove_in_mapviewer:
            self.delete_data(Constants.FRICTIONS.value,
                                Constants.GUI_ID_FRICTION.value)
        self.data_frictions.SetValueFromString('False')
        self.enable_forced_value()
        self.selection_friction_mode.Enable(False)
        logging.info(_(f"{Constants.GUI_ID_FRICTION.value} deleted."))

    def delete_land_mark(self, remove_in_mapviewer = True):
        """Delete the landmarks
        from both this GUI and
        the interface.

        :param remove_in_mapviewer: remove the object from the mapviewer
        (this option skips the removal from mapviewer
        in case of unavailable object in the mapviewer), defaults to True
        :type remove_in_mapviewer: bool, optional
        """
        self.data_landmark.Enable(enable=False)
        if remove_in_mapviewer:
            self.delete_data(Constants.LANDMARK.value,
                                Constants.GUI_ID_LANDMARK.value)
        self.data_landmark.SetValueFromString('False')
        logging.info(_(f"{Constants.GUI_ID_LANDMARK.value} deleted."))

    def delete_line_in_txt_file(self, file_path:str, line_to_delete:str):
        """Delete a specific line (known) in a given text file.

        :param file_path: computer path to the text file,
        :type file_path: str
        :param line_to_delete: line that should be deleted.
        :type line_to_delete: str
        """
        with open(file_path,"r") as file:
            lines = file.readlines()

        with open(file_path,"w") as file:
            for line in lines:
                if line !=  line_to_delete:
                    file.write(line)

    def update_data(self,
                    variable_name: str,
                    new_object_id: str):
        """update (link) to the right data (object)
        in the interface.

        :param variable_name: new object's name in this notebook.
        :type variable_name: str
        :param new_object_id: new object's name in the mapviewer
        :type new_object_id: str
        """
        try:
            self.data.pop(variable_name)
        except KeyError:
            pass
        self.data[variable_name] = self.get_object_from_WolfMapViewer(new_object_id)

    def correct_parameters(self,directory = ''):
        """Correct the content of the parameter files
        (.param and .param.default created by the fortran executable.)

        :param directory: computer's path to the directory containing the files, defaults to ''
        :type directory: str, optional
        """
        for file in os.listdir(directory):
            if file.endswith(".param"):
                param_file = os.path.join(directory, file)
                self.delete_line_in_txt_file(param_file,
                                     'Limiteur\t7\tType de limitation des reconstruction en lineaire (integer1)\n')
            elif file.endswith(".param.default"):
                default_file = os.path.join(directory, file)
                self.delete_line_in_txt_file(default_file,
                                     'Limiteur\t7\tType de limitation des reconstruction en lineaire (integer1)\n')

    # --- CONTROLS ---
    #_________________

    def freeze_commands(self):
        """Freeze most of the notebook
        commands to avoid manipulation errors.
        """
        self.data_cross_sections.Enable(enable=False)
        self.data_river_banks.Enable(enable=False)
        self.data_bathymetry.Enable(enable=False)
        self.data_frictions.Enable(enable=False)
        self.data_landmark.Enable(enable=False)
        self.extrapolation_of_extremities.Enable(enable=False)
        # self.discretization_step.Enable(enable=False) # FIXME to be implemented later
        self.selection_friction_mode.Enable(enable=False)
        self.agglomeration_friction_mode.Enable(enable=False)
        self.forced_value.Enable(enable=False)
        self.type_ic_file.Enable(enable=False)
        self.water_depth.Enable(enable=False)
        # self.water_level.Enable(enable=False) # FIXME Not yet used (the method is still ackward)
        self.discharge.Enable(enable=False)
        self.computation_mode.Enable(enable=False)
        self.executable.Enable(enable=False)
        self.run_simulation.Enable(enable=False)
        self.steadiness_mode.Enable(False)
        self.hydrographs_preprocess.Enable(False)
        self.epsilon.Enable(False)
        self.button_parameter.Enable(enable=False)
        self.button_save.Enable(enable=False)

    def freeze_cross_sections_related(self):
        """Freeze all commands which require
        the presence of sorted cross sections.
        """
        self.extrapolation_of_extremities.Enable(enable=False)
        # self.discretization_step.Enable(enable=False) # FIXME to be implemented later
        self.forced_value.Enable(enable=False)
        self.type_ic_file.Enable(enable=False)
        self.water_depth.Enable(enable=False)
        # self.water_level.Enable(enable=False) # FIXME Not yet used (the method is still ackward)
        self.discharge.Enable(enable=False)
        self.computation_mode.Enable(enable=False)
        self.executable.Enable(enable=False)
        self.steadiness_mode.Enable(False)
        self.run_simulation.Enable(enable=False)
        self.disable_infiltration_preprocess()
        self.disable_action_in_mapviewer()

    def unfreeze_crossections_related(self):
        """Unfreeze all commands which require
        the presence of sorted cross sections.
        """
        self.extrapolation_of_extremities.Enable(enable=True)
        # self.discretization_step.Enable(enable=True)  # FIXME to be implemented later

        self.type_ic_file.Enable(enable = True)
        self.water_depth.Enable(enable=True)
        # self.water_level.Enable(enable=True) # FIXME Not yet used (the method is still ackward.)
        # self.discharge.Enable(enable=True)
        self.steadiness_mode.Enable(True)
        self.computation_mode.Enable(enable=True)
        self.executable.Enable(enable=True)
        self.run_simulation.Enable(enable=True)
        self.enable_infiltration_preprocess()
        if self.agglomeration_friction_mode.IsEnabled():
            pass
        else:
            self.forced_value.Enable(enable=True)

    def enable_selection_mode_frictions(self):
        """Enable the selection of a friction mode.
        """
        if self.forced_value.IsEnabled():
            self.forced_value.Enable(False)
        self.selection_friction_mode.Enable(True)
        self.selection_friction_mode.SetValue(2)

    def selection_friction_mode_changed(self):
        """Based on a selected friction mode,
        enable either the option for agglomeration of friction
        or for forcing a unique friction value on all profiles.
        """
        value = self.selection_friction_mode.GetValueAsString()
        if value == Titles.FORCE_VALUE.value:
            self.enable_forced_value()
        elif  value == Titles.UNDER_PROFILES.value:
            self.enable_agglomeration_mode()

    def enable_agglomeration_mode(self):
        """Enable the agglomeration of frictions
        from a 2D array.
        """
        if self.selection_friction_mode.IsEnabled():
            self.forced_value.Enable(False)
            self.agglomeration_friction_mode.Enable(True)
            self.agglomeration_friction_mode.SetValue(1)
            self.selection_friction_mode.SetValue(2)

    def enable_forced_value(self):
        """Enable the forcing of a unique friction
        value on all profiles.
        """
        if self.selection_friction_mode.IsEnabled():
            self.forced_value.Enable(True)
            self.selection_friction_mode.SetValue(1)
            self.agglomeration_friction_mode.Enable(False)

    def chek_cross_sections(self):
        """Check the property box of the cross section
        on the main page.
        """
        self.data_cross_sections.SetValueFromString('True')

    def chek_bed_and_banks(self):
        """Check the property box of the bed and banks
        on the main page.
        """
        self.data_river_banks.SetValueFromString('True')

    def chek_bathymetry(self):
        """Check the property box of the bathymetry
        on the main page.
        """
        self.data_bathymetry.SetValueFromString('True')

    def chek_friction(self):
        """Check the property box of the friction
        on the main page.
        """
        self.data_frictions.SetValueFromString('True')

    def chek_land_mark(self):
        """Check the property box of the land marks
        on the main page.
        """
        self.data_landmark.SetValueFromString('True')

    def enable_button_parameters(self):
        """Allow the parameters button usage
        on the main page.
        """
        self.button_parameter.Enable(enable=True)

    def disable_button_parameters(self):
        """Block the parameters button usage
        on the main page"""
        self.button_parameter.Enable(enable=False)

    def enable_button_save(self):
        """Allow the button save usage on
        the main page
        """
        self.button_save.Enable(True)

    def disable_button_save(self):
        """Block the button
        save usage on the main page"""
        self.button_save.Enable(False)

    def enable_infiltration_preprocess(self):
        """Allow the choice between continuous hydrographs
        or a stepwise ones (pre-processed).
        """
        if Titles.INFILTRATIONS.value in self.notebook_pages.keys():
            self.hydrographs_preprocess.Enable(True)
            # self.epsilon.Enable(True)

    def enable_initial_discharge(self):
        """Enable the encoding of the initial
        disharge value.
        """
        if self.type_ic_file.IsEnabled():
            if self.discharge.IsEnabled():
                self.discharge.Enable(enable= False)
            else:
                self.discharge.Enable(enable=True)

    def disable_infiltration_preprocess(self):
        """Restrict the choice between continuous hydrographs
        or a stepwise ones (pre-processed).
        """
        self.hydrographs_preprocess.Enable(False)
        self.epsilon.SetValue(0.01)
        self.epsilon.Enable(False)

    def lock_executable(self):
        """Block the manual selection of an executable type.
        """
        if self.executable_selected != None:
            self.executable.SetValueFromString(self.executable_selected)
        else:
            self.executable.SetValue(0)

    def cross_check_sections(self):
        """Automatically enable or disable the cross section property check box.
        """
        current_value = self.data_cross_sections.GetValue()
        if current_value == True:
            self.data_cross_sections.SetValueInEvent(False)
        elif current_value == False:
            self.data_cross_sections.SetValueInEvent(True)

    # --- RETRIEVING INPUTS ---
    #____________________________

    def get_boundary_conditions(self) -> dict:
        """Return the dictionnary of boundary conditions.

        :return: dictionnary of boundary conditions.
        :rtype: dict
        """
        page_boundary_conditions: Boundary_condition_Page
        page_boundary_conditions = self.notebook.GetPage(self.find_page_number(Titles.BC_CONDITIONS.value))
        assert len(page_boundary_conditions.dictionary_boundary_conditions) > 0,\
            logging.info("Error - Boundary conditions not defined.")
        return page_boundary_conditions.dictionary_boundary_conditions

    def get_hydrographs(self) -> dict:
        """Return the dictionnary of hydrographs.
        (infiltrations).

        :return: dictionnary of hydrographs
        :rtype: dict
        """
        page_hydrographs : MultigridPage
        page_hydrographs = self.notebook.GetPage(self.find_page_number(Titles.INFILTRATIONS.value))
        assert len(page_hydrographs.dictionary_hydrographs) > 0,\
            logging.info("Error - No infiltrations in the dictionary of hydrographs")
        return page_hydrographs.dictionary_hydrographs

    def get_frictions(self):
        """Return the friction values.

        :raises Exception: in case friction values are still missing and wx.exist.
        :raises Exception: in case friction values are still missing
        :return: friction values
        :rtype: `wolfarray` or `int`
        """
        if self.forced_value.IsEnabled():
            return abs(float(self.forced_value.GetValue()))

        elif not self.forced_value.IsEnabled():
            if isinstance(self.data[Constants.FRICTIONS.value],WolfArray):
                return self.data[Constants.FRICTIONS.value]
            else:
                if self.wx_exists:
                    raise Exception(logging.warning("Friction are still missing:\
                                                    Provide a wolfarray or force a value."))
                else:
                    raise Exception("Friction are still missing:\
                                    Provide a wolfarray or force a value.")

    def get_agglomeration_mode(self) -> str:
        """Return the agglomeration mode
        of frictions selected on the main page.

        :return: agglomeration mode of values
        (mean, median, min, max, etc).
        :rtype: str
        """
        if not self.forced_value.IsEnabled():
            return self.agglomeration_friction_mode.GetValueAsString().lower()
        else:
            return 'mean'

    def get_roughness_option(self) -> str:
        """Return the selection mode of frictions
        chosen on the main page.

        :return: selected mode
        :rtype: str
        """
        if not self.forced_value.IsEnabled():
            option = self.selection_friction_mode.GetValueAsString()
            if option == Titles.BETWEEN_PROFILES.value:
                return 'under_polygons'
            elif option == Titles.UNDER_PROFILES.value:
                return 'under_profile'
        else:
            return 'under_profile'

    def get_initial_water_depth(self) -> float:
        """Return the encoded value of
        the initial water depth.

        :return: intial water depth
        :rtype: float
        """
        if self.water_depth.IsEnabled():
            return float(self.water_depth.GetValue())

    def get_initial_discharge(self):
        """Return the encoded value of the
        discharge.

        :return: initial discharge
        :rtype: `float` or `None`
        """
        if self.discharge.IsEnabled():
            return float(self.discharge.GetValue())
        else:
            return None

    def get_ic_file_format(self) -> str:
        """Return the file format
        of intial conditions.

        :return: file format
        :rtype: str
        """
        if self.type_ic_file.IsEnabled:
            return self.type_ic_file.GetValueAsString()
        else:
            logging.warning("The format of initial conditions\
                            is not activated.")

    def get_infiltration_preprocess(self) -> str:
        """Return the selected mode in which the
        infiltrations hydrographs will be preprocessed.

        :return: preprossing mode (stepwise or continuous)
        :rtype: str
        """
        if len (self.get_hydrographs()) > 0:
            value = self.hydrographs_preprocess.GetValueAsString()
            if value == Titles.NO_PREPROCESSING.value:
                return 'continuous'
            elif value == Titles.STEPWISE.value:
                return 'stepwise'

    def get_epsilon(self) -> float:
        """Return the margin used to preprocess
        the infiltrations in case the stepwise option
        is selected.

        :return: epsilon (margin)
        :rtype: float
        """
        return float(self.epsilon.GetValue())

    def get_computation_mode(self) -> str:
        """Return the computation
        mode used by the 1D executable.

        :return: computation mode (evolutive or fixed)
        :rtype: _type_
        """
        if self.computation_mode.IsEnabled():
            value = self.computation_mode.GetValueAsString()
            if value == Titles.EVOLUTIVE.value:
                return 'evolutive'
            elif value == Titles.FIXED.value:
                return 'fixed'
        else:
            logging.warning("The computation mode\
                            is not activated.")

    def get_steadiness_mode (self) -> str:
        """Return the steadiness mode
        which will be used by the executable.

        :return: steadiness mode
        (No precomputation, precomputation, and steady)
        :rtype: str
        """
        if self.steadiness_mode.IsEnabled():
            value = self.steadiness_mode.GetValueAsString()
            if value == Titles.NO_PRECOMPUTATION.value:
                return 'no precomputation'
            elif value == Titles.PRECOMPUTATION.value:
                return 'precomputation'
            elif value == Titles.STEADY.value:
                return 'steady'
        else:
            logging.warning("The steadiness mode\
                            is not activated.")

    def get_executable(self) -> str:
        """Return the executable type
        to be used in `.bat` file.

        :return: excecutable type (currently wolfcli and wolfclid)
        :rtype: str
        """
        if self.executable.IsEnabled():
            value = self.executable.GetValue()
            if value != 0:
                executable_type = os.path.split(self.executable_path)[1]
                assert executable_type[:-4] == self.executable_selected.lower(),\
                    "The executable path is different from the selected executable."
                return self.executable.GetValueAsString().lower()

    def get_folder_executable(self) -> str:
        """return the computer path to
        the folder containing the executable.

        :return: folder(computer path in full)
        :rtype: str
        """
        if self.executable.IsEnabled():
            return os.path.split(self.executable_path)[0]

    def get_run_command(self) -> str:
        """Return the status of the run command.
        whether the simulation should be run
        or not after its creation.

        :return: status(yes or no)
        :rtype: str
        """
        if self.run_simulation.IsEnabled():
            value = self.run_simulation.GetValue()
            if value == True:
                return 'yes'
            else:
                return 'no'

    def get_extrapolation_of_extremities(self) -> float:
        """Return the value encode in the extrapolation of extremities.

        :return: Value of how far the 2 extremities of each
        profile should be elevated vertically.
        :rtype: float
        """
        if self.extrapolation_of_extremities.IsEnabled():
            return float(self.extrapolation_of_extremities.GetValue())
        else:
            logging.info('The extrapolation of exetremities is not enabled.')

    # --- TEST ---
    # ____________

    def test_required_data(self)-> bool:
        """ Test if all the required data are available
        to create and save a wolf 1D model.

        :return: True or False
        :rtype: bool
        """
        if Constants.CROSS_SECTIONS.value in self.data and Constants.BED_AND_BANKS.value in self.data:
            if self.notebook.GetPageCount() < 2:
                logging.info("Infiltrations and/or boundary conditions are still missing.")
                return False
            if len(self.get_hydrographs()) == 0:
                logging.info("Infiltrations are not defined.")
                return False
            if len(self.get_boundary_conditions()) == 0:
                logging.info("Boundary conditions are not defined. ")
                return False
            if self.executable_selected == None:
                logging.info("Could not proceed because the executable is not yet provided.")
                return False
            return True
        else:
            logging.info("Could not proceed because 1D data are still missing.")
            return False

    # --- USEFUL METHODS ---
    # ______________________

    def initialize_param_file(self):
        """Create the parameters file
        (`.param ` and `.param.default`)
        from the wolf executable (`.exe`).

        This method initialize a `temporary directory` in
        which it copies the executable and create 2 files
        `create_simul.txt` and `temporary.bat`.

          - The create_simul file contains the commands necessary
         to generate the parameter files from the executable
         by just passing in the directory;
          - Whereas, the .bat file contains
          a command to launch the executable (`.exe`).

        After running the wolf executable (`.exe`),
        the param file created, is first corected and then copied in the simulation directory.
        This file is then read by wolfparam to allow the modification of parameters through
        the wolfparam window (`wx.notebook`).
        """

        if self.simulation_directory != '' or self.simulation_directory != None:
            with tempfile.TemporaryDirectory() as temporary_directory:
                executable = self.get_executable()

                create_file = self.initialize_file(temporary_directory,
                                                "create_simul.txt")
                bat_file = self.initialize_file(temporary_directory,
                                                "temporary.bat")
                # FIXME create1d command of wolfcli is unable to write in a different directory
                # Than the one in which wolfcli.exe is contained.
                directory_executable = os.path.split(self.executable_path)[0]
                temporay_exe = shutil.copy(self.executable_path, temporary_directory)

                with open(create_file,'w') as f:
                    f.write(f"Dirs:"+"\n")
                    f.write(f"output_directory	{temporary_directory}"+"\n")
                    f.write(f"Files:"+"\n")
                    f.write(f"generic_file	simul"+"\n")
                    f.write(f"Action:"+"\n")
                    f.write(f"example_files	1"+"\n")

                with open(bat_file,'w') as bat:
                    bat.write(f'{temporary_directory[:2]}\n')
                    bat.write(f'cd "{temporary_directory}"\n')
                    bat.write(f'{executable} create1d in="{temporary_directory}"')


                run = Popen(bat_file, stdin=PIPE,stdout=PIPE,stderr=PIPE,cwd=temporary_directory)
                run.wait()
                run.returncode
                file = os.path.join(temporary_directory,r"helpme\simul.param.default")
                assert self.simulation_name != None or self.simulation_name != '',\
                    "The simulation name is not defined."
                logging.info(_("Initialization of the param files..."))
                new_param = os.path.join(self.simulation_directory,f"{self.simulation_name}.param")
                new_default = os.path.join(self.simulation_directory,f"{self.simulation_name}.param.default")
                shutil.copy(file, new_param)
                shutil.copy(file, new_default)
                self.correct_parameters(self.simulation_directory)

            self.grid_parameters = Wolf_Param(self,
                                            filename= new_param,
                                            title=Titles.WOLF_PARAM_WINDOW.value,
                                            w= Constants.FRAMESIZE.value[0],
                                            h= Constants.FRAMESIZE.value[1],
                                            ontop= True,
                                            force_even_if_same_default= True)
            self.param_exists = True
            logging.info("Simulation parameters enabled.")
        else:
            logging.info("Cannot initialize the model\
                         because the simulation directory is not defined.")

    def initialize_file(self, directory_path: str, filename:str) -> str:
        """Initialize a computer path to a new file.

        :param directory_path: Path to the folder
        :type directory_path: str
        :param filename: filename
        :type filename: str
        :return: full computer path to the new file
        :rtype: str
        """
        return os.path.join(directory_path, filename)

    def click_on_parameters(self, event: wx.Event):
        """The click on  the parameters button launch the process:
         - to create a simulatin directory (folder)
         - to initialize the param file
         - to disable the button parameters while enabling the button save.

        :param event: wx.EVT_BUTTON
        :type event: wx.Event
        """
        if self.test_required_data() == True:
            self.simulation_directory = self.create_simulation_directory()
            self.initialize_param_file()
            self.disable_button_parameters()
            self.enable_button_save()

    def create_simulation_directory(self) -> str:
        """Create and return the simulation directory.

        :return: computer path to the folder
        in which the simulation files wil be written.
        :rtype: str
        """
        dlg = wx.DirDialog(None, _('Specify a simulation directory'))
        ret = dlg.ShowModal()
        if ret == wx.ID_CANCEL:
            return ''
        elif ret == wx.ID_OK:
            file_path = dlg.GetPath()
            dlg_name = wx.TextEntryDialog(self,_('Model name'), _('Provide a name for this model.'), _('simul'))
            if dlg_name == wx.ID_CANCEL:
                return ''
            elif dlg_name.ShowModal() == wx.ID_OK:
                self.simulation_name = dlg_name.GetValue()
                return self.creator1D.create_simulation_directory(file_path, self.simulation_name)

        dlg = wx.DirDialog(None, _('Specify a simulation directory'))
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            file_path = dlg.GetPath()
        elif ret == wx.ID_CANCEL:
            return ''

        dlg_name = wx.TextEntryDialog(self,_('Model name'), _('Provide a name for this model.'), _('simul'))

        if dlg_name.ShowModal() == wx.ID_OK:
            simulation_name = dlg_name.GetValue()
            return self.creator1D.create_simulation_directory(file_path, simulation_name)
        else:
            return ''

    def infiltration_preprocess_changed(self):
        """Manage the choice of the infiltration preprocessing mode.
        """
        value = self.hydrographs_preprocess.GetValueAsString()
        if  value == Titles.STEPWISE.value:
            self.epsilon.Enable(True)
        elif value == Titles.NO_PREPROCESSING.value:
            self.epsilon.SetValue(0.01)
            self.epsilon.Enable(False)

    def close(self):
        self.Destroy()
        logging.info(_("Wolf1D closed."))

    def quit(self, event: wx.Event):
        """Destroy safely this window from the menu.

        :param event: wx.event
        :type event: wx.Event
        """
        self.close()

    def onclose(self, event: wx.Event):
        self.close()

    def get_bathymetry(self):
        """Return the bathymetry object
        from the notebook.

        :return: bathymetry object
        :rtype: `WolfArray`
        """
        try:
            return self.data[Constants.BATHYMETRY.value]
        except KeyError:
            return None

    # --- CREATION OF A SIMULATION ---
    # ________________________________

    def button_save_clicked(self, event: wx.Event):
        """Gather all the inputs in the notebook
        and generate a 1D model (simulation).

        :param event: wx.EVT_BUTTON
        :type event: wx.Event
        :raises Exception: In case, the model fails to create the simulation
        for whatever reasons.
        """
        if self.test_required_data() == True:
            if self.simulation_directory != '':
                logging.info(_("Creating the model... ... ...\
                                \nPatience, you'll be notified whenever the model is ready."))
                # self.grid_parameters.saveme FIXME Param from GUI
                # FIXME Parallel value should not be mandatory in case only one vector exists.
                try:
                    self.disable_button_save()
                    # self.grid_parameters.Hide()
                    simul = self.creator1D.write_simulation_files_from_crosssections(folder_path = self.simulation_directory,
                                                                            cross_sections = self.data[Constants.CROSS_SECTIONS.value],
                                                                            parallels = self.data[Constants.BED_AND_BANKS.value],
                                                                            banks= self.data[Constants.BED_AND_BANKS.value],
                                                                            boundary_conditions= self.get_boundary_conditions(),
                                                                            hydrographs=self.get_hydrographs(),
                                                                            roughness= self.get_frictions(),
                                                                            roughness_selection= self.get_agglomeration_mode(),
                                                                            roughness_option= self.get_roughness_option(),
                                                                            exe_file= self.get_folder_executable(),
                                                                            initial_depth= self.get_initial_water_depth(),
                                                                            topography= self.get_bathymetry(),
                                                                            initial_discharge= self.get_initial_discharge(),
                                                                            file_type_initial_cond= self.get_ic_file_format(),
                                                                            extrapolation_of_extremities= self.get_extrapolation_of_extremities(),
                                                                            wetdry= self.get_computation_mode(),
                                                                            steady= self.get_steadiness_mode(),
                                                                            writing_type_infiltration= self.get_infiltration_preprocess(),
                                                                            epsilon_infiltration= self.get_epsilon(),
                                                                            executable_type= self.get_executable(),
                                                                            run_simulation= 'no',
                                                                            simulation_name= self.simulation_name,
                                                                            new_directory= self.simulation_directory
                                                                            )
                    logging.info(_("The model was successfully created."))
                    self.grid_parameters.save_automatically_to_file()
                    self.param_exists == False
                    self.enable_button_parameters()
                    self.grid_parameters.Destroy()
                    if self.get_run_command() == 'yes':
                        try:
                            self.creator1D.run_bat_files(os.path.join(simul[0], f'{simul[1]}.bat'))
                        except:
                            try:
                                batch_file = self.creator1D.find_file_from_extension(self.simulation_directory, '.bat')
                            except:
                                logging.info(f"The batch file was not found.\n The {self.simulation_name} was not run.")

                except:
                    self.enable_button_parameters()
                    raise Exception(logging.info("The simulation not saved due to an error."))
        # self.disable_button_save()

    # --- DEPRECIATING METHODS ---
    # ____________________________

    def __call_parameters(self):
        """
        FIXME outdated no longer used
        A temporary .param file is created
        to initialize the panel of parameters.

        If the panel is closed (destroyed),
        the information are lost.

        FIXME wolf_Param should be a panel not a frame.
        """

        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_creator = Creator_1D()
            temp_creator.write_parameters(temporary_directory)
            for file in os.listdir(temporary_directory):
                if file.endswith(".param"):
                    self.grid_parameters = Wolf_Param(self,
                                                filename= os.path.join(temporary_directory,file),
                                                title=Titles.WOLF_PARAM_WINDOW.value,
                                                w= Constants.FRAMESIZE.value[0],
                                                h= Constants.FRAMESIZE.value[1])
                    self.param_exists = True
                    self.grid_parameters.saveme.Enable(False)
                    # self.grid_parameters.reloadme.Enable(False)
                    break

        # # temporary_directory.close

    def __click_on_parameters(self, event:wx.Event):
        # FIXME
        id  = event.GetEventObject().GetName()
        if id == 'parameters':
            if self.param_exists:
                try:
                    if self.grid_parameters.IsShown():
                        pass
                    else:
                        self.grid_parameters.Show()
                except RuntimeError:
                    self.param_exists= False
                    self.call_parameters()
            else:
                self.call_parameters()

    def __button_save_clicked(self, event: wx.Event):
        """
        Display
        """
        if self.test_required_data() == True:
            self.simulation_directory = self.create_simulation_directory()
            self.initialize_param_file()

            if self.simulation_directory != '':
                # self.grid_parameters.saveme FIXME Param from GUI
                # FIXME Parallel value should not be mandatory in case only one vector exists.
                self.creator1D.write_simulation_files_from_crosssections(folder_path = self.simulation_directory,
                                                                        cross_sections = self.data[Constants.CROSS_SECTIONS.value],
                                                                        parallels = self.data[Constants.BED_AND_BANKS.value],
                                                                        banks= self.data[Constants.BED_AND_BANKS.value],
                                                                        boundary_conditions= self.get_boundary_conditions(),
                                                                        hydrographs=self.get_hydrographs(),
                                                                        roughness= self.get_frictions(),
                                                                        roughness_selection= self.get_agglomeration_mode(),
                                                                        roughness_option= self.get_roughness_option(),
                                                                        exe_file= self.get_folder_executable(),
                                                                        initial_depth= self.get_initial_water_depth(),
                                                                        topography= self.data[Constants.BATHYMETRY.value],
                                                                        initial_discharge= self.get_initial_discharge(),
                                                                        file_type_initial_cond= self.get_ic_file_format(),
                                                                        extrapolation_of_extremities= self.get_extrapolation_of_extremities(),
                                                                        wetdry= self.get_computation_mode(),
                                                                        steady= self.get_steadiness_mode(),
                                                                        writing_type_infiltration= self.get_infiltration_preprocess(),
                                                                        epsilon_infiltration= self.get_epsilon(),
                                                                        executable_type= self.get_executable(),
                                                                        run_simulation= self.get_run_command(),
                                                                        simulation_name= self.simulation_name,
                                                                        new_directory= self.simulation_directory
                                                                        )

    def __button_save_clicked(self, event: wx.Event):
        """Gather all the inputs in the notebook
        and generate a 1D model (simulation).

        :param event: wx.EVT_BUTTON
        :type event: wx.Event
        :raises Exception: In case, the model fails to create the simulation
        for whatever reasons.
        """
        if self.test_required_data() == True:
            self.grid_parameters.save_automatically_to_file()

        if self.simulation_directory != '':
            logging.info(_("Creating the model... ... ...\
                            \nPatience, you'll be notified whenever the model is ready."))
            # self.grid_parameters.saveme FIXME Param from GUI
            # FIXME Parallel value should not be mandatory in case only one vector exists.
            try:
                self.disable_button_save()
                # self.grid_parameters.Hide()
                self.creator1D.write_simulation_files_from_crosssections(folder_path = self.simulation_directory,
                                                                        cross_sections = self.data[Constants.CROSS_SECTIONS.value],
                                                                        parallels = self.data[Constants.BED_AND_BANKS.value],
                                                                        banks= self.data[Constants.BED_AND_BANKS.value],
                                                                        boundary_conditions= self.get_boundary_conditions(),
                                                                        hydrographs=self.get_hydrographs(),
                                                                        roughness= self.get_frictions(),
                                                                        roughness_selection= self.get_agglomeration_mode(),
                                                                        roughness_option= self.get_roughness_option(),
                                                                        exe_file= self.get_folder_executable(),
                                                                        initial_depth= self.get_initial_water_depth(),
                                                                        topography= self.data[Constants.BATHYMETRY.value],
                                                                        initial_discharge= self.get_initial_discharge(),
                                                                        file_type_initial_cond= self.get_ic_file_format(),
                                                                        extrapolation_of_extremities= self.get_extrapolation_of_extremities(),
                                                                        wetdry= self.get_computation_mode(),
                                                                        steady= self.get_steadiness_mode(),
                                                                        writing_type_infiltration= self.get_infiltration_preprocess(),
                                                                        epsilon_infiltration= self.get_epsilon(),
                                                                        executable_type= self.get_executable(),
                                                                        run_simulation= self.get_run_command(),
                                                                        simulation_name= self.simulation_name,
                                                                        new_directory= self.simulation_directory
                                                                        )
                logging.info(_("The model was successfully created."))
                self.grid_parameters.Destroy()
                self.param_exists == False
                self.enable_button_parameters()

            except:
                self.enable_button_parameters()
                raise Exception(logging.info("The simulation not saved due to an error."))

    def __add_bed_and_banks(self, event: pg.EVT_PG_DOUBLE_CLICK):
        """
        Add or change the river and bank data.
        """
        id = event.PropertyName
        if id == 'bed_and_banks':
            gui_id = Constants.GUI_ID_BED_AND_BANKS.value
            self.add_object(file='vector', id=gui_id)
            self.update_data(variable_name= Constants.BED_AND_BANKS.value,
                            new_object_id= gui_id)
            self.chek_bed_and_banks()
            self.data_river_banks.Enable(enable=True)
            self.Refresh()
            logging.info(_('New river bed and banks available!'))

    def __delete_bed_and_banks(self, event: pg.EVT_PG_CHANGED):
        """
        Delete the bed and banks
        from both this GUI and
        the interface.
        """
        id = event.PropertyName
        if id == 'bed_and_banks':
            self.data_cross_sections.Enable(enable=False)
            self.delete_data(Constants.BED_AND_BANKS.value,
                             Constants.GUI_ID_BED_AND_BANKS.value)

    def __add_crossection(self, event: pg.EVT_PG_DOUBLE_CLICK):
        '''
        Add or change the cross section.
        '''
        id = event.PropertyName
        if id == 'data_cross_sections':
            gui_id = Constants.GUI_ID_CROSS_SECTION.value
            self.add_object(file='cross_sections',id=gui_id)
            self.update_data(variable_name= Constants.CROSS_SECTIONS.value,
                            new_object_id= gui_id)
            # self.data[Constants.CROSS_SECTIONS.value] =  self.get_object_from_WolfMapViewer(gui_id)
            self.chek_cross_sections()
            self.data_cross_sections.Enable(enable=True)
            self.Refresh()
            logging.info(_('New cross section available!'))

    def __delete_crossection(self, event:pg.EVT_PG_CHANGED):
        """
        Delete the cross section
        from both this GUI and
        the interface.
        """
        id = event.PropertyName
        if id == 'data_cross_sections':
            self.data_cross_sections.Enable(enable=False)
            self.delete_data(Constants.CROSS_SECTIONS.value,
                             Constants.GUI_ID_CROSS_SECTION.value)
            # self.data_cross_sections.se
            # self.data_cross_sections.Enable(enable=False)

    def __create_id(self, curdict: dict, id:str= None) -> str:
        """

        Dialog box to create the object name
         - curdict: directory selfmapviewer

        @ The object name is created at this step
        and then passed to the wolfpy interface with suffix
        to clearly distinguish the elements in use.

        FIXME It would have been nice to have a select ID though.
        """
        if id == None:
            dlg = wx.TextEntryDialog(self, _('ID ? (case insensitive)'), _('Choose an identifier'), _('NewObject'))
            dlg.SetValue('')
            if len(curdict) == 0:
                if dlg.ShowModal() == wx.ID_OK:
                    id = dlg.GetValue()

                # elif dlg.ShowModal() == wx.ID_CANCEL:
                #     id = None


            else:
                id = list(curdict.keys())[0]
                while id.lower() in curdict:
                    if dlg.ShowModal() == wx.ID_OK:
                        id = dlg.GetValue()
                    # elif dlg.ShowModal() == wx.ID_CANCEL:
                    #     id = None

        dlg.Destroy()

        if id != None:
            if id.lower() in curdict:
                endid = '_'
                while id.lower() in curdict:
                    id += endid
            new_id =  Constants.NAME_PREFIX.value + id
        else:
            new_id = None

        return new_id

    def __add_river_banks(self, event: pg.EVT_PG_SELECTED):
        id = event.PropertyName
        if id == 'bed_and_banks':
            gui_id = Constants.Name
            self.data[Constants.CROSS_SECTIONS.value] = self.select_mapviewer_data('vector')

class MultigridPage(wx.Panel):
    """Grid of hydrographs.
    It's a plug and play panel on a given page.
    The panel contains a grid which allow the user
    to encode manually or automatically (upload)
    the hydrographs (infiltrations) of a 1D model.

    :param wx: The panel on which the grid is displayed.
    :type wx: `wx.panel`
    """
    def __init__(self, parent):
        """Constructor

        :param parent: the panel, notebook or page containing the grid.
        :type parent: wx.panel
        """
        super().__init__(parent)
        # Sizers
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        # Data
        self.dictionary_hydrographs = {}
        self.selected_cell_name = None
        self.cur_name = None

    def tree_profiles(self,
                      profile_names:list[str],
                      title ='Hydrographs',
                      number_of_rows = 1,
                      number_of_columns = 2):
        """A table containing the daata.

        :param profile_names: List of profile names
        :type profile_names: list[str]
        :param title: The page name that will be
        displayed to the users, defaults to 'Hydrographs'
        :type title: str, optional
        :param number_of_rows: Intializes the numbers
        of rows (ent), defaults to 1
        :type number_of_rows: int, optional
        :param number_of_columns: the number of columns
        in the grid (in case of new variables), defaults to 2
        :type number_of_columns: int, optional
        .. todo:: FIXME add a graph plot between the variables
        and the buttons (to give to the user a visual trend the entries).
        """
        # --- Panel and sizer setups ---
        # _____________________________

        self.sizer_tree_data = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.sizer_tree_data, 1, wx.EXPAND)
        self.sizertreelist = wx.BoxSizer(wx.VERTICAL)
        self.sizer_tree_data.Add(self.sizertreelist, 1, wx.EXPAND)
        self.tree_names = TreeListCtrl(self,
                                             style=wx.dataview.TL_CHECKBOX|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_EDIT_LABELS)
        self.tree_names_column = self.tree_names.AppendColumn(_('Selected cells'))
        self.root_tree_names = self.tree_names.GetRootItem()
        self.tree_names_items = []
        for name in profile_names:
            items = self.tree_names.AppendItem(self.root_tree_names, text= name)
            self.tree_names_items.append(items)

        # --- Hydrographs ---
        #____________________

        self.sizer_grid = wx.BoxSizer(wx.VERTICAL)
        self.sizer_but = wx.BoxSizer(wx.VERTICAL)

        self.sizer_tree_data.Add(self.sizer_grid, 1, wx.EXPAND)
        self.grid_hydrographs = CpGrid(parent = self, id = -1, style= wx.WANTS_CHARS)
        self.grid_hydrographs.CreateGrid(number_of_rows, number_of_columns)
        self.grid_hydrographs.SetColLabelValue(0,_('Time'))
        self.grid_hydrographs.SetColLabelValue(1, ('Discharge'))

        self.button_hydrograph = wx.Button(self, id = wx.ID_ANY, label ='Save changes', name ='save_hydrograph')
        self.button_hydrograph.SetToolTip(_('Save the inputs as an hydrograph.'))
        self.button_hydrograph.Bind(wx.EVT_BUTTON, self.add_hydrographs_to_dict_wx)

        self.button_add_arrow = wx.Button(self, id  = wx.ID_ANY, label=  _('Add row'), name= 'add_row_hydrograph')
        self.button_add_arrow.SetToolTip(_('Add a new row to the grid'))
        self.button_add_arrow.Bind(wx.EVT_BUTTON, self.add_row)

        self.button_loadfromfile = wx.Button(self, id  = wx.ID_ANY, label=  _('Load from file'), name= 'load_hydrograph')
        self.button_loadfromfile.SetToolTip(_('Load the hydrograph from an existing file'))
        self.button_loadfromfile.Bind(wx.EVT_BUTTON, self.load_hydrogaph)

        self.button_delete = wx.Button(self, id = wx.ID_ANY, label ='Delete', name ='delete_hydrograph')
        self.button_delete.SetToolTip(_('Delete the hydrograph (data) displayed.'))
        self.button_delete.Bind(wx.EVT_BUTTON, self.delete_hydrograph_from_dict)

        # Sizer order
        #____________
        self.sizertreelist.Add(self.tree_names, 10, wx.EXPAND)
        self.sizer_grid.Add(self.grid_hydrographs, 1, wx.EXPAND)
        self.sizer_grid.Add(self.sizer_but, 0, wx.EXPAND)

        self.sizer_but.Add(self.button_add_arrow, 0, wx.EXPAND)
        self.sizer_but.Add(self.button_delete, 0, wx.EXPAND)
        self.sizer_but.Add(self.button_loadfromfile,0, wx.EXPAND)
        self.sizer_but.Add(self.button_hydrograph, 0, wx.EXPAND)

        # --- Binding methods ---
        #________________________
        self.Bind(EVT_TREELIST_ITEM_CHECKED, self.block_check_item)
        self.Bind(EVT_TREELIST_SELECTION_CHANGED, self.on_select_item)

        # --- Layout ---
        #_______________
        self.SetAutoLayout(True)
        self.Show()

    def get_tree_list_first_item(self):
        """Set the the first item on the tree list
        as the curname (current name).

        .. Note:: FIXME It still does not work properly.
        .. todo:: FIXME review the whole method.
        """
        self.myitem = self.tree_names.GetFirstItem()
        self.cur_name = self.tree_names.GetItemText(self.myitem)

    def get_name_of_selected_cell(self):
        """Get the name of the selected cell.

        .. Note:: FIXME depreciating.
        """
        item = self.tree_names.GetSelection()
        self.selected_cell_name = self.tree_names.GetItemText(item)

    def add_hydrographs_to_dict(self):
        """Get the users inputs and
        append them to the page's dictionary
        as the hydrograph associated
        to the key of the selected cell.
        """
        # first item selection
        if self.cur_name == None:
            self.get_tree_list_first_item()
        observations = {}
        for i in range(self.grid_hydrographs.GetNumberRows()):
            time = float(self.grid_hydrographs.GetCellValue(i,0))
            discharge = float(self.grid_hydrographs.GetCellValue(i,1))
            observations[time] = discharge
        self.dictionary_hydrographs[self.cur_name] = Hydrograph(observations)
        self.tree_names.CheckItem(self.myitem)

    def add_hydrographs_to_dict_wx(self, event: TreeListEvent):
        """Add the hydrograph to the dictionnary
        through a wx.Event.

        :param event: wx.EVT_BUTTON
        :type event: TreeListEvent
        """
        self.add_hydrographs_to_dict()

    def add_row(self, event: wx.Event):
        """Adds new row in the table of records (grid)

        :param event: wx.EVT_BUTTON
        :type event: wx.Event
        """
        id = event.GetEventObject().GetName()
        if id == 'add_row_hydrograph':
            self.grid_hydrographs.AppendRows()

    def load_hydrogaph(self, event: wx.Event):
        """Load an hydrograph (list of discharges
        evolution through time) from a text file on
        the wolfhece hydrograph format.

        :param event: wx.EVT_BUTTON
        :type event: wx.Event
        """

        id = event.GetEventObject().GetName()
        if id == 'load_hydrograph':
            dlg = wx.FileDialog(self, 'Select the hydrograph file',
                                wildcard='Hydrograph WOLF (*.txt)|*.txt')
            ret = dlg.ShowModal()
            if ret == wx.ID_OK:
                file_path = dlg.GetPath()
            dlg.Destroy()
            hydrograph = Hydrograph(file_path)
            step_number = hydrograph.size
            self.grid_hydrographs.DeleteRows(numRows=self.grid_hydrographs.GetNumberRows())
            self.grid_hydrographs.AppendRows(step_number)
            for i in range(step_number):
                self.grid_hydrographs.SetCellValue(i,0,str(hydrograph.index[i]))
                self.grid_hydrographs.SetCellValue(i,1,str(hydrograph.values[i]))

            self.add_hydrographs_to_dict()
            self.Refresh()

    def delete_hydrograph_from_dict(self, event:wx.Event):
        """Removes the entry saved by the user on the selected cell.

        :param event: wx.EVT_BUTTON
        :type event: wx.Event
        """
        if self.cur_name in self.dictionary_hydrographs:
            deleted_hygrograph = self.dictionary_hydrographs.pop(self.cur_name)
            self.tree_names.UncheckItem(self.myitem)
        number_of_rows = self.grid_hydrographs.GetNumberRows()
        if number_of_rows == 1:
            self.grid_hydrographs.DeleteRows()
        elif number_of_rows > 1:
            self.grid_hydrographs.DeleteRows(numRows=self.grid_hydrographs.GetNumberRows())
        else:
            logging.info('Nothing to delete the number of rows is zero.')

        self.grid_hydrographs.AppendRows()
        self.Refresh()
        logging.info('Hydrograph rows deleted.')

    def block_check_item(self, event:wx.Event):
        """Controls which item is checked or not
        based on the mouse operations (events).

        :param event: EVT_TREELIST_ITEM_CHECKED
        :type event: wx.Event
        """
        if self.tree_names.GetCheckedState(self.myitem) == 1:
            self.tree_names.UncheckItem(self.myitem)
        elif self.tree_names.GetCheckedState(self.myitem) == 0:
            self.tree_names.CheckItem(self.myitem)
        self.Refresh()

    def on_select_item(self, event : TreeListEvent):
        """Return the name of the cell selected by the user after,
        displaying the infiltration informations on the screen.

        :param event: EVT_TREELIST_SELECTION_CHANGED
        :type event: TreeListEvent
        :return: name of the selected item
        :rtype: str
        """
        # Data managements
        self.myitem  = event.GetItem()
        self.cur_name = self.tree_names.GetItemText(self.myitem)
        self.selected_cell_name = self.cur_name

        if self.cur_name in self.dictionary_hydrographs:
            self.load_from_Hydrograph(self.dictionary_hydrographs[self.cur_name])
        else:
            self.grid_hydrographs.DeleteRows(numRows=self.grid_hydrographs.GetNumberRows())
            self.grid_hydrographs.AppendRows() # 1 row

        return self.cur_name

    def load_from_Hydrograph(self, hydrograph: Hydrograph):
        """Fills the grid of infiltration from
        the hydrograph object available from the wolfhece library.

        :param hydrograph: Hydrrograph on the wolfhece format
        :type hydrograph: Hydrograph
        """
        lgth = hydrograph.size

        self.grid_hydrographs.DeleteRows(numRows=self.grid_hydrographs.GetNumberRows())
        self.grid_hydrographs.AppendRows(lgth)

        for i in range(lgth):
            self.grid_hydrographs.SetCellValue(i, 0, str(hydrograph.index[i]))
            self.grid_hydrographs.SetCellValue(i, 1, str(hydrograph.values[i]))

        self.Refresh()

class Boundary_condition_Page(wx.Panel):
    """Grid of Boundary conditions.
    It's a plug and play panel on a given page.
    The panel contains a grid which
    allow the user to encode manually or automatically (upload)
    the boundary conditions of a 1D model.

    :param wx: _description_
    :type wx: _type_

    .. note:: FIXME it would have been nice to have unifom format
    (file) of boundary conditions for all wolf models (1,2 or 3D).
    In that way, one class can be used to manage all operations
    regardless of the dimensions (1,2 or 3D).
    """
    def __init__(self, parent):
        """Constructor

        :param parent: the panel, notebook or page containing the grid.
        :type parent: wx.panel
        """
        super().__init__(parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        # Data
        self.dictionary_boundary_conditions = {}
        self.cur_name = None

    def tree_profiles(self,
                      profile_names:list[str],
                      title ='Boundary conditions',
                      number_of_rows = 1,
                      number_of_columns = 2):
        """A table containing the data.

        :param profile_names: List of profile names.
        :type profile_names: list[str]
        :param title: The page name that will be
        displayed to the users, defaults to 'Boundary conditions'
        :type title: str, optional
        :param number_of_rows: Intializes the numbers
        of rows (ent), defaults to 1
        :type number_of_rows: int, optional
        :param number_of_columns: the number of columns
        in the grid (in case of new variables), defaults to 2
        :type number_of_columns: int, optional
        """
        # --- Panel and sizer setups ---
        #_______________________________
        self.sizer_tree_data = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.sizer_tree_data, 1, wx.EXPAND)
        self.sizertreelist = wx.BoxSizer(wx.VERTICAL)
        self.sizer_tree_data.Add(self.sizertreelist, 1, wx.EXPAND)
        self.tree_names = TreeListCtrl(self,
                                             style=wx.dataview.TL_CHECKBOX|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_EDIT_LABELS)

        self.tree_names_column = self.tree_names.AppendColumn(_('Selected cells'))
        self.root_tree_names = self.tree_names.GetRootItem()
        self.tree_names_items = []
        for name in profile_names:
            items = self.tree_names.AppendItem(self.root_tree_names, text= name)
            self.tree_names_items.append(items)
        # --- Hydrographs ---
        #____________________
        self.sizer_grid = wx.BoxSizer(wx.VERTICAL)
        self.sizer_tree_data.Add(self.sizer_grid, 1, wx.EXPAND)
        self.grid_boundary_conditions = pg.PropertyGridManager(parent = self,
                                                               style = pg.PG_BOLD_MODIFIED|
                                                                pg.PG_SPLITTER_AUTO_CENTER|
                                                                pg.PGMAN_DEFAULT_STYLE
                                                                )
        # --- Displayed name ---
        #_______________________
        self.boundary_conditions = pg.PropertyCategory(Titles.GUI_GRID_BOUNDARY_CONDITIONS.value)
        self.grid_boundary_conditions.Append(self.boundary_conditions)
        # --- Data ---
        #_____________
        self.cell_side_boundary_conditions = pg.EnumProperty(label = 'Cell side',
                                         name = 'cell_side',
                                         labels = [Titles.BC_UPSTREAM.value,Titles.BC_DOWNSTREAM.value],
                                         values = [1,2],
                                         value = 2
                                        )
        self.type_boundary_conditions = pg.EnumProperty(label = 'Type',
                                         name = 'type_BC',
                                         labels = [Titles.BC_WATER_DEPTH_1.value,
                                                   Titles.BC_WATER_LEVEL_2.value,
                                                   Titles.BC_DISCHARGE_3.value,
                                                   Titles.BC_FROUDE_4.value,
                                                   Titles.BC_FREE_5.value,
                                                   Titles.BC_IMPERVIOUS_99.value,
                                                   Titles.BC_JUNCTION_100.value,
                                                   Titles.BC_MOBILE_DAM_127.value,],
                                         values = [1,2,3,4,5,6,7,8],
                                         value = 1,
                                        )
        self.value_boundary_conditions = pg.FloatProperty(label = Titles.BC_VALUE.value,
                                                         name ='value_boundary_conditions',
                                                         value= 0.)
        self.grid_boundary_conditions.Append(self.cell_side_boundary_conditions)
        self.grid_boundary_conditions.Append(self.type_boundary_conditions)
        self.grid_boundary_conditions.Append(self.value_boundary_conditions)

        # --- Buttons ----
        #_________________
        self.button_save_BC = wx.Button(self, id = wx.ID_ANY, label ='Save changes', name ='save_boundary_condtions')
        self.button_save_BC.SetToolTip(_('Save the inputs as a boundary conditions.'))
        self.button_save_BC.Bind(wx.EVT_BUTTON, self.add_boundary_condition_to_dict_wx)

        self.button_delete = wx.Button(self, id = wx.ID_ANY, label ='Delete', name ='delete_boundary_conditions')
        self.button_delete.SetToolTip(_('Delete the cells as a boundary conditions.'))
        self.button_delete.Bind(wx.EVT_BUTTON, self.delete_boundary_condition_from_dict)

        # --- Sizer order ---
        #____________________

        self.sizertreelist.Add(self.tree_names, 1, wx.EXPAND)
        self.sizer_grid.Add(self.grid_boundary_conditions, 10, wx.EXPAND)
        self.sizer_grid.Add(self.button_delete, 1, wx.EXPAND)
        self.sizer_grid.Add(self.button_save_BC, 1, wx.EXPAND)

        # --- Binding events ---
        #_______________________
        # self.Bind(EVT_TREELIST_ITEM_ACTIVATED, self.oncheckitem) #FIXME works as well alternative
        self.Bind(EVT_TREELIST_ITEM_CHECKED, self.block_check_item)
        self.Bind(EVT_TREELIST_SELECTION_CHANGED, self.oncheckitem)

        # --- Display ---
        #________________
        self.Show()

    def get_tree_list_first_item(self):
        """Set the the first item on the tree list
        as the curname (current name).

        .. Note:: FIXME It still does not work properly.
        .. todo:: FIXME review the whole method.
        """
        self.myitem = self.tree_names.GetFirstItem()
        self.cur_name = self.tree_names.GetItemText(self.myitem)

    def add_boundary_conditions_to_dict(self):
        """Get the users inputs and
        append them to the page's dictionary.
        In the dictionnary, the boundary conditions
        are associated to the key of the selected cells.
        """
        if self.cur_name == None:
            # first item selection
            self.get_tree_list_first_item()
        observations = {}
        cell_side = self.cell_side_boundary_conditions.GetValue()
        type_bc = self.type_boundary_conditions.GetValue()
        value_bc = float(self.value_boundary_conditions.GetValue())

        self.dictionary_boundary_conditions[self.cur_name] =(self.convert_cell_side_value(cell_side),
                                                             self.convert_type_boundary_condition(type_bc),
                                                             value_bc)
        self.tree_names.CheckItem(self.myitem)

    def convert_cell_side_value(self, value:int)-> str:
        """Return the location of the boundary condition
        on a selected cell (upstream or downstream).

        :param value: 1 for upstream or 2 for downstream
        :type value: int
        :return: `upstream `or `downstream`
        :rtype: str
        """
        if value == 1:
            return Titles.BC_UPSTREAM.value
        elif value == 2:
            return Titles.BC_DOWNSTREAM.value

    def convert_type_boundary_condition(self, value:int) -> str:
        """Return the type of boundary condition
         corresponding to the encoded integer.

        :param value: _description_
        :type value: int
        :return: _description_
        :rtype: str
        """
        if value == 1:
            return Titles.BC_WATER_DEPTH_1.value
        elif value == 2:
            return Titles.BC_WATER_LEVEL_2.value
        elif value == 3:
            return Titles.BC_DISCHARGE_3.value
        elif value == 4:
            return Titles.BC_FROUDE_4.value
        elif value == 5:
            return Titles.BC_FREE_5.value
        elif value == 6:
            return Titles.BC_IMPERVIOUS_99.value
        elif value == 7:
            return Titles.BC_JUNCTION_100.value
        elif value == 8:
            return Titles.BC_MOBILE_DAM_127.value

    def add_boundary_condition_to_dict_wx(self, event: TreeListEvent):
        """Add the boundary condition to the dictionnary
        through a wx.Event.

        :param event: wx.EVT_BUTTON
        :type event: TreeListEvent
        """
        self.add_boundary_conditions_to_dict()

    def delete_boundary_condition_from_dict(self, event:wx.Event):
        """Removes the entry saved by the user on specified cell.

        :param event: wx.EVT_BUTTON
        :type event: wx.Event
        """
        if self.cur_name in self.dictionary_boundary_conditions:
            deleted_boundary_condition = self.dictionary_boundary_conditions.pop(self.cur_name)
            self.tree_names.UncheckItem(self.myitem)
            self.reset_condition()
            logging.info('Boundary condition deleted.')

        else:
            logging.info('Boundary condition\nNothing to delete.')

        self.Refresh()

    def block_check_item(self, event:wx.Event):
        """Controls which item is checked or not
        based on the mouse operations (events).

        :param event: EVT_TREELIST_ITEM_CHECKED
        :type event: wx.Event
        """
        if self.tree_names.GetCheckedState(self.myitem) == 1:
            self.tree_names.UncheckItem(self.myitem)
        elif self.tree_names.GetCheckedState(self.myitem) == 0:
            self.tree_names.CheckItem(self.myitem)

        self.Refresh()

    def oncheckitem(self, event : TreeListEvent):
        """Return the name of the cell selected by the user after,
        displaying the informations regarding the boundary
        conditions in the grid.

        :param event: EVT_TREELIST_SELECTION_CHANGED
        :type event: TreeListEvent
        :return: name of the selected item
        :rtype: str
        """
        # Data managemgemens
        self.myitem  = event.GetItem()
        self.cur_name = self.tree_names.GetItemText(self.myitem)
        if self.cur_name in self.dictionary_boundary_conditions:
            self.load_from_boundary_conditions(self.dictionary_boundary_conditions[self.cur_name])
        else:
            self.reset_condition()
        return self.cur_name

    def load_from_boundary_conditions(self, condition: tuple[str, str, float]):
        """Fills the grid of boundary conditions from a tuple
        containing:
            - condition[0] : cell side,
            - condition[1]: type of boundary condition,
            - condition[2]: Value of boundary condition.

        :param condition: information about the boundary conditon.
        :type condition: tuple[str, str, float]

        .. todo:: - FIXME implement a simple test for protection.
        """
        assert isinstance(condition[0],(str)), "Boundary condition: Wrong type cell side."
        assert isinstance(condition[1], (str)), "Boundary condition: Wrong type of boundary condition."
        assert isinstance(condition[2],(float,int)), "Boundary condition: value not numeric."
        self.cell_side_boundary_conditions.SetValueFromString(condition[0])
        self.type_boundary_conditions.SetValueFromString(condition[1])
        self.value_boundary_conditions.SetValueFromString(str(condition[2]))
        self.Refresh()

    def reset_condition(self):
        """Reset the information displayed in the grid to default values.
        """
        self.cell_side_boundary_conditions.SetValueFromString(Titles.BC_DOWNSTREAM.value)
        self.type_boundary_conditions.SetValueFromInt(0)
        self.value_boundary_conditions.SetValueFromInt(0)
