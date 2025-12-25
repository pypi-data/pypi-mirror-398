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

from ..PyTranslate import _
from ..matplotlib_fig import Matplotlib_Figure, PRESET_LAYOUTS

import wx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backend_bases import KeyEvent, MouseEvent
from PIL import Image, ImageOps

import logging

class Digitizer:

    def __init__(self):

        """
        Main function of curve digitizer
        """

        plt.ion()

        # self.curves=[]

        # open the dialog
        file = wx.FileDialog(None,_("Select image to digitize"),
                wildcard="gif image (*.gif)|*.gif|jpeg image (*.jpg)|*.jpg|png image (*.png)|*.png|All files (*.*)|*.*",)

        if file.ShowModal() == wx.ID_CANCEL:
            return
        else:
            #récuparétaion du nom de fichier avec chemin d'accès
            self.filein =file.GetPath()

        # show the image
        self.figure = Matplotlib_Figure(PRESET_LAYOUTS.DEFAULT_EQUAL)
        self.figure.cur_ax.set_aspect('equal')
        self.figure.fig_properties._axes[0]._equal_axis == 1

        # win = self.figure._collaps_pane.GetPane()
        # self._convert_xy = wx.Button(win, -1, 'Convert XY to world coordinates')
        # self._convert_xy.Bind(wx.EVT_BUTTON, self.convert_xy)
        # self.figure._sizer_xls.Add(self._convert_xy, 0, wx.EXPAND)
        # self.figure.Layout()

        self.figure.add_image(self.filein, origin='lower')
        self.fig.tight_layout()

        self.ref_x = []
        self.ref_y = []

        self.ref_x_length = 0
        self.ref_y_length = 0

        self.xy = []

        # get reference length in x direction
        wx.MessageBox(_("Use SHIFT + Right Mouse Button to select two points as X reference.\n\nWe will use only the delta X to calculate the scaling factor.\nSo, the Y distance will be ignored."),_("Select reference X"))
        self.new_line(is_world=False, label = 'Reference X', color='black', linewidth=2)
        self.figure.action = ('Ref X', self._callback_pt)

    @property
    def ax(self) -> Axes:
        return self.figure.ax[0]

    @property
    def fig(self) -> Figure:
        return self.figure.fig

    # def convert_xy(self, event):
    #     """
    #     Convert the pixel coordinates to world coordinates
    #     """
    #     xy = self.figure.get_xy_from_grid()

    #     xy[:,0] = (xy[:,0] - self.origin_img[0]) * self.factor_X + self.origin_world[0]
    #     xy[:,1] = (xy[:,1] - self.origin_img[1]) * self.factor_Y + self.origin_world[1]

    #     self.figure.fill_grid_with_xy_np(xy)

    def new_line(self, is_world:bool = True, ax=None, **kwargs):

        line_props = self.figure.new_line(ax=ax, **kwargs)

        if is_world:
            line_props.xscale = self.factor_X
            line_props.yscale = self.factor_Y
            line_props.xorigin_world = self.origin_world[0]
            line_props.yorigin_world = self.origin_world[1]
            line_props.xorigin_local = self.origin_img[0]
            line_props.yorigin_local = self.origin_img[1]
            line_props.populate()

    def _callback_digitize(self, xy, which):

        if which == 'Digitize':
            pass
            # self.xy.append(xy)
        elif which == 'End Digitize':

            MsgBox = wx.MessageDialog(None,_("Digitize another curve?"),style=wx.YES_NO)
            reply=MsgBox.ShowModal()

            if reply == wx.ID_YES:
                self.new_line()
            else:
                self.figure.action = None

    def _callback_origin(self, xy, which):

        if which == 'Origin':
            self.origin_img = xy

            valid_origin = False
            while not valid_origin:
                dlg = wx.TextEntryDialog(None,_("Set the origin coordinate (X,Y)"),_("Set the origin"), "0,0")
                ret = dlg.ShowModal()

                if ret == wx.ID_OK:
                    origin = dlg.GetValue().split(',')

                    try:
                        self.origin_world = (float(origin[0]),float(origin[1]))
                        valid_origin = True
                    except:
                        valid_origin = False

            wx.MessageBox(_("Please digitize the curve.\n\n" +
                " - MAJ + Right click  : add point\n"+
                " - Press Enter : finish"),
                _("Digitize curve"))

            self.new_line(is_world = True, label = 'Curve', linewidth=1.5)
            self.figure.action = ('Digitize', self._callback_digitize)

    def _callback_pt(self, xy, which):

        if which == 'Ref X':
            self.ref_x.append(xy)

            if len(self.ref_x) == 2:

                validLength = False
                dlg=wx.TextEntryDialog(None,_("Enter the reference length [user unit | mm | cm | m | km]"))

                while not validLength:
                    dlg.ShowModal()

                    try:
                        self.ref_x_length = float(dlg.GetValue())
                        if self.ref_x_length > 0:
                            validLength = True
                    except:
                        validLength = False

                dlg.Destroy()

                # calculate scaling factor
                deltaref = np.abs(self.ref_x[1][0] - self.ref_x[0][0])
                self.factor_X = self.ref_x_length / deltaref

                reply = wx.MessageDialog(None,"{:4.0f} pixels in {:s} direction corresponding to {:4.4f} units. Is this correct?".format(deltaref, 'X', self.ref_x_length),style=wx.YES_NO)

                if reply.ShowModal() == wx.ID_NO:
                    logging.info(_('Retry !'))
                    self.ref_x = []
                    self.ref_x_length = 0
                else:
                    self.figure.action = None
                    MsgBox = wx.MessageDialog(None,_('Do you want to use the same reference along Y?'),style=wx.YES_NO)
                    result=MsgBox.ShowModal()
                    if result == wx.ID_YES:
                        self.factor_Y = self.factor_X

                        wx.MessageBox(_("Click one point for a reference in local axis (s,z)"),_("Select an origin"))
                        self.new_line(is_world = False, label = 'Origin', color='red', linewidth=4)
                        self.figure.action = ('Origin', self._callback_origin)
                    else:
                        # get the reference length in y direction
                        self.new_line(is_world = False, label = 'Reference Y', color='black', linewidth=2)
                        wx.MessageBox(_("Use SHIFT + Right Mouse Button to select two points as Y reference.\n\nWe will use only the delta Y to calculate the scaling factor.\nSo, the X distance will be ignored."),_("Select reference Y"))
                        self.figure.action = ('Ref Y', self._callback_pt)

        elif which == 'Ref Y':
            self.ref_y.append(xy)

            if len(self.ref_y) == 2:

                validLength = False
                dlg=wx.TextEntryDialog(None,_("Enter the reference length [user unit | mm | cm | m | km]"))
                while not validLength:
                    dlg.ShowModal()

                    try:
                        self.ref_y_length = float(dlg.GetValue())
                        if self.ref_y_length > 0:
                            validLength = True
                    except:
                        validLength = False

                dlg.Destroy()

                # calculate scaling factor
                deltaref = np.abs(self.ref_y[1][1] - self.ref_y[0][1])
                self.factor_Y = self.ref_y_length / deltaref

                reply = wx.MessageDialog(None,"{:4.0f} pixels in {:s} direction corresponding to {:4.4f} units. Is this correct?".format(deltaref, 'Y', self.ref_y_length),style=wx.YES_NO)

                if reply.ShowModal() == wx.ID_NO:
                    logging.info(_('Retry !'))
                    self.ref_y = []
                    self.ref_y_length = 0
                else:
                    wx.MessageBox(_("Click one point for a reference in local axis (s,z)"),_("Select an origin"))
                    self.new_line(is_world = False, label = 'Origin', color='red', linewidth=4)
                    self.figure.action = ('Origin', self._callback_origin)

if __name__ == "__main__":
    # run the main function
    ex = wx.App()
    digit = Digitizer()
    ex.MainLoop()