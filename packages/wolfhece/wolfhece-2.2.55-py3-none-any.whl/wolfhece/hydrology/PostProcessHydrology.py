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
from numpy.testing._private.utils import measure

from .Catchment import *
from .Comparison import *
from ..wolf_array import *
from ..PyParams import*
from ..PyTranslate import _

class PostProcessHydrology(wx.Frame):


    directoryPath:str
    filename:str
    writeDir:str

    myCatchments:dict
    dictToCompare:dict
    myComparison:Comparison

    def __init__(self, parent=None, title="", w=500, h=500, postProFile=''):
        wx_exists = wx.App.Get()
        if wx_exists:
            super(PostProcessHydrology, self).__init__(parent, title=title, size=(w,h))

        self.directoryPath   = ""
        self.filename        = ""
        self.writeDir        = ""

        self.myCatchments = {}
        self.myComparison = {}
        self.dictToCompare = {}


        if postProFile=='':
            idir=wx.FileDialog(None,"Choose simulation file",wildcard='Fichiers de comparaison (*.compar)|*.compar|Fichiers post-processing (*.postPro)|*.postPro')
            if idir.ShowModal() == wx.ID_CANCEL:
                print("Post process cancelled!")
                sys.exit()
            self.filename = idir.GetPath()
            self.directoryPath = idir.GetDirectory() + "\\"
        else:
             self.filename = postProFile
             self.directoryPath = os.path.dirname(postProFile) + "\\"


        # if writeDir=='':
        #     idir=wx.DirDialog(None,"Choose writing file")
        #     if idir.ShowModal() == wx.ID_CANCEL:
        #         print("I'm here!")
        #         sys.exit()
        #     writeDir =idir.GetPath()+"\\"

        # Reading a compare file
        if(self.filename[-7:]==".compar"):
            # Reading of the input file 'Input.compar'
            paramsCompar = Wolf_Param(to_read=False,toShow=False)
            paramsCompar.ReadFile(self.filename)
            nbCatchment = int(paramsCompar.myparams['Main information']['nb catchment'][key_Param.VALUE])

            beginElement = 'Catchment '
            for i in range(1,nbCatchment+1):
                element = beginElement + str(i)
                self.myCatchments[element]={}
                self.myCatchments[element]['Title'] = paramsCompar.myparams[element]['name'][key_Param.VALUE]
                # Just check and correct the name of the filePath the way
                paramsCompar.myparams[element]['filePath'][key_Param.VALUE] = paramsCompar.myparams[element]['filePath'][key_Param.VALUE].replace("\\", "/")
                if not(paramsCompar.myparams[element]['filePath'][key_Param.VALUE].endswith('/')):
                    paramsCompar.myparams[element]['filePath'][key_Param.VALUE] = paramsCompar.myparams[element]['filePath'][key_Param.VALUE] + '/'
                dirName = paramsCompar.myparams[element]['filePath'][key_Param.VALUE]
                # Read the name of the input file
                try:
                    self.fileName = paramsCompar.myparams[element]['fileName'][key_Param.VALUE]
                except:
                    self.fileName = "Input.postPro"
                
                isOk,fileName = check_path(join(dirName,self.fileName), self.directoryPath)
                paramsCatchment = Wolf_Param(to_read=False, toShow=False)
                paramsCatchment.ReadFile(fileName)
                nameCatchment = paramsCatchment.myparams['Main information']['Name'][key_Param.VALUE]

                paramsCatchment.myparams['Main information']['directoryPath'][key_Param.VALUE] = paramsCatchment.myparams['Main information']['directoryPath'][key_Param.VALUE].replace("\\", "/")
                if not(paramsCatchment.myparams['Main information']['directoryPath'][key_Param.VALUE].endswith('/')):
                    paramsCatchment.myparams['Main information']['directoryPath'][key_Param.VALUE] = paramsCatchment.myparams['Main information']['directoryPath'][key_Param.VALUE] + '/'
                dirCatchment = paramsCatchment.myparams['Main information']['directoryPath'][key_Param.VALUE]

                isOk, dirCatchment = check_path(dirCatchment, prefix=self.directoryPath,applyCWD=True)
                if isOk<0:
                    print("ERROR : Problem in directory path!")

                try:
                    catchmentFileName = paramsCatchment.myparams['Main information']['Catchment file name'][key_Param.VALUE]
                except:
                    catchmentFileName = ""
                try:
                    rbFileName = paramsCatchment.myparams['Main information']['RB file name'][key_Param.VALUE]
                except:
                    rbFileName = ""
                try:
                    tz = int(paramsCatchment.myparams['Main information']['time zone'][key_Param.VALUE])
                except:
                    tz = 0

                if(int(paramsCatchment.myparams['Plot information']['plot all subbasin'][key_Param.VALUE]) == 1):
                    plotAllHydro = True
                else:
                    plotAllHydro = False
                if nbCatchment > 1:
                    isCompared = True
                else:
                    isCompared = True
                self.myCatchments[element]['Object'] = Catchment(nameCatchment, dirCatchment, plotAllHydro, isCompared, _catchmentFileName=catchmentFileName, _rbFileName=rbFileName, _tz=tz)
            if(nbCatchment>0):
                dictToCompare = paramsCompar.myparams['Plots']
                self.myComparison = Comparison(self.directoryPath, self.myCatchments, dictToCompare)
                self.myComparison.compare_now()

        elif(self.filename[-8:]=='.postPro'):
            self.myCatchments['Catchment 1']={}
            self.myCatchments['Catchment 1']['Title']=''
            paramsCatchment = Wolf_Param(to_read=False, toShow=False)
            paramsCatchment.ReadFile(self.filename)
            nameCatchment = paramsCatchment.myparams['Main information']['Name'][key_Param.VALUE]
            if(int(paramsCatchment.myparams['Plot information']['plot all subbasin'][key_Param.VALUE]) == 1):
                plotAllHydro = True
            else:
                plotAllHydro = False
            isCompared = False
            try:
                tz = int(paramsCatchment.myparams['Main information']['time zone'][key_Param.VALUE])
            except:
                tz = 0

            self.myCatchments['Catchment 1']['Object'] = Catchment(nameCatchment, self.directoryPath, plotAllHydro, _plotNothing=False, _tz=tz)

        else:
            print("ERROR: No valid input file found in this folder!")
            sys.exit()

        plt.show()

        print("That's all folks! ")




# When this module is run (not imported) then create the app, the
# frame, show it, and start the event loop.
if __name__ == '__main__':

    ex = wx.App()
    exLocale = wx.Locale()
    exLocale.Init(wx.LANGUAGE_ENGLISH)
    ex.MainLoop()

    myObj = PostProcessHydrology()
