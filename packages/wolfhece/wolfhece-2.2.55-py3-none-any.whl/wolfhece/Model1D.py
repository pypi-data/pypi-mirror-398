"""
Author: HECE - University of Liege, Pierre Archambeau, Utashi Ciraane Docile
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

# --- Librairies ---
# __________________

import copy
import enum
import logging
import math
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np

import os, warnings
import pandas as pd
import shutil
import subprocess
import sys
import typing
import wx

from decimal import Decimal
from IPython.display import  HTML
from matplotlib import animation ,rcParams
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator,FuncFormatter
from PIL import Image
from shapely.ops import substring, split, LineString, Point
from subprocess import Popen, PIPE
from tqdm import tqdm
from typing import Literal,Union
from wx.dataview import TreeListCtrl

from .GraphProfile import PlotCSAll
from .PyCrosssections import crosssections, profile, postype, INTERSEC
from .PyHydrographs import Hydrograph
from .pylogging import create_wxlogwindow
from .PyParams import Wolf_Param
from .PyTranslate import _
from .PyVertexvectors import Zones, zone, vector, wolfvertex
from .wolf_array import WolfArray, header_wolf
from .wolf_vrt import crop_vrt
from .xyz_file import xyz_scandir

# --- Constants ---
# __________________

class Constants(enum.Enum):
    """Constants used in this module."""
    BANK_WIDTH = 1
    CENTERED_TEXT = wx.TE_CENTRE|wx.TE_PROCESS_ENTER|wx.TE_RICH
    DPI = 60
    FRAMESIZE = (960,540)
    GENERAL_FONTSIZE = 'small'
    GRAVITATION = 9.81
    NULL = -99999
    PRECISION = ':#.20F'
    SEPARATOR = '\t'
    TRANSPARENCY_FLOOD = 1
    TRANSPARENCY_RIVER = 1

    # PRECISION = ':#.20F' FIXME

# --- Titles and labels ---
# __________________________

class Titles(enum.Enum):
    """Titles used in this module."""
    BRANCH = _('')
    WX = _('WOLF - Create 1D model from 2D data')

# --- Colors ---
# ______________

class Colors(enum.Enum):
    """Colors used in this module.
    """
    BED = 'black'
    FLOODED_ALL = 'red'
    FLOODED_LEFT = 'green'
    FLOODED_RIGHT ='yellow'
    LEFT_BANK = 'red'
    MATPLOTLIB_CYCLE = rcParams["axes.prop_cycle"]()
    PROPOSED = wx.BLUE
    RIGHT_BANK = 'blue'
    RIVER_COLOR = 'cyan'
    TQDM = 'cyan'
    WX = 'white'

# --- File extensions ---
# _______________________
class fileExtensions(enum.Enum):
    """File extensions used in this module."""
    AINI = '.aini'
    BANKS = '.banks'
    BREADTH = '.breadth'
    CL = '.cl'          # Boundary conditions
    CVG = '.cvg'
    DEPTH ='.depth'
    DIAM = '.diam'
    GTV = '.gtv'
    HELP = '.help'
    HINI = '.hini'
    INF = '.inf'
    INFIL ='.infil'
    LENGHTSVECZ = '_lengths.vecz'
    LENGTHS = '.lengths'
    PARAMETERS = '.param'
    PTV = '.ptv'
    QINI ='.qini'
    ROUGHNESS = '.rough'
    TOP = '.top'
    VECTOR2D = '.vec'
    VECTOR3D = '.vecz'
    WIDTH = ''
    ZINI = '.zini'

# --- Creator of 1D models ---
# ____________________________

class Creator_1D:
    """Class for the creation of  1D modelS.
    This object contains the methods operations
    performed in the creation of 1D models.
    They consist of the following operations:
        - Concatenation of information in 1 and 2 dimensions,
        - Extraction of information from 2D data if provided,
        - Creation of a 1D model (simulation).

    .. todo:: 1) FIXME Create unittests for methods in this class,
    .. todo:: 2) FIXME Fasten the methods in this class using multiprocess.
    """

    def __init__(self):
        # Test whether an interface exists
        self.wx_exists = wx.App.Get()
        # Simulation directory
        self.directory_name = ''
        # Riverbed of the current model
        self.banksbed = None


    # --- Vectors operation (Wolf vectors)---
    # ________________________________________
    # FIXME Check whether this methods could not fit better in the module Pyvertexvectors.py

    def match_ends_2vectors(self,
                            zones1: Zones,
                            zones2: Zones,
                            id1:int = 0,
                            id2:int = 0) -> Zones:
        """Aligns the vertices of  2 successive zone
        containing each 3 vectors (1 vector and its 2 parallels).
        The idea is to match the end of each vector with
        the beginning of its corresponding in the other zone.

        :param zones1: First vector,
        :type zones1: Zones
        :param zones2: Second vector,
        :type zones2: Zones
        :param id1:  Position in `.myzones` of the zone
        containing the vectors, defaults to 0

        :type id1: int, optional
        :param id2: Position in `.myzones` of the zone
        containing the vectors, defaults to 0

        :type id2: int, optional
        :return: The 2 zones with the aligned vertices.
        :rtype: Zones
        """
        znes1 = zones1
        znes2 = zones2
        vecs1 = znes1.myzones[id1].myvectors
        vecs2 = znes2.myzones[id1].myvectors

        # selection of vectors and parallels based on their indexes
        for n in range(3):
            vector1_1 = vecs1[n]
            vector2_1 = vecs2[n]

            i = vector1_1.myvertices
            j = vector2_1.myvertices
            # Computation of all possible distances between the first and the last point
            distance1 = math.sqrt(((i[-1].x - j[0].x)**2) + ((i[-1].y - j[0].y)**2)) #last point - first point
            distance2 = math.sqrt(((i[-1].x - j[-1].x)**2) + ((i[-1].y - j[-1].y)**2)) #last point - last point
            distance1_r = math.sqrt(((i[0].x - j[0].x)**2) + ((i[0].y - j[0].y)**2)) # first point - first point
            distance2_r = math.sqrt(((i[0].x - j[-1].x)**2) + ((i[0].y - j[-1].y)**2)) #first point - last point

            all = [distance1, distance2, distance1_r, distance2_r]
            # Selection of the scenario based on a test of the least value
            if min(all) == distance2:
                vector2_1.myvertices.reverse()
            elif min(all) == distance1_r:
                vector1_1.myvertices.reverse()
            elif min(all) ==distance2_r:
                vector1_1.myvertices.reverse()
                vector2_1.myvertices.reverse()

        return znes1, znes2

    def delete_overlaps_2vectors(self,
                                 zones1: Zones,
                                 zones2: Zones,
                                 id1:int = 0,
                                 id2:int = 0,
                                 buffer:int = None ) -> Zones:
        """Delete overlapping vertices of 2 successive Vectors,
        containng each 3 vectors (1 vector and its 2 parallels).

        :param zones1: First vector,
        :type zones1: Zones
        :param zones2: second vector,
        :type zones2: Zones
        :param id1: Position in `.myzones` of the zone
        containing the vectors, defaults to 0

        :type id1: int, optional
        :param id2: Position in `.myzones` of the zone
        containing the vectors, defaults to 0

        :type id2: int, optional
        :param buffer: number of vertices to process on each vector
        starting from the end of the vector (None means all vertices are processed),
        defaults to None

        :type buffer: int, optional
        :return: The vectors with the deleted overlaps.
        :rtype: Zones

        .. todo:: 1) FIXME Generalize the method to work with any number of vectors.
        .. todo:: 2) FIXME iS there a way to perform this operation geometrically with shapely line string?
        .. todo:: 3) FIXME Create unittests for this method.
        """
        znes1 = zones1
        znes2 = zones2
        vector1_1 = znes1.myzones[id1].myvectors[0]
        vector1_2 = znes1.myzones[id1].myvectors[1]
        vector1_3 = znes1.myzones[id1].myvectors[2]
        vector2_1 = znes2.myzones[id2].myvectors[0]
        vector2_2 = znes2.myzones[id2].myvectors[1]
        vector2_3 = znes2.myzones[id2].myvectors[2]

        if buffer != None:
            buffer1 = buffer2 = buffer3 =buffer
        else:
            buffer1 = len(vector2_1.myvertices)
            buffer2 = len(vector2_2.myvertices)
            buffer3 = len(vector2_3.myvertices)


        distance1 = []
        distance2 = []
        distance_bed = []

        distance1_b = []
        distance2_b = []

        for i in  vector1_1.myvertices[-buffer1:]:
            for j in vector2_1.myvertices[:buffer1]:
                distance = math.sqrt(((i.x - j.x)**2) + ((i.y - j.y)**2))
                distance1.append(distance)

        for i in  vector1_3.myvertices[-buffer1:]:
            for j in vector2_1.myvertices[:buffer1]:
                distance = math.sqrt(((i.x - j.x)**2) + ((i.y - j.y)**2))
                distance2.append(distance)

        for i in  vector1_2.myvertices[-buffer2:]:
            for j in vector2_2.myvertices[:buffer2]:
                distance = math.sqrt(((i.x - j.x)**2) + ((i.y - j.y)**2))
                distance_bed.append(distance)


        for i in  vector1_1.myvertices[-buffer3:]:
            for j in vector2_3.myvertices[:buffer3]:
                distance = math.sqrt(((i.x - j.x)**2) + ((i.y - j.y)**2))
                distance1_b.append(distance)

        for i in  vector1_3.myvertices[-buffer3:]:
            for j in vector2_3.myvertices[:buffer3]:
                distance = math.sqrt(((i.x - j.x)**2) + ((i.y - j.y)**2))
                distance2_b.append(distance)


        min1 = min(distance1)
        min2 = min(distance2)

        minbed = min(distance_bed)

        min1b = min(distance1_b)
        min2b = min(distance2_b)

        ind_bed = distance_bed.index(minbed)
        modulus_bed =  ind_bed % buffer2
        vector2_2.myvertices = vector2_2.myvertices[modulus_bed +1: ]

        if min(distance1) <= min(distance2):
            ind1 =distance1.index(min1)
            modulus =  ind1 % buffer1
            vector2_1.myvertices = vector2_1.myvertices[modulus +1: ]

        elif min(distance1) > min(distance2):
            ind2 = distance2.index(min2)
            modulus = ind2 % buffer1
            vector2_1.myvertices = vector2_1.myvertices[modulus +1: ] #FIXME

        if min(distance1_b) <= min(distance2_b):
            ind =distance1_b.index(min1b)
            modulus =  ind % buffer3
            vector2_3.myvertices = vector2_3.myvertices[modulus +1: ]
            # vector2_3.nbvertices = len(vector2_3.myvertices)

        elif min(distance1_b) > min(distance2_b):
            ind =distance2_b.index(min2b)
            modulus =  ind % buffer3
            vector2_3.myvertices = vector2_3.myvertices[modulus +1: ]
            # vector2_3.nbvertices = len(vector2_3.myvertices)

        return znes1, znes2

    def connect_2vectors(self,
                         zones1: Zones,
                         zones2: Zones,
                         id1:int = 0,
                         id2:int = 0) -> Zones:
        """Connect (link) 2 vectors extremity of 2 successive zones
        containing each 3 vectors (1 vectors and its 2 parallels) and,
        return a new zone with the concatenations.

        :param zones1: First vector
        :type zones1: Zones
        :param zones2: Second
        :type zones2: Zones
        :param id1: Position in .myzones of the zone containing the vectors, defaults to 0
        :type id1: int, optional
        :param id2: Position in .myzones of the zone containing the vectors, defaults to 0
        :type id2: int, optional
        :return: return a new vector which is the concatenation of the 2 first ones.
        :rtype: Zones
        """
        znes1 = zones1
        znes2 = zones2
        zone1 = znes1.myzones[id1]
        zone2 = znes2.myzones[id2]
        if len(zone1.myvectors) == len(zone2.myvectors):
            vector_1 = zone1.myvectors[0]
            vector_bed_1 = zone1.myvectors[1]
            vector_1_2 = zone1.myvectors[2]

            vector2_1 =zone2.myvectors[0]
            vector_bed_2 = zone2.myvectors[1]
            v2_2 =zone2.myvectors[2]

            d1 =math.sqrt(((vector_1.myvertices[-1].x - vector2_1.myvertices[0].x)**2) +
                        ((vector_1.myvertices[-1].y - vector2_1.myvertices[0].y)**2))

            d2 =math.sqrt(((vector_1.myvertices[-1].x - v2_2.myvertices[0].x)**2) +
                        ((vector_1.myvertices[-1].y - v2_2.myvertices[0].y)**2))

            new_zone= Zones()
            zone_vect = zone(name='Concatenated', parent=new_zone)
            new_zone.add_zone(zone_vect)

            vbed = vector(name='bed', parentzone= new_zone.myzones[0])
            vbed.myvertices = vector_bed_1.myvertices + vector_bed_2.myvertices
            # vbed.nbvertices = vector_bed_1.nbvertices + vector_bed_2.nbvertices


            if d1 > d2:
                new_vector1 = vector(name='bank1', parentzone= new_zone.myzones[0])
                new_vector1.myvertices = vector_1.myvertices + v2_2.myvertices
                # new_vector1.nbvertices = vector_1.nbvertices + v2_2.nbvertices
                new_vector1_2 = vector(name='bank2', parentzone= new_zone.myzones[0])
                new_vector1_2.myvertices = vector_1_2.myvertices + vector2_1.myvertices
                # new_vector1_2.nbvertices = vector_1_2.nbvertices + vector2_1.nbvertices

            else:
                new_vector1 = vector(name='bank1', parentzone= new_zone.myzones[0])
                new_vector1.myvertices = vector_1.myvertices + vector2_1.myvertices
                # new_vector1.nbvertices = vector_1.nbvertices + vector2_1.nbvertices
                new_vector1_2 = vector(name='bank2', parentzone= new_zone.myzones[0])
                new_vector1_2.myvertices = vector_1_2.myvertices + v2_2.myvertices
                # new_vector1_2.nbvertices = vector_1_2.nbvertices + v2_2.nbvertices

            zone_vect.add_vector(new_vector1)
            zone_vect.add_vector(vbed)
            zone_vect.add_vector(new_vector1_2)
            new_zone.find_minmax(True)
            return new_zone

    def concatenate_2_zones(self,
                            zones1: Zones,
                            zones2: Zones,
                            id1:int = 0,
                            id2: int = 0,
                            buffer: int = None,
                            save_as:str = None) -> Zones:
        """ Return the concatenation of 2 vectors file (Zones)
        containing each 3 vectors (1 vector and its 2 parallels) after:
            - matching their ends,
            - deleting the overlaps and,
            - connecting the vectors.

        :param zones1: first vector
        :type zones1: Zones
        :param zones2: second vector
        :type zones2: Zones
        :param id1: Position in .myzones of the zone containing the vectors, defaults to 0
        :type id1: int, optional
        :param id2: Position in .myzones of the zone containing the vectors, defaults to 0
        :type id2: int, optional
        :param buffer: While deleting overlaps,
        this is the number of vertices to process on each vector
        starting from the end of the vector
        (None means all vertices are processed),defaults to None, defaults to None

        :type buffer: int, defaults to None
        :param save_as: File path of the new vector, defaults to None
        :type save_as: str, optional
        :return: _description_
        :rtype: the vector containing the concatenation of the 2 first ones.
        """
        znes1a,znes2a = self.match_ends_2vectors(zones1, zones2, id1, id2)
        znes1b,znes2b = self.delete_overlaps_2vectors(znes1a, znes2a, id1, id2, buffer)
        zones = self.connect_2vectors(znes1b,znes2b,id1,id2)
        if save_as:
            zones.saveas(save_as)
        return zones

    def read_zones_paths(self,
                         file_list: list[str]) -> list[Zones]:
        """Return a list of vectors(`Zones`) objects,
        from a list of given file paths of vectors(`Zones`).

        :param file_list: List of file paths of vectors,
        :type file_list: list[str]
        :return: the list of vectors(`Zones`) objects.
        :rtype: list[Zones]
        """
        return [Zones(file) for file in file_list]

    def concatenate_listof_zones(self,
                                 file_list:list[str]= None,
                                 zones_list: list[Zones] = None,
                                 id1:int = 0,
                                 id2: int = 0,
                                 buffer: int = None,
                                 save_as:str = None) -> Zones:
        """Return a zones which is the concatenation of a sorted list of zones containing each
        3 vectors (1 vector and its 2 parallels) after:
            - matching their ends,
            - deleting the overlaps and,
            - connecting the vectors.

        :param file_list: list of given file paths, defaults to None
        :type file_list: list[str], optional
        :param zones_list: vectors(`Zones`) objects, defaults to None
        :type zones_list: list[Zones], optional
        :param id1: Position in .myzones of the zone containing the vectors, defaults to 0
        :type id1: int, optional
        :param id2: Position in .myzones of the zone containing the vectors, defaults to 0
        :type id2: int, optional
        :param buffer: _description_, defaults to None
        :type buffer: While deleting overlaps, this is the number of vertices
        to process on each vector starting from the end of the vector
        (None means all vertices are processed),defaults to None

        :param save_as: _description_, defaults to None
        :type save_as: File path of the new vector, optional
        :raises Exception: With a GUI, to warn the user that the list of zones is missing.
        :raises Exception: Without GUI, to warn the user that the list of zones is missing.
        :return: A vector (Zones) containing the concatenation of all the vectors.
        :rtype: Zones
        """
        if file_list:
            working_list = self.read_zones_paths(file_list)
        elif zones_list:
            working_list = zones_list
        else:
            if  self.wx_exists:
                raise Exception(logging.info(_("The list of Zones is missing.")))
            else:
                raise Exception(_("The list of Zones is missing."))

        concatenated = [working_list[0]]
        for i in range(len(working_list)-1):
            zones = self.concatenate_2_zones(concatenated[i],working_list[i+1],id1, id2)
            concatenated.append(zones)

        new_zones = concatenated[-1]
        if save_as:
            if self.directory_name != '':
                branches_file = self.initialize_file(save_as, "_branches.vec")
            else:
                branches_file = save_as

            new_zones.saveas(branches_file)
            # new_zones.saveas(save_as)
        return new_zones

    def create_Zonesfromzones(self,
                              zone_list: list[zone],
                              save_as: str = '') -> Zones:
        """Return a vector (`Zones`) from a list of zones (`Zone`).

        :param zone_list: list of zones
        :type zone_list: list[zone]
        :param save_as: File path to the vector file, defaults to ''
        :type save_as: str, optional
        :return: The vector (`Zones`) containing the list of zones.
        :rtype: Zones
        """
        znes= Zones()
        znes.myzones = zone_list
        znes.find_minmax()
        if save_as!= '':
            znes.saveas(save_as)
        return znes

    def create_branches(self,
                        zones_group: list[list[Zones]],
                        save_as:str = '') -> Zones:         #FIXME implement unique zone case
        """Create branches(`Zone`) from a list of vectors('Zones').
        FIXME: This method is not used in the current version of the software.
        FIXME: It could be implemented in the future but with a dictionary instead of a list.

        :param zones_group: list of list of vectors per branch
        :type zones_group: list[list[Zones]]
        :param save_as: File path to the folder where the new information is saved, defaults to ''
        :type save_as: str, optional
        :return: Concatenation of all the branches(List of `Zones`)
        :rtype: Zones
        """
        groups = zones_group
        all_zone = []
        k=1
        for group in tqdm(groups):
                concatenation = self.concatenate_listof_zones(zones_list = group)
                concatenation.myzones[0].myname = Titles.BRANCH.value +f'{k}'
                all_zone.append(concatenation.myzones[0])
                k+=1
        branches = self.create_Zonesfromzones(all_zone,save_as)
        branches.find_minmax(True)

        return branches

    def create_branches_from_list_of_zones(self,
                                        zones_list: list[Zones],
                                        id = 1,
                                        save_as:str = '',) -> Zones:
        """Generate branches from a list of vectors (`Zones`).
        The concept here is to loop on all vectors and then to add each zone
        contained in those vectors to a new zone that will be returned.
        FIXME: Remove Id from all methods and delete the parameter from the method signature.

        :param zones_list: List of vectors (`Zones`).
        :type zones_list: list[Zones]
        :param id: Depreciated, defaults to 1
        :type id: int, optional
        :param save_as: File path to the new vector(`Vector`), defaults to ''
        :type save_as: str, optional
        :return: The new vector (`Zones`) containing all zones.
        :rtype: Zones
        """
        new_zones = Zones(is2D=False)
        k=1
        for znes in zones_list:
            for zne in znes.myzones:
                new_zone = zne.deepcopy_zone()
                new_zones.add_zone(new_zone)

        new_zones.find_minmax(True)

        if save_as:
            path = self.initialize_file(save_as,fileExtensions.VECTOR3D.value)
            new_zones.saveas(path)
        return new_zones

    def create_polygons(self, zones: Zones, discretization: float=1, howmanypoly:int=1, save_as: str ='') -> Zones:
        """Return polygons created from parallels and vectors.

        :param zones: The vector ('Zones'),
        :type zones: Zones
        :param discretization: discretization steps between profiles, defaults to 1
        :type discretization: float, optional
        :param howmanypoly: Number of polygons, defaults to 1
        :type howmanypoly: int, optional
        :param save_as: Path to the new vector(`Vector`) file, defaults to ''
        :type save_as: str, optional
        :return: _description_
        :rtype: Zones
        """
        znes= zones.deepcopy_zones()
        for i in tqdm(range(len(zones.myzones)), desc= "Creating polygons:", unit='zone', colour= Colors.TQDM.value):
            # znes.myzones[i].create_polygon_from_parallel(ds = discretization, howmanypoly = 1, fill_structure=False) # FIXME check why this was working previuosly
            znes.myzones[i].create_polygon_from_parallel(ds = discretization, howmanypoly = 1)

        for i in range(len(zones.myzones)):
            znes.myzones.pop(0)

        znes.find_minmax(True)
        if save_as != '':
            poly_file = os.path.join(save_as, 'polygons.vec')
            znes.saveas(poly_file)

        return znes

    def create_branches_sections(self,
                                 zones: Zones,
                                 discretization: float = 1,
                                 save_as = '') -> Zones:
        """ Create sections on model skeleton (river branches)
        and return  a Zones containing
        all sections per zone.

        :param zones: `Zones` containing the vectors
        :type zones: Zones
        :param discretization: Distance between sections, defaults to 1
        :type discretization: float, optional
        :param save_as: File path where the new section are saved as vector, defaults to ''
        :type save_as: str, optional
        :return: `Zones` containing all sections.
        :rtype: Zones
        """
        znes = zones
        all_zone= []
        k = 1

        for zne in tqdm(znes.myzones, desc='Creating sections', colour= Colors.TQDM.value, unit='zone'):
            id = k-1
            new_znes = self.create_river_sections(znes,id,discretization)
            new_zne = new_znes.myzones[0]
            new_zne.myname = Titles.BRANCH.value + f'{k}'
            all_zone.append(new_zne)
            k+=1

        # FIXME add the save option in case the user does not want the file.

        branches = self.create_Zonesfromzones(all_zone,save_as)
        return branches

    def create_river_sections(self,
                              zones: Zones,
                              id:int = 0,
                              discretization: float = 1,
                              save_as: str ='',
                              plot_check = False) -> Zones:
        """From 2 parallels (river banks), a vector (river bed) and a discretization step
        this method generates and returns the corresponding profiles (river sections) as a Zones object.
        @The paralles and vectors shoulb stored in the same Zone and their index should follow this format:
            - 0: Left bank
            - 1: River bed
            - 2: Right bank

        :param zones: `Zones` containing the parallels
        :type zones: Zones
        :param id: index of the object `Zone` containing `vectors`, defaults to 0
        :type id: int, optional
        :param discretization: Distance between sections, defaults to 1
        :type discretization: float, optional
        :param save_as: File path of the new Zones , defaults to ''
        :type save_as: str, optional
        :param plot_check: if the results should be plotted or not, defaults to False
        :type plot_check: bool, optional
        :return: The new Zones containing the profiles (sections).
        :rtype: Zones

        .. todo:: 1) FIXME create a test for this method
        .. todo:: 2) FIXME Think about a faster way to create the profiles
        .. todo:: 3) FIXME Break this method into smaller methods
        """
        # Vectors selection
        znes = zones
        zne = znes.myzones[id]
        bank1 = zne.myvectors[0]
        bed = zne.myvectors[1]
        bank2 = zne.myvectors[2]
        # Shapely Linestring
        lsl = bank1.asshapely_ls()
        lsc = bed.asshapely_ls()
        lsr = bank2.asshapely_ls()
        # Number of points (Discretization)
        nb = int(np.ceil(lsc.length/discretization))
        # Adimensional distances along center vector
        sloc = np.linspace(0.,1.,nb,endpoint=True)
        # Points along center vector
        ptsc = [lsc.interpolate(curs,True) for curs in sloc]
        # Real distances along left, right and center vector
        sl = [lsl.project(curs) for curs in ptsc]
        sr = [lsr.project(curs) for curs in ptsc]
        sc = [lsc.project(curs) for curs in ptsc]
        # Creation of profiles
        name = 'Section - '
        new_znes = Zones()
        vec_zone = zone(name='Trace cross sections', parent=zones)
        new_znes.add_zone(vec_zone)

        # for i in tqdm(range(len(sl)-1), desc='Creation of polygons: ', colour= Colors.TQDM.value):
        for i in range(len(sl)-1):              # FIXME  Check this indexation
            #mean distance along center will be stored as Z value of each vertex
            smean =(sc[i]+sc[i+1])/2.
            curvec1=vector(name='poly'+str(i+1))
            curvec2=vector(name='poly'+str(i+1))
            # Shapely substrings (Length between 2 points)
            sublsl= substring(lsl,sl[i],sl[i+1])
            sublsr= substring(lsr,sr[i],sr[i+1])
            #Test wether the substring result is Point or LineString and then add the substring points as  wolf vertices to a new vector
            if sublsl.geom_type=='Point':
                curvec1.add_vertex(wolfvertex(sublsl.x,sublsl.y,smean))
            elif sublsl.geom_type=='LineString':
                xy=np.asarray(sublsl.coords)
                for a in xy:
                    curvec1.add_vertex(wolfvertex(a[0], a[1], smean))

            if sublsr.geom_type=='Point':
                curvec2.add_vertex(wolfvertex(sublsr.x,sublsr.y,smean))

            elif sublsr.geom_type=='LineString':
                xy=np.asarray(sublsr.coords)
                for a in xy:
                    curvec2.add_vertex(wolfvertex(a[0], a[1], smean))

            new_vector= vector(name= name + '%s'%(i), parentzone=vec_zone)
            vert1 = curvec1.myvertices[0]
            vert2 = curvec2.myvertices[0]
            new_vector.add_vertex(vert1)
            new_vector.add_vertex(vert2)
            vec_zone.add_vector(new_vector)

        new_znes.find_minmax(update=True)
        if plot_check:
            plt.figure('Check profiles',figsize=(20,5))
            for vec in vec_zone.myvectors:
                plt.plot([vec.myvertices[0].x, vec.myvertices[-1].x],[vec.myvertices[0].y,vec.myvertices[-1].y ],color ='blue', lw= 1, ls ='--')
            plt.show()

        if save_as !='':
            new_znes.saveas(save_as)

        return new_znes

    def create_support_from_sections(self, sections: Zones, save_as: str) -> Zones:
        """Create supports from sections (midline).
        The supports are the midpoints of the sections.

        :param sections: `Zones` containing the sections
        :type sections: Zones
        :param save_as: File path of the new Zones, defaults to ''
        :type save_as: str, optional
        :return: The new Zones containing the supports.
        :rtype: Zones

        .. todo:: 1) FIXME create a test for this method
        .. todo:: 2) FIXME Think about a faster way to create the supports
        .. todo:: 3) FIXME could it replace the current method for the cration of bed in wolfpy?
        """
        # Create supports from sections.
        new_zones = Zones()
        id = 1
        for zne in tqdm(sections.myzones, desc = 'Creating vector files:', colour= Colors.TQDM.value):
            # id = 1  # Changing the sections name
            vec_id = 1
            new_zone = zone(name= f'{id}', parent= new_zones)
            new_zones.add_zone(new_zone)
            new_vec = vector(name = f'{vec_id}', parentzone=new_zone)
            new_zone.add_vector(new_vec)
            for vec in zne.myvectors:
                vert1 = vec.myvertices[0]
                vert2 = vec.myvertices[-1]
                mid_vertx = (vert1.x + vert2.x)/2
                mid_verty = (vert1.y + vert2.y)/2
                mid_vert = wolfvertex(mid_vertx, mid_verty)
                new_vec.add_vertex(mid_vert)
            id += 1

        new_zones.find_minmax(update=True)
        if save_as:
            if self.directory_name != '':
                vec_file = self.initialize_file(save_as,'.vec')
            else:
                vec_file = save_as
            new_zones.saveas(vec_file)

        return new_zones

    def save_only_vec(self,
                      zones: Zones,
                      id: int = 1,
                      id_vec:int = 1,
                      save_as: str='',
                      format: str='') -> Zones:
        """Save only one vector from a Zones object.

        :param zones: `Zones` containing the vector
        :type zones: Zones
        :param id: Index of the zone containing the vector, defaults to 1
        :type id: int, optional
        :param id_vec: Index of the vector in the zone, defaults to 1
        :type id_vec: int, optional
        :param save_as: File path of the new vector, defaults to ''
        :type save_as: str, optional
        :param format: Format of the new vector, defaults to ''
        :type format: str, optional
        :return: The new Zones containing the vector.
        :rtype: Zones
        """
        znes = zones
        if format =='vec':
            znes.force3D = False
        kept_zone = znes.myzones[id]
        kept_zone.myname = 'Zone'
        kept_vector = kept_zone.myvectors[id_vec]
        kept_vector.myname = 'trace'
        znes.myzones = []
        kept_zone.myvectors = []
        kept_zone.add_vector(kept_vector)
        znes.add_zone(kept_zone)
        znes.find_minmax(True)
        if save_as != '':
            if format == '' :
                znes.saveas(filename = save_as +'.vec')
                znes.saveas(filename = save_as+'.vecz')

            elif format=='vecz':
                znes.saveas(filename = save_as +'.vecz')

            elif format == 'vec':
                znes.saveas(filename = save_as +'.vec')


            else:
                if self.wx_exists:
                    raise Exception(logging.info('This Vector format is not available.'))
                else:
                    raise Exception('This Vector format is not available.')
        return znes

    def refine_vector_from_2D(self,
                              vect: vector,
                              discretization = 1) -> list:
        """
        Refine a vector based on a given discretization step.
        Returns a python list.

        :param vect: Vector to refine
        :type vect: vector
        :param discretization: Discret
        :type discretization: float
        :return: List of points
        :rtype: list
        """

        myls = vect.asshapely_ls()
        length = myls.length
        nb = int(np.ceil(length/discretization*2))
        alls = np.linspace(0,int(length),nb)
        pts = [myls.interpolate(curs) for curs in alls]
        return pts

    def remove_zone(self,
                    zones: Zones,
                    id: int = 0) -> Zones:
        """Remove a zone from a Zones object.

        :param zones: `Zones` containing the zone to remove
        :type zones: Zones
        :param id: Index of the zone to remove, defaults to 0
        :type id: int, optional
        :return: The new Zones without the removed zone.
        :rtype: Zones
        """
        znes = zones
        znes.myzones.pop(id)
        return znes

    def place_minimum_altitude(self, zones: Zones, filename: str, save_as: str = '') -> Zones:
        """Return a Zones object in which all altitudes below a defined treshold
        for specific vectors (sections specified in a csv file) are raised
        to the new altitudes.

        :param zones: Zones object containing the vectors
        :type zones: Zones
        :param filename: .csv file containing the sections and their minimum altitudes,
        first column is the section name and second column is the minimum altitude.

        :type filename: str
        :param save_as: path to the the file where the modified Zones will be saved
        if no path is given the results is not saved but only returned , defaults to ''

        :type save_as: str, optional
        :return: New Zones object with the modified altitudes
        :rtype: Zones
        """
        # Read the csv file as a pandas dataframe
        # df_sections = self.read_csv_as_dataframe(filename, column_names=['section', 'altitude'])
        df_sections = pd.read_csv(filename, names=['section', 'altitude'])
        df_sections['section'] = df_sections['section'].astype(str)
        # Replace the minimum altitude by comparing the altitude of each vertex to the minimum altitude
        for zne in zones.myzones:
            for vec in tqdm(zne.myvectors, desc='Replacing minimum altitude', colour= Colors.TQDM.value, unit='vector'):
                if vec.myname in df_sections['section'].values:
                    index = df_sections.index[df_sections['section'] == vec.myname][0]
                    test =  df_sections['altitude'][index]
                    for vert in vec.myvertices:
                        if vert.z < test:
                            vert.z = test
                    if self.wx_exists:
                        logging.info(f"Minimum altitude for {vec.myname} is now {test}")
                    else:
                        print(f"Minimum altitude for {vec.myname} is now {test}")
        # Save the new Zones
        zones.find_minmax(update=True)
        if save_as:
            zones.saveas(save_as)
        return zones

    def change_minimum_altitude(self, zones: Zones,filename: str, save_as: str = '') -> Zones:
        """Return a Zones object in which all altitudes below a defined treshold
        for specific vectors (sections specified in a csv file) are raised
        to the new altitudes.

        :param zones: Zones object containing the vectors
        :type zones: Zones
        :param filename: .csv file containing the sections and their minimum altitudes,
        first column is the section name and second column is the minimum altitude.

        :type filename: str
        :param save_as: path to the the file where the modified Zones will be saved
        if no path is given the results is not saved but only returned , defaults to ''

        :type save_as: str, optional
        :return: New Zones object with the modified altitudes
        :rtype: Zones
        """
        # Read the csv file as a pandas dataframe
        # df_sections = self.read_csv_as_dataframe(filename, column_names=['section', 'altitude'])
        df_sections = pd.read_csv(filename, names=['section', 'altitude', 'new_altitude'])
        df_sections['section'] = df_sections['section'].astype(str)
        # Replace the minimum altitude by comparing the altitude of each vertex to the minimum altitude
        for zne in zones.myzones:
            for vec in tqdm(zne.myvectors, desc='Replacing minimum altitude', colour= Colors.TQDM.value, unit='vector'):
                if vec.myname in df_sections['section'].values:
                    index = df_sections.index[df_sections['section'] == vec.myname][0]
                    test =  df_sections['altitude'][index]
                    new_value = df_sections['new_altitude'][index]
                    for vert in vec.myvertices:
                        if vert.z < test:
                            vert.z =new_value
                    if self.wx_exists:
                        logging.info(f"Minimum altitude for {vec.myname} has been changed to {new_value}.")
                    else:
                        print(f"Minimum altitude for {vec.myname} has been changed to {new_value}.")
        # Save the new Zones
        zones.find_minmax(update=True)
        if save_as:
            zones.saveas(save_as)
        return zones

    def __change_minimum_altitude(self, zones: Zones,filename: str, save_as: str = '') -> Zones:
        """Return a Zones object in which all altitudes below a defined treshold
        for specific vectors (sections specified in a csv file) are raised
        to the new altitudes.

        :param zones: Zones object containing the vectors
        :type zones: Zones
        :param filename: .csv file containing the sections and their minimum altitudes,
        first column is the section name and second column is the minimum altitude.

        :type filename: str
        :param save_as: path to the the file where the modified Zones will be saved
        if no path is given the results is not saved but only returned , defaults to ''

        :type save_as: str, optional
        :return: New Zones object with the modified altitudes
        :rtype: Zones
        """
        # Read the csv file as a pandas dataframe
        # df_sections = self.read_csv_as_dataframe(filename, column_names=['section', 'altitude'])
        df_sections = pd.read_csv(filename, names=['section', 'altitude', 'new_altitude'])
        # Replace the minimum altitude by comparing the altitude of each vertex to the minimum altitude
        for zne in zones.myzones:
            for vec in tqdm(zne.myvectors, desc='Replacing minimum altitude', colour= Colors.TQDM.value, unit='vector'):
                if vec.myname in df_sections['section'].values or int(vec.myname) in df_sections['section'].values:

                    try:
                        index = df_sections.index[df_sections['section'] == vec.myname][0]
                    except IndexError:
                        index = df_sections.index[df_sections['section'] == int(vec.myname)][0]

                    test =  df_sections['altitude'][index]
                    new_value = df_sections['new_altitude'][index]
                    for vert in vec.myvertices:
                        if vert.z < test:
                            vert.z =new_value
                    if self.wx_exists:
                        logging.info(f"Minimum altitude for {vec.myname} has been changed to {new_value}.")
                    else:
                        print(f"Minimum altitude for {vec.myname} has been changed to {new_value}.")
        # Save the new Zones
        zones.find_minmax(update=True)
        if save_as:
            zones.saveas(save_as)
        return zones

    def reverse_sense_zones(self, zones: Zones, save_as: str = '') -> Zones:
        """Reverse the sense of the vectors in a Zones object.

        :param zones: Zones object containing the vectors
        :type zones: Zones
        :param save_as: path to the the file where the modified Zones will be saved
        if no path is given the results is not saved but only returned , defaults to ''

        :type save_as: str, optional
        :return: New Zones object with the reversed vectors
        :rtype: Zones
        """
        znes = zones.deepcopy_zones()
        for zne in znes.myzones:
            for vec in zne.myvectors:
                vec.myvertices.reverse()
        znes.find_minmax(update=True)
        if save_as:
            znes.saveas(save_as)
        return znes

    def v_shape_cross_section(self,
                            cross_sections: crosssections,
                            profile_name: str,
                            increment:float = None,
                            zmax:float = None,
                            save_as:str ='') -> crosssections:
        """Create a V shape profile from a given profile in a cross section object
        and return the new cross section object.
        """

        prof = cross_sections.get_profile(profile_name)
        self.v_shape(prof, increment, zmax)
        cross_sections.find_minmax(update=True)

        if save_as:
            cross_sections.saveas(save_as)
        return cross_sections

    def v_shape(self,
                prof: profile,
                increment = None,
                zmax = None) -> profile:
        sz = prof.get_sz()

        # If the max height is not provided.
        if zmax is None:
            zmax = max(sz[1])
        zmin = min(sz[1])
        # Distance between point
        height = zmax - zmin

        #  To check if the number of vertices is odd or even
        modulus = len(sz[0]) % 2

        # Odd case
        if modulus != 0:
            start = round(len(sz[0])/2)
            coords_mid = prof.myvertices[start -1]
            coords_mid.z = zmin
        # Even case
        elif modulus == 0:
            start = int(len(sz[0])/2)
            coords_mid = prof.myvertices[start - 1]
            coords_mid.z = zmin
            coords_mid_1 = prof.myvertices[start]
            coords_mid_1.z = zmin
        # in case the increment is not given,the height is divided equally
        if increment is None:
            number_of_increment = start
            increment = height/number_of_increment

        for i in range(1, start):
            z = zmin + (increment*i)
            vert_1 = prof.myvertices[(start - 1) - i]
            if modulus == 0:
                vert_2 = prof.myvertices[(start ) + i]
            elif modulus != 0:
                vert_2 = prof.myvertices [(start - 1) + i]

            vert_1.z = z
            vert_2.z = z


        prof.find_minmax()

    def transform_to_rectangular_shape(self,
                                       prof: profile,
                                       nb_vertices: int,
                                       zmin: float = None,
                                       zmax: float = None):
        sz = prof.get_sz()
        if zmin is None:
            zmin = min(sz[1])
        if zmax is None:
            zmax = max(sz[1])
        modulus = len(sz[0]) % 2
        if modulus != 0:
            start = round(len(sz[0])/2)
            coords_mid = prof.myvertices[start -1]
            coords_mid.z = zmin

        elif modulus == 0:
            start = int(len(sz[0])/2)
            coords_mid = prof.myvertices[start - 1]
            coords_mid.z = zmin
            coords_mid_1 = prof.myvertices[start]
            coords_mid_1.z = zmin

        for i in range(1,start):
            vert_1 = prof.myvertices[(start - 1) - i]
            if modulus == 0:
                vert_2 = prof.myvertices[(start ) + i]
            elif modulus != 0:
                vert_2 = prof.myvertices [(start - 1) + i]
            if i < nb_vertices:
                vert_1.z = zmin
                vert_2.z = zmin
            else:
                vert_1.z = zmax
                vert_2.z = zmax

        prof.find_minmax()

    def rectangular_shape_cross_section(self,
                                        cross_sections: crosssections,
                                        profile_name: str,
                                        nb_vertices: int,
                                        zmin: float = None,
                                        zmax: float = None,
                                        save_as: str = '') -> crosssections:
        """Create a rectangular shape profile from a given profile in a cross section object
        and return the new cross section object.
        """
        prof = cross_sections.get_profile(profile_name)
        self.transform_to_rectangular_shape(prof, nb_vertices, zmin, zmax)
        cross_sections.find_minmax(update=True)
        if save_as:
            cross_sections.saveas(save_as)
        return cross_sections

    def v_shape_vector(self,
                prof: vector,
                increment = None,
                zmax = None) -> vector:
        sz = prof.get_sz()
        if zmax is None:
            zmax = max(sz[1])
        zmin = min(sz[1])
        # Distance between point
        height = zmax - zmin
        #  To check if the number of vertices is odd or even
        modulus = len(sz[0]) % 2

        # Odd case
        if modulus != 0:
            start = round(len(sz[0])/2)
            sz[1][start] = zmin
        # Even case
        elif modulus == 0:
            start = int(len(sz[0])/2)
            sz[1][start] = zmin
            sz[1][start+1] = zmin

        # in case the increment is not given,the height is divided equally
        if increment is None:
            number_of_increment = len(range(start))
            increment = height/number_of_increment

    def _v_shape(self,
                prof: profile,
                increment = None,
                zmax = None) -> profile:
        sz = prof.get_sz()
        # If the max height is not provided.
        if zmax is None:
            zmax = max(sz[1])
        zmin = min(sz[1])
        # Distance between point
        height = zmax - zmin
        # Reshaping the profile
        origin = prof.get_xy_from_s(sz[0][0])
        end = prof.get_xy_from_s(sz[0][-1])
        sz[1] = 0
        trace = [[origin.x, origin.y], [end.x, end.y]]
        prof.set_sz(np.array([sz[0], sz[1]]), trace)
        #  To check if the number of vertices is odd or even
        modulus = len(sz[0]) % 2
        # Odd case
        if modulus != 0:
            start = round(len(sz[0])/2)
            sz[1][start] = zmin
        # Even case
        else:
            start = int(len(sz[0])/2)
            sz[1][start] = zmin
            sz[1][start+1] = zmin

        # in case the increment is not given,the height is divided equally
        if increment is None:
            number_of_increment = len(range(start))
            increment = height/number_of_increment

        for i in range(start):
            sz[1][i] = zmax - increment*i
            sz[1][-i] = sz[1][i]
        origin = prof.get_xy_from_s(sz[0][0])
        end = prof.get_xy_from_s(sz[0][-1])
        # origin = prof.myvertices[0]
        # end = prof.myvertices[-1]
        trace = [[origin.x, origin.y], [end.x, end.y]]
        prof.set_sz(np.array([sz[0], sz[1]]), trace)



    # --- Vectors - plotting methods ---
    #____________________________________

    def plot_zones(self,
                   zones_list: list[Zones],
                   id: int = 0) -> None:
        """Plot the `vector` objecs in a list of `Zones`
        on a matplotlib figure.

        :param zones_list: List of vector files (`Zones`)
        :type zones_list: list[Zones]
        :param id: Index of the zone containing the vector object
        in all `Zones`, defaults to 0

        :type id: int, optional

        .. todo:: 1) FIXME Add detailed information (legends, title, an so on) to the plot.
        .. todo:: 2) FIXME Think about a test for this method. could it be used in GUI?
        """
        zone_list = [i.myzones[id] for i in zones_list]

        for j in zone_list:
            x1 = [i.x for i in j.myvectors[0].myvertices]
            y1 = [i.y for i in j.myvectors[0].myvertices]
            x2 = [i.x for i in j.myvectors[1].myvertices]
            y2 = [i.y for i in j.myvectors[1].myvertices]
            x3 = [i.x for i in j.myvectors[2].myvertices]
            y3 = [i.y for i in j.myvectors[2].myvertices]
            plt.plot(x1, y1, color = Colors.LEFT_BANK, lw =Constants.BANK_WIDTH, label =_('Left bank'))
            plt.plot(x2, y2, color = Colors.BED, lw =Constants.BANK_WIDTH, label =_('Bed'))
            plt.plot(x3, y3, color = Colors.RIGHT_BANK, lw =Constants.BANK_WIDTH, label =_('Right bank'))
        plt.grid()
        plt.show()
        plt.close()

    def plot_separated_zones(self,
                             zones_list: list[Zones],
                             id: int = 0) -> None:
        """Plot each `vector`object ina list of `Zones`
        on a specific graph of a matplotlib figure.

        :param zones_list: _description_
        :type zones_list: list[Zones]
        :param id: _description_, defaults to 0
        :type id: int, optional

        .. todo:: 1) FIXME Add detailed information (legends, title, an so on) to the plot.
        .. todo:: 2) FIXME Think about a test for this method. could it be used in GUI?
        """

        # Plot the zones vector on separeted matplotlib figure.

        zone_list = [i.myzones[id] for i in zones_list]

        fig, axs = plt.subplots(len(zone_list))

        for j in zone_list:
            x1 = [i.x for i in j.myvectors[0].myvertices]
            y1 = [i.y for i in j.myvectors[0].myvertices]
            x2 = [i.x for i in j.myvectors[1].myvertices]
            y2 = [i.y for i in j.myvectors[1].myvertices]
            x3 = [i.x for i in j.myvectors[2].myvertices]
            y3 = [i.y for i in j.myvectors[2].myvertices]
            n = zone_list.index(j)
            axs[n].plot(x1, y1, color = Colors.LEFT_BANK, lw =Constants.BANK_WIDTH, label =_('Left bank'))
            axs[n].plot(x2, y2, color = Colors.BED, lw =Constants.BANK_WIDTH, label =_('Bed'))
            axs[n].plot(x3, y3, color = Colors.RIGHT_BANK, lw =Constants.BANK_WIDTH, label =_('Right bank'))
            axs[n].legend(fontsize= 'xx-small', loc='upper right')
            axs[n].grid()

        plt.grid()
        plt.show()
        plt.close()

    def plot_parallels_width(self,
                             zones: Zones,
                             id:int = 0,
                             discretization: float = 1,
                             Figure_title:str='Width between vectors',
                             ticks_spacing: int = 1000,
                             fig_width = 30,
                             fig_height = 10,
                             color = 'red',
                             linewidth = 2,
                             x_unit = '$m$',
                             y_unit = '$m$') -> None:
        """Plot the distance between 2 parallels (for instance river width)
        as a function of their mid-vector length.
            - Id : zone index
            - The discretization step is chosen by the user.

        .. note:: The procedure is the following:
                - From the 3 vectors of the zone, the center vector is discretized based on the discretization step provided by the user (1 length unit by default).
                - The number of points is calculated as the length of the center vector divided by the discretization step.
                - The number of points selected is the smallest integer greater than the division result.
                - The newpoints  are then projected on the left and right vectors.
                - The distance between the left and right vectors is then calculated, and plotted as a function of the distance along the center vector, after a postprocessing check using subtrings and vectors.

        :param zones: `Zones` object containing the vectors,
        :type zones: Zones
        :param id: Zones in which the vectors are stored, defaults to 0
        :type id: int, optional
        :param discretization: After how many unit a disctance should be sampled, defaults to 1
        :type discretization: float, optional
        :param Figure_title: Title to be displayed on the figure, defaults to ''
        :type Figure_title: str, optional
        :param ticks_spacing: Discretization of the x axis, defaults to 1000
        :type ticks_spacing: int, optional

        .. note:: FIXME Should be an option in GUI and check whether the substring step is necessary.

        .. todo:: 1) FIXME Add detailed information (legends, title, an so on) to the plot.
        .. todo:: 2) FIXME Think about a test for this method. could it be used in GUI?
        """

        znes = zones
        zne = znes.myzones[id]
        # Vectors
        vec1 = zne.myvectors[0]
        vec2 = zne.myvectors[1]
        vec3 = zne.myvectors[2]
        #  Vectors as shapely Linestrings
        lsl = vec1.asshapely_ls()
        lsc = vec2.asshapely_ls()
        lsr = vec3.asshapely_ls()
        lss= [lsl,lsc,lsr] # FIXME

        # Visual idea of the river as linestrings
        # lsl _________________________

        # lsc -------------------------

        # lsr _________________________

        #Number of points
        nb = int(np.ceil(lsc.length/discretization))
        #Adimensional distances along center vector
        sloc = np.linspace(0.,1.,nb,endpoint=True)

        # Visual idea of the adimendsional riverbed rediscretized with equidistant points
        # 0|-----|-----|-----|-----|1

        #Points along center vector
        ptsc = [lsc.interpolate(curs,True) for curs in sloc]

        # Visual idea of the riverbed rediscretized with equidistant points
        # lsc0|-----|-----|-----|-----|lscf

        #Real distances along left, right and center vector
        sl = [lsl.project(curs) for curs in ptsc]
        sr = [lsr.project(curs) for curs in ptsc]
        sc = [lsc.project(curs) for curs in ptsc]

        # Visual idea of the river rediscretized with equidistant points (projection of those points on banks)

        # lsl0|_____|_____|_____|_____|lslf

        # lsc0|-----|-----|-----|-----|lscf

        # lsr0|_____|_____|_____|_____|lsrf

        # Zones of polygones
        zonepoly1 = zone(name='polygons_1')
        zonepoly2 = zone(name='polygons_2')
        left = []
        right = []
        # For consistency reasons, the distance between 2 successive points is converted
        # to substring and then each point of the substring is stored as a vertex.
        # The operation is done at both banks at the same time,
        # therefore, each vertex has it corresponding point on the other bank.
        # The point are then stored in 2 vectors from which the distance is computed since the number of vertex is the same.

        for i in range(len(sl)-1):
            #mean distance along center will be stored as Z value of each vertex
            smean =(sc[i]+sc[i+1])/2.

            curvec1=vector(name='poly'+str(i+1),parentzone=zonepoly1)
            curvec2=vector(name='poly'+str(i+1),parentzone=zonepoly2)

            sublsl= substring(lsl,sl[i],sl[i+1])
            sublsr= substring(lsr,sr[i],sr[i+1])

        #Test if the substring result is Point or LineString
            if sublsl.geom_type=='Point':
                curvec1.add_vertex(wolfvertex(sublsl.x,sublsl.y,smean))
            elif sublsl.geom_type=='LineString':
                xy=np.asarray(sublsl.coords)
                for a in xy:
                    curvec1.add_vertex(wolfvertex(a[0], a[1], smean))



            if sublsr.geom_type=='Point':
                curvec2.add_vertex(wolfvertex(sublsr.x,sublsr.y,smean))
            elif sublsr.geom_type=='LineString':
                xy=np.asarray(sublsr.coords)
                for a in xy:
                    curvec2.add_vertex(wolfvertex(a[0], a[1], smean))
            left.append(curvec1)
            right.append(curvec2)

            zonepoly1.add_vector(curvec1)
            zonepoly2.add_vector(curvec2)

        #force to update minmax in the zone --> mandatory to plot
        zonepoly1.find_minmax(True)
        zonepoly2.find_minmax(True)

        x01 = zonepoly1.myvectors[0].myvertices[0].x
        y01 = zonepoly1.myvectors[0].myvertices[0].y
        x02 = zonepoly2.myvectors[0].myvertices[0].x
        y02 = zonepoly2.myvectors[0].myvertices[0].y
        d0 = math.sqrt(((x02-x01)**2)  + ((y02-y01)**2))
        width = [d0]
        for i in range(len(zonepoly1.myvectors)):
                x1 = zonepoly1.myvectors[i].myvertices[-1].x
                y1 = zonepoly1.myvectors[i].myvertices[-1].y
                x2 = zonepoly2.myvectors[i].myvertices[-1].x
                y2 = zonepoly2.myvectors[i].myvertices[-1].y
                d = math.sqrt(((x2-x1)**2)  + ((y2-y1)**2))
                width.append(d)

        fig, ax = plt.subplots()
        fig.set_size_inches(fig_width, fig_height)
        ax.plot(sc, width, color=color, lw=linewidth, label='Width')

        ax.set_ylim(min(width)-0.5, max(width)+0.5)
        ax.set_xlim(0,max(sc))
        ax.set_ylabel(f'Width [{y_unit}]', fontsize='large' )
        ax.set_xlabel(f'Length [{x_unit}]', fontsize='large')
        ax.xaxis.set_major_locator(MultipleLocator(ticks_spacing))
        ax.xaxis.set_major_formatter('{x:.0f}')
        ax.xaxis.set_minor_locator(MultipleLocator(ticks_spacing/5))
        ax.grid()
        plt.suptitle('%s'%(Figure_title), fontsize= 'x-large', fontweight= 'bold')
        plt.show()
        plt.close()

    # --- Arrays (Wolf Arrays) ---
    #_____________________________
    # FIXME : This part of the code should be moved to wolfarray.py
    # FIXME : The methods should be refactored and tested.

    def refine_array_by_2(self, array: WolfArray) -> WolfArray:
        """
        Return a remeshed WolfArray in which
        the cells size is divided by 2.
        :param array: WolfArray to refine
        :type array: WolfArray
        :return: Remeshed WolfArray
        :rtype: WolfArray
        """
        wolfarray = array
        curarray = array.array
        shp = curarray.shape
        shp0 = shp[0]*2
        shp1 = shp[1]*2
        index = np.zeros((shp0,), dtype = int)
        index2 = np.zeros((shp1,), dtype = int)
        for i in range(0,shp0,2):
            val1 = int(i/2)
            index[i] = val1
            index[i+1] = val1

        for i in range(0,shp1,2):
            val2 = int(i/2)
            index2[i] = val2
            index2[i+1] = val2

        buffer = curarray[index]

        final: np.ndarray
        final = buffer[:, index2]
        wolfarray.array= final
        wolfarray.nbx = final.shape[0]
        wolfarray.nby = final.shape[1]
        wolfarray.dx = array.dx/2
        wolfarray.dy = array.dy/2
        return wolfarray

    def refine_array(self,array: WolfArray, discretize: int=2) -> WolfArray:
        """
        Refine (divide) the cell size of a Wolfarray
        and return the new array.
        - @ The logarithm of discretize in base 2  must be an integer.

        :param array: WolfArray to refine
        :type array: WolfArray
        :param discretize: Discretization step, defaults to 2
        :type discretize: int, optional
        :return: New WolfArray
        :rtype: WolfArray
        """
        curarray = array

        if discretize == 2:
            final = self.refine_array_by_2(curarray)
        elif discretize > 2:
            nb = int(math.log(discretize,2))
            for i in range(nb):
                final = self.refine_array_by_2(curarray)

        else:
            final = curarray
            if self.wx_exists:
                raise Exception(logging.info("Couldn't refine the WolfArray due to the discretization"))
            else:
                raise Exception("Couldn't refine the WolfArray due to the discretization")

        return final

    def concatenate_2_wolfarrays(self,
                                 array1: WolfArray,
                                 array2: WolfArray) -> WolfArray:
        """
        Return the concatenation of 2 WolfArrays.

        :param array1: First WolfArray
        :type array1: WolfArray
        :param array2: Second WolfArray
        :type array2: WolfArray
        :return: Concatenated WolfArray
        :rtype: WolfArray
        """
        xbounds, ybounds = array1.find_union(array2)
        x = int(round(xbounds[1] - xbounds[0]))
        y = int(round(ybounds[1] - ybounds[0]))

        if array1.dx == array2.dx:
            dx = array1.dx
            nbx = int(round(x/dx))

        else:
            if array1.dx > array2.dx:
                ds = (array1.dx/array2.dx)
                array1 = self.refine_array(array1,ds)
                dx = array1.dx
                nbx = int(round(x/dx))
            else:
                ds =(array2.dx/array1.dx)
                array2 = self.refine_array(array2,ds)
                dx = array2.dx
                nbx = int(round(x/dx))


        if array1.dy == array2.dy :
            dy = array1.dy
            nby = int(round(y/dy))
        else:
            array1.dy= array2.dy = dx
            # Added
            # ----------------
            dy = dx
            nby = int(round(y/dy))

        if array1.dz == array2.dz:
            dz= array1.dz
        else:
            array1.dz= array2.dz = dx

        new_array = WolfArray()
        new_array.origx = min(array1.origx, array2.origx)
        new_array.origy = min(array1.origy, array2.origy)

        new_array.origx = 0
        new_array.origy = 0

        new_array.translx = xbounds[0]
        new_array.transly  = ybounds[0]

        new_array.dx = dx
        new_array.dy = dy
        new_array.dz = dz
        #FIXME probabbly deleted from wolfarray methods
        # new_array.nb_blocks = 1
        # new_array.nb_blocks = array1.nb_blocks
        new_array.head_blocks= array1.head_blocks.copy()
        new_array.nbx = nbx
        new_array.nby = nby

        new_array.array = np.ma.MaskedArray(np.zeros((nbx,nby), order = 'F', dtype = np.float32)) # FIXME find a  way to fill the new arrays

        origx_glob = new_array.origx + new_array.translx
        origy_glob = new_array.origy + new_array.transly

        origx1_glob = array1.translx + array1.origx
        origy1_glob = array1.transly + array1.origy
        origx2_glob = array2.translx + array2.origx
        origy2_glob = array2.transly + array2.origy

        a1x = int(round((origx1_glob - origx_glob)/array1.dx))
        a1y = int(round((origy1_glob - origy_glob)/array1.dx))
        a2x = int(round((origx2_glob - origx_glob)/array2.dx))
        a2y = int(round((origy2_glob - origy_glob)/array2.dx))
        lim_a1x = a1x + array1.nbx
        lim_a1y = a1y + array1.nby
        lim_a2x = a2x + array2.nbx
        lim_a2y = a2y + array2.nby


        array1.mask_reset()

        new_array.array[a2x: lim_a2x, a2y : lim_a2y][array2.array > 0]=  array2.array[array2.array > 0]
        new_array.array[a1x: lim_a1x, a1y: lim_a1y][array1.array >0 ] =  array1.array[array1.array > 0 ]
        new_array.mask_data(new_array.nullvalue)

        return new_array

    def merge_wolfarrays(self,
                         arrays:list[WolfArray],
                         save_as:str='') -> WolfArray:
        """"
        Return a wolfArray which is the concatenation of the given list of WolfArrays.

        :param arrays: List of WolfArrays
        :type arrays: list[WolfArray]
        :param save_as: File path of the new WolfArray, defaults to ''
        :type save_as: str, optional
        :return: Concatenated WolfArray
        :rtype: WolfArray
        """
        concatenation = [arrays[0]]

        for i in tqdm(range(len(arrays)-1),desc='Merging WolfArrays', unit='WolfArray', colour=Colors.TQDM.value):
            new_array = self.concatenate_2_wolfarrays(concatenation[-1],arrays[i+1])
            concatenation.append(new_array)
            concatenation.pop(0)

        if save_as!='':
            concatenation[-1].write_all(save_as)
        return concatenation[-1]

    def new_array_from_vrt(self,
                           array: WolfArray,
                           vrt_file: str,
                           file_out: str = '',
                           wolfarray_not_tif = True,
                           save: bool = True) -> WolfArray:
        """
        Return a new WolfArray extracted from a VRT file.
         - The new array is extracted based on the bounds of the given WolfArray.
         - the new array is either saved on `.tif` or bin `.format`.

        :param array: WolfArray from which the bounds are copied (mask)
        :type array: WolfArray
        :param vrt_file: file path to the VRT file from which the new array is extracted
        :type vrt_file: str
        :param file_out: File path of the new WolfArray, file_out is provided ('' by default)
        a folder of the mask (given array) is used  to store the output under the same name
        as the previous but with a prefix `new_` added, defaults to ''

        :type file_out: str, optional
        :param load: If the new WolfArray should be loaded or not, defaults to True
        :type load: bool, optional
        :param wolfarray_not_tif: If the new WolfArray should be saved as a `.bin` file or `.tif` file, defaults to True
        :type wolfarray_not_tif: bool, optional
        :return: New WolfArray
        :rtype: WolfArray
         """
        # Get the bounds of the array
        bounds = array.get_bounds()

        # If the file_out is not provided, the new array is saved in the same folder as the previous one
        # Changing names
        if file_out == '':
            splitted_path = os.path.split(array.filename)
            new_name = f"new_{os.path.splitext(os.path.basename(array.filename))[0]}.tif"
            file_out = os.path.join(splitted_path[0], new_name)

        # Croping the array extent from the VRT file
        crop_vrt(fn = vrt_file, crop = bounds, fout = file_out)
        # Reading the cropped array
        new_array = WolfArray(file_out)
        # if the new_array should be saved or only returned
        if save:
            # if the new array should be saved as a `.bin` file
            # We create the new name, save the `.bin` array and remove the `.tif` of.
            if wolfarray_not_tif:
                wolf_array_name = f"{os.path.splitext(os.path.basename(array.filename))[0]}.bin"
                array_folder =os.path.split(new_array.filename)[0]
                new_file = os.path.join(array_folder, wolf_array_name)
                new_array.write_all(new_file)
                os.remove(file_out)
                return WolfArray(new_file)
            else:
                return new_array
        else:
            os.remove(file_out)
            return new_array

    def get_arrays_from_vrt(self,
                            arrays:list[WolfArray],
                            vrt_file: str,
                            wolfarray_not_tif = True,
                            save = True) -> list[WolfArray]:
        """
        Return a list of WolfArrays extracted from a VRT file.
        - The new arrays are extracted based on the bounds of the given WolfArrays.
        - The new arrays are either saved on `.tif` or bin `.format`.

        ! The new arrays are saved in the same folder as the previous one.

        :param arrays: List of WolfArrays from which the bounds are copied (masks)
        :type arrays: list[WolfArray]
        :param vrt_file: file path to the VRT file from which the new arrays are extracted
        :type vrt_file: str
        :param wolfarray_not_tif: If the new WolfArrays should be saved as a `.bin` file or `.tif` file,
        defaults to True

        :type wolfarray_not_tif: bool, optional
        :return: List of new WolfArrays
        :rtype: list[WolfArray]
        """
        new_arrays = []
        try:
            for array in tqdm(arrays):
                # new_array = self.new_array_from_vrt(array= array,
                #                                     vrt_file=vrt_file,
                #                                     wolfarray_not_tif=wolfarray_not_tif)
                # new_arrays.append(new_array.filename)
                new_arrays.append(self.new_array_from_vrt(array= array,
                                                        vrt_file=vrt_file,
                                                        wolfarray_not_tif=wolfarray_not_tif,
                                                        save= save))
            return new_arrays
        except:
            if self.wx_exists:
                raise Exception(logging.info('An error occured while extracting the WolfArrays from the VRT file.'))
            else:
                raise Exception('An error occured while extracting the WolfArrays from the VRT file.')



    # # --- Vector + Arrays Get values from array (Vector + Arrays) ---
    #__________________________________________________________________

    def get_values_from_array(self,
                              zones: Zones,
                              array: WolfArray,
                              save_as:str,
                              filter_null = False,
                              selection = True,
                              tif = False) -> Zones:
        """
        Get the values from an array based on a given Zones (vectors),
        - In each zone, the vector are first refined based on the array cells size.
        - a new Zones with its vectors value filled is returned.

        :param zones: `Zones` containing the vectors
        :type zones: Zones
        :param array: `WolfArray` containing the values
        :type array: WolfArray
        :param save_as: File path of the new Zones, defaults to ''
        :type save_as: str, optional
        :param filter_null: If the null values should be filtered or not, defaults to False
        :type filter_null: bool, optional
        :param selection: If the values should be selected or not, defaults to True
        :type selection: bool, optional
        :param tif: If the array is a tif file or not, defaults to False
        :type tif: bool, optional
        :return: The new Zones with its vectors value filled.
        :rtype: Zones
        """
        znes = zones
        new_znes = Zones(is2D=False)
        if tif:
            ds = 1
        else:
            ds = min(array.dx, array.dy)
        for zne in tqdm(znes.myzones, desc=_('Getting values from array:'), unit= 'Zone', colour=Colors.TQDM.value):
            prof_zone = zone( name=zne.myname, parent=new_znes)
            new_znes.add_zone(prof_zone)
            k=1
            for vec in zne.myvectors:
                prof =  vector(name ='%s'%(k), parentzone = prof_zone, is2D = False)
                prof_zone.add_vector(prof)
                pts = self.refine_vector_from_2D(vec,ds)

                # Getting values
                values = [array.get_value(curpt.x, curpt.y, nullvalue = Constants.NULL.value) for curpt in pts]

                # Assigning values to the  corresponding vertex
                if filter_null:
                    for curpt, curvalue in zip(pts,values):
                        if curvalue != Constants.NULL.value:
                            prof.add_vertex(wolfvertex(curpt.x, curpt.y, curvalue))
                else:
                    for curpt, curvalue in zip(pts,values):
                        prof.add_vertex(wolfvertex(curpt.x, curpt.y, curvalue))
                k+=1

        new_znes.find_minmax(update=True)
        if save_as !='':
            new_znes.saveas(save_as)
        return new_znes

    def update_z_value(self, znes: Zones, array: WolfArray, save_as: str) -> Zones:
        """
        Update the z value of the vertices in a Zones object
        based on the values of a WolfArray.

        :param znes: `Zones` containing the vectors
        :type znes: Zones
        :param array: `WolfArray` containing the values
        :type array: WolfArray
        :param save_as: File path of the new Zones, defaults to ''
        :type save_as: str, optional
        :return: The new Zones with updated z values.
        :rtype: Zones
        """
        new_zones = znes.deepcopy_zones()
        id = 1
        for zne in tqdm (new_zones.myzones, desc='Writing the .vecz file:', colour= Colors.TQDM.value):
            zne.myname = f'{id}'
            vec_id = 1
            for vec in zne.myvectors:
                vec.myname = f'{vec_id}'
                for vert in vec.myvertices:
                    vert.z= array.get_value(vert.x, vert.y)
                vec_id += 1
            id += 1

        new_zones.find_minmax(update=True)

        if save_as:
            vecz_file = self.initialize_file(save_as,'.vecz')
            new_zones.saveas(vecz_file)

    def wolfarray_from_xyz(self,
                           xyz_directory: str,
                           coordinate_origin: tuple,
                           coordinate_extent: tuple,
                            dx: float= 1,
                            dy: float= 1,
                           save_as: str = '',
                           nullvalue: float = -99999.,
                           mask_nullvalue = True) -> WolfArray:
        """
        return a WolfArray from a .XYZ file.

        .. notes:: After scanning the directory and concatenating all the the xyz  files into one file,
        a wolfarry with the given extent is created. All  values are first set  to -99999.
        Then, the array is filled with the values from the xyz file and mask is placed wherever values are not available.

        :param wyz_directory: computer path to the folder containing the .XYZ files
        :type wyz_directory: str
        :param coordinate_origin: Origin of the WolfArray. (x,y) of the lower left corner.
        :type coordinate_origin: tuple
        :param coordinate_extent: Extent of the WolfArray. (x,y) of the upper right corner.
        :type coordinate_extent: tuple
        :param dx: Cell size in x direction, defaults to 1
        :type dx: float, optional
        :param dy: Cell size in y direction, defaults to 1
        :type dy: float, optional
        :param save_as: computer path of the file where new WolfArray will be stored, defaults to ''
        :type save_as: str, optional
        :return: WolfArray

        """

        header = self.create_header_wolf_array(dx = dx,
                                               dy = dy,
                                               originx = coordinate_origin[0],
                                               originy = coordinate_origin[1],
                                               extentx = coordinate_extent[0],
                                               extenty = coordinate_extent[1]
                                               )

        cropini = [[float(coordinate_origin[0]), float(coordinate_extent[0])],
                                   [float(coordinate_origin[1]), float(coordinate_extent[1])]]



        file_xyz = xyz_scandir(xyz_directory, cropini)

        new_array = WolfArray()
        new_array.init_from_header(header)
        new_array.nullvalue = nullvalue
        new_array.array.data[:,:] = nullvalue
        new_array.fillin_from_xyz(file_xyz)
        if mask_nullvalue:
            new_array.mask_data(new_array.nullvalue)
        if save_as:
            new_array.write_all(save_as)
        return new_array

    def create_header_wolf_array(self,
                    dx: float,
                    dy: float,
                    originx: float,
                    originy: float,
                    extentx:float = None,
                    extenty:float = None,
                    nbx: int = None,
                    nby: int = None) -> header_wolf:
        """ Fill and return a header of a wolf_2D array (header_wolf object).

        :param dx: Cell size in x direction
        :type dx: float
        :param dy: Cell size in y direction
        :type dy: float
        :param originx: x coordinate of the origin of the WolfArray (lower left corner).
        :type originx: float
        :param originy: y coordinate of the origin of the WolfArray (lower left corner).
        :type originy: float
        :param extentx: x coordinate of the upper right corner, defaults to None
        :type extentx: float, optional
        :param extenty: y coordinate of the upper right corner, defaults to None
        :type extenty: float, optional
        :param nbx: Number of cells in x direction, defaults to None
        :type nbx: int, optional
        :param nby: Number of cells in y direction, defaults to None
        :type nby: int, optional
        :return: Header of the WolfArray
        :rtype: header_wolf
        """
        assert isinstance(originx, (float, int)), 'originx should be a float'
        assert isinstance(originy,( float,int)), 'originy should be a float'
        assert isinstance(dx, (float,int)), 'dx should be a float'
        assert isinstance(dy, (float,int)), 'dy should be a float'

        if extentx is not None and extenty is not None:
            assert isinstance(extentx, (float,int)), 'extentx should be a float'
            assert isinstance(extenty, (float,int)), 'extenty should be a float'
            nbx = int((extentx- originx)/dx)
            nby = int((extenty- originy)/dy)

        if nbx is not None and nby is not None:
            assert isinstance(nbx, int), 'nbx should be an integer'
            assert isinstance(nby, int), 'nby should be an integer'
            nbx = nbx
            nby = nby

        myhead = header_wolf()
        myhead.origx = originx
        myhead.origy = originy
        myhead.dx = dx
        myhead.dy = dy
        myhead.nbx = nbx
        myhead.nby = nby

        return myhead


    # --- Cross sections ---
    #_______________________
    # FIXME: Reread the comments and refactor the methods.

    def save_as_1D_crossections(self,
                                zones: Zones,
                                format ='vecz',
                                save_as: str='',
                                return_list = True) -> list[crosssections]: # FIXME list of cross sections
        r"""
        Save each `Zone` in `Zones` as a cross sections file and,
        return a list of cross sections.

        /!\ The `Zones` should contain the river sections to be transformed into cross sections.

        :param zones: `Zones` containing the vectors
        :type zones: Zones
        :param format: Format of the new cross sections file, defaults to 'zones'
        :type format: str, optional
        :param save_as: File path where the new cross sections are saved, defaults to ''
        :type save_as: str, optional
        :param return_list: If the method should return a list of cross sections or not, defaults to True
        :type return_list: bool, optional
        :return: List of cross sections
        :rtype: list[crosssections]
        """
        mycs = []
        k=1
        for zne in zones.myzones:
            new_zone = Zones()
            new_zone.add_zone(zne)
            new_zone.find_minmax()
            cross = crosssections(new_zone, format=format)
            mycs.append(cross)
            if save_as:
                directory_name= 'Profiles'
                directory = self.create_directory(save_as, directory_name)
                file_name =f'Crossection_{k}.vecz'
                directory = os.path.join(save_as,directory_name)
                path = os.path.join(directory,file_name)
                cross.saveas(path)
            k+=1
        if return_list:
            return mycs
        else:
            return cross

    def create_profiles(self,
                        zones:Zones,
                        topo:WolfArray,
                        discretization:int = 1,
                        save_as:str ='',
                        tif = False) -> Zones:
        """
        Create profiles from river sections and topography.
        - The method creates the river sections from the `Zones` and discretization step.
        - It then creates the supports (midline vectors) from the sections.
        - It updates the z value of the supports based on the topography.
        - The method returns the profiles as a `Zones`.
        - The profiles are saved as a .vecz file.
        - The method also returns the profiles as a list of cross sections.

        :param zones: `Zones` containing the vectors
        :type zones: Zones
        :param topo: `WolfArray` containing the topography
        :type topo: WolfArray
        :param discretization: Distance between sections, defaults to 1
        :type discretization: int, optional
        :param save_as: File path of the new Zones, defaults to ''
        :type save_as: str, optional
        :param tif: If the array is a tif file or not, defaults to False
        :type tif: bool, optional
        :return: The profiles as a Zones
        :rtype: Zones
        """
        "Create profiles from river sections and topography."
        file_name = 'Profiles_vector.vecz'
        file_path = os.path.join(save_as, file_name)
        sections = self.create_branches_sections(zones, discretization)
        support = self.create_support_from_sections(sections, save_as)
        support_vecz = self.update_z_value(support, topo, save_as)          # FIXME check the return value and where it's saved.
        profiles = self.get_values_from_array(sections, topo, file_path, tif=tif)
        return profiles

    def sort_crossections_list(self,
                               crosses:list[crosssections],
                               zones:Zones,
                               vector_id: int = 1) -> list[list[profile]]:
        """
        This methods sort cross sections.
        - The method returns a list of list of profiles.
        - The profiles are sorted based on the given vectors in the `Zones`.

        :param crosses: List of cross sections
        :type crosses: list[crosssections]
        :param zones: `Zones` containing the vectors
        :type zones: Zones
        :param vector_id: Index of the vector in the zone, defaults to 1
        :type vector_id: int, optional
        :return: List of list of profiles
        :rtype: list[list[profile]]
        """
        sorted_cs: list
        prof: profile
        # List of all crossections per zones
        mycs = crosses
        # The list receiving the sorted profiles per zones.
        new_cs = []
        # Iteration on the cross sections to sort the profiles per zones.
        for i in tqdm(range(len(mycs)), desc='Sorting cross sections:', unit='zone', colour=Colors.TQDM.value):
            # selection of the corresponding zone in the support Zones.
            zne = zones.myzones[i]
            # selection of the support vector in the Zone
            vec = zne.myvectors[vector_id]
            # Transformation into a shapely vector (linestring)
            support = vec.asshapely_ls()
            # Selection of the  corresponding cross section (dictionary of profiles)
            cs = mycs[i]
            # Sorting the crossection under the name 'sorted'
            cs.sort_along(support,'sorted')
            sorted_prof = cs.sorted['sorted']['sorted']
            unsorted_prof = list(cs.myprofiles.keys())
            # checking if any profile was left out while sorting the crossection
            # FIXME respect the profile locations in case of more than one profile
            if len(sorted_prof) != len(unsorted_prof):
                sorted_names =[a.myname for a in sorted_prof]
                # In case a profile was left out, it's appended to the list.
                # This implementation was done this way because it was  occuring only for the first profile
                for j in  unsorted_prof:
                    if j not in sorted_names:
                        sorted_prof.append(cs.myprofiles.get(j)['cs'])

            # selection of the sorted profiles as a list
            sorted_cs = cs.sorted['sorted']['sorted']
            # reversing the order of profile to match a 1D simulation
            sorted_cs.reverse()
            # Appending the new cross section as a list.
            new_cs.append(sorted_cs)

        # Renaming profiles
        counter = 1
        for zne in tqdm(new_cs, desc='renaming profiles:', colour= Colors.TQDM.value):
            for prof in zne:
                prof.myname = f'{counter:d}'
                counter+=1
        # FIXME find a way to return a list of list of list of crossections or a 3D numpy array
        return new_cs

    def sort_all_cross_section_in_one_list(self, mycross: crosssections, zones: Zones, id:int=1) -> list:
        """
        Return all sorted profiles based on the given vectors in
        only one list.

        :param mycross: `crosssections` containing the profiles
        :type mycross: crosssections
        :param zones: `Zones` containing the vectors
        :type zones: Zones
        :param id: Index of the vector in the zone, defaults to 1
        :type id: int, optional
        :return: List of all profiles sorted based on the given vector
        :rtype: list
        """
        sorted_cross_sections = self.sort_crossections_list(mycross, zones, id)
        prof_list = []
        for zone_list in sorted_cross_sections:
            prof_list += zone_list
        return prof_list

    def get_sorted_cross_sections_name(self,  mycross: crosssections, zones: Zones, id:int=1) -> list:
        """
        Return a list of names of  all profiles sorted based on the given vector.

        :param mycross: `crosssections` containing the profiles
        :type mycross: crosssections
        :param zones: `Zones` containing the vectors
        :type zones: Zones
        :param id: Index of the vector in the zone, defaults to 1
        :type id: int, optional
        :return: List of all profiles names sorted based on the given vector
        :rtype: list
        """
        sorted_cross_sections = self.sort_crossections_list(mycross, zones, id)
        name_list = []
        for zone_list in sorted_cross_sections:
            names = [prof.myname for prof in zone_list]
            name_list += names
        return name_list

    def get_sorted_cells_name(self,  mycross: crosssections, zones: Zones, id:int=1) -> list:
        """
        Return a list of names of all profiles sorted based on the given vector.

        :param mycross: `crosssections` containing the profiles
        :type mycross: crosssections
        :param zones: `Zones` containing the vectors
        :type zones: Zones
        :param id: Index of the vector in the zone, defaults to 1
        :type id: int, optional
        :return: List of all profiles names sorted based on the given vector
        :rtype: list
        """
        sorted_cross_sections = self.sort_crossections_list(mycross, zones, id)
        name_list = []
        for zone_list in sorted_cross_sections:
            names = [prof.myname for prof in zone_list[:-1]]
            name_list += names
        return name_list

    def crossection_from_list(self, profiles: list[list[profile]], save_as: str ='') -> crosssections:
        """
        Create and return a cross section object `crosssections` from a list of profiles.

        :param profiles: List of profiles
        :type profiles: list[list[profile]]
        :param save_as: File path of the new  cross section object, defaults to ''
        :type save_as: str, optional
        :return: New cross section
        :rtype: crosssections
        """
        znes = Zones(is2D=False)
        zne= zone(is2D=False, parent= znes)
        znes.add_zone(zne)

        for lst in profiles:
            zne.myvectors += lst
        znes.find_minmax(True)
        mycross = crosssections(znes,'zones')
        if save_as!='':
            mycross.saveas(save_as)
        return mycross

    def add_2_crossections(self,
                           crosssections1: crosssections,
                           crosssections2: crosssections,
                           prefixes: list[str,str]= ["1","2"],
                           save_as:str = '') -> crosssections:
        """
        Concatenate 2 cross sections and
        return the concatenation as a new cross section file.

        :param crosssections1: First cross section
        :type crosssections1: crosssections
        :param crosssections2: Second cross section
        :type crosssections2: crosssections
        :param prefixes: Prefixes for the cross sections, defaults to ["1","2"]
        :type prefixes: list[str,str], optional
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: New cross section
        :rtype: crosssections
        """

        if isinstance(prefixes[0], int) and isinstance(prefixes[1], int):
            prefixes = [str(prefixes[0]),str(prefixes[1])]

        dict_profile1 = crosssections1.myprofiles
        lst1 = list(dict_profile1.values())

        dict_profile2 = crosssections2.myprofiles
        lst2 = list(dict_profile2.values())

        vectors1 = [lst1[i]['cs'] for i in range(len(lst1))]
        vectors2 = [lst2[i]['cs'] for i in range(len(lst2))]
        vec: vector
        for vec in vectors1:
            vec.myname = f'{prefixes[0]}_{vec.myname}'

        for vec in vectors2:
            vec.myname = f'{prefixes[1]}_{vec.myname}'

        new_zones = Zones(is2D=False)
        new_zone = zone(is2D=False, parent=new_zones)
        new_zones.add_zone(new_zone)
        new_zone.myvectors = vectors1 + vectors2

        new_zones.find_minmax(True)
        new_crossections = crosssections(new_zones, 'zones')
        if save_as != '':
            path = self.initialize_file(save_as, 'concatenated_crosssections.vecz')
            new_crossections.find_minmax(True)
            new_crossections.saveas(path)
        return new_crossections

    def create_Zones_from_vectors(self, vectors: list[vector]) -> Zones:
        """
        Return a Zones from a list of vectors.

        :param vectors: List of vectors
        :type vectors: list[vector]
        :return: New Zones
        :rtype: Zones
        """
        new_zones = Zones()
        new_zone = zone(name = 'parallels', parent=new_zones)
        new_zones.add_zone(new_zone)
        for vec in vectors:
            new_zone.add_vector(vec)
        # new_zone.myvectors = vectors
        # new_zone.nbvectors = len(new_zone.myvectors) FIXME Not needed anymore
        new_zones.find_minmax(True)
        return new_zones

    def create_cross_sections_from_vectors(self, profiles: list[profile]) -> crosssections:
        """
        Create and Return a cross section object (`crosssections`)
        from a list of profiles.

        :param profiles: List of profiles
        :type profiles: list[profile]
        :return: New cross section
        :rtype: crosssections
        """
        new_zones = Zones(is2D=False)
        new_zone = zone(is2D=False, parent=new_zones)
        new_zones.add_zone(new_zone)
        new_zone.myvectors = profiles
        new_zones.find_minmax(True)
        new_crossections = crosssections(new_zones, 'vecz')
        return new_crossections

    def extrapolate_extremities(self,
                              crossections : crosssections,
                              added_height: float = 0,
                              save_as:str ='') -> crosssections:
        """
        Return a new cross section with the extremities of each profile extrapolated.

        :param crossections: `crosssections` containing the profiles
        :type crossections: crosssections
        :param added_height: Height to add to the extremities, defaults to 0
        :type added_height: float, optional
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: New cross section with the extremities extrapolated
        :rtype: crosssections
        """
        lst = list(crossections.myprofiles.values())
        profiles = [lst[i]['cs'] for i in range(len(lst))]
        vect: vector
        new_profiles = []
        for vect in profiles:
            vert1 = vect.myvertices[0]
            vert2 = vect.myvertices[-1]
            vect.myvertices.insert(0, wolfvertex(vert1.x, vert1.y,  (vert1.z + added_height)))
            vect.myvertices.append( wolfvertex(vert2.x, vert2.y, (vert2.z + added_height)))
            # vect.nbvertices = len(vect.myvertices)
            # vect.add_vertex(wolfvertex(vert1.x, vert1.y,  (vert1.z + added_height)))
            # vect.add_vertex(wolfvertex(vert2.x, vert2.y, (vert2.z + added_height)))
            vect.find_minmax()
            new_profiles.append(vect)


        new_crossections = self.create_cross_sections_from_vectors(new_profiles)

        if save_as != '':
            path = self.initialize_file(save_as, '_extrapolated_cross_sections.vecz')
            new_crossections.find_minmax(True)
            new_crossections.saveas(path)
        return new_crossections

    def delete_profile(self, mycross: crosssections, profile_keys: list, save_as: str = ''):
        """
        Return a new cross section file were the given profiles have been removed.
         - The profile keys are the names of the profiles to remove.

        :param mycross: `crosssections` containing the profiles
        :type mycross: crosssections
        :param profile_keys: List of profiles keys to remove
        :type profile_keys: list
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: New cross section with the given profiles removed
        :rtype: crosssections
        """
        for profile_key in profile_keys:
            if not isinstance(profile_key,str):
                profile_key = str(profile_key)
            try:
                del mycross.myprofiles[profile_key]
            except KeyError:
                warnings.warn(f"This profile's key ({profile_key}) was not found.")

        if save_as != '':
            mycross.saveas(save_as)

        return mycross

    def roughness_from_polygons(self,
                                array: WolfArray,
                                zones: Zones,
                                mode:typing.Literal['mean', 'median', 'min', 'max', 'value'] = 'mean',
                                value: float = 0.04) -> list[list[float]]:
        """
        Associate a roughness (friction) value to each cross section.

        The value is selected from the  2D cells in between
        the cross section of interest and the next one,
        according to the chosen mode and the polygon file `Zones`.

        The different modes are:
            - mean,
            - median,
            - min,
            - max,
            - value.
        If value is selected, the given value is
        forced on all crossections.

        :param array: WolfArray containing the values
        :type array: WolfArray
        :param zones: Zones containing the vectors
        :type zones: Zones
        :param mode: Mode to select the roughness value, defaults to 'mean'
        :type mode: typing.Literal['mean', 'median', 'min', 'max', 'value'], optional
        :param value: Value to force, defaults to 0.04
        :type value: float, optional
        :return: List of lists of roughnesses value
        :rtype: list[list[float]]
        """
        frictions = []
        #FIXME Check wether a polygon is created or not.
        for zne in tqdm(zones.myzones, desc = 'Extracting roughnesses:', unit= 'Zones', colour= Colors.TQDM.value):
            roughnesses = [array.get_values_insidepoly(vec) for vec in zne.myvectors]
            if mode == 'mean':
                roughness = [np.average(i[0])  for i in roughnesses]
            elif mode =='median':
                roughness = [np.median(i[0]) for i in roughnesses]
            elif mode == 'min':
                roughness = [np.amin(i[0]) for i in roughnesses]
            elif mode == 'max':
                roughness = [np.amax(i[0]) for i in roughnesses]
            elif mode == 'value':
                roughness = [i if i== value else value for i in roughnesses]
            else:
                if self.wx_exists:
                    raise Exception(logging.info('This mode is not defined!'))
                else:
                    raise Exception(_('This mode is not defined!'))
            frictions.append(roughness)

        return frictions

    def roughness_from_profiles(self,
                                array: WolfArray,
                                crosses: list[list[profile]],
                                mode:typing.Literal['mean', 'median', 'min', 'max', 'value'] = 'mean',
                                value:float = 0.04) -> list[list[float]]:
        """
        Associate a roughness (friction) value to each cross section.

        The value is selected from the cells under
        the cross section of interest according to the chosen mode.

        The different modes are:
            - mean,
            - median,
            - min,
            - max,
            - value.
        If value is selected, the given value is
        forced on all crossections.

        :param array: WolfArray containing the values
        :type array: WolfArray
        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param mode: Mode to select the roughness value, defaults to 'mean'
        :type mode: typing.Literal['mean', 'median', 'min', 'max', 'value'], optional
        :param value: Value to force, defaults to 0.04
        :type value: float, optional
        :return: List of lists of roughnesses value
        :rtype: list[list[float]]
        """
        mycs = crosses
        frictions = []
        for znes in tqdm(mycs, desc = 'Extracting roughnesses:', unit= 'Zones', colour= Colors.TQDM.value):
            roughnesses = [array.get_values_underpoly(prof) for prof in znes]
            # roughnesses = [array.get_values_underpoly(prof) for prof in tqdm(znes, desc = 'Extracting roughnesses:', unit= 'Zones', colour= Colors.TQDM.value)]
            if mode == 'mean':
                roughness = [np.average(i[0]) for i in roughnesses]
            elif mode =='median':
                roughness = [np.median(i[0]) for i in roughnesses]
            elif mode == 'min':
                roughness = [np.amin(i[0]) for i in roughnesses]
            elif mode == 'max':
                roughness = [np.amax(i[0]) for i in roughnesses]
            elif mode == 'value':
                roughness = [i if i== value else value for i in roughnesses]
            else:
                if self.wx_exists:
                    raise Exception(logging.info(_('This mode is not defined!')))
                else:
                    raise Exception(_('This mode is not defined!'))
            frictions.append(roughness)
        return frictions

    def roughness_from_value(self,
                             crosses: list[list[profile]],
                             value:float = 0.04) -> list[list[float]]:
        """
        Return a list of lists of roughnesses value.

        The method forces the given value on all crossections.

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param value: Value to force, defaults to 0.04
        :type value: float, optional
        :return: List of lists of roughnesses value
        :rtype: list[list[float]]
        """
        frictions = []
        for zne in tqdm(crosses, desc = 'Forcing roughnesses:', unit= 'Zones', colour= Colors.TQDM.value):
            roughness = [value for prof in zne]
            frictions.append(roughness)
        return frictions

    def ic_relations_hspw(self,
                          crosses: list[list[profile]],
                          h: float =None,
                          zval:float = None) -> np.ndarray:
        """
        Return the HSPW relations (Initial Conditions) of all profiles
        as a numpy arrray for a given water depth or a given altitude.
        np.array

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param h: Water depth, defaults to None
        :type h: float, optional
        :param zval: Altitude, defaults to None
        :type zval: float, optional
        :return: HSPW relations (Initial Conditions) of all profiles
        :rtype: np.ndarray
        """
        prof: profile
        all_relations = []
        mycs = crosses
        zne_id_skeleton =  1
        for znes in tqdm(mycs, desc='Computing IC relations', colour='cyan', unit= 'profile'):
            # zne_id_skeleton = mycrosses.index(znes) + 1
            vec_id_zne = 1
            seg_id_vec = 1
            for prof in znes[:-1]:
                s,z = prof.get_sz()
                zmin = min(z)
                if h:
                    z_computed = h + zmin
                    area, perimeter, width, radius = prof.relation_oneh(cury = z_computed)
                    profile_relations  = [zne_id_skeleton, vec_id_zne, seg_id_vec, area, perimeter, width, radius, h, z_computed]
                    all_relations.append(profile_relations)
                else:
                    if zval:
                        h_computed = zval- zmin
                        area, perimeter, width, radius = prof.relation_oneh(cury = zval)
                        profile_relations = [zne_id_skeleton, vec_id_zne, seg_id_vec, area, perimeter, width, radius, h_computed, zval]
                        all_relations.append(profile_relations)
                    else:
                        if self.wx_exists:
                            raise Exception(logging.info(_('Please enter a water depth (h) or a water surface (z) value!')))
                seg_id_vec += 1
            zne_id_skeleton += 1
        relations = np.array(all_relations)
        return relations, (zne_id_skeleton - 1)

    def test_presence_section_name(self, section: vector, list_of_names:list[str]):
        """Check if a section is in a list of names. Return True if it's not.

        :param section: section (profile)
        :type section: vector
        :param list_of_names: list of section names to check
        :type list_of_names: list[str]
        :return: bool
        """
        name = section.myname
        if isinstance(name, str):
            if "copy" in name.lower():
                name = name.split('_')[0]
        return not name in list_of_names

    def delete_sections_from_cross_sections(self,
                                            cross_sections: crosssections,
                                            list_to_delete: list[str],
                                            save_as = '',
                                            id_zone: int= 0) -> crosssections:
        """Delete a list of sections from a cross_sections object based on their names and
        return a new cross_sections object.

        :param cross_sections: cross sections object
        :type cross_sections: crosssections
        :param list_to_delete: list of section names to delete
        :type list_to_delete: list[str]
        :param id_zone: index of the zone  from which vectors are selected, defaults to 0
        :return: crosssections where the sections are deleted.
        :rtype: crosssections
        """
        # 1. Get all sections as vector from cross_sections
        # all_sections = cross_sections.myzones.deepcopy_zones(add_suffix = False) # add_suffix deepcopy_zones is not needed anymore
        all_sections = cross_sections.myzones.deepcopy_zones()
        sections  = all_sections.myzones[id_zone].myvectors
        # indices_to_delete = []
        sections_filtered = list(filter(lambda section: self.test_presence_section_name(section, list_to_delete), sections))
        all_sections.myzones[id_zone].myvectors = sections_filtered


        # 3. Updating the zone  of sections
        all_sections.find_minmax(update=True)
        # 4. Create a new cross_sections
        new_cross_sections = crosssections(all_sections, format='vecz')
        if save_as != '':
            new_cross_sections.saveas(save_as)
        # Return the new cross_sections
        return new_cross_sections

    def select_sections_from_cross_sections(self,
                                                 cross_sections: crosssections,
                                                 list_to_select: list[str],
                                                 save_as:str ='',
                                                 id_zone: int= 0) -> crosssections:
        """Select a list of sections from a cross_sections object based on their names and
        return a new cross_sections object.

        :param cross_sections: cross sections object
        :type cross_sections: crosssections
        :param list_to_select: list of section names to select
        :type list_to_select: list[str]
        :param id_zone: index of the zone  from which vectors are selected, defaults to 0
        :return: crosssections where the sections are selected.
        :rtype: crosssections
        """

        all_sections =  cross_sections.myzones.myzones[id_zone].myvectors
        names = [section.myname for section in all_sections]
        selection = []
        for name in list_to_select:
            if name in names:
                selection.append(all_sections[names.index(name)])
        zones = Zones()
        zne = zone(parent = zones)
        zones.myzones.append(zne)
        zones.myzones[0].myvectors = selection
        zones.find_minmax(update=True)
        new_cross_sections = crosssections(zones, format='vecz')
        if save_as != '':
            new_cross_sections.saveas(save_as)
        return new_cross_sections


    # --- Graph cross sections ---
    #______________________________

    def plot_graph_crossections(self,
                                mycross: crosssections,
                                vect:vector= None,
                                profile_name = 1,
                                width = 30,
                                height = 15):
        """
        Return a graph on the GraphNotebook format.
        The graph contains the profile characteristics
        (Spatial location, sections, discharges relations, HSPW relations, etc.).

        :param mycross: `crosssections` containing the profiles
        :type mycross: crosssections
        :param vect: `vector` containing the profiles
        in case the profiles should be sorted, defaults to None

        :type vect: vector, optional
        :param profile_name: Index of the profile, defaults to 1
        :type profile_name: int, optional
        :return: Figure containing a plot of the profile charactersitics.
        :rtype: Figure
        """
        myplot = PlotCSAll(None)
        if vect:
            mycross.sort_along(vect.asshapely_ls(),'sorted', downfirst=False)
            myplot.cs_setter(mycross = mycross, active_profile = mycross.get_profile(profile_name-1, 'sorted'))

        else:
            active_profile = mycross.myprofiles[f'{profile_name}']['cs']
            myplot.cs_setter(mycross = mycross, active_profile= active_profile)
            # myplot.cs_setter(mycross = mycross, active_profile= mycross.get_profile(1, 'cs'))
            myplot.figure.set_size_inches(width,height)

    # --- Simulation (Writing simulation files) ---
    #______________________________________________

    def create_directory(self,
                         save_as: str,
                         directory_name: str)-> str:
        '''
        Creates and return a directory based on the inputs:
            - save_as: a  computer path and,
            - directory_name: a desired directory name.

        :param save_as: Computer path
        :type save_as: str
        :param directory_name: Desired directory name
        :type directory_name: str
        :return: Directory path
        :rtype: str
        '''
        directory = os.path.join(save_as, directory_name)
        try:
            os.makedirs(directory, exist_ok= True)
        except OSError as error:
            # print("Directory '%s' cannot be created" % directory_name) # FIXME wx.log message for wolfpy
            if self.wx_exists:
                logging.info(f"The directory {directory_name} cannot be created.")
            else:
                warnings.warn(f"The directory {directory_name} cannot be created.", UserWarning)
        return directory

    def create_simulation_directory(self,
                                    save_as:str,
                                    directory_name:str ='simul') -> str:
        '''
        Create and return a simulation directory.

        :param save_as: Computer path
        :type save_as: str
        :param directory_name: Desired directory name
        :type directory_name: str
        :return: Simulation directory
        :rtype: str
        '''
        self.directory_name = directory_name
        simulation_directory = self.create_directory(save_as, self.directory_name)
        return simulation_directory

    def initialize_file(self,
                        save_as: str,
                        format:str,
                        directory_name:str ='simul') -> str:
        '''
        Create a new file based on:
         - The provided directory or self.directory and,
         - the given extension.

        :param save_as: Computer path
        :type save_as: str
        :param format: File extension
        :type format: str
        :param directory_name: Desired directory name, defaults to 'simul'
        :type directory_name: str, optional
        :return: File path
        :rtype: str
        '''
        if directory_name == '':
            file_path = os.path.join(save_as, format)
        else:
            if self.directory_name != '':
                filename = self.directory_name + format
            else:
                self.directory_name = self.create_simulation_directory(save_as, directory_name)
                filename =self.directory_name + format

            file_path = os.path.join(save_as,filename)

        return file_path

    def count_lists_in_list(self, lst: list[list], nodes_1D = False) -> int:
        r"""
        Return the sum of lengths of lists in a list.
            - /!\ Attention for 1D nodes (nodes_1D),
            the number of nodes is the number
            of crossections minus one.
        :param lst: List of lists
        :type lst: list[list]
        :param nodes_1D: If the nodes are 1D, defaults to False
        :type nodes_1D: bool, optional
        :return: Sum of lengths of lists in a list
        :rtype: int
        """
        counter: int
        counter = 0
        if nodes_1D:
            for i in lst:
                counter += (len(i) -1)

        else:
            for i in lst:
                counter += len(i)
        return counter

    def write_file_from_listof_profiles(self,
                                        file:str,
                                        data:list[list[profile]],
                                        index:list[int],
                                        force_last = False) -> None:
        """
        Writer of  a file from a list of profiles.
        Wolf Template for writing file based on a list of profiles.

        #FIXME ackward method
        :param file: File path
        :type file: str
        :param data: List of profiles
        :type data: list[list[profile]]
        :param index: Index of the profiles
        :type index: list[int]
        :param force_last: If the last profile should be forced, defaults to False
        :type force_last: bool, optional
        :return: None
        :rtype: None
        """


        lgth = self.count_lists_in_list(data, True)
        sep = Constants.SEPARATOR.value
        with open(file,'w') as f:
            f.write(str(lgth)+'\n')
            zne_id_skeleton = 1
            for znes in tqdm(data, dec='Writing files:', colour='Cyan'):
                vec_id_zne = 1 # FIXME Use it or clean it.
                seg_id_vec = 1
                for prof in znes:
                    val1 = int(index[0])
                    val2 = int(index[1])

                    if force_last:
                        val3 = index[2]
                    else:
                        val3 = index[2]

                    f.write(f'{zne_id_skeleton}{sep}{val1}{sep}{val2}{sep}{val3}' + '\n')
                    seg_id_vec+=1
                zne_id_skeleton += 1

            # for zne in tqdm

    def _write_relations_profiles(self,
                                 crosses:list[list[profile]],
                                 save_as:str) -> None:
        r"""
        /!\ Has been deprecated.

        - Write the HSPW (Heigh, wetted Section, wetted Perimeter, top Width)relations
        of each profile in each cross section as a file;
        - Write one corresponding .ptv file (matches profile index to the corresponding profile number);
        - Write one corresponding .gtv file (maches profile number to the correponding relation files).

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """
        prof: profile
        # List of sorted cross sections
        mycs = crosses
        # Separator
        sep = Constants.SEPARATOR.value
        # The directory name that will receive the tabulated relations.
        directory_name = 'cross_sections'
        # Creation of the directory
        cross_directory = self.create_directory(save_as,directory_name)
        # File that will receive the position of tabular values
        ptv_file = self.initialize_file(save_as, fileExtensions.PTV.value)
        # File that will receive the memory links to tabular values
        gtv_file = self.initialize_file(save_as, fileExtensions.GTV.value)
        # Relative position in the simulation directory
        targeted_file ='.\\'
        tartgeted_path = os.path.join(targeted_file, directory_name)
        # Number of segments  in the simulation
        lgth = self.count_lists_in_list(mycs, nodes_1D= True)
        # Writing the files
        with open(gtv_file,'w', newline='\n')as gtv:
            gtv.write(f'{(lgth):12d}'+'\n')
            # ptv file
            with open(ptv_file,'w', newline='\n') as ptv:
                ptv.write(f'{lgth:12d}' +'\n')
                # Zone index in the skeleton (starts at one because Fortran count from one)
                zne_id_skeleton = 1
                # Indice in the gtv and ptv files
                indice = 1
                # iterations on cross sections
                for zne in tqdm (mycs, desc='Writing relations:', colour= Colors.TQDM.value, unit= 'zne'):
                    # vector id in zone
                    vec_id_zne = 1
                    # segment id in vector
                    seg_id_vec = 1

                    for prof in zne:
                                    # Added # FIXME talk to Mr. Archambeau about the new calculations of relations,
                                    # discretization is richer than the vertices' method witch is faster
                                    # and not completely accurate for small values

                    # All relations
                        area,perimeter,radius,depth,width,critical_discharge = prof.relations()

                        filename = f'tv_{zne_id_skeleton}_{vec_id_zne}_{indice}.tv' # FIXME Double zne_id_skeleton
                        gtv_path = os.path.join(tartgeted_path, filename)
                        ptv.write(f'{zne_id_skeleton:12d}{sep}{vec_id_zne:12d}{sep}{seg_id_vec:12d}{sep}{indice:12d}'+'\n') # FIXME Double zne_id_skeleton
                        gtv.write(f'{indice:12d}{sep}{gtv_path}'+'\n')
                        profile_file = os.path.join(cross_directory, filename)
                        # FIXME check whether it is necessary to keep the last profile -> relation
                        #Added
                        with open(profile_file,'w', newline='\n') as pro:
                            pro_lgth = len(area) # FIXME insert a check here
                            pro.write(f'{pro_lgth:12}' + '\n')
                            for i in range(len(area)):
                                h = depth[i]
                                s = area[i]
                                p = perimeter[i]
                                pro.write(f'{h:20.14f}{sep}{s:20.14f}{sep}{p:20.14f}' +'\n')
                        indice += 1
                        seg_id_vec += 1
                    zne_id_skeleton += 1

    def __write_relations_profiles(self,
                                 crosses:list[list[profile]],
                                 save_as:str) -> None:
        r"""
        /!\ Has been deprecated.

        - Write the HSPW (Height, wetted Section, wetted Perimeter, top Width)relations
        of each profile in each cross section as a file;
        - Write one corresponding .ptv file (matches profile index to the corresponding profile number);
        - Write one corresponding .gtv file (maches profile number to the correponding relation files).
        """
        # FIXME something is broken in the routine
        prof: profile
        # List of sorted cross sections
        mycs = crosses
        # Separator
        sep = Constants.SEPARATOR.value
        # The directory name that will receive the tabulated relations.
        directory_name = 'cross_sections'
        # Creation of the directory
        cross_directory = self.create_directory(save_as,directory_name)
        # File that will receive the position of tabular values
        ptv_file = self.initialize_file(save_as, fileExtensions.PTV.value)
        # File that will receive the memory links to tabular values
        gtv_file = self.initialize_file(save_as, fileExtensions.GTV.value)
        # File that will receive the top width relations for each cross sections
        breadth_file = self.initialize_file(save_as, fileExtensions.BREADTH.value)
        depth_file = self.initialize_file(save_as, fileExtensions.DEPTH.value)
        # Relative position in the simulation directory
        targeted_file ='.\\'
        tartgeted_path = os.path.join(targeted_file, directory_name)
        # Number of segments  in the simulation
        lgth = self.count_lists_in_list(mycs, nodes_1D= True)
        # Writing the files
        # gtv file
        with open(gtv_file,'w', newline='\n')as gtv:
            gtv.write(f'{(lgth):12d}'+'\n')
            # ptv file
            with open(ptv_file,'w', newline='\n') as ptv:
                ptv.write(f'{lgth:12d}' +'\n')
                with open(breadth_file,'w', newline='\n') as brdth:
                    with open(depth_file,'w', newline='\n') as dpth:
                        nb_crosses = self.count_lists_in_list(crosses)
                        # brdth.write(f'{nb_crosses:12}' + '\n')
                        # dpth.write(f'{nb_crosses:12}' + '\n')
                        # Zone index in the skeleton (starts at one because Fortran count from one)
                        zne_id_skeleton = 1
                        # Indice in the gtv and ptv files
                        indice = 1
                        # # Collections of depths and breadths
                        depths = []
                        breadths =[]
                        # iterations on cross sections
                        for zne in tqdm (mycs, desc='Writing relations:', colour= Colors.TQDM.value, unit= 'zne'):
                            # vector id in zone
                            vec_id_zne = 1
                            # segment id in vector
                            seg_id_vec = 1

                            # for prof in zne[:-1]:
                            for prof in zne:
                                # Added # FIXME talk to Mr. Archambeau about the new calculations of relations,
                                # discretization is richer than the vertices' method witch is faster
                                # and not completely accurate for small values
                                s,z = prof.get_sz()
                                zmin = min(z)
                                smax =max(s)
                                z_array = np.array(z)
                                z_array = np.unique(z_array)
                                all_relations = [prof.relation_oneh(val) for val in z_array]
                                prof_depths = []
                                prof_breadths =[]
                                filename = f'tv_{zne_id_skeleton}_{vec_id_zne}_{indice}.tv' # FIXME Double zne_id_skeleton
                                gtv_path = os.path.join(tartgeted_path, filename)
                                ptv.write(f'{zne_id_skeleton:12d}{sep}{vec_id_zne:12d}{sep}{seg_id_vec:12d}{sep}{indice:12d}'+'\n') # FIXME Double zne_id_skeleton
                                gtv.write(f'{indice:12d}{sep}{gtv_path}'+'\n')
                                profile_file = os.path.join(cross_directory, filename)
                                with open(profile_file,'w', newline='\n') as pro:
                                        assert len(all_relations) == len(z_array)
                                        pro_lgth = len(all_relations) # FIXME insert a check here
                                        pro.write(f'{pro_lgth:12}' + '\n')
                                        for i in range(pro_lgth):
                                            h = z_array[i ]- zmin
                                            s = all_relations[i][0]
                                            p = all_relations[i][1]
                                            w = all_relations[i][2]
                                            pro.write(f'{h:20.14f}{sep}{s:20.14f}{sep}{p:20.14f}' +'\n')
                                            prof_depths.append(h)
                                            prof_breadths.append(w)
                                depths.append(prof_depths)
                                breadths.append(prof_breadths)


                                indice += 1
                                seg_id_vec += 1
                            zne_id_skeleton += 1

                        # FIXME find a clever way to save files
                        # np.save(breadth_file,np.array(breadths, dtype='object'))
                        # np.save(depth_file,np.array(depths, dtype='object'))
                        # np.savetxt(breadth_file, np.array(breadths,dtype='object'), delimiter='\t', fmt = '%s')
                        # np.savetxt(depth_file, np.array(depths,dtype='object'), delimiter='\t', fmt = '%s')
                            # Added
                        # brdth.write(f'{depths}\n{breadths}')

                        # depths_array = np.array(depths)
                        # breadths_array = np.array(breadths)
                        # np.savetxt(depth_file, depths_array, delimiter='\t',fmt=depths_array.dtype)
                        # np.savetxt(breadth_file, breadths_array, delimiter='\t',fmt=breadths_array.dtype)

    def write_relations_profiles(self,
                                 crosses:list[list[profile]],
                                 save_as:str) -> None:
        """
        - Write the HSPW (Heigh, wetted Section, wetted Perimeter, top Width)relations
        of each profile in each cross section as a file;
        - Write one corresponding .ptv file (matches profile index to the corresponding profile number);
        - Write one corresponding .gtv file (maches profile number to the correponding relation files).

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: None
        :rtype: None
        .. todo:: FIXME make robust tests for all cases
        """
        prof: profile
        # List of sorted cross sections
        mycs = crosses
        # Separator
        sep = Constants.SEPARATOR.value
        # The directory name that will receive the tabulated relations.
        directory_name = 'cross_sections'
        directory_breadths = 'top_widths'
        # Creation of the directory
        cross_directory = self.create_directory(save_as,directory_name)
        breadth_directory = self.create_directory(save_as,directory_breadths )

        # File that will receive the position of tabular values
        ptv_file = self.initialize_file(save_as, fileExtensions.PTV.value)
        # File that will receive the memory links to tabular values
        gtv_file = self.initialize_file(save_as, fileExtensions.GTV.value)
        # Relative position in the simulation directory
        targeted_file ='.\\'
        tartgeted_path = os.path.join(targeted_file, directory_name)
        # Number of segments  in the simulation
        lgth = self.count_lists_in_list(mycs, nodes_1D= True)
        # Writing the files
        # gtv file
        with open(gtv_file,'w', newline='\n')as gtv:
            gtv.write(f'{(lgth):12d}'+'\n')
            # ptv file
            with open(ptv_file,'w', newline='\n') as ptv:
                ptv.write(f'{lgth:12d}' +'\n')
                # Zone index in the skeleton (starts at one because Fortran count from one)
                zne_id_skeleton = 1
                # Indice in the gtv and ptv files
                indice = 1
                # iterations on cross sections
                for zne in tqdm (mycs, desc='Writing relations:', colour= Colors.TQDM.value, unit= 'zne'):
                    # vector id in zone
                    vec_id_zne = 1
                    # segment id in vector
                    seg_id_vec = 1

                    # for prof in zne[:-1]:
                    for prof in zne:
                        # Added # FIXME talk to Mr. Archambeau about the new calculations of relations,
                        # discretization is richer than the vertices' method witch is faster
                        # and not completely accurate for small values
                        s,z = prof.get_sz()
                        zmin = min(z)
                        smax =max(s)
                        z_array = np.array(z)
                        z_array = np.unique(z_array)
                        all_relations = [prof.relation_oneh(val) for val in z_array]
                        filename = f'tv_{zne_id_skeleton}_{vec_id_zne}_{indice}.tv' # FIXME Double zne_id_skeleton
                        gtv_path = os.path.join(tartgeted_path, filename)
                        ptv.write(f'{zne_id_skeleton:12d}{sep}{vec_id_zne:12d}{sep}{seg_id_vec:12d}{sep}{indice:12d}'+'\n') # FIXME Double zne_id_skeleton
                        gtv.write(f'{indice:12d}{sep}{gtv_path}'+'\n')
                        profile_file = os.path.join(cross_directory, filename)

                        fname_breadth = f'tv_{zne_id_skeleton}_{vec_id_zne}_{indice}.breadth' # FIXME Double zne_id_skeleton
                        breadth_file = os.path.join(breadth_directory, fname_breadth)

                        with open(breadth_file,'w', newline='\n') as brdth:
                            with open(profile_file,'w', newline='\n') as pro:
                                    assert len(all_relations) == len(z_array)
                                    pro_lgth = len(all_relations) # FIXME insert a check here
                                    pro.write(f'{pro_lgth:12}' + '\n')
                                    brdth.write(f'{pro_lgth:12}'+ '\n')
                                    for i in range(pro_lgth):
                                        h = z_array[i ]- zmin
                                        s = all_relations[i][0]
                                        p = all_relations[i][1]
                                        w = all_relations[i][2]
                                        pro.write(f'{h:20.14f}{sep}{s:20.14f}{sep}{p:20.14f}' +'\n')
                                        brdth.write(f'{h:20.14f}{sep}{w:20.14f}'+'\n')
                        indice += 1
                        seg_id_vec += 1
                    zne_id_skeleton += 1

    def  write_banks_file(self,
                          crosses: list[list[profile]],
                          save_as: str) -> list[list[profile]]:
        """
       write banks (.banks) file in the given directory.
        - if a directory is not provided, a file named simul.banks is created.

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: List of cross sections
        :rtype: list[list[profile]]
        """
        mycs = crosses
        sep = Constants.SEPARATOR.value
        pre = Constants.PRECISION.value
        bank_file = self.initialize_file(save_as, fileExtensions.BANKS.value)
        lgth = self.count_lists_in_list(mycs, True)
        with open(bank_file,'w') as f:
            f.write(str(lgth)+'\n')
            zne_id_skeleton = 1
            for zne in tqdm(mycs, desc='Writing banks:', colour='cyan', unit='profile'):
                vec_id_zne = 1
                seg_id_vec = 1
                for prof in zne:
                    s,z = prof.get_sz()
                    if prof.bankleft == None:
                        prof.bankleft = z[0]
                    if prof.bankright == None:
                        prof.bankright = z[-1]
                    f.write(f'{zne_id_skeleton}{sep}{vec_id_zne}{sep}{seg_id_vec}{sep}{seg_id_vec}{sep}{prof.bankleft:#.20F}{sep}{prof.bankright:#.20F}'+'\n')
                    seg_id_vec+=1
                zne_id_skeleton+=1
        return mycs

    def write_file_from_np_array(self,
                                 file:str,
                                 data: np.ndarray,
                                 index: list[int],
                                 desc ='Writing:',
                                 force_last = False,
                                 q: float = 0.,
                                 nb_updates: int = 0) -> None:
        """
        Write a file from a numpy array.
        Wolf Template for writing file based on a numpy array.

        :param file: File path
        :type file: str
        :param data: Numpy array
        :type data: np.ndarray
        :param index: Index of the array
        :type index: list[int]
        :param desc: Description, defaults to 'Writing:'
        :type desc: str, optional
        :param force_last: If the last value should be forced, defaults to False
        :type force_last: bool, optional
        :param q: Discharge, defaults to 0.
        :type q: float, optional
        :param nb_updates: Number of updates, defaults to 0
        :type nb_updates: int, optional
        :return: None
        :rtype: None
        """

        sep = Constants.SEPARATOR.value
        with open(file,'w') as f:
            f.write(str(data.shape[0]) + '\n')
            for i in tqdm(data,desc,colour=Colors.TQDM.value):
                val1 =int(i[index[0]])
                val2 = int(i[index[1]])
                val3 = int(i[index[2]])
                if force_last:  #FIXME What was this for?
                    # val3 = index[2]
                    f.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{q:#20F}'+'\n') # Mainly for Qini
                    # f.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{q:d}'+'\n') # Mainly for Qini
                else:
                    value =i[index[3]]
                    f.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{value:#20F}'+'\n') # 1 is still hard coded due to the current data format

    def write_ini_files(self,
                        ic: np.ndarray,
                        save_as: str,
                        q: float = None,
                        nb_updates:int = 0,
                        file_choice:list[str] = ['.hini', '.zini', '.aini']
                    )-> None:
        """
        Write all the intial condition files (.aini, .zini, .hini),
            - if a discharge (q) is provided, .qini is also writen.

        :param ic: Initial conditions
        :type ic: np.ndarray
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param q: Discharge, defaults to None
        :type q: float, optional
        :param nb_updates: Number of updates, defaults to 0
        :type nb_updates: int, optional
        :param file_choice: List of file extensions, defaults to ['.hini', '.zini', '.aini']
        :type file_choice: list[str], optional
        :return: None
        :rtype: None
        """
        # Files
        # Implemented to write only the qini file
        file_aini = self.initialize_file(save_as, fileExtensions.AINI.value)
        file_zini = self.initialize_file(save_as, fileExtensions.ZINI.value)
        file_hini = self.initialize_file(save_as, fileExtensions.HINI.value)
        file_qini = self.initialize_file(save_as, fileExtensions.QINI.value)

        if '.aini' in file_choice:
            self.write_file_from_np_array(file_aini,  ic, [0, 1, 2, 3], nb_updates=nb_updates, desc= 'Writing aini:')
        if '.zini' in file_choice:
            self.write_file_from_np_array(file_zini,  ic, [0, 1, 2, -1], nb_updates=nb_updates, desc ='Writing zini:')
        if '.hini' in file_choice:
            self.write_file_from_np_array(file_hini,  ic, [0, 1, 2, -2], nb_updates=nb_updates, desc = 'Writing hini:')

        # qini
        self.write_file_from_np_array(file_qini,  ic, [0, 1, 2], nb_updates=nb_updates, desc= 'Writing qini:', force_last=True, q=q)

    def write_lengthsvecz_file(self,
                               crosses:list[list[profile]],
                               discretization: float,
                               save_as: str) -> Zones:
        """
        Write the length vecz file.
        The file is mainly use for plotting purposes.

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param discretization: Discret
        :type discretization: float
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: Zones
        :rtype: Zones
        """
        mycs = crosses
        file = self.initialize_file(save_as, fileExtensions.LENGHTSVECZ.value)
        zones = Zones(is2D= False)
        index1 = 1
        for znes in tqdm(mycs, desc = 'Writing length vecz:', colour = Colors.TQDM.value):
            zne = zone(is2D= False, parent = zones)
            zones.add_zone(zne)
            zne.myname = f'zone{index1}'
            vect = vector(is2D=False, parentzone = zne)
            vect.myname = 'bed_min'
            zne.add_vector(vect)
            val1 = 0
            for prof in znes:
                s,z = prof.get_sz()
                val3 = min(z)
                val2 = 0.
                vert = wolfvertex(x= val1, y = val2, z = val3)
                vect.add_vertex(vert)
                val1 += discretization
            index1 += 1

        zones.find_minmax(True)
        zones.saveas(file)
        return zones

    def delete_line_in_txt_file(self, file_path:str, line_to_delete:str):
        """
        Delete a known line in a text file.

        :param file_path: File path
        :type file_path: str
        :param line_to_delete: Line to delete
        :type line_to_delete: str
        """
        with open(file_path,"r") as file:
            lines = file.readlines()

        with open(file_path,"w") as file:
            for line in lines:
                if line !=  line_to_delete:
                    file.write(line)

    def write_line_in_txt_file(self, file_path:str, line_to_write:str):
        """
        Write a line in a text file.

        :param file_path: File path
        :type file_path: str
        :param line_to_write: Line to write
        :type line_to_write: str
        """
        with open(file_path, "w") as file:
            file.write(line_to_write)

    def correct_parameters(self, directory = '', from_steady = False):
        """
        Correct the parameters files by deleting the line
        'Limiteur\t7' in the .param file and
        'Limiteur\t7\tType de limitation des reconstruction en lineaire (integer1)'
        in the .param.default file.

        :param directory: Directory path, defaults to ''
        :type directory: str, optional

        .. note:: FIXME delete from_steady  arguments wherever it's still implemented in this module.
        """

        if directory == '':
            directory = self.directory_name
        for file in os.listdir(directory):
            if file.endswith(".param"):
                param_file = os.path.join(directory, file)
                self.delete_line_in_txt_file(param_file,
                                     'Limiteur\t7\n')
            elif file.endswith(".param.default"):
                default_file = os.path.join(directory, file)
                self.delete_line_in_txt_file(default_file,
                                     'Limiteur\t7\tType de limitation des reconstruction en lineaire (integer1)\n')

    def write_parameters(self,
                         save_as:str,
                         max_iter: int= 100000000,
                         max_time: float = 255600.0,
                         round_time: float= 0.00000000000000000000e-02,
                         local_time_step: int = 0,
                         start_time: float=0.00000000000000000000e-02,
                         write_freq: int = 3600,
                         write_type: int = 2,
                         reconstruction: int =1,
                         rk_model: int = 2,
                         rk_coeff: float = 0.5,
                         courant_number: float = 0.25,
                         froude_max:float = 20,
                         friction_law: int =3,
                         Verbosity: int=1,
                         ) -> None:
        """
        Write the file containing the simulation parameters of a wolf 1D model.

        .. note:: with the implementation of Pyparams object in the Wolf module, this method is deprecating.

        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param max_iter: Maximum iteration, defaults to 100000000
        :type max_iter: int, optional
        :param max_time: Maximum time, defaults to 255600.0
        :type max_time: float, optional
        :param round_time: Round time, defaults to 0.00000000000000000000e-02
        :type round_time: float, optional
        :param local_time_step: Local time step, defaults to 0
        :type local_time_step: int, optional
        :param start_time: Start time, defaults to 0.00000000000000000000e-02
        :type start_time: float, optional
        :param write_freq: Write frequency, defaults to 3600
        :type write_freq: int, optional
        :param write_type: Write type, defaults to 2
        :type write_type: int, optional
        :param reconstruction: Reconstruction, defaults to 1
        :type reconstruction: int, optional
        :param rk_model: RK model, defaults to 2
        :type rk_model: int, optional
        :param rk_coeff: RK coefficient, defaults to 0.5
        :type rk_coeff: float, optional
        :param courant_number: Courant number, defaults to 0.25
        :type courant_number: float, optional
        :param froude_max: Froude max, defaults to 20
        :type froude_max: float, optional
        :param friction_law: Friction law, defaults to 3
        :type friction_law: int, optional
        :param Verbosity: Verbosity, defaults to 1
        :type Verbosity: int, optional
        """
        filename = self.initialize_file(save_as, '.param')
        with open(filename,'w') as f:
            f.write(' Time :'+'\n')
            f.write(f'Maximum iteration\t{max_iter:d}\tNumber of iterations (integer)'+ '\n')
            f.write(f'Maximum time\t{max_time:.1F}\tTime of simulation (double, seconds)'+ '\n')
            f.write(f'Round Time\t{round_time:#.20F}\tForced time interval (double)'+ '\n')
            f.write(f'Local time_stepping\t{local_time_step:d}\tLocal time stepping - 0 = .false., 1 = .true. (integer))'+ '\n')
            f.write(f'Start Time\t{start_time:#.20F}\tStarting time (double)'+ '\n')
            f.write(' Results :'+'\n')
            f.write(f'Write frequency\t{write_freq:#.20F}\tWriting interval (integer or double)' + '\n')
            f.write(f'Write type\t{write_type:d}\tTesting type - iterations = 1, time = 2 (integer)'+ '\n')
            f.write(' Spatial scheme :'+'\n')
            f.write(f'Reconstruction\t{reconstruction:d}\tReconstruction method - constant = 1, linear = 2 (integer)'+'\n')
            f.write(' Temporal scheme :'+'\n')
            f.write(f'RK model\t{rk_model:d}\tRunge-Kutta scheme - 1, 2 or 3 (integer) - (n-1) coefficients to provide'+'\n')
            f.write(f'RK Coeff (2)\t{rk_coeff:#.20F}\tSecond coefficient (double)' + '\n')
            f.write(f'Courant Number\t{courant_number:#.20F}\tLimitation of the time step through the Courant number (double)'+ '\n')
            f.write(' Limitations :'+'\n')
            f.write(f'Maximum Froude\t{froude_max:#.20F}\tLimitation of the results through the Froude number (double)'+ '\n')
            f.write(' Source Terms :'+'\n')
            f.write(f'Friction Law\t{friction_law:d}\tFriction law - Bazin = 1, Colebrook = 2, Manning = 3, Barr-Bathurst = 4'+ '\n')
            f.write(' Verbosity :'+'\n')
            f.write(f'Code Verbosity\t{Verbosity:d}\tVerbosity of the computation - 1 = .true. , 0 = .false. (integer)'+ '\n')
        if self.wx_exists :
            pass
        else:
            checker = Wolf_Param(filename=filename)
            checker.SavetoFile(event=None)

    def _read_hydrograph_from_textfile(self, file:str)-> list[list[list,list]]:
        """
        Read a hydrograph from a text file.

        :param file: File path
        :type file: str
        :return: Hydrograph
        :rtype: list[list[list,list]]
        """
        data = pd.read_csv(file,header=0, delimiter='\t',names=['time','discharge'])
        hydrograph = [[list(data['time']), list(data['discharge'])]]
        return hydrograph

    def _write_infiltrations(self,
                             selected_profiles:list[str],
                             crosses: list[list[profile]],
                             hydrographs: list[list[list,list]],
                             save_as: str,
                             writing_method: Literal['continuous', 'stepwise'] = 'continuous',
                             epsilon:float = 0.01):
        """
        Write the infiltration files (.inf, .infil, .tv).
        - if a writing method is not provided, the default is continuous.

        .. note:: FIXME a dict combining hydrographs and selected profiles could be more useful.

        :param selected_profiles: Selected profiles
        :type selected_profiles: list[str]
        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param hydrographs: Hydrographs
        :type hydrographs: list[list[list,list]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param writing_method: Writing method, defaults to 'continuous'
        :type writing_method: Literal['continuous', 'stepwise'], optional
        :param epsilon: Epsilon, defaults to 0.01
        :type epsilon: float, optional

        """
        mycs = crosses
        sep = Constants.SEPARATOR.value
        selection = self.select_profiles(selected_profiles, mycs)
        inf_file = self.initialize_file(save_as, fileExtensions.INF.value)
        infil_file = self.initialize_file(save_as, fileExtensions.INFIL.value)
        lgth = len(selection)
        target = '.\\'
        if writing_method == 'continuous':
            with open(inf_file, 'w') as inf:
                inf.write(str(lgth) + '\n')
                with open(infil_file, 'w') as infil:
                    infil.write(str(lgth)+'\n')
                    index = 1

                    for id in tqdm(selection, desc='Writing infiltrations', colour= Colors.TQDM.value):
                        val1 = id[0]
                        val2 =id[1]
                        val3=id[2]
                        inf.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{index}' +'\n')
                        tv_name =f'infil{index-1}.tv'
                        tv_file = self.initialize_file(save_as, tv_name, directory_name='')
                        with open(tv_file,'w') as tv:
                            table = hydrographs[index-1] # Hint: Python count from zero
                            durations = table[0]
                            infiltration =  table[1]
                            lgth_duration = len(durations)
                            tv.write(str(lgth_duration) + '\n')
                            for i in range(lgth_duration):
                                tv.write(f'{durations[i]}{sep}{infiltration[i]}' + '\n')
                            infil.write("'"+f'{target + tv_name}'+"'"+'\n')
                            index += 1

        elif writing_method == 'stepwise':
            with open(inf_file, 'w') as inf:
                inf.write(str(lgth) + '\n')
                with open(infil_file, 'w') as infil:
                    infil.write(str(lgth)+'\n')
                    index = 1

                    for id in tqdm(selection, desc='Writing infiltrations', colour= Colors.TQDM.value):
                        val1 = id[0]
                        val2 =id[1]
                        val3=id[2]
                        inf.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{index}' +'\n')
                        tv_name =f'infil{index-1}.tv'
                        tv_file = self.initialize_file(save_as, tv_name, directory_name='')
                        with open(tv_file,'w') as tv:
                            table = hydrographs[index-1] # Hint: Python count from zero
                            durations = table[0]
                            infiltration =  table[1]
                            lgth_duration = len(durations)
                            tv.write(str(int(2*lgth_duration) - 1) + '\n')
                            tv.write(f'{durations[0]}{sep}{infiltration[0]}' + '\n')
                            for a in range(lgth_duration-1):
                                i = a+1
                                tv.write(f'{durations[i] - epsilon}{sep}{infiltration[i-1]}' + '\n')
                                tv.write(f'{durations[i]}{sep}{infiltration[i]}' + '\n')
                            infil.write("'"+f'{target + tv_name}'+"'"+'\n')
                            index += 1


        else:
            raise Exception('Define a writing a method!')

    def read_hydrograph_from_textfile(self, file:str)-> list[list[list,list]]: # FIXME nameread discharges from
        r"""
        Return a hydrograph from a text file.
        /!\ The file should be on the wolf hydrograph format.

        :param file: File path
        :type file: str
        :return: Hydrograph
        :rtype: list[list[list,list]]
        """
        hydrograph = Hydrograph(file)
        return hydrograph

    def write_infiltrations_from_dict(self,
                                        crosses: list[list[profile]],
                                        hydrographs: dict[str, Union[Hydrograph, list,tuple]],
                                        save_as: str,
                                        writing_method: Literal['continuous', 'stepwise'] = 'continuous',
                                        epsilon:float = 0.01
                                        ):
        """
        Write the infiltration files (.inf, .infil, .tv).

        .. note:: FIXME  a dict combining hydrographs and selected profiles could be more useful.

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param hydrographs: Hydrographs
        :type hydrographs: dict[str, Union[Hydrograph, list,tuple]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param writing_method: Writing method, defaults to 'continuous'
        :type writing_method: Literal['continuous', 'stepwise'], optional
        :param epsilon: Epsilon, defaults to 0.01
        :type epsilon: float, optional
        """
        mycs = crosses
        sep = Constants.SEPARATOR.value
        selected_profiles = [prof for prof in hydrographs]
        selection = self.select_profiles(selected_profiles, mycs)
        inf_file = self.initialize_file(save_as, fileExtensions.INF.value)
        infil_file = self.initialize_file(save_as, fileExtensions.INFIL.value)
        lgth = len(hydrographs)
        target = '.\\'
        if writing_method == 'continuous':
            with open(inf_file, 'w') as inf:
                inf.write(str(lgth) + '\n')
                with open(infil_file, 'w') as infil:
                    infil.write(str(lgth)+'\n')
                    index = 1
                    for n in tqdm(range(lgth), desc='Writing infiltrations', colour= Colors.TQDM.value):
                    # for id in tqdm(selection, desc='Writing infiltrations', colour= Colors.TQDM.value):
                        # index_id = selected
                        node = selected_profiles[n]
                        id = selection[n]
                        val1 = id[0]
                        val2 = id[1]
                        val3= id[2]
                        inf.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{index}' +'\n')
                        tv_name =f'infil{index-1}.tv'
                        tv_file = self.initialize_file(save_as, tv_name, directory_name='')
                        if isinstance(hydrographs[node], Hydrograph):
                            hydrographs[node].write_as_wolf_file(tv_file,writing_method='continuous')
                        elif isinstance(hydrographs[node], (list,tuple)):
                            with open(tv_file,'w') as tv:
                                table = hydrographs[node] # Hint: Python count from zero
                                durations = table[0]
                                infiltration =  table[1]
                                lgth_duration = len(durations)
                                tv.write(str(lgth_duration) + '\n')
                                for i in range(lgth_duration):
                                    tv.write(f'{durations[i]}{sep}{infiltration[i]}' + '\n')
                        infil.write("'"+f'{target + tv_name}'+"'"+'\n')
                        index += 1

        elif writing_method == 'stepwise':
            with open(inf_file, 'w') as inf:
                inf.write(str(lgth) + '\n')
                with open(infil_file, 'w') as infil:
                    infil.write(str(lgth)+'\n')
                    index = 1
                    for i in tqdm(range(lgth), desc='Writing infiltrations', colour= Colors.TQDM.value):
                        node = selected_profiles[i]
                        id = selection[i]
                        val1 = id[0]
                        val2 = id[1]
                        val3= id[2]
                        inf.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{index}' +'\n')
                        tv_name =f'infil{index-1}.tv'
                        tv_file = self.initialize_file(save_as, tv_name, directory_name='')
                        # FIXME id issue
                        if isinstance(hydrographs[node], Hydrograph):
                            hydrographs[node].write_as_wolf_file(tv_file,writing_method='stepwise')
                        elif isinstance(hydrographs[node], (list,tuple)):
                            with open(tv_file,'w') as tv:
                                table = hydrographs[node] # Hint: Python count from zero
                                durations = table[0]
                                infiltration =  table[1]
                                lgth_duration = len(durations)
                                tv.write(str(int(2*lgth_duration) - 1) + '\n')
                                tv.write(f'{durations[0]}{sep}{infiltration[0]}' + '\n')
                                for a in range(lgth_duration-1):
                                    i = a+1
                                    tv.write(f'{durations[i] - epsilon}{sep}{infiltration[i-1]}' + '\n')
                                    tv.write(f'{durations[i]}{sep}{infiltration[i]}' + '\n')
                        infil.write("'"+f'{target + tv_name}'+"'"+'\n')
                        index += 1
        else:
            raise Exception('Define a writing a method!')

    def write_infiltrations(self,
                             selected_profiles:list[str],
                             crosses: list[list[profile]],
                             hydrographs: Union[list[Hydrograph], list[list[list,list]]],
                             save_as: str,
                             writing_method: Literal['continuous', 'stepwise'] = 'continuous',
                             epsilon:float = 0.01):
        r"""
        - Write the infiltration files (.inf, .infil, .tv) and,
        - Apply the preprocessing mode to the hydrographs before writing them.

        /!\  if a writing method is not provided, the default is continuous.

        :param selected_profiles: Selected profiles
        :type selected_profiles: list[str]
        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param hydrographs: Hydrographs
        :type hydrographs: Union[list[Hydrograph], list[list[list,list]]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param writing_method: Writing method, defaults to 'continuous'
        :type writing_method: Literal['continuous', 'stepwise'], optional
        :param epsilon: Epsilon, defaults to 0.01
        :type epsilon: float, optional
        """
        mycs = crosses
        sep = Constants.SEPARATOR.value

        selection = self.select_profiles(selected_profiles, mycs)
        inf_file = self.initialize_file(save_as, fileExtensions.INF.value)
        infil_file = self.initialize_file(save_as, fileExtensions.INFIL.value)

        lgth = len(selection)
        target = '.\\'
        if writing_method == 'continuous':
            with open(inf_file, 'w') as inf:
                inf.write(str(lgth) + '\n')
                with open(infil_file, 'w') as infil:
                    infil.write(str(lgth)+'\n')
                    index = 1

                    for id in tqdm(selection, desc='Writing infiltrations', colour= Colors.TQDM.value):
                        val1 = id[0]
                        val2 =id[1]
                        val3=id[2]
                        inf.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{index}' +'\n')
                        tv_name =f'infil{index-1}.tv'
                        tv_file = self.initialize_file(save_as, tv_name, directory_name='')
                        if isinstance(hydrographs[index -1], Hydrograph):
                            hydrographs[index -1].write_as_wolf_file(tv_file,writing_method='continuous')
                        elif isinstance(hydrographs[index -1], list):
                            with open(tv_file,'w') as tv:
                                table = hydrographs[index-1] # Hint: Python count from zero
                                durations = table[0]
                                infiltration =  table[1]
                                lgth_duration = len(durations)
                                tv.write(str(lgth_duration) + '\n')
                                for i in range(lgth_duration):
                                    tv.write(f'{durations[i]}{sep}{infiltration[i]}' + '\n')
                        infil.write("'"+f'{target + tv_name}'+"'"+'\n')
                        index += 1

        elif writing_method == 'stepwise':
            with open(inf_file, 'w') as inf:
                inf.write(str(lgth) + '\n')
                with open(infil_file, 'w') as infil:
                    infil.write(str(lgth)+'\n')
                    index = 1

                    for id in tqdm(selection, desc='Writing infiltrations', colour= Colors.TQDM.value):
                        val1 = id[0]
                        val2 =id[1]
                        val3=id[2]
                        inf.write(f'{val1}{sep}{val2}{sep}{val3}{sep}{index}' +'\n')
                        tv_name =f'infil{index-1}.tv'
                        tv_file = self.initialize_file(save_as, tv_name, directory_name='')
                        if isinstance(hydrographs[index -1], Hydrograph):
                            hydrographs[index -1].write_as_wolf_file(tv_file,
                                                                                           writing_method='stepwise',
                                                                                           epsilon=epsilon)
                        elif isinstance(hydrographs[index -1], list):
                            with open(tv_file,'w') as tv:
                                table = hydrographs[index-1] # Hint: Python count from zero
                                durations = table[0]
                                infiltration =  table[1]
                                lgth_duration = len(durations)
                                tv.write(str(int(2*lgth_duration) - 1) + '\n')
                                tv.write(f'{durations[0]}{sep}{infiltration[0]}' + '\n')
                                for a in range(lgth_duration-1):
                                    i = a+1
                                    tv.write(f'{durations[i] - epsilon}{sep}{infiltration[i-1]}' + '\n')
                                    tv.write(f'{durations[i]}{sep}{infiltration[i]}' + '\n')
                        infil.write("'"+f'{target + tv_name}'+"'"+'\n')
                        index += 1


        else:
            raise Exception('Define a writing a method!')

    def select_one_profile(self,
                           profile_name: str,
                           crosses: list[list[profile]]) -> list[int,int,int]:
        """
        Return the selected profile.
        :raise: if the profile is not found, an exception is raised.

        :param profile_name: Profile name
        :type profile_name: str
        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :return: Selected profile
        :rtype: list[int,int,int]
        """
        mycs = crosses
        indice = 1
        zne_id_skeleton = 1
        for znes in mycs:
            vec_id_zne = 1
            seg_id_vec = 1
            for prof in znes:
                if profile_name == prof.myname:
                    selection = [zne_id_skeleton, vec_id_zne, seg_id_vec, indice]
                    return selection
                else:
                    seg_id_vec += 1
                    indice += 1
            zne_id_skeleton += 1


        if self.wx_exists:
            raise Exception(logging.info(_(f'The Profile -> {profile_name} was not found.')))
        else:
            raise Exception(_(f'The Profile -> {profile_name} was not found.'))

    def select_profiles(self,
                        profiles_names:list[str],
                        crosses: list[profile]) -> list[list[int, int,int]]:
        """
        Return a list of lists containing
        the respective indices of the selected profiles.

        :param profiles_names: Profiles names
        :type profiles_names: list[str]
        :param crosses: List of cross sections
        :type crosses: list[profile]
        :return: Selected profiles
        :rtype: list[list[int, int,int]]
        """
        mycs = crosses
        selection = []
        for name in tqdm(profiles_names, desc= 'selecting profiles', colour = Colors.TQDM.value):
            selected =self.select_one_profile(name, mycs)
            selection.append(selected)

        return selection

    def write_cvg_file(self, selected_profiles:list[str], crosses: list[list[profile]], save_as:str) -> None:
        """
        Specify the node for the code verbosity in the shell (.cvg_file).

        .. note:: with the implementation of Pyparams object in the Wolf module, this method is deprecating.

        :param selected_profiles: Selected profiles
        :type selected_profiles: list[str]
        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """
        mycs =  crosses
        sep= Constants.SEPARATOR.value
        selection = self.select_profiles(selected_profiles, mycs)
        cvg_file = self.initialize_file(save_as, '.cvg')
        lgth = len(selection)
        with open(cvg_file, 'w') as cvg:
            cvg.write(str(lgth)+'\n')
            for id in tqdm(selection, desc='Writing .cvg:',colour= Colors.TQDM.value):
                val1 = id[0]
                val2 = id[1]
                val3 = id[2]
                cvg.write(f'{val1}{sep}{val1}{sep}{val3}' + '\n') #FIXME modified for verificaton (val1 2 times)

    def write_cvgn_file(self, selected_profiles:list[str], crosses: list[list[profile]], save_as:str):
        """
        Write the file for Code verbosity on nodes (cvgn.file).

        .. note:: with the implementation of Pyparams object in the Wolf module, this method is deprecating.

        :param selected_profiles: Selected profiles
        :type selected_profiles: list[str]
        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """
        mycs = crosses
        sep = Constants.SEPARATOR.value
        selection = self.select_profiles(selected_profiles, mycs)
        cvgn_file = self.initialize_file(save_as,'.cvgn')
        lgth = len(selection)
        with open(cvgn_file, 'w') as cvgn:
            cvgn.write(str(lgth)+ '\n')
            index = 1
            for id in tqdm(selection, desc='Writing .cvgn file', colour= Colors.TQDM.value):
                val1 =id[0]
                val2 = id[1]
                val3 = id[2]
                cvgn.write(f'{val1}{sep}{val1}{sep}{val3}{sep}{val1}')
                index += 1

    def write_vector_files(self,
                           cross:list[list[profile]],
                           save_as: str,
                           banksbed:Zones = None,
                           which_type:Literal['vec','vecz','both'] = 'both'):
        """
        Write 3 vectors files.
            - A 3D vector connecting all profiles bed in each zone,
            - A 2D vector connecting all profiles bed in each zone,
            - A length file (for plotting purpose)

        :param cross: List of cross sections
        :type cross: list[list[profile]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param banksbed: Banks and bed, defaults to None
        :type banksbed: Zones, optional
        :param which_type: Which type, defaults to 'both'
        :type which_type: Literal['vec','vecz','both'], optional
        :return: Zones
        :rtype: Zones
        """
        # FIXME add an option to select the middle of the crossection instead of just the bottom.
        # FIXME delete discretization from all examples and from this method. It's not used

        # Creation of files
        vecz_file = self.initialize_file(save_as,'.vecz')
        vec_file = self.initialize_file(save_as,'.vec')
        # # length_file = self.initialize_file(save_as,'_length.vecz')      #Not Useful here: inadequate format
        # Creation of Zones

        vecz_zones = Zones()
        vec_zones = Zones(is2D=True)
        banks_zones = Zones()
        # First index in the skeleton
        index1 = 1
        # Iterations on the zones
        for znes in tqdm(cross, desc= 'Writing vectors:', colour= Colors.TQDM.value):
            # Creation of zones
            banks_zone = zone(is2D=False, parent= banks_zones)
            zne1 = zone(is2D=False, parent=vecz_zones)
            zne2 = zone(is2D=True, parent=vec_zones)

            zne1.myname= f'{index1}'
            zne2.myname= f'{index1}'
            banks_zone.myname= f'{index1}'

            # Adding the zone to the Zones
            vecz_zones.add_zone(zne1)
            vec_zones.add_zone(zne2)
            banks_zones.add_zone(banks_zone)


            # Creation of vectors
            vector_index = 1
            vect1 = vector(is2D=False, name = f'{vector_index}', parentzone=zne1)
            vect2 = vector(is2D=True, name = f'{vector_index}', parentzone=zne2)
            left = vector(is2D=True, name = 'left', parentzone=banks_zone)
            bed = vector(is2D=True, name = 'bed', parentzone=banks_zone)
            right = vector(is2D=True, name = 'right', parentzone=banks_zone)

            # Adding the vectors to the zones
            zne1.add_vector(vect1)
            zne2.add_vector(vect2)
            banks_zone.add_vector(left)
            banks_zone.add_vector(bed)
            banks_zone.add_vector(right)

            # iterations on profiles

            check = [] # to delete
            if banksbed == None:
                if self.banksbed != None:
                    bed_vectors = self.set_banksbed_vectors(self.banksbed)
                    for prof in znes:
                        # for vert in prof.myvertices:
                        #     check.append((min(vert.z), prof.myname)) #to delete

                        # print(prof.myname, prof.myvertices[0], prof.myvertices[-1])
                        assert prof.banksbed_postype == postype.BY_VERTEX
                        self.set_banksbed_vertex_from_ls(prof, bed_vectors)
                        vect1.add_vertex(prof.bed)
                        vect2.add_vertex(prof.bed)
                        left.add_vertex(prof.bankleft)
                        bed.add_vertex(prof.bed)
                        right.add_vertex(prof.bankright)
                    # print(min(check)) #to delete
                    banks_zones.force3D = True
                    banks_zones.find_minmax(True)
                    banks_zones.saveas(vec_file[:-4] +'_banksbed.vecz')


                else:
                    for prof in znes:
                        assert prof.banksbed_postype == postype.BY_VERTEX
                        vertex_bed = prof.bed_vertex
                        vect1.add_vertex(vertex_bed)
                        vect2.add_vertex(wolfvertex(vertex_bed.x, vertex_bed.y))


            elif banksbed != None:
                bed_vectors = self.set_banksbed_vectors(banksbed)
                for prof in znes:
                    # assert prof.banksbed_postype == postype.BY_VERTEX
                    self.set_banksbed_vertex_from_ls(prof, bed_vectors)
                    vertex_bed = prof.bed_vertex
                    vect1.add_vertex(vertex_bed)
                    vect2.add_vertex(wolfvertex(vertex_bed.x, vertex_bed.y))
                banks_zones.force3D = True
                banks_zones.find_minmax(True)
                banks_zones.saveas(vec_file[:-4] +'_banksbed.vecz')
        vecz_zones.force3D = True
        vecz_zones.find_minmax(True)
        vec_zones.find_minmax(True)
        if which_type =='both':
            vecz_zones.saveas(vecz_file)
            vec_zones.saveas(vec_file)
        elif which_type =='vec':
            vec_zones.saveas(vec_file)
        elif which_type =='vecz':
            vecz_zones.saveas(vecz_file)
        return vecz_zones

    def set_banksbed_vertex_from_ls(self, prof: profile, ls: tuple[LineString]):
        """
        Set the banks and bed from a LineString.

        :param prof: Profile
        :type prof: profile
        :param ls: LineString
        :type ls: tuple[LineString]
        """
        prof_ls = prof.asshapely_ls()
        left_inter = prof_ls.intersection(ls[0])
        bed_inter =prof_ls.intersection(ls[1])
        right_inter =prof_ls.intersection(ls[2])
        # print(left_inter, bed_inter, right_inter)

        assert prof.banksbed_postype == postype.BY_VERTEX
        # FIXME insert a test checking the intersections between profiles and parallels.
        assert isinstance(left_inter, Point), f'The section: {prof.myname} - left intersection is not a Point but a {type(left_inter)}'
        prof.bankleft = wolfvertex(left_inter.x, left_inter.y, left_inter.z)
        prof.bed = wolfvertex(bed_inter.x, bed_inter.y, bed_inter.z)
        assert isinstance(right_inter, Point), f'The section: {prof.myname} - left intersection is not a Point but a {type(right_inter)}'
        prof.bankright = wolfvertex(right_inter.x, right_inter.y, right_inter.z)
        prof.find_minmax()

    def set_banksbed_vectors(self, zones: Zones) -> tuple[LineString]:
        """
        Set the banks and bed from a Zones.

        :param zones: Zones
        :type zones: Zones
        :return: tuple[LineString]
        :rtype: tuple[LineString]
        """
        if isinstance(zones, str):
            try:
                znes = Zones(zones)
            except:
                raise Exception('Bad entry')
        else:
            znes = zones

        self.banksbed = znes
        left_bank = znes.myzones[0].myvectors[0]
        bed = znes.myzones[0].myvectors[1]
        right_bank = znes.myzones[0].myvectors[2]
        left_ls = left_bank.asshapely_ls()
        right_ls = right_bank.asshapely_ls()
        bed_ls = bed.asshapely_ls()
        return (left_ls, bed_ls, right_ls)

    def find_banksbed(self, prof: profile, banks: Zones):
        """
        Find the banks and bed (`vector`) from a profile (`profile`) and a Zones.
        The banks and bed points are the intersection between the profile and the bed and banks .

        :param prof: Profile
        :type prof: profile
        :param banks: Banks
        :type banks: Zones
        """

        # river banks
        left_bank = banks.myzones[0].myvectors[0]
        bed_bank = banks.myzones[0].myvectors[1]
        right_bank = banks.myzones[0].myvectors[2]
        prof_ls = prof.asshapely_ls()

        left_ls = left_bank.asshapely_ls()
        prof_ls = prof.asshapely_ls()
        left_inter =prof_ls.intersection(left_ls)
        s_left = prof.get_s_from_xy(wolfvertex(left_inter.x, left_inter.y))
        prof.update_banksbed_from_s3d('left', s_left)

        print(prof.bankleft_vertex.x, prof.bankleft_vertex.y)

    def write_lengths_file(self, crosses: list[list[profile]], discretization: float, save_as: str)-> None:
        """
        Write the lengths file `.lengths` of a 1D model.

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param discretization: Discretization
        :type discretization: float
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """
        mycs = crosses
        sep = Constants.SEPARATOR.value
        length_file = self.initialize_file(save_as, '.lengths')
        lgth = self.count_lists_in_list(mycs, True)
        with open(length_file,'w',newline='\n') as f:
            f.write(f'{lgth:12d}'+'\n')
            # index0 = 1  #FIXME because there was only one vector per zone in the vesdre valley
            index1 = 1
            for znes in tqdm(mycs, desc= 'Writing .lengths:', colour= Colors.TQDM.value):
                vector_id = 1
                index2 = 1
                for prof in znes:
                    f.write(f'{index1:12d}{sep}{vector_id:12d}{sep}{index2:12d}{sep}{discretization:15.8f}'+'\n')
                    index2 += 1
                index1 += 1
            f.close()

    def write_roughnesses(self, roughnesses: list[list[float]], save_as) -> None:
        """
        Write the roughnesses file `.rough` of 1D model.

        :param roughnesses: Roughnesses
        :type roughnesses: list[list[float]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """
        myroughnesses = roughnesses
        sep = Constants.SEPARATOR.value
        # FIXME add an assert between the number of profiles and the number of roughnesses
        rough_file = self.initialize_file(save_as, '.rough')
        lgth = self.count_lists_in_list(myroughnesses,True)

        with open(rough_file,'w') as f:
            f.write(str(lgth)+'\n')

            index1 = 1
            for zne in tqdm(myroughnesses, desc='Writing roughnesses:', colour= Colors.TQDM.value, unit='zone'):
                index2=1
                for prof_rough in zne:
                    f.write(f'{1}{sep}{index1}{sep}{index2}{sep}{prof_rough:#.20F}' + '\n')
                    index2 += 1
            # f.write(f'{1}{sep}{index1}{sep}{index2}{sep}{prof_rough:#.20F}') # Duplication of the last value because the approximation is made in between profiles.

    def save_sorted_crosssesctions(self, sorted_cross:list[list[profile]], save_as:str):
        """
        Save the sorted cross sections.

        :param sorted_cross: Sorted cross sections
        :type sorted_cross: list[list[profile]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """
        for profs in sorted_cross:
            new_zones = Zones(is2D=False)
            new_zone = zone(is2D=False,parent=new_zones)
            new_zones.add_zone(new_zone)
            new_zone.myvectors = profs
            new_zones.find_minmax(True)

            new_cross_sections = crosssections(new_zones, 'zones')
            cross_file = self.initialize_file(save_as, '_crosssections.vecz')
            new_cross_sections.saveas(cross_file)

    def test_intersection_linestring_and_profile(self, ls: LineString, prof: profile):
        """
        Test the intersection between a LineString and a profile.

        :param ls: LineString
        :type ls: LineString
        :param prof: Profile
        :type prof: profile
        :return: True if there is no intersection, False otherwise
        :rtype: bool
        """
        profile_ls = prof.asshapely_ls()
        # intersection = ls.intersection(profile_ls)
        intersection = ls.intersects(profile_ls)
        if intersection:
            return False
        else:
            return True

    def delete_intesections_profile_vectors(self,
                                            cross_sections: crosssections,
                                            zones: Zones,
                                            save_as:str ='',
                                            id_zone = 0) -> crosssections:
        '''
        Delete the profiles in cross-sections file
        that are intersecting the vectors contained
        in a Zones.

        :param cross_sections: Cross sections
        :type cross_sections: crosssections
        :param zones: Zones
        :type zones: Zones
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param id_zone: Id of the zone, defaults to 0
        :type id_zone: int, optional
        '''
        mycs = cross_sections.myprofiles
        profiles =[]

        for curkey in mycs:
           profiles.append( mycs[curkey]['cs'])

        for zne in zones.myzones:
            for vec in zne.myvectors:
                vec_ls = vec.asshapely_ls()
                profiles = list(filter(lambda prof : self.test_intersection_linestring_and_profile(vec_ls, prof), profiles))

        new_crossections = self.create_cross_sections_from_vectors(profiles)
        if save_as != '':
            new_crossections.saveas(save_as)

        return new_crossections

    def create_profile_from_vector(self, vect: vector, topo_array: WolfArray) -> profile:
        """
        Create a new profile from a vector and a topographic array.

        :param vect: Vector
        :type vect: vector
        :param topo_array: Topography array
        :type topo_array: WolfArray
        :return: Profile
        :rtype: profile
        """
        ds = min(topo_array.dx, topo_array.dy) # Discretisation step
        pts = vect._refine2D(ds)
        values = [topo_array.get_value(curpt.x, curpt.y, nullvalue = -99999) for curpt in pts]

        if vect.myname == '':
            prof =  vector(name = 'inserted', is2D = False)
        else:
            prof =  vector(name = vect.myname, is2D = False)

        for curpt, curvalue in zip(pts,values):
                    prof.add_vertex(wolfvertex(curpt.x, curpt.y, curvalue))

        prof.find_minmax()

        new_profile = profile(prof.myname)
        new_profile.myvertices = copy.deepcopy(prof.myvertices)
        # new_profile.nbvertices = copy.deepcopy(prof.nbvertices)
        new_profile.find_minmax()
        return new_profile

    def insert_profiles_from_2D_zones(self,
                                      cross_sections: crosssections,
                                      zones: Zones,
                                      topo_array: WolfArray,
                                      save_as = '') -> crosssections:
        """
        Concatenate a `Zones` of 2D vectors to a `crosssections` file
        and return a new `crosssections` file  as the result of the concatenation.

        :param cross_sections: Cross sections
        :type cross_sections: crosssections
        :param zones: Zones
        :type zones: Zones
        :param topo_array: Topography array
        :type topo_array: WolfArray
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: Cross sections
        :rtype: crosssections
        """
        mycs = cross_sections.myprofiles
        profiles =[]
        for curkey in mycs:
           profiles.append( mycs[curkey]['cs'])

        # ds = min(topo_array.dx, topo_array.dy)
        for zne in zones.myzones:
            for vect in tqdm(zne.myvectors):
                new_profile = self.create_profile_from_vector(vect,topo_array)
                profiles.append(new_profile)

        new_crosssections = self.create_cross_sections_from_vectors(profiles)

        if save_as != '':
            new_crosssections.saveas(save_as)

        return new_crosssections

    def insert_cross_sections_from_zones(self,
                                      cross_sections: crosssections,
                                      zones: Zones,
                                      topo_array: WolfArray,
                                      save_as = '') -> crosssections:
        """
        Concatenate a `Zones` of 2D vectors to a `crosssections` file
        after deleting the profiles that are intersecting the vectors contained in the `Zones`.
        Return a new `crosssections` file  which is  the result of the concatenation.

        :param cross_sections: Cross sections
        :type cross_sections: crosssections
        :param zones: Zones
        :type zones: Zones
        :param topo_array: Topography array
        :type topo_array: WolfArray
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: Cross sections
        :rtype: crosssections
        """

        cleaned_cross_sections = self.delete_intesections_profile_vectors(cross_sections,zones)
        new_cross_sections =  self.insert_profiles_from_2D_zones(cleaned_cross_sections, zones,topo_array,save_as)

        return new_cross_sections

    def extend_parallels(self, vect: vector, left_distance: float, right_distance: float, save_as:str='') -> Zones:
        """
        Extend the distance between parallels of a vector and return a new `Zones` file.

        :param vect: Vector (bed)
        :type vect: vector
        :param left_distance: Left distance (left bank)
        :type left_distance: float
        :param right_distance: Right distance (right bank)
        :type right_distance: float
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :return: Zones
        :rtype: Zones
        """
        left_parallels = vect.parallel_offset(left_distance, side='left')
        right_parallels = vect.parallel_offset(right_distance, side='right')
        vectors = [right_parallels,vect, left_parallels]
        new_zones = self.create_Zones_from_vectors(vectors)
        if save_as != '':
            new_zones.saveas(save_as)
        return new_zones

    def write_generic_file(self, save_as):
        """
        Write a generic file for the 1D model.
        The generic file is an essential pre-requiste for  the Fortran code
        inorder to read the model files.

        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """

        gen_file = self.initialize_file(save_as,"")
        with open(gen_file,'w') as f:
            return

        # return gen_file

    def convert_type_boundary_condition(self,
                                        type_bc: Union[int,str]):
        """ Convert the type of boundary conditions written as string into integer
        readable by the FORTRAN code (executable).
        - Type of BC, value\n
        -----------------\n
        - waterdepth ->	    1\n
        - waterlevel ->	    2\n

        - discharge ->	    3\n
        - froude ->	        4\n
        - free ->	        5\n
        - impervious ->	  99\n
        - junction ->	  100\n
        - mobile_dam ->	  127\n
        """

        if isinstance(type_bc, int):
            if type_bc in (1,2,3,4,5,99,100,127):
                return type_bc
            else:
                if self.wx_exists:
                    raise Exception(logging.info(_('Bad type of boundary condition.')))
                else:
                    raise Exception(_('Bad type of boundary condition.'))

        elif isinstance(type_bc, str):
            if type_bc.lower() == 'water depth':
                return 1
            elif type_bc.lower() == 'water level':
                return 2
            elif type_bc.lower() == 'discharge':
                return 3
            elif type_bc.lower() == 'froude':
                return 4
            elif type_bc.lower() == 'free':
                return 5
            elif type_bc.lower() == 'impervious':
                return 99
            elif  type_bc.lower() == 'junction':
                return 100
            elif type_bc.lower() == 'mobile_dam':
                return 127
            else:
                if self.wx_exists:
                    raise Exception(logging.info(_('Bad type of boundary condition.')))
                else:
                    raise Exception(_('Bad type of boundary condition.'))

    def write_cl_file(self,
                      crosses: list[list[profile]],
                      cl_value: dict[str:(str,str,float)],
                      save_as:str ): #selected_profiles:list[str],
        """
        Write the file of boundary conditions (.cl file).
        cl value(`profile name`: (`upstream or downstream`,
        `type of boundary condition` , `value of boundary
        condition`))

        - Type of BC, value\n
        -----------------\n
        - waterdepth ->	    1\n
        - waterlevel ->	    2\n
        - discharge ->	    3\n
        - froude ->	        4\n
        - free ->	        5\n
        - impervious ->	  99\n
        - junction ->	  100\n
        - mobile_dam ->	  127\n

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param cl_value: Boundary conditions values
        :type cl_value: dict[str:(str,str,float)]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """
        condition_loc: str
        # Cross sections
        mycs = crosses
        # Constant used as THE separator in the text file
        sep = Constants.SEPARATOR.value
        # Names of selected profiles
        selected_profiles = list(cl_value.keys())
        # Selection of profiles indices based on their names.
        selection = self.select_profiles(selected_profiles, mycs)
        # Creation of the boundary conditions file
        cl_file = self.initialize_file(save_as,'.cl')
        # File length -> The number of available profiles
        lgth = len(selected_profiles)
        # Available types of boundary conditions in WOLF1D
        sample = [1,2,3,4,5,99,100,127]
        # Writing the file
        with open(cl_file,'w', newline='\n') as  cl:
            # First line the number of boundary conditions
            cl.write(f'{lgth:12d}' + '\n')
            # Iterations in the list of selected profiles
            for prof in tqdm(selected_profiles, desc= _('Writing boundary conditions'), colour = Colors.TQDM.value):
                # Extraction of the corresponding conditions from the dictionary values
                b_condition = cl_value.get(prof)
                # Location of the condition Upstream or Downstream
                condition_loc = b_condition[0]
                # Type of condition
                condition_type = self.convert_type_boundary_condition(b_condition[1])
                # Value to be use as the condition
                condition_value = b_condition[2]

                #Testing the inputs
                # Checking the validity of the provided location
                if condition_loc.lower() == 'downstream':
                    loc = -1
                elif condition_loc.lower() == 'upstream':
                    loc = 1
                else:
                    if self.wx_exists:
                        raise Exception(logging.info(_('Bad location of boundary condition.')))
                    else:
                        raise Exception(_('Bad location of boundary condition.'))
                # Checking the validity of the provided type
                if condition_type in sample:
                    id = selected_profiles.index(prof)
                    prof_indices = selection[id]
                    val1 = prof_indices[0] # FIXME check whether it should start from 0 or from 1
                    val2 = prof_indices[1]
                    # Writing the condition.
                    # cl.write(f'{val1:12d}{sep}{val2:12d}{sep}{loc:12d}{sep}{condition_type:12d}{sep}{condition_value:20.14f}' +'\n')

                    # FIXME testing the location
                    if loc == 1:
                        cl.write(f'{np.int32(val1)}{sep}{np.int32(val2)}{sep}{np.int32(loc)}{sep}{np.int32(condition_type)}{sep}{np.float32(condition_value)}{sep}zone, vecteur, amont=1 & aval=-1, type,  valeur' +'\n')
                    else:
                        cl.write(f'{np.int32(val1)}{sep}{np.int32(val2)}{sep}{np.int32(loc)}{sep}{np.int32(condition_type)}{sep}{np.float32(condition_value)}' +'\n')

                # Log messages
                else:
                    if self.wx_exists:
                        raise Exception(logging.info(_('Bad type of boundary condition.')))
                    else:
                        raise Exception(_('Bad type of boundary condition.'))

    def write_width_file(self, crosses:list[list[profile]], width:float , save_as:str):
        r'''
        Write the width file (.width file).
        - The width is constant for all the profiles

        Only used for rectangular channels.
        /!\ The width is the same for all the profiles
        /!\ The width is the same for all the zones
        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param width: Width
        :type width: float
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        '''
        mycs = crosses
        sep = Constants.SEPARATOR.value
        width_file = self.initialize_file(save_as, '`.width`')
        lgth = self.count_lists_in_list(mycs,True)

        with open(width_file,'w') as f:
            f.write(str(f'{lgth}' + '\n'))

            index1 = 1
            for zne in tqdm(mycs,desc='Writing width:', colour=Colors.TQDM.value, unit='zone'):
                index2=1
                vector_id = 1
                for prof in zne:
                    f.write(f'{index1}{sep}{vector_id}{sep}{index2}{sep}{width}' +'\n')
                    index2 += 1
                index1 += 1

    def write_top_file(self, crosses:list[list[profile]], save_as: str):
        """
        Write the topographic file (`.top`).

        :param crosses: List of cross sections
        :type crosses: list[list[profile]]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        """
        mycs = crosses
        sep = Constants.SEPARATOR.value
        topo_file = self.initialize_file(save_as, '.top')
        lgth = self.count_lists_in_list(mycs, True)

        with open(topo_file,'w') as f:
            f.write(f'{lgth}'+'\n')
            index1 = 1
            for zne in tqdm(mycs,desc='Writing topo:', colour=Colors.TQDM.value, unit='zone'):
                index2 = 1
                vector_id  = 1
                for prof in zne:
                    assert prof.banksbed_postype == postype.BY_VERTEX
                    value = prof.bed.z
                    f.write(f'{index1}{sep}{vector_id}{sep}{index2}{sep}{value}' + "\n")
                    index2 += 1
                index1 += 1

    def write_batch_simulations(self,
                         directory_of_executable:str,
                         simulations_path:list[str],
                         batch_name: str = 'batch_all_simuls',
                         wetdry:Literal['fixed', 'evolutive']='evolutive',
                         steady:Literal['no precomputation', 'precomputation', 'steady'] = 'precomputation',
                         executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                         ) -> str:
        """
        Write a bat file (`.bat`) for all simulations.
        A .bat file contains a small commmand used to call the executable and run the simulations.

        :param directory_of_executable: Directory of the executable
        :type directory_of_executable: str
        :param simulations_path: Simulations paths
        :type simulations_path: list[str]
        :param batch_name: Batch name, defaults to 'batch_all_simuls'
        :type batch_name: str, optional
        :param wetdry: Wetdry, defaults to 'evolutive'
        :type wetdry: Literal['fixed', 'evolutive'], optional
        :param steady: Steady, defaults to 'precomputation'
        :type steady: Literal['no precomputation', 'precomputation', 'steady'], optional
        :param executable_type: Executable type, defaults to 'wolfcli'
        :type executable_type: Literal['wolfcli', 'wolfclid'], optional
        :return: Batch file
        :rtype: str
        """
        # FIXME Execute parallel commands in cmd with .bat file, best option.
        directory_simulations = os.path.split(simulations_path[0])[0]
        batch_file = self.initialize_file(directory_simulations, f'{batch_name}.bat','')

        if wetdry == 'fixed':
            wtd = 0
        elif wetdry == 'evolutive':
            wtd= 1

        if steady== 'precomputation':
            std= 1
        elif steady == 'no precomputation':
            std = 0
        elif steady == 'steady':
            std=2

        path_directory = os.path.abspath(directory_of_executable)
        with open(batch_file,'w') as bat:
            # Important step: The first line below set the computers space (root directory),
            # useful when the simulation and the executable are in different folders.
            bat.write(f'{path_directory[:2]}\n')
            bat.write(f'cd "{path_directory}"\n')

            for simulation in simulations_path:
                path_simulation = os.path.abspath(simulation)

                for file in os.listdir(path_simulation):
                    generic_file_path = os.path.join(path_simulation,file)
                    extension = os.path.splitext(generic_file_path)[-1]
                    if os.path.isfile(generic_file_path):
                        if extension == '':
                            simulation_name = file
                # # bat.write(f'cd "{path_directory}"\n') # Added
                bat.write(f'{executable_type} run_wolf1d dirin="{path_simulation}" in="{simulation_name}" wetdry={wtd} steady={std}\n')

        return batch_file

    def write_batch_file(self,
                         directory_of_executable:str,
                         directory_simulation:str,
                         simulation_name:str,
                         wetdry:Literal['fixed', 'evolutive']='evolutive',
                         steady:Literal['no precomputation', 'precomputation', 'steady'] = 'precomputation',
                         executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                         different_names=False,
                         new_name:str =''
                         ) -> str:
        """
        Write a batch file (.bat file).
        A .bat file contains a small commmand used to call the executable and run the simulations.

        :param directory_of_executable: Directory of the executable
        :type directory_of_executable: str
        :param directory_simulation: Directory of the simulation
        :type directory_simulation: str
        :param simulation_name: Simulation name
        :type simulation_name: str
        :param wetdry: Wetdry, defaults to 'evolutive'
        :type wetdry: Literal['fixed', 'evolutive'], optional
        :param steady: Steady, defaults to 'precomputation
        :type steady: Literal['no precomputation', 'precomputation', 'steady'], optional
        :param executable_type: Executable type, defaults to 'wolfcli'
        :type executable_type: Literal['wolfcli', 'wolfclid'], optional
        :param different_names: Different names, defaults to False
        :type different_names: bool, optional
        :param new_name: New name, defaults to ''
        :type new_name: str, optional
        :return: Batch file
        :rtype: str
        """
        # batch_file = self.initialize_file(directory_simulation,)
        if different_names:
            batch_file =self.initialize_file(directory_simulation, f'{new_name}.bat','') # To avoid simul name FIXME make it clean
        else:
            batch_file =self.initialize_file(directory_simulation, f'{simulation_name}.bat', directory_name='')

        if wetdry == 'fixed':
            wtd = 0
        elif wetdry == 'evolutive':
            wtd= 1

        if steady== 'precomputation':
            std= 1
        elif steady == 'no precomputation':
            std = 0
        elif steady == 'steady':
            std=2

        find_full_path ='%~dp0'
        path_directory = os.path.abspath(directory_of_executable)
        path_simulation = os.path.abspath(directory_simulation)

        for file in os.listdir(directory_simulation):
            generic_file_path = os.path.join(directory_simulation,file)
            extension = os.path.splitext(generic_file_path)[-1]
            if os.path.isfile(generic_file_path):
                if extension == '':
                    simulation_name = file
        with open(batch_file,'w') as bat:
            bat.write(f'{path_directory[:2]}\n')
            bat.write(f'cd "{path_directory}"\n')
            bat.write(f'{executable_type} run_wolf1d dirin="{path_simulation}" in="{simulation_name}" wetdry={wtd} steady={std}')

        return batch_file

    def run_bat_files(self, batch_file:str, communicate=False):
        """
        Run the .bat file in a windows shell
        to start the computations (simulation).

        :param batch_file: Batch file
        :type batch_file: str
        :param communicate: Communicate, defaults to False
        :type communicate: bool, optional
        """
        splitted_path = os.path.split(batch_file)
        directory = splitted_path[0]
        command = f'start cmd.exe /k "{batch_file}"'
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        if self.wx_exists:
            logging.info(f'{directory} Check the new shell window.\nThe simulation is running...')
        else:
            logging.warn(f'{directory} Check the new shell window.\nThe simulation is running...')

    def _run_batch_file(self, batch_file:str, communicate=False):
        """
        Run the .bat file in a windows shell
        to start the computations (simulation).

        :param batch_file: Batch file
        :type batch_file: str
        :param communicate: Communicate, defaults to False
        :type communicate: bool, optional
        FIXME Deprecated.
        """

        splitted_path = os.path.split(batch_file)
        directory = splitted_path[0]
        # simulation_name = splitted_path[1]
        logging.warn(f'{directory} running... \nThe process may take time.')
        # The working directory has to be specified otherwise it does not work.
        directory = os.path.split(batch_file)[0]

        run = Popen(batch_file, stdin=PIPE,stdout=PIPE,stderr=PIPE,cwd=directory)

        # run = Popen(batch_file, stdin=PIPE,stdout=PIPE,stderr=PIPE, close_fds=True)
        # run = Popen(batch_file, stdin=None,stdout=None,stderr=None, close_fds=True)
        # output, err = run.communicate()
        # run.returncode
        # run = Popen(batch_file,stdout=sys.stdout)
        if communicate:
            while True:
                l =run.stdout.readline()
                if not l:
                    break
            print(l)
        else:
            output, err = run.communicate()
        logging.warn(f'{directory} completed.')
        run.returncode

    def run_batch_file_multiprocess(batch_file:str, communicate=False):
        """
        Run the .bat file in a windows shell
        to start the computations (simulation).

        FIXME still not working.
        .. note:: Find a way to implement it.

        :param batch_file: Batch file
        :type batch_file: str
        :param communicate: Communicate, defaults to False
        :type communicate: bool, optional
        """
        run = Popen(batch_file, stdin=PIPE,stdout=PIPE,stderr=PIPE)
        # output, err = run.communicate()
        # run.returncode
        # run = Popen(batch_file,stdout=sys.stdout)
        if communicate:
            while True:
                l =run.stdout.readline()
                if not l:
                    break
            print(l)
        else:
            output, err = run.communicate()
        run.returncode

    def _run_batch_file(self, batch_file:str):
        """
        Run the .bat file in a windows shell
        to start the computations (simulation).

        :param batch_file: Batch file
        :type batch_file: str
        """
        # find_full_path ='%~dp0'
        run = Popen(batch_file, stdin=PIPE,stdout=PIPE,stderr=PIPE)
        # output, err = run.communicate()
        while True:
            l =run.stdout.readline()
            if not l:
                break
            print(l)
        run.returncode
        # subprocess.call(f'{batch_file}', shell=True)

    def run_everything(self, batch_file):
        """
        Run the .bat file in a windows shell
        to start the computations (simulation).

        :param batch_file: Batch file
        :type batch_file: str
        """
        all_runs = [Popen(batch_file, stdin=PIPE,stdout=PIPE,stderr=PIPE) for i in range(5)]

        for i in range(5):
            while True:
                l =all_runs[i].stdout.readline()
                if not l:
                    all_runs[i] = all_runs[i].returncode
                    break
                print(l)

    def _run_bat_files(self, bat_file, force_cwd = False, initial_condition = False):
        """
        Run the .bat file in a windows shell
        to start the computations (simulation).

        :param batch_file: Batch file
        :type batch_file: str
        :param force_cwd: Force current working directory, defaults to False
        :type force_cwd: bool, optional
        """
        splitted_path = os.path.split(bat_file)
        directory = splitted_path[0]
        simulation_name = splitted_path[1]
        if initial_condition:
            if self.wx_exists:
                logging.info(f'{simulation_name} running... \nComputing initial conditions.')
            else:
                logging.warn(f'{simulation_name} running... \nComputing initial conditions.')
        else:
            logging.warn(f'{simulation_name} running... \nThe process may take time.')

        if force_cwd:
            directory = os.path.split(bat_file)[0]
            run = subprocess.run(bat_file, shell=True, capture_output= True, text=True,cwd=directory )
        else:
            run = subprocess.run(bat_file, shell=True, capture_output= True, text=True)
        logging.warn(f'{simulation_name} completed.')

        if self.wx_exists:
            logging.info(run.stdout)
        else:
            print(run.stdout)
        # while  True:
        #     l = run.stdout
        #     if not l:
        #         break

    def write_help_file(self, save_as: str) -> None:
        """
        Write the help file.
        Contains the list of mandatory and optional files to create a 1D model.

        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional

        .. todo: FIXME implement a test before launching the model based on this list.
        """
        help_file = self.initialize_file(save_as,'.help')
        sep = Constants.SEPARATOR.value
        with open(help_file, 'w') as f:
            f.write(f'Mandatory files' + '\n')
            f.write(f'***************' + '\n' +'\n')
            f.write(f'Geometry :' + '\n')
            f.write(f'  - Skeleton	.vecz'+ '\n')
            f.write(f'  - Cross sections'+ '\n')
            f.write(f'          1° rectangular	.width'+ '\n')
            f.write(f'          2° real (tabulated values)	.gtv    	.ptv'+ '\n')
            f.write(f'Initial conditions :'+'\n')
            f.write(f'  - discharge	.qini  '+'\n')
            f.write(f'  - one or several files of (read one after one with substitution)'+'\n')
            f.write(f'          1° wet area	.aini '+'\n')
            f.write(f'          2° waterdepth	.hini '+'\n')
            f.write(f'          3° waterlevel	.zini  '+'\n')
            f.write(f'Boundary conditions	.cl'+'\n')
            f.write(f'Roughness	.rough '+'\n'+'\n')
            f.write(f'Optional files'+'\n')
            f.write(f'**************'+'\n')
            f.write(f'Infiltration zones	.infil  	.inf'+'\n')
            f.write(f'Convergence borders	.cvg'+'\n')
            f.write(f'If not correctly defined by skeleton :'+'\n')
            f.write(f'  - Topography (segment)	.top'+'\n')
            f.write(f'  - Lengths (segment)	.lengths'+'\n')
            f.write(f'Parameters of the computation (only those different from default values)	.param'+'\n')

    def remove_directory(self,directory:str) -> None:
        """
        Delete a directory (folder).

        :param directory: Directory  path
        :type directory: str
        """
        shutil.rmtree(directory)
        logging.info(f'{directory} removed.')

    def find_1D_binary_results(self, directory:str) -> tuple[str]:  #FIXME find why self is not working
        r"""
        /!\ This method has been deprecated.
        Return a tuple containing the paths to the model:

            - Head file (binary file containing the necessary
              information to interpret the results
              -> number of time steps, coordinates, simulated times, real times);
            - Depth file (binary file containing the computed depths at each time step);
            - Discharge file (binary file containing the computed discharges at each time step);
            - Wetted sections file (binary file containing the wetted sections for each time step).

        :param directory: Directory
        :type directory: str
        :return: Paths to the model
        :rtype: tuple[str]

        """
        for file in os.listdir(directory):
            if file.endswith(".HEAD"):
                head_file = os.path.join(directory,file)
            elif file.endswith(".RH"):
                results_depths = os.path.join(directory,file)
            elif file.endswith(".RQ"):
                results_discharges = os.path.join(directory,file)
            elif file.endswith(".RA"):
                results_wetted_sections = os.path.join(directory,file)

        return (head_file,results_depths, results_discharges, results_wetted_sections)

    def read_1D_binary_results(self, results: list[str]) -> tuple[np.ndarray]:
        r'''
        /!\ This method has been deprecated. Check the the class` Wolfresults_1D` for the new implementation.
        Return a tuple containing the simulated results as numpy arrays in this order:
            - 0. Nodes coordinates (np.ndarray),
            - 1. Water depths (np.ndarray),
            - 2. Discharges (np.ndarray),
            - 3. Wetted sections (np.ndarray),
            - 5. real times
            - 6. Simulated times
        '''
        path_head = results[0]
        path_depths = results[1]
        path_discharges = results[2]
        path_wetted_sections = results[3]
        file_size = os.path.getsize(path_head) # size of head file in bytes

        with open (path_head,"rb") as head_binary:
            # Necessary informations to extract coordinates
            head_in_bytes = head_binary.read()
            cells_number = np.frombuffer(head_in_bytes, dtype=np.int32, count=1)[0]
            nb_coordinates_data = 3 * cells_number
            time_steps_number = (file_size - 4 - (4 * nb_coordinates_data))/8
            assert (time_steps_number).is_integer(),\
                f'The number of results is not an integer {time_steps_number}'
            results_number = int(time_steps_number)

            # Extraction of cell coordinates
            head_data = np.frombuffer(head_in_bytes, dtype= np.float32)
            coordinates = head_data[1 :  nb_coordinates_data + 1].reshape(cells_number,3)
            coordinates = np.roll(coordinates, 1, axis= 0)
            # coordinates: [0] == z | [1] == Y | [2] == X
            coordinates = np.flip(coordinates, axis=1)

            # Extraction of time steps
            all_times = head_data[nb_coordinates_data + 1::]
            simulated_times = all_times[1::2]
            real_times = all_times[::2]
            # print(real_times)

        # Extration of computed depths
        with open(path_depths,"rb") as depths_binary:
            depths_in_bytes = depths_binary.read()
            depths_data = np.frombuffer(depths_in_bytes, dtype= np.float32)
            depths = depths_data.reshape(cells_number, results_number, order='F') # The file is in fortran convention
            depths = np.roll(depths, 1, axis=0)

        # Extraction of computed discharges
        with open(path_discharges,"rb") as discharges_binary:
            discharges_in_bytes = discharges_binary.read()
            discharges_data = np.frombuffer(discharges_in_bytes, dtype= np.float32)
            discharges = discharges_data.reshape(cells_number, results_number, order='F') # The file is in fortran convention
            discharges = np.roll(discharges, 1, axis=0)

        # Extraction of computed wetted sections
        with open(path_wetted_sections,"rb") as wetted_sections_binary:
            wetted_sections_in_bytes = wetted_sections_binary.read()
            wetted_sections_data = np.frombuffer(wetted_sections_in_bytes, dtype= np.float32)
            wetted_sections = wetted_sections_data.reshape(cells_number, results_number, order='F') # The file is in fortran convention
            wetted_sections = np.roll(wetted_sections, 1, axis=0)




        return (coordinates, depths, discharges, wetted_sections, real_times, simulated_times)

    def plot_1D_results(self, results:tuple[np.ndarray],
                        save_as:str ='',
                        figure_size = (20,10),
                        first_time_step= 1,
                        animations = True,
                        max_ylimits= (0.9, 0.9, 2.5, 1.5, 1, 1),
                        landmark:Zones = None,
                        banks: Zones = None,
                        dpi: float = Constants.DPI.value ) -> None:
        r"""
        /!\ This method has been deprecated. Check the the class` Wolfresults_1D` for the new implementation.
        Plot the results of 1D model either:
            - as a gif  (evolution of all parameters)
            Starting from a particular time step (firt_time_step) or,
            - As a picture (only the first time step).

        @ The counting of time steps starts from 1,
        and negative counting (from the back) works too.

        @ In case a bad time steps is passed, the last time step will be plotted.

        @ max_ylimits allows the resizing of the maximum y limits of each of the 4 plots respectively.
            - For instance, the maximum ylim for discharges (third plot) =
            max(discharges) + (2.5 * max(discharges))

        :param results: Results
        :type results: tuple[np.ndarray]
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param figure_size: Figure size, defaults to (20,10)
        :type figure_size: tuple, optional
        :param first_time_step: First time step, defaults to 1
        :type first_time_step: int, optional
        :param animations: Animations, defaults to True
        :type animations: bool, optional
        :param max_ylimits: Maximum y limits, defaults to (0.9, 0.9, 2.5, 1.5, 1, 1)
        :type max_ylimits: tuple, optional
        :param landmark: Landmark, defaults to None
        :type landmark: Zones, optional
        :param banks: Banks, defaults to None
        :type banks: Zones, optional
        :param dpi: Dpi, defaults to Constants.DPI.value
        :type dpi: float, optional
        """
        # Splitting and naming the results
        coordinates = results[0]
        depths = results[1]
        discharges = results[2]
        wetted_sections = results[3]
        real_times = results[4]
        simulated_times = results[5]
        # x_axis = coordinates[:,2]
        topo = coordinates[:,0]
        coords = coordinates[-1]

        # Froude computations
        velocities = discharges/wetted_sections
        g = Constants.GRAVITATION.value
        froudes = velocities/np.sqrt(g*depths)



        #wolf vector file
        def vector_from_coordinates(coords: np.ndarray) -> vector:
            vector_coords = vector(is2D=False)
            for node in coordinates:
                vert = wolfvertex(node[2], node[1], node[0])
                vector_coords.add_vertex(vert)

            vector_coords.find_minmax()
            return vector_coords

        vector_coords = vector_from_coordinates(coords)
        s_topo,z_topo= vector_coords.get_sz()

        x_axis = s_topo
        # topo = z_topo

        left_bank = banks.myzones[0].myvectors[0]
        bed_bank = banks.myzones[0].myvectors[1]
        right_bank = banks.myzones[0].myvectors[2]

        lsg = vector_coords.asshapely_ls()
        left_curvi = [lsg.project(Point(vert.x,vert.y)) for vert in left_bank.myvertices]
        right_curvi = [lsg.project(Point(vert.x,vert.y)) for vert in right_bank.myvertices]
        bed_curvi = [lsg.project(Point(vert.x,vert.y)) for vert in bed_bank.myvertices]
        bottom_curvi = [lsg.project(Point(vert.x, vert.y)) for vert in vector_coords.myvertices]

        s_left, z_left = left_bank.get_sz()
        s_right, z_right = right_bank.get_sz()
        s_bed, z_bed = bed_bank.get_sz()
        # x_axis = bottom_curvi

        # x_axis = s_bed[1:]



        # Plotting bank lines

        # vector_banks = vector_from_coordinates(banks)
        # vector_el

        # Testing the given first time step
        if first_time_step < 0 and (-first_time_step) <= depths.shape[1]:
            first_timestep = depths.shape[1] + first_time_step
        elif first_time_step > 0 and first_time_step <= depths.shape[1]:
            first_timestep= first_time_step - 1 # Python counts from 0.
        else:
            first_timestep = depths.shape[1] - 1
            warnings.warn(f'The input first_time_step was not found, therefore, the last time step is plotted.', UserWarning)

        # Creation of figure
        fig = plt.figure(figsize=figure_size, facecolor='white')
        # fig.suptitle('Results - 1D model\n', fontsize= 'x-large', fontweight= 'bold')
        fig.suptitle(f'Results - 1D model\n$Time: (step: {first_timestep + 1} - $simulated: {simulated_times[first_timestep]:#.1f}s$ - real: {real_times[first_timestep]:#.1e} s)$',
                      fontsize= 'x-large', fontweight= 'bold')

        # Axes
        # Water level
        ax1 = fig.add_subplot(234)
        ax1.plot(x_axis,  topo, color= 'black')
        water_level, = ax1.plot(x_axis,  (topo+ depths[:,first_timestep]), color= 'cyan', ls='-.')
        ax1.fill_between(x_axis, topo, (topo+ depths[:,first_timestep]), where = topo <= (topo+ depths[:,first_timestep]),\
                          color ='cyan', alpha =0.3, interpolate=True, label = 'Water level')
        ax1.fill_between(x_axis, topo, y2= min(topo), color = 'black', alpha = 0.2, label = 'Bed',interpolate=True)
        ax1.set_xlim(min(x_axis), max(x_axis))
        ax1.set_ylim(min(topo), max(topo+ depths[:,first_timestep]) + max_ylimits[0]* max(topo+ depths[:,first_timestep]))
        ax1.set_ylabel('Altitude [m]')
        ax1.set_xlabel('Length [m]')
        ax1.grid()
        ax1.set_title(f'Water level', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        # ax1.set_title(f'Water level: Time step - {first_timestep + 1}', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        # ax1.set_title(f'Water level - Time: (simulated:{simulated_times[first_timestep]:#.1f}s - real: {real_times[first_timestep]:#.1f}s)',
                    #    fontdict={'fontsize': 'large', 'fontweight':'bold'})

        # Water depth
        ax2 = fig.add_subplot(231)
        water_depth, = ax2.plot(x_axis, depths[:,first_timestep], color= 'cyan', ls='-.')
        ax2.fill_between(x_axis, depths[:,first_timestep], color ='cyan', alpha =0.3, interpolate=True, label = 'Water depth')
        ax2.set_xlim(min(x_axis), max(x_axis))
        ax2.set_ylim(0, max(depths[:,first_timestep]) + max_ylimits[1]* max(depths[:,first_timestep]))
        ax2.set_ylabel('Depth [m]')
        ax2.set_xlabel('Length [m]')
        ax2.grid()
        ax2.set_title(f'Water depth', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        # ax2.set_title(f'Water depth: Time step - {first_timestep + 1}', fontdict={'fontsize': 'large', 'fontweight':'bold'})

        # Discharges
        ax3 = fig.add_subplot(235)
        discharge, = ax3.plot(x_axis, discharges[:,first_timestep], color= 'red', ls='-.')
        ax3.fill_between(x_axis, discharges[:,first_timestep], color ='red', alpha =0.3, interpolate=True, label = 'Discharge')
        ax3.set_xlim(min(x_axis), max(x_axis))
        ax3.set_ylim(0, max(discharges[:,first_timestep]) + max_ylimits[2]* max(discharges[:,first_timestep]))
        ax3.set_ylabel('Discharge [$m^3/s$]')
        ax3.set_xlabel('Length [m]')
        ax3.grid()
        ax3.set_title(f'Discharge', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        # ax3.set_title(f'Discharge: Time step - {first_timestep + 1}', fontdict={'fontsize': 'large', 'fontweight':'bold'})

        # Wetted sections
        ax4 = fig.add_subplot(236)
        wetted_section, = ax4.plot(x_axis, wetted_sections[:,first_timestep], color= 'blue', ls='-.')
        ax4.fill_between(x_axis, wetted_sections[:,first_timestep], color ='blue', alpha =0.3, interpolate=True, label = 'Wetted sections')
        ax4.set_xlim(min(x_axis), max(x_axis))
        ax4.set_ylim(0, max(wetted_sections[:,first_timestep]) + max_ylimits[3]* max(wetted_sections[:,first_timestep]))
        ax4.set_ylabel('Wetted sections [$m^2$]')
        ax4.set_xlabel('Length [m]')
        ax4.grid()
        ax4.set_title(f'Wetted sections', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        # ax4.set_title(f'Wetted sections: Time step - {first_timestep + 1}', fontdict={'fontsize': 'large', 'fontweight':'bold'})

        # Froude number
        ax5 = fig.add_subplot(233)
        froude, = ax5.plot(x_axis, froudes[:,first_timestep], color= 'blue', ls='-.')
        ax5.fill_between(x_axis, froudes[:,first_timestep], color ='blue', alpha =0.3, interpolate=True, label = 'Froude numbers')
        ax5.set_xlim(min(x_axis), max(x_axis))
        ax5.set_ylim(0, max(froudes[:,first_timestep]) + max_ylimits[4]* max(froudes[:,first_timestep]))
        ax5.set_ylabel('Froude number')
        ax5.set_xlabel('Length [m]')
        ax5.grid()
        ax5.set_title(f'Froude numbers', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        # ax5.set_title(f'Wetted sections: Time step - {first_timestep + 1}', fontdict={'fontsize': 'large', 'fontweight':'bold'})

         # Velocities
        ax6 = fig.add_subplot(232)
        velocity, = ax6.plot(x_axis, velocities[:,first_timestep], color= 'red', ls='-.')
        ax6.fill_between(x_axis, velocities[:,first_timestep], color ='red', alpha =0.3, interpolate=True, label = 'Velocities')
        ax6.set_xlim(min(x_axis), max(x_axis))
        ax6.set_ylim(0, max(velocities[:,first_timestep]) + max_ylimits[5] * max(velocities[:,first_timestep]))
        ax6.set_ylabel('Velocities [m/s]')
        ax6.set_xlabel('Length [m]')
        ax6.grid()
        ax6.set_title(f'Velocities [m/s]', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        # ax5.set_title(f'Wetted sections: Time step - {first_timestep + 1}', fontdict={'fontsize': 'large', 'fontweight':'bold'})


        # print(left_curvi)



        # def _project_vector(banks:Zones):
        #     left_bank = banks.myzones[0].myvectors[0]
        #     bed_bank = banks.myzones[0].myvectors[1]
        #     right_bank = banks.myzones[0].myvectors[0]
        #     lsg = vector_coords.asshapely_ls()
        #     left_curvi = [lsg.project(Point(vert.x,vert.y)) for vert in left_bank.myvertices]
        #     left_bank_x = []

        #     # for vert in left_bank.myvertices:
        #     #     lsg.project(Point(vert.x,vert.y))


        def _landmark(landmark,index, texts = True):
            # landmark: Zones

            landmark_names = [curvec.myname for curvec in landmark.myzones[0].myvectors]
            lsg = vector_coords.asshapely_ls()
            curvi_landmarks =[lsg.project(Point((vect.myvertices[0].x + vect.myvertices[1].x)/2.,
                                               (vect.myvertices[0].y + vect.myvertices[1].y)/2.))
                                               for vect in landmark.myzones[0].myvectors]

            alpha = 0.7
            for s_landmark, name_landmark in zip(curvi_landmarks, landmark_names):
                if texts:
                    ax1.text(s_landmark, max(topo),name_landmark, rotation=30, alpha =alpha)
                    ax2.text(s_landmark, (0.8 *max_ylimits[1]*max(depths[:,index])),name_landmark, rotation=30, alpha =alpha)
                    ax3.text(s_landmark, (0.8 *max_ylimits[2]*max(discharges[:,index])),name_landmark, rotation=30, alpha =alpha)
                    ax4.text(s_landmark, (0.8 *max_ylimits[3]*max(wetted_sections[:,index])),name_landmark, rotation=30, alpha =alpha)
                    ax5.text(s_landmark, (0.8 *max_ylimits[4]*max(froudes[:,index])),name_landmark, rotation=30, alpha =alpha)
                    ax6.text(s_landmark, (0.8 *max_ylimits[5]*max(velocities[:,index])),name_landmark, rotation=30, alpha =alpha)

                ax1.vlines(s_landmark, min(topo), max(topo), color='black', linestyles='--', alpha =alpha)
                ax2.vlines(s_landmark, 0, (0.8 *max_ylimits[1]*max(depths[:,index])), color='black', linestyles='--', alpha =alpha)
                ax3.vlines(s_landmark, 0, (0.8 *max_ylimits[2]*max(discharges[:,index])), color='black', linestyles='--', alpha =alpha)
                ax4.vlines(s_landmark, 0,(0.8 *max_ylimits[3]* max(wetted_sections[:,index])), color='black', linestyles='--', alpha =alpha)
                ax5.vlines(s_landmark, 0, (0.8 *max_ylimits[4]* max(froudes[:,index])), color='black', linestyles='--', alpha =alpha)
                ax6.vlines(s_landmark, 0, (0.8 *max_ylimits[5]* max(velocities[:,index])), color='black', linestyles='--', alpha =alpha)

        if landmark != None:
            _landmark(landmark, first_time_step)

        if banks != None:
            # bank_left = banks.myzones[0].myvectors[0]
            # bank_bed = banks.myzones[0].myvectors[1]
            # bank_right = banks.myzones[0].myvectors[2]
            # s_left, z_left = bank_left.get_sz()
            # s_right, z_right = bank_right.get_sz()
            # s_bed, z_bed = bank_bed.get_sz()
            # ax1.plot(s_left,  z_left, color= 'green', ls ='--', label = 'Left bank', alpha = 0.2)
            # ax1.plot(s_right,  z_right, color= 'blue', ls ='--', label = 'Right bank', alpha = 0.2)
            banks_alpha =0.3
            ax1.plot(left_curvi,  z_left, color= 'green', ls ='--', label = 'Left bank', alpha = banks_alpha)
            ax1.plot(right_curvi,  z_right, color= 'blue', ls ='--', label = 'Right bank', alpha = banks_alpha)
            # FIXME the lengths are different.
            # ax2.plot(s_right,  z_right - z_bed, color= 'blue', ls ='--', label = 'Right bank', alpha = banks_alpha)
            # ax2.plot(s_left,  z_left - z_bed, color= 'green', ls ='--', label = 'Left bank', alpha = banks_alpha)



        # Legends
        ax1.legend()
        ax2.legend()
        ax3.legend()
        ax4.legend()
        ax5.legend()
        ax6.legend()



        def _animated1D_plots(i):
            '''
            Animation of results for gif file.
            '''
            index = i+ first_timestep
            wl = topo + depths[:, index] # Water level
            h = depths[:, index] # Water depth
            q = discharges[:, index] # Discharge
            a = wetted_sections[:, index]  # Wetted sections

            v = q/a
            fr = v/np.sqrt(g*h)

            # Setting the data
            water_level.set_data(x_axis, wl)
            water_depth.set_data(x_axis, h)
            discharge.set_data(x_axis, q)
            wetted_section.set_data(x_axis, a)
            velocity.set_data(x_axis, v)
            froude.set_data(x_axis, fr)

            # Cleaning  the axes and  and new drawings
            ax1.collections.clear()
            ax1.fill_between(x_axis, topo, wl, where= topo <= wl,facecolor='cyan',alpha=0.3,interpolate=True)
            ax1.fill_between(x_axis, topo, y2= min(topo), color = 'black', label = 'topo',  alpha = 0.3)

            ax2.collections.clear()
            ax2.fill_between(x_axis, h, facecolor='cyan',alpha=0.3,interpolate=True)

            ax3.collections.clear()
            ax3.fill_between(x_axis, q, facecolor='red',alpha=0.3,interpolate=True)

            ax4.collections.clear()
            ax4.fill_between(x_axis, a, facecolor='blue',alpha=0.3,interpolate=True)

            ax5.collections.clear()
            ax5.fill_between(x_axis, fr, facecolor='blue',alpha=0.3,interpolate=True)

            ax6.collections.clear()
            ax6.fill_between(x_axis, v, facecolor='red',alpha=0.3,interpolate=True)

            # ax1.set_title(f'Water level: Time step - {i + 1 + first_timestep}', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            # ax2.set_title(f'Water depth: Time step - {i + 1 + first_timestep}', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            # ax3.set_title(f'Discharge: Time step - {i + 1 + first_timestep}', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            # ax4.set_title(f'Wetted sections:Time step - {i + 1 + first_timestep}', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            fig.suptitle(f'Results - 1D model\n$Time: (step: {index} - $simulated: {simulated_times[index-1]:#.1f}s$ - real: {real_times[index-1]:#.1e} s)$',
                      fontsize= 'x-large', fontweight= 'bold')
            if landmark != None:
                _landmark(landmark, first_time_step, texts=False)


        # Gif Outputs
        if animations:
            rcParams['animation.embed_limit'] = 2**128 # Final size
            ani = animation.FuncAnimation(
                                    fig,
                                    _animated1D_plots,
                                    interval = 200,
                                    blit = False,
                                    frames = depths.shape[1] - first_timestep,
                                    repeat_delay = 100)

            if save_as != '':
                writergif = animation.PillowWriter(fps=5)
                ani.save(save_as, writer=writergif, dpi = dpi)

            return HTML(ani.to_jshtml())
        # Picture as output
        else:
            if save_as !='':
                # plt.savefig(save_as, dpi= dpi)
                plt.savefig(save_as, dpi= dpi)
            plt.show()

    def plot_hydrograph_nodes(self,
                              results:tuple[np.ndarray],
                              which_nodes:list[int] = [0,-1],
                              save_as:str ='',
                              figure_size = (20,10)):
        r"""
        /!\ This method has been deprecated. Check the the class` Wolfresults_1D` for the new implementation.

        Plot the hydrographs of the nodes.

        :param results: Results
        :type results: tuple[np.ndarray]
        :param which_nodes: Which nodes, defaults to [0,-1]
        :type which_nodes: list[int], optional
        :param save_as: File path of the new cross section, defaults to ''
        :type save_as: str, optional
        :param figure_size: Figure size, defaults to (20,10)
        :type figure_size: tuple, optional
        """

        discharges = results[2]
        times = results[-1] # 15 min

        n = discharges.shape[0]
        lgth = times.shape[0]

        # Creation of the figure
        fig = plt.figure(figsize=figure_size, facecolor='white')

        # Axes (2 graphs)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)

        # List of information necessary for the axes property
        min_discharges = []
        max_discharges = []
        max_times = []
        id_cells =[]

        # Refactorisation of the entry (positive or negative)
        for i in which_nodes:
            if i > 0:
                id_cell = i
                id = i - 1
            elif i < 0:
                id_cell = n + i + 1
                id = i
            elif i == 0:
                id_cell = i + 1
                id = i

            # collecting the curve properties for the Axes
            min_discharges.append(np.amin(discharges[id,:]))
            max_discharges.append(np.amax(discharges[id,:]))
            discharge_max = np.argmax(discharges[id,:])
            max_times.append(times[discharge_max])
            id_cells.append(id_cell)
            # Plots
            ax1.plot(times, discharges[id,:], label=f'Node- {id_cell}')
            ax2.plot((times - times[discharge_max]), discharges[id,:], label=f'Node- {id_cell}')

        # Properties first axis
        ax1.set_xlim(np.min(times),np.max(times))
        ax1.set_ylim(min(min_discharges), (max(max_discharges) + 0.1*max(max_discharges)))
        ax1.set_ylabel('Discharge [$m^3$]', fontsize= 'x-large')
        ax1.set_xlabel('Simulated times [$s$]', fontsize= 'x-large')
        ax1.legend()
        ax1.xaxis.set_ticks(np.arange(min(times),max(times),900))
        ax1.grid()

        # Properties second axis
        tmax = np.max(times) - np.min(times)
        ax2.set_xlim((-tmax/2),(tmax/2))
        ax2.text(-tmax/2,
                 max(max_discharges) + 0.05* max(max_discharges),
                 f'$Phase-shift: {max_times[0]-max_times[-1]:#.2f}s$', fontsize =14)
        ax2.set_ylim(min(min_discharges), (max(max_discharges) + 0.1*max(max_discharges)))
        ax2.set_xlabel('Time from maximum [s]', fontsize= 'x-large')
        ax2.legend()
        # ax2.xaxis.set_ticks(np.arange((-tmax/2),(tmax/2),900))
        ax2.grid()

        # figure title, save and display parameters
        fig.suptitle(f'Hydrographs nodes - {id_cells}', fontsize= 'x-large', fontweight= 'bold')
        if save_as != '':
            fig.savefig(save_as, dpi =300)
        plt.show()

    def write_simulation_files_from_crosssections(self,
                                                folder_path:str,
                                                cross_sections: crosssections,
                                                parallels: Zones,
                                                banks: Zones,
                                                boundary_conditions: dict,
                                                roughness:Union[float,WolfArray],
                                                hydrographs: list[list[list]],
                                                exe_file:str,
                                                topography: WolfArray = None,
                                                initial_discharge:float = None,
                                                simulation_name:str = 'simul',
                                                discretisation:float = 10.,
                                                extrapolation_of_extremities:float = 100.,
                                                initial_depth:float = 1.,
                                                write_in: Literal['iterations', 'times'] = 'times',
                                                output_frequency:int = 900,
                                                polygon_number:int = 1,
                                                code_verbosity_profile: list = [1],
                                                simulation_time:int = None,
                                                roughness_option: Literal['under_profile', 'under_polygons']= 'under_profile',
                                                roughness_selection:Literal['min','mean','median','max'] = 'mean',
                                                file_type_initial_cond: Literal['.aini','.hini','.zini'] = '.aini',
                                                infiltration_profiles:list =['1'],
                                                wetdry:Literal['fixed', 'evolutive']='evolutive',
                                                steady:Literal['no precomputation', 'precomputation', 'steady'] = 'precomputation',
                                                executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                                                run_simulation: Literal['yes', 'no'] = 'no',
                                                writing_type_infiltration: Literal['continuous', 'stepwise'] = 'continuous',
                                                epsilon_infiltration:float = 0.01,
                                                new_directory = '',
                                                force_steady = True
                                                ) -> tuple:
        """
        Write the simulation files (the 1D model) from the cross sections and the other parameters with one line of code.

        :param folder_path: Folder path
        :type folder_path: str
        :param cross_sections: Cross sections
        :type cross_sections: crosssections
        :param parallels: Parallels
        :type parallels: Zones
        :param banks: Banks
        :type banks: Zones
        :param boundary_conditions: Boundary conditions
        :type boundary_conditions: dict
        :param roughness: Roughness
        :type roughness: Union[float,WolfArray]
        :param hydrographs: Hydrographs
        :type hydrographs: list[list[list]]
        :param exe_file: Exe file
        :type exe_file: str
        :param topography: Topography, defaults to None
        :type topography: WolfArray, optional
        :param initial_discharge: Initial discharge, defaults to None
        :type initial_discharge: float, optional
        :param simulation_name: Simulation name, defaults to 'simul'
        :type simulation_name: str, optional
        :param discretisation: Discretisation, defaults to 10.
        :type discretisation: float, optional
        :param extrapolation_of_extremities: Extrapolation of extremities, defaults to 100.
        :type extrapolation_of_extremities: float, optional
        :param initial_depth: Initial depth, defaults to 1.
        :type initial_depth: float, optional
        :param write_in: Write in, defaults to 'times'
        :type write_in: Literal['iterations', 'times'], optional
        :param output_frequency: Output frequency, defaults to 900
        :type output_frequency: int, optional
        :param polygon_number: Polygon number, defaults to 1
        :type polygon_number: int, optional
        :param code_verbosity_profile: Code verbosity profile, defaults to [1]
        :type code_verbosity_profile: list, optional
        :param simulation_time: Simulation time, defaults to None
        :type simulation_time: int, optional
        :param roughness_option: Roughness option, defaults to 'under_profile'
        :type roughness_option: Literal['under_profile', 'under_polygons'], optional
        :param roughness_selection: Roughness selection, defaults to 'mean'
        :type roughness_selection: Literal['min','mean','median','max'], optional
        :param file_type_initial_cond: File type initial cond, defaults to '.aini'
        :type file_type_initial_cond: Literal['.aini','.hini','.zini'], optional
        :param infiltration_profiles: Infiltration profiles, defaults to ['1']
        :type infiltration_profiles: list, optional
        :param wetdry: Wetdry, defaults to 'evolutive'
        :type wetdry: Literal['fixed', 'evolutive'], optional
        :param steady: Steady, defaults to 'precomputation'
        :type steady: Literal['no precomputation', 'precomputation', 'steady'], optional
        :param executable_type: Executable type, defaults to 'wolfcli'
        :type executable_type: Literal['wolfcli', 'wolfclid'], optional
        :param run_simulation: Run simulation, defaults to 'no'
        :type run_simulation: Literal['yes', 'no'], optional
        :param writing_type_infiltration: Writing type infiltration, defaults to 'continuous'
        :type writing_type_infiltration: Literal['continuous', 'stepwise'], optional
        :param epsilon_infiltration: Epsilon infiltration, defaults to 0.01
        :type epsilon_infiltration: float, optional
        :param new_directory: New directory, defaults to ''
        :type new_directory: str, optional
        :param force_steady: Force steady, defaults to True
        :type force_steady: bool, optional
        :return: tuple
        :rtype: tuple
        """


        # Simulation directory (contains all simulation files)
        if new_directory != '':
            directory = new_directory
        else:
            directory = self.create_simulation_directory(folder_path,simulation_name)

        # The extremities of each profile is extrapolated to avoid negative water depths in case of high discharges
        extrapolated_cross_sections = self.extrapolate_extremities(cross_sections,
                                                                    extrapolation_of_extremities,
                                                                    directory)
        # The crossection are sorted based on the river bed (middle parallel)
        sorted_crosssections = self.sort_crossections_list([extrapolated_cross_sections], banks)
        #
        if simulation_time:
            time = simulation_time
        else:
            # FIXME Multiple hydrographs
            if isinstance(hydrographs,dict):
                times = []
                for hydro, prof in hydrographs.items():
                    if isinstance(prof, Hydrograph):
                        times.append(max(prof.index))
                    elif isinstance(prof, list):
                        latest_time = prof[0][-1]
                        times.append(latest_time)

                time = max(times)

            else:
                if isinstance(hydrographs[0], Hydrograph):
                    time = max(hydrographs[0].index)
                elif isinstance(hydrographs[0], list):
                    time = hydrographs[0][0][-1]

        if initial_discharge:
            q_ini = initial_discharge
        else:
            if isinstance(hydrographs,dict):
                discharges = []
                for hydro, prof in hydrographs.items():
                    if isinstance(prof, Hydrograph):
                        first_discharge = prof.values[0]
                        discharges.append(first_discharge)
                    elif isinstance(prof, list):
                        first_discharge = prof[0][0]
                        discharges.append(first_discharge)
                q_ini = min(discharges)
            else:
                if isinstance(hydrographs[0], Hydrograph):
                    q_ini = hydrographs[0].values[0]
                elif isinstance(hydrographs[0], list):
                    q_ini = hydrographs[0][1][0]

        # Bank file
        if banks.is2D:
            bank_file = self.get_values_from_array(banks, topography, directory + '\\banks.vecz')
        else:
            bank_file = banks
            bank_file.saveas(directory + '\\banks.vecz')


        # FIXME is it necessery  to have parallels (next round), is it only for cell size or a better used could be found?


        # Write the tabulated relations of each cross section (profile)
        write_relations = self.write_relations_profiles(sorted_crosssections, directory)

        # Write roughnesses
        if isinstance(roughness, float) or isinstance(roughness, int):
            roughnesses = self.roughness_from_value(sorted_crosssections,  value = roughness)

        elif isinstance(roughness, WolfArray):
            if roughness_option == 'under_profile':
                roughnesses = self.roughness_from_profiles(roughness, sorted_crosssections, mode=roughness_selection)

            elif roughness_option == 'under_polygons':
                # FIXME to be verified issue with the extent of profiles
                # (the number of new polygons is different from the number of digitized profiles)
                # May be a test should be implemented on each profiles (probable solution).
                if isinstance(parallels, Zones):
                    # Polygons
                    polygons = self.create_polygons(parallels, discretisation, polygon_number, directory)
                    roughnesses = self.roughness_from_polygons(roughness, polygons, mode=roughness_selection)

        roughness_file = self.write_roughnesses(roughnesses, directory)

        # Compute & write the intial conditions
        ic_relations, nb_updates = self.ic_relations_hspw(sorted_crosssections, initial_depth)

        # The simulation is initialized based on the wetted area (more practical)
        ini_files = self.write_ini_files(ic_relations,
                                            directory,
                                            q = q_ini,
                                            nb_updates= nb_updates,
                                            file_choice=[file_type_initial_cond])

        # Write the boundary conditions
        cl_file = self.write_cl_file(sorted_crosssections, boundary_conditions, directory)

        # Write .top file (topography)
        top_file = self.write_top_file(sorted_crosssections,directory)

        # Write the .vec file (discretization file of the simulation topography - lowest riverbed point)
        vec_file1 = self.write_vector_files(sorted_crosssections, save_as=directory,which_type='vecz')

        # Sets the predefined river banks and bed on each cross sections
        set_bank = self.set_banksbed_vectors(bank_file)

        # Write the .vec file (discretization file of the simulation topography - midriver)
        vec_file2 = self.write_vector_files(sorted_crosssections, save_as=directory, which_type='vec')

        # Write the generic file
        genfile = self.write_generic_file(directory)

        #-----------------------------------------------------------

        # Write the infiltrations
        if isinstance(hydrographs, dict):
            infil = self.write_infiltrations_from_dict(sorted_crosssections,
                                         hydrographs,
                                         directory,
                                         writing_type_infiltration,
                                         epsilon_infiltration)
        elif isinstance(hydrographs,list):
            infil = self.write_infiltrations(infiltration_profiles,
                                            sorted_crosssections,
                                            hydrographs,
                                            directory,
                                            writing_type_infiltration,
                                            epsilon_infiltration)



        # Update the distribution of initial discharges from the infiltrations
        self.update_qini_file_from_infiltration_dict(hydrographs, directory)

        # 22. Compute a steady state solution
        #---------------------------------------------------------------
        if steady == 'precomputation':
            # The first batch file is used to compute the steady state solution
            bat_file = self.write_batch_file(directory_of_executable = exe_file,
                                                directory_simulation= directory,
                                                simulation_name= simulation_name)
            self.start_from_steady_state(directory)
            batch_file = self.write_batch_file(directory_of_executable = exe_file,
                                           directory_simulation = directory,
                                           simulation_name = simulation_name,
                                           wetdry = wetdry,
                                           steady ='no precomputation',
                                           executable_type = executable_type)
        else:
            batch_file = self.write_batch_file(directory_of_executable = exe_file,
                                           directory_simulation = directory,
                                           simulation_name = simulation_name,
                                           wetdry = wetdry,
                                           steady = steady,
                                           executable_type = executable_type)

        #------------------------------

        # write the simulation parameters
        if write_in == 'times':
            write_type = 2
        elif write_in =='iterations':
            write_type = 1
        if self.wx_exists == None:
            param = self.write_parameters(directory, write_freq= output_frequency, write_type= write_type, max_time=time)


        if run_simulation == 'yes':
            # logging.warn(f'{simulation_name} running... \nThe process may take time.')
            self.run_bat_files(batch_file)
            # logging.warn(f'{simulation_name} completed.')
        return (directory,simulation_name, sorted_crosssections, ic_relations, nb_updates)

    def find_file_from_extension(self, directory:str, file_extension:str) -> str:
        """Return a file in a directory based on its extension.

        :param directory: file path to the folder
        :type directory: str
        :param file_extension: file extension
        :type file_extension: str
        :return: file path
        """
        for file in os.listdir(directory):
            if file.endswith(file_extension):
                return os.path.join(directory, file)

        raise Exception(f'No file with the extension {file_extension} was found in the directory {directory}.')

    def start_from_steady_state(self, directory:str, plot = True):
        """Compute the steady state solution and update the initial conditions based on the results.

        :param directory: directory (simulation folder)
        :type directory: str
        :param plot: wheter the process should open a matplotlib figure
        containing the steady state solution or not, defaults to True

        :type plot: bool, optional
        """
        self.write_parameters(directory, write_type= 2, max_time=0)
        bat_file = self.find_file_from_extension(directory, '.bat')
        self._run_bat_files(bat_file, initial_condition= True)
        # self.run_bat_files(bat_file)
        self.update_initial_conditions_from_results(directory, time_step=1, plot=plot)

    def update_initial_conditions_from_results(self,
                                               directory:str,
                                               time_step:int =1,
                                               plot:bool = True):
        results = Wolfresults_1D(directory)

        if plot:
            results.plot_variables(figures=['water level','discharge', 'froude','water depth','velocity','wetted section' ]
                                   ,time_step=time_step, grid_x_m= 1000)
            self.log_message('Proposed initial conditions plotted.')

        results.update_ic_from_time_steps(time_step)
        self.log_message('New initial conditions.')

    def log_message(self, message:str):
        """Message for the user.

        :param message: message
        :type message: str
        """
        if self.wx_exists:
            logging.info(message)
        else:
            print(message)

    def create_multiple_simulations_from_csv(self,
                                            csv_filename:str,
                                            folder_path:str,
                                            cross_sections: crosssections,
                                            parallels: Zones,
                                            banks: Zones,
                                            boundary_conditions: dict,
                                            roughness:Union[float,WolfArray],
                                            hydrographs: list[list[list]],
                                            exe_file:str,
                                            topography: WolfArray = None,
                                            initial_discharge:float = None,
                                            simulation_name:str = 'simul',
                                            discretisation:float = 10.,
                                            extrapolation_of_extremities:float = 100.,
                                            initial_depth:float = 1.,
                                            write_in: Literal['iterations', 'times'] = 'times',
                                            output_frequency:int = 900,
                                            polygon_number:int = 1,
                                            code_verbosity_profile: list = [1],
                                            simulation_time:int = None,
                                            roughness_option: Literal['under_profile', 'under_polygons']= 'under_profile',
                                            roughness_selection:Literal['min','mean','median','max'] = 'mean',
                                            file_type_initial_cond: Literal['.aini','.hini','.zini'] = '.aini',
                                            infiltration_profiles:list =['1'],
                                            wetdry:Literal['fixed', 'evolutive']='evolutive',
                                            steady:Literal['no precomputation', 'precomputation', 'steady'] = 'steady',
                                            executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                                            run_simulation: Literal['yes', 'no'] = 'no',
                                            force_steady = True
                                            ):
        """
        Create multiple simulations from a csv file.

        :param csv_filename: Csv filename
        :type csv_filename: str
        :param folder_path: Folder path
        :type folder_path: str
        :param cross_sections: Cross sections
        :type cross_sections: crosssections
        :param parallels: Parallels
        :type parallels: Zones
        :param banks: Banks
        :type banks: Zones
        :param boundary_conditions: Boundary conditions
        :type boundary_conditions: dict
        :param roughness: Roughness
        :type roughness: Union[float,WolfArray]
        :param hydrographs: Hydrographs
        :type hydrographs: list[list[list]]
        :param exe_file: Exe file
        :type exe_file: str
        :param topography: Topography, defaults to None
        :type topography: WolfArray, optional
        :param initial_discharge: Initial discharge, defaults to None
        :type initial_discharge: float, optional
        :param simulation_name: Simulation name, defaults to 'simul'
        :type simulation_name: str, optional
        :param discretisation: Discretisation, defaults to 10.
        :type discretisation: float, optional
        :param extrapolation_of_extremities: Extrapolation of extremities, defaults to 100.
        :type extrapolation_of_extremities: float, optional
        :param initial_depth: Initial depth, defaults to 1.
        :type initial_depth: float, optional
        :param write_in: Write in, defaults to 'times'
        :type write_in: Literal['iterations', 'times'], optional
        :param output_frequency: Output frequency, defaults to 900
        :type output_frequency: int, optional
        :param polygon_number: Polygon number, defaults to 1
        :type polygon_number: int, optional
        :param code_verbosity_profile: Code verbosity profile, defaults to [1]
        :type code_verbosity_profile: list, optional
        :param simulation_time: Simulation time, defaults to None
        :type simulation_time: int, optional
        :param roughness_option: Roughness option, defaults to 'under_profile'
        :type roughness_option: Literal['under_profile', 'under_polygons'], optional
        :param roughness_selection: Roughness selection, defaults to 'mean'
        :type roughness_selection: Literal['min','mean','median','max'], optional
        :param file_type_initial_cond: File type initial cond, defaults to '.aini'
        :type file_type_initial_cond: Literal['.aini','.hini','.zini'], optional
        :param infiltration_profiles: Infiltration profiles, defaults to ['1']
        :type infiltration_profiles: list, optional
        :param wetdry: Wetdry, defaults to 'evolutive'
        :type wetdry: Literal['fixed', 'evolutive'], optional
        :param steady: Steady, defaults to 'steady'
        :type steady: Literal['no precomputation', 'precomputation', 'steady'], optional
        :param executable_type: Executable type, defaults to 'wolfcli'
        :type executable_type: Literal['wolfcli', 'wolfclid'], optional
        :param run_simulation: Run simulation, defaults to 'no'
        :type run_simulation: Literal['yes', 'no'], optional
        :param force_steady: Force steady, defaults to True
        :type force_steady: bool, optional
        """
        # df = pd.read_csv(csv_filename, header=0, names = ['discharge'])
        df = self.read_csv_as_dataframe(csv_filename,column_names=['discharge'])
        k=1
        for discharge in list(df['discharge']):
            if force_steady:
                hydrographs =[[[0],[discharge]]]
            self.write_simulation_files_from_crosssections(folder_path,
                                                            cross_sections,
                                                            parallels,
                                                            banks,
                                                            boundary_conditions,
                                                            roughness,
                                                            hydrographs,
                                                            exe_file,
                                                            topography,
                                                            discharge,
                                                            simulation_name +f'{k}',
                                                            discretisation,
                                                            extrapolation_of_extremities,
                                                            initial_depth,
                                                            write_in,
                                                            output_frequency,
                                                            polygon_number,
                                                            code_verbosity_profile,
                                                            simulation_time,
                                                            roughness_option,
                                                            roughness_selection,
                                                            file_type_initial_cond,
                                                            infiltration_profiles,
                                                            wetdry,
                                                            steady,
                                                            executable_type,
                                                            run_simulation)
            k += 1

    def read_csv_as_dataframe(self, filename:str,  column_names:list = None, sep =',', header:int = 0, ) -> pd.DataFrame:
        """
        Read a csv file and return a pandas dataframe.

        :param filename: Filename
        :type filename: str
        :param column_names: Column names, defaults to None
        :type column_names: list, optional
        :param sep: Separator, defaults to ','
        :type sep: str, optional
        :param header: Header, defaults to 0
        :type header: int, optional
        :return: Pandas dataframe
        :rtype: pd.DataFrame
        """
        if column_names != None:
            return pd.read_csv(filename, sep=',', header=header, names=column_names)
        else:
            return pd.read_csv(filename, sep=',', header=header)

    def read_csv_as_infiltrations(self, filename:str,  sep =',', header:int = 0) -> list[dict]:
        """
        Read a csv file and return a list containing the infiltrations(hydrographs and profiles).

        :param filename: Filename
        :type filename: str
        :param sep: Separator, defaults to ','
        :type sep: str, optional
        :param header: Header, defaults to 0
        :type header: int, optional
        :return: List of infiltrations
        :rtype: list[dict]
        """
        df  = pd.read_csv(filename, sep=',',header=header)
        profiles = df.columns.values
        infiltrations = []
        for n in range(df.shape[0]):
                infiltration = {}
                for i in range(len(profiles)):
                        infiltration[profiles[i]] = Hydrograph({0:df[profiles[i]][n]})
                infiltrations.append(infiltration)
        return infiltrations

    def create_simulations_from_csv(self,
                                    csv_filename:str,
                                    folder_path:str,
                                    cross_sections: crosssections,
                                    parallels: Zones,
                                    banks: Zones,
                                    boundary_conditions: dict,
                                    roughness:Union[float,WolfArray],
                                    exe_file:str,
                                    hydrographs: list[list[list]] = None,
                                    topography: WolfArray = None,
                                    initial_discharge:float = None,
                                    simulation_name:str = 'simul',
                                    discretisation:float = 10.,
                                    extrapolation_of_extremities:float = 100.,
                                    initial_depth:float = 1.,
                                    write_in: Literal['iterations', 'times'] = 'times',
                                    output_frequency:int = 900,
                                    polygon_number:int = 1,
                                    code_verbosity_profile: list = [1],
                                    simulation_time:int = None,
                                    roughness_option: Literal['under_profile', 'under_polygons']= 'under_profile',
                                    roughness_selection:Literal['min','mean','median','max'] = 'mean',
                                    file_type_initial_cond: Literal['.aini','.hini','.zini'] = '.aini',
                                    infiltration_profiles:list =['1'],
                                    wetdry:Literal['fixed', 'evolutive']='evolutive',
                                    steady:Literal['no precomputation', 'precomputation', 'steady'] = 'precomputation',
                                    executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                                    run_simulation: Literal['yes', 'no'] = 'no',
                                    writing_type_infiltration: Literal['continuous', 'stepwise'] = 'continuous',
                                    epsilon_infiltration:float = 0.01,
                                    force_steady = True) -> None:
        """
        Create simulations from a csv file.

        :param csv_filename: Csv filename
        :type csv_filename: str
        :param folder_path: Folder path
        :type folder_path: str
        :param cross_sections: Cross sections
        :type cross_sections: crosssections
        :param parallels: Parallels
        :type parallels: Zones
        :param banks: Banks
        :type banks: Zones
        :param boundary_conditions: Boundary conditions
        :type boundary_conditions: dict
        :param roughness: Roughness
        :type roughness: Union[float,WolfArray]
        :param exe_file: Exe file
        :type exe_file: str
        :param hydrographs: Hydrographs, defaults to None
        :type hydrographs: list[list[list]], optional
        :param topography: Topography, defaults to None
        :type topography: WolfArray, optional
        :param initial_discharge: Initial discharge, defaults to None
        :type initial_discharge: float, optional
        :param simulation_name: Simulation name, defaults to 'simul'
        :type simulation_name: str, optional
        :param discretisation: Discretisation, defaults to 10.
        :type discretisation: float, optional
        :param extrapolation_of_extremities: Extrapolation of extremities, defaults to 100.
        :type extrapolation_of_extremities: float, optional
        :param initial_depth: Initial depth, defaults to 1.
        :type initial_depth: float, optional
        :param write_in: Write in, defaults to 'times'
        :type write_in: Literal['iterations', 'times'], optional
        :param output_frequency: Output frequency, defaults to 900
        :type output_frequency: int, optional
        :param polygon_number: Polygon number, defaults to 1
        :type polygon_number: int, optional
        :param code_verbosity_profile: Code verbosity profile, defaults to [1]
        :type code_verbosity_profile: list, optional
        :param simulation_time: Simulation time, defaults to None
        :type simulation_time: int, optional
        :param roughness_option: Roughness option, defaults to 'under_profile'
        :type roughness_option: Literal['under_profile', 'under_polygons'], optional
        :param roughness_selection: Roughness selection, defaults to 'mean'
        :type roughness_selection: Literal['min','mean','median','max'], optional
        :param file_type_initial_cond: File type initial cond, defaults to '.aini'
        :type file_type_initial_cond: Literal['.aini','.hini','.zini'], optional
        :param infiltration_profiles: Infiltration profiles, defaults to ['1']
        :type infiltration_profiles: list, optional
        :param wetdry: Wetdry, defaults to 'evolutive'
        :type wetdry: Literal['fixed', 'evolutive'], optional
        :param steady: Steady, defaults to 'precomputation'
        :type steady: Literal['no precomputation', 'precomputation', 'steady'], optional
        :param executable_type: Executable type, defaults to 'wolfcli'
        :type executable_type: Literal['wolfcli', 'wolfclid'], optional
        :param run_simulation: Run simulation, defaults to 'no'
        :type run_simulation: Literal['yes', 'no'], optional
        :param writing_type_infiltration: Writing type infiltration, defaults to 'continuous'
        :type writing_type_infiltration: Literal['continuous', 'stepwise'], optional
        :param epsilon_infiltration: Epsilon infiltration, defaults to 0.01
        :type epsilon_infiltration: float, optional
        :param force_steady: Force steady, defaults to True
        :type force_steady: bool, optional
        """
        df = self.read_csv_as_dataframe(csv_filename,column_names=['discharge'])
        discharge = df['discharge'][0]
        # hydrograph = Hydrograph({0:discharge})
        if force_steady:
                # hydrographs = {}
                hydrographs =[[[0],[discharge]]]
        original_simulation =self.write_simulation_files_from_crosssections(folder_path,
                                                            cross_sections,
                                                            parallels,
                                                            banks,
                                                            boundary_conditions,
                                                            roughness,
                                                            hydrographs,
                                                            exe_file,
                                                            topography,
                                                            discharge,
                                                            simulation_name,
                                                            discretisation,
                                                            extrapolation_of_extremities,
                                                            initial_depth,
                                                            write_in,
                                                            output_frequency,
                                                            polygon_number,
                                                            code_verbosity_profile,
                                                            simulation_time,
                                                            roughness_option,
                                                            roughness_selection,
                                                            file_type_initial_cond,
                                                            infiltration_profiles,
                                                            wetdry,
                                                            steady,
                                                            executable_type,
                                                            run_simulation ='no',
                                                            writing_type_infiltration = writing_type_infiltration,
                                                            epsilon_infiltration = epsilon_infiltration)
        procedures =[]

        new_sims =[]
        for new_discharge in list(df['discharge']):
            hydrographs =[[[0],[new_discharge]]]

            extension =f'_Q{int(new_discharge)}'
            new_sim_name = original_simulation[0] + extension
            new_sim = self.copy_simulation_files(original_simulation[0],new_sim_name, ignore_filetype='*.bat')
            new_sims.append(new_sim)


            self.write_ini_files(original_simulation[3],
                                 new_sim,
                                 new_discharge,
                                 original_simulation[4],
                                 file_choice=file_type_initial_cond)

            self.write_infiltrations(infiltration_profiles,original_simulation[2],hydrographs,new_sim)

            new_batchfile = self.write_batch_file(directory_of_executable = exe_file,
                                directory_simulation = new_sim,
                                simulation_name = simulation_name,
                                wetdry = wetdry,
                                steady = steady,
                                executable_type = executable_type,
                                different_names= True,
                                new_name=simulation_name + extension)
            procedures.append(new_batchfile)

            # # procedure = multiprocessing.Process(target= run_batch_file_multiprocess, args = (new_batchfile))
            # # procedure.start()
            # procedures.append(new_batchfile)
            # if run_simulation == 'yes':
            #     self.run_batch_file(new_batchfile)
            #     # procedure.start()

        batch_file_group = self.write_batch_simulations(directory_of_executable = exe_file,
                                                       simulations_path=new_sims,
                                                       wetdry = wetdry,
                                                       steady = steady,
                                                       executable_type = executable_type)

        if run_simulation == 'yes':
            # runs=[self.run_batch_file(i) for i in tqdm(procedures,'Running simulations', colour= Colors.TQDM.value)]
            # run = self.run_batch_file(batch_file_group)
            run = self.run_bat_files(batch_file_group)
            # # pool = multiprocessing.Pool(processes=len(procedures))
            # runs=[multiprocessing.Process(run_batch_file_multiprocess, args=i) for i in tqdm(procedures)]

    def copy_simulation_files(self,
                              simulation:str,
                              save_as:str,
                              ignore_filetype: Literal['.*qini','*.aini', '*.zini','*.hini','*.cl', '*.rough', 'infil*','*.inf'
                                                            '*.infil','*.param','*.top','*.ptv','*.gtv','.log', '.count'
                                                            '*.HEAD','*.RA', '*.RB','*.RQ','*.RS','*.vecz','*.vec','*.txt', '*.bat'] = '') -> str:
        """
        Copy simulation files.

        :param simulation: Simulation
        :type simulation: str
        :param save_as: Save as
        :type save_as: str
        :param ignore_filetype: Ignore filetype, defaults to ''
        :type ignore_filetype: str, optional
        :return: Copied directory
        :rtype: str
        """
        if ignore_filetype != '':
            try:
                copied_directory = shutil.copytree(src = simulation, dst= save_as)
            except FileExistsError:
                # os.rmdir(save_as)
                # copied_directory = shutil.copytree(src = simulation, dst= save_as)
                raise Exception(f"The file named ({save_as}) exists already.\n Rename the new file or delete the existing file.")
        else:
            try:
                copied_directory = shutil.copytree(src = simulation, dst= save_as, ignore=shutil.ignore_patterns(ignore_filetype))
            except FileExistsError:
                # os.rmdir(save_as)
                # copied_directory = shutil.copytree(src = simulation, dst= save_as, ignore=shutil.ignore_patterns(ignore_filetype))
                raise Exception(f"The file named ({save_as}) exists already.\n Rename the new file or delete the existing file.")
        return copied_directory

    def copy_multiple_simulations_from_csv(self, csv_filename:str, simulation:str) -> None:
        """
        Copy multiple simulations from a csv file.

        :param csv_filename: Csv filename
        :type csv_filename: str
        :param simulation: Simulation
        :type simulation: str
        """

        df = self.read_csv_as_dataframe(csv_filename,column_names=['discharge'])
        lgth = df.shape[0]
        for discharge in tqdm(df['discharge']):
            self.copy_simulation_files(simulation, simulation + f'_Q{discharge}')

    def distribute_values_as_sum(self, array: np.ndarray) -> np.ndarray:
        """Return a 1D array were the 0 are filled with the previous value in the table, and
        the existing values are replaced by their summed with the previous value in the table.

        :param array: Array(1D) containing the vaalues of the initial discharge at specific profiles
        :type array: np.ndarray
        :return: Updated array
        :rtype: np.ndarray
        """
        for i in range(len(array) - 1):
            j = i + 1
            if array[j] == 0:
                array[j] = array[i]
            elif  array[i] != 0:
                array[j] += array[i]
        return array

    def find_qini_values_from_infiltration_dict(self, infiltration:dict) -> dict:
        """
        Return a dictionnary  containing the infiltration profiles and their initial discharge (first value).

        These dictionnary can be used

        :param infiltration: Infiltration
        :type infiltration: dict
        :return: Initial infiltrations
        :rtype: dict
        """

        keys = []
        values =[]
        initial_infiltrations = {}
        for key in infiltration:
            if isinstance(infiltration[key], Hydrograph):
                qini = infiltration[key].values[0]
            elif isinstance(infiltration[key], (list,tuple)):
                qini = infiltration[key][0]
            elif isinstance(infiltration[key], (float,int)):
                qini = infiltration[key]
            else:
                raise Exception('The initial discharge is not well defined.')
            initial_infiltrations[int(key)-1] = qini

        return initial_infiltrations

    def compute_qini_values_from_infiltrations_dict(self,
                                                   infiltrations: dict,
                                                   nb_cells: int) -> np.ndarray:
        """Compute the initial discharge from a dictionary of infiltrations.
        The method returns an array of initial discharges. The array values are
        distributed from the distribution (linear sum) of the first infiltration values.

        :param infiltrations: Infiltrations (dictionnary of hydrographs)
        :type infiltrations: dict
        :param nb_cells: Number of cells
        :type nb_cells: int
        :return: Initial discharges
        :rtype: np.ndarray
        """
        qini_values = np.zeros(nb_cells)
        initial_infiltrations = self.find_qini_values_from_infiltration_dict(infiltrations)
        for key in initial_infiltrations:
            qini_values[key] = initial_infiltrations[key]

        qini_values = self.distribute_values_as_sum(qini_values)
        # print(qini_values)
        return qini_values

    def update_qini_file_from_infiltration_dict(self,
                                                infiltrations: dict,
                                                directory:str):
        """Upadte the qini file from a dictionary of infiltrations.

        :param infiltrations: Infiltrations
        :type infiltrations: dict
        :param directory: Directory (folder)
        :type directory: str
        """
        # Find the qini file from the simulation directory
        qini_file = self.find_file_from_extension(directory, '.qini')
        # Read the qini file as a  pandas dataframe
        qini_dataframe = self.read_ini_file_as_dataframe(qini_file)
        # Find the number of cells in the simulation
        number_of_cells = len(qini_dataframe['value'])
        # Compute the qini values from the infiltrations dictionary
        qini = self.compute_qini_values_from_infiltrations_dict(infiltrations, number_of_cells)
        # Update the qini file with the computed values
        self.update_ini_file(qini_file, qini)

    def read_ini_file_as_dataframe(self, ini_file:str):
        """Read an ini file and return a pandas dataframe.

        :param ini_file: File of initial conditions
        :type ini_file: str
        :return: Pandas dataframe
        :rtype: pd.DataFrame
        """
        dataframe = pd.read_csv(ini_file,
                         sep= Constants.SEPARATOR.value,
                         skiprows=1,
                         names=['skeleton', 'zone', 'segment','value']
                         )
        return dataframe

    def update_ini_file(self, ini_file:str, new_values: np.ndarray)-> None:
        """Update the initial condition file with new values.
        The method reads the initial condition file as a pandas dataframe,
        then replace old the values by the new values.

        :param ini_file: File of initial condition
        :type ini_file: str
        :param new_values: New values
        :type new_values: np.ndarray
        """
        df = self.read_ini_file_as_dataframe(ini_file)
        lgth_values = len(df['value'])
        lgth_new_values = len(new_values)
        assert lgth_values == lgth_new_values,\
            f"The length of the new values - {lgth_new_values} is not consistent with the initial condition file - {lgth_values}."

        df['value'] = new_values
        sep = Constants.SEPARATOR.value
        with open(ini_file, 'w') as f:
            f.write(f"{lgth_new_values}\n")
            for i in range(lgth_values):
                f.write(f"{df['skeleton'][i]}{sep}{df['zone'][i]}{sep}{df['segment'][i]}{sep}{str(df['value'][i])}\n")

        # Implement a clever way of writing or updating this file from ic or existing files.
        # check wolfresults_1D update ini file or find another way to update the file.


    # --- Outdated methods (deprecated) ---
    #_________________________

    def __write_batch_file(self,
                         directory_of_executable:str,
                         directory_simulation:str,
                         simulation_name:str,
                         wetdry:Literal['fixed', 'evolutive']='evolutive',
                         steady:Literal['no precomputation', 'precomputation', 'steady'] = 'precomputation',
                         executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                         different_names=False,
                         new_name:str =''
                         ) -> str:
        if different_names:
            batch_file =self.initialize_file(directory_of_executable, f'{new_name}.bat','') # To avoid simul name FIXME make it clean
        else:
            batch_file =self.initialize_file(directory_of_executable, '.bat')



        if wetdry == 'fixed':
            wtd = 0
        elif wetdry == 'evolutive':
            wtd= 1

        if steady== 'precomputation':
            std= 1
        elif steady == 'no precomputation':
            std = 0
        elif steady == 'steady':
            std=2

        find_full_path ='%~dp0'
        with open(batch_file,'w') as bat:
            bat.write(f'cd "{directory_of_executable}"\n')
            # bat.write(f'{executable_type} run_wolf1d dirin="%~dp0{simulation_name}" in="{simulation_name}" wetdry={wtd} steady={std}')
            if different_names:
                bat.write(f'{executable_type} run_wolf1d dirin="{find_full_path}{new_name}" in="{simulation_name}" wetdry={wtd} steady={std}')
                # if directory_simulation[0] =='.':
                #     bat.write(f'{executable_type} run_wolf1d dirin="{find_full_path}{directory_simulation}" in="{simulation_name}" wetdry={wtd} steady={std}')
                # else:
                #     bat.write(f'{executable_type} run_wolf1d dirin="{find_full_path}{directory_simulation}" in="{simulation_name}" wetdry={wtd} steady={std}')

            else:
                bat.write(f'{executable_type} run_wolf1d dirin="{find_full_path}{simulation_name}" in="{simulation_name}" wetdry={wtd} steady={std}')

        return batch_file

    def match_ends_2vectors_outdated(self,
                            zones1: Zones,
                            zones2: Zones,
                            id1:int = 0,
                            id2:int = 0) -> Zones:
        """
        Aligns the vertices of  2 successive zone
        containing each 3 vectors (1 vector and its 2 parallels),
        so that, the end of each vector matches the begining of its corresponding in the other zone.
            - id1: zone id in zones1.myzones,
            - id2: zone id in zones2.myzones.
        """
        znes1 = zones1
        znes2 = zones2
        vector1_1 = znes1.myzones[id1].myvectors[0]
        vector1_2 = znes1.myzones[id1].myvectors[1]
        vector1_3 = znes1.myzones[id1].myvectors[2]
        vector2_1 = znes2.myzones[id2].myvectors[0]
        vector2_2 = znes2.myzones[id2].myvectors[1]
        vector2_3 = znes2.myzones[id2].myvectors[2]
        i = vector1_1.myvertices
        j = vector2_1.myvertices

        distance1 = math.sqrt(((i[-1].x - j[0].x)**2) + ((i[-1].y - j[0].y)**2)) #last point - first point
        distance2 = math.sqrt(((i[-1].x - j[-1].x)**2) + ((i[-1].y - j[-1].y)**2)) #last point - last point
        distance1_r = math.sqrt(((i[0].x - j[0].x)**2) + ((i[0].y - j[0].y)**2)) # first point - first point
        distance2_r = math.sqrt(((i[0].x - j[-1].x)**2) + ((i[0].y - j[-1].y)**2)) #first point - last point

        all = [distance1, distance2, distance1_r, distance2_r]

        if min(all) == distance2:
            vector2_1.myvertices.reverse()
            vector2_2.myvertices.reverse()
            vector2_3.myvertices.reverse()

        elif min(all) == distance1_r:
            vector1_1.myvertices.reverse()
            vector1_2.myvertices.reverse()
            vector1_3.myvertices.reverse()

        elif min(all) ==distance2_r:
            vector1_1.myvertices.reverse()
            vector1_2.myvertices.reverse()
            vector1_3.myvertices.reverse()
            vector2_1.myvertices.reverse()
            vector2_2.myvertices.reverse()
            vector2_3.myvertices.reverse()

        return znes1, znes2

    def __save_as_1D_crossections(self,
                                  zones: Zones,
                                  format ='vecz',
                                  save_as: str='') -> crosssections:
        znes = zones
        path = save_as + 'profiles' + id +'.vecz'
        index = 1
        for vec in znes.myzones[0].myvectors:
            vec.myname = '%s'%(index)
            index+=1

        znes.find_minmax()
        znes.saveas(path)
        cross= crosssections(mydata= path,format='vecz')
        cross.format = format
        if save_as:
            cross.saveas(save_as)
        return cross

    def __update_qini_file_from_infiltration_dict(self,
                                                infiltrations: dict,
                                                directory:str):
        """Deprecating due to the last for loop (it's obviously a code duplication)."""

        qini_file = self.find_file_from_extension(directory, '.qini')
        qini_dataframe = self.read_ini_file_as_dataframe(qini_file)
        number_of_cells = len(qini_dataframe['value'])
        qini = self.compute_qini_values_from_infiltrations_dict(infiltrations, number_of_cells)
        for file in os.listdir(directory):
            if file.endswith('.qini'):
                qini_file = os.path.join(directory, file)
                self.update_ini_file(qini_file, qini)

    def _create_simulations_from_csv(self,
                                    csv_filename:str,
                                    folder_path:str,
                                    cross_sections: crosssections,
                                    parallels: Zones,
                                    banks: Zones,
                                    boundary_conditions: dict,
                                    roughness:Union[float,WolfArray],
                                    hydrographs: list[list[list]],
                                    exe_file:str,
                                    topography: WolfArray = None,
                                    initial_discharge:float = None,
                                    simulation_name:str = 'simul',
                                    discretisation:float = 10.,
                                    extrapolation_of_extremities:float = 100.,
                                    initial_depth:float = 1.,
                                    write_in: Literal['iterations', 'times'] = 'times',
                                    output_frequency:int = 900,
                                    polygon_number:int = 1,
                                    code_verbosity_profile: list = [1],
                                    simulation_time:int = None,
                                    roughness_option: Literal['under_profile', 'under_polygons']= 'under_profile',
                                    roughness_selection:Literal['min','mean','median','max'] = 'mean',
                                    file_type_initial_cond: Literal['.aini','.hini','.zini'] = '.aini',
                                    infiltration_profiles:list =['1'],
                                    wetdry:Literal['fixed', 'evolutive']='evolutive',
                                    steady:Literal['no precomputation', 'precomputation', 'steady'] = 'precomputation',
                                    executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                                    run_simulation: Literal['yes', 'no'] = 'no',
                                    writing_type_infiltration: Literal['continuous', 'stepwise'] = 'continuous',
                                    epsilon_infiltration:float = 0.01,
                                    force_steady = True) -> None:
        """Deprecated"""

        infiltrations = self.read_csv_as_infiltrations(csv_filename)
        names = self.read_csv_as_dataframe(csv_filename)

        # # df = self.read_csv_as_dataframe(csv_filename,column_names=['discharge'])
        # # discharge = df['discharge'][0]
        # hydrograph = Hydrograph({0:discharge})
        if force_steady:
                hydrographs = infiltrations[0]
                # hydrographs = {}
                # hydrographs =[[[0],[discharge]]]
        original_simulation =self.write_simulation_files_from_crosssections(folder_path,
                                                            cross_sections,
                                                            parallels,
                                                            banks,
                                                            boundary_conditions,
                                                            roughness,
                                                            hydrographs,
                                                            exe_file,
                                                            topography,
                                                            initial_discharge,
                                                            simulation_name,
                                                            discretisation,
                                                            extrapolation_of_extremities,
                                                            initial_depth,
                                                            write_in,
                                                            output_frequency,
                                                            polygon_number,
                                                            code_verbosity_profile,
                                                            simulation_time,
                                                            roughness_option,
                                                            roughness_selection,
                                                            file_type_initial_cond,
                                                            infiltration_profiles,
                                                            wetdry,
                                                            steady,
                                                            executable_type,
                                                            run_simulation ='no',
                                                            writing_type_infiltration = writing_type_infiltration,
                                                            epsilon_infiltration = epsilon_infiltration)
        procedures =[]

        for new_infiltration in infiltrations:
            hydrographs = new_infiltration
            values = list(new_infiltration.values())
            extension =f'_Q{int(values[0])}' # FIXME
            new_sim = self.copy_simulation_files(original_simulation[0],original_simulation[0] + extension)

            self.write_ini_files(original_simulation[3],
                                 new_sim,
                                 new_infiltration,
                                 original_simulation[4],
                                 file_choice=file_type_initial_cond)

            self.write_infiltrations(infiltration_profiles,original_simulation[2],hydrographs,new_sim)

            new_batchfile = self.write_batch_file(directory_of_executable = exe_file,
                                directory_simulation = new_sim,
                                simulation_name = simulation_name,
                                wetdry = wetdry,
                                steady = steady,
                                executable_type = executable_type,
                                different_names= True,
                                new_name=simulation_name + extension)
            procedures.append(new_batchfile)


            # # procedure = multiprocessing.Process(target= run_batch_file_multiprocess, args = (new_batchfile))
            # # procedure.start()
            # procedures.append(new_batchfile)
            # if run_simulation == 'yes':
            #     self.run_batch_file(new_batchfile)
            #     # procedure.start()

        if run_simulation == 'yes':
            runs=[self.run_batch_file(i) for i in tqdm(procedures,'Running simulations', colour= Colors.TQDM.value)]
            # # pool = multiprocessing.Pool(processes=len(procedures))
            # runs=[multiprocessing.Process(run_batch_file_multiprocess, args=i) for i in tqdm(procedures)]

    def _start_from_steady_state(self,
                                profile:str,
                                infiltrations:dict,
                                list_of_sorted_cross: list,
                                directory,
                                plot = True,
                                ):
        qini = infiltrations[profile]
        if isinstance(qini, Hydrograph):
            qini = qini.values[0]
        elif isinstance(qini, (list,tuple)):
            # FIXME to be verified
            qini = qini[0]
        elif qini == float:
            qini = qini
        else:
            raise ValueError('The initial discharge is not well defined.')

        hydrograph = Hydrograph({0:qini})

        new_infiltrations = {profile:hydrograph}
        self.write_infiltrations_from_dict(list_of_sorted_cross, new_infiltrations, directory)
        self.write_parameters(directory, write_type= 2, max_time=0)
        bat_file = self.find_file_from_extension(directory, '.bat')
        self._run_bat_files(bat_file, initial_condition= True)
        # self.run_bat_files(bat_file)
        self.update_initial_conditions_from_results(directory, time_step=1, plot=plot)

    def __write_simulation_files_from_crosssections(self,
                                                folder_path:str,
                                                cross_sections: crosssections,
                                                parallels: Zones,
                                                banks: Zones,
                                                boundary_conditions: dict,
                                                roughness:Union[float,WolfArray],
                                                hydrographs: list[list[list]],
                                                exe_file:str,
                                                topography: WolfArray = None,
                                                initial_discharge:float = None,
                                                simulation_name:str = 'simul',
                                                discretisation:float = 10.,
                                                extrapolation_of_extremities:float = 100.,
                                                initial_depth:float = 1.,
                                                write_in: Literal['iterations', 'times'] = 'times',
                                                output_frequency:int = 900,
                                                polygon_number:int = 1,
                                                code_verbosity_profile: list = [1],
                                                simulation_time:int = None,
                                                roughness_option: Literal['under_profile', 'under_polygons']= 'under_profile',
                                                roughness_selection:Literal['min','mean','median','max'] = 'mean',
                                                file_type_initial_cond: Literal['.aini','.hini','.zini'] = '.aini',
                                                infiltration_profiles:list =['1'],
                                                wetdry:Literal['fixed', 'evolutive']='evolutive',
                                                steady:Literal['no precomputation', 'precomputation', 'steady'] = 'precomputation',
                                                executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                                                run_simulation: Literal['yes', 'no'] = 'no',
                                                writing_type_infiltration: Literal['continuous', 'stepwise'] = 'continuous',
                                                epsilon_infiltration:float = 0.01,
                                                new_directory = '',
                                                force_steady = True
                                                ) -> tuple:
        """
        Write the simulation files (the 1D model) from the cross sections and the other parameters with one line of code.

        :param folder_path: Folder path
        :type folder_path: str
        :param cross_sections: Cross sections
        :type cross_sections: crosssections
        :param parallels: Parallels
        :type parallels: Zones
        :param banks: Banks
        :type banks: Zones
        :param boundary_conditions: Boundary conditions
        :type boundary_conditions: dict
        :param roughness: Roughness
        :type roughness: Union[float,WolfArray]
        :param hydrographs: Hydrographs
        :type hydrographs: list[list[list]]
        :param exe_file: Exe file
        :type exe_file: str
        :param topography: Topography, defaults to None
        :type topography: WolfArray, optional
        :param initial_discharge: Initial discharge, defaults to None
        :type initial_discharge: float, optional
        :param simulation_name: Simulation name, defaults to 'simul'
        :type simulation_name: str, optional
        :param discretisation: Discretisation, defaults to 10.
        :type discretisation: float, optional
        :param extrapolation_of_extremities: Extrapolation of extremities, defaults to 100.
        :type extrapolation_of_extremities: float, optional
        :param initial_depth: Initial depth, defaults to 1.
        :type initial_depth: float, optional
        :param write_in: Write in, defaults to 'times'
        :type write_in: Literal['iterations', 'times'], optional
        :param output_frequency: Output frequency, defaults to 900
        :type output_frequency: int, optional
        :param polygon_number: Polygon number, defaults to 1
        :type polygon_number: int, optional
        :param code_verbosity_profile: Code verbosity profile, defaults to [1]
        :type code_verbosity_profile: list, optional
        :param simulation_time: Simulation time, defaults to None
        :type simulation_time: int, optional
        :param roughness_option: Roughness option, defaults to 'under_profile'
        :type roughness_option: Literal['under_profile', 'under_polygons'], optional
        :param roughness_selection: Roughness selection, defaults to 'mean'
        :type roughness_selection: Literal['min','mean','median','max'], optional
        :param file_type_initial_cond: File type initial cond, defaults to '.aini'
        :type file_type_initial_cond: Literal['.aini','.hini','.zini'], optional
        :param infiltration_profiles: Infiltration profiles, defaults to ['1']
        :type infiltration_profiles: list, optional
        :param wetdry: Wetdry, defaults to 'evolutive'
        :type wetdry: Literal['fixed', 'evolutive'], optional
        :param steady: Steady, defaults to 'precomputation'
        :type steady: Literal['no precomputation', 'precomputation', 'steady'], optional
        :param executable_type: Executable type, defaults to 'wolfcli'
        :type executable_type: Literal['wolfcli', 'wolfclid'], optional
        :param run_simulation: Run simulation, defaults to 'no'
        :type run_simulation: Literal['yes', 'no'], optional
        :param writing_type_infiltration: Writing type infiltration, defaults to 'continuous'
        :type writing_type_infiltration: Literal['continuous', 'stepwise'], optional
        :param epsilon_infiltration: Epsilon infiltration, defaults to 0.01
        :type epsilon_infiltration: float, optional
        :param new_directory: New directory, defaults to ''
        :type new_directory: str, optional
        :param force_steady: Force steady, defaults to True
        :type force_steady: bool, optional
        :return: tuple
        :rtype: tuple
        """


        # Simulation directory (contains all simulation files)
        if new_directory != '':
            directory = new_directory
        else:
            directory = self.create_simulation_directory(folder_path,simulation_name)

        # The extremities of each profile is extrapolated to avoid negative water depths in case of high discharges
        extrapolated_cross_sections = self.extrapolate_extremities(cross_sections,
                                                                    extrapolation_of_extremities,
                                                                    directory)
        # The crossection are sorted based on the river bed (middle parallel)
        sorted_crosssections = self.sort_crossections_list([extrapolated_cross_sections], banks)
        #
        if simulation_time:
            time = simulation_time
        else:
            # FIXME Multiple hydrographs
            if isinstance(hydrographs,dict):
                times = []
                for hydro, prof in hydrographs.items():
                    if isinstance(prof, Hydrograph):
                        times.append(max(prof.index))
                    elif isinstance(prof, list):
                        latest_time = prof[0][-1]
                        times.append(latest_time)

                time = max(times)

            else:
                if isinstance(hydrographs[0], Hydrograph):
                    time = max(hydrographs[0].index)
                elif isinstance(hydrographs[0], list):
                    time = hydrographs[0][0][-1]

        if initial_discharge:
            q_ini = initial_discharge
        else:
            if isinstance(hydrographs,dict):
                discharges = []
                for hydro, prof in hydrographs.items():
                    if isinstance(prof, Hydrograph):
                        first_discharge = prof.values[0]
                        discharges.append(first_discharge)
                    elif isinstance(prof, list):
                        first_discharge = prof[0][0]
                        discharges.append(first_discharge)
                q_ini = min(discharges)
            else:
                if isinstance(hydrographs[0], Hydrograph):
                    q_ini = hydrographs[0].values[0]
                elif isinstance(hydrographs[0], list):
                    q_ini = hydrographs[0][1][0]

        # Bank file
        if banks.is2D:
            bank_file = self.get_values_from_array(banks, topography, directory + '\\banks.vecz')
        else:
            bank_file = banks
            bank_file.saveas(directory + '\\banks.vecz')

        # Polygons
        # FIXME is it necessery  to have parallels (next round), is it only for cell size or a better used could be found?
        if isinstance(parallels, Zones):
            polygons = self.create_polygons(parallels, discretisation, polygon_number, directory)

        # Write the tabulated relations of each cross section (profile)
        write_relations = self.write_relations_profiles(sorted_crosssections, directory)

        # Write roughnesses
        if isinstance(roughness, float) or isinstance(roughness, int):
            roughnesses = self.roughness_from_value(sorted_crosssections,  value = roughness)

        elif isinstance(roughness, WolfArray):
            if roughness_option == 'under_profile':
                roughnesses = self.roughness_from_profiles(roughness, sorted_crosssections, mode=roughness_selection)

            elif roughness_option == 'under_polygons':
                # FIXME to be verified issue with the extent of profiles
                # (the number of new polygons is different from the number of digitized profiles)
                # May be a test should be implemented on each profiles (probable solution).
                roughnesses = self.roughness_from_polygons(roughness, polygons, mode=roughness_selection)

        roughness_file = self.write_roughnesses(roughnesses, directory)

        # Compute & write the intial conditions
        ic_relations, nb_updates = self.ic_relations_hspw(sorted_crosssections, initial_depth)

        # The simulation is initialized based on the wetted area (more practical)
        ini_files = self.write_ini_files(ic_relations,
                                            directory,
                                            q = q_ini,
                                            nb_updates= nb_updates,
                                            file_choice=[file_type_initial_cond])

        # Write the boundary conditions
        cl_file = self.write_cl_file(sorted_crosssections, boundary_conditions, directory)

        # Write .top file (topography)
        top_file = self.write_top_file(sorted_crosssections,directory)

        # Write the .vec file (discretization file of the simulation topography - lowest riverbed point)
        vec_file1 = self.write_vector_files(sorted_crosssections, save_as=directory,which_type='vecz')

        # Sets the predefined river banks and bed on each cross sections
        set_bank = self.set_banksbed_vectors(bank_file)

        # Write the .vec file (discretization file of the simulation topography - midriver)
        vec_file2 = self.write_vector_files(sorted_crosssections, save_as=directory, which_type='vec')

        # Write the infiltrations
        if isinstance(hydrographs, dict):
            infil = self.write_infiltrations_from_dict(sorted_crosssections,
                                         hydrographs,
                                         directory,
                                         writing_type_infiltration,
                                         epsilon_infiltration)
        elif isinstance(hydrographs,list):
            infil = self.write_infiltrations(infiltration_profiles,
                                            sorted_crosssections,
                                            hydrographs,
                                            directory,
                                            writing_type_infiltration,
                                            epsilon_infiltration)

        # write the simulation parameters
        if write_in == 'times':
            write_type = 2
        elif write_in =='iterations':
            write_type = 1
        if self.wx_exists == None:
            param = self.write_parameters(directory, write_freq= output_frequency, write_type= write_type, max_time=time)
        # # if steady == 'precomputation' or steady == 'steady':
        # #     self.correct_parameters(directory, from_steady=True)
        # # else:
        # #     self.correct_parameters(directory)
        # self.correct_parameters(directory) FIXME for other cases when the GUI is not used

        genfile = self.write_generic_file(directory)
        batch_file = self.write_batch_file(directory_of_executable = exe_file,
                                           directory_simulation = directory,
                                           simulation_name = simulation_name,
                                           wetdry = wetdry,
                                           steady = steady,
                                           executable_type = executable_type)
        if run_simulation == 'yes':
            # logging.warn(f'{simulation_name} running... \nThe process may take time.')
            self.run_bat_files(batch_file)
            # logging.warn(f'{simulation_name} completed.')
        return (directory,simulation_name, sorted_crosssections, ic_relations, nb_updates)

    def ____write_simulation_files_from_crosssections(self,
                                                folder_path:str,
                                                cross_sections: crosssections,
                                                parallels: Zones,
                                                banks: Zones,
                                                boundary_conditions: dict,
                                                roughness:Union[float,WolfArray],
                                                hydrographs: list[list[list]],
                                                exe_file:str,
                                                topography: WolfArray = None,
                                                initial_discharge:float = None,
                                                simulation_name:str = 'simul',
                                                discretisation:float = 10.,
                                                extrapolation_of_extremities:float = 100.,
                                                initial_depth:float = 1.,
                                                write_in: Literal['iterations', 'times'] = 'times',
                                                output_frequency:int = 900,
                                                polygon_number:int = 1,
                                                code_verbosity_profile: list = [1],
                                                simulation_time:int = None,
                                                roughness_option: Literal['under_profile', 'under_polygons']= 'under_profile',
                                                roughness_selection:Literal['min','mean','median','max'] = 'mean',
                                                file_type_initial_cond: Literal['.aini','.hini','.zini'] = '.aini',
                                                infiltration_profiles:list =['1'],
                                                wetdry:Literal['fixed', 'evolutive']='evolutive',
                                                steady:Literal['no precomputation', 'precomputation', 'steady'] = 'precomputation',
                                                executable_type: Literal['wolfcli', 'wolfclid'] = 'wolfcli',
                                                run_simulation: Literal['yes', 'no'] = 'no',
                                                writing_type_infiltration: Literal['continuous', 'stepwise'] = 'continuous',
                                                epsilon_infiltration:float = 0.01,
                                                new_directory = '',
                                                steady_state_profile = '',
                                                force_steady = True,
                                                start_from_steady_state = False,
                                                plot_steady_state = True
                                                ) -> tuple:
        """
        Write the simulation files (the 1D model) from the cross sections and the other parameters with one line of code.

        :param folder_path: Folder path
        :type folder_path: str
        :param cross_sections: Cross sections
        :type cross_sections: crosssections
        :param parallels: Parallels
        :type parallels: Zones
        :param banks: Banks
        :type banks: Zones
        :param boundary_conditions: Boundary conditions
        :type boundary_conditions: dict
        :param roughness: Roughness
        :type roughness: Union[float,WolfArray]
        :param hydrographs: Hydrographs
        :type hydrographs: list[list[list]]
        :param exe_file: Exe file
        :type exe_file: str
        :param topography: Topography, defaults to None
        :type topography: WolfArray, optional
        :param initial_discharge: Initial discharge, defaults to None
        :type initial_discharge: float, optional
        :param simulation_name: Simulation name, defaults to 'simul'
        :type simulation_name: str, optional
        :param discretisation: Discretisation, defaults to 10.
        :type discretisation: float, optional
        :param extrapolation_of_extremities: Extrapolation of extremities, defaults to 100.
        :type extrapolation_of_extremities: float, optional
        :param initial_depth: Initial depth, defaults to 1.
        :type initial_depth: float, optional
        :param write_in: Write in, defaults to 'times'
        :type write_in: Literal['iterations', 'times'], optional
        :param output_frequency: Output frequency, defaults to 900
        :type output_frequency: int, optional
        :param polygon_number: Polygon number, defaults to 1
        :type polygon_number: int, optional
        :param code_verbosity_profile: Code verbosity profile, defaults to [1]
        :type code_verbosity_profile: list, optional
        :param simulation_time: Simulation time, defaults to None
        :type simulation_time: int, optional
        :param roughness_option: Roughness option, defaults to 'under_profile'
        :type roughness_option: Literal['under_profile', 'under_polygons'], optional
        :param roughness_selection: Roughness selection, defaults to 'mean'
        :type roughness_selection: Literal['min','mean','median','max'], optional
        :param file_type_initial_cond: File type initial cond, defaults to '.aini'
        :type file_type_initial_cond: Literal['.aini','.hini','.zini'], optional
        :param infiltration_profiles: Infiltration profiles, defaults to ['1']
        :type infiltration_profiles: list, optional
        :param wetdry: Wetdry, defaults to 'evolutive'
        :type wetdry: Literal['fixed', 'evolutive'], optional
        :param steady: Steady, defaults to 'precomputation'
        :type steady: Literal['no precomputation', 'precomputation', 'steady'], optional
        :param executable_type: Executable type, defaults to 'wolfcli'
        :type executable_type: Literal['wolfcli', 'wolfclid'], optional
        :param run_simulation: Run simulation, defaults to 'no'
        :type run_simulation: Literal['yes', 'no'], optional
        :param writing_type_infiltration: Writing type infiltration, defaults to 'continuous'
        :type writing_type_infiltration: Literal['continuous', 'stepwise'], optional
        :param epsilon_infiltration: Epsilon infiltration, defaults to 0.01
        :type epsilon_infiltration: float, optional
        :param new_directory: New directory, defaults to ''
        :type new_directory: str, optional
        :param force_steady: Force steady, defaults to True
        :type force_steady: bool, optional
        :return: tuple
        :rtype: tuple
        """


        # Simulation directory (contains all simulation files)
        if new_directory != '':
            directory = new_directory
        else:
            directory = self.create_simulation_directory(folder_path,simulation_name)

        # The extremities of each profile is extrapolated to avoid negative water depths in case of high discharges
        extrapolated_cross_sections = self.extrapolate_extremities(cross_sections,
                                                                    extrapolation_of_extremities,
                                                                    directory)
        # The crossection are sorted based on the river bed (middle parallel)
        sorted_crosssections = self.sort_crossections_list([extrapolated_cross_sections], banks)
        #
        if simulation_time:
            time = simulation_time
        else:
            # FIXME Multiple hydrographs
            if isinstance(hydrographs,dict):
                times = []
                for hydro, prof in hydrographs.items():
                    if isinstance(prof, Hydrograph):
                        times.append(max(prof.index))
                    elif isinstance(prof, list):
                        latest_time = prof[0][-1]
                        times.append(latest_time)

                time = max(times)

            else:
                if isinstance(hydrographs[0], Hydrograph):
                    time = max(hydrographs[0].index)
                elif isinstance(hydrographs[0], list):
                    time = hydrographs[0][0][-1]

        if initial_discharge:
            q_ini = initial_discharge
        else:
            if isinstance(hydrographs,dict):
                discharges = []
                for hydro, prof in hydrographs.items():
                    if isinstance(prof, Hydrograph):
                        first_discharge = prof.values[0]
                        discharges.append(first_discharge)
                    elif isinstance(prof, list):
                        first_discharge = prof[0][0]
                        discharges.append(first_discharge)
                q_ini = min(discharges)
            else:
                if isinstance(hydrographs[0], Hydrograph):
                    q_ini = hydrographs[0].values[0]
                elif isinstance(hydrographs[0], list):
                    q_ini = hydrographs[0][1][0]

        # Bank file
        if banks.is2D:
            bank_file = self.get_values_from_array(banks, topography, directory + '\\banks.vecz')
        else:
            bank_file = banks
            bank_file.saveas(directory + '\\banks.vecz')

        # Polygons
        # FIXME is it necessery  to have parallels (next round), is it only for cell size or a better used could be found?
        if isinstance(parallels, Zones):
            polygons = self.create_polygons(parallels, discretisation, polygon_number, directory)

        # Write the tabulated relations of each cross section (profile)
        write_relations = self.write_relations_profiles(sorted_crosssections, directory)

        # Write roughnesses
        if isinstance(roughness, float) or isinstance(roughness, int):
            roughnesses = self.roughness_from_value(sorted_crosssections,  value = roughness)

        elif isinstance(roughness, WolfArray):
            if roughness_option == 'under_profile':
                roughnesses = self.roughness_from_profiles(roughness, sorted_crosssections, mode=roughness_selection)

            elif roughness_option == 'under_polygons':
                # FIXME to be verified issue with the extent of profiles
                # (the number of new polygons is different from the number of digitized profiles)
                # May be a test should be implemented on each profiles (probable solution).
                roughnesses = self.roughness_from_polygons(roughness, polygons, mode=roughness_selection)

        roughness_file = self.write_roughnesses(roughnesses, directory)

        # Compute & write the intial conditions
        ic_relations, nb_updates = self.ic_relations_hspw(sorted_crosssections, initial_depth)

        # The simulation is initialized based on the wetted area (more practical)
        ini_files = self.write_ini_files(ic_relations,
                                            directory,
                                            q = q_ini,
                                            nb_updates= nb_updates,
                                            file_choice=[file_type_initial_cond])

        # Write the boundary conditions
        cl_file = self.write_cl_file(sorted_crosssections, boundary_conditions, directory)

        # Write .top file (topography)
        top_file = self.write_top_file(sorted_crosssections,directory)

        # Write the .vec file (discretization file of the simulation topography - lowest riverbed point)
        vec_file1 = self.write_vector_files(sorted_crosssections, save_as=directory,which_type='vecz')

        # Sets the predefined river banks and bed on each cross sections
        set_bank = self.set_banksbed_vectors(bank_file)

        # Write the .vec file (discretization file of the simulation topography - midriver)
        vec_file2 = self.write_vector_files(sorted_crosssections, save_as=directory, which_type='vec')
        # write the generic file
        genfile = self.write_generic_file(directory)
        # Write the batch file
        batch_file = self.write_batch_file(directory_of_executable = exe_file,
                                           directory_simulation = directory,
                                           simulation_name = simulation_name,
                                           wetdry = wetdry,
                                           steady = steady,
                                           executable_type = executable_type)

        # Update initial conditions
        if start_from_steady_state:
            self.start_from_steady_state(directory, plot = plot_steady_state)

            # # if profile == '':
            # #     profile = '1'
            # # self.start_from_steady_state(profile=steady_state_profile,
            # #                              infiltrations= hydrographs,
            # #                              list_of_sorted_cross= sorted_crosssections,
            # #                              directory= directory,
            # #                              plot= plot_steady_state)

            # Write the batch file
            batch_file = self.write_batch_file(directory_of_executable = exe_file,
                                            directory_simulation = directory,
                                            simulation_name = simulation_name,
                                            wetdry = wetdry,
                                            steady = 'no precomputation',
                                            executable_type = executable_type)

        # Write the infiltrations
        if isinstance(hydrographs, dict):
            infil = self.write_infiltrations_from_dict(sorted_crosssections,
                                         hydrographs,
                                         directory,
                                         writing_type_infiltration,
                                         epsilon_infiltration)
        elif isinstance(hydrographs,list):
            infil = self.write_infiltrations(infiltration_profiles,
                                            sorted_crosssections,
                                            hydrographs,
                                            directory,
                                            writing_type_infiltration,
                                            epsilon_infiltration)

        # write the simulation parameters
        if write_in == 'times':
            write_type = 2
        elif write_in =='iterations':
            write_type = 1
        if self.wx_exists == None:
            param = self.write_parameters(directory, write_freq= output_frequency, write_type= write_type, max_time=time)

        if run_simulation == 'yes':
            # logging.warn(f'{simulation_name} running... \nThe process may take time.')
            self.run_bat_files(batch_file)
            # logging.warn(f'{simulation_name} completed.')
        return (directory,simulation_name, sorted_crosssections, ic_relations, nb_updates)

# --- Wolf 1D results ---
#________________________

class Wolfresults_1D:
    """
        Read the results of a Wolf 1D model and
        enable the visualization (plots) of variables namely
        water level, water depth, discharge,
        wetted sections, velocity and Froude number.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.
        """
    def __init__(self, simulation_directory:str = None)-> None:
        """
        Constructor of the class Wolfresults

        :param simulation_directory: Computer path to the folder containing the results of the simulation
        :type simulation_directory: str

        .. todo:: FIXME Implement a consitency check of the files
        .. to do:: FIXME  Use a multiprocess to speed up the creation of `.gif` files.
        .. to do: FIXME: find a way to implement an initial time for the simulation
        """
        # Useful properties for other methds
        self.directory = simulation_directory
        self.breath_file = None
        self.breath_directory = None
        self.bank_file = None
        self.support_file = None
        self.cross_sections_file = None
        self.simulation_name = os.path.split(self.directory)[1]

        # Files detection in the directory
        for file in os.listdir(simulation_directory):
            if file.endswith(".HEAD"):
                self.head_file = os.path.join(simulation_directory,file)
            elif file.endswith(".RH"):
                self.depths_file = os.path.join(simulation_directory,file)
            elif file.endswith(".RQ"):
                self.discharges_file = os.path.join(simulation_directory,file)
            elif file.endswith(".RA"):
                self.wetted_sections_file = os.path.join(simulation_directory,file)
            # Result from post_process
            elif file.endswith(".RWIDTH"):
                self.breath_file = os.path.join(simulation_directory,file)
            # Preprocess data to fasten the computation
            elif file.endswith('top_widths'):
                self.breath_directory = self.directory +f'\\{file}'
            # Data for the computation of width relationships
            elif file.endswith('sections.vecz'):
                self.cross_sections_file = os.path.join(simulation_directory,file)
            elif file.endswith(f'{self.simulation_name}.vec'):
                self.support_file = os.path.join(simulation_directory,file)
            elif file.endswith('banks.vecz'):
                self.bank_file = os.path.join(simulation_directory,file)

            elif file.endswith('_banksbed.vecz'):
                self.banksbed_file = os.path.join(simulation_directory,file)



        # Reading the results
        #  # head file
        file_size = os.path.getsize(self.head_file) # size of head file in bytes
        with open (self.head_file,"rb") as head_binary:
            # Necessary informations to extract coordinates
            head_in_bytes = head_binary.read()
            cells_number = np.frombuffer(head_in_bytes, dtype=np.int32, count=1)[0]
            nb_coordinates_data = 3 * cells_number
            time_steps_number = (file_size - 4 - (4 * nb_coordinates_data))/8
            assert (time_steps_number).is_integer(),\
                f'The number of results is not an integer {time_steps_number}'
            results_number = int(time_steps_number)

            # Extraction of cell coordinates
            head_data = np.frombuffer(head_in_bytes, dtype= np.float32)
            coordinates = head_data[1 :  nb_coordinates_data + 1].reshape(cells_number,3)
            coordinates = np.roll(coordinates, 1, axis= 0)
            # # @ coordinates: [0] == Z | [1] == Y | [2] == X
            self.coordinates = np.flip(coordinates, axis=1)
            self.topo = self.coordinates[:,0]
            self.xy = self.coordinates[-1]
            self.vector_coordinates = None
            self.s_curvi = None

            # Extraction of time steps
            all_times = head_data[nb_coordinates_data + 1::]
            self.simulated_times = all_times[1::2] # FIXME why does it start from 1?
            # self.simulated_times = all_times[::2]
            self.real_times = all_times[::2]

            # Formula for available results
            available_results = int(time_steps_number*cells_number*4)
            file_size_depths = os.path.getsize(self.depths_file)
            file_size_discharges = os.path.getsize(self.discharges_file)
            file_size_wetted_sections = os.path.getsize(self.wetted_sections_file)
        assert available_results <= file_size_depths and available_results <= file_size_discharges and available_results <= file_size_discharges and available_results <= file_size_wetted_sections,\
            f'The file sizes (.HEAD,.RH, .RQ, .RA) are not consistent.'


        # Extration of computed depths
        with open(self.depths_file,"rb") as depths_binary:
            depths_in_bytes = depths_binary.read(available_results)
            depths_data = np.frombuffer(depths_in_bytes, dtype= np.float32)
            depths = depths_data.reshape(cells_number, results_number, order='F') # The file is in fortran convention
            self.depths = np.roll(depths, 1, axis=0)

        # Extraction of computed discharges
        with open(self.discharges_file,"rb") as discharges_binary:
            discharges_in_bytes = discharges_binary.read(available_results)
            discharges_data = np.frombuffer(discharges_in_bytes, dtype= np.float32)
            discharges = discharges_data.reshape(cells_number, results_number, order='F') # The file is in fortran convention
            self.discharges = np.roll(discharges, 1, axis=0)

        # Extraction of computed wetted sections
        with open(self.wetted_sections_file,"rb") as wetted_sections_binary:
            wetted_sections_in_bytes = wetted_sections_binary.read(available_results)
            wetted_sections_data = np.frombuffer(wetted_sections_in_bytes, dtype= np.float32)
            wetted_sections = wetted_sections_data.reshape(cells_number, results_number, order='F') # The file is in fortran convention
            self.wetted_sections = np.roll(wetted_sections, 1, axis=0)

        self.velocities = self.discharges/self.wetted_sections
        # To avoid nan values, copy false means the original array is modified and returned.
        self.velocities = np.nan_to_num(self.velocities, copy=False)
        if self.breath_file != None:
            self.widths = np.loadtxt(self.breath_file)
            if self.widths.shape == self.wetted_sections.shape:
                self.froudes = self.discharges / (self.wetted_sections*np.sqrt(Constants.GRAVITATION.value*(self.wetted_sections/self.widths)))
                # To avoid nan values, copy false means the original array is modified and returned.
                self.froudes = np.nan_to_num(self.froudes, copy=False, nan=0.0, posinf=0.0,neginf=0.0)
            # In case the model has written new results
            else:
                if self.breath_directory != None:
                    self.breadth_list = os.listdir(self.breath_directory)
                    self.compute_froude()
        else:
            if self.breath_directory != None:
                self.breadth_list = os.listdir(self.breath_directory)
                self.compute_froude()
            else:
                self.breadth_list = None
                if self.cross_sections_file != None and self.support_file != None:
                    self.create_widths_and_froudes()
                else:
                    self.froudes = None
                    warnings.warn('Froude numbers will not be plotted due missing data.', UserWarning)

        # FIXME Implement an array for self.water_level using water depths and cordinates and use it in the code
        if self.vector_coordinates is None:
            self._vector_from_coordinates()
        self.water_levels = self.depths + np.array(self.z_coords)[:,None]

        assert self.depths.shape == self.discharges.shape == self.wetted_sections.shape == self.velocities.shape == self.water_levels.shape,\
            f'The reshape of results in numpy failed (different shapes instead of a unique one).'
        self.results_length =  self.depths.shape[1]
        self.depths_max = self.find_max(self.depths)
        self.discharges_max = self.find_max(self.discharges)
        self.wetted_sections_max = self.find_max(self.wetted_sections)
        self.velocities_max = self.find_max(self.velocities)
        # if self.froudes != None:
        self.froudes_max = self.find_max(self.froudes)
        self.water_level_ymax = self.depths_max + self.find_max(self.topo) # FIXME

        if self.banksbed_file is not None:
            self._river_banksbed(self.banksbed_file)
            # FIXME delete the unnecessary call of this function (self._river_banksbed) in the plotting methods

        # print('done')

    def get_closest_simulated_time_index(self, time:float)-> int:
        """Return the index of the closest time step to a given time.

        The closest time step is obtained by subtracting
        the provided time from all simulated times steps.
        The smallest difference is then used to find the index of
        closest time step.

        :param time: the desired time
        :type time: float
        :return: the index of the closest time step
        :rtype: int
        """
        assert time >= 0 and time <= self.simulated_times[-1],\
            f'The time ({time}) should be greater than 0 and less than the last simulated time - ({self.simulated_times[-1]})'
        dif_array = np.absolute(self.simulated_times - time)
        id = np.argmin(dif_array)
        return id

    def get_closest_simulated_results(self,
                                      time:float,
                                      node:int,
                                      which_results: Literal['water level',
                                                             'water depth',
                                                             'discharge',
                                                             'velocity',
                                                             'froude',
                                                             'wetted section',
                                                             'top width',
                                                             'all'] = 'all'
                                      )-> Union[float, dict]:
        """
        Return the simulated conditions (water level, water depth, discharge, velocity, froude, wetted section, top width
        ) at the closest time step to a given time.

        :param time: the desired time
        :type time: float
        :param node: the desired node
        :type node: int
        :return: the conditions at the closest time step
        :rtype: np.ndarray
        """
        id = self.get_closest_simulated_time_index(time)
        water_level = self.water_levels[node,id]
        depth = self.depths[node][id]
        disharge = self.discharges[node][id]
        velocity = self.velocities[node][id]
        froude = self.froudes[node][id]
        wetted_section = self.wetted_sections[node][id]
        top_width = self.widths[node][id]
        results = {'water level': water_level,
                   'water depth': depth,
                   'discharge': disharge,
                   'velocity': velocity,
                   'froude': froude,
                   'wetted section': wetted_section,
                   'top width': top_width}

        if which_results == 'all':

            return results
        else:
            return results[which_results]

    def update_ic_from_time_steps(self, time_step:int = -1) -> np.ndarray:
        """Return the simulated conditions (a,q,h, r) at a given time step as a `np.ndarray`.
            - a: Wetted section (index 0),
            - s: Wetted perimeter (index 1),
            - w: Top width (index 2),
            - r: Hydraulic radius (index 3).

        :param time_step: the desired time steps, defaults to -1
        :type time_step: int, optional
        :return: the conditions at the specified time step
        :rtype: np.ndarray
        """
        real_time_step = self.convert_time_step(time_step)
        for file in os.listdir(self.directory):
            if file.endswith(".aini"):
                aini_file = os.path.join(self.directory,file)
                wetted_sections = self.wetted_sections[:,real_time_step]
                self.update_ini_file(aini_file, wetted_sections)
            elif file.endswith(".hini"):
                hini_file = os.path.join(self.directory,file)
                depths = self.depths[:,real_time_step]
                self.update_ini_file(hini_file, depths)
            elif file.endswith(".zini"):
                zini_file = os.path.join(self.directory,file)
                water_level = self.water_levels[:,real_time_step]
                self.update_ini_file(zini_file, water_level)
            elif file.endswith(".qini"):
                qini_file = os.path.join(self.directory,file)
                discharges = self.discharges[:,real_time_step]
                self.update_ini_file(qini_file, discharges)


        # wetted_sections = self.wetted_sections[:,real_time_step]
        # discharges = self.discharges[:,real_time_step]
        # depths = self.depths[:,real_time_step]
        # wetted_perimeters = self.wetted_sections[:,real_time_step] # FIXME not yet available
        # top_widths = self.widths[:,real_time_step] # FIXME not yet available

    def update_ini_file(self, ini_file:str, new_values: np.ndarray)-> None:
        """Update the initial condition file with new values."""
        df = pd.read_csv(ini_file,
                         sep= Constants.SEPARATOR.value,
                         skiprows=1,
                         names=['skeleton', 'zone', 'segment','value']
                         )
        lgth_values = len(df['value'])
        lgth_new_values = len(new_values)
        assert lgth_values == lgth_new_values,\
            f"The length of the new values - {lgth_new_values} is not consistent with the initial condition file - {lgth_values}."

        df['value'] = new_values
        sep = Constants.SEPARATOR.value
        with open(ini_file, 'w') as f:
            f.write(f"{lgth_new_values}\n")
            for i in range(lgth_values):
                f.write(f"{df['skeleton'][i]}{sep}{df['zone'][i]}{sep}{df['segment'][i]}{sep}{str(df['value'][i])}\n")

    def get_one_node_evolution(self,
                                node:int = 0,
                                variable:Literal['water level', 'discharge', 'water depth', 'velocity', 'wetted section', 'froude'] = 'discharge',
                                first_time_step = 0,
                                last_time_step = -1 )-> np.ndarray:
        """Return the discharges at a given node (cross section) for all time steps.

        :param node: the desired node, defaults to 0
        :type node: int, optional
        :return: the discharges at the specified node for all time steps
        :rtype: np.ndarray
        """
        assert isinstance(node, int),\
            f"The node should be an integer greater than 0, not {node}."
        assert isinstance(first_time_step, int) and isinstance(last_time_step, int),\
            f"The time steps should be integers, not {first_time_step} and {last_time_step}."

        if variable == 'discharge':
            variable_data = self.discharges
        elif variable == 'water depth':
            variable_data = self.depths
        elif variable == 'water level':
            variable_data = self.water_levels
        elif variable == 'velocity':
            variable_data = self.velocities
        elif variable == 'wetted section':
            variable_data = self.wetted_sections
        elif variable == 'froude':
            variable_data = self.froudes
        else:
            raise ValueError(f"The variable {variable} is not available in results.")

        real_first_time_step = self.convert_time_step(first_time_step)
        real_last_time_step = self.convert_time_step(last_time_step)
        assert real_first_time_step < real_last_time_step,\
            f"The first time step should be less than the last time step, not {real_first_time_step} and {real_last_time_step}."

        if last_time_step == -1:
            data = variable_data[node,first_time_step:]
            time = self.simulated_times[first_time_step:]
        elif last_time_step < 0 and last_time_step != -1:
            data = variable_data[node,first_time_step: (last_time_step +1)]
            time = self.simulated_times[first_time_step: (last_time_step +1)]
        else:
            data = variable_data[node,first_time_step:last_time_step]
            time = self.simulated_times[first_time_step:last_time_step]
        node_data = pd.Series(data, index = time)
        return node_data

    def get_one_node_evolution_on_hydrograph_format(self,
                                             node:int = 0,
                                             variable: Literal['water level', 'discharge', 'water depth',
                                                               'velocity', 'wetted section', 'froude'] = 'discharge',
                                             first_time_step = 0,
                                             last_time_step = -1,
                                             ) -> Hydrograph:
        """Return  the hydrograph of a given node for a speiciified range of time steps.

        :param node: the desired node, defaults to 0
        :type node: int, optional
        :param first_time_step: the first time step, defaults to 0
        :type first_time_step: int, optional
        :param last_time_step: the last time step, defaults to -1
        :type last_time_step: int, optional
        :return: the hydrograph of the specified node
        :rtype: Hydrograph
        """

        node_data = self.get_one_node_evolution(node=node,variable=variable,first_time_step=first_time_step,last_time_step=last_time_step)
        return Hydrograph(node_data)

    def plot_water_level(self,
                         figax:tuple = None,
                         time_step:int = 1,
                         banksbed: Union[str, Zones] = '',
                         landmark: Union[str,Zones]= '',
                         save_as:str ='',
                         figsize:tuple = (20,10),
                         alpha =0.3,
                         grid_x_m:float= 1000.,
                         grid_y_m:float = 10.,
                         convert_step = True,
                         steps_limit = False,
                         show = True):
        """
        Plot the water level and
        return  the information associated with the the figure's axis.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to 10.
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Axe
        :rtype: Axes
        """
        # If a figure does not exist a figure is created with one axe.
        if figax is None:
            fig = plt.figure('Water level', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        # Convert the time step into a standardized version for other usages.
        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        # Test whether the vector defining the lowest point of each vector is defined
        # if not, the vector is created
        if self.vector_coordinates is None:
            self._vector_from_coordinates()


        # the left bank and the right bank of the river are provided.
        if banksbed != '':
            self._river_banksbed(banksbed)
            ax.plot(self.left_bank_curvi, self.z_bankleft, color= 'black', ls = 'dotted', lw = 0.5, alpha=1, label='Left bank')
            ax.plot(self.right_bank_curvi, self.z_bankright, color= 'black', ls = 'dashed', lw =0.5, alpha=1, label='Right bank')

        # Y data FIXME Change the addition with the indexation of the water level array avoid water depth in the methods
        depth =self.depths[:,real_time_step]
        # water_line = self.z_coords + depth
        water_line = self.water_levels[:,real_time_step]
        # In case the middle bed,

        # The graphs
        # Lowest points of the river bed
        ax.plot(self.s_coords, self.z_coords, color= 'black')
        water_level, = ax.plot(self.s_coords, water_line, color ='cyan', ls='-.', alpha=0.01)
        if banksbed != '':
            minimum_banks = np.minimum(self.z_bankleft,self.z_bankright)
            maximum_banks = np.maximum(self.z_bankleft,self.z_bankright)

            ax.fill_between(self.s_coords, self.z_coords, water_line, where =   minimum_banks[:-1] <= water_line,
                                            color = Colors.RIVER_COLOR.value,
                                            alpha = Constants.TRANSPARENCY_RIVER.value,
                                            interpolate=True, label='Below banks')

            ax.fill_between(self.s_coords, self.z_coords, water_line, where =   water_line <= maximum_banks[:-1],
                                            color = Colors.RIVER_COLOR.value,
                                            alpha = Constants.TRANSPARENCY_RIVER.value,
                                            interpolate=True)


            ax.fill_between(self.s_coords, self.z_bankright[:-1],  water_line, where =   self.z_bankright[:-1] < water_line,
                                            color =Colors.FLOODED_RIGHT.value, alpha=Constants.TRANSPARENCY_FLOOD.value,
                                            interpolate=True, label='Right flooded')

            ax.fill_between(self.s_coords, self.z_bankleft[:-1],  water_line, where =   self.z_bankleft[:-1] < water_line,
                                            color =Colors.FLOODED_LEFT.value, alpha=Constants.TRANSPARENCY_FLOOD.value,
                                            interpolate=True, label='Left flooded')

            ax.fill_between(self.s_coords, maximum_banks[:-1], water_line, where =   maximum_banks[:-1] <= water_line,
                                            color =Colors.FLOODED_ALL.value,
                                            alpha=Constants.TRANSPARENCY_FLOOD.value,interpolate=True, label='All flooded')

        ax.fill_between(self.s_coords, self.z_coords, y2=self.z_min,
                            color = 'black', alpha =0.2, label ='Bed', interpolate= True)

        # axis parameters
        ax.set_xlim(0, self.s_max)
        if banksbed != '':
            if steps_limit:
                y_max = max(max(self.z_bankleft) + self.depths_max, max(self.z_bankright)) + self.depths_max
            else:
                 y_max = max(max(self.z_bankleft), max(self.z_bankright)) + max(depth)
            ax.set_ylim(self.z_min, y_max)
            ax.yaxis.set_ticks(np.arange(self.z_min, y_max, grid_y_m))
        else:
            if steps_limit:
                y_max =max(water_line) +  self.depths_max
            else:
                y_max =max(water_line) + max(depth)

            ax.set_ylim(self.z_min, y_max)
            ax.yaxis.set_ticks(np.arange(self.z_min, y_max, grid_y_m))

        ax.set_ylabel('Altitude [m]')
        ax.set_xlabel('Length [m]')
        ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x_m))

        ax.grid()
        ax.set_title(f'Water level', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        if landmark != '':
            self._landmark(landmark,ax,real_time_step)
        ax.legend()
        if figax is None:
            if save_as != '':
                plt.savefig(save_as)
            if show:
                plt.tight_layout()
                plt.show()

        return water_level

    def _plot_water_level(self,
                         figax:tuple = None,
                         time_step:int = 1,
                         banksbed: Union[str, Zones] = '',
                         landmark: Union[str,Zones]= '',
                         save_as:str ='',
                         figsize:tuple = (20,10),
                         alpha =0.3,
                         grid_x_m:float= 1000.,
                         grid_y_m:float = 10.,
                         convert_step = True,
                         steps_limit = False,
                         show = True):
        """
        Deprecated method
        """
        if figax is None:
            fig = plt.figure('Water level', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y data
        depth =self.depths[:,real_time_step]
        water_line = self.z_coords + depth
        # In case the middle bed,
        # the left bank and the right bank of the river are provided.
        if banksbed != '':
            self._river_banksbed(banksbed)
            ax.plot(self.left_bank_curvi, self.z_bankleft, color= 'black', ls = 'dotted', lw = 0.5, alpha=1, label='Left bank')
            ax.plot(self.right_bank_curvi, self.z_bankright, color= 'black', ls = 'dashed', lw =0.5, alpha=1, label='Right bank')

        # The graphs
        # Lowest points of the river bed
        ax.plot(self.s_coords, self.z_coords, color= 'black')
        water_level, = ax.plot(self.s_coords, water_line, color ='cyan', ls='-.', alpha=alpha)
        ax.fill_between(self.s_coords, self.z_coords, water_line,where = self.z_coords <=water_line,
                                       color ='cyan', alpha=alpha, interpolate=True, label='Water level')
        ax.fill_between(self.s_coords,self.z_coords, y2=self.z_min,
                        color = 'black', alpha =0.2, label ='Bed', interpolate= True)
        if banksbed != '':
            ax.fill_between(self.s_coords, water_line, self.z_bankleft[:-1], where = water_line >= self.z_bankleft[:-1],
                                       color ='red', alpha=alpha, interpolate=True, label='Left flooded')
            ax.fill_between(self.s_coords, water_line, self.z_bankright[:-1], where = water_line >= self.z_bankright[:-1],
                                       color ='magenta', alpha=alpha, interpolate=True, label='Right flooded')

        # axis parameters
        ax.set_xlim(0, self.s_max)
        if banksbed != '':
            if steps_limit:
                y_max = max(max(self.z_bankleft) + self.depths_max, max(self.z_bankright)) + self.depths_max
            else:
                 y_max = max(max(self.z_bankleft), max(self.z_bankright)) + max(depth)
            ax.set_ylim(self.z_min, y_max)
            ax.yaxis.set_ticks(np.arange(self.z_min, y_max, grid_y_m))
        else:
            if steps_limit:
                y_max =max(water_line) +  self.depths_max
            else:
                y_max =max(water_line) + max(depth)

            ax.set_ylim(self.z_min, y_max)
            ax.yaxis.set_ticks(np.arange(self.z_min, y_max, grid_y_m))

        ax.set_ylabel('Altitude [m]')
        ax.set_xlabel('Length [m]')
        ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x_m))

        ax.grid()
        ax.set_title(f'Water level', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        if landmark != '':
            self._landmark(landmark,ax,real_time_step)
        ax.legend()
        if figax is None:
            if save_as != '':
                plt.savefig(save_as)
            if show:
                plt.show()

        return water_level

    def plot_line_water_level(self,
                            figax:tuple[Figure, Axes] = None,
                            time_step:int = 1,
                            banksbed: Union[str, Zones] = '',
                            landmark: Union[str,Zones]= '',
                            save_as:str ='',
                            figsize:tuple = (20,10),
                            alpha =0.3,
                            grid_x_m:float= 1000.,
                            grid_y_m:float = 10.,
                            convert_step = True,
                            steps_limit = False,
                            label:str ='',
                            color:str= 'blue',
                            linestyle = 'solid',
                            linewidth = 0.7,
                            show = True):
        """
        Plot the water level as a continous line and
        return  the information associated with the axe.

        Landmarks are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to 10.
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param label: Label, defaults to ''
        :type label: str, optional
        :param color: Color, defaults to 'blue'
        :type color: str, optional
        :param linestyle: Linestyle, defaults to 'solid'
        :type linestyle: str, optional
        :param linewidth: Linewidth, defaults to 0.7
        :type linewidth: float, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Water level
        :rtype: Line2D
        """

        if figax is None:
            fig = plt.figure('Water level', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y data
        depth =self.depths[:,real_time_step]
        # water_line = self.z_coords + depth
        water_line = self.water_levels[:,real_time_step]
        # In case the middle bed,
        # the left bank and the right bank of the river are provided.
        if banksbed != '':
            self._river_banksbed(banksbed)

        # The graphs
        if label =='':
            label = self.simulation_name
        water_level, = ax.plot(self.s_coords,
                               water_line,
                               color = color,
                               ls=linestyle,
                               linewidth=linewidth,
                               label = label)

        ax.legend()
        # axis parameters
        if fig is None:
            ax.set_xlim(0, self.s_max)
            if banksbed != '':
                if steps_limit:
                    y_max = max(max(self.z_bankleft) + self.depths_max, max(self.z_bankright)) + self.depths_max
                else:
                    y_max = max(max(self.z_bankleft), max(self.z_bankright)) + max(depth)
                ax.set_ylim(self.z_min, y_max)
                ax.yaxis.set_ticks(np.arange(self.z_min, y_max, grid_y_m))
            else:
                if steps_limit:
                    y_max =max(water_line) +  self.depths_max
                else:
                    y_max =max(water_line) + max(depth)

                ax.set_ylim(self.z_min, y_max)
                ax.yaxis.set_ticks(np.arange(self.z_min, y_max, grid_y_m))

            ax.set_ylabel('Altitude [m]')
            ax.set_xlabel('Length [m]')

            ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x_m))

            ax.grid()
            ax.set_title(f'Water level', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            if landmark != '':
                self._landmark(landmark,ax,real_time_step)
            # ax.legend()
            if figax is None:
                if save_as != '':
                    plt.savefig(save_as)
                # plt.show()

        # if show:
        #     fig.show()
        return water_level

    def plot_water_depth(self,
                         figax:tuple = None,
                         time_step:int = 1,
                         banksbed: Union[str, Zones] = '',
                         landmark: Union[str,Zones]= '',
                         save_as:str ='',
                         figsize:tuple = (20,10),
                         alpha =0.3,
                         grid_x_m:float= 1000.,
                         grid_y_m:float = .5,
                         convert_step = True,
                         steps_limit = False,
                         show = True
                         ):
        """
        Plot the water depth and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to .5
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Water depth
        :rtype: Line2D
        """

        if figax is None:
            fig = plt.figure('Water depth', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        depth =self.depths[:,real_time_step]
        # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)

        # plots
        water_depth, = ax.plot(self.s_coords, depth, color ='cyan', ls='-.')
        ax.fill_between(self.s_coords, depth,
                                       color ='cyan', alpha=alpha, interpolate=True, label='Water Depth')

        # axis parameters
        ax.set_xlim(0, self.s_max)
        if steps_limit:
            y_max = self.depths_max + 0.3* self.depths_max
        else:
            y_max = max(depth) + 0.3* max(depth)

        ax.set_ylim(0, y_max)
        ax.set_ylabel('Depth [m]')
        ax.set_xlabel('Length [m]')
        ax.xaxis.set_ticks(np.arange(0, self.s_max, grid_x_m))
        grid_y = self._yticks_update(y_max)
        ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
        ax.grid()
        ax.set_title(f'Water depth', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        if landmark != '':
            self._landmark(landmark,ax,real_time_step, variable='water depth')
        ax.legend()
        if figax is None:
            if save_as != '':
                plt.savefig(save_as)
            if show:
                plt.tight_layout()
                plt.show()

        return water_depth

    def plot_line_water_depth(self,
                            figax:tuple[Figure, Axes] = None,
                            time_step:int = 1,
                            banksbed: Union[str, Zones] = '',
                            landmark: Union[str,Zones]= '',
                            save_as:str ='',
                            figsize:tuple = (20,10),
                            alpha =0.3,
                            grid_x_m:float= 1000.,
                            grid_y_m:float = 10.,
                            convert_step = True,
                            steps_limit = False,
                            label:str ='',
                            color:str= 'blue',
                            linestyle = 'solid',
                            linewidth = 0.7,
                            show = True
                            ):
        """
        Plot the water depth as a line and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to 10.
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param label: Label, defaults to ''
        :type label: str, optional
        :param color: Color, defaults to 'blue'
        :type color: str, optional
        :param linestyle: Linestyle, defaults to 'solid'
        :type linestyle: str, optional
        :param linewidth: Linewidth, defaults to 0.7
        :type linewidth: float, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Water depth
        :rtype: Line2D
        """

        if figax is None:
            fig = plt.figure('Water depth', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        depth =self.depths[:,real_time_step]
        # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)

        # plots
        if label =='':
            label = self.simulation_name
        water_depth, = ax.plot(self.s_coords,
                               depth,
                               color =color,
                               ls=linestyle,
                               linewidth=linewidth,
                               label=label)
        # ax.fill_between(self.s_coords, depth,
        #                                color ='cyan', alpha=alpha, interpolate=True, label='Water Depth')

        # axis parameters
        ax.legend()
        if figax is None:
            ax.set_xlim(0, self.s_max)
            if steps_limit:
                y_max = self.depths_max + 0.3* self.depths_max
            else:
                y_max = max(depth) + 0.3* max(depth)

            ax.set_ylim(0, y_max)
            ax.set_ylabel('Depth [m]')
            ax.set_xlabel('Length [m]')
            ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x_m))
            grid_y = self._yticks_update(y_max)
            ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
            ax.grid()
            ax.set_title(f'Water depth', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            if landmark != '':
                self._landmark(landmark,ax,real_time_step, variable='water depth')
            if save_as != '':
                plt.savefig(save_as)
        # if show:
        #     fig.show()

        return water_depth

    def plot_discharges(self,
                         figax:tuple = None,
                         time_step:int = 1,
                         banksbed: Union[str, Zones] = '',
                         landmark: Union[str,Zones]= '',
                         save_as:str ='',
                         figsize:tuple = (20,10),
                         alpha =0.3,
                         grid_x_m:float= 1000.,
                         grid_y_m:float = None,
                         convert_step = True,
                         steps_limit = False,
                         show = True):
        """
        Plot the discharges and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to None
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Water discharge
        :rtype: Line2D
        """
        if figax is None:
            fig = plt.figure('Discharge', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        discharge =self.discharges[:,real_time_step]
         # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)
        # plots
        water_discharge, = ax.plot(self.s_coords, discharge, color ='red', ls='-.')
        ax.fill_between(self.s_coords, discharge,
                                       color ='red', alpha=alpha, interpolate=True, label='Discharge')

        # axis parameters
        ax.set_xlim(0, self.s_max)
        if steps_limit:
            y_max = self.discharges_max + 0.3*self.discharges_max
        else:
            y_max = max(discharge) + 0.3* max(discharge)

        ax.set_ylim(0, y_max)
        ax.set_ylabel('Discharges [m$^3$/s]')
        ax.set_xlabel('Length [m]')
        ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x_m))

        grid_y = self._yticks_update(y_max)
        ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
        ax.grid()
        ax.set_title(f'Discharge', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        if landmark != '':
            self._landmark(landmark,ax,real_time_step, variable='discharge')
        ax.legend()
        if figax is None:
            if save_as != '':
                plt.savefig(save_as)
            if show:
                plt.tight_layout()
                plt.show()

        return water_discharge

    def plot_line_discharges(self,
                            figax:tuple[Figure, Axes] = None,
                            time_step:int = 1,
                            banksbed: Union[str, Zones] = '',
                            landmark: Union[str,Zones]= '',
                            save_as:str ='',
                            figsize:tuple = (20,10),
                            alpha =0.3,
                            grid_x_m:float= 1000.,
                            grid_y_m:float = 10.,
                            convert_step = True,
                            steps_limit = False,
                            label:str ='',
                            color:str= 'blue',
                            linestyle = 'solid',
                            linewidth = 0.7,
                            show = True
                            ):
        """
        Plot the discharges as a line and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to 10.
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param label: Label, defaults to ''
        :type label: str, optional
        :param color: Color, defaults to 'blue'
        :type color: str, optional
        :param linestyle: Linestyle, defaults to 'solid'
        :type linestyle: str, optional
        :param linewidth: Linewidth, defaults to 0.7
        :type linewidth: float, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Water discharge
        :rtype: Line2D
        """

        if figax is None:
            fig = plt.figure('Discharge', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        discharge = self.discharges[:,real_time_step]
         # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)
        # plots
        if label =='':
            label = self.simulation_name
        water_discharge, = ax.plot(self.s_coords, discharge, color =color, ls=linestyle, linewidth=linewidth, label=label)
        # ax.fill_between(self.s_coords, discharge,
        #                                color ='red', alpha=alpha, interpolate=True, label='Discharge')

        # axis parameters
        ax.legend()

        if figax is None:
            ax.set_xlim(0, self.s_max)
            if steps_limit:
                y_max = self.discharges_max + 0.3*self.discharges_max
            else:
                y_max = max(discharge) + 0.3* max(discharge)

            ax.set_ylim(0, y_max)
            ax.set_ylabel('Discharges [m$^3$/s]')
            ax.set_xlabel('Length [m]')
            ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x_m))

            grid_y = self._yticks_update(y_max)
            ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
            ax.grid()
            ax.set_title(f'Discharge', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            if landmark != '':
                self._landmark(landmark,ax,real_time_step, variable='discharge')

            if figax is None:
                if save_as != '':
                    plt.savefig(save_as)
        # if show:
        #     fig.show()

        return water_discharge

    def plot_wetted_sections(self,
                         figax:tuple = None,
                         time_step:int = 1,
                         banksbed: Union[str, Zones] = '',
                         landmark: Union[str,Zones]= '',
                         save_as:str ='',
                         figsize:tuple = (20,10),
                         alpha =0.3,
                         grid_x:float= 1000.,
                         grid_y:float = None,
                         convert_step = True,
                         steps_limit = False,
                         show = True):
        """
        Plot the wetted sections and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x: Grid x, defaults to 1000.
        :type grid_x: float, optional
        :param grid_y: Grid y, defaults to None
        :type grid_y: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Wetted sections
        :rtype: Line2D
        """
        if figax is None:
            fig = plt.figure('Wetted Sections', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        wetted_setions =self.wetted_sections[:,real_time_step]
         # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)
        # plots
        wetted_setion, = ax.plot(self.s_coords, wetted_setions, color ='blue', ls='-.')
        ax.fill_between(self.s_coords, wetted_setions,
                                       color ='blue', alpha=alpha, interpolate=True, label='Wetted sections')

        # axis parameters
        ax.set_xlim(0, self.s_max)
        if steps_limit:
            y_max = self.wetted_sections_max + 0.3* self.wetted_sections_max
        else:
            y_max = max(wetted_setions) + 0.3* max(wetted_setions)
        ax.set_ylim(0, y_max)
        ax.set_ylabel('Wetted sections [m$^2$]')
        ax.set_xlabel('Length [m]')
        ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x))
        grid_y = self._yticks_update(y_max)
        ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
        ax.grid()
        ax.set_title(f'Wetted sections', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        if landmark != '':
            self._landmark(landmark,ax,real_time_step, variable='wetted sections')
        ax.legend()

        if figax is None:
            if save_as != '':
                plt.savefig(save_as)
            if show:
                plt.tight_layout()
                plt.show()
        return wetted_setion

    def plot_line_wetted_sections(self,
                                figax:tuple[Figure, Axes] = None,
                                time_step:int = 1,
                                banksbed: Union[str, Zones] = '',
                                landmark: Union[str,Zones]= '',
                                save_as:str ='',
                                figsize:tuple = (20,10),
                                alpha =0.3,
                                grid_x_m:float= 1000.,
                                grid_y_m:float = 10.,
                                convert_step = True,
                                steps_limit = False,
                                label:str ='',
                                color:str= 'blue',
                                linestyle = 'solid',
                                linewidth = 0.7,
                                show = True
                                ):
        """
        Plot the wetted sections as a line and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to 10.
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param label: Label, defaults to ''
        :type label: str, optional
        :param color: Color, defaults to 'blue'
        :type color: str, optional
        :param linestyle: Linestyle, defaults to 'solid'
        :type linestyle: str, optional
        :param linewidth: Linewidth, defaults to 0.7
        :type linewidth: float, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Wetted sections
        :rtype: Line2D
        """
        if figax is None:
            fig = plt.figure('Wetted Sections', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        wetted_setions =self.wetted_sections[:,real_time_step]
         # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)
        # plots
        if label =='':
            label = self.simulation_name
        wetted_setion, = ax.plot(self.s_coords,
                                 wetted_setions,
                                 color = color,
                                 ls = linestyle,
                                 lw = linewidth,
                                 label = label)

        # ax.fill_between(self.s_coords, wetted_setions,
        #                                color ='blue', alpha=alpha, interpolate=True, label='Wetted sections')
        ax.legend()
        if figax is None:
            # axis parameters
            ax.set_xlim(0, self.s_max)

            if steps_limit:
                y_max = self.wetted_sections_max + 0.3* self.wetted_sections_max
            else:
                y_max = max(wetted_setions) + 0.3* max(wetted_setions)
            ax.set_ylim(0, y_max)
            ax.set_ylabel('Wetted sections [m$^2$]')
            ax.set_xlabel('Length [m]')
            # ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x)) # FIXME gri_x
            grid_y = self._yticks_update(y_max)
            ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
            ax.grid()
            ax.set_title(f'Wetted sections', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            if landmark != '':
                self._landmark(landmark,ax,real_time_step, variable='wetted sections')


            if figax is None:
                if save_as != '':
                    plt.savefig(save_as)
                if show:
                    fig.show()
        return wetted_setion

    def plot_velocities(self,
                         figax:tuple = None,
                         time_step:int = 1,
                         banksbed: Union[str, Zones] = '',
                         landmark: Union[str,Zones]= '',
                         save_as:str ='',
                         figsize:tuple = (20,10),
                         alpha =0.3,
                         grid_x:float= 1000.,
                         grid_y:float = None,
                         convert_step = True,
                         steps_limit = False,
                         show = True):
        """
        Plot the velocities and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x: Grid x, defaults to 1000.
        :type grid_x: float, optional
        :param grid_y: Grid y, defaults to None
        :type grid_y: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Velocity
        :rtype: Line2D
        """

        if figax is None:
            fig = plt.figure('Velocities', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        velocities = self.velocities[:,real_time_step]
         # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)
        # plots
        velocity, = ax.plot(self.s_coords, velocities, color ='red', ls='-.')
        ax.fill_between(self.s_coords, velocities,
                                       color ='red', alpha=alpha, interpolate=True, label='Velocity')

        # axis parameters
        ax.set_xlim(0, self.s_max)
        if steps_limit:
            y_max = self.velocities_max + 0.3* self.velocities_max
        else:
            y_max = max(velocities) + 0.3* max(velocities)


        ax.set_ylim(0, y_max)
        ax.set_ylabel('Velocity [m/s]')
        ax.set_xlabel('Length [m]')
        ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x))
        grid_y = self._yticks_update(y_max)
        ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
        ax.grid()
        ax.set_title(f'Velocity', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        if landmark != '':
            self._landmark(landmark,ax,real_time_step, variable='velocity')
        ax.legend()

        if figax is None:
            if save_as != '':
                plt.savefig(save_as)
            if show:
                plt.tight_layout()
                plt.show()

        return velocity

    def plot_line_velocities(self,
                                figax:tuple[Figure, Axes] = None,
                                time_step:int = 1,
                                banksbed: Union[str, Zones] = '',
                                landmark: Union[str,Zones]= '',
                                save_as:str ='',
                                figsize:tuple = (20,10),
                                alpha =0.3,
                                grid_x_m:float= 1000.,
                                grid_y_m:float = 10.,
                                convert_step = True,
                                steps_limit = False,
                                label:str ='',
                                color:str= 'blue',
                                linestyle = 'solid',
                                linewidth = 0.7,
                                show = True
                                ):
        """
        Plot the velocities as a line and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to 10.
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param label: Label, defaults to ''
        :type label: str, optional
        :param color: Color, defaults to 'blue'
        :type color: str, optional
        :param linestyle: Linestyle, defaults to 'solid'
        :type linestyle: str, optional
        :param linewidth: Linewidth, defaults to 0.7
        :type linewidth: float, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Velocity
        :rtype: Line2D
        """

        if figax is None:
            fig = plt.figure('Velocities', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        velocities = self.velocities[:,real_time_step]
         # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)
        # plots
        if label =='':
            label = self.simulation_name
        velocity, = ax.plot(self.s_coords,
                            velocities,
                            color =color,
                            ls=linestyle,
                            lw=linewidth,
                            label= label)
        # ax.fill_between(self.s_coords, velocities,
        #                                color ='red', alpha=alpha, interpolate=True, label='Velocity')
        ax.legend()
        if figax is None:
            # axis parameters
            ax.set_xlim(0, self.s_max)
            if steps_limit:
                y_max = self.velocities_max + 0.3* self.velocities_max
            else:
                y_max = max(velocities) + 0.3* max(velocities)


            ax.set_ylim(0, y_max)
            ax.set_ylabel('Velocity [m/s]')
            ax.set_xlabel('Length [m]')
            # ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x)) FIXME
            grid_y = self._yticks_update(y_max)
            ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
            ax.grid()
            ax.set_title(f'Velocity', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            if landmark != '':
                self._landmark(landmark,ax,real_time_step, variable='velocity')


            if figax is None:
                if save_as != '':
                    plt.savefig(save_as)
                if show:
                    fig.show()
        return velocity

    def plot_froudes(self,
                    figax:tuple = None,
                    time_step:int = 1,
                    banksbed: Union[str, Zones] = '',
                    landmark: Union[str,Zones]= '',
                    save_as:str ='',
                    figsize:tuple = (20,10),
                    alpha =0.3,
                    grid_x:float= 1000.,
                    grid_y:float = None,
                    convert_step =True,
                    steps_limit = False,
                    show = True):
        """
        Plot the Froude numbers and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x: Grid x, defaults to 1000.
        :type grid_x: float, optional
        :param grid_y: Grid y, defaults to None
        :type grid_y: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Froude number
        :rtype: Line2D
        """

        if self.froudes is None:
            warnings.warn(f"The Froude values are not available.\n\
                             Check the presence of a top width file in the simulation's repository.", UserWarning)
            return
            # self.compute_froude()
            # try:
            #     self.compute_froude()
            # except:
            #     warnings.warn(f"The Froude values are not available.\n\
            #                 Check the presence of a top width file in the simulation's repository.", UserWarning)
            #     return

        if figax is None:
            fig = plt.figure('Froude', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        froudes = self.froudes[:,real_time_step]
         # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)
        # plots
        froude, = ax.plot(self.s_coords, froudes, color ='blue', ls='-.')
        ax.fill_between(self.s_coords, froudes,
                                       color ='blue', alpha=alpha, interpolate=True, label='Subcritical')
        ax.fill_between(self.s_coords, froudes,y2 =1, where= 1<= froudes,
                                       color ='blue', alpha=1, interpolate=True, label='Supercritical')
        ax.hlines([1], 0, self.s_max, colors='red',linestyles= 'dotted')

        # axis parameters
        ax.set_xlim(0, self.s_max)
        if steps_limit:
            y_max = self.froudes_max + 0.3* self.froudes_max
        else:
            y_max = max(froudes) + 0.3* max(froudes)

        ax.set_ylim(0, y_max)
        ax.set_ylabel('Froude number')
        ax.set_xlabel('Length [m]')
        ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x))
        grid_y = self._yticks_update(y_max)
        ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
        ax.grid()
        ax.set_title(f'Froude number', fontdict={'fontsize': 'large', 'fontweight':'bold'})
        if landmark != '':
            self._landmark(landmark,ax,real_time_step, variable='froude')
        ax.legend()

        if figax is None:
            if save_as != '':
                plt.savefig(save_as)
            if show:
                plt.show()
        return froude

    def plot_line_froudes(self,
                    figax:tuple[Figure, Axes] = None,
                    time_step:int = 1,
                    banksbed: Union[str, Zones] = '',
                    landmark: Union[str,Zones]= '',
                    save_as:str ='',
                    figsize:tuple = (20,10),
                    alpha =0.3,
                    grid_x_m:float= 1000.,
                    grid_y_m:float = 10.,
                    convert_step = True,
                    steps_limit = False,
                    label:str ='',
                    color:str= 'blue',
                    linestyle = 'solid',
                    linewidth = 0.7,
                    show = True
                    ):
        """
        Plot the Froude numbers as a line and
        return  the information associated with the axe.

        Landmarks: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param figax: Figure and axe
        :type figax: tuple, optional
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x_m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y_m, defaults to 10.
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        :param label: Label, defaults to ''
        :type label: str, optional
        :param color: Color, defaults to 'blue'
        :type color: str, optional
        :param linestyle: Linestyle, defaults to 'solid'
        :type linestyle: str, optional
        :param linewidth: Linewidth, defaults to 0.7
        :type linewidth: float, optional
        :param show: Show, defaults to True
        :type show: bool, optional
        :return: Froude number
        :rtype: Line2D
        """

        if self.froudes is None:
            warnings.warn(f"The Froude values are not available.\n\
                             Check the presence of a top width file in the simulation's repository.", UserWarning)
            return
            # self.compute_froude()
            # try:
            #     self.compute_froude()
            # except:
            #     warnings.warn(f"The Froude values are not available.\n\
            #                 Check the presence of a top width file in the simulation's repository.", UserWarning)
            #     return

        if figax is None:
            fig = plt.figure('Froude', figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            fig,ax = figax

        if convert_step == True:
            real_time_step = self.convert_time_step(time_step)
        else:
            real_time_step = time_step

        if self.vector_coordinates is None:
            self._vector_from_coordinates()

        # Y-data
        froudes = self.froudes[:,real_time_step]
         # For plot harmony (curviline distances)
        if banksbed != '':
            if self.s_curvi == None:
                self._river_banksbed(banksbed)
        # plots
        if label =='':
            label = self.simulation_name
        froude, = ax.plot(self.s_coords,
                          froudes,
                          color =color,
                          ls=linestyle,
                          lw= linewidth,
                          label=label)
        # ax.fill_between(self.s_coords, froudes,
        #                                color ='blue', alpha=alpha, interpolate=True, label='Subcritical')
        # ax.fill_between(self.s_coords, froudes,y2 =1, where= 1<= froudes,
        #                                color ='blue', alpha=1, interpolate=True, label='Supercritical')
        # ax.hlines([1], 0, self.s_max, colors='red',linestyles= 'dotted')

        # axis parameters
        ax.legend()
        if figax is None:
            ax.set_xlim(0, self.s_max)
            if steps_limit:
                y_max = self.froudes_max + 0.3* self.froudes_max
            else:
                y_max = max(froudes) + 0.3* max(froudes)

            ax.set_ylim(0, y_max)
            ax.set_ylabel('Froude number')
            ax.set_xlabel('Length [m]')
            # ax.xaxis.set_ticks(np.arange(0, self.s_max,grid_x))
            grid_y = self._yticks_update(y_max)
            ax.yaxis.set_ticks(np.arange(0, y_max,grid_y))
            ax.grid()
            ax.set_title(f'Froude number', fontdict={'fontsize': 'large', 'fontweight':'bold'})
            if landmark != '':
                self._landmark(landmark,ax,real_time_step, variable='froude')


            if figax is None:
                if save_as != '':
                    plt.savefig(save_as)
                if show:
                    fig.show()
        return froude

    def create_axis(self, figures: list):
        '''
        Return the predefined matplolib index(es)
        used to create the figure's axes
        based on their number.

        :param figures: List of figures
        :type figures: list
        :return: List of axes
        :rtype: list
        '''
        nb_figures = len(figures)
        if nb_figures == 1:
            axes =[111]
        elif nb_figures ==2:
            axes = [211, 212]
        elif nb_figures == 3:
            axes = [311,312,313]
        elif nb_figures == 4:
            axes = [221,222,223,224]
        else:
            axes = [231,232,233,234,235,236]
        return axes

    def plot_variables(self,
                        figures:list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']] =['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'],
                        time_step:int = 1,
                        banksbed: Union[str, Zones] = '',
                        landmark: Union[str,Zones]= '',
                        save_as:str ='',
                        figsize:tuple = (30,10),
                        alpha:float = 0.3,
                        show = True,
                        steps_limit = True,
                        grid_x_m = 1000,
                        grid_y_m =10) -> list[tuple[Line2D,Axes, Figure]]:
        """
        Plot the selected variables in figures and
        return  the information associated with their axes.


        :param figures: List of spefic figures to be plotted,
        defaults to ['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']
        :type figures: list
        :param time_step: Desired results (time step) to be plotted, defaults to 1
        :type time_step: int, optional
        :param banksbed: Bed and banks of the river, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Size of the figure, defaults to (30,10)
        :type figsize: tuple, optional
        :param alpha: figure transparency, defaults to 0.3
        :type alpha: float, optional
        :param show: Should the figure be shown, defaults to True
        :type show: bool, optional
        :param steps_limit: Steps limit, defaults to True
        :type steps_limit: bool, optional
        :return: List of axes
        :rtype: list
        """


        fig = plt.figure('Simulated variables', figsize=figsize, facecolor='white')

        real_time_step = self.convert_time_step(time_step)
        new_axes = self.create_axis(figures)
        axes_for_updates = copy.deepcopy(new_axes)

        # axes_for_updates = []
        if 'water level' in figures:
            wl_id= figures.index('water level')
            ax1 = fig.add_subplot(new_axes[wl_id])
            # id_water_level = figures.index('water level')
            # ax1 = fig.add_subplot(231)
            water_level = self.plot_water_level((fig, ax1),
                                                real_time_step,
                                                banksbed,
                                                landmark,
                                                save_as,
                                                grid_x_m = grid_x_m,
                                                grid_y_m = grid_y_m,
                                                convert_step = False,
                                                steps_limit = steps_limit)
            # axes_for_updates.append((water_level,ax1,fig))
            axes_for_updates[wl_id] = (water_level,ax1,fig)

        # else:
        #     axes_for_updates.append(False)

        if 'water depth' in figures:
            h_id= figures.index('water depth')
            ax2 = fig.add_subplot(new_axes[h_id])
            # ax2 = fig.add_subplot(234)
            water_depth =self.plot_water_depth((fig, ax2),
                                               real_time_step,
                                               banksbed,
                                               landmark,
                                               save_as,
                                               grid_x_m = grid_x_m,
                                               grid_y_m = grid_y_m,
                                               convert_step=False,
                                               steps_limit=steps_limit)
            # axes_for_updates.append((water_depth,ax2,fig))
            axes_for_updates[h_id] = (water_depth,ax2,fig)
        # else:
        #     axes_for_updates.append(False)

        if 'discharge' in figures:
            q_id= figures.index('discharge')
            ax3 = fig.add_subplot(new_axes[q_id])
            # ax3 = fig.add_subplot(232)
            discharge = self.plot_discharges((fig, ax3),
                                             real_time_step,
                                             banksbed,
                                             landmark,
                                             save_as,
                                             grid_x_m = grid_x_m,
                                             grid_y_m = grid_y_m,
                                             convert_step=False,
                                             steps_limit=steps_limit)
            # axes_for_updates.append((discharge,ax3,fig))
            axes_for_updates[q_id]= (discharge,ax3,fig)
        # else:
        #     axes_for_updates.append(False)

        if 'wetted section' in figures:
            a_id= figures.index('wetted section')
            ax4 = fig.add_subplot(new_axes[a_id])
            # ax4 = fig.add_subplot(233)
            wetted_section = self.plot_wetted_sections((fig, ax4),
                                                       real_time_step,
                                                       banksbed,
                                                       landmark,
                                                       save_as,
                                                       grid_x = grid_x_m,
                                                       grid_y = grid_y_m,
                                                       convert_step=False,
                                                       steps_limit=steps_limit)
            # axes_for_updates.append((wetted_section,ax4,fig))
            axes_for_updates[a_id] = (wetted_section,ax4,fig)
        # else:
        #     axes_for_updates.append(False)

        if 'velocity' in figures:
            v_id= figures.index('velocity')
            ax5 = fig.add_subplot(new_axes[v_id])
            # ax5 = fig.add_subplot(235)
            velocity = self.plot_velocities((fig, ax5),
                                            real_time_step,
                                            banksbed,
                                            landmark,
                                            save_as,
                                            grid_x = grid_x_m,
                                            grid_y= grid_y_m,
                                            convert_step=False,
                                            steps_limit=steps_limit)
            # axes_for_updates.append((velocity,ax5,fig))
            axes_for_updates[v_id] = (velocity,ax5,fig)
        # else:
        #     axes_for_updates.append(False)

        if 'froude' in figures:
            fr_id= figures.index('froude')
            ax6 = fig.add_subplot(new_axes[fr_id])
            # ax6 = fig.add_subplot(236)
            froude = self.plot_froudes((fig, ax6),
                                       real_time_step,
                                       banksbed,
                                       landmark,
                                       save_as,
                                       grid_x = grid_x_m,
                                       grid_y = grid_y_m,
                                       convert_step=False,
                                       steps_limit=steps_limit)
            # axes_for_updates.append((froude,ax6,fig))
            axes_for_updates[fr_id] = (froude, ax6, fig)
        # else:
        #     axes_for_updates.append(False)

        fig.suptitle(f'Results - 1D model\n$Time: (step: {real_time_step+1} - $simulated: {self.simulated_times[real_time_step]:#.1f}s$ - real: {self.real_times[real_time_step]:#.1e} s)$',
                        fontsize= 'x-large', fontweight= 'bold')

        plt.tight_layout()
        if save_as != '':
            plt.savefig(save_as)
        if show:
            # plt.tight_layout()
            plt.show()



        return axes_for_updates

    def animate_1D_plots(self,
                            figures:list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']] =['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'],
                            time_step:int = 1,
                            banksbed: Union[str, Zones] = '',
                            landmark: Union[str,Zones]= '',
                            figsize:tuple = (20,10),
                            alpha:float = 0.3,
                            save_as:str='',
                            grid_x = 1000,
                            grid_y = 10):
        """
        Animate the selected variables in figures, save them as a file and
        return  the information associated with their axes.

        FIXME: implement multiprocesses to speed up the process.

        :param figures: List of figures
        :type figures: list
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :return: List of axes
        :rtype: list
        """

        animation_axes = self.plot_variables(figures,
                                  time_step,
                                  banksbed,
                                  landmark= landmark,
                                  figsize=figsize,
                                  alpha=alpha,
                                  grid_x_m = grid_x,
                                  grid_y_m = grid_y,
                                  show=False)
        for charactetristic in animation_axes:
                if len(charactetristic) == 3:
                    fig = charactetristic[2]
                    break
        real_time_step = self.convert_time_step(time_step)
        new_axes = self.create_axis(figures)
        if banksbed != '':
            minimum_banks = np.minimum(self.z_bankleft,self.z_bankright)
            maximum_banks = np.maximum(self.z_bankleft,self.z_bankright)

        # animation_axes = figure_charateristics[0]
        # fig = figure_charateristics[-1]
        def _update_plots(i:int):
            index = i + real_time_step -1
            h = self.depths[:, index]
            wl= self.z_coords + h
            q = self.discharges[:, index]
            a = self.wetted_sections[:, index]
            v = self.velocities[:, index]
            # if self.froudes != None:
            fr = self.froudes[:, index]

            if 'water level' in figures:
                wl_id= figures.index('water level')
                water_level = animation_axes[wl_id][0]
                ax_wl = animation_axes[wl_id][1]
                water_level.set_data(self.s_coords,wl)
                for coll in ax_wl.collections:
                    coll.remove()
                # ax_wl.collections.clear()
                # ax_wl.fill_between(self.s_coords,
                #                 self.z_coords,
                #                 wl,
                #                 where=self.z_coords <= wl,
                #                 facecolor='cyan',
                #                 alpha=0.3,
                #                 interpolate=True )

                if banksbed != '':

                    ax_wl.fill_between(self.s_coords, self.z_coords, wl, where =   minimum_banks[:-1] <= wl,
                                                    color = Colors.RIVER_COLOR.value,
                                                    alpha = Constants.TRANSPARENCY_RIVER.value,
                                                    interpolate=True, label='Below banks')
                    ax_wl.fill_between(self.s_coords, self.z_coords, wl, where =   wl <= maximum_banks[:-1],
                                                    color = Colors.RIVER_COLOR.value,
                                                    alpha = Constants.TRANSPARENCY_RIVER.value,
                                                    interpolate=True)


                    ax_wl.fill_between(self.s_coords, self.z_bankright[:-1],  wl, where =   self.z_bankright[:-1] < wl,
                                                    color =Colors.FLOODED_RIGHT.value, alpha=Constants.TRANSPARENCY_FLOOD.value,
                                                    interpolate=True, label='Right flooded')

                    ax_wl.fill_between(self.s_coords, self.z_bankleft[:-1],  wl, where =   self.z_bankleft[:-1] < wl,
                                                    color =Colors.FLOODED_LEFT.value, alpha=Constants.TRANSPARENCY_FLOOD.value,
                                                    interpolate=True, label='left flooded')

                    ax_wl.fill_between(self.s_coords, maximum_banks[:-1], wl, where =   maximum_banks[:-1] <= wl,
                                                    color =Colors.FLOODED_ALL.value,
                                                    alpha=Constants.TRANSPARENCY_FLOOD.value,interpolate=True, label='All flooded')

                ax_wl.fill_between(self.s_coords,
                                self.z_coords,
                                y2 = self.z_min,
                                color='black',
                                label ='topo',
                                alpha =0.3
                                    )

                # # to be verified
                if banksbed != '':
                    ax_wl.fill_between(self.s_coords, wl, self.z_bankleft[:-1], where = wl >= self.z_bankleft[:-1],
                                            color ='red', alpha=alpha, interpolate=True, label='Left flooded')
                    ax_wl.fill_between(self.s_coords, wl, self.z_bankright[:-1], where = wl >= self.z_bankright[:-1],
                                            color ='magenta', alpha=alpha, interpolate=True, label='Right flooded')

                if landmark != '':
                    self._landmark(landmark,ax_wl,index, variable='water level', text= False)
                # ax_wl.grid()

            if 'water depth' in figures:
                h_id= figures.index('water depth')
                water_depth = animation_axes[h_id][0]
                ax_h = animation_axes[h_id][1]
                water_depth.set_data(self.s_coords, h)
                for coll in ax_h.collections:
                    coll.remove()
                # ax_h.collections.clear()
                ax_h.fill_between(self.s_coords, h, facecolor= 'cyan', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_h,index, variable='water depth', text= False)

            if 'discharge' in figures:
                q_id= figures.index('discharge')
                discharge = animation_axes[q_id][0]
                ax_q = animation_axes[q_id][1]
                discharge.set_data(self.s_coords,q)
                for coll in ax_q.collections:
                    coll.remove()
                # ax_q.collections.clear()
                ax_q.fill_between(self.s_coords, q, facecolor= 'red', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_q,index, variable='discharge', text= False)

            if 'wetted section' in figures:
                a_id= figures.index('wetted section')
                wetted_section= animation_axes[a_id][0]
                ax_a = animation_axes[a_id][1]
                wetted_section.set_data(self.s_coords, a)
                for coll in ax_a.collections:
                    coll.remove()
                # ax_a.collections.clear()
                ax_a.fill_between(self.s_coords, a, facecolor= 'blue', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_a,index, variable='wetted sections', text= False)

            if 'velocity' in figures:
                v_id= figures.index('velocity')
                velocity = animation_axes[v_id][0]
                ax_v = animation_axes[v_id][1]
                velocity.set_data(self.s_coords, v)
                for coll in ax_v.collections:
                    coll.remove()
                # ax_v.collections.clear()
                ax_v.fill_between(self.s_coords, v, facecolor= 'red', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_v,index, variable='velocity', text= False)

            if 'froude' in figures:
                fr_id= figures.index('froude')
                froude = animation_axes[fr_id][0]
                ax_fr = animation_axes[fr_id][1]
                froude.set_data(self.s_coords, fr)
                for coll in ax_fr.collections:
                    coll.remove()
                # ax_fr.collections.clear()
                # ax_fr.fill_between(self.s_coords, fr, facecolor= 'blue', alpha= 0.3, interpolate=True)

                ax_fr.fill_between(self.s_coords, fr,
                                       color ='blue', alpha=alpha, interpolate=True, label='Subcritical')
                ax_fr.fill_between(self.s_coords, fr,y2 =1, where= 1<= fr,
                                       color ='blue', alpha=1, interpolate=True, label='Supercritical')

                ax_fr.hlines([1], 0, self.s_max, colors='red',linestyles= 'dotted')
                if landmark != '':
                    self._landmark(landmark,ax_fr,index, variable='froude', text= False)


            fig.suptitle(f'Results - 1D model\n$Time: (step: {index+1} - $simulated: {self.simulated_times[index+1]:#.1f}s$ - real: {self.real_times[index+1]:#.1e} s)$',
                        fontsize= 'x-large', fontweight= 'bold')


        rcParams['animation.embed_limit'] = 2**128 # Maximum size gif
        ani = animation.FuncAnimation(fig,
                                    _update_plots,
                                    interval = 200,
                                    blit = False,
                                    frames = self.simulated_times.shape[0] - real_time_step,
                                    repeat_delay = 100)

        if save_as != '':
            writergif = animation.PillowWriter(fps=5)
            ani.save(save_as, writer=writergif)

        return HTML(ani.to_jshtml())

    def ____FIXMEanimate_1D_plots(self,
                            figures:list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']] =['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'],
                            time_step:int = 1,
                            banksbed: Union[str, Zones] = '',
                            landmark: Union[str,Zones]= '',
                            figsize:tuple = (20,10),
                            alpha:float = 0.3,
                            save_as:str='',
                            grid_x = 1000,
                            grid_y = 10):
        """
        Animate the selected variables in figures, save them as a file and
        return  the information associated with their axes.

        FIXME: implement multiprocesses to speed up the process.

        :param figures: List of figures
        :type figures: list
        :param time_step: Time step, defaults to 1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param figsize: Figsize, defaults to (20,10)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :return: List of axes
        :rtype: list
        """

        animation_axes = self.plot_variables(figures,
                                  time_step,
                                  banksbed,
                                  landmark= landmark,
                                  figsize=figsize,
                                  alpha=alpha,
                                  grid_x_m = grid_x,
                                  grid_y_m = grid_y,
                                  show=False)
        for charactetristic in animation_axes:
                if len(charactetristic) == 3:
                    fig = charactetristic[2]
                    break
        real_time_step = self.convert_time_step(time_step)
        new_axes = self.create_axis(figures)
        if banksbed != '':
            minimum_banks = np.minimum(self.z_bankleft,self.z_bankright)
            maximum_banks = np.maximum(self.z_bankleft,self.z_bankright)

        # animation_axes = figure_charateristics[0]
        # fig = figure_charateristics[-1]
        def _update_plots(i:int):
            index = i + real_time_step -1
            h = self.depths[:, index]
            wl= self.z_coords + h
            q = self.discharges[:, index]
            a = self.wetted_sections[:, index]
            v = self.velocities[:, index]
            # if self.froudes != None:
            fr = self.froudes[:, index]

            if 'water level' in figures:
                wl_id= figures.index('water level')
                water_level = animation_axes[wl_id][0]
                ax_wl = animation_axes[wl_id][1]
                water_level.set_data(self.s_coords,wl)
                ax_wl.collections.clear()
                # ax_wl.fill_between(self.s_coords,
                #                 self.z_coords,
                #                 wl,
                #                 where=self.z_coords <= wl,
                #                 facecolor='cyan',
                #                 alpha=0.3,
                #                 interpolate=True )

                if banksbed != '':

                    ax_wl.fill_between(self.s_coords, self.z_coords, wl, where =   minimum_banks[:-1] <= wl,
                                                    color = Colors.RIVER_COLOR.value,
                                                    alpha = Constants.TRANSPARENCY_RIVER.value,
                                                    interpolate=True, label='Below banks')
                    ax_wl.fill_between(self.s_coords, self.z_coords, wl, where =   wl <= maximum_banks[:-1],
                                                    color = Colors.RIVER_COLOR.value,
                                                    alpha = Constants.TRANSPARENCY_RIVER.value,
                                                    interpolate=True)


                    ax_wl.fill_between(self.s_coords, self.z_bankright[:-1],  wl, where =   self.z_bankright[:-1] < wl,
                                                    color =Colors.FLOODED_RIGHT.value, alpha=Constants.TRANSPARENCY_FLOOD.value,
                                                    interpolate=True, label='Right flooded')

                    ax_wl.fill_between(self.s_coords, self.z_bankleft[:-1],  wl, where =   self.z_bankleft[:-1] < wl,
                                                    color =Colors.FLOODED_LEFT.value, alpha=Constants.TRANSPARENCY_FLOOD.value,
                                                    interpolate=True, label='left flooded')

                    ax_wl.fill_between(self.s_coords, maximum_banks[:-1], wl, where =   maximum_banks[:-1] <= wl,
                                                    color =Colors.FLOODED_ALL.value,
                                                    alpha=Constants.TRANSPARENCY_FLOOD.value,interpolate=True, label='All flooded')

                ax_wl.fill_between(self.s_coords,
                                self.z_coords,
                                y2 = self.z_min,
                                color='black',
                                label ='topo',
                                alpha =0.3
                                    )

                # # to be verified
                if banksbed != '':
                    ax_wl.fill_between(self.s_coords, wl, self.z_bankleft[:-1], where = wl >= self.z_bankleft[:-1],
                                            color ='red', alpha=alpha, interpolate=True, label='Left flooded')
                    ax_wl.fill_between(self.s_coords, wl, self.z_bankright[:-1], where = wl >= self.z_bankright[:-1],
                                            color ='magenta', alpha=alpha, interpolate=True, label='Right flooded')

                if landmark != '':
                    self._landmark(landmark,ax_wl,index, variable='water level', text= False)
                # ax_wl.grid()

            if 'water depth' in figures:
                h_id= figures.index('water depth')
                water_depth = animation_axes[h_id][0]
                ax_h = animation_axes[h_id][1]
                water_depth.set_data(self.s_coords, h)
                ax_h.collections.clear()
                ax_h.fill_between(self.s_coords, h, facecolor= 'cyan', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_h,index, variable='water depth', text= False)

            if 'discharge' in figures:
                q_id= figures.index('discharge')
                discharge = animation_axes[q_id][0]
                ax_q = animation_axes[q_id][1]
                discharge.set_data(self.s_coords,q)
                ax_q.collections.clear()
                ax_q.fill_between(self.s_coords, q, facecolor= 'red', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_q,index, variable='discharge', text= False)

            if 'wetted section' in figures:
                a_id= figures.index('wetted section')
                wetted_section= animation_axes[a_id][0]
                ax_a = animation_axes[a_id][1]
                wetted_section.set_data(self.s_coords, a)
                ax_a.collections.clear()
                ax_a.fill_between(self.s_coords, a, facecolor= 'blue', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_a,index, variable='wetted sections', text= False)

            if 'velocity' in figures:
                v_id= figures.index('velocity')
                velocity = animation_axes[v_id][0]
                ax_v = animation_axes[v_id][1]
                velocity.set_data(self.s_coords, v)
                ax_v.collections.clear()
                ax_v.fill_between(self.s_coords, v, facecolor= 'red', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_v,index, variable='velocity', text= False)

            if 'froude' in figures:
                fr_id= figures.index('froude')
                froude = animation_axes[fr_id][0]
                ax_fr = animation_axes[fr_id][1]
                froude.set_data(self.s_coords, fr)
                ax_fr.collections.clear()
                # ax_fr.fill_between(self.s_coords, fr, facecolor= 'blue', alpha= 0.3, interpolate=True)

                ax_fr.fill_between(self.s_coords, fr,
                                       color ='blue', alpha=alpha, interpolate=True, label='Subcritical')
                ax_fr.fill_between(self.s_coords, fr,y2 =1, where= 1<= fr,
                                       color ='blue', alpha=1, interpolate=True, label='Supercritical')

                ax_fr.hlines([1], 0, self.s_max, colors='red',linestyles= 'dotted')
                if landmark != '':
                    self._landmark(landmark,ax_fr,index, variable='froude', text= False)


            fig.suptitle(f'Results - 1D model\n$Time: (step: {index+1} - $simulated: {self.simulated_times[index+1]:#.1f}s$ - real: {self.real_times[index+1]:#.1e} s)$',
                        fontsize= 'x-large', fontweight= 'bold')

            # pillow_image = Image.frombytes('RGB',fig.canvas.get_width_height(),fig.canvas.tostring_rgb())

        rcParams['animation.embed_limit'] = 2**128 # Maximum size gif
        ani = animation.FuncAnimation(fig,
                                    _update_plots,
                                    interval = 200,
                                    blit = False,
                                    frames = self.simulated_times.shape[0] - real_time_step,
                                    repeat_delay = 100)

        if save_as != '':
            writergif = animation.PillowWriter(fps=5)
            ani.save(save_as, writer=writergif)

        return HTML(ani.to_jshtml())

    def _animate_1D_plots(self,
                            figures:list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']] =['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'],
                            time_step:int = 1,
                            banksbed: Union[str, Zones] = '',
                            landmark: Union[str,Zones]= '',
                            figsize:tuple = (20,10),
                            alpha:float = 0.3,
                            save_as:str=''):
        r"""
        /!\ Deprecating
        Animate the selected variables in figures, save them as a file and
        return  the information associated with their axes.
        """

        animation_axes = self.plot_variables(figures,
                                  time_step,
                                  banksbed,
                                  landmark= landmark,
                                  figsize=figsize,
                                  alpha=alpha,
                                  show=False)
        for charactetristic in animation_axes:
                if len(charactetristic) == 3:
                    fig = charactetristic[2]
                    break
        real_time_step = self.convert_time_step(time_step)
        new_axes = self.create_axis(figures)

        # animation_axes = figure_charateristics[0]
        # fig = figure_charateristics[-1]
        def _update_plots(i:int):
            index = i + real_time_step -1
            h = self.depths[:, index]
            wl= self.z_coords + h
            q = self.discharges[:, index]
            a = self.wetted_sections[:, index]
            v = self.velocities[:, index]
            # if self.froudes != None:
            fr = self.froudes[:, index]



            if 'water level' in figures:
                wl_id= figures.index('water level')
                water_level = animation_axes[wl_id][0]
                ax_wl = animation_axes[wl_id][1]
                water_level.set_data(self.s_coords,wl)
                ax_wl.collections.clear()
                ax_wl.fill_between(self.s_coords,
                                self.z_coords,
                                wl,
                                where=self.z_coords <= wl,
                                facecolor='cyan',
                                alpha=0.3,
                                interpolate=True )

                ax_wl.fill_between(self.s_coords,
                                self.z_coords,
                                y2 = self.z_min,
                                color='black',
                                label ='topo',
                                alpha =0.3
                                    )

                # # to be verified
                if banksbed != '':
                    ax_wl.fill_between(self.s_coords, wl, self.z_bankleft[:-1], where = wl >= self.z_bankleft[:-1],
                                            color ='red', alpha=alpha, interpolate=True, label='Left flooded')
                    ax_wl.fill_between(self.s_coords, wl, self.z_bankright[:-1], where = wl >= self.z_bankright[:-1],
                                            color ='magenta', alpha=alpha, interpolate=True, label='Right flooded')

                if landmark != '':
                    self._landmark(landmark,ax_wl,index, variable='water level', text= False)
                # ax_wl.grid()

            if 'water depth' in figures:
                h_id= figures.index('water depth')
                water_depth = animation_axes[h_id][0]
                ax_h = animation_axes[h_id][1]
                water_depth.set_data(self.s_coords, h)
                ax_h.collections.clear()
                ax_h.fill_between(self.s_coords, h, facecolor= 'cyan', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_h,index, variable='water depth', text= False)

            if 'discharge' in figures:
                q_id= figures.index('discharge')
                discharge = animation_axes[q_id][0]
                ax_q = animation_axes[q_id][1]
                discharge.set_data(self.s_coords,q)
                ax_q.collections.clear()
                ax_q.fill_between(self.s_coords, q, facecolor= 'red', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_q,index, variable='discharge', text= False)

            if 'wetted section' in figures:
                a_id= figures.index('wetted section')
                wetted_section= animation_axes[a_id][0]
                ax_a = animation_axes[a_id][1]
                wetted_section.set_data(self.s_coords, a)
                ax_a.collections.clear()
                ax_a.fill_between(self.s_coords, a, facecolor= 'blue', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_a,index, variable='wetted sections', text= False)

            if 'velocity' in figures:
                v_id= figures.index('velocity')
                velocity = animation_axes[v_id][0]
                ax_v = animation_axes[v_id][1]
                velocity.set_data(self.s_coords, v)
                ax_v.collections.clear()
                ax_v.fill_between(self.s_coords, v, facecolor= 'red', alpha= 0.3, interpolate=True)
                if landmark != '':
                    self._landmark(landmark,ax_v,index, variable='velocity', text= False)

            if 'froude' in figures:
                fr_id= figures.index('froude')
                froude = animation_axes[fr_id][0]
                ax_fr = animation_axes[fr_id][1]
                froude.set_data(self.s_coords, fr)
                ax_fr.collections.clear()
                # ax_fr.fill_between(self.s_coords, fr, facecolor= 'blue', alpha= 0.3, interpolate=True)

                ax_fr.fill_between(self.s_coords, fr,
                                       color ='blue', alpha=alpha, interpolate=True, label='Subcritical')
                ax_fr.fill_between(self.s_coords, fr,y2 =1, where= 1<= fr,
                                       color ='blue', alpha=1, interpolate=True, label='Supercritical')

                ax_fr.hlines([1], 0, self.s_max, colors='red',linestyles= 'dotted')
                if landmark != '':
                    self._landmark(landmark,ax_fr,index, variable='froude', text= False)


            fig.suptitle(f'Results - 1D model\n$Time: (step: {index+1} - $simulated: {self.simulated_times[index+1]:#.1f}s$ - real: {self.real_times[index+1]:#.1e} s)$',
                        fontsize= 'x-large', fontweight= 'bold')


        rcParams['animation.embed_limit'] = 2**128 # Maximum size gif
        ani = animation.FuncAnimation(fig,
                                    _update_plots,
                                    interval = 200,
                                    blit = False,
                                    frames = self.simulated_times.shape[0] - real_time_step,
                                    repeat_delay = 100)

        if save_as != '':
            writergif = animation.PillowWriter(fps=5)
            ani.save(save_as, writer=writergif)

        return HTML(ani.to_jshtml())

    def convert_time_step(self, time_step):
        """
        Convert entry into a unique time step format
        usable by other methods.
        Return the real time step.

        :param time_step: Time step
        :type time_step: int
        :return: Real time step
        :rtype: int
        """
        # lgth = results_array.shape[1]
        if time_step < 0 and (-time_step) <= self.results_length:
            real_timestep = self.results_length + time_step
        elif time_step > 0 and time_step <= self.results_length:
            real_timestep= time_step - 1 # Python counts from 0.
        elif time_step == 0:
            real_timestep = 0
        else:
            real_timestep = self.results_length - 1
            warnings.warn(f'The input (time step) was not found; therefore, the last time step is plotted.', UserWarning)
        return real_timestep

    def __convert_time_step(self, time_step, results_array: np.array):
        """Deprecated"""
        lgth = results_array.shape[1]
        if time_step < 0 and (-time_step) <= lgth:
            real_timestep = lgth + time_step
        elif time_step > 0 and time_step <= lgth:
            real_timestep= time_step - 1 # Python counts from 0.
        else:
            real_timestep = lgth - 1
            warnings.warn(f'The input (time step) was not found; therefore, the last time step is plotted.', UserWarning)
        return real_timestep

    def _vector_from_coordinates(self) -> vector:
        """
        Create a vector from the lowest points of each section
        (coordinates).

        :return: Vector
        :rtype: vector
        """
        self.vector_coordinates = vector(is2D=False)
        for node in self.coordinates:
            vert = wolfvertex(node[2], node[1], node[0])
            self.vector_coordinates.add_vertex(vert)

        self.vector_coordinates.find_minmax()
        self.s_coords, self.z_coords = self.vector_coordinates.get_sz()
        self.s_min = min(self.s_coords)
        self.s_max =max(self.s_coords)
        self.z_min = min(self.z_coords)
        self.z_max =max(self.z_coords)

    def _landmark(self,
                  landmark: Union[Zones,str],
                  ax:Axes,
                  time_step: int,
                  text = True,
                  variable: Literal['water level', 'water depth', 'discharge', 'wetted sections','velocity', 'froude'] = 'water level',
                  alpha = 0.7,
                  rotation = 30,
                  ymax:float = None):
        """
        Plot landmarks which are hydraulic structures (bridges, culverts, weirs, etc.) or
        any other point of interest in the river.

        :param landmark: Landmark
        :type landmark: Union[Zones,str]
        :param ax: Axes
        :type ax: Axes
        :param time_step: Time step
        :type time_step: int
        :param text: Text, defaults to True
        :type text: bool, optional
        :param variable: Variable, defaults to 'water level'
        :type variable: Literal['water level', 'water depth', 'discharge', 'wetted sections','velocity', 'froude'], optional
        :param alpha: Alpha, defaults to 0.7
        :type alpha: float, optional
        :param rotation: Rotation, defaults to 30
        :type rotation: int, optional
        :param ymax: Ymax, defaults to None
        :type ymax: float, optional
        """

        if isinstance(landmark,str):
            landmark = Zones(landmark)
        landmark_names = [curvec.myname for curvec in landmark.myzones[0].myvectors]
        if self.s_curvi != None:
            lsg = self.mid_river_ls
        else:
            if self.vector_coordinates is None:
                self._vector_from_coordinates()
            lsg = self.vector_coordinates.asshapely_ls()
        curvi_landmarks =[lsg.project(Point((vect.myvertices[0].x + vect.myvertices[1].x)/2.,
                                               (vect.myvertices[0].y + vect.myvertices[1].y)/2.))
                                               for vect in landmark.myzones[0].myvectors]
        for s_landmark, name_landmark in zip(curvi_landmarks, landmark_names):
            if variable == 'water level':
                if ymax != None:
                    zmax = ymax
                else:
                    zmax = self.z_max
                ax.vlines(s_landmark, self.z_min, zmax, color='black', linestyles='--', alpha =alpha)
                if text:
                    ax.text(s_landmark, zmax,name_landmark, rotation=rotation, alpha =alpha)
            elif variable == 'water depth':
                if ymax != None:
                    max_depth = ymax
                else:
                    depth = self.depths[:,time_step] #FIXME automate this procedure
                    max_depth = max(depth)
                limit =  max_depth+ 0.1*max_depth
                ax.vlines(s_landmark, 0, limit , color='black', linestyles='--', alpha =alpha)
                if text:
                    ax.text(s_landmark, limit,name_landmark, rotation=rotation, alpha =alpha)
            elif variable == 'discharge':
                if ymax != None:
                    max_discharge = ymax

                else:
                    max_discharge = max(self.discharges[:,time_step])
                limit =  max_discharge+ 0.1*max_discharge
                ax.vlines(s_landmark, 0, limit, color='black', linestyles='--', alpha =alpha)
                if text:
                    ax.text(s_landmark, limit,name_landmark, rotation=rotation, alpha =alpha)
            elif variable == 'wetted sections':
                if ymax != None:
                    max_wetted_sections = ymax
                else:
                    max_wetted_sections = max(self.wetted_sections[:,time_step])
                limit = max_wetted_sections + 0.1*max_wetted_sections
                ax.vlines(s_landmark, 0,limit, color='black', linestyles='--', alpha =alpha)
                if text:
                    ax.text(s_landmark, limit,name_landmark, rotation=rotation, alpha =alpha)
            elif variable == 'velocity':
                if ymax != None:
                    max_velocities = ymax
                else:
                    max_velocities = max(self.velocities[:,time_step])
                limit = max_velocities + 0.1*max_velocities
                ax.vlines(s_landmark, 0, limit, color='black', linestyles='--', alpha =alpha)
                if text:
                    ax.text(s_landmark, limit,name_landmark, rotation=rotation, alpha =alpha)
            elif variable == 'froude':
                if ymax != None:
                    max_froudes = ymax
                else:
                    max_froudes = max(self.froudes[:,time_step])
                limit = max_froudes + 0.1*max_froudes
                ax.vlines(s_landmark, 0, limit, color='black', linestyles='--', alpha =alpha)
                if text:
                    ax.text(s_landmark, limit,name_landmark, rotation=rotation, alpha =alpha)

    def _river_banksbed(self, bedbanks: Union[Zones,str], zone_id:int = 0):
        """
        Set the river banks (left and right) and update
        the curviligne coordinates (self.s_coords) used for plotting
        (projections).

         - self.s_curvi = projections of lowest bed points on the mid-river bed vector (from _banksbed.vec),
         - self.left_bank_curvi = projections of left bank on the mid_river bed vector,
         - self.right_bank_curvi = projections of right bank on the mid_river bed vector.

        :param bedbanks: Bedbanks
        :type bedbanks: Union[Zones,str]
        :param zone_id: Zone id, defaults to 0
        :type zone_id: int, optional
        """
        if isinstance(bedbanks, str):
            bedbanks = Zones(bedbanks)
        bedbanks: Zones
        curzone = bedbanks.myzones[zone_id]
        left_bank = curzone.myvectors[0]
        bed = curzone.myvectors[1]
        right_bank = curzone.myvectors[2]
        self.mid_river_ls = bed.asshapely_ls()
        if self.vector_coordinates is None:
            self._vector_from_coordinates()
        bed_river_ls = self.vector_coordinates.asshapely_ls()
        self.s_curvi = [self.mid_river_ls.project(Point(vert.x, vert.y, vert.z)) for vert in self.vector_coordinates.myvertices]
        self.left_bank_curvi = [self.mid_river_ls.project(Point(vert.x, vert.y, vert.z)) for vert in left_bank.myvertices]
        self.s_bankleft, self.z_bankleft = left_bank.get_sz()
        self.right_bank_curvi = [self.mid_river_ls.project(Point(vert.x, vert.y, vert.z)) for vert in left_bank.myvertices]
        self.s_bankright, self.z_bankright = right_bank.get_sz()
        self.Update_curviline_coordinates()

    def Update_curviline_coordinates(self):
        """
        Update initial curviligne coordinates of the river bed (self.s_coords)
        projected curviligne coordinate (self.s_curvi).
        """
        if self.s_curvi != None:
                self.s_coords = self.s_curvi
                self.s_min = min(self.s_curvi)
                self.s_max = max(self.s_curvi)

    def _yticks_update(self, y_max):
        """
        Update the yticks of the graph.

        :param y_max: Y max
        :type y_max: float
        :return: Grid y
        :rtype: float
        """

        if y_max < 0.0001:
            grid_y = .00001
        elif y_max < 0.001:
            grid_y = .0001
        elif y_max < 0.01:
            grid_y = .001
        elif y_max < 0.1:
            grid_y = .01
        elif y_max < 1:
            grid_y = .1
        elif y_max < 3:
            grid_y = .2
        elif y_max < 5:
            grid_y = .5
        elif y_max < 10:
            grid_y = 1
        elif y_max < 20:
            grid_y = 2
        elif y_max < 50:
            grid_y = 5
        elif y_max < 100:
            grid_y = 10
        elif y_max < 200:
            grid_y = 20
        elif y_max < 1000:
            grid_y =50
        elif y_max > 1000:
            grid_y = 100
        return grid_y

    def _xticks_update(self, x_max):
        """
        Update the xticks of the graph.

        :param x_max: x max
        :type x_max: float
        :return: Grid x
        :rtype: float
        """
        if x_max < 1:
            grid_x = .1
        elif x_max >= 1 and x_max < 3:
            grid_x = .2
        elif x_max >= 3  and x_max < 5:
            grid_x = .5
        elif x_max >= 5  and x_max < 10:
            grid_x = 1
        elif x_max >= 10  and x_max < 20:
            grid_x = 2
        elif x_max >= 20  and x_max < 50:
            grid_x = 5
        elif x_max >= 50  and x_max < 100:
            grid_x = 10
        elif x_max >= 100  and x_max < 200:
            grid_x = 20
        elif x_max >= 200  and x_max < 1000:
            grid_x =200
        elif x_max >= 1000  and x_max < 10000:
            grid_x = 1000
        elif x_max >= 10000  and x_max < 20000:
            grid_x = 2000
        elif x_max >= 20000  and x_max < 50000:
            grid_x = 5000
        elif x_max >= 50000  and x_max < 100000:
            grid_x = 10000
        elif x_max >= 100000:
            grid_x = 20000
        return grid_x

    def _xticks_update_time(self, x_max):
        """
        Update the xticks of the graph.

        :param x_max: X max
        :type x_max: float
        :return: Grid x
        :rtype: float
        """

        if x_max < 1:
            grid_x = .1
        elif x_max < 3:
            grid_x = .2
        elif x_max < 5:
            grid_x = .5
        elif x_max < 10:
            grid_x = 1
        elif x_max < 20:
            grid_x = 2
        elif x_max < 60:
            grid_x = 5
        elif x_max < 120:
            grid_x = 10
        elif x_max < 300:
            grid_x = 30
        elif x_max < 900:
            grid_x = 90
        elif x_max < 9000:
            grid_x = 900
        elif x_max < 90000:
            grid_x = 3600
        elif x_max < 900000:
            grid_x = 36000
        elif x_max > 100000:
            grid_x = 360000

        return grid_x

    def return_only_width(self, depth: float, prof:profile)-> float:
        """
        Return the width of the profile for a given depth.

        :param depth: Depth
        :type depth: float
        :param prof: Profile
        :type prof: profile
        :return: Width
        :rtype: float
        """
        area,perimeter,width,radius = prof.relation_oneh(depth)
        return width

    def find_width_from_sz(self, depth: float, s: list, z:list) -> float:
        """
        Find the width from the s and z coordinates.

        :param depth: Depth
        :type depth: float
        :param s: S
        :type s: list
        :param z: Z
        :type z: list
        :return: Width
        :rtype: float
        """
        width = 0.0
        for i in range(0,len(s)-1):
            x1 = s[i]
            depth1= z[i]
            x2= s[i+1]
            depth2= z[i+1]
            delta_width = 0.0
            if depth1 < depth and depth2 < depth:
                delta_width = (x2 - x1)
            else:
                xx = INTERSEC(x1,depth1,x2,depth2, depth)
                if x1<=xx and xx <= x2:
                    if depth2 <= depth and depth <= depth1:
                        delta_width= (x2-xx)
                    if depth1 <= depth and  depth <= depth2:
                        delta_width = (xx-x1)
            width += delta_width
        return width

    def find_breadth_file(self, index):
        """
        Find the breadth file.

        :param index: Index
        :type index: int
        :return: Relations
        :rtype: np.array
        """
        for file in self.breadth_list:
            if file.endswith(f'{index}.breadth'):
               breadth_file =self.breath_directory +f'\\{file}'
               relations = np.loadtxt(breadth_file, delimiter ='\t', skiprows=1)

        return relations

    def compute_froude(self):
        """
        Compute the Froude number.
        """
        assert self.breadth_list != None,f'The top widths files are missing.'
        shape_mold = self.depths.shape
        self.widths = np.zeros(shape_mold)
        for i in range(shape_mold[0]):
            depths = self.depths[i,:]
            relations = self.find_breadth_file(i+1)
            smax= max(relations[:,1])
            self.widths[i,:] = np.interp(self.depths[i,:], relations[:,0], relations[:,1], left=0, right=smax)
        np.savetxt(self.directory + f'\\{self.simulation_name}.RWIDTH',self.widths)
        self.froudes = self.discharges / (self.wetted_sections*np.sqrt(Constants.GRAVITATION.value*(self.wetted_sections/self.widths)))

    def create_widths_and_froudes(self):
        """
        Create the widths and Froudes.
        Write the `.RWIDTH` file which contains the simulated top widths by the model.
        This file is used to compute the Froude number.
        """
        cross_sections = crosssections(self.cross_sections_file, 'vecz')
        if self.bank_file != None:
            riverbed_zones = Zones(self.bank_file)
            riverbed = riverbed_zones.myzones[0].myvectors[1]
        else:
            riverbed_zones = Zones(self.support_file)
            riverbed = riverbed_zones.myzones[0].myvectors[0]
        cross_sections.sort_along(riverbed.asshapely_ls(), 'sorted')
        sorted_crossections = np.array(cross_sections.sorted['sorted']['sorted'][:-1])
        shape_mold = self.depths.shape
        assert sorted_crossections.shape[0] == shape_mold[0]
        self.widths = np.zeros(shape_mold)
        prof: profile
        for i in tqdm(range(len(sorted_crossections))):
            prof = sorted_crossections[i]
            s,z = prof.get_sz()
            zmin = min(z)
            smax =max(s)
            water_lines = self.depths[i,:] + zmin
            z_array = np.array(z)
            z_array = np.unique(z_array)
            possible_widths = np.array([self.find_width_from_sz(depth,s,z) for depth in z_array])
            self.widths[i,:] = np.interp(water_lines, z_array, possible_widths, left=0, right=smax)
        np.savetxt(self.directory + f'\\{self.simulation_name}.RWIDTH',self.widths)
        self.froudes = self.discharges / (self.wetted_sections*np.sqrt(Constants.GRAVITATION.value*(self.wetted_sections/self.widths)))

    def _compute_froude(self,
                       cross_sections: crosssections,
                       riverbed:Union[vector, Zones, str] = vector,
                       zone_index:int=0,
                       vector_index:int = 0):
        """Deprecated"""
        if isinstance(riverbed, Zones):
            riverbed = riverbed.myzones[zone_index].myvectors[vector_index]
        elif isinstance(riverbed, str):
            riverbed = Zones(riverbed)
            riverbed = riverbed.myzones[zone_index].myvectors[vector_index]

        cross_sections.sort_along(riverbed.asshapely_ls(), 'sorted')
        sorted_crossections = np.array(cross_sections.sorted['sorted']['sorted'][:-1])
        shape_mold = self.depths.shape
        assert sorted_crossections.shape[0] == shape_mold [0]
        self.widths = np.zeros(shape_mold)
        prof: profile
        for i in tqdm(range(len(sorted_crossections))):
            # froude[i,:] = np.array([prof.relation_oneh()[2] for i in ) ])

            prof = sorted_crossections[i]
            s,z = prof.get_sz()
            zmin = min(z)
            smax =max(s)
            water_lines = self.depths[i,:] + zmin
            z_array = np.array(z)
            z_array = np.unique(z_array)
            # width[i,:] = np.array([self.find_width_from_sz(depth,s,z) for depth in water_lines])
            possible_widths = np.array([self.find_width_from_sz(depth,s,z) for depth in z_array])


            self.widths[i,:] = np.interp(water_lines, z_array, possible_widths, left=0, right=smax)
        # print(np.count_nonzero(self.width))
        # np.savetxt(r'.\Theux_1d_model\width.txt', self.widths, delimiter='\t')
        self.froudes = self.discharges / (self.wetted_sections*np.sqrt(Constants.GRAVITATION.value*(self.wetted_sections/self.widths)))
        # np.savetxt(r'.\Theux_1d_model\froude.txt', self.froudes, delimiter='\t')
        # np.savetxt(r'.\Theux_1d_model\discharge.txt', self.discharges, delimiter='\t')

    def find_max(self,array:np.ndarray) -> float:
        """
        Find the maximum value of an array.

        :param array: Array
        :type array: np.ndarray
        :return: Maximum
        :rtype: float
        """
        return np.max(array)

    def update_yaxis(self,
                     ax: Axes,
                     ymax: float,
                     ymin = None,
                     ):
        """
        Update the y-axis.

        :param ax: Axes
        :type ax: Axes
        :param ymax: Y max
        :type ymax: float
        :param ymin: Y min, defaults to None
        :type ymin: Union[float, None], optional
        """

        grid_y = self._yticks_update(ymax)
        if ymin is None:
            ax.set_ylim(bottom = None, top =ymax)
            ax.yaxis.set_ticks(np.arange(0, ymax, grid_y))
        else:
            ax.set_ylim(bottom = ymin, top =ymax)
            ax.yaxis.set_ticks(np.arange(ymin, ymax, grid_y))

    def find_figures_characteristics(self,
                    axes_for_updates:list[tuple[Line2D, Axes,Figure]],
                    figures:list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']] =['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'],
                    ):
        """
        Return the right index of axes to be plotted.

        :param axes_for_updates: Axes for updates
        :type axes_for_updates: list[tuple[Line2D, Axes,Figure]]
        :param figures: Figures, defaults to ['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']
        :type figures: list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']], optional
        :return: Indices
        :rtype: dict
        """
        indices = {}
        # new_axis = self.create_axis(figures)
        if 'water level' in figures:
            indices['water level'] = axes_for_updates[figures.index('water level')]
        if 'water depth' in figures:
            indices['water depth'] = axes_for_updates[figures.index('water depth')]
        if 'discharge' in figures:
            indices['discharge'] = axes_for_updates[figures.index('discharge')]
        if 'velocity' in figures:
            indices['velocity'] = axes_for_updates[figures.index('velocity')]
        if 'wetted section' in figures:
            indices['wetted section'] = axes_for_updates[figures.index('wetted section')]
        if 'froude' in figures:
            indices['froude'] = axes_for_updates[figures.index('froude')]

        # indices = {'water level':wl_id,
        #            'water depth': h_id,
        #            'discharge': q_id,
        #            'velocity': v_id,
        #            'wetted section': a_id,
        #            'froude': fr_id}
        return indices

    def plot_nodes_evolution(self,
                           which_nodes:list[int] = [0,-1],
                           variable_name:Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'] = 'discharge',
                           save_as:str = '',
                           figure_size = (25,15),
                           linewidth = 2.,
                           plotting_style:Literal['scatter','line', 'combined'] = 'line',
                           convert_to: Literal['days', 'hours', 'minutes', 'seconds'] = 'seconds'
                           ):
        """
        Plot the evolution in time of specified nodes for a variable.

        :param which_nodes: nodes for which the results will be displayed on the hydrograph,defaults to [0,-1]
        :type which_nodes: list[int], optional
        :param variable_name: the variable to plot , defaults to 'discharge'
        :type variable_name: Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'], optional
        :param save_as: File path where the figure is saved, defaults to ''
        :type save_as: str, optional
        :param figure_size: Figure size, defaults to (25,15)
        :type figure_size: tuple, optional
        :param linewidth: Linewidth on the graph (matplotlib format), defaults to 2.
        :type linewidth: float, optional
        :param plotting_style: Plotting style (matplotlib format), defaults to 'line'
        :type plotting_style: Literal['scatter','line', 'combined'], optional
        """
        coefficient = self.find_conversion_factor_from_seconds(convert_to)

        def axis_as_time_unit(val, pos):
            value = val/coefficient
            return f'{value:#.1F}'

        fig = plt.figure(figsize = figure_size, facecolor='white')
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        ax1.xaxis.set_major_formatter(FuncFormatter(axis_as_time_unit))
        ax2.xaxis.set_major_formatter(FuncFormatter(axis_as_time_unit))

        # Define the variable
        if variable_name == 'discharge':
            variable = self.discharges
            ax1.set_ylabel('Discharge [$m^3$/s]', fontsize= 'x-large')
        elif variable_name == 'water depth':
            variable = self.depths
            ax1.set_ylabel('Water depth [m]', fontsize= 'x-large')
        elif variable_name == 'velocity':
            variable =self.velocities
            ax1.set_ylabel('Velocity [m/s]', fontsize= 'x-large')
        elif variable_name == 'wetted section':
            variable = self.wetted_sections
            ax1.set_ylabel('Wetted section[$m^2$]', fontsize= 'x-large')
        elif variable_name == 'froude':
            variable = self.froudes
            ax1.set_ylabel('Froude number', fontsize= 'x-large')
        elif variable_name =='water level':
            variable = self.water_levels
            ax1.set_ylabel('Water level [m]', fontsize= 'x-large')
        else:
            raise Exception('The variable name is incorrect')


        n = variable.shape[0]
        #
        lgth =self.simulated_times.shape[0]
        # List of information necessary for the axes property
        min_variable = []
        max_variable = []
        max_times = []
        id_cells =[]

        # Refactorisation of the entry (positive or negative)
        for i in which_nodes:

            if i > 0:
                id_cell = i
                id = i - 1
            elif i < 0:
                id_cell = n + i + 1
                id = i
            elif i == 0:
                id_cell = i + 1
                id = i

            # collecting the curve properties for the Axes
            min_variable.append(np.amin(variable[id,:]))
            max_variable.append(np.amax(variable[id,:]))
            variable_max = np.argmax(variable[id,:])
            max_times.append(self.simulated_times[variable_max])
            id_cells.append(id_cell)
            # Plots
            if plotting_style == 'line':
                ax1.plot(self.simulated_times, variable[id,:], label=f'Node- {id_cell}', linewidth= linewidth)
                ax2.plot((self.simulated_times - self.simulated_times[variable_max]),
                        variable[id,:], label=f'Node- {id_cell}', linewidth= linewidth)
            elif plotting_style == 'scatter':
                ax1.scatter(self.simulated_times, variable[id,:], label=f'Node- {id_cell}', linewidth= linewidth)
                ax2.scatter((self.simulated_times - self.simulated_times[variable_max]),
                        variable[id,:], label=f'Node- {id_cell}', linewidth= linewidth)

            elif plotting_style == 'combined':
                ax1.plot(self.simulated_times, variable[id,:], label=f'Node- {id_cell}', linewidth= linewidth)
                ax1.scatter(self.simulated_times, variable[id,:], label=f'Node- {id_cell}', linewidth= linewidth)
                ax2.plot((self.simulated_times - self.simulated_times[variable_max]),
                        variable[id,:], label=f'Node- {id_cell}', linewidth= linewidth)
                ax2.scatter((self.simulated_times - self.simulated_times[variable_max]),
                        variable[id,:], label=f'Node- {id_cell}', linewidth= linewidth)

        # Properties first axis
        ax1.set_xlim(np.min(self.simulated_times),np.max(self.simulated_times))
        ax1.set_ylim(min(min_variable), (max(max_variable) + 0.1*max(max_variable)))
        # ax1.set_ylabel('Discharge [$m^3$]', fontsize= 'x-large')
        # ax1.set_xlabel('Simulated time [$s$]', fontsize= 'x-large')
        ax1.set_xlabel(f'Time [{convert_to}]')
        ax1.legend()
        # ax1.xaxis.set_ticks(np.arange(min(times),max(times),900))
        x_max = max(self.simulated_times)
        x_grid = self._xticks_update_time(x_max)
        ax1.xaxis.set_ticks(np.arange(min(self.simulated_times),x_max,x_grid))
        ax1.grid()
        ax1.set_title(f"Normal",
                      fontsize= 'x-large',
                      fontweight= 'bold')

        # Properties second axis
        tmax = np.max(self.simulated_times) - np.min(self.simulated_times)
        ax2.set_xlim((-tmax/2),(tmax/2))
        # ax2.text(-tmax/2,
        #          max(max_variable) + 0.05* max(max_variable),
        #          f'$Phase-shift: {max_times[0]-max_times[-1]:#.2f}s$', fontsize =14)
        ax2.set_ylim(min(min_variable), (max(max_variable) + 0.1*max(max_variable)))
        # ax2.set_xlabel('Time from maximum [s]', fontsize= 'x-large')
        ax2.set_xlabel(f'Time from maximum [{convert_to}]')
        ax2.legend()
        # ax2.xaxis.set_ticks(np.arange((-tmax/2),(tmax/2),900))
        ax2.grid()
        ax2.set_title(f"With a phase shit of {max_times[0]-max_times[-1]:#.1f}s",
                      fontsize= 'x-large',
                      fontweight= 'bold')

        # figure title, save and display parameters
        fig.suptitle(f'Nodes: {id_cells} - evolution of {variable_name}',
                     fontsize= 'xx-large',
                     fontweight= 'bold')
        # fig.suptitle(f'Hydrographs nodes - {id_cells}', fontsize= 'xx-large', fontweight= 'bold')
        if save_as != '':
            fig.savefig(save_as)
        plt.show()

    def plot_hydrograph_nodes(self,
                              which_nodes:list[int] = [0,-1],
                              save_as:str ='',
                              figure_size = (25,15)):
        """This method is deprecating. Plot nodes evolution provides more flexibility
        Plot the evolution in time of the discharge.

        :param which_nodes: _description_, defaults to [0,-1]
        :type which_nodes: list[int], optional
        :param save_as: file path, defaults to ''
        :type save_as: str, optional
        :param figure_size: Figure size, defaults to (25,15)
        :type figure_size: tuple, optional
        """

        discharges = self.discharges
        times = self.simulated_times

        n = discharges.shape[0]
        lgth = times.shape[0]

        # Creation of the figure
        fig = plt.figure(figsize=figure_size, facecolor='white')

        # Axes (2 graphs)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)

        # List of information necessary for the axes property
        min_discharges = []
        max_discharges = []
        max_times = []
        id_cells =[]

        # Refactorisation of the entry (positive or negative)
        for i in which_nodes:
            if i > 0:
                id_cell = i
                id = i - 1
            elif i < 0:
                id_cell = n + i + 1
                id = i
            elif i == 0:
                id_cell = i + 1
                id = i

            # collecting the curve properties for the Axes
            min_discharges.append(np.amin(discharges[id,:]))
            max_discharges.append(np.amax(discharges[id,:]))
            discharge_max = np.argmax(discharges[id,:])
            max_times.append(times[discharge_max])
            id_cells.append(id_cell)
            # Plots
            ax1.plot(times, discharges[id,:], label=f'Node- {id_cell}')
            ax2.plot((times - times[discharge_max]), discharges[id,:], label=f'Node- {id_cell}')

        # Properties first axis
        ax1.set_xlim(np.min(times),np.max(times))
        ax1.set_ylim(min(min_discharges), (max(max_discharges) + 0.1*max(max_discharges)))
        ax1.set_ylabel('Discharge [$m^3$]', fontsize= 'x-large')
        ax1.set_xlabel('Simulated times [$s$]', fontsize= 'x-large')
        ax1.legend()
        # ax1.xaxis.set_ticks(np.arange(min(times),max(times),900))
        x_max = max(times)
        x_grid = self._xticks_update_time(x_max)
        ax1.xaxis.set_ticks(np.arange(min(times),x_max,x_grid))
        ax1.grid()

        # Properties second axis
        tmax = np.max(times) - np.min(times)
        ax2.set_xlim((-tmax/2),(tmax/2))
        ax2.text(-tmax/2,
                 max(max_discharges) + 0.05* max(max_discharges),
                 f'$Phase-shift: {max_times[0]-max_times[-1]:#.2f}s$', fontsize =14)
        ax2.set_ylim(min(min_discharges), (max(max_discharges) + 0.1*max(max_discharges)))
        ax2.set_xlabel('Time from maximum [s]', fontsize= 'x-large')
        ax2.legend()
        # ax2.xaxis.set_ticks(np.arange((-tmax/2),(tmax/2),900))
        ax2.grid()

        # figure title, save and display parameters
        fig.suptitle(f'Hydrographs nodes - {id_cells}', fontsize= 'x-large', fontweight= 'bold')
        if save_as != '':
            fig.savefig(save_as, dpi =300)
        plt.show()

    @staticmethod
    def find_conversion_factor_from_seconds(convert_to: Literal['days', 'hours', 'minutes', 'seconds'] = 'seconds') -> int:
        """
        Find the conversion factor of a given time format to seconds.

        :param convert_to: The time format to convert to.
        :type convert_to: Literal['days', 'hours', 'minutes', 'seconds']
        :return: The conversion factor.
        :rtype: int
        """
        if convert_to == 'days':
            return 86400
        elif convert_to == 'hours':
            return 3600
        elif convert_to == 'minutes':
            return 60
        elif convert_to == 'seconds':
            return 1
        else:
            raise ValueError('The time format is not recognized')

    def project_coordinates_on_bed(self, x:float, y:float, z:float = None) -> tuple[int, float]:
        """
        Return the projection of the given point coorinates on the river bed.
        The return format is the following (x, y, s).
        Where,
         - x is the x coordinate of the projected point,
         - y is the y coordinate of the projected point,
         - s is the curviligne coordinate of the projected point (length from origin).

        :param x: X coordinate
        :type x: float
        :param y: Y coordinate
        :type y: float
        :param z: Z coordinate, defaults to None
        :type z: float, optional
        :return: Projected coordinates
        :rtype: tuple[float,float,float]
        """

        if z is None:
            projection = self.mid_river_ls.project(Point(x,y))

        else:
            projection = self.mid_river_ls.project(Point(x,y,z))


        closest_length, index_in_the_simulation = self.find_nearest(self.s_coords, projection)

        return index_in_the_simulation, closest_length

    def find_nearest(self, array: np.array, value: Literal[int, float]) -> tuple[float,int]:
        "Find the nearest value to the <value> and its index in an array."
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx], idx

    def get_results_from_xy_coordinates(self, x:float, y:float, time:int) -> dict:
        """
        Return the results of the closest point coordinates for a given time.

        :param x: X coordinate
        :type x: float
        :param y: Y coordinate
        :type y: float
        :param time: Time step
        :type time: int
        :return: Results
        :rtype: dict
        """
        assert isinstance(time, int), 'The time step must be an integer.'

        index, s = self.project_coordinates_on_bed(x,y)
        # results = self.get_closest_simulated_results(time, index)
        # results['Distance'] = s
        return self.get_closest_simulated_results(time, index)

    def get_simulated_velocity(self, node_index: int, time_index: int) -> float:
        """Return the simulated velocity at a given node and time step."""
        # assert isinstance(time_index, (int, np.ndarray)), 'The time step must be an integer or an array of integers.'
        # assert isinstance(node_index, (int, np.ndarray)), 'The node index must be an integer or an array of integers.'
        return self.velocities[node_index][time_index]

    def _get_buoy_trajectories(self,
                              time:float,
                              x:float,
                              y:float,
                              distance: float = None,
                              number_cells = None) -> pd.DataFrame:
        assert time>=0 and time <= self.simulated_times[-1],\
            f'The time must be within the simulation time range. {self.simulated_times[0]} <= time <= {self.simulated_times[-1]}'

        buoy_data = pd.DataFrame(columns = ['time',
                                            'distance',
                                            'water level',
                                            'water depth',
                                            'discharge',
                                            'velocity',
                                            'froude',
                                            'wetted section',
                                            'top width'])


        if distance is None and number_cells is None:
            all_cells = len(self.s_coords)
            index, s = self.project_coordinates_on_bed(x, y)
            distance = s

        while tqdm(index < all_cells, desc='Computing buoy trajectories', unit='node', disable = True):

            results = self.get_closest_simulated_results(time, index)

            buoy_data.loc[len(buoy_data.index)] ={'time': time,
                                                'distance': distance,
                                                'water level': results['water level'],
                                                'water depth': results['water depth'],
                                                'discharge': results['discharge'],
                                                'velocity': results['velocity'],
                                                'froude': results['froude'],
                                                'wetted section': results['wetted section'],
                                                'top width': results['top width']}

            new_index = index + 1
            if new_index < all_cells:
                distance = self.s_coords[new_index]
                distance_difference = self.s_coords[new_index] - self.s_coords[index]
                # time += distance_difference / results['velocity']
                time += distance_difference / abs(results['velocity']) # FIXME
            index = new_index

        return buoy_data

    def update_spatial_index_from_velocity(self, spatial_index:int, velocity:float,) -> int:
        """
        Update the spatial index based on the velocity.
        """
        if velocity > 0:
            new_spatial_index = spatial_index + 1
        elif velocity < 0:
            new_spatial_index = spatial_index - 1
        elif velocity == 0:
            raise ValueError(f'The velocity at node - {spatial_index} is null. The buoy is not moving.')
        else:
            raise ValueError(f'The velocity at node - {spatial_index} is not a number.')
        return new_spatial_index

    def update_spatial_index_from_velocity_backwards(self, spatial_index:int, velocity:float,) -> int:
        """
        Update the spatial index based on the velocity.
        """
        if velocity > 0:
            new_spatial_index = spatial_index - 1
        elif velocity < 0:
            new_spatial_index = spatial_index + 1
        elif velocity == 0:
            raise ValueError(f'The velocity at node - {spatial_index} is null. The buoy is not moving.')
        else:
            raise ValueError(f'The velocity at node - {spatial_index} is not a number.')
        return new_spatial_index

    def update_null_and_missing_velocities(self, velocity: float, treshold: float = 0.0001):
        """
        If the velocity is null or a missing value,
        a treshold (preferably very small) is returned
        as the new velocity to avoid division by zero or nan.

        @ Added during Gaia's internship
        to handle null and missing velocities.
        """
        if velocity > 0:
            return velocity
        elif  velocity < 0:
            return velocity
        elif velocity == 0:
            logging.warning(f'The velocity was zero. It has been changed to 0.0001m/s')
            return treshold
        else:
            logging.warning(f'The velocity was not a number. It has been changed to 0.0001m/s')
            return treshold

    def _create_buoy_dataframe(self) -> pd.DataFrame:
        """
        Create a DataFrame to store data from a drifter (buoy) trajectory.
        """
        columns = ['time',
                'distance',
                'water level',
                'water depth',
                'discharge',
                'velocity',
                'froude',
                'wetted section',
                'top width']
        return pd.DataFrame(columns=columns)

    def _compute_number_of_cells_on_curvilinear_vector(self) -> int:
        """Return the number of cells on the curvilinear vector."""
        return len(self.s_coords)

    def _get_results_velocity_for_buoy(self, results: dict) -> float:
        """
        Extract the velocity result for the buoy from the results dictionary.
        """
        assert isinstance(results, dict), 'The results must be a dictionary.'
        velocity = results.get('velocity', None)
        if velocity is None:
            raise Exception('Velocity not found')
        return self.update_null_and_missing_velocities(velocity)

    def _get_distance_between_spatial_indices(self, from_index:int, to_index:int) -> float:
        """
        Compute the distance between two spatial indices.
        """
        return self.s_coords[to_index] - self.s_coords[from_index]

    def _update_time_from_distance_and_velocity(self,
                                               time: float,
                                               distance: float,
                                               velocity:float) -> float:
        """
        Return the updated time which is computed
        based on the provided distance and velocity.

        !!! Mainly used in buoy applications (drifters)
        in the forward direction.

        :param time: Initial time
        :type time: float
        :param distance: Distance travelled between two points.
        :type distance: float
        :param velocity: Velocity
        :type velocity: float
        :return: Updated time
        :rtype: float
        """
        time_delta = abs(distance)/ abs(velocity)
        return time + time_delta

    def _update_time_from_distance_and_velocity_backwards(self,
                                               time: float,
                                               distance: float,
                                               velocity:float) -> float:
        """
        Return the updated time which is computed
        based on the provided distance and velocity.

        !!! Mainly used in buoy applications (drifters)
        in the backward direction.

        :param time: Initial time
        :type time: float
        :param distance: Distance travelled between two points.
        :type distance: float
        :param velocity: Velocity
        :type velocity: float
        :return: Updated time
        :rtype: float
        """
        time_delta = abs(distance)/ abs(velocity)
        return time - time_delta

    def _verify_and_correct_overtime(self, time: float):
        """
        Ensure the time does not exceed the simulated time range.
        """
        if time > self.simulated_times [-1]:
            return self.simulated_times[-1]
        return time

    def _verify_and_correct_overtime_backwards(self, time: float):
        """
        Return the starting time  of the simulation
        if the provided time is less than the first simulated time.
        
        ! To ensure the time does not exceed the simulated time range,
        lowest boundary.
        """
        if time < self.simulated_times[0]:
            return self.simulated_times[0]
        return time

    def _verify_and_correct_overtime_smart_way(self,
                                               time_0: float,
                                               time_1: float,
                                               temporal_index_0: int,
                                               temporal_index_1: int,
                                               distance: float,
                                               spatial_index: int) -> tuple[float, int]:
        """
        FIXME: examine this algorithm and check its impact on results.
        to ensure the time does not exceed the simulated time range.
        """
        if time_1 > self.simulated_times [-1]:
            while time_1 > self.simulated_times[-1]:
                temporal_index_1 += 1
                results = self.get_closest_simulated_results(self.simulated_times[temporal_index_1], spatial_index)
                velocity = self._get_results_velocity_for_buoy(results)
                time = self._update_time_from_distance_and_velocity(time, distance, velocity)

                time_delta = abs(distance) / abs(velocity)
                time_1 = time_0 + time_delta
            # To avoid repeating the same procedure at the next test.
            temporal_index_0 = temporal_index_1
        return time_1, temporal_index_0

    def _verify_and_correct_overtime_smart_way_backwards(self,
                                               time_0: float,
                                               time_1: float,
                                               temporal_index_0: int,
                                               temporal_index_1: int,
                                               distance: float,
                                               spatial_index: int) -> tuple[float, int]:
        """
        FIXME: examine this algorithm and check its impact on results.
        Ensure the time does not exceed the simulated time range.
        """
        if time_1 < self.simulated_times [0]:
            while time_1 < self.simulated_times[0]:
                temporal_index_1 -= 1
                results = self.get_closest_simulated_results(self.simulated_times[temporal_index_1], spatial_index)
                velocity = self._get_results_velocity_for_buoy(results)
                time = self._update_time_from_distance_and_velocity(time, distance, velocity)

                time_delta = abs(distance) / abs(velocity)
                time_1 = time_0 - time_delta
            # To avoid repeating the same procedure at the next test.
            temporal_index_0 = temporal_index_1
        return time_1, temporal_index_0

    def _corrected_skipped_temporal_indices(self,
                                             time_0: float,
                                             time_1: float,
                                             temporal_index_0: int,
                                             temporal_index_1: int,
                                             distance: float,
                                             spatial_index: int,
                                             velocity: float) -> tuple[float, int]:
        
        """
        Correct the time and spatial index if some temporal indices were skipped.
        (! Mainly for forwards direction)

        This can happen when the buoy moved faster 
        than the first encountered flow velocity in the simulation.

        For instance, if the buoy moved from temporal index 5 to 10,
        the maximum simulated velocity  between indices 5 and 10 is searched.

        :param time_0: Initial time
        :type time_0: float
        :param time_1: Updated time
        :type time_1: float
        :param temporal_index_0: Initial temporal index
        :type temporal_index_0: int
        :param temporal_index_1: Updated temporal index
        :type temporal_index_1: int
        :param distance: Distance travelled between two points.
        :type distance: float
        :param spatial_index: Spatial index
        :type spatial_index: int
        :param velocity: Velocity
        :type velocity: float
        :return: Updated time and spatial index
        :rtype: tuple[float, int]
        """
        if temporal_index_1 - temporal_index_0 > 1:
            potential_temporal_indices = np.arange(temporal_index_0, temporal_index_1 + 1, 1)
            potential_velocities = self.get_simulated_velocity(spatial_index, potential_temporal_indices)

            # 1. Getting the maximum velocity in the time range.
            maximum_velocity = np.max(potential_velocities)
            # 2. If the maximum velocity is not the previously extracted velocity which means the buoy moved faster,
            # the temporal index is updated to the index of the maximum velocity.
            if maximum_velocity != velocity:
                updated_temporal_index = potential_temporal_indices[np.argmax(potential_velocities)]
                # 3. The time and the results are updated.
                updated_time = self.simulated_times[updated_temporal_index]
                results = self.get_closest_simulated_results(updated_time, spatial_index)
                velocity = self._get_results_velocity_for_buoy(results)
                time_1 = self._update_time_from_distance_and_velocity(time_0, distance, velocity)
                # The spatial index is updated (mainly the sign)
                new_spatial_index = self.update_spatial_index_from_velocity(spatial_index, velocity)
                return time_1, new_spatial_index
        return time_1, spatial_index

    def _corrected_skipped_temporal_indices_backwards(self,
                                             time_0: float,
                                             time_1: float,
                                             temporal_index_0: int,
                                             temporal_index_1: int,
                                             distance: float,
                                             spatial_index: int,
                                             velocity: float) -> tuple[float, int]:
        
        """
        Correct the time and spatial index if some temporal indices were skipped.
        (! Mainly for backwards direction)
        This can happen when the buoy moved faster
        than the first encountered flow velocity in the simulation.
        For instance, if the buoy moved from temporal index 10 to 5,
        the maximum simulated velocity  between indices 5 and 10 is searched.
        :param time_0: Initial time
        :type time_0: float
        :param time_1: Updated time
        :type time_1: float
        :param temporal_index_0: Initial temporal index
        :type temporal_index_0: int
        :param temporal_index_1: Updated temporal index
        :type temporal_index_1: int
        :param distance: Distance travelled between two points.
        :type distance: float
        :param spatial_index: Spatial index
        :type spatial_index: int
        :param velocity: Velocity
        :type velocity: float
        :return: Updated time and spatial index
        :rtype: tuple[float, int]
        """
        if  temporal_index_0 - temporal_index_1> 1:
            potential_temporal_indices = np.arange(temporal_index_1,temporal_index_0 + 1, 1)
            potential_velocities = self.get_simulated_velocity(spatial_index, potential_temporal_indices)

            # 1. Getting the maximum velocity in the time range.
            maximum_velocity = np.max(potential_velocities)
            # 2. If the maximum velocity is not the previously extracted velocity which means the buoy moved faster,
            # the temporal index is updated to the index of the maximum velocity.
            if maximum_velocity != velocity:
                updated_temporal_index = potential_temporal_indices[np.argmax(potential_velocities)]
                # 3. The time and the results are updated.
                updated_time = self.simulated_times[updated_temporal_index]
                results = self.get_closest_simulated_results(updated_time, spatial_index)
                velocity = self._get_results_velocity_for_buoy(results)
                time_1 = self._update_time_from_distance_and_velocity_backwards(time_0, distance, velocity)
                # The spatial index is updated (mainly the sign)
                new_spatial_index = self.update_spatial_index_from_velocity_backwards(spatial_index, velocity)
                return time_1, new_spatial_index
        return time_1, spatial_index

    def get_buoy_forward_trajectory(self,
                              time:float,
                              x:float,
                              y:float,
                              debug = False) -> pd.DataFrame:
        """
        Compute the trajectory of a buoy (drifter) in the forward direction.
        :param time: Initial time
        :type time: float
        :param x: X coordinate of the initial position
        :type x: float
        :param y: Y coordinate of the initial position
        :type y: float
        :param debug: If True, print debug information, defaults to False
        :type debug: bool, optional
        :return: DataFrame containing the buoy trajectory data
        :rtype: pd.DataFrame
        """

        # Step 1: We verify whether the time is within the simulated range.
        # ----------------------------------------------------------------
        assert time>=0 and time <= self.simulated_times[-1],\
            f'The time must be within the simulated time span.\
                {self.simulated_times[0]} <= time - {time} <= {self.simulated_times[-1]}'
        # Step 2: We create a DataFrame to store the buoy trajectory data.
        # ---------------------------------------------------------------
        buoy_data = self._create_buoy_dataframe()

        # Step 3: Compute the  curvilinear distance from the first simulation cell
        # and its index (spatial index). FInd the number of cells in the results
        # -------------------------------------------------------------------------
        spatial_index, distance = self.project_coordinates_on_bed(x, y)
        number_of_cells = self._compute_number_of_cells_on_curvilinear_vector()

        # Step 4: Extraction of results
        # -----------------------------

        # 4.1. Creation of loop to ensure that the computations are done within
        # the simulated time range and spatial limits.
        # -------------------------------------------------------------------
        if debug:
            # disable = False
            disable = True
        else:
            disable = True
        while tqdm(spatial_index <  number_of_cells-1 and time < self.simulated_times[-1],\
                   desc='Computing buoy trajectories', unit='cell', disable=disable):
            # 4.1.2. Get the closest simulated results in time at the provided coordinates.
            # -------------------------------------------------------------------------
            results = self.get_closest_simulated_results(time, spatial_index)
            time_0 = time   # Is it necessary? doesnt look great, isn't it?

            # 4.1.3. Extract the velocity from the results dictionary.
            # -------------------------------------------------------------------------
            velocity = self._get_results_velocity_for_buoy(results)

            # 4.1.4. Update the spatial index based on the velocity extracted.
            # -------------------------------------------------------------------------
            new_spatial_index = self.update_spatial_index_from_velocity(spatial_index, velocity)

            # 4.1.5. Compute the distance between the 2 spatial indices.
            # -------------------------------------------------------------------------
            distance_between_cells = self._get_distance_between_spatial_indices(spatial_index, new_spatial_index)

            # 4.1.6. Update the time based on the distance and velocity.
            # -------------------------------------------------------------------------
            time_1 = self._update_time_from_distance_and_velocity(time_0, distance_between_cells, velocity)

            # 4.1.7. Results verifications
            # -------------------------------------------------------------------------
            time_1 = self._verify_and_correct_overtime(time_1)

            # 4.1.8. Get the temporal indices of the computed time
            # -------------------------------------------------------------------------
            temporal_index_0 = self.get_closest_simulated_time_index(time_0)
            temporal_index_1 = self.get_closest_simulated_time_index(time_1)

            # 4.1.9. Another correction of times
            # ----------------------------------
            # FIXME: This step is probably useless.Check it in debug mode..
            time_1, temporal_index_0 = self._verify_and_correct_overtime_smart_way(time_0=time_0,
                                                                                   time_1=time_1,
                                                                                   temporal_index_0=temporal_index_0,
                                                                                   temporal_index_1=temporal_index_1,
                                                                                   distance=distance_between_cells,
                                                                                   spatial_index=spatial_index,
                                                                                   )

            # 4.1.10. Case for temporal indices which have been skipped (not).
            # ----------------------------------------------------------------
            if temporal_index_1 - temporal_index_0 > 1:
                time_1, new_spatial_index = self._corrected_skipped_temporal_indices(time_0=time_0,
                                                                                    time_1=time_1,
                                                                                    temporal_index_0=temporal_index_0,
                                                                                    temporal_index_1=temporal_index_1,
                                                                                    distance=distance_between_cells,
                                                                                    spatial_index=spatial_index,
                                                                                    velocity=velocity)
            # 4.1.11. the results are added to the dataframe.
            # ----------------------------------------------------------------
            buoy_data.loc[len(buoy_data.index)] ={'time': time,
                                            'distance': distance,
                                            'water level': results['water level'],
                                            'water depth': results['water depth'],
                                            'discharge': results['discharge'],
                                            'velocity': results['velocity'],
                                            'froude': results['froude'],
                                            'wetted section': results['wetted section'],
                                            'top width': results['top width']}

            # 4.1.12. Updating the time and spatial index for the next  iteration.
            if new_spatial_index < number_of_cells:
                time = time_1
                spatial_index = new_spatial_index
                distance = self.s_coords[spatial_index]
                if debug:
                    text_limit = '*'
                    logging.info(f'\n{text_limit*50}\
                                 \n\tTime: {time:#.2F} s,\
                                 \n\tSpatial index: {spatial_index} out of {number_of_cells - 1},\
                                 \n\tDistance: {distance:#.2F} m,\
                                 \n\tVelocity: {velocity:#.2F} m/s\
                                 \n{text_limit*50}')
                # (print(f'New spatial index: {spatial_index} out of {number_of_cells}'))

        return buoy_data

    def get_buoy_backward_trajectory(self,
                              time:float,
                              x:float,
                              y:float,
                              debug = False) -> pd.DataFrame:
        """
        Compute the trajectory of a buoy (drifter) in the backward direction.

        :param time: Initial time
        :type time: float
        :param x: X coordinate of the initial position
        :type x: float
        :param y: Y coordinate of the initial position
        :type y: float
        :param debug: If True, print debug information, defaults to False
        :type debug: bool, optional
        :return: DataFrame containing the buoy trajectory data
        :rtype: pd.DataFrame
        """

        # Step 1: We verify whether the time is within the simulated range.
        # ----------------------------------------------------------------
        assert time>=0 and time <= self.simulated_times[-1],\
            f'The time must be within the simulated time span.\
                {self.simulated_times[0]} <= time - {time} <= {self.simulated_times[-1]}'
        # Step 2: We create a DataFrame to store the buoy trajectory data.
        # ---------------------------------------------------------------
        buoy_data = self._create_buoy_dataframe()

        # Step 3: Compute the  curvilinear distance from the first simulation cell
        # and its index (spatial index). FInd the number of cells in the results
        # -------------------------------------------------------------------------
        spatial_index, distance = self.project_coordinates_on_bed(x, y)
        number_of_cells = self._compute_number_of_cells_on_curvilinear_vector()

        # Step 4: Extraction of results
        # -----------------------------

        # 4.1. Creation of loop to ensure that the computations are done within
        # the simulated time range and spatial limits.
        # -------------------------------------------------------------------
        if debug:
            # disable = False
            disable = True
        else:
            disable = True
        while tqdm(spatial_index >=  0 and time >= self.simulated_times[0],\
                   desc='Computing buoy trajectory backwards', unit='cell', disable=disable):
            # 4.1.2. Get the closest simulated results in time at the provided coordinates.
            # -------------------------------------------------------------------------
            results = self.get_closest_simulated_results(time, spatial_index)
            time_0 = time

            # 4.1.3. Extract the velocity from the results dictionary.
            # -------------------------------------------------------------------------
            velocity = self._get_results_velocity_for_buoy(results)

            # 4.1.4. Update the spatial index based on the velocity extracted.
            # -------------------------------------------------------------------------
            new_spatial_index = self.update_spatial_index_from_velocity_backwards(spatial_index, velocity)
            if new_spatial_index > 0:

                # 4.1.5. Compute the distance between the 2 spatial indices.
                # -------------------------------------------------------------------------
                distance_between_cells = self._get_distance_between_spatial_indices(spatial_index, new_spatial_index)

                # 4.1.6. Update the time based on the distance and velocity.
                # -------------------------------------------------------------------------
                time_1 = self._update_time_from_distance_and_velocity_backwards(time_0, distance_between_cells, velocity)

                # 4.1.7. Results verifications
                # -------------------------------------------------------------------------
                time_1 = self._verify_and_correct_overtime_backwards(time_1)

                # 4.1.8. Get the temporal indices of the computed time
                # -------------------------------------------------------------------------
                temporal_index_0 = self.get_closest_simulated_time_index(time_0)
                temporal_index_1 = self.get_closest_simulated_time_index(time_1)

                # 4.1.9. Another correction of times
                # ----------------------------------
                # FIXME: This step is probably useless.Check it in debug mode..
                time_1, temporal_index_0 = self._verify_and_correct_overtime_smart_way_backwards(time_0=time_0,
                                                                                    time_1=time_1,
                                                                                    temporal_index_0=temporal_index_0,
                                                                                    temporal_index_1=temporal_index_1,
                                                                                    distance=distance_between_cells,
                                                                                    spatial_index=spatial_index,
                                                                                    )

                # 4.1.10. Case for temporal indices which have been skipped (not).
                # ----------------------------------------------------------------
                if  temporal_index_0 - temporal_index_1 > 1:
                    time_1, new_spatial_index = self._corrected_skipped_temporal_indices_backwards(time_0=time_0,
                                                                                        time_1=time_1,
                                                                                        temporal_index_0=temporal_index_0,
                                                                                        temporal_index_1=temporal_index_1,
                                                                                        distance=distance_between_cells,
                                                                                        spatial_index=spatial_index,
                                                                                        velocity=velocity)
                # 4.1.11. the results are added to the dataframe.
                # ----------------------------------------------------------------
                buoy_data.loc[len(buoy_data.index)] ={'time': time,
                                                'distance': distance,
                                                'water level': results['water level'],
                                                'water depth': results['water depth'],
                                                'discharge': results['discharge'],
                                                'velocity': results['velocity'],
                                                'froude': results['froude'],
                                                'wetted section': results['wetted section'],
                                                'top width': results['top width']}

                # 4.1.12. Updating the time and spatial index for the next  iteration.
                if new_spatial_index >= 0:
                    time = time_1
                    spatial_index = new_spatial_index
                    distance = self.s_coords[spatial_index]
                    if debug:
                        text_limit = '*'
                        print(f'\n{text_limit*50}\
                                    \n\tTime: {time:#.2F} s,\
                                    \n\tSpatial index: {spatial_index} out of {number_of_cells - 1},\
                                    \n\tDistance: {distance:#.2F} m,\
                                    \n\tVelocity: {velocity:#.2F} m/s\
                                    \n{text_limit*50}')
                        if spatial_index == 0:
                            print('The spatial index has reached the first cell.')
                    # (print(f'New spatial index: {spatial_index} out of {number_of_cells}'))

            else:
                spatial_index = new_spatial_index
                if debug:
                    print(f'\n{text_limit*50}\
                            \n\tTime: {time:#.2F} s,\
                            \n\tSpatial index: {spatial_index} out of {number_of_cells - 1},\
                            \n\tDistance: {distance:#.2F} m,\
                            \n\tVelocity: {velocity:#.2F} m/s\
                            \n{text_limit*50}')

        return buoy_data

    def get_buoy_trajectories(self,
                              time:float,
                              x:float,
                              y:float,
                              distance: float = None,
                              number_cells = None) -> pd.DataFrame:
        assert time>=0 and time <= self.simulated_times[-1],\
            f'The time must be within the simulation time range. {self.simulated_times[0]} <= time - {time} <= {self.simulated_times[-1]}'

        buoy_data = pd.DataFrame(columns = ['time',
                                            'distance',
                                            'water level',
                                            'water depth',
                                            'discharge',
                                            'velocity',
                                            'froude',
                                            'wetted section',
                                            'top width'])



        # 1. Definition of spatial and temporal indices
        # FIXME: What if only the distance is provided? or the opposite?
        # also what if one or both of them are wrong?
        # This should be a method make it robust.
        if distance is None and number_cells is None:
            # all_cells = len(self.s_coords)
            # index, s = self.project_coordinates_on_bed(x, y)
            spatial_index, distance = self.project_coordinates_on_bed(x, y)
            # time_0 = time
            number_of_cells = len(self.s_coords)

        # 2. Extraction of results

        # while tqdm(spatial_index >= 0 and spatial_index <  number_of_cells, desc='Computing buoy trajectories', unit='cell', disable=True):
        while tqdm(spatial_index <  number_of_cells-1 and time < self.simulated_times[-1],\
                   desc='Computing buoy trajectories', unit='cell', disable=True):

            results = self.get_closest_simulated_results(time, spatial_index)
            time_0 = time

            # 2. 1.  updating the spatial index (forard or backward movement)
            # FIXME: create a method for extracting and updating the velocity
            # because it's somehow recurrent throughout the code.
            velocity = results['velocity']
            # FIXME rethink this approach of changing null & missing values.
            velocity = self.update_null_and_missing_velocities(velocity)
            new_spatial_index = self.update_spatial_index_from_velocity(spatial_index, velocity)

            # 2.2.  Computing the distance between cells
            # FIXME: Make it a method and add assert for verifications.
            distance_between_cells = self.s_coords[new_spatial_index] - self.s_coords[spatial_index]

            # 2.3.  Updating the time
            # FIXME: Create a methods one for computing the time between successive cells and,
            # another for updating the time.
            time_delta = abs(distance_between_cells) / abs(velocity)
            time_1 = time_0 + time_delta

            # 2.4.  Correction of the results
            temporal_index_0 = self.get_closest_simulated_time_index(time_0)

            if time_1 > self.simulated_times [-1]:
                time_1 = self.simulated_times[-1]
            temporal_index_1 = self.get_closest_simulated_time_index(time_1)


            # FIXME time -1 has a big issue.
            # In case the time is bigger than the simulation time range, the time is updated to the last time step.
            # This is the case for extremely low velocities which could lead to infinitely very long times.
            #FIXME: clean these steps (make them cleaner)
            if time_1 > self.simulated_times [-1] or time_1 < 0:
                while time_1 > self.simulated_times[-1]:
                    temporal_index_1 += 1
                    results = self.get_closest_simulated_results(self.simulated_times[temporal_index_1], spatial_index)
                    velocity = results['velocity']
                    velocity = self.update_null_and_missing_velocities(velocity)
                    time_delta = abs(distance_between_cells) / abs(velocity)
                    time_1 = time_0 + time_delta
                # To avoid repeating the same procedure at the next test.
                temporal_index_0 = temporal_index_1

            # temporal_index_1 = self.get_closest_simulated_time_index(time_1)

            # Case for temporal indices which have been skipped (not).
            if temporal_index_1 - temporal_index_0 > 1:
                potential_temporal_indices = np.arange(temporal_index_0, temporal_index_1+1, 1)
                potential_velocities = self.get_simulated_velocity(spatial_index, potential_temporal_indices) # FIXME check if it works for arrays.
                # 2.5. Checking whether the extracted velocities are rigoursly the same.
                # FIXME assert velocity in potential_velocities, \
                    # f'The velocity extracted - {velocity} is not in the potential velocities - {potential_velocities}.'
                # assert potential_velocities[0]- velocity < 1e-5, 'The velocities extracted are not the same.'
                # 2.6. Getting the maximum velocity in the time range.
                maximum_velocity = np.max(potential_velocities) # FIXME find  a better way to do this.
                # 2.7. If the maximum velocity is not the previously extracted velocity which means the buoy moved faster,
                # the temporal index is updated to the index of the maximum velocity.
                if maximum_velocity != velocity:
                    updated_temporal_index = potential_temporal_indices[np.argmax(potential_velocities)]
                    # 2.8. The time and the results are updated.
                    updated_time = self.simulated_times[updated_temporal_index]
                    results = self.get_closest_simulated_results(updated_time, spatial_index)
                    velocity = results['velocity']
                    velocity = self.update_null_and_missing_velocities(velocity)
                    # The time increment is updated.
                    new_time_delta = abs(distance_between_cells) / abs(velocity)
                    # The spatial index is updated (mainly the sign)
                    new_spatial_index = self.update_spatial_index_from_velocity(spatial_index, velocity)
                    time_1 =  time_0 + new_time_delta

            # 2.9. The results are added to the dataframe.
            buoy_data.loc[len(buoy_data.index)] ={'time': time,
                                            'distance': distance,
                                            'water level': results['water level'],
                                            'water depth': results['water depth'],
                                            'discharge': results['discharge'],
                                            'velocity': results['velocity'],
                                            'froude': results['froude'],
                                            'wetted section': results['wetted section'],
                                            'top width': results['top width']}

            # 2.10. Updating the time and spatial index for the next  iteration.
            if new_spatial_index < number_of_cells:
                time = time_1
                spatial_index = new_spatial_index
                distance = self.s_coords[spatial_index]
                # (print(f'New spatial index: {spatial_index} out of {number_of_cells}'))

        return buoy_data

    def get_backwards_buoy_trajectories(self,
                              time:float,
                              x:float,
                              y:float,
                              distance: float = None,
                              number_cells = None) -> pd.DataFrame:
        """Deprecated: Use get_buoy_backward_trajectory instead."""
        assert time>=0 and time <= self.simulated_times[-1],\
            f'The time must be within the simulation time range. {self.simulated_times[0]} <= time - {time} <= {self.simulated_times[-1]}'

        buoy_data = pd.DataFrame(columns = ['time',
                                            'distance',
                                            'water level',
                                            'water depth',
                                            'discharge',
                                            'velocity',
                                            'froude',
                                            'wetted section',
                                            'top width'])



        # 1. Definition of spatial and temporal indices
        if distance is None and number_cells is None:
            # all_cells = len(self.s_coords)
            # index, s = self.project_coordinates_on_bed(x, y)
            spatial_index, distance = self.project_coordinates_on_bed(x, y)
            # time_0 = time
            number_of_cells = len(self.s_coords)

        # 2. Extraction of results

        # while tqdm(spatial_index >= 0 and spatial_index <  number_of_cells, desc='Computing buoy trajectories', unit='cell', disable=True):
        while tqdm(spatial_index <  number_of_cells-1 and time < self.simulated_times[-1],\
                   desc='Computing buoy trajectories', unit='cell', disable=True):

            results = self.get_closest_simulated_results(time, spatial_index)
            time_0 = time

            # 2. 1.  updating the spatial index (forard or backward movement)
            velocity = results['velocity']
            # FIXME rethink this approach of changing null & missing vaalues
            velocity = self.update_null_and_missing_velocities(velocity)
            new_spatial_index = self.update_spatial_index_from_velocity_backwards(spatial_index, velocity)

            # 2.2.  Computing the distance between cells
            distance_between_cells = self.s_coords[new_spatial_index] - self.s_coords[spatial_index]

            # 2.3.  Updating the time
            time_delta = abs(distance_between_cells) / abs(velocity)
            time_1 = time_0 + time_delta

            # 2.4.  Correction of the results
            temporal_index_0 = self.get_closest_simulated_time_index(time_0)

            if time_1 > self.simulated_times[-1]:
                time_1 = self.simulated_times[-1]
            elif time_1 < self.simulated_times[0]:
                time_1 = self.simulated_times[0]
            temporal_index_1 = self.get_closest_simulated_time_index(time_1)



            # FIXME time -1 has a big issue.
            # In case the time is bigger than the simulation time range, the time is updated to the last time step.
            # This is the case for extremely low velocities which could lead to infinitely very long times.
            if time_1 > self.simulated_times [-1] or time_1 < self.simulated_times[0]:
                while time_1 > self.simulated_times[-1]:
                    temporal_index_1 -= 1
                    results = self.get_closest_simulated_results(self.simulated_times[temporal_index_1], spatial_index)
                    velocity = results['velocity']
                    velocity = self.update_null_and_missing_velocities(velocity)
                    time_delta = abs(distance_between_cells) / abs(velocity)
                    time_1 = time_0 + time_delta
                # To avoid repeating the same procedure at the next test.
                temporal_index_0 = temporal_index_1

            # temporal_index_1 = self.get_closest_simulated_time_index(time_1)

            # Case for temporal indices which have been skipped (not).
            if temporal_index_0 - temporal_index_1 > 1:
                # potential_temporal_indices = np.arange(temporal_index_0, temporal_index_1+1, 1)
                potential_temporal_indices = np.arange(temporal_index_1, temporal_index_0+1, 1)
                potential_velocities = self.get_simulated_velocity(spatial_index, potential_temporal_indices) # FIXME check if it works for arrays.
                # 2.5. Checking whether the extracted velocities are rigoursly the same.
                # FIXME assert velocity in potential_velocities, \
                    # f'The velocity extracted - {velocity} is not in the potential velocities - {potential_velocities}.'
                # assert potential_velocities[0]- velocity < 1e-5, 'The velocities extracted are not the same.'
                # 2.6. Getting the maximum velocity in the time range.
                maximum_velocity = np.max(potential_velocities) # FIXME find  a better way to do this.
                # 2.7. If the maximum velocity is not the previously extracted velocity which means the buoy moved faster,
                # the temporal index is updated to the index of the maximum velocity.
                if maximum_velocity != velocity:
                    updated_temporal_index = potential_temporal_indices[np.argmax(potential_velocities)]
                    # 2.8. The time and the results are updated.
                    updated_time = self.simulated_times[updated_temporal_index]
                    results = self.get_closest_simulated_results(updated_time, spatial_index)
                    velocity = results['velocity']
                    velocity = self.update_null_and_missing_velocities(velocity)
                    # The time increment is updated.
                    new_time_delta = abs(distance_between_cells) / abs(velocity)
                    # The spatial index is updated (mainly the sign)
                    new_spatial_index = self.update_spatial_index_from_velocity_backwards(spatial_index, velocity)
                    time_1 =  time_0 + new_time_delta

            # 2.9. The results are added to the dataframe.
            buoy_data.loc[len(buoy_data.index)] ={'time': time,
                                            'distance': distance,
                                            'water level': results['water level'],
                                            'water depth': results['water depth'],
                                            'discharge': results['discharge'],
                                            'velocity': results['velocity'],
                                            'froude': results['froude'],
                                            'wetted section': results['wetted section'],
                                            'top width': results['top width']}

            # 2.10. Updating the time and spatial index for the next  iteration.
            if new_spatial_index <  number_of_cells and new_spatial_index >=0:
                time = time_1
                spatial_index = new_spatial_index
                distance = self.s_coords[spatial_index]
                # (print(f'New spatial index: {spatial_index} out of {number_of_cells}'))

        return buoy_data

    def get_mean_values_along_trajectory(self,
                                    time_1:float,
                                    x_1:float,
                                    y_1:float,
                                    time_2:float,
                                    x_2:float,
                                    y_2:float
                                    ) -> pd.DataFrame:
        """
        Return the mean of all simulated values along a trajectory defined by two points and two times.
        The distance in the returned dataframe is the curvilinear distance along the river bed 
        for each reported time step.

        :param time_1: Initial time
        :type time_1: float
        :param x_1: X coordinate of the initial position
        :type x_1: float
        :param y_1: Y coordinate of the initial position
        :type y_1: float
        :param time_2: Final time
        :type time_2: float
        :param x_2: X coordinate of the final position
        :type x_2: float
        :param y_2: Y coordinate of the final position
        :type y_2: float
        """
        assert time_1 >= 0 and time_1 <= self.simulated_times[-1],\
            f'The time_1 must be within the simulation time range.\
                {self.simulated_times[0]} <= time_1 - {time_1} <= {self.simulated_times[-1]}'

        assert time_2 >= 0 and time_2 <= self.simulated_times[-1],\
            f'The time_2 must be within the simulation time range.\
                {self.simulated_times[0]} <= time_2 - {time_2} <= {self.simulated_times[-1]}'
        assert time_2 > time_1, 'The time_2 must be greater than time_1.'

        spatial_index_1, distance_1 = self.project_coordinates_on_bed(x_1, y_1)
        spatial_index_2, distance_2 = self.project_coordinates_on_bed(x_2, y_2)
        assert spatial_index_2 > spatial_index_1, 'The second point must be downstream the first point.'
        temporal_index_1 = self.get_closest_simulated_time_index(time_1)
        temporal_index_2 = self.get_closest_simulated_time_index(time_2)

        results ={'distance': self.s_coords[spatial_index_1: spatial_index_2 + 1],
                'water level': np.mean(self.water_levels[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1], axis =1),
                'water depth': np.mean(self.depths[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1], axis =1),
                'discharge': np.mean(self.discharges[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1], axis =1),
                'velocity': np.mean(self.velocities[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1], axis =1),
                'froude': np.mean(self.froudes[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1], axis =1),
                'wetted section':np.mean(self.wetted_sections[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1], axis =1),
                'top width': np.mean(self.widths[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1], axis =1),
                  }
        mean_values = pd.DataFrame(results)
        return mean_values

    def get_mean_of_trajectory_variables(self,
                                    time_1:float,
                                    x_1:float,
                                    y_1:float,
                                    time_2:float,
                                    x_2:float,
                                    y_2:float
                                    ) -> dict:
        """
        Return all simulated values along a trajectory defined by two points and two times.
        The  curvilinear distance along the river bed for each reported time step is not returned.

        :param time_1: Initial time
        :type time_1: float
        :param x_1: X coordinate of the initial position
        :type x_1: float
        :param y_1: Y coordinate of the initial position
        :type y_1: float
        :param time_2: Final time
        :type time_2: float
        :param x_2: X coordinate of the final position
        :type x_2: float
        :param y_2: Y coordinate of the final position
        :type y_2: float
        :return: A dictionary containing the mean values of the simulated variables along the trajectory.
        :rtype: dict
        """
        assert time_1 >= 0 and time_1 <= self.simulated_times[-1],\
            f'The time_1 must be within the simulation time range.\
                {self.simulated_times[0]} <= time_1 - {time_1} <= {self.simulated_times[-1]}'

        assert time_2 >= 0 and time_2 <= self.simulated_times[-1],\
            f'The time_2 must be within the simulation time range.\
                {self.simulated_times[0]} <= time_2 - {time_2} <= {self.simulated_times[-1]}'
        assert time_2 > time_1, 'The time_2 must be greater than time_1.'

        spatial_index_1, distance_1 = self.project_coordinates_on_bed(x_1, y_1)
        spatial_index_2, distance_2 = self.project_coordinates_on_bed(x_2, y_2)
        assert spatial_index_2 > spatial_index_1, 'The second point must be downstream the first point.'
        temporal_index_1 = self.get_closest_simulated_time_index(time_1)
        temporal_index_2 = self.get_closest_simulated_time_index(time_2)

        results ={
                'water level': np.mean(self.water_levels[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1]),
                'water depth': np.mean(self.depths[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1]),
                'discharge': np.mean(self.discharges[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1]),
                'velocity': np.mean(self.velocities[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1]),
                'froude': np.mean(self.froudes[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1]),
                'wetted section':np.mean(self.wetted_sections[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1]),
                'top width': np.mean(self.widths[spatial_index_1: spatial_index_2 + 1, temporal_index_1: temporal_index_2 + 1]),
                  }

        return results

    def ___get_buoy_trajectories(self,
                              time:float,
                              x:float,
                              y:float,
                              distance: float = None,
                              number_cells = None) -> pd.DataFrame:
        """Deprecated: Use get_buoy_trajectories instead."""
        assert time>=0 and time <= self.simulated_times[-1],\
            f'The time must be within the simulation time range. {self.simulated_times[0]} <= time <= {self.simulated_times[-1]}'

        buoy_data = pd.DataFrame(columns = ['time',
                                            'distance',
                                            'water level',
                                            'water depth',
                                            'discharge',
                                            'velocity',
                                            'froude',
                                            'wetted section',
                                            'top width'])



        # 1. Definition of spatial and temporal indices
        if distance is None and number_cells is None:
            # all_cells = len(self.s_coords)
            # index, s = self.project_coordinates_on_bed(x, y)
            spatial_index, distance = self.project_coordinates_on_bed(x, y)
            time_0 = time
            number_of_cells = len(self.s_coords)

        # 2. Extraction of results

        # while tqdm(spatial_index >= 0 and spatial_index <  number_of_cells, desc='Computing buoy trajectories', unit='cell', disable=True):
        while tqdm(spatial_index <  number_of_cells-1, desc='Computing buoy trajectories', unit='cell', disable=True):

            results = self.get_closest_simulated_results(time, spatial_index)

            # 2. 1.  updating the spatial index (forard or backward movement)
            velocity = results['velocity']
            new_spatial_index = self.update_spatial_index_from_velocity(spatial_index, velocity)

            # 2.2.  Computing the distance between cells
            distance_between_cells = self.s_coords[new_spatial_index] - self.s_coords[spatial_index]

            # 2.3.  Updating the time
            time_delta = abs(distance_between_cells) / abs(velocity)
            time_1 = time_0 + time_delta

            # 2.4.  Correction of the results
            temporal_index_0 = self.get_closest_simulated_time_index(time_0)
            temporal_index_1 = self.get_closest_simulated_time_index(time_1)

            if time_1 > self.simulated_times [-1] or time_1 < 0:
                # # temporal_index_1 =  temporal_index_0
                time = self.simulated_times[-1]
                time_1 = self.simulated_times[-1]
                spatial_index =  len(self.s_coords) - 1


                # while time_1 > self.simulated_times[-1]:
                #     temporal_index_1 += 1
                #     results = self.get_closest_simulated_results(self.simulated_times[temporal_index_1], spatial_index)
                #     velocity = results['velocity']
                #     time_delta = abs(distance_between_cells) / abs(velocity)
                #     time_1 = time_0 + time_delta

            else:
                if temporal_index_1 - temporal_index_0 > 1:
                    potential_temporal_indices = np.arange(temporal_index_0, temporal_index_1+1, 1)
                    potential_velocities = self.get_simulated_velocity(spatial_index, potential_temporal_indices) # FIXME check if it works for arrays.
                    # 2.5. Checking whether the extracted velocities are rigoursly the same.
                    # FIXME assert velocity in potential_velocities, \
                        # f'The velocity extracted - {velocity} is not in the potential velocities - {potential_velocities}.'
                    # assert potential_velocities[0]- velocity < 1e-5, 'The velocities extracted are not the same.'
                    # 2.6. Getting the maximum velocity in the time range.
                    maximum_velocity = np.max(potential_velocities) # FIXME find  a better way to do this.
                    # 2.7. If the maximum velocity is not the previously extracted velocity which means the buoy moved faster,
                    # the temporal index is updated to the index of the maximum velocity.
                    if maximum_velocity != velocity:
                        updated_temporal_index = potential_temporal_indices[np.argmax(potential_velocities)]
                        # 2.8. The time and the results are updated.
                        updated_time = self.simulated_times[updated_temporal_index]
                        results = self.get_closest_simulated_results(updated_time, spatial_index)
                        velocity = results['velocity']
                        # The time increment is updated.
                        new_time_delta = abs(distance_between_cells) / abs(velocity)
                        # The spatial index is updated (mainly the sign)
                        new_spatial_index = self.update_spatial_index_from_velocity(spatial_index, velocity)
                        time_1 =  time_0 + new_time_delta

            # 2.9. The results are added to the dataframe.
            buoy_data.loc[len(buoy_data.index)] ={'time': time,
                                            'distance': distance,
                                            'water level': results['water level'],
                                            'water depth': results['water depth'],
                                            'discharge': results['discharge'],
                                            'velocity': results['velocity'],
                                            'froude': results['froude'],
                                            'wetted section': results['wetted section'],
                                            'top width': results['top width']}

            # 2.10. Updating the time and spatial index for the next  iteration.
            if new_spatial_index < number_of_cells:
                time = time_1
                spatial_index = new_spatial_index

                # (print(f'New spatial index: {spatial_index} out of {number_of_cells}'))

        return buoy_data


# --- Multiple Wolf 1D results ---
#_________________________________
class MultipleWolfresults_1D:
    """
    This class is used to plot multiple
    Wolf 1D results on the same figure.

    It is a wrapper around Wolfresults_1D class.

    The main goal is to plot the  temporal and spatial
    evolution of the water level, discharge, wetted section,
    water depth, velocity and Froude Number for different simulations.
    """
    def __init__(self,
                simulations:list[str],
                model_index:int = 0,
                figures:list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']] =['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'],
                time_step:int = -1,
                banksbed: Union[str, Zones] ='',
                landmark: Union[str,Zones]= '',
                save_as:str ='',
                figsize:tuple = (25,15),
                alpha =0.3,
                line_width = 2.,
                show = False
                ) -> None:
        """
        Constructor of the class.

        :param simulations: Simulations
        :type simulations: [str]
        :param model_index: Model index, defaults to 0
        :type model_index: int, optional
        :param figures: Figures, defaults to ['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']
        :type figures: list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']], optional
        :param time_step: Time step, defaults to -1
        :type time_step: int, optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figure size, defaults to (25,15)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param line_width: Line width, defaults to 2.
        :type line_width: float, optional
        :param show: Show, defaults to False
        :type show: bool, optional
        """

        self.models = [Wolfresults_1D(simul) for simul in simulations]
        self.model_index = model_index
        self.figures = figures
        self.time_step = time_step
        self.banksbed = banksbed
        self.landmark = landmark
        self.save_as = save_as
        self.figsize = figsize
        self.alpha = alpha
        self.linewidth = line_width
        self.show = show
        self.colors = Colors.MATPLOTLIB_CYCLE.value
        self.graph = None
        # self.ymax = max (self.models[0].find_max())

        # To update ylimits
        self.max_depths = max([model.depths_max for model in self.models])
        self.max_discharge = max([model.discharges_max for model in self.models])
        self.max_wetted_section = max([model.wetted_sections_max for model in self.models])
        self.max_velocity = max([model.velocities_max for model in self.models])
        self.max_froude= max([model.froudes_max for model in self.models])
        self.max_water_level = max([model.water_level_ymax for model in self.models])

        # grid
        self.subdivisions_x = 1000
        self.subdivisions_y = 2

    def create_graph(self, show_landmarks = False):
        """
        Create the initial figure on which other simulated results will be added.

        :param show_landmarks: Show landmarks, defaults to False
        :type show_landmarks: bool, optional
        """

        if show_landmarks:
            self.graph = self.models[self.model_index].plot_variables(figures=self.figures,
                                                                        time_step=self.time_step,
                                                                        banksbed= self.banksbed,
                                                                        landmark= self.landmark,
                                                                        save_as= self.save_as,
                                                                        figsize= self.figsize,
                                                                        alpha=self.alpha,
                                                                        grid_x_m=self.subdivisions_x,
                                                                        grid_y_m=self.subdivisions_y,
                                                                        show=False)
        else:
            self.graph = self.models[self.model_index].plot_variables(figures=self.figures,
                                                                    time_step=self.time_step,
                                                                    banksbed= self.banksbed,
                                                                    save_as= self.save_as,
                                                                    figsize= self.figsize,
                                                                    alpha=self.alpha,
                                                                    grid_x_m=self.subdivisions_x,
                                                                    grid_y_m=self.subdivisions_y,
                                                                    show=False)
        # Dictionary containing each plot characteristics(plot for update, axis, figure)
        self.characteristics = self.models[self.model_index].find_figures_characteristics(self.graph,self.figures)
        # self.fig = self.characteristics[0][-1]

    def plot_variable_lines(self):
        """
        Add other simulated results as lines.

        """

        ax: Axes
        names = ['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']
        if self.graph is None:
            self.create_graph()
        for model in self.models:
            color=next(self.colors)['color']
            for name in names:
                if name in self.characteristics :
                    char = self.characteristics[name]
                    fig = char[-1]
                    ax = char[1]
                    if name =='water level':
                        ymax =self.max_water_level + 0.05*self.max_water_level
                        ymin = self.models[self.model_index].z_min
                        self.models[self.model_index].update_yaxis(ax,ymax,ymin)
                        self._update_landmark(ax,name, self.max_water_level)
                        model.plot_line_water_level((fig,ax),color=color, linewidth=self.linewidth)

                    elif name =='water depth':
                        ymax = self.max_depths + 0.3*self.max_depths
                        self.models[self.model_index].update_yaxis(ax,ymax)
                        self._update_landmark(ax,name, self.max_depths)
                        model.plot_line_water_depth((fig,ax),color=color, linewidth=self.linewidth)

                    elif name =='discharge':
                        ymax = self.max_discharge + 0.3*self.max_discharge
                        self.models[self.model_index].update_yaxis(ax,ymax)
                        self._update_landmark(ax,name, self.max_discharge)
                        model.plot_line_discharges((fig,ax),color=color, linewidth=self.linewidth)

                    elif name =='wetted section':
                        ymax = self.max_wetted_section + 0.3*self.max_wetted_section
                        self.models[self.model_index].update_yaxis(ax,ymax)
                        self._update_landmark(ax,name, self.max_wetted_section)
                        model.plot_line_wetted_sections((fig,
                                                            ax),
                                                            color=color, linewidth=self.linewidth)

                    elif name =='velocity':
                        ymax = self.max_velocity + 0.3*self.max_velocity
                        self.models[self.model_index].update_yaxis(ax,ymax)
                        self._update_landmark(ax,name, self.max_velocity)
                        model.plot_line_velocities((fig,ax),color=color, linewidth=self.linewidth)

                    elif name =='froude':
                        ymax = self.max_froude + 0.3*self.max_froude
                        self.models[self.model_index].update_yaxis(ax,ymax)
                        self._update_landmark(ax,name, self.max_froude)
                        model.plot_line_froudes((fig,ax),color=color, linewidth=self.linewidth)

    def __plot_variable_lines(self,
                      names:list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']]=['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']):
        """
        Plot variable lines.

        :param names: Names, defaults to ['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']
        :type names: list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']], optional
        """
        ax: Axes
        if self.graph is None:
            self.create_graph()
        for name in names:
            if name in self.characteristics :
                char = self.characteristics[name]
                fig = char[-1]
                ax = char[1]
                if name =='water level':
                    ymax =self.max_water_level + 0.05*self.max_water_level
                    ymin = self.models[self.model_index].z_min
                    self.models[self.model_index].update_yaxis(ax,ymax,ymin)
                    self._update_landmark(ax,name, self.max_water_level)
                    # if self.landmark != '':
                    #     self.models[self.model_index]._landmark(self.landmark,
                    #                                             ax,
                    #                                             self.time_step,
                    #                                               variable=name,
                    #                                                 ymax= self.max_water_level)
                    for model in self.models:
                        # ax.set_ylim(top =self.max_water_level + 0.1*self.max_water_level)
                        model.plot_line_water_level((fig,
                                                    ax),
                                                    color=next(self.colors)['color'])
                elif name =='water depth':
                    ymax = self.max_depths + 0.3*self.max_depths
                    self.models[self.model_index].update_yaxis(ax,ymax)
                    self._update_landmark(ax,name, self.max_depths)
                    # if self.landmark != '':
                    #     self.models[self.model_index]._landmark(self.landmark,
                    #                                             ax,
                    #                                             self.time_step,
                    #                                               variable= name,
                    #                                                 ymax= self.max_depths)
                    for model in self.models:
                        # ax.set_ylim(top =self.max_depths + 0.3*self.max_depths)
                        model.plot_line_water_depth((fig,
                                                    ax),
                                                    color=next(self.colors)['color'])
                elif name =='discharge':
                    ymax = self.max_discharge + 0.3*self.max_discharge
                    self.models[self.model_index].update_yaxis(ax,ymax)
                    self._update_landmark(ax,name, self.max_discharge)
                    for model in self.models:
                        # ymax =self.max_discharge + 0.3*self.max_discharge
                        # ax.set_ylim(top =ymax)
                        # grid_y = model._yticks_update(ymax)
                        # ax.yaxis.set_ticks(np.arange(0, ymax, grid_y))
                        model.plot_line_discharges((fig,
                                                    ax),
                                                    color=next(self.colors)['color'])
                elif name =='wetted section':
                    ymax = self.max_wetted_section + 0.3*self.max_wetted_section
                    self.models[self.model_index].update_yaxis(ax,ymax)
                    self._update_landmark(ax,name, self.max_wetted_section)
                    for model in self.models:
                        # ax.set_ylim(top =self.max_wetted_section + 0.3*self.max_wetted_section)
                        model.plot_line_wetted_sections((fig,
                                                        ax),
                                                        color=next(self.colors)['color'])

                elif name =='velocity':
                    ymax = self.max_velocity + 0.3*self.max_velocity
                    self.models[self.model_index].update_yaxis(ax,ymax)
                    self._update_landmark(ax,name, self.max_velocity)
                    for model in self.models:
                        # ax.set_ylim(top =self.max_velocity + 0.3*self.max_velocity)
                        model.plot_line_velocities((fig,
                                                    ax),
                                                    color=next(self.colors)['color'])
                elif name =='froude':
                    ymax = self.max_froude + 0.3*self.max_froude
                    self.models[self.model_index].update_yaxis(ax,ymax)
                    self._update_landmark(ax,name, self.max_froude)
                    for model in self.models:
                        # ax.set_ylim(top =self.max_velocity + 0.3*self.max_velocity)
                        model.plot_line_froudes((fig,
                                                ax),
                                                color=next(self.colors)['color'])

    def _update_landmark(self, ax: Axes, name:str, ymax:float):
        """
        Update the landmark.

        :param ax: Axes
        :type ax: Axes
        :param name: Name
        :type name: str
        :param ymax: Y max
        :type ymax: float
        """

        if self.landmark != '':
            self.models[self.model_index]._landmark(self.landmark,
                                                    ax,
                                                    self.time_step,
                                                        variable= name,
                                                        ymax= ymax)

    def plot_water_levels(self):
        """
        Deprecated
        Plot water levels.
        """

        if self.graph is None:
            self.create_graph()
        if 'water level' in self.characteristics :
            water_level_char = self.characteristics['water level']
            for model in self.models:
                model.plot_line_water_level((water_level_char[-1],
                                                water_level_char[1]),
                                                color=next(self.colors)['color'])

    def plot_water_depths(self):
        """
        Deprecated
        Plot water depths.
        """

        if self.graph is None:
            self.create_graph()
        if 'water depth' in self.characteristics :
            water_depth_char = self.characteristics['water depth']
            for model in self.models:
                model.plot_line_water_depth((water_depth_char[-1],
                                                water_depth_char[1]),
                                                color=next(self.colors)['color'])

    def plot_discharges(self):
        """
        Deprecated
        Plot discharges.
        """
        if self.graph is None:
            self.create_graph()
        discharge_char = self.characteristics['discharge']
        for model in self.models:
            model.plot_line_discharges((discharge_char[-1],
                                         discharge_char[1]),
                                         color=next(self.colors)['color'])

    def plot_wetted_sections(self):
        """
        Deprecated
        Plot wetted sections.
        """

        if self.graph is None:
            self.create_graph()
        wetted_section_char = self.characteristics['wetted section']
        for model in self.models:
            model.plot_line_wetted_sections((wetted_section_char[-1],
                                         wetted_section_char[1]),
                                         color=next(self.colors)['color'])

    def plot_velocities(self):
        """
        Deprecated
        Plot velocities.
        """

        if self.graph is None:
            self.create_graph()
        velocity_char = self.characteristics['velocity']
        for model in self.models:
            model.plot_line_velocities((velocity_char[-1],
                                         velocity_char[1]),
                                         color=next(self.colors)['color'])

    def plot_froudes(self):
        """
        Deprecated
        Plot froudes.
        """

        if self.graph is None:
            self.create_graph()
        froude_char = self.characteristics['froude']
        for model in self.models:
            model.plot_line_froudes((froude_char[-1],
                                         froude_char[1]),
                                         color=next(self.colors)['color'])

    def plot_one_results(self,
                         model_index:int =0,
                         time_step:int = -1,
                         figures:list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']] =['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude'],
                         banksbed: Union[str, Zones] = '',
                         landmark: Union[str,Zones]= '',
                         save_as:str ='',
                         figsize:tuple = (25,15),
                         alpha =0.3,
                         grid_x_m:float= 1000.,
                         grid_y_m:float = 10.,
                         convert_step = True,
                         steps_limit = False):
        """
        Plot one results.

        :param model_index: Model index, defaults to 0
        :type model_index: int, optional
        :param time_step: Time step, defaults to -1
        :type time_step: int, optional
        :param figures: Figures, defaults to ['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']
        :type figures: list[Literal['water level', 'discharge', 'wetted section','water depth', 'velocity', 'froude']], optional
        :param banksbed: Banksbed, defaults to ''
        :type banksbed: Union[str, Zones], optional
        :param landmark: Landmark, defaults to ''
        :type landmark: Union[str,Zones], optional
        :param save_as: Save as, defaults to ''
        :type save_as: str, optional
        :param figsize: Figure size, defaults to (25,15)
        :type figsize: tuple, optional
        :param alpha: Alpha, defaults to 0.3
        :type alpha: float, optional
        :param grid_x_m: Grid x m, defaults to 1000.
        :type grid_x_m: float, optional
        :param grid_y_m: Grid y m, defaults to 10.
        :type grid_y_m: float, optional
        :param convert_step: Convert step, defaults to True
        :type convert_step: bool, optional
        :param steps_limit: Steps limit, defaults to False
        :type steps_limit: bool, optional
        """

        if model_index!= 0:
            self.model_index = model_index

        self.figures = figures

        self.graph = self.models[self.model_index].plot_variables(figures=figures,
                                                time_step=time_step,
                                                banksbed= banksbed,
                                                landmark= landmark,
                                                save_as= save_as,
                                                figsize= figsize,
                                                alpha=alpha, show=False)

        characteristics = self.models[self.model_index].find_figures_characteristics(self.graph,figures)
        wl_char = characteristics['water level']
        # wl_char[1].set_default_color_cycle
        # self.models[-1].plot_line_water_level((wl_char[-1], wl_char[1]))
        colors = rcParams["axes.prop_cycle"]()
        # colors = rcParams["axes.default_color_cycle"]()
        for model in self.models:
            model.plot_line_water_level((wl_char[-1], wl_char[1]), color=next(colors)['color'])

# --- Modify wolf 1D parameters ---
#_________________________________

class ModifyParams:
    """Modify the parameters of
    an existing simulation using
    the Wolf_Param module.
    """
    def __init__(self,simulation_folder:str = ''):
        """
        Constructor of the class.

        :param simulation_folder: _description_, defaults to ''
        :type simulation_folder: str, optional
        """
        self.simulation_folder = simulation_folder
        self.wx_exists = wx.GetApp()

    def find_simulation_file(self, file_extension:str, folder:str = '' ):
        """Find a simulation file in a simulation folder based on the file extension.

        .. note:: FIXME: Insert a checking test for double files with the same extension.

        :param file_extension: File extension
        :type file_extension: str
        :param folder: Folder, defaults to ''
        :type folder: str, optional
        :return: File path
        :rtype: str
        """
        if self.simulation_folder != "" and folder == '':
            folder = self.simulation_folder
        for filename in os.listdir(folder):
            if filename.endswith(file_extension):
                return os.path.abspath(os.path.join(folder, filename))

        raise Exception("File not found.")

    def modify_params_existing_simulation(self,
                                        simulation_folder: str='',
                                        parent = None,
                                        w: int = 460,
                                        h: int = 560,
                                        ontop: bool = False,
                                        to_read: bool = True,
                                        withbuttons: bool = True,
                                        DestroyAtClosing: bool = True,
                                        toShow: bool = True,
                                        init_GUI: bool = True,
                                        force_even_if_same_default: bool = False):
        """Modify the parameters of an existing simulation using the Wolf_Param module.

        :param simulation_folder: Simulation folder, defaults to ''
        :type simulation_folder: str, optional
        :param parent: Parent, defaults to None
        :type parent: None, optional
        :param w: Width, defaults to 460
        :type w: int, optional
        :param h: Height, defaults to 560
        :type h: int, optional
        :param ontop: Ontop, defaults to False
        :type ontop: bool, optional
        :param to_read: To read, defaults to True
        :type to_read: bool, optional
        :param withbuttons: Withbuttons, defaults to True
        :type withbuttons: bool, optional
        :param DestroyAtClosing: DestroyAtClosing, defaults to True
        :type DestroyAtClosing: bool, optional
        :param toShow: To show, defaults to True
        :type toShow: bool, optional
        :param init_GUI: Init GUI, defaults to True
        :type init_GUI: bool, optional
        :param force_even_if_same_default: Force even if same default, defaults to False
        :type force_even_if_same_default: bool, optional
        """

        if self.simulation_folder != "" and simulation_folder == '':
            simulation_folder = self.simulation_folder
        param_file = self.find_simulation_file( ".param", simulation_folder)
        app = wx.App()
        grid_param = Wolf_Param(parent= parent,
                               filename = param_file,
                               title = f"Parameters: {self.get_last_name_of_path(simulation_folder)}",
                               w = w,
                               h = h,
                               ontop = ontop,
                               to_read = to_read,
                               withbuttons = withbuttons,
                               DestroyAtClosing = DestroyAtClosing,
                               toShow = toShow,
                               init_GUI = init_GUI,
                               force_even_if_same_default = True
                               )
        app.MainLoop()

    def run_simulation(self, simulation_folder:str =''):
        """Run a wolf model with the .bat file in the simulation folder.

        :param simulation_folder: Simulation folder, defaults to ''
        :type simulation_folder: str, optional
        """
        if self.simulation_folder != "" and simulation_folder == '':
            simulation_folder = self.simulation_folder
        bat_file = self.find_simulation_file(".bat",simulation_folder)
        self.run_bat_files(bat_file)

    def run_bat_files(self, bat_file:str):
        """
        Run the .bat file in a Window's shell
        to start the computations (simulation).

        :param bat_file: Bat file
        :type bat_file: str
        """
        splitted_path = os.path.split(bat_file)
        directory = splitted_path[0]
        command = f"start cmd.exe /k {bat_file}"
        shell_window = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        logging.info(f'{directory} Check the new shell window.\nThe simulation is running...')
        if self.wx_exists:
            logging.info(f'{self.get_last_name_of_path(splitted_path[1])} Check the new shell window.\nThe simulation is running...')
        else:
            logging.warn(f'{self.get_last_name_of_path(splitted_path[1])} -> Check the new shell window.\nThe simulation is running...')

    def get_last_name_of_path(self, path_string:str):
        """Get the last folder or file of a path.

        :param path_string: Path string
        :type path_string: str
        :return: Last folder
        :rtype: str
        """
        return os.path.split(path_string)[1]
