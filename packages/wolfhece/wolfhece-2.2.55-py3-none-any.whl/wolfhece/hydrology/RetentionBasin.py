"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import sys
import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange, MicrosecondLocator
from matplotlib.font_manager import FontProperties
from scipy.interpolate import interp1d
import os
import ctypes as ct

from .SubBasin import *
from .Outlet import *
from .Dumping import *
from ..PyTranslate import _
from . import constant as cst
from ..PyVertexvectors import getIfromRGB, getRGBfromI

class RetentionBasin():
    ## @var outFlow
    # Final hydro of the anthropogenic module. Combined with the potentiel upstream hydros and treated.
    # Version :
    #  - < 2023.0  : "outFlow" is a dictionnary and public variable.
    #                Consider timeDelay so that time is at 0 at the global outlet. Therefore the transfer to the general outlet is applied.
    #  - >= 2023.1 : "_outflow" is now a private dictionnary linked to a property called "outFlow".
    #                It considers the hydro at the local time. To apply the transfer call the property "glob_hydro"
    _outFlow:dict
    surfaceDrainedHydro:float # TO BUILD !!!!!!!!!!!!!!
    filledVolume:np.ndarray
    intletsObj:dict
    directFluxObj:dict

    def __init__(self, _dateBegin=None, _dateEnd=None, _deltaT:int=None, _time=None, _id='J1', _name='Default name', _type='',
                 _dictRB={}, _directDictRB={}, _tz=0, _outletNames=[], withRBDict=True, _workingDir=""):
        print('Creation of a RetentionBasin!')
        self.iD = _id
        self.name = _name
        self.type = _type
        self.time = _time
        self.dictRB = {}
        self.alreadyUsed = False
        self.isLeveled = False
        self.myLevel = 2
        self.dateBegin = _dateBegin
        self.dateEnd = _dateEnd
        self.deltaT = _deltaT
        self.tz = _tz
        self.fileNameRead = _workingDir # //
        self.fileNameWrite = self.fileNameRead
        if(_time is None):
            if(_dateBegin is None or _dateEnd is None or _deltaT is None):
                self.time = None
                self.filledVolume = None
            else:
                tzDelta = datetime.timedelta(hours=self.tz)
                ti = datetime.datetime.timestamp(self.dateBegin-tzDelta)
                tf = datetime.datetime.timestamp(self.dateEnd-tzDelta)
                self.time = np.arange(ti,tf+self.deltaT,self.deltaT)
                self.filledVolume = np.zeros(len(self.time), dtype=np.float64)

        self.x = 0.0
        self.y = 0.0
        self.surfaceDrainedHydro = 0.0

        # Dimensions
        self.hFloor = 0.0
        self.hBank = 0.0
        self.hStagn = 0.0
        self.volume = 0.0
        self.surface = 0.0
        self.hi = 0.0
        self.vi = 0.0

        # inlets and outlets
        self.intletsObj = {}
        self.inlets = None
        self.inletsRaw = None

        self.directFluxObj = {}
        self.directFluxInRB = None
        self.directFluxInRB_Raw = None
        self.downstreamObj = {}
        self._outFlow = {}
        if(_outletNames != []):
            for i in range(len(_outletNames)):
                self._outFlow[_outletNames[i]]={}
                self._outFlow[_outletNames[i]]["Net"] = []
                self._outFlow[_outletNames[i]]["Raw"] = []
                self.downstreamObj[_outletNames[i]] = None

        self.rain = []

        self.qLim = None        # object to compute "l'ecretage"

        self.outletObj = None   # object to compute the outlet

        self.zData = None         # height from z-v file stored
        self.vData = None         # volume from z-v file stored
        self.zvInterpol = None

        self.timeDelay = 0.0    # [s]????? -> A vérifier!!!
        self.timeDelayObj = None

        self.peakVal = 0.0                          # [m³/s] peak value for total outFlow
        self.peakTime = None                        # datetime of the peak for total outflow -> time delay is already applied


        if(_dictRB!={}):
            # Init of the object allowing to determine the outlet flux
            tmpCounter = 0
            for element in _dictRB:
                if(_dictRB[element]['from'][key_Param.VALUE] == self.iD):
                    if(tmpCounter>0):
                        logging.error("ERROR: the same RB associated to two different caracteristics. Please check the RetentionBasin.postPro file.")
                        raise ValueError("The same RB associated to two different caracteristics. Please check the RetentionBasin.postPro file.")
                    self.dictRB = _dictRB[element]
                    tmpCounter +=1
            if(tmpCounter == 0):
                logging.error("Error: no RB associated! Please check the RetentionBasin.postPro file.")
                raise ValueError("No RB associated! Please check the RetentionBasin.postPro file.")
        elif(_directDictRB!={}):
            self.dictRB = _directDictRB
        elif(withRBDict):
            print("ERROR: Not enough elements, it lacks a least a dictionary!")
            print("Do you still want to continue [Y-YES] [N-NO]?")
            myAnswer = input("Enter your answer:")
            isOk = False
            while(not isOk):
                if(myAnswer=="Y" or myAnswer=="y"):
                    isOk = True
                    self.dictRB['type'] = {}
                    self.dictRB['type'][key_Param.VALUE] = ""
                elif(myAnswer=="N" or myAnswer=="n"):
                    raise ValueError("No answer given!")
        else:
            self.dictRB['type'] = {}
            self.dictRB['type'][key_Param.VALUE] = ""



        self.type = self.dictRB['type'][key_Param.VALUE]
        if('stagnant height' in self.dictRB):
            self.hStagn =  float(self.dictRB['stagnant height'][key_Param.VALUE])
        if(self.type == 'HighwayRB'):
            self.surface = float(self.dictRB['surface'][key_Param.VALUE])
            self.hBank = float(self.dictRB['height 2'][key_Param.VALUE])
            self.volume = self.surface * self.hBank
        elif(self.type == 'RobiernuRB'):
            self.volume = float(self.dictRB['volume'][key_Param.VALUE])
        elif(self.type == 'OrbaisRB'):
            self.volume = float(self.dictRB['volume'][key_Param.VALUE])
            try:
                zvFile = self.dictRB['Z-V file'][key_Param.VALUE]
            except:
                zvFile = ""
            if(zvFile!=""):
                zvFile = zvFile.replace("\\", "/")
                self.read_zv(zvFile)

            # self.qLim = float(self.dictRB['ecretage']['value'])
        # elif(self.type == 'HelleRB'):
        #     self.volume = float(self.dictRB['volume']['value'])
        #     print("ERROR: Not implemented yet!")
        #     sys.exit()
        elif(self.type == 'ForcedDam'):
            self.volume = float(self.dictRB['volume'][key_Param.VALUE])
            self.hi = float(self.dictRB['initial height'][key_Param.VALUE])
            self.vi = self.h_to_volume(self.hi)

            try:
                zvFile = self.dictRB['Z-V file'][key_Param.VALUE]
            except:
                zvFile = ""
            if(zvFile!=""):
                zvFile = zvFile.replace("\\", "/")

                #FIXME : Blinder la gestion des noms relatifs via une fonction
                if os.path.isabs(zvFile):
                    self.read_zv(zvFile)
                else:
                    self.read_zv(os.path.join(self.fileNameRead,zvFile))

            if("time delay" in self.dictRB):
                self.timeDelay = float(self.dictRB["time delay"][key_Param.VALUE])
        elif(self.type == "HelleRB"):
            self.volume = float(self.dictRB['volume'][key_Param.VALUE])
            try:
                zvFile = self.dictRB['Z-V file'][key_Param.VALUE]
                isOk, zvFile = check_path(zvFile, self.fileNameRead, applyCWD=True)
                if isOk<0:
                    print("ERROR : Problem in the Z-V file!")
                    zvFile = ""
            except:
                zvFile = ""
            if(zvFile!=""):
                zvFile = zvFile.replace("\\", "/")
                self.read_zv(zvFile)

        else:
            print("WARNING: This type RB was not recognised! Please check the RetentionBasin.postPro file.")


        if ("initial height" in self.dictRB):
            self.hi = float(self.dictRB['initial height'][key_Param.VALUE])
            self.vi = self.h_to_volume(self.hi)

        if("time delay" in self.dictRB):
            self.timeDelay = float(self.dictRB["time delay"][key_Param.VALUE])

        # Creation of Outlet object
        self.outletObj = Outlet(self.dictRB, _workingDir=self.fileNameRead, time=self.time)
        self.qLim = Dumping(self.dictRB)



        # if('direct inside RB' in self.myCatchment[self.iD]):
        #     if(self.myCatchment[self.iD]['direct inside RB'] != ''):
        #         self.sum_directFluxInRB()
        # self.sumHydro = self.run()
        # print(self.sumHydro)<


    def increment_level(self):
        "This procedure increment the level in the Topo dictionary"
        self.myLevel += 1


    def add_inlet(self, toPoint, name="DEFAULT"):
        "This procedure link the inlets to the object"
        self.intletsObj[name] = toPoint

        if("time delay from module" in self.dictRB):
            nameModule = self.dictRB["time delay from module"][key_Param.VALUE]
            if(toPoint.iD == nameModule):
                self.timeDelay = toPoint.timeDelay
                self.x = toPoint.x
                self.y = toPoint.y



    def add_downstreamObj(self, toPoint, name="DEFAULT", deltaTime=0.0, tolerance=0):
        """This procedure link the downstream element to the object
            tolerance indicates if the downstream objet should already exist (=0) to continue => to implement
        """
        if toPoint is not None:
            self.downstreamObj[name] = toPoint
            if(name in self.downstreamObj):
                self.downstreamObj[name] = toPoint
            else:
                logging.error("ERROR: this outlet name is not recognised!")
                logging.error("Name = ", name)
                raise ValueError("This outlet name is not recognised!")

        self._outFlow[name] = {}
        self._outFlow[name]["Net"] = []
        self._outFlow[name]["Raw"] = []
        self._outFlow[name]["delta time"] = deltaTime

        if("time delay from module" in self.dictRB):
            nameModule = self.dictRB["time delay from module"][key_Param.VALUE]
            if(toPoint.iD == nameModule):
                self.timeDelay = toPoint.timeDelay
                self.x = toPoint.x
                self.y = toPoint.y


    def add_directFluxObj(self, toPoint, name="DEFAULT"):
        "This procedure link the direct inlet elements to the object"
        self.directFluxObj[name] = toPoint

        if("time delay from module" in self.dictRB):
            nameModule = self.dictRB["time delay from module"][key_Param.VALUE]
            if(toPoint.iD == nameModule):
                self.timeDelay = toPoint.timeDelay
                self.x = toPoint.x
                self.y = toPoint.y


    def compute_hydro(self, givenDirectFluxIn=[], givenInlet=[]):
        """ This function computes the raw and real hydrographs.

            The volume filled and then the water height in the RB at time $t$ will be evaluated will depend of the flows
            at time $t-1$ exept if the

            Internal variables modified : self.inlets, self.inletsRaw,
                                        self.directFluxInRB, self.directFluxInRB_Raw,
                                        self._outFlowRaw, self._outFlow, self.filledVolume
            CAUTION: - Discussion about the ceil or the floor for the timeDelay indice!!!
                     - UPDATE 2023.1 now the outFlow are not delayed anymore !!!! -> IMPORTANT UPDATE
        """
        self.sum_inlets(givenInlet)
        self.sum_directFluxInRB(givenDirectFluxIn)
        mainNameOut = list(self._outFlow.items())[0][0]
        # In the Raw hydrograph the first outlet is considered to be the main one. Therefore the exit where the flux would go if the structure were to present
        self._outFlow[mainNameOut]["Raw"] = self.inletsRaw + self.directFluxInRB_Raw
        for iOutFlow in range(1,len(list(self._outFlow.items()))):
            nameOut = list(self._outFlow.items())[iOutFlow][0]
            self._outFlow[nameOut]["Raw"] = np.zeros(len(self.inletsRaw))

        # sizeOfHydro = len(self.time)-1
        sizeOfHydro = len(self.time)    # Size of hydro is no longer t-1 smaller than time
        # Volume of the RB filled with water
        self.filledVolume = np.zeros(sizeOfHydro, dtype=np.float64)
        for elOutFlow in self._outFlow:
            self._outFlow[elOutFlow]["Net"] =  np.zeros(sizeOfHydro)

        self.filledVolume[0] = self.h_to_volume(self.hi)
        outFlowReservoir = np.zeros(sizeOfHydro)
        for i in range(1,sizeOfHydro):
            # # To avoid a division by zero and physically correct.
            # if(self.surface == 0.0):
            #     h = 0.0
            # else:
            #     h = self.filledVolume[i-1]/self.surface
            # 1st evaluation of the outlet of the RB according to Vfilled at the previous time
            h = self.volume_to_h(self.filledVolume[i-1])
            # Qout = self.outletObj.compute(h,self.time[self.convert_index_global_to_local(i)])
            Qout = self.outletObj.compute(h,self.time[i], index=i)
            qLim = self.qLim.compute(h,self.time[i])
            Qin = self.directFluxInRB[i-1]+max(self.inlets[i-1]-qLim,0.)
            rhs = Qin - Qout
            outFlowReservoir[i-1]=Qout
            # If the volume increase => the outflow is kept (Maybe to improve!! The height can go to the upper threshold)
            if rhs>0:
                self.filledVolume[i] = self.filledVolume[i-1] + rhs*(self.time[i]-self.time[i-1])
            # If the volume is decreasing but is not enough to empty it at this time step
            elif self.filledVolume[i-1]>abs(rhs*(self.time[i]-self.time[i-1])):
                self.filledVolume[i] = self.filledVolume[i-1] + rhs*(self.time[i]-self.time[i-1])
                # if(self.surface == 0.0):
                #     h = 0.0
                # else:
                #     h = self.filledVolume[i]/self.surface
                h = self.volume_to_h(self.filledVolume[i])
                # All the values:
                    # -outlet,
                    # -ecretage,
                    # -volume,
                # will be reevaluated. Because we can go to the lower threshold.
                # Qout = self.outletObj.compute(h,self.time[self.convert_index_global_to_local(i)])
                Qout = self.outletObj.compute(h,self.time[i], index=i)
                qLim = self.qLim.compute(h,self.time[i])
                rhs = self.directFluxInRB[i-1]+max(self.inlets[i-1]-qLim,0.)-Qout
                outFlowReservoir[i-1] = Qout
                self.filledVolume[i] = self.filledVolume[i-1] + rhs*(self.time[i]-self.time[i-1])

            else:
                self.filledVolume[i] =0
                outFlowReservoir[i-1] = self.filledVolume[i-1]/((self.time[i]-self.time[i-1]))+self.directFluxInRB[i-1]+max(self.inlets[i-1]-qLim,0.)

            if self.filledVolume[i]>self.volume:
                outFlowReservoir[i-1] += (self.filledVolume[i]-self.volume)/((self.time[i]-self.time[i-1]))
                self.filledVolume[i] = self.volume

            self._outFlow = self.compute_final(outFlowReservoir[i-1],min(self.inlets[i-1],qLim),i-1)
            # self.outFlow[i-1]+=min(self.inlets[i-1],qLim)

        return self._outFlow


    def compute_one_step_hydro(self, i, givenDirectFluxIn:float=None, givenInlet:float=None):
        """ This function computes the raw and real hydrographs for one time step.

            The volume filled and then the water height in the RB at time $t$ will be evaluated will depend of the flows
            at time $t-1$ exept if the

            Internal variables modified : self.inlets, self.inletsRaw,
                                        self.directFluxInRB, self.directFluxInRB_Raw,
                                        self._outFlowRaw, self._outFlow, self.filledVolume
            CAUTION: - Discussion about the ceil or the floor for the timeDelay indice!!!
                     - UPDATE 2023.1 now the outFlow are not delayed anymore !!!! -> IMPORTANT UPDATE
        """
        self.sum_one_step_directFluxInRB(i, givenDirectFluxIn)
        self.sum_one_step_inlets(i, givenInlet)

        mainNameOut = list(self._outFlow.items())[0][0]
        # In the Raw hydrograph the first outlet is considered to be the main one. Therefore the exit where the flux would go if the structure were to present
        self._outFlow[mainNameOut]["Raw"][i] = self.inletsRaw[i] + self.directFluxInRB_Raw[i]
        for iOutFlow in range(1,len(list(self._outFlow.items()))):
            nameOut = list(self._outFlow.items())[iOutFlow][0]
            self._outFlow[nameOut]["Raw"][i] = 0.0

        # Compute
        h = self.volume_to_h(self.filledVolume[i])
        # Qout = self.outletObj.compute(h,self.time[self.convert_index_global_to_local(i)])
        Qout = self.outletObj.compute(h,self.time[i+1], index=i+1)
        qLim = self.qLim.compute(h,self.time[i+1])
        Qin = self.directFluxInRB[i-1]+max(self.inlets[i]-qLim,0.)
        rhs = Qin - Qout
        outFlowReservoir = Qout
        # If the volume increase => the outflow is kept (Maybe to improve!! The height can go to the upper threshold)
        if rhs>0:
            self.filledVolume[i+1] = self.filledVolume[i] + rhs*(self.time[i+1]-self.time[i])
        # If the volume is decreasing but is not enough to empty it at this time step
        elif self.filledVolume[i]>abs(rhs*(self.time[i+1]-self.time[i])):
            self.filledVolume[i+1] = self.filledVolume[i] + rhs*(self.time[i+1]-self.time[i])
            # if(self.surface == 0.0):
            #     h = 0.0
            # else:
            #     h = self.filledVolume[i]/self.surface
            h = self.volume_to_h(self.filledVolume[i+1])
            # All the values:
                # -outlet,
                # -ecretage,
                # -volume,
            # will be reevaluated. Because we can go to the lower threshold.
            # Qout = self.outletObj.compute(h,self.time[self.convert_index_global_to_local(i)])
            Qout = self.outletObj.compute(h,self.time[i+1], index=i+1)
            qLim = self.qLim.compute(h,self.time[i+1])
            rhs = self.directFluxInRB[i]+max(self.inlets[i]-qLim,0.)-Qout
            outFlowReservoir = Qout
            self.filledVolume[i+1] = self.filledVolume[i] + rhs*(self.time[i+1]-self.time[i])

        else:
            self.filledVolume[i+1] =0
            outFlowReservoir = self.filledVolume[i]/((self.time[i+1]-self.time[i]))+self.directFluxInRB[i]+max(self.inlets[i]-qLim,0.)

        if self.filledVolume[i+1]>self.volume:
            outFlowReservoir += (self.filledVolume[i+1]-self.volume)/((self.time[i+1]-self.time[i]))
            self.filledVolume[i+1] = self.volume

        self._outFlow = self.compute_final(outFlowReservoir,min(self.inlets[i],qLim),i)


    def init_all_inlets(self):
        """ This function initializes the inlets and directFluxInRB of the RB
            Internal variables modified: self.inlets, self.inletsRaw, self.directFluxInRB, self.directFluxInRB_Raw
        """
        self.inlets = np.zeros(len(self.time),dtype=ct.c_double, order='F')
        self.inletsRaw = np.zeros(len(self.time),dtype=ct.c_double, order='F')

        self.directFluxInRB = np.zeros(len(self.time),dtype=ct.c_double, order='F')
        self.directFluxInRB_Raw = np.zeros(len(self.time),dtype=ct.c_double, order='F')


    def sum_inlets(self, givenInlet=[]):
        """ This procedure sum all the inlets of the RB
            Caution: inlets variable is different from directFluxIn !!

            Internal variables modified: self.inlets, self.inletsRaw
        """
        if(self.intletsObj != {}):
            nameOutFlow = list(self.intletsObj.items())[0][0]
            curObj = self.intletsObj[nameOutFlow]
            # Compute the transfer time between modules
            if type(curObj) is SubBasin:
                timeInlet = curObj.timeDelay
                deltaTr = timeInlet - self.timeDelay
            else:
                # Assumption the transfer time between the 2 RB is ambiguous
                # Therefore, the transfer time is set to 0.0
                deltaTr = 0.0
            self.inlets = curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameOutFlow, lag=deltaTr)
            self.inletsRaw = curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameOutFlow, lag=deltaTr)
            for i in range(1,len(list(self.intletsObj.items()))):
                nameOutFlow = list(self.intletsObj.items())[i][0]
                curObj = self.intletsObj[nameOutFlow]
                timeInlet = curObj.timeDelay
                if type(curObj) is SubBasin:
                    timeInlet = curObj.timeDelay
                    deltaTr = timeInlet - self.timeDelay
                else:
                    # Assumption the transfer time between the 2 RB is ambiguous
                    # Therefore, the transfer time is set to 0.0
                    deltaTr = 0.0

                self.inlets += curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameOutFlow, lag=deltaTr)
                self.inletsRaw += curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameOutFlow, lag=deltaTr)
        elif(givenInlet != []):
            if(len(givenInlet)!=len(self.time)):
                logging.error("The dimension of the time array and the given inlet are not the same!")
                logging.error(f"Length obtained = {len(givenInlet)}")
                logging.error(f"Length expected = {len(self.time)}")
                raise ValueError("The dimension of the time array and the given inlet are not the same!")
            self.inlets = givenInlet
            self.inletsRaw = givenInlet
        else:
            # self.inlets = np.zeros(len(self.time)-1)        # the size of outflow will always be 1 element smaller than time (convention)
            # self.inletsRaw = np.zeros(len(self.time)-1)     # the size of outflow will always be 1 element smaller than time (convention)
            self.inlets = np.zeros(len(self.time),dtype=ct.c_double, order='F')        # the size of outflow is no longer 1 element smaller than time (convention)
            self.inletsRaw = np.zeros(len(self.time),dtype=ct.c_double, order='F')     # the size of outflow is no longer 1 element smaller than time (convention)


    def sum_directFluxInRB(self, givenDirectFluxIn=[]):
        """This procedure computes the flux going directly inside the RB

            Internal variables modified: self.directFluxInRB, self.directFluxInRB_Raw
        """
        if(self.directFluxObj != {}):
            nameOutFlow = list(self.directFluxObj.items())[0][0]
            curObj = self.directFluxObj[nameOutFlow]
            timeInlet = curObj.timeDelay
            if type(curObj) is SubBasin:
                timeInlet = curObj.timeDelay
                deltaTr = timeInlet - self.timeDelay
            else:
                # Assumption the transfer time between the 2 RB is ambiguous
                # Therefore, the transfer time is set to 0.0
                deltaTr = 0.0
            deltaTr = timeInlet - self.timeDelay
            self.directFluxInRB = curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameOutFlow, lag=deltaTr)
            self.directFluxInRB_Raw = curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameOutFlow, lag=deltaTr)
            for i in range(1,len(list(self.directFluxObj.items()))):
                nameOutFlow = list(self.directFluxObj.items())[i][0]
                curObj = self.directFluxObj[nameOutFlow]
                timeInlet = curObj.timeDelay
                if type(curObj) is SubBasin:
                    timeInlet = curObj.timeDelay
                    deltaTr = timeInlet - self.timeDelay
                else:
                    # Assumption the transfer time between the 2 RB is ambiguous
                    # Therefore, the transfer time is set to 0.0
                    deltaTr = 0.0

                try:
                    self.directFluxInRB += curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameOutFlow, lag=deltaTr)
                except:
                    print("Hello!!!! TO CHANGE!!!!")
                    nbElT = len(self.directFluxInRB)
                    nbTMP = len(self.directFluxObj[nameOutFlow].outFlow[nameOutFlow]["Net"])
                    if(nbElT==nbTMP+1):
                        tmpHydro = self.directFluxInRB.copy()
                        self.directFluxInRB = np.zeros(nbTMP)
                        self.directFluxInRB[:] = tmpHydro[:-1]
                        self.directFluxInRB += self.directFluxObj[nameOutFlow].outFlow[nameOutFlow]["Net"]
                    elif(nbTMP==nbElT+1):
                        self.directFluxInRB[:] = self.directFluxObj[nameOutFlow].outFlow[nameOutFlow]["Net"][:-1]
                    else:
                        print("Hello!!!! ERROR!!!!")

                # self.directFluxInRB_Raw += self.directFluxObj[nameOutFlow].outFlow[nameOutFlow]["Raw"]
                try:
                    self.directFluxInRB_Raw += curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameOutFlow, lag=deltaTr)
                except:
                        logging.error("ERROR : Should not be here !!!!!")
                        print("Hello!!!! TO CHANGE!!!!")
                        nbElT = len(self.directFluxInRB_Raw)
                        nbTMP = len(self.directFluxObj[nameOutFlow].outFlow[nameOutFlow]["Raw"])
                        if(nbElT==nbTMP+1):
                            tmpHydro = self.directFluxInRB_Raw.copy()
                            self.directFluxInRB_Raw = np.zeros(nbTMP)
                            self.directFluxInRB_Raw[:] = tmpHydro[:-1]
                            self.directFluxInRB_Raw += self.directFluxObj[nameOutFlow].outFlow[nameOutFlow]["Raw"]
                        elif(nbTMP==nbElT+1):
                            self.directFluxInRB_Raw[:] = self.directFluxObj[nameOutFlow].outFlow[nameOutFlow]["Raw"][:-1]
                        else:
                            print("Hello!!!! ERROR!!!!")

        elif(givenDirectFluxIn != []):
            # FIXME The following line to potentially change !!!
            if(len(givenDirectFluxIn)!=len(self.time)):
                logging.error("The dimension of the time array and the given inlet are not the same!")
                logging.error("Length optained = ", len(givenDirectFluxIn))
                logging.error("Length expected = ", len(self.time))
                raise ValueError("The dimension of the time array and the given inlet are not the same!")
            self.directFluxInRB = givenDirectFluxIn
            self.directFluxInRB_Raw = givenDirectFluxIn
        else:
            # self.directFluxInRB = np.zeros(len(self.time)-1)
            # self.directFluxInRB_Raw = np.zeros(len(self.time)-1)
            self.directFluxInRB = np.zeros(len(self.time), dtype=ct.c_double, order='F')
            self.directFluxInRB_Raw = np.zeros(len(self.time), dtype=ct.c_double, order='F')


    def sum_one_step_inlets(self, i, givenInlet:float=None):
        if self.intletsObj != {}:
            nameOutFlow = list(self.intletsObj.items())[0][0]
            curObj = self.intletsObj[nameOutFlow]
            # Compute the transfer time between modules
            if type(curObj) is SubBasin:
                timeInlet = curObj.timeDelay
                deltaTr = timeInlet - self.timeDelay
            else:
                # Assumption the transfer time between the 2 RB is ambiguous
                # Therefore, the transfer time is set to 0.0
                deltaTr = 0.0
            self.inlets[i] = curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameOutFlow, lag=deltaTr)[i]
            self.inletsRaw[i] = curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameOutFlow, lag=deltaTr)[i]
            for i in range(1,len(list(self.intletsObj.items()))):
                nameOutFlow = list(self.intletsObj.items())[i][0]
                curObj = self.intletsObj[nameOutFlow]
                timeInlet = curObj.timeDelay
                if type(curObj) is SubBasin:
                    timeInlet = curObj.timeDelay
                    deltaTr = timeInlet - self.timeDelay
                else:
                    # Assumption the transfer time between the 2 RB is ambiguous
                    # Therefore, the transfer time is set to 0.0
                    deltaTr = 0.0

                self.inlets[i] += curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameOutFlow, lag=deltaTr)[i]
                self.inletsRaw[i] += curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameOutFlow, lag=deltaTr)[i]
        elif(givenInlet is not None):
            self.inlets[i] = givenInlet
            self.inletsRaw[i] = givenInlet
        else:
            self.inlets[i] = 0.0
            self.inletsRaw[i] = 0.0


    def sum_one_step_directFluxInRB(self, i, givenDirectFluxIn:float=None):
        """This procedure computes the flux going directly inside the RB

            Internal variables modified: self.directFluxInRB, self.directFluxInRB_Raw
        """
        if(self.directFluxObj != {}):
            nameOutFlow = list(self.directFluxObj.items())[0][0]
            curObj = self.directFluxObj[nameOutFlow]
            timeInlet = curObj.timeDelay
            if type(curObj) is SubBasin:
                timeInlet = curObj.timeDelay
                deltaTr = timeInlet - self.timeDelay
            else:
                # Assumption the transfer time between the 2 RB is ambiguous
                # Therefore, the transfer time is set to 0.0
                deltaTr = 0.0
            deltaTr = timeInlet - self.timeDelay
            self.directFluxInRB[i] = curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameOutFlow, lag=deltaTr)[i]
            self.directFluxInRB_Raw[i] = curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameOutFlow, lag=deltaTr)[i]
            for i in range(1,len(list(self.directFluxObj.items()))):
                nameOutFlow = list(self.directFluxObj.items())[i][0]
                curObj = self.directFluxObj[nameOutFlow]
                timeInlet = curObj.timeDelay
                if type(curObj) is SubBasin:
                    timeInlet = curObj.timeDelay
                    deltaTr = timeInlet - self.timeDelay
                else:
                    # Assumption the transfer time between the 2 RB is ambiguous
                    # Therefore, the transfer time is set to 0.0
                    deltaTr = 0.0

                self.directFluxInRB[i] += curObj.get_outFlow(typeOutFlow="Net", whichOutFlow=nameOutFlow, lag=deltaTr)[i]
                self.directFluxInRB_Raw[i] += curObj.get_outFlow(typeOutFlow="Raw", whichOutFlow=nameOutFlow, lag=deltaTr)[i]



    def plot(self, workingDir, plotRaw=True, axis="Hours",rangeData=[], deltaMajorTicks=24.0*3600.0, deltaMinorTicks=3600.0, tzPlot=0, unitReservoir="[m^3]"):
        """ This procedure plots:
        - the inlets: in color chosen randomly by matplotlib
        - DirectIn : in color chosen randomly by matplotlib and in '-.' lines
        - the outlet: in black solid line
        - the raw outlet: in black dashed line
        """

        # x = self.time/3600.0
        if(axis=="Hours"):
            x = (self.time[:-1]-self.time[0])/3600.0
        else:
            tzDelta = datetime.timedelta(seconds=tzPlot*3600.0)
            timeDelayDelta = datetime.timedelta(seconds=self.timeDelay)
            beginDate = datetime.datetime.fromtimestamp(self.time[0], tz=datetime.timezone.utc)+tzDelta
            endDate = datetime.datetime.fromtimestamp(self.time[-1], tz=datetime.timezone.utc)+tzDelta
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

        fig = plt.figure(figsize=(8.3, 11.7))
        ax1 = plt.subplot(2,1,1)

        # plt.subplot(2,1,1)
        # ax1.grid()

        if(axis=="Hours"):
            ax1.set_xlabel('Temps [h]', fontproperties=font11)
        else:
            ax1.set_xlabel('Date (GMT+'+str(tzPlot)+')', fontproperties=font11)
        ax1.set_ylabel('Débits [m³/s]', fontproperties=font11)
        fig.legend(loc="upper right")
        fig.suptitle(self.name + " Hydrogrammes écrêtés", fontproperties=font14)



        for iInlet in self.intletsObj:

            y = self.intletsObj[iInlet].get_outFlow_global(typeOutFlow="Net", whichOutFlow=iInlet)
            name = self.intletsObj[iInlet].name + " " + iInlet
            if(axis=="Hours"):
                ax1.plot(x, y, label = name)
            else:
                x_plot = ph.check_drange_bug(x_date, y)
                ax1.plot_date(x_plot, y, '-', label = name)
        for iInlet in self.directFluxObj :
            y = self.directFluxObj[iInlet].get_outFlow_global(typeOutFlow="Net", whichOutFlow=iInlet)
            name = self.directFluxObj[iInlet].name + " " + iInlet
            if(name=="ss 18" or name=="ss 19"):
                name = "Qin BV"

            if(axis=="Hours"):
                ax1.plot(x, y, '-.', label = name)
            else:
                x_plot = ph.check_drange_bug(x_date, y)
                ax1.plot_date(x_plot, y, '-.', label = name)

        for iOutFlow in self._outFlow:
            y = self.get_outFlow_global(typeOutFlow="Net", whichOutFlow=iOutFlow)

            if(axis=="Hours"):
                ax1.plot(x, y, label = self.name+" "+iOutFlow, color='k')
            else:
                x_plot = ph.check_drange_bug(x_date, y)
                ax1.plot_date(x_plot, y, '-', label = self.name+" "+iOutFlow, color='k')

        if(plotRaw):
            nameMainOut = list(self._outFlow.items())[0][0]
            y = self.get_outFlow_global(typeOutFlow="Raw", whichOutFlow=nameMainOut)

            if(axis=="Hours"):
                ax1.plot(x, y, '--', label = self.name+' Raw', color='k')
            else:
                x_plot = ph.check_drange_bug(x_date, y)
                ax1.plot(x_plot, y, '--', label = self.name+' Raw', color='k')

        if(axis=="Hours"):
            ax1.set_xlim(x[0], x[len(x)-1])
            ax1.grid()

        else:
            ax1.set_xlim(rangeData[0], rangeData[1])


            for label in ax1.get_xticklabels():
                label.set_rotation(30)
                label.set_horizontalalignment('right')
            ax1.tick_params(axis='y',labelcolor='k')


            if(deltaMajorTicks>0):
                majorTicks = HourLocator(interval=math.floor(deltaMajorTicks/3600))
                # majorTicks = drange(beginDate, endDate, deltaTimeMajorTicks)
                # ax1.set_xticks(majorTicks)
                ax1.xaxis.set_major_locator(majorTicks)
                ax1.grid(which='major', alpha=1.0)


                if(deltaMinorTicks>0):
                    # deltaTimeMinorTicks = datetime.timedelta(seconds=deltaMinorTicks)
                    # minorTicks = drange(beginDate, endDate, deltaTimeMinorTicks)
                    # ax1.set_xticks(minorTicks, minor=True)
                    # ax1.grid(which='minor', alpha=0.2)
                    ax1.minorticks_on()
                    minorTicks = MicrosecondLocator(interval=deltaMinorTicks*1E6)
                    ax1.xaxis.set_minor_locator(minorTicks)
                    # plt.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
                    ax1.grid(which='minor', alpha=0.2)
            else:
                ax1.grid()


        fig.legend(prop=font11)
        try:
            fig.savefig(workingDir+'PostProcess/QT_HydroEcrete_'+self.name+'.pdf')
        except:
            fig.savefig(workingDir+'/QT_HydroEcrete_'+self.name+'.pdf')

        ax2 = plt.subplot(2,1,2)


        ax2.set_xlabel('Temps [h]', fontproperties=font11)
        fig.legend(loc="upper right", prop=font11)
        fig.suptitle("Volume cumulé", fontproperties=font11)
        if unitReservoir == "[m^3]":
            ax2.set_ylabel('Volume [m³]', fontproperties=font11)
            y = self.filledVolume
        else:
            ax2.set_ylabel('Height [m]', fontproperties=font11)
            myH = np.zeros(len(self.filledVolume))
            for ii in range(len(self.filledVolume)):
                myH[ii] =  self.volume_to_h(self.filledVolume[ii])
            y = myH


        if(axis=="Hours"):
            ax2.plot(x, y, label = self.name)
            if unitReservoir == "[m^3]":
                y = self.volume*np.ones(len(x))
            else:
                y = self.hBank*np.ones(len(x))
        else:
            x_plot = ph.check_drange_bug(x_date, y)
            ax2.plot_date(x_plot, y, '-', label = self.name)
            if unitReservoir == "[m^3]":
                y = self.volume*np.ones(len(x_date))
            else:
                y = self.hBank*np.ones(len(x_date))
        if(axis=="Hours"):
            if unitReservoir == "[m^3]":
                ax2.plot(x, y, '--', label = "Volume max")
            else:
                ax2.plot(x, y, '--', label = "Height max")
            ax2.set_xlim(x[0], x[len(x)-1])
            ax2.grid()
        else:
            if unitReservoir == "[m^3]":
                x_plot = ph.check_drange_bug(x_date, y)
                ax2.plot_date(x_plot, y, '--', label = "Volume max")
            else:
                x_plot = ph.check_drange_bug(x_date, y)
                ax2.plot_date(x_plot, y, '--', label = "Height max")
            ax2.set_xlim(rangeData[0], rangeData[1])


            for label in ax2.get_xticklabels():
                label.set_rotation(30)
                label.set_horizontalalignment('right')
            ax2.tick_params(axis='y',labelcolor='k')

            if(deltaMajorTicks>0):
                majorTicks = HourLocator(interval=math.floor(deltaMajorTicks/3600))
                ax2.xaxis.set_major_locator(majorTicks)
                ax2.grid(which='major', alpha=1.0)


                if(deltaMinorTicks>0):
                    ax2.minorticks_on()
                    minorTicks = MicrosecondLocator(interval=deltaMinorTicks*1E6)
                    ax2.xaxis.set_minor_locator(minorTicks)
                    ax2.grid(which='minor', alpha=0.2)
            else:
                ax2.grid()

        fig.legend(prop=font11)
        fig.savefig(workingDir+'PostProcess'+self.name+'.pdf')




    def plot_outlet(self, Measures=None, rangeData=[], yrangeRain=[], yrangeData=[], ylabel=[],addData=[], dt_addData=[], beginDates_addData=[], endDates_addData=[],\
                    label_addData=[], color_addData=[],factor=1.5, graph_title='', withEvap=False, writeFile='', withDelay=True, deltaMajorTicks=-1,deltaMinorTicks=-1, tzPlot=0, figure=None):

        print("plot_outlet() function for RB -> TO DO !!!")

        return


    def add_rain(self, workingDir, tzDelta=datetime.timedelta(hours=0)):
        """ This function returns the a time array and a array containing the sum of all the rain in the inlets
            Value changed :  self.rain
        """
        if(self.directFluxObj == {}):
            nameInit = list(self.intletsObj.items())[0][0]
            rain = np.zeros(len(self.intletsObj[nameInit].rain))
        else:
            nameInit = list(self.directFluxObj.items())[0][0]
            rain = np.zeros(len(self.directFluxObj[nameInit].rain))
        for iInlet in self.intletsObj:
            rain += self.intletsObj[iInlet].rain
        for iInlet in self.directFluxObj:
            rain += self.directFluxObj[iInlet].rain
        self.rain = rain
        return self.time


    def volume_to_h(self, volume):

        if(volume==0.0):
            h=0
        elif(self.zData is not None):
            if(volume>max(self.zvVtoHInterpol.x)):
                # h = max(self.zvVtoHInterpol.y)
                slope = (self.zvVtoHInterpol.y[-1]-self.zvVtoHInterpol.y[-2])/(self.zvVtoHInterpol.x[-1]-self.zvVtoHInterpol.x[-2])
                h = slope*(volume-self.zvVtoHInterpol.x[-1])+max(self.zvVtoHInterpol.y)
            else:
                h = self.zvVtoHInterpol(volume)
        else:
            if(self.surface == 0.0):
                h = 0.0
            else:
                h = volume/self.surface

        return h


    def h_to_volume(self, h):

        if(h==0):
            vol = 0
        elif(self.zData is not None):
            if(h>max(self.zvHtoVInterpol.x)):
                # h_tmp=max(self.zvHtoVInterpol.x)
                # vol = self.zvHtoVInterpol(h_tmp)

                slope = (self.zvHtoVInterpol.y[-1]-self.zvHtoVInterpol.y[-2])/(self.zvHtoVInterpol.x[-1]-self.zvHtoVInterpol.x[-2])
                vol = slope*(h-self.zvHtoVInterpol.x[-1])+max(self.zvHtoVInterpol.y)
            else:
                vol = self.zvHtoVInterpol(h)
        else:
            vol = h*self.surface

        return vol


    def read_zv(self, fileName, typeOfInterpolation='linear'):

        if os.path.exists(fileName):
            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = list(data_reader)
            matrixData = np.array(list_data).astype("float")
            self.zData = matrixData[:,0]
            self.vData = matrixData[:,1]

            self.zvVtoHInterpol = interp1d(self.vData,self.zData, kind=typeOfInterpolation, assume_sorted=True, fill_value='extrapolate')  # kind is 'linear' by default in interp1d
            self.zvHtoVInterpol = interp1d(self.zData,self.vData, kind=typeOfInterpolation, assume_sorted=True, fill_value='extrapolate')


    def convert_index_global_to_local(self, i, lagTime=0.0):

        logging.error("This function is obsolate since version" + str(cst.VERSION_WOLFHYDRO_2023_1))

        index = math.floor(self.timeDelay/(self.time[1]-self.time[0]))
        index = i - index

        if(index<0):
            index = 0

        return index



    def convert_data_global_to_local(self, dataGlob):

        logging.error("This function is obsolate since version" + str(cst.VERSION_WOLFHYDRO_2023_1))

        dataLoc = np.zeros(len(dataGlob))

        myIndex = math.floor(self.timeDelay/(self.time[1]-self.time[0]))
        if(myIndex==0):
            dataLoc = dataGlob[:]
        elif(myIndex<len(dataLoc)):
            dataLoc[:-myIndex] = dataGlob[myIndex:]
        else:
            logging.error("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
            raise ValueError("The simulation time is not long enough for this subbasin to be taken into account")

        return dataLoc




    def convert_index_global_to_other_global(self, i, timeDelayOut=0.0, timeDelta=0.0):

        logging.error("This function is obsolate since version" + str(cst.VERSION_WOLFHYDRO_2023_1))

        index = math.floor((self.timeDelay-timeDelayOut-timeDelta)/(self.time[1]-self.time[0]))
        index = i - index

        # if(index<0):
        #     index = 0

        return index



    def convert_data_global_to_other_global(self, vector, timeDelayOut=0.0, timeDelta=0.0):

        myIndex = self.convert_data_global_to_other_global(0, timeDelayOut=timeDelayOut, timeDelta=timeDelta)

        result = np.zeros(len(vector))
        if(myIndex==0):
            result = vector[:]
        elif(abs(myIndex)<len(vector)):
            if(myIndex>0):
                result[:-myIndex] = vector[myIndex:]
            else:
                result[myIndex:] = vector[:-myIndex]
        else:
            raise ValueError("The simulation time is not long enough for this subbasin to be taken into account")

        return result



    def convert_time_global_to_local(self, time):

        logging.warning("This function is operational but obsolate since version" + str(cst.VERSION_WOLFHYDRO_2023_1))

        realTime = time - self.timeDelay

        return realTime




    def get_outFlow(self, whichOutFlow="", typeOutFlow="Net", unit="m3/s", lag:float=0.0):

        myOutFlow = np.zeros(len(self.time),dtype=ct.c_double, order='F')

        if(whichOutFlow==""):
            nameOutFlow = list(self._outFlow.items())[0][0]
        else:
            nameOutFlow = whichOutFlow

        if lag < 0.0:
            logging.warning("TimeDelay difference is negative!")
            logging.warning("Therefore, lag will be imposed to zero!")
            lag = 0.0

        if "delta time" in self._outFlow[nameOutFlow]:
            timeDelta = self._outFlow[nameOutFlow]["delta time"]
            lag += timeDelta


        index = math.floor(lag/(self.time[1]-self.time[0]))

        curOutFlow = self._outFlow[nameOutFlow][typeOutFlow]

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
            if self.surfaceDrainedHydro==0.0:
                logging.error("ERROR: the surface drained = 0! Not possible to express the outFlow in mm/s!")
                raise ValueError("ERROR: the surface drained = 0! Not possible to express the outFlow in mm/s!")
            myOutFlow *= 3.6/self.surfaceDrainedHydro


        return myOutFlow


    def get_outFlow_noDelay(self, whichOutFlow="", unit="m3/s"):
        """
        This function returns the total outlet of the basin and considers t0=0 at the outlet of the
        subbasin without considering timeDelay (the time of the real outlet of the whole potential catchment)
        """
        logging.warning("This function 'get_outFlow_noDelay' is operational but obsolate since version" + str(cst.VERSION_WOLFHYDRO_2023_1))

        # if(whichOutFlow==""):
        #     nameOutFlow = list(self.outFlow.items())[0][0]
        #     outFlowOut = self.outFlow[nameOutFlow]["Net"]
        # else:
        #     outFlowOut = self.outFlow[whichOutFlow]["Net"]

        # tmpHydro = np.zeros(len(outFlowOut))
        # index = math.floor(self.timeDelay/self.deltaT)
        # if(index==0):
        #     tmpHydro = outFlowOut
        # elif(index<len(outFlowOut)):
        #     tmpHydro[:-index] = outFlowOut[index:]
        # else:
        #     print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
        #     sys.exit()

        # if unit=='mm/h':
        #     if self.surfaceDrainedHydro==0.0:
        #         print("ERROR: the surface drained = 0! Not possible to express the outFlow in mm/s!")
        #         sys.exit()
        #     tmpHydro *= 3.6/self.surfaceDrainedHydro
        # return tmpHydro
        return self.get_outFlow(whichOutFlow=whichOutFlow, typeOutFlow="Net", unit=unit)



    def get_outFlowRaw_noDelay(self, whichOutFlow="", unit="m3/s"):
        """
        This function returns the total raw outlet of the basin and considers t0=0 at the outlet of the
        subbasin without considering timeDelay (the time of the real outlet of the whole potential catchment)
        """

        logging.warning("This function 'get_outFlowRaw_noDelay' is operational but obsolate since version" + str(cst.VERSION_WOLFHYDRO_2023_1))

        # if(whichOutFlow==""):
        #     nameOutFlow = list(self.outFlow.items())[0][0]
        #     outFlowOut = self.outFlow[nameOutFlow]["Raw"]
        # else:
        #     outFlowOut = self.outFlow[whichOutFlow]["Raw"]

        # tmpHydro = np.zeros(len(outFlowOut))
        # index = math.floor(self.timeDelay/self.deltaT)
        # if(index==0):
        #     tmpHydro = outFlowOut
        # elif(index<len(outFlowOut)):
        #     tmpHydro[:-index] = outFlowOut[index:]
        # else:
        #     print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
        #     sys.exit()

        # if unit=='mm/h':
        #     if self.surfaceDrainedHydro==0.0:
        #         print("ERROR: the surface drained = 0! Not possible to express the outFlow in mm/s!")
        #         sys.exit()
        #     tmpHydro *= 3.6/self.surfaceDrainedHydro


        # return tmpHydro

        return self.get_outFlow(whichOutFlow=whichOutFlow, typeOutFlow="Raw", unit=unit)


    def get_inlets_noDelay(self, unit='m3/s')->np.ndarray:
        """
        This function returns the total inlets of the basin and considers t0=0 at the outlet of the
        subbasin without considering timeDelay (the time of the real outlet of the whole potential catchment)
        """

        logging.warning("This function 'get_inlets_noDelay()' is operational but obsolate since version" + str(cst.VERSION_WOLFHYDRO_2023_1))
        logging.warning("Please use the function 'get_inlets()' instead")

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

        # return tmpHydro

        return self.get_inlets(unit=unit)


    def get_inlets(self, unit:str='m3/s', lag:float=0.0):

        if lag < 0.0:
            logging.error("TimeDelay difference cannot be negative for a SubBasin!!")
            logging.warning("Therefore, lag will be imposed to zero! This might create some mistakes!")
            lag = 0.0

        myInlet = np.zeros(len(self.inlets),dtype=ct.c_double, order='F')
        index = math.floor(lag/(self.time[1]-self.time[0]))

        if(index==0):
            myInlet = self.inlets.copy()
        elif(index<len(myInlet)):
            myInlet[index:] = self.inlets[:-index].copy()
        else:
            logging.error("Warning: the simulation time is not long enough for this subbasin to be taken into account")
            logging.error("Error informations : ")
            logging.error("Function name : get_inlets()")
            logging.error("index = " + str(index))
            logging.error("len(myOutFlow) = " + str(len(myInlet)))
            logging.error("Lag = " + str(lag))
            return myInlet

        if unit=='mm/h':
            myInlet *= 3.6/self.surfaceDrainedHydro

        return myInlet


    def get_direct_insideRB_inlets(self, unit:str='m3/s', lag:float=0.0)->np.ndarray:

        if lag < 0.0:
            logging.error("TimeDelay difference cannot be negative for a SubBasin!!")
            logging.warning("Therefore, lag will be imposed to zero! This might create some mistakes!")
            lag = 0.0

        direct_inlets = np.zeros(len(self.directFluxInRB),dtype=ct.c_double, order='F')
        index = math.floor(lag/(self.time[1]-self.time[0]))

        if(index==0):
            direct_inlets = self.directFluxInRB.copy()
        elif(index<len(direct_inlets)):
            direct_inlets[index:] = self.directFluxInRB[:-index].copy()
        else:
            logging.error("Warning: the simulation time is not long enough for this subbasin to be taken into account")
            logging.error("Error informations : ")
            logging.error("Function name : get_inlets()")
            logging.error("index = " + str(index))
            logging.error("len(myOutFlow) = " + str(len(direct_inlets)))
            logging.error("Lag = " + str(lag))
            return direct_inlets

        if unit=='mm/h':
            logging.warning("Arguable way to convert in mm/h, there is ambiguity!")
            direct_inlets *= 3.6/self.surfaceDrainedHydro

        return direct_inlets


    def write_height_reservoir(self, workingDir):

        myH = np.zeros(len(self.filledVolume))
        for ii in range(len(self.filledVolume)):
            myH[ii] =  self.volume_to_h(self.filledVolume[ii])

        DataWrite = []
        for ii in range(len(self.filledVolume)):
            dateData = datetime.datetime.fromtimestamp(self.time[ii]-self.timeDelay,tz=datetime.timezone.utc)
            strDated = dateData.strftime("%d/%m/%Y %H:%M:%S")
            DataWrite.append([strDated, myH[ii]])

        fname=os.path.join(workingDir,self.name+'_H.csv')
        if os.path.exists(fname):
            f = open(fname, 'w')
        writer = csv.writer(f, delimiter="\t")
        for row in DataWrite:
            writer.writerow(row)




    def compute_final(self, Qres, Qstream, step):

        mainNameOut = list(self._outFlow.items())[0][0]
        if(self.type == "HelleRB"):
            # Natural exit
            self._outFlow[mainNameOut]["Net"][step] = Qres

            # Artificial exit
            nameArtificialExit = list(self._outFlow.items())[1][0]
            self._outFlow[nameArtificialExit]["Net"][step] = Qstream
            # timeDelayNextRB = self.downstreamObj[nameArtificialExit].timeDelay
            # timeDelta = self._outFlow[nameArtificialExit]["delta time"]
            # newStep = self.convert_index_global_to_other_global(step,timeDelayOut=timeDelayNextRB,timeDelta=timeDelta)
            # if(newStep>0 and newStep<len(self._outFlow[nameArtificialExit]["Net"])):
            #     self._outFlow[nameArtificialExit]["Net"][newStep] = Qstream

        else:
            self._outFlow[mainNameOut]["Net"][step] = Qstream + Qres


        return self._outFlow


    def get_surface_proportions(self, show=True):

        myNames = []
        mySurf = []
        for element in self.intletsObj:
            curObj = self.intletsObj[element]
            curName, curSurf = curObj.get_surface_proportions(show=False)
            myNames.append(curName)
            mySurf.append(curSurf)

        if show==True:
            print("To DO!!!")()



    def find_outFlow_peak(self, whichOutFlow=""):

        myOutFlow = self.get_outflow(typeOutFlow="Net", whichOutFlow=whichOutFlow)

        maxIndex = np.argmax(myOutFlow)
        maxValue = myOutFlow[maxIndex]
        maxTime = self.time[maxIndex]
        maxDatetime = datetime.datetime.fromtimestamp(maxTime, tz=datetime.timezone.utc)

        self.peakVal = maxValue
        self.peakTime = maxDatetime



    def get_outFlow_peak(self, noDelay=False, whichOutFlow=""):

        if(self.peakVal==0.0 or self.peakTime is None):
            self.find_outFlow_peak(whichOutFlow=whichOutFlow)

        maxValue = self.peakVal
        maxDatetime = self.peakTime

        if(noDelay):
            detlaTimeDelay = datetime.timedelta(seconds=self.timeDelay)
            maxDatetime -= detlaTimeDelay

        return maxValue, maxDatetime





    def compute_Q_from_V(self, givenDirectFluxIn=[], givenInlet=[], average_steps=1):
        """ This function computes the raw and real hydrographs.

            The volume filled and then the water height in the RB at time $t$ will be evaluated will depend of the flows
            at time $t-1$ exept if the

            Internal variables modified : self.inlets, self.inletsRaw,
                                        self.directFluxInRB, self.directFluxInRB_Raw,
                                        self.outFlowRaw, self.outFlow, self.filledVolume
        """
        self.sum_inlets(givenInlet)
        self.sum_directFluxInRB(givenDirectFluxIn)
        mainNameOut = list(self._outFlow.items())[0][0]
        # In the Raw hydrograph the first outlet is considered to be the main one. Therefore the exit where the flux would go if the structure were to present
        self._outFlow[mainNameOut]["Raw"] = self.inletsRaw + self.directFluxInRB_Raw

        # relVol useful to reduce the round errors in derivative computation to get dVdt
        relVol = self.relative_filledVolume
        for iOutFlow in range(1,len(list(self._outFlow.items()))):
            nameOut = list(self._outFlow.items())[iOutFlow][0]
            self._outFlow[nameOut]["Raw"] = np.zeros(len(self.inletsRaw), dtype=ct.c_double, order='F')

        sizeOfHydro = len(self.time)
        for elOutFlow in self._outFlow:
            self._outFlow[elOutFlow]["Net"] =  np.zeros(sizeOfHydro, dtype=ct.c_double, order='F')

        outFlowReservoir = np.zeros(sizeOfHydro, dtype=ct.c_double, order='F')
        for i in range(1,sizeOfHydro):

            h = self.volume_to_h(self.filledVolume[i-1])
            qLim = self.qLim.compute(h,self.time[i])

            dVdt = self.compute_derivative(relVol, i, nbStep=average_steps)
            Qin = self.directFluxInRB[i-1]+max(self.inlets[i-1]-qLim,0.)
            Qout = -(dVdt-Qin)

            outFlowReservoir[i-1] = Qout

            # If the volume is greater than the max capacity of reservoir :
            # filledVolume is corrected to be max outflow, howerver as dVdt is based on relative Volume difference
            # => the outFlow computation is not influenced!
            if self.filledVolume[i]>self.volume:
                logging.warning("Volume greater than the max capacity of the reservoir!")
                # outFlowReservoir[i-1] += (self.filledVolume[i]-self.volume)/((self.time[i]-self.time[i-1]))
                self.filledVolume[i] = self.volume

            self._outFlow = self.compute_final(outFlowReservoir[i-1],min(self.inlets[i-1],qLim),i-1)


        return self._outFlow



    def read_volume(self, fileName:str, tzDelta=datetime.timedelta(hours=0)):

        print("Reading the measurements volume file...")

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
        # Init of the outflow array
        timeInterval = self.dateEnd-self.dateBegin
        height = np.zeros(int(timeInterval.total_seconds()/self.deltaT))
        timeArray = np.zeros(int(timeInterval.total_seconds()/self.deltaT)+1)

        # From the measurements file, we will only read the desired data and save it in outflow
        prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), tzinfo=datetime.timezone.utc)
        prevDate -= tzDelta
        index = 0
        add1Hour = datetime.timedelta(hours=1)
        secondsInDay = 24*60*60

        # Verification
        if(datetime.datetime.timestamp(prevDate)>datetime.datetime.timestamp(self.dateBegin)):
            logging.error("ERROR: the first hydro data element is posterior to dateBegin!")
            raise ValueError("ERROR: the first hydro data element is posterior to dateBegin!")

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
                datetime.datetime.timestamp(currDate)<datetime.datetime.timestamp(self.dateEnd)):
                    height[index] = matrixData[i][4]
                    diffDate = currDate - prevDate
                    diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                    timeArray[index] = datetime.datetime.timestamp(currDate)
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
                datetime.datetime.timestamp(currDate)<datetime.datetime.timestamp(self.dateEnd)):
                    if(matrixData[i][6]<0):
                        height[index] = 0.0
                    else:
                        height[index] = matrixData[i][6]
                    height[index] = matrixData[i][6]
                    diffDate = currDate - prevDate
                    diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                    timeArray[index] = datetime.datetime.timestamp(currDate)
                    index += 1
        # The last date is not taken into account in hydro as the last date rain and evap is needed for implicit simulations
        diffDate = currDate - prevDate
        # Add the last element in the time matrix as its size is 1 element bigger than outlet
        timeArray[-1] = timeArray[-2] + diffTimeInSeconds
        if(self.deltaT!=diffDate.seconds):
            logging.error("ERROR: The last timestep in hydro data does not coincide with the one expected!")
            raise ValueError("ERROR: The last timestep in hydro data does not coincide with the one expected!")
        # Save time array if it does not exist yet
        # Otherwise, check the consistency of the array with the time array of the object
        if(self.time is None):
            self.time=timeArray
        elif(self.time.all()!=timeArray.all()):
            logging.error("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")
            raise ValueError("ERROR: the dates read are not consitent with the dates already recored in this subbasin!")

        volume = np.array([self.h_to_volume(i) for i in height])

        return timeArray, volume



    # def compute_Qout_from_V(self, refVolume, indexSimul, indexData):

    #     # # To Complete !!!!
    #     if(indexData<3):
    #         vm1 = refVolume[indexData-1]
    #         vi = refVolume[indexData]
    #     else:
    #         vm1 = (refVolume[indexData-3]+refVolume[indexData-2]+refVolume[indexData-1])/3
    #         vi = (refVolume[indexData-2]+refVolume[indexData-1]+refVolume[indexData])/3

    #     Qout = (vi-vm1) / (self.time[indexSimul]-self.time[indexSimul-1])
    #     # Qout = (refVolume[indexData] - refVolume[indexData-1]) / (self.time[indexSimul]-self.time[indexSimul-1])

    #     return Qout


    # def compute_Qout_from_V_mean(self, refVolume, indexData ,indexSimul=None, nbStep=1):

    #     if indexSimul is None:
    #         indexSimul


    #     # To Complete !!!!
    #     if(indexData<nbStep):
    #         vim1 = refVolume[indexData-1]
    #         vi = refVolume[indexData]
    #     else:
    #         vim1 = (np.sum(refVolume[indexData-nbStep:indexData]))/nbStep
    #         vi = (np.sum(refVolume[indexData-nbStep+1:indexData+1]))/nbStep

    #     Qout = -(vi-vim1) / (self.time[indexSimul]-self.time[indexSimul-1])
    #     # Qout = (refVolume[indexData] - refVolume[indexData-1]) / (self.time[indexSimul]-self.time[indexSimul-1])

    #     return Qout

    def compute_derivative(self, data, indexData ,indexSimul=None, nbStep=1):

        if indexSimul is None:
            indexSimul = indexData

        if indexData<nbStep :
            dim1 = data[indexData-1]
            di = data[indexData]
        else:
            dim1 = (np.sum(data[indexData-nbStep:indexData]))/nbStep
            di = (np.sum(data[indexData-nbStep+1:indexData+1]))/nbStep

        dXdt = (di-dim1) / (self.time[indexSimul]-self.time[indexSimul-1])

        return dXdt


    def construct_surfaceDrainedHydro(self):
        """
        Calculates the total surface drained hydrology by summing up the surface drained hydrology values
        from the directFluxObj and intletsObj modules.
        Cautions: when there are several outflows in a module, the surfaceDrainedHydro is added only once,
        towards the natural outlet of the module (by convention the first outflow).

        Returns:
            None
        """

        self.surfaceDrainedHydro = 0.0

        for key, cur_module in self.directFluxObj.items():
            names = cur_module.get_outFlow_names()
            if len(names)==1:
                self.surfaceDrainedHydro += cur_module.surfaceDrainedHydro
            else:
                if names[0] == key:
                    self.surfaceDrainedHydro += cur_module.surfaceDrainedHydro

        for key, cur_module in self.intletsObj.items():
            names = cur_module.get_outFlow_names()
            if len(names)==1:
                self.surfaceDrainedHydro += cur_module.surfaceDrainedHydro
            else:
                if names[0] == key:
                    self.surfaceDrainedHydro += cur_module.surfaceDrainedHydro


    def unuse(self, mask=[]):

        self.alreadyUsed = False
        for element in self.intletsObj:
            self.intletsObj[element].unuse(mask=mask)

        for element in self.directFluxObj:
            self.directFluxObj[element].unuse(mask=mask)


    def activate(self, effSubs:list=[], effSubsSort:list=[], mask:list=[], onlyItself:bool=False):

        curSub = effSubs
        curSubSort = effSubsSort
        if self.alreadyUsed == False:
            self.alreadyUsed = True
            for element in self.intletsObj:
                curSub, curSubSort = self.intletsObj[element].activate(mask=mask, effSubs=curSub, effSubsSort=curSubSort, onlyItself=onlyItself)

            for element in self.directFluxObj:
                curSub, curSubSort = self.directFluxObj[element].activate(mask=mask, effSubs=curSub, effSubsSort=curSubSort, onlyItself=onlyItself)


        return curSub, curSubSort


    def reset_timeDelay(self, keepDelta=False, keepDeltaAll=False, upStreamTime=0.0):

        self.timeDelay = 0.0
        for element in self.intletsObj:
            self.intletsObj[element].reset_timeDelay(keepDelta=keepDelta, keepDeltaAll=keepDeltaAll,upStreamTime=upStreamTime)

        for element in self.directFluxObj:
            self.directFluxObj[element].reset_timeDelay(keepDelta=keepDelta, keepDeltaAll=keepDeltaAll, upStreamTime=upStreamTime)

        self.update_timeDelay()


    # Associate the Subbasin object to which timeDelay will be applied
    def find_timeDelayObj(self):

        timeDelay = 0.0
        self.timeDelayObj = None

        if("time delay from module" in self.dictRB):
            nameModule = self.dictRB["time delay from module"][key_Param.VALUE]
        else:
            return timeDelay


        for element in self.intletsObj:
            upEl = self.intletsObj[element]
            if upEl.iD == nameModule or upEl.name==nameModule:
                timeDelay = upEl.timeDelay
                self.timeDelayObj = upEl
                return timeDelay

        for element in self.directFluxObj:
            upEl = self.directFluxObj[element]
            if upEl.iD == nameModule or upEl.name==nameModule:
                timeDelay = upEl.timeDelay
                self.timeDelayObj = upEl
                return timeDelay

        return timeDelay



    def update_timeDelay(self):

        self.timeDelay = self.timeDelayObj.timeDelay


    def add_timeDelay(self, deltaT=0.0, reset=False, resetAll=False):

        for element in self.intletsObj:
            self.intletsObj[element].add_timeDelay(deltaT, reset=resetAll, resetAll=resetAll)

        for element in self.directFluxObj:
            self.directFluxObj[element].add_timeDelay(deltaT, reset=resetAll, resetAll=resetAll)

        # Here we are sure all the upstream subbasins are updated -> timeDelay updated
        self.update_timeDelay()


    def get_inletsName(self):

        allInlets = []

        for element in self.intletsObj:
            allInlets.append(str(self.intletsObj[element].name))

        for element in self.directFluxObj:
            allInlets.append(str(self.directFluxObj[element].name))

        return allInlets

    
    def get_inletCoords(self):

        allCoords = []

        for element in self.intletsObj:
            allCoords.append([self.intletsObj[element].x, self.intletsObj[element].y])

        for element in self.directFluxObj:
            allCoords.append([self.directFluxObj[element].x, self.directFluxObj[element].y])

        return allCoords
    
    def get_zone(self) -> zone:
        """ Return a zone instance to insert in viewer """

        myzone = zone(name = self.name)

        x,y = self.x, self.y

        xy_inlets = self.get_inletCoords()  
        names     = self.get_inletsName()
        for xy, curname in zip(xy_inlets, names):
            locx, locy = xy
            newvec = vector(name = curname)
            newvec.add_vertex(wolfvertex(locx,locy))
            newvec.add_vertex(wolfvertex(x,y))

            newvec.myprop.color = getIfromRGB([255,100,0])
            newvec.myprop.width = 3

            myzone.add_vector(newvec, forceparent=True)

        return myzone


    def get_timeDelays(self, timeDelays={}):

        timeDelays[self.name] = self.timeDelay
        for element in self.intletsObj:
            timeDelays = self.intletsObj[element].get_timeDelays(timeDelays)

        for element in self.directFluxObj:
            timeDelays = self.directFluxObj[element].get_timeDelays(timeDelays)

        return timeDelays

    def get_timeDelays_inlets(self):


        all_timeDelays = {el.timeDelay-self.timeDelay for el in self.intletsObj.values()}
        all_timeDelays.update({el.timeDelay-self.timeDelay for el in self.directFluxObj.values()})

        return all_timeDelays


    ##  This procedure save in a "transfer.param" file the timeDelay of the SubBasin and all its upstream elements
    def save_timeDelays(self):

        for element in self.intletsObj:
            self.intletsObj[element].save_timeDelays()

        for element in self.directFluxObj:
            self.directFluxObj[element].save_timeDelays()



    ## The value to extract will be applied to the same object we extract timeDelay
    def get_value_outlet(self, wolfarray):

        value = self.timeDelayObj.get_value_outlet(wolfarray)

        return value


    def get_iDSorted(self):

        return self.timeDelayObj.get_iDSorted()


    def get_outFlow_names(self)->list:

        return list(self._outFlow.keys())


    ## This procedure is updating all the hydrographs of all upstream elements imposing limits
    # @var level_min integer that specify the potential level at which the update should be stopped.
    def update_upstream_hydro(self, level_min:int=1, update_upstream:bool=True):

        for key in self.intletsObj:
            curObj = self.intletsObj[key]
            if curObj.myLevel>=level_min:
                curObj.update_hydro(update_upstream=update_upstream, level_min=level_min)


        for key in self.directFluxObj:
            curObj = self.directFluxObj[key]
            if curObj.myLevel>=level_min:
                curObj.update_hydro(update_upstream=update_upstream, level_min=level_min)



    ## This procedure is updating all the hydrographs and possibly all upstream elements imposing limits
    # @var update_upstream boolean that specify whether the upstream elements should also be updated
    # @var level_min integer that specify the potential level at which the update should be stopped.
    def update_hydro(self, update_upstream:bool=True, level_min:int=1):

        # !!! (ALERT) : So far, we consider that a RB object will always need to update its upstream elements
        # TODO : a potiential future need will require only an optimisation of the RB and fixed upstream elements!
        # if update_upstream:
        #     self.update_upstream_hydro(level_min=level_min)
        self.update_upstream_hydro(update_upstream=update_upstream,level_min=level_min)

        self.compute_hydro()



    def get_outFlow_global(self, whichOutFlow="", typeOutFlow="Net"):
        """The outFlow global property.
        Returns the outFlow in the global time, i.e. the hydrograph to which the timeDelay is applied.
        """
        if self.type == "HelleRB" :
            if whichOutFlow == list(self._outFlow.keys())[0]:
                tD = self.timeDelay
            else:
                tD = self.downstreamObj[whichOutFlow].timeDelay
        else:
            tD = self.timeDelay

        gOutFlow = self.get_outFlow(whichOutFlow=whichOutFlow, typeOutFlow=typeOutFlow, lag=tD)

        return gOutFlow


    def convert_mmh_2_m3s(self, value):

        if self.surfaceDrainedHydro>0:
            return value*self.surfaceDrainedHydro/3.6
        else:
            logging.error("Cannot convert in m³/s if the surface drained is not defined or 0!")
            return value

    def convert_m3s_2_mmh(self, value):

        if self.surfaceDrainedHydro>0:
            return value*3.6/self.surfaceDrainedHydro
        else:
            logging.error("Cannot convert in m³/s if the surface drained is not defined or 0!")
            return value


    @property
    def relative_filledVolume(self):
        """
        The relative_fillevolume is computed on the basis of filledvolume and initial volume
        """
        return self.filledVolume-self.vi

    @relative_filledVolume.setter
    def relative_filledVolume(self, value):
        """
        If we set the volume with relative value, the filledVolume is filled
        """
        self.filledVolume = value + self.vi

    def set_volume(self, volume:np.ndarray, time:np.ndarray=None):

        nbT = len(self.time)
        if time is None:
            if len(volume)==nbT:
                self.filledVolume = volume
            else:
                logging.error("The dimension of volume is not compatible with the one expected !")
                return
        else:
            if (time[1]-time[0]!=self.deltaT) or (time[0]%self.time[0]!=0):
                # TODO : code this interpolation !
                logging.error("This function is not capable yet to take into account a different timesteps! ")
                logging.error("Time step expected in time = "+self.deltaT)
                return
            self.filledVolume = np.zeros(nbT, type=np.float64)
            mask = (time>=self.time[0]) & (time<=self.time[-1])
            imin = np.argmax(mask)
            imax = min(np.argmin(mask[imin:]), nbT)
            self.filledVolume = volume[imin:imax+1]

        return


    def evaluate_objective_function(self, unit="mm/h")->np.ndarray:
        # unit = "m3/s"

        return self.get_direct_insideRB_inlets(unit=unit)


    def update_from_RBdict(self, dict_RB={}):

        self.type = self.dictRB['type'][key_Param.VALUE]
        if('stagnant height' in self.dictRB):
            self.hStagn =  float(self.dictRB['stagnant height'][key_Param.VALUE])
        if(self.type == 'HighwayRB'):
            self.surface = float(self.dictRB['surface'][key_Param.VALUE])
            self.hBank = float(self.dictRB['height 2'][key_Param.VALUE])
            self.volume = self.surface * self.hBank
        elif(self.type == 'RobiernuRB'):
            self.volume = float(self.dictRB['volume'][key_Param.VALUE])
        elif(self.type == 'OrbaisRB'):
            self.volume = float(self.dictRB['volume'][key_Param.VALUE])
            try:
                zvFile = self.dictRB['Z-V file'][key_Param.VALUE]
            except:
                zvFile = ""
            if(zvFile!=""):
                zvFile = zvFile.replace("\\", "/")
                self.read_zv(zvFile)

        elif(self.type == 'ForcedDam'):
            self.volume = float(self.dictRB['volume'][key_Param.VALUE])
            self.hi = float(self.dictRB['initial height'][key_Param.VALUE])
            self.vi = self.h_to_volume(self.hi)

            try:
                zvFile = self.dictRB['Z-V file'][key_Param.VALUE]
            except:
                zvFile = ""
            if(zvFile!=""):
                zvFile = zvFile.replace("\\", "/")

                #FIXME : Blinder la gestion des noms relatifs via une fonction
                if os.path.isabs(zvFile):
                    self.read_zv(zvFile)
                else:
                    self.read_zv(os.path.join(self.fileNameRead,zvFile))

            if("time delay" in self.dictRB):
                self.timeDelay = float(self.dictRB["time delay"][key_Param.VALUE])
        elif(self.type == "HelleRB"):
            self.volume = float(self.dictRB['volume'][key_Param.VALUE])
            try:
                zvFile = self.dictRB['Z-V file'][key_Param.VALUE]
                isOk, zvFile = check_path(zvFile, self.fileNameRead, applyCWD=True)
                if isOk<0:
                    print("ERROR : Problem in the Z-V file!")
                    zvFile = ""
            except:
                zvFile = ""
            if(zvFile!=""):
                zvFile = zvFile.replace("\\", "/")
                self.read_zv(zvFile)

        else:
            print("WARNING: This type RB was not recognised! Please check the RetentionBasin.postPro file.")


    def init_time_simulation(self, dateBegin:datetime.datetime, dateEnd:datetime.datetime, deltaT:float, tz:int=0):

            tzDelta = datetime.timedelta(hours=self.tz)
            self.dateBegin = dateBegin
            self.dateEnd = dateEnd
            self.deltaT = deltaT
            ti = datetime.datetime.timestamp(self.dateBegin-tzDelta)
            tf = datetime.datetime.timestamp(self.dateEnd-tzDelta)
            self.time = np.arange(ti,tf+self.deltaT,self.deltaT)

            return self.time


    def init_internal_variable(self):

        for iOutFlow in range(len(list(self._outFlow.items()))):
            nameOut = list(self._outFlow.items())[iOutFlow][0]
            self._outFlow[nameOut]["Net"] = np.zeros(len(self.time), dtype=np.float64)
            self._outFlow[nameOut]["Raw"] = np.zeros(len(self.time), dtype=np.float64)

        self.filledVolume = np.zeros(len(self.time), dtype=np.float64)