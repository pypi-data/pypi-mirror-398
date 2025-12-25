from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from typing import Literal
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
from matplotlib.axes import Axes
from wolfhece.CpGrid import CpGrid
from wolfhece.PyParams import Wolf_Param, new_json
from wolfhece.PyTranslate import _
from wolfhece.PyVertex import getRGBfromI

from PIL import Image, ImageOps


import wx
from matplotlib.backend_bases import KeyEvent, MouseEvent
from matplotlib.lines import Line2D


import logging
import json
from pathlib import Path
from enum import Enum


def sanitize_fmt(fmt):
    """
    Sanitizes the given format string for numerical formatting.
    This function ensures that the format string is in a valid format
    for floating-point number representation. If the input format string
    is 'None' or an empty string, it defaults to '.2f'. Otherwise, it
    ensures that the format string contains a decimal point and ends with
    'f' for floating-point representation. If the format string is '.f',
    it defaults to '.2f'.

    :param fmt: The format string to be sanitized.
    :type fmt: str
    :return: A sanitized format string suitable for floating-point number formatting.
    :rtype: str
    """
    if fmt in ['None', '']:
        return '.2f'
    else:
        if not '.' in fmt:
            fmt = '.' + fmt

        if not 'f' in fmt:
            fmt = fmt + 'f'

        if fmt == '.f':
            fmt = '.2f'

        return fmt


class Matplotlib_ax_properties():

    def __init__(self, ax:Axes =None) -> None:

        self._ax = ax
        self._myprops = None
        self._lines:list[Matplolib_line_properties] = []

        self._tmp_line_prop:Matplolib_line_properties = None
        self._selected_line = -1

        if ax is None:
            self.title = 'Figure'
            self.xtitle = 'X [m]'
            self.ytitle = 'Y [m]'
            self.legend = False
            self.xmin = -99999
            self.xmax = -99999
            self.ymin = -99999
            self.ymax = -99999
            self.gridx_major = False
            self.gridy_major = False
            self.gridx_minor = False
            self.gridy_minor = False

            self._equal_axis = 0
            self.scaling_factor = 1.

            self.ticks_x = 1.
            self.ticks_y = 1.
            self.ticks_label_x = 1.
            self.ticks_label_y = 1.

            self.format_x = '.2f'
            self.format_y = '.2f'
        else:
            self.title = ax.get_title()
            self.xtitle = ax.get_xlabel()
            self.ytitle = ax.get_ylabel()
            self.legend = ax.get_legend() is not None
            self.xmin = -99999
            self.xmax = -99999
            self.ymin = -99999
            self.ymax = -99999
            self.gridx_major = False
            self.gridy_major = False
            self.gridx_minor = False
            self.gridy_minor = False

            aspect = ax.get_aspect()
            self._equal_axis = 0 if aspect == 'auto' else 1 if aspect in [1., 'equal'] else 2
            self.scaling_factor = 0 if aspect == 'auto' else 1 if aspect in [1., 'equal'] else aspect

            self.ticks_x = ax.get_xticks()
            self.ticks_y = ax.get_yticks
            self.ticks_label_x = ax.get_xticklabels()
            self.ticks_label_y = ax.get_yticklabels()

            self.format_x = '.2f'
            self.format_y = '.2f'

        self._set_props()

    @property
    def is_equal(self):

        if self._equal_axis == 1:
            return 'equal'
        elif self._equal_axis == 0:
            return 'auto'
        else:
            return self.scaling_factor

    def reset_selection(self):
        if self._selected_line>=0:
            for curline in self._lines:
                curline.selected = False
            self._selected_line = -1

    def select_line(self, idx:int):

        if self._selected_line>=0:
            self.reset_selection()

        if idx>=0 and idx<len(self._lines):
            self._selected_line = idx
            self._lines[idx].selected = True

    def set_ax(self, ax:Axes):
        self._ax = ax

        if ax is None:
            return

        self.get_properties()

        self._lines = [Matplolib_line_properties(line, self) for line in ax.get_lines()]

        return self

    def _set_props(self):
        """ Set the properties UI """

        if self._myprops is not None:
            return

        self._myprops = Wolf_Param(title='Figure properties',
                                   w= 500, h= 400,
                                   to_read= False,
                                   ontop= False,
                                   init_GUI= False)

        self._myprops.set_callbacks(None, self.destroyprop)

        # self._myprops.hide_selected_buttons() # only 'Apply' button

        self._myprops.addparam('Draw','Title',self.title,'String','Title')
        self._myprops.addparam('Draw','X title',self.xtitle,'String','X title')
        self._myprops.addparam('Draw','Y title',self.ytitle,'String','Y title')
        self._myprops.addparam('Draw','Legend',self.legend,'Logical','Legend')

        self._myprops.addparam('Bounds','X min',self.xmin,'Float','X min')
        self._myprops.addparam('Bounds','X max',self.xmax,'Float','X max')
        self._myprops.addparam('Bounds','Y min',self.ymin,'Float','Y min')
        self._myprops.addparam('Bounds','Y max',self.ymax,'Float','Y max')

        self._myprops.addparam('Ticks X','Positions',self.ticks_x,'String','X ticks')
        self._myprops.addparam('Ticks X','Labels',self.ticks_label_x,'String','X ticks labels')

        self._myprops.addparam('Ticks Y','Positions',self.ticks_y,'String','Y ticks')
        self._myprops.addparam('Ticks Y','Labels',self.ticks_label_y,'String','Y ticks labels')

        self._myprops.addparam('Formats','Ticks X',self.format_x,'String','X format')
        self._myprops.addparam('Formats','Ticks Y',self.format_y,'String','Y format')
        self._myprops.addparam('Formats','Shape',self._equal_axis,'Integer','Shape', jsonstr= new_json({'auto':0, 'equal':1, 'specific':2}))
        self._myprops.addparam('Formats','Scaling factor',self.scaling_factor,'Float','Scaling factor')

        self._myprops.add_param('Grid','Major X', self.gridx_major, 'Logical', 'Major grid X')
        self._myprops.add_param('Grid','Major Y', self.gridy_major, 'Logical', 'Major grid Y')

        self._myprops.Populate()

    def populate(self):
        """ Populate the properties UI """

        if self._myprops is None:
            self._set_props()

        self._myprops[('Draw','Title')] = self.title
        self._myprops[('Draw','X title')] = self.xtitle
        self._myprops[('Draw','Y title')] = self.ytitle
        self._myprops[('Draw','Legend')] = self.legend

        self._myprops[('Bounds','X min')] = self.xmin
        self._myprops[('Bounds','X max')] = self.xmax
        self._myprops[('Bounds','Y min')] = self.ymin
        self._myprops[('Bounds','Y max')] = self.ymax

        self._myprops[('Grid','Major X')] = self.gridx_major
        self._myprops[('Grid','Major Y')] = self.gridy_major

        self._myprops[('Ticks X','Positions')] = self.ticks_x
        self._myprops[('Ticks X','Labels')] = self.ticks_label_x

        self._myprops[('Ticks Y','Positions')] = self.ticks_y
        self._myprops[('Ticks Y','Labels')] = self.ticks_label_y

        self._myprops[('Formats','Ticks X')] = self.format_x
        self._myprops[('Formats','Ticks Y')] = self.format_y

        self._myprops[('Formats','Shape')] = self._equal_axis
        self._myprops[('Formats','Scaling factor')] = self.scaling_factor

        self._myprops.Populate()

    def ui(self):

        if self._myprops is not None:
            self._myprops.CenterOnScreen()
            self._myprops.Raise()
            self._myprops.Show()
            return

        self._set_props()

        self._myprops.Show()

        self._myprops.SetTitle(_('Ax properties'))

        icon = wx.Icon()
        icon_path = Path(__file__).parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        self._myprops.SetIcon(icon)

        self._myprops.Center()
        self._myprops.Raise()

    def destroyprop(self):
        self._myprops=None

    def bounds_lines(self):

        if self._ax is None:
            logging.warning('No axes found')
            return

        lines = self._ax.get_lines()
        img   = self._ax.get_images()

        if len(lines) == 0 and len(img) == 0:
            logging.warning('No lines/image found')
            return

        xmin = np.inf
        xmax = -np.inf
        ymin = np.inf
        ymax = -np.inf

        for line in lines:
            x = line.get_xdata()
            y = line.get_ydata()

            xmin = min(xmin, np.min(x))
            xmax = max(xmax, np.max(x))
            ymin = min(ymin, np.min(y))
            ymax = max(ymax, np.max(y))

        for im in img:
            x = im.get_extent()
            xmin = min(xmin, x[0])
            xmax = max(xmax, x[1])
            ymin = min(ymin, x[2])
            ymax = max(ymax, x[3])

        return xmin, xmax, ymin, ymax

    def fill_property(self, verbosity= True):

        if self._myprops is None:
            logging.warning('Properties UI not found')
            return

        self._myprops.apply_changes_to_memory(verbosity= verbosity)

        self.title = self._myprops[('Draw','Title')]
        self.xtitle = self._myprops[('Draw','X title')]
        self.ytitle = self._myprops[('Draw','Y title')]
        self.legend = self._myprops[('Draw','Legend')]

        self.xmin = self._myprops[('Bounds','X min')]
        self.xmax = self._myprops[('Bounds','X max')]
        self.ymin = self._myprops[('Bounds','Y min')]
        self.ymax = self._myprops[('Bounds','Y max')]

        self.gridx_major = self._myprops[('Grid','Major X')]
        self.gridy_major = self._myprops[('Grid','Major Y')]

        xmin, xmax, ymin, ymax = self.bounds_lines()

        if self.xmin == -99999.:
            self.xmin = xmin
        if self.xmax == -99999.:
            self.xmax = xmax
        if self.ymin == -99999.:
            self.ymin = ymin
        if self.ymax == -99999.:
            self.ymax = ymax

        self.format_x = sanitize_fmt(self._myprops[('Formats','Ticks X')])
        self.format_y = sanitize_fmt(self._myprops[('Formats','Ticks Y')])

        def format_value(value, fmt):
            return '{value:{fmt}}'.format(value=value, fmt=fmt)

        ticks_x = self._myprops[('Ticks X','Positions')]
        if '[' in ticks_x:
            self.ticks_x = [float(cur.replace("'",'').replace(',','')) for cur in self._myprops[('Ticks X','Positions')].replace('[','').replace(']','').split()]
        else:
            try:
                self.ticks_x = float(ticks_x)
                self.ticks_x = np.linspace(self.xmin, self.xmax, int(np.ceil((self.xmax-self.xmin)/self.ticks_x)+1), endpoint=True).tolist()
            except:
                self.ticks_x = np.linspace(self.xmin, self.xmax, 5).tolist()

        ticks_label_x = self._myprops[('Ticks X','Labels')]
        if '[' in ticks_label_x:
            self.ticks_label_x = [cur.replace("'",'').replace(',','') for cur in self._myprops[('Ticks X','Labels')].replace('[','').replace(']','').split()]
            if len(self.ticks_label_x) != len(self.ticks_x):
                self.ticks_label_x = [format_value(cur, self.format_x) for cur in self.ticks_x]
        else:
            self.ticks_label_x = [format_value(cur, self.format_x) for cur in self.ticks_x]

        ticks_y = self._myprops[('Ticks Y','Positions')]
        if '[' in ticks_y:
            self.ticks_y = [float(cur.replace("'",'').replace(',','')) for cur in self._myprops[('Ticks Y','Positions')].replace('[','').replace(']','').split()]
        else:
            try:
                self.ticks_y = float(ticks_y)
                self.ticks_y = np.linspace(self.ymin, self.ymax, int(np.ceil((self.ymax-self.ymin)/self.ticks_y)+1), endpoint= True).tolist()
            except:
                self.ticks_y = np.linspace(self.ymin, self.ymax, 5).tolist()

        ticks_label_y = self._myprops[('Ticks Y','Labels')]
        if '[' in ticks_label_y:
            self.ticks_label_y = [cur.replace("'",'').replace(',','') for cur in self._myprops[('Ticks Y','Labels')].replace('[','').replace(']','').split()]
            if len(self.ticks_label_y) != len(self.ticks_y):
                self.ticks_label_y = [format_value(cur, self.format_y) for cur in self.ticks_y]
        else:
            self.ticks_label_y = [format_value(cur, self.format_y) for cur in self.ticks_y]

        self._equal_axis = self._myprops[('Formats','Shape')]
        self.scaling_factor = self._myprops[('Formats','Scaling factor')]

        self.set_properties()

    def set_properties(self, ax:Axes = None):

        if ax is None:
            ax = self._ax

        ax.set_title(self.title)
        ax.set_xlabel(self.xtitle)
        ax.set_ylabel(self.ytitle)

        ax.xaxis.grid(self.gridx_major)
        ax.yaxis.grid(self.gridy_major)

        if len(self.ticks_x) <= 100:
            ax.set_xticks(self.ticks_x, self.ticks_label_x)
        if len(self.ticks_y) <= 100:
           ax.set_yticks(self.ticks_y, self.ticks_label_y)

        if self.legend:
            update = any(line.update_legend for line in self._lines)
            if update:
                ax.legend().set_visible(False)
                for line in self._lines:
                    line.update_legend = True
            ax.legend().set_visible(True)
        else:
            ax.legend().set_visible(False)

        ax.set_aspect(self.is_equal)

        ax.set_xlim(self.xmin, self.xmax)
        ax.set_ylim(self.ymin, self.ymax)

        ax.figure.canvas.draw()

        self.get_properties()

    def get_properties(self, ax:Axes = None):

        if ax is None:
            ax = self._ax

        self.title = ax.get_title()
        self.xtitle = ax.get_xlabel()
        self.ytitle = ax.get_ylabel()
        self.legend = ax.legend().get_visible()
        self.xmin, self.xmax = ax.get_xlim()
        self.ymin, self.ymax = ax.get_ylim()

        self.gridx_major = any(line.get_visible() for line in ax.get_xgridlines())
        self.gridy_major = any(line.get_visible() for line in ax.get_ygridlines())

        self.ticks_x = [str(cur) for cur in ax.get_xticks()]
        self.ticks_y = [str(cur) for cur in ax.get_yticks()]

        self.ticks_label_x = [label.get_text().replace("'",'').replace(',','') for label in ax.get_xticklabels()]
        self.ticks_label_y = [label.get_text().replace("'",'').replace(',','') for label in ax.get_yticklabels()]

        if ax.get_aspect() == 'auto':
            self._equal_axis = 0
            self.scaling_factor = 1.
        elif ax.get_aspect() == 1.:
            self._equal_axis = 1
            self.scaling_factor = 1.
        else:
            self._equal_axis = 2
            self.scaling_factor = ax.get_aspect()
            logging.warning('Aspect ratio not found, set to auto')

        self.populate()

    def to_dict(self) -> str:
        """ properties to dict """

        props= {'title':self.title,
                'xtitle':self.xtitle,
                'ytitle':self.ytitle,
                'legend':self.legend,
                'xmin':self.xmin,
                'xmax':self.xmax,
                'ymin':self.ymin,
                'ymax':self.ymax,
                'ticks_x':self.ticks_x,
                'ticks_y':self.ticks_y,
                'ticks_label_x':self.ticks_label_x,
                'ticks_label_y':self.ticks_label_y}

        if self._lines is not None:
            props['lines'] = [line.to_dict() for line in self._lines]
        else:
            props['lines'] = []

        return props

    def from_dict(self, props:dict, frame:wx.Frame = None):
        """ properties from dict """

        keys = ['title', 'xtitle', 'ytitle', 'legend', 'xmin', 'xmax', 'ymin', 'ymax', 'ticks_x', 'ticks_y', 'ticks_label_x', 'ticks_label_y']

        for key in keys:
            try:
                setattr(self, key, props[key])
            except:
                logging.warning('Key not found in properties dict')
                pass

        if isinstance(self.ticks_x,list):
            self.ticks_x = [float(cur) for cur in props['ticks_x']]
        elif isinstance(self.ticks_x,float):
            self.ticks_x = [self.ticks_x]
        elif isinstance(self.ticks_x,str):
            self.ticks_x = [float(self.ticks_x)]

        if isinstance(self.ticks_y,list):
            self.ticks_y = [float(cur) for cur in props['ticks_y']]
        elif isinstance(self.ticks_y,float):
            self.ticks_y = [self.ticks_y]
        elif isinstance(self.ticks_y,str):
            self.ticks_y = [float(self.ticks_y)]

        if isinstance(self.ticks_label_x,list):
            pass
        elif isinstance(self.ticks_label_x,float):
            self.ticks_label_x = [self.ticks_label_x]
        elif isinstance(self.ticks_label_x,str):
            self.ticks_label_x = [self.ticks_label_x]

        if isinstance(self.ticks_label_y,list):
            pass
        elif isinstance(self.ticks_label_y,float):
            self.ticks_label_y = [self.ticks_label_y]
        elif isinstance(self.ticks_label_y,str):
            self.ticks_label_y = [self.ticks_label_y]

        assert len(self.ticks_x) == len(self.ticks_label_x), f'{len(self.ticks_x)} != {len(self.ticks_label_x)}'
        assert len(self.ticks_y) == len(self.ticks_label_y), f'{len(self.ticks_y)} != {len(self.ticks_label_y)}'

        for line in props['lines']:
            if 'xdata' in line and 'ydata' in line:
                xdata = line['xdata']
                ydata = line['ydata']
                self._ax.plot(xdata, ydata)

        self.populate()

        self._lines = [Matplolib_line_properties(line, self).from_dict(line_props) for line_props, line in zip(props['lines'], self._ax.get_lines())]

        return self

    def serialize(self):
        """ Serialize the properties """

        return json.dumps(self.to_dict(), indent=4)

    def deserialize(self, props:str):
        """ Deserialize the properties """

        self.from_dict(json.loads(props))

    def add_props_to_sizer(self, frame:wx.Frame, sizer:wx.BoxSizer):
        """ Add the properties to a sizer """

        self._myprops.ensure_prop(frame, show_in_active_if_default=True, height=300)
        sizer.Add(self._myprops.prop, proportion= 1, flag= wx.EXPAND)

        self._myprops.prop.Hide()

    def show_props(self):
        """ Show the properties """

        self._myprops.prop.Show()

    def hide_props(self):
        """ Hide the properties """

        self._myprops.prop.Hide()

    def hide_all_props(self):
        """ Hide all properties """

        self.hide_props()

        for line in self._lines:
            line.hide_props()

    def del_line(self, idx:int):
        """ Delete a line """

        if idx>=0 and idx<len(self._lines):
            self._lines[idx].delete()
            self._lines.pop(idx)
            self._ax.lines.pop(idx)


MARKERS_MPL = ['None','o', 'v', '^', '<', '>', 's', 'p', 'P', '*', 'h', 'H', '+', 'x', 'X', 'D', 'd', '|', '_']
LINESTYLE_MPL = ['-', '--', '-.', ':', 'solid', 'dashed', 'dashdot', 'dotted', 'None']


def convert_colorname_rgb(color:str) -> str:
    """
    Convert a given color name or abbreviation to its corresponding RGB tuple.

    :param color: The color name or abbreviation to convert.
                  Supported colors are 'b'/'blue', 'g'/'green', 'r'/'red',
                  'c'/'cyan', 'm'/'magenta', 'y'/'yellow', 'k'/'black',
                  'w'/'white', and 'o'/'orange'.
    :type color: str
    :return: A tuple representing the RGB values of the color. If the color is not
             recognized, returns (0, 0, 0) which corresponds to black.
    :rtype: tuple
    """

    if color in COLORS_MPL:
        if color in ['b', 'blue']:
            return (0,0,255)
        elif color in ['g', 'green']:
            return (0,128,0)
        elif color in ['r', 'red']:
            return (255,0,0)
        elif color in ['c', 'cyan']:
            return (0,255,255)
        elif color in ['m', 'magenta']:
            return (255,0,255)
        elif color in ['y', 'yellow']:
            return (255,255,0)
        elif color in ['k', 'black']:
            return (0,0,0)
        elif color in ['w', 'white']:
            return (255,255,255)
        elif color in ['o', 'orange']:
            return (255,165,0)
    else:
        return(0,0,0)


def convert_color(value:str | tuple) -> tuple:
    """ Convert a hex color to RGB """

    if isinstance(value, tuple):
        return tuple([int(cur*255) for cur in value])
    elif isinstance(value, str):
        if value.startswith('#'):
            value = value.lstrip('#')
            return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
        else:
            return convert_colorname_rgb(value)
    else:
        return (0,0,0)


class Matplolib_line_properties():

    def __init__(self, line:Line2D=None, ax_props:"Matplotlib_ax_properties"= None) -> None:

        self.wx_exits = wx.App.Get() is not None

        self._ax_props = ax_props

        self.color = (0,0,255)
        self.linewidth = 1.5
        self._linestyle = 0
        self._marker = 0
        self.markersize = 6
        self.alpha = 1.0
        self.label = 'Line'
        self.markerfacecolor = (0,0,255)
        self.markeredgecolor = (0,0,255)
        self.markeredgewidth = 1.5
        self.visible = True
        self.zorder = 1
        self.picker:bool = False
        self.picker_radius:float = 5.0

        self._selected = False
        self._selected_prop:Matplolib_line_properties = None

        self._myprops = None
        self._line = line

        self.update_legend = False

        self._scales = [1.0, 1.0]
        self._origin_world = [0.0, 0.0]
        self._origin_local = [0.0, 0.0]

        self._set_props()

        if self._line is not None:
            self.get_properties()

    def get_xydata(self, two_columns:bool = False):
        """ Get the xy data """

        if self._line is None:
            return None

        if two_columns:
            return (self._line.get_xdata() - self._origin_local[0]) * self._scales[0] + self._origin_world[0], \
                   (self._line.get_ydata() - self._origin_local[1]) * self._scales[1] + self._origin_world[1]
        else:
            return np.array([(self._line.get_xdata() - self._origin_local[0]) * self._scales[0] + self._origin_world[0],
                             (self._line.get_ydata() - self._origin_local[1]) * self._scales[1] + self._origin_world[1]]).T

    def set_xydata(self, xy_data:np.ndarray):
        """ Set the xy data """

        if self._line is None:
            return

        self._line.set_xdata((xy_data[:,0] - self._origin_world[0]) / self._scales[0] + self._origin_local[0])
        self._line.set_ydata((xy_data[:,1] - self._origin_world[1]) / self._scales[1] + self._origin_local[1])

    @property
    def xdata(self):
        return self.get_xydata(two_columns= True)[0]

    @property
    def ydata(self):
        return self.get_xydata(two_columns= True)[1]

    @property
    def xydata(self):
        return self.get_xydata()

    @xydata.setter
    def xydata(self, value):

        if not isinstance(value, np.ndarray):
            logging.warning('xydata must be a numpy array')
            return

        if value.shape[1] != 2:
            logging.warning('xydata must have 2 columns')
            return

        self.set_xydata(value)

    @property
    def ax_props(self):
        return self._ax_props

    @ax_props.setter
    def ax_props(self, value):
        self._ax_props = value

    @property
    def ax(self):
        return self._ax_props._ax

    @property
    def fig(self):
        return self._ax_props._ax.figure

    def copy(self):
        new_prop = Matplolib_line_properties()

        new_prop._ax_props = self._ax_props

        new_prop.color = self.color
        new_prop.linewidth = self.linewidth
        new_prop._linestyle = self._linestyle
        new_prop._marker = self._marker
        new_prop.markersize = self.markersize
        new_prop.alpha = self.alpha
        new_prop.label = self.label
        new_prop.markerfacecolor = self.markerfacecolor
        new_prop.markeredgecolor = self.markeredgecolor
        new_prop.markeredgewidth = self.markeredgewidth
        new_prop.visible = self.visible
        new_prop.zorder = self.zorder
        new_prop.picker = self.picker
        new_prop.picker_radius = self.picker_radius

        return new_prop

    def presets(self, preset:str):
        """ Set the properties to a preset """

        self.color = (0,0,255)
        self.linewidth = 1.5
        self._linestyle = 0
        self._marker = 0
        self.markersize = 6
        self.alpha = 1.0
        self.label = 'Line'
        self.markerfacecolor = (0,0,255)
        self.markeredgecolor = (0,0,255)
        self.markeredgewidth = 1.5
        self.visible = True
        self.zorder = 1
        self.picker = False
        self.picker_radius = 5.0

        if preset == 'default':
            pass
        elif preset == 'water':
            self.color = (0,0,255)
            self.linewidth = 2.5
            self.label = 'Water'
        elif preset == 'land':
            self.color = (0,255,0)
            self.linewidth = 2.5
            self.label = 'Land'
        elif preset == 'banks':
            self.color = (128,128,128)
            self.linestyle = 1
            self.linewidth = 1.0

        self.set_properties()

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value
        self.set_properties()

    @property
    def linestyle(self):
        return LINESTYLE_MPL[self._linestyle]

    @linestyle.setter
    def linestyle(self, value):

        if isinstance(value, str):
            if value in LINESTYLE_MPL:
                self._linestyle = LINESTYLE_MPL.index(value)
            else:
                logging.warning('Line style not found, set to default')
                self._linestyle = 0
        elif isinstance(value, int):
            self._linestyle = value
        else:
            logging.warning('Line style not found, set to default')
            self._linestyle = 0

    @property
    def marker(self):
        return MARKERS_MPL[self._marker]

    @marker.setter
    def marker(self, value):
        if isinstance(value, str):
            if value in MARKERS_MPL:
                self._marker = MARKERS_MPL.index(value)
            else:
                logging.warning('Marker not found, set to default')
                self._marker = 0
        elif isinstance(value, int):
            self._marker = value
        else:
            logging.warning('Marker not found, set to default')
            self._marker = 0

    def set_line(self, line:Line2D):
        self._line = line

        if line is None:
            return

        self.get_properties()

        return self


    def on_pick(self, line:Line2D, mouseevent:MouseEvent):
        if mouseevent.button == 1:
            pass
            print(mouseevent.xdata, mouseevent.ydata)

            # line.set_color('r')
            # line.figure.canvas.draw()

        return True, dict()

    def get_properties(self, line:Line2D= None):

        if line is None:
            line = self._line

        if line is None:
            logging.warning('Line not found/defined')
            return

        self.color = convert_color(line.get_color())
        self.linewidth = line.get_linewidth()
        self.linestyle = line.get_linestyle()

        if self.linestyle not in LINESTYLE_MPL:
            self.linestyle = '-'
            logging.warning('Line style not found, set to default')

        self.marker = line.get_marker()

        if self.marker not in MARKERS_MPL:
            self.marker = 'o'
            logging.warning('Marker not found, set to default')

        self.markersize = line.get_markersize()
        self.alpha = line.get_alpha() if line.get_alpha() is not None else 1.0
        self.label = line.get_label()
        self.markerfacecolor = convert_color(line.get_markerfacecolor())
        self.markeredgecolor = convert_color(line.get_markeredgecolor())
        self.markeredgewidth = line.get_markeredgewidth()
        self.visible = line.get_visible()
        self.zorder = line.get_zorder()

        self.picker = line.get_picker() is not None
        self.picker_radius = line.get_pickradius()

    def _set_props(self):
        """ Set the properties UI """

        if self._myprops is not None:
            return

        self._myprops = Wolf_Param(title='Line properties', w= 500, h= 400, to_read= False, ontop= False, init_GUI= False)

        self._myprops.set_callbacks(None, self.destroyprop)

        # self._myprops.hide_selected_buttons() # only 'Apply' button

        self._myprops.addparam('Draw','Color',self.color,'Color','Drawing color')
        self._myprops.addparam('Draw','Width',self.linewidth,'Float','Drawing width')
        self._myprops.addparam('Draw','Style',self._linestyle,'Integer','Drawing style', jsonstr= new_json({'-':0, '--':1, '-.':2, ':':3, 'None':8, 'solid': 0, 'dashed': 1, 'dashdot': 2, 'dotted': 3}))
        self._myprops.addparam('Draw', 'Alpha', self.alpha, 'Float', 'Transparency')
        self._myprops.addparam('Draw', 'Label', self.label, 'String', 'Label')
        self._myprops.addparam('Draw', 'Visible', self.visible, 'Logical', 'Visible')
        self._myprops.addparam('Draw', 'Zorder', self.zorder, 'Integer', 'Zorder')

        self._myprops.addparam('Marker', 'Marker', self._marker, 'Integer', 'Marker style', jsonstr= new_json({'None':0, 'o': 1, 'v': 2, '^': 3, '<': 4, '>': 5, 's': 6, 'p': 7, 'P': 8, '*': 9, 'h': 10, 'H': 11, '+': 12, 'x': 13, 'X': 14, 'D': 15, 'd': 16, '|': 17, '_': 18}))
        self._myprops.addparam('Marker', 'Markersize', self.markersize, 'Float', 'Marker size')
        self._myprops.addparam('Marker', 'Markerfacecolor', self.markerfacecolor, 'Color', 'Marker face color')
        self._myprops.addparam('Marker', 'Markeredgecolor', self.markeredgecolor, 'Color', 'Marker edge color')
        self._myprops.addparam('Marker', 'Markeredgewidth', self.markeredgewidth, 'Float', 'Marker edge width')

        self._myprops.addparam('Picker', 'Picker', self.picker, 'Logical', 'Picker')
        self._myprops.addparam('Picker', 'Picker radius', self.picker_radius, 'Float', 'Picker radius')

        self._myprops.addparam('Scales', 'X scale', self._scales[0], 'Float', 'X scale')
        self._myprops.addparam('Scales', 'Y scale', self._scales[1], 'Float', 'Y scale')

        self._myprops.addparam('Origin', 'X world', self._origin_world[0], 'Float', 'X origin into world')
        self._myprops.addparam('Origin', 'Y world', self._origin_world[1], 'Float', 'Y origin into world')
        self._myprops.addparam('Origin', 'X local', self._origin_local[0], 'Float', 'X origin into local references')
        self._myprops.addparam('Origin', 'Y local', self._origin_local[1], 'Float', 'Y origin into local references')

        self._myprops.Populate()
        # self._myprops.Layout()
        # self._myprops.SetSizeHints(500,500)

    def populate(self):
        """ Populate the properties UI """

        if self._myprops is None:
            self._set_props()

        self._myprops[('Draw','Color')] = self.color
        self._myprops[('Draw','Width')] = self.linewidth
        self._myprops[('Draw','Style')] = self._linestyle
        self._myprops[('Draw','Alpha')] = self.alpha
        self._myprops[('Draw','Label')] = self.label
        self._myprops[('Draw','Visible')] = self.visible
        self._myprops[('Draw','Zorder')] = self.zorder

        self._myprops[('Marker', 'Marker')] = self._marker
        self._myprops[('Marker', 'Markersize')] = self.markersize
        self._myprops[('Marker', 'Markeredgecolor')] = self.markeredgecolor
        self._myprops[('Marker', 'Markerfacecolor')] = self.markerfacecolor
        self._myprops[('Marker', 'Markeredgewidth')] = self.markeredgewidth

        self._myprops[('Picker', 'Picker')] = self.picker
        self._myprops[('Picker', 'Picker radius')] = self.picker_radius

        self._myprops[('Scales', 'X scale')] = self._scales[0]
        self._myprops[('Scales', 'Y scale')] = self._scales[1]

        self._myprops[('Origin', 'X world')] = self._origin_world[0]
        self._myprops[('Origin', 'Y world')] = self._origin_world[1]
        self._myprops[('Origin', 'X local')] = self._origin_local[0]
        self._myprops[('Origin', 'Y local')] = self._origin_local[1]

        self._myprops.Populate()

    def ui(self):

        if self._myprops is not None:
            self._myprops.CenterOnScreen()
            self._myprops.Raise()
            self._myprops.Show()
            return

        self._set_props()

        self._myprops.Show()
        self._myprops.SetTitle(_('Line properties'))

        icon = wx.Icon()
        icon_path = Path(__file__).parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        self._myprops.SetIcon(icon)

        self._myprops.Center()
        self._myprops.Raise()

    def destroyprop(self):
        self._myprops=None

    def fill_property(self, verbosity:bool= True):

        if self._myprops is None:
            logging.warning('Properties UI not found')
            return

        self._myprops.apply_changes_to_memory(verbosity= verbosity)

        self.color = getRGBfromI(self._myprops[('Draw','Color')])
        self.linewidth = self._myprops[('Draw','Width')]
        self.linestyle = self._myprops[('Draw','Style')]
        self.alpha = self._myprops[('Draw', 'Alpha')]

        self.update_legend = self.label == self._myprops[('Draw', 'Label')]

        self.label = self._myprops[('Draw', 'Label')]
        self.visible = self._myprops[('Draw', 'Visible')]
        self.zorder = self._myprops[('Draw', 'Zorder')]

        self.marker = self._myprops[('Marker', 'Marker')]
        self.markersize = self._myprops[('Marker', 'Markersize')]
        self.markeredgecolor = getRGBfromI(self._myprops[('Marker', 'Markeredgecolor')])
        self.markerfacecolor = getRGBfromI(self._myprops[('Marker', 'Markerfacecolor')])
        self.markeredgewidth = self._myprops[('Marker', 'Markeredgewidth')]

        self.picker = self._myprops[('Picker', 'Picker')]
        self.picker_radius = self._myprops[('Picker', 'Picker radius')]

        self._scales[0] = self._myprops[('Scales', 'X scale')]
        self._scales[1] = self._myprops[('Scales', 'Y scale')]

        self._origin_world[0] = self._myprops[('Origin', 'X world')]
        self._origin_world[1] = self._myprops[('Origin', 'Y world')]

        self._origin_local[0] = self._myprops[('Origin', 'X local')]
        self._origin_local[1] = self._myprops[('Origin', 'Y local')]

        self.set_properties()

    def set_properties(self, line:Line2D = None):

        if line is None:
            line = self._line

        if line is None:
            logging.warning('Line not found/defined')
            return

        def check_color(color):
            if isinstance(color, str):
                color = convert_colorname_rgb(color)
            color = tuple([c/255. for c in color])
            return color

        line.set_color(check_color(self.color if not self.selected else (255,0,0)))
        line.set_linewidth(self.linewidth if not self.selected else 3.0)
        line.set_linestyle(self.linestyle if not self.selected else '-')

        line.set_marker(self.marker)
        line.set_markersize(self.markersize)
        line.set_alpha(self.alpha)
        line.set_label(self.label)
        line.set_markerfacecolor(check_color(self.markerfacecolor if not self.selected else (255,0,0)))
        line.set_markeredgecolor(check_color(self.markeredgecolor))
        line.set_markeredgewidth(self.markeredgewidth)

        line.set_visible(self.visible)
        line.set_zorder(self.zorder)

        line.set_pickradius(self.picker_radius)

        line.set_picker(self.on_pick if self.picker else lambda line,mouseevent: (False, dict()))

        if self._ax_props is not None:
            self._ax_props.fill_property(verbosity= False)
        else:
            line.axes.figure.canvas.draw()

    def show_properties(self):
        self.ui()

    @property
    def has_world_transfer(self):
        return self._scales[0] != 1.0 or self._scales[1] != 1.0 or self._origin_world[0] != 0. or self._origin_world[1] != 0. or self._origin_local[0] != 0. or self._origin_local[1] != 0.

    def to_dict(self) -> str:
        """ properties to dict """

        # We need to store the local data
        xy = self._line.get_xydata()
        xdata = xy[:,0].tolist()
        ydata = xy[:,1].tolist()

        locdict = {'color':self.color,
                'linewidth':self.linewidth,
                'linestyle':self.linestyle,
                'marker':self.marker,
                'markersize':self.markersize,
                'alpha':self.alpha,
                'label':self.label,
                'markerfacecolor':self.markerfacecolor,
                'markeredgecolor':self.markeredgecolor,
                'markeredgewidth':self.markeredgewidth,
                'visible':self.visible,
                'zorder':self.zorder,
                'picker':self.picker,
                'picker_radius':self.picker_radius,
                'xdata':xdata,
                'ydata':ydata,
                'xscale':self._scales[0],
                'yscale':self._scales[1],
                'xorigin_world':self._origin_world[0],
                'yorigin_world':self._origin_world[1],
                'xorigin_local':self._origin_local[0],
                'yorigin_local':self._origin_local[1]}

        if self.has_world_transfer:
            world_xdata, world_ydata = self.get_xydata(two_columns = True)
            world_xdata = world_xdata.tolist()
            world_ydata = world_ydata.tolist()

            locdict['world_xdata'] = world_xdata
            locdict['world_ydata'] = world_ydata

        return locdict

    def from_dict(self, props:dict):
        """ properties from dict """

        keys = ['color', 'linewidth', 'linestyle', 'marker', 'markersize', 'alpha',
                'label', 'markerfacecolor', 'markeredgecolor', 'markeredgewidth',
                'visible', 'zorder', 'picker', 'picker_radius',
                'xscale', 'yscale', 'xorigin_world', 'yorigin_world', 'xorigin_local', 'yorigin_local']

        for key in keys:
            try:
                setattr(self, key, props[key])
            except:
                logging.warning('Key not found in properties dict')
                pass

        # ATTENTION : The next 2 lines are done in the to_dict method of the axes
        # xydata = np.array([props['xdata'], props['ydata']]).T
        # self.set_xydata(xydata)

        self.populate()
        self.set_properties()

        return self

    @property
    def xscale(self):
        return self._scales[0]

    @xscale.setter
    def xscale(self, value):
        self._scales[0] = value

    @property
    def yscale(self):
        return self._scales[1]

    @yscale.setter
    def yscale(self, value):
        self._scales[1] = value

    @property
    def xorigin_world(self):
        return self._origin_world[0]

    @xorigin_world.setter
    def xorigin_world(self, value):
        self._origin_world[0] = value

    @property
    def yorigin_world(self):
        return self._origin_world[1]

    @yorigin_world.setter
    def yorigin_world(self, value):
        self._origin_world[1] = value

    @property
    def xorigin_local(self):
        return self._origin_local[0]

    @xorigin_local.setter
    def xorigin_local(self, value):
        self._origin_local[0] = value

    @property
    def yorigin_local(self):
        return self._origin_local[1]

    @yorigin_local.setter
    def yorigin_local(self, value):
        self._origin_local[1] = value

    def add_props_to_sizer(self, frame:wx.Frame, sizer:wx.BoxSizer):
        """ Add the properties to a sizer """

        self._myprops.ensure_prop(frame, show_in_active_if_default=True, height=300)
        sizer.Add(self._myprops.prop, proportion= 1, flag= wx.EXPAND)
        self._myprops.prop.Hide()

    def show_props(self):
        """ Show the properties """

        self.populate()
        self._myprops.prop.Show()

    def hide_props(self):
        """ Hide the properties """

        self._myprops.prop.Hide()

    def delete(self):
        """ Delete the properties """

        self._myprops.prop.Hide()
        self._myprops.prop.Destroy()
        self._myprops = None
        self._line = None

class PRESET_LAYOUTS(Enum):
    DEFAULT = (1,1, 'auto')
    MAT2X2  = (2,2, 'auto')
    DEFAULT_EQUAL = (1,1, 'equal')
class Matplotlib_Figure(wx.Frame):
    """  Matplotlib Figure with wx Frame """

    def __init__(self, layout:tuple | list | dict | PRESET_LAYOUTS = None) -> None:
        """
        Layout can be a tuple, a list, a dict or a string.
        If a string, it must be a list of strings or a list of lists. It will be used in fig.subplot_mosaic.
        If a tuple or a list of 2 integers. It will be used in fig.subplots.
        if a dict, it must contain 'nrows' and 'ncols' and 'ax_cells' (list of tuples with row_start, row_end, col_start, col_end, key).
        It will be used in fig.add_gridspec.

        The class has:
        - fig: the figure
        - ax_dict: a dict of axes --> key: name of the axes, value: axes
        - ax: a list of axes --> always flatten

        The properties of the figure can be accessed by self.fig_properties.
        The properties of the axes can be accessed by self._axes_properties.
        The current Axes can be accessed by self.cur_ax.

        A plot can be added by self.add_plot(xdata, ydata, label, color, linestyle, linewidth, marker, markersize, markerfacecolor, markeredgecolor, markeredgewidth, alpha, visible, zorder, picker, picker_radius)

        :param layout: layout of the figure
        :type layout: tuple | list | dict | str
        """

        self.wx_exists = wx.App.Get() is not None

        self.fig = Figure()
        # self.fig.set_visible(False)
        dpi = self.fig.get_dpi()
        size_x, size_y = self.fig.get_size_inches()

        if self.wx_exists:
            size_x = size_x*dpi+16
            size_y = size_y*dpi+240

            #compare to screen size
            screen = wx.Display(0)
            screen_size = screen.GetGeometry().GetSize()
            if size_x > screen_size[0]:
                size_x = screen_size[0]
            if size_y > screen_size[1]:
                size_y = screen_size[1]

            wx.Frame.__init__(self, None, -1, 'Matplotlib Figure', size=(size_x, size_y), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)

        self.ax_dict:dict[str,Axes] = {}    # dict of axes
        self.ax:list[Axes] = []             # list of axes -- always flatten
        self.shown_props = None     # shown properties
        self._shiftdown = False

        self._action = None
        self._keep_first_point = True

        self.apply_layout(layout)   # apply the layout
        pass

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        self._action = value

    def presets(self, which:PRESET_LAYOUTS = PRESET_LAYOUTS.DEFAULT):
        """ Presets """

        if which not in PRESET_LAYOUTS:
            logging.warning('Preset not found')
            return

        self.apply_layout(which)

    @property
    def layout(self):
        return self._layout

    def apply_layout(self, layout:tuple | list | dict | PRESET_LAYOUTS):
        """ Apply the layout

        Choose between (subplots, subplot_mosaic, gridspec) according to the type of layout (tuple, list[str], dict)
        """

        self._layout = layout

        if self._layout is None:
            logging.info('No layout defined')
            return

        if isinstance(layout, PRESET_LAYOUTS):

            self.apply_layout(layout.value)
            return

        if isinstance(layout, tuple | list):
            # check is the first element is a string - layout can be a list of lists
            tmp_layout = []
            for cur in layout:
                if isinstance(cur, list):
                    tmp_layout.extend(cur)
                else:
                    tmp_layout.append(cur)

            if isinstance(tmp_layout[0], str):
                # List of strings - subplot_mosaic returns a dict of Axes
                self.ax_dict = self.fig.subplot_mosaic(layout)
                # store the axes in a list -- So we can access them by index, not only by name
                self.ax = [ax for ax in self.ax_dict.values()]
            else:
                # Tuple or list of 3 elements - subplots
                if len(layout) != 3:
                    logging.warning('Layout must be a tuple or a list of 3 elements (nbrows:int, nbcols:int, aspect_ratio:str|float)')
                    return

                self.nbrows, self.nbcols, ratio = layout
                if self.nbrows*self.nbcols == 1:
                    # Convert to list -- subplots returns a single Axes but we want a list
                    self.ax = [self.fig.subplots(self.nbrows, self.nbcols)]
                else:
                    # Flatten the axes -- sbplots returns a 2D array of Axes but we want a list
                    self.ax = self.fig.subplots(self.nbrows, self.nbcols).flatten()

                for curax in self.ax:
                    if ratio == 'auto':
                        curax.set_aspect('auto')
                    elif ratio == 'equal':
                        curax.set_aspect('equal')
                    else:
                        curax.set_aspect(ratio)

                # store the axes in a dict -- So we can access them by name, not only by index
                self.ax_dict = {f'{i}':ax for i, ax in enumerate(self.ax)}
                for key,ax in self.ax_dict.items():
                    ax._label = key

        elif isinstance(layout, dict):
            # dict --> Gridspec

            # Check if nrows and ncols are defined
            if 'nrows' not in layout or 'ncols' not in layout:
                logging.warning('nrows and ncols must be defined in the layout')
                return

            if 'ax_cells' not in layout:
                logging.warning('ax_cells must be defined in the layout')
                return

            gs:GridSpec = self.fig.add_gridspec(nrows= layout['nrows'], ncols= layout['ncols'])
            ax_cells = layout['ax_cells']

            for row_start, row_end, col_start, col_end, key in ax_cells:
                self.ax_dict[key] = self.fig.add_subplot(gs[row_start:row_end, col_start:col_end])
                self.ax_dict[key]._label = key

            self.ax = [ax for ax in self.ax_dict.values()]

        self._fig_properties = Matplotlib_figure_properties(self, self.fig)

        if self.wx_exists:
            self.set_wx()

    @property
    def fig_properties(self) -> "Matplotlib_figure_properties":
        return self._fig_properties

    @property
    def _axes_properties(self) -> list[Matplotlib_ax_properties]:
        return self._fig_properties._axes

    @property
    def nbrows(self):
        return self._nbrows

    @nbrows.setter
    def nbrows(self, value:int):
        self._nbrows = value

    @property
    def nbcols(self):
        return self._nbcols

    @nbcols.setter
    def nbcols(self, value:int):
        self._nbcols = value

    @property
    def nb_axes(self):
        return len(self.ax)

    def set_wx(self):
        """ Set the wx Frame Design """

        self.SetIcon(wx.Icon(str(Path(__file__).parent / "apps/wolf.ico")))

        self._sizer = wx.BoxSizer(wx.VERTICAL)

        # Matplotlib canvas interacting with wx
        # --------------------------------------

        self._canvas = FigureCanvas(self, -1, self.fig)
        self._sizer.Add(self._canvas, 1, wx.EXPAND | wx.ALL)

        # Bind events
        self._canvas.Bind(wx.EVT_ENTER_WINDOW, self.ChangeCursor)
        self._canvas.mpl_connect('motion_notify_event', self.UpdateStatusBar)
        self._canvas.mpl_connect('button_press_event', self.OnClickCanvas)
        self._canvas.mpl_connect('key_press_event', self.OnKeyCanvas)
        self._canvas.mpl_connect('key_release_event', self.OnKeyRelease)

        # Toolbar - Matplotlib
        # --------------------

        self._toolbar = NavigationToolbar(self._canvas, self)


        # Buttons - Figure, Axes, Lines properties
        # --------- ------------------------------

        self._prop_but = wx.Button(self, -1, 'Figure Properties')

        self._ax_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._ax_current = wx.Choice(self, -1, choices=[ax._label for ax in self.ax])
        self._ax_current.SetToolTip('Select the current ax -- Axes are enumerated from left to right and top to bottom')
        self._ax_current.SetSelection(0)
        self._ax_but = wx.Button(self, -1, 'Ax Properties')
        self._ax_but.SetToolTip('Choosing the properties of the current ax -- Axes are enumerated from left to right and top to bottom')

        self._ax_current.Bind(wx.EVT_CHOICE, self.on_ax_choice)
        self._ax_but.Bind(wx.EVT_BUTTON, self.on_ax_properties)

        self._ax_sizer.Add(self._ax_current, 1, wx.EXPAND)
        self._ax_sizer.Add(self._ax_but, 1, wx.EXPAND)

        self._line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._line_current = wx.Choice(self, -1, choices=[str(i) for i in range(len(self.cur_ax.get_lines()))])
        self._line_current.SetSelection(0)
        self._line_but = wx.Button(self, -1, 'Line Properties')

        self._line_but.Bind(wx.EVT_BUTTON, self.on_line_properties)
        self._line_current.Bind(wx.EVT_CHOICE, self.on_line_choose)

        self._line_sizer.Add(self._line_current, 1, wx.EXPAND)
        self._line_sizer.Add(self._line_but, 1, wx.EXPAND)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self._prop_but.Bind(wx.EVT_BUTTON, self.on_fig_properties)

        self._sizer.Add(self._toolbar, 0, wx.EXPAND)
        self._sizer.Add(self._prop_but, 0, wx.EXPAND)

        self._sizer.Add(self._ax_sizer, 0, wx.EXPAND)
        self._sizer.Add(self._line_sizer, 0, wx.EXPAND)

        self._statusbar = wx.StatusBar(self)
        self._sizer.Add(self._statusbar, 0, wx.EXPAND)

        # Buttons - Save, Load
        # --------------------

        self._save_but = wx.Button(self, -1, 'Save')
        self._load_but = wx.Button(self, -1, 'Load')

        self._save_but.Bind(wx.EVT_BUTTON, self.on_save)
        self._load_but.Bind(wx.EVT_BUTTON, self.on_load)

        self._sizer_save_load = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer_save_load.Add(self._save_but, 1, wx.EXPAND)
        self._sizer_save_load.Add(self._load_but, 1, wx.EXPAND)
        self._sizer.Add(self._sizer_save_load, 0, wx.EXPAND)

        self._applyt_but = wx.Button(self, -1, 'Apply Properties')
        self._applyt_but.Bind(wx.EVT_BUTTON, self.onapply_properties)
        self._sizer.Add(self._applyt_but, 0, wx.EXPAND)

        # Collapsible pane -- Grid Xls, Properties
        # ----------------------------------

        self._collaps_pane = wx.CollapsiblePane(self, label='Properties', style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        self._collaps_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_collaps_pane)

        win = self._collaps_pane.GetPane()
        self._sizer_grid_props = wx.BoxSizer(wx.HORIZONTAL)
        win.SetSizer(self._sizer_grid_props)
        self._sizer_grid_props.SetSizeHints(win)

        # XLS sizer
        # ---------
        self._sizer_xls = wx.BoxSizer(wx.VERTICAL)

        self._xls = CpGrid(win, -1, wx.WANTS_CHARS)
        self._update_xy = wx.Button(win, -1, 'Update XY')
        self._update_xy.Bind(wx.EVT_BUTTON, self.update_line_from_grid)

        self._add_row = wx.Button(win, -1, 'Add rows')
        self._add_row.Bind(wx.EVT_BUTTON, self.add_row_to_grid)

        self._new_line = wx.Button(win, -1, 'New line')
        self._new_line.Bind(wx.EVT_BUTTON, self.onnew_line)

        self._add_line = wx.Button(win, -1, 'Add line')
        self._add_line.Bind(wx.EVT_BUTTON, self.onadd_line)

        self._del_line = wx.Button(win, -1, 'Remove line')
        self._del_line.Bind(wx.EVT_BUTTON, self.ondel_line)

        self._sizer_xls.Add(self._xls, 1, wx.EXPAND)

        self._sizer_update_add = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer_add_remove = wx.BoxSizer(wx.HORIZONTAL)

        self._sizer_xls.Add(self._sizer_update_add, 0, wx.EXPAND)
        self._sizer_xls.Add(self._sizer_add_remove, 0, wx.EXPAND)

        self._sizer_update_add.Add(self._update_xy, 1, wx.EXPAND)
        self._sizer_update_add.Add(self._add_row, 1, wx.EXPAND)

        self._sizer_add_remove.Add(self._new_line, 1, wx.EXPAND)
        self._sizer_add_remove.Add(self._add_line, 1, wx.EXPAND)
        self._sizer_add_remove.Add(self._del_line, 1, wx.EXPAND)

        # Properties sizer
        # ---------------

        # Add all props from axes
        self._fig_properties.add_props_to_sizer(win, self._sizer_grid_props)

        self._sizer_grid_props.Add(self._sizer_xls, 1, wx.GROW | wx.ALL)

        # self._sizer.Add(self._sizer_grid_props, 1, wx.EXPAND)
        self._collaps_pane.Expand()

        self._sizer.Add(self._collaps_pane, 0, wx.EXPAND | wx.ALL)

        self._xls.CreateGrid(10, 2)
        self._xls.SetColLabelValue(0, 'X')
        self._xls.SetColLabelValue(1, 'Y')
        self._xls.SetMaxSize((-1, 400))


        self.SetSizer(self._sizer)
        self.SetAutoLayout(True)
        # self.Layout()
        self.Fit()

        self.Bind(wx.EVT_SIZE, self.on_size)

        self.Show()
        self._collapsible_size = self._collaps_pane.GetSize()

    def on_save(self, event):
        """ Save the figure """

        with wx.FileDialog(self, "Save figure", wildcard="JSON files (*.json)|*.json", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            path = fileDialog.GetPath()
            self.save(str(path))

    def on_load(self, event):
        """ Load the figure """

        with wx.FileDialog(self, "Open figure", wildcard="JSON files (*.json)|*.json", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            path = fileDialog.GetPath()
            self.load(str(path))

    def ChangeCursor(self, event:MouseEvent):
        self._canvas.SetCursor(wx.Cursor(wx.CURSOR_BULLSEYE))

    def UpdateStatusBar(self, event:MouseEvent):

        if event.inaxes:
            idx= event.inaxes.get_figure().axes.index(event.inaxes)
            x, y = event.xdata, event.ydata
            self._statusbar.SetStatusText("Axes index= " + str(idx) + " -- x= "+str(x)+" -- y="+str(y))

    def _mask_all_axes_props(self):
        for ax_prop in self._axes_properties:
            ax_prop._myprops.prop.Hide()

    def _show_axes_props(self, idx:int):
        self._mask_all_axes_props()
        self._axes_properties[idx]._myprops.prop.Show()

    @property
    def cur_ax(self) -> Axes:
        return self.ax[int(self._ax_current.GetSelection())]

    @cur_ax.setter
    def cur_ax(self, idx:int):
        if idx < 0 or idx >= len(self.ax):
            logging.warning('Index out of range')
            return

        self._ax_current.SetSelection(idx)
        self._fill_lines_ax()

    @property
    def cur_ax_properties(self) -> Matplotlib_ax_properties:
        return self._axes_properties[int(self._ax_current.GetSelection())]

    @cur_ax_properties.setter
    def cur_ax_properties(self, idx:int):

        if idx < 0 or idx >= len(self._axes_properties):
            logging.warning('Index out of range')
            return

        self._ax_current.SetSelection(idx)
        self._fill_lines_ax()

    @property
    def cur_line_properties(self) -> Matplolib_line_properties:

        if self._line_current.GetSelection() == -1:
            return None

        return self.cur_ax_properties._lines[int(self._line_current.GetSelection())]

    @property
    def cur_line(self) -> Line2D:

        if self._line_current.GetSelection() == -1:
            return None
        else:
            return self.cur_ax.get_lines()[int(self._line_current.GetSelection())]

    def get_figax(self):

        if len(self.ax) == 1:
            return self.fig, self.ax[0]
        else:
            return self.fig, self.ax

    def on_close(self, event):
        self.Destroy()

    def on_fig_properties(self, event):
        """ Show the figure properties """
        self.show_fig_properties()

    def show_fig_properties(self):
        # self._fig_properties.ui()
        self._hide_all_props()
        self._fig_properties.show_props()
        self.Layout()
        self.shown_props = self._fig_properties

    def _fill_lines_ax(self, idx:int = None):
        self._line_current.SetItems([line.get_label() for line in self.cur_ax.get_lines()])
        self._line_current.SetSelection(0)

        if idx is not None:
            self._line_current.SetSelection(idx)

    def on_ax_choice(self, event):
        self._fill_lines_ax()

    def on_ax_properties(self, event):
        """ Show the ax properties """
        self.show_curax_properties()

    def show_curax_properties(self):
        # self.cur_ax_properties.ui()
        self._hide_all_props()
        self.cur_ax_properties.show_props()
        self.Layout()
        self.shown_props = self.cur_ax_properties

    def on_line_properties(self, event):
        """ Show the line properties """
        self.show_curline_properties()

    def show_curline_properties(self):
        # self.cur_line_properties.ui()
        self._hide_all_props()

        if self._line_current.GetSelection() == -1:
            return

        self.cur_line_properties.show_props()
        # self.Layout()
        self._sizer_grid_props.Layout()
        self.shown_props = self.cur_line_properties

    def onapply_properties(self, event):
        """ Apply the properties """

        if self.shown_props is not None:
            self.shown_props.fill_property()
            self.update_layout()

    def _hide_all_props(self):

        self._fig_properties.hide_props()
        for ax_prop in self._axes_properties:
            ax_prop.hide_all_props()

    def on_line_choose(self, event):

        self.cur_ax_properties.reset_selection()
        self.cur_ax_properties.select_line(self._line_current.GetSelection())
        self.fill_grid_with_xy()

    def on_size(self, event):
        """ Resize event """

        width, height = self.fig.get_size_inches()
        dpi = self.fig.get_dpi()
        width_pix = int(width * dpi)
        height_pix = int(height * dpi)

        self._canvas.MinSize = (width_pix, height_pix)

        self._collapsible_size = self._collaps_pane.GetSize()

        event.Skip()

    def update_layout(self):

        if not self.wx_exists:
            return

        width, height = self.fig.get_size_inches()
        dpi = self.fig.get_dpi()
        width_pix = int(width * dpi)
        height_pix = int(height * dpi)

        self._canvas.MinSize = (width_pix, height_pix)

        self.SetSize((width_pix + 16, height_pix + 210 + self._collapsible_size[1]))

        self.Fit()

    def on_collaps_pane(self, event):
        """ Collapsible pane event """

        if event.GetCollapsed():
            self._collaps_pane.Collapse()
        else:
            self._collaps_pane.Expand()

        if self._collapsible_size != self._collaps_pane.GetSize():
            self.SetSize((self.GetSize()[0], self.GetSize()[1] + self._collaps_pane.GetSize()[1]-self._collapsible_size[1]))
            self._collapsible_size = self._collaps_pane.GetSize()

        self.Fit()

    def OnKeyCanvas(self, event:KeyEvent):

        if event.key == 'escape':
            self._axes_properties[int(self._ax_current.GetSelection())].reset_selection()
        elif event.key == 'shift':
            self._shiftdown = True
        elif event.key == 'enter':
            if self.action is not None:
                action, callback = self.action
                if action == 'Digitize':
                    callback((0,0), 'End Digitize')

    def OnKeyRelease(self, event:KeyEvent):
        if event.key == 'shift':
            self._shiftdown = False

    def OnClickCanvas(self, event:MouseEvent):

        rclick = event.button == 3
        lclick = event.button == 1
        middle = event.button == 2

        if not (rclick or middle):
            return

        if event.inaxes:
            ax:Axes = event.inaxes
            idx= ax.get_figure().axes.index(event.inaxes)
            x, y = event.xdata, event.ydata

            if middle:
                if self.action is not None:
                    action, callback = self.action
                    if action == 'Digitize':
                        callback((0,0), 'End Digitize')

            if rclick:

                if self._shiftdown:
                    # add a point to the current line, update the grid and plot
                    xy = self.cur_line.get_xydata()

                    if xy.shape[0] == 1:
                        if self._keep_first_point:
                            xy = np.vstack((xy, [x,y]))
                        else:
                            xy = np.asarray([[x,y]])
                            self._keep_first_point = True
                    else:
                        xy = np.vstack((xy, [x,y]))

                    self.cur_line.set_data(xy[:,0], xy[:,1])
                    self.fill_grid_with_xy_np(self.cur_line_properties.get_xydata())
                    self._canvas.draw()

                if self.action is not None:

                    action, callback = self.action

                    if action == 'Digitize':
                        if not self._shiftdown:
                            logging.warning('Shift must be down to digitize')
                    elif action == 'Ref X':
                        if not self._shiftdown:
                            logging.warning('Shift must be down to set X reference')
                        else:
                            callback((x,y), action)
                    elif action == 'Ref Y':
                        if not self._shiftdown:
                            logging.warning('Shift must be down to set Y reference')
                        else:
                            callback((x,y), action)
                    elif action == 'Origin':
                        if not self._shiftdown:
                            logging.warning('Shift must be down to set origin')
                        else:
                            callback((x,y), action)

                elif not self._shiftdown:
                    # Find the closest line and select it

                    lines = ax.get_lines()
                    if len(lines) == 0:
                        logging.warning('No lines !')
                        return

                    dist_min = 1e6
                    line_min = None

                    for line in lines:
                        xy = line.get_xydata()
                        if xy.shape[0] == 0:
                            continue

                        dist = np.linalg.norm(xy - np.array([x,y]), axis=1)
                        idx_min = np.argmin(dist)
                        if dist[idx_min] < dist_min:
                            dist_min = dist[idx_min]
                            line_min = line

                    self._ax_current.SetSelection(idx)
                    self._fill_lines_ax(idx = lines.index(line_min))
                    self._axes_properties[idx].select_line(lines.index(line_min))

                    self.fill_grid_with_xy_np(self.cur_line_properties.get_xydata())

            self.show_curline_properties()

    def fill_grid_with_xy(self, line:Line2D= None, grid:CpGrid= None, colx:int= 0, coly:int= 1):

        if line is None:
            line = self.cur_line

        if grid is None:
            grid = self._xls

        xy = line.get_xydata()

        grid.ClearGrid()

        if grid.GetNumberRows() < len(xy):
            grid.AppendRows(len(xy)-grid.GetNumberRows())
        elif grid.GetNumberRows() > len(xy):
            grid.DeleteRows(len(xy), grid.GetNumberRows()-len(xy))

        for i in range(len(xy)):
            grid.SetCellValue(i, colx, str(xy[i,0]))
            grid.SetCellValue(i, coly, str(xy[i,1]))

    def fill_grid_with_xy_np(self, xy:np.ndarray, grid:CpGrid = None, colx:int= 0, coly:int= 1):

        if grid is None:
            grid = self._xls

        grid.ClearGrid()

        if grid.GetNumberRows() < len(xy):
            grid.AppendRows(len(xy)-grid.GetNumberRows())
        elif grid.GetNumberRows() > len(xy):
            grid.DeleteRows(len(xy), grid.GetNumberRows()-len(xy))

        for i in range(len(xy)):
            grid.SetCellValue(i, colx, str(xy[i,0]))
            grid.SetCellValue(i, coly, str(xy[i,1]))

    def get_xy_from_grid(self):
        """ Get the xy from the grid """

        return self._get_xy_from_grid(self._xls)

    def update_line_from_grid(self, event):

        line = self.cur_line

        #count not null values
        n = 0
        for i in range(self._xls.GetNumberRows()):
            if self._xls.GetCellValue(i, 0) != '' and self._xls.GetCellValue(i, 1) != '':
                n += 1

        xy = np.zeros((n, 2))

        for i in range(n):
            xy[i,0] = float(self._xls.GetCellValue(i, 0))
            xy[i,1] = float(self._xls.GetCellValue(i, 1))

        self.cur_line_properties.set_xydata(xy)
        self._canvas.draw()
        self.update_layout()

    def add_row_to_grid(self, event):

        dlg = wx.TextEntryDialog(self, 'Number of rows to add', 'Add rows', '1')
        dlg.ShowModal()

        try:
            n = int(dlg.GetValue())
        except:
            n = 1

        self._xls.AppendRows(n)

    def onadd_line(self, event):
        """ Add a plot to the current ax """

        xy = self._get_xy_from_grid(self._xls)
        self.add_line(xy, self.cur_ax)

    def onnew_line(self, event):
        """ Add a plot to the current ax """
        self.new_line()

    def new_line(self, ax:Axes=None, **kwargs) -> Matplolib_line_properties:
        """ Add a plot to the current ax """

        curline = self.cur_line
        if curline is not None:
            xy = curline.get_xydata()
            xy = np.asarray([[xy[0,0],xy[0,1]]])
        else:
            xy = np.asarray([[0,0]])

        self._keep_first_point = False
        return self.add_line(xy, ax, **kwargs)

    def _get_xy_from_grid(self, grid:CpGrid, colx:int= 0, coly:int= 1):
        """ Get the xy from a grid """

        #Searching xy in the grid
        #count not null values
        n = 0
        for i in range(grid.GetNumberRows()):
            if grid.GetCellValue(i, colx) != '' and grid.GetCellValue(i, coly) != '':
                n += 1

        xy = np.zeros((n, 2))

        for i in range(n):
            xy[i,0] = float(grid.GetCellValue(i, colx))
            xy[i,1] = float(grid.GetCellValue(i, coly))

        return xy

    def add_line(self, xy:np.ndarray, ax:Axes=None, **kwargs) -> Matplolib_line_properties:
        """ Add a plot to the current ax """

        ax, idx_ax = self.get_ax_idx(ax)

        ax.plot(xy[:,0], xy[:,1], **kwargs)

        cur_ax_prop:Matplotlib_ax_properties = self._axes_properties[idx_ax]
        cur_ax_prop._lines.append(Matplolib_line_properties(ax.get_lines()[-1], cur_ax_prop))
        cur_ax_prop._lines[-1].add_props_to_sizer(self._collaps_pane.GetPane(), self._sizer_grid_props)

        self._fill_lines_ax(len(ax.get_lines())-1)

        self.update_layout()
        self._canvas.SetFocus()

        return self.cur_ax_properties._lines[-1]

    def add_image(self, image:np.ndarray | str, ax:Axes= None, **kwargs):

        ax, idx_ax = self.get_ax_idx(ax)

        if isinstance(image, str):
            image = ImageOps.flip(Image.open(image))
            ax.axis('off')  # clear x-axis and y-axis

        ax.imshow(image, **kwargs)

        self.update_layout()
        self._canvas.SetFocus()

    def ondel_line(self, event):
        """ Remove a plot from the current ax """

        if self._line_current.GetSelection() == -1:
            return

        dlg = wx.MessageDialog(self, _('Do you want to remove the selected line?\n\nSuch action is irrevocable !\n\nPlease consider to set "Visible" to "False" to hide data'), _('Remove line'), wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT)

        ret = dlg.ShowModal()
        if ret == wx.ID_NO:
            return

        idx = self._line_current.GetSelection()
        self.del_line(idx)

        self._fill_lines_ax()

    def del_line(self, idx:int):
        """ Delete a line """

        self.cur_ax_properties.del_line(idx)
        self.update_layout()

    def get_ax_idx(self, key:str | int | Axes= None) -> Axes:

        if key is None:
            return self.cur_ax, self._ax_current.GetSelection()

        if isinstance(key, str):
            if key in self.ax_dict:
                return self.ax_dict[key], list(self.ax_dict.keys()).index(key)
            else:
                logging.warning('Key not found')
                return None
        elif isinstance(key, int):
            if key >= 0 and key < len(self.ax):
                return self.ax[key], key
            else:
                logging.warning('Index out of range')
                return None
        elif isinstance(key, Axes):
            return key, list(self.ax_dict.values()).index(key)

    def plot(self, x:np.ndarray, y:np.ndarray, ax:Axes | int | str= None, **kwargs):
        """ Plot x, y on the current ax or on the ax specified

        :param x: x values
        :param y: y values
        :param ax: ax to plot on
        :param kwargs: kwargs for the plot (same as matplotlib.pyplot.plot)
        """

        ax, idx_ax = self.get_ax_idx(ax)

        ax.plot(x, y, **kwargs)

        new_props = Matplolib_line_properties(ax.get_lines()[-1], self._axes_properties[idx_ax])

        if self.wx_exists:
            new_props.add_props_to_sizer(self._collaps_pane.GetPane(), self._sizer_grid_props)

        ax_prop:Matplotlib_ax_properties = self._axes_properties[idx_ax]
        ax_prop._lines.append(new_props)
        ax_prop.get_properties()

        if self.wx_exists:
            if ax == self.cur_ax:
                self._line_current.SetItems([line.get_label() for line in ax.get_lines()])
                self._line_current.SetSelection(len(ax.get_lines())-1)

        self.fig.tight_layout()
        self.fig.canvas.draw()
        self.update_layout()

    def scatter(self, x:np.ndarray, y:np.ndarray, ax:Axes | int | str= None, **kwargs):
        """ Scatter Plot x, y on the current ax or on the ax specified

        :param x: x values
        :param y: y values
        :param ax: ax to plot on
        :param kwargs: kwargs for the plot (same as matplotlib.pyplot.plot)
        """

        ax, idx_ax = self.get_ax_idx(ax)

        ax.scatter(x, y, **kwargs)

        # new_props = Matplolib_line_properties(ax.get_lines()[-1], self._axes_properties[idx_ax])

        # if self.wx_exists:
        #     new_props.add_props_to_sizer(self._collaps_pane.GetPane(), self._sizer_grid_props)

        ax_prop:Matplotlib_ax_properties = self._axes_properties[idx_ax]
        # ax_prop._lines.append(new_props)
        ax_prop.get_properties()

        if self.wx_exists:
            if ax == self.cur_ax:
                self._line_current.SetItems([line.get_label() for line in ax.get_lines()])
                self._line_current.SetSelection(len(ax.get_lines())-1)

        self.fig.tight_layout()
        self.fig.canvas.draw()
        self.update_layout()

    def violinplot(self, dataset:np.ndarray, position:np.ndarray=None, ax:Axes | int | str= None, **kwargs):
        """ Plot x, y on the current ax or on the ax specified

        :param x: x values
        :param y: y values
        :param ax: ax to plot on
        :param kwargs: kwargs for the plot (same as matplotlib.pyplot.plot)
        """

        ax, idx_ax = self.get_ax_idx(ax)

        ax.violinplot(dataset, position, **kwargs)

        # new_props = Matplolib_line_properties(ax.get_lines()[-1], self._axes_properties[idx_ax])

        # if self.wx_exists:
        #     new_props.add_props_to_sizer(self._collaps_pane.GetPane(), self._sizer_grid_props)

        # ax_prop:Matplotlib_ax_properties = self._axes_properties[idx_ax]
        # ax_prop._lines.append(new_props)
        # ax_prop.get_properties()

        # if self.wx_exists:
        #     if ax == self.cur_ax:
        #         self._line_current.SetItems([line.get_label() for line in ax.get_lines()])
        #         self._line_current.SetSelection(len(ax.get_lines())-1)

        self.fig.tight_layout()
        self.fig.canvas.draw()
        self.update_layout()


    def to_dict(self) -> dict:
        """ properties to dict """

        ret = {}
        if self.wx_exists:
            ret['frame_name'] = self.GetName()
            ret['frame_size_x'] = self.GetSize()[0]
            ret['frame_size_y'] = self.GetSize()[1]

        ret['layout'] = self._layout
        ret['fig'] = self._fig_properties.to_dict()
        ret['axes'] = [ax.to_dict() for ax in self._axes_properties]

        return ret

    def from_dict(self, props:dict):
        """ properties from dict """

        if 'layout' not in props:
            logging.error('No layout found in properties')
            return

        self.apply_layout(props['layout'])
        self._fig_properties.from_dict(props['fig'])
        for ax_props, ax in zip(props['axes'], self._axes_properties):
            ax:Matplotlib_ax_properties
            ax.from_dict(ax_props)


        if self.wx_exists:
            for ax_props, ax in zip(props['axes'], self._axes_properties):
                for line in ax._lines:
                    line.add_props_to_sizer(self._collaps_pane.GetPane(), self._sizer_grid_props)

            if 'frame_name' in props:
                self.SetName(props['frame_name'])
            if 'frame_size_x' in props and 'frame_size_y' in props:
                self.SetSize(props['frame_size_x'], props['frame_size_y'])

            self.Layout()

        return self

    def serialize(self):
        """ Serialize the properties """

        return json.dumps(self.to_dict(), indent=4)

    def deserialize(self, props:str):
        """ Deserialize the properties """

        self.from_dict(json.loads(props))

    def save(self, filename:str):

        with open(filename, 'w') as f:
            f.write(self.serialize())

    def load(self, filename:str):

        with open(filename, 'r') as f:
            self.deserialize(f.read())

    def save_image(self, filename:str, dpi:int= 100):

        self.fig.savefig(filename, dpi= dpi)

    def set_x_bounds(self, xmin:float, xmax:float, ax:Axes | int | str= None):

        ax, idx_ax = self.get_ax_idx(ax)

        ax.set_xlim(xmin, xmax)
        self._axes_properties[idx_ax].get_properties()

        self.fig.tight_layout()
        self._canvas.draw()

    def set_y_bounds(self, ymin:float, ymax:float, ax:Axes | int | str= None):

        ax, idx_ax = self.get_ax_idx(ax)

        ax.set_ylim(ymin, ymax)
        self._axes_properties[idx_ax].get_properties()

        self.fig.tight_layout()
        self._canvas.draw()
class Matplotlib_figure_properties():

    def __init__(self, parent:Matplotlib_Figure = None, fig:Figure = None) -> None:

        self.wx_exists = wx.App.Get() is not None

        self.parent = parent
        self._myprops = None
        self._fig:Figure = None
        self._axes = None

        self.title = 'Figure'
        self.size_width = 8
        self.size_height = 6
        self.dpi = 100
        self._filename = None

        self.set_fig(fig)
        self._set_props()

    def set_fig(self, fig:Figure):

        self._fig = fig

        if fig is None:
            return

        self._axes:list[Matplotlib_ax_properties] = [Matplotlib_ax_properties(ax) for ax in fig.get_axes()]
        self.get_properties()

        return self

    def _set_props(self):
        """ Set the properties UI """

        if self._myprops is not None:
            return

        self._myprops = Wolf_Param(title='Figure properties', w= 500, h= 400, to_read= False, ontop= False, init_GUI= False)

        self._myprops.set_callbacks(None, self.destroyprop)

        # self._myprops.hide_selected_buttons()

        self._myprops.addparam('Draw','Title',self.title,'String','SupTitle of the figure')
        self._myprops.addparam('Draw','Width',self.size_width,'Float','Width in inches')
        self._myprops.addparam('Draw','Height',self.size_height,'Float','Height in inches')
        self._myprops.addparam('Draw','DPI',self.dpi,'Integer','DPI - Dots per inch')
        self._myprops.addparam('Draw','Filename',self._filename,'File','Filename')

        self._myprops.Populate()

        # self._myprops.Layout()
        # self._myprops.SetSizeHints(500,500)

    def populate(self):
        """ Populate the properties UI """

        if self._myprops is None:
            self._set_props()

        self._myprops[('Draw','Title')] = self.title
        self._myprops[('Draw','Width')] = self.size_width
        self._myprops[('Draw','Height')] = self.size_height
        self._myprops[('Draw','DPI')] = self.dpi
        self._myprops[('Draw','Filename')] = self._filename

        self._myprops.Populate()

    def ui(self):
        """ Create the properties UI """

        if not self.wx_exists:
            return

        if self._myprops is not None:
            self._myprops.CenterOnScreen()
            self._myprops.Raise()
            self._myprops.Show()
            return

        self._set_props()
        self._myprops.Show()

        self._myprops.SetTitle(_('Figure properties'))

        icon = wx.Icon()
        icon_path = Path(__file__).parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        self._myprops.SetIcon(icon)

        self._myprops.Center()

        self._myprops.Raise()

    def destroyprop(self):
        self._myprops=None

    def fill_property(self):

        if self._myprops is None:
            logging.warning('Properties UI not found')
            return

        self._myprops.apply_changes_to_memory()

        self.title = self._myprops[('Draw','Title')]
        self.size_width = self._myprops[('Draw','Width')]
        self.size_height = self._myprops[('Draw','Height')]
        self.dpi = self._myprops[('Draw','DPI')]
        self._filename = self._myprops[('Draw','Filename')]

        self.set_properties()

    def set_properties(self, fig:Figure = None):

        if fig is None:
            fig = self._fig

        if self.size_height == 0 or self.size_width == 0:
            logging.warning('Size is 0')
            return

        fig.set_dpi(self.dpi)
        fig.set_size_inches(self.size_width, self.size_height)
        fig.suptitle(self.title)
        fig.tight_layout()

        fig.canvas.draw()

        self.get_properties()

    def get_properties(self, fig:Figure = None):

        if fig is None:
            fig = self._fig

        self.title = ''
        self.size_width, self.size_height = fig.get_size_inches()
        self.dpi = fig.get_dpi()

    def to_dict(self) -> str:
        """ properties to dict """

        return {'title':self.title if self.title != 'Figure' else '',
                'size_width':self.size_width,
                'size_height':self.size_height,
                'dpi':self.dpi}

    def from_dict(self, props:dict):
        """ properties from dict """

        keys = ['title', 'size_width', 'size_height', 'dpi']

        for key in keys:
            try:
                setattr(self, key, props[key])
            except:
                logging.warning('Key not found in properties dict')
                pass

        self.set_properties()

        return self

    def add_props_to_sizer(self, frame:wx.Frame, sizer:wx.BoxSizer):
        """ Add the properties to a sizer """

        self._myprops.ensure_prop(frame, show_in_active_if_default=True, height=300)
        sizer.Add(self._myprops.prop, proportion= 1, flag= wx.EXPAND)
        self._myprops.prop.Hide()

        for ax in self._axes:
            ax.add_props_to_sizer(frame, sizer)

        pass

    def show_props(self):
        """ Show the properties """

        self._myprops.prop.Show()

    def hide_props(self):
        """ Hide the properties """

        self._myprops.prop.Hide()


COLORS_MPL = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w', 'blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black', 'white', 'orange']