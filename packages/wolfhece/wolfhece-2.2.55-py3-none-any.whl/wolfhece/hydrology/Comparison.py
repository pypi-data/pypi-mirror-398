"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import sys                              # module to stop the program when an error is encountered
import os
import matplotlib.pyplot as plt
import numpy as np
from wx.core import DD_CHANGE_DIR

from ..PyTranslate import _
from .Catchment import *

class Comparison:
    """
    This class contains several Catchment objects and all the procedures
    to produce plots that can compare different results of these Catchments.
    """

    ## Constructor
    def __init__(self, workingDir, dictCatchment, dictToCompar):

        # ===========
        #
        #

        ## @var workingDir The path of the working directory
        self.workingDir = workingDir + 'PostProcess_Comparison/'


        ## Dictionary containing all the objects Catchment:
        #  @var dictCatchment dictionnary containing: 'Title' and 'Object'
        #  'Title': the name that one wants to give to the element on graphs
        #  'Object': The Catchment object containing all the information of the Catchment.
        self.myCatchments = dictCatchment


        ## @var dictToCompar
        # Dictionary containing:
        # - 1: if the plot function is used
        # - 0: otherwise
        self.dictToCompar = dictToCompar


        ## @var plotDict disctionnary containing all basic plot informations
        self.plotDict = {}

        # ==========================================================================================

        # Creation of the PostProcess directory
        # It will contain all the the saved results.

        if not os.path.exists(self.workingDir):
            try:
                os.mkdir(self.workingDir)
            except OSError:
                print ("Creation of the directory %s failed" % self.workingDir)
            else:
                print ("Successfully created the directory %s" % self.workingDir)


        # Verification that the number of Catchments to compare is greater than 1
        if(len(self.myCatchments)<=1):
            print('ERROR: Cannot compare less than 2 Catchments')
            # sys.exit()


    def compare_now(self):

        # Check and run all the functions to use
        if(int(self.dictToCompar['hydro subbasin'][key_Param.VALUE]) == 1):
            self.hydro_subbasin()
        if(int(self.dictToCompar['hydro junction'][key_Param.VALUE]) == 1):
            self.hydro_junction()
        if(int(self.dictToCompar['hydro final'][key_Param.VALUE]) == 1):
            self.hydro_final()


    def hydro_subbasin(self):
        print("Comparison of all subbasin ...")

        # Test that the number of subbasins are the same
        nbSubBasins=len(self.myCatchments['Catchment 1']['Object'].subBasinDict)
        for i in range(2, len(self.myCatchments)+1):
            txtTmp = 'Catchment ' + str(i)
            tmpNb = len(self.myCatchments[txtTmp]['Object'].subBasinDict)
            if(tmpNb!=nbSubBasins):
                print("ERROR: These Catchments cannot be compared as their number of subbasins are not the same!")
                sys.exit()


        for subId in range(1,tmpNb+1):
            # Figure Rain on a first y axis
            fig,ax1=plt.subplots()
            ax1.set_xlabel('Time [years]')
            ax1.set_ylabel(_('Discharge [mm/s]'),color='k') #Color express in %RGB: (1,1,1)
            # ax1.set_ylim(0, self.myHydro.max()*2)
            # ax1.hist(data1,color=(0,0,1),edgecolor='black',linewidth=1.2)
            max_= 0
            for element in self.myCatchments:
                title = self.myCatchments[element]['Title']
                pointer = self.myCatchments[element]['Object'].subBasinDict[subId]
                x = pointer.time/(3600.0*24*365)+2000    # [years]
                y1 = pointer.myHydro*pointer.surfaceDrained/3.6
                y2 = pointer.rain
                if(y1.max()>max_):
                    max_ = y1.max()
                ax1.set_ylim(0, max_*2)
                ax1.set_xticks([2000, 2001, 2002, 2003])
                ax1.plot(x,y1,'--',label=title)
            ax1.tick_params(axis='y',labelcolor='k')

            # Figure Hydro on a second y axis
            ax2=ax1.twinx()
            ax2.set_ylabel(_('Precipitations [m³/s]'),color='b')
            ax2.set_ylim(y2.max()*3, 0)
            ax2.plot(x,y2,color='b')
            ax2.fill_between(x, y2, 0, color='b')
            ax2.tick_params(axis='y',labelcolor='b')
            fig.tight_layout()
            handles, labels = ax1.get_legend_handles_labels()
            fig.legend(handles, labels)
            plt.savefig(self.workingDir+'/Subbasin_'+str(subId)+'_Compar'+'.pdf')


    def hydro_junction(self):
        print("Comparison of all junctions ...")


        # # Test that the number of subbasins are the same
        # nbJunction=len(self.myCatchments['Catchment 1']['Object'].intersection)
        # for i in range(2, len(self.myCatchments)+1):
        #     txtTmp = 'Catchment ' + str(i)
        #     tmpNb = len(self.myCatchments[txtTmp]['Object'].intersection)
        #     if(tmpNb!=nbJunction):
        #         print("ERROR: These Catchments cannot be compared as their number of subbasins are not the same!")
        #         sys.exit()


        # for subId in range(1,tmpNb+1):
        #     # Figure Rain on a first y axis
        #     fig,ax1=plt.subplots()
        #     ax1.set_xlabel('Temps [h]')
        #     ax1.set_ylabel('Débits [mm/s]',color='k') #Color express in %RGB: (1,1,1)
        #     # ax1.set_ylim(0, self.myHydro.max()*2)
        #     # ax1.hist(data1,color=(0,0,1),edgecolor='black',linewidth=1.2)
        #     max_= 0
        #     for element in self.myCatchments:
        #         title = self.myCatchments[element]['Title']
        #         pointer = self.myCatchments[element]['Object'].intersection[subId]
        #         x = pointer.time/3600.0    # [h]
        #         y1 = pointer.myHydro
        #         y2 = pointer.rain
        #         if(y1.max()>max_):
        #             max_ = y1.max()
        #         ax1.set_ylim(0, max_*2)
        #         ax1.plot(x,y1,label=title)
        #     ax1.tick_params(axis='y',labelcolor='k')

        #     # Figure Hydro on a second y axis
        #     ax2=ax1.twinx()
        #     ax2.set_ylabel('Précipitations [m³/s]',color='b')
        #     ax2.set_ylim(y2.max()*3, 0)
        #     ax2.plot(x,y2,color='b')
        #     ax2.fill_between(x, y2, 0, color='b')
        #     ax2.tick_params(axis='y',labelcolor='b')
        #     fig.tight_layout()
        #     handles, labels = ax1.get_legend_handles_labels()
        #     fig.legend(handles, labels)
        #     plt.savefig(self.workingDir+'/Subbasin_'+str(subId)+'_Compar'+'.pdf')

    ## Caution the number of levels are not assumed to be the same here! This function can compare
    #  catchments with completely different topology
    def hyetos(self, catchColors=[], rangeRain=[], writeFile='', myTraits=None, beginDate=None, endDate=None, dt=None, yrangeData=[], \
                addData=[], dt_addData=[], beginDates_addData=[], endDates_addData=[],label_addData=[], color_addData=[], typeOfTraits_addData=[],cumulOrigin_addData=[]):
        """
        TO DO : A Généraliser dans le cas où les sous-bassins n'ont pas le même nom et topologie !!!!!
        """
        print("Comparison of the hyetos from all subbasins")

        if(beginDate is None):
            beginDate = []
            for idCatch in self.myCatchments:
                beginDate.append(self.myCatchments[idCatch]['Object'].dateBegin)
                # beginDate = self.myCatchments[idCatch]['Object'].dateBegin
                # break

        if(endDate is None):
            endDate = []
            for idCatch in self.myCatchments:
                endDate.append(self.myCatchments[idCatch]['Object'].dateEnd)
                # endDate = self.myCatchments[idCatch]['Object'].dateEnd
                # break

        if(dt is None):
            dt=[]
            for idCatch in self.myCatchments:
                dt.append(self.myCatchments[idCatch]['Object'].deltaT)


        basinNames = [] # contains all the names of the subbasin
        for idCatch in self.myCatchments:
            curCatch = self.myCatchments[idCatch]['Object']
            for nameBasin in curCatch.subBasinDict:
                if(not(nameBasin in basinNames)):
                    basinNames.append(nameBasin)


        nbCatchment = len(self.myCatchments)
        x_title = "Dates"


        if(catchColors==[]):
            tmpColors = np.random.rand(nbCatchment)
            for icolor in range(len(tmpColors)):
                catchColors.append(tmpColors[icolor])

        elif(len(catchColors)!=nbCatchment):
            print("ERROR: the number of catchments is not the same as the number of colors given")

        for nameBasin in basinNames:

            y1 = []
            y2 = []
            yLabels = []
            myTraits = []
            for idCatch in self.myCatchments:
                curCatch = self.myCatchments[idCatch]['Object']
                y1.append(curCatch.subBasinDict[nameBasin].myRain[:-1])

                dtH = curCatch.subBasinDict[nameBasin].deltaT/3600.0
                tmpCumul = datt.cumul_data(curCatch.subBasinDict[nameBasin].myRain[:-1], dtH, dtH)
                y2.append(tmpCumul)
                yLabels.append(curCatch.name)

                graph_title = curCatch.subBasinDict[nameBasin].name
                myTraits.append('-')


            nbAddData = 0
            if(addData!=[]):
                nbAddData = len(addData)
                for i in range(nbAddData):
                    y1.append(addData[i][:-1])
                    tmpY2 = datt.cumul_data(addData[i][:-1], dt_addData[i]/3600.0, dt_addData[i]/3600.0)
                    if(cumulOrigin_addData!=[]):
                        y2.append(tmpY2-cumulOrigin_addData[i])
                    else:
                        y2.append(tmpY2)
                    beginDate.append(beginDates_addData[i])
                    endDate.append(endDates_addData[i])
                    dt.append(dt_addData[i])
                    if(label_addData!=[]):
                        yLabels.append(label_addData[i])
                    if(color_addData!=[]):
                        catchColors.append(color_addData[i])
                    if(typeOfTraits_addData!=[]):
                        myTraits.append(typeOfTraits_addData[i])



            # Plot Rains
            yTitles = "Pluies [mm/h]"
            writeFileDef = writeFile + "_Rain_" + graph_title.replace(".","")
            ph.plot_hydro(nbCatchment+nbAddData, y1, x_title=x_title, y_titles=yTitles, beginDate=beginDate,endDate=endDate,dt=dt,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=rangeRain,y_data_range=yrangeData,myColors=catchColors,typeOfTraits=myTraits,writeFile=writeFileDef)

            # Plot Cumulated rains
            yTitles = "Cumulated Rain [mm]"
            writeFileDef = writeFile + "_CumulRain_" + graph_title.replace(".","")
            ph.plot_hydro(nbCatchment+nbAddData, y2, x_title=x_title, y_titles=yTitles, beginDate=beginDate,endDate=endDate, dt=dt,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=rangeRain,y_data_range=yrangeData,myColors=catchColors,typeOfTraits=myTraits,writeFile=writeFileDef)

            plt.show()



    def comparison_with_measures(self,addCatchment):

            print("TO DO")
            sys.exit()

            x_range = [x_min,x_max]

            attemptName = "Comparaison Hydro"

            for element in testFroudeCatchment.subBasinDict:
                if(testFroudeCatchment.subBasinDict[element].name == "Chaudfontaine"):
                    stationName = "Chaudfontaine"
                    Qnat = naturalCatchment.subBasinDict[element].myHydro[:]
                    addData = []
                    addData.append(Qnat[:-1])
                    dtAddData = [testFroudeCatchment.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd]
                    label_addData = ["BV avant modification du Froude"]
                    color_addData = ["y"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(Measures=RV.MeasuresChau,withEvap=False,rangeData=x_range,graph_title=stationName ,writeFile=writeDir+stationName+attemptName, withDelay=False)
                elif(testFroudeCatchment.subBasinDict[element].name == "Theux"):
                    stationName = "Theux"
                    Qnat = naturalCatchment.subBasinDict[element].myHydro[:]
                    addData = []
                    addData.append(Qnat[:-1])
                    dtAddData = [testFroudeCatchment.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd]
                    label_addData = ["BV avant modification du Froude"]
                    color_addData = ["y"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(Measures=RV.MeasuresTheu,withEvap=False,rangeData=x_range,graph_title=stationName,writeFile=writeDir+stationName+attemptName, withDelay=False)
                elif(testFroudeCatchment.subBasinDict[element].name == "SPIXHE"):
                    stationName = "SPIXHE"
                    Qnat = naturalCatchment.subBasinDict[element].myHydro[:]
                    addData = []
                    addData.append(Qnat[:-1])
                    dtAddData = [testFroudeCatchment.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd]
                    label_addData = ["BV avant modification du Froude"]
                    color_addData = ["y"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(Measures=RV.MeasuresSpix,withEvap=False,rangeData=x_range,graph_title=stationName ,writeFile=writeDir+stationName+attemptName, withDelay=False)
                elif(testFroudeCatchment.subBasinDict[element].name == "Station Verviers"):
                    stationName = "Station Verviers"
                    Qnat = naturalCatchment.subBasinDict[element].myHydro[:]
                    addData = []
                    addData.append(Qnat[:-1])
                    dtAddData = [testFroudeCatchment.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd]
                    label_addData = ["BV avant modification du Froude"]
                    color_addData = ["y"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(Measures=RV.MeasuresVerv,withEvap=False,rangeData=x_range,graph_title=stationName ,writeFile=writeDir+stationName+attemptName, withDelay=False)
                elif(testFroudeCatchment.subBasinDict[element].name == "Station Foret (Magne)"):
                    stationName = "Station Foret (Magne)"
                    Qnat = naturalCatchment.subBasinDict[element].myHydro[:]
                    addData = []
                    addData.append(Qnat[:-1])
                    dtAddData = [testFroudeCatchment.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd]
                    label_addData = ["BV avant modification du Froude"]
                    color_addData = ["y"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(Measures=RV.MeasuresFor,withEvap=False,rangeData=x_range,graph_title=stationName ,writeFile=writeDir+stationName+attemptName, withDelay=False)
                elif(testFroudeCatchment.subBasinDict[element].name == "Polleur"):
                    stationName = "Polleur"
                    Qnat = naturalCatchment.subBasinDict[element].myHydro[:]
                    addData = []
                    addData.append(Qnat[:-1])
                    dtAddData = [testFroudeCatchment.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd]
                    label_addData = ["BV avant modification du Froude"]
                    color_addData = ["y"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(Measures=RV.MeasuresPoll,withEvap=False,rangeData=x_range,graph_title=stationName ,writeFile=writeDir+stationName+attemptName, withDelay=False)
                elif(testFroudeCatchment.subBasinDict[element].name == "Belleheid"):
                    stationName = "Belleheid"
                    Qnat = naturalCatchment.subBasinDict[element].myHydro[:]
                    addData = []
                    addData.append(Qnat[:-1])
                    dtAddData = [testFroudeCatchment.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd]
                    label_addData = ["BV avant modification du Froude"]
                    color_addData = ["y"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(Measures=RV.MeasuresBell,withEvap=False,rangeData=x_range,graph_title=stationName ,writeFile=writeDir+stationName+attemptName, withDelay=False)
                elif(testFroudeCatchment.subBasinDict[element].name == "Barrage Vesdre"):
                    stationName = "Barrage Vesdre"
                    Qnat = naturalCatchment.subBasinDict[element].myHydro[:]
                    addData = []
                    addData.append(Qnat[:-1])
                    dtAddData = [testFroudeCatchment.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd]
                    label_addData = ["BV avant modification du Froude"]
                    color_addData = ["y"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(Measures=RV.MeasuresBVesIn,withEvap=False,rangeData=x_range,graph_title=stationName ,writeFile=writeDir+stationName+attemptName, withDelay=False, yrangeData=yrangeData, yrangeRain=yrangeRain)
                elif(testFroudeCatchment.subBasinDict[element].name == "BV Barrage Vesdre"):
                    stationName = "BV B Vesdre"
                    Qnat = naturalCatchment.subBasinDict[11].myHydro[:]

                    addData = []
                    addData.append(QVesdreFroude[:-1])
                    addData.append(QVesdreBeforeFroude[:-1])
                    addData.append(RV.MeasuresBVesIn.myHydro[:])

                    dtAddData = [testFroudeCatchment.deltaT,testFroudeCatchment.deltaT,RV.MeasuresBVesIn.deltaT]
                    beginDatesAddData = [testFroudeCatchment.dateBegin, testFroudeCatchment.dateBegin,RV.MeasuresBVesIn.dateBegin]
                    endDatesAddData = [testFroudeCatchment.dateEnd,testFroudeCatchment.dateEnd,RV.MeasuresBVesIn.dateEnd]
                    label_addData = ["Debits simulés avec apport de la Helle et de la Soor","BV avant modification du Froude", "Hydrogramme entrant reconstruit"]
                    color_addData = ["b","y","k"]

                    testFroudeCatchment.subBasinDict[element].plot_outlet(withEvap=False,rangeData=x_range,graph_title=stationName ,writeFile=writeDir+stationName+attemptName, withDelay=False, \
                        addData=addData,dt_addData=dtAddData,beginDates_addData=beginDatesAddData,endDates_addData=endDatesAddData,label_addData=label_addData,color_addData=color_addData)



    def outlet_all_basins_same_topo(self, plotDict={}, show=True, envelop=False, refModuleName =""):

        # Load General characteristics of the dictionnary
        if(not("Time Zone Plot" in plotDict["General Parameters"])):
            tzPlot = 0
            tzDelta = datetime.timedelta(hours=0)
        else:
            tzPlot = plotDict["General Parameters"]["Time Zone Plot"]
            tzDelta = datetime.timedelta(hours=tzPlot)

        # if(envelop and not("Ref Name" in plotDict["General Parameters"])):
        #     refName = "Catchment 1"
        # else:
        #     refName = plotDict["General Parameters"]["Ref Name"]

        if(not("Add Table" in plotDict["General Parameters"])):
            addTable = False
        else:
            addTable = plotDict["General Parameters"]["Add Table"]

        if(not("Date Begin" in plotDict["General Parameters"])):
            beginDate = []
            for idCatch in self.myCatchments:
                if(not(envelop)):
                    beginDate.append(self.myCatchments[idCatch]['Object'].dateBegin+tzDelta)
                elif(idCatch==refName):
                    beginDate.append(self.myCatchments[idCatch]['Object'].dateBegin+tzDelta)
        else:
            beginDate = plotDict["General Parameters"]["Date Begin"]+tzDelta

        if(not("Date End" in plotDict["General Parameters"])):
            endDate = []
            for idCatch in self.myCatchments:
                if(not(envelop)):
                    endDate.append(self.myCatchments[idCatch]['Object'].dateEnd+tzDelta)
                elif(idCatch==refName):
                    endDate.append(self.myCatchments[idCatch]['Object'].dateEnd+tzDelta)
        else:
            endDate = plotDict["General Parameters"]["Date End"]+tzDelta

        if(not("Dt" in plotDict["General Parameters"])):
            dt=[]
            for idCatch in self.myCatchments:
                if(not(envelop)):
                    dt.append(self.myCatchments[idCatch]['Object'].deltaT)
                elif(idCatch==refName):
                    dt.append(self.myCatchments[idCatch]['Object'].deltaT)
        else:
            dt = plotDict["General Parameters"]["Dt"]



        # All the useful junctions will be listed so that all the elements won't be analysed anymore
        basinId = [] # contains all the names of the subbasin
        basinNames = {}
        for idCatch in self.myCatchments:
            curCatch = self.myCatchments[idCatch]['Object']
            for id in curCatch.subBasinDict:
                curBasin = curCatch.subBasinDict[id]
                if(not(id in basinId) and (curBasin.name in plotDict)):
                    basinId.append(id)
                    basinNames[id] = (curBasin.name)



        nbCatchment = len(self.myCatchments)
        x_title = "Dates " + "(GMT+"+ str(tzPlot) + ")"


        if(not("Catchment colors" in plotDict["General Parameters"])):
            tmpColors = np.random.rand(nbCatchment)
            catchColors = []
            for icolor in range(len(tmpColors)):
                if(not(envelop)):
                    catchColors.append(tmpColors[icolor])
                elif(idCatch==refName):
                    catchColors.append(tmpColors[icolor])
        else:
            catchColors = []
            catchColors = plotDict["General Parameters"]["Catchment colors"]


        if("Catchment traits" in plotDict["General Parameters"]):
            myTraits = []
            myTraits = plotDict["General Parameters"]["Catchment traits"]
            if(len(myTraits)!=nbCatchment):
                print("ERROR: the number of catchments is not the same as the number of colors given")
                sys.exit()


        if(len(catchColors)!=nbCatchment and not(envelop)):
            print("ERROR: the number of catchments is not the same as the number of colors given")
            sys.exit()

        if("Same rain" in plotDict["General Parameters"]):
            sameRain = plotDict["General Parameters"]["Same rain"]
        else:
            sameRain = True

        if("Display rain" in plotDict["General Parameters"]):
            displayRain = plotDict["General Parameters"]["Display rain"]
        else:
            displayRain = True

        if(refModuleName!=""):
            print("To Do !!!!")
            sys.exit()


        for id in basinId:

            y1 = []
            yLabels = []
            if(not("Catchment traits" in plotDict["General Parameters"])):
                myTraits = []
            rain = None
            z = []
            nbAddRain=0
            y_labelAddRain = []
            upperPlot = False
            allSurfaces = []
            mySurf = 0.0
            if(basinNames[id]=="BV Barrage Vesdre"):
                if(envelop):
                    firstKey = list(self.myCatchments.items())[0][0]
                    nbTElements = len(self.myCatchments[firstKey]['Object'].subBasinDict[id].get_outFlow_noDelay())
                    allHydros = np.zeros((nbTElements,nbCatchment))
                    counter = 0
                    for idCatch in self.myCatchments:
                        curCatch = self.myCatchments[idCatch]['Object']

                        tmp = curCatch.retentionBasinDict["J18"].directFluxInRB
                        tmpHydro = np.zeros(len(tmp))

                        index = math.floor(curCatch.retentionBasinDict["J18"].timeDelay/curCatch.retentionBasinDict["J18"].deltaT)
                        if(index==0):
                            tmpHydro = tmp
                        elif(index<len(tmp)):
                            tmpHydro[:-index] = tmp[index:]
                        else:
                            print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                            sys.exit()


                        allHydros[:,counter] = tmpHydro[:]


                        if(idCatch==refName):
                            y1.append(tmpHydro[:])
                            yLabels.append(curCatch.name)

                            if("Station Name" in plotDict[basinNames[id]]):
                                graph_title = plotDict[basinNames[id]]["Station Name"]
                            else:
                                graph_title = curCatch.subBasinDict[id].name

                            myTraits.append('-')

                    ymax = np.amax(allHydros, axis=1)
                    ymin = np.amin(allHydros, axis=1)

                else:
                    for idCatch in self.myCatchments:
                        curCatch = self.myCatchments[idCatch]['Object']
                        if(curCatch.myModel==cst.tom_UH):

                            # tmp = curCatch.retentionBasinDict["J18"].directFluxInRB
                            # tmpHydro = np.zeros(len(tmp))

                            # index = math.floor(curCatch.retentionBasinDict["J18"].timeDelay/curCatch.retentionBasinDict["J18"].deltaT)
                            # if(index==0):
                            #     tmpHydro = tmp
                            # elif(index<len(tmp)):
                            #     tmpHydro[:-index] = tmp[index:]
                            # else:
                            #     print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                            #     sys.exit()

                            cur_module:RetentionBasin = curCatch.retentionBasinDict["J18"]
                            tmpHydro = cur_module.get_direct_insideRB_inlets(unit='m3/s')

                            y1.append(tmpHydro[:])
                        else:

                            # tmp = curCatch.retentionBasinDict["J18"].directFluxInRB
                            # tmpHydro = np.zeros(len(tmp))

                            # index = math.floor(curCatch.retentionBasinDict["J18"].timeDelay/curCatch.retentionBasinDict["J18"].deltaT)
                            # if(index==0):
                            #     tmpHydro = tmp
                            # elif(index<len(tmp)):
                            #     tmpHydro[:-index] = tmp[index:]
                            # else:
                            #     print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                            #     sys.exit()
                            cur_module:RetentionBasin = curCatch.retentionBasinDict["J18"]
                            tmpHydro = cur_module.get_direct_insideRB_inlets(unit='m3/s')

                            y1.append(tmpHydro[:])
                        yLabels.append(curCatch.name)

                        if("Station Name" in plotDict[basinNames[id]]):
                            graph_title = plotDict[basinNames[id]]["Station Name"]
                        else:
                            graph_title = curCatch.subBasinDict[id].name

                        if(not("Catchment traits" in plotDict["General Parameters"])):
                                myTraits.append('-')


            elif(basinNames[id]=="BV Barrage Gileppe"):
                if(envelop):
                    firstKey = list(self.myCatchments.items())[0][0]
                    nbTElements = len(self.myCatchments[firstKey]['Object'].subBasinDict[id].get_outFlow_noDelay())
                    allHydros = np.zeros((nbTElements,nbCatchment))
                    counter = 0
                    for idCatch in self.myCatchments:
                        curCatch = self.myCatchments[idCatch]['Object']
                        tmp = curCatch.retentionBasinDict["J16"].directFluxInRB

                        tmpHydro = np.zeros(len(tmp))

                        index = math.floor(curCatch.retentionBasinDict["J16"].timeDelay/curCatch.retentionBasinDict["J18"].deltaT)
                        if(index==0):
                            tmpHydro = tmp
                        elif(index<len(tmp)):
                            tmpHydro[:-index] = tmp[index:]
                        else:
                            print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                            sys.exit()
                        allHydros[:,counter] = tmpHydro[:]

                        if(idCatch==refName):
                            y1.append(tmpHydro[:])
                            yLabels.append(curCatch.name)

                            if("Station Name" in plotDict[basinNames[id]]):
                                graph_title = plotDict[basinNames[id]]["Station Name"]
                            else:
                                graph_title = curCatch.subBasinDict[id].name

                            myTraits.append('-')


                    ymax = np.amax(allHydros, axis=1)
                    ymin = np.amin(allHydros, axis=1)

                else:
                    for idCatch in self.myCatchments:
                        curCatch = self.myCatchments[idCatch]['Object']
                        if(curCatch.myModel==cst.tom_UH):
                            # tmp = curCatch.subBasinDict[19].myHydro[:] + curCatch.retentionBasinDict["J19"].get_outFlow_noDelay()
                            # y1.append(tmp[:])
                            tmp = curCatch.retentionBasinDict["J16"].directFluxInRB
                            tmpHydro = np.zeros(len(tmp))

                            index = math.floor(curCatch.retentionBasinDict["J16"].timeDelay/curCatch.retentionBasinDict["J18"].deltaT)
                            if(index==0):
                                tmpHydro = tmp
                            elif(index<len(tmp)):
                                tmpHydro[:-index] = tmp[index:]
                            else:
                                print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                                sys.exit()
                            y1.append(tmpHydro[:])
                        else:
                            tmp = curCatch.retentionBasinDict["J16"].directFluxInRB
                            tmpHydro = np.zeros(len(tmp))

                            index = math.floor(curCatch.retentionBasinDict["J16"].timeDelay/curCatch.retentionBasinDict["J18"].deltaT)
                            if(index==0):
                                tmpHydro = tmp
                            elif(index<len(tmp)):
                                tmpHydro[:-index] = tmp[index:]
                            else:
                                print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                                sys.exit()
                            y1.append(tmpHydro[:])

                        yLabels.append(curCatch.name)

                        if("Station Name" in plotDict[basinNames[id]]):
                            graph_title = plotDict[basinNames[id]]["Station Name"]
                        else:
                            graph_title = curCatch.subBasinDict[id].name

                        if(not("Catchment traits" in plotDict["General Parameters"])):
                                myTraits.append('-')
            else:
                # Envelop graph. It will only save the min, max and the ref
                if(envelop):
                    firstKey = list(self.myCatchments.items())[0][0]
                    nbTElements = len(self.myCatchments[firstKey]['Object'].subBasinDict[id].get_outFlow_noDelay())
                    allHydros = np.zeros((nbTElements,nbCatchment))
                    counter = 0
                    for idCatch in self.myCatchments:
                        curCatch = self.myCatchments[idCatch]['Object']
                        tmp = curCatch.subBasinDict[id].get_outFlow_noDelay()
                        allHydros[:,counter] = tmp[:]
                        counter += 1

                        if(idCatch==refName):
                            y1.append(tmp[:])
                            yLabels.append(curCatch.name)

                            if("Station Name" in plotDict[basinNames[id]]):
                                graph_title = plotDict[basinNames[id]]["Station Name"]
                            else:
                                graph_title = curCatch.subBasinDict[id].name
                            myTraits.append('-')

                        if(sameRain and displayRain):
                            if(rain is None):
                                rain = curCatch.subBasinDict[id].rain/curCatch.subBasinDict[id].surfaceDrainedHydro*3.6
                        elif(displayRain):
                            upperPlot = True
                            nbAddRain += 1
                            z.append(curCatch.subBasinDict[id].rain/curCatch.subBasinDict[id].surfaceDrainedHydro*3.6)
                            y_labelAddRain.append(curCatch.name)

                    ymax = np.amax(allHydros, axis=1)
                    ymin = np.amin(allHydros, axis=1)

                else:
                    for idCatch in self.myCatchments:
                        curCatch = self.myCatchments[idCatch]['Object']
                        tmp = curCatch.subBasinDict[id].get_outFlow_noDelay()
                        y1.append(tmp[:])
                        yLabels.append(curCatch.name)

                        if("Station Name" in plotDict[basinNames[id]]):
                            graph_title = plotDict[basinNames[id]]["Station Name"]
                        else:
                            graph_title = curCatch.subBasinDict[id].name

                        if(not("Catchment traits" in plotDict["General Parameters"])):
                            myTraits.append('-')

                        if(sameRain and displayRain):
                            if(rain is None):
                                rain = curCatch.subBasinDict[id].rain/curCatch.subBasinDict[id].surfaceDrainedHydro*3.6
                        elif(displayRain):
                            upperPlot = True
                            nbAddRain += 1
                            z.append(curCatch.subBasinDict[id].rain/curCatch.subBasinDict[id].surfaceDrainedHydro*3.6)
                            y_labelAddRain.append(curCatch.name)

                        mySurf =  curCatch.subBasinDict[id].surfaceDrainedHydro


            nbAddData = 0
            beginDateAddData = []
            endDateAddData = []
            dtAddData = []
            catchColorsAddData = []
            if("Add Data" in plotDict[basinNames[id]]):
                nbAddData = len(plotDict[basinNames[id]]["Add Data"]["Data"])
                for i in range(nbAddData):
                    y1.append(plotDict[basinNames[id]]["Add Data"]["Data"][i][:])
                    if("Date Begin" in plotDict[basinNames[id]]["Add Data"]):
                        beginDateAddData.append(plotDict[basinNames[id]]["Add Data"]["Date Begin"][i]+tzDelta)
                    elif("Date Begin" in plotDict["General Parameters"]["Add Data"]):
                        beginDateAddData.append(plotDict["General Parameters"]["Add Data"]["Date Begin"][i]+tzDelta)

                    if("Date End" in plotDict[basinNames[id]]["Add Data"]):
                        endDateAddData.append(plotDict[basinNames[id]]["Add Data"]["Date End"][i]+tzDelta)
                    elif("Date End" in plotDict["General Parameters"]["Add Data"]):
                        endDateAddData.append(plotDict["General Parameters"]["Add Data"]["Date End"][i]+tzDelta)

                    if("Dt" in plotDict[basinNames[id]]["Add Data"]):
                        dtAddData.append(plotDict[basinNames[id]]["Add Data"]["Dt"][i])
                    elif("Dt" in plotDict["General Parameters"]["Add Data"]):
                        dtAddData.append(plotDict["General Parameters"]["Add Data"]["Dt"][i])

                    if("Labels" in plotDict[basinNames[id]]["Add Data"]):
                        yLabels.append(plotDict[basinNames[id]]["Add Data"]["Labels"][i])
                    elif("Labels" in plotDict["General Parameters"]["Add Data"]):
                        yLabels.append(plotDict["General Parameters"]["Add Data"]["Labels"][i])

                    if("Colors" in plotDict[basinNames[id]]["Add Data"]):
                        catchColorsAddData.append(plotDict[basinNames[id]]["Add Data"]["Colors"][i])
                    elif("Colors" in plotDict["General Parameters"]["Add Data"]):
                        catchColorsAddData.append(plotDict["General Parameters"]["Add Data"]["Colors"][i])

                    if("Type of Traits" in plotDict[basinNames[id]]["Add Data"]):
                        myTraits.append(plotDict[basinNames[id]]["Add Data"]["Type of Traits"][i])
                    elif("Type of Traits" in plotDict["General Parameters"]["Add Data"]):
                        myTraits.append(plotDict["General Parameters"]["Add Data"]["Type of Traits"][i])

            if("Measures" in plotDict[basinNames[id]]):
                Measures = plotDict[basinNames[id]]["Measures"]
                myMeasure = Measures.myHydro
                yLabels.append(_("Measurement"))
                catchColorsAddData.append('k')
                myTraits.append('-')
                if(Measures.surfaceDrainedHydro>0.0):
                    surfaceMeasure=Measures.surfaceDrainedHydro
                elif(mySurf!=0.0):
                    surfaceMeasure = mySurf
                else:
                    surfaceMeasure = -1.0
            else:
                myMeasure = []
                Measures = None

            if("X Range" in plotDict["General Parameters"]):
                xRange = plotDict["General Parameters"]["X Range"]
            else:
                xRange = []

            if("Y Range" in plotDict["General Parameters"]):
                yRange = plotDict["General Parameters"]["Y Range"]
            else:
                yRange = []

            if("Writing Directory" in plotDict["General Parameters"]):
                writeFile = plotDict["General Parameters"]["Writing Directory"]
            else:
                writeFile = ""

            if("Add Measure in table" in plotDict["General Parameters"]):
                addMeasfInTab = plotDict["General Parameters"]["Add Measure in table"]
            else:
                addMeasfInTab = False


            if(mySurf!=0.0):
                allSurfaces = [mySurf]*(nbCatchment+nbAddData)

            # Plot Rains
            yTitles = _("Discharge [m³/s]")
            writeFileDef = os.path.join(writeFile, "OutFlow_" + graph_title.replace(".",""))
            if(Measures is not None):
                if(envelop):
                    ph.plot_hydro(1+nbAddData,y1,rain=rain,x_title=x_title, y_titles=yTitles, beginDate=beginDate+beginDateAddData,endDate=endDate+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                            measures=myMeasure,beginDateMeasure=Measures.dateBegin+tzDelta, endDateMeasure=Measures.dateEnd+tzDelta, dtMeasure=Measures.deltaT, surfaceMeasure=surfaceMeasure, addMeasfInTab=addMeasfInTab,\
                            upperPlot=upperPlot,nbAddPlot=nbAddRain,z=z,y_labelAddPlot=y_labelAddRain,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,\
                            y_envelop=[ymin,ymax],addTable=addTable, allSurfaces=allSurfaces)
                else:
                    ph.plot_hydro(nbCatchment+nbAddData,y1,rain=rain,x_title=x_title, y_titles=yTitles, beginDate=beginDate+beginDateAddData,endDate=endDate+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                            measures=myMeasure,beginDateMeasure=Measures.dateBegin+tzDelta, endDateMeasure=Measures.dateEnd+tzDelta, dtMeasure=Measures.deltaT, surfaceMeasure=surfaceMeasure, addMeasfInTab=addMeasfInTab,\
                            upperPlot=upperPlot,nbAddPlot=nbAddRain,z=z,y_labelAddPlot=y_labelAddRain,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,addTable=addTable,allSurfaces=allSurfaces)

            else:
                if(envelop):
                    ph.plot_hydro(1+nbAddData,y1,rain=rain,x_title=x_title, y_titles=yTitles, beginDate=beginDate+beginDateAddData,endDate=endDate+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                                y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                                upperPlot=upperPlot,nbAddPlot=nbAddRain,z=z,y_labelAddPlot=y_labelAddRain,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,\
                                y_envelop=[ymin,ymax],addTable=addTable,allSurfaces=allSurfaces)
                else:
                    ph.plot_hydro(nbCatchment+nbAddData,y1,rain=rain,x_title=x_title, y_titles=yTitles, beginDate=beginDate+beginDateAddData,endDate=endDate+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                            upperPlot=upperPlot,nbAddPlot=nbAddRain,z=z,y_labelAddPlot=y_labelAddRain,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,addTable=addTable,allSurfaces=allSurfaces)


        if(show):
            plt.show()



    def outlet_all_RB_height_same_topo(self, plotDict={}, show=True, envelop=False, displayMax=False):
        """
        Plot the heights of all rentention basin. The measures given should also be heights in [m].
        This function considers that the topology in all the catchments is the same.
        """
        if(not("Time Zone Plot" in plotDict["General Parameters"])):
            tzPlot = 0
            tzDelta = datetime.timedelta(hours=0)
        else:
            tzPlot = plotDict["General Parameters"]["Time Zone Plot"]
            tzDelta = datetime.timedelta(hours=tzPlot)

        if(not("Date Begin" in plotDict["General Parameters"])):
            beginDate = []
            for idCatch in self.myCatchments:
                beginDate.append(self.myCatchments[idCatch]['Object'].dateBegin+tzDelta)
        else:
            beginDate = plotDict["General Parameters"]["Date Begin"]+tzDelta

        if(not("Date End" in plotDict["General Parameters"])):
            endDate = []
            for idCatch in self.myCatchments:
                endDate.append(self.myCatchments[idCatch]['Object'].dateEnd+tzDelta)
        else:
            endDate = plotDict["General Parameters"]["Date End"]+tzDelta

        if(not("Dt" in plotDict["General Parameters"])):
            dt=[]
            for idCatch in self.myCatchments:
                dt.append(self.myCatchments[idCatch]['Object'].deltaT)
        else:
            dt = plotDict["General Parameters"]["Dt"]

        if(not("Add Table" in plotDict["General Parameters"])):
            addTable = False
        else:
            addTable = plotDict["General Parameters"]["Add Table"]

        # if(envelop and not("Ref Name" in plotDict["General Parameters"])):
        #     refName = "Catchment 1"

        # else:
        #     refName = plotDict["General Parameters"]["Ref Name"]


        RBId = [] # contains all the names of the subbasin
        RBNames = {}
        for idCatch in self.myCatchments:
            curCatch = self.myCatchments[idCatch]['Object']
            for id in curCatch.retentionBasinDict:
                curBasin = curCatch.retentionBasinDict[id]
                if(not(id in RBId) and (curBasin.name in plotDict)):
                    RBId.append(id)
                    RBNames[id] = (curBasin.name)



        nbCatchment = len(self.myCatchments)
        x_title = "Dates " + "(GMT+" + str(tzPlot) + ")"


        if(not("Catchment colors" in plotDict["General Parameters"])):
            tmpColors = np.random.rand(nbCatchment)
            catchColors = []
            for icolor in range(len(tmpColors)):
                catchColors.append(tmpColors[icolor])
        else:
            catchColors = []
            catchColors = plotDict["General Parameters"]["Catchment colors"]
        if(len(catchColors)!=nbCatchment):
            print("ERROR: the number of catchments is not the same as the number of colors given")
            sys.exit()

        if("Catchment traits" in plotDict["General Parameters"]):
            myTraits = []
            myTraits = plotDict["General Parameters"]["Catchment traits"]
            if(len(myTraits)!=nbCatchment):
                print("ERROR: the number of catchments is not the same as the number of colors given")
                sys.exit()


        for id in RBId:

            y1 = []
            yLabels = []
            myTraits = []
            timeDelay = []
            for idCatch in self.myCatchments:
                curCatch = self.myCatchments[idCatch]['Object']
                myH = np.zeros(len(curCatch.retentionBasinDict[id].filledVolume))
                for ii in range(len(curCatch.retentionBasinDict[id].filledVolume)):
                    myH[ii] =  curCatch.retentionBasinDict[id].volume_to_h(curCatch.retentionBasinDict[id].filledVolume[ii])
                y1.append(myH[:])
                yLabels.append(curCatch.name)
                timeDelay.append(datetime.timedelta(seconds=curCatch.retentionBasinDict[id].timeDelay))

            beginDateRB = []
            endDateRB = []
            for ii in range(nbCatchment):
                # beginDateRB.append(beginDate[ii] - timeDelay[ii])   # A ameliorer!!!
                # endDateRB.append(endDate[ii] - timeDelay[ii])
                beginDateRB.append(beginDate[ii])   # A ameliorer!!!
                endDateRB.append(endDate[ii])


                if("Station Name" in plotDict[RBNames[id]]):
                    graph_title = plotDict[RBNames[id]]["Station Name"]
                else:
                    graph_title = curCatch.retentionBasinDict[id].name

                if(not("Catchment traits" in plotDict["General Parameters"])):
                    myTraits.append('-')


            nbAddData = 0
            beginDateAddData = []
            endDateAddData = []
            dtAddData = []
            catchColorsAddData = []
            if("Add Data" in plotDict[RBNames[id]]):
                nbAddData = len(plotDict[RBNames[id]]["Add Data"]["Data"])
                for i in range(nbAddData):
                    y1.append(plotDict[RBNames[id]]["Add Data"]["Data"][i][:])
                    if("Date Begin" in plotDict[RBNames[id]]["Add Data"]):
                        beginDateAddData.append(plotDict[RBNames[id]]["Add Data"]["Date Begin"][i]+tzDelta)
                    elif("Date Begin" in plotDict["General Parameters"]["Add Data"]):
                        beginDateAddData.append(plotDict["General Parameters"]["Add Data"]["Date Begin"][i]+tzDelta)

                    if("Date End" in plotDict[RBNames[id]]["Add Data"]):
                        endDateAddData.append(plotDict[RBNames[id]]["Add Data"]["Date End"][i]+tzDelta)
                    elif("Date End" in plotDict["General Parameters"]["Add Data"]):
                        endDateAddData.append(plotDict["General Parameters"]["Add Data"]["Date End"][i]+tzDelta)

                    if("Dt" in plotDict[RBNames[id]]["Add Data"]):
                        dtAddData.append(plotDict[RBNames[id]]["Add Data"]["Dt"][i])
                    elif("Dt" in plotDict["General Parameters"]["Add Data"]):
                        dtAddData.append(plotDict["General Parameters"]["Add Data"]["Dt"][i])

                    if("Labels" in plotDict[RBNames[id]]["Add Data"]):
                        yLabels.append(plotDict[RBNames[id]]["Add Data"]["Labels"][i])
                    elif("Labels" in plotDict["General Parameters"]["Add Data"]):
                        yLabels.append(plotDict["General Parameters"]["Add Data"]["Labels"][i])

                    if("Colors" in plotDict[RBNames[id]]["Add Data"]):
                        catchColorsAddData.append(plotDict[RBNames[id]]["Add Data"]["Colors"][i])
                    elif("Colors" in plotDict["General Parameters"]["Add Data"]):
                        catchColorsAddData.append(plotDict["General Parameters"]["Add Data"]["Colors"][i])

                    if("Type of Traits" in plotDict[RBNames[id]]["Add Data"]):
                        myTraits.append(plotDict[RBNames[id]]["Add Data"]["Type of Traits"][i])
                    elif("Type of Traits" in plotDict["General Parameters"]["Add Data"]):
                        myTraits.append(plotDict["General Parameters"]["Add Data"]["Type of Traits"][i])

            if("Y Range" in plotDict[RBNames[id]]):
                yRange = plotDict[RBNames[id]]["Y Range"]
            elif("Y Range" in plotDict["General Parameters"]):
                yRange = plotDict["General Parameters"]["Y Range"]
            else:
                yRange = []

            if("Measures" in plotDict[RBNames[id]]):
                Measures = plotDict[RBNames[id]]["Measures"]
                myMeasure = Measures.myHydro
                yLabels.append(_("Measurement"))
                catchColorsAddData.append('k')
                myTraits.append('--')
            else:
                myMeasure = []
                Measures = None

            if("X Range" in plotDict["General Parameters"]):
                xRange = plotDict["General Parameters"]["X Range"]
            else:
                xRange = []


            if("Writing Directory" in plotDict["General Parameters"]):
                writeFile = plotDict["General Parameters"]["Writing Directory"]
            else:
                writeFile = ""





            # Plot Rains
            yTitles = _("Water level [m]")
            writeFileDef = os.path.join(writeFile, "H_" + graph_title.replace(".",""))
            if(Measures is not None):
                ph.plot_hydro(nbCatchment+nbAddData, y1,x_title=x_title, y_titles=yTitles, beginDate=beginDateRB+beginDateAddData,endDate=endDateRB+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                            measures=myMeasure,beginDateMeasure=Measures.dateBegin+tzDelta, endDateMeasure=Measures.dateEnd+tzDelta,dtMeasure=Measures.deltaT,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,
                            addTable=addTable)
            else:
                ph.plot_hydro(nbCatchment+nbAddData, y1,x_title=x_title, y_titles=yTitles, beginDate=beginDateRB+beginDateAddData,endDate=endDateRB+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,
                            addTable=addTable)

        if(show):
            plt.show()


    def outlet_all_RB_hydro_same_topo(self, plotDict={}, show=True, envelop=False, refModuleName =""):

        # Load General characteristics of the dictionnary
        if(not("Time Zone Plot" in plotDict["General Parameters"])):
            tzPlot = 0
            tzDelta = datetime.timedelta(hours=0)
        else:
            tzPlot = plotDict["General Parameters"]["Time Zone Plot"]
            tzDelta = datetime.timedelta(hours=tzPlot)

        #******************************************************
        #FIXME : is it correct ??
        if(envelop and not("Ref Name" in plotDict["General Parameters"])):
            refName = "Catchment 1"
        else:
            refName = plotDict["General Parameters"]["Ref Name"]
        #******************************************************

        if(not("Add Table" in plotDict["General Parameters"])):
            addTable = False
        else:
            addTable = plotDict["General Parameters"]["Add Table"]

        if(not("Date Begin" in plotDict["General Parameters"])):
            beginDate = []
            for idCatch in self.myCatchments:
                if(not(envelop)):
                    beginDate.append(self.myCatchments[idCatch]['Object'].dateBegin+tzDelta)
                elif(idCatch==refName):
                    beginDate.append(self.myCatchments[idCatch]['Object'].dateBegin+tzDelta)
        else:
            beginDate = plotDict["General Parameters"]["Date Begin"]+tzDelta

        if(not("Date End" in plotDict["General Parameters"])):
            endDate = []
            for idCatch in self.myCatchments:
                if(not(envelop)):
                    endDate.append(self.myCatchments[idCatch]['Object'].dateEnd+tzDelta)
                elif(idCatch==refName):
                    endDate.append(self.myCatchments[idCatch]['Object'].dateEnd+tzDelta)
        else:
            endDate = plotDict["General Parameters"]["Date End"]+tzDelta

        if(not("Dt" in plotDict["General Parameters"])):
            dt=[]
            for idCatch in self.myCatchments:
                if(not(envelop)):
                    dt.append(self.myCatchments[idCatch]['Object'].deltaT)
                elif(idCatch==refName):
                    dt.append(self.myCatchments[idCatch]['Object'].deltaT)
        else:
            dt = plotDict["General Parameters"]["Dt"]



        # All the useful junctions will be listed so that all the elements won't be analysed anymore
        RBId = [] # contains all the names of the subbasin
        RBNames = {}
        for idCatch in self.myCatchments:
            curCatch = self.myCatchments[idCatch]['Object']
            for id in curCatch.retentionBasinDict:
                curBasin = curCatch.retentionBasinDict[id]
                if(not(id in RBId) and (curBasin.name in plotDict)):
                    RBId.append(id)
                    RBNames[id] = (curBasin.name)



        nbCatchment = len(self.myCatchments)
        x_title = "Dates " + "(GMT+"+ str(tzPlot) + ")"


        if(not("Catchment colors" in plotDict["General Parameters"])):
            tmpColors = np.random.rand(nbCatchment)
            catchColors = []
            for icolor in range(len(tmpColors)):
                if(not(envelop)):
                    catchColors.append(tmpColors[icolor])
                elif(idCatch==refName):
                    catchColors.append(tmpColors[icolor])
        else:
            catchColors = []
            catchColors = plotDict["General Parameters"]["Catchment colors"]


        if("Catchment traits" in plotDict["General Parameters"]):
            myTraits = []
            myTraits = plotDict["General Parameters"]["Catchment traits"]
            if(len(myTraits)!=nbCatchment):
                print("ERROR: the number of catchments is not the same as the number of colors given")
                sys.exit()


        if(len(catchColors)!=nbCatchment and not(envelop)):
            print("ERROR: the number of catchments is not the same as the number of colors given")
            sys.exit()


        if(refModuleName!=""):
            print("To Do !!!!")
            sys.exit()


        for id in RBId:

            y1 = []
            yLabels = []
            if(not("Catchment traits" in plotDict["General Parameters"])):
                myTraits = []
            rain = None
            z = []
            nbAddRain=0
            y_labelAddRain = []
            upperPlot = False
            allSurfaces = []
            mySurf = 0.0
            if(envelop):
                firstKey = list(self.myCatchments.items())[0][0]
                nbTElements = len(self.myCatchments[firstKey]['Object'].subBasinDict[id].get_outFlow_noDelay())
                allHydros = np.zeros((nbTElements,nbCatchment))
                counter = 0
                for idCatch in self.myCatchments:
                    curCatch = self.myCatchments[idCatch]['Object']

                    tmp = curCatch.retentionBasinDict["J18"].directFluxInRB
                    tmpHydro = np.zeros(len(tmp))

                    index = math.floor(curCatch.retentionBasinDict["J18"].timeDelay/curCatch.retentionBasinDict["J18"].deltaT)
                    if(index==0):
                        tmpHydro = tmp
                    elif(index<len(tmp)):
                        tmpHydro[:-index] = tmp[index:]
                    else:
                        print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                        sys.exit()


                    allHydros[:,counter] = tmpHydro[:]


                    if(idCatch==refName):
                        y1.append(tmpHydro[:])
                        yLabels.append(curCatch.name)

                        if("Station Name" in plotDict[basinNames[id]]):
                            graph_title = plotDict[basinNames[id]]["Station Name"]
                        else:
                            graph_title = curCatch.subBasinDict[id].name

                        myTraits.append('-')

                ymax = np.amax(allHydros, axis=1)
                ymin = np.amin(allHydros, axis=1)

            else:
                for idCatch in self.myCatchments:
                    curCatch = self.myCatchments[idCatch]['Object']
                    if(curCatch.myModel==cst.tom_UH):

                        tmp = curCatch.retentionBasinDict[id].directFluxInRB
                        tmpHydro = np.zeros(len(tmp))

                        index = math.floor(curCatch.retentionBasinDict[id].timeDelay/curCatch.retentionBasinDict[id].deltaT)
                        if(index==0):
                            tmpHydro = tmp
                        elif(index<len(tmp)):
                            tmpHydro[:-index] = tmp[index:]
                        else:
                            print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                            sys.exit()

                        y1.append(tmpHydro[:])
                    elif(curCatch.myModel==cst.tom_2layers_linIF or curCatch.myModel==cst.tom_2layers_UH):

                        tmp = curCatch.retentionBasinDict[id].directFluxInRB
                        tmpHydro = np.zeros(len(tmp))

                        index = math.floor(curCatch.retentionBasinDict[id].timeDelay/curCatch.retentionBasinDict[id].deltaT)
                        if(index==0):
                            tmpHydro = tmp
                        elif(index<len(tmp)):
                            tmpHydro[:-index] = tmp[index:]
                        else:
                            print("ERROR: the simulation time is not long enough for this subbasin to be taken into account")
                            sys.exit()

                        y1.append(tmpHydro[:])
                    yLabels.append(curCatch.name)

                    if("Station Name" in plotDict[RBNames[id]]):
                        graph_title = plotDict[RBNames[id]]["Station Name"]
                    else:
                        graph_title = curCatch.retentionBasinDict[id].name

                    if(not("Catchment traits" in plotDict["General Parameters"])):
                            myTraits.append('-')




            nbAddData = 0
            beginDateAddData = []
            endDateAddData = []
            dtAddData = []
            catchColorsAddData = []
            if("Add Data" in plotDict[RBNames[id]]):
                nbAddData = len(plotDict[RBNames[id]]["Add Data"]["Data"])
                for i in range(nbAddData):
                    y1.append(plotDict[RBNames[id]]["Add Data"]["Data"][i][:])
                    if("Date Begin" in plotDict[RBNames[id]]["Add Data"]):
                        beginDateAddData.append(plotDict[RBNames[id]]["Add Data"]["Date Begin"][i]+tzDelta)
                    elif("Date Begin" in plotDict["General Parameters"]["Add Data"]):
                        beginDateAddData.append(plotDict["General Parameters"]["Add Data"]["Date Begin"][i]+tzDelta)

                    if("Date End" in plotDict[RBNames[id]]["Add Data"]):
                        endDateAddData.append(plotDict[RBNames[id]]["Add Data"]["Date End"][i]+tzDelta)
                    elif("Date End" in plotDict["General Parameters"]["Add Data"]):
                        endDateAddData.append(plotDict["General Parameters"]["Add Data"]["Date End"][i]+tzDelta)

                    if("Dt" in plotDict[RBNames[id]]["Add Data"]):
                        dtAddData.append(plotDict[RBNames[id]]["Add Data"]["Dt"][i])
                    elif("Dt" in plotDict["General Parameters"]["Add Data"]):
                        dtAddData.append(plotDict["General Parameters"]["Add Data"]["Dt"][i])

                    if("Labels" in plotDict[RBNames[id]]["Add Data"]):
                        yLabels.append(plotDict[RBNames[id]]["Add Data"]["Labels"][i])
                    elif("Labels" in plotDict["General Parameters"]["Add Data"]):
                        yLabels.append(plotDict["General Parameters"]["Add Data"]["Labels"][i])

                    if("Colors" in plotDict[RBNames[id]]["Add Data"]):
                        catchColorsAddData.append(plotDict[RBNames[id]]["Add Data"]["Colors"][i])
                    elif("Colors" in plotDict["General Parameters"]["Add Data"]):
                        catchColorsAddData.append(plotDict["General Parameters"]["Add Data"]["Colors"][i])

                    if("Type of Traits" in plotDict[RBNames[id]]["Add Data"]):
                        myTraits.append(plotDict[RBNames[id]]["Add Data"]["Type of Traits"][i])
                    elif("Type of Traits" in plotDict["General Parameters"]["Add Data"]):
                        myTraits.append(plotDict["General Parameters"]["Add Data"]["Type of Traits"][i])

            if("Measures" in plotDict[RBNames[id]]):
                Measures = plotDict[RBNames[id]]["Measures"]
                myMeasure = Measures.myHydro
                yLabels.append(_("Measurement"))
                catchColorsAddData.append('k')
                myTraits.append('-')
                if(Measures.surfaceDrainedHydro>0.0):
                    surfaceMeasure=Measures.surfaceDrainedHydro
                elif(mySurf!=0.0):
                    surfaceMeasure = mySurf
            else:
                myMeasure = []
                Measures = None

            if("X Range" in plotDict["General Parameters"]):
                xRange = plotDict["General Parameters"]["X Range"]
            else:
                xRange = []

            if("Y Range" in plotDict["General Parameters"]):
                yRange = plotDict["General Parameters"]["Y Range"]
            else:
                yRange = []

            if("Writing Directory" in plotDict["General Parameters"]):
                writeFile = plotDict["General Parameters"]["Writing Directory"]
            else:
                writeFile = ""

            if("Add Measure in table" in plotDict["General Parameters"]):
                addMeasfInTab = plotDict["General Parameters"]["Add Measure in table"]
            else:
                addMeasfInTab = False


            if(mySurf!=0.0):
                allSurfaces = [mySurf]*(nbCatchment+nbAddData)

            # Plot Rains
            yTitles = _("Discharge [m³/s]")
            writeFileDef = writeFile + "OutFlow_" + graph_title.replace(".","")
            if(Measures is not None):
                if(envelop):
                    ph.plot_hydro(1+nbAddData,y1,rain=rain,x_title=x_title, y_titles=yTitles, beginDate=beginDate+beginDateAddData,endDate=endDate+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                            measures=myMeasure,beginDateMeasure=Measures.dateBegin+tzDelta, endDateMeasure=Measures.dateEnd+tzDelta, dtMeasure=Measures.deltaT, addMeasfInTab=False,\
                            upperPlot=upperPlot,nbAddPlot=nbAddRain,z=z,y_labelAddPlot=y_labelAddRain,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,\
                            y_envelop=[ymin,ymax],addTable=addTable, allSurfaces=allSurfaces)
                else:
                    ph.plot_hydro(nbCatchment+nbAddData,y1,rain=rain,x_title=x_title, y_titles=yTitles, beginDate=beginDate+beginDateAddData,endDate=endDate+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                            measures=myMeasure,beginDateMeasure=Measures.dateBegin+tzDelta, endDateMeasure=Measures.dateEnd+tzDelta, dtMeasure=Measures.deltaT, addMeasfInTab=False,\
                            upperPlot=upperPlot,nbAddPlot=nbAddRain,z=z,y_labelAddPlot=y_labelAddRain,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,addTable=addTable,allSurfaces=allSurfaces)

            else:
                if(envelop):
                    ph.plot_hydro(1+nbAddData,y1,rain=rain,x_title=x_title, y_titles=yTitles, beginDate=beginDate+beginDateAddData,endDate=endDate+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                                y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                                upperPlot=upperPlot,nbAddPlot=nbAddRain,z=z,y_labelAddPlot=y_labelAddRain,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,\
                                y_envelop=[ymin,ymax],addTable=addTable,allSurfaces=allSurfaces)
                else:
                    ph.plot_hydro(nbCatchment+nbAddData,y1,rain=rain,x_title=x_title, y_titles=yTitles, beginDate=beginDate+beginDateAddData,endDate=endDate+endDateAddData,dt=dt+dtAddData,graph_title=graph_title, \
                            y_labels=yLabels,rangeData=xRange,y_data_range=yRange,myColors=catchColors+catchColorsAddData,typeOfTraits=myTraits,writeFile=writeFileDef,\
                            upperPlot=upperPlot,nbAddPlot=nbAddRain,z=z,y_labelAddPlot=y_labelAddRain,deltaMajorTicks=86400/2.0,deltaMinorTicks=3600,addTable=addTable,allSurfaces=allSurfaces)


        if(show):
            plt.show()


    def plot_ind_subBasins(self, withEvap=False, withCt=False, selection_by_iD=[], writeDir=""):
        """
        Plot subbasins selected by id from all catchment on individual graphs. Not regrouped yet on a sigle graph.
        """

        for idCatch in self.myCatchments:
            graph_title = self.myCatchments[idCatch]['Object'].name + " :"
            writeFile = writeDir + self.myCatchments[idCatch]['Object'].name
            self.myCatchments[idCatch]['Object'].plot_allSub(withEvap=withEvap, withCt=withCt, selection_by_iD=selection_by_iD, graph_title=graph_title, show=False, writeDir=writeFile)



    def plot_all_diff_cumulRain_with_lagtime(self, interval=0, selection_by_iD=[], writeDir=""):

        for idCatch in self.myCatchments:
            curCatch:Catchment = self.myCatchments[idCatch]['Object']
            graph_title = curCatch.name + " :"
            curCatch.plot_all_diff_cumulRain_with_lagtime(interval, lagTime=0.0, selection_by_iD=selection_by_iD, graph_title=graph_title, show=False, writeDir=writeDir)



    # FIXME : TODO complete that function that plot a comparison of the cumulated volumes
    # def plot_all_cumulRain(self, selection_by_iD:list=[], writeDir:str="", show:bool=True):

    #     times = []
    #     for idCatch in self.myCatchments:
    #         curCatch:Catchment = self.myCatchments[idCatch]['Object']
    #         graph_title = curCatch.name + " :"
    #         cur_t, curVol = curCatch.get_all_cumulRain(selection_by_iD)

    #     for
    #         plt.figure()
    #         plt.title(graph_title)
    #         for i in range(len(curVol)):
    #             plt.plot(cur_t, curVol[i])
    #         plt.savefig(os.path.join(writeDir, graph_title))

    #     if show : plt.show()



    def save_all_ExcelFile_Vesdre_simul2D(self, writeDir=""):

        if(writeDir==""):
            writeDir = self.workingDir

        for idCatch in self.myCatchments:
            curCatch = self.myCatchments[idCatch]['Object']
            fileName = curCatch.name.replace("/","_") + "_Data_simul2D.xlsx"
            fileName = fileName.replace(" ", "_")
            curCatch.save_ExcelFile_Vesdre_simul2D(fileName=fileName, directory=writeDir)




    def construct_default_plotDict(self, mycolors=[]):

        nbCatchments = len(self.myCatchments)
        allColors = ["b","r","g","m","tab:pink","c","tab:gray","tab:brown"]
        if(mycolors==[]):
            if(nbCatchments>len(allColors)):
                print("ERROR : the number of comparison is greater than the number of saved colors. Please execute this fonction again and specify your own colors in 'mycolors='")
                sys.exit()
            else:
                mycolors = allColors[:nbCatchments]


        self.plotDict["General Parameters"] = {}
        self.plotDict["General Parameters"]["Writing Directory"] = self.workingDir
        self.plotDict["General Parameters"]["Catchment colors"] = mycolors
        self.plotDict["General Parameters"]["X Range"] = []
        self.plotDict["General Parameters"]["Y Range"] = []
        self.plotDict["General Parameters"]["Same rain"] = True
        self.plotDict["General Parameters"]["Display rain"] = True

        self.plotDict["General Parameters"]["Time Zone Plot"] = 0    # GMT+0
        self.plotDict["General Parameters"]["Display rain"] = False
        self.plotDict["General Parameters"]["Add Measure in table"] = False



    def add_stations_to_plotDict(self, stationKeys:list=[], stationNames:list=[], measures:list=[]):

        nbStations = len(stationKeys)
        for i in range(nbStations):
            element  = stationKeys[i]
            self.plotDict[element] = {}
            if(stationNames!=[]):
                if(stationNames[i]!=""):
                    name = stationNames[i]
                    self.plotDict[element]["Station Name"] = name
            if(measures!=[]):
                if(measures[i]is not None):
                    self.plotDict[element]["Measures"] = measures[i]



    def add_station_to_plotDict(self, stationKey:str, stationName:str="",measure=None, xRange=None, yRange=None):

        if(not(stationKey in self.plotDict)):
            self.plotDict[stationKey] = {}

        if(measure is not None):
            self.plotDict[stationKey]["Measures"] = measure

        if(xRange is not None):
            self.plotDict[stationKey]["X Range"] = xRange
        if(yRange is not None):
            self.plotDict[stationKey]["Y Range"] = yRange



    def add_data_in_station(self, stationKey:str, data:list=[], datesBegin:list=[], datesEnd:list=[], deltaT:list=[], labels:list=[], colors:list=[], typeOfTraits:list=[], addDataObj:list=[], addDataUnits:str="m3/s"):

        # If the name of the station is not already in the dictionnary we created it.
        if(not(stationKey in self.plotDict)):
            self.add_station_to_plotDict(stationKey)

        if(not("Add Data" in self.plotDict["General Parameters"])):
            self.plotDict["General Parameters"]["Add Data"] = {}

        self.plotDict[stationKey]["Add Data"] = {}

        if(addDataObj==[]):
            if(data==[]):
                print("WARNING: no additionnal data given in this station!")
                del self.plotDict[stationKey]["Add Data"]
                return
            self.plotDict[stationKey]["Add Data"]["Data"] = data
            if(datesBegin!=[]):
                self.plotDict[stationKey]["Add Data"]["Date Begin"] = datesBegin
            if(datesEnd!=[]):
                self.plotDict[stationKey]["Add Data"]["Date End"] = datesEnd
            if(deltaT!=[]):
                self.plotDict[stationKey]["Add Data"]["Dt"] = deltaT
        else:
            self.add_data_in_station_from_Subbasin(stationKey, addDataObj, addDataUnits=addDataUnits)
        if(labels!=[]):
            self.plotDict[stationKey]["Add Data"]["Labels"] = labels
        if(colors!=[]):
            self.plotDict[stationKey]["Add Data"]["Colors"] = colors
        if(typeOfTraits!=[]):
            self.plotDict[stationKey]["Add Data"]["Type of Traits"] = typeOfTraits



    def add_data_in_station_from_Subbasin(self, stationKey:str, myAddDataObj:list, addDataUnits:str="m3/s"):

        self.plotDict[stationKey]["Add Data"]["Data"] = []
        self.plotDict[stationKey]["Add Data"]["Date Begin"] = []
        self.plotDict[stationKey]["Add Data"]["Date End"] = []
        self.plotDict[stationKey]["Add Data"]["Dt"] = []

        for element in myAddDataObj:
            self.plotDict[stationKey]["Add Data"]["Data"].append(element.get_myHydro(unit=addDataUnits))
            self.plotDict[stationKey]["Add Data"]["Date Begin"].append(element.dateBegin)
            self.plotDict[stationKey]["Add Data"]["Date End"].append(element.dateEnd)
            self.plotDict[stationKey]["Add Data"]["Dt"].append(element.deltaT)


    def set_general_plot(self, xRange=None, yRange=None, timeZone=None,sameRain=None, displayRain=None, addTable=None, addMeasureTable=None, refName=None, writingDir=""):

        if(xRange is not None):
            self.plotDict["General Parameters"]["X Range"] = xRange
        if(yRange is not None):
            self.plotDict["General Parameters"]["Y Range"] = yRange
        if(timeZone is not None):
            self.plotDict["General Parameters"]["Time Zone Plot"] = timeZone
        if(sameRain is not None):
            self.plotDict["General Parameters"]["Same rain"] = sameRain
        if(displayRain is not None):
            self.plotDict["General Parameters"]["Display rain"] = displayRain
        if(addTable is not None):
            self.plotDict["General Parameters"]["Add Table"] = addTable
        if(addMeasureTable is not None):
            self.plotDict["General Parameters"]["Add Measure in table"] = addMeasureTable
        if(refName is not None):
            self.plotDict["General Parameters"]["Ref Name"] = refName
        if(writingDir!=""):
            self.plotDict["General Parameters"]["Writing Directory"] = writingDir



    def set_station_plot(self, stationKey, xRange=None, yRange=None, measure=None):

        if(xRange is not None):
            self.plotDict[stationKey]["X Range"] = xRange
        if(yRange is not None):
            self.plotDict[stationKey]["Y Range"] = yRange
        if(measure is not None):
            self.plotDict[stationKey]["Measures"] = measure


    def reset_addData(self, stationKey, backupAddData=None):

        backupAddData = self.plotDict[stationKey]["Add Data"]
        # self.plotDict[stationKey]["Add Data"] = {}
        del self.plotDict[stationKey]["Add Data"]



    def plot_Nash_and_peak(self, stationKey:list[str, int], measures:list[SubBasin], intervals:list=[], toShow:bool=True):
        assert len(stationKey) == len(measures)

        all_ns = {stationKey[i]: [ self.myCatchments[el]["Object"].get_sub_Nash(measures[i], stationKey[i], intervals)
                    for el in self.myCatchments ]
                  for i in range(len(stationKey))
                }
        print(all_ns)

        all_peaks = [ [ self.myCatchments[el]["Object"].get_sub_peak(stationKey[i], intervals)
                        for el in self.myCatchments ]
                     for i in range(len(stationKey))
                    ]

        print(all_peaks)

        meas_peak = [ measures[i].get_peak(intervals)
                     for i in range(len(stationKey)) ]

        # The following lines is take the peak difference between simulation and measurements -> Display 0.0 if the measurement is 0.0
        isZero = np.array(meas_peak)==0
        notZero = np.array(meas_peak)!=0
        peak_prop = {stationKey[i]: [ list( (np.array(el)-np.array(meas_peak[i]))/(np.array(meas_peak[i])+isZero[i]) *notZero[i] )
                        for el in all_peaks[i] ]
                     for i in range(len(stationKey))
                    }

        print(meas_peak)
        print(peak_prop)

        all_data = [all_ns, peak_prop]

        # Define all colors
        colors_Nash = {}
        for key, value in all_ns.items():
            colors_Nash[key] = []
            for i_model in range(len(value)):
                colors_Nash[key].append([])
                for j in range(len(value[i_model])):
                    curNS = value[i_model][j]
                    if curNS<0.0:
                        colors_Nash[key][i_model].append("r")
                        continue
                    elif curNS<0.4:
                        colors_Nash[key][i_model].append("tab:orange")
                        continue
                    elif curNS<0.6:
                        colors_Nash[key][i_model].append("tab:olive")
                        continue
                    elif curNS<0.8:
                        colors_Nash[key][i_model].append("tab:green")
                        continue
                    else:
                        colors_Nash[key][i_model].append("g")


        colors_peaks = {}
        for key, value in peak_prop.items():
            colors_peaks[key] = []
            for i_model in range(len(value)):
                colors_peaks[key].append([])
                for j in range(len(value[i_model])):
                    curP = value[i_model][j]
                    if curP<0.0:
                        colors_peaks[key][i_model].append("r")
                    else:
                        colors_peaks[key][i_model].append("b")

        all_colors = [colors_Nash, colors_peaks]

        ## Sort all station in a particular order
        sorted_keys = list(all_data[0].keys())

        ## Str of dates
        all_names = ["\n - \n".join([cdate[0].strftime("%d/%m/%Y"), cdate[1].strftime("%d/%m/%Y")]) for cdate in intervals]


        ## Plot
        nb_stations = len(stationKey)
        type_of_model = [self.myCatchments[el]["Title"] for el in self.myCatchments]
        type_of_data = ["Nash", r"$  \frac{Q^{s}_{max}-Q^{m}_{max}}{Q^{m}_{max}} $ "]
        type_of_data_names = ["Nash", "Exceedance"]

        # ph.bar_Nash_n_other(all_data, all_colors, nb_x=len(intervals), nb_data=len(type_of_model), nb_lines=nb_stations,
        #                     y_titles=type_of_data, x_titles=all_names, nameModel=type_of_model, line_names=sorted_keys, toShow=False)

        # =========
        # =========
        # Plot tables - 2nd version with the table instead of bars
        all_ns= {
            cur_catch["Title"]: np.array([list(cur_catch["Object"].get_sub_Nash(measures[i], stationKey[i], intervals)) for i in range(len(stationKey))])
            for cur_catch in self.myCatchments.values()
        }

        all_peaks = {cur_catch["Title"]: np.array([cur_catch["Object"].get_sub_peak(stationKey[i], intervals) for i in range(len(stationKey))])
                     for cur_catch in self.myCatchments.values()
        }

        print(all_peaks)

        meas_peak = np.array([ measures[i].get_peak(intervals)
                     for i in range(len(stationKey)) ])

        # The following lines is take the peak difference between simulation and measurements -> Display 0.0 if the measurement is 0.0
        isZero = (meas_peak==0)
        notZero = (meas_peak!=0)
        peak_prop = {
            cur_model: (value-meas_peak)/(meas_peak+isZero) *notZero
            for cur_model, value in all_peaks.items()
        }

        # Concatenate all data
        all_data = [all_ns, peak_prop]

        for data, name_of_data in zip(all_data, type_of_data_names):
            for cur_model, cur_data in data.items():
                file_name = os.path.join(self.workingDir, name_of_data+"_"+cur_model)+".png"
                # cur_title = cur_model + ": " + name_of_data
                ph.table_Nash_n_other(cur_data, name_of_data,
                                    row_names=sorted_keys, column_names=all_names,
                                    writeFile=file_name, toShow=False)
        if toShow:
            plt.show()