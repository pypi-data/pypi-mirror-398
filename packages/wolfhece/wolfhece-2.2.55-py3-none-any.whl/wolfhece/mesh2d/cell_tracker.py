"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

#Libraries
from os.path import join, exists
import matplotlib.pyplot as plt
import numpy as np
import logging

from ..PyTranslate import _
from .. import wolfresults_2D as res

#This class tracks the evolution of a variable on specific cell(s)
class Tracker:

    def __init__(self, directory:str=None, filename:str='simul'):
        #Model Initializtaion

        self.directory = directory
        if directory is None:
            self.directory = str(input("Please, Insert the path to the models: "))

        self.link = join(self.directory, filename)

        if exists(self.link):
            self.model = res.Wolfresults_2D(self.link)
        else:
            logging.warning(_("Bad file or path -- Retry !"))

    def coords(self):
        #Choice of the entry method
        choice = int(input("Will you use a preestablished list (0) or Will you insert  a list of points coordinate (1)"))
        if choice == 0:
            template = (input("Which Vesdre model?\n\
                (0): Scenario Verviers new\n\
                (1): Vesdre - Tr 3 - Chaudfontaine - Confluence Ourthe\n\
                (2): Vesdre - Tr 3 - Prayon - Chaudfontaine\n\
                (3): Vesdre - Tr 3 - Nessonvaux - Prayon\n\
                (4): Vesdre - Tr 3 - Les Douwis - Nessonvaux\n\
                (5): Vesdre - Tr 3 - Confluence Hoegne - Les Douwis\n\
                (6): Vesdre - Tr 2b - Verviers - Confluence Hoegne\n\
                (7): Vesdre - Tr 2b - Renoupre - Verviers\n\
                (8): Vesdre - Tr 2b - Limbourg - Renoupre\n\
                (9): Vesdre - Tr 2b - Confluence La Gileppe - Limbourg\n\
                (10): Vesdre - Tr 2a - Confluence Helle - Confluence La Gileppe\n\
                (11): Vesdre - Tr 1 - Barrage Eupen - Confluence Helle\n\
                (12): Hoegne - Tr 3 - Forges Thiry - Confluence Vesdre\n\
                (13): Hoegne - Tr 3 - Confluence Wayai - Forges Thiry\n\
                Insert the integer of your choice: "))

            if template == "1":
                coords = np.array([[33,383,3], [752,788,2],[1298,86,2]])
                #USE WOLFPY TO FIND CORRESPONDING CELLS NEAR BOUNDARY CONDITIONS
            elif template =="2":
                coords = np.array([[26,585,2], [663,364,2],[1624,32,2]])

            elif template =="3":
                coords = np.array([[19,708,2], [1080,166,2],[2137,601,2]])

            elif template =="4":
                coords = np.array([[34,413,2], [734,712,2],[1702,117,2]])

            elif template == "5":
                coords = np.array([[76, 8, 3], [101,410 , 4],[220, 58, 4],[1067, 350, 3]])

            elif template == "6":
                coords = np.array([[15, 24, 2], [1036,154 , 2],[1462, 1358, 2]])

            elif template == "7":
                coords = np.array([[21, 30, 2], [1033,470 , 2],[2027, 924, 2]])

            elif template == "8":
                coords = np.array([[24, 64, 2], [757,501 , 2],[1686,794, 2]])

            elif template == "9":
                coords = np.array([[26, 970, 2], [462,537 , 2],[1476,347, 2]])

            elif template == "10":
                coords = np.array([[13, 15, 3], [1433,458 , 2],[2330,963, 2]])

            elif template == "11":
                coords = np.array([[33, 202, 2], [871,200 , 2],[1523,290, 2],[1732,67, 2]])

            elif template == "12":
                coords = np.array([[73, 97, 2], [200, 1903, 3],[491, 49, 3], [423, 49, 3]])

            elif template == "13":
                coords = np.array([[398, 443, 4], [334, 1579, 2],[1785, 139, 2], [35, 108, 3]])

            elif template == "0":
                coords = np.array([[37, 431, 1], [1106, 870, 1],[1640, 1306, 1], [2310, 1342, 1]])

        else:
            dpoints = int(input('How many dpoints?:'))
            points = []
            for n in range(dpoints):
                coord = [int(input('insert x%s:'%(n+1))),int(input('insert y%s:'%(n+1))) ,int(input('insert bloc:'))]
                points.append(coord)
            coords = np.array(points)
        return coords

    def time_step(self):
        timestp = int(input("For which time steps? \nInsert either \n 0 for all of them or \n 1 for a specific time step range: "))

        if timestp == 0:
            a = 1
            b = self.model.get_nbresults()

        if timestp == 1:
            a = int(input("Please insert first the time step"))
            b = int(input("Please insert last the time step"))

        if timestp != 0 or timestp != 1:
            print("Sorry, that was neither 0 nor 1")
        return (a,b)

    def reader(self, dpoints:list=None, start_timestep:int=1, end_timestep:int=-1):
        """

        Args:
            dpoints (list, optional): Cooordinates list [[X1,Y1,block1], ..., [Xn,Yn,blockn]]
        """
        if dpoints is None:
            dpoints = self.coords()

        nb = self.model.get_nbresults()
        if start_timestep==-1:
            a,b = self.time_step()
        else:
            a = start_timestep
            b = end_timestep
            if b==-1:
                b=nb

        s = dpoints.shape
        datah = []
        datawl = []
        datafr = []
        datavabs= []

        for n in range(a,b+1):
            self.model.read_oneresult(n)
            #water depth
            h = [self.model.get_values_as_wolf(dpoints [i,0],dpoints [i,1],dpoints [i,2])[0]
                    for i in range(s[0])]
            datah.append(h)

            #water level
            wl = [self.model.get_values_as_wolf(dpoints [i,0],dpoints [i,1],dpoints [i,2])[7]
                    for i in range(s[0])]
            datawl.append(wl)

            #Absolute velocity
            vabs = [self.model.get_values_as_wolf(dpoints [i,0],dpoints [i,1],dpoints [i,2])[5]
                    for i in range(s[0])]
            datavabs.append(vabs)
            #Froude number
            fr = [self.model.get_values_as_wolf(dpoints [i,0],dpoints [i,1],dpoints [i,2])[6]
                    for i in range(s[0])]
            datafr.append(fr)
            print(('Result %s/%s')%(n,(b-a)+1))

        matrixh = np.array(datah)
        graph = matrixh.T

        matrixwl = np.array(datawl)
        graphwl = matrixwl.T

        matrixfr = np.array(datafr)
        graphfr = matrixfr.T

        matrixvabs = np.array(datavabs)
        graphvabs = matrixvabs.T


        #figure formats
        #plt.xkcd() #only for fun
        fig, ((f1,f4),(f2,f3)) = plt.subplots(2,2)
        #fig, (f1,f4,f2,f3) = plt.subplots(4) #another vision

        for n in range(matrixh.shape[1]):
            f1.plot(range(a,b+1,1),graph[n],
                linewidth=1,
                label='cell: bloc%s, x%s, y%s'%(dpoints[[n],[2]],dpoints[[n],[0]],dpoints[[n],[1]]))
        f1.legend(loc='upper right', framealpha=0.1, fontsize=7)
        f1.set(xlim=(a,b))
        f1.grid(visible=1, color= 'black', linewidth=0.2)
        f1.set(ylabel='Water height (m)')


        for n in range(matrixwl.shape[1]):
            f2.plot(range(a,b+1,1),graphwl[n],
                linewidth=1,
                label='cell: bloc: %s, x: %s, y:%s'%(dpoints[[n],[2]],dpoints[[n],[0]],dpoints[[n],[1]]))
        f2.legend(loc='upper right',framealpha=0.2, fontsize=7 )
        f2.set(xlim=(a,b))
        f2.set(ylabel='Water level (m)')
        f2.grid(visible=1, color= 'black', linewidth=0.1 )


        for n in range(matrixfr.shape[1]):
            f3.plot(range(a,b+1,1),graphfr[n],
                linewidth=1,
                label='cell: bloc: %s, x: %s, y:%s'%(dpoints[[n],[2]],dpoints[[n],[0]],dpoints[[n],[1]]))
        f3.legend(loc='upper right',framealpha=0.2, fontsize=7 )
        f3.set(xlim=(a,b))
        f3.grid(visible=1, color= 'black', linewidth=0.1 )
        f3.set(ylabel='Froude number')


        for n in range(matrixvabs.shape[1]):
            f4.plot(range(a,b+1,1),graphvabs[n],
                linewidth=1,
                label='cell: bloc: %s, x: %s, y:%s'%(dpoints[[n],[2]],dpoints[[n],[0]],dpoints[[n],[1]]))
        f4.legend(loc='upper right',framealpha=0.2, fontsize=7 )
        f4.set(xlim=(a,b))
        f4.grid(visible=1, color= 'black', linewidth=0.1 )
        f4.set(ylabel='Velocity (m/s)')

        plt.xlabel('Time steps')
        plt.tight_layout()
        plt.savefig( self.directory + '\Cells evolutions.png', format='png', dpi= 300)
        plt.show()

if __name__ =="__main__":
    t =Tracker()
    t.reader()
    print('done')
