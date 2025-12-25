"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec

from ..PyTranslate import _
from ..wolf_array import *
from ..PyParams import*

def extract_array(fileName:str):

    wolfArray_read = WolfArray(fileName)
    array = wolfArray_read.array
    arrayMask = np.ma.getmaskarray(array)

    return array, arrayMask


def extract_and_sort_data(fileName:str):

    wolfArray_read = WolfArray(fileName)
    wolfArray_mask = np.ma.getmaskarray(wolfArray_read.array)
    arrayRead = []
    for i in range(wolfArray_read.nbx):
        for j in range(wolfArray_read.nby):
            # element = wolfArray_read.get_value_from_ij(i,j)
            element = wolfArray_read.array[i][j]
            elementMask = wolfArray_mask[i][j]
            if elementMask==True or element == float('inf'):
                continue
            arrayRead.append(element)
    wolfArray_sort = np.sort(arrayRead, axis = None)

    return wolfArray_sort


def extract_stat_distribution(fileName, interval=[0,0], steps=None):

    wolfArray_read = WolfArray(fileName)
    arrayRead = wolfArray_read.array
    histo, dataSorted = make_stat_distribution(arrayRead,interval,steps)

    return histo, dataSorted


def extract_slopes_from_river_and_basin(slopesFile, riverFile, plotHisto=True, plotWhat="", plotTitle="", plotNow=False, plotLimitsCumul=[], interval=[0,0], steps=None, \
                                        figSize = [10.4,6.25], condition='', condValue=None, subbasinID=1, subbasinFile=""):

    # Extraction of slopes and river array
    wolfSlopes = WolfArray(slopesFile)
    wolfRiver = WolfArray(riverFile)


    # Extraction of mask array
    slopesMask = np.ma.getmask(wolfSlopes.array)
    riverMask = np.ma.getmask(wolfRiver.array)

    if(subbasinFile!=""):
        wolfSub = WolfArray(subbasinFile)


    # The slopes array is divided in slopes in river, slopes in basin and slopes out of the domain (masked)
    nbx = wolfSlopes.nbx
    nby = wolfSlopes.nby
    slopesBasin = []
    slopesRiver = []
    xRiver = []
    yRiver = []
    iRiver = []
    jRiver = []

    if(subbasinFile==""):
        for i in range(nbx):
            for j in range(nby):
                element =  wolfSlopes.array[i][j]
                if slopesMask[i][j]:
                    continue
                if riverMask[i][j]:
                    slopesBasin.append(element)
                else:
                    slopesRiver.append(element)
                    # i+1 & j+1 car en Fortran les indices commencent à 1
                    x,y = wolfSlopes.get_xy_from_ij(i+1,j+1)
                    x,y = wolfRiver.get_xy_from_ij(i+1,j+1)
                    xRiver.append(x)
                    yRiver.append(y)
                    iRiver.append(i+1)
                    jRiver.append(j+1)
    else:
        for i in range(nbx):
            for j in range(nby):
                element =  wolfSlopes.array[i][j]
                if slopesMask[i][j]:
                    continue
                if wolfSub.array[i][j]==subbasinID:
                    if riverMask[i][j]:
                        slopesBasin.append(element)
                    else:
                        slopesRiver.append(element)
                        # i+1 & j+1 car en Fortran les indices commencent à 1
                        x,y = wolfSlopes.get_xy_from_ij(i+1,j+1)
                        x,y = wolfRiver.get_xy_from_ij(i+1,j+1)
                        xRiver.append(x)
                        yRiver.append(y)
                        iRiver.append(i+1)
                        jRiver.append(j+1)

    slopesBasin_sorted = np.sort(slopesBasin, axis = None)
    slopesRiver_sorted = np.sort(slopesRiver, axis = None)
    indexModif = np.argsort(slopesRiver)
    xRiverSort = [None]*len(slopesRiver_sorted)
    yRiverSort = [None]*len(slopesRiver_sorted)
    iRiverSort = [None]*len(slopesRiver_sorted)
    jRiverSort = [None]*len(slopesRiver_sorted)
    for i in range(len(slopesRiver_sorted)):
        oldIndex = indexModif[i]
        xRiverSort[i] = xRiver[oldIndex]
        yRiverSort[i] = yRiver[oldIndex]
        iRiverSort[i] = iRiver[oldIndex]
        jRiverSort[i] = jRiver[oldIndex]


    if plotHisto:
        if(plotWhat=="" or plotWhat=="All" or plotWhat=="all" or plotWhat=="ALL"):
            nbPlot = 2
            plotRiver = True
            plotBasin = True
            gs = gridspec.GridSpec(nbPlot*4, 5)  # Subdivision of the main window in a grid of several subplots
            gs1 = gs[:4,:]
            gs2 = gs[4:,:]
        elif(plotWhat=="River" or plotWhat=="river" or plotWhat=="RIVER"):
            nbPlot = 1
            plotRiver = True
            plotBasin = False
            gs = gridspec.GridSpec(nbPlot*4, 5)  # Subdivision of the main window in a grid of several subplots
            gs2 = gs[:4,:]
        elif(plotWhat=="Basin" or plotWhat=="basin" or plotWhat=="BASIN"):
            nbPlot = 1
            plotRiver = False
            plotBasin = True
            gs = gridspec.GridSpec(nbPlot*4, 5)  # Subdivision of the main window in a grid of several subplots
            gs1 = gs[:4,:]
        else:
            print("ERROR: invalid argument 'plotWhat' ")
            sys.exit()

        minValue = 100
        maxValue = -1
        if interval==[0,0]:
            if plotBasin:
                minValue = slopesBasin_sorted[0]
                maxValue = slopesBasin_sorted[-1]
            if plotRiver:
                if slopesRiver_sorted[0]<minValue:
                    minValue = slopesRiver_sorted[0]
                if slopesRiver_sorted[-1]>maxValue:
                    maxValue = slopesRiver_sorted[-1]
        else :
            minValue = interval[0]
            maxValue = interval[1]

        if steps is None:
            steps = (maxValue-minValue)/10.0

        fig = plt.figure(figsize=(figSize[0],figSize[1]))
        if plotTitle=="":
            fig.suptitle('Slopes distribution in basin and river')
        else:
            fig.suptitle(plotTitle)
        myBins =  np.arange(minValue,maxValue, steps)*100

        if plotBasin:
            ax1 = plt.subplot(gs1)
            ax1.hist(slopesBasin_sorted*100, bins=myBins, label='Slopes in basin', color='r')
            ax1.set_xlabel('Slope [%]')
            ax1.set_ylabel('Number of elements')
            ax1.set_xlim([minValue*100,maxValue*100])
            ax1.grid()

            ax1_2 = ax1.twinx()
            ax1_2.set_ylabel('Cumulative distribution [-]',color='k')
            ax1_2.hist(slopesBasin_sorted*100, len(myBins), color='k',cumulative=True,density=True,histtype='step')
            if(plotLimitsCumul!=[]):
                ax1_2.plot(myBins,plotLimitsCumul[0]*np.ones(len(myBins)), 'g--')
                ax1_2.plot(myBins,plotLimitsCumul[1]*np.ones(len(myBins)), 'r--')
            # plt.hist(slopesBasin, bins=myBins, label='Slopes in basin', color='r')
            # ax1.set_legend()
            plt.legend()

        if plotRiver:
            ax2 = plt.subplot(gs2)
            ax2.hist(slopesRiver_sorted*100, bins=myBins, label='Slopes in river', color='b')
            ax2.set_xlabel('Slope [%]')
            ax2.set_ylabel('Number of elements')
            ax2.set_xlim([minValue*100,maxValue*100])
            ax2.grid()
            ax2_2 = ax2.twinx()
            ax2_2.set_ylabel('Cumulative distribution [-]',color='k')
            ax2_2.hist(slopesRiver_sorted*100, len(myBins), color='k',cumulative=True,density=True,histtype='step')
            if(plotLimitsCumul!=[]):
                ax2_2.plot(myBins,plotLimitsCumul[0]*np.ones(len(myBins)), 'g--')
                ax2_2.plot(myBins,plotLimitsCumul[1]*np.ones(len(myBins)), 'r--')
            # plt.hist(slopesRiver, bins=myBins, label='Slopes in river', color='b')
            plt.legend()

        if plotNow:
            plt.show()


        if condition!='' and condValue is not None:
            tmpRiver = slopesRiver_sorted.copy()
            # if(condition==">"):
            #     nb = len(tmpRiver)
            #     for i in range(nb):
            #         tmpRiver =

    return slopesBasin_sorted, slopesRiver_sorted, xRiverSort, yRiverSort, iRiverSort, jRiverSort



def sort_data(array):

    arrayMask = np.ma.getmaskarray(array)
    dataUseful = []
    nbx = len(array)
    nby = len(array[0])
    for i in range(nbx):
        for j in range(nby):
            element = array[i][j]
            elementMask = arrayMask[i][j]
            if elementMask==True or element == float('inf'):
                continue
            dataUseful.append(element)
    dataSorted = np.sort(dataUseful, axis = None)

    return dataSorted



def make_stat_distribution(array, interval=[0,0], steps=None):

    dataSorted = sort_data(array)

    if interval==[0,0]:
        minValue = dataSorted[0]
        maxValue = dataSorted[-1]
    else :
        minValue = interval[0]
        maxValue = interval[1]

    if steps is None:
        steps = (maxValue-minValue)/10.0

    myBins = np.arange(minValue,maxValue, steps)
    histo = np.histogram(dataSorted, bins=myBins, density=True)

    return histo, dataSorted



def plot_hist(dataSorted, interval=[0,0], steps=0.0001, label='', color='b', plotNow=False):

    if interval==[0,0]:
        minValue = dataSorted[0]
        maxValue = dataSorted[-1]
    else :
        minValue = interval[0]
        maxValue = interval[1]

    if steps is None:
        steps = (maxValue-minValue)/10.0

    myBins =  np.arange(minValue,maxValue, steps)
    plt.hist(dataSorted, bins=myBins, label=label, color=color)
    plt.legend()

    if plotNow:
        plt.show()


# def get_coord_riverSlopes_with_condition(slopesSorted:list, limitValue:float, condSymb:str):

#     if condSymb=='>':

#         nb = len(slopesSorted)
#         for i in range(nb):
#             if()

#     elif condSymb=='<':
#         dd

#     else:
#         print("ERROR: the condition symbole is not correct! Please add only '<', '>' or '='!")
#         sys.exit()
