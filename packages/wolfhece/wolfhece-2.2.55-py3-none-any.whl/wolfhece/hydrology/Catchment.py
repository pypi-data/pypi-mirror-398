"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy  as np
import csv
import time as time_mod
import sys                              # module to stop the program when an error is encountered
import json                             # mudule to use json file
import pandas as pd                     # module to write data in Excel file
import datetime                         # module which contains objects treating dates
import matplotlib.pyplot as plt
from dbfread import DBF                 # module to treat DBF files

#  libraries to import for graphiz (Here to draw flowcharts)
import graphviz
import os
import copy                             # module to copy objects

from ..PyTranslate import _

if os.path.isdir('C:/Program Files (x86)/Graphviz/bin'):
    os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz/bin'    # Without this line the path to graphiz app might not be found
elif os.path.isdir('C:/Program Files/Graphviz/bin'):
    os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'    # Without this line the path to graphiz app might not be found
else:
    print(_('Note: do not forget to install the graphviz app and add it to the PATH to make it work'))
# --------------------------------

# from ..wolf_texture import genericImagetexture
# from ..PyDraw import WolfMapViewer
from .SubBasin import *
from .RetentionBasin import *
from .read import *
from ..wolf_array import *
from ..PyParams import *
from ..PyVertex import cloud_vertices, getIfromRGB,wolfvertex
from .PyWatershed import Watershed, Node_Watershed


# %% Classes

class Catchment:
    """This object contains all the information about the Catchment.

        The Catchment is composed of element that can be:
            - Subbasin
            - RetentionBasin

        In the Catchment the following rules are applied:
            - there is one and only one outlet.
            - one element

    """

    time_delays_F:np.ndarray                                                # array pointed to the array time_delays in Fortran and composed the time delays of each subbasin
    _version:float                                                          # version of the wolfHydro python code. Useful for identifying the file versions to read and how to interpret them
    charact_watrshd:Watershed                                               # Watershed object containing the most useful properties of the arrays in Characteristics maps
    subBasinCloud:cloud_vertices                                            # cloud of points containing the true coordinates (used in simulation) of all subbasin outlets
    retentionBasinCloud:cloud_vertices                                      # cloud of points containing the true coordinates (used in simulation) of all retention basins
    iP_Cloud:cloud_vertices                                                 # cloud of points containing the given coordinates (given in param files) of all subbasin outlets

    catchmentDict:dict[Union[str, int], Union[SubBasin, RetentionBasin]]    # dictionnary containing all the elements of the catchment
    subBasinDict:dict[int, SubBasin]                                        # dictionnary containing all the subbasins with the convention dict{ID Interior Point : SubBasin object}
    retentionBasinDict:dict[str, RetentionBasin]                            # dictionnary containing all the anthropogenic modules

    def __init__(self, _name, _workingDir, _plotAllSub, _plotNothing, _initWithResults=True, _catchmentFileName="", _rbFileName="", _tz=0, version=cst.VERSION_WOLFHYDRO):
        "This is the constructor of the class Catchment in which all the caractertics and the network of sub-basins will be created"
        # Init of all the propperties' object
        self.name = _name
        self.workingDir = _workingDir
        self.plotAllSub = _plotAllSub
        self.plotNothing = _plotNothing
        if(self.plotNothing == True):
            self.plotAllSub = False
        self.tz = _tz                                                       # time zone in GMT+0
        self.time = None                                                    #
        self.deltaT = 0.0                                                   # Time step of the simulation
        self.dateBegin = None                                               # Object datetime of the beginning date of the simulation
        self.dateEnd = None                                                 # Object datetime of the end date of the simulation
        self.myModel = None
        self.nbCommune = 0
        self.nbSubBasin = 0
        self.hyeto = {}                                                     # Pluie pour chaque "commune"
        self.catchmentDict = {}
        self.subBasinDict = {}

        self.subBasinCloud=cloud_vertices()
        self.subBasinCloud.myprop.color=getIfromRGB((255,131,250))
        self.subBasinCloud.myprop.filled=True

        self.retentionBasinCloud=cloud_vertices()
        self.retentionBasinCloud.myprop.color=getIfromRGB((0,131,255))
        self.retentionBasinCloud.myprop.filled=True

        self.iP_Cloud=cloud_vertices()
        self.iP_Cloud.myprop.color=getIfromRGB((255,131,250))
        self.iP_Cloud.myprop.filled=True

        self.retentionBasinDict = {}
        self.topologyDict = {}
        self.dictIdConversion = {}
        self.hyetoDict = {}
        self.intersection = {}
        self.catchmentDict['Elements'] = {}
        self.catchmentDict['Subbasin'] = self.subBasinDict
        self.catchmentDict['RB'] = self.retentionBasinDict
        self.catchmentDict['Topo'] = self.topologyDict
        self.catchmentDict['Hyeto'] = self.hyeto
        self.catchmentDict['dictIdConversion'] = self.dictIdConversion
        self.junctionNamesDict = {}                                         # Dictionnary containing all the names associated with their junction
        self.myStationsDict = {}
        self.myEffSortSubBasins = []                                        # List of effective Subbasins indicated by their sorted number from Fortran (int)
        self.myEffSubBasins = []                                            # List of effective Subbasins indicated by their Interior Point number (int)
        # self.topologyFrame = wx.Frame(None)
        self.junctionOut = ""
        self.levelOut = -1

        self.time_delays_F = None
        self.ptr_time_delays = None

        self._version = version


        if(_initWithResults==False):
            return

        # Creation of the PostProcess directory
        # It will contain all the the saved results.
        writingDir = os.path.join(self.workingDir,'PostProcess')
        if not os.path.exists(writingDir):
            try:
                os.mkdir(writingDir)
            except OSError:
                print ("Creation of the directory %s failed" % writingDir)
            else:
                print ("Successfully created the directory %s" % writingDir)

        # Read the input files
        # read the Main File
        self.paramsInput = Wolf_Param(to_read=False, toShow=False)
        self.paramsInput.ReadFile(os.path.join(self.workingDir,'Main_model.param'))
        # Get the version of WOLFHydro
        self.change_version(self.paramsInput.get_param("General information", "Version WOLFHydo"))
        # self.paramsInput.Hide()

        # read the topology file
        self.paramsTopology = Wolf_Param(to_read=False,toShow=False)
        if(self.paramsInput is self.paramsTopology):
            print("Error: the same Wof_Param object was created")
            sys.exit()

        if(_catchmentFileName==""):
            catchmentFileName = 'Catchment.postPro'
        else:
            catchmentFileName = _catchmentFileName
        if os.path.exists(os.path.join(self.workingDir,catchmentFileName)):
            self.paramsTopology.ReadFile(os.path.join(self.workingDir,catchmentFileName))
        else:
            logging.error("The following topology file is not present !")
            logging.error("File name : "+ os.path.join(self.workingDir,catchmentFileName))
        # self.paramsTopology.Hide()

        if(self.paramsInput.myparams is self.paramsTopology.myparams):
            print("Error: the same dictionnary was created for the params in the input files")
            sys.exit()
        # Read data and characteristics of the RB and its outlet
        self.paramsRB = Wolf_Param(to_read=False,toShow=False)
        if(self.paramsRB is self.paramsTopology):
            print("Error: the same Wof_Param object was created")
            sys.exit()

        if(_rbFileName==""):
            rbFileName = 'RetentionBasins.postPro'
        else:
            rbFileName = _rbFileName
        rbFileName = os.path.join(self.workingDir,rbFileName)
        if os.path.exists(rbFileName):
            self.paramsRB.ReadFile(os.path.join(self.workingDir,rbFileName))
        else:
            logging.error("The following RB file is not present !")
            logging.error("File name : "+ rbFileName)
        # self.paramsRB.Hide()

        if(self.paramsRB.myparams is self.paramsTopology.myparams):
            print("Error: the same dictionnary was created for the params in the input files")
            sys.exit()

        # Get the number of subbasins
        self.nbSubBasin = int(self.paramsInput[('Semi distributed model', 'How many?')]) + 1 # +1 because the outlet is also counted

        # Fill the dictionary containing the id of the sorted subbasin returned by the Fortran code
        self.init_dictIdConversion(self.workingDir)

        # Fill the dictionary containing the id of the hyeto to read when the ordred hyeto is given
        self.init_hyetoDict()

        # Get the information on the characteristic maps computed by the Fortran code
        # self.topo_wolf_array = WolfArray(self.workingDir + "Characteristic_maps/Drainage_basin.b")
        # self.topo_wolf_array = WolfArray(self.workingDir + "Characteristic_maps/Drainage_basin.b2")
        self.time_wolf_array = WolfArray(os.path.join(self.workingDir,"Characteristic_maps/Drainage_basin.time"))
        self.charact_watrshd = Watershed(self.workingDir, dir_mnt_subpixels=self.paramsInput[('Sub-pixeling', 'Directory')])
        self.set_eff_outlet_coord()

        # time array:
        self.get_time()
        # self.time, self.rain = self.get_rain(self.workingDir+'Subbasin_1/')
        # TO DO: Check how the rain is read for the first time

        # Get the hydrology model used (1-linear reservoir, 2-VHM, 3-Unit Hydrograph)
        self.myModel = self.paramsInput[('Model Type', 'Type of hydrological model')]

        # Save the stations SPW characteristics in a dictionnary
        self.read_measuring_stations_SPW()




        try:

            # Construction of the Catchment
            # ------------------------------

            # 1) 1st Iteration: Object creation

            # Iterate through the Input params dictionnary
            self.create_ObjectsInCatchment()

            self.charact_watrshd.set_names_subbasins([(cur.iDSorted, cur.name) for cur in self.subBasinDict.values()])

            # self.add_hyetoToDict()


            # 2) 2nd Iteration: Link between objects
            self.link_objects()   # This procedure also creates the first layer of the topo tree by identifying the source ss-basins

            """
            The topo tree is organised by level:
            - The first level contains should only contain subbasins which don't have any input flows.
            Therefore, they already contains all the information to build their hydrograph
            - The second and upper levels can contain either RB or subbasins with input flows.

            """

            # 3) 3rd Iteration: Complete the tree
            self.complete_topoDict()
            if(not(self.plotNothing)):
                flowchart = graphviz.Digraph("Test")
                flowchart.format = 'png'
                self.draw_flowChart(flowchart)
                # flowchart.view()
                flowchart.save(directory=self.workingDir)
                flowchart.render(os.path.join(self.workingDir,"Topology"), view=False)
                #  Hello! To DO !!! the following lines problem
                # topologyImage = Image.open(BytesIO(flowchart.pipe(format="png")))
                # # topologyImage = Image.open(os.path.join(self.working
                # # Dir,"Test.png"))

                # # self.topoMapViewer = WolfMapViewer(None, "Topology", treewidth=0)
                # ratio = topologyImage.width/topologyImage.height
                # # self.topoMapViewer = WolfMapViewer(None, "Topology",w=topologyImage.width,h=topologyImage.height,treewidth=0)
                # self.topoMapViewer = WolfMapViewer(None, "Topology",w=4000*ratio,treewidth=0)
                # self.topoMapViewer.add_object('Other', newobj=genericImagetexture('Other','Topology',self.topoMapViewer,xmin=0, xmax=topologyImage.width,
                #                     ymin=0, ymax=topologyImage.height, width=topologyImage.width, height=topologyImage.height,imageObj=topologyImage),
                #                     ToCheck=False, id='Topology')
                # self.topoMapViewer.Autoscale()
                # self.topoMapViewer.OnPaint(None)
                # self.topoMapViewer.Show()
                pass

                # isNotCorrect = True
                # while(isNotCorrect):
                #     print("Is this Flowchart ok?")
                #     print("Y-Yes, N-No")
                #     answer = input("Your answer:")
                #     if(answer=="N" or answer=="No"):
                #         print("The postprocess was stopped by the user!")
                #         sys.exit()
                #     elif(answer=="Y" or answer=="Yes"):
                #         isNotCorrect = False
                #     else:
                #         print("ERROR: Please enter the correct answer!")

                # r = wx.MessageDialog(None, "Is this Flowchart ok?", "Topology verification", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()

                # if r != wx.ID_YES:
                #     print("The postprocess was stopped by the user!")
                #     sys.exit()

            # Definition of junctionOut by default the last junction/element in the topology tree
            self.junctionOut = self.get_lastJunctionKey()

            # Associate objects linked to timeDelay in all RB objects
            tmp = self.find_all_timeDelayObj()

            # ===============================
            # Computation of the hydrographs
            self.construct_hydro()

            # Reading of the rain for each subbasin
            try:
                self.add_rainToAllObjects()
            except:
                print("ERROR! The rain couldn't be created. This might be induced by the lack of the dbf file!")
                pass

            # Contruct the effective subbasins
            self.get_eff_subBasin()

            # Construct the surface drained by anthropogenic modules
            self.construct_surfaceDrainedHydro_RB()

            # Read the landuses of all subbasins
            self.read_all_landuses()

            # ==============================
            # Save in excel file all the hydrographs

            # Hello! To uncomment!!!!
            # self.save_ExcelFile()
            # self.save_ExcelFile_noLagTime()
            # self.save_ExcelFile_V2()
            # self.save_characteristics()

            # Plot the of the subbasin or RB with level above 1 in the topo tree
            self.plotNothing = True
            if(not(self.plotNothing)):
                self.plot_intersection()
            # Plot all the subbasin hydrographs and hyetograph
            if(self.plotAllSub):
                self.plot_allSub()

            # self.charact_watrshd.impose_sorted_index_subbasins([cur.iDSorted for cur in self.subBasinDict.values()])

            self._fill_cloud_retentionbasin()

        except:
            logging.error(_("An error occured during the creation of the Catchment object."))
            logging.info(_("If you are in a preprocessing step, it could be a normal issue."))
            return

    def get_subBasin(self, id_sorted_or_name:int | str) -> SubBasin:
        """
        This method returns the subbasin object associated with the sorted id or name given in argument.

        The sorted id is the one given by the Fortran code.
        """

        if isinstance(id_sorted_or_name, str):
            for cursub in self.subBasinDict.values():
                if(cursub.name.lower() == id_sorted_or_name.lower()):
                    return cursub

        elif isinstance(id_sorted_or_name, int):
            for cursub in self.subBasinDict.values():
                if(cursub.iDSorted == id_sorted_or_name):
                    return cursub
        return None


    def get_time(self):
        """ This method saves the time characteristics read in the .param file and build a time array.
            The convention used for the time written in the .param is as follow: YYYYMMDD-HHMMSS
            It is important to notice that the dateBegin and dateEnd are converted in GMT+0

            Internal variables modified : self.deltaT, self.dateBegin, self.dateEnd, self.time.

            NB : If any change in the convention is mentionned in the comment following the dates the code will return an error
                Otherwise, no procedure will warn the user that a converntion is modified.
        """
        commentRead1 = self.paramsInput.myparams_default['Temporal Parameters']['Start date time'][key_Param.COMMENT]
        commentRead2 = self.paramsInput.myparams_default['Temporal Parameters']['End date time'][key_Param.COMMENT]
        if (commentRead1.replace(' ', '') != 'Startdate[YYYYMMDD-HHMMSS]'):
            print("ERROR: The convention in the start date is different from the one treated in this code. Please change it or modify the function get_time().")
            sys.exit()
        if (commentRead2.replace(' ', '') != 'Enddate[YYYYMMDD-HHMMSS]'):
            print("ERROR:The convention in the end date is different from the one treated in this code. Please change it or modify the function get_time().")
            sys.out()
        try:
            dateRead1 = self.paramsInput.myparams['Temporal Parameters']['Start date time'][key_Param.VALUE]
        except:
            dateRead1 = self.paramsInput.myparams_default['Temporal Parameters']['Start date time'][key_Param.VALUE]

        try:
            dateRead2 = self.paramsInput.myparams['Temporal Parameters']['End date time'][key_Param.VALUE]
        except:
            dateRead2 = self.paramsInput.myparams_default['Temporal Parameters']['End date time'][key_Param.VALUE]
        tzDelta = datetime.timedelta(hours=self.tz)
        self.deltaT = float(self.paramsInput.myparams['Temporal Parameters']['Time step'][key_Param.VALUE])
        self.dateBegin = datetime.datetime(year=int(dateRead1[0:4]), month=int(dateRead1[4:6]), day=int(dateRead1[6:8]), hour=int(dateRead1[9:11]), minute=int(dateRead1[11:13]), second=int(dateRead1[13:15]),  microsecond=0, tzinfo=datetime.timezone.utc)
        self.dateBegin -= tzDelta
        self.dateEnd = datetime.datetime(year=int(dateRead2[0:4]), month=int(dateRead2[4:6]), day=int(dateRead2[6:8]), hour=int(dateRead2[9:11]), minute=int(dateRead2[11:13]), second=int(dateRead2[13:15]),  microsecond=0, tzinfo=datetime.timezone.utc)
        self.dateEnd -= tzDelta
        diffDate = self.dateEnd - self.dateBegin
        # secondsInDay = 24*60*60
        # diffTimeInSeconds = diffDate.days*secondsInDay + diffDate.seconds
        ti = datetime.datetime.timestamp(self.dateBegin)
        tf = datetime.datetime.timestamp(self.dateEnd)
        # self.time = np.arange(0,diffTimeInSeconds+1,self.deltaT)
        self.time = np.arange(ti,tf+self.deltaT,self.deltaT)



    def get_rain(self, workingDir):
        fileName = 'simul_lumped_rain.txt'
        with open(os.path.join(workingDir,fileName), newline = '') as fileID2:
            data_reader = csv.reader(fileID2, delimiter='\t')
            list_data = []
            i=0
            for raw in data_reader:
                if i>1:
                    list_data.append(raw)
                i += 1
        matrixData = np.array(list_data).astype("float")
        rain = np.zeros(len(matrixData))
        time = np.zeros(len(matrixData))
        for i in range(len(matrixData)):
            time[i] = matrixData[i][4]*60 + matrixData[i][3]*60**2 + (matrixData[i][0]-matrixData[0][0])*(60**2)*24 + (matrixData[i][1]-matrixData[0][1])*(60**2)*24*31
            rain[i] = matrixData[i][6]

        return time, rain



    def get_hyeto(self, fileName):
        f = open(fileName, "r")
        stringTab = []
        for line in f:
            stringTab.append(line.lstrip())

        matrixData = np.zeros((len(stringTab)-1,2))
        for i in range(len(stringTab)):
            if(i>0):
                tmpTxt = stringTab[i].split(" ", 1)
                tmpTxt[1] = tmpTxt[1].strip()
                tmpTxt[1] = tmpTxt[1].replace("\n", "")
                matrixData[i-1][0] = float(tmpTxt[0])
                matrixData[i-1][1] = float(tmpTxt[1])

        rain = np.zeros(len(matrixData))
        time = np.zeros(len(matrixData))
        time0 = matrixData[0][0]
        for i in range(len(matrixData)):
            time[i] = matrixData[i][0]-time0
            rain[i] = matrixData[i][1]
        return time, rain



    def init_dictIdConversion(self, workingDir):
        """ Procedure that converts the Id of the intersection points in the input file into the sorted sub-basin ids
            file read: simul_sorted_interior_points.txt
            Internal variables modified: self.dictIdConversion

            The conversion dictionnary has the given form:
            self.dictIdConversion[Internal Point id] = sorted subbasin from the lowest to the highest
        """
        fileNameInteriorPoints = os.path.join(workingDir,'simul_sorted_interior_points.txt')

        if not os.path.exists(fileNameInteriorPoints):
            logging.error("The file simul_sorted_interior_points.txt is not present in the working directory!")
            return

        # !!! Add the case the file is not present.
        with open(fileNameInteriorPoints) as fileID:
            data_reader = csv.reader(fileID, delimiter='\t')
            list_data = []
            i=0
            for raw in data_reader:
                if i>0:
                    list_data.append([int(raw[i].replace(' ','')) for i in range(0,len(raw))])
                i += 1

        nbData = len(list_data)
        if(self.nbSubBasin != nbData):
            if(self.nbSubBasin == 0):
                print("WARNING : The number of subbasins not encoded yet")
            else:
                print("ERROR : The number subbasin is not consistent with the number of lines in the file: simul_sorted_interior_points.txt")
                sys.exit()

        for num in range(1, nbData+1):
            for index in range(nbData):
                if (list_data[index][0]==num):
                    self.dictIdConversion[num] = list_data[index][1]
                    break
                if(index == nbData-1):
                    print("Not normal:" , num)



    def create_ObjectsInCatchment(self):
        """ Procedure which creates the objects in the dictionnaries of the subbasins and the RB and
            each object are pointed in the global catchment dictionnary.
            This procedre also create the 1st level of the Topo dictionnary.
            Internal variables modified: subBasinDict, retentionBasinDict, self.catchmentDict,
        """
        # Creates Subbasins
        counter = 0
        for counter in range(1, self.nbSubBasin):
            tmpNameParam = 'Interior point '+ str(counter)
            if('X' in self.paramsInput.myparams[tmpNameParam] and 'Y' in self.paramsInput.myparams[tmpNameParam]):
                x = float(self.paramsInput.myparams[tmpNameParam]['X'][key_Param.VALUE])
                y = float(self.paramsInput.myparams[tmpNameParam]['Y'][key_Param.VALUE])
            elif("Station Code" in self.paramsInput.myparams[tmpNameParam]):
                stationCode = self.paramsInput.myparams[tmpNameParam]["Station Code"][key_Param.VALUE]
                x = self.myStationsDict[int(stationCode)]["X"]
                y = self.myStationsDict[int(stationCode)]["Y"]
            elif("Station Name" in self.paramsInput.myparams[tmpNameParam]):
                stationName = self.paramsInput.myparams[tmpNameParam]["Station Name"][key_Param.VALUE]
                x = self.myStationsDict[stationName]["X"]
                y = self.myStationsDict[stationName]["Y"]
            else:
                print("ERROR: Impossible to indentify the position of the interior points! Please check your param file!")
                sys.exit()

            mysubxy=wolfvertex(x,y)
            self.iP_Cloud.add_vertex(mysubxy)

            idSorted = self.catchmentDict['dictIdConversion'][counter]
            cur_outlet:wolfvertex = self.subBasinCloud.myvertices[idSorted-1]["vertex"]
            # self.subBasinDict[counter] = SubBasin(counter, self.time, self.workingDir, self.hyeto, x, y, idSorted)
            self.subBasinDict[counter] = SubBasin(self.dateBegin, self.dateEnd, self.deltaT, self.myModel, self.workingDir,
                                         _iD_interiorPoint=counter, _idSorted=idSorted, _hyeto=self.hyeto, _x=cur_outlet.x, _y=cur_outlet.y, _tz=self.tz, version=self._version)
            self.catchmentDict['ss'+str(counter)] = self.subBasinDict[counter]

            mysubxy=wolfvertex(x,y)
            self.iP_Cloud.add_vertex(mysubxy)

        counter += 1
        tmpNameParam = 'Outlet Coordinates'
        if('X' in self.paramsInput.myparams[tmpNameParam] and 'Y' in self.paramsInput.myparams[tmpNameParam]):
            x = float(self.paramsInput.myparams[tmpNameParam]['X'][key_Param.VALUE])
            y = float(self.paramsInput.myparams[tmpNameParam]['Y'][key_Param.VALUE])
        elif("Station Code" in self.paramsInput.myparams[tmpNameParam]):
            stationCode = self.paramsInput.myparams[tmpNameParam]["Station Code"][key_Param.VALUE]
            x = self.myStationsDict[int(stationCode)]["X"]
            y = self.myStationsDict[int(stationCode)]["Y"]
        elif("Station Name" in self.paramsInput.myparams[tmpNameParam]):
            stationName = self.paramsInput.myparams[tmpNameParam]["Station Name"][key_Param.VALUE]
            x = self.myStationsDict[stationName]["X"]
            y = self.myStationsDict[stationName]["Y"]
        else:
            print("ERROR: Impossible to indentify the position of the interior points! Please check your param file!")
            sys.exit()
        # x = float(self.paramsInput.myparams[tmpNameParam]['X'][key_Param.VALUE])
        # y = float(self.paramsInput.myparams[tmpNameParam]['Y'][key_Param.VALUE])
        idSorted = self.catchmentDict['dictIdConversion'][counter]
        cur_outlet:wolfvertex = self.subBasinCloud.myvertices[idSorted-1]["vertex"]
        # self.subBasinDict[counter] = SubBasin(counter, self.time, self.workingDir, self.hyeto, x, y, idSorted)
        self.subBasinDict[counter] = SubBasin(self.dateBegin, self.dateEnd, self.deltaT, self.myModel, self.workingDir,
                                     _iD_interiorPoint=counter, _idSorted=idSorted, _hyeto=self.hyeto, _x=x, _y=y, _tz=self.tz, version=self._version)

        mysubxy=wolfvertex(x,y)
        self.iP_Cloud.add_vertex(mysubxy)

        self.catchmentDict['ss'+str(counter)] = self.subBasinDict[counter]
        # This following line must be present to create the outFlow dictionary of the last element
        self.subBasinDict[counter].add_downstreamObj(None, name="FINAL OUTLET")


        # Creates RB and checking if the topo file contains only these types of junction
        for element in self.paramsTopology.myparams:
            # If Subbasin:
            if(self.paramsTopology.myparams[element]['type'][key_Param.VALUE] == 'Subbasin'):
                idBasin = int(self.paramsTopology.myparams[element]['number'][key_Param.VALUE].replace('ss', ''))
                nameBasin = self.paramsTopology.myparams[element]['name'][key_Param.VALUE]
                inletsString = self.paramsTopology.myparams[element]['inlets'][key_Param.VALUE].strip()
                # Save the name of the basin
                self.subBasinDict[idBasin].add_name(nameBasin)
                # Check if the subbasin have inlets or not => if not can be on the first layer of the topology tree.
                if(inletsString!='--'):
                    self.subBasinDict[idBasin].change_haveInlets()
                # Save the element of the subbasin dictionnary also in the global Cachment dictionnary with 'J' prefix.
                self.catchmentDict[element] = self.subBasinDict[idBasin]
                # Save the element of the subbasin dictionnary also in the global Cachment dictionnary with 'ss' prefix
                # -> First free the object aleady created with the 'ss' prefix
                # Therefore a subbasin with several inputs can be called in the Catchment dictionnary with prefix 'J' or 'ss' or the name of the station
                self.catchmentDict[self.paramsTopology.myparams[element]['number'][key_Param.VALUE]] = None
                self.catchmentDict[self.paramsTopology.myparams[element]['number'][key_Param.VALUE]] = self.subBasinDict[idBasin]
                self.junctionNamesDict[self.paramsTopology.myparams[element]['name'][key_Param.VALUE]] = element
            # If RB:
            elif(self.paramsTopology.myparams[element]['type'][key_Param.VALUE] == 'RB'):
                idBasin = element
                # Save the name of the RB
                nameBasin = self.paramsTopology.myparams[element]['name'][key_Param.VALUE]
                # Create the RB object
                typeOfRB = self.paramsTopology.myparams[element]['type of RB'][key_Param.VALUE]
                # Outlet names if present
                myOutletsNames = []
                self.junctionNamesDict[self.paramsTopology.myparams[element]['name'][key_Param.VALUE]] = element
                try:
                    nbOutlets = int(self.paramsTopology.myparams[element]['nb outlets'][key_Param.VALUE])
                except:
                    nbOutlets = 0
                    myOutletsNames.append(element)

                for iOutlet in range(nbOutlets):
                    myOutletsNames.append(self.paramsTopology.myparams[element]["outlet "+str(iOutlet+1)][key_Param.VALUE])
                    self.junctionNamesDict[self.paramsTopology.myparams[element]["outlet "+str(iOutlet+1)][key_Param.VALUE]] = element

                self.retentionBasinDict[element] = RetentionBasin(self.dateBegin, self.dateEnd, self.deltaT, self.time, idBasin, nameBasin, typeOfRB, self.paramsRB.myparams, _tz=self.tz, _outletNames=myOutletsNames, _workingDir=self.workingDir)

                # Save the RB in the RB dictionnary into the global Catchment dictionnary
                self.catchmentDict[element] = self.retentionBasinDict[element]

            # If none of the junction above
            else:
                print("ERROR: This type of junction is unknown. Please check the topo postprocess file")
                sys.exit()

    def _fill_cloud_retentionbasin(self):
        """ This procedure fills the cloud of the retention basin with the vertices of the retention basin and its inlets. """

        for curRT in self.retentionBasinDict.values():
            curRT:RetentionBasin
            self.retentionBasinCloud.add_vertex(wolfvertex(curRT.x,curRT.y))
            inlet_coords = curRT.get_inletCoords()
            for cur_inlet in inlet_coords:
                self.retentionBasinCloud.add_vertex(wolfvertex(cur_inlet[0],cur_inlet[1]))

    def get_retentionbasin_zones(self)-> Zones:
        """ This method returns a Zones instance of the retention basins. """

        zones = Zones()
        for curRB in self.retentionBasinDict.values():
            curRB:RetentionBasin
            zones.add_zone(curRB.get_zone(), forceparent=True)

        return zones


    def link_objects(self):
        """ This procedure link all the subbasins and the retention basin altogether to form a network.
            If a subbasin without inlet whatsoever is detected, one adds it to the first level of the Topology tree.

            Internal variables modified: subBasinDict, retentionBasinDict, topologyDict

        """
        print("Procedure of objects linking ongoing")
        nbSub = 0
        nbInter = 0
        self.topologyDict['Level 1'] = {}

        if len(self.paramsTopology.myparams)==0 or len(self.subBasinDict)==1:
            self.topologyDict['Level 1']['ss1'] = self.subBasinDict[1]
            return


        for element in self.paramsTopology.myparams:
            if(self.paramsTopology.myparams[element]['type'][key_Param.VALUE] == 'RB'):
                # Case 1) inlets
                if('inlets' in self.paramsTopology.myparams[element]):
                    # Split the string at each ',' in several smaller strings
                    tmpString = self.paramsTopology.myparams[element]['inlets'][key_Param.VALUE].split(',')
                    # Loop on the strings representing the inlets
                    for i in range(len(tmpString)):
                        # Remove leading and trailing white spaces
                        tmpString[i]= tmpString[i].strip()
                        # If the inlet is a subbasin
                        if tmpString[i][0:2] == 'ss' :
                            # This variable will count the number of subbasins to check if all of them are used.
                            nbSub += 1
                            # In the subbasin dict, only the number is kept as identifier.
                            iDSub =  int(tmpString[i].replace('ss', ''))
                            # Check if the subbasin were already used or not. It cannot be used more than once.
                            if(self.subBasinDict[iDSub].alreadyUsed):
                                print("ERROR: a subbasin has already been used. Please check the topology file!")
                                sys.exit()
                            # The RB is saved as a downstream object of the inlet
                            self.subBasinDict[iDSub].add_downstreamObj(self.retentionBasinDict[element], name=tmpString[i])
                            # The inlet is linked as an inlet of the RB
                            self.retentionBasinDict[element].add_inlet(self.subBasinDict[iDSub], name=tmpString[i])
                            # If the inlet is a subbasin which has no inlets, it is added to the 1st level of the topo tree.
                            # This procedure can be carried out as haveInlets have already been determined for all subbasin
                            # in the creation of the objects.
                            if(not(self.subBasinDict[iDSub].haveInlets)):
                                self.subBasinDict[iDSub].isLeveled = True
                                self.topologyDict['Level 1'][tmpString[i]] = self.subBasinDict[iDSub]
                            # Else the level of the subbasin in the topo tree is incremented (set to 2 if the tree is correct).
                            else:
                                self.subBasinDict[iDSub].increment_level()
                        # 'J' can be a RB or a subbasin
                        elif(tmpString[i][0] == 'J' and (tmpString[i] in self.paramsTopology.myparams)):
                            # This variable count the number of iteration to see if all are used.
                            nbInter += 1
                            # if the inlet is a subbasin:
                            if(self.paramsTopology.myparams[tmpString[i]]['type'][key_Param.VALUE] == 'Subbasin'):
                                nbSub += 1
                                iDSub = int(self.paramsTopology.myparams[tmpString[i]]['number'][key_Param.VALUE].replace('ss', ''))
                                # A same subbasin cannot be used twice
                                if(self.subBasinDict[iDSub].alreadyUsed):
                                    print("ERROR: a subbasin has already been used. Please check the topology file!")
                                    sys.exit()
                                # Add the RB as the dowstream object of the inlet
                                self.subBasinDict[iDSub].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i])
                                # Add inlet
                                self.retentionBasinDict[element].add_inlet(self.subBasinDict[iDSub],name=tmpString[i])
                                if(not(self.subBasinDict[iDSub].haveInlets)):
                                    self.subBasinDict[iDSub].isLeveled = True
                                    self.topologyDict['Level 1'][tmpString[i]] = self.subBasinDict[iDSub]
                                else:
                                    self.subBasinDict[iDSub].increment_level()
                            # if the inlet is a RB:
                            elif(self.paramsTopology.myparams[tmpString[i]]['type'][key_Param.VALUE] == 'RB'):
                                # A RB can be used used twice
                                if(self.retentionBasinDict[tmpString[i]].alreadyUsed):
                                    # print("ERROR: this RB was already used! Please check the topo file.")
                                    print("This RB has at least 2 outlets.")
                                    # sys.exit()
                                self.retentionBasinDict[tmpString[i]].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i])
                                self.retentionBasinDict[element].add_inlet(self.retentionBasinDict[tmpString[i]],name=tmpString[i])
                            else:
                                print("This type of intersection is not recognised. Please check your topo file.")
                                sys.exit()
                        elif(tmpString[i] in self.junctionNamesDict):
                            junctionName = self.junctionNamesDict[tmpString[i]]

                            # This variable count the number of iteration to see if all are used.
                            nbInter += 1
                            # if the inlet is a subbasin:
                            if(self.paramsTopology.myparams[junctionName]['type'][key_Param.VALUE] == 'Subbasin'):
                                nbSub += 1
                                iDSub = int(self.paramsTopology.myparams[junctionName]['number'][key_Param.VALUE].replace('ss', ''))
                                # A same subbasin cannot be used twice
                                if(self.subBasinDict[iDSub].alreadyUsed):
                                    print("ERROR: a subbasin has already been used. Please check the topology file!")
                                    sys.exit()
                                # Add the RB as the dowstream object of the inlet
                                self.subBasinDict[iDSub].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i])
                                # Add inlet
                                self.retentionBasinDict[element].add_inlet(self.subBasinDict[iDSub],name=tmpString[i])
                                if(not(self.subBasinDict[iDSub].haveInlets)):
                                    self.subBasinDict[iDSub].isLeveled = True
                                    self.topologyDict['Level 1'][tmpString[i]] = self.subBasinDict[iDSub]
                                else:
                                    self.subBasinDict[iDSub].increment_level()
                            # if the inlet is a RB:
                            elif(self.paramsTopology.myparams[junctionName]['type'][key_Param.VALUE] == 'RB'):
                                # Check delta time applied to all exits
                                tmpNbOutlets = 1
                                deltaTime = 0.0
                                if('nb outlets' in self.paramsTopology.myparams[junctionName]):
                                    tmpNbOutlets = int(self.paramsTopology.myparams[junctionName]['nb outlets'][key_Param.VALUE])
                                    if(tmpNbOutlets>1):
                                        for iOutlets in range(tmpNbOutlets):
                                            if(self.paramsTopology.myparams[junctionName]['outlet '+str(iOutlets+1)][key_Param.VALUE]==tmpString[i]):
                                                try:
                                                    deltaTime = float(self.paramsTopology.myparams[junctionName]['delta time '+str(iOutlets+1)][key_Param.VALUE])
                                                except:
                                                    deltaTime = 0.0

                                    elif('delta time 1' in self.paramsTopology.myparams[junctionName]):
                                        deltaTime = float(self.paramsTopology.myparams[junctionName]['delta time 1'][key_Param.VALUE])

                                # A RB can be used used twice
                                if(self.retentionBasinDict[junctionName].alreadyUsed):
                                    # print("ERROR: this RB was already used! Please check the topo file.")
                                    print("This RB has at least 2 outlets.")
                                    # sys.exit()
                                self.retentionBasinDict[junctionName].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i],deltaTime=deltaTime)
                                self.retentionBasinDict[element].add_inlet(self.retentionBasinDict[junctionName],name=tmpString[i])
                            else:
                                print("This type of intersection is not recognised. Please check your topo file.")
                                sys.exit()
                        else:
                            print("This type of inlet is not recognised. Please check your topo file.")
                            sys.exit()
                # Case 2 : same procedure but for the flux entering the directly in RB
                if('direct inside RB' in self.paramsTopology.myparams[element]):
                    tmpString = self.paramsTopology.myparams[element]['direct inside RB'][key_Param.VALUE].split(',')
                    for i in range(len(tmpString)):
                        tmpString[i]= tmpString[i].strip()
                        # Save the dowstream link of each element in the dictionnary
                        if tmpString[i][0:2] == 'ss' :
                            nbSub += 1
                            iDSub =  int(tmpString[i].replace('ss', ''))
                            if(self.subBasinDict[iDSub].alreadyUsed):
                                # print("ERROR: a subbasin has already been used. Please check the topology file!")
                                print("This RB has at least 2 exits")
                                # sys.exit()

                            self.subBasinDict[iDSub].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i])
                            self.retentionBasinDict[element].add_directFluxObj(self.subBasinDict[iDSub],name=tmpString[i])
                            if(not(self.subBasinDict[iDSub].haveInlets)):
                                self.subBasinDict[iDSub].isLeveled = True
                                self.topologyDict['Level 1'][tmpString[i]] = self.subBasinDict[iDSub]
                            else:
                                self.subBasinDict[iDSub].increment_level()
                        elif(tmpString[i][0] == 'J' and (tmpString[i] in self.paramsTopology.myparams)):
                            nbInter += 1
                            if(self.paramsTopology.myparams[tmpString[i]]['type'][key_Param.VALUE] == 'Subbasin'):
                                nbSub += 1
                                iDSub = int(self.paramsTopology.myparams[tmpString[i]]['number'][key_Param.VALUE].replace('ss', ''))
                                if(self.subBasinDict[iDSub].alreadyUsed):
                                    print("ERROR: a subbasin has already been used. Please check the topology file!")
                                    sys.exit()
                                self.subBasinDict[iDSub].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i])
                                self.retentionBasinDict[element].add_directFluxObj(self.subBasinDict[iDSub],name=tmpString[i])
                                if(not(self.subBasinDict[iDSub].haveInlets)):
                                    self.subBasinDict[iDSub].isLeveled = True
                                    self.topologyDict['Level 1'][tmpString[i]] = self.subBasinDict[iDSub]
                                else:
                                    self.subBasinDict[iDSub].increment_level()

                            elif(self.paramsTopology.myparams[tmpString[i]]['type'][key_Param.VALUE] == 'RB'):
                                if(self.retentionBasinDict[tmpString[i]].alreadyUsed):
                                    # print("ERROR: a RB has aleady been used! Please check your topo file.")
                                    # sys.exit()
                                    print("This RB has at least 2 exits")
                                self.retentionBasinDict[tmpString[i]].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i])
                                self.retentionBasinDict[element].add_directFluxObj(self.retentionBasinDict[tmpString[i]],name=tmpString[i])

                            else:
                                print("This type of intersection is not recognised. Please check your topo file.")
                                sys.exit()

                        elif(tmpString[i] in self.junctionNamesDict):
                            junctionName = self.junctionNamesDict[tmpString[i]]

                            nbInter += 1
                            if(self.paramsTopology.myparams[junctionName]['type'][key_Param.VALUE] == 'Subbasin'):
                                nbSub += 1
                                iDSub = int(self.paramsTopology.myparams[junctionName]['number'][key_Param.VALUE].replace('ss', ''))
                                if(self.subBasinDict[iDSub].alreadyUsed):
                                    print("ERROR: a subbasin has already been used. Please check the topology file!")
                                    sys.exit()
                                self.subBasinDict[iDSub].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i])
                                self.retentionBasinDict[element].add_directFluxObj(self.subBasinDict[iDSub],name=tmpString[i])
                                if(not(self.subBasinDict[iDSub].haveInlets)):
                                    self.subBasinDict[iDSub].isLeveled = True
                                    self.topologyDict['Level 1'][tmpString[i]] = self.subBasinDict[iDSub]
                                else:
                                    self.subBasinDict[iDSub].increment_level()

                            elif(self.paramsTopology.myparams[junctionName]['type'][key_Param.VALUE] == 'RB'):
                                if(self.retentionBasinDict[junctionName].alreadyUsed):
                                    # print("ERROR: a RB has aleady been used! Please check your topo file.")
                                    # sys.exit()
                                    print("This RB has at least 2 exits")
                                self.retentionBasinDict[junctionName].add_downstreamObj(self.retentionBasinDict[element],name=tmpString[i])
                                self.retentionBasinDict[element].add_directFluxObj(self.retentionBasinDict[junctionName],name=tmpString[i])

                        else:
                            print("This type of inlet is not recognised. Please check your topo file.")
                            sys.exit()
            # If the intersection is a subbasin, same procedure as for the RB, exept that no direct flux
            # are considered anymore.
            elif(self.paramsTopology.myparams[element]['type'][key_Param.VALUE] == 'Subbasin'):
                elementId =  int(self.paramsTopology.myparams[element]['number'][key_Param.VALUE].replace('ss', ''))
                tmpString = self.paramsTopology.myparams[element]['inlets'][key_Param.VALUE].split(',')
                # If there are no inlet labelled by "--", add it on the first level
                if(len(tmpString)==1 and tmpString[0].strip()=='--'):
                    # self.topologyDict['Level 1'][element] = self.subBasinDict[elementId]
                    nbInter += 1
                    continue

                for i in range(len(tmpString)):
                    tmpString[i]= tmpString[i].strip()
                    # Save the dowstream link of each element in the dictionnary
                    if tmpString[i][0:2] == 'ss' :
                        nbSub += 1
                        iDSub =  int(tmpString[i].replace('ss', ''))
                        if(self.subBasinDict[iDSub].alreadyUsed):
                            print("ERROR: a subbasin has already been used. Please check the topology file!")
                            sys.exit()
                        self.subBasinDict[iDSub].add_downstreamObj(self.subBasinDict[elementId],name=tmpString[i])
                        self.subBasinDict[elementId].add_inlet(self.subBasinDict[iDSub],name=tmpString[i])
                        if(not(self.subBasinDict[iDSub].haveInlets)):
                            self.subBasinDict[iDSub].isLeveled = True
                            self.topologyDict['Level 1'][tmpString[i]] = self.subBasinDict[iDSub]
                        else:
                            self.subBasinDict[iDSub].increment_level()
                    elif tmpString[i][0] == 'J' and (tmpString[i] in self.paramsTopology.myparams):
                        nbInter += 1
                        if(self.paramsTopology.myparams[tmpString[i]]['type'][key_Param.VALUE] == 'Subbasin'):
                            nbSub += 1
                            iDSub = int(self.paramsTopology.myparams[tmpString[i]]['number'][key_Param.VALUE].replace('ss', ''))
                            if(self.subBasinDict[iDSub].alreadyUsed):
                                print("ERROR: a subbasin has already been used. Please check the topology file!")
                                sys.exit()
                            self.subBasinDict[iDSub].add_downstreamObj(self.subBasinDict[elementId],name=tmpString[i])
                            self.subBasinDict[elementId].add_inlet(self.subBasinDict[iDSub],name=tmpString[i])
                            if(not(self.subBasinDict[iDSub].haveInlets)):
                                self.subBasinDict[iDSub].isLeveled = True
                                self.topologyDict['Level 1'][tmpString[i]] = self.subBasinDict[iDSub]
                            elif(self.subBasinDict[iDSub].myLevel == 1):
                                self.subBasinDict[iDSub].increment_level()
                        elif(self.paramsTopology.myparams[tmpString[i]]['type'][key_Param.VALUE] == 'RB'):
                            if(self.retentionBasinDict[tmpString[i]].alreadyUsed):
                                print("ERROR: a RB has already been used! Please check your topo file.")
                                sys.exit()
                            self.retentionBasinDict[tmpString[i]].add_downstreamObj(self.subBasinDict[elementId],name=tmpString[i])
                            self.subBasinDict[elementId].add_inlet(self.retentionBasinDict[tmpString[i]],name=tmpString[i])
                        else:
                            print("This type of intersection is not recognised. Please check your topo file.")
                            sys.exit()

                    elif(tmpString[i] in self.junctionNamesDict):
                        junctionName = self.junctionNamesDict[tmpString[i]]

                        nbInter += 1
                        if(self.paramsTopology.myparams[junctionName]['type'][key_Param.VALUE] == 'Subbasin'):
                            nbSub += 1
                            iDSub = int(self.paramsTopology.myparams[junctionName]['number'][key_Param.VALUE].replace('ss', ''))
                            if(self.subBasinDict[iDSub].alreadyUsed):
                                print("ERROR: a subbasin has already been used. Please check the topology file!")
                                sys.exit()
                            self.subBasinDict[iDSub].add_downstreamObj(self.subBasinDict[elementId],name=tmpString[i])
                            self.subBasinDict[elementId].add_inlet(self.subBasinDict[iDSub],name=tmpString[i])
                            if(not(self.subBasinDict[iDSub].haveInlets)):
                                self.subBasinDict[iDSub].isLeveled = True
                                self.topologyDict['Level 1'][junctionName] = self.subBasinDict[iDSub]
                            elif(self.subBasinDict[iDSub].myLevel == 1):
                                self.subBasinDict[iDSub].increment_level()
                        elif(self.paramsTopology.myparams[junctionName]['type'][key_Param.VALUE] == 'RB'):
                            if(self.retentionBasinDict[junctionName].alreadyUsed):
                                print("ERROR: a RB has already been used! Please check your topo file.")
                                sys.exit()
                            self.retentionBasinDict[junctionName].add_downstreamObj(self.subBasinDict[elementId],name=tmpString[i])
                            self.subBasinDict[elementId].add_inlet(self.retentionBasinDict[junctionName],name=tmpString[i])
                        else:
                            print("This type of intersection is not recognised. Please check your topo file.")
                            sys.exit()

                    else:
                        print("This type of inlet is not recognised. Please check your topo file.")
                        sys.exit()

        # Necessary but not sufficent condition for the Catchment network to be valid.
        # Second verification in the TopoDict construction
        if(not(nbSub==self.nbSubBasin or nbSub==self.nbSubBasin-1) or nbInter==0):
            print("WARNING: all the subbasins or junctions are not used in the Catchment network! Please check your topo file.")
            # sys.exit()



    def complete_topoDict(self):
        """ Procedure that finish to complete the topo tree.
            Before calling this procedure, only the first level were completed in self.link_objects().

            Modified internal variables: self.topologyDict

            Strategy:
                - We save the element on a certain level if all his inlets have inferior levels.

            TO DO: Add a test that counts the number of subbasins and check if the number is right or not
                    -> take into account the fact that a subbasin can be the last element in this computation.
        """
        toContinue = True   # variable used to stop the while loop
        # As the first level is already completed, we begin at level 2
        if(self.nbSubBasin==1):
            return
        level = 2
        while(toContinue):
            levelName = 'Level '+ str(level)
            print('Complete '+levelName)
            self.topologyDict[levelName] = {}
            # element : name to search in the dict topo et catchment
            for element in self.topologyDict['Level '+str(level-1)]:
                # If one element in the previous level does not have a downstream
                # => It's the outlet of the Cachtment (as 1! outlet is possible in a same catchment)
                # => The level in the dictionnary is removed
                # => Stop the loop
                if(self.catchmentDict[element].downstreamObj == {}):
                    toContinue = False
                    # self.catchmentDict[element].increment_level()
                    del self.topologyDict[levelName]
                    break

                for elDown in self.catchmentDict[element].downstreamObj:
                    dowObj = self.catchmentDict[element].downstreamObj[elDown]
                    if(dowObj.myLevel > level):
                        continue
                    # iInlet : index of the inlet
                    okLevel = True
                    # We loop on the inlets of the downstream element:
                        # if: at least 1 element as the same or higher level as the current one
                            # => increment level of the downstream element
                            # => We go another element on level-1
                        # else: we save the downstream element in topo tree on the 'level' branch
                    for elInlet in dowObj.intletsObj:
                        if(dowObj.intletsObj[elInlet].myLevel >= level):
                            dowObj.increment_level()
                            okLevel = False
                            break
                        if(dowObj.intletsObj[elInlet].isLeveled == False):
                            dowObj.increment_level()
                            okLevel = False
                            break

                    if(type(dowObj) == RetentionBasin):
                        if(len(dowObj.directFluxObj) != 0):
                            for elInlet in dowObj.directFluxObj:
                                if(dowObj.directFluxObj[elInlet].myLevel >= level):
                                    dowObj.increment_level()
                                    okLevel = False
                                    break
                                if(dowObj.directFluxObj[elInlet].isLeveled == False):
                                    dowObj.increment_level()
                                    okLevel = False
                                    break
                    # Here all the inlets are on inferior level
                    if(okLevel):
                        tmpID = dowObj.iD
                        self.topologyDict[levelName][tmpID] = self.catchmentDict[tmpID]
                        dowObj.myLevel = level
                        self.catchmentDict[tmpID].isLeveled = True
            level += 1



    def construct_hydro(self, firstLevel=1, lastLevel=-1, fromStation:str="", updateAll:bool=False):
        """ This procedure will use the topo tree to build the hydrographs of all elements

            Internal variable changed: self.catchmentDict
        """
        if fromStation == "":
            if(lastLevel==-1):
                lastLevel = len(self.topologyDict)
            elif(lastLevel<firstLevel):
                print("ERROR : the first level should be greater than the last one!")
                sys.exit()
            elif(lastLevel>len(self.topologyDict)):
                print("ERROR : the last level should be smaller than maximum level indice !")
                sys.exit()

            print("Constructing hydros")
            for i in range(firstLevel, lastLevel+1):
                tmpLevel = 'Level '+ str(i)
                for element in self.topologyDict[tmpLevel]:
                    self.catchmentDict[element].compute_hydro()
        else:
            junctionKey = self.get_key_catchmentDict(name=fromStation)
            if junctionKey is None:
                logging.error("ERROR : Wrong station name to start an upstream update !")
                return
            self.catchmentDict[junctionKey].update_hydro(update_upstream=updateAll, level_min=firstLevel)



    def read_Jsonfile(self, fileName):
        "Function which reads a json file as input"
        with open(fileName, 'r') as json_file:
            data = json.load(json_file)
            print("data = ", data)
        return data



    def save_ExcelFile(self):
        "Procedure that saves the data in an Excel file."
        # Writes subbasins' hydrographs
        writer = pd.ExcelWriter(os.path.join(self.workingDir,"PostProcess/Data_outflow.xlsx"), engine = 'xlsxwriter')
        columnNames = ['Time [s]', 'Real hydrograph [m^3/s]', 'Raw hydrograph [m^3/s]']
        for element in self.subBasinDict:
            excelData = np.zeros((len(self.time),3))
            sheetName = self.subBasinDict[element].name
            curSub:SubBasin = self.subBasinDict[element]
            outFlowNet = curSub.outFlow_global
            outFlowRaw = curSub.outFlowRaw_global
            if(len(sheetName)>30):
                sheetName = sheetName[:30]
            for i in range(len(self.time)):
                excelData[i][0] = self.time[i]
                excelData[i][1] = outFlowNet[i]
                excelData[i][2] = outFlowRaw[i]
            df = pd.DataFrame(excelData, columns=columnNames)
            df.to_excel(writer , sheet_name= sheetName[0:min(len(sheetName),30)])
            curSheet = writer.sheets[sheetName]
            curSheet.autofit()
        # Writes the RB hydrographs
        for element in self.retentionBasinDict:
            curRB:RetentionBasin = self.retentionBasinDict[element]
            outFlowNames = curRB.get_outFlow_names()
            nbOutFlow = len(outFlowNames)
            excelData = np.zeros((len(self.time),1+nbOutFlow*2))
            sheetName = curRB.name
            columnNames = ['Time [s]']
            iOutFlow = 0
            for elOut in outFlowNames:
                myOutFlowNet = curRB.get_outFlow_global(whichOutFlow=elOut, typeOutFlow="Net")
                myOutFlowRaw = curRB.get_outFlow_global(whichOutFlow=elOut, typeOutFlow="Raw")
                columnNames.append(elOut+" Net")
                columnNames.append(elOut+" Raw")
                for i in range(len(self.time)):
                    excelData[i][0] = self.time[i]
                    excelData[i][iOutFlow*2+1] = myOutFlowNet[i]
                    excelData[i][iOutFlow*2+2] = myOutFlowRaw[i]
            df = pd.DataFrame(excelData, columns=columnNames)
            df.to_excel(writer , sheet_name= sheetName)
            curSheet = writer.sheets[sheetName]
            curSheet.autofit()

        writer.close()



    def save_ExcelFile_noLagTime(self):
        "Procedure that saves the data in an Excel file."
        # Writes subbasins' hydrographs
        writer = pd.ExcelWriter(os.path.join(self.workingDir,"PostProcess/Data_outflow_noLagTime.xlsx"), engine = 'xlsxwriter')
        columnNames = ['Time [s]', 'Real hydrograph [m^3/s]', 'Raw hydrograph [m^3/s]']
        for element in self.subBasinDict:
            excelData = np.zeros((len(self.time),3))
            sheetName = self.subBasinDict[element].name
            if(len(sheetName)>30):
                sheetName = sheetName[:30]
            tmpOutFlow = self.subBasinDict[element].get_outFlow_noDelay()
            tmpOutFlowRaw = self.subBasinDict[element].get_outFlowRaw_noDelay()
            for i in range(len(self.time)-1):
                excelData[i][0] = self.time[i]
                excelData[i][1] = tmpOutFlow[i]
                excelData[i][2] = tmpOutFlowRaw[i]
            df = pd.DataFrame(excelData, columns=columnNames)
            df.to_excel(writer , sheet_name= sheetName[0:min(len(sheetName),30)])
            curSheet = writer.sheets[sheetName]
            curSheet.autofit()

        # Writes the RB hydrographs
        for element in self.retentionBasinDict:
            excelData = np.zeros((len(self.time),3))
            sheetName = self.retentionBasinDict[element].name
            tmpOutFlow = self.retentionBasinDict[element].get_outFlow_noDelay()
            tmpOutFlowRaw = self.retentionBasinDict[element].get_outFlowRaw_noDelay()
            for i in range(len(self.time)-1):
                excelData[i][0] = self.time[i]
                excelData[i][1] = tmpOutFlow[i]
                excelData[i][2] = tmpOutFlowRaw[i]
            df = pd.DataFrame(excelData, columns=columnNames)
            df.to_excel(writer , sheet_name= sheetName)
            curSheet = writer.sheets[sheetName]
            curSheet.autofit()

        writer.close()

        print("File saved : ", os.path.join(self.workingDir,"PostProcess/Data_myHydro.xlsx"))


    def save_ExcelFile_inlets_noLagTime(self):
        "Procedure that saves the inlets in an Excel file."
        # Writes subbasins inlets' hydrographs
        writer = pd.ExcelWriter(os.path.join(self.workingDir,"PostProcess/Data_inlets_noLagTime.xlsx"), engine = 'xlsxwriter')
        for element in self.subBasinDict:
            columnNames = ['Time [s]', 'Real hydrograph [m^3/s]', 'Total inlets [m^3/s]', 'My hydro [m^3/s]']
            curSub:SubBasin = self.subBasinDict[element]
            nbInlets = len(curSub.intletsObj)
            iIndex = 4
            excelData = np.zeros((len(self.time),iIndex+nbInlets))
            sheetName = curSub.name
            if(len(sheetName)>30):
                sheetName = sheetName[:30]
            excelData[:,0] = curSub.time
            excelData[:,1] = curSub.get_outFlow_noDelay()
            excelData[:,2] = curSub.get_inlets_noDelay(unit="m3/s")
            excelData[:,3] = curSub.get_myHydro(unit="m3/s")
            # Go through all the inlets
            i = iIndex
            for iInlet in curSub.intletsObj:
                curIn = curSub.intletsObj[iInlet]
                curColumn = curIn.name+" ("+iInlet+") [m^3/s] at "+str(curIn.timeDelay-curSub.timeDelay)+" sec"
                columnNames.append(curColumn)
                excelData[:,i] = curIn.get_outFlow_noDelay()
                i += 1

            df = pd.DataFrame(excelData, columns=columnNames)
            df.to_excel(writer , sheet_name= sheetName[0:min(len(sheetName),30)])
            curSheet = writer.sheets[sheetName]
            curSheet.autofit()

        # Writes the RB hydrographs
        for element in self.retentionBasinDict:
            columnNames = ['Time [s]', 'Real hydrograph [m^3/s]', 'Total inlets [m^3/s]']
            curRB:RetentionBasin = self.retentionBasinDict[element]
            nbInlets = len(curRB.intletsObj)
            iIndex = 3
            excelData = np.zeros((len(self.time),iIndex+nbInlets))
            sheetName = curRB.name
            excelData[:,0] = curRB.time
            excelData[:,1] = curRB.get_outFlow(unit="m3/s")
            # excelData[:,2] = curRB.get_inlets_noDelay(unit="m3/s")
            excelData[:,2] = curRB.get_inlets(unit="m3/s") + curRB.get_direct_insideRB_inlets(unit="m3/s")

            i = iIndex
            for iInlet in curRB.intletsObj:
                curIn = curRB.intletsObj[iInlet]
                curColumn = iInlet+" [m^3/s] at "+str(curIn.timeDelay-curRB.timeDelay)+" sec"
                columnNames.append(curColumn)
                excelData[:,i] = curIn.get_outFlow_noDelay()
                i += 1
            df = pd.DataFrame(excelData, columns=columnNames)
            df.to_excel(writer , sheet_name= sheetName)
            curSheet = writer.sheets[sheetName]
            curSheet.autofit()

        writer.close()
        print("File saved : ", os.path.join(self.workingDir,"PostProcess/Data_myHydro.xlsx"))


    def save_ExcelFile_V2(self):
        "Procedure that saves the data in an Excel file."
        # Writes subbasins' hydrographs
        writer = pd.ExcelWriter(os.path.join(self.workingDir,"PostProcess/Data_myHydro.xlsx"), engine = 'xlsxwriter')
        nbSub = len(self.subBasinDict)
        excelData = np.zeros((len(self.time),nbSub+1))
        columnNames = []

        columnNames.append("Times")
        for element in self.subBasinDict:
            columnNames.append(self.subBasinDict[element].name)
            for i in range(len(self.time)-1):
                excelData[i][0] = self.time[i]
                excelData[i][element] = self.subBasinDict[element].myHydro[i]*self.subBasinDict[element].surfaceDrained/3.6
        df = pd.DataFrame(excelData, columns=columnNames)
        df.to_excel(writer, sheet_name="Hydrographs")

        excelData = np.zeros((nbSub,2))
        coordinateNames = ["x", "y"]
        columnNames.pop(0)

        for element in self.subBasinDict:
            excelData[element-1][0] = self.subBasinDict[element].x
            excelData[element-1][1] = self.subBasinDict[element].y

        df = pd.DataFrame(excelData, columns=coordinateNames, index=columnNames)
        df.to_excel(writer, sheet_name="Outlet coordinates")

        writer.close()
        print("File saved : ", os.path.join(self.workingDir,"PostProcess/Data_myHydro.xlsx"))


    def save_ExcelFile_Vesdre_simul2D(self, fileName="PostProcess/Data_simul2D.xlsx", directory=""):
        "Procedure that saves the data in an Excel file."
        # Writes subbasins' hydrographs
        if(directory==""):
            directory = os.path.join(self.workingDir,"PostProcess/")
        writer = pd.ExcelWriter(directory+fileName, engine = 'xlsxwriter')
        nbSub = len(self.subBasinDict)
        excelData = np.zeros((len(self.time)-1,19))
        columnNames = []
        listBasinsToSkip = ["SPIXHE", "Theux", "Eupen aval conf. Helle", "Belleheid", "BV Barrage Vesdre", "BV Barrage Gileppe", "BV Helle", "BV Soor"]
        basinToApplyAfter = ["Theux", "Eupen aval conf. Helle"]
        RBToApplyAfter = ["Gileppe", "Barrage Vesdre"]

        columnNames.append("Times")
        counter = 1
        for element in self.subBasinDict:
            curSubBasin = self.subBasinDict[element]
            if(curSubBasin.name in listBasinsToSkip):
                continue

            columnNames.append(self.subBasinDict[element].name)
            for i in range(len(self.time)-1):
                excelData[i][0] = self.time[i]
                excelData[i][counter] = self.subBasinDict[element].myHydro[i]*self.subBasinDict[element].surfaceDrained/3.6
            counter += 1

        for element in self.subBasinDict:
            curSubBasin = self.subBasinDict[element]
            if(curSubBasin.name == "Theux"):
                columnNames.append(self.subBasinDict[element].name)
                excelData[:,counter] = curSubBasin.get_outFlow_noDelay()
                counter += 1
            elif(curSubBasin.name == "Eupen aval conf. Helle"):
                columnNames.append(self.subBasinDict[element].name + "& Helle & Soor")
                currTimeDelay = curSubBasin.timeDelay
                curHydro = curSubBasin.myHydro*curSubBasin.surfaceDrained/3.6
                tmpHydro = np.zeros(len(curHydro))
                for iInlet in curSubBasin.intletsObj:
                    curInlet = curSubBasin.intletsObj[iInlet]
                    if(curInlet.name=="Helle" or curInlet.name=="Soor"):
                        tmpHydro += curInlet.get_outFlow(whichOutFlow=iInlet,typeOutFlow="Net")
                curHydro += curSubBasin.convert_data_global_to_local(tmpHydro)
                excelData[:,counter] = curHydro
                counter += 1

        for element in self.retentionBasinDict:
            curRB = self.retentionBasinDict[element]
            if(curRB.name in RBToApplyAfter):
                columnNames.append(curRB.name)
                excelData[:,counter] = curRB.get_outFlow_noDelay()
                counter += 1


        df = pd.DataFrame(excelData, columns=columnNames)
        df.to_excel(writer, sheet_name="Hydrographs")

        excelData = np.zeros((19-1,2))
        coordinateNames = ["x", "y"]
        columnNames.pop(0)

        counter = 0
        for element in self.subBasinDict:
            curSubBasin = self.subBasinDict[element]
            if(curSubBasin.name in listBasinsToSkip):
                continue

            excelData[counter][0] = curSubBasin.x
            excelData[counter][1] = curSubBasin.y
            counter += 1


        for element in self.subBasinDict:
            curSubBasin = self.subBasinDict[element]
            if(curSubBasin.name == "Theux"):
                excelData[counter][0] = curSubBasin.x
                excelData[counter][1] = curSubBasin.y
                counter += 1
            elif(curSubBasin.name == "Eupen aval conf. Helle"):
                excelData[counter][0] = curSubBasin.x
                excelData[counter][1] = curSubBasin.y
                counter += 1

        for element in self.retentionBasinDict:
            curRB = self.retentionBasinDict[element]
            if(curRB.name in RBToApplyAfter):
                excelData[counter][0] = curRB.x
                excelData[counter][1] = curRB.y
                counter += 1

        df = pd.DataFrame(excelData, columns=coordinateNames, index=columnNames)
        df.to_excel(writer, sheet_name="Outlet coordinates")

        writer.close()



    def save_ExcelFile_Vesdre_all(self, fileName="PostProcess/Data_simul2D.xlsx", directory=""):
        "Procedure that saves the data in an Excel file."
        # Writes subbasins' hydrographs
        if(directory==""):
            directory = self.workingDir + "PostProcess/"
        writer = pd.ExcelWriter(directory+fileName, engine = 'xlsxwriter')
        nbSub = len(self.subBasinDict)
        excelData = np.zeros((len(self.time)-1,27))
        columnNames = []
        # listBasinsToSkip = ["SPIXHE", "Theux", "Eupen aval conf. Helle", "Belleheid", "BV Barrage Vesdre", "BV Barrage Gileppe", "BV Helle", "BV Soor"]
        listBasinsToSkip = []
        basinToApplyAfter = ["Theux", "Eupen aval conf. Helle"]
        RBToApplyAfter = ["Gileppe", "Barrage Vesdre"]

        columnNames.append("Times")
        counter = 1
        for element in self.subBasinDict:
            curSubBasin = self.subBasinDict[element]
            if(curSubBasin.name in listBasinsToSkip):
                continue

            columnNames.append(self.subBasinDict[element].name)
            for i in range(len(self.time)-1):
                excelData[i][0] = self.time[i]
            excelData[:,counter] = self.subBasinDict[element].get_outFlow_noDelay()
            counter += 1


        for element in self.retentionBasinDict:
            curRB = self.retentionBasinDict[element]
            columnNames.append(curRB.name)
            excelData[:,counter] = curRB.get_outFlow_noDelay()
            counter += 1


        df = pd.DataFrame(excelData, columns=columnNames)
        df.to_excel(writer, sheet_name="Hydrographs")

        excelData = np.zeros((27-1,2))
        coordinateNames = ["x", "y"]
        columnNames.pop(0)

        counter = 0
        for element in self.subBasinDict:
            curSubBasin = self.subBasinDict[element]
            if(curSubBasin.name in listBasinsToSkip):
                continue

            excelData[counter][0] = curSubBasin.x
            excelData[counter][1] = curSubBasin.y
            counter += 1


        for element in self.retentionBasinDict:
            curRB = self.retentionBasinDict[element]
            if(curRB.name in RBToApplyAfter):
                excelData[counter][0] = curRB.x
                excelData[counter][1] = curRB.y
                counter += 1

        df = pd.DataFrame(excelData, columns=coordinateNames, index=columnNames)
        df.to_excel(writer, sheet_name="Outlet coordinates")

        writer.close()



    def save_hydro_for_2D(self, fileName:str="Hydros_2_simul2D.txt", directory:str="", format:str='%1.5e'):
        """
        Procedure that saves the data in an text file that can be read and used in a 2D model.

        Args:
            fileName (str, optional): The name of the file to save the data to. Defaults to "Hydros_2_simul2D.txt".
            directory (str, optional): The directory to save the file in. Defaults to an empty string.

        Returns:
            None
        """
        # Writes subbasins' hydrographs
        if(directory==""):
            directory = join(self.workingDir,"PostProcess")

        cur_file = join(directory,fileName)
        time = np.reshape(self.time - self.time[0],(len(self.time),1))
        # Extract the data for the hydrological and anthropogenic modules
        data_subs = [cur_sub.outFlow for cur_sub in sorted(self.subBasinDict.values(), key=lambda sub: sub.iDSorted)]
        data_anth = [cur_anth.get_outFlow(whichOutFlow=name) for cur_anth in self.retentionBasinDict.values() for name in cur_anth.get_outFlow_names()]
        # Extract the column names according to their sorted subbasin indices
        col_time = ["Time [s]"]
        col_subs = [cur_sub.name for cur_sub in sorted(self.subBasinDict.values(), key=lambda sub: sub.iDSorted)]
        col_anth = [" : ".join([cur_anth.name, name])
                    for cur_anth in self.retentionBasinDict.values()
                    for name in cur_anth.get_outFlow_names()]


        all_data = np.concatenate((time, np.array(data_subs).T, np.array(data_anth).T), axis=1)
        all_columns = "\t".join(col_time+col_subs+col_anth)

        # Save the data in a text file
        np.savetxt(cur_file, all_data, delimiter='\t', newline="\n", header=all_columns, fmt=format)


    def save_own_hydro_for_2D(self, fileName:str="HydrosSub_2_simul2D.txt", directory:str="", format:str='%1.5e'):
        """
        Saves subbasins' hydrographs from their own drained surface only (not taking into account the
        surface drained by the inlets or upstream elements) to a text file that can be read and used in a 2D model.

        Args:
            fileName (str, optional): Name of the output file. Defaults to "HydrosSub_2_simul2D.txt".
            directory (str, optional): Directory where the file will be saved. Defaults to an empty string.
            format (str, optional): Format string for the data values. Defaults to '%1.5e'.

        Returns:
            None
        """
        # Writes subbasins' hydrographs
        if(directory==""):
            directory = join(self.workingDir,"PostProcess")

        cur_file = join(directory,fileName)
        time = np.reshape(self.time - self.time[0],(len(self.time),1))
        # Extract the data for the hydrological and anthropogenic modules
        data_subs = [cur_sub.get_myHydro(unit="m3/s") for cur_sub in sorted(self.subBasinDict.values(), key=lambda sub: sub.iDSorted)]
        # Extract the column names according to their sorted subbasin indices
        col_time = ["Time [s]"]
        col_subs = [cur_sub.name for cur_sub in sorted(self.subBasinDict.values(), key=lambda sub: sub.iDSorted)]


        all_data = np.concatenate((time, np.array(data_subs).T), axis=1)
        all_columns = "\t".join(col_time+col_subs)

        # Save the data in a text file
        np.savetxt(cur_file, all_data, delimiter='\t', newline="\n", header=all_columns, fmt=format)


    def save_characteristics(self):
        "Procedure that saves the data in an Excel file."
        # Writes subbasins' main characteristics
        writer = pd.ExcelWriter(os.path.join(self.workingDir,"PostProcess/Basins_Characteristics.xlsx"), engine = 'xlsxwriter')
        columnNames = ['Characteristic', 'unit']
        # excelData = np.zeros((16,self.nbSubBasin+2))
        # excelData = [[] for i in range(self.nbSubBasin+2)]
        excelData = [[] for i in range(100)]
        iBasin = 1
        for level in self.topologyDict:
            for curBasin in self.topologyDict[level]:
                if(type(self.topologyDict[level][curBasin])!=SubBasin):
                    continue

                if(iBasin==1):
                    excelData[0].append("Coord")
                    excelData[0].append("x")
                    excelData[1].append("Coord")
                    excelData[1].append("y")
                    iChar = 2
                    for name in self.topologyDict[level][curBasin].mainCharactDict:
                        excelData[iChar].append(name)
                        excelData[iChar].append(self.topologyDict[level][curBasin].mainCharactDict[name]["unit"])

                        iChar += 1

                columnNames.append(self.topologyDict[level][curBasin].name)
                iChar = 2
                excelData[0].append(self.topologyDict[level][curBasin].x)
                excelData[1].append(self.topologyDict[level][curBasin].y)
                for curChar in self.topologyDict[level][curBasin].mainCharactDict:
                    excelData[iChar].append(self.topologyDict[level][curBasin].mainCharactDict[curChar]["value"])
                    iChar += 1
                iBasin += 1

        df = pd.DataFrame(excelData, columns=columnNames)
        df.to_excel(writer)
        writer.close()



    def read_dbfFile(self, fileName):
        dbfDict = DBF(fileName, load=True)
        return dbfDict



    def init_hyetoDict(self):
        """ Procedure that saves the all the hyeto data of the Catchment in a dictionnary
            Internal variables modified: self.hyetoDict

            Structure du dictionnaire
            self.hyetoDict:
                - Ordered To Nb: self.hyetoDict['Ordered To Nb'][nb] = iD
                    - iD = hyeto nb of the file to read in the folder "Whole_basin". E.g.: the file "[iD]evap.hyeto"
                    - nb = hyeto number sorted from 1 to nbHyeto. E.g.: if iD=['2', '5', '7'] => self.hyetoDict['Ordered To Nb'][2] = '5'
                - Hyetos : self.hyetoDict['Hyetos'][nb]
                    - time: time array read in the .hyeto file
                    - rain: rain array read in the .hyeto file

        TO DO: Consider a more general way to detect .dbf files. E.G. when the data are read in NetCDF files.
        """

        # Read the DBF file to save all the "Ordered To Nb" in the dictionnary
        fileName = os.path.join(self.workingDir, "Whole_basin/Rain_basin_geom.vec.dbf")

        if self.type_of_rain == cst.source_municipality_unit_hyeto:
            try:
                if(os.path.exists(fileName)):
                    dbfDict = self.read_dbfFile(fileName)
                    self.hyetoDict['Ordered To Nb'] = {}
                    self.hyetoDict['Hyetos'] = {}

                    for i in range(len(dbfDict.records)):
                        iDsorted = i + 1
                        iDHyeto = dbfDict.records[i]['data']
                        self.hyetoDict['Ordered To Nb'][iDsorted] = iDHyeto

                    # Read all the .hyeto file to save the time and rain arrays
                    beginFileName = os.path.join(self.workingDir,"Whole_basin/")
                    endFileName = "rain.hyeto"
                    for element in self.hyetoDict['Ordered To Nb']:
                        nbToRead = self.hyetoDict['Ordered To Nb'][element]
                        fileName = os.path.join(beginFileName, nbToRead+ endFileName)
                        isOk, fileName = check_path(fileName, applyCWD=True)
                        if isOk<0:
                            # print("WARNING: could not find any dbf file! ")
                            time_mod.sleep(.5)
                            return
                        [time, rain] = self.get_hyeto(fileName)
                        self.hyetoDict['Hyetos'][element] = {}
                        self.hyetoDict['Hyetos'][element]['time'] = time
                        self.hyetoDict['Hyetos'][element]['rain'] = rain
            except:
                print("WARNING: problem in some dbf file! ")
                time_mod.sleep(.5)
            else:
                print("WARNING: could not find any dbf file! ")
                time_mod.sleep(.5)


    def add_rainToAllObjects(self):
        "Add rain and hyetographs to all subbasins"

        # for element in self.subBasinDict:
        #     timeTest, _ = self.subBasinDict[element].add_rain(self.workingDir)
        #     if not(np.array_equal(timeTest,self.time)):
        #         print("ERROR: the time arrays are different!")
        #     self.subBasinDict[element].add_hyeto(self.workingDir, self.hyetoDict)
        txt = "Level "
        for i in range(1,len(self.topologyDict)+1):
            indexName = txt + str(i)
            for element in self.topologyDict[indexName]:
                timeTest = self.topologyDict[indexName][element].add_rain(self.workingDir, tzDelta=datetime.timedelta(hours=self.tz))

                if timeTest is None:
                    print(f"WARNING: No rain data found for {element} in {indexName}.")
                    continue

                if not(np.array_equal(timeTest,self.time)):
                    print("ERROR: the time arrays are different!")
                if type(self.topologyDict[indexName][element]) == SubBasin:
                    try:
                        self.topologyDict[indexName][element].add_hyeto(self.workingDir, self.hyetoDict)
                    except:
                        print("ERROR! The hyeto couldn't be created. This might be induced by the lack of the dbf file!")



    def plot_intersection(self, rangeData=[], plot_raw=True, tzPlot=0, axis:str="Datetime", show:bool=True):
        "This procedure will plot all the subbasins or RB with level>1 in the topo tree."
        txt = "Level "
        # plot_raw = True
        if(len(self.retentionBasinDict)==0 and not(plot_raw)):
            plot_raw = False
        for i in range(2, len(self.topologyDict)+1):
            indexName = txt + str(i)
            for element in self.topologyDict[indexName]:
                self.topologyDict[indexName][element].plot(self.workingDir,plot_raw,axis=axis,rangeData=rangeData,tzPlot=tzPlot)
        if show:
            plt.show()



    def plot_allSub(self, withEvap=False, withCt=False, selection_by_iD=[], graph_title="", show=True, writeDir="", figure=None, Measures=[]):
        "This procedure plots the hydrographs and hyetographs of all subbasins"

        if(selection_by_iD==[]):
            for element in self.subBasinDict:
                graph_title_basin = graph_title + " " + self.subBasinDict[element].name
                writeFile = writeDir + "_" + self.subBasinDict[element].name.replace(".","")
                self.subBasinDict[element].plot_myBasin(withEvap=withEvap, withCt=withCt, graph_title=graph_title_basin, writeFile=writeFile, figure=figure)
        else:
            if Measures==[]:
                Measures = [None]*len(selection_by_iD)
            else:
                if(len(Measures)!=len(selection_by_iD)):
                    print("ERROR : cannot plot with Measures as it has not the same dimensions as the selection_by_iD variable.")
                    print("len(Measures) = ", len(Measures))
                    print("len(selection_by_iD) = ", len(selection_by_iD))
                    print("Plot without Measure ...")
                    Measures = [None]*len(self.selection_by_iD)

            index = 0
            for element in selection_by_iD:
                if element in self.subBasinDict:
                    graph_title_basin = graph_title + " " + self.subBasinDict[element].name
                    writeFile = writeDir + "_" + self.subBasinDict[element].name.replace(".","")
                    self.subBasinDict[element].plot_myBasin(Measures=Measures[index],withEvap=withEvap, withCt=withCt, graph_title=graph_title_basin, writeFile=writeFile, figure=figure)
                index += 1

        if(show):
            plt.show()


    def plot_allJct(self, withEvap=False, selection_by_key=[], graph_title="", show=True, writeDir="", figure=None, Measures=[], Measure_unit="m3/s", addTable=False, rangeData=[]):
        "This procedure plots the hydrographs and hyetographs of all junctions"

        if(writeDir==""):
            writeDir = os.path.join(self.workingDir, "PostProcess", "Junction")
        else:
            writeDir = os.path.join(writeDir, "Junction")

        if(selection_by_key==[]):
            for element in self.subBasinDict:
                graph_title_module = graph_title + " " + self.subBasinDict[element].name
                writeFile = writeDir + "_" + self.subBasinDict[element].name.replace(".","")
                self.subBasinDict[element].plot_outlet(withEvap=withEvap, graph_title=graph_title_module, writeFile=writeFile, figure=figure, withDelay=False, Measure_unit=Measure_unit, addTable=addTable, rangeData=rangeData)
            for element in self.retentionBasinDict:
                graph_title_module = graph_title + " " + self.retentionBasinDict[element].name
                writeFile = writeDir + "_" + self.retentionBasinDict[element].name.replace(".","")
                self.retentionBasinDict[element].plot_outlet(withEvap=withEvap, graph_title=graph_title_module, writeFile=writeFile, figure=figure, withDelay=False, Measure_unit=Measure_unit, addTable=addTable, rangeData=rangeData)

        else:
            allKeys = self.get_keys_catchmentDict(selection_by_key)
            if Measures==[]:
                Measures = [None]*len(selection_by_key)
            else:
                if(len(Measures)!=len(selection_by_key)):
                    print("ERROR : cannot plot with Measures as it has not the same dimensions as the selection_by_iD variable.")
                    print("len(Measures) = ", len(Measures))
                    print("len(selection_by_iD) = ", len(selection_by_key))
                    print("Plot without Measure ...")
                    Measures = [None]*len(self.selection_by_iD)

            index = 0
            for element in allKeys:
                if element in self.catchmentDict:
                    graph_title_module = graph_title + " " + self.catchmentDict[element].name
                    writeFile = writeDir + "_" + self.catchmentDict[element].name.replace(".","")
                    self.catchmentDict[element].plot_outlet(Measures=Measures[index],withEvap=withEvap, graph_title=graph_title_module, writeFile=writeFile, figure=figure, withDelay=False, Measure_unit=Measure_unit, addTable=addTable, rangeData=rangeData)
                index += 1

        if(show):
            plt.show()



    def draw_flowChart(self, flowchart):
        """This procedure save and plot a flowchart representing the topo tree
            input: - flowchart: graphviz.Digraph Object -> modified at the end

        """

        # Creation of the flowchart nodes -> first iteration of the topo tree.
        for level in range(1, len(self.topologyDict)+1):
            nameLevel = 'Level ' + str(level)
            with flowchart.subgraph() as s:
                s.attr(rank='same')
                for element in self.topologyDict[nameLevel]:
                    nodeName = self.topologyDict[nameLevel][element].name
                    if(type(self.topologyDict[nameLevel][element])==RetentionBasin):
                        shapeName = 'box'
                    elif(type(self.topologyDict[nameLevel][element])==SubBasin):
                        shapeName = 'ellipse'
                        nodeID = self.topologyDict[nameLevel][element].iD
                        sortNodeID = str(self.topologyDict[nameLevel][element].iDSorted)
                        if(nodeID != nodeName.replace(' ', '')):
                            nodeName += ' ('+nodeID+')'
                        nodeName += ' [sub'+sortNodeID+']'
                    s.node(nodeName, shape=shapeName)
        # Creation of the flowchart edges -> second iteration of the topo tree.
        for level in range(1, len(self.topologyDict)):
            nameLevel = 'Level ' + str(level)
            for element in self.topologyDict[nameLevel]:
                nodeName = self.topologyDict[nameLevel][element].name
                if(type(self.topologyDict[nameLevel][element])==SubBasin):
                    nodeID = self.topologyDict[nameLevel][element].iD
                    sortNodeID = str(self.topologyDict[nameLevel][element].iDSorted)
                    if(nodeID != nodeName.replace(' ', '')):
                        nodeName += ' ('+nodeID+')'
                    nodeName += ' [sub'+sortNodeID+']'
                for idownStream in self.topologyDict[nameLevel][element].downstreamObj:
                    downName = self.topologyDict[nameLevel][element].downstreamObj[idownStream].name
                    if(type(self.topologyDict[nameLevel][element].downstreamObj[idownStream])==SubBasin):
                        nodeID = self.topologyDict[nameLevel][element].downstreamObj[idownStream].iD
                        sortNodeID = str(self.topologyDict[nameLevel][element].downstreamObj[idownStream].iDSorted)
                        if(nodeID != downName.replace(' ', '')):
                            downName += ' ('+nodeID+')'
                        downName += ' [sub'+sortNodeID+']'
                    flowchart.edge(nodeName, downName)

    def save_flow_chart(self, filename="Topology", directory="") -> str:
        """ This procedure saves the flowchart representing the topo tree

        :param filename: Name of the file to save the flowchart as.
        :param directory: Directory where the flowchart will be saved. If not provided, it will be saved in the working directory.
        """

        flowchart = graphviz.Digraph("Test")
        flowchart.format = 'png'
        self.draw_flowChart(flowchart)
        # flowchart.view()
        flowchart.save(directory=self.workingDir)
        flowchart.render(os.path.join(self.workingDir,"Topology"), view=False)

        logging.info("Flowchart saved as: " + os.path.join(self.workingDir,"Topology.png"))
        return os.path.join(self.workingDir,"Topology.png")

    def make_stat_distributionOfslope(self):
        """ This procedure plot the stat distribution of slopes.
        """
        print("Procedure for slope's stat distribution ongoing")
        slope_wolf_array = WolfArray(os.path.join(self.workingDir,"Characteristic_maps/Drainage_basin.slope"))
        slope_array = []
        for i in range(slope_wolf_array.nbx):
            for j in range(slope_wolf_array.nby):
                element = slope_wolf_array.get_value_from_ij(i,j)
                if element == float('inf'):
                    continue
                slope_array.append(element)
        slope_arraySort = np.sort(slope_array, axis = None)
        maxSlope = slope_arraySort[len(slope_arraySort)-1]
        myBins = np.arange(0,maxSlope, 0.0001)
        slopeHisto = np.histogram(slope_arraySort, bins=myBins, density=True)

        return slopeHisto, slope_arraySort
        print("Hello!")



    def make_stat_distributionOfTime(self):
        """ This procedure plot the stat distribution of slopes.
        """
        print("Procedure for slope's stat distribution ongoing")
        slope_wolf_array = WolfArray(os.path.join(self.workingDir,"Characteristic_maps/Drainage_basin.slope"))
        slope_array = []
        for i in range(slope_wolf_array.nbx):
            for j in range(slope_wolf_array.nby):
                element = slope_wolf_array.get_value_from_ij(i,j)
                if element == float('inf'):
                    continue
                slope_array.append(element)
        slope_arraySort = np.sort(slope_array, axis = None)
        maxSlope = slope_arraySort[len(slope_arraySort)-1]
        myBins = np.arange(0,maxSlope, 0.0001)
        slopeHisto = np.histogram(slope_arraySort, bins=myBins, density=True)

        return slopeHisto, slope_arraySort
        print("Hello!")



    def check_massConservation(self):
        """ This procedure check whether the mass conservation is verified ot not.
        """
        print("Checking the mass conservation ...")

        cumulRain = 0.0
        cumulFlow = 0.0


        nbLevels = len(self.topologyDict)

        # CAUTION !!!!!!hardcoded value for the Ourthe Basin !!!!!!!!
        surface = 1615.02000*(1000.0)**2
        ds = 10000.0
        not_used_rain = 1.45312406886231*ds



        tmpCount = 0
        nameLastLevel = 'Level '+ str(nbLevels)
        for element in self.topologyDict[nameLastLevel]:
            nbElements = len(self.topologyDict[nameLastLevel][element].rain)
            plotCumulRain = np.zeros(nbElements)
            plotCumulFlow = np.zeros(nbElements)
            outFLow = self.topologyDict[nameLastLevel][element].get_outFlow_global(typeOutFlow="Net")

            cumulRain = np.sum(self.topologyDict[nameLastLevel][element].rain)      # [mm/h]
            cumulFlow = np.sum(outFLow)   # [m^3/s]
            # cumulFlow = np.sum(self.topologyDict[nameLastLevel][element].outFlow)   # [m^3/s]
            plotCumulRain[0] = self.topologyDict[nameLastLevel][element].rain[0]*self.deltaT
            plotCumulFlow[0] = outFLow[0]*self.deltaT
            for i in range(1,nbElements):
                plotCumulRain[i] = plotCumulRain[i-1] + self.topologyDict[nameLastLevel][element].rain[i]*self.deltaT
                plotCumulFlow[i] = plotCumulFlow[i-1] + outFLow[i]*self.deltaT

        cumulRain = cumulRain/(1000.0*3600.0)*surface
        cumulFlow = cumulFlow+not_used_rain
        plotCumulRain = plotCumulRain/(1000.0*3600.0)*surface

        # ~~~~~~~~~~~~~~~~~~
        x = (self.time/(3600.0*24.0*365.0))+2000.0

        font11 = FontProperties()
        font11.set_family('serif')
        font11.set_name('Euclid')
        font11.set_size(11)

        font14 = FontProperties()
        font14.set_family('serif')
        font14.set_name('Euclid')
        font14.set_size(14)

        plt.figure(figsize=(11.7,8.3))
        plt.grid()
        plt.xlabel('Temps [h]', fontproperties=font11)
        plt.ylabel('Volume cumulé [m³]', fontproperties=font11)
        plt.legend(loc="best")
        plt.title(self.name + " Conservation du volume", fontproperties=font14)

        y = plotCumulRain
        plt.plot(x, y, label = 'pluie')
        y = plotCumulFlow
        plt.plot(x, y, label = 'volume écoulé')
        plt.xlim(2000, 2003)
        plt.xticks([2000, 2001, 2002, 2003])
        plt.legend(prop=font11)
        plt.savefig(os.path.join(self.workingDir,'PostProcess/Conservation_volume_'+self.name+'.pdf'))
        print("Is it the correct mass?")
        plt.show()
        print("Hello!")



    def copy(self):

        copiedObj = Catchment(self.name, self.workingDir,False, True, _initWithResults=False)

        copiedObj.time = self.time.copy()
        copiedObj.deltaT = self.deltaT
        copiedObj.dateBegin = copy.deepcopy(self.dateBegin)
        copiedObj.dateEnd = copy.deepcopy(self.dateEnd)
        copiedObj.myModel = self.myModel
        copiedObj.nbCommune = self.nbCommune
        copiedObj.nbSubBasin = self.nbSubBasin
        copiedObj.hyeto = copy.deepcopy(self.hyeto)
        copiedObj.catchmentDict = copy.deepcopy(self.catchmentDict)
        copiedObj.subBasinDict = copy.deepcopy(self.subBasinDict)
        copiedObj.retentionBasinDict = copy.deepcopy(self.retentionBasinDict)
        copiedObj.topologyDict = copy.deepcopy(self.topologyDict)
        copiedObj.dictIdConversion = copy.deepcopy(self.dictIdConversion)
        copiedObj.hyetoDict = copy.deepcopy(self.hyetoDict)
        copiedObj.intersection = copy.deepcopy(self.intersection)

        return copiedObj



    def get_time_btw_ssbasins(self, stationNames=[], unit='h', ref=[]):
        """
            Returns the transfer time between susBasin modules
        """
        deltaTimeMat = []
        deltaTime =[]
        if(stationNames!=[]):
            nbIntervals = len(stationNames)
            for iStation in range(nbIntervals):
                deltaTimeMat.append([-1,-1])
                for ii in range(1,len(self.subBasinDict)+1):
                    if(self.subBasinDict[ii].name==stationNames[iStation][0]):
                        index = 0
                    elif(self.subBasinDict[ii].name==stationNames[iStation][1]):
                        index = 1
                    else:
                        continue
                    x = self.subBasinDict[ii].x
                    y = self.subBasinDict[ii].y
                    i, j = self.time_wolf_array.get_ij_from_xy(x,y)
                    deltaTimeMat[iStation][index] = self.time_wolf_array.array[i][j]
                    if(unit=="h"):
                        deltaTimeMat[iStation][index] /=3600.0

                deltaTime.append(deltaTimeMat[iStation][1]-deltaTimeMat[iStation][0])

        for iStation in range(nbIntervals):
            if(unit=='h'):
                hours = math.floor(deltaTime[iStation])
                minutes = math.floor((deltaTime[iStation]-hours)*60.0)
                seconds = math.floor((((deltaTime[iStation]-hours)*60.0)-minutes)*60.0)
                stringTime = str(hours) + "h" + str(minutes) + "m" + str(seconds) + "sec"
            if(ref!=[]):
                print(stationNames[iStation][0] + " -> " + stationNames[iStation][1] + " = " + stringTime + " / " + ref[iStation] +" [" + unit + "] ")
            else:
                print(stationNames[iStation][0] + " -> " + stationNames[iStation][1] + " = " + stringTime + " [" + unit + "] ")

        return deltaTime




    def operation_on_param_file(self, fileName, which, operation=None):


        if(which=="Umax"):
            for iBasin in range(1,len(self.subBasinDict)+1):
                myBasin = self.subBasinDict[iBasin]
                dirID = myBasin.iDSorted

                fileToModif = os.path.join(self.workingDir, "//Subbasin_" + str(dirID) + "//" + fileName)

                paramsInput = Wolf_Param(to_read=False,toShow=False)
                paramsInput.ReadFile(fileToModif)
                try:
                    myInterval = paramsInput.get_param("Distributed production model parameters", "Time span soil")
                    nbIntervals = math.floor(myInterval/myBasin.deltaT)
                except:
                    nbIntervals = len(myBasin.myRain)-1

                # ['Semi distributed model']['How many?'][key_Param.VALUE]

                maxRain = 0.0
                for iel in range(len(myBasin.myRain)-nbIntervals):
                    mySum = np.sum(myBasin.myRain[iel:iel+nbIntervals])*myBasin.deltaT/3600.0
                    if maxRain < mySum:
                        maxRain = mySum

                paramsInput.myparams["Distributed production model parameters"][which][key_Param.VALUE] = maxRain

                # paramsInput.ApplytoMemory(None)
                paramsInput.SavetoFile(None)


    def _correct_Umax_from_old_model(self, adapt_with_rain:bool=True, k_opt:float=0.0, U_max_opt=0.0):
        fileName = "simul_soil.param"
        which="Umax"

        for iBasin in range(1,len(self.subBasinDict)+1):
            myBasin = self.subBasinDict[iBasin]
            dirID = myBasin.iDSorted

            fileToModif = os.path.join(self.workingDir, "Subbasin_" + str(dirID), fileName)

            paramsInput = Wolf_Param(to_read=False,toShow=False)
            paramsInput.ReadFile(fileToModif)

            if U_max_opt>0.0:
                maxRain = U_max_opt
            elif adapt_with_rain:
                myInterval = paramsInput.get_param("Distributed production model parameters", "Time span soil", default_value=0.0)
                if myInterval==0.0:
                    nbIntervals = len(myBasin.myRain)-1
                else:
                    nbIntervals = math.floor(myInterval/myBasin.deltaT)
                kernel = np.ones(nbIntervals)
                volRain = np.convolve(myBasin.myRain, kernel)*myBasin.deltaT/3600.0
                maxRain = np.max(volRain)
            else:
                maxRain = paramsInput.get_param("Distributed production model parameters", "Umax")
                if maxRain==0.0:
                    logging.warning("The Umax is not adapted with the rain and its value is 0.0. It might be better to put 'adapt_with_rain' to True.")

            if k_opt==0.0:
                k = paramsInput.get_param("Horton parameters", "k", default_value=0.0)
                if k==0.0:
                    continue
            else:
                k = k_opt

            U_max = maxRain/k

            paramsInput.change_param("Distributed production model parameters", which, U_max)
            paramsInput.change_param("Horton parameters", "k", 0.0)

            # paramsInput.ApplytoMemory(None)
            paramsInput.SavetoFile(None)



    def plot_all_diff_cumulRain_with_lagtime(self, interval=0, lagTime=0, selection_by_iD=[], graph_title="", show=True, writeDir="", lawNetRain=0, netRainParams={}):
        """

        """

        if(selection_by_iD==[]):
            for iBasin in range(1,len(self.subBasinDict)+1):
                curBasin = self.subBasinDict[iBasin]
                curBasin.plot_diff_cumulRain_with_lagtime(interval, lagTime, graph_title=graph_title, writeDir=writeDir, lawNetRain=lawNetRain, netRainParams=netRainParams)
        else:
            for iBasin in self.subBasinDict:
                if iBasin in selection_by_iD:
                    curBasin = self.subBasinDict[iBasin]
                    curBasin.plot_diff_cumulRain_with_lagtime(interval, lagTime, graph_title=graph_title, writeDir=writeDir, lawNetRain=lawNetRain, netRainParams=netRainParams)

        if(show):
            plt.show()


    def get_all_cumulRain(self, selection_by_iD=[]) -> tuple[np.array, list[np.array]]:
        '''

        '''
        list_rain = []

        if(selection_by_iD==[]):
            for iBasin in range(1,len(self.subBasinDict)+1):
                curBasin:SubBasin = self.subBasinDict[iBasin]
                list_rain.append(curBasin.cumul_rain)
        else:
            for iBasin in self.subBasinDict:
                if iBasin in selection_by_iD:
                    curBasin:SubBasin = self.subBasinDict[iBasin]
                    list_rain.append(curBasin.cumul_rain)


        return self.time, list_rain


    def read_measuring_stations_SPW(self, fileNameIn=""):
        """
        Function that read the stations, their characteristics and locations and store all information in a dictionnary
        """

        # Collect fileName
        if fileNameIn!="":
             fileName = fileNameIn
        else:
            directory = self.paramsInput.get_param("Measuring stations SPW", "Directory")
            isOk, directory = check_path(directory, self.workingDir)
            if isOk<0:
                logging.error(_("ERROR : measuring station data path not present! "))
            fileName = os.path.join(directory, self.paramsInput.get_param("Measuring stations SPW", "Filename"))


        if os.path.exists(fileName):
            # Reading the station file
            with open(fileName, newline = '') as fileID:
                data_reader = csv.reader(fileID, delimiter='\t')
                list_data = []
                i = 0
                for raw in data_reader:
                    list_data.append(raw)
        else:
            logging.error(_("ERROR : measuring station data file not present! "))
            return

        # Building dictionnary
        for line in list_data:
            key = line[3].replace("'","")
            if(line[2][-4:]=="1002"):
                keyCode = int(line[2])
                self.myStationsDict[key] = {}
                self.myStationsDict[key]["Number"] = int(line[0])
                self.myStationsDict[key]["Reference"] = line[1].replace("'","")
                self.myStationsDict[key]["Station Code"] = int(line[2])
                self.myStationsDict[key]["Station Name"] = line[3].replace("'","")
                self.myStationsDict[key]["River Name"] = line[4].replace("'","")
                self.myStationsDict[key]["Day"] = int(line[5])
                self.myStationsDict[key]["Month"] = int(line[6])
                self.myStationsDict[key]["Year"] = int(line[7])
                self.myStationsDict[key]["X"] = int(line[8])
                self.myStationsDict[key]["Y"] = int(line[9])
                self.myStationsDict[key]["Z"] = float(line[10])

                self.myStationsDict[keyCode] = self.myStationsDict[key]



    def get_eff_subBasin(self):

        nbIP = self.paramsInput[("Semi distributed model", "How many?")]
        try:
            allSub = int(self.paramsInput[("Semi distributed model", "Compute all?")])
        except:
            allSub = 1

        if(allSub==0 or allSub==-1):
            for i in range(1,nbIP+1):
                isActive = self.paramsInput[(f"Interior point {i}", "Active")]
                if(isActive==1):
                    self.myEffSortSubBasins.append(self.dictIdConversion[i])
                    self.myEffSubBasins.append(i)
        else:
            for i in range(1,nbIP+1):
                self.myEffSortSubBasins.append(self.dictIdConversion[i])
                self.myEffSubBasins.append(i)

        if(allSub==-1 or allSub==1):
            self.myEffSortSubBasins.append(self.dictIdConversion[nbIP+1])
            self.myEffSubBasins.append(nbIP+1)

        self.myEffSortSubBasins.sort()

    def get_one_surfaces_proportions(self, whichName):

        for element in self.subBasinDict:
            curObj = self.subBasinDict[element]
            curName = curObj.name
            if curName.relace(" ","") == whichName.relace(" ",""):
                mySurf = curObj.get_surface_proportions(show=True)

        return mySurf


    # def construct_hydro_from_sub(self, subID:int, isSort:bool=False):
    #     if isSort:
    #         myID = self.dictIdConversion[subID]
    #     else:
    #         myID = subID

    #     for ilevel in range(1,len(self.topologyDict)+1):

    def update_hydro(self, idCompar, fromLevel:bool=False, level_min:int=1):

        print("I'm here!")

        isOk = 0

        if fromLevel:
            self.construct_hydro(lastLevel=self.levelOut, firstLevel=level_min)
        else:
            self.construct_hydro(fromStation=self.junctionOut)

        return isOk



    def get_cvg(self, pointerData):

        isOk = 0

        nbT = len(self.time)
        myshape = (nbT,2)

        myArray = self.make_nd_array(pointerData, myshape, dtype=ct.c_double, order='F', own_data=False)

        # myData = np.zeros(myshape, dtype=ct.c_double, order='F')
        # myData[:,0] = self.time

        if(self.junctionOut == ""):
            lastLevel = len(self.topologyDict)
            prefix = "Level "
            nameSub = list(self.topologyDict[prefix+str(lastLevel)].items())[0][0]
            myArray[:,1] = self.topologyDict[prefix+str(lastLevel)][nameSub].evaluate_objective_function(unit='mm/h')
        else:
            myArray[:,1] = self.catchmentDict[self.junctionOut].evaluate_objective_function(unit='mm/h')


        # pointerData = myData.ctypes.data_as(ct.POINTER(ct.c_double))


        return isOk


    def define_station_out(self, stationOut):

        if(stationOut in self.junctionNamesDict):
            junctionName = self.junctionNamesDict[stationOut]
        else:
            junctionName = stationOut

        if(junctionName in self.catchmentDict):
            self.junctionOut = junctionName
            self.levelOut = self.catchmentDict[junctionName].myLevel
            return 0
        else:
            logging.error("ERROR : junction not found!")
            self.junctionOut = self.get_lastJunctionKey()
            self.levelOut = len(self.topologyDict)
            return -1


    def sort_level_given_junctions(self, givenJct:list, changeNames=False):
        sortList = []
        levelList = []
        nameList = []
        sortIndex = []
        for element in givenJct:
            if element in self.junctionNamesDict:
                junctionName = self.junctionNamesDict[element]
            else:
                junctionName = element

            if(junctionName in self.catchmentDict):
                nameList.append(junctionName)
                levelList.append(self.catchmentDict[junctionName].myLevel)
                # curLevel = self.catchmentDict[junctionName].myLevel
            else:
                print("ERROR : junction not found!")
                return None

        sortIndex = np.argsort(levelList)

        for i in range(len(sortIndex)):
            if(changeNames):
                sortList.append(nameList[sortIndex[i]])
            else:
                sortList.append(givenJct[sortIndex[i]])


        return sortList


    def construct_surfaceDrainedHydro_RB(self):

        prefix = 'Level '
        for level in range(1,len(self.topologyDict)+1):
            levelName = prefix + str(level)
            for element in self.topologyDict[levelName]:
                curObj = self.topologyDict[levelName][element]
                if type(curObj) == RetentionBasin:
                    curObj.construct_surfaceDrainedHydro()



    def activate_usefulSubs(self, mask=[], blockJunction=[], onlyItself:bool=False):

        self.myEffSubBasins = []
        self.myEffSortSubBasins = []

        if(self.junctionOut==""):
            lastLevel = len(self.topologyDict)
            prefix = "Level "
            junctionName = list(self.topologyDict[prefix+str(lastLevel)].items())[0][0]
        else:
            junctionName = self.junctionOut

        self.catchmentDict[junctionName].unuse()
        # Block certain junction not to activate all his upstream inlets
        for element in blockJunction:
            blockKey = self.get_key_catchmentDict(element)
            if blockKey is not None:
                self.catchmentDict[blockKey].alreadyUsed = True

        self.myEffSubBasins, self.myEffSortSubBasins = self.catchmentDict[junctionName].activate(
            effSubs=[], effSubsSort=[], mask=mask, onlyItself=onlyItself)

        self.write_eff_subBasin()


    def get_key_catchmentDict(self, name):


        if name in self.catchmentDict:
            junctionKey = name
        elif name in self.junctionNamesDict:
            junctionKey = self.junctionNamesDict[name]
        else:
            print("ERROR: the name is not a key of catchmentDict!")
            junctionKey = None

        return junctionKey


    def get_keys_catchmentDict(self, names:list):
        junctionKeys:list = []

        for curName in names:
            junctionKeys.append(self.get_key_catchmentDict(curName))

        return junctionKeys


    def write_eff_subBasin(self):

        self.paramsInput.change_param("Semi distributed model", "Compute all?", 0)
        for iSub in range(1,len(self.subBasinDict)):
            self.paramsInput.change_param("Interior point "+str(iSub), "Active", 0)

        for iSub in self.myEffSubBasins:
            if(iSub!=len(self.subBasinDict)):
                self.paramsInput.change_param("Interior point "+str(iSub), "Active", 1)
            else:
                self.paramsInput.change_param("Semi distributed model", "Compute all?", -1)

        self.paramsInput.SavetoFile(None)
        self.paramsInput.Reload(None)



    def read_hydro_eff_subBasin(self):

        for iSub in self.myEffSubBasins:
            curSub:SubBasin
            curSub = self.subBasinDict[iSub]
            timeTest, curSub.myHydro = curSub.get_hydro(curSub.iDSorted, self.workingDir, tzDelta = datetime.timedelta(self.tz))



    def update_timeDelay(self, stationName, value=0.0, reset=False):
        deltaT = value
        if(self.junctionOut==""):
            lastLevel = len(self.topologyDict)
            prefix = "Level "
            refName = list(self.topologyDict[prefix+str(lastLevel)].items())[0][0]
        else:
            refName = self.junctionOut

        isOk = 0
        junctionName = self.get_key_catchmentDict(stationName)
        curModule = self.catchmentDict[junctionName]
        refModule = self.catchmentDict[refName]
        initTime = refModule.timeDelay

        self.reset_timeDelay(stationOut=stationName)
        print("All reset timeDelays = ", self.get_all_timeDelay())
        curModule.add_timeDelay(initTime+deltaT, reset=reset, resetAll=False)
        print("All updated timeDelays = ", self.get_all_timeDelay())

        return isOk


    ## Update all timeDelays according to time_delays_F -> then it should be associated with the variable in Fortran
    def update_timeDelays_from_F(self, stationName, value=0.0, reset=False):
        isOk = 0
        junctionName = self.get_key_catchmentDict(stationName)
        refModule = self.catchmentDict[junctionName]
        initTime = refModule.timeDelay
        refID_F = refModule.iDSorted
        refID = refID_F-1

        for element in refModule.intletsObj:
            curModule = refModule.intletsObj[element]
            curID_F = curModule.get_iDSorted()
            curID = curID_F-1
            self.reset_timeDelay(stationOut=element)
            print("All reset timeDelays = ", self.get_all_timeDelay())
            deltaT = self.time_delays_F[curID]-self.time_delays_F[refID]
            curModule.add_timeDelay(initTime+deltaT, reset=reset, resetAll=False)
            print("All updated timeDelays = ", self.get_all_timeDelay())
            print("time_delays_F = ", self.time_delays_F)

        return isOk



    def reset_timeDelay(self, stationOut=""):

        if(stationOut!=""):
            junctionName = self.get_key_catchmentDict(stationOut)
            upStreamTime = 0.0
        elif(self.junctionOut==""):
            lastLevel = len(self.topologyDict)
            prefix = "Level "
            junctionName = list(self.topologyDict[prefix+str(lastLevel)].items())[0][0]
            upStreamTime = -1.0
        else:
            junctionName = self.junctionOut
            upStreamTime = -1.0

        curModule = self.catchmentDict[junctionName]
        # The first element should keep its timeDelay (upStreamTime=-1), but for the others the delta should be kept
        # curModule.reset_timeDelay(keepDelta=False, keepDeltaAll=True, upStreamTime=-1.0)
        curModule.reset_timeDelay(keepDelta=False, keepDeltaAll=True, upStreamTime=upStreamTime)


    def get_inletsName(self, stationOut):

        junctionName = self.get_key_catchmentDict(stationOut)
        curModule = self.catchmentDict[junctionName]
        allInlets = curModule.get_inletsName()

        return allInlets



    def get_all_timeDelay(self, ref = ""):

        if(ref==""):
            junctionKey = self.junctionOut
        else:
            junctionKey = self.get_key_catchmentDict(name=ref)
            if junctionKey is None:
                logging.error("ERROR : Wrong reference to extract timeDelay !")
                return

        timeDelays = {}
        refObj = self.catchmentDict[junctionKey]
        timeDelays["Cur station = "+refObj.name] = refObj.timeDelay
        for element in refObj.intletsObj:
            curInlet = refObj.intletsObj[element]
            timeDelays = curInlet.get_timeDelays(timeDelays=timeDelays)


        return timeDelays


    def get_timeDelays_inlets(self, ref:str = "") -> dict[str, float]:


        if(ref==""):
            junctionKey = self.junctionOut
        else:
            junctionKey = self.get_key_catchmentDict(name=ref)
            if junctionKey is None:
                logging.error("ERROR : Wrong reference to extract timeDelay !")
                return

        junctionKey = self.junctionOut
        refObj = self.catchmentDict[junctionKey]
        time_delays_inlets = refObj.get_timeDelays_inlets()

        return time_delays_inlets


    ## Procedure that force all SubBasins to write their timeDelays and all upstream elements
    # @var junctionList
    def save_timeDelays(self, junctionList:list):

        for element in junctionList:
            junctionName = self.get_key_catchmentDict(element)
            if junctionName is None:
                print("ERROR : abort saving the timeDelays of ", junctionName)
            self.catchmentDict[junctionName].save_timeDelays()



    ## Function that returns the last element junction key name
    def get_lastJunctionKey(self):

        lastLevel = len(self.topologyDict)
        prefix = "Level "
        junctionName = list(self.topologyDict[prefix+str(lastLevel)].items())[0][0]

        return junctionName



    ## Set all timeDelays for each elements
    def set_timeDelays(self, method="wolf_array", junctionKey="", readWolf:bool=True, updateAll:bool=False):

        if method.lower() == "wolf_array":
            # If asked, time wolf_array are read again
            if readWolf==True:
                self.time_wolf_array = WolfArray(os.path.join(self.workingDir,"Characteristic_maps/Drainage_basin.time"))
                self.charact_watrshd.to_update_times = True
                self.update_charact_watrshd()
            # Update only 1 element and tranfer it to the upstream elements
            if updateAll:
                if junctionKey == "":
                    refName = self.junctionOut
                else:
                    refName = self.get_key_catchmentDict(junctionKey)
                refModule = self.catchmentDict[refName]

                refTime = refModule.get_value_outlet(self.time_wolf_array)

                for element in refModule.intletsObj:
                    curModule = refModule.intletsObj[element]
                    ti = curModule.get_value_outlet(self.time_wolf_array)
                    deltaTime = ti-refTime
                    self.update_timeDelay(stationName=element, value=deltaTime)
            # Update all upstream element according the time wolf_array
            else:
                print("ERROR : updateAll cannot be False, this situation is not implemented yet! -> Catchment.py/set_timeDelays")
                return
        else:
            print("ERROR : This method is not implemented yet! -> Catchment.py/set_timeDelays")
            # for curLevel in self.topologyDict:
            #     for element in self.topologyDict[curLevel]:
            #         self.topologyDict[curLevel][element].set_timeDelay(method=method, wolfarray=self.time_wolf_array)
            return


    ## Find all time delays and save timeDelayObj in all RetentionBasin
    def find_all_timeDelayObj(self):
        curRB:RetentionBasin
        timeDelays:list = []

        for element in self.retentionBasinDict:
            curRB = self.retentionBasinDict[element]
            timeDelays.append(curRB.find_timeDelayObj())

        return timeDelays


    ## plot all the timeDelays whether it is only the subbasin or the hydrological subbasin.
    def plot_landuses(self, selection_by_iD:list=[], graph_title:str="",  onlySub:bool=True, show:bool=True, writeDir:str="", figure=None):
        if(selection_by_iD==[]):
            for element in self.subBasinDict:
                curSub:SubBasin = self.subBasinDict[element]
                curSub.plot_landuses(onlySub=onlySub, figure=figure, toShow=show, writeFile=writeDir)
        else:
            for element in selection_by_iD:
                if element in self.subBasinDict:
                    curSub:SubBasin = self.subBasinDict[element]
                    curSub.plot_landuses(onlySub=onlySub, figure=figure, toShow=show, writeFile=writeDir)

        if(show):
            plt.show()


    def read_all_landuses(self):

        landuse_file = self.paramsInput.get_param(group="LandUse", name="Directory")
        isOk, landuse_file = check_path(landuse_file, prefix=self.workingDir)

        for key in self.subBasinDict:
            curSub:SubBasin = self.subBasinDict[key]
            # Read subbasin landuses
            curSub.read_landuses(onlySub=True, landuse_index_transform=landuse_file, toSave=True)
            # Read hydro subbasin landuses
            curSub.read_landuses(onlySub=False, landuse_index_transform=landuse_file, toSave=True)


    ## Build a compare file compatible for optimisation from a C_hyd file
    def build_compare_file(self, hydroFile:str, unit:str="mm/h", otherSurf:float=0.0, lag:int=0, junction:str="",
                           dateBegin:datetime.datetime=None, dateEnd:datetime.datetime=None, deltaT:datetime.timedelta=None):

        curDir = os.path.dirname(hydroFile)
        curFile = os.path.basename(hydroFile)
        GMTdata = datetime.timedelta(hours=lag)

        # Init if the time characteristics
        if dateBegin == None:
            dateBegin = self.dateBegin
        if dateEnd == None:
            dateEnd = self.dateEnd
        if deltaT == None:
            deltaT = self.deltaT

        # Get the disired Subbasin object or create a new one
        if junction == "":
            if otherSurf==0.0 and unit=="mm/h":
                logging.error("If no surface is provided or its value is 0.0, it is impossible to provide hydro to compare in mm/h ! ")
                return -1
            if unit != "mm/h":
                logging.error("Other unit than mm/h not implemented yet !")

            curJct = SubBasin(dateBegin, dateEnd, deltaT, constant.measures, curDir)
            tmp, hydro = curJct.get_hydro(1, workingDir=curDir, fileNames=curFile, tzDelta=GMTdata)
            surface = otherSurf
        else:
            junctionKey = self.get_key_catchmentDict(junction)
            if junctionKey == None:
                logging.error("ERROR : The junction name given in 'build_compare_file' is not correct ! " + junctionKey)
                return -1
            curJct = self.catchmentDict[junctionKey]
            tmp, hydro = curJct.get_hydro(1, workingDir=curDir, fileNames=curFile, tzDelta=GMTdata)
            surface = curJct.surfaceDrainedHydro

        # Transform hydro in compatible
        if unit == "mm/h":
            cmpHydro = hydro * 3.6/surface
        else:
            logging.error("Other units not taken into account yet !")
            return -1



        return 0


    def change_version(self, newVersion=None):

        if newVersion == None:
            self._version = float(cst.VERSION_WOLFHYDRO)
        elif type(newVersion) == str:
            self._version = float(newVersion)
        else:
            self._version = newVersion

        return


    def get_version(self):

        return self._version



    def get_sub_Nash(self, measure:SubBasin,
                     selection_by_iD,
                     intervals:list[tuple[datetime.datetime]]=[]):

        # for element in selection_by_iD:
        #     junctionKey = self.get_key_catchmentDict(name=element)
        #     if junctionKey in self.subBasinDict:
        #         curSub:SubBasin = self.subBasinDict[junctionKey]
        #         ns = curSub.evaluate_Nash(measure=measure, intervals=intervals)
        junctionKey = self.get_key_catchmentDict(name=selection_by_iD)
        if junctionKey in self.catchmentDict:
            curSub:SubBasin = self.catchmentDict[junctionKey]
            ns = curSub.evaluate_Nash(measure=measure, intervals=intervals)

        return ns



    def get_sub_peak(self, selection_by_iD,
                     intervals:list[tuple[datetime.datetime]]=[]):

        junctionKey = self.get_key_catchmentDict(name=selection_by_iD)
        if junctionKey in self.catchmentDict:
            curSub:SubBasin = self.catchmentDict[junctionKey]
            ns = curSub.get_peak(intervals=intervals)

        return ns


    def set_eff_outlet_coord(self):

        try:
            all_nodes = [self.charact_watrshd.find_rivers(whichsub=ii+1) for ii in range(self.nbSubBasin)]
            if len(all_nodes) == 0:
                logging.warning("No effective outlet coordinates found in the watershed. Please check the watershed data.")
                return -1
            all_nodes = [sublist[0][0] for sublist in all_nodes if len(sublist[0]) > 0]
            for el in all_nodes:
                el:Node_Watershed
                mysubxy=wolfvertex(el.x,el.y)
                self.subBasinCloud.add_vertex(mysubxy)
            return 0
        except Exception as e:
            logging.error(f"Error in setting effective outlet coordinates: {e}")
            return -1

    def update_charact_watrshd(self):
        if self.charact_watrshd.to_update_times:
            self.charact_watrshd.update_times(self.time_wolf_array)


    def get_all_x_production(self, selection_by_iD: list = [], to_save:bool=True, to_plot:bool=False) -> dict:
        """
        Retrieves the x production values for all sub-basins or a specific selection of sub-basins.

        Args:
            selection_by_iD (list, optional): A list of sub-basin IDs to retrieve x production values for.
                                              If empty, retrieves x production values for all sub-basins.
                                              Defaults to [].

        Returns:
            dict: A dictionary containing the sub-basin names or IDs as keys and their corresponding x production values as values.
        """

        all_x = {}

        if selection_by_iD == []:
            for iBasin in range(1, len(self.subBasinDict) + 1):
                curBasin: SubBasin = self.subBasinDict[iBasin]
                all_x[curBasin.name] = curBasin.collect_x_from_production()
        else:
            for curID in selection_by_iD:
                cur_key = self.get_key_catchmentDict(curID)
                curBasin: SubBasin = self.catchmentDict[cur_key]
                all_x[curID] = curBasin.collect_x_from_production()

        if to_save:
            rd.write_excel_from_dict(all_x, path=self.workingDir, fileName="PostProcess/all_x.xlsx", time=self.time)

        return all_x


    def get_all_fractions(self, plt_dict:dict[str:np.array]={},selection_by_iD: list = [],
                          to_save:bool=True, to_plot:bool=False,
                          summary:str=None, summary_interval:list[datetime.datetime]=None,
                          add_info:dict[dict[str,float]]={}) -> dict:
        """
        Retrieves the physical flux fractions values for all sub-basins or a specific selection of sub-basins.

        Args:
            selection_by_iD (list, optional): A list of sub-basin IDs to retrieve fractions values for.
                                              If empty, retrieves fractions values for all sub-basins.
                                              Defaults to [].

        Returns:
            dict: A dictionary containing the sub-basin names or IDs as keys and their corresponding fractions values as values.
        """

        all_fractions = {}

        if selection_by_iD == []:
            all_fractions = {curBasin.name: curBasin.collect_fractions() for curBasin in self.subBasinDict.values()}

        else:
            for curID in selection_by_iD:
                cur_key = self.get_key_catchmentDict(curID)
                curBasin: SubBasin = self.catchmentDict[cur_key]
                all_fractions[curID] = curBasin.collect_fractions()

        if summary is not None:
            summary_fractions = {}
            summary_dict = {}
            if selection_by_iD == []:
                summary_fractions = {curBasin.name: curBasin.get_summary_fractions(summary=summary, interval=summary_interval)
                                     for curBasin in self.subBasinDict.values()}
            else:
                for curID in selection_by_iD:
                    cur_key = self.get_key_catchmentDict(curID)
                    curBasin: SubBasin = self.catchmentDict[cur_key]
                    summary_fractions[curID] = curBasin.get_summary_fractions(summary=summary, interval=summary_interval)

            summary_dict["Stations"] = [cur_name for cur_name in summary_fractions]
            # Get columns names and remove all duplicates with set
            all_columns = list(set(cur_key for cur_dict in summary_fractions.values() for cur_key in cur_dict.keys()))

            for cur_dict in summary_fractions.values():
                for cur_key in all_columns:
                    if cur_key not in summary_dict:
                        summary_dict[cur_key] = []
                    if not cur_key in cur_dict:
                        summary_dict[cur_key].append(np.nan)
                    else:
                        summary_dict[cur_key].append(cur_dict[cur_key])

            if add_info!={}:
                for key_add, add_dict in add_info.items():
                    summary_dict[key_add] = []
                    for key in summary_dict["Stations"]:
                        if key in add_dict:
                            summary_dict[key_add].append(add_dict[key])
                        else:
                            summary_dict[key_add].append(np.nan)



            # summary_dict = {cur_key: [cur_dict[cur_key] for cur_dict in summary_fractions.values() if cur_key in cur_dict]
            #                 for cur_dict in summary_fractions.values() for cur_key in cur_dict}
            # all_fractions["Summary"] = summary_dict

        if to_save:
            rd.write_excel_from_dict(all_fractions, path=self.workingDir, fileName="PostProcess/all_frac.xlsx", time=self.time, summary=summary_dict)

        if to_plot:
            self.plot_all_fractions(all_fractions)

        return all_fractions


    def plot_all_fractions(self, all_fractions:dict[str:np.array]={}, selection_by_iD:list=[], to_show:bool=False, writeDir:str="", range_data:list[datetime.datetime]=[]):

        if(writeDir==""):
            writeDir = os.path.join(self.workingDir, "PostProcess")

        if selection_by_iD == []:
            for curBasin in self.subBasinDict.values():
                curBasin.plot_all_fractions(all_fractions=all_fractions, to_show=False, writeDir=writeDir, range_data=range_data)
        else:
            for curID in selection_by_iD:
                cur_key = self.get_key_catchmentDict(curID)
                curBasin: SubBasin = self.catchmentDict[cur_key]
                curBasin.plot_all_fractions(to_show=False, writeDir=writeDir, range_data=range_data)

        if to_show:
            plt.show()

        return

    def get_all_iv_production(self, selection_by_iD: list = [], to_save:bool=True) -> dict:
        """
        Retrieves the x production values for all sub-basins or a specific selection of sub-basins.

        Args:
            selection_by_iD (list, optional): A list of sub-basin IDs to retrieve x production values for.
                                              If empty, retrieves x production values for all sub-basins.
                                              Defaults to [].

        Returns:
            dict: A dictionary containing the sub-basin names or IDs as keys and their corresponding x production values as values.
        """

        all_iv = {}

        if selection_by_iD == []:
            for iBasin in range(1, len(self.subBasinDict) + 1):
                curBasin: SubBasin = self.subBasinDict[iBasin]
                all_iv[curBasin.name] = curBasin.collect_all_internal_variables()
        else:
            for curID in selection_by_iD:
                cur_key = self.get_key_catchmentDict(curID)
                curBasin: SubBasin = self.catchmentDict[cur_key]
                all_iv[curID] = curBasin.collect_all_internal_variables()

        if to_save:
            rd.write_excel_from_dict(all_iv, path=self.workingDir, fileName="PostProcess/all_iv.xlsx", time=self.time)

        return all_iv


    def activate_all_internal_variables(self, selection_by_iD: list = [])->dict:
        """
        Activates all internal variables for all sub-basins or a specific selection of sub-basins.

        Args:
            selection_by_iD (list, optional): A list of sub-basin IDs to activate internal variables for.
                                              If empty, activates internal variables for all sub-basins.
                                              Defaults to [].

        Returns:
            dict: A dictionary containing the sub-basin names or IDs as keys and their corresponding internal variables as values.
        """

        if selection_by_iD == []:
            for iBasin in range(1, len(self.subBasinDict) + 1):
                curBasin: SubBasin = self.subBasinDict[iBasin]
                curBasin.activate_all_internal_variables()
        else:
            for curID in selection_by_iD:
                cur_key = self.get_key_catchmentDict(curID)
                curBasin: SubBasin = self.catchmentDict[cur_key]
                curBasin.activate_all_internal_variables()


    def check_presence_of_iv(self, selection_by_iD: list = []) -> dict:
        """
        Checks the presence of internal variables for all sub-basins or a specific selection of sub-basins.

        Args:
            selection_by_iD (list, optional): A list of sub-basin IDs to check the presence of internal variables for.
                                              If empty, checks the presence of internal variables for all sub-basins.
                                              Defaults to [].

        Returns:
            dict: A dictionary containing the sub-basin names or IDs as keys and their corresponding internal variables as values.
        """

        all_x = {}

        if selection_by_iD == []:
            for iBasin in range(1, len(self.subBasinDict) + 1):
                curBasin: SubBasin = self.subBasinDict[iBasin]
                all_x[curBasin.name] = curBasin.check_presence_of_iv()
        else:
            for curID in selection_by_iD:
                cur_key = self.get_key_catchmentDict(curID)
                curBasin: SubBasin = self.catchmentDict[cur_key]
                all_x[curID] = curBasin.check_presence_of_iv()

        return all_x


    def get_all_Qtest(self, selection_by_iD: list = [], nb_atttempts:int=-1) :

        if selection_by_iD == []:
            q_test = [curBasin.get_all_Qtest(nb_atttempts) for curBasin in self.subBasinDict.values()]
        else:
            # for curID in selection_by_iD:
            #     cur_key = self.get_key_catchmentDict(curID)
            #     curBasin: SubBasin = self.catchmentDict[cur_key]
            #     q_test = curBasin.get_all_Qtest(nb_atttempts)
            q_test = [
                self.catchmentDict[self.get_key_catchmentDict(curID)].get_all_Qtest(nb_atttempts)
                for curID in selection_by_iD ]

        return q_test


    def _get_simulation_intervals(self):
        """
        This procedure is getting the simulation intervals of the current module.
        """

        nb_interv = self.paramsInput.get_param("Simulation intervals", "Nb", default_value=0)
        simulation_intervals = []
        for i in range(1, nb_interv+1):
            str_di = self.paramsInput.get_param("Simulation intervals", "Date begin "+str(i))
            di = datetime.datetime.strptime(str_di, cst.DATE_FORMAT_HYDRO).replace(tzinfo=datetime.timezone.utc)
            str_df = self.paramsInput.get_param("Simulation intervals", "Date end "+str(i))
            df = datetime.datetime.strptime(str_df, cst.DATE_FORMAT_HYDRO).replace(tzinfo=datetime.timezone.utc)
            simulation_intervals.append((di,df))

        return simulation_intervals


    def _set_simulation_intervals(self, simulation_intervals:list[tuple[datetime.datetime,datetime.datetime]]):
        """
        This procedure is setting the simulation intervals of the current module.
        """

        self.paramsInput.change_param("Simulation intervals", "Nb", len(simulation_intervals))
        for i, interval in enumerate(simulation_intervals):
            self.paramsInput.change_param("Simulation intervals", "Date begin "+str(i+1), interval[0].strftime(cst.DATE_FORMAT_HYDRO))
            self.paramsInput.change_param("Simulation intervals", "Date end "+str(i+1), interval[1].strftime(cst.DATE_FORMAT_HYDRO))

        self.paramsInput.SavetoFile(None)
        self.paramsInput.Reload(None)


    @property
    def simulation_intervals(self) ->list[tuple[datetime.datetime,datetime.datetime]]:
        return self._get_simulation_intervals()


    @simulation_intervals.setter
    def simulation_intervals(self, value:list[tuple[datetime.datetime,datetime.datetime]]):
        self._set_simulation_intervals(value)


    def _get_temporal_parameters(self) ->tuple[datetime.datetime, datetime.datetime]:
        """
        This procedure is getting the temporal parameters of the current module.
        """

        return (self.dateBegin, self.dateEnd)


    def _set_temporal_parameters(self, simulation_intervals:tuple[datetime.datetime,datetime.datetime]):
        """
        This procedure is setting the temporal parameters of the current module.
        """

        self.dateBegin = simulation_intervals[0]
        self.dateEnd = simulation_intervals[1]

        self.paramsInput.change_param("Temporal Parameters", "Start date time", self.dateBegin.strftime(cst.DATE_FORMAT_HYDRO))
        self.paramsInput.change_param("Temporal Parameters", "End date time", self.dateEnd.strftime(cst.DATE_FORMAT_HYDRO))

        self.paramsInput.SavetoFile(None)
        self.paramsInput.Reload(None)


    @property
    def temporal_parameters(self) ->tuple[datetime.datetime, datetime.datetime]:
        return self._get_temporal_parameters()


    @temporal_parameters.setter
    def temporal_parameters(self, value:tuple[datetime.datetime,datetime.datetime]):
        self._set_temporal_parameters(value)


    def _set_IC_qif(self, keys:list[str], values:np.ndarray):
        assert len(keys) == len(values), "The number of keys should be equal to the number of values !"
        # assert len(keys) == len(self.subBasinDict), "The number of keys should be equal to the number of sub-basins !"
        # assert len(values) == len(self.subBasinDict), "The number of values should be equal to the number of sub-basins !"
        fileName = "simul_if.param"
        group = "Initial conditions"
        key = "Outflow"

        for iBasin in range(1,len(self.subBasinDict)+1):
            if self.subBasinDict[iBasin].name in keys:
                index = np.where(np.array(keys) == self.subBasinDict[iBasin].name)[0][0]
            else:
                logging.warning(f"The sub-basin {self.subBasinDict[iBasin].name} is not in the keys list !")
                continue
            myBasin = self.subBasinDict[iBasin]
            dirID = myBasin.iDSorted

            fileToModif = os.path.join(self.workingDir, "Subbasin_" + str(dirID), fileName)

            paramsInput = Wolf_Param(to_read=False,toShow=False)
            paramsInput.ReadFile(fileToModif)
            paramsInput.change_param(group, key, values[index])
            paramsInput.SavetoFile(None)
            paramsInput.Reload(None)


    def get_outflow(self, station_out:str="") -> np.ndarray:
        """
        Set the initial conditions for the outflow of the outlet defined by junctionOut.

        Args:
            keys (list[str]): List of sub-basin names.
            values (np.ndarray): Corresponding outflow values for each sub-basin.
        """
        if station_out == "":
            key_module = self.junctionOut
        else:
            key_module = self.get_key_catchmentDict(station_out)
            if station_out is None:
                logging.error("ERROR : The station name given in 'get_outflow' is not correct ! " + station_out)
                return None
        cur_module = self.catchmentDict[key_module]
        return cur_module.get_outFlow()


    @property
    def type_of_rain(self) -> int:
        rain = self.paramsInput.get_param("Atmospheric data", "Type of rainfall")
        if rain == cst.source_custom:
            rain = self.paramsInput.get_param("Custom inputs", "Rain data")

        return rain


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
