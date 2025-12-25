# Librairies
"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from cmath import isnan
import numpy as np
import wx
import wx.lib.agw.aui as aui
import copy
from shapely.geometry import LineString,Point
from matplotlib.figure import Figure
from matplotlib.axis import Axis
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas, NavigationToolbar2WxAgg as NavigationToolbar
from wx.grid import Grid
from PIL import Image
import logging

from .PyVertexvectors import Zones, vector, zone
from .PyCrosssections import profile,crosssections
from .PyVertexvectors import Zones,zone,vector
from .PyTranslate import _
from .PyVertex import getIfromRGB,getRGBfromI, wolfvertex
from .CpGrid import CpGrid
from .wolfresults_2D import Wolfresults_2D
from .PyWMS import getWalonmap


class ProfilePanel(wx.Panel):
    """
    A wx.panel on which the matplolib figure is displayed.
    """
    figure: Figure

    def __init__(self, parent, id =-1, dpi= None, toolbar = True, **kwargs):

        # test if wx App is running
        # if not, wx commands must be discarded
        self.wx_exists = wx.App.Get() is not None

        #Figure
        if self.wx_exists:
            self.figure = Figure(dpi = dpi, figsize=(8,4))
        else:
            self.figure = plt.figure(dpi = dpi, figsize=(15,10)) # FIXME not exactly the same than mplfig.Figure, probably rendering machine

        self.ax_cs_real= None
        self.ax_img= None
        self.ax_cs_anam = None
        self.ax_dis= None
        self.ax_hsw= None

        self.add_ax()
        # self.Layout()

        if self.wx_exists:
            # impossible to initialize wx.Panel if wx.App is not running
            super().__init__(parent,id =id, **kwargs)

            self.canvas = FigureCanvas(self,1, self.figure) #<-- wx.canvas for the matplolib figure
            self.canvas.ClearBackground()

            #Sizers
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.sizerfig = wx.BoxSizer(wx.HORIZONTAL)


            self.sizerfig.Add(self.canvas, 1, wx.EXPAND) #wx.EXPAND expands the given object proportions in case the windows is resized.
            self.sizer.Add(self.sizerfig, 7, wx.EXPAND)


            self.SetSizer(self.sizer)

    def add_ax(self):                                                   #Just in case a 3D projection is implemented
        """
        This methods creates the axes of the Matplolib figure either 3d or 2d (defaults = five 2D axes).
        """
        self.gs = self.figure.add_gridspec(2,3, wspace =0.35, hspace=0.35)   #Utilized to merge the 2 first axes of the figure (next line)
        self.ax_cs_real = self.figure.add_subplot(self.gs[0,:2])
        self.ax_img = self.figure.add_subplot(233)
        self.ax_cs_anam = self.figure.add_subplot(234)
        self.ax_dis = self.figure.add_subplot(235)
        self.ax_hsw = self.figure.add_subplot(236)

        self.ax_img.clear()
        self.ax_cs_anam.clear()
        self.ax_cs_real.clear()
        self.ax_dis.clear()
        self.ax_hsw.clear()

        return self.ax_cs_real, self.ax_img, self.ax_dis, self.ax_hsw

    def get_fig_ax(self) -> tuple[Figure, Axis, Axis, Axis, Axis, Axis]:
        """
        This method returns the active axes of the matplotlib figure.
        """
        return self.figure, self.ax_cs_real, self.ax_cs_anam, self.ax_img, self.ax_dis, self.ax_hsw



# class for plotting all figures at once
class PlotCSAll(ProfilePanel):
    """
    A class containing the necessary tools to draw the different graphs of a profile (Cross section).
    """
    def __init__(self,
                 parent:aui.AuiNotebook,
                 id=-1,
                 dpi=None,
                 my_cross_sections:crosssections = None,
                 my_profile:profile=None,
                 **kwargs):

        super().__init__(parent, id, dpi, **kwargs)

        self.compare = None

        self.grid_vertices = None
        self.grid_simulations = None

        self.parent = parent                                                    # aui.AuiNotebook

        self.my_cross_sections = my_cross_sections

        self.cs = 1
        self.wdepth = 0
        self.wlevel = 0
        self.minwlevel = 0
        self.maxwlevel = 10000000
        self.wdis = 0
        self.Manning = 0.04
        self.Strickler = 1/self.Manning
        self.slope = 0.001

        self.set_cs(my_profile)

        self.reset_models()
        self.init_UI()
        # self.Layout()

    def init_UI(self):
        """
        Init UI if wx.app is running
        Otherwise --> return
        """
        if not self.wx_exists:
            return

        #FIXME (Add a tool box for the figure or each specific axis legend)
        #Intialization of the panel tools --> FIXME (add water depth, level, discharges and slope message options)

        ##sizers
        self.sizernextprev = wx.StaticBoxSizer(wx.HORIZONTAL, self, label = _('Cross section (Selection)'))
        self.sizerposbank = wx.StaticBoxSizer(wx.HORIZONTAL,self, label = _('Geometric parameters'))
        self.sizerparam = wx.StaticBoxSizer(wx.HORIZONTAL,self, label = _('Hydraulic parameters'))
        self.sizerparam_box = wx.StaticBoxSizer(wx.HORIZONTAL,self, label = _('Parameters'))
        self.sizersimulations = wx.StaticBoxSizer(wx.HORIZONTAL,self, label = _('Additional tools'))


        ##Buton for changing cross section (FIXME add a Txtcontrol to jump on a specific cross section)
        self.cs = 1
        self.ButPrev = wx.Button(self, label =_('Previous'))
        self.ButNext = wx.Button(self,label =_('Next'))
        self.txtselectcs = wx.TextCtrl(self, wx.ID_ANY, str(self.cs), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name =_('textselectcs'))
        self.sizernextprev.Add(self.ButPrev,1, wx.LEFT|wx.EXPAND)
        self.sizernextprev.Add(self.ButNext,1,wx.LEFT|wx.EXPAND)
        self.sizernextprev.Add(self.txtselectcs,1,wx.LEFT|wx.EXPAND )
        #Tool tips
        self.ButPrev.SetToolTip(_("Previous profile if the cross sections are sorted."))
        self.ButNext.SetToolTip(_("Next profile if the cross sections are sorted."))
        self.txtselectcs.SetToolTip(_("Jump to the inserted profile."))

        ##General movements
        curs = 5000
        self.slidergenhor = wx.Slider(self, wx.ID_ANY, curs, 0, 1000, wx.DefaultPosition, wx.DefaultSize,  wx.SL_TOP|wx.SL_VALUE_LABEL, name=_('sliderhor'))
        self.txthor = wx.TextCtrl(self, wx.ID_ANY, str(curs), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = _('texthor'))
        self.slidergenver= wx.Slider(self, wx.ID_ANY, curs, 0, 10000, wx.DefaultPosition, wx.DefaultSize, wx.SL_LEFT|wx.SL_INVERSE|wx.SL_VALUE_LABEL,name=_('sliderver') )
        self.txtver = wx.TextCtrl(self, wx.ID_ANY, str(curs), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = _('textver'))
        self.sizerslider0= wx.StaticBoxSizer(wx.VERTICAL, self, label="V. mvt (mm)")
        self.sizerslider00= wx.StaticBoxSizer(wx.VERTICAL, self, label="H. mvt (mm)")
        #Tool tips
        self.slidergenhor.SetToolTip(_('This slider moves horizontally the whole current profile.'))
        self.slidergenver.SetToolTip(_('This slider moves vertically the whole current profile.'))
        self.txthor.SetToolTip(_('The input moves horizontally the whole current profile.'))
        self.txtver.SetToolTip(_('The input moves vertically the whole current profile.'))


        ###Vertical
        self.sizerslider0.Add(self.slidergenver,1, wx.ALIGN_CENTER)
        self.sizerslider0.Add(self.txtver,0, wx.ALIGN_CENTER)

        ###Horizontal
        self.sizerslider00.Add(self.slidergenhor,1,wx.ALIGN_CENTER)
        self.sizerslider00.Add(self.txthor,0,wx.ALIGN_CENTER)


        ##sliders and Text controls

        ### From the left side of the screen (1st box) --> Left bank
        self.sizerslider1 = wx.StaticBoxSizer(wx.VERTICAL, self, label = _('Left bank (mm)'))
        curs = 0
        self.sliderleft = wx.Slider(self, wx.ID_ANY, curs,0,10000, wx.DefaultPosition, wx.DefaultSize, wx.SL_TOP|wx.SL_VALUE_LABEL, name=_('sliderleft'))
        self.txtleft = wx.TextCtrl(self, wx.ID_ANY, str(curs), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = _('textleft'))
        self.sizerslider1.Add(self.sliderleft, 1, wx.ALIGN_CENTER)
        self.sizerslider1.Add(self.txtleft, 0, wx.ALIGN_CENTER)

        #Tool tips
        self.sliderleft.SetToolTip(_('This slider modifies the left bank position on the current profile.'))
        self.txtleft.SetToolTip(_('The input modifies the left bank position on the current profile.'))




        ### From left side of the screen (2nd box) --> river bed
        self.sizerslider2 =wx.StaticBoxSizer(wx.VERTICAL, self,label = _('River bed (mm)'))
        curs = 0
        self.sliderbed = wx.Slider(self, wx.ID_ANY, curs,0,10000, wx.DefaultPosition, wx.DefaultSize,  wx.SL_TOP|wx.SL_VALUE_LABEL, name=_('sliderbed'))
        self.txtbed = wx.TextCtrl(self, wx.ID_ANY, str(curs), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = _('textbed'))
        self.sizerslider2.Add(self.sliderbed, 1, wx.ALIGN_CENTER)
        self.sizerslider2.Add(self.txtbed, 0, wx.ALIGN_CENTER)
        #Tool tips
        self.sliderbed.SetToolTip(_('This slider modifies the river bed position on the current profile.'))
        self.txtbed.SetToolTip(_('The input modifies the river bed position on the current profile.'))




        ### From left side of the screen (3rd box) --> right bank
        self.sizerslider3 = wx.StaticBoxSizer(wx.VERTICAL, self, label =_('Right bank (mm)'))
        curs = 0
        self.sliderright = wx.Slider(self, wx.ID_ANY, curs,0,10000, wx.DefaultPosition, wx.DefaultSize,  wx.SL_TOP|wx.SL_VALUE_LABEL, name=_('sliderright'))
        self.txtright = wx.TextCtrl(self, wx.ID_ANY, str(curs), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name =_('textright'))
        self.sizerslider3.Add(self.sliderright,1, wx.ALIGN_CENTER)
        self.sizerslider3.Add(self.txtright, 0, wx.ALIGN_CENTER)
        #Tool tips
        self.sliderright.SetToolTip(_('This slider modifies the right bank position on the current profile.'))
        self.txtright.SetToolTip(_('The input modifies the right bank position on the current profile.'))



        ##Handling wx events with the class functions #FIXME  when done update by adding an underscore to these functions (they should not be callled in other scripts)

        ###Buttons
        self.ButPrev.Bind(wx.EVT_BUTTON, self.plot_up)
        self.ButNext.Bind(wx.EVT_BUTTON, self.plot_down)
        self.txtselectcs.Bind(wx.EVT_TEXT_ENTER, self.jump_to_cs)

        ###General movement of banks
        #Sliders
        self.slidergenhor.Bind(wx.EVT_SLIDER, self.movegenslider)
        self.slidergenver.Bind(wx.EVT_SLIDER, self.movegenslider)

        ###sliders and text controls
        ####Sliders
        self.sliderleft.Bind(wx.EVT_SLIDER, self.movebanksslider)
        self.sliderbed.Bind(wx.EVT_SLIDER, self.movebanksslider)
        self.sliderright.Bind(wx.EVT_SLIDER, self.movebanksslider)

        #### Text controls
        self.txtleft.Bind(wx.EVT_TEXT_ENTER, self.movebanksslider)
        self.txtbed.Bind(wx.EVT_TEXT_ENTER, self.movebanksslider)
        self.txtright.Bind(wx.EVT_TEXT_ENTER, self.movebanksslider)
        self.txthor.Bind(wx.EVT_TEXT_ENTER, self.movegenslider)
        self.txtver.Bind(wx.EVT_TEXT_ENTER, self.movegenslider)

        #### Hydro sliders
        #font = wx.Font( wx.FontInfo(10).Bold().Underline() ) FIXME (check about font and positions later)
        self.sizerslider4= wx.StaticBoxSizer(wx.VERTICAL, self, label=_("Water depth (m)"))
        self.sizerslider5= wx.StaticBoxSizer(wx.VERTICAL, self, label=_("Water level (m)"))
        self.sizerslider6= wx.StaticBoxSizer(wx.VERTICAL, self, label=_("Discharge (m^3/s)")) #FIXME Notation
        self.sizergeom =  wx.StaticBoxSizer(wx.VERTICAL, self, label= _("Other parameters"))

        ##### water depth

        self.wdepth = 0
        #self.wdepth_n= wx.StaticText(self, id = wx.ID_ANY,label="Water depth - h\n(mm)")
        #self.sizerslider4.Add(self.wdepth_n,0,wx.EXPAND)
        #box1 = wx.StaticBox(self, wx.ID_ANY, "Water Depth")
        #self.sizerslider4.Add(box1,0,wx.EXPAND)
        self.txtwdepth = wx.TextCtrl(self, wx.ID_ANY, str(self.wdepth), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = _('textwdepth'))
        self.txtwdepth.Bind(wx.EVT_TEXT_ENTER, self.movewaterdepth)
        self.sliderwdepth =   wx.Slider(self, wx.ID_ANY, self.wdepth, 0, 100000, wx.DefaultPosition, wx.DefaultSize, wx.SL_LEFT|wx.SL_INVERSE|wx.SL_VALUE_LABEL,name= _('sliderwdepth') )
        self.sizerslider4.Add(self.sliderwdepth,0, wx.ALIGN_CENTER)
        self.sliderwdepth.Bind(wx.EVT_SLIDER, self.movewaterdepth)
        self.sizerslider4.Add(self.txtwdepth,0,wx.CENTER|wx.EXPAND)
        #Tool tips
        self.sliderwdepth.SetToolTip(_('This slider adjusts the desired water depth on graphs.'))
        self.txtwdepth.SetToolTip(_('The input adjusts the desired water depth on graphs.'))




        ###### water level
        self.wlevel = 0
        self.minwlevel = 0
        self.maxwlevel = 10000000
        self.txtwlevel = wx.TextCtrl(self, wx.ID_ANY, str(self.minwlevel), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = _('textwlevel'))
        self.txtwlevel.Bind(wx.EVT_TEXT_ENTER, self.movewaterlevel)
        self.sliderwlevel =   wx.Slider(self, wx.ID_ANY, self.wlevel, self.minwlevel, self.maxwlevel, wx.DefaultPosition, wx.DefaultSize, wx.SL_RIGHT|wx.SL_INVERSE|wx.SL_VALUE_LABEL,name=_('sliderwlevel') )
        self.sizerslider5.Add(self.sliderwlevel,0,wx.ALIGN_CENTER)
        self.sliderwlevel.Bind(wx.EVT_SLIDER, self.movewaterlevel)
        self.sizerslider5.Add(self.txtwlevel,0,wx.ALIGN_CENTER)
        #Tool tips
        self.sliderwlevel.SetToolTip(_('This slider adjusts the desired water level on graphs.'))
        self.txtwlevel.SetToolTip(_('The input adjusts the desired water level on graphs.'))


        #####Discharges
        self.wdis = 0
        self.sliderwdis=   wx.Slider(self, wx.ID_ANY, self.wdis, 0., 10000, wx.DefaultPosition, wx.DefaultSize, wx.SL_TOP|wx.SL_VALUE_LABEL,name=_('sliderwdis') )
        self.txtwdis = wx.TextCtrl(self, wx.ID_ANY, str(self.wdis), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = _('textwdis'))
        self.txtwdis.Bind(wx.EVT_TEXT_ENTER, self.movewaterdis)
        self.sizerslider6.Add(self.sliderwdis,1, wx.ALIGN_CENTER)
        self.sliderwdis.Bind(wx.EVT_SLIDER, self.movewaterdis)
        self.sizerslider6.Add(self.txtwdis,0,wx.ALIGN_CENTER)
        #Tool tips
        self.sliderwdis.SetToolTip(_('This slider plots the desired discharge and its geometric characteristics on the 2 last graphs.'))
        self.txtwdis.SetToolTip(_('The input plots the desired discharge and its geometric characteristics on the 2 last graphs.'))



        ### Manning
        self.Manning = 0.04
        self.labelManning = wx.StaticText(self, wx.ID_ANY, _('Manning Coef.'))
        self.txtManning  =  wx.TextCtrl(self, wx.ID_ANY, str(self.Manning), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = 'textManning')
        self.txtManning.Bind(wx.EVT_TEXT_ENTER, self.compute_relations)
        self.sizergeom.Add(self.labelManning, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.sizergeom.Add(self.txtManning,0,wx.EXPAND)
        #Tool Tip
        self.txtManning.SetToolTip(_('The Manning coefficient modifies the friction values, and therefore, the plotted discharges.'))

        ### Strickler

        self.Strickler = 1/self.Manning
        self.labelStrickler = wx.StaticText(self, wx.ID_ANY, _('Strickler Coef.'))
        self.txtStrickler  =  wx.TextCtrl(self, wx.ID_ANY, str(self.Strickler), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = 'textStrickler')
        self.txtStrickler.Bind(wx.EVT_TEXT_ENTER, self.compute_relations)
        self.sizergeom.Add(self.labelStrickler, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.sizergeom.Add(self.txtStrickler,0,wx.EXPAND)
        #Tool Tip
        self.txtStrickler.SetToolTip(_('The Strickler coefficient modifies the friction values, and therefore, the plotted discharges.'))

        ### Slopes

        self.slope = 0.001
        self.labelslope = wx.StaticText(self, wx.ID_ANY, _('slope'))
        self.txtslope  =  wx.TextCtrl(self, wx.ID_ANY, str(self.slope), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name = _('textslope'))
        self.txtslope.Bind(wx.EVT_TEXT_ENTER, self.compute_relations)
        self.sizergeom.Add(self.labelslope, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.sizergeom.Add(self.txtslope,0,wx.EXPAND)
        #Tool tip
        self.txtslope.SetToolTip(_('Modify the profile discharges according to a chosen bed slope.'))


        #Other options
        self.Butprofvert =  wx.Button(self, label = _('Modify profile'))
        self.Butsimul = wx.Button(self, label = _('Wolf models data'))

        self.Butdrawprof = wx.Button(self, label = _('Draw on profile'))
        self.Butupdateprof = wx.Button(self, label = _('Refresh the drawings'))

        #self.Butprofvert_sz = wx.Button(self, label = _('Modify profile (SZ)'))



        self.sizersimulations.Add(self.Butsimul, 1, wx.EXPAND)
        self.sizersimulations.Add(self.Butprofvert,1,wx.EXPAND)
        self.sizersimulations.Add(self.Butdrawprof, 1, wx.EXPAND)
        #self.sizersimulations.Add(self.Butprofvert_sz,1,wx.EXPAND)
        self.sizersimulations.Add(self.Butupdateprof,1, wx.EXPAND)

        self.Butsimul.Bind(wx.EVT_BUTTON, self.simulations)
        #self.Butprofvert.Bind(wx.EVT_BUTTON, self.modify_vertex) #FIXME
        self.Butupdateprof.Bind(wx.EVT_BUTTON, self._draw_on_profile)
        # self.Butprofvert_sz.Bind(wx.EVT_BUTTON, self.modify_vertex_sz) #FIXME
        self.Butdrawprof.Bind(wx.EVT_BUTTON, self.add_zones)

        #Tool tip
        self.Butsimul.SetToolTip(_('Display the water level and discharges corresponding to the active wolf simulations.'))
        self.Butprofvert.SetToolTip(_('Create a new page where the profile displayed on Figure 1 can be modified and compared to itself.\
                                      \n A table containing its vertices and sz coordinate is also displayed)'))
        #self.Butprofvert_sz.SetToolTip(_('Display a table containing the profile characterisitcs in sz mode (only available in modification mode -> Options).'))
        self.Butupdateprof.SetToolTip(_('Update all modifications made on the profile'))
        self.Butdrawprof.SetToolTip(_('Draw additional information on the current profile (structures).'))

        #Sliders alignement (first added, first display (above))
        #Groups
        self.sizer.Add(self.sizernextprev, 0, wx.EXPAND)

        self.sizerparam_box.Add(self.sizerparam, 1, wx.LEFT|wx.EXPAND)
        self.sizerparam_box.Add(self.sizerposbank,1,wx.LEFT|wx.EXPAND)        #check the meaning of 0 and 1
        self.sizer.Add(self.sizerparam_box, 1, wx.EXPAND)

        self.sizer.Add(self.sizersimulations,0.9, wx.EXPAND)

        #Geometric
        self.sizerposbank.Add(self.sizerslider1,1, wx.EXPAND) #FIXME Positions of the boxsizer
        self.sizerposbank.Add(self.sizerslider2,1, wx.EXPAND) #FIXME Positions of the boxsizer
        self.sizerposbank.Add(self.sizerslider3,1,  wx.EXPAND) #FIXME Positions of the boxsizer
        self.sizerposbank.Add(self.sizerslider00,1,wx.EXPAND)
        self.sizerposbank.Add(self.sizerslider0,1,wx.EXPAND)


        #Hydro
        self.sizerparam.Add(self.sizerslider5,1,wx.EXPAND)
        self.sizerparam.Add(self.sizerslider4,1,wx.EXPAND)
        self.sizerparam.Add(self.sizerslider6,1,wx.EXPAND)
        self.sizerparam.Add(self.sizergeom,1,wx.EXPAND)

        #self.disprop = wx.StaticText(self,wx.ID_ANY,_('Critical characteristics: \n Hydraulic radius:%s \n wet area:%s \n Wet perimeter:%s \n Top Width:%s' % (cr_radius, cr_wetarea, cr_wetperimeter, cr_width)))
        #self.sizerslider6.Add(self.disprop,1, wx.ALIGN_CENTER)


        #Matplolib toolbar
        self.toolbar = NavigationToolbar(self.canvas)           #Ajout d'une barre d'outils pour la figure courante
        self.toolbar.Realize()
        self.sizer.Add(self.toolbar,0.9, wx.ALIGN_CENTER)
        self.SetAutoLayout(True)

    # Functions
    def set_cs(self, my_profile:profile=None, vec: list[vector] = [], Manning=0.04, plot=True) -> None:
        """
        This function sets the cross section (profile of interest in the list of cross sections provided as vectors) and
        initialise the slider positions as well as the values displayed on the wx panel.
        """
        if my_profile is None:
            self.mycs = None
            return # Nothing to do

        if self.mycs is not None:
            self.mycs.uncolor_active_profile(plot_opengl= False)

        my_profile.color_active_profile(plot_opengl= False)

        #Initialisation and reinitialisation of the plot parameters
        self.mycs = my_profile

        self.mycs.prepare() #Précalcule les relations sz...

        # Computations methods from Pycrossection.
        self.mycs.relations()
        if self.mycs.up and self.mycs.down:
            slup,slope_center,sld = self.mycs.slopes()
            self.set_Manning(Manning, slope_center)
        else:
            self.set_Manning(Manning)

        self.wlevel = self.mycs.zmin
        self.wdepth = 0
        self.wdis= 0

        self.vec:list[vector] = vec

        self.update_UI()

        # Modified to take into account the comparison of crossections.
        if plot:
            if self.compare is None:
                self.update_plots(True)
            elif self.compare is not None:
                self.update_plots()

    def update_UI(self, reset = True ):

        if not self.wx_exists:
            return

        ymax = self.mycs.zmax
        ymin = self.mycs.zmin

        self.minwlevel = ymin*10000
        self.maxwlevel = ymax*10000
        length = self.mycs.length3D

        self.sliderwlevel.SetMin(self.minwlevel)
        self.sliderwlevel.SetMax(self.maxwlevel)
        self.sliderwlevel.SetValue(self.minwlevel)
        self.sliderwdepth.SetMin(0)
        self.sliderwdepth.SetMax((ymax-ymin)*100000)
        self.sliderwdepth.SetValue(0)
        self.txtwlevel.SetLabel("{0:.3f}".format(self.minwlevel/10000))
        self.txtwdepth.SetValue("{0:.3f}".format(0))
        self.txtwdis.SetValue("{0:.3f}".format(0))

        self.txtManning.SetValue("{0:.3f}".format(self.Manning))
        self.txtStrickler.SetValue("{0:.3f}".format(1/self.Manning))

        self.sliderwdis.SetValue(self.wdis)
        self.txtwdis.SetValue("{0:.3f}".format(self.wdis))

        self.sliderleft.SetMax(10000*length)
        self.sliderbed.SetMax(10000*length)
        self.sliderright.SetMax(10000*length)
        self.slidergenhor.SetMax(10000*(length/2))
        self.slidergenhor.SetMin(-10000*(length/2))
        self.slidergenver.SetMax(50000)
        self.slidergenver.SetMin(-50000)
        self.slidergenhor.SetValue(0)
        self.slidergenver.SetValue(0)
        self.txthor.SetLabel("{0:.3f}".format(0))
        self.txtver.SetLabel("{0:.3f}".format(0))

        sl,sb,sr,yl,yb,yr, sld, srd, yld, yrd = self.mycs.get_sz_banksbed()

        # Banks (sliders positions and text control values).
        if self.mycs.bankleft is not None:
            self.sliderleft.SetValue((sl)*10000)
            self.txtleft.SetLabelText("{0:.3f}".format(sl))

        if self.mycs.bed is not None:
            self.sliderbed.SetValue((sb)*10000)
            self.txtbed.SetLabelText("{0:.3f}".format(sb))

        if  self.mycs.bankright is not None:
            self.sliderright.SetValue((sr)*10000)
            self.txtright.SetLabelText("{0:.3f}".format(sr))

        self.set_slope(newslope=self.slope, nManning=self.Manning) # FIXME (fixing bugs)

        self.sliderwdis.SetMax(self.qmax*10000)
        self.txtselectcs.SetValue(self.mycs.myname)

        if reset:
            self.zones = None
            # self.copy_nbvertices = None
            self.copy_vertices = None
            # added
            self.copy_compare_vertices = None
            # self.copy_compare_nbvertices = None

    def update_plots(self, update_image=False):
        #plots
        if update_image: self.mapviewer_activector()
        self.plot_profile()
        self.plot_discharge()
        self.plot_hspw()
        self.plot_cs()

    def mapviewer_activector(self):
        """
        This methods activates and colors the active profile in wolfhece.pydraw ,and therefore, in the wolfpy GUI too.
        """
        if self.mapviewer is not None:
            from wolfhece.PyDraw import WolfMapViewer
            self.mapviewer:WolfMapViewer

            ax3 = self.ax_img
            fig = self.figure
            # self.mapviewer.set_active_profile(self.mycs)   #We set the active profile in wolfhece.pydraw
            self.mapviewer.set_active_vector(self.mycs)    #To avoid visual confusions, we set the profile as the active vector in wolfhece.pydraw
            self.mycs.color_active_profile(plot_opengl= True)        #we thicken and color the profile in red.
            size = 200
            self.mapviewer.zoom_on_active_profile(size=size)    #We zoom on the profile in the gui.
            self.mapviewer.Paint()                             #We take the visual information in the GUI necessary for a screen shot.
            self.mapviewer.display_canvasogl(fig= fig, ax = ax3) #We return a clear screen shot of the wolfpy GUI as a matplolib graph (ax).
        else:
            self.mycs.color_active_profile(plot_opengl= False)

            bounds = self.mycs.get_bounds(100.)

            """
            FIXME find a way to better iterate over the different orthophotos
            orthos = {'IMAGERIE': {'1971': 'ORTHO_1971', '1994-2000': 'ORTHO_1994_2000',
                                '2006-2007': 'ORTHO_2006_2007',
                                '2009-2010': 'ORTHO_2009_2010',
                                '2012-2013': 'ORTHO_2012_2013',
                                '2015': 'ORTHO_2015', '2016': 'ORTHO_2016', '2017': 'ORTHO_2017',
                                '2018': 'ORTHO_2018', '2019': 'ORTHO_2019', '2020': 'ORTHO_2020',
                                '2021': 'ORTHO_2021', '2022 printemps': 'ORTHO_2022_PRINTEMPS', '2022 été': 'ORTHO_2022_ETE',
                               '2023 été': 'ORTHO_2023_ETE'}}
            """

            try:
                mybytes = getWalonmap(cat='IMAGERIE/ORTHO_2022_PRINTEMPS',xl = bounds[0][0], yl = bounds[0][1], xr = bounds[1][0], yr = bounds[1][1], w=500, h=500, tofile=False)
                image = Image.open(mybytes)
                self.ax_img.clear()
                self.ax_img.imshow(image, origin='upper', extent=(bounds[0][0],bounds[1][0],bounds[0][1],bounds[1][1]))
                self.ax_img.plot([self.mycs.myvertices[0].x, self.mycs.myvertices[-1].x], [self.mycs.myvertices[0].y, self.mycs.myvertices[-1].y], c='red', linewidth=3)
            except:
                pass

    def set_Manning(self, nManning:float, slope:float=-99999):
        if nManning>0:

            if slope>0.:
                self.slope=slope

            self.Manning = nManning
            self.Strickler = 1./nManning
            self.mycs.ManningStrickler_profile(slope= self.slope, nManning= self.Manning)

            return nManning
        else:
            return self.Manning

    def set_Strickler(self, kStrickler:float, slope:float=-99999):
        if kStrickler>0:

            if slope>0.:
                self.slope=slope

            self.Manning = 1./kStrickler
            self.Strickler = kStrickler
            self.mycs.ManningStrickler_profile(slope= self.slope, nManning= self.Manning)
            return kStrickler
        else:
            return self.Strickler

    def set_slope(self, newslope:float, nManning:float=-99999):
        if newslope>0:

            if nManning>0.:
                self.Manning=nManning

            self.slope = newslope
            self.qmax = self.mycs.ManningStrickler_profile(slope= self.slope, nManning= self.Manning)
            return newslope
        else:
            return self.slope

    def compute_relations(self, event: wx.Event):
        """
        This method computes the discharges based on a choosen friction coefficient (Manning or Strickler) and a slope.
        The computations are trigged by wx.Events (user's inputs in txt ctrl).
        """

        id = event.GetEventObject().GetName()

        if id == 'textManning':

            val= self.set_Manning(float(self.txtManning.Value))
            self.txtManning.SetValue("{0:.3f}".format(self.Manning))
            self.txtStrickler.SetValue("{0:.3f}".format(self.Strickler))

        elif id == 'textStrickler':

            val= self.set_Strickler(float(self.txtStrickler.Value))
            self.txtStrickler.SetValue("{0:.3f}".format(self.Strickler))
            self.txtManning.SetValue("{0:.3f}".format(self.Manning))

        elif id == 'textslope':

            val= self.set_slope(float(self.txtslope.Value))

            self.txtslope.SetValue("{0:.4f}".format(self.slope))

        self.plot_discharge()
        self.plot_hspw()
        self.plot_cs()

    def cs_setter(self, mycross: crosssections = None, active_profile : profile = None, compare : profile = None, mapviewer = None, plot=True):
        """
        This method sets simultaneously the cross section (mycross : parent) and the profile (active vector : child) active in wolf GUI or defined by the user.
        If no profile is given, the method returns the profile corresponding to the first key(string) in the cross section dictionary.
        Moreover, if a comparison profile (compare) is given, the methods sets that profile as the reference against which modifications on the active profile are compared.
        """

        #Initializations of the profile
        self.mapviewer = mapviewer                      #Pointing to WolfMapViewer (This establishes the communication between the 2 interfaces)
        self.my_cross_sections = mycross

        if compare is not None:
            self.compare = compare
            self.compare.prepare()

        elif compare is None:
            self.compare = None

        if active_profile is not None:
            self.set_cs(active_profile)
        else:
            key1 = next(iter(self.my_cross_sections.myprofiles))
            self.set_cs(self.my_cross_sections.myprofiles[key1]['cs'])

    def jump_to_cs(self, event: wx.Event):
        """
        Based on the user's input, the method jumps to the selected profile in the cross section.
        """
        id = event.GetEventObject().GetName()

        if id == 'textselectcs':
            index= str(self.txtselectcs.Value)
            keylist = list(self.my_cross_sections.myprofiles.keys())
            if index in keylist:
                val = self.my_cross_sections.myprofiles[index]['cs']
            else:
                index = keylist[0]
                val = self.my_cross_sections.myprofiles[index]['cs']

        self.set_cs(val)

    def movegenslider(self,event: wx.Event):
        """
        Using wx.Event, this methods moves (up or down, left or right) the whole river bed (banks and bed) displayed on the figure.
        """

        if self.mycs is None:
            return

        id = event.GetEventObject().GetName()
        cs:profile =self.mycs
        length = cs.length3D


        #Movemments of river bed
        # Sliders
        if id == 'sliderhor':
            sdatum = float(self.slidergenhor.Value)/10000
            cs.update_sdatum(sdatum)
            self.txthor.SetValue("{0:.3f}".format(cs.sdatum))

        elif id == 'sliderver':
            zdatum = float(self.slidergenver.Value)/10000.
            cs.update_zdatum(zdatum)
            self.txtver.SetValue("{0:.3f}".format(cs.zdatum))

        #Text controls
        elif id == 'texthor':
            curs = float(self.txthor.Value)
            if curs <= -(length/2):
                curs= -(length/2)

            elif curs >= (length/2):
                curs = (length/2)

            cs.update_sdatum(curs)

            self.slidergenhor.SetValue(10000*(curs))
            self.txthor.SetValue("{0:.3f}".format(curs))


        elif id == 'textver':
            curz = float(self.txtver.Value)
            if curz <= -5:
                curz= - 5

            elif curz >= 5:
                curz = 5

            cs.update_zdatum(curz)

            self.slidergenver.SetValue(10000*(curz))
            self.txtver.SetValue("{0:.3f}".format(curz))

        #Update of plots
        self.plot_profile()
        self.plot_cs()

    def movebanksslider(self, event: wx.Event):
        """
        This function updates a position of the river bank(left, bed, or right) based on the user's entry(sliding a slider or input of a float value).
        """
        #Intialization
        if self.mycs is None:
            return

        id = event.GetEventObject().GetName()
        cs:profile =self.mycs
        length = cs.length3D

        #Updates from sliders

        if id == 'sliderleft':
            curs = float(self.sliderleft.Value)/10000.
            self.txtleft.SetValue("{0:.3f}".format(curs))

            cs.update_banksbed_from_s3d('left', curs)

        elif id=='sliderbed':
            curs=float(self.sliderbed.Value)/10000.
            self.txtbed.SetValue("{0:.3f}".format(curs))

            cs.update_banksbed_from_s3d('bed', curs)

        elif id =='sliderright':
            curs = float(self.sliderright.Value)/10000.
            self.txtright.SetValue("{0:.3f}".format(curs))

            cs.update_banksbed_from_s3d('right', curs)

        #Updates from text controls
        elif id=='textleft':
            curs=float(self.txtleft.Value)

            if curs<0.:
                curs=0.
                self.txtleft.SetValue("{0:.3f}".format(curs))
                self.sliderleft.SetValue(curs*10000.)

            elif curs>length:
                curs=length
                self.txtleft.SetValue("{0:.3f}".format(curs))
                self.sliderleft.SetValue(curs*10000.)

            curslider = curs*10000.
            self.sliderleft.SetValue(curslider)

            cs.update_banksbed_from_s3d('left', curs)

        elif id=='textbed':
            curs=float(self.txtbed.Value)

            if curs<0.:
                curs=0.
                self.txtbed.SetValue("{0:.3f}".format(curs))
                self.sliderbed.SetValue(curs*10000.)

            elif curs>length:
                curs=length
                self.txtbed.SetValue("{0:.3f}".format(length))
                self.sliderbed.SetValue(curs*10000.)

            curslider = curs*10000.
            self.sliderbed.SetValue(curslider)

            cs.update_banksbed_from_s3d('bed', curs)

        elif id =='textright':
            curs = float(self.txtright.Value)

            #Safelock for negative distance (limits of the cross section)
            if curs < 0:
                curs = 0.
                self.txtright.SetValue("{0:.3f}".format(curs))
                self.sliderright.SetValue(curs*10000.)


            #Safelock for a distance beyond the crossection's length
            elif curs > length:
                curs = length
                self.txtright.SetValue("{0:.3f}".format(length))
                self.sliderright.SetValue(curs*10000.)


            curslider = curs*10000.
            self.sliderright.SetValue(curslider)

            cs.update_banksbed_from_s3d('right', curs)

        self.plot_profile()
        self.plot_cs()

    def movewaterdepth(self, event: wx.Event):
        """
        This method increases or decreases the water depth plotted on graphs.
        """
        if self.mycs is None:
            return

        id = event.GetEventObject().GetName()

        ymin = self.mycs.zmin
        ymax = self.mycs.zmax

        if id == 'sliderwdepth':
            val = float(self.sliderwdepth.Value)/100000

            if val + ymin > ymax:
                self.wdepth = ymax-ymin
                self.wlevel = self.wdepth + ymin

            else:
                self.wdepth = val
                self.wlevel = self.wdepth + ymin


        elif id== 'textwdepth':
            val = float(self.txtwdepth.Value)

            if val + ymin <= ymin:
                self.wdepth = 0.
                self.wlevel = self.wdepth + ymin

            elif val + ymin > ymax:                       #FIXME (Is this limit realistic for all possible cases?)
                self.wdepth = ymax-ymin
                self.wlevel = self.wdepth + ymin

            else:
                self.wdepth = val
                self.wlevel = self.wdepth + ymin

            self.sliderwdepth.SetValue(self.wdepth*100000)

        self.txtwdepth.SetValue("{0:.3f}".format(self.wdepth))
        self.txtwlevel.SetValue("{0:.3f}".format(self.wlevel))
        self.sliderwlevel.SetValue(self.wlevel*10000)

        #Plots
        self.update_plots()

    def movewaterlevel(self, event: wx.Event):
        """
        This method increases or decreases the water level plotted on graphs.
        """

        if self.mycs is None:
            return

        ymin = self.mycs.zmin
        ymax = self.mycs.zmax

        id = event.GetEventObject().GetName()

        if id == 'sliderwlevel':
            val = (float(self.sliderwlevel.Value))/10000
            self.wlevel =val
            self.wdepth = (self.wlevel - ymin)

        elif id == 'textwlevel':
            val = float(self.txtwlevel.Value)
            if val <= ymin:
                self.wlevel = ymin
                self.wdepth = 0


            elif val > ymax:                    #FIXME (Is this limit realistic for all possible cases?)
                self.wlevel = ymax
                self.wdepth = (self.wlevel - ymin)

            else:
                self.wlevel = val
                self.wdepth = self.wlevel - ymin

            self.sliderwlevel.SetValue(self.wlevel*10000)


        self.txtwlevel.SetValue("{0:.3f}".format(self.wlevel))
        self.txtwdepth.SetValue("{0:.3f}".format(self.wdepth))
        self.sliderwdepth.SetValue(self.wdepth*100000)

        self.update_plots()

    def movewaterdis(self, event: wx.Event):
        """
        This method selects and plots a specific discharges in the GUI based on the user's input.
        """

        if self.mycs is None:
            return
        id = event.GetEventObject().GetName()

        if id == 'sliderwdis':
            val= float(self.sliderwdis.Value)/10000
            self.wdis = val


        elif id == 'textwdis':
            val = float(self.txtwdis.Value)
            if val <= 0:
                self.wdis = 0

            elif val > self.qmax:                    #FIXME
                self.wdis = self.qmax

            else:
                self.wdis = val

        self.txtwdis.SetValue("{0:.3f}".format(self.wdis))
        self.sliderwdis.SetValue(self.wdis*10000)

        self.plot_discharge()
        self.plot_hspw()
        self.plot_cs()

    def plot_profile(self, figax:tuple[Figure, Axis] = None):
        """
        This method plots the geometric profiles on the first and third graph.
        The third graph is anamorphosed to allow comparisons with other graphs using the same scale.
        """
        cs:profile = self.mycs

        if figax is None:
            fig = self.figure
            ax1 = self.ax_cs_real
            ax4 = self.ax_cs_anam
        else:
            fig, ax1=figax
            ax4=None

        #The profile
        sl,sb,sr,yl,yb,yr=cs.plotcs_profile(fig = fig,
                                            ax = ax1,
                                            vecs = self.vec ,
                                            compare = self.compare,
                                            fwd=self.wdepth,
                                            fwl=self.wlevel,
                                            simuls = self.models,
                                            forceaspect = True,
                                            plotlaz=True)

        #The neighbouring profiles (up and down)
        if cs.up is not None and cs.up is not cs:
            cs.up._plot_only_cs(fig=fig,
                                ax=ax1,
                                style='dashed',
                                label=cs.up.myname,
                                centerx=sb)

        if cs.down is not None and cs.down is not cs:
            cs.down._plot_only_cs(fig=fig,
                                  ax=ax1,
                                  style='dotted',
                                  label=cs.down.myname,
                                  centerx=sb)

        if ax4 is not None:
            # The anamorphosed view
            sl,sb,sr,yl,yb,yr=cs.plotcs_profile(fig = fig,
                                                ax = ax4,
                                                vecs = self.vec ,
                                                simuls = self.models,
                                                fwd =self.wdepth,
                                                fwl=self.wlevel,
                                                forceaspect = False,
                                                plotlaz=True)

        #Legends
        leg1 = ax1.legend(bbox_to_anchor = (0.,0.9, 1.1,0.2),
                          ncol= 4, mode = 'expand',
                          fontsize= 'xx-small',
                          markerscale = 0.5,
                          borderaxespad=-1.05)
        if self.wx_exists:
            leg1.set_draggable(True) #For legend displacements #FIXME

        leg4 = ax4.legend(bbox_to_anchor = (0.,0.9, 1.1,0.2),
                          ncol= 4,
                          mode = 'expand',
                          fontsize= 'xx-small',
                          markerscale = 0.5,
                          borderaxespad=-1.05)
        if self.wx_exists:
            leg4.set_draggable(True)

    def plot_discharge(self, figax:tuple[Figure, Axis] = None):
        """
        This method plots the discharge relationships of the active profile on the 5th axis of the matplotlib figure.
        """

        if figax is None:
            fig = self.figure
            ax5 = self.ax_dis
        else:
            fig,ax5 = figax
        labels = False

        #graphs
        self.mycs.plotcs_discharges(fig = fig,
                                    ax = ax5,
                                    fwl=self.wlevel,
                                    fwd = self.wdepth,
                                    fwq = self.wdis,
                                    labels= labels,
                                    simuls=self.models)

        #Legend
        leg5 = ax5.legend(bbox_to_anchor = (0.,0.95, 1.1,0.2),
                          ncol= 4, mode = 'expand',
                          fontsize= 'xx-small',
                          markerscale = 0.5,
                          borderaxespad=-1.05)
        if self.wx_exists:
            leg5.set_draggable(True)

    def plot_hspw(self, figax:tuple[Figure, Axis] = None):
        """
        The methods plots the hydraulic radius - H, the wetted area - S, the wetted perimeter - P and top width - W on sixth axis and last graph of the figure.
        """
        if figax is None:
            fig = self.figure
            ax6 = self.ax_hsw
        else:
            fig, ax6 = figax

        labels = False
        self.mycs.plotcs_hspw(fig= fig,
                              ax = ax6,
                              fwl=self.wlevel,
                              fwd = self.wdepth,
                              fwq = self.wdis,
                              labels= labels)

        leg6 = ax6.legend(bbox_to_anchor = (0.,0.95, 1.1,0.2),
                          ncol= 4, mode = 'expand',
                          fontsize= 'xx-small',
                          markerscale = 0.5,
                          borderaxespad=-1.05)
        if self.wx_exists:
            leg6.set_draggable(True)

    def plot_cs(self):
        """
        This method plots 6 matplotlib graphs of the active profile.
        In order to do so, it uses the stored self graphs defined by other plotting methods.
        Storing the graphs avoid unnecessary repetitions of plots each time the method is called.
        """
        fig = self.figure

        fig.suptitle('Cross section - %s'%(self.mycs.myname), size=15)
        self.gs.tight_layout(fig)
        #fig.tight_layout()

        if self.wx_exists:
            self.canvas.draw()
        else:
            fig.canvas.draw()

    def plot_up(self, event: wx.Event):
        """
        This function plots the upstream's cross section by upgrading the current cross section with the next upstream.
        """
        if self.mycs.up is None:
            return

        self.mycs.uncolor_active_profile(plot_opengl= False)
        self.set_cs(self.mycs.up)
        self.plot_cs()

    def plot_down(self,event: wx.Event):
        """
        This function plots the downstream's cross section by upgrading the current cross section with the next downsrtream.
        """
        if self.mycs.down is None:
            return

        self.mycs.uncolor_active_profile(plot_opengl= False)
        self.set_cs(self.mycs.down)
        self.plot_cs()

    def add_model(self, newsim):
        """Add a new sim to the sims dictionnary"""
        self.models.append(newsim)

    def reset_models(self):
        """Reset the sims dictionnary"""
        self.models=[]

    def simulations(self, event: wx.Event):
        """
        This method displays on the profile and on the discharge graphs, the hydraulic characteristics in the numerical simulations.
        Also, it triggers a new window containing a table (grid) of the displayed values.
        FIXME add a plot method for 2D and 1D results.
        """
        # Data from numerical simulations

        # Set 'Model Key','Discharge','Water depth','Water level'

        if self.grid_simulations is None:
            self.models=[]

            for curkey, cursim in self.sims.items():

                ds = cursim.get_dxdy_min()

                pts = self.mycs._refine2D(ds/2.)

                allz = [cursim.get_value(curpt.x, curpt.y, nullvalue=-99999) for curpt in pts]

            self.models = np.array([['Q25',250.5, 2,76],['Q50',500,3,77], ['Q100',800,4,78],['Q1000',1500,5,79.2]])

            # Calling the grid's class and displaying as well as getting the data from its table (FIXME: Safety for future improvements)

            self.grid_simulations = windowsgrid(parent=None)
            self.grid_simulations.set_grid_sims(models = self.models,
                                                            title = 'C.S.- %s'%(self.mycs.myname))

            self.plot_profile()
            self.plot_discharge()
            self.plot_cs()
        else:
            self.grid_simulations.Show()

    def _update_sims(self):

        self.models = np.asarray(list(self.grid_simulations.get_vals_sims()))
        self.grid_simulations = None

    def modify_vertex(self):
        """
        This method displays a new window containing the vertices of the active cross sections for modifications.
        """
        if self.compare is not None:

            if self.grid_vertices is None:
                self.grid_vertices = windowsgrid(parent=None)
                self.grid_vertices.set_grid_vert(my_profile =self.mycs,
                                            ref = self.compare,
                                            title= 'C.S.- %s'%(self.mycs.myname),
                                            callback= self._update_profile_callback,
                                            call1 = self.update_profile,
                                            call2 = self.update_profile_from_sz)
                self.grid_vertices.Show()

            else:
                self.grid_vertices.Show()

    def show_vertices(self, event: wx.Event):
        self.modify_vertex()

    def update_profile(self,event: wx.Event):
        """
        This method allows the update of the profile plot
        - if the profile vertices are modified or
        - or if a structure is drawn (projected) on the profile.
        """
        self._reset_profile_vertices()
        if self.compare is not None and self.grid_vertices is not None:
            self.mycs.updatefromgrid(gridfrom = self.grid_vertices.profile_xls)

        self._update_drawings()

    def _reset_profile_vertices(self):
        if self.copy_vertices: # and self.copy_nbvertices:
            self.mycs.myvertices = self.copy_vertices
            # added
            self.compare.myvertices = self.copy_compare_vertices

    def update_profile_from_sz(self, event:wx.Event):
        """
        Mise à jour depuis un CpGrid
        """
        self._reset_profile_vertices()
        curv:wolfvertex
        gridfrom = self.grid_vertices.profile_xls

        nbl=gridfrom.GetNumberRows()
        k=0
        S=[]
        Z =[]

        while k<nbl:
            z=gridfrom.GetCellValue(k,2)
            s=gridfrom.GetCellValue(k,4)

            if z=='':
                z=0.

            if s!='':
                S.append(float(s))
                Z.append(float(z))
                k+=1

            elif s=='':
                break

            else:
                raise Exception(_("Recheck your sz data"))
                break

        sz = np.array([S,Z])
        length_compare = self.compare.asshapely_ls()
        vertices = []
        nbv = 0

        for i in range(len(sz[0])) :
            coords  = length_compare.interpolate(sz[0][i])
            curv = wolfvertex(coords.x, coords.y, sz[1][i])
            vertices.append(curv)
            nbv += 1

        self.mycs.reset_prepare()
        self.mycs.myvertices=vertices

        self._update_drawings()

    def _update_profile_callback(self):
        self.mycs.updatefromgrid(gridfrom = self.grid_vertices.profile_xls)
        self.grid_vertices = None

    def project_zones_on_trace(self, new_zones:Zones = None, reset_vec=True):

        if new_zones is None:
            return

        if reset_vec:
            self.vec=[]

        for zone in new_zones.myzones:
            for vec in zone.myvectors:
                if vec.myprop.used:
                    self.add_vec(vec= vec)

    def add_vec(self, vec: vector, reset_first=False):
        """
        This method projects a vector on the profile traces and
        appends the projection to the list utilised to plot the structures.
        """
        if reset_first:self.vec=[]

        curvec:vector = vec.projectontrace(self.mycs)
        self.vec.append(curvec)

    def populate_xy_from_sz(self):
        """
        This method populate xy colum based on s and z entries.
        """
        self.Butgetxy_fromsz =wx.Button(self, label = _('Get xy from sz'))
        self.zones.xls

    def add_zones(self, event: wx.Event):
        """
        This method creates a new zones and displays its structure on the screen.
        """
        # self.zones: Zones
        if self.zones:

            for i in range(self.zones.nbzones):
                for vec in self.zones.myzones[i].myvectors:
                    self.zones.evaluate_s(vec= vec, dialog_box=False)
            self.zones.showstructure()

        else:
            self.zones = Zones(parent = self.mapviewer)
            self.zones.showstructure()

    def _update_drawings(self):
        if self.compare is not None and self.grid_vertices is not None:
            self.harmonize_profiles()
            self.mycs.prepare()
            #self.zones = Zones(parent = self.mapviewer) # Added to avoid bug in wolfpy

        if self.compare is not None and self.grid_simulations is not None:
            self.models = np.asarray(list(self.grid_simulations.get_vals_sims()))

        if self.zones:
            self.project_zones_on_trace(self.zones)
        # added
        self.mycs.prepare()
        self.mycs.relations()
        self.set_Manning(nManning=self.Manning)

        #self.plot_profile()
        self.update_UI(reset=False)
        self.update_plots()
        self.plot_cs()

    def _draw_on_profile(self, event: wx.Event):
        """
        This method display a grid where vertor can be encoded and drawn on the figure.
        """
        if self.zones:
            self.zones.xls
        self._update_drawings()

    def get_copy_compare(self):
        """
        This method creates a new panel containing a copy of the active profile.
        """
        page = PlotCSAll(None)
        copy_cs = self.mycs.deepcopy_profile()
        page.cs_setter(active_profile = copy_cs, compare = self.mycs, mapviewer=self.mapviewer)
        page.vec = self.vec

        # page.plot_profile()
        # page.plot_cs()

        return page

    def harmonize_profiles(self):
        """
        This method harmonizes the profiles characteristic (vertices).
        The method inserts missing vertices on  both profiles to allow their comparison.
        """
        if self.compare:
            # A copy of vertices is stored in memory to conserve the discretization of the initial profile.
            self.copy_vertices = copy.deepcopy(self.mycs.myvertices)
            # self.copy_nbvertices = copy.deepcopy(self.mycs.nbvertices)
            self.copy_compare_vertices = copy.deepcopy(self.compare.myvertices)
            # self.copy_compare_nbvertices = copy.deepcopy(self.compare.nbvertices)

            # Resetting the crossections characteristics after modifications from the table (cpgrid)
            self.mycs.reset_prepare()
            self.compare.reset_prepare()

            # Getting sz data from the 2 profiles (modified and reference)
            sz1 = self.mycs.get_sz()
            sz2 = self.compare.get_sz()

            # Creating a buffer with unique values of the sz(s) union
            mycs = np.array(sz1[0])
            reference = np.array(sz2[0])
            # test



            if mycs.shape[0] != reference.shape[0] or np.unique(mycs).shape[0] != np.sort(mycs).shape[0] or np.unique(reference).shape[0] != np.sort(reference).shape[0]:
                t =0.000001
                all = np.concatenate((mycs, reference), axis=None)
                all_sort = np.sort(all)
                all_dif = np.diff(all_sort)
                dif = np.insert(all_dif,0,1) # FIXME find an elegant way.
                new_sz  = all_sort[dif>t]

                #all_unique = np.unique(all)
            else:
                #check = np.allclose(mycs, reference)
                #if check == False:
                check_unique = np.isclose(mycs, reference)

                # Finding all differences between sz data
                dif_sz1 = mycs[check_unique == False]
                dif_sz2 = reference[check_unique == False]

                common_sz = mycs[check_unique == True]
                new = np.concatenate((common_sz, dif_sz1,dif_sz2), axis=None)
                new_sz = np.unique(new)



            # Harmonizing the modified profile
            length_cs = self.mycs.asshapely_ls()
            length_compare = self.compare.asshapely_ls()
            # Harmonized properties
            cs_vertices = []
            compare_vertices = []

            # process
            for i in new_sz:
                # Shapely cordinates
                coords_cs  = length_cs.interpolate(i)
                coords_compare  = length_compare.interpolate(i)
                # Wolf vertex
                curvert_cs = wolfvertex(coords_cs.x, coords_cs.y, coords_cs.z)
                curvert_compare = wolfvertex(coords_compare.x, coords_compare.y, coords_compare.z)
                cs_vertices.append(curvert_cs)
                compare_vertices.append(curvert_compare)

            # Update of the 2 profiles characteristics
            self.mycs.myvertices= cs_vertices
            self.compare.myvertices= compare_vertices

class windowsgrid(wx.Frame):
    """
    A class containing the different grids used for plotting the graphs.
    """
    def __init__(self, *args, callback=None, **kwargs):
        super(windowsgrid, self).__init__(*args, **kwargs)

        self.Bind(wx.EVT_CLOSE, self.Quit)

    def _update_buttons(self):
        self.But_update = wx.Button(self, label = _('Update profile'))

    def update_grid_vert(self, my_profile: profile, ref: profile = None, title : str = None, callback = None):
        self.set_grid_vert(my_profile=my_profile, ref= ref, title = title, callback = callback)
        self.Refresh(True)

    def set_grid_sz(self, my_profile: profile, ref: profile = None, title : str = None, callback = None):
        self.SetBackgroundColour('white')

    def set_grid_vert( self, my_profile: profile, ref: profile = None, title : str = None, callback = None, call1 = None, call2 = None):
        """
        This method displays a grid containing the active profile vertices.
        Also,the method contains a grid with the profile of reference for simultaneous insertion of vertices.
        """
        self.SetBackgroundColour('white')
        self.SetSize(width = 500, height=600)

        self.callback = callback

        self.mycs = my_profile
        self.ref = ref
        vertices = self.mycs.myvertices
        nb_rows = self.mycs.nbvertices

        gridsizer = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(gridsizer)

        self.profile_xls: CpGrid
        self.profile_xls = CpGrid(self, 1, wx.WANTS_CHARS)

        #New grid
        #self.ref_xls: CpGrid
        #self.ref_xls(self, 1, wx.WANTS_CHARS)

        gridsizer.Add(self.profile_xls, 1, wx.EXPAND)

        #Grid filling
        self.profile_xls.CreateGrid(nb_rows,5)
        self.mycs.fillgrid(gridto = self.profile_xls)
        self._evaluate_s()

        # Update buttons

        # Button from xyz
        But_update_from_xyz = wx.Button(self, label = _('Update profile from xyz'))
        gridsizer.Add(But_update_from_xyz, 0, wx.EXPAND)
        But_update_from_xyz.Bind(wx.EVT_BUTTON, call1)

        # Button from sz

        But_update_from_sz = wx.Button(self, label = _('Update profile from sz'))
        gridsizer.Add(But_update_from_sz, 0, wx.EXPAND)
        But_update_from_sz.Bind(wx.EVT_BUTTON, call2)


        #self.ref_xls.CreateGrid(nb_rows,5)
        #self.ref.fillgrid(gridto = self.ref_xls)

        #FIXME insert vertices on both profile and reference

        #sizerrows =  wx.StaticBoxSizer(wx.HORIZONTAL, self, label= _("Add rows (vertices)"))
        #self.txtrows = wx.TextCtrl(self, wx.ID_ANY, str(0), wx.DefaultPosition, wx.DefaultSize, style =wx.TE_CENTER|wx.TE_PROCESS_ENTER, name =_('rows'))
        #gridsizer.Add(sizerrows, 0, wx.EXPAND) #FIXME
        #sizerrows.Add(self.txtrows,1, wx.EXPAND) #FIXME
        #self.txtrows.Bind(wx.EVT_TEXT_ENTER, self.update_nbrows)

        self.SetTitle('Profile vertices - %s'%((title)))
        self.Center(dir = wx.VERTICAL)
        #self.Show(True)

    def _evaluate_s(self):
        """
        Compute and fill the s coordinates in the profile grid.
        """
        curv = self.mycs
        curv.update_lengths()
        self.profile_xls.SetCellValue(0,4,'0.0')
        s=0.
        for k in range(curv.nbvertices-1):
            s+=curv._lengthparts2D[k]
            self.profile_xls.SetCellValue(k+1,4,str(s))

    def set_grid_sims(self, models, title : str = None, callback = None):
        """
        This method displays a wx.grid containing the numerical models data.
        """

        self.callback = callback

        self.SetBackgroundColour('white')
        self.SetSize(width = 600, height = 500)

        panel = wx.Panel(self)
        gridsizer = wx.BoxSizer()
        gridsizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(gridsizer)

        menubar = wx.MenuBar()

        fileButton = wx.Menu()
        exitItem = fileButton.Append(wx.ID_EXIT, 'Exit', 'Close this window')

        menubar.Append(fileButton, 'Options')

        #grid creation
        self.qgrid: CpGrid = Grid(panel, name='Models',pos=(0,0), size =(1200,900))

        self.qgrid.CreateGrid(1,4)

        self.qgrid.SetColLabelValue(0,_('Model'))
        self.qgrid.SetColLabelValue(1,_('Discharge'))
        self.qgrid.SetColLabelValue(2,_('Water depth'))
        self.qgrid.SetColLabelValue(3,_('Water level'))

        nb=self.qgrid.GetNumberRows()

        if len(models) - nb > 0:
            self.qgrid.AppendRows(len(models) - nb+10)

        k=0
        for curv in models:
           self.qgrid.SetCellValue(k,0,str(curv[k]))
           self.qgrid.SetCellValue(k,1,str(curv[k]))
           self.qgrid.SetCellValue(k,2,str(curv[k]))
           self.qgrid.SetCellValue(k,3,str(curv[k]))
           k+=1

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.Quit, exitItem)

        self.SetTitle('Available models - %s'%((title)))
        self.Center(dir = wx.VERTICAL)
        self.Show(True)

    def get_vals_sims(self):
        # data
        nb_rows = self.qgrid.GetNumberRows()
        models = []

        for row in range(nb_rows):
            ids = self.qgrid.GetCellValue(row, 0)
            q = float(self.qgrid.GetCellValue(row, 1))
            h = float(self.qgrid.GetCellValue(row,2))
            z = float(self.qgrid.GetCellValue(row,3))
            if ids != '':
                models.append([ids,q,h,z])

        return models

    def Quit(self, event: wx.Event):
        """
        This method closes the wx.Frame containing the grid.
        """
        if self.callback is not None:
            self.callback()

        self.Hide()
        #self.Destroy()


class ProfileNotebook(wx.Frame):
    """
    Fenêtre contenant potentiellement plusieurs graphiques Matplotlib.
    """
    def __init__(self, mapviewer = None, show=True, framesize=(1024,768)):                                                      #Notebook (multiple plots) a wx.window should be passed inside (parent or you create your own)
        """
        Initialisation
        Si un parent est fourni, on l'attache, sinon on crée une fenêtre indépendante.
        """
        super().__init__(None, wx.ID_ANY, 'Wolf - Plotter',size=framesize)                                                                                        #Inheritance
        self.Maximize(True) #FIXME (Default solution for better visualisation)

        self.mapviewer  = mapviewer                                                                                                         #Parent
        self.notebook   = aui.AuiNotebook(self)     # ajout du notebook

        sizers = wx.BoxSizer()               #sizer pour servir de contenant au notebook
        sizers.Add(self.notebook, 1, wx.EXPAND)   #ajout du notebook au sizer et demande d'étendre l'objet en cas de redimensionnement
        self.SetSizer(sizers)                #applique le sizer

        menubar = wx.MenuBar()
        options_menu = wx.Menu()

        #modifyButton = options_menu.Append(wx.ID_ANY,_('Modify C.S.'), _('Modify the current profile') )
        legendButton = options_menu.Append(wx.ID_ANY,_('Legend parameters'), _('Modify the legends aspect'))
        quitButton = options_menu.Append(wx.ID_EXIT, _('Quit'),_('Close the whole notebook....'))
        menubar.Append(options_menu,_('Options'))

        self.SetMenuBar(menubar)
        #self.Bind(wx.EVT_MENU, self.modify_cs, modifyButton)
        self.Bind(wx.EVT_MENU, self.OnClose, quitButton)

        if show:                                                                                                                    #If true
            self.Show()                                                                                                       #show the frame

        self.Bind(wx.EVT_CLOSE , self.OnClose)                                                                                      #closing the window
        self.Bind(wx.EVT_WINDOW_DESTROY , self.OnClose)
        self.page_number = 0

    def OnClose(self,event):
        """
        This method closes the notebook.
        """
        self.notebook.Close()

    def modify_cs( self,event):
        """
        This method creates a new panel containing a copy of the active profile.

        The copy is used to modify the profile and to compare the modifications with the original profile.
        """

        n = self.notebook.GetPageCount()
        self.page_number += 1
        newpage = self.add("Modified: {}".format(self.page_number))

        page_src = self.notebook.GetPage(0)
        copy_cs = page_src.mycs.deepcopy_profile()

        if page_src.mapviewer is not None:            #Implemented for an utilisation outside of the interface.
            page_src.mapviewer.display_canvasogl(fig = newpage.figure , ax = newpage.ax_img)  #The view is set here to maintain the position of the active profile in the GUI.

        newpage.cs_setter(active_profile= copy_cs, compare = page_src.mycs)
        newpage.zones = page_src.zones # To avoid redrawing the vector (structures)
        newpage.plot_profile()
        newpage.plot_cs()
        newpage.modify_vertex()
        newpage.Show()
        self.notebook.SetSelection(n)

    def add(self, name="plot"):
        """
        Ajout d'un onglet au notebook
        L'onglet contient une Figure Matplotlib
        On retourne la figure du nouvel onglet
        """
        page = PlotCSAll(self.notebook)  # PLOTCSALL first page of the notebook
        self.notebook.AddPage(page, name)        #ajout de l'objet Plot au notebook
        #page.Butprofvert.Bind(wx.EVT_BUTTON, self.modify_cs)           # Uncomment in case a return to the first figure is not needed
        if self.notebook.GetPageCount() == 1:    # Uncomment in case a return to the first figure is needed
            page.Butprofvert.Bind(wx.EVT_BUTTON, self.modify_cs)
        else:
            page.Butprofvert.Bind(wx.EVT_BUTTON, page.show_vertices)

        return page

class ProfileWithoutGUI():
    """
    This class launches the notebook without passing through the wolfpy GUI.

    Useful for scripts commands (an example is provide in )
    """
    def __init__(self,  fcrossection ='', fsupport= '', format='') :

        self.cross = crosssections(fcrossection, format) #Crossection data
        self.myvec = Zones(fsupport)                   #Vector data

        self.app=wx.App()
        self.curprofile : profile
        self.plotter = ProfileNotebook()
        self.plotter.add('Figure 1') # .figure.add_subplot()


        if fsupport != '':
            self.cross.sort_along(self.myvec.myzones[0].myvectors[0].asshapely_ls(),'vesdre')


    def plot_prof(self, index ='', cross = None, active_vector = None):
        """
        This method launches the notebook without any wolf GUI.
        """

        if index != '':
            self.curprofile = self.cross.myprofiles[index]['cs']
            self.plotter.notebook.GetPage(0).cs_setter(mycross = self.cross, active_profile = self.curprofile)

        elif  index == '':
            self.plotter.notebook.GetPage(0).cs_setter(mycross = self.cross)


        self.app.MainLoop()
