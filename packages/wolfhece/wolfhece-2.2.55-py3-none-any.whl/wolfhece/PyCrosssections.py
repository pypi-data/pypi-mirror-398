"""
Author: HECE - University of Liege, Pierre Archambeau, Utashi Ciraane Docile
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from numpy import asarray,ndarray,arange,zeros,linspace,concatenate,unique,amin,amax
import math
import matplotlib.pyplot as plt
from shapely.geometry import LineString,MultiLineString,Point,Polygon,CAP_STYLE,Point
from shapely import prepare, is_prepared, destroy_prepared
from shapely.ops import nearest_points,substring
from OpenGL.GL  import *
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from os import path
import pygltflib
import typing
import copy
from enum import Enum
import logging
import wx
from typing import Union, Literal
from pathlib import Path
import pandas as pd
from numba import njit

from .PyTranslate import _
from .drawing_obj import Element_To_Draw
from .PyVertexvectors import vector,zone,Zones
from .PyVertex import wolfvertex,cloud_vertices, getIfromRGB
from .lazviewer.laz_viewer import xyz_laz_grids, myviewer

example_largesect="""-138 100
-114 90
-70 80
-45 70
-32 62
0 61.5
32 62
60 70
80 80
98 84
120 87"""

example_smallsect="""0 68
10 67
12 65
15 63
20 62
24 61.5
30 62
35 64
40 66
42 66.5
50 68"""

example_diffsect1="""0 10
10 5
12 5
15 6
16 6
17 5
20 3
25 3
30 5
42 7
50 10"""

@njit
def INTERSEC(x1:float, y1:float, x2:float, y2:float, el:float):
    """Procédure de calcul de l'abscisse d'intersection d'une altitude donnée el
    dans un segment défini par ses coordonnées (x1,y1) et (x2,y2)"""
    xx=1.0e10

    if x2-x1==0.:
        if y2>y1:
            if y1<=el<=y2:
                return x2
        elif y2<y1:
            if y2<=el<=y1:
                return x2
    elif 0.0<abs(y2-y1):
        a=(y2-y1)/(x2-x1)
        b=(x2*y1-x1*y2)/(x2-x1)
        xx=(el-b)/a
    return xx

def _shift_np(base:np.ndarray, x:float, y:float):
    """ Copy a Numpy array and translate it by (x,y) in the XY plane """

    copie = base.copy()
    copie[:,0] += x
    copie[:,1] += y
    return copie

@njit
def _find_shift_at_xy(section:np.ndarray, x3:float, y3:float):
    """ Find the Delta X and Delta Y to shift a section
    to be parallel to itself at point (x3,y3) """

    x1 = section[0,0]
    y1 = section[0,1]
    x2 = section[-1,0]
    y2 = section[-1,1]

    if x2==x1:
        y4 = y3
        x4 = x1
    else:
        a = (y2-y1)/(x2-x1)
        b = y1-(a*x1)

        # vecteur = ([1,a])
        # normale = ([-a,1])
        # normale_opposée = ([a,-1])

        c = -1/a
        d = y3-(c*x3)

        x4 = (d-b)/(a-c)
        y4 = a*x4 + b

    x = (x3-x4)
    y = (y3-y4)

    return x,y

class postype(Enum):
    """
    Mode de stockage des points de référence (berges, fond lit)
    """
    BY_VERTEX   = 0 # sur base de coordonnées (wolfvertex)
    BY_S3D      = 1 # sur base d'une position curviligne 3D (le long de la trace de la section)
    BY_INDEX    = 2 # sur base d'un index de vertex

class profile(vector):
    """
    Subclass of a vector to define a river profile/cross-section.

    Some attributes are added to manage specific points of the profile (banks, bed).
    The bankleft, bankright, bed, bankleft_down, bankright_down attributes can be wolfvertex,
    index of vertex or s3D position depending on banksbed_postype.

    If a profile is part of a croossection object, the parent attribute points to it.
    If the profiles are ordered along a river, the up and down attributes point to the upstream and downstream profiles.

    sdatum and zdatum are offsets to be added to the curvilinear abscissa and altitudes of the profile.

    The stored coordinates are in 3D (x, y, z). If data_sect is provided at initialization, we expect (X, Z) data.
    The x coordinate is the curvilinear abscissa along the section and z is the altitude (y is set to 0).

    ATTENTION:
        Normally, a profile is a succession of points in a vertical plane, aligned along a trace.
        In this implementation, the points can be in 3D space, not necessarily aligned.
        Some routines have a 'cumul' parameter to compute the curvilinear abscissa along the section.
        If 'cumul' is True, the real curvilinear abscissa is computed.
        If 'cumul' is False, the distance **between each point and the first point** is computed.
    """

    def __init__(self, name:str, data_sect:str | np.ndarray | list | vector = '', parent = None) -> None:
        """ Initialization of a profile

        :param name: name of the profile
        :param data_sect: section data as a string (x z) separated by spaces and line breaks
        :param parent: parent object (crosssections)
        """

        super().__init__(name=name)

        if not isinstance(data_sect, (str, np.ndarray, list, vector)):
            raise TypeError(_('data_sect must be a string, numpy array or list'))

        # Les positions de référence sont intanciées à None
        # Elles sont accessibles comme "property" de l'objet --> valeur "brute"
        # mais il est également possible d'obtenir l'info à travers :
        #  - bankleft_vertex, bankright_vertex, bed_vertex qui retournent un vertex quel que soit le format de stockage
        #  - bankleft_s3D, bankright_s3D, bed_s3D qui retournent la position curvi 3D quel que soit le format de stockage
        #  - bankleft_sz, bankright_sz, bed_sz qui retournent un couple (s,z) quel que soit le format de stockage

        self._bankleft=None
        self._bankright=None
        self._bed=None

        self._bankleft_down=None
        self._bankright_down=None

        self.banksbed_postype = postype.BY_VERTEX

        self.refpoints={}

        self.s = 0.0
        self.up:profile = None
        self.down:profile = None

        self.laz = False # if True, points from LAZ file are loaded around the section

        if parent is not None:
            assert isinstance(parent,crosssections), _('Bad type of parent object')

        self.parent=parent

        # self.zdatum = 0.
        # self.add_zdatum = False

        # self.sdatum = 0.
        # self.add_sdatum = False

        self.orient = None

        self.sz = None
        self.sz_bankbed = None
        self.s3d_bankbed = None
        self.prepared = False # if True, one can call self.sz instead of self.get_sz

        self.smin = -99999
        self.smax = -99999
        self.zmin = -99999
        self.zmax = -99999

        # Uniform discharge
        self.q_slope = None # Based on imposed slope and roughness
        self.q_down = 0.  # Based on downstream slope (if oriented sections exist) and roughness
        self.q_up = 0.  # Based on upstream slope (if oriented sections exist) and roughness
        self.q_centered = 0. # Based on centered slope (if oriented sections exist) and roughness

        self.wetarea = None
        self.wetperimeter = None
        self.hydraulicradius = None
        self.waterdepth = None
        self.localwidth = None
        self.criticaldischarge = None

        self._linestring_sz = None
        self._linestring_s3dz = None

        if isinstance(data_sect, str):
            if data_sect != '':
                for curline in data_sect.splitlines():
                    values=curline.split(' ')
                    curvert=wolfvertex(float(values[0]), 0., float(values[1]))
                    self.add_vertex(curvert)
                self.prepare()
            else:
                logging.debug(_('Empty data_sect string -- no vertex added'))
        elif isinstance(data_sect, np.ndarray):
            if data_sect.shape[1]==2:
                for cur in data_sect:
                    curvert=wolfvertex(float(cur[0]), 0., float(cur[1]))
                    self.add_vertex(curvert)
                self.prepare()
            else:
                logging.error(_('Bad shape of input array in data_sect -- no vertex added'))
        elif isinstance(data_sect, list):
            if all(isinstance(item, (list, tuple, np.ndarray)) and len(item)==2 for item in data_sect):
                for cur in data_sect:
                    curvert=wolfvertex(float(cur[0]), 0., float(cur[1]))
                    self.add_vertex(curvert)
                self.prepare()
            elif all(isinstance(item, wolfvertex) for item in data_sect):
                self.add_vertex(data_sect)
                self.prepare()
            else:
                logging.error(_('Bad shape of input list in data_sect -- no vertex added'))
        elif isinstance(data_sect, vector):
            self.add_vertex(data_sect.myvertices.copy())
            self.prepare()

    @property
    def linked_arrays(self):
        """ Return the linked arrays from parent crosssection if any.
        Useful to plot associated data along the section.
        """

        if self.parent is not None:
            return self.parent.get_linked_arrays()
        else:
            return {}

    @property
    def bankleft(self):
        """ Return the bankleft reference point in its raw format (wolfvertex, index or s3D) """
        return self._bankleft

    @bankleft.setter
    def bankleft(self,value):
        """ Set the bankleft reference point in its raw format (wolfvertex, index or s3D) """
        self._bankleft = value

    @property
    def bankright(self):
        """ Return the bankright reference point in its raw format (wolfvertex, index or s3D) """
        return self._bankright

    @bankright.setter
    def bankright(self,value):
        """ Set the bankright reference point in its raw format (wolfvertex, index or s3D) """
        self._bankright = value

    @property
    def bankleft_down(self):
        """ Return the bankleft_down reference point in its raw format (wolfvertex, index or s3D) """
        return self._bankleft_down

    @bankleft_down.setter
    def bankleft_down(self,value):
        """ Set the bankleft_down reference point in its raw format (wolfvertex, index or s3D) """
        self._bankleft_down = value

    @property
    def bankright_down(self):
        """ Return the bankright_down reference point in its raw format (wolfvertex, index or s3D) """
        return self._bankright_down

    @bankright_down.setter
    def bankright_down(self,value):
        """ Set the bankright_down reference point in its raw format (wolfvertex, index or s3D) """
        self._bankright_down = value

    @property
    def bed(self):
        """ Return the bed reference point in its raw format (wolfvertex, index or s3D) """
        return self._bed

    @bed.setter
    def bed(self,value):
        """ Set the bed reference point in its raw format (wolfvertex, index or s3D) """
        self._bed = value

    @property
    def bankleft_vertex(self):
        """ Return the bankleft reference point as a wolfvertex whatever the storage format """
        if self._bankleft is None:
            return None

        if self.banksbed_postype == postype.BY_VERTEX:
            return self._bankleft
        elif self.banksbed_postype == postype.BY_INDEX:
            return self.myvertices[self._bankleft]
        else:
            return self.interpolate(self._bankleft, adim=False)

    @property
    def bankright_vertex(self):
        """ Return the bankright reference point as a wolfvertex whatever the storage format """
        if self._bankright is None:
            return None

        if self.banksbed_postype == postype.BY_VERTEX:
            return self._bankright
        elif self.banksbed_postype == postype.BY_INDEX:
            return self.myvertices[self._bankright]
        else:
            return self.interpolate(self._bankright, adim=False)

    @property
    def bankleft_down_vertex(self):
        """ Return the bankleft_down reference point as a wolfvertex whatever the storage format """
        if self._bankleft_down is None:
            return None

        if self.banksbed_postype == postype.BY_VERTEX:
            return self._bankleft_down
        elif self.banksbed_postype == postype.BY_INDEX:
            return self.myvertices[self._bankleft_down]
        else:
            return self.interpolate(self._bankleft_down, adim=False)

    @property
    def bankright_down_vertex(self):
        """ Return the bankright_down reference point as a wolfvertex whatever the storage format """
        if self._bankright_down is None:
            return None

        if self.banksbed_postype == postype.BY_VERTEX:
            return self._bankright_down
        elif self.banksbed_postype == postype.BY_INDEX:
            return self.myvertices[self._bankright_down]
        else:
            return self.interpolate(self._bankright_down, adim=False)

    @property
    def bed_vertex(self):
        """ Return the bed reference point as a wolfvertex whatever the storage format """
        if self._bed is None:
            return None

        if self.banksbed_postype == postype.BY_VERTEX:
            return self._bed
        elif self.banksbed_postype == postype.BY_INDEX:
            return self.myvertices[self._bed]
        else:
            return self.interpolate(self._bed, adim=False)

    @property
    def bankleft_s3D(self):
        """ Return the bankleft reference point as a s3D position whatever the storage format """
        if self.banksbed_postype == postype.BY_S3D:
            return self._bankleft
        else:
            # on dispose d'un vertex 3D et on doit retnvoyer une position s3D
            # --> projection x,y sur la trace --> récupération de 's'
            # --> calcul de la distance s3D via shapely LineString sz en projetant '(s,z)'
            if self.bankleft_vertex is not None:
                ls2d = self.linestring
                lssz = self.linestring_sz
                curvert = self.bankleft_vertex
                s = ls2d.project(Point(curvert.x, curvert.y))
                s3d = lssz.project(Point(s,curvert.z))
            else:
                s3d = 0.
            return s3d

    @property
    def bankright_s3D(self):
        """ Return the bankright reference point as a s3D position whatever the storage format """
        if self.banksbed_postype == postype.BY_S3D:
            return self._bankright
        else:
            # on dispose d'un vertex 3D et on doit retnvoyer une position s3D
            # --> projection x,y sur la trace --> récupération de 's'
            # --> calcul de la distance s3D via shapely LineString sz en projetant '(s,z)'
            if self.bankright_vertex is not None:
                ls2d = self.linestring
                lssz = self.linestring_sz
                curvert = self.bankright_vertex
                s = ls2d.project(Point(curvert.x, curvert.y))
                s3d = lssz.project(Point(s,curvert.z))
            else:
                s3d = self.length3D
            return s3d

    @property
    def bankleft_down_s3D(self):
        """ Return the bankleft_down reference point as a s3D position whatever the storage format """
        if self.banksbed_postype == postype.BY_S3D:
            return self._bankleft_down
        else:
            # on dispose d'un vertex 3D et on doit retnvoyer une position s3D
            # --> projection x,y sur la trace --> récupération de 's'
            # --> calcul de la distance s3D via shapely LineString sz en projetant '(s,z)'
            if self.bankleft_down_vertex is not None:
                ls2d = self.linestring
                lssz = self.linestring_sz
                curvert = self.bankleft_down_vertex
                s = ls2d.project(Point(curvert.x, curvert.y))
                s3d = lssz.project(Point(s,curvert.z))
            else:
                s3d = 0.
            return s3d

    @property
    def bankright_down_s3D(self):
        """ Return the bankright_down reference point as a s3D position whatever the storage format """
        if self.banksbed_postype == postype.BY_S3D:
            return self._bankright_down
        else:
            # on dispose d'un vertex 3D et on doit retnvoyer une position s3D
            # --> projection x,y sur la trace --> récupération de 's'
            # --> calcul de la distance s3D via shapely LineString sz en projetant '(s,z)'
            if self.bankright_down_vertex is not None:
                ls2d = self.linestring
                lssz = self.linestring_sz
                curvert = self.bankright_down_vertex
                s = ls2d.project(Point(curvert.x, curvert.y))
                s3d = lssz.project(Point(s,curvert.z))
            else:
                s3d = self.length3D
            return s3d

    @property
    def bed_s3D(self):
        """ Return the bed reference point as a s3D position whatever the storage format """
        if self.banksbed_postype == postype.BY_S3D:
            return self._bed
        else:
            # on dispose d'un vertex 3D et on doit retnvoyer une position s3D
            # --> projection x,y sur la trace --> récupération de 's'
            # --> calcul de la distance s3D via shapely LineString sz en projetant '(s,z)'
            if self.bed_vertex is not None:
                ls2d = self.linestring
                lssz = self.linestring_sz
                curvert = self.bed_vertex
                s = ls2d.project(Point(curvert.x, curvert.y))
                s3d = lssz.project(Point(s,curvert.z))
            else:
                s3d = self.length3D/2.
            return s3d

    @property
    def bankleft_sz(self):
        """ Return the bankleft reference point as a (s,z) tuple whatever the storage format """
        ls2d = self.linestring
        curvert = self.bankleft_vertex
        s = ls2d.project(Point(curvert.x, curvert.y))
        return s, curvert.z

    @property
    def bankright_sz(self):
        """ Return the bankright reference point as a (s,z) tuple whatever the storage format """
        ls2d = self.linestring
        curvert = self.bankright_vertex
        s = ls2d.project(Point(curvert.x, curvert.y))
        return s, curvert.z

    @property
    def bed_sz(self):
        """ Return the bed reference point as a (s,z) tuple whatever the storage format """
        ls2d = self.linestring
        curvert = self.bed_vertex
        s = ls2d.project(Point(curvert.x, curvert.y))
        return s, curvert.z

    @property
    def bankleft_down_sz(self):
        """ Return the bankleft_down reference point as a (s,z) tuple whatever the storage format """
        ls2d = self.linestring
        curvert = self.bankleft_down_vertex
        s = ls2d.project(Point(curvert.x, curvert.y))
        return s, curvert.z

    @property
    def bankright_down_sz(self):
        """ Return the bankright_down reference point as a (s,z) tuple whatever the storage format """
        ls2d = self.linestring
        curvert = self.bankright_down_vertex
        s = ls2d.project(Point(curvert.x, curvert.y))
        return s, curvert.z

    def verif(self):

        self.update_lengths()


    def triangulation_gltf(self, zmin:float):
        """
        Génération d'un info de triangulation pour sortie au format GLTF --> Blender

        La triangulation est constituée de la section et d'une base plane à l'altitude zmin, a priori sous le lit de la rivière.

        :param zmin: position d'altitude minimale de la triangulation
        """

        section = self.asnparray3d()
        base = section.copy()
        base[:,2] = zmin

        points = np.concatenate((section,base), axis=0)
        triangles=[]
        nb=self.nbvertices
        for j in range (nb-1):
            a = 0+j
            b = nb+1+j
            c = nb+j
            for i in range(2):
                triangles.append([a,b,c])
                c = b
                b = a+1

        return points, triangles

    def triangulation_ponts(self, x:float ,y:float, zmax:float):
        """
        Triangulation d'une section de pont

        :param x: coordonnée X du point de référence du pont
        :param y: coordonnée Y du point de référence du pont
        :param zmax: altitude du tablier du pont
        """

        section = self.asnparray3d()
        x1,y1=_find_shift_at_xy(section,x,y)
        parallele = _shift_np(section,x1,y1)

        base1 = section.copy()
        base1[:,2]= zmax
        base2 = parallele.copy()
        base2[:,2]= zmax
        points = np.concatenate((section,base1,parallele,base2),axis=0)
        triangles=[]
        for j in range (len(section)-1):
            a = 0+j
            b = len(section)+1+j
            c = len(section)+j
            for i in range(2):
                triangles.append([a,b,c])
                c = b
                b = a+1
        for j in range (len(section)-1):
            a = len(section)+j
            b = len(section)*3+j+1
            c = len(section)*3+j
            for i in range(2):
                triangles.append([a,b,c])
                c = b
                b = a+1
        for j in range (len(section)-1):
            a = len(section)*2+j
            b = len(section)*3+j+1
            c = len(section)*3+j
            for i in range(2):
                triangles.append([a,b,c])
                c = b
                b = a+1
        for j in range (len(section)-1):
            a = 0+j
            b = len(section)*2+j+1
            c = len(section)*2+j
            for i in range(2):
                triangles.append([a,b,c])
                c = b
                b = a+1
        triangles.append([0,len(section)*3,len(section)*2])
        triangles.append([0,len(section),len(section)*3])
        triangles.append([len(section)-1,len(section)*4-1,len(section)*3-1])
        triangles.append([len(section)-1,len(section)*2-1,len(section)*4-1])
        return(np.asarray([[curpt[0],curpt[2],-curpt[1]] for curpt in points],dtype=np.float32),np.asarray(triangles,dtype=np.uint32))

    def _set_orient(self):
        """
        Calcul du vecteur directeur de la section sur base des points extrêmes
        """

        if self.nbvertices<2:
            logging.error(_('Not enough vertices to define an orientation'))
            self.orient = np.zeros(2)
            return

        self.orient = asarray([self.myvertices[-1].x-self.myvertices[0].x,
                              self.myvertices[-1].y-self.myvertices[0].y])

        dist = np.linalg.norm(self.orient)
        if dist==0.:
            logging.error(_('Bad vertices to define an orientation -- identical points'))
            self.orient = np.zeros(2)
            return

        self.orient = self.orient / np.linalg.norm(self.orient)

    @property
    def trace_increments(self):
        """ Return the orientation vector of the section (unit vector in the XY plane)
        """
        if self.orient is None:
            self._set_orient()
        return self.orient

    def get_xy_from_s(self, s:float) -> tuple[float, float]:
        """
        Récupération d'un tuple (x,y) sur base d'une distance 2D 's' orientée dans l'axe de la section

        :param s: distance curviligne 2D le long de la section supposée plane étant donné l'utilisation de l'orientation
        """

        if self.orient is None:
            self._set_orient()

        return self.myvertices[0].x+self.orient[0]*s,self.myvertices[0].y+self.orient[1]*s

    def set_vertices_sz_orient(self, sz:np.ndarray | tuple | list, xy1:np.ndarray | list | tuple, xy2:np.ndarray | list | tuple):
        """
        Ajout de vertices depuis :
          - une matrice numpy (s,z) -- shape = (nb_vert,2) ou une liste ou un tuple convertibles en numpy array
          - un point source [x,y]
          - un point visé [x,y]

        Le point source correspond au vertex de s=0.
        Le point visé sert uniquement à définir l'orientation de la section.

        :param sz: matrice numpy (s,z) -- shape = (nb_vert,2)
        :param xy1: point source [x,y]
        :param xy2: point visé [x,y]
        """

        if isinstance(sz,list):
            sz = np.asarray(sz)
        if isinstance(sz,tuple):
            sz = np.asarray(sz)
        if isinstance(xy1,list):
            xy1 = np.asarray(xy1)
        if isinstance(xy2,list):
            xy2 = np.asarray(xy2)
        if isinstance(xy1,tuple):
            xy1 = np.asarray(xy1)
        if isinstance(xy2,tuple):
            xy2 = np.asarray(xy2)

        if sz.shape[1]==2 and xy1.shape==(2,) and xy2.shape==(2,):
            if not np.array_equal(xy1,xy2):
                self.myvertices=[]

                dx, dy = xy2[0]-xy1[0], xy2[1]-xy1[1]
                norm = np.linalg.norm([dx,dy])
                dx, dy = dx/norm, dy/norm

                for cur in sz:
                    x, y = xy1[0] + dx*cur[0], xy1[1] + dy*cur[0]
                    self.add_vertex(wolfvertex(x, y, float(cur[1])))
            else:
                logging.error(_('Bad input points in set_vertices_sz_orient -- identical points'))
        else:
            logging.error(_('Bad shape of input arrays in set_vertices_sz_orient'))

    def get_laz_around(self, length_buffer:float = 10.):
        """
        Récupération de points LAZ autour de la section

        :param length_buffer: distance latérale [m] autour de la section pour la récupération des points LAZ
        """

        self.laz = False

        if self.parent is None:
            logging.error(_('No parent crosssection object -- cannot get LAZ points'))
            return

        if self.parent.gridlaz is None:
            logging.error(_('No LAZ grid in parent crosssection object -- cannot get LAZ points'))
            return

        mypoly = self.linestring.buffer(length_buffer, cap_style=CAP_STYLE.square)
        mybounds = ((mypoly.bounds[0], mypoly.bounds[2]), (mypoly.bounds[1], mypoly.bounds[3]))

        myxyz = self.parent.gridlaz.scan(mybounds)

        prepare(mypoly)
        mytests = [mypoly.contains(Point(cur[:3])) for cur in myxyz]
        destroy_prepared(mypoly)

        self.usedlaz = np.asarray(myxyz[mytests])

        orig = [self.myvertices[0].x,self.myvertices[0].y]
        a=[self.myvertices[-1].x-self.myvertices[0].x,self.myvertices[-1].y-self.myvertices[0].y]
        a= a/np.linalg.norm(a)

        self.s_laz = np.asarray([np.dot(a,cur[:2]-orig) for cur in self.usedlaz])

        self.colors_laz=np.ones((self.usedlaz.shape[0],4),dtype=np.float32)

        self.colors_laz[self.usedlaz[:,3]==1]=[.5,.5,.5,1.]
        self.colors_laz[self.usedlaz[:,3]==2]=[.5,.25,.25,1.]
        self.colors_laz[self.usedlaz[:,3]==4]=[0.,0.5,0.,1.]
        self.colors_laz[self.usedlaz[:,3]==9]=[0.,0.5,1.,1.]
        self.colors_laz[self.usedlaz[:,3]==10]=[1,0.2,0.2,1.]

        s = np.asarray([float(np.cross(a,cur[:2]-orig))  for cur in self.usedlaz])
        smax=np.max(np.abs(s))
        self.colors_laz[:,3] = 1.-np.abs(s)/smax

        up=np.where(s[:]<0.)[0]
        down=np.where(s[:]>=0.)[0]
        self.uplaz = self.s_laz[up]
        self.downlaz = self.s_laz[down]

        self.uplaz_colors = self.colors_laz[up]
        self.downlaz_colors = self.colors_laz[down]

        self.upz = self.usedlaz[up]
        self.downz = self.usedlaz[down]

        self.laz=True

    def plot_laz(self, length_buffer:float = 5., fig:Figure=None, ax:Axes=None, show=False):
        """
        Dessin des points LAZ sur le graphique Matplotlib

        :param length_buffer: distance latérale [m] autour de la section pour la récupération des points LAZ
        :param fig: figure Matplotlib
        :param ax: axes Matplotlib
        :param show: if True, show the figure
        """

        if not self.laz:
            self.get_laz_around(length_buffer)

        if not self.laz:
            logging.error(_('No LAZ points to plot'))
            return None

        if ax is None:
            fig = plt.figure()
            ax=fig.add_subplot(111)

        # ax.scatter(self.s_laz,self.usedlaz[:,2],c=self.colors_laz,marker='.')
        ax.scatter(self.uplaz,self.upz[:,2],c=self.uplaz_colors,marker='.')
        ax.scatter(self.downlaz,self.downz[:,2],c=self.downlaz_colors,marker='+')

        if show:
            fig.show()

        return np.min(self.usedlaz[:,2]),np.max(self.usedlaz[:,2])

    def slide_vertex(self, s:float):
        """
        Glissement des vertices d'une constante 's'

        :param s: distance de glissement dans l'axe de la section
        """

        if self.orient is None:
            self._set_orient()

        # increments de position
        dx = self.orient[0] *s
        dy = self.orient[1] *s

        for curv in self.myvertices:
            curv.x +=dx
            curv.y +=dy

    def movebankbed_index(self,
                          which:Literal['left', 'right', 'bed', 'left_down', 'right_down'],
                          orientation:Literal['left', 'right']) -> None:
        """
        Déplacement des points de référence sur base d'un index.
        Le cas échéant, adaptation du mode de stockage.

        :param which: point à déplacer ('left', 'right', 'bed', 'left_down', 'right_down')
        :param orientation: direction du déplacement ('left' ou 'right')
        """
        if self.banksbed_postype == postype.BY_VERTEX:
            if which=='left':
                k = self.myvertices.index(self._bankleft)
            elif which=='right':
                k = self.myvertices.index(self._bankright)
            elif which=='bed':
                k = self.myvertices.index(self._bed)
            elif which=='left_down':
                k = self.myvertices.index(self._bankleft_down)
            elif which=='right_down':
                k = self.myvertices.index(self._bankright_down)

            if orientation=='left':
                k=max(0,k-1)
            elif orientation=='right':
                k=min(self.nbvertices-1,k+1)

            if which=='left':
                self._bankleft=k
            elif which=='right':
                self._bankright=k
            elif which=='bed':
                self._bed=k
            elif which=='left_down':
                self._bankleft_down=k
            elif which=='right_down':
                self._bankright_down=k

        elif self.banksbed_postype == postype.BY_S3D:
            if which=='left':
                k = 0
                self._bankleft=k
            elif which=='right':
                k = self.nbvertices-1
                self._bankright=k
            elif which=='bed':
                k = int(self.nbvertices/2)
                self._bed=k
            elif which=='left_down':
                k = 1
                self._bankleft_down=k
            elif which=='right_down':
                k = self.nbvertices-2
                self._bankright_down=k


        if self.banksbed_postype == postype.BY_INDEX:
            if which=='left':
                k = self._bankleft
            elif which=='right':
                k = self._bankright
            elif which=='bed':
                k = self._bed
            elif which=='left_down':
                k = self._bankleft_down
            elif which=='right_down':
                k = self._bankright_down

            if orientation=='left':
                k=max(0,k-1)
            elif orientation=='right':
                k=min(self.nbvertices-1,k+1)

            if which=='left':
                self._bankleft=k
            elif which=='right':
                self._bankright=k
            elif which=='bed':
                self._bed=k
            elif which=='left_down':
                self._bankleft_down=k
            elif which=='right_down':
                self._bankright_down=k

        self.banksbed_postype = postype.BY_INDEX

        if self.prepared:
            self.sz_bankbed = self.get_sz_banksbed(force=True)
            self.s3d_bankbed = self.get_s3d_banksbed(force=True)

    def update_sdatum(self, new_sdatum:float):
        """
        Mise à jour de la position de la section selon sa trace

        :param new_sdatum: nouvelle valeur de sdatum
        """

        sdatum_prev = self.sdatum

        self.sdatum = new_sdatum
        self.add_sdatum = True

        if self.prepared:
            delta = new_sdatum - sdatum_prev
            self.sz[:,0] += delta
            self.smin += delta
            self.smax += delta

    def update_zdatum(self, new_zdatum:float):
        """
        Mise à jour de l'altitude de référence de la section

        :param new_zdatum: nouvelle valeur de zdatum
        """

        zdatum_prev = self.zdatum

        self.zdatum = new_zdatum
        self.add_zdatum = True

        if self.prepared:
            delta = new_zdatum - zdatum_prev
            self.sz[:,1] += delta
            self.zmin += delta
            self.zmax += delta

    def update_banksbed_from_s3d(self,
                                 which:Literal['left', 'right', 'bed', 'left_down', 'right_down'],
                                 s:float):
        """
        Mise à jour des points de référence depuis une coordonnée curvi 3D

        :param which: point à modifier ('left', 'right', 'bed', 'left_down', 'right_down')
        :param s: nouvelle position curvi 3D du point
        """

        if self.banksbed_postype != postype.BY_S3D:
            s1, s2, s3, s4, s5 = self.get_s3d_banksbed()
            self.bankleft = s1
            self.bankleft_down = s2
            self.bed = s3
            self.bankright_down = s4
            self.bankright = s5

        self.banksbed_postype = postype.BY_S3D

        if which=='left':
            self.bankleft = s

            if self.prepared:
                self.s3d_bankbed[0]=s

        elif which =='right':
            self.bankright = s

            if self.prepared:
                self.s3d_bankbed[4]=s

        elif which=='bed':
            self.bed = s

            if self.prepared:
                self.s3d_bankbed[2]=s

        elif which=='left_down':
            self.bankleft_down = s

            if self.prepared:
                self.s3d_bankbed[1]=s

        elif which=='right_down':
            self.bankright_down = s

            if self.prepared:
                self.s3d_bankbed[3]=s

        if self.prepared:
            self.sz_bankbed = self.get_sz_banksbed(force=True)

    def save(self, f):
        """
        Surcharge de l'opération d'écriture

        :param f: fichier ouvert en écriture
        """

        if self.parent.forcesuper:
            super().save(f)
        else:
            for curvert in self.myvertices:
                which=''
                if curvert is self.bed:
                    which = "BED"
                elif curvert is self.bankleft:
                    which = "LEFT"
                elif curvert is self.bankright:
                    which = "RIGHT"
                elif curvert is self.bankleft_down:
                    which = "LEFT_DOWN"
                elif curvert is self.bankright_down:
                    which = "RIGHT_DOWN"

                f.write("{0}\t{1}\t{2}\t{3}\t{4}\n".format(self.myname, curvert.x, curvert.y, which, curvert.z))

    def get_s_from_xy(self, xy:wolfvertex, cumul:bool = False) -> float:
        """
        Retourne la coordonnée curviligne (ou distance euclidienne selon l'orientation de la section)
        du point xy donné en tant qu'objet wolfvertex.

        Dans cette routine, 'cumul' est à False par défaut pour être rétro-compatible avec les versions précédentes.
        ATTENTION: Cette valeur par défaut n'est pas identique à celle utilisée dans 'get_sz'.

        :param xy: vertex dont on veut la coordonnée curvi 2D
        :param cumul: si True, la coordonnée curvi 2D est cumulée (distance le long de la section)
                       si False, la coordonnée curvi 2D est la distance euclidienne au point de départ
        """

        if cumul:
            s = self.linestring.project(Point(xy.x, xy.y))
            return s

        x1 = self.myvertices[0].x
        y1 = self.myvertices[0].y
        length = math.sqrt((xy.x-x1)**2.+(xy.y-y1)**2.)

        return length

    # def get_sz(self, cumul=True) -> tuple[np.ndarray, np.ndarray]:
    #     """
    #     Surcharge de la méthode get_sz de la classe mère wolfsection pour ajouter les datums s et z.

    #     :param cumul: si True, la coordonnée curvi 2D est cumulée (distance le long de la section)
    #                    si False, la coordonnée curvi 2D est la distance euclidienne au point de départ
    #     :return: tuple (s,z) avec s la coordonnée curvi 2D
    #     """

    #     if self.prepared:
    #         return self.sz[:,0], self.sz[:,1]

    #     s, z = super().get_sz(cumul=cumul)

    #     if self.add_zdatum:
    #         z += self.zdatum

    #     if self.add_sdatum:
    #         s += self.sdatum

    #     return s,z

    def set_sz(self, sz:np.ndarray, trace:list[tuple[float, float]]):
        """
        Calcule les positions des vertices sur base d'une matrice sz et d'une trace.

        :param s: colonne 0
        :param z: colonne 1
        :param trace: liste de 2 couples xy -> [[x1,y1], [x2,y2]]

        FIXME: Vérifier la possibilité de fusionner avec set_vertices_sz_orient
        """

        orig = trace[0]
        end = trace[1]

        if np.all(np.asarray(orig)==np.asarray(end)):
            logging.error(_('Bad input points in set_sz -- identical points'))
            return

        vec = np.asarray(end)-np.asarray(orig)
        vec = vec/np.linalg.norm(vec)

        xy = np.asarray([s*vec+np.asarray(orig) for s in sz[:,0]])

        for i in range(len(xy)):
            curvert = wolfvertex(xy[i,0],xy[i,1],sz[i,1])
            self.add_vertex(curvert)

    def get_sz_banksbed(self, cumul=True, force:bool=False) -> tuple[float, float, float, float, float, float, float, float, float, float]:
        """
        Retourne les positions des points de référence  mais avec la coordonnée curvi 2D
         - (sleft, sbed, sright, zleft, zbed, zright, sbankleft_down, sbankright_down, zbankleft_down, zbankright_down)

        :param cumul: si True, la coordonnée curvi 2D est cumulée (distance le long de la section)
                       si False, la coordonnée curvi 2D est la distance euclidienne au point de départ
        :param force: si True, force le recalcul même si la section est déjà préparée
        """

        if self.prepared and not force:
            return self.sz_bankbed

        x1 = self.myvertices[0].x
        y1 = self.myvertices[0].y

        if self.bankleft is not None:
            if cumul:
                sleft, zleft = self.bankleft_sz
            else:
                curvert = self.bankleft_vertex
                x2 = curvert.x
                y2 = curvert.y
                sleft = math.sqrt((x2-x1)**2.+(y2-y1)**2.)
                zleft=curvert.z
        else:
            sleft=-99999.
            zleft=-99999.

        if self.bankright is not None:
            if cumul:
                sright, zright = self.bankright_sz
            else:
                curvert = self.bankright_vertex
                x2 = curvert.x
                y2 = curvert.y
                sright = math.sqrt((x2-x1)**2.+(y2-y1)**2.)
                zright=curvert.z
        else:
            sright=-99999.
            zright=-99999.

        if self.bed is not None:
            if cumul:
                sbed, zbed = self.bed_sz
            else:
                curvert = self.bed_vertex
                x2 = curvert.x
                y2 = curvert.y
                sbed = math.sqrt((x2-x1)**2.+(y2-y1)**2.)
                zbed=curvert.z
        else:
            sbed=-99999.
            zbed=-99999.

        if self.bankleft_down is not None:
            if cumul:
                sbankleft_down, zbankleft_down = self.bankleft_down_sz
            else:
                curvert = self.bankleft_down_vertex
                x2 = curvert.x
                y2 = curvert.y
                sbankleft_down = math.sqrt((x2-x1)**2.+(y2-y1)**2.)
                zbankleft_down=curvert.z
        else:
            sbankleft_down=-99999.
            zbankleft_down=-99999.

        if self.bankright_down is not None:
            if cumul:
                sbankright_down, zbankright_down = self.bankright_down_sz
            else:
                curvert = self.bankright_down_vertex
                x2 = curvert.x
                y2 = curvert.y
                sbankright_down = math.sqrt((x2-x1)**2.+(y2-y1)**2.)
                zbankright_down=curvert.z
        else:
            sbankright_down=-99999.
            zbankright_down=-99999.

        if self.add_sdatum:
            sleft+=self.sdatum
            sbed+=self.sdatum
            sright+=self.sdatum
            sbankleft_down+=self.sdatum
            sbankright_down+=self.sdatum
        if self.add_zdatum:
            zleft+=self.zdatum
            zbed+=self.zdatum
            zright+=self.zdatum
            zbankleft_down+=self.zdatum
            zbankright_down+=self.zdatum

        return sleft,sbed,sright,zleft,zbed,zright, sbankleft_down, sbankright_down, zbankleft_down, zbankright_down

    def get_s3d_banksbed(self, force:bool=False)-> tuple[float, float, float, float, float]:
        """
        Retourne les coordonnée curvi 3D des points de référence
         - (sleft, sleft_down, sbed, sright_down, sright)
        """

        if self.prepared and not force:
            return self.s3d_bankbed

        return self.bankleft_s3D, self.bankleft_down_s3D, self.bed_s3D, self.bankright_down_s3D, self.bankright_s3D

    def asshapely_sz(self) -> LineString:
        """
        Retroune la section comme objet shapely - polyligne selon la trace avec altitudes
        """

        s,z = self.get_sz()
        return LineString(np.asarray([[curs, curz] for curs, curz in zip(s,z)]))

    @property
    def linestring_sz(self) -> LineString:
        """
        Retroune la section comme objet shapely - polyligne selon la trace avec altitudes
        """

        if self._linestring_sz is not None:
            return self._linestring_sz

        self._linestring_sz = self.asshapely_sz()
        prepare(self._linestring_sz)
        return self._linestring_sz

    def asshapely_s3dz(self) -> LineString:
        """
        Retroune la section comme objet shapely - polyligne selon la trace 3D avec altitudes
        """

        s = self.get_s3d()
        z = [cur.z for cur in self.myvertices]
        return LineString(np.asarray([[curs, curz] for curs, curz in zip(s,z)]))

    @property
    def s3dz(self) -> np.ndarray:
        """
        Retroune la section comme matrice numpy (s3d,z)
        """

        s = self.get_s3d()
        z = [cur.z for cur in self.myvertices]
        return np.column_stack([s,z])

    @property
    def linestring_s3dz(self) -> LineString:
        """
        Retroune la section comme objet shapely - polyligne selon la trace 3D avec altitudes
        """

        if self._linestring_s3dz is not None:
            return self._linestring_s3dz

        self._linestring_s3dz = self.asshapely_s3dz()
        prepare(self._linestring_s3dz)
        return self._linestring_s3dz

    def prepare(self,cumul=True):
        """
        Pre-Compute sz, sz_banked and shapely objects to avoid multiple computation
        """

        self.reset_prepare()
        self.update_lengths()
        x,y = self.get_sz()
        self.sz = np.column_stack([x,y])
        self.smin = min(x)
        self.smax = max(x)
        self.zmin = min(y)
        self.zmax = max(y)

        self.prepare_shapely(linestring=True, polygon=False)
        self.sz_bankbed = list(self.get_sz_banksbed(cumul))
        self.s3d_bankbed = list(self.get_s3d_banksbed())

        self.prepared=True

    def __del__(self):

        self.reset_prepare()
        super().__del__()

    def _reset_linestring_sz_s3dz(self):

        if self._linestring_sz is not None:
            if is_prepared(self._linestring_sz):
                destroy_prepared(self._linestring_sz)
            self._linestring_sz=None

        if self._linestring_s3dz is not None:
            if is_prepared(self._linestring_s3dz):
                destroy_prepared(self._linestring_s3dz)
            self._linestring_s3dz=None


    def reset_prepare(self):
        """
        Réinitialisation de la préparation de la section
        """

        self.sz = None
        self.smin = -99999
        self.smax = -99999
        self.zmin = -99999
        self.zmax = -99999
        self.sz_bankbed = None
        self.s3d_bankbed = None
        self.reset_linestring()
        self._reset_linestring_sz_s3dz()

        self.prepared=False

    def get_min(self) -> wolfvertex:
        """ Return the vertex with minimum elevation """
        return sorted(self.myvertices,key=lambda x:x.z)[0]

    def get_max(self) -> wolfvertex:
        """ Return the vertex with maximum elevation """
        return sorted(self.myvertices,key=lambda x:x.z)[-1]

    def get_minz(self) -> float:
        """ Return the minimum elevation """
        return amin(list(x.z for x in self.myvertices))

    def get_maxz(self) -> float:
        """ Return the maximum elevation """
        return amax(list(x.z for x in self.myvertices))

    def relation_oneh(self, cury:float, x:float = None, y:float = None):
        """ Compute the hydraulic characteristics for a given water elevation 'cury'

        :param cury: water elevation
        :param x: optional x coordinates of the section (if None, use the section's coordinates)
        :param y: optional y coordinates of the section (if None, use the section's coordinates)
        :return: a,s,w,r  (wetted area, wetted perimeter, top width, hydraulic radius)

        """
        if x is None and y is None:
            x,y=self.get_sz()

        s=a=w=0.0
        for i in range(0,len(x)-1):
            #recherche des intersections sur les segments
            x1=x[i]
            y1=y[i]
            x2=x[i+1]
            y2=y[i+1]

            #calcul des incréments de section et de périmètre
            dS=0.0
            dA=0.0
            dL=0.0
            # if y1<=cury and y2<=cury: # The inferiority was not strict under this condition especially for the computation of the wetted perimeter
            if y1<cury and y2<cury:
                #le segment est totalement situé en dessous de la hauteur utile
                dS=math.sqrt((x2-x1)**2.+(y2-y1)**2.)
                dA=0.5*(2.0*cury-y1-y2)*(x2-x1)
                dL=(x2-x1)
            else:
                xx=INTERSEC(x1,y1,x2,y2,cury)
                if x1<=xx and xx<=x2:
                    #le segment intersecte la hauteur utile
                    if y2<=cury and cury<=y1:
                        dS=math.sqrt((x2-xx)**2.+(y2-cury)**2.)
                        dA=0.5*(x2-xx)*(cury-y2)
                        dL=(x2-xx)
                    if y1<=cury and cury<=y2:
                        dS=math.sqrt((xx-x1)**2.+(cury-y1)**2.)
                        dA=0.5*(xx-x1)*(cury-y1)
                        dL=(xx-x1)

            #ajout des incréments
            s+=dS
            a+=dA
            w+=dL

        if 0.0<s:
            r=a/s
        else:
            r=0.

        return float(a), float(s), float(w), float(r)

    def relations(self, discretize: int = 100, plot = True):
        """
        This method returns 6 numpy arrays each containing the evolution
        of a specific hydraulic characteristic with respect to the water depth in the profile
        (wetted area, wetted perimeter, top width, water detph, hydraulic radius, critical discharge).
        """

        x,y=self.get_sz()

        ymin=min(y)
        ymax=max(y)

        yy = concatenate([linspace(ymin,ymax,discretize),y])   #  To avoid hard coding the discretization
        yy=unique(yy)
        yy.sort()

        nb=len(yy)

        a=zeros(nb)      # Area
        s=zeros(nb)      # Wet perimeter
        w=zeros(nb)      # Top width
        r=zeros(nb)      # Hydraulic radius
        h=zeros(nb)      # Water depth
        qcr = zeros(nb)  # Critical discharge

        for k in range(nb):
            a[k],s[k],w[k],r[k] = self.relation_oneh(yy[k],x,y)
            h[k]=yy[k]-ymin
            # Test to avoid division by zero in case the top width equals 0 (often first value)
            if w[k] != 0:
                qcr[k] = math.sqrt((9.81*((a[k])**3))/(w[k]))
            else:
                qcr[k] = 0.

        #Initialisation for plots
        if plot:                                        # In order to allow other usages apart from Graphprofile.
            self.wetarea = a
            self.wetperimeter = s
            self.hydraulicradius = r
            self.waterdepth=h
            self.localwidth=w
            self.criticaldischarge = qcr

        return a,s,r,h,w,qcr

    def slopes(self):
        """ Compute the slopes of the section with respect to the upstream and downstream sections """

        if self.up is None or self.down is None:
            logging.error(_('No upstream or downstream section defined for section {}').format(self.myname))
            return 0.,0.,0.

        slopedown = (self.get_minz() - self.down.get_minz()) / abs(self.down.s - self.s+1.e-10)
        slopeup   = (self.up.get_minz() - self.get_minz()) / abs(self.s - self.up.s+1.e-10)
        slopecentered = (self.up.get_minz() - self.down.get_minz()) / abs(self.down.s - self.up.s+1.e-10)

        return slopeup,slopecentered,slopedown

    def ManningStrickler_Q(self, slope:float = 1.e-3, nManning:float = 0., KStrickler:float = 0.):
        """Procédure générique pour obtenir une relation uniforme Q-H sur base d'une pente et d'un coefficient de frottement.

        :param slope: une pente
        :param nManning: un coefficient de frottement
        :param KStrickler: un coefficient de frottement (if nManning > 0.0, KStrickler is ignored)
        """

        if slope <= 0.:
            logging.error(_('No positive slope provided for section {}').format(self.myname))
            return

         # Calcul des caractéristiques hydrauliques si pas encore faites

        if self.waterdepth is None:
            self.relations(plot = True)

        if nManning==0. and KStrickler==0.:
            logging.error(_('No friction coefficient provided for section {}').format(self.myname))
            return
        elif nManning > 0.:
            coeff = 1. / nManning
        elif KStrickler>0.:
            coeff = KStrickler

        nn = len(self.waterdepth)
        sqrtslope = math.sqrt(slope)

        self.q_slope = asarray([coeff * self.hydraulicradius[k]**(2./3.)* sqrtslope * self.wetarea[k] for k in range(nn)])

        return self.q_slope

    def ManningStrickler_oneQ(self, slope:float = 1.e-3, nManning:float = 0., KStrickler:float = 0., cury:float = 0.):
        """Procédure générique pour obtenir une relation uniforme Q-H sur base

        :param slope: une pente
        :param nManning: un coefficient de frottement
        :param KStrickler: un coefficient de frottement (if nManning > 0.0, KStrickler is ignored)
        :param cury: une hauteur d'eau
        :return: le débit Q
        """

        if slope <= 0.:
            logging.error(_('No positive slope provided for section {}').format(self.myname))
            return

        if nManning==0. and KStrickler==0.:
            return
        elif nManning>0.:
            coeff=1./nManning
        elif KStrickler>0.:
            coeff = KStrickler

        a,s,w,r = self.relation_oneh(cury)

        sqrtslope=math.sqrt(slope)

        q=coeff * r**(2./3.) * sqrtslope * a

        return q

    def deepcopy_profile(self, name: str = None, appendstr: str = '_copy'):
        """
        This method returns a deepcopy of the active profile.
        The profile features are individually transferred, therefore,
        only the necessary features are copied.

        :param name: name of the copied profile (if None, the current profile's name + appendstr is used)
        :param appendstr: string to append to the current profile's name if no new name is given (default: '_copy')
        :return: the copied profile
        """
        # if a new name is not given, we add _copy to the current profile's name.
        if name is None:
            name = self.myname + appendstr

        # We create the new  profile (copy).
        copied_profile = profile(name)

        # Deep copies
        # 1. Vertices
        copied_profile.myvertices = copy.deepcopy(self.myvertices)
        # 3. The river banks
        copied_profile.bankleft = copy.deepcopy(self.bankleft)
        copied_profile.bankright = copy.deepcopy(self.bankright)
        copied_profile.bed = copy.deepcopy(self.bed)
        copied_profile.banksbed_postype = copy.deepcopy(self.banksbed_postype)
        copied_profile.bankleft_down = copy.deepcopy(self.bankleft_down)
        copied_profile.bankright_down = copy.deepcopy(self.bankright_down)

        return copied_profile

    def color_active_profile(self, width: float = 3., color: list = [255, 0, 0], plot_opengl:bool = True):
        """
        This method colors and thickens the active profile
        (default width : 3, default color: red).

        :param width: width of the profile
        :param color: color of the profile as a list of RGB values (0-255)
        :param plot_opengl: if True, update the OpenGL plot of the parent zone
        """

        self.myprop.width = width
        self.myprop.color = getIfromRGB(color)

        if plot_opengl:
            if self.parentzone is not None:
                self.parentzone.plot(True) # FIXME (Parent zone)

    def highlighting(self, width: float = 3., color: list = [255, 0, 0] , plot_opengl:bool = True):
        """ Alias for color_active_profile """

        self.color_active_profile(width, color)

    def uncolor_active_profile(self, plot_opengl = True):
        """
        This method resets the width and the color of the active profile to 1 and black.
        """
        self.myprop.width = 1
        self.myprop.color = getIfromRGB([0, 0, 0])

        if plot_opengl:
            if self.parentzone is not None:
                self.parentzone.plot(True)

    def withdrawing(self, plot_opengl:bool = True):
        """Alias for uncolor_active_profile"""

        self.uncolor_active_profile(plot_opengl)

    def ManningStrickler_profile(self, slope: float =1.e-3, nManning: float =0., KStrickler: float=0.):
        """
        Procédure générique pour obtenir une relation uniforme Q-H d'un profile

        :param slope: une pente
        :param nManning: un coefficient de frottement
        :param KStrickler: un coefficient de frottement (if nManning > 0.0, KStrickler is ignored)

        ainsi que les relations correspondant aux pentes aval(slope down), amont(slopeup), et amont-aval (centered).

        :return: le débit Q maximum parmi les 4 relations
        """
        if self.down is not None and self.up is not None:
            slopeup,slopecentered,slopedown = self.slopes()
            # slopes are not necessarily positive --> subsequent tests

            slopeup = max(slopeup, 0.)
            slopecentered = max(slopecentered, 0.)
            slopedown = max(slopedown, 0.)
        else:
            slopecentered = 0.
            slopedown = 0.
            slopeup = 0.

        if nManning==0. and KStrickler==0.:
            logging.error(_('No friction coefficient provided for section {}').format(self.myname))
            return
        elif nManning>0.:
            coeff=1./nManning
        elif KStrickler>0.:
            coeff = KStrickler

        nn=len(self.waterdepth)


        sqrtslope = math.sqrt(slope)
        sqrtslopedown= math.sqrt(slopedown)
        sqrtslopecentered= math.sqrt(slopecentered)
        sqrtslopeup= math.sqrt(slopeup)

        self.q_slope = asarray([coeff*(self.hydraulicradius[k]**(2/3))*sqrtslope*self.wetarea[k] for k in range (nn)])
        self.q_down=asarray([coeff * self.hydraulicradius[k]**(2./3.)*sqrtslopedown * self.wetarea[k] for k in range(nn)])
        self.q_up=asarray([coeff * self.hydraulicradius[k]**(2./3.)*sqrtslopeup * self.wetarea[k] for k in range(nn)])
        self.q_centered=asarray([coeff * self.hydraulicradius[k]**(2./3.)*sqrtslopecentered * self.wetarea[k] for k in range(nn)])

        return max(max(self.q_slope), max(self.q_down), max(self.q_up), max(self.q_centered), max(self.criticaldischarge))

    def plotcs_profile(self,
                       fig: Figure = None,
                       ax: Axes = None,
                       compare:"profile" = None,
                       vecs : list = [],
                       col_structure: str ='none',
                       fwl: float = None,
                       fwd: float = None,
                       simuls:list=None,
                       show:bool = False,
                       forceaspect:bool = True,
                       plotlaz:bool = True,
                       clear:bool = True,
                       redraw:bool = True ):
        """
        This method plots the physical geometry of the current cross section (profile).

           - If a reference profile (compare) is given, the method hatchs the differences with resepect to cuts and fills.
           - If forceaspect is activated, the x and y axes are plotted using the same scale, otherwise, the figure is anamorphosed.
           - fwl (for water level) and fwd (for water depth) allow the visualisation of a specific water level on the graph.
           - idsimul: list of available numerical simulations containing this profile,
           - zsimul: list of water level in the simulations.
           - col_structure colors the structure displayed.

        :param fig: Matplotlib figure
        :param ax: Matplotlib axes
        :param compare: reference profile to compare with
        :param vecs: list of vector objects to plot on the section (e.g. levees, dikes, ...)
        :param col_structure: color of the structures (default: 'none')
        :param fwl: water level to plot (if None, no water level is plotted)
        :param fwd: water depth to plot (if None, no water level is plotted)
        :param simuls: list of simulations containing the profile (id, name, date, time, water level)
        :param show: if True, show the figure
        :param forceaspect: if True, force aspect ratio
        :param plotlaz: if True, plot LAZ points if available
        :param clear: if True, clear the axis before plotting
        :param redraw: if True, redraw the figure after plotting

        """

        idsimul=None
        zsimul=None
        if simuls is not None:
            if len(simuls)>0:
                idsimul = [cursimul[0] for cursimul in simuls]
                zsimul  = [cursimul[3] for cursimul in simuls]

        sl,sb,sr,zl,zb,zr, sld, srd, zld, zrd = self.get_sz_banksbed()
        x,y = self.get_sz()

        if fwl is None:
            if fwd is None or fwd <= 0:
                fwd =0
                fwl= self.zmin+ fwd
            elif fwd > 0 :
                fwl = self.zmin + fwd

        elif fwl is not None:
            fwl = fwl
            fwd = fwl-self.zmin

        # Creation of a new ax for cleaning purposes in the wolfhece.Graphprofile.
        myax1 = ax
        if redraw:
            if clear:
                myax1.clear()

        # Additional drawings on the profile (plots)
        vec: vector
        max_z = [self.zmax] #Fo ylim
        for vec in  vecs:
            n = vec.nbvertices
            verts = vec.asnparray() # 2D array containing x,y corresponding x , z
            max_z.append(np.max( verts[:,1]))

            myax1.fill(verts[:,0], verts[:,1], color= col_structure, lw = 2, hatch = _('///'), edgecolor = 'black')


        #Plots
        myax1.plot(x,y,color=_('black'),lw=2)
        myax1.fill_between(x,y,linewidth= 2,label=_('River bed'), color=_('black'), alpha = 0.2)

        if compare is not None:
            compare_s, compare_z = compare.get_sz()

            # New methods fill & cuts
            # Altitude diferences
            z = y - compare_z
            # Length differences
            s = x[1:] - x[:-1]

            # Method to compute the interection of 2 segments
            def _slope(s1 = 0., z1 = 0., s2 = 0., z2 = 0.):
                m =(z1 - z2)/(s1-s2)
                return m

            def _intersect_s(s1,z1,slp1,  sref1, zref1,slpref1):
                intersection = zref1 - z1 + slp1*s1 -slpref1*sref1
                return intersection

            def _intersect_z(intersect_s, z1, s1, slp1):
                intersection = (intersect_s*slp1) + z1 -slp1*s1
                return intersection

            def _intersect_coords(smod1, zmod1,
                                  smod2, zmod2,
                                  sref1, zref1,
                                  sref2, zref2):

                if smod2 - smod1 == 0 or sref1 - sref2 == 0:
                    raise Exception('Kindly delete duplicated point(s) in your data.')  #FIXME How one could handle this elegantly?

                else:
                    slope_mod = (zmod2 - zmod1)/(smod2 - smod1) # slope modified
                    slope_ref = (zref2 - zref1)/(sref2 - sref1) # slope reference
                    s_int = (zref1 - zmod1 + slope_mod*smod1 - slope_ref*sref1)/(slope_mod - slope_ref)
                    z_int = zmod1 + slope_mod*(s_int -smod1)
                    return s_int, z_int

            # Method to compute the areas (scenarios)

            def _area_triangle(b = None, h = None):
                area = (b*h)/2
                return area

            def _area_trapezoid(b1 = None, b2 = None, h= None):
                area = ((b1+b2)/2)*h
                return area

            # Handling the 4 cases
            positive_trap = []
            negative_trap = []
            positive_tri = []
            negative_tri = []

            for i in range(len(z)-1):
                if z[i] ==0 and z[i+1] ==0:
                    a =0
                    positive_trap.append(a)

                if z[i] > 0. and  z[i+1] > 0.:
                    a = _area_trapezoid(b1=z[i], b2=z[i+1], h = s[i])
                    positive_trap.append(a)

                if z[i] < 0. and z[i+1] < 0.:
                    a = _area_trapezoid(b1=z[i], b2=z[i+1], h = s[i])
                    negative_trap.append(a)

                if z[i] >= 0. and z[i+1] < 0. or z[i] > 0. and z[i+1] <= 0.:
                    #s_inter, z_inter = _intersect_coords(smod=s_x[i], zmod=z_y[i], sref =sref_x[i], zref = zref_y[i])
                    s_inter, z_inter = _intersect_coords(smod1 = x[i], zmod1 = y[i],
                                                         smod2 = x[i+1], zmod2 = y[i+1],
                                                         sref1 = compare_s[i], zref1 = compare_z[i],
                                                         sref2 = compare_s[i+1], zref2 = compare_z[i+1])
                    a_fill = (z[i] *(s_inter - compare_s[i]))/2
                    a_cut = (z[i+1]*(compare_s[i+1] - s_inter))/2
                    positive_tri.append(a_fill)
                    negative_tri.append(a_cut)

                if z[i] <= 0. and  z[i+1]>0 or z[i] < 0. and  z[i+1]>=0:
                    s_inter, z_inter = _intersect_coords(smod1 = x[i], zmod1 = y[i],
                                                         smod2 = x[i+1], zmod2 = y[i+1],
                                                         sref1 = compare_s[i], zref1 = compare_z[i],
                                                         sref2 = compare_s[i+1], zref2 = compare_z[i+1])
                    a_fill = (z[i+1]*(compare_s[i+1] - s_inter))/2
                    a_cut = (z[i] *(s_inter - compare_s[i]))/2
                    positive_tri.append(a_fill)
                    negative_tri.append(a_cut)

            fill = sum(positive_trap) + sum(positive_tri)
            cut = sum(negative_trap) + sum(negative_tri)
            total_area = abs(cut) + abs(fill)
            balance = fill + cut
            myax1.annotate('earthmoving: %.2f $m^3/m$ \n balance: %.2f $m^3/m$'% (total_area, balance), (self.smax/2, self.zmax-1), fontsize = _('x-small'))

            myax1.plot(compare_s,compare_z,color=_('red'), lw=2, ls = _('dashed'), label =_('Reference'))

            myax1.fill_between(x, y, compare_z, where=(y < compare_z), interpolate= True,color =_('none'),\
                                alpha = 0.2, hatch = _('///'), edgecolor= _('red'), label =_('Cuts: %.2f $m^3/m$'%(cut)))

            myax1.fill_between(x,  y, compare_z,where=(y > compare_z), interpolate= True, color =_('red'),\
                                alpha = 0.2, hatch = _('///'), edgecolor= _('white'), label=_('Fill: %.2f $m^3/m$'%(fill)))




        #Banks
        if sl != -99999.:
            myax1.plot(sl,zl,_('om'), label= _('Left bank'))
        if sb != -99999.:
            myax1.plot(sb,zb,_('ob'), label= _('River bed'))
        if sr != -99999.:
            myax1.plot(sr,zr,_('og'), label= _('Right bank'))
        if sld != -99999.:
            myax1.plot(sld,zld,_('*r'), label= _('Left bank down'))
        if srd != -99999.:
            myax1.plot(srd,zrd,_('*g'), label= _('Right bank down'))

        #Available simulations
        if zsimul is not None:
            for i in range(len(zsimul)):
                myax1.axhline(y=zsimul[i], color=_('blue'), alpha=0.7, lw=1, label =_('Simulation'), ls =_('dashed'))
                myax1.annotate(idsimul[i], (self.smax/2, zsimul[i] +0.1 ), alpha=0.7 , fontsize = _('xx-small'), color=_('blue'))

        #Displayed water level
        myax1.fill_between(x,y, fwl, where= y < fwl ,facecolor=_('cyan'),alpha=0.3,interpolate=True)

        #Figure parameter
        if zsimul is not None:
            myax1.set_ylim(self.zmin, max(self.zmax +1, max(zsimul) + 1, max(max_z)+1))   #In case the water level in a simulation is above the maximum altitude of the profile.

        elif max_z != []:
            myax1.set_ylim(self.zmin, max(self.zmax, max(max_z)+1))

        else:
            myax1.set_ylim(self.zmin, self.zmax +1)

        myax1.set_xlim(min(x), max(x))
        myax1.set_xlabel(_('Section Width ($m$)'), size=12)
        myax1.set_ylabel(_('Altitude - Z \n($m$)'), size=12)

        ## equal aspect between axis
        if forceaspect:
            myax1.set_aspect(_('equal'), adjustable=_('box'))

        ## Second Y - axis --> relationship functions
        def alt_to_depth(y):
            return y-self.zmin
        def depth_to_alt(y):
            return y+self.zmin

        secax = myax1.secondary_yaxis(_('right'), functions=(alt_to_depth, depth_to_alt))

        myax1.grid(axis=_('y'), ls= _('--'))

        if show:
            fig.show()

        return sl, sb, sr, zl, zb, zr

    def plotcs_discharges(self,
                          fig: Figure = None,
                          ax: Axes = None,
                          fwl: float = None,
                          fwd: float = None,
                          fwq: float = None,
                          simuls:list=None,
                          show:bool = False,
                          clear:bool = True,
                          labels:bool = True,
                          redraw:bool =True,
                          force_label_to_right:bool = True):
        """
        This method plots the discharges relationship computed
        with the methods: relations and ManningStrcikler_profile.

        - fwl: for water level,
        - fwd: for water depth,
        - fwq: for water discharge,
        - idsimul: list of available numerical models.
        - qsimul: list of discharges in the available numerical models,
        - hsimul: list of water depth in the available numerical models.

        :param fig: Matplotlib figure
        :param ax: Matplotlib axes
        :param fwl: water level to plot (if None, no water level is plotted)
        :param fwd: water depth to plot (if None, no water level is plotted)
        :param fwq: discharge to plot (if None, no discharge is plotted)
        :param simuls: list of simulations containing the profile (id, name, date, time, discharge, water level)
        :param show: if True, show the figure
        :param clear: if True, clear the axis before plotting
        :param labels: if True, show the legend
        :param redraw: if True, redraw the figure after plotting
        """

        if self.q_slope is None:
            raise Exception(_('Please compute the discharge relationship first using the method "ManningStrickler_profile"'))

        hsimul  = None
        qsimul  = None
        idsimul = None
        if simuls is not None:
            if len(simuls)>0:
                hsimul = [cursimul[2] for cursimul in simuls]
                qsimul = [cursimul[1] for cursimul in simuls]
                idsimul= [cursimul[0] for cursimul in simuls]


        sl,sb,sr,zl,zb,zr, sld, srd, zld, zrd = self.get_sz_banksbed()
        x,y = self.get_sz()

        if fwl is None:
            if fwd is None or fwd <= 0:
                fwd =0
                fwl= self.zmin+ fwd
                plot_wl = False
            elif fwd > 0 :
                fwl = self.zmin + fwd
                plot_wl = True

        elif fwl is not None:
            fwl = fwl
            fwd = fwl-self.zmin
            plot_wl = True

        if fig is None:
            fig, ax = plt.subplots()

        # Creation of a new ax for cleaning purposes in the wolfhece.Graphprofile.
        myax2 = ax
        if redraw:
            if clear:
                myax2.clear()

        # Discharges in available numerical models
        if qsimul is not None and hsimul is not None:
            myax2.scatter(qsimul,hsimul + self.zmin, c=_('blue'), alpha= 0.8, label =_('Available models'))
            for i in range(len(qsimul)):
                myax2.annotate(idsimul[i], (qsimul[i], hsimul[i] + self.zmin), alpha= 0.8, fontsize = _('xx-small'),color =_('blue'))

        # plots
        myax2.plot(self.criticaldischarge,self.waterdepth + self.zmin,color=_('red'),lw=2.0,label=_('Critical Discharge ($m^3/s$)'), ls =_('dashed'))
        myax2.plot(self.q_slope,self.waterdepth + self.zmin ,color=_('black'),lw=2.0,label=_('Q - chosen slope'))

        # Other  curves are plotted only if the cross sections are sorted along the river bed.
        if self and self.down and self.up:
            myax2.plot(self.q_down,self.waterdepth + self.zmin,color=_('black'),lw=1.0,label=_('Q - slope (%s - %s)')%(self.myname,self.down.myname), alpha = 0.5, ls = _('dotted'))
            myax2.plot(self.q_up,self.waterdepth + self.zmin,color=_('black'),lw=1.0,label=_('Q slope (%s - %s)')%(self.up.myname,self.myname), alpha= 0.5, ls= _('--'))     #Plot the evolution of the uniform discharge as function of water depth
            myax2.plot(self.q_centered,self.waterdepth + self.zmin ,color=_('black'),lw=1.0,label=_('Q slope (%s -  %s)')%(self.up.myname,self.down.myname), alpha = 0.5, ls = _('-.'))

        # Displayed discharge
        if fwq is not None:
            myax2.axvline(x=fwq, color=_('blue'), alpha=1, lw=2, label =_(' QD - Desired discharge'))

        # River banks
        if zl and zr and zb:
            myax2.axhline(y=zl, color=_('magenta'), alpha=1, lw=1, label =_('Left bank'), ls =_('dotted'))
            myax2.axhline(y=zr, color=_('green'), alpha=1, lw=1, label =_('Right bank'), ls =_('dotted') )
            myax2.axhline(y=zb, color=_('blue'), alpha=1, lw=1, label =_('Bed'), ls =_('dotted'))

        # Desired water depth
        if plot_wl:
            myax2.axhspan(ymin= self.zmin, ymax =fwl,color=_('cyan'), alpha=0.2, lw=2, label =_('Desired water depth'))

        myax2.set_xlabel(_('Discharge - Q ($m^3/s$)'), size=12)
        myax2.set_ylim(self.zmin, self.zmax+1)

        if qsimul is not None:
            myax2.set_xlim(0., max(max(self.q_down),max(self.q_up),max(self.q_centered),max(self.q_slope), max(self.criticaldischarge),max(qsimul)))
        else:
            if self and self.down and self.up:
                myax2.set_xlim(0., max(max(self.q_down),max(self.q_up),max(self.q_centered),max(self.q_slope), max(self.criticaldischarge)))
            else:
                myax2.set_xlim(0., max(max(self.q_slope), max(self.criticaldischarge)))

        # Conversion methods for the second matplotlib ax
        def alt_to_depth(y):
            return y-self.zmin
        def depth_to_alt(y):
            return y+self.zmin

        secax = myax2.secondary_yaxis('right', functions=(alt_to_depth,depth_to_alt))
        #secax.set_yticks(y)
        myax2.yaxis.tick_left()
        #myax2.set_yticks(alt_to_depth(self.waterdepth))
        #secax.set_yticks(self.waterdepth +self.ymin)

        #myax2.grid(axis= 'y' , ls= _('--'))

        myax2.grid(axis ='both')



        if labels:
            myax2.set_ylabel(_('Altitude - Z ($m$)'), size=12, rotation=270,labelpad=35)
            if force_label_to_right:
                myax2.yaxis.set_label_position('right')
            secax.set_ylabel(_('Water depth - h ($m$)'), size=12, labelpad=10)
            fig.suptitle('Discharges C.S. - %s'%(self.myname), size=15)


        if show:
            fig.show()

    def plot_discharges_UnCr(self,
                          fig: Figure = None,
                          ax: Axes = None,
                          fwl: float = None,
                          fwd: float = None,
                          fwq: float = None,
                          simuls:list=None,
                          show:bool = False,
                          clear:bool = True,
                          labels:bool = True,
                          redraw:bool =True,
                          force_label_to_right:bool = False):

        self.plotcs_discharges(fig, ax, fwl, fwd, fwq, simuls, show, clear, labels, redraw, force_label_to_right)

    def plotcs_hspw(self,
                    fig:Figure = None, ax:Axes = None,
                    fwl:float = None, fwd:float = None,
                    fwq:float = None,
                    show:bool = False, clear:bool = True,
                    labels:bool = True, redraw:bool =True,
                    force_label_to_right:bool = True):

        """
        This method plots the hydraulic geometries computed by the relations method
        (Hydraulic radius, wetted area, wetted perimeter, Top width).

        - fwl: for water level,
        - fwd: for water depth,
        - fwq: for water discharge.

        :param fig: Matplotlib figure
        :param ax: Matplotlib axes
        :param fwl: water level to plot (if None, no water level is plotted)
        :param fwd: water depth to plot (if None, no water level is plotted)
        :param fwq: discharge to plot (if None, no discharge is plotted)
        :param show: if True, show the figure
        :param clear: if True, clear the axis before plotting
        :param labels: if True, show the legend
        :param redraw: if True, redraw the figure after plotting

        """
        if self.waterdepth is None:
            self.relations()

        if fig is None and ax is None:
            fig, ax = plt.subplots()

        sl,sb,sr,zl,zb,zr, sld, srd, zld, zrd = self.get_sz_banksbed()
        x,y = self.get_sz()

        if fwl is None:
            if fwd is None or fwd <= 0:
                fwd =0
                fwl= self.zmin+ fwd
                plot_wl = False
            elif fwd > 0 :
                fwl = self.zmin + fwd
                plot_wl = True

        elif fwl is not None:
            fwl = fwl
            fwd = fwl-self.zmin
            plot_wl = True

        # Creation of a new ax for cleaning purposes in the wolfhece.Graphprofile.
        myax3 = ax
        axt3 = ax
        if redraw:
            if clear:
                axt3.clear()
                # myax3.clear()

        # Plots
        # FIXME (Clearing issues) a second x axis for the Hydraulic radius to provide more clarity.
        axt3.plot(self.hydraulicradius,self.waterdepth + self.zmin,color=_('green'),lw=2,label=_('H - Hydraulic radius($m$)'), ls= _('--')) #Plot the evaluation of the hydraulic radius as function of water depth
        axt3.set_xlim(0, max(self.hydraulicradius))

        myax3.plot(self.wetarea,self.waterdepth + self.zmin,color=_('black'),lw=2.0,label=_('S - Wet area ($m^2$)'))          #Plot the wetted area as function of water depth
        myax3.plot(self.wetperimeter,self.waterdepth + self.zmin,color=_('magenta'),lw=1,label=_('P -  Wet perimeter($m$)'))  #Plot the wetted perimeter as function of water depth
        myax3.plot(self.localwidth,self.waterdepth + self.zmin,color=_('red'),lw=1,label=_('W - Top Width ($m$)'))      #Plot the evalution of the water table as function of water depth

        # Selection of hydraulic geometries based on their index
        if fwq is not None and fwq > 0.:
            # First, We select the closest critical discharge to the user's input.
            mask = np.absolute(self.criticaldischarge - fwq)
            index  = np.argmin(mask)
            # Second, since the matrices have the same shapes and their elements are sorted likewise,
            # we use the index of the selected critical discharge to find the corresponding hydraulic geometries.
            cr_wetarea = self.wetarea[index]
            cr_wetperimeter = self.wetperimeter[index]
            cr_width = self.localwidth[index]
            cr_radius = self.hydraulicradius[index]
            cr_h = self.waterdepth[index]
            myax3.plot(cr_wetarea,cr_h + self.zmin,'ok' )
            myax3.annotate(_('$Critical$ $characteristics$ \nH: %s $m$ \nS: %s $m^2$ \nP: %s $m$ \nW: %s $m$  \n \n')% (round(cr_radius,2),round(cr_wetarea,2),round(cr_wetperimeter,2),round(cr_width,2)),\
                 (cr_wetarea, cr_h + self.zmin),  alpha= 1, fontsize = _('x-small'),color =_('black'))

            #Finally, we plot the critical hydraulic geometries as dots.
            myax3.plot(cr_wetperimeter,cr_h + self.zmin,_('om') )
            myax3.plot(cr_width,cr_h + self.zmin,_('or') )
            myax3.plot(cr_radius,cr_h + self.zmin,_('og') )

        #Displayed water depths and banks
        if plot_wl:
            myax3.axhspan(ymin= self.zmin, ymax =fwd + self.zmin,color=_('cyan'), alpha=0.2, lw=2, label =_('Desired water depth'))

        if zl != -99999.:
            myax3.axhline(y=zl, color=_('magenta'), alpha=1, lw=1, label =_('Left bank'), ls =_('dotted') )
        if zr != -99999.:
            myax3.axhline(y=zr, color=_('green'), alpha=1, lw=1, label =_('right bank'), ls =_('dotted') )
        if zb != -99999.:
            myax3.axhline(y=zb, color=_('blue'), alpha=1, lw=1, label =_(' bed '), ls =_('dotted'))

        #Limits and labels
        myax3.set_ylim(self.zmin,self.zmax+1)
        myax3.set_xlim(0., max(max(self.wetarea), max(self.wetperimeter), max(self.localwidth)))
        myax3.set_xlabel(_('S - P - W'), size=12)
        myax3.set_ylabel(_('Altitude - Z ($m$)'), size=12,rotation=270, labelpad=50)

        #Conversion methods for the second y axis
        def alt_to_depth(y):
            return y-self.zmin
        def depth_to_alt(y):
            return y+self.zmin
        secax = myax3.secondary_yaxis('right', functions=(alt_to_depth,depth_to_alt))

        myax3.yaxis.tick_left()
        if force_label_to_right:
            myax3.yaxis.set_label_position('right')
        if labels:
            secax.set_ylabel(_('Water depth - h ($m$)'), size=12, rotation=270, labelpad=20)
        myax3.grid()

        if show:
            fig.show()

    def plotcs_relations(self,
                    fig:Figure = None, ax:Axes = None,
                    fwl:float = None, fwd:float = None,
                    fwq:float = None,
                    show:bool = False, clear:bool = True,
                    labels:bool = True, redraw:bool =True,
                    force_label_to_right:bool = False
                    ):
        """
        This method plots the cross section relations (geometry, hydraulic geometries)

        It is the same than 'plotcs_hspw' but with (force_label_to_right = False) by default
        """

        self.plotcs_hspw(fig=fig, ax=ax,
                         fwl=fwl, fwd=fwd,
                         fwq=fwq,
                         show=show, clear=clear,
                         labels=labels, redraw=redraw,
                         force_label_to_right=force_label_to_right)


    def plot_linked(self, fig:Figure, ax:Axes, linked_arrays:dict, colors:list=['red','blue','green']):
        """ Plot linked arrays on the section plot """

        from .wolf_array import WolfArray

        # colors=['red','blue','green']
        nb_colors = len(colors)

        k=0
        for curlabel, curarray in linked_arrays.items():

            curarray:WolfArray
            if curarray.plotted:

                length = self.linestring.length
                ds = min(curarray.dx,curarray.dy)
                nb = int(np.ceil(length/ds*2))

                alls = np.linspace(0, length, nb, endpoint=True)

                pts = [self.linestring.interpolate(curs) for curs in alls]

                allz = [curarray.get_value(curpt.x,curpt.y) for curpt in pts]

                if np.max(allz)>-99999:
                    ax.plot(alls,allz,
                            color=colors[np.mod(k,nb_colors)],
                            lw=2.0,
                            label=curlabel)
                k+=1

    def _plot_only_cs(self,
                      fig:Figure=None, ax:Axes=None,
                      label='', alpha=0.8, lw=1., style: str ='dashed',
                      centerx=0., centery=0., grid=True, col_ax: str = 'black'):
        """ Plot only the cross section line on an existing axis """

        x,y=self.get_sz()

        sl,sb,sr,yl,yb,yr, sld, srd, yld, yrd = self.get_sz_banksbed()

        if centerx >0. and sb!=-99999.:
            decal = centerx-sb
            x+=decal
            sl+=decal
            sb+=decal
            sr+=decal

        if centery >0. and yb!=-99999.:
            decal = centery-yb
            y+=decal
            yl+=decal
            yb+=decal
            yr+=decal

        ax.plot(x,y,color=col_ax,
                lw=lw,
                linestyle=style,
                alpha=alpha,
                label=label)

        curtick=ax.get_xticks()
        ax.set_xticks(np.arange(min(curtick[0],(x[0]//2)*2),max(curtick[-1],(x[-1]//2)*2),2))

        if sl != -99999.:
            ax.plot(sl,yl,'or',alpha=alpha)
        if sb != -99999.:
            ax.plot(sb,yb,'ob',alpha=alpha)
        if sr != -99999.:
            ax.plot(sr,yr,'og',alpha=alpha)
        if sld != -99999.:
            ax.plot(sld,yld,'*r',alpha=alpha)
        if srd != -99999.:
            ax.plot(srd,yrd,'*g',alpha=alpha)

    def _plot_only_cs_min_at_x0(self,
                      fig:Figure=None, ax:Axes=None,
                      label='', alpha=0.8, lw=1., style: str ='dashed',
                      grid=True, col_ax: str = 'black'):

        """ Plot only the cross section line on an existing axis.
        We assume that the minimum elevation is at x=0.
        """

        x,y=self.get_sz()
        x = x - x[np.argmin(y)]

        ax.plot(x,y,color=col_ax,
                lw=lw,
                linestyle=style,
                alpha=alpha,
                label=label)


    def plot_cs(self,
                fwl:float = None, show:bool = False, forceaspect:bool = True,
                fig:Figure = None, ax:Axes = None,
                plotlaz:bool = True, clear:bool = True,
                linked_arrays:dict = {}):
        """ Plot the cross section with matplotlib - with options

        :param fwl: fill water level - if None, no filling
        :param show: if True, show the figure
        :param forceaspect: if True, force aspect ratio
        :param fig: figure Matplotlib
        :param ax: axes Matplotlib
        :param plotlaz: if True, plot LAZ points if available
        :param clear: if True, clear the axis before plotting
        :param linked_arrays: dictionary of linked arrays to plot on the section
        """

        if linked_arrays is None:
            linked_arrays = {}

        x,y=self.get_sz()

        sl,sb,sr,yl,yb,yr, sld, srd, yld, yrd = self.get_sz_banksbed()

        xmin=x[0]
        xmax=x[-1]
        ymin=self.get_minz()
        ymax=self.get_maxz()

        dy=ymax-ymin
        ymin-=dy/4.
        ymax+=dy/4.

        if ax is None:
            redraw=False
            fig = plt.figure()
            ax=fig.add_subplot(111)
        else:
            redraw=True
            if clear:
                ax.cla()

        if np.min(y) != -99999. and np.max(y) != -99999.:
            ax.plot(x,y,color='black',
                    lw=2.0,
                    label='Profil')

        if self.parent is not None:
            if plotlaz and self.parent.gridlaz is not None:
                minlaz=ymin
                maxlaz=ymax
                minlaz,maxlaz=self.plot_laz(fig=fig,ax=ax)
                if np.min(y) != -99999. and np.max(y) != -99999.:
                    ymin = min(ymin,minlaz)
                    ymax = max(ymax,maxlaz)
                else:
                    ymin = minlaz
                    ymax = maxlaz

        self.plot_linked(fig,ax,linked_arrays)

        if fwl is not None:
            ax.fill_between(x,y,fwl,where=y<=fwl,facecolor='cyan',alpha=0.3,interpolate=True)

        if sl != -99999.:
            ax.plot(sl,yl,'or')
        if sb != -99999.:
            ax.plot(sb,yb,'ob')
        if sr != -99999.:
            ax.plot(sr,yr,'og')
        if sld != -99999.:
            ax.plot(sld,yld,'*r')
        if srd != -99999.:
            ax.plot(srd,yrd,'*g')

        ax.set_title(self.myname)
        ax.set_xlabel(_('Distance [m]'))
        ax.set_ylabel('Elevation [EL.m]')
        ax.legend()

        tol=(xmax-xmin)/10.
        ax.set_xlim(xmin-tol,xmax+tol)
        ax.set_ylim(ymin,ymax)

        nbticks = 20
        dzticks = max((((ymax-ymin)/nbticks) // .25) *.25,.25)

        ax.set_yticks(np.arange((ymin//.25)*.25,(ymax//.25)*.25,dzticks))
        ax.grid()

        if forceaspect:
            aspect=1.0*(ymax-ymin)/(xmax-xmin)*(ax.get_xlim()[1] - ax.get_xlim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[0])
            ax.set_aspect(aspect)

        if show:
            fig.show()

        if redraw:
            fig.canvas.draw()

        return sl,sb,sr,yl,yb,yr

    def _plot_extremities(self, ax:plt.Axes, s:int = 50, colors:tuple[str, str] = ('blue', 'green')) -> None:
        """
        Plot the extremities of the cross-section on the given axes.
        """
        x_left = self[0].x
        y_left = self[0].y
        x_right = self[-1].x
        y_right = self[-1].y

        ax.scatter(x_left, y_left, color=colors[0], s=s, label='Left extremity')
        ax.scatter(x_right, y_right, color=colors[1], s=s, label='Right extremity')
        ax.legend()

    def _plot_extremities_sz(self, ax:plt.Axes, s:int = 10, colors:tuple[str, str] = ('blue', 'green')) -> None:
        """
        Plot the extremities of the cross-section on the given axes.
        """
        x_left = 0. #self[0].x
        y_left = self[0].z
        x_right = self.length2D #self[-1].x
        y_right = self[-1].z

        ax.scatter(x_left, y_left, color=colors[0], s=s)
        ax.scatter(x_right, y_right, color=colors[1], s=s)
        ax.legend()


class crosssections(Element_To_Draw):
    """
    Gestion de sections en travers pour différents formats
        - SPW 2000 --> format ='2000'
        - SPW 2022 --> format ='2022'
        - SPW_2025 --> format ='2025_xlsx'
        - WOLF vecz --> format ='vecz'
        - WOLF sxy --> format ='sxy'
        - WOLF zones --> format ='zones'

    L'objet stocke ses informations dans un dictionnaire : self.myprofiles
    Les clés de chaque entrée sont:
        ['index']   : integer
        ['left']    : wolfvertex
        ['bed']     : wolfvertex
        ['right']   : wolfvertex
        ['left_down'] : wolfvertex
        ['right_down']: wolfvertex
        ['cs']      : profile (surcharge de vector)

    Pour le moment, il est possible de lire les fichiers et d'effectuer certains traitements (tri selon vecteur, export gltf...).

    Une instance de cet objet peut être ajouté à une instance graphique WOLF pour affichage.
    Pour ce faire:
        - une propriété "myzones" de type "Zones" est présente pour stocker les sections sous forme WOLF "ZONES/ZONE/VECTOR/VERTICES". --> "crosssections" n'est donc pas une extension de "Zones" !!
        - deux instances de "cloud_vertices" contiennent les vertices des sections :
            - cloud
            - cloud_all

    :attention: !! La classe n'est pas encore prévue pour créer des sections en travers!!

    """

    myprofiles:dict[str | int: dict['cs':profile, 'index':int, 'left':wolfvertex, 'bed':wolfvertex, 'right':wolfvertex, 'left_down':wolfvertex, 'right_down':wolfvertex]]
    mygenprofiles:dict

    def __init__(self,
                 fn_or_Zones:str | Path | Zones = '',
                 format:typing.Literal['2000','2022', '2025_xlsx','vecz','sxy', 'zones']='2022',
                 dirlaz:typing.Union[str, xyz_laz_grids] =r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\LAZ_Vesdre\2023',
                 mapviewer = None,
                 idx='',
                 plotted=True,
                 from_zones:Zones = None,
                 force_unique_name:bool = False) -> None:
        """
        Constructor of the crosssections class

        ATTENTION:
        - If you use "from_zones", the cross-sections will be read from the provided Zones instance, overriding fn_or_Zones and format.
        - If you use "from_zones", the cross-sections will be added only if "used" in the Zones instance.
        - If you use "fn_or_Zones" as an instance of Zones, the format must be "zones". In this case, only the first zone will be used and cross-sections will be added even if not "used".

        :param fn_or_Zones: filename (str or Path) or instance of Zones containing the sections
        :param format: format of the sections file - '2000','2022','2025_xlsx','vecz','sxy', 'zones'
        :param dirlaz: directory containing LAZ files or instance of xyz_laz_grids
        :param mapviewer: instance of MapViewer (if None, no mapviewer is used)
        :param idx: index of the crosssections instance
        :param plotted: if True, the crosssections will be plotted in the mapviewer (if provided)
        :param from_zones: if not None, the sections will be read from the provided Zones instance (overrides fn_or_Zones and format)
        :param force_unique_name: if True, force unique names for each section (useful when reading from Zones)
        :return: None

        """

        self.dirlaz = None
        self.gridlaz = None

        assert format in ['2000','2022','2025_xlsx','vecz','sxy', 'zones'], _('Format %s not supported!')%format

        super().__init__(idx=idx, plotted= plotted, mapviewer=mapviewer, need_for_wx=False)

        if from_zones is not None:
            assert isinstance(from_zones, Zones), _('from_zones must be an instance of Zones!')
            self.filename = ''
            format=''
        elif isinstance(fn_or_Zones, Zones):
            assert format=='zones', _('If fn_or_Zones is an instance of Zones, format must be "zones"!')
            self.filename = fn_or_Zones.filename
        elif isinstance(fn_or_Zones, (str, Path)):
            self.filename = fn_or_Zones
        else:
            raise Exception(_('fn_or_Zones must be a string, Path or an instance of Zones!'))

        self.myzones=None
        self.myzone=None

        if isinstance(dirlaz, (str, Path)):
            if path.exists(dirlaz):
                self.dirlaz=dirlaz
                self.gridlaz = xyz_laz_grids(self.dirlaz)
            else:
                self.dirlaz=''
                self.gridlaz =None

        elif isinstance(dirlaz,xyz_laz_grids):
            self.gridlaz = dirlaz
            self.dirlaz = 'instance xyz_laz_grids'

        self.format = None

        self.linked_zones=None

        if format in ['2000','2022','sxy']:
            self.filename=fn_or_Zones
            if Path(fn_or_Zones).exists() and fn_or_Zones!='':
                f=open(fn_or_Zones,'r')
                lines=f.read().splitlines()
                f.close()
            else:
                lines = []
        elif format=='2025_xlsx':
            # For the 2025_xlsx format, we need to read the file using pandas
            if Path(fn_or_Zones).exists() and fn_or_Zones!='':
                # read the first sheet of the excel file
                # Note: header=1 means that the first row is not the header, but the second row is.
                logging.info(_('Reading cross section data from %s')%fn_or_Zones)
                try:
                    lines = pd.read_excel(fn_or_Zones, sheet_name=0, header=1)
                    logging.info(_('Cross section data read successfully from %s')%fn_or_Zones)
                except Exception as e:
                    logging.error(_('Error reading the file %s: %s')%(fn_or_Zones, str(e)))
                    lines = pd.DataFrame()
            else:
                logging.error(_('File %s does not exist!')%fn_or_Zones)
                lines = []
        # For other formats (e.g.  vecz)
        else:
            lines=[]

        self.myprofiles={}
        self.mygenprofiles={}

        self.cloud = None
        self.cloud_all = None

        self.multils = None

        self.sorted:dict[str, dict['sorted': list[vector], 'support':LineString]]
        # Dictionnaire des sections triées, peut contenir plusieurs tris selon différents vecteurs de tri.
        # Ceci est utile pour créer des sous-groupes de sections le long d'un cours d'eau ou de cours d'eau différents.
        # Chaque entrée est un dictionnaire avec les clés:
        #     - 'sorted' : liste des sections triées
        #     - 'support': LineString support du tri
        self.sorted = {}

        self.plotted = False

        if isinstance(lines, pd.DataFrame): # Format is '2025_xlsx'

            self.format='2025_xlsx'

            # We attend these columns:
            # 'Num', 'X', 'Y', 'Z', 'Code'
            if 'Num' not in lines.columns or 'X' not in lines.columns or 'Y' not in lines.columns or 'Z' not in lines.columns or 'Code' not in lines.columns:
                logging.error(_('The file %s does not contain the required columns: Num, X, Y, Z, Code')%self.filename)
                return

            nbsects = int(lines['Num'].max())

            # Convert X and Y to float
            lines['X'] = lines['X'].apply(lambda x: float(x.replace('.', '').replace(',', '.')) if isinstance(x, str) else float(x))
            lines['Y'] = lines['Y'].apply(lambda x: float(x.replace('.', '').replace(',', '.')) if isinstance(x, str) else float(x))
            # Convert Z to float and in meters
            # Note: The Z values are in mm, so we divide by 1000 to convert to meters.
            lines['Z'] = lines['Z'].apply(lambda x: float(x.replace('.', '').replace(',', '.'))/1000. if isinstance(x, str) else float(x)/1000.)

            for index in range(1, nbsects + 1):
                #création d'un nouveau dictionnaire
                name = str(index)
                curdict = self.myprofiles[name] = {}
                curdict['index'] = index
                curdict['cs'] = profile(name=name, parent=self)

                curdict['left'] = None
                curdict['bed'] = None
                curdict['right'] = None
                curdict['left_down'] = None
                curdict['right_down'] = None

                cursect:profile
                cursect = curdict['cs']

                df = lines[lines['Num'] == index]

                for ___, row in df.iterrows():
                    x = row['X']
                    y = row['Y']
                    z = row['Z']
                    label = row['Code']

                    # Add vertex to the current section
                    curvertex=wolfvertex(x,y,z)
                    cursect.add_vertex(curvertex)

                    if label == 'HBG':
                        if cursect.bankleft is None:
                            cursect.bankleft = wolfvertex(x,y,z)
                            curdict['left'] = cursect.bankleft
                        else:
                            logging.debug(name)
                    elif label == 'THA':
                        if cursect.bed is None:
                            cursect.bed=wolfvertex(x,y,z)
                            curdict['bed']=cursect.bed
                        else:
                            logging.debug(name)
                    elif label == 'HBD':
                        if cursect.bankright is None:
                            cursect.bankright=wolfvertex(x,y,z)
                            curdict['right']=cursect.bankright
                        else:
                            logging.debug(name)
                    elif label == 'BBG':
                        # This is a special case for the 2025 format, where the bank left down is defined as BBG (Bas Berge Gauche in French).
                        if cursect.bankleft_down is None:
                            cursect.bankleft_down = wolfvertex(x,y,z)
                            curdict['left_down'] = cursect.bankleft_down
                        else:
                            logging.debug(name)
                    elif label == 'BBD':
                        # This is a special case for the 2025 format, where the bank right down is defined as BBD (Bas Berge Droite in French).
                        if cursect.bankright_down is None:
                            cursect.bankright_down = wolfvertex(x,y,z)
                            curdict['right_down'] = cursect.bankright_down
                        else:
                            logging.debug(name)

        elif len(lines)>0:

            if format=='2000':
                self.format='2000'
                lines.pop(0)
                nameprev=''
                index=0
                for curline in lines:
                    vals=curline.split('\t')
                    name=vals[0]

                    if name!=nameprev:
                        #création d'un nouveau dictionnaire
                        self.myprofiles[name]={}
                        curdict=self.myprofiles[name]
                        curdict['index']=index
                        index+=1
                        curdict['cs']=profile(name=name,parent=self)
                        cursect:profile
                        cursect=curdict['cs']

                        curdict['left'] = None
                        curdict['bed'] = None
                        curdict['right'] = None
                        curdict['left_down'] = None
                        curdict['right_down'] = None

                    x=float(vals[1])
                    y=float(vals[2])
                    type=vals[3]
                    z=float(vals[4])

                    curvertex=wolfvertex(x,y,z)
                    cursect.add_vertex(curvertex)
                    if type=='LEFT':
                        if cursect.bankleft is None:
                            cursect.bankleft=wolfvertex(x,y,z)
                            curdict['left']=cursect.bankleft
                        else:
                            logging.debug(name)
                    elif type=='BED':
                        if cursect.bed is None:
                            cursect.bed=wolfvertex(x,y,z)
                            curdict['bed']=cursect.bed
                        else:
                            logging.debug(name)
                    elif type=='RIGHT':
                        if cursect.bankright is None:
                            cursect.bankright=wolfvertex(x,y,z)
                            curdict['right']=cursect.bankright
                        else:
                            logging.debug(name)

                    nameprev=name
            elif format=='2022':
                self.format='2022'
                lines.pop(0)
                nameprev=''
                index=0
                for curline in lines:
                    vals=curline.split('\t')

                    if vals[0].find('.')>0:
                        name=vals[0].split('.')[0]
                        xpos=1
                        ypos=xpos+1
                        zpos=ypos+1
                        labelpos=zpos+1
                    else:
                        name=vals[0]
                        xpos=2
                        ypos=xpos+1
                        zpos=ypos+1
                        labelpos=zpos+1

                    if name!=nameprev:
                        #création d'un nouveau dictionnaire
                        self.myprofiles[name]={}
                        curdict=self.myprofiles[name]
                        curdict['index']=index
                        index+=1
                        curdict['cs']=profile(name=name,parent=self)
                        cursect:profile
                        cursect=curdict['cs']
                        curdict['left'] = None
                        curdict['bed'] = None
                        curdict['right'] = None
                        curdict['left_down'] = None
                        curdict['right_down'] = None

                    x=float(vals[xpos].replace(',','.'))
                    y=float(vals[ypos].replace(',','.'))
                    z=float(vals[zpos].replace(',','.'))

                    curvertex=wolfvertex(x,y,z)
                    cursect.add_vertex(curvertex)

                    type=''
                    type=vals[labelpos]

                    if type=='HBG':
                        if cursect.bankleft is None:
                            cursect.bankleft=wolfvertex(x,y,z)
                            curdict['left']=cursect.bankleft
                        else:
                            logging.debug(name)
                    elif type=='TWG':
                        if cursect.bed is None:
                            cursect.bed=wolfvertex(x,y,z)
                            curdict['bed']=cursect.bed
                        else:
                            logging.debug(name)
                    elif type=='HBD':
                        if cursect.bankright is None:
                            cursect.bankright=wolfvertex(x,y,z)
                            curdict['right']=cursect.bankright
                        else:
                            logging.debug(name)

                    nameprev=name
            elif format=='sxy':
                self.format='sxy'
                nbpotsect = int(lines[0])
                index=1
                for i in range(nbpotsect):
                    vals=lines[index].split(',')
                    nbrel=int(vals[0])
                    index+=1
                    sz = np.asarray([np.float64(cursz) for k in range(index,index+nbrel) for cursz in lines[k].split(',') ]).reshape([nbrel,2],order='C')
                    self.mygenprofiles[i+1]=sz
                    index+=nbrel

                nbsect = int(lines[index])
                # o linked position in a 2D array (i, j) (integer,integer) (optional)
                # o datum (float) – added to the Z_min of the raw cross section (optional)
                # o boolean value indicating whether the relative datum must be added (logical)
                # o boolean value indicating whether it is a real or synthetic section (logical)
                # o ID of the cross section to which this line relates (integer)
                # o pair of coordinates of the left end point (float, float)
                # o pair of coordinates of the right end point (float, float)
                # o pair of coordinates of the minor bed (float, float) (optional)
                # o pair of coordinates of the left bank in local reference (float, float) (optional)
                # o pair of coordinates of the right bank in local reference (float, float) (optional)
                # o boolean value indicating whether an attachment point has been defined (optional)
                # # 2,2,0,#FALSE#,#TRUE#,16,222075.5,110588.5,222331.5,110777.5,99999,99999,99999,99999,99999,99999,#FALSE#
                # 2,2,0,#FALSE#,#TRUE#,17,222131.6,110608.2,222364.4,110667.9,99999,99999,99999,99999,99999,99999,#FALSE#
                index+=1
                #création d'un nouveau dictionnaire
                for i in range(nbsect):
                    name=str(i+1)
                    vals=lines[index].split(',')
                    index+=1

                    posi = int(vals[0])
                    posj = int(vals[1])
                    zdatum = float(vals[2])
                    add_zdatum=vals[3]=='#TRUE#'
                    real_sect=vals[4]=='#TRUE#'
                    id = int(vals[5])
                    startx=float(vals[6])
                    starty=float(vals[7])
                    endx=float(vals[8])
                    endy=float(vals[9])
                    beds=float(vals[10])
                    bedz=float(vals[11])
                    lbs=float(vals[12])
                    lbz=float(vals[13])
                    rbs=float(vals[14])
                    rbz=float(vals[15])
                    attached=vals[16]=='#TRUE#'

                    curdict=self.myprofiles[name]={}
                    curdict['index']=id
                    curdict['cs']=profile(name=name,parent=self)
                    cursect:profile
                    cursect=curdict['cs']
                    curdict['left'] = None
                    curdict['bed'] = None
                    curdict['right'] = None
                    curdict['left_down'] = None
                    curdict['right_down'] = None

                    cursect.zdatum = zdatum
                    cursect.add_zdatum = add_zdatum

                    cursect.set_sz(self.mygenprofiles[id],[[startx,starty],[endx,endy]])

                    if lbs!=99999:
                        cursect.bankleft=wolfvertex(lbs,lbz)
                        curdict['left']=cursect.bankleft
                    if beds!=99999:
                        cursect.bed=wolfvertex(beds,bedz)
                        curdict['bed']=cursect.bed
                    if rbs!=99999:
                        cursect.bankright=wolfvertex(rbs,rbz)
                        curdict['right']=cursect.bankright


        elif from_zones is not None:

            for curzone in from_zones.myzones:
                for curvec in curzone.myvectors:
                    if curvec.used:

                        if curvec.myname in self.myprofiles.keys():
                            if force_unique_name:
                                logging.info(_('Profile %s already exists in cross-sections. We change its name to %s.')%(curvec.myname, f"{curvec.myname}_{len(self.myprofiles)}"))
                                curvec.myname = f"{curvec.myname}_{len(self.myprofiles)}"
                            else:
                                logging.warning(_('Profile %s already exists in cross-sections. Previous will be overwritten.')%curvec.myname)

                        self.myprofiles[curvec.myname]={}
                        curdict=self.myprofiles[curvec.myname]

                        curdict['index']=len(self.myprofiles)
                        curdict['left']=None
                        curdict['bed']=None
                        curdict['right']=None
                        curdict['left_down'] = None
                        curdict['right_down'] = None

                        curdict['cs'] = profile(name=curvec.myname, parent=self)
                        cursect:profile
                        cursect=curdict['cs']

                        cursect.myvertices = curvec.myvertices.copy()

        elif len(lines)==0:

            if format=='vecz' or format=='zones':

                if isinstance(fn_or_Zones, Zones):
                    self.filename=fn_or_Zones.filename
                    tmpzones = fn_or_Zones

                elif isinstance(fn_or_Zones, (str, Path)):
                    self.filename=fn_or_Zones
                    tmpzones = Zones(fn_or_Zones, find_minmax=False)

                curzone:zone
                curvec:vector
                curzone = tmpzones.myzones[0]
                index=0
                for curvec in curzone.myvectors:

                    if curvec.myname in self.myprofiles.keys():
                        if force_unique_name:
                            logging.info(_('Profile %s already exists in cross-sections. We change its name to %s.')%(curvec.myname, f"{curvec.myname}_{index}"))
                            curvec.myname = f"{curvec.myname}_{index}"
                        else:
                            logging.warning(_('Profile %s already exists in cross-sections. Previous will be overwritten.')%curvec.myname)

                    self.myprofiles[curvec.myname]={}
                    curdict=self.myprofiles[curvec.myname]

                    curdict['index']=index
                    curdict['left']=None
                    curdict['bed']=None
                    curdict['right']=None
                    curdict['left_down'] = None
                    curdict['right_down'] = None

                    index+=1
                    curdict['cs']=profile(name=curvec.myname, parent=self, data_sect=curvec.myvertices.copy())

        self.verif_bed()
        self.find_minmax(True)
        self.init_cloud()


    @property
    def nb_profiles(self):
        """ Return the number of profiles in the cross-sections. """
        return len(self.myprofiles)

    def __getitem__(self, key):
        """ Get a profile by its name, index or (x, y) coordinates.

        :param key: The name or index  of the profile or coordinates where the search is performed.
        :type key: str | int | tuple | list
        :return: The profile corresponding to the key.
        :rtype: profile
        """

        if isinstance(key, str):
            return self.myprofiles[key]['cs']
        elif isinstance(key, int):
            return self.myprofiles[list(self.myprofiles.keys())[key]]['cs']
        elif isinstance(key, tuple | list):
            if len(key) == 2:
                x, y = key
                assert isinstance(x, float) and isinstance(y, float), _('Coordinates must be floats.')
                return self.select_profile(x, y)
        else:
            raise KeyError(_('Key must be a string or an integer or a tuple/list of (float, float).'))

    def init_cloud(self):
        """ Initialiaze cloud points for cross-sections. """

        self.cloud = cloud_vertices()
        self.cloud_all = cloud_vertices()
        self.fillin_cloud_all()

        self.cloud.myprop.filled=True
        self.cloud.myprop.width=8
        self.cloud_all.myprop.filled=True
        self.cloud_all.myprop.width=4

    def add(self, newprofile:profile | vector):
        """ Add a new profile or vector to the cross-sections.

        :param newprofile: A profile or vector to be added.
        :type newprofile: profile | vector
        """

        if isinstance(newprofile, profile):
            curvec = newprofile
            curdict = self.myprofiles[newprofile.myname] = {}

            curdict['index']=len(self.myprofiles)
            curdict['cs'] = newprofile
            curdict['left']= newprofile.bankleft_vertex.copy() if newprofile.bankleft_vertex else None
            curdict['bed']= newprofile.bed_vertex.copy() if newprofile.bed_vertex else None
            curdict['right']=newprofile.bankright_vertex.copy() if newprofile.bankright_vertex else None
            curdict['left_down'] = newprofile.bankleft_down_vertex.copy() if newprofile.bankleft_down_vertex else None
            curdict['right_down'] = newprofile.bankright_down_vertex.copy() if newprofile.bankright_down_vertex else None

        elif isinstance(newprofile, vector):
            curvec = newprofile
            curdict = self.myprofiles[curvec.myname] = {}

            curdict['index']=len(self.myprofiles)
            curdict['left']=None
            curdict['bed']=None
            curdict['right']=None
            curdict['left_down'] = None
            curdict['right_down'] = None

            cursect = curdict['cs'] = profile(name=curvec.myname,parent=self)
            cursect.myvertices = curvec.myvertices

    def get_linked_arrays(self):
        """
        Passerelle pour obntenir les matrices liées
        """
        if self.mapviewer is not None:
            return self.mapviewer.get_linked_arrays()
        else:
            return {}

    def get_profile(self, which_prof, which_dict:str=None):
        """
        Recherche et renvoi d'un profil sur base du nom ou de son index et éventuellement de la liste triée.

        :param which_prof: Nom du profil ou index du profil à rechercher.
        :type which_prof: str | int
        :param which_dict: Nom du dictionnaire trié à utiliser, si applicable.
        :type which_dict: str | None
        """
        if which_dict is not None:
            # on travaille sur les vecteurs triés
            if which_dict in self.sorted.keys():
                curlist = self.sorted[which_dict]['sorted']
                if isinstance(which_prof, str):
                    keys = [curprof.myname for curprof in curlist]
                    if which_prof in keys:
                        return curlist[keys.index(which_prof)]
                    else:
                        logging.error(_('Profile %s not found in sorted dictionaries!')%which_prof)
                        return None

                elif isinstance(which_prof, int):
                    if which_prof<0 or which_prof>=len(curlist):
                        logging.error(_('Index %d out of range (0 to %d)!')%(which_prof,len(curlist)-1))
                        return None

                    return curlist[which_prof]
            else:
                logging.error(_('Dictionary %s not found in sorted dictionaries!')%which_dict)
                return None

        else:
            if isinstance(which_prof, str):
                keys = self.myprofiles.keys()
                if which_prof in keys:
                    return self.myprofiles[which_prof]['cs']
                else:
                    logging.error(_('Profile %s not found!')%which_prof)
                    return None

            elif isinstance(which_prof, int):
                if which_prof<0 or which_prof>=len(self.myprofiles):
                    logging.error(_('Index %d out of range (0 to %d)!')%(which_prof,len(self.myprofiles)-1))
                    return None

                return self.myprofiles[list(self.myprofiles.keys())[which_prof]]['cs']
            else:
                logging.error(_('which_prof must be a string or an integer!'))
                return None

        return None

    def fillin_cloud_all(self):
        """ Fill the cloud_all with all vertices from all profiles. """

        curprof:profile
        for idx,vect in self.myprofiles.items():
            curprof=vect['cs']
            for curvert in curprof.myvertices:
                self.cloud_all.add_vertex(curvert)

        self.cloud_all.find_minmax()

    def update_cloud(self):
        """ Update the cloud with vertices from all profiles. """

        curprof:profile
        for idx,vect in self.myprofiles.items():
            curprof=vect['cs']
            if not curprof.bankleft is None:
                myvert = wolfvertex(curprof.bankleft.x,curprof.bankleft.y)
                self.cloud.add_vertex(myvert)
            if not curprof.bankright is None:
                myvert = wolfvertex(curprof.bankright.x,curprof.bankright.y)
                self.cloud.add_vertex(myvert)
            if not curprof.bed is None:
                myvert = wolfvertex(curprof.bed.x,curprof.bed.y)
                self.cloud.add_vertex(myvert)

            for idx,curvert in curprof.refpoints.items():
                self.cloud.add_vertex(curvert)

        self.cloud.find_minmax(True)

    def create_vector_from_centers(self, which_dict:str=None):
        """ Create a vector from the centers of the cross-sections."""

        if which_dict is not None:
            if which_dict not in self.sorted.keys():
                logging.error(_('Dictionary %s not found in sorted dictionaries!')%which_dict)
                return vector(name='center', is2D=False)

            curslist = self.sorted[which_dict]['sorted']
            centers = [curs.linestring.interpolate(0.5, normalized=True) for curs in curslist]
        else:
            centers = [curs['cs'].linestring.interpolate(0.5, normalized=True) for idx,curs in self.myprofiles.items()]

        newvec = vector(name='center', is2D=False)
        newvec.add_vertex([wolfvertex(pt.x, pt.y) for pt in centers])
        return newvec

    def create_vector_from_lefts(self, copy:bool=True, which_dict:str=None):
        """ Create a vector from the left (first vertex) of the cross-sections.

        :param copy: If True, create a copy of the left vertices. If False, use the original vertices.
        :type copy: bool
        """

        if which_dict is not None:
            if which_dict not in self.sorted.keys():
                logging.error(_('Dictionary %s not found in sorted dictionaries!')%which_dict)
                return vector(name='left', is2D=False)

            curslist = self.sorted[which_dict]['sorted']

        else:
            curslist = self.myprofiles.values()

        if copy:
            lefts = [curs['cs'][0].copy() for curs in curslist]
        else:
            lefts = [curs['cs'][0] for curs in curslist]

        newvec = vector(name='left', is2D=False)
        newvec.add_vertex(lefts)
        return newvec

    def create_vector_from_rights(self, copy:bool=True, which_dict:str=None):
        """ Create a vector from the right (last vertex) of the cross-sections.

        :param copy: If True, create a copy of the right vertices. If False, use the original vertices.
        :type copy: bool
        """

        if which_dict is not None:
            if which_dict not in self.sorted.keys():
                logging.error(_('Dictionary %s not found in sorted dictionaries!')%which_dict)
                return vector(name='right', is2D=False)

            curslist = self.sorted[which_dict]['sorted']
        else:
            curslist = self.myprofiles.values()

        if copy:
            rights = [curs['cs'][-1].copy() for curs in curslist]
        else:
            rights = [curs['cs'][-1] for curs in curslist]

        newvec = vector(name='right', is2D=False)
        newvec.add_vertex(rights)
        return newvec

    def check_left_right_coherence(self):
        """ Check the coherence of left and right banks in the cross-sections.

        :return: -2 if both banks intersect the center line, -1 if only left bank intersects, 1 if only right bank intersects, 0 if no intersection.
        :rtype: int
        """

        center = self.create_vector_from_centers()
        left = self.create_vector_from_lefts(copy=False)
        right = self.create_vector_from_rights(copy=False)

        # If the left bank intersects the center line, we have a problem.
        # If it is the case, the right bank must intersect the center line too.

        if center.linestring.intersects(left.linestring):
            if not center.linestring.intersects(right.linestring):
                logging.warning(_('Left bank intersects the center line, but right bank does not!'))
                return -1
            else:
                logging.info(_('Left and right banks intersect the center line. Please check the profiles.'))
                return -2
        else:
            if center.linestring.intersects(right.linestring):
                logging.warning(_('Right bank intersects the center line, but left bank does not!'))
                return 1
            else:
                logging.info(_('Left and right banks do not intersect the center line.'))
        return 0

    def create_zone_from_banksbed(self):
        """ Create a zone from the banks and bed of the cross-sections."""

        if self.linked_zones is None:
            return

        bed = [curs['cs'].bed for idx,curs in self.myprofiles.items()]
        left = [curs['cs'].bankleft for idx,curs in self.myprofiles.items()]
        right = [curs['cs'].bankright for idx,curs in self.myprofiles.items()]

        newzone=zone(name='banksbed',parent=self.linked_zones,is2D=False)
        self.linked_zones.add_zone(newzone)

        newvec = vector(name='left',is2D=False,parentzone=newzone)
        newvec.myvertices=left
        newzone.add_vector(newvec)

        newvec = vector(name='bed',is2D=False,parentzone=newzone)
        newvec.myvertices=bed
        newzone.add_vector(newvec)

        newvec = vector(name='right',is2D=False,parentzone=newzone)
        newvec.myvertices=right
        newzone.add_vector(newvec)

    def link_external_zones(self, mylink:Zones):
        """ Link the cross-sections to external zones. """

        self.linked_zones = mylink
        self.find_intersect_with_link_zones()

    def find_intersect_with_link_zones(self):
        """ Find intersections between the cross-sections and linked zones. """

        if self.linked_zones is None:
            return

        which=['THA','HBG','HBD']
        linkprop=['bed','left','right']

        for curzone in self.linked_zones.myzones:
            curzone:zone
            for myvec in curzone.myvectors:
                myvec:vector

                if myvec.myname in which:
                    curlinkprop = linkprop[which.index(myvec.myname)]
                else:
                    curlinkprop = myvec.myname

                myvecls = myvec.asshapely_ls()
                prepare(myvecls)

                for cursname in self.myprofiles.values():
                    curs:profile
                    curs=cursname['cs']
                    cursls = curs.asshapely_ls()
                    if myvecls.intersects(cursls):
                        pt = myvecls.intersection(cursls)

                        if pt.geom_type=='MultiPoint':
                            pt=pt.geoms[0]
                        elif pt.geom_type=='GeometryCollection':
                            pt=pt.centroid

                        try:
                            myvert=wolfvertex(pt.x,pt.y,pt.z)
                        except:
                            myvert=wolfvertex(pt.x,pt.y)

                        if curlinkprop=='bed':
                            curs.bed = myvert
                        elif curlinkprop=='left':
                            curs.bankleft = myvert
                        elif curlinkprop=='right':
                            curs.bankright = myvert
                        else:
                            curs.refpoints[curlinkprop]=myvert

                        cursname[curlinkprop]=myvert
                destroy_prepared(myvecls)

        self.update_cloud()

    def export_gltf(self,zmin,fn=''):
        """ Export the cross-sections to a GLTF file. """

        points=[]
        triangles=[]
        incr=0

        curs:profile
        for cursname in self.myprofiles.values():
            curs=cursname['cs']
            m, n = curs.triangulation_gltf(zmin)
            points.append(np.asarray(m,dtype=np.float32))
            triangles.append(np.asarray(n,dtype=np.uint32)+incr)
            incr += len(m)

        points = np.concatenate(points)

        tmpy=points[:,1].copy()
        points[:,1] = points[:,2].copy()
        points[:,2] = -tmpy.copy()
        triangles = np.concatenate(triangles)

        triangles_binary_blob = triangles.flatten().tobytes()
        points_binary_blob = points.tobytes()

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
                    count=triangles.size,
                    type=pygltflib.SCALAR,
                    max=[int(triangles.max())],
                    min=[int(triangles.min())],
                ),
                pygltflib.Accessor(
                    bufferView=1,
                    componentType=pygltflib.FLOAT,
                    count=len(points),
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

        if fn=='':
            fn=self.filename.rpartition('.')[0]+'gltf'

        gltf.save(fn)

    def export_gltf_gen(self,points,triangles,fn=''):
        """ Export generated cross-sections to a GLTF file. """

        triangles_binary_blob = triangles.flatten().tobytes()
        points_binary_blob = points.tobytes()

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
                    count=triangles.size,
                    type=pygltflib.SCALAR,
                    max=[int(triangles.max())],
                    min=[int(triangles.min())],
                ),
                pygltflib.Accessor(
                    bufferView=1,
                    componentType=pygltflib.FLOAT,
                    count=len(points),
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

        if fn=='':
            fn=self.filename.rpartition('.')[0]+'gltf'

        gltf.save(fn)

    def set_zones(self, forceupdate:bool=False):
        """ Set/Prepare the zones for the cross-sections. """

        if forceupdate:
            self.myzone=None
            self.myzones=None

        if self.myzones is None:
            self.myzones=Zones(is2D=False, mapviewer=self.mapviewer)
            self.myzones.force3D=True
            self.myzone=zone(name='CS',parent=self.myzones)
            self.myzones.add_zone(self.myzone)

            for curprof in self.myprofiles.keys():
                curdict=self.myprofiles[curprof]
                curvec=curdict['cs']
                curvec:profile
                if curvec.used:
                    self.myzone.add_vector(curvec, forceparent=True)

            if self.plotted:
                self._prep_listogl()

    def showstructure(self, parent=None, forceupdate=False):
        """ Show the structure of the cross-sections in the zones. """

        self.set_zones()
        self.myzones.showstructure(parent, forceupdate)

    def get_upstream(self) -> dict['cs':profile, 'index':int, 'left':wolfvertex | None, 'bed':wolfvertex | None, 'right':wolfvertex | None, 'left_down':wolfvertex | None, 'right_down':wolfvertex | None]:
        """ Get the upstream profile of the cross-sections."""

        curprof = self[0]

        if curprof.up is None:
            logging.warning(_('No upstream profile defined for profile %s.')%curprof.myname)
            return self.myprofiles[curprof.myname]

        while curprof.up is not curprof:
            curprof = curprof.up

        return self.myprofiles[curprof.myname]

    def get_downstream(self) -> dict['cs':profile, 'index':int, 'left':wolfvertex | None, 'bed':wolfvertex | None, 'right':wolfvertex | None, 'left_down':wolfvertex | None, 'right_down':wolfvertex | None]:
        """ Get the downstream profile of the cross-sections. """

        curprof = self[0]

        if curprof.down is None:
            logging.warning(_('No downstream profile defined for profile %s.')%curprof.myname)
            return self.myprofiles[curprof.myname]

        while curprof.down is not curprof:
            curprof = curprof.down

        return self.myprofiles[curprof.myname]

    def rename(self, fromidx:int, updown:bool=True):
        """" Rename the cross-sections starting from a given index.

        :param fromidx: The index from which to start renaming.
        :type fromidx: int
        :param updown: If True, renames upstream sections; if False, renames all sections.
        :type updown: bool
        """

        idx=fromidx

        if updown:
            curdict=self.get_upstream()
            curvec:profile
            curvec=curdict['cs']
            while curvec.down is not curvec:
                self.myprofiles[idx]=curdict
                self.myprofiles.pop(curvec.myname)
                curvec.myname=str(idx)
                idx+=1

                curdict = self.myprofiles[curvec.down.myname]
                curvec=curvec.down

            self.myprofiles[idx]=curdict
            self.myprofiles.pop(curvec.myname)
            curvec.myname=str(idx)
        else:
            mykeys=list(self.myprofiles.keys())
            for curprof in mykeys:
                curdict=self.myprofiles[idx]=self.myprofiles[curprof]
                self.myprofiles.pop(curprof)
                curdict['cs'].myname=str(idx)
                idx+=1

        self.set_zones(True)

    def saveas(self,filename:str | Path = None):
        """ Save the cross-sections to a file in the specified format. """

        self.forcesuper=False

        if filename is not None:
            self.filename = str(filename)

        assert isinstance(self.filename, str), _('Filename must be a string.')

        if self.filename is None:
            logging.error(_('No Filename -- Retry !'))
            return

        if self.filename.endswith('.vecz'):
            self.forcesuper=True
            self.saveas_wolfvec(self.filename)

        elif self.format=='2000' or self.format=='2022':

            with open(self.filename,'w') as f:
                f.write("Profile\tx\ty\tBerge\tz\n")
                for idx,locdict in self.myprofiles.items():
                    curprof=locdict['cs']
                    curprof.save(f)

        elif self.format=='2025_xlsx':
            # For the 2025_xlsx format, we need to save the data using pandas
            data = []
            for idx, locdict in self.myprofiles.items():
                curprof = locdict['cs']
                for vertex in curprof.myvertices:
                    data.append({
                        'Num': idx,
                        'X': vertex.x,
                        'Y': vertex.y,
                        'Z': vertex.z * 1000.,  # Convert to mm
                        'Code': self.get_label(locdict, vertex)
                    })

            df = pd.DataFrame(data)
            # we need to ensure that the header begins at the second row
            df = df[['Num', 'X', 'Y', 'Z', 'Code']]
            # Save to Excel file
            with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
                # Write a blank row first, then the data starting from row 2
                pd.DataFrame([]).to_excel(writer, sheet_name='Sheet1', index=False, header=False)
                df.to_excel(writer, sheet_name='Sheet1', index=False, startrow=1)

        elif self.format=='sxy':
            with open(self.filename,'w') as f:
                f.write(str(len(self.mygenprofiles)))
                for curid in self.mygenprofiles.keys():
                    cursect = self.mygenprofiles[curid]
                    f.write('{n},0'.format(n=len(cursect)))
                    for xy in cursect:
                        f.write('{x},{y}'.format(x=xy[0],y=xy[1]))
                f.write(str(len(self.myprofiles)))
                for curid in self.myprofiles.keys():
                    curdict = self.myprofiles[curid]
                    cursect:profile
                    cursect = curdict['cs']
                    locid=curdict['index']

                    f.write('2,2,{zdatum},{add_datum},#TRUE#,{id},{x1},{y1},{x2},{y2},{beds},{bedz},{lbs},{lbz},{rbs},{rbz},#FALSE#'.format(
                                    zdatum=xy[0],
                                    add_datum=xy[1],
                                    id=locid,
                                    x1=cursect.myvertices[0].x,
                                    y1=cursect.myvertices[0].y,
                                    x2=cursect.myvertices[-1].x,
                                    y2=cursect.myvertices[-1].y,
                                    beds=cursect.get_s_from_xy(cursect.bed),
                                    bedz=cursect.bed.z,
                                    lbs=cursect.get_s_from_xy(cursect.bankleft),
                                    lbz=cursect.bankleft.z,
                                    rbs=cursect.get_s_from_xy(cursect.bankright),
                                    rbz=cursect.bankright.z))

    def get_label(self, profile_dict:dict, vertex:wolfvertex):
        """ Get the label for a vertex based on its type.

        :param profile_dict: Dictionary containing the profile information.
        :type profile_dict: dict
        :param vertex: The vertex for which to get the label.
        :type vertex: wolfvertex
        :return: The label for the vertex.
        :rtype: str
        """
        try:
            if profile_dict['left'] is not None:
                if vertex.is_like(profile_dict['left']):
                    return 'HBG'

            if profile_dict['bed'] is not None:
                if vertex.is_like(profile_dict['bed']):
                    return 'THA'

            if profile_dict['right'] is not None:
                if vertex.is_like(profile_dict['right']):
                    return 'HBD'

            if profile_dict['left_down'] is not None:
                if vertex.is_like(profile_dict['left_down']):
                    return 'BBG'

            if profile_dict['right_down'] is not None:
                if vertex.is_like(profile_dict['right_down']):
                    return 'BBD'

            return ''
        except:
            logging.error(_('Error in get_label for vertex: {v}').format(v=vertex))
            logging.info(_('Please report this bug to Pierre Archambeau.'))
            return ''

    def verif_bed(self):
        """Verification de l'existence du point lit mineur sinon attribution de l'altitude minimale"""

        for idx,curvect in self.myprofiles.items():
            curprof=curvect['cs']
            if curprof.bed is None:
                curprof.bed = curprof.get_min()

    def get_min(self, whichname:str = '', whichprofile:profile = None):
        """ Get the minimum vertex of a profile or cross-section. """

        curvect:profile
        if whichname!='':
            curvect=self.myprofiles[whichname]['cs']
            curvert=curvect.myvertices

        elif whichprofile is not None:
            curvect=whichprofile['cs']
            curvert=curvect.myvertices
        return sorted(curvert,key=lambda x:x.z)[0]

    def asshapely_ls(self):
        """ Convert the cross-sections to a MultiLineString using Shapely. """

        mylines=[]
        curvect:profile
        for idx,curvect in self.myprofiles.items():
            mylines.append(curvect['cs'].asshapely_ls())
        return MultiLineString(mylines)

    def prepare_shapely(self):
        """ Prepare the cross-sections for Shapely operations. """

        self.multils = self.asshapely_ls()

    def sort_along(self, vecsupport:LineString | vector, name:str, downfirst=True):
        """
        Sélectionne les sections qui intersectent un vecteur support
        et les trie selon l'abscisse curviligne
        """

        if isinstance(vecsupport, vector):
            vecsupport = vecsupport.linestring
            to_destroy = False
        elif isinstance(vecsupport, LineString):
            prepare(vecsupport) #Prepare le vecteur support aux opérations récurrentes
            to_destroy = True
        else:
            raise TypeError(_('vecsupport must be a LineString or a vector.'))

        curdict = self.sorted[name]={}
        curdict['support'] = vecsupport
        mysorted = curdict['sorted']  = []
        length = vecsupport.length

        curvect:profile
        for idx,curv in self.myprofiles.items():
            #bouclage sur les sections
            curvect=curv['cs']
            #obtention de la section sous forme d'un objet Shapely
            myline = curvect.linestring
            if vecsupport.intersects(myline):
                # le vecteur intersecte --> on calcule le point d'intersection
                myintersect = vecsupport.intersection(myline)

                if myintersect.geom_type=='MultiPoint':
                    myintersect=myintersect.geoms[0]
                elif myintersect.geom_type=='GeometryCollection':
                    myintersect=myintersect.centroid

                #on projette l'intersection sur le support pour trouver l'abscisse curvi
                try:
                    mydist = vecsupport.project(myintersect)
                except:
                    pass

                #on ajoute le vecteur à la liste
                mysorted.append(curvect)
                if downfirst:
                    curvect.s = length - mydist
                else:
                    curvect.s = mydist

        if to_destroy:
            destroy_prepared(vecsupport)

        if len(mysorted)==0:
            logging.warning(_('No cross-section intersects the support vector!'))
            return 0

        #on trie le résultat en place
        mysorted.sort(key=lambda x:x.s)

        mysorted[0].down = mysorted[1]
        mysorted[0].up = mysorted[0]
        mysorted[-1].up = mysorted[-2]
        mysorted[-1].down = mysorted[-1]
        for idx in arange(1,len(mysorted)-1):
            mysorted[idx].down = mysorted[idx+1]
            mysorted[idx].up = mysorted[idx-1]

        return len(mysorted)

    def find_minmax(self, update:bool=False):
        """ Find the minimum and maximum coordinates of the cross-sections.

        :param update: If True, updates the min/max values based on the current profiles.
        :type update: bool
        """

        if len(self.myprofiles)==0:
            self.xmin = 0
            self.ymin = 0
            self.xmax = 0
            self.ymax = 0
            return

        if update:
            for idx,vect in self.myprofiles.items():
                vect['cs'].find_minmax(only_firstlast = True)

        self.xmin = min(vect['cs'].xmin for idx,vect in self.myprofiles.items())
        self.ymin = min(vect['cs'].ymin for idx,vect in self.myprofiles.items())
        self.xmax = max(vect['cs'].xmax for idx,vect in self.myprofiles.items())
        self.ymax = max(vect['cs'].ymax for idx,vect in self.myprofiles.items())

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """ Plotting cross-sections """
        self.set_zones()
        self.myzones.plot(sx, sy, xmin, ymin, xmax, ymax, size)

    def _prep_listogl(self):
        """ Prepare list of GL objects """
        self.myzones.prep_listogl()

    def saveas_wolfvec(self,filename:str):
        """ Save the cross-sections as a WOLF vector file. """
        self.set_zones()
        self.myzones.saveas(filename=filename)

    def select_profile(self, x:float, y:float) -> profile:
        """ Select the profile closest to the given coordinates (x, y).

        :param x: X coordinate of the point.
        :param y: Y coordinate of the point.
        """

        mypt = Point(x,y)
        distmin=1.e300
        profmin=None

        curprof:profile
        for idx,vect in self.myprofiles.items():
            curprof=vect['cs']
            myshap=curprof.asshapely_ls()

            try:
                dist=myshap.distance(mypt)

                if dist<distmin:
                    profmin=curprof
                    distmin=dist
            except:
                pass
        return profmin

class Interpolator():
    """
    Objet d'interpolation sur sections en travers

        - self.interpolants est une liste de listes
        - chaque élément de self.interpolants est également une liste de listes
        - chaque liste de self.interpolants[k] contient les wolfvertex de la section discrétisée

    """

    def __init__(self,
                 vec1:vector,
                 vec2:vector,
                 supports:list[vector],
                 ds:float = 1.,
                 epsilon:float = 5e-2) -> None:
        """
        Initialize the Interpolator with two vectors and a list of support vectors.

        Not all supports need to intersect both sections.
        First, we check if each support intersects the sections.
        If a support does not intersect both sections, it will be ignored.

        Support vectors must have Z coordinates.

        If the Z-coordinates at the intersection points between the supports and the sections are not identical,
        "alpha" values are computed for interpolation:

            alpha = Z_support / Z_section

        The Z-coordinate of each interpolated point is then:

            Z_interp = Z_section * alpha

        Alpha is linearly interpolated between the two sections according to
        the curvilinear abscissa. The same applies to the Z-coordinates of the supports and the sections.

        If the sections are not straight lines, a "trace" is defined by the intersection points
        between the supports and the sections. This trace is used to pre-compute the interpolation points.
        Then, deltas (in X and Y) are added to "deform" the local sections.
        These deltas are linearly interpolated between the two sections.

        :param vec1: The first vector representing the first section.
        :type vec1: vector | profile
        :param vec2: The second vector representing the second section.
        :type vec2: vector | profile
        :param supports: A list of support vectors used for interpolation. This should be a list of vectors, not a zone.
        :type supports: list[vector]
        :param ds: The step size for interpolation, default is 1.0 [m].
        :type ds: float
        :param epsilon: The tolerance for intersection checks, default is 5e-2 [m] (5 cm).
        :type epsilon: float
        """

        self.interpolants=[]

        sect1 = {} # local dict to store section 1 data
        sect2 = {} # local dict to store section 2 data

        self.no_intersect = {} # dict to store sections not intersected by supports
        for sup_key in supports:
            self.no_intersect[sup_key.myname] = []

        used_supports:dict[int: dict['vec':vector, int:float]] = {}

        #Linestrings shapely des sections 1 et 2
        #ATTENTION, SHAPELY est une librairie géométrique 2D --> des outils spécifiques ont été programmés pour faire l'interpolation 3D
        s1 = sect1['ls'] = vec1.linestring
        s2 = sect2['ls'] = vec2.linestring

        eps = epsilon  # Tolérance pour vérifier l'intersection

        # Check if sections intersect the supports at their endpoints, considering a small epsilon (eps) for precision issues
        def check_intersection(section_ls:LineString, vec:profile, myls:LineString, eps:float):
            loc = None
            # Try intersection at start
            pt = Point(section_ls.xy[0][0], section_ls.xy[1][0])
            pt_proj = myls.interpolate(myls.project(pt))
            length = pt_proj.distance(pt)
            intersected = length < eps
            if intersected:
                vec.myvertices[0].x = pt_proj.xy[0][0]
                vec.myvertices[0].y = pt_proj.xy[1][0]
                section_ls = vec.linestring
                loc = 'first'

            # Try intersection at end if not found at start
            if not intersected:
                pt = Point(section_ls.xy[0][-1], section_ls.xy[1][-1])
                pt_proj = myls.interpolate(myls.project(pt))
                length = pt_proj.distance(pt)
                intersected = length < eps
                if intersected:
                    vec.myvertices[-1].x = pt_proj.xy[0][-1]
                    vec.myvertices[-1].y = pt_proj.xy[1][-1]
                    section_ls = vec.linestring
                    loc = 'last'
            return intersected, section_ls, loc

        for idx_support, cur_trace in enumerate(supports):
            # Recherche des distances des intersections des sections sur le support

            # linestring of the current support
            cur_support_ls = cur_trace.linestring

            #intersections between the support vector and the sections
            i1 = cur_support_ls.intersects(s1) # check if intersects section 1 --> return True or False -- see https://shapely.readthedocs.io/en/2.1.1/reference/shapely.intersects.html

            # If the section does not intersect the support, two possibilities:
            # 1. The first vertex of the section is on/near the support line
            # 2. The last vertex of the section is on/near the support line
            # If neither is the case, we ignore this support.

            if not i1:
                i1, s1, _loc = check_intersection(s1, vec1, cur_support_ls, eps)

            i2 = cur_support_ls.intersects(s2) # check if intersects section 2
            if not i2:
                i2, s2, _loc = check_intersection(s2, vec2, cur_support_ls, eps)

            # Si le support intersecte les sections, on le conserve
            # et on le stocke dans le dictionnaire used_supports
            if i1 and i2:
                loc_sup = used_supports[len(used_supports)] = {}
                loc_sup['vec'] = cur_trace

            # Stores the sections id that are not intersected by the support
            support_key = cur_trace.myname
            if not i1:
                self.no_intersect[support_key].append(vec1.myname)
            if not i2:
                self.no_intersect[support_key].append(vec2.myname)

        # Need to reset the PREPARED linestrings
        # to ensure they are recalculated with the new coordinates
        # of the sections after the intersection checks.
        # This is necessary because the coordinates may have been adjusted
        # to ensure they are close to the support lines.
        # Otherwise, the linestrings may not reflect the actual geometry.
        vec1.reset_linestring()
        vec2.reset_linestring()

        s1 = vec1.linestring
        s2 = vec2.linestring

        # Loop over support vectors to find intersections with the sections
        #  - find the useful portion between intersections on the supports
        #  - compute the distances along the sections for these intersections
        for k in range(len(used_supports)):

            # distances des intersections des sections sur le support
            cur_trace:vector
            cur_trace = used_supports[k]['vec']

            cur_support_ls:LineString
            cur_support_ls = cur_trace.linestring

            # Coordonnées d'intersection du vecteur support avec les sections
            # On est certain que cela s'intersecte puisque l'on a vérifié juste avant

            # Section "amont"
            i1 = cur_support_ls.intersection(s1) # --> return a Point or MultiPoint -- see https://shapely.readthedocs.io/en/stable/reference/shapely.intersection.html
            if not i1:
                i1, s1, loc1 = check_intersection(s1, vec1, cur_support_ls, eps)
                if loc1=='first':
                    i1 = Point(s1.xy[0][0], s1.xy[1][0])
                elif loc1=='last':
                    i1 = Point(s1.xy[0][-1], s1.xy[1][-1])

            elif i1.geom_type=='MultiPoint':
                i1=i1.geoms[0]
                logging.debug('MultiPoint -- use first point or debug')


            # Section "aval"
            i2 = cur_support_ls.intersection(s2)
            if not i2:
                i2, s2, loc2 = check_intersection(s2, vec2, cur_support_ls, eps)
                if loc2=='first':
                    i2 = Point(s2.xy[0][0], s2.xy[1][0])
                elif loc2=='last':
                    i2 = Point(s2.xy[0][-1], s2.xy[1][-1])

            elif i2.geom_type=='MultiPoint':
                i2=i2.geoms[0]
                logging.debug('MultiPoint -- use first point or debug')

            # Les distances curvilignes, sur les sections, sont calculées
            # en projetant l'intersection du vecteur support et des sections
            sect1[k] = s1.project(i1)
            sect2[k] = s2.project(i2)

            # Les distances, sur le support, sont calculées en projetant
            # l'intersection du vecteur support et des sections
            used_supports[k][1] = cur_support_ls.project(i1)
            if used_supports[k][1] == -1.:
                # Problème de précision de calcul à gérer
                # Même type de problème que lors de la vérification de l'intersection

                # We test the distance to the first and last points of the section
                # to ensure we have a valid projection.
                # We project on the support AND the section and store the result
                # in the used_supports and sect1/sect2 dictionaries.

                pt_first = Point(vec1[0].x, vec1[0].y)
                pt_last  = Point(vec1[-1].x, vec1[-1].y)

                if cur_support_ls.distance(pt_first) < eps:
                    used_supports[k][1] = cur_support_ls.project(pt_first)
                    sect1[k] = s1.project(pt_first)

                elif cur_support_ls.distance(pt_last) < eps:
                    used_supports[k][1] = cur_support_ls.project(pt_last)
                    sect1[k] = s1.project(pt_last)

            used_supports[k][2] = cur_support_ls.project(i2)
            if used_supports[k][2] == -1.:
                # Problème de précision de calcul -- see previous comment
                pt_first = Point(vec2[0].x, vec2[0].y)
                pt_last  = Point(vec2[-1].x, vec2[-1].y)

                if cur_support_ls.distance(pt_first) < eps:
                    used_supports[k][2] = cur_support_ls.project(pt_first)
                    sect2[k] = s2.project(pt_first)

                elif cur_support_ls.distance(pt_last) < eps:
                    used_supports[k][2] = cur_support_ls.project(pt_last)
                    sect2[k] = s2.project(pt_last)

            # Replace the vector by the portion of the support vector between the two intersections
            used_supports[k]['vec'] = cur_trace.substring(used_supports[k][1], # curvilinear position of the intersection with section 1
                                                          used_supports[k][2], # curvilinear position of the intersection with section 2
                                                          is3D = False, # Compute in 2D, not 3D
                                                          adim = False  # In real coordinates, not adimensional
                                                          )


        # Bouclage sur les intervalles --> nb_supports-1
        for k in range(len(used_supports)-1):

            interpolant=[]
            self.interpolants.append(interpolant)

            cur_support_left:vector
            cur_support_right:vector
            curvec1:vector
            curvec2:vector

            # Morceaux de sections entre intersections avec le support.
            # Comme les distances ont été calculées avec Shapely,
            # on doit trouver les morceaux en 2D et non 3D.
            curvec1=sect1['sub'+str(k)]=vec1.substring(sect1[k],sect1[k+1],is3D=False,adim=False)
            curvec2=sect2['sub'+str(k)]=vec2.substring(sect2[k],sect2[k+1],is3D=False,adim=False)

            # Pointeurs vers les morceaux des supports
            cur_support_left = used_supports[k]['vec']
            cur_support_right = used_supports[k+1]['vec']

            # MAJ des longueurs 2D ET 3D
            cur_support_left.update_lengths()
            cur_support_right.update_lengths()
            curvec1.update_lengths()
            curvec2.update_lengths()

            # Trouve la liste des distances à traiter pour le maillage

            # Nombre de points (entier) à évaluer pour s'approcher de la distance ds souhaitée
            # On divise la longueur 3D maximales des sections par la taille souhaitée
            # et on arrondit à l'entier supérieur
            nbi_sect = np.ceil(max(curvec1.length3D, curvec2.length3D) / ds)
            if nbi_sect == 0:
                logging.warning(_('No points to interpolate between sections {s1} and {s2} with distance {d} m.').format(s1=curvec1.myname, s2=curvec2.myname, d=ds))
            else:
                locds  = 1./float(nbi_sect) # nouvelle distance de calcul

                # Create a list of adimensional distances where to interpolate
                # We use :
                # - the cumulative length of the sections to create a list of distances
                # - a range from 0 to 1 with the step size locds
                dist3d = np.concatenate([np.arange(0.,1.,locds),
                                         np.cumsum(curvec1._lengthparts3D) / curvec1.length3D,
                                         np.cumsum(curvec2._lengthparts3D) / curvec2.length3D])

                # Remove duplicates AND sort the distances
                dist3d = np.unique(dist3d)

            # Nombre de points à traiter sur les supports.
            # On divise la longueur 3D maximale des supports par la taille souhaitée
            # et on arrondi à l'entier supérieur
            nbi_support = int(np.ceil(max(cur_support_left.length3D, cur_support_right.length3D) / ds))

            # Nouvelle distance de calcul
            locds = 1./float(nbi_support)

            # Wolfvertex des points d'intersection des sections avec les supports

            # section amont/support gauche
            pt1_left  = curvec1.interpolate(s= 0., is3D = True, adim = True)
            # section amont/support droit
            pt1_right = curvec1.interpolate(s= 1., is3D = True, adim = True)

            # section aval/support gauche
            pt2_left  = curvec2.interpolate(s= 0., is3D = True, adim = True)
            # section aval/support droit
            pt2_right = curvec2.interpolate(s= 1., is3D = True, adim = True)

            # Vecteurs temporaires pour les sections.
            # Ces nouveaux vecteurs sont des segments de droite entre les intersections
            # des sections avec les supports.
            # Cela définit ainsi la trace des sections, même si en réalité tous leurs
            # points ne sont pas alignés.

            # Rappel : Cette procédure a au départ été écrite pour de vraies sections en travers.
            #          Elle a été adaptée pour fonctionner avec des sections 3D de forme quelconque.

            # Passage via vector pour conversion vers LineString
            # NDLR : on aurait sans doute pu faire plus simple ;-)
            s1_trace = vector(name= 'temp1')
            s2_trace = vector(name= 'temp2')

            s1_trace.add_vertex([pt1_left, pt1_right])
            s2_trace.add_vertex([pt2_left, pt2_right])

            # Convert to LineString for Shapely operations
            s1_trace = s1_trace.linestring
            s2_trace = s2_trace.linestring

            sloc = 0. # position adimensionnelle le long du support
            # On a calculé la distance utile de discrétisation "locds".
            # On va donc évoluer le long des supports en incrémentant "sloc" progressivement.

            # Compute alpha coefficients for left and right endpoints of the support vectors
            def safe_div(a, b):
                return a / b if b != 0. else 0.

            for s_along_sup in range(nbi_support + 1):

                logging.debug(str(s_along_sup))

                # Interpolation 3D sur les 2 supports
                #
                # Si le vecteur support est 3D, on souhaite utiliser les positions
                # relatives des points des sections par rapport aux points du support
                # pour calculer les positions des points interpolés.

                l1 = cur_support_left.interpolate(s= sloc, is3D= True, adim= True)
                l2 = cur_support_right.interpolate(s= sloc, is3D= True, adim= True)

                # Trace de la future section interpolée.
                # Tout comme "s1_trace" et "s2_trace"", c'est un segment de droite
                # qui servira de position de départ à laquelle des incréments seront ajoutés.
                # Cela définira les points de la section interpolée.
                #
                # On garde ici l'objet de type "vector"
                cur_trace=vector(name='loc')
                cur_trace.add_vertex([l1, l2])
                all_points_interp = []

                if l1.z != 0. and l1.z != -99999.:
                    # Le support est 3D
                    alpha1_left = safe_div(l1.z, pt1_left.z)
                    alpha2_left = safe_div(l1.z, pt2_left.z)
                else:
                    alpha1_left = 0.
                    alpha2_left = 0.

                if l2.z != 0. and l2.z != -99999.:
                    # Le support est 3D
                    alpha1_right = safe_div(l2.z, pt1_right.z)
                    alpha2_right = safe_div(l2.z, pt2_right.z)
                else:
                    alpha1_right = 0.
                    alpha2_right = 0.

                # Bouclage sur tous les points d'interpolation
                # sur les sections
                for curdist in dist3d:

                    # Interpolation 3D dans les 2 sections
                    cur1 = curvec1.interpolate(s= curdist, is3D = True, adim = True)
                    cur2 = curvec2.interpolate(s= curdist, is3D = True, adim = True)

                    # Pondération linéaire des alphas
                    alpha1 = alpha1_left * (1.-curdist) + alpha1_right*curdist
                    alpha2 = alpha2_left * (1.-curdist) + alpha2_right*curdist

                    # Projection 2D des points sur les traces des sections
                    # En fonction de la forme réelle de la section, ces projections
                    # pourraient ne pas être situées selon une abscisse curviligne
                    # strictement croissante le long de la section.
                    s_proj1 = s1_trace.project(Point(cur1.x, cur1.y))
                    s_proj2 = s2_trace.project(Point(cur2.x, cur2.y))

                    # Interpolation des points sur les traces des sections
                    proj_1 = s1_trace.interpolate(s_proj1)
                    proj_2 = s2_trace.interpolate(s_proj2)

                    s_proj1 /= s1_trace.length # adimensional position along the section 1
                    s_proj2 /= s2_trace.length # adimensional position along the section 2

                    # Relative position of the points on the support.
                    # We calculate the difference between the projected points and the original points.
                    dx1 = cur1.x - proj_1.x
                    dy1 = cur1.y - proj_1.y
                    dx2 = cur2.x - proj_2.x
                    dy2 = cur2.y - proj_2.y

                    # Linear ponderation of the differences
                    dx = dx1*(1.-sloc) + dx2*sloc
                    dy = dy1*(1.-sloc) + dy2*sloc
                    s  = s_proj1*(1.-sloc) + s_proj2*sloc

                    # !! Interpolation en 2D !! pour être cohérent avec le "s" des traces.
                    pt = cur_trace.interpolate(s, is3D = False, adim = True)

                    # Pondération des altitudes
                    zloc = cur1.z*alpha1 + sloc * (cur2.z*alpha2-cur1.z*alpha1)

                    # Ajout du point
                    all_points_interp.append(wolfvertex(pt.x+dx, pt.y+dy, zloc))

                # ajout de la liste des points interpolés dans la section
                interpolant.append(all_points_interp)

                # mise à jour de la position le long de la section
                sloc += locds

                # Limite la position à 1.0 pour éviter les débordements.
                # La sommation des distances ne garantit pas que la position
                # le long de la section soit strictement inférieure à 1.0.
                sloc = min(sloc,1.)


    def get_xyz_for_viewer(self, nbsub=10):
        """ Get the XYZ coordinates for the viewer.

        :param nbsub: Number of subdivisions for each segment, default is 10.
        :type nbsub: int
        :return: A numpy array of shape [(nb-1)*nbsub, 4] containing the XYZ coordinates.
        :rtype: np.ndarray
        """

        pts=self.interpolants

        nb=0
        for curpt in pts:
            for curl in curpt:
                nb+=(len(curpt)-1)*(len(curl)-1)*3+(len(curl)-1)+(len(curpt))

        pond=np.arange(0.,1.,1./float(nbsub))
        xyz=np.ones([(nb-1)*nbsub,4],order='F')
        start=0
        for curpt in pts:
            for k in range(len(curpt)-1):
                curl=curpt[k]
                nextl=curpt[k+1]
                for i in range(len(curl)-1):
                    v1=curl[i].getcoords()
                    v2=curl[i+1].getcoords()
                    v3=nextl[i].getcoords()

                    xyz[start:start+nbsub,:3]=[v1+(v2-v1)*curpond for curpond in pond]
                    start+=nbsub
                    xyz[start:start+nbsub,:3]= [v2+(v3-v2)*curpond for curpond in pond]
                    start+=nbsub
                    xyz[start:start+nbsub,:3]= [v3+(v1-v3)*curpond for curpond in pond]
                    start+=nbsub

            curl=curpt[-1]
            for i in range(len(curl)-1):
                v1=curl[i].getcoords()
                v2=curl[i+1].getcoords()
                xyz[start:start+nbsub,:3]=[v1+(v2-v1)*curpond for curpond in pond]
                start+=nbsub
            for k in range(len(curpt)-1):
                curl=curpt[k]
                nextl=curpt[k+1]
                v1=curl[-1].getcoords()
                v3=nextl[-1].getcoords()
                xyz[start:start+nbsub,:3]=[v1+(v3-v1)*curpond for curpond in pond]
                start+=nbsub

        return xyz

    def add_triangles_to_zone(self, myzone:zone):
        """ Add triangles to the specified zone based on the interpolants.

        :param myzone: The zone to which the triangles will be added.
        :type myzone: zone
        """

        nb=0
        npt=1
        for curpt in self.interpolants:
            for k in range(len(curpt)-1):
                curl=curpt[k]
                nextl=curpt[k+1]
                for i in range(len(curl)-1):
                    curvec = vector(name='tr'+'_'+str(npt)+'_'+str(k)+'_'+str(i),parentzone=myzone)
                    curvec.add_vertex([curl[i],curl[i+1],nextl[i]])
                    curvec.close_force()
                    curvec.myprop.used=False
                    myzone.add_vector(curvec)

                    curvec = vector(name='tr'+'_'+str(npt)+'_'+str(k+1)+'_'+str(i),parentzone=myzone)
                    curvec.add_vertex([nextl[i],curl[i+1],nextl[i+1]])
                    curvec.close_force()
                    curvec.myprop.used=False
                    myzone.add_vector(curvec)

            npt+=1
            nb+=(len(curpt)-1)*(len(curl)-1)*3+(len(curl)-1)+(len(curpt))

    def get_triangles(self, forgltf=True):
        """ Get the triangles and points for the interpolants.

        ATTENTION : gltf format coordinates as [x, z, -y] and "forgltf" is True by default.
        It is not the case in "get_points" where forgltf is False by default.

        :param forgltf: If True, formats the points for glTF export, default is True.
        :type forgltf: bool
        :return: A tuple containing the number of points, points array, and triangles array.
        :rtype: tuple[int, np.ndarray, np.ndarray]
        """
        points=[]
        triangles=[]
        nbpts=0
        nbtr=0
        for curpt in self.interpolants:

            nb_points_perline = len(curpt[0])
            nbsect=len(curpt)
            if forgltf:
                pointsloc=[[pt.x,pt.z,-pt.y] for curl in curpt for pt in curl]
            else:
                pointsloc=[[pt.x,pt.y,pt.z] for curl in curpt for pt in curl]

            trianglesloc=[[[k+decal*nb_points_perline+nbpts,
                        k+1+decal*nb_points_perline+nbpts,
                        nb_points_perline+k+decal*nb_points_perline+nbpts],

                        [nb_points_perline+k+decal*nb_points_perline+nbpts,
                        k+1+decal*nb_points_perline+nbpts,
                        nb_points_perline+k+decal*nb_points_perline+1+nbpts]]
                            for decal in range(len(curpt)-1) for k in range(nb_points_perline-1)]

            nbpts+=nb_points_perline*nbsect
            nbloc=(nb_points_perline-1)*(nbsect-1)*2
            nbtr+=nbloc

            points.append(pointsloc)
            triangles.append(np.asarray(trianglesloc).reshape([nbloc,3]))


        points=np.asarray(np.concatenate(points),dtype=np.float32)
        triangles=np.asarray(np.concatenate(triangles),dtype=np.uint32)


        if len(np.argwhere(np.isnan(points)==True))>0:
            logging.error(_('NaN values found in points array.'))
            raise ValueError(_('NaN values found in points array.'))

        return nbpts,points,triangles

    def get_points(self, forgltf=False):
        """ Get the points for the interpolants.

        ATTENTION : gltf format coordinates as [x, z, -y] and "forgltf" is False by default.
        It is not the case in "get_triangles" where forgltf is True by default.

        :param forgltf: If True, formats the points for glTF export, default is False.
        :type forgltf: bool
        :return: A tuple containing the number of points and the points array.
        :rtype: tuple[int, np.ndarray]
        """

        points=[]
        nbpts=0
        for curpt in self.interpolants:

            nb_points_perline = len(curpt[0])
            nbsect=len(curpt)
            if forgltf:
                pointsloc=[[pt.x,pt.z,-pt.y] for curl in curpt for pt in curl]
            else:
                pointsloc=[[pt.x,pt.y,pt.z] for curl in curpt for pt in curl]

            nbpts+=nb_points_perline*nbsect
            points.append(pointsloc)

        if forgltf:
            points=np.asarray(np.concatenate(points),dtype=np.float32)
        else:
            points=np.asarray(np.concatenate(points))

        return nbpts,points

    @classmethod
    def export_gltf(cls, points=None, triangles=None, fn:str | Path = None):
        """ Export the interpolated sections as a glTF file.

        GLTF can be opened in many 3D viewers, including Blender, Cesium, and others.

        :param points: Optional points array, if None, it will be generated from the interpolants.
        :type points: np.ndarray | None
        :param triangles: Optional triangles array, if None, it will be generated from the interpolants.
        :type triangles: np.ndarray | None
        :param fn: The filename to save the glTF file, if None, a file dialog will be shown.
        :type fn: str | Path | None
        :return: None
        :rtype: None
        """

        triangles_binary_blob = triangles.flatten().tobytes()
        points_binary_blob = points.tobytes()

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
                    count=triangles.size,
                    type=pygltflib.SCALAR,
                    max=[int(triangles.max())],
                    min=[int(triangles.min())],
                ),
                pygltflib.Accessor(
                    bufferView=1,
                    componentType=pygltflib.FLOAT,
                    count=len(points),
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

        if fn is not None:
            if isinstance(fn, str):
                fn = Path(fn)
        else:
            try:
                dlg=wx.FileDialog(None,_('Choose filename'),wildcard='binary gltf2 (*.glb)|*.glb|gltf2 (*.gltf)|*.gltf|All (*.*)|*.*',style=wx.FD_SAVE)
                ret=dlg.ShowModal()
                if ret==wx.ID_CANCEL:
                    dlg.Destroy()
                    return

                fn=dlg.GetPath()
                dlg.Destroy()
            except:
                logging.error(_('Wx FileDialog error. Is wx running ?'))
                return

        gltf.save(fn)

    def _export_gltf(self, fn:str | Path = None):
        """ Export the interpolated sections as a glTF file.

        GLTF can be opened in many 3D viewers, including Blender, Cesium, and others.

        :param points: Optional points array, if None, it will be generated from the interpolants.
        :type points: np.ndarray | None
        :param triangles: Optional triangles array, if None, it will be generated from the interpolants.
        :type triangles: np.ndarray | None
        :param fn: The filename to save the glTF file, if None, a file dialog will be shown.
        :type fn: str | Path | None
        :return: None
        :rtype: None
        """
        points, triangles= self.get_triangles()
        Interpolator.export_gltf(points, triangles, fn)



    def get_xy_z_for_griddata(self):
        """
        Get the XY and Z coordinates for griddata interpolation (Scipy).
        """
        xy = np.asarray([[curvertex.x,curvertex.y] for curpt in self.interpolants for curl in curpt for curvertex in curl])
        z = np.asarray([curvertex.z for curpt in self.interpolants for curl in curpt for curvertex in curl])

        return xy,z

class Interpolators():
    """
    Classe de gestion des interpolations sur sections en travers.

    La préparation de la triangulation est faite sur base de vecteurs supports (instance de type "Zones")
    et de sections en travers stockées dans une instance de type "crosssections".
    """

    def __init__(self, banks:Zones, cs:crosssections, ds:float = 1.) -> None:
        """
        Constructeur de la classe Interpolators.

        :param banks: Zones contenant les vecteurs supports (pay attention to the used property for zone and vectors)
        :param cs: objet 'crosssections' contenant les sections en travers --> voir PyCrosssections
        :param ds: distance souhaitée de discrétisation [m]
        """

        self.points    = None # Points for triangulation
        self.triangles = None # Triangles for triangulation

        # Convert the supports/banks to a list of vectors
        # All vectors in the zones will be used (independent of the zone name)
        # If a zone/vector is not used, it will not be included in the list
        self.mybanks = [curv for curzone in banks.myzones if curzone.used for curv in curzone.myvectors if curv.used]

        cs.set_zones() # Force the cross-sections to be set up as a Zones object

        self.myinterp:list[Interpolator]=[] # List of Interpolator objects

        # self.mycs = cs.myzones # pointer to the zones of the cross-sections
        zonecs = cs.myzones.myzones[0]

        if zonecs.myvectors[0].up is not None:
            # Les sections ont été triées sur base d'un vecteur support
            # On les traite dans l'ordre du tri
            cs1:profile
            cs1 = cs.get_upstream()['cs']

            while cs1.down is not cs1:
                cs2=cs1.down

                logging.info('{} - {}'.format(cs1.myname,cs2.myname))

                myinterp = Interpolator(cs1, cs2, self.mybanks, ds)

                if len(myinterp.interpolants)>0:
                    self.myinterp.append(myinterp)
                else:
                    logging.error('No interpolation found between {} and {}'.format(cs1.myname,cs2.myname))

                cs1=cs2
        else:
            # Les sections n'ont pas été triées
            # --> on les traite dans l'ordre d'énumération
            self.no_intersect = {} # Dictionary to store ID of sections not intersected by supports
            for sup_key in self.mybanks:
                self.no_intersect[sup_key.myname] = []

            for i in range(zonecs.nbvectors-1):
                cs1:vector
                cs2:vector
                cs1 = zonecs.myvectors[i]   # Cross-section 1
                cs2 = zonecs.myvectors[i+1] # Cross-section 2

                logging.info('{} - {}'.format(cs1.myname,cs2.myname))

                myinterp = Interpolator(cs1, cs2, self.mybanks, ds)

                # Accumulate non-intersecting section IDs from this interpolator to interpolate between the omitted sections later
                for sup_key in self.mybanks:
                    self.no_intersect[sup_key.myname].extend(myinterp.no_intersect[sup_key.myname])


                if len(myinterp.interpolants)>0:
                    self.myinterp.append(myinterp)
                else:
                    logging.error('No interpolation found between {} and {}'.format(cs1.myname,cs2.myname))

            # Fill the gaps between non-intersected sections
            # Convert stored section IDs to indices (preserve order, remove duplicates)
            for sup_key, ids in self.no_intersect.items():
                self.no_intersect[sup_key] = [zonecs.vector_names.index(id) for id in list(dict.fromkeys(ids))]
            keys = list(self.no_intersect.keys()) # List of support names
            for i in range(0, len(keys) - 1):
                left = self.no_intersect[keys[i]]
                right = self.no_intersect[keys[i + 1]]
                invalid_cs = sorted(set(left) | set(right))
                idx_cs = 0
                while idx_cs < len(invalid_cs):
                    if invalid_cs[idx_cs] == 0:
                        idx_cs += 1
                        continue # skip if first section invalid
                    elif invalid_cs[idx_cs] == zonecs.nbvectors - 1:
                        break # stop if last section invalid

                    idx_up = invalid_cs[idx_cs]-1
                    if idx_cs+1 < len(invalid_cs):
                        while invalid_cs[idx_cs] == invalid_cs[idx_cs+1]-1: # check for consecutive invalid sections
                            idx_cs += 1
                            if invalid_cs[idx_cs] == zonecs.nbvectors - 1:
                                break
                    idx_down = invalid_cs[idx_cs]+1
                    cs1 = zonecs.myvectors[idx_up]
                    cs2 = zonecs.myvectors[idx_down]
                    myinterp = Interpolator(cs1, cs2, self.mybanks[i:i+2], ds)
                    self.myinterp.append(myinterp)
                    idx_cs += 1


        self.add_interpolators(cs.myzones.parent)

    def add_interpolators(self, parent):
        """
        Ajout d'objets 'Interpolators' pour affichage/stockage
        """
        self.myzones = Zones(parent=parent)

        id=0
        points=[]
        triangles=[]
        decal=0

        for curinterp in self.myinterp:
            id+=1

            myzone = zone(name='Interpolator'+str(id), parent=self.myzones, is2D=False)
            myzone.used=False
            self.myzones.add_zone(myzone)
            curinterp.add_triangles_to_zone(myzone)

            nbpts,pts,tr=curinterp.get_triangles()

            points.append(pts)
            triangles.append(tr+decal)
            decal+=nbpts


        self.points, self.triangles = np.concatenate(points), np.concatenate(triangles)

    def export_gltf(self, fn:str | Path = None):
        """ Export the interpolated sections as a glTF file. """
        if self.points is None or self.triangles is None:
            logging.error('No points or triangles available for export.')
            return

        Interpolator.export_gltf(points=self.points, triangles=self.triangles, fn=fn)


    def viewer_interpolator(self):
        """ Display the interpolated sections in a viewer. """

        xyz=[]
        for curinterp in self.myinterp:
            xyz.append(curinterp.get_xyz_for_viewer())

        xyz=np.concatenate(xyz)

        myviewer(xyz,0)

    @property
    def points_xyz(self):
        """ Get the XYZ coordinates of the interpolated points.

        Points are stored as [x,z,-y] for glTF compatibility.
        Convert them to [x,y,z] for other uses.
        """
        pts = self.points.reshape([-1,3])[:,[0,2,1]].copy()  # Convert from [x,z,-y] to [x,y,z]
        pts[:,1] = -pts[:,1]  # Convert from -y to y
        return pts

    def interp_on_array(self, myarray,
                        method:Literal["nearest", "linear", "cubic"],
                        use_cloud:bool=True,
                        mask_outside_polygons:bool=False):
        """ Interpolate the sections on a WolfArray.

        :param myarray: The WolfArray to interpolate on.
        :type myarray: WolfArray
        :param method: The interpolation method to use, default is "linear".
        :type method: str
        :param use_cloud: If True, uses cloud interpolation, otherwise triangulation, default is True.
        :type use_cloud: bool
        """
        from .wolf_array import WolfArray
        from .PyVertexvectors import Triangulation

        myarray:WolfArray

        if use_cloud:
            xy=[]
            z=[]
            for curinterp in self.myinterp:
                tmpxy,tmpz = curinterp.get_xy_z_for_griddata()
                xy.append(tmpxy)
                z.append(tmpz)

            xy = np.concatenate(xy)
            z = np.concatenate(z)
            myarray.interpolate_on_cloud(xy,z,method)

            if mask_outside_polygons:

                # Mask points outside the polygons defined by the triangulation
                # Does not solve the problem of points alongside the polygons or on the vertices
                # observed in some cases if we use triangulation.
                #
                # Should be improved by searching the contour of the polygons
                # like the concatenation of external supports (left + last_section + right_inverted + first_section_inverted)

                tmp_tri = Triangulation(pts = self.points_xyz, tri=self.triangles)
                ij = myarray.get_ij_inside_listofpolygons(tmp_tri._get_polygons())
                myarray.array.mask[:,:] = True  # Mask all points
                myarray.array.mask[ij[:,0], ij[:,1]] = False  # Unmask
                myarray.set_nullvalue_in_mask()
        else:
            for interp in self.myinterp:
                n, pts, tri = interp.get_triangles(forgltf=False)
                myarray.interpolate_on_triangulation(pts, tri, interp_method= 'scipy')

    def saveas(self, fn: str | Path):
        """ Save the interpolators to files.

        Each interpolator will be saved as a separate file with a .tri extension.

        :param fn: The filename to save the interpolators.
        :type fn: str | Path
        """
        from .PyVertexvectors import Triangulation

        if isinstance(fn, str):
            fn = Path(fn)

        for i, interp in enumerate(self.myinterp):
            n, pts, tri = interp.get_triangles(forgltf=False)
            tmp_tri = Triangulation(pts = pts, tri = tri)
            tmp_tri.saveas(fn.parent / (fn.stem + f'_interp{i+1}.tri'))
