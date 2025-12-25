"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
import sys
try:
    from OpenGL.GL import *
except:
    msg=_('Error importing OpenGL library')
    msg+=_('   Python version : ' + sys.version)
    msg+=_('   Please check your version of opengl32.dll -- conflict may exist between different files present on your desktop')
    raise Exception(msg)

import math
from shapely.geometry import Point, LineString, MultiPoint
from os.path import exists
import wx
import re
import logging
from scipy.spatial import KDTree
from pathlib import Path
from typing import Literal, Union
from shapely.geometry import Polygon
from enum import Enum

from .PyParams import Wolf_Param, key_Param, Type_Param, new_json
from .PyTranslate import _
from .drawing_obj import Element_To_Draw
from .textpillow import Text_Image, Text_Infos, Font_Priority
from .wolf_texture import Text_Image_Texture

def getRGBfromI(rgbint:int):
    """ Convert integer to RGB """

    if isinstance(rgbint, tuple):
        return rgbint[0], rgbint[1], rgbint[2]
    elif isinstance(rgbint, list):
        return rgbint[0], rgbint[1], rgbint[2]
    elif isinstance(rgbint, int):
        blue = rgbint & 255
        green = (rgbint >> 8) & 255
        red = (rgbint >> 16) & 255
        return red, green, blue
    else:
        logging.error('Error in getRGBfromI')
        return 0, 0, 0

def getIfromRGB(rgb:Union[list, tuple]):
    """ Convert RGB to integer """

    red = int(rgb[0])
    green = int(rgb[1])
    blue = int(rgb[2])
    RGBint = (red << 16) + (green << 8) + blue
    return RGBint


def circle(x: float, y: float, r: float, numseg: int = 20):
    glBegin(GL_POLYGON)
    for ii in range(numseg + 1):
        theta = 2.0 * 3.1415926 * float(ii) / float(numseg)
        x1 = r * math.cos(theta)
        y1 = r * math.sin(theta)
        glVertex2f(x + x1, y + y1)
    glEnd()


def cross(x: float, y: float, r: float):
    glBegin(GL_LINES)
    glVertex2f(x - r, y)
    glVertex2f(x + r, y)
    glEnd()
    glBegin(GL_LINES)
    glVertex2f(x, y - r)
    glVertex2f(x, y + r)
    glEnd()


def quad(x: float, y: float, r: float):
    glBegin(GL_QUADS)
    glVertex2f(x - r, y - r)
    glVertex2f(x + r, y - r)
    glVertex2f(x + r, y + r)
    glVertex2f(x - r, y + r)
    glEnd()

class Cloud_Styles(Enum):
    POINT  = 0
    CIRCLE = 1
    CROSS  = 2
    QUAD   = 3

class wolfvertex:
    """Vertex WOLF - 3 coordonnées + valeurs associées dans un dictionnaire"""

    x: float
    y: float
    z: float
    values: dict = None

    def __init__(self, x:float, y:float, z:float=-99999.) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.in_use = True
        self.values = None

    def rotate(self, angle:float, center:tuple):
        """ Rotate the vertex

        :param angle: angle in radians (positive for counterclockwise)
        :param center: center of the rotation (x, y)
        """

        x = self.x - center[0]
        y = self.y - center[1]

        x1 = x * math.cos(angle) - y * math.sin(angle)
        y1 = x * math.sin(angle) + y * math.cos(angle)

        self.x = x1 + center[0]
        self.y = y1 + center[1]

    def as_shapelypoint(self):
        """ Return a shapely Point """

        return Point(self.getcoords())

    def copy(self):
        """ Return a copy of the vertex """

        return wolfvertex(self.x, self.y, self.z)

    def getcoords(self):
        """
        Return the coordinates as a numpy array
        """

        return np.array([self.x, self.y, self.z])

    def dist3D(self, v:"wolfvertex") -> float:
        """
        Return the 3D distance to another vertex

        :param v: vertex to compare
        """

        v = self.getcoords() - v.getcoords()
        return np.sqrt(np.inner(v, v))

    def dist2D(self, v:"wolfvertex") -> float:
        """
        Return the 2D distance to another vertex

        :param v: vertex to compare
        """

        v = self.getcoords()[0:2] - v.getcoords()[0:2]
        return np.sqrt(np.inner(v, v))

    def addvalue(self, id, value):
        """
        Add a value to the vertex

        :param id: key of the value
        :param value: value to add
        """

        if self.values is None:
            self.values = {}
        self.values[id] = value

    def add_value(self, id, value):
        """
        Add a set of values to the vertex

        :param id: key of the value
        :param value: value to add
        """

        self.addvalue(id, value)

    def add_values(self, values:dict):
        """
        Add a set of values to the vertex

        :param values: dictionary of values to add
        """

        if self.values is None:
            self.values = {}
        for key, value in values.items():
            self.values[key] = value

    def getvalue(self, id):
        """
        Return a value from the vertex

        :param id: key of the value
        """

        if not self.values is None:
            if id in self.values.keys():
                return self.values[id]
            else:
                return None

    def get_value(self, id):
        """
        Return a set of values from the vertex

        :param id: key of the value
        """

        return self.getvalue(id)

    def get_values(self, ids:list) -> dict:
        """
        Return a set of values from the vertex
        """

        ret = {}
        for id in ids:
            if id in self.values.keys():
                ret[id] = self.values[id]

        return ret

    def limit2bounds(self, bounds=None):
        """
        Limit the vertex to a set of bounds

        :param bounds: [[xmin, xmax], [ymin, ymax]] -- floats
        """

        if bounds is None:
            return

        self.x = max(self.x, bounds[0][0])
        self.x = min(self.x, bounds[0][1])
        self.y = max(self.y, bounds[1][0])
        self.y = min(self.y, bounds[1][1])

    def is_like(self, v:"wolfvertex", tol:float=1.e-6):
        """
        Return True if the vertex is close to another one

        :param v: vertex to compare
        :param tol: tolerance
        """

        if abs(self.x - v.x) < tol and abs(self.y - v.y) < tol and abs(self.z - v.z) < tol:
            return True
        else:
            return False

class cloudproperties:
    """
    Properties of a cloud of vertices

    """

    used: bool

    color: int
    width: int
    style: int
    alpha: int
    filled: bool
    legendvisible: bool
    transparent: bool
    flash: bool

    legendtext: str
    legendrelpos: int
    legendx: float
    legendy: float

    legendbold: bool
    legenditalic: bool
    legendunderlined: bool
    legendfontname = str
    legendfontsize: int
    legendcolor: int
    legendpriority:int
    legendorientation:int
    legendwidth:int
    legendheight:int

    extrude: bool = False

    myprops: Wolf_Param = None

    def __init__(self, lines=[], parent:"cloud_vertices"=None) -> None:

        self.parent = parent

        if len(lines) > 0:
            pass
            # line1=lines[0].split(',')
            # line2=lines[1].split(',')

            # self.color=int(line1[0])
            # self.width=int(line1[1])
            # self.style=int(line1[2])
            # self.filled=line1[4]=='#TRUE#'
            # self.legendvisible=line1[5]=='#TRUE#'
            # self.transparent=line1[6]=='#TRUE#'
            # self.alpha=int(line1[7])
            # self.flash=line1[8]=='#TRUE#'

            # self.legendtext=line2[0]
            # self.legendrelpos=int(line2[1])
            # self.legendx=float(line2[2])
            # self.legendy=float(line2[3])
            # self.legendbold=line2[4]=='#TRUE#'
            # self.legenditalic=line2[5]=='#TRUE#'
            # self.legendfontname=str(line2[6])
            # self.legendfontsize=int(line2[7])
            # self.legendcolor=int(line2[8])
            # self.legendunderlined=line2[9]=='#TRUE#'

            # self.used=lines[2]=='#TRUE#'
        else:
            self.color = 0
            self.width = 10
            self.style = 0
            self.filled = False
            self.legendvisible = False
            self.transparent = False
            self.alpha = 0
            self.flash = False

            self.legendtext = ''
            self.legendrelpos = 5
            self.legendx = 0.
            self.legendy = 0.
            self.legendbold = False
            self.legenditalic = False
            self.legendfontname = 'Arial'
            self.legendfontsize = 10
            self.legendcolor = 0
            self.legendunderlined = False
            self.legendpriority = Font_Priority.FONTSIZE.value
            self.legendorientation = 0
            self.legendwidth = 100
            self.legendheight = 100

            self.used = True
        pass

    def fill_property(self):

        self.color = getIfromRGB(self.myprops[('Draw', 'Color')])
        self.width = self.myprops[('Draw', 'Width')]
        self.style = self.myprops[('Draw', 'Style')]
        self.filled = self.myprops[('Draw', 'Filled')]
        self.transparent = self.myprops[('Draw', 'Transparent')]
        self.alpha = self.myprops[('Draw', 'Alpha')]
        self.flash = self.myprops[('Draw', 'Flash')]

        self.legendvisible = self.myprops[('Legend', 'Visible')]
        self.legendtext = self.myprops[('Legend', 'Text')]
        self.legendrelpos = self.myprops[('Legend', 'Relative position')]
        self.legendx = self.myprops[('Legend', 'X')]
        self.legendy = self.myprops[('Legend', 'Y')]
        self.legendbold = self.myprops[('Legend', 'Bold')]
        self.legenditalic = self.myprops[('Legend', 'Italic')]
        self.legendfontname = self.myprops[('Legend', 'Font name')]
        self.legendfontsize = self.myprops[('Legend', 'Font size')]
        self.legendcolor = getIfromRGB(self.myprops[('Legend','Color')])
        self.legendunderlined = self.myprops[('Legend', 'Underlined')]

        self.legendorientation = self.myprops[('Legend', 'Orientation')]
        self.legendwidth = self.myprops[('Legend', 'Width')]
        self.legendheight = self.myprops[('Legend', 'Height')]
        self.legendpriority = self.myprops[('Legend', 'Priority')]

        self.parent.forceupdategl = True
        # self.parent.initialiazed_textures = False

        if self.parent.mapviewer is not None:
            self.parent.mapviewer.Refresh()

    def defaultprop(self):
        """
        Default properties

        """
        if self.myprops is None:
            self.myprops = Wolf_Param(title='Cloud Properties', to_read=False, force_even_if_same_default=True)
            self.myprops.hide_selected_buttons()
            self.myprops._callbackdestroy = self.destroyprop
            self.myprops._callback = self.fill_property
            self.myprops.saveme.Disable()
            self.myprops.loadme.Disable()
            self.myprops.reloadme.Disable()

        self.myprops.addparam('Draw', 'Color', getRGBfromI(0), Type_Param.Color, 'Drawing color', whichdict='Default')
        self.myprops.addparam('Draw', 'Width', 10, Type_Param.Float, 'Drawing width', whichdict='Default')

        jsonstr = new_json({_('Point'):Cloud_Styles.POINT.value, _('Circle'):Cloud_Styles.CIRCLE.value, _('Cross'):Cloud_Styles.CROSS.value, _('Quad'):Cloud_Styles.QUAD.value})

        self.myprops.addparam('Draw', 'Style', 0, Type_Param.Integer, 'Drawing style', whichdict='Default', jsonstr=jsonstr)

        self.myprops.addparam('Draw', 'Filled', False, Type_Param.Logical, '', whichdict='Default')
        self.myprops.addparam('Draw', 'Transparent', False, Type_Param.Logical, '', whichdict='Default')
        self.myprops.addparam('Draw', 'Alpha', 0, Type_Param.Integer, 'Transparent intensity', whichdict='Default')
        self.myprops.addparam('Draw', 'Flash', False, Type_Param.Logical, '', whichdict='Default')

        self.myprops.addparam('Legend', 'Visible', False, Type_Param.Logical, '', whichdict='Default')
        self.myprops.addparam('Legend', 'Text', '', Type_Param.String, '', whichdict='Default')


        #1--4--7
        #|  |  |
        #2--5--8
        #|  |  |
        #3--6--9
        jsonstr = new_json({_('Left'): 2, _('Right'):8, _('Top'):4, _('Bottom'):6, _('Center'):5, _('Top left'):1, _('Top right'):7, _('Bottom left'):3, _('Bottom right'):9}, _('Relative position of the legend'))
        self.myprops.addparam('Legend','Relative position',5,'Integer','',whichdict='Default', jsonstr=jsonstr)

        self.myprops.addparam('Legend', 'X', 0, 'Float', '', whichdict='Default')
        self.myprops.addparam('Legend', 'Y', 0, 'Float', '', whichdict='Default')
        self.myprops.addparam('Legend', 'Bold', False, Type_Param.Logical, '', whichdict='Default')
        self.myprops.addparam('Legend', 'Italic', False, Type_Param.Logical, '', whichdict='Default')
        self.myprops.addparam('Legend', 'Font name', 'Arial', Type_Param.String, '', whichdict='Default')
        self.myprops.addparam('Legend', 'Font size', 10, Type_Param.Integer, '', whichdict='Default')
        self.myprops.addparam('Legend', 'Color', getRGBfromI(0), Type_Param.Color, '', whichdict='Default')
        self.myprops.addparam('Legend', 'Underlined', False, Type_Param.Logical, '', whichdict='Default')

        self.myprops.addparam('Legend', 'Width', 100, 'Integer', _('Width of the legend [m]'), whichdict='Default')
        self.myprops.addparam('Legend', 'Height', 100, 'Integer', _('Height of the legend [m]'), whichdict='Default')
        self.myprops.addparam('Legend', 'Orientation', 0, 'Integer', _('Orientation of the legend [Degree]'), whichdict='Default')

        jsonstr = new_json({_('Width'): 1, _('Height'):2, _('Fontsize'):3}, _('Priority will be respected during the OpenGL plot rendering'))
        self.myprops.addparam('Legend','Priority', 3 ,'Integer', whichdict='Default', jsonstr=jsonstr)

    def destroyprop(self):
        self.myprops = None

    def show(self):
        self.defaultprop()

        self.myprops[('Draw', 'Color')]         = getRGBfromI(self.color)
        self.myprops[('Draw', 'Width')]         = self.width
        self.myprops[('Draw', 'Style')]         = self.style
        self.myprops[('Draw', 'Filled')]        = self.filled
        self.myprops[('Draw', 'Transparent')]   = self.transparent
        self.myprops[('Draw', 'Alpha')]         = self.alpha
        self.myprops[('Draw', 'Flash')]         = self.flash

        self.myprops[('Legend', 'Visible')]     = self.legendvisible
        self.myprops[('Legend', 'Text')]        = self.legendtext
        self.myprops[('Legend', 'Relative position')] = self.legendrelpos
        self.myprops[('Legend', 'X')]           = self.legendx
        self.myprops[('Legend', 'Y')]           = self.legendy
        self.myprops[('Legend', 'Bold')]        = self.legendbold
        self.myprops[('Legend', 'Italic')]      = self.legenditalic
        self.myprops[('Legend', 'Font name')]   = self.legendfontname
        self.myprops[('Legend', 'Font size')]   = self.legendfontsize
        self.myprops[('Legend', 'Color')]       = getRGBfromI(self.legendcolor)
        self.myprops[('Legend', 'Underlined')]  = self.legendunderlined

        self.myprops[('Legend', 'Width')]       = self.legendwidth
        self.myprops[('Legend', 'Height')]      = self.legendheight
        self.myprops[('Legend', 'Orientation')] = self.legendorientation
        self.myprops[('Legend', 'Priority')]    = self.legendpriority

        self.myprops.Populate()
        self.myprops.Show()


class cloud_vertices(Element_To_Draw):
    """
    Scatter points with associated values

    Accepted formats : dxf, ascii

    Ascii separator : tabulation '\t', semicolon ';'

    'dxf' type is automatically finded based on file extension otherwise, ascii file is supposed.

    If header exists in the first line of the file, you have to mention it by header=True in initialization.

    Total number of columns (nb) is important :
        - if nb >3 : the file must contain a header
        - if header[2].lower() == 'z', the file contains XYZ coordinates, otherwise all columns >1 are interpreted as values associated to XY

    Number os values = nb - (2 or 3) depending if Z coordinate exists

    Data are stored in Python dictionnary :
        - 'vertex' : XY or XYZ

    Each value is accessible through its headname as key :
        - 'headname1' : value with headname1
        - 'headname2' : value with headname2
        - 'headnamen' : value with headnamen

    For more information, see 'readfile' or 'import_from_dxf'

    """
    filename: str
    myvertices: dict[int, dict['vertex':wolfvertex, str:float]]

    xbounds: tuple
    ybounds: tuple
    zbounds: tuple

    myprop: cloudproperties
    mytree : KDTree

    def __init__(self,
                 fname: Union[str, Path] = '',
                 fromxls: str = '',
                 header: bool = False,
                 toload=True,
                 idx: str = '',
                 plotted: bool = True,
                 mapviewer=None,
                 need_for_wx: bool = False,
                 bbox:Polygon = None,
                 dxf_imported_elts = ['MTEXT', 'INSERT']) -> None:
        """
        Init cloud of vertices

        :param fname: file name
        :param fromxls: string read from xls file and to be parsed
        :param header: header in file (first line with column names)
        :param toload: load file at init
        :param idx: identifier -- see Element_To_Draw
        :param plotted: plot at init -- see Element_To_Draw
        :param mapviewer: mapviewer -- see Element_To_Draw
        :param need_for_wx: see Element_To_Draw
        """

        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self.myvertices = {}
        self.filename = str(fname)

        self.loaded = False

        self._header = header

        self.gllist = 0
        self.forceupdategl = False
        self.ongoing = False

        self.xbounds = (0., 0.)
        self.ybounds = (0., 0.)
        self.zbounds = (0., 0.)

        self.myprop = cloudproperties(parent=self)

        self.mytree = None

        # self.initialiazed_textures = False

        if self.filename != '':
            if toload:
                if Path(fname).suffix.lower() == '.dxf':
                    self.import_from_dxf(self.filename, imported_elts=dxf_imported_elts)
                elif Path(fname).suffix.lower() == '.shp':
                    self.import_from_shapefile(self.filename, bbox=bbox)
                else:
                    self.readfile(self.filename, header)

    def __getitem__(self, key):

        return self.myvertices[key]

    def create_kdtree(self):
        """
        Set a Scipy KDTree structure based on a copy of the vertices
        """

        xyz = self.get_xyz()
        self.mytree = KDTree(xyz)

    def find_nearest(self, xyz:np.ndarray | list, nb:int =1):
        """
        Find nearest neighbors from Scipy KDTree structure based on a copy of the vertices.

        See : https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.query.html

        :param xyz: coordinates to find nearest neighbors -- shape (n, m) - where m is the number of coordinates (2 or 3)
        :param nb: number of nearest neighbors to find
        :return: list of distances, list of "Wolfvertex", list of elements stored in self.myvertices - or list of lists if xyz is a list of coordinates
        """

        if isinstance(xyz, list):
            if len(xyz) > 0:
                if isinstance(xyz[0], float | int):
                    logging.warning(_('xyz is a list of floats -- converting to a list of lists'))
                    xyz = [xyz]

            xyz = np.array(xyz)

        try:
            keys = list(self.myvertices.keys())
            if self.mytree is None:
                self.create_kdtree()

            if xyz.shape[1] != self.mytree.m:
                logging.error(_('Error in find_nearest -- xyz must be a list or 2D array with {} columns').format(self.mytree.m))
                return None, None, None

            dist, ii = self.mytree.query(xyz, k=nb)

            if xyz.shape[0] == 1:
                if nb == 1:
                    return dist[0], self.myvertices[keys[ii[0]]]['vertex'], self.myvertices[keys[ii[0]]]
                else:
                    return dist[0], [self.myvertices[keys[curi]]['vertex'] for curi in ii[0]], [self.myvertices[keys[curi]] for curi in ii[0]]
            else:
                if nb == 1:
                    return dist, [self.myvertices[keys[curi]]['vertex'] for curi in ii], [self.myvertices[keys[curi]] for curi in ii]
                else:
                    return dist, [[self.myvertices[keys[curi]]['vertex'] for curi in curii] for curii in ii], [[self.myvertices[keys[curi]] for curi in curii] for curii in ii]

        except Exception as e:
            logging.error(_('Error in find_nearest -- {}').format(e))
            logging.error(_('Check your input data -- it must be a list or 2D array with 3 columns'))
            return None, None, None

    def init_from_nparray(self, array:np.ndarray):
        """
        Fill-in from nparray -- shape (n,3)
        """

        k = 0
        for curv in array:
            mv = wolfvertex(curv[0], curv[1], curv[2])
            self.myvertices[k] = {}
            self.myvertices[k]['vertex'] = mv
            k += 1

        self.xbounds = (np.min(array[:, 0]), np.max(array[:, 0]))
        self.ybounds = (np.min(array[:, 1]), np.max(array[:, 1]))
        self.loaded = True

    def check_plot(self):
        """ The cloud is plotted -- useful for mapviewer """

        self.plotted = True
        if not self.loaded:
            self.readfile(self.filename, self._header)
            self.loaded = True

    def uncheck_plot(self, unload=True):
        """ The cloud is not plotted -- useful for mapviewer """

        self.plotted = False

    def readfile(self, fname:str='', header: bool = False):
        """
        Reading an ascii file with or without header

        :param fname: (str) file name
        :param header: (bool) header in file (first line with column names)

        The separator is automatically detected among : tabulation, semicolon, space, comma.

        The file must contain at least 2 columns (X, Y) and may contain a third one (Z) and more (values).
        If values are present, they are stored in the dictionnary with their header name as key.
        """

        if fname != '':
            headers = None
            nbcols = 0
            zpresent = False
            nbvals = 0
            firstval = 0

            xmin = 1.e300
            xmax = -1.e300
            ymin = 1.e300
            ymax = -1.e300
            zmin = 1.e300
            zmax = -1.e300

            f = open(fname, 'r')
            content = f.read().splitlines()
            f.close()

            if header:
                curhead = content[0]
                content.pop(0)
                sep = ' '
                if '\t' in curhead:
                    # séparateur tabulation
                    sep = '\t'
                elif ';' in curhead:
                    # séparateur tabulation
                    sep = ';'
                elif ',' in curhead:
                    # séparateur espace
                    sep = ','
                elif ' ' in curhead:
                    # séparateur espace
                    sep = ' '
                headers = curhead.split(sep)
                nbcols = len(headers)
            else:
                curline = content[0]
                sep = ' '
                if '\t' in curline:
                    # séparateur tabulation
                    sep = '\t'
                elif ';' in curline:
                    # séparateur point-virgule
                    sep = ';'
                elif ',' in curline:
                    # séparateur virgule
                    sep = ','
                    curline = re.sub(' +', ' ', curline)
                elif ' ' in curline:
                    # séparateur espace
                    sep = ' '
                    curline = re.sub(' +', ' ', curline)

                curval = curline.split(sep)
                nbcols = len(curval)

                if not header:
                    try:
                        x = float(curval[0])
                        y = float(curval[1])
                        z = 0.
                        if nbcols > 2:
                            z = float(curval[2])
                    except ValueError as e:
                        logging.error(_('Error converting first row to float as "header" is set to False.'))
                        logging.error(_('Check your input file : ')+fname)
                        logging.info(_('Using the first row as header.'))
                        header = True
                        headers = curhead.split(sep)

            if nbcols < 2:
                logging.warning(_('Not enough values on one line -- Retry !!'))
                return
            elif nbcols > 3:
                if headers is None:
                    logging.warning(_('No headers -- Retry !!'))
                    return
                else:
                    if headers[2].lower() == 'z':
                        zpresent = True
                        nbvals = nbcols - 3
                        firstval = 3
                    else:
                        # on interprète la 3ème colonne comme valeur et non comme Z
                        zpresent = False
                        nbvals = nbcols - 2
                        firstval = 2
            elif nbcols == 3:
                if headers is None:
                    zpresent = True
                else:
                    if headers[2].lower() == 'z':
                        zpresent = True
                    else:
                        # on interprète la 3ème colonne comme valeur et non comme Z
                        zpresent = False
                        nbvals = 1
                        firstval = 2
            k = 0
            for curline in content:
                curline = re.sub(' +', ' ', curline)
                curval = curline.split(sep)

                x = float(curval[0])
                y = float(curval[1])
                z = 0
                if zpresent:
                    z = float(curval[2])

                curvert = wolfvertex(x, y, z)
                curdict = self.myvertices[k] = {}
                curdict['vertex'] = curvert

                xmin = min(x, xmin)
                xmax = max(x, xmax)
                ymin = min(y, ymin)
                ymax = max(y, ymax)
                zmin = min(z, zmin)
                zmax = max(z, zmax)

                if nbvals > 0:
                    for i in range(firstval, firstval + nbvals):
                        curdict[headers[i]] = curval[i]

                k += 1

            self.xbounds = (xmin, xmax)
            self.ybounds = (ymin, ymax)

            self.loaded = True

    def import_from_dxf(self, fn:str='', imported_elts=['MTEXT', 'INSERT']):
        """
        Importing DXF file using ezdxf library

        :param fn: file name (*.dxf)

        """
        if fn == '' or not exists(fn):
            logging.error(_('File not found : ')+fn)
            return

        import ezdxf

        # Lecture du fichier dxf et identification du modelspace
        logging.info(_('Reading DXF file : ')+fn)
        doc = ezdxf.readfile(fn)
        msp = doc.modelspace()

        logging.info(_('Number of entities : ')+str(len(msp)))
        logging.info(_('Number of layers : ')+str(len(doc.layers)))
        logging.info(_('Treating entities... '))

        # Bouclage sur les éléments du DXF
        k=0
        for e in msp:
            if doc.layers.get(e.dxf.layer).is_on():
                if e.dxftype() in imported_elts:
                    if e.dxftype() == "MTEXT" or e.dxftype()=='INSERT':
                        x = e.dxf.insert[0]
                        y = e.dxf.insert[1]
                        z = e.dxf.insert[2]

                        if z!=0.:
                            curvert = wolfvertex(x, y, z)
                            curdict = self.myvertices[k] = {}
                            curdict['vertex'] = curvert
                            k += 1

                    elif e.dxftype() == "POLYLINE":
                        # récupération des coordonnées
                        verts = [cur.dxf.location.xyz for cur in e.vertices]
                        for cur in verts:
                            curvert = wolfvertex(cur[0],cur[1],cur[2])
                            curdict = self.myvertices[k] = {}
                            curdict['vertex'] = curvert
                            k += 1

                    elif e.dxftype() == "LWPOLYLINE":
                        # récupération des coordonnées
                        verts = np.array(e.lwpoints.values)
                        verts = verts.reshape([verts.size // 5,5])[:,:2]   #  in ezdxf 1.3.5, the lwpoints.values attribute is a np.ndarray [n,5]
                        verts = np.column_stack([verts,[e.dxf.elevation]*len(verts)])

                        for cur in verts:
                            curvert = wolfvertex(cur[0],cur[1],cur[2])
                            curdict = self.myvertices[k] = {}
                            curdict['vertex'] = curvert
                            k += 1

                    elif e.dxftype() == "LINE":
                        # récupération des coordonnées
                        curvert = wolfvertex(e.dxf.start[0],e.dxf.start[1],e.dxf.start[2])
                        curdict = self.myvertices[k] = {}
                        curdict['vertex'] = curvert
                        k += 1

                        curvert = wolfvertex(e.dxf.end[0],e.dxf.end[1],e.dxf.end[2])
                        curdict = self.myvertices[k] = {}
                        curdict['vertex'] = curvert
                        k += 1

                else:
                    logging.warning(_('DXF element not supported/ignored : ') + e.dxftype())
            else:
                logging.info(_('Layer {} is off'.format(e.dxf.layer)))

        self.find_minmax(True)
        self.loaded = True

        logging.info(_('Number of imported points : ')+str(k))
        logging.info(_('Importation finished'))

        return k

    def import_from_shapefile(self, fn:str='', targetcolumn:str = 'X1_Y1_Z1', bbox:Polygon = None):
        """
        Importing Shapefile using geopandas library

        :param fn: file name
        :param targetcolumn: column name to be used for XYZ coordinates -- 'X1_Y1_Z1' is used by SPW-ARNE-DCENN

        """

        if fn == '' or not exists(fn):
            logging.error(_('File not found : ')+fn)
            return

        import geopandas as gpd

        # read data
        gdf:gpd.GeoDataFrame = gpd.read_file(fn, bbox=bbox)

        if gdf is None:
            logging.error(_('Error during import of shapefile : ')+fn)
            return

        # check if the file is empty
        if gdf.empty:
            logging.error(_('Imported shapefile is empty : ')+fn)
            return

        #check if the number of lines is > 0
        if len(gdf) == 0:
            logging.error(_('Imported shapefile is empty : ')+fn)
            return

        # Bouclage sur les éléments du Shapefile
        if targetcolumn in gdf.columns:
            k=0
            for index, row in gdf.iterrows():
                x, y, z = row[targetcolumn].split(',')
                x = float(x)
                y = float(y)
                z = float(z)

                curvert = wolfvertex(x, y, z)
                curdict = self.myvertices[k] = {}
                curdict['vertex'] = curvert
                k += 1

        elif 'geometry' in gdf.columns:

            try:
                for k, (xx,yy) in enumerate(zip(gdf.geometry.x, gdf.geometry.y)):
                    curvert = wolfvertex(xx, yy)
                    curdict = self.myvertices[k] = {}
                    curdict['vertex'] = curvert

            except Exception as e:
                logging.error(_('Geometry not found (MultiPoint or Point) -- Please check your shapefile : ')+fn)
                logging.error(e)
                return

        else:

            if self.wx_exists:

                dlg = wx.SingleChoiceDialog(None, _('Choose the column to be used for XYZ coordinates'), _('Column choice'), gdf.columns)
                if dlg.ShowModal() == wx.ID_OK:
                    targetcolumn = dlg.GetStringSelection()
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return
            else:
                logging.error(_('Column not found : ')+targetcolumn)
                return

            try:

                k=0
                for index, row in gdf.iterrows():
                    x, y, z = row[targetcolumn].split(',')
                    x = float(x)
                    y = float(y)
                    z = float(z)

                    curvert = wolfvertex(x, y, z)
                    curdict = self.myvertices[k] = {}
                    curdict['vertex'] = curvert
                    k += 1
            except:
                logging.error(_('Error during import of shapefile : ')+fn)
                return

        self.find_minmax(True)
        self.loaded = True

        logging.info(_('Number of imported points : ')+str(k))

        return k

    def add_vertex(self, vertextoadd: wolfvertex = None, id=None, cloud: dict = None):
        """ Add a vertex to the cloud

        :param vertextoadd: vertex to add
        :param id: id of the vertex -- if None, the id is the length of the cloud
        :param cloud: cloud of vertices to add -- wolfvertex instances are pointed not copied

        """

        if vertextoadd is not None:
            curid = id
            if curid is None:
                curid = len(self.myvertices)
            self.myvertices[curid] = {}
            self.myvertices[curid]['vertex'] = vertextoadd
            self._updatebounds(vertextoadd)

        if cloud is not None:
            for id, item in cloud.items():
                self.myvertices[id] = item

            self._updatebounds(newcloud=cloud)
        pass

    def remove_vertex(self, id: int):
        """ Remove a vertex from the cloud

        :param id: id of the vertex to remove
        """

        if id in self.myvertices:
            del self.myvertices[id]
            self._updatebounds()
        else:
            logging.warning(_('Vertex with id {} not found in the cloud').format(id))

    def add_vertices(self, vertices:list[wolfvertex]):
        """ Add a list of vertices to the cloud """

        first_id = len(self.myvertices)
        for curid, curvert in enumerate(vertices):
            self.myvertices[first_id + curid] = {}
            self.myvertices[first_id + curid]['vertex'] = curvert
            self._updatebounds(curvert)

    def get_vertices(self):
        """ Return the vertices as a list """

        return [self.myvertices[item]['vertex'] for item in self.myvertices]

    # def _create_textures(self):
    #     """ Create textures for the cloud """

    #     mapviewer = self.get_mapviewer()

    #     for id, item in enumerate(self.myvertices):
    #         curvert = self.myvertices[item]['vertex']

    #         curtxt_infos = Text_Infos(self.myprop.legendpriority,
    #                                   (np.cos(self.myprop.legendorientation/180*np.pi),
    #                                    np.sin(self.myprop.legendorientation/180*np.pi)),
    #                                   self.myprop.legendfontname,
    #                                   self.myprop.legendfontsize,
    #                                   self.myprop.legendcolor,
    #                                   dimsreal=(self.myprop.legendwidth, self.myprop.legendheight)
    #                                   )

    #         self.myvertices[item]['texture'] = Text_Image_Texture(item, mapviewer, curtxt_infos, None, curvert.x, curvert.y)

    #     self.initialiazed_textures = True


    def plot_legend(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot OpenGL

        Legend is an image texture

        FIXME : to be improved
        """
        if self.get_mapviewer() is None:
            logging.warning(_('No mapviewer available for legend plot'))
            return

        if self.myprop.legendvisible:

            dx = xmax - xmin
            dy = ymax - ymin

            if dx > 50_000. or dy > 50_000.:
                logging.warning(_('Too large bounds for legend plot -- skipping'))
                return

            mapviewer = self.get_mapviewer()

            which_legend = self.myprop.legendtext

            for id, item in enumerate(self.myvertices):

                curvert = self.myvertices[item]['vertex']

                if curvert.x > xmin and curvert.x < xmax and curvert.y > ymin and curvert.y < ymax:

                    if which_legend == '':
                        text_legend = str(item)
                    elif which_legend == 'ID':
                        text_legend = str(id)
                    elif which_legend == 'X':
                        text_legend = str(curvert.x)
                    elif which_legend == 'Y':
                        text_legend = str(curvert.y)
                    elif which_legend == 'Z':
                        text_legend = str(curvert.z)
                    elif which_legend in self.myvertices[item]:
                        text_legend = self.myvertices[item][which_legend]
                    else:
                        text_legend = which_legend

                    r,g,b = getRGBfromI(self.myprop.legendcolor)

                    curtxt_infos = Text_Infos(self.myprop.legendpriority,
                                            (np.cos(self.myprop.legendorientation/180*np.pi),
                                            np.sin(self.myprop.legendorientation/180*np.pi)),
                                            self.myprop.legendfontname,
                                            self.myprop.legendfontsize,
                                            (r,g,b,255),
                                            dimsreal=(self.myprop.legendwidth, self.myprop.legendheight),
                                            relative_position=self.myprop.legendrelpos
                                            )

                    text = Text_Image_Texture(text_legend, mapviewer, curtxt_infos, None, curvert.x, curvert.y)

                    text.paint()

    def reset_listogl(self):
        """
        Reset the OpenGL list

        """

        if self.gllist != 0:
            glDeleteLists(self.gllist, 1)
            self.gllist = 0

        self.forceupdategl = True
        self.ongoing = False

    def plot(self, update:bool=False, *args, **kwargs):
        """
        OpenGL plot of the cloud of vertices

        FIXME : to be improved
        """

        if update or self.gllist == 0 or self.forceupdategl and not self.ongoing:
            curvert: wolfvertex
            self.ongoing = True

            color = self.myprop.color
            width = self.myprop.width
            style = self.myprop.style
            filled = self.myprop.filled

            if self.gllist != 0:
                glDeleteLists(self.gllist, 1)

            self.gllist = glGenLists(1)
            glNewList(self.gllist, GL_COMPILE)

            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            if filled:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

            if style == Cloud_Styles.POINT.value:
                glPointSize(width)
                rgb = getRGBfromI(color)
                glBegin(GL_POINTS)
                for id, item in enumerate(self.myvertices):
                    curvert = self.myvertices[item]['vertex']
                    glColor3ub(int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    glVertex2f(curvert.x, curvert.y)

                glEnd()
            elif style == Cloud_Styles.CIRCLE.value:
                glPointSize(1)
                rgb = getRGBfromI(color)
                for id, item in enumerate(self.myvertices):
                    curvert = self.myvertices[item]['vertex']
                    glColor3ub(int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    circle(curvert.x, curvert.y, width / 2.)

            elif style == Cloud_Styles.CROSS.value:
                glPointSize(1)
                rgb = getRGBfromI(color)
                for id, item in enumerate(self.myvertices):
                    curvert = self.myvertices[item]['vertex']
                    glColor3ub(int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    cross(curvert.x, curvert.y, width / 2)

            elif style == Cloud_Styles.QUAD.value:
                glPointSize(1)
                rgb = getRGBfromI(color)
                for id, item in enumerate(self.myvertices):
                    curvert = self.myvertices[item]['vertex']
                    glColor3ub(int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    quad(curvert.x, curvert.y, width / 2)

            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

            glEndList()
            self.forceupdategl = False
            self.ongoing = False
        else:
            glCallList(self.gllist)
            pass

        self.plot_legend(**kwargs)

    def show_properties(self):
        """ Show properties of the cloud """

        self.myprop.show()

    def _updatebounds(self, newvert: wolfvertex = None, newcloud: dict = None):
        """
        Update the bounds of the cloud

        :param newvert : (optional) vertex added to the cloud
        :param newcloud: (optional) cloud added to the cloud

        'newvert' or 'newcloud' can be passed as argument during add_vertex operation.
        In this way, the bounds are updated without going through all the vertices -> expected more rapid.

        """

        xmin = self.xbounds[0]
        xmax = self.xbounds[1]
        ymin = self.ybounds[0]
        ymax = self.ybounds[1]
        zmin = self.zbounds[0]
        zmax = self.zbounds[1]

        if not newvert is None:
            xmin = min(newvert.x, xmin)
            xmax = max(newvert.x, xmax)
            ymin = min(newvert.y, ymin)
            ymax = max(newvert.y, ymax)
            zmin = min(newvert.z, zmin)
            zmax = max(newvert.z, zmax)

            self.xbounds = (xmin, xmax)
            self.ybounds = (ymin, ymax)
            self.zbounds = (zmin, zmax)

        if not newcloud is None:
            for item in newcloud.values():
                curvert = item['vertex']
                xmin = min(curvert.x, xmin)
                xmax = max(curvert.x, xmax)
                ymin = min(curvert.y, ymin)
                ymax = max(curvert.y, ymax)
                zmin = min(curvert.z, zmin)
                zmax = max(curvert.z, zmax)

            self.xbounds = (xmin, xmax)
            self.ybounds = (ymin, ymax)
            self.zbounds = (zmin, zmax)

    def find_minmax(self, force=False):
        """
        Find the bounds of the cloud

        :param force: force the computation of the bounds

        """

        if force:
            self.xmin = 1.e300
            self.xmax = -1.e300
            self.ymin = 1.e300
            self.ymax = -1.e300
            self.zmin = 1.e300
            self.zmax = -1.e300

            # if no vertice or file not present -> return
            if len(self.myvertices) == 0 :
                return

            xyz = self.get_xyz()
            self.xmin = np.min(xyz[:,0])
            self.xmax = np.max(xyz[:,0])
            self.ymin = np.min(xyz[:,1])
            self.ymax = np.max(xyz[:,1])
            self.zmin = np.min(xyz[:,2])
            self.zmax = np.max(xyz[:,2])

            # for item in self.myvertices:
            #     curvert = self.myvertices[item]['vertex']

            #     x = curvert.x
            #     y = curvert.y
            #     z = curvert.z

            #     self.xmin = min(x, self.xmin)
            #     self.xmax = max(x, self.xmax)
            #     self.ymin = min(y, self.ymin)
            #     self.ymax = max(y, self.ymax)
            #     self.zmin = min(z, self.zmin)
            #     self.zmax = max(z, self.zmax)

            self.xbounds = (self.xmin, self.xmax)
            self.ybounds = (self.ymin, self.ymax)
            self.zbounds = (self.zmin, self.zmax)

            pass

    def get_xyz(self, key='vertex') -> np.ndarray:
        """
        Return the vertices as numpy array

        :param key: key to be used for the third column (Z) -- 'vertex' or any key in the dictionnary -- if 'vertex'', [[X,Y,Z]] are returned

        """

        if self._header:
            if key=='vertex':
                xyz = [[curvert['vertex'].x, curvert['vertex'].y, curvert['vertex'].z]  for curvert in self.myvertices.values()]
            else:
                xyz = [[curvert['vertex'].x, curvert['vertex'].y, float(curvert[key])]  for curvert in self.myvertices.values()]
        else:
            xyz = [[curvert['vertex'].x, curvert['vertex'].y, curvert['vertex'].z]  for curvert in self.myvertices.values()]
        return np.array(xyz)

    @property
    def has_values(self) -> bool:
        """
        Check if the cloud has values (other than X,Y,Z)
        """

        if self._header:
            return len(self.myvertices[0]) > 1
        else:
            return False

    @property
    def header(self) -> list[str]:
        """
        Return the headers of the cloud
        """

        if self._header:
            return list(self.myvertices[0].keys())
        else:
            return []

    def add_values_by_id_list(self, id:str, values:list[float]):
        """
        Add values to the cloud

        :param id: use as key for the values
        :param values: list of values to be added - must be the same length as number of vertices

        """

        if len(values) != len(self.myvertices):
            logging.warning(_('Number of values does not match the number of vertices -- Retry !!'))
            logging.info(_(('Number of vertices : ')+str(len(self.myvertices))))
            return

        for item, val in zip(self.myvertices.values(), values):
            item[id] = val

        self._header = True

    @property
    def xyz(self) -> np.ndarray:
        """
        Alias for get_xyz method
        """

        return self.get_xyz(key='vertex')

    @property
    def nbvertices(self) -> int:
        """
        Number of vertices in the cloud
        """

        return len(self.myvertices)

    def interp_on_array(self, myarray, key:str='vertex', method:Literal['linear', 'nearest', 'cubic'] = 'linear'):
        """
        Interpolation of the cloud on a 2D array

        :param myarray: WolfArray instance
        :param key: key to be used for the third column (Z) -- 'vertex' or any key in the dictionnary
        :param method: interpolation method -- 'linear', 'nearest', 'cubic'

        see interpolate_on_cloud method of WolfArray for more information

        """

        xyz = self.get_xyz(key)
        myarray.interpolate_on_cloud(xyz[:,:2], xyz[:,2], method)

    def iter_on_vertices(self):
        """ Iteration on vertices """

        for cur in self.myvertices.values():
            yield cur['vertex']

    def get_multipoint(self):
        """ Return the cloud as a Shapely MultiPoint """

        return MultiPoint([cur.as_shapelypoint() for cur in self.iter_on_vertices()])

    def projectontrace(self, trace, return_cloud:bool = True, proximity:float = 99999.):
        """
        Project the cloud onto a trace (type 'vector')

        :param trace: vector class
        :param return_cloud: return a cloud or the lists [s],[z]
        :param proximity: search distance for projection

        Return:
            if return_cloud:
                New cloud containing the position information on the trace and altitude (s,z)
            else:
                s,z: 2 lists of floats
        """

        # trace:vector
        tracels:LineString
        tracels = trace.asshapely_ls() # conversion en linestring Shapely

        if proximity == 99999.:
            # on garde tous les points

            all_s = [tracels.project(Point(cur['vertex'].x,cur['vertex'].y)) for cur in self.myvertices.values()] # Projection des points sur la trace et récupération de la coordonnées curviligne
            all_z = [cur['vertex'].z for cur in self.myvertices.values()]

        else:

            buffer = tracels.buffer(proximity) # buffer de la trace

            multipoints = self.get_multipoint() # conversion en multipoint Shapely

            mp = multipoints.intersection(buffer) # intersection avec le buffer

            all_s = [tracels.project(Point(cur.x,cur.y)) for cur in mp.geoms] # Projection des points sur la trace et récupération de la coordonnées curviligne
            all_z = [cur.z for cur in mp.geoms] # récupération de l'altitude

        new_dict = {}
        k=0
        for s,z in zip(all_s,all_z):
            new_dict[k] = {'vertex':wolfvertex(s,z)}
            k+=1

        if return_cloud:
            newcloud = cloud_vertices(idx=_('Projection on ')+trace.myname)
            newcloud.add_vertex(cloud=new_dict)

            return newcloud
        else:
            return all_s, all_z

    def plot_matplotlib(self, ax=None, **kwargs):
        """
        Plot the cloud using matplotlib

        :param ax: axis to plot on -- if None, a new figure is created
        :param kwargs: additional arguments for matplotlib

        """
        import matplotlib.pyplot as plt

        if ax is None:
            fig, ax = plt.subplots()

        x = [cur['vertex'].x for cur in self.myvertices.values()]
        y = [cur['vertex'].y for cur in self.myvertices.values()]

        ax.scatter(x, y, **kwargs)

        return fig, ax