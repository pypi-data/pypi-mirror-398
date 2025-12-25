"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
from wx.dataview import TreeListCtrl
from wx import dataview, StaticText, TextCtrl
from os.path import exists,join,splitext,dirname
from os import scandir, chdir, getcwd
import numpy as np
import subprocess

from ..PyTranslate import _
from ..wolfresults_2D import Wolfresults_2D
from .wolf2dprev import prev_infiltration
from ..wolf_array import WolfArray

CHECK_EXT=['.top', '.frot']
EXTRACT_IC = 'extract_results_mb'
RUN = 'run_wolf2d_prev'

class config_manager_2D:
    """
    Gestionnaire de configurations 2D
    """

    def __init__(self, workingdir = '', mapviewer = None) -> None:
        """
        Recherche de toutes les modélisation dans un répertoire et ses sous-répertoires
        """
        self.workingdir=''
        self.wolfcli=''

        if workingdir == '':
            dlg = wx.DirDialog(None,_('Choose directory to scan'),style = wx.FD_OPEN)
            ret = dlg.ShowModal()
            if ret != wx.ID_OK:
                dlg.Destroy()
                return
            workingdir = dlg.GetPath()
            dlg.Destroy()

        self.workingdir = workingdir
        self.mapviewer  = mapviewer

        self.configs = {}
        self.scan_wdir()
        self.find_sims()

        if mapviewer is not None:
            self.create_frame()
        else:
            self.txtctrl = None

        self.find_wolfcli(self.workingdir)

    def create_frame(self):

        self.myframe = wx.Frame(None,wx.ID_ANY,_('Configurations model WOLF2D'),)

        sizergeneral = wx.BoxSizer(wx.VERTICAL)
        sizergen = wx.BoxSizer(wx.HORIZONTAL)
        sizerprop = wx.BoxSizer(wx.VERTICAL)
        self.treelist = TreeListCtrl(self.myframe, style=dataview.TL_CHECKBOX)

        # self.treelist.Bind(wx.EVT_CHAR_HOOK, self.OnHotKey)
        # self.treelist.Bind(dataview.EVT_TREELIST_SELECTION_CHANGED,self.onselectitem)
        self.treelist.Bind(dataview.EVT_TREELIST_ITEM_CHECKED, self.OnCheckItem)
        self.treelist.Bind(dataview.EVT_TREELIST_ITEM_ACTIVATED, self.OnActivateTreeElem)
        # self.treelist.Bind(dataview.EVT_TREELIST_ITEM_CONTEXT_MENU, self.OntreeRight)


        self.root = self.treelist.GetRootItem()
        self.treelist.AppendColumn(_('2D Models'))
        self._append_item2tree(self.configs,self.root)

        self.txtctrl = TextCtrl(self.myframe, style=wx.TE_MULTILINE|wx.TE_BESTWRAP)

        self.checkconsistency = wx.Button(self.myframe,label = _('Check files consistency'))
        self.checkconsistency.Bind(wx.EVT_BUTTON,self.oncheckconsistency)

        self.launchsel = wx.Button(self.myframe,label = _('Launch selected models'))
        self.launchsel.Bind(wx.EVT_BUTTON,self.onlaunchmodelsel)
        self.launchall = wx.Button(self.myframe,label = _('Launch all models'))
        self.launchall.Bind(wx.EVT_BUTTON,self.onlaunchallmodel)

        self.extracticsel = wx.Button(self.myframe,label = _('Extract IC for selected models'))
        self.extracticsel.Bind(wx.EVT_BUTTON,self.onextracticsel)
        self.extracticall = wx.Button(self.myframe,label = _('Extract IC for all models'))
        self.extracticall.Bind(wx.EVT_BUTTON,self.onextracticall)

        self.choosewolfcli = wx.Button(self.myframe,label = _('Choose executable'))
        self.choosewolfcli.Bind(wx.EVT_BUTTON,self.onwolfcli)

        self.createzbin = wx.Button(self.myframe,label = _('Create surface elevation'))
        self.createzbin.Bind(wx.EVT_BUTTON,self.oncreatezbin)

        self.diffhbin = wx.Button(self.myframe,label = _('Difference in water depth IC'))
        self.diffhbin.Bind(wx.EVT_BUTTON,self.ondiffhbin)

        sizerprop.Add(self.checkconsistency,1,wx.EXPAND)
        sizerprop.Add(self.launchsel,1,wx.EXPAND)
        sizerprop.Add(self.launchall,1,wx.EXPAND)
        sizerprop.Add(self.extracticsel,1,wx.EXPAND)
        sizerprop.Add(self.extracticall,1,wx.EXPAND)
        sizerprop.Add(self.choosewolfcli,1,wx.EXPAND)
        sizerprop.Add(self.createzbin,1,wx.EXPAND)
        sizerprop.Add(self.diffhbin,1,wx.EXPAND)

        sizergen.Add(self.treelist,1,wx.EXPAND)
        sizergen.Add(sizerprop,1,wx.EXPAND)

        sizergeneral.Add(sizergen,1,wx.EXPAND)
        sizergeneral.Add(self.txtctrl,1,wx.EXPAND)

        self.myframe.SetSizer(sizergeneral)
        self.myframe.Layout()
        self.myframe.Centre(wx.BOTH)
        self.myframe.Show()

    def onwolfcli(self,e:wx.KeyEvent):
        self.find_wolfcli()

    def ondiffhbin(self,e:wx.KeyEvent):
        """
        Ajoute une matrice de différentiel entre 2 scénario d'une même simulation
        """
        mysims = self.get_genfiles()

        if len(mysims)>2:
            dlg = wx.MessageDialog(None,_('Too many selected simulations'))
            dlg.ShowModal()
            dlg.Destroy()
            return
        if len(mysims)<2:
            dlg = wx.MessageDialog(None,_('Too few selected simulations'))
            dlg.ShowModal()
            dlg.Destroy()
            return

        test_exists = exists(mysims[0] + '.hbin')
        test_exists &= exists(mysims[1] + '.hbin')

        if not test_exists:
            dlg = wx.MessageDialog(None,_('Check you IC files and Retry !'))
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlg = wx.SingleChoiceDialog(None, _('Choose the reference'), _('Choice of reference'), mysims)
        ret = dlg.ShowModal()
        ref = dlg.GetSelection()

        hbin=[]
        for cursim in mysims:
            hbin.append(WolfArray(cursim + '.hbin'))

        diff: WolfArray
        if ref==0:
            diff = hbin[1] - hbin[0]
        else:
            diff = hbin[0] - hbin[1]

        diff.mypal.default16()
        self.mapviewer.add_object('array', newobj=diff, id='difference src='+mysims[ref])

        # path = dirname(__file__)
        # fn = join(path, '..\\models\\diff16.pal')
        # if exists(fn):
        #     diff.mypal.readfile(fn)
        #     diff.mypal.automatic = False
        #     diff.myops.palauto.SetValue(0)

    def oncreatezbin(self,e:wx.KeyEvent):

        dlg = wx.MessageDialog(None,_('Do you want to work on all models ?'),style=wx.YES_NO)
        ret=dlg.ShowModal()
        if ret==wx.ID_YES:
            mysims = self.get_genfiles(True)
        else:
            mysims = self.get_genfiles()

        dlg.Destroy()

        dlg = wx.TextEntryDialog(None, _('Enter an epsilon on water depth [m]'),value='0.0')
        ret = dlg.ShowModal()

        eps=0.
        if ret == wx.ID_OK:
            eps = float(dlg.GetValue())

        dlg.Destroy()

        for cursim in mysims:

            curtop = WolfArray(cursim + '.topini_fine')
            curh = WolfArray(cursim + '.hbin')

            curh.array[curh.array<=eps]=0.
            curtop.array[curh.array<=eps]=0.

            curzbin = curh+curtop
            curzbin.filename = cursim + '.zbin'
            curzbin.write_all()

    def oncheckconsistency(self,e:wx.MouseEvent):

        mysims = self.get_genfiles(True)

        self.txtctrl.Clear()

        self.txtctrl.WriteText(_('References\n'))

        refs=[]
        for curext in CHECK_EXT:
            self.txtctrl.WriteText(mysims[0]+curext+'\n')
            refs.append(WolfArray(mysims[0]+curext))

        self.txtctrl.WriteText('\n')

        mysims.pop(0)

        whichdiff = ''
        for cursim in mysims:
            for curext,curref in zip(CHECK_EXT,refs):
                comp = WolfArray(cursim+curext)
                diff = comp-curref
                if np.count_nonzero(diff.array)>0 :
                    whichdiff += cursim + ' {} \n'.format(curext)

        if whichdiff=='':
            self.txtctrl.WriteText(_('All is fine !'))
        else:
            self.txtctrl.WriteText(whichdiff)

    def extract_ic_one(self,fn):

        olddir= getcwd()
        dirwolfcli =  dirname(self.wolfcli)
        chdir(dirwolfcli)

        pid = subprocess.run('wolfcli' + ' ' + EXTRACT_IC + ' in="{}" out="{}" format=0'.format(fn,fn), shell=True, encoding='cp1252')
        pid = subprocess.run('wolfcli' + ' ' + EXTRACT_IC + ' in="{}" out="{}" format=1'.format(fn,fn), shell=True, encoding='cp1252')

        chdir(olddir)

    def run_one(self,fn):

        args = RUN + ' genfile="{}"'.format(fn)
        # pid = subprocess.run(self.wolfcli + ' ' + args, capture_output=True,start_new_session=True)
        pass

    def onextracticsel(self,e:wx.MouseEvent):

        mysims = self.get_genfiles()
        for cursim in mysims:
            self.extract_ic_one(cursim)

    def onextracticall(self,e:wx.MouseEvent):

        mysims = self.get_genfiles(True)
        for cursim in mysims:
            self.extract_ic_one(cursim)

    def onlaunchmodelsel(self,e:wx.MouseEvent):
        mysims = self.get_genfiles()
        for cursim in mysims:
            self.run_one(cursim)

    def onlaunchallmodel(self,e:wx.MouseEvent):
        mysims = self.get_genfiles(True)
        for cursim in mysims:
            self.run_one(cursim)

    def get_genfiles(self,force=False):
        """ Get paths to all or selected simulations """
        genfiles=[]
        curitem = self.treelist.GetFirstItem()

        while curitem.IsOk():
            if self.treelist.GetItemText(curitem) == 'genfile':
                if self.treelist.GetCheckedState(curitem) == wx.CHK_CHECKED or force:
                    genfiles += [self.treelist.GetItemData(curitem)]
            curitem = self.treelist.GetNextItem(curitem)

        return genfiles


    def OnCheckItem(self,e):
        myitem = e.GetItem()
        ctrl = wx.GetKeyState(wx.WXK_CONTROL)
        myparent = self.treelist.GetItemParent(myitem)
        mydata = self.treelist.GetItemData(myitem)
        check = self.treelist.GetCheckedState(myitem)

        self._checkitem(myitem,check)

    def _checkitem(self,myitem,check):
        child = self.treelist.GetFirstChild(myitem)
        while child.IsOk():
            subchild = self.treelist.GetFirstChild(child)
            if subchild.IsOk():
                self._checkitem(child,check)

            self.treelist.CheckItem(child,check)
            child = self.treelist.GetNextSibling(child)


    def OnActivateTreeElem(self,e):
        myitem = e.GetItem()
        ctrl = wx.GetKeyState(wx.WXK_CONTROL)

        myparent = self.treelist.GetItemParent(myitem)
        mydata = self.treelist.GetItemData(myitem)
        check = self.treelist.GetCheckedState(myitem)

        nameparent = self.treelist.GetItemText(myparent).lower()
        nameitem = self.treelist.GetItemText(myitem).lower()

        if nameitem=='fil':
            mydata:prev_infiltration
            txt = _('Number of zones : {} \n'.format(mydata.nb_zones))
            for i in range(1,mydata.nb_zones+1):
                txt += _('Q zone {} : {} \n'.format(i,mydata._infiltrations_chronology[0][i]))

            self.txtctrl.Clear()
            self.txtctrl.WriteText(txt)
            self.myframe.Layout()

        if ctrl and (self.mapviewer is not None):
            #Ajout de la simulation à l'interface
            if nameitem == 'genfile':

                mywolf = Wolfresults_2D(mydata)
                mywolf.read_param_simul()
                mywolf.read_oneresult()

                myparentsup = self.treelist.GetItemParent(myparent)
                myid = self.treelist.GetItemText(myparentsup) + ' - ' + self.treelist.GetItemText(myparent)

                dlg = wx.TextEntryDialog(None, message=_('Set id'), value = myid)
                ret = dlg.ShowModal()

                newid = dlg.GetValue()
                if newid !='':
                    myid = newid

                self.mapviewer.add_object('res2d', newobj=mywolf, id=myid)
                self.mapviewer.menu_wolf2d()


    def _append_item2tree(self,curel,root):

        for idx, (k,v) in enumerate(curel.items()):
            if isinstance(v,dict):
                newroot = self.treelist.AppendItem(root,k, data=curel[k])
                self._append_item2tree(v,newroot)
            else:
                newroot = self.treelist.AppendItem(root,k,data = v)

    def scan_wdir(self):
        """
        Récupération de tous les répertoires et sous-répertoires
        et placement dans le dictionnaire self.configs
        """
        if self.workingdir !='':
            self._scan_dir(self.workingdir,self.configs)

    def find_sims(self):

        self._find_sims(self.configs,self.workingdir)

    def _scan_dir(self,wd:str,curdict:dict):

        for curel in scandir(wd):
            if curel.is_dir():
                newel=curdict[curel.name]={}
                self._scan_dir(curel,newel)

    def _find_sims(self,curdict:dict,keyname:str):

        if len(curdict.keys())>0:
            for i, (k, v) in enumerate(curdict.items()):
                self._find_sims(curdict[k],join(keyname,k))

        name = self._find_sim(keyname)
        if name is not None:
            curdict['genfile'] = name
            curdict['fil'] = prev_infiltration(None,name)
            curdict['fil'].read_file()

    def _find_sim(self,wd):
        for curel in scandir(wd):
            if curel.is_file():
                ext=splitext(curel)
                if len(ext[1])==0:
                    return join(wd,curel.name)

        return None

    def find_wolfcli(self,wd=''):

        self.wolfcli=''
        if wd!='':
            for curel in scandir(wd):
                if curel.is_file():
                    if "wolfcli" in curel.name:
                        self.wolfcli = join(wd,'wolfcli.exe')

        while not 'wolfcli' in self.wolfcli.lower():
            dlg = wx.FileDialog(None,_('Choose the wolf executable'), wildcard='Exe (*.exe)|*.exe',style = wx.FD_OPEN)
            ret = dlg.ShowModal()
            if ret != wx.ID_OK:
                dlg.Destroy()
                return
            self.wolfcli = dlg.GetPath()
            dlg.Destroy()

        if self.txtctrl is not None:
            self.txtctrl.Clear()
            self.txtctrl.WriteText(_('Found executable !\n') + self.wolfcli)

        return None
