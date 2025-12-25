"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from pathlib import Path
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import (
    FigureCanvasWxAgg as FigureCanvas,
    NavigationToolbar2WxAgg as NavigationToolbar,
)

import shutil
import ctypes as ct


import wolf_libs
from .PostProcessHydrology import PostProcessHydrology
from .Catchment import *
from .Comparison import *
from .read import *
from ..wolf_array import *
from ..PyGui import GenMapManager,HydrologyModel
from . import cst_exchanges as cste
from . import constant as cst
from . import Models_characteristics as mc
from . import Internal_variables as iv
from ..PyTranslate import _
import traceback
import gc


# %% Constants
DLL_FILE = "WolfDll.dll"                # Name of the release DLL
DLL_FILE_DEBUG = "WolfDll_debug.dll"    # Name of the debug DLL
DLL_FILE_TEST = "WolfDll_test.dll"      # Name of the test DLL (to deactivate random numbers generation)


# %% Classes
class CaseOpti(GenMapManager):

    launcherDir:str
    # nbParams:int
    # optiFactor:ct.c_double

    launcherParam:Wolf_Param
    refCatchment:Catchment
    idToolItem:int
    mydro:HydrologyModel
    idMenuItem:int

    # FIXME : this variable is just there before the seperation between the object optimisation and GUI optimisation
    wx_exists:bool

    # callBack_proc:dict
    # callBack_ptr:dict

    def __init__(self, *args, **kw):
        self.wx_exists = wx.App.Get() is not None # test if wx App is running
        if self.wx_exists:
            super().__init__(*args, **kw)
        # super().__init__(splash=splash, *args, **kw)

        self.launcherDir = ""

    def read_param(self, dir, copyDefault=False, callback=None, workingDir:Path = ""):

        self.launcherDir = Path(dir)
        workingDir = Path(workingDir)

        if not os.path.exists(self.launcherDir):
            try:
                os.mkdir(self.launcherDir)
                shutil.copyfile(workingDir / "launcher.param.default", self.launcherDir / "launcher.param")
                shutil.copyfile(workingDir / "launcher.param.default", self.launcherDir / "launcher.param.default")
            except OSError:
                print ("Creation of the directory %s failed" % self.launcherDir)
            else:
                print ("Successfully created the directory %s" % self.launcherDir)

        if copyDefault:
            shutil.copyfile(workingDir / "launcher.param.default", self.launcherDir / "launcher.param")
            shutil.copyfile(workingDir / "launcher.param.default", self.launcherDir / "launcher.param.default")

        self.launcherParam = Wolf_Param(to_read=True, filename=self.launcherDir / "launcher.param",title="launcher", toShow=False)


    def show_launcherParam(self, event):

        self.launcherParam.Show()
        pass


    def show_mydro(self, event):
        self.mydro.Show()
        pass




class Optimisation(wx.Frame):

    workingDir:str
    # launcherDir:list
    myParams:dict
    myParamsPy:dict
    curParams_vec_F:np.ndarray
    nbParams:int
    optiFactor_F:ct.c_double
    bestFactor:float

    comparHowParam:Wolf_Param
    # launcherParam:Wolf_Param
    saParam:Wolf_Param
    optiParam:Wolf_Param

    # refCatchment:Catchment
    dllFortran:ct.CDLL
    pathDll:str

    callBack_proc:dict
    callBack_ptr:dict

    myCases:list[CaseOpti]

    myStations:list[str]
    compareFilesDict:dict[str, str]
    compareSubBasins:dict[str, SubBasin]
    all_intervals:list[tuple[datetime.datetime, datetime.datetime]]

    # FIXME : this variable is just there before the seperation between the object optimisation and GUI optimisation
    wx_exists:bool

    def __init__(self, parent=None, title="", w=500, h=500, init_wx=True, debugDLL=False, for_test:bool=False):

        self.wx_exists = wx.App.Get() is not None # test if wx App is running

        if self.wx_exists:
            super(Optimisation, self).__init__(parent, title=title, size=(w,h))

        self.debugDLL = debugDLL

        self.workingDir = ""
        # self.launcherDir = []
        self.myParams = {}
        self.myParamsPy = {}
        self.nbParams = 0

        # point to the wolf_libs package directory
        self.pathDll = wolf_libs.__path__[0]

        self.callBack_proc = {}
        self.callBack_ptr = {}

        self.myCases = []

        self.myStations = []
        self.compareFilesDict = {}
        self.all_intervals = None

        self.curParams_vec_F = None

        if self.debugDLL:
            self.load_dll(self.pathDll, DLL_FILE_DEBUG)
        else:
            if for_test:
                self.load_dll(self.pathDll, DLL_FILE_TEST)
            else:
                self.load_dll(self.pathDll, DLL_FILE)

        # FIXME
        if self.wx_exists:
            self.initGUI()


    def initGUI(self):

        menuBar = wx.MenuBar()

        # Creation of the Menu
        fileMenu = wx.Menu()
        newClick = fileMenu.Append(wx.ID_ANY, 'New')
        self.Bind(wx.EVT_MENU, self.new, newClick)
        openClick = fileMenu.Append(wx.ID_ANY, 'Open')
        self.Bind(wx.EVT_MENU, self.load, openClick)
        resetClick = fileMenu.Append(wx.ID_ANY, 'Reset')
        self.Bind(wx.EVT_MENU, self.reset, resetClick)
        destroyClick = fileMenu.Append(wx.ID_ANY, 'Destroy')
        self.Bind(wx.EVT_MENU, self.destroyOpti, destroyClick)

        fileMenu.AppendSeparator()

        quitClick = wx.MenuItem(fileMenu, wx.ID_EXIT, 'Quit\tCtrl+W')
        fileMenu.Append(quitClick)
        # quitClick = wx.MenuItem(fileMenu, wx.ID_EXIT, 'Quit\tCtrl+W')

        # Creation of the param file Menu
        paramMenu = wx.Menu()
        testOptiClick = paramMenu.Append(wx.ID_ANY, 'test_opti.param')
        self.Bind(wx.EVT_MENU, self.show_optiParam, testOptiClick)
        compareHowClick = paramMenu.Append(wx.ID_ANY, 'compare.how.param')
        self.Bind(wx.EVT_MENU, self.show_comparHowParam, compareHowClick)
        saClick = paramMenu.Append(wx.ID_ANY, 'sa.param')
        self.Bind(wx.EVT_MENU, self.show_saParam, saClick)
        paramMenu.AppendSeparator()
        # add Cases

        # Creation of the Tools Menu
        toolMenu = wx.Menu()
        applyClick = toolMenu.Append(wx.ID_ANY, 'Apply best parameters')
        self.Bind(wx.EVT_MENU, self.apply_optim, applyClick)
        visualiseClick = toolMenu.Append(wx.ID_ANY, 'Visualise best parameters : lumped')
        self.Bind(wx.EVT_MENU, self.plot_optim_sub, visualiseClick)
        visualiseClick_SD = toolMenu.Append(wx.ID_ANY, 'Visualise best parameters : Semi-dist')
        self.Bind(wx.EVT_MENU, self.plot_optim_jct, visualiseClick_SD)
        getRsltClick = toolMenu.Append(wx.ID_ANY, 'Get all outlets')
        self.Bind(wx.EVT_MENU, self.get_all_outlets, getRsltClick)
        getInletsClick = toolMenu.Append(wx.ID_ANY, 'Get all inlets')
        self.Bind(wx.EVT_MENU, self.write_all_inlets, getInletsClick)
        landuseClick = toolMenu.Append(wx.ID_ANY, 'Plot all landuses')
        self.Bind(wx.EVT_MENU, self.plot_all_landuses, landuseClick)
        landuseHydroClick = toolMenu.Append(wx.ID_ANY, 'Plot all hydro landuses')
        self.Bind(wx.EVT_MENU, self.plot_all_landuses_hydro, landuseHydroClick)
        internValClick = toolMenu.Append(wx.ID_ANY, 'Extract internal variables')
        self.Bind(wx.EVT_MENU, self.extract_internal_variables, internValClick)
        plotParetoClick = toolMenu.Append(wx.ID_ANY, 'Plot Nash vs Qexcess')
        self.Bind(wx.EVT_MENU, self.plot_Nash_vs_Qexcess, plotParetoClick)
        testEquiFinClick = toolMenu.Append(wx.ID_ANY, 'Test equifinality with Nash')
        self.Bind(wx.EVT_MENU, self.test_equifinality_with_Nash, testEquiFinClick)
        plotEquiFinClick = toolMenu.Append(wx.ID_ANY, 'Plot equifinality with Nash')
        self.Bind(wx.EVT_MENU, self.plot_equifinality, plotEquiFinClick)
        testEquiFinClick = toolMenu.Append(wx.ID_ANY, 'Models analysis with Nash')
        self.Bind(wx.EVT_MENU, self.launch_models_properties_with_Nash, testEquiFinClick)
        plotEquiFinClick = toolMenu.Append(wx.ID_ANY, 'Plot analysis with Nash')
        self.Bind(wx.EVT_MENU, self.plot_model_analysis, plotEquiFinClick)


        # Creation of the Lauch Menu
        launchMenu = wx.Menu()
        normalLaunchClick = launchMenu.Append(wx.ID_ANY, '1 Basin')
        self.Bind(wx.EVT_MENU, self.launch_lumped_optimisation, normalLaunchClick)
        SDLaunch = launchMenu.Append(wx.ID_ANY, 'Semi-Distributed')
        self.Bind(wx.EVT_MENU, self.launch_semiDistributed_optimisation, SDLaunch)
        SDCompute = launchMenu.Append(wx.ID_ANY, 'Semi-Distributed apply')
        self.Bind(wx.EVT_MENU, self.generate_semiDist_optim_simul, SDCompute)

        # Creation of the Hydro Menu
        hydroSimul = wx.Menu()
        computeHydroClick = hydroSimul.Append(wx.ID_ANY, 'compute')
        self.Bind(wx.EVT_MENU, self.compute0_distributed_hydro_model, computeHydroClick)

        menuBar.Append(fileMenu, 'File')
        menuBar.Append(paramMenu, 'Param files')
        menuBar.Append(toolMenu, 'Tools')
        menuBar.Append(launchMenu, 'Launch')
        menuBar.Append(hydroSimul, 'Hydro')

        # Debug menu
        if(self.debugDLL):
            toolDebug = wx.Menu()
            DebugCompute = toolDebug.Append(wx.ID_ANY, 'Debug all params tests')
            self.Bind(wx.EVT_MENU, self.generate_semiDist_debug_simul, DebugCompute)
            menuBar.Append(toolDebug, 'Debug')

        self.SetMenuBar(menuBar)

        self.SetSize((1700, 900))
        self.SetTitle("Optimisation")
        self.Centre()

        # All Menu bars will be unavailable except the File one
        myExceptions = ['File', 'Hydro']
        self.disable_all_MenuBar(exceptions=myExceptions)

    def quitGUI(self, event):
        self.Close()


    def new(self, event):
        """ Create a new optimisation directory and files. """

        launcherDir = "simul_1"

        # Selection of the working directory
        idir=wx.DirDialog(None,"Choose an optimisation directory")
        if idir.ShowModal() == wx.ID_CANCEL:
            logging.info("Optimisation cancelled!")
            idir.Destroy()
            return

        self.workingDir = Path(idir.GetPath())
        launcherDir = self.workingDir / launcherDir
        idir.Destroy()

        # Launch the Fortran code a first time to generate the default files
        self.default_files()

        # Copy and reading of the optiParam file
        shutil.copyfile(self.workingDir / "test_opti.param.default", self.workingDir / "test_opti.param")
        shutil.copyfile(self.workingDir / "sa.param.default", self.workingDir / "sa.param")
        shutil.copyfile(self.workingDir / "compare.how.param.default", self.workingDir / "compare.how.param")

        if not launcherDir.exists():
            try:
                launcherDir.mkdir(parents=True, exist_ok=True)
            except OSError:
                print ("Creation of the directory %s failed" % launcherDir)
            else:
                print ("Successfully created the directory %s" % launcherDir)
        shutil.copyfile(self.workingDir / "launcher.param.default", launcherDir /"launcher.param")
        shutil.copyfile(self.workingDir / "launcher.param.default", launcherDir / "launcher.param.default")


        # Read the main opti file
        self.optiParam = Wolf_Param(to_read=True, filename= self.workingDir / "test_opti.param", title = "test_opti", toShow = False)
        # # Update all the paths and read all simul
        # self.init_dir_in_params()
        # Read all the param files and init the Case objects and then read the param files associated
        newCase = CaseOpti()
        newCase.read_param(launcherDir, copyDefault=True, callback=self.update_parameters_launcher, workingDir = self.workingDir)
        self.myCases.append(newCase)

        # Update all the paths and read all simul
        self.init_dir_in_params()

        self.comparHowParam = Wolf_Param(to_read=True,filename= self.workingDir / "compare.how.param",title="compare.how",toShow=False)
        self.saParam = Wolf_Param(to_read=True,filename= self.workingDir / "sa.param", title="sa",toShow=False)
        self.saParam._callback = self.update_parameters_SA
        # initialise all param files according to the reference characteristics
        self.init_with_reference()
        self.init_myParams()
        self.init_with_default_lumped(replace=True)

        # Case Tool added
        try:
            newId = wx.Window.NewControlId()
            iMenu = self.MenuBar.FindMenu('Param files')
            paramMenu = self.MenuBar.Menus[iMenu][0]
            curName = 'Case '+str(1)
            caseMenu = wx.Menu()
            paramCaseFile = caseMenu.Append(wx.ID_ANY, 'launcher.param')
            self.Bind(wx.EVT_MENU, newCase.show_launcherParam, paramCaseFile)
            guiHydroCase = caseMenu.Append(wx.ID_ANY, 'GUI Hydro')
            curDir = newCase.launcherParam.get_param("Calculs","Répertoire simulation de référence")
            isOk, curDir = check_path(curDir, prefix=self.workingDir, applyCWD=True)
            if isOk<0:
                logging.error("ERROR : in path of launcherDir")
            newCase.mydro = HydrologyModel(directory=curDir)
            newCase.mydro.Hide()
            self.Bind(wx.EVT_MENU, newCase.show_mydro, guiHydroCase)
            curCase = paramMenu.Append(newId, curName, caseMenu)
        except:
            logging.error("ERROR: launch again the app and apply 'load' files.")



        # Let all the menu bars be available in GUI
        self.enable_MenuBar("Param files")
        self.enable_MenuBar("Launch")


    def load(self, event, workingDir:str="", fileName:str=""):

        # Selection of the main
        if workingDir=="":
            idir=wx.FileDialog(None,"Choose an optimatimisation file",wildcard='Fichiers param (*.param)|*.param')
            if idir.ShowModal() == wx.ID_CANCEL:
                logging.info(_("Post process cancelled!"))
                idir.Destroy()
                return
                # sys.exit()
            fileOpti = idir.GetPath()
            readDir = idir.GetDirectory() + "\\"
            idir.Destroy()
        else:
            readDir = workingDir
            if fileName=="": fileName="test_opti.param"
            fileOpti = os.path.join(readDir, fileName)


        # Read the main opti file
        self.optiParam = Wolf_Param(to_read=True, filename=fileOpti, title="test_opti",toShow=False)
        initDir = self.optiParam.get_param("Optimizer","dir")
        isOk, initDir = check_path(initDir, prefix=readDir, applyCWD=True)

        if initDir is None:
            logging.error("ERROR: in path of initDir")
            return
        #
        if os.path.samefile(readDir, initDir):
            self.workingDir = initDir
        else:
            self.workingDir = readDir
            self.optiParam.change_param("Optimizer","dir", self.workingDir)
        nbcases = int(self.optiParam.get_param("Cases","nb"))
        if nbcases>1:
            wx.MessageBox(_('So far, there can only have 1 case! This will change soon.'), _('Error'), wx.OK|wx.ICON_ERROR)
            return
        self.launcherDir = []
        for i in range(nbcases):
            newCase = CaseOpti()
            launcherDir = self.optiParam.get_param("Cases","dir_"+str(i+1))
            isOk, launcherDir = check_path(launcherDir, prefix=self.workingDir, applyCWD=True)
            if isOk<0:
                logging.error("ERROR : in path of launcherDir")
            newCase.read_param(launcherDir, copyDefault=False, callback=self.update_parameters_launcher)
            # FIXME TO CHANGE when seperation with the GUI
            if self.wx_exists:
                newId = wx.Window.NewControlId()
                iMenu = self.MenuBar.FindMenu('Param files')
                paramMenu = self.MenuBar.Menus[iMenu][0]
                curName = 'Case '+str(i+1)
                iItem = self.MenuBar.FindMenuItem('Param files', curName)
                if(iItem==wx.NOT_FOUND):
                    caseMenu = wx.Menu()
                    paramCaseFile = caseMenu.Append(wx.ID_ANY, 'launcher.param')
                    self.Bind(wx.EVT_MENU, newCase.show_launcherParam, paramCaseFile)
                    guiHydroCase = caseMenu.Append(wx.ID_ANY, 'GUI Hydro')
                    refDir = newCase.launcherParam.get_param("Calculs","Répertoire simulation de référence")
                    isOk, refDir = check_path(refDir, prefix=launcherDir, applyCWD=True)
                    if isOk<0:
                        logging.error("ERROR : in path of launcherDir")
                    newCase.mydro = HydrologyModel(directory=refDir)
                    newCase.mydro.Hide()
                    self.Bind(wx.EVT_MENU, newCase.show_mydro, guiHydroCase)
                    curCase = paramMenu.Append(newId, curName, caseMenu)
                else:
                    logging.Warning(_("WARNING : this scenario was not implemented yet. This might induce an error!"))
                    # iItem =
                    curCase = paramMenu.Replace(iItem)
                self.Bind(wx.EVT_MENU, newCase.show_launcherParam, curCase)
                newCase.idMenuItem = newId
            else:
                refDir = newCase.launcherParam.get_param("Calculs","Répertoire simulation de référence")
                isOk, refDir = check_path(refDir, prefix=launcherDir, applyCWD=True)
                newCase.mydro = HydrologyModel(directory=refDir)
            self.myCases.append(newCase)


        self.comparHowParam = Wolf_Param(to_read=True,filename=os.path.join(self.workingDir,"compare.how.param"),title="compare.how",toShow=False)
        self.saParam = Wolf_Param(to_read=True,filename=os.path.join(self.workingDir,"sa.param"), title="sa",toShow=False)
        for i in range(nbcases):
            self.get_reference(idLauncher=i)
            self.init_myParams(idLauncher=i)

        # Check if the optimisation intervals are within the simulation interval
        self.checkIntervals()

        #
        self.init_with_default_lumped()

        # Let all the menu bars be available in GUI
        if self.wx_exists:
            self.enable_MenuBar("Param files")
            self.enable_MenuBar("Launch")
            self.enable_MenuBar("Tools")
            if self.debugDLL:
                self.enable_MenuBar("Debug")


    def apply_optim(self, event, idLauncher:int=0,
                    replace_only_if_better:bool=False, optim_params:np.ndarray=None):
        """
        Apply optimal parameters based on the results file of the optimisation : ".rpt".

        Args:
            event: The event from the GUI.
            idLauncher (optional: int(0)): The ID of the launcher.
            replace_only_if_better (optional: bool(False) by default): A boolean indicating whether to replace the current parameters if the new ones are better.

        Returns:
            If replace_only_if_better is False, returns the best parameters found.
            If replace_only_if_better is True and the new parameters are better, returns the best parameters found.
            Otherwise, returns None.
        """
        # Get the best parameters
        if optim_params is None:
            bestParams:np.array = self.collect_optim()
        else:
            # FIXME : gneralise the -1 for the test for any number of objective function
            assert self.nbParams==len(optim_params)-1, "ERROR : the number of parameters to appy are the ones expected!"
            bestParams:np.array = optim_params

        test_best = bestParams[-1] # FIXME : gneralise the -1 for the test for any number of objective function
        if not replace_only_if_better:
            self.apply_optim_2_params(bestParams[:-1], idLauncher=idLauncher)
            self.bestFactor = test_best
            return bestParams
        elif test_best>self.bestFactor:
            self.apply_optim_2_params(bestParams[:-1], idLauncher=idLauncher)
            self.bestFactor = bestParams[-1]
            return bestParams
        else:
            return None



    # Initialisation of the Optimizer from Fortran
    def init_lumped_hydro(self, event):

        self.init_optimizer()



    def init_with_default_lumped(self, replace:bool=False):
        # if replace:
        #     r = wx.ID_NO
        # else:
        #     r = wx.MessageDialog(None, "Do you want to keep your own parameters files?", "Warning", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()

        # if r != wx.ID_YES:

        #     self.optiParam.change_param("Cases","nb", 1)
        #     self.optiParam.change_param("Optimizer","tuning_method",2)
        #     self.optiParam.change_param("Optimizer","max_nb_run",30000)
        #     self.optiParam.change_param("Comparison factors","nb",1)
        #     self.optiParam.change_param("Comparison factors","which_factor_1",1)

        #     self.comparHowParam.change_param("Comparison global characteristics","nb",1)
        #     self.comparHowParam.change_param("Comparison 1","type",1)
        #     self.comparHowParam.change_param("Comparison 1","nb factors",1)
        #     self.comparHowParam.change_param("Comparison 1","nb intervals",1)
        #     self.comparHowParam.change_param("Comparison 1","factor 1",1)

        #     self.saParam.change_param("Optimisation parameters","eps",1.0E-03)
        #     self.saParam.change_param("Optimisation parameters","rt",0.1)
        #     self.saParam.change_param("Optimisation parameters","ns",10)
        #     self.saParam.change_param("Optimisation parameters","nt",10)
        #     self.saParam.change_param("Optimisation parameters","neps",3)
        #     self.saParam.change_param("Optimisation parameters","Nombre iteration max",500)
        #     self.saParam.change_param("Optimisation parameters","Initial Temperature",20)
        #     self.saParam.callback = self.update_parameters_SA

        #     self.myCases[0].launcherParam.change_param("Calculs","Type de modèle",4)
        #     self.myCases[0].launcherParam.change_param("Calculs","Nombre de simulations parallèles",1)
        #     self.myCases[0].launcherParam.change_param("Récupération des résultats","Nombre de bords de convergence",0)
        #     self.myCases[0].launcherParam.change_param("Récupération des résultats","Nombre de noeuds de convergence",1)
        #     self.myCases[0].launcherParam.change_param("Récupération des résultats","extract_exchange_zone",0)
        #     self.myCases[0].launcherParam.change_param("Récupération des résultats","type_of_geom",2)
        #     self.myCases[0].launcherParam.change_param("Récupération des résultats","type_of_exchange",15)
        #     self.myCases[0].launcherParam.change_param("Récupération des résultats","type_of_data",13)

        #     # if(self.refCatchment.myModel==cst.tom_2layers_linIF):
        #     #     self.init_lumped_model()

        #     self.init_lumped_model()

        #     self.init_myParams()

        #     self.optiParam.SavetoFile(None)
        #     self.optiParam.Reload(None)

        #     self.comparHowParam.SavetoFile(None)
        #     self.comparHowParam.Reload(None)

        #     self.saParam.SavetoFile(None)
        #     self.saParam.Reload(None)

        #     self.myCases[0].launcherParam.SavetoFile(None)
        #     self.myCases[0].launcherParam.Reload(None)
        return


    # def init_2layers_linIF(self):
    def init_lumped_model(self):

        curCase = self.myCases[0]

        self.saParam.change_param("Initial parameters", "Read initial parameters?", 0)

        # Retrieve the dictionnary with the properties of all models (parameters, files, etc)
        myModel = curCase.refCatchment.myModel
        nbParams = cste.modelParamsDict[myModel]["Nb"]
        myModelDict = cste.modelParamsDict[myModel]["Parameters"]

        prefix1 = "param_"
        i=1
        for element in myModelDict:
            paramName = prefix1 + str(i)
            curCase.launcherParam.add_param(groupname=paramName, name="type_of_data", value=element, type="int")
            i+=1

        curCase.launcherParam.change_param("Paramètres à varier","Nombre de paramètres à varier",nbParams)
        self.nbParams = nbParams

        prefix2 = "Parameter "
        for i in range(1,self.nbParams+1):
            paramName = prefix2 + str(i)
            self.saParam.add_param(groupname="Lowest values", name=paramName, value=0.0)
            # if not paramName in self.saParam.myparams["Lowest values"]:
            #     self.saParam.myparams["Lowest values"][paramName] = {}
            #     self.saParam.myparams["Lowest values"][paramName]["value"] = 0.0
            self.saParam.add_param(groupname="Highest values", name=paramName, value=0.0)
            # if not paramName in self.saParam.myparams["Highest values"]:
            #     self.saParam.myparams["Highest values"][paramName] = {}
            #     self.saParam.myparams["Highest values"][paramName]["value"] = 0.0
            if not paramName in self.saParam.myparams["Steps"]:
                self.saParam.myparams["Steps"][paramName] = {}
                self.saParam.myparams["Steps"][paramName]["value"] = 0.0
            self.saParam.add_param(groupname="Initial parameters", name=paramName, value=0.0)
            # if not paramName in self.saParam.myparams["Initial parameters"]:
            #     self.saParam.myparams["Initial parameters"][paramName] = {}
            #     self.saParam.myparams["Initial parameters"][paramName]["value"] = 0.0
            paramName = prefix1 + str(i)
            curCase.launcherParam.add_param(groupname=paramName, name="geom_filename", value="my_geom.txt")
            curCase.launcherParam.add_param(groupname=paramName, name="type_of_geom", value=0)
            curCase.launcherParam.add_param(groupname=paramName, name="type_of_exchange", value=-3)
            # self.myCases[0].launcherParam.myparams[paramName]["geom_filename"] = {}
            # self.myCases[0].launcherParam.myparams[paramName]["geom_filename"]["value"] = "my_geom.txt"
            # self.myCases[0].launcherParam.myparams[paramName]["type_of_geom"] = {}
            # self.myCases[0].launcherParam.myparams[paramName]["type_of_geom"]["value"] = 0
            # self.myCases[0].launcherParam.myparams[paramName]["type_of_exchange"] = {}
            # self.myCases[0].launcherParam.myparams[paramName]["type_of_exchange"]["value"] = -3


    def init_myParams(self, idLauncher=0):
        curCatch:Catchment
        self.nbParams = int(self.myCases[idLauncher].launcherParam.get_param("Paramètres à varier", "Nombre de paramètres à varier"))
        curCatch = self.myCases[idLauncher].refCatchment
        launcher_param = self.myCases[idLauncher].launcherParam

        for i in range(1,self.nbParams+1):
            curParam = "param_" + str(i)
            self.myParams[i] = {}
            self.myParams[i]["type"] = int(self.myCases[idLauncher].launcherParam.get_param(curParam, "type_of_data"))
            self.myParams[i]["value"] = 0.0
            # Check cst_echange.py for the values (only consider the param of the Froude model)
            if self.myParams[i]["type"]>100 and self.myParams[i]["type"]<106:
                self.myParams[i]["update"] = curCatch.update_timeDelays_from_F
                sorted_id = int(launcher_param.get_param(curParam, "Subbasin id", default_value=0))
                if sorted_id == 0:
                    self.myParams[i]["junction_name"] = curCatch.junctionOut
                else:
                    cur_id = list(curCatch.dictIdConversion.keys())[list(curCatch.dictIdConversion.values()).index(sorted_id)]
                    self.myParams[i]["junction_name"] = curCatch.subBasinDict[cur_id].name

            else:
                self.myParams[i]["update"] = self.update_nothing
                self.myParams[i]["junction_name"] = curCatch.junctionOut


            typeParam = int(self.myParams[i]["type"])
            # If it is a Python parameter to optim
            if(typeParam<0):
                self.myParamsPy[i] = self.myParams[i]
                if(typeParam==cste.exchange_parameters_py_timeDelay):
                    self.myParamsPy[i]["update"] = self.myCases[idLauncher].refCatchment.update_timeDelay
                    self.myParamsPy[i]["junction_name"] = self.myCases[idLauncher].launcherParam.get_param(curParam, "junction_name")


    def collect_optim(self, fileName=""):

        isOk,fileName = check_path(fileName, self.workingDir)
        if fileName=="":
            nameTMP = self.optiParam.get_param("Optimizer","fname")
        else:
            isOk,nameTMP = check_path(fileName, self.workingDir)

        optimFileTxt = os.path.join(self.workingDir, nameTMP+".rpt")
        optimFileBin = os.path.join(self.workingDir, nameTMP+".rpt.dat")

        isOk, optimFileBin = check_path(optimFileBin)
        if isOk>0:
            optimFile = optimFileBin
            allParams = read_bin(self.workingDir, nameTMP+".rpt.dat", uniform_format=8)
            matrixData = np.array(allParams[-1]).astype("double")
        else:
            isOk, optimFileTxt = check_path(optimFileTxt)
            if isOk>0:
                optimFile = optimFileTxt
                try:
                    with open(optimFile, newline = '') as fileID:
                        data_reader = csv.reader(fileID, delimiter=' ',skipinitialspace=True)
                        list_data = []
                        for raw in data_reader:
                            if(len(raw)>1):
                                if raw[0]+" "+raw[1]=="Best run":
                                    list_data.append(raw[3:-1])
                    matrixData = np.array(list_data[0]).astype("double")
                except:
                    wx.MessageBox(_('The best parameters file is not found!'), _('Error'), wx.OK|wx.ICON_ERROR)

            else:
                logging.error('The best parameters file is not found!')
                return


        return matrixData


    def init_with_reference(self, idLauncher=0):

        curCase = self.myCases[idLauncher]
        refCatch = curCase.refCatchment

        # First path opened by the GUI selecting the the working directory
        defaultPath = self.myCases[idLauncher].launcherParam.get_param("Calculs","Répertoire simulation de référence")
        isOk, defaultPath = check_path(defaultPath, self.workingDir)
        if isOk<0:
            defaultPath = ""

        # Selection of the working directory
        idir=wx.FileDialog(None,"Choose a reference file",wildcard='Fichiers post-processing (*.postPro)|*.postPro',defaultDir=defaultPath)
        if idir.ShowModal() == wx.ID_CANCEL:
            logging.info(_("Post process cancelled!"))
            idir.Destroy()

        refFileName = idir.GetPath()
        refDir = idir.GetDirectory() + "\\"
        idir.Destroy()

        myPostPro = PostProcessHydrology(postProFile=refFileName)

        # Recover the Catchment object
        self.myCases[idLauncher].refCatchment = myPostPro.myCatchments["Catchment 1"]['Object']
        curCase.launcherParam.change_param("Calculs", "Répertoire simulation de référence", refCatch.workingDir)

        # Create an empty geom.txt file
        geomName = self.myCases[idLauncher].launcherParam.get_param("Récupération des résultats","geom_filename")
        open(self.myCases[idLauncher].launcherDir[idLauncher]+geomName, mode='a').close()

        # Complete the default model parameters



        # Complete compare.how file
        dateTmp = refCatch.paramsInput.get_param("Temporal Parameters","Start date time")
        self.comparHowParam.change_param("Comparison 1","date begin 1",dateTmp)
        dateTmp = refCatch.paramsInput.get_param("Temporal Parameters","End date time")
        self.comparHowParam.change_param("Comparison 1","date end 1",dateTmp)

        # update param files
        self.myCases[idLauncher].launcherParam.SavetoFile(None)
        self.myCases[idLauncher].launcherParam.Reload(None)
        self.comparHowParam.SavetoFile(None)
        self.comparHowParam.Reload(None)


    def get_reference(self, refFileName="", idLauncher=0):

        if(refFileName==""):
            # First path opened by the GUI selecting the the working directory
            launcherDir = self.optiParam.get_param("Cases","dir_"+str(idLauncher+1))
            isOk, launcherDir = check_path(launcherDir, prefix=self.workingDir, applyCWD=True)
            defaultPath = self.myCases[idLauncher].launcherParam.get_param("Calculs","Répertoire simulation de référence")
            isOk, defaultPath = check_path(defaultPath, launcherDir)
            if isOk<0:
                defaultPath = ""
            if self.wx_exists:
                idir=wx.FileDialog(None,"Choose a reference file",wildcard='Fichiers post-processing (*.postPro)|*.postPro',defaultDir=defaultPath)
                if idir.ShowModal() == wx.ID_CANCEL:
                    logging.info(_("Post process cancelled!"))
                    idir.Destroy()
                refFileName = idir.GetPath()
                refDir = idir.GetDirectory()
                idir.Destroy()
            else:
                refDir = defaultPath
                refFileName = join(refDir, "Input.postPro")



        myPostPro = PostProcessHydrology(postProFile=refFileName)
        # Recover the Catchment object
        self.myCases[idLauncher].refCatchment = myPostPro.myCatchments["Catchment 1"]['Object']

        # Just save the path in the param file if it is different -> to keep it relative if it is given like that
        if not os.path.samefile(refDir, defaultPath):
            self.myCases[idLauncher].launcherParam.change_param("Calculs", "Répertoire simulation de référence", refDir)

        # Create an empty geom.txt file
        geomName = self.myCases[idLauncher].launcherParam.get_param("Récupération des résultats","geom_filename")
        open(os.path.join(self.myCases[idLauncher].launcherDir,geomName), mode='a').close()

        # update param files
        self.myCases[idLauncher].launcherParam.SavetoFile(None)
        self.myCases[idLauncher].launcherParam.Reload(None)

        # Init the outlet ID
        stationOut = self.optiParam.get_param("Semi-Distributed","Station measures 1")
        if stationOut is None:
            stationOut = self.comparHowParam.get_param("Comparison 1","station measures")
            if stationOut is None:
                stationOut = " "
        else:
            compareFileName = self.optiParam.get_param("Semi-Distributed","File reference 1")
            shutil.copyfile(os.path.join(self.workingDir,compareFileName), os.path.join(self.workingDir,"compare.txt"))
        self.myCases[idLauncher].refCatchment.define_station_out(stationOut)


    def init_dir_in_params(self):

        self.optiParam.change_param("Optimizer","dir", self.workingDir)
        for i in range(len(self.myCases)):
            self.optiParam.change_param("Cases","dir_"+str(i+1), os.path.join(self.workingDir,"simul_"+str(i+1)))
        self.optiParam.change_param("Predefined parameters","fname", os.path.join(self.workingDir,"param.what"))
        self.optiParam.SavetoFile(None)
        self.optiParam.Reload(None)


    def update_dir_in_params(self):

        self.optiParam.change_param("Optimizer","dir", self.workingDir)
        for i in range(len(self.myCases)):
            self.optiParam.change_param("Cases","dir_"+str(i+1), self.myCases[i].launcherDir)
        self.optiParam.change_param("Predefined parameters","fname", os.path.join(self.workingDir,"param.what"))
        self.optiParam.SavetoFile(None)
        self.optiParam.Reload(None)


    def checkIntervals(self):

        logging.info(_("So far do nothing to check intervals!"))
        # self.comparHowParam[]


    def update_parameters_launcher(self, idLauncher=0):
        self.myCases[idLauncher].launcherParam.change_param("Paramètres à varier","Nombre de paramètres à varier",self.nbParams)


    def update_parameters_SA(self):

        # Update the parameters numbers in SA file, according to
        for curGroup in self.saParam.myIncParam:
            for element in self.saParam.myIncParam[curGroup]:
                curParam = self.saParam.myIncParam[curGroup][element]
                if not  "Ref param" in curParam:
                    savedDict = self.saParam.myIncParam[curGroup]["Saved"][curGroup]
                    templateDict = self.saParam.myIncParam[curGroup]["Dict"]
                    for i in range(1,self.nbParams+1):
                        curGroup = curParam.replace("$n$",str(i))
                        if(curGroup in self.saParam.myparams):
                            savedDict[curGroup] = {}
                            savedDict[curGroup] = self.saParam.myparams[curGroup]
                        elif(curGroup in savedDict):
                            self.saParam.myparams[curGroup] = {}
                            self.saParam.myparams[curGroup] = savedDict[curGroup]
                        else:
                            self.saParam.myparams[curGroup] = {}
                            self.saParam.myparams[curGroup] = templateDict.copy()


        # update param files
        # self.launcherParam.SavetoFile(None)
        # self.launcherParam.Reload(None)
        self.saParam.SavetoFile(None)
        self.saParam.Reload(None)


    def plot_optim_sub(self, event, idLauncher=0):
        # this function will plot the hydrographs with the optimal parameters compared to the objective
        figure = Figure(figsize=(5, 4), dpi=100)

        self.axes = figure.add_subplot(111)

        # self.myCases[idLauncher].refCatchment.plot_allSub(withEvap=False, withCt=False, selection_by_iD=self.myCases[idLauncher].refCatchment.myEffSubBasins, \
        #                             graph_title="My optimal configuration", show=True, writeDir=self.workingDir,figure=figure)
        self.myCases[idLauncher].refCatchment.plot_allSub(withEvap=False, withCt=False, selection_by_iD=self.myCases[idLauncher].refCatchment.myEffSubBasins, \
                                    graph_title="My optimal configuration", show=True, writeDir=self.workingDir)

        # self.axes.set_xlabel('x axis')
        self.canvas = FigureCanvas(self, -1, figure)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.TOP | wx.LEFT | wx.EXPAND)

        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)

        # update the axes menu on the toolbar
        self.toolbar.update()
        self.SetSizer(self.sizer)
        self.Fit()


    def plot_optim_jct(self, event, idLauncher=0):
        # this function will plot the hydrographs with the optimal parameters compared to the objective

        refCatch:Catchment = self.myCases[idLauncher].refCatchment

        # Construction of the Measures, in other words the references
        compMeas = []
        if self.myStations==[]:
            self.set_compare_stations(idLauncher=idLauncher)

        compMeas = list(self.compareSubBasins.values())

        # Construction of the wx window for plot
        figure = Figure(figsize=(5, 4), dpi=100)

        self.axes = figure.add_subplot(111)


        r = wx.MessageDialog(
            None, "Do you want to add a table?", "Plot question",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        ).ShowModal()

        if r == wx.ID_YES:
            addTable = True
        else:
            addTable = False
        # FIXME To remove !!!!
        # ti = datetime.datetime(year=2021, month=7, day=13, hour=0, minute=0, second=0,  microsecond=0, tzinfo=datetime.timezone.utc)
        # tf = datetime.datetime(year=2021, month=7, day=16, hour=6, minute=0, second=0,  microsecond=0, tzinfo=datetime.timezone.utc)
        # rangeData = [ti, tf]
        # refCatch.plot_allJct(Measures=compMeas, withEvap=False, selection_by_key=self.myStations, \
        #                             graph_title="My optimal configurations", show=True, writeDir=self.workingDir, Measure_unit="mm/h", addTable=addTable, rangeData=rangeData)
        refCatch.plot_allJct(Measures=compMeas, withEvap=False, selection_by_key=self.myStations, \
                                    graph_title="My optimal configurations", show=True, writeDir=self.workingDir, Measure_unit="mm/h", addTable=addTable)
        # refCatch.plot_allJct(Measures=compMeas, withEvap=False, selection_by_key=self.myStations, \
        #                             graph_title="My optimal configurations", show=True, writeDir=self.workingDir, Measure_unit="mm/h", addTable=addTable, rangeData=rangeData)

        # refCatch.plot_allJct(Measures=compMeas, withEvap=False, withCt=False, selection_by_key=self.myStations, \
        #                             graph_title="My optimal configurations", show=True, writeDir=self.workingDir,figure=figure)

        # self.axes.set_xlabel('x axis')
        self.canvas = FigureCanvas(self, -1, figure)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.TOP | wx.LEFT | wx.EXPAND)

        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)

        # update the axes menu on the toolbar
        self.toolbar.update()
        self.SetSizer(self.sizer)
        self.Fit()


    def load_dll(self, path:str, fileName:str = "WolfDLL.dll"):
        """ Load the Fortran DLL for optimization.

        :param path: The directory where the DLL is located.
        :param fileName: The name of the DLL file to load.
        """

        libpath = os.path.join(path, fileName)

        if not Path(libpath).exists():
            # try libs subdirectory
            libpath = os.path.join(path, "libs", fileName)
            if not Path(libpath).exists():
                logging.error(f"Library not found: {libpath}")
                return

        try:
            self.dllFortran = ct.CDLL(libpath)
        except:
            logging.error(_('Error during loading of WolfDLL.dll -- Please check if all Fortran DLL dependencies are met !'))

    def default_files(self):
        """ Create the default optimizer files in the working directory. """

        pathPtr = str(self.workingDir).encode('ansi')
        fileNamePtr = "test_opti.param".encode('ansi')
        self.dllFortran.new_optimizer_files_py.restype = ct.c_int
        self.dllFortran.new_optimizer_files_py.argtypes = [ct.c_char_p, ct.c_char_p, ct.c_int, ct.c_int]

        logging.info(_("Launch a Fortran procedure"))
        id = self.dllFortran.new_optimizer_files_py(pathPtr,fileNamePtr,ct.c_int(len(pathPtr)),ct.c_int(len(fileNamePtr)))

        logging.info(_("id optimizer = "), id)

        logging.info(_("End of Fortran procedure"))

    def compute_optimizer(self, idOpti=1):

        self.dllFortran.compute_optimizer_py.restype = ct.c_int
        self.dllFortran.compute_optimizer_py.argtypes = [ct.POINTER(ct.c_int)]

        logging.info(_("Launch a Fortran procedure"))
        isOk = self.dllFortran.compute_optimizer_py(ct.byref(ct.c_int(idOpti)))
        logging.info(_("End of Fortran procedure"))

        if isOk!=0:
            logging.error("ERROR: in the Fotran routine in the optimizer computation!")


    def evaluate_model_optimizer(self, parameters:np.array, idOpti:int=1):

        self.dllFortran.evaluate_model_optimizer_py.restype = ct.c_double
        self.dllFortran.evaluate_model_optimizer_py.argtypes = [ct.POINTER(ct.c_int),
                                                                ct.POINTER(ct.c_int),
                                                                ct.POINTER(ct.c_double)]

        dims = np.array([len(parameters)], dtype=ct.c_int, order='F')
        p = np.array(parameters, dtype=ct.c_double, order='F')

        pointerDims = dims.ctypes.data_as(ct.POINTER(ct.c_int))
        pointer_p = p.ctypes.data_as(ct.POINTER(ct.c_double))

        logging.info(_("Launch a Fortran procedure"))
        obj_fct = self.dllFortran.evaluate_model_optimizer_py(ct.byref(ct.c_int(idOpti)),
                                                           pointerDims,
                                                           pointer_p)
        logging.info(_("End of Fortran procedure"))

        return obj_fct


    def write_mesh_results_optimizer(self, idOpti:int=1):

        self.dllFortran.write_mesh_results_optimizer_py.restype = ct.c_int
        self.dllFortran.write_mesh_results_optimizer_py.argtypes = [ct.POINTER(ct.c_int)]


        logging.info(_("Launch a Fortran procedure"))
        isOk = self.dllFortran.write_mesh_results_optimizer_py(ct.byref(ct.c_int(idOpti)))
        logging.info(_("End of Fortran procedure"))

        if isOk!=0:
            logging.error("ERROR: in the Fotran routine in the optimizer computation!")


    def init_optimizer(self, idForced=-1):

        pathPtr = str(self.workingDir).encode('ansi')
        fileNamePtr = "test_opti.param".encode('ansi')
        self.dllFortran.init_optimizer_py.restype = ct.c_int
        self.dllFortran.init_optimizer_py.argtypes = [ct.c_char_p, ct.c_char_p, ct.c_int, ct.c_int,ct.POINTER(ct.c_int)]

        if(idForced<0):
            opt_id = None
        else:
            opt_id = ct.byref(ct.c_int(idForced))
        logging.info(_("Launch a Fortran procedure"))
        id = self.dllFortran.init_optimizer_py(pathPtr,fileNamePtr,ct.c_int(len(pathPtr)),ct.c_int(len(fileNamePtr)), opt_id)

        logging.info(_("id optimizer = "), id)

        logging.info(_("End of Fortran procedure"))


    def init_optimizer_again(self, event, idForced=1):

        pathPtr = str(self.workingDir).encode('ansi')
        fileNamePtr = "test_opti.param".encode('ansi')
        self.dllFortran.init_optimizer_py.restype = ct.c_int
        self.dllFortran.init_optimizer_py.argtypes = [ct.c_char_p, ct.c_char_p, ct.c_int, ct.c_int,ct.POINTER(ct.c_int)]

        if(idForced<0):
            opt_id = None
        else:
            opt_id = ct.byref(ct.c_int(idForced))
        logging.info(_("Launch a Fortran procedure"))
        id = self.dllFortran.init_optimizer_py(pathPtr,fileNamePtr,ct.c_int(len(pathPtr)),ct.c_int(len(fileNamePtr)), opt_id)

        logging.info(_("id optimizer = "), id)

        logging.info(_("End of Fortran procedure"))



    def compute_distributed_hydro_model(self, idLauncher=0):

        self.dllFortran.compute_dist_hydro_model_py.restype = ct.c_int
        self.dllFortran.compute_dist_hydro_model_py.argtypes = [ct.c_char_p, ct.c_int]

        pathPtr = self.myCases[idLauncher].refCatchment.workingDir.encode('ansi')

        logging.info(_("Compute distributed hydro model ..."))
        isOk = self.dllFortran.compute_dist_hydro_model_py(pathPtr, ct.c_int(len(pathPtr)))
        logging.info(_("End of distributed hydro model."))


    def compute0_distributed_hydro_model(self, event):

        self.dllFortran.compute_dist_hydro_model_py.restype = ct.c_int
        self.dllFortran.compute_dist_hydro_model_py.argtypes = [ct.c_char_p, ct.c_int]

        idir=wx.DirDialog(None,"Choose an hydrology directory")
        if idir.ShowModal() == wx.ID_CANCEL:
            logging.info(_("Hydrology computation cancelled!"))
            idir.Destroy()
            return
        pathPtr = idir.GetPath().encode('ansi')
        idir.Destroy()


        logging.info(_("Compute distributed hydro model ..."))
        isOk = self.dllFortran.compute_dist_hydro_model_py(pathPtr, ct.c_int(len(pathPtr)))
        logging.info(_("End of distributed hydro model."))




    def associate_ptr(self, event, which="all", idOpti=1, idLauncher=0):

        self.dllFortran.associate_ptr_py.restype = ct.c_int
        self.dllFortran.associate_ptr_py.argtypes = [ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.c_int,
                                                ct.POINTER(ct.c_int), ct.POINTER(ct.c_double)]

        self.dllFortran.get_cptr_py.restype = ct.POINTER(ct.c_double)
        self.dllFortran.get_cptr_py.argtypes = [ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.c_int,
                                                ct.POINTER(ct.c_int)]

        self.dllFortran.associate_callback_fct.restype = ct.c_int
        self.dllFortran.associate_callback_fct.argtypes = [ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.c_int,
                                                ct.POINTER(ct.c_int), ct.POINTER(ct.c_double)]

        if(which.lower()=="all"):
            self.associate_ptr_params(idOpti,idLauncher)
            self.associate_ptr_opti_factor(idOpti,idLauncher)
            self.associate_ptr_q_all(idOpti,idLauncher)
            if(self.myCases[idLauncher].refCatchment.myModel == cst.tom_2layers_linIF or \
              self.myCases[idLauncher].refCatchment.myModel == cst.tom_2layers_UH):
                self.associate_ptr_time_delays(idOpti,idLauncher)


            self.associate_callback_fct_update(idOpti,idLauncher)
            self.associate_callback_fct_getcvg(idOpti,idLauncher)


    def associate_callback_fct(self):
        logging.info(_("Associate callback function ..."))


    def associate_callback_fct_update(self, idOpti=1, idLauncher=0):
        # The function proc and ptr should be kept in memory to keep function pointer
        self.callBack_proc[cste.fptr_update] = ct.CFUNCTYPE(ct.c_int, ct.c_int)
        update_proc = self.callBack_proc[cste.fptr_update]
        self.callBack_ptr[cste.fptr_update] = update_proc(self.update_hydro)
        update_ptr = self.callBack_ptr[cste.fptr_update]


        self.dllFortran.associate_callback_fct.restype = ct.c_int
        self.dllFortran.associate_callback_fct.argtypes = [ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.c_int,
                                                ct.POINTER(ct.c_int), update_proc]

        # nb of arguments in the dimensions vector (dims)
        ndims = 1
        # init of the dimensions vector
        dims = np.zeros((ndims,), dtype=ct.c_int, order='F')
        pointerDims = dims.ctypes.data_as(ct.POINTER(ct.c_int))

        # Launch Fortran function
        self.dllFortran.associate_callback_fct(ct.byref(ct.c_int(idOpti)),ct.byref(ct.c_int(idLauncher+1)),
                                            ct.c_int(cste.fptr_update),pointerDims,update_ptr)

        logging.info(_("End of update pointer association!"))



    def associate_callback_fct_getcvg(self, idOpti=1, idLauncher=0):
        self.callBack_proc[cste.fptr_get_cvg] = ct.CFUNCTYPE(ct.c_int, ct.POINTER(ct.c_double))
        getcvg_proc = self.callBack_proc[cste.fptr_get_cvg]
        self.callBack_ptr[cste.fptr_get_cvg] = getcvg_proc(self.get_cvg)
        getcvg_ptr = self.callBack_ptr[cste.fptr_get_cvg]


        self.dllFortran.associate_callback_fct.restype = ct.c_int
        self.dllFortran.associate_callback_fct.argtypes = [ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.c_int,
                                                ct.POINTER(ct.c_int), getcvg_proc]

        # nb of arguments in the dimensions vector (dims)
        ndims = 1
        # init of the dimensions vector
        dims = np.zeros((ndims,), dtype=ct.c_int, order='F')
        pointerDims = dims.ctypes.data_as(ct.POINTER(ct.c_int))

        # Launch Fortran function
        self.dllFortran.associate_callback_fct(ct.byref(ct.c_int(idOpti)),ct.byref(ct.c_int(idLauncher+1)),
                                            ct.c_int(cste.fptr_get_cvg),pointerDims,getcvg_ptr)

        logging.info(_("End of pointer association!"))


    def associate_ptr_q_all(self, idOpti=1, idLauncher=0):
        # nb of arguments in the dimensions vector (dims)
        ndims = 3
        # init of the dimensions vector
        dims = np.zeros((ndims,), dtype=ct.c_int, order='F')
        pointerDims = dims.ctypes.data_as(ct.POINTER(ct.c_int))

        counter = 1
        for iSub in self.myCases[idLauncher].refCatchment.myEffSortSubBasins:
            # curSub = self.refCatchment.subBasinDict[iSub]
            mydict = self.myCases[idLauncher].refCatchment.dictIdConversion
            idIP= list(mydict.keys())[list(mydict.values()).index(iSub)]
            curSub = self.myCases[idLauncher].refCatchment.subBasinDict[idIP]
            dims[2] = counter
            dims[0] = len(self.myCases[idLauncher].refCatchment.time)
            # call of the Fortran function
            curSub.ptr_q_all = None
            curSub.ptr_q_all = self.dllFortran.get_cptr_py(ct.byref(ct.c_int(idOpti)),ct.byref(ct.c_int(idLauncher+1)),
                                            ct.c_int(cste.ptr_q_all), pointerDims)
            curSub.myHydro = None
            curSub.myHydro = self.make_nd_array(curSub.ptr_q_all, shape=(dims[0],dims[1]), dtype=ct.c_double, order='F', own_data=False)


            # print("output[1,0] = ", curSub.myHydro[1,0])
            # print("output[2,0] = ", curSub.myHydro[2,0])
            # print("output[3,0] = ", curSub.myHydro[3,0])
            # print("output[3,1) = ", curSub.myHydro[3,1])
            # print("curSub = ", curSub.myHydro)
            counter += 1


    def associate_ptr_iv_saved(self, idOpti=1, idLauncher=0):
        # nb of arguments in the dimensions vector (dims)
        ndims = 3
        # init of the dimensions vector
        dims = np.zeros((ndims,), dtype=ct.c_int, order='F')
        pointerDims = dims.ctypes.data_as(ct.POINTER(ct.c_int))

        counter = 1
        for iSub in self.myCases[idLauncher].refCatchment.myEffSortSubBasins:
            # curSub = self.refCatchment.subBasinDict[iSub]
            mydict = self.myCases[idLauncher].refCatchment.dictIdConversion
            idIP= list(mydict.keys())[list(mydict.values()).index(iSub)]
            curSub = self.myCases[idLauncher].refCatchment.subBasinDict[idIP]
            dims[2] = counter
            dims[0] = len(self.myCases[idLauncher].refCatchment.time)
            # call of the Fortran function
            curSub.ptr_iv_saved = None
            curSub.ptr_iv_saved = self.dllFortran.get_cptr_py(ct.byref(ct.c_int(idOpti)),ct.byref(ct.c_int(idLauncher+1)),
                                            ct.c_int(cste.ptr_iv_saved), pointerDims)
            curSub.saved_iv = None
            curSub.saved_iv = self.make_nd_array(curSub.ptr_iv_saved, shape=(dims[0],dims[1]), dtype=ct.c_double, order='F', own_data=False)

            counter += 1


    def associate_ptr_time_delays(self, idOpti=1, idLauncher=0):
        # nb of arguments in the dimensions vector (dims)
        ndims = 1
        # init of the dimensions vector
        dims = np.zeros((ndims,), dtype=ct.c_int, order='F')
        pointerDims = dims.ctypes.data_as(ct.POINTER(ct.c_int))

        mydict = self.myCases[idLauncher].refCatchment.dictIdConversion
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        dims[0] = self.myCases[idLauncher].refCatchment.nbSubBasin
        # call of the Fortran function
        curCatch.time_delays_F = None
        curCatch.ptr_time_delays = None
        curCatch.ptr_time_delays = self.dllFortran.get_cptr_py(ct.byref(ct.c_int(idOpti)),ct.byref(ct.c_int(idLauncher+1)),
                                        ct.c_int(cste.ptr_time_delays), pointerDims)
        curCatch.time_delays_F = self.make_nd_array(curCatch.ptr_time_delays, shape=(dims[0],), dtype=ct.c_double, order='F', own_data=False)



    def associate_ptr_params(self, idOpti=1, idLauncher=0):
        # nb of arguments in the dimensions vector (dims)
        ndims = 1
        # init of the dimensions vector
        dims = np.empty((ndims,), dtype=ct.c_int, order='F')
        # The only dimension is the number of parameters to calibrate
        dims[0] = self.nbParams
        self.curParams_vec_F = np.empty((self.nbParams,), dtype=ct.c_double, order='F')
        # creation of the c_ptr to give to fortran to reconstruct the tensors
        pointerParam = self.curParams_vec_F.ctypes.data_as(ct.POINTER(ct.c_double))
        pointerDims = dims.ctypes.data_as(ct.POINTER(ct.c_int))
        # call of the Fortran function
        isOk = self.dllFortran.associate_ptr_py(ct.byref(ct.c_int(idOpti)),ct.byref(ct.c_int(idLauncher+1)), ct.c_int(cste.ptr_params),
                                        pointerDims, pointerParam)

        logging.info(_("End of parameter pointer association."))



    def associate_ptr_opti_factor(self, idOpti=1, idLauncher=0):
        # nb of arguments in the dimensions vector (dims)
        ndims = 1
        # init of the dimensions vector
        dims = np.empty((ndims,), dtype=ct.c_int, order='F')
        # The only dimension is the number of parameters to calibrate
        dims[0] = 1
        self.optiFactor_F = ct.c_double(0.0)
        # creation of the c_ptr to give to fortran to reconstruct the tensors
        pointerDims = dims.ctypes.data_as(ct.POINTER(ct.c_int))
        # call of the Fortran function
        isOk = self.dllFortran.associate_ptr_py(ct.byref(ct.c_int(idOpti)),ct.byref(ct.c_int(idLauncher+1)), ct.c_int(cste.ptr_opti_factors),
                                        pointerDims, ct.byref(self.optiFactor_F))

        logging.info(_("End of factor pointer association."))


    def get_all_activated_iv(self, idOpti:int=1, idLauncher:int=0,
                             iv_variables:tuple[np.ndarray, np.ndarray]=None)-> tuple[np.ndarray, np.ndarray]:
        def check_iv_variables(iv_ids, iv_values, expected_nb_iv):
            assert iv_ids.dtype == np.dtype(ct.c_int), "The vector of ids iv_ids dtype is not ct.c_int (float64)"
            assert iv_ids.flags['F_CONTIGUOUS'], "The vector of ids iv_ids is not Fortran-ordered (order='F')"
            assert iv_ids.shape[0] == expected_nb_iv, f"Expected {expected_nb_iv} ids, got {iv_ids.shape[0]}"
            assert iv_values.dtype == np.dtype(ct.c_double), "Array of i.v. dtype is not ct.c_double (float64)"
            assert iv_values.flags['F_CONTIGUOUS'], "Array of i.v. is not Fortran-ordered (order='F')"
            assert iv_values.shape[1] == expected_nb_iv, f"Expected {expected_nb_iv} values per id, got {iv_values.shape[1]}"

        self.dllFortran.get_nb_activated_iv_py.restype = ct.c_int
        self.dllFortran.get_nb_activated_iv_py.argtypes = [ct.POINTER(ct.c_int),
                                                           ct.POINTER(ct.c_int),
                                                           ct.POINTER(ct.c_int)]

        self.dllFortran.get_all_activated_iv_py.restype = ct.c_int
        self.dllFortran.get_all_activated_iv_py.argtypes = [ct.POINTER(ct.c_int),
                                                           ct.POINTER(ct.c_int),
                                                           ct.POINTER(ct.c_int),
                                                           ct.POINTER(ct.c_int),
                                                           ct.POINTER(ct.c_int),
                                                           ct.POINTER(ct.c_double)]

        nb_iv = ct.c_int()
        logging.info(_("Launch a Fortran procedure"))
        isOk = self.dllFortran.get_nb_activated_iv_py(ct.byref(ct.c_int(idOpti)),
                                                      ct.byref(ct.c_int(idLauncher+1)),
                                                      ct.byref(nb_iv))
        if isOk!=0:
            logging.error("Problem in the Fortran routine in get_nb_activated_iv_py!")
            return None, None
        if nb_iv.value == 0:
            logging.warning("No activated input variables found in the Fortran routine in get_nb_activated_iv_py!")
            return None, None

        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        nb_t = ct.c_int(len(curCatch.time))
        if iv_variables is not None:
            # If iv_variables is provided, use its shape to determine the number of intervals
            iv_ids, iv_values = iv_variables
            check_iv_variables(iv_ids, iv_values, nb_iv.value)
        else:
            iv_ids = np.zeros((nb_iv.value,), dtype=ct.c_int, order='F')
            iv_values = np.zeros((nb_t.value, nb_iv.value), dtype=ct.c_double, order='F')
        ptr_ids = iv_ids.ctypes.data_as(ct.POINTER(ct.c_int))
        ptr_values = iv_values.ctypes.data_as(ct.POINTER(ct.c_double))
        # FIXME: consider all effective sub-basin
        # TODO: generalise for when several effective subbasins
        id_sub_eff = ct.c_int(0)

        isOk = self.dllFortran.get_all_activated_iv_py(ct.byref(ct.c_int(idOpti)),
                                                        ct.byref(ct.c_int(idLauncher+1)),
                                                        ct.byref(nb_t),
                                                        ct.byref(nb_iv),
                                                        ptr_ids,
                                                        ptr_values,
                                                        id_sub_eff)
        if isOk<0:
            logging.error("Problem in the Fortran routine in get_all_activated_iv_py!")
            return None, None

        logging.info(_("End of Fortran procedure"))

        return iv_ids, iv_values


    def init_distributed_hydro_model(self, event):

        pathPtr = str(self.workingDir).encode('ansi')
        fileNamePtr = "test_opti.param".encode('ansi')
        self.dllFortran.init_dist_hydro_model_py.restype = ct.c_int
        self.dllFortran.init_dist_hydro_model_py.argtypes = []

        logging.info(_("Launch a Fortran procedure"))
        id = self.dllFortran.init_dist_hydro_model_py()

        logging.info(_("id distributed_hydro_model = %d"), id)

        logging.info(_("End of Fortran procedure"))


    def launch_lumped_optimisation(self, event, idOpti=1):

        # Launch Fortran routine to initialise the object
        self.init_optimizer(idOpti)

        # Associate all the pointers between Python and Fortran
        self.associate_ptr(event, which="all",idOpti=idOpti)

        # Launch Fortran routine to compute optimisation and write the best results
        self.compute_optimizer(idOpti=idOpti)

        logging.info(_("Best parameters : %s"), self.curParams_vec_F)
        logging.info(_("Best Factor = %s"), self.optiFactor_F)

        # Apply the best parameters
        self.apply_optim(None)

        # Simulation with the best parameters
        self.compute_distributed_hydro_model()

        # Possibility to use the optimisation results enabled
        self.enable_MenuBar("Tools")


    def test_update_hydro_py(self, event):


        self.dllFortran.test_update_hydro.restype = None
        self.dllFortran.test_update_hydro.argtypes = []

        # call of the Fortran function
        self.dllFortran.test_update_hydro()


    def launch_semiDistributed_optimisation(self, event, idOpti=1, idLauncher=0):
        """
        Procedure launching the semi-distributed optimisation process.

        Args:
            event: The event triggering the optimisation.
            idOpti (int): The ID of the optimizer in Fortran.
            idLauncher (int): The ID of the launcher.

        Returns:
            None
        """
        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        # if (self.optiParam.get_group("Semi-Distributed"))is not None:
        try:
            nbRefs = self.optiParam.get_param("Semi-Distributed","nb")
            onlyOwnSub = self.optiParam.get_param("Semi-Distributed", "Own_SubBasin")
            if onlyOwnSub is None:
                onlyOwnSub = False
            doneList = []
            previousLevel = 1
            # Collect sort and save the compare stations
            self.set_compare_stations(idLauncher=idLauncher)
            sortJct = self.myStations
            readDict = self.compareFilesDict
            # Get the initial number of intervals
            # -> these can evolve according to the measurement available at each station
            is_ok = self._save_opti_intervals()
            if is_ok<0:
                logging.error("Problem in optimisation intervals! Optimisation abort !")
                return
            all_intervals = self.all_intervals
            simul_intervals = curCatch.simulation_intervals
            # FIXME : to potentially remove
            nb_comparisons = self.comparHowParam.get_param("Comparison global characteristics","nb")
            nb_intervals_init = len(self.all_intervals)
            # Get the number of attempts with random initial conditions and from the best parameters for each station
            # The total number of iterations per station is the product of these two numbers :
            # nb_iter total = nb_iter_from_random * nb_iter_from_best
            nb_iter_from_random = self.optiParam.get_param("Optimizer","nb iter from random initial conditions",default_value=1)
            nb_iter_from_best = self.optiParam.get_param("Optimizer","nb iter from best",default_value=1)

            for iOpti in range(len(sortJct)):
                stationOut = sortJct[iOpti]
                # Build the current compare.txt file and replace all nan values by 0.0
                self.save_current_compare_file(stationOut=stationOut)
                # Save the name of the station that will be the output
                curCatch.define_station_out(stationOut)
                # Activate all the useful subs and write it in the param file
                curCatch.activate_usefulSubs(blockJunction=doneList, onlyItself=onlyOwnSub)
                # Select correct calibration intervals -> remove the intervals with NaN
                cur_intervals = self.select_opti_intervals(all_intervals=all_intervals, stationOut=stationOut, filter_nan=True)
                self.save_opti_dates_to_file(cur_intervals)
                is_ok = self._save_opti_intervals(stationOut=stationOut, intervals=cur_intervals)

                # Rename the result file
                self.optiParam.change_param("Optimizer", "fname", stationOut)
                self.optiParam.SavetoFile(None)
                self.optiParam.Reload(None)
                self.update_myParams(idLauncher)
                # Prepare the paramPy dictionnary before calibration
                self.prepare_calibration_timeDelay(stationOut=stationOut)
                # Prepare the potential discontinuous simulation
                # FIXME : to potentially uncomment or removed : probably remove because we want to generate the complete event simulations to progress in the optimisation
                # self.prepare_simulation(opti_intervals=cur_intervals, idLauncher=idLauncher)
                # Check the initial parameters and if they are forced
                init_params = self.get_initial_parameters()
                ## loop on the number of different optimisation attempt we would like for each station
                best_params_overall = None
                cur_i = 0
                i_best_overal = 0
                for i_rand in range(nb_iter_from_random):
                    best_params = init_params
                    for i_best in range(nb_iter_from_best):
                        # Prepare I.C. starting from best configuration
                        self.prepare_init_params_from_best(best_params=best_params, idLauncher=idLauncher)
                        # Reload the useful modules
                        self.reload_hydro(idCompar=0, fromStation=stationOut, lastLevel=previousLevel, updateAll=True)
                        # Compute
                        self.init_optimizer(idOpti)
                        self.associate_ptr(None, idOpti=idOpti)
                        self.compute_optimizer(idOpti)
                        # Collect the best parameters and their objective function(s)
                        test_params = self.apply_optim(None, replace_only_if_better=(i_best!=0)) # Always apply the best parameters for the first iteration
                        # If test_params are not the best or 1st test => We don't save them
                        if test_params is not None:
                            best_params = test_params
                            if best_params_overall is None:
                                best_params_overall = best_params
                            elif best_params[-1] > best_params_overall[-1]:
                                best_params_overall = best_params
                                i_best_overal = cur_i
                        # copy the optimisation results to save it on the disk
                        shutil.copyfile(self.workingDir / (stationOut+".rpt.dat"),
                                        self.workingDir / (stationOut+"_"+str(cur_i+1)+".rpt.dat"))
                        shutil.copyfile(self.workingDir / (stationOut+".rpt"),
                                        self.workingDir / (stationOut+"_"+str(cur_i+1)+".rpt"))
                        cur_i += 1
                # Apply the best parameters overall attemps
                self.apply_optim(None,optim_params=best_params_overall)
                # Reset the init parameters
                self.reset_init_params(init_params)
                # copy the optimisation results to save it on the disk
                shutil.copyfile(self.workingDir / (stationOut+"_"+str(i_best_overal+1)+".rpt.dat"),
                                self.workingDir / (stationOut+".rpt.dat"))
                shutil.copyfile(self.workingDir/ (stationOut+"_"+str(i_best_overal+1)+".rpt"),
                                self.workingDir / (stationOut+".rpt"))

                # Simulation with the best parameters
                self.compute_distributed_hydro_model()
                cur_p = best_params_overall[:-1]
                cur_obj = best_params_overall[-1]
                cur_obj2 = self.evaluate_model_optimizer(cur_p, idOpti=idOpti)
                logging.info(_("cur_obj : %s ; cur_obj2 : %s"), cur_obj, cur_obj2)
                if cur_obj != cur_obj2:
                    logging.error(_("The objective function is not the same as the one computed"))
                # Update myHydro of all effective subbasins to get the best configuration upstream
                curCatch.read_hydro_eff_subBasin()
                # Update timeDelays according to time wolf_array
                self.apply_timeDelay_dist(idOpti=idOpti, idLauncher=idLauncher, junctionKey=stationOut)
                # Update the outflows
                curCatch.update_hydro(idCompar=0)
                # reset the simulation intervals to their initial values
                # FIXME : to potentially uncomment or removed : probably remove because we want to generate the complete event simulations to progress in the optimisation
                # self.reset_simulation_intervals(simul_intervals, idLauncher=idLauncher)
                # All upstream elements of a reference will be fixed
                doneList.append(stationOut)
                previousLevel = curCatch.levelOut

            # Reset the optimisation file
            self.save_opti_dates_to_file(self.all_intervals)
        except:
            print(traceback.format_exc())
            logging.error("A problem occured ! Semi-distributed optimisation abort !")
            # Reset the optimisation file
            self.save_opti_dates_to_file(self.all_intervals)
            # reset the simulation intervals to their initial values
            # FIXME : to potentially uncomment or removed : probably remove because we want to generate the complete event simulations to progress in the optimisation
            self.reset_simulation_intervals(simul_intervals, idLauncher=idLauncher)

        # Possibility to use the optimisation results enabled
        self.enable_MenuBar("Tools")

        logging.info(_("End of semi-distributed optimisation!"))


    # TO DO : Change this function to Case -> to make it compatible with several cases.
    def update_hydro(self, idCompar):

        t0 = time_mod.process_time()
        # Will update all the normal parameters
        for element in self.myParams:
            junctionName = self.myParams[element]["junction_name"]
            paramValue = self.curParams_vec_F[element-1]
            if paramValue != self.myParams[element]["value"]:
                self.myParams[element]["value"] = paramValue
                isOk = self.myParams[element]["update"](junctionName, value=paramValue)


        # # Will update all the Python parameters
        # for element in self.myParamsPy:
        #     junctionName = self.myParamsPy[element]["junction_name"]
        #     timeDelta = self.curParams_vec[element-1]
        #     if timeDelta != self.myParamsPy[element]["value"]:
        #         self.myParamsPy[element]["value"] = timeDelta
        #         # self.myParamsPy[element]["update"](junctionName, value=timeDelta)
        #         isOk = self.myParamsPy[element]["update"](junctionName, value=timeDelta)

        isOk = self.myCases[0].refCatchment.update_hydro(idCompar, fromLevel=False)
        tf = time_mod.process_time()
        logging.info(_("Time in update_hydro() : %s"), tf-t0)
        logging.info(_("curParam = %s"), self.curParams_vec_F)
        logging.info(_("All timeDelays = %s"), self.myCases[0].refCatchment.get_all_timeDelay())
        tf = time_mod.process_time()
        logging.info(_("Time in update_hydro() : %s"), tf-t0)
        return isOk


    def reload_hydro(self, idCompar, firstLevel:int=1, lastLevel:int=-1, fromStation:str="", updateAll:bool=False):

        curCatch:Catchment = self.myCases[0].refCatchment
        isOk = curCatch.construct_hydro(firstLevel=firstLevel, lastLevel=lastLevel,
                                        fromStation=fromStation, updateAll=updateAll)

        return isOk


    # TO DO : Change this function to Case -> to make it compatible with several cases.
    def get_cvg(self, pointerData):

        isOk = self.myCases[0].refCatchment.get_cvg(pointerData)

        return isOk


    def update_timeDelay(self, index):

        isOk = 0.0
        newTimeDelay = self.curParams_vec_F[index-1]
        if(self.myParamsPy[index]["value"]!=newTimeDelay):
            junctionName = self.myParamsPy[index]["junction_name"]
            self.myParamsPy[index]["value"] = newTimeDelay
            isOk = self.myParamsPy[index]["update"](junctionName, value=newTimeDelay)
            # self.refCatchment.reset_timeDelay()
            # isOk = self.refCatchment.update_timeDelay(junctionName, value=newTimeDelay)

        # self.myParamsPy[index]["value"] = newTimeDelay

        return isOk



    def prepare_calibration_timeDelay(self, stationOut, idLauncher=0):

        # Check whether the timeDelay should be calibrated
        readTxt = int(self.optiParam.get_param("Semi-Distributed", "Calibrate_times"))
        if readTxt == 1:
            calibrate_timeDelay=True
        else:
            calibrate_timeDelay=False

        # myModel = self.myCases[idLauncher].refCatchment.myModel
        # nbParamsModel = cste.modelParamsDict[myModel]["Nb"]
        self.remove_py_params(idLauncher)
        nbParamsModel = self.myCases[idLauncher].launcherParam.get_param("Paramètres à varier", "Nombre de paramètres à varier")


        if calibrate_timeDelay:

            # Should delete all the python parameters in both myParams and myParamsPy dictionnaries
            # FIXME To generalise that part
            oldDim = len(self.myParams)
            for i in range(nbParamsModel+1, oldDim+1):
                del self.myParams[i]
                del self.myParamsPy[i]


            inletsNames = self.myCases[idLauncher].refCatchment.get_inletsName(stationOut)
            nbInlets = len(inletsNames)

            nbParams = nbParamsModel + nbInlets
            self.nbParams = nbParams
            self.myCases[idLauncher].launcherParam.change_param("Paramètres à varier", "Nombre de paramètres à varier", nbParams)

            prefix1 = "param_"
            prefix2 = "Parameter "

            for i in range(nbInlets):
                paramName = prefix1 + str(nbParamsModel+i+1)
                # self.myCases[idLauncher].launcherParam.myparams[paramName]={}
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["type_of_data"] = {}
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["type_of_data"]["value"] = cste.exchange_parameters_py_timeDelay
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["type_of_data"]["type"] = 'Integer'
                self.myCases[idLauncher].launcherParam.add_group(paramName)
                self.myCases[idLauncher].launcherParam.add_param(paramName, "type_of_data", cste.exchange_parameters_py_timeDelay, Type_Param.Integer)
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["geom_filename"] = {}
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["geom_filename"]["value"] = "my_geom.txt"
                self.myCases[idLauncher].launcherParam.add_param(paramName, "geom_filename", "my_geom.txt", Type_Param.File)
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["type_of_geom"] = {}
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["type_of_geom"]["value"] = 0
                self.myCases[idLauncher].launcherParam.add_param(paramName, "type_of_geom", 0, Type_Param.Integer)
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["type_of_exchange"] = {}
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["type_of_exchange"]["value"] = -3
                self.myCases[idLauncher].launcherParam.add_param(paramName, "type_of_exchange", -3, Type_Param.Integer)

                # Particularity of this Python parameter
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["junction_name"] = {}
                # self.myCases[idLauncher].launcherParam.myparams[paramName]["junction_name"]["value"] = inletsNames[i]
                self.myCases[idLauncher].launcherParam.add_param(paramName, "junction_name", inletsNames[i], Type_Param.String)

                self.myParams[nbParamsModel+i+1] = {}
                self.myParams[nbParamsModel+i+1]["type"] = self.myCases[idLauncher].launcherParam.get_param(paramName, "type_of_data")
                self.myParams[nbParamsModel+i+1]["value"] = 0.0

                self.myParamsPy[nbParamsModel+i+1] = self.myParams[nbParamsModel+i+1]
                self.myParamsPy[nbParamsModel+i+1]["update"] = self.myCases[idLauncher].refCatchment.update_timeDelay
                self.myParamsPy[nbParamsModel+i+1]["junction_name"] = inletsNames[i]

                # Check and replace the time delay params
                paramName = prefix2 + str(nbParamsModel+i+1)
                cur_param = self.saParam.get_param("Lowest values",paramName)
                if cur_param is None:
                    self.saParam.change_param("Lowest values", paramName, 0.0)
                else:
                    if float(cur_param) != 0.0:
                        logging.warning(_("The parameters applied to timeDelays are different than the ones recommanded!"))
                        logging.warning(_("This procedure can be dangerous in semi distributed optimisation! Do it at your own risk!"))

                cur_param = self.saParam.get_param("Highest values",paramName)
                if cur_param is None:
                    self.saParam.change_param("Highest values", paramName, 5.0*24.0*3600.0)
                else:
                    if float(cur_param) != 5.0*24.0*3600.0:
                        logging.warning(_("The parameters applied to timeDelays are different than the ones recommanded!"))
                        logging.warning(_("This procedure can be dangerous in semi distributed optimisation! Do it at your own risk!"))

                cur_param = self.saParam.get_param("Steps",paramName)
                if cur_param is None:
                    self.saParam.change_param("Steps", paramName, self.myCases[idLauncher].refCatchment.deltaT)
                else:
                    if float(cur_param) != self.myCases[idLauncher].refCatchment.deltaT:
                        logging.warning(_("The parameters applied to timeDelays are different than the ones recommanded!"))
                        logging.warning(_("This procedure can be dangerous in semi distributed optimisation! Do it at your own risk!"))

                cur_param = self.saParam.get_param("Initial parameters",paramName)
                if cur_param is None:
                    self.saParam.change_param("Initial parameters", paramName, 1.0*3600.0)
                else:
                    if float(cur_param) != 1.0*3600.0:
                        logging.warning(_("The parameters applied to timeDelays are different than the ones recommanded!"))
                        logging.warning(_("This procedure can be dangerous in semi distributed optimisation! Do it at your own risk!"))

        else:
            self.nbParams = nbParamsModel
            self.myCases[idLauncher].launcherParam.change_param("Paramètres à varier", "Nombre de paramètres à varier", self.nbParams)


        self.myCases[idLauncher].launcherParam.SavetoFile(None)
        self.myCases[idLauncher].launcherParam.Reload(None)
        self.saParam.SavetoFile(None)
        self.saParam.Reload(None)


    def reset(self, event):

        print("TO DO !!!!")


    def disable_all_MenuBar(self, exceptions=[]):

        for element in range(len(self.MenuBar.Menus)):
            curMenu = self.MenuBar.Menus[element][0]
            nameMenu = self.MenuBar.Menus[element][1]

            if(not(nameMenu in exceptions)):
                self.MenuBar.EnableTop(element, False)


    def enable_MenuBar(self, menuBar:str):

        idMenu = self.MenuBar.FindMenu(menuBar)
        self.MenuBar.EnableTop(idMenu, enable=True)


    def enable_Menu(self, menuItem:str, menuBar:str, isEnable:bool):

        idItem = self.MenuBar.FindMenuItem(menuBar, menuItem)
        objItem = self.MenuBar.FindItemById(idItem)
        objItem.Enable(isEnable)


    def add_Case(self):
        print("TO DO!!!")
        # Add the creation of the case object
        # Add the Case in the ToolBar item


    def launch_optimisation(self, idOpti=1):

        # Check if lumped or semi-distriuted
        if((self.optiParam.get_group("Semi-Distributed"))is not None):
            self.launch_semiDistributed_optimisation(idOpti=idOpti)
        else:
            self.launch_lumped_optimisation(None, idOpti=idOpti)
            self.apply_optim(None)



    def show_optiParam(self, event):

        self.optiParam.Show()
        pass


    def show_saParam(self, event):

        self.saParam.Show()
        pass


    def show_comparHowParam(self, event):

        self.comparHowParam.Show()
        pass


    def update_nothing(self, whatever, value=0.0):

        isOk = 0
        return isOk


    def apply_timeDelay_dist(self, idOpti:int=1, idLauncher:int=0, junctionKey:str=""):

        curRef:Catchment = self.myCases[idLauncher].refCatchment

        if curRef.myModel == cst.tom_2layers_linIF or curRef.myModel == cst.tom_2layers_UH:
            curRef.set_timeDelays(method="wolf_array", junctionKey=junctionKey, updateAll=True)

        # Write all the timeDelays in files
        curRef.save_timeDelays([junctionKey])


    def update_time_delays(self, idOpti:int=1, idLauncher:int=0):
        self.dllFortran.update_time_delay_py.restype = ct.c_int
        self.dllFortran.update_time_delay_py.argtypes = [ct.POINTER(ct.c_int), ct.POINTER(ct.c_int)]
        # call of the Fortran function
        isOk = self.dllFortran.update_time_delay_py(ct.byref(ct.c_int(idOpti)),ct.byref(ct.c_int(idLauncher+1)))

        return isOk


    ## Update the dictionnaries of myParams if any changes is identified
    # TODO : Generalised for all type of changes and all the necessary tests -> So far just update the junction name
    def update_myParams(self, idLauncher=0):
        curCatch:Catchment

        curCatch = self.myCases[idLauncher].refCatchment
        launcher_param = self.myCases[idLauncher].launcherParam

        for i in range(1,self.nbParams+1):
            curParam = "param_" + str(i)

            sorted_id = int(launcher_param.get_param(curParam, "Subbasin id", default_value=0))
            if sorted_id == 0:
                self.myParams[i]["junction_name"] = curCatch.junctionOut
            else:
                cur_id = list(curCatch.dictIdConversion.keys())[list(curCatch.dictIdConversion.values()).index(sorted_id)]
                self.myParams[i]["junction_name"] = curCatch.subBasinDict[cur_id].name



    ## Function to determine the compare stations, compare files and the compare station SubBasin objects for each station
    def set_compare_stations(self, idLauncher):

        if (self.optiParam.get_group("Semi-Distributed"))!=None:
            refCatch = self.myCases[idLauncher].refCatchment
            nbRefs = self.optiParam.get_param("Semi-Distributed","nb")

            readDict = {}
            # Read all ref data
            for iRef in range(1, nbRefs+1):
                stationOut = self.optiParam.get_param("Semi-Distributed","Station measures "+str(iRef))
                compareFileName = self.optiParam.get_param("Semi-Distributed","File reference "+str(iRef))
                readDict[stationOut] = compareFileName
            self.compareFilesDict = readDict
            # Sort all the junctions by level
            self.myStations = refCatch.sort_level_given_junctions(list(readDict.keys()), changeNames=False)
            # Prepare the SubBasin compare objects for each station.
            self.compareSubBasins = {stationOut: SubBasin(name=stationOut, _model=cst.compare_opti, _workingDir=self.workingDir)
                                     for stationOut in self.myStations}
            # This loop read all the measure and init the hydro surface of each SubBasin element
            for key, cur_obj in self.compareSubBasins.items():
                tmp, cur_obj.myHydro = cur_obj.get_hydro(1, workingDir=self.workingDir, fileNames=readDict[key])
                keyBasin = refCatch.get_key_catchmentDict(key)
                cur_basin = refCatch.catchmentDict[keyBasin]
                cur_obj.surfaceDrained = cur_basin.surfaceDrainedHydro
                cur_obj.surfaceDrainedHydro = cur_basin.surfaceDrainedHydro
                cur_obj.compute_hydro()
                # FIXME : generalise this verification or allow the measurements to adapt or build themselves correctly !!!
                # assert cur_obj.dateBegin==refCatch.dateBegin and cur_obj.dateEnd==refCatch.dateEnd, "The measures and simulations does not have compatible intervals!"


    def destroyOpti(self, event):
        for element in self.myCases:
            element.mydro.Destroy()
            element.Destroy()
        self.Destroy()

        wx.Exit()


    def get_all_outlets(self, event, idLauncher:int=0):
        # this function will save all the hydrographs with the optimal parameters

        refCatch:Catchment = self.myCases[idLauncher].refCatchment
        refCatch.save_ExcelFile_noLagTime()


    def write_all_inlets(self,event, idLauncher:int=0):
        # this function will save the hydrographs and the inlets with the optimal parameters
        refCatch:Catchment = self.myCases[idLauncher].refCatchment
        refCatch.save_ExcelFile_inlets_noLagTime()


    def plot_all_landuses(self, event, idLauncher:int=0):
        # this function plots the landuses of all hydro subbasins
        refCatch:Catchment = self.myCases[idLauncher].refCatchment
        refCatch.plot_landuses(onlySub=True, show=True)


    def plot_all_landuses_hydro(self, event, idLauncher:int=0):
        # this function plots the landuses of all hydro subbasins
        refCatch:Catchment = self.myCases[idLauncher].refCatchment
        refCatch.plot_landuses(onlySub=False, show=True)


    ## Apply the best parameters of an optimisation which implies that :
    #   - the ".rpt" file of the results of an optimisation should be present
    #   - the optimal paramters will be replaced in their respective param files
    #   - the timeDelays will then be updated either with :
    #           - Python paramters itself
    #           - an estimation from the runnof model
    # Once all the optimal parameters are applied, a new simulation is launched to generate the "best" hydrograph
    def generate_semiDist_optim_simul(self, event, idOpti=1,idLauncher:int=0):

        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        if(self.optiParam.get_group("Semi-Distributed"))is not None:
            nbRefs = self.optiParam.get_param("Semi-Distributed","nb")
            onlyOwnSub = self.optiParam.get_param("Semi-Distributed", "Own_SubBasin")
            if onlyOwnSub is None:
                onlyOwnSub = False
            doneList = []
            sortJct = []
            readDict = {}
            # Read all ref data
            for iRef in range(1, nbRefs+1):
                stationOut = self.optiParam.get_param("Semi-Distributed","Station measures "+str(iRef))
                compareFileName = self.optiParam.get_param("Semi-Distributed","File reference "+str(iRef))
                readDict[stationOut] = compareFileName
            self.compareFilesDict = readDict
            # Sort all the junctions by level
            sortJct = curCatch.sort_level_given_junctions(list(readDict.keys()), changeNames=False)
            self.myStations = sortJct

            for iOpti in range(len(sortJct)):
                stationOut = sortJct[iOpti]
                compareFileName = readDict[stationOut]
                # Copy the correct compare.txt file
                shutil.copyfile(self.workingDir / compareFileName, self.workingDir /"compare.txt")
                # Save the name of the station that will be the output
                curCatch.define_station_out(stationOut)
                # Activate all the useful subs and write it in the param file
                curCatch.activate_usefulSubs(blockJunction=doneList, onlyItself=onlyOwnSub)
                # Rename the result file
                self.optiParam.change_param("Optimizer", "fname", stationOut)
                self.optiParam.SavetoFile(None)
                self.optiParam.Reload(None)
                #
                self.update_myParams(idLauncher)
                # Preparing the dictionnaries of Parameters to be updated -> not just useful for calibration here !
                self.prepare_calibration_timeDelay(stationOut=stationOut)
                # Fill the param files with their best values
                self.apply_optim(None)
                # Simulation with the best parameters
                self.compute_distributed_hydro_model()
                # Update myHydro of all effective subbasins to get the best configuration upstream
                curCatch.read_hydro_eff_subBasin()
                # Update timeDelays according to time wolf_array
                self.apply_timeDelay_dist(idOpti=idOpti, idLauncher=idLauncher, junctionKey=stationOut)
                # Update the outflows
                curCatch.update_hydro(idCompar=0)
                # All upstream elements of a reference will be fixed
                doneList.append(stationOut)


    def generate_semiDist_debug_simul(self, event, idOpti=1,idLauncher:int=0):

        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        if(self.optiParam.get_group("Semi-Distributed"))is not None:
            nbRefs = self.optiParam.get_param("Semi-Distributed","nb")
            onlyOwnSub = self.optiParam.get_param("Semi-Distributed", "Own_SubBasin")
            if onlyOwnSub is None:
                onlyOwnSub = False
            doneList = []
            sortJct = []
            readDict = {}
            # Read all ref data
            for iRef in range(1, nbRefs+1):
                stationOut = self.optiParam.get_param("Semi-Distributed","Station measures "+str(iRef))
                compareFileName = self.optiParam.get_param("Semi-Distributed","File reference "+str(iRef))
                readDict[stationOut] = compareFileName
            self.compareFilesDict = readDict
            # Sort all the junctions by level
            sortJct = curCatch.sort_level_given_junctions(list(readDict.keys()), changeNames=False)
            self.myStations = sortJct

            for iOpti in range(len(sortJct)):
                stationOut = sortJct[iOpti]
                compareFileName = readDict[stationOut]
                # Copy the correct compare.txt file
                shutil.copyfile(self.workingDir / compareFileName, self.workingDir /"compare.txt")
                # Save the name of the station that will be the output
                curCatch.define_station_out(stationOut)
                # Activate all the useful subs and write it in the param file
                curCatch.activate_usefulSubs(blockJunction=doneList, onlyItself=onlyOwnSub)
                # Rename the result file
                self.optiParam.change_param("Optimizer", "fname", stationOut)
                self.optiParam.SavetoFile(None)
                self.optiParam.Reload(None)
                #
                self.update_myParams(idLauncher)
                # TO DO -> adapt all the debug_info files
                # write it here !!!!

                # ====
                # Fill the param files and generate all their best configurations
                self.apply_all_tests(idLauncher)
                # Check with a reference
                # TO DO !!!!!

                # All upstream elements of a reference will be fixed
                doneList.append(stationOut)


    def read_all_attempts_SA(self, format="rpt", all_attempts=False, filter_repetitions=True, stationOut:str=""):

        if stationOut=="":
            nameTMP = self.optiParam.get_param("Optimizer","fname")
        else:
            nameTMP = stationOut

        if all_attempts:
            nb_iter_from_random = self.optiParam.get_param("Optimizer","nb iter from random initial conditions",
                                                       default_value=1)
            nb_iter_from_best = self.optiParam.get_param("Optimizer","nb iter from best",
                                                     default_value=1)
            nb_attempts = nb_iter_from_random * nb_iter_from_best
            all_names = [nameTMP+"_"+str(i+1) for i in range(nb_attempts)]
        else:
            all_names = [nameTMP]

        matrixParam = np.empty((0, self.nbParams), dtype="double")
        vectorObjFct = np.empty((0,), dtype="double")

        if format=="rpt":
            for cur_file in all_names:
                optimFile = self.workingDir / (cur_file+".rpt")

                try:
                    with open(optimFile, newline = '') as fileID:
                        data_reader = csv.reader(fileID, delimiter='|',skipinitialspace=True, )
                        list_param = []
                        list_ObjFct = []
                        line = 0
                        for raw in data_reader:
                            if(line<3):
                                line += 1
                                continue
                            if(len(raw)<=1):
                                break
                            else:
                                usefulData = raw[2:-2]
                                list_param.append(usefulData)
                                list_ObjFct.append(raw[-2])
                            line += 1
                    matrixParam = np.vstack((matrixParam,
                                            np.array(list_param).astype("double")))
                    vectorObjFct = np.append(vectorObjFct,
                                            np.array(list_ObjFct).astype("double"))
                except:
                    wx.MessageBox(_('The best parameters file is not found!'), _('Error'), wx.OK|wx.ICON_ERROR)

        elif format==".dat":
            for cur_file in all_names:
                optimFile = self.workingDir / (cur_file+".rpt.dat")
                isOk, optimFile = check_path(optimFile)
                if isOk>0:
                    allData = read_bin(self.workingDir, cur_file+".rpt.dat", uniform_format=8)
                    allData = np.array(allData).astype("double")
                    matrixParam = np.vstack((matrixParam, allData[:-1,:-1]))
                    vectorObjFct = np.append(vectorObjFct, allData[:-1,-1])

        if filter_repetitions:
            logging.info("Filtering the repetitions in the attempts!")
            filter_matrix, indices, inverse, counts = np.unique(matrixParam, axis=0,
                                                                return_index=True,
                                                                return_inverse=True,
                                                                return_counts=True)
            vectorObjFct = vectorObjFct[indices]
            matrixParam = filter_matrix
            logging.info("The max number of repetitions = "+ str(np.max(counts)))

        return matrixParam, vectorObjFct


    def apply_optim_2_params(self, params:np.array, idLauncher=0):

        refCatch:Catchment = self.myCases[idLauncher].refCatchment
        myModel = refCatch.myModel

        if self.curParams_vec_F is None \
            or len(self.curParams_vec_F) != self.nbParams:

            self.curParams_vec_F = np.empty((self.nbParams,), dtype=ct.c_double, order='F')

        myModelDict = cste.modelParamsDict[myModel]["Parameters"]

        for cur_effsub in range(len(refCatch.myEffSubBasins)):

            filePath = os.path.join(refCatch.workingDir, "Subbasin_" + str(refCatch.myEffSortSubBasins[cur_effsub]))

            for i in range(self.nbParams):
                myType = self.myParams[i+1]["type"]
                if(int(myType)>0):
                    # If the parameter is not for the current effective subbasin
                    # then we skip it
                    if "junction_name" in self.myParams[i+1]:
                        cur_sub = refCatch.catchmentDict[refCatch.get_key_catchmentDict(self.myParams[i+1]["junction_name"])]
                        if cur_sub.iDSorted != refCatch.myEffSortSubBasins[cur_effsub]:
                            continue
                    self.myParams[i+1]["value"] = params[i]

                    all_files = myModelDict[int(myType)]["File"]
                    if type(all_files) is not list:
                        # Extract the unit conversion factor
                        if "Convertion Factor" in myModelDict[int(myType)]:
                            convFact = myModelDict[int(myType)]["Convertion Factor"]
                        else:
                            convFact = 1.0
                        fileName = myModelDict[int(myType)]["File"]
                        myGroup = myModelDict[int(myType)]["Group"]
                        myKey = myModelDict[int(myType)]["Key"]
                        self.write_one_opti_param(filePath, fileName, myGroup, myKey, params[i], convers_factor=convFact)
                    else:
                        # Extract the unit conversion factor in a list which is the same size as the number of files
                        if "Convertion Factor" in myModelDict[int(myType)]:
                            convFact = myModelDict[int(myType)]["Convertion Factor"]
                        else:
                            convFact = [1.0]*len(all_files)
                        # Iterate over all the files to fill for one parameter
                        for iFile in range(len(all_files)):
                            fileName = all_files[iFile]
                            myGroup = myModelDict[int(myType)]["Group"][iFile]
                            myKey = myModelDict[int(myType)]["Key"][iFile]
                            self.write_one_opti_param(filePath, fileName, myGroup, myKey, params[i], convers_factor=convFact[iFile])
                else:
                    self.curParams_vec_F[i] = params[i]
                    self.update_timeDelay(i+1)
                    refCatch.save_timeDelays([self.myParams[i+1]["junction_name"]])
                    print("TO DO : Complete the python parameter dict!!!!!!!")



    def apply_all_tests(self, idLauncher=0):

        refCatch:Catchment = self.myCases[idLauncher].refCatchment

        # Get all the tested parameters
        allParams, objFct = self.read_all_attempts_SA()

        for i in range(len(allParams)):
            curParams = allParams[i]
            self.apply_optim_2_params(curParams, idLauncher=idLauncher)

            # Simulation with the best parameters
            self.compute_distributed_hydro_model()
            # Update myHydro of all effective subbasins to get the best configuration upstream
            refCatch.read_hydro_eff_subBasin()
            # Update the outflows
            refCatch.update_hydro(idCompar=0)



    def remove_py_params(self, idLauncher:int=0):
            """
            Removes the Python parameters from the optimization configuration.

            Args:
                idLauncher (int, optional): The ID of the launcher. Defaults to 0.
            """
            cur_opti = self.myCases[idLauncher]
            paramDict = cur_opti.launcherParam
            nb_params = int(paramDict.get_param("Paramètres à varier", "Nombre de paramètres à varier"))

            myModel = self.myCases[idLauncher].refCatchment.myModel
            nbParamsModel = cste.modelParamsDict[myModel]["Nb"]*len(cur_opti.refCatchment.myEffSubBasins)

            for i in range(1,nb_params+1):
                curParam = "param_" + str(i)
                curType = int(paramDict.get_param(curParam, "type_of_data"))
                if curType < 0:
                    del paramDict.myparams[curParam]
                    nb_params -= 1

            # Test
            # assert nb_params > nbParamsModel, "The number of parameters to optimize is not equal to the number of parameters of the model!"
            if nb_params >  nbParamsModel:
                logging.error("The number of to optimise are greater than the number of max parameter of the model!! ")
                assert nb_params > nbParamsModel, "The number of parameters to optimize is not equal to the number of parameters of the model!"
                return

            self.myCases[idLauncher].launcherParam.change_param("Paramètres à varier", "Nombre de paramètres à varier", nb_params)

            return


    def _read_opti_intervals(self, idLauncher:int=0)->list[tuple[datetime.datetime, datetime.datetime]]:
        """
        .. todo::
            - Add the measure of the comparison file in properties of the object opti
            - Check according to the current Observation, which comparision intervals are posssible -> and sort them
            - Save the comparison intervals somewhere
            - Save the useful comparison intervals somewhere
            - Return the useful intervals.
        """
        # file_compare = os.path.join(self.workingDir,"compare.txt")
        # isOk, file_compare = check_path(file_compare)
        # if isOk<0:
        #     logging.error("The file compare.txt is not found!")
        #     return

        # Read the comparison file
        if self.myStations==[]:
            self.set_compare_stations(idLauncher=idLauncher)

        nb_comparison = self.comparHowParam.get_param("Comparison global characteristics", "nb")
        str_di = "date begin"
        str_df = "date end"

        intervals = []
        for icomp in range(1, nb_comparison+1):
            cur_key = " ".join(["Comparison", str(icomp)])
            nb_intervals = self.comparHowParam.get_param(cur_key, "nb intervals")
            for i_inter in range(1,nb_intervals+1):
                str_read = self.comparHowParam.get_param(cur_key, " ".join([str_di,str(i_inter)]))
                di = datetime.datetime.strptime(str_read, cst.DATE_FORMAT_HYDRO).replace(tzinfo=datetime.timezone.utc)
                str_read = self.comparHowParam.get_param(cur_key," ".join([str_df,str(i_inter)]))
                df = datetime.datetime.strptime(str_read, cst.DATE_FORMAT_HYDRO).replace(tzinfo=datetime.timezone.utc)
                # Check that di is a timestamp lower than other date #FIXME : to be transfer in a test function !!!!
                if di>df:
                    logging.error("The date end is lower than the date begin!")
                    return None
                else:
                    intervals.append((di,df))


        return intervals


    def _save_opti_intervals(self, idLauncher:int=0, stationOut:str="",
                             intervals:list[tuple[datetime.datetime, datetime.datetime]]=None)->int:
        if stationOut == "":
            suffix = "0"
        else:
            suffix = stationOut

        if intervals is None:
            self.all_intervals = self._read_opti_intervals(idLauncher=idLauncher)

        compare_file = self.workingDir / "compare.how.param"

        # In case of a problem, the initial compare file is copied
        compare_file_cp = self.workingDir / ("compare.how_"+suffix+"_tmp.param")
        isOk, compare_file_cp = check_path(compare_file_cp)
        if isOk<0 and stationOut=="":
            compare_file_cp = self.workingDir / ("compare.how_"+suffix+".param")
            shutil.copyfile(compare_file, compare_file_cp)
            logging.info(_("The following file has been copied : "), compare_file_cp)
        else:
            shutil.copyfile(compare_file, compare_file_cp)
            logging.info(_("The following file has been copied : %s"), compare_file_cp)

        if self.all_intervals is None:
            return -1
        else:
            return 0


    def select_opti_intervals(self, all_intervals:list[tuple[datetime.datetime, datetime.datetime]]=None,
                              idLauncher:int=0, stationOut="", filter_nan:bool=True)->list[tuple]:
        """
        .. todo::
            - Add the measure of the comparison file in properties of the object opti
            - Check according to the current Observation, which comparision intervals are posssible -> and sort them
            - Save the comparison intervals somewhere
            - Save the useful comparison intervals somewhere
            - Return the useful intervals.
        """
        cur_opti = self.myCases[idLauncher]
        cur_ref = cur_opti.refCatchment

        if stationOut == "":
            stationOut = cur_ref.junctionOut

        if all_intervals is None:
            if self.all_intervals is None:
                logging.error("The intervlas are not defined! Please add them in the function arguments or use the funcion '_save_opti_intervals()' to save them internally (at your own risk!)")
                # id_ok= self._save_opti_intervals(idLauncher=idLauncher)
                # if id_ok<0:
                #     return None

            else:
                all_intervals = self.all_intervals

        if self.myStations==[]:
            self.set_compare_stations(idLauncher=idLauncher)

        keyBasin = cur_ref.get_key_catchmentDict(stationOut)
        cur_basin = cur_ref.catchmentDict[keyBasin]

        # Select the optimisation intervals that are relevant according to the available measures
        # effective_intv = [interv for interv in all_intervals if interv[0]>=cur_basin.dateBegin and interv[1]<=cur_basin.dateEnd]
        effective_intv = self._intersect_intervals(all_intervals, (cur_basin.dateBegin, cur_basin.dateEnd))
        if filter_nan:
            effective_intv = self._define_intervals_with_nan_measures(effective_intv, self.compareSubBasins,
                                                                      idLauncher=idLauncher, stationOut=stationOut)
            effective_intv = self._define_intervals_with_nan_inlets(effective_intv, {cur_basin.name: cur_basin},
                                                                    idLauncher=idLauncher, stationOut=stationOut)
        return effective_intv


    def _define_intervals_with_ts(self, intervals: list[tuple[datetime.datetime, datetime.datetime]], time:np.ndarray, ts:np.ndarray, idLauncher: int = 0):
        """
        Defines new intervals excluding all NaN measures based on the given intervals and measures dictionary.
        For instance, if there is continuous NaN measures within a given interval, the function will split
        that interval into smaller that do not contain NaN measures.

        Args:
            intervals (list[tuple[datetime.datetime, datetime.datetime]]): A list of intervals represented as tuples of start and end datetime objects.
            ts (dict[str, SubBasin]): A dictionary of time series where the keys are station names and the values are vectors of numpy array.
            idLauncher (int, optional): The id of the launcher. Defaults to 0.
            stationOut (str, optional): The station name. Defaults to "".

        Returns:
            list[tuple[datetime.datetime, datetime.datetime]]: A list of intervals with NaN measures.

        Raises:
            None

        """

        # get the indices of the nan values
        non_nan_locations = ~np.isnan(ts)
        within_intervals = np.sum(
            [(time >= datetime.datetime.timestamp(interv[0])) *
             (time <= datetime.datetime.timestamp(interv[1]))
             for interv in intervals],
            axis=0) > 0
        # Both conditions should be satisfied
        all_conditions = np.where(non_nan_locations * within_intervals)[0]

        # Check all the discontinuities and the indices they start
        # i.e. when the index difference is not 1
        # +1 as the np.diff is one element sooner than nan_locations: diff[0]=v[1]-v[0]
        group_starts = np.where(np.diff(all_conditions) != 1)[0] + 1

        # Add 0 as it is the first index of the first group
        group_starts = np.insert(group_starts, 0, 0)

        # Identify where the groups stop.
        group_ends = np.append(group_starts[1:] - 1, len(all_conditions)-1)

        # Get the timestamps of the first and last nan element and form groups of discontinuities
        iterv_timestamp = [(time[all_conditions[i_i]], time[all_conditions[i_f]]) for i_i, i_f in zip(group_starts, group_ends)]
        interv_dates = [(datetime.datetime.fromtimestamp(iterv[0],tz=datetime.timezone.utc),
                         datetime.datetime.fromtimestamp(iterv[1], tz=datetime.timezone.utc))
                         for iterv in iterv_timestamp]

        return interv_dates


    def _define_intervals_with_nan_inlets(self, intervals: list[tuple[datetime.datetime, datetime.datetime]], measures: dict[str, SubBasin],
                                            idLauncher: int = 0, stationOut: str = ""):
        """
        Defines new intervals excluding all NaN measures based on the given intervals and measures dictionary.
        For instance, if there is continuous NaN measures within a given interval, the function will split
        that interval into smaller that do not contain NaN measures.

        Args:
            intervals (list[tuple[datetime.datetime, datetime.datetime]]): A list of intervals represented as tuples of start and end datetime objects.
            measures (dict[str, SubBasin]): A dictionary of measures where the keys are station names and the values are SubBasin objects.
            idLauncher (int, optional): The id of the launcher. Defaults to 0.
            stationOut (str, optional): The station name. Defaults to "".

        Returns:
            list[tuple[datetime.datetime, datetime.datetime]]: A list of intervals with NaN measures.

        Raises:
            None

        """
        if stationOut not in measures:
            logging.error("The stationOut is not in the measures dictionary!")
            return None

        cur_el = measures[stationOut]
        hydro = cur_el.get_inlets()
        time = cur_el.time

        return self._define_intervals_with_ts(intervals, time, hydro, idLauncher=idLauncher)


    def _define_intervals_with_nan_measures(self, intervals: list[tuple[datetime.datetime, datetime.datetime]], measures: dict[str, SubBasin],
                                            idLauncher: int = 0, stationOut: str = ""):
        """
        Defines new intervals excluding all NaN measures based on the given intervals and measures dictionary.
        For instance, if there is continuous NaN measures within a given interval, the function will split
        that interval into smaller that do not contain NaN measures.

        Args:
            intervals (list[tuple[datetime.datetime, datetime.datetime]]): A list of intervals represented as tuples of start and end datetime objects.
            measures (dict[str, SubBasin]): A dictionary of measures where the keys are station names and the values are SubBasin objects.
            idLauncher (int, optional): The id of the launcher. Defaults to 0.
            stationOut (str, optional): The station name. Defaults to "".

        Returns:
            list[tuple[datetime.datetime, datetime.datetime]]: A list of intervals with NaN measures.

        Raises:
            None

        """
        if stationOut not in measures:
            logging.error("The stationOut is not in the measures dictionary!")
            return None

        cur_el = measures[stationOut]
        hydro = cur_el.get_myHydro()
        time = cur_el.time

        return self._define_intervals_with_ts(intervals, time, hydro, idLauncher=idLauncher)


    def save_opti_dates_to_file(self, opti_dates:list[tuple[datetime.datetime,datetime.datetime]]):
        """
        Here the procedure is saving the intervals of dates for calibration in the compare.how.param
        """
        # Verifications
        assert len(opti_dates)>0, "The list of dates is empty!"
        for i_opti in opti_dates:
            assert i_opti[1]>i_opti[0], "The start date is not lower than the end date!"

        nb_comparison = self.comparHowParam.get_param("Comparison global characteristics", "nb")

        str_di = "date begin"
        str_df = "date end"

        for icomp in range(1, nb_comparison+1):
            cur_key = " ".join(["Comparison", str(icomp)])
            nb_intervals = len(opti_dates)
            self.comparHowParam.change_param(cur_key, "nb intervals", nb_intervals)
            for i_inter in range(1,nb_intervals+1):
                di = datetime.datetime.strftime(opti_dates[i_inter-1][0], cst.DATE_FORMAT_HYDRO)
                df = datetime.datetime.strftime(opti_dates[i_inter-1][1], cst.DATE_FORMAT_HYDRO)
                # FIXME : Change addparam to add_param
                self.comparHowParam.addparam(cur_key, " ".join([str_di,str(i_inter)]), di, type="str")
                self.comparHowParam.addparam(cur_key, " ".join([str_df,str(i_inter)]), df, type="str")

        self.comparHowParam.SavetoFile(None)
        self.comparHowParam.Reload(None)


    def prepare_init_params_from_best(self, best_params:np.array, idLauncher:int=0):
        # If there are no best params the initial values will be random
        if best_params is None:
            # Force the initial parameters to be defined randomly
            self.saParam.change_param("Initial parameters", "Read initial parameters?", 0)
            return

        # In the following code, we apply the best parameters to the initial parameters
        self.saParam.change_param("Initial parameters", "Read initial parameters?", 1)
        for i in range(self.nbParams):
            self.saParam.change_param("Initial parameters", " ".join(["Parameter",str(i+1)]), best_params[i])

        self.saParam.SavetoFile(None)
        self.saParam.Reload(None)


    def get_initial_parameters(self)-> np.array:
        read_IP = self.saParam.get_param("Initial parameters", "Read initial parameters?")
        if read_IP == 1:
            # FIXME : Generalise for more than 1 objctive function
            init_params = np.zeros(self.nbParams+1)
            for i in range(self.nbParams):
                init_params[i] = self.saParam.get_param("Initial parameters", " ".join(["Parameter",str(i+1)]))
            init_params[-1] = -sys.float_info.max
        else:
            init_params = None

        return init_params


    def reset_init_params(self, init_params:np.array):
        if init_params is None:
            return
        for i in range(self.nbParams):
            self.saParam.change_param("Initial parameters", " ".join(["Parameter",str(i+1)]), init_params[i])
        logging.info(_("Reset init params : %s"), init_params)
        self.saParam.SavetoFile(None)
        self.saParam.Reload(None)


    def extract_internal_variables(self, event, idLauncher:int=0, to_plot:bool=True):
        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        ## Check the relevance to launch the detailed simulation to extract the internal variables
        all_x = curCatch.get_all_x_production()
        all_iv = curCatch.get_all_iv_production()
        # Graphical interface to ask the user if he wants to launch the detailed simulation
        if all_x=={} or all_iv=={}:
            to_generate = True
            if self.wx_exists:
                dlg = wx.MessageDialog(None, "No internal variables were detected! Do you want to launch a detailed simulation ?", "Warning", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                r = dlg.ShowModal()
                if r == wx.ID_YES:
                    to_generate = True
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return None
            else:
                to_generate = True
        else:
            to_generate = False
            if self.wx_exists:
                dlg = wx.MessageDialog(None, "Internal variables were detected! Do you still want to launch a detailed simulation ?", "Warning", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                r = dlg.ShowModal()
                if r == wx.ID_YES:
                    to_generate = True
                dlg.Destroy()
                # FIXME :  ADD the terminal
            else:
                to_generate = False
        # Enter here if a detailed simulation is required
        if to_generate:
            curCatch.activate_all_internal_variables()
            self.generate_semiDist_optim_simul(None, idLauncher=idLauncher)
            all_x = curCatch.get_all_x_production()
            all_iv = curCatch.get_all_iv_production()

        effective_intv = self.select_opti_intervals(idLauncher=idLauncher, stationOut="")
        all_Nash = {"Nash" : self.get_all_Nash()}
        all_frac = curCatch.get_all_fractions(summary="mean", summary_interval=effective_intv, add_info=all_Nash)


        if to_plot:
            for interv in effective_intv:
                all_frac = curCatch.plot_all_fractions(all_fractions=all_frac, to_show=True, range_data=list(interv))

        return all_x, all_iv, all_frac


    def _check_presence_of_iv(self, idLauncher:int=0):
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        return curCatch.check_presence_of_iv()


    def plot_Nash_vs_Qexcess(self, event, idLauncher:int=0):
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        all_params, all_nash = self.read_all_attempts_SA(format=".dat")
        nb_tests = np.shape(all_nash)[0]

        if self.myStations==[]:
            self.set_compare_stations(idLauncher=idLauncher)

        compMeas = []
        for iOpti in range(len(self.myStations)):
            dateBegin = curCatch.dateBegin
            dateEnd = curCatch.dateEnd
            deltaT = curCatch.deltaT # [sec]
            stationOut = self.myStations[iOpti]
            compareFileName = self.compareFilesDict[stationOut]
            dir_Meas = self.workingDir
            compMeas.append(SubBasin(dateBegin, dateEnd, deltaT, cst.compare_opti, dir_Meas))
            _,cur_comp = compMeas[iOpti].get_hydro(1, workingDir=dir_Meas, fileNames=compareFileName)
            keyBasin = curCatch.get_key_catchmentDict(stationOut)
            cur_basin = curCatch.catchmentDict[keyBasin]
            cur_comp = cur_comp*cur_basin.surfaceDrained/3.6
            all_qtests = curCatch.get_all_Qtest(nb_atttempts=nb_tests, selection_by_iD=[stationOut])
            # FIXME : Check the type of interpolation to use
            interp_qcomp = np.interp(curCatch.time, compMeas[iOpti].time, cur_comp)
            q_diff = np.array([np.count_nonzero((qtest-interp_qcomp <0.0) & (qtest != 0.0))/np.count_nonzero((qtest != 0.0))
                               for qtest in all_qtests[0]])
            fig, ax = plt.subplots()
            for i in range(nb_tests-1):
                ax.scatter(q_diff[i], all_nash[i], s=0.5, c='b', marker='o', alpha=i/nb_tests)
            ax.scatter(q_diff[-1], all_nash[-1], s=0.5, c='b', marker='o', label="test", alpha=1)
            # ax.scatter(q_diff, all_nash, s=0.5, c='b', marker='o', label="test")
            ax.set_xlabel("Non-exceedance fraction. Portion of the observations below the simulated series (Qs>Qo)")
            ax.set_ylabel("Nash-Sutcliffe efficiency")
            ax.set_ylim(1.0, -1.0)
            ax.set_xlim(0.0, 1.0)

            i_best = np.argmax(all_nash)

            ax.scatter(q_diff[i_best], all_nash[i_best], color='red', s=30, label="Best Nash")
            ax.set_title("2000-2011 GR4H "+stationOut)
            ax.legend()
            fig.savefig(os.path.join(curCatch.workingDir, "PostProcess/Nash_vs_Qexcess_"+stationOut+".png"))


        plt.show()


    def get_all_Nash(self):

        return {cur_file: self.collect_optim(cur_file)[-1] for cur_file in self.myStations}

    # FIXME this function is not correct -> to be corrected and delete the remove_py_params and updtate_myParams calls
    def get_all_params(self, idLauncher:int=0):
        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        hydro_model = curCatch.myModel

        # Read the comparison file
        if self.myStations==[]:
            self.set_compare_stations(idLauncher=idLauncher)

        calibrate_timeDelay = bool(int(self.optiParam.get_param("Semi-Distributed", "Calibrate_times")))
        myModelDict = cste.modelParamsDict[hydro_model]["Parameters"]

        all_names = {}
        for stationOut in self.myStations:
            curCatch.define_station_out(stationOut)
            self.remove_py_params(idLauncher)
            self.update_myParams(idLauncher)

            id_params = [self.myParams[i]["type"] for i in range(1,self.nbParams+1)]
            names = [myModelDict[cur_id]["Name"] for cur_id in id_params if cur_id>0]
            all_names[stationOut] = names
            if calibrate_timeDelay:
                # Get_nb inlets
                inletsNames = self.myCases[idLauncher].refCatchment.get_inletsName(stationOut)
                nbInlets = len(inletsNames)
                for i in range(nbInlets):
                    names.append("TimeDelay "+inletsNames[i])
            # Complete the names according to the stations concerned

        optim = {cur_file: self.collect_optim(cur_file) for cur_file in self.myStations}

        # all_params = {}
        # for key, value in optim.items():
        #     all_params[key] = {}
        #     for i, cur_name in enumerate(all_names):
        #         all_params[key][cur_name] = value[i]

        all_params = {key:
                      {cur_name : value[i] for i, cur_name in enumerate(all_names)}
                      for key, value in optim.items()}

        return all_params


    def save_all_params(self, all_params:dict={}, idLauncher:int=0):

        all_keys = list(all_params.keys())

        return


    def save_current_compare_file(self, stationOut: str):
        """
        Save the current compare file for a given station to prepare optimisation with Fortran.

        Args:
            stationOut (str): The station identifier.

        Returns:
            None

        Raises:
            None
        """
        compare_file_name = self.compareFilesDict[stationOut]
        cur_sub = self.compareSubBasins[stationOut]

        time = cur_sub.time
        hydro = cur_sub.get_myHydro()
        hydro = np.nan_to_num(hydro, nan=0.0)

        data = np.column_stack((time, hydro))
        # Define header
        header = f"{data.shape[0]:d}\t{data.shape[1]:d}"
        # Write to file
        np.savetxt(
            self.workingDir / "compare.txt",
            data,
            header=header,
            fmt=["%d", "%e"],
            comments="",
            delimiter="\t",
        )


    def prepare_simulation(self, opti_intervals:list[tuple[datetime.datetime, datetime.datetime]],
                           idLauncher:int=0):

        cur_catch = self.myCases[idLauncher].refCatchment
        # TODO : Create an object hydro intervals with activate property and a method to retrun a list of tuples
        simul_intevals = cur_catch.simulation_intervals
        # See which simulation intervals should be activated
        eff_simul_intervals = []
        for simul_intrv in simul_intevals:
            to_activate = False
            for cur_opti_intrv in opti_intervals:
                if cur_opti_intrv[0]>simul_intrv[0] and cur_opti_intrv[1]<simul_intrv[1]:
                    to_activate = True
                    break
            if to_activate:
                eff_simul_intervals.append(simul_intrv)

        cur_catch.simulation_intervals = eff_simul_intervals

        return


    def reset_simulation_intervals(self, default_interval:list[tuple[datetime.datetime, datetime.datetime]],
                                   idLauncher:int=0):

        cur_catch = self.myCases[idLauncher].refCatchment
        cur_catch.simulation_intervals = default_interval

        return

    # FIXME : this function has been dashed off -> functionnal but not well written!!
    # TODO : to improve !!!!!!
    def test_equifinality_with_Nash(self, event, idLauncher:int=0, idOpti:int=1, quantile_Nash:float=0.01, std_Nash:float=0.3, clustering_Nash:bool=True):
        """
        Test the equifinality of the model.

        Args:
            idLauncher (int, optional): The id of the launcher. Defaults to 0.

        Returns:
            None

        Raises:
            None
        """
        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        onlyOwnSub = self.optiParam.get_param("Semi-Distributed", "Own_SubBasin")
        if onlyOwnSub is None:
            onlyOwnSub = False
        doneList = []
        previousLevel = 1
        # Collect sort and save the compare stations
        self.set_compare_stations(idLauncher=idLauncher)
        sortJct = self.myStations
        # Get the initial number of intervals
        # -> these can evolve according to the measurement available at each station
        is_ok = self._save_opti_intervals()
        all_intervals = self.all_intervals
        # Activate the writing of the internal variables
        curCatch.activate_all_internal_variables()
        # Prepare the Excel writer
        writer_tot = pd.ExcelWriter(self.workingDir / "all_best_tests.xlsx", engine = 'xlsxwriter')

        for iOpti in range(len(sortJct)):
            stationOut = sortJct[iOpti]
            logging.info("==================")
            logging.info("Station : "+stationOut)
            # Build the current compare.txt file and replace all nan values by 0.0
            self.save_current_compare_file(stationOut=stationOut)
            # Save the name of the station that will be the output
            curCatch.define_station_out(stationOut)
            # Activate all the useful subs and write it in the param file
            curCatch.activate_usefulSubs(blockJunction=doneList, onlyItself=onlyOwnSub)
            # Rename the result file
            self.optiParam.change_param("Optimizer", "fname", stationOut)
            self.optiParam.SavetoFile(None)
            self.optiParam.Reload(None)
            self.update_myParams(idLauncher)
            # Prepare the paramPy dictionnary before calibration
            self.prepare_calibration_timeDelay(stationOut=stationOut)
            # Reload the useful modules
            self.reload_hydro(idCompar=0, fromStation=stationOut, lastLevel=previousLevel, updateAll=True)
            # Select correct calibration intervals -> remove the intervals with NaN
            cur_intervals = self.select_opti_intervals(all_intervals=all_intervals, stationOut=stationOut, filter_nan=True)
            self.save_opti_dates_to_file(cur_intervals)
            ## =======
            ## Init
            ## =======
            self.init_optimizer(idOpti)
            self.associate_ptr(None, idOpti=idOpti)
            # Get the best parameters to test
            all_params = self.get_best_params(stationOut=stationOut, quantile=quantile_Nash, std=std_Nash, apply_clustering=clustering_Nash)
            ## =======
            ## Compute
            ## =======
            all_frac = []

            for i in range(len(all_params)):
                cur_p = all_params[i, :-1]
                cur_obj = all_params[i, -1]
                cur_obj2 = self.evaluate_model_optimizer(cur_p, idOpti=idOpti)
                logging.info(_("cur_obj : %s ; cur_obj2 : %s"), cur_obj, cur_obj2)
                if cur_obj != cur_obj2:
                    logging.error("The objective function is not the same as the one computed by the model!")
                    logging.error("cur_obj : "+str(cur_obj)+" ; cur_obj2 : "+str(cur_obj2))
                # assert cur_obj == cur_obj2, "The objective function is not the same as the one computed by the model!"
                self.write_mesh_results_optimizer(idOpti=idOpti)
                # Save all the variables/evaluations desired
                frac_dict = self._get_cur_fractions(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                cur_all_frac = list(frac_dict.values())
                frac_vol_dict = self._get_volume_fractions(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                qof_max = self._get_max_runoff(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                p_excess = self._get_exceedance(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                max_sim_obs = self._get_ratio_max_sim_obs(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                # Extract the time delays
                all_timeDelays = curCatch.get_timeDelays_inlets(ref=stationOut)
                all_timeDelays_str = {key : str(datetime.timedelta(seconds=all_timeDelays[key])) for key in all_timeDelays}
                cur_timeDelays = list(all_timeDelays_str.values())
                # Concatenate all the informations
                cur_all_frac = list(cur_p) + cur_timeDelays + cur_all_frac + list(frac_vol_dict.values()) + [qof_max, p_excess, max_sim_obs, cur_obj]
                all_frac.append(cur_all_frac)

            # Get param names
            names = self.get_param_names(idLauncher=idLauncher, stationOut=stationOut)
            # Save the evaluations
            var_names = names \
                        + list(all_timeDelays_str.keys()) \
                        + list(frac_dict.keys()) \
                        + list(frac_vol_dict.keys()) \
                        + ["% max runoff", "P. of exceedance", "Qmax_simul/Q_max_measure", "Nash"]

            cur_df = pd.DataFrame(all_frac, columns=var_names)
            # write first the tempory results for each station
            writer_stat = pd.ExcelWriter(self.workingDir / (stationOut+"_tests.xlsx"), engine = 'xlsxwriter')
            cur_df.to_excel(writer_stat, sheet_name=stationOut, columns=var_names)
            writer_stat.sheets[stationOut].autofit()
            writer_stat.close()
            # write now the informations for all the stations in the same excel file
            cur_df.to_excel(writer_tot, sheet_name=stationOut, columns=var_names)
            writer_tot.sheets[stationOut].autofit()

            ## =======
            ## =======
            # Collect the best parameters and their objective function(s)
            best_params = self.apply_optim(None)
            # Simulation with the best parameters
            self.compute_distributed_hydro_model()
            # Update myHydro of all effective subbasins to get the best configuration upstream
            curCatch.read_hydro_eff_subBasin()
            # Update timeDelays according to time wolf_array
            self.apply_timeDelay_dist(idOpti=idOpti, idLauncher=idLauncher, junctionKey=stationOut)
            # Update the outflows
            curCatch.update_hydro(idCompar=0)

            # All upstream elements of a reference will be fixed
            doneList.append(stationOut)
            previousLevel = curCatch.levelOut

        writer_tot.close()
        logging.info("The equifinality test is finished!")


    def get_best_params(self, stationOut:str,
                        criterion:str="Nash", quantile:float=None, std:float=None, eps:float=0.2, rmv_near_max=None, nb_rand_close:int=10,
                        objective_fct:bool= True, apply_clustering:bool=False, objective_weight:float=1.0):
        from sklearn.cluster import DBSCAN
        """
        Get the best parameters for a given station.

        Args:
            stationOut (str): The station identifier.
            idLauncher (int, optional): The id of the launcher. Defaults to 0.

        Returns:
            np.array: The best parameters.

        Raises:
            None
        """

        best_objfct = self.collect_optim()[-1]
        all_params, all_obj_fct = self.read_all_attempts_SA(format=".dat", all_attempts=True)
        if quantile is not None:
            quantile_cond = (all_obj_fct > np.quantile(all_obj_fct, quantile))
        else:
            quantile_cond = np.ones_like(all_obj_fct, dtype=bool)
        if std is not None:
            std_cond = (all_obj_fct > best_objfct*(1-std))
        else:
            std_cond = np.ones_like(all_obj_fct, dtype=bool)
        if rmv_near_max is not None:
            tooclose_cond = (all_obj_fct < best_objfct*(1-rmv_near_max)) | (all_obj_fct == best_objfct)
        else:
            tooclose_cond = np.ones_like(all_obj_fct, dtype=bool)

        all_cond = np.where(quantile_cond & std_cond & tooclose_cond)[0]
        eff_params = all_params[all_cond]
        eff_obj = all_obj_fct[all_cond]

        if objective_fct:
            eff_params = np.column_stack((eff_params, eff_obj))
        # Select randomly the parameters that are close to the best one
        if nb_rand_close>0:
            close_params = all_params[~tooclose_cond]
            if np.shape(close_params)[0]>0:
                close_obj = all_obj_fct[~tooclose_cond]
                # random selection of the parameters that are close to the best one
                idx = np.random.choice(np.shape(close_params)[0], size=nb_rand_close, replace=False)
                selected_params = close_params[idx]
                selected_obj = close_obj[idx]
                tot_add_params = np.column_stack((selected_params, selected_obj))
                # Add the selected parameters to the eff_params
                eff_params = np.vstack((eff_params, tot_add_params))

        # In this part we filter abd remove the parameters that are almost equivalent
        # To do so, we use the DBSCAN clustering algorithm to group the parameters that are close to each other
        # and only keep the set of parameter that has the best Nash-Sutcliffe efficiency per group
        # The parameters that are not grouped are considered had "particular" and are still kept in the final set
        if apply_clustering:
            # If the number of lines of the parameters is higher than 500_000, we select a random sample of 500_000 lines
            if np.shape(eff_params)[0] > 100_000:
                logging.warning("The number of parameters is higher than 500_000. A random sample of 500_000 parameters will be selected.")
                # Select a random sample of 500_000 lines
                idx = np.random.choice(np.shape(eff_params)[0], size=100_000, replace=False)
                eff_params = eff_params[idx]
                return eff_params
            # "Normalise" or scale btw [0;1] the parameter vector to make the clustering more efficient
            min_param = np.min(eff_params, axis=0)
            max_param = np.max(eff_params, axis=0)
            norm_params = (eff_params-min_param)/(max_param-min_param)
            # Add weight to the objective function to make it more important in the clustering
            # FIXME : to be improved
            norm_params[:,-1] = norm_params[:,-1]*objective_weight
            # Apply the DBSCAN clustering algorithm to group the parameters and conversion to float32 to avoid memory issues
            db = DBSCAN(eps=eps,metric='euclidean').fit(norm_params.astype(np.float32))
            labels = db.labels_
            # Extraction of the number of groups and particular cases
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)
            noise_ind = np.where(labels==-1)[0]

            # First extract all the vectors that are grouped and their indices
            grouped_ind = db.core_sample_indices_
            grouped_params = eff_params[grouped_ind]
            grouped_labels = labels[grouped_ind]

            # Init of the filtered parameters vector
            filtered_params = np.zeros((n_clusters+n_noise, np.shape(eff_params)[1]))
            # Loop to determine the best set of parameter per group
            best_indices_per_group = np.zeros(n_clusters, dtype=int)
            for i in range(n_clusters):
                cur_indices = np.where(grouped_labels==i)[0]
                cur_group = grouped_params[cur_indices]
                best_indices_per_group[i] = np.argmax(cur_group[:,-1])

            # Keep the best set of parameters per group
            filtered_params[:n_clusters] = grouped_params[best_indices_per_group]
            # Keep all the element that could not be grouped
            filtered_params[n_clusters:] = eff_params[noise_ind]

            return filtered_params

        return eff_params


    # FIXME :  interp function used -> add the method of interpolation as an argument
    def _get_exceedance(self, idLauncher:int=0, stationOut:str="",
                         intervals:list[tuple[datetime.datetime, datetime.datetime]]=[]) -> float:
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        cur_key = curCatch.get_key_catchmentDict(stationOut)
        curBasin: SubBasin = curCatch.catchmentDict[cur_key]

        simul = curBasin.outFlow
        measure = self.compareSubBasins[stationOut]
        compare = np.interp(curCatch.time, measure.time, measure.outFlow)

        if intervals != []:
            interv = np.zeros(len(curCatch.time), dtype=bool)
            for el in intervals:
                date_i = datetime.datetime.timestamp(el[0])
                date_f = datetime.datetime.timestamp(el[1])
                interv += (curCatch.time>=date_i) & (curCatch.time<=date_f) & \
                        (~np.isnan(compare)) & (~np.isnan(simul)) & (~np.isinf(simul))
        else:
            interv = np.ones(len(curCatch.time), dtype=bool)

        eff_simul = simul[interv]
        eff_compare = compare[interv]

        q_diff = np.count_nonzero((eff_simul-eff_compare <0.0) & (eff_simul != 0.0))/np.count_nonzero((eff_simul != 0.0))

        return q_diff


    # FIXME :  to improve and generalise
    def _get_cur_fractions(self, idLauncher:int=0, stationOut:str="",
                         intervals:list[tuple[datetime.datetime, datetime.datetime]]=[]) -> dict[list[str], list[float]]:
        """
        Save the evaluations of the model.

        Args:
            idOpti (int, optional): The id of the optimisation. Defaults to 1.
            stationOut (str, optional): The station identifier. Defaults to "".
            fct_list (list[str], optional): A list of functions. Defaults to [].

        Returns:
            None

        Raises:
            None
        """
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        cur_key = curCatch.get_key_catchmentDict(stationOut)
        curBasin: SubBasin = curCatch.catchmentDict[cur_key]
        if type(curBasin) != SubBasin:
            logging.warning("The current module is not a SubBasin object!")
            return None
        cur_fracts = curBasin.get_summary_fractions(summary="mean", interval=intervals)

        return cur_fracts


    # TODO : to finish this function
    def _get_volume_fractions(self, idLauncher:int=0, stationOut:str="",
                         intervals:list[tuple[datetime.datetime, datetime.datetime]]=[]) -> dict[list[str], list[float]]:

        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        cur_key = curCatch.get_key_catchmentDict(stationOut)
        curBasin: SubBasin = curCatch.catchmentDict[cur_key]
        if type(curBasin) != SubBasin:
            logging.warning("The current module is not a SubBasin object!")
            return None
        cur_fracts = curBasin.get_volume_fractions(interval=intervals)
        return cur_fracts

    def _get_flow_fractions(self, idLauncher:int=0, stationOut:str="",
                         intervals:list[tuple[datetime.datetime, datetime.datetime]]=[],
                         from_full_matrix:tuple[np.ndarray, np.ndarray]=None) -> dict[list[str], list[float]]:
        """This function retrieves the flow fractions for a given sub-basin.
        It can also take a "full matrix" of internal variables to compute the fractions.
        This "full matrix" is a tuple containing the ids of the internal variables and the matrix itself.

        :param idLauncher: ID of the launcher, defaults to 0
        :type idLauncher: int, optional
        :param stationOut: Name of the outlet station, defaults to ""
        :type stationOut: str, optional
        :param intervals: List of start date and end date for the intervals to evaluate the flow fractions, defaults to []
        :type intervals: list[tuple[datetime.datetime, datetime.datetime]], optional
        :param from_full_matrix: Containing the matrix (nb_t, nb_iv) of I.V. coming from the Fortran code directly (not read in files), defaults to None
        :type from_full_matrix: tuple[np.ndarray, np.ndarray], optional
        :return: Dictionary containing the flow fractions for each type of flow with their names as keys and the fractions as values.
        :rtype: dict[list[str], list[float]]
        """

        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        cur_key = curCatch.get_key_catchmentDict(stationOut)
        curBasin: SubBasin = curCatch.catchmentDict[cur_key]
        if type(curBasin) != SubBasin:
            logging.warning("The current module is not a SubBasin object!")
            return None
        if from_full_matrix is not None:
            ids, iv_matrix = from_full_matrix
            all_f = mc.MODELS_VAR[curBasin.model].get_dict_from_matrix_and_ids(iv_matrix, list(ids),type_of_var=iv.FINAL_OUT_VAR)
            all_f.update(mc.MODELS_VAR[curBasin.model].get_dict_from_matrix_and_ids(iv_matrix, list(ids),type_of_var=iv.DEFAULT_VAR))
        else:
            all_f = {}
        cur_fracts = curBasin.get_flow_fractions(all_f=all_f, interval=intervals, summary="mean")
        return cur_fracts

    def _get_max_flow_fractions(self, idLauncher:int=0, stationOut:str="",
                         intervals:list[tuple[datetime.datetime, datetime.datetime]]=[],
                         from_full_matrix:tuple[np.ndarray, np.ndarray]=None) -> dict[list[str], list[float]]:

        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        cur_key = curCatch.get_key_catchmentDict(stationOut)
        curBasin: SubBasin = curCatch.catchmentDict[cur_key]
        if type(curBasin) != SubBasin:
            logging.warning("The current module is not a SubBasin object!")
            return None
        if from_full_matrix is not None:
            ids, iv_matrix = from_full_matrix
            all_f = mc.MODELS_VAR[curBasin.model].get_dict_from_matrix_and_ids(iv_matrix, list(ids),type_of_var=iv.FINAL_OUT_VAR)
            all_f.update(mc.MODELS_VAR[curBasin.model].get_dict_from_matrix_and_ids(iv_matrix, list(ids),type_of_var=iv.DEFAULT_VAR))
        else:
            all_f = {}
        cur_fracts = curBasin.get_flow_fractions(all_f=all_f, interval=intervals, summary="max")
        cur_fracts = {"max"+key: value for key, value in cur_fracts.items()}
        return cur_fracts


    def _get_punctual_reservoir_fractions(self, eval_date:datetime.datetime,
                                          idLauncher:int=0, stationOut:str="",
                                          from_full_matrix:tuple[np.ndarray, np.ndarray]=None) -> dict[list[str], list[float]]:

        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        cur_key = curCatch.get_key_catchmentDict(stationOut)
        curBasin: SubBasin = curCatch.catchmentDict[cur_key]
        if type(curBasin) != SubBasin:
            logging.warning("The current module is not a SubBasin object!")
            return None
        if from_full_matrix is not None:
            ids, iv_matrix = from_full_matrix
            all_iv = mc.MODELS_VAR[curBasin.model].get_dict_from_matrix_and_ids(iv_matrix, list(ids),type_of_var=iv.IV_VAR)
        else:
            all_iv = {}
        linked_params = mc.MODELS_VAR[curBasin.model].get_all_linked_params()
        i_params = self._get_key_from_type_all_parameters(list(linked_params.values()))
        max_params = {var_name: self.myParams[i_params[param_id]]["value"] for var_name, param_id in linked_params.items()}
        cur_fracts = curBasin.get_iv_fractions_one_date(all_iv=all_iv,max_params=max_params, eval_date=eval_date)
        return cur_fracts


    # FIXME :  to improve and generalise
    def _get_max_runoff(self, idLauncher:int=0, stationOut:str="",
                         intervals:list[tuple[datetime.datetime, datetime.datetime]]=[]) -> dict[list[str], list[float]]:

        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        cur_key = curCatch.get_key_catchmentDict(stationOut)
        curBasin: SubBasin = curCatch.catchmentDict[cur_key]
        cur_fracts = curBasin.get_summary_fractions(summary="max", interval=intervals)

        return cur_fracts["% qof"]


    def _get_ratio_max_sim_obs(self, idLauncher:int=0, stationOut:str="",
                         intervals:list[tuple[datetime.datetime, datetime.datetime]]=[]) -> float:

        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        cur_key = curCatch.get_key_catchmentDict(stationOut)
        curBasin: SubBasin = curCatch.catchmentDict[cur_key]
        measure = self.compareSubBasins[stationOut]

        if intervals != []:
            interv_simul = np.zeros(len(curCatch.time), dtype=bool)
            interv_meas = np.zeros(len(measure.time), dtype=bool)
            for el in intervals:
                date_i = datetime.datetime.timestamp(el[0])
                date_f = datetime.datetime.timestamp(el[1])
                interv_simul += (curCatch.time>=date_i) & (curCatch.time<=date_f)
                interv_meas += (measure.time>=date_i) & (measure.time<=date_f)
        else:
            interv_simul = np.ones(len(curCatch.time), dtype=bool)
            interv_meas = np.ones(len(measure.time), dtype=bool)

        simul = curBasin.outFlow[interv_simul]
        compare = measure.outFlow[interv_meas]
        ratio = np.nanmax(simul)/np.nanmax(compare)

        return ratio


    # Here, we condider that the parameters were already sorted, i.e. model parameters first and Python parameters (<0) after
    def get_param_names(self, idLauncher:int=0, stationOut:str=""):
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        myModelDict = cste.modelParamsDict[curCatch.myModel]["Parameters"]
        id_params = [self.myParams[i]["type"] for i in range(1,self.nbParams+1)]
        names = [myModelDict[cur_id]["Name"] for cur_id in id_params if cur_id>0]

        calibrate_timeDelay = bool(int(self.optiParam.get_param("Semi-Distributed", "Calibrate_times")))
        if calibrate_timeDelay:
            # Get_nb inlets
            inletsNames = self.myCases[idLauncher].refCatchment.get_inletsName(stationOut)
            nbInlets = len(inletsNames)
            for i in range(nbInlets):
                names.append("TimeDelay "+inletsNames[i])

        return names

    # Plot the equifinalty test for each station
    def plot_equifinality(self, event, idLauncher:int=0):

        physical_properties = ["%qof", "%qif", "%qbf", "%loss"]
        physical_properties_vol = ['% qof volume', '% qif volume', '% qbf volume', '% loss volume']
        # physical_properties_vol = [el+" volume" for el in physical_properties]
        colors_properties = ["b", "g", "k", "orange"]
        y_label = "Nash"

        if self.myStations==[]:
            self.set_compare_stations(idLauncher=idLauncher)
        sortJct = self.myStations

        for iOpti in range(len(sortJct)):
            stationOut = sortJct[iOpti]
            filename = self.workingDir / (stationOut+"_tests.xlsx")
            if os.path.isfile(filename):
                df = pd.read_excel(filename, sheet_name=stationOut)
                # Plot the physical properties
                fig, ax = plt.subplots()
                for cur_prop, cur_color in zip(physical_properties, colors_properties):
                    cur_columns = [col for col in df.columns if cur_prop in col.replace(" ", "")]
                    if cur_columns != []:
                        corr_prop = cur_columns[0]
                        ax.scatter(df.loc[:,corr_prop], df.loc[:,y_label], s=0.5, c=cur_color,
                                   marker='o', label=cur_prop, alpha=0.4)
                ax.set_xlabel("% of the rain [-]")
                ax.set_ylabel(y_label+" [-]")
                ax.set_title("Proportion of rain : "+stationOut)
                ax.legend()
                fig.savefig( self.workingDir / ("Equifinality_physical_prop_"+stationOut+".png"))
                # Plot the physical property volumes
                fig, ax = plt.subplots()
                for cur_prop, cur_color in zip(physical_properties_vol, colors_properties):
                    cur_columns = [col for col in df.columns if cur_prop.replace(" ", "") in col.replace(" ", "")]
                    if cur_columns != []:
                        corr_prop = cur_columns[0]
                        ax.scatter(df.loc[:,corr_prop], df.loc[:,y_label], s=0.5, c=cur_color,
                                   marker='o', label=cur_prop, alpha=0.4)
                ax.set_xlabel("% of the rain volume [-]")
                ax.set_ylabel(y_label+" [-]")
                ax.set_title("Proportion of rain volume : "+stationOut)
                ax.legend()
                fig.savefig(self.workingDir / ("Equifinality_physical_prop_volumes_"+stationOut+".png"))
                # Plot the Probability of exceedance
                cur_color = colors_properties[0]
                x_label = "P. of exceedance"
                fig, ax = plt.subplots()
                if x_label in df.columns:
                    ax.scatter(df.loc[:,x_label], df.loc[:,y_label], s=0.5, c=cur_color, marker='o', label=x_label)
                ax.set_xlabel(x_label +" [-]")
                ax.set_ylabel(y_label+" [-]")
                ax.set_title("Probability of Q_sim > Q_meas : "+stationOut)
                ax.legend()
                fig.savefig(self.workingDir / ("Equifinality_prob_excess_"+stationOut+".png"))
                # Plot Q_sim/Q_max
                x_label = "Qmax_simul/Q_max_measure"
                fig, ax = plt.subplots()
                if x_label in df.columns:
                    ax.scatter(df.loc[:,x_label], df.loc[:,y_label], s=0.5, c=cur_color, marker='o', label=x_label)
                ax.set_xlabel(x_label +" [-]")
                ax.set_ylabel(y_label+" [-]")
                ax.set_title("Peak analysis : "+stationOut)
                ax.legend()
                fig.savefig(self.workingDir / ("Equifinality_peaks_ratio_"+stationOut+".png"))
                # Plot % of the max runoff
                x_label = "% max runoff"
                fig, ax = plt.subplots()
                if x_label in df.columns:
                    ax.scatter(df.loc[:,x_label], df.loc[:,y_label], s=0.5, c=cur_color, marker='o', label=x_label)
                ax.set_xlabel(x_label +" [-]")
                ax.set_ylabel(y_label+" [-]")
                ax.set_title("Max runoff [%] : "+stationOut)
                ax.legend()
                fig.savefig(self.workingDir / ("Equifinality_max_runoff_"+stationOut+".png"))
            else:
                logging.error("The file "+filename+" does not exist!")

        plt.show()

    # Plot the equifinalty test for each station
    def plot_model_analysis(self, event, idLauncher:int=0):

        physical_properties = ["%q_of", "%q_if", "%q_bf"]
        # physical_properties_vol = [el+" volume" for el in physical_properties]
        colors_properties = ["b", "g", "k"]
        y_label = "Nash"

        if self.myStations==[]:
            self.set_compare_stations(idLauncher=idLauncher)
        sortJct = self.myStations

        for iOpti in range(len(sortJct)):
            stationOut = sortJct[iOpti]
            filename = self.workingDir / (stationOut+"_tests.xlsx")
            if os.path.isfile(filename):
                df = pd.read_excel(filename, sheet_name=stationOut)
                # Plot the physical properties
                fig, ax = plt.subplots()
                for cur_prop, cur_color in zip(physical_properties, colors_properties):
                    cur_columns = [col for col in df.columns if cur_prop in col.replace(" ", "").lower()]
                    if cur_columns != []:
                        corr_prop = cur_columns[0]
                        ax.scatter(df.loc[:,corr_prop], df.loc[:,y_label], s=0.5, c=cur_color,
                                   marker='o', label=cur_prop, alpha=0.4)
                ax.set_xlabel("% of the rain [-]")
                ax.set_ylabel(y_label+" [-]")
                ax.set_title("Proportion of rain : "+stationOut)
                ax.legend()
                fig.savefig(self.workingDir / ("Equifinality_physical_prop_"+stationOut+".png"))
                # Plot the Probability of exceedance
                cur_color = colors_properties[0]
                x_label = "P. of exceedance"
                fig, ax = plt.subplots()
                if x_label in df.columns:
                    ax.scatter(df.loc[:,x_label], df.loc[:,y_label], s=0.5, c=cur_color, marker='o', label=x_label)
                ax.set_xlabel(x_label +" [-]")
                ax.set_ylabel(y_label+" [-]")
                ax.set_title("Probability of Q_sim > Q_meas : "+stationOut)
                ax.legend()
                fig.savefig(self.workingDir / ("Equifinality_prob_excess_"+stationOut+".png"))
                # Plot Q_sim/Q_max
                x_label = "Qmax_simul/Q_max_measure"
                fig, ax = plt.subplots()
                if x_label in df.columns:
                    ax.scatter(df.loc[:,x_label], df.loc[:,y_label], s=0.5, c=cur_color, marker='o', label=x_label)
                ax.set_xlabel(x_label +" [-]")
                ax.set_ylabel(y_label+" [-]")
                ax.set_title("Peak analysis : "+stationOut)
                ax.legend()
                fig.savefig(self.workingDir / ("Equifinality_peaks_ratio_"+stationOut+".png"))

            else:
                logging.error("The file "+filename+" does not exist!")

        plt.show()


    def add_Case(self, idLauncher:int=0):

        i = idLauncher
        newCase = CaseOpti()
        launcherDir = self.optiParam.get_param("Cases","dir_"+str(i+1))
        isOk, launcherDir = check_path(launcherDir, prefix=self.workingDir, applyCWD=True)
        if isOk<0:
            logging.error("ERROR : in path of launcherDir")
        newCase.read_param(launcherDir, copyDefault=False, callback=self.update_parameters_launcher)
        # FIXME TO CHANGE when seperation with the GUI
        if self.wx_exists:
            newId = wx.Window.NewControlId()
            iMenu = self.MenuBar.FindMenu('Param files')
            paramMenu = self.MenuBar.Menus[iMenu][0]
            curName = 'Case '+str(i+1)
            iItem = self.MenuBar.FindMenuItem('Param files', curName)
            if(iItem==wx.NOT_FOUND):
                caseMenu = wx.Menu()
                paramCaseFile = caseMenu.Append(wx.ID_ANY, 'launcher.param')
                self.Bind(wx.EVT_MENU, newCase.show_launcherParam, paramCaseFile)
                guiHydroCase = caseMenu.Append(wx.ID_ANY, 'GUI Hydro')
                refDir = newCase.launcherParam.get_param("Calculs","Répertoire simulation de référence")
                isOk, refDir = check_path(refDir, prefix=launcherDir, applyCWD=True)
                if isOk<0:
                    logging.error("ERROR : in path of launcherDir")
                newCase.mydro = HydrologyModel(directory=refDir)
                newCase.mydro.Hide()
                self.Bind(wx.EVT_MENU, newCase.show_mydro, guiHydroCase)
                curCase = paramMenu.Append(newId, curName, caseMenu)
            else:
                logging.warning(_("WARNING : this scenario was not implemented yet. This might induce an error!"))
                # iItem =
                curCase = paramMenu.Replace(iItem)
        else:
            refDir = newCase.launcherParam.get_param("Calculs","Répertoire simulation de référence")
            isOk, refDir = check_path(refDir, prefix=launcherDir, applyCWD=True)
            newCase.mydro = HydrologyModel(directory=refDir)

        self.Bind(wx.EVT_MENU, newCase.show_launcherParam, curCase)
        newCase.idMenuItem = newId
        self.myCases.append(newCase)


    def launch_semi_dist_parameters(self, idLauncher:int=0, idOpti:int=1,
                                    params_to_test:dict[str, np.ndarray]={},
                                    return_outflows:bool=False) -> dict[str, np.ndarray]:
        # Return variable
        all_outlets = {}
        # Useful variables
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        doneList = []
        previousLevel = 1
        # Get if the optimisation or the set of parameters is only for 1 subbasin severals
        onlyOwnSub = self.optiParam.get_param("Semi-Distributed", "Own_SubBasin")
        if onlyOwnSub is None:
            onlyOwnSub = False
        # Collect sort and save the compare stations
        self.set_compare_stations(idLauncher=idLauncher)
        sortJct = self.myStations
        # Get the initial number of intervals
        # -> these can evolve according to the measurement available at each station
        is_ok = self._save_opti_intervals()
        all_intervals = self.all_intervals
        # Extract the number of time steps to initialise the matrices
        nb_time_steps = len(curCatch.time)
        # Loop over all stations to apply the set of parameters
        for stationOut in sortJct:
            if not stationOut in list(params_to_test.keys()):
                continue
            # Definition of the current subbasin
            cur_key = curCatch.get_key_catchmentDict(stationOut)
            curBasin: SubBasin = curCatch.catchmentDict[cur_key]
            # Extract all the parameters to test
            all_params = params_to_test[stationOut]
            logging.info("==================")
            logging.info("Station : "+stationOut)
            # Prepare all the file in the hydrology optimisation and simulation directories
            self._prepare_opti_hydro_files(stationOut=stationOut, idLauncher=idLauncher,
                                          onlyOwnSub=onlyOwnSub, doneList=doneList, previousLevel=previousLevel)
            # Select correct calibration intervals -> remove the intervals with NaN
            cur_intervals = self.select_opti_intervals(all_intervals=all_intervals, stationOut=stationOut, filter_nan=True)
            self.save_opti_dates_to_file(cur_intervals)
            ## ===================================================================================================================
            ## Init
            ## ===================================================================================================================
            self.init_optimizer(idOpti)
            self.associate_ptr(None, idOpti=idOpti)
            ## ===================================================================================================================
            ## Compute
            ## ===================================================================================================================
            all_outlets[stationOut] = np.zeros((len(all_params), nb_time_steps))
            for i in range(len(all_params)):
                cur_p = all_params[i, :-1]
                cur_obj2 = self.evaluate_model_optimizer(cur_p, idOpti=idOpti)
                all_outlets[stationOut][i,:] = curBasin.outFlow
                # Small test
                cur_obj = all_params[i, -1]
                logging.info(_("cur_obj : %s ; cur_obj2 : %s"), cur_obj, cur_obj2)
                if cur_obj != cur_obj2:
                    logging.error("The objective function is not the same as the one computed by the model!")
                    logging.error("cur_obj : "+str(cur_obj)+" ; cur_obj2 : "+str(cur_obj2))
            ## ===================================================================================================================
            ## ===================================================================================================================
            # Collect the best parameters and their objective function(s)
            best_params = self.apply_optim(None)
            # Simulation with the best parameters
            self.compute_distributed_hydro_model()
            # Update myHydro of all effective subbasins to get the best configuration upstream
            curCatch.read_hydro_eff_subBasin()
            # Update timeDelays according to time wolf_array
            self.apply_timeDelay_dist(idOpti=idOpti, idLauncher=idLauncher, junctionKey=stationOut)
            # Update the outflows
            curCatch.update_hydro(idCompar=0)

            # All upstream elements of a reference will be fixed
            doneList.append(stationOut)
            previousLevel = curCatch.levelOut

        logging.info("All the parameters have been tested!")
        if return_outflows:
            return all_outlets


    def _prepare_opti_hydro_files(self, stationOut:str, idLauncher:int=0, onlyOwnSub:bool=False,
                                 doneList:list[str]=[], previousLevel:int=1):
        # Useful variables
        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        # Build the current compare.txt file and replace all nan values by 0.0
        self.save_current_compare_file(stationOut=stationOut)
        # Save the name of the station that will be the output
        curCatch.define_station_out(stationOut)
        # Activate all the useful subs and write it in the param file
        curCatch.activate_usefulSubs(blockJunction=doneList, onlyItself=onlyOwnSub)
        # Rename the result file
        self.optiParam.change_param("Optimizer", "fname", stationOut)
        self.optiParam.SavetoFile(None)
        self.optiParam.Reload(None)
        self.update_myParams(idLauncher)
        # Prepare the paramPy dictionnary before calibration
        self.prepare_calibration_timeDelay(stationOut=stationOut)
        # Reload the useful modules
        self.reload_hydro(idCompar=0, fromStation=stationOut, lastLevel=previousLevel, updateAll=True)



    def write_one_opti_param(self, filPath:Path, fileName:Path, myGroup:str, myKey:str, value:float, convers_factor:int=1.0):
        tmpWolf = Wolf_Param(to_read=True, filename=os.path.join(filPath,fileName),toShow=False, init_GUI=False)
        tmpWolf.change_param(myGroup, myKey, value/convers_factor)
        tmpWolf.SavetoFile(None)
        # tmpWolf.OnClose(None)
        tmpWolf = None


    # FIXME : this function has been dashed off -> functionnal but not well written!!
    # TODO : to improve !!!!!!
    def launch_models_propertie_with_Nash_old(self, event, idLauncher:int=0, idOpti:int=1, quantile_Nash:float=0.01, std_Nash:float=0.03, clustering_Nash:bool=True,
                                          save_every:int=100, restart_from_file:bool=True):
        """
        Analyse the properties of the model and compare them with the Nash coefficient.

        Args:
            idLauncher (int, optional): The id of the launcher. Defaults to 0.

        Returns:
            None

        Raises:
            None
        """
        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        onlyOwnSub = self.optiParam.get_param("Semi-Distributed", "Own_SubBasin")
        if onlyOwnSub is None:
            onlyOwnSub = False
        doneList = []
        previousLevel = 1
        # Collect sort and save the compare stations
        self.set_compare_stations(idLauncher=idLauncher)
        sortJct = self.myStations
        # Get the initial number of intervals
        # -> these can evolve according to the measurement available at each station
        is_ok = self._save_opti_intervals()
        all_intervals = self.all_intervals
        # Activate the writing of the internal variables
        curCatch.activate_all_internal_variables()
        # Prepare the Excel writer
        writer_tot = pd.ExcelWriter(self.workingDir / "all_best_tests.xlsx", engine = 'xlsxwriter')

        for iOpti in range(len(sortJct)):
            stationOut = sortJct[iOpti]
            logging.info("==================")
            logging.info("Station : "+stationOut)
            # Build the current compare.txt file and replace all nan values by 0.0
            self.save_current_compare_file(stationOut=stationOut)
            # Save the name of the station that will be the output
            curCatch.define_station_out(stationOut)
            # Activate all the useful subs and write it in the param file
            curCatch.activate_usefulSubs(blockJunction=doneList, onlyItself=onlyOwnSub)
            # Select correct calibration intervals -> remove the intervals with NaN
            cur_intervals = self.select_opti_intervals(all_intervals=all_intervals, stationOut=stationOut, filter_nan=True)
            self.save_opti_dates_to_file(cur_intervals)
            # Rename the result file
            self.optiParam.change_param("Optimizer", "fname", stationOut)
            self.optiParam.SavetoFile(None)
            self.optiParam.Reload(None)
            self.update_myParams(idLauncher)
            # Prepare the paramPy dictionnary before calibration
            self.prepare_calibration_timeDelay(stationOut=stationOut)
            # Reload the useful modules
            self.reload_hydro(idCompar=0, fromStation=stationOut, lastLevel=previousLevel, updateAll=True)
            ## =======
            ## Init
            ## =======
            self.init_optimizer(idOpti)
            self.associate_ptr(None, idOpti=idOpti)
            # Get the best parameters to test
            all_params = self.get_best_params(stationOut=stationOut, quantile=quantile_Nash, std=std_Nash, rmv_near_max=1e-4, apply_clustering=clustering_Nash)
            ## =======
            ## Compute
            ## =======
            all_frac = []
            # Check if the excel file already exists and load it to check if some parameters have already been tested
            if restart_from_file:
                all_frac, all_params = self._reload_model_analysis(stationOut=stationOut, all_params=all_params)
            # Get param names
            names = self.get_param_names(idLauncher=idLauncher, stationOut=stationOut)
            logging.info("The number of sets of parameters to test are : "+str(len(all_params)))
            for i in tqdm(range(len(all_params))):
                cur_p = all_params[i, :-1]
                cur_obj = all_params[i, -1]
                cur_obj2 = self.evaluate_model_optimizer(cur_p, idOpti=idOpti)
                logging.info(_("cur_obj : %s ; cur_obj2 : %s"), cur_obj, cur_obj2)
                if cur_obj != cur_obj2:
                    logging.error("The objective function is not the same as the one computed by the model!")
                    logging.error("cur_obj : "+str(cur_obj)+" ; cur_obj2 : "+str(cur_obj2))
                # assert cur_obj == cur_obj2, "The objective function is not the same as the one computed by the model!"
                self.write_mesh_results_optimizer(idOpti=idOpti)
                # Save all the variables/evaluations desired
                frac_flow_dict = self._get_flow_fractions(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                max_flow_dict = self._get_max_flow_fractions(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                init_iv =  self._get_punctual_reservoir_fractions(eval_date=cur_intervals[0][0], idLauncher=idLauncher, stationOut=stationOut)
                p_excess = self._get_exceedance(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                max_sim_obs = self._get_ratio_max_sim_obs(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                # Extract the time delays
                all_timeDelays = curCatch.get_timeDelays_inlets(ref=stationOut)
                all_timeDelays_str = {key : str(datetime.timedelta(seconds=all_timeDelays[key])) for key in all_timeDelays}
                cur_timeDelays = list(all_timeDelays_str.values())
                # Concatenate all the informations
                cur_all_frac = (list(cur_p)
                                + cur_timeDelays
                                + list(frac_flow_dict.values())
                                + list(max_flow_dict.values())
                                + list(init_iv.values())
                                + [p_excess, max_sim_obs, cur_obj])
                all_frac.append(cur_all_frac)
                # Periodically save the evaluations in case of trouble
                if (i + 1) % save_every == 0:
                    # Save the evaluations
                    var_names = names \
                                + list(all_timeDelays_str.keys()) \
                                + list(frac_flow_dict.keys()) \
                                + list(max_flow_dict.keys()) \
                                + list(init_iv.keys()) \
                                + ["P. of exceedance", "Qmax_simul/Q_max_measure", "Nash"]
                    cur_df = pd.DataFrame(all_frac, columns=var_names)
                    # write first the tempory results for each station
                    writer_stat = pd.ExcelWriter(self.workingDir / (stationOut+"_tests.xlsx"), engine = 'xlsxwriter')
                    cur_df.to_excel(writer_stat, sheet_name=stationOut, columns=var_names)
                    writer_stat.sheets[stationOut].autofit()
                    writer_stat.close()

            # Save the evaluations
            if(len(all_params))>0:
                var_names = names \
                            + list(all_timeDelays_str.keys()) \
                            + list(frac_flow_dict.keys()) \
                            + list(max_flow_dict.keys()) \
                            + list(init_iv.keys()) \
                            + ["P. of exceedance", "Qmax_simul/Q_max_measure", "Nash"]
                cur_df = pd.DataFrame(all_frac, columns=var_names)
                # write first the tempory results for each station
                writer_stat = pd.ExcelWriter(self.workingDir / (stationOut+"_tests.xlsx"), engine = 'xlsxwriter')
                cur_df.to_excel(writer_stat, sheet_name=stationOut, columns=var_names)
                writer_stat.sheets[stationOut].autofit()
                writer_stat.close()
                # write now the informations for all the stations in the same excel file
                cur_df.to_excel(writer_tot, sheet_name=stationOut, columns=var_names)
                writer_tot.sheets[stationOut].autofit()

            ## =======
            ## =======
            # Collect the best parameters and their objective function(s)
            best_params = self.apply_optim(None)
            # Simulation with the best parameters
            self.compute_distributed_hydro_model()
            # Update myHydro of all effective subbasins to get the best configuration upstream
            curCatch.read_hydro_eff_subBasin()
            # Update timeDelays according to time wolf_array
            self.apply_timeDelay_dist(idOpti=idOpti, idLauncher=idLauncher, junctionKey=stationOut)
            # Update the outflows
            curCatch.update_hydro(idCompar=0)

            # All upstream elements of a reference will be fixed
            doneList.append(stationOut)
            previousLevel = curCatch.levelOut

        writer_tot.close()
        logging.info("The equifinality test is finished!")

    # FIXME : this function has been dashed off -> functionnal but not well written!!
    # TODO : to improve !!!!!!
    def launch_models_propertie_with_Nash_old2(self, event, idLauncher:int=0, idOpti:int=1, quantile_Nash:float=0.01, std_Nash:float=0.03, clustering_Nash:bool=True,
                                          save_every:int=1000, restart_from_file:bool=True,
                                          intervals:list[tuple[datetime.datetime, datetime.datetime]]=[]):
        """
        Analyse the properties of the model and compare them with the Nash coefficient.

        Args:
            idLauncher (int, optional): The id of the launcher. Defaults to 0.

        Returns:
            None

        Raises:
            None
        """
        curCatch:Catchment = self.myCases[idLauncher].refCatchment

        onlyOwnSub = self.optiParam.get_param("Semi-Distributed", "Own_SubBasin")
        if onlyOwnSub is None:
            onlyOwnSub = False
        doneList = []
        previousLevel = 1
        # Collect sort and save the compare stations
        self.set_compare_stations(idLauncher=idLauncher)
        sortJct = self.myStations
        # Get the initial number of intervals
        # -> these can evolve according to the measurement available at each station
        is_ok = self._save_opti_intervals()
        all_intervals = self.all_intervals
        # Activate the writing of the internal variables
        curCatch.activate_all_internal_variables()
        # Prepare the Excel writer
        writer_tot = pd.ExcelWriter(self.workingDir / "all_best_tests.xlsx", engine = 'xlsxwriter')

        for iOpti in range(len(sortJct)):
            stationOut = sortJct[iOpti]
            logging.info("==================")
            logging.info("Station : "+stationOut)
            # Build the current compare.txt file and replace all nan values by 0.0
            self.save_current_compare_file(stationOut=stationOut)
            # Save the name of the station that will be the output
            curCatch.define_station_out(stationOut)
            # Activate all the useful subs and write it in the param file
            curCatch.activate_usefulSubs(blockJunction=doneList, onlyItself=onlyOwnSub)
            # Select correct calibration intervals -> remove the intervals with NaN
            cur_intervals = self.select_opti_intervals(all_intervals=all_intervals, stationOut=stationOut, filter_nan=True)
            flood_intervals = (date(2021, 7, 13, 0, 0, 0, tzinfo=datetime.timezone.utc),
                                    date(2021, 7, 17, 0, 0, 0, tzinfo=datetime.timezone.utc))
            phys_prop_intervals = self._intersect_intervals(cur_intervals, flood_intervals)
            self.save_opti_dates_to_file(cur_intervals)
            # Rename the result file
            self.optiParam.change_param("Optimizer", "fname", stationOut)
            self.optiParam.SavetoFile(None)
            self.optiParam.Reload(None)
            self.update_myParams(idLauncher)
            # Prepare the paramPy dictionnary before calibration
            self.prepare_calibration_timeDelay(stationOut=stationOut)
            # Reload the useful modules
            self.reload_hydro(idCompar=0, fromStation=stationOut, lastLevel=previousLevel, updateAll=True)
            ## =======
            ## Init
            ## =======
            self.init_optimizer(idOpti)
            self.associate_ptr(None, idOpti=idOpti)
            # Get the best parameters to test
            all_params = self.get_best_params(stationOut=stationOut, quantile=quantile_Nash, std=std_Nash, rmv_near_max=1e-4, apply_clustering=clustering_Nash)
            ## =======
            ## Compute
            ## =======
            all_frac = []
            ids = None
            iv_matrix = None
            # Check if the excel file already exists and load it to check if some parameters have already been tested
            if restart_from_file:
                all_frac, all_params = self._reload_model_analysis(stationOut=stationOut, all_params=all_params)
            # Get param names
            names = self.get_param_names(idLauncher=idLauncher, stationOut=stationOut)
            logging.info("The number of sets of parameters to test are : "+str(len(all_params)))
            for i in tqdm(range(len(all_params))):
                cur_p = all_params[i, :-1]
                cur_obj = all_params[i, -1]
                cur_obj2 = self.evaluate_model_optimizer(cur_p, idOpti=idOpti)
                logging.info(_("cur_obj : %s ; cur_obj2 : %s"), cur_obj, cur_obj2)
                if cur_obj != cur_obj2:
                    logging.error(_("The objective function is not the same as the one computed by the model!"))
                    logging.error(_("cur_obj : %s ; cur_obj2 : %s"), cur_obj, cur_obj2)
                # Recover the full matrix from Fortran
                if ids is None or iv_matrix is None:
                    iv_data = None
                else:
                    iv_data = (ids, iv_matrix)
                ids, iv_matrix = self.get_all_activated_iv(idOpti=idOpti, idLauncher=idLauncher, iv_variables=iv_data)
                # Save all the variables/evaluations desired
                frac_flow_dict = self._get_flow_fractions(idLauncher=idLauncher, stationOut=stationOut, intervals=phys_prop_intervals,
                                                          from_full_matrix=(ids, iv_matrix))
                max_flow_dict = self._get_max_flow_fractions(idLauncher=idLauncher, stationOut=stationOut, intervals=phys_prop_intervals,
                                                             from_full_matrix=(ids, iv_matrix))
                init_iv =  self._get_punctual_reservoir_fractions(eval_date=cur_intervals[0][0], idLauncher=idLauncher, stationOut=stationOut,
                                                                  from_full_matrix=(ids, iv_matrix))
                p_excess = self._get_exceedance(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                max_sim_obs = self._get_ratio_max_sim_obs(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                # Extract the time delays
                all_timeDelays = curCatch.get_timeDelays_inlets(ref=stationOut)
                all_timeDelays_str = {key : str(datetime.timedelta(seconds=all_timeDelays[key])) for key in all_timeDelays}
                cur_timeDelays = list(all_timeDelays_str.values())
                # Concatenate all the informations
                cur_all_frac = (list(cur_p)
                                + cur_timeDelays
                                + list(frac_flow_dict.values())
                                + list(max_flow_dict.values())
                                + list(init_iv.values())
                                + [p_excess, max_sim_obs, cur_obj])
                all_frac.append(cur_all_frac)
                # Periodically save the evaluations in case of trouble
                if (i + 1) % save_every == 0:
                    # Save the evaluations
                    var_names = names \
                                + list(all_timeDelays_str.keys()) \
                                + list(frac_flow_dict.keys()) \
                                + list(max_flow_dict.keys()) \
                                + list(init_iv.keys()) \
                                + ["P. of exceedance", "Qmax_simul/Q_max_measure", "Nash"]
                    cur_df = pd.DataFrame(all_frac, columns=var_names)
                    # write first the tempory results for each station
                    writer_stat = pd.ExcelWriter(self.workingDir / (stationOut+"_tests.xlsx"), engine = 'xlsxwriter')
                    cur_df.to_excel(writer_stat, sheet_name=stationOut, columns=var_names)
                    writer_stat.sheets[stationOut].autofit()
                    writer_stat.close()


            # Save the evaluations
            if(len(all_params))>0:
                var_names = names \
                            + list(all_timeDelays_str.keys()) \
                            + list(frac_flow_dict.keys()) \
                            + list(max_flow_dict.keys()) \
                            + list(init_iv.keys()) \
                            + ["P. of exceedance", "Qmax_simul/Q_max_measure", "Nash"]
                cur_df = pd.DataFrame(all_frac, columns=var_names)
                # write first the tempory results for each station
                writer_stat = pd.ExcelWriter(self.workingDir / (stationOut+"_tests.xlsx"), engine = 'xlsxwriter')
                cur_df.to_excel(writer_stat, sheet_name=stationOut, columns=var_names)
                writer_stat.sheets[stationOut].autofit()
                writer_stat.close()
                # write now the informations for all the stations in the same excel file
                cur_df.to_excel(writer_tot, sheet_name=stationOut, columns=var_names)
                writer_tot.sheets[stationOut].autofit()

            ## =======
            ## =======
            # Collect the best parameters and their objective function(s)
            best_params = self.apply_optim(None)
            # Simulation with the best parameters
            self.compute_distributed_hydro_model()
            # Update myHydro of all effective subbasins to get the best configuration upstream
            curCatch.read_hydro_eff_subBasin()
            # Update timeDelays according to time wolf_array
            self.apply_timeDelay_dist(idOpti=idOpti, idLauncher=idLauncher, junctionKey=stationOut)
            # Update the outflows
            curCatch.update_hydro(idCompar=0)

            # All upstream elements of a reference will be fixed
            doneList.append(stationOut)
            previousLevel = curCatch.levelOut

        writer_tot.close()
        logging.info("The equifinality test is finished!")


    # FIXME : this function has been dashed off -> functionnal but not well written!!
    # TODO : to improve !!!!!!
    def launch_models_properties_with_Nash(self, event, idLauncher:int=0, idOpti:int=1, quantile_Nash:float=0.01, std_Nash:float=0.03, clustering_Nash:bool=False,
                                          save_every:int=1000, restart_from_file:bool=False,
                                          evaluation_interval:tuple[datetime.datetime, datetime.datetime]=[]):
        """
        Analyse the properties of the model and compare them with the Nash coefficient.

        Args:
            idLauncher (int, optional): The id of the launcher. Defaults to 0.

        Returns:
            None

        Raises:
            None
        """
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        try:
            onlyOwnSub = self.optiParam.get_param("Semi-Distributed", "Own_SubBasin")
            if onlyOwnSub is None:
                onlyOwnSub = False
            doneList = []
            previousLevel = 1
            # Collect sort and save the compare stations
            self.set_compare_stations(idLauncher=idLauncher)
            sortJct = self.myStations
            # Get the initial number of intervals
            # -> these can evolve according to the measurement available at each station
            self.all_intervals = self._read_opti_intervals(idLauncher=idLauncher)
            all_intervals = self.all_intervals
            # Activate the writing of the internal variables
            curCatch.activate_all_internal_variables()
            # Prepare the Excel writer
            writer_tot = pd.ExcelWriter(self.workingDir / "all_best_tests.xlsx", engine = 'xlsxwriter')

            for iOpti in range(len(sortJct)):
                stationOut = sortJct[iOpti]
                logging.info("==================")
                logging.info("Station : "+stationOut)
                isOk, cur_intervals = self.prepare_optimize_model_F_one_station(stationOut=stationOut, idLauncher=idLauncher, idOpti=idOpti,
                                                        all_intervals=all_intervals, already_done_subbasins=doneList,
                                                        onlyOwnSub=onlyOwnSub, previousLevel=previousLevel,
                                                        return_intervals=True)
                # Get the best parameters to test
                all_params = self.get_best_params(stationOut=stationOut, quantile=None, std=0.1, rmv_near_max=None, apply_clustering=clustering_Nash)
                ## =======
                ## Compute loop
                ## =======
                # FIXME : if no list, just keep the cur_intervals and also no intervals intersection application
                if evaluation_interval == []:
                    evaluation_interval = (date(2021, 7, 13, 0, 0, 0, tzinfo=datetime.timezone.utc),
                                        date(2021, 7, 17, 0, 0, 0, tzinfo=datetime.timezone.utc))
                phys_prop_intervals = self._intersect_intervals(cur_intervals, evaluation_interval)
                all_frac = []
                ids = None
                iv_matrix = None
                # Check if the excel file already exists and load it to check if some parameters have already been tested
                if restart_from_file:
                    all_frac, all_params = self._reload_model_analysis(stationOut=stationOut, all_params=all_params)
                # Get param names
                names = self.get_param_names(idLauncher=idLauncher, stationOut=stationOut)
                logging.info("The number of sets of parameters to test are : "+str(len(all_params)))
                for i in tqdm(range(len(all_params))):
                    cur_p = all_params[i, :-1]
                    cur_obj = all_params[i, -1]
                    cur_obj2 = self.evaluate_model_optimizer(cur_p, idOpti=idOpti)
                    logging.info(_("cur_obj : %s ; cur_obj2 : %s"), cur_obj, cur_obj2)
                    if cur_obj != cur_obj2:
                        logging.error(_("The objective function is not the same as the one computed by the model!"))
                        logging.error(_("cur_obj : %s ; cur_obj2 : %s"), cur_obj, cur_obj2)
                    # Recover the full matrix from Fortran
                    if ids is None or iv_matrix is None:
                        iv_data = None
                    else:
                        iv_data = (ids, iv_matrix)
                    ids, iv_matrix = self.get_all_activated_iv(idOpti=idOpti, idLauncher=idLauncher, iv_variables=iv_data)
                    # Save all the variables/evaluations desired
                    frac_flow_dict = self._get_flow_fractions(idLauncher=idLauncher, stationOut=stationOut, intervals=phys_prop_intervals,
                                                            from_full_matrix=(ids, iv_matrix))
                    max_flow_dict = self._get_max_flow_fractions(idLauncher=idLauncher, stationOut=stationOut, intervals=phys_prop_intervals,
                                                                from_full_matrix=(ids, iv_matrix))
                    init_iv =  self._get_punctual_reservoir_fractions(eval_date=cur_intervals[0][0], idLauncher=idLauncher, stationOut=stationOut,
                                                                    from_full_matrix=(ids, iv_matrix))
                    p_excess = self._get_exceedance(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                    max_sim_obs = self._get_ratio_max_sim_obs(idLauncher=idLauncher, stationOut=stationOut, intervals=cur_intervals)
                    # Extract the time delays
                    all_timeDelays = curCatch.get_timeDelays_inlets(ref=stationOut)
                    all_timeDelays_str = {key : str(datetime.timedelta(seconds=all_timeDelays[key])) for key in all_timeDelays}
                    cur_timeDelays = list(all_timeDelays_str.values())
                    # Concatenate all the informations
                    cur_all_frac = (list(cur_p)
                                    + cur_timeDelays
                                    + list(frac_flow_dict.values())
                                    + list(max_flow_dict.values())
                                    + list(init_iv.values())
                                    + [p_excess, max_sim_obs, cur_obj])
                    all_frac.append(cur_all_frac)
                    # Periodically save the evaluations in case of trouble
                    if (i + 1) % save_every == 0:
                        # Save the evaluations
                        var_names = names \
                                    + list(all_timeDelays_str.keys()) \
                                    + list(frac_flow_dict.keys()) \
                                    + list(max_flow_dict.keys()) \
                                    + list(init_iv.keys()) \
                                    + ["P. of exceedance", "Qmax_simul/Q_max_measure", "Nash"]
                        cur_df = pd.DataFrame(all_frac, columns=var_names)
                        # write first the tempory results for each station
                        writer_stat = pd.ExcelWriter(self.workingDir / (stationOut+"_tests.xlsx"), engine = 'xlsxwriter')
                        cur_df.to_excel(writer_stat, sheet_name=stationOut, columns=var_names)
                        writer_stat.sheets[stationOut].autofit()
                        writer_stat.close()


                # Save the evaluations
                if(len(all_params))>0:
                    var_names = names \
                                + list(all_timeDelays_str.keys()) \
                                + list(frac_flow_dict.keys()) \
                                + list(max_flow_dict.keys()) \
                                + list(init_iv.keys()) \
                                + ["P. of exceedance", "Qmax_simul/Q_max_measure", "Nash"]
                    cur_df = pd.DataFrame(all_frac, columns=var_names)
                    # write first the tempory results for each station
                    writer_stat = pd.ExcelWriter(self.workingDir / (stationOut+"_tests.xlsx"), engine = 'xlsxwriter')
                    cur_df.to_excel(writer_stat, sheet_name=stationOut, columns=var_names)
                    writer_stat.sheets[stationOut].autofit()
                    writer_stat.close()
                    # write now the informations for all the stations in the same excel file
                    cur_df.to_excel(writer_tot, sheet_name=stationOut, columns=var_names)
                    writer_tot.sheets[stationOut].autofit()

                ## =======
                ## =======
                # Reset the configuration of the optimal parameters in all file and in all variables
                self.reload_optimal_subbasin(idLauncher=idLauncher, idOpti=idOpti, stationOut=stationOut)

                # All upstream elements of a reference will be fixed
                doneList.append(stationOut)
                previousLevel = curCatch.levelOut

            # Reset the optimisation file
            self.save_opti_dates_to_file(self.all_intervals)
            writer_tot.close()
        except Exception as e:
            logging.error("An error occurred during the model properties analysis: " + str(e))
            # Reset the optimisation file
            self.save_opti_dates_to_file(self.all_intervals)
            raise e
        logging.info("The equifinality test is finished!")

    # FIXME : it might be better to pass the myParams to the CaseOpti object instead to allow parallelisation
    def _build_type_to_key_index(self) -> dict[int, int]:
        return {param["type"]: i for i, param in self.myParams.items()}

    def _get_key_from_type_all_parameters(self, list_type_param: list[int]) -> dict[int | None]:
        type_to_key = self._build_type_to_key_index()
        return {cur_key: type_to_key.get(cur_key) for cur_key in list_type_param}

    def _get_key_from_type_parameter(self, type_param:int) -> int:
        return next((i for i, param in self.myParams.items() if param["type"] == type_param), None)

    def _intersect_intervals(self, intervals:list[tuple[date, date]], flood_intervals:tuple[date, date]):
        result = []
        flood_start, flood_end = flood_intervals
        for int_start, int_end in intervals:
            # Find overlap
            start = max(int_start, flood_start)
            end = min(int_end, flood_end)
            if start < end:  # There is an overlap
                result.append((start, end))
        return result

    def reload_optimal_subbasin(self, idLauncher:int=0, idOpti:int=1, stationOut:str=None):
        """
        Reload the optimal subbasin for a given idLauncher and idOpti.

        Args:
            idLauncher (int): The id of the launcher.
            idOpti (int): The id of the optimizer.
            stationOut (str): The name of the station.

        Returns:
            None

        Raises:
            None
        """
        # Get the current catchment
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        # Collect the best parameters and their objective function(s)
        best_params = self.apply_optim(None)
        # Simulation with the best parameters
        self.compute_distributed_hydro_model()
        # Update myHydro of all effective subbasins to get the best configuration upstream
        curCatch.read_hydro_eff_subBasin()
        # Update timeDelays according to time wolf_array
        self.apply_timeDelay_dist(idOpti=idOpti, idLauncher=idLauncher, junctionKey=stationOut)
        # Update the outflows
        curCatch.update_hydro(idCompar=0)



    def init_optimize_model_f(self, idOpti:int=1):
        """
        Initialize the optimization model for a given idOpti.

        Args:
            idOpti (int): The id of the optimizer.

        Returns:
            None

        Raises:
            None
        """
        # Initialize the optimizer
        self.init_optimizer(idOpti)
        # Associate the pointer to the optimizer
        self.associate_ptr(None, idOpti=idOpti)


    def prepare_optimize_model_F_one_station(self, idLauncher:int=0, idOpti:int=1, stationOut:str=None, all_intervals:list[tuple[date, date]]=[],
                                          onlyOwnSub:bool=True, previousLevel:int=1, already_done_subbasins:list[str]=[],
                                          return_intervals:bool=False):
        isOk = 0
        # Get the current catchment
        curCatch:Catchment = self.myCases[idLauncher].refCatchment
        # Define the outlet station and keep the same if not provided
        if stationOut is None:
            stationOut = curCatch.junctionOut
        # Select and save the compare file off the outlet station
        self.save_current_compare_file(stationOut=stationOut)
        # Save the name of the station that will be the output
        curCatch.define_station_out(stationOut)
        # Activate all the useful subs and write it in the param file
        curCatch.activate_usefulSubs(blockJunction=already_done_subbasins, onlyItself=True)
        # Select correct calibration intervals -> remove the intervals with NaN
        if all_intervals == []:
            all_intervals = self._read_opti_intervals(idLauncher=idLauncher)
        cur_intervals = self.select_opti_intervals(all_intervals=all_intervals, stationOut=stationOut, filter_nan=True)
        self.save_opti_dates_to_file(cur_intervals)
        # Rename the result file
        self.optiParam.change_param("Optimizer", "fname", stationOut)
        self.optiParam.SavetoFile(None)
        self.optiParam.Reload(None)
        self.update_myParams(idLauncher)
        # Prepare the paramPy dictionnary before calibration
        self.prepare_calibration_timeDelay(stationOut=stationOut)
        # Reload the useful modules
        self.reload_hydro(idCompar=0, fromStation=stationOut, lastLevel=previousLevel, updateAll=True)
        ## =======
        ## Init
        ## =======
        self.init_optimize_model_f(idOpti=idOpti)

        if return_intervals:
            return isOk, cur_intervals
        else:
            return isOk


    def extract_hydro_from_params(self, idLauncher:int=0, idOpti:int=1, stationOut:str=None,
                                  all_params:np.ndarray=None):
        """
        Extract the hydro from the parameters.

        Args:
            idLauncher (int): The id of the launcher.
            idOpti (int): The id of the optimizer.
            stationOut (str): The name of the station.
            all_params (np.ndarray): The parameters to be tested.

        Returns:
            None

        Raises:
            None
        """
        if all_params is None:
            all_params = self.get_best_params(stationOut=stationOut, quantile=0.01, std=0.03, rmv_near_max=1e-4, apply_clustering=True)

        cur_catch = self.myCases[idLauncher].refCatchment
        self.all_intervals = self._read_opti_intervals(idLauncher=idLauncher)
        # Prepare the optimization model for one station
        self.prepare_optimize_model_F_one_station(idLauncher=idLauncher, idOpti=idOpti, stationOut=stationOut)
        # Init the matrix of hydrographs
        nb_tests = np.shape(all_params)[0]
        optimal_hydro = cur_catch.get_outflow()
        test_hydro = np.zeros((nb_tests, len(optimal_hydro)))

        # Evaluate the model with the parameters
        for i in tqdm(range(nb_tests)):
            cur_p = all_params[i, :-1]
            cur_obj = all_params[i, -1]
            cur_obj2 = self.evaluate_model_optimizer(cur_p, idOpti=idOpti)
            if cur_obj != cur_obj2:
                logging.error("The objective function is not the same as the one computed by the model!")
                logging.error("cur_obj : "+str(cur_obj)+" ; cur_obj2 : "+str(cur_obj2))
            test_hydro[i, :] = cur_catch.get_outflow()

        # Reset the configuration of the optimal parameters in all file and in all variables
        self.reload_optimal_subbasin(idLauncher=idLauncher, idOpti=idOpti, stationOut=stationOut)
        optimal_hydro_2 = cur_catch.get_outflow()
        if not np.allclose(optimal_hydro, optimal_hydro_2):
            logging.error("The optimal hydrograph is not the same as the one computed by the model!")
            logging.error("optimal_hydro : "+str(optimal_hydro)+" ; optimal_hydro_2 : "+str(optimal_hydro_2))

        # Reset the optimisation file
        self.save_opti_dates_to_file(self.all_intervals)
        # One of the test_hydro should be the same as the optimal hydrograph
        # if np.min(test_hydro-optimal_hydro, axis=1)<1e-3:
        #     return test_hydro, optimal_hydro
        # if not np.allclose(test_hydro, optimal_hydro):

        return test_hydro, optimal_hydro

    def make_nd_array(self, c_pointer, shape, dtype=np.float64, order='C', own_data=True,readonly=False):
        arr_size = np.prod(shape[:]) * np.dtype(dtype).itemsize

        buf_from_mem = ct.pythonapi.PyMemoryView_FromMemory
        buf_from_mem.restype = ct.py_object
        buf_from_mem.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
        if readonly:
            buffer = buf_from_mem(c_pointer, arr_size, 0x100)
        else:
            buffer = buf_from_mem(c_pointer, arr_size, 0x200)

        arr = np.ndarray(tuple(shape[:]), dtype, buffer, order=order,)
        if own_data and not arr.flags.owndata:
            return arr.copy()
        else:
            return arr

    def _reload_model_analysis(self, stationOut:str, all_params:np.ndarray)-> tuple[list, np.ndarray]:
        """
        Reload the model analysis for a given station.

        Args:
            stationOut (str): The name of the station.
            all_params (np.ndarray): The parameters to be tested.

        Returns:
            None

        Raises:
            None
        """
        # Check if the excel file already exists and load it to check if some parameters have already been tested
        filename = self.workingDir / (stationOut+"_tests.xlsx")
        # just_params = all_params[:, :-1]
        nb_params = np.shape(all_params)[1] - 1
        if os.path.isfile(filename):
            df = pd.read_excel(self.workingDir / (stationOut+"_tests.xlsx"), sheet_name=stationOut)
            # Extract all the values of the dataframe in a list
            all_data_tested = df.iloc[:, 1:].values.tolist()
            # Extract all the values of the dataframe in a numpy array
            all_params_tested = df.iloc[:, 1:nb_params+1].values
            # Remove the parameters that have already been tested
            new_params = np.array([el for el in all_params if ~np.any(np.all(np.isclose(all_params_tested, el[:-1], atol=1e-6), axis=1))])
            return all_data_tested, new_params

        return [], all_params
