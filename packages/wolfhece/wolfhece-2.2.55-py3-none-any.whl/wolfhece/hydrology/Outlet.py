"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os import times,path
import sys
from textwrap import dedent
import numpy as np
from scipy.interpolate import interp1d
import csv
import datetime                         # module which contains objects treating dates

from ..PyParams import key_Param

from .read import *
from ..PyTranslate import _

if not '_' in __builtins__:
    import gettext
    _=gettext.gettext

class Outlet:
    
    def __init__(self, _retentionBasinDict, _workingDir="", time=None):
        print("Run Outlet")
        self.myType = ''
        self.myRbDict = _retentionBasinDict
        self.fileNameRead = _workingDir # //
        self.fileNameWrite = self.fileNameRead
        self.nbFlows = 0
        self.flows = []
        self.times = []
        self.time = time

        self.myType = self.myRbDict['type'][key_Param.VALUE]
        self.myRef = []
        self.myRefInterp = None

        try:
            fileRef = self.myRbDict["Reference fileName"][key_Param.VALUE]
            isOk, fileRef = check_path(fileRef, self.fileNameRead, applyCWD=True)
            if isOk<0:
                print("ERROR : Problem in the Reference fileName!")
                fileRef = ""
        except:
            fileRef = ""
        try:
            tz = float(self.myRbDict["Time zone"][key_Param.VALUE])
            tz = float(self.myRbDict["Time zone"][key_Param.VALUE])
        except:
            tz = 0.0

        if(fileRef!=""):
            self.myRefInterp = self.read_ref(fileRef, tz=tz)
            if self.time is not None:
                # FIXME : if dt(reference) < dt(simulation) => utiliser une moyenne sur tout l'intervalle !!!!!! --> TO DO !!!!
                self.myRef = np.zeros(np.shape(self.time))
                # Check the indices useful for simulation and put the other
                intrsct = np.intersect1d(self.myRefInterp.x, self.time, return_indices=True)
                # Indices containing all the data in common between the time of the forced outflow data and the simulation time
                iTime = intrsct[2]
                imax = np.max(iTime)
                imin = np.min(iTime)
                self.myRef[imin:imax+1] = self.myRefInterp(self.time[imin:imax+1])


        if("nb flows" in self.myRbDict):
            self.nbFlows = int(self.myRbDict["nb flows"][key_Param.VALUE])

            for i in range(1,self.nbFlows+1):
                self.flows.append(float(self.myRbDict['flow '+str(i)][key_Param.VALUE]))
                if(i==1):
                    self.times.append(-1.0)
                else:
                    tmpDate = datetime.datetime.strptime(self.myRbDict['time '+str(i)][key_Param.VALUE], "%d-%m-%Y %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
                    tmpTime = datetime.datetime.timestamp(tmpDate)
                    self.times.append(tmpTime)


    def compute(self, h, t=-1.0, index=-1):
        if(self.myType == 'HighwayRB'):
            q = self.compute_HighwayRB(h)
        elif(self.myType == 'RobiernuRB'):
            q = self.compute_RobiernuRB(h)
        elif(self.myType == 'OrbaisRB' or self.myType == "HelleRB"):
            if(self.nbFlows>0):
                q = self.compute_multistep(h,t)
            else:
                q = self.compute_OrbaisRB(h)
        # elif(self.myType == "HelleRB"):
        #     q = self.compute_HelleRB(h)
        elif(self.myType == "ForcedDam"):
            q = self.compute_forcedDam(t, index=index)
        return q


    def compute_HighwayRB(self, h):
        "This function compute the "
        q = 0.0
        h0 = float(self.myRbDict['stagnant height'][key_Param.VALUE])
        h1 = float(self.myRbDict['height 1'][key_Param.VALUE])
        h2 = float(self.myRbDict['height 2'][key_Param.VALUE])
        q1 = float(self.myRbDict['flow 1'][key_Param.VALUE])
        q2 = float(self.myRbDict['flow 2'][key_Param.VALUE])

        if(h<=h1):
            q = q1
        else:
            q = q2
        return q

    def compute_RobiernuRB(self, h):
        q = float(self.myRbDict['flow 1'][key_Param.VALUE])
        return q

    def compute_OrbaisRB(self, h):
        q = float(self.myRbDict['flow 1'][key_Param.VALUE])
        return q


    # def compute_HelleRB(self,h):
    #     qRmoved = float(self.myRbDict['flow 1']['value'])
    #     q = 0.0
    #     return q

    def compute_forcedDam(self, time, index=-1):
        if self.time is None or index<0:
            if(time<min(self.myRefInterp.x) or time>max(self.myRefInterp.x)):
                q=0.0
            else:
                q = self.myRefInterp(time)

        elif index<len(self.myRef):
            q = self.myRef[index]

        else:
            q = 0.0

        return q


    def compute_multistep(self, h, time):

        q = self.flows[-1]

        for i in range(self.nbFlows-1):
            if(time<self.times[i+1]):
                q = self.flows[i]
                break

        return q





    def read_ref(self, fileName, typeOfInterpolation='linear', tz=0):
        """
        tz represents the time zone "GMT+"tz
        """
        if not path.exists(fileName):
            return

        if(type(fileName)!=str):
            print("ERROR: Expecting only 1 file name for measurements!")
            sys.exit()
        with open(fileName, newline = '') as fileID:
            data_reader = csv.reader(fileID, delimiter=' ',skipinitialspace=True)
            list_data = []
            i=0
            for raw in data_reader:
                if i>3:
                    list_data.append(raw)
                if i==2:
                    nbCl = int(raw[0])
                i += 1
        matrixData = np.array(list_data).astype("float")
        # Init of the outflow array
        timeInterval = len(matrixData)
        outFlow = np.zeros(timeInterval)
        timeArray = np.zeros(timeInterval)

        # From the measurements file, we will only read the desired data and save it in outflow
        prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), tzinfo=datetime.timezone.utc)
        index = 0
        add1Hour = datetime.timedelta(hours=1)
        secondsInDay = 24*60*60

        if(nbCl==5):
            # Caution : the index of the loop start at 24 because the timestamp function
            # does not work until the 2/01/1970 at 03:00:00. => Je ne sais pas pourquoi ?!
            for i in range(25,len(matrixData)):
                # The hours are written in the file in [1,24] instead of [0,23]. Conversion below:
                if(int(matrixData[i][3])==24):
                    currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=23, tzinfo=datetime.timezone.utc) + add1Hour
                else:
                    currDate = datetime.datetime(year=int(matrixData[i][2]), month=int(matrixData[i][1]), day=int(matrixData[i][0]), hour=int(matrixData[i][3]), tzinfo=datetime.timezone.utc)
                if(int(matrixData[i-1][3])==24):
                    prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=23, tzinfo=datetime.timezone.utc) + add1Hour
                else:
                    prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=int(matrixData[i-1][3]), tzinfo=datetime.timezone.utc)
                # Start at dateBegin and go to the element before dateEnd. Because the last date is needed for rain and evap in implicit simulations.
                if(datetime.datetime.timestamp(currDate)>=datetime.datetime.timestamp(self.dateBegin) and \
                datetime.datetime.timestamp(currDate)<datetime.datetime.timestamp(self.dateEnd)):
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
                prevDate = datetime.datetime(year=int(matrixData[i-1][2]), month=int(matrixData[i-1][1]), day=int(matrixData[i-1][0]), hour=int(matrixData[i-1][3]), minute=int(matrixData[i-1][4]), second=int(matrixData[i-1][5]),tzinfo=datetime.timezone.utc)
                # Start at dateBegin and go to the element before dateEnd. Because the last date is needed for rain and evap in implicit simulations.
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
        timeArray[-1] = timeArray[-2] + diffTimeInSeconds

        timeArray -= tz*3600

        interpol = interp1d(timeArray,outFlow,kind=typeOfInterpolation, assume_sorted=True)

        return interpol
