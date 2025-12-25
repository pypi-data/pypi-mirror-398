"""
Author: HECE - University of Liege, Pierre Archambeau, Utashi Ciraane Docile
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os import path
from typing import Union
import numpy as np
import triangle.tri
import wx
import wx._dataview
from wx.dataview import *
from wx.core import BoxSizer, TreeItemId
from OpenGL.GL  import *
from shapely.geometry import LineString, MultiLineString,Point,MultiPoint,Polygon,JOIN_STYLE, MultiPolygon
from shapely.ops import nearest_points
from shapely import delaunay_triangles, prepare, is_prepared, destroy_prepared
import pygltflib
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib import cm
from matplotlib.colors import Colormap
from matplotlib.tri import Triangulation as mpl_tri
import warnings

import struct
import pyvista as pv
from typing import Union, Literal
import logging
from tqdm import tqdm
import copy
import geopandas as gpd
import io
from typing import Union, Literal
from pathlib import Path
import triangle
from concurrent.futures import ThreadPoolExecutor, wait


from .wolf_texture import genericImagetexture
from .PyTranslate import _
from .CpGrid import CpGrid
from .PyVertex import wolfvertex,getIfromRGB,getRGBfromI, cloud_vertices
from .PyParams import Wolf_Param, Type_Param, new_json
from .wolf_texture import Text_Image_Texture,Text_Infos
from .drawing_obj import Element_To_Draw
from .matplotlib_fig import Matplotlib_Figure as MplFig
from .PyPalette import wolfpalette

try:
    from .pydownloader import download_file, toys_dataset
except ImportError as e:
    raise Exception(_('Error importing pydownloader module'))

class Triangulation(Element_To_Draw):
    """ Triangulation based on a listof vertices
    and triangles enumerated by their vertex indices """

    def __init__(self, fn='', pts=[], tri=[], idx: str = '', plotted: bool = True, mapviewer=None, need_for_wx: bool = False) -> None:
        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self.filename = ''

        self.tri= tri
        self.pts = pts

        self.id_list = -99999

        self.nb_tri = len(tri)
        self.nb_pts = len(pts)

        self._used_tri = [True] * self.nb_tri

        self._move_start = None
        self._move_step = None  # step for a move
        self._rotation_center = None
        self._rotation_step = None
        self._cache = None

        if fn !='':
            self.filename=fn
            self.read(fn)
        else:
            self.validate_format()
        pass

    def validate_format(self):
        """ Force the format of the data """

        if isinstance(self.pts,list):
            self.pts = np.asarray(self.pts)
        if isinstance(self.tri,list):
            self.tri = np.asarray(self.tri)

    def as_polydata(self) -> pv.PolyData:
        """ Convert the triangulation to a PyVista PolyData object """

        return pv.PolyData(np.asarray(self.pts),np.column_stack([[3]*self.nb_tri,self.tri]), self.nb_tri)

    def from_polydata(self, poly:pv.PolyData):
        """ Convert a PyVista PolyData object to the triangulation format """

        self.pts = np.asarray(poly.points.copy())
        self.tri = np.asarray(poly.faces.reshape([int(len(poly.faces)/4),4])[:,1:4])

        self.nb_pts = len(self.pts)
        self.nb_tri = len(self.tri)

    def clip_surface(self, other:"Triangulation", invert=True, subdivide=0):
        """ Clip the triangulation with another one """

        if subdivide==0:
            mypoly = self.as_polydata()
            mycrop = other.as_polydata()
        else:
            mypoly = self.as_polydata().subdivide(subdivide)
            mycrop = other.as_polydata().subdivide(subdivide)

        res = mypoly.clip_surface(mycrop, invert=invert)

        if len(res.faces)>0:
            self.from_polydata(res)

    def get_mask(self, eps:float= 1e-10):
        """
        Teste si la surface de tous les triangles est positive

        Retire les triangles problématiques
        """

        if self.nb_tri>0:
            v1 = [self.pts[curtri[1]][:2] - self.pts[curtri[0]][:2] for curtri in self.tri]
            v2 = [self.pts[curtri[2]][:2] - self.pts[curtri[0]][:2] for curtri in self.tri]
            self.areas = np.cross(v2,v1,)/2
            return self.areas <= eps

            # invalid_tri = np.sort(np.where(self.areas<=eps)[0])
            # for curinv in invalid_tri[::-1]:
            #     self.tri.pop(curinv)

            # self.nb_tri = len(self.tri)

    def import_from_gltf(self, fn=''):
        """ Import a GLTF file and convert it to the triangulation format """

        wx_exists = wx.GetApp() is not None

        if fn =='' and wx_exists:
            dlg=wx.FileDialog(None,_('Choose filename'),wildcard='binary gltf2 (*.glb)|*.glb|gltf2 (*.gltf)|*.gltf|All (*.*)|*.*',style=wx.FD_OPEN)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            fn=dlg.GetPath()
            dlg.Destroy()
        else:
            fn = str(fn)

        gltf = pygltflib.GLTF2().load(fn)

        # get the first mesh in the current scene
        mesh = gltf.meshes[gltf.scenes[gltf.scene].nodes[0]]

        # get the vertices for each primitive in the mesh
        for primitive in mesh.primitives:

            # get the binary data for this mesh primitive from the buffer
            accessor = gltf.accessors[primitive.attributes.POSITION]

            bufferView = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[bufferView.buffer]
            data = gltf.get_data_from_buffer_uri(buffer.uri)

            logging.info(_('Importing GLTF file : {}').format(fn))
            logging.info(_('Number of vertices : {}').format(accessor.count))

            # pull each vertex from the binary buffer and convert it into a tuple of python floats
            points = np.zeros([accessor.count, 3], order='F', dtype=np.float64)
            for i in range(accessor.count):
                index = bufferView.byteOffset + accessor.byteOffset + i * 12  # the location in the buffer of this vertex
                d = data[index:index + 12]  # the vertex data
                v = struct.unpack("<fff", d)  # convert from base64 to three floats

                points[i, :] = np.asarray([v[0], -v[2], v[1]])

                if np.mod(i,100000)==0:
                    logging.info(_('Reading vertex {}').format(i))

            accessor = gltf.accessors[primitive.indices]

            bufferView = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[bufferView.buffer]
            data = gltf.get_data_from_buffer_uri(buffer.uri)

            triangles = []
            if accessor.componentType==pygltflib.UNSIGNED_SHORT:
                size=6
                format='<HHH'
            elif accessor.componentType==pygltflib.UNSIGNED_INT:
                size=12
                format='<LLL'

            logging.info(_('Number of triangles : {}').format(int(accessor.count/3)))
            for i in range(int(accessor.count/3)):

                index = bufferView.byteOffset + accessor.byteOffset + i*size  # the location in the buffer of this vertex
                d = data[index:index+size]  # the vertex data
                v = struct.unpack(format, d)   # convert from base64 to three floats
                triangles.append(list(v))

                if np.mod(i,100000)==0:
                    logging.info(_('Reading triangle {}').format(i))

        # On souhaite obtenir une triangulation du type :
        #   - liste de coordonnées des sommets des triangles
        #   - par triangle, liste de 3 indices, un pour chaque sommet
        #
        # Si le fichier GLTF vient de Blender, il y aura des informations de normales ...
        # Il est donc préférable de filtrer les points pour ne garder que des valeurs uniques
        # On ne souhaite pas gérer le GLTF dans toute sa généralité mais uniquement la triangulation de base
        logging.info(_('Sorting information ...'))
        xyz_u,indices = np.unique(np.array(points),return_inverse=True,axis=0)
        logging.info(_('Creating triangles ...'))
        triangles = [[indices[curtri[0]],indices[curtri[1]],indices[curtri[2]]] for curtri in list(triangles)]

        self.pts = xyz_u
        self.tri = triangles

        self.nb_pts = len(self.pts)
        self.nb_tri = len(self.tri)

    def export_to_gltf(self,fn=''):
        """ Export the triangulation to a GLTF file """

        #on force les types de variables
        triangles = np.asarray(self.tri).astype(np.uint32)
        points = np.column_stack([self.pts[:,0],self.pts[:,2],-self.pts[:,1]]).astype(np.float32)

        triangles_binary_blob = triangles.flatten().tobytes()
        points_binary_blob = points.flatten().tobytes()

        gltf = pygltflib.GLTF2(
            scene=0,
            scenes=[pygltflib.Scene(nodes=[0])],
            nodes=[pygltflib.Node(mesh=0)],
            meshes=[
                pygltflib.Mesh(
                    primitives=[
                        pygltflib.Primitive(
                            attributes=pygltflib.Attributes(POSITION=1), indices=0
                        )
                    ]
                )
            ],
            accessors=[
                pygltflib.Accessor(
                    bufferView=0,
                    componentType=pygltflib.UNSIGNED_INT,
                    count=self.nb_tri*3,
                    type=pygltflib.SCALAR,
                    max=[int(triangles.max())],
                    min=[int(triangles.min())],
                ),
                pygltflib.Accessor(
                    bufferView=1,
                    componentType=pygltflib.FLOAT,
                    count=self.nb_pts,
                    type=pygltflib.VEC3,
                    max=points.max(axis=0).tolist(),
                    min=points.min(axis=0).tolist(),
                ),
            ],
            bufferViews=[
                pygltflib.BufferView(
                    buffer=0,
                    byteLength=len(triangles_binary_blob),
                    target=pygltflib.ELEMENT_ARRAY_BUFFER,
                ),
                pygltflib.BufferView(
                    buffer=0,
                    byteOffset=len(triangles_binary_blob),
                    byteLength=len(points_binary_blob),
                    target=pygltflib.ARRAY_BUFFER,
                ),
            ],
            buffers=[
                pygltflib.Buffer(
                    byteLength=len(triangles_binary_blob) + len(points_binary_blob)
                )
            ],
        )
        gltf.set_binary_blob(triangles_binary_blob + points_binary_blob)

        if fn =='':
            dlg=wx.FileDialog(None,_('Choose filename'),wildcard='binary gltf2 (*.glb)|*.glb|gltf2 (*.gltf)|*.gltf|All (*.*)|*.*',style=wx.FD_SAVE)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            fn=dlg.GetPath()
            dlg.Destroy()

        gltf.save(fn)
        return fn

    def saveas(self,fn=''):
        """
        Binary '.TRI' format on disk is, little endian :
           - int32 for number of points
           - int32 as 64 ou 32 for float64 or float32
           - VEC3 (float64 or float32) for points
           - int32 for number of triangles
           - VEC3 uint32  for triangles
        """
        if self.filename=='' and fn=='':
            return

        if fn!='':
            self.filename = fn

        triangles = np.asarray(self.tri).astype(np.uint32)
        points = np.asarray(self.pts) #.astype(np.float64)

        with open(self.filename,'wb') as f:
            f.write(self.nb_pts.to_bytes(4,'little'))

            if points.dtype == np.float64:
                f.write(int(64).to_bytes(4,'little'))
            else:
                f.write(int(32).to_bytes(4,'little'))
            points.tofile(f,"")

            f.write(self.nb_tri.to_bytes(4,'little'))
            triangles.tofile(f,"")

    def read(self,fn:str):
        """ Read a binary '.TRI' file """

        fn = str(fn)

        if fn.endswith('.dxf'):
            self.import_dxf(fn)
        elif fn.endswith('.gltf') or fn.endswith('.glb'):
            self.import_from_gltf(fn)
        elif fn.endswith('.tri'):
            with open(fn,'rb') as f:
                self.nb_pts = int.from_bytes(f.read(4),'little')
                which_type = int.from_bytes(f.read(4),'little')
                if which_type == 64:
                    buf = np.frombuffer(f.read(8 * self.nb_pts * 3), dtype=np.float64)
                    self.pts = np.array(buf.copy(), dtype=np.float64).reshape([self.nb_pts,3])
                elif which_type == 32:
                    buf = np.frombuffer(f.read(4 * self.nb_pts * 3), dtype=np.float32)
                    self.pts = np.array(buf.copy(), dtype=np.float32).reshape([self.nb_pts,3]).astype(np.float64)

                self.nb_tri = int.from_bytes(f.read(4),'little')
                buf = np.frombuffer(f.read(4 * self.nb_tri * 3), dtype=np.uint32)
                self.tri = np.array(buf.copy(), dtype=np.uint32).reshape([self.nb_tri,3]).astype(np.int32)

        self.validate_format()
        self.find_minmax(True)
        self.reset_plot()

    def reset_plot(self):
        """ Reset the OpenGL plot """

        try:
            if self.id_list!=-99999:
                glDeleteLists(self.id_list)
        except:
            pass

        self.id_list = -99999

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None ):
        """ Plot the triangulation in OpenGL """

        if self.id_list == -99999:
            try:
                self.id_list = glGenLists(1)

                glNewList(self.id_list, GL_COMPILE)

                glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)

                for curtri in self.tri:
                    glBegin(GL_LINE_STRIP)

                    glColor3ub(int(0),int(0),int(0))

                    glVertex2d(self.pts[curtri[0]][0], self.pts[curtri[0]][1])
                    glVertex2d(self.pts[curtri[1]][0], self.pts[curtri[1]][1])
                    glVertex2d(self.pts[curtri[2]][0], self.pts[curtri[2]][1])
                    glVertex2d(self.pts[curtri[0]][0], self.pts[curtri[0]][1])

                    glEnd()

                glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)

                glEndList()
                glCallList(self.id_list)
            except:
                logging.warning('Problem with OpenGL plot - Triangulation.plot')
        else:
            glCallList(self.id_list)

    def plot_matplotlib(self, ax:Axes | tuple[Figure, Axes] = None, color='black', alpha=1., lw=1.5, **kwargs):
        """ Plot the triangulation in Matplotlib
        """

        if isinstance(ax, tuple):
            fig, ax = ax
        elif ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        if self.nb_tri>0:
            for curtri in self.tri:
                x = [self.pts[curtri[0]][0], self.pts[curtri[1]][0], self.pts[curtri[2]][0], self.pts[curtri[0]][0]]
                y = [self.pts[curtri[0]][1], self.pts[curtri[1]][1], self.pts[curtri[2]][1], self.pts[curtri[0]][1]]
                ax.plot(x, y, color=color, alpha=alpha, lw=lw, **kwargs)
        else:
            logging.warning('No triangles to plot')

        return fig, ax

    @property
    def mpl_triangulation(self) -> mpl_tri:
        """ Return the triangulation as a Matplotlib Triangulation object """
        if self.nb_tri>0:
            return mpl_tri(self.pts[:,0], self.pts[:,1], self.tri)
        else:
            logging.warning('No triangles to plot')
            return None

    def plot_matplotlib_3D(self, ax:Axes | tuple[Figure, Axes] = None, color='black', alpha=0.2, lw=1.5, edgecolor='k', shade=True, **kwargs):
        """ Plot the triangulation in Matplotlib 3D
        """

        if self.nb_tri>0:
            if isinstance(ax, tuple):
                fig, ax = ax
            elif ax is None:
                fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
            else:
                fig = ax.figure

            ax.plot_trisurf(self.mpl_triangulation, Z=self.pts[:,2], color=color, alpha=alpha, lw=lw, edgecolor=edgecolor, shade=shade, **kwargs)

            return fig, ax
        else:
            logging.warning('No triangles to plot')
            return None, None

    def find_minmax(self,force):
        """ Find the min and max of the triangulation

        :param force: force the min and max to be calculated
        """

        if force:
            if self.nb_pts>0:
                self.xmin=np.min(self.pts[:,0])
                self.ymin=np.min(self.pts[:,1])
                self.xmax=np.max(self.pts[:,0])
                self.ymax=np.max(self.pts[:,1])

    def import_dxf(self,fn):
        """ Import a DXF file and convert it to the triangulation format """

        import ezdxf

        if not path.exists(fn):
            logging.warning(_('File not found !') + ' ' + fn)
            return

        # Lecture du fichier dxf et identification du modelspace
        doc = ezdxf.readfile(fn)
        msp = doc.modelspace()

        # Liste de stockage des coordonnées des faces 3D
        xyz = []

        # Bouclage sur les éléments du DXF
        for e in msp:
            if e.dxftype() == "3DFACE":
                # récupération des coordonnées
                # --> on suppose que ce sont des triangles (!! une face3D peut être un quadrangle !! on oublie donc la 4ème coord)
                xyz += [e[0],e[1],e[2]]

        # On souhaite obtenir une triangulation du type :
        #   - liste de coordonnées des sommets des triangles
        #   - par triangle, liste de 3 indices, un pour chaque sommet
        #
        # Actuellement, les coordonnées sont multipliées car chaque face a été extraite indépendamment
        # On commence donc par identifier les coordonnées uniques, par tuple
        # return_inverse permet de constituer la liste d'indices efficacement
        #
        xyz_u,indices = np.unique(np.array(xyz),return_inverse=True,axis=0)
        triangles = indices.reshape([int(len(indices)/3),3])

        self.tri = triangles.astype(np.int32)
        self.pts = xyz_u
        self.nb_pts = len(self.pts)
        self.nb_tri = len(self.tri)
        self.validate_format()

    def set_cache(self):
        """ Set the cache for the vertices """

        self._cache = self.pts.copy()

    def clear_cache(self):
        """ Clear the cache for the vertices """

        self._cache = None

    def move(self, delta_x:float, delta_y:float, use_cache:bool = True):
        """ Move the vertices by a delta_x and delta_y

        :param delta_x: delta x [m]
        :param delta_y: delta y [m]
        """

        if use_cache and self._cache is None:
            self.set_cache()

        if use_cache:
            self.pts[:,0] = self._cache[:,0] + delta_x
            self.pts[:,1] = self._cache[:,1] + delta_y
        else:
            self.pts[:,0] += delta_x
            self.pts[:,1] += delta_y

    def rotate(self, angle:float, center:tuple, use_cache:bool = True):
        """ Rotate the vertices around a center

        :param angle: angle in degrees -- positive for clockwise rotation
        :param center: center of rotation
        """
        angle = np.radians(angle)
        c,s = np.cos(angle), np.sin(angle)
        R = np.array([[c,-s],[s,c]])

        if use_cache and self._cache is None:
            self.set_cache()

        if use_cache:
            locxy = self._cache[:,:2] - np.array(center)
            self.pts[:,:2] = np.dot(R,locxy.T).T + np.array(center)
        else:
            locxy = self.pts[:,:2] - np.array(center)
            self.pts[:,:2] = np.dot(R,locxy.T).T + np.array(center)

    def rotate_xy(self, x:float, y:float, use_cache:bool = True):
        """ Rotate the vector around the rotation center and a xy point """

        if self._rotation_center is None:
            logging.error('No rotation center defined -- set it before rotating by this routine')
            return self

        angle = np.degrees(np.arctan2(-(y-self._rotation_center[1]), x-self._rotation_center[0]))

        if self._rotation_step is not None:
            angle = np.round(angle/self._rotation_step)*self._rotation_step

        return self.rotate(-angle, center=self._rotation_center, use_cache=use_cache)

    def _get_polygons(self) -> list[Polygon]:
        """ Get the polygons from the triangulation """
        polygons = []
        for curtri in self.tri:
            if len(curtri) == 3:
                poly = Polygon([self.pts[curtri[0]][:2], self.pts[curtri[1]][:2], self.pts[curtri[2]][:2]])
                if poly.is_valid:
                    polygons.append(poly)
                else:
                    logging.debug('Invalid polygon found in triangulation: {}'.format(poly))
            else:
                logging.error('Triangle with {} vertices found in triangulation: {}'.format(len(curtri), curtri))
        return polygons

    def unuse_triangles_containing_points(self, points:list[Point]):
        """ Unuse triangles containing points """

        polys = self._get_polygons()
        for point in points:
            for i, poly in enumerate(polys):
                if poly.contains(point):
                    self._used_tri[i] = False

    def get_triangles_as_listwolfvertices(self, used_only:bool=True) -> list[list[wolfvertex]]:
        """ Get the triangles as a list of wolfvertex objects """

        triangles = []
        for i, curtri in enumerate(self.tri):
            if not used_only or (used_only and self._used_tri[i]):
                if len(curtri) == 3:
                    v1 = wolfvertex(self.pts[curtri[0]][0], self.pts[curtri[0]][1], self.pts[curtri[0]][2])
                    v2 = wolfvertex(self.pts[curtri[1]][0], self.pts[curtri[1]][1], self.pts[curtri[1]][2])
                    v3 = wolfvertex(self.pts[curtri[2]][0], self.pts[curtri[2]][1], self.pts[curtri[2]][2])
                    triangles.append([v1, v2, v3])
                else:
                    logging.warning('Triangle with {} vertices found in triangulation: {}'.format(len(curtri), curtri))
        return triangles

class vectorproperties:
    """ Vector properties """
    used:bool

    color:int
    width:int
    style:int
    alpha:int
    closed=bool
    filled:bool
    legendvisible:bool
    transparent:bool
    flash:bool

    legendtext:str
    legendrelpos:int
    legendx:float
    legendy:float

    legendbold:bool
    legenditalic:bool
    legendunderlined:bool
    legendfontname=str
    legendfontsize:int
    legendcolor:int

    extrude:bool = False

    myprops:Wolf_Param = None

    def __init__(self, lines:list[str]=[], parent:"vector"=None) -> None:
        """
        Init the vector properties -- Compatibility with VB6, Fortran codes --> Modify with care

        :param lines: list of lines from a file
        :param parent: parent vector
        """

        self.parent:vector
        self.parent=parent

        if len(lines)>0:
            line1=lines[0].split(',')
            line2=lines[1].split(',')

            self.color=int(line1[0])
            self.width=int(line1[1])
            self.style=int(line1[2])
            self.closed=line1[3]=='#TRUE#'
            self.filled=line1[4]=='#TRUE#'
            self.legendvisible=line1[5]=='#TRUE#'
            self.transparent=line1[6]=='#TRUE#'
            self.alpha=int(line1[7])
            self.flash=line1[8]=='#TRUE#'

            self.legendtext=line2[0]
            self.legendrelpos=int(line2[1])
            self.legendx=float(line2[2])
            self.legendy=float(line2[3])
            self.legendbold=line2[4]=='#TRUE#'
            self.legenditalic=line2[5]=='#TRUE#'
            self.legendfontname=str(line2[6])
            self.legendfontsize=int(line2[7])
            self.legendcolor=int(line2[8])
            self.legendunderlined=line2[9]=='#TRUE#'

            self.used=lines[2]=='#TRUE#'
        else:
            # default values in case of new vector
            self.color=0
            self.width=1
            self.style=1
            self.closed=False
            self.filled=False
            self.legendvisible=False
            self.transparent=False
            self.alpha=0
            self.flash=False

            self.legendtext=''
            self.legendrelpos=5
            self.legendx=0.
            self.legendy=0.
            self.legendbold=False
            self.legenditalic=False
            self.legendfontname='Arial'
            self.legendfontsize=10
            self.legendcolor=0
            self.legendunderlined=False

            self.used=True

            self.plot_indices = False

        self._values = {}

        # FIXME : to be changed
        # if self.parent is not None:
        #     self.closed = self.parent.closed

        self.init_extra()

    def __getitem__(self, key:str) -> Union[int,float,bool,str]:
        """ Get a value """
        if key in self._values:
            return self._values[key]
        else:
            return None

    def __setitem__(self, key:str, value:Union[int,float,bool,str]):
        """ Set a value """
        self._values[key] = value

    def set_color_from_value(self, key:str, cmap:wolfpalette | str | Colormap | cm.ScalarMappable, vmin:float= 0., vmax:float= 1.):
        """ Set the color from a value """

        if key in self._values:
            val = self._values[key]

            # Test if val is a numeric value or can be converted to a numeric value
            try:
                val = float(val)
            except:
                logging.warning('Value {} is not a numeric value'.format(val))
                self.color = 0
                return

            val_adim = (val-vmin)/(vmax-vmin)

            if isinstance(cmap, wolfpalette):
                self.color = getIfromRGB(cmap.get_rgba_oneval(val))
            elif isinstance(cmap, str):
                cmap = cm.get_cmap(cmap)
                self.color = getIfromRGB(cmap(val_adim, bytes=True))
            elif isinstance(cmap, Colormap):
                self.color = getIfromRGB(cmap(val_adim, bytes=True))
            elif isinstance(cmap, cm.ScalarMappable):
                self.color = getIfromRGB(cmap.to_rgba(val, bytes=True)[:3])
        else:
            self.color = 0

    def init_extra(self):
        """
        Init extra properties --> not compatible with VB6, Fortran codes

        Useful for Python UI, OpenGL legend, etc.
        """
        self.legendlength = 100.
        self.legendheight = 100.
        self.legendpriority = 3
        self.legendorientation = 0.

        self.attachedimage = None
        self.imagevisible = False
        self.textureimage:genericImagetexture = None
        self.image_scale = 1.0
        self.image_relative_posx = 0.0
        self.image_relative_posy = 0.0
        self.image_attached_pointx = -99999.
        self.image_attached_pointy = -99999.

        self.plot_indices = False

        self._cached_offset = None

    def get_extra(self) -> list[float,float,int,float,str,bool, float, float, float, float, float]:
        """ Return extra properties """
        return [self.legendlength,
                self.legendheight,
                self.legendpriority,
                self.legendorientation,
                str(self.attachedimage),
                self.imagevisible,
                self.plot_indices,
                self.image_scale,
                self.image_relative_posx,
                self.image_relative_posy,
                self.image_attached_pointx,
                self.image_attached_pointy
                ]

    def set_extra(self, linesextra:list[float,float,int,float,str,bool, float, float, float, float, float] = None):
        """ Set extra properties """

        if linesextra is None:
            return

        assert len(linesextra)>=4, 'Extra properties must be a list of [float, float, int, float, str, bool]'

        self.legendlength = float(linesextra[0])
        self.legendheight = float(linesextra[1])
        self.legendpriority = int(linesextra[2])
        self.legendorientation = float(linesextra[3])

        if len(linesextra)>4:
            self.attachedimage = Path(linesextra[4])
            self.imagevisible = linesextra[5].lower() == 'true'

        if len(linesextra)>6:
            self.plot_indices = linesextra[6].lower() == 'true'

        if len(linesextra)>7:
            self.image_scale = float(linesextra[7])
            self.image_relative_posx = float(linesextra[8])
            self.image_relative_posy = float(linesextra[9])
            self.image_attached_pointx = float(linesextra[10])
            self.image_attached_pointy = float(linesextra[11])

    def load_extra(self, lines:list[str]) -> int:
        """ Load extra properties from lines """

        nb_extra = int(lines[0])
        linesextra = lines[1:1+nb_extra]
        self.set_extra(linesextra)

        return nb_extra+1

    def save_extra(self, f:io.TextIOWrapper):
        """ Save extra properties to opened file """

        extras = self.get_extra()

        f.write(self.parent.myname+'\n')
        f.write('{}\n'.format(len(extras)))
        for curextra in extras:
            f.write('{}'.format(curextra)+'\n')

    def save(self, f:io.TextIOWrapper):
        """
        Save properties to opened file

        Pay attention to the order of the lines and the format to be compatible with VB6, Fortran codes
        """
        line1 = str(self.color) + ',' + str(self.width)+','+ str(self.style)

        added = ',#TRUE#' if self.closed else ',#FALSE#'
        line1+=added
        added = ',#TRUE#' if self.filled else ',#FALSE#'
        line1+=added
        added = ',#TRUE#' if self.legendvisible else ',#FALSE#'
        line1+=added
        added = ',#TRUE#' if self.transparent else ',#FALSE#'
        line1+=added
        line1+=','+str(self.alpha)
        added = ',#TRUE#' if self.flash else ',#FALSE#'
        line1+=added

        f.write(line1+'\n')

        line1 = self.legendtext + ',' + str(self.legendrelpos)+','+ str(self.legendx)+','+ str(self.legendy)
        added = ',#TRUE#' if self.legendbold else ',#FALSE#'
        line1+=added
        added = ',#TRUE#' if self.legenditalic else ',#FALSE#'
        line1+=added
        line1+= ','+self.legendfontname + ',' + str(self.legendfontsize)+ ',' + str(self.legendcolor)
        added = ',#TRUE#' if self.legendunderlined else ',#FALSE#'
        line1+=added

        f.write(line1+'\n')

        added = '#TRUE#' if self.used else '#FALSE#'
        f.write(added+'\n')

    @property
    def image_path(self) -> Path:
        """ Return the path of the attached image """
        return Path(self.attachedimage)

    @image_path.setter
    def image_path(self, value:Path):
        """ Set the path of the attached image """

        if self.attachedimage != value:
            self.unload_image()

        self.attachedimage = Path(value)

    def load_unload_image(self):
        """ Load an attached image """

        if self.imagevisible:
            if self.attachedimage is not None:
                self.attachedimage = Path(self.attachedimage)
                if self.attachedimage.exists():

                    (xmin,xmax),(ymin,ymax) = self.parent.get_bounds_xx_yy()

                    if self.textureimage is not None:
                        if self.textureimage.imageFile == self.attachedimage:
                            self.textureimage.drawing_scale = self.image_scale
                            self.textureimage.offset = (self.image_relative_posx, self.image_relative_posy)
                            self.textureimage.xmin = xmin
                            self.textureimage.xmax = xmax
                            self.textureimage.ymin = ymin
                            self.textureimage.ymax = ymax
                            return
                        else:
                            self.textureimage.unload()

                    self.textureimage = genericImagetexture(which = 'attachedfile',
                                                            label=self.parent.myname,
                                                            mapviewer= self.parent.get_mapviewer(),
                                                            imageFile=self.attachedimage,
                                                            xmin=xmin,
                                                            xmax=xmax,
                                                            ymin=ymin,
                                                            ymax=ymax,
                                                            drawing_scale= self.image_scale,
                                                            offset = (self.image_relative_posx, self.image_relative_posy))
                else:
                    logging.warning('Image not found : {}'.format(self.attachedimage))
        else:
            self.unload_image()

    def unload_image(self):
        """ Unload the attached image """

        if self.textureimage is not None:
            self.textureimage.unload()
            self.textureimage = None

    def fill_property(self, props:Wolf_Param = None, updateOGL:bool = True):
        """
        Callback for the properties UI

        When the 'Apply' button is pressed, this function is called
        """

        if props is None:
            props = self.myprops

        self.color = getIfromRGB(props[('Draw','Color')])
        self.width = props[('Draw','Width')]
        # self.style = props[('Draw','Style')]

        old_closed = self.closed
        self.closed = props[('Draw','Closed')]

        if old_closed != self.closed:
            self.parent._reset_listogl()

        self.filled = props[('Draw','Filled')]
        self.transparent = props[('Draw','Transparent')]
        self.alpha = props[('Draw','Alpha')]
        # self.flash = props[('Draw','Flash')]
        self.plot_indices = props[('Draw','Plot indices if active')]

        self.legendunderlined = props[('Legend','Underlined')]
        self.legendbold = props[('Legend','Bold')]

        self.legendfontname = self._convert_int2fontname(props[('Legend','Font name')])

        self.legendfontsize = props[('Legend','Font size')]
        self.legendcolor = getIfromRGB(props[('Legend','Color')])
        self.legenditalic = props[('Legend','Italic')]
        self.legendrelpos = props[('Legend','Relative position')]

        text = props[('Legend','Text')]

        self.legendvisible = props[('Legend','Visible')]

        self.legendlength = props[('Legend','Length')]
        self.legendheight = props[('Legend','Height')]
        self.legendpriority = props[('Legend','Priority')]
        self.legendorientation = props[('Legend','Orientation')]

        self.attachedimage = Path(props[('Image','Attached image')])
        self.imagevisible = props[('Image','To show')]
        self.image_scale = props[('Image','Scale')]
        self.image_relative_posx = props[('Image','Relative position X')]
        self.image_relative_posy = props[('Image','Relative position Y')]
        self.image_attached_pointx = props[('Image','Attached point X')]
        self.image_attached_pointy = props[('Image','Attached point Y')]

        posx = props[('Move','Start X')]
        posy = props[('Move','Start Y')]
        move_step = props[('Move','Step [m]')]

        if posx != 99999. and posy != 99999.:
            self.parent._move_start = (posx,posy)
        else:
            self.parent._move_start = None

        if move_step != 99999.:
            self.parent._move_step = move_step
        else:
            self.parent._move_step = None

        posx = props[('Rotation','Center X')]
        posy = props[('Rotation','Center Y')]
        rot_step = props[('Rotation','Step [degree]')]

        if posx != 99999. and posy != 99999.:
            self.parent._rotation_center = (posx,posy)
        else:
            self.parent._rotation_center = None

        if rot_step != 99999.:
            self.parent._rotation_step = rot_step
        else:
            self.parent._rotation_step = None

        angle = props[('Rotation','Angle [degree]')]
        dx = props[('Move','Delta X')]
        dy = props[('Move','Delta Y')]

        if angle != 0. and (dx != 0. or dy != 0.):
            logging.error('Both rotation and move are selected')
        elif angle != 0.:
            if self.parent._rotation_center is not None:
                self.parent.rotate(angle, self.parent._rotation_center)
                self.parent.clear_cache()
        elif dx != 0. or dy != 0.:
            self.parent.move(dx,dy)
            self.parent.clear_cache()

        # FIXME : Must be positionned here to avoid bug during update of move and rotate
        #  set_legend_position and set_legend_text will call update_props... It is not a good idea !!
        posx = props[('Legend','X')]
        posy = props[('Legend','Y')]
        self.parent.set_legend_position(posx,posy)
        self.parent.set_legend_text(text)

        self.load_unload_image()

        try:
            if updateOGL:
                self.parent.parentzone.prep_listogl()

                if self.parent.parentzone.parent is None:
                    logging.critical('Problem with OpenGL update - parent/mapviewer is None -- Track this issue')

                self.parent.parentzone.parent.mapviewer.Refresh()
        except:
            logging.warning('Problem with OpenGL update - vectorproperties.fill_property')
            pass

    def _defaultprop(self):
        """
        Create the default properties for the vector and the associated UI
        """

        if self.myprops is None:
            self.myprops=Wolf_Param(title='Vector Properties', w= 500, h= 800, to_read= False, ontop= False)
            self.myprops.show_in_active_if_default = True
            self.myprops._callbackdestroy = self.destroyprop
            self.myprops._callback=self.fill_property

            self.myprops.hide_selected_buttons() # only 'Apply' button

        self.myprops.addparam('Geometry','Length 2D',99999.,Type_Param.Float,'',whichdict='Default')
        self.myprops.addparam('Geometry','Length 3D',99999.,Type_Param.Float,'',whichdict='Default')
        self.myprops.addparam('Geometry','Surface',99999.,Type_Param.Float,'',whichdict='Default')

        self.myprops.addparam('Draw','Color',(0,0,0),'Color','Drawing color',whichdict='Default')
        self.myprops.addparam('Draw','Width',1,'Integer','Drawing width',whichdict='Default')
        # self.myprops.addparam('Draw','Style',1,'Integer','Drawing style',whichdict='Default')
        self.myprops.addparam('Draw','Closed',False,'Logical','',whichdict='Default')
        self.myprops.addparam('Draw','Filled',False,'Logical','',whichdict='Default')
        self.myprops.addparam('Draw','Transparent',False,'Logical','',whichdict='Default')
        self.myprops.addparam('Draw','Alpha',0,'Integer','Transparency intensity (255 is opaque)',whichdict='Default')
        # self.myprops.addparam('Draw','Flash',False,'Logical','',whichdict='Default')

        self.myprops.addparam('Legend','Visible',False,'Logical','',whichdict='Default')

        comment = _('Text for the legend \n \
if :\n \
    - "Not used", the value will not be replaced\n \
    - "name", the value will be the name of the vector\n \
    - "first z", the value will be the z coordinate of the first vertex\n \
    - "length2D", the value will be the 2D length of the vector\n \
    - "length3D", the value will be the 3D length of the vector\n \
    - "id", the value will be the index of the vector')

        self.myprops.addparam('Legend','Text','','String',comment,whichdict='Default')

        #1--4--7
        #|  |  |
        #2--5--8
        #|  |  |
        #3--6--9
        jsonstr = new_json({_('Left'): 2, _('Right'):8, _('Top'):4, _('Bottom'):6, _('Center'):5, _('Top left'):1, _('Top right'):7, _('Bottom left'):3, _('Bottom right'):9}, _('Relative position of the legend'))
        self.myprops.addparam('Legend','Relative position',5,'Integer','',whichdict='Default', jsonstr=jsonstr)

        comment = _('Position of the legend \n \
if :\n \
    - "Not used", the value will be the median of the coordinates of the vertices\n \
    - "median", the value will be the median of the coordinates of the vertices\n \
    - "mean", the value will be the mean of the coordinates of the vertices\n \
    - "min", the value will be the minimum of the coordinates of the vertices\n \
    - "max", the value will be the maximum of the coordinates of the vertices\n \
    - "first", the value will be the coordinate of the first vertex\n \
    - "last", the value will be the coordinate of the last vertex')

        self.myprops.addparam('Legend','X',0,Type_Param.String, comment,whichdict='Default')
        self.myprops.addparam('Legend','Y',0,Type_Param.String, comment,whichdict='Default')

        self.myprops.addparam('Legend','Bold',False,'Logical','',whichdict='Default')
        self.myprops.addparam('Legend','Italic',False,'Logical','',whichdict='Default')


        jsonstr = new_json({_('Arial'): 1, _('Helvetica'):2, _('Sans Serif'):3}, _('Font name for the legend -- if not found, Arial will be used -- TTF file must be in a "fonts" directory in the same directory as the package'))
        self.myprops.addparam('Legend','Font name', 1 , 'Integer','',whichdict='Default', jsonstr=jsonstr)

        self.myprops.addparam('Legend','Font size',10,'Integer','',whichdict='Default')
        self.myprops.addparam('Legend','Color',(0,0,0),'Color','',whichdict='Default')
        self.myprops.addparam('Legend','Underlined',False,'Logical','',whichdict='Default')
        self.myprops.addparam('Legend','Length',0,'Float','',whichdict='Default')
        self.myprops.addparam('Legend','Height',0,'Float','',whichdict='Default')

        jsonstr = new_json({_('Width'): 1, _('Height'):2, _('Fontsize'):3}, _('Priority will be respected during the OpenGL plot rendering'))
        self.myprops.addparam('Legend','Priority', 3 ,'Integer', whichdict='Default', jsonstr=jsonstr)
        self.myprops.addparam('Legend','Orientation',0,'Float',whichdict='Default', comment=_('In degrees'))

        self.myprops.addparam('Image','Attached image','',Type_Param.File, '', whichdict='Default')
        self.myprops.addparam('Image','To show',False,Type_Param.Logical,'',whichdict='Default')
        self.myprops.addparam('Image','Scale',1.0,Type_Param.Float,'',whichdict='Default')
        self.myprops.addparam('Image','Relative position X',0.0,Type_Param.Float,'',whichdict='Default')
        self.myprops.addparam('Image','Relative position Y',0.0,Type_Param.Float,'',whichdict='Default')
        self.myprops.addparam('Image','Attached point X',-99999.,Type_Param.Float,'',whichdict='Default')
        self.myprops.addparam('Image','Attached point Y',-99999.,Type_Param.Float,'',whichdict='Default')

    def destroyprop(self):
        """
        Nullify the properties UI

        Destroy has been called, so the UI is not visible anymore
        """
        self.myprops=None

    def show(self):
        """
        Show the properties

        Firstly, set default values
        Then, add the current properties to the UI
        """
        self._defaultprop()
        self.update_myprops()
        self.myprops.Layout()
        self.myprops.SetSizeHints(500,800)
        self.myprops.Show()

        self.myprops.SetTitle(_('Vector properties - {}'.format(self.parent.myname)))

        icon = wx.Icon()
        icon_path = Path(__file__).parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        self.myprops.SetIcon(icon)

        self.myprops.Center()
        self.myprops.Raise()

    def show_properties(self):
        """ Show the properties -- alias of show() """

        self.show()

    def hide_properties(self):
        """ Hide the properties """

        if self.myprops is not None:
            self.myprops.Hide()

    def _convert_fontname2int(self, fontname:str) -> int:

        if fontname.lower() in 'arial.ttf':
            return 1
        elif fontname.lower() in 'helvetica.ttf':
            return 2
        elif fontname.lower() in 'sanserif.ttf':
            return 3
        else:
            return 1

    def _convert_int2fontname(self, id:int) -> str:

            if id == 1:
                return 'Arial'
            elif id == 2:
                return 'Helvetica'
            elif id == 3:
                return 'SanSerif'
            else:
                return 'Arial'

    def update_myprops(self):
        """ Update the properties """

        if self.myprops is not None:
            self.parent.update_lengths()
            self.myprops[( 'Geometry','Length 2D')] = self.parent.length2D if self.parent.length2D is not None else 0.
            self.myprops[( 'Geometry','Length 3D')] = self.parent.length3D if self.parent.length3D is not None else 0.
            self.myprops[( 'Geometry','Surface')] = self.parent.area if self.parent.area is not None else 0.

            self.myprops[('Draw','Color')]      = getRGBfromI(self.color)
            self.myprops[('Draw','Width')]      = self.width
            # self.myprops[('Draw','Style')]      = self.style
            self.myprops[('Draw','Closed')]     = self.closed
            self.myprops[('Draw','Filled')]     = self.filled
            self.myprops[('Draw','Transparent')]= self.transparent
            self.myprops[('Draw','Alpha')]          = self.alpha
            # self.myprops[('Draw','Flash')]      = self.flash
            self.myprops[('Draw','Plot indices if active')]       = self.plot_indices

            self.myprops[('Legend','Visible')]  = self.legendvisible
            self.myprops[('Legend','Text')]     = self.legendtext
            self.myprops[('Legend','Relative position')]=self.legendrelpos
            self.myprops[('Legend','X')]        = str(self.legendx)
            self.myprops[('Legend','Y')]        = str(self.legendy)
            self.myprops[('Legend','Bold')]     = self.legendbold
            self.myprops[('Legend','Italic')]   = self.legenditalic

            self.myprops[('Legend','Font name')]= self._convert_fontname2int(self.legendfontname)

            self.myprops[('Legend','Font size')]= self.legendfontsize
            self.myprops[('Legend','Color')]    = getRGBfromI(self.legendcolor)
            self.myprops[('Legend','Underlined')]= self.legendunderlined

            self.myprops[('Legend','Length')]     = self.legendlength
            self.myprops[('Legend','Height')]     = self.legendheight
            self.myprops[('Legend','Priority')]   = self.legendpriority
            self.myprops[('Legend','Orientation')]= self.legendorientation

            self.myprops[('Image','Attached image')] = str(self.attachedimage)
            self.myprops[('Image','To show')] = self.imagevisible
            self.myprops[('Image','Scale')] = self.image_scale
            self.myprops[('Image','Relative position X')] = self.image_relative_posx
            self.myprops[('Image','Relative position Y')] = self.image_relative_posy
            self.myprops[('Image','Attached point X')] = self.image_attached_pointx
            self.myprops[('Image','Attached point Y')] = self.image_attached_pointy

            if self.parent._rotation_center is not None:
                self.myprops[('Rotation','center X')] = self.parent._rotation_center[0]
                self.myprops[('Rotation','Center Y')] = self.parent._rotation_center[1]
            else:
                self.myprops[('Rotation','Center X')] = 99999.
                self.myprops[('Rotation','Center Y')] = 99999.

            if self.parent._rotation_step is not None:
                self.myprops[('Rotation','Step [degree]')] = self.parent._rotation_step
            else:
                self.myprops[('Rotation','Step [degree]')] = 99999.

            self.myprops[('Rotation', 'Angle [degree]')] = 0.

            if self.parent._move_start is not None:
                self.myprops[('Move','Start X')] = self.parent._move_start[0]
                self.myprops[('Move','Start Y')] = self.parent._move_start[1]
            else:
                self.myprops[('Move','Start X')] = 99999.
                self.myprops[('Move','Start Y')] = 99999.

            if self.parent._move_step is not None:
                self.myprops[('Move','Step [m]')] = self.parent._move_step
            else:
                self.myprops[('Move','Step [m]')] = 99999.

            self.myprops[('Move','Delta X')] = 0.
            self.myprops[('Move','Delta Y')] = 0.

            self.myprops.Populate()

    def update_image_texture(self):
        """ Update the image texture if it exists """
        if self.textureimage is not None:
            (xmin, xmax), (ymin, ymax) = self.parent.get_bounds_xx_yy()
            self.textureimage.xmin = xmin
            self.textureimage.xmax = xmax
            self.textureimage.ymin = ymin
            self.textureimage.ymax = ymax
            self.textureimage.drawing_scale = self.image_scale
            self.textureimage.offset = (self.image_relative_posx, self.image_relative_posy)

    def _offset_image_texture(self, delta_x:float, delta_y:float):
        """ Offset the image texture by a delta in x and y direction """

        if self._cached_offset is None:
            self._cached_offset = (self.image_relative_posx, self.image_relative_posy)

        self.image_relative_posx = self._cached_offset[0] + delta_x
        self.image_relative_posy = self._cached_offset[1] + delta_y

    def _reset_cached_offset(self):
        """ Reset the cached offset for the image texture """
        self._cached_offset = None

class vector:
    """
    Objet de gestion d'informations vectorielles

    Une instance 'vector' contient une liste de 'wolfvertex'
    """

    myname:str
    parentzone:"zone"
    #parentzone:Zones
    nbvertices:int
    myvertices:list[wolfvertex]
    myprop:vectorproperties

    xmin:float
    ymin:float
    xmax:float
    ymax:float

    mytree:TreeListCtrl
    myitem:TreeItemId

    def __init__(self, lines:list=[], is2D=True, name='NoName',
                 parentzone:"zone"=None, fromshapely=None, fromnumpy:np.ndarray = None) -> None:
        """

        :param lines: utile pour lecture de fichier
        :param is2D: on interprète les 'vertices' comme 2D même si chaque 'wolfvertex' contient toujours x, y et z
        :param name: nom du vecteur
        :param parentzone: instance de type 'zone' qui contient le 'vector'

        """

        self.myname=''
        self.is2D = is2D  # Force a 2D interpretation of the vertices, even if a z coordinate is present.
        # self.closed=False # True if the vector is a polygon. !! The last vertex is not necessarily the same as the first one. In this case, some routines will add a virtual segment at the end. !!

        self.mytree = None

        self.parentzone:zone
        self.parentzone=parentzone
        self.xmin=-99999.
        self.ymin=-99999.
        self.xmax=-99999.
        self.ymax=-99999.

        self._mylimits = None # ((xmin,xmax),(ymin,ymax)) --> Useful for wolf2dprev/block_contour objects

        self.textimage:Text_Image_Texture=None

        self.length2D=None
        self.length3D=None
        self._lengthparts2D=None
        self._lengthparts3D=None

        self._normals = None
        self._center_segments = None

        self._simplified_geometry = False

        if type(lines)==list:
            if len(lines)>0:
                self.myname=lines[0]
                tmp_nbvertices=int(lines[1])
                self.myvertices=[]

                if is2D:
                    for i in range(tmp_nbvertices):
                        try:
                            curx,cury=lines[2+i].split()
                        except:
                            curx,cury=lines[2+i].split(',')
                        curvert = wolfvertex(float(curx),float(cury))
                        self.myvertices.append(curvert)
                else:
                    for i in range(tmp_nbvertices):
                        try:
                            curx,cury,curz=lines[2+i].split()
                        except:
                            curx,cury,curz=lines[2+i].split(',')
                        curvert = wolfvertex(float(curx),float(cury),float(curz))
                        self.myvertices.append(curvert)

                self.myprop=vectorproperties(lines[tmp_nbvertices+2:],parent=self)

        if name!='' and self.myname=='':
            self.myname=name
            self.myvertices=[]
            self.myprop=vectorproperties(parent=self)

        self._cache_vertices = None
        self._move_start = None
        self._move_step = None

        self._rotation_center = None
        self._rotation_step = None

        self._linestring = None
        self._polygon = None

        # Utile surtout pour les sections en travers
        self.zdatum = 0.
        self.add_zdatum=False
        self.sdatum = 0.
        self.add_sdatum=False

        if fromshapely is not None:
            self.import_shapelyobj(fromshapely)

        if fromnumpy is not None:
            self.add_vertices_from_array(fromnumpy)

    def _set_limits(self):
        """ Retain current limits before any modification """

        # Set self.minx, self.maxx), (self.miny, self.maxy)
        # on basis of the self.myvertices

        self.find_minmax()
        self._mylimits = ((self.xmin, self.xmax), (self.ymin, self.ymax))

    def __add__(self, other:"vector") -> "vector":
        """ Add two vectors together """
        if not isinstance(other, vector):
            raise TypeError("Can only add vector to vector")
        new_vector = vector(name=self.myname + '_' + other.myname)
        new_vector.myvertices = self.myvertices.copy() + other.myvertices.copy()
        return new_vector

    def add_value(self, key:str, value:Union[int,float,bool,str]):
        """ Add a value to the properties """
        self.myprop[key] = value

    def get_value(self, key:str) -> Union[int,float,bool,str]:
        """ Get a value from the properties """
        return self.myprop[key]

    def set_color_from_value(self, key:str, cmap:wolfpalette | Colormap | cm.ScalarMappable, vmin:float= 0., vmax:float= 1.):
        """ Set the color from a value """
        self.myprop.set_color_from_value(key, cmap, vmin, vmax)

    def set_alpha(self, alpha:int):
        """ Set the alpha value """
        self.myprop.alpha = alpha
        self.myprop.transparent = alpha != 0

    def set_filled(self, filled:bool):
        """ Set the filled value """
        self.myprop.filled = filled

    @property
    def polygon(self) -> Polygon:
        """ Return the polygon """

        if self._polygon is None:
            self.prepare_shapely(linestring=False)
        return self._polygon

    @property
    def linestring(self) -> LineString:
        """ Return the linestring """

        if self._linestring is None:
            self.prepare_shapely(polygon=False)
        return self._linestring

    def buffer(self, distance:float, resolution:int=16, inplace:bool=True) -> "vector":
        """ Create a new vector buffered around the vector """

        poly = self.polygon
        buffered = poly.buffer(distance, resolution=resolution)

        if inplace:
            self.import_shapelyobj(buffered)
            self.reset_linestring()
            return self
        else:
            newvec = vector(fromshapely=buffered, name=self.myname)
            return newvec

    def set_legend_text(self, text:str):
        """ Set the legend text """

        if text is _('Not used'):
            pass
        elif text == _('name'):
            self.myprop.legendtext = self.myname
        elif text == _('first z'):
            if self.nbvertices>0:
                self.myprop.legendtext = str(self.myvertices[0].z)
            else:
                self.myprop.legendtext = ''
        elif text == _('length2D'):
            self.myprop.legendtext = str(self.length2D)
        elif text == _('length3D'):
            self.myprop.legendtext = str(self.length3D)
        elif text == _('id'):
            if self.parentzone is not None:
                self.myprop.legendtext = str(self.parentzone.myvectors.index(self))
            else:
                self.myprop.legendtext = ''
        else:
            self.myprop.legendtext = str(text)

        self.myprop.update_myprops()

    def set_legend_text_from_value(self, key:str, visible:bool=True):
        """ Set the legend text from a value """

        if key in self.myprop._values:
            self.myprop.legendtext = str(self.myprop._values[key])
            self.myprop.legendvisible = visible
            self.myprop.update_myprops()

    def set_legend_position(self, x:str | float, y:str | float):
        """ Set the legend position """

        if isinstance(x, str):
            if x == _('Not used'):
                pass
            elif x.lower() == _('median'):
                # valeur mediane selon x et y
                xy = self.xy
                self.myprop.legendx = np.median(xy[:,0])
            elif x.lower() == _('mean'):
                # valeur moyenne selon x et y
                xy = self.xy
                self.myprop.legendx = np.mean(xy[:,0])
            elif x.lower() == _('min'):
                # valeur minimale selon x et y
                xy = self.xy
                self.myprop.legendx = np.min(xy[:,0])
            elif x.lower() == _('max'):
                # valeur maximale selon x et y
                xy = self.xy
                self.myprop.legendx = np.max(xy[:,0])
            elif x.lower() == _('first'):
                self.myprop.legendx = self.myvertices[0].x
            elif x.lower() == _('last'):
                self.myprop.legendx = self.myvertices[-1].x
            else:
                self.myprop.legendx = float(x)
        elif isinstance(x, float):
            self.myprop.legendx = x

        if isinstance(y, str):
            if y == _('Not used'):
                pass
            elif y.lower() == _('median'):
                # valeur mediane selon x et y
                xy = self.xy
                self.myprop.legendy = np.median(xy[:,1])
            elif y.lower() == _('mean'):
                # valeur moyenne selon x et y
                xy = self.xy
                self.myprop.legendy = np.mean(xy[:,1])
            elif y.lower() == _('min'):
                # valeur minimale selon x et y
                xy = self.xy
                self.myprop.legendy = np.min(xy[:,1])
            elif y.lower() == _('max'):
                # valeur maximale selon x et y
                xy = self.xy
                self.myprop.legendy = np.max(xy[:,1])
            elif y.lower() == _('first'):
                self.myprop.legendy = self.myvertices[0].y
            elif y.lower() == _('last'):
                self.myprop.legendy = self.myvertices[-1].y
            else:
                self.myprop.legendy = float(y)
        elif isinstance(y, float):
            self.myprop.legendy = y

        self.myprop.update_myprops()

    @property
    def closed(self) -> bool:
        return self.myprop.closed

    @closed.setter
    def closed(self, value:bool):
        self.myprop.closed = value
        if self.myprop.myprops is not None:
            self.myprop.myprops.Populate()

    def set_cache(self):
        """ Set the cache for the vertices """

        self._cache_vertices = self.asnparray3d()
        self._cache_bounds = np.array([[self.xmin, self.xmax], [self.ymin, self.ymax]])

    def clear_cache(self):
        """ Clear the cache for the vertices """

        self._cache_vertices = None
        self._cache_bounds = None

    def move(self, deltax:float, deltay:float, use_cache:bool = True, inplace:bool = True):
        """
        Move the vector

        :param deltax: delta x
        :param deltay: delta y
        :param use_cache: use the cache if available
        :param inplace: move the vector inplace or return a new vector
        """

        if self._move_step is not None:
            deltax = np.round(deltax/self._move_step)*self._move_step
            deltay = np.round(deltay/self._move_step)*self._move_step

        if inplace:
            if use_cache and self._cache_vertices is None:
                self.set_cache()

            if use_cache:
                self.xy = self._cache_vertices[:,:2] + np.array([deltax, deltay])
                self.xmin = self._cache_bounds[0,0] + deltax
                self.xmax = self._cache_bounds[0,1] + deltax
                self.ymin = self._cache_bounds[1,0] + deltay
                self.ymax = self._cache_bounds[1,1] + deltay
            else:
                for curvert in self.myvertices:
                    curvert.x += deltax
                    curvert.y += deltay
                # update the bounds
                self.xmin += deltax
                self.xmax += deltax
                self.ymin += deltay
                self.ymax += deltay

            # update the texture image position if it exists
            if self.myprop.textureimage is not None:
                self.myprop.textureimage.xmin = self.xmin
                self.myprop.textureimage.xmax = self.xmax
                self.myprop.textureimage.ymin = self.ymin
                self.myprop.textureimage.ymax = self.ymax

            return self
        else:
            new_vector = self.deepcopy_vector(self.myname + '_moved')
            new_vector.move(deltax, deltay, inplace=True)

            return new_vector

    def rotate(self, angle:float, center:tuple[float,float]=(0.,0.), use_cache:bool = True, inplace:bool = True):
        """
        Rotate the vector

        :param angle: angle in degrees
        :param center: center of the rotation
        :param use_cache: use the cache if available
        :param inplace: rotate the vector inplace or return a new vector
        """

        if inplace:
            if use_cache and self._cache_vertices is None:
                self.set_cache()

            if use_cache:
                locxy = self._cache_vertices[:,:2] - np.array(center)

                rotation_matrix = np.array([[np.cos(np.radians(angle)), -np.sin(np.radians(angle))],
                                            [np.sin(np.radians(angle)), np.cos(np.radians(angle))]])

                self.xy = np.dot(locxy, rotation_matrix) + np.array(center)
            else:
                for curvert in self.myvertices:
                    curvert.rotate(angle, center)

            self.find_minmax()

            if self.myprop.textureimage is not None:
                self.myprop.textureimage.xmin = self.xmin
                self.myprop.textureimage.xmax = self.xmax
                self.myprop.textureimage.ymin = self.ymin
                self.myprop.textureimage.ymax = self.ymax

            return self
        else:
            new_vector = self.deepcopy_vector(self.myname + '_rotated')
            new_vector.rotate(angle, center, inplace=True)

            return new_vector

    def rotate_xy(self, x:float, y:float, use_cache:bool = True, inplace:bool = True):
        """ Rotate the vector around the rotation center and a xy point """

        if self._rotation_center is None:
            logging.error('No rotation center defined -- set it before rotating by this routine')
            return self

        angle = np.degrees(np.arctan2(-(y-self._rotation_center[1]), x-self._rotation_center[0]))

        if self._rotation_step is not None:
            angle = np.round(angle/self._rotation_step)*self._rotation_step

        return self.rotate(angle, center=self._rotation_center, use_cache=use_cache, inplace=inplace)

    def get_mapviewer(self):
        """
        Retourne l'instance de la mapviewer
        """
        if self.parentzone is not None:
            return self.parentzone.get_mapviewer()
        else:
            return None

    def show_properties(self):
        """ Show the properties """

        if self.myprop is not None:
            self.myprop.show()

    def hide_properties(self):
        """ Hide the properties """

        if self.myprop is not None:
            self.myprop.hide_properties()

    def get_normal_segments(self, update: bool = False) -> np.ndarray:
        """
        Return the normals of each segment

        The normals are oriented to the left
        """

        if self._normals is not None and not update:
            return self._normals

        if self.nbvertices<2:
            return None

        xy = self.asnparray()
        delta = xy[1:]-xy[:-1]
        norm = np.sqrt(delta[:,0]**2+delta[:,1]**2)
        normals = np.zeros_like(delta)
        notnull = np.where(norm!=0)
        normals[notnull,0] = -delta[notnull,1]/norm[notnull]
        normals[notnull,1] = delta[notnull,0]/norm[notnull]

        self._normals = normals

        return normals

    def get_center_segments(self, update: bool = False) -> np.ndarray:
        """
        Return the center of each segment
        """

        if self._center_segments is not None and not update:
            return self._center_segments

        if self.nbvertices<2:
            return None

        xy = self.asnparray()
        centers = (xy[1:]+xy[:-1])/2.

        self._center_segments = centers
        
        return centers

    @property
    def nbvertices(self) -> int:
        return len(self.myvertices)

    @property
    def used(self) -> bool:
        return self.myprop.used

    @used.setter
    def used(self, value:bool):
        self.myprop.used = value

    def import_shapelyobj(self, obj):
        """ Importation d'un objet shapely """

        self.myvertices = []
        if isinstance(obj, LineString):
            self.is2D = not obj.has_z
            xyz = np.array(obj.coords)
            self.add_vertices_from_array(xyz)

        elif isinstance(obj, Polygon):
            self.is2D = not obj.has_z
            xyz = np.array(obj.exterior.coords)
            self.add_vertices_from_array(xyz)
            self.close_force()
        else:
            logging.warning(_('Object type {} not supported -- Update "import_shapelyobj"').format(type(obj)))

    def get_bounds(self, grid:float = None):
        """
        Return tuple with :
          - (lower-left corner), (upper-right corner)

        If you want [[xmin,xmax],[ymin,ymax]], use get_bounds_xx_yy() instead.

        """
        if grid is None:
            return ((self.xmin, self.ymin), (self.xmax, self.ymax))
        else:
            xmin = float(np.int(self.xmin/grid)*grid)
            ymin = float(np.int(self.ymin/grid)*grid)

            xmax = float(np.ceil(self.xmax/grid)*grid)
            ymax = float(np.ceil(self.ymax/grid)*grid)
            return ((xmin, ymin), (xmax, ymax))

    def get_bounds_xx_yy(self, grid:float = None):
        """
        Return tuple with :
          - (xmin,xmax), (ymin, ymax)

        If you want [[lower-left corner],[upper-right corner]], use get_bounds() instead.

        """
        if grid is None:
            return ((self.xmin, self.xmax), (self.ymin, self.ymax))
        else:
            xmin = float(np.int(self.xmin/grid)*grid)
            ymin = float(np.int(self.ymin/grid)*grid)

            xmax = float(np.ceil(self.xmax/grid)*grid)
            ymax = float(np.ceil(self.ymax/grid)*grid)
            return ((xmin, xmax), (ymin, ymax))

    def get_mean_vertex(self, asshapelyPoint = False):
        """ Return the mean vertex """

        if self.closed or (self.myvertices[0].x == self.myvertices[-1].x and self.myvertices[0].y == self.myvertices[-1].y):
            # if closed, we don't take the last vertex otherwise we have a double vertex
            x_mean = np.mean([curvert.x for curvert in self.myvertices[:-1]])
            y_mean = np.mean([curvert.y for curvert in self.myvertices[:-1]])
            z_mean = np.mean([curvert.z for curvert in self.myvertices[:-1]])
        else:
            x_mean = np.mean([curvert.x for curvert in self.myvertices])
            y_mean = np.mean([curvert.y for curvert in self.myvertices])
            z_mean = np.mean([curvert.z for curvert in self.myvertices])

        if asshapelyPoint:
            return Point(x_mean, y_mean, z_mean)
        else:
            return wolfvertex(x_mean, y_mean, z_mean)

    def highlighting(self, rgb=(255,0,0), linewidth=3):
        """
        Mise en évidence
        """

        self._oldcolor = self.myprop.color
        self._oldwidth = self.myprop.color

        self.myprop.color = getIfromRGB(rgb)
        self.myprop.width = linewidth

    def withdrawal(self):
        """
        Mise en retrait
        """

        try:
            self.myprop.color = self._oldcolor
            self.myprop.width = self._oldwidth
        except:
            self.myprop.color = 0
            self.myprop.width = 1

    def save(self,f):
        """
        Sauvegarde sur disque
        """

        f.write(self.myname+'\n')
        f.write(str(self.nbvertices)+'\n')

        force3D=False
        if self.parentzone is not None:
            force3D = self.parentzone.parent.force3D

        if self.is2D and not force3D:
            for curvert in self.myvertices:
                f.write(f'{curvert.x},{curvert.y}'+'\n')
        else:
            for curvert in self.myvertices:
                f.write(f'{curvert.x},{curvert.y},{curvert.z}'+'\n')

        self.myprop.save(f)

    def reverse(self):
        """Renverse l'ordre des vertices"""

        self.myvertices.reverse()

    def isinside(self,x,y):
        """Teste si la coordonnée (x,y) est dans l'objet -- en 2D"""

        if self.nbvertices==0:
            return False

        poly = self.polygon
        inside2 = poly.contains(Point([x,y]))
        return inside2

    def contains(self, x:float, y:float) -> bool:
        """ alias for isinside """
        return self.isinside(x, y)

    def asshapely_pol(self) -> Polygon:
        """
        Conversion des coordonnées en Polygon Shapely
        """

        if self.nbvertices<3:
            return Polygon()

        coords=self.asnparray()
        return Polygon(coords)

    def asshapely_pol3D(self) -> Polygon:
        """
        Conversion des coordonnées en Polygon Shapely
        """

        if self.nbvertices<3:
            return Polygon()

        coords=self.asnparray3d()
        return Polygon(coords)

    def asshapely_ls3d(self) -> LineString:
        """
        Conversion des coordonnées en Linestring Shapely
        """

        coords=self.asnparray3d()
        return LineString(coords)

    def asshapely_ls(self) -> LineString:
        """
        Conversion des coordonnées en Linestring Shapely
        """

        coords=self.asnparray3d()
        return LineString(coords)

    def asshapely_mp(self) -> MultiPoint:
        """
        Conversion des coordonnées en Multipoint Shapely
        """

        multi=self.asnparray3d()
        return MultiPoint(multi)

    def asnparray(self):
        """
        Conversion des coordonnées en Numpy array -- en 2D

        return : np.ndarray -- shape = (nb_vert,2)

        """

        return np.asarray(list([vert.x,vert.y] for vert in self.myvertices))

    def asnparray3d(self):
        """
        Conversion des coordonnées en Numpy array -- en 3D

        return : np.ndarray -- shape = (nb_vert,3)

        """
        xyz= np.asarray(list([vert.x,vert.y,vert.z] for vert in self.myvertices))

        if self.add_zdatum:
            xyz[:,2]+=self.zdatum
        return xyz

    def prepare_shapely(self, prepare_shapely:bool = True, linestring:bool = True, polygon:bool = True):
        """
        Conversion Linestring Shapely et rétention de l'objet afin d'éviter de multiples appels
        par ex. dans une boucle.

        :param prepare_shapely: Préparation de l'objet Shapely pour une utilisation optimisée
                                - True par défaut
                                - see https://shapely.readthedocs.io/en/stable/reference/shapely.prepare.html
        :param linestring: Préparation du linestring
        :param polygon: Préparation du polygon

        """

        self.reset_linestring()

        if linestring:
            self._linestring = self.asshapely_ls()
        if polygon:
            self._polygon = self.asshapely_pol()

        if prepare_shapely:
            if linestring:
                if not self._linestring.is_empty:
                    prepare(self._linestring)
            if polygon:
                # Test if empty or not
                if not self._polygon.is_empty:
                    prepare(self._polygon)


    def projectontrace(self, trace:"vector"):
        """
        Projection du vecteur sur une trace (type 'vector')

        :return: Nouveau vecteur contenant les infos de position sur la trace et d'altitude (s,z) aux positions (x,y)
        """

        # trace:vector
        tracels:LineString
        tracels = trace.asshapely_ls() # conversion en linestring Shapely

        xyz = self.asnparray3d() # récupération des vertices en numpy array
        all_s = [tracels.project(Point(cur[0],cur[1])) for cur in xyz] # Projection des points sur la trace et récupération de la coordonnées curviligne

        # création d'un nouveau vecteur
        newvec = vector(name=_('Projection on ')+trace.myname)
        for s,(x,y,z) in zip(all_s,xyz):
            newvec.add_vertex(wolfvertex(s,z))

        return newvec

    def parallel_offset(self, distance=5., side:Literal['left', 'right']='left'):
        """
        Create a parallel offset of the vector

        :param distance: The distance parameter must be a positive float value.
        :param side: The side parameter may be ‘left’ or ‘right’. Left and right are determined by following the direction of the given geometric points of the LineString.
        """

        if self.nbvertices<2:
            return None

        myls = self.asshapely_ls()

        mypar = myls.parallel_offset(distance=abs(distance), side=side, join_style=JOIN_STYLE.round)

        if mypar.geom_type=='MultiLineString':
            return None


        if len(mypar.coords) >0:
            # if side=='right':
            #     #On souhaite garder une même orientation pour les vecteurs
            #     mypar = substring(mypar, 1., 0., normalized=True)

            newvec = vector(name='par' + str(distance) +'_'+ self.myname, parentzone= self.parentzone)

            for x,y in mypar.coords:
                xy = Point(x,y)
                curs = mypar.project(xy, True)
                curz = myls.interpolate(curs,True).z

                newvert = wolfvertex(x,y,curz)
                newvec.add_vertex(newvert)

            return newvec
        else:
            return None

    def intersection(self, vec2:"vector" = None, eval_dist=False,norm=False, force_single=False):
        """
        Calcul de l'intersection avec un autre vecteur
        Attention, le shapely du vecteur vec2 et self sont automatiquement préparés. Si modifié après intersection, il faut penser à les re-préparer
        avec self.reset_linestring() ou self.prepare_shapely(). Dans le cas contraire, les anciens vecteurs préparés seront utilisés.

        Return :
         - le point d'intersection
         - la distance (optional) le long de 'self'

        Utilisation de Shapely
        """

        # check if the vectors are closed
        ls1 = self.linestring
        ls2 = vec2.linestring
        # ls1 = self.asshapely_ls() if self._linestring is None else self._linestring
        # ls2 = vec2.asshapely_ls() if vec2._linestring is None else vec2._linestring


        myinter = ls1.intersection(ls2)

        if isinstance(myinter, MultiPoint):
            if force_single:
                myinter = myinter.geoms[0]
        elif isinstance(myinter, MultiLineString):
            if force_single:
                myinter = Point(myinter.geoms[0].xy[0][0],myinter.geoms[0].xy[1][0])

        if myinter.is_empty:
            if eval_dist:
                return None, None
            else:
                return None

        if eval_dist:
            mydists = ls1.project(myinter,normalized=norm)
            return myinter,mydists
        else:
            return myinter

    def intersects(self, x:float, y:float) -> bool:
        """ Check if the point (x, y) intersects with the vector. """
        point = Point(x, y)
        return self.linestring.intersects(point)

    def aligned_with(self, x:float, y:float, tolerance:float = 1e-6) -> bool:
        """ Check if the point (x, y) is aligned with the vector. """
        return self.intersects(x, y) and self.linestring.distance(Point(x, y)) < tolerance

    def reset(self):
        """Remise à zéro"""
        self.myvertices=[]
        self.reset_linestring()

    def reset_linestring(self):
        """Remise à zéro de l'objet Shapely"""

        if self._linestring is not None:
            if is_prepared(self._linestring):
                destroy_prepared(self._linestring)
            self._linestring=None

        if self._polygon is not None:
            if is_prepared(self._polygon):
                destroy_prepared(self._polygon)
            self._polygon=None

    def add_vertex(self,addedvert: Union[list[wolfvertex], wolfvertex]):
        """
        Ajout d'un wolfvertex
        Le compteur est automatqiuement incrémenté
        """
        if type(addedvert) is list:
            for curvert in addedvert:
                self.add_vertex(curvert)
        else:
            assert(addedvert is not None)
            assert isinstance(addedvert, wolfvertex)
            self.myvertices.append(addedvert)

    def add_vertices_from_array(self, xyz:np.ndarray):
        """
        Ajout de vertices depuis une matrice numpy -- shape = (nb_vert,2 ou 3)
        """

        assert isinstance(xyz, np.ndarray), "xyz must be a numpy array of shape (nb_vert, 2 or 3)"

        if xyz.dtype==np.int32:
            xyz = xyz.astype(np.float64)

        if xyz.shape[1]==3:
            for cur in xyz:
                self.add_vertex(wolfvertex(cur[0], cur[1], cur[2]))
        elif xyz.shape[1]==2:
            for cur in xyz:
                self.add_vertex(wolfvertex(cur[0], cur[1]))

    def count(self):
        """
        Retroune le nombre de vertices

        For compatibility with older version of the code --> use 'nbvertices' property instead
        Must be removed in the future
        """
        # Nothing to do because nbvertices is a property
        # self.nbvertices=len(self.myvertices)
        return

    def close_force(self):
        """
        Force la fermeture du 'vector'

        Commence par vérifier si le premier point possède les mêmes coords que le dernier
        Si ce n'est pas le cas, on ajoute un wolfvertes

        self.closed -> True
        """
        """ A polygon is closed either if
        - it has the `closed` attribute.
        - it has not the `closed` attribute, in which case there must be
          a repeated vertex in its vertices.
        """
        # FIXME With this code, it is possible to have apolygon marked
        # as closed but without an actual closing vertex...

        # FIXME Wouldn't it be better to have a vector that can be
        # requested to become a closed or not closed one, depending
        # on the needs of the caller ?

        # First condition checks that the same vertex is not at the
        # beginning and end of the vector (it it was, vector would be closed)
        # second and third condition tests that, if begin and end vertices
        # are different, they also have different coordinates (this
        # again checks that the vector is not closed; in the case where
        # two vertices are not the same one but have the same coordinates)

        is_open = not((self.myvertices[-1] is self.myvertices[0]) or \
            (self.myvertices[-1].x==self.myvertices[0].x and \
             self.myvertices[-1].y==self.myvertices[0].y))

        if not self.is2D :
            is_open = is_open or self.myvertices[-1].z!=self.myvertices[0].z

        if is_open:
            self.add_vertex(self.myvertices[0])
        self.closed=True

    def force_to_close(self):
        """ Force the vector to be closed """

        self.close_force()

    def _nblines(self):
        """
        routine utile pour l'initialisation sur base de 'lines'
        """
        return self.nbvertices+5

    def verify_s_ascending(self):
        """
        Vérifie que les points d'un vecteur sont énumérés par distances 2D croissantes

        Utile notamment pour le traitement d'interpolation de sections en travers afin d'éviter une triangulation non valable suite à des débords
        """
        s,z=self.get_sz(cumul=False)

        correction=False
        where=[]

        for i in range(self.nbvertices-1):
            if s[i]>s[i+1]:
                #inversion si le points i est plus loin que le i+1
                correction=True
                where.append(i+1)

                x=self.myvertices[i].x
                y=self.myvertices[i].y

                self.myvertices[i].x=self.myvertices[i+1].x
                self.myvertices[i].y=self.myvertices[i+1].y

                self.myvertices[i+1].x=x
                self.myvertices[i+1].y=y

        return correction,where

    def find_nearest_vert(self,x,y):
        """
        Trouve le vertex le plus proche de la coordonnée (x,y) -- en 2D
        """
        xy=Point(x,y)
        mynp = self.asnparray()
        mp = MultiPoint(mynp)
        near = np.asarray(nearest_points(mp,xy)[0].coords)
        return self.myvertices[np.asarray(np.argwhere(mynp==near[0])[0,0])]

    def insert_nearest_vert(self,x,y):
        """
        Insertion d'un nouveau vertex au plus proche de la coordonnée (x,y) -- en 2D
        """
        xy=Point(x,y)
        mynp = self.asnparray()
        mp = MultiPoint(mynp)
        ls = LineString(mynp)

        nearmp = nearest_points(mp,xy) #point le plus proche sur base du nuage
        nearls = nearest_points(ls,xy) #point le plus proche sur base de la ligne

        smp = ls.project(nearmp[0]) #distance le long de la ligne du sommet le plus proche
        sls = ls.project(nearls[0]) #distance le long de la ligne du point le plus proche au sens géométrique (perpendiculaire au segment)

        indexmp= np.argwhere(mynp==np.asarray([nearmp[0].x, nearmp[0].y]))[0,0] #index du vertex

        if indexmp==0 and self.closed:
            #le vecteur est fermé
            #il faut donc chercher à savoir si le point est après le premier point ou avant le dernier (qui possèdent les mêmes coords)
            if sls<=ls.length and sls >=ls.project(Point([self.myvertices[-2].x,self.myvertices[-2].y])):
                smp=ls.length
                indexmp=self.nbvertices-1
            else:
                indexmp=1
        else:
            if sls >= smp:
                #le point projeté sur la droite est au-delà du vertex le plus proche
                #on ajoute donc le point après
                indexmp+=1

        myvert=wolfvertex(x,y)
        self.myvertices.insert(indexmp,myvert)

        return self.myvertices[indexmp]

    def update_image_texture(self):
        """
        Met à jour la texture de l'image si elle existe
        """

        self.myprop.update_image_texture()

    def find_minmax(self, only_firstlast:bool=False):
        """
        Recherche l'extension spatiale du vecteur

        :param only_firstlast: si True, on ne recherche que les coordonnées du premier et du dernier vertex
        """

        if self.nbvertices > 0:

            if only_firstlast:
                self.xmin=min(self.myvertices[0].x, self.myvertices[-1].x)
                self.ymin=min(self.myvertices[0].y, self.myvertices[-1].y)
                self.xmax=max(self.myvertices[0].x, self.myvertices[-1].x)
                self.ymax=max(self.myvertices[0].y, self.myvertices[-1].y)
            else:
                self.xmin=min(vert.x for vert in self.myvertices)
                self.ymin=min(vert.y for vert in self.myvertices)
                self.xmax=max(vert.x for vert in self.myvertices)
                self.ymax=max(vert.y for vert in self.myvertices)

            self.update_image_texture()
        else:
            self.xmin=-99999.
            self.ymin=-99999.
            self.xmax=-99999.
            self.ymax=-99999.

    @property
    def has_interior(self):
        """ Return True if the vector has an interior """

        not_in_use = [curvert for curvert in self.myvertices if not curvert.in_use]

        return len(not_in_use) > 0

    def check_if_interior_exists(self):
        """ Check if the vector has an interior and adapt in_use accordingly.

        The verification is only made in 2D, as the interior is defined as a pair of segments that correspond exactly to the same coordinates.
        Z coordinates are not taken into account in this verification.

                """

        xy = self.xy
        if self.closed and (xy[0,0] == xy[-1,0] and xy[0,1] == xy[-1,1]):
            # If the vector is closed, we remove the last vertex to avoid checking it
            xy = xy[:-1]

        xy_unique, inverse, count = np.unique(xy, return_inverse=True, return_counts=True, axis=0)

        duplicate_found = False

        if xy.shape[0] != xy_unique.shape[0]:
            # There are duplicates, we need to test if the duplicate form a segment

            # Find the duplicate indices
            duplicate_indices = np.where(count > 1)[0]
            # Find the inverse indices of the duplicates
            duplicate_indices = np.where(np.isin(inverse, duplicate_indices))[0]
            diff = np.diff(duplicate_indices)

            for i in range(len(diff)):
                # Set the in_use property to False for the vertices that are not used
                if diff[i] == 1:
                    self.myvertices[duplicate_indices[i+1]].in_use = False
                    duplicate_found = True

        if duplicate_found:
            self.reset_linestring()
            self._reset_listogl()


    @property
    def nb_interiors(self) -> int:
        """ Return the number of interiors in the vector.

        If the vector is filled, it returns the number of pairs of vertices not in use.
        If the vector is not filled, it returns the number of vertices not in use.
        """
        not_in_use = [curvert for curvert in self.myvertices if not curvert.in_use]

        return len(not_in_use) // 2 if self.myprop.filled else len(not_in_use)

    @property
    def _parts(self) -> "zone":
        """ Return the parts of the vector as a zone.

        Useful for creating subpolygons or triangulation.
        """
        self.find_minmax()

        parts = zone()
        current_part = vector()
        for curvert in self.myvertices:
            if curvert.in_use:
                current_part.add_vertex(curvert)
            else:
                if current_part.nbvertices > 0:
                    if parts.nbvectors > 0:
                        current_part.force_to_close()
                    parts.add_vector(current_part)
                current_part = vector()

        for curvert in current_part.myvertices:
            parts.myvectors[0].add_vertex(curvert)

        parts.myvectors[0].force_to_close()

        return parts

    def get_subpolygons(self) -> list[list[wolfvertex]]:
        """
        Return a list of polygons from the vector

        If the vector has no interior, the list contains the whole vector as a polygon
        """

        if self.nbvertices == 0:
            logging.debug(_('Vector {} has no vertices -- cannot create subpolygons').format(self.myname))
            return []

        if self.myprop.filled:
            if self.has_interior:
                #En attendant de lier WOLF-Fortran, on utilise la triangulation contrainte de la librairie Triangle -- https://rufat.be/triangle/

                parts = self._parts
                tri = parts.create_constrainedDelaunay(nb = 0)
                centroid_interiors = [part.centroid for part in parts.myvectors[1:]]
                tri.unuse_triangles_containing_points(centroid_interiors)

                return tri.get_triangles_as_listwolfvertices()

            else:
                if self._simplified_geometry:
                    if self.myprop.closed and (self.myvertices[0].x != self.myvertices[-1].x or self.myvertices[0].y != self.myvertices[-1].y):
                        return [self.myvertices + [self.myvertices[0]]]
                    else:
                        return [self.myvertices]
                else:
                    if self.polygon.area == 0:
                        logging.debug(_('Vector {} has no area -- cannot create triangulation').format(self.myname))
                        return []
                    else:
                        xx, yy = self.polygon.exterior.xy

                        # On translate les coordonnées pour éviter les erreurs de triangulation
                        tr_x = np.array(xx).min()
                        tr_y = np.array(yy).min()

                        xx = np.array(xx)-tr_x
                        yy = np.array(yy)-tr_y

                        geom = {'vertices' : [[x,y] for x,y in zip(xx[:-1],yy[:-1])], 'segments' : [[i,i+1] for i in range(len(xx)-2)]+[[len(xx)-2,0]]}

                        try:
                            delaunay = triangle.triangulate(geom, 'p')
                            tri = []
                            for curtri in delaunay['triangles']:
                                # on traduit les coordonnées pour revenir dans le monde réel
                                tri.append([wolfvertex(delaunay['vertices'][curtri[i]][0] + tr_x, delaunay['vertices'][curtri[i]][1] + tr_y) for i in range(3)])
                            return tri
                        except:
                            pass

        else:
            if self.has_interior:
                # not_in_use = [curvert for curvert in self.myvertices if not curvert.in_use]

                alls = []

                new_poly = []
                alls.append(new_poly)

                for curvert in self.myvertices:
                    if curvert.in_use:
                        new_poly.append(curvert)
                    else:
                        new_poly = []
                        alls.append(new_poly)
                        new_poly.append(curvert)

                if self.myprop.closed and (self.myvertices[0].x != self.myvertices[-1].x or self.myvertices[0].y != self.myvertices[-1].y):
                    alls[0].append(self.myvertices[0])

                return alls
            else:
                if self.myprop.closed and (self.myvertices[0].x != self.myvertices[-1].x or self.myvertices[0].y != self.myvertices[-1].y):
                    return [self.myvertices + [self.myvertices[0]]]
                else:
                    return [self.myvertices]

    def _plot_square_at_vertices(self, size=5):
        """
        Plot small squares at each vertex, in OpenGL
        """

        if self.nbvertices == 0:
            return

        curvert: wolfvertex
        ongoing = True

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        # if filled:
        #     glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glPointSize(size)
        rgb = getRGBfromI(self.myprop.color)
        glBegin(GL_POINTS)
        for curvert in self.myvertices:
            glColor3ub(int(rgb[0]), int(rgb[1]), int(rgb[2]))
            glVertex2f(curvert.x, curvert.y)
        glEnd()

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        ongoing = False

    def _plot_index_vertex(self, idx:int = None, xy:tuple[float,float] = None,
                           sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot OpenGL

        :param idx: index of the vertex to plot
        :param xy: coordinates (x,y) of the vertex to plot
        :param sx: scale x
        :param sy: scale y
        :param xmin: minimum x
        :param ymin: minimum y
        :param xmax: maximum x
        :param ymax: maximum y
        :param size: size of the text
        """
        if self.get_mapviewer() is None:
            logging.warning(_('No mapviewer available for legend plot'))
            return

        if xy is not None:
            x, y = xy
            curvert = self.find_nearest_vert(x, y)
            idx = self.myvertices.index(curvert)
        elif idx is not None:
            if idx < 0 or idx >= self.nbvertices:
                logging.warning(_('Index {} out of range for vector {}').format(idx, self.myname))
                return
            curvert = self.myvertices[idx]
        else:
            logging.warning(_('No index or coordinates provided for plotting index vertex'))
            return

        if not (xmin is None or ymin is None or xmax is None or ymax is None):
            if curvert.x < xmin or curvert.x > xmax or curvert.y < ymin or curvert.y > ymax:
                logging.debug(_('Vertex {} at ({},{}) is out of bounds ({},{},{},{}))'.format(idx, curvert.x, curvert.y, xmin, ymin, xmax, ymax)))
                return

        self._textimage = Text_Image_Texture(str(idx+1),
                                            self.get_mapviewer(), # mapviewer de l'instance Zones qui contient le vecteur
                                            self._get_textfont_idx(),
                                            self,
                                            curvert.x,
                                            curvert.y)
        self._textimage.paint()

    def _plot_all_indices(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot all indices of the vertices in OpenGL
        :param sx: scale x
        :param sy: scale y
        :param xmin: minimum x
        :param ymin: minimum y
        :param xmax: maximum x
        :param ymax: maximum y
        :param size: size of the text
        """
        if self.get_mapviewer() is None:
            logging.warning(_('No mapviewer available for legend plot'))
            return
        if self.nbvertices == 0:
            logging.warning(_('No vertices to plot indices for vector {}').format(self.myname))
            return
        if self.myprop.used:
            for idx in range(self.nbvertices):
                self._plot_index_vertex(idx=idx, sx=sx, sy=sy, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, size=size)

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot OpenGL
        """
        if self.myprop.used:

            if self.myprop.filled:
                glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
            else:
                glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)

            rgb=getRGBfromI(self.myprop.color)

            if self.myprop.transparent:
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                # glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
            else:
                glDisable(GL_BLEND)

            glLineWidth(float(self.myprop.width))
            #glPointSize(float(self.myprop.width))

            if self.myprop.transparent:
                glColor4ub(int(rgb[0]),int(rgb[1]),int(rgb[2]),int(self.myprop.alpha))
            else:
                glColor3ub(int(rgb[0]),int(rgb[1]),int(rgb[2]))

            if self.myprop.filled:

                # ls = self.polygon

                if False:

                    #FIXME : Shapely have not constrained Delaunay triangulation -- using Delaunay from Wolf Fortran instead
                    ls = ls.segmentize(.1)
                    delaunay = delaunay_triangles(ls)

                    for curpol in delaunay.geoms:
                        if ls.contains(curpol.centroid):
                            glBegin(GL_POLYGON)
                            for curvert in curpol.exterior.coords:
                                glVertex2d(curvert[0],curvert[1])
                            glEnd()
                        else:
                            logging.debug(_('Polygon not in Polygon'))

                else:
                    # #En attendant de lier WOLF-Fortran, on utilise la triangulation contrainte de la librairie Triangle -- https://rufat.be/triangle/
                    # xx, yy = ls.exterior.xy

                    # # On translate les coordonnées pour éviter les erreurs de triangulation
                    # tr_x = np.array(xx).min()
                    # tr_y = np.array(yy).min()

                    # xx = np.array(xx)-tr_x
                    # yy = np.array(yy)-tr_y

                    # geom = {'vertices' : [[x,y] for x,y in zip(xx[:-1],yy[:-1])], 'segments' : [[i,i+1] for i in range(len(xx)-2)]+[[len(xx)-2,0]]}

                    # try:
                    #     delaunay = triangle.triangulate(geom, 'p')
                    #     for curtri in delaunay['triangles']:
                    #         glBegin(GL_POLYGON)
                    #         for i in range(3):
                    #             # on retraduit les coordonnées pour revenir dans le monde réel
                    #             glVertex2d(delaunay['vertices'][curtri[i]][0] + tr_x, delaunay['vertices'][curtri[i]][1] + tr_y)
                    #         glEnd()
                    # except:
                    #     pass

                    all_polys = self.get_subpolygons()
                    for curpoly in all_polys:
                        glBegin(GL_POLYGON)
                        for curvertex in curpoly:
                            glVertex2d(curvertex.x, curvertex.y)
                        glEnd()

            else:
                all_polys = self.get_subpolygons()

                for curpoly in all_polys:

                    glBegin(GL_LINE_STRIP)

                    for curvertex in curpoly:
                        glVertex2d(curvertex.x, curvertex.y)

                    glEnd()

            glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
            glDisable(GL_BLEND)
            glLineWidth(1.0)

    def plot_legend(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot OpenGL

        Legend is an image texture
        """
        if self.get_mapviewer() is None:
            logging.warning(_('No mapviewer available for legend plot'))
            return

        if self.myprop.legendvisible and self.myprop.used:

            self.textimage = Text_Image_Texture(self.myprop.legendtext,
                                                self.get_mapviewer(), # mapviewer de l'instance Zones qui contient le vecteur
                                                self._get_textfont(),
                                                self,
                                                self.myprop.legendx,
                                                self.myprop.legendy)
            self.textimage.paint()
        else:
            self.textimage = None

    def plot_legend_mpl(self, ax:plt.Axes):
        """
        Plot Legend on Matplotlib Axes
        """

        if self.myprop.legendvisible and self.myprop.used:

            ax.text(self.myprop.legendx, self.myprop.legendy, self.myprop.legendtext,
                    fontsize=self.myprop.legendfontsize,
                    fontname=self.myprop.legendfontname,
                    color=getRGBfromI(self.myprop.legendcolor),
                    rotation=self.myprop.legendorientation,
                    ha='center', va='center')

    def plot_image(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """ plot attached images """

        if self.get_mapviewer() is None:
            logging.warning(_('No mapviewer available for image plot'))
            return

        if self.myprop.imagevisible and self.myprop.used:

            try:

                if self.myprop.textureimage is None:
                    self.myprop.load_unload_image()

                if self.myprop.textureimage is not None:
                    self.myprop.textureimage.paint()
                else:
                    logging.warning(_('No image texture available for plot'))
            except Exception as e:
                logging.error(_('Error while plotting image texture: {}').format(e))

    def plot_matplotlib(self, ax:plt.Axes | tuple[Figure, Axes] = None):
        """
        Plot Matplotlib - XY coordinates ONLY

        :param ax: Matplotlib Axes to plot on or a tuple (fig, ax) where fig is the figure and ax is the axes.
        If ax is None, a new figure and axes will be created.
        """

        if isinstance(ax, tuple):
            # if ax is a tuple, we assume it is (fig, ax)
            fig, ax = ax
        elif ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        if self.myprop.used:

            if self.myprop.filled:
                rgb=getRGBfromI(self.myprop.color)
                subpoly = self.get_subpolygons()
                for curpoly in subpoly:
                    if self.myprop.transparent:
                        ax.fill([curvert.x for curvert in curpoly], [curvert.y for curvert in curpoly], color=(rgb[0]/255.,rgb[1]/255.,rgb[2]/255.,self.myprop.alpha))
                    else:
                        ax.fill([curvert.x for curvert in curpoly], [curvert.y for curvert in curpoly], color=(rgb[0]/255.,rgb[1]/255.,rgb[2]/255.))
            else:
                rgb=getRGBfromI(self.myprop.color)
                subpoly = self.get_subpolygons()
                for curpoly in subpoly:
                    if self.myprop.transparent:
                        ax.plot([curvert.x for curvert in curpoly], [curvert.y for curvert in curpoly], color=(rgb[0]/255.,rgb[1]/255.,rgb[2]/255.,self.myprop.alpha), linewidth=self.myprop.width)
                    else:
                        ax.plot([curvert.x for curvert in curpoly], [curvert.y for curvert in curpoly], color=(rgb[0]/255.,rgb[1]/255.,rgb[2]/255.), linewidth=self.myprop.width)

            self.plot_legend_mpl(ax)

        return fig, ax

    def plot_matplotlib_sz(self, ax:plt.Axes | tuple[Figure, Axes] = None):
        """
        Plot Matplotlib - SZ coordinates ONLY.

        S is the curvilinear abscissa, Z is the elevation.

        :param ax: Matplotlib Axes to plot on or a tuple (fig, ax) where fig is the figure and ax is the axes.
        If ax is None, a new figure and axes will be created.
        """

        if isinstance(ax, tuple):
            # if ax is a tuple, we assume it is (fig, ax)
            fig, ax = ax
        elif ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        if self.myprop.used:
            s,z = self.sz_curvi

            rgb=getRGBfromI(self.myprop.color)
            if self.myprop.transparent:
                ax.plot(s, z, color=(rgb[0]/255., rgb[1]/255., rgb[2]/255., self.myprop.alpha), linewidth=self.myprop.width)
            else:
                ax.plot(s, z, color=(rgb[0]/255., rgb[1]/255., rgb[2]/255.), linewidth=self.myprop.width)

        return fig, ax

    def plot_linked(self, fig, ax, linked_arrays:dict):
        """
        Graphique Matplolib de valeurs dans les matrices liées
        """
        # from .wolf_array import WolfArray
        # from .wolfresults_2D import Wolfresults_2D

        colors=['red','blue','green']

        exit=True
        for curlabel, curarray in linked_arrays.items():
            if curarray.plotted:
                exit=False

        if exit:
            logging.warning(_('No plotted linked arrays'))
            return

        k=0

        myls = self.asshapely_ls()
        length = myls.length
        tol=length/10.
        ax.set_xlim(0-tol,length+tol)

        zmin=99999.
        zmax=-99999.
        nullvalue = -99999

        for curlabel, curarray in linked_arrays.items():
            if curarray.plotted:

                ds = curarray.get_dxdy_min()

                nb = int(np.ceil(length/ds*2))

                alls = np.linspace(0,int(length),nb)

                pts = [myls.interpolate(curs) for curs in alls]

                allz = np.asarray([curarray.get_value(curpt.x,curpt.y, nullvalue= nullvalue) for curpt in pts])

                zmaxloc=np.max(allz[allz!=nullvalue])
                zminloc=np.min(allz[allz!=nullvalue])

                zmax=max(zmax,zmaxloc)
                zmin=min(zmin,zminloc)

                if np.max(allz)>nullvalue:
                    # select parts
                    if nullvalue in allz:
                        # find all parts separated by nullvalue
                        nulls = np.argwhere(allz==nullvalue)
                        nulls = np.insert(nulls,0,-1)
                        nulls = np.append(nulls,len(allz))

                        addlabel = True
                        for i in range(len(nulls)-1):
                            if nulls[i+1]-nulls[i]>1:
                                ax.plot(alls[nulls[i]+1:nulls[i+1]],allz[nulls[i]+1:nulls[i+1]],
                                        color=colors[np.mod(k,3)],
                                        lw=2.0,
                                        label=curlabel if addlabel else None)
                                addlabel = False

                    else:
                        ax.plot(alls,allz,
                                color=colors[np.mod(k,3)],
                                lw=2.0,
                                label=curlabel)
                k+=1

        ax.set_ylim(zmin,zmax)
        ax.legend()
        ax.grid()
        fig.canvas.draw()

        return fig,ax

    def plot_linked_wx(self, fig:MplFig, linked_arrays:dict):
        """
        Graphique Matplolib de valeurs dans les matrices liées.

        Version pour wxPython
        """

        colors=['red','blue','green']

        exit=True
        for curlabel, curarray in linked_arrays.items():
            if curarray.plotted:
                exit=False

        if exit:
            return

        k=0

        myls = self.asshapely_ls()
        length = myls.length
        tol=length/10.
        fig.cur_ax.set_xlim(0-tol,length+tol)

        zmin=99999.
        zmax=-99999.
        nullvalue = -99999

        for curlabel, curarray in linked_arrays.items():
            if curarray.plotted:

                ds = curarray.get_dxdy_min()

                nb = int(np.ceil(length/ds*2))

                alls = np.linspace(0,int(length),nb)

                pts = [myls.interpolate(curs) for curs in alls]

                allz = np.asarray([curarray.get_value(curpt.x,curpt.y, nullvalue= nullvalue) for curpt in pts])

                zmaxloc=np.max(allz[allz!=nullvalue])
                zminloc=np.min(allz[allz!=nullvalue])

                zmax=max(zmax,zmaxloc)
                zmin=min(zmin,zminloc)

                if np.max(allz)>nullvalue:
                    # select parts
                    if nullvalue in allz:
                        # find all parts separated by nullvalue
                        nulls = np.argwhere(allz==nullvalue)
                        nulls = np.insert(nulls,0,-1)
                        nulls = np.append(nulls,len(allz))

                        addlabel = True
                        for i in range(len(nulls)-1):
                            if nulls[i+1]-nulls[i]>1:
                                fig.plot(alls[nulls[i]+1:nulls[i+1]],allz[nulls[i]+1:nulls[i+1]],
                                        color=colors[np.mod(k,3)],
                                        lw=2.0,
                                        label=curlabel if addlabel else None)
                                addlabel = False

                    else:
                        fig.plot(alls,allz,
                                color=colors[np.mod(k,3)],
                                lw=2.0,
                                label=curlabel)
                k+=1

        fig.cur_ax.set_ylim(zmin,zmax)
        fig.cur_ax.legend()
        fig.cur_ax.grid()

        return fig

    def plot_mpl(self, show=False,
                 forceaspect=True,
                 fig:Figure=None,
                 ax:Axes=None,
                 labels:dict={},
                 clear_ax:bool =True):
        """
        Graphique Matplolib du vecteur - SZ coordinates ONLY

        DEPRECATED: Use plot_matplotlib_sz instead.
        """
        warnings.warn("plot_mpl is deprecated, use plot_matplotlib_sz instead", DeprecationWarning, stacklevel=2)

        x,y=self.get_sz()

        xmin=x[0]
        xmax=x[-1]
        ymin=np.min(y)
        ymax=np.max(y)

        if ax is None:
            redraw=False
            fig = plt.figure()
            ax=fig.add_subplot(111)
        else:
            redraw=True
            if clear_ax:
                # Clear the axes if specified
                ax.cla()

        if 'title' in labels.keys():
            ax.set_title(labels['title'])
        if 'xlabel' in labels.keys():
            ax.set_xlabel(labels['xlabel'])
        if 'ylabel' in labels.keys():
            ax.set_ylabel(labels['ylabel'])

        if ymax>-99999.:

            dy=ymax-ymin
            ymin-=dy/4.
            ymax+=dy/4.

            ax.plot(x,y,color='black',
                    lw=2.0,
                    label=self.myname)

            ax.legend()

            tol=(xmax-xmin)/10.
            ax.set_xlim(xmin-tol,xmax+tol)
            ax.set_ylim(ymin,ymax)

            if forceaspect:
                aspect=1.0*(ymax-ymin)/(xmax-xmin)*(ax.get_xlim()[1] - ax.get_xlim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[0])
                ax.set_aspect(aspect)

        if show:
            fig.show()

        if redraw:
            fig.canvas.draw()

        return fig,ax

    def _get_textfont(self):
        """ Retunr a 'Text_Infos' instance for the legend """

        r,g,b = getRGBfromI(self.myprop.legendcolor)
        tinfos =  Text_Infos(self.myprop.legendpriority,
                             (np.cos(self.myprop.legendorientation/180*np.pi),
                              np.sin(self.myprop.legendorientation/180*np.pi)),
                             self.myprop.legendfontname,
                             self.myprop.legendfontsize,
                             colour=(r,g,b,255),
                             dimsreal=(self.myprop.legendlength,
                                       self.myprop.legendheight),
                             relative_position=self.myprop.legendrelpos)

        return tinfos

    def _get_textfont_idx(self):
        """ Retunr a 'Text_Infos' instance for the legend """

        r,g,b = getRGBfromI(self.myprop.color)
        tinfos =  Text_Infos(3,
                             (1., 0.),
                             self.myprop.legendfontname,
                             12,
                             colour=(r,g,b,255),
                             dimsreal=(self.myprop.legendlength,
                                       self.myprop.legendheight),
                             relative_position=7)

        return tinfos

    def add2tree(self, tree:TreeListCtrl, root):
        """
        Ajout de l'objte à un TreeListCtrl wx
        """
        self.mytree=tree
        self.myitem=tree.AppendItem(root, self.myname,data=self)
        if self.myprop.used:
            tree.CheckItem(self.myitem)

    def unuse(self):
        """
        L'objet n'est plus à utiliser
        """
        self.myprop.used=False
        if self.mytree is not None:
            self.mytree.UncheckItem(self.myitem)

        self._reset_listogl()

    def use(self):
        """
        L'objet n'est plus à utiliser
        """
        self.myprop.used=True
        if self.mytree is not None:
            self.mytree.CheckItem(self.myitem)


        self._reset_listogl()

    def fillgrid(self, gridto:CpGrid):
        """
        Remplissage d'un CpGrid
        """
        curv:wolfvertex

        gridto.SetColLabelValue(0,'X')
        gridto.SetColLabelValue(1,'Y')
        gridto.SetColLabelValue(2,'Z')
        gridto.SetColLabelValue(3,'value')
        gridto.SetColLabelValue(4,'s curvi')
        gridto.SetColLabelValue(5,'in use')

        nb=gridto.GetNumberRows()
        if len(self.myvertices)-nb>0:
            gridto.AppendRows(len(self.myvertices)-nb)
        k=0
        for curv in self.myvertices:
           gridto.SetCellValue(k,0,str(curv.x))
           gridto.SetCellValue(k,1,str(curv.y))
           gridto.SetCellValue(k,2,str(curv.z))
           gridto.SetCellValue(k,5,'1' if curv.in_use else '0')
           k+=1

    def _fillgrid_only_i(self, gridto:CpGrid):
        """
        Remplissage d'un CpGrid
        """
        curv:wolfvertex

        gridto.SetColLabelValue(0,'X')
        gridto.SetColLabelValue(1,'Y')
        gridto.SetColLabelValue(2,'Z')
        gridto.SetColLabelValue(3,'value')
        gridto.SetColLabelValue(4,'s curvi')
        gridto.SetColLabelValue(5,'in use')

        nb=gridto.GetNumberRows()
        if len(self.myvertices)-nb>0:
            gridto.AppendRows(len(self.myvertices)-nb)
        k=0

        for curv in self.myvertices:
           gridto.SetCellValue(k, 5, '1' if curv.in_use else '0')
           k+=1

    def updatefromgrid(self,gridfrom:CpGrid):
        """
        Mise à jour depuis un CpGrid
        """
        curv:wolfvertex

        nbl=gridfrom.GetNumberRows()
        k=0
        while k<nbl:
            x=gridfrom.GetCellValue(k,0)
            y=gridfrom.GetCellValue(k,1)
            z=gridfrom.GetCellValue(k,2)
            inuse = gridfrom.GetCellValue(k,5)
            if z=='':
                z=0.
            if x!='':
                if k<self.nbvertices:
                    self.myvertices[k].x=float(x)
                    self.myvertices[k].y=float(y)
                    self.myvertices[k].z=float(z)
                    self.myvertices[k].in_use = inuse=='1'
                else:
                    newvert=wolfvertex(float(x),float(y),float(z))
                    self.add_vertex(newvert)
                k+=1
            else:
                break

        while k<self.nbvertices:
            self.myvertices.pop(k)

        if self._linestring is not None or self._polygon is not None:
            self.prepare_shapely()

        self._reset_listogl()

    def get_s2d(self) -> np.ndarray:
        """
        Calcule et retourne des positions curvilignes 2D
        """

        s2d = np.zeros(self.nbvertices)
        for k in range(1, self.nbvertices):
            s2d[k] = s2d[k-1] + self.myvertices[k-1].dist2D(self.myvertices[k])

        return s2d

    def get_s3d(self) -> np.ndarray:
        """
        Calcule et retourne des positions curvilignes 3D
        """

        s3d=np.zeros(self.nbvertices)
        for k in range(1,self.nbvertices):
            s3d[k] = s3d[k-1] + self.myvertices[k-1].dist3D(self.myvertices[k])

        return s3d

    def get_sz(self, cumul=True):
        """
        Calcule et retourne la distance horizontale cumulée ou non.
        de chaque point vis-à-vis du premier point

        Utile pour le tracé de sections en travers ou des vérifications de position

        :param cumul: si True, retourne la distance cumulée 2D le long du vecteur. si False, retourne la distance 2D entre chaque point et le premier.
        """
        z = np.asarray([vert.z for vert in self.myvertices])

        nb = len(z)
        s = np.zeros(nb)

        if cumul:
            x1 = self.myvertices[0].x
            y1 = self.myvertices[0].y
            for i in range(nb-1):
                x2 = self.myvertices[i+1].x
                y2 = self.myvertices[i+1].y

                length = np.sqrt((x2-x1)**2.+(y2-y1)**2.)
                s[i+1] = s[i]+length

                x1=x2
                y1=y2
        else:
            for i in range(nb):
                s[i] = self.myvertices[0].dist2D(self.myvertices[i])

        if self.add_sdatum:
            s += self.sdatum
        if self.add_zdatum:
            z += self.zdatum

        return s,z

    def update_lengths(self):
        """
        Mise à jour de la longueur
         - en 2D
         - en 3D

        Retient également les longueurs de chaque segment
        """
        if self.nbvertices < 2:
            logging.warning(_('No enough vertices in vector to compute lenghts'))
            return

        self._lengthparts2D=np.zeros(self.nbvertices-1)
        self._lengthparts3D=np.zeros(self.nbvertices-1)

        for k in range(self.nbvertices-1):
            self._lengthparts2D[k] = self.myvertices[k].dist2D(self.myvertices[k+1])
            self._lengthparts3D[k] = self.myvertices[k].dist3D(self.myvertices[k+1])

        if self.closed and self.myvertices[0]!=self.myvertices[-1]:
            self._lengthparts2D[-1] = self.myvertices[-2].dist2D(self.myvertices[-1])
            self._lengthparts3D[-1] = self.myvertices[-2].dist3D(self.myvertices[-1])

        self.length2D = np.sum(self._lengthparts2D)
        self.length3D = np.sum(self._lengthparts3D)

    def get_segment(self, s, is3D, adim=True,frombegin=True):
        """
        Retrouve le segment associé aux paramètres passés
        """

        if self.length2D is None or self.length3D is None:
            self.update_lengths()
        else:
            if len(self._lengthparts2D) != self.nbvertices-1 or len(self._lengthparts3D) != self.nbvertices-1:
                self.update_lengths()

        if is3D:
            length = self.length3D
            lengthparts = self._lengthparts3D
        else:
            length = self.length2D
            lengthparts = self._lengthparts2D

        cums = np.cumsum(lengthparts)

        if adim:
            if length == 0.:
                logging.warning(_('Length of vector {} is zero, cannot compute segments').format(self.myname))

            cums = cums.copy()/length
            cums[-1]=1.
            lengthparts = lengthparts.copy()/length
            if s>1.:
                s=1.
            if s<0.:
                s=0.
        else:
            if s>length:
                s=length
            if s<0.:
                s=0.

        if frombegin:
            k=0
            while s>cums[k] and k < self.nbvertices-2:
                k+=1
        else:
            k=self.nbvertices-2
            if k>0:
                while s<cums[k] and k>0:
                    k-=1
                if (k==0 and s<cums[0]) or s==cums[self.nbvertices-2]:
                    pass
                else:
                    k+=1

        if k==len(cums):
            k-=1

        return k,cums[k],lengthparts

    def _refine2D(self, ds):
        """
        Raffine un vecteur selon un pas 'ds'

        Return :
         Liste Python avec des Point Shapely
        """

        myls = self.asshapely_ls()
        length = myls.length

        nb = int(np.ceil(length/ds))+1

        if length<1:
            length*=1000.
            alls = np.linspace(0, length, nb)
            alls/=1000.
        else:
            alls = np.linspace(0, length, nb, endpoint=True)

        pts = [myls.interpolate(curs) for curs in alls]
        # pts = [(curpt.x, curpt.y) for curpt in pts]

        return pts

    def split(self, ds, new=True):
        """
        Création d'un nouveau vecteur sur base du découpage d'un autre et d'un pas spatial à respecter
        Le nouveau vecteur contient tous les points de l'ancien et des nouveaux sur base d'un découpage 3D

        :param ds: pas spatial
        :param new: si True, le vecteur est ajouté à la zone parente
        """
        newvec = vector(name=self.myname+'_split',parentzone=self.parentzone)

        self.update_lengths()

        locds = ds/self.length3D

        dist3d = np.concatenate([np.arange(0.,1.,locds),np.cumsum(self._lengthparts3D)/self.length3D])
        dist3d = np.unique(dist3d)

        for curs in dist3d:
            newvec.add_vertex(self.interpolate(curs,is3D=True,adim=True))

        if new:
            curzone:zone
            curzone=self.parentzone
            if curzone is not None:
                curzone.add_vector(newvec)
                curzone._fill_structure()
        else:
            self.myvertices = newvec.myvertices
            self.update_lengths()

    def interpolate(self,s,is3D=True,adim=True,frombegin=True) -> wolfvertex:
        """
        Interpolation linéaire à une abscisse curviligne 's' donnée

        Calcul par défaut :
          - en 3D
          - en adimensionnel
        """

        if self.length2D is None or self.length3D is None:
            self.update_lengths()

        if self.length2D == 0.:
            pond = 0.
            k = 0
        else:
            k,cums,lengthparts=self.get_segment(s,is3D,adim,frombegin)
            pond = (cums-s)/lengthparts[k]

        return wolfvertex(self.myvertices[k].x*pond+self.myvertices[k+1].x*(1.-pond),
                          self.myvertices[k].y*pond+self.myvertices[k+1].y*(1.-pond),
                          self.myvertices[k].z*pond+self.myvertices[k+1].z*(1.-pond))

    def substring(self,s1,s2,is3D=True,adim=True,eps=1.e-2):
        """
        Récupération d'une fraction de vector entre 's1' et 's2'
        Nom similaire à la même opération dans Shapely mais qui ne gère, elle, que le 2D
        """
        if s1==s2:
            logging.debug(_('Substring with same start and end abscissa: s1={} s2={}').format(s1, s2))
            s2+=eps

        k1,cums1,lengthparts1=self.get_segment(s1,is3D,adim,True)
        k2,cums2,lengthparts2=self.get_segment(s2,is3D,adim,False)

        pond1 = max((cums1-s1)/lengthparts1[k1],0.) if lengthparts1[k1] > 0. else 0.
        pond2 = min((cums2-s2)/lengthparts2[k2],1.) if lengthparts2[k2] > 0. else 1.

        v1= wolfvertex(self.myvertices[k1].x*pond1+self.myvertices[k1+1].x*(1.-pond1),
                       self.myvertices[k1].y*pond1+self.myvertices[k1+1].y*(1.-pond1),
                       self.myvertices[k1].z*pond1+self.myvertices[k1+1].z*(1.-pond1))

        v2= wolfvertex(self.myvertices[k2].x*pond2+self.myvertices[k2+1].x*(1.-pond2),
                       self.myvertices[k2].y*pond2+self.myvertices[k2+1].y*(1.-pond2),
                       self.myvertices[k2].z*pond2+self.myvertices[k2+1].z*(1.-pond2))

        newvec = vector(name='substr')

        newvec.add_vertex(v1)

        if s1<=s2:
            if is3D:
                for k in range(k1+1,k2+1):
                    if self.myvertices[k].dist3D(newvec.myvertices[-1])!=0.:
                        newvec.add_vertex(self.myvertices[k])
            else:
                for k in range(k1+1,k2+1):
                    if self.myvertices[k].dist2D(newvec.myvertices[-1])!=0.:
                        newvec.add_vertex(self.myvertices[k])
        else:
            if is3D:
                for k in range(k1+1,k2+1,-1):
                    if self.myvertices[k].dist3D(newvec.myvertices[-1])!=0.:
                        newvec.add_vertex(self.myvertices[k])
            else:
                for k in range(k1+1,k2+1,-1):
                    if self.myvertices[k].dist2D(newvec.myvertices[-1])!=0.:
                        newvec.add_vertex(self.myvertices[k])

        if [v2.x,v2.y,v2.z] != [newvec.myvertices[-1].x,newvec.myvertices[-1].y,newvec.myvertices[-1].z]:
            newvec.add_vertex(v2)

        # if newvec.nbvertices==0:
        #     a=1
        # if newvec.nbvertices==1:
        #     a=1
        # newvec.update_lengths()
        # if np.min(newvec._lengthparts2D)==0.:
        #     a=1
        return newvec

    def get_values_linked_polygon(self, linked_arrays:list, getxy=False) -> dict:
        """
        Retourne les valeurs contenue dans le polygone

        linked_arrays : liste Python d'objet matriciels WolfArray (ou surcharge)
        """
        vals={}

        for curarray in linked_arrays:
            if curarray.plotted:
                vals[curarray.idx] = curarray.get_values_insidepoly(self, getxy=getxy)
            else:
                vals[curarray.idx] = None

        return vals

    def get_all_values_linked_polygon(self, linked_arrays, getxy=False) -> dict:
        """
        Retourne toutes les valeurs contenue dans le polygone --> utile au moins pour les résultats WOLF2D

        linked_arrays : liste Python d'objet matriciels WolfArray (ou surcharge)
        """
        vals={}

        for curarray in linked_arrays:
            if curarray.plotted:
                vals[curarray.idx] = curarray.get_all_values_insidepoly(self, getxy=getxy)
            else:
                vals[curarray.idx] = None

        return vals

    def get_all_values_linked_polyline(self,linked_arrays, getxy=True) -> dict:
        """
        Retourne toutes les valeurs sous la polyligne --> utile au moins pour les résultats WOLF2D

        linked_arrays : liste Python d'objet matriciels WolfArray (ou surcharge)
        """
        vals={}

        for curarray in linked_arrays:
            if curarray.plotted:
                vals[curarray.idx], xy = curarray.get_all_values_underpoly(self, getxy=getxy)
            else:
                vals[curarray.idx] = None

        return vals

    def get_values_on_vertices(self,curarray):
        """
        Récupération des valeurs sous les vertices et stockage dans la coordonnée 'z'
        """
        if not curarray.plotted:
            return

        for curpt in self.myvertices:
            curpt.z = curarray.get_value(curpt.x,curpt.y)

    def get_values_linked(self, linked_arrays:dict, refine=True, filter_null = False):
        """
        Récupération des valeurs dans les matrices liées sous les vertices et stockage dans la coordonnée 'z'
        Possibilité de raffiner la discrétisation pour obtenir au moins une valeur par maille
        """

        exit=True
        for curlabel, curarray in linked_arrays.items():
            if curarray.plotted:
                # at least one plotted array
                exit=False

        if exit:
            return

        if refine:
            myzone=zone(name='linked_arrays - fine step')

            for curlabel, curarray in linked_arrays.items():
                if curarray.plotted:

                    myvec=vector(name=curlabel,parentzone=myzone)
                    myzone.add_vector(myvec)

                    ds = curarray.get_dxdy_min()

                    pts = self._refine2D(ds)

                    allz = [curarray.get_value(curpt.x, curpt.y, nullvalue=-99999) for curpt in pts]

                    if filter_null:
                        for curpt,curz in zip(pts,allz):
                            if curz!=-99999:
                                myvec.add_vertex(wolfvertex(curpt.x,curpt.y,curz))
                    else:
                        for curpt,curz in zip(pts,allz):
                            myvec.add_vertex(wolfvertex(curpt.x,curpt.y,curz))

        else:
            myzone=zone(name='linked_arrays')
            for curlabel, curarray in linked_arrays.items():
                if curarray.plotted:

                    myvec=vector(name=curlabel,parentzone=myzone)
                    myzone.add_vector(myvec)

                    if filter_null:
                        for curpt in self.myvertices:
                            locval = curarray.get_value(curpt.x, curpt.y, nullvalue=-99999)
                            if locval !=-99999:
                                myvec.add_vertex(wolfvertex(curpt.x, curpt.y, locval))
                    else:
                        for curpt in self.myvertices:
                            locval = curarray.get_value(curpt.x, curpt.y, nullvalue=-99999)
                            myvec.add_vertex(wolfvertex(curpt.x, curpt.y, locval))

        return myzone

    def deepcopy_vector(self, name: str = None, parentzone = None) -> 'vector':
        """
        Return a deep copy of the vector.
        """

        if name is None:
            name = self.myname + "_copy"

        if parentzone is not None:
            copied_vector = vector(name=name,parentzone=parentzone)
        else:
            copied_vector = vector(name=name)

        copied_vector.myvertices = copy.deepcopy(self.myvertices)
        # FIXME : deepcopy of properties is not working
        # copied_vector.myprop = copy.deepcopy(self.myprop)

        copied_vector.closed = self.closed

        copied_vector.zdatum = self.zdatum
        copied_vector.add_zdatum = self.add_zdatum

        copied_vector.sdatum = self.sdatum
        copied_vector.add_sdatum = self.add_sdatum

        return copied_vector

    def deepcopy(self, name: str = None, parentzone = None) -> 'vector':
        """
        Return a deep copy of the vector.
        """

        return self.deepcopy_vector(name, parentzone)

    @property
    def centroid(self):
        """
        Return the centroid of the vector
        """

        return self.polygon.centroid

    def set_legend_to_centroid(self, text:str='', visible:bool=True):
        """
        Positionne la légende au centre du vecteur
        """
        self.myprop.legendvisible = visible

        centroid = self.centroid

        self.myprop.legendx = centroid.x
        self.myprop.legendy = centroid.y
        self.myprop.legendtext = text if text else self.myname

    def set_legend_visible(self, visible:bool=True):
        """
        Set the visibility of the legend.
        """
        self.myprop.legendvisible = visible

    def set_legend_position_to_centroid(self):
        """
        Positionne la légende au centre du vecteur
        """

        centroid = self.centroid
        self.myprop.legendx = centroid.x
        self.myprop.legendy = centroid.y

    def set_z(self, new_z:np.ndarray):
        """ Set the z values of the vertices """
        warnings.warn(_('This method is deprecated, use the z property instead.'), DeprecationWarning, stacklevel=2)

        self.z = new_z

    @property
    def z(self):
        """ Return the z values of the vertices as a numpy array. """
        z = np.asarray([curvert.z for curvert in self.myvertices])
        if self.add_zdatum:
            z+=self.zdatum
        return z

    @property
    def x(self):
        """ Return the x values of the vertices as a numpy array. """
        return np.asarray([curvert.x for curvert in self.myvertices])

    @property
    def y(self):
        """ Return the y values of the vertices as a numpy array. """
        return np.asarray([curvert.y for curvert in self.myvertices])

    @property
    def xy(self):
        """ Return the x, y values of the vertices as a 2D numpy array. """
        return np.asarray([[curvert.x, curvert.y] for curvert in self.myvertices])

    @property
    def xz(self):
        """ Return the x, z values of the vertices as a 2D numpy array. """
        return np.asarray([[curvert.x, curvert.z] for curvert in self.myvertices])

    @property
    def xyz(self):
        """ Return the x, y, z values of the vertices as a 3D numpy array. """
        return self.asnparray3d()

    @property
    def i(self):
        """ Return the in_use values of the vertices. """
        return np.asarray([curvert.in_use for curvert in self.myvertices])

    @property
    def xyzi(self):
        """ Return the x, y, z and in_use values of the vertices. """
        x = self.x
        y = self.y
        z = self.z
        i = self.i
        return np.column_stack((x,y,z,i))

    @property
    def xyi(self):
        """ Return the x, y and in_use values of the vertices. """
        return np.asarray([[curvert.x, curvert.y, curvert.in_use] for curvert in self.myvertices])

    @property
    def sz_curvi(self):
        """ Return the curvilinear abscissa and thz Z-value of the vector. """
        return self.get_sz()

    @property
    def s_curvi(self):
        """ Return the curvilinear abscissa of the vector. """
        sz = self.get_sz()
        return sz[0]

    @x.setter
    def x(self, new_x:np.ndarray | list):
        """ Set the x values of the vertices.

        :param new_x: numpy array or list with x values - must have the same length as the number of vertices
        :type new_x: np.ndarray | list
        """

        if isinstance(new_x, list):
            new_x = np.array(new_x)

        if len(new_x) != self.nbvertices:
            logging.warning(_('New x values have not the same length as the number of vertices'))
            return

        for curvert, newx in zip(self.myvertices, new_x):
            curvert.x = newx

        self._reset_listogl()
        self.reset_linestring()

    @y.setter
    def y(self, new_y:np.ndarray | list):
        """ Set the y values of the vertices.

        :param new_y: numpy array or list with y values - must have the same length as the number of vertices
        :type new_y: np.ndarray | list
        """

        if isinstance(new_y, list):
            new_y = np.array(new_y)

        if len(new_y) != self.nbvertices:
            logging.warning(_('New y values have not the same length as the number of vertices'))
            return

        for curvert, newy in zip(self.myvertices, new_y):
            curvert.y = newy

        self._reset_listogl()
        self.reset_linestring()

    @z.setter
    def z(self, new_z:np.ndarray | float | list):
        """ Set the z values of the vertices

        :param new_z: numpy array, float or list (but WolfArray is supported too)
        :type new_z: np.ndarray | float | list | WolfArray
        """
        from .wolf_array import WolfArray

        if isinstance(new_z, (int, float)):
            new_z = np.full(self.nbvertices, new_z, dtype=float)
        elif isinstance(new_z, WolfArray):
            wa = new_z

            new_z = []
            for curvert in self.myvertices:
                i,j = wa.xy2ij(curvert.x, curvert.y)
                if i>0 and j>0 and i < wa.nbx and j < wa.nby:
                    new_z.append(wa.array[i, j])

        if isinstance(new_z, list):
            new_z = np.array(new_z)

        if len(new_z) != self.nbvertices:
            logging.warning(_('New z values have not the same length as the number of vertices'))
            return

        if self.add_zdatum:
            for curvert, newz in zip(self.myvertices, new_z):
                curvert.z = newz - self.zdatum
        else:
            for curvert, newz in zip(self.myvertices, new_z):
                curvert.z = newz

        self._reset_listogl()
        self.reset_linestring()

    @xyz.setter
    def xyz(self, new_xyz:np.ndarray | list):
        """ Set the x, y, z values of the vertices.

        :param new_xyz: numpy array or list with x, y, z values - must have the same length as the number of vertices
        :type new_xyz: np.ndarray | list
        """

        if isinstance(new_xyz, list):
            new_xyz = np.array(new_xyz)

        if len(new_xyz) != self.nbvertices:
            logging.warning(_('New xyz values have not the same length as the number of vertices'))
            return

        if self.add_zdatum:
            for curvert, newxyz in zip(self.myvertices, new_xyz):
                curvert.x = newxyz[0]
                curvert.y = newxyz[1]
                curvert.z = newxyz[2] - self.zdatum
        else:
            for curvert, newxyz in zip(self.myvertices, new_xyz):
                curvert.x = newxyz[0]
                curvert.y = newxyz[1]
                curvert.z = newxyz[2]

        self._reset_listogl()
        self.reset_linestring()


    @xy.setter
    def xy(self, new_xy:np.ndarray | list):
        """ Set the x, y values of the vertices.

        :param new_xy: numpy array or list with x, y values - must have the same length as the number of vertices
        :type new_xy: np.ndarray | list
        """

        if isinstance(new_xy, list):
            new_xy = np.array(new_xy)

        if len(new_xy) != self.nbvertices:
            logging.warning(_('New xy values have not the same length as the number of vertices'))
            return

        for curvert, newxy in zip(self.myvertices, new_xy):
            curvert.x = newxy[0]
            curvert.y = newxy[1]

        self._reset_listogl()
        self.reset_linestring()

    @xz.setter
    def xz(self, new_xz:np.ndarray | list):
        """ Set the x, z values of the vertices.

        :param new_xz: numpy array or list with x, z values - must have the same length as the number of vertices
        :type new_xz: np.ndarray | list
        """

        if isinstance(new_xz, list):
            new_xz = np.array(new_xz)

        if len(new_xz) != self.nbvertices:
            logging.warning(_('New xz values have not the same length as the number of vertices'))
            return

        if self.add_zdatum:
            for curvert, newxz in zip(self.myvertices, new_xz):
                curvert.x = newxz[0]
                curvert.z = newxz[1] - self.zdatum
        else:
            for curvert, newxz in zip(self.myvertices, new_xz):
                curvert.x = newxz[0]
                curvert.z = newxz[1]

        self._reset_listogl()
        self.reset_linestring()

    @xyzi.setter
    def xyzi(self, new_xyzi:np.ndarray | list):
        """ Set the x, y, z, in_use values of the vertices.

        :param new_xyzi: numpy array or list with x, y, z, in_use values - must have the same length as the number of vertices
        :type new_xyzi: np.ndarray | list
        """

        if isinstance(new_xyzi, list):
            new_xyzi = np.array(new_xyzi)

        if len(new_xyzi) != self.nbvertices:
            logging.warning(_('New xyzi values have not the same length as the number of vertices'))
            return

        for curvert, newxyzi in zip(self.myvertices, new_xyzi):
            curvert.x = newxyzi[0]
            curvert.y = newxyzi[1]
            curvert.z = newxyzi[2] - self.zdatum if self.add_zdatum else newxyzi[2]
            curvert.in_use = newxyzi[3]

        self._reset_listogl()
        self.reset_linestring()

    @xyi.setter
    def xyi(self, new_xyi:np.ndarray | list):
        """ Set the x, y, in_use values of the vertices.

        :param new_xyi: numpy array or list with x, y, in_use values - must have the same length as the number of vertices
        :type new_xyi: np.ndarray | list
        """

        if isinstance(new_xyi, list):
            new_xyi = np.array(new_xyi)

        if len(new_xyi) != self.nbvertices:
            logging.warning(_('New xyi values have not the same length as the number of vertices'))
            return

        for curvert, newxyi in zip(self.myvertices, new_xyi):
            curvert.x = newxyi[0]
            curvert.y = newxyi[1]
            curvert.in_use = newxyi[2]

        self._reset_listogl()
        self.reset_linestring()

    @i.setter
    def i(self, new_i:np.ndarray | list):
        """ Set the in_use values of the vertices.

        :param new_i: numpy array or list with in_use values - must have the same length as the number of vertices
        :type new_i: np.ndarray | list
        """

        if isinstance(new_i, list):
            new_i = np.array(new_i)

        if len(new_i) != self.nbvertices:
            logging.warning(_('New i values have not the same length as the number of vertices'))
            return

        for curvert, newi in zip(self.myvertices, new_i):
            curvert.in_use = newi

        self._reset_listogl()
        self.reset_linestring()

    @sz_curvi.setter
    def sz_curvi(self, sz_new:np.ndarray | list):
        """ Interpolate the vertice Z-coordinates based on a polyline defined as curvilinear abscissa and Z-value.

        :param sz_new: numpy array or list with curvilinear abscissa and Z-value pairs
        :type sz_new: np.ndarray | list
        """

        if isinstance(sz_new, list):
            sz_new = np.array(sz_new)

        f = interp1d(sz_new[:,0],sz_new[:,1], bounds_error=False, fill_value='extrapolate')

        s = self.s_curvi
        for idx, curvert in enumerate(self.myvertices):
            curvert.z = f(s[idx])

        self._reset_listogl()
        self.reset_linestring()

    @s_curvi.setter
    def s_curvi(self, new_s:np.ndarray | list):
        """ Replace the vertice XY-coordinates based on the curvilinear abscissa.

        :param new_s: numpy array or list with curvilinear abscissa values - must have the same length as the number of vertices
        :type new_s: np.ndarray | list
        """

        if isinstance(new_s, list):
            new_s = np.array(new_s)

        if len(new_s) != self.nbvertices:
            logging.warning(_('New s values have not the same length as the number of vertices'))
            return

        poly = self.linestring

        for idx, curvert in enumerate(self.myvertices):
            curvert.x, curvert.y = poly.interpolate(new_s[idx]).xy

        self._reset_listogl()
        self.reset_linestring()


    def __str__(self):
        return self.myname

    def __len__(self):
        return self.nbvertices

    def __iter__(self) -> wolfvertex:
        return iter(self.myvertices)

    def __getitem__(self, ndx:int) -> wolfvertex:
        """ Permet de retrouver un vertex sur base de son index """
        if ndx>=0 and ndx < self.nbvertices:
            return self.myvertices[ndx]
        elif ndx < 0 and abs(ndx) <= self.nbvertices:
            return self.myvertices[ndx + self.nbvertices]
        else:
            logging.warning(_('Index out of range'))

    def __setitem__(self, ndx:int, value:wolfvertex):
        """ Permet de modifier un vertex sur base de son index """
        if ndx>=0 and ndx < self.nbvertices:
            self.myvertices[ndx] = value
            self._reset_listogl()
            self.reset_linestring()
        elif ndx < 0 and abs(ndx) <= self.nbvertices:
            self.myvertices[ndx + self.nbvertices] = value
            self._reset_listogl()
            self.reset_linestring()
        else:
            logging.warning(_('Index out of range'))

    def __delitem__(self, ndx:int):
        """ Permet de supprimer un vertex sur base de son index.

        Exemple:
        del myvector[0]  # Supprime le premier vertex
        """
        if ndx>=0 and ndx < self.nbvertices:
            self.myvertices.pop(ndx)
            self._reset_listogl()
            self.reset_linestring()
        elif ndx < 0 and abs(ndx) <= self.nbvertices:
            self.myvertices.pop(ndx + self.nbvertices)
            self._reset_listogl()
            self.reset_linestring()
        else:
            logging.warning(_('Index out of range'))

    def append(self, other:"vector", merge_type:Literal['link', 'copy']='link'):
        """
        Append a vector to the current one
        """

        if merge_type == 'link':
            self.myvertices.extend(other.myvertices)
        elif merge_type == 'copy':
            self.myvertices.extend(other.myvertices.copy())
        else:
            logging.warning(_('Merge type not supported'))

        self.update_lengths()
        self._reset_listogl()
        self.reset_linestring()

    def cut(self, s:float, is3D:bool=True, adim:bool=True, frombegin:bool=True):
        """
        cut a vector at a given curvilinear abscissa
        """

        newvec = vector(name=self.myname+'_cut', parentzone=self.parentzone)
        self.parentzone.add_vector(newvec, update_struct=True)

        k,cums,lengthparts=self.get_segment(s,is3D,adim,frombegin)

        if frombegin:
            newvec.myvertices = self.myvertices[:k+1]
            self.myvertices = self.myvertices[k:]
        else:
            newvec.myvertices = self.myvertices[k:]
            self.myvertices = self.myvertices[:k+1]

        self.update_lengths()
        newvec.update_lengths()

        self._reset_listogl()
        self.reset_linestring()

        return newvec

    def _reset_listogl(self):
        """
        Reset the list of OpenGL display
        """
        if self.parentzone is not None:
            self.parentzone.reset_listogl()

    def select_points_inside(self, xy:cloud_vertices | np.ndarray):
        """ Select the points inside a polygon

        :param xy: cloud_vertices or np.ndarray with x,y coordinates
        :return: list of boolean
        """

        self.prepare_shapely(True)

        if isinstance(xy, cloud_vertices):
            xy = xy.get_xyz()[:,0:2]

        inside = [self.polygon.contains(Point(curxy)) for curxy in xy]

        return inside

    def get_first_point_inside(self, xy: cloud_vertices | np.ndarray):
        """
        Returns the first point (x, y) inside the polygon.

        :param xy: Point cloud (cloud_vertices or np.ndarray)
        :type xy: cloud_vertices | np.ndarray
        :return: Coordinates (x, y) of the first point found inside, or None if none
        :rtype: tuple[float, float] | None
        """
        self.prepare_shapely(True)

        if isinstance(xy, cloud_vertices):
            xy = xy.get_xyz()[:, 0:2]

        for curxy in xy:
            if self.polygon.contains(Point(curxy)):
                return float(curxy[0]), float(curxy[1])
        return None

    def split_cloud(self, cloud_to_split:cloud_vertices):
        """ Split a cloud of vertices on the vector """

        inside = self.select_points_inside(cloud_to_split)

        cloud_inside = cloud_vertices(idx = 'inside_'+cloud_to_split.idx)
        cloud_outside = cloud_vertices(idx = 'outside_'+cloud_to_split.idx)

        vertices = cloud_to_split.get_vertices()

        for idx, (locinside, curvert) in enumerate(zip(inside, vertices)):
            if locinside:
                cloud_inside.add_vertex(curvert)
            else:
                cloud_outside.add_vertex(curvert)

        return cloud_inside, cloud_outside


    def check_if_closed(self) -> bool:
        """
        Check if the vector is closed
        """

        return not self.check_if_open()


    def check_if_open(self) -> bool:
        """ Check if the vector is open """

        is_open = not((self.myvertices[-1] is self.myvertices[0]) or \
            (self.myvertices[-1].x==self.myvertices[0].x and \
             self.myvertices[-1].y==self.myvertices[0].y))

        if not self.is2D :
            is_open = is_open or self.myvertices[-1].z!=self.myvertices[0].z

        self.closed = not is_open

        return is_open

    @property
    def surface(self):
        """
        Compute the surface of the vector
        """

        if self.closed:
            return self.polygon.area
        else:
            return 0.

    @property
    def area(self):
        """ Alias for surface """
        return self.surface

    def interpolate_coordinates(self):
        """
        Interpole les valeurs Z des vertices sur base des seules valeurs connues,
        càd autre que infinity ou -99999 ou 99999.
        """

        sz = self.get_sz()
        s = sz[0]
        z = sz[1]

        # Remove -99999 and empty values
        valid_indices = np.where((z != -99999.) & (z != 99999.) & (z != '') & (np.isfinite(z)))[0]
        if len(valid_indices) == 0:
            logging.warning(_('No valid z values to interpolate'))
            return

        f = interp1d(s[valid_indices], z[valid_indices])

        for k in range(self.nbvertices):
            if k not in valid_indices:
                z = f(s[k])
                self.myvertices[k].z = z

        self.update_lengths()
        self._reset_listogl()

    def __del__(self):
        """ Destructor """
        self._reset_listogl()
        self.reset_linestring()


class zone:
    """
    Objet de gestion d'informations vectorielles

    Une instance 'zone' contient une listde de 'vector' (segment, ligne, polyligne, polygone...)
    """

    myname:str
    nbvectors:int
    myvectors:list[vector]

    xmin:float
    ymin:float
    xmax:float
    ymax:float

    selected_vectors:list[tuple[vector,float]]
    mytree:TreeListCtrl
    myitem:TreeItemId

    def __init__(self,
                 lines:list[str]=[],
                 name:str='NoName',
                 parent:"Zones"=None,
                 is2D:bool=True,
                 fromshapely:Union[LineString,Polygon,MultiLineString, MultiPolygon]=None) -> None:

        self.myprop = None
        self.myprops = None

        self.myname = ''        # name of the zone
        self.idgllist = -99999  # id of the zone in the gllist
        self.active_vector=None # current active vector
        self.parent=parent      # parent object - type(Zones)

        self.xmin = -99999.
        self.ymin = -99999.
        self.xmax = -99999.
        self.ymax = -99999.

        self.has_legend = False # indicate if at least one vector in the zone has a legend
        self.has_image  = False # indicate if at least one vector in the zone has an image

        self._move_start = None # starting point for a move
        self._move_step = None  # step for a move
        self._rotation_center = None # center of rotation
        self._rotation_step = None   # step for rotation

        if len(lines)>0:
            # Decoding from lines -- lines is a list of strings provided by the parent during reading
            # The order of the lines is important to ensure compatibility with the WOLF2D format
            self.myname=lines[0]
            tmp_nbvectors=int(lines[1])
            self.myvectors=[]
            curstart=2

            if tmp_nbvectors>1000:
                logging.info(_('Many vectors in zone -- {} -- Be patient !').format(tmp_nbvectors))

            for i in range(tmp_nbvectors):
                curvec=vector(lines[curstart:],parentzone=self,is2D=is2D)
                curstart+=curvec._nblines()
                self.myvectors.append(curvec)
                if tmp_nbvectors>1000:
                    if i%100==0:
                        logging.info(_('{} vectors read').format(i))

        if name!='' and self.myname=='':
            self.myname=name
            self.myvectors=[]

        self.selected_vectors=[]                # list of selected vectors
        self.multils:MultiLineString = None     # MultiLineString shapely
        self.used = True                        # indicate if the zone must used or not --> corresponding to checkbox in the tree

        self.mytree=None                        # TreeListCtrl wx

        if fromshapely is not None:
            # Object can be created from a shapely object
            self.import_shapelyobj(fromshapely)

    def check_if_interior_exists(self):
        """ Check if the zone has at least one vector with interior points """

        list(map(lambda curvec: curvec.check_if_interior_exists(), self.myvectors))

    def add_values(self, key:str, values:np.ndarray):
        """ add values to the zone """

        if self.nbvectors != values.shape[0]:
            logging.warning(_('Number of vectors and values do not match'))
            return

        list(map(lambda cur: cur[0].add_value(key, cur[1]), zip(self.myvectors, values)))

    def get_values(self, key:str) -> np.ndarray:
        """ get values from the zone """

        return np.array([curvec.get_value(key) for curvec in self.myvectors])

    def set_colors_from_value(self, key:str, cmap:wolfpalette | Colormap | cm.ScalarMappable, vmin:float= 0., vmax:float= 1.):
        """ Set the colors for the zone """

        list(map(lambda curvec: curvec.set_color_from_value(key, cmap, vmin, vmax), self.myvectors))

    def set_alpha(self, alpha:int):
        """ Set the alpha for the zone """

        list(map(lambda curvec: curvec.set_alpha(alpha), self.myvectors))

    def set_filled(self, filled:bool):
        """ Set the filled for the zone """

        list(map(lambda curvec: curvec.set_filled(filled), self.myvectors))

    def check_if_open(self):
        """ Check if the vectors in the zone are open """
        list(map(lambda curvect: curvect.check_if_open(), self.myvectors))

    def buffer(self, distance:float, resolution:int=16, inplace:bool = False) -> 'zone':
        """ Create a new zone with a buffer around each vector """

        if inplace:
            newzone = self
        else:
            newzone = zone(name=self.myname)

        retmap = list(map(lambda x: x.buffer(distance, resolution, inplace), self.myvectors))

        if inplace:
            return self

        for curvec in retmap:
            newzone.add_vector(curvec, forceparent=True)

        return newzone

    def set_legend_text(self, text:str):
        """
        Set the legend text for the zone
        """

        list(map(lambda curvect: curvect.set_legend_text(text), self.myvectors))

    def set_legend_text_from_values(self, key:str):
        """
        Set the legend text for the zone from a value
        """

        list(map(lambda curvect: curvect.set_legend_text_from_value(key), self.myvectors))


    def set_legend_position(self, x, y):
        """
        Set the legend position for the zone
        """
        list(map(lambda curvect: curvect.set_legend_position(x, y), self.myvectors))

    @property
    def area(self):
        """ Compute the area of the zone """
        return sum(self.areas)

    @property
    def areas(self):
        """ List of all areas """
        return [curvec.surface for curvec in self.myvectors]

    def set_cache(self):
        """
        Set the cache for the zone and all its vectors
        """

        list(map(lambda curvect: curvect.set_cache(), self.myvectors))

    def clear_cache(self):
        """
        Clear the cache for the zone and all its vectors
        """
        list(map(lambda curvect: curvect.clear_cache(), self.myvectors))

        self._move_start = None
        self._move_step = None
        self._rotation_center = None
        self._rotation_step = None

        self.find_minmax(update=True)

    def move(self, dx:float, dy:float, use_cache:bool=True, inplace:bool=True):
        """
        Move the zone and all its vectors
        """

        if self._move_step is not None:
            dx = np.round(dx/self._move_step)*self._move_step
            dy = np.round(dy/self._move_step)*self._move_step

        if inplace:
            for curvect in self.myvectors:
                curvect.move(dx, dy, use_cache)
            return self
        else:
            newzone = self.deepcopy()
            newzone.move(dx, dy, use_cache= False)
            return newzone

    def rotate(self, angle:float, center:tuple[float,float], use_cache:bool=True, inplace:bool=True):
        """
        Rotate the zone and all its vectors

        :param angle: angle in degrees (clockwise)
        :param center: center of rotation
        :param use_cache: use the cache for the vertices
        :param inplace: modify the zone in place or return a new one
        """

        if inplace:
            for curvect in self.myvectors:
                curvect.rotate(angle, center, use_cache)
            return self
        else:
            newzone = self.deepcopy()
            newzone.rotate(angle, center, use_cache= False)
            return newzone

    def rotate_xy(self, x:float, y:float, use_cache:bool=True, inplace:bool=True):
        """
        Rotate the zone and all its vectors in the xy plane
        """

        if self._rotation_center is None:
            logging.error(_('No rotation center defined - Set it before rotating by this routine'))
            return self

        angle = np.degrees(-np.arctan2(y-self._rotation_center[1], x-self._rotation_center[0]))

        if self._rotation_step is not None:
            angle = np.round(angle/self._rotation_step)*self._rotation_step

        return self.rotate(angle, self._rotation_center, use_cache, inplace)

    @property
    def nbvectors(self):
        return len(self.myvectors)

    def get_mapviewer(self):
        """
        Retourne l'instance de la mapviewer
        """
        return self.parent.get_mapviewer()

    def import_shapelyobj(self, obj):
        """ Importation d'un objet shapely """

        if isinstance(obj, LineString):
            curvec = vector(fromshapely= obj, parentzone=self, name = self.myname)
            self.add_vector(curvec)
        elif isinstance(obj, Polygon):
            curvec = vector(fromshapely= obj, parentzone=self, name = self.myname)
            self.add_vector(curvec)
        elif isinstance(obj, MultiLineString):
            for curls in list(obj.geoms):
                curvec = vector(fromshapely= curls, parentzone=self, name = self.myname)
                self.add_vector(curvec)
        elif isinstance(obj, MultiPolygon):
            for curpoly in list(obj.geoms):
                curvec = vector(fromshapely= curpoly, parentzone=self, name = self.myname)
                self.add_vector(curvec)
        else:
            logging.warning(_('Object type {} not supported -- Update "import_shapelyobj"').format(type(obj)))

    def get_vector(self,keyvector:Union[int, str])->vector:
        """
        Retrouve le vecteur sur base de son nom ou de sa position
        Si plusieurs vecteurs portent le même nom, seule le premier est retourné
        """
        if isinstance(keyvector,int):
            if keyvector < self.nbvectors:
                return self.myvectors[keyvector]
            return None
        if isinstance(keyvector,str):
            zone_names = [cur.myname for cur in self.myvectors]
            if keyvector in zone_names:
                return self.myvectors[zone_names.index(keyvector)]
            return None

    @property
    def vector_names(self)->list[str]:
        """ Return the list of vector names """
        return [cur.myname for cur in self.myvectors]

    def __getitem__(self, ndx:Union[int,str]) -> vector:
        """ Permet de retrouver un vecteur sur base de son index """
        return self.get_vector(ndx)

    def export_shape(self, fn:str = ''):
        """ Export to shapefile using GDAL/OGR """

        from osgeo import osr, ogr

        fn = str(fn)

        # create the spatial reference system, Lambert72
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31370)

        # create the data source
        driver: ogr.Driver
        driver = ogr.GetDriverByName("ESRI Shapefile")

        # create the data source
        if not fn.endswith('.shp'):
            fn += '.shp'
        ds = driver.CreateDataSource(fn)

        # create one layer
        layer = ds.CreateLayer("poly", srs, ogr.wkbPolygon) # FIXME What about other geometries (line, points)?

        # Add ID fields
        idFields=[]
        idFields.append(ogr.FieldDefn('curvi', ogr.OFTReal))
        layer.CreateField(idFields[-1])

        # Create the feature and set values
        featureDefn = layer.GetLayerDefn()
        feature = ogr.Feature(featureDefn)

        for curvec in self.myvectors:
            ring = ogr.Geometry(ogr.wkbLinearRing)
            for curvert in curvec.myvertices:
                # Creating a line geometry
                ring.AddPoint(curvert.x,curvert.y)

            # Create polygon
            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(ring)

            feature.SetGeometry(poly)
            feature.SetField('curvi', float(curvec.myvertices[0].z))

            layer.CreateFeature(feature)

        feature = None

        # Save and close DataSource
        ds = None

    def save(self, f:io.TextIOWrapper):
        """
        Ecriture sur disque
        """
        f.write(self.myname+'\n')
        f.write(str(self.nbvectors)+'\n')
        for curvect in self.myvectors:
            curvect.save(f)

    def save_extra(self, f:io.TextIOWrapper):
        """
        Ecriture des options EXTRA
        """
        f.write(self.myname+'\n')
        curvect:vector
        for curvect in self.myvectors:
            curvect.myprop.save_extra(f)

    def load_extra(self, lines:list[str]) -> int:
        """
        Lecture des options EXTRA
        """
        curvect:vector
        nb_treated = 0
        i=0
        idx_vect = 0
        while nb_treated < self.nbvectors:
            curvect = self.myvectors[idx_vect]
            assert curvect.myname == lines[i], _('Vector name mismatch')
            i+=1
            ret = curvect.myprop.load_extra(lines[i:])
            i+=ret
            nb_treated += 1
            idx_vect += 1

        return i

    def add_vector(self, addedvect:vector, index=-99999, forceparent=False, update_struct=False):
        """
        Ajout d'une instance 'vector'

        :param addedvect: instance 'vector' à ajouter
        :param index: position d'insertion
        :param forceparent: True = forcer le parent à être la zone dans lequel le vecteur est ajouté

        """

        if index==-99999 or index >self.nbvectors:
            self.myvectors.append(addedvect)
        else:
            self.myvectors.insert(index,addedvect)

        # FIXME set vector's parent to self ?
        # NOT necessary because, in some situation, we can add a vector
        #  to a temporary zone without forcing its parent to be this zone
        if forceparent:
            addedvect.parentzone = self

        if self.nbvectors==1:
            self.active_vector = addedvect
            # FIXME else ?
            # NOTHING because the active vector is normally choosen by the UI or during special operations
            # Here, we select the first added vector

        if update_struct:
            self._fill_structure()

    def count(self):
        """
        Compte le nombre de vecteurs

        For compatibility with older versions --> Must be removed in future version
        """
        # self.nbvectors=len(self.myvectors)
        # Nothing to do because the number of vectors is a property
        return

    def _nblines(self):
        """
        Utile pour init par 'lines'
        """
        nb=2
        for curvec in self.myvectors:
            nb+=curvec._nblines()

        return nb

    def find_minmax(self, update=False, only_firstlast:bool=False):
        """
        Recherche de l'emprise spatiale de toute la zone

        :param update: True = mise à jour des valeurs ; False = utilisation des valeurs déjà calculées
        :param only_firstlast: True = recherche uniquement sur les premiers et derniers points de chaque vecteur
        """
        if update:
            for vect in self.myvectors:
                vect.find_minmax(only_firstlast=only_firstlast)

        if self.nbvectors==0:
            self.xmin=-99999.
            self.ymin=-99999.
            self.xmax=-99999.
            self.ymax=-99999.
        else:
            minsx=np.asarray([vect.xmin for vect in self.myvectors if vect.xmin!=-99999.])
            minsy=np.asarray([vect.ymin for vect in self.myvectors if vect.ymin!=-99999.])
            maxsx=np.asarray([vect.xmax for vect in self.myvectors if vect.xmax!=-99999.])
            maxsy=np.asarray([vect.ymax for vect in self.myvectors if vect.ymax!=-99999.])

            if minsx.size == 0:
                self.xmin=-99999.
                self.ymin=-99999.
                self.xmax=-99999.
                self.ymax=-99999.
            else:
                self.xmin = minsx.min()
                self.xmax = maxsx.max()
                self.ymin = minsy.min()
                self.ymax = maxsy.max()

    def prep_listogl(self):
        """
        Préparation des listes OpenGL pour augmenter la vitesse d'affichage
        """
        self.plot(prep = True)

    def plot(self, prep:bool=False, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Graphique OpenGL

        :param prep: True = préparation des listes OpenGL ; False = affichage direct
        """

        if prep:
            if len(self.myvectors) == 0:
                logging.debug(_('No vector in zone -- {}').format(self.myname))
                return

            try:
                if self.idgllist==-99999:
                    self.idgllist = glGenLists(1)

                self.has_legend = False
                self.has_image  = False

                glNewList(self.idgllist,GL_COMPILE)
                for curvect in self.myvectors:
                    curvect.plot()
                    self.has_legend |= curvect.myprop.legendvisible
                    self.has_image  |= curvect.myprop.imagevisible
                glEndList()
            except:
                logging.error(_('OpenGL error in zone.plot'))
        else:
            if len(self.myvectors) == 0:
                logging.debug(_('No vector in zone -- {}').format(self.myname))
                return

            if self.idgllist!=-99999:
                glCallList(self.idgllist)
            else:
                self.has_legend = False
                self.has_image  = False

                for curvect in self.myvectors:
                    curvect.plot()
                    self.has_legend |= curvect.myprop.legendvisible
                    self.has_image  |= curvect.myprop.imagevisible

        if self.has_image:
            for curvect in self.myvectors:
                curvect.plot_image(sx, sy, xmin, ymin, xmax, ymax, size)

        if self.has_legend:
            for curvect in self.myvectors:
                curvect.plot_legend(sx, sy, xmin, ymin, xmax, ymax, size)

    def plot_matplotlib(self, ax:plt.Axes | tuple[Figure, Axes] = None, **kwargs):
        """
        Plot the zone using matplotlib

        :param ax: matplotlib Axes
        :param kwargs: additional arguments
        """

        if isinstance(ax, tuple):
            fig, ax = ax
        elif ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        # for curvect in self.myvectors:
        #     curvect.plot_matplotlib(ax)
        list(map(lambda curvect: curvect.plot_matplotlib(ax), self.myvectors))

        return fig, ax

    def select_vectors_from_point(self,x:float,y:float,inside=True):
        """
        Sélection du vecteur de la zone sur base d'une coordonnée (x,y) -- en 2D

        inside : True = le point est contenu ; False = le point le plus proche
        """

        if self.nbvectors==0:
            logging.warning(_('No vector in zone -- {}').format(self.myname))
            return

        curvect:vector
        self.selected_vectors.clear()

        if inside:
            for curvect in self.myvectors:
                if curvect.isinside(x,y):
                    self.selected_vectors.append((curvect,99999.))
        else:
            distmin=99999.
            for curvect in self.myvectors:
                nvert:wolfvertex
                nvert= curvect.find_nearest_vert(x,y)
                dist=np.sqrt((nvert.x-x)**2.+(nvert.y-y)**2.)
                if dist<distmin:
                    distmin=dist
                    vectmin=curvect

            self.selected_vectors.append((vectmin,distmin))

    def add2tree(self,tree:TreeListCtrl,root):
        """
        Ajout à un objet TreeListCtrl
        """
        self.mytree=tree
        self.myitem=tree.AppendItem(root, self.myname,data=self)

        for curvect in self.myvectors:
            curvect.add2tree(tree,self.myitem)

        if self.used:
            tree.CheckItem(self.myitem)
        else:
            tree.UncheckItem(self.myitem)

    def unuse(self):
        """
        Ne plus utiliser
        """
        for curvect in self.myvectors:
            curvect.unuse()
        self.used=False

        if self.mytree is not None:
            self.mytree.UncheckItem(self.myitem)

        self.reset_listogl()

    def use(self):
        """
        A utiliser
        """
        for curvect in self.myvectors:
            curvect.use()
        self.used=True

        if self.mytree is not None:
            self.mytree.CheckItem(self.myitem)

        self.reset_listogl()

    def asshapely_ls(self):
        """
        Retroune la zone comme MultiLineString Shaely
        """
        mylines=[]
        curvect:vector
        for curvect in self.myvectors:
            mylines.append(curvect.asshapely_ls())
        return MultiLineString(mylines)

    def prepare_shapely(self):
        """
        Converti l'objet en MultiLineString Shapely et stocke dans self.multils
        """
        self.multils = self.asshapely_ls()

    def get_selected_vectors(self,all=False):
        """
        Retourne la liste du/des vecteur(s) sélectionné(s)
        """
        if all:
            mylist=[]
            if len(self.selected_vectors)>0:
                mylist.append(self.selected_vectors)
            return mylist
        else:
            if len(self.selected_vectors)>0:
                return self.selected_vectors[0]

        return None

    def add_parallel(self,distance):
        """
        Ajoute une parallèle au vecteur actif
        """

        if distance>0.:
            mypl = self.active_vector.parallel_offset(distance,'right')
        elif distance<0.:
            mypl = self.active_vector.parallel_offset(distance,'left')
        else:
            mypl = vector(name=self.active_vector.myname+"_duplicate")
            mypl.myvertices = [wolfvertex(cur.x,cur.y,cur.z) for cur in self.active_vector.myvertices]


        if mypl is None:
            return

        mypl.parentzone = self
        self.add_vector(mypl)

    def parallel_active(self,distance):
        """
        Ajoute une parallèle 'left' et 'right' au vecteur actif
        """

        if self.nbvectors>1:
            self.myvectors = [curv for curv in self.myvectors if curv ==self.active_vector]

        mypl = self.active_vector.parallel_offset(distance,'left')
        mypr = self.active_vector.parallel_offset(distance,'right')

        if mypl is None or mypr is None:
            return

        self.add_vector(mypl, 0)
        self.add_vector(mypr, 2)

    def create_multibin(self, nb:int = None, nb2:int = 0) -> Triangulation:
        """
        Création d'une triangulation sur base des vecteurs
        Tient compte de l'ordre

        :param nb : nombre de points de découpe des vecteurs
        :param nb2 : nombre de points en perpendiculaire

        return :
         - instance de 'Triangulation'
        """

        wx_exists = wx.App.Get() is not None

        # transformation des vecteurs en polyline shapely
        nbvectors = self.nbvectors
        myls = []
        for curv in self.myvectors:
            myls.append(curv.asshapely_ls())

        if nb is None and wx_exists:
            dlg=wx.NumberEntryDialog(None,
                                     _('How many points along polylines ?')+'\n'+
                                     _('Length size is {} meters').format(myls[0].length),
                                     'nb',
                                     'dl size',
                                     100,
                                     1,
                                     10000)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            nb=int(dlg.GetValue())
            dlg.Destroy()
        else:
            try:
                nb=int(nb)
            except:
                logging.warning( _('Bad parameter nb'))
                return None

        # redécoupage des polylines
        s = np.linspace(0.,1.,num=nb,endpoint=True)

        newls = []
        for curls in myls:
            newls.append(LineString([curls.interpolate(curs,True) for curs in s]))

        if nb2==0 and wx_exists:
            dlg=wx.NumberEntryDialog(None,
                                     _('How many points between two polylines ?'),
                                     'nb2',
                                     'perpendicular',
                                     0,
                                     1,
                                     10000)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return None

            nb2=int(dlg.GetValue())
            dlg.Destroy()
        else:
            try:
                nb2=int(nb2)
            except:
                logging.warning( _('Bad parameter nb2'))
                return None

        if nb2>0:
            finalls = []
            ds = 1./float(nb2+1)
            sperp = np.arange(ds,1.,ds)

            for j in range(len(newls)-1):
                myls1:LineString
                myls2:LineString
                myls1 = newls[j]
                myls2 = newls[j+1]
                xyz1 = np.asarray(myls1.coords[:])
                xyz2 = np.asarray(myls2.coords[:])

                finalls.append(myls1)

                for curds in sperp:
                    finalls.append(LineString(xyz1*(1.-curds)+xyz2*curds))

            finalls.append(myls2)
            newls = finalls

        nbvectors = len(newls)
        points=np.zeros((nb*nbvectors,3),dtype=np.float64)

        xyz=[]
        for curls in newls:
            xyz.append(np.asarray(curls.coords[:]))

        decal=0
        for i in range(len(xyz[0])):
            for k in range(nbvectors):
                points[k+decal,:] = xyz[k][i]
            decal+=nbvectors

        decal=0
        triangles=[]

        nbpts=nbvectors
        triangles.append([[i+decal,i+decal+1,i+decal+nbpts] for i in range(nbpts-1)])
        triangles.append([[i+decal+nbpts,i+decal+1,i+decal+nbpts+1] for i in range(nbpts-1)])

        for k in range(1,nb-1):
            decal=k*nbpts
            triangles.append([ [i+decal,i+decal+1,i+decal+nbpts] for i in range(nbpts-1)])
            triangles.append([ [i+decal+nbpts,i+decal+1,i+decal+nbpts+1] for i in range(nbpts-1)])
        triangles=np.asarray(triangles,dtype=np.uint32).reshape([(2*nbpts-2)*(nb-1),3])

        mytri=Triangulation(pts=points,tri=triangles)
        mytri.find_minmax(True)

        return mytri

    def create_tri_crosssection(self, ds:float = 1.) -> Triangulation:
        """ Create a triangulation like cross sections and support vectors.
        """

        supports = [curv for curv in self.myvectors if curv.myname.startswith('support')]
        others = [curv for curv in self.myvectors if curv not in supports]

        if len(supports) ==0:
            logging.error(_('No support vector found'))
            return None

        if len(others) == 0:
            logging.error(_('No cross section vector found'))
            return None

        from .PyCrosssections import Interpolators, crosssections, profile

        banks = Zones(plotted=False)
        onezone = zone(name='support')
        banks.add_zone(onezone, forceparent=True)
        onezone.myvectors = supports

        cs = crosssections(plotted=False)
        for curprof in others:
            cs.add(curprof)

        cs.verif_bed()
        cs.find_minmax(True)
        cs.init_cloud()
        cs.sort_along(supports[0].asshapely_ls(), 'poly', downfirst = False)
        # cs.set_zones(True)

        interp = Interpolators(banks, cs, ds)
        interp.export_gltf()

        return interp

    def create_constrainedDelaunay(self, nb:int = None) -> Triangulation:
        """
        Création d'une triangulation Delaunay contrainte sur base des vecteurs de la zone.

        Il est nécessaire de définir au moins un polygone définissant la zone de triangulation.
        Les autres vecteurs seront utilisés comme contraintes de triangulation.

        Utilisation de la librairie "triangle" (https://www.cs.cmu.edu/~quake/triangle.delaunay.html)

        :param nb: nombre de points de découpe des vecteurs (0 pour ne rien redécouper)
        """

        wx_exists = wx.App.Get() is not None

        # Transformation des vecteurs en polylines shapely
        # Utile pour le redécoupage
        myls = []
        for curv in self.myvectors:
            myls.append(curv.asshapely_ls())

        meanlength = np.mean([curline.length for curline in myls])

        if nb is None and wx_exists:
            dlg=wx.NumberEntryDialog(None,
                                     _('How many points along polylines ? (0 to use as it is)')+'\n'+
                                     _('Mean length size is {} meters').format(meanlength),
                                     'nb',
                                     'dl size',
                                     100,
                                     0,
                                     10000)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            nb=int(dlg.GetValue())
            dlg.Destroy()
        else:
            try:
                nb=int(nb)
            except:
                logging.warning( _('Bad parameter nb'))
                return None

        if nb==0:
            # no decimation
            newls = myls
        else:
            # redécoupage des polylines
            s = np.linspace(0., 1., num=nb, endpoint=True)

            newls = [LineString([curls.interpolate(curs,True) for curs in s]) for curls in myls if curls.length>0.]

        # Récupération des coordonnées des points
        xyz = [np.asarray(curls.coords[:]) for curls in newls]
        xyz = np.concatenate(xyz)

        # Recherche du minimum pour recentrer les coordonnées et éviter des erreurs de calcul
        xmin = xyz[:,0].min()
        ymin = xyz[:,1].min()

        xyz[:,0] -= xmin
        xyz[:,1] -= ymin

        # Remove duplicate points
        xyz, indices = np.unique(xyz, axis=0, return_inverse=True)

        # Numérotation des segments
        segments = []
        k = 0
        for cur in newls:
            for i in range(len(cur.coords)-1):
                segments.append([indices[k], indices[k+1]])
                k+=1

        # Création de la géométrie pour la triangulation
        geom = {'vertices' : [[x,y] for x,y in xyz[:,:2]],
                'segments' : segments}

        try:
            # Triangulation
            delaunay = triangle.triangulate(geom, 'p') # d'autres options sont possibles (voir la doc de triangle)

            # Recover z values from xyz for each vertex
            # Searching value in xyz is not the best way
            # We create a dictionary to avoid searching manually
            xyz_dict = {(curxyz[0], curxyz[1]): curxyz[2] for curxyz in xyz}
            allvert = []
            for curvert in delaunay['vertices']:
                x = curvert[0]
                y = curvert[1]
                z = xyz_dict.get((x, y), 0.)
                allvert.append([x + xmin, y + ymin, z])

            # Create the Triangulation object
            mytri=Triangulation(pts= allvert,
                                tri= [curtri for curtri in delaunay['triangles']])
            mytri.find_minmax(True)

        except Exception as e:
            logging.error(_('Error in constrained Delaunay triangulation - {e}'))
            return None

        return mytri

    def createmultibin_proj(self, nb=None, nb2=0) -> Triangulation:
        """
        Création d'une triangulation sur base des vecteurs par projection au plus proche du vecteur central
        Tient compte de l'ordre

        :param nb : nombre de points de découpe des vecteurs
        :param nb2 : nombre de points en perpendiculaire

        return :
         - instance de 'Triangulation'
        """

        wx_exists = wx.App.Get() is not None

        # transformation des vecteurs en polyline shapely
        nbvectors = self.nbvectors
        myls = []
        for curv in self.myvectors:
            myls.append(curv.asshapely_ls())

        if nb is None and wx_exists:
            dlg=wx.NumberEntryDialog(None,_('How many points along polylines ?')+'\n'+
                                        _('Length size is {} meters').format(myls[0].length),'nb','dl size',100,1,10000)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            nb=int(dlg.GetValue())
            dlg.Destroy()
        else:
            logging.warning( _('Bad parameter nb'))

        # redécoupage des polylines
        s = np.linspace(0.,1.,num=nb,endpoint=True)

        newls = []
        supportls = myls[int(len(myls)/2)]
        supportls = LineString([supportls.interpolate(curs,True) for curs in s])
        for curls in myls:
            curls:LineString
            news = [curls.project(Point(curpt[0], curpt[1])) for curpt in supportls.coords]
            news.sort()
            newls.append(LineString([curls.interpolate(curs) for curs in news]))

        if nb2==0 and wx_exists:
            dlg=wx.NumberEntryDialog(None,_('How many points between two polylines ?'), 'nb2','perpendicular',0,0,10000)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            nb2=int(dlg.GetValue())
            dlg.Destroy()

        if nb2>0:
            finalls = []
            ds = 1./float(nb2+1)
            sperp = np.arange(ds,1.,ds)

            for j in range(len(newls)-1):
                myls1:LineString
                myls2:LineString
                myls1 = newls[j]
                myls2 = newls[j+1]
                xyz1 = np.asarray(myls1.coords[:])
                xyz2 = np.asarray(myls2.coords[:])

                finalls.append(myls1)

                for curds in sperp:
                    finalls.append(LineString(xyz1*(1.-curds)+xyz2*curds))

            finalls.append(myls2)
            newls = finalls

        nbvectors = len(newls)
        points=np.zeros((nb*nbvectors,3),dtype=np.float64)

        xyz=[]
        for curls in newls:
            xyz.append(np.asarray(curls.coords[:]))

        decal=0
        for i in range(len(xyz[0])):
            for k in range(nbvectors):
                points[k+decal,:] = xyz[k][i]
            decal+=nbvectors

        decal=0
        triangles=[]

        nbpts=nbvectors
        triangles.append([[i+decal,i+decal+1,i+decal+nbpts] for i in range(nbpts-1)])
        triangles.append([[i+decal+nbpts,i+decal+1,i+decal+nbpts+1] for i in range(nbpts-1)])

        for k in range(1,nb-1):
            decal=k*nbpts
            triangles.append([ [i+decal,i+decal+1,i+decal+nbpts] for i in range(nbpts-1)])
            triangles.append([ [i+decal+nbpts,i+decal+1,i+decal+nbpts+1] for i in range(nbpts-1)])
        triangles=np.asarray(triangles,dtype=np.uint32).reshape([(2*nbpts-2)*(nb-1),3])

        mytri=Triangulation(pts=points,tri=triangles)
        mytri.find_minmax(True)

        return mytri

    def create_polygon_from_parallel(self, ds:float, howmanypoly=1) ->None:
        """
        Création de polygones depuis des vecteurs parallèles

        La zone à traiter ne peut contenir que 3 vecteurs

        Une zone de résultat est ajouté à l'objet

        ds : desired size/length of the polygon, adjusted on the basis of a number of polygons rounded up to the nearest integer
        howmanypoly : Number of transversal polygons (1 = one large polygon, 2 = 2 polygons - one left and one right)
        """

        assert self.nbvectors==3, _('The zone must contain 3 and only 3 vectors')

        vecleft:vector
        vecright:vector
        veccenter:vector
        vecleft = self.myvectors[0]
        veccenter = self.myvectors[1]
        vecright = self.myvectors[2]

        #Shapely LineString
        lsl = vecleft.asshapely_ls()
        lsr = vecright.asshapely_ls()
        lsc = veccenter.asshapely_ls()

        #Number of points
        nb = int(np.ceil(lsc.length / ds))
        #Adimensional distances along center vector
        sloc = np.linspace(0.,1.,nb,endpoint=True)
        #Points along center vector
        ptsc = [lsc.interpolate(curs,True) for curs in sloc]
        #Real distances along left, right and center vector
        sl = [lsl.project(curs) for curs in ptsc]
        sr = [lsr.project(curs) for curs in ptsc]
        sc = [lsc.project(curs) for curs in ptsc]

        if howmanypoly==1:
            #un seul polygone sur base des // gauche et droite
            zonepoly = zone(name='polygons_'+self.myname,parent=self.parent)

            self.parent.add_zone(zonepoly)

            for i in range(len(sl)-1):

                #mean distance along center will be stored as Z value of each vertex
                smean =(sc[i]+sc[i+1])/2.
                curvec=vector(name='poly'+str(i+1),parentzone=zonepoly)
                #Substring for Left and Right
                sublsl = vecleft.substring(sl[i], sl[i+1], False, False)
                sublsr = vecright.substring(sr[i], sr[i+1], False, False)
                # sublsl=substring(lsl,sl[i],sl[i+1])
                # sublsr=substring(lsr,sr[i],sr[i+1])

                #Test if the substring result is Point or LineString
                if isinstance(sublsl, vector):
                    vr = sublsr.myvertices.copy()
                    vr.reverse()
                    curvec.myvertices = sublsl.myvertices.copy() + vr
                    for curv in curvec.myvertices:
                        curv.z = smean
                else:
                    if sublsl.geom_type=='Point':
                        curvec.add_vertex(wolfvertex(sublsl.x,sublsl.y,smean))
                    elif sublsl.geom_type=='LineString':
                        xy=np.asarray(sublsl.coords)
                        for (x,y) in xy:
                            curvec.add_vertex(wolfvertex(x,y,smean))

                    if sublsr.geom_type=='Point':
                        curvec.add_vertex(wolfvertex(sublsr.x,sublsr.y,smean))
                    elif sublsr.geom_type=='LineString':
                        xy=np.asarray(sublsr.coords)
                        xy=np.flipud(xy)
                        for (x,y) in xy:
                            curvec.add_vertex(wolfvertex(x,y,smean))

                #force to close the polygon
                curvec.close_force()
                #add vector to zone
                zonepoly.add_vector(curvec)

                #set legend text
                curvec.myprop.legendtext = '{:.2f}'.format(smean)

                xy = curvec.asnparray()
                curvec.myprop.legendx = np.mean(xy[:,0])
                curvec.myprop.legendy = np.mean(xy[:,1])

            #force to update minmax in the zone --> mandatory to plot
            zonepoly.find_minmax(True)
        else:
            #deux polygones sur base des // gauche et droite
            zonepolyleft = zone(name='polygons_left_'+self.myname,parent=self.parent)
            zonepolyright = zone(name='polygons_right_'+self.myname,parent=self.parent)
            self.parent.add_zone(zonepolyleft)
            self.parent.add_zone(zonepolyright)

            for i in range(len(sl)-1):

                smean =(sc[i]+sc[i+1])/2.
                curvecleft=vector(name='poly'+str(i+1),parentzone=zonepolyleft)
                curvecright=vector(name='poly'+str(i+1),parentzone=zonepolyright)

                # sublsl=substring(lsl,sl[i],sl[i+1])
                # sublsr=substring(lsr,sr[i],sr[i+1])
                # sublsc=substring(lsc,sc[i],sc[i+1])
                sublsl = vecleft.substring(sl[i], sl[i+1], False, False)
                sublsr = vecright.substring(sr[i], sr[i+1], False, False)
                sublsc = veccenter.substring(sc[i], sc[i+1], False, False)

                if isinstance(sublsl, vector):
                    vr = sublsr.myvertices.copy()
                    vr.reverse()
                    vcr = sublsc.myvertices.copy()
                    vcr.reverse()
                    curvecleft.myvertices = sublsl.myvertices.copy() + vcr
                    curvecright.myvertices = sublsc.myvertices.copy() + vr
                    for curv in curvecleft.myvertices:
                        curv.z = smean
                    for curv in curvecright.myvertices:
                        curv.z = smean
                else:
                    #left poly
                    if sublsl.geom_type=='Point':
                        curvecleft.add_vertex(wolfvertex(sublsl.x,sublsl.y,smean))
                    elif sublsl.geom_type=='LineString':
                        xy=np.asarray(sublsl.coords)
                        for (x,y) in xy:
                            curvecleft.add_vertex(wolfvertex(x,y,smean))

                    if sublsc.geom_type=='Point':
                        curvecleft.add_vertex(wolfvertex(sublsc.x,sublsc.y,smean))
                    elif sublsc.geom_type=='LineString':
                        xy=np.asarray(sublsc.coords)
                        xy=np.flipud(xy)
                        for (x,y) in xy:
                            curvecleft.add_vertex(wolfvertex(x,y,smean))

                    #right poly
                    if sublsc.geom_type=='Point':
                        curvecright.add_vertex(wolfvertex(sublsc.x,sublsc.y,smean))
                    elif sublsc.geom_type=='LineString':
                        xy=np.asarray(sublsc.coords)
                        for (x,y) in xy:
                            curvecright.add_vertex(wolfvertex(x,y,smean))

                    if sublsr.geom_type=='Point':
                        curvecright.add_vertex(wolfvertex(sublsr.x,sublsr.y,smean))
                    elif sublsr.geom_type=='LineString':
                        xy=np.asarray(sublsr.coords)
                        xy=np.flipud(xy)
                        for (x,y) in xy:
                            curvecright.add_vertex(wolfvertex(x,y,smean))

                curvecleft.close_force()
                curvecright.close_force()

                #set legend text
                curvecleft.myprop.legendtext = '{:.2f}'.format(smean)
                curvecright.myprop.legendtext = '{:.2f}'.format(smean)

                xy = curvecleft.asnparray()
                curvecleft.myprop.legendx = np.mean(xy[:,0])
                curvecleft.myprop.legendy = np.mean(xy[:,1])
                xy = curvecright.asnparray()
                curvecright.myprop.legendx = np.mean(xy[:,0])
                curvecright.myprop.legendy = np.mean(xy[:,1])

                zonepolyleft.add_vector(curvecleft)
                zonepolyright.add_vector(curvecright)


            zonepolyleft.find_minmax(True)
            zonepolyright.find_minmax(True)

        self._fill_structure()

    def _fill_structure(self):
        """
        Mise à jour des structures
        """
        if self.parent is not None:
            self.parent.fill_structure()

    def create_sliding_polygon_from_parallel(self,
                                             poly_length:float,
                                             ds_sliding:float,
                                             farthest_parallel:float,
                                             interval_parallel:float=None,
                                             intersect=None,
                                             howmanypoly=1,
                                             eps_offset:float=0.25):
        """
        Create sliding polygons from a support vector.

        "poly_length" is the length of the polygons.
        "ds_sliding" is the sliding length.

        If "ds_sliding" is lower than "ds", the polygons are overlapping.
        If "ds_sliding" is greater than "ds", the polygons are separated.
        If "ds_sliding" is equal to "ds", the polygons are adjacent.

        The zone to be processed can only contain 1 vector.
        A result zone is added to the object.

        The sliding polygons are created on the basis of the left
        and right parallels of the central vector.

        "farthest_parallel" is the farthest parallel.
        "interval_parallel" is the distance between each parallels. If not defined, it is equal to "farthest_parallel".

        Lateral sides of the polygons are defined by projecting the
        points/vertices of the support vector onto the parallels,
        from the nearest to the farthest.

        The method first creates the parallels.
        Then, it intersects the parallels with the constraints defined in the "intersect" zone.
        The intersection is done with an offset defined by "eps_offset".

        :param poly_length: size/length of the polygon, adjusted on the basis of a number of polygons rounded up to the nearest integer
        :param ds_sliding: sliding length
        :param farthest_parallel: position of the parallels
        :param interval_parallel: parallel intervals (internal computation)
        :param intersect:  zone class containing constraints
        :param howmanypoly: number of transversal polygons (1 = one large polygon, 2 = 2 polygons - one left and one right)
        :param eps_offset: space width impose to the "intersect"
        """

        assert self.nbvectors==1, _('The zone must contain 1 and only 1 vector')

        veccenter:vector

        # All parallels on the left
        vecleft:dict[str,vector]={}
        # All parallels on the right
        vecright:dict[str,vector]={}
        veccenter = self.myvectors[0]
        veccenter.update_lengths()

        logging.info(_('Length of the center vector: {}').format(veccenter.length2D))

        # Returned zone
        myparallels = zone()

        if interval_parallel is None :
            logging.warning(_('Interval between parallels is not defined --> set to farthest_parallel'))
            interval_parallel : farthest_parallel

        if interval_parallel > farthest_parallel:
            logging.warning(_('Interval between parallels is greater than farthest_parallel --> set to farthest_parallel'))
            interval_parallel = farthest_parallel

        # All parallel distances
        all_par = np.arange(0, farthest_parallel, interval_parallel)[1:]
        all_par = np.concatenate((all_par,[farthest_parallel]))
        logging.info(_('All parallel distances: {}').format(all_par))

        for curpar in tqdm(all_par):
            # add current parallel to the dicts
            vecleft[curpar] = veccenter.parallel_offset(curpar, 'left')
            vecright[curpar]= veccenter.parallel_offset(curpar, 'right')

            myparallels.add_vector(vecleft[curpar], forceparent=True)
            myparallels.add_vector(vecright[curpar], forceparent=True)

            if isinstance(intersect, zone):
                # Some constraints are defined
                #
                # gestion de vecteurs d'intersection
                for curint in intersect.myvectors:
                    if not curint.used:
                        continue

                    # bouclage sur les vecteurs
                    curint1 = curint.parallel_offset(-eps_offset/2., side='left')
                    curint2 = curint.parallel_offset( eps_offset/2., side='right')

                    # recherche si une intersection existe
                    pt, dist = vecleft[curpar].intersection(curint1, eval_dist=True, force_single=True)
                    if pt is not None:
                        logging.debug(_('Intersection found on left parallel at distance {}').format(dist))
                        #Une intersection existe --> on ajoute la portion de vecteur

                        # Projection du point d'intersection sur le vecteur à suivre
                        dist2 = curint1.linestring.project(pt)

                        # recherche de la portion de vecteur
                        # subs = extrêmité -> intersection
                        # subs_inv = intersection -> extrêmité
                        subs  = curint1.substring(0. , dist2, is3D=False, adim=False)
                        subs.reverse()

                        subs2 = curint2.substring(0., dist2, is3D=False, adim=False)

                        vec1 = vecleft[curpar].substring(0., dist, is3D=False, adim=False)
                        vec2 = vecleft[curpar].substring(dist, vecleft[curpar].length2D, is3D=False, adim=False)

                        # combinaison du nouveau vecteur vecleft constitué de :
                        #  - la partie avant l'intersection
                        #  - l'aller-retour
                        #  - la partie après l'intersection
                        vecleft[curpar].myvertices = vec1.myvertices.copy() + subs.myvertices.copy() + subs2.myvertices.copy() + vec2.myvertices.copy()

                        # mise à jour des caractéristiques
                        vecleft[curpar].find_minmax()
                        vecleft[curpar].update_lengths()
                        vecleft[curpar].reset_linestring()
                        curint1.reset_linestring()
                        curint2.reset_linestring()

                    pt, dist = vecright[curpar].intersection(curint1, eval_dist=True, force_single=True)
                    if pt is not None:
                        logging.debug(_('Intersection found on right parallel at distance {}').format(dist))

                        dist2 = curint1.linestring.project(pt)

                        #Une intersection existe --> on ajoute la portion de vecteur
                        subs  = curint1.substring(0., dist2, is3D=False, adim=False)

                        subs2 = curint2.substring(0., dist2, is3D=False, adim=False)
                        subs2.reverse()

                        vec1 = vecright[curpar].substring(0., dist, is3D=False, adim=False)
                        vec2 = vecright[curpar].substring(dist, vecright[curpar].length2D, is3D=False, adim=False)

                        vecright[curpar].myvertices = vec1.myvertices.copy() + subs2.myvertices.copy() + subs.myvertices.copy() + vec2.myvertices.copy()

                        vecright[curpar].find_minmax()
                        vecright[curpar].update_lengths()
                        vecright[curpar].reset_linestring()
                        curint1.reset_linestring()
                        curint2.reset_linestring()

        #Shapely LineString
        lsl:dict[str,LineString] = {key:vec.asshapely_ls() for key,vec in vecleft.items()}
        lsr:dict[str,LineString] = {key:vec.asshapely_ls() for key,vec in vecright.items()}
        lsc = veccenter.asshapely_ls()

        #Number of points
        nb = int(np.ceil(lsc.length / float(ds_sliding)))

        #Dimensional distances along center vector
        sloc = np.asarray([float(ds_sliding) * cur for cur in range(nb)])
        sloc2 = sloc + float(poly_length)
        sloc2[sloc2>veccenter.length2D]=veccenter.length2D

        #Points along center vector
        ptsc  = [veccenter.interpolate(curs, is3D=False, adim=False) for curs in sloc]
        ptsc2 = [veccenter.interpolate(curs, is3D=False, adim=False) for curs in sloc2]

        sc  = [lsc.project(Point(curs.x, curs.y)) for curs in ptsc]
        sc2 = [lsc.project(Point(curs.x, curs.y)) for curs in ptsc2]

        #Real distances along left, right and center vector
        sl={}
        sr={}
        sl2={}
        sr2={}
        ptl={}
        ptl2={}
        ptr={}
        ptr2={}

        # on calcule les points de proche en proche (// par //)
        # utile pour la prise en compte des intersections avec les polylignes de contrainte
        curpts = ptsc
        for key,ls in lsl.items():
            sl[key]  = [ls.project(Point(curs.x, curs.y)) for curs in curpts]
            ptl[key] = [ls.interpolate(curs) for curs in sl[key]]
            curpts = ptl[key]

        curpts = ptsc2
        for key,ls in lsl.items():
            sl2[key]  = [ls.project(Point(curs.x, curs.y)) for curs in curpts]
            ptl2[key] = [ls.interpolate(curs) for curs in sl2[key]]
            curpts = ptl2[key]

        curpts = ptsc
        for key,ls in lsr.items():
            sr[key]  = [ls.project(Point(curs.x, curs.y)) for curs in curpts]
            ptr[key] = [ls.interpolate(curs) for curs in sr[key]]
            curpts = ptr[key]

        curpts = ptsc2
        for key,ls in lsr.items():
            sr2[key]  = [ls.project(Point(curs.x, curs.y)) for curs in curpts]
            ptr2[key] = [ls.interpolate(curs) for curs in sr2[key]]
            curpts = ptr2[key]

        if howmanypoly==1:
            #un seul polygone sur base des // gauche et droite
            zonepoly = zone(name='polygons_'+self.myname, parent=self.parent)

            self.parent.add_zone(zonepoly, forceparent=True)

            for i in range(nb):
                ptc1 = sc[i]
                ptc2 = sc2[i]
                pt1 = [cur[i] for cur in sl.values()]
                pt2 = [cur[i] for cur in sl2.values()]
                pt3 = [cur[i] for cur in sr.values()]
                pt4 = [cur[i] for cur in sr2.values()]

                #mean distance along center will be stored as Z value of each vertex
                smean =(ptc1+ptc2)/2.
                curvec=vector(name='poly'+str(i), parentzone=zonepoly)

                #Substring for Left and Right
                sublsl=vecleft[farthest_parallel].substring(pt1[-1], pt2[-1], is3D=False, adim=False)
                sublsr=vecright[farthest_parallel].substring(pt3[-1], pt4[-1], is3D=False, adim=False)
                sublsr.reverse()
                sublsc=veccenter.substring(ptc1,ptc2,is3D=False, adim=False)

                upl   = [wolfvertex(pt[i].x, pt[i].y) for pt in ptl.values()]
                upr   = [wolfvertex(pt[i].x, pt[i].y) for pt in ptr.values()]
                upr.reverse()
                downl = [wolfvertex(pt[i].x, pt[i].y) for pt in ptl2.values()]
                downl.reverse()
                downr = [wolfvertex(pt[i].x, pt[i].y) for pt in ptr2.values()]

                curvec.myvertices = sublsl.myvertices.copy() + downl[1:].copy() + [sublsc.myvertices[-1].copy()] + downr[:-1].copy() + sublsr.myvertices.copy() + upr[1:].copy() + [sublsc.myvertices[0].copy()] + upl[:-1].copy()
                for curvert in curvec.myvertices:
                    curvert.z = smean

                #force to close the polygon
                curvec.close_force()
                #add vector to zone
                zonepoly.add_vector(curvec, forceparent=True)

            #force to update minmax in the zone --> mandatory to plot
            zonepoly.find_minmax(True)
        else:
            #deux polygones sur base des // gauche et droite
            zonepolyleft = zone(name='polygons_left_'+self.myname, parent=self.parent)
            zonepolyright = zone(name='polygons_right_'+self.myname, parent=self.parent)
            self.parent.add_zone(zonepolyleft, forceparent=True)
            self.parent.add_zone(zonepolyright, forceparent=True)

            for i in range(nb):
                ptc1 = sc[i]
                ptc2 = sc2[i]
                pt1 = [cur[i] for cur in sl.values()]
                pt2 = [cur[i] for cur in sl2.values()]
                pt3 = [cur[i] for cur in sr.values()]
                pt4 = [cur[i] for cur in sr2.values()]

                #mean distance along center will be stored as Z value of each vertex
                smean =(ptc1+ptc2)/2.
                curvecleft=vector(name='poly'+str(i+1), parentzone=zonepolyleft)
                curvecright=vector(name='poly'+str(i+1), parentzone=zonepolyright)

                #Substring for Left and Right
                sublsl=vecleft[farthest_parallel].substring(pt1[-1], pt2[-1], is3D=False, adim=False)
                sublsr=vecright[farthest_parallel].substring(pt3[-1], pt4[-1], is3D=False, adim=False)
                sublsr.reverse()

                sublsc=veccenter.substring(ptc1,ptc2,is3D=False, adim=False)
                sublscr = sublsc.deepcopy()
                sublscr.reverse()

                upl   = [wolfvertex(pt[i].x, pt[i].y) for pt in ptl.values()]
                upr   = [wolfvertex(pt[i].x, pt[i].y) for pt in ptr.values()]
                upr.reverse()
                downl = [wolfvertex(pt[i].x, pt[i].y) for pt in ptl2.values()]
                downl.reverse()
                downr = [wolfvertex(pt[i].x, pt[i].y) for pt in ptr2.values()]

                curvecleft.myvertices  = sublsl.myvertices.copy() + downl[1:-1].copy() + sublscr.myvertices.copy() + upl[1:-1].copy()
                curvecright.myvertices = sublsc.myvertices.copy() + downr[1:-1].copy() + sublsr.myvertices.copy() + upr[1:-1].copy()

                for curvert in curvecleft.myvertices:
                    curvert.z = smean
                for curvert in curvecright.myvertices:
                    curvert.z = smean

                curvecleft.close_force()
                curvecright.close_force()

                zonepolyleft.add_vector(curvecleft)
                zonepolyright.add_vector(curvecright)

            zonepolyleft.find_minmax(True)
            zonepolyright.find_minmax(True)

        self._fill_structure()

        if self.get_mapviewer() is not None:
            self.get_mapviewer().Paint()

        return myparallels

    def get_values_linked_polygons(self, linked_arrays, stats=True) -> dict:
        """
        Récupération des valeurs contenues dans tous les polygones de la zone

        Retourne un dictionnaire contenant les valeurs pour chaque polygone

        Les valeurs de chaque entrée du dict peuvent contenir une ou plusieurs listes en fonction du retour de la fonction de l'objet matriciel appelé
        """
        exit=True
        for curarray in linked_arrays:
            if curarray.plotted:
                exit=False

        if exit:
            return None

        vals= {idx: {'values' : curpol.get_values_linked_polygon(linked_arrays)} for idx, curpol in enumerate(self.myvectors)}

        if stats:
            self._stats_values(vals)

        return vals

    def get_all_values_linked_polygon(self, linked_arrays, stats=True, key_idx_names:Literal['idx', 'name']='idx', getxy=False) -> dict:
        """
        Récupération des valeurs contenues dans tous les polygones de la zone

        Retourne un dictionnaire contenant les valeurs pour chaque polygone

        ATTENTION :
           Il est possible de choisir comme clé soit l'index du vecteur dans la zone, soit non nom
           Si le nom est choisi, cela peut aboutir à une perte d'information car il n'y a pas de certitude que les noms de vecteur soient uniques
           --> il est nécessaire que l'utilisateur soit conscient de cette possibilité

        Les valeurs de chaque entrée du dict peuvent contenir une ou plusieurs listes en fonction du retour de la fonction de l'objet matriciel appelé
        """
        exit=True
        for curarray in linked_arrays:
            if curarray.plotted:
                exit=False

        if exit:
            return None

        if key_idx_names=='idx':
            vals= {idx: {'values' : curpol.get_all_values_linked_polygon(linked_arrays, getxy=getxy)} for idx, curpol in enumerate(self.myvectors)}
        else:
            vals= {curpol.myname: {'values' : curpol.get_all_values_linked_polygon(linked_arrays, getxy=getxy)} for idx, curpol in enumerate(self.myvectors)}

        # if stats:
        #     self._stats_values(vals)

        return vals

    def _stats_values(self,vals:dict):
        """
        Compute statistics on values dict resulting from 'get_values_linked_polygons'
        """

        for curpol in vals.values():
            medianlist  =curpol['median'] = []
            meanlist = curpol['mean'] = []
            minlist = curpol['min'] = []
            maxlist = curpol['max'] = []
            p95 = curpol['p95'] = []
            p5 = curpol['p5'] = []
            for curval in curpol['values']:

                if curval[1] is not None:

                    if curval[0] is not None and len(curval[0])>0:

                        medianlist.append(  (np.median(curval[0]),  np.median(curval[1]) ) )
                        meanlist.append(    (np.mean(curval[0]),    np.mean(curval[1]) ) )
                        minlist.append(     (np.min(curval[0]),      np.min(curval[1]) ) )
                        maxlist.append(     (np.max(curval[0]),      np.max(curval[1]) ) )
                        p95.append(         (np.percentile(curval[0],95),   np.percentile(curval[1],95) ) )
                        p5.append(          (np.percentile(curval[0],5),    np.percentile(curval[1],5)  ) )

                    else:
                        medianlist.append((None,None))
                        meanlist.append((None,None))
                        minlist.append((None,None))
                        maxlist.append((None,None))
                        p95.append((None,None))
                        p5.append((None,None))
                else:

                    if curval[0] is not None and len(curval[0])>0:
                        medianlist.append(np.median(curval[0]))
                        meanlist.append(np.mean(curval[0]))
                        minlist.append(np.min(curval[0]))
                        maxlist.append(np.max(curval[0]))
                        p95.append(np.percentile(curval[0],95))
                        p5.append(np.percentile(curval[0],5))
                    else:
                        medianlist.append(None)
                        meanlist.append(None)
                        minlist.append(None)
                        maxlist.append(None)
                        p95.append(None)
                        p5.append(None)

    def plot_linked_polygons(self, fig:Figure, ax:Axes,
                             linked_arrays:dict, linked_vec:dict[str,"Zones"]=None,
                             linestyle:str='-', onlymedian:bool=False,
                             withtopography:bool = True, ds:float = None):
        """
        Création d'un graphique sur base des polygones

        Chaque polygone se positionnera sur base de la valeur Z de ses vertices
           - façon conventionnelle de définir une longueur
           - ceci est normalement fait lors de l'appel à 'create_polygon_from_parallel'
           - si les polygones sont créés manuellement, il faut donc prendre soin de fournir l'information adhoc ou alors utiliser l'rgument 'ds'

        ATTENTION : Les coordonnées Z ne sont sauvegardées sur disque que si le fichier est 3D, autrement dit au format '.vecz'

        :param fig: Figure
        :param ax: Axes
        :param linked_arrays: dictionnaire contenant les matrices à lier -- les clés sont les labels
        :param linked_vec: dictionnaire contenant les instances Zones à lier -- Besoin d'une zone et d'un vecteur 'trace/trace' pour convertir les positions en coordonnées curvilignes
        :param linestyle: style de ligne
        :param onlymedian: affiche uniquement la médiane
        :param withtopography: affiche la topographie
        :param ds: pas spatial le long de l'axe

        """

        colors=['red','blue','green','darkviolet','fuchsia','lime']

        #Vérifie qu'au moins une matrice liée est fournie, sinon rien à faire
        exit=True
        for curlabel, curarray in linked_arrays.items():
            if curarray.plotted:
                exit=False
        if exit:
            return

        k=0

        zmin=99999.
        zmax=-99999.

        if ds is None:
            # Récupération des positions
            srefs=np.asarray([curpol.myvertices[0].z for curpol in self.myvectors])
        else:
            # Création des positions sur base de 'ds'
            srefs=np.arange(0., float(self.nbvectors) * ds, ds)

        for idx, (curlabel, curarray) in enumerate(linked_arrays.items()):
            if curarray.plotted:

                logging.info(_('Plotting linked polygons for {}'.format(curlabel)))
                logging.info(_('Number of polygons : {}'.format(self.nbvectors)))
                logging.info(_('Extracting values inside polygons...'))

                vals= [curarray.get_values_insidepoly(curpol) for curpol in self.myvectors]

                logging.info(_('Computing stats...'))

                values = np.asarray([cur[0] for cur in vals],dtype=object)
                valel  = np.asarray([cur[1] for cur in vals],dtype=object)

                zmaxloc=np.asarray([np.max(curval) if len(curval) >0 else -99999. for curval in values])
                zminloc=np.asarray([np.min(curval) if len(curval) >0 else -99999. for curval in values])

                zmax=max(zmax,np.max(zmaxloc[np.where(zmaxloc>-99999.)]))
                zmin=min(zmin,np.min(zminloc[np.where(zminloc>-99999.)]))

                if zmax>-99999:

                    zloc = np.asarray([np.median(curpoly) if len(curpoly) >0 else -99999. for curpoly in values])

                    ax.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                            color=colors[np.mod(k,3)],
                            lw=2.0,
                            linestyle=linestyle,
                            label=curlabel+'_median')

                    zloc = np.asarray([np.min(curpoly) if len(curpoly) >0 else -99999. for curpoly in values])

                    if not onlymedian:

                        ax.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                                color=colors[np.mod(k,3)],alpha=.3,
                                lw=2.0,
                                linestyle=linestyle,
                                label=curlabel+'_min')

                        zloc = np.asarray([np.max(curpoly) if len(curpoly) >0 else -99999. for curpoly in values])

                        ax.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                                color=colors[np.mod(k,3)],alpha=.3,
                                lw=2.0,
                                linestyle=linestyle,
                                label=curlabel+'_max')

                if withtopography and idx==0:
                    if valel[0] is not None:
                        zmaxloc=np.asarray([np.max(curval) if len(curval) >0 else -99999. for curval in valel])
                        zminloc=np.asarray([np.min(curval) if len(curval) >0 else -99999. for curval in valel])

                        zmax=max(zmax,np.max(zmaxloc[np.where(zmaxloc>-99999.)]))
                        zmin=min(zmin,np.min(zminloc[np.where(zminloc>-99999.)]))

                        if zmax>-99999:

                            zloc = np.asarray([np.median(curpoly) if len(curpoly) >0 else -99999. for curpoly in valel])

                            ax.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                                    color='black',
                                    lw=2.0,
                                    linestyle=linestyle,
                                    label=curlabel+'_top_median')

                        # if not onlymedian:
                            # zloc = np.asarray([np.min(curpoly) for curpoly in valel])

                            # ax.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                            #         color='black',alpha=.3,
                            #         lw=2.0,
                            #         linestyle=linestyle,
                            #         label=curlabel+'_top_min')

                            # zloc = np.asarray([np.max(curpoly) for curpoly in valel])

                            # ax.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                            #         color='black',alpha=.3,
                            #         lw=2.0,
                            #         linestyle=linestyle,
                            #         label=curlabel+'_top_max')

                k+=1

        for curlabel, curzones in linked_vec.items():
            curzones:Zones
            names = [curzone.myname for curzone in curzones.myzones]
            trace = None
            tracels = None

            logging.info(_('Plotting linked zones for {}'.format(curlabel)))

            curzone: zone
            if 'trace' in names:
                curzone = curzones.get_zone('trace')
                trace = curzone.get_vector('trace')

                if trace is None:
                    if curzone is not None:
                        if curzone.nbvectors>0:
                            trace = curzone.myvectors[0]

                if trace is not None:
                    tracels = trace.asshapely_ls()
                else:
                    logging.warning(_('No trace found in the vectors {}'.format(curlabel)))
                    break

            if ('marks' in names) or ('repères' in names):
                if ('marks' in names):
                    curzone = curzones.myzones[names.index('marks')]
                else:
                    curzone = curzones.myzones[names.index('repères')]

                logging.info(_('Plotting marks for {}'.format(curlabel)))
                logging.info(_('Number of marks : {}'.format(curzone.nbvectors)))

                for curvect in curzone.myvectors:
                    curls = curvect.asshapely_ls()

                    if curls.intersects(tracels):
                        inter = curls.intersection(tracels)
                        curs = float(tracels.project(inter))

                        ax.plot([curs, curs], [zmin, zmax], linestyle='--', label=curvect.myname)
                        ax.text(curs, zmax, curvect.myname, fontsize=8, ha='center', va='bottom')

            if ('banks' in names) or ('berges' in names):

                if ('banks' in names):
                    curzone = curzones.myzones[names.index('banks')]
                else:
                    curzone = curzones.myzones[names.index('berges')]

                logging.info(_('Plotting banks for {}'.format(curlabel)))
                logging.info(_('Number of banks : {}'.format(curzone.nbvectors)))

                for curvect in curzone.myvectors:
                    curvect: vector

                    curproj = curvect.projectontrace(trace)
                    sz = curproj.asnparray()
                    ax.plot(sz[:,0], sz[:,1], label=curvect.myname)

            if ('bridges' in names) or ('ponts' in names):
                if ('bridges' in names):
                    curzone = curzones.myzones[names.index('bridges')]
                else:
                    curzone = curzones.myzones[names.index('ponts')]

                logging.info(_('Plotting bridges for {}'.format(curlabel)))

                for curvect in curzone.myvectors:
                    curvect: vector
                    curls = curvect.asshapely_ls()

                    if curls.intersects(tracels):

                        logging.info(_('Bridge {} intersects the trace'.format(curvect.myname)))

                        inter = curls.intersection(tracels)
                        curs = float(tracels.project(inter))
                        locz = np.asarray([vert.z for vert in curvect.myvertices])
                        zmin = np.amin(locz)
                        zmax = np.amax(locz)

                        ax.scatter(curs, zmin, label=curvect.myname + ' min')
                        ax.scatter(curs, zmax, label=curvect.myname + ' max')

        ax.set_ylim(zmin,zmax)
        zmodmin= np.floor_divide(zmin*100,25)*25/100
        ax.set_yticks(np.arange(zmodmin,zmax,.25))
        fig.canvas.draw()

    def plot_linked_polygons_wx(self, fig:MplFig,
                             linked_arrays:dict, linked_vec:dict[str,"Zones"]=None,
                             linestyle:str='-', onlymedian:bool=False,
                             withtopography:bool = True, ds:float = None):
        """
        Création d'un graphique sur base des polygones

        Chaque polygone se positionnera sur base de la valeur Z de ses vertices
           - façon conventionnelle de définir une longueur
           - ceci est normalement fait lors de l'appel à 'create_polygon_from_parallel'
           - si les polygones sont créés manuellement, il faut donc prendre soin de fournir l'information adhoc ou alors utiliser l'rgument 'ds'

        ATTENTION : Les coordonnées Z ne sont sauvegardées sur disque que si le fichier est 3D, autrement dit au format '.vecz'

        :param fig: Figure
        :param ax: Axes
        :param linked_arrays: dictionnaire contenant les matrices à lier -- les clés sont les labels
        :param linked_vec: dictionnaire contenant les instances Zones à lier -- Besoin d'une zone et d'un vecteur 'trace/trace' pour convertir les positions en coordonnées curvilignes
        :param linestyle: style de ligne
        :param onlymedian: affiche uniquement la médiane
        :param withtopography: affiche la topographie
        :param ds: pas spatial le long de l'axe

        """

        colors=['red','blue','green','darkviolet','fuchsia','lime']

        #Vérifie qu'au moins une matrice liée est fournie, sinon rien à faire
        exit=True
        for curlabel, curarray in linked_arrays.items():
            if curarray.plotted:
                exit=False
        if exit:
            return

        k=0

        zmin=99999.
        zmax=-99999.

        if ds is None:
            # Récupération des positions
            srefs=np.asarray([curpol.myvertices[0].z for curpol in self.myvectors])
        else:
            # Création des positions sur base de 'ds'
            srefs=np.arange(0., float(self.nbvectors) * ds, ds)

        for idx, (curlabel, curarray) in enumerate(linked_arrays.items()):
            if curarray.plotted:

                logging.info(_('Plotting linked polygons for {}'.format(curlabel)))
                logging.info(_('Number of polygons : {}'.format(self.nbvectors)))
                logging.info(_('Extracting values inside polygons...'))

                vals= [curarray.get_values_insidepoly(curpol) for curpol in self.myvectors]

                logging.info(_('Computing stats...'))

                values = np.asarray([cur[0] for cur in vals],dtype=object)
                valel  = np.asarray([cur[1] for cur in vals],dtype=object)

                zmaxloc=np.asarray([np.max(curval) if len(curval) >0 else -99999. for curval in values])
                zminloc=np.asarray([np.min(curval) if len(curval) >0 else -99999. for curval in values])

                zmax=max(zmax,np.max(zmaxloc[np.where(zmaxloc>-99999.)]))
                zmin=min(zmin,np.min(zminloc[np.where(zminloc>-99999.)]))

                if zmax>-99999:

                    zloc = np.asarray([np.median(curpoly) if len(curpoly) >0 else -99999. for curpoly in values])

                    fig.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                            color=colors[np.mod(k,3)],
                            lw=2.0,
                            linestyle=linestyle,
                            label=curlabel+'_median')

                    zloc = np.asarray([np.min(curpoly) if len(curpoly) >0 else -99999. for curpoly in values])

                    if not onlymedian:

                        fig.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                                color=colors[np.mod(k,3)],alpha=.3,
                                lw=2.0,
                                linestyle=linestyle,
                                label=curlabel+'_min')

                        zloc = np.asarray([np.max(curpoly) if len(curpoly) >0 else -99999. for curpoly in values])

                        fig.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                                color=colors[np.mod(k,3)],alpha=.3,
                                lw=2.0,
                                linestyle=linestyle,
                                label=curlabel+'_max')

                if withtopography and idx==0:
                    if valel[0] is not None:
                        zmaxloc=np.asarray([np.max(curval) if len(curval) >0 else -99999. for curval in valel])
                        zminloc=np.asarray([np.min(curval) if len(curval) >0 else -99999. for curval in valel])

                        zmax=max(zmax,np.max(zmaxloc[np.where(zmaxloc>-99999.)]))
                        zmin=min(zmin,np.min(zminloc[np.where(zminloc>-99999.)]))

                        if zmax>-99999:

                            zloc = np.asarray([np.median(curpoly) if len(curpoly) >0 else -99999. for curpoly in valel])

                            fig.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                                    color='black',
                                    lw=2.0,
                                    linestyle=linestyle,
                                    label=curlabel+'_top_median')

                        # if not onlymedian:
                            # zloc = np.asarray([np.min(curpoly) for curpoly in valel])

                            # ax.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                            #         color='black',alpha=.3,
                            #         lw=2.0,
                            #         linestyle=linestyle,
                            #         label=curlabel+'_top_min')

                            # zloc = np.asarray([np.max(curpoly) for curpoly in valel])

                            # ax.plot(srefs[np.where(zloc!=-99999.)],zloc[np.where(zloc!=-99999.)],
                            #         color='black',alpha=.3,
                            #         lw=2.0,
                            #         linestyle=linestyle,
                            #         label=curlabel+'_top_max')

                k+=1

        for curlabel, curzones in linked_vec.items():
            curzones:Zones
            names = [curzone.myname for curzone in curzones.myzones]
            trace = None
            tracels = None

            logging.info(_('Plotting linked zones for {}'.format(curlabel)))

            curzone: zone
            if 'trace' in names:
                curzone = curzones.get_zone('trace')
                trace = curzone.get_vector('trace')

                if trace is None:
                    if curzone is not None:
                        if curzone.nbvectors>0:
                            trace = curzone.myvectors[0]

                if trace is not None:
                    tracels = trace.asshapely_ls()
                else:
                    logging.warning(_('No trace found in the vectors {}'.format(curlabel)))
                    break

            if ('marks' in names) or ('repères' in names):
                if ('marks' in names):
                    curzone = curzones.myzones[names.index('marks')]
                else:
                    curzone = curzones.myzones[names.index('repères')]

                logging.info(_('Plotting marks for {}'.format(curlabel)))
                logging.info(_('Number of marks : {}'.format(curzone.nbvectors)))

                for curvect in curzone.myvectors:
                    curls = curvect.asshapely_ls()

                    if curls.intersects(tracels):
                        inter = curls.intersection(tracels)
                        curs = float(tracels.project(inter))

                        fig.plot([curs, curs], [zmin, zmax], linestyle='--', label=curvect.myname)
                        fig.text(curs, zmax, curvect.myname, fontsize=8, ha='center', va='bottom')

            if ('banks' in names) or ('berges' in names):

                if ('banks' in names):
                    curzone = curzones.myzones[names.index('banks')]
                else:
                    curzone = curzones.myzones[names.index('berges')]

                logging.info(_('Plotting banks for {}'.format(curlabel)))
                logging.info(_('Number of banks : {}'.format(curzone.nbvectors)))

                for curvect in curzone.myvectors:
                    curvect: vector

                    curproj = curvect.projectontrace(trace)
                    sz = curproj.asnparray()
                    fig.plot(sz[:,0], sz[:,1], label=curvect.myname)

            if ('bridges' in names) or ('ponts' in names):
                if ('bridges' in names):
                    curzone = curzones.myzones[names.index('bridges')]
                else:
                    curzone = curzones.myzones[names.index('ponts')]

                logging.info(_('Plotting bridges for {}'.format(curlabel)))

                for curvect in curzone.myvectors:
                    curvect: vector
                    curls = curvect.asshapely_ls()

                    if curls.intersects(tracels):

                        logging.info(_('Bridge {} intersects the trace'.format(curvect.myname)))

                        inter = curls.intersection(tracels)
                        curs = float(tracels.project(inter))
                        locz = np.asarray([vert.z for vert in curvect.myvertices])
                        zmin = np.amin(locz)
                        zmax = np.amax(locz)

                        fig.plot(curs, zmin, label=curvect.myname + ' min', marker='x')
                        fig.plot(curs, zmax, label=curvect.myname + ' max', marker='x')

        fig.cur_ax.set_ylim(zmin,zmax)
        zmodmin= np.floor_divide(zmin*100,25)*25/100
        fig.cur_ax.set_yticks(np.arange(zmodmin,zmax,.25))

    def reset_listogl(self):
        """
        Reset OpenGL lists.

        Force deletion of the OpenGL list.
        If the object is newly plotted, the lists will be recreated.
        """

        if self.idgllist!=-99999:
            glDeleteLists(self.idgllist,1)
            self.idgllist=-99999

    def deepcopy_zone(self, name: str =None, parent: str= None) -> "zone":
        """ Return a deep copy of the zone"""

        if name is None:
            name =  self.myname + '_copy'

        if parent is not None:
            copied_zone = zone(name=name, parent=parent)
        else:
            copied_zone = zone(name=name)

        copied_zone.myvectors = []
        for vec in self.myvectors:
            copied_vec = vec.deepcopy_vector(parentzone = copied_zone)
            copied_zone.add_vector(copied_vec, forceparent=True)

        return copied_zone

    def deepcopy(self, name: str =None, parent: str= None) -> "zone":
        """ Return a deep copy of the zone"""

        return self.deepcopy_zone(name, parent)

    def show_properties(self):
        """ Show properties of the zone --> will be applied to all vectors int he zone """

        if self.myprops is None:
            locvec = vector()
            locvec.show_properties()
            self.myprops = locvec.myprop.myprops

        self.myprops[('Legend','X')] = str(99999.)
        self.myprops[('Legend','Y')] = str(99999.)
        self.myprops[('Legend','Text')] = _('Not used')

        if self._rotation_center is None:
            self.myprops[('Rotation','Center X')] = 99999.
            self.myprops[('Rotation','Center Y')] = 99999.
        else:
            self.myprops[('Rotation','Center X')] = self._rotation_center.x
            self.myprops[('Rotation','Center Y')] = self._rotation_center.y

        if self._rotation_step is None:
            self.myprops[('Rotation','Step [degree]')] = 99999.
        else:
            self.myprops[('Rotation','Step [degree]')] = self._rotation_step

        self.myprops[('Rotation', 'Angle [degree]')] = 0.

        if self._move_start is None:
            self.myprops[('Move','Start X')] = 99999.
            self.myprops[('Move','Start Y')] = 99999.
        else:
            self.myprops[('Move','Start X')] = self._move_start.x
            self.myprops[('Move','Start Y')] = self._move_start.y

        if self._move_step is None:
            self.myprops[('Move','Step [m]')] = 99999.
        else:
            self.myprops[('Move','Step [m]')] = self._move_step

        self.myprops[('Move', 'Delta X')] = 0.
        self.myprops[('Move', 'Delta Y')] = 0.

        self.myprops.Populate()
        self.myprops.set_callbacks(self._callback_prop, self._callback_destroy_props)

        self.myprops.SetTitle(_('Zone properties - {}'.format(self.myname)))
        self.myprops.Center()
        self.myprops.Raise()

    def hide_properties(self):
        """ Hide the properties window """

        if self.myprops is not None:
            # window for general properties
            self.myprops.Hide()

        for curvect in self.myvectors:
            curvect.hide_properties()


    def _callback_destroy_props(self):
        """ Callback to destroy the properties window """

        if self.myprops is not None:
            self.myprops.Destroy()

        self.myprops = None

    def _callback_prop(self):
        """ Callback to update properties """

        if self.myprops is None:
            logging.warning(_('No properties available'))
            return

        for curvec in self.myvectors:
            curvec.myprop.fill_property(self.myprops, updateOGL = False)

        angle = self.myprops[('Rotation', 'Angle [degree]')]
        dx = self.myprops[('Move', 'Delta X')]
        dy = self.myprops[('Move', 'Delta Y')]

        if angle!=0. and (dx!=0. or dy!=0.):
            logging.warning(_('Rotation and translation are not compatible'))
            return
        elif angle!=0.:
            if self._rotation_center is None:
                logging.warning(_('No rotation center defined'))
                return
            else:
                self.rotate(angle, self._rotation_center)
                self.clear_cache()
        elif dx!=0. or dy!=0.:
            self.move(dx, dy)
            self.clear_cache()

        if self.parent.mapviewer is not None:
            self.prep_listogl()
            self.parent.mapviewer.Refresh()

    def set_legend_to_centroid(self):
        """
        Set the legend to the centroid of the vectors
        """
        list(map(lambda curvec: curvec.set_legend_to_centroid(), self.myvectors))

    def set_legend_visible(self, visible:bool=True):
        """
        Set the visibility of the legend for all vectors in the zone
        """
        list(map(lambda curvec: curvec.set_legend_visible(visible), self.myvectors))

class Zones(wx.Frame, Element_To_Draw):
    """
    Objet de gestion d'informations vectorielles

    Une instance 'Zones' contient une liste de 'zone'

    Une instance 'zone' contient une listde de 'vector' (segment, ligne, polyligne, polygone...)
    """

    tx:float
    ty:float

    # nbzones:int

    myzones:list[zone]
    treelist:TreeListCtrl
    xls:CpGrid

    def __init__(self,
                 filename:Union[str, Path]='',
                 ox:float=0.,
                 oy:float=0.,
                 tx:float=0.,
                 ty:float=0.,
                 parent=None,
                 is2D=True,
                 idx: str = '',
                 colname: str = None,
                 plotted: bool = True,
                 mapviewer=None,
                 need_for_wx: bool = False,
                 bbox:Polygon = None,
                 find_minmax:bool = True,
                 shared:bool = False,
                 colors:dict = None) -> None:
        """
        Objet de gestion et d'affichage d'informations vectorielles

        :param filename: nom du fichier à lire
        :param ox: origine X
        :param oy: origine Y
        :param tx: Translation selon X
        :param ty: Translation selon Y
        :param parent: objet parent -- soit une instance 'WolfMapViewer', soit une instance 'Ops_Array' --> est utile pour transférer la propriété 'active_vector' et obtenir diverses informations ou lancer des actions
        :param is2D: si True --> les vecteurs sont en 2D
        :param idx: identifiant
        :param plotted: si True --> les vecteurs sont prêts à être affichés
        :param mapviewer: instance WolfMapViewer
        :param need_for_wx: si True --> permet l'affichage de la structure via WX car une app WX existe et est en cours d'exécution
        :param bbox: bounding box
        :param find_minmax: si True --> recherche des valeurs min et max
        :param shared: si True --> les vecteurs sont partagés entre plusieurs autres objets --> pas de préparation de la liste OGL

        wx_exists : si True --> permet l'affichage de la structure via WX car une app WX existe et est en cours d'exécution

        Si wx_exists alors on cherche une instance WolfMapViewer depuis le 'parent' --> set_mapviewer()
        Dans ce cas, le parent doit posséder une routine du type 'get_mapviewer()'

        Exemple :

        def get_mapviewer(self):
            # Retourne une instance WolfMapViewer
            return self.mapviewer
        """

        Element_To_Draw.__init__(self, idx, plotted, mapviewer, need_for_wx)

        self._myprops = None # common properties of all zones

        self.loaded=True
        self.shared = shared # shared betwwen several WolfArray, wolfresults2d...

        self.active_vector:vector = None
        self.active_zone:zone = None
        self.last_active = None # dernier élément activé dans le treelist

        self.force3D=False
        self.is2D=is2D

        self.filename=str(filename)

        self.parent = parent        # objet parent (PyDraw, OpsArray, Wolf2DModel...)

        self.wx_exists = wx.App.Get() is not None
        self.xls = None
        self.labelactvect = None
        self.labelactzone = None

        if self.wx_exists:

            self.set_mapviewer()

            try:
                super(Zones, self).__init__(None, size=(400, 400))
                self.Bind(wx.EVT_CLOSE,self.OnClose) # on lie la procédure de fermeture de façon à juste masquer le Frame et non le détruire
            except:
                raise Warning(_('Bad wx context -- see Zones.__init__'))

        self.init_struct=True # il faudra initialiser la structure dans showstructure lors du premier appel

        self.xmin=ox
        self.ymin=oy

        self._first_find_minmax:bool = True

        self.tx=tx
        self.ty=ty
        self.myzones=[]

        self._move_start = None
        self._move_step = None
        self._rotation_center = None
        self._rotation_step = None

        only_firstlast = False # By default, we are using all vertices
        if self.filename!='':
            # lecture du fichier

            # Check if fname is an url
            _filename = str(self.filename).strip()
            if _filename.startswith('http:') or _filename.startswith('https:'):
                try:
                    self.filename = str(download_file(_filename))
                except Exception as e:
                    logging.error(_('Error while downloading file: %s') % e)
                    return

            if self.filename.endswith('.dxf'):
                self.is2D=False
                self.import_dxf(self.filename)
                only_firstlast = True # We limit the number of vertices to the first and last ones to accelerate the process

            elif self.filename.endswith('.shp'):
                self.is2D=False
                self.import_shapefile(self.filename, bbox=bbox, colname=colname)
                only_firstlast = True # We limit the number of vertices to the first and last ones to accelerate the process

            elif self.filename.endswith('.gpkg'):
                self.is2D=False
                self.import_gpkg(self.filename, bbox=bbox)
                only_firstlast = True # We limit the number of vertices to the first and last ones to accelerate the process

            elif Path(filename).is_dir() and self.filename.endswith('.gdb'):
                self.is2D=False
                self.import_gdb(self.filename, bbox=bbox)
                only_firstlast = True # We limit the number of vertices to the first and last ones to accelerate the process

            elif self.filename.endswith('.vec') or self.filename.endswith('.vecz'):

                if self.filename.endswith('.vecz'):
                    self.is2D=False

                f = open(self.filename, 'r')
                lines = f.read().splitlines()
                f.close()

                try:
                    tx,ty=lines[0].split()
                except:
                    tx,ty=lines[0].split(',')

                self.tx=float(tx)
                self.ty=float(ty)
                tmp_nbzones=int(lines[1])

                curstart=2
                for i in range(tmp_nbzones):
                    curzone=zone(lines[curstart:],parent=self,is2D=self.is2D)
                    self.myzones.append(curzone)
                    curstart+=curzone._nblines()

                if Path(self.filename + '.extra').exists():
                    # lecture des propriétés "extra"
                    with open(self.filename + '.extra', 'r') as f:
                        lines = f.read().splitlines()

                    try:
                        nblines = len(lines)
                        i=0
                        idx_zone = 0
                        while i<nblines:
                            curzone = self.myzones[idx_zone]
                            assert curzone.myname == lines[i], _('Error while reading extra properties of {}'.format(self.filename))
                            i+=1
                            ret = curzone.load_extra(lines[i:])
                            i+=ret
                            idx_zone += 1
                    except:
                        logging.warning(_('Error while reading extra properties of {}'.format(self.filename)))

            if find_minmax:
                logging.info(_('Finding min and max values'))
                self.find_minmax(True, only_firstlast)

        if colors is not None:
            self.colorize_data(colors, filled=True)

        if plotted and self.has_OGLContext and not self.shared:
            logging.debug(_('Preparing OpenGL lists'))
            self.prep_listogl()
            logging.debug(_('OpenGL lists ready'))

    @property
    def mynames(self) -> list[str]:
        """ Return the names of all zones """

        return [curzone.myname for curzone in self.myzones]

    def check_if_interior_exists(self):
        """ Check if the zone has at least one vector with interior points """
        for curzone in self.myzones:
            curzone.check_if_interior_exists()

    def add_values(self, key:str, values:np.ndarray | dict):
        """
        Add values to the zones
        """

        if isinstance(values, dict):
            for k, val in values.items():
                if not isinstance(val, np.ndarray):
                    val = np.asarray(val)

                if k in self.mynames:
                    self[k].add_values(key, val)

        elif isinstance(values, np.ndarray):
            if values.shape[0] != self.nbzones:
                logging.warning(_('Number of values does not match the number of zones'))
                return

            for idx, curzone in enumerate(self.myzones):
                curzone.add_values(key, values[idx])

    def get_values(self, key:str) -> np.ndarray:
        """
        Get values from the zones
        """

        return np.asarray([curzone.get_values(key) for curzone in self.myzones])

    def set_colors_from_value(self, key:str, cmap:wolfpalette | str | Colormap | cm.ScalarMappable, vmin:float = 0., vmax:float = 1.):
        """
        Set colors to the zones
        """

        if isinstance(cmap, str):
            cmap = cm.get_cmap(cmap)

        for curzone in self.myzones:
            curzone.set_colors_from_value(key, cmap, vmin, vmax)

    def set_alpha(self, alpha:int):
        """
        Set alpha to the zones
        """

        for curzone in self.myzones:
            curzone.set_alpha(alpha)

    def set_filled(self, filled:bool):
        """
        Set filled to the zones
        """

        for curzone in self.myzones:
            curzone.set_filled(filled)

    def check_if_open(self):
        """ Check if the vectors in the zone are open """
        for curzone in self.myzones:
            curzone.check_if_open()

    def concatenate_all_vectors(self) -> list[vector]:
        """ Concatenate all vectors in the zones """
        ret = []
        for curzone in self.myzones:
            ret.extend(curzone.myvectors)
        return ret

    def prepare_shapely(self):
        """ Prepare shapely objects for all vectors in zones """
        allvec = self.concatenate_all_vectors()
        list(map(lambda x: x.prepare_shapely(True), allvec))

    def filter_contains(self, others:list[vector]) -> "Zones":
        """ Create a new "Zones" instance with
        vectors in 'others' contained in the zones """

        if isinstance(others, Zones):
            allvec = others.concatenate_all_vectors()
        elif isinstance(others, list):
            allvec = others
        else:
            logging.warning(_('Unknown type for others'))
            return None

        centroids = [curvec.centroid for curvec in allvec]
        newzones = Zones()

        for curzone in self.myzones:
            if curzone.nbvectors != 1:
                logging.warning(_('Zone {} has more than one vector'.format(curzone.myname)))
                continue

            poly = curzone[0].polygon
            # element-wise comparison
            contains = list(map(lambda x: poly.contains(x), centroids))

            newzone = zone(name=curzone.myname, parent=newzones)
            newzone.myvectors = list(map(lambda x: allvec[x], np.where(contains)[0]))
            newzones.add_zone(newzone, forceparent=True)

        return newzones

    @property
    def areas(self):
        """ List of areas of all zones """

        return [curzone.areas for curzone in self.myzones]

    def buffer(self, distance:float, resolution:int = 16, inplace:bool = True):
        """ Buffer all zones """

        if inplace:
            newzones = self
        else:
            newzones = Zones()

        retmap = list(map(lambda x: x.buffer(distance, resolution, inplace=inplace), self.myzones))

        for curzone in retmap:
            newzones.add_zone(curzone, forceparent=True)

        newzones.find_minmax(True)
        if inplace:
            return self

        return newzones

    def set_cache(self):
        """ Set cache for all zones """

        for curzone in self.myzones:
            curzone.set_cache()

    def clear_cache(self):
        """ Clear cache for all zones """

        for curzone in self.myzones:
            curzone.clear_cache()

    def move(self, dx:float, dy:float, use_cache:bool = True, inplace:bool = True):
        """ Move all zones """

        if self._move_step is not None:
            dx = np.round(dx/self._move_step)*self._move_step
            dy = np.round(dy/self._move_step)*self._move_step

        if inplace:
            for curzone in self.myzones:
                curzone.move(dx, dy, use_cache=use_cache, inplace=inplace)

            return self

        else:
            newzones = self.deepcopy_zones()
            newzones.move(dx, dy, use_cache=False, inplace=True)
            newzones.find_minmax(True)
            return newzones

    def rotate(self, angle:float, center:Point = None, use_cache:bool = True, inplace:bool = True):
        """ Rotate all zones """

        if self._rotation_step is not None:
            angle = np.round(angle/self._rotation_step)*self._rotation_step

        if inplace:
            for curzone in self.myzones:
                curzone.rotate(angle, center, use_cache=use_cache, inplace=inplace)

            return self

        else:
            newzones = self.deepcopy_zones()
            newzones.rotate(angle, center, use_cache=False, inplace=True)
            newzones.find_minmax(True)
            return newzones

    def rotate_xy(self, angle:float, center:Point = None, use_cache:bool = True, inplace:bool = True):
        """ Rotate all zones """

        if inplace:
            for curzone in self.myzones:
                curzone.rotate_xy(angle, center, use_cache=use_cache, inplace=inplace)

            return self

        else:
            newzones = self.deepcopy_zones()
            newzones.rotate_xy(angle, center, use_cache=False, inplace=True)
            newzones.find_minmax(True)
            return newzones

    def force_unique_zone_name(self):
        """
        Check if all zones have a unique id

        If not, the id will be set to the index of the zone in the list
        """

        names = [curzone.myname for curzone in self.myzones]
        unique_names = set(names)

        if len(unique_names) != len(names):
            for idx, curzone in enumerate(self.myzones):
                if names.count(curzone.myname)>1:
                    curzone.myname += '_'+str(idx)

    def set_legend_text(self, text:str):
        """
        Set the legend text for the zones
        """

        for curzone in self.myzones:
            curzone.set_legend_text(text)

    def set_legend_text_from_values(self, key:str):
        """
        Set the legend text for the zones from the values
        """

        for curzone in self.myzones:
            curzone.set_legend_text_from_values(key)

    def set_legend_to_centroid(self):
        """
        Set the legend to the centroid of the zones
        """

        for curzone in self.myzones:
            curzone.set_legend_to_centroid()

    def set_legend_position(self, x, y):
        """
        Set the legend position for the zones
        """

        for curzone in self.myzones:
            curzone.set_legend_position(x, y)

    @property
    def nbzones(self):
        return len(self.myzones)

    def import_shapefile(self, fn:str,
                         bbox:Polygon = None, colname:str = None):
        """
        Import shapefile by using geopandas

        Shapefile == 1 zone

        """

        logging.info(_('Importing shapefile {}'.format(fn)))
        content = gpd.read_file(fn, bbox=bbox)

        self.import_GeoDataFrame(content=content, colname=colname)


    def import_GeoDataFrame(self, content:gpd.GeoDataFrame,
                            bbox:Polygon = None, colname:str = None):
        """
        Import a GeoDataFrame geopandas

        Shapefile == 1 zone
        """

        logging.info(_('Importing GeoDataFrame'))

        if bbox is not None:
            # filter content
            content = content.cx[bbox.bounds[0]:bbox.bounds[2], bbox.bounds[1]:bbox.bounds[3]]

        logging.info(_('Converting DataFrame into zones'))
        if colname is not None and colname not in content.columns:
            logging.warning(_('Column {} not found in the DataFrame'.format(colname)))
            logging.info(_('We are using the available known columns'))
            colname = ''

        def add_zone_from_row(row):
            idx, row = row
            keys = list(row.keys())
            if colname in keys:
                name = str(row[colname])
            elif 'NAME' in keys:
                name = str(row['NAME'])
            elif 'location' in keys:
                name = str(row['location']) # tuilage gdal
            elif 'Communes' in keys:
                name = str(row['Communes'])
            elif 'name' in keys:
                name = str(row['name'])
            elif 'MAJ_NIV3T' in keys:
                # WALOUS
                name = str(row['MAJ_NIV3T'])
            elif 'NATUR_DESC' in keys:
                name = str(row['NATUR_DESC'])
            elif 'mun_name_f' in keys:
                name = str(row['mun_name_f']).replace('[','').replace(']','').replace("'",'')
            elif 'mun_name_fr' in keys:
                name = str(row['mun_name_fr'])
            else:
                name = str(idx)

            poly = row['geometry']

            newzone = zone(name=name, parent = self, fromshapely = poly)
            return newzone

        self.myzones = list(map(add_zone_from_row, content.iterrows()))

        pass

    def export_GeoDataFrame(self) -> gpd.GeoDataFrame:
        """
        Export to a GeoDataFrame
        """
        names=[]
        geoms=[]

        # One zone is a polygon
        for curzone in self.myzones:
            if curzone.nbvectors == 0:
                logging.warning(_('Zone {} contains no vector'.format(curzone.myname)))
                continue

            elif curzone.nbvectors>1:
                logging.warning(_('Zone {} contains more than one vector -- only the first one will be exported'.format(curzone.myname)))

            names.append(curzone.myname)
            for curvect in curzone.myvectors[:1]:
                if curvect.is2D:
                    if curvect.closed:
                        geoms.append(curvect.polygon)
                    else:
                        geoms.append(curvect.polygon)
                else:
                    if curvect.closed:
                        geoms.append(curvect.asshapely_pol3D())
                    else:
                        geoms.append(curvect.asshapely_ls3d())

        gdf = gpd.GeoDataFrame({'id':names,'geometry':geoms})
        gdf.crs = 'EPSG:31370'

        return gdf

    def export_to_shapefile(self, filename:str):
        """
        Export to shapefile.

        The first vector of each zone will be exported.

        If you want to export all vectors, you have to use "export_shape" of the zone object.

        FIXME: Add support of data fields
        """

        gdf = self.export_GeoDataFrame()
        gdf.to_file(filename)

    def export_active_zone_to_shapefile(self, filename:str):
        """
        Export the active_zone to shapefile.
        """

        if self.active_zone is None:
            logging.warning(_('No active zone'))
            return

        self.active_zone.export_shape(filename)

    def import_gdb(self, fn:str, bbox:Polygon = None):
        """ Import gdb by using geopandas and Fiona"""

        import fiona

        layers = fiona.listlayers(fn)

        if self.wx_exists:
            dlg = wx.MultiChoiceDialog(None, _('Choose the layers to import'), _('Choose the layers'), layers)

            if dlg.ShowModal() == wx.ID_OK:
                layers = [layers[i] for i in dlg.GetSelections()]
            else:
                return

        for curlayer in layers:

            content = gpd.read_file(fn, bbox=bbox, layer=curlayer)

            if len(content)>1000:
                logging.warning(_('Layer {} contains more than 1000 elements -- it may take a while to import'.format(curlayer)))

            for idx, row in content.iterrows():
                if 'NAME' in row.keys():
                    name = row['NAME']
                elif 'MAJ_NIV3T' in row.keys():
                    # WALOUS
                    name = row['MAJ_NIV3T']
                elif 'NATUR_DESC' in row.keys():
                    name = row['NATUR_DESC']
                else:
                    name = str(idx)

                poly = row['geometry']

                newzone = zone(name=name, parent = self, fromshapely = poly)
                self.add_zone(newzone)

                if len(content)>1000:
                    if idx%100==0:
                        logging.info(_('Imported {} elements'.format(idx)))

    def import_gpkg(self, fn:str, bbox:Polygon = None):
        """ Import gdb by using geopandas and Fiona"""

        import fiona

        layers = fiona.listlayers(fn)

        if self.wx_exists:
            dlg = wx.MultiChoiceDialog(None, _('Choose the layers to import'), _('Choose the layers'), layers)

            if dlg.ShowModal() == wx.ID_OK:
                layers = [layers[i] for i in dlg.GetSelections()]
            else:
                return

        for curlayer in layers:

            content = gpd.read_file(fn, bbox=bbox, layer=curlayer)

            if len(content)>1000:
                logging.warning(_('Number of elements in layer {} : {}'.format(curlayer, len(content))))
                logging.warning(_('Layer {} contains more than 1000 elements -- it may take a while to import'.format(curlayer)))

                if self.wx_exists:
                    dlg = wx.MessageDialog(None, _('Layer {} contains more than 1000 elements -- it may take a while to import\n\nContinue ?'.format(curlayer)), _('Warning'), wx.OK | wx.CANCEL | wx.ICON_WARNING)
                    ret = dlg.ShowModal()
                    dlg.Destroy()
                    if ret == wx.ID_CANCEL:
                        return

            for idx, row in content.iterrows():
                if 'NAME' in row.keys():
                    name = row['NAME']
                elif 'CANU' in row.keys():
                    name = row['CANU']
                elif 'MAJ_NIV3T' in row.keys():
                    # WALOUS
                    name = row['MAJ_NIV3T']
                elif 'NATUR_DESC' in row.keys():
                    name = row['NATUR_DESC']
                elif 'Type' in row.keys():
                    name = row['Type']
                else:
                    name = str(idx)

                poly = row['geometry']

                newzone = zone(name=name, parent = self, fromshapely = poly)
                self.add_zone(newzone)

                if len(content)>1000:
                    if idx%100==0:
                        logging.info(_('Imported {} elements'.format(idx)))

    def set_mapviewer(self):
        """ Recherche d'une instance WolfMapViewer depuis le parent """
        from .PyDraw import WolfMapViewer

        if self.parent is None:
            # Nothing to do because 'parent' is None
            return

        try:
            self.mapviewer = self.parent.get_mapviewer()
        except:
            self.mapviewer = None

            assert isinstance(self.mapviewer, WolfMapViewer), _('Bad mapviewer -- verify your code or bad parent')

    def colorize_data(self, colors:dict[str:list[int]], filled:bool = False) -> None:
        """
        Colorize zones based on a dictionary of colors

        Zone's name must be the key of the dictionary

        """

        std_color = getIfromRGB([10, 10, 10])

        for curzone in self.myzones:
            if curzone.myname in colors:
                curcolor = getIfromRGB(colors[curzone.myname])
            else:
                curcolor = std_color

            for curvect in curzone.myvectors:
                curvect.myprop.color = curcolor
                curvect.myprop.alpha = 180
                curvect.myprop.transparent = True
                curvect.myprop.filled = filled and curvect.closed

    def set_width(self, width:int) -> None:
        """ Change with of all vectors in all zones """
        for curzone in self.myzones:
            for curvect in curzone.myvectors:
                curvect.myprop.width = width

        self.prep_listogl()

    def get_zone(self,keyzone:Union[int, str])->zone:
        """
        Retrouve la zone sur base de son nom ou de sa position
        Si plusieurs zones portent le même nom, seule la première est retournée
        """
        if isinstance(keyzone,int):
            if keyzone<self.nbzones:
                return self.myzones[keyzone]
            return None
        if isinstance(keyzone,str):
            zone_names = [cur.myname for cur in self.myzones]
            if keyzone in zone_names:
                return self.myzones[zone_names.index(keyzone)]
            return None

    def __getitem__(self, ndx:Union[int, str, tuple]) -> Union[zone, vector]:
        """
        Retourne la zone sur base de son nom ou de sa position

        :param ndx: Clé ou index de zone -- si tuple, alors (idx_zone, idx_vect) ou (keyzone, keyvect)

        """

        if isinstance(ndx,tuple):
            idx_zone = ndx[0]
            idx_vect = ndx[1]

            return self.get_zone(idx_zone)[idx_vect]
        else:
            return self.get_zone(ndx)

    @property
    def zone_names(self) -> list[str]:
        """ Return the list of zone names """
        return [cur.myname for cur in self.myzones]

    def import_dxf(self, fn, imported_elts=['POLYLINE','LWPOLYLINE','LINE']):
        """
        Import of a DXF file as a 'Zones'.

        The DXF file is read and the elements are stored in zones based on their layers.

        The supported elements are POLYLINE, LWPOLYLINE and LINE.
        If you want to import other elements, you must upgrade this routine `import_dxf`.

        :param fn: name of the DXF file to import
        :param imported_elts: list of DXF elements to import. Default is ['POLYLINE','LWPOLYLINE','LINE'].
        :return: None
        """
        import ezdxf

        if not path.exists(fn):
            logging.warning(_('File not found !') + ' ' + fn)
            return

        for elt in imported_elts:
            assert elt in ['POLYLINE', 'LWPOLYLINE', 'LINE'], _('Unsupported DXF element: {}').format(elt)

        self.is2D = False # we assume it's a 3D DXF

        # Lecture du fichier dxf et identification du modelspace
        doc = ezdxf.readfile(fn)
        msp = doc.modelspace()
        # layers = doc.layers

        used_layers = {}
        notloaded = {}

        # Bouclage sur les éléments du DXF pour identifier les layers utiles et ensuite créer les zones adhoc
        for e in msp:
            if doc.layers.get(e.dxf.layer).is_on():
                if e.dxftype() in imported_elts:
                    if e.dxftype() == "POLYLINE":
                        if e.dxf.layer not in used_layers.keys():
                            curlayer = used_layers[e.dxf.layer]={}
                        else:
                            curlayer = used_layers[e.dxf.layer]
                        curlayer[e.dxftype().lower()]=0

                    elif e.dxftype() == "LWPOLYLINE":
                        if e.dxf.layer not in used_layers.keys():
                            curlayer = used_layers[e.dxf.layer]={}
                        else:
                            curlayer = used_layers[e.dxf.layer]
                        curlayer[e.dxftype().lower()]=0

                    elif e.dxftype() == "LINE": # dans ce cas spécifique, ce sont a priori les lignes composant les croix sur les points levés
                        if e.dxf.layer not in used_layers.keys():
                            curlayer = used_layers[e.dxf.layer]={}
                        else:
                            curlayer = used_layers[e.dxf.layer]
                        curlayer[e.dxftype().lower()]=0
                else:
                    if not e.dxftype() in notloaded.keys():
                        notloaded[e.dxftype()] = 0

                    notloaded[e.dxftype()] += 1
                    logging.debug(_('DXF element not supported : ') + e.dxftype())
            else:
                logging.info(_('Layer {} is off'.format(e.dxf.layer)))

        if len(notloaded)>0:
            logging.warning(_('Not loaded DXF elements : '))
            for curtype in notloaded.keys():
                logging.warning(_('  {} : {}'.format(curtype, notloaded[curtype])))

        # Création des zones
        for curlayer in used_layers.keys():
            for curtype in used_layers[curlayer].keys():
                curzone = used_layers[curlayer][curtype] = zone(name = '{} - {}'.format(curlayer,curtype), is2D=self.is2D, parent=self)
                self.add_zone(curzone)

        # Nouveau bouclage sur les éléments du DXF pour remplissage
        nbid=0
        for e in msp:
            if doc.layers.get(e.dxf.layer).is_on():

                if e.dxftype() == "POLYLINE":
                    nbid+=1
                    # récupération des coordonnées
                    verts = [cur.dxf.location.xyz for cur in e.vertices]

                    curzone = used_layers[e.dxf.layer][e.dxftype().lower()]

                    curpoly = vector(is2D=False,name=e.dxf.handle,parentzone=curzone)
                    curzone.add_vector(curpoly)

                    for cur in verts:
                        myvert = wolfvertex(cur[0],cur[1],cur[2])
                        curpoly.add_vertex(myvert)

                elif e.dxftype() == "LWPOLYLINE":
                    nbid+=1
                    # récupération des coordonnées
                    verts = np.array(e.lwpoints.values)
                    verts = verts.reshape([verts.size // 5,5])[:,:2]   #  in ezdxf 1.3.5, the lwpoints.values attribute is a np.ndarray [n,5]
                    # verts = verts.reshape([len(verts) // 5,5])[:,:2] #  in ezdxf 1.2.0, the lwpoints.values attribute was flattened
                    verts = np.column_stack([verts,[e.dxf.elevation]*len(verts)])

                    curzone = used_layers[e.dxf.layer][e.dxftype().lower()]

                    curpoly = vector(is2D=False,name=e.dxf.handle,parentzone=curzone)
                    curzone.add_vector(curpoly)
                    for cur in verts:
                        myvert = wolfvertex(cur[0],cur[1],cur[2])
                        curpoly.add_vertex(myvert)

                elif e.dxftype() == "LINE":
                    nbid+=1

                    curzone = used_layers[e.dxf.layer][e.dxftype().lower()]

                    curpoly = vector(is2D=False,name=e.dxf.handle,parentzone=curzone)
                    curzone.add_vector(curpoly)

                    # récupération des coordonnées
                    myvert = wolfvertex(e.dxf.start[0],e.dxf.start[1],e.dxf.start[2])
                    curpoly.add_vertex(myvert)
                    myvert = wolfvertex(e.dxf.end[0],e.dxf.end[1],e.dxf.end[2])
                    curpoly.add_vertex(myvert)

        logging.info(_('Number of imported elements : ')+str(nbid))

    def find_nearest_vector(self, x:float, y:float) -> vector:
        """
        Trouve le vecteur le plus proche de la coordonnée (x,y)
        """
        xy=Point(x,y)

        distmin=99999.
        minvec=None
        curzone:zone
        for curzone in self.myzones:
            curvect:vector
            for curvect in curzone.myvectors:
                mynp = curvect.asnparray()
                mp = MultiPoint(mynp)
                near = nearest_points(mp,xy)[0]
                dist = xy.distance(near)
                if dist < distmin:
                    minvec=curvect
                    distmin=dist

        return minvec

    def find_vector_containing_point(self, x:float, y:float) -> vector:
        """ Trouve le prmier vecteur contenant le point (x,y) """
        xy = Point(x, y)
        for curzone in self.myzones:
            for curvect in curzone.myvectors:
                if curvect.polygon.contains(xy):
                    return curvect

    def reset_listogl(self):
        """
        Reset des listes OpenGL pour toutes les zones
        """
        for curzone in self.myzones:
            curzone.reset_listogl()

    def prep_listogl(self):
        """
        Préparation des listes OpenGL pour augmenter la vitesse d'affichage
        """

        try:
            for curzone in self.myzones:
                curzone.prep_listogl()
        except:
            logging.warning(_('Error while preparing OpenGL lists'))

    def check_plot(self):
        """
        L'objet doit être affiché

        Fonction principalement utile pour l'objet WolfMapViewer et le GUI
        """
        self.plotted = True

    def uncheck_plot(self, unload=True):
        """
        L'objet ne doit pas être affiché

        Fonction principalement utile pour l'objet WolfMapViewer et le GUI
        """
        self.plotted = False

    def save(self):
        """
        Sauvegarde sur disque, sans remise en cause du nom de fichier
        """
        if self.filename =='':
            logging.warning(_('No filename defined'))
            return

        self.saveas()

    def saveas(self, filename:str=''):
        """
        Sauvegarde sur disque

        filename : chemin d'accès potentiellement différent de self.filename

        si c'est le cas, self.filename est modifié
        """

        filename = str(filename)

        if filename!='':
            self.filename=filename

        if self.filename.endswith('.shp'):
            self.export_to_shapefile(self.filename)

        else:
            if self.filename.endswith('.vecz'):
                self.force3D=True #on veut un fichier 3D --> forcage du paramètre

            with open(self.filename, 'w') as f:
                f.write(f'{self.tx} {self.ty}'+'\n')
                f.write(str(self.nbzones)+'\n')
                for curzone in self.myzones:
                    curzone.save(f)

            with open(self.filename + '.extra', 'w') as f:
                for curzone in self.myzones:
                    curzone.save_extra(f)

    def OnClose(self, e):
        """
        Fermeture de la fenêtre
        """
        if self.wx_exists:
            self.Hide()

    def add_zone(self, addedzone:zone, forceparent=False):
        """
        Ajout d'une zone à la liste
        """
        self.myzones.append(addedzone)

        if forceparent:
            addedzone.parent = self

    def create_zone(self, name:str = '') -> zone:
        """ Create a new zone and add it to the list of zones """
        newzone = zone(name=name, parent=self, is2D=self.is2D)
        self.myzones.append(newzone)
        return newzone

    def find_minmax(self, update=False, only_firstlast:bool=False):
        """
        Trouve les bornes des vertices pour toutes les zones et tous les vecteurs

        :param update : si True, force la MAJ des minmax dans chaque zone; si False, compile les minmax déjà présents
        :param only_firstlast : si True, ne prend en compte que le premier et le dernier vertex de chaque vecteur
        """

        if self.nbzones > 100:
            with ThreadPoolExecutor() as executor:
                # zone.find_minmax(update or self._first_find_minmax, only_firstlast)
                futures = [executor.submit(zone.find_minmax, update or self._first_find_minmax, only_firstlast) for zone in self.myzones]
                wait(futures)
        else:
            for curzone in self.myzones:
                curzone.find_minmax(update or self._first_find_minmax, only_firstlast)

        if self.nbzones > 0:

            minsx = np.asarray([zone.xmin for zone in self.myzones if zone.xmin!=-99999.])
            minsy = np.asarray([zone.ymin for zone in self.myzones if zone.ymin!=-99999.])
            maxsx = np.asarray([zone.xmax for zone in self.myzones if zone.xmax!=-99999.])
            maxsy = np.asarray([zone.ymax for zone in self.myzones if zone.ymax!=-99999.])

            if minsx.size == 0:
                self.xmin = 0.
                self.ymin = 0.
                self.xmax = 1.
                self.ymax = 1.
            else:
                self.xmin = minsx.min()
                self.xmax = maxsx.max()
                self.ymin = minsy.min()
                self.ymax = maxsy.max()

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Dessine les zones
        """
        for curzone in self.myzones:
            curzone.plot(sx=sx, sy=sy, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, size=size)

    def plot_matplotlib(self, ax:Axes | tuple[Figure, Axes] = None):
        """ Plot with matplotlib """

        if isinstance(ax, tuple):
            fig, ax = ax
        elif ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        for curzone in self.myzones:
            curzone.plot_matplotlib(ax)

        return fig, ax

    def select_vectors_from_point(self, x:float, y:float, inside=True):
        """
        Sélection de vecteurs dans chaque zones sur base d'une coordonnée
          --> remplit la liste 'selected_vectors' de chaque zone

        inside : si True, teste si le point est contenu dans le polygone; si False, sélectionne le vecteur le plus proche
        """
        xmin=1e30
        for curzone in self.myzones:
            xmin = curzone.select_vectors_from_point(x,y,inside)

    def show_properties(self, parent=None, forceupdate=False):
        """
        Affichage des propriétés des zones

        :param parent: soit une instance 'WolfMapViewer', soit une instance 'Ops_Array'  --> est utile pour transférer la propriété 'active_vector' et obtenir diverses informations
                       si parent est d'un autre type, il faut s'assurer que les options/actions sont consistantes
        :param forceupdate: si True, on force la mise à jour de la structure

        """
        self.showstructure(parent, forceupdate)

    def hide_properties(self):
        """ Hide the properties window """

        self.Hide()

        if self._myprops is not None:
            self._myprops.Hide()

        for curzone in self.myzones:
            curzone.hide_properties()

    def showstructure(self, parent=None, forceupdate=False):
        """
        Affichage de la structure des zones

        :param parent: soit une instance 'WolfMapViewer', soit une instance 'Ops_Array'  --> est utile pour transférer la propriété 'active_vector' et obtenir diverses informations
                        si parent est d'un autre type, il faut s'assurer que les options/actions sont consistantes
        :param forceupdate: si True, on force la mise à jour de la structure

        """
        if self.parent is None:
            self.parent = parent

        self.wx_exists = wx.App.Get() is not None

        if forceupdate:
            self.init_struct = True
            self.parent = parent

        if self.wx_exists:
            self.set_mapviewer()
            # wx est initialisé et tourne --> on peut créer le Frame associé aux vecteurs
            if self.init_struct:
                self.init_ui()

            self.Show()
            self.Center()
            self.Raise()

    def init_ui(self):
        """
        Création de l'interface wx de gestion de l'objet
        """
        if self.wx_exists:
            # la strcuture n'existe pas encore
            box = BoxSizer(orient=wx.HORIZONTAL)

            boxleft = BoxSizer(orient=wx.VERTICAL)
            boxright = BoxSizer(orient=wx.VERTICAL)

            boxadd = BoxSizer(orient=wx.VERTICAL)
            boxdelete = BoxSizer(orient=wx.VERTICAL)
            boxupdown = BoxSizer(orient=wx.HORIZONTAL)
            boxupdownv = BoxSizer(orient=wx.VERTICAL)
            boxupdownz = BoxSizer(orient=wx.VERTICAL)

            self.xls=CpGrid(self,-1,wx.WANTS_CHARS)
            self.xls.CreateGrid(10,6)

            sizer_add_update = BoxSizer(orient=wx.HORIZONTAL)
            self.addrows = wx.Button(self,label=_('Rows+'))
            self.addrows.SetToolTip(_("Add rows to the grid --> Useful for manually adding some points to a vector"))
            self.addrows.Bind(wx.EVT_BUTTON,self.Onaddrows)

            self.updatevertices = wx.Button(self,label=_('Update'))
            self.updatevertices.SetToolTip(_("Transfer the coordinates from the editor to the memory and update the plot"))
            self.updatevertices.Bind(wx.EVT_BUTTON,self.Onupdatevertices)

            self._test_interior = wx.Button(self,label=_('Test interior'))
            self._test_interior.SetToolTip(_("Test if some segments of the active vector are exactly the same"))
            self._test_interior.Bind(wx.EVT_BUTTON,self.Ontest_interior)

            self.plot_mpl = wx.Button(self,label=_('Plot xy'))
            self.plot_mpl.SetToolTip(_("Plot the active vector in a new window (matplotlib)"))
            self.plot_mpl.Bind(wx.EVT_BUTTON,self.Onplotmpl)

            self.plot_mplsz = wx.Button(self,label=_('Plot sz'))
            self.plot_mplsz.SetToolTip(_("Plot the active vector in a new window (matplotlib)"))
            self.plot_mplsz.Bind(wx.EVT_BUTTON,self.Onplotmplsz)

            sizer_add_update.Add(self.addrows,1, wx.EXPAND)
            sizer_add_update.Add(self.updatevertices, 1, wx.EXPAND)
            sizer_add_update.Add(self.plot_mpl,1, wx.EXPAND)
            sizer_add_update.Add(self.plot_mplsz,1, wx.EXPAND)

            self.capturevertices = wx.Button(self,label=_('Add'))
            self.capturevertices.SetToolTip(_("Capture new points from mouse clicks \n\n Keyboard 'Return' to stop the action ! "))
            self.capturevertices.Bind(wx.EVT_BUTTON,self.Oncapture)

            self.modifyvertices = wx.Button(self,label=_('Modify'))
            self.modifyvertices.SetToolTip(_("Modify some point from mouse clicks \n\n - First click around the desired point \n - Move the position \n - Validate by a click \n\n Keyboard 'Return' to stop the action ! "))
            self.modifyvertices.Bind(wx.EVT_BUTTON,self.Onmodify)

            self.dynapar = wx.Button(self,label=_('Add and parallel'))
            self.dynapar.SetToolTip(_("Capture new points from mouse clicks and create parallel \n\n - MAJ + Middle Mouse Button to adjust the semi-distance \n - CTRL + MAJ + Middle Mouse Button to choose specific semi-distance \n\n Keyboard 'Return' to stop the action ! "))
            self.dynapar.Bind(wx.EVT_BUTTON,self.OncaptureandDynapar)

            self.createapar = wx.Button(self,label=_('Create parallel'))
            self.createapar.SetToolTip(_("Create a single parallel to the currently activated vector as a new vector in the same zone"))
            self.createapar.Bind(wx.EVT_BUTTON,self.OnAddPar)

            self._btn_simplify = wx.Button(self,label=_('Simplify'))
            self._btn_simplify.SetToolTip(_("Simplify the currently activated vector using the Douglas-Peucker algorithm"))
            self._btn_simplify.Bind(wx.EVT_BUTTON,self.Onsimplify)

            sizer_reverse_split = BoxSizer(orient=wx.HORIZONTAL)
            self.reverseorder = wx.Button(self,label=_('Reverse points order'))
            self.reverseorder.SetToolTip(_("Reverse the order/sens of the currently activated vector -- Overwrite the data"))
            self.reverseorder.Bind(wx.EVT_BUTTON,self.OnReverse)

            self.sascending = wx.Button(self,label=_('Verify vertices positions'))
            self.sascending.SetToolTip(_("Check whether the vertices of the activated vector are ordered according to increasing 's' defined as 2D geometric distance \n If needed, invert some positions and return information to the user"))
            self.sascending.Bind(wx.EVT_BUTTON,self.Onsascending)

            self._btn_buffer = wx.Button(self,label=_('Buffer'))
            self._btn_buffer.SetToolTip(_("Create a buffer around the currently activated vector\nThe buffer replaces the current vector"))
            self._btn_buffer.Bind(wx.EVT_BUTTON,self.Onbuffer)

            self.insertvertices = wx.Button(self,label=_('Insert'))
            self.insertvertices.SetToolTip(_("Insert new vertex into the currently active vector from mouse clicks \n The new vertex is inserted along the nearest segment  \n\n Keyboard 'Return' to stop the action ! "))
            self.insertvertices.Bind(wx.EVT_BUTTON,self.Oninsert)

            self.splitvertices = wx.Button(self,label=_('Copy and Split'))
            self.splitvertices.SetToolTip(_("Make a copy of the currently active vector and add new vertices according to a user defined length \n The new vertices are evaluated based on a 3D curvilinear distance"))
            self.splitvertices.Bind(wx.EVT_BUTTON,self.Onsplit)

            self.interpxyz = wx.Button(self,label=_('Interpolate coords'))
            self.interpxyz.SetToolTip(_("Linear Interpolation of the Z values if empty or egal to -99999 \n The interpolation uses the 's' value contained in the 5th column of the grid, X being the first one"))
            self.interpxyz.Bind(wx.EVT_BUTTON,self.Oninterpvec)

            self.evaluates = wx.Button(self,label=_('Evaluate s'))
            self.evaluates.SetToolTip(_("Calculate the curvilinear 's' distance using a '2D' or '3D' approach and store the result in the 5th column of the grid, X being the first one"))
            self.evaluates.Bind(wx.EVT_BUTTON,self.Onevaluates)

            self.update_from_s = wx.Button(self,label=_('Update from sz (support)'))
            self.update_from_s.SetToolTip(_("Update the coordinates of the vertices based on the 's' distance \n The interpolation uses the 's' value contained in the 5th column of the grid, X being the first one.\nThe support vector is in XY. It will be replaced."))
            self.update_from_s.Bind(wx.EVT_BUTTON,self.Onupdate_from_sz_support)

            #  Modified
            self.zoomonactive = wx.Button(self,label=_('Zoom on active vector'))
            self.zoomonactive.SetToolTip(_("Zoom on the active vector and a default view size of 500 m x 500 m"))
            self.zoomonactive.Bind(wx.EVT_BUTTON,self.Onzoom)

            # Added
            self.zoomonactivevertex = wx.Button(self, label =_('Zoom on active vertex'))
            self.zoomonactivevertex.SetToolTip(_("Zoom on the active vertex and a default view size of 50 m x 50 m"))
            self.zoomonactivevertex.Bind(wx.EVT_BUTTON, self.Onzoomvertex)
            boxzoom = BoxSizer(orient=wx.HORIZONTAL)
            boxzoom.Add(self.zoomonactive,1, wx.EXPAND)
            boxzoom.Add(self.zoomonactivevertex,1, wx.EXPAND)

            self.saveimages = wx.Button(self,label=_('Save images from active zone'))
            self.saveimages.Bind(wx.EVT_BUTTON,self.Onsaveimages)

            self.binfrom3 = wx.Button(self,label=_('Create bin from 3 vectors'))
            self.binfrom3.SetToolTip(_("Create a bin/rectangular channel based on 3 vectors in the currently active zone \n Some parameters will be prompted to the user (lateral height, ...) and if a triangular mesh must be created --> Blender"))
            self.binfrom3.Bind(wx.EVT_BUTTON,self.Oncreatebin)

            sizer_triangulation = wx.BoxSizer(wx.HORIZONTAL)
            self.trifromall = wx.Button(self,label=_('Triangulation'))
            self.trifromall.SetToolTip(_("Create a triangular mesh based on all vectors within the currently active zone.\nUse the vertices as they are after subdividing the vectors into a specified number of points.\nAdd the resulting mesh to the GUI.\nThis can be useful in certain interpolation methods."))
            self.trifromall.Bind(wx.EVT_BUTTON,self.Oncreatemultibin)

            self.trifromall_proj = wx.Button(self,label=_('Triang. (projection)'))
            self.trifromall_proj.SetToolTip(_("Create a triangular mesh based on all vectors in the currently active zone.\nGenerate vertices by projecting the central polyline, or the nearest one if there is an even number of polylines, onto the other polylines.\nAdd the resulting mesh to the GUI.\nThis can be useful in certain interpolation methods."))
            self.trifromall_proj.Bind(wx.EVT_BUTTON,self.Oncreatemultibin_project)

            sizer_triangulation.Add(self.trifromall, 1, wx.EXPAND)
            sizer_triangulation.Add(self.trifromall_proj, 1, wx.EXPAND)

            sizer_delaunay = wx.BoxSizer(wx.HORIZONTAL)
            self.constrainedDelaunay = wx.Button(self,label=_('Constr. Delaunay'))
            self.constrainedDelaunay.SetToolTip(_("Create a triangular mesh based on all vectors in the currently active zone."))
            self.constrainedDelaunay.Bind(wx.EVT_BUTTON,self.OnconstrainedDelaunay)

            self.tri_cs = wx.Button(self,label=_('Triang. (cross-section)'))
            self.tri_cs.SetToolTip(_("Create a triangular mesh based on all vectors in the currently active zone.\nSupport vectors must have 'support' in their name.\nOthers must cross the supports."))
            self.tri_cs.Bind(wx.EVT_BUTTON,self.Oncreatetricrosssection)

            sizer_delaunay.Add(self.constrainedDelaunay, 1, wx.EXPAND)
            sizer_delaunay.Add(self.tri_cs, 1, wx.EXPAND)

            sizer_polygons = wx.BoxSizer(wx.HORIZONTAL)
            self.polyfrompar = wx.Button(self,label=_('Polygons from paral.'))
            self.polyfrompar.SetToolTip(_("Create polygons in a new zone from parallels defined by " + _('Add and parallel') + _(" and a 2D curvilinear distance \n Useful for plotting some results or analyse data inside each polygon")))
            self.polyfrompar.Bind(wx.EVT_BUTTON,self.Oncreatepolygons)

            self.slidingpoly = wx.Button(self,label=_('Sliding polygons'))
            self.slidingpoly.SetToolTip(_("Create sliding polygons in a new zone"))
            self.slidingpoly.Bind(wx.EVT_BUTTON,self.Oncreateslidingpoly)

            sizer_polygons.Add(self.polyfrompar, 1, wx.EXPAND)
            sizer_polygons.Add(self.slidingpoly, 1, wx.EXPAND)

            # Added
            self.getxyfromsz = wx.Button(self, label = _('Update from sz (2 points)'))
            self.getxyfromsz.SetToolTip(_("Populate the X an Y columns based on: \n - Given sz coordinates, \n - 2 Points \n - The X and Y coordinates of the initial point (s = 0) and,  \n - The X and Y coordinates of a second point (for the direction)"))
            self.getxyfromsz.Bind(wx.EVT_BUTTON, self.get_xy_from_sz)

            boxright.Add(self.xls,1,wx.EXPAND)
            boxright.Add(sizer_add_update,0,wx.EXPAND)

            # boxright.Add(self.updatevertices,0,wx.EXPAND)

            subboxadd = BoxSizer(orient=wx.HORIZONTAL)
            subboxadd.Add(self.capturevertices,1,wx.EXPAND)
            subboxadd.Add(self.dynapar,1,wx.EXPAND)
            boxright.Add(subboxadd,0,wx.EXPAND)

            subboxmod = wx.BoxSizer(wx.HORIZONTAL)
            subboxmod.Add(self.modifyvertices,1,wx.EXPAND)
            subboxmod.Add(self.insertvertices,1,wx.EXPAND)
            boxright.Add(subboxmod,0,wx.EXPAND)

            subboxparsimpl = wx.BoxSizer(orient=wx.HORIZONTAL)
            subboxparsimpl.Add(self.createapar,1,wx.EXPAND)
            subboxparsimpl.Add(self._btn_simplify,1,wx.EXPAND)

            boxright.Add(subboxparsimpl,0,wx.EXPAND)

            sizer_reverse_split.Add(self.reverseorder,1,wx.EXPAND)
            sizer_reverse_split.Add(self.splitvertices,1,wx.EXPAND)
            boxright.Add(sizer_reverse_split,0,wx.EXPAND)
            # boxright.Add(self.splitvertices,0,wx.EXPAND)

            # boxright.Add(self.zoomonactive,0,wx.EXPAND)
            boxright.Add(boxzoom,0,wx.EXPAND)

            box_s = wx.BoxSizer(wx.HORIZONTAL)
            boxright.Add(box_s,0,wx.EXPAND)

            box_s.Add(self.evaluates,1,wx.EXPAND)
            box_s.Add(self.update_from_s,1,wx.EXPAND)
            box_s.Add(self.getxyfromsz,1,wx.EXPAND) # Added

            box_interp_indices = wx.BoxSizer(wx.HORIZONTAL)
            box_interp_indices.Add(self.interpxyz,1,wx.EXPAND)
            box_interp_indices.Add(self._test_interior, 1, wx.EXPAND)


            boxright.Add(box_interp_indices,0,wx.EXPAND)


            _sizer_ascbuffer = wx.BoxSizer(wx.HORIZONTAL)
            _sizer_ascbuffer.Add(self.sascending,1,wx.EXPAND)
            _sizer_ascbuffer.Add(self._btn_buffer,1,wx.EXPAND)
            boxright.Add(_sizer_ascbuffer,0,wx.EXPAND)

            sizer_values_surface = wx.BoxSizer(wx.HORIZONTAL)
            self.butgetval = wx.Button(self,label=_('Get values'))
            self.butgetval.SetToolTip(_("Get values of the attached/active array (not working with 2D results) on each vertex of the active vector and update the editor"))
            self.butgetval.Bind(wx.EVT_BUTTON,self.Ongetvalues)

            self.btn_surface = wx.Button(self,label=_('Surface'))
            self.btn_surface.SetToolTip(_("Compute the surface of the active vector/polygon"))
            self.btn_surface.Bind(wx.EVT_BUTTON,self.Onsurface)

            sizer_values_surface.Add(self.butgetval,1,wx.EXPAND)
            sizer_values_surface.Add(self.btn_surface,1,wx.EXPAND)

            boxright.Add(sizer_values_surface,0,wx.EXPAND)

            self.butgetvallinked = wx.Button(self,label=_('Get values (all)'))
            self.butgetvallinked.SetToolTip(_("Get values of all the visible arrays and 2D results on each vertex of the active vector \n\n Create a new zone containing the results"))
            self.butgetvallinked.Bind(wx.EVT_BUTTON,self.Ongetvalueslinked)

            self.butgetrefvallinked = wx.Button(self,label=_('Get values (all and remeshing)'))
            self.butgetrefvallinked.SetToolTip(_("Get values of all the visible arrays and 2D results on each vertex of the active vector \n and more is the step size of the array is more precise \n\n Create a new zone containing the results"))
            self.butgetrefvallinked.Bind(wx.EVT_BUTTON,self.Ongetvalueslinkedandref)

            self._move_rotate_sizer = wx.BoxSizer(wx.HORIZONTAL)

            self.butmove = wx.Button(self,label=_('Move'))
            self.butmove.SetToolTip(_("Move the active vector - If not defined in properties, the first right click is the origin of the move"))
            self.butmove.Bind(wx.EVT_BUTTON,self.OnMove)

            self.butrotate = wx.Button(self,label=_('Rotate'))
            self.butrotate.SetToolTip(_("Rotate the active vector - If not defined in properties, the first right click is the origin of the rotation"))
            self.butrotate.Bind(wx.EVT_BUTTON,self.OnRotate)

            self._move_rotate_sizer.Add(self.butmove, 1, wx.EXPAND)
            self._move_rotate_sizer.Add(self.butrotate, 1, wx.EXPAND)

            sizer_budget = wx.BoxSizer(wx.HORIZONTAL)
            sizer_budget.Add(self.butgetvallinked,1,wx.EXPAND)
            sizer_budget.Add(self.butgetrefvallinked,1,wx.EXPAND)
            boxright.Add(sizer_budget,0,wx.EXPAND)
            # boxright.Add(self.butgetrefvallinked,0,wx.EXPAND)


            boxright.Add(self._move_rotate_sizer, 0, wx.EXPAND)

            self.treelist = TreeListCtrl(self,style=TL_CHECKBOX|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_EDIT_LABELS)
            self.treelist.AppendColumn('Zones')
            self.treelist.Bind(EVT_TREELIST_ITEM_CHECKED, self.OnCheckItem)
            self.treelist.Bind(EVT_TREELIST_ITEM_ACTIVATED, self.OnActivateItem)
            self.treelist.Bind(EVT_TREELIST_ITEM_CONTEXT_MENU,self.OnRDown)

            self.treelist.Bind(wx.EVT_CHAR,self.OnEditLabel)

            self.labelactvect = wx.StaticText( self, wx.ID_ANY, _("None"), style=wx.ALIGN_CENTER_HORIZONTAL )
            self.labelactvect.Wrap( -1 )
            self.labelactvect.SetToolTip(_('Name of the active vector'))
            self.labelactzone = wx.StaticText( self, wx.ID_ANY, _("None"), style=wx.ALIGN_CENTER_HORIZONTAL )
            self.labelactzone.Wrap( -1 )
            self.labelactzone.SetToolTip(_('Name of the active zone'))

            sizer_addzonevector=wx.BoxSizer(wx.HORIZONTAL)
            self.addzone = wx.Button(self,label=_('Add zone'))
            self.addvector = wx.Button(self,label=_('Add vector'))

            sizer_addzonevector.Add(self.addzone,1,wx.EXPAND)
            sizer_addzonevector.Add(self.addvector,1,wx.EXPAND)

            self.duplicatezone = wx.Button(self,label=_('Duplicate zone'))
            self.duplicatevector = wx.Button(self,label=_('Duplicate vector'))

            self.deletezone = wx.Button(self,label=_('Delete zone'))
            self.findactivevector = wx.Button(self,label=_('Find in all'))
            self.findactivevector.SetToolTip(_("Search and activate the nearest vector by mouse click (Searching window : all zones)"))
            self.findactivevectorcurz = wx.Button(self,label=_('Find in active'))
            self.findactivevectorcurz.SetToolTip(_("Search and activate the nearest vector by mouse click (Searching window : active zone)"))
            self.deletevector = wx.Button(self,label=_('Delete vector'))

            self.upvector = wx.Button(self,label=_('Up vector'))
            self.downvector = wx.Button(self,label=_('Down vector'))
            self.upzone = wx.Button(self,label=_('Up zone'))
            self.downzone = wx.Button(self,label=_('Down zone'))
            # self.interpolate = wx.Button(self,label=_('Interpolate vector'))

            self._move_rotate_zone_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.butmove_zone = wx.Button(self,label=_('Move zone'))
            self.butmove_zone.SetToolTip(_("Move the active zone - If not defined in properties, the first right click is the origin of the move"))
            self.butmove_zone.Bind(wx.EVT_BUTTON,self.OnMoveZone)

            self.butrotate_zone = wx.Button(self,label=_('Rotate zone'))
            self.butrotate_zone.SetToolTip(_("Rotate the active zone - If not defined in properties, the first right click is the origin of the rotation"))
            self.butrotate_zone.Bind(wx.EVT_BUTTON,self.OnRotateZone)

            self._move_rotate_zone_sizer.Add(self.butmove_zone, 1, wx.EXPAND)
            self._move_rotate_zone_sizer.Add(self.butrotate_zone, 1, wx.EXPAND)

            self.addzone.Bind(wx.EVT_BUTTON,self.OnClickadd_zone)
            self.addvector.Bind(wx.EVT_BUTTON,self.OnClickadd_vector)

            self.duplicatezone.Bind(wx.EVT_BUTTON,self.OnClickduplicate_zone)
            self.duplicatevector.Bind(wx.EVT_BUTTON,self.OnClickduplicate_vector)

            self.deletezone.Bind(wx.EVT_BUTTON,self.OnClickdelete_zone)
            self.deletevector.Bind(wx.EVT_BUTTON,self.OnClickdelete_vector)
            self.upvector.Bind(wx.EVT_BUTTON,self.OnClickup_vector)
            self.downvector.Bind(wx.EVT_BUTTON,self.OnClickdown_vector)

            self.upzone.Bind(wx.EVT_BUTTON,self.OnClickup_zone)
            self.downzone.Bind(wx.EVT_BUTTON,self.OnClickdown_zone)

            # self.interpolate.Bind(wx.EVT_BUTTON,self.OnClickInterpolate)
            self.findactivevector.Bind(wx.EVT_BUTTON,self.OnClickfindactivate_vector)
            self.findactivevectorcurz.Bind(wx.EVT_BUTTON,self.OnClickfindactivate_vector2)

            boxadd.Add(self.labelactvect,1,wx.EXPAND)
            boxadd.Add(self.labelactzone,1,wx.EXPAND)
            boxadd.Add(sizer_addzonevector,1,wx.EXPAND)
            # boxadd.Add(self.addvector,1,wx.EXPAND)

            boxduplicate = wx.BoxSizer(wx.HORIZONTAL)
            boxduplicate.Add(self.duplicatezone,1,wx.EXPAND)
            boxduplicate.Add(self.duplicatevector,1,wx.EXPAND)
            boxadd.Add(boxduplicate,1,wx.EXPAND)

            subboxadd = wx.BoxSizer(wx.HORIZONTAL)
            subboxadd.Add(self.findactivevector,1,wx.EXPAND)
            subboxadd.Add(self.findactivevectorcurz,1,wx.EXPAND)
            boxadd.Add(subboxadd,1,wx.EXPAND)

            subboxdelete = wx.BoxSizer(wx.HORIZONTAL)
            subboxdelete.Add(self.deletezone,1,wx.EXPAND)
            subboxdelete.Add(self.deletevector,1,wx.EXPAND)

            boxdelete.Add(subboxdelete,1,wx.EXPAND)

            boxupdown.Add(boxupdownz,1,wx.EXPAND)
            boxupdown.Add(boxupdownv,1,wx.EXPAND)

            boxupdownv.Add(self.upvector,1,wx.EXPAND)
            boxupdownv.Add(self.downvector,1,wx.EXPAND)
            boxupdownz.Add(self.upzone,1,wx.EXPAND)
            boxupdownz.Add(self.downzone,1,wx.EXPAND)

            # boxdelete.Add(self.interpolate,1,wx.EXPAND)
            boxtri = wx.BoxSizer(wx.VERTICAL)
            boxtri.Add(self.saveimages,1,wx.EXPAND)
            boxtri.Add(self.binfrom3,1,wx.EXPAND)
            boxtri.Add(sizer_triangulation,1,wx.EXPAND)
            # boxtri.Add(self.trifromall,1,wx.EXPAND)
            # boxtri.Add(self.trifromall_proj,1,wx.EXPAND)
            boxtri.Add(sizer_delaunay,1,wx.EXPAND)
            boxtri.Add(sizer_polygons,1,wx.EXPAND)
            # boxtri.Add(self.polyfrompar,1,wx.EXPAND)
            # boxtri.Add(self.slidingpoly,1,wx.EXPAND)

            boxleft.Add(self.treelist,1,wx.EXPAND)
            boxleft.Add(boxadd,0,wx.EXPAND)
            boxleft.Add(boxdelete,0,wx.EXPAND)
            boxleft.Add(boxupdown,0,wx.EXPAND)
            boxleft.Add(boxtri,0,wx.EXPAND)
            boxleft.Add(self._move_rotate_zone_sizer, 0, wx.EXPAND)

            box.Add(boxleft,1,wx.EXPAND)
            box.Add(boxright,1,wx.EXPAND)

            self.fill_structure()

            self.treelist.SetSize(200,500)
            self.SetSize(650,700)

            self.SetSizer(box)

            icon = wx.Icon()
            icon_path = Path(__file__).parent / "apps/wolf.ico"
            icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
            self.SetIcon(icon)

            if self.idx == '':
                if self.parent is not None:
                    try:
                        self.SetTitle(_('Zones associated to : {}'.format(self.parent.idx)))
                    except:
                        logging.warning(_('No parent idx found'))
            else:
                self.SetTitle(_('Zones : {}'.format(self.idx)))

            self.init_struct=False

    def get_xy_from_sz(self, event: wx.Event):
        """
        Add vertices and their respectives xy coordinates from s and Z entries in the xls grid:
            - NB: The coordinates of the initial point s= 0 and one other points should be explicitly given in the xls grid.
        """
        if self.wx_exists:
            if self.verify_activevec():
                return

        curv  = self.active_vector
        n_rows = self.xls.GetNumberRows()

        if n_rows < 2:
            logging.warning(_('You need at least 2 points to interpolate the XY coordinates from the SZ coordinates'))
            return

        # Getting the 2 first XY coordinates
        X = []
        Y = []

        z_row = 1 #Starting from the second row because the first one is the initial point

        # First row coordinates
        x1 = self.xls.GetCellValue(0,0)
        y1 = self.xls.GetCellValue(0,1)


        if x1 != '' and y1 != '':
            X.append(float(x1))
            Y.append(float(y1))

        else:
            raise Exception('Encode the coordinates of the initial point (S = 0 -->  first point)')

        # Coordinates of the second points
        while z_row < n_rows:
            if len(X) < 2 and len(Y) < 2:
                x2 = self.xls.GetCellValue(z_row,0)
                y2 = self.xls.GetCellValue(z_row,1)

                if x2 != '' and y2 != '':
                    X.append(float(x2))
                    Y.append(float(y2))

                z_row += 1

            else:
                break

        xy1 = np.array([X[0], Y[0]])
        xy2 = np.array([X[1], Y[1]])

        # xy2 /= np.linalg.norm(xy2 - xy1)

        # Collection of sz coordinates
        row = 0

        SZ = []

        while row < n_rows:
            s = self.xls.GetCellValue(row,4)
            z = self.xls.GetCellValue(row,2)

            if z=='':
                z=0.

            if s != '':
                SZ.append((s,z))
                row += 1

            elif s=='':         #FIXME logging msg to notify the user a point is missing
                break

            else:
                raise Exception (_("Recheck your data inputs"))
                break

        sz = np.asarray(SZ,dtype='float64') # FIXME The type is required otherwise type == <U

        self.update_from_sz_direction(xy1, xy2, sz)

        # update of the xls grid
        for k in range(curv.nbvertices ):
            self.xls.SetCellValue(k,0,str(curv.myvertices[k].x))
            self.xls.SetCellValue(k,1,str(curv.myvertices[k].y))


    def fill_structure(self):
        """
        Remplissage de la structure wx
        """

        def store_tree_state(tree:TreeListCtrl):
            """ Store the state of the tree control.

            Recursively store the state of the tree control in a list of item data.
            """

            expended_items = []
            root = tree.GetRootItem()

            if root is None:
                return

            def traverse_and_store(item:wx._dataview.TreeListItem):
                if not item.IsOk():
                    return

                if tree.IsExpanded(item):
                    expended_items.append(tree.GetItemData(item))

                item = tree.GetNextItem(item)

                traverse_and_store(item)

            traverse_and_store(root)

            return expended_items

        def restore_tree_state(tree:TreeListCtrl, expended_items):
            """ Restore the state of the tree control.

            Recursively restore the state of the tree control from a list of item data.
            """

            if len(expanded)==0:
                # Nothing to do
                return

            root = tree.GetRootItem()

            if root is None:
                return

            def traverse_and_restore(item):
                if not item.IsOk():
                    return

                if tree.GetItemData(item) in expended_items:
                    tree.Expand(item)

                item = tree.GetNextItem(item)
                traverse_and_restore(item)

            traverse_and_restore(root)

        if self.wx_exists:
            if self.xls is not None:

                expanded = store_tree_state(self.treelist)

                self.treelist.DeleteAllItems()

                root = self.treelist.GetRootItem()
                mynode=self.treelist.AppendItem(root, 'All zones', data=self)
                self.treelist.CheckItem(mynode)

                for curzone in self.myzones:
                    curzone.add2tree(self.treelist,mynode)

                self.treelist.Expand(mynode)

                restore_tree_state(self.treelist, expanded)

    def expand_tree(self, objzone=None):
        """
        Développe la structure pour un objet spécifique stocké dans la self.treelist.

        L'objet peut être une 'zone' ou un 'vector' --> see more in 'fill_structure'.
        """

        if self.wx_exists:
            if self.xls is not None:
                root = self.treelist.GetRootItem()

                curchild = self.treelist.GetFirstChild(root)
                curzone=self.treelist.GetItemData(curchild)

                while curchild is not None:
                    if curzone is objzone:
                        self.treelist.Expand(curchild)
                        break
                    else:
                        curchild=self.treelist.GetNextItem(curchild)
                        curzone=self.treelist.GetItemData(curchild)

    def Oncapture(self, event:wx.MouseEvent):
        """
        Ajoute de nouveaux vertices au vecteur courant
        Fonctionne par clicks souris via le GUI wx de WolfMapViewer
        """

        if self.wx_exists:
            # N'est pas à strictement parlé dépendant de wx mais n'a de sens
            # que si le mapviewer est défini --> si un GUI wx existe
            if self.verify_activevec():
                return

            self.mapviewer.start_action('capture vertices', _('Capture vertices'))
            firstvert=wolfvertex(0.,0.)
            self.active_vector.add_vertex(firstvert)
            self.active_vector._reset_listogl()
            self.mapviewer.mimicme()

    def OnReverse(self, event:wx.MouseEvent):
        """
        Renverse le vecteur courant
        """

        if self.wx_exists:
            # N'est pas à strictement parlé dépendant de wx mais n'a de sens
            # que si le mapviewer est défini --> si un GUI wx existe
            if self.verify_activevec():
                return

            self.active_vector.reverse()
            self.fill_structure()
            self.active_vector._reset_listogl()

    def Onsimplify(self, event:wx.MouseEvent):
        """
        Simplify the active vector using the Douglas-Peucker algorithm
        """

        if self.verify_activevec():
            return

        tolerance = 1.0
        if self.wx_exists:

            dlg = wx.TextEntryDialog(None, _('Tolerance ?'), value='1.0')
            ret = dlg.ShowModal()
            tolerance = dlg.GetValue()
            dlg.Destroy()
            try:
                tolerance = float(tolerance)
            except:
                logging.warning(_('Bad value -- Retry !'))
                return

        new_ls = self.active_vector.linestring.simplify(tolerance, preserve_topology=True)

        xy = new_ls.xy # shape (2, n)
        xy = np.array(xy).T # shape (n, 2)

        if len(xy) == 0:
            logging.warning(_('No points to add'))
            return

        tmp = self.active_vector.deepcopy().linestring
        self.active_vector.reset()
        for x, y in xy:
            pt = Point(x, y)
            self.active_vector.add_vertex(wolfvertex(x, y, tmp.interpolate(tmp.project(pt)).z))

        self.xls_active_vector()
        self.active_vector._reset_listogl()


    def OnAddPar(self, event:wx.MouseEvent):
        """
        Ajout d'une parallèle au vecteur courant via le bouton adhoc
        """

        if self.wx_exists:
            if self.verify_activevec():
                return

            dlg = wx.TextEntryDialog(None,_('Normal distance ? \nd > 0 is right \n d < 0 is left'),value='0.0')
            ret=dlg.ShowModal()
            dist=dlg.GetValue()
            dlg.Destroy()
            try:
                dist = float(dist)
            except:
                logging.warning(_('Bad value -- Retry !'))
                return

            self.active_zone.add_parallel(dist)
            self.fill_structure()
            self.find_minmax(True)
            self.expand_tree(self.active_zone)
            self.active_zone.reset_listogl()

    def OnMove(self, event:wx.MouseEvent):
        """
        Déplacement du vecteur actif
        """
        if self.wx_exists:
            if self.verify_activevec():
                return

            self.mapviewer.start_action('move vector', _('Move vector'))
            self.active_vector.set_cache()
            self.mapviewer.mimicme()

    def OnMoveZone(self, event:wx.MouseEvent):
        """
        Déplacement de la zone active
        """
        if self.wx_exists:
            if self.verify_activezone():
                return

            self.mapviewer.start_action('move zone', _('Move zone'))
            self.active_zone.set_cache()
            self.mapviewer.mimicme()

    def OnRotate(self, event:wx.MouseEvent):
        """
        Rotation du vecteur actif
        """

        if self.wx_exists:
            if self.verify_activevec():
                return

            self.mapviewer.start_action('rotate vector', _('Rotate vector'))
            self.active_vector.set_cache()
            self.mapviewer.mimicme()

    def OnRotateZone(self, event:wx.MouseEvent):
        """
        Rotation de la zone active
        """

        if self.wx_exists:
            if self.verify_activezone():
                return

            self.mapviewer.start_action('rotate zone', _('Rotate zone'))
            self.active_zone.set_cache()
            self.mapviewer.mimicme()

    def OncaptureandDynapar(self, event:wx.MouseEvent):
        """
        Ajoute des vertices au vecteur courant et crée des parallèles gauche-droite
        """

        if self.wx_exists:
            if self.verify_activevec():
                return

            if self.active_zone.nbvectors > 1:
                dlg = wx.MessageDialog(None, _('You already have more than one vector in the active zone. This action will conserve only the active vector.\nDo you want to continue?'), _('Warning'), style=wx.YES_NO | wx.ICON_WARNING)
                ret = dlg.ShowModal()
                if ret == wx.ID_NO:
                    dlg.Destroy()
                    return
                logging.warning(_('You already have more than one vector in the active zone. This action will conserve only the active vector and you want it.'))
                dlg.Destroy()

            self.mapviewer.start_action('dynamic parallel', _('Dynamic parallel'))

            firstvert=wolfvertex(0.,0.)
            self.active_vector.add_vertex(firstvert)
            self.mapviewer.mimicme()
            self.active_zone.reset_listogl()


    def Onsascending(self, e:wx.MouseEvent):
        """
        S'assure que les points sont ordonnés avec une distance 2D croissante

        Retourne un message avec les valeurs modifiées le cas échéant
        """

        if self.wx_exists:
            if self.verify_activevec():
                return

            correct,wherec= self.active_vector.verify_s_ascending()
            self.xls_active_vector()

            if correct:
                msg=_('Modification on indices :\n')
                for curi in wherec:
                    msg+= str(curi)+'<-->'+str(curi+1)+'\n'
                dlg=wx.MessageDialog(None,msg)
                dlg.ShowModal()
                dlg.Destroy()

    def Onbuffer(self, e:wx.MouseEvent):
        """ Create a buffer around the currently activated vector.
        The buffer replaces the active vector in the same zone."""

        if self.wx_exists:
            if self.verify_activevec():
                return

            dlg = wx.TextEntryDialog(None, _('Buffer distance ?'), value='5.0')
            ret = dlg.ShowModal()
            dist = dlg.GetValue()
            dlg.Destroy()
            try:
                dist = float(dist)
            except:
                logging.warning(_('Bad value -- Retry !'))
                return
            if dist <= 0:
                logging.warning(_('Buffer distance must be > 0 -- Retry !'))
                return

            if self.active_vector.nbvertices == 1:
                self.active_vector.myvertices = self.active_vector.myvertices * 3
                logging.warning(_('The active vector has only one vertex. It will be duplicated to create a buffer.'))
            if self.active_vector.nbvertices == 2:
                self.active_vector.myvertices = self.active_vector.myvertices + [self.active_vector.myvertices[0]]
                logging.warning(_('The active vector has only two vertices. The first one will be duplicated to create a buffer.'))

            self.active_vector.buffer(dist)
            self.active_vector._reset_listogl()

    def Onmodify(self, event:wx.MouseEvent):
        """
        Permet la modification interactive de vertex dans le vector actif

        Premier click : recherche du vertex le plus proche
        Second click  : figer la nouvelle position

        --> action active jusqu'à sélectionne une autre action ou touche Entrée
        """

        if self.wx_exists:
            if self.verify_activevec():
                return

            self.mapviewer.start_action('modify vertices', _('Modify vertices'))
            self.mapviewer.mimicme()
            self.active_zone.reset_listogl()

    def OnPlotIndices(self, event:wx.MouseEvent):
        """
        Plot the indices of the active vector in the mapviewer
        """

        if self.wx_exists:
            if self.verify_activevec():
                return
            self.mapviewer._force_to_plot_indices = True

    def Onzoom(self, event:wx.MouseEvent):
        """
        Zoom sur le vecteur actif dans le mapviewer
        """

        if self.wx_exists:
            if self.verify_activevec():
                return

            self.mapviewer.zoomon_activevector()

    def Onzoomvertex(self, event:wx.MouseEvent):
        """
        Zoom sur le vertex actif dans le mapviewer
        """

        if self.wx_exists:
            if self.verify_activevec():
                return

            self.mapviewer.zoomon_active_vertex()

    def Ongetvalues(self, e:wx.MouseEvent):
        """
        Récupère les valeurs dans une matrice

        --> soit la matrice courante
        --> soit la matrice active de l'interface parent
        """

        if self.verify_activevec():
            return

        try:
            curarray = self.parent.active_array
            if curarray is not None:
                self.active_vector.get_values_on_vertices(curarray)
                self.active_vector.fillgrid(self.xls)
            else:
                logging.info(_('Please activate the desired array'))
        except:
            raise Warning(_('Not supported in the current parent -- see PyVertexVectors in Ongetvalues function'))

    def Onsurface(self, e:wx.MouseEvent):
        """
        Calcul de la surface du vecteur actif
        """

        if self.verify_activevec():
            return

        dlg = wx.MessageDialog(None, _('The surface of the active vector is : {} m²'.format(self.active_vector.surface)), style = wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def Ongetvalueslinked(self, e:wx.MouseEvent):
        """
        Récupération des valeurs sous toutes les matrices liées pour le vecteur actif

        Crée une nouvelle zone contenant une copie du vecteur
        Le nombre de vertices est conservé
        """

        if self.parent is not None:
            if self.verify_activevec():
                return

            try:
                linked = self.parent.get_linked_arrays()

                if len(linked)>0:
                    newzone:zone
                    newzone = self.active_vector.get_values_linked(linked, False)

                    self.add_zone(newzone)
                    newzone.parent=self

                    self.fill_structure()
            except:
                raise Warning(_('Not supported in the current parent -- see PyVertexVectors in Ongetvalueslinked function'))

    def Ongetvalueslinkedandref(self, e:wx.MouseEvent):
        """
        Récupération des valeurs sous toutes les matrices liées pour le vecteur actif

        Crée une nouvelle zone contenant une copie du vecteur.

        Le nombre de vertices est adapté pour correspondre au mieux à la matrice de liée et ne pas perdre, si possible, d'information.
        """
        if self.parent is not None:
            if self.verify_activevec():
                return

            linked=self.parent.get_linked_arrays()

            if len(linked)>0:
                newzone:zone
                newzone=self.active_vector.get_values_linked(linked)

                self.add_zone(newzone)
                newzone.parent=self

                self.fill_structure()

    def Onsaveimages(self, event:wx.MouseEvent):
        """
        Enregistrement d'une image pour tous les vecteurs
        """

        self.save_images_fromvec()

    def Oncreatepolygons(self, event:wx.MouseEvent):
        """
        Création de polygones depuis des paralèles contenues dans la zone active
        """

        if self.active_zone is None:
            logging.warning(_('No active zone - Nothing to do !'))
            return

        if self.wx_exists:
            curz = self.active_zone

            if curz.nbvectors!=3:
                logging.warning(_('The active zone must contain 3 vectors and only 3'))
                return

            self.active_zone.myvectors[1].update_lengths()

            poly_dlg = wx.Dialog(None, title=_('Polygons from parallels options'), size=(400, 350))
            poly_dlg.SetBackgroundColour(wx.Colour(240, 240, 240))
            poly_sizer = wx.BoxSizer(wx.VERTICAL)
            poly_sizer.Add(wx.StaticText(poly_dlg, label=_('Polygons from parallels options')), 0, wx.ALL | wx.CENTER, 5)
            poly_sizer.Add(wx.StaticText(poly_dlg, label=_('This will create polygons from the parallels in the active zone')), 0, wx.ALL | wx.CENTER, 5)
            poly_sizer.Add(wx.StaticText(poly_dlg, label=_('Please enter the parameters below:')), 0, wx.ALL | wx.CENTER, 5)
            poly_sizer.Add(wx.StaticText(poly_dlg, label=_('Longitudinal size [cm]:')), 0, wx.ALL | wx.LEFT, 5)
            ds_text = wx.TextCtrl(poly_dlg, value='5000')  # Default
            poly_sizer.Add(ds_text, 0, wx.ALL | wx.EXPAND, 5)
            poly_sizer.Add(wx.StaticText(poly_dlg, label=_('How many polygons? \n\n 1 = one large polygon from left to right\n 2 = two polygons - one left and one right')), 0, wx.ALL | wx.LEFT, 5)
            nb_text = wx.TextCtrl(poly_dlg, value='1')  # Default
            poly_sizer.Add(nb_text, 0, wx.ALL | wx.EXPAND, 5)
            ok_button = wx.Button(poly_dlg, label=_('OK'))
            ok_button.Bind(wx.EVT_BUTTON, lambda evt: self._OnCreatePolygons(evt, ds_text, nb_text, poly_dlg))
            poly_sizer.Add(ok_button, 0, wx.ALL | wx.CENTER, 5)
            poly_dlg.SetSizer(poly_sizer)
            poly_dlg.Layout()
            poly_dlg.CentreOnParent()
            poly_dlg.ShowModal()

            # dlg=wx.NumberEntryDialog(None,_('What is the desired longitudinal size [cm] ?'),'ds','ds size',500,1,10000)
            # ret=dlg.ShowModal()
            # if ret==wx.ID_CANCEL:
            #     dlg.Destroy()
            #     return

            # ds=float(dlg.GetValue())/100.
            # dlg.Destroy()

            # dlg=wx.NumberEntryDialog(None,_('How many polygons ? \n\n 1 = one large polygon from left to right\n 2 = two polygons - one left and one right'),'Number','Polygons',1,1,2)
            # ret=dlg.ShowModal()
            # if ret==wx.ID_CANCEL:
            #     dlg.Destroy()
            #     return

            # nb=int(dlg.GetValue())
            # dlg.Destroy()


    def _OnCreatePolygons(self, event:wx.MouseEvent, ds_text:wx.TextCtrl, nb_text:wx.TextCtrl, option_dialog:wx.Dialog):
        """
        Handle the creation of polygons based on user input from the dialog.
        """

        try:
            ds = float(ds_text.GetValue()) / 100.0  # Convert cm to
            nb = int(nb_text.GetValue())  # Number of polygons

            if ds <= 0:
                wx.MessageBox(_('Please enter a valid distance greater than 0.'), _('Input Error'), wx.OK | wx.ICON_ERROR)
                return

            if ds > self.active_zone.myvectors[1].length2D:
                wx.MessageBox(_('The distance must be less than the length of the center vector in the active zone.'), _('Input Error'), wx.OK | wx.ICON_ERROR)
                return

            if nb < 1 or nb > 2:
                wx.MessageBox(_('Please enter a valid number of polygons (1 or 2).'), _('Input Error'), wx.OK | wx.ICON_ERROR)
                return
        except ValueError:
            wx.MessageBox(_('Please enter valid numeric values for all fields.'), _('Input Error'), wx.OK | wx.ICON_ERROR)
            return

        try:
            self.active_zone.create_polygon_from_parallel(ds,nb)
        except Exception as e:
            logging.error(_('Error during polygon creation: {}').format(str(e)))

        if self.get_mapviewer() is not None:
            self.get_mapviewer().Paint()

        option_dialog.Destroy()


    def Oncreateslidingpoly(self, event:wx.MouseEvent):
        """
        Create sliding polygons from a support vector
        """

        if self.active_zone is None:
            logging.warning(_('No active zone - Nothing to do !'))
            return

        if self.active_zone.nbvectors!=1:
            logging.error(_('The active zone must contain 1 vector and only 1'))
            dlg = wx.MessageDialog(None,_('The active zone must contain 1 vector and only 1'),style=wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        option_dialog = wx.Dialog(None, title=_('Sliding polygons options'), size=(450, 520))
        option_dialog.SetBackgroundColour(wx.Colour(240, 240, 240))
        option_sizer = wx.BoxSizer(wx.VERTICAL)
        option_sizer.Add(wx.StaticText(option_dialog, label=_('Sliding polygons options')), 0, wx.ALL | wx.CENTER, 5)
        option_sizer.Add(wx.StaticText(option_dialog, label=_('This will create sliding polygons from the active vector in the active zone')), 0, wx.ALL | wx.CENTER, 5)
        option_sizer.Add(wx.StaticText(option_dialog, label=_('Please enter the parameters below:')), 0, wx.ALL | wx.CENTER, 5)
        option_sizer.Add(wx.StaticText(option_dialog, label=_('Longitudinal size [cm]:')), 0, wx.ALL | wx.LEFT, 5)
        ds_text = wx.TextCtrl(option_dialog, value='5000')  # Default value in cm
        option_sizer.Add(ds_text, 0, wx.ALL | wx.EXPAND, 5)
        option_sizer.Add(wx.StaticText(option_dialog, label=_('Sliding length [cm]:')), 0, wx.ALL | wx.LEFT, 5)
        sliding_text = wx.TextCtrl(option_dialog, value='5000')  # Default value
        option_sizer.Add(sliding_text, 0, wx.ALL | wx.EXPAND, 5)
        option_sizer.Add(wx.StaticText(option_dialog, label=_('Farthest parallel [cm]:')), 0, wx.ALL | wx.LEFT, 5)
        farthest_text = wx.TextCtrl(option_dialog, value='10000')  # Default
        option_sizer.Add(farthest_text, 0, wx.ALL | wx.EXPAND, 5)
        option_sizer.Add(wx.StaticText(option_dialog, label=_('Parallel interval [cm]:')), 0, wx.ALL | wx.LEFT, 5)
        interval_text = wx.TextCtrl(option_dialog, value='1000')  # Default
        option_sizer.Add(interval_text, 0, wx.ALL | wx.EXPAND, 5)

        intersect_sizer = wx.BoxSizer(wx.HORIZONTAL)
        inter_checkbox = wx.CheckBox(option_dialog, label=_('Use intersect zone if available'))
        inter_checkbox.SetValue(True)  # Default to True
        offset_text = wx.TextCtrl(option_dialog, value='10')  # Default offset value
        intersect_sizer.Add(inter_checkbox, 0, wx.ALL | wx.LEFT, 5)
        intersect_sizer.Add(wx.StaticText(option_dialog, label=_('Offset [cm]:')), 0, wx.ALL | wx.LEFT, 5)
        intersect_sizer.Add(offset_text, 0, wx.ALL | wx.EXPAND, 5)
        option_sizer.Add(wx.StaticText(option_dialog, label=_('If you have a zone named "intersect", you can use it to constrain the polygons.\nWhen constraint vectors are present, they cannot intersect the central vector.\nLikewise, they must be drawn moving away from the central vector.')), 0, wx.ALL | wx.CENTER, 5)

        option_sizer.Add(intersect_sizer, 0, wx.ALL | wx.LEFT, 5)
        separate_checkbox = wx.CheckBox(option_dialog, label=_('Separate left and right polygons'))
        separate_checkbox.SetValue(False)  # Default to False
        option_sizer.Add(separate_checkbox, 0, wx.ALL | wx.LEFT, 5)
        ok_button = wx.Button(option_dialog, label=_('OK'))
        ok_button.Bind(wx.EVT_BUTTON, lambda evt: self._OnCreateSlidingPolygon(evt, ds_text, sliding_text, farthest_text, interval_text, inter_checkbox, offset_text, separate_checkbox, option_dialog))
        option_sizer.Add(ok_button, 0, wx.ALL | wx.CENTER, 5)
        option_dialog.SetSizer(option_sizer)
        option_dialog.Layout()
        option_dialog.Centre()

        try:
            option_dialog.ShowModal()
        except:
            logging.error(_('Error during sliding polygons calculation.'))

        option_dialog.Destroy()

    def _OnCreateSlidingPolygon(self, event, ds_text, sliding_text, farthest_text, interval_text, inter_checkbox, offset_text, separate_checkbox, option_dialog:wx.Dialog):
        """
        Handle the creation of sliding polygons based on user input from the dialog.
        """

        try:
            ds = float(ds_text.GetValue()) / 100.0  # Convert cm to m
            sliding = float(sliding_text.GetValue()) / 100.0  # Convert cm
            farthest = float(farthest_text.GetValue()) / 100.0  # Convert cm to m
            interval = float(interval_text.GetValue()) / 100.0  # Convert cm to
            intersect = inter_checkbox.GetValue()  # Boolean value
            separate = separate_checkbox.GetValue()  # Boolean value
            offset = float(offset_text.GetValue())/100.0  # Offset value in m
        except ValueError:
            wx.MessageBox(_('Please enter valid numeric values for all fields.'), _('Input Error'), wx.OK | wx.ICON_ERROR)
            return

        if separate:
            howmany = 2  # Separate left and right polygons
        else:
            howmany = 1  # Single polygon

        # #dialog box for length, sliding length, farthest parallel and parallel interval
        # dlg=wx.NumberEntryDialog(None,_('What is the desired longitudinal size [cm] ?'),'ds','ds size',5000,1,100000)
        # ret=dlg.ShowModal()
        # if ret==wx.ID_CANCEL:
        #     dlg.Destroy()
        #     return

        # ds=float(dlg.GetValue())/100.

        # dlg.Destroy()

        # dlg=wx.NumberEntryDialog(None,_('What is the desired sliding length [cm] ?'),'sliding','sliding size',5000,1,100000)
        # ret=dlg.ShowModal()
        # if ret==wx.ID_CANCEL:
        #     dlg.Destroy()
        #     return

        # sliding=float(dlg.GetValue())/100.

        # dlg.Destroy()

        # dlg=wx.NumberEntryDialog(None,_('What is the desired farthest parallel [cm] ?'),'farthest','farthest size',10000,1,100000)
        # ret=dlg.ShowModal()
        # if ret==wx.ID_CANCEL:
        #     dlg.Destroy()
        #     return

        # farthest=float(dlg.GetValue())/100.

        # dlg.Destroy()

        # dlg=wx.NumberEntryDialog(None,_('What is the desired parallel interval [cm] ?'),'interval','interval size',int(farthest*10.),1,int(farthest*100.))
        # ret=dlg.ShowModal()
        # if ret==wx.ID_CANCEL:
        #     dlg.Destroy()
        #     return

        # interval=float(dlg.GetValue())/100.

        # dlg.Destroy()

        zones_names=[curz.myname.lower() for curz in self.myzones]
        # if "intersect" in zones_names:
        #     dlg = wx.MessageDialog(None,_('Do you want to use the intersect zone ?'),style=wx.YES_NO)
        #     ret=dlg.ShowModal()
        #     if ret==wx.ID_YES:
        #         inter = True
        #     else:
        #         inter = False
        #     dlg.Destroy()
        # else:
        #     inter = False

        inter_zone = None
        if intersect:
            if "intersect" in zones_names:
                inter_zone = self.myzones[zones_names.index("intersect")]

        # dlg = wx.MessageDialog(None,_('Do you want to separate left and right polygons ?'),style=wx.YES_NO)
        # ret=dlg.ShowModal()
        # if ret==wx.ID_YES:
        #     howmany = 2
        # else:
        #     howmany = 1

        try:
            self.active_zone.create_sliding_polygon_from_parallel(ds, sliding, farthest, interval, inter_zone, howmany, eps_offset=offset)
        except:
            logging.error(_('Error during sliding polygons calculation.'))

        option_dialog.Close()


    def Oncreatebin(self,event:wx.MouseEvent):
        """
        Création d'un canal sur base de 3 parallèles
        """
        if self.wx_exists:
            if self.active_zone is None:
                return

            curz = self.active_zone

            if curz.nbvectors!=3:
                logging.warning(_('The active zone must contain 3 vectors and only 3'))

            dlg=wx.MessageDialog(None,_('Do you want to copy the center elevations to the parallel sides ?'),style=wx.YES_NO)
            ret=dlg.ShowModal()
            if ret==wx.ID_YES:
                left:LineString
                center:LineString
                right:LineString

                left = curz.myvectors[0].asshapely_ls()
                center = curz.myvectors[1].asshapely_ls()
                right = curz.myvectors[2].asshapely_ls()

                for idx,coord in enumerate(left.coords):
                    xy = Point(coord[0],coord[1])
                    curs = left.project(xy,True)
                    curz.myvectors[0].myvertices[idx].z=center.interpolate(curs,True).z

                for idx,coord in enumerate(right.coords):
                    xy = Point(coord[0],coord[1])
                    curs = right.project(xy,True)
                    curz.myvectors[2].myvertices[idx].z=center.interpolate(curs,True).z

            dlg.Destroy()

            left:LineString
            center:LineString
            right:LineString

            left = curz.myvectors[0].asshapely_ls()
            center = curz.myvectors[1].asshapely_ls()
            right = curz.myvectors[2].asshapely_ls()

            dlg=wx.NumberEntryDialog(None,_('What is the desired lateral size [cm] ?'),'ds','ds size',500,1,10000)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            addedz=float(dlg.GetValue())/100.
            dlg.Destroy()

            dlg=wx.NumberEntryDialog(None,_('How many points along center polyline ?')+'\n'+
                                        _('Length size is {} meters').format(center.length),'nb','dl size',100,1,10000)
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            nb=int(dlg.GetValue())
            dlg.Destroy()

            s = np.linspace(0.,1.,num=nb,endpoint=True)
            points=np.zeros((5*nb,3),dtype=np.float32)

            decal=0
            for curs in s:

                ptl=left.interpolate(curs,True)
                ptc=center.interpolate(curs,True)
                ptr=right.interpolate(curs,True)

                points[0+decal,:] = np.asarray([ptl.coords[0][0],ptl.coords[0][1],ptl.coords[0][2]])
                points[1+decal,:] = np.asarray([ptl.coords[0][0],ptl.coords[0][1],ptl.coords[0][2]])
                points[2+decal,:] = np.asarray([ptc.coords[0][0],ptc.coords[0][1],ptc.coords[0][2]])
                points[3+decal,:] = np.asarray([ptr.coords[0][0],ptr.coords[0][1],ptr.coords[0][2]])
                points[4+decal,:] = np.asarray([ptr.coords[0][0],ptr.coords[0][1],ptr.coords[0][2]])

                points[0+decal,2] += addedz
                points[4+decal,2] += addedz

                decal+=5

            decal=0
            triangles=[]

            nbpts=5
            triangles.append([[i+decal,i+decal+1,i+decal+nbpts] for i in range(nbpts-1)])
            triangles.append([[i+decal+nbpts,i+decal+1,i+decal+nbpts+1] for i in range(nbpts-1)])

            for k in range(1,nb-1):
                decal=k*nbpts
                triangles.append([ [i+decal,i+decal+1,i+decal+nbpts] for i in range(nbpts-1)])
                triangles.append([ [i+decal+nbpts,i+decal+1,i+decal+nbpts+1] for i in range(nbpts-1)])
            triangles=np.asarray(triangles,dtype=np.uint32).reshape([(2*nbpts-2)*(nb-1),3])

            mytri=Triangulation(pts=points,tri=triangles)
            mytri.find_minmax(True)
            fn=mytri.export_to_gltf()

            dlg=wx.MessageDialog(None,_('Do you want to add triangulation to parent gui ?'),style=wx.YES_NO)
            ret=dlg.ShowModal()
            if ret==wx.ID_YES:

                self.mapviewer.add_object('triangulation',newobj=mytri)
                self.mapviewer.Refresh()

            dlg.Destroy()

    def Oncreatemultibin(self, event:wx.MouseEvent):
        """
        Création d'une triangulation sur base de plusieurs vecteurs
        """
        if self.wx_exists:
            if self.active_zone is None:
                return

            myzone = self.active_zone

            if myzone.nbvectors<2:

                dlg = wx.MessageDialog(None,_('Not enough vectors/polylines in the active zone -- Add element and retry !!'))
                ret = dlg.ShowModal()
                dlg.Destroy()
                return

            mytri = myzone.create_multibin()

            self.mapviewer.add_object('triangulation',newobj=mytri)
            self.mapviewer.Refresh()

    def Oncreatetricrosssection(self, event:wx.MouseEvent):
        """ Create a tringulation like cross-sections and support vectors """
        if self.wx_exists:

            if self.get_mapviewer() is None:
                logging.warning(_('No mapviewer found'))
                return

            if self.active_zone is None:
                logging.warning(_('No active zone found'))
                return

            # dlg for ds value
            dlg = wx.NumberEntryDialog(None,_('What is the desired size [cm] ?'),'ds','ds size',50,1,10000)
            ret = dlg.ShowModal()
            if ret == wx.ID_CANCEL:
                dlg.Destroy()
                return

            ds = float(dlg.GetValue())/100.
            dlg.Destroy()

            myzone = self.active_zone

            mapviewer = self.get_mapviewer()
            mapviewer.set_interp_cs(myzone.create_tri_crosssection(ds), True)

    def OnconstrainedDelaunay(self, event:wx.MouseEvent):
        """
        Create a constrained Delaunay triangulation from the active zone
        """
        if self.wx_exists:
            if self.active_zone is None:
                return

            myzone = self.active_zone

            mytri = myzone.create_constrainedDelaunay()

            self.mapviewer.add_object('triangulation',newobj=mytri)
            self.mapviewer.Refresh()

    def Oncreatemultibin_project(self, event:wx.MouseEvent):
        """
        Création d'une triangulation sur base de plusieurs vecteurs
        Les sommets sont recherchés par projection d'un vecteur sur l'autre
        """
        if self.wx_exists:
            if self.active_zone is None:
                return

            myzone = self.active_zone

            if myzone.nbvectors<2:

                dlg = wx.MessageDialog(None,_('Not enough vectors/polylines in the active zone -- Add element and retry !!'))
                ret = dlg.ShowModal()
                dlg.Destroy()
                return

            mytri = myzone.createmultibin_proj()
            self.mapviewer.add_object('triangulation',newobj=mytri)
            self.mapviewer.Refresh()

    def save_images_fromvec(self, dir=''):
        """
        Sauvegarde d'images des vecteurs dans un répertoire

        FIXME : pas encore vraiment au point
        """
        if dir=='':
            if self.wx_exists:
                dlg = wx.DirDialog(None,"Choose directory to store images",style=wx.FD_SAVE)
                ret=dlg.ShowModal()

                if ret==wx.ID_CANCEL:
                    dlg.Destroy()
                    return

                dir = dlg.GetPath()
                dlg.Destroy()

        if dir=='':
            return

        for curzone in self.myzones:
            for curvec in curzone.myvectors:
                if curvec.nbvertices>1:
                    oldwidth=curvec.myprop.width
                    curvec.myprop.width=4
                    myname = curvec.myname

                    self.Activate_vector(curvec)

                    if self.mapviewer is not None:
                        if self.mapviewer.linked:
                            for curview in self.mapviewer.linkedList:
                                title = curview.GetTitle()
                                curview.zoomon_activevector()
                                fn = path.join(dir,title + '_' + myname+'.png')
                                curview.save_canvasogl(fn)
                        else:
                            self.mapviewer.zoomon_activevector()
                            fn = path.join(dir,myname+'.png')
                            self.mapviewer.save_canvasogl(fn)

                            fn = path.join(dir,'palette_v_' + myname+'.png')
                            self.mapviewer.active_array.mypal.export_image(fn,'v')
                            fn = path.join(dir,'palette_h_' + myname+'.png')
                            self.mapviewer.active_array.mypal.export_image(fn,'h')

                    curvec.myprop.width = oldwidth

    def Oninsert(self, event:wx.MouseEvent):
        """
        Insertion de vertex dans le vecteur courant
        """
        if self.wx_exists:
            if self.verify_activevec():
                return

            self.mapviewer.start_action('insert vertices', _('Insert vertices'))
            self.mapviewer.mimicme()

            self.active_zone.reset_listogl()

    def Onsplit(self, event:wx.MouseEvent):
        """
        Split le vecteur courant selon un pas spatial déterminé
        """
        if self.wx_exists:
            if self.verify_activevec():
                return

        dlg=wx.NumberEntryDialog(None,_('What is the desired longitudinal size [cm] ?'),'ds','ds size',100,1,100000)
        ret=dlg.ShowModal()
        if ret==wx.ID_CANCEL:
            dlg.Destroy()
            return

        ds=float(dlg.GetValue())/100.
        dlg.Destroy()

        self.active_vector.split(ds)

    def Onevaluates(self, event:wx.MouseEvent):
        """
        Calcule la position curviligne du vecteur courant

        Le calcul peut être mené en 2D ou en 3D
        Remplissage du tableur dans la 5ème colonne
        """
        if self.wx_exists:
            if self.verify_activevec():
                return

        curv = self.active_vector
        curv.update_lengths()

        dlg = wx.SingleChoiceDialog(None, "Which mode?", "How to evaluate lengths?", ['2D','3D'])
        ret=dlg.ShowModal()

        if ret==wx.ID_CANCEL:
            dlg.Destroy()
            return

        method=dlg.GetStringSelection()
        dlg.Destroy()

        self.xls.SetCellValue(0,4,'0.0')
        s=0.
        if method=='2D':
            for k in range(curv.nbvertices-1):
                s+=curv._lengthparts2D[k]
                self.xls.SetCellValue(k+1,4,str(s))
        else:
            for k in range(curv.nbvertices-1):
                s+=curv._lengthparts3D[k]
                self.xls.SetCellValue(k+1,4,str(s))

    def Onupdate_from_sz_support(self, event:wx.MouseEvent):
        """ Update the active vector from the sz values in the xls grid """

        if self.active_vector is None:
            logging.info(_('No active vector -- Nothing to do'))
            return

        sz = []

        # Getting s values and Z values from the xls grid
        # s in column 4 and z in column 2
        # The first row is the header
        nbrows = self.xls.GetNumberRows()
        if self.xls.GetCellValue(nbrows-1,4) != '':
            self.xls.AppendRows(1)
        i = 0
        while self.xls.GetCellValue(i,4) != '':
                s = self.xls.GetCellValue(i,4)
                z = self.xls.GetCellValue(i,2)
                try:
                    s = float(s)
                except:
                    logging.error(_('Error during update from sz support - check your s data and types (only float)'))
                    return

                try:
                    if z == '':
                        logging.warning(_('No z value -- setting to 0.0'))
                        z = 0.0
                    else:
                        z = float(z)
                except:
                    logging.error(_('Error during update from sz support - check your z data and types (only float)'))
                    return

                sz.append((s, z))
                i += 1

        if len(sz) == 0:
            logging.warning(_('No data to update -- Please set s in column "s curvi" (5th) and z in column Z (3th)'))
            return

        logging.info(f'Number of points: {len(sz)}')

        vec_sz = np.array(sz)

        memory_xyz = []
        i = 0
        while self.xls.GetCellValue(i,0) != '':
            memory_xyz.append((float(self.xls.GetCellValue(i,0)), float(self.xls.GetCellValue(i,1)), float(self.xls.GetCellValue(i,2))))
            i += 1

        try:
            self.update_from_sz_support(vec=self.active_vector, sz=vec_sz)

            # update of the xls grid
            for k in range(self.active_vector.nbvertices ):
                self.xls.SetCellValue(k,0,str(self.active_vector.myvertices[k].x))
                self.xls.SetCellValue(k,1,str(self.active_vector.myvertices[k].y))
        except:
            logging.error(_('Error during update from sz support - check your data'))
            logging.info(_('Resetting the active vector to its original state'))

            self.active_vector.myvertices = []
            for cur in memory_xyz:
                self.active_vector.add_vertex(wolfvertex(cur[0], cur[1], cur[2]))
            self.active_vector._reset_listogl()
            self.active_vector.update_lengths()
            self.active_vector.find_minmax(True)

            for k in range(self.active_vector.nbvertices ):
                self.xls.SetCellValue(k,0,str(self.active_vector.myvertices[k].x))
                self.xls.SetCellValue(k,1,str(self.active_vector.myvertices[k].y))

    def update_from_sz_direction(self, xy1:np.ndarray, xy2:np.ndarray, sz:np.ndarray):
        """ Update the active vector from the sz values in the xls grid """

        if self.active_vector is None:
            logging.info(_('No active vector -- Nothing to do'))
            return

        curv = self.active_vector

        # Creation of vertices
        if sz.shape[1]==2 and xy1.shape==(2,) and xy2.shape==(2,):
            if not np.array_equal(xy1,xy2):
                curv.myvertices=[]

                dx, dy = xy2[0]-xy1[0], xy2[1]-xy1[1]
                norm = np.linalg.norm([dx,dy])
                dx, dy = dx/norm, dy/norm

                for cur in sz:
                    x, y = xy1[0] + dx*cur[0], xy1[1] + dy*cur[0]
                    curv.add_vertex(wolfvertex(x, y, float(cur[1])))

        self.find_minmax(True)

    def update_from_sz_support(self,
                               vec: vector,
                               sz:np.ndarray,
                               dialog_box = True,
                               method:Literal['2D', '3D'] = '3D'):
        """ Update the coordinates from the support vector and a sz array.

        The support vector is used to interpolate the z values, at the s values.
        It must long enough to cover the s values.

        :param vec: The vector to update. It is also the support vector.
        :param sz: The sz array to use for the update
        :param dialog_box: If True, a dialog box will be shown to choose the method
        :param method: The method to use for the interpolation. '2D' or '3D'
        """

        if sz.shape[0] ==0:
            logging.warning(_('No data to update'))
            return

        support_vec = vec.deepcopy_vector()
        support_vec.update_lengths()

        if support_vec.length2D is None or support_vec.length3D is None:
            logging.warning(_('The support vector must be updated before updating the active vector'))
            return

        if dialog_box:
            dlg = wx.SingleChoiceDialog(None, "Which mode?", "How to evaluate lengths?", ['2D','3D'])
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            method=dlg.GetStringSelection()
            dlg.Destroy()
        # else:
        #     method = '2D'

        if method not in ['2D', '3D']:
            logging.warning(_('Method not supported -- only 2D and 3D are supported'))
            return

        if method == '2D':
            if sz[-1,0] > support_vec.length2D:
                logging.warning(_('The last point is beyond the vector length. You must add more points !'))
                return
        else:
            if sz[-1,0] > support_vec.length3D:
                logging.warning(_('The last point is beyond the vector length. You must add more points !'))
                return

        vec.myvertices = []
        for s,z in sz:
            new_vertex = support_vec.interpolate(s, method == method, adim= False)
            new_vertex.z = z
            vec.add_vertex(new_vertex)

        vec._reset_listogl()
        vec.update_lengths()

        self.find_minmax(True)

    def evaluate_s(self, vec: vector =None, dialog_box = True):
        """
        Calcule la position curviligne du vecteur encodé.

        Le calcul peut être mené en 2D ou en 3D.
        Remplissage du tableur dans la 5ème colonne.
        """

        curv = vec
        curv.update_lengths()

        if dialog_box:
            dlg = wx.SingleChoiceDialog(None, "Which mode?", "How to evaluate lengths?", ['2D','3D'])
            ret=dlg.ShowModal()
            if ret==wx.ID_CANCEL:
                dlg.Destroy()
                return

            method=dlg.GetStringSelection()
            dlg.Destroy()
        else:
            method = '2D'

        self.xls.SetCellValue(0,4,'0.0')
        s=0.
        if curv.nbvertices > 0:
            if method=='2D':
                for k in range(curv.nbvertices-1):
                    s+=curv._lengthparts2D[k]
                    self.xls.SetCellValue(k+1,4,str(s))
            else:
                for k in range(curv.nbvertices-1):
                    s+=curv._lengthparts3D[k]
                    self.xls.SetCellValue(k+1,4,str(s))

    def Oninterpvec(self, event:wx.MouseEvent):
        """
        Interpole les valeurs Z de l'éditeur sur base des seules valeurs connues,
        càd autre que vide ou -99999
        """
        if self.verify_activevec():
            return

        curv = self.active_vector

        s=[]
        z=[]

        for k in range(curv.nbvertices):
            zgrid = self.xls.GetCellValue(k,2)
            sgrid = self.xls.GetCellValue(k,4)
            if zgrid!='' and float(zgrid)!=-99999.:
                z.append(float(zgrid))
                s.append(float(sgrid))

        if len(z)==0:
            return

        f = interp1d(s,z)

        for k in range(curv.nbvertices):
            zgrid = self.xls.GetCellValue(k,2)
            sgrid = self.xls.GetCellValue(k,4)
            if zgrid=='' or float(zgrid)==-99999.:
                z = f(float(sgrid))
                self.xls.SetCellValue(k,2,str(z))

    def Onupdatevertices(self,event):
        """
        Mie à jour des vertices sur base du tableur
        """
        if self.verify_activevec():
            return

        self.active_vector.updatefromgrid(self.xls)
        self.find_minmax(True)

    def Ontest_interior(self, event:wx.MouseEvent):
        """ Test if the active vector has interior portions """
        if self.verify_activevec():
            return

        self.active_vector.check_if_interior_exists()

        self.active_vector._fillgrid_only_i(self.xls)

        self.get_mapviewer().Paint()


    def Onplotmpl(self, event:wx.MouseEvent):
        """
        Plot active vector in matplotlib
        """

        if self.verify_activevec():
            return

        fig, ax = plt.subplots()
        self.active_vector.plot_matplotlib(ax)
        ax.set_aspect('equal')
        fig.show()

    def Onplotmplsz(self, event:wx.MouseEvent):
        """
        Plot active vector in matplotlib with sz values
        """
        if self.verify_activevec():
            return

        fig, ax = plt.subplots()
        s, z = self.active_vector.sz_curvi
        ax.plot(s, z)
        ax.set_xlabel('s')
        ax.set_ylabel('z')
        fig.show()

    def Onaddrows(self, event:wx.MouseEvent):
        """
        Ajout de lignes au tableur
        """
        if self.wx_exists:
            nbrows=None
            dlg=wx.TextEntryDialog(None,_('How many rows?'),value='1')
            while nbrows is None:
                rc = dlg.ShowModal()
                if rc == wx.ID_OK:
                    nbrows = int(dlg.GetValue())
                    self.xls.AppendRows(nbrows)
                else:
                    return

    def OnClickadd_zone(self, event:wx.MouseEvent):
        """
        Ajout d'une zone au GUI
        """
        if self.wx_exists:
            curname=None
            dlg=wx.TextEntryDialog(None,_('Choose a name for the new zone'),value='New_Zone')
            while curname is None:
                rc = dlg.ShowModal()
                if rc == wx.ID_OK:
                    curname = str(dlg.GetValue())
                    newzone = zone(name=curname,parent=self)
                    self.add_zone(newzone)
                    self.fill_structure()
                    self.active_zone = newzone
                else:
                    return

    def OnClickadd_vector(self, event:wx.MouseEvent):
        """
        Ajout d'un vecteur à la zone courante
        """

        if self.active_zone is None:
            logging.warning(_('No active zone - Can not add a vector to None !'))
            logging.warning(_('Please activate a zone first'))
            return

        if self.wx_exists:
            curname=None
            dlg=wx.TextEntryDialog(None,_('Choose a name for the new vector'),value='New_Vector')
            while curname is None:
                rc = dlg.ShowModal()
                if rc == wx.ID_OK:
                    curname = str(dlg.GetValue())
                    newvec = vector(name=curname,parentzone=self.active_zone)
                    self.active_zone.add_vector(newvec)
                    self.fill_structure()
                    self.Activate_vector(newvec)
                else:
                    return

    def OnClickduplicate_zone(self, event:wx.MouseEvent):
        """ Duplication de la zone active """
        if self.wx_exists:
            if self.verify_activezone():
                return

            newzone = self.active_zone.deepcopy_zone()
            newzone.myname = self.active_zone.myname + '_copy'
            self.add_zone(newzone, forceparent=True)
            self.fill_structure()
            self.Activate_zone(newzone)

    def OnClickduplicate_vector(self, event:wx.MouseEvent):
        """
        Duplication du vecteur actif
        """

        if self.active_vector is None:
            logging.warning(_('No active vector - Can not duplicate None !'))
            logging.warning(_('Please activate a vector first'))
            return

        if self.wx_exists:
            if self.verify_activevec():
                return

            newvec = self.active_vector.deepcopy_vector()
            newvec.myname = self.active_vector.myname + '_copy'
            self.active_zone.add_vector(newvec, forceparent=True)
            self.fill_structure()
            self.Activate_vector(newvec)

    def OnClickdelete_zone(self, event:wx.MouseEvent):
        """
        Suppression de la zone courante
        """

        if self.active_zone is None:
            logging.warning(_('No active zone - Can not delete None !'))
            logging.warning(_('Please activate a zone first'))
            return

        if self.wx_exists:
            curname=self.active_zone.myname
            r = wx.MessageDialog(
                None,
                _('The zone {n} will be deleted. Continue?').format(n=curname),
                style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                ).ShowModal()

            if r != wx.ID_YES:
                return

            self.delete_zone(self.active_zone)

    def delete_zone(self, zone_to_del:zone, update_ui:bool=True):
        """
        Delete a zone from this Zones.

        :param zone: Zone to delete
        :param update_ui: if `True` reflects the deleteion in the user
            interface.
        """
        assert zone_to_del is not None, "None can't be deleted"
        assert zone_to_del in self.myzones, "The zone you rpovided is nowhere to be found"

        # Even if one destroys the zone in the Zones, the active vector may
        # still have a reference to it. In that case it will continue to be
        # drawn in PyDraw and we don't want that.

        if self.active_vector is not None:
            self.Activate_vector(None)

        if self.active_zone == zone_to_del:
            self.Activate_zone(None)

        self.myzones.remove(zone_to_del)

        # Vectors of this zone are drawn into an opengl list. So if we clear the
        # list, then we clear the vectors too. Zones class has no GL list.
        zone_to_del.reset_listogl()

        if update_ui:
            self.fill_structure()
            self.find_minmax(True)
            if self.get_mapviewer() is not None:
                self.get_mapviewer().Paint()

    def delete_all_zones(self):
        """
        Delete all zone's from this Zones.
        """
        for zone in set(self.myzones): # a set so that I don't iterate over myzones and delete from it simultaneously
            self.delete_zone(zone, update_ui=False)

        self.fill_structure()
        self.find_minmax(True)
        if self.get_mapviewer() is not None:
            self.get_mapviewer().Paint()

    def OnClickfindactivate_vector(self, event:wx.MouseEvent):
        """
        Recherche et activation d'un vecteur dans toutes les zones
        """
        if self.wx_exists:

            dlg=wx.MessageDialog(None,"Search only closed polyline?",style=wx.YES_NO)
            ret=dlg.ShowModal()
            dlg.Destroy()

            if ret==wx.YES:
                self.mapviewer.start_action('select active vector inside', _('Select active vector inside'))
            else:
                self.mapviewer.start_action('select active vector all', _('Select active vector all'))

            self.mapviewer.active_zones=self

    def OnClickfindactivate_vector2(self, event:wx.MouseEvent):
        """
        Recherche et activation d'un vecteur dans la zone courante
        """
        if self.wx_exists:

            dlg=wx.MessageDialog(None,"Search only closed polyline?",style=wx.YES_NO)
            ret=dlg.ShowModal()
            dlg.Destroy()

            if ret==wx.YES:
                self.mapviewer.start_action('select active vector2 inside', _('Select active vector2 inside'))
            else:
                self.mapviewer.start_action('select active vector2 all', _('Select active vector2 all'))

            self.mapviewer.active_zone=self.active_zone
            self.mapviewer.active_zones=self

    def get_selected_vectors(self, all=False):
        """
        all = True  : Récupération et renvoi des vecteurs sélectionnés dans les zones
        all = False : Récupération et renvoi du vecteur le plus proche
        """
        if all:
            mylist=[]
            for curzone in self.myzones:
                ret = curzone.get_selected_vectors(all)
                if ret is not None:
                    mylist.append(ret)
            return mylist
        else:
            distmin=99999.
            vecmin:vector = None
            for curzone in self.myzones:
                ret = curzone.get_selected_vectors()
                if ret is not None:
                    if (ret[1]<distmin) or (vecmin is None):
                        distmin= ret[1]
                        vecmin = ret[0]

            return vecmin

    def verify_activevec(self):
        """
        Vérifie si un vecteur actif est défini, si 'None' affiche un message

        Return :
           True if self.active_vector is None
           False otherwise
        """
        if self.active_vector is None:
            if self.wx_exists:
                msg=''
                msg+=_('Active vector is None\n')
                msg+=_('\n')
                msg+=_('Retry !\n')
                wx.MessageBox(msg)
            else:
                logging.warning(_('Active vector is None - Retry !'))
            return True
        return False

    def verify_activezone(self):
        """
        Vérifie si une zone active est définie, si 'None' affiche un message

        Return :
           True if self.active_zone is None
           False otherwise
        """
        if self.active_zone is None:
            if self.wx_exists:
                msg=''
                msg+=_('Active zone is None\n')
                msg+=_('\n')
                msg+=_('Retry !\n')
                wx.MessageBox(msg)
            return True
        return False

    def OnClickdelete_vector(self, event:wx.MouseEvent):
        """
        Suppression du vecteur actif
        """
        if self.wx_exists:
            if self.verify_activevec():
                return

            curname=self.active_vector.myname
            r = wx.MessageDialog(None, _('The vector {n} will be deleted. Continue?').format(n=curname), style=wx.YES_NO | wx.ICON_QUESTION).ShowModal()

            if r != wx.ID_YES:
                return

            actzone =self.active_zone

            if actzone.nbvectors==0:
                return

            idx = int(actzone.myvectors.index(self.active_vector))
            if idx >= 0 and idx < actzone.nbvectors:
                actzone.reset_listogl()
                actzone.myvectors.pop(idx)

                if actzone.nbvectors == 0:
                    self.Activate_vector(None)
                elif idx < actzone.nbvectors:
                    self.Activate_vector(actzone.myvectors[idx])
                else:
                    self.Activate_vector(actzone.myvectors[-1])

                self.fill_structure()
                self.find_minmax(True)

            if self.get_mapviewer() is not None:
                self.get_mapviewer().Paint()


    def OnClickup_vector(self, event:wx.MouseEvent):
        """Remonte le vecteur actif dans la liste de la zone"""
        if self.verify_activevec():
            return

        for idx,curv in enumerate(self.active_zone.myvectors):

            if curv == self.active_vector:
                if idx==0:
                    return
                self.active_zone.myvectors.pop(idx)
                self.active_zone.myvectors.insert(idx-1,curv)

                self.fill_structure()

                break

    def OnClickdown_vector(self, event:wx.MouseEvent):
        """Descend le vecteur actif dans la liste de la zone"""
        if self.verify_activevec():
            return

        for idx,curv in enumerate(self.active_zone.myvectors):

            if curv == self.active_vector:
                if idx==self.active_zone.nbvectors:
                    return
                self.active_zone.myvectors.pop(idx)
                self.active_zone.myvectors.insert(idx+1,curv)

                self.fill_structure()

                break

    def OnClickup_zone(self, event:wx.MouseEvent):
        """Remonte la zone active dans la liste de la zones self"""

        for idx,curz in enumerate(self.myzones):

            if curz == self.active_zone:
                if idx==0:
                    return
                self.myzones.pop(idx)
                self.myzones.insert(idx-1,curz)

                self.fill_structure()

                break

    def OnClickdown_zone(self, event:wx.MouseEvent):
        """Descend la zone active dans la liste de la zones self"""
        for idx,curz in enumerate(self.myzones):

            if curz == self.active_zone:
                if idx==self.nbzones:
                    return
                self.myzones.pop(idx)
                self.myzones.insert(idx+1,curz)

                self.fill_structure()

                break

    def unuse(self):
        """
        Rend inutilisé l'ensemble des zones
        """
        for curzone in self.myzones:
            curzone.unuse()

    def use(self):
        """
        Rend utilisé l'ensemble des zones
        """
        for curzone in self.myzones:
            curzone.use()

    def OnCheckItem(self, event:wx.MouseEvent):
        """
        Coche/Décoche un ékement de la treelist
        """
        if self.wx_exists:
            myitem=event.GetItem()
            check = self.treelist.GetCheckedState(myitem)
            myitemdata=self.treelist.GetItemData(myitem)
            if check:
                myitemdata.use()
            else:
                myitemdata.unuse()

    def _callback_destroy_props(self):

        self.myprops = None

    def _callback_prop(self):

        if self._myprops is None:
            logging.warning(_('No properties available'))
            return

        for curzone in self.myzones:
            for curvec in curzone.myvectors:
                curvec.myprop.fill_property(self._myprops, updateOGL = False)

        posx = self._myprops[('Move','Start X')]
        posy = self._myprops[('Move','Start Y')]
        if posx != 99999. and posy != 99999.:
            self._move_start = (posx,posy)
        else:
            self._move_start = None

        step = self._myprops[('Move','Step [m]')]
        if step != 99999.:
            self._move_step = step
        else:
            self._move_step = None

        posx = self._myprops[('Rotation','Center X')]
        posy = self._myprops[('Rotation','Center Y')]
        if posx != 99999. and posy != 99999.:
            self._rotation_center = (posx,posy)
        else:
            self._rotation_center = None

        step = self._myprops[('Rotation','Step [degree]')]
        if step != 99999.:
            self._rotation_step = step
        else:
            self._rotation_step = None

        angle = self._myprops[('Rotation','Angle [degree]')]
        dx = self._myprops[('Move','Delta X')]
        dy = self._myprops[('Move','Delta Y')]

        if angle != 0. and (dx!= 0. or dy!=0.):
            logging.error(_('Rotation and move are not compatible - Choose one and only one'))
        elif angle!= 0.:
            if self._rotation_center is None:
                logging.error(_('No rotation center defined - Choose one'))
            else:
                self.rotate(angle, self._rotation_center)
                self.clear_cache()
        elif dx!= 0. or dy!=0.:
            self.move(dx,dy)
            self.clear_cache()

        if self.mapviewer is not None:
            self.prep_listogl()
            self.mapviewer.Refresh()


    def _edit_all_properties(self):
        """ Show properties of the zone --> will be applied to all vectors int he zone """

        if self._myprops is None:
            locvec = vector()
            locvec.show_properties()

            self._myprops = locvec.myprop.myprops

        self._myprops[('Legend','X')] = str(99999.)
        self._myprops[('Legend','Y')] = str(99999.)
        self._myprops[('Legend','Text')] = _('Not used')

        if self._rotation_center is not None:
            self._myprops[('Rotation', 'Center X')] = self._rotation_center[0]
            self._myprops[('Rotation', 'Center Y')] = self._rotation_center[1]
        else:
            self._myprops[('Rotation', 'Center X')] = 99999.
            self._myprops[('Rotation', 'Center Y')] = 99999.

        if self._rotation_step is not None:
            self._myprops[('Rotation', 'Step [degree]')] = self._rotation_step
        else:
            self._myprops[('Rotation', 'Step [degree]')] = 99999.

        self._myprops['Rotation', 'Angle [degree]'] = 0.

        if self._move_start is not None:
            self._myprops[('Move', 'Start X')] = self._move_start[0]
            self._myprops[('Move', 'Start Y')] = self._move_start[1]
        else:
            self._myprops[('Move', 'Start X')] = 99999.
            self._myprops[('Move', 'Start Y')] = 99999.

        self._myprops[('Move', 'Delta X')] = 0.
        self._myprops[('Move', 'Delta Y')] = 0.

        if self._move_step is not None:
            self._myprops[('Move', 'Step [m]')] = self._move_step
        else:
            self._myprops[('Move', 'Step [m]')] = 99999.

        self._myprops.Populate()
        self._myprops.set_callbacks(self._callback_prop, self._callback_destroy_props)

        self._myprops.SetTitle(_('Properties for all vectors in {}'.format(self.filename)))
        self._myprops.Center()
        self._myprops.Raise()


    def OnRDown(self, event:TreeListEvent):
        """
        Affiche les propriétés du vecteur courant
        Clicl-droit
        """
        if self.wx_exists:
            if self.active_zone is None and self.active_zone is None:

                logging.info(_('You will edit the properties of the entire instance (all zones and all vectors)'))
                self._edit_all_properties()

            elif isinstance(self.last_active, vector):
                self.active_vector.show_properties()

            elif isinstance(self.last_active, zone):
                self.active_zone.show_properties()

    def OnActivateItem(self, event:TreeListEvent):
        """
        Activation d'un élément dans le treelist
        """
        if self.wx_exists:
            myitem=event.GetItem()
            myitemdata=self.treelist.GetItemData(myitem)

            if isinstance(myitemdata,vector):
                self.Activate_vector(myitemdata)
            elif isinstance(myitemdata,zone):
                self.Activate_zone(myitemdata)
            else:
                self.Activate_vector(None)
                self.Activate_zone(None)

            self.last_active = myitemdata

    def Activate_vector(self, object:vector):
        """
        Mémorise l'objet passé en argument comme vecteur actif

        Pousse la même information dans l'objet parent s'il existe
        """
        if self.wx_exists:
            self.active_vector = object

            if self.active_vector is None:
                logging.info(_('Active vector is now set to None'))
                if self.xls is not None:
                    self.labelactvect.SetLabel('None')
                    self.xls.ClearGrid()
                if self.parent is not None:
                    try:
                        self.parent.Active_vector(self.active_vector)
                    except:
                        raise Warning(_('Not supported in the current parent -- see PyVertexVectors in Activate_vector function'))
                return

            if self.xls is not None:
                self.xls_active_vector()

            if object.parentzone is not None:
                self.active_zone = object.parentzone
                object.parentzone.active_vector = object

            if self.parent is not None:
                try:
                    self.parent.Active_vector(self.active_vector)
                except:
                    raise Warning(_('Not supported in the current parent -- see PyVertexVectors in Activate_vector function'))

            if self.xls is not None:
                self.labelactvect.SetLabel(self.active_vector.myname)
                self.labelactzone.SetLabel(self.active_zone.myname)
                self.Layout()

    def Activate_zone(self, object:zone):
        """
        Mémorise l'objet passé en argument comme zone active

        Pousse la même information dans l'objet parent s'il existe
        """

        if self.wx_exists:
            self.active_zone = object

            if self.active_zone is None:
                logging.info(_('Active zone is now set to None'))
                self.labelactzone.SetLabel('None')
                self.xls.ClearGrid()
                return

            if object.active_vector is not None:
                self.active_vector = object.active_vector
            elif object.nbvectors>0:
                self.Activate_vector(object.myvectors[0])

            if self.active_vector is None:
                logging.warning(_('No vector in the active zone'))
                if self.parent is not None:
                    try:
                        self.parent.Active_zone(self.active_zone)
                    except:
                        raise Warning(_('Not supported in the current parent -- see PyVertexVectors in Activate_zone function'))
            else:
                self.labelactvect.SetLabel(self.active_vector.myname)

            if self.labelactzone is not None:
                self.labelactzone.SetLabel(self.active_zone.myname)
            self.Layout()

    def xls_active_vector(self):
        """
        Remplit le tableur
        """
        if self.wx_exists:
            if self.xls is not None:
                self.xls.ClearGrid()
                self.active_vector.fillgrid(self.xls)

    def OnEditLabel(self, event:wx.MouseEvent):
        """
        Edition de la clé/label de l'élément actif du treelist
        """
        if self.wx_exists:

            key=event.GetKeyCode()

            if key==wx.WXK_F2:
                if self.last_active is not None:
                    curname=None
                    dlg=wx.TextEntryDialog(None,_('Choose a new name'), value=self.last_active.myname)
                    while curname is None:
                        rc = dlg.ShowModal()
                        if rc == wx.ID_OK:
                            curname = str(dlg.GetValue())
                            dlg.Destroy()
                            self.last_active.myname = curname
                            self.fill_structure()
                        else:
                            dlg.Destroy()
                            return

    def deepcopy_zones(self, name:str = None) -> "Zones":
        """
        Return the deep copy of the current
        Zones (a new object).
        """
        copied_Zones = Zones(idx=name)
        copied_Zones.myzones = list(map(lambda zne: zne.deepcopy_zone(parent= copied_Zones), self.myzones))
        # for zne in self.myzones:
        #     new_zne = zne.deepcopy_zone(parent= copied_Zones)
        #     copied_Zones.add_zone(new_zne,forceparent=True)
        copied_Zones.find_minmax(True)
        return copied_Zones

    def deepcopy(self, name:str = None) -> "Zones":
        """
        Return the deep copy of the current
        Zones (a new object).
        """
        return self.deepcopy_zones(name=name)

class Grid(Zones):
    """
    Grid to draw on the mapviewer.

    Contains one zone and 3 vectors (gridx, gridy, contour).

    Each gridx and gridy vector contains vertices forming a continuous line.
    Contour vector contains 4 vertices forming a closed polyline.

    Drawing all the elements on the mapviewer allows to draw a grid.

    Based on spatial extent and resolution.
    """

    def __init__(self,
                 size:float=1000.,
                 ox:float=0.,
                 oy:float=0.,
                 ex:float=1000.,
                 ey:float=1000.,
                 parent=None):

        super().__init__(ox=ox, oy=oy, parent=parent)

        mygrid=zone(name='grid',parent=self)
        self.add_zone(mygrid)

        gridx=vector(name='gridx')
        gridy=vector(name='gridy')
        contour=vector(name='contour')

        mygrid.add_vector(gridx)
        mygrid.add_vector(gridy)
        mygrid.add_vector(contour)

        self.creategrid(size,ox,oy,ex,ey)

    def creategrid(self,
                   size:float=100.,
                   ox:float=0.,
                   oy:float=0.,
                   ex:float=1000.,
                   ey:float=1000.):

        mygridx=self.myzones[0].myvectors[0]
        mygridy=self.myzones[0].myvectors[1]
        contour=self.myzones[0].myvectors[2]
        mygridx.reset()
        mygridy.reset()
        contour.reset()

        locox=int(ox/size)*size
        locoy=int(oy/size)*size
        locex=(np.ceil(ex/size))*size
        locey=(np.ceil(ey/size))*size

        nbx=int(np.ceil((locex-locox)/size))
        nby=int(np.ceil((locey-locoy)/size))

        dx=locex-locox
        dy=locey-locoy

        #grillage vertical
        xloc=locox
        yloc=locoy
        for i in range(nbx):
            newvert=wolfvertex(xloc,yloc)
            mygridx.add_vertex(newvert)

            yloc+=dy
            newvert=wolfvertex(xloc,yloc)
            mygridx.add_vertex(newvert)

            xloc+=size
            dy=-dy

        #grillage horizontal
        xloc=locox
        yloc=locoy
        for i in range(nby):
            newvert=wolfvertex(xloc,yloc)
            mygridy.add_vertex(newvert)

            xloc+=dx
            newvert=wolfvertex(xloc,yloc)
            mygridy.add_vertex(newvert)

            yloc+=size
            dx=-dx

        newvert=wolfvertex(locox,locoy)
        contour.add_vertex(newvert)
        newvert=wolfvertex(locex,locoy)
        contour.add_vertex(newvert)
        newvert=wolfvertex(locex,locey)
        contour.add_vertex(newvert)
        newvert=wolfvertex(locox,locey)
        contour.add_vertex(newvert)

        self.find_minmax(True)