"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import sys
import numpy as np
import csv
import os
import logging

from numpy.ma.core import append, shape
from numpy.testing._private.utils import suppress_warnings
# import constant as cst
import math
import time as time_mod
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange, MicrosecondLocator
import scipy.stats as stats             #pip install Scipy
import datetime                         # module which contains objects treating dates
from matplotlib.font_manager import FontProperties
from dbfread import DBF
import ctypes as ct
import pandas as pd
from pathlib import Path
import ctypes as ct

from ..PyTranslate import _
from . import plot_hydrology as ph
from . import data_treatment as datt
from . import read as rd
from . import constant as cst
from . import Models_characteristics as mc
from . import Internal_variables as iv

from ..wolf_array import *
from ..PyParams import*

## TO DO:
# - add the arguments _dateBegin, _dateEnd and _deltaT as optional
#       -> In this way, the init of these variable can be done by reading the rain, evap or outflow file if not already init

class SubBasin:

    name:str
    iD:int
    iDSorted:int
    x:float
    y:float
    haveInlets:bool
    alreadyUsed:bool
    isLeveled:bool
    isActivated:bool

    ## Time array containing all the timestamps
    # @var time timestamps array of dimension equal to rain and evap (or 1 element more than myHydro so far (VHM but not UH)).
    time:np.ndarray

    dateBegin:datetime.datetime     # Must be in GMT+0 !!!
    dateEnd:datetime.datetime       # Must be in GMT+0 !!!
    deltaT:datetime.timedelta
    # @var timezone in GMT saved to converted all computed or read data so that all data are expressed in GMT+0
    tz:float
    model:int

    treated:bool
    myLevel:bool
    fileNameRead:str
    fileNameWrite:str               # FIXME TO DO !!!!!!!!

    ## Dictionary containing all the objects Catchment:
    ## @var myHydro an array whose dimensions depends on the model chosen:
    #  - Unit hydrographs and Linear reservoir models : $1\times n$ elements
    #  - VHM model : $3\times n$ elements:
    #                myHydro[i][0] : overland flow
    #                myHydro[i][1] : interflow
    #                myHydro[i][2] : baseflow
    #  @unit $[\si{m}^3/\si{s}}]$
    myHydro:np.ndarray              # [mm/h] Fortran-like array that is pointed to by ptr_q_all with Fortran DLL (old version in [m^3/s])
    iv_saved:np.ndarray             # [mm/h] or [mm] or [-] depending on the variable

    intletsObj:dict
    inlets:np.ndarray
    inletsRaw:np.ndarray
    downstreamObj:dict

    ## @var outFlow
    # Hydro of the hydrological subbasin. Combined with the potentiel upstream hydros.
    # Version :
    #  - < 2023.0  : "outFlow" is a dictionnary and public variable.
    #                Consider timeDelay so that time is at 0 at the global outlet. Therefore the transfer to the general outlet is applied.
    #  - >= 2023.1 : "_outflow" is now a private dictionnary linked to a property called "outFlow".
    #                It considers the hydro at the local time. To apply the transfer call the property "glob_hydro"
    # @unit $[\si{m}^3/\si{s}}]$
    _outFlow:dict                    # [m^3/s] Hydro of the hydrological subbasin. Combined with the potentiel upstream hydros. Consider timeDelay so that time is at 0

    # self.outFlowRaw = []          # [m^3/s]
    # Hyeto
    myHyetoDict:dict
    myRain:np.ndarray               # [mm/h]   Caution in the difference of units in rain !!!!!!
    rain:np.ndarray                 # [m^3/h]  Caution in the difference of units in rain !!!!!!
    # Evapotranspiration
    myEvap:np.ndarray               # [mm/h]
    evap:np.ndarray                 # [mm/h]
    # Temperature
    myTemp:np.ndarray

    # Main subbasin characteristics
    mainCharactDict:dict            # Dictionnary with the main characteristics of the subbasin
    mainCharactDictWholeHydro:dict  # Dictionnary with the main characteristics of the subbasin
    landuseDict:dict                # Dictionnary with all landuses of the subbasin
    landuseHydroDict:dict           # Dictionnary with all landuses of the hydro subbasin

    # Further information
    surfaceDrained:float            # [km^2]
    surfaceDrainedHydro:float       # [km^2]
    timeDelay:float                 # [s]

    peakVal:float                   # [m³/s] peak value for total outFlow
    peakTime:datetime.datetime      # datetime of the peak for total outflow -> time delay is already applied

    # Hello!
    ptr_q_all:ct._Pointer|None      # Pointer to Fortran for the result matrix
    ptr_iv_saved:ct._Pointer|None   # Pointer to Fortran for the saved internal variables

    transferParam:Wolf_Param        # Parameter file with the type of transfer applied -> e.g. timeDelay

    _version:float                  # version of the wolfHydro python code. Useful for identifying the file versions to read and how to interpret them


    def __init__(self, _dateBegin:datetime.datetime=None, _dateEnd:datetime.datetime=None, _deltaT:int=0, _model=cst.measures,_workingDir:str="",
                 _hyeto:dict={}, _x:float=0.0, _y:float=0.0, surfaceDrained:float=0.0,
                 _iD_interiorPoint:int=1,_idSorted:int=1, name:str=None, readHydro=True, _tz:int=0, version:str=cst.VERSION_WOLFHYDRO):
        if(name is None):
            self.name = 'ss '+ str(_iD_interiorPoint)
        else:
            self.name = name
        self.iD = 'ss'+str(_iD_interiorPoint)
        self.iDSorted = _idSorted
        self.x = _x
        self.y = _y
        self.haveInlets = False
        self.alreadyUsed = False    # //
        self.isLeveled = False
        self.isActivated = True
        ## Time array containing all the timestamps
        # @var time timestamps array of dimension equal to rain and evap (or 1 element more than myHydro so far (VHM but not UH)).
        self.time = None

        self.dateBegin = _dateBegin     # Must be in GMT+0 !!!
        self.dateEnd = _dateEnd         # Must be in GMT+0 !!!
        self.deltaT = _deltaT
        # @var timezone in GMT saved to converted all computed or read data so that all data are expressed in GMT+0
        self.tz = _tz
        self.model = _model


        self.treated = False        # //
        self.myLevel = 1
        self.fileNameRead = _workingDir # //
        self.fileNameWrite = self.fileNameRead  # TO DO !!!!!!!!
        # self.intersectIndex = 0

        ## Dictionary containing all the objects Catchment:
        ## @var myHydro an array whose dimensions depends on the model chosen:
        #  - Unit hydrographs and Linear reservoir models : $1\times n$ elements
        #  - VHM model : $3\times n$ elements:
        #                myHydro[i][0] : overland flow
        #                myHydro[i][1] : interflow
        #                myHydro[i][2] : baseflow
        #  @unit $[\si{m}^3/\si{s}}]$
        self.myHydro = np.empty((0,0),dtype=ct.c_double, order='F')     # [mm/h] hydrograph of the subbasin (old version in [m^3/s]) (potentially with Fortran pointer to ptr_q_all)
        self.saved_iv = np.empty((0,0),dtype=ct.c_double, order='F')    # [mm/h] or [mm] or [-] depending on the variable (potentially with Fortran pointer to ptr_iv_saved)

        self.intletsObj = {}
        self.inlets = None
        self.inletsRaw = None
        self.downstreamObj = {}

        ## @var outFlow
        # Hydro of the hydrological subbasin. Combined with the potentiel upstream hydros. Consider timeDelay so that time is at 0
        # @unit $[\si{m}^3/\si{s}}]$
        self._outFlow = {}                           # [m^3/s] Hydro of the hydrological subbasin. Combined with the potentiel upstream hydros. Consider timeDelay so that time is at 0

        # self.outFlowRaw = []                        # [m^3/s]
        # Hyeto
        self.myHyetoDict = {}
        self.myRain = None                          # [mm/h]   Caution in the difference of units in rain !!!!!!
        self.rain = []                              # [m^3/h]  Caution in the difference of units in rain !!!!!!
        # Evapotranspiration
        self.myEvap = None                          # [mm/h]
        self.evap = None                            # [mm/h]
        # Temperature
        self.myTemp = None
        # Outflow converted in hystograph
        self.hydrograph = None        # //
        # self.hystograph = []

        # Main subbasin characteristics
        self.mainCharactDict = {}                   # Dictionnary with the main characteristics of the subbasin
        self.mainCharactDictWholeHydro = {}         # Dictionnary with the main characteristics of the hydro subbasin
        self.landuseDict = {}                       # Dictionnary with all landuses of the subbasin
        self.landuseHydroDict = {}                  # Dictionnary with all landuses of the hydro subbasin

        # Further information
        self.surfaceDrained = surfaceDrained        # [km^2]
        self.surfaceDrainedHydro = surfaceDrained   # [km^2]
        self.timeDelay = 0.0                        # [s]

        self.peakVal = 0.0                          # [m³/s] peak value for total outFlow
        self.peakTime = None                        # datetime of the peak for total outflow -> time delay is already applied

        # param files
        self.transferParam = None

        # Hello!
        self.ptr_q_all = None
        self.ptr_iv_saved = None

        # version of the Python WOLFHydro
        self._version = version


        # Verification of the unicity of the time array
        # Load all the hydrographs of the sub-basins
        if(self.model==cst.measures or self.model==cst.compare_opti):
            readHydro=False

        # Get the main characteristics of the subbasin. If the hydro can be read, so be the main characteristics
        if(readHydro):
            self.read_myMainCharacteristics(_workingDir)
            self.init_timeDelay()

        if(readHydro):
            timeTest, self.myHydro = self.get_hydro(self.iDSorted, _workingDir, tzDelta=datetime.timedelta(hours=self.tz))
            if(self.time is None):
                self.time = timeTest
            else:
                if not(np.array_equal(timeTest,self.time)):
                    print('ERROR: Time array not the same! Please check your answers.')
                    sys.exit()


        print('SubBasin Initialised!')




    def change_haveInlets(self):
        "This procedure only increment the number of inlets of a subbasin"
        self.haveInlets = True


    def get_hydro(self, iDSorted, workingDir, fileNames=None, tzDelta=datetime.timedelta(hours=0)):
        if(self.model==cst.tom_UH):
            print("Reading the Unit Hydrograph outlets...")

            # initialisation of the fileNames
            if(fileNames is None):
                subBasinName = 'Subbasin_' + str(iDSorted) + '/'
                typeOfFileName = 'simul_of.txt'
                fileName = os.path.join(workingDir, subBasinName, typeOfFileName)
                file_exists = os.path.exists(fileName)
                if(not(file_exists)):
                    typeOfFileName = 'simul_net_trans_rain.txt'
                    fileName = os.path.join(workingDir,subBasinName, typeOfFileName)
                    file_exists = os.path.exists(fileName)
                    if(file_exists):
                        print("ERROR : the file simul_net_trans_rain.txt is not used yet in this version! Please check version of the code before 05/11/2021 !")
                        print("Hydro file = ", fileName)
                        sys.exit()
                    else:
                        print("ERROR : the hydro file is not present here!")
                        print("Hydro file = ", fileName)
                        sys.exit()
            else:
                # The file can only be a string or a list with 1 string
                if(type(fileNames)==str):
                    fileName = workingDir + fileNames[0]
                elif(type(fileNames)==list and len(fileNames)!=1):
                    fileName = workingDir + fileNames
                else:
                    print("ERROR: Expecting only 1 file name for UH model!")
                    sys.exit()

            # Reading the hydro output file
            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = []
                i = 0
                for raw in data_reader:
                    if i>1:
                        list_data.append(raw)
                    i += 1
            matrixData = np.array(list_data).astype("float")
            timeArray = np.zeros(len(matrixData))                 # +1 as the time array is not one element more than the outlet in UH
            outFlow = np.zeros(len(matrixData),dtype=ct.c_double, order='F')

            # Init the time properties if not already done
            if self.dateBegin is None or self.dateEnd is None or self.deltaT == 0:
                self.dateBegin = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]),
                                                    hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.dateEnd = datetime.datetime(year=int(matrixData[-1][2]), month=int(matrixData[-1][1]), day=int(matrixData[-1][0]),
                                                    hour=int(matrixData[-1][3]), minute=int(matrixData[-1][4]), second=int(matrixData[-1][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.deltaT = (datetime.datetime(year=int(matrixData[1][2]), month=int(matrixData[1][1]), day=int(matrixData[1][0]),
                                hour=int(matrixData[1][3]), minute=int(matrixData[1][4]), second=int(matrixData[1][5]),
                                microsecond=0, tzinfo=datetime.timezone.utc) - self.dateBegin).total_seconds()

            secondsInDay = 24*60*60
            prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]),
                                         hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),
                                         microsecond=0, tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            if(self.dateBegin!=prevDate):
                print("ERROR: The first date in hydro data does not coincide with the one expected!")
                print("Date read = ", prevDate)
                print("Date expected = ", self.dateBegin)
                sys.exit()
            # outFlow[0] = matrixData[0][6]*self.surfaceDrained/3.6
            if self._version<2022.0:
                outFlow[0] = matrixData[0][6]/self.surfaceDrained*3.6
            else:
                outFlow[0] = matrixData[0][6]

            timeArray[0] = datetime.datetime.timestamp(prevDate)
            # Caution!! -1 is here because the size of hydros in UH is the same as rain (not the case in VHM)
            nbData = len(matrixData)

            for i in range(1,nbData):
                currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]),
                                             hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),
                                             microsecond=0, tzinfo=datetime.timezone.utc)
                currDate -= tzDelta
                prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]),
                                             hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),
                                             microsecond=0, tzinfo=datetime.timezone.utc)
                prevDate -= tzDelta
                diffDate = currDate - prevDate
                diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                timeArray[i] = datetime.datetime.timestamp(currDate)
                # timeArray[i] = timeArray[i-1] + diffTimeInSeconds
                # outFlow[i] = matrixData[i][6]*self.surfaceDrained/3.6
                outFlow[i] = matrixData[i][6]
            # timeArray[-1] = timeArray[-2] + diffTimeInSeconds
            # The last date is not taken into account in hydro as the last date rain and evap is needed for implicit simulations
            # if(self.dateEnd-diffDate!=currDate):
            #     print("ERROR: The last date in hydro data does not coincide with the one expected!")
            #     sys.exit()
            if(self.dateEnd!=currDate):
                if(self.dateEnd!=currDate+datetime.timedelta(seconds=diffTimeInSeconds)):
                    print("ERROR: The last date in hydro data does not coincide with the one expected!")
                    print("Date read = ", currDate)
                    print("Date expected = ", self.dateEnd)
                    sys.exit()
                else:
                    logging.warning(_("ERROR: The last date in hydro data does not coincide with the one expected!"))
                    logging.warning(_("Date read = "+ str(currDate)))
                    logging.warning(_("Date expected = "+ str(self.dateEnd)))
                    logging.warning(_("The time series will be adapted to fit the expected dimensions"))
                    timeArray = np.append(timeArray, 0)
                    outFlow = np.append(outFlow, 0.0)
            if(self.deltaT!=diffTimeInSeconds):
                print("ERROR: The last timestep in hydro data does not coincide with the one expected!")
                print("Delta t read = ", diffTimeInSeconds)
                print("Delta t expected = ", self.deltaT)
                sys.exit()
            # Save time array if it does not exist yet
            # Otherwise, check the consistency of the array with the time array of the object
            if(self.time is None):
                self.time=timeArray
            elif(self.time!=timeArray):
                print("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")
                sys.exit()

            if self._version<2022.0:
                outFlow[:] = outFlow[:]/self.surfaceDrained*3.6

        elif(self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH):
            # For this model, there are 3 different layers to read.

            print("Reading the 2 outlet files...")
            matrixData = []

            # Reading the overland flow file and time
            if(fileNames is None):
                subBasinName = os.path.join(workingDir, 'Subbasin_' + str(iDSorted))
                subBasinName = os.path.join(subBasinName, 'simul_')
                fileName = subBasinName + "of.txt"

                # fileName = subBasinName + "of.dat"
                # isOk, fileName = rd.check_path(fileName)
                # readBin = True
                # if not isOk:
                #     fileName = subBasinName + "of.txt"
                #     readBin = False

            else:
                if(len(fileNames)!=2):
                    print("ERROR: Expecting 2 file names for VHM model!")
                    sys.exit()
                fileName = workingDir + fileNames[0]
            #     readBin = False

            # if readBin:
            #     os.path.join(workingDir, 'Subbasin_' + str(iDSorted))
            #     list_data = rd.read_bin(os.path.join(workingDir, 'Subbasin_' + str(iDSorted)), 'simul_if.dat', hydro=True)
            #     matrixData = np.array(list_data).astype("float")
            # else:
            #     with open(fileName, newline = '') as fileID:
            #         data_reader = csv.reader(fileID, delimiter='\t')
            #         list_data = []
            #         i=0
            #         for raw in data_reader:
            #             if i>1:
            #                 list_data.append(raw)
            #             i += 1
            #     matrixData = np.array(list_data).astype("float")

            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = []
                i=0
                for raw in data_reader:
                    if i>1:
                        list_data.append(raw)
                    i += 1
            matrixData = np.array(list_data).astype("float")

            timeArray = np.zeros(len(matrixData))
            # Init of the outflow array
            outFlow = np.zeros((len(matrixData),2),dtype=ct.c_double, order='F')

            # Init the time properties if not already done
            if self.dateBegin is None or self.dateEnd is None or self.deltaT == 0:
                self.dateBegin = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]),
                                                    hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.dateEnd = datetime.datetime(year=int(matrixData[-1][2]), month=int(matrixData[-1][1]), day=int(matrixData[-1][0]),
                                                    hour=int(matrixData[-1][3]), minute=int(matrixData[-1][4]), second=int(matrixData[-1][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.deltaT = (datetime.datetime(year=int(matrixData[1][2]), month=int(matrixData[1][1]), day=int(matrixData[1][0]),
                                hour=int(matrixData[1][3]), minute=int(matrixData[1][4]), second=int(matrixData[1][5]),
                                microsecond=0, tzinfo=datetime.timezone.utc) - self.dateBegin).total_seconds()

            secondsInDay = 24*60*60
            prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            if(self.dateBegin!=prevDate):
                print("ERROR: The first date in hydro data does not coincide with the one expected!")
                print("Date read = ", prevDate)
                print("Date expected = ", self.dateBegin)
                sys.exit()
            timeArray[0] = datetime.datetime.timestamp(prevDate)
            # Older versions of that of UH file was expressed in m³/s
            if self._version<2022.0:
                outFlow[0][0] = matrixData[0][6]/self.surfaceDrained*3.6
            else:
                outFlow[0][0] = matrixData[0][6]
            for i in range(1,len(matrixData)):

                currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]),
                                             hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),
                                             microsecond=0, tzinfo=datetime.timezone.utc)
                currDate -= tzDelta
                prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]),
                                             hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),
                                             microsecond=0, tzinfo=datetime.timezone.utc)
                prevDate -= tzDelta
                diffDate = currDate - prevDate
                diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                timeArray[i] = datetime.datetime.timestamp(currDate)
                # timeArray[i] = timeArray[i-1] + diffTimeInSeconds
                if self._version<2022.0:
                    outFlow[i][0] = matrixData[i][6]/self.surfaceDrained*3.6
                else:
                    outFlow[i][0] = matrixData[i][6]

            # timeArray[-1] = timeArray[-2] + diffTimeInSeconds
            # The last date is not taken into account in hydro as the last date rain and evap is needed for implicit simulations
            # if(self.dateEnd-diffDate!=currDate):
            #     print("ERROR: The last date in hydro data does not coincide with the one expected!")
            #     sys.exit()
            # if(self.dateEnd!=currDate):
            #     print("ERROR: The last date in hydro data does not coincide with the one expected!")
            #     print("Date read = ", currDate)
            #     print("Date expected = ", self.dateEnd)
            #     sys.exit()
            if(self.dateEnd!=currDate):
                if(self.dateEnd!=currDate+datetime.timedelta(seconds=diffTimeInSeconds)):
                    print(_("ERROR: The last date in hydro data does not coincide with the one expected!"))
                    print(_("Date read = ", currDate))
                    print(_("Date expected = ", self.dateEnd))
                    sys.exit()
                else:
                    logging.warning("ERROR: The last date in hydro data does not coincide with the one expected!")
                    logging.warning(_("Date read = ") + str(currDate))
                    logging.warning(_("Date expected = ") +  str(self.dateEnd))
                    logging.warning(_("The time series will be adapted to fit the expected dimensions"))
                    timeArray = np.append(timeArray, 0)
                    # outFlow = np.append(outFlow, 0.0)
                    newLine = np.zeros((1, 2), dtype=ct.c_double, order='F')
                    outFlow = np.vstack([outFlow, newLine])

            if(self.deltaT!=diffTimeInSeconds):
                print("ERROR: The last timestep in hydro data does not coincide with the one expected!")
                print("Delta t = ", diffTimeInSeconds)
                print("Delta t expected = ", self.deltaT)
                sys.exit()
            # Save time array if it does not exist yet
            # Otherwise, check the consistency of the array with the time array of the object
            if(self.time is None):
                self.time=timeArray
            elif((self.time!=timeArray).all()):
                print("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")
                sys.exit()

            # Reading the interflow file
            matrixData = []
            # if(fileNames is None):
            #     # Changes ongoing -> read bin
            #     fileName = subBasinName + "if.dat"
            #     isOk, fileName = rd.check_path(fileName)
            #     readBin = True
            #     if not isOk:
            #         fileName = subBasinName + "if.txt"
            #         readBin = False
            #     # ======
            # else:
            #     fileName = workingDir + fileNames[1]
            #     readBin = False

            fileName = subBasinName + "if.txt"
            readBin = False

            if readBin:
                os.path.join(workingDir, 'Subbasin_' + str(iDSorted))
                list_data = rd.read_bin(os.path.join(workingDir, 'Subbasin_' + str(iDSorted)), 'simul_if.dat', hydro=True)
                matrixData = np.array(list_data).astype("float")
            else:
                with open(fileName, newline = '') as fileID:
                    data_reader = csv.reader(fileID, delimiter='\t')
                    list_data = []
                    i=0
                    for raw in data_reader:
                        if i>1:
                            list_data.append(raw)
                        i += 1
                matrixData = np.array(list_data).astype("float")

            if(self.model==cst.tom_2layers_linIF):
                # outFlow[0][1] = matrixData[0][6]*self.surfaceDrained/3.6
                outFlow[0][1] = matrixData[0][6]
                for i in range(1,len(matrixData)):
                    # outFlow[i][1] = matrixData[i][6]*self.surfaceDrained/3.6
                    outFlow[i][1] = matrixData[i][6]
            else:
                if self._version<2022.0:
                    outFlow[0][1] = matrixData[0][6]/self.surfaceDrained*3.6
                    for i in range(1,len(matrixData)):
                        outFlow[i][1] = matrixData[i][6]/self.surfaceDrained*3.6
                else:
                    outFlow[0][1] = matrixData[0][6]
                    for i in range(1,len(matrixData)):
                        outFlow[i][1] = matrixData[i][6]

        elif(self.model==cst.tom_VHM):
            # For this model, there are 3 different layers to read.

            print("Reading the 3 VHM outlet files...")
            matrixData = []

            # Reading the overland flow file and time
            if(fileNames is None):
                subBasinName = os.path.join(workingDir, 'Subbasin_' + str(iDSorted))
                subBasinName = os.path.join(subBasinName, 'simul_')
                fileName = subBasinName + "of.txt"
            else:
                if(len(fileNames)!=3):
                    print("ERROR: Expecting 3 file names for VHM model!")
                    sys.exit()
                fileName = workingDir + fileNames[0]

            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = []
                i=0
                for raw in data_reader:
                    if i>1:
                        list_data.append(raw)
                    i += 1
            matrixData = np.array(list_data).astype("float")
            timeArray = np.zeros(len(matrixData))

            # Init the time properties if not already done
            if self.dateBegin is None or self.dateEnd is None or self.deltaT == 0:
                self.dateBegin = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]),
                                                    hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.dateEnd = datetime.datetime(year=int(matrixData[-1][2]), month=int(matrixData[-1][1]), day=int(matrixData[-1][0]),
                                                    hour=int(matrixData[-1][3]), minute=int(matrixData[-1][4]), second=int(matrixData[-1][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.deltaT = (datetime.datetime(year=int(matrixData[1][2]), month=int(matrixData[1][1]), day=int(matrixData[1][0]),
                                hour=int(matrixData[1][3]), minute=int(matrixData[1][4]), second=int(matrixData[1][5]),
                                microsecond=0, tzinfo=datetime.timezone.utc) - self.dateBegin).total_seconds()

            # Init of the outflow array
            outFlow = np.zeros((len(matrixData),3),dtype=ct.c_double, order='F')

            secondsInDay = 24*60*60
            prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            if(self.dateBegin!=prevDate):
                print("ERROR: The first date in hydro data does not coincide with the one expected!")
                print("Date read = ", prevDate)
                print("Date expected = ", self.dateBegin)
                sys.exit()
            timeArray[0] = datetime.datetime.timestamp(prevDate)
            # outFlow[0][0] = matrixData[0][6]*self.surfaceDrained/3.6
            outFlow[0][0] = matrixData[0][6]
            for i in range(1,len(matrixData)):
                currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
                currDate -= tzDelta
                prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
                prevDate -= tzDelta
                diffDate = currDate - prevDate
                diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                timeArray[i] = datetime.datetime.timestamp(currDate)
                # timeArray[i] = timeArray[i-1] + diffTimeInSeconds

                # outFlow[i][0] = matrixData[i][6]*self.surfaceDrained/3.6
                outFlow[i][0] = matrixData[i][6]

            # timeArray[-1] = timeArray[-2] + diffTimeInSeconds
            # The last date is not taken into account in hydro as the last date rain and evap is needed for implicit simulations
            # if(self.dateEnd-diffDate!=currDate):
            #     print("ERROR: The last date in hydro data does not coincide with the one expected!")
            #     sys.exit()
            if(self.dateEnd!=currDate):
                print("ERROR: The last date in hydro data does not coincide with the one expected!")
                print("Date read = ", currDate)
                print("Date expected = ", self.dateEnd)
                sys.exit()
            if(self.deltaT!=diffTimeInSeconds):
                print("ERROR: The last timestep in hydro data does not coincide with the one expected!")
                print("Delta t read = ", diffTimeInSeconds)
                print("Delta t expected = ", self.deltaT)
                sys.exit()
            # Save time array if it does not exist yet
            # Otherwise, check the consistency of the array with the time array of the object
            if(self.time is None):
                self.time=timeArray
            elif((self.time!=timeArray).all()):
                print("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")
                sys.exit()

            # Reading the interflow file
            matrixData = []
            if(fileNames is None):
                fileName = subBasinName + "if.txt"
            else:
                fileName = workingDir + fileNames[1]

            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = []
                i=0
                for raw in data_reader:
                    if i>1:
                        list_data.append(raw)
                    i += 1
            matrixData = np.array(list_data).astype("float")

            # outFlow[0][1] = matrixData[0][6]*self.surfaceDrained/3.6
            outFlow[0][1] = matrixData[0][6]
            for i in range(1,len(matrixData)):
                # outFlow[i][1] = matrixData[i][6]*self.surfaceDrained/3.6
                outFlow[i][1] = matrixData[i][6]

            # Reading the baseflow file
            matrixData = []
            if(fileNames is None):
                fileName = subBasinName + "bf.txt"
            else:
                fileName = workingDir + fileNames[2]

            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = []
                i=0
                for raw in data_reader:
                    if i>1:
                        list_data.append(raw)
                    i += 1
            matrixData = np.array(list_data).astype("float")

            # outFlow[0][2] = matrixData[0][6]*self.surfaceDrained/3.6
            outFlow[0][2] = matrixData[0][6]
            for i in range(1,len(matrixData)):
                # outFlow[i][2] = matrixData[i][6]*self.surfaceDrained/3.6
                outFlow[i][2] = matrixData[i][6]

        elif(self.model==cst.tom_GR4):
            # For this model, there is only 1 output to consider.

            print("Reading the 1 outlet file ...")
            matrixData = []

            # Reading the overland flow file and time
            if(fileNames is None):
                subBasinName = os.path.join(workingDir, 'Subbasin_' + str(iDSorted), 'simul_')
                fileName = subBasinName + "GR4_out.txt"
            else:
                # The file can only be a string or a list with 1 string
                if(type(fileNames)==str):
                    fileName = workingDir + fileNames[0]
                elif(type(fileNames)==list and len(fileNames)==1):
                    fileName = workingDir + fileNames
                else:
                    print("ERROR: Expecting only 1 file name for UH model!")
                    sys.exit()

            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = []
                i=0
                for raw in data_reader:
                    if i>1:
                        list_data.append(raw)
                    i += 1
            matrixData = np.array(list_data).astype("float")
            timeArray = np.zeros(len(matrixData))
            # Init of the outflow array
            outFlow = np.zeros((len(matrixData),1),dtype=ct.c_double, order='F')

            # Init the time properties if not already done
            if self.dateBegin is None or self.dateEnd is None or self.deltaT == 0:
                self.dateBegin = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]),
                                                    hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.dateEnd = datetime.datetime(year=int(matrixData[-1][2]), month=int(matrixData[-1][1]), day=int(matrixData[-1][0]),
                                                    hour=int(matrixData[-1][3]), minute=int(matrixData[-1][4]), second=int(matrixData[-1][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.deltaT = (datetime.datetime(year=int(matrixData[1][2]), month=int(matrixData[1][1]), day=int(matrixData[1][0]),
                                hour=int(matrixData[1][3]), minute=int(matrixData[1][4]), second=int(matrixData[1][5]),
                                microsecond=0, tzinfo=datetime.timezone.utc) - self.dateBegin).total_seconds()

            secondsInDay = 24*60*60
            prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            if(self.dateBegin!=prevDate):
                print("ERROR: The first date in hydro data does not coincide with the one expected!")
                print("Date read = ", prevDate)
                print("Date expected = ", self.dateBegin)
                sys.exit()
            timeArray[0] = datetime.datetime.timestamp(prevDate)
            # outFlow[0][0] = matrixData[0][6]*self.surfaceDrained/3.6
            outFlow[0][0] = matrixData[0][6]
            for i in range(1,len(matrixData)):
                currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]),
                                             hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),
                                             microsecond=0, tzinfo=datetime.timezone.utc)
                currDate -= tzDelta
                prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]),
                                             hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),
                                             microsecond=0, tzinfo=datetime.timezone.utc)
                prevDate -= tzDelta
                diffDate = currDate - prevDate
                diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                timeArray[i] = datetime.datetime.timestamp(currDate)
                # timeArray[i] = timeArray[i-1] + diffTimeInSeconds

                # outFlow[i][0] = matrixData[i][6]*self.surfaceDrained/3.6
                outFlow[i][0] = matrixData[i][6]

            # timeArray[-1] = timeArray[-2] + diffTimeInSeconds
            # The last date is not taken into account in hydro as the last date rain and evap is needed for implicit simulations
            # if(self.dateEnd-diffDate!=currDate):
            #     print("ERROR: The last date in hydro data does not coincide with the one expected!")
            #     sys.exit()
            if(self.dateEnd!=currDate):
                print("ERROR: The last date in hydro data does not coincide with the one expected!")
                print("Date read = ", currDate)
                print("Date expected = ", self.dateEnd)
                sys.exit()
            if(self.deltaT!=diffTimeInSeconds):
                print("Delta t read = ", diffTimeInSeconds)
                print("Delta t expected = ", self.deltaT)
                print("ERROR: The last timestep in hydro data does not coincide with the one expected!")
                sys.exit()
            # Save time array if it does not exist yet
            # Otherwise, check the consistency of the array with the time array of the object
            if(self.time is None):
                self.time=timeArray
            elif((self.time!=timeArray).all()):
                print("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")
                sys.exit()

        elif(self.model==cst.measures):
            print("Reading the measurements outlet file...")
            if(type(fileNames)!=str):
                print("ERROR: Expecting only 1 file name for measurements!")
                sys.exit()
            fileName = os.path.join(workingDir,fileNames)
            nbCl = 0
            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter=' ',skipinitialspace=True)
                list_data = []
                i=0
                for raw in data_reader:
                    if i>3:
                        list_data.append(raw[0:nbCl])
                    if i==2:
                        nbCl = int(raw[0])
                    i += 1

            matrixData = np.array(list_data).astype("float")
            # Init the time properties if not already done
            if self.dateBegin is None or self.dateEnd is None or self.deltaT == 0:
                if nbCl==5:
                    self.dateBegin = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), tzinfo=datetime.timezone.utc)
                    self.dateEnd = datetime.datetime(year=int(matrixData[-1][2]), month=int(matrixData[-1][1]), day=int(matrixData[-1][0]), hour=int(matrixData[-1][3]), tzinfo=datetime.timezone.utc)
                    self.deltaT = (datetime.datetime(year=int(matrixData[1][2]), month=int(matrixData[1][1]), day=int(matrixData[1][0]), hour=int(matrixData[1][3]), tzinfo=datetime.timezone.utc)
                                    - self.dateBegin).total_seconds()
                if nbCl==7:
                    self.dateBegin = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]),
                                                       hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),
                                                       microsecond=0, tzinfo=datetime.timezone.utc)
                    self.dateEnd = datetime.datetime(year=int(matrixData[-1][2]), month=int(matrixData[-1][1]), day=int(matrixData[-1][0]),
                                                       hour=int(matrixData[-1][3]), minute=int(matrixData[-1][4]), second=int(matrixData[-1][5]),
                                                       microsecond=0, tzinfo=datetime.timezone.utc)
                    self.deltaT = (datetime.datetime(year=int(matrixData[1][2]), month=int(matrixData[1][1]), day=int(matrixData[1][0]),
                                    hour=int(matrixData[1][3]), minute=int(matrixData[1][4]), second=int(matrixData[1][5]),
                                    microsecond=0, tzinfo=datetime.timezone.utc) - self.dateBegin).total_seconds()

            # Init of the outflow array
            timeInterval = self.dateEnd-self.dateBegin+datetime.timedelta(seconds=self.deltaT)
            outFlow = np.zeros(int(timeInterval.total_seconds()/self.deltaT),dtype=ct.c_double, order='F')
            timeArray = np.zeros(int(timeInterval.total_seconds()/self.deltaT))

            # From the measurements file, we will only read the desired data and save it in outflow
            prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            index = 0
            add1Hour = datetime.timedelta(hours=1)
            secondsInDay = 24*60*60

            # Verification
            if(datetime.datetime.timestamp(prevDate)>datetime.datetime.timestamp(self.dateBegin)):
                logging.error("ERROR: the first hydro data element is posterior to dateBegin!")
                print("Date read = ", prevDate)
                print("Date expected = ", self.dateBegin)
                sys.exit()

            if(nbCl==5):
                # Caution : the index of the loop start at 24 because the timestamp function
                # does not work until the 2/01/1970 at 03:00:00. => Je ne sais pas pourquoi ?!
                for i in range(25,len(matrixData)):
                    # The hours are written in the file in [1,24] instead of [0,23]. Conversion below:
                    if(int(matrixData[i][3])==24):
                        currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=23, tzinfo=datetime.timezone.utc) + add1Hour
                    else:
                        currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=int(matrixData[i][3]), tzinfo=datetime.timezone.utc)
                    currDate -= tzDelta
                    if(int(matrixData[i-1][3])==24):
                        prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=23, tzinfo=datetime.timezone.utc) + add1Hour
                    else:
                        prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=int(matrixData[i-1][3]), tzinfo=datetime.timezone.utc)
                    prevDate -= tzDelta
                    # Start at dateBegin and go to the element before dateEnd. Because the last date is needed for rain and evap in implicit simulations.
                    if(datetime.datetime.timestamp(currDate)>=datetime.datetime.timestamp(self.dateBegin) and \
                    datetime.datetime.timestamp(currDate)<=datetime.datetime.timestamp(self.dateEnd)):
                        outFlow[index] = matrixData[i][4]
                        diffDate = currDate - prevDate
                        diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                        timeArray[index] = datetime.datetime.timestamp(currDate)
                        # timeArray[index] = timeArray[index-1] + diffTimeInSeconds
                        index += 1
            elif(nbCl==7):
                for i in range(len(matrixData)):
                    # The hours are written in the file in [1,24] instead of [0,23]. Conversion below:
                    currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),tzinfo=datetime.timezone.utc)
                    currDate -= tzDelta
                    prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),tzinfo=datetime.timezone.utc)
                    prevDate -= tzDelta
                    # Start at dateBegin and go to the element before dateEnd. Because the last date is needed for rain and evap in implicit simulations.
                    if(datetime.datetime.timestamp(currDate)>=datetime.datetime.timestamp(self.dateBegin) and \
                    datetime.datetime.timestamp(currDate)<=datetime.datetime.timestamp(self.dateEnd)):
                        if(matrixData[i][6]<0):
                            outFlow[index] = 0.0
                        else:
                            outFlow[index] = matrixData[i][6]
                        outFlow[index] = matrixData[i][6]
                        diffDate = currDate - prevDate
                        diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                        timeArray[index] = datetime.datetime.timestamp(currDate)
                        # timeArray[index] = timeArray[index-1] + diffTimeInSeconds
                        index += 1
            # The last date is not taken into account in hydro as the last date rain and evap is needed for implicit simulations
            diffDate = currDate - prevDate
            # Add the last element in the time matrix as its size is 1 element bigger than outlet
            # timeArray[-1] = timeArray[-2] + diffTimeInSeconds
            if(self.deltaT!=diffDate.seconds):
                print("ERROR: The last timestep in hydro data does not coincide with the one expected!")
                print("Delta t read = ", diffDate.seconds)
                print("Delta t expected = ", self.deltaT)
                sys.exit()
            # Save time array if it does not exist yet
            # Otherwise, check the consistency of the array with the time array of the object
            if(self.time is None):
                self.time=timeArray
            elif(self.time!=timeArray):
                print("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")
                sys.exit()

        elif(self.model==cst.compare_opti):
            print("Reading the measurements outlet file...")
            if(type(fileNames)!=str):
                print("ERROR: Expecting only 1 file name for measurements!")
                sys.exit()
            fileName = os.path.join(workingDir, fileNames)
            nbCl = 0
            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t',skipinitialspace=True)
                list_data = []
                i=0
                for raw in data_reader:
                    if i==0:
                        nbL = int(raw[0])
                        nbCl = int(raw[1])
                    else:
                        list_data.append(raw[0:nbCl])
                    i += 1

            matrixData = np.array(list_data).astype("float")

            # Init the time properties if not already done
            if self.dateBegin is None or self.dateEnd is None or self.deltaT == 0:
                self.dateBegin = datetime.datetime.fromtimestamp(matrixData[0][0], tz=datetime.timezone.utc)
                self.dateEnd = datetime.datetime.fromtimestamp(matrixData[-1][0], tz=datetime.timezone.utc)
                self.deltaT = matrixData[1][0]-matrixData[0][0]

            # Init of the outflow array
            timeInterval = self.dateEnd-self.dateBegin+datetime.timedelta(seconds=self.deltaT)
            # outFlow = np.zeros(int(timeInterval.total_seconds()/self.deltaT),dtype=ct.c_double, order='F')
            outFlow = np.zeros(len(matrixData),dtype=ct.c_double, order='F')
            timeArray = np.zeros(len(matrixData))

            # From the measurements file, we will only read the desired data and save it in outflow
            prevDate = int(matrixData[0][0])
            outFlow[0] = matrixData[0][1]
            timeArray[0] = prevDate
            index = 1
            add1Hour = datetime.timedelta(hours=1)
            secondsInDay = 24*60*60

            # Verification
            if(prevDate>datetime.datetime.timestamp(self.dateBegin)):
                logging.error("ERROR: the first hydro data element is posterior to dateBegin!")
                print("Date read = ", prevDate)
                print("Date expected = ", self.dateBegin)
                sys.exit()

            for i in range(1,len(matrixData)):
                currDate = int(matrixData[i][0])
                prevDate = int(matrixData[i-1][0])
                # Start at dateBegin and go to the element before dateEnd. Because the last date is needed for rain and evap in implicit simulations.
                if(currDate>=datetime.datetime.timestamp(self.dateBegin) and \
                currDate<=datetime.datetime.timestamp(self.dateEnd)):
                    outFlow[index] = matrixData[i][1]
                    diffDate = currDate - prevDate
                    timeArray[index] = currDate
                    index += 1


            # The last date is not taken into account in hydro as the last date rain and evap is needed for implicit simulations
            diffDate = currDate - prevDate
            # Add the last element in the time matrix as its size is 1 element bigger than outlet
            # timeArray[-1] = timeArray[-2] + diffTimeInSeconds
            if(self.deltaT!=diffDate):
                print("WARNING: The last timestep in hydro data does not coincide with the one expected!")
                print("Delta t read = ", diffDate)
                print("Delta t expected = ", self.deltaT)
                print("Replacing the deltaT by the one read on the file!")
                self.deltaT = diffDate
                # sys.exit()
            # Save time array if it does not exist yet
            # Otherwise, check the consistency of the array with the time array of the object
            if(self.time is None):
                self.time=timeArray
            elif(self.time!=timeArray):
                print("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")
                sys.exit()
            return timeArray[:index], outFlow[:index]

        else:
            # Valid for any hydro model with an assement module at the end, there is only 1 output to consider.

            print("Reading the 1 outlet file ...")
            matrixData = []

            # Reading the overland flow file and time
            if(fileNames is None):
                subBasinName = os.path.join(workingDir, 'Subbasin_' + str(iDSorted), 'simul_')
                fileName = subBasinName + "out.txt"
            else:
                # The file can only be a string or a list with 1 string
                if(type(fileNames)==str):
                    fileName = workingDir + fileNames[0]
                elif(type(fileNames)==list and len(fileNames)==1):
                    fileName = workingDir + fileNames
                else:
                    print("ERROR: Expecting only 1 file name for UH model!")
                    sys.exit()

            if not Path(fileName).exists():
                logging.error("The file " + fileName + " does not exist!")
                return None, None

            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = []
                i=0
                for raw in data_reader:
                    if i>1:
                        list_data.append(raw)
                    i += 1
            matrixData = np.array(list_data).astype("float")
            timeArray = np.zeros(len(matrixData))
            # Init of the outflow array
            outFlow = np.zeros((len(matrixData),1),dtype=ct.c_double, order='F')

            # Init the time properties if not already done
            if self.dateBegin is None or self.dateEnd is None or self.deltaT == 0:
                self.dateBegin = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]),
                                                    hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.dateEnd = datetime.datetime(year=int(matrixData[-1][2]), month=int(matrixData[-1][1]), day=int(matrixData[-1][0]),
                                                    hour=int(matrixData[-1][3]), minute=int(matrixData[-1][4]), second=int(matrixData[-1][5]),
                                                    microsecond=0, tzinfo=datetime.timezone.utc)
                self.deltaT = (datetime.datetime(year=int(matrixData[1][2]), month=int(matrixData[1][1]), day=int(matrixData[1][0]),
                                hour=int(matrixData[1][3]), minute=int(matrixData[1][4]), second=int(matrixData[1][5]),
                                microsecond=0, tzinfo=datetime.timezone.utc) - self.dateBegin).total_seconds()

            secondsInDay = 24*60*60
            prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            if(self.dateBegin!=prevDate):
                print("ERROR: The first date in hydro data does not coincide with the one expected!")
                print("Date read = ", prevDate)
                print("Date expected = ", self.dateBegin)
                sys.exit()
            timeArray[0] = datetime.datetime.timestamp(prevDate)
            outFlow[0][0] = matrixData[0][6]

            for i in range(1,len(matrixData)):
                currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]),
                                             hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),
                                             microsecond=0, tzinfo=datetime.timezone.utc)
                currDate -= tzDelta
                prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]),
                                             hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),
                                             microsecond=0, tzinfo=datetime.timezone.utc)
                prevDate -= tzDelta
                diffDate = currDate - prevDate
                diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                timeArray[i] = datetime.datetime.timestamp(currDate)

                outFlow[i][0] = matrixData[i][6]

            if(self.dateEnd!=currDate):
                print("ERROR: The last date in hydro data does not coincide with the one expected!")
                print("Date read = ", currDate)
                print("Date expected = ", self.dateEnd)
                sys.exit()
            if(self.deltaT!=diffTimeInSeconds):
                print("Delta t read = ", diffTimeInSeconds)
                print("Delta t expected = ", self.deltaT)
                print("ERROR: The last timestep in hydro data does not coincide with the one expected!")
                sys.exit()
            # Save time array if it does not exist yet
            # Otherwise, check the consistency of the array with the time array of the object
            if(self.time is None):
                self.time=timeArray
            elif((self.time!=timeArray).all()):
                print("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")
                sys.exit()

        return timeArray, outFlow


    def get_outFlow_noDelay(self, unit='m3/s'):
        """
        This function returns the total outlet of the basin and considers t0=0 at the outlet of the
        subbasin without considering timeDelay (the time of the real outlet of the whole potential catchment)
        """
        logging.warning("This function is operational but obsolate since version" + str(cst.VERSION_WOLFHYDRO))

        # nameOut = list(self.outFlow.items())[0][0]
        # myOutFlow = self.outFlow[nameOut]["Net"]
        # tmpHydro = np.zeros(len(myOutFlow))
        # index = math.floor(self.timeDelay/self.deltaT)
        # if(index==0):
        #     tmpHydro = myOutFlow.copy()
        # elif(index<len(myOutFlow)):
        #     tmpHydro[:-index] = myOutFlow[index:]
        # else:
        #     print("Warning: the simulation time is not long enough for this subbasin to be taken into account")

        #     print("Error informations : ")
        #     print("Function name : get_outFlow_noDelay()")
        #     print("index = ", index)
        #     print("len(myOutFlow) = ", len(myOutFlow))
        #     print("self.timeDelay = ", self.timeDelay)
        #     return tmpHydro

        # if unit=='mm/h':
        #     tmpHydro *= 3.6/self.surfaceDrainedHydro


        return self.get_outFlow(unit=unit)



    def get_outFlowRaw_noDelay(self, unit='m3/s'):
        """
        This function returns the total raw outlet of the basin and considers t0=0 at the outlet of the
        subbasin without considering timeDelay (the time of the real outlet of the whole potential catchment)
        """

        logging.warning("This function is operational but obsolate since version" + str(cst.VERSION_WOLFHYDRO))

        # nameOut = list(self.outFlow.items())[0][0]
        # myOutFlow = self.outFlow[nameOut]["Raw"]
        # tmpHydro = np.zeros(len(myOutFlow))
        # index = math.floor(self.timeDelay/self.deltaT)
        # if(index==0):
        #     tmpHydro = myOutFlow.copy()
        # elif(index<len(myOutFlow)):
        #     tmpHydro[:-index] = myOutFlow[index:]
        # else:
        #     logging.error("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
        #     logging.error("Error informations : ")
        #     logging.error("Function name : get_outFlowRaw_noDelay()")
        #     logging.error("index = " + str(index))
        #     logging.error("len(myOutFlow) = " + str(len(myOutFlow)))
        #     logging.error("self.timeDelay = " + str(self.timeDelay))
        #     return

        # if unit=='mm/h':
        #     tmpHydro *= 3.6/self.surfaceDrainedHydro

        return self.get_outFlow(typeOutFlow="Raw", unit=unit)


    def get_inlets_noDelay(self, unit='m3/s'):
        """
        This function returns the total inlets of the basin and considers t0=0 at the outlet of the
        subbasin without considering timeDelay (the time of the real outlet of the whole potential catchment)
        """

        logging.warning("This function is operational but obsolate since version" + str(cst.VERSION_WOLFHYDRO))

        # nameOut = list(self.outFlow.items())[0][0]
        # myInlets = self.inlets
        # tmpHydro = np.zeros(len(myInlets))
        # index = math.floor(self.timeDelay/self.deltaT)
        # if(index==0):
        #     tmpHydro = myInlets.copy()
        # elif(index<len(myInlets)):
        #     tmpHydro[:-index] = myInlets[index:]
        # else:
        #     print("Warning: the simulation time is not long enough for this subbasin to be taken into account")

        #     print("Error informations : ")
        #     print("Function name : get_inlets_noDelay()")
        #     print("index = ", index)
        #     print("len(myInlets) = ", len(myInlets))
        #     print("self.timeDelay = ", self.timeDelay)
        #     return

        # if unit=='mm/h':
        #     tmpHydro *= 3.6/self.surfaceDrainedHydro

        return self.inlets


    def add_name(self, myName):
        "this function add a name to the subasin"
        self.name = myName


    def increment_level(self):
        "This procedure increment the level in the Topo dictionary"
        self.myLevel += 1


    def set_level(self, level):
        self.myLevel = level


    def add_inlet(self, toPoint, name="DEFAULT"):
        "This procedure link the inlets to the object"
        self.intletsObj[name] = toPoint


    def add_downstreamObj(self, toPoint, name="DEFAULT"):
        "This procedure link the downstream element to the object"
        if toPoint is not None:
            self.downstreamObj[name] = toPoint
        self._outFlow[name] = {}
        self._outFlow[name]["Net"] = []
        self._outFlow[name]["Raw"] = []


    def compute_hydro(self):
        r"""
        This procedure computes the total hydrograph and raw hydrograph of subbasin

        The total hydrograph $q_{tot} is obtained with the formula:
        \f[
        q_{tot} = \sum q_{\text{inlets}} + q_{\text{me}}$
        \f]
        , with $q_{\text{me}}$ the hydrograph of the subbasin alone.

        Internal variable changed: outFlowRaw, outFlow, inletsRaw
        CAUTION:
            - Discussion about the ceil or the floor for the timeDelay indice!!!
            - UPDATE 2023.1 now the outFlow are not delayed anymore !!!! -> IMPORTANT UPDATE

        """
        if(len(self._outFlow)==0):
            self._outFlow["DEFAULT"] = {}

        nameOutFlow = list(self._outFlow.items())[0][0]
        # Sum all the inlets hydrographs
        self.sum_inlets()
        if(self.model==cst.tom_UH or self.model==cst.measures or
           self.model==cst.tom_GR4 or self.model==cst.compare_opti):
            tmpHydro = np.zeros(len(self.myHydro),dtype=ct.c_double, order='F')
            if(self.model==cst.tom_GR4):
                tmpHydro = self.myHydro[:,0]*self.surfaceDrained/3.6
            else:
                # tmpHydro = self.myHydro*self.surfaceDrained/3.6
                tmpHydro = self.get_myHydro(unit="m3/s")

            # Raw hydrograp
            self._outFlow[nameOutFlow]["Raw"] = self.inletsRaw + tmpHydro
            # Real hydrograph
            self._outFlow[nameOutFlow]["Net"]  = self.inlets + tmpHydro
        elif(self.model==cst.tom_VHM or self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH or
             self.model==cst.tom_HBV or self.model==cst.tom_SAC_SMA or self.model==cst.tom_NAM or self.model==cst.tom_SAC_SMA_LROF):
            tmpOutFlow = np.sum(self.myHydro,1)*self.surfaceDrained/3.6

            # Raw hydrograph
            self._outFlow[nameOutFlow]["Raw"] = np.zeros(len(tmpOutFlow))
            self._outFlow[nameOutFlow]["Raw"] = self.inletsRaw + tmpOutFlow
            # for i in range(len(self.myHydro)):
            #     self.outFlowRaw[i] = self.inletsRaw[i] + np.sum(self.myHydro[i])

            # Real hydrograph
            self._outFlow[nameOutFlow]["Net"] = np.zeros(len(self.myHydro))
            self._outFlow[nameOutFlow]["Net"] = self.inlets + tmpOutFlow
            # for i in range(len(self.myHydro)):
            #     self.outFlow[i] = self.inlets[i] + np.sum(self.myHydro[i])


    def sum_inlets(self):
        """ Sum all the inlet hydrographs of a subbasin. Return an array of zeros otherwise.

            Internal variable changed: self.inlets, self.inletsRaw
        """
        if(self.haveInlets):
            nameInlet = list(self.intletsObj.items())[0][0]
            curObj = self.intletsObj[nameInlet]
            timeInlet = curObj.timeDelay
            deltaTr = timeInlet - self.timeDelay
            self.inlets = curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameInlet, lag=deltaTr)
            self.inletsRaw = curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameInlet, lag=deltaTr)
            for i in range(1,len(self.intletsObj)):
                nameInlet = list(self.intletsObj.items())[i][0]
                curObj = self.intletsObj[nameInlet]
                timeInlet = curObj.timeDelay
                deltaTr = timeInlet - self.timeDelay
                self.inlets += curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameInlet, lag=deltaTr)
                self.inletsRaw += curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameInlet, lag=deltaTr)
        else:
            if self.myHydro is not None:
                self.inlets = np.zeros(len(self.myHydro), dtype=ct.c_double, order='F')
                self.inletsRaw = np.zeros(len(self.myHydro), dtype=ct.c_double, order='F')
            else:
                logging.error("ERROR: No hydrograph computed for this subbasin!")


    def add_rain(self, workingDir, fileName=None, tzDelta=datetime.timedelta(hours=0)):
        """ This procedure
            - reads: the time, rain in the rain file
            - saves: the rain of the subbasin, sum of the rain's inlets
            - returns: the time array read.
            - Variables modified: self.rain, self.myRain
        """
        # Reading and saving the rain's basin
        if(fileName is None):
            fileName = 'Subbasin_'+str(self.iDSorted)+'/simul_lumped_rain.txt'

        if not Path(os.path.join(workingDir,fileName)).exists():
            logging.error("The file " + os.path.join(workingDir,fileName) + " does not exist!")
            return None

        with open(os.path.join(workingDir,fileName), newline = '') as fileID2:
            data_reader = csv.reader(fileID2, delimiter='\t')
            list_data = []
            i=0
            for raw in data_reader:
                if i>1:
                    list_data.append(raw)
                i += 1
        matrixData = np.array(list_data).astype("float")
        rainAll = np.zeros(len(matrixData))
        timeAll = np.zeros(len(matrixData))

        secondsInDay = 24*60*60
        prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
        prevDate -= tzDelta
        timeAll[0] = datetime.datetime.timestamp(prevDate)
        timeI = datetime.datetime.timestamp(self.dateBegin)
        timeF = datetime.datetime.timestamp(self.dateEnd)
        if(timeI<timeAll[0]):
            print("ERROR: The rain dates in simul_lumped_rain are not compatible with the beginning of the simulation !")
            print("Date read = ", prevDate)
            print("Starting date of the simulation = ", self.dateBegin)
            sys.exit()
        for i in range(1,len(matrixData)):
            currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            currDate -= tzDelta
            prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            diffDate = currDate - prevDate
            diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
            timeAll[i] = datetime.datetime.timestamp(currDate)
            # time[i] = time[i-1] + diffTimeInSeconds
            rainAll[i] = matrixData[i][6]
        # Check the compatibility of the time steps with the hydro simulation
        if(self.deltaT!=diffTimeInSeconds):
            print("ERROR: The last timestep in rain data does not coincide with the one expected!")
            print("Delta t read = ", diffTimeInSeconds)
            print("Delta t expected = ", self.deltaT)
            sys.exit()
        # Extract just the part of the rain contained in the simulation range
        condTime = (timeAll>=timeI) & (timeAll<=timeF)
        time = np.extract(condTime, timeAll)
        rain = np.extract(condTime, rainAll)

        # Test of the code good procedure -> to remove
        if(timeF!=time[-1]):
            print("ERROR: The last date in rain data does not coincide with the one expected!")
            print("Date timestamp read = ", time[-1])
            print("Date timestamp expected = ", self.dateEnd)
            sys.exit()
        # Save the time if it does not exist yet
        if(self.time is None):
            self.time=time
            print("Time didn't exist before, therefore it is save now according to rain data time serie!")

        elif not(np.array_equal(time,self.time)):
            print('Time arrays are not the same! Please check your answers.')

        self.myRain = rain
        # Unit conversion to [m^3/s]
        if(self.surfaceDrained==0):
            print("WARNING : surfaceDrained=0! It should not be the case to apply correctly this step. Please check your precedure and define its value!")
        rain = rain*10**(-3)*self.surfaceDrained*10**(6)/3600.0
        # Sum of the rain of all the inlets to get the total rain
        for iInlet in self.intletsObj:
            rain += self.intletsObj[iInlet].rain
        self.rain = rain

        return time


    def add_evap(self, workingDir, fileName=None, tzDelta=datetime.timedelta(hours=0)):
        """ This procedure
            - reads: the time, evapotranspiration in the evap file
            - saves: the evapotranspiration of the subbasin, sum of the evapotranspiration's inlets -> to correct with surface of the basin
            - returns: the time array read.
            - Variables modified: self.evap, self.myEvap
        """
        # Reading and saving the evap's basin
        if(fileName is None):
            fileName = 'Subbasin_'+str(self.iDSorted)+'/simul_lumped_evap.txt'

        with open(workingDir+fileName, newline = '') as fileID2:
            data_reader = csv.reader(fileID2, delimiter='\t')
            list_data = []
            i=0
            for raw in data_reader:
                if i>1:
                    list_data.append(raw)
                i += 1
        matrixData = np.array(list_data).astype("float")
        evapAll = np.zeros(len(matrixData))
        timeAll = np.zeros(len(matrixData))

        secondsInDay = 24*60*60
        prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
        prevDate -= tzDelta
        timeAll[0] = datetime.datetime.timestamp(prevDate)
        timeI = datetime.datetime.timestamp(self.dateBegin)
        timeF = datetime.datetime.timestamp(self.dateEnd)
        # Check the coherence between the first date in rain and the simualtion range. It can have more rain data than simulation but not the contrary!
        if(timeI<time[0]):
            print("ERROR: The rain dates in simul_lumped_rain are not compatible with the beginning of the simulation !")
            print("Date read = ", prevDate)
            print("Starting date of the simulation = ", self.dateBegin)
            sys.exit()

        for i in range(1,len(matrixData)):
            currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            currDate -= tzDelta
            prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            diffDate = currDate - prevDate
            diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
            timeAll[i] = datetime.datetime.timestamp(currDate)
            # time[i] = time[i-1] + diffTimeInSeconds
            evapAll[i] = matrixData[i][6]
        # Check the compatibility of the time steps with the hydro simulation
        if(self.deltaT!=diffTimeInSeconds):
            print("ERROR: The last timestep in rain data does not coincide with the one expected!")
            print("Delta t read = ", diffTimeInSeconds)
            print("Delta t expected = ", self.deltaT)
            sys.exit()

        # Extract just the part of the rain contained in the simulation range
        condTime = (timeAll>=timeI) & (timeAll<=timeF)
        time = np.extract(condTime, timeAll)
        evap = np.extract(condTime, evapAll)

        # Test of the code good procedure -> to remove
        if(timeF!=time[-1]):
            print("ERROR: The last date in rain data does not coincide with the one expected!")
            print("Date read = ", time[-1])
            print("Date expected = ", self.dateEnd)
            sys.exit()
        # Save the time if it does not exist yet
        if(self.time is None):
            self.time=time
            print("Time didn't exist before, therefore it is saved now according to rain data time serie!")
        elif not(np.array_equal(time,self.time)):
            print('Time arrays are not the same! Please check your answers.')

        self.myEvap = evap

        # Unit conversion to [m^3/s]
        if(self.surfaceDrained==0):
            print("WARNING : surfaceDrained=0! It should not be the case to apply correctly this step. Please check your precedure and define its value!")
        evap = evap*10**(-3)*self.surfaceDrained*10**(6)/3600.0
        # Sum of the evap of all the inlets to get the total evap
        for i in range(len(self.intletsObj)):
            evap += self.intletsObj[i].evap
        self.evap = evap

        return time


    def add_temp(self, workingDir, fileName=None, tzDelta=datetime.timedelta(hours=0)):
        """ This procedure
            - reads: the time, mean temperature in a day in the Temp file
            - saves: the temperatures of the subbasin
            - returns: the time array read.
            - Variables modified: self.myTemp
        """
        # Reading and saving the temperature's basin
        if(fileName is None):
            fileName = 'Subbasin_'+str(self.iDSorted)+'/simul_lumped_Temp.txt'

        with open(workingDir+fileName, newline = '') as fileID2:
            data_reader = csv.reader(fileID2, delimiter='\t')
            list_data = []
            i=0
            for raw in data_reader:
                if i>1:
                    list_data.append(raw)
                i += 1
        matrixData = np.array(list_data).astype("float")
        temp = np.zeros(len(matrixData))
        time = np.zeros(len(matrixData))

        secondsInDay = 24*60*60
        prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), minute=int(matrixData[0][4]), second=int(matrixData[0][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
        prevDate -= tzDelta
        if(self.dateBegin!=prevDate):
            print("ERROR: The first date in temperature data does not coincide with the one expected!")
            print("Date read = ", prevDate)
            print("Date expected = ", self.dateBegin)
            sys.exit()
        time[0] = datetime.datetime.timestamp(prevDate)
        for i in range(1,len(matrixData)):
            currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=int(matrixData[i][3]), minute=int(matrixData[i][4]), second=int(matrixData[i][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            currDate -= tzDelta
            prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),  microsecond=0, tzinfo=datetime.timezone.utc)
            prevDate -= tzDelta
            diffDate = currDate - prevDate
            diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
            time[i] = datetime.datetime.timestamp(currDate)
            # time[i] = time[i-1] + diffTimeInSeconds
            temp[i] = matrixData[i][6]
        if(self.dateEnd!=currDate):
            print("ERROR: The last date in temperature data does not coincide with the one expected!")
            print("Date read = ", currDate)
            print("Date expected = ", self.dateEnd)
            sys.exit()
        if(self.deltaT!=diffTimeInSeconds):
            print("ERROR: The last timestep in temperature data does not coincide with the one expected!")
            print("Delta t read = ", diffTimeInSeconds)
            print("Delta t expected = ", self.deltaT)
            sys.exit()
        if(self.time is None):
            self.time = time
        elif not(np.array_equal(time,self.time)):
            print('Time arrays are not the same! Please check your answers.')
            sys.exit()
        self.myTemp = temp

        return time


    def read_dbfFile(self, fileName):
        dbfDict = DBF(fileName, load=True)
        return dbfDict


    def add_hyeto(self, workingDir, hyetoDict):
        """Add hyetographs to the subbasin
            TO DO: Adapt the code to find automatically the .dbf files. E.G. when data are read in NetCDF files.
        """
        fileName  = Path(workingDir) / ('Subbasin_'  +str(self.iDSorted)) / 'simul_rain_geom.vec.dbf'
        fileName2 = Path(workingDir) / ('Subbasin_'  +str(self.iDSorted)) /'/simul_geom.vec.dbf'

        if(fileName.exists()):
            dbDict = self.read_dbfFile(str(fileName))
            for i in range(len(dbDict.records)):
                idHyeto = int(dbDict.records[i]['data'])
                # idMyHyeto = hyetoDict['Ordered To Nb'][idHyeto]
                self.myHyetoDict[idHyeto] = hyetoDict['Hyetos'][idHyeto]
        elif(fileName2.exists()):
            dbDict = self.read_dbfFile(str(fileName2))
            for i in range(len(dbDict.records)):
                idHyeto = int(dbDict.records[i]['data'])
                # idMyHyeto = hyetoDict['Ordered To Nb'][idHyeto]
                self.myHyetoDict[idHyeto] = hyetoDict['Hyetos'][idHyeto]
        else:
            print("WARNING: No dbf file")


    def plot(self, workingDir, plotRaw=False, axis="Hours", yAdd=[], yAddName=[], rangeData=[], deltaMajorTicks=12.0*3600.0, deltaMinorTicks=3600.0, tzPlot=0):
        """ This procedure plots:
        - the inlets: in color chosen randomly by matplotlib
        - the outlet: in black solid line
        - the raw outlet: in black dashed line
        """

        if(self.model==cst.tom_UH or self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH or self.model==cst.tom_GR4 or
           self.model==cst.tom_HBV or self.model==cst.tom_SAC_SMA or self.model==cst.tom_NAM or self.model==cst.tom_SAC_SMA_LROF):
            # x = self.time/3600.0
            if(axis=="Hours"):
                x = (self.time[:]-self.time[0])/3600.0
            else:
                tzDelta = datetime.timedelta(seconds=tzPlot*3600.0)
                timeDelayDelta = datetime.timedelta(seconds=self.timeDelay)
                beginDate = datetime.datetime.fromtimestamp(self.time[0], tz=datetime.timezone.utc)+tzDelta-timeDelayDelta
                endDate = datetime.datetime.fromtimestamp(self.time[-1], tz=datetime.timezone.utc)+tzDelta-timeDelayDelta
                dt = self.time[1]-self.time[0]
                time_delta = datetime.timedelta(seconds=dt)
                if(rangeData==[]):
                    rangeData = [beginDate,endDate]
                x_date = drange(beginDate, endDate+time_delta, time_delta)

            font11 = FontProperties()
            font11.set_family('serif')
            font11.set_name('Euclid')
            font11.set_size(11)

            font14 = FontProperties()
            font14.set_family('serif')
            font14.set_name('Euclid')
            font14.set_size(14)

            # fig = plt.figure(figsize=(11.7,8.3))
            fig = plt.figure(figsize=(10.4,6.25))
            ax1 = plt.subplot(1,1,1)
            ax1.grid()
            if(axis=="Hours"):
                ax1.set_xlabel('Temps [h]', fontproperties=font11)
            else:
                ax1.set_xlabel('Dates (GMT+'+str(tzPlot)+')', fontproperties=font11)
            ax1.set_ylabel('Débits [m³/s]', fontproperties=font11)
            # fig.legend(loc="best")
            fig.legend()

            for iInlet in self.intletsObj:
                y = self.intletsObj[iInlet].get_outFlow_global(typeOutFlow="Net", whichOutFlow=iInlet)
                name = self.intletsObj[iInlet].name

                if(axis=="Hours"):
                    ax1.plot(x, y, label = name)
                else:
                    if(len(x_date)-1==len(y)):
                        # print("ERROR: dimension of dates 1 elements greater than data! This could be a problem induced by drange() ... To investigate...")
                        # toContinue = input("Do you still want to continue nonetheless? Y-[Yes] N-[No]: ")
                        logging.error("ERROR: dimension of dates 1 elements greater than data! This could be a problem induced by drange() ... To investigate...")
                        x_date = x_date[:-1]

                    ax1.plot_date(x_date, y, '-', label = name)

            if yAdd!=[]:
                # ########
                nbyAdd = np.shape(yAdd)[0]
                for i in range(nbyAdd):
                    y = yAdd[i][:]
                    name = yAddName[i]
                    if(axis=="Hours"):
                        ax1.plot(x, y, label = name)
                    else:
                        ax1.plot_date(x_date, y, '-', label = name)


            if(self.model==cst.tom_UH or self.model==cst.tom_GR4):
                # y = self.myHydro
                tmpHydro = []
                tmpHydro.append(np.zeros(len(self.myHydro)))
                index = math.floor(self.timeDelay/self.deltaT)
                if(index==0):
                    if(self.model==cst.tom_GR4):
                        tmpHydro = self.myHydro[:,0]*self.surfaceDrained/3.6
                    else:
                        tmpHydro[0] = self.myHydro*self.surfaceDrained/3.6
                elif(index<len(self.myHydro)):
                    if(self.model==cst.tom_GR4):
                        tmpHydro = self.myHydro[:,0]*self.surfaceDrained/3.6
                    else:
                        tmpHydro[0][index:] = self.myHydro[:-index]*self.surfaceDrained/3.6
                    # tmpHydro[index:] = self.myHydro[:-index]
            elif(self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH):
                tmpHydro = []
                for i in range(2):
                    tmpHydro.append(np.zeros(len(self.myHydro)))
                index = math.floor(self.timeDelay/self.deltaT)
                for i in range(2):
                    if(index==0):
                        tmpHydro[i] = self.myHydro[:,i]*self.surfaceDrained/3.6
                    elif(index<len(self.myHydro)):
                        tmpHydro[i][index:] = self.myHydro[:-index,i]*self.surfaceDrained/3.6


            myLabels = []
            if(self.model==cst.tom_UH):
                myLabels.append(self.name+' raw')
            elif(self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH):
                myLabels.append(self.name+' overland flow')
                myLabels.append(self.name+' interflows')

            for i in range(len(tmpHydro)):
                y = tmpHydro[i]
                if(axis=="Hours"):
                    ax1.plot(x, y, label = self.name)
                else:
                    ax1.plot_date(x_date, y, '-', label = self.name)

            if(axis=="Hours"):
                if(self.model==cst.tom_UH):
                    y = self.myHydro*self.surfaceDrained/3.6
                    if(axis=="Hours"):
                        ax1.plot(x, y,'--',label = self.name+' local')
                    else:
                        ax1.plot_date(x_date, y,'--',label = self.name+' local')
                elif(self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH):
                    for i in range(2):
                        y = self.myHydro[:,i]*self.surfaceDrained/3.6
                        if(axis=="Hours"):
                            ax1.plot(x, y,'--',label = self.name+ myLabels[i]+' raw')
                        else:
                            ax1.plot_date(x_date, y,'--',label = self.name+ myLabels[i]+' raw')



            y = self.get_outFlow_global(typeOutFlow="Net")
            # plt.plot(x, y, label = 'Outlet '+self.name, color='k')
            if(axis=="Hours"):
                ax1.plot(x, y, label = 'Outlet', color='k')
            else:
                ax1.plot_date(x_date, y, '-', label = 'Outlet', color='k')

            if(plotRaw):
                y = self.get_outFlow_global(typeOutFlow="Raw")
                if(axis=="Hours"):
                    ax1.plot(x, y, '--', label = 'Outlet '+self.name+' Raw', color='k')
                else:
                    ax1.plot_date(x_date, y, '--', label = 'Outlet '+self.name+' Raw', color='k')
                ax1.set_title(self.name + " Hydrogrammes écrêtés", fontproperties=font14)
            else:
                ax1.set_title(self.name + " Hydrogrammes", fontproperties=font14)
            if(axis=="Hours"):
                ax1.set_xlim(x[0], x[-1])
            else:
                ax1.set_xlim(rangeData[0], rangeData[1]-time_delta)

            for label in ax1.get_xticklabels():
                label.set_rotation(30)
                label.set_horizontalalignment('right')
            ax1.tick_params(axis='y',labelcolor='k')

            if(deltaMajorTicks>0):
                if(axis=="Datetime"):
                    majorTicks = HourLocator(interval=math.floor(deltaMajorTicks/3600),tz=datetime.timezone.utc)
                    ax1.xaxis.set_major_locator(majorTicks)
                    ax1.grid(which='major', alpha=1.0)


                if(deltaMinorTicks>0):
                    if(axis=="Datetime"):
                        ax1.minorticks_on()
                        minorTicks = MicrosecondLocator(interval=deltaMinorTicks*1E6,tz=datetime.timezone.utc)
                        ax1.xaxis.set_minor_locator(minorTicks)
                        ax1.grid(which='minor', alpha=0.2)
            else:
                ax1.grid()


            # fig.legend(prop=font11,loc="best")
            fig.legend(prop=font11)


            if(plotRaw):
                plt.savefig(os.path.join(workingDir,'PostProcess/QT_HydroEcrete_'+self.name+'.pdf'))
            else:
                plt.savefig(workingDir+'PostProcess/QT_Hydro_'+self.name+'.pdf')
            # if(plotRaw):
            #     plt.savefig(workingDir+'QT_HydroEcrete_'+self.name+'.pdf')
            # else:
            #     plt.savefig(workingDir+'QT_Hydro_'+self.name+'.pdf')

        elif(self.model==cst.tom_VHM):
            print("ERROR: the plot for VHM is not implemented yet!")
            sys.exit()

        else:
            print("ERROR: the plot for this option is not implemented yet!")
            sys.exit()


    def plot_myBasin(self, Measures=None, rangeData=[], yrangeRain=[], yrangeData=[], factor=1.5, graph_title='', withEvap=False, writeFile='', withCt=False, figure=None):
        "This procedure plots its own hydrographs and hyetographs"

        # Determine the number of elements according to the model chosen
        if(self.model==cst.tom_UH):
            nbElements = 1
            lastElement = 0
        elif(self.model==cst.tom_VHM):
            nbElements = 4
            lastElement = 0
        elif(self.model==cst.tom_GR4):
            nbElements = 1
            lastElement = 0
        elif(self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH):
            nbElements = 3
            lastElement = 0
        else:
            nbElements = 1
            lastElement = 0

        # Construction of the list of element to plot on the main hydrograph
        myOutFlow = self.outFlow_global
        tmpSum = np.zeros(len(myOutFlow)-lastElement)
        y = np.zeros((len(myOutFlow)-lastElement,nbElements))
        if(self.model==cst.tom_UH):
            y[:,0] = self.myHydro[:]*self.surfaceDrained/3.6
        elif(self.model==cst.tom_VHM or self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH):
            for i in range(nbElements-1+lastElement):
                y[:,i] = self.myHydro[:,i]*self.surfaceDrained/3.6
                tmpSum += self.myHydro[:,i]*self.surfaceDrained/3.6
            y[:,-1] = tmpSum
        elif(self.model==cst.tom_GR4 or self.model==cst.tom_HBV or
             self.model==cst.tom_SAC_SMA or self.model==cst.tom_NAM or self.model==cst.tom_SAC_SMA_LROF):
            y[:,0] = self.myHydro[:,0]*self.surfaceDrained/3.6
        else:
            print("ERROR: this model was not implemented yet!")
            sys.exit()

        # Add the measures if available
        if(Measures is not None):
            myMeasure = Measures.myHydro

        # label on x-axis
        x_title = "dates"

        # label on y-axis
        y_titles = []
        if(self.model==cst.tom_VHM):
            y_titles.append("Overland flow")
            y_titles.append("Interflow")
            y_titles.append("Baseflow")
            y_titles.append("Total")
        elif(self.model==cst.tom_UH):
            y_titles.append('')
        elif(self.model==cst.tom_GR4):
            y_titles.append("GR4 flow")
        elif(self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH):
            y_titles.append("Overland flow")
            y_titles.append("Interflow")
            y_titles.append("Total")
        else:
            y_titles.append("Total")

        if(Measures is not None):
            y_titles.append("Measurement")

        # Colors of the plot
        myColors = []
        for i in range(nbElements):
            myColors.append('')
        if(Measures is not None):
            myColors.append('k')

        # Type of trait in the plot
        myTraits = []
        for i in range(nbElements):
            myTraits.append('-')
        if(Measures is not None):
            myTraits.append('--')

        # The additional plots to add
        # Evapotranspiration
        z = []
        y_labelAddPlot = []
        haveUpperPlot = False
        nbAddPlot = 0
        if(withEvap):
            z.append(self.myEvap)
            y_labelAddPlot.append('Evapotranpiration [mm/h]')
            haveUpperPlot = True
            nbAddPlot += 1
        if(withCt):
            myCt = self.compute_runnoff_Ct_coeffs()
            z.append(myCt)
            y_labelAddPlot.append('$C_t$ [-]')
            haveUpperPlot = True
            nbAddPlot += 1

        # Graph title:
        if(graph_title==''):
            if(self.name is not None):
                graph_title = "Hydrogramme de " + self.name

        # Range to consider
        if(rangeData==[]):
            rangeData = [self.dateBegin, self.dateEnd]
        if(factor!=1.5 and yrangeRain!=[]):
            print("WARNING: factor and range cannot be specified at the same time. Only factor will be taken into account.")
            yrangeRain=[]
        if(factor!=1.5 and yrangeData!=[]):
            print("WARNING: factor and range cannot be specified at the same time. Only factor will be taken into account.")
            yrangeData=[]

        if(writeFile!=""):
            writeFile = writeFile + "Subbasin_hydro"

        # Check if the intervals is too wild to impose the deltaMajorTicks
        timeInterval = self.dateEnd-self.dateBegin
        if timeInterval.days < 100:
            deltaMajorTicks = 86400
            deltaMinorTicks = 3600
        else:
            deltaMajorTicks = -1
            deltaMinorTicks = -1

        # Launch the procedure
        if(Measures is not None):
            ph.plot_hydro(nbElements,y,self.myRain,x_title=x_title,y_titles='', beginDate=self.dateBegin,endDate=self.dateEnd,
                        dt=self.deltaT,graph_title=graph_title,y_labels=y_titles,rangeData=rangeData,y_rain_range=yrangeRain,y_data_range=yrangeData,factor_RH=factor,myColors=myColors,typeOfTraits=myTraits,
                        measures=myMeasure,beginDateMeasure=Measures.dateBegin, endDateMeasure=Measures.dateEnd, dtMeasure=Measures.deltaT,
                        upperPlot=haveUpperPlot,nbAddPlot=nbAddPlot,z=z,y_labelAddPlot=y_labelAddPlot,writeFile=writeFile,deltaMajorTicks=deltaMajorTicks,deltaMinorTicks=deltaMinorTicks, figure=figure)
        else:
            ph.plot_hydro(nbElements,y,self.myRain,x_title=x_title,y_titles='', beginDate=self.dateBegin,endDate=self.dateEnd,
                        dt=self.deltaT,graph_title=graph_title,y_labels=y_titles,rangeData=rangeData,y_rain_range=yrangeRain,y_data_range=yrangeData,myColors=myColors,typeOfTraits=myTraits,
                        upperPlot=haveUpperPlot,nbAddPlot=nbAddPlot,z=z,y_labelAddPlot=y_labelAddPlot,writeFile=writeFile,deltaMajorTicks=deltaMajorTicks,deltaMinorTicks=deltaMinorTicks, figure=figure)

        # x = self.time/3600.0    # [h]

        # y1 = self.myHydro
        # y2 = self.rain

        # # Figure Rain on a first y axis
        # fig,ax1=plt.subplots()
        # ax1.set_xlabel('Temps [h]')
        # ax1.set_ylabel('Débits [m³/s]',color='k') #Color express in %RGB: (1,1,1)
        # ax1.set_ylim(0, self.myHydro.max()*2)
        # # ax1.hist(data1,color=(0,0,1),edgecolor='black',linewidth=1.2)
        # ax1.plot(x,y1, color='k')
        # ax1.tick_params(axis='y',labelcolor='k')

        # # Figure Hydro on a second y axis
        # ax2=ax1.twinx()
        # ax2.set_ylabel('Précipitations [mm/h]',color='b')
        # ax2.set_ylim(self.rain.max()*3, 0)
        # ax2.plot(x,y2,color='b')
        # ax2.fill_between(x, y2, 0, color='b')
        # ax2.tick_params(axis='y',labelcolor='b')
        # fig.tight_layout()


    def plot_outlet(self, Measures=None, rangeData=[], yrangeRain=[], yrangeData=[], ylabel=[],addData=[], dt_addData=[], beginDates_addData=[], endDates_addData=[],\
                    label_addData=[], color_addData=[],factor=1.5, graph_title='', withEvap=False, writeFile='', withDelay=True, deltaMajorTicks=-1,deltaMinorTicks=-1, tzPlot=0, Measure_unit="m3/s", addTable=False, figure=None):
        "This procedure plots its own hydrographs and hyetographs"

        # Determine the number of elements according to the model chosen
        if(self.model==cst.tom_UH):
            nbElements = 1    ###
            # nbElements = 2  ###
            lastElement = 1
        elif(self.model==cst.tom_VHM):
            # nbElements = 4
            nbElements = 1
            lastElement = 0
        elif(self.model==cst.tom_GR4):
            nbElements = 1
            lastElement = 0
        elif(self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH):
            # nbElements = 3
            nbElements = 1
            lastElement = 0
        else:
            nbElements = 1
            lastElement = 0


        # Take into account any additionnal data given and add it to plot
        nbCol_addData = 0
        if(addData!=[]):
            shape_addData = np.shape(addData)
            if(len(shape_addData)==1):
                if(dt_addData==[]):
                    nbCol_addData = 1
                    nbElements += nbCol_addData
                elif(type(addData[0])==list or type(addData[0])==np.ndarray):
                    nbCol_addData = len(addData)
                    nbElements = nbElements + nbCol_addData
                else:
                    nbCol_addData = 1
                    nbElements += nbCol_addData
            elif(len(shape_addData)==2):
                if(type(addData)==list):
                    nbCol_addData = len(addData)
                    nbElements = nbElements + nbCol_addData
                else:
                    nbCol_addData = np.shape(addData)[1]
                    nbElements = nbElements + nbCol_addData
            else:
                print("ERROR : the array additional data (addData) can only be a vector or a matrix!")
                print("Type of additional data = ", type(addData))
                print("Shape = ", shape_addData)
                print(addData)
                sys.exit()

            # nbElements = nbElements + nbCol_addData
            if(dt_addData!=[]):
                dt = []
                beginDate = []
                endDate = []
                dt.append(self.deltaT)
                beginDate.append(self.dateBegin+datetime.timedelta(hours=tzPlot))
                endDate.append(self.dateEnd+datetime.timedelta(hours=tzPlot))
                for i in range(nbCol_addData):
                    dt.append(dt_addData[i])
                    beginDate.append(beginDates_addData[i]+datetime.timedelta(hours=tzPlot))
                    endDate.append(endDates_addData[i]+datetime.timedelta(hours=tzPlot))
            else:
                dt = [self.deltaT]
                beginDate = [self.dateBegin+datetime.timedelta(hours=tzPlot)]
                endDate = [self.dateEnd+datetime.timedelta(hours=tzPlot)]

        else:
            dt = [self.deltaT]
            beginDate = [self.dateBegin+datetime.timedelta(hours=tzPlot)]
            endDate = [self.dateEnd+datetime.timedelta(hours=tzPlot)]


        # Conversion rain from [m³/s] to [mm/h]
        rain = self.rain/self.surfaceDrainedHydro*3.6

        # Construction of the list of element to plot on the main hydrograph
        myOutFlow = self.outFlow_global
        tmpSum = np.zeros(len(myOutFlow)-lastElement)
        # y = np.zeros((len(self.outFlow)-lastElement,nbElements))
        y = []
        if(self.model==cst.tom_UH or self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH or
           cst.tom_GR4 or cst.tom_HBV or cst.tom_SAC_SMA or cst.tom_NAM or self.model==cst.tom_SAC_SMA_LROF):
            if(withDelay):
                # y[:,0] = self.outFlow[:-1]
                y.append(myOutFlow[:])
            else:
                tmpSum = self.get_outFlow_noDelay()
                # y[:,0] = tmpSum[:-1]
                y.append(tmpSum[:])

            # cumul_rain = datt.cumul_data(self.rain,self.deltaT, self.deltaT)    ###
            # y[:,1] = cumul_rain[:-1]/cumul_rain[-1]*np.max(self.outFlow)    ###

            if nbCol_addData==1:
                # y[:,2] = addData    ###
                # y[:,1] = addData    ###
                # y.append(addData)    ###
                if(type(addData)==list):
                    y.append(addData[0])
                else:
                    y.append(addData[:,0])

            else:
                if(type(addData)==list):
                    for col in range(nbCol_addData):
                        # y[:,1+col] = addData[col]     ###
                        # y[:,2+col] = addData[:,col]     ###
                        y.append(addData[col])     ###
                elif(type(addData)==np.ndarray):
                    for col in range(nbCol_addData):
                        # y[:,1+col] = addData[:,col]     ###
                        # y[:,2+col] = addData[:,col]     ###
                        y.append(addData[:,col])     ###



        elif(self.model==cst.tom_VHM):
            print("ERROR : VHM not implemented yet! Please check the code")
            sys.exit()
            for i in range(nbElements-1+lastElement):
                y[:,i] = self.myHydro[:,i]
                tmpSum += self.myHydro[:,i]
            y[:,-1] = tmpSum
        elif(self.model==cst.tom_GR4):
            print("ERROR : GR4 not implemented yet! Please check the code")
            sys.exit()
            y[:,0] = self.outFlow[:,0]
        else:
            print("ERROR: this model was not implemented yet!")
            sys.exit()

        # Add the measures if available
        if(Measures!=None):
            if Measure_unit=="mm/h":
                myMeasure = Measures.myHydro*self.surfaceDrainedHydro/3.6
            else:
                myMeasure = Measures.myHydro

        # label on x-axis
        x_title = 'Dates (GMT+'+str(tzPlot)+')'

        # label on y-axis
        y_titles = []
        if(self.model==cst.tom_VHM):
            # y_titles.append("Overland flow")
            # y_titles.append("Interflow")
            # y_titles.append("Baseflow")
            # y_titles.append("Total")
            y_titles.append(_('Débits simulés'))
        elif(self.model==cst.tom_UH or self.model==cst.tom_2layers_linIF or self.model==cst.tom_2layers_UH or
             self.model==cst.tom_HBV or self.model==cst.tom_SAC_SMA or self.model==cst.tom_NAM, self.model==cst.tom_SAC_SMA_LROF):
            if(ylabel==[]):
                y_titles.append(_('Débits simulés'))
                # y_titles.append('Avec reconstruction Qout B. Vesdre')
                # y_titles.append('Avec Qout décrit par Le Soir au B. Vesdre')
                # y_titles.append('Débits nuls aux barrages')
                # avec Qout décrit par Le Soir B. Vesdre
                # y_titles.append('Débits décrits dans Le Soir')
                # y_titles.append('Cumulated rain')    ###
            else:
                y_titles.append(ylabel)

            # if(label_addData !=[]):
            #     for ii in label_addData :
            #         y_titles.append(ii)
                # y_titles.append(label_addData)

        elif(self.model==cst.tom_GR4):
            if(ylabel==[]):
                y_titles.append("GR4 flow")
            else:
                y_titles.append(ylabel)


        if(label_addData !=[]):
            for ii in label_addData :
                y_titles.append(ii)

        if(Measures is not None):
            # y_titles.append("Measures")
            y_titles.append("Measurement")
            # y_titles.append("Débits entrant reconstruits")

        # Colors of the plot
        myColors = []
        for i in range(nbElements):
            # myColors.append('')
            if(color_addData!=[]):
                if(i>=nbElements-nbCol_addData):
                    myColors.append(color_addData[i+nbCol_addData-nbElements])
                    # myColors.append(color_addData)
                else:
                    myColors.append('')
            else:
                myColors.append('')
        if(Measures is not None):
            myColors.append('k')

        # Type of trait in the plot
        myTraits = []
        for i in range(nbElements):
            myTraits.append('-')
        if(Measures is not None):
            myTraits.append('--')

        # The additional plots to add
        # Evapotranspiration
        z = []
        y_labelAddPlot = []
        haveUpperPlot = False
        if(withEvap):
            z.append(self.myEvap)
            y_labelAddPlot.append('Evapotranpiration [mm/h]')
            haveUpperPlot = True

        # Graph title:
        if(graph_title==''):
            if(self.name is not None):
                graph_title = "Hydrogramme de " + self.name

        # Range to consider
        if(rangeData==[]):
            rangeData = [self.dateBegin, self.dateEnd]
        if(factor!=1.5 and yrangeRain!=[]):
            print("WARNING: factor and range cannot be specified at the same time. Only factor will be taken into account.")
            yrangeRain=[]
        if(factor!=1.5 and yrangeData!=[]):
            print("WARNING: factor and range cannot be specified at the same time. Only factor will be taken into account.")
            yrangeData=[]

        if addTable:
            allSurfaces = [self.surfaceDrainedHydro]
            if Measures != None:
                surfaceMeasure = Measures.surfaceDrained
                if surfaceMeasure <=0:
                    surfaceMeasure = self.surfaceDrainedHydro
                addMeasfInTab=True
        else:
            allSurfaces = []
            surfaceMeasure=-1.0
            addMeasfInTab = False


        # Launch the procedure
        if(Measures is not None):
            ph.plot_hydro(nbElements,y,rain,x_title=x_title,y_titles='',beginDate=beginDate,endDate=endDate,
                        dt=dt,graph_title=graph_title,y_labels=y_titles,rangeData=rangeData,y_rain_range=yrangeRain,y_data_range=yrangeData,factor_RH=factor,myColors=myColors,typeOfTraits=myTraits,
                        measures=myMeasure,beginDateMeasure=Measures.dateBegin+datetime.timedelta(hours=tzPlot), endDateMeasure=Measures.dateEnd+datetime.timedelta(hours=tzPlot), dtMeasure=Measures.deltaT,
                        upperPlot=haveUpperPlot,nbAddPlot=1,z=z,y_labelAddPlot=y_labelAddPlot,writeFile=writeFile,deltaMajorTicks=deltaMajorTicks,deltaMinorTicks=deltaMinorTicks,
                        addTable=addTable,allSurfaces=allSurfaces,surfaceMeasure=surfaceMeasure,addMeasfInTab=addMeasfInTab,figure=figure)
        else:
            ph.plot_hydro(nbElements,y,rain,x_title=x_title,beginDate=beginDate,endDate=endDate,
                        dt=dt,graph_title=graph_title,y_labels=y_titles,rangeData=rangeData,y_rain_range=yrangeRain,y_data_range=yrangeData,myColors=myColors,typeOfTraits=myTraits,
                        upperPlot=haveUpperPlot,nbAddPlot=1,z=z,y_labelAddPlot=y_labelAddPlot,writeFile=writeFile,deltaMajorTicks=deltaMajorTicks,deltaMinorTicks=deltaMinorTicks,
                        addTable=addTable,allSurfaces=allSurfaces, figure=figure)


    def create_histo(self, time, hyeto):
        "Transform the hyeto data and its assiciated time in a histogram"
        size = len(hyeto)
        hyeto2 = np.zeros(size*2)
        time2  = np.zeros(size*2)
        for i in range(size):
            time2[i*2+1]  = time[i]
            hyeto2[i*2+1] = hyeto[i]

        time2[0]  = 0
        hyeto2[0] = hyeto2[1]
        for i in range(size-1):
            time2[i*2+2]    = time2[i*2+1]
            hyeto2[i*2+2] = hyeto2[i*2+3]

        plt.figure()
        plt.grid()
        plt.xlabel('temps [h]')
        plt.ylabel('intensité $[mm^3/s]$')
        plt.legend(loc="best")
        plt.title("Hyétogrammes")
        plt.plot(time2, hyeto2)
        plt.plot(time2, hyeto2)
        plt.plot(time2, hyeto2)
        plt.plot(time2, hyeto2)
        plt.xlim(0,time2[len(time2)-1])


    def read_myMainCharacteristics(self, workingDir:str, fileNameList:list=[]):
        """ This procedure read the main characteristics of the subbasin and hydro subbasin
            TO COMPLETE ...
        """
        if fileNameList==[]:
            fileName = "Subbasin_" + str(self.iDSorted) + "/" + "simul_subbasin.avrg_caractSubBasin"
            fileNameHydro = "Subbasin_" + str(self.iDSorted) + "/" + "simul_subbasin.avrg_caractWholeHydroSubBasin"
        else:
            assert len(fileNameList) == 2, ("If the fileNameList provided, it must be dimension 2")
            fileName = fileNameList[0]
            fileNameHydro = fileNameList[1]

        filename = Path(workingDir) / fileName
        if filename.exists():

            with open(filename, newline = '') as fileID2:
                data_reader = csv.reader(fileID2, delimiter='\t')
                list_data = []
                i=0
                for raw in data_reader:
                    if i>0:
                        list_data.append(raw)
                    i += 1

            tmp = ''
            for i in range(len(list_data)):
                if(list_data[i][0][:4]=="Area"):
                    tmp = list_data[i][0].split()
                    self.surfaceDrained = float(tmp[1].split("[")[0])
                    self.mainCharactDict["Area"] = {}
                    self.mainCharactDict["Area"]["value"] = self.surfaceDrained
                    self.mainCharactDict["Area"]["unit"] = "["+tmp[1].split("[")[1]
                elif(list_data[i][0][:9]=="Perimeter"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDict["Perimeter"] = {}
                    self.mainCharactDict["Perimeter"]["value"] = float(tmp[1].split("[")[0])
                    self.mainCharactDict["Perimeter"]["unit"] = "["+tmp[1].split("[")[1]
                elif(list_data[i][0][:13]=="Average slope"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDict["Average slope"] = {}
                    self.mainCharactDict["Average slope"]["value"] = float(tmp[2].split("[")[0])
                    self.mainCharactDict["Average slope"]["unit"] = "["+tmp[2].split("[")[1]
                elif(list_data[i][0][:35]=="Compactness coefficient (Gravelius)"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDict["Compactness coefficient (Gravelius)"] = {}
                    self.mainCharactDict["Compactness coefficient (Gravelius)"]["value"] = float(tmp[3].split("[")[0])
                    self.mainCharactDict["Compactness coefficient (Gravelius)"]["unit"] = "[-]"
                elif(list_data[i][0][:12]=="Max lag time"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDict["Max lag time"] = {}
                    self.mainCharactDict["Max lag time"]["value"] = float(tmp[3].split("[")[0])
                    self.mainCharactDict["Max lag time"]["unit"] = "["+tmp[3].split("[")[1]
                elif(list_data[i][0][:12] == "Min lag time"):
                    tmp = list_data[i][0].split()
                    self.timeDelay = float(tmp[3].split("[")[0])
                    self.mainCharactDict["Min lag time"] = {}
                    self.mainCharactDict["Min lag time"]["value"] = float(tmp[3].split("[")[0])
                    self.mainCharactDict["Min lag time"]["unit"] = "["+tmp[3].split("[")[1]
                elif(list_data[i][0][:12]=="Max altitude"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDict["Max altitude"] = {}
                    self.mainCharactDict["Max altitude"]["value"] = float(tmp[2].split("[")[0])
                    self.mainCharactDict["Max altitude"]["unit"] = "["+tmp[2].split("[")[1]
                elif(list_data[i][0][:12]=="Min altitude"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDict["Min altitude"] = {}
                    self.mainCharactDict["Min altitude"]["value"] = float(tmp[2].split("[")[0])
                    self.mainCharactDict["Min altitude"]["unit"] = "["+tmp[2].split("[")[1]
                elif(list_data[i][0][:21]=="Fraction of landuse n"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDict["Fraction of landuse n "+tmp[4]] = {}
                    self.mainCharactDict["Fraction of landuse n "+tmp[4]]["value"] = float(tmp[5].split("[")[0])
                    self.mainCharactDict["Fraction of landuse n "+tmp[4]]["unit"] = "["+tmp[5].split("[")[1]
        else:
            logging.error(f"File {filename} does not exist. Cannot read averaged characteristics.")


        data_reader = None
        list_data = []
        # fileName  = "/Subbasin_" + str(self.iDSorted) + "/" + "simul_subbasin.avrg_caractWholeHydroSubBasin"

        fileNameHydro = Path(workingDir) / fileNameHydro
        if fileNameHydro.exists():
            with open(fileNameHydro, newline = '') as fileID2:
                data_reader = csv.reader(fileID2, delimiter='\t')
                list_data = []
                i=0
                for raw in data_reader:
                    if i>0:
                        list_data.append(raw)
                    i += 1

            tmp = ''
            for i in range(len(list_data)):
                if(list_data[i][0][:4]=="Area"):
                    tmp = list_data[i][0].split()
                    self.surfaceDrainedHydro = float(tmp[1].split("[")[0])
                    self.mainCharactDictWholeHydro["Area"] = {}
                    self.mainCharactDictWholeHydro["Area"]["value"] = self.surfaceDrainedHydro
                    self.mainCharactDictWholeHydro["Area"]["unit"] = "["+tmp[1].split("[")[1]
                elif(list_data[i][0][:9]=="Perimeter"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDictWholeHydro["Perimeter"] = {}
                    self.mainCharactDictWholeHydro["Perimeter"]["value"] = float(tmp[1].split("[")[0])
                    self.mainCharactDictWholeHydro["Perimeter"]["unit"] = "["+tmp[1].split("[")[1]
                elif(list_data[i][0][:13]=="Average slope"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDictWholeHydro["Average slope"] = {}
                    self.mainCharactDictWholeHydro["Average slope"]["value"] = float(tmp[2].split("[")[0])
                    self.mainCharactDictWholeHydro["Average slope"]["unit"] = "["+tmp[2].split("[")[1]
                elif(list_data[i][0][:35]=="Compactness coefficient (Gravelius)"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDictWholeHydro["Compactness coefficient (Gravelius)"] = {}
                    self.mainCharactDictWholeHydro["Compactness coefficient (Gravelius)"]["value"] = float(tmp[3].split("[")[0])
                    self.mainCharactDictWholeHydro["Compactness coefficient (Gravelius)"]["unit"] = "[-]"
                elif(list_data[i][0][:12]=="Max lag time"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDictWholeHydro["Max lag time"] = {}
                    self.mainCharactDictWholeHydro["Max lag time"]["value"] = float(tmp[3].split("[")[0])
                    self.mainCharactDictWholeHydro["Max lag time"]["unit"] = "["+tmp[3].split("[")[1]
                elif(list_data[i][0][:12] == "Min lag time"):
                    tmp = list_data[i][0].split()
                    self.timeDelay = float(tmp[3].split("[")[0])
                    self.mainCharactDictWholeHydro["Min lag time"] = {}
                    self.mainCharactDictWholeHydro["Min lag time"]["value"] = float(tmp[3].split("[")[0])
                    self.mainCharactDictWholeHydro["Min lag time"]["unit"] = "["+tmp[3].split("[")[1]
                elif(list_data[i][0][:12]=="Max altitude"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDictWholeHydro["Max altitude"] = {}
                    self.mainCharactDictWholeHydro["Max altitude"]["value"] = float(tmp[2].split("[")[0])
                    self.mainCharactDictWholeHydro["Max altitude"]["unit"] = "["+tmp[2].split("[")[1]
                elif(list_data[i][0][:12]=="Min altitude"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDictWholeHydro["Min altitude"] = {}
                    self.mainCharactDictWholeHydro["Min altitude"]["value"] = float(tmp[2].split("[")[0])
                    self.mainCharactDictWholeHydro["Min altitude"]["unit"] = "["+tmp[2].split("[")[1]
                elif(list_data[i][0][:21]=="Fraction of landuse n"):
                    tmp = list_data[i][0].split()
                    self.mainCharactDictWholeHydro["Fraction of landuse n "+tmp[4]] = {}
                    self.mainCharactDictWholeHydro["Fraction of landuse n "+tmp[4]]["value"] = float(tmp[5].split("[")[0])
                    self.mainCharactDictWholeHydro["Fraction of landuse n "+tmp[4]]["unit"] = "["+tmp[5].split("[")[1]

        else:
            logging.error(f"File {fileNameHydro} does not exist. Cannot read averaged characteristics of the whole hydro subbasin.")


    def get_flood(self, path='', check_coherence=False):

        if(path==''):
            path = self.fileNameRead

        paramFile = Wolf_Param(to_read=False,toShow=False)
        paramFile.ReadFile(path +'simul_flood.out.param')

        nbFloods = int(paramFile.myparams['Floods characteristics']['nb'][key_Param.VALUE])
        dt = float(paramFile.myparams['Floods characteristics']['dt'][key_Param.VALUE])

        filePre = "simul_flood"
        floodData = []
        dateMask = []
        myOutFlow = self.outFlow_global
        mask = np.full((len(myOutFlow)), False, dtype=bool)
        j_saved = 0
        for i in range(nbFloods):
            floodData.append([])
            fileName = filePre + str(i+1) + ".dat"
            floodData[i] = rd.read_bin(path,fileName)
            dateMask.append([])
            # dateMask[i].append(datetime.datetime(year=int(floodData[i][0][2]), month=int(floodData[i][0][1]), day=int(floodData[i][0][0]), hour=int(floodData[i][0][3]), minute=int(floodData[i][0][4]), second=int(floodData[i][0][5]),  microsecond=0, tzinfo=datetime.timezone.utc))
            # dateMask[i].append(datetime.datetime(year=int(floodData[i][-1][2]), month=int(floodData[i][-1][1]), day=int(floodData[i][-1][0]), hour=int(floodData[i][-1][3]), minute=int(floodData[i][-1][4]), second=int(floodData[i][-1][5]),  microsecond=0, tzinfo=datetime.timezone.utc))
            tStart = datetime.datetime.timestamp(datetime.datetime(year=int(floodData[i][0][2]), month=int(floodData[i][0][1]), day=int(floodData[i][0][0]), hour=int(floodData[i][0][3]), minute=int(floodData[i][0][4]), second=int(floodData[i][0][5]),  microsecond=0, tzinfo=datetime.timezone.utc))
            nbElements = len(floodData[i])
            for j in range(j_saved,len(myOutFlow)):
                if(self.time[j]>=tStart):
                    mask[j:j+nbElements] = np.full(nbElements, True, dtype=bool)
                    j_saved = j
                    break

        effFlood = np.ma.array(myOutFlow,mask=mask)

        return effFlood



    def get_Nash_Flood(self, measures, tMeasures, dateBegin=None, dateEnd=None, path=''):

        if(dateBegin is None):
            dateBegin = self.dateBegin
        if(dateEnd is None):
            dateEnd = self.dateEnd
        if(path==''):
            path = self.fileNameRead

        effFlood = self.get_flood(path=path)
        Nash = datt.evaluate_Nash(effFlood.data, self.time, measures, tMeasures, dateBegin, dateEnd, mask=effFlood.mask)

        return Nash



    def get_outFlow(self, typeOutFlow:str="Net", unit:str='m3/s', whichOutFlow="", lag:float=0.0):

        if lag < 0.0:
            logging.error("TimeDelay difference cannot be negative for a SubBasin!!")
            logging.warning("Therefore, lag will be imposed to zero! This might create some mistakes!")
            lag = 0.0

        myOutFlow = np.zeros(len(self.myHydro),dtype=ct.c_double, order='F')
        index = math.floor(lag/(self.time[1]-self.time[0]))
        nameOut = list(self._outFlow.items())[0][0]
        if whichOutFlow!="" and whichOutFlow!=nameOut:
            logging.error("ERROR : the key argument of the ouFlow is not the same of the one in this SubBasin!")
            logging.error("Its original time will be applied ")
        curOutFlow = self._outFlow[nameOut][typeOutFlow]

        if(index==0):
            myOutFlow = curOutFlow.copy()
        elif(index<len(myOutFlow)):
            myOutFlow[index:] = curOutFlow[:-index].copy()
        else:
            logging.error("Warning: the simulation time is not long enough for this subbasin to be taken into account")
            logging.error("Error informations : ")
            logging.error("Function name : get_outFlow_noDelay()")
            logging.error("index = " + str(index))
            logging.error("len(myOutFlow) = " + str(len(myOutFlow)))
            logging.error("Lag = " + str(lag))
            return myOutFlow


        if unit=='mm/h':
            myOutFlow *= 3.6/self.surfaceDrainedHydro

        return myOutFlow


    def get_outFlow_at_time(self, time:datetime.datetime, typeOutFlow:str="Net", unit:str='m3/s', whichOutFlow="", lag:float=0.0):
        if time.tzname() != "UTC":
            logging.warning(f"Time {time} is not in UTC! Be aware that the time will keep the time zone you defined !")

        return self.get_outFlow(typeOutFlow=typeOutFlow, unit=unit, whichOutFlow=whichOutFlow, lag=lag)[np.where(self.time==time.timestamp())][0]


    def get_inlets(self, unit:str='m3/s', lag:float=0.0):

        if lag < 0.0:
            logging.error("TimeDelay difference cannot be negative for a SubBasin!!")
            logging.warning("Therefore, lag will be imposed to zero! This might create some mistakes!")
            lag = 0.0

        myInlet = np.zeros(len(self.myHydro),dtype=ct.c_double, order='F')
        index = math.floor(lag/(self.time[1]-self.time[0]))

        if(index==0):
            myInlet = self.inlets.copy()
        elif(index<len(myInlet)):
            myInlet[index:] = self.inlets[:-index].copy()
        else:
            logging.error("Warning: the simulation time is not long enough for this subbasin to be taken into account")
            logging.error("Error informations : ")
            logging.error("Function name : get_outFlow_noDelay()")
            logging.error("index = " + str(index))
            logging.error("len(myOutFlow) = " + str(len(myInlet)))
            logging.error("Lag = " + str(lag))
            return myInlet

        if unit=='mm/h':
            myInlet *= 3.6/self.surfaceDrainedHydro

        return myInlet


    def convert_data_global_to_local(self, dataGlob):

        dataLoc = np.zeros(len(dataGlob))

        myIndex = math.floor(self.timeDelay/(self.time[1]-self.time[0]))
        if(myIndex==0):
            dataLoc = dataGlob[:]
        elif(myIndex<len(dataLoc)):
            dataLoc[:-myIndex] = dataGlob[myIndex:]
        else:
            print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
            print("Error informations : ")
            print("Function name : convert_data_global_to_local()")
            print("index = ", myIndex)
            print("len(dataLoc) = ", len(dataLoc))
            print("self.timeDelay = ", self.timeDelay)
            sys.exit()

        return dataLoc



    def compute_runnoff_Ct_coeffs(self, method=-1):

        subBasinName = 'Subbasin_' + str(self.iDSorted) + '/'
        typeOfFileName = 'simul_soil.param'
        fileName = os.path.join(self.fileNameRead, subBasinName, typeOfFileName)
        wolf_If = Wolf_Param(to_read=False,toShow=False)
        wolf_If.ReadFile(fileName)

        runnofCt = np.zeros(len(self.myRain[:]))



        if method == -1 :
            # detect the method on the params files -> TO DO
            myMethod = int(wolf_If.get_param("Distributed production model parameters","Type of infiltration"))


        if(myMethod==cst.tom_infil_Horton):
            myParams = []
            myParams.append(float(wolf_If.get_param("Horton parameters","F0")))
            myParams.append(float(wolf_If.get_param("Horton parameters","Fc")))
            myParams.append(float(wolf_If.get_param("Horton parameters","k")))


            uMax = float(wolf_If.get_param("Distributed production model parameters","Umax"))
            p = self.myRain[:]
            nb_timesteps = len(p)

            timeLag = float(wolf_If.get_param("Distributed production model parameters","Time lag"))
            try:
                timeSpan = float(wolf_If.get_param("Distributed production model parameters","Time span soil"))
                nbIntervals = math.ceil(timeSpan/self.deltaT)
            except:
                nbIntervals = len(self.myRain)
            nbLagSteps = math.ceil(timeLag/self.deltaT*3600.0)
            nbLagSteps = min(max(0,nbLagSteps),nb_timesteps)

            u = np.zeros(len(self.myRain))
            if(nbIntervals<len(self.myRain)):
                for iel in range(len(self.myRain)):
                    u[iel] = np.sum(self.myRain[max((iel-nbIntervals)+1,0):iel+1])*self.deltaT/3600.0
            else:
                u = np.cumsum(self.myRain)*self.deltaT/3600.0

            infil = datt.Horton_function(u, uMax, myParams)

            if nbLagSteps != 0:
                runnofCt[:nbLagSteps] = 1.0-myParams[0]
                runnofCt[nbLagSteps:] = (1.-infil[:-nbLagSteps])
            else:
                runnofCt[:] = 1.-infil[:]

        else:
            print("ERROR: this infil. model is not recognised or not implemented yet! ")
            sys.exit()


        return runnofCt




    def plot_diff_cumulRain_with_lagtime(self, interval=0.0, lagTime=0.0, graph_title="", factor=1.5, writeDir="", lawNetRain=cst.tom_netRain_no, netRainParams={}):
        """
        @var interval interval to consider in the gliding sum [sec]
        @var lagTime time to skip before applyihng the current rain [sec]
        """
        if interval==0:
            nbIntervals = len(self.myRain)
        else:
            nbIntervals = math.ceil(interval/self.deltaT)

        if lagTime==0:
            nbLagSteps = 0
        else:
            nbLagSteps =  math.ceil(lagTime/self.deltaT)

        if(lawNetRain==cst.tom_netRain_no):
            rain = self.myRain
        elif(lawNetRain==cst.tom_netRain_storage):
            Hs = 0.0
            Ts = 0.0
            S0 = 0.0
            if("Hs" in netRainParams):
                Hs = netRainParams["Hs"]
            if("Ts" in netRainParams):
                Ts = netRainParams["Ts"]
            if("S0" in netRainParams):
                S0 = netRainParams["S0"]
            rain = self.apply_stock_reservoir(Hs=Hs, Ts=Ts, curS0=S0)
        else:
            print("ERROR: Not the correct type of rain preprocess model. Please check argument 'lawNetRain' ")

        tmpCumul  = np.zeros(len(rain))
        tmpCumul2 = np.zeros(len(rain))
        # if(nbIntervals<len(self.myRain)):
        #     for iel in range(len(self.myRain)):
        #         tmpCumul[iel] = np.sum(self.myRain[max((iel-nbIntervals)+1,0):iel+1])*self.deltaT/3600.0
        # else:
        #     tmpCumul = np.cumsum(self.myRain)*self.deltaT/3600.0

        # Cumulated sum over the given interval -> fast running procedure
        kernel = np.ones(nbIntervals)
        tmpCumul = np.convolve(rain,kernel)[:-nbIntervals+1]*self.deltaT/3600.0
        if(nbLagSteps==0):
            tmpCumul2[:] = tmpCumul[:].copy()
            tmpCumul = np.convolve(self.myRain,kernel)[:-nbIntervals+1]*self.deltaT/3600.0
        else:
            tmpCumul2[nbLagSteps:] = tmpCumul[:-nbLagSteps]


        # Determine the number of elements to plot
        nbElements = 3
        lastElement = 0



        # Construction of the list of element to plot on the main hydrograph
        myOutFlow = self.outFlow_global
        tmpSum = np.zeros(len(myOutFlow)-lastElement)
        y = np.zeros((len(myOutFlow)-lastElement,nbElements))

        y[:,0] = tmpCumul[:]
        y[:,1] = tmpCumul2[:]
        y[:,2] = tmpCumul[:] - tmpCumul2[:]



        # label on x-axis
        x_title = "dates : GMT+" + str(self.tz)

        # label on y-axis
        y_title = "Volume [mm]"

        # label on y-axis
        y_titles = []

        if(lawNetRain==cst.tom_netRain_no):
            y_titles.append("Cumulated Rain")
            y_titles.append("Cumulated Rain with lag time")
        elif(lawNetRain==cst.tom_netRain_storage):
            y_titles.append("Cumulated Raw Rain")
            y_titles.append("Cumulated Net Rain")
        y_titles.append("Delta Cumulated Rain")


        # Colors of the plot
        myColors = []
        for i in range(nbElements):
            myColors.append('')

        # Type of trait in the plot
        myTraits = []
        myTraits.append('--')
        myTraits.append('--')
        myTraits.append('-')

        # The additional plots to add
        # Evapotranspiration
        z = []
        y_labelAddPlot = []
        haveUpperPlot = False
        nbAddPlot = 0

        # Graph title:
        if(graph_title==''):
            if(self.name is not None):
                graph_title = "Cumulated volume in " + self.name + " : step = " + str(interval/3600) + " [h]"

        # Range to consider
        rangeData = [self.dateBegin, self.dateEnd]
        yrangeRain = []
        yrangeData = [min(y[:,2]),max(max(y[:,0]),max(y[:,2]))*1.5]
        if writeDir == "":
            writeFile = ""
        else:
            writeFile = writeDir + "CumulRain_Delta_" + self.name + "_" + str(int(interval/3600)) + "_" + str(int(lagTime/3600))+".png"

        # if(factor!=1.5 and yrangeRain!=[]):
        #     print("WARNING: factor and range cannot be specified at the same time. Only factor will be taken into account.")
        #     yrangeRain=[]
        # if(factor!=1.5 and yrangeData!=[]):
        #     print("WARNING: factor and range cannot be specified at the same time. Only factor will be taken into account.")
        #     yrangeData=[]


        # Launch the procedure
        ph.plot_hydro(nbElements,y,rain,x_title=x_title,y_titles=y_title, beginDate=self.dateBegin,endDate=self.dateEnd,
                        dt=self.deltaT,graph_title=graph_title,y_labels=y_titles,rangeData=rangeData,y_rain_range=yrangeRain,y_data_range=yrangeData,myColors=myColors,typeOfTraits=myTraits,
                        upperPlot=haveUpperPlot,nbAddPlot=nbAddPlot,z=z,y_labelAddPlot=y_labelAddPlot,deltaMajorTicks=86400,deltaMinorTicks=3600, writeFile=writeFile)




    def find_outFlow_peak(self):

        myOutFlow = self.outFlow_global

        maxIndex = np.argmax(myOutFlow)
        maxValue = myOutFlow[maxIndex]
        maxTime = self.time[maxIndex]
        maxDatetime = datetime.datetime.fromtimestamp(maxTime, tz=datetime.timezone.utc)

        self.peakVal = maxValue
        self.peakTime = maxDatetime




    def get_outFlow_peak(self, noDelay=False):

        if(self.peakVal==0.0 or self.peakTime is None):
            self.find_outFlow_peak()

        maxValue = self.peakVal
        maxDatetime = self.peakTime

        if(noDelay):
            detlaTimeDelay = datetime.timedelta(seconds=self.timeDelay)
            maxDatetime -= self.timeDelay

        return maxValue, maxDatetime



    ##  This function returns the net rain vector after applying a storage reservoir.
    # @var H_s max height of the reservoir [mm]
    # @var T_s time to empty completely the reservoir [h]
    def apply_stock_reservoir(self, Hs, Ts, curS0=0.0):
        """
        This function returns the net rain vector after applying a storage reservoir.
        @var H_s max height of the reservoir [mm]
        @var T_s time to empty completely the reservoir [h]
        """

        Pnet = np.zeros_like(self.myRain)
        curS = curS0
        Qs = Hs/Ts
        dt = self.deltaT/3600.0


        for curT in range(len(self.myRain)):
            curS += (self.myRain[curT]-Qs)*dt
            Pnet[curT] = max(0.0, curS-Hs)/dt
            curS = max(0.0,min(curS,Hs))

        return Pnet



    def unuse(self, mask=[]):

        self.alreadyUsed = False
        for element in self.intletsObj:
            self.intletsObj[element].unuse(mask=mask)



    def activate(self, effSubs:list=[], effSubsSort:list=[], mask:list=[], onlyItself:bool=False):

        self.isActivated = True
        if self.alreadyUsed == False:
            self.alreadyUsed = True
            effSubs.append(int(self.iD.replace("ss","")))
            effSubsSort.append(self.iDSorted)
            if onlyItself == False:
                for element in self.intletsObj:
                    effSubs, effSubsSort = self.intletsObj[element].activate(mask=mask, effSubs=effSubs, effSubsSort=effSubsSort, onlyItself=onlyItself)
                    # effSubs.extend(tmpSub)
                    # effSubsSort.extend(tmpSubSort)

        return effSubs, effSubsSort


    def reset_timeDelay(self, keepDelta=False, keepDeltaAll=False, upStreamTime=-1.0):

        # This step reset the timeDelay but still keep the time delta between modules
        if keepDelta:
            curTime = self.timeDelay
            self.timeDelay = self.timeDelay-upStreamTime
        else:
            curTime = self.timeDelay
            if(upStreamTime>=0):
                self.timeDelay = 0.0

        for element in self.intletsObj:
            self.intletsObj[element].reset_timeDelay(keepDelta=keepDeltaAll, keepDeltaAll=keepDeltaAll, upStreamTime=curTime)



    def add_timeDelay(self, deltaT=0.0, reset=False, resetAll=False):

        if reset:
            self.timeDelay = deltaT
        else:
            self.timeDelay += deltaT

        for element in self.intletsObj:
            self.intletsObj[element].add_timeDelay(self.timeDelay, reset=resetAll, resetAll=resetAll)


    def get_inletsName(self):

        allInlets = []

        for element in self.intletsObj:
            allInlets.append(str(self.intletsObj[element].name))

        return allInlets


    def get_timeDelays(self, timeDelays={}):

        timeDelays[self.name] = self.timeDelay
        for element in self.intletsObj:
            timeDelays = self.intletsObj[element].get_timeDelays(timeDelays)

        return timeDelays


    def get_timeDelays_inlets(self):

        return {el.name: el.timeDelay-self.timeDelay for el in self.intletsObj.values()}


    def get_surface_proportions(self, show=True):
        print("To DO!!!")


    ## This procedure initialises the time delays (time to transfer hydrographs) with respect to the outlet
    def init_timeDelay(self):
        workinDir = os.path.join(self.fileNameRead, "Subbasin_"+str(self.iDSorted))
        fileName = "transfer.param"
        fileTitle = os.path.join(workinDir,fileName)
        if os.path.exists(fileTitle):
            self.transferParam = Wolf_Param(filename=fileTitle,toShow=False)
            transferModel = int(self.transferParam.get_param("General properties","Type of model"))
            if transferModel == cst.tom_transf_no:
                print("The time estimation will be taken into account for timeDelay!")
            elif transferModel == cst.tom_transf_cst:
                # Update timeDelay from transfer file
                self.timeDelay = self.transferParam.get_param("Constant", "Time Delay")
            else:
                print("ERROR in 'init_timeDelay' -> SubBasin : this model is not implemented yet!")
                print("Model required = ", transferModel)

        else:
            print("WARNING : transfer file not present! The time estimation will be taken into account for timeDelay!")


    ## This function returns the value read at the outlet on a Wolf map
    def get_value_outlet(self, wolfarray:WolfArray):
        # If no map, not possible to go further with this method
        if type(wolfarray) != WolfArray:
            print("ERROR : wolfarray not a WolfArray type!")
            print("Type given : ", type(wolfarray))
            return None

        value = wolfarray.get_value(self.x, self.y)

        if value == -99999:
            print("ERROR : timeDelay not found for this element : ")
            print("Name = ", self.name)
            print("File = ", wolfarray.filename)
            print("===================")
            return None

        return value


    def get_iDSorted(self):

        return self.iDSorted


    # ## Set all desired timeDelays in the network
    # def set_timeDelay(self, method:str="wolf_array", wolfarray:WolfArray=None, tRef_old:float=0.0, tRef_new:float=0.0, updateDownstream:bool=True):

    #     if method.lower() == "wolf_array":
    #         timeDelay = self.get_value_outlet(wolfarray)
    #         if timeDelay is None:
    #             return None
    #         self.timeDelay = timeDelay
    #     else:
    #         print("ERROR: This method to set timeDelay is not recognised!")
    #         return

    #     if updateDownstream:
    #         for element in self.intletsObj:
    #             curObj = self.intletsObj[element]
    #             curObj.
    #             # curObj = self.add_timeDelay




    ##  This procedure save in a "transfer.param" file the timeDelay of the SubBasin
    def save_timeDelay(self, changeTofMod=True):
        print("Saving timeDelay from SubBasin", self.name)
        workinDir = os.path.join(self.fileNameRead, "Subbasin_"+str(self.iDSorted))
        fileName = "transfer.param"
        fileTitle = os.path.join(workinDir,fileName)

        if self.transferParam is None:
            self.transferParam = Wolf_Param(filename=fileTitle,toShow=False)

        self.transferParam.change_param("Constant","Time Delay", self.timeDelay)
        if changeTofMod:
            self.transferParam.change_param("General properties","Type of model", cst.tom_transf_cst)
        self.transferParam.SavetoFile(None)
        self.transferParam.Reload(None)


    ##  This procedure save in a "transfer.param" file the timeDelay of the SubBasin and all its upstream elements
    def save_timeDelays(self):

        self.save_timeDelay()
        for element in self.intletsObj:
            self.intletsObj[element].save_timeDelays()


    def get_myHydro(self, unit:str="mm/h") -> np.ndarray:

        if unit=="m3/s" or unit=="m^3/s":
            if self.model == cst.measures:
                # FIXME we consider so far that myHydro of a measures are in m^3/h
                myHydro = self.myHydro
            elif self.surfaceDrained<=0.0:
                logging.error("The surface drained is negative or equal to zero! myHydro will be given in mm/h!")
                if len(np.shape(self.myHydro)) == 1:
                    myHydro = self.myHydro.copy()
                else:
                    myHydro = np.sum(self.myHydro,1)
            else:
                if len(np.shape(self.myHydro)) == 1:
                    myHydro = self.myHydro*self.surfaceDrained/3.6
                else:
                    myHydro = np.sum(self.myHydro,1)*self.surfaceDrained/3.6
        else:
            if len(np.shape(self.myHydro)) == 1:
                myHydro = self.myHydro.copy()
            else:
                myHydro = np.sum(self.myHydro,1)

        return myHydro


    ## This function is getting the name/meaning behind landuse indices
    # It will then fill the given or not dict of landuse with a name property
    def get_landuse_index_transform_default(self, landuseDict:dict={}) -> dict:

        if landuseDict is None:
            landuseDict = {}

        for key in cst.DEFAULT_LANDUSE:
            if not key in landuseDict:
                landuseDict[key] = {}
            landuseDict[key]["name"] = cst.DEFAULT_LANDUSE[key]
            landuseDict[key]["surface"] = 0.0
            landuseDict[key]["unit"] = "[-]"

        return landuseDict


    ## This function is getting the name/meaning behind landuse indices
    # It will then fill the given or not dict of landuse with a name property
    def get_landuse_index_transform(self, directory:str, landuseDict:dict={}) -> dict:
        if directory=="":
            landuseDict = self.get_landuse_index_transform_default(landuseDict=landuseDict)
            return
        else:
            fileName = "Landuse_index_transform.txt"
            fileName = os.path.join(directory,fileName)
            if not(os.path.exists(fileName)):
                logging.error("This path does not exist : ")
                logging.error(fileName)
                logging.error("get_landuse_index_transform() aborded !")
                return None

        toStart = False
        with open(fileName, newline = '') as fileID:
            data_reader = csv.reader(fileID, delimiter='=')
            list_data = []
            for curData in data_reader:
                if curData == []:
                    pass
                elif toStart and len(curData)==2:
                    list_data.append(curData)
                elif len(curData[0])>13:
                    if curData[0][:13] == "Signification":
                        toStart = True

        for line in list_data:
            if len(line)>1:
                key = int(line[0])
                if not key in landuseDict:
                    landuseDict[key] = {}
                landuseDict[key]["name"] = line[1].strip()
                landuseDict[key]["surface"] = 0.0
                landuseDict[key]["unit"] = "[-]"

        return landuseDict

    ## This function is reading the string of the landuse in the avrg_charact file
    def read_landuses(self, fileName:str="", onlySub:bool=True, landuseName:str="", landuse_index_transform:str="", toSave:bool=True) -> dict:

        # Choose if it's only the SubBasin of the hydro SubBasin
        if onlySub:
            avrgDict = self.mainCharactDict
            if avrgDict == {}:
                self.read_myMainCharacteristics(self.fileNameRead)
                avrgDict
        else:
            avrgDict = self.mainCharactDictWholeHydro
            if avrgDict == {}:
                self.read_myMainCharacteristics(self.fileNameRead)

        # Get the names of all landuses
        landuseDict = {}
        landuseDict = self.get_landuse_index_transform(landuse_index_transform, landuseDict=landuseDict)
        if landuseDict is None:
            landuseDict = self.get_landuse_index_transform_default(landuseDict=landuseDict)

        # Get the surfaces and units of all landuses
        for key in landuseDict:
            associated_key = "Fraction of landuse n "+str(key)
            if associated_key in avrgDict:
                # If the lanuse type is not present, it will be set to 0.0
                landuseDict[key]["surface"] = avrgDict[associated_key]["value"]
                landuseDict[key]["unit"] = avrgDict[associated_key]["unit"]
            else:
                landuseDict[key]["surface"] = 0.0
                landuseDict[key]["unit"] = "[-]"

        if toSave:
            if onlySub:
                self.landuseDict = landuseDict
            else:
                self.landuseHydroDict = landuseDict

        return landuseDict


    def get_landuses(self, onlySub:bool=True) -> dict:

        if onlySub:
            return self.landuseDict
        else:
            return self.landuseHydroDict


    def plot_landuses(self, onlySub:bool=True, figure=None, toShow=False, writeFile=""):

        landuseDict = self.get_landuses(onlySub=onlySub)

        if landuseDict == {}:
            logging.error("No landuse dict found !")
            logging.error("Please use first the function read_landuse()! ")
            logging.error("Plot aborted !")
            return

        # Creation of data and legend
        data = []
        names = []
        for landuse in landuseDict.values():
            data.append(landuse["surface"])
            names.append(landuse["name"])

        # Creation of colors
        colorDict = {}
        colorDict["forêt"] = 'tab:green'
        colorDict["prairie"] = 'tab:olive'
        colorDict["culture"] = 'tab:brown'
        colorDict["pavés/urbain"] = 'tab:gray'
        colorDict["rivière"] = 'tab:cyan'
        colorDict["plan d'eau"] = 'tab:blue'

        colors = []
        for i in range(len(names)):
            key = names[i]
            if key in colorDict:
                colors.append(colorDict[key])

        # Creation of title
        title = "Landuses in "
        if onlySub:
            typeOfSub = "subbasin "
        else:
            typeOfSub = "hydrological subbasin "
        title  += typeOfSub + "in " + self.name

        if writeFile == "":
            writeFile = os.path.join(self.fileNameWrite, "PostProcess", title.replace(" ", "_"))
        else:
            writeFile = writeFile

        ph.plot_piechart(data,legend=names, title=title, colors=colors, autopct="", figure=figure, writeFile=writeFile, toShow=toShow)

        if toShow:
            plt.show()


    def get_outFlow_names(self)->list:

        return list(self._outFlow.keys())


    def change_version(self, newVersion=None):

        if newVersion is None:
            self._version = float(cst.VERSION_WOLFHYDRO)
        elif type(newVersion) == str:
            self._version = float(newVersion)
        else:
            self._version = newVersion

        return


    def get_version(self):

        return self._version


    ## This procedure is updating all the hydrographs of all upstream elements imposing limits
    # @var level_min integer that specify the potential level at which the update should be stopped.
    def update_upstream_hydro(self, level_min:int=1, update_upstream:bool=True):

        for key in self.intletsObj:
            curObj = self.intletsObj[key]
            if curObj.myLevel>=level_min:
                curObj.update_hydro(update_upstream=True, level_min=level_min)



    ## This procedure is updating all the hydrographs and possibly all upstream elements imposing limits
    # @var update_upstream boolean that specify whether the upstream elements should also be updated
    # @var level_min integer that specify the potential level at which the update should be stopped.
    def update_hydro(self, update_upstream:bool=True, level_min:int=1):

        if update_upstream:
            self.update_upstream_hydro(level_min=level_min)

        self.compute_hydro()


    def get_outFlow_global(self, whichOutFlow="", typeOutFlow="Net"):

        if typeOutFlow == "Net":
            return self.outFlow_global
        elif typeOutFlow =="Raw":
            return self.outFlowRaw_global
        else:
            logging.error("Not a recognised typeOutFlow ! ")
            return None


    @property
    def outFlow(self)->np.ndarray:
        """The outFlow property."""
        return self.get_outFlow(typeOutFlow="Net", unit="m³/s")


    @property
    def outFlowRaw(self):
        """The outFlow property."""
        return self.get_outFlow(typeOutFlow="Raw", unit="m³/s")


    @property
    def outFlow_global(self):
        """The outFlow global property.
        Returns the outFlow in the global time, i.e. the hydrograph to which the timeDelay is applied.
        """
        gOutFlow = np.zeros(len(self.myHydro),dtype=ct.c_double, order='F')
        index = math.floor(self.timeDelay/self.deltaT)
        if(index==0):
            gOutFlow = self.outFlow
        elif(index<len(self.myHydro)):
            gOutFlow[index:] = self.outFlow[:-index]
        else:
            logging.error("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
            logging.error("Error informations : ")
            logging.error("Function name : outFlow_global()")
            logging.error("Name = "+ self.name)
            logging.error("ID = "+ str(self.iD))
            logging.error("index = " +  str(index))
            logging.error("len(myOutFlow) = "+ str(len(self.myHydro)))
            logging.error("self.timeDelay = "+ str(self.timeDelay))
            logging.error("All inlets timeDelay :")

            for element in self.intletsObj:
                curObj = self.intletsObj[element]
                logging.error(str(curObj.timeDelay))
            logging.error("=================")

        return gOutFlow


    @property
    def outFlowRaw_global(self):
        """The outFlow global property.
        Returns the outFlow in the global time, i.e. the hydrograph to which the timeDelay is applied.
        """
        gOutFlow = np.zeros(len(self.myHydro),dtype=ct.c_double, order='F')
        index = math.floor(self.timeDelay/self.deltaT)
        if(index==0):
            gOutFlow = self.outFlow
        elif(index<len(self.myHydro)):
            gOutFlow[index:] = self.outFlowRaw[:-index]
        else:
            logging.error("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
            logging.error("Error informations : ")
            logging.error("Function name : outFlow_global()")
            logging.error("Name = "+ self.name)
            logging.error("ID = "+ str(self.iD))
            logging.error("index = " +  str(index))
            logging.error("len(myOutFlow) = "+ str(len(self.myHydro)))
            logging.error("self.timeDelay = "+ str(self.timeDelay))
            logging.error("All inlets timeDelay :")

            for element in self.intletsObj:
                curObj = self.intletsObj[element]
                logging.error(str(curObj.timeDelay))
            logging.error("=================")

        return gOutFlow


    @property
    def cumul_rain(self) -> np.array:
        return np.cumsum(self.myRain)



    def evaluate_Nash(self, measure,
                      intervals:list[tuple[datetime.datetime]]=[]) -> list[float]:
        ns = []

        if intervals == []:
            ns.append( datt.evaluate_Nash(self.outFlow, self.time,
                                         measures=measure.get_myHydro(), tMeasures=measure.time,
                                         dateBegin=self.dateBegin, dateEnd=self.dateEnd) )
            return tuple(ns)

        # for el in intervals:
        #     ns.append( datt.evaluate_Nash(self.outFlow, self.time,
        #                                  measures=measure.get_myHydro(), tMeasures=measure.time,
        #                                  dateBegin=el[0], dateEnd=el[1]) )
        ns = [ datt.evaluate_Nash(self.outFlow, self.time,
                                  measures=measure.get_myHydro(), tMeasures=measure.time,
                                  dateBegin=el[0], dateEnd=el[1])
              for el in intervals ]

        return tuple(ns)


    def get_peak(self, intervals:list[tuple[datetime.datetime]]=[]) -> list[float]:

        peak_s = []
        for element in intervals:
            # We conisder the indice to form complete intervals
            simul_i = math.ceil((element[0]-self.dateBegin).total_seconds()/self.deltaT)
            simul_f = math.floor((element[1]-self.dateBegin).total_seconds()/self.deltaT)
            # meas_i = math.floor((element[0]-measure.dateBegin).total_seconds/measure.deltaT)
            # meas_f = math.floor((element[1]-measure.dateBegin).total_seconds/measure.deltaT)
            if simul_i<0 or simul_f>len(self.time):
                continue
            peak_s.append(self.outFlow[simul_i:simul_f+1].max())

        return peak_s


    def collect_x_from_production(self) -> dict[str,np.array]:
        """
        This procedure is collecting all the time series fractions of each outflow of the hydrological production models written in Fortran

        Returns:
            dict[str, np.array]: A dictionary containing the fractions of each outflow.
        """
        all_x = {}

        if self.model == cst.tom_VHM:
            all_x = self.collect_x_VHM()
        elif self.model == cst.tom_GR4:
            all_x = self.collect_x_GR4()
        elif self.model == cst.tom_2layers_linIF:
            all_x = self.collect_x_2layers()

        return all_x

    def collect_fractions(self) -> dict[str,np.array]:
        """
        This procedure is collecting all the fractions of each outflow of the hydrological production models.

        Returns:
            dict[str, np.array]: A dictionary containing the fractions of each outflow.
        """
        all_x = self.collect_x_from_production()

        if self.model == cst.tom_VHM:
            all_f = self._collect_fractions_VHM(all_x)
        elif self.model == cst.tom_GR4:
            all_f = self._collect_fractions_GR4(all_x)
        elif self.model == cst.tom_2layers_linIF:
            all_f = self._collect_fractions_2layers(all_x)

        return all_f


    def collect_all_internal_variables(self) -> dict[str,np.array]:
        """
        This procedure is collecting all internal variables of the hydrological production models.

        Returns:
            dict[str, np.array]: A dictionary containing the fractions of each outflow.
        """
        all_iv = {}

        if self.model == cst.tom_VHM:
            all_iv = self.collect_iv_VHM()
        elif self.model == cst.tom_GR4:
            all_iv = self.collect_iv_GR4()
        elif self.model == cst.tom_2layers_linIF:
            all_iv = self.collect_iv_2layers()

        return all_iv


    def activate_all_internal_variables(self):
        """
        This procedure is activating all internal variables of all the hydrological modules.
        """
        # if self.model == cst.tom_VHM:
        #     self.activate_all_iv_VHM()
        # elif self.model == cst.tom_GR4:
        #     self.activate_all_iv_GR4()
        # elif self.model == cst.tom_2layers_linIF:
        #     self.activate_all_iv_2layers()
        cur_dir = os.path.join(self.fileNameRead, "Subbasin_"+str(self.iDSorted))
        mc.MODELS_VAR[self.model].deactivate_all(directory=cur_dir, prefix_file='simul')
        mc.MODELS_VAR[self.model].activate_all(directory=cur_dir, prefix_file='simul', type_of_var=iv.FINAL_OUT_VAR)
        mc.MODELS_VAR[self.model].activate_all(directory=cur_dir, prefix_file='simul', type_of_var=iv.IV_VAR)


    def collect_x_VHM(self) -> dict[str,np.array]:
        """
        This procedure is collecting all the fractions of each outflow of the VHM model.

        Returns:
        - all_x: A dictionary containing the fractions of each outflow of the VHM model.
        """
        list_keys = ["x", "U"]
        files_per_keys = [["xbf", "xif", "xof", "xu"],[]]
        group = "Internal variables to save"
        param = "simul_soil"

        all_x = self.collect_internal_variables(list_keys, files_per_keys,
                            group_name=group, param_name=param)

        return all_x


    def _collect_fractions_VHM(self, all_x:dict[str,np.array]) -> dict[str,np.array]:
        """
        This procedure is collecting all the fractions of each outflow of the VHM model.

        Returns:
        - all_f: A dictionary containing the fractions of each outflow of the VHM model.
        """
        all_f = {}

        if all_x=={}:
            return all_f

        condition = self.myRain > 0.0

        all_f["% qof"] = np.where(condition, all_x["xof"] * 100.0, np.nan)
        all_f["% qif"] = np.where(condition, all_x["xif"] * 100.0, np.nan)
        all_f["% qbf"] = np.where(condition, all_x["xbf"] * 100.0, np.nan)
        all_f["% loss"] = np.where(condition, all_x["xu"]  * 100.0, np.nan)

        return all_f


    def collect_iv_VHM(self) -> dict[str,np.array]:
        """
        This procedure is collecting all internal variables of the VHM model in each module.

        Returns:
        - all_iv: A dictionary containing all internal variables of the VHM model.
        """
        list_keys = ["x", "U"]
        files_per_keys = [[],["U"]]
        group = "Internal variables to save"
        param = "simul_soil"

        all_iv = self.collect_internal_variables(list_keys, files_per_keys,
                            group_name=group, param_name=param)

        return all_iv


    def activate_all_iv_VHM(self):
        """
        This procedure is activating all internal variables of the VHM model in each module.
        """
        list_keys = ["x", "U"]
        group = "Internal variables to save"
        param = "simul_soil"

        self.activate_internal_variables(list_keys, group_name=group, param_name=param)


    def collect_x_GR4(self) -> dict[str,np.array]:
        """
        This procedure is collecting the fractions of each outflow of the GR4 model.

        Returns:
            dict[str, np.array]: A dictionary containing all fractions of each outflow of the GR4 model.
        """
        all_x = {}

        return all_x


    def _collect_fractions_GR4(self, all_x:dict[str,np.array]) -> dict[str,np.array]:
        """
        This procedure is collecting all the fractions of each outflow of the GR4 model.

        Returns:
        - all_f: A dictionary containing the fractions of each outflow of the GR4 model.
        """
        all_f = {}

        return all_f


    def collect_iv_GR4(self) -> dict[str,np.array]:
        """
        This procedure is collecting all internal variables of the GR4 model in each module.

        Returns:
        - all_iv: A dictionary containing all internal variables of the GR4 model.
        """
        all_iv = {}

        return all_iv


    def activate_all_iv_GR4(self):
        """
        This procedure is activating all internal variables of the GR4 model in each module.
        """
        return


    def collect_x_2layers(self) -> dict[str,np.array]:
        """
        This procedure is collecting the fractions of each outflow of the 2 layers model.

        Returns:
            A dictionary containing the collected fractions of each outflow variables.
        """
        list_keys = ["x", "U", "Reservoir"]
        files_per_keys = [["xif"], [], ["xp"]]
        group = "Internal variables to save"
        param = "simul_soil"

        all_x = self.collect_internal_variables(list_keys, files_per_keys,
                                                group_name=group, param_name=param)

        return all_x


    def _collect_fractions_2layers(self, all_x:dict[str,np.array]) -> dict[str,np.array]:
        """
        This procedure is collecting all the fractions of each outflow of the 2 layers model.

        Returns:
        - all_f: A dictionary containing the fractions of each outflow of the 2 layers model.
        """
        all_f = {}

        if all_x=={}:
            return all_f

        condition = self.myRain > 0.0

        f_if = np.where(condition, all_x["xp"] * all_x["xif"], np.nan)

        all_f["% qof"] = (all_x["xp"] - f_if) * 100.0
        all_f["% qif"] = f_if * 100.0
        all_f["% loss"] = np.where(condition, (1.0 - all_x["xp"]) * 100.0, np.nan)

        return all_f


    def collect_iv_2layers(self) -> dict[str,np.array]:
        """
        This procedure is collecting all internal variables of the 2 layers model in each module.

        Returns:
        - all_iv: A dictionary containing the fractions all internal variables of the 2 layers model.
        """
        list_keys = ["x", "U", "Reservoir"]
        files_per_keys = [[], ["U"], ["S"]]
        group = "Internal variables to save"
        param = "simul_soil"

        all_iv = self.collect_internal_variables(list_keys, files_per_keys,
                                                group_name=group, param_name=param)

        return all_iv


    def activate_all_iv_2layers(self):
        """
        This procedure is activating all internal variables of the 2 layers model in each module.
        """
        list_keys = ["x", "U", "Reservoir"]
        group = "Internal variables to save"
        param = "simul_soil"

        self.activate_internal_variables(list_keys, group_name=group, param_name=param)


    def collect_internal_variables(self, list_keys:list[str], files_per_keys:list[list[str]],
                  group_name:str="Internal variables to save", param_name:str="simul_soil"
                )-> dict[str,np.array]:
        """
        Collects all the internal variables of the 2 layers model.

        Parameters:
        - list_keys (list[str]): List of keys representing the internal variables to collect.
        - files_per_keys (list[list[str]]): List of lists containing the file names associated with each key.
        - group_name (str, optional): Name of the group containing the internal variables to save. Default is "Internal variables to save".
        - production_name (str, optional): Name of the production file. Default is "simul_soil".

        Returns:
        - dict[str,np.array]: A dictionary containing the collected internal variables, where the keys are the variable names and the values are numpy arrays.

        """
        all_iv = {}

        production_file = ".".join([param_name,"param"])
        cur_dir = os.path.join(self.fileNameRead, "Subbasin_"+str(self.iDSorted))
        param_fileName = os.path.join(cur_dir, production_file)

        wolf_soil = Wolf_Param(to_read=True, filename=param_fileName,toShow=False, init_GUI=False)

        for index, curKey in enumerate(list_keys):
            ok_IV = wolf_soil.get_param(group_name, curKey, default_value=0)
            if ok_IV == 1:
                for curVar in files_per_keys[index]:
                    ts_file = "".join([param_name, "_", curVar, ".dat"])
                    isOk, tmp = rd.check_path(os.path.join(cur_dir, ts_file))
                    if isOk<0:
                        logging.warning("The file : " + ts_file + " does not exist!")
                        continue
                    time, cur_iv = rd.read_hydro_file(cur_dir, ts_file)
                    all_iv[curVar] = cur_iv
            else:
                logging.warning("Please activate the interval variable : " + curKey + "to have access the following fraction of outlets : ")

        return all_iv


    def activate_internal_variables(self, list_keys:list[str], group_name:str="Internal variables to save", param_name:str="simul_soil"):
        """
        Activates all the internal variables of the 2 layers model.

        Parameters:
        - list_keys (list[str]): List of keys representing the internal variables to collect.

        """
        production_file = ".".join([param_name,"param"])
        cur_dir = os.path.join(self.fileNameRead, "Subbasin_"+str(self.iDSorted))
        param_fileName = os.path.join(cur_dir, production_file)

        wolf_soil = Wolf_Param(to_read=True, filename=param_fileName,toShow=False, init_GUI=False)

        for curKey in list_keys:
            wolf_soil.change_param(group_name, curKey, 1)

        wolf_soil.SavetoFile(None)
        wolf_soil.Reload(None)

        return

    def get_summary_fractions(self, summary:str="mean", all_f:dict={},
                              interval:list[tuple[datetime.datetime, datetime.datetime]]=None) -> dict[str, np.array]:
        """
        This procedure is returning a summary of the fractions of the current module.

        Parameters:
        - summary (str): The type of summary to return.
        - interval (list[datetime.datetime], optional): The interval of time to consider. Default is None.

        Returns:
        - dict: A dictionary containing the summary of the fractions of the current module.
        """

        if all_f == {}:
            all_f = self.collect_fractions()

        return self._operation_on_ts(all_f, operation=summary, interval=interval)


    def get_volume_fractions(self, all_f:dict={},
                              interval:list[tuple[datetime.datetime, datetime.datetime]]=None) -> dict[str, np.array]:
        """
        This procedure is returning a summary of the fractions of the current module.

        Parameters:
        - summary (str): The type of summary to return.
        - interval (list[datetime.datetime], optional): The interval of time to consider. Default is None.

        Returns:
        - dict: A dictionary containing the summary of the fractions of the current module.
        """

        if all_f == {}:
            all_f = self.collect_fractions()

        all_v = {key: val/100.0*self.myRain for key, val in all_f.items()}

        if interval is not None:
            interv = np.zeros(len(self.time), dtype=bool)
            for el in interval:
                date_i = datetime.datetime.timestamp(el[0])
                date_f = datetime.datetime.timestamp(el[1])
                interv += (self.time>=date_i) & (self.time<=date_f)
        else:
            interv = np.ones(len(self.time), dtype=bool)

        tot_rain = np.nansum(self.myRain[interv])*self.deltaT/3600

        return {key+" volume": (np.nansum(all_v[key][interv])*self.deltaT/3600)/tot_rain*100 for key in all_v}


    def check_presence_of_iv(self):
        """
        This procedure is checking the presence of internal variables in the current module.
        """
        # TODO

        return


    def get_all_Qtest(self, nb_atttempts=-1, typeOutFlow:str="Net", unit:str='m3/s', whichOutFlow="", lag:float=0.0) -> np.array:
        """
        This function returns the Qtest hydrograph of the current module.

        Parameters:
        - which (str, optional): The type of hydrograph to return. Default is "Net".

        Returns:
        - np.array: The Qtest hydrograph of the current module.
        """

        # FIXME Take into account all the possible types of hydrographs and units
        file_debug_info = "simul_GR4_out_debuginfo.txt"
        prefix = "simul_GR4_out"

        working_dir =  os.path.join(self.fileNameRead, 'Subbasin_' + str(self.iDSorted) + '/')

        q_test = []

        file_debug_info = "_".join([prefix,"_debuginfo.txt"])
        if nb_atttempts < 0:
            with open(os.path.join(working_dir,file_debug_info), 'r') as file:
                lines = file.readline()
            items = lines.split('\t')
            nb_init = int(items[0])
            nb_max = int(items[0])
            nb_atttempts = nb_max

        all_files = [os.path.join(working_dir,"".join([prefix,str(i+1)+".dat"])) for i in range(nb_atttempts)]
        areOk = [(rd.check_path(file)[0])>=0
                 for file in all_files]
        max_index = next((i for i, x in enumerate(areOk) if x == False), len(areOk))
        q_test = [rd.read_hydro_file(working_dir, file_name)[1]*self.surfaceDrained/3.6
                  for file_name in all_files[:max_index]]


        # for i in range(nb_atttempts):
        #     file_name = "".join([prefix,str(i+1)+".dat"])
        #     isOk, full_name = rd.check_path(os.path.join(working_dir, file_name))
        #     if isOk<0:
        #         break
        #     t, cur_q = rd.read_hydro_file(working_dir, file_name)
        #     cur_q = cur_q*self.surfaceDrained/3.6
        #     q_test.append(cur_q)

        return q_test


    def plot_all_fractions(self, all_fractions:dict[str:np.array]={},figure=None, to_show:bool=False, writeDir:str="", range_data:list[datetime.datetime]=[]) -> None:

        if writeDir == "":
            writeFile = os.path.join(self.fileNameWrite, "PostProcess", "_".join(["Q_fractions", self.name]))
        else:
            writeFile = os.path.join(writeDir, "_".join(["Q_fractions", self.name]))

        if all_fractions == {}:
            all_fractions = self.collect_fractions()
            if all_fractions == {}:
                logging.warning("No fractions found!")
                return
        elif self.name in all_fractions:
            all_fractions = all_fractions[self.name]
        else:
            all_fractions =  {}
            logging.warning("The name of the current module is not in the dictionary of fractions!")

        nb_elements = len(all_fractions)
        if nb_elements == 0:
            logging.warning("No fractions found!")
            return
        y = [el for el in all_fractions.values()]
        x = [el for el in all_fractions.keys()]
        y_label = "Fractions of the outflows [%]"
        graph_title = "Fractions of the outflows of " + self.name

        ph.plot_hydro(nb_elements, y,time=self.time, y_titles=y_label, y_labels=x, writeFile=writeFile, figure=figure, graph_title=graph_title, rangeData=range_data)

        if to_show:
            plt.show()


    def evaluate_objective_function(self, unit="mm/h")->np.ndarray:
        """
        This procedure is evaluating the objective function of the current module.

        Returns:
        - np.ndarray: The objective function of the current module.
        """
        # FIXME
        unit='mm/h'

        return self.get_outFlow(unit=unit)


    def get_flow_fractions(self, all_f:dict={}, summary:str=None,
                              interval:list[tuple[datetime.datetime, datetime.datetime]]=None) -> dict[str, np.ndarray|float]:
        """
        This procedure is returning a summary of the fractions of the current module.

        Parameters:
        - summary (str): The type of summary to return.
        - interval (list[datetime.datetime], optional): The interval of time to consider. Default is None.

        Returns:
        - dict: A dictionary containing the summary of the fractions of the current module.
        """
        print(f"Computing flow fractions for station :{self.name}")
        if all_f == {}:
            cur_dir = os.path.join(self.fileNameRead, "Subbasin_"+str(self.iDSorted))
            all_qin = mc.MODELS_VAR[self.model].get_all_iv_timeseries(directory=cur_dir,
                                            prefix_file='simul', type_of_var=iv.FINAL_OUT_VAR)
            all_f = mc.MODELS_VAR[self.model].get_all_iv_timeseries(directory=cur_dir,
                                            prefix_file='simul', type_of_var=iv.DEFAULT_VAR)
            all_f.update(all_qin)

        q_simul = self.get_myHydro(unit='mm/h')
        for key, val in all_f.items():
            if len(val) != len(q_simul):
                logging.warning(f"Length of {key} does not match with the length of the simulated flow!")
                continue
        # all_r = {"%"+key: val/q_simul * 100.0 for key, val in all_f.items()}
        all_r = {
            f"%{key}": np.where(np.isfinite(val / q_simul), (val / q_simul) * 100.0, np.nan)
            for key, val in all_f.items()
        }

        return self._operation_on_ts(all_r, summary=summary, interval=interval)


    def get_iv(self, all_iv:dict={}, max_params:dict={}, summary:str=None,
                interval:list[tuple[datetime.datetime, datetime.datetime]]=None) -> dict[str, np.array]:
        """
        This procedure is returning a summary of the fractions of the current module.

        Parameters:
        - summary (str): The type of summary to return.
        - interval (list[datetime.datetime], optional): The interval of time to consider. Default is None.

        Returns:
        - dict: A dictionary containing the summary of the fractions of the current module.
        """

        if all_iv == {}:
            cur_dir = os.path.join(self.fileNameRead, "Subbasin_"+str(self.iDSorted))
            all_iv = mc.MODELS_VAR[self.model].get_all_iv_timeseries(directory=cur_dir,
                                            prefix_file='simul', type_of_var=iv.IV_VAR)
        if max_params != {}:
            out_dict = {key: all_iv[key]/cur_max*100 for key, cur_max in max_params.items()}
        else:
            out_dict = all_iv

        return self._operation_on_ts(out_dict, summary=summary, interval=interval)


    def get_iv_fractions_one_date(self, all_iv:dict={}, max_params:dict={}, eval_date:datetime.datetime=None) -> dict[str, np.array]:
        """
        This procedure is returning a summary of the fractions of the current module.

        Parameters:
        - summary (str): The type of summary to return.
        - interval (list[datetime.datetime], optional): The interval of time to consider. Default is None.

        Returns:
        - dict: A dictionary containing the summary of the fractions of the current module.
        """

        all_iv = self.get_iv(all_iv=all_iv, max_params=max_params, summary=None)
        t_eval = datetime.datetime.timestamp(eval_date)
        eval_i = np.searchsorted(self.time, t_eval)
        if self.time[eval_i] != t_eval:
            logging.warning("The date is not in the time series!")
            return {}

        return {"% "+key: val[eval_i] for key, val in all_iv.items()}


    def import_from_pandas_Series(self, data:pd.Series, which="outFlow"):
        time = data.index.values.astype(np.int64) // 10 ** 9

        if which == "outFlow":
            self._outFlow["Net"] = data.values.astype(dtype=ct.c_double, order='F')
        elif which == "outFlowRaw":
            self._outFlow["Raw"] = data.values.astype(dtype=ct.c_double, order='F')
        elif which == "myHydro":
            self.myHydro = data.values.astype(dtype=ct.c_double, order='F')
        elif which == "myRain":
            data = data.values.astype(dtype=np.double, order='F')
        elif which == "cumul_rain":
            data = data.values.astype(dtype=np.double, order='F')
        else:
            logging.error("Not a recognised 'which' argument!")
            logging.error("Try the following : 'ouflow', 'outFlowRaw', 'myHydro', 'myRain', 'cumul_rain'")

        return

    def export_to_pandas_Series(self, which="outFlow"):
        idx = pd.to_datetime(self.time, unit='s', utc=True)

        if which == "outFlow":
            data = self.outFlow
        elif which == "outFlowRaw":
            data = self.outFlowRaw
        elif which == "myHydro":
            data = self.myHydro
        elif which == "myRain":
            data = self.myRain
        elif which == "cumul_rain":
            data = self.cumul_rain
        else:
            logging.error("Not a recognised 'which' argument!")
            logging.error("Try the following : 'ouflow', 'outFlowRaw', 'myHydro', 'myRain', 'cumul_rain'")
            return None

        tserie = pd.Series(data, index=idx, copy=True, name=" ".join([self.name,which]))

        return tserie


    def _operation_on_ts(self, ts:dict[str, np.ndarray], summary:str=None, interval:list[tuple[datetime.datetime, datetime.datetime]]=None):
        if interval is not None:
            interv = np.zeros(len(self.time), dtype=bool)
            for el in interval:
                date_i = datetime.datetime.timestamp(el[0])
                date_f = datetime.datetime.timestamp(el[1])
                interv += (self.time>=date_i) & (self.time<=date_f)
        else:
            interv = np.ones(len(self.time), dtype=bool)

        if summary is None:
            return {key: ts[key][interv] for key in ts}
        elif summary == "mean":
            return {key: np.nanmean(ts[key], where=interv) for key in ts}
        elif summary == "median":
            return {key: np.nanmedian(ts[key][interv]) for key in ts}
        elif summary == "std":
            return {key: np.nanstd(ts[key][interv]) for key in ts}
        elif summary == "min":
            return {key: np.nanmin(ts[key], where=interv) for key in ts}
        elif summary == "max":
            return {key: np.nanmax(ts[key], where=interv, initial=0.0) for key in ts}
        else:
            logging.error("The summary type is not recognised!")
            return {}

    # def plot_Nash_vs_Qexcess(self, figure:plt.axis=None, toShow:bool=False, writeFile:str=""):



    # FIXME Remove the lines below when it is confirmed
    #                   |
    #                   |
    #                   V

    # ## Function computing the cumulative volume of a given flow
    # # @var flow the flow to treat. Units: [m^3/s]
    # # @var dtData time step of the argument 'flow'. Units: [s]
    # # @var dtOut time step of the desired cumulative volume. It should be a multiple of 'dtData'. Units: [s]
    # # \undeline{Caution}: Take care to the units of dtData and dtOut according to the flow units.
    # # E.g. Hyeto and Evap in [mm/h]                     => dtData in [h]
    # # \underline{But}: outflow and myHydro in [m^3/s]   => dtData in [sec]
    # # Returns the cumulative volume. Units: [m^3]
    # # TO do: ajouter interval de temps
    # def construct_cumulVolume(self, flow, dtData, dtOut):
    #     # Check validity of the arguments
    #     if(dtOut%dtData!=0):
    #         print("ERROR: the time step of the desired output is not compatible with the data timestep!")
    #         sys.exit()
    #     else:
    #         factor = int(dtOut/dtData)   # conversion factor from data timestep and cumul time step

    #     cumul = np.zeros(int(len(flow)/factor))
    #     cumul[0] = flow[0]
    #     for i in range(1,int(len(flow)/factor)):
    #         cumul[i] = cumul[i-1] + np.sum(flow[i*factor: (i+1)*factor])*dtData

    #     return cumul
