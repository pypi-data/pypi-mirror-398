"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import ctypes
myappid = 'wolf_hece_uliege' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

#import des modules
from os import path
import sys
import wx
from pathlib import Path
from typing import Union

#Import des modules WOLF
from ..PyTranslate import _
from ..PyDraw import WolfMapViewer
from ..wolf_array import WolfArray

def main(mydir:Path=None, ListArrays:list[WolfArray]=None):
    """
    Comparaison de 2 cartes WOLF

    :param mydir : répertoire contenant 2 matrices WOLF (ref.bin et comp.bin) et leurs fichiers accompagant
    :param ListArrays : liste de 2 objets WolfArray
    """
    if mydir is not None:
        assert isinstance(mydir,Path), _('mydir must be a Path object')
        assert mydir.exists(), _('mydir must exist')
        fileref = Path(path.join(mydir,'ref.bin'))
        filecomp = Path(path.join(mydir,'comp.bin'))
        assert fileref.exists(), _('ref.bin not found in directory')
        assert filecomp.exists(), _('comp.bin not found in directory')
    if ListArrays is not None:
        assert isinstance(ListArrays,list), _('ListArrays must be a list')
        assert len(ListArrays)==2, _('ListArrays must contain 2 WolfArray objects')
        assert isinstance(ListArrays[0],WolfArray), _('ListArrays must contain 2 WolfArray objects')
        assert isinstance(ListArrays[1],WolfArray), _('ListArrays must contain 2 WolfArray objects')

    #Déclaration de l'App WX
    ex = wx.App()
    #Choix de la langue
    exLocale = wx.Locale()
    exLocale.Init(wx.LANGUAGE_ENGLISH)

    #Création de 3 fenêtres de visualisation basées sur la classe "WolfMapViewer"
    first = WolfMapViewer(None,'First',w=600,h=600)
    second = WolfMapViewer(None,'Second',w=600,h=600)
    third = WolfMapViewer(None,'Third',w=600,h=600)

    #Création d'une liste contenant les 3 instances d'objet "WolfMapViewer"
    mylist:list[WolfMapViewer]=[]
    mylist.append(first)
    mylist.append(second)
    mylist.append(third)

    #On indique que les objets sont liés en actiavt le Booléen et en pointant la liste précédente
    for curlist in mylist:
        curlist.linked=True
        curlist.linkedList=mylist

    if mydir is not None:
        #Création des matrices WolfArray sur base des fichiers
        mnt = WolfArray(path.join(mydir,'ref.bin'))
        mns = WolfArray(path.join(mydir,'comp.bin'))
    elif ListArrays is not None:
        mnt = ListArrays[0]
        mns = ListArrays[1]

    #Création du différentiel -- Les opérateurs mathématiques sont surchargés
    diff = mns-mnt

    #Ajout des matrices dans les fenêtres de visualisation
    first.add_object('array',newobj=mnt,ToCheck=True,id='reference')
    second.add_object('array',newobj=mns,ToCheck=True,id='comparison')
    third.add_object('array',newobj=diff,ToCheck=True,id='DIFF = comp-ref')

    #boucle infinie pour gérer les événements GUI
    ex.MainLoop()

if __name__=='__main__':
    """
    Gestion de l'éxécution du module en tant que code principal

    """
    # total arguments
    n = len(sys.argv)
    # arguments
    print("Total arguments passed:", n)
    assert n in [2,3], _('Usage : wolfcompare <directory> or wolfcompare <file1> <file2>')

    if n==2:
        mydir = Path(sys.argv[1])
        if mydir.exists():
            main(mydir)
        else:
            print(_('Directory not found'))
    elif n==3:
        file1 = Path(sys.argv[1])
        file2 = Path(sys.argv[2])

        if file1.exists() and file2.exists():
            main('', [WolfArray(file1), WolfArray(file2)])
        else:
            if not file1.exists():
                print(_('File {} not found'.format(file1)))
            if not file2.exists():
                print(_('File {} not found'.format(file2)))