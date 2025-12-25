"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
from wx.dataview import TreeListCtrl, TreeListItem
from wx import dataview, StaticText, TextCtrl
from os.path import exists,join,splitext,dirname
from os import scandir, chdir, getcwd
import numpy as np
import subprocess
import logging
from enum import Enum
import numpy as np
from collections import namedtuple
from pathlib import Path
from osgeo import gdal
from typing import Union, Literal
import json
import pandas as pd
from datetime import datetime as dt
import matplotlib.pyplot as plt
import types

from ..PyTranslate import _
from ..wolfresults_2D import Wolfresults_2D
from ..wolf_array import WolfArray, header_wolf, WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_SINGLE
from .check_scenario import check_file_update, check_file_bc, import_files
from .update_void import create_new_file as update_void
from .imposebc_void import create_new_file as bc_void
from ..wolf_vrt import create_vrt_from_files_first_based, translate_vrt2tif
from ..PyDraw import WolfMapViewer, draw_type
from ..PyHydrographs import Hydrograph
from .update_void import Update_Sim
from ..Results2DGPU import wolfres2DGPU
from ..PyParams import Wolf_Param
from ..PyVertexvectors import Zones, zone, vector, wolfvertex, getIfromRGB, getRGBfromI

# WOLFGPU
try:
    from wolfgpu.simple_simulation import SimpleSimulation, SimulationDuration, SimulationDurationType
    from wolfgpu.results_store import ResultsStore
except:
    logging.error(_('WOLFGPU not installed !'))

# *****************
#  ACCEPTED PREFIX
# *****************
# bath_*.tif
# mann_*.tif
# infil_*.tif

ACCEPTED_PREFIX = ['bath_', 'mann_', 'infil_', 'roof_', 'deck_']

def delete_folder(pth:Path):
    for sub in pth.iterdir():
        if sub.is_dir():
            delete_folder(sub)
        else:
            sub.unlink()
    pth.rmdir() # if you just want to delete the dir content but not the dir itself, remove this line

# extension des fichiers à vérifier
class GPU_2D_file_extensions(Enum):
    TIF  = '.tif'  # raster
    TIFF = '.tiff' # raster
    PY   = '.py'   # python script
    NPY  = '.npy'  # numpy array
    BIN  = '.bin'  # WOLF binary file
    JSON = '.json' # json file
    TXT  = '.txt'  # hydrographs

class IC_scenario(Enum):
    WATERDEPTH  = "h.npy"
    DISCHARGE_X = 'qx.npy'
    DISCHARGE_Y = 'qy.npy'
    BATHYMETRY  = 'bathymetry.npy'

ALL_EXTENSIONS = [cur.value for cur in GPU_2D_file_extensions]

# Predefined keys
WOLF_UPDATE   = 'Wolf update'
WOLF_BC       = 'Wolf boundary conditions'
OTHER_SCRIPTS = 'Other scripts'
IS_SIMUL      = 'is_simul'
IS_SCENARIO   = 'is_scenario'
IS_RESULTS    = 'is_results'
HAS_RESULTS   = 'has_results'
MISSING       = 'missing'
SUBDIRS       = 'subdirs'
DISCHARGES    = 'discharges'
INITIAL_CONDITIONS = 'initial_conditions'

# Définition d'un namedtuple pour représenter les fichiers d'une simulation GPU
_gpu_file = namedtuple('gpufile', ['name', 'type', 'extension'])

# Liste des fichiers à vérifier
class GPU_2D_file(Enum):
    PARAMETERS   = _gpu_file('parameters', str       , GPU_2D_file_extensions.JSON.value)
    BATHYMETRY   = _gpu_file('bathymetry', np.float32, GPU_2D_file_extensions.NPY.value)
    WATER_DEPTH  = _gpu_file('h'         , np.float32, GPU_2D_file_extensions.NPY.value)
    DISCHARGE_X  = _gpu_file('qx'        , np.float32, GPU_2D_file_extensions.NPY.value)
    DISCHARGE_Y  = _gpu_file('qy'        , np.float32, GPU_2D_file_extensions.NPY.value)
    MANNING      = _gpu_file('manning'   , np.float32, GPU_2D_file_extensions.NPY.value)
    COMPUTATION_MASK = _gpu_file('nap'   , np.uint8  , GPU_2D_file_extensions.NPY.value)
    INFILTRATION = _gpu_file('infiltration_zones', np.int32, GPU_2D_file_extensions.NPY.value)
    ROOF         = _gpu_file('bridge_roof'       , np.float32, GPU_2D_file_extensions.NPY.value)
    # DECK         = _gpu_file('bridge_deck'        , np.float32, GPU_2D_file_extensions.NPY.value)

# répertoire de sortie des simulations GPU
RESULT_DIR = 'simul_gpu_results'

class Hydrograph_scenario():
    """ Hydrograph for a scenario """
    def __init__(self, fname:Path, sep:str = '\t', decimal='.') -> None:

        self._data = pd.read_csv(fname, sep=sep, decimal=decimal, header=0, index_col=0)
        self._filename = fname
        self._name = str(fname.with_suffix('').name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def data(self) -> pd.DataFrame:
        return self._data

    def plot(self, figax = None):

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig,ax = figax

        self._data.plot(ax=ax, drawstyle="steps-post")

        return fig,ax

class InitialConditions_scenario():
    """ Initial conditions for a scenario """

    def __init__(self, dir:Path) -> None:

        self.h: np.ndarray     = None
        self.qx: np.ndarray    = None
        self.qy: np.ndarray    = None
        self.bathy: np.ndarray = None

        if (dir / IC_scenario.WATERDEPTH.value).exists():
            self.h = np.load(dir / IC_scenario.WATERDEPTH.value)
        else:
            logging.warning(_('No waterdepth file found !'))
        if (dir / IC_scenario.DISCHARGE_X.value).exists():
            self.qx = np.load(dir / IC_scenario.DISCHARGE_X.value)
        else:
            logging.warning(_('No discharge x file found !'))
        if (dir / IC_scenario.DISCHARGE_Y.value).exists():
            self.qy = np.load(dir / IC_scenario.DISCHARGE_Y.value)
        else:
            logging.warning(_('No discharge y file found !'))
        if (dir /IC_scenario.BATHYMETRY.value).exists():
            self.bathy = np.load(dir / IC_scenario.BATHYMETRY.value)
        else:
            logging.warning(_('No bathymetry file found !'))

    @property
    def z_elevation(self) -> np.ndarray:
        """ Return the elevation of the water surface """

        return self.bathy + self.h

    def set_h_from_z(self, z: np.ndarray):
        """ Set the water depth from the elevation of the water surface """

        assert z.shape == self.bathy.shape, _('Bad shape for z !')

        self.h = z - self.bathy

        self.h[self.h < 0.] = 0.
        self.qx[self.h < 0.] = 0.
        self.qy[self.h < 0.] = 0.

    def save(self, dir:Path):
        """ Save the initial conditions """

        if self.h is not None:
            np.save(dir / IC_scenario.WATERDEPTH.value, self.h)
        if self.qx is not None:
            np.save(dir / IC_scenario.DISCHARGE_X.value, self.qx)
        if self.qy is not None:
            np.save(dir / IC_scenario.DISCHARGE_Y.value, self.qy)
        if self.bathy is not None:
            np.save(dir / IC_scenario.BATHYMETRY.value, self.bathy)

class Config_Manager_2D_GPU:
    """
    Gestionnaire de configurations 2D - code GPU
    """

    def __init__(self, workingdir:str = '', mapviewer:WolfMapViewer = None, python_venv:Path = None, create_ui_if_wx:bool = False) -> None:
        """
        Recherche de toutes les modélisation dans un répertoire et ses sous-répertoires
        """
        self.wx_exists = wx.App.Get() is not None

        self.workingdir:Path = None
        self.wolfgpu:Path = None
        self._py_env:Path = python_venv

        if workingdir == '':
            if self.wx_exists:
                dlg = wx.DirDialog(None,_('Choose directory to scan'), style = wx.FD_OPEN)
                ret = dlg.ShowModal()
                if ret != wx.ID_OK:
                    dlg.Destroy()
                    return
                workingdir = dlg.GetPath()
                dlg.Destroy()
            else:
                logging.error(_('No working directory provided !'))
                return

        if not exists(workingdir):
            logging.error(_('Directory does not exist !'))
            return

        self.find_wolfgpu()
        self.workingdir = Path(workingdir)
        self.mapviewer  = mapviewer

        self._txtctrl = None
        self._ui  = None
        self._create_ui_if_wx = create_ui_if_wx

        self._epsilon = 0.01
        self._filter_independent = True

        self._active_simulation = None

        self.load_data()

    def find_wolfgpu(self):
        """ Find the wolfgpu Path from wolfgpu package"""

        import importlib.util
        import sys

        if self._py_env is None:
            self._py_env = Path(sys.executable).parent

        # Find wolfgpu.exe in script directory
        candidate = self._py_env / 'wolfgpu.exe'

        if candidate.exists():
            self.wolfgpu = candidate
            return

        candidate = self._py_env / 'Scripts' / 'wolfgpu.exe'

        if candidate.exists():
            self.wolfgpu = candidate
            return
        else:
            logging.error(_('WOLFGPU not found !'))
            self.wolfgpu = None
            self._py_env = None


    def _test_ui(self):
        """ Test if the UI is available """

        if self._ui is not None:
            if self._ui._frame.IsShown():
                return True

        return False

    def load_data(self):
        """ Chargement/Rechargement des données """
        self.configs = {}
        self.scan_wdir()
        self.find_files()

        if self._ui is not None:
            # la fenêtre est déjà ouverte
            self._ui.refill_data(self.configs)
        else:
            if self.wx_exists and self._create_ui_if_wx:
                self._ui = UI_Manager_2D_GPU(self.configs, parent=self)


    @property
    def epsilon(self):
        return self._epsilon

    @epsilon.setter
    def epsilon(self, val:float):
        self._epsilon = val

    @property
    def filter_independent(self):
        return self._filter_independent

    @filter_independent.setter
    def filter_independent(self, val:bool):
        self._filter_independent = val

    @property
    def txtctrl(self):
        if self._ui is None:
            return None
        return self._ui._txtctrl

    # Scanning directories
    # --------------------
    def _scan_dir(self, wd:Path, curdict:dict):
        """ Scan récursif d'un répertoire de base et création de sous-dictionnaires """
        for curel in scandir(wd):
            if curel.is_dir():
                newel = curdict[Path(curel)]={}
                self._scan_dir(curel, newel)

    def scan_wdir(self):
        """
        Récupération de tous les répertoires et sous-répertoires
        et placement dans le dictionnaire self.configs
        """
        if self.workingdir.name =='':
            logging.warning(_('Nothing to do !'))
            return

        self._scan_dir(self.workingdir, self.configs)

    # Get properties
    # --------------

    def get_header(self) -> header_wolf:
        """ Get header from .tif file """

        if len(self.configs[GPU_2D_file_extensions.TIF.value])==0:
            return header_wolf()

        curtif = self.configs[GPU_2D_file_extensions.TIF.value][0]

        return self._get_header(curtif)

    def _get_header(self, filearray:Path) -> header_wolf:
        """ Get header from .tif file """

        if not filearray.exists():
            return header_wolf()

        header = header_wolf()

        if filearray.suffix == GPU_2D_file_extensions.TIF.value:

            raster:gdal.Dataset
            raster = gdal.Open(str(filearray))
            geotr = raster.GetGeoTransform()

            # Dimensions
            nbx = raster.RasterXSize
            nby = raster.RasterYSize

            dx = abs(geotr[1])
            dy = abs(geotr[5])
            origx = geotr[0]

            if geotr[5]<0.:
                origy = geotr[3]+geotr[5]*float(nby)
            else:
                origy = geotr[3]

        elif filearray.suffix == GPU_2D_file_extensions.NPY.value:
            with open(filearray, 'rb') as f:
                major, minor = np.lib.format.read_magic(f)
                shape, fortran, dtype = np.lib.format.read_array_header_1_0(f)
                nbx, nby = shape

                dx, dy, origx, origy = (1., 1., 0., 0.)

                # Il y de fortes chances que cette matrice numpy provienne d'une modélisation GPU
                #  et donc que les coordonnées et la résolution soient disponibles dans un fichier parameters.json
                if (filearray.parent / 'parameters.json').exists():
                    with open(filearray.parent / 'parameters.json', 'r') as f:
                        params = json.load(f)

                    if 'parameters' in params.keys():
                        if "dx" in params['parameters'].keys() :
                            dx = float(params['parameters']["dx"])
                        if "dy" in params['parameters'].keys() :
                            dy = float(params['parameters']["dy"])
                        if "base_coord_x" in params['parameters'].keys() :
                            origx = float(params['parameters']["base_coord_x"])
                        if "base_coord_y" in params['parameters'].keys() :
                            origy = float(params['parameters']["base_coord_y"])

        elif filearray.suffix == GPU_2D_file_extensions.BIN.value:

            header.read_txt_header(str(filearray))
            return header

        header.dx = dx
        header.dy = dy
        header.origx = origx
        header.origy = origy
        header.nbx = nbx
        header.nby = nby

        return header

    def get_all_numpy(self) -> list[Path]:
        """ Get all numpy files """

        all_numpy = []

        for key, curdict in self._flat_configs:
            if GPU_2D_file_extensions.NPY.value in curdict.keys():
                if len(curdict[GPU_2D_file_extensions.NPY.value])>0:
                    if not curdict[IS_RESULTS]:
                        all_numpy += curdict[GPU_2D_file_extensions.NPY.value]
                    else:
                        logging.warning(_('Numpy files in simulation directory -- Ignored !'))

        return all_numpy

    def get_all_tif(self) -> list[Path]:
        """ Get all tif files """

        all_tif = []

        for key, curdict in self._flat_configs:
            if GPU_2D_file_extensions.TIF.value in curdict.keys():
                if len(curdict[GPU_2D_file_extensions.TIF.value])>0:
                    all_tif += curdict[GPU_2D_file_extensions.TIF.value]

        return all_tif

    def get_all_sims(self) -> list[Path]:
        """ Get all simulation files """

        all_sims = []

        for key, curdict in self._flat_configs:
            if IS_SIMUL in curdict.keys():
                if curdict[IS_SIMUL]:
                    all_sims.append(curdict['path'])

        return all_sims

    def _flatten_configs(self) -> list[dict]:
        """ flatten configs """

        def _flatten(curdict:dict, ret:list):
            """ flatten a dict """
            for key, val in curdict.items():
                if isinstance(val, dict):
                    ret.append((key, val))
                    _flatten(val, ret)

        self._flat_configs = []
        _flatten(self.configs, self._flat_configs)


    def check_prefix(self, list_tif:list[Path]) -> str:
        """ Check if all files have the right prefix """

        logging.info(_('Checking if prefix of all files are right...\n'))

        logging.info(_('Number of tif files : {}'.format(len(list_tif))))

        standard_files = ['bathymetry.tif',
                          'manning.tif',
                          'infiltration.tif',
                          'h.tif',
                          'qx.tif',
                          'qy.tif',
                          'roof.tif',
                          'deck.tif']

        log = ''
        for curtif in list_tif:

            if curtif.name.lower() in standard_files:
                # No need to test the prefix
                break

            # test if the prefix is in the accepted prefix
            if not any([curtif.name.lower().startswith(curprefix) for curprefix in ACCEPTED_PREFIX]):
                loclog = _('Bad prefix for {} !'.format(curtif.name)) + '\n'

                tests = ['man_', 'mnn_', 'ann_', 'mamn_', 'mannn_']
                for test in tests:
                    if curtif.name.lower().startswith(test):
                        loclog += _('Did you mean "mann_" ?') + '\n'
                        break

                tests = ['bath_', 'bth_', 'ath_', 'bat_', 'bathymetry_']
                for test in tests:
                    if curtif.name.lower().startswith(test):
                        loclog += _('Did you mean "bath_" ?') + '\n'
                        break

                tests = ['infil_', 'infl_', 'nfil_', 'ifil_', 'infiltration_', 'infli_']
                for test in tests:
                    if curtif.name.lower().startswith(test):
                        loclog += _('Did you mean "infil_" ?') + '\n'
                        break

                tests = ['rof_', 'rooof_', 'rofo_', 'oof_', 'roff_']
                for test in tests:
                    if curtif.name.lower().startswith(test):
                        loclog += _('Did you mean "roof_" ?') + '\n'
                        break

                tests = ['dec_', 'dek_', 'dck_', 'deeck_', 'decq_']
                for test in tests:
                    if curtif.name.lower().startswith(test):
                        loclog += _('Did you mean "deck_" ?') + '\n'
                        break

                logging.warning(loclog)

                log += loclog

        return log

    def check_consistency(self) -> str:
        """
        Check consistency of all files

        All numpy files must have the same shape as the tif file in the root directory
        All hydrographs must have the same number of columns
        """

        logging.info(_('Checking consistency of all files except simulation results...\n'))

        logging.info(_('NPY files...'))
        numpyfiles = self.get_all_numpy()

        logging.info(_('Number of numpy files : {}'.format(len(numpyfiles))))

        log = ''
        for curnpy in numpyfiles:

            # test if the shape of the numpy file is the same as the tif file
            # using memmap to avoid loading the whole array in memory -> faster
            arr = np.lib.format.open_memmap(curnpy, mode='r')

            if arr.shape != (self._header.nbx, self._header.nby):
                loclog = _('Bad shape for {} !'.format(curnpy))
                log += loclog + '\n'
                logging.warning(loclog)

            del(arr)

        logging.info(_('Hydrographs...'))
        hydro = self.get_hydrographs()
        if len(hydro) == 0:
            logging.info(_('No hydrographs found !'))
            log += _('No hydrographs found !') + '\n'
        else:
            try:
                nb = hydro[0].data.shape[1]

                logging.info(_('Number of hydrographs : {}'.format(len(hydro))))
                for curhydro in hydro:
                    if curhydro.data.shape[1] != nb:
                        loclog = _('Bad number of columns for {} !'.format(curhydro[0]._filename))
                        log += loclog + '\n'
                        logging.warning(loclog)
            except Exception as e:
                logging.error(_('Error while checking hydrographs: {}').format(e))
                log += _('Error while checking hydrographs: {}').format(e) + '\n'

        return log

    def check_one_simulation(self) -> str:
        """
        Check consistency of one simulation

        """

        if self._active_simulation is None:
            logging.error(_('No active simulation !'))
            return _('No active simulation !')

        logging.info(_('Checking consistency of one simulation...\n'))

        logging.info(_('NPY files...'))
        numpyfiles = self._active_simulation[GPU_2D_file_extensions.NPY.value]
        numpynames = [file.name.lower() for file in numpyfiles]

        logging.info(_('Number of numpy files : {}'.format(len(numpyfiles))))

        if self._header.nbx == 0 or self._header.nby == 0:
            logging.error(_('No header found !'))
            logging.info(_('Trying to get header from first numpy file...'))
            try:
                wa = WolfArray(numpyfiles[0])
                self._header = wa.get_header()
            except Exception as e:
                logging.error(_('Error while getting header from first numpy file: {}').format(e))
                return _('Error while getting header from first numpy file: {}').format(e)

        log = ''
        for curnpy in numpyfiles:

            # test if the shape of the numpy file is the same as the tif file
            # using memmap to avoid loading the whole array in memory -> faster
            arr = np.lib.format.open_memmap(curnpy, mode='r')

            if arr.shape != (self._header.nbx, self._header.nby):
                loclog = _('Bad shape for {} !'.format(curnpy))
                log += loclog + '\n'
                logging.warning(loclog)

            del(arr)

        logging.info(_('Hydrographs...'))
        hydro = self.get_hydrographs()
        if len(hydro) == 0:
            logging.info(_('No hydrographs found !'))
            log += _('No hydrographs found !') + '\n'
        else:
            try:
                nb = hydro[0].data.shape[1]

                logging.info(_('Number of hydrographs : {}'.format(len(hydro))))
                for curhydro in hydro:
                    if curhydro.data.shape[1] != nb:
                        loclog = _('Bad number of columns for {} !'.format(curhydro[0]._filename))
                        log += loclog + '\n'
                        logging.warning(loclog)
            except Exception as e:
                logging.error(_('Error while checking hydrographs: {}').format(e))
                log += _('Error while checking hydrographs: {}').format(e) + '\n'

        for curfile in GPU_2D_file:
            if curfile.value.extension == '.npy':
                if curfile.value.name + curfile.value.extension not in numpynames:
                    loclog = _('Missing file {} !').format(curfile.value.name + curfile.value.extension)
                    log += loclog + '\n'
                    logging.warning(loclog)
                else:
                    try:
                        wa = WolfArray(numpyfiles[numpynames.index(curfile.value.name + curfile.value.extension)])
                        if wa.dtype != curfile.value.type:
                            loclog = _('Bad dtype for {} ! Expected {}, got {}').format(
                                curfile.value.name + curfile.value.extension,
                                curfile.value.type, wa.dtype)
                            log += loclog + '\n'
                            logging.warning(loclog)
                        del(wa)
                    except Exception as e:
                        loclog = _('Error while checking {}: {}').format(
                            curfile.value.name + curfile.value.extension, e)
                        log += loclog + '\n'
                        logging.error(loclog)

        if 'nap.npy' in numpynames:
            nap =  WolfArray(numpyfiles[numpynames.index('nap.npy')])
        else:
            nap = None
            logging.error(_('No nap file found !'))
            log += _('No nap file found !') + '\n'

        if nap is not None:
            if 'infiltration_zones.npy' in numpynames:
                # Check if infiltration zones are consistent
                infil_zones = WolfArray(numpyfiles[numpynames.index('infiltration_zones.npy')])

                if np.any(infil_zones.array[nap.array == 0] != 0):
                    loclog = _('Infiltration zones are not consistent with the nap file !')
                    log += loclog + '\n'

                # find all non zero infiltration zones
                non_zero_infil_zones = list(set(np.unique(infil_zones.array[nap.array == 1])))
                if len(non_zero_infil_zones) == 0:
                    loclog = _('No infiltration zones found !')
                    log += loclog + '\n'
                else:
                    if non_zero_infil_zones[0] == 0:
                        #pop
                        non_zero_infil_zones.pop(0)
                    if len(non_zero_infil_zones) == 0:
                        loclog = _('No infiltration zones found !')
                        log += loclog + '\n'

                    elif non_zero_infil_zones[0] !=1:
                        loclog = _('Infiltration zones should start at 1 ! Found {} instead.').format(non_zero_infil_zones[0])
                        log += loclog + '\n'
                        logging.warning(loclog)

                        # increments
                        if not all([non_zero_infil_zones[i] - non_zero_infil_zones[i-1] == 1 for i in range(1, len(non_zero_infil_zones))]):
                            loclog = _('Infiltration zones are not consecutive !')
                            log += loclog + '\n'
                            logging.warning(loclog)
                del(infil_zones)

            if 'bathymetry.npy' in numpynames:
                # Check if infiltration zones are consistent
                bath = WolfArray(numpyfiles[numpynames.index('bathymetry.npy')])

                if np.any(bath.array[nap.array == 0] != 99999.):
                    loclog = _("Some bathymetry's cells are different of 99999 outside the computation domain !\n")
                    loclog += _('This may lead to unexpected results !')
                    log += loclog + '\n'

                del(bath)

            for file in ['h.npy', 'qx.npy', 'qy.npy']:
                if file in numpynames:
                    # Check if infiltration zones are consistent
                    bath = WolfArray(numpyfiles[numpynames.index(file)])

                    if np.any(bath.array[nap.array == 0] != 0.):
                        loclog = _("Some cells are different of 0.0 outside the computation domain in {}!\n").format(file)
                        loclog += _('This may lead to unexpected results !')
                        log += loclog + '\n'

                    del(bath)

        return log

    # Analyze files
    # -------------

    def _find_files_subdirs(self, wd:Path, curdict:dict, erase_cache:bool = True):
        """ Recherche des fichiers de simulation/scenario dans un répertoire """

        # create list for all extensions
        self._prefill_dict(curdict)
        curdict['path'] = wd

        # scan each file

        for curel in scandir(wd):
            if curel.is_file():
                if not curel.name.startswith('__'):
                    if curel.name.startswith('cache_'):
                        if erase_cache:
                            # Delete cache file if exists. Normally, it should not exist as it is created by WOLF as temporary file.
                            # It will be recreated by WOLF if necessary and destroyed at the end of the process.
                            # The presence of this file is a sign that the simulation creation process was not completed.
                            Path(curel).unlink()
                            continue

                    parts=splitext(curel)

                    if len(parts)==2:
                        ext = parts[1]
                        if ext in ALL_EXTENSIONS:
                            locpath = Path(curel.path)
                            if ext == GPU_2D_file_extensions.PY.value:
                                # test if it is a WOLF update file
                                if check_file_update(locpath):
                                    curdict[ext][WOLF_UPDATE].append(locpath)
                                elif check_file_bc(locpath):
                                    curdict[ext][WOLF_BC].append(locpath)
                                else:
                                    curdict[ext][OTHER_SCRIPTS].append(locpath)

                            else:
                                # ajout du fichier dans la liste
                                curdict[ext].append(locpath)
                else:
                    pass

            elif curel.is_dir():
                if curel.name.startswith('__'):
                  pass
                elif curel.name == RESULT_DIR:
                    curdict[HAS_RESULTS] = True
                else:
                    curdict[SUBDIRS].append(Path(curel.name))

        # test if it is a simulation
        self._test_is_simul(curdict)

        # test if it is a scenario
        self._test_is_scenario(curdict)

        # test if it is a results directory
        self._test_is_results(curdict)

    def _recursive_find_files(self, wd:Path, curdict:dict, erase_cache:bool = True):
        """ Recherche récursive des fichiers de simulation/scenario dans les
        répertoires dont la structure a été traduite en dictionnaire """

        if len(curdict.keys())>0:
            for k in curdict.keys():
                self._recursive_find_files(k, curdict[k])

        if not '__' in wd.name:
            self._find_files_subdirs(wd, curdict, erase_cache)

    def _prefill_dict(self, curdict:dict):
        """ Création des listes pour toutes les extensions """
        for ext in ALL_EXTENSIONS:
            if ext == GPU_2D_file_extensions.PY.value:
                curdict[ext] = {}
                curdict[ext][WOLF_UPDATE] = []
                curdict[ext][WOLF_BC] = []
                curdict[ext][OTHER_SCRIPTS] = []
            else:
                curdict[ext] = []

        curdict[IS_SIMUL]    = False
        curdict[IS_SCENARIO] = False
        curdict[IS_RESULTS]  = False
        curdict[HAS_RESULTS] = False
        curdict[MISSING]     = []
        curdict[SUBDIRS]     = []
        curdict['path']      = None

    def _test_is_simul(self, curdict:dict):
        """ Teste si le répertoire contient des fichiers de simulation """

        ok = True

        # présence du fichier de paramètres
        if GPU_2D_file_extensions.JSON.value in curdict.keys():
            ok &= (GPU_2D_file.PARAMETERS.value.name+GPU_2D_file.PARAMETERS.value.extension).lower() in [cur.name.lower() for cur in curdict[GPU_2D_file_extensions.JSON.value]]

            if ok:
                try:
                    json_data = json.load(open(curdict['path'] / (GPU_2D_file.PARAMETERS.value.name+GPU_2D_file.PARAMETERS.value.extension), 'r'))
                except json.JSONDecodeError as e:
                    logging.error(_('Error decoding JSON file: {}').format(e))
                    curdict['missing'].append(GPU_2D_file_extensions.JSON.value)
                    ok = False
                    return

        else:
            curdict['missing'].append(GPU_2D_file_extensions.JSON.value)
            ok = False

        if ok:
            # Présence des fichiers de calcul
            if GPU_2D_file_extensions.NPY.value in curdict.keys():

                path_bath = curdict['path'] / Path(json_data['maps']['bathymetry'])
                ok &= path_bath.exists()

                path_mann = curdict['path'] / Path(json_data['maps']['manning'])
                ok &= path_mann.exists()

                path_nap = curdict['path'] / Path(json_data['maps']['NAP'])
                ok &= path_nap.exists()

                path_h = curdict['path'] / Path(json_data['maps']['h'])
                ok &= path_h.exists()

                path_qx = curdict['path'] / Path(json_data['maps']['qx'])
                ok &= path_qx.exists()

                path_qy = curdict['path'] / Path(json_data['maps']['qy'])
                ok &= path_qy.exists()

                if 'infiltration_zones' in json_data['maps'].keys():
                    path_infil = curdict['path'] / Path(json_data['maps']['infiltration_zones'])
                    ok &= path_infil.exists()

                if not ok:
                    curdict['missing'].append(GPU_2D_file_extensions.NPY.value)

                # for curfile in GPU_2D_file:
                #     if curfile.value.extension == GPU_2D_file_extensions.NPY.value:
                #         ok &= (curfile.value.name + curfile.value.extension).lower() in [cur.name.lower() for cur in curdict[GPU_2D_file_extensions.NPY.value]]
            else:
                curdict['missing'].append(GPU_2D_file_extensions.NPY.value)
                ok = False
        else:
            pass

        curdict[IS_SIMUL] = ok

    def _test_is_scenario(self, curdict:dict):
        """ Teste si le répertoire contient des fichiers de scénario """

        ok = False

        ok |= len(curdict[GPU_2D_file_extensions.TIF.value])>0
        ok |= len(curdict[GPU_2D_file_extensions.TIFF.value])>0

        for sublist in curdict[GPU_2D_file_extensions.PY.value].values():
            ok |= len(sublist)>0

        curdict[IS_SCENARIO] = ok

    def _test_is_results(self, curdict:dict):
        """ Teste si le répertoire contient des fichiers de résultats """

        ok = False

        # test du fichier 'metadata.json'
        if GPU_2D_file_extensions.JSON.value in curdict.keys():
            for curfile in curdict[GPU_2D_file_extensions.JSON.value]:
                ok = curfile.name.lower() == 'metadata.json'
                if ok:
                    break

        curdict[IS_RESULTS] = ok

    def find_files(self):
        """
        Recehrche des fichiers de simulation/scenario dans les répertoires dont la structure a été traduite en dictionnaire
        """
        if self.workingdir.name =='':
            logging.warning(_('Nothing to do !'))
            return

        self._recursive_find_files(self.workingdir, self.configs)
        self._flatten_configs()

        # initialisation du header
        self._header = self.get_header()

    # Assembly
    # --------
    def get_tree(self, from_path:Path) -> list[Path]:
        """
        Get tree from a path

        Fnd all directories from the current path to the working directory
        """

        curtree = [from_path]

        while str(from_path) != str(self.workingdir):
            from_path = from_path.parent
            curtree.insert(0, from_path)

        return curtree

    def get_dicts(self, from_tree:list[Path]) -> list[dict]:
        """ Get dicts from a tree """

        curdict = [self.configs]

        for curpath in from_tree[1:]:
            curdict.append(curdict[-1][curpath])

        return curdict

    def _select_tif_partname(self, curdict:dict, tifstr:Literal['bath_', 'mann_', 'infil_', 'roof_', 'deck_']):
        """ Select tif files with a 'str' as name's prefix """

        assert tifstr in ACCEPTED_PREFIX, _('Bad prefix !')

        if tifstr == 'bath_':
            forced_add = ['bathymetry.tif']
        elif tifstr == 'mann_':
            forced_add = ['manning.tif']
        elif tifstr == 'infil_':
            forced_add = ['infiltration.tif']
        elif tifstr == 'roof_':
            forced_add = ['roof.tif']
        elif tifstr == 'deck_':
            forced_add = ['deck.tif']

        tif_list = [curtif for curtif in curdict[GPU_2D_file_extensions.TIF.value] \
                    if curtif.name.lower().startswith(tifstr) or \
                       curtif.name.lower() in forced_add]

        tif_list += [curtif for curtif in curdict[GPU_2D_file_extensions.TIFF.value] \
                    if curtif.name.lower().startswith(tifstr) or \
                       curtif.name.lower() in forced_add]

        return tif_list

    def check_nodata(self, from_path:Path):
        """ Check nodata in a path """

        curtree = self.get_tree(from_path)
        curdicts = self.get_dicts(curtree)

        # tous les fichiers tif -> list of lists
        all_tif_bath = [self._select_tif_partname(curdict, 'bath_') for curdict in curdicts]
        all_tif_mann = [self._select_tif_partname(curdict, 'mann_') for curdict in curdicts]
        all_tif_infil = [self._select_tif_partname(curdict, 'infil_') for curdict in curdicts]
        all_tif_roof = [self._select_tif_partname(curdict, 'roof_') for curdict in curdicts]
        all_tif_deck = [self._select_tif_partname(curdict, 'deck_') for curdict in curdicts]

        # flatten list of lists
        all_tif_bath = [curel for curlist in all_tif_bath if len(curlist)>0 for curel in curlist]
        all_tif_mann = [curel for curlist in all_tif_mann if len(curlist)>0 for curel in curlist]
        all_tif_infil = [curel for curlist in all_tif_infil if len(curlist)>0 for curel in curlist]
        all_tif_roof = [curel for curlist in all_tif_roof if len(curlist)>0 for curel in curlist]
        all_tif_deck = [curel for curlist in all_tif_deck if len(curlist)>0 for curel in curlist]

        for cur_lst in [all_tif_bath, all_tif_mann, all_tif_infil, all_tif_roof, all_tif_deck]:
            for cur_tif in cur_lst:
                curarray:WolfArray = WolfArray(cur_tif)
                if curarray.nullvalue != 99999.:
                    curarray.nullvalue = 99999.
                    curarray.set_nullvalue_in_mask()
                    curarray.write_all()
                    logging.warning(_('Bad nodata value for {} !'.format(cur_tif.name)))


    def create_vrt(self, from_path:Path):
        """ Create a vrt file from a path """

        logging.info(_('Checking virtual files...'))

        logging.info(_('Checking nodata values...'))
        self.check_nodata(from_path)

        curtree = self.get_tree(from_path)
        curdicts = self.get_dicts(curtree)

        # tous les fichiers tif -> list of lists
        all_tif_bath = [self._select_tif_partname(curdict, 'bath_') for curdict in curdicts]
        all_tif_mann = [self._select_tif_partname(curdict, 'mann_') for curdict in curdicts]
        all_tif_infil = [self._select_tif_partname(curdict, 'infil_') for curdict in curdicts]
        all_tif_roof = [self._select_tif_partname(curdict, 'roof_') for curdict in curdicts]
        all_tif_deck = [self._select_tif_partname(curdict, 'deck_') for curdict in curdicts]

        # flatten list of lists
        all_tif_bath = [curel for curlist in all_tif_bath if len(curlist)>0 for curel in curlist]
        all_tif_mann = [curel for curlist in all_tif_mann if len(curlist)>0 for curel in curlist]
        all_tif_infil = [curel for curlist in all_tif_infil if len(curlist)>0 for curel in curlist]
        all_tif_roof = [curel for curlist in all_tif_roof if len(curlist)>0 for curel in curlist]
        all_tif_deck = [curel for curlist in all_tif_deck if len(curlist)>0 for curel in curlist]

        # création du fichier vrt
        create_vrt_from_files_first_based(all_tif_bath, from_path / '__bath_assembly.vrt')
        create_vrt_from_files_first_based(all_tif_mann, from_path / '__mann_assembly.vrt')

        if len(all_tif_infil)>0:
            create_vrt_from_files_first_based(all_tif_infil, from_path / '__infil_assembly.vrt')
        else:
            logging.info(_('No infiltration files found ! -> no __infil_assembly.vrt file created !'))

        if len(all_tif_roof)>0:
            create_vrt_from_files_first_based(all_tif_roof, from_path / '__roof_assembly.vrt')
        else:
            logging.info(_('No roof files found ! -> no __roof_assembly.vrt file created !'))

        if len(all_tif_deck)>0:
            create_vrt_from_files_first_based(all_tif_deck, from_path / '__deck_assembly.vrt')
        else:
            logging.info(_('No deck files found ! -> no __deck_assembly.vrt file created !'))

    def create_vec(self,
                   from_path:Path,
                   which:Literal['bath_', 'mann_', 'infil_', 'roof_', 'deck_'] = 'bath_') -> Zones:
        """ Create a vec file from a path """

        assert which in ACCEPTED_PREFIX, _('Bad prefix !')

        curtree = self.get_tree(from_path)
        curdicts = self.get_dicts(curtree)

        # tous les fichiers tif -> list of lists
        all_tif = [self._select_tif_partname(curdict, which) for curdict in curdicts]

        # création du fichier vect
        new_zones = Zones(idx = from_path.name, parent=self)

        for cur_list in all_tif:
            if len(cur_list)>0:

                logging.info(_('Treating {} files...'.format(len(cur_list))))

                for curtif in cur_list:

                    logging.info(_('Start : {} file...'.format(curtif.name)))

                    new_zone = zone(name = curtif.name, parent = new_zones)
                    new_zones.add_zone(new_zone)

                    curarray = WolfArray(curtif)
                    curarray.nullify_border(width=1) # Force a null value border --> necessary to avoid artefacts in the contour as no test is done on the border
                    sux, sux, curvect, interior = curarray.suxsuy_contour()
                    new_zone.add_vector(curvect, forceparent=True)
                    curvect.set_legend_to_centroid(curtif.name)
                    curvect.myprop.color = getIfromRGB((0, 0, 255))
                    curvect.myprop.width = 3

                    bounds = curarray.get_bounds()
                    bounds_vec = vector(name='bounds')

                    bounds_vec.add_vertex(wolfvertex(bounds[0][0], bounds[1][0]))
                    bounds_vec.add_vertex(wolfvertex(bounds[0][1], bounds[1][0]))
                    bounds_vec.add_vertex(wolfvertex(bounds[0][1], bounds[1][1]))
                    bounds_vec.add_vertex(wolfvertex(bounds[0][0], bounds[1][1]))
                    bounds_vec.close_force()

                    bounds_vec.myprop.color = getIfromRGB((255, 0, 0))
                    bounds_vec.myprop.width = 3

                    new_zone.add_vector(bounds_vec, forceparent=True)

                    logging.info(_('End : {} file...'.format(curtif.name)))

        new_zones.find_minmax(update=True)
        new_zones.saveas(str(from_path / (which +'_assembly.vecz')))

        logging.info(_(f'End of {which}_assembly.vecz creation !'))

        return new_zones

    def translate_vrt2tif(self, from_path:Path):
        """ Translate vrt to tif """

        vrtin = ['__bath_assembly.vrt', '__mann_assembly.vrt', '__infil_assembly.vrt', '__roof_assembly.vrt', '__deck_assembly.vrt']
        fout  = ['__bathymetry.tif'   , '__manning.tif', '__infiltration.tif', '__roof.tif', '__deck.tif']

        for curin, curout in zip(vrtin, fout):
            if (from_path / curin).exists():
                translate_vrt2tif(from_path / curin, from_path / curout)

    def apply_scripts_bath_mann_inf_roof_deck(self, from_path:Path):
        """ Apply all scripts """

        filenames = ['__bathymetry.tif', '__manning.tif', '__infiltration.tif', '__roof.tif', '__deck.tif']

        # check if present on disk
        if not all([(from_path / curfile).exists() for curfile in filenames]):
            logging.error(_('At least one of the files is missing !'))

            for curfile in filenames:
                if not (from_path / curfile).exists():
                    logging.error(_(f'{curfile} is missing !'))
            return

        arrays = [WolfArray(from_path / curfile) for curfile in filenames]

        self._apply_scripts_update_topo_maning_inf_roof_deck(from_path, arrays[0], arrays[1], arrays[2], arrays[3], arrays[4])

        # write the files
        arrays[0].write_all(from_path / '__bathymetry_after_scripts.tif')
        arrays[1].write_all(from_path / '__manning_after_scripts.tif')
        arrays[2].write_all(from_path / '__infiltration_after_scripts.tif')
        arrays[3].write_all(from_path / '__roof_after_scripts.tif')
        arrays[4].write_all(from_path / '__deck_after_scripts.tif')


    def _import_scripts(self, from_path:Path, which) -> list[types.ModuleType]:
        """ List all modules in structure and import them.

        As multiple files with a same name can be found in the structure,
        a copy of the file is made in the same folder with a unique name
        and then imported.

        So, if a file is required in the script, the relative import can be used.
        If we cache the file in an other folder, the relative import will not work.

        After the import, the copied files are deleted.
        """

        import shutil

        assert isinstance(from_path, Path), _('Bad type for from_path !')

        curtree = self.get_tree(from_path)
        curdicts = self.get_dicts(curtree)

        # tous les fichiers .py -> list of lists
        all_py = [curpy for curdict in curdicts for curpy in curdict[GPU_2D_file_extensions.PY.value][which]]

        # make a copy in a cache file in the same folder but with a unique name
        to_import = []
        for idx, cur_py in enumerate(all_py):
            cur_py:Path
            cur_dir = cur_py.parent
            cached_name = 'cache_py_' + cur_py.stem + str(idx) + '.py'
            shutil.copy(cur_py, cur_dir / cached_name)
            to_import.append(cur_dir / cached_name)

        imported_mod = import_files(to_import)

        # #del all caches files
        # for cur_py in to_import:
        #     cur_py.unlink()

        return imported_mod

    def _import_scripts_topo_manning_inf_roof_deck(self, from_path:Path) -> list[types.ModuleType]:
        """ import all topo and manning scripts from a path """

        return self._import_scripts(from_path, WOLF_UPDATE)

    def _apply_scripts_update_topo_maning_inf_roof_deck(self,
                                              modules:list[types.ModuleType] | Path | str,
                                              array_bat:WolfArray,
                                              array_mann:WolfArray,
                                              array_inf:WolfArray,
                                              array_roof:WolfArray,
                                              array_deck:WolfArray):
        """ Apply all scripts from a list of modules """

        if isinstance(modules, str):
            modules = Path(modules)

        if isinstance(modules, Path):
            modules = self._import_scripts_topo_manning_inf_roof_deck(modules)

        for curmod in modules:
            instmod = curmod.Update_Sim_Scenario()
            try:
                if not hasattr(instmod, "update_topobathy"):
                    logging.info(_('No update_topobathy method found in the script {}!').format(curmod))
                else:
                    instmod.update_topobathy(array_bat)
            except Exception as e:
                logging.error(_('An error occured during bathymetry script - {}!').format(e))

            try:
                if not hasattr(instmod, "update_manning"):
                    logging.info(_('No update_manning method found in the script {}!').format(curmod))
                else:
                    instmod.update_manning(array_mann)
            except Exception as e:
                logging.error(_('An error occured during manning script - {}!').format(e))

            try:
                if not hasattr(instmod, "update_infiltration"):
                    logging.info(_('No update_infiltration method found in the script {}!').format(curmod))
                else:
                    instmod.update_infiltration(array_inf)
            except Exception as e:
                logging.error(_('An error occured during infiltration script - {}!').format(e))

            try:
                if not hasattr(instmod, "update_roof"):
                    logging.info(_('No update_roof method found in the script {}!').format(curmod))
                else:
                    instmod.update_roof(array_roof)
            except Exception as e:
                logging.error(_('An error occured during roof script - {}!').format(e))

            try:
                if not hasattr(instmod, "update_deck"):
                    logging.info(_('No update_deck method found in the script {}!').format(curmod))
                else:
                    instmod.update_deck(array_deck)
            except Exception as e:
                logging.error(_('An error occured during deck script - {}!').format(e))

    def _import_scripts_bc(self, from_path:Path) -> list[types.ModuleType]:
        """ Import all BC's scripts from a path """

        return self._import_scripts(from_path, WOLF_BC)

    def _apply_scripts_bc(self, modules:list[types.ModuleType] | Path | str, sim:"SimpleSimulation"):
        """ Apply all scripts from a list of modules """

        if isinstance(modules, str):
            modules = Path(modules)

        if isinstance(modules, Path):
            modules = self._import_scripts_bc(modules)

        for curmod in modules:
            try:
                curmod.Impose_BC_Scenario().impose_bc(sim)
            except Exception as e:
                logging.error(_('An error occured during BC script - {}!').format(e))


    def load_hydrograph(self, path:Path, toplot=True) -> tuple[Hydrograph_scenario, plt.Figure, plt.Axes]:
        """ Load hydrograph from a path """
        hydro = Hydrograph_scenario(path)
        fig,ax = None, None
        if toplot:
            fig,ax = hydro.plot()
            fig.show()

        return hydro, fig, ax

    def load_ic(self, path:Path) -> InitialConditions_scenario:
        """ Load initial conditions from a path """

        path = Path(path)

        low_keys = [Path(curkey).name.lower() for curkey in self.configs.keys()]
        if INITIAL_CONDITIONS in low_keys:
            return InitialConditions_scenario(self.workingdir / INITIAL_CONDITIONS / path.stem.replace('sim_', ''))
        else:
            return None

    def get_hydrographs(self) -> list[Hydrograph]:
        """ Get all hydrographs"""

        all_hydro = []

        low_keys = [Path(curkey).name.lower() for curkey in self.configs.keys()]
        if DISCHARGES in low_keys:
            curkey = [curkey for curkey in self.configs.keys()][low_keys.index(DISCHARGES)]
            list_hydro = self.configs[curkey][GPU_2D_file_extensions.TXT.value]

            for curq in list_hydro:
                all_hydro.append(self.load_hydrograph(curq, toplot=False)[0])

        return all_hydro

    def get_initial_conditions(self) -> list[InitialConditions_scenario]:
        """ Get all initial conditions """

        low_keys = [Path(curkey).name.lower() for curkey in self.configs.keys()]
        if INITIAL_CONDITIONS in low_keys:
            return [self.load_ic(curpath) for curpath in self.configs.keys()[low_keys.index(INITIAL_CONDITIONS)]]
        else:
            return []

    def get_names_hydrographs(self) -> list[str]:

        all_hydros = self.get_hydrographs()
        names = [curhydro.name for curhydro in all_hydros]

        return names

    def get_name_initial_conditions(self) -> list[str]:

        low_keys = [Path(curkey).name.lower() for curkey in self.configs.keys()]
        names = []
        if INITIAL_CONDITIONS in low_keys:
            dirdict = self.configs[list(self.configs.keys())[low_keys.index(INITIAL_CONDITIONS)]][SUBDIRS]
            names = [curpath.name for curpath in dirdict]

        return names

    def create_void_infil(self):
        """  create void infiltration_zones file """

        if (self.workingdir / 'bathymetry.tif').exists():
            locheader = self.get_header()
            infilzones = WolfArray(srcheader=locheader, whichtype= WOLF_ARRAY_FULL_INTEGER)
            infilzones.array.data[:,:] = 0
            infilzones.nullvalue = -1
            infilzones.write_all(str(self.workingdir / 'infiltration.tif'))

            if (self.workingdir / 'infiltration.tif').exists():
                logging.info(_('infiltration.tif created and set to -1 ! -- Please edit it !'))
            else:
                logging.error(_("infiltration.tif not created ! --  Does 'bathymetry.tif' or any '.tif' file exist in the root directory ?"))
        else:
            logging.error(_("No 'bathymetry.tif' file found in the root directory !"))

    def create_void_dtm(self):
        """ create void dtm file """
        if (self.workingdir / 'bathymetry.tif').exists():
            locheader = self.get_header()
            dtm = WolfArray(srcheader=locheader, whichtype= WOLF_ARRAY_FULL_SINGLE)
            dtm.array.data[:,:] = 99999.
            dtm.nullvalue = 99999.
            dtm.write_all(str(self.workingdir / 'dtm.tif'))

            if (self.workingdir / 'dtm.tif').exists():
                logging.info(_('dtm.tif created and set to 99999. ! -- Please edit it !'))
            else:
                logging.error(_("dtm.tif not created ! --  Does 'bathymetry.tif' or any '.tif' file exist in the root directory ?"))
        else:
            logging.error(_("No 'bathymetry.tif' file found in the root directory !"))

    def create_void_roof(self):
        """ create void roof file """

        if (self.workingdir / 'bathymetry.tif').exists():
            locheader = self.get_header()
            roof = WolfArray(srcheader=locheader, whichtype= WOLF_ARRAY_FULL_SINGLE)
            roof.array.data[:,:] = 99999.
            roof.nullvalue = 99999.
            roof.write_all(str(self.workingdir / 'roof.tif'))

            if (self.workingdir / 'roof.tif').exists():
                logging.info(_('roof.tif created and set to 99999. ! -- Please edit it !'))
            else:
                logging.error(_("roof.tif not created ! --  Does 'bathymetry.tif' or any '.tif' file exist in the root directory ?"))
        else:
            logging.error(_("No 'bathymetry.tif' file found in the root directory !"))

    def create_void_deck(self):
        """ create void deck file """

        if (self.workingdir / 'bathymetry.tif').exists():
            locheader = self.get_header()
            deck = WolfArray(srcheader=locheader, whichtype= WOLF_ARRAY_FULL_SINGLE)
            deck.array.data[:,:] = 99999.
            deck.nullvalue = 99999.
            deck.write_all(str(self.workingdir / 'deck.tif'))

            if (self.workingdir / 'deck.tif').exists():
                logging.info(_('deck.tif created and set to 99999. ! -- Please edit it !'))
            else:
                logging.error(_("deck.tif not created ! --  Does 'bathymetry.tif' or any '.tif' file exist in the root directory ?"))
        else:
            logging.error(_("No 'bathymetry.tif' file found in the root directory !"))


    def combine_bath_roof_deck(self, bathymetry:WolfArray,
                               bridge_roof:WolfArray, bridge_deck:WolfArray,
                               threshold:float = .05) -> str:
        """ Verify bathymetry, roof and deck """

        ret = ''
        if bridge_roof is None:
            ret	+= _('No bridge roof found !')
        if bridge_deck is None:
            ret	+= _('No bridge deck found !')

        if ret != '':
            logging.error(ret)
            return ret

        # si la matrice de toit de pont est plus basse que la bathymétrie, on met à 99999
        # la bathymétrie et le toit de pont.
        # Ainsi, ces maille seront infranchissables.
        # Cela peut être utile pour discrétiser les piles dans les données du toit, plutôt que de les
        # laisser inclure dans un fichier bath_ séparé.

        mask_roof = np.where(bridge_roof.array.data != 99999.)
        mask_deck = np.where(bridge_deck.array.data != 99999.)
        if mask_roof[0].shape != mask_deck[0].shape:
            ret += _('Roof and deck have different shapes !\n')
            ret += _(' -- If not desired, please check your data\n')

        mask = np.where(bridge_roof.array.data > bridge_deck.array.data)
        if mask[0].shape[0] > 0:
            ret += _('Some roof values are higher than deck values !\n')
            ret += _('-- Roof values will be set to deck values\n')
            bridge_roof.array.data[mask] = bridge_deck.array.data[mask]

        mask = np.where(bridge_roof.array.data <= bathymetry.array.data)
        if mask[0].shape[0] > 0:
            ret += _('Some roof values are lower than or equal to bathymetry values !\n')
            ret += _(' -- Roof values will be set to 99999\n')
            ret += _(' -- Bathymetry values will be set to max(bath, deck)\n')
            ret += _(' -- These cells will remain impassable until the water level rises above them\n')
            bridge_roof.array.data[mask] = 99999.
            bathymetry.array.data[mask]  = np.maximum(bridge_deck.array.data[mask], bathymetry.array.data[mask])

        mask = np.where(bridge_roof.array.data - bathymetry.array.data < threshold)
        if mask[0].shape[0] > 0:
            ret += _('Some roof values are close to bathymetry values (threshold is {} cm) !\n').format(int(threshold*100))
            ret += _(' -- Bathymetry will be impose to the deck level\n')
            ret += _(' -- New roof values will be set to 99999\n')
            ret += _(' -- New deck values will be set to 99999\n')
            bathymetry.array.data[mask] = bridge_deck.array.data[mask]
            bridge_deck.array.data[mask] = 99999.
            bridge_roof.array.data[mask] = 99999.

        if ret != '':
            logging.warning(ret)

        bridge_deck.nullvalue = 99999.
        bridge_roof.nullvalue = 99999.
        bridge_deck.mask_data(99999.)
        bridge_roof.mask_data(99999.)

        return ret

    def create_simulation(self,
                          dir:Path,
                          idx_hydros:list[int] = [-1],
                          delete_existing:bool = False,
                          preserve_ic:bool=False,
                          callback = None) -> list[Path]:
        """ Create a simulation from different hydrographs """

        if isinstance(dir, str):
            dir = Path(dir)

        # test if dir is in the tree
        dirs_key  = [key for key, curdict in self._flat_configs]
        dirs_dict = [curdict for key, curdict in self._flat_configs]

        if not dir in dirs_key:
            logging.error(_('Directory {} not found ! - Aborting !'.format(dir)))
            return

        # dictionnaire associé au scénario du répertoire
        scen_dict = dirs_dict[dirs_key.index(dir)]

        # search for hydrographs
        hydros = self.get_hydrographs()
        names  = self.get_names_hydrographs()
        if idx_hydros == [-1]:
            idx_hydros = list(range(len(hydros)))

        maxhydro = max(idx_hydros)
        minhydro = min(idx_hydros)

        if maxhydro >= len(hydros):
            logging.error(_('Index {} too high ! - Aborting !'.format(maxhydro)))
            return
        if minhydro < 0:
            logging.error(_('Index {} too low ! - Aborting !'.format(minhydro)))
            return

        # select hydrographs
        used_hydros = [hydros[curidx] for curidx in idx_hydros]
        used_names  = [names[curidx] for curidx in idx_hydros]

        ic_available = self.get_name_initial_conditions()
        used_ic = []

        for curname in used_names:
            if curname in ic_available:
                used_ic.append(self.load_ic(curname))
            else:
                used_ic.append(None)

        if len(used_hydros)==0:
            logging.error(_('No hydrograph selected ! - Aborting !'))
            return

        # create subdirectories for each hydrograph
        used_dirs = [Path(dir / ('simulations/sim_' + curname)) for curname in used_names]
        for curdir in used_dirs:
            if curdir.exists():
                if delete_existing:
                    logging.info(_('Directory {} already exists ! -- Deleting it !'.format(curdir)))
                    try:
                        delete_folder(curdir)
                    except:
                        logging.error(_('Directory {} not deleted !'.format(curdir)))
                else:
                    logging.info(_('Directory {} already exists ! -- Using it'.format(curdir)))
            else:
                logging.info(_('Creating directory {} !'.format(curdir)))
                curdir.mkdir(parents=True)

        # Assembly of bathymetry, manning and infiltration if exists
        self.create_vrt(dir)
        self.translate_vrt2tif(dir)

        quit = False
        if not (dir / '__bathymetry.tif').exists():
            logging.error(_('No __bathymetry.tif found !'))
            quit = True
        if not (dir / '__manning.tif').exists():
            logging.error(_('No __manning.tif found !'))
            quit = True

        if quit:
            logging.error(_('Bad assembly operation -- Simulation creation aborted !'))
            return

        bat = WolfArray(str(dir / '__bathymetry.tif'))
        man = WolfArray(str(dir / '__manning.tif'))

        # check for infiltration
        if exists(dir / '__infiltration.tif'):
            infiltration = WolfArray(str(dir / '__infiltration.tif'))

            if infiltration.nullvalue != 0:
                infiltration.nullvalue = 0
                infiltration.set_nullvalue_in_mask()
                logging.warning(_('Bad null value for infiltration ! -- Set to 0 !'))

            if infiltration.wolftype != WOLF_ARRAY_FULL_INTEGER:
                logging.error(_('Infiltration .tif must be a full integer array ! -- The array will be ignored !'))
                infiltration = WolfArray(srcheader=bat.get_header(), whichtype= WOLF_ARRAY_FULL_INTEGER)
                infiltration.array.data[:,:] = 0

        else:
            infiltration = WolfArray(srcheader=bat.get_header(), whichtype= WOLF_ARRAY_FULL_INTEGER)
            infiltration.array.data[:,:] = 0
            infiltration.nullvalue = 0

        # check for roof
        if exists(dir / '__roof.tif'):
            roof = WolfArray(str(dir / '__roof.tif'))
            if roof.wolftype != WOLF_ARRAY_FULL_SINGLE:
                logging.error(_('Roof .tif must be a full single array ! -- The array will be ignored !'))
                roof = WolfArray(srcheader=bat.get_header(), whichtype= WOLF_ARRAY_FULL_SINGLE)
                roof.array.data[:,:] = 99999.
                roof.nullvalue = 99999.
                roof.nbnotnull = 0
        else:
            roof = WolfArray(srcheader=bat.get_header(), whichtype= WOLF_ARRAY_FULL_SINGLE)
            roof.array.data[:,:] = 99999.
            roof.nullvalue = 99999.
            roof.nbnotnull = 0

        # check for deck
        if exists(dir / '__deck.tif'):
            deck = WolfArray(str(dir / '__deck.tif'))
            if deck.wolftype != WOLF_ARRAY_FULL_SINGLE:
                logging.error(_('Deck .tif must be a full single array ! -- The array will be ignored !'))
                deck = WolfArray(srcheader=bat.get_header(), whichtype= WOLF_ARRAY_FULL_SINGLE)
                deck.array.data[:,:] = 99999.
                deck.nullvalue = 99999.
                deck.nbnotnull = 0
        else:
            deck = WolfArray(srcheader=bat.get_header(), whichtype= WOLF_ARRAY_FULL_SINGLE)
            deck.array.data[:,:] = 99999.
            deck.nullvalue = 99999.
            deck.nbnotnull = 0

        # applying Python scrpitps on ARRAYS
        self._apply_scripts_update_topo_maning_inf_roof_deck(dir, bat, man, infiltration, roof, deck)

        self.combine_bath_roof_deck(bat, roof, deck)

        # save arrays on disk
        bat.write_all(str(dir / '__bathymetry_after_scripts.tif'))
        man.write_all(str(dir / '__manning_after_scripts.tif'))
        infiltration.write_all(str(dir / '__infiltration_after_scripts.tif'))
        roof.write_all(str(dir / '__roof_after_scripts.tif'))
        deck.write_all(str(dir / '__deck_after_scripts.tif'))

        # create simulation
        allsims = []
        for id_sim, (curdir, curhydro, curic) in enumerate(zip(used_dirs, used_hydros, used_ic)):

            if callback is not None:
                callback(id_sim)

            # instanciation de la simulation
            cursim = SimpleSimulation(self._header.nbx, self._header.nby)

            # paramétrage spatial
            cursim.param_dx = self._header.dx
            cursim.param_dy = self._header.dy
            cursim.param_base_coord_ll_x = self._header.origx
            cursim.param_base_coord_ll_y = self._header.origy

            # paramétrage hydraulique/numérique
            cursim.param_courant = .4
            cursim.param_runge_kutta = .5

            # associating arrays to simulation
            cursim.bathymetry = bat.array.data
            cursim.manning    = man.array.data
            cursim.nap        = np.zeros((self._header.nbx, self._header.nby), dtype=np.uint8)
            cursim.nap[cursim.bathymetry != 99999.] = 1

            if curic is None:
                curic:InitialConditions_scenario
                # No global initial conditions
                if not preserve_ic:
                    # reset initial conditions
                    cursim.h          = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)
                    cursim.qx         = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)
                    cursim.qy         = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)
                else:
                    # Using initial conditions from disk - sim directory
                    if (curdir / 'h.npy').exists():
                        cursim.h = np.load(curdir / 'h.npy')
                    else:
                        cursim.h = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)
                    if (curdir / 'qx.npy').exists():
                        cursim.qx = np.load(curdir / 'qx.npy')
                    else:
                        cursim.qx = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)
                    if (curdir / 'qy.npy').exists():
                        cursim.qy = np.load(curdir / 'qy.npy')
                    else:
                        cursim.qy = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)
            else:
                if not preserve_ic:
                    # Using global initial conditions if available
                    if curic.h is not None:
                        cursim.h = curic.h
                    else:
                        cursim.h = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)
                    if curic.qx is not None:
                        cursim.qx = curic.qx
                    else:
                        cursim.qx = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)

                    if curic.qy is not None:
                        cursim.qy = curic.qy
                    else:
                        cursim.qy = np.zeros((self._header.nbx, self._header.nby), dtype=np.float32)


            # check if infiltration array is strictly inside nap
            if not np.all(cursim.nap[infiltration.array.data[infiltration.array.data > 0]] == 1):
                logging.warning(_('Infiltration zones must be strictly inside the NAP !'))
                logging.warning(_('Infiltration zones outside NAP will be set to 0 !'))

                #count number of infiltration zones outside NAP
                nb_outside = np.sum(infiltration.array.data[(infiltration.array.data > 0) & (cursim.nap == 0)])
                logging.warning(_('Number of infiltration zones outside NAP: {}').format(nb_outside))
                # index infiltration zones outside NAP
                indices = list(set(infiltration.array.data[(infiltration.array.data > 0) & (cursim.nap == 0)]))
                logging.warning(_('Indices of infiltration zones outside NAP: {}').format(indices))
                infiltration.array.data[(infiltration.array.data > 0) & (cursim.nap == 0)] = 0

            cursim.infiltration_zones = np.asarray(infiltration.array.data, dtype=np.int32)

            if roof.nbnotnull == 0:
                cursim.bridge_roof = None
                logging.info(_("No cells defined as roof ! -- Roof will be ignored !"))
            else:
                cursim.bridge_roof = roof.array.data
                logging.info(_("You have {} cells defined as roof").format(roof.nbnotnull))

            # if deck.nbnotnull == 0:
            #     cursim.bridge_deck = None
            #     logging.info(_("No cells defined as deck ! -- Deck will be ignored !"))
            # else:
            #     cursim.bridge_deck = deck.array.data
            #     logging.info(_("You have {} cells defined as deck").format(deck.nbnotnull))

            # paramétrage hydro

            # add hydrograph
            for idx, curline in curhydro.data.iterrows():
                cursim.add_infiltration(float(idx), [float(cur) for cur in curline.values])
            if curhydro.data.index[-1] == 0:
                cursim.param_duration = SimulationDuration(SimulationDurationType.SECONDS, float(86400))
                cursim.add_infiltration(float(86400), [float(cur) for cur in curline.values])
            elif curhydro.data.index[-1]==999999.:
                cursim.param_duration = SimulationDuration(SimulationDurationType.SECONDS, float(86400))
            else:
                cursim.param_duration = SimulationDuration(SimulationDurationType.SECONDS, float(curhydro.data.index[-1]))

            # check for infiltration zones vs hydrograph
            hydro = cursim.infiltrations_chronology
            nb_zones = len(hydro[0][1])
            if infiltration.array.max() != nb_zones:
                logging.error(_('You must have {} Infiltration zones but {} are defined!'.format(nb_zones, infiltration.array.max())))
                return

            # default reporting period
            cursim._param_report_period = SimulationDuration.from_seconds(3600)

            # applying Python scrpitps on SIMULATION --> Boundary conditions
            self._apply_scripts_bc(dir, cursim)

            # cursim.h[cursim.infiltration_zones > 0] = .5

            # save simulation
            cursim.save(curdir)

            logging.info(cursim.check_errors())
            logging.info(_('Simulation {} created !'.format(curdir)))

            with open(curdir / 'quickrun.bat', 'w', encoding='utf-8') as f:
                f.write("@echo off\n")
                f.write("\n")
                f.write(str(curdir.drive) + '\n')
                f.write('cd {}\n'.format(str(curdir.parent)))
                f.write("\n")
                f.write("set WOLFGPU_PARAMS=-quickrun " + str(curdir.name) + "\n")
                f.write("\n")
                f.write("where wolfgpu.exe\n")
                f.write("IF %ERRORLEVEL%==0 (\n")
                f.write("wolfgpu %WOLFGPU_PARAMS%\n")
                f.write("goto :exit\n")
                f.write(")\n")
                f.write("\n")
                f.write("echo -------------------------------\n")
                f.write("echo ERROR !!!\n")
                f.write("echo -------------------------------\n")
                f.write("echo I can't find wolfgpu.exe.\n")
                f.write("echo It is normally installed in the 'Scripts' subdirectory of your python\n")
                f.write("echo directory (or environment).\n")
                f.write("echo This 'Scripts' subdirectory must be available on the PATH environment variable.\n")
                f.write("echo I am now going to try to run wolfgpu as a regular python module\n")
                f.write("echo -------------------------------\n")
                f.write("pause\n")
                f.write("python -m wolfgpu.cli %WOLFGPU_PARAMS%\n")
                f.write(":exit\n")

            allsims.append(curdir / 'quickrun.bat')

        logging.info(_('Simulation creation finished !'))
        logging.warning(_('Do not forget to update/set the boundary conditions if not set by scripts !'))

        return allsims

    def create_batch(self, path:Path, allsims:list[Path]) -> str:
        """ Create a batch file """

        if len(allsims) == 0:
            return

        batch = ''
        batch += str(allsims[0].drive) + '\n'
        for cursim in allsims:
            cursim:Path
            batch += 'cd {}\n'.format(str(cursim.parent))
            batch += 'call ' + str(cursim.name) + '\n'

        with open(path, 'w', encoding='utf-8') as f:
            f.write(batch)

        if self.wolfgpu is None:
            logging.warning('****************************************************')
            logging.warning(_('Wolfgpu.exe not found !'))
            logging.warning(_('It is normally installed in the "Scripts" subdirectory of your python directory (or environment).'))
            logging.warning(_('This "Scripts" subdirectory must be available on the PATH environment variable.'))
            logging.warning('****************************************************')
        else:
            logging.info('****************************************************')
            logging.info(_('Wolfgpu.exe found in {}!').format(self.wolfgpu))
            logging.info(_('You can now run the simulations !'))
            logging.info(_('Do not forget to activate your Python virtual environment if you are using one !'))
            logging.info('****************************************************')

        return batch

    def run_batch(self, batch:Path):
        """ run a batch file in a subprocess """

        if not batch.exists():
            logging.error(_('Batch file {} does not exist !'.format(batch)))
            return
        if not batch.is_file():
            logging.error(_('Batch file {} is not a file !'.format(batch)))
            return
        if batch.suffix != '.bat':
            logging.error(_('Batch file {} is not a .bat file !'.format(batch)))
            return

        import subprocess
        # Execute the batch file in a separate process
        subprocess.Popen(str(batch), shell=True)

    def get_mapviewer(self):
        """ Get the mapviewer object """

        return self.mapviewer

    def transfer_ic(self, dir1: Path, dir2: Path):
        """ Transfer IC from one sim to another """

        ic1 = self.load_ic(dir1)

        if ic1 is None:
            logging.error(_('No IC found in {} !'.format(dir1)))
            return

        ic2 = self.load_ic(dir2)

        if ic2 is None:
            logging.error(_('No IC found in {} !'.format(dir2)))
            return

        ic2.qx = ic1.qx
        ic2.qy = ic1.qy
        ic2.set_h_from_z(ic1.z_elevation)

        ic2.save(dir2)

    def extract_tif(self, from_path:Path, to_path:Path):
        """ Extract tif files from IC """

        from_path = Path(from_path)
        to_path = Path(to_path)

        prefix = from_path.parent.parent.parent.name + '_' + from_path.parent.parent.name + '_' + from_path.name

        ext = ['h.npy', 'qx.npy', 'qy.npy', 'bathymetry.npy']

        for curext in ext:
            tmp_array = WolfArray(from_path / curext)
            tmp_array.write_all((to_path / (prefix + '_' + curext)).with_suffix('.tif'))

class UI_Manager_2D_GPU():
    """ User Interface for scenario 2D GPU """

    def __init__(self, data:dict, parent:Config_Manager_2D_GPU) -> None:
        self._parent = parent
        self._batch = None
        self.create_UI()
        # Fill tree with data
        self._append_configs2tree(data, self._root)

        self._txtctrl.Clear()
        self._txtctrl.write(str(self._parent._header))

        self._wp:dict[SimpleSimulation, Wolf_Param] = {}

    def refill_data(self, data:dict):
        """ Fill tree with data """

        # la fenêtre est déjà ouverte
        self._treelist.DeleteAllItems()
        self._txtctrl.SetBackgroundColour(wx.WHITE)
        self._txtctrl.SetForegroundColour(wx.BLACK)
        self._txtctrl.Clear()

        # Fill tree with data
        self._append_configs2tree(data, self._root)

    def create_UI(self):
        """
        Création de l'interface graphique

        Partie latérale gauche - arbre des simulations
        Partie latérale droite - boutons d'actions
        Partie inférieure - affichage des informations

        """

        # frame creation
        self._frame = wx.Frame(self._parent.get_mapviewer(), wx.ID_ANY, _('Scenario WOLF2D_GPU'), size=(800,800))

        # sizers creation -- frame's structure
        sizer_updown = wx.BoxSizer(wx.VERTICAL)
        sizer_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons = wx.BoxSizer(wx.VERTICAL)

        sizer_txt_ckd = wx.BoxSizer(wx.HORIZONTAL)

        # # Liste des chemins d'accès aux icônes
        # icon_paths = []
        # icon_path = Path(__file__).parent / '..\\icons'
        # for curicon in scandir(icon_path):
        #     if curicon.is_file():
        #         icon_paths.append(Path(curicon))

        # # Création de l'objet wx.ImageList
        # image_list = wx.ImageList()

        # # Chargement des icônes dans l'image list
        # for path in icon_paths:
        #     icon = wx.Icon(str(path), wx.BITMAP_TYPE_PNG)
        #     image_list.Add(icon)

        # tree creation
        self._treelist = TreeListCtrl(self._frame,
                                      style=dataview.TL_CHECKBOX|
                                      wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_HAS_BUTTONS)

        # self._treelist.AssignImageList(image_list)

        # tree actions
        self._treelist.Bind(dataview.EVT_TREELIST_ITEM_CHECKED, self.OnCheckItem)            # check/uncheck
        self._treelist.Bind(dataview.EVT_TREELIST_ITEM_ACTIVATED, self.OnActivateTreeElem)   # double click

        # tree root
        self._root = self._treelist.GetRootItem()
        self._selected_item = None
        self._treelist.AppendColumn(_('2D GPU Models'))

        # multilines text control for information
        self._txtctrl = TextCtrl(self._frame, style=wx.TE_MULTILINE|wx.TE_BESTWRAP|wx.TE_RICH)

        # Action buttons
        # --------------
        self._reload = wx.Button(self._frame,label = _('Reload/Update structure'))
        self._reload.Bind(wx.EVT_BUTTON,self.onupdate_structure)
        self._reload.SetToolTip(_('reScan the directory and reload the entire structure'))

        tif_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._create_void_infil = wx.Button(self._frame,label = _('Create .tif infiltration zones'))
        self._create_void_infil.Bind(wx.EVT_BUTTON,self.oncreate_void_infil)
        self._create_void_infil.SetToolTip(_('Create a void infiltration zones file based on bathymetry.tif'))

        self._create_dtm = wx.Button(self._frame,label = _('Create .tif DTM'))
        self._create_dtm.Bind(wx.EVT_BUTTON,self.oncreate_dtm)
        self._create_dtm.SetToolTip(_('Create a DTM file based on bathymetry.tif\n\n - bathymetry.tif must be present in the root directory'))

        tif_sizer.Add(self._create_void_infil, 1, wx.EXPAND)
        tif_sizer.Add(self._create_dtm, 1, wx.EXPAND)

        bridge_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._create_void_roof = wx.Button(self._frame,label = _('Create .tif bridge/culvert roof elevation'))
        self._create_void_roof.Bind(wx.EVT_BUTTON,self.oncreate_void_roof)
        self._create_void_roof.SetToolTip(_('Create a void roof file based on bathymetry.tif'))

        self._create_void_deck = wx.Button(self._frame,label = _('Create .tif bridge/culvert deck elevation'))
        self._create_void_deck.Bind(wx.EVT_BUTTON,self.oncreate_void_deck)
        self._create_void_deck.SetToolTip(_('Create a void deck file based on bathymetry.tif'))

        bridge_sizer.Add(self._create_void_roof, 1, wx.EXPAND)
        bridge_sizer.Add(self._create_void_deck, 1, wx.EXPAND)

        self._create_void_scripts = wx.Button(self._frame,label = _('Create void scripts'))
        self._create_void_scripts.Bind(wx.EVT_BUTTON,self.oncreate_void_scripts)
        self._create_void_scripts.SetToolTip(_('Create void script files for topography, manning and infiltration'))

        self._create_vrt = wx.Button(self._frame,label = _('Assembly .vrt to current level'))
        self._create_vrt.Bind(wx.EVT_BUTTON,self.oncreatevrt)
        self._create_vrt.SetToolTip(_('Create a .vrt file from all bathymetry, manning, infiltration, roof and deck .tif files\nBe sure that all files are right named !\n\n - bathymetry must contain "bath"\n - manning must contain "mann"\n - infiltration must contain "infil"\n - roof must contain "roof"\n - deck must contain "deck"'))

        self._translate_vrt = wx.Button(self._frame,label = _('Translate .vrt to .tif'))
        self._translate_vrt.Bind(wx.EVT_BUTTON,self.ontranslatevrt2tif)
        self._translate_vrt.SetToolTip(_('Translate .vrt files to .tif files\n\n - __bath_assembly.vrt -> __bathymetry.tif\n - __mann_assembly.vrt -> __manning.tif\n - __infil_assembly.vrt -> __infiltration.tif\n - __roof_assembly.vrt -> __roof.tif\n - __deck_assembly.vrt -> __deck.tif'))

        self._apply_scripts = wx.Button(self._frame,label = _('Apply scripts on bathymetry, manning, infiltration, roof and deck elevation'))
        self._apply_scripts.Bind(wx.EVT_BUTTON,self.onapply_scripts)
        self._apply_scripts.SetToolTip(_('Apply scripts on bathymetry, manning and infiltration\n\n - bathymetry.tif\n - manning.tif\n - infiltration.tif\n - roof.tif\n - deck.tif\n\nThe scripts must be in the structure starting with parent directory and descending.'))

        self._create_vec = wx.Button(self._frame,label = _('Search spatial coverage from current level'))
        self._create_vec.Bind(wx.EVT_BUTTON,self.oncreatevec)
        self._create_vec.SetToolTip(_('Create a .vecz file (with contour and global bounds) from all bathymetry and manning .tif files\nBe sure that all files are right named !\n\n - bathymetry must contain "bath"\n - manning must contain "mann"\n - infiltration must contain "infil"\n - roof must contain "roof"\n - deck must contain "deck"'))

        self._check_prefix = wx.Button(self._frame,label = _('Check prefix (tif files)'))
        self._check_prefix.Bind(wx.EVT_BUTTON,self.oncheck_prefix)
        self._check_prefix.SetToolTip(_('Check prefix of .tif files\n\n - bath_*.tif\n - mann_*.tif\n - infil_*.tif\n - roof_*.tif\n - deck_*.tif\n\nThe prefix must be "bath_", "mann_", "infil_", "roof_" and "deck__"'))

        self._checkconsistency = wx.Button(self._frame,label = _('Check consistency'))
        self._checkconsistency.Bind(wx.EVT_BUTTON,self.oncheck_consistency)
        self._checkconsistency.SetToolTip(_('Check consistency of the scenario\n\n - bathymetry.tif\n - manning.tif\n - infiltration.tif\n - hydrographs\n - initial conditions\n - boundary conditions\n - scripts'))

        self._checkonesimulation = wx.Button(self._frame,label = _('Check one simulation'))
        self._checkonesimulation.Bind(wx.EVT_BUTTON,self.oncheck_one_simulation)
        self._checkonesimulation.SetToolTip(_('Check consistency of one simulation'))

        self._createsim = wx.Button(self._frame,label = _('Create simulation(s)'))
        self._createsim.Bind(wx.EVT_BUTTON,self.oncreate_simulation)
        self._createsim.SetToolTip(_('Create simulation(s) from selected hydrographs'))

        self._transfer_ic = wx.Button(self._frame,label = _('Transfer global initial conditions'))
        self._transfer_ic.Bind(wx.EVT_BUTTON,self.ontransfer_ic)
        self._transfer_ic.SetToolTip(_('Transfer global initial conditions from a simulation to another\n\nThe directory {} must exist !\n\nAnd subdirectories related to the discharges must also be present.\n\nIf not, firstly, extract global IC with ALT+DCLICK on simulations.'.format(INITIAL_CONDITIONS)))

        self._extract_tif = wx.Button(self._frame,label = _('Extract .tif files for all selected scenarios'))
        self._extract_tif.Bind(wx.EVT_BUTTON,self.onextract_tif)
        self._extract_tif.SetToolTip(_('Extract .tif files for all selected scenarios'))

        self._runbatch = wx.Button(self._frame,label = _('Run batch file !'))
        self._runbatch.Bind(wx.EVT_BUTTON,self.onrun_batch)
        self._runbatch.SetToolTip(_('Run the batch file on local machine\n\n - The batch file must be created before\n - The batch file must be a .bat file'))

        self.listsims = wx.Button(self._frame,label = _('List simulation(s)'))
        self.listsims.Bind(wx.EVT_BUTTON,self.onlist_simulation)
        self.listsims.SetToolTip(_('List all simulations and print them in the text control'))

        # Text control
        # ------------

        self.epsilon = wx.TextCtrl(self._frame, value='0.01', style=wx.TE_PROCESS_ENTER | wx.TE_CENTER)
        self.epsilon.Bind(wx.EVT_TEXT_ENTER, self.onchange_epsilon)
        self.epsilon.SetToolTip(_('Epsilon value\nValues below this threshold will be considered as 0.0\n\nPress Enter to validate'))

        # checkbox control
        # ----------------

        self.filter = wx.CheckBox(self._frame, label=_('Filter independent zones'), style=wx.CHK_2STATE)
        self.filter.SetValue(True)
        self.filter.Bind(wx.EVT_CHECKBOX, self.onchange_filter)
        self.filter.SetToolTip(_('Filter independent zones\nFirst a labelling will be applied\nThen only the most important zone is kept\nThe others are set to 0.0'))

        sizer_txt_ckd.Add(self.filter, 1, wx.EXPAND)
        sizer_txt_ckd.Add(self.epsilon, 1, wx.EXPAND)

        # Positions
        # ---------

        # buttons -> sizer
        sizer_buttons.Add(self._reload,1,wx.EXPAND)
        sizer_buttons.Add(tif_sizer,1,wx.EXPAND)
        sizer_buttons.Add(bridge_sizer,1,wx.EXPAND)
        sizer_buttons.Add(self._create_void_scripts,1,wx.EXPAND)
        sizer_buttons.Add(self._check_prefix,1,wx.EXPAND)
        sizer_buttons.Add(self._create_vrt,1,wx.EXPAND)
        sizer_buttons.Add(self._translate_vrt,1,wx.EXPAND)
        sizer_buttons.Add(self._apply_scripts,1,wx.EXPAND)

        _sizer_check = wx.BoxSizer(wx.HORIZONTAL)
        _sizer_check.Add(self._checkconsistency, 1, wx.EXPAND)
        _sizer_check.Add(self._checkonesimulation, 1, wx.EXPAND)

        sizer_buttons.Add(_sizer_check,1,wx.EXPAND)
        sizer_buttons.Add(self._create_vec,1,wx.EXPAND)
        sizer_buttons.Add(self.listsims,1,wx.EXPAND)
        sizer_buttons.Add(self._createsim,1,wx.EXPAND)
        sizer_buttons.Add(self._runbatch,1,wx.EXPAND)
        sizer_buttons.Add(self._transfer_ic,1,wx.EXPAND)
        sizer_buttons.Add(self._extract_tif,1,wx.EXPAND)
        sizer_buttons.Add(sizer_txt_ckd,1,wx.EXPAND)

        # tree, buttons -> horizontal sizer
        sizer_horizontal.Add(self._treelist,1,wx.EXPAND)
        sizer_horizontal.Add(sizer_buttons,1,wx.EXPAND)

        # txt_ctrl, (tree, buttons) -> updown sizer
        sizer_updown.Add(sizer_horizontal,1,wx.EXPAND)
        sizer_updown.Add(self._txtctrl,1,wx.EXPAND)

        # link sizer to frame
        self._frame.SetSizer(sizer_updown)

        if self._parent.get_mapviewer() is not None:
            self._frame.SetIcon(self._parent.get_mapviewer().GetIcon())

        # Layout
        self._frame.Layout()

        # Set the position to the center of the screen
        self._frame.Centre(wx.BOTH)

        # Show
        self._frame.Show()

    def onchange_epsilon(self, e:wx.KeyEvent):
        """ Change epsilon value """

        try:
            epsilon = float(self.epsilon.GetValue())
            self._parent.epsilon = epsilon
        except:
            logging.error(_('Epsilon value must be a float -- set 0.0 by default !'))
            self._parent.epsilon = 0.

    def onchange_filter(self, e:wx.MouseEvent):
        """ Change filter independent zones value """

        self._parent.filter_independent = self.filter.GetValue()

    def reload(self):
        """ Reload the structure """

        self._parent.load_data()

    def onupdate_structure(self,e:wx.MouseEvent):
        """ Mise à jour de la structure """

        self.reload()

    def oncreate_void_infil(self, e:wx.MouseEvent):
        """ Création d'un fichier d'infiltration vide """

        self._parent.create_void_infil()
        self.reload()

    def oncreate_dtm(self, e:wx.MouseEvent):
        """ Création d'un fichier DTM vide """

        self._parent.create_void_dtm()
        self.reload()

    def oncreate_void_roof(self, e:wx.MouseEvent):
        """ Création d'un fichier de toit de pont vide """

        self._parent.create_void_roof()
        self.reload()

    def oncreate_void_deck(self, e:wx.MouseEvent):
        """ Création d'un fichier de tablier de pont vide """

        self._parent.create_void_deck()
        self.reload()

    def oncreate_void_scripts(self,e:wx.MouseEvent):
        """ Création d'un script vide """

        def_dir = str(self._parent.workingdir)
        if isinstance(self._selected_item, Path):
            def_dir = str(self._selected_item.parent)

        dlg = wx.DirDialog(None, _('Choose a scenario directory'), style = wx.DD_DIR_MUST_EXIST, defaultPath=def_dir) #, wildcard = 'Python script (*.py)|*.py')
        ret = dlg.ShowModal()
        if ret != wx.ID_OK:
            dlg.Destroy()
            return

        wdir = dlg.GetPath()
        dlg.Destroy()

        file_update = Path(wdir) / 'update_top_mann_scen.py'

        if file_update.exists():
            dlg = wx.MessageDialog(None, _('File {} already exists ! \n Overwrite ?'.format(file_update)), _('Warning'), wx.YES_NO)
            ret = dlg.ShowModal()

            if ret != wx.ID_YES:
                dlg.Destroy()
                dlg = wx.FileDialog(None, _('Choose a new file name'), style = wx.FD_SAVE, defaultDir=wdir, defaultFile='_'+str(file_update.name), wildcard = 'Python script (*.py)|*.py')
                ret = dlg.ShowModal()
                if ret != wx.ID_OK:
                    dlg.Destroy()
                    return
                file_update = Path(dlg.GetPath())
                dlg.Destroy()

        update_void(file_update)

        file_bc = Path(wdir) / 'impose_bc_scen.py'
        if file_bc.exists():
            dlg = wx.MessageDialog(None, _('File {} already exists ! \n Overwrite ?'.format(file_bc)), _('Warning'), wx.YES_NO)
            ret = dlg.ShowModal()

            if ret != wx.ID_YES:
                dlg.Destroy()
                dlg = wx.FileDialog(None, _('Choose a new file name'), style = wx.FD_SAVE, defaultDir=wdir, defaultFile='_'+str(file_bc.name), wildcard = 'Python script (*.py)|*.py')
                ret = dlg.ShowModal()
                if ret != wx.ID_OK:
                    dlg.Destroy()
                    return
                file_update = Path(dlg.GetPath())
                dlg.Destroy()

        bc_void(file_bc)

        self.reload()

    def oncreatevrt(self,e:wx.MouseEvent):
        """ Création d'un fichier vrt """

        if self._selected_item is None:
            logging.error(_('Please select a scenario to analyze by activating an elemnt in the tree list !'))
            return

        logging.info(_('Creating vrt ...'))
        mydata = self._treelist.GetItemData(self._selected_item)

        if not isinstance(mydata, dict):
            logging.error(_('Please select a scenario to analyze ! - The selected item is not a scenario'))
            return

        if not mydata.get('path', None):
            logging.error(_('Please select a scenario to analyze !'))
            return

        # création du fichier vrt
        self._parent.create_vrt(mydata['path'])
        logging.info(_('... done !'))

        self.reload()

    def oncreatevec(self,e:wx.MouseEvent):
        """ Création d'un fichier vec """

        if self._selected_item is None:
            logging.error(_('Please select a scenario to analyze by activating an elemnt in the tree list !'))
            return

        logging.info(_('Creating vecz ...'))
        mydata = self._treelist.GetItemData(self._selected_item)

        if not isinstance(mydata, dict):
            logging.error(_('Please select a scenario to analyze ! - The selected item is not a scenario'))
            return

        if not mydata.get('path', None):
            logging.error(_('Please select a scenario to analyze !'))
            return

        # création du fichier vrt
        new_zones = self._parent.create_vec(mydata['path'])
        logging.info(_('... done !'))

        dlg = wx.MessageDialog(None, _('Do you want to add the new zones to the map ?'), _('Warning'), wx.YES_NO)
        ret = dlg.ShowModal()

        if ret == wx.ID_YES:

            new_zones.set_mapviewer()

            cur_ids = self._parent.mapviewer.get_list_keys(drawing_type=draw_type.VECTORS)
            newid = mydata['path'].name
            while newid in cur_ids:
                newid = newid + '_'
            self._parent.mapviewer.add_object('vector', newobj = new_zones, id=newid)
            self._parent.mapviewer.Refresh()

        dlg.Destroy()

        self.reload()

    def ontranslatevrt2tif(self,e:wx.MouseEvent):
        """ Traduction d'un fichier vrt en tif """

        logging.info(_('Translating vrt to tif ...'))
        if self._selected_item is None or self._selected_item == self._treelist.GetRootItem():
            logging.info(_('No item selected ! -- using root item'))
            with wx.MessageDialog(None, _('No item selected ! -- using root item'), _('Warning'), wx.OK | wx.CANCEL | wx.ICON_WARNING) as dlg:
                dlg:wx.MessageDialog
                ret = dlg.ShowModal()
                if ret != wx.ID_OK:
                    return
            mydata = self._parent.configs
        else:
            mydata = self._treelist.GetItemData(self._selected_item)

        if not isinstance(mydata, dict):
            logging.error(_('Please select a scenario to analyze ! - The selected item is not a scenario'))
            return

        if not mydata.get('path', None):
            logging.error(_('Please select a scenario to analyze !'))
            return

        # création du fichier vrt
        self._parent.translate_vrt2tif(mydata['path'])
        logging.info(_('... done !'))

    def onapply_scripts(self,e:wx.MouseEvent):
        """ Application des scripts sur les fichiers tif """

        logging.info(_('Applying scripts ...'))
        if self._selected_item is None or self._selected_item == self._treelist.GetRootItem():
            logging.info(_('No item selected ! -- using root item'))
            with wx.MessageDialog(None, _('No item selected ! -- using root item'), _('Warning'), wx.OK | wx.CANCEL | wx.ICON_WARNING) as dlg:
                dlg:wx.MessageDialog
                ret = dlg.ShowModal()
                if ret != wx.ID_OK:
                    return
            mydata = self._parent.configs
        else:
            mydata = self._treelist.GetItemData(self._selected_item)

        if not isinstance(mydata, dict):
            logging.error(_('Please select a scenario to analyze ! - The selected item is not a scenario'))
            return

        if not mydata.get('path', None):
            logging.error(_('Please select a scenario to analyze !'))
            return

        # application des scripts
        self._parent.apply_scripts_bath_mann_inf_roof_deck(mydata['path'])

        self.reload()
        logging.info(_('... done !'))

    def oncheck_prefix(self,e:wx.MouseEvent):
        """ Vérification des préfixes des fichiers tif """

        logging.info(_('Checking prefix ...'))
        if self._selected_item is None or self._selected_item == self._treelist.GetRootItem():
            logging.info(_('No item selected ! -- using root item'))
            with wx.MessageDialog(None, _('No item selected ! -- using root item ?'), _('Warning'), wx.OK | wx.CANCEL | wx.ICON_WARNING) as dlg:
                dlg:wx.MessageDialog
                ret = dlg.ShowModal()
                if ret != wx.ID_OK:
                    return
            mydata = self._parent.configs
        else:
            mydata = self._treelist.GetItemData(self._selected_item)

        # création du fichier vrt
        log = self._parent.check_prefix(mydata['.tif']+mydata['.tiff'])
        if log =='':
            self._txtctrl.WriteText("\n".join([_("All is fine !")]))
        else:
            self._txtctrl.WriteText(log)

    def oncheck_one_simulation(self, e:wx.MouseEvent):
        """ Vérification de la cohérence d'une simulation
        """
        self._txtctrl.Clear()
        log = self._parent.check_one_simulation()
        if log == '':
            self._txtctrl.WriteText("\n\n".join([_("All seems fine !")]))
        else:
            self._txtctrl.WriteText("\n\n".join([log]))

        # Info on Python Environment and wolfgpu Path and version
        # -------------------------------------------------------

        import sys
        # Python Environment
        self._txtctrl.write(_('\nPython Environment\n'))
        self._txtctrl.write('-------------------\n')
        self._txtctrl.write('Python version : {}\n'.format(sys.version))
        self._txtctrl.write('Python path : {}\n'.format(sys.executable))
        self._txtctrl.write('Python version info : {}\n'.format(sys.version_info))

        # Test if wolfgpu.exe exists in script directory
        # wolfgpu Path and version
        self._txtctrl.write('\nWolfgpu Path and version\n')
        self._txtctrl.write('------------------------\n')

        wolfgpu = self._parent.wolfgpu
        if wolfgpu.exists():
            self._txtctrl.write('Wolfgpu.exe found in : {}\n'.format(self._parent.wolfgpu.parent))
        else:
            self._txtctrl.write('Wolfgpu.exe not found !\n')
            self._parent.wolfgpu = None


    def oncheck_consistency(self,e:wx.MouseEvent):
        """ Vérification de la cohérence des fichiers """

        self._txtctrl.Clear()

        log = self._parent.check_consistency()
        if log =='':
            self._txtctrl.WriteText("\n\n".join([_("All is fine !")]))
        else:
            self._txtctrl.WriteText("\n\n".join([log]))

        # Info on Python Environment and wolfgpu Path and version
        # -------------------------------------------------------

        import sys
        # Python Environment
        self._txtctrl.write(_('\nPython Environment\n'))
        self._txtctrl.write('-------------------\n')
        self._txtctrl.write('Python version : {}\n'.format(sys.version))
        self._txtctrl.write('Python path : {}\n'.format(sys.executable))
        self._txtctrl.write('Python version info : {}\n'.format(sys.version_info))

        # Test if wolfgpu.exe exists in script directory
        # wolfgpu Path and version
        self._txtctrl.write('\nWolfgpu Path and version\n')
        self._txtctrl.write('------------------------\n')

        wolfgpu = self._parent.wolfgpu
        if wolfgpu.exists():
            self._txtctrl.write('Wolfgpu.exe found in : {}\n'.format(self._parent.wolfgpu.parent))
        else:
            self._txtctrl.write('Wolfgpu.exe not found !\n')
            self._parent.wolfgpu = None


    def choice_hydrograph(self) -> list[int]:

        names = self._parent.get_names_hydrographs()
        dlg = wx.MultiChoiceDialog(None, _('Choose hydrograph'), _('Hydrographs'), names)
        ret = dlg.ShowModal()
        if ret != wx.ID_OK:
            dlg.Destroy()
            return None

        idx = dlg.GetSelections()
        dlg.Destroy()

        return idx

    def onextract_tif(self, e:wx.MouseEvent):
        """ Extraction des fichiers tif """

        logging.info(_('Extracting tif files ...'))

        sims = self.get_sims_only()

        with wx.DirDialog(None, _('Choose a directory to store tif files'), style = wx.DD_DIR_MUST_EXIST) as dlg:
            dlg:wx.DirDialog
            ret = dlg.ShowModal()
            if ret != wx.ID_OK:
                return

            wdir = dlg.GetPath()

        for cursim in sims:
            self._parent.extract_tif(cursim['path'], wdir)

        self.reload()

        logging.info(_('... done !'))

    def ontransfer_ic(self, e:wx.MouseEvent):
        """ Transfert des conditions initiales """

        logging.info(_('Transferring initial conditions ...'))

        with wx.DirDialog(None, _('Choose the source scenario directory'), style = wx.DD_DIR_MUST_EXIST) as dlg:
            dlg:wx.DirDialog
            ret = dlg.ShowModal()
            if ret != wx.ID_OK:
                return

            wdir = dlg.GetPath()

        with wx.DirDialog(None, _('Choose the destination scenario directory'), style = wx.DD_DIR_MUST_EXIST) as dlg:
            dlg:wx.DirDialog
            ret = dlg.ShowModal()
            if ret != wx.ID_OK:
                return

            wdir2 = dlg.GetPath()

        self._parent.transfer_ic(Path(wdir), Path(wdir2))

        self.reload()

    def oncreate_simulation(self, e:wx.MouseEvent):
        """ Creation d'une simulation """

        logging.info(_('Creating simulation ...'))
        hydro = self.choice_hydrograph()
        if hydro is None:
            return

        if len(hydro)==0:
            return

        # Recherche du répertoire de base à ouvrir
        #  utilisatation du répertoire sélectionné ou du répertoire parent/source
        #  si aucun élément sélectionné ou si l'élément sélectionné n'est pas un dictionnaire
        if self._selected_item is None or self._selected_item == self._treelist.GetRootItem():
            logging.info(_('No item selected ! -- using root item'))
            mydata = self._parent.configs
        else:
            mydata = self._treelist.GetItemData(self._selected_item)

            if isinstance(mydata, dict):
                pass
            else:
                logging.info(_('The current activated item is not a dictionnary ! -- using root item'))
                mydata = self._parent.configs

        dlg = wx.DirDialog(None, _('Choose a scenario directory'), style = wx.DD_DIR_MUST_EXIST, defaultPath=str(mydata['path']))
        ret = dlg.ShowModal()
        if ret != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        dlg.Destroy()

        dlg = wx.MessageDialog(None, _('Do you want to delete existing simulations ?'), _('Warning'), wx.YES_NO)
        ret = dlg.ShowModal()
        destroy_if_exists = ret == wx.ID_YES
        dlg.Destroy()

        preserve_ic = False
        if not destroy_if_exists:
            dlg = wx.MessageDialog(None, _('Do you want to preserve initial conditions ?'), _('Warning'), wx.YES_NO)
            ret = dlg.ShowModal()
            preserve_ic = ret == wx.ID_YES
            dlg.Destroy()

        pgbar = wx.ProgressDialog(_('Creating simulations ...'), _('Please wait ...'), maximum=len(hydro), parent=self._frame, style = wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)

        try:
            allsims = self._parent.create_simulation(Path(path), hydro, destroy_if_exists, preserve_ic, callback=pgbar.Update)
        except Exception as e:
            logging.error(_('Error while creating simulations !'))
            logging.error(str(e))
            dlg = wx.MessageDialog(None, _('Error while creating simulations !\n\n{}'.format(str(e))), _('Error'), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            allsims = None

        pgbar.Destroy()

        self.reload()

        if allsims is None:
            logging.error(_('No simulation created !'))
            return

        if len(allsims)>0:

            self._txtctrl.write(_('You have created {} simulations\n\n'.format(len(allsims))))
            for cursim in allsims:
                self._txtctrl.write(str(cursim) + '\n')

            dlg = wx.MessageDialog(None, _('Do you want to create a batch file ?'), _('Warning'), wx.YES_NO)
            ret = dlg.ShowModal()
            create_batch = ret == wx.ID_YES
            dlg.Destroy()

            if create_batch:
                dlg = wx.FileDialog(None, _('Choose a batch file name'), style = wx.FD_SAVE, defaultDir=str(path), defaultFile='quickruns.bat', wildcard = 'Batch file (*.bat)|*.bat')
                ret = dlg.ShowModal()
                if ret != wx.ID_OK:
                    dlg.Destroy()
                    return
                batch = Path(dlg.GetPath())
                dlg.Destroy()

                self._batch = batch
                batch = self._parent.create_batch(Path(batch), allsims)

                self._txtctrl.write('\n\n')
                self._txtctrl.write(_('You can run the simulations with the following commands / batch file :\n\n'))

                self._txtctrl.write(batch)

        logging.info(_('... done !'))

    def onrun_batch(self,e:wx.MouseEvent):
        """ run batch file """

        if self._batch is None:
            return

        self._parent.run_batch(self._batch)

    def onlist_simulation(self,e:wx.MouseEvent):
        """ List all simulations and print infos in text control """

        all_sims = self._parent.get_all_sims()

        self._txtctrl.Clear()
        self._txtctrl.write(_('You have {} simulations\n\n'.format(len(all_sims))))
        self._txtctrl.write(_('List of simulations\n\n'))
        for cursim in all_sims:
            self._txtctrl.write(str(cursim) + '\n')


    def get_sims_only(self, force=False):
        """ Get paths to all or selected simulations """

        sims=[]

        curitem:TreeListItem
        curitem = self._treelist.GetFirstItem()

        while curitem.IsOk():

            mydata  = self._treelist.GetItemData(curitem)
            checked = self._treelist.GetCheckedState(curitem) == wx.CHK_CHECKED

            if isinstance(mydata, dict):
                if IS_SIMUL in mydata:
                    if mydata[IS_SIMUL]:
                        if checked or force:
                            sims += [mydata]

            curitem = self._treelist.GetNextItem(curitem)
            # curitem = self._treelist.GetItemParent(curitem)

        return sims

    def OnCheckItem(self,e):
        """ All levels under the item are checked/unchecked"""

        myitem = e.GetItem()

        ctrl = wx.GetKeyState(wx.WXK_CONTROL)

        myparent:TreeListItem
        myparent = self._treelist.GetItemParent(myitem)
        mydata = self._treelist.GetItemData(myitem)
        check = self._treelist.GetCheckedState(myitem)

        self._treelist.CheckItemRecursively(myitem, check)

    def _callbackwp(self):
        """ Callback for wolfparam """
        for cursim in self._wp:
            curwp = self._wp[cursim]
            if curwp is not None:
                try:
                    if curwp.Shown:
                        cursim.from_wolfparam(curwp)
                        cursim._save_json()
                except Exception as e:
                    self._wp[cursim] = None
                    logging.error(_('Error while saving parameters for simulation {}'.format(cursim.path.name)))
                    logging.error(str(e))

    def _callbackwp_destroy(self):
        """ Callback for wolfparam """
        for cursim in self._wp:
            curwp = self._wp[cursim]
            if curwp is not None:
                try:
                    if curwp.Shown:
                        cursim.from_wolfparam(curwp)
                        cursim._save_json()
                except Exception as e:
                    self._wp[cursim] = None
                    logging.error(_('Error while saving parameters for simulation {}'.format(cursim.path.name)))
                    logging.error(str(e))

    def OnActivateTreeElem(self, e):
        """
        If you double click on a tree element
        """

        myitem:TreeListItem
        myitem = e.GetItem()

        self._selected_item = myitem

        # State of the CTRL key
        # - True if pressed
        #  - False if not pressed
        ctrl = wx.GetKeyState(wx.WXK_CONTROL)
        shift = wx.GetKeyState(wx.WXK_SHIFT)
        alt = wx.GetKeyState(wx.WXK_ALT)

        # Upstream tree element
        myparent = self._treelist.GetItemParent(myitem)

        # State of the item - Checked or not
        check = self._treelist.GetCheckedState(myitem)

        # Data associated with the item
        mydata = self._treelist.GetItemData(myitem)

        self._txtctrl.Clear()
        self._txtctrl.SetBackgroundColour(wx.WHITE)
        self._txtctrl.SetForegroundColour(wx.BLACK)

        self._parent._active_simulation = None
        if isinstance(mydata, dict):
            self._txtctrl.write(_('Yous have selected : {}\n\n'.format(str(mydata['path']))))

            if mydata[IS_SIMUL]:
                self._parent._active_simulation = mydata
                self._txtctrl.write(_('GPU SIMULATION\n\n'))

                if ctrl and not shift and not alt:
                    # CTRL pressed
                    # - Open the simulation in the viewer

                    logging.info(_('Opening simulation {}'.format(mydata['path'].name)))

                    ids = self._parent.mapviewer.get_list_keys(draw_type.RES2D)

                    newid = str(mydata['path'].name)
                    while newid.lower() in ids:

                        dlg = wx.TextEntryDialog(None, _('Choose a name for the new object'), _('Name'), str(mydata['path'].name) + '_new')
                        ret = dlg.ShowModal()
                        if ret != wx.ID_OK:
                            dlg.Destroy()
                            return

                        newid = dlg.GetValue()
                        dlg.Destroy()

                    logging.info(_('  Reading simulation data'))
                    addedsim = wolfres2DGPU(str(mydata['path'] / 'simul_gpu_results'), eps=1e-5, idx=newid, mapviewer=self._parent.mapviewer)

                    addedsim.epsilon = self._parent.epsilon
                    addedsim._epsilon_default = self._parent.epsilon
                    addedsim.to_filter_independent = self._parent.filter_independent

                    logging.info(_('  Adding simulation to the mapviewer'))
                    self._parent.mapviewer.add_object('res2d_gpu', newobj=addedsim, id=newid)

                    # add the related menus to the mapviewer
                    self._parent.mapviewer.menu_wolf2d()
                    self._parent.mapviewer.menu_2dgpu()

                    logging.info(_('  Reading last step'))
                    addedsim.read_oneresult()
                    logging.info(_('  Coloring the map'))
                    addedsim.set_currentview()

                    logging.info(_('Simulation {} opened and added !'.format(mydata['path'].name)))

                elif shift and ctrl:
                    # Ctrl + Shift pressed
                    # Extract IC from a specific result and save it the current simulation

                    logging.info(_('Extracting IC from a specific result and save it the current simulation'))

                    res_path = mydata['path'] / 'simul_gpu_results'
                    if res_path.exists():
                        store = ResultsStore(res_path, mode='r')

                        dlg = wx.SingleChoiceDialog(None, _('Choose a result'), _('Results'), [str(cur) for cur in range(1, store.nb_results+1)])
                        ret = dlg.ShowModal()

                        if ret != wx.ID_OK:
                            dlg.Destroy()
                            return

                        idx = int(dlg.GetSelection())
                        dlg.Destroy()

                        sim = SimpleSimulation.load(mydata['path'])
                        sim.write_initial_condition_from_record(res_path, idx, mydata['path'])

                        if self._parent.filter_independent:
                            logging.info(_('Filtering independent zones'))
                            self.filter_independent_zones(1, mydata['path'])
                        else:
                            logging.info(_('No filtering applied'))

                    logging.info(_('IC extracted and saved !'))

                elif ctrl and alt:
                    # ctrl + alt
                    # Extract last result and save it as IC for the current simulation

                    logging.info(_('Extracting last result and save it as IC for the current simulation'))

                    res_path = mydata['path'] / 'simul_gpu_results'
                    if res_path.exists():
                        store = ResultsStore(res_path, mode='r')

                        idx = store.nb_results

                        sim = SimpleSimulation.load(mydata['path'])
                        sim.write_initial_condition_from_record(res_path, idx, mydata['path'])

                        if self._parent.filter_independent:
                            logging.info(_('Filtering independent zones'))
                            self.filter_independent_zones(1, mydata['path'])
                        else:
                            logging.info(_('No filtering applied'))

                    logging.info(_('IC extracted and saved !'))

                elif shift:
                    # shift pressed
                    # show the parameters of the simulation

                    logging.info(_('Opening parameters for simulation {}'.format(mydata['path'].name)))

                    sim = SimpleSimulation.load(mydata['path'])

                    wp = sim.to_wolfparam()
                    self._wp[sim] = wp
                    wp.set_callbacks(self._callbackwp, self._callbackwp_destroy)
                    wp._set_gui(title='Parameters for simulation {}'.format(mydata['path'].name), toShow=False)
                    wp.hide_selected_buttons()
                    wp.Show()

                elif alt:
                    # alt pressed
                    # Extract last result and save it as General Initial conditions

                    logging.info(_('Extracting last result and save it as General Initial conditions'))

                    res_path = mydata['path'] / 'simul_gpu_results'
                    if res_path.exists():
                        sim = SimpleSimulation.load(mydata['path'])
                        destpath = self._parent.workingdir / INITIAL_CONDITIONS / mydata['path'].name.replace('sim_', '')
                        sim.write_initial_condition_from_record(res_path, None, destpath)

                        if self._parent.filter_independent:
                            logging.info(_('Filtering independent zones'))
                            self.filter_independent_zones(1, destpath)
                        else:
                            logging.info(_('No filtering applied'))

                    logging.info(_('IC extracted and saved !'))

                else:
                    self._txtctrl.write(_('\n\n CTRL  + double click to open the simulation results in the UI'))
                    self._txtctrl.write(_('\n SHIFT + double click to edit simulation parameters in the UI'))
                    self._txtctrl.write(_('\n ALT   + double click to extract last result as general initial conditions'))
                    self._txtctrl.write(_('\n CTRL  + ALT   + double click to extract last result as initial conditions and update the simulation'))
                    self._txtctrl.write(_('\n CTRL  + SHIFT + double click to extract a specific result as initial conditions and update the simulation'))

        elif isinstance(mydata, list):

            def allfiles(curlist):
                """ Get all files from a list of files """
                allfiles = '\n'
                for curfile in curlist:
                    allfiles+= curfile.name +'\n'
                return allfiles

            self._txtctrl.write(_('Yous have selected a list : {}'.format(allfiles(mydata))))

        elif isinstance(mydata, Path):
            self._txtctrl.write(_('Yous have selected : {} \n\n'.format(str(mydata))))

            if mydata.name.endswith(GPU_2D_file_extensions.PY.value):
                # script Python
                self._txtctrl.write(_('\n\n CTRL+ double click to open the script in the viewer (not an editor !)'))

                # Name of the item and its parent
                nameparent = self._treelist.GetItemText(myparent).lower()
                nameitem   = self._treelist.GetItemText(myitem).lower()

                if nameparent ==  WOLF_UPDATE.lower() or nameparent == OTHER_SCRIPTS.lower() or nameparent == WOLF_BC.lower() :
                    # script

                    if ctrl :
                        # CTRL pressed
                        # - Open the script in the editor
                        self._open_script(mydata, nameparent in [WOLF_UPDATE.lower(), WOLF_BC.lower()])

            elif mydata.name.endswith(GPU_2D_file_extensions.JSON.value):
                # fichier de paramètres
                if ctrl :
                    # script
                    with open(mydata, 'r', encoding='utf-8') as file:
                        txt = json.load(file)
                        self._txtctrl.write(str(txt))
                else:
                    self._txtctrl.write(_('\n\n CTRL+ double click to open the json file in the viewer (not an editor !)'))

            elif mydata.name.endswith(GPU_2D_file_extensions.TIF.value) or mydata.name.endswith(GPU_2D_file_extensions.NPY.value) or mydata.name.endswith(GPU_2D_file_extensions.BIN.value):
                # proposition de chargement dans l'UI  (pas de message si CTRL+double click)

                self._txtctrl.write(str(self._parent._get_header(mydata)))

                if self._parent.mapviewer is not None:
                    if not ctrl:
                        dlg = wx.MessageDialog(None, _('Do you want to load the file in the mapviewer ?'), _('Load file'), wx.YES_NO)
                        ret = dlg.ShowModal()
                        dlg.Destroy()
                        if ret != wx.ID_YES:
                            return

                    myarray = WolfArray(str(mydata), srcheader=self._parent._header, nullvalue=99999., idx=str(mydata.name))

                    ids = self._parent.mapviewer.get_list_keys(draw_type.ARRAYS)
                    newid = str(mydata.name)
                    while newid in ids:
                        newid = newid + '_'

                    self._parent.mapviewer.add_object('array', newobj=myarray, id=newid)

            elif mydata.name.endswith(GPU_2D_file_extensions.TXT.value):
                # Chragement d'un hydrogramme
                try:
                    hydro, fig, ax = self._parent.load_hydrograph(mydata, ctrl)
                    if hydro._data.empty:
                        with open(mydata, 'r', encoding='utf-8') as file:
                            txt = file.read()
                            self._txtctrl.write(txt)
                    else:
                        self._txtctrl.write(_('There are {} columns\n\n'.format(len(hydro._data.columns))))
                        for idx, curcol in enumerate(hydro._data.columns):
                            self._txtctrl.write('    - {} has index \t{} \tin the infiltration array'.format(curcol, idx+1) + '\n')
                        self._txtctrl.write('\n\n')

                        self._txtctrl.write(_('Time'))
                        for curcol in hydro._data.columns:
                            self._txtctrl.write('\t'+curcol)
                        self._txtctrl.write('\n')

                        if hydro._data.shape[0]>50:
                            logging.warning(_('Too many lines in the hydrograph -- only the first 50 will be displayed !'))

                            for idx, curline in hydro._data.iloc[:50].iterrows():
                                self._txtctrl.write(str(idx))
                                for curval in curline.values:
                                    self._txtctrl.write('\t' + str(curval))
                                self._txtctrl.write('\n')

                        else:
                            for idx, curline in hydro._data.iterrows():
                                self._txtctrl.write(str(idx))
                                for curval in curline.values:
                                    self._txtctrl.write('\t' + str(curval))
                                self._txtctrl.write('\n')

                except:
                    with open(mydata, 'r', encoding='utf-8') as file:
                        txt = file.read()
                        self._txtctrl.write(txt)


    def filter_independent_zones(self, n_largest:int = 1, icpath:Path=None):
        """
        Filtre des zones indépendantes et conservation des n plus grandes

        """

        from scipy.ndimage import label, sum_labels

        waterdepth = icpath / 'h.npy'
        waterdepth = np.load(waterdepth)
        np.save(icpath / '_h_before_filtering.npy', waterdepth)

        # labellisation
        labeled_array = waterdepth.copy()
        labeled_array[np.where(waterdepth<self._parent.epsilon)] = 0

        labeled_array, num_features = label(labeled_array)

        longueur = []

        longueur = list(sum_labels(np.ones(labeled_array.shape, dtype=np.int32), labeled_array, range(1, num_features+1)))
        longueur = [[longueur[j], j+1] for j in range(0, num_features)]
        longueur.sort(key=lambda x: x[0], reverse=True)

        newh = np.zeros_like(waterdepth)
        for j in range(0,n_largest):
            newh[labeled_array == longueur[j][1]] = waterdepth[labeled_array == longueur[j][1]]


        np.save(icpath / 'h.npy', newh)

        qx = icpath / 'qx.npy'
        if qx.exists():
            qx = np.load(qx)
            np.save(icpath / '_qx_before_filtering.npy', qx)
            qx[newh==0.]=0.
            np.save(icpath / 'qx.npy', qx)

        qy = icpath / 'qy.npy'
        if qy.exists():
            qy = np.load(qy)
            np.save(icpath / '_qy_before_filtering.npy', qy)
            qy[newh==0.]=0.
            np.save(icpath / 'qy.npy', qy)

    def clear_text(self):
        """ Reset txt control"""

        self._txtctrl.Clear()
        self._txtctrl.SetBackgroundColour(wx.WHITE)
        self._txtctrl.SetForegroundColour(wx.BLACK)

    def _open_script(self, mydata:Path, wolf:bool=False):
        """ Open the script in the editor """

        if mydata.exists():
            with open(mydata, 'r', encoding='utf-8') as file:
                txt = file.read()
                self.clear_text()

                if wolf:
                    self._txtctrl.SetBackgroundColour(wx.Colour(28,142,62))
                    self._txtctrl.SetForegroundColour(wx.WHITE)

                    self._txtctrl.WriteText('WOLF update or BC file\n------------------\n\n')
                    # self._txtctrl.SetForegroundColour(wx.BLACK)
                else:
                    self._txtctrl.SetBackgroundColour(wx.RED)
                    self._txtctrl.SetForegroundColour(wx.WHITE)
                    self._txtctrl.WriteText(' **NOT** WOLF update or BC file\n-----------------------------\n\n')
                    # self._txtctrl.SetForegroundColour(wx.BLACK)

                self._txtctrl.WriteText(txt)

                self._frame.Layout()

    def _append_configs2tree(self, curdict:dict, root:TreeListItem):
        """ Ajout des éléments du dictionnaire dans l'arbre sur base de la racine fournie """

        for idx, (k,v) in enumerate(curdict.items()):

            if isinstance(v, dict):

                if isinstance(k,Path):
                    # on ne garde que le nom du chemin complet
                    kstr = k.name
                else:
                    kstr = str(k)

                if kstr != SUBDIRS and '__' not in kstr:

                    create = True
                    if kstr == GPU_2D_file_extensions.PY.value:
                        # Pas d'ajout de noeud à l'arbre si pas de fichiers .py
                        create = len(v[WOLF_UPDATE])>0 or len(v[OTHER_SCRIPTS])>0 or len(v[WOLF_BC])>0

                    if create:
                        newroot = self._treelist.AppendItem(root, kstr, data = v)
                        self._append_configs2tree(v, newroot)

            elif isinstance(v, list):

                if isinstance(k,Path):
                    # on ne garde que le nom du chemin complet
                    k=k.name
                else:
                    kstr = str(k)

                if len(v)>0:
                    if (kstr in ALL_EXTENSIONS or kstr == WOLF_UPDATE or kstr == OTHER_SCRIPTS or kstr == WOLF_BC) and (kstr != SUBDIRS):
                        newroot = self._treelist.AppendItem(root, k, data = v)

                        for curfile in v:
                            self._treelist.AppendItem(newroot, curfile.name, data = curfile)