"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import sys                              # module to stop the program when an error is encountered
import numpy as np
import math
import datetime
import os
import csv
import logging

import ctypes as ct

from ..PyTranslate import _

if not '_' in __builtins__:
    import gettext
    _=gettext.gettext


## Function computing the cumulative volume of a given flow
# @var flow the flow to treat. Units: [m^3/s]
# @var dtData time step of the argument 'flow'. Units: [s]
# @var dtOut time step of the desired cumulative volume. It should be a multiple of 'dtData'. Units: [s]
# @var tData time array containing the timestamps of the data
# @var tRange optional array of datetime objects containing the range [tmin, tmax] in which the cumul sum will be carried out
# \undeline{Caution}: Take care to the units of dtData and dtOut according to the flow units.
# E.g. Hyeto and Evap in [mm/h]                     => dtData in [h]
# \underline{But}: outflow and myHydro in [m^3/s]   => dtData in [sec]
# Returns the cumulative volume. Units: [m^3]
# TO DO:    - ajouter interval de temps
#           - ajouter un argument 'unité'
def cumul_data(data, dtData, dtOut, tData=None, beginDate=None, tRange=None, noDataValue=None):
    # Check validity of the arguments
    if(dtOut%dtData!=0):
        print("ERROR: the time step of the desired output is not compatible with the data timestep!")
        sys.exit()
    else:
        factor = dtOut/dtData   # conversion factor from data timestep and cumul time step


    add_1_cell = 0
    if(tRange is None):
        # To detect the difference between a rain and an hydrograph data
        if(len(data)%int(factor)!=0):
            add_1_cell = 1

        cumul = np.zeros(int(len(data)/factor)+add_1_cell)
        iInit = 0
        iEnd = int(len(data)/factor)
    elif(tData is not None):
        # No distinction between rain and hydro needed here as the range is directly specified -> TO DISCUSS!!!
        tMin = datetime.datetime.timestamp(tRange[0])
        tMax = datetime.datetime.timestamp(tRange[1])
        if((tMax-tMin)%factor!=0):
            print("ERROR: the interval given does not coincide with the timestep of the desired output!")
            sys.exit()

        # We check whether the range is within data
        datesOk = False
        for i in range(len(data)):
            if(tMin==tData[i]):
                if((i+(tMax-tMin)/dtData)>len(data)-1):
                    print("ERROR: the upper bound of the desired range in out of data bounds!")
                    sys.exit()
                else:
                    datesOk = True
        if(datesOk==False):
            print("ERROR: lower bound of the range in out of the data bounds!")
            sys.exit()

    elif(beginDate is not None):
        tMin = tRange[0]
        tMax = tRange[1]
        iInit = index_from_date(beginDate, tMin, dtData, dtUnit="sec", roundType="ceil")
        iInit = math.ceil(iInit/factor)
        iEnd = index_from_date(beginDate, tMax, dtData, dtUnit="sec", roundType="floor")
        iEnd = math.floor(iEnd/factor)

        cumul = np.zeros(int((iEnd-iInit)))


    # Check whether there are holes in data.
    dataCorr = data.copy()
    if(noDataValue is not None):
        if(np.all(dataCorr>noDataValue)):
            holesInData = False
        else:
            holesInData = True
            isaved = -1
            for i in range(int((iInit)*factor), int(iEnd*factor)):
                if(dataCorr[i]<=noDataValue and isaved==-1):
                    isaved = i-1
                elif(isaved==-1):
                    continue
                elif(dataCorr[i]>noDataValue):
                    slope = (dataCorr[i]-dataCorr[isaved])/(i-isaved)
                    for j in range(isaved,i):
                        dataCorr[j] = dataCorr[isaved] + slope*(j-isaved)
                    isaved = -1
            if(isaved!=-1):
                lastIndex = math.floor(isaved/factor)-iInit
            else:
                lastIndex = len(cumul)

    else:
        holesInData = False
        lastIndex = len(cumul)



    cumul[0] = np.sum(dataCorr[iInit*int(factor):iInit*int(factor)+int(factor)])/factor*dtOut
    for i in range(iInit+1,iEnd):
        cumul[i-iInit] = cumul[i-iInit-1] + np.sum(dataCorr[i*int(factor): (i+1)*int(factor)])/factor*dtOut


    if(tRange is None):
        i = int(len(dataCorr)/factor)
        if(len(dataCorr)%int(factor)!=0):
            cumul[i] = cumul[int(len(dataCorr)/factor)-1] + dataCorr[i*int(factor)]/factor*dtOut

    if(holesInData):
        return cumul,lastIndex
    else:
        return cumul


## Function computing the cumulative volume of a given flow and for each season
# This function does not compute the volumes for incomplete seasons (i.e. at the beginning or at the end of the interval)
#
def cumul_data_per_season(data, dtData, dtOut, tData):
    # Check the validity of the arguments
    if(dtOut%dtData!=0):
        print("ERROR: the time step of the desired output is not compatible with the data timestep!")
        sys.exit()
    else:
        factor = dtOut/dtData   # conversion factor from data timestep and cumul time step

    ## Definition of the ongoing year
    tmpDate = datetime.datetime.fromtimestamp(tData[0], tz=datetime.timezone.utc)
    myYear = tmpDate.year

    ## Definition of :
    # - tOut array : time array of the output
    # - cumul list : list of cumul volume computed at each season
    tOut = [np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0)]
    cumul = [np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0)]




    ## Definition of the constants

    # @var mySeason Integer which is
    # =0, spring
    # =1, summer
    # =2, fall
    # =3, winter
    mySeason = 0

    # The dates for the beginning of each season
    dSeasons= []
    # Spring    -> [0]
    dSeasons.append(datetime.datetime(year=myYear, month=3, day=21, tzinfo=datetime.timezone.utc))
    # Summer    -> [1]
    dSeasons.append(datetime.datetime(year=myYear, month=6, day=21, tzinfo=datetime.timezone.utc))
    # Fall      -> [2]
    dSeasons.append(datetime.datetime(year=myYear, month=9, day=21, tzinfo=datetime.timezone.utc))
    # Winter    -> [3]
    dSeasons.append(datetime.datetime(year=myYear, month=12, day=21, tzinfo=datetime.timezone.utc))

    # Timestamps for the beginning of each season
    tSeasons = np.zeros(len(dSeasons))
    for i in range(len(dSeasons)):
        tSeasons[i] = datetime.datetime.timestamp(dSeasons[i])


    ## Initialisation

    # Evaluation of the current season
    for i in range(len(tSeasons)):
        if(tData[0]<=tSeasons[i]):
            if(i<3):
                mySeason = i
                break
            else:
                mySeason = 0
                myYear += 1
                # Update of the seasons dates and times
                for j in range(dSeasons):
                    dSeasons[j] = dSeasons[j].replace(dSeasons[j].year+1)
                for j in range(len(tSeasons)):
                    tSeasons[j] = datetime.datetime.timestamp(dSeasons[j])
                break

    # Identification of the first element to treat
    firstIndex = int((tSeasons[mySeason]-tData[0])/dtData)
    if((tSeasons[mySeason]-tData[0])%dtData!=0):
        print("ERROR: this case was not considered in the code yet!")
        sys.exit()


    # Identification of the last element to treat
    lastSeason = 0
    lastTime = tData[-1]
    tmpDate = datetime.datetime.fromtimestamp(lastTime, tz=datetime.timezone.utc)
    lastYear = tmpDate.year

    tmpSeasons = []
    tmpSeasons.append(datetime.datetime.timestamp(datetime.datetime(year=lastYear, month=3, day=21, tzinfo=datetime.timezone.utc)))
    tmpSeasons.append(datetime.datetime.timestamp(datetime.datetime(year=lastYear, month=6, day=21, tzinfo=datetime.timezone.utc)))
    tmpSeasons.append(datetime.datetime.timestamp(datetime.datetime(year=lastYear, month=9, day=21, tzinfo=datetime.timezone.utc)))
    tmpSeasons.append(datetime.datetime.timestamp(datetime.datetime(year=lastYear, month=12, day=21, tzinfo=datetime.timezone.utc)))

    # The incomplete seasons are removed from the calculus
    for i in range(len(tmpSeasons)-1,0-1,-1):
        if(tData[-1]>=tmpSeasons[i]):
            if(i<0):
                lastSeason = tmpSeasons[i-1]
                break
            else:
                lastYear -= 1
                lastSeason = datetime.datetime.timestamp(datetime.datetime(year=lastYear-1, month=12, day=21, tzinfo=datetime.timezone.utc))
                break
        elif(i==0):
            lastYear -= 1
            lastSeason = datetime.datetime.timestamp(datetime.datetime(year=lastYear-1, month=12, day=21, tzinfo=datetime.timezone.utc))
            break


    ## Main loop

    # ajouter l'init the tStart ou tEnd (ou les 2)
    while(tSeasons[mySeason]<=lastSeason):
        # Indentification of the interval of the seasons
        tStart = tSeasons[mySeason]
        if(mySeason<3):
            nextSeason = mySeason+1
            tEnd = tSeasons[nextSeason]
        else:
            # Update of the season's dates and times
            for j in range(len(dSeasons)):
                dSeasons[j] = dSeasons[j].replace(dSeasons[j].year+1)
            for j in range(len(tSeasons)):
                tSeasons[j] = datetime.datetime.timestamp(dSeasons[j])
            nextSeason = 0
            tEnd = tSeasons[nextSeason]

        # Identification of the number of time steps in this interval
        nbElementsIn = int((tEnd-tStart)/dtData)
        nbElementsOut = int((tEnd-tStart)/dtOut)
        tmpCumul = np.zeros(nbElementsOut)
        tmptOut = np.zeros(nbElementsOut)

        # Computation of the cumul volume for the current season
        if(len(cumul[mySeason])==0):
            tmpCumul[0] = np.sum(data[firstIndex:firstIndex+int(factor)])/factor*dtOut
        else:
            tmpCumul[0] = cumul[mySeason][-1] + (np.sum(data[firstIndex:firstIndex+int(factor)]))/factor*dtOut

        tmptOut[0] = tData[firstIndex]

        for i in range(1,nbElementsOut):
            tmpCumul[i] = tmpCumul[i-1] + np.sum(data[firstIndex+i*int(factor) : firstIndex+(i+1)*int(factor)])/factor*dtOut
            tmptOut[i] = tData[firstIndex+i*int(factor)]

        # Small test to check if all the elements were used in the data
        if((i+1)*int(factor) != nbElementsIn):
            print("ERROR: in the number of element In considered!!")
            sys.exit()
        firstIndex += (i+1)*int(factor)

        # Addition of the new cumul array to the previous one
        cumul[mySeason] = np.append(cumul[mySeason], tmpCumul)
        tOut[mySeason] = np.append(tOut[mySeason], tmptOut)

        mySeason = nextSeason


    return tOut, cumul




## Function decomposing data per each season and returns an array per season.
# This function does not decompose data for incomplete seasons (i.e. at the beginning or at the end of the interval)
#
def decompose_data_per_season(data, dtData, dtOut, tData):

    ## Definition of the ongoing year
    tmpDate = datetime.datetime.fromtimestamp(tData[0], tz=datetime.timezone.utc)
    myYear = tmpDate.year

    ## Definition of :
    # - tOut array : time array of the output
    # - newData list : list of data decomposed into each season
    tOut = [np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0)]
    newData = [np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0)]




    ## Definition of the constants

    # @var mySeason Integer which is
    # =0, spring
    # =1, summer
    # =2, fall
    # =3, winter
    mySeason = 0

    # The dates for the beginning of each season
    dSeasons= []
    # Spring    -> [0]
    dSeasons.append(datetime.datetime(year=myYear, month=3, day=21, tzinfo=datetime.timezone.utc))
    # Summer    -> [1]
    dSeasons.append(datetime.datetime(year=myYear, month=6, day=21, tzinfo=datetime.timezone.utc))
    # Fall      -> [2]
    dSeasons.append(datetime.datetime(year=myYear, month=9, day=21, tzinfo=datetime.timezone.utc))
    # Winter    -> [3]
    dSeasons.append(datetime.datetime(year=myYear, month=12, day=21, tzinfo=datetime.timezone.utc))

    # Timestamps for the beginning of each season
    tSeasons = np.zeros(len(dSeasons))
    for i in range(len(dSeasons)):
        tSeasons[i] = datetime.datetime.timestamp(dSeasons[i])


    ## Initialisation

    # Evaluation of the current season
    for i in range(len(tSeasons)):
        if(tData[0]<=tSeasons[i]):
            if(i<3):
                mySeason = i
                break
            else:
                mySeason = 0
                myYear += 1
                # Update of the seasons dates and times
                for j in range(dSeasons):
                    dSeasons[j] = dSeasons[j].replace(dSeasons[j].year+1)
                for j in range(len(tSeasons)):
                    tSeasons[j] = datetime.datetime.timestamp(dSeasons[j])
                break

    # Identification of the first element to treat
    firstIndex = int((tSeasons[mySeason]-tData[0])/dtData)
    if((tSeasons[mySeason]-tData[0])%dtData!=0):
        print("ERROR: this case was not considered in the code yet!")
        sys.exit()


    # Identification of the last element to treat
    lastSeason = 0
    lastTime = tData[-1]
    tmpDate = datetime.datetime.fromtimestamp(lastTime, tz=datetime.timezone.utc)
    lastYear = tmpDate.year

    tmpSeasons = []
    tmpSeasons.append(datetime.datetime.timestamp(datetime.datetime(year=lastYear, month=3, day=21, tzinfo=datetime.timezone.utc)))
    tmpSeasons.append(datetime.datetime.timestamp(datetime.datetime(year=lastYear, month=6, day=21, tzinfo=datetime.timezone.utc)))
    tmpSeasons.append(datetime.datetime.timestamp(datetime.datetime(year=lastYear, month=9, day=21, tzinfo=datetime.timezone.utc)))
    tmpSeasons.append(datetime.datetime.timestamp(datetime.datetime(year=lastYear, month=12, day=21, tzinfo=datetime.timezone.utc)))

    # The incomplete seasons are removed from the calculus
    for i in range(len(tmpSeasons)-1,0-1,-1):
        if(tData[-1]>=tmpSeasons[i]):
            if(i<0):
                lastSeason = tmpSeasons[i-1]
                break
            else:
                lastYear -= 1
                lastSeason = datetime.datetime.timestamp(datetime.datetime(year=lastYear-1, month=12, day=21, tzinfo=datetime.timezone.utc))
                break
        elif(i==0):
            lastYear -= 1
            lastSeason = datetime.datetime.timestamp(datetime.datetime(year=lastYear-1, month=12, day=21, tzinfo=datetime.timezone.utc))
            break


    ## Main loop

    # ajouter l'init the tStart ou tEnd (ou les 2)
    while(tSeasons[mySeason]<=lastSeason):
        # Indentification of the interval of the seasons
        tStart = tSeasons[mySeason]
        if(mySeason<3):
            nextSeason = mySeason+1
            tEnd = tSeasons[nextSeason]
        else:
            # Update of the season's dates and times
            for j in range(len(dSeasons)):
                dSeasons[j] = dSeasons[j].replace(dSeasons[j].year+1)
            for j in range(len(tSeasons)):
                tSeasons[j] = datetime.datetime.timestamp(dSeasons[j])
            nextSeason = 0
            tEnd = tSeasons[nextSeason]

        # Identification of the number of time steps in this interval
        nbElements = int((tEnd-tStart)/dtData)
        tmpdata = np.zeros(nbElements)
        tmptOut = np.zeros(nbElements)

        # Computation of the cumul volume for the current season
        if(len(newData[mySeason])==0):
            tmpdata[0] = data[firstIndex]
        else:
            tmpdata[0] = data[firstIndex]

        tmptOut[0] = tData[firstIndex]

        for i in range(1,nbElements):
            tmpdata[i] = tmpdata[i-1] + data[firstIndex+i]
            tmptOut[i] = tData[firstIndex+i]

        # Small test to check if all the elements were used in the data
        if((i+1) != nbElements):
            print("ERROR: in the number of element In considered!!")
            sys.exit()
        firstIndex += (i+1)

        # Addition of the new cumul array to the previous one
        newData[mySeason] = np.append(newData[mySeason], tmpdata)
        tOut[mySeason] = np.append(tOut[mySeason], tmptOut)

        mySeason = nextSeason


    return tOut, newData





## cst = [m^3/s]
# dt = [sec]
# Attention si c'est: - une pluie -> ok
#                     - un débit  -> enlever une taille
def cumul_fromCst(cst, dateBegin, dateEnd, dt, isFlow=False):
    timeLength = dateEnd-dateBegin
    if(dt==3600):
        if(timeLength.total_seconds()%3600==0):
            mySize = int(timeLength.total_seconds()/3600)
        else:
            print("ERROR: the number of hours not an integer!")
            sys.exit()
    elif(timeLength.total_seconds()%3600==0):
        mySize = int(timeLength.total_seconds()/dt)

    if(isFlow==False):
        mySize +=1
    # else:
        # mySize +=1
    cumul = np.zeros(mySize)
    cumul[0] = cst
    for i in range(1,mySize):
        cumul[i] = cumul[i-1] + cst*dt

    return cumul



def evaluate_Nash(simul, tSimul, measures, tMeasures, dateBegin, dateEnd, mask=[]):
    """
    Function evaluating the Nash-Suttcliff coeff
    Caution: So far, if a measure is 0, it is not considered in the N-S evaluation.
    """
    # Nash–Sutcliffe model efficiency coefficient
    print("TO CORRECT -> Check 'Hello !'  !!!!!")

    # Definition of the time step
    # Test of the constant time step - for simulation
    dtS = tSimul[1]-tSimul[0]
    for i in range(2,len(measures)):
        tmp_dt = tSimul[i]-tSimul[i-1]
        # Hello ! A corriger!!!!!!!!!
        # if(tmp_dt!=dtS):
            # print("WARNING: the time step is not regular and constant in the simulation data !")
            # print("Two timestamps can be equal when there is time changeover.")
            # sys.exit()
    # Test of the constant time step - for measures
    dtM = tMeasures[1]-tMeasures[0]
    for i in range(2,len(measures)):
        tmp_dt = tSimul[i]-tSimul[i-1]
        # if(tmp_dt!=dtM):
        #     print("WARNING: the time step is not regular and constant in the measures!")
        #     print("Two timestamps can be equal when there is time changeover.")
            # sys.exit()


    # Definition of the factor between both time steps
    if(dtM%dtS!=0):
        print("ERROR: the time step of the desired output is not compatible with the data timestep!")
        sys.exit()
    else:
        factor = dtM/dtS   # conversion factor from data timestep and cumul time step


    # Definition of the first elements
    ti = datetime.datetime.timestamp(dateBegin)
    tend = datetime.datetime.timestamp(dateEnd)
    # - simulation:
    first_el_simul = -9999
    last_el_simul = -9999
    for i in range(len(tSimul)):
        if(tSimul[i]==ti):
            first_el_simul = i
        if(tSimul[i]==tend):
            last_el_simul = i
            break
    if(first_el_simul==-9999 or last_el_simul==-9999):
        print("ERROR: the simulation data are out of range!")
        sys.exit()
    nb_el_simul = last_el_simul - first_el_simul
    # - measures:
    first_el_measures = -9999
    last_el_measures = -9999
    for i in range(len(tSimul)):
        if(tMeasures[i]==ti):
            first_el_measures = i
        if(tMeasures[i]==tend):
            last_el_measures = i
            break
    if(first_el_measures==-9999 or last_el_measures==-9999):
        print("ERROR: the simulation data are out of range!")
        sys.exit
    nb_el_measures = last_el_measures - first_el_measures

    # Verification of the proportionality between simulations and measures
    if(nb_el_simul%nb_el_measures!=0):
        print("ERROR: proportionality between simulations and measures!")
        sys.exit()


    sumNum = 0.0
    sumDen = 0.0
    meanMeasures = 0.0
    if mask==[]:
        # meanMeasures = np.mean(measures[first_el_measures:last_el_measures+1])
        counter = 0
        mask = [False for i in range(nb_el_measures)]
        for i in range(nb_el_measures):
            if(measures[first_el_measures+i]!=0.0):
                meanMeasures += measures[first_el_measures+i]
                mask[i]= True
                counter += 1
        if counter == 0:
            return 0.0
        meanMeasures = meanMeasures/counter

        for i in range(nb_el_measures):
            if(mask[i]==True):
                sumNum += (simul[first_el_simul+i*int(factor)]-measures[first_el_measures+i])**2.0
                sumDen += (measures[first_el_measures+i]-meanMeasures)**2.0
    else:
        counter = 0
        for i in range(nb_el_measures):
            if(mask[first_el_simul+i*int(factor) and measures[first_el_measures+i]!=0]):
                meanMeasures += measures[first_el_measures+i]
                counter += 1
        meanMeasures = meanMeasures/counter

        for i in range(nb_el_measures):
            if(mask[first_el_simul+i*int(factor)]):
                sumNum += (simul[first_el_simul+i*int(factor)]-measures[first_el_measures+i])**2.0
                sumDen += (measures[first_el_measures+i]-meanMeasures)**2.0



    NSE = 1.0 - (sumNum/sumDen)

    # sumNum = 0.0
    # sumDen = 0.0
    # meanMeasures = np.mean(measures)
    # for i in range(len(measures)):
    #     sumNum += (outflow[(first_el)*4+4*i]-measures[i])**2.0
    #     sumDen += (measures[i]-meanMeasures)**2.0


    # NSE = 1.0 - (sumNum/sumDen)

    return NSE



def evaluate_logNash(simul, tSimul, measures, tMeasures, dateBegin, dateEnd):
    # Nash–Sutcliffe model efficiency coefficient
    print("TO CORRECT -> Check 'Hello !'  !!!!!")

    # Definition of the time step
    # Test of the constant time step - for simulation
    dtS = tSimul[1]-tSimul[0]
    for i in range(2,len(measures)):
        tmp_dt = tSimul[i]-tSimul[i-1]
        # Hello ! A corriger!!!!!!!!!
        # if(tmp_dt!=dtS):
            # print("WARNING: the time step is not regular and constant in the simulation data !")
            # print("Two timestamps can be equal when there is time changeover.")
            # sys.exit()
    # Test of the constant time step - for measures
    dtM = tMeasures[1]-tMeasures[0]
    for i in range(2,len(measures)):
        tmp_dt = tSimul[i]-tSimul[i-1]
        # if(tmp_dt!=dtM):
        #     print("WARNING: the time step is not regular and constant in the measures!")
        #     print("Two timestamps can be equal when there is time changeover.")
            # sys.exit()


    # Definition of the factor between both time steps
    if(dtM%dtS!=0):
        print("ERROR: the time step of the desired output is not compatible with the data timestep!")
        sys.exit()
    else:
        factor = dtM/dtS   # conversion factor from data timestep and cumul time step


    # Definition of the first elements
    ti = datetime.datetime.timestamp(dateBegin)
    tend = datetime.datetime.timestamp(dateEnd)
    # - simulation:
    first_el_simul = -9999
    last_el_simul = -9999
    for i in range(len(tSimul)):
        if(tSimul[i]==ti):
            first_el_simul = i
        if(tSimul[i]==tend):
            last_el_simul = i
            break
    if(first_el_simul==-9999 or last_el_simul==-9999):
        print("ERROR: the simulation data are out of range!")
        sys.exit()
    nb_el_simul = last_el_simul - first_el_simul
    # - measures:
    first_el_measures = -9999
    last_el_measures = -9999
    for i in range(len(tSimul)):
        if(tMeasures[i]==ti):
            first_el_measures = i
        if(tMeasures[i]==tend):
            last_el_measures = i
            break
    if(first_el_measures==-9999 or last_el_measures==-9999):
        print("ERROR: the simulation data are out of range!")
        sys.exit
    nb_el_measures = last_el_measures - first_el_measures

    # Verification of the proportionality between simulations and measures
    if(nb_el_simul%nb_el_measures!=0):
        print("ERROR: proportionality between simulations and measures!")
        sys.exit()


    sumNum = 0.0
    sumDen = 0.0
    meanMeasures = np.mean(measures[first_el_measures:last_el_measures+1])
    for i in range(nb_el_measures):
        sumNum += (np.log(simul[first_el_simul+i*int(factor)])-np.log(measures[first_el_measures+i]))**2.0
        sumDen += (np.log(measures[first_el_measures+i])-np.log(meanMeasures))**2.0


    logNSE = 1.0 - (sumNum/sumDen)

    return logNSE



## Function to convert rain data from rain .dat file into another data matrix with a new timestep
# @var data Matrix containing all data in a rain file. Units: [day]-[month]-[year]-[hour]-[min]-[sec]-[mm/h]
def convert_inother_timestep(data, dtIn, dtOut):
    """
    data
    Check script Test_convert_dt_data for more information
    Function to correct!!! Only valid for rain data in [mm/h] with dtIn=1h -> dtOut=1day
    """

    if(dtIn%dtOut==0):
        # dtIn is a multiple of dtOut
        print("This case was not considered yet. Please complete it!")
        sys.exit()

        return dataOut

    elif(dtOut%dtIn==0):
        # dtOut is a multiple of dtIn
        factor = int(dtOut/dtIn)
        dataOut = np.zeros((len(data)*factor,7))

        for i in range(len(data)):
            for j in range(factor):
                dataOut[i*factor+j][:] = data[i][:]
                dataOut[i*factor+j][3] = j

        return dataOut
    else:
        print("This case was not considered yet. Please complete it!")
        sys.exit()



## Function to convert data with a smaller timestep into data with a greater timestep
# @var data vector of data to convert
# @var dtIn time step of the data
# @var dtOut time step of the data to return
# @var method string containing the method to use to aggregate the data
def aggregate(data, dtIn, dtOut, method="mean"):

    if(dtOut%dtIn!=0):
        print("ERROR: the data time step is not a multiple of the desired timestep")
        sys.exit()


    factor = int(dtOut/dtIn)
    nbIn  = len(data)
    nbOut = int(nbIn/factor)
    dataOut = np.zeros(len(data)/factor)

    if(method=="mean"):
        for i in range(nbOut):
            for j in range(factor):
                dataOut[i] += data[i*factor+j]/factor

        return dataOut


    elif(method=="sum"):
        print("ERROR: Not implemented yet!")
        return dataOut



def index_from_date(beginDate, currentDate, dt, dtUnit="sec", roundType="nearest"):

    deltaDate = currentDate - beginDate
    deltaSec = deltaDate.seconds
    deltaDay = deltaDate.days
    if(dtUnit=="sec" or dtUnit=="SEC"):
        delta = deltaSec + deltaDay*3600.0*24.0
    elif(dtUnit=="hour" or dtUnit=="HOUR"):
        delta = deltaSec/60 + deltaDay*24
    elif(dtUnit=="days" or dtUnit=="DAYS"):
        delta = deltaSec/(60.0*3600.0) + deltaDay

    if(roundType=="nearest"):
        myIndex = int(round(delta/dt))
    elif(roundType=="floor"):
        myIndex = math.floor(delta/dt)
    elif(roundType=="ceil"):
        myIndex = math.ceil(delta/dt)

    return myIndex




def Horton_function(u, uMax, infilParams):

    f0 = infilParams[0]
    fc = infilParams[1]
    k = infilParams[2]

    infil = fc + (f0-fc)*np.exp(-k*u/uMax)

    return infil





def read_C_hyd(fileName, path, dateBegin=None, dateEnd=None, deltaT=None, tzDelta=datetime.timedelta(hours=0)):

    if(type(fileName)!=str):
        print("ERROR: Expecting only 1 file name for measurements!")
        sys.exit()
    fileName = os.path.join(path,fileName)
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
            elif i==3:
                nbLines = int(raw[0])
            i += 1

    matrixData = np.array(list_data).astype("float")
    # Init of the outflow array
    if dateBegin!=None and dateEnd!=None and deltaT!=None:
        timeInterval = dateEnd-dateBegin+datetime.timedelta(seconds=deltaT)
        outFlow = np.zeros(int(timeInterval.total_seconds()/deltaT),dtype=ct.c_double, order='F')
        timeArray = np.zeros(int(timeInterval.total_seconds()/deltaT))
        ti = datetime.datetime.timestamp(dateBegin)
        tf = datetime.datetime.timestamp(dateEnd)
    else:
        outFlow = np.zeros(nbLines,dtype=ct.c_double, order='F')
        timeArray = np.zeros(nbLines)
        ti = 0.0
        tf = sys.float_info.max


    # From the measurements file, we will only read the desired data and save it in outflow
    prevDate = datetime.datetime(year=int(matrixData[0][2]), month=int(matrixData[0][1]), day=int(matrixData[0][0]), hour=int(matrixData[0][3]), tzinfo=datetime.timezone.utc)
    prevDate -= tzDelta
    index = 0
    add1Hour = datetime.timedelta(hours=1)
    secondsInDay = 24*60*60

    # Verification
    if(datetime.datetime.timestamp(prevDate)>ti):
        print("ERROR: the first hydro data element is posterior to dateBegin!")
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
            if(datetime.datetime.timestamp(currDate)>=ti and \
            datetime.datetime.timestamp(currDate)<=tf):
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
            if(datetime.datetime.timestamp(currDate)>=ti and \
            datetime.datetime.timestamp(currDate)<=tf):
                if(matrixData[i][6]<0):
                    outFlow[index] = 0.0
                else:
                    outFlow[index] = matrixData[i][6]
                outFlow[index] = matrixData[i][6]
                diffDate = currDate - prevDate
                diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
                timeArray[index] = datetime.datetime.timestamp(currDate)
                index += 1
    # The last date is not taken into account in hydro as the last date rain and evap is needed for implicit simulations
    diffDate = currDate - prevDate
    # Add the last element in the time matrix as its size is 1 element bigger than outlet
    if(deltaT!=diffDate.seconds):
        print("ERROR: The last timestep in hydro data does not coincide with the one expected!")
        sys.exit()

    return timeArray, outFlow



def write_compare_file(data:list, fileName, delimter="\t" ):

    nbL = len(data)
    nbC = 2
    for element in data:
        if len(element) != nbC:
            logging.error("The number of columns expected (here 2) are not coherent with the data !")

    header = [nbL, nbC]
    data.insert(0, header)

    f = open(fileName, "w")
    for element in data:
        line = delimter.join(element)
        f.write(line)

    f.close()



def convert_to_compareData(time, hydro, unitsOut="mm/h", unitsIn="m^3/s", DrainageSurface=0.0):

    if len(time) == len(hydro):
        nbLines = len(time)
    else:
        print("ERROR : time and data vecteur does not have the same dimensions!")

    myData = np.zeros(nbLines,2)
    # Timestamp of data
    myData[:,0] = time
    # Hydro construction
    if unitsOut == unitsIn:
        convFactor = 1.0
    elif unitsIn=="m^3/s" and unitsOut=="mm/h":
        convFactor = DrainageSurface/3.6 # A VERIFIER!!!
    # A VERIFIER!!!
    myData[:,1] = hydro * convFactor


    return myData