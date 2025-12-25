"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

try:
    from osgeo import gdal, osr
    gdal.UseExceptions()
except ImportError as e:
    print(e)
    raise Exception(_('Error importing GDAL library'))

import os
import sys
import warnings

import numpy as np
import numpy.ma as ma

from typing import Union, Literal
from matplotlib.axis import Axis
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap
import math as m
import logging
import json
import tempfile
from pathlib import Path
from tqdm import tqdm

try:
    from OpenGL.GL import *
except:
    msg=_('Error importing OpenGL library')
    msg+=_('   Python version : ' + sys.version)
    msg+=_('   Please check your version of opengl32.dll -- conflict may exist between different files present on your desktop')
    raise Exception(msg)

import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.path as mpltPath
import re
import wx
from scipy.interpolate import interp2d, griddata
from scipy.ndimage import laplace, label, sum_labels
from shapely.geometry import Point, LineString, MultiLineString, Polygon, MultiPolygon, MultiPoint
from shapely.ops import linemerge, substring, polygonize_full
from shapely import contains, contains_properly, contains_xy, touches, prepare, destroy_prepared, is_prepared
from os.path import dirname,basename,join
import logging
from typing import Literal
from copy import deepcopy
from enum import Enum

try:
    from .PyTranslate import _
except ImportError as e:
    print(e)
    raise Exception(_('Error importing modules'))

try:
    from .Coordinates_operations import reproject_and_resample_raster
except ImportError as e:
    print(e)
    raise Exception(_('Error importing modules'))

try:
    from .GraphNotebook import PlotPanel
except ImportError as e:
    print(e)
    raise Exception(_('Error importing modules GraphNotebook'))

try:
    from .CpGrid import CpGrid
except ImportError as e:
    print(e)
    raise Exception(_('Error importing modules'))

try:
    from .drawing_obj import Element_To_Draw
except ImportError as e:
    print(e)
    raise Exception(_('Error importing modules'))

try:
    from wolf_libs import wolfogl

except ImportError as e:
    msg=_('Error importing wolfogl.pyd')
    msg+=_('   Python version : ' + sys.version)
    msg+=_('   If your Python version is not 3.10.x, you need to get an adapted library in wolfhece library path libs')
    msg+=_('   Please contact us or launch *python compile_wcython.py build_ext --inplace* in :')
    msg+='      ' + os.path.dirname(__file__)
    msg+=_('   if you have the source files of the Cython modules.')

    raise Exception(msg)

try:
    from .xyz_file import XYZFile
    from .PyPalette import wolfpalette
    from .PyVertexvectors import Zones, vector, wolfvertex, zone, Triangulation
    from .PyVertex import cloud_vertices
    from .opengl.py3d import Cache_WolfArray_plot3D, WolfArray_plot3D
except ImportError as e:
    print(e)
    raise Exception(_('Error importing modules'))

try:
    from .pydownloader import download_file, toys_dataset
except ImportError as e:
    raise Exception(_('Error importing pydownloader module'))

# try:
#     from wolfhece_tools.wolf_array import header_wolf
# except ImportError as e:
#     logging.error(e)
#     raise Exception(_('Error importing modules wolfhece_tools - please install it via pip install wolfhece_tools'))

import math
from fractions import Fraction

def pgcd_decimal(a, b):
    # Convertir les décimaux en fractions exactes
    fa = Fraction(a).limit_denominator()
    fb = Fraction(b).limit_denominator()

    # Extraire les numérateurs et dénominateurs
    num_a, den_a = fa.numerator, fa.denominator
    num_b, den_b = fb.numerator, fb.denominator

    # Mettre au même dénominateur
    lcm_den = math.lcm(den_a, den_b)
    a_int = num_a * (lcm_den // den_a)
    b_int = num_b * (lcm_den // den_b)

    # PGCD des entiers
    pgcd_int = math.gcd(a_int, b_int)

    # Revenir à l’échelle décimale
    return pgcd_int / lcm_den

WOLF_ARRAY_HILLSHAPE = -1
WOLF_ARRAY_FULL_SINGLE = 1
WOLF_ARRAY_FULL_DOUBLE = 2
WOLF_ARRAY_SYM_DOUBLE = 12
WOLF_ARRAY_FULL_LOGICAL = 4
WOLF_ARRAY_CSR_DOUBLE = 5
WOLF_ARRAY_FULL_INTEGER = 6
WOLF_ARRAY_FULL_SINGLE_3D = 7
WOLF_ARRAY_FULL_INTEGER8 = 8
WOLF_ARRAY_FULL_UINTEGER8 = 88

WOLF_ARRAY_MB_SINGLE = 3
WOLF_ARRAY_MB_INTEGER = 9

WOLF_ARRAY_FULL_INTEGER16_2 = 0
WOLF_ARRAY_FULL_INTEGER16 = 11
WOLF_ARRAY_MNAP_INTEGER = 20

WOLF_ARRAY_MB = [WOLF_ARRAY_MB_SINGLE, WOLF_ARRAY_MB_INTEGER, WOLF_ARRAY_MNAP_INTEGER]

VERSION_RGB = 3

from numba import jit

@jit(nopython=True)
def custom_gradient(array: np.ndarray):
    """ Calculate the gradient manually """
    grad_x = np.zeros_like(array)
    grad_y = np.zeros_like(array)

    for i in range(1, array.shape[0] - 1):
        for j in range(1, array.shape[1] - 1):
            grad_x[i, j] = (array[i + 1, j] - array[i - 1, j]) / 2.0
            grad_y[i, j] = (array[i, j + 1] - array[i, j - 1]) / 2.0

    return grad_x, grad_y

@jit(nopython=True)
def hillshade(array:np.ndarray, azimuth:float, angle_altitude:float) -> np.ndarray:
    """ Create a hillshade array """

    azimuth = 360.0 - azimuth

    x, y = custom_gradient(array)
    slope = np.pi / 2. - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-x, y)
    azimuthrad = azimuth * np.pi / 180.
    altituderad = angle_altitude * np.pi / 180.

    shaded = np.sin(altituderad) * np.sin(slope) + np.cos(altituderad) * \
             np.cos(slope) * np.cos((azimuthrad - np.pi / 2.) - aspect)
    shaded += 1.
    shaded *= .5

    return shaded.astype(np.float32)
class Rebin_Ops(Enum):
    MIN = 0
    MEAN = 1
    MAX = 2
    SUM = 3
    MEDIAN = 4

    @classmethod
    def get_numpy_ops(cls):
        """ Return a list of numpy functions corresponding to the enum values """

        # CAUTION : Order is important and must match the enum values
        return [np.ma.min, np.ma.mean, np.ma.max, np.ma.sum, np.ma.median]

    @classmethod
    def get_ops(cls, name:str):
        """ Return the numpy function corresponding to a string """

        if isinstance(name, Rebin_Ops):
            return cls.get_numpy_ops()[name.value]
        elif isinstance(name, str):
            if name == 'min':
                return np.ma.min
            elif name == 'mean':
                return np.ma.mean
            elif name == 'max':
                return np.ma.max
            elif name == 'sum':
                return np.ma.sum
            elif name == 'median':
                return np.ma.median
            else:
                return None
        else:
            return None

def getkeyblock(i, addone=True) -> str:
    """
    Name/Key of a block in the dictionnary of a WolfArrayMB instance

    For Fortran compatibility, addone is True by default so first block is "block1" and not "block0"
    """
    if addone:
        return 'block' + str(i + 1)
    else:
        return 'block' + str(i)

def decodekeyblock(key, addone=True) -> int:
    """
    Decode key of a block in the dictionnary of a WolfArrayMB instance

    For Fortran compatibility, addone is True by default so first block is "block1" and not "block0"
    """
    if addone:
        return int(key[5:])
    else:
        return int(key[5:]) - 1



class header_wolf():
    """
    Header of WolfArray

    In case of a mutliblock, the header have informations about all the blocks in head_blocks dictionnary.
    Block keys are generated by "getkeyblock" function
    """

    # FIXME It'd be wise to put the multiblock case into another class.
    # for example "header_wolf_MB" else one could construct hierearchies
    # of headers which don't exist in practice.

    head_blocks: dict[str,"header_wolf"]

    def __init__(self) -> None:
        """
        Origin (origx, origy, [origz]) is the point in local space from which every other coordinates are measured.

        Translation (translx, transly, [translz]) is the translation of the origin in global space. If translation is null, the origin is the same in local and global space. :-)

        Resolution (dx, dy, [dz]) is the spatial resolution of the array.

        Nullvalue is the value of the null value in the array.

        (nbx, nby, [nbz]) are the number of cells in the array along X and Y [and Z]. It is the shape of the array.

        @property nbdims is the number of dimensions of the array (2 or 3)
        """

        self.origx = 0.0
        self.origy = 0.0
        self.origz = 0.0

        self.translx = 0.0
        self.transly = 0.0
        self.translz = 0.0

        self.dx = 0.0
        self.dy = 0.0
        self.dz = 0.0

        self.nbx = 0
        self.nby = 0
        self.nbz = 0

        self.head_blocks = {}

        self._nullvalue = 0.

        self._epsg = None

    def __str__(self) -> str:
        """ Return a string representation of the header """
        ret = ''
        ret += _('Shape  : {} x {} \n').format(self.nbx, self.nby)
        ret += _('Resolution  : {} x {} \n').format(self.dx, self.dy)
        ret += _('Spatial extent : \n')
        ret += _('   - Origin : ({} ; {}) \n').format(self.origx, self.origy)
        ret += _('   - End : ({} ; {}) \n').format(self.origx + self.nbx * self.dx, self.origy +self.nby * self.dy)
        ret += _('   - Width x Height : {} x {} \n').format(self.nbx * self.dx, self.nby * self.dy)
        ret += _('   - Translation : ({} ; {})\n').format(self.translx, self.transly)
        ret += _('Null value : {}\n\n'.format(self.nullvalue))

        if len(self.head_blocks) > 0:
            ret += _('Number of blocks : {}\n\n').format(len(self.head_blocks))
            for key, value in self.head_blocks.items():
                ret += _('Block {} : \n\n').format(key)
                ret += str(value)

        return ret

    @property
    def epsg(self):
        return self._epsg

    @epsg.setter
    def epsg(self, value:int | str):

        if isinstance(value, str):
            if value in ['Belgique 1972', 'EPSG:31370', '31370', 'Belgium 1972']:
                self._epsg = 31370
            elif value in ['RGF93 / Lambert-93', 'EPSG:2154', '2154', 'France Lambert-93']:
                self._epsg = 2154
            elif value in ['Detutschland GK3', 'EPSG:31467', '31467', 'Germany GK3', 'Allemagne GK3']:
                self._epsg = 31467
            else:
                try:
                    epsg_code = int(value.split(':')[1])
                    self._epsg = epsg_code
                except (IndexError, ValueError):
                    logging.warning(_('Could not parse EPSG code from string: {}').format(value))
                    self._epsg = None

        elif isinstance(value, int):
            self._epsg = value

    @property
    def nullvalue(self):
        return self._nullvalue

    @nullvalue.setter
    def nullvalue(self, value:float):
        self._nullvalue = value

    @property
    def nbdims(self):
        if self.nbz == 0:
            if self.nbx > 0 and self.nby > 0:
                return 2
            else:
                return 0
        elif self.nbz > 0:
            return 3
        else:
            raise Exception(_('The number of dimensions is not correct'))

    @nbdims.setter
    def nbdims(self, value):
        logging.warning(_('nbdims was an attribute of header_wolf.\nIt is now a read-only property.\nPlease use nbx, nby and nbz instead to define the shape of the array'))
        raise Exception(_('This property is read-only'))

    @property
    def shape(self):
        if self.nbdims == 2:
            return (self.nbx, self.nby)
        elif self.nbdims == 3:
            return (self.nbx, self.nby, self.nbz)
        else:
            return (0, 0)

    @shape.setter
    def shape(self, value:tuple[int]):
        if len(value) == 3:
            self.nbx = value[0]
            self.nby = value[1]
            self.nbz = value[2]
        elif len(value) == 2:
            self.nbx = value[0]
            self.nby = value[1]
            self.nbz = 0
        else:
            raise Exception(_('The number of dimensions is not correct'))

    @property
    def nb_blocks(self):
        return len(self.head_blocks)

    def __getitem__(self, key:Union[int,str]=None):
        """
        Return block header

        :param key: block's index (0-based) or key (str)
        :return: header_wolf instance if key is found, None otherwise
        """
        if key is None:
            return self

        if isinstance(key,int):
            _key = getkeyblock(key)
        else:
            _key = key

        if _key in self.head_blocks.keys():
            return self.head_blocks[_key]
        else:
            return None

    def __setitem__(self, key:Union[int,str], value:"header_wolf"):
        """
        Set block header

        :param value: tuple (key, header_wolf)

        'key' can be an int (0-based) or a str
        If str, please use getkeyblock function to generate the key
        """

        if isinstance(key,int):
            _key = getkeyblock(key)
        else:
            _key = key

        self.head_blocks[_key] = deepcopy(value)

    @property
    def resolution(self):
        return self.get_resolution()

    @resolution.setter
    def resolution(self, value:tuple[float]):

        if len(value) == 2:
            self.set_resolution(value[0], value[1])
        elif len(value) == 3:
            self.set_resolution(value[0], value[1], value[2])

    @property
    def origin(self):
        return self.get_origin()

    @origin.setter
    def origin(self, value:tuple[float]):

        if len(value) == 2:
            self.set_origin(value[0], value[1])
        elif len(value) == 3:
            self.set_origin(value[0], value[1], value[2])

    @property
    def translation(self):
        return self.get_translation()

    @translation.setter
    def translation(self, value:tuple[float]):
        if len(value) == 2:
            self.set_translation(value[0], value[1])
        elif len(value) == 3:
            self.set_translation(value[0], value[1], value[2])

    def set_resolution(self, dx:float, dy:float, dz:float= 0.):
        """
        Set resolution
        """

        self.dx = dx
        self.dy = dy
        self.dz = dz

    def set_origin(self, x:float, y:float, z:float = 0.):
        """
        Set origin

        :param x: origin along X
        :param y: origin along Y
        :param z: origin along Z
        """
        self.origx = x
        self.origy = y
        self.origz = z

    def get_origin(self):
        """
        Return origin
        """

        return (self.origx, self.origy, self.origz)

    def get_resolution(self):
        """
        Return resolution
        """

        return (self.dx, self.dy, self.dz)

    def get_translation(self):
        """
        Return translation
        """

        return (self.translx, self.transly, self.translz)

    def set_translation(self, tr_x:float, tr_y:float, tr_z:float= 0.):
        """
        Set translation

        :param tr_x: translation along X
        :param tr_y: translation along Y
        :param tr_z: translation along Z
        """
        self.translx = tr_x
        self.transly = tr_y
        self.translz = tr_z

    def get_bounds(self, abs=True):
        """
        Return bounds in coordinates

        :param abs: if True, add translation to (x, y) (coordinate to global space)
        :return: tuple of two lists of two floats - ([xmin, xmax],[ymin, ymax])
        """
        if abs:
            return ([self.origx + self.translx, self.origx + self.translx + float(self.nbx) * self.dx],
                    [self.origy + self.transly, self.origy + self.transly + float(self.nby) * self.dy])
        else:
            return ([self.origx, self.origx + float(self.nbx) * self.dx],
                    [self.origy, self.origy + float(self.nby) * self.dy])

    def get_extent(self, abs=True):
        """
        Return extent in coordinates
        :param abs: if True, add translation to (x, y) (coordinate to global space)
        :return: list of four floats - [xmin, xmax, ymin, ymax]
        """
        bounds = self.get_bounds(abs)
        return [bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]]

    def get_scale_yoverx(self):
        """
        Return the scale of the array (height over width)
        """
        if self.dx == 0 or self.dy == 0 or self.nbx == 0 or self.nby == 0:
            return 1.

        return float((self.nby * self.dy) / (self.nbx * self.dx))

    def get_bounds_ij(self, abs=False):
        """
        Return bounds in indices

        Firstly, get_bounds is called to get bounds in coordinates and then get_ij_from_xy is called to get bounds in indices.

        :param abs: if True, add translation to (x, y) (coordinate to global space)
        """
        mybounds = self.get_bounds(abs)

        return (
            [self.get_ij_from_xy(mybounds[0][0], mybounds[1][0], abs=abs), self.get_ij_from_xy(mybounds[0][1], mybounds[0][0], abs=abs)],
            [self.get_ij_from_xy(mybounds[0][0], mybounds[1][1], abs=abs), self.get_ij_from_xy(mybounds[0][1], mybounds[1][1], abs=abs)])

    def get_ij_from_xy(self, x:float, y:float, z:float=0., scale:float=1., aswolf:bool=False, abs:bool=True, forcedims2:bool=False) -> Union[tuple[np.int32,np.int32], tuple[np.int32,np.int32,np.int32]]:
        """
        Get indices from coordinates

        :param x: X coordinate
        :param y: Y coordinate
        :param z: Z coordinate (optional)
        :param scale: scaling of the spatial resolution (dx,dy,[dz])
        :param aswolf: if True, return if one-based (as Wolf VB6 or Fortran), otherwise 0-based (default Python standard)
        :param abs: if True, remove translation from (x, y, [z]) (coordinate from global space)
        :param forcedims2: if True, force to return only 2 indices even if z is supplied
        """

        locx = np.float64(x) - self.origx
        locy = np.float64(y) - self.origy
        locz = np.float64(z) - self.origz
        if abs:
            locx = locx - self.translx
            locy = locy - self.transly
            locz = locz - self.translz

        i = np.int32(np.floor(locx / (self.dx * scale)))
        j = np.int32(np.floor(locy / (self.dy * scale)))

        if aswolf:
            i += 1
            j += 1

        if self.nbdims == 3 and not forcedims2:
            k = np.int32(np.floor(locz / (self.dz * scale)))
            if aswolf:
                k += 1
            return i, j, k
        elif self.nbdims == 2 or forcedims2:
            return i, j

    def get_ij_from_xy_array(self, xy:np.ndarray, scale:float=1., aswolf:bool=False, abs:bool=True, forcedims2:bool=False) -> np.ndarray:
        """
        Get indices from coordinates

        :param xy = numpy array containing (x, y, [z]) coordinates - shape (n, 2) or (n, 3)
        :param scale = scaling of the spatial resolution (dx,dy,[dz])
        :param aswolf = if True, return if one-based (as Wolf VB6 or Fortran), otherwise 0-based (default Python standard)
        :param abs = if True, remove translation from (x, y, [z]) (coordinate from global space)
        :param forcedims2 = if True, force to return only 2 indices even if z is supplied

        :return: numpy array containing (i, j, [k]) indices - shape (n, 2) or (n, 3)
        """

        if isinstance(xy,tuple):
            if len(xy) == 2:
                if (isinstance(xy[0],np.ndarray)) and (isinstance(xy[1],np.ndarray)):
                    if len(xy[0]) == len(xy[1]):
                        locxy = np.vstack((xy[0], xy[1])).T
                        logging.warning(_('get_ij_from_xy_array - xy is a tuple of 2 arrays, it is converted to a 2D array'))
            else:
                locxy = np.array(xy)
        elif isinstance(xy,list):
            locxy = np.array(xy)
        else:
            locxy = xy.copy()

        if forcedims2:
            locij = np.zeros((locxy.shape[0],2), dtype=np.int32)
        else:
            locij = np.zeros(locxy.shape, dtype=np.int32)

        if locxy.size == 0:
            return locij

        locxy[:,0] -= self.origx
        locxy[:,1] -= self.origy

        if abs:
            locxy[:,0] -= self.translx
            locxy[:,1] -= self.transly

        i = np.int32(locxy[:,0] / (self.dx * scale))
        j = np.int32(locxy[:,1] / (self.dy * scale))

        if aswolf:
            i += 1
            j += 1

        if self.nbdims == 3 and not forcedims2:
            locxy[:,2] -= self.origz
            if abs:
                locxy[:,2] -= self.translz
            k = np.int32(locxy[:,2] / (self.dz * scale))

            if aswolf:
                k += 1

            locij[:,0] = i
            locij[:,1] = j
            locij[:,2] = k

            return locij

        elif self.nbdims == 2 or forcedims2:
            locij[:,0] = i
            locij[:,1] = j
            return locij


    def get_xy_from_ij(self, i:int, j:int, k:int=0, scale:float=1., aswolf:bool=False, abs:bool=True) -> Union[tuple[np.float64,np.float64], tuple[np.float64,np.float64,np.float64]]:
        """
        Get coordinates from indices

        :param i = index along X coordinate
        :param j = index along Y coordinate
        :param k = index along Z coordinate (optional)
        :param scale = scaling of the spatial resolution (dx,dy,[dz])
        :param aswolf = if True, input is one-based (as Wolf VB6 or Fortran), otherwise 0-based (default Python standard)
        :param abs = if True, add translation to results (x, y, [z]) (coordinate to global space)
        """
        i = np.int32(i)
        j = np.int32(j)

        if aswolf:
            # FIXME Put assertion here.
            i += -1
            j += -1

        if abs:
            x = (np.float64(i) + .5) * (self.dx * scale) + self.origx + self.translx
            y = (np.float64(j) + .5) * (self.dy * scale) + self.origy + self.transly
        else:
            x = (np.float64(i) + .5) * (self.dx * scale) + self.origx
            y = (np.float64(j) + .5) * (self.dy * scale) + self.origy

        if self.nbdims == 3:
            k = np.int32(k)
            if aswolf:
                k += -1

            if abs:
                z = (np.float64(k) - .5) * (self.dz * scale) + self.origz + self.translz
            else:
                z = (np.float64(k) - .5) * (self.dz * scale) + self.origz

            return x, y, z

        elif self.nbdims == 2:
            return x, y
        else:
            raise Exception(_("The number of coordinates is not correct"))

    def transform(self):
        """ Return the affine transformation.

        Similar to rasterio.transform.Affine

        In WOLF, the convention is :
         - origin is at the lower-left corner
         - the origin is at the corner of the cell dx, dy, so the center of the cell is at dx/2, dy/2
         - X axis is along the rows - i index
         - Y axis is along the columns - j index

         So, the affine transformation is :
            (dx, 0, origx + translx + dx /2, 0, dy, origy + transly + dy/2)
        """
        from rasterio.transform import Affine
        return Affine(self.dx, 0, self.origx + self.translx + self.dx / 2,
                      0, self.dy, self.origy + self.transly + self.dy / 2)

    def _transform_gmrio(self):
        """ Return the affine transformation.

        !! Inverted ij/ji convention !!

        Similar to rasterio.transform.Affine

        In WOLF, the convention is :
         - origin is at the lower-left corner
         - the origin is at the corner of the cell dx, dy, so the center of the cell is at dx/2, dy/2
         - X axis is along the rows - i index
         - Y axis is along the columns - j index

         So, the affine transformation is :
            (dx, 0, origx + translx + dx /2, 0, dy, origy + transly + dy/2)
        """
        from rasterio.transform import Affine
        return Affine(0, self.dy, -(self.origy + self.transly),
                      self.dx, 0, -(self.origx + self.transly))

    def get_xy_from_ij_array(self, ij:np.ndarray, scale:float=1., aswolf:bool=False, abs:bool=True) -> np.ndarray:
        """
        Converts array coordinates (numpy cells) to this array's world coodinates.

        :param ij = numpy array containing (i, j, [k]) indices - shape (n, 2) or (n, 3)
        :param scale = scaling of the spatial resolution (dx,dy,[dz])
        :param aswolf = if True, input is one-based (as Wolf VB6 or Fortran), otherwise 0-based (default Python standard)
        :param abs = if True, add translation to results (x, y, [z]) (coordinate to global space)

        ..warning: 'ij' is not the result of np.where() but if you want to use np.where() you can use the following code:
        ```
        np.vstack((ij[0], ij[1])).T
        ```

        """

        if isinstance(ij,tuple):
            if len(ij) == 2:
                if (isinstance(ij[0],np.ndarray)) and (isinstance(ij[1],np.ndarray)):
                    if len(ij[0]) == len(ij[1]):
                        ij = np.vstack((ij[0], ij[1])).T
                        logging.warning(_('get_xy_from_ij_array - ij is a tuple of 2 arrays, it is converted to a 2D array'))
            else:
                ij = np.array(ij)

        elif isinstance(ij,list):
            if len(ij) == 2:
                if (isinstance(ij[0],np.ndarray)) and (isinstance(ij[1],np.ndarray)):
                    if len(ij[0]) == len(ij[1]):
                        ij = np.vstack((ij[0], ij[1])).T
                        logging.warning(_('get_xy_from_ij_array - ij is a list of 2 arrays, it is converted to a 2D array'))
            else:
                ij = np.array(ij)

        if abs:
            tr_x = self.translx
            tr_y = self.transly
            tr_z = self.translz
        else:
            tr_x = 0.
            tr_y = 0.
            tr_z = 0.

        if aswolf:
            decali = -1
            decalj = -1
            decalk = -1
        else:
            decali = 0
            decalj = 0
            decalk = 0

        xy = np.zeros(ij.shape)
        xy[:,0] = (np.float64( (ij[:,0])+decali) + .5) * (self.dx*scale) + self.origx + tr_x
        xy[:,1] = (np.float64( (ij[:,1])+decalj) + .5) * (self.dy*scale) + self.origy + tr_y

        if self.nbdims == 3 and ij.shape[1]==3:
            xy[:,2] = (np.float64( (ij[:,2])+decalk) + .5) * (self.dz*scale) + self.origz + tr_z

        return xy

    def ij2xy(self, i:int, j:int, k:int=0, scale:float=1., aswolf:bool=False, abs:bool=True) -> Union[tuple[np.float64,np.float64], tuple[np.float64,np.float64,np.float64]]:
        """ alias for get_xy_from_ij """
        return self.get_xy_from_ij(i, j, k, scale, aswolf, abs)

    def ij2xy_np(self, ij:np.ndarray, scale:float=1., aswolf:bool=False, abs:bool=True) -> np.ndarray:
        """ alias for get_xy_from_ij_array

        :param ij: numpy array containing (i, j, [k]) indices - like np.argwhere() - shape (n, 2) or (n, 3)
        :param scale: scaling of the spatial resolution (dx,dy,[dz])
        :param aswolf: if True, input is one-based (as Wolf VB6 or Fortran), otherwise 0-based (default Python standard)
        :param abs: if True, add translation to results (x, y, [z]) (coordinate to global space)

        ..warning: 'ij' is not the result of np.where() but if you want to use np.where() you can use the following code:
        ```
        np.vstack((ij[0], ij[1])).T
        ```

        :return: numpy array containing (x, y, [z]) coordinates - shape (n, 2) or (n, 3)
        """
        return self.get_xy_from_ij_array(ij, scale, aswolf, abs)

    def ij2xy_np_ij_from_npwhere(self, ij:np.ndarray, scale:float=1., aswolf:bool=False, abs:bool=True) -> np.ndarray:
        """ alias for get_xy_from_ij_array but with ij as np.where result
        """

        ij = np.vstack((ij[0], ij[1])).T
        return self.get_xy_from_ij_array(ij, scale, aswolf, abs)

    def xy2ij(self, x:float, y:float, z:float=0., scale:float=1., aswolf:bool=False, abs:bool=True, forcedims2:bool=False) -> Union[tuple[np.int32,np.int32], tuple[np.int32,np.int32,np.int32]]:
        """ alias for get_ij_from_xy """
        return self.get_ij_from_xy(x, y, z, scale, aswolf, abs, forcedims2)

    def xy2ij_np(self, xy:np.ndarray, scale:float=1., aswolf:bool=False, abs:bool=True) -> np.ndarray:
        """
        alias for get_ij_from_xy_array

        :param xy: numpy array containing (x, y, [z]) coordinates - shape (n, 2) or (n, 3)
        :param scale: scaling of the spatial resolution (dx,dy,[dz])
        :param aswolf: if True, return if one-based (as Wolf VB6 or Fortran), otherwise 0-based (default Python standard)
        :param abs: if True, remove translation from (x, y, [z]) (coordinate from global space)
        :param forcedims2: if True, force to return only 2 indices even if z is supplied

        :return : numpy array containing (i, j, [k]) indices - shape (n, 2) or (n, 3)
        """
        return self.get_ij_from_xy_array(xy, scale, aswolf, abs)

    def xyz2ijk_np(self, xyz:np.ndarray, scale:float=1., aswolf:bool=False, abs:bool=True) -> np.ndarray:
        """ alias for get_xy_from_ij_array """
        assert xyz.shape[1] == 3, _('xyz must be a 2D array with 3 columns')
        return self.get_xy_from_ij_array(xyz, scale, aswolf, abs)

    def ijk2xyz_np(self, ijk:np.ndarray, scale:float=1., aswolf:bool=False, abs:bool=True) -> np.ndarray:
        """ alias for get_xy_from_ij_array """
        assert ijk.shape[1] == 3, _('ijk must be a 2D array with 3 columns')
        return self.get_xy_from_ij_array(ijk, scale, aswolf, abs)


    def find_intersection(self, other:"header_wolf", ij:bool = False) -> Union[tuple[list[float],list[float]], tuple[list[list[float]],list[list[float]]]]:
        """
        Find the intersection of two header

        :param other: other header
        :param ij: if True, return indices instead of coordinates

        :return: None or tuple of two lists of two floats - ([xmin, xmax],[ymin, ymax]) or indices in each header (if ij=True) [[imin1, imax1], [jmin1, jmax1]], [[imin2, imax2], [jmin2, jmax2]]
        """
        mybounds = self.get_bounds()
        otherbounds = other.get_bounds()

        if otherbounds[0][0] > mybounds[0][1]:
            return None
        elif otherbounds[1][0] > mybounds[1][1]:
            return None
        elif otherbounds[0][1] < mybounds[0][0]:
            return None
        elif otherbounds[1][1] < mybounds[1][0]:
            return None
        else:
            ox = max(mybounds[0][0], otherbounds[0][0])
            oy = max(mybounds[1][0], otherbounds[1][0])
            ex = min(mybounds[0][1], otherbounds[0][1])
            ey = min(mybounds[1][1], otherbounds[1][1])
            if ij:
                i1, j1 = self.get_ij_from_xy(ox, oy)
                i2, j2 = self.get_ij_from_xy(ex, ey)

                i3, j3 = other.get_ij_from_xy(ox, oy)
                i4, j4 = other.get_ij_from_xy(ex, ey)
                return ([[i1, i2], [j1, j2]],
                        [[i3, i4], [j3, j4]])
            else:
                return ([ox, ex], [oy, ey])

    def find_union(self, other:Union["header_wolf", list["header_wolf"]]) -> tuple[list[float],list[float]]:
        """
        Find the union of two header

        :return: tuple of two lists of two floats - ([xmin, xmax],[ymin, ymax])
        """

        if isinstance(other, list):

            for cur in other:
                assert isinstance(cur, header_wolf), _('All elements in the list must be header_wolf instances')

            [ox,ex], [oy,ey] = self.get_bounds()

            for cur in other:
                otherbounds = cur.get_bounds()

                ox = min(ox, otherbounds[0][0])
                oy = min(oy, otherbounds[1][0])
                ex = max(ex, otherbounds[0][1])
                ey = max(ey, otherbounds[1][1])

        else:

            mybounds = self.get_bounds()
            otherbounds = other.get_bounds()

            ox = min(mybounds[0][0], otherbounds[0][0])
            oy = min(mybounds[1][0], otherbounds[1][0])
            ex = max(mybounds[0][1], otherbounds[0][1])
            ey = max(mybounds[1][1], otherbounds[1][1])

        return ([ox, ex], [oy, ey])

    def read_txt_header(self, filename:str):
        """
        Read informations from header .txt

        :param filename: path and filename of the basefile

        If filename is a Path object, it is converted to a string
        If filename ends with '.tif', nothing is done because infos are in the .tif file
        If filename ends with '.flt', a .hdr file must be present and it will be read
        Otherwise, a filename.txt file must be present
        """
        if isinstance(filename, Path):
            filename = str(filename)

        locpath = Path(filename)

        if filename.endswith('.tif') or filename.endswith('.tiff') :
            # from osgeo import gdal

            raster:gdal.Dataset
            raster = gdal.Open(filename)
            geotr = raster.GetGeoTransform()
            self.dx = geotr[1]
            self.dy = abs(geotr[5])
            if geotr[5] < 0.:
                self.origx = geotr[0]
                self.origy = geotr[3] + raster.RasterYSize * geotr[5]
            else:
                self.origx = geotr[0]
                self.origy = geotr[3]
            self.nbx = raster.RasterXSize
            self.nby = raster.RasterYSize

            """
            https://docs.qgis.org/3.34/en/docs/user_manual/processing_algs/gdal/rasterconversion.html

            0 — Use Input Layer Data Type
            1 — Byte (Eight bit unsigned integer (quint8))
            2 — Int16 (Sixteen bit signed integer (qint16))
            3 — UInt16 (Sixteen bit unsigned integer (quint16))
            4 — UInt32 (Thirty two bit unsigned integer (quint32))
            5 — Int32 (Thirty two bit signed integer (qint32))
            6 — Float32 (Thirty two bit floating point (float))
            7 — Float64 (Sixty four bit floating point (double))
            8 — CInt16 (Complex Int16)
            9 — CInt32 (Complex Int32)
            10 — CFloat32 (Complex Float32)
            11 — CFloat64 (Complex Float64)
            12 — Int8 (Eight bit signed integer (qint8))
            """

            dtype = raster.GetRasterBand(1).DataType

            if dtype == 1:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER8
            elif dtype in [2,3]:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER16
            elif dtype in [4,5] :
                self.wolftype = WOLF_ARRAY_FULL_INTEGER
            elif dtype ==6:
                self.wolftype = WOLF_ARRAY_FULL_SINGLE
            elif dtype == 7:
                self.wolftype = WOLF_ARRAY_FULL_DOUBLE
            else:
                logging.error(_('The datatype of the raster is not supported -- {}'.format(dtype)))
                logging.error(_('Please convert the raster to a supported datatype - or upgrade the code to support this datatype'))
                logging.error(_('See : read_txt_header and import_geotif in wolf_array.py'))
                return

            # Find the EPSG code
            proj = raster.GetProjection()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(proj)
            if srs.IsProjected:
                self.epsg = int(srs.GetAttrValue('AUTHORITY',1))

                if "EPSG:" in proj:
                    try:
                        idx1 = proj.index("EPSG:")
                        idx2 = proj.index('"', idx1)
                        epsg2 = int(proj[idx1+5:idx2])
                        if epsg2 != self.epsg:
                            logging.warning(_('Mismatch in EPSG code detection: {} and {}').format(self.epsg, epsg2))
                            logging.warning(_("Check your file's projection -- You can use gdalinfo command line tool"))
                            self.epsg = epsg2
                            logging.warning(_('Using EPSG: {}').format(self.epsg))
                    except:
                        logging.warning(_('Could not check EPSG code in the projection string'))
                        logging.warning(_("Check your file's projection -- You can use gdalinfo command line tool"))

        elif filename.endswith('.vrt'):
            # Virtual raster
            # from osgeo import gdal

            raster:gdal.Dataset
            raster = gdal.Open(filename)
            geotr = raster.GetGeoTransform()
            self.dx = geotr[1]
            self.dy = abs(geotr[5])
            self.origx = geotr[0]
            self.origy = geotr[3]

            if geotr[5] < 0.:
                self.origy = geotr[3] + raster.RasterYSize * geotr[5]

            self.nbx = raster.RasterXSize
            self.nby = raster.RasterYSize

            dtype = raster.GetRasterBand(1).DataType

            if dtype == 1:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER8
            elif dtype in [2,3]:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER16
            elif dtype in [4,5] :
                self.wolftype = WOLF_ARRAY_FULL_INTEGER
            elif dtype ==6:
                self.wolftype = WOLF_ARRAY_FULL_SINGLE
            elif dtype == 7:
                self.wolftype = WOLF_ARRAY_FULL_DOUBLE
            else:
                logging.error(_('The datatype of the raster is not supported -- {}'.format(dtype)))
                logging.error(_('Please convert the raster to a supported datatype - or upgrade the code to support this datatype'))
                logging.error(_('See : read_txt_header and import_geotif in wolf_array.py'))
                return

            # Find the EPSG code
            proj = raster.GetProjection()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(proj)
            if srs.IsProjected:
                self.epsg = int(srs.GetAttrValue('AUTHORITY',1))

                if "EPSG:" in proj:
                    try:
                        idx1 = proj.index("EPSG:")
                        idx2 = proj.index('"', idx1)
                        epsg2 = int(proj[idx1+5:idx2])
                        if epsg2 != self.epsg:
                            logging.warning(_('Mismatch in EPSG code detection: {} and {}').format(self.epsg, epsg2))
                            logging.warning(_("Check your file's projection -- You can use gdalinfo command line tool"))
                            self.epsg = epsg2
                            logging.warning(_('Using EPSG: {}').format(self.epsg))
                    except:
                        logging.warning(_('Could not check EPSG code in the projection string'))
                        logging.warning(_("Check your file's projection -- You can use gdalinfo command line tool"))


        elif filename.endswith('.npy') and not os.path.exists(filename + '.txt'):
            # Il y de fortes chances que cette matrice numpy provienne d'une modélisation GPU
            #  et donc que les coordonnées et la résolution soient disponibles dans un fichier parameters.json
            if (locpath.parent / 'parameters.json').exists():
                with open(locpath.parent / 'parameters.json', 'r') as f:
                    params = json.load(f)

                if 'parameters' in params.keys():
                    if "dx" in params['parameters'].keys() :
                        self.dx = float(params['parameters']["dx"])
                    if "dy" in params['parameters'].keys() :
                        self.dy = float(params['parameters']["dy"])
                    if "base_coord_x" in params['parameters'].keys() :
                        self.origx = float(params['parameters']["base_coord_x"])
                    if "base_coord_y" in params['parameters'].keys() :
                        self.origy = float(params['parameters']["base_coord_y"])

                self.nullvalue = 0 if 'nap.npy' in filename.lower() else 99999.
            else:

                self.dx = 1.
                self.dy = 1.
                self.origx = 0.
                self.origy = 0.

            # Numpy format
            with open(filename, 'rb') as f:
                version = np.lib.format.read_magic(f)
                if version[0] == 1:
                    shape, fortran, dtype = np.lib.format.read_array_header_1_0(f)
                elif version[0] == 2:
                    shape, fortran, dtype = np.lib.format.read_array_header_2_0(f)
                else:
                    raise ValueError("Unknown numpy version: %s" % version)

            self.nbx, self.nby = shape

            if dtype == np.float32:
                self.wolftype = WOLF_ARRAY_FULL_SINGLE
            elif dtype == np.float64:
                self.wolftype = WOLF_ARRAY_FULL_DOUBLE
            elif dtype == np.int32:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER
            elif dtype == np.int16:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER16
            elif dtype == np.uint8:
                self.wolftype = WOLF_ARRAY_FULL_UINTEGER8
            elif dtype == np.int8:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER8
            else:
                logging.error(_('Unsupported type in numpy file -- Abort loading'))
                return

        elif filename.endswith('.flt'):
            # Fichier .flt
            if not os.path.exists(filename[:-4] + '.hdr'):
                logging.warning(_('File {} does not exist -- Retry!'.format(filename[:-4] + '.hdr')))
                return

            f = open(filename[:-4] + '.hdr', 'r')
            lines = f.read().splitlines()
            f.close()

            for curline in lines:
                if 'NCOLS' in curline.upper():
                    tmp = curline.split(' ')
                    self.nbx = int(tmp[-1])
                elif 'NROWS' in curline.upper():
                    tmp = curline.split(' ')
                    self.nby = int(tmp[-1])
                elif 'XLLCORNER' in curline.upper():
                    tmp = curline.split(' ')
                    self.origx = float(tmp[-1])
                elif 'YLLCORNER' in curline.upper():
                    tmp = curline.split(' ')
                    self.origy = float(tmp[-1])
                elif 'ULXMAP' in curline.upper():
                    tmp = curline.split(' ')
                    self.origx = float(tmp[-1])
                    self.flipupd=True
                elif 'ULYMAP' in curline.upper():
                    tmp = curline.split(' ')
                    self.origy = float(tmp[-1])
                    self.flipupd=True
                elif 'CELLSIZE' in curline.upper():
                    tmp = curline.split(' ')
                    self.dx = self.dy = float(tmp[-1])
                elif 'XDIM' in curline.upper():
                    tmp = curline.split(' ')
                    self.dx = float(tmp[-1])
                elif 'YDIM' in curline.upper():
                    tmp = curline.split(' ')
                    self.dy = float(tmp[-1])
                elif 'NODATA' in curline.upper():
                    tmp = curline.split(' ')
                    self.nullvalue = float(tmp[-1])

            self.origx -= self.dx*0.5
            self.origy += self.dy*0.5

            if self.flipupd:
                self.origy -= self.dy*float(self.nby)

        else:
            if not os.path.exists(filename + '.txt'):
                logging.info(_('File {} does not exist -- Maybe be a parameter.json exists or retry !'.format(filename + '.txt')))
                return

            with open(filename + '.txt', 'r') as f:
                lines = f.read().splitlines()

            tmp = lines[0].split(':')
            self.nbx = int(tmp[1])
            tmp = lines[1].split(':')
            self.nby = int(tmp[1])
            tmp = lines[2].split(':')
            self.origx = float(tmp[1])
            tmp = lines[3].split(':')
            self.origy = float(tmp[1])
            tmp = lines[4].split(':')
            self.dx = float(tmp[1])
            tmp = lines[5].split(':')
            self.dy = float(tmp[1])
            tmp = lines[6].split(':')
            self.wolftype = int(tmp[1])
            tmp = lines[7].split(':')
            self.translx = float(tmp[1])
            tmp = lines[8].split(':')
            self.transly = float(tmp[1])

            decal = 9
            if self.wolftype == WOLF_ARRAY_FULL_SINGLE_3D:
                tmp = lines[9].split(':')
                self.nbz = int(tmp[1])
                tmp = lines[10].split(':')
                self.origz = float(tmp[1])
                tmp = lines[11].split(':')
                self.dz = float(tmp[1])
                tmp = lines[12].split(':')
                self.translz = float(tmp[1])
                decal = 13

            if self.wolftype in WOLF_ARRAY_MB:
                tmp = lines[decal].split(':')
                nb_blocks = int(tmp[1])

                decal += 1
                for i in range(nb_blocks):
                    curhead = header_wolf()
                    tmp = lines[decal].split(':')
                    curhead.nbx = int(tmp[1])
                    tmp = lines[decal + 1].split(':')
                    curhead.nby = int(tmp[1])
                    tmp = lines[decal + 2].split(':')
                    curhead.origx = float(tmp[1])
                    tmp = lines[decal + 3].split(':')
                    curhead.origy = float(tmp[1])
                    tmp = lines[decal + 4].split(':')
                    curhead.dx = float(tmp[1])
                    tmp = lines[decal + 5].split(':')
                    curhead.dy = float(tmp[1])
                    decal += 6

                    curhead.translx = self.translx + self.origx
                    curhead.transly = self.transly + self.origy

                    self.head_blocks[getkeyblock(i)] = curhead

    @classmethod
    def read_header(cls, filename:str) -> "header_wolf":
        """
        alias for read_txt_header

        :param filename: path and filename of the basefile
        """
        newhead = cls()
        newhead.read_txt_header(filename)
        return newhead

    def write_header(self, filename:str,
                     wolftype:int,
                     forceupdate:bool=False):
        """
        alias for write_txt_header
        """
        self.write_txt_header(filename, wolftype, forceupdate)

    def write_txt_header(self,
                         filename:str,
                         wolftype:int,
                         forceupdate:bool=False):
        """
        Writing the header to a text file

        Nullvalue is not written

        :param filename: path and filename with '.txt' extension, which will NOT be automatically added
        :param wolftype: type of the WOLF_ARRAY_* array
        :param forceupdate: if True, the file is rewritten even if it already exists
        """

        assert wolftype in [WOLF_ARRAY_CSR_DOUBLE, WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_SYM_DOUBLE, WOLF_ARRAY_FULL_LOGICAL,
                            WOLF_ARRAY_CSR_DOUBLE, WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_SINGLE_3D, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8,
                            WOLF_ARRAY_MB_SINGLE, WOLF_ARRAY_MB_INTEGER, WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_MNAP_INTEGER, WOLF_ARRAY_FULL_INTEGER16_2], _('The type of array is not correct')

        if not os.path.exists(filename) or forceupdate:
            with open(filename,'w') as f:

                """ Ecriture de l'en-tête de Wolf array """
                f.write('NbX :\t{0}\n'.format(str(self.nbx)))
                f.write('NbY :\t{0}\n'.format(str(self.nby)))
                f.write('OrigX :\t{0}\n'.format(str(self.origx)))
                f.write('OrigY :\t{0}\n'.format(str(self.origy)))
                f.write('DX :\t{0}\n'.format(str(self.dx)))
                f.write('DY :\t{0}\n'.format(str(self.dy)))
                f.write('TypeEnregistrement :\t{0}\n'.format(str(wolftype)))
                f.write('TranslX :\t{0}\n'.format(str(self.translx)))
                f.write('TranslY :\t{0}\n'.format(str(self.transly)))
                if wolftype == WOLF_ARRAY_FULL_SINGLE_3D:
                    f.write('NbZ :\t{0}\n'.format(str(self.nbz)))
                    f.write('OrigZ :\t{0}\n'.format(str(self.origz)))
                    f.write('DZ :\t{0}\n'.format(str(self.dz)))
                    f.write('TranslZ :\t{0}\n'.format(str(self.translz)))

                if wolftype in WOLF_ARRAY_MB:
                    f.write('Nb Blocs :\t{0}\n'.format(str(self.nb_blocks)))
                    for i in range(self.nb_blocks):
                        curhead = self.head_blocks[getkeyblock(i)]
                        f.write('NbX :\t{0}\n'.format(str(curhead.nbx)))
                        f.write('NbY :\t{0}\n'.format(str(curhead.nby)))
                        f.write('OrigX :\t{0}\n'.format(str(curhead.origx)))
                        f.write('OrigY :\t{0}\n'.format(str(curhead.origy)))
                        f.write('DX :\t{0}\n'.format(str(curhead.dx)))
                        f.write('DY :\t{0}\n'.format(str(curhead.dy)))

    def is_like(self, other:"header_wolf", check_mb:bool=False) -> bool:
        """
        Comparison of two headers

        :param other: other header to compare
        :param check_mb: if True, the comparison is done on the blocks too

        The nullvalue is not taken into account
        """
        test = True
        test &= self.origx == other.origx
        test &= self.origy == other.origy
        test &= self.origz == other.origz

        test &= self.translx == other.translx
        test &= self.transly == other.transly
        test &= self.translz == other.translz

        test &= self.dx == other.dx
        test &= self.dy == other.dy
        test &= self.dz == other.dz

        test &= self.nbx == other.nbx
        test &= self.nby == other.nby
        test &= self.nbz == other.nbz

        test &= self.nbdims == other.nbdims

        if check_mb:
            test &= self.nb_blocks == other.nb_blocks
            for block1, block2 in zip(self.head_blocks.values(), other.head_blocks.values()):
                test &= block1.is_like(block2)

        return test

    def align2grid(self, x1:float, y1:float, eps:float=0.0001) -> tuple[float,float]:
        """
        Align coordinates to nearest grid point
        where the grid is defined by the borders of the array.

        """

        if x1-self.origx < 0:
            x2 = np.round((x1 - self.origx + eps) / self.dx) * self.dx + self.origx
        else:
            x2 = np.round((x1 - self.origx - eps) / self.dx) * self.dx + self.origx

        if y1-self.origy < 0:
            y2 = np.round((y1 - self.origy + eps) / self.dy) * self.dy + self.origy
        else:
            y2 = np.round((y1 - self.origy - eps) / self.dy) * self.dy + self.origy

        return x2, y2

    def _rasterize_segment(self,
                           x1:float, y1:float,
                           x2:float, y2:float,
                           xstart:float=None,
                           ystart:float=None,
                           n_packet:int = 10) -> list[list[float]]:
        """
        Rasterize a segment according to the grid
        where the grid is defined by the borders of the array.

        :param x1: x coordinate of the first point
        :param y1: y coordinate of the first point
        :param x2: x coordinate of the second point
        :param y2: y coordinate of the second point
        :param xstart: x coordinate of the starting point
        :param ystart: y coordinate of the starting point

        :return: numpy array of the rasterized segment
        """

        if xstart is None and ystart is None:
            xstart, ystart = self.align2grid(x1, y1)

        x2, y2 = self.align2grid(x2, y2)

        points=[]
        points.append([xstart, ystart])

        length = 99999.
        prec = min(self.dx, self.dy)
        direction = np.array([x2-xstart, y2-ystart])
        length = np.linalg.norm(direction)
        direction /= length

        while length >= prec:

            if np.abs(direction[0])>= np.abs(direction[1]):

                if length > n_packet*prec:
                    # I we are far from the end of the segment, we can use the n_packet to rasterize
                    # this will be used to avoid to many straight lines
                    nx = np.abs(int(direction[0] * (n_packet-1))) # number of points in x direction
                    ny = np.abs(int(direction[1] * (n_packet-1))) # number of points in y direction

                    n_common = min(nx, ny) # number of common points

                    for i in range(n_common):
                        xstart += self.dx * np.sign(direction[0])
                        points.append([xstart, ystart])
                        ystart += self.dy * np.sign(direction[1])
                        points.append([xstart, ystart])

                    for i in range(nx - n_common):
                        xstart += self.dx * np.sign(direction[0])
                        points.append([xstart, ystart])

                    for j in range(ny - n_common):
                        ystart += self.dy * np.sign(direction[1])
                        points.append([xstart, ystart])
                else:
                    xstart += self.dx * np.sign(direction[0])
                    points.append([xstart, ystart])
            else:
                if length > n_packet*prec:
                    nx = np.abs(int(direction[0] * (n_packet-1)))
                    ny = np.abs(int(direction[1] * (n_packet-1)))

                    n_common = min(nx, ny)

                    for j in range(n_common):
                        ystart += self.dy * np.sign(direction[1])
                        points.append([xstart, ystart])
                        xstart += self.dx * np.sign(direction[0])
                        points.append([xstart, ystart])

                    for j in range(ny - n_common):
                        ystart += self.dy * np.sign(direction[1])
                        points.append([xstart, ystart])

                    for i in range(nx - n_common):
                        xstart += self.dx * np.sign(direction[0])
                        points.append([xstart, ystart])

                else:
                    ystart += self.dy * np.sign(direction[1])
                    points.append([xstart, ystart])

            direction = np.array([x2-xstart, y2-ystart])

            length = np.linalg.norm(direction)
            if length >  0.:
                direction /= length

        return points

    def rasterize_vector_along_grid(self, vector2raster:vector, outformat:Union[np.ndarray, vector]=vector) -> Union[np.ndarray,vector]:
        """
        Rasterize a vector according to the grid

        :param vector2raster: vector to rasterize
        :param outformat: output format (np.ndarray or vector)
        """

        assert outformat in [np.ndarray, vector], _('outformat must be np.ndarray or vector')

        # get the vertices of the vector
        xy = vector2raster.asnparray().tolist()

        # rasterize the vector
        rasterized = []
        rasterized += self._rasterize_segment(xy[0][0], xy[0][1], xy[1][0], xy[1][1])

        for i in range(1, len(xy)-1):
            out =  self._rasterize_segment(xy[i][0], xy[i][1],
                                                  xy[i+1][0], xy[i+1][1],
                                                  rasterized[-1][0], rasterized[-1][1])
            rasterized += out[1:]

        # get the indices of the rasterized vector
        xy = np.array(rasterized)

        if outformat is np.ndarray:
            return xy
        elif outformat is vector:
            #create new vector
            newvector = vector()
            newvector.add_vertices_from_array(xy)

            return newvector

    def rasterize_zone_along_grid(self, zone2raster:zone, outformat:Union[np.ndarray, vector]=zone) -> Union[np.ndarray,zone]:
        """ Rasterize a zone according to the grid

        :param zone2raster: zone to rasterize
        :param outformat: output format (np.ndarray or zone)
        """

        assert outformat in [np.ndarray, zone], _('outformat must be np.ndarray or zone')

        if outformat is zone:
            out_vec = vector
        else:
            out_vec = np.ndarray
        new_vecs = []
        for vec in zone2raster.myvectors:
            new_vecs.append(self.rasterize_vector_along_grid(vec, outformat=out_vec))

        if outformat is np.ndarray:
            return np.vstack(new_vecs)
        elif outformat is zone:
            # create new zone
            newzone = zone()
            for vec, oldvec in zip(new_vecs, zone2raster.myvectors):
                vec.myname = oldvec.myname  # keep the original name
                newzone.add_vector(vec, forceparent=True)
            return newzone


    def rasterize_vector(self, vector2raster:vector, outformat:Union[np.ndarray, vector]=vector) -> Union[np.ndarray,vector]:
        """ DEPRECATED since 2.2.8 -- use rasterize_vector_along_grid instead.

        Will be removed in 2.3.0
        """
        logging.warning(_('rasterize_vector is deprecated since 2.2.8 -- use rasterize_vector_along_grid instead'))
        return self.rasterize_vector_along_grid(vector2raster, outformat=outformat)

    def get_xy_infootprint_vect(self, myvect: vector | Polygon, eps:float = 0.) -> tuple[np.ndarray,np.ndarray]:
        """
        Return the coordinates and the indices of the cells in the footprint of a vector.

        Coordinates are stored in a numpy array of shape (n,2) where n is the number of cells in the footprint.
        Indices are stored in a numpy array of shape (n,2) where n is the number of cells in the footprint. -> See get_ij_infootprint

        :param myvect: target vector or Shapely Polygon
        :param eps: epsilon to avoid rounding errors
        :return: tuple of two numpy arrays - (coordinates, indices)

        """

        myptsij = self.get_ij_infootprint_vect(myvect, eps=eps)
        mypts=np.asarray(myptsij.copy(),dtype=np.float64)

        mypts[:,0] = (mypts[:,0]+.5)*self.dx +self.origx +self.translx
        mypts[:,1] = (mypts[:,1]+.5)*self.dy +self.origy +self.transly

        return mypts, myptsij

    def  get_xy_infootprint(self, myvect: vector | Polygon, eps:float = 0.) -> tuple[np.ndarray,np.ndarray]:
        """
        Return the coordinates and the indices of the cells in the footprint of a vector.

        Coordinates are stored in a numpy array of shape (n,2) where n is the number of cells in the footprint.
        Indices are stored in a numpy array of shape (n,2) where n is the number of cells in the footprint. -> See get_ij_infootprint

        Main principle:
        - get the indices with 'get_ij_infootprint'
        - then convert them to coordinates.

        :param myvect: target vector or Shapely Polygon
        :param eps: epsilon to avoid rounding errors
        :return: tuple of two numpy arrays - (coordinates, indices)
        """

        return self.get_xy_infootprint_vect(myvect, eps=eps)

    def get_ij_infootprint_vect(self, myvect: vector | Polygon, eps:float = 0.) -> np.ndarray:
        """
        Return the indices of the cells in the footprint of a vector.

        Main principle:
        - get the bounding box of the vector
        - convert the bounding box to indices
        - limit indices to the array size
        - create a meshgrid of indices

        Indices are stored in a numpy array of shape (n,2) where n is the number of cells in the footprint.

        :param myvect: target vector or Shapely Polygon
        :param eps: epsilon to avoid rounding errors
        :return: numpy array of indices
        """

        if isinstance(myvect, Polygon):
            xmin, ymin, xmax, ymax = myvect.bounds
        elif isinstance(myvect, vector):
            xmin, ymin, xmax, ymax = myvect.xmin, myvect.ymin, myvect.xmax, myvect.ymax
        else:
            logging.error(_('The object must be a vector or a Polygon'))
            return np.array([])

        i1, j1 = self.get_ij_from_xy(xmin+eps, ymin+eps)
        i2, j2 = self.get_ij_from_xy(xmax-eps, ymax-eps)

        i1 = max(i1,0) # FIXME Why ??? How could i,j be negative ? --> because this function can be called with a vector that is not in the array (e.g. a vector defined by clicks in the UI)
        j1 = max(j1,0)
        i2 = min(i2,self.nbx-1)
        j2 = min(j2,self.nby-1)

        xv,yv = np.meshgrid(np.arange(i1,i2+1),np.arange(j1,j2+1))
        mypts = np.hstack((xv.flatten()[:,np.newaxis],yv.flatten()[:,np.newaxis]))

        return mypts

    def get_ij_infootprint(self, myvect: vector | Polygon, eps:float = 0.) -> np.ndarray:
        """
        Return the indices of the cells in the footprint of a vector

        Main principle:
        - get the bounding box of the vector
        - convert the bounding box to indices
        - limit indices to the array size
        - create a meshgrid of indices

        Indices are stored in a numpy array of shape (n,2) where n is the number of cells in the footprint.

        :param myvect: target vector or Shapely Polygon
        :param eps: epsilon to avoid rounding errors
        :return: numpy array of indices
        """
        return self.get_ij_infootprint_vect(myvect, eps=eps)

    def convert_xy2ij_np(self,xy):
        """
        Convert XY coordinates to IJ indices **(0-based)** with Numpy without any check/options

        :param xy: = numpy array of shape (n,2) with XY coordinates

        """

        return np.asarray((xy[:,0]-self.origx -self.translx)/self.dx-.5,dtype=np.int32), \
               np.asarray((xy[:,1]-self.origy -self.transly)/self.dy-.5,dtype=np.int32)

    def convert_ij2xy_np(self,ij):
        """
        Convert IJ indices **(0-based)** to XY coordinates with Numpy without any check/options

        :param ij: = numpy array of shape (n,2) with IJ indices

        """

        return np.asarray((ij[:,0]+.5)*self.dx+self.origx +self.translx ,dtype=np.float64), \
               np.asarray((ij[:,1]+.5)*self.dy+self.origy +self.transly ,dtype=np.float64)

    def is_in_footprint(self, x:float, y:float, eps:float=0.) -> bool:
        """
        Check if a point is in the footprint of the array
        :param x: x coordinate
        :param y: y coordinate
        :param eps: epsilon to avoid rounding errors
        :return: True if the point is in the footprint, False otherwise
        """
        return (x >= self.origx + self.translx - eps) and (x <= self.origx + self.translx + self.nbx * self.dx + eps) and \
               (y >= self.origy + self.transly - eps) and (y <= self.origy + self.transly + self.nby * self.dy + eps)

    @classmethod
    def make(self, orig: tuple[float, float] = (0.0, 0.0), nb: tuple[int, int]=(0,0), d:tuple[float, float]=(1.0,1.0)):
        wh = header_wolf()
        wh.nbx, wh.nby = nb
        wh.origx, wh.origy = orig
        wh.dx, wh.dy = d
        return wh

    @classmethod
    def make_from_xybounds_grid(self,
                                xbounds:tuple[float,float], ybounds:tuple[float,float],
                                d:tuple[float,float]=(1.0,1.0), grid_to_align:'header_wolf' = None):
        """ Create a header_wolf from the bounds in x and y and the resolution in x and y.
        If grid_size is provided, the origin will be adjusted to fit the grid size.

        :param xbounds: tuple of two floats - (xmin, xmax)
        :param ybounds: tuple of two floats - (ymin, ymax)
        :param d: tuple of two floats - (dx, dy)
        :param grid_to_align: header_wolf - grid to adjust the origin
        :return: header_wolf instance
        """
        wh = header_wolf()
        wh.dx, wh.dy = d

        # The origin are at the lower left corner.
        # So we need to adjust the bounds accordingly the grid size.
        if grid_to_align is not None:
            wh.origx = (xbounds[0] - ((xbounds[0] - grid_to_align.origx) % grid_to_align.dx))
            wh.origy = (ybounds[0] - ((ybounds[0] - grid_to_align.origy) % grid_to_align.dy))
        else:
            wh.origx = xbounds[0]
            wh.origy = ybounds[0]

        wh.nbx = int(np.ceil( (xbounds[1]-wh.origx) / wh.dx ))
        wh.nby = int(np.ceil( (ybounds[1]-wh.origy) / wh.dy ))
        return wh

    @classmethod
    def make_from_header(self, other:"header_wolf"):
        wh = header_wolf()
        wh.nbx, wh.nby = other.nbx, other.nby
        wh.origx, wh.origy = other.origx, other.origy
        wh.dx, wh.dy = other.dx, other.dy
        return wh

    def copy(self) -> "header_wolf":
        """ Return a copy of the header_wolf instance """
        return header_wolf.make_from_header(self)

    @classmethod
    def from_slices(self, x_slice:slice, y_slice:slice, d:tuple[float, float]=(1.0,1.0)):
        wh = header_wolf()
        wh.dx, wh.dy = d
        wh.nbx, wh.nby = x_slice.stop - x_slice.start, y_slice.stop - y_slice.start
        wh.origx, wh.origy = x_slice.start * wh.dx, y_slice.start * wh.dy
        return wh

    def to_slices(self) -> tuple[slice, slice]:
        x_slice = slice(int(self.origx / self.dx), int(self.origx / self.dx) + self.nbx)
        y_slice = slice(int(self.origy / self.dy), int(self.origy / self.dy) + self.nby)
        return x_slice, y_slice

    def to_dict(self, type_to_save: Literal["header_wolf", "bounds"] = "header_wolf") -> dict:

        if type_to_save == "header_wolf":
            d= {
                "header_type": "header_wolf",
                "dx": self.dx,
                "dy": self.dy,
                "origx": self.origx,
                "origy": self.origy,
                "nbx": self.nbx,
                "nby": self.nby
                }
        elif type_to_save == "bounds":
            d= {
                "header_type": "bounds",
                "minx": self.origx,
                "miny": self.origy,
                "maxx": self.origx + self.dx * self.nbx,
                "maxy": self.origy + self.dy * self.nby,
                }
        else:
            raise ValueError(f"Unknown type_to_save '{type_to_save}'. Supported values are 'header_wolf' and 'bounds'.")

        return d

    @classmethod
    def from_dict(cls, d:dict, dxdy:tuple[float,float]=None, grid:"header_wolf"=None) -> "header_wolf":

        hdr_type = d.get("header_type", "header_wolf")

        newhdr = header_wolf()

        if hdr_type == "header_wolf":
            return header_wolf.make(
                orig=(d["origx"], d["origy"]),
                nb=(d["nbx"], d["nby"]),
                d=(d["dx"], d["dy"])
                )

        elif hdr_type == "bounds":
            assert dxdy is not None or grid is not None, _('dxdy must be provided when loading from bounds')

            if dxdy is not None:
                if grid is None:
                    grid = header_wolf.make(orig = (d["minx"], d["miny"]),
                                            nb = (1,1),
                                            d = dxdy)
                    return header_wolf.make_from_xybounds_grid(xbounds=(d["minx"], d["maxx"]),
                                                               ybounds=(d["miny"], d["maxy"]),
                                                               d=dxdy,
                                                               grid_to_align=grid)
                if grid is not None:
                    return header_wolf.make_from_xybounds_grid(
                        xbounds=(d["minx"], d["maxx"]),
                        ybounds=(d["miny"], d["maxy"]),
                        d=dxdy,
                        grid_to_align=grid
                        )

            elif grid is not None:
                return header_wolf.make_from_xybounds_grid(
                    xbounds=(d["minx"], d["maxx"]),
                    ybounds=(d["miny"], d["maxy"]),
                    d=(grid.dx, grid.dy),
                    grid_to_align=grid
                    )

class NewArray(wx.Dialog):
    """
    wx GUI interaction to create a new WolfArray

    Once filled, user/__init__ must call "init_from_new"
    """

    def __init__(self, parent, mapviewer= None):
        super(NewArray, self).__init__(parent, title=_('New array'), size=(300, 300),
                                       style=wx.DEFAULT_DIALOG_STYLE | wx.TAB_TRAVERSAL | wx.OK)

        self._mapviewer = mapviewer

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        glsizer = self.CreateSeparatedButtonSizer(wx.OK)

        gSizer1 = wx.GridSizer(6, 2, 0, 0)

        glsizer.Insert(0, gSizer1)

        self.m_staticText9 = wx.StaticText(self, wx.ID_ANY, u"dX [m]", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText9.Wrap(-1)

        gSizer1.Add(self.m_staticText9, 0, wx.ALL, 5)

        self.dx = wx.TextCtrl(self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.dx, 0, wx.ALL, 5)

        self.m_staticText10 = wx.StaticText(self, wx.ID_ANY, u"dY [m]", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText10.Wrap(-1)

        gSizer1.Add(self.m_staticText10, 0, wx.ALL, 5)

        self.dy = wx.TextCtrl(self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.dy, 0, wx.ALL, 5)

        self.m_staticText11 = wx.StaticText(self, wx.ID_ANY, u"NbX [-]", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText11.Wrap(-1)

        gSizer1.Add(self.m_staticText11, 0, wx.ALL, 5)

        self.nbx = wx.TextCtrl(self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.nbx, 0, wx.ALL, 5)

        self.m_staticText12 = wx.StaticText(self, wx.ID_ANY, u"NbY [-]", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText12.Wrap(-1)

        gSizer1.Add(self.m_staticText12, 0, wx.ALL, 5)

        self.nby = wx.TextCtrl(self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.nby, 0, wx.ALL, 5)

        self.m_staticText13 = wx.StaticText(self, wx.ID_ANY, u"Origin X [m]", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText13.Wrap(-1)

        gSizer1.Add(self.m_staticText13, 0, wx.ALL, 5)

        self.ox = wx.TextCtrl(self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.ox, 0, wx.ALL, 5)

        self.m_staticText14 = wx.StaticText(self, wx.ID_ANY, u"Origin Y [m]", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText14.Wrap(-1)

        gSizer1.Add(self.m_staticText14, 0, wx.ALL, 5)

        self.oy = wx.TextCtrl(self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.oy, 0, wx.ALL, 5)

        # self.OK = wx.Button( self, wx.ID_ANY, u"Validate", wx.DefaultPosition, wx.DefaultSize, 0 )
        # gSizer1.Add( self.OK, 0, wx.ALL, 5 )

        sizer_hor = wx.BoxSizer(wx.HORIZONTAL)
        self._sameas_button = wx.Button(self, wx.ID_ANY, u"Same as...", wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_hor.Add(self._sameas_button, 0, wx.ALL, 5)

        if self._mapviewer is not None:
            self._samezoom_parent = wx.Button(self, wx.ID_ANY, u"Current zoom...", wx.DefaultPosition, wx.DefaultSize, 0)
            sizer_hor.Add(self._samezoom_parent, 0, wx.ALL, 5)
            self._samezoom_parent.Bind(wx.EVT_BUTTON, self.on_samezoom_parent)

        glsizer.Add(sizer_hor, 1, wx.ALL, 1)

        self._sameas_button.Bind(wx.EVT_BUTTON, self.on_sameas)

        self.nbx.SetFocus()
        self.nbx.SelectAll()
        self.SetSizer(glsizer)
        self.Layout()

        self.Centre(wx.BOTH)

    def on_samezoom_parent(self, event):
        """ Fill the fields with the same values as the parent """

        if self._mapviewer is not None:

            with wx.TextEntryDialog(self, _('Round to the nearest x m ?'), _('Round to the nearest x m ?'), '10', style=wx.OK | wx.CANCEL) as dlg:
                if dlg.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind

                try:
                    roundto = int(dlg.GetValue())
                except:
                    logging.error(_('The value must be a number'))
                    return

            xmin, ymin, xmax, ymax = self._mapviewer.get_canvas_bounds()
            self.ox.SetValue(str((xmin // roundto) * roundto))
            self.oy.SetValue(str((ymin // roundto) * roundto))

            self.dx.SetValue(str(1))
            self.dy.SetValue(str(1))

            self.nbx.SetValue(str((math.ceil(xmax - xmin) // roundto) *roundto))
            self.nby.SetValue(str((math.ceil(ymax - ymin) // roundto) *roundto))


    def on_sameas(self, event):
        """ Fill the fields with the same values as a file array """

        with wx.FileDialog(self, _("Choose a file"), wildcard="Wolf array files (*.bin;*.flt;*.tif,*.npy)|*.bin;*.flt;*.tif;*.npy",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            filename = fileDialog.GetPath()
            header = header_wolf()
            header.read_txt_header(filename)

            self.dx.SetValue(str(header.dx))
            self.dy.SetValue(str(header.dy))
            self.nbx.SetValue(str(header.nbx))
            self.nby.SetValue(str(header.nby))
            self.ox.SetValue(str(header.origx))
            self.oy.SetValue(str(header.origy))

#FIXME : Generalize to 3D
class CropDialog(wx.Dialog):
    """
    wx GUI interaction to crop 2D array's data

    Used in "read_data" of a WolfArray
    """

    def __init__(self, parent, mapviewer=None):
        super(CropDialog, self).__init__(parent, title=_('Cropping array'), size=(300, 300),
                                         style=wx.DEFAULT_DIALOG_STYLE | wx.TAB_TRAVERSAL | wx.OK)

        self._mapviewer = mapviewer

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        glsizer = self.CreateSeparatedButtonSizer(wx.OK)

        gSizer1 = wx.GridSizer(6, 2, 0, 0)

        glsizer.Insert(0, gSizer1)

        self.m_staticText9 = wx.StaticText(self, wx.ID_ANY, u"dX", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText9.Wrap(-1)

        gSizer1.Add(self.m_staticText9, 0, wx.ALL, 5)

        self.dx = wx.TextCtrl(self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.dx, 0, wx.ALL, 5)

        self.m_staticText10 = wx.StaticText(self, wx.ID_ANY, u"dY", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText10.Wrap(-1)

        gSizer1.Add(self.m_staticText10, 0, wx.ALL, 5)

        self.dy = wx.TextCtrl(self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.dy, 0, wx.ALL, 5)

        self.m_staticText11 = wx.StaticText(self, wx.ID_ANY, u"OrigX - lower left corner", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText11.Wrap(-1)

        gSizer1.Add(self.m_staticText11, 0, wx.ALL, 5)

        self.ox = wx.TextCtrl(self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.ox, 0, wx.ALL, 5)

        self.m_staticText12 = wx.StaticText(self, wx.ID_ANY, u"OrigY - lower left corner", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText12.Wrap(-1)

        gSizer1.Add(self.m_staticText12, 0, wx.ALL, 5)

        self.oy = wx.TextCtrl(self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.oy, 0, wx.ALL, 5)

        self.m_staticText13 = wx.StaticText(self, wx.ID_ANY, u"EndX - upper right corner", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText13.Wrap(-1)

        gSizer1.Add(self.m_staticText13, 0, wx.ALL, 5)

        self.ex = wx.TextCtrl(self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.ex, 0, wx.ALL, 5)

        self.m_staticText14 = wx.StaticText(self, wx.ID_ANY, u"EndY - upper right corner", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText14.Wrap(-1)

        gSizer1.Add(self.m_staticText14, 0, wx.ALL, 5)

        self.ey = wx.TextCtrl(self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        gSizer1.Add(self.ey, 0, wx.ALL, 5)

        # self.OK = wx.Button( self, wx.ID_ANY, u"Validate", wx.DefaultPosition, wx.DefaultSize, 0 )
        # gSizer1.Add( self.OK, 0, wx.ALL, 5 )

        sizer_hor = wx.BoxSizer(wx.HORIZONTAL)
        self.sameas_button = wx.Button(self, wx.ID_ANY, u"Same as...", wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_hor.Add(self.sameas_button, 0, wx.ALL, 5)

        if self._mapviewer is not None:
            self.samezoom_parent = wx.Button(self, wx.ID_ANY, u"Current zoom...", wx.DefaultPosition, wx.DefaultSize, 0)
            sizer_hor.Add(self.samezoom_parent, 0, wx.ALL, 5)
            self.samezoom_parent.Bind(wx.EVT_BUTTON, self.on_samezoom_parent)

        glsizer.Add(sizer_hor, 1, wx.ALL, 1)

        self.sameas_button.Bind(wx.EVT_BUTTON, self.on_sameas)

        self.ox.SetFocus()
        self.ox.SelectAll()
        self.SetSizer(glsizer)
        self.Layout()

        self.Centre(wx.BOTH)

    def get_header(self):
        """ Return a header_wolf object with the values of the dialog """

        myhead = header_wolf()
        myhead.origx = float(self.ox.Value)
        myhead.origy = float(self.oy.Value)
        myhead.dx = float(self.dx.Value)
        myhead.dy = float(self.dy.Value)
        myhead.nbx = int((float(self.ex.Value) - myhead.origx) / myhead.dx)
        myhead.nby = int((float(self.ey.Value) - myhead.origy) / myhead.dy)

        return myhead

    def on_samezoom_parent(self, event):
        """ Fill the fields with the same values as the parent """

        if self._mapviewer is not None:

            with wx.TextEntryDialog(self, _('Round to the nearest x m ?'), _('Round to the nearest x m ?'), '10', style=wx.OK | wx.CANCEL) as dlg:
                if dlg.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind

                try:
                    roundto = int(dlg.GetValue())
                except:
                    logging.error(_('The value must be a number'))
                    return

            xmin, ymin, xmax, ymax = self._mapviewer.get_canvas_bounds()
            self.ox.SetValue(str((xmin // roundto) * roundto))
            self.oy.SetValue(str((ymin // roundto) * roundto))

            # self.dx.SetValue(str(1))
            # self.dy.SetValue(str(1))

            self.ex.SetValue(str((math.ceil(xmax // roundto) * roundto)))
            self.ey.SetValue(str((math.ceil(ymax // roundto) * roundto)))


    def on_sameas(self, event):
        """ Fill the fields with the same values as a file array """

        with wx.FileDialog(self, _("Choose a file"), wildcard="Wolf array files (*.bin;*.flt;*.tif,*.npy)|*.bin;*.flt;*.tif;*.npy",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            filename = fileDialog.GetPath()
            header = header_wolf()
            header.read_txt_header(filename)

            # self.dx.SetValue(str(header.dx))
            # self.dy.SetValue(str(header.dy))
            self.ox.SetValue(str(header.origx))
            self.oy.SetValue(str(header.origy))
            self.ex.SetValue(str(header.origx + header.nbx * header.dx))
            self.ey.SetValue(str(header.origy + header.nby * header.dy))

    def get_crop(self):
        """ Return the crop values """
        try:
            return [[float(self.ox.Value), float(self.oy.Value)], [float(self.ex.Value), float(self.ey.Value)]]
        except:
            logging.error(_('Values must be numbers'))
            return None

import string
class IntValidator(wx.Validator):
    ''' Validates data as it is entered into the text controls. '''

    #----------------------------------------------------------------------
    def __init__(self):
        super(IntValidator, self).__init__()
        self.Bind(wx.EVT_CHAR, self.OnChar)

    #----------------------------------------------------------------------
    def Clone(self):
        '''Required Validator method'''
        return IntValidator()

    #----------------------------------------------------------------------
    def Validate(self, win):
        return True

    #----------------------------------------------------------------------
    def TransferToWindow(self):
        return True

    #----------------------------------------------------------------------
    def TransferFromWindow(self):
        return True

    #----------------------------------------------------------------------
    def OnChar(self, event):
        keycode = int(event.GetKeyCode())
        if keycode < 256:
            #print keycode
            key = chr(keycode)

            if key not in string.digits:
                return
        event.Skip()
class Ops_Array(wx.Frame):
    """
    Operations wx.Frame on WolfArray class

    This class is used to perform operations on a WolfArray
    """

    def __init__(self, parentarray:"WolfArray", mapviewer=None):
        """ Init the Ops_Array class

        :param parentarray: WolfArray to operate on
        :param mapviewer: WolfMapViewer to update if necessary
        """

        self.parentarray:WolfArray
        self.parentarray = parentarray

        from .PyDraw import WolfMapViewer
        self.mapviewer:WolfMapViewer
        self.mapviewer = mapviewer

        self.wx_exists = wx.App.Get() is not None

        # active objects
        self.active_vector:vector = None
        self.active_zone:zone = None
        self.active_array:WolfArray = self.parentarray

        self.myzones = Zones(parent=self)
        self.myzonetmp = zone(name='tmp')
        self.vectmp = vector(name='tmp')
        self.fnsave = ''

        self.myzonetmp.add_vector(self.vectmp, forceparent=True)
        self.myzones.add_zone(self.myzonetmp, forceparent=True)

        self.myzones.mapviewer = mapviewer

        self._levels = []

        if self.wx_exists:
            self.set_GUI()

    @property
    def usemask(self):
        """ Return the usemask Value """
        return self.selectrestricttomask.GetValue()

    @property
    def idx(self):
        """ Return the idx of the parentarray """
        return self.parentarray.idx

    def get_mapviewer(self):
        """ Retourne l'instance WolfMapViewer """
        return self.mapviewer

    def get_linked_arrays(self):
        """ Pour compatibilité avec la gestion de vecteur et WolfMapViewer """
        if self.is_shared:
            comp, diff = self._get_comp_elts_diff()
            ret = {}
            for elt in comp + diff:
                ret[elt.idx] = elt
            return ret
        else:
            return {self.parentarray.idx: self.parentarray}

    def set_GUI(self):
        """Set the wx GUI"""

        super(Ops_Array, self).__init__(None, title=_('Operators'), size=(600, 700),
                                        style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        # GUI
        self.Bind(wx.EVT_CLOSE, self.onclose)
        self.Bind(wx.EVT_SHOW, self.onshow)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        # GUI Notebook
        self.array_ops = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize)

        #  panel Selection
        # -----------------

        self.selection = wx.Panel(self.array_ops, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.array_ops.AddPage(self.selection, _("Selection"), True)

        #  panel Operations
        # -----------------

        self.operation = wx.Panel(self.array_ops, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.array_ops.AddPage(self.operation, _("Operators"), False)

        #  panel Mask
        # -----------------

        self.mask = wx.Panel(self.array_ops, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.array_ops.AddPage(self.mask, _("Mask"), False)

        #  panel Interpolation
        # ---------------------

        # if self.parentarray.nb_blocks>0:
        #     self.Interpolation  = None
        # else:
        self.Interpolation = wx.Panel(self.array_ops, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.array_ops.AddPage(self.Interpolation, _("Interpolation"), False)

        #  panel Tools/Misc
        # -----------------

        self.tools = wx.Panel(self.array_ops, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.array_ops.AddPage(self.tools, _("Miscellaneous"), False)

        # panel PALETTE de couleurs
        # -------------------------

        self.Palette = PlotPanel(self.array_ops, wx.ID_ANY, toolbar=False)
        self.palgrid = CpGrid(self.Palette, wx.ID_ANY, style=wx.WANTS_CHARS | wx.TE_CENTER)
        self.palapply = wx.Button(self.Palette, wx.ID_ANY, _("Apply"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.palapply.SetToolTip(_('Apply changes in memory'))
        self.palgrid.CreateGrid(16, 4)
        self.palauto = wx.CheckBox(self.Palette, wx.ID_ANY, _("Automatic"), wx.DefaultPosition, wx.DefaultSize,
                                   style=wx.CHK_CHECKED)
        self.palauto.SetToolTip(_('Activating/Deactivating automatic colormap values distribution'))

        self.uniforminparts = wx.CheckBox(self.Palette, wx.ID_ANY, _("Uniform in parts"), wx.DefaultPosition, wx.DefaultSize,
                                   style=wx.CHK_UNCHECKED)
        self.uniforminparts.SetToolTip(_('Activating/Deactivating linear interpolation'))

        self.palalpha = wx.CheckBox(self.Palette, wx.ID_ANY, _("Opacity"), wx.DefaultPosition, wx.DefaultSize,
                                    style=wx.CHK_CHECKED)
        self.palalpha.SetToolTip(_('Activating/Deactivating transparency of the array'))
        self.palshader = wx.CheckBox(self.Palette, wx.ID_ANY, _("Hillshade"), wx.DefaultPosition, wx.DefaultSize,
                                     style=wx.CHK_CHECKED)
        self.palshader.SetToolTip(_('Activating/Deactivating hillshade on colors and create if necessary a gray map'))

        self.palalphaslider = wx.Slider(self.Palette, wx.ID_ANY, 100, 0, 100, wx.DefaultPosition, wx.DefaultSize,
                                        wx.SL_HORIZONTAL, name='palslider')
        self.palalphaslider.SetToolTip(_('Global opacity (transparent --> opaque)'))

        self.palalphahillshade = wx.Slider(self.Palette, wx.ID_ANY, 100, 0, 100, wx.DefaultPosition, wx.DefaultSize,
                                           wx.SL_HORIZONTAL, name='palalphaslider')
        self.palalphahillshade.SetToolTip(_('Hillshade transparency (transparent-->opaque)'))
        self.palazimuthhillshade = wx.Slider(self.Palette, wx.ID_ANY, 315, 0, 360, wx.DefaultPosition, wx.DefaultSize,
                                             wx.SL_HORIZONTAL, name='palazimuthslider')
        self.palazimuthhillshade.SetToolTip(_('Hillshade azimuth (0-->360)'))
        self.palaltitudehillshade = wx.Slider(self.Palette, wx.ID_ANY, 0, 0, 90, wx.DefaultPosition, wx.DefaultSize,
                                              wx.SL_HORIZONTAL, name='palaltitudeslider')
        self.palaltitudehillshade.SetToolTip(_('Hillshade altitude (0-->90)'))

        self.palsave = wx.Button(self.Palette, wx.ID_ANY, _("Save to file"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.palsave.SetToolTip(_('Save colormap on .pal file'))

        sizer_loadpal = wx.BoxSizer(wx.HORIZONTAL)

        self.palload = wx.Button(self.Palette, wx.ID_ANY, _("Load from file"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.palload.SetToolTip(_('Load colormap from .pal file'))

        self._default_pal = wx.Button(self.Palette, wx.ID_ANY, _("Load precomputed"), wx.DefaultPosition, wx.DefaultSize, 0)
        self._default_pal.SetToolTip(_('Load a default colormap available in the software'))

        sizer_loadpal.Add(self.palload, 1, wx.EXPAND)
        sizer_loadpal.Add(self._default_pal, 1, wx.EXPAND)

        self.palimage = wx.Button(self.Palette, wx.ID_ANY, _("Create image"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.palimage.SetToolTip(_('Generate colormap image (horizontal, vertical or both) and save to disk'))
        self.paldistribute = wx.Button(self.Palette, wx.ID_ANY, _("Evenly spaced"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.paldistribute.SetToolTip(_('Set colormap values based on minimum+maximum or minimum+step'))
        if self.parentarray.mypal.automatic:
            self.palauto.SetValue(1)
        else:
            self.palauto.SetValue(0)

        if self.parentarray.mypal.interval_cst:
            self.uniforminparts.SetValue(1)
        else:
            self.uniforminparts.SetValue(0)

        self.palalpha.SetValue(1)

        self.palchoosecolor = wx.Button(self.Palette, wx.ID_ANY, _("Choose color for current value"),
                                        wx.DefaultPosition, wx.DefaultSize)
        self.palchoosecolor.SetToolTip(_('Color dialog box for the current selected value in the grid'))

        self.Palette.sizerfig.Add(self.palgrid, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palauto, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.uniforminparts, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palalpha, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palalphaslider, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palshader, 1, wx.EXPAND)

        self.Palette.sizer.Add(self.palalphahillshade, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palazimuthhillshade, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palaltitudehillshade, 1, wx.EXPAND)

        self.Palette.sizer.Add(self.palchoosecolor, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palapply, 1, wx.EXPAND)
        self.Palette.sizer.Add(sizer_loadpal, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palsave, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.palimage, 1, wx.EXPAND)
        self.Palette.sizer.Add(self.paldistribute, 1 , wx.EXPAND)

        self.array_ops.AddPage(self.Palette, _("Palette"), False)

        # HISTOGRAMMES
        # ----------------

        self.histo = PlotPanel(self.array_ops, wx.ID_ANY, toolbar=True)
        self.histoupdate = wx.Button(self.histo, wx.ID_ANY, _("All data..."), wx.DefaultPosition, wx.DefaultSize, 0)
        self.histoupdatezoom = wx.Button(self.histo, wx.ID_ANY, _("On zoom..."), wx.DefaultPosition, wx.DefaultSize, 0)
        self.histoupdateerase = wx.Button(self.histo, wx.ID_ANY, _("Erase"), wx.DefaultPosition, wx.DefaultSize, 0)

        self.histo.sizer.Add(self.histoupdate, 0, wx.EXPAND)
        self.histo.sizer.Add(self.histoupdatezoom, 0, wx.EXPAND)
        self.histo.sizer.Add(self.histoupdateerase, 0, wx.EXPAND)

        self.array_ops.AddPage(self.histo, _("Histogram"), False)

        # LINKS
        # ----------------

        self.links = wx.Panel(self.array_ops, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.array_ops.AddPage(self.links, _("Links"), False)

        # Interpolation
        # ----------------

        if self.Interpolation is not None:

            gSizer1 = wx.GridSizer(0, 2, 0, 0)

            self.interp2D = wx.Button(self.Interpolation, wx.ID_ANY, _("2D Interpolation on selection"), wx.DefaultPosition,
                                    wx.DefaultSize, 0)
            self.interp2D.SetToolTip(_('Spatial interpolation based on nodes stored in the named groups. \n The interpolation apply only on the current selection.'))
            gSizer1.Add(self.interp2D, 0, wx.EXPAND)
            self.interp2D.Bind(wx.EVT_BUTTON, self.interpolation2D)

            self.m_button7 = wx.Button(self.Interpolation, wx.ID_ANY, _("Stage/Volume/Surface evaluation"), wx.DefaultPosition,
                                    wx.DefaultSize, 0)
            self.m_button7.SetToolTip(_('Evaluate stage-volume-surface relationship.\nResults : csv and array saved on disk\n\n CAUTION : This function will be applied only on the selected area except if you select "all".\nIn the latter case, the computation time could be long if the array are very large.'))

            if self.parentarray.nb_blocks>0:
                self.m_button7.Disable()
                self.m_button7.SetToolTip(_('Evaluate stage-volume-surface relationship.\nResults : arrays and csv file saved on disk\n\nThis function is not available for multi-block arrays.'))

            gSizer1.Add(self.m_button7, 0, wx.EXPAND)
            self.m_button7.Bind(wx.EVT_BUTTON, self.volumesurface)

            self.m_button8 = wx.Button(self.Interpolation, wx.ID_ANY, _("Interpolation on active zone \n polygons"),
                                    wx.DefaultPosition, wx.DefaultSize, 0)
            self.m_button8.SetToolTip(_('Spatial interpolation based on all polygons in active zone'))

            gSizer1.Add(self.m_button8, 0, wx.EXPAND)
            self.m_button8.Bind(wx.EVT_BUTTON, self.interp2Dpolygons)

            self.m_button9 = wx.Button(self.Interpolation, wx.ID_ANY, _("Interpolation on active zone \n 3D polylines"),
                                    wx.DefaultPosition, wx.DefaultSize, 0)
            self.m_button9.SetToolTip(_('Spatial interpolation based on all polylines in active zone'))

            gSizer1.Add(self.m_button9, 0, wx.EXPAND)
            self.m_button9.Bind(wx.EVT_BUTTON, self.interp2Dpolylines)

            self.m_button10 = wx.Button(self.Interpolation, wx.ID_ANY, _("Interpolation on active vector \n polygon"),
                                        wx.DefaultPosition, wx.DefaultSize, 0)
            self.m_button10.SetToolTip(_('Spatial interpolation based on active polygon'))

            gSizer1.Add(self.m_button10, 0, wx.EXPAND)
            self.m_button10.Bind(wx.EVT_BUTTON, self.interp2Dpolygon)

            self.m_button11 = wx.Button(self.Interpolation, wx.ID_ANY, _("Interpolation on active vector \n 3D polyline"),
                                        wx.DefaultPosition, wx.DefaultSize, 0)
            self.m_button11.SetToolTip(_('Spatial interpolation based on active polyline'))

            gSizer1.Add(self.m_button11, 0, wx.EXPAND)
            self.m_button11.Bind(wx.EVT_BUTTON, self.interp2Dpolyline)

            self.Interpolation.SetSizer(gSizer1)
            self.Interpolation.Layout()
            gSizer1.Fit(self.Interpolation)

        # Tools
        # ----------------

        Toolssizer = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.lbl_nullval = wx.StaticText(self.tools,label=_('Null value'))
        self.txt_nullval = wx.TextCtrl(self.tools,value=str(self.parentarray.nullvalue), style=wx.TE_CENTER)
        self.txt_nullval.SetToolTip(_('Array null value'))
        hbox.Add(self.lbl_nullval, 0, wx.EXPAND|wx.ALL)
        hbox.Add(self.txt_nullval, 1, wx.EXPAND|wx.ALL)

        self.ApplyTools = wx.Button(self.tools, wx.ID_ANY, _("Apply null value"), wx.DefaultPosition,wx.DefaultSize, 0)


        self.nullborder = wx.Button(self.tools, wx.ID_ANY, _("Null border"), wx.DefaultPosition,wx.DefaultSize, 0)

        self.filter_zone = wx.Button(self.tools, wx.ID_ANY, _("Filter zone"), wx.DefaultPosition,wx.DefaultSize, 0)

        self.labelling = wx.Button(self.tools, wx.ID_ANY, _("Labelling"), wx.DefaultPosition,wx.DefaultSize, 0)

        stats_sizer = wx.BoxSizer(wx.HORIZONTAL)
        stats_sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.statistics = wx.Button(self.tools, wx.ID_ANY, _("Statistics"), wx.DefaultPosition,wx.DefaultSize, 0)
        self.plot_stats = wx.Button(self.tools, wx.ID_ANY, _("Plot statistics\nCurrent zoom"), wx.DefaultPosition,wx.DefaultSize, 0)
        self.plot_stats_zone = wx.Button(self.tools, wx.ID_ANY, _("Plot statistics\nCurrent zone"), wx.DefaultPosition,wx.DefaultSize, 0)
        self.plot_stats_vector = wx.Button(self.tools, wx.ID_ANY, _("Plot statistics\nCurrent vector"), wx.DefaultPosition,wx.DefaultSize, 0)

        stats_sizer.Add(self.statistics, 1, wx.EXPAND)
        stats_sizer.Add(self.plot_stats, 1, wx.EXPAND)

        stats_sizer2.Add(self.plot_stats_zone, 1, wx.EXPAND)
        stats_sizer2.Add(self.plot_stats_vector, 1, wx.EXPAND)

        self.clean = wx.Button(self.tools, wx.ID_ANY, _("Clean"), wx.DefaultPosition,wx.DefaultSize, 0)

        self.extract_selection = wx.Button(self.tools, wx.ID_ANY, _("Extract selection"), wx.DefaultPosition,wx.DefaultSize, 0)

        cont_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._contour_int = wx.Button(self.tools, wx.ID_ANY, _("Contour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self._contour_list = wx.Button(self.tools, wx.ID_ANY, _("Contour specific"), wx.DefaultPosition, wx.DefaultSize, 0)

        cont_sizer.Add(self._contour_int, 1, wx.EXPAND)
        cont_sizer.Add(self._contour_list, 1, wx.EXPAND)

        Toolssizer.Add(hbox, 0, wx.EXPAND)
        Toolssizer.Add(self.ApplyTools, 1, wx.EXPAND)
        Toolssizer.Add(self.nullborder, 1, wx.EXPAND)
        Toolssizer.Add(self.filter_zone, 1, wx.EXPAND)
        Toolssizer.Add(self.labelling, 1, wx.EXPAND)
        Toolssizer.Add(self.clean, 1, wx.EXPAND)
        Toolssizer.Add(self.extract_selection, 1, wx.EXPAND)
        Toolssizer.Add(stats_sizer, 1, wx.EXPAND)
        Toolssizer.Add(stats_sizer2, 1, wx.EXPAND)
        Toolssizer.Add(cont_sizer, 1, wx.EXPAND)

        self.ApplyTools.SetToolTip(_("Apply Nullvalue into memory/object"))
        self.nullborder.SetToolTip(_("Set null value on the border of the array\n\nYou will be asked for the width of the border (in cells)"))
        self.filter_zone.SetToolTip(_("Filter the array based on contiguous zones\n\nConservation of the ones which contain selected nodes"))
        self.labelling.SetToolTip(_("Labelling of contiguous zones using Scipy.label function\n\nReplacing the current values by the labels"))
        self.clean.SetToolTip(_("Clean the array\n\nRemove small isolated patches of data"))
        self.extract_selection.SetToolTip(_("Extract the current selection"))
        self.statistics.SetToolTip(_("Compute statistics on the array\n\nResults are displayed in a dialog box"))
        self.plot_stats.SetToolTip(_("Plot statistics on the array\n\nResults are displayed in a separate figure"))

        self.tools.SetSizer(Toolssizer)
        self.tools.Layout()
        Toolssizer.Fit(self.tools)

        # Selection
        # ----------------

        bSizer15 = wx.BoxSizer(wx.VERTICAL)

        bSizer21 = wx.BoxSizer(wx.HORIZONTAL)

        bSizer16 = wx.BoxSizer(wx.VERTICAL)
        bSizer16_1 = wx.BoxSizer(wx.VERTICAL)
        bSizer16_2 = wx.BoxSizer(wx.VERTICAL)
        bSizer16_3 = wx.BoxSizer(wx.VERTICAL)

        selectmethodChoices = [_("by clicks"),
                               _("inside active vector"),
                               _("inside active zone"),
                               _("inside temporary vector"),
                               _("along active vector"),
                               _("along active zone"),
                               _("along temporary vector"),
                            #    _("outside active vector")
                               ]
        self.selectmethod = wx.RadioBox(self.selection, wx.ID_ANY, _("How to select nodes?"), wx.DefaultPosition,
                                        wx.DefaultSize, selectmethodChoices, 1, wx.RA_SPECIFY_COLS)
        self.selectmethod.SetSelection(0)
        self.selectmethod.SetToolTip(_("Selection mode : \n - one by one (keyboard shortcut N) \n- inside the currently activated polygon (keyboard shortcut V) \n- inside the currently activated zone (multipolygons) \n- inside a temporary polygon (keyboard shortcut B) \n- along the currently activated polyline \n- along the currently activated zone (multipolylines) \n- along a temporary polyline"))

        bSizer16.Add(self.selectmethod, 0, wx.ALL, 5)

        self.selectrestricttomask = wx.CheckBox(self.selection,wx.ID_ANY,_('Use mask to restrict'))
        self.selectrestricttomask.SetValue(True)
        self.selectrestricttomask.SetToolTip(_('If checked, the selection will be restricted by the mask data'))

        bSizer16.Add(self.selectrestricttomask, 0, wx.ALL, 5)

        self.LaunchSelection = wx.Button(self.selection, wx.ID_ANY,
                                         _("Action !"), wx.DefaultPosition,
                                         wx.DefaultSize, 0)
        # self.LaunchSelection.SetBackgroundColour((0,128,64,255))
        self.LaunchSelection.SetDefault()
        # self.LaunchSelection.SetForegroundColour((255,255,255,255))
        font = wx.Font(12, wx.FONTFAMILY_DECORATIVE, 0, 90, underline = False,faceName ="")
        self.LaunchSelection.SetFont(font)

        bSizer16.Add(self.LaunchSelection, 0, wx.EXPAND)

        self.AllSelection = wx.Button(self.selection, wx.ID_ANY,
                                      _("Select all nodes"), wx.DefaultPosition,
                                      wx.DefaultSize, 0)
        self.AllSelection.SetToolTip(_("Select all nodes in one click - store 'All' in the selection list"))
        bSizer16_1.Add(self.AllSelection, 1, wx.EXPAND)

        memory_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.MoveSelection = wx.Button(self.selection, wx.ID_ANY,
                                       _("Move selection to..."), wx.DefaultPosition,
                                       wx.DefaultSize, 0)
        self.MoveSelection.SetToolTip(_("Store the current selection in an indexed list -- useful for some interpolation methods"))

        self.ReselectMemory = wx.Button(self.selection, wx.ID_ANY,
                                        _("Reselect from..."), wx.DefaultPosition,
                                        wx.DefaultSize, 0)
        self.ReselectMemory.SetToolTip(_("Reselect the nodes from an indexed list"))

        memory_sizer.Add(self.MoveSelection, 1, wx.EXPAND)
        memory_sizer.Add(self.ReselectMemory, 1, wx.EXPAND)
        bSizer16_1.Add(memory_sizer, 1, wx.EXPAND)

        reset_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ResetSelection = wx.Button(self.selection, wx.ID_ANY,
                                        _("Reset"), wx.DefaultPosition,
                                        wx.DefaultSize, 0)
        self.ResetSelection.SetToolTip(_("Reset the current selection list (keyboard shortcut r)"))

        self.ResetAllSelection = wx.Button(self.selection, wx.ID_ANY,
                                           _("Reset All"), wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        self.ResetAllSelection.SetToolTip(_("Reset the current selection list and the indexed lists (keyboard shortcut R)"))

        reset_sizer.Add(self.ResetSelection, 1, wx.EXPAND)
        reset_sizer.Add(self.ResetAllSelection, 1, wx.EXPAND)
        bSizer16_1.Add(reset_sizer, 1, wx.EXPAND)

        save_load_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SaveSelection = wx.Button(self.selection, wx.ID_ANY,
                                        _("Save"), wx.DefaultPosition,
                                        wx.DefaultSize, 0)
        self.SaveSelection.SetToolTip(_("Save the current selection list to disk"))

        self.LoadSelection = wx.Button(self.selection, wx.ID_ANY,
                                        _("Load"), wx.DefaultPosition,
                                        wx.DefaultSize, 0)
        self.LoadSelection.SetToolTip(_("Load a selection list from disk"))

        save_load_sizer.Add(self.SaveSelection, 1, wx.EXPAND)
        save_load_sizer.Add(self.LoadSelection, 1, wx.EXPAND)
        bSizer16_1.Add(save_load_sizer, 1, wx.EXPAND)

        clipboad_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.to_clipboard_str = wx.Button(self.selection, wx.ID_ANY, _("To clipboard (str)"), wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.to_clipboard_str.SetToolTip(_("Copy the current selection to the clipboard as a string"))

        self.to_clipboard_script = wx.Button(self.selection, wx.ID_ANY, _("To clipboard (script)"), wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.to_clipboard_script.SetToolTip(_("Copy the current selection to the clipboard as a script"))

        clipboad_sizer.Add(self.to_clipboard_str, 1, wx.EXPAND)
        clipboad_sizer.Add(self.to_clipboard_script, 1, wx.EXPAND)

        erode_dilate_sizer = wx.BoxSizer(wx.VERTICAL)
        self.expand_selection = wx.Button(self.selection, wx.ID_ANY, _("Dilate"), wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.expand_selection.SetToolTip(_("Expand the current selection to the nearest nodes"))

        self.contract_selection = wx.Button(self.selection, wx.ID_ANY, _("Erode"), wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.contract_selection.SetToolTip(_("Contract the current selection to the nearest nodes"))

        self.expand_unselect_interior = wx.Button(self.selection, wx.ID_ANY, _("Dilate contour"), wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.expand_unselect_interior.SetToolTip(_("Expand the contour of the current selection and unselect the interior nodes"))

        self.unselect_interior = wx.Button(self.selection, wx.ID_ANY, _("Unselect interior"), wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.unselect_interior.SetToolTip(_("Conserve the contour of the current selection and unselect the interior nodes"))

        er_dil_1 = wx.BoxSizer(wx.HORIZONTAL)
        er_dil_2 = wx.BoxSizer(wx.HORIZONTAL)
        er_dil_1.Add(self.expand_selection, 1, wx.EXPAND)
        er_dil_1.Add(self.contract_selection, 1, wx.EXPAND)
        er_dil_2.Add(self.expand_unselect_interior, 1, wx.EXPAND)
        er_dil_2.Add(self.unselect_interior, 1, wx.EXPAND)

        erode_dilate_sizer.Add(er_dil_1, 1, wx.EXPAND)
        erode_dilate_sizer.Add(er_dil_2, 1, wx.EXPAND)

        erode_dilate_options = wx.BoxSizer(wx.HORIZONTAL)
        self._label_passes = wx.StaticText(self.selection, wx.ID_ANY, _("Passes"), wx.DefaultPosition, wx.DefaultSize, 0)
        self._erode_dilate_value = wx.TextCtrl(self.selection, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        self._erode_dilate_value.SetToolTip(_("Number of passes for the erode/dilate operation"))
        self._erode_dilate_value.SetValidator(validator=IntValidator())

        erode_dilate_options.Add(self._label_passes, 1, wx.EXPAND)
        erode_dilate_options.Add(self._erode_dilate_value, 1, wx.EXPAND)

        self._erode_dilate_structure = wx.ComboBox(self.selection, wx.ID_ANY, _("Cross"), wx.DefaultPosition, wx.DefaultSize,
                                                    ["Cross", "Square"], wx.CB_READONLY)
        self._erode_dilate_structure.SetToolTip(_("Structuring shape for the erode/dilate operation -- Cross-shaped is the 4 nearest nodes, Square-shaped is the 8 nearest nodes"))
        erode_dilate_options.Add(self._erode_dilate_structure, 1, wx.EXPAND)

        erode_dilate_sizer.Add(erode_dilate_options, 1, wx.EXPAND)

        # MultiBlocks
        # ----------------
        # Add a listbox to define the active blocks

        if self.parentarray.nb_blocks>0:
            self._list = wx.ListBox(self.selection,
                                    wx.ID_ANY,
                                    wx.DefaultPosition,
                                    wx.DefaultSize,
                                    [_('All')] + [str(i) for i in range(1, self.parentarray.nb_blocks+1)],
                                    style = wx.LB_MULTIPLE | wx.LB_NEEDED_SB)
            self._list.SetToolTip(_("Active block"))
            bSizer16.Add(self._list, 1, wx.EXPAND)

            self._list.Bind(wx.EVT_LISTBOX, self.OnBlockSelect)

            # self._open_block = wx.Button(self.selection, wx.ID_ANY, _("Open block"), wx.DefaultPosition,
            #                                 wx.DefaultSize, 0)

            # self._open_block.SetToolTip(_("Open the Operation manager for the selected block"))
            # self._open_block.Bind(wx.EVT_BUTTON, self.OnOpenBlock)

            # bSizer16.Add(self._open_block, 0, wx.EXPAND)

        bSizer16_1.Add(erode_dilate_sizer, 1, wx.EXPAND, 5)
        bSizer16_1.Add(clipboad_sizer, 1, wx.EXPAND)

        bSizer16.Add(bSizer16_1, 1, wx.EXPAND, 5)
        # bSizer16.Add(bSizer16_2, 1, wx.EXPAND, 5)
        bSizer21.Add(bSizer16, 1, wx.EXPAND, 5)

        # VECTORS Manager
        # ----------------

        bSizer17 = wx.BoxSizer(wx.VERTICAL)

        self.m_button2 = wx.Button(self.selection, wx.ID_ANY, _("Manage vectors"), wx.DefaultPosition, wx.DefaultSize,
                                   0)
        self.m_button2.SetToolTip(_("Open the vector manager attached to the array"))
        bSizer17.Add(self.m_button2, 0, wx.EXPAND)

        self.active_vector_id = wx.StaticText(self.selection, wx.ID_ANY, _("Active vector"), wx.DefaultPosition,
                                              wx.DefaultSize, 0)
        self.active_vector_id.Wrap(-1)

        bSizer17.Add(self.active_vector_id, 0, wx.EXPAND)

        self.CurActiveparent = wx.StaticText(self.selection, wx.ID_ANY, _("Active parent"), wx.DefaultPosition,
                                             wx.DefaultSize, 0)
        self.CurActiveparent.Wrap(-1)

        bSizer17.Add(self.CurActiveparent, 0, wx.EXPAND)

        self.loadvec = wx.Button(self.selection, wx.ID_ANY, _("Load from file..."), wx.DefaultPosition, wx.DefaultSize,
                                 0)
        self.loadvec.SetToolTip(_("Load a vector file into the vector manager"))
        bSizer17.Add(self.loadvec, 0, wx.EXPAND)

        self.saveas = wx.Button(self.selection, wx.ID_ANY, _("Save as..."), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer17.Add(self.saveas, 0, wx.EXPAND)
        self.saveas.SetToolTip(_("Save the vector manager to a new vector file"))

        self.save = wx.Button(self.selection, wx.ID_ANY, _("Save"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.save.SetToolTip(_("Save the vector manager to the kwnown vector file"))
        bSizer17.Add(self.save, 0, wx.EXPAND)

        bSizer21.Add(bSizer17, 1, wx.EXPAND, 5)

        bSizer15.Add(bSizer21, 1, wx.EXPAND, 5)

        bSizer22 = wx.BoxSizer(wx.HORIZONTAL)

        self.nbselect = wx.StaticText(self.selection, wx.ID_ANY, _("nb"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.nbselect.Wrap(-1)

        bSizer22.Add(self.nbselect, 1, wx.EXPAND, 10)

        self.minx = wx.StaticText(self.selection, wx.ID_ANY, _("xmin"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.minx.Wrap(-1)

        self.minx.SetToolTip(_("X Mininum"))

        bSizer22.Add(self.minx, 1, wx.EXPAND, 10)

        self.maxx = wx.StaticText(self.selection, wx.ID_ANY, _("xmax"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.maxx.Wrap(-1)

        self.maxx.SetToolTip(_("X Maximum"))

        bSizer22.Add(self.maxx, 1, wx.EXPAND, 10)

        self.miny = wx.StaticText(self.selection, wx.ID_ANY, _("ymin"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.miny.Wrap(-1)

        self.miny.SetToolTip(_("Y Minimum"))

        bSizer22.Add(self.miny, 1, wx.EXPAND, 10)

        self.maxy = wx.StaticText(self.selection, wx.ID_ANY, _("ymax"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.maxy.Wrap(-1)

        self.maxy.SetToolTip(_("Y Maximum"))

        bSizer22.Add(self.maxy, 1, wx.EXPAND, 10)

        bSizer15.Add(bSizer22, 0, wx.EXPAND, 5)

        self.selection.SetSizer(bSizer15)
        self.selection.Layout()
        bSizer15.Fit(self.selection)

        # Mask
        sizermask = wx.BoxSizer(wx.VERTICAL)
        self.mask.SetSizer(sizermask)

        maskdata = wx.Button(self.mask, wx.ID_ANY, _("Mask nodes (only Condition )"), wx.DefaultPosition, wx.DefaultSize, 0)
        maskdata.SetToolTip(_("This action will use the condition AND NOT the operator to mask some selected nodes \n If no node selectd --> Nothing to do !!"))
        sizermask.Add(maskdata, 1, wx.EXPAND)
        maskdata.Bind(wx.EVT_BUTTON, self.Onmask)

        sizer_unmask = wx.BoxSizer(wx.HORIZONTAL)
        unmaskall = wx.Button(self.mask, wx.ID_ANY, _("Unmask all"), wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_unmask.Add(unmaskall, 1, wx.EXPAND)
        unmaskall.Bind(wx.EVT_BUTTON, self.Unmaskall)
        unmaskall.SetToolTip(_("Unmask all values in the current array"))

        unmasksel = wx.Button(self.mask, wx.ID_ANY, _("Unmask selection"), wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_unmask.Add(unmasksel, 1, wx.EXPAND)
        unmasksel.Bind(wx.EVT_BUTTON, self.Unmask_selection)
        unmasksel.SetToolTip(_("Unmask all values in the current selection \n If you wish to unmask some of the currently masked data, you have to first select the desired nodes by unchecking the 'Use mask to retrict' on the 'Selection' panel, otherwise it is impossible to select these nodes"))

        sizermask.Add(sizer_unmask, 1, wx.EXPAND)

        invertmask = wx.Button(self.mask, wx.ID_ANY, _("Invert mask"), wx.DefaultPosition, wx.DefaultSize, 0)
        sizermask.Add(invertmask, 1, wx.EXPAND)
        invertmask.Bind(wx.EVT_BUTTON, self.InvertMask)
        invertmask.SetToolTip(_("Logical operation on mask -- mask = ~mask"))

        sizer_maskunmask_poly = wx.BoxSizer(wx.HORIZONTAL)

        mask_in_poly = wx.Button(self.mask, wx.ID_ANY, _("Mask inside active vector (+NoData)"), wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_maskunmask_poly.Add(mask_in_poly, 1, wx.EXPAND)
        mask_in_poly.Bind(wx.EVT_BUTTON, self.Mask_inside_active_vector)
        mask_in_poly.SetToolTip(_("Mask all values inside the active vector and set NoData to masked values"))

        mask_out_poly = wx.Button(self.mask, wx.ID_ANY, _("Mask outside active vector (+NoData)"), wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_maskunmask_poly.Add(mask_out_poly, 1, wx.EXPAND)
        mask_out_poly.Bind(wx.EVT_BUTTON, self.Mask_outside_active_vector)
        mask_out_poly.SetToolTip(_("Mask all values outside the active vector and set NoData to masked values"))

        sizermask.Add(sizer_maskunmask_poly, 1, wx.EXPAND)

        sizer_maskunmask_poly_wonodata = wx.BoxSizer(wx.HORIZONTAL)

        mask_in_poly_nodata = wx.Button(self.mask, wx.ID_ANY, _("Mask inside active vector"), wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_maskunmask_poly_wonodata.Add(mask_in_poly_nodata, 1, wx.EXPAND)
        mask_in_poly_nodata.Bind(wx.EVT_BUTTON, self.Mask_inside_active_vector_wo_nodata)
        mask_in_poly_nodata.SetToolTip(_("Mask all values inside the active vector"))

        mask_out_poly_nodata = wx.Button(self.mask, wx.ID_ANY, _("Mask outside active vector"), wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_maskunmask_poly_wonodata.Add(mask_out_poly_nodata, 1, wx.EXPAND)
        mask_out_poly_nodata.Bind(wx.EVT_BUTTON, self.Mask_outside_active_vector_wo_nodata)
        mask_out_poly_nodata.SetToolTip(_("Mask all values outside the active vector"))

        sizermask.Add(sizer_maskunmask_poly_wonodata, 1, wx.EXPAND)

        mask_inside_polys =wx.BoxSizer(wx.HORIZONTAL)
        mask_in_polys = wx.Button(self.mask, wx.ID_ANY, _("Mask inside active zone (+NoData)"), wx.DefaultPosition, wx.DefaultSize, 0)
        mask_inside_polys.Add(mask_in_polys, 1, wx.EXPAND)
        mask_in_polys.Bind(wx.EVT_BUTTON, self.Mask_inside_active_zone)
        mask_in_polys.SetToolTip(_("Mask all values inside the active zone and set NoData to masked values"))

        mask_inside_polys_nodata = wx.Button(self.mask, wx.ID_ANY, _("Mask inside active zone"), wx.DefaultPosition, wx.DefaultSize, 0)
        mask_inside_polys.Add(mask_inside_polys_nodata, 1, wx.EXPAND)
        mask_inside_polys_nodata.Bind(wx.EVT_BUTTON, self.Mask_inside_active_zone_wo_nodata)
        mask_inside_polys_nodata.SetToolTip(_("Mask all values inside the active zone"))

        sizermask.Add(mask_inside_polys, 1, wx.EXPAND)

        self.mask.Layout()
        sizermask.Fit(self.mask)

        # Operations
        sizeropgen = wx.BoxSizer(wx.VERTICAL)
        sepopcond = wx.BoxSizer(wx.HORIZONTAL)
        sizerop = wx.BoxSizer(wx.VERTICAL)
        sizercond = wx.BoxSizer(wx.VERTICAL)
        # bSizer26 = wx.BoxSizer( wx.VERTICAL )

        # bSizer14.Add( bSizer26, 1, wx.EXPAND, 5 )
        sepopcond.Add(sizercond, 1, wx.EXPAND)
        sepopcond.Add(sizerop, 1, wx.EXPAND)
        sizeropgen.Add(sepopcond, 1, wx.EXPAND)

        operationChoices = [u"+", u"-", u"*", u"/", _("replace")]
        self.choiceop = wx.RadioBox(self.operation, wx.ID_ANY,
                                    _("Operator"), wx.DefaultPosition,
                                    wx.DefaultSize, operationChoices, 1, wx.RA_SPECIFY_COLS)
        self.choiceop.SetSelection(4)
        sizerop.Add(self.choiceop, 1, wx.EXPAND)

        self.opvalue = wx.TextCtrl(self.operation, wx.ID_ANY, u"1",
                                   wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        sizerop.Add(self.opvalue, 0, wx.EXPAND)
        self.opvalue.SetToolTip(_('Numeric value or "Null"'))

        conditionChoices = [u"<", u"<=", u"=", u">=", u">", u"isNaN"]
        self.condition = wx.RadioBox(self.operation, wx.ID_ANY, _("Condition"), wx.DefaultPosition, wx.DefaultSize,
                                     conditionChoices, 1, wx.RA_SPECIFY_COLS)
        self.condition.SetSelection(2)
        sizercond.Add(self.condition, 1, wx.EXPAND)

        self.condvalue = wx.TextCtrl(self.operation, wx.ID_ANY, u"0",
                                     wx.DefaultPosition, wx.DefaultSize, style=wx.TE_CENTER)
        sizercond.Add(self.condvalue, 0, wx.EXPAND)

        self.ApplyOp = wx.Button(self.operation, wx.ID_ANY, _("Apply math operator (Condition and Operator)"), wx.DefaultPosition,
                                 wx.DefaultSize, 0)
        sizeropgen.Add(self.ApplyOp, 1, wx.EXPAND)
        self.ApplyOp.SetToolTip(_("This action will use the condition AND the operator to manipulate the selected nodes"))

        self.SelectOp = wx.Button(self.operation, wx.ID_ANY, _("Select nodes (only Condition)"), wx.DefaultPosition,
                                  wx.DefaultSize, 0)
        self.SelectOp.SetToolTip(_("This action will use the condition AND NOT the operator to select some nodes"))
        sizeropgen.Add(self.SelectOp, 1, wx.EXPAND)

        self.nbselect2 = wx.StaticText(self.operation, wx.ID_ANY, _("nb"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.nbselect2.Wrap(-1)
        sizeropgen.Add(self.nbselect2, 0, wx.EXPAND)
        self.nbselect2.SetToolTip(_("Number of selected nodes"))

        self.operation.SetSizer(sizeropgen)
        self.operation.Layout()
        sizeropgen.Fit(self.operation)

        gensizer = wx.BoxSizer(wx.VERTICAL)
        gensizer.Add(self.array_ops, 1, wx.EXPAND | wx.ALL)

        self.SetSizer(gensizer)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.LaunchSelection.Bind(wx.EVT_BUTTON, self.OnLaunchSelect)
        self.AllSelection.Bind(wx.EVT_BUTTON, self.OnAllSelect)
        self.MoveSelection.Bind(wx.EVT_BUTTON, self.OnMoveSelect)
        self.ReselectMemory.Bind(wx.EVT_BUTTON, self.OnReselectMemory)
        self.ResetSelection.Bind(wx.EVT_BUTTON, self.OnResetSelect)
        self.ResetAllSelection.Bind(wx.EVT_BUTTON, self.OnResetAllSelect)
        self.to_clipboard_str.Bind(wx.EVT_BUTTON, self.OnToClipboardStr)
        self.to_clipboard_script.Bind(wx.EVT_BUTTON, self.OnToClipboardStr)

        self.SaveSelection.Bind(wx.EVT_BUTTON, self.OnSaveSelection)
        self.LoadSelection.Bind(wx.EVT_BUTTON, self.OnLoadSelection)

        self.m_button2.Bind(wx.EVT_BUTTON, self.OnManageVectors)
        self.loadvec.Bind(wx.EVT_BUTTON, self.OnLoadvec)
        self.saveas.Bind(wx.EVT_BUTTON, self.OnSaveasvec)
        self.save.Bind(wx.EVT_BUTTON, self.OnSavevec)
        self.ApplyOp.Bind(wx.EVT_BUTTON, self.OnApplyOpMath)
        self.ApplyTools.Bind(wx.EVT_BUTTON, self.OnApplyNullvalue)
        self.nullborder.Bind(wx.EVT_BUTTON, self.OnNullBorder)
        self.filter_zone.Bind(wx.EVT_BUTTON, self.OnFilterZone)
        self.clean.Bind(wx.EVT_BUTTON, self.OnClean)
        self.labelling.Bind(wx.EVT_BUTTON, self.OnLabelling)
        self.statistics.Bind(wx.EVT_BUTTON, self.OnStatistics)
        self.plot_stats.Bind(wx.EVT_BUTTON, self.OnPlotStatistics)
        self.plot_stats_zone.Bind(wx.EVT_BUTTON, self.OnPlotStatisticsZone)
        self.plot_stats_vector.Bind(wx.EVT_BUTTON, self.OnPlotStatisticsVector)
        self.extract_selection.Bind(wx.EVT_BUTTON, self.OnExtractSelection)
        self._contour_int.Bind(wx.EVT_BUTTON, self.OnContourInt)
        self._contour_list.Bind(wx.EVT_BUTTON, self.OnContourList)

        self.SelectOp.Bind(wx.EVT_BUTTON, self.OnApplyOpSelect)
        self.palapply.Bind(wx.EVT_BUTTON, self.Onupdatepal)
        self.palsave.Bind(wx.EVT_BUTTON, self.Onsavepal)
        self.palload.Bind(wx.EVT_BUTTON, self.Onloadpal)
        self._default_pal.Bind(wx.EVT_BUTTON, self.Onloaddefaultpal)
        self.palimage.Bind(wx.EVT_BUTTON, self.Onpalimage)
        self.paldistribute.Bind(wx.EVT_BUTTON, self.Onpaldistribute)
        self.palchoosecolor.Bind(wx.EVT_BUTTON, self.OnClickColorPal)
        self.histoupdate.Bind(wx.EVT_BUTTON, self.OnClickHistoUpdate)
        self.histoupdatezoom.Bind(wx.EVT_BUTTON, self.OnClickHistoUpdate)
        self.histoupdateerase.Bind(wx.EVT_BUTTON, self.OnClickHistoUpdate)

        self.contract_selection.Bind(wx.EVT_BUTTON, self.OnContractSelection)
        self.expand_selection.Bind(wx.EVT_BUTTON, self.OnExpandSelection)
        self.expand_unselect_interior.Bind(wx.EVT_BUTTON, self.OnExpandUnselectInterior)
        self.unselect_interior.Bind(wx.EVT_BUTTON, self.OnUnselectInterior)

        icon = wx.Icon()
        icon_path = Path(__file__).parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

    def OnBlockSelect(self, event):
        """ Select block """

        self.parentarray.active_blocks = self._list.GetSelections()

    # def OnOpenBlock(self, event):
    #     """ Open block """

    #     sel = self._list.GetSelections()

    #     if len(sel)==0:
    #         logging.info('No block selected')
    #         return
    #     elif len(sel)>1:
    #         logging.info('Only one block can be selected')
    #         return
    #     elif sel[0]==0:
    #         logging.info('All blocks selected -- Choose only one specific block')
    #         return
    #     else:
    #         keyblock = getkeyblock(sel[0], addone=False)

    #         ops = self.parentarray.myblocks[keyblock].myops

    #         if ops is not None:
    #             ops.Show()

    def interpolation2D(self, event: wx.MouseEvent):
        """ calling Interpolation 2D """

        keys = list(self.parentarray.SelectionData.selections.keys())
        keys = [k for k in keys if len(self.parentarray.SelectionData.selections[k]) >0]

        if len(keys) > 0:
            if len(keys) == 1:
                self.parentarray.interpolation2D(keys[0])
            else:
                with wx.SingleChoiceDialog(self, 'Choose the selection to interpolate', 'Selections', keys) as dlg:
                    if dlg.ShowModal() == wx.ID_OK:
                        selection = dlg.GetStringSelection()
                        self.parentarray.interpolation2D(selection)

                    dlg.Destroy()

    def Unmaskall(self, event: wx.MouseEvent):
        """
        Unmask all values in the current array
        @author Pierre Archambeau
        """

        self.parentarray.mask_reset()
        self.refresh_array()

    def Unmask_selection(self, event:wx.MouseEvent):
        """
        Enlève le masque des éléments sélectionnés
        @author Pierre Archambeau
        """

        self.parentarray.SelectionData.unmask_selection()


    def InvertMask(self, event: wx.MouseEvent):
        """ Invert mask """

        self.parentarray.mask_invert()
        self.refresh_array()

    def Mask_inside_active_vector(self, event: wx.MouseEvent):
        """ Mask inside the active vector """
        if self.active_vector is not None:
            self.parentarray.mask_insidepoly(self.active_vector,)
            self.refresh_array()

    def Mask_inside_active_vector_wo_nodata(self, event: wx.MouseEvent):
        """ Mask inside the active vector without setting NoData """
        if self.active_vector is not None:
            self.parentarray.mask_insidepoly(self.active_vector, set_nullvalue=False)
            self.refresh_array()

    def Mask_outside_active_vector(self, event: wx.MouseEvent):
        """ Mask outside the active vector """
        if self.active_vector is not None:
            self.parentarray.mask_outsidepoly(self.active_vector)
            self.refresh_array()

    def Mask_inside_active_zone(self, event: wx.MouseEvent):
        """ Mask inside the active zone """
        if self.active_zone is not None:
            self.parentarray.mask_insidepolys(self.active_zone.myvectors)
            self.refresh_array()

    def Mask_inside_active_zone_wo_nodata(self, event: wx.MouseEvent):
        """ Mask inside the active zone without setting NoData """
        if self.active_zone is not None:
            self.parentarray.mask_insidepolys(self.active_zone.myvectors, set_nullvalue=False)
            self.refresh_array()

    def Mask_outside_active_vector_wo_nodata(self, event: wx.MouseEvent):
        """ Mask outside the active vector without setting NoData """
        if self.active_vector is not None:
            self.parentarray.mask_outsidepoly(self.active_vector, set_nullvalue=False)
            self.refresh_array()

    def interp2Dpolygons(self, event: wx.MouseEvent):
        """
        Bouton d'interpolation sous tous les polygones d'une zone
        cf WolfArray.interp2Dpolygon
        """

        self.parentarray.SelectionData.interp2Dpolygons(self.active_zone)

    def interp2Dpolygon(self, event: wx.MouseEvent):
        """
        Bouton d'interpolation sous un polygone
        cf WolfArray.interp2Dpolygon
        """

        self.parentarray.SelectionData.interp2Dpolygon(self.active_vector)

    def interp2Dpolylines(self, event: wx.MouseEvent):
        """
        Bouton d'interpolation sous toutes les polylignes de la zone
        cf parent.interp2Dpolyline
        """

        self.parentarray.SelectionData.interp2Dpolylines(self.active_zone)


    def interp2Dpolyline(self, event: wx.MouseEvent):
        """
        Bouton d'interpolation sous la polyligne active
        cf parent.interp2Dpolyline
        """

        self.parentarray.SelectionData.interp2Dpolyline(self.active_vector)

    def volumesurface(self, event):
        """
        Click on evaluation of stage-storage-surface relation
        """

        self.parentarray.SelectionData.volumesurface()

    def OnAllSelect(self, event):
        """
        Select all --> just put "all" in "myselection"
        """

        self.parentarray.SelectionData.select_all()
        self.parentarray.myops.nbselect.SetLabelText('All')
        self.parentarray.myops.nbselect2.SetLabelText('All')

    def OnReselectMemory(self, event):
        """
        Reselect from memory
        """

        if self.parentarray.mngselection is not None:
            self.parentarray.mngselection.reselect_from_memory()

    def OnMoveSelect(self, event):
        """Transfert de la sélection courante dans un dictionnaire"""

        dlg = wx.TextEntryDialog(self, 'Choose id', 'id?')
        ret = dlg.ShowModal()

        if ret == wx.ID_CANCEL:
            logging.info('Cancel transfer')
            dlg.Destroy()
            return

        idtxt = dlg.GetValue()
        dlg.Destroy()

        if self.parentarray.SelectionData is not None:
            if self.parentarray.SelectionData.nb > 0:
                dlg = wx.ColourDialog(self)
                ret = dlg.ShowModal()
                if ret == wx.ID_OK:
                    color = dlg.GetColourData()
                    color = color.GetColour().Get()
                    dlg.Destroy()
                else:
                    logging.info('Cancel transfer')
                    dlg.Destroy()
                    return
            else:
                color = (20,20,20,255)

        self.parentarray.SelectionData.move_selectionto(idtxt, color)

    def OnContractSelection(self, event):
        """ Contract selection """

        nb = int(self._erode_dilate_value.GetValue())
        if self._erode_dilate_structure.GetValue() == 'Cross':
            structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        else:
            structure = np.ones((3, 3))

        self.parentarray.SelectionData.erode_selection(nb, self.usemask, structure)
        self.refresh_array()

    def OnExpandSelection(self, event):
        """ Expand selection """
        nb = int(self._erode_dilate_value.GetValue())
        if self._erode_dilate_structure.GetValue() == 'Cross':
            structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        else:
            structure = np.ones((3, 3))

        self.parentarray.SelectionData.dilate_selection(nb, self.usemask, structure)
        self.refresh_array()

    def OnExpandUnselectInterior(self, event):
        """ Expand contour """

        nb = int(self._erode_dilate_value.GetValue())
        if self._erode_dilate_structure.GetValue() == 'Cross':
            structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        else:
            structure = np.ones((3, 3))

        self.parentarray.SelectionData.dilate_contour_selection(nb, self.usemask, structure)
        self.refresh_array()

    def OnUnselectInterior(self, event):
        """ Contract contour """
        self.parentarray.SelectionData.erode_contour_selection()
        self.refresh_array()

    def reset_selection(self):
        """
        Reset of current selection
        """

        self.parentarray.SelectionData.reset()

        self.nbselect.SetLabelText('0')
        self.nbselect2.SetLabelText('0')
        self.minx.SetLabelText('0')
        self.miny.SetLabelText('0')
        self.maxx.SetLabelText('0')
        self.maxy.SetLabelText('0')

    def reset_all_selection(self):
        """
        Reset of current selection and stored ones
        """

        self.reset_selection()
        self.parentarray.SelectionData.reset_all()

    def OnResetSelect(self, event):
        """
        Click on Reset of current selection
        """

        self.reset_selection()
        self.refresh_array()

    def OnResetAllSelect(self, event):
        """
        Click on reset all
        """

        self.reset_all_selection()
        self.refresh_array()

    def OnSaveSelection(self, event):
        """
        Save the current selection
        """

        self.parentarray.SelectionData.save_selection()

    def OnLoadSelection(self, event):
        """
        Load a selection
        """

        self.parentarray.SelectionData.load_selection()

    def OnToClipboardStr(self, event):
        """
        Copy the current selection to the clipboard as a string
        """

        if event.GetId() == self.to_clipboard_str.GetId():
            whichtype = 'string'
        elif event.GetId() == self.to_clipboard_script.GetId():
            whichtype = 'script'

        if self.parentarray.mngselection is not None:

            selectobj = self.parentarray.mngselection

            if selectobj.nb > 0:
                choices = [_("Current selection")]
                for cur in selectobj.selections.items():
                    choices.append(cur[0])

                dlg = wx.MultiChoiceDialog(None, "Choose the selection to copy", "Choices", choices)
                ret = dlg.ShowModal()
                if ret == wx.ID_CANCEL:
                    dlg.Destroy()
                    return

                sel = dlg.GetSelections()
                dlg.Destroy()

            else:
                sel = [0]

            if len(sel) == 0:
                return
            elif len(sel) == 1:
                sel = int(sel[0])

                if sel == 0:
                    sel = None
                else:
                    sel =choices[sel]

                self.parentarray.mngselection.copy_to_clipboard(which = sel, typestr=whichtype)

            else:
                txt = ''
                for cursel in sel:
                    if cursel == 0:
                        cursel = None
                    else:
                        cursel = choices[cursel]

                    if whichtype == 'script':
                        txt += self.parentarray.mngselection.get_script(which = cursel)
                    else:
                        txt += self.parentarray.mngselection.get_string(which = cursel)

                    txt += '\n'

                if wx.TheClipboard.Open():
                    wx.TheClipboard.Clear()
                    wx.TheClipboard.SetData(wx.TextDataObject(txt))
                    wx.TheClipboard.Close()

        else:
            logging.error('Error in OnToClipboardStr')

    def OnApplyOpSelect(self, event):
        """ Select nodes based on condition """

        # condition operator
        curcond = self.condition.GetSelection()
        # condition value
        curcondvalue = float(self.condvalue.GetValue())

        self.parentarray.SelectionData.condition_select(curcond, curcondvalue, usemask=self.usemask)

        self.refresh_array()

    def OnApplyNullvalue(self, event:wx.MouseEvent):
        """ Apply null value to the array """

        newnull = self.txt_nullval.Value
        if newnull.lower() == 'nan':
            newnull = np.nan
        else:
            newnull = float(newnull)

        if self.parentarray.nullvalue!= newnull:

            self.parentarray.nullvalue = newnull
            self.parentarray.mask_data(newnull)
            self.refresh_array()

    def refresh_array(self):
        """ Force refresh of the parent array """

        if self.parentarray is not None:
            self.parentarray.reset_plot()

    def OnNullBorder(self, event:wx.MouseEvent):
        """ Nullify the border of the array """

        dlg = wx.SingleChoiceDialog(None, "Choose the border width [number of nodes]", "Border width", [str(i) for i in range(1, 20)])

        ret = dlg.ShowModal()
        if ret == wx.ID_CANCEL:
            dlg.Destroy()
            return

        borderwidth = int(dlg.GetStringSelection())

        self.parentarray.nullify_border(borderwidth)

    def OnFilterZone(self, event:wx.MouseEvent):
        """ Filter the array based on contiguous zones """

        self.parentarray.filter_zone()

        dlg = wx.MessageDialog(None, _('Do you want to set null value in the masked data ?'), _('Masked data'), wx.YES_NO | wx.ICON_QUESTION)
        ret = dlg.ShowModal()

        if ret == wx.ID_YES:
            self.parentarray.set_nullvalue_in_mask()

        dlg.Destroy()

    def OnClean(self, event:wx.MouseEvent):
        """ Clean the array -- Remove the isolated cells """

        dlg = wx.NumberEntryDialog(None, 'Minimum number of nodes for a patch to be kept', 'Minimum number of nodes', 'Minimum number of nodes', 10, 1, 1000)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        minnodes = dlg.GetValue()
        self.parentarray.clean_small_patches(minnodes)

        dlg.Destroy()

        dlg = wx.MessageDialog(None, _('Do you want to set null value in the masked data ?'), _('Masked data'), wx.YES_NO | wx.ICON_QUESTION)
        ret = dlg.ShowModal()

        if ret == wx.ID_YES:
            self.parentarray.set_nullvalue_in_mask()

        dlg.Destroy()

    def OnLabelling(self, event:wx.MouseEvent):
        """ Labelling of contiguous zones """

        self.parentarray.labelling()

    def OnStatistics(self, event:wx.MouseEvent):
        """ Statistics on the array """

        ret = self.parentarray.statistics()

        ret_frame = wx.Frame(None, -1, _('Statistics of {} on selected values').format(self.parentarray.idx), size = (300, 200))

        icon = wx.Icon()
        icon_path = Path(__file__).parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        ret_frame.SetIcon(icon)

        ret_panel = wx.Panel(ret_frame, -1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        # Add a cpGrid and put statistics in it
        cp = CpGrid(ret_panel, wx.ID_ANY, style=wx.WANTS_CHARS | wx.TE_CENTER)
        cp.CreateGrid(len(ret), 2)

        sizer.Add(cp, 1, wx.EXPAND)

        for i, (key,val) in enumerate(ret.items()):
            if i != len(ret)-1:
                cp.SetCellValue(i, 0, key)
                cp.SetCellValue(i, 1, str(val))

        ret_panel.SetSizer(sizer)
        ret_panel.Layout()

        ret_frame.SetSize((300, 200))
        ret_frame.Centre()

        ret_frame.Show()

    def OnPlotStatistics(self, event:wx.MouseEvent):
        """ Plot statistics on the current zoom"""

        from .analyze_poly import Array_analysis_onepolygon

        logging.info(_('Plotting statistics on the current zoom'))
        if self.parentarray.nbnotnull > 50_000:
            logging.info(_('Quite large array - please wait a bit...'))

        analyzer = Array_analysis_onepolygon(self.parentarray, self.mapviewer.get_bounds_as_polygon())

        try:
            analyzer.plot_values(engine = 'plotly')
        except:
            logging.error(_('Error in plotly engine - Try seaborn engine'))
            logging.info(_('If you have not installed plotly, please install it with "pip install plotly"'))
            try:
                analyzer.plot_values(engine = 'seaborn')
            except:
                logging.error('Error in seaborn engine')

        logging.info(_('Done !'))

    def OnPlotStatisticsZone(self, event:wx.MouseEvent):
        """ Plot statistics on the current zone """

        if self.mapviewer is not None:
            if self.mapviewer.active_zone is not None:
                from .analyze_poly import Array_analysis_polygons

                logging.info(_('Plotting statistics on the current zone'))

                analyzer = Array_analysis_polygons(self.parentarray, self.mapviewer.active_zone)
                try:
                    analyzer.plot_values(engine = 'plotly')
                except:
                    logging.error(_('Error in plotly engine - Try seaborn engine'))
                    logging.info(_('If you have not installed plotly, please install it with "pip install plotly"'))
                    try:
                        analyzer.plot_values(engine = 'seaborn')
                    except:
                        logging.error('Error in seaborn engine')

                logging.info(_('Done !'))

            else:
                logging.error(_('No active zone to plot statistics'))
                logging.info(_('Please select a zone to plot statistics'))
        else:
            logging.error(_('No active mapviewer to plot statistics'))

    def OnPlotStatisticsVector(self, event:wx.MouseEvent):
        """ Plot statistics on the current vector """

        if self.mapviewer is not None:
            if self.mapviewer.active_vector is not None:
                from .analyze_poly import Array_analysis_onepolygon

                logging.info(_('Plotting statistics on the current vector'))

                # Get the active vector
                analyzer = Array_analysis_onepolygon(self.parentarray, self.mapviewer.active_vector)
                try:
                    analyzer.plot_values(engine = 'plotly')
                except:
                    logging.error(_('Error in plotly engine - Try seaborn engine'))
                    logging.info(_('If you have not installed plotly, please install it with "pip install plotly"'))
                    try:
                        analyzer.plot_values(engine = 'seaborn')
                    except:
                        logging.error('Error in seaborn engine')

                logging.info(_('Done !'))

            else:
                logging.error(_('No active vector to plot statistics'))
                logging.info(_('Please select a vector to plot statistics'))
        else:
            logging.error(_('No active mapviewer to plot statistics'))

    def OnExtractSelection(self, event:wx.MouseEvent):
        """ Extract the current selection """

        self.parentarray.extract_selection()

    def OnContourInt(self, event:wx.MouseEvent):
        """ Create contour - number of contours """

        with wx.NumberEntryDialog(None, 'Number of contours', 'Number of contours', 'Number of contours', 20, 1, 1000) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                nbcontours = dlg.GetValue()

                logging.info(_('Baking contour'))
                cont = self.parentarray.contour(levels = nbcontours)
                logging.info(_('Add contour to viewer'))
                cont.prep_listogl()
                mapv = self.get_mapviewer()
                mapv.add_object('vector', newobj = cont, id = cont.idx)
                self.get_mapviewer().Paint()
                logging.info(_('Done !'))

    def OnContourList(self, event:wx.MouseEvent):
        """ Create contour - list of values """

        if self.parentarray is None:
            logging.error('No parent array')
            logging.info('Nothing to do ! -- Check the routine OnContourList if needed !')
            return

        with wx.TextEntryDialog(None, 'List of specific values separated by comma or tuple (min;max;step)\n\nValues in tuples must be separated by ";"',
                                'List of values', f'{self.parentarray.zmin}, {self.parentarray.zmax}') as dlg:

            if dlg.ShowModal() == wx.ID_OK:
                txt = dlg.GetValue()

                self._levels = []
                if ',' in txt:
                    for cur in txt.split(','):
                        if '(' in cur:
                            cur = cur.replace('(', '').replace(')', '')
                            cur = cur.split(';')
                            if len(cur) == 3:
                                minval = float(cur[0])
                                maxval = float(cur[1])
                                step = float(cur[2])
                                self._levels.extend(np.arange(minval, maxval, step))
                            else:
                                logging.warning('Ignoring tuple with wrong number of values - {}'.format(cur))
                        else:
                            try:
                                self._levels.append(float(cur))
                            except:
                                logging.error('Error in chain text to float - {}'.format(cur))
                elif '(' in txt:
                    cur = txt.replace('(', '').replace(')', '')
                    cur = cur.split(';')
                    if len(cur) == 3:
                        minval = float(cur[0])
                        maxval = float(cur[1])
                        step = float(cur[2])
                        self._levels.extend(np.arange(minval, maxval, step))
                    else:
                        logging.warning('Ignoring tuple with wrong number of values - {}'.format(cur))
                else:
                    try:
                        self._levels = [float(txt)]
                    except:
                        logging.error('Error in chain text to float - {}'.format(txt))
                        return

                if isinstance(self._levels, list):
                    if len(self._levels) == 0:
                        logging.error('Nothing to do !')
                        return

                logging.info(_('Baking contour'))
                cont = self.parentarray.contour(levels = self._levels)
                logging.info(_('Add contour to viewer'))
                cont.prep_listogl()
                self.get_mapviewer().add_object('vector', newobj = cont, id = cont.idx)
                self.get_mapviewer().Paint()
                logging.info(_('Done !'))

    def OnApplyOpMath(self, event:wx.MouseEvent):
        """ Apply math operator to the array """

        # operator type
        curop = self.choiceop.GetSelection()
        # condition type
        curcond = self.condition.GetSelection()

        # operator value
        opval = self.opvalue.GetValue()
        if opval.lower() == 'null' or opval.lower() == 'nan' or opval.lower() == 'nul':
            curopvalue = self.parentarray.nullvalue
        else:
            try:
                tmp_float = float(opval)
            except:
                logging.error('Error in float conversion - Do you try to set null value ? - Accepted values : "Null" or "NaN"')
                return

            curopvalue = tmp_float

        # condition value
        curcondvalue = self.condvalue.GetValue()
        if curcondvalue.lower() == 'null' or curcondvalue.lower() == 'nan' or curcondvalue.lower() == 'nul':
            curcondvalue = self.parentarray.nullvalue
        else:
            try:
                tmp_float = float(curcondvalue)
            except:
                logging.error('Error in float conversion - Do you try to set null value ? - Accepted values : "Null" or "NaN"')
                return

            curcondvalue = tmp_float

        self.parentarray.SelectionData.treat_select(curop, curcond, curopvalue, curcondvalue)

    def Onmask(self, event:wx.MouseEvent):
        """ Mask nodes based on condition """

        curop = self.choiceop.GetSelection()
        curcond = self.condition.GetSelection()

        try:
            curopvalue = float(self.opvalue.GetValue())
        except:
            logging.error('Error in float conversion - operator')
            return
        try:
            curcondvalue = float(self.condvalue.GetValue())
        except:
            logging.error('Error in float conversion - condition')
            return

        self.parentarray.SelectionData.mask_condition(curop, curcond, curopvalue, curcondvalue)
        self.refresh_array()

    def OnManageVectors(self, event:wx.MouseEvent):
        """ Open vector manager  """

        self.show_structure_OpsVectors()

    def show_structure_OpsVectors(self):
        """ Show the structure of the vector manager """

        if self.mapviewer is not None:
            if self.mapviewer.linked:
                # The viewer is linked to other viewers
                if self.mapviewer.link_shareopsvect:
                    # The viewer shares the vector manager with the other viewers
                    if self.myzones.get_mapviewer() in self.mapviewer.linkedList:
                        # The viewer is in the active linked viewers
                        self.myzones.showstructure()
                    return

        self.myzones.showstructure()

    def hide_properties(self):
        """ Hide the properties panel """

        try:
            self.myzones.hide_properties()
            self.Hide()
        except Exception as e:
            logging.error('Error in hide_properties : %s' % e)

    @property
    def is_shared(self):
        """ Check if the vector manager is shared """

        if self.mapviewer is not None:
            if self.mapviewer.linked:
                if not self.mapviewer.linkedList is None:
                    comp = None
                    for curviewer in self.mapviewer.linkedList:
                        if curviewer.compare_results is not None:
                            comp = curviewer.compare_results
                            break

                    if comp is not None:
                        elts = comp.elements
                        diff = comp.diff
                        if self.parentarray in elts or self.parentarray in diff and self.mapviewer.link_shareopsvect:
                            return True

        return False

    def _get_comp_elts_diff(self):
        """ Get the elements and the differences of the linked arrays """

        if self.mapviewer is not None:
            if self.mapviewer.linked:
                if not self.mapviewer.linkedList is None:
                    comp = None
                    for curviewer in self.mapviewer.linkedList:
                        if curviewer.compare_results is not None:
                            comp = curviewer.compare_results
                            break

                    if comp is not None:
                        return comp.elements, comp.diff

        return [], []

    def _link_zones(self):
        """ Link the same vector manager to all the linked arrays """

        if self.mapviewer is not None:
            if self.mapviewer.linked:
                if not self.mapviewer.linkedList is None:
                    comp = None
                    for curviewer in self.mapviewer.linkedList:
                        if curviewer.compare_results is not None:
                            comp = curviewer.compare_results
                            break

                    if comp is not None:
                        elts = comp.elements
                        for curelt in elts:
                            if self.parentarray is not curelt:
                                curelt.myops.myzones = self.myzones
                                curelt.myops.fnsave = self.fnsave

                        diff = comp.diff
                        for curelt in diff:
                            if self.parentarray is not curelt:
                                curelt.myops.myzones = self.myzones
                                curelt.myops.fnsave = self.fnsave

                for curviewer in self.mapviewer.linkedList:
                    curviewer.Refresh()

    def OnLoadvec(self, event:wx.MouseEvent):
        """ Load vector file """

        dlg = wx.FileDialog(None, 'Select file',
                            wildcard='Vec file (*.vec)|*.vec|Vecz file (*.vecz)|*.vecz|Dxf file (*.dxf)|*.dxf|All (*.*)|*.*', style=wx.FD_OPEN)

        ret = dlg.ShowModal()
        if ret == wx.ID_CANCEL:
            dlg.Destroy()
            return

        self.fnsave = dlg.GetPath()
        dlg.Destroy()

        self.myzones = Zones(self.fnsave, parent= self, shared= self.is_shared)

        # Link the same vector manager to all the linked arrays
        if self.mapviewer is not None:
            if self.mapviewer.linked:
                self._link_zones()
            else:
                self.mapviewer.Refresh()

    def OnSaveasvec(self, event:wx.MouseEvent):
        """ Save vector file """

        dlg = wx.FileDialog(None, 'Select file', wildcard='Vec file (*.vec)|*.vec|Vecz file (*.vecz)|*.vecz|All (*.*)|*.*', style=wx.FD_SAVE)

        ret = dlg.ShowModal()
        if ret == wx.ID_CANCEL:
            dlg.Destroy()
            return

        self.fnsave = dlg.GetPath()
        dlg.Destroy()

        self.myzones.saveas(self.fnsave)

        # Link the same vector manager to all the linked arrays
        #FIXME : only works if the active_array is the good one
        if self.mapviewer is not None:
            if self.mapviewer.linked:
                if not self.mapviewer.linkedList is None:
                    for curViewer in self.mapviewer.linkedList:
                        if curViewer.link_shareopsvect:
                            curViewer.active_array.myops.fnsave = self.fnsave

    def OnSavevec(self, event:wx.MouseEvent):
        """ Save vector file """
        if self.fnsave == '':
            return

        self.myzones.saveas(self.fnsave)

    def select_node_by_node(self):
        """
        Select nodes by individual clicks

        Set the right action in the mapviewer who will attend the clicks
        """

        if self.mapviewer is not None:
            self.mapviewer.start_action('select node by node', _('Please click on the desired nodes...'))
            self.mapviewer.active_array = self.parentarray
            self.mapviewer.set_label_selecteditem(self.parentarray.idx)

    def select_zone_inside_manager(self):
        """
        Select nodes inside the active zone (manager)
        """

        if self.active_zone is None:
            logging.warning(_('Please select an active zone !'))
            return

        for curvec in self.active_zone.myvectors:
            self._select_vector_inside_manager(curvec)

        self.refresh_array()

    def select_vector_inside_manager(self):
        """
        Select nodes inside the active vector (manager)
        """
        if self.active_vector is None:
            logging.warning(_('Please select an active vector !'))
            return

        if self.active_vector.nbvertices == 0:
            logging.warning(_('Please add points to vector or select another !'))
            return

        logging.info(_('Select nodes inside the active polygon/vector...'))

        self._select_vector_inside_manager(self.active_vector)
        self.refresh_array()

    def select_vector_outside_manager(self):
        """ Select nodes outside the active vector (manager) """
        if self.active_vector is None:
            logging.warning(_('Please activate a vector !'))
            return

        if self.active_vector.nbvertices == 0:
            logging.warning(_('Please add points to vector or select another !'))
            return

        logging.info(_('Select nodes outside the active polygon/vector...'))
        self._select_vector_outside_manager(self.active_vector)
        self.refresh_array()


    def _select_vector_inside_manager(self, vect: vector):
        """ Select nodes inside a vector or set action to add vertices to a vector by clicks"""

        if vect.nbvertices > 2:
            self.parentarray.SelectionData.select_insidepoly(vect)

        elif self.mapviewer is not None:
            if vect.nbvertices < 3:
                logging.info(_('Please add points to vector !'))

            self.mapviewer.start_action('select by vector inside', _('Please draw a polygon...'))
            self.mapviewer.active_array = self.parentarray
            self.mapviewer.set_label_selecteditem(self.parentarray.idx)
            self.Active_vector(vect)

            firstvert = wolfvertex(0., 0.)
            self.vectmp.add_vertex(firstvert)

    def _select_vector_outside_manager(self, vect: vector):
        """ Select nodes outside a vector or set action to add vertices to a vector by clicks"""

        if vect.nbvertices > 2:
            self.parentarray.SelectionData.select_outsidepoly(vect)

        elif self.mapviewer is not None:
            if vect.nbvertices < 3:
                logging.info(_('Please add points to vector !'))

            self.mapviewer.start_action('select by vector outside', _('Please draw a polygon...'))
            self.mapviewer.active_array = self.parentarray
            self.mapviewer.set_label_selecteditem(self.parentarray.idx)
            self.Active_vector(vect)

            firstvert = wolfvertex(0., 0.)
            self.vectmp.add_vertex(firstvert)

    def select_zone_under_manager(self):
        """ Select nodes along the active zone (manager) """

        if self.active_zone is None:
            logging.warning(_('Please activate a zone !'))
            return

        logging.info(_('Select nodes along the active zone - all polylines...'))

        for curvec in self.active_zone.myvectors:
            self._select_vector_under_manager(curvec)

        self.refresh_array()

    def select_vector_under_manager(self):
        """ Select nodes along the active vector (manager) """
        if self.active_vector is None:
            logging.warning(_('Please activate a vector !'))
            return

        logging.info(_('Select nodes along the active polyline/vector...'))

        self._select_vector_under_manager(self.active_vector)
        self.refresh_array()

    def _select_vector_under_manager(self, vect: vector):
        """ Select nodes along a vector or set action to add vertices to a vector by clicks """

        if vect.nbvertices > 1:
            self.parentarray.SelectionData.select_underpoly(vect)

        elif self.mapviewer is not None:
            if vect.nbvertices < 2:
                logging.info(_('Please add points to vector by clicks !'))

            self.mapviewer.start_action('select by vector along', _('Please draw a polyline...'))
            self.mapviewer.active_array = self.parentarray
            self.mapviewer.set_label_selecteditem(self.parentarray.idx)
            self.Active_vector(vect)

            firstvert = wolfvertex(0., 0.)
            self.vectmp.add_vertex(firstvert)

    def select_vector_inside_tmp(self):
        """ Select nodes inside the temporary vector """

        if self.mapviewer is not None:
            logging.info(_('Select nodes inside a temporary polygon/vector...'))
            logging.info(_('Please add points to vector by clicks !'))

            self.mapviewer.start_action('select by tmp vector inside', _('Please draw a polygon...'))
            self.vectmp.reset()
            self.Active_vector(self.vectmp)
            self.mapviewer.active_array = self.parentarray
            self.mapviewer.set_label_selecteditem(self.parentarray.idx)

            firstvert = wolfvertex(0., 0.)
            self.vectmp.add_vertex(firstvert)

    def select_vector_under_tmp(self):
        """ Select nodes along the temporary vector """
        if self.mapviewer is not None:
            logging.info(_('Select nodes along a temporary polygon/vector...'))
            logging.info(_('Please add points to vector by clicks !'))

            self.mapviewer.start_action('select by tmp vector along', _('Please draw a polyline...'))
            self.vectmp.reset()
            self.Active_vector(self.vectmp)
            self.mapviewer.active_array = self.parentarray
            self.mapviewer.set_label_selecteditem(self.parentarray.idx)

            firstvert = wolfvertex(0., 0.)
            self.vectmp.add_vertex(firstvert)

    def OnLaunchSelect(self, event:wx.MouseEvent):
        """ Action button """

        id = self.selectmethod.GetSelection()

        if id == 0:
            logging.info(_('Node selection by individual clicks'))
            logging.info(_(''))
            logging.info(_('   Clicks on the desired nodes...'))
            logging.info(_(''))
            self.select_node_by_node()
        elif id == 1:
            logging.info(_('Node selection inside active vector (manager)'))
            self.select_vector_inside_manager()
        elif id == 2:
            logging.info(_('Node selection inside active zone (manager)'))
            self.select_zone_inside_manager()
        elif id == 3:
            logging.info(_('Node selection inside temporary vector'))
            logging.info(_(''))
            logging.info(_('   Choose vector by clicks...'))
            logging.info(_(''))
            self.select_vector_inside_tmp()
        elif id == 4:
            logging.info(_('Node selection along active vector (manager)'))
            self.select_vector_under_manager()
        elif id == 5:
            logging.info(_('Node selection along active zone (manager)'))
            self.select_zone_under_manager()
        elif id == 6:
            logging.info(_('Node selection along temporary vector'))
            logging.info(_(''))
            logging.info(_('   Choose vector by clicks...'))
            logging.info(_(''))
            self.select_vector_under_tmp()
        # elif id == 7:
        #     logging.info(_('Node selection outside active vector (manager)'))
        #     self.select_vector_outside_manager()

    def onclose(self, event:wx.MouseEvent):
        """ Hide the window """

        self.Hide()

    def onshow(self, event:wx.MouseEvent):
        """ Show the window - set string with null value and update palette """
        if self.parentarray.nullvalue == np.nan:
            self.txt_nullval.Value = 'nan'
        else :
            self.txt_nullval.Value = str(self.parentarray.nullvalue)

        self.update_palette()

    def Active_vector(self, vect: vector, copyall:bool=True):
        """ Set the active vector to vect and forward to mapviewer """

        if vect is None:
            return
        self.active_vector = vect
        self.active_vector_id.SetLabelText(vect.myname)

        if vect.parentzone is not None:
            self.active_zone = vect.parentzone

        if self.mapviewer is not None and copyall:
            self.mapviewer.Active_vector(vect)

    def Active_zone(self, target_zone:zone):
        """ Set the active zone to target_zone and forward to mapviewer """
        self.active_zone = target_zone
        if self.mapviewer is not None:
            self.mapviewer.Active_zone(target_zone)

    def update_palette(self):
        """
        Update palette

        Redraw the palette with Matplotlib and fill the grid with the values and RGB components
        """
        self.Palette.add_ax()
        fig, ax = self.Palette.get_fig_ax()
        self.parentarray.mypal.plot(fig, ax)
        fig.canvas.draw()
        self.parentarray.mypal.fillgrid(self.palgrid)

    def Onsavepal(self, event:wx.MouseEvent):
        """ Save palette to file """

        myarray: WolfArray
        myarray = self.parentarray
        myarray.mypal.savefile()

    def Onloadpal(self, event:wx.MouseEvent):
        """ Load palette from file """

        myarray: WolfArray
        myarray = self.parentarray
        myarray.mypal.readfile()

        myarray.mypal.automatic = False
        self.palauto.SetValue(0)

        self.refresh_array()

    def Onloaddefaultpal(self, event:wx.MouseEvent):
        """ Load default palette """

        import glob

        # list of all .pal file in model directory

        dirpal = os.path.join(os.path.dirname(__file__), 'models')

        listpal = glob.glob(dirpal + '/*.pal')

        if len(listpal) == 0:
            logging.info('No default palette found')
            return

        listpal = [os.path.basename(i) for i in listpal]

        dlg = wx.SingleChoiceDialog(None, 'Choose the default palette', 'Default palette', listpal)
        ret = dlg.ShowModal()

        if ret == wx.ID_CANCEL:
            dlg.Destroy()

        self.parentarray.mypal.readfile(dirpal + '/' + dlg.GetStringSelection())

        self.parentarray.mypal.automatic = False
        self.palauto.SetValue(0)

        self.refresh_array()

    def Onpalimage(self, event:wx.MouseEvent):
        """ Create image from palette """
        myarray: WolfArray
        myarray = self.parentarray
        myarray.mypal.export_image()

    def Onpaldistribute(self, event:wx.MouseEvent):
        """ Evenly spaced values in palette """

        myarray: WolfArray
        myarray = self.parentarray
        myarray.mypal.distribute_values()

        myarray.mypal.automatic = False
        self.palauto.SetValue(0)

        self.refresh_array()

    def Onupdatepal(self, event:wx.MouseEvent):
        """ Apply options to palette """
        curarray: WolfArray
        curarray = self.parentarray

        dellists = False
        auto = self.palauto.IsChecked()
        uni  = self.uniforminparts.IsChecked()

        oldalpha = curarray.alpha
        if self.palalpha.IsChecked():
            curarray.alpha=1.
        else:
            curarray.alpha = float(self.palalphaslider.GetValue()) / 100.

        ret = curarray.mypal.updatefromgrid(self.palgrid)
        if curarray.mypal.automatic != auto or curarray.alpha != oldalpha or ret or auto != curarray.mypal.automatic or uni != curarray.mypal.interval_cst:
            curarray.mypal.automatic = auto
            curarray.mypal.interval_cst = uni
            curarray.updatepalette(0)
            dellists = True

        shadehill = self.palshader.IsChecked()
        if not curarray.shading and shadehill:
            curarray.shading = True
            dellists = True

        if shadehill:
            azim = float(self.palazimuthhillshade.GetValue())
            alti = float(self.palaltitudehillshade.GetValue())

            if curarray.azimuthhill != azim:
                curarray.azimuthhill = azim
                curarray.shading = True

            if curarray.altitudehill != alti:
                curarray.altitudehill = alti
                curarray.shading = True

            alpha = float(self.palalphahillshade.GetValue()) / 100.

            if curarray.shaded is None:
                logging.error('No shaded array')
            else:
                if curarray.shaded.alpha != alpha:
                    curarray.shaded.alpha = alpha
                    curarray.shading = True

        if dellists:
            self.refresh_array()

    def OnClickHistoUpdate(self, event: wx.Event):
        """ Create a histogram of the current array """

        itemlabel = event.GetEventObject().GetLabel()
        fig, ax = self.histo.get_fig_ax()

        if itemlabel == self.histoupdateerase.LabelText:
            ax.clear()
            fig.canvas.draw()
            return

        myarray: WolfArray
        myarray = self.parentarray

        onzoom = []
        if itemlabel == self.histoupdatezoom.LabelText:
            if self.mapviewer is not None:
                onzoom = [self.mapviewer.xmin, self.mapviewer.xmax, self.mapviewer.ymin, self.mapviewer.ymax]

        partarray = myarray.get_working_array(onzoom).flatten(order='F')  # .sort(axis=-1)

        ax: Axis
        ax.hist(partarray, 200, density=True)

        fig.canvas.draw()

    def OnClickColorPal(self, event: wx.Event):
        """ Edit color of a palette item """

        gridto = self.palgrid
        k = gridto.GetGridCursorRow()
        r = int(gridto.GetCellValue(k, 1))
        g = int(gridto.GetCellValue(k, 2))
        b = int(gridto.GetCellValue(k, 3))

        curcol = wx.ColourData()
        curcol.SetChooseFull(True)
        curcol.SetColour(wx.Colour(r, g, b))

        dlg = wx.ColourDialog(None, curcol)
        ret = dlg.ShowModal()

        if ret == wx.ID_CANCEL:
            dlg.Destroy()
            return

        curcol = dlg.GetColourData()
        rgb = curcol.GetColour()


        # k = gridto.GetGridCursorRow()
        gridto.SetCellValue(k, 1, str(rgb.red))
        gridto.SetCellValue(k, 2, str(rgb.green))
        gridto.SetCellValue(k, 3, str(rgb.blue))
        dlg.Destroy()


ALL_SELECTED = 'all'

class StorageMode(Enum):
    """ Storage mode for selections in WolfArray """
    LIST = 0
    ARRAY = 1

class SelectionData():
    """
    User-selected data in a WolfArray

    Contains two storage elements :
        - myselection
        - selections( dict): Stored selection(s) to be used, for example, in a spatial interpolation operation.
                             These selections are only lost in the event of a general reset.

    The selected nodes are stored using their "world" spatial coordinates so that they can be easily transferred to other objects.

    The "myselection" can be stored in two modes :
        - LIST: 'all' or list of (x, y) coordinates or tuple of ('all', np.ndarray) for all nodes and excluded nodes
        - ARRAY: np.ndarray of selected nodes (boolean array) with shape (nbx, nby) where nbx and nby are the number of nodes in the x and y directions respectively.
        The boolean array is True if the node is selected, False if not selected.

    The selection can be converted from one mode to another automatically based on the number of nodes in the array.
    If the number of nodes exceeds a threshold (default is 100,000), the selection is stored as an ARRAY.
    Otherwise, it is stored as a LIST.

    The selection can be forced to a specific storage mode using the `force_storage_mode` method.
    """

    # 'all' or list of (x, y) coordinates or a tuple of ('all', np.ndarray) for all nodes and excluded nodes
    _myselection:list[tuple[float, float]] | str | tuple[str, np.ndarray]

    selections: dict[str:dict['select':list[tuple[float, float]], 'idgllist':int, 'color':list[float]]]

    def __init__(self, parent:"WolfArray", threshold_array_mode:int = 100_000) -> None:
        """ Initialize the SelectionData object.

        :param parent: The parent WolfArray object to which this selection data belongs.
        :param threshold_array_mode: The threshold number of nodes to switch from LIST to ARRAY storage mode.
        """

        self.parent: WolfArray
        self.parent = parent

        self.wx_exists = wx.GetApp() is not None

        self._myselection = []
        self.selections = {}

        self._boolarray: np.ndarray | None = None # boolean array for selection - True if selected, False if not selected

        self._storage_mode = StorageMode.LIST # 0: 'all' or list of (x, y) coordinates or tuple of ('all', np.ndarray) for all nodes and excluded nodes, 1 for np.ndarray of selected nodes

        self.update_plot_selection = False # force to update OpenGL list if True
        self.hideselection = False
        self.numlist_select = 0 # OpenGL list index
        self.threshold_array_mode = threshold_array_mode # Default threshold for switching storage mode

    def _auto_storage_mode(self):
        """ Choose the storage mode based on the number of nodes in the array """

        if self.nb > self.threshold_array_mode:
            _storage_mode = StorageMode.ARRAY
        else:
            _storage_mode = StorageMode.LIST

        if self._storage_mode != _storage_mode:
            self._convert_to_storage_mode(_storage_mode)

    def _convert_to_storage_mode(self, new_mode:StorageMode):
        """ Convert the selection to the new storage mode.

        :param new_mode: The new storage mode to convert to (StorageMode.LIST or StorageMode.ARRAY).
        """

        logging.info('Switching storage mode to {}'.format(new_mode))

        if self._storage_mode == StorageMode.LIST:
            # Convert from 'all' or list of (x, y) coordinates or tuple of ('all', np.ndarray) to np.ndarray
            _bool_array = self._myselection_as_array

            if self._myselection == ALL_SELECTED:
                _bool_array[:,:] = True

            elif isinstance(self._myselection, list):

                if len(self._myselection) == 0:
                    _bool_array[:,:] = False
                else:
                    _bool_array[:,:] = False
                    xy = np.asarray(self._myselection)
                    ij = self.parent.xy2ij_np(xy)
                    _bool_array[ij[:, 0], ij[:, 1]] = True

            elif isinstance(self._myselection, tuple) and len(self._myselection) == 2 and self._myselection[0] == ALL_SELECTED:
                _bool_array[:,:] = True
                _excluded_nodes = self._myselection[1]

                if _excluded_nodes.size > 0:
                    _excluded_nodes = self.parent.xy2ij_np(_excluded_nodes)
                    _bool_array[_excluded_nodes[:, 0], _excluded_nodes[:, 1]] = False

            self._myselection = []

        elif self._storage_mode == StorageMode.ARRAY:

            if self.is_all_selected():
                self._myselection = ALL_SELECTED
            else:
                nb = self.nb
                if nb == 0:
                    self._myselection = []
                elif nb / max(self.parent.nbnotnull, 1) > 0.5:
                    ij_not_selected = np.argwhere(~self._myselection_as_array)
                    xy_not_selected = self.parent.ij2xy_np(ij_not_selected)
                    self._myselection = (ALL_SELECTED, xy_not_selected)
                else:
                    ij_selected = np.argwhere(self._myselection_as_array)
                    xy_selected = self.parent.ij2xy_np(ij_selected)
                    self._myselection = list(map(tuple, xy_selected))

        self._storage_mode = new_mode

    def force_storage_mode(self, new_mode:StorageMode):
        """ Force the storage mode to the new mode.

        :param new_mode: The new storage mode to force (StorageMode.LIST or StorageMode.ARRAY).
        """

        if new_mode not in StorageMode:
            logging.error('Invalid storage mode - must be LIST or ARRAY')
            return
        if self._storage_mode != new_mode:
            self._convert_to_storage_mode(new_mode)

    @property
    def myselection(self) -> list[tuple[float, float]] | str:
        """ Current selection of nodes.

        Returns:
            - 'all' if all nodes are selected
            - list of (x, y) coordinates if specific nodes are selected
        """

        if self._storage_mode == StorageMode.LIST:
            if self._myselection == ALL_SELECTED:
                return ALL_SELECTED
            elif isinstance(self._myselection, list):
                return self._myselection
            elif isinstance(self._myselection, tuple) and len(self._myselection) == 2 and self._myselection[0] == ALL_SELECTED:

                excluded_nodes = self._myselection[1]
                if excluded_nodes.shape[0] == 0:
                    return ALL_SELECTED
                else:
                    if self.parent.usemask:
                        # Return all nodes except the excluded ones
                        loc_mask = ~ self.parent.array.mask.copy()
                    else:
                        loc_mask = np.ones((self.parent.nbx, self.parent.nby), dtype=bool)

                    ij_excluded = self.parent.xy2ij_np(excluded_nodes)
                    loc_mask[ij_excluded[:, 0], ij_excluded[:, 1]] = False
                    ij = np.argwhere(loc_mask)
                    xy = self.parent.ij2xy_np(ij)
                    return list(map(tuple, xy))  # Convert to list of tuples

        elif self._storage_mode == StorageMode.ARRAY:
            if self.is_all_selected():
                return ALL_SELECTED
            else:
                nbsel = np.count_nonzero(self._myselection_as_array)
                if nbsel == 0:
                    return []
                else:
                    # Convert boolean array to list of (x, y) coordinates
                    ij_selected = np.argwhere(self._myselection_as_array)
                    xy_selected = self.parent.ij2xy_np(ij_selected)
                    return list(map(tuple, xy_selected))

        else:
            logging.error('Invalid storage mode - must be LIST or ARRAY')
            return []

    @property
    def _myselection_as_array(self) -> np.ndarray:
        """ Current selection of nodes as a numpy array.

        Returns:
            - np.ndarray of shape (nbx, nby) where nbx and nby are the number of nodes in the x and y directions respectively.
            - True if the node is selected, False if not selected.
        """

        if self._storage_mode == StorageMode.LIST:

            if self._boolarray is not None:
                return self._boolarray

            self._boolarray = np.zeros((self.parent.nbx, self.parent.nby), dtype=bool)

            if self._myselection == ALL_SELECTED:
                if self.parent.usemask:
                    self._boolarray[:,:] = ~self.parent.array.mask[:,:]
                else:
                    self._boolarray[:,:] = True

            elif isinstance(self._myselection, list):
                # Convert list of (x, y) coordinates to boolean array
                if len(self._myselection) > 0:
                    xy= np.asarray(self._myselection)
                    ij = self.parent.xy2ij_np(xy)
                    self._boolarray[ij[:, 0], ij[:, 1]] = True

            elif isinstance(self._myselection, tuple) and len(self._myselection) == 2 and self._myselection[0] == ALL_SELECTED:

                # tuple of ('all', np.ndarray) for all nodes and excluded nodes
                if self.parent.usemask:
                    self._boolarray[:,:] = ~self.parent.array.mask[:,:]
                else:
                    self._boolarray[:,:] = True

                # Exclude nodes from the second element of the tuple
                excluded_nodes = self.myselection[1]
                if excluded_nodes.size > 0:
                    excluded_ij = self.parent.xy2ij_np(excluded_nodes)
                    self._boolarray[excluded_ij[:, 0], excluded_ij[:, 1]] = False

        elif self._storage_mode == StorageMode.ARRAY:

            if self._boolarray is None:
                self._boolarray = np.zeros((self.parent.nbx, self.parent.nby), dtype=bool)

        return self._boolarray

    @_myselection_as_array.setter
    def _myselection_as_array(self, value: np.ndarray):
        """ Set the current selection of nodes as a numpy array.

        :param value: numpy array of shape (nbx, nby) where nbx and nby are the number of nodes in the x and y directions respectively.
        True if the node is selected, False if not selected.
        """

        if not isinstance(value, np.ndarray):
            logging.error('Invalid value for myselection_as_array - must be a numpy array')
        if value.shape != (self.parent.nbx, self.parent.nby):
            logging.error('Invalid shape for myselection_as_array - must be ({}, {})'.format
                          (self.parent.nbx, self.parent.nby))

        if self._boolarray is None:
            self._boolarray = value.copy()
        else:
            self._boolarray[:,:] = value[:,:]

    @property
    def myselection_npargwhere(self) -> np.ndarray:
        """ Current selection of nodes as a numpy array using np.argwhere """
        return np.argwhere(self._myselection_as_array)

    @myselection.setter
    def myselection(self, value: list[tuple[float, float]] | str | tuple[str, np.ndarray]):
        """ Set the current selection of nodes.

        :param value: 'all' to select all nodes, a list of (x, y) coordinates to select specific nodes,
                       or a tuple of ('all', np.ndarray) for all nodes and excluded nodes.
        """

        if self._storage_mode == StorageMode.ARRAY:
            # Convert to the new storage mode if necessary
            if isinstance(value, list):
                if len(value) == 0:
                    self._myselection_as_array[:,:] = False
                else:
                    ij = self.parent.xy2ij_np(np.array(value))
                    self._myselection_as_array[:,:] = False
                    self._myselection_as_array[ij[:, 0], ij[:, 1]] = True

            elif isinstance(value, str):

                if value == ALL_SELECTED:
                    if self.parent.usemask:
                        self._myselection_as_array[:,:] = ~self.parent.array.mask[:,:]
                    else:
                        self._myselection_as_array[:,:] = True
                else:
                    logging.error('Invalid selection value - must be "all" or a list of (x, y) coordinates')

            elif isinstance(value, tuple) and len(value) == 2 and value[0] == ALL_SELECTED:
                # tuple of ('all', np.ndarray) for all nodes and excluded nodes
                if self.parent.usemask:
                    self._myselection_as_array[:,:] = ~self.parent.array.mask[:,:]
                else:
                    self._myselection_as_array[:,:] = True

                excluded_nodes = value[1]
                if excluded_nodes.size > 0:
                    ij_excluded = self.parent.xy2ij_np(excluded_nodes)
                    self._myselection_as_array[ij_excluded[:, 0], ij_excluded[:, 1]] = False

            else:
                logging.error('Invalid selection value - must be "all" or a list of (x, y) coordinates or a tuple of ("all", np.ndarray)')

        elif self._storage_mode == StorageMode.LIST:

            if isinstance(value, list):
                if len(value) == 0:
                    self._myselection = []
                else:
                    self._myselection = value

            elif isinstance(value, str):
                if value == ALL_SELECTED:
                    self._myselection = ALL_SELECTED
                else:
                    logging.error('Invalid selection value - must be "all" or a list of (x, y) coordinates')

            elif isinstance(value, tuple) and len(value) == 2 and value[0] == ALL_SELECTED:
                # tuple of ('all', np.ndarray) for all nodes and excluded nodes
                self._myselection = value

            else:
                logging.error('Invalid selection value - must be "all" or a list of (x, y) coordinates or a tuple of ("all", np.ndarray)')

        self.update_nb_nodes_selection()

    def is_all_selected(self) -> bool:
        """ Check if all nodes are selected.

        :return: True if all nodes are selected, False otherwise
        """

        if self._storage_mode == StorageMode.LIST:

            if self.myselection == ALL_SELECTED:
                return True
            elif isinstance(self.myselection, list):
                if self.parent.usemask:
                    return len(self.myselection) == self.parent.nbnotnull
                else :
                    return len(self.myselection) == self.parent.nbx * self.parent.nby
            elif isinstance(self.myselection, tuple) and len(self.myselection) == 2 and self.myselection[0] == ALL_SELECTED:
                # tuple of ('all', np.ndarray) for all nodes and excluded nodes
                if self.myselection[1].size == 0:
                    return True
            return False

        elif self._storage_mode == StorageMode.ARRAY:
            if self.nb > 0:
                # Check if all nodes are selected in the boolean array
                if self.parent.usemask:
                    return np.all(self._myselection_as_array)
                else:
                    return np.all(self._myselection_as_array == ~self.parent.array.mask)
            else:
                return False

    def set_selection_from_list_xy(self, xylist: list[tuple[float, float]]):
        """ Set the current selection from a list of (x, y) coordinates.

        Alias for myselection setter to set a list of (x, y) coordinates.
        This will convert the list to the appropriate storage mode if necessary.
        """

        self.myselection = xylist

    @property
    def dx(self) -> float:
        """ Resolution in x """

        if self.parent is None:
            return 0.
        else:
            return self.parent.dx

    @property
    def dy(self) -> float:
        """ Resolution in y """

        if self.parent is None:
            return 0.
        else:
            return self.parent.dy

    @property
    def nb(self) -> int:
        """ Number of selected nodes. """

        if self._storage_mode == StorageMode.LIST:

            if self._myselection == ALL_SELECTED:
                if self.parent.usemask:
                    return self.parent.nbnotnull
                else:
                    return self.parent.nbx * self.parent.nby

            elif isinstance(self._myselection, tuple) and len(self._myselection) == 2 and self._myselection[0] == ALL_SELECTED:
                # tuple of ('all', np.ndarray) for all nodes and excluded nodes
                if self.parent.usemask:
                    return self.parent.nbnotnull - self._myselection[1].shape[0]
                else:
                    return self.parent.nbx * self.parent.nby - self._myselection[1].shape[0]
            else:
                return len(self._myselection)

        elif self._storage_mode == StorageMode.ARRAY:

            return np.count_nonzero(self._myselection_as_array)

    def unmask_selection(self, resetplot:bool=True):
        """ Unmask selection """

        if self.nb == 0:
            return

        self.parent.array.mask[self.myselection_npargwhere] = False

        if resetplot:
            self.parent.reset_plot()

    def reset(self):
        """ Reset the selection """

        self.myselection = []
        self._boolarray = None  # Reset the boolean array
        self._storage_mode = StorageMode.LIST  # Reset the storage mode to LIST

    def reset_all(self):
        """ Reset the selection """

        self.reset()
        self.selections = {}

    def get_string(self, which:str = None, all_memories:bool= False) -> str:
        """ Get string of the current selection or of a stored one.

        :param which: id/key of the selection to get the string for. If None, get the current selection.
        :param all_memories: If True, include all stored selections in the output string.
        :return: String representation of the selection.
        """

        if which is None:
            curlist = self.myselection
            txt = 'X\tY\n'
        else:
            if str(which) in self.selections:
                all_memories = False
                curlist = self.selections[str(which)]['select']
                txt = 'Selection {}\n'.format(which)
                txt += 'Color : {}\n'.format(self.selections[str(which)]['color'])
                txt += 'X\tY\n'
            else:
                logging.error(_('Selection {} does not exist').format(which))
                return ''

        if len(curlist) == 0:
            return ''

        if curlist == ALL_SELECTED:
            txt += 'all\n'
            return txt

        for cur in curlist:
            txt += str(cur[0]) + '\t' + str(cur[1]) + '\n'

        txt += 'i\tj\t1-based indices\n'
        for cur in curlist:
            i,j = self.parent.get_ij_from_xy(cur[0], cur[1], aswolf=True)
            txt += str(i) + '\t' + str(j) + '\n'

        if all_memories:
            for key, cur in self.selections.items():
                txt += self.get_string(key)

        return txt

    def get_script(self, which:int = None) -> str:
        """ Get script of the current selection or of a stored one.

        :param which: id/key of the selection to get the script for. If None, get the current selection.
        :return: Script representation of the selection.
        """

        if self.myselection == ALL_SELECTED:
            logging.error(_('Cannot create script for "all" selection'))
            return ''

        txt = '# script adapted to a WolfGPU script\n'
        txt += '#  - (i,j) are 1-based for add_boundary_condition -- Do not forget to adapt BC type, value and direction or use BC Manager\n'
        txt += '#  - (i,j) are 0-based for infiltration zones\n\n'

        if which is None:
            curlist = self.myselection
            idx = 0
        else:
            if str(which) in self.selections:
                txt += '# Selection {}\n'.format(which)
                curlist = self.selections[str(which)]['select']
                idx = which
            else:
                logging.error(_('Selection {} does not exist').format(which))
                return ''

        if len(curlist) == 0:
            return ''

        txt += '# For boundary conditions :\n'
        for cur in curlist:
            i,j = self.parent.get_ij_from_xy(cur[0], cur[1], aswolf=True)
            txt += "simul.add_boundary_condition(i={}, j={}, bc_type=BoundaryConditionsTypes.FROUDE_NORMAL, bc_value=.3, border=Direction.LEFT)".format(i, j) + '\n'

        txt += '\n\n# For infiltration zones :\n'
        for cur in curlist:
            i,j = self.parent.get_ij_from_xy(cur[0], cur[1], aswolf=True)
            txt += "infiltration_zones.array[{},{}]={}".format(i-1, j-1, idx) + '\n'

        txt += '\n\n"""If needed, selection as string :\n'
        txt += self.get_string(which)
        txt += '"""\n'

        return txt

    def copy_to_clipboard(self, which:int = None, typestr:Literal['string', 'script'] = 'string'):
        """ Copy current selection to clipboard.

        -- ONLY WORKS WITH wxPython --

        :param which: id/key of the selection to copy. If None, copy the current selection.
        :param typestr: Type of data to copy to clipboard - 'string' for string representation, 'script' for script representation.
        """

        if self.wx_exists:
            if wx.TheClipboard.Open():
                wx.TheClipboard.Clear()
                if typestr == 'string':
                    wx.TheClipboard.SetData(wx.TextDataObject(self.get_string(which)))
                else:
                    wx.TheClipboard.SetData(wx.TextDataObject(self.get_script(which)))

                wx.TheClipboard.Close()
            else:
                logging.warning(_('Cannot open the clipboard'))
        else:
            logging.warning(_('Clipboard is not available in this environment'))

    def reselect_from_memory(self, idx:list[str] = None):
        """
        Reselect a stored selection

        :param idx: id/key of the selection to reselect. If None, show a dialog to choose from available selections.
        """

        if idx is None:
            if not self.wx_exists:
                logging.error(_('Cannot reselect from memory - no wxPython available'))
                logging.error(_('Please use the method reselect_from_memory with a list of keys'))
                return

            keys = list(self.selections.keys())

            keys = [cur for cur in keys if len(self.selections[cur]['select']) > 0]

            with wx.MultiChoiceDialog(None, "Choose the memory to reselect", "Choices", keys+['All']) as dlg:
                ret = dlg.ShowModal()
                if ret == wx.ID_CANCEL:
                    return

                idx = dlg.GetSelections()
                if len(idx) == 0:
                    return

                if len(idx) == 1 and idx[0] == len(keys):
                    idx = keys
                elif len(idx) in idx:
                    idx = keys
                else:
                    idx = [keys[i] for i in idx]

        for curidx in idx:
            if curidx in self.selections:
                self.add_nodes_to_selection(self.selections[curidx]['select'])
                # self.myselection += self.selections[curidx]['select']
            else:
                logging.error(_('Selection {} does not exist').format(idx))

            # self.update_nb_nodes_selection()
            self.parent.reset_plot()

    def move_selectionto(self, idx:str, color:list[float], resetplot:bool=True):
        """
        Transfer current selection to dictionary

        :param idx: id/key of the selection
        :param color: color of the selection - list of 4 integers between 0 and 255
        :param resetplot: if True, reset the plot after moving the selection
        """

        assert len(color) == 4, "color must be a list of 4 integers between 0 and 255"

        # force idx to be a string
        idtxt = str(idx)
        self.selections[idtxt] = {}
        curdict = self.selections[idtxt]

        curdict['select'] = self.myselection
        curdict['idgllist'] = 0 # will be created later - index of OpenGL list
        curdict['color'] = color

        self.myselection = []   # reset current selection
        # self.update_nb_nodes_selection()

        if resetplot:
            self.parent.reset_plot()

    def plot_selection(self):
        """ Plot current selection and stored selections """

        # Make a copy of the current value of the flag because it will be modified in the function _plot_selection
        # So, if we want to update the plot, we need to apply the flag on each selection (current ans stored)
        update_select = self.update_plot_selection

        if len(self.selections) > 0:
            # plot stored selections
            for cur in self.selections.values():
                if cur['select'] != ALL_SELECTED:
                    self.update_plot_selection = update_select
                    col = cur['color']
                    cur['idgllist'] = self._plot_selection(cur['select'],
                                                           (float(col[0]) / 255., float(col[1]) / 255.,
                                                            float(col[2]) / 255.),
                                                           cur['idgllist'])


        if self._myselection != ALL_SELECTED and not isinstance(self._myselection, tuple):
            # plot current selection in RED if not 'all'
            if self.nb > 0:
                self.update_plot_selection = update_select
                self.numlist_select = self._plot_selection(self.myselection,
                                                           (1., 0., 0.),
                                                           self.numlist_select)

    def _plot_selection(self, curlist:list[float], color:list[float], loclist:int=0):
        """
        Plot a selection

        :param curlist: list of selected nodes -- list of tuples (x,y)
        :param color: color of the selection - list of 3 floats between 0 and 1
        :param loclist: index of OpenGL list
        """

        #FIXME : Is it a good idea to use SHADER rather than list ?
        if self.update_plot_selection:

            dx = self.dx
            dy = self.dy

            if loclist != 0:
                glDeleteLists(loclist, 1)

            loclist = glGenLists(1)
            glNewList(loclist, GL_COMPILE)

            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glBegin(GL_QUADS)
            for cursel in curlist:
                x1 = cursel[0] - dx / 2.
                x2 = cursel[0] + dx / 2.
                y1 = cursel[1] - dy / 2.
                y2 = cursel[1] + dy / 2.
                glColor3f(color[0], color[1], color[2])
                glVertex2f(x1, y1)
                glVertex2f(x2, y1)
                glVertex2f(x2, y2)
                glVertex2f(x1, y2)
            glEnd()

            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            for cursel in curlist:
                glBegin(GL_LINE_STRIP)
                x1 = cursel[0] - dx / 2.
                x2 = cursel[0] + dx / 2.
                y1 = cursel[1] - dy / 2.
                y2 = cursel[1] + dy / 2.
                glColor3f(0., 1., 0.)
                glVertex2f(x1, y1)
                glVertex2f(x2, y1)
                glVertex2f(x2, y2)
                glVertex2f(x1, y2)
                glVertex2f(x1, y1)
                glEnd()

            glEndList()
            glCallList(loclist)
            self.update_plot_selection = False
        else:
            if loclist != 0:
                glCallList(loclist)

        return loclist

    def add_node_to_selection(self, x:float, y:float, verif:bool=True):
        """
        Add one coordinate to the selection

        :param x: x coordinate - float
        :param y: y coordinate - float
        :param verif: if True, the coordinates are checked to avoid duplicates
        """

        # on repasse par les i,j car les coordonnées transférées peuvent venir d'un click souris
        # le but est de ne conserver que les coordonnées des CG de mailles
        i, j = self.parent.get_ij_from_xy(x, y)

        if self.parent.check_bounds_ij(i, j):
        # if i>=0 and j>=0 and i<self.parent.nbx and j<self.parent.nby:
            self._add_node_to_selectionij(i, j, verif)
            return 0 # useful for MB
        else:
            return -1 # useful for MB

        self.update_nb_nodes_selection()

    def add_nodes_to_selection(self, xy:list[float] | np.ndarray, verif:bool=True):
        """
        Add multiple coordinates to the selection.

        :param xy: list of coordinates or numpy array of shape (nb_nodes, 2) where nb_nodes is the number of nodes
                   or a numpy array of shape (nbx, nby) where nbx and nby are the number of nodes in the x and y directions respectively.
                   If a numpy array of shape (nbx, nby) is provided, it is assumed to be a boolean array where True indicates a selected node.
        :param verif: if True, the coordinates are checked to avoid duplicates
        """

        # on repasse par les i,j car les coordonnées transférées peuvent venir d'un click souris
        # le but est de ne conserver que les coordonnées des CG de mailles
        if isinstance(xy, np.ndarray):
            self._add_nodes_to_selection_np(xy, verif)
        else:
            ij = [self.parent.get_ij_from_xy(x, y) for x, y in xy]
            self._add_nodes_to_selectionij(ij, verif)

    def _add_node_to_selectionij(self, i:int, j:int, verif=True):
        """
        Add one ij coordinate to the selection.

        :param i: i coordinate
        :param j: j coordinate
        :param verif: if True, the coordinates are checked to avoid duplicates
        """

        if self._storage_mode == StorageMode.ARRAY:

            if verif:
                self._boolarray[i, j] = not self._boolarray[i, j]
            else:
                self._boolarray[i, j] = True

        elif self._storage_mode == StorageMode.LIST:
            x1, y1 = self.parent.get_xy_from_ij(i, j)

            if self._myselection == ALL_SELECTED:
                # If all nodes are selected, we need to exclude the current node
                self._myselection = (ALL_SELECTED, np.array([[x1, y1]]))  # Exclude the current node
            elif isinstance(self._myselection, tuple) and len(self._myselection) == 2 and self._myselection[0] == ALL_SELECTED:
                # check is the current node is in the excluded nodes
                excluded_nodes = self._myselection[1].tolist()
                if (x1, y1) in excluded_nodes:
                    # If the current node is in the excluded nodes, we remove it from the excluded nodes
                    ret = excluded_nodes.index((x1, y1))
                    excluded_nodes.pop(ret)
                    if len(excluded_nodes) == 0:
                        self._myselection = ALL_SELECTED  # All nodes are selected again
                    else:
                        self._myselection = (ALL_SELECTED, np.array(excluded_nodes))
                else:
                    # The node is included in the selection, we add it to the excluded nodes
                    excluded_nodes.append((x1, y1))
                    self._myselection = (ALL_SELECTED, np.array(excluded_nodes))
            else:
                if verif:
                    try:
                        ret = self._myselection.index((x1, y1))
                    except:
                        ret = -1
                    if ret >= 0:
                        self._myselection.pop(ret)

                        return 0
                    else:
                        self._myselection.append((x1, y1))
                        return 0
                else:
                    self._myselection.append((x1, y1))
                    return 0

    def _add_nodes_to_selectionij(self, ij:list[tuple[float, float]], verif:bool=True):
        """
        Add multiple ij coordinates to the selection

        :param ij: list of ij coordinates
        :param verif: if True, the coordinates are checked to avoid duplicates
        """

        if len(ij)==0:
            logging.info(_('Nothing to do in add_nodes_to_selectionij !'))
            return

        nbini = self.nb

        ij = np.asarray(ij)

        if self._storage_mode == StorageMode.ARRAY:
            if verif:
                self._boolarray[ij[:, 0], ij[:, 1]] = np.logical_xor(self._boolarray[ij[:, 0], ij[:, 1]], True)
            else:
                self._boolarray[ij[:, 0], ij[:, 1]] = True

        elif self._storage_mode == StorageMode.LIST:

            xy = self.parent.ij2xy_np(ij)

            if self._myselection == ALL_SELECTED:
                # If all nodes are selected, we need to exclude the current nodes
                self._myselection = (ALL_SELECTED, xy)  # Exclude the current nodes

            elif isinstance(self._myselection, tuple) and len(self._myselection) == 2 and self._myselection[0] == ALL_SELECTED:
                # check if the current nodes are in the excluded nodes
                excluded_nodes = self._myselection[1]
                # extend the excluded nodes with the new ones
                excluded_nodes = np.vstack((excluded_nodes, xy))

                # Find the duplicates in the excluded nodes
                selunique, counts = np.unique(excluded_nodes, return_counts=True, axis=0)
                # les éléments énumérés plus d'une fois doivent être enlevés
                locsort = sorted(zip(counts.tolist(), selunique.tolist()), reverse=True)
                counts = [x[0] for x in locsort]
                sel = [tuple(x[1]) for x in locsort]
                # on recherche le premier 1
                if 1 in counts:
                    idx = counts.index(1)
                    # on ne conserve que la portion de liste utile
                    self._myselection = (ALL_SELECTED, np.array(sel[idx:]))
                else:
                    self._myselection = ALL_SELECTED  # All nodes are selected again
            else:
                # Add the new nodes to the selection

                if nbini != 0:
                    self._myselection += xy.tolist()

                    if verif:
                        # trouve les éléments uniques dans la liste de tuples (--> axis=0) et retourne également le comptage
                        selunique, counts = np.unique(self._myselection, return_counts=True, axis=0)

                        # les éléments énumérés plus d'une fois doivent être enlevés
                        # on trie par ordre décroissant
                        locsort = sorted(zip(counts.tolist(), selunique.tolist()), reverse=True)
                        counts = [x[0] for x in locsort]
                        sel = [tuple(x[1]) for x in locsort]

                        # on recherche le premier 1
                        if 1 in counts:
                            idx = counts.index(1)
                            # on ne conserve que la portion de liste utile
                            self._myselection = sel[idx:]
                        else:
                            self._myselection = []
                    else:
                        self._myselection = np.unique(self.myselection, axis=0).tolist()
                else:
                    self._myselection = xy.tolist()

        self.update_nb_nodes_selection()

    def _add_nodes_to_selection_np(self, ij:np.ndarray, verif:bool=True):
        """ Add multiple coordinates to the selection from a numpy array

        :param ij: numpy array of coordinates - same shape as the parent array (nbx, nby) or (nb_nodes, 2)
        :param verif: if True, the coordinates are checked to avoid duplicates
        """

        assert ij.shape == (self.parent.nbx, self.parent.nby) or ij.shape[1]==2, _('Invalid shape for ij - must be ({}, {})'.format(self.parent.nbx, self.parent.nby))

        dtype = ij.dtype
        if dtype not in [np.bool, np.int32, np.int64]:
            assert ij.shape[1] == 2, _('Invalid shape for ij - must be ({}, {}) or (nb_nodes, 2)'.format(self.parent.nbx, self.parent.nby))
            ij = self.parent.xy2ij_np(ij)

        if self._storage_mode == StorageMode.ARRAY:
            if verif:
                if ij.shape[1] == 2:
                    # using xy from np.where
                    self._myselection_as_array[ij[:,0], ij[:,1]] = np.logical_xor(self._myselection_as_array[ij[:, 0], ij[:, 1]], True)
                else:
                    self._myselection_as_array[:,:] = np.logical_xor(self._myselection_as_array, ij)
            else:
                if ij.shape[1] == 2:
                    # using xy from np.where
                    self._myselection_as_array[ij[:,0], ij[:,1]] = True
                else:
                    self._myselection_as_array[ij] = True

        elif self._storage_mode == StorageMode.LIST:
            if ij.shape[1] == 2:
                # using xy from np.where
                self._add_nodes_to_selectionij(ij, verif)
            else:
                # Convert the numpy array to a list of tuples
                ij = np.argwhere(ij)
                self._add_nodes_to_selectionij(ij, verif)

    def select_insidepoly(self, myvect: vector):
        """ Select nodes inside a polygon.

        :param myvect: vector defining the polygon
        """

        nbini = self.nb

        self.hideselection = self.parent.usemask

        inside = self.parent.get_ij_inside_polygon(myvect, usemask=self.hideselection)

        if inside.shape[0] == 0:
            logging.info(_('No nodes inside the polygon'))
            return
        else:
            if inside.shape[0] > self.threshold_array_mode:
                self.force_storage_mode(StorageMode.ARRAY)

            self._add_nodes_to_selectionij(inside, verif= nbini != 0)

        self.hideselection=False

    def select_underpoly(self, myvect: vector):
        """ Select nodes along a polyline

        :param myvect: vector defining the polyline
        """

        nbini = self.nb

        myvect.find_minmax()
        mypoints = self.parent.get_ij_under_polyline(myvect)

        if self.parent.usemask:
            # If the parent uses a mask, we need to check if the points are not masked
            mypoints = mypoints[~self.parent.array.mask[mypoints[:, 0], mypoints[:, 1]]]

        if len(mypoints) == 0:
            logging.info(_('No nodes under the polyline'))
            return

        self.add_nodes_to_selection(mypoints, verif = nbini != 0)

    def dilate_selection(self, nb_iterations:int, use_mask:bool = True, structure:np.ndarray = None):
        """ Extend the selection.

        :param nb_iterations: Number of iterations to dilate the selection
        :param use_mask: If True, use the mask of the parent array to limit the dilation
        :param structure: Structuring element for dilation, default is a cross shape (nodes directly adjacent in the x or y direction)
        """

        if self.is_all_selected():
            logging.info(_('Cannot extend selection when all nodes are selected'))
            return

        if self.nb == 0:
            logging.info(_('No nodes selected'))
            return

        if nb_iterations < 1:
            logging.info(_('Number of iterations must be greater than 0'))
            return

        if self.parent.array is None:
            logging.info(_('No array to select from'))
            return

        from scipy import ndimage

        self._myselection_as_array[:,:] = ndimage.binary_dilation(self._myselection_as_array,
                                           iterations=nb_iterations,
                                           mask=~self.parent.array.mask if use_mask else None,
                                           structure=structure)

        self._storage_mode = StorageMode.ARRAY  # Ensure we are in ARRAY mode
        self.update_nb_nodes_selection()

    def erode_selection(self, nb_iterations:int, use_mask:bool = True, structure:np.ndarray = None):
        """ Reduce the selection.

        :param nb_iterations: Number of iterations to erode the selection
        :param use_mask: If True, use the mask of the parent array to limit the erosion
        :param structure: Structuring element for erosion, default is a cross shape (nodes directly adjacent in the x or y direction)
        """

        if self.is_all_selected():
            logging.info(_('Cannot reduce selection when all nodes are selected'))
            return

        if self.nb == 0:
            logging.info(_('No nodes selected'))
            return

        if nb_iterations < 1:
            logging.info(_('Number of iterations must be greater than 0'))
            return

        if self.parent.array is None:
            logging.info(_('No array to select from'))
            return

        from scipy import ndimage

        self._myselection_as_array[:,:] = ndimage.binary_erosion(self._myselection_as_array,
                                            iterations=nb_iterations,
                                            mask=~self.parent.array.mask if use_mask else None,
                                            structure=structure)

        self._storage_mode = StorageMode.ARRAY  # Ensure we are in ARRAY mode
        self.update_nb_nodes_selection()

    def dilate_contour_selection(self, nbiter:int= 1, use_mask:bool = True, structure:np.ndarray = np.ones((3,3))):
        """ Dilate the contour of the selection.

        :param nbiter: Number of iterations to dilate the selection
        :param use_mask: If True, use the mask of the parent array to limit the dilation
        :param structure: Structuring element for dilation, default is a 3x3 square
        """

        if self.nb > 0:
            oldsel = self._myselection_as_array.copy()
            self.dilate_selection(nbiter, use_mask, structure)
            # We keep only the new nodes that were not in the old selection
            self._myselection_as_array[:,:] = np.logical_and(self._myselection_as_array, ~oldsel)
            self._storage_mode = StorageMode.ARRAY  # Ensure we are in ARRAY mode
            self.update_nb_nodes_selection()
        else:
            logging.info('No selection to expand/dilate')

    def erode_contour_selection(self):
        """ Erode the contour of the selection.

        :param nbiter: Number of iterations to erode the selection
        :param use_mask: If True, use the mask of the parent array to limit the erosion
        :param structure: Structuring element for erosion, default is a 3x3 square
        """

        if self.nb > 0:
            oldselect = self._myselection_as_array.copy()
            self.erode_selection(1)
            self._myselection_as_array[:,:] = np.logical_and(self._myselection_as_array, oldselect)
            self._storage_mode = StorageMode.ARRAY  # Ensure we are in ARRAY mode
            self.update_nb_nodes_selection()
        else:
            logging.info('No selection to contract/erode')

    def save_selection(self, filename:str=None):
        """ Save the selection to a file.

        :param filename: Name of the file to save the selection to. If None, a dialog will be shown to choose the file.
        """

        if filename is None:
            with wx.FileDialog(None, 'Save selection', wildcard='Text files (*.txt)|*.txt',
                                 style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
                if dlg.ShowModal() == wx.ID_CANCEL:
                    return
                filename = dlg.GetPath()

        with open(filename, 'w') as f:
            f.write(self.get_string(all_memories=True))

    def load_selection(self, filename:str=None):
        """ Load a selection from a file.

        :param filename: Name of the file to load the selection from. If None, a dialog will be shown to choose the file.
        """

        if filename is None:
            with wx.FileDialog(None, 'Load selection', wildcard='Text files (*.txt)|*.txt',
                                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
                if dlg.ShowModal() == wx.ID_CANCEL:
                    return
                filename = dlg.GetPath()

        with open(filename, 'r') as f:
            lines = f.readlines()

        xy = []
        k=0
        for line in lines:
            if line[0] == 'X':
                k+=1
                continue
            if line[0] == 'i':
                k+=1
                break
            x, y = line.split()
            xy.append((float(x), float(y)))
            k+=1

        self.myselection = xy
        self.update_nb_nodes_selection()

        k += len(xy)

        while k < len(lines):
            lines = lines[k:]
            k=0
            for line in lines:
                if 'Selection' in line:
                    idx = line.split()[1]
                    self.selections[idx] = {}
                    xy = []
                    k+=1
                elif 'Color' in line:
                    color = [int(x.replace('[','').replace(']','').replace(',','')) for x in line.split()[2:]]
                    self.selections[idx]['Color'] = color
                    k+=1
                elif line[0] == 'X':
                    k+=1
                    continue
                elif line[0] == 'i':
                    k+=len(xy)+1
                    self.selections[idx]['select']=xy
                    break
                else:
                    x, y = line.split()
                    xy.append((float(x), float(y)))
                    k+=1

        self.parent.reset_plot()

    def update_nb_nodes_selection(self, autostoragemode:bool=True) -> tuple[int, float, float, float, float]:
        """ Update the number of selected nodes.

        :param autostoragemode: If True, automatically switch to ARRAY mode if the number of selected nodes exceeds the threshold.
        :return: Tuple containing the number of selected nodes, and the bounds of the selection (xmin, xmax, ymin, ymax).
        """

        if autostoragemode:
            self._auto_storage_mode()

        if self._storage_mode == StorageMode.ARRAY:
            nb = np.count_nonzero(self._myselection_as_array)
        elif self._storage_mode == StorageMode.LIST:
            if self.is_all_selected():
                if self.parent.usemask:
                    nb = self.parent.nbnotnull
                else:
                    nb = self.parent.nbx * self.parent.nby
            elif isinstance(self._myselection, tuple) and len(self._myselection) == 2 and self._myselection[0] == ALL_SELECTED:
                # tuple of ('all', np.ndarray) for all nodes and excluded nodes

                if self.parent.usemask:
                    nb = self.parent.nbnotnull
                else:
                    nb = self.parent.nbx * self.parent.nby

                nb -= len(self._myselection[1])
            else:
                nb = len(self._myselection)

        self.update_plot_selection = True
        if self.wx_exists:
            if nb > 10000:
                if not self.hideselection:
                    self.update_plot_selection = False  # on met par défaut à False car OpenGL va demander une MAJ de l'affichage le temps que l'utilisateur réponde
                    dlg = wx.MessageDialog(None,
                                        'Large selection !!' + str(nb) + '\n Do you want plot the selected cells?',
                                        style=wx.YES_NO)
                    ret = dlg.ShowModal()
                    if ret == wx.ID_YES:
                        self.update_plot_selection = True
                    else:
                        self.update_plot_selection = False
                        self.hideselection = True
                    dlg.Destroy()
            else:
                self.update_plot_selection = True

        if nb>0:
            if self.is_all_selected():
                [xmin, xmax], [ymin, ymax] = self.parent.get_bounds()
            else:
                if self._storage_mode == StorageMode.ARRAY:
                    # Get the bounds of the selection from the boolean array
                    sel = np.argwhere(self._myselection_as_array)
                    xmin = np.min(sel[:, 0])
                    ymin = np.min(sel[:, 1])
                    xmax = np.max(sel[:, 0])
                    ymax = np.max(sel[:, 1])
                    xmin, ymin = self.parent.get_xy_from_ij(xmin, ymin)
                    xmax, ymax = self.parent.get_xy_from_ij(xmax, ymax)

                elif self._storage_mode == StorageMode.LIST:
                    xmin = np.min(np.asarray(self.myselection)[:, 0])
                    ymin = np.min(np.asarray(self.myselection)[:, 1])
                    xmax = np.max(np.asarray(self.myselection)[:, 0])
                    ymax = np.max(np.asarray(self.myselection)[:, 1])
        else:
            xmin = -99999.
            ymin = -99999.
            xmax = -99999.
            ymax = -99999.

        if self.parent.myops is not None:

            self.parent.myops.nbselect.SetLabelText(str(nb))
            self.parent.myops.nbselect2.SetLabelText(str(nb))

            if nb>0:

                self.parent.myops.minx.SetLabelText('{:.3f}'.format(xmin))
                self.parent.myops.miny.SetLabelText('{:.3f}'.format(ymin))
                self.parent.myops.maxx.SetLabelText('{:.3f}'.format(xmax))
                self.parent.myops.maxy.SetLabelText('{:.3f}'.format(ymax))

        return nb, xmin, xmax, ymin, ymax

    def condition_select(self, cond:str | int, condval, condval2 = 0, usemask:bool = False):
        """ Select nodes based on a condition.

        :param cond: condition to apply (0: '<', 1: '<=', 2: '==', 3: '>=', 4: '>', 5: 'NaN', 6: '>=<=', 7: '><', 8: '<>')
        :param condval: value to compare with
        :param condval2: second value to compare with (for ranges)
        :param usemask: whether to use the mask or not
        """

        array = self.parent.array
        nbini = self.nb

        if array.dtype == np.float32:
            condval = np.float32(condval)
            condval2 = np.float32(condval2)
        elif array.dtype == np.float64:
            condval = np.float64(condval)
            condval2 = np.float64(condval2)
        elif array.dtype == np.int32:
            condval = np.int32(condval)
            condval2 = np.int32(condval2)
        elif array.dtype == np.int64:
            condval = np.int64(condval)
            condval2 = np.int64(condval2)
        elif array.dtype == np.int16:
            condval = np.int16(condval)
            condval2 = np.int16(condval2)
        elif array.dtype == np.int8:
            condval = np.int8(condval)
            condval2 = np.int8(condval2)
        else:
            logging.error(_('Unknown dtype in treat_select !'))
            return


        if usemask :
            mask=np.logical_not(array.mask)
            if nbini == 0:
                try:
                    if cond == 0 or cond=='<':
                        # <
                        ij = np.argwhere((array < condval) & mask)
                    elif cond == 1 or cond=='<=':
                        # <=
                        ij = np.argwhere((array <= condval) & mask)
                    elif cond == 2 or cond=='==':
                        # ==
                        ij = np.argwhere((array == condval) & mask)
                    elif cond == 3 or cond=='>=':
                        # >=
                        ij = np.argwhere((array >= condval) & mask)
                    elif cond == 4 or cond=='>':
                        # >
                        ij = np.argwhere((array > condval) & mask)
                    elif cond == 5 or cond=='NaN':
                        # NaN
                        ij = np.argwhere((np.isnan(array)) & mask)
                    elif cond == 6 or cond=='>=<=':
                        # interval with equality
                        ij = np.argwhere(((array>=condval) & (array<=condval2)) & mask)
                    elif cond == 7 or cond=='><':
                        # interval without equality
                        ij = np.argwhere(((array>condval) & (array<condval2)) & mask)
                    elif cond == 8 or cond=='<>':
                        # interval without equality
                        ij = np.argwhere(((array<condval) | (array>condval2)) & mask)

                    self._add_nodes_to_selectionij(ij, nbini != 0)
                except:
                    logging.error(_('Error in condition_select -- nbini == 0 ! -- Please report this bug, specifying the context'))
                    return
            else:
                try:
                    if self.nb > self.threshold_array_mode:
                        # If the selection is large, we use the boolean array
                        ijall = np.argwhere(self._myselection_as_array)
                    else:
                        # Otherwise, we use the selection list
                        sel = np.asarray(self.myselection)
                        ijall = self.parent.xy2ij_np(sel)

                    if cond == 0 or cond=='<':
                        # <
                        ij = np.argwhere((array[ijall[:, 0], ijall[:, 1]] < condval) & (mask[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 1 or cond=='<=':
                        # <=
                        ij = np.argwhere((array[ijall[:, 0], ijall[:, 1]] <= condval) & (mask[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 2 or cond=='==':
                        # ==
                        ij = np.argwhere((array[ijall[:, 0], ijall[:, 1]] == condval) & (mask[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 3 or cond=='>=':
                        # >=
                        ij = np.argwhere((array[ijall[:, 0], ijall[:, 1]] >= condval) & (mask[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 4 or cond=='>':
                        # >
                        ij = np.argwhere((array[ijall[:, 0], ijall[:, 1]] > condval) & (mask[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 5 or cond=='NaN':
                        # NaN
                        ij = np.argwhere((np.isnan(array[ijall[:, 0], ijall[:, 1]])) & (mask[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 6 or cond=='>=<=':
                        # interval with equality
                        ij = np.argwhere(((array[ijall[:, 0], ijall[:, 1]]>=condval) & (array[ijall[:, 0], ijall[:, 1]]<=condval2)) & (mask[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 7 or cond=='><':
                        # interval without equality
                        ij = np.argwhere(((array[ijall[:, 0], ijall[:, 1]]>condval) & (array[ijall[:, 0], ijall[:, 1]]<condval2)) & (mask[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 8 or cond=='<>':
                        # interval without equality
                        ij = np.argwhere(((array[ijall[:, 0], ijall[:, 1]]<condval) | (array[ijall[:, 0], ijall[:, 1]]>condval2)) & (mask[ijall[:, 0], ijall[:, 1]]))

                    ij = ij.flatten()
                    self._add_nodes_to_selectionij(ijall[ij], nbini != 0)
                except:
                    logging.error(_('Error in condition_select ! -- Please report this bug, specifying the context'))
                    return
        else:
            if nbini == 0:
                try:
                    if cond == 0 or cond=='<':
                        # <
                        ij = np.argwhere(array < condval)
                    elif cond == 1 or cond=='<=':
                        # <=
                        ij = np.argwhere(array <= condval)
                    elif cond == 2 or cond=='==':
                        # ==
                        ij = np.argwhere(array == condval)
                    elif cond == 3 or cond=='>=':
                        # >=
                        ij = np.argwhere(array >= condval)
                    elif cond == 4 or cond=='>':
                        # >
                        ij = np.argwhere(array > condval)
                    elif cond == 5 or cond=='NaN':
                        # NaN
                        ij = np.argwhere(np.isnan(array))
                    elif cond == 6 or cond=='>=<=':
                        # interval with equality
                        ij = np.argwhere((array>=condval) & (array<=condval2))
                    elif cond == 7 or cond=='><':
                        # interval without equality
                        ij = np.argwhere((array>condval) & (array<condval2))
                    elif cond == 8 or cond=='<>':
                        # interval without equality
                        ij = np.argwhere((array<condval) | (array>condval2))
                    elif cond == -1 or cond=='Mask':
                        # Mask
                        ij = np.argwhere(array.mask)
                    elif cond == -2 or cond=='NotMask':
                        # Mask
                        ij = np.argwhere(np.logical_not(array.mask))

                    self._add_nodes_to_selectionij(ij, nbini != 0)
                except:
                    logging.error(_('Error in condition_select -- nbini == 0 ! -- Please report this bug, specifying the context'))
                    return
            else:
                try:
                    if self.nb > self.threshold_array_mode:
                        ijall = np.argwhere(self._myselection_as_array)
                    else:
                        sel = np.asarray(self.myselection)
                        ijall = self.parent.xy2ij_np(sel)

                    if cond == 0 or cond=='<':
                        # <
                        ij = np.argwhere(array[ijall[:, 0], ijall[:, 1]] < condval)
                    elif cond == 1 or cond=='<=':
                        # <=
                        ij = np.argwhere(array[ijall[:, 0], ijall[:, 1]] <= condval)
                    elif cond == 2 or cond=='==':
                        # ==
                        ij = np.argwhere(array[ijall[:, 0], ijall[:, 1]] == condval)
                    elif cond == 3 or cond=='>=':
                        # >=
                        ij = np.argwhere(array[ijall[:, 0], ijall[:, 1]] >= condval)
                    elif cond == 4 or cond=='>':
                        # >
                        ij = np.argwhere(array[ijall[:, 0], ijall[:, 1]] > condval)
                    elif cond == 5 or cond=='NaN':
                        # NaN
                        ij = np.argwhere(np.isnan(array[ijall[:, 0], ijall[:, 1]]))
                    elif cond == 6 or cond=='>=<=':
                        # interval with equality
                        ij = np.argwhere((array[ijall[:, 0], ijall[:, 1]]>=condval) & (array[ijall[:, 0], ijall[:, 1]]<=condval2))
                    elif cond == 7 or cond=='><':
                        # interval without equality
                        ij = np.argwhere((array[ijall[:, 0], ijall[:, 1]]>condval) & (array[ijall[:, 0], ijall[:, 1]]<condval2))
                    elif cond == 8 or cond=='<>':
                        # interval without equality
                        ij = np.argwhere((array[ijall[:, 0], ijall[:, 1]]<condval) | (array[ijall[:, 0], ijall[:, 1]]>condval2) )
                    elif cond == -1 or cond=='Mask':
                        # Mask
                        ij = np.argwhere(array.mask[ijall[:, 0], ijall[:, 1]])
                    elif cond == -2 or cond=='NotMask':
                        # Mask
                        ij = np.argwhere(np.logical_not(array.mask[ijall[:, 0], ijall[:, 1]]))

                    ij = ij.flatten()
                    self._add_nodes_to_selectionij(ijall[ij], nbini != 0)
                except:
                    logging.error(_('Error in condition_select ! -- Please report this bug, specifying the context'))
                    return

        # self.update_nb_nodes_selection()

    def treat_select(self, op:int, cond:int, opval, condval):
        """ Apply an operation on the selected nodes based on a condition.

        :param op: operation to apply (0: '+', 1: '-', 2: '*', 3: '/', 4: 'replace')
        :param cond: condition to apply (0: '<', 1: '<=', 2: '==', 3: '>=', 4: '>', 5: 'NaN')
        :param opval: value to apply the operation with
        :param condval: value to compare with
        """
        # operationChoices = [ u"+", u"-", u"*", u"/", u"replace'" ]
        # conditionChoices = [ u"<", u"<=", u"=", u">=", u">",u"isNaN" ]
        def test(val, cond, condval):
            if cond == 0:
                return val < condval
            elif cond == 1:
                return val <= condval
            elif cond == 2:
                return val == condval
            elif cond == 3:
                return val >= condval
            elif cond == 4:
                return val > condval
            elif cond == 5:
                return np.isnan(val)

        array = self.parent.array

        if array.dtype == np.float32:
            opval = np.float32(opval)
            condval = np.float32(condval)
        elif array.dtype == np.float64:
            opval = np.float64(opval)
            condval = np.float64(condval)
        elif array.dtype == np.int32:
            opval = np.int32(opval)
            condval = np.int32(condval)
        elif array.dtype == np.int64:
            opval = np.int64(opval)
            condval = np.int64(condval)
        elif array.dtype == np.int16:
            opval = np.int16(opval)
            condval = np.int16(condval)
        elif array.dtype == np.int8:
            opval = np.int8(opval)
            condval = np.int8(condval)
        else:
            logging.error(_('Unknown dtype in treat_select !'))
            return

        if self.myselection == ALL_SELECTED:
            if op == 0:
                if cond == 0:
                    # <
                    ind = np.argwhere(np.logical_and(array < condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] += opval
                elif cond == 1:
                    # <=
                    ind = np.argwhere(np.logical_and(array <= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] += opval
                elif cond == 2:
                    # ==
                    ind = np.argwhere(np.logical_and(array == condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] += opval
                elif cond == 3:
                    # >=
                    ind = np.argwhere(np.logical_and(array >= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] += opval
                elif cond == 4:
                    # >
                    ind = np.argwhere(np.logical_and(array > condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] += opval
                elif cond == 5:
                    # NaN
                    ind = np.argwhere(np.logical_and(np.isnan(array), np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
            elif op == 1:
                if cond == 0:
                    # <
                    ind = np.argwhere(np.logical_and(array < condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] -= opval
                elif cond == 1:
                    # <=
                    ind = np.argwhere(np.logical_and(array <= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] -= opval
                elif cond == 2:
                    # ==
                    ind = np.argwhere(np.logical_and(array == condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] -= opval
                elif cond == 3:
                    # >=
                    ind = np.argwhere(np.logical_and(array >= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] -= opval
                elif cond == 4:
                    # >
                    ind = np.argwhere(np.logical_and(array > condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] -= opval
                elif cond == 5:
                    # NaN
                    ind = np.argwhere(np.logical_and(np.isnan(array), np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
            elif op == 2:
                if cond == 0:
                    # <
                    ind = np.argwhere(np.logical_and(array < condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] *= opval
                elif cond == 1:
                    # <=
                    ind = np.argwhere(np.logical_and(array <= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] *= opval
                elif cond == 2:
                    # ==
                    ind = np.argwhere(np.logical_and(array == condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] *= opval
                elif cond == 3:
                    # >=
                    ind = np.argwhere(np.logical_and(array >= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] *= opval
                elif cond == 4:
                    # >
                    ind = np.argwhere(np.logical_and(array > condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] *= opval
                elif cond == 5:
                    # NaN
                    ind = np.argwhere(np.logical_and(np.isnan(array), np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
            elif op == 3 and opval != 0.:
                if cond == 0:
                    # <
                    ind = np.argwhere(np.logical_and(array < condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] /= opval
                elif cond == 1:
                    # <=
                    ind = np.argwhere(np.logical_and(array <= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] /= opval
                elif cond == 2:
                    # ==
                    ind = np.argwhere(np.logical_and(array == condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] /= opval
                elif cond == 3:
                    # >=
                    ind = np.argwhere(np.logical_and(array >= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] /= opval
                elif cond == 4:
                    # >
                    ind = np.argwhere(np.logical_and(array > condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] /= opval
                elif cond == 5:
                    # NaN
                    ind = np.argwhere(np.logical_and(np.isnan(array), np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = 0
            elif op == 4:
                if cond == 0:
                    # <
                    ind = np.argwhere(np.logical_and(array < condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
                elif cond == 1:
                    # <=
                    ind = np.argwhere(np.logical_and(array <= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
                elif cond == 2:
                    # ==
                    ind = np.argwhere(np.logical_and(array == condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
                elif cond == 3:
                    # >=
                    ind = np.argwhere(np.logical_and(array >= condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
                elif cond == 4:
                    # >
                    ind = np.argwhere(np.logical_and(array > condval, np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
                elif cond == 5:
                    # NaN
                    ind = np.argwhere(np.logical_and(np.isnan(array), np.logical_not(array.mask)))
                    array[ind[:, 0], ind[:, 1]] = opval
        else:
            if len(self.myselection) == 0:
                logging.info(_('Nothing to do in treat_select ! -- PLease select some nodes'))
                return

            ij = [self.parent.get_ij_from_xy(cur[0], cur[1]) for cur in self.myselection]

            if op == 0:
                for i, j in ij:
                    if test(array.data[i, j], cond, condval):
                        array.data[i, j] += opval
            elif op == 1:
                for i, j in ij:
                    if test(array.data[i, j], cond, condval):
                        array.data[i, j] -= opval
            elif op == 2:
                for i, j in ij:
                    if test(array.data[i, j], cond, condval):
                        array.data[i, j] *= opval
            elif op == 3 and opval != 0.:
                for i, j in ij:
                    if test(array.data[i, j], cond, condval):
                        array.data[i, j] /= opval
            elif op == 4:
                for i, j in ij:
                    if test(array.data[i, j], cond, condval):
                        array.data[i, j] = opval

        self.parent.mask_data(self.parent.nullvalue)

        self.refresh_parantarray()

    def refresh_parantarray(self):
        """ Refresh the parent array after a selection """

        self.parent.reset_plot()

    def mask_condition(self, op:int, cond:int, opval, condval):
        """ Mask nodes based on a condition.

        :param op: operation to apply (0: '+', 1: '-', 2: '*', 3: '/', 4: 'replace')
        :param cond: condition to apply (0: '<', 1: '<=', 2: '==', 3: '>=', 4: '>', 5: 'NaN')
        :param opval: value to apply the operation with
        :param condval: value to compare with
        """

        # operationChoices = [ u"+", u"-", u"*", u"/", u"replace'" ]
        # conditionChoices = [ u"<", u"<=", u"=", u">=", u">",u"isNaN" ]
        def test(val, cond, condval):
            if cond == 0:
                return val < condval
            elif cond == 1:
                return val <= condval
            elif cond == 2:
                return val == condval
            elif cond == 3:
                return val >= condval
            elif cond == 4:
                return val > condval
            elif cond == 5:
                return np.isnan(val)

        array = self.parent.array

        if array.dtype == np.float32:
            opval = np.float32(opval)
            condval = np.float32(condval)
        elif array.dtype == np.float64:
            opval = np.float64(opval)
            condval = np.float64(condval)
        elif array.dtype == np.int32:
            opval = np.int32(opval)
            condval = np.int32(condval)
        elif array.dtype == np.int64:
            opval = np.int64(opval)
            condval = np.int64(condval)
        elif array.dtype == np.int16:
            opval = np.int16(opval)
            condval = np.int16(condval)
        elif array.dtype == np.int8:
            opval = np.int8(opval)
            condval = np.int8(condval)
        else:
            logging.error(_('Unknown dtype in treat_select !'))
            return

        if self.myselection == ALL_SELECTED:
            if cond == 0:
                # <
                ind = np.argwhere(np.logical_and(array < condval, np.logical_not(array.mask)))
            elif cond == 1:
                # <=
                ind = np.argwhere(np.logical_and(array <= condval, np.logical_not(array.mask)))
            elif cond == 2:
                # ==
                ind = np.argwhere(np.logical_and(array == condval, np.logical_not(array.mask)))
            elif cond == 3:
                # >=
                ind = np.argwhere(np.logical_and(array >= condval, np.logical_not(array.mask)))
            elif cond == 4:
                # >
                ind = np.argwhere(np.logical_and(array > condval, np.logical_not(array.mask)))
            elif cond == 5:
                # NaN
                ind = np.argwhere(np.logical_and(np.isnan(array), np.logical_not(array.mask)))

            array.mask[ind[:, 0], ind[:, 1]] = True

        else:
            npself = np.asarray(self.myselection)
            ij = self.parent.xy2ij_np(npself)
            array.mask[ij[:, 0], ij[:, 1]] = test(array.data[ij[:, 0], ij[:, 1]], cond, condval)

            # ij = [self.parent.get_ij_from_xy(cur[0], cur[1]) for cur in self.myselection]

            # for i, j in ij:
            #     if test(array.data[i, j], cond, condval):
            #         array.mask[i, j] = True

        self.parent.nbnotnull = array.count()
        self.parent.updatepalette()
        self.parent.delete_lists()

    def get_values_sel(self) -> np.ndarray:
        """ Get the values of the selected nodes.

        :return: numpy array of values of the selected nodes, or -99999 if all nodes are selected.
        """

        if self.myselection == ALL_SELECTED:
            return -99999
        else:
            sel = np.asarray(self.myselection)
            if len(sel) == 1:
                ijall = self.parent.xy2ij_np(sel)
                z = self.parent.array[ijall[0], ijall[1]]
            else:
                ijall = self.parent.xy2ij_np(sel)
                z = self.parent.array[ijall[:, 0], ijall[:, 1]].flatten()

        return z

    def _get_header(self) -> header_wolf | None:
        """ Header corresponding to the selection """

        sel = np.asarray(self.myselection)

        myhead = header_wolf()

        if self.dx == 0. or self.dy == 0.:
            logging.error(_('dx or dy is null in get_header - Abort !'))
            return None

        myhead.dx = self.dx
        myhead.dy = self.dy
        myhead.translx = 0.
        myhead.transly = 0.

        myhead.origx = np.amin(sel[:, 0]) - self.dx / 2.
        myhead.origy = np.amin(sel[:, 1]) - self.dy / 2.

        ex = np.amax(sel[:, 0]) + self.dx / 2.
        ey = np.amax(sel[:, 1]) + self.dy / 2.

        myhead.nbx = int((ex - myhead.origx) / self.dx)
        myhead.nby = int((ey - myhead.origy) / self.dy)

        return myhead

    def get_newarray(self) -> "WolfArray":
        """ Create a new array from the selection.

        :return: a new WolfArray object containing the selected nodes, or None if the selection is empty. Null values are set to -99999.
        If all nodes are selected, returns a WolfArray molded from the parent.
        """

        if self.nb == 0:
            return None

        if self.myselection == ALL_SELECTED:
            return WolfArray(mold=self.parent)

        newarray = WolfArray()
        lochead = self._get_header()
        if lochead is None:
            logging.error(_('Error in get_newarray !'))
            return

        newarray.init_from_header(self._get_header())

        sel = np.asarray(self.myselection)
        if len(sel) == 1:
            # ijall = np.asarray(self.parent.get_ij_from_xy(sel[0, 0], sel[0, 1])).transpose()
            ijall = self.parent.xy2ij_np(sel)
            z = self.parent.array[ijall[0], ijall[1]]
        else:
            ijall = np.asarray(self.parent.get_ij_from_xy(sel[:, 0], sel[:, 1])).transpose()
            ijall = self.parent.xy2ij_np(sel)
            z = self.parent.array[ijall[:, 0], ijall[:, 1]].flatten()

        newarray.array[:, :] = -99999.
        newarray.nullvalue = -99999.

        newarray.set_values_sel(sel, z)

        return newarray

    def select_all(self):
        """ Select all nodes.

        It will set the selection to ALL_SELECTED, which is a special value indicating that all nodes are selected.
        """

        self.myselection = ALL_SELECTED

    def interp2Dpolygons(self, working_zone:zone,
                         method:Literal["nearest", "linear", "cubic"] = None,
                         resetplot:bool = True,
                         keep:Literal['all', 'below', 'above'] = 'all'):
        """
        Interpolation sous tous les polygones d'une zone
        cf parent.interp2Dpolygon

        Useful for WX GUI, where the method is chosen by the user.
        From script, you can call this method directly from the parent array
        with the desired method and keep parameters.
        """

        if method is None:
            choices = ["nearest", "linear", "cubic"]
            dlg = wx.SingleChoiceDialog(None, "Pick an interpolate method", "Choices", choices)
            ret = dlg.ShowModal()
            if ret == wx.ID_CANCEL:
                dlg.Destroy()
                return

            method = dlg.GetStringSelection()
            dlg.Destroy()

        self.parent.interpolate_on_polygons(working_zone, method, keep)

        if resetplot:
            self.parent.reset_plot()

    def interp2Dpolygon(self, working_vector:vector,
                        method:Literal["nearest", "linear", "cubic"] = None,
                        resetplot:bool = True,
                        keep:Literal['all', 'below', 'above'] = 'all'):
        """
        Interpolation sous un polygone
        cf parent.interp2Dpolygon

        Useful for WX GUI, where the method is chosen by the user.
        From script, you can call this method directly from the parent array
        with the desired method and keep parameters.
        """

        if method is None:
            choices = ["nearest", "linear", "cubic"]
            dlg = wx.SingleChoiceDialog(None, "Pick an interpolate method", "Choices", choices)
            ret = dlg.ShowModal()
            if ret == wx.ID_CANCEL:
                dlg.Destroy()
                return

            method = dlg.GetStringSelection()
            dlg.Destroy()

        self.parent.interpolate_on_polygon(working_vector, method, keep)

        if resetplot:
            self.parent.reset_plot()

    def interp2Dpolylines(self, working_zone:zone, resetplot:bool = True):
        """
        Interpolation sous toutes les polylignes de la zone
        cf parent.interp2Dpolyline

        Useful for WX GUI, where the method is chosen by the user.
        From script, you can call this method directly from the parent array
        with the desired method and keep parameters.
        """

        self.parent.interpolate_on_polylines(working_zone)

        if resetplot:
            self.parent.reset_plot()

    def interp2Dpolyline(self, working_vector:vector, resetplot:bool = True):
        """
        Interpolation sous la polyligne active
        cf parent.interp2Dpolyline

        Useful for WX GUI, where the method is chosen by the user.
        From script, you can call this method directly from the parent array
        with the desired method and keep parameters.
        """

        self.parent.interpolate_on_polyline(working_vector)

        if resetplot:
            self.parent.reset_plot()

    def copy(self, source:"SelectionData"):
        """ Copy the selection data from another SelectionData object.

        :param source: another SelectionData object to copy from.
        """

        if source._storage_mode == StorageMode.ARRAY:
            self._storage_mode = StorageMode.ARRAY
            self._myselection_as_array = source._myselection_as_array.copy()

        elif source._storage_mode == StorageMode.LIST:
            self._storage_mode = StorageMode.LIST
            self._myselection = source._myselection.copy()

    def volumesurface(self, show=True):
        """
        Evaluation of stage-storage-surface relation from "volume_estimation" routine of the WolfArray.

        If the selection is empty, it will use the whole array.
        If the selection is ALL_SELECTED, it will use the whole array.
        If the selection is not empty, it will use the selected nodes only -- see "get_newarray" routine.

        If the parent array is linked to a MapViewer, it will apply the same operation to all linked active arrays.

        :param show: if True, the figure will be shown.
        """

        if self.parent.get_mapviewer() is not None:

            mapviewer = self.parent.get_mapviewer()

            if mapviewer.linked:

                # If linked arrays, we copy the selection data to all linked arrays
                arrays = [cur.active_array for cur in mapviewer.linkedList]
                for cur in arrays:
                    if cur is not self.parent:
                        cur.SelectionData.copy(self.parent.SelectionData)

                if self.nb == 0 or self.myselection == ALL_SELECTED:
                    for cur in arrays:
                        fig, axs = cur.volume_estimation()
                        if show:
                            fig.show()
                else:
                    for cur in arrays:
                        myarray = cur.SelectionData.get_newarray()
                        fig, axs = myarray.volume_estimation()
                        if show:
                            fig.show()
            else:
                if len(self.parent.SelectionData.myselection) == 0 or self.parent.SelectionData.myselection == ALL_SELECTED:
                    myarray = self.parent
                else:
                    myarray = self.parent.SelectionData.get_newarray()
                    myarray.SelectionData.selections = self.parent.SelectionData.selections.copy()

                fig, axs = myarray.volume_estimation()

                if show:
                    fig.show()
        else:
            if self.nb == 0 or self.myselection == ALL_SELECTED:
                myarray = self.parent
            else:
                myarray = self.get_newarray()
                myarray.SelectionData.selections = self.selections.copy()

            fig, axs = myarray.volume_estimation()

            if show:
                fig.show()

class SelectionDataMB(SelectionData):
    """ Extension of SelectionData to manage multiple blocks.

    All routines are not implemented yet, as they depend on the specificities of the blocks.

    For the rest, it is mainly a simple wrapper around the SelectionData of each block.
    """

    def __init__(self, parent:"WolfArrayMB"):
        SelectionData.__init__(self, parent)

        self.parent:"WolfArrayMB" = parent

    @property
    def nb(self):

        return np.sum([cur.SelectionData.nb for cur in self.parent.active_blocks])

    def unmask_selection(self):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.unmask_selection(resetplot=False)

        self.parent.reset_plot()

    def reset(self):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.reset()

    def select_all(self):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.select_all()

    def reset_all(self):
        """ Reset the selection """

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.reset_all()

    def get_string(self, which:str = None) -> str:

        logging.error(_('Not yet implemented for Multi-Blocks'))

    def save_selection(self, filename:str=None, which:str = None):

        logging.error(_('Not yet implemented for Multi-Blocks'))

    def load_selection(self, filename:str=None, which:str = None):

        logging.error(_('Not yet implemented for Multi-Blocks'))

    def get_script(self, which:int = None) -> str:

        logging.error(_('Not yet implemented for Multi-Blocks'))

    def get_newarray(self):

        logging.error(_('Not yet implemented for Multi-Blocks'))

    def add_node_to_selection(self, x:float, y:float, verif:bool=True):
        """ Add a node to the selection """

        for curblock in self.parent.active_blocks:
            ret = curblock.SelectionData.add_node_to_selection(x, y, verif)

    def add_nodes_to_selection(self, xy:list[float] | np.ndarray, verif:bool=True):
        """ Add nodes to the selection """

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.add_nodes_to_selection(xy, verif)

    def select_insidepoly(self, myvect: vector):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.select_insidepoly(myvect)

    def select_underpoly(self, myvect: vector):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.select_underpoly(myvect)

    def dilate_selection(self, nb_iterations:int, use_mask:bool = True, structure:np.ndarray = None):
        """ Extend the selection """

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.dilate_selection(nb_iterations, use_mask, structure)

    def erode_selection(self, nb_iterations:int, use_mask:bool = True, structure:np.ndarray = None):
        """ Reduce the selection """

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.erode_selection(nb_iterations, use_mask, structure)

    def update_nb_nodes_selection(self):
        """ Update the number of nodes selected """

        # Get infos from all blocks
        ret = []
        for curblock in self.parent.active_blocks:
            ret.append(curblock.SelectionData.update_nb_nodes_selection())

        # sum all the nodes
        nb = np.sum([cur[0] for cur in ret])

        if nb > 0 :
            xmin = np.min([cur[1] for cur in ret if cur[1] != -99999.])
            ymin = np.min([cur[3] for cur in ret if cur[3] != -99999.])
            xmax = np.max([cur[2] for cur in ret if cur[2] != -99999.])
            ymax = np.max([cur[4] for cur in ret if cur[4] != -99999.])

        if self.parent.myops is not None:

            self.parent.myops.nbselect.SetLabelText(str(nb))
            self.parent.myops.nbselect2.SetLabelText(str(nb))

            if nb>0:
                self.parent.myops.minx.SetLabelText('{:.3f}'.format(xmin))
                self.parent.myops.miny.SetLabelText('{:.3f}'.format(ymin))
                self.parent.myops.maxx.SetLabelText('{:.3f}'.format(xmax))
                self.parent.myops.maxy.SetLabelText('{:.3f}'.format(ymax))
            else:
                self.parent.myops.minx.SetLabelText('')
                self.parent.myops.miny.SetLabelText('')
                self.parent.myops.maxx.SetLabelText('')
                self.parent.myops.maxy.SetLabelText('')


    def condition_select(self, cond, condval, condval2=0, usemask=False):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.condition_select(cond, condval, condval2, usemask)

    def treat_select(self, op, cond, opval, condval):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.treat_select(op, cond, opval, condval)

    def mask_condition(self, op, cond, opval, condval):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.mask_condition(op, cond, opval, condval)

    def plot_selection(self):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.plot_selection()

    def move_selectionto(self, idx:str, color:list[float]):

        for curblock in self.parent.active_blocks:
            curblock.SelectionData.move_selectionto(idx, color, resetplot=False)

        self.parent.reset_plot()

    def copy_to_clipboard(self, which:int = None, typestr:Literal['string', 'script'] = 'string'):

        logging.error(_('Not yet implemented for Multi-Blocks'))

    def interp2Dpolygons(self, working_zone:zone,
                         method:Literal["nearest", "linear", "cubic"] = None,
                         resetplot:bool = True,
                         keep:Literal['all', 'below', 'above'] = 'all'):
        """
        Interpolation sous tous les polygones d'une zone
        cf parent.interp2Dpolygon
        """

        if method is None:
            choices = ["nearest", "linear", "cubic"]
            dlg = wx.SingleChoiceDialog(None, "Pick an interpolate method", "Choices", choices)
            ret = dlg.ShowModal()
            if ret == wx.ID_CANCEL:
                dlg.Destroy()
                return

            method = dlg.GetStringSelection()
            dlg.Destroy()

        self.parent.interpolate_on_polygons(working_zone, method, keep)

        if resetplot:
            self.parent.reset_plot()

    def interp2Dpolygon(self, working_vector:vector,
                        method:Literal["nearest", "linear", "cubic"] = None,
                        resetplot:bool = True,
                        keep:Literal['all', 'below', 'above'] = 'all'):
        """
        Interpolation sous un polygone
        cf parent.interp2Dpolygon
        """

        if method is None:
            choices = ["nearest", "linear", "cubic"]
            dlg = wx.SingleChoiceDialog(None, "Pick an interpolate method", "Choices", choices)
            ret = dlg.ShowModal()
            if ret == wx.ID_CANCEL:
                dlg.Destroy()
                return

            method = dlg.GetStringSelection()
            dlg.Destroy()

        self.parent.interpolate_on_polygon(working_vector, method, keep)

        if resetplot:
            self.parent.reset_plot()

    def interp2Dpolylines(self, working_zone:zone, resetplot:bool = True):
        """
        Interpolation sous toutes les polylignes de la zone
        cf parent.interp2Dpolyline
        """

        self.parent.interpolate_on_polylines(working_zone)

        self.parent.reset_plot()

    def interp2Dpolyline(self, working_vector:vector, resetplot:bool = True):
        """
        Interpolation sous la polyligne active
        cf parent.interp2Dpolyline
        """

        self.parent.interpolate_on_polyline(working_vector)

        self.parent.reset_plot()

    def volumesurface(self, show=True):
        """
        Evaluation of stage-storage-surface relation
        """

        logging.error(_('Not yet implemented for Multi-Blocks'))

class WolfArray(Element_To_Draw, header_wolf):
    """
    Classe pour l'importation de WOLF arrays

    simple précision, double précision, entier...
    """
    array: ma.masked_array
    mygrid: dict # For OpenGL
    linkedvec: vector # used in some operations
    linkedarrays: list["WolfArray"] # used in some operations

    # Origin and translation of the coordinate-system
    # in which the array-data coordinates are expressed.
    origx: float
    origy: float
    origz: float
    translx: float
    transly: float
    translz: float

    myops: Ops_Array

    def __init__(self,
                 fname:str          = None,
                 mold:"WolfArray"   = None,
                 masknull:bool      = True,
                 crop:list[list[float],list[float]]=None,
                 whichtype          = WOLF_ARRAY_FULL_SINGLE,
                 preload:bool       = True,
                 create:bool        = False,
                 mapviewer          = None,
                 nullvalue:float    = 0.,
                 srcheader:header_wolf = None,
                 idx:str            = '',
                 plotted:bool       = False,
                 need_for_wx:bool   = False,
                 mask_source:np.ndarray = None,
                 np_source:np.ndarray = None,
                 ) -> None:
        """
        Constructor of the WolfArray class

        :param fname: filename/filepath - if provided, the file will be read on disk
        :param mold: initialize from a copy a the mold object --> must be a WolfArray if not None - Do not impose the type of the array. The source array will be converted if necessary. Change "whichtype" to impose a type.
        :param masknull: mask data based on the nullvalue
        :param crop: crop data based on the spatial extent [[xmin, xmax], [ymin,ymax]]
        :param whichtype: type of the numpy array (float32 as default)
        :param preload: True = load data during initialization ; False = waits for the display to be required
        :param create: True = create a new array from wxDialog
        :param mapviewer: WolfMapViewer instance to display data
        :param nullvalue: null value used to mask data
        :param srcheader: initialize dimension from header_wolf instance
        :param idx: indentity --> required by the mapviewer
        :param plotted: True = will be plotted if required by the mapviewer
        :param need_for_wx: True = a wxApp is required (if no application is underway --> Error)
        :param mask_source: mask to link to the data
        :param np_source: numpy array to link to the data

        """
        try:
            pass
            # wolfogl.powermode('ON')
        except PermissionError:
            print(_('wolfogl not available -- Pleas check your wolfhece installation'))

        Element_To_Draw.__init__(self, idx, plotted, mapviewer, need_for_wx)
        header_wolf.__init__(self)

        self.mngselection = None

        self.myblocks = None
        self._active_blocks = None

        self.flipupd=False
        self.array:ma.masked_array = None       # numpy masked array to stored numerical data

        self.linkedvec = None
        self.linkedarrays = []

        self.filename = ''
        self.isblock = False
        self.blockindex = 0
        self.wolftype = whichtype

        self.preload = preload
        self.loaded = False
        self.masknull = masknull

        if VERSION_RGB==1 : self.rgb = None         # numpy array with colorize values
        self.alpha = 1.         # transparency alpha value
        self.shading = False    # if True, rgb will be shaded

        self.azimuthhill = 315. # sun position - azimuth
        self.altitudehill = 0.  # sun position - altitude

        if self.wolftype != WOLF_ARRAY_HILLSHAPE and mapviewer is not None:
            self.shaded = WolfArray(whichtype=WOLF_ARRAY_HILLSHAPE)
            self.shaded.mypal.defaultgray()
            self.shaded.mypal.automatic = False
        else:
            self.shaded = None

        self._nullvalue = nullvalue
        self.nbnotnull = 99999      # number of non-null values in the entire aray
        self.nbnotnullzoom = 99999  # number of non-null values in the current visible part in mapviwer
        self.nbtoplot = 0

        self.gridsize = 100         # virtual grid for plotting operations
        self.gridmaxscales = -1     # maximum scale used

        # colormap
        self.mypal = wolfpalette(None, "Palette of colors")
        self.mypal.default16()
        self.mypal.automatic = True
        self.mygrid = {}

        self._array3d = None
        self.viewers3d:list[WolfArray_plot3D] = []

        self.cropini = crop

        if isinstance(srcheader, header_wolf):
            header=srcheader
            self.origx = header.origx
            self.origy = header.origy
            self.origz = header.origz

            self.translx = header.translx
            self.transly = header.transly
            self.translz = header.translz

            self.dx = header.dx
            self.dy = header.dy
            self.dz = header.dz

            self.nbx = int(header.nbx)
            self.nby = int(header.nby)
            self.nbz = int(header.nbz)

            self.head_blocks = header.head_blocks.copy()

            if self.nb_blocks>0:
                self.myblocks = {}

            if np_source is None:
                self.allocate_ressources()
            else:
                assert np_source.shape == (self.nbx, self.nby), _('Shape of np_source is not compatible with header')

                if self.dtype != np_source.dtype:
                    logging.warning(_(f"dtype of np_source is not compatible with header -- Conversion will be done to match wolf header's type {self.dtype}"))
                    np_source = np_source.astype(self.dtype)

                self.array = ma.MaskedArray(np_source, mask= np_source[:,:] == self.nullvalue if self.masknull else np.zeros(np_source.shape, dtype=bool), copy=False, order='C')

            # # FIXME Why not initialize with nullvalue ?
            # self.array = ma.MaskedArray(np.ones((self.nbx, self.nby), order='F', dtype=self.dtype))

        if fname is not None:

            # check if fname is an url
            if str(fname).startswith('http:') or str(fname).startswith('https:'):
                try:
                    fname = download_file(fname)
                except Exception as e:
                    logging.error(_('Error while downloading file: %s') % e)
                    return

            self.filename = str(fname)
            logging.debug(_('Loading file : %s') % self.filename)
            self.read_all()

            if mask_source is not None:
                logging.debug(_('Applying mask from source'))
                self.copy_mask_log(mask_source)
                logging.debug(_('Data masked'))
            elif masknull and (self.preload or self.loaded):
                logging.debug(_('Masking data with nullvalue'))
                self.mask_data(self.nullvalue)
                logging.debug(_('Data masked'))

        elif mold is not None:
            if self.cropini is None:
                self.nbx = mold.nbx
                self.nby = mold.nby
                self.nbz = mold.nbz
                self.dx = mold.dx
                self.dy = mold.dy
                self.dz = mold.dz
                self.origx = mold.origx
                self.origy = mold.origy
                self.origz = mold.origz
                self.translx = mold.translx
                self.transly = mold.transly
                self.translz = mold.translz
                self.array = ma.copy(mold.array.astype(self.dtype))
                if idx=='':
                    self.idx = mold.idx
            else:
                imin, jmin = mold.get_ij_from_xy(self.cropini[0][0], self.cropini[1][0])
                imax, jmax = mold.get_ij_from_xy(self.cropini[0][1], self.cropini[1][1])

                imin = int(imin)
                jmin = int(jmin)
                imax = int(imax)
                jmax = int(jmax)

                self.nbx = imax - imin
                self.nby = jmax - jmin
                self.dx  = mold.dx
                self.dy  = mold.dy
                self.origx, self.origy = mold.get_xy_from_ij(imin, jmin)
                self.origx -= self.dx / 2.
                self.origy -= self.dy / 2.
                self.translx = mold.translx
                self.transly = mold.transly

                if idx=='':
                    self.idx = mold.idx

                self.array = ma.copy(mold.array[imin:imax, jmin:jmax].astype(self.dtype))

        elif create:
            assert self.wx_exists, _('Array creation required a running wx App to display the UI')
            # Dialog for the creation of a new array
            new = NewArray(None, self.get_mapviewer())

            ret = new.ShowModal()
            if ret == wx.ID_CANCEL:
                return
            else:
                self.init_from_new(new)


        self.add_ops_sel() # Ajout d'un gestionnaire de sélection et d'opérations

    @property
    def epsg_parent(self) -> int:
        """ Get the EPSG code of the parent mapviewer """
        if self.get_mapviewer() is not None:
            return self.get_mapviewer().epsg
        else:
            logging.debug(_('No mapviewer linked to the array -- returning array EPSG'))
            return self.epsg

    def _check_epsg_coherence(self):
        """ Check the coherence of the EPSG code between the array and the mapviewer """
        epsg_viewer = self.epsg_parent
        if epsg_viewer is None or epsg_viewer != self.epsg:
            logging.warning(_('EPSG code of the array (%s) is different from the mapviewer (%s)') % (self.epsg, epsg_viewer))
            return False

        return True

    @property
    def usemask(self):
        """ Check if we want to use the mask in the operations """
        if self.myops is not None:
            return self.myops.usemask
        else:
            return False

    def __getstate__(self):
        """ Récupération de l'état de l'objet pour la sérialisation """
        state = self.__dict__.copy()

        # Remove the OpenGL reference to avoid bad references
        if 'mygrid' in state:
            state['mygrid'] = {}
            """ If not empty, the OpenGL list is not properly serialized.
            During "delete_lists" routine, tghe OpenGL can produce an error.
            """
        if 'shaded' in state:
            state['shaded'] = None  # Avoid serializing the shaded WolfArray
        return state

    def __setstate__(self, state):
        """ Récupération de l'état de l'objet pour la désérialisation """
        self.__dict__.update(state)

    def set_opacity(self, alpha:float):
        """ Set the transparency of the array """

        if alpha <0.:
            alpha = 0.

        if alpha > 1.:
            alpha = 1.

        self.alpha = alpha

        if self.myops is not None:
            self.myops.palalpha.SetValue(0)
            self.myops.palalphaslider.SetValue(int(alpha*100))

        self.reset_plot()

        return self.alpha

    # def find_minmax(self, update=False):

    #     if update:
    #         [self.xmin, self.xmax], [self.ymin, self.ymax] = self.get_bounds()

    @property
    def memory_usage(self):
        """
        Return the memory usage of the header
        """

        if self.nbz == 0:
            size = self.nbx * self.nby
        else:
            size = self.nbx * self.nby * self.nbz

        if self.wolftype == WOLF_ARRAY_FULL_SINGLE:
            return size * 4
        elif self.wolftype == WOLF_ARRAY_FULL_DOUBLE:
            return size * 8
        elif self.wolftype == WOLF_ARRAY_FULL_INTEGER:
            return size * 4
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
            return size * 2
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8]:
            return size
        else:
            return size * 4

    @property
    def memory_usage_mask(self):
        """
        Return the memory usage of the mask
        """

        if self.nbz == 0:
            size = self.nbx * self.nby
        else:
            size = self.nbx * self.nby * self.nbz

        return size * 1

    def __del__(self):
        """ Destructeur de la classe """
        try:
            # Perform cleanup tasks safely
            self.delete_lists()
            if hasattr(self, 'array'):
                del self.array
            if VERSION_RGB == 1 and hasattr(self, 'rgb'):
                del self.rgb
            if hasattr(self, '_array3d'):
                del self._array3d
            if hasattr(self, 'mypal'):
                del self.mypal
            if hasattr(self, 'shaded'):
                del self.shaded

            try:
                if sys.meta_path is not None:
                    # Perform garbage collection if gc is available
                    import gc
                    gc.collect()
            except Exception:
                # Try/except to avoid issues during interpreter shutdown
                pass

        except Exception as e:
            print(f"Exception in WolfArray destructor: {e} -- Please report this issue")

    def extract_selection(self):
        """ Extract the current selection """

        newarray = self.SelectionData.get_newarray()

        mapviewer = self.get_mapviewer()

        if mapviewer is not None:
            mapviewer.add_object('array', newobj = newarray, ToCheck = True, id = self.idx + '_extracted')

    def get_centers(self, usenap:bool = True):
        """ Get the centers of the cells """

        if usenap:
            ij = np.argwhere(self.array.mask==False,)
            xy = self.get_xy_from_ij_array(ij).copy().flatten()
        else:
            ij = np.meshgrid(np.arange(self.nbx), np.arange(self.nby))
            ij = np.asarray([ij[0].flatten(), ij[1].flatten()]).T
            xy = self.get_xy_from_ij_array(ij).copy().flatten()

        return xy.astype(np.float32)

    def prepare_3D(self):
        """ Prepare the array for 3D display """

        if self.array.ndim != 2:
            logging.error(_('Array is not 2D'))
            return

        self._quads = self.get_centers()
        ztext = np.require(self.array.data.copy(), dtype=np.float32, requirements=['C'])

        assert ztext.flags.c_contiguous, _('ztext is not C-contiguous')

        ztext[self.array.mask] = self.array.min()
        self._array3d = WolfArray_plot3D(self._quads,
                                         self.dx, self.dy,
                                         self.origx, self.origy,
                                         zscale = 1.,
                                         ztexture = ztext,
                                         color_palette=self.mypal.get_colors_f32().flatten(),
                                         color_values=self.mypal.values.astype(np.float32))

    def check_bounds_ij(self, i:int, j:int):
        """Check if i and j are inside the array bounds"""
        return i>=0 and j>=0 and i<self.nbx and j<self.nby

    def check_bounds_xy(self, x:float, y:float):
        """Check if i and j are inside the array bounds"""
        i,j = self.get_ij_from_xy(x,y)
        return self.check_bounds_ij(i,j)

    def show_properties(self):
        """ Affichage des propriétés de la matrice dans une fenêtre wxPython """
        if self.wx_exists and self.myops is not None:
            self.myops.SetTitle(_('Operations on array: ') + self.idx)

            self.myops.Show()

            self.myops.Center()
            self.myops.Raise()

    def hide_properties(self):
        """ Hide the properties window """

        if self.wx_exists and self.myops is not None:
            self.myops.hide_properties()

    @property
    def nullvalue(self) -> float:
        """ Return the null value """
        return self._nullvalue

    @nullvalue.setter
    def nullvalue(self, value:float):
        """ Set the null value """

        self._nullvalue = value

    @property
    def nodata(self) -> float:
        """ alias for nullvalue """
        return self._nullvalue

    @nodata.setter
    def nodata(self, value:float):
        """ alias for nullvalue """
        self._nullvalue = value

    @property
    def SelectionData(self) -> SelectionData:
        """ Return the data of the selection """

        return self.mngselection

    @property
    def Operations(self) -> Ops_Array:
        """ Return the operations on the array """
        return self.myops

    @property
    def active_blocks(self) -> list["WolfArray"]:
        """ Return the active blocks """

        if self.nb_blocks>0 and self._active_blocks is not None:

            if isinstance(self._active_blocks, list):
                return [self.myblocks[cur] for cur in self._active_blocks]
            elif self._active_blocks == 0:
                return [k for k in self.myblocks.values()]
            elif self._active_blocks in self.myblocks:
                return [self.myblocks[self._active_blocks]]
            else:
                return None

        else:
            return [self]

    @active_blocks.setter
    def active_blocks(self, value:Union[str, int, list[int]]):
        """
        Set the active blocks

        :param value: name of the block or index 1-based or list of index 1-based

        """

        if isinstance(value, str):
            if value in self.myblocks:
                self._active_blocks = value
                logging.info(_(f'Block found - {value}'))
            else:
                self._active_blocks = None
                logging.info(_('Block not found'))

        elif isinstance(value, int):

            if value == 0:
                self._active_blocks = 0
                logging.info(_('All blocks selected'))
            else:
                value = getkeyblock(value, addone=False)

                if value in self.myblocks:
                    self._active_blocks = value
                    logging.info(_(f'Block found - {value}'))
                else:
                    self._active_blocks = None
                    logging.info(_('Block not found'))

        elif isinstance(value, list):

            if 0 in value:
                self._active_blocks = 0
                logging.info(_('All blocks selected'))
            else:
                value = [getkeyblock(cur, addone=False) for cur in value]
                value = [cur for cur in value if cur in self.myblocks]

                if len(value)>0:
                    self._active_blocks = value
                    logging.info(_('List of blocks selected'))
                else:
                    self._active_blocks = None
                    logging.info(_('No block found'))

        else:
            logging.error(_('Unknown type for active_blocks'))

    @property
    def dtype(self):
        """
        Return the numpy dtype corresponding to the WOLF type

        Pay ettention to the difference between :
         - LOGICAL : Fortran and VB6
         - Bool : Python

        In VB6, logical is stored as int16
        In Fortran, there are Logical*1, Logical*2, Logical*4, Logical*8
        In Python, bool is one byte
        In Numpy, np.bool_ is one byte
        """

        if self.wolftype in [WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_SYM_DOUBLE, WOLF_ARRAY_CSR_DOUBLE]:
            dtype = np.float64
        elif self.wolftype in [WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_FULL_SINGLE_3D, WOLF_ARRAY_MB_SINGLE]:
            dtype = np.float32
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_MB_INTEGER, WOLF_ARRAY_MNAP_INTEGER]:
            dtype = np.int32
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
            dtype = np.int16
        elif self.wolftype == WOLF_ARRAY_FULL_INTEGER8:
            dtype = np.int8
        elif self.wolftype == WOLF_ARRAY_FULL_UINTEGER8:
            dtype = np.uint8
        elif self.wolftype == WOLF_ARRAY_FULL_LOGICAL:
            dtype = np.int16

        return dtype

    @property
    def dtype_gdal(self):
        """ Return the GDAL dtype corresponding to the WOLF type """

        if self.wolftype in [WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_SYM_DOUBLE, WOLF_ARRAY_CSR_DOUBLE]:
            dtype = gdal.GDT_Float64
        elif self.wolftype in [WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_FULL_SINGLE_3D, WOLF_ARRAY_MB_SINGLE]:
            dtype = gdal.GDT_Float32
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_MB_INTEGER, WOLF_ARRAY_MNAP_INTEGER]:
            dtype = gdal.GDT_Int32
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
            dtype = gdal.GDT_Int16
        elif self.wolftype == WOLF_ARRAY_FULL_INTEGER8:
            dtype = gdal.GDT_Byte
        elif self.wolftype == WOLF_ARRAY_FULL_UINTEGER8:
            dtype = gdal.GDT_Byte
        elif self.wolftype == WOLF_ARRAY_FULL_LOGICAL:
            dtype = gdal.GDT_Int16

        return dtype

    @property
    def dtype_str(self):
        """
        Return the numpy dtype corresponding to the WOLF type, as a string

        Pay ettention to the difference between :
            - LOGICAL : Fortran and VB6
            - Bool : Python

        In VB6, logical is stored as int16
        In Fortran, there are Logical*1, Logical*2, Logical*4, Logical*8
        In Python, bool is one byte
        In Numpy, np.bool_ is one byte
        """

        if self.wolftype in [WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_SYM_DOUBLE, WOLF_ARRAY_CSR_DOUBLE]:
            dtype = _('float64 - 8 bytes per values')
        elif self.wolftype in [WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_FULL_SINGLE_3D, WOLF_ARRAY_MB_SINGLE]:
            dtype = _('float32 - 4 bytes per values')
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_MB_INTEGER, WOLF_ARRAY_MNAP_INTEGER]:
            dtype = _('int32 - 4 bytes per values')
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
            dtype = _('int16 - 2 bytes per values')
        elif self.wolftype == WOLF_ARRAY_FULL_INTEGER8:
            dtype = _('int8 - 1 byte per values')
        elif self.wolftype == WOLF_ARRAY_FULL_UINTEGER8:
            dtype = _('uint8 - 1 byte per values')
        elif self.wolftype == WOLF_ARRAY_FULL_LOGICAL:
            dtype = _('int16 - 2 bytes per values')

        return dtype

    @property
    def zmin(self):
        """ Return the minimum value of the masked array """

        return np.ma.min(self.array)

    @property
    def zmax(self):
        """ Return the maximum value of the masked array """

        return np.ma.max(self.array)

    @property
    def zmin_global(self):
        """ Return the minimum value of the array -- all data (masked or not) """

        return np.min(self.array.data)

    @property
    def zmax_global(self):
        """ Return the maximum value of the array -- all data (masked or not) """

        return np.max(self.array.data)

    def loadnap_and_apply(self):
        """
        Load a mask file (aka nap) and apply it to the array;

        The mask values are set to the nullvalue.

        The mask file must have the same name as the array file, with the extension .napbin.
        It is useful for 2D WOLF simulations.
        """

        file_name, file_extension = os.path.splitext(self.filename)
        fnnap = file_name + '.napbin'
        if os.path.exists(fnnap):
            locnap = WolfArray(fnnap)

            self.array.data[np.where(locnap.array.mask)] = self.nullvalue
            self.mask_data(self.nullvalue)

            self.reset_plot()

    def add_crosslinked_array(self, newlink:"WolfArray"):
        """Ajout d'une matrice liée croisée"""
        self.linkedarrays.append(newlink)
        newlink.linkedarrays.append(self)

    def share_palette(self):
        """Partage de la palette de couleurs entre matrices liées"""
        for cur in self.linkedarrays:
            if id(cur.mypal) != id(self.mypal):
                cur.mypal = self.mypal

    def filter_inundation(self, epsilon:float = None, mask:np.ndarray = None):
        """
        Apply filter on array :
            - mask data below eps
            - mask data outisde linkedvec

        :param epsilon: value under which data are masked
        :param mask: mask to apply if eps is None

        If all params are None, the function will mask NaN values
        """
        if epsilon is not None:
            self.array[np.where(self.array<epsilon)] = self.nullvalue
        elif mask is not None:
            self.array.data[mask] = self.nullvalue

        idx_nan  = np.where(np.isnan(self.array))

        if len(idx_nan[0])>0:

            self.array[idx_nan] = self.nullvalue
            self.array.mask[idx_nan] = True

            logging.warning(_('NaN values found in the array'))

            if len(idx_nan[0])<10:
                for i,j in zip(idx_nan[0],idx_nan[1]):
                    logging.warning(f'NaN at {i+1},{j+1} -- 1-based')
            else:
                for i,j in zip(idx_nan[0][:10],idx_nan[1][:10]):
                    logging.warning(f'NaN at {i+1},{j+1} -- 1-based')

                logging.warning(f'... and {len(idx_nan[0])-10} more')

        self.mask_data(self.nullvalue)

        if self.linkedvec is not None:
            self.mask_outsidepoly(self.linkedvec)

        self.reset_plot()

    def filter_independent_zones(self, n_largest:int = 1, reset_plot:bool = True):
        """
        Filtre des zones indépendantes et conservation des n plus grandes

        """

        # labellisation
        labeled_array = self.array.data.copy()
        labeled_array[np.where(self.array.mask)] = 0

        labeled_array, num_features = label(labeled_array)
        # convertion en masked array
        labeled_array = ma.asarray(labeled_array)
        labeled_array.mask = np.zeros(labeled_array.shape, dtype=bool)
        # application du masque
        labeled_array.mask[:,:] = self.array.mask[:,:]

        longueur = []
        labeled_array[labeled_array.mask] = 0

        longueur = list(sum_labels(np.ones(labeled_array.shape, dtype=np.int32), labeled_array, range(1, num_features+1)))
        longueur = [[longueur[j], j+1] for j in range(0, num_features)]
        # longueur = [[np.sum(labeled_array[labeled_array == j]) // j, j] for j in range(1, num_features+1)]
        longueur.sort(key=lambda x: x[0], reverse=True)

        self.array.mask[:,:] = True
        for j in range(0, n_largest):
            self.array.mask[labeled_array == longueur[j][1]] = False

        self.set_nullvalue_in_mask()

        if reset_plot:
            self.reset_plot()

    def filter_zone(self, set_null:bool = False, reset_plot:bool = True):
        """
        Filtre des zones et conservation de celles pour lesquelles des
        mailles sont sélectionnées

        """

        if self.SelectionData.nb == 0:
            logging.info(_('No selection -- no filtering'))
            return

        if self.SelectionData.myselection == ALL_SELECTED:
            logging.info(_('All nodes selected -- no filtering'))
            return

        # labellisation
        labeled_array = self.array.data.copy()
        labeled_array[np.where(self.array.mask)] = 0

        labeled_array, num_features = label(labeled_array)

        # récupération des zones utiles
        vals_ij = [self.get_ij_from_xy(cur[0], cur[1]) for cur in self.SelectionData.myselection]
        vals = list(set([labeled_array[int(cur[0]), int(cur[1])] for cur in vals_ij]))

        self.array.mask[:,:] = True

        for j in vals:
            self.array.mask[labeled_array == j] = False

        if set_null:
            self.set_nullvalue_in_mask()

        if reset_plot:
            self.reset_plot()

    def clean_small_patches(self, min_size:int = 1, set_null:bool = False, reset_plot:bool = True):
        """ Clean small patches in the array """

        if min_size < 1:
            logging.error(_('Minimum size must be greater than 1'))
            return

        # labellisation
        labeled_array = self.array.data.copy()
        labeled_array[np.where(self.array.mask)] = 0

        labeled_array, num_features = label(labeled_array,)

        # count the number of elements in each patch
        patch_size = np.bincount(labeled_array.ravel())

        # mask the small patches
        mask_small_patches = patch_size < min_size
        labeled_array[mask_small_patches[labeled_array]] = 0

        # mask data in the array based on the labeled array
        self.array.mask[labeled_array == 0] = True

        if set_null:
            self.set_nullvalue_in_mask()

        if reset_plot:
            self.reset_plot()

    def labelling(self, reset_plot:bool = True):
        """
        Labelling of the array using Scipy

        """

        # labellisation
        labeled_array = self.array.data.copy()
        labeled_array[np.where(self.array.mask)] = 0

        labeled_array, num_features = label(labeled_array)

        self.array.data[:,:] = labeled_array[:,:].astype(self.dtype)

        if reset_plot:
            self.reset_plot()

    def statistics(self, inside_polygon:vector | Polygon | np.ndarray = None) -> dict[str, float | np.ndarray]:
        """
        Statistics on Selected data or the whole array if no selection

        :param inside_polygon: vector or Polygon to select data inside the polygon
        :return: mean, std, median, sum, volume (sum*dx*dy), values
        :rtype: dict[str, float | np.ndarray]

        Translated Keys are:
            - _('Mean'): mean value of the selected data
            - _('Std'): standard deviation of the selected data
            - _('Median'): median value of the selected data
            - _('Sum'): sum of the selected data
            - _('Volume'): volume of the selected data (sum * dx * dy)
            - _('Values'): values of the selected data as a numpy array
        """

        if inside_polygon is not None:
            if isinstance(inside_polygon, vector | Polygon):
                ij = self.get_ij_inside_polygon(inside_polygon)
            elif isinstance(inside_polygon, np.ndarray):
                if inside_polygon.ndim == 2 and inside_polygon.shape[1] == 2:
                    ij = self.get_ij_from_xy_array(inside_polygon)
                else:
                    logging.error(_('Invalid shape for inside_polygon numpy array'))
                    return {}

            vals = self.array[ij[:,0], ij[:,1]]

        elif self.SelectionData.nb == 0 or self.SelectionData.myselection == ALL_SELECTED:
            logging.info(_('No selection -- statistics on the whole array'))
            vals = self.array[~self.array.mask].ravel().data	# all values

        else:
            vals = self.SelectionData.get_values_sel()

        mean = np.ma.mean(vals)
        std = np.ma.std(vals)
        median = np.ma.median(vals)
        sum = np.ma.sum(vals)
        vol = sum * self.dx * self.dy

        return {_('Mean'): mean, _('Std'): std, _('Median'): median, _('Sum'): sum, _('Volume'): vol, _('Values'): vals}

    def export_geotif(self, outdir:str= '', extent:str= '', EPSG:int = None):
        """
        Export de la matrice au format Geotiff

        Pour sauvegarder l'objet au format Geotiff, il est recommandé d'utiliser
        la fonction write_all plutôt que celle-ci directement.

        Formats supportés :
            - Int32
            - Int16
            - Int8
            - Byte
            - Float32
            - Float64

        :param outdir: directory - If provided, the file will be savd as "outdir/idx+extent.tif"
                                   If not provided, we use the filename attribute

        :param extent: suffix to add to the filename before the extension '.tif' (only if outdir is provided)
        :param EPSG: EPSG code, by default 31370 (Lambert 72)
        """

        if EPSG is None and self.epsg is None:
            EPSG = 31370 # Default EPSG code is Belgian Lambert 72
        elif EPSG is None:
            EPSG = self.epsg

        outdir = str(outdir)
        extent = str(extent)

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(EPSG)

        if outdir=='' and extent=='':
            filename = self.filename
        else:
            filename = join(outdir,self.idx)+extent+'.tif'

        arr=self.array
        if arr.dtype == np.float32:
            arr_type = gdal.GDT_Float32
            nullvalue = self.nullvalue
        elif arr.dtype == np.float64:
            arr_type = gdal.GDT_Float64
            nullvalue = self.nullvalue
        elif arr.dtype == np.int8:
            arr_type = gdal.GDT_Byte
            nullvalue = int(self.nullvalue)
        elif arr.dtype == np.int16:
            arr_type = gdal.GDT_Int16
            nullvalue = int(self.nullvalue)
        elif arr.dtype == np.uint8:
            arr_type = gdal.GDT_Byte
            nullvalue = int(self.nullvalue)
        else:
            arr_type = gdal.GDT_Int32
            nullvalue = int(self.nullvalue)

        driver: gdal.Driver
        out_ds: gdal.Dataset
        band: gdal.Band
        driver = gdal.GetDriverByName("GTiff")
        # bytes_per_pixel = arr.data.dtype.itemsize
        estimated_file_size = self.memory_usage #arr.shape[0] * arr.shape[1] * bytes_per_pixel

        # Check if estimated file size exceeds 4GB
        if (estimated_file_size > 4 * 1024**3):  # 4GB in bytes
            options = ['COMPRESS=LZW', 'BIGTIFF=YES']
            logging.info('BigTIFF format will be used!')
        else:
            options = ['COMPRESS=LZW']

        out_ds = driver.Create(str(filename), arr.shape[0], arr.shape[1], 1, arr_type, options=options)

        if out_ds is None:
            logging.error(_('Could not create the file {filename}'))
            return

        out_ds.SetProjection(srs.ExportToWkt())


        # On utilise le coin supérieur gauche de la matrice et la taille des pixels selon y est négative
        # !! gdalBuiltvrt ne supporte que cette convention !!
        out_ds.SetGeoTransform([self.origx+self.translx,
                                self.dx,
                                0.,
                                self.origy+self.transly+float(self.nby)*self.dy,
                                0.,
                                -self.dy])

        band = out_ds.GetRasterBand(1)
        band.SetNoDataValue(nullvalue)
        band.WriteArray(np.flipud(arr.data.transpose()))
        band.FlushCache()
        try:
            band.ComputeStatistics(True)
        except RuntimeError as e:
            # If the array is mainly composed of null values, ComputeStatistics(True) will fail because ComputeStatistics(True) takes a subset of the data to compute statistics (and it may only find null values resulting to an error while in the array, it is not the case)
            try:
                band.ComputeStatistics(0)  # Using 0 for exact stats instead of True (which implies approximate)
            except RuntimeError as e:
                print("Warning: ComputeStatistics failed:", e)



    def get_dxdy_min(self):
        """
        Return the minimal size

        Mainly useful in PyVertexVectors to get the minimal size of the cells
        and ensure compatibility with the 2D results (GPU and Multiblocks)
        """
        return min(self.dx, self.dy)

    def get_dxdy_max(self):
        """
        Return the maximal size

        Mainly useful in PyVertexVectors to get the minimal size of the cells
        and ensure compatibility with the 2D results (GPU and Multiblocks)
        """
        return max(self.dx, self.dy)

    def _import_npy(self, fn:str='', crop:list[float]=None):
        """
        Import a numpy file.

        Must be called after the header is initialized, e.g. read_txt_header.

        :param fn: filename
        :param crop: crop the data - [xmin, xmax, ymin, ymax]
        """

        if fn !='':
            pass
        elif self.filename !='':
            fn = self.filename
        else:
            return

        # Numpy format
        locarray = np.load(self.filename)

        assert locarray.shape[0] == self.nbx, _('Incompatible dimensions')
        assert locarray.shape[1] == self.nby, _('Incompatible dimensions')

        if crop is not None :
            # logging.error(_('Cropping not yet implemented for numpy files'))

            imin, jmin = self.get_ij_from_xy(crop[0][0], crop[1][0])
            imax, jmax = self.get_ij_from_xy(crop[0][1], crop[1][1])

            imin = int(imin)
            jmin = int(jmin)
            imax = int(imax)
            jmax = int(jmax)

            self.nbx = imax - imin
            self.nby = jmax - jmin
            self.dx  = self.dx
            self.dy  = self.dy
            self.origx, self.origy = self.get_xy_from_ij(imin, jmin)
            self.origx -= self.dx / 2.
            self.origy -= self.dy / 2.
            self.translx = self.translx
            self.transly = self.transly

            locarray = locarray[imin:imax, jmin:jmax]

        self.array = np.ma.asarray(locarray)

    def import_vrt(self, fn:str='', which:int = None, crop:list[float]=None):
        """ Import a VRT file.

        A Virtual Raster Tile (VRT) is an XML-based format used by GDAL to describe
        a raster dataset. It allows users to create virtual datasets that reference
        other raster files without duplicating the actual data. VRT files can be used
        to mosaic multiple raster files, apply transformations, or define custom
        raster structures.

        :param fn: filename
        :param which: band to import
        :param crop: crop the data - [xmin, xmax, ymin, ymax]
        """

        if fn !='':
            pass
        elif self.filename !='':
            fn = self.filename
        else:
            return

        if not os.path.exists(fn):
            logging.error(_('File not found'))
            return

        # convert vrt to tif and mport tif
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpfile = join(tmpdirname, 'tmp.tif')

            if crop is not None:

                tmpdx = self.dx

                fn_crop = fn + '_crop.tif'
                if type(crop) is np.ndarray:
                    if crop.shape == (4,):
                        logging.error(_('Crop must be a list or a numpy array with 4 values - [[xmin, xmax], [ymin, ymax]]'))
                        crop = [[crop[0], crop[1]], [crop[2], crop[3]]]
                elif isinstance(crop, list | tuple):
                    if len(crop) == 4:
                        logging.error(_('Crop must be a list or a numpy array with 4 values - [[xmin, xmax], [ymin, ymax]]'))
                        crop = [[crop[0], crop[1]], [crop[2], crop[3]]]
                else:
                    if not self.wx_exists:
                        logging.error(_('WX App is required to display the UI'))
                        return

                    raster_in:gdal.Dataset
                    raster_in = gdal.Open(fn)

                    proj = raster_in.GetProjection()

                    geotr = raster_in.GetGeoTransform()
                    self.dx = geotr[1]
                    self.dy = abs(geotr[5])

                    ulx = geotr[0]
                    uly = geotr[3]
                    llx = ulx + geotr[1] * raster_in.RasterXSize
                    lly = uly + geotr[5] * raster_in.RasterYSize

                    newcrop = CropDialog(None, self.get_mapviewer())

                    if self.wx_exists:
                        bounds = self.mapviewer.get_canvas_bounds()

                        newcrop.dx.Value = str(self.dx)
                        newcrop.dy.Value = str(self.dy)

                        newcrop.dx.Enable(False)
                        newcrop.dy.Enable(False)

                        newcrop.ox.Value = str(float((bounds[0] // 50.) * 50.))
                        newcrop.ex.Value = str(float((bounds[2] // 50.) * 50.))
                        newcrop.oy.Value = str(float((bounds[1] // 50.) * 50.))
                        newcrop.ey.Value = str(float((bounds[3] // 50.) * 50.))

                    badvalues = True
                    while badvalues:
                        badvalues = False

                        ret = newcrop.ShowModal()
                        if ret == wx.ID_CANCEL:
                            newcrop.Destroy()
                            return
                        else:
                            crop = [[float(newcrop.ox.Value), float(newcrop.ex.Value)],
                                    [float(newcrop.oy.Value), float(newcrop.ey.Value)]]

                            tmpdx = float(newcrop.dx.Value)
                            tmpdy = float(newcrop.dy.Value)

                        if self.dx != tmpdx or self.dy != tmpdy:
                            if tmpdx / self.dx != tmpdy / self.dy:
                                badvalues = True

                    newcrop.Destroy()

                [xmin, xmax], [ymin, ymax] = crop

                gdal.Translate(tmpfile, fn, projWin=[xmin, ymax, xmax, ymin])
            else:
                gdal.Translate(tmpfile, fn)

            self.import_geotif(tmpfile, which)

    def import_geotif(self, fn:str='', which:int = None, crop:list[float]=None):
        """
        Import Geotiff Raster file.

        A Geotiff (Geographic Tagged Image File Format) is a widely used raster file format
        that embeds geographic metadata within the TIFF file structure. It allows for the storage
        of georeferencing information, such as coordinate systems, map projections, and spatial
        extents, alongside the raster image data. This makes Geotiff files suitable for use in
        Geographic Information Systems (GIS) and remote sensing applications.

        Formats supportés :
            - Int8
            - Int16
            - Int32
            - Float32
            - Float64
            - uInt8 but will be convert as signed Int8

        :param fn: filename
        :param which: band to import
        :param crop: crop the data - [xmin, xmax, ymin, ymax] or [[xmin, xmax], [ymin, ymax]]
        """
        # from osgeo import gdal, osr, gdalconst

        if fn !='':
            pass
        elif self.filename !='':
            fn = self.filename
        else:
            logging.error(_('No filename provided in import_geotif'))
            return

        need_wx = False

        raster:gdal.Dataset
        if crop is not None :
            if not os.path.exists(fn):
                logging.error(_('File not found'))
                return

            tmpdx = self.dx

            fn_crop = fn + '_crop.tif'

            raster_in:gdal.Dataset
            raster_in = gdal.Open(fn)

            geotr = raster_in.GetGeoTransform()
            self.dx = geotr[1]
            self.dy = abs(geotr[5])

            ulx = geotr[0]
            uly = geotr[3]
            llx = ulx + geotr[1] * raster_in.RasterXSize
            lly = uly + geotr[5] * raster_in.RasterYSize

            if type(crop) is np.ndarray:
                if crop.shape == (4,):
                    pass
                elif crop.shape == (2,2):
                    crop = [crop[0][0], crop[0][1], crop[1][0], crop[1][1]]
                else:
                    logging.error(_('Crop must be a list or a numpy array with 4 values - xmin, xmax, ymin, ymax'))
            elif type(crop) in [list, tuple]:
                if len(crop) == 2:
                    if len(crop[0]) == 2 and len(crop[1]) == 2:
                        crop = [crop[0][0], crop[0][1], crop[1][0], crop[1][1]]
                    else:
                        logging.error(_('Crop must be a list or a numpy array with 4 values - xmin, xmax, ymin, ymax'))
                        return
                elif len(crop) ==4:
                    pass
            else:
                if not self.wx_exists:
                    logging.error(_('Crop must be a list or a numpy array with 4 values - xmin, xmax, ymin, ymax'))
                    return

                need_wx = True

                newcrop = CropDialog(None, self.get_mapviewer())

                if self.wx_exists:
                    bounds = self.mapviewer.get_canvas_bounds()

                    newcrop.dx.Value = str(self.dx)
                    newcrop.dy.Value = str(self.dy)

                    newcrop.dx.Enable(False)
                    newcrop.dy.Enable(False)

                    newcrop.ox.Value = str(float((bounds[0] // 50.) * 50.))
                    newcrop.ex.Value = str(float((bounds[2] // 50.) * 50.))
                    newcrop.oy.Value = str(float((bounds[1] // 50.) * 50.))
                    newcrop.ey.Value = str(float((bounds[3] // 50.) * 50.))

                badvalues = True
                while badvalues:
                    badvalues = False

                    ret = newcrop.ShowModal()
                    if ret == wx.ID_CANCEL:
                        newcrop.Destroy()
                        return
                    else:
                        crop = [float(newcrop.ox.Value), float(newcrop.ex.Value),
                                float(newcrop.oy.Value), float(newcrop.ey.Value)]

                        tmpdx = float(newcrop.dx.Value)
                        tmpdy = float(newcrop.dy.Value)

                    if self.dx != tmpdx or self.dy != tmpdy:
                        if tmpdx / self.dx != tmpdy / self.dy:
                            badvalues = True

                newcrop.Destroy()

            xmin, xmax, ymin, ymax = crop

            if need_wx:

                with wx.FileDialog(None, _('Save the cropped file for later'), wildcard="Tiff files (*.tif)|*.tif",
                                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        from tempfile import NamedTemporaryFile
                        tmpfile = str(NamedTemporaryFile(suffix='.tif').name)
                    else:
                        fn_crop = fileDialog.GetPath()

                if uly > lly:
                    raster = gdal.Translate(fn_crop, fn, projWin=[xmin, ymax, xmax, ymin])
                else:
                    raster = gdal.Translate(fn_crop, fn, projWin=[xmin, ymin, xmax, ymax])

                fn  = fn_crop
            else:
                fn_tmp = '__tmp_wolf.tif'

                if uly > lly:
                    raster = gdal.Translate(fn_tmp, fn, projWin=[xmin, ymax, xmax, ymin])
                else:
                    raster = gdal.Translate(fn_tmp, fn, projWin=[xmin, ymin, xmax, ymax])
                fn = fn_tmp
        else:
            raster = gdal.Open(fn)


        if raster is None:
            logging.error(_('Could not open the file {fn}'))
            return

        # Dimensions
        self.nbx = raster.RasterXSize
        self.nby = raster.RasterYSize

        # Number of bands
        nb = raster.RasterCount

        if which is None:

            names = [raster.GetRasterBand(which+1).GetDescription() for which in range(nb)]

            if nb>1:
                if self.wx_exists :
                    dlg = wx.SingleChoiceDialog(None,
                                                _('Which band?'),
                                                _('Band choice'),
                                                names)
                    ret = dlg.ShowModal()

                    if ret == wx.ID_CANCEL:
                        dlg.Destroy()
                        return

                    which = dlg.GetSelection()+1
                    dlg.Destroy()
                else:
                    which =1
            else:
                which=1
        else:
            if which > nb:
                which = nb
            if which < 1:
                which = 1

        # Metadata for the raster dataset
        # meta = raster.GetMetadata()

        # Read the raster band as separate variable
        band = raster.GetRasterBand(which)

        # Data type of the values
        self.nullvalue = band.GetNoDataValue()
        if self.nullvalue is None:
            self.nullvalue = 0.

        geotr = raster.GetGeoTransform()
        self.origx = geotr[0]

        self.dx = geotr[1]
        self.dy = abs(geotr[5])

        try:
            if geotr[5] <0.:
                self.origy = geotr[3]+geotr[5]*self.nby
                tmp_array = np.transpose(np.flipud(band.ReadAsArray()))
            else:
                self.origy = geotr[3]
                tmp_array = np.transpose(band.ReadAsArray())

            self.array = np.ma.asarray(tmp_array.copy())

            assert self.array.iscontiguous(), _('Array is not contiguous')

            del tmp_array

            if self.array.dtype == np.float64:
                self.wolftype = WOLF_ARRAY_FULL_DOUBLE
            elif self.array.dtype == np.float32:
                self.wolftype = WOLF_ARRAY_FULL_SINGLE
            elif self.array.dtype == np.int32:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER
            elif self.array.dtype == np.uint8:
                logging.warning(_('***************************************************'))
                logging.warning(_(' Conversion of uint8 to int8'))
                logging.warning(_(' If you save this file, it will be converted to int8'))
                logging.warning(_('***************************************************'))
                self.array = self.array.astype(np.int8)
                self.wolftype = WOLF_ARRAY_FULL_INTEGER8
            elif self.array.dtype == np.int8:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER8
            elif self.array.dtype == np.int16:
                self.wolftype = WOLF_ARRAY_FULL_INTEGER16

        except:
            logging.warning(_('Error during importing tif file'))

        # Find the EPSG code
        proj = raster.GetProjection()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(proj)
        if srs.IsProjected:
            self.epsg = int(srs.GetAttrValue('AUTHORITY',1))

            if "EPSG:" in proj:
                try:
                    idx1 = proj.index("EPSG:")
                    idx2 = proj.index('"', idx1)
                    epsg2 = int(proj[idx1+5:idx2])
                    if epsg2 != self.epsg:
                        logging.warning(_('Mismatch in EPSG code detection: {} and {}').format(self.epsg, epsg2))
                        logging.warning(_("Check your file's projection -- You can use gdalinfo command line tool"))
                        self.epsg = epsg2
                        logging.warning(_('Using EPSG: {}').format(self.epsg))
                except:
                    logging.warning(_('Could not check EPSG code in the projection string'))
                    logging.warning(_("Check your file's projection -- You can use gdalinfo command line tool"))
        else:
            self.epsg = self.epsg_parent

        # Close the raster
        raster.FlushCache()
        raster = None

        try:
            if fn_tmp == '__tmp_wolf.tif':
                os.remove(fn_tmp)
        except:
            pass

    def add_ops_sel(self):
        """
        Adding selection manager and operations array

        - Ops_Array (GUI) if mapviewer is not None
        - create SelectionData (Selection manager) if None
        """

        if self.wx_exists and self.mapviewer is not None:
            self.myops = Ops_Array(self, self.mapviewer)
            self.myops.Hide()
        else:
            self.myops = None

        if self.mngselection is None:

            if self.nb_blocks>0:
                self.mngselection = SelectionDataMB(self)
            else:
                self.mngselection = SelectionData(self)

    def change_gui(self, newparentgui):
        """
        Move GUI to another instance

        :param newparentgui: WolfMapViewer instance
        """

        from .PyDraw import WolfMapViewer
        assert isinstance(newparentgui, WolfMapViewer), _('newparentgui must be a WolfMapViewer instance')

        self.wx_exists = wx.App.Get() is not None

        if self.mapviewer is None:
            self.mapviewer = newparentgui
            self.add_ops_sel()
        else:
            self.mapviewer = newparentgui
            if self.myops is not None:
                self.myops.mapviewer = newparentgui
            else:
                self.add_ops_sel()

    def compare_cloud(self, mycloud:cloud_vertices, delta:list[float] = [.15, .5, 1.]):
        """
        Graphique de comparaison des valeurs d'un nuage de points et des valeurs de la matrice sous les mêmes positions

        :param mycloud: cloud_vertices
        :param delta: list of tolerance for the comparison

        """

        # Get the values of the cloud
        xyz_cloud = mycloud.get_xyz()
        # Get values of the array at the same positions
        zarray = np.array([self.get_value(curxy[0],curxy[1]) for curxy in xyz_cloud])

        # count the number of points outside the array
        nbout = np.count_nonzero(zarray==-99999)

        # Get the values of the cloud that are not outside the array
        # Separate XY and Z values (cloud and array)
        #  - z values
        z_cloud = xyz_cloud[zarray!=-99999][:,2]
        #  - xy values
        xy_cloud = xyz_cloud[zarray!=-99999][:,:2]

        #  - array values
        zarray = zarray[zarray!=-99999]

        # concatenate all z values
        zall = np.concatenate([z_cloud,zarray])
        # find the min and max values
        zmin = np.min(zall)
        zmax = np.max(zall)

        # compute differences
        diffz = zarray-z_cloud
        # choose a colormap
        cmap = plt.cm.get_cmap('RdYlBu')
        mindiff = np.min(diffz)
        maxdiff = np.max(diffz)

        # Plot the differences [0] and the position [1]
        fig,ax = plt.subplots(2,1)
        ax[0].set_title(_('Comparison Z - ') + str(nbout) + _(' outside points on ') + str(len(xyz_cloud)))
        sc0 = ax[0].scatter(z_cloud,zarray,s=10,c=diffz,cmap = cmap, vmin=mindiff, vmax=maxdiff)
        ax[0].set_xlabel(_('Scatter values'))
        ax[0].set_ylabel(_('Array values'))
        ax[0].set_xlim([zmin,zmax])
        ax[0].set_ylim([zmin,zmax])

        ax[0].plot([zmin,zmax],[zmin,zmax], color='black')

        if delta is not None:
            if isinstance(delta, list):
                for idx, curdelta in enumerate(delta):
                    curdelta = abs(float(curdelta))
                    ax[0].plot([zmin,zmax],[zmin+delta,zmax+delta], 'k--', alpha=1.-1./(idx+1))
                    ax[0].plot([zmin,zmax],[zmin-delta,zmax-delta], 'k--', alpha=1.-1./(idx+1))

        ax[0].axis('equal')

        sc1 = ax[1].scatter(xy_cloud[:,0],xy_cloud[:,1],s=10,c=diffz,cmap = cmap, vmin=mindiff, vmax=maxdiff)
        fig.colorbar(sc1)
        ax[1].axis('equal')

        plt.show()

    def compare_tri(self,mytri:Triangulation):
        """ Graphique de comparaison des valeurs d'un nuage de points et des valeurs de la matrice sous les mêmes positions """
        xyz_cloud = mytri.pts
        zarray = np.array([self.get_value(curxy[0],curxy[1]) for curxy in xyz_cloud])

        nbout = np.count_nonzero(zarray==-99999)

        z_cloud = xyz_cloud[zarray!=-99999][:,2]
        xy_cloud = xyz_cloud[zarray!=-99999][:,:2]
        zarray = zarray[zarray!=-99999]

        zall = np.concatenate([z_cloud,zarray])
        zmin = np.min(zall)
        zmax = np.max(zall)

        diffz = zarray-z_cloud
        cmap = plt.cm.get_cmap('RdYlBu')
        mindiff = np.min(diffz)
        maxdiff = np.max(diffz)

        fig,ax = plt.subplots(2,1)
        ax[0].set_title(_('Comparison Z - ') + str(nbout) + _(' outside points on ') + str(len(xyz_cloud)))
        sc0 = ax[0].scatter(z_cloud,zarray,s=10,c=diffz,cmap = cmap, vmin=mindiff, vmax=maxdiff)
        ax[0].set_xlabel(_('Scatter values'))
        ax[0].set_ylabel(_('Array values'))
        ax[0].set_xlim([zmin,zmax])
        ax[0].set_ylim([zmin,zmax])
        ax[0].plot([zmin,zmax],[zmin,zmax])
        ax[0].axis('equal')

        sc1 = ax[1].scatter(xy_cloud[:,0],xy_cloud[:,1],s=10,c=diffz,cmap = cmap, vmin=mindiff, vmax=maxdiff)
        fig.colorbar(sc1)
        ax[1].axis('equal')

        plt.show()

    def interpolate_on_polygon(self, working_vector: vector,
                               method:Literal["nearest", "linear", "cubic"]="linear",
                               keep:Literal['all', 'below', 'above'] = 'all',
                               rescale:bool = False,
                               method_selection:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']="shapely_strict",
                               usemask:bool = True,
                               epsilon:float = 0.0):
        """
        Interpolation sous un polygone.

        L'interpolation a lieu :
          - uniquement dans les mailles sélectionnées si elles existent
          - dans les mailles contenues dans le polygone sinon

        On utilise ensuite "griddata" de Scipy pour interpoler les altitudes des mailles
        depuis les vertices 3D du polygone.

        :ATTENTION: l'interpolation est réalisée en réels flottants 64 bits. Le résultat sera ensuite transformé dans le type de la matrice.

        :param working_vector: vector - polygon with z values
        :param method: interpolation method - 'nearest', 'linear' or 'cubic'
        :param keep: 'all' to keep all interpolated values
                     'below' to keep only values below the current value in the array
                     'above' to keep only values above the current value in the array
        :param rescale: rescale the input data to [0, 1] for better numerical stability (only for 'linear' and 'cubic' methods)
        :return: None
        """

        if self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_INTEGER16]:
            logging.info(_('Your array contains integer data. The interpolation will be done in float and then converted to integer using "np.ceil" operator.'))

        if vector.area == 0.:
            logging.error(_('The polygon has no area'))
            return

        if keep not in ['all', 'below', 'above']:
            logging.error(_('keep must be "all", "below" or "above"'))
            raise ValueError

        if method not in ['nearest', 'linear', 'cubic']:
            logging.error(_('method must be "nearest", "linear" or "cubic"'))
            raise ValueError

        if self.mngselection is None:
            destxy = self.get_xy_inside_polygon(working_vector, method = method_selection, usemask = usemask, epsilon = epsilon)
            if len(destxy)==0:
                logging.debug(_('No points to interpolate'))
                return

            destij = self.xy2ij_np(destxy)

        elif self.mngselection.myselection == 'all':
            destij = np.where(self.array.mask == False)
            destij = np.array(destij).transpose()

            if len(destij)==0:
                logging.debug(_('No points to interpolate'))
                return

            destxy = self.ij2xy_np(destij)
        else:
            if self.SelectionData.nb == 0:
                destxy = self.get_xy_inside_polygon(working_vector, method= method_selection, usemask= usemask, epsilon= epsilon)
                if destxy.shape[0] == 0:
                    logging.debug(_('No points to interpolate'))
                    return
            else:
                destxy = self.SelectionData.myselection

                if len(destxy)==0:
                    logging.debug(_('No points to interpolate'))
                    return

            destij = self.xy2ij_np(destxy)

        xyz = working_vector.asnparray3d()

        newvalues = griddata(xyz[:, :2], xyz[:, 2], destxy, method=method, fill_value=-99999., rescale = rescale)

        if keep == 'all':
            locmask = np.where(newvalues != -99999.)
        elif keep == 'below':
            locmask = np.where((newvalues != -99999.) & (newvalues < self.array.data[destij[:, 0], destij[:, 1]]))
        elif keep == 'above':
            locmask = np.where((newvalues != -99999.) & (newvalues > self.array.data[destij[:, 0], destij[:, 1]]))

        if self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_INTEGER16]:
            logging.debug(_('Converting interpolated values to integer using "np.ceil" operator'))
            newvalues = np.ceil(newvalues)
            newvalues = newvalues.astype(self.array.dtype)

        self.array.data[destij[locmask][:, 0], destij[locmask][:, 1]] = newvalues[locmask]

    def rasterize_vector_valuebyid(self, working_vector: vector,
                                   id,
                                   method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']="shapely_strict",
                                   usemask:bool = True,
                                   epsilon:float = 0.0):
        """
        Rasterize a vector using the value of the id
        """

        if not isinstance(working_vector, vector):
            logging.error(_('working_vector must be a vector. You provided a {}').format(type(working_vector)))
            return

        if working_vector.get_value(id) is None:
            logging.error(_('No value for id {}').format(id))
            return

        val = working_vector.get_value(id)
        if val is None:
            logging.error(_('No value for id {}').format(id))
            return

        self.fillin_vector_with_value(working_vector, val, method=method, usemask=usemask, epsilon=epsilon)

    def fillin_vector_with_value(self, working_vector: vector,
                                 value: int | float | str,
                                 method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']="shapely_strict",
                                 usemask:bool = True,
                                 epsilon:float = 0.0):
        """
        Fill in a vector using the provided value

        :param working_vector: vector
        :param value: value to fill in (float or int depending on the array type)
        :param method: method to get points inside the polygon
                       - 'mpl' : matplotlib.path.Path.contains_points (fast for simple polygons)
                       - 'shapely_strict' : shapely contains (strictly inside the polygon)
                       - 'shapely_wboundary' : shapely contains or on the boundary (inside or on the polygon)
                       - 'rasterio' : rasterio.features.rasterize (fast for complex polygons with holes)
        :param usemask: if True, only fill in the masked points
        :param epsilon: tolerance for shapely methods (to consider points on the boundary)
        """

        if not isinstance(working_vector, vector):
            logging.error(_('working_vector must be a vector. You provided a {}').format(type(working_vector)))
            return

        try:
            if self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_INTEGER16]:
                val = int(float(value))
            else:
                val = float(value)
        except:
            logging.error(_('Value {} is not a number').format(value))
            return

        ij = self.get_ij_inside_polygon(working_vector, method = method, usemask = usemask, eps = epsilon)
        if len(ij) == 0:
            logging.debug(_('No points to rasterize'))
            return
        self.array.data[ij[:, 0], ij[:, 1]] = val

    def fillin_zone_with_value(self,
                               working_zone: zone,
                               value,
                               method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']="shapely_strict",
                               usemask:bool = True,
                               epsilon:float = 0.0):
        """
        Fill in a zone using the provided value
        """
        if not isinstance(working_zone, zone):
            logging.error(_('working_zone must be a zone. You provided a {}').format(type(working_zone)))
            return
        for curvec in working_zone.myvectors:
            self.fillin_vector_with_value(curvec, value, method, usemask, epsilon)

    def fillin_zones_with_value(self,
                                working_zones: Zones,
                                value,
                                method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']="shapely_strict",
                                usemask:bool = True,
                                epsilon:float = 0.0):
        """
        Fill in zones using the provided value
        """
        if not isinstance(working_zones, Zones):
            logging.error(_('working_zones must be a Zones. You provided a {}').format(type(working_zones)))
            return
        for curzone in working_zones.myzones:
            self.fillin_zone_with_value(curzone, value, method, usemask, epsilon)

    def rasterize_zone_valuebyid(self,
                                 working_zone: zone,
                                 id,
                                 method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']="shapely_strict",
                                 usemask:bool = True,
                                 epsilon:float = 0.0):
        """
        Rasterize a zone using the value of the id
        """

        if not isinstance(working_zone, zone):
            logging.error(_('working_zone must be a zone. You provided a {}').format(type(working_zone)))
            return

        for curvec in working_zone.myvectors:
            self.rasterize_vector_valuebyid(curvec, id, method, usemask, epsilon)

    def rasterize_zones_valuebyid(self,
                                  working_zones: Zones,
                                  id,
                                  method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']="shapely_strict",
                                  usemask:bool = True,
                                  epsilon:float = 0.0):
        """
        Rasterize a zone using the value of the id
        """

        if not isinstance(working_zones, Zones):
            logging.error(_('working_zone must be a zone. You provided a {}').format(type(working_zones)))
            return

        for curzone in working_zones.myzones:
            self.rasterize_zone_valuebyid(curzone, id, method, usemask, epsilon)

    def interpolate_on_polygons(self, working_zone:zone,
                                method:Literal["nearest", "linear", "cubic"]="linear",
                                keep:Literal['all', 'below', 'above'] = 'all'):
        """
        Interpolation sous plusieurs polygones d'une même zone

        """

        for curvec in working_zone.myvectors:
            self.interpolate_on_polygon(curvec, method, keep)

    def interpolate_strictly_on_polyline(self, working_vector:vector, usemask=True, keep:Literal['all', 'below', 'above'] = 'all'):
        """
        Interpolation des mailles strictement sous une polyligne.

        On utilise ensuite "interpolate" de shapely pour interpoler les altitudes des mailles
        depuis les vertices 3D de la polyligne
        """

        vecls = working_vector.linestring
        xy = self.get_xy_strictly_on_borders(working_vector, usemask=usemask)
        if xy.shape[0] == 0:
            logging.debug(_('No points to interpolate'))
            return
        ij = np.asarray([self.get_ij_from_xy(x, y) for x, y in xy])
        newz = np.asarray([vecls.interpolate(vecls.project(Point(x, y))).z for x, y in xy])

        if keep == 'all':
            self.array.data[ij[:, 0], ij[:, 1]] = newz
        elif keep == 'below':
            locmask = np.where((newz != -99999.) & (newz < self.array.data[ij[:, 0], ij[:, 1]]))
            self.array.data[ij[locmask][:, 0], ij[locmask][:, 1]] = newz[locmask]
        elif keep == 'above':
            locmask = np.where((newz != -99999.) & (newz > self.array.data[ij[:, 0], ij[:, 1]]))
            self.array.data[ij[locmask][:, 0], ij[locmask][:, 1]] = newz[locmask]

    def interpolate_strictly_on_vertices(self, working_vector:vector, usemask=True, keep:Literal['all', 'below', 'above'] = 'all'):
        """
        Interpolation des mailles strictement sous une polyligne.

        On utilise ensuite "interpolate" de shapely pour interpoler les altitudes des mailles
        depuis les vertices 3D de la polyligne
        """

        vecls = working_vector.linestring
        xy = self.get_xy_strictly_on_vertices(working_vector, usemask=usemask)
        if xy.shape[0] == 0:
            logging.debug(_('No points to interpolate'))
            return
        ij = np.asarray([self.get_ij_from_xy(x, y) for x, y in xy])
        newz = np.asarray([vecls.interpolate(vecls.project(Point(x, y))).z for x, y in xy])

        if keep == 'all':
            self.array.data[ij[:, 0], ij[:, 1]] = newz
        elif keep == 'below':
            locmask = np.where((newz != -99999.) & (newz < self.array.data[ij[:, 0], ij[:, 1]]))
            self.array.data[ij[locmask][:, 0], ij[locmask][:, 1]] = newz[locmask]
        elif keep == 'above':
            locmask = np.where((newz != -99999.) & (newz > self.array.data[ij[:, 0], ij[:, 1]]))
            self.array.data[ij[locmask][:, 0], ij[locmask][:, 1]] = newz[locmask]

    def interpolate_on_polyline(self, working_vector:vector, usemask=True):
        """
        Interpolation sous une polyligne

        L'interpolation a lieu :
          - uniquement dans les mailles sélectionnées si elles existent
          - dans les mailles sous la polyligne sinon

        On utilise ensuite "interpolate" de shapely pour interpoler les altitudes des mailles
        depuis les vertices 3D de la polyligne
        """

        vecls = working_vector.asshapely_ls()

        if self.SelectionData is None:
            allij = self.get_ij_under_polyline(working_vector, usemask)
            allxy = [self.get_xy_from_ij(cur[0], cur[1]) for cur in allij]
        else:
            if self.SelectionData.nb == 0:
                allij = self.get_ij_under_polyline(working_vector, usemask)
                allxy = [self.get_xy_from_ij(cur[0], cur[1]) for cur in allij]
            else:
                allxy = self.SelectionData.myselection
                allij = np.asarray([self.get_ij_from_xy(x,y) for x,y in allxy])

        newz = np.asarray([vecls.interpolate(vecls.project(Point(x, y))).z for x, y in allxy])
        self.array.data[allij[:, 0], allij[:, 1]] = newz

    def interpolate_on_polylines(self, working_zone:zone, usemask=True):
        """ Interpolation sous toutes les polylignes d'une même zone """

        for curvec in working_zone.myvectors:
            self.interpolate_on_polyline(curvec, usemask)


    def interpolate_on_cloud(self, xy:np.ndarray, z:np.ndarray, method:Literal['linear', 'nearest', 'cubic']= 'linear'):
        """
        Interpolation sur un nuage de points.

        L'interpolation a lieu :
          - uniquement dans les mailles sélectionnées si elles existent
          - dans les mailles contenues dans le polygone convexe contenant les points sinon

        Using griddata from Scipy.

        :param xy: numpy.array of vertices - shape (n,2)
        :param z: numpy.array of values - shape (n,)
        :param method: method for the interpolation -- 'nearest', 'linear' or 'cubic'

        See : https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html
        """

        if self.mngselection.myselection == [] or self.mngselection.myselection == ALL_SELECTED:

            decalx = self.origx + self.translx
            decaly = self.origy + self.transly
            x = np.arange(self.dx / 2. + decalx, float(self.nbx) * self.dx + self.dx / 2 + decalx, self.dx)
            y = np.arange(self.dy / 2. + decaly, float(self.nby) * self.dy + self.dy / 2 + decaly, self.dy)
            grid_x, grid_y = np.meshgrid(x, y, sparse=True, indexing='xy')

            newvalues = griddata(xy, z, (grid_x, grid_y), method=method, fill_value=-99999.).transpose()
            self.array.data[np.where(newvalues != -99999.)] = newvalues[np.where(newvalues != -99999.)]

        else:
            ij = np.asarray([self.get_ij_from_xy(x, y) for x, y in self.mngselection.myselection])
            newvalues = griddata(xy, z, self.mngselection.myselection, method=method, fill_value=-99999.)

            ij = ij[np.where(newvalues != -99999.)]
            newvalues = newvalues[np.where(newvalues != -99999.)]
            self.array.data[ij[:, 0], ij[:, 1]] = newvalues

        self.reset_plot()

    def interpolate_on_triangulation(self, coords, triangles,
                                     grid_x=None, grid_y = None,
                                     mask_tri=None,
                                     interp_method:Literal['matplotlib','scipy'] = 'scipy',
                                     keep:Literal['all', 'below', 'above'] = 'all',
                                     points_along_edges:bool = True):
        """
        Interpolation sur une triangulation.

        L'interpolation a lieu :
          - uniquement dans les mailles sélectionnées si elles existent
          - dans les mailles contenues dans la triangulation sinon

        Scipy(griddata) is used by default (more robust), but Matplotlib can be used as well (more strict). If Matplotlib crashes, try with Scipy.

        **Matplotlib is more strict on the quality of the triangulation.**

        :param coords: numpy.array of vertices - shape (n,3)
        :param triangles: numpy.array of triangles - shape (m,3)
        :param grid_x: numpy.array of x values where the interpolation will be done -- if None, the grid is created from the array
        :param grid_y: numpy.array of y values where the interpolation will be done -- if None, the grid is created from the array
        :param mask_tri: numpy.array of mask for the triangles
        :param interp_method: method for the interpolation -- 'matplotlib' or 'scipy'
        :param keep: 'all' to keep all values, 'below' to keep only values below the current array, 'above' to keep only values above the current array

        For matplotlib algo, see : https://matplotlib.org/stable/gallery/images_contours_and_fields/triinterp_demo.html
        For scipy algo, see : https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html

        """


        if interp_method =='matplotlib':
            # FIXME : This part could be optimized, I think

            import matplotlib.tri as mtri

            use_scipy=False

            try:
                if self.mngselection is not None:
                    if self.mngselection.myselection != [] and self.mngselection.myselection != ALL_SELECTED:
                        # interpolation only in the selected cells

                        # Convert coordinates to indices
                        ij = np.asarray([self.get_ij_from_xy(x, y) for x, y in self.mngselection.myselection])

                        try:
                            # Opérateur d'interpolation linéaire
                            triang = mtri.Triangulation(coords[:,0],coords[:,1],triangles)
                            if mask_tri is not None:
                                triang.set_mask(mask_tri)
                            interplin = mtri.LinearTriInterpolator(triang, coords[:,2])            # Interpolation et récupération dans le numpy.array de l'objet Wolf
                        except:
                            raise Warning(_('Bad triangulation - try with another method like Scipy'))

                        newvalues = np.ma.masked_array([interplin(x, y) for x, y in self.mngselection.myselection])

                        if newvalues.mask.shape!=():
                            # We have a mask

                            nonmasked_values = np.where(~newvalues.mask)
                            ij = ij[nonmasked_values]
                            newvalues = newvalues[nonmasked_values]

                            if keep == 'below':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[np.where(~newvalues.mask)]
                                newvalues = newvalues[nonmasked_values]

                            elif keep == 'above':
                                newvalues = np.ma.masked_array(newvalues[nonmasked_values], mask=(newvalues[nonmasked_values] < self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[np.where(~newvalues.mask)]
                                newvalues = newvalues[nonmasked_values]

                            self.array.data[ij[:, 0], ij[:, 1]] = newvalues
                        else:
                            # No mask --> boolean

                            if keep == 'below':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[np.where(~newvalues.mask)]
                                newvalues = newvalues[nonmasked_values]

                            elif keep == 'above':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues < self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[np.where(~newvalues.mask)]
                                newvalues = newvalues[nonmasked_values]

                            self.array.data[ij[:, 0], ij[:, 1]] = newvalues

                    elif self.mngselection.myselection == ALL_SELECTED and (grid_x is None and grid_y is None):
                        # interpolation in all the cells

                        # Creating a grid for all cells
                        decalx = self.origx + self.translx
                        decaly = self.origy + self.transly
                        x = np.arange(self.dx / 2. + decalx, float(self.nbx) * self.dx + self.dx / 2 + decalx, self.dx)
                        y = np.arange(self.dy / 2. + decaly, float(self.nby) * self.dy + self.dy / 2 + decaly, self.dy)
                        grid_x, grid_y = np.meshgrid(x, y, indexing='ij')
                        grid_ij = self.xy2ij_np(np.concatenate([grid_x.ravel()[:, np.newaxis], grid_y.ravel()[:, np.newaxis]], axis=1))

                        try:
                            # Opérateur d'interpolation linéaire
                            triang = mtri.Triangulation(coords[:,0],coords[:,1],triangles)
                            if mask_tri is not None:
                                triang.set_mask(mask_tri)
                            interplin = mtri.LinearTriInterpolator(triang, coords[:,2])
                        except:
                            raise Warning(_('Bad triangulation - try with another method like Scipy'))

                        # Interpolation et récupération dans le numpy.array de l'objet Wolf
                        newvalues = interplin(grid_x,grid_y)

                        nonmasked_values = np.where(~newvalues.mask)
                        ij = grid_ij[nonmasked_values]
                        newvalues = newvalues[nonmasked_values]

                        if keep == 'below':
                            newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data[grid_ij[:, 0], grid_ij[:, 1]]))

                            nonmasked_values = np.where(~newvalues.mask)
                            ij = grid_ij[nonmasked_values]
                            newvalues = newvalues[nonmasked_values]

                        elif keep == 'above':
                            newvalues = np.ma.masked_array(newvalues, mask=(newvalues < self.array.data[grid_ij[:, 0], grid_ij[:, 1]]))

                            nonmasked_values = np.where(~newvalues.mask)
                            ij = grid_ij[nonmasked_values]
                            newvalues = newvalues[nonmasked_values]

                        self.array.data[ij[:, 0], ij[:, 1]] = newvalues

                    elif (grid_x is not None and grid_y is not None):
                        # Working on an imposed grid

                        # Opérateur d'interpolation linéaire
                        try:
                            triang = mtri.Triangulation(coords[:,0],coords[:,1],triangles)
                            if mask_tri is not None:
                                triang.set_mask(mask_tri)
                            interplin = mtri.LinearTriInterpolator(triang, coords[:,2])            # Interpolation et récupération dans le numpy.array de l'objet Wolf
                            newvalues = np.ma.masked_array([interplin(x, y) for x, y in zip(grid_x.ravel(),grid_y.ravel())])
                        except:
                            raise Warning(_('Bad triangulation - try with another method like Scipy'))

                        # newvalues is a vector of values

                        # ij is a vector of indices
                        ij = np.asarray([self.get_ij_from_xy(x, y) for x, y in zip(grid_x.ravel(),grid_y.ravel())])

                        if newvalues.mask.shape!=():

                            nonmasked_values = np.where(~newvalues.mask)
                            ij = ij[nonmasked_values]
                            newvalues = newvalues[nonmasked_values]

                            if keep == 'below':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[nonmasked_values]
                                newvalues = newvalues[nonmasked_values]

                            elif keep == 'above':

                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues < self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[nonmasked_values]
                                newvalues = newvalues[nonmasked_values]

                            self.array.data[ij[:, 0], ij[:, 1]] = newvalues
                        else:

                            if keep == 'below':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data[ij[:, 0], ij[:, 1]]))
                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[nonmasked_values]
                                newvalues = newvalues[nonmasked_values]
                            elif keep == 'above':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues < self.array.data[ij[:, 0], ij[:, 1]]))
                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[nonmasked_values]
                                newvalues = newvalues[nonmasked_values]

                            self.array.data[ij[:, 0], ij[:, 1]] = newvalues

                    else:
                        # Working on the whole array

                        # Creating a grid for all cells
                        decalx = self.origx + self.translx
                        decaly = self.origy + self.transly
                        x = np.arange(self.dx / 2. + decalx, float(self.nbx) * self.dx + self.dx / 2 + decalx, self.dx)
                        y = np.arange(self.dy / 2. + decaly, float(self.nby) * self.dy + self.dy / 2 + decaly, self.dy)
                        grid_x, grid_y = np.meshgrid(x, y, indexing='ij')

                        try:
                            # Opérateur d'interpolation linéaire
                            triang = mtri.Triangulation(coords[:,0],coords[:,1],triangles)
                            if mask_tri is not None:
                                triang.set_mask(mask_tri)
                            interplin = mtri.LinearTriInterpolator(triang, coords[:,2])
                            # Interpolation et récupération dans le numpy.array de l'objet Wolf

                            # newvalues is an array
                            newvalues = interplin(grid_x,grid_y).astype(np.float32)

                            assert newvalues.shape == (self.nbx, self.nby), _('Bad shape for newvalues')

                            if keep == 'below':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data))
                            elif keep == 'above':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues < self.array.data))

                            nonmasked_values = np.where(~newvalues.mask)

                            self.array.data[nonmasked_values] = newvalues[nonmasked_values]
                        except:
                            raise Warning(_('Bad triangulation - try with another method like Scipy'))
                else:
                    if grid_x is None and grid_y is None:

                        decalx = self.origx + self.translx
                        decaly = self.origy + self.transly
                        x = np.arange(self.dx / 2. + decalx, float(self.nbx) * self.dx + self.dx / 2 + decalx, self.dx)
                        y = np.arange(self.dy / 2. + decaly, float(self.nby) * self.dy + self.dy / 2 + decaly, self.dy)
                        grid_x, grid_y = np.meshgrid(x, y, indexing='ij')

                        # Opérateur d'interpolation linéaire
                        triang = mtri.Triangulation(coords[:,0],coords[:,1],triangles)
                        interplin = mtri.LinearTriInterpolator(triang, coords[:,2])
                        # Interpolation et récupération dans le numpy.array de l'objet Wolf
                        newvalues = np.ma.masked_array([interplin(x, y) for x, y in zip(grid_x.ravel(), grid_y.ravel())])
                        # newvalues = interplin(grid_x,grid_y).astype(np.float32)

                        nonmasked_values = np.where(~newvalues.mask)
                        grid_x = grid_x.ravel()[nonmasked_values]
                        grid_y = grid_y.ravel()[nonmasked_values]
                        newvalues = newvalues[nonmasked_values]

                        # make a shape (n, 2) from grid_x and grid_y
                        grid_x = grid_x[:, np.newaxis]
                        grid_y = grid_y[:, np.newaxis]
                        # concatenate grid_x and grid_y
                        grid_ij = self.xy2ij_np(np.concatenate([grid_x, grid_y], axis=1))

                        if keep == 'below':
                            newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data[grid_ij[:,0], grid_ij[:,1]]))

                            nonmasked_values = np.where(~newvalues.mask)
                            grid_ij = grid_ij[nonmasked_values]
                            newvalues = newvalues[nonmasked_values]

                        elif keep == 'above':
                            newvalues = np.ma.masked_array(newvalues, mask=(newvalues < self.array.data[grid_ij[:,0], grid_ij[:,1]]))

                            nonmasked_values = np.where(~newvalues.mask)
                            grid_ij = grid_ij[nonmasked_values]
                            newvalues = newvalues[nonmasked_values]

                        self.array.data[grid_ij[:,0], grid_ij[:,1]] = newvalues

                    else:
                        ij = np.asarray([self.get_ij_from_xy(x, y) for x, y in zip(grid_x.ravel(),grid_y.ravel())])

                        # Opérateur d'interpolation linéaire
                        triang = mtri.Triangulation(coords[:,0],coords[:,1],triangles)
                        interplin = mtri.LinearTriInterpolator(triang, coords[:,2])            # Interpolation et récupération dans le numpy.array de l'objet Wolf
                        newvalues = np.ma.masked_array([interplin(x, y) for x, y in zip(grid_x.ravel(), grid_y.ravel())])

                        if newvalues.mask.shape!=():
                            nonmasked_values = np.where(~newvalues.mask)
                            ij = ij[nonmasked_values]
                            newvalues = newvalues[nonmasked_values]

                            if keep == 'below':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[nonmasked_values]
                                newvalues = newvalues[nonmasked_values]

                            elif keep == 'above':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues < self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[nonmasked_values]
                                newvalues = newvalues[nonmasked_values]

                            self.array.data[ij[:, 0], ij[:, 1]] = newvalues
                        else:
                            if keep == 'below':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues > self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[nonmasked_values]
                                newvalues = newvalues[nonmasked_values]

                            elif keep == 'above':
                                newvalues = np.ma.masked_array(newvalues, mask=(newvalues < self.array.data[ij[:, 0], ij[:, 1]]))

                                nonmasked_values = np.where(~newvalues.mask)
                                ij = ij[nonmasked_values]
                                newvalues = newvalues[nonmasked_values]

                            self.array.data[ij[:, 0], ij[:, 1]] = newvalues

                #on force les valeurs masquées à nullvalue afin que l'interpolation n'applique pas ses effets dans cette zone
                self.array.data[self.array.mask]= self.nullvalue
            except:
                logging.error(_('Bad triangulation - We will try with Scipy'))
                use_scipy=True

        if interp_method != 'matplotlib' or use_scipy:
            # We need to convert the triangle to a vector to call the interpolation

            for curtri in triangles:
                curvec = vector(is2D=False)
                for curpt in curtri:
                    curvec.add_vertex(wolfvertex(coords[curpt,0], coords[curpt,1], coords[curpt,2]))
                curvec.close_force()

                # if bool(np.isnan(curvec.x).any() or np.isnan(curvec.y).any()):
                #     continue
                self.interpolate_on_polygon(curvec, "linear", keep)

                if points_along_edges:
                    # Test points along edges
                    self.interpolate_strictly_on_polyline(curvec, usemask=True, keep=keep)
                    # self.interpolate_strictly_on_vertices(curvec, usemask=True, keep=keep)

        self.reset_plot()
        return

    def import_from_gltf(self, fn:str='', fnpos:str='', interp_method:Literal['matplotlib','scipy'] = 'matplotlib'):
        """
        Import from GLTF/GLB format

        :param fn: filename
        :param fnpos: filename for the position's information
        :param interp_method: method for the interpolation -- 'matplotlib' or 'scipy'

        """
        #FIXME : add the possibility to use PyVista

        if fn == '' or fnpos == '':
            logging.info(_('Retry !! -- Bad files'))
            return

        if self.mapviewer is not None:
            if self.mapviewer.link_params is None:
                self.mapviewer.link_params = {}

            self.mapviewer.link_params['gltf file'] = fn
            self.mapviewer.link_params['gltf pos'] = fnpos

        mytri = Triangulation()
        mytri.import_from_gltf(fn)

        with open(fnpos, 'r') as f:
            mylines = f.read().splitlines()

            ox = float(mylines[0])
            oy = float(mylines[1])

            nbx = int(mylines[2])
            nby = int(mylines[3])

            i1 = int(mylines[4])
            j1 = int(mylines[5])
            i2 = int(mylines[6])
            j2 = int(mylines[7])

            xmin = float(mylines[8])
            xmax = float(mylines[9])
            ymin = float(mylines[10])
            ymax = float(mylines[11])
            try:
                znull = float(mylines[12])
            except:
                znull=-99999.

        x = np.arange(self.dx / 2. + ox, float(nbx) * self.dx + self.dx / 2 + ox, self.dx)
        y = np.arange(self.dy / 2. + oy, float(nby) * self.dy + self.dy / 2 + oy, self.dy)

        if interp_method =='matplotlib':
            grid_x, grid_y = np.meshgrid(x, y, indexing='ij')
            self.interpolate_on_triangulation(np.asarray(mytri.pts),mytri.tri, grid_x, grid_y, mytri.get_mask())
        else:
            grid_x, grid_y = np.meshgrid(x, y, sparse=True, indexing='xy')
            newvalues = griddata(np.asarray(mytri.pts)[:,0:2], np.asarray(mytri.pts)[:,2], (grid_x, grid_y), method='linear')
            locmask = np.logical_and(np.logical_not(self.array.mask[i1:i2, j1:j2]),
                                    np.logical_not(np.isnan(newvalues.transpose())))
            self.array.data[i1:i2, j1:j2][locmask] = newvalues.transpose()[locmask]

        self.reset_plot()

    def export_to_gltf(self, bounds:list[float]=None, fn:str=''):
        """
        Export to GLTF/GLB format

        :param bounds: [[xmin,xmax],[ymin,ymax]]
        :param fn: filename
        """

        mytri, znull = self.get_triangulation(bounds)
        mytri.export_to_gltf(fn)
        mytri.saveas(fn+'.tri')

        if bounds is None:
            ox = self.origx + self.translx
            oy = self.origy + self.transly
            nbx = self.nbx
            nby = self.nby
            i1 = 0
            i2 = self.nbx
            j1 = 0
            j2 = self.nby
            bounds = [[ox,ox+float(nbx)*self.dx],[oy,oy+float(nby)*self.dy]]

        else:
            ox = max(self.origx, bounds[0][0])
            oy = max(self.origy, bounds[1][0])

            i1, j1 = self.get_ij_from_xy(ox, oy)
            i2, j2 = self.get_ij_from_xy(bounds[0][1], bounds[1][1])

            i1 = max(i1, 0)
            j1 = max(j1, 0)
            i2 = min(i2 + 1, self.nbx)
            j2 = min(j2 + 1, self.nby)

            nbx = i2 - i1
            nby = j2 - j1

        with open(fn + '.pos', 'w') as f:
            f.write(str(ox) + '\n')
            f.write(str(oy) + '\n')
            f.write(str(nbx) + '\n')
            f.write(str(nby) + '\n')
            f.write(str(i1) + '\n')
            f.write(str(j1) + '\n')
            f.write(str(i2) + '\n')
            f.write(str(j2) + '\n')
            f.write(str(bounds[0][0]) + '\n')
            f.write(str(bounds[0][1]) + '\n')
            f.write(str(bounds[1][0]) + '\n')
            f.write(str(bounds[1][1]) + '\n')
            f.write(str(znull))

    def get_triangulation(self, bounds:list[float]=None):
        """
        Traingulation of the array

        :param bounds: [[xmin,xmax],[ymin,ymax]]
        """
        all = bounds is None
        if bounds is None:
            ox = self.origx + self.translx
            oy = self.origy + self.transly
            nbx = self.nbx
            nby = self.nby
            i1 = 0
            i2 = self.nbx
            j1 = 0
            j2 = self.nby

            bounds = [[ox,ox+float(nbx)*self.dx],[oy,oy+float(nby)*self.dy]]

        else:
            ox = max(self.origx, bounds[0][0])
            oy = max(self.origy, bounds[1][0])

            i1, j1 = self.get_ij_from_xy(ox, oy)
            i2, j2 = self.get_ij_from_xy(bounds[0][1], bounds[1][1])

            i1 = max(i1, 0)
            j1 = max(j1, 0)
            i2 = min(i2 + 1, self.nbx)
            j2 = min(j2 + 1, self.nby)

            nbx = i2 - i1
            nby = j2 - j1

        refx = ox
        refy = oy

        x = np.arange(self.dx / 2. + refx, float(nbx) * self.dx + self.dx / 2 + refx, self.dx)
        y = np.arange(self.dy / 2. + refy, float(nby) * self.dy + self.dy / 2 + refy, self.dy)

        znull = np.min(self.array[i1:i2, j1:j2])-1.

        if all:
            locarr = np.copy(self.array.data)
            locarr[self.array.mask] = znull
            points = np.meshgrid(x,y)
            points = np.concatenate((points[0].flatten(), points[1].flatten(),locarr.flatten())).reshape([3,len(x)*len(y)]).transpose()
        else:

            points = np.asarray(
                [[xx, yy, self.get_value(xx + ox - refx, yy + oy - refy, nullvalue=znull)] for xx in x for yy in y],
                dtype=np.float32)

        decal = 0
        triangles = []
        triangles.append([[i + decal, i + decal + 1, i + decal + nby] for i in range(nby - 1)])
        triangles.append([[i + decal + nby, i + decal + 1, i + decal + nby + 1] for i in range(nby - 1)])

        for k in tqdm(range(1, nbx - 1)):
            decal = k * nby
            triangles.append([[i + decal, i + decal + 1, i + decal + nby] for i in range(nby - 1)])
            triangles.append([[i + decal + nby, i + decal + 1, i + decal + nby + 1] for i in range(nby - 1)])
        triangles = np.asarray(triangles, dtype=np.uint32).reshape([(2 * nby - 2) * (nbx - 1), 3])

        mytri = Triangulation(pts = points, tri = triangles)
        return mytri, znull

    def hillshade(self, azimuth:float, angle_altitude:float):
        """ Create a hillshade array  -- see "hillshade" function accelerated by JIT"""

        if self.shaded is None:
            logging.error(_('No shaded array'))
            return

        self.shaded.set_header(self.get_header())
        self.shaded.array = hillshade(self.array.data, azimuth, angle_altitude)
        self.shaded.delete_lists()

    def get_gradient_norm(self):
        """ Compute and return the norm of the gradient """

        mygradient = WolfArray(mold=self)

        x, y = np.gradient(self.array, self.dx, self.dy)
        mygradient.array = ma.asarray(np.pi / 2. - np.arctan(np.sqrt(x * x + y * y)))
        mygradient.array.mask = self.array.mask

        return mygradient

    def get_laplace(self):
        """ Compute and return the laplacian """
        mylap = WolfArray(mold=self)
        mylap.array = ma.asarray(laplace(self.array) / self.dx ** 2.)
        mylap.array.mask = self.array.mask

        return mylap

    def volume_estimation(self, axs:plt.Axes= None):
        """ Estimation of the volume of the selected zone """

        vect = self.array[np.logical_not(self.array.mask)].flatten()
        zmin = np.amin(vect)
        zmax = np.amax(vect)

        dlg = wx.TextEntryDialog(None, _("Desired Z max ?\n Current Z min :") + str(zmin), _("Z max?"), str(zmax))
        ret = dlg.ShowModal()

        if ret == wx.ID_CANCEL:
            dlg.Destroy()
            return

        zmax = float(dlg.GetValue())
        dlg.Destroy()

        dlg = wx.NumberEntryDialog(None, _("How many values?"), _("How many?"), _("How many ?"), 10, 0, 200)
        ret = dlg.ShowModal()

        if ret == wx.ID_CANCEL:
            dlg.Destroy()
            return

        nb = dlg.GetValue()
        dlg.Destroy()

        deltaz = (zmax - zmin) / nb
        curz = zmin
        nbgroupement = []
        labeled_areas = []
        stockage = []
        z = []

        methods = [_("All cells below the elevation (even if cells are disconnected)"),
                     _("Only the largest connected area below the elevation (not necessarily the same for each elevation)"),
                        _("Only the area below the elevation (if containing the cells stored in memory selection)")]

        keys_select = list(self.SelectionData.selections.keys())
        if len(keys_select) == 0:
            methods = methods[:2]
            use_memory = False

        dlg = wx.SingleChoiceDialog(None, _("Choose a method for selecting the area to integrate"), _("Labeling?"), methods)
        ret = dlg.ShowModal()

        if ret == wx.ID_CANCEL:
            dlg.Destroy()
            return

        if dlg.GetSelection() == 0:
            labeled = False
        else:
            labeled = True
            if dlg.GetSelection() == 1:
                use_memory = False
            else:
                if len(keys_select) >1:
                    dlg = wx.SingleChoiceDialog(None, _("Choose a memory selection"), _("Memory selection?"), keys_select)
                    ret = dlg.ShowModal()

                    if ret == wx.ID_CANCEL:
                        dlg.Destroy()
                        return

                    key = keys_select[dlg.GetSelection()]
                else:
                    key = keys_select[0]

                xy_key = self.SelectionData.selections[key]['select']
                if len(xy_key) == 0:
                    logging.error(_('Empty selection'))
                    return

                ij_key = self.xy2ij_np(xy_key)

                use_memory = True

        extensionmax = WolfArray(mold=self)
        extensionmax.array[:, :] = 0.

        if labeled:
            for i in tqdm(range(nb + 1)):
                z.append(curz)

                # Compute difference between the array and the current elevation
                if i == 0:
                    diff = self.array - (curz + 1.e-3)
                else:
                    diff = self.array - curz

                # Keep only the negative values
                diff[diff > 0] = 0.
                diff.data[diff.mask] = 0.

                if np.count_nonzero(diff < 0.) > 1:
                    # More than one cell below the elevation

                    # Labeling of the cells below the elevation
                    labeled_array, num_features = label(diff.data)
                    # Applying the same mask as the original array
                    labeled_array = ma.asarray(labeled_array)
                    labeled_array.mask = self.array.mask

                    if use_memory:
                        # Use only the labeled areas containing the cells stored in memory selection
                        labeled_areas = []
                        for curij in ij_key:
                            labeled_areas.append(labeled_array[curij[0], curij[1]])

                        # Remove masked value
                        labeled_areas = [x for x in labeled_areas if x is not ma.masked]
                        # Remove duplicates
                        labeled_areas = list(set(labeled_areas))

                        for curarea in labeled_areas:
                            if curarea ==0:
                                volume = 0.
                                surface = 0.
                                continue

                            # Search
                            mask = labeled_array == curarea
                            area = np.where(mask)
                            volume = -self.dx * self.dy * np.sum(diff[area])
                            surface = self.dx * self.dy * len(area[0])
                            extensionmax.array[np.logical_and(mask, extensionmax.array[:, :] == 0.)] = float(i + 1)

                    else:
                        labeled_areas = list(sum_labels(np.ones(labeled_array.shape, dtype=np.int32), labeled_array, range(1, num_features+1)))
                        labeled_areas = [[x, y] for x, y in zip(labeled_areas, range(1, num_features+1))]
                        labeled_areas.sort(key=lambda x: x[0], reverse=True)
                        jmax = labeled_areas[0][1]
                        nbmax = labeled_areas[0][0]

                        volume = -self.dx * self.dy * np.sum(diff[labeled_array == jmax])
                        surface = self.dx * self.dy * nbmax
                        extensionmax.array[np.logical_and(labeled_array == jmax, extensionmax.array[:, :] == 0.)] = float(i + 1)
                else:
                    # Only one cell below the elevation
                    volume = -self.dx * self.dy * np.sum(diff)
                    surface = self.dx * self.dy * np.count_nonzero(diff<0.)
                    extensionmax.array[np.logical_and(diff[:,:]<0., extensionmax.array[:, :] == 0.)] = float(i + 1)

                stockage.append([volume, surface])
                curz += deltaz

        else:
            for i in tqdm(range(nb + 1)):
                z.append(curz)

                if i == 0:
                    diff = self.array - (curz + 1.e-3)
                else:
                    diff = self.array - curz

                diff[diff > 0] = 0.
                diff.data[diff.mask] = 0.
                volume = -self.dx * self.dy * np.sum(diff)
                surface = self.dx * self.dy * np.count_nonzero(diff<0.)
                stockage.append([volume, surface])
                curz += deltaz

                extensionmax.array[np.logical_and(diff[:,:]<0., extensionmax.array[:, :] == 0.)] = float(i + 1)

        dlg = wx.FileDialog(None, _('Choose filename for zoning result'), wildcard='bin (*.bin)|*.bin|tif (*.tif)|*.tif|All (*.*)|*.*', style=wx.FD_SAVE)
        ret = dlg.ShowModal()
        if ret == wx.ID_CANCEL:
            dlg.Destroy()
            return

        fn = dlg.GetPath()
        dlg.Destroy()

        extensionmax.filename = fn
        extensionmax.write_all()

        if axs is None:
            fig, axs = plt.subplots(1, 2, tight_layout=True)
        else:
            fig = axs[0].get_figure()

        axs[0].plot(z, [x[0] for x in stockage])
        axs[0].scatter(z, [x[0] for x in stockage])
        axs[0].set_xlabel(_("Elevation [m]"), size=15)
        axs[0].set_ylabel(_("Volume [$m^3$]"), size=15)
        axs[1].step(z, [x[1] for x in stockage], where='post')
        axs[1].scatter(z, [x[1] for x in stockage])
        axs[1].set_xlabel(_("Elevation [m]"), size=15)
        axs[1].set_ylabel(_("Surface [$m^2$]"), size=15)
        fig.suptitle(_("Retention capacity of the selected zone"), fontsize=20)

        with open(fn[:-4] + '_hvs.txt', 'w') as f:
            f.write('H [m]\tZ [m DNG]\tVolume [$m^3$]\tSurface [$m^2$]\n')
            for curz, (curv, curs) in zip(z, stockage):
                f.write('{}\t{}\t{}\t{}\n'.format(curz - zmin, curz, curv, curs))

        return fig, axs

    def surface_volume_estimation_from_elevation(self, axs:plt.Axes= None,
                           desired_zmin:float = None, desired_zmax:float = None,
                           nb:int = 100,
                           method:Literal['all below', 'largest area', 'selected'] = 'largest area',
                           selected_cells:list[tuple[float, float]] = None,
                           dirout:str | Path = None,
                           invert_z:bool = False,
                           array_to_integrate:"WolfArray" = None
                           ):
        """ Estimation of the surface and volume from an elevation array.

        :param axs: Axes to plot the results
        :param desired_zmin: Minimum elevation to consider
        :param desired_zmax: Maximum elevation to consider
        :param nb: Number of elevation steps
        :param method: Method to use for the estimation ('all below', 'largest area', 'selected')
        :param selected_cells: List of kernel cells (if method is 'selected') -- Consider only the areas containing these cells
        :param dirout: Directory to save the results
        :return: Figure and Axes with the results
        :rtype: tuple[plt.Figure, plt.Axes]
        """

        assert method in ['all below', 'largest area', 'selected'], _('Method must be one of "all below", "largest area", or "selected"')
        if array_to_integrate is not None:
            assert isinstance(array_to_integrate, WolfArray), _('array_to_integrate must be a WolfArray instance')
            assert array_to_integrate.nbx == self.nbx and array_to_integrate.nby == self.nby, _('array_to_integrate must have the same dimensions as the current WolfArray')

        vect = self.array[np.logical_not(self.array.mask)].flatten()
        zmin = np.amin(vect)
        zmax = np.amax(vect)

        if desired_zmin is not None:
            zmin = desired_zmin

        if desired_zmax is not None:
            zmax = desired_zmax

        deltaz = (zmax - zmin) / nb

        curz = zmin
        labeled_areas = []
        stockage = []
        z = []

        if method == 'all below':
            labeled = False
        else:
            labeled = True
            if method == 'largest area':
                use_memory = False
            else:
                xy_key = np.asarray(selected_cells, dtype=np.float64)
                if xy_key is None:
                    logging.error(_('Empty selection'))
                    return

                if len(xy_key) == 0:
                    logging.error(_('Empty selection'))
                    return

                ij_key = self.xy2ij_np(xy_key)

                use_memory = True

        extensionmax = WolfArray(mold=self)
        extensionmax.array[:, :] = 0.

        if labeled:
            for i in tqdm(range(nb + 1)):
                z.append(curz)

                # Compute difference between the array and the current elevation
                if i == 0:
                    diff = self.array - (curz + 1.e-3)
                else:
                    diff = self.array - curz

                # Keep only the negative values
                diff[diff > 0] = 0.
                diff.data[diff.mask] = 0.

                if np.count_nonzero(diff < 0.) > 1:
                    # More than one cell below the elevation

                    # Labeling of the cells below the elevation
                    labeled_array, num_features = label(diff.data)
                    # Applying the same mask as the original array
                    labeled_array = ma.asarray(labeled_array)
                    labeled_array.mask = self.array.mask

                    if use_memory:
                        # Use only the labeled areas containing the cells stored in selected_cells
                        labeled_areas = []
                        for curij in ij_key:
                            labeled_areas.append(labeled_array[curij[0], curij[1]])

                        # Remove masked value
                        labeled_areas = [x for x in labeled_areas if x is not ma.masked]
                        # Remove duplicates
                        labeled_areas = list(set(labeled_areas))

                        for curarea in labeled_areas:
                            if curarea == 0:
                                volume = 0.
                                surface = 0.
                                continue

                            # Search
                            mask = labeled_array == curarea
                            area = np.argwhere(mask)

                            if array_to_integrate is None:
                                volume = -self.dx * self.dy * np.ma.sum(diff[area])
                            else:
                                volume = self.dx * self.dy * np.ma.sum(array_to_integrate.array[area[:,0], area[:,1]])

                            surface = self.dx * self.dy * area.shape[0]
                            extensionmax.array[np.logical_and(mask, extensionmax.array == 0.)] = float(i + 1)

                    else:
                        labeled_areas = list(sum_labels(np.ones(labeled_array.shape, dtype=np.int32), labeled_array, range(1, num_features+1)))
                        labeled_areas = [[x, y] for x, y in zip(labeled_areas, range(1, num_features+1))]
                        labeled_areas.sort(key=lambda x: x[0], reverse=True)
                        jmax = labeled_areas[0][1]
                        nbmax = labeled_areas[0][0]

                        if array_to_integrate is None:
                            volume = -self.dx * self.dy * np.ma.sum(diff[labeled_array == jmax])
                        else:
                            volume = self.dx * self.dy * np.ma.sum(array_to_integrate.array[labeled_array == jmax])

                        surface = self.dx * self.dy * nbmax
                        extensionmax.array[np.logical_and(labeled_array == jmax, extensionmax.array == 0.)] = float(i + 1)
                else:
                    # Only one cell below the elevation
                    if array_to_integrate is None:
                        volume = -self.dx * self.dy * np.ma.sum(diff)
                    else:
                        volume = self.dx * self.dy * np.ma.sum(array_to_integrate.array[diff < 0.])

                    surface = self.dx * self.dy * np.count_nonzero(diff<0.)
                    extensionmax.array[np.logical_and(diff[:,:]<0., extensionmax.array[:, :] == 0.)] = float(i + 1)

                stockage.append([abs(volume), abs(surface)])
                curz += deltaz

        else:
            for i in tqdm(range(nb + 1)):
                z.append(curz)

                if i == 0:
                    diff = self.array - (curz + 1.e-3)
                else:
                    diff = self.array - curz

                diff[diff > 0] = 0.
                diff.data[diff.mask] = 0.

                if array_to_integrate is None:
                    volume  = -self.dx * self.dy * np.ma.sum(diff)
                    surface = self.dx * self.dy * np.count_nonzero(diff<0.)
                    stockage.append([abs(volume), abs(surface)])
                else:
                    ij = np.argwhere(diff < 0.)
                    volume  = self.dx * self.dy * np.ma.sum(array_to_integrate.array[ij[:,0], ij[:,1]])
                    surface = self.dx * self.dy * ij.shape[0]
                    stockage.append([volume, abs(surface)])

                curz += deltaz

                extensionmax.array[np.logical_and(diff[:,:]<0., extensionmax.array[:, :] == 0.)] = float(i + 1)

        if dirout is None:
            dirout = Path(self.filename).parent / 'surface_volume'

        if isinstance(dirout, str):
            dirout = Path(dirout)
        if not dirout.exists():
            dirout.mkdir(parents=True, exist_ok=True)

        extensionmax.filename = str(dirout / 'surface_volume_extension.tif')
        extensionmax.write_all()

        if axs is None:
            fig, axs = plt.subplots(1, 2, tight_layout=True)
        else:
            fig = axs[0].get_figure()

        if invert_z:
            z = [abs(zmin - x) for x in z]
            labelx = _("Water depth [m]")
        else:
            labelx = _("Elevation [m]")

        axs[0].plot(z, [x[0] for x in stockage])
        axs[0].scatter(z, [x[0] for x in stockage])
        axs[0].set_xlabel(labelx, size=10)
        axs[0].set_ylabel(_("Volume [$m^3$]"), size=10)
        axs[1].step(z, [x[1] for x in stockage], where='post')
        axs[1].scatter(z, [x[1] for x in stockage])
        axs[1].set_xlabel(labelx, size=10)
        axs[1].set_ylabel(_("Surface [$m^2$]"), size=10)
        fig.suptitle(_("Retention capacity"), fontsize=12)

        fig.savefig(dirout / 'surface_volume.png', dpi=300)

        fn = dirout / 'surface_volume_hvs.txt'
        with open(fn, 'w') as f:
            f.write('H [m]\tZ [m DNG]\tVolume [$m^3$]\tSurface [$m^2$]\n')
            for curz, (curv, curs) in zip(z, stockage):
                f.write('{}\t{}\t{}\t{}\n'.format(curz - zmin, curz, curv, curs))

        return fig, axs

    def surface_volume_estimation_from_waterdepth(self, axs:plt.Axes=None,
                                                  desired_zmin:float = None, desired_zmax:float = None,
                                                  nb:int = 100,
                                                  method:Literal['all below', 'largest area', 'selected'] = 'largest',
                                                  selected_cells:list[tuple[float, float]] = None,
                                                  dirout:str | Path = None):
        """ Estimation of the surface and volume from a water depth array.
        :param axs: Axes to plot the results
        :param desired_zmin: Minimum water depth to consider
        :param desired_zmax: Maximum water depth to consider
        :param nb: Number of water depth steps
        :param method: Method to use for the estimation ('all below', 'largest area', 'selected')
        :param selected_cells: List of kernel cells (if method is 'selected') -- Consider only the areas containing these cells
        :param dirout: Directory to save the results
        :return: Figure and Axes with the results
        :rtype: tuple[plt.Figure, plt.Axes]
        """

        neg_array = WolfArray(mold=self)
        neg_array.array[:,:] = -self.array
        return neg_array.surface_volume_estimation_from_elevation(desired_zmin=-desired_zmax if desired_zmax is not None else None,
                                                                  desired_zmax=-desired_zmin if desired_zmin is not None else None,
                                                                  nb=nb, method=method,
                                                                  selected_cells=selected_cells,
                                                                  dirout=dirout if dirout is not None else Path(self.filename).parent / 'surface_volume',
                                                                  axs=axs, invert_z=True)


    def paste_all(self, fromarray:"WolfArray", mask_after:bool=True):
        """ Paste all the values from another WolfArray """

        fromarray: WolfArray

        # Récupération des bornes de la matrice source dans la matrice de destination
        i1, j1 = self.get_ij_from_xy(fromarray.origx, fromarray.origy)
        i2, j2 = self.get_ij_from_xy(fromarray.origx + fromarray.nbx * fromarray.dx,
                                     fromarray.origy + fromarray.nby * fromarray.dy)

        # Limitation des bornes à la matrice de destination
        i1 = max(0, i1)
        j1 = max(0, j1)
        i2 = min(self.nbx, i2)
        j2 = min(self.nby, j2)

        # Conversion des bornes utiles en coordonnées
        x1, y1 = self.get_xy_from_ij(i1, j1)
        x2, y2 = self.get_xy_from_ij(i2, j2)

        # Récupération des bornes utiles dans la matrice source
        i3, j3 = fromarray.get_ij_from_xy(x1, y1)
        i4, j4 = fromarray.get_ij_from_xy(x2, y2)

        # Sélection des valeurs non masquées
        # Attention : le résultat est en indices relatifs à [i3,j3] --> demande une conversion en indices absolus pour retrouver les valeurs dans la matrice complète
        usefulij = np.where(np.logical_not(fromarray.array.mask[i3:i4, j3:j4]))

        i5, j5 = self.get_ij_from_xy(x1, y1)

        # Décalage des indices pour la matrice de destination
        usefulij_dest = (usefulij[0] + i5, usefulij[1] + j5)
        usefulij[0][:] += i3
        usefulij[1][:] += j3

        self.array.data[usefulij_dest] = fromarray.array.data[usefulij]

        if mask_after:
            self.mask_data(self.nullvalue)
            self.reset_plot()

    def set_values_sel(self, xy:list[float], z:list[float], update:bool=True):
        """
        Set values at the selected positions

        :param xy: [[x1,y1],[x2,y2],...]
        :param z: [z1,z2,...]
        :param update: update the plot
        """

        sel = np.asarray(xy)
        z   = np.asarray(z)

        if len(sel) == 1:
            ijall = self.xy2ij_np(sel)

            i, j = ijall[0, 0], ijall[0, 1]
            if i < 0 or i >= self.nbx or j < 0 or j >= self.nby:
                logging.error(_('Selected point is out of bounds'))
                return
            else:
                self.array[i, j] = z
        else:
            # ijall = np.asarray(self.get_ij_from_xy(sel[:, 0], sel[:, 1])).transpose()
            ijall = self.xy2ij_np(sel)

            useful = np.where((ijall[:, 0] >= 0) & (ijall[:, 0] < self.nbx) & (ijall[:, 1] >= 0) & (ijall[:, 1] < self.nby))

            self.array[ijall[useful, 0], ijall[useful, 1]] = z[useful]

        self.mask_data(self.nullvalue)

        if update:
            self.reset_plot()

    def init_from_new(self, dlg: NewArray):
        """
        Initialize the array properties from the NewArray dialog
        """

        self.dx = float(dlg.dx.Value)
        self.dy = float(dlg.dy.Value)
        self.nbx = int(dlg.nbx.Value)
        self.nby = int(dlg.nby.Value)
        self.origx = float(dlg.ox.Value)
        self.origy = float(dlg.oy.Value)

        self.array = ma.MaskedArray(np.ones((self.nbx, self.nby), order='F', dtype=np.float32))
        self.mask_reset()

    def init_from_header(self, myhead: header_wolf, dtype:np.dtype = None, force_type_from_header:bool=False):
        """
        Initialize the array properties from a header_wolf object

        :param myhead: header_wolf object
        :param dtype: numpy dtype
        :param force_type_from_header: force the type from the header passed as argument
        """
        if force_type_from_header:
            self.wolftype = myhead.wolftype

        if dtype is None:
            if self.wolftype == WOLF_ARRAY_FULL_DOUBLE:
                dtype = np.float64
            elif self.wolftype == WOLF_ARRAY_FULL_SINGLE:
                dtype = np.float32
            elif self.wolftype == WOLF_ARRAY_FULL_INTEGER:
                dtype = np.int32
            elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
                dtype = np.int16
            elif self.wolftype == WOLF_ARRAY_FULL_INTEGER8:
                dtype = np.int8
            elif self.wolftype == WOLF_ARRAY_FULL_UINTEGER8:
                dtype = np.uint8

        self.dx = myhead.dx
        self.dy = myhead.dy
        self.nbx = myhead.nbx
        self.nby = myhead.nby
        self.origx = myhead.origx
        self.origy = myhead.origy
        self.translx = myhead.translx
        self.transly = myhead.transly

        self.array = ma.MaskedArray(np.ones((self.nbx, self.nby), order='F', dtype=dtype))
        self.mask_reset()

    def interpolation2D(self, key:str='1'):
        """ Interpolation 2D based on selected points in key 1 """

        #FIXME : auhtorize interpolation on other keys

        key = str(key)
        if key in self.mngselection.selections.keys():
            if len(self.mngselection.myselection)>0:
                curlist = self.mngselection.selections[key]['select']
                cursel = self.mngselection.myselection
                if len(curlist) > 0:
                    ij = [self.get_ij_from_xy(cur[0], cur[1]) for cur in curlist]
                    z = [self.array.data[curij[0], curij[1]] for curij in ij]

                    if cursel == ALL_SELECTED:
                        xall = np.linspace(self.origx + self.dx / 2., self.origx + (float(self.nbx) - .5) * self.dx,
                                        self.nbx)
                        yall = np.linspace(self.origy + self.dy / 2., self.origy + (float(self.nby) - .5) * self.dy,
                                        self.nby)
                        cursel = [(x, y) for x in xall for y in yall]

                    z = griddata(curlist, z, cursel, fill_value=np.nan)

                    for cur, curz in zip(cursel, z):
                        if not np.isnan(curz):
                            i, j = self.get_ij_from_xy(cur[0], cur[1])
                            self.array.data[i, j] = curz

                    self.reset_plot()

    def copy_mask(self, source:"WolfArray", forcenullvalue:bool= False, link:bool=True):
        """
        Copy/Link the mask from another WolfArray

        :param source: WolfArray source
        :param forcenullvalue: force nullvalue in the masked zone
        :param link: link the mask if True (default), copy it otherwise
        """

        assert self.shape == source.shape, _('Bad shape')

        if forcenullvalue:
            self.array[np.where(source.array.mask)] = self.nullvalue

        if link:
            self.array.mask = source.array.mask
        else:
            self.array.mask = source.array.mask.copy()

        self.nbnotnull = source.nbnotnull

        self.reset_plot()

    def mask_union(self, source:"WolfArray", link:bool=True):
        """
        Union of the mask with another WolfArray

        :param source: WolfArray source
        :param link: link the mask if True (default), copy it otherwise
        """

        union = self.array.mask & source.array.mask

        self.array[(~union) & (self.array.mask)] = self.nullvalue
        source.array[(~union) & (source.array.mask)] = self.nullvalue


        if link:
            self.array.mask = union
            source.array.mask = union
        else:
            self.array.mask = union.copy()
            source.array.mask = union.copy()

        self.reset_plot()
        source.reset_plot()

    def mask_unions(self, sources:list["WolfArray"], link:bool=True):
        """
        Union of the mask with another WolfArrays

        :param source: list of WolfArray sourceq
        :param link: link the mask if True (default), copy it otherwise
        """

        for cursrc in sources:
            union = self.array.mask & cursrc.array.mask

        self.array[(~union) & (self.array.mask)] = self.nullvalue
        for cursrc in sources:
            cursrc.array[(~union) & (cursrc.array.mask)] = self.nullvalue


        if link:
            self.array.mask = union
            for cursrc in sources:
                cursrc.array.mask = union
        else:
            self.array.mask = union.copy()
            for cursrc in sources:
                cursrc.array.mask = union.copy()

        self.reset_plot()
        for cursrc in sources:
            cursrc.reset_plot()


    def copy_mask_log(self, mask:np.ndarray, link:bool=True):
        """
        Copy the mask from a numpy array

        :param mask: numpy array
        :param link: link the mask if True (default), copy it otherwise
        """
        assert self.shape == mask.shape, _('Bad shape')

        if self.array is None:
            logging.debug(_('No array !!'))
            return

        if link:
            self.array.mask = mask
        else:
            self.array.mask = mask.copy()

        self.reset_plot()

    def check_plot(self):
        """ Make sure the array is plotted """

        self.plotted = True

        if not self.loaded and self.filename != '':
            # if not loaded, load it
            self.read_all()
            # self.read_data()
            if self.masknull:
                self.mask_data(self.nullvalue)

        self.loaded = True

        if VERSION_RGB==1 :
            if self.rgb is None:
                self.updatepalette(0)

    def uncheck_plot(self, unload:bool=True, forceresetOGL:bool=False, askquestion:bool=True):
        """
        Make sure the array is not plotted

        :param unload: unload the data if True (default), keep it otherwise
        :param forceresetOGL: force the reset of the OpenGL lists
        :param askquestion: ask the question if True and a wx App is running (default), don't ask it otherwise
        """

        self.plotted = False

        if unload and self.filename != '':
            if Path(self.filename).exists():
                # An array can exists with a filename but no written data on disk
                # In this case, we don't want to delete the data in memory

                if askquestion and self.wx_exists:
                    dlg = wx.MessageDialog(None,
                                        _('Do you want to unload data? \n If YES, the data will be reloaded from file once checekd \n If not saved, modifications will be lost !!'),
                                        style=wx.YES_NO)
                    ret = dlg.ShowModal()
                    if ret == wx.ID_YES:
                            unload=True

                if unload:
                    self.delete_lists()
                    self.array = np.zeros([1])
                    if VERSION_RGB==1 : self.rgb = None
                    self.loaded = False
                    return

        if not forceresetOGL:
            if askquestion and self.wx_exists:
                dlg = wx.MessageDialog(None, _('Do you want to reset OpenGL lists?'), style=wx.YES_NO)
                ret = dlg.ShowModal()
                if ret == wx.ID_YES:
                    self.delete_lists()
                    if VERSION_RGB==1 : self.rgb = None
        else:
            self.delete_lists()
            if VERSION_RGB==1 : self.rgb = None

    def get_header(self, abs:bool=True) -> header_wolf:
        """
        Return a header_wolf object - different from the self object header

        :param abs: if True (default), return an absolute header (shifted origin) and translation set to 0.
        """

        curhead = header_wolf()

        curhead.origx = self.origx
        curhead.origy = self.origy
        curhead.origz = self.origz

        curhead.dx = self.dx
        curhead.dy = self.dy
        curhead.dz = self.dz

        curhead.nbx = self.nbx
        curhead.nby = self.nby
        curhead.nbz = self.nbz

        curhead.translx = self.translx
        curhead.transly = self.transly
        curhead.translz = self.translz

        curhead.head_blocks = self.head_blocks.copy()

        curhead.wolftype = self.wolftype

        if abs:
            curhead.origx += curhead.translx
            curhead.origy += curhead.transly
            curhead.origz += curhead.translz

            curhead.translx = 0.
            curhead.transly = 0.
            curhead.translz = 0.
        return curhead

    def set_header(self, header: header_wolf):
        """ Set the header from a header_wolf object """
        self.origx = header.origx
        self.origy = header.origy
        self.origz = header.origz

        self.translx = header.translx
        self.transly = header.transly
        self.translz = header.translz

        self.dx = header.dx
        self.dy = header.dy
        self.dz = header.dz

        self.nbx = header.nbx
        self.nby = header.nby
        self.nbz = header.nbz

        self.head_blocks = header.head_blocks.copy()

        self.add_ops_sel()

    def __add__(self, other):
        """Surcharge de l'opérateur d'addition"""
        newArray = WolfArray(whichtype=self.wolftype)
        newArray.nbx = self.nbx
        newArray.nby = self.nby
        newArray.dx = self.dx
        newArray.dy = self.dy
        newArray.origx = self.origx
        newArray.origy = self.origy
        newArray.translx = self.translx
        newArray.transly = self.transly

        if self.nbdims == 3:
            newArray.nbz = self.nbz
            newArray.dz = self.dz
            newArray.origz = self.origz
            newArray.translz = self.translz

        if type(other) in [float, int]:

            if type(other) == int and self.wolftype in [WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_FULL_SINGLE]:
                other = float(other)
            elif type(other) == float and self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8]:
                other = int(other)

            if other != 0.:
                newArray.array = np.ma.masked_array(self.array + other, self.array.mask, dtype=self.array.dtype)
        else:
            newArray.array = np.ma.masked_array(self.array + other.array, self.array.mask, dtype=self.array.dtype)
        newArray.count()

        assert newArray.array.dtype == self.array.dtype, _('Bad dtype')

        return newArray

    def __mul__(self, other):
        """Surcharge de l'opérateur d'addition"""
        newArray = WolfArray(whichtype=self.wolftype)
        newArray.nbx = self.nbx
        newArray.nby = self.nby
        newArray.dx = self.dx
        newArray.dy = self.dy
        newArray.origx = self.origx
        newArray.origy = self.origy
        newArray.translx = self.translx
        newArray.transly = self.transly

        if self.nbdims == 3:
            newArray.nbz = self.nbz
            newArray.dz = self.dz
            newArray.origz = self.origz
            newArray.translz = self.translz

        if type(other) in [float, int]:

            if type(other) == int and self.wolftype in [WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_FULL_SINGLE]:
                other = float(other)
            elif type(other) == float and self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8]:
                other = int(other)

            if other != 0.:
                newArray.array = np.ma.masked_array(self.array * other, self.array.mask, dtype=self.array.dtype)
            else:
                logging.debug(_('Multiplication by 0'))
                newArray.array = np.ma.masked_array(self.array * other, self.array.mask, dtype=self.array.dtype)
        else:
            newArray.array = np.ma.masked_array(self.array * other.array, self.array.mask, dtype=self.array.dtype)
        newArray.count()

        assert newArray.array.dtype == self.array.dtype, _('Bad dtype')

        return newArray

    def __sub__(self, other):
        """Surcharge de l'opérateur de soustraction"""
        newArray = WolfArray(whichtype=self.wolftype)
        newArray.nbx = self.nbx
        newArray.nby = self.nby
        newArray.dx = self.dx
        newArray.dy = self.dy
        newArray.origx = self.origx
        newArray.origy = self.origy
        newArray.translx = self.translx
        newArray.transly = self.transly

        if self.nbdims == 3:
            newArray.nbz = self.nbz
            newArray.dz = self.dz
            newArray.origz = self.origz
            newArray.translz = self.translz

        if type(other) in [float, int]:

            if type(other) == int and self.wolftype in [WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_FULL_SINGLE]:
                other = float(other)
            elif type(other) == float and self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8]:
                other = int(other)

            if other != 0.:
                newArray.array = np.ma.masked_array(self.array - other, self.array.mask, dtype=self.array.dtype)
        else:
            newArray.array = np.ma.masked_array(self.array - other.array, self.array.mask, dtype=self.array.dtype)
        newArray.count()

        assert newArray.array.dtype == self.array.dtype, _('Bad dtype')

        return newArray

    def __pow__(self, other):
        """Surcharge de l'opérateur puissance"""
        newArray = WolfArray(whichtype=self.wolftype)
        newArray.nbx = self.nbx
        newArray.nby = self.nby
        newArray.dx = self.dx
        newArray.dy = self.dy
        newArray.origx = self.origx
        newArray.origy = self.origy
        newArray.translx = self.translx
        newArray.transly = self.transly

        if self.nbdims == 3:
            newArray.nbz = self.nbz
            newArray.dz = self.dz
            newArray.origz = self.origz
            newArray.translz = self.translz

        if type(other) in [float, int]:

            if type(other) == int and self.wolftype in [WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_FULL_SINGLE]:
                other = float(other)
            elif type(other) == float and self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8]:
                other = int(other)

            newArray.array = np.ma.masked_array(self.array ** other, self.array.mask, dtype=self.array.dtype)
        else:
            logging.error(_('Power operator only implemented for scalars'))
            newArray.array[:,:] = 0

        newArray.count()

        assert newArray.array.dtype == self.array.dtype, _('Bad dtype')

        return newArray

    def __truediv__(self, other):
        """Surcharge de l'opérateur division"""
        newArray = WolfArray(whichtype=self.wolftype)
        newArray.nbx = self.nbx
        newArray.nby = self.nby
        newArray.dx = self.dx
        newArray.dy = self.dy
        newArray.origx = self.origx
        newArray.origy = self.origy
        newArray.translx = self.translx
        newArray.transly = self.transly

        if self.nbdims == 3:
            newArray.nbz = self.nbz
            newArray.dz = self.dz
            newArray.origz = self.origz
            newArray.translz = self.translz

        if type(other) in [float, int]:

            if type(other) == int and self.wolftype in [WOLF_ARRAY_FULL_DOUBLE, WOLF_ARRAY_FULL_SINGLE]:
                other = float(other)
            elif type(other) == float and self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8]:
                other = int(other)

            if other != 0.:
                newArray.array = np.ma.masked_array(self.array / other, self.array.mask, dtype=self.array.dtype)
            else:
                logging.error(_('Division by 0 -- Nothing to do !'))
        else:
            newArray.array = np.ma.masked_array(np.where(other == 0., 0., self.array / other.array), self.array.mask, dtype=self.array.dtype)
        newArray.count()

        assert newArray.array.dtype == self.array.dtype, _('Bad dtype')

        return newArray

    def concatenate(self, list_arr:list["WolfArray"], nullvalue:float = 0.):
        """
        Concatenate the values from another WolfArrays into a new one

        :param list_arr: list of WolfArray objects
        :return: a new WolfArray
        :return_type: WolfArray
        """

        list_arr:list[WolfArray]

        for curarray in list_arr:
            assert isinstance(curarray, WolfArray), "The list must contain WolfArray objects"
            assert curarray.nbdims == self.nbdims, "The arrays must have the same number of dimensions"
            assert curarray.dx == self.dx and curarray.dy == self.dy, "The arrays must have the same dx and dy"
            assert curarray.translx == 0 and curarray.transly == 0, "The translations must be zero"
            assert (np.abs(curarray.origx-self.origx)%int(self.dx) == 0)and(np.abs(curarray.origy-self.origy)%int(self.dy) == 0), "The origins are not compatible! You need to do some interpolation stuff"
            assert self.translx == 0 and self.transly == 0, "The translations must be zero"
            assert self.wolftype == curarray.wolftype, "The arrays must have the same wolftype"

        # create an array
        newArray = WolfArray(nullvalue=nullvalue, whichtype=self.wolftype)

        Xlim,Ylim = self.find_union(list_arr)

        newArray.origx  = Xlim[0]
        newArray.origy  = Ylim[0]
        newArray.dx     = self.dx
        newArray.dy     = self.dy

        newArray.nbx = int(np.diff(Xlim)[0]/newArray.dx)
        newArray.nby = int(np.diff(Ylim)[0]/newArray.dy)

        newArray.translx = 0.
        newArray.transly = 0.

        newArray.array = np.ma.masked_array(np.ones((newArray.nbx, newArray.nby), dtype=self.dtype) * nullvalue, mask=True, dtype=self.dtype)

        newArray.paste_all(self, mask_after=False)

        for curarray in list_arr:
            Array_intersect = curarray.find_intersection(self, ij=True)

            if Array_intersect is not None:
                logging.info(_("There is intersection. By default, the array {} overlaps the first one.".format(curarray.filename)))

            newArray.paste_all(curarray, mask_after=False)

        newArray.mask_data(nullvalue)


        return newArray

    def mask_outsidepoly(self, myvect: vector, eps:float = 0.,
                         set_nullvalue:bool=True, method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict'):
        """
        Mask nodes outside a polygon and set values to nullvalue

        :param myvect: target vector in global coordinates
        """
        # The polygon here is in world coordinates
        # (coord will be converted back with translation, origin and dx/dy)
        # (mesh coord, 0-based)

        # trouve les indices dans le polygone
        myij = self.get_ij_inside_polygon(myvect, usemask=True, eps=eps, method=method)

        self.array.mask.fill(True) # Mask everything

        # démasquage des mailles contenues
        self.array.mask[myij[:,0],myij[:,1]] = False

        if set_nullvalue:
            # annulation des valeurs en dehors du polygone
            self.set_nullvalue_in_mask()

        self.count()

    def mask_insidepoly(self, myvect: vector, eps:float = 0.,
                        set_nullvalue:bool=True, method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='mpl'):
        """
        Mask nodes inside a polygon and set values to nullvalue

        :param myvect: target vector in global coordinates
        """
        # The polygon here is in world coordinates
        # (coord will be converted back with translation, origin and dx/dy)
        # (mesh coord, 0-based)

        # trouve les indices dans le polygone
        myij = self.get_ij_inside_polygon(myvect, usemask=False, eps=eps, method=method)

        if set_nullvalue:
            # annulation des valeurs en dehors du polygone
            self.array.data[myij[:,0],myij[:,1]] = self.nullvalue

        # masquage des mailles contenues
        self.array.mask[myij[:,0],myij[:,1]] = True

        self.count()

    def mask_insidepolys(self, myvects: list[vector], eps:float = 0.,
                        set_nullvalue:bool=True, method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='mpl'):
        """
        Mask nodes inside a polygon and set values to nullvalue

        :param myvect: target vector in global coordinates
        """
        # The polygon here is in world coordinates
        # (coord will be converted back with translation, origin and dx/dy)
        # (mesh coord, 0-based)

        # trouve les indices dans le polygone
        for myvect in myvects:
            myij = self.get_ij_inside_polygon(myvect, usemask=False, eps=eps, method=method)

            if myij.shape[0] == 0:
                logging.warning(_("No indices found in the polygon {}").format(myvect.myname))
            else:
                # masquage des mailles contenues
                self.array.mask[myij[:,0],myij[:,1]] = True

                if set_nullvalue:
                    # annulation des valeurs en dehors du polygone
                    self.array.data[myij[:,0],myij[:,1]] = self.nullvalue

        self.count()

    # *************************************************************************************************************************
    # POSITION and VALUES associated to a vector/polygon/polyline
    # These functions can not be stored in header_wolf, because wa can use the mask of the array to limit the search
    # These functions are also present in WolfResults_2D, but they are not exactly the same due to the structure of the results
    # *************************************************************************************************************************
    def get_xy_inside_polygon(self,
                              myvect: vector | Polygon,
                              usemask:bool=True,
                              method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict',
                              epsilon:float = 0.):
        """
        Return the coordinates inside a polygon.

        Main principle:
        - Get all the coordinates in the footprint of the polygon (taking into account the epsilon if provided)
        - Test each coordinate if it is inside the polygon or not (and along boundary if method allows it)
        - Apply the mask if requested

        Returned values are stored in an array of shape (N,2) with N the number of points found inside the polygon.

        :param myvect: target vector - vector or Shapely Polygon
        :param usemask: limit potential nodes to unmaksed nodes
        :param method: method to use ('mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio') - default is 'shapely_strict'
        :param epsilon: tolerance for the point-in-polygon test - default is 0.
        """

        if method == 'mpl':
            return self.get_xy_inside_polygon_mpl(myvect, usemask= usemask, epsilon = epsilon)
        elif method == 'shapely_strict':
            return self.get_xy_inside_polygon_shapely(myvect, usemask, strictly=True, epsilon=epsilon)
        elif method == 'shapely_wboundary':
            return self.get_xy_inside_polygon_shapely(myvect, usemask, strictly=False, epsilon=epsilon)
        elif method == 'rasterio':
            return self.get_xy_inside_polygon_rasterio(myvect, usemask, epsilon=epsilon)

    def get_xy_strictly_on_borders(self, myvect: vector | Polygon | LineString, usemask:bool=True,
                                  method:Literal['shapely']='shapely'):
        """
        Return the coordinates strictly on the borders of a polygon.

        ATTENTION : Tests are performed numerically, so the results may not be exact
        in the sense of pure geometry.

        Do not confuse with "get_xy_under_polyline" which
        "rasterize" the polyline to find useful coordinates.

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        :param method: method to use ('shapely' for now)
        """

        # As we will use Shapely(contains) to test if points are on the border,
        # we need to use a Linestring or a Polygon.boundary.
        if isinstance(myvect, vector):
            myvect.find_minmax()
            boundary = myvect.linestring
        elif isinstance(myvect, Polygon):
            boundary = myvect.boundary
        elif isinstance(myvect, LineString):
            boundary = myvect

        if not is_prepared(boundary):
            prepare(boundary) # Prepare the polygon for **faster** contains check -- VERY IMPORTANT
            to_destroy = True
        else:
            to_destroy = False
        mypointsxy, mypointsij = self.get_xy_infootprint_vect(myvect)

        points= np.array([Point(x,y) for x,y in mypointsxy])
        on_border = list(map(lambda point: boundary.contains(point), points))

        if to_destroy:
            destroy_prepared(boundary) # Destroy the prepared polygon

        to_keep = np.where(on_border)
        mypointsxy = mypointsxy[to_keep]

        if mypointsxy.shape[0] == 0:
            return mypointsxy

        if usemask:
            mypointsij = mypointsij[to_keep]
            mymask = np.logical_not(self.array.mask[mypointsij[:, 0], mypointsij[:, 1]])
            mypointsxy = mypointsxy[np.where(mymask)]

        return mypointsxy

    def get_xy_strictly_on_vertices(self,
                                    myvect: vector | Polygon | LineString,
                                    usemask:bool=True,
                                    method:Literal['shapely']='shapely',
                                    eps:float = 1.e-4):
        """
        Return the coordinates strictly on the vertices of a polygon, Linestring or vector.

        ATTENTION : Tests are performed numerically, so the results may not be exact
        in the sense of pure geometry.

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        :param method: method to use ('shapely' for now)
        """

        # As we will use Shapely(contains) to test if points are on the border,
        # we need to use a Linestring or a Polygon.boundary.
        if isinstance(myvect, vector):
            myvect.find_minmax()
            boundary = myvect.linestring
        elif isinstance(myvect, Polygon):
            boundary = myvect.boundary
        elif isinstance(myvect, LineString):
            boundary = myvect

        if not is_prepared(boundary):
            prepare(boundary) # Prepare the polygon for **faster** contains check -- VERY IMPORTANT
            to_destroy = True
        else:
            to_destroy = False

        mypointsxy, mypointsij = self.get_xy_infootprint_vect(myvect)

        # Calculate distances to the vertices
        # We use the vertices of the polygon or linestring to check if points are on the
        # vertices.

        points      = np.array([Point(x,y) for x,y in mypointsxy])
        vertices    = [Point(pt[0], pt[1], pt[2]) for pt in boundary.coords]
        on_vertices = list(map(lambda point: any(vert.distance(point) < eps for vert in vertices), points))

        if to_destroy:
            destroy_prepared(boundary) # Destroy the prepared polygon

        to_keep = np.where(on_vertices)
        mypointsxy = mypointsxy[to_keep]

        if mypointsxy.shape[0] == 0:
            return mypointsxy

        if usemask:
            mypointsij = mypointsij[to_keep]
            mymask = np.logical_not(self.array.mask[mypointsij[:, 0], mypointsij[:, 1]])
            mypointsxy = mypointsxy[np.where(mymask)]

        return mypointsxy

    def get_xy_inside_polygon_mpl(self,
                                  myvect: vector | Polygon,
                                  usemask:bool=True,
                                  epsilon:float = 0.):
        """
        Return the coordinates inside a polygon

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        """

        if isinstance(myvect, vector):
            # force la mise à jour des min/max
            myvect.find_minmax()
            # Conversion des coordonnées en numpy pour plus d'efficacité (du moins on espère)
            myvert = myvect.asnparray()
        elif isinstance(myvect, Polygon):
            myvert = myvect.exterior.coords[:-1]

        mypointsxy, mypointsij = self.get_xy_infootprint_vect(myvect, eps = epsilon)
        path = mpltPath.Path(myvert)
        inside = path.contains_points(mypointsxy)

        mypointsxy = mypointsxy[np.where(inside)]

        if usemask:
            mypointsij = mypointsij[np.where(inside)]
            mymask = np.logical_not(self.array.mask[mypointsij[:, 0], mypointsij[:, 1]])
            mypointsxy = mypointsxy[np.where(mymask)]

        return mypointsxy

    def get_xy_inside_polygon_shapely(self,
                                      myvect: vector | Polygon,
                                      usemask:bool=True,
                                      strictly:bool=True,
                                      epsilon:float=0.):
        """
        Return the coordinates inside a polygon

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        """

        if isinstance(myvect, vector):
            myvect.find_minmax()
            polygon = myvect.polygon
        elif isinstance(myvect, Polygon):
            polygon = myvect

        if not is_prepared(polygon):
            prepare(polygon) # Prepare the polygon for **faster** contains check -- VERY IMPORTANT
            to_destroy = True
        else:
            to_destroy = False
        mypointsxy, mypointsij = self.get_xy_infootprint_vect(myvect, eps = epsilon)

        if strictly:
            inside = contains_xy(polygon, mypointsxy[:,0], mypointsxy[:,1])
        else:
            points= np.array([Point(x,y) for x,y in mypointsxy])
            boundary = polygon.boundary
            inside = contains(polygon, points)
            on_border = list(map(lambda point: boundary.contains(point), points))
            inside = np.logical_or(inside, on_border)

        if to_destroy:
            destroy_prepared(polygon) # Destroy the prepared polygon

        to_keep = np.where(inside)
        mypointsxy = mypointsxy[to_keep]

        if mypointsxy.shape[0] == 0:
            return mypointsxy

        if usemask:
            mypointsij = mypointsij[to_keep]
            mymask = np.logical_not(self.array.mask[mypointsij[:, 0], mypointsij[:, 1]])
            mypointsxy = mypointsxy[np.where(mymask)]

        return mypointsxy

    def get_xy_inside_polygon_rasterio(self, myvect: vector | Polygon, usemask:bool=True, epsilon:float = 0.):
        """
        Return the coordinates inside a polygon
        """
        # force la mise à jour des min/max
        myvect.find_minmax()

        mypointsxy, mypointsij = self.get_xy_infootprint_vect(myvect, eps = epsilon)

        from rasterio.features import geometry_mask

        poly = myvect.polygon
        mask = geometry_mask([poly], out_shape=(self.nbx, self.nby),
                             transform=self._transform_gmrio(),
                             invert=True,
                             all_touched=False)
        # filter mypointsxy where mask is True
        # mypointsij is a vector of (i,j) indices
        mypointsxy = mypointsxy[mask[mypointsij[:, 0], mypointsij[:, 1]]]

        if usemask:
            mypointsij = mypointsij[mask[mypointsij[:, 0], mypointsij[:, 1]]]
            mymask = np.logical_not(self.array.mask[mypointsij[:, 0], mypointsij[:, 1]])
            mypointsxy = mypointsxy[np.where(mymask)]

        return mypointsxy

    def get_xy_under_polyline(self, myvect: vector, usemask:bool=True):
        """
        Return the coordinates along a polyline

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        """

        allij = self.get_ij_under_polyline(myvect, usemask)
        mypoints = [self.get_xy_from_ij(cur[0], cur[1]) for cur in allij]

        return mypoints

    def get_ij_inside_polygon(self,
                              myvect: vector | Polygon,
                              usemask:bool=True,
                              eps:float = 0.,
                              method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict'):
        """
        Return the indices inside a polygon.

        Main principle:
        - First, get all indices in the footprint of the polygon (bounding box + epsilon)
        - Then, test each point if it is inside the polygon with the selected method
        - Filter with the mask if needed

        Returned indices are stored in an array of shape (N,2) with N the number of points found inside the polygon.

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        :param eps: epsilon for the intersection
        :param method: method to use ('mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio') - default is 'shapely_strict'
        """

        if method == 'mpl':
            return self.get_ij_inside_polygon_mpl(myvect, usemask, eps)
        elif method == 'shapely_strict':
            return self.get_ij_inside_polygon_shapely(myvect, usemask, eps, strictly=True)
        elif method == 'shapely_wboundary':
            return self.get_ij_inside_polygon_shapely(myvect, usemask, eps, strictly=False)
        elif method == 'rasterio':
            return self._get_ij_inside_polygon_rasterio(myvect, usemask, eps)


    def get_ij_inside_listofpolygons(self,
                                     myvects: list[vector | Polygon],
                                     usemask:bool=True,
                                     eps:float = 0.,
                                     method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict'):
        """
        Return the indices inside a list of polygons
        :param myvects: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        :param eps: epsilon for the intersection
        :param method: method to use ('mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio') - default is 'shapely_strict'
        """
        if isinstance(myvects, zone):
            myvects = myvects.myvectors

        alls = list(map(lambda vec: self.get_ij_inside_polygon(vec, usemask, method=method), myvects))
        #remove empty arrays
        alls = [cur for cur in alls if cur.shape[0] > 0]
        if len(alls) == 0:
            return np.empty((0, 2), dtype=int)
        # Concatenate all arrays
        mypointsij = np.concatenate(alls, axis=0)
        # Remove duplicates
        mypointsij = np.unique(mypointsij, axis=0)
        if mypointsij.shape[0] == 0:
            return np.empty((0, 2), dtype=int)
        return mypointsij


    def get_ij_inside_polygon_mpl(self, myvect: vector | Polygon, usemask:bool=True, eps:float = 0.):
        """
        Return the indices inside a polygon

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        :param eps: epsilon for the intersection
        """

        # force la mise à jour des min/max
        if isinstance(myvect, vector):
            myvect.find_minmax()

        mypointsxy, mypointsij = self.get_xy_infootprint_vect(myvect, eps=eps)

        # Conversion des coordonnées en numpy pour plus d'efficacité (du moins on espère)
        myvert = myvect.asnparray()

        path = mpltPath.Path(myvert)
        inside = path.contains_points(mypointsxy)

        mypointsij = mypointsij[np.where(inside)]

        if usemask:
            mymask = np.logical_not(self.array.mask[mypointsij[:, 0], mypointsij[:, 1]])
            mypointsij = mypointsij[np.where(mymask)]

        return mypointsij

    def get_ij_inside_polygon_shapely(self, myvect: vector | Polygon,
                                      usemask:bool=True,
                                      eps:float = 0.,
                                      strictly:bool=True):
        """
        Return the indices inside a polygon with the contains method of shapely

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        :param eps: epsilon for the intersection
        :param strictly: if True, the points on the border are not considered inside
        """

        # force la mise à jour des min/max
        if isinstance(myvect, vector):
            myvect.find_minmax()
            poly = myvect.polygon
        elif isinstance(myvect, Polygon):
            poly = myvect

        mypointsxy, mypointsij = self.get_xy_infootprint_vect(myvect, eps=eps)

        if not is_prepared(poly):
            prepare(poly)  # Prepare the polygon for **faster** contains check -- VERY IMPORTANT
            to_destroy = True
        else:
            to_destroy = False

        if strictly:
            inside = contains_xy(poly, mypointsxy[:,0], mypointsxy[:,1])
        else:
            points= np.array([Point(x,y) for x,y in mypointsxy])
            boundary = poly.boundary
            inside = contains(poly, points)
            on_border = list(map(lambda point: boundary.contains(point), points))
            inside = np.logical_or(inside, on_border)

        if to_destroy:
            destroy_prepared(poly) # Destroy the prepared polygon

        mypointsij = mypointsij[np.where(inside)]

        if usemask:
            mymask = np.logical_not(self.array.mask[mypointsij[:, 0], mypointsij[:, 1]])
            mypointsij = mypointsij[np.where(mymask)]

        return mypointsij

    def _get_ij_inside_polygon_rasterio(self, myvect: vector | Polygon, usemask:bool=True, eps:float = 0.):
        """
        Return the indices inside a polygon with the geometry_mask method of rasterio.

        :remark: get_ij_inside_polygon_shapely is more efficient

        FIXME : geometry_mask seems strange -- it does not work as documented -- RatsrIO 1.3.x

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        :param eps: epsilon for the intersection
        """

        # force la mise à jour des min/max
        if isinstance(myvect, vector):
            myvect.find_minmax()
            poly = myvect.polygon
        elif isinstance(myvect, Polygon):
            poly = myvect

        mypointsxy, mypointsij = self.get_xy_infootprint_vect(myvect, eps=eps)

        from rasterio.features import geometry_mask

        mask = geometry_mask([poly], out_shape=(self.nbx, self.nby),
                             transform=self._transform_gmrio(),
                             invert=True,
                             all_touched=False)
        # filter mypointsij where mask is True
        # mypointsij is a vector of (i,j) indices
        mypointsij = mypointsij[mask[mypointsij[:, 0], mypointsij[:, 1]]]

        if usemask:
            mymask = np.logical_not(self.array.mask[mypointsij[:, 0], mypointsij[:, 1]])
            mypointsij = mypointsij[np.where(mymask)]

        return mypointsij

    def intersects_polygon(self, myvect: vector | Polygon,
                           usemask:bool=True,
                           method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict',
                           buffer:float= 0.) -> bool:
        """ Return True if the array intersects the polygon

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        """

        if buffer > 0.:
            bufvect = myvect.buffer(buffer, inplace= False)
            return self.get_xy_inside_polygon(bufvect, usemask, method).shape[0] > 0
        else:
            return self.get_xy_inside_polygon(myvect, usemask, method).shape[0] > 0

    def intersects_polygon_shapely(self, myvect: vector | Polygon,
                                   eps:float = 0.,
                                   usemask:bool=True,
                                   buffer:float= 0.) -> bool:
        """ Return True if the array intersects the polygon

        :param myvect: target vector
        :param usemask: limit potential nodes to unmaksed nodes
        :param eps: epsilon for the intersection
        :param buffer: buffer for the intersection - using buffer from Shapely [m]
        """
        warnings.warn("intersects_polygon_shapely is deprecated, use intersects_polygon with method='shapely_strict' instead", DeprecationWarning)

        if buffer > 0.:
            poly = myvect.polygon.buffer(buffer)
            return self.get_xy_inside_polygon_shapely(poly, usemask, epsilon=eps).shape[0] > 0
        else:
            return self.get_xy_inside_polygon_shapely(myvect, usemask, epsilon=eps).shape[0] > 0

    def interects_listofpolygons(self, myvects:zone | list[vector],
                                 usemask:bool=True,
                                 method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict',
                                 buffer:float= 0.) -> list[bool]:
        """
        Element-wise intersection with a list of polygons
        """

        if isinstance(myvects, zone):
            myvects = myvects.myvectors
        elif isinstance(myvects, list):
            pass
        else:
            logging.error("Bad type")
            return {}

        return list(map(lambda x: self.intersects_polygon(x, usemask, method, buffer), myvects))

    def intersects_zones(self, zones:Zones | list[zone],
                         usemask:bool=True,
                         method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict',
                         buffer:float = 0.) -> list[list[bool]]:
        """
        Element-wise intersection with a list of zones
        """

        if isinstance(zones, Zones):
            zones = zones.myzones
        elif isinstance(zones, list):
            pass
        else:
            logging.error("Bad type")
            return {}

        return list(map(lambda x: self.interects_listofpolygons(x, usemask, method, buffer), zones))

    def get_total_area_if_intersects(self, myvects:Zones | list[vector],
                                usemask:bool=True,
                                method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict',
                                buffer:float= 0.,
                                coefficient:float = 1.) -> float | list[float]:
        """
        Return the area of the intersection with a list of polygons
        """

        if isinstance(myvects, Zones):
            ret = []
            for curzone in myvects.myzones:
                myvects = curzone.myvectors
                intersects = self.interects_listofpolygons(myvects, usemask, method, buffer)
                ret.append(sum([x.area for x in myvects if intersects[myvects.index(x)]]) * coefficient)
            return ret
        elif isinstance(myvects, list):
            intersects = self.interects_listofpolygons(myvects, usemask, method, buffer)
            return sum([x.area for x in myvects if intersects[myvects.index(x)]]) * coefficient

    def get_ij_under_polyline(self, myvect: vector, usemask:bool=True, step_factor:float=1.):
        """
        Return the indices along a polyline

        :param myvect: target vector
        :param usedmask: limit potential nodes to unmaksed nodes
        :param step_factor: step factor for the discretization of myvect (<1 for thinner, >1 for coarser)

        :return: array of shape (N,2) with N the number of points found under the polyline
        """

        if step_factor>1.0:
            logging.warning("Step_factor greater than 1.0 may lead to lots of missing (i,j) even if faster")
        else:
            def mod_fix(x, y, tol=1e-10):
                result = np.mod(x, y)
                return 0 if np.isclose(result, 0, atol=tol) else (y if np.isclose(result, y, atol=tol) else result)
            assert mod_fix(1.0,step_factor)==0, "1.0 should be a multiple of step_factor"

        # assert step_factor<=1., "Step factor must be <= 1"

        ds = step_factor*min(self.dx, self.dy)
        pts = myvect._refine2D(ds)

        allij = np.asarray([self.get_ij_from_xy(curpt.x, curpt.y) for curpt in pts])

        allij = np.unique(allij, axis=0)

        # filter negative indexes
        allij = allij[np.where((allij[:, 0] >= 0) & (allij[:, 1] >= 0) & (allij[:, 0] < self.nbx) & (allij[:, 1] < self.nby))]

        if usemask:
            mymask = np.logical_not(self.array.mask[allij[:, 0], allij[:, 1]])
            allij = allij[np.where(mymask)]

        return allij

    def get_values_insidepoly(self, myvect: vector, usemask:bool=True, getxy:bool=False,
                              method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict') -> tuple[np.ndarray, np.ndarray | None]:
        """
        Récupération des valeurs contenues dans un polygone

        :param usemask: (optional) restreint les éléments aux éléments non masqués de la matrice
        :param getxy: (optional) retourne en plus les coordonnées des points
        """
        mypoints = self.get_xy_inside_polygon(myvect, usemask, method= method)
        myvalues = np.asarray([self.get_value(cur[0], cur[1]) for cur in mypoints])

        if getxy:
            return myvalues, mypoints
        else:
            return myvalues, None

    def get_values_inside_listofpolygons(self, myvects:zone | list[vector], usemask:bool=True, getxy:bool=False) -> dict:
        """
        Récupération des valeurs contenues dans une instance Zones ou une liste de vecteurs
        """

        ret = {}
        if isinstance(myvects, zone):
            out = ret[myvects.myname] = {}
            myvects = myvects.myvectors
        elif isinstance(myvects, list):
            out = ret
        else:
            logging.error("Bad type")
            return {}

        for vec in myvects:
            out[vec.myname] = self.get_values_insidepoly(vec, usemask, getxy)


    def get_values_inside_zones(self, zones:Zones | list[zone], usemask:bool=True, getxy:bool=False) -> dict:
        """
        Récupération des valeurs contenues dans une instance Zones ou une liste de "zone"
        """

        ret = {}
        if isinstance(zones, Zones):
            out = ret[zones.idx] = {}
            myzones = zones.myzones
        elif isinstance(zones, list):
            myzones = zones
            out = ret
        else:
            logging.error("Bad type")
            return {}

        for zone in myzones:
            out[zone.myname] = self.get_values_inside_listofpolygons(zone, usemask, getxy)

    def get_values_underpoly(self, myvect: vector, usemask:bool=True, getxy:bool=False):
        """
        Récupération des valeurs contenues sous une polyligne

        :param usemask: (optional) restreint les éléments aux éléments non masqués de la matrice
        :param getxy: (optional) retourne en plus les coordonnées des points
        """
        mypoints = self.get_xy_under_polyline(myvect, usemask)

        myvalues = np.asarray([self.get_value(cur[0], cur[1]) for cur in mypoints])

        if getxy:
            return myvalues, mypoints
        else:
            return myvalues, None

    def get_all_values_insidepoly(self, myvect: vector, usemask:bool=True, getxy:bool=False):
        """
        Récupération de toutes les valeurs contenues dans un polygone

        :param usemask: (optional) restreint les éléments aux éléments non masqués de la matrice
        :param getxy: (optional) retourne en plus les coordonnées des points

        ICI on retourne le résultat de get_values_insidepoly, car une seule matrice, mais une autre classe pourrait vouloir faure autre chose
          C'est le cas notamment de Wolfresults_2D
        """

        return self.get_values_insidepoly(myvect, usemask, getxy)

    def get_all_values_underpoly(self, myvect: vector, usemask:bool=True, getxy:bool=False):
        """
        Récupération de toutes les valeurs sous la polyligne

        :param usemask: (optional) restreint les éléments aux éléments non masqués de la matrice
        :param getxy: (optional) retourne en plus les coordonnées des points

        ICI on retourne le résultat de get_values_underpoly, car une seule matrice, mais une autre classe pourrait vouloir faure autre chose
          C'est le cas notamment de Wolfresults_2D
        """

        return self.get_values_underpoly(myvect, usemask, getxy)

    def count_unique_pixels(self) -> dict[int, int]:
        """
        Count the number of pixels for each unique value in the array
        :return: dictionary with the code as key and the number of pixels as value
        """
        if self.wolftype not in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8]:
            logging.error("Bad wolftype")
            return {}

        counts = np.bincount(self.array[~self.array.mask].ravel())
        ret = {i: int(val) for i, val in enumerate(counts) if val > 0}

        return ret

    def get_unique_areas(self, format:Literal['m2', 'ha', 'km2'] = 'm2') -> dict[int, float]:
        """
        Get the areas of each code in the array
        :param array: numpy array or WolfArray
        :return: dictionary with the code as key and the area in m² as value
        """
        ret = self.count_unique_pixels()

        fact = 1.0
        if format in ['ha', 'Ha']:
            fact = 0.0001
        elif format in ['km2', 'km²']:
            fact = 1e-6
        elif format not in ['m2', 'm²']:
            logging.error("Bad format")
            return {}

        # Convert counts to areas in m²
        return {code: float(count) * self.dx * self.dy * fact for code, count in ret.items()}

    def count_insidepoly(self, myvect: vector,
                         usemask:bool=True,
                         method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict',
                         coefficient:float = 1.):
        """
        Compte le nombre de valeurs contenues dans un polygone

        :param myvect: target vector
        :param usemask: (optional) restreint les éléments aux éléments non masqués de la matrice
        :param method: (optional) method to use
        :param coefficient: (optional) coefficient to apply to the count (default 1.)
        """

        ij = self.get_ij_inside_polygon(myvect, usemask, method=method)
        return ij.shape[0] * coefficient

    def count_inside_listofpolygons(self, myvects:zone | list[vector],
                                    usemask:bool=True,
                                    method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict',
                                    coefficient:float = 1.):
        """
        Compte le nombre de valeurs contenues dans une instance Zones ou une liste de vecteurs

        :param myvects: target vectors or zone
        :param usemask: (optional) restreint les éléments aux éléments non masqués de la matrice
        :param method: (optional) method to use
        :param coefficient: (optional) coefficient to apply to the count (default 1.)
        """

        if isinstance(myvects, zone):
            myvects = myvects.myvectors
        else:
            logging.error("Bad type")
            return {}

        return list(map(lambda vec: self.count_insidepoly(vec, usemask, method=method, coefficient=coefficient), myvects))

    def count_inside_zones(self, zones:Zones | list[zone],
                           usemask:bool=True,
                           method:Literal['mpl', 'shapely_strict', 'shapely_wboundary', 'rasterio']='shapely_strict',
                           coefficient:float = 1.):
        """
        Compte le nombre de valeurs contenues dans une instance Zones ou une liste de "zone"

        :param zones: target zones or list of zones
        :param usemask: (optional) restreint les éléments aux éléments non masqués de la matrice
        :param method: (optional) method to use
        :param coefficient: (optional) coefficient to apply to the count (default 1.)
        """

        if isinstance(zones, Zones):
            zones = zones.myzones
        else:
            logging.error("Bad type")

        return list(map(lambda loczone: self.count_inside_listofpolygons(loczone, usemask, method=method, coefficient=coefficient), zones))

    # *************************************************************************************************************************
    # END POSITION and VALUES associated to a vector/polygon/polyline
    # *************************************************************************************************************************

    def reset(self):
        """ Reset the array to nullvalue """

        if self.nbdims == 2:
            self.array[:, :] = self.nullvalue
        elif self.nbdims == 3:
            self.array[:, :, :] = self.nullvalue

    def allocate_ressources(self):
        """ Memory Allocation according to dtype/wolftype"""

        if self.nbdims == 2:
            self.array = ma.ones([self.nbx, self.nby], order='F', dtype=self.dtype)
        elif self.nbdims == 3:
            self.array = ma.ones([self.nbx, self.nby, self.nbz], order='F', dtype=self.dtype)

        self.mask_reset()

    def read_all(self, which_band = None):
        """ Lecture d'un Wolf aray depuis le nom de fichier """

        THRESHOLD = 100_000_000

        if not os.path.exists(self.filename):
            logging.error(_('No data file : ')+self.filename)
            if self.wx_exists:
                dlg = wx.MessageDialog(None, _('No data file : ')+self.filename,
                                        _('Wolf array'), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
            return

        def check_threshold(nbx, nby, THRESHOLD) -> bool:
            if nbx * nby > THRESHOLD:
                logging.info(_('The array is very large > 100M pixels'))
                logging.info(_('Preloading is not recommended for efficiency reasons'))
                logging.info(_('Maybe could you crop the array to a smaller size'))
                logging.info(_('Disabling automatic colormap update'))
                self.mypal.automatic = False
                return True
            else:
                return False

        if self.filename.endswith('.tif') or self.filename.endswith('.tiff'):
            self.read_txt_header()

            if self.preload:

                update_min_max = check_threshold(self.nbx, self.nby, THRESHOLD)

                self.import_geotif(which= which_band, crop = self.cropini)
                self.loaded = True

                if update_min_max:
                    self.mypal.distribute_values(self.array.min(), self.array.max())

        elif self.filename.endswith('.npy'):
            self.read_txt_header()

            if self.preload:
                update_min_max = check_threshold(self.nbx, self.nby, THRESHOLD)

                self._import_npy(crop = self.cropini)
                self.loaded = True

                if update_min_max:
                    self.mypal.distribute_values(self.array.min(), self.array.max())

        elif self.filename.endswith('.vrt'):
            self.read_txt_header()

            if self.preload:
                update_min_max = check_threshold(self.nbx, self.nby, THRESHOLD)
                self.import_vrt(which= which_band, crop = self.cropini)
                self.loaded = True

                if update_min_max:
                    self.mypal.distribute_values(self.array.min(), self.array.max())
        else:
            self.read_txt_header()

            if self.nb_blocks > 0:
                # At this point, we have the header, we know the number of blocks, if exists
                self.myblocks = {}

            if self.preload:
                update_min_max = check_threshold(self.nbx, self.nby, THRESHOLD)

                self.read_data()
                self.loaded = True

                if update_min_max:
                    self.mypal.distribute_values(self.array.min(), self.array.max())

    def write_all(self, newpath:str | Path = None, EPSG:int = None):
        """
        Ecriture de tous les fichiers d'un Wolf array

        :param newpath: new path and filename with extension -- if None, use the current filename
        :param EPSG: EPSG code for geotiff
        """

        if isinstance(newpath, Path):
            newpath = str(newpath)

        if newpath is not None:
            self.filename = newpath

        self.filename = str(self.filename)

        if self.filename.endswith('.tif') or self.filename.endswith('.tiff'):
            self.export_geotif(EPSG=EPSG)

        elif self.filename.endswith('.npy'):

            writing_header = True
            if self.dtype !=  self.array.data.dtype:
                logging.warning(_('Data type changed -- Force conversion to internal numpy array'))
                locarray = self.array.data
                if locarray.dtype == np.float32:
                    self.wolftype = WOLF_ARRAY_FULL_SINGLE
                    logging.warning(_('Data type changed to float32'))
                elif locarray.dtype == np.float64:
                    self.wolftype = WOLF_ARRAY_FULL_DOUBLE
                    logging.warning(_('Data type changed to float64'))
                elif locarray.dtype == np.int32:
                    self.wolftype = WOLF_ARRAY_FULL_INTEGER
                    logging.warning(_('Data type changed to int32'))
                elif locarray.dtype == np.int16:
                    self.wolftype = WOLF_ARRAY_FULL_INTEGER16
                    logging.warning(_('Data type changed to int16'))
                elif locarray.dtype == np.int8:
                    self.wolftype = WOLF_ARRAY_FULL_INTEGER8
                    logging.warning(_('Data type changed to int8'))
                elif locarray.dtype == np.uint8:
                    self.wolftype = WOLF_ARRAY_FULL_UINTEGER8
                    logging.warning(_('Data type changed to uint8'))
                else:
                    logging.error(_('Unsupported type in numpy file -- Abort wrting header file'))
                    writing_header = False

            np.save(self.filename, self.array.data)

            if writing_header:
                self.write_txt_header()
        else:
            self.write_txt_header()
            self.write_array()

    def get_rebin_shape_size(self, factor:float, reshape_array_if_necessary:bool = False) -> tuple[tuple[int, int], tuple[float, float]]:
        """
        Return the new shape after rebinning.

        newdx = dx * factor
        newdy = dy * factor

        The shape is adjusted to be a multiple of the factor.

        :param factor: factor of resolution change -- > 1.0 : decrease resolution, < 1.0 : increase resolution
        :type factor: float
        :return: new shape
        :rtype: Tuple[int, int], Tuple[float, float]
        """

        newdx = self.dx * float(factor)
        newdy = self.dy * float(factor)

        newnbx = self.nbx
        newnby = self.nby

        if factor >=1.0:
            # Decrease resolution
            to_reshape = False
            if np.mod(self.nbx,factor) != 0 or np.mod(self.nby,factor) != 0 :
                newnbx = self.nbx
                newnby = self.nby
                if np.mod(self.nbx,factor) !=0:
                    newnbx = int(self.nbx + factor - np.mod(self.nbx,factor))
                    to_reshape = True
                if np.mod(self.nby,factor) !=0:
                    newnby = int(self.nby + factor - np.mod(self.nby,factor))
                    to_reshape = True

                if to_reshape and reshape_array_if_necessary:
                    logging.warning(f"The shape ({self.nbx}, {self.nby}) is not a multiple of the factor {factor}")
                    new_array = ma.masked_array(np.ones((newnbx, newnby), dtype= self.dtype) * self.nullvalue, dtype= self.dtype)
                    new_array[:self.nbx, :self.nby] = self.array
                    self.array = new_array
        else:
            # Increase resolution
            if abs(int(1/factor) - 1/factor) > 1e-6:
                # find the greatest common divisor of between self.dx and old_dx
                gcd = pgcd_decimal(self.dx, self.dx * factor)
                intermediate_factor = gcd / self.dx

                [newnbx,newnby], [dx,dy] = self.get_rebin_shape_size(intermediate_factor)

                factor = factor / intermediate_factor

                if np.mod(newnbx,factor) != 0 or np.mod(newnby,factor) != 0 :
                    if np.mod(newnbx,factor) !=0:
                        newnbx = int(newnbx + factor - np.mod(newnbx,factor))
                    if np.mod(newnby,factor) !=0:
                        newnby = int(newnby + factor - np.mod(newnby,factor))

                newdx = dx * factor
                newdy = dy * factor

        newnbx = int(newnbx / factor)
        newnby = int(newnby / factor)

        return (newnbx, newnby), (newdx, newdy)

    def get_rebin_header(self, factor:float) -> header_wolf:
        """
        Return a new header after rebinning.

        :param factor: factor of resolution change -- > 1.0 : decrease resolution, < 1.0 : increase resolution
        :type factor: float

        :return: new header
        :rtype: header_wolf
        """

        newshape, newdx_dy = self.get_rebin_shape_size(factor)

        newheader = self.get_header()

        newheader.nbx = newshape[0]
        newheader.nby = newshape[1]
        newheader.dx = newdx_dy[0]
        newheader.dy = newdx_dy[1]

        return newheader

    def rebin(self,
              factor:float,
              operation:Literal['mean', 'sum', 'min', 'max', 'median'] ='mean',
              operation_matrix:"WolfArray"=None) -> None:
        """
        Change resolution - **in place**.

        If you want to keep current data, copy the WolfArray into a new variable -> newWA = Wolfarray(mold=curWA).

        :param factor: factor of resolution change -- > 1.0 : decrease resolution, < 1.0 : increase resolution
        :type factor: float
        :param operation: operation to apply on the blocks ('mean', 'sum', 'min', 'max', 'median')
        :type operation: str, Rebin_Ops
        :param operation_matrix: operation matrix to apply on the blocks -- see the Enum "Rebin_Ops" for more infos. The matrix must have the same shape as the new array
        :type operation_matrix: WolfArray

        """

        op_str = operation
        (testnbx, testnby), __ = self.get_rebin_shape_size(factor)

        if operation_matrix is not None:
            tmp_header = self.get_rebin_header(factor)
            if not operation_matrix.is_like(tmp_header):
                logging.error(_("The operation matrix must have the same shape as the new array"))
                logging.info(_("You can use the get_rebin_header method to get the new header if you don't know it"))
                return

            logging.info(_("Operation matrix detected"))
            logging.info(_("The operation matrix will be used to apply the operation on the blocks"))
        else:

            operation = Rebin_Ops.get_ops(operation)

            if operation is None:
                logging.error(_("Operator not supported -- Must be a string in ['sum', 'mean', 'min', 'max', 'median'] or a Rebin_Ops Enum"))
                return

            if not callable(operation):
                logging.error(_("Operator not supported -- Must be a string in ['sum', 'mean', 'min', 'max', 'median'] or a Rebin_Ops Enum"))


        new_shape, (dx, dy) = self.get_rebin_shape_size(factor, reshape_array_if_necessary= True)

        if factor >=1.0:
            # Decrease resolution

            if operation_matrix is not None:
                # Reshape the input array to split it into blocks of size f x f
                reshaped_a = self.array.reshape(new_shape[0], int(factor), new_shape[1], int(factor))

                # Swap axes to make blocks as separate dimensions
                reshaped_a = reshaped_a.swapaxes(1, 2)

                # Initialize the output matrix
                self.array = ma.masked_array(np.ones((new_shape[0], new_shape[1]), dtype= self.dtype) * self.nullvalue, dtype= self.dtype)

                # Check the dtype of the newly initialized array
                assert self.array.dtype == self.dtype, _('Bad dtype')

                # Vectorized operations
                for op_idx, operation in enumerate(Rebin_Ops.get_numpy_ops()):
                    mask = (operation_matrix.array == op_idx)
                    if np.any(mask):
                        block_results = operation(reshaped_a, axis=(2, 3))
                        self.array[mask] = block_results[mask]

            else:
                compression_pairs = [(d, c // d) for d, c in zip(new_shape,
                                                                self.array.shape)]
                flattened = [l for p in compression_pairs for l in p]
                self.array = operation(self.array.reshape(flattened), axis=(1, 3)).astype(self.dtype)

            self.set_nullvalue_in_mask()
        else:

            # Increase resolution

            if abs(int(1/factor) - 1/factor) > 1e-6:
                logging.warning(f"The factor {factor} doesn't lead to an integer dimension for the Kronecker product")
                logging.warning("The array will be rebinned firstly using the most common factor and then using the operation")

                # find the greatest common divisor of between self.dx and old_dx
                gcd  = pgcd_decimal(self.dx, self.dx * factor)
                intermediate_factor = gcd / self.dx

                logging.warning(f"The greatest common divisor is {gcd}")

                tmp = WolfArray(mold=self, whichtype=self.wolftype)
                tmp.rebin(intermediate_factor)

                if op_str is None:
                    op_str = 'min'

                tmp.rebin(factor / intermediate_factor, operation= op_str)
                self.array = tmp.array
                tmp.array = None
                del tmp
            else:

                ones = np.ones( (int(1/factor), int(1/factor)), dtype=self.array.dtype)
                self.array = np.kron(self.array, ones).astype(self.array.dtype)

            self.mask_data(self.nullvalue)

        self.nbx = new_shape[0]
        self.nby = new_shape[1]
        self.dx = dx
        self.dy = dy

        assert isinstance(self.array, ma.MaskedArray), _('The array must be a masked array')
        assert self.array.shape == (testnbx, testnby), _(f'Bad shape: {self.array.shape} != {(testnbx, testnby)}')

        self.count()

        # rebin must not change the type of the array
        assert self.array.dtype == self.dtype, _(f'Bad dtype: {self.array.dtype} != {self.dtype}')

    def read_txt_header(self):
        """
        Read header from txt file
        Supercharged by WolfArray to avoid explicit call to read_txt_header with parameters
        """

        super().read_txt_header(self.filename)

    def write_txt_header(self):
        """
        Write header to txt file
        Supercharged by WolfArray to avoid explicit call to write_txt_header with parameters
        """

        super().write_txt_header(self.filename+'.txt', self.wolftype, forceupdate=True)

    def _reload(self):
        """ Reload the data from the file """
        self.read_all()
        self.mask_force_null()

    def read_data(self):
        """Opération de lecture des données depuis le fichier connu"""
        if not os.path.exists(self.filename):
            if self.wx_exists:
                logging.warning(_('No data file : ')+self.filename)
            return

        if self.cropini is None:
            with open(self.filename, 'rb') as f:
                self._read_binary_data(f)

        else:
            tmpdx = self.dx
            if type(self.cropini) is np.ndarray:
                pass
            elif type(self.cropini) is list:
                pass
            else:
                if self.wx_exists:
                    newcrop = CropDialog(None, self.get_mapviewer())

                    if self.mapviewer is not None:
                        bounds = self.mapviewer.get_canvas_bounds()

                        newcrop.dx.Value = str(self.dx)
                        newcrop.dy.Value = str(self.dy)

                        # newcrop.dx.Enable(False)
                        # newcrop.dy.Enable(False)

                        newcrop.ox.Value = str(float((bounds[0] // 50.) * 50.))
                        newcrop.ex.Value = str(float((bounds[2] // 50.) * 50.))
                        newcrop.oy.Value = str(float((bounds[1] // 50.) * 50.))
                        newcrop.ey.Value = str(float((bounds[3] // 50.) * 50.))

                    badvalues = True
                    while badvalues:
                        badvalues = False

                        ret = newcrop.ShowModal()
                        if ret == wx.ID_CANCEL:
                            newcrop.Destroy()
                            return
                        else:
                            self.cropini = [[float(newcrop.ox.Value), float(newcrop.ex.Value)],
                                            [float(newcrop.oy.Value), float(newcrop.ey.Value)]]
                            tmpdx = float(newcrop.dx.Value)
                            tmpdy = float(newcrop.dy.Value)

                        if self.dx != tmpdx or self.dy != tmpdy:
                            if tmpdx / self.dx != tmpdy / self.dy:
                                badvalues = True

                    newcrop.Destroy()

                    self.cropini = [[self.cropini[0][0] + self.dx/2., self.cropini[0][1] + self.dx/2.],
                                    [self.cropini[1][0] + self.dy/2., self.cropini[1][1] + self.dy/2.]]
                else:
                    logging.warning(_('No crop defined and no wxPython available'))
                    logging.info(_('Abort reading data !'))
                    return



            with open(self.filename, 'rb') as f:
                if self.wolftype == WOLF_ARRAY_FULL_SINGLE or self.wolftype == WOLF_ARRAY_FULL_SINGLE_3D:

                    imin, jmin = self.get_ij_from_xy(self.cropini[0][0], self.cropini[1][0])
                    imax, jmax = self.get_ij_from_xy(self.cropini[0][1], self.cropini[1][1])

                    imin = int(imin)
                    jmin = int(jmin)
                    imax = int(imax)
                    jmax = int(jmax)

                    oldnbx = self.nbx
                    oldnby = self.nby

                    self.nbx = imax - imin
                    self.nby = jmax - jmin
                    self.origx, self.origy = self.get_xy_from_ij(imin, jmin)
                    self.origx -= self.dx / 2.
                    self.origy -= self.dy / 2.

                    locarray = np.zeros([self.nbx, self.nby])

                    # on boucle sur les 'j'
                    nbi = imax - imin
                    if self.filename.endswith('.flt'):
                        f.seek(((oldnby - jmax) * oldnbx + imin) * 4)
                    else:
                        f.seek((imin + jmin * oldnbx) * 4)

                    for j in range(jmin, jmax):
                        locarray[0:imax - imin, j - jmin] = np.frombuffer(f.read(4 * nbi), dtype=np.float32)
                        f.seek((oldnbx - nbi) * 4, 1)

                    self.array = ma.masked_array(locarray, dtype=np.float32)

                else:
                    logging.warning(_('Unsupported wolftype for cropping'))
                    return

            if self.filename.endswith('.flt'):
                # fichier .flt --> miroir "horizontal"
                self.array = np.fliplr(self.array)

            if self.dx != tmpdx:
                self.rebin(tmpdx / self.dx)

        self.loaded = True

    def _read_binary_data(self, f, seek=0):
        """ Read binary data from file """

        if seek > 0:
            f.seek(0)

        if self.wolftype == WOLF_ARRAY_FULL_SINGLE or self.wolftype == WOLF_ARRAY_FULL_SINGLE_3D:
            locarray = np.frombuffer(f.read(self.nbx * self.nby * 4), dtype=np.float32)
            self.array = ma.masked_array(locarray.copy(), dtype=np.float32)
        elif self.wolftype == WOLF_ARRAY_FULL_LOGICAL:
            locarray = np.frombuffer(f.read(self.nbx * self.nby * 2), dtype=np.int16)
            self.array = ma.masked_array(locarray.copy(), dtype=np.int16)
        elif self.wolftype == WOLF_ARRAY_FULL_DOUBLE:
            locarray = np.frombuffer(f.read(self.nbx * self.nby * 8), dtype=np.float64)
            self.array = ma.masked_array(locarray.copy(), dtype=np.float64)
        elif self.wolftype == WOLF_ARRAY_FULL_INTEGER:
            locarray = np.frombuffer(f.read(self.nbx * self.nby * 4), dtype=np.int32)
            self.array = ma.masked_array(locarray.copy(), dtype=np.int32)
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
            locarray = np.frombuffer(f.read(self.nbx * self.nby * 2), dtype=np.int16)
            self.array = ma.masked_array(locarray.copy(), dtype=np.int16)
        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER8]:
            locarray = np.frombuffer(f.read(self.nbx * self.nby * 2), dtype=np.int8)
            self.array = ma.masked_array(locarray.copy(), dtype=np.int8)
        elif self.wolftype in [WOLF_ARRAY_FULL_UINTEGER8]:
            locarray = np.frombuffer(f.read(self.nbx * self.nby * 2), dtype=np.uint8)
            self.array = ma.masked_array(locarray.copy(), dtype=np.uint8)

        if self.nbdims == 2:
            self.array = self.array.reshape(self.nbx, self.nby, order='F')
            if self.flipupd:
                self.array=np.fliplr(self.array)

        elif self.nbdims == 3:
            self.array = self.array.reshape(self.nbx, self.nby, self.nbz, order='F')

    def write_array(self):
        """ Ecriture du tableau en binaire """
        self.array.data.transpose().tofile(self.filename, "")

    def write_xyz(self, fname:str):
        """ Ecriture d un fichier xyz avec toutes les données du Wolf Array """
        my_file = XYZFile(fname)
        my_file.fill_from_wolf_array(self)
        my_file.write_to_file()

    def get_xyz(self, which='all') -> np.ndarray:
        """ Return an array of xyz coordinates and values """

        x1, y1 = self.get_xy_from_ij(0, 0)
        x2, y2 = self.get_xy_from_ij(self.nbx, self.nby, aswolf=True)
        xloc = np.linspace(x1, x2, self.nbx)
        yloc = np.linspace(y1, y2, self.nby)
        xy = np.meshgrid(xloc, yloc, indexing='xy')

        xyz = np.column_stack([xy[0].flatten(), xy[1].flatten(), self.array.flatten()])

        filter = np.invert(ma.getmaskarray(self.array).flatten())

        return xyz[filter]

    @classmethod
    def set_general_frame_from_xyz(cls, fname:str, dx:float, dy:float, border_size:int=5, delimiter:str=',', fillin:bool=False):
        """
        Lecture d'un fichier texte xyz et initialisation des données de base

        :param fname: nom du fichier xyz
        :param dx: pas en x
        :param dy: pas en y
        :param border_size: nombre de mailles de bordure en plus de l'extension spatiale du fichier
        """

        my_file = XYZFile(fname, delimiter=delimiter)
        my_file.read_from_file()
        (xlim, ylim) = my_file.get_extent()

        Array = WolfArray()
        Array.dx = dx
        Array.dy = dy
        Array.origx = m.floor(xlim[0]) - dx/2. - float(border_size) * Array.dx
        Array.origy = m.floor(ylim[0]) - dy/2. - float(border_size) * Array.dy
        Array.nbx = int((m.floor(xlim[1]) - m.ceil(xlim[0])) / Array.dx) + 1 + 2*border_size
        Array.nby = int((m.floor(ylim[1]) - m.ceil(ylim[0])) / Array.dy) + 1 + 2*border_size

        Array.array = np.ma.zeros((Array.nbx, Array.nby), dtype=np.float32)

        if fillin:
            Array.fillin_from_xyz(my_file.xyz)

        return Array

    @classmethod
    def set_general_frame_from_xyz_dir(cls, path:str, bounds:list, delimiter:str=',', dxdy:tuple[float, float]= None, border_size:int=5, fillin:bool=True):
        """
        Lecture d'un dossier contenant des fichiers texte xyz, initialisation des données de base et chargement de la matrice
        Renvoie un WolfArray or False si le fichier n'est pas dans les limites

        :param path: chemin du dossier avec les fichier xyz
        :dtype path: str
        :param bounds: limites de l'extension spatiale
        :dtype bounds: list
        :param delimiter: délimiteur des fichiers xyz
        :dtype delimiter: str
        :param border_size: nombre de mailles de bordure en plus de l'extension spatiale du fichier
        :dtype border_size: int
        """

        Data_xyz = XYZFile('nothing.xyz', folder=path, bounds=bounds, delimiter=delimiter)

        if Data_xyz.nblines == 0:
            logging.info(f"File not in the boundaries for {path.split(os.sep)[-1]}")
            return False

        xlim, ylim = Data_xyz.get_extent()

        if dxdy is None:
            # We assume dx and dy are equals within xyz file
            dx = np.diff(Data_xyz.xyz[0:2,0])[0]
            logging.info(f"dx = {dx} ; dy = {dx}")
            dy = dx
        else:
            dx,dy = dxdy
            assert dx is not None and dy is not None, _('dx and dy must be defined')

        Array = WolfArray()
        Array.dx = dx
        Array.dy = dy
        Array.origx = m.floor(xlim[0]) -dx/2. - float(border_size) * Array.dx
        Array.origy = m.floor(ylim[0]) -dy/2. - float(border_size) * Array.dy
        Array.nbx = int((m.floor(xlim[1]) - m.ceil(xlim[0])) / Array.dx) +1 + 2*border_size
        Array.nby = int((m.floor(ylim[1]) - m.ceil(ylim[0])) / Array.dy) +1 + 2*border_size

        Array.array = np.ma.zeros((Array.nbx, Array.nby))

        if fillin:
            Array.fillin_from_xyz(Data_xyz.xyz)

        return Array

    def fillin_from_xyz(self, xyz:np.ndarray):
        """ Remplissage du tableau à partir d'un tableau xyz.

        :param xyz: Numpy array - shape (n, 3)
        """

        ij = self.get_ij_from_xy(xyz[:, 0], xyz[:, 1])
        # filter points outside the array
        filter = (ij[0] >= 0) & (ij[0] < self.nbx) & (ij[1] >= 0) & (ij[1] < self.nby)
        xyz = xyz[filter]
        ij = (ij[0][filter], ij[1][filter])

        if self.dtype == np.float32:
            self.array.data[ij] = np.float32(xyz[:, 2])
        elif self.dtype == np.float64:
            self.array.data[ij] = np.float64(xyz[:, 2])
        elif self.dtype == np.int32:
            self.array.data[ij] = np.int32(xyz[:, 2])
        elif self.dtype == np.int16:
            self.array.data[ij] = np.int16(xyz[:, 2])
        elif self.dtype == np.int8:
            self.array.data[ij] = np.int8(xyz[:, 2])
        else:
            logging.warning(_('Type not supported : ')+str(self.dtype))

    def fillin_from_ijz(self, ijz:np.ndarray):
        """ Remplissage du tableau à partir d'un tableau ijz

        :param ijz: Numpy array - shape (n, 3)
        """

        try:
            i = ijz[:, 0].astype(int)
            j = ijz[:, 1].astype(int)
        except Exception as e:
            logging.error(_('Error in conversion of ijz to int : ')+str(e))
            return

        if self.dtype == np.float32:
            self.array.data[i, j] = np.float32(ijz[:, 2])
        elif self.dtype == np.float64:
            self.array.data[i, j] = np.float64(ijz[:, 2])
        elif self.dtype == np.int32:
            self.array.data[i, j] = np.int32(ijz[:, 2])
        elif self.dtype == np.int16:
            self.array.data[i, j] = np.int16(ijz[:, 2])
        elif self.dtype == np.int8:
            self.array.data[i, j] = np.int8(ijz[:, 2])
        else:
            logging.warning(_('Type not supported : ')+str(self.dtype))

    def mask_force_null(self):
        """
        Force to unmask all and mask null value
        """
        self.mask_reset()
        self.mask_data(self.nullvalue)
        self.reset_plot()

    def unmask(self):
        """ alias to mask_reset """
        self.mask_reset()

    def mask_clear(self):
        """ alias to mask_reset """
        self.mask_reset()

    def mask_reset(self):
        """
        Unmask everything
        """

        if self.nbdims == 2:
            # FIXME if mask linking should work
            # as expected, then we do: self.array.mask.fill(0.0)
            # to avoid replacing the linked mask by a (non linked) one.

            if isinstance(self.array.mask, np.bool_):
                # mask is not an array, but a single boolean value
                self.array.mask = np.zeros(self.array.shape)
            else:
                self.array.mask.fill(False) # False == not masked

            self.nbnotnull = self.nbx * self.nby

        elif self.nbdims == 3:
            if isinstance(self.array.mask, np.bool_):
                self.array.mask = np.zeros((self.nbx, self.nby, self.nbz))
            else:
                self.array.mask.fill(False) # False == not masked

            self.nbnotnull = self.nbx * self.nby * self.nbz

    def count(self):
        """ Count the number of not masked values """

        self.nbnotnull = self.array.count()
        return self.nbnotnull

    def mask_data(self, value):
        """ Mask cell where values are equal to `value`"""
        if self.array is None:
            return

        try:
            if not (np.isnan(value) or math.isnan(value)):
                if self.wolftype in [WOLF_ARRAY_FULL_INTEGER]:
                    value=np.int32(value)
                elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
                    value=np.int16(value)
                elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER8]:
                    try:
                        value = np.int8(value)
                    except:
                        value = 0
                        logging.warning(_('Value too high for int8 conversion'))
                        logging.warning(_('Value set to 0'))

                elif self.wolftype in [WOLF_ARRAY_FULL_UINTEGER8]:
                    try:
                        value = np.uint8(value)
                    except:
                        value = 0
                        logging.warning(_('Value too high for int8 conversion'))
                        logging.warning(_('Value set to 0'))
        except:
            logging.error(_('Type not supported : {} - {}'.format(value, type(value))))
            logging.warning(_('Masking operation compromised'))

        if value is not None:

            if isinstance(self.array.mask, np.bool_):
                # mask is not an array, but a single boolean value
                # we must create a new mask array
                if np.isnan(value) or math.isnan(value):
                    self.array.mask = np.isnan(self.array.data)
                else:
                    self.array.mask = self.array.data == value
            else:
                # Copy to prevent unlinking the mask (see `mask_reset`)
                if np.isnan(value) or math.isnan(value):
                    np.copyto(self.array.mask, np.isnan(self.array.data))
                    # self.array.mask[:,:] = np.isnan(self.array.data)
                else:
                    np.copyto(self.array.mask, self.array.data == value)
                    # self.array.mask[:,:] = self.array.data == value
        self.count()

    def mask_lower(self, value):
        """ Mask cell where values are strictly lower than `value` """
        if self.array is None:
            return

        # Copy to prevent unlinking the mask (see `mask_reset`)
        np.copyto(self.array.mask, self.array.data < value)
        self.count()

    def mask_lowerequal(self, value):
        """ Mask cell where values are lower or equal than `value`"""
        if self.array is None:
            return

        # Copy to prevent unlinking the mask (see `mask_reset`)
        np.copyto(self.array.mask, self.array.data <= value)
        self.count()

    def mask_greater(self, value):
        """ Mask cell where values are strictly greater than `value` """
        if self.array is None:
            return

        # Copy to prevent unlinking the mask (see `mask_reset`)
        np.copyto(self.array.mask, self.array.data > value)
        self.count()

    def mask_greaterequal(self, value):
        """ Mask cell where values are greater or equal than `value`"""
        if self.array is None:
            return

        # Copy to prevent unlinking the mask (see `mask_reset`)
        np.copyto(self.array.mask, self.array.data >= value)
        self.count()


    def set_nullvalue_in_mask(self):
        """ Set nullvalue in masked cells """
        if self.array is None:
            return
        self.array.data[self.array.mask] = self.nullvalue

    def reset_plot(self, whichpal=0, mimic=True):
        """ Reset plot of the array """

        self.count()
        if self.plotted:
            self.delete_lists()

            if mimic:
                for cur in self.linkedarrays:
                    if id(cur.mypal) == id(self.mypal) and id(self) !=id(cur):
                        cur.reset_plot(whichpal=whichpal, mimic=False)

            self.updatepalette(whichpal)

            if self.mapviewer is not None:
                self.mapviewer.Refresh()

    def mask_allexceptdata(self, value):
        """ Mask cell where values are different from `value`"""
        if self.array is None:
            return

        # Copy to prevent unlinking the mask (see `mask_reset`)
        np.copyto(self.array.mask, self.array.data != value)
        self.count()

    def mask_invert(self):
        """ Invert the mask """
        if self.array is None:
            return
        # Copy to prevent unlinking the mask (see `mask_reset`)
        np.copyto(self.array.mask, np.logical_not(self.array.mask))
        self.count()

    def meshgrid(self, mode:Literal['gc', 'borders']='gc'):
        """
        Création d'un maillage 2D

        :param mode: 'gc' pour les centres de mailles, 'borders' pour les bords de mailles
        """

        x_start = self.translx + self.origx
        y_start = self.transly + self.origy
        if mode == 'gc':
            x_discr = np.linspace(x_start + self.dx / 2, x_start + self.nbx * self.dx - self.dx / 2, self.nbx)
            y_discr = np.linspace(y_start + self.dy / 2, y_start + self.nby * self.dy - self.dy / 2, self.nby)
        elif mode == 'borders':
            x_discr = np.linspace(x_start, x_start + self.nbx * self.dx, self.nbx + 1)
            y_discr = np.linspace(y_start, y_start + self.nby * self.dy, self.nby + 1)

        y, x = np.meshgrid(y_discr, x_discr)
        return x, y

    def convolve(self,
                 filter,
                 method:Literal['scipyfft',
                                'jaxfft',
                                'classic']='scipyfft',
                 inplace:bool=True) -> "WolfArray":
        """
        Convolve the array with a filter.

        The array and the filter should have the same dtype. If not, a warning is issued and the array dtype is used.

        Thus:

        - An int8 array convolved with float32 filter will be converted to int8.
        - A float32 array convolved with int8 filter will be converted to float32.

        **User should be careful with the dtype of both the array AND the filter.**

        :param filter: filter to convolve with
        :param method: method to use for convolution ('scipyfft', 'jaxfft', 'classic')
        :param inplace: if True, the array is modified in place, otherwise a new array is returned -- same type as the original one
        :return: convolved array, WolfArray instance

        """

        if isinstance(filter, WolfArray):
            _filter = filter.array.data.copy()
            _filter[filter.array.mask] = 0.0
        elif isinstance(filter, np.ndarray):
            _filter = filter.copy()
            _filter[np.isnan(_filter)] = 0.0
        else:
            logging.error("Filter must be a WolfArray or a numpy array")
            return None

        if self.dtype != _filter.dtype:
            logging.warning(_("Filter and array should have the same dtype - {} - {}").format(self.dtype, _filter.dtype))
            logging.warning(_("Convolution result will have the dtype - {}").format(self.dtype))

        if method == 'classic':
            from scipy.signal import convolve2d
            convolved = convolve2d(self.array.data, _filter, mode='same', fillvalue=0.0)
        elif method == 'scipyfft':
            from scipy.signal import fftconvolve
            convolved = fftconvolve(self.array.data, _filter, mode='same')
        elif method == 'jaxfft':
            import jax.numpy as jnp
            from jax.scipy.signal import fftconvolve as jax_fftconvolve
            jax_filter = jnp.array(_filter)
            jax_array = jnp.array(self.array.data)
            convolved = jax_fftconvolve(jax_array, jax_filter, mode='same')
            convolved = jnp.asarray(convolved)
        else:
            logging.error("Method not supported")
            return None

        if inplace:
            self.array.data[:,:] = convolved
            return self
        else:
            newWolfArray = WolfArray(mold=self, whichtype=self.wolftype)
            newWolfArray.array.data[:,:] = convolved
            newWolfArray.array.mask[:,:] = self.array.mask[:,:]
            newWolfArray.count()
            return newWolfArray

    def crop_array(self, bbox:list[list[float],list[float]], setnull_trx_try:bool = False) -> "WolfArray":
        """ Crop the data based on the bounding box.

        Beware of the grid:
        - If the cropped region is smaller than a cell, then the cropped array
          will be empty.
        - If the cropped region doesn't align with the source array grid, it
          will be forced to do so.

        :param bbox: bounding box [[xmin, xmax], [ymin, ymax]].
        :param setnull_trx_try: set the translation to 0 if True, origx and
          origy will be set to the lower left corner of the bbox. Default is
          `False`.
        """

        xmin, xmax = bbox[0]
        ymin, ymax = bbox[1]

        # Make sure the bounding box can be used.
        if xmin > xmax:
            xmin, xmax = xmax, xmin
        if ymin > ymax:
            ymin, ymax = ymax, ymin

        imin, jmin = self.get_ij_from_xy(xmin, ymin)
        imax, jmax = self.get_ij_from_xy(xmax, ymax)

        imin = int(imin)
        jmin = int(jmin)
        imax = int(imax)
        jmax = int(jmax)

        newheader = header_wolf()
        newheader.nbx = imax-imin
        newheader.nby = jmax-jmin
        newheader.dx  = self.dx
        newheader.dy  = self.dy
        newheader.origx, newheader.origy = self.get_xy_from_ij(imin, jmin, abs = setnull_trx_try)
        newheader.origx -= self.dx / 2.
        newheader.origy -= self.dy / 2.
        newheader.translx = self.translx
        newheader.transly = self.transly

        if setnull_trx_try:
            newheader.translx = 0.
            newheader.transly = 0.

        newarray = WolfArray(srcheader=newheader)

        if imin < imax and jmin < jmax:
            newarray.array[:,:] = self.array[imin:imax, jmin:jmax]
        else:
            # One of the dimensions has 0 size => the array is empty
            pass

        return newarray

    def crop_masked_at_edges(self):
        """
        Crop the array to remove masked cells at the edges of the array
        :return: cropped array, WolfArray instance
        """

        # Get max indexes
        Existing_indexes = np.argwhere(self.array.mask!=True)
        Max_index = np.max(Existing_indexes, 0)
        Min_index = np.min(Existing_indexes, 0)

        # convert index in location
        xMax, yMax = self.convert_ij2xy_np(Max_index.reshape((1,2)))
        xMin, yMin = self.convert_ij2xy_np(Min_index.reshape((1,2)))

        # crop
        nbx=np.ceil((xMax[0]-xMin[0])/self.dx).astype(int)+1 #+1 otherwise you remove one line
        nby=np.ceil((yMax[0]-yMin[0])/self.dy).astype(int)+1 #+1 otherwise you remove one column
        return self.crop(int(Min_index[0]),int(Min_index[1]),int(nbx),int(nby))


    def crop(self, i_start:int, j_start:int, nbx:int, nby:int, k_start:int=1, nbz:int=1):
        """
        Crop the array

        :param i_start: start index in x
        :param j_start: start index in y
        :param nbx: number of cells in x
        :param nby: number of cells in y
        :param k_start: start index in z
        :param nbz: number of cells in z

        :return: cropped array, WolfArray instance
        """

        assert type(i_start) == int, "i_start must be an integer"
        assert type(j_start) == int, "j_start must be an integer"
        assert type(nbx) == int, "nbx must be an integer"
        assert type(nby) == int, "nby must be an integer"
        assert type(k_start) == int, "k_start must be an integer"
        assert type(nbz) == int, "nbz must be an integer"

        newWolfArray = WolfArray(nullvalue=self.nullvalue)
        newWolfArray.nbx = nbx
        newWolfArray.nby = nby
        newWolfArray.dx = self.dx
        newWolfArray.dy = self.dy
        newWolfArray.origx = self.origx + float(i_start) * self.dx
        newWolfArray.origy = self.origy + float(j_start) * self.dy
        newWolfArray.translx = self.translx
        newWolfArray.transly = self.transly

        if self.nbdims == 3:
            newWolfArray.nbz = nbz
            newWolfArray.dz = self.dz
            newWolfArray.origz = self.origz + float(k_start) * self.dz
            newWolfArray.translz = self.translz

            newWolfArray.array = self.array[i_start:i_start + nbx, j_start:j_start + nby, k_start:k_start + nbz].copy()
        elif self.nbdims == 2:
            newWolfArray.array = self.array[i_start:i_start + nbx, j_start:j_start + nby].copy()

        return newWolfArray

    def extend(self, x_ext:int, y_ext:int):
        """
        Extend the array

        Crop is the opposite
        """

        assert x_ext >= 0 and y_ext >= 0
        assert self.nbdims == 2, "Only 2D arrays are supported"

        # Remember WolfArrays are masked. Therefore
        # we need to extend mask. In this case, not specifying
        # anything will expand the mask with "dont mask"
        # values.

        # extend vertically
        ex = self.array

        if x_ext > 0:
            # dtype is important: it allows to keep a Fortran friendly
            # type I think.
            ex = ma.append(
                ex,
                np.array([0] * ex.shape[1] * x_ext, dtype=ex.dtype).reshape((x_ext, -1)),
                axis=0,
            )
            self.nbx += x_ext

        # extend horizontally
        if y_ext > 0:
            ex = ma.append(
                ex,
                np.array([0] * ex.shape[0] * y_ext, dtype=ex.dtype).reshape((-1, y_ext)),
                axis=1,
            )
            self.nby += y_ext

        self.array = ex

        self.mask_data(self.nullvalue)

    def extremum(self, which:Literal['min','max']='min'):
        """ Return the extremum value """

        if which == 'min':
            my_extr = np.amin(self.array)
        elif which == 'max':
            my_extr = np.amax(self.array)
        else:
            logging.warning(_('Extremum not supported : ')+which)
            my_extr = -99999.

        return my_extr

    def get_value(self, x:float, y:float, z:float=0., nullvalue:float=-99999, convert_to_float:bool=True):
        """
        Return the value at given coordinates

        :param x: x coordinate
        :param y: y coordinate
        :param z: z coordinate
        :param nullvalue: value to return if the point is outside the array
        """

        if isinstance(self.array.mask, np.bool_):
            logging.error(_('Mask is not an array - Please check your data'))
            return nullvalue

        if self.nbdims == 2:
            i, j = self.get_ij_from_xy(x, y)
            if i >= 0 and i < self.nbx and j >= 0 and j < self.nby:
                if self.array.mask[i, j]:
                    value = nullvalue
                else:
                    value = self.array[i, j]
            else:
                value = nullvalue

        elif self.nbdims == 3:
            i, j, k = self.get_ij_from_xy(x, y, z)
            if i >= 0 and i < self.nbx and j >= 0 and j < self.nby and k >= 0 and k < self.nbz:

                if self.array.mask[i, j, k]:
                    value = nullvalue
                else:
                    value = self.array[i, j, k]
            else:
                value = nullvalue

        if convert_to_float:
            return float(value)
        else:
            return value

    def get_xlim(self, window_x:float, window_y:float):
        """
        Return the limits in x for a given window size

        :param window_x: window size in x
        :param window_y: window size in y
        """

        a_x = window_x / (float(self.nbx) * self.dx)
        a_y = window_y / (float(self.nby) * self.dy)

        if a_x < a_y:
            # C'est la mise à l'échelle selon x qui compte
            return (self.origx + self.translx, self.origx + self.translx + self.nbx * self.dx)
        else:
            # C'est la mise à l'échelle selon y qui compte
            l = (self.nby * self.dy) / window_y * window_x
            return (self.origx + self.translx + self.nbx * self.dx * 0.5 - l * 0.5,
                    self.origx + self.translx + self.nbx * self.dx * 0.5 + l * 0.5)

    def get_ylim(self, window_x:float, window_y:float):
        """
        Retrun the limits in y for a given window size

        :param window_x: window size in x
        :param window_y: window size in y
        """
        a_x = window_x / (float(self.nbx) * self.dx)
        a_y = window_y / (float(self.nby) * self.dy)
        if a_x < a_y:
            # C'est la mise à l'échelle selon x qui compte
            l = (self.nbx * self.dx) / window_x * window_y
            return (self.origy + self.transly + self.nby * self.dy * 0.5 - l * 0.5,
                    self.origy + self.transly + self.nby * self.dy * 0.5 + l * 0.5)
        else:
            # C'est la mise à l'échelle selon y qui compte
            return (self.origy + self.transly, self.origy + self.transly + self.nby * self.dy)

    def get_working_array(self, onzoom:list[float]=[]):
        """
        Return the part of the array in the zoom window

        :param onzoom: zoom window -- [xmin, xmax, ymin, ymax]
        """

        if onzoom != []:
            istart, jstart = self.get_ij_from_xy(onzoom[0], onzoom[2])
            iend, jend = self.get_ij_from_xy(onzoom[1], onzoom[3])

            istart = 0 if istart < 0 else istart
            jstart = 0 if jstart < 0 else jstart
            iend = self.nbx if iend > self.nbx else iend
            jend = self.nby if jend > self.nby else jend

            partarray = self.array[istart:iend, jstart:jend]
            self.nbnotnullzoom = partarray.count()
            return partarray[partarray.mask == False]
        else:
            return self.array[self.array.mask == False]

    def updatepalette(self, which:int=0, onzoom=[]):
        """
        Update the palette/colormap

        :param which: which palette to update
        :param onzoom: zoom window -- [xmin, xmax, ymin, ymax]
        """

        if self.array is None:
            return

        if self.mypal.automatic:
            if onzoom != []:
                self.mypal.isopop(self.get_working_array(onzoom), self.nbnotnullzoom)
            else:
                self.mypal.isopop(self.get_working_array(), self.nbnotnull)

        if VERSION_RGB==1 or which == 1:
            if self.nbx * self.nby > 1_000_000 : logging.info(_('Computing colors'))
            if self.wolftype not in [WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8]:
                # FIXME: Currently, only some types are supported in Cython/OpenGL library
                self._tmp_float32 = self.array.astype(dtype=np.float32)
                self.rgb = self.mypal.get_rgba(self._tmp_float32)
            else:
                self._tmp_float32 = None
                self.rgb = self.mypal.get_rgba(self.array)
            if self.nbx * self.nby > 1_000_000 : logging.info(_('Colors computed'))
        elif VERSION_RGB in [2 ,3]:
            if self.wolftype not in [WOLF_ARRAY_FULL_SINGLE,
                                     WOLF_ARRAY_FULL_INTEGER8,
                                     WOLF_ARRAY_FULL_UINTEGER8,
                                     WOLF_ARRAY_FULL_INTEGER16,
                                     WOLF_ARRAY_FULL_INTEGER16_2,
                                     WOLF_ARRAY_FULL_INTEGER,
                                     WOLF_ARRAY_FULL_DOUBLE,
                                     WOLF_ARRAY_HILLSHAPE]:
                # FIXME: Currently, only some types are supported in Cython/OpenGL library
                self._tmp_float32 = self.array.astype(dtype=np.float32)
            else:
                self._tmp_float32 = None


        if VERSION_RGB==1 or which == 1:
            if self.shading:
                pond = (self.shaded.array-.5)*2.
                pmin = (1. - self.shaded.alpha) * self.rgb
                pmax = self.shaded.alpha * np.ones(self.rgb.shape) + (1. - self.shaded.alpha) * self.rgb
                for i in range(4):
                    self.rgb[pond<0,i] = self.rgb[pond<0,i] * (1.+pond[pond<0]) - pmin[pond<0,i] * pond[pond<0]
                    self.rgb[pond>0,i] = self.rgb[pond>0,i] * (1.-pond[pond>0]) + pmax[pond>0,i] * pond[pond>0]

        if VERSION_RGB==1 or which == 1: self.rgb[self.array.mask] = [1., 1., 1., 0.]

        if self.myops is not None:
            # update the wx
            self.myops.update_palette()

        if len(self.viewers3d) > 0:
            for cur in self.viewers3d:
                cur.update_palette(self.idx, self.mypal.get_colors_f32().flatten(), self.mypal.values.astype(np.float32))

    def find_minmax(self, update=False):
        """ Find the min and max values of the array

        ATTENTION : Just to conform to the interface of the Element_To_Draw class
        """
        if update:
            [self.xmin, self.xmax], [self.ymin, self.ymax] = self.get_bounds()

    def plot(self, sx:float=None, sy:float=None, xmin:float=None, ymin:float=None, xmax:float=None, ymax:float=None, size:float=None):
        """
        Plot the array - OpenGL

        :param sx: scale along X
        :param sy: scale along Y
        :param xmin: Lower-Left coordinates in X
        :param ymin: Lower-Left coordinates in Y
        :param xmax: Upper-Right coordinates in X
        :param ymax: Upper-Right coordinates in Y
        :param size: size of the window (not used here but necessary for compatibility with Element_To_Draw)
        """
        if not self.plotted:
            return

        self.plotting = True

        if self.plotted and sx is None:
            sx = self.sx
            sy = self.sy
            xmin = self._xmin_plot
            xmax = self._xmax_plot
            ymin = self._ymin_plot
            ymax = self._ymax_plot
        else:
            self.sx = sx
            self.sy = sy
            self._xmin_plot = xmin
            self._xmax_plot = xmax
            self._ymin_plot = ymin
            self._ymax_plot = ymax

        nbpix = min(sx * self.dx, sy * self.dy)
        if nbpix == 0.:
            logging.warning(_('WolfArray.plot - No pixels to plot'))
            return
        elif nbpix >= 1.:
            # si une maille est tracée sur au moins 2 pixels
            curscale = 1
        elif math.ceil(1. / nbpix) <= 3:
            curscale = math.ceil(math.ceil(1. / nbpix))
        else:
            curscale = math.ceil(math.ceil(1. / nbpix) / 3) * 3

        curscale = max(curscale, 1)
        cursize = curscale  # 2.**curscale
        curnbx = max(math.ceil(float(self.nbx) / (self.gridsize * cursize)), 1)
        curnby = max(math.ceil(float(self.nby) / (self.gridsize * cursize)), 1)

        if not cursize in self.mygrid.keys():
            self.mygrid[cursize] = {}
            curlist = self.mygrid[cursize]
            curlist['nbx'] = curnbx
            curlist['nby'] = curnby
            numlist = glGenLists(curnbx * curnby)
            curlist['firstlist'] = numlist
            logging.debug(_('OpenGL lists - allocation') + ' - ' +_('first list')+str(numlist) )
            curlist['mylists'] = np.linspace(numlist, numlist + curnbx * curnby - 1, num=curnbx * curnby,
                                             dtype=np.integer).reshape((curnbx, curnby), order='F')
            curlist['done'] = np.zeros((curnbx, curnby), dtype=np.integer, order='F')

        if (curnbx == 1 and curnby == 1):
            if (self.gridmaxscales == -1):
                self.gridmaxscales = curscale
            elif curscale > self.gridmaxscales:
                curscale = self.gridmaxscales
                cursize = curscale
                curnbx = max(math.ceil(float(self.nbx) / (self.gridsize * cursize)), 1)
                curnby = max(math.ceil(float(self.nby) / (self.gridsize * cursize)), 1)

        istart, jstart = self.get_ij_from_xy(xmin, ymin, scale=cursize * float(self.gridsize))
        iend, jend = self.get_ij_from_xy(xmax, ymax, scale=cursize * float(self.gridsize))

        istart = max(0, istart)
        jstart = max(0, jstart)
        iend = min(curnbx - 1, iend)
        jend = min(curnby - 1, jend)

        if self.wolftype != WOLF_ARRAY_HILLSHAPE and self.shading:
            self.hillshade(self.azimuthhill, self.altitudehill)

            if VERSION_RGB==1 :
                self.updatepalette(0)
                self.shaded.updatepalette(0)

            self.shading=False
            if self.mapviewer is not None:
                from .PyDraw import draw_type
                if not self.idx + '_hillshade' in self.mapviewer.get_list_keys(drawing_type=draw_type.ARRAYS, checked_state= None) :# .added['arrays'].keys():
                    self.mapviewer.add_object('array', newobj=self.shaded, ToCheck=True, id=self.idx + '_hillshade')

        try:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            for j in range(jstart, jend + 1):
                for i in range(istart, iend + 1):
                    self.fillonecellgrid(cursize, i, j)
                    try:
                        mylistdone = self.mygrid[cursize]['done'][i, j]
                        if mylistdone == 1:
                            mylist = self.mygrid[cursize]['mylists'][i, j]
                            if mylist > 0:
                                glCallList(self.mygrid[cursize]['mylists'][i, j])
                    except Exception as e:
                        logging.error(_('OpenGL error in WolfArray.plot 1 -- Please report this case with the data file and the context in which the error occured'))
                        logging.error(e)

            glDisable(GL_BLEND)
        except Exception as e:
            logging.error(_('OpenGL error in WolfArray.plot 2 -- Please report this case with the data file and the context in which the error occured'))
            logging.error(e)

        self.plotting = False

        # Plot selected nodes
        if self.mngselection is not None:
            self.mngselection.plot_selection()

        # Plot zones attached to array
        if self.myops is not None:
            self.myops.myzones.plot()

    def delete_lists(self):
        """ Delete OpenGL lists """

        logging.debug(_('OpenGL lists - deletion -- array {}'.format(self.idx)))
        for idx, cursize in enumerate(self.mygrid):
            curlist = self.mygrid[cursize]
            nbx = curlist['nbx']
            nby = curlist['nby']
            first = curlist['firstlist']

            try:
                glDeleteLists(first, nbx * nby)
            except Exception as e:
                logging.error(_('OpenGL error in WolfArray.delete_lists -- Please report this case with the data file and the context in which the error occured'))
                logging.error(e)

            logging.debug(str(first)+'  '+str(nbx * nby))

        self.mygrid = {}
        self.gridmaxscales = -1

    def plot_matplotlib(self, figax:tuple=None,
                        getdata_im:bool=False,
                        update_palette:bool=True,
                        vmin:float=None, vmax:float=None,
                        figsize:tuple=None,
                        Walonmap:bool=False,
                        cat:Literal['IMAGERIE/ORTHO_1971', 'IMAGERIE/ORTHO_1994_2000', 'IMAGERIE/ORTHO_2006_2007', 'IMAGERIE/ORTHO_2009_2010',
                                    'IMAGERIE/ORTHO_2012_2013', 'IMAGERIE/ORTHO_2015', 'IMAGERIE/ORTHO_2016',
                                    'IMAGERIE/ORTHO_2017', 'IMAGERIE/ORTHO_2018', 'IMAGERIE/ORTHO_2019',
                                    'IMAGERIE/ORTHO_2020', 'IMAGERIE/ORTHO_2021', 'IMAGERIE/ORTHO_2022_PRINTEMPS',
                                    'IMAGERIE/ORTHO_2022_ETE', 'IMAGERIE/ORTHO_2023_ETE', 'IMAGERIE/ORTHO_LAST',
                                    'orthoimage_coverage', 'orthoimage_coverage_2016', 'orthoimage_coverage_2017',
                                    'orthoimage_coverage_2018', 'orthoimage_coverage_2019',
                                    'orthoimage_coverage_2020', 'orthoimage_coverage_2021',
                                    'orthoimage_coverage_2022', 'crossborder', 'crossborder_grey',
                                    'overlay', 'topo', 'topo_grey'] = 'IMAGERIE/ORTHO_LAST',
                        first_mask_data:bool=True,
                        with_legend:bool=False,
                        IGN:bool=False,
                        Cartoweb:bool=False):
        """
        Plot the array - Matplotlib version

        Using imshow and RGB array

        Plot the array using Matplotlib.
        This method visualizes the array data using Matplotlib's `imshow` function.
        It supports optional overlays, custom palettes, and value range adjustments.

        Notes:
        ------
        - The method applies a mask to the data using the `nullvalue` attribute before plotting.
        - If `Walonmap` is True, the method fetches and overlays a map image using the WalOnMap service.
        - The aspect ratio of the plot is set to 'equal'.

        :param figax: A tuple containing a Matplotlib figure and axis (fig, ax). If None, a new figure and axis are created.
        :type figax: tuple, optional (Default value = None)
        :param getdata_im: If True, returns the image object along with the figure and axis. Default is False, then it only returns (fig, ax).
        :type getdata_im: bool, optional (Default value = False)
        :param update_palette: If True, updates the color palette before plotting. Default is True.
        :type update_palette: bool, optional (Default value = True)
        :param vmin: Minimum value for color scaling. If None, the minimum value is determined automatically. Default is None.
        :type vmin: float, optional (Default value = None)
        :param vmax: Maximum value for color scaling. If None, the maximum value is determined automatically. Default is None.
        :type vmax: float, optional (Default value = None)
        :param figsize: Size of the figure in inches (width, height). Only used if `figax` is None. Default is None.
        :type figsize: tuple, optional (Default value = None)
        :param Walonmap: If True, overlays a map image using the WalOnMap service. Default is False.
        :type Walonmap: bool, optional (Default value = False)
        :param cat: The category of the map to fetch from the WalOnMap service. Default is 'IMAGERIE/ORTHO_2022_ETE'.
            Available orthos:
            - `'IMAGERIE/ORTHO_1971'`
            - `'IMAGERIE/ORTHO_1994_2000'`
            - `'IMAGERIE/ORTHO_2006_2007'`
            - `'IMAGERIE/ORTHO_2009_2010'`
            - `'IMAGERIE/ORTHO_2012_2013'`
            - `'IMAGERIE/ORTHO_2015'`
            - `'IMAGERIE/ORTHO_2016'`
            - `'IMAGERIE/ORTHO_2017'`
            - `'IMAGERIE/ORTHO_2018'`
            - `'IMAGERIE/ORTHO_2019'`
            - `'IMAGERIE/ORTHO_2020'`
            - `'IMAGERIE/ORTHO_2021'`
            - `'IMAGERIE/ORTHO_2022_PRINTEMPS'`
            - `'IMAGERIE/ORTHO_2022_ETE'`
            - `'IMAGERIE/ORTHO_2023_ETE'`
            - `'IMAGERIE/ORTHO_LAST'`
            - 'orthoimage_coverage'
            - 'orthoimage_coverage_2016',
            - 'orthoimage_coverage_2017',
            - 'orthoimage_coverage_2018',
            - 'orthoimage_coverage_2019',
            - 'orthoimage_coverage_2020',
            - 'orthoimage_coverage_2021',
            - 'orthoimage_coverage_2022'
            - 'crossborder',
            - 'crossborder_grey',
            - 'overlay',
            - 'topo',
            - 'topo_grey'
        :type cat: str, optional (Default value = `'IMAGERIE/ORTHO_2022_ETE'`)
        :param first_mask_data: If True, applies the mask to the data before plotting. Default is True.
        :type first_mask_data: bool, optional (Default value = True)
        :param with_legend: If True, adds a color legend to the plot. Default is False.
        :type with_legend: bool, optional (Default value = False)
        :return: If `getdata_im` is False, returns (fig, ax), where `fig` is the Matplotlib figure and `ax` is the axis. If `getdata_im` is True, returns (fig, ax, im), where `im` is the image object created by `imshow`.
        :rtype: tuple
        """

        available_Walonmap = ['IMAGERIE/ORTHO_1971', 'IMAGERIE/ORTHO_1994_2000', 'IMAGERIE/ORTHO_2006_2007', 'IMAGERIE/ORTHO_2009_2010',
                                    'IMAGERIE/ORTHO_2012_2013', 'IMAGERIE/ORTHO_2015', 'IMAGERIE/ORTHO_2016',
                                    'IMAGERIE/ORTHO_2017', 'IMAGERIE/ORTHO_2018', 'IMAGERIE/ORTHO_2019',
                                    'IMAGERIE/ORTHO_2020', 'IMAGERIE/ORTHO_2021', 'IMAGERIE/ORTHO_2022_PRINTEMPS',
                                    'IMAGERIE/ORTHO_2022_ETE', 'IMAGERIE/ORTHO_2023_ETE', 'IMAGERIE/ORTHO_LAST']
        available_IGN = ['orthoimage_coverage', 'orthoimage_coverage_2016', 'orthoimage_coverage_2017',
                         'orthoimage_coverage_2018', 'orthoimage_coverage_2019',
                         'orthoimage_coverage_2020', 'orthoimage_coverage_2021',
                         'orthoimage_coverage_2022']
        available_Cartoweb = ['crossborder', 'crossborder_grey', 'overlay', 'topo', 'topo_grey']

        if first_mask_data:
            self.mask_data(self.nullvalue)

        if update_palette:
            self.updatepalette(0)

        if figax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig, ax = figax

        if Walonmap:
            from .PyWMS import getWalonmap
            from PIL import Image

            if cat not in available_Walonmap:
                logging.error(_('The category {} is not available in WalOnMap').format(cat))
                logging.error(_('Available categories are: {}').format(', '.join(available_Walonmap)))
            else:
                try:
                    bounds = self.get_bounds()

                    scale_covery = (bounds[0][1] - bounds[0][0]) / (bounds[1][1] - bounds[1][0])

                    if scale_covery > 1.:
                        # x is larger than y
                        w = 2000
                        h = int(2000 / scale_covery)
                    else:
                        # y is larger than x
                        h = 2000
                        w = int(2000 * scale_covery)

                    IO_image = getWalonmap(cat, bounds[0][0], bounds[1][0],
                                        bounds[0][1], bounds[1][1],
                                        w=w, h=h, tofile=False) # w=self.nbx, h=self.nby

                    image = Image.open(IO_image)

                    ax.imshow(image.transpose(Image.Transpose.FLIP_TOP_BOTTOM), extent=(bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]), alpha=1, origin='lower')
                except Exception as e:
                    logging.error(_('Error while fetching the map image from WalOnMap'))
                    logging.error(e)

        elif IGN:
            from .PyWMS import getNGI
            from PIL import Image

            if cat not in available_IGN:
                logging.error(_('The category {} is not available in IGN').format(cat))
                logging.error(_('Available categories are: {}').format(', '.join(available_IGN)))

            else:
                try:
                    bounds = self.get_bounds()
                    scale_covery = (bounds[0][1] - bounds[0][0]) / (bounds[1][1] - bounds[1][0])
                    if scale_covery > 1.:
                        # x is larger than y
                        w = 2000
                        h = int(2000 / scale_covery)
                    else:
                        # y is larger than x
                        h = 2000
                        w = int(2000 * scale_covery)
                    IO_image = getNGI(cat, bounds[0][0], bounds[1][0],
                                    bounds[0][1], bounds[1][1],
                                        w=w, h=h, tofile=False) # w=self.nbx, h=self.nby
                    image = Image.open(IO_image)
                    ax.imshow(image.transpose(Image.Transpose.FLIP_TOP_BOTTOM), extent=(bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]), alpha=1, origin='lower')
                except Exception as e:
                    logging.error(_('Error while fetching the map image from IGN'))
                    logging.error(e)

        elif Cartoweb:
            from .PyWMS import getCartoweb
            from PIL import Image

            if cat not in available_Cartoweb:
                logging.error(_('The category {} is not available in Cartoweb').format(cat))
                logging.error(_('Available categories are: {}').format(', '.join(available_Cartoweb)))
            else:
                try:
                    bounds = self.get_bounds()
                    scale_covery = (bounds[0][1] - bounds[0][0]) / (bounds[1][1] - bounds[1][0])
                    if scale_covery > 1.:
                        # x is larger than y
                        w = 2000
                        h = int(2000 / scale_covery)
                    else:
                        # y is larger than x
                        h = 2000
                        w = int(2000 * scale_covery)
                    IO_image = getCartoweb(cat, bounds[0][0], bounds[1][0],
                                            bounds[0][1], bounds[1][1],
                                            w=w, h=h, tofile=False) # w=self.nbx, h=self.nby
                    image = Image.open(IO_image)
                    ax.imshow(image.transpose(Image.Transpose.FLIP_TOP_BOTTOM), extent=(bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]), alpha=1, origin='lower')
                except Exception as e:
                    logging.error(_('Error while fetching the map image from Cartoweb'))
                    logging.error(e)

        if vmin is None and vmax is not None:
            vmin = self.mypal.values[0]
        elif vmax is None and vmin is not None:
            vmax = self.mypal.values[-1]

        if (vmin is None) and (vmax is None):
            # im = ax.imshow(self.array.transpose(), origin='lower', cmap=self.mypal,
            #         extent=(self.origx, self.origx + self.dx * self.nbx, self.origy, self.origy + self.dy * self.nby))
            im = ax.imshow(self.array.transpose(),
                           origin='lower',
                           norm = self.mypal.norm,
                           cmap=self.mypal.cmap,
                           interpolation='none',
                           extent=(self.origx,
                                   self.origx + self.dx * self.nbx,
                                   self.origy,
                                   self.origy + self.dy * self.nby),
                           alpha=np.select([self.array.mask.T, ~self.array.mask.T],
                                            [np.zeros(self.shape).T, np.ones(self.shape).T * self.alpha]))

            if with_legend:
                # add a legend in a new axis
                ax_leg = fig.add_axes([0.92, 0.12, 0.04, 0.8])
                from matplotlib.colorbar import ColorbarBase
                from matplotlib import colors
                cbar = ColorbarBase(ax_leg, cmap=self.mypal.cmap, norm=self.mypal.norm, orientation='vertical')
                cbar.set_ticks(self.mypal.values)

                # ticks labels with 3 decimal places
                labels = [f"{val:.3f}" for val in self.mypal.values]
                cbar.set_ticklabels(labels)
                cbar.ax.tick_params(labelsize=8)
                cbar.ax.yaxis.set_label_position('left')
                cbar.ax.yaxis.set_ticks_position('right')
                cbar.ax.yaxis.set_tick_params(width=0.5, size=2, direction='in', color='black')


        else:
            im = ax.imshow(self.array.transpose(),
                           origin='lower',
                           cmap=self.mypal,
                           extent=(self.origx,
                                   self.origx + self.dx * self.nbx,
                                   self.origy,
                                   self.origy + self.dy * self.nby),
                           vmin=vmin, vmax=vmax,
                           alpha=np.select([self.array.mask.T, ~self.array.mask.T],
                                           [np.zeros(self.shape).T, np.ones(self.shape).T * self.alpha]))


            if with_legend:
                # add a legend in a new axis
                ax_leg = fig.add_axes([0.92, 0.12, 0.04, 0.8])
                from matplotlib.colorbar import ColorbarBase
                from matplotlib import colors
                from matplotlib.colors import Normalize
                cbar = ColorbarBase(ax_leg, cmap=self.mypal.cmap, norm= Normalize(vmin, vmax), orientation='vertical')
                vals = list(np.linspace(vmin, vmax, self.mypal.nb, endpoint=True))
                # limit to 2 decimal places
                vals = [round(val, 2) for val in vals]
                cbar.set_ticks(vals)
                cbar.set_ticklabels(vals)
                cbar.ax.tick_params(labelsize=8)
                cbar.ax.yaxis.set_label_position('left')
                cbar.ax.yaxis.set_ticks_position('right')
                cbar.ax.yaxis.set_tick_params(width=0.5, size=2, direction='in', color='black')

        ax.set_aspect('equal')

        if getdata_im:
            return fig, ax, im
        else:
            return fig, ax

    def fillonecellgrid(self, curscale, loci, locj, force=False):
        """ Fill one cell of the plotted grid """

        cursize = curscale

        if not cursize in self.mygrid.keys():
            return

        curlist = self.mygrid[cursize]
        exists = curlist['done'][loci, locj]

        if exists == 0 or force:
            logging.debug('Computing OpenGL List for '+str(loci)+';' +str(locj) + ' on scale factor '+str(curscale))

            ox = self.origx + self.translx
            oy = self.origy + self.transly
            dx = self.dx
            dy = self.dy

            numlist = int(curlist['mylists'][loci, locj])
            logging.debug('  - creation list{}'.format(numlist))

            try:
                glNewList(numlist, GL_COMPILE)
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

                step = self.gridsize * cursize
                jstart = max(locj * step, 0)
                jend = min(jstart + step, self.nby)
                istart = max(loci * step, 0)
                iend = min(istart + step, self.nbx)

                try:
                    if VERSION_RGB == 1:
                        if self.wolftype != WOLF_ARRAY_FULL_SINGLE:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_uint8(self._tmp_float32, self.rgb, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, np.uint8(self.alpha*255))
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_uint8(self._tmp_float32, self.rgb, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, np.uint8(self.alpha*255))
                        else:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_uint8(self.array, self.rgb, ox, oy, dx, dy, jstart, jend, istart, iend, cursize,
                                                self.nullvalue, np.uint8(self.alpha*255))
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_uint8(self.array, self.rgb, ox, oy, dx, dy, jstart, jend, istart, iend, cursize,
                                                self.nullvalue, np.uint8(self.alpha*255))
                    elif VERSION_RGB == 2:
                        if self.wolftype == WOLF_ARRAY_FULL_INTEGER8:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_int8_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_int8_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                        elif self.wolftype == WOLF_ARRAY_FULL_UINTEGER8:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_uint8_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_uint8_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_int16_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_int16_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                        elif self.wolftype == WOLF_ARRAY_FULL_INTEGER:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_int_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_int_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                        elif self.wolftype == WOLF_ARRAY_FULL_DOUBLE:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_double_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_double_pal(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst))
                        elif self.wolftype not in [WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_HILLSHAPE]:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_pal(self._tmp_float32, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), -1.)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_pal(self._tmp_float32, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), -1.)
                        else:
                            clr_float = self.mypal.colorsflt.copy()
                            clr_float[:,3] = self.alpha
                            if '_hillshade' in self.idx:
                                clr_float[1,3] = 0.

                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:

                                    wolfogl.addme_pal(self.array, clr_float, self.mypal.values, ox, oy, dx, dy, jstart, jend, istart, iend, cursize,
                                                self.nullvalue, self.alpha, int(self.mypal.interval_cst), -1.)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_pal(self.array, clr_float, self.mypal.values, ox, oy, dx, dy, jstart, jend, istart, iend, cursize,
                                                self.nullvalue, self.alpha, int(self.mypal.interval_cst), -1.)

                    elif VERSION_RGB == 3:
                        if self.wolftype == WOLF_ARRAY_FULL_INTEGER8:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_int8_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_int8_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                        elif self.wolftype == WOLF_ARRAY_FULL_UINTEGER8:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_uint8_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_uint8_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                        elif self.wolftype in [WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_int16_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_int16_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                        elif self.wolftype == WOLF_ARRAY_FULL_INTEGER:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_int_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_int_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                        elif self.wolftype == WOLF_ARRAY_FULL_DOUBLE:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_double_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_double_pal_mask(self.array, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), self.array.mask)
                        elif self.wolftype not in [WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_HILLSHAPE]:
                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:
                                    wolfogl.addme_pal_mask(self._tmp_float32, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), -1., self.array.mask)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_pal_mask(self._tmp_float32, self.mypal.colorsflt, self.mypal.values, ox, oy, dx, dy, jstart,
                                                jend, istart, iend, cursize, self.nullvalue, self.alpha, int(self.mypal.interval_cst), -1., self.array.mask)
                        else:
                            clr_float = self.mypal.colorsflt.copy()
                            clr_float[:,3] = self.alpha
                            if '_hillshade' in self.idx:
                                clr_float[1,3] = 0.

                            if self.nbnotnull != self.nbx * self.nby:
                                if self.nbnotnull > 0:

                                    wolfogl.addme_pal_mask(self.array, clr_float, self.mypal.values, ox, oy, dx, dy, jstart, jend, istart, iend, cursize,
                                                self.nullvalue, self.alpha, int(self.mypal.interval_cst), -1., self.array.mask)
                            elif self.nbnotnull > 0:
                                wolfogl.addmeall_pal_mask(self.array, clr_float, self.mypal.values, ox, oy, dx, dy, jstart, jend, istart, iend, cursize,
                                                self.nullvalue, self.alpha, int(self.mypal.interval_cst), -1., self.array.mask)

                except Exception as e:
                    logging.error(repr(e))
                    raise NameError(_('OpenGL error in WolfArray.fillonecellgrid -- Please report this case with the data file and the context in which the error occured'))

                    pass
                glEndList()
            except Exception as e:
                logging.error(repr(e))
                raise NameError(
                    'Opengl in WolfArray_fillonecellgrid -- maybe a conflict with an existing opengl32.dll file - please rename the opengl32.dll in the libs directory and retry')

            curlist['done'][loci, locj] = 1

    def suxsuy_contour(self,
                       filename:str='',
                       abs:bool=False,
                       one_vec_if_ml:bool = True) -> tuple[list[int,int],
                                                           list[int,int],
                                                           vector | zone,
                                                           bool]:
        """
        The borders are computed on basis of the current *mask*

        :param filename: if provided, write 'sux', 'sux' and 'xy' files
        :param abs: add translation coordinates (Global World Coordinates)

        :return: indicesX, indicesY, contourgen, interior

        indicesX : list of coupled indices along X - vertical border - 1-based like Fortran
        indicesY : list of coupled indices along Y - horizontal border - 1-based like Fortran
        contourgen : external contour
        interior : if False, contour is unique ; if True, interior contours exist -> interior parts are merged
        """

        # Calcul des bords libres SUX, SUY
        indicesX=[]
        indicesY=[]

        locls=[]

        dx = self.dx
        dy = self.dy

        translx = self.origx
        transly = self.origy
        if abs:
            translx += self.translx
            transly += self.transly

        horiz = np.where(self.array.mask[0:self.nbx-1,0:self.nby-1] ^ self.array.mask[1:self.nbx,0:self.nby-1])
        vert  = np.where(self.array.mask[0:self.nbx-1,0:self.nby-1] ^ self.array.mask[0:self.nbx-1,1:self.nby])

        for i,j in zip(horiz[0],horiz[1]):
            x1 = float(i+1) * dx + translx
            y1 = float(j+1) * dy + transly
            indicesX.append([i+2, j+1])
            locls.append(LineString([[x1,y1-dy],[x1,y1]]))

        for i,j in zip(vert[0],vert[1]):
            x1 = float(i+1) * dx + translx
            y1 = float(j+1) * dy + transly
            indicesY.append([i+1, j+2])
            locls.append(LineString([[x1-dx,y1],[x1,y1]]))

        if not locls:
            raise Exception(_("I can't detect any contour. Is this right ?"))

        interior=False
        # generate contour from partial linestring --> using Shapely to do that !
        contour = linemerge(locls)

        if contour.geom_type == 'LineString':
            # All is fine - only one vector
            xy = np.asarray(contour.coords)
            nb = len(xy)
            contourgen = vector(name='external border')
            for x,y in xy:
                contourgen.add_vertex(wolfvertex(x,y))

        elif contour.geom_type == 'MultiLineString':
            if one_vec_if_ml:
                interior=True
                # Multiple vectors --> combine

                # searching the longest LineString -> external contour
                contour:MultiLineString
                lenghts=[mygeom.length  for mygeom in contour.geoms]
                ind = np.argmax(lenghts)

                xyall=[np.column_stack([np.asarray(mygeom.coords),np.zeros(len(mygeom.coords))]) for mygeom in contour.geoms]

                # coordinates of the longest LineString
                xy = xyall[ind]

                for i in range(len(xyall)):
                    if i!=ind:
                        # Concatenate local LineString to the external contour + 2 connection segments
                        # Z coordinate is set to 1. -> will be used to check it after and change "in_use" property
                        xy=np.concatenate([xy,
                                        np.asarray([xyall[i][0,0],xyall[i][0,1],1.]).reshape([1,3]),
                                        xyall[i][1:],
                                        np.asarray([xy[0,0],xy[0,1],1.]).reshape([1,3])])

                nb = len(xy)
                contourgen = vector(name='external border')
                for x,y,z in xy:
                    contourgen.add_vertex(wolfvertex(x,y,z))
                    contourgen.myvertices[-1].in_use = z == 0. # the new vertex is related to a connection segment --> ignore for numerical precision in intersection operations/calculations
            else:
                contourgen = zone(name = 'contour')

                for cur_ls in contour.geoms:
                    xy = np.asarray(cur_ls.coords)
                    nb = len(xy)

                    cur_vec = vector(name='external border')
                    for x,y in xy:
                        cur_vec.add_vertex(wolfvertex(x,y))

                    contourgen.add_vector(cur_vec, forceparent=True)

        else:
            contourgen = None
            err = _(f"Unsupported Shapely contour result: {contour.geom_type}")
            logging.warning(err)

        if filename != '':

            # There is some knowledge about SUX, SUY, XY files there:
            # https://gitlab.uliege.be/HECE/wolf-interface/-/blob/master/InterfaceVB6/FrmAffichage.frm

            with open(filename+'.sux','w') as f:
                np.savetxt(f,np.asarray(indicesX), delimiter=',', fmt='%u,%u')

            with open(filename + '.suy', 'w') as f:
                np.savetxt(f, np.asarray(indicesY), delimiter=',', fmt='%u,%u')

            with open(filename + '.xy', 'w') as f:
                f.write('{}\n'.format(nb))
                # FIXME Stef commented that. Maybe wrong !!!
                # xy[:,0]-=translx-self.origx
                # xy[:,1]-=transly-self.origy
                np.savetxt(f, xy[:,:2], delimiter='\t')

        return indicesX,indicesY,contourgen,interior

    def imshow(self, figax:tuple[Figure, Axis] = None,
               cmap:Colormap = None, step_ticks=100.) -> tuple[Figure, Axis]:
        """
        Create Matplotlib image from WolfArray
        """

        # Use figax if passed as argument
        if figax is None:
            fig,ax = plt.subplots(1,1)
        else:
            fig,ax = figax

        bounds = self.get_bounds()

        if cmap is None:
            # update local colors if not already done
            if self.rgb is None:
                self.updatepalette(1)

            # Pointing RGB
            colors = self.rgb
            colors[self.array.mask,3] = 0.
            # Plot
            colors = colors.swapaxes(0,1)
            ax.imshow(colors, origin='lower')

        else:
            # Full scale image values
            vals = self.array.data
            alpha = np.zeros(vals.shape)
            alpha[~ self.array.mask] = 1.
            # Plot
            vals = vals.swapaxes(0,1)
            alpha = alpha.swapaxes(0,1)
            ax.imshow(vals, origin='lower', cmap=cmap, alpha=alpha)

        ax.set_aspect('equal')

        x_start = (bounds[0][0] // step_ticks) * step_ticks
        x_end   = (bounds[0][1] // step_ticks) * step_ticks

        y_start = (bounds[1][0] // step_ticks) * step_ticks
        y_end   = (bounds[1][1] // step_ticks) * step_ticks

        x_pos = np.arange(x_start, x_end+.0001, step_ticks)
        y_pos = np.arange(y_start, y_end+.0001, step_ticks)

        i = [self.get_ij_from_xy(x, 0.)[0] for x in x_pos]
        j = [self.get_ij_from_xy(0., y)[1] for y in y_pos]

        ax.set_xticks(i)
        ax.set_xticklabels(x_pos, rotation = 30)

        ax.set_yticks(j)
        ax.set_yticklabels(y_pos)

        return fig,ax

    def set_array_from_numpy(self, array:np.ndarray, nullvalue:float = None):
        """
        Set array from numpy array
        """
        if array.shape != (self.nbx, self.nby):
            logging.warning(f"Array shape {array.shape} is not compatible with WolfArray shape {self.nbx, self.nby}")
            return

        def wolftype_from_npz(curarray:np.ndarray):
            if curarray.dtype == np.float64:
                return WOLF_ARRAY_FULL_DOUBLE
            elif curarray.dtype == np.float32:
                return WOLF_ARRAY_FULL_SINGLE
            elif curarray.dtype == np.int32:
                return WOLF_ARRAY_FULL_INTEGER
            elif curarray.dtype == np.int8:
                return WOLF_ARRAY_FULL_INTEGER8
            elif curarray.dtype == np.uint8:
                return WOLF_ARRAY_FULL_UINTEGER8

        self.array = np.ma.array(array.copy())
        self.wolftype = wolftype_from_npz(array)

        if nullvalue is not None:
            self.nullvalue = nullvalue
        self.mask_data(self.nullvalue)
        self.reset_plot()

    def nullify_border(self, width:int = 1):
        """
        Set border to nullvalue
        """
        self.array.data[:width,:] = self.nullvalue
        self.array.data[-width:,:] = self.nullvalue
        self.array.data[:,:width] = self.nullvalue
        self.array.data[:,-width:] = self.nullvalue

        self.array.mask[:width,:] = True
        self.array.mask[-width:,:] = True
        self.array.mask[:,:width] = True
        self.array.mask[:,-width:] = True

    def as_WolfArray(self, abs:bool=True) -> "WolfArray":
        """
        Return a WolfArray object from this WolfArray
        """

        NewArray = WolfArray(mold=self)

        if abs:
            NewArray.origx += self.translx
            NewArray.origy += self.transly
            NewArray.translx = 0.
            NewArray.transly = 0.

        return NewArray

    def get_unique_values(self):
        """
        Return unique values in the array
        """

        unique = np.ma.unique(self.array)

        while unique[-1] is np.ma.masked and len(unique) > 1:
            unique = unique[:-1]

        return unique

    def map_values(self, keys_vals:dict, default:float=None):
        """
        Mapping array values to new values defined by a dictionnary.

        First, check if all values are in keys_vals. If not, set to default.
        If default is None, set to nullvalue.

        :param keys_vals: dictionary of values to map
        :param default: default value if key not found
        """

        vals = self.get_unique_values()

        def_keys = []
        for val in vals:
            if val not in keys_vals:
                logging.warning(_(f"Value {val} not in keys_vals -- Will be set to default or NullValue"))
                def_keys.append(val)
                continue

        for key, val in keys_vals.items():
            self.array.data[self.array.data == key] = val

        if default is None:
            default = self.nullvalue

        for key in def_keys:
            self.array.data[self.array.data == key] = default

        self.mask_data(self.nullvalue)

        self.reset_plot()

    @classmethod
    def from_other_epsg_coo(cls,
                            input_raster_path:str,
                            input_srs='EPSG:3812',
                            output_srs='EPSG:31370',
                            resampling_method=gdal.GRA_Bilinear,
                            xRes:float=0.5, yRes:float=0.5):
        """
        Reprojects and resamples a raster file from an other EPSG coordinates and return it as a WolfArray.

        :param input_raster_path: The path to the input raster file.
        :type input_raster_path: str
        :param input_srs: The input spatial reference system (SRS) in the format 'EPSG:XXXX'. Defaults to Lambert 2008 'EPSG:3812'.
        :type input_srs: str
        :param output_srs: The output spatial reference system (SRS) in the format 'EPSG:XXXX'. Defaults to Belgian Lambert 72 'EPSG:31370'.
        :type output_srs: str
        :param resampling_method: The resampling method to use. Defaults to gdal.GRA_Bilinear. Resampling method can be chosen among the gdal GRA_*
        constants (gdal.GRA_Average; gdal.GRA_Bilinear; gdal.GRA_Cubic; gdal.GRA_CubicSpline;
        gdal.GRA_Lanczos; gdal.GRA_Mode; gdal.GRA_NearestNeighbour)
        :type resampling_method: int
        :param xRes: The desired output resolution in the x direction. Defaults to 0.5.
        :type xRes (float): float
        :param yRes: The desired output resolution in the y direction. Defaults to 0.5.
        :type yRes (float): float

        :raises AssertionError: If the input or output raster file is not a GeoTIFF file.
        :raises RuntimeError: If the input raster file cannot be opened.
        :raises PermissionError: If there is a permission error while trying to delete the output raster file.
        :raises Exception: If an unexpected error occurs while trying to delete the output raster file.
        :raises RuntimeError: If the reprojection fails for the input raster file.

        :return: WolfArray
        """

        #sanitize input
        input_raster_path = str(input_raster_path)
        input_srs = str(input_srs)
        output_srs = str(output_srs)

        assert resampling_method in [gdal.GRA_Average, gdal.GRA_Bilinear, gdal.GRA_Cubic, gdal.GRA_CubicSpline, gdal.GRA_Lanczos, gdal.GRA_Mode, gdal.GRA_NearestNeighbour], "Invalid resampling method"

        # Define temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            output_raster_path = os.path.join(temp_dir, "Array_72.tif")
            reproject_and_resample_raster(input_raster_path, output_raster_path, input_srs, output_srs, resampling_method, xRes, yRes)
            Array3 = WolfArray(output_raster_path, nullvalue=-9999)
        return Array3

    def reproject(self, output_epsg:int,
                  resampling_method=gdal.GRA_Bilinear,
                  ) -> "WolfArray":
        """
        Reprojects and resamples the WolfArray to a new EPSG coordinate system.

        :param output_epsg: The output EPSG code for the desired coordinate system.
        :type output_epsg: int
        :param resampling_method: The resampling method to use. Defaults to gdal.GRA_Bilinear. Resampling method can be chosen among the gdal GRA_*
        constants (gdal.GRA_Average; gdal.GRA_Bilinear; gdal.GRA_Cubic; gdal.GRA_CubicSpline;
        gdal.GRA_Lanczos; gdal.GRA_Mode; gdal.GRA_NearestNeighbour)
        :type resampling_method: int
        :return: WolfArray
        """

        assert isinstance(output_epsg, int), "output_epsg must be an integer"
        assert resampling_method in [gdal.GRA_Average, gdal.GRA_Bilinear, gdal.GRA_Cubic, gdal.GRA_CubicSpline, gdal.GRA_Lanczos, gdal.GRA_Mode, gdal.GRA_NearestNeighbour], "Invalid resampling method"

        # Define temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_all(os.path.join(temp_dir, "Array_input.tif"))
            output_raster_path = os.path.join(temp_dir, "Array_reprojected.tif")
            reproject_and_resample_raster(os.path.join(temp_dir, "Array_input.tif"),
                                          output_raster_path,
                                          f'EPSG:{self.epsg}',
                                          f'EPSG:{output_epsg}',
                                          resampling_method=resampling_method)

            Array3 = WolfArray(output_raster_path, nullvalue=-9999)
        return Array3

    def contour(self, levels:Union[int, list[float]] = 10) -> Zones:
        """ Compute contour lines """

        if isinstance(levels, int):
            levels = np.linspace(self.array.min(), self.array.max(), levels)

        x, y = self.meshgrid()
        cs = plt.contour(x, y, self.array, levels=levels)

        zones = Zones(idx = self.idx + '_contour', mapviewer = self.get_mapviewer())

        if hasattr(cs, 'collections'):
            # MATPLOTLIB <=3.8
            logging.debug('MATPLOTLIB <=3.8')
            logging.debug(_('DEPRECATED: MATPLOTLIB <=3.8 -- You should consider upgrading to a more recent version of Matplotlib'))
            logging.debug(_('Take care Basemap may not be available in recent versions of mpl_toolkits'))
            for collection, level in zip(cs.collections, cs.levels):
                zone_level = zone(name=f'Contour {level}')
                for idx, path in enumerate(collection.get_paths()):
                    vector_level = vector(name=f'Contour {level} - {idx}')
                    zone_level.add_vector(vector_level, forceparent=True)
                    for vertices in path.to_polygons(closed_only=False):
                        for vertex in vertices:
                            vector_level.add_vertex(wolfvertex(vertex[0], vertex[1]))
                zones.add_zone(zone_level, forceparent=True)
        else:
            # MATPLOTLIB >3.8
            logging.debug('MATPLOTLIB >3.8')
            for path, level in zip(cs.get_paths(), cs.levels):
                zone_level = zone(name=f'Contour {level}')
                for idx, vertices in enumerate(path.to_polygons(closed_only=False)):
                    vector_level = vector(name=f'Contour {level} - {idx}')
                    zone_level.add_vector(vector_level, forceparent=True)
                    for vertex in vertices:
                        vector_level.add_vertex(wolfvertex(vertex[0], vertex[1]))
                zones.add_zone(zone_level, forceparent=True)

        return zones

    def inpaint(self, mask_array:"WolfArray" = None, test_array:"WolfArray" = None,
                ignore_last:int = 1, multiprocess:bool = True):
        """ InPaintaing holes in the array

        :param mask_array: where computation is done
        :param test_array: used in test -- interpolation is accepted if new value is over test_array
        :param ignore_last: number of last patches to ignore
        :param multiprocess: use multiprocess for inpainting
        """

        from .eikonal import inpaint_array

        if mask_array is None:
            mask_array = self.array.mask
        elif isinstance(mask_array, WolfArray):
            mask_array = mask_array.array.data

        if test_array is None:
            test_array = np.ones(self.array.data.shape) * self.array.data.min()
        elif isinstance(test_array, WolfArray):
            test_array = test_array.array.data

        time, wl_np, wd_np = inpaint_array(self.array.data,
                                            mask_array,
                                            test_array,
                                            ignore_last_patches= ignore_last,
                                            dx = self.dx,
                                            dy = self.dy,
                                            NoDataValue = self.nullvalue,
                                            inplace=True,
                                            multiprocess= multiprocess)

        wd = WolfArray(mold=self)
        wd.array[:,:] = wd_np[:,:]
        wd.mask_data(self.nullvalue)

        wl = self

        self.mask_data(self.nullvalue)
        self.reset_plot()
        return time, wl, wd

    def _inpaint_waterlevel_dem_dtm(self, dem:"WolfArray", dtm:"WolfArray",
                                    ignore_last:int = 1, use_fortran:bool = False,
                                    multiprocess:bool = True):
        """ InPaintaing waterlevel holes in the array.

        We use DEM and DTM to mask and constraint the inpainting process.

        :param dem: Digital Elevation Model (same as simulation model)
        :param dtm: Digital Terrain Model
        :param ignore_last: number of last patches to ignore
        :param use_fortran: use Fortran inpainting code
        :param multiprocess: use multiprocess for inpainting
        """

        if use_fortran:
            import shutil
            from tempfile import TemporaryDirectory
            # check if hoels.exe is available in PATH
            if shutil.which('holes.exe') is None:
                logging.error(_('holes.exe not found in PATH'))
                logging.info(_('We use the Python version of inpainting'))
                use_fortran = False

            else:
                with TemporaryDirectory() as tmpdirname:
                    # create mask from DEM, DTM and WL

                    mask = self._create_building_holes_dem_dtm(dem, dtm, ignore_last)

                    # save mask and dtm to temporary files
                    locdir = Path(tmpdirname)
                    wl_name = locdir / 'array.bin'
                    mask_name = locdir / 'mask.bin'
                    dtm_name = locdir / 'dtm.bin'

                    mask.write_all(mask_name)
                    dtm.write_all(dtm_name)

                    oldname = self.filename
                    self.write_all(wl_name)
                    self.filename = oldname

                    # call holes.exe
                    olddir = os.getcwd()

                    # change to temporary directory
                    os.chdir(locdir)
                    shell_command = f'holes.exe inpaint in={wl_name} mask={mask_name} dem={dtm_name} avoid_last={ignore_last} out=temp'
                    logging.info(shell_command)
                    logging.info('Inpainting holes using holes.exe')
                    os.system(shell_command)
                    logging.info('Done - reading inpainted array')

                    # read inpainted array
                    wl = WolfArray(locdir / 'temp_combl.tif')
                    wd = WolfArray(locdir / 'temp_h.tif')

                    wd.array[wd.array < 0.] = 0.
                    wd.mask_data(0.)

                    os.chdir(olddir)

                    self.array.data[:,:] = wl.array.data[:,:]

                    time = None

        if not use_fortran:

            from .eikonal import inpaint_waterlevel

            time, wl_np, wd_np = inpaint_waterlevel(self.array.data,
                                                dem.array.data,
                                                dtm.array.data,
                                                ignore_last_patches= ignore_last,
                                                dx = self.dx,
                                                dy = self.dy,
                                                NoDataValue = self.nullvalue,
                                                inplace=True,
                                                multiprocess= multiprocess)

            wd = WolfArray(mold=self)
            wd.array[:,:] = wd_np[:,:]
            wd.mask_data(self.nullvalue)

            wl = self

        self.mask_data(self.nullvalue)
        self.reset_plot()
        return time, wl, wd

    def count_holes(self, mask:"WolfArray" = None):
        """ Count holes in the array """
        from .eikonal import count_holes

        if mask is None:
            mask = self.array.mask
        elif isinstance(mask, WolfArray):
            mask = mask.array.data

        return count_holes(mask)

    def select_holes(self, mask:"WolfArray" = None, ignore_last:int = 1):
        """ Select holes in the array """

        if mask is None:
            mask = self.array.mask
        elif isinstance(mask, WolfArray):
            mask = mask.array.data

        labels, numfeatures = label(mask)

        # count cells in holes
        nb_cells = np.bincount(labels.ravel())

        # sort by number of cells
        idx = np.argsort(nb_cells)

        for i in range(ignore_last):
            labels[labels == idx[-1-i]] = 0

        # select holes but ignoring last ones
        ij = np.argwhere(labels)

        # Convert i,j to x,y

        xy = self.ij2xy_np(ij)

        self.SelectionData.myselection = list(xy)
        self.SelectionData.update_nb_nodes_selection()

    def create_mask_holes(self, ignore_last:int = 1) -> "WolfArray":
        """ Select holes in the array and create a new aray """

        labels, numfeatures = label(self.array.mask)

        # count cells in holes
        nb_cells = np.bincount(labels.ravel())

        # sort by number of cells
        idx = np.argsort(nb_cells)

        for i in range(ignore_last):
            labels[labels == idx[-1-i]] = 0

        newarray = WolfArray(mold=self)
        # newarray.allocate_ressources()
        newarray.array.data[:,:] = labels
        newarray.array.mask[:,:] = ~labels.astype(bool)
        newarray.set_nullvalue_in_mask()

        return newarray

    def create_binary_mask(self, threshold:float = 0.) -> "WolfArray":
        """ Create a binary mask from the array """

        newarray = WolfArray(mold=self)
        newarray.array.data[:,:] = self.array.data > threshold
        newarray.array.mask[:,:] = ~newarray.array.data.astype(bool)
        newarray.set_nullvalue_in_mask()

        return newarray

    def fill_holes_with_value(self, value:float, mask:"WolfArray" = None, ignore_last:int = 1):
        """ Fill holes in the array with a value """

        if mask is None:
            mask = self.array.mask

        labels, numfeatures = label(mask)

        # count cells in holes
        nb_cells = np.bincount(labels.ravel())

        # sort by number of cells
        idx = np.argsort(nb_cells)

        for i in range(ignore_last):
            labels[labels == idx[-1-i]] = 0

        self.array.data[labels > 0] = value
        self.array.mask[labels > 0] = False # unmask filled data

    def fill_holes_with_value_if_intersects(self, value:float,
                                            vects:list[vector] | Zones,
                                            method:Literal['matplotlib','shapely_strict', 'shapely'] = 'shapely_strict',
                                            buffer:float = 0.):
        """ Fill holes in the array with a value if it intersects with the mask """

        if isinstance(vects, Zones):
            vects = vects.concatenate_all_vectors()

        for vec in vects:
            self._fill_holes_with_value_if_intersects(value, vec, method, buffer)
        # list(map(self._fill_holes_with_value_if_intersects, [value]*len(vects), vects, [method]*len(vects), [buffer]*len(vects))) # parallel version

    def _fill_holes_with_value_if_intersects(self, value:float,
                                            vect:vector,
                                            method:Literal['matplotlib','shapely_strict', 'shapely'] = 'shapely_strict',
                                            buffer:float = 0.) -> "WolfArray":

        if buffer > 0.:
            # As we use a buffer, we check the intersction with the buffer...
            if self.intersects_polygon(vect, method=method, buffer=buffer):
                # ...but we fill the original polygon, not the buffered one
                ij = self.get_ij_inside_polygon(vect, method=method, usemask=False)
                self.array.data[ij[:,0], ij[:,1]] = value
                self.array.mask[ij[:,0], ij[:,1]] = False
        else:
            ij = self.get_ij_inside_polygon(vect, method=method, buffer=buffer, usemask=False)

            if ij.size[0] > 0:
                self.array.data[ij[:,0], ij[:,1]] = value
                self.array.mask[ij[:,0], ij[:,1]] = False

    def _create_building_holes_dem_dtm(self, dem:"WolfArray", dtm:"WolfArray", ignore_last:int = 1) -> "WolfArray":
        """ Select holes in the array and create a new aray """

        buildings = dem - dtm
        buildings.array[buildings.array < 0.] = 0.
        buildings.array[buildings.array > 0.] = dtm.array[buildings.array > 0.]
        buildings.array[buildings.array == 0.] = dem.array.max() + 1.

        return buildings

    @classmethod
    def merge(cls, others:list["WolfArrayMB"], abs:bool=True, copy:bool = True) -> "WolfArray":
        """
        Merge several WolfArray into a single WolfArray

        :param others: list of WolfArray to merge
        :param abs: if True -> Global World Coordinates
        :param copy: if True -> copy data (**Not necessary** if data header CAN BE modified. It can be save memory)
        """

        newMBArray = WolfArrayMB()

        for curarray in others:
            newMBArray.add_block(curarray, force_idx=True, copyarray=copy)

        newMBArray.set_header_from_added_blocks()

        return newMBArray.as_WolfArray(abs=abs)


class WolfArrayMB(WolfArray):
    """
    Matrice multiblocks

    Les blocs (objets WolfArray) sont stockés dans un dictionnaire "myblocks"
    """

    # Each block is denoted by a block key (see function `getkeyblock`).
    myblocks: dict[str, WolfArray]

    def __init__(self, fname=None, mold=None, masknull=True, crop=None, whichtype=WOLF_ARRAY_MB_SINGLE, preload=True,
                 create=False, mapviewer=None, nullvalue=0, srcheader=None):

        super().__init__(fname, mold, masknull, crop, whichtype, preload, create, mapviewer, nullvalue, srcheader)

        self.mngselection = SelectionDataMB(self)
        self._active_blocks = 0

        if self.myblocks is None:
            self.myblocks = {}

    @property
    def zmin(self) -> float:
        """ Return the minimum value of the array """

        zmin = np.min([curblock.zmin for curblock in self.myblocks.values()])

        return zmin

    @property
    def zmax(self) -> float:
        """ Return the maximum value of the array """

        zmax = np.max([curblock.zmax for curblock in self.myblocks.values()])

        return zmax

    @property
    def zmin_global(self) -> float:
        """ Return the minimum value of the array """

        zmin = np.min([curblock.zmin_global for curblock in self.myblocks.values()])

        return zmin

    @property
    def zmax_global(self) -> float:
        """ Return the maximum value of the array """

        zmax = np.max([curblock.zmax_global for curblock in self.myblocks.values()])

        return zmax


    def contour(self, levels:Union[int, list[float]] = 10) -> Zones:
        """ Compute contour lines """

        tmp = self.as_WolfArray()
        return tmp.contour(levels)

    def extract_selection(self):
        """ Extract the current selection """

        newarrays = []

        for curblock in self.myblocks.values():
            newblock = curblock.SelectionData.get_newarray()

            if newblock is not None:
                newarrays.append(newblock)

        if len(newarrays) == 0:
            logging.warning(_('No selection to extract'))
            return None

        newMBarray = WolfArrayMB()
        for newarray in newarrays:
            newMBarray.add_block(newarray, force_idx=True)

        mapviewer = self.get_mapviewer()

        if mapviewer is not None:
            mapviewer.add_object('array', newobj = newarray, ToCheck = True, id = self.idx + '_extracted')

    @property
    def nullvalue(self) -> float:
        """ Return the null value """

        return self._nullvalue

    @nullvalue.setter
    def nullvalue(self, value:float):
        """ Set the null value """

        self._nullvalue = value

        if self.myblocks is not None:
            for curblock in self.myblocks.values():
                curblock.nullvalue = value

    def add_ops_sel(self):
        """ Add operations and selection manager to all blocks """

        super().add_ops_sel()

        if self.myblocks is None:
            self.myblocks = {}

        for curblock in self.myblocks.values():
            curblock.add_ops_sel()

    def filter_zone(self, set_null:bool = False):
        """
        Filtre des zones et conservation de celles pour lesquelles des
        mailles sont sélectionnées

        """

        for curblock in self.myblocks.values():
            curblock.filter_zone(set_null, reset_plot=False)

        self.reset_plot()

    def labelling(self):
        """
        Labelling of the array using Scipy

        """

        for curblock in self.myblocks.values():
            curblock.labelling(reset_plot=False)

        self.reset_plot()

    def interpolate_on_polygon(self, working_vector: vector,
                               method:Literal["nearest", "linear", "cubic"]="linear",
                               keep:Literal['all', 'below', 'above'] = 'all'):
        """
        Interpolation sous un polygone

        L'interpolation a lieu :
          - uniquement dans les mailles sélectionnées si elles existent
          - dans les mailles contenues dans le polygone sinon

        On utilise ensuite "griddata" pour interpoler les altitudes des mailles
        depuis les vertices 3D du polygone
        """

        for curblock in self.myblocks.values():
            curblock.interpolate_on_polygon(working_vector, method, keep)

    def interpolate_on_polygons(self, working_zone: zone,
                                method:Literal["nearest", "linear", "cubic"]="linear",
                                keep:Literal['all', 'below', 'above'] = 'all'):

        for curvector in working_zone.myvectors:
            self.interpolate_on_polygon(curvector, method, keep)

    def interpolate_on_polyline(self, working_vector:vector, usemask=True):
        """
        Interpolation sous une polyligne

        L'interpolation a lieu :
          - uniquement dans les mailles sélectionnées si elles existent
          - dans les mailles sous la polyligne sinon

        On utilise ensuite "interpolate" de shapely pour interpoler les altitudes des mailles
        depuis les vertices 3D de la polyligne
        """

        for curblock in self.myblocks.values():
            curblock.interpolate_on_polyline(working_vector, usemask)

    def interpolate_on_polylines(self, working_zone:zone, usemask=True):
        """ Interpolation sous les polylignes d'une même zone """

        for curvec in working_zone.myvectors:
            self.interpolate_on_polyline(curvec, usemask)

    def check_bounds_ij(self, i:int, j:int):
        """Check if i and j are inside the array bounds"""

        x,y = self.get_xy_from_ij(i,j)
        return self.check_bounds_xy(x,y)

    def check_bounds_xy(self, x:float, y:float):
        """Check if i and j are inside the array bounds"""

        xmin, xmax, ymin, ymax = self.get_bounds()

        return x>=xmin and x<=xmax and y>=ymin and y<=ymax

    def __getitem__(self, block_key:Union[int,str]) -> WolfArray:
        """Access a block of this multi-blocks array."""
        if isinstance(block_key,int):
            _key = getkeyblock(block_key)
        else:
            _key = block_key

        if _key in self.myblocks.keys():
            return self.myblocks[_key]
        else:
            return None

    def add_block(self, arr: WolfArray, force_idx:bool=False, copyarray=False):
        """
        Adds a properly configured block this multiblock.

        Do not forget to call "set_header_from_added_blocks" after adding all blocks.

        :param arr: The block to add.
        :param force_idx: If True, the index/key will be set on `arr`. If False, the index/key must already be set on `arr`.
        """

        if copyarray:
            arr = WolfArray(mold=arr, nullvalue=arr.nullvalue)
            force_idx = True

        if force_idx:
            arr.idx = getkeyblock(len(self.myblocks))
        else:
            assert arr.idx is not None and type(arr.idx) == str and arr.idx.strip() != '', f"The block index/key is wrong {arr.idx}"
            assert arr.idx not in self.myblocks, "You can't have the same block twice"
            pos = len(self.myblocks)
            posidx = decodekeyblock(arr.idx, False)
            assert pos == posidx, f"The block index/key is wrong {arr.idx}"

        self.myblocks[arr.idx] = arr

        arr.isblock = True
        arr.blockindex = len(self.myblocks) - 1


    def share_palette(self):
        """Partage de la palette de couleurs entre matrices liées"""
        for cur in self.linkedarrays:
            if id(cur.mypal)!= id(self.mypal):
                cur.mypal = self.mypal
                cur.link_palette()

    def copy_mask(self, source:"WolfArrayMB", forcenullvalue:bool= False):
        """ Copy the mask of two arrays """

        if isinstance(self, type(source)):
            if self.check_consistency(source):
                i=0
                for curblock, curblockother in zip(self.myblocks.values(),source.myblocks.values()):
                    curblock.copy_mask(curblockother, forcenullvalue)
                    i+=1
                self.reset_plot()
        else:
            logging.warning(_('Copy mask not supported between different types of arrays'))

    def count(self):
        """ Count the number of not null cells """

        self.nbnotnull = 0
        for i in range(self.nb_blocks):
            curblock = self.myblocks[getkeyblock(i)]
            curarray = curblock.array
            nbnotnull = curarray.count()
            curblock.nbnotnull = nbnotnull
            self.nbnotnull += nbnotnull

    def check_plot(self):
        """ Check plot and apply to each block """

        self.plotted = True
        self.mimic_plotdata()

        if not self.loaded and self.filename != '':
            if os.path.exists(self.filename):
                self.read_data()
                if self.masknull:
                    self.mask_data(self.nullvalue)

                if VERSION_RGB==1 :
                    if self.rgb is None:
                        self.rgb = np.ones((self.nbx, self.nby, 4), order='F', dtype=np.integer)

                self.updatepalette(0)
                self.loaded = True
            else:
                raise Exception(_(f"Trying to load an array that doesn't exist ({self.filename})"))
        else:
            logging.info(_('Array already loaded'))

    def uncheck_plot(self, unload:bool=True, forceresetOGL:bool=False, askquestion:bool=True):
        """ Uncheck plot and apply to each block """

        self.plotted = False
        self.mimic_plotdata()

        if unload and self.filename != '':
            if askquestion and not forceresetOGL:
                if self.wx_exists:
                    dlg = wx.MessageDialog(None, _('Do you want to reset OpenGL lists?'), style=wx.YES_NO)
                    ret = dlg.ShowModal()
                    if ret == wx.ID_YES:
                        forceresetOGL = True
                else:
                    forceresetOGL = True

            for curblock in self.myblocks.values():
                curblock.uncheck_plot(unload, forceresetOGL, askquestion=False)
                if VERSION_RGB==1 : self.rgb = None

            self.myblocks = {}
            self.loaded = False
        else:
            logging.info(_('Array not unloaded'))

    def mask_data(self, value):
        """ Mask cells where values are equal to `value`"""

        if self.wolftype in [WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER16, WOLF_ARRAY_FULL_INTEGER16_2]:
            value=int(value)

        if value is not None:

            for curblock in self.myblocks.values():
                curarray = curblock.array

                if isinstance(curarray.mask, np.bool_):
                    # mask is not an array, but a single boolean value
                    # we must create a new mask array
                    if np.isnan(value) or math.isnan(value):
                        curarray.mask = np.isnan(curarray.data)
                    else:
                        curarray.mask = curarray.data == value
                else:
                    # Copy to prevent unlinking the mask (see `mask_reset`)
                    if np.isnan(value) or math.isnan(value):
                        np.copyto(curarray.mask, np.isnan(curarray.data))
                    else:
                        np.copyto(curarray.mask, curarray.data == value)

            self.count()

        # for i in range(self.nb_blocks):
        #     curblock = self.myblocks[getkeyblock(i)]
        #     curarray = curblock.array
        #     curarray.mask = curarray.data == value

        # self.count()

    def mask_union(self, source:"WolfArrayMB"):
        """
        Union of the masks of two arrays

        Applying for each block iteratively.
        """
        if isinstance(self, type(source)):
            if self.check_consistency(source):
                i=0
                for curblock, curblockother in zip(self.myblocks.values(),source.myblocks.values()):
                    curblock.mask_union(curblockother)
                    i+=1
                self.reset_plot()

    def read_data(self):
        """ Lecture du tableau en binaire """

        with open(self.filename, 'rb') as f:
            for i in range(self.nb_blocks):

                if self.wolftype == WOLF_ARRAY_MB_SINGLE:
                    curblock = WolfArray(whichtype=WOLF_ARRAY_FULL_SINGLE, srcheader=self.head_blocks[getkeyblock(i)])
                elif self.wolftype == WOLF_ARRAY_MB_INTEGER:
                    curblock = WolfArray(whichtype=WOLF_ARRAY_FULL_INTEGER)

                curblock.isblock = True
                curblock.blockindex = i
                curblock.idx = getkeyblock(i)

                curblock._read_binary_data(f)

                self.myblocks[getkeyblock(i)] = curblock

    def write_array(self):
        """ Ecriture du tableau en binaire """
        with open(self.filename, 'wb') as f:
            for i in range(self.nb_blocks):
                curarray = self.myblocks[getkeyblock(i)]
                f.write(curarray.array.data.transpose().tobytes())

    def get_ij_from_xy(self, x:float, y:float, z:float=0., scale:float=1., aswolf:bool=False, abs:bool=True, which_block:int=1):
        """
        alias for get_ij_from_xy for the block `which_block

        :param x: x coordinate
        :param y: y coordinate
        :param z: z coordinate
        :param scale: scale factor
        :param aswolf: if True, then the indices are 1-based like Fortran, otherwise 0-based like Python
        :param abs: if True, then the translation is taken into account
        :param which_block: block index 1-based
        """
        return self.myblocks[getkeyblock(which_block, False)].get_ij_from_xy(x, y, z, scale, aswolf, abs)

    def get_values_as_wolf(self, i:int, j:int, which_block:int=1):
        """
        Return the value at indices (i,j) of the block `which_block.

        :param i: i index
        :param j: j index
        :param which_block: block index 1-based
        """
        h = np.nan
        if which_block == 0:
            logging.warning("Block index is probably 0-based. It should be 1-based.")
            return h

        keyblock = getkeyblock(which_block, False)
        curblock = self.myblocks[keyblock]

        nbx = curblock.nbx
        nby = curblock.nby

        if (i > 0 and i <= nbx and j > 0 and j <= nby):
            h = curblock.array[i - 1, j - 1]

        return h

    def get_value(self, x:float, y:float, abs:bool=True):
        """
        Read the value at world coordinate (x,y). if `abs` is
        given, then the translation is is taken into account.

        If no block covers the coordinate, then np.nan is returned
        If several blocks cover the given coordinate then the first
        match is returned (and thus, the others are ignored).

        :param x: x coordinate
        :param y: y coordinate
        :param abs: if True, then the translation is taken into account

        :return: the value at (x,y) or np.nan if no block covers the coordinate
        """

        h = np.nan
        for curblock in self.myblocks.values():
            curblock: WolfArray
            nbx = curblock.nbx
            nby = curblock.nby

            i, j = curblock.get_ij_from_xy(x, y, abs=abs)

            if (i > 0 and i <= nbx and j > 0 and j <= nby):
                h = curblock.array[i, j]
                if not curblock.array.mask[i, j]:
                    break

        return h

    def get_xy_from_ij(self, i:int, j:int, which_block:int, aswolf:bool=False, abs:bool=True):
        """
        Return the world coordinates (x,y) of the indices (i,j) of the block `which_block.

        :param i: i index -- 1-based like Fortran or 0-based like Python, see 'aswolf' parameter
        :param j: j index -- 1-based like Fortran or 0-based like Python, see 'aswolf' parameter
        :param which_block: block index 1-based
        :param aswolf: if True, (i,j) are 1-based like Fortran, otherwise 0-based like Python
        :param abs: if True, then the translation is taken into account
        """

        if which_block == 0:
            logging.warning("Block index is probably 0-based. It should be 1-based.")
            return

        k = getkeyblock(which_block, False)
        assert k in self.myblocks, f"The block '{k}' you ask for doesn't exist."

        x, y = self.myblocks[k].get_xy_from_ij(i, j, aswolf=aswolf, abs=abs)
        return x, y

    def get_blockij_from_xy(self, x:float, y:float, abs:bool=True):
        """
        Return the block indices (i,j) of the block covering the world coordinate (x,y)

        :param x: x coordinate
        :param y: y coordinate
        :param abs: if True, then the translation is taken into account

        :return: the block indices (i,j,[k]) or (-1,-1,-1) if no block covers the coordinate
        """

        exists = False
        k = 1
        for curblock in self.myblocks.values():
            curblock: WolfArray
            nbx = curblock.nbx
            nby = curblock.nby

            i, j = curblock.get_ij_from_xy(x, y, abs=abs)

            if (i > 0 and i <= nbx and j > 0 and j <= nby):
                if not curblock.array.mask[i, j]:
                    exists = True
                    break
            k += 1

        if exists:
            return i, j, k
        else:
            return -1, -1, -1

    def link_palette(self):
        """Lier les palettes des blocs à la palette de l'objet parent"""

        for curblock in self.myblocks.values():
            curblock.mypal = self.mypal

    def updatepalette(self, which:int=0, onzoom:list[float]=[]):
        """
        Update the palette/colormap of the array

        :param which: which colormap to use
        :param onzoom: if not empty, then only the values within the zoom are used to update the palette -- [xmin,xmax,ymin,ymax]

        """

        if len(self.myblocks) == 0:
            return

        if self.mypal.automatic:
            if onzoom != []:
                allarrays = []
                for curblock in self.myblocks.values():
                    istart, jstart = curblock.get_ij_from_xy(onzoom[0], onzoom[2])
                    iend, jend = curblock.get_ij_from_xy(onzoom[1], onzoom[3])

                    istart = 0 if istart < 0 else istart
                    jstart = 0 if jstart < 0 else jstart
                    iend = curblock.nbx if iend > curblock.nbx else iend
                    jend = curblock.nby if jend > curblock.nby else jend

                    partarray = curblock.array[istart:iend, jstart:jend]
                    partarray = partarray[partarray.mask == False]
                    if len(partarray) > 0:
                        allarrays.append(partarray.flatten())

                allarrays = np.concatenate(allarrays)
                self.mypal.isopop(allarrays, allarrays.count())
            else:
                allarrays = np.concatenate(
                    [curblock.array[curblock.array.mask == False].flatten() for curblock in self.myblocks.values()])
                self.mypal.isopop(allarrays, self.nbnotnull)

        self.link_palette()

        if VERSION_RGB ==1:
            for curblock in self.myblocks.values():
                curblock.rgb = self.mypal.get_rgba(curblock.array)

        if self.myops is not None:
            self.myops.update_palette()

    def delete_lists(self):
        """ Delete OpenGL lists """
        for curblock in self.myblocks.values():
            curblock.delete_lists()

    def mimic_plotdata(self):
        """ Copy plot flags to children """
        for curblock in self.myblocks.values():
            curblock: WolfArray
            curblock.plotted = self.plotted
            curblock.plotting = self.plotting

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size = None):
        """ Plot the array """
        self.plotting = True
        self.mimic_plotdata()

        for curblock in self.myblocks.values():
            curblock.plot(sx, sy, xmin, ymin, xmax, ymax)

        self.plotting = False
        self.mimic_plotdata()

        # Plot selected nodes
        if self.SelectionData is not None:
            self.SelectionData.plot_selection()

        # Plot zones attached to array
        if self.myops is not None:
            self.myops.myzones.plot()


    def fillonecellgrid(self, curscale, loci, locj, force=False):
        for curblock in self.myblocks.values():
            curblock.fillonecellgrid(curscale, loci, locj, force)

    def check_consistency(self, other):
        """ Vérifie la cohérence entre deux matrices """
        test = isinstance(self, type(other))

        if test:
            for curblock, curblockother in zip(self.myblocks.values(),other.myblocks.values()):
                curblock:WolfArray
                curblockother:WolfArray

                test &= curblock.get_header().is_like(curblockother.get_header())

        return test

    def __add__(self, other):
        """Surcharge de l'opérateur d'addition"""

        newArray = WolfArrayMB()
        newArray.set_header(self.get_header())

        if isinstance(self, type(other)):
            if self.check_consistency(other):
                i=0
                for curblock, curblockother in zip(self.myblocks.values(),other.myblocks.values()):
                    newblock = curblock+curblockother
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return None

        elif isinstance(other, float):
            if other != 0.:
                i=0
                for curblock in self.myblocks.values():
                    newblock = curblock+other
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return self

        return newArray

    def __mul__(self, other):
        """Surcharge de l'opérateur d'addition"""
        newArray = WolfArrayMB()
        newArray.set_header(self.get_header())

        if isinstance(self, type(other)):
            if self.check_consistency(other):
                i=0
                for curblock, curblockother in zip(self.myblocks.values(),other.myblocks.values()):
                    newblock = curblock*curblockother
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return None

        elif isinstance(other, float):
            if other != 0.:
                i=0
                for curblock in self.myblocks.values():
                    newblock = curblock*other
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return self

        return newArray

    def __sub__(self, other):
        """Surcharge de l'opérateur de soustraction"""
        newArray = WolfArrayMB()
        newArray.set_header(self.get_header())

        if isinstance(self, type(other)):
            if self.check_consistency(other):
                i=0
                for curblock, curblockother in zip(self.myblocks.values(),other.myblocks.values()):
                    newblock = curblock-curblockother
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return None

        elif isinstance(other, float):
            if other != 0.:
                i=0
                for curblock in self.myblocks.values():
                    newblock = curblock-other
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return self

        return newArray

    def __pow__(self, other):
        """Surcharge de l'opérateur puissance"""
        newArray = WolfArrayMB()
        newArray.set_header(self.get_header())

        if isinstance(self, type(other)):
            if self.check_consistency(other):
                i=0
                for curblock, curblockother in zip(self.myblocks.values(),other.myblocks.values()):
                    newblock = curblock**curblockother
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return None

        elif isinstance(other, float):
            if other != 0.:
                i=0
                for curblock in self.myblocks.values():
                    newblock = curblock**other
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return self

        return newArray

    def __truediv__(self, other):
        """Surcharge de l'opérateur division"""
        newArray = WolfArrayMB()
        newArray.set_header(self.get_header())

        if isinstance(self, type(other)):
            if self.check_consistency(other):
                i=0
                for curblock, curblockother in zip(self.myblocks.values(),other.myblocks.values()):
                    newblock = curblock/curblockother
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return None

        elif isinstance(other, float):
            if other != 0.:
                i=0
                for curblock in self.myblocks.values():
                    newblock = curblock/other
                    newblock.isblock = True
                    newblock.blockindex = i
                    newArray.myblocks[getkeyblock(i)] = newblock
                    i+=1
            else:
                return self

        return newArray

    def reset(self):
        """ Reset each block"""
        for i in range(self.nb_blocks):
            self[i].reset()

    def mask_reset(self):
        """ Reset mask  -- mask = False everywhere """
        for i in range(self.nb_blocks):
            self[i].mask_reset()
        self.count()

    def mask_data(self, value):
        """ Mask cells where values are equal to `value`"""
        for i in range(self.nb_blocks):
            self[i].mask_data(value)
        self.count()

    def mask_lower(self, value):
        """ Mask cell where values are strictly lower than `value` """
        for i in range(self.nb_blocks):
            self[i].mask_lower(value)
        self.count()

    def mask_lowerequal(self, value):
        """ Mask cell where values are lower than or equal to `value` """
        for i in range(self.nb_blocks):
            self[i].mask_lowerequal(value)
        self.count()

    def mask_greater(self, value):
        """ Mask cell where values are strictly greater than `value` """
        for i in range(self.nb_blocks):
            self[i].mask_greater(value)
        self.count()

    def mask_greaterequal(self, value):
        """ Mask cell where values are greater than or equal to `value` """
        for i in range(self.nb_blocks):
            self[i].mask_greaterequal(value)
        self.count()

    def imshow(self, figax:tuple[Figure, Axis] = None, cmap:Colormap = None, step_ticks=100.) -> tuple[Figure, Axis]:
        """
        Create Matplotlib image from MultiBlock array
        """

        # Use figax if passed as argument
        if figax is None:
            fig,ax = plt.subplots(1,1)
        else:
            fig,ax = figax

        # Find minimal spatial resolution
        dx = sorted([self[i].dx for i in range(self.nb_blocks)])

        dx_min = dx[0]

        bounds = self.get_bounds()

        # Set local WolfHeader
        _header = self.get_header()
        _header.dx = dx_min
        _header.dy = dx_min
        _header.nbx = int((bounds[0][1]-bounds[0][0])/dx_min)
        _header.nby = int((bounds[1][1]-bounds[1][0])/dx_min)

        if cmap is None:
            # Full scale image color
            colors = np.zeros((_header.nbx, _header.nby,4))
            # Iterate on blocks
            for i in range(self.nb_blocks):

                # update local colors if not already done
                if self[i].rgb is None:
                    self[i].updatepalette(0)
                # Pointing RGB
                _colors = self[i].rgb

                if self[i].dx > dx_min:
                    n = int(self[i].dx / dx_min)
                    tmpcolors = np.zeros((_colors.shape[0]*n, _colors.shape[1]*n, _colors.shape[2]))
                    for i in range(n):
                        for j in range(n):
                            tmpcolors[i::n,j::n,:] = _colors
                    _colors = tmpcolors

                # Searching relative position
                x,y = self[i].get_xy_from_ij(0,0)
                loci,locj = _header.get_ij_from_xy(x,y)

                # Alias subarray in colors
                sub = colors[loci:loci+_colors.shape[0], locj:locj+_colors.shape[1],:]
                # Copy color if not masked values
                sub[~ self[i].array.mask,:] = _colors[~ self[i].array.mask,:]

            # Plot
            colors = colors.swapaxes(0,1)
            ax.imshow(colors, origin='lower')

        else:
            # Full scale image values
            vals = np.zeros((_header.nbx, _header.nby))
            alpha = np.zeros(vals.shape)

            # Iterate on blocks
            for i in range(self.nb_blocks):

                # Pointing values
                _vals = self[i].array.data

                if self[i].dx > dx_min:
                    n = int(self[i].dx / dx_min)
                    tmpvals = np.zeros((_vals.shape[0]*n, _vals.shape[1]*n))
                    for i in range(n):
                        for j in range(n):
                            tmpvals[i::n,j::n,:] = _vals
                    _vals = tmpvals

                # Searching relative position
                x,y = self[i].get_xy_from_ij(0,0)
                loci,locj = _header.get_ij_from_xy(x,y)

                # Alias subarray in values
                sub = vals[loci:loci+_vals.shape[0], locj:locj+_vals.shape[1]]
                # Copy values if not masked
                sub[~ self[i].array.mask] = _vals[~ self[i].array.mask]

                sub = alpha[loci:loci+_vals.shape[0], locj:locj+_vals.shape[1]]
                sub[~ self[i].array.mask] = 1.

            # Plot
            vals = vals.swapaxes(0,1)
            alpha = alpha.swapaxes(0,1)
            ax.imshow(vals, origin='lower', cmap=cmap, alpha=alpha)

        ax.set_aspect('equal')

        x_start = (bounds[0][0] // step_ticks) * step_ticks
        x_end   = (bounds[0][1] // step_ticks) * step_ticks

        y_start = (bounds[1][0] // step_ticks) * step_ticks
        y_end   = (bounds[1][1] // step_ticks) * step_ticks

        x_pos = np.arange(x_start, x_end+.0001, step_ticks)
        y_pos = np.arange(y_start, y_end+.0001, step_ticks)

        i = [self.get_ij_from_xy(x, 0.)[0] for x in x_pos]
        j = [self.get_ij_from_xy(0., y)[1] for y in y_pos]

        ax.set_xticks(i)
        ax.set_xticklabels(x_pos, rotation = 30)

        ax.set_yticks(j)
        ax.set_yticklabels(y_pos)

        return fig,ax

    def allocate_ressources(self):
        """ Allocate memory ressources """

        if self.myblocks is None:
            logging.warning("No blocks to allocate")
        else:

            if len(self.myblocks)==0:
                for id, (key, curhead) in enumerate(self.head_blocks.items()):
                    if self.wolftype == WOLF_ARRAY_MB_SINGLE:
                        self.myblocks[key] = WolfArray(srcheader=curhead, whichtype=WOLF_ARRAY_FULL_SINGLE)
                    elif self.wolftype == WOLF_ARRAY_MB_INTEGER:
                        self.myblocks[key] = WolfArray(srcheader=curhead, whichtype=WOLF_ARRAY_FULL_INTEGER)

                    self.myblocks[key].isblock = True
                    self.myblocks[key].blockindex = id
                    self.myblocks[key].idx = key

    def set_header_from_added_blocks(self):
        """ Set header from blocks """

        if len(self.myblocks) > 0:

            origx = min([curblock.origx + curblock.translx for curblock in self.myblocks.values()])
            origy = min([curblock.origy + curblock.transly for curblock in self.myblocks.values()])
            endx  = max([curblock.origx + curblock.translx + curblock.nbx*curblock.dx for curblock in self.myblocks.values()])
            endy  = max([curblock.origy + curblock.transly + curblock.nby*curblock.dy for curblock in self.myblocks.values()])

            self.dx = endx - origx
            self.dy = endy - origy

            self.nbx = 1
            self.nby = 1

            self.origx = origx
            self.origy = origy

            self.translx = 0.
            self.transly = 0.

            self.head_blocks = {}
            for curblock in self.myblocks.values():

                new_trx = self.origx + self.translx
                new_try = self.origy + self.transly

                ox = curblock.origx + curblock.translx
                oy = curblock.origy + curblock.transly

                curblock.origin = (ox - new_trx, oy - new_try)
                curblock.translation = (new_trx, new_try)

                self.head_blocks[curblock.idx] = curblock.get_header()

    def as_WolfArray(self, abs:bool=True, forced_header:header_wolf = None) -> WolfArray:
        """
        Convert to WolfArray -- Rebin blocks if necessary

        :param abs: if True, then the translation is taken into account
        :param forced_header: if not None, then the header is forced to this value
        """

        newArray = WolfArray()

        if forced_header is None:
            myhead = self.get_header(abs=abs)
        else:
            myhead = forced_header
            myhead.wolftype = self.wolftype

        dx = set([curblock.get_header().dx for curblock in iter(self.myblocks.values())])
        dy = set([curblock.get_header().dy for curblock in iter(self.myblocks.values())])

        if len(dx) == 1 and len(dy) == 1:
            # only one resolution

            newArray.dx = list(dx)[0]
            newArray.dy = list(dy)[0]

            newArray.origx = myhead.origx
            newArray.origy = myhead.origy
            newArray.nbx   = int((myhead.nbx*myhead.dx)//newArray.dx)
            newArray.nby   = int((myhead.nby*myhead.dy)//newArray.dy)
            newArray.translx = myhead.translx
            newArray.transly = myhead.transly

            newArray.wolftype = WOLF_ARRAY_FULL_SINGLE if myhead.wolftype == WOLF_ARRAY_MB_SINGLE else WOLF_ARRAY_FULL_INTEGER

            newArray.allocate_ressources()
            newArray.array[:,:] = 0

            for curblock in self.myblocks.values():

                ij = np.where(~curblock.array.mask)
                if len(ij[0]) > 0:
                    if len(ij[0])>0:
                        i = ij[0]
                        j = ij[1]

                        x0, y0 = curblock.get_xy_from_ij(0,0, abs=True)
                        i0, j0 = newArray.get_ij_from_xy(x0, y0, abs=True)

                        i_dest = i + i0
                        j_dest = j + j0

                        newArray.array[i_dest,j_dest] = curblock.array[i,j]
                        newArray.array.mask[i_dest,j_dest] = False
                    else:
                        logging.debug(f"Block {curblock.idx} is empty or totally masked.")
                else:
                    logging.debug(f"Block {curblock.idx} is empty or totally masked.")

        else:
            # multiple resolutions

            dx = list(dx)
            dy = list(dy)

            dx.sort()
            dy.sort()

            newArray.dx = dx[0]
            newArray.dy = dy[0]
            newArray.origx = myhead.origx
            newArray.origy = myhead.origy
            newArray.nbx   = int((myhead.nbx*myhead.dx)//newArray.dx)
            newArray.nby   = int((myhead.nby*myhead.dy)//newArray.dy)
            newArray.translx = myhead.translx
            newArray.transly = myhead.transly

            newArray.wolftype = WOLF_ARRAY_FULL_SINGLE if myhead.wolftype == WOLF_ARRAY_MB_SINGLE else WOLF_ARRAY_FULL_INTEGER

            newArray.allocate_ressources()
            newArray.array[:,:] = 0

            for curblock in self.myblocks.values():

                if curblock.dx == dx[0] and curblock.dy == dy[0]:
                    # same resolution
                    blockArray = curblock
                else:
                    # rebin

                    factor = dx[0]/curblock.dx
                    blockArray = WolfArray(mold=curblock)
                    blockArray.rebin(factor)


                ij = np.where(~blockArray.array.mask)
                if len(ij[0]) > 0:
                    if len(ij[0])>0:
                        i = ij[0]
                        j = ij[1]

                        x0, y0 = blockArray.get_xy_from_ij(0,0, abs=True)
                        i0, j0 = newArray.get_ij_from_xy(x0, y0, abs=True)

                        i_dest = i + i0
                        j_dest = j + j0

                        newArray.array[i_dest,j_dest] = blockArray.array[i,j]
                        newArray.array.mask[i_dest,j_dest] = False
                    else:
                        logging.debug(f"Block {curblock.idx} is empty or totally masked.")
                else:
                    logging.debug(f"Block {curblock.idx} is empty or totally masked.")

        return newArray

    def plot_matplotlib(self,
                        figax:tuple=None,
                        getdata_im:bool=False,
                        update_palette:bool=True,
                        vmin:float=None, vmax:float=None,
                        figsize:tuple=None,
                        Walonmap:bool=False,
                        cat:str='IMAGERIE/ORTHO_2022_ETE',
                        first_mask_data:bool=True,
                        with_legend:bool=False):
        """
        Plot the multi-block (MB) array - Matplotlib version

        Converts the MB array to single/mono-block and,
        Uses the `plot_matplotlib` method of the WolfArray class.

        Using imshow and RGB array

        Plot the array using Matplotlib.
        This method visualizes the array data using Matplotlib's `imshow` function.
        It supports optional overlays, custom palettes, and value range adjustments.

        Notes:
        ------
        - The method applies a mask to the data using the `nullvalue` attribute before plotting.
        - If `Walonmap` is True, the method fetches and overlays a map image using the WalOnMap service.
        - The aspect ratio of the plot is set to 'equal'.

        :param figax: A tuple containing a Matplotlib figure and axis (fig, ax). If None, a new figure and axis are created.
        :type figax: tuple, optional (Default value = None)
        :param getdata_im: If True, returns the image object along with the figure and axis. Default is False, then it only returns (fig, ax).
        :type getdata_im: bool, optional (Default value = False)
        :param update_palette: If True, updates the color palette before plotting. Default is True.
        :type update_palette: bool, optional (Default value = True)
        :param vmin: Minimum value for color scaling. If None, the minimum value is determined automatically. Default is None.
        :type vmin: float, optional (Default value = None)
        :param vmax: Maximum value for color scaling. If None, the maximum value is determined automatically. Default is None.
        :type vmax: float, optional (Default value = None)
        :param figsize: Size of the figure in inches (width, height). Only used if `figax` is None. Default is None.
        :type figsize: tuple, optional (Default value = None)
        :param Walonmap: If True, overlays a map image using the WalOnMap service. Default is False.
        :type Walonmap: bool, optional (Default value = False)
        :param cat: The category of the map to fetch from the WalOnMap service. Default is 'IMAGERIE/ORTHO_2022_ETE'.
            Available orthos:
            - `'IMAGERIE/ORTHO_1971'`
            - `'IMAGERIE/ORTHO_1994_2000'`
            - `'IMAGERIE/ORTHO_2006_2007'`
            - `'IMAGERIE/ORTHO_2009_2010'`
            - `'IMAGERIE/ORTHO_2012_2013'`
            - `'IMAGERIE/ORTHO_2015'`
            - `'IMAGERIE/ORTHO_2016'`
            - `'IMAGERIE/ORTHO_2017'`
            - `'IMAGERIE/ORTHO_2018'`
            - `'IMAGERIE/ORTHO_2019'`
            - `'IMAGERIE/ORTHO_2020'`
            - `'IMAGERIE/ORTHO_2021'`
            - `'IMAGERIE/ORTHO_2022_PRINTEMPS'`
            - `'IMAGERIE/ORTHO_2022_ETE'`
            - `'IMAGERIE/ORTHO_2023_ETE'`
            - `'IMAGERIE/ORTHO_LAST'`
        :type cat: str, optional (Default value = `'IMAGERIE/ORTHO_2022_ETE'`)
        :param first_mask_data: If True, applies the mask to the data before plotting. Default is True.
        :type first_mask_data: bool, optional (Default value = True)
        :param with_legend: If True, adds a color legend to the plot. Default is False.
        :type with_legend: bool, optional (Default value = False)
        :return: If `getdata_im` is False, returns (fig, ax), where `fig` is the Matplotlib figure and `ax` is the axis. If `getdata_im` is True, returns (fig, ax, im), where `im` is the image object created by `imshow`.
        :rtype: tuple
        """

        # Convert to single block
        single_block = self.as_WolfArray()

        return single_block.plot_matplotlib(figax=figax,
                                            getdata_im=getdata_im,
                                            update_palette=update_palette,
                                            vmin=vmin, vmax=vmax,
                                            figsize=figsize,
                                            Walonmap=Walonmap,
                                            cat=cat,
                                            first_mask_data=first_mask_data,
                                            with_legend=with_legend)


def split_floatstring_from_FORTRAN(value:str) -> list[str]:
    """
    Useful for reading MNAP files written by the FORTRAN executable from old simulations.
    If the string contains two floats, returns a list where the input is
    split into two strings.
    Otherwise, returns a list with the original string as the only element.

    !!! A list is returned to handle potential cases in the future where the second
    float might be needed.

    :param value: Input string potentially containing two floats concatenated.
    :return: List of strings after splitting.
    """
    test_split = value.split('.')
    if len(test_split) == 3:
        return [
            test_split[0] + '.' + test_split[1][:5],
            test_split[1][5:] + '.' + test_split[2]
        ]

    else:
        return [value]

class WolfArrayMNAP(WolfArrayMB):
    """
    Matrice MNAP d'une modélisation WOLF2D

    Elle contient toutes les informations de maillage en Multi-blocks
    ainsi que les relations de voisinage de blocs.

    Surcharge de WolfArrayMB avec modification des opérations de lecture/écriture
    car le fichier est au format TEXTE/ASCII et d'une structure spécifique.

    """

    # Each zone will have the contour of one block.
    contour: Zones

    def __init__(self, fname=None, mold=None, masknull=True, crop=None):
        super().__init__(fname, mold, masknull, crop)


    def write_all(self):

        def padf(n):
            s = f"{n:.5f}"
            return f"{s:>12}"

        def padi(n):
            return f"{n:>15}"

        with open(self.filename,"w") as f:
            f.write(padi(self.nb_blocks) + "\n")

            for i in range(self.nb_blocks):
                curkey = getkeyblock(i)
                curarray: WolfArray = self.myblocks[curkey]
                f.write(padf(curarray.dx)+ padf(curarray.dy) + "\n")
                f.write(padf(curarray.origx + curarray.translx) + padf(curarray.origx + curarray.translx + curarray.dx*curarray.nbx) + "\n")
                f.write(padf(curarray.origy + curarray.transly) + padf(curarray.origy + curarray.transly + curarray.dy*curarray.nby) + "\n")
                f.write(padi(curarray.nbx) + padi(curarray.nby) + "\n")

                # FIXME curarray.array = np.flipud(np.ma.asarray(myarray, order='F')).transpose()
                mask = np.transpose(np.flipud(curarray.array.mask))
                for y in range(curarray.nby):
                    f.write("".join([f"{int(not curarray.array.mask[x,y]):>4}" for x in range(curarray.nbx)]) + "\n")

                vertices = self.contour.myzones[0].myvectors[0].myvertices
                f.write(padi(len(vertices)) + "\n")

                for v in vertices:
                    v : wolfvertex
                    f.write(padf(v.x) + padf(v.y) + "\n")

    def read_data(self):

        # Vérification de l'existence de certains attributs
        if self.myblocks is None:
            self.myblocks = {}

        # une matrice WolfArrayMB n'a pas de contour -> ajout d'un attribut spécifique
        self.contour = Zones()

        if Path(self.filename + '.mnap').exists():

            with open(self.filename + '.mnap') as f:

                # Lecture au format texte
                lines = f.read().splitlines()

                # nombre de blocks dans la première ligne
                nb_blocks = abs(int(lines[0]))

                decal = 1
                for i in range(nb_blocks):
                    # bouclage sur chque block
                    curkey = getkeyblock(i)

                    curarray = WolfArray(whichtype=WOLF_ARRAY_FULL_INTEGER8)
                    self.myblocks[curkey] = curarray

                    assert curarray.wolftype == WOLF_ARRAY_FULL_INTEGER8, "Type de block incorrect"

                    curarray.isblock = True
                    curarray.blockindex = i

                    # Recherche des informations de maillage - dx, dy, origx, origy, nbx, nby
                    tmp = re.sub('\\s+', ' ', lines[decal].strip()).split(' ')
                    curarray.dx = float(tmp[0])
                    curarray.dy = float(tmp[1])

                    tmp = re.sub('\s+', ' ', lines[decal + 1].strip()).split(' ')
                    curarray.origx = float(split_floatstring_from_FORTRAN(tmp[0])[0]) - self.origx
                    tmp = re.sub('\s+', ' ', lines[decal + 2].strip()).split(' ')
                    curarray.origy = float(split_floatstring_from_FORTRAN(tmp[0])[0]) - self.origy

                    tmp = re.sub('\\s+', ' ', lines[decal + 3].strip()).split(' ')
                    curarray.nbx = int(tmp[0])
                    curarray.nby = int(tmp[1])

                    decal += 4

                    #Lecture de la matrice de maillage pour le block en cours
                    myarray = []

                    for j in range(curarray.nby):
                        newline = [np.int32(curval) for curval in re.sub('\\s+', ' ', lines[decal].strip()).split()]
                        while len(newline) != curarray.nbx:
                            decal += 1
                            newline = np.concatenate([newline, [np.int32(curval) for curval in
                                                                re.sub('\\s+', ' ', lines[decal].strip()).split()]])
                        myarray.append(newline)
                        decal += 1

                    curarray.array = np.flipud(np.ma.asarray(myarray, order='F', dtype=np.int8)).transpose()

                    # curarray.array[curarray.array < 0] = 0

                    assert curarray.dtype == np.int8, "Type de block incorrect"
                    assert curarray.array.dtype == np.int8
                    assert curarray.wolftype == WOLF_ARRAY_FULL_INTEGER8, "Type de block incorrect"

                    #Lecture du contour de block
                    curzone = zone(name=curkey)
                    contourblock = vector(name='contour')

                    curzone.add_vector(contourblock)
                    self.contour.add_zone(curzone)

                    nbvert = int(lines[decal])
                    for j in range(nbvert):
                        decal += 1
                        xy = re.sub('\\s+', ' ', lines[decal].strip()).split(' ')
                        myvert = wolfvertex(float(xy[0]), float(xy[1]))
                        contourblock.add_vertex(myvert)
                    decal += 1
                    curarray.translx = self.translx + self.origx
                    curarray.transly = self.transly + self.origy

                    # Remplissagze du header
                    # --> la matrice MNAP est la référence d'une simulation 2D
                    #     pour obtenir les informations de maillage
                    curhead = self.head_blocks[getkeyblock(i)] = header_wolf()

                    curhead.nbx = curarray.nbx
                    curhead.nby = curarray.nby
                    curhead.dx = curarray.dx
                    curhead.dy = curarray.dy
                    curhead.origx = curarray.origx
                    curhead.origy = curarray.origy
                    curhead.translx = curarray.translx
                    curhead.transly = curarray.transly

    def read_txt_header(self):
        """
        Surcharge de la lecture du header

        Il n'y a pas en tant que tel de header d'un fichier MNAP.

        Les informations de translation sont dans le fichier ".trl".

        Les informations de tailles de maille 'fines',
        Nbx, Nby et coordonnées d'origine sont dans le fichier ".par"

        """

        if os.path.exists(self.filename + '.trl'):
            with open(self.filename + '.trl') as f:
                lines = f.read().splitlines()
                self.translx = float(lines[1])
                self.transly = float(lines[2])

        if os.path.exists(self.filename + '.par'):
            with open(self.filename + '.par') as f:
                lines = f.read().splitlines()
                self.dx = float(lines[7])
                self.dy = float(lines[8])
                self.nbx = int(lines[9])
                self.nby = int(lines[10])
                self.origx = float(lines[11])
                self.origy = float(lines[12])

        # Imposition du type de stockage
        self.wolftype = WOLF_ARRAY_MNAP_INTEGER

    def get_one_mask(self, which:int | str):
        """
        Return the mask of the block `which`
        """

        if isinstance(which, int):
            key = getkeyblock(which)
        else:
            key = which

        return self.myblocks[key].array.data != 1

    def get_all_masks(self):
        """
        Return all masks
        """

        return [curblock.array.data != 1 for curblock in self.myblocks.values()]