"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

try:
    from cmath import isnan
    import numpy as np
    import wx
    import wx.lib.agw.aui as aui
    from shapely.geometry import LineString,Point
    from matplotlib import figure as mplfig
    import matplotlib.pyplot as plt
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas, NavigationToolbar2WxAgg as NavigationToolbar
    import logging
except ImportError as e:
    print(f"Import error: {e}")
    raise ImportError

try:
    from .PyCrosssections import profile,crosssections
    from .PyVertexvectors import Zones,zone,vector
    from .PyTranslate import _
    from .PyVertex import getIfromRGB,getRGBfromI, wolfvertex
except ImportError as e:
    print(f"Import error: {e}")
    raise ImportError

class PlotPanel(wx.Panel):
    """
    Un seul Panneau du notebook

    Plusieurs sizers :
        - sizerfig (horizontal) avec la figure en premier élément --> l'ajout se place à droite
        - sizer    (vertical) avec comme éléments sizerfig et la barre d'outils Matplotlib --> l'ajout se place en dessous
    """

    figure:mplfig.Figure

    def __init__(self, parent, id=-1, dpi=None,toolbar=True, **kwargs):

        self.wx_exists = wx.App.Get() is not None

        #Figure
        if self.wx_exists:
            self.figure = mplfig.Figure(dpi = dpi, figsize=(2,2))
        else:
            self.figure = plt.figure(dpi = dpi, figsize=(15,10))

        self.myax=None

        if self.wx_exists:
            super().__init__(parent, id=id, **kwargs)

            self.canvas = FigureCanvas(self, -1, self.figure)       #Création d'un Canvas wx pour contenir le dessin de la figure Matplotlib

            self.sizerfig = wx.BoxSizer(wx.HORIZONTAL)                        #ajout d'un sizer pour placer la figure et la barre d'outils l'une au-dessus de l'autre
            self.sizer = wx.BoxSizer(wx.VERTICAL)                        #ajout d'un sizer pour placer la figure et la barre d'outils l'une au-dessus de l'autre

            self.sizerfig.Add(self.canvas, 1, wx.EXPAND)                    #ajout du canvas
            self.sizer.Add(self.sizerfig, 1, wx.EXPAND)                    #ajout du canvas

            if toolbar:
                self.toolbar = NavigationToolbar(self.canvas)           #Ajout d'une barre d'outils pour la figure courante
                self.toolbar.Realize()
                self.sizer.Add(self.toolbar, 0, wx.LEFT| wx.EXPAND)         #ajout de la barre

            self.SetSizer(self.sizer)                                    #application du sizer

    def add_ax(self, ax3d=False) -> Axes:
        if ax3d:
            if self.myax is None:
                self.myax = self.figure.add_subplot(projection='3d')
        else:
            if self.myax is None:
                self.myax = self.figure.add_subplot()
        return self.myax

    def get_fig_ax(self, ax3d=False) -> tuple[Figure, Axes]:

        if self.myax is None:
            self.myax = self.add_ax(ax3d)

        return self.figure, self.myax

class PlotCS(PlotPanel):
    """
    Panels de traçage des sections en travers
    @author Pierre Archambeau
    """

    def __init__(self,
                 parent:aui.AuiNotebook,
                 id=-1,
                 dpi=None,
                 mycs:profile=None,
                 **kwargs):

        super().__init__(parent, id, dpi, **kwargs)

        self.mycs = mycs
        self.linked_arrays={}

        self.figsuppl = {}

        self.init_UI()

    def init_UI(self):

        if self.wx_exists:

            self.sizernextprev = wx.BoxSizer(wx.HORIZONTAL)                        #ajout d'un sizer pour placer la figure et la barre d'outils l'une au-dessus de l'autre
            self.sizerposbank = wx.BoxSizer(wx.HORIZONTAL)                        #ajout d'un sizer pour placer la figure et la barre d'outils l'une au-dessus de l'autre
            # self.sizerposbankbut = wx.BoxSizer(wx.HORIZONTAL)                        #ajout d'un sizer pour placer la figure et la barre d'outils l'une au-dessus de l'autre

            self.sizer.Add(self.sizernextprev,0,wx.EXPAND)
            self.sizer.Add(self.sizerposbank,0,wx.EXPAND)
            # self.sizer.Add(self.sizerposbankbut,0,wx.EXPAND)

            self.ButPrev = wx.Button(self,label=_("Previous"))
            self.ButNext = wx.Button(self,label=_("Next"))

            curs=5000
            self.slidergenhor = wx.Slider(self, wx.ID_ANY, curs, 0, 10000, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL,name='sliderhor' )
            self.slidergenver = wx.Slider(self, wx.ID_ANY, curs, 0, 10000, wx.DefaultPosition, wx.DefaultSize, wx.SL_VERTICAL,name='sliderver' )

            self.slidergenhor.SetToolTip(_("To shift Horizontal position of the section"))
            self.slidergenver.SetToolTip(_("To shift Vertical position of the section"))

            self.sizer.Add(self.slidergenhor,0,wx.EXPAND)
            self.sizerfig.Add(self.slidergenver,0,wx.EXPAND)

            self.sizernextprev.Add(self.ButPrev,1,wx.LEFT| wx.EXPAND)
            self.sizernextprev.Add(self.ButNext,1,wx.LEFT| wx.EXPAND)

            self.sizerslider1 = wx.BoxSizer(wx.VERTICAL)
            curs = 0
            self.sliderleft = wx.Slider(self, wx.ID_ANY, curs, 0, 10000, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL,name='sliderleft' )
            self.txtleft = wx.TextCtrl( self, wx.ID_ANY, str(curs), wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER|wx.TE_PROCESS_ENTER,name='textleft' )

            self.sliderleft.SetToolTip(_("To shift Left bank position of the section"))
            self.txtleft.SetToolTip(_("Curvilinear left bank position of the section [m]"))

            self.sizerslider1.Add( self.sliderleft, 1, wx.EXPAND)
            self.sizerslider1.Add( self.txtleft, 0, wx.EXPAND)
            self.sizerposbank.Add(self.sizerslider1,1,wx.EXPAND)

            self.sizerslider2 = wx.BoxSizer(wx.VERTICAL)
            curs = 0
            self.sliderbed = wx.Slider(self, wx.ID_ANY, curs, 0, 10000, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL,name='sliderbed' )
            self.txtbed = wx.TextCtrl( self, wx.ID_ANY, str(curs), wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER|wx.TE_PROCESS_ENTER,name='textbed' )

            self.sliderbed.SetToolTip(_("To shift Bed position of the section"))
            self.txtbed.SetToolTip(_("Curvilinear bed position of the section [m]"))

            self.sizerslider2.Add( self.sliderbed, 1, wx.EXPAND)
            self.sizerslider2.Add( self.txtbed, 0, wx.EXPAND)
            self.sizerposbank.Add(self.sizerslider2, 1, wx.EXPAND)

            self.sizerslider3 = wx.BoxSizer(wx.VERTICAL)
            curs = 0
            self.sliderright = wx.Slider(self, wx.ID_ANY, curs, 0, 10000, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL,name='sliderright' )
            self.txtright = wx.TextCtrl( self, wx.ID_ANY, str(curs), wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER|wx.TE_PROCESS_ENTER,name='textright' )

            self.sliderright.SetToolTip(_("To shift Right bank position of the section"))
            self.txtright.SetToolTip(_("Curvilinear right bank position of the section [m]"))

            self.sizerslider3.Add( self.sliderright, 1, wx.EXPAND)
            self.sizerslider3.Add( self.txtright, 0, wx.EXPAND)
            self.sizerposbank.Add(self.sizerslider3, 1, wx.EXPAND)

            self._sizer_shift_general = wx.BoxSizer(wx.HORIZONTAL)
            self._txt_zdatum = wx.TextCtrl(self, wx.ID_ANY, str(0), wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER|wx.TE_PROCESS_ENTER,name='textzdatum' )
            self._txt_zdatum.SetToolTip(_("Vertical shifting position of the section [m]"))
            self._txt_sdatum = wx.TextCtrl(self, wx.ID_ANY, str(0), wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER|wx.TE_PROCESS_ENTER,name='textsdatum' )
            self._txt_sdatum.SetToolTip(_("Horizontal shifting position of the section [m]"))

            self._sizer_shift_general.Add(self._txt_sdatum, 1, wx.EXPAND)
            self._sizer_shift_general.Add(self._txt_zdatum, 1, wx.EXPAND)

            self.sizer.Add(self._sizer_shift_general, 0, wx.EXPAND)

            self.txtbed.Bind(wx.EVT_TEXT_ENTER,self.movebanksslider)
            self.txtleft.Bind(wx.EVT_TEXT_ENTER,self.movebanksslider)
            self.txtright.Bind(wx.EVT_TEXT_ENTER,self.movebanksslider)
            self._txt_zdatum.Bind(wx.EVT_TEXT_ENTER,self.movegenslider)
            self._txt_sdatum.Bind(wx.EVT_TEXT_ENTER,self.movegenslider)

            self.sliderleft.Bind(wx.EVT_SLIDER,self.movebanksslider)
            self.sliderbed.Bind(wx.EVT_SLIDER,self.movebanksslider)
            self.sliderright.Bind(wx.EVT_SLIDER,self.movebanksslider)

            self.slidergenhor.Bind(wx.EVT_SLIDER,self.movegenslider)
            self.slidergenver.Bind(wx.EVT_SLIDER,self.movegenslider)

            self.ButPrev.Bind(wx.EVT_BUTTON,self.plot_up)
            self.ButNext.Bind(wx.EVT_BUTTON,self.plot_down)

    def set_linked_arrays(self,linked_arrays:dict):
        self.linked_arrays=linked_arrays

    def set_cs(self, mycs:profile, plot:bool = True):

        if self.mycs is not None:
            self.mycs.uncolor_active_profile()

        self.mycs = mycs

        self.mycs.color_active_profile()

        self.mycs.prepare()

        if self.wx_exists:

            sl,sb,sr,yl,yb,yr, sld,srd,yld,yrd = self.mycs.get_sz_banksbed()
            length = self.mycs.length3D

            if self.mycs.bankleft is not None:
                self.sliderleft.SetValue(int(sl/length*10000.))
                self.txtleft.SetLabelText(str(sl))
            else:
                self.sliderleft.SetValue(0)
                self.txtleft.SetLabelText(str(0))

            if self.mycs.bed is not None:
                self.sliderbed.SetValue(int(sb/length*10000.))
                self.txtbed.SetLabelText(str(sb))
            else:
                self.sliderbed.SetValue(5000)
                self.txtbed.SetLabelText(str(self.mycs.length3D/2.))

            if self.mycs.bankright is not None:
                self.sliderright.SetValue(int(sr/length*10000.))
                self.txtright.SetLabelText(str(sr))
            else:
                self.sliderright.SetValue(10000)
                self.txtright.SetLabelText(str(self.mycs.length3D))

            if self.mycs.add_zdatum:
                self._txt_zdatum.SetValue(str(self.mycs.zdatum))
            else:
                self._txt_zdatum.SetValue(str(0))

            if self.mycs.add_sdatum:
                self._txt_sdatum.SetValue(str(self.mycs.sdatum*10000./self.mycs.length3D))
            else:
                self._txt_sdatum.SetValue(str(0))

        if plot:
            self.plot_cs()

    def movegenslider(self,event):
        if self.mycs is None:
            return

        id = event.GetEventObject().GetName()
        cs:profile = self.mycs
        length = cs.length3D

        if id=='sliderhor':
            cs.sdatum = float(self.slidergenhor.Value-5000)/10000.*length
            cs.add_sdatum=True
            self._txt_sdatum.SetValue(str(cs.sdatum))

        elif id=='sliderver':
            cs.zdatum = -float(self.slidergenver.Value-5000)/1000.
            cs.add_zdatum=True
            self._txt_zdatum.SetValue(str(cs.zdatum))

        elif id=='textzdatum':
            try:
                cs.zdatum = float(self._txt_zdatum.Value)
                cs.add_zdatum=True
                self.slidergenver.SetValue(int(cs.zdatum*1000.)+ 5000)
            except ValueError:
                self._txt_zdatum.SetValue(str(cs.zdatum))
                logging.error("Invalid value for zdatum: %s", self._txt_zdatum.Value)
                return

        elif id=='textsdatum':
            try:
                cs.sdatum = float(self._txt_sdatum.Value)
                cs.add_sdatum=True
                self.slidergenhor.SetValue(int(cs.sdatum/length*10000.)+ 5000)
            except ValueError:
                self._txt_sdatum.SetValue(str(cs.sdatum))
                logging.error("Invalid value for sdatum: %s", self._txt_sdatum.Value)
                return

        if cs.prepared:
            cs.prepare()

        self.plot_cs()

    def movebanksslider(self,event:wx.Event):
        if self.mycs is None:
            return

        id = event.GetEventObject().GetName()
        cs:profile = self.mycs
        length = cs.length3D

        if id=='sliderleft':
            curs=float(self.sliderleft.Value)/10000.*length
            self.txtleft.SetValue("{0:.2f}".format(curs))
            cs.update_banksbed_from_s3d('left',curs)
        elif id=='sliderright':
            curs=float(self.sliderright.Value)/10000.*length
            self.txtright.SetValue("{0:.2f}".format(curs))
            cs.update_banksbed_from_s3d('right',curs)
        elif id=='sliderbed':
            curs=float(self.sliderbed.Value)/10000.*length
            self.txtbed.SetValue("{0:.2f}".format(curs))
            cs.update_banksbed_from_s3d('bed',curs)
        elif id=='textleft':
            curs=float(self.txtleft.Value)
            if curs<0.:
                self.txtleft.SetValue('0.')
                curs=0.
            elif curs>length:
                self.txtleft.SetValue(str(length))
                curs=length
            curslider = int(curs/length*10000.)
            self.sliderleft.SetValue(curslider)
            cs.update_banksbed_from_s3d('left',curs)
        elif id=='textright':
            curs=float(self.txtright.Value)
            if curs<0.:
                self.txtright.SetValue('0.')
                curs=0.
            elif curs>length:
                curs=length
                self.txtright.SetValue(str(length))
            curslider = int(curs/self.length*10000.)
            self.sliderright.SetValue(curslider)
            cs.update_banksbed_from_s3d('right',curs)
        elif id=='textbed':
            curs=float(self.txtbed.Value)
            if curs<0.:
                self.txtbed.SetValue('0.')
                curs=0.
            elif curs>length:
                self.txtbed.SetValue(str(length))
                curs=length
            curslider = int(curs/length*10000.)
            self.sliderbed.SetValue(curslider)
            cs.update_banksbed_from_s3d('bed',curs)

        self.plot_cs()

    def plot_cs(self):
        cs:profile = self.mycs

        fig=self.figure
        ax=self.myax

        sl,sb,sr,yl,yb,yr = cs.plot_cs(fig=fig, ax=ax, forceaspect=False, plotlaz=True, linked_arrays=self.linked_arrays)

        if cs.up is not None and cs.up is not cs:
            cs.up._plot_only_cs(fig=fig, ax=ax, style='dashdot', label=cs.up.myname, centerx=sb)
        if cs.down is not None and cs.down is not cs:
            cs.down._plot_only_cs(fig=fig, ax=ax, label=cs.down.myname, centerx=sb)

        fig.canvas.draw()

        cursup=1
        if cursup in self.figsuppl.keys():
            fig=self.figsuppl[cursup]['figure']
            ax=self.figsuppl[cursup]['ax']
            cs.plot_cs(fig=fig, ax=ax, linked_arrays=self.linked_arrays)
            fig.canvas.draw()

        cursup=2
        if cursup in self.figsuppl.keys():
            fig=self.figsuppl[cursup]['figure']
            ax=self.figsuppl[cursup]['ax']
            cs.plot_cs(fig=fig,ax=ax,forceaspect=False, linked_arrays=self.linked_arrays)
            fig.canvas.draw()

        cursup=3
        if cursup in self.figsuppl.keys():
            fig=self.figsuppl[cursup]['figure']
            ax=self.figsuppl[cursup]['ax']

            sl,sb,sr,yl,yb,yr=cs.plot_cs(fig=fig, ax=ax, forceaspect=False, plotlaz=True, linked_arrays=self.linked_arrays)

            if cs.up is not None and cs.up is not cs:
                cs.up._plot_only_cs(fig=fig,ax=ax,style='dashdot',label=cs.up.myname,centerx=sl+(sr-sl)/2.)
            if cs.down is not None and cs.down is not cs:
                cs.down._plot_only_cs(fig=fig,ax=ax,label=cs.down.myname,centerx=sl+(sr-sl)/2.)
            fig.canvas.draw()

        cursup=4
        if cursup in self.figsuppl.keys():
            fig=self.figsuppl[cursup]['figure']
            ax=self.figsuppl[cursup]['ax']
            sl,sb,sr,yl,yb,yr=cs.plot_cs(fig=fig, ax=ax, forceaspect=False, plotlaz=True, linked_arrays=self.linked_arrays)
            if cs.up is not None and cs.up is not cs:
                cs.up._plot_only_cs(fig=fig,ax=ax,style='dashdot',label=cs.up.myname,centerx=sl+(sr-sl)/2.,centery=yb)
            if cs.down is not None and cs.down is not cs:
                cs.down._plot_only_cs(fig=fig,ax=ax,label=cs.down.myname,centerx=sl+(sr-sl)/2.,centery=yb)
            fig.canvas.draw()

    def plot_up(self,event):

        if self.mycs.up is not None:
            self.set_cs(self.mycs.up)
            self.plot_cs()

    def plot_down(self,event):

        if self.mycs.down is not None:
            self.set_cs(self.mycs.down)
            self.plot_cs()
class ManagerInterp(PlotPanel):

    def __init__(self, parent, id=-1, dpi=None, **kwargs):

        super().__init__(parent, id, dpi, **kwargs)

        self.active_zones = None
        self.active_zone = None
        self.active_vec = None
        self.active_cs = None

        self.mapviewer = None

        self.fig_3D = None
        self.ax_3D = None

        self.sizernextprev = wx.BoxSizer(wx.HORIZONTAL)                        #ajout d'un sizer pour placer la figure et la barre d'outils l'une au-dessus de l'autre
        self.sizerposbank = wx.BoxSizer(wx.HORIZONTAL)                        #ajout d'un sizer pour placer la figure et la barre d'outils l'une au-dessus de l'autre
        self.sizertransfer = wx.BoxSizer(wx.HORIZONTAL)                        #ajout d'un sizer pour placer la figure et la barre d'outils l'une au-dessus de l'autre

        self.sizer.Add(self.sizernextprev,0,wx.EXPAND)
        self.sizer.Add(self.sizerposbank,0,wx.EXPAND)
        self.sizer.Add(self.sizertransfer,0,wx.EXPAND)

        self.ButPrev = wx.Button(self,label=_("Previous"))
        self.ButNext = wx.Button(self,label=_("Next"))

        self.tftHBG = wx.Button(self,label=_("Transfer to HBG"))
        self.tftHBD = wx.Button(self,label=_("Transfer to HBD"))
        self.tftTHA = wx.Button(self,label=_("Transfer to THA"))
        self.tftGarbage = wx.Button(self,label=_("Transfer to Garbage"))
        self.correctz = wx.Button(self,label=_("Apply correction on Z elevation"))
        self.transfernewzone = wx.Button(self,label=_("Create new supports..."))

        self.sizernextprev.Add(self.ButPrev,1,wx.LEFT| wx.EXPAND)
        self.sizernextprev.Add(self.ButNext,1,wx.LEFT| wx.EXPAND)

        self.sizerposbank.Add(self.correctz,1,wx.EXPAND)
        self.sizerposbank.Add(self.tftHBG,1,wx.EXPAND)
        self.sizerposbank.Add(self.tftTHA,1,wx.EXPAND)
        self.sizerposbank.Add(self.tftHBD,1,wx.EXPAND)
        self.sizerposbank.Add(self.tftGarbage,1,wx.EXPAND)

        self.sizertransfer.Add(self.transfernewzone,1,wx.EXPAND)

        self.ButPrev.Bind(wx.EVT_BUTTON,self.plot_up)
        self.ButNext.Bind(wx.EVT_BUTTON,self.plot_down)

        self.tftHBD.Bind(wx.EVT_BUTTON,self.hbd)
        self.tftHBG.Bind(wx.EVT_BUTTON,self.hbg)
        self.tftTHA.Bind(wx.EVT_BUTTON,self.tha)
        self.tftGarbage.Bind(wx.EVT_BUTTON,self.garbage)
        self.correctz.Bind(wx.EVT_BUTTON,self.corrz)

        self.transfernewzone.Bind(wx.EVT_BUTTON,self._transfernewzone)

    def pointing(self,gui,accs:crosssections,ac_vec:vector):
        self.mapviewer=gui
        self.active_cs=accs

        self.active_zones=accs.linked_zones

        if ac_vec.parentzone.parent is self.active_zones:
            self.active_zone = ac_vec.parentzone
            self.active_vec = ac_vec
            self.curidx = self.active_zone.myvectors.index(ac_vec)
        else:
            self.active_zone=self.active_zones.myzones[0]
            self.curidx = 0
            self.active_vec = self.active_zone.myvectors[self.curidx]

        self.create_struct()

        for curcs in self.active_cs.myprofiles.values():
            curprof:profile
            curprof = curcs['cs']
            curprof.prepare_shapely()

        self.plot_curvec()

    def create_struct(self):
        zonename=['THA','HBG','HBD','Garbage']

        self.active_zones.showstructure()

        self.tft={}
        act_zones= [cur.myname for cur in self.active_zones.myzones]

        for curname in zonename:
            if not curname in act_zones:
                added_zone = zone(name=curname,parent=self.active_zones)
                self.active_zones.add_zone(added_zone)
                self.tft[curname]=added_zone
            else:
                self.tft[curname]=self.active_zones.myzones[act_zones.index(curname)]

        self.active_zones.fill_structure()

    def tft_vec(self,zonename):
        curzone:zone
        curzone=self.tft[zonename]
        curzone.add_vector(self.active_vec)
        self.active_vec.parentzone = curzone

        curzone=self.active_zone
        curzone.myvectors.pop(self.curidx)

        self.active_zones.fill_structure()

        self.uncolor_acvec()

        if curzone.nbvectors>0:
            self.active_vec=curzone.myvectors[min(curzone.nbvectors-1,self.curidx)]
            self.plot_curvec()
        pass

    def color_acvec(self):
        curvec:vector
        curvec=self.active_vec

        curvec.myprop.color = getIfromRGB([255,0,0])
        curvec.myprop.width = 3
        self.mapviewer.zoomon_activevector()

    def uncolor_acvec(self):
        curvec:vector
        curvec=self.active_vec

        curvec.myprop.color = self.oldcol
        curvec.myprop.width = self.oldwidth

    def plot_curvec(self):

        curvec:vector
        curvec=self.active_vec

        self.oldcol = curvec.myprop.color
        self.oldwidth = curvec.myprop.width

        self.color_acvec()

        s,z = curvec.get_sz()

        self.myax.clear()
        self.ax_3D.clear()

        self.myax.set_title(curvec.myname)
        self.myax.plot(s,z)

        xyz=curvec.asnparray3d()
        self.ax_3D.plot(xyz[:,0],xyz[:,1],xyz[:,2])

        curvec.prepare_shapely()

        self.sprof=[]
        self.zprof=[]
        self.name=[]

        msg=''
        for curcs in self.active_cs.myprofiles.values():
            curprof:profile
            curprof = curcs['cs']


            if curvec.linestring.intersects(curprof.linestring):
                inter = curvec.linestring.intersection(curprof.linestring)
                if inter.geom_type=='MultiPoint':
                    inter=inter.geoms[0]
                    msg+='Bad intersection on section : '+curprof.myname +'\n'
                elif inter.geom_type=='GeometryCollection':
                    inter=inter.centroid
                    msg+='Bad intersection on section : '+curprof.myname+'\n'

                curs=curvec.linestring.project(inter)
                if curs==-1:
                    return
                else:
                    self.sprof.append(curs)
                    curz=curprof.interpolate(curprof.linestring.project(inter),is3D=False,adim=False).z
                    if np.isnan(curz):
                        curz=0.
                    self.zprof.append(curz)

                self.name.append(curprof.myname)

                xyz=curprof.asnparray3d()
                self.ax_3D.plot(xyz[:,0],xyz[:,1],xyz[:,2])
            else:
                inter = curprof.linestring.project(Point(curvec.myvertices[0].x,curvec.myvertices[0].y,curvec.myvertices[0].z))
                inter=curprof.interpolate(inter)
                msg+='Bad intersection on section : '+curprof.myname+'\n'

                self.sprof.append(curvec.linestring.project(Point(inter.x,inter.y,inter.z)))
                curz=curprof.interpolate(curprof.linestring.project(Point(inter.x,inter.y,inter.z)),is3D=False,adim=False).z
                if np.isnan(curz):
                    curz=0.
                self.zprof.append(curz)
                self.name.append(curprof.myname)

                xyz=curprof.asnparray3d()
                self.ax_3D.plot(xyz[:,0],xyz[:,1],xyz[:,2])

        if msg!='':
            dlg=wx.MessageBox(msg,'Required action')

        self.myax.scatter(self.sprof,self.zprof)

        for curx,cury,curname in zip(self.sprof,self.zprof,self.name):
            self.myax.text(curx,cury+.5,curname)

        self.myax.set_ylim([np.min([np.min(z),np.min(self.zprof)])-5.,np.max([np.max(z),np.max(self.zprof)])+5.])
        self.myax.set_xlim([0.,np.max(s)])

        self.figure.canvas.draw()
        self.fig_3D.canvas.draw()

    def tha(self,event):
        self.tft_vec('THA')

    def hbg(self,event):
        self.tft_vec('HBG')

    def hbd(self,event):
        self.tft_vec('HBD')

    def garbage(self,event):
        self.tft_vec('Garbage')

    def _transfernewzone(self,event):
        self.active_cs.create_zone_from_banksbed()

    def corrz(self,event):
        """Correction des altitudes du vecteur support"""

        #abscisse curvi du support
        curvec:vector
        curvec=self.active_vec
        s,z = curvec.get_sz()
        curls = curvec.asshapely_ls()

        #abscisse curvi combinées des sections et du support
        snew = np.unique(np.asarray(s.tolist() + self.sprof))

        ls = LineString(np.asarray([[s,z] for s,z in sorted(zip(self.sprof,self.zprof))]))

        #redécoupage du vecteur selon des nouvelles abscisses curvi
        curvec.myvertices=[]
        for curs in snew:
            mypt = curls.interpolate(curs)
            curvec.add_vertex(wolfvertex(mypt.x,mypt.y,mypt.z))

        s,z = curvec.get_sz()

        #recherche des altitudes
        decal = np.min(self.sprof)

        for i in range(curvec.nbvertices):
            if s[i]-decal<0.:
                newz = self.zprof[0]
            elif s[i]-decal>self.sprof[-1]:
                newz = self.zprof[-1]
            else:
                newz = ls.interpolate(s[i]-decal).y
            curvec.myvertices[i].z=newz

        self.plot_curvec()

    def plot_up(self,event):
        self.curidx-=1
        self.curidx=max(0,self.curidx)

        self.uncolor_acvec()

        if self.active_zone.nbvectors==0:
            return

        self.active_vec = self.active_zone.myvectors[self.curidx]
        self.plot_curvec()

        pass

    def plot_down(self,event):
        self.curidx+=1
        self.curidx=min(self.curidx,self.active_zone.nbvectors-1)

        self.uncolor_acvec()

        if self.active_zone.nbvectors==0:
            return

        self.active_vec = self.active_zone.myvectors[self.curidx]
        self.plot_curvec()
        pass

class PlotNotebook(wx.Panel):
    """
    Fenêtre contenant potentiellement plusieurs graphiques Matplotlib
    """

    def __init__(self, mapviewer = None, id=-1,show=True,framesize=(1024,768)):
        """Initialisation
         Si un parent est fourni, on l'attache, sinon on crée une fenêtre indépendante
        """
        self.frame = wx.Frame(None, -1, 'Plotter',size=framesize)
        super().__init__(self.frame, id=id)

        self.mapviewer=mapviewer
        self.ntb = aui.AuiNotebook(self)    #ajout du notebook
        sizer = wx.BoxSizer()               #sizer pour servir de contenant au notebook
        sizer.Add(self.ntb, 1, wx.EXPAND)   #ajout du notebook au sizer et demande d'étendre l'objet en cas de redimensionnement
        self.SetSizer(sizer)                #applique le sizer
        if show:
            self.frame.Show()

        self.Bind(wx.EVT_CLOSE , self.OnClose)
        self.Bind(wx.EVT_WINDOW_DESTROY , self.OnClose)

    def OnClose(self,event):
        if self.mapviewer is not None:
            try:
                self.mapviewer.notebookbanks = None #FIXME Pas très "propre" --> pour être plus général cela devrait être réalisé par un appel à une fonction callback qui pourrait être personnalisée
            except:
                pass

    def add(self, name="plot",which="") -> PlotPanel:
        """
        Ajout d'un onglet au notebook
        L'onglet contient une Figure Matplotlib
        On retourne la figure du nouvel onglet
        """

        if which=="":
            page = PlotPanel(self.ntb)               #crée un objet Plot
            self.ntb.AddPage(page, name)        #ajout de l'objet Plot au notebook

        elif which=="CS":

            nbsuppl=4

            pages=[]
            pagenames=[]

            pages.append(PlotCS(self.ntb))               #crée un objet Plot
            for i in range(nbsuppl):
                pages.append(PlotPanel(self.ntb) )              #crée un objet Plot

            pagenames.append(name)
            pagenames.append(name+_(' expand'))
            pagenames.append(name+_(' neighbors - bed centered'))
            pagenames.append(name+_(' neighbors - L/R centered'))
            pagenames.append(name+_(' neighbors - L/R centered and Z'))

            for page,myname in zip(pages,pagenames):
                self.ntb.AddPage(page, myname)        #ajout de l'objet Plot au notebook

            pages[0].add_ax()
            for i in range(1,nbsuppl+1):
                ax=pages[i].add_ax()
                pages[0].figsuppl[i]={}
                pages[0].figsuppl[i]['figure'] = pages[i].figure
                pages[0].figsuppl[i]['ax'] = ax
                pages[0].figsuppl[i]['figure'] = pages[i].figure

            page = pages[0]

        elif which=="ManagerInterp":
            page = ManagerInterp(self.ntb)               #crée un objet Plot
            page2 = PlotPanel(self.ntb)               #crée un objet Plot

            self.ntb.AddPage(page, name)        #ajout de l'objet Plot au notebook
            self.ntb.AddPage(page2, name+' 3D')        #ajout de l'objet Plot au notebook

            ax=page.add_ax()
            ax2=page2.add_ax(True)

            page.fig_3D = page2.figure
            page.ax_3D = ax2

        return page

    def getfigure(self,index = -1, caption="") -> mplfig.Figure:
        if index!=-1:
            return self.ntb.GetPage(index).figure
        elif caption!="":
            for curpage in range(self.ntb.GetPageCount()):
                if caption==self.ntb.GetPageText(curpage):
                    return self.ntb.GetPage(curpage).figure
            return
        else:
            return
