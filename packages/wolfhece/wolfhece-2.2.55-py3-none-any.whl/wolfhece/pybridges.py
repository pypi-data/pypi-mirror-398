"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os.path import splitext, exists, join, isfile, basename
from os import listdir, scandir
import numpy as np
from shapely.geometry import LineString, MultiLineString,Point,MultiPoint,Polygon,JOIN_STYLE
from shapely.ops import nearest_points,substring, split
from typing import Literal, Union
import matplotlib.pyplot as plt
from enum import Enum
import logging
from pathlib import Path

from .PyTranslate import _
from .PyVertexvectors import Zones, zone, vector, vectorproperties, getIfromRGB
from .drawing_obj import Element_To_Draw
from .PyTranslate import _
from .wolfresults_2D import views_2D

class stored_values_unk(Enum):
    WATERDEPTH = (0, views_2D.WATERDEPTH.value)
    QX         = (1, views_2D.QX.value)
    QY         = (2, views_2D.QY.value)
    UX         = (3, views_2D.UX.value)
    UY         = (4, views_2D.UY.value)
    UNORM      = (5, views_2D.UNORM.value)
    FROUDE     = (6, views_2D.FROUDE.value)
    WATERLEVEL = (7, views_2D.WATERLEVEL.value)
    WATERSTAGE = (7, views_2D.WATERLEVEL.value)
    TOPOGRAPHY = (8, views_2D.TOPOGRAPHY.value)
    HEAD       = (-1, views_2D.HEAD.value)
    DIFFERENCE_Z_UP_DOWN    = (-1, _('Difference of waterlevel (up-down)'))
    DIFFERENCE_HEAD_UP_DOWN = (-1, _('Difference of head  (up-down)'))

class stored_values_pos(Enum):
    INDICE_I    = (0, 'Indice i')
    INDICE_J    = (1, 'Indice j')
    NUM_BLOCK   = (2, 'Block')

class stored_values_coords(Enum):
    X = (0, 'CoordX')
    Y = (1, 'CoordY')

class zones_in_file_fr_vec(Enum):
    PARTS = '3 zones'
    RIVER = 'entier'

class zones_in_file(Enum):
    PARTS = _('bridge_position')
    RIVER = _('river')
    DECK = _('deck')
    ROOF = _('roof')
    PIER = _('pier')
    CROSS_SECTIONS = _('crosssections')
    EXTRACTION = _('extraction')

class operators(Enum):
    MEDIAN = 'median'
    MIN = 'min'
    MAX = 'max'
    PERCENTILE5 = 'p5'
    PERCENTILE95 = 'p95'
    ALL ='all'

class parts_values(Enum):
    CENTRAL     = _('central')
    UPSTREAM    = _('upstream')
    DOWNSTREAM  = _('downstream')

class rivers_values(Enum):
    RIVERBED     = _('riverbed')
    LEFTBANK    = _('leftbank')
    RIGHTBANK  = _('rightbank')

class cs_values(Enum):
    UPSTREAM   = _('upstream')
    MIDDLE     = _('middle')
    DOWNSTREAM = _('downstream')

class Bridge(Zones):
    """
    Bridge class

    Representation :

            Downstream

                |
            *-------*
            |   |   |
            |  down |
            |   |   |
            *-------*
            |   |   |
            |  cent |
            |   |   |
            *-------*
            |   |   |
            |   up  |
            |   |   |
            *-------*
                |

                /\
            Upstream

    Enumeration of vertices :

                ^               ^               ^
            3-------2       0-------3       1-------2
            |   |   |       |   |   |       |   |   |
            |  cent |       |  upst |       |  down |
            |   |   |       |   |   |       |   |   |
            0-------1       1-------2       0-------3
                ^               ^               ^

    """

    @classmethod
    def new_bridge(cls, name:str):
        """
        Create a new bridge with name
        """
        new_bridge = cls()
        new_bridge.myname = name
        new_bridge.idx = name

        position = zone(name = zones_in_file.PARTS.value)
        new_bridge.add_zone(position, forceparent=True)

        new_bridge.centralpart = vector(name = parts_values.CENTRAL.value)
        position.add_vector(new_bridge.centralpart, forceparent=True)

        new_bridge.upstream = vector(name = parts_values.UPSTREAM.value)
        position.add_vector(new_bridge.upstream, forceparent=True)

        new_bridge.downstream = vector(name = parts_values.DOWNSTREAM.value)
        position.add_vector(new_bridge.downstream, forceparent=True)

        river = zone(name = zones_in_file.RIVER.value)
        new_bridge.add_zone(river, forceparent=True)

        new_bridge.leftbank = vector(name = rivers_values.LEFTBANK.value)
        new_bridge.riverbed = vector(name = rivers_values.RIVERBED.value)
        new_bridge.rightbank = vector(name = rivers_values.RIGHTBANK.value)

        river.add_vector(new_bridge.leftbank, forceparent=True)
        river.add_vector(new_bridge.riverbed, forceparent=True)
        river.add_vector(new_bridge.rightbank, forceparent=True)

        new_bridge.add_zone(zone(name = zones_in_file.DECK.value), forceparent=True)
        new_bridge.add_zone(zone(name = zones_in_file.ROOF.value), forceparent=True)
        new_bridge.add_zone(zone(name = zones_in_file.PIER.value), forceparent=True)
        new_bridge.add_zone(zone(name = zones_in_file.CROSS_SECTIONS.value), forceparent=True)
        new_bridge.add_zone(zone(name = zones_in_file.EXTRACTION.value), forceparent=True)

        new_bridge.fill_structure()

        return new_bridge

    def __init__(self, myfile='', ds:float=5.,
                 ox: float = 0, oy: float = 0,
                 tx: float = 0, ty: float = 0,
                 parent=None, is2D=True,
                 idx: str = '',
                 wx_exists:bool = False,
                 mapviewer=None
                 ):

        super().__init__(myfile, ox, oy, tx, ty, parent, is2D, idx=idx, plotted= wx_exists, mapviewer= mapviewer)
        self.init_ui()

        self.centralpart = None
        self.upstream = None
        self.downstream = None

        self.riverbed = None
        self.leftbank = None
        self.rightbank = None

        self.polygons_zone = None

        self.mapviewer = mapviewer

        self.parent = parent

        if myfile != '':
            self.myname = splitext(basename(myfile))[0]
            extension = splitext(basename(myfile))[1]


            if extension == '.vec':

                # recherche de la zone du fichier contenant les 3 parties de l'ouvrage
                curzone = self.get_zone(zones_in_file_fr_vec.PARTS.value)
                if curzone is None:
                    curzone = self.get_zone(0)
                    curzone.myname = zones_in_file_fr_vec.PARTS.value # on force le nom de la zone pour éviter de refaire le test ailleurs
                if curzone is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))

                # attribution des vecteurs pour les différentes parties de l'ouvrage

                self.centralpart       = curzone.get_vector('tablier') # 4 vertices from Upstream Left to Dowstream Left passing by Upstream Right and Downstream Right
                if self.centralpart is None:
                    self.centralpart       = curzone.get_vector('seuil') # 4 vertices from Upstream Left to Dowstream Left passing by Upstream Right and Downstream Right

                self.upstream   = curzone.get_vector('amont')   # 4 vertices from Upstream Left Deck  to Upstream Right Deck passing by Upstream Left Bank and Upstream Right Bank
                self.downstream = curzone.get_vector('aval')    # 4 vertices from Downstream Left Deck Left to Downstream Right Deck passing by Downstream Left Bank and Downstream Right Bank

                xydeck = self.centralpart.asnparray()

                # point central de l'ouvrage
                self.centerx = np.mean(xydeck[:,0]) # X coordinate of the deck
                self.centery = np.mean(xydeck[:,1]) # X coordinate of the deck
                self.curvi = 0                      # s curvilinear coordinate of the deck along a support polyline

                """
                Si certaines parties ne sont pas attribuées, il peut s'agir d'une mauvaise appellation.
                Dans ce cas, on attribue sur base de la position dans la zone
                """
                assert curzone.nbvectors==3, _('Bad number of parts')

                if self.centralpart is None:
                    self.centralpart = curzone.get_vector(0)
                if self.upstream is None:
                    self.upstream = curzone.get_vector(1)
                if self.downstream is None:
                    self.downstream = curzone.get_vector(2)

                if self.centralpart is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))
                if self.upstream is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))
                if self.downstream is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))

                curzone = self.get_zone(zones_in_file_fr_vec.RIVER.value)
                if curzone is None:
                    curzone = self.get_zone(1)
                    curzone.myname = zones_in_file_fr_vec.RIVER.value # on force le nom de la zone pour éviter de refaire le test ailleurs
                if curzone is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))

                self.riverbed = curzone.get_vector('parallèle')    # vertices from upstream to downstream
                if self.riverbed is None:
                    self.riverbed = curzone.get_vector(1)
                if self.riverbed is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))

                self.riverbed.reverse()

                self.leftbank = curzone.get_vector(2)    # vertices from upstream to downstream
                if self.leftbank is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))

                self.leftbank.reverse()

                self.rightbank = curzone.get_vector(0)    # vertices from upstream to downstream
                if self.rightbank is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))

                self.rightbank.reverse()

            elif extension == '.vecz':

                zone_names = [curzone.myname for curzone in self.myzones]

                # test if all zones are present
                for curkey in zones_in_file:
                    if curkey.value not in zone_names:
                        logging.warning(_('Zone {} not found in file {}'.format(curkey.value, myfile)))


                if zones_in_file.PARTS.value in zone_names:
                    # recherche de la zone du fichier contenant les 3 parties de l'ouvrage
                    curzone = self.get_zone(zones_in_file.PARTS.value)

                    vec_names = [curvec.myname for curvec in curzone.myvectors]
                    for curkey in parts_values:
                        if curkey.value not in vec_names:
                            logging.error(_('Vector {} not found in zone {}'.format(curkey.value, zones_in_file.PARTS.value)))

                    # attribution des vecteurs pour les différentes parties de l'ouvrage
                    self.centralpart    = curzone.get_vector(parts_values.CENTRAL.value) # 4 vertices from Upstream Left to Dowstream Left passing by Upstream Right and Downstream Right
                    self.upstream       = curzone.get_vector(parts_values.UPSTREAM.value)   # 4 vertices from Upstream Left Deck  to Upstream Right Deck passing by Upstream Left Bank and Upstream Right Bank
                    self.downstream     = curzone.get_vector(parts_values.DOWNSTREAM.value)    # 4 vertices from Downstream Left Deck Left to Downstream Right Deck passing by Downstream Left Bank and Downstream Right Bank

                xydeck = self.centralpart.asnparray()

                # point central de l'ouvrage
                self.centerx = np.mean(xydeck[:,0]) # X coordinate of the deck
                self.centery = np.mean(xydeck[:,1]) # X coordinate of the deck
                self.curvi = 0                      # s curvilinear coordinate of the deck along a support polyline

                if self.centralpart is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))
                if self.upstream is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))
                if self.downstream is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))

                if zones_in_file.RIVER.value in zone_names:
                    curzone = self.get_zone(zones_in_file.RIVER.value)

                    self.riverbed = curzone.get_vector(rivers_values.RIVERBED.value)    # vertices from upstream to downstream
                    self.leftbank = curzone.get_vector(rivers_values.LEFTBANK.value)    # vertices from upstream to downstream
                    self.rightbank = curzone.get_vector(rivers_values.RIGHTBANK.value)    # vertices from upstream to downstream

                if self.riverbed is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))
                if self.leftbank is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))
                if self.rightbank is None:
                    raise Warning(_('Bad file : {}'.format(myfile)))

        self.create_polygon_river(ds)
        self.force_plot()

        self.colorize()

    def force_plot(self):

        vecs = [self.centralpart, self.upstream, self.downstream, self.riverbed, self.leftbank, self.rightbank]
        vec: vector
        for vec in vecs:
            if vec is not None:
                vec.myprop.used=True

    def create_polygon_river(self, ds:float=5.):
        """ Create river polygons """

        if self.leftbank is not None and self.riverbed is not None and self.rightbank is not None:

            keys_zones = [curzone.myname for curzone in self.myzones]
            if "_river_auto" in keys_zones:
                logging.warning(_('Polygons already created'))
                return

            self.polygons_zone = zone(name= "_river_auto")
            self.add_zone(self.polygons_zone, forceparent=True)
            self.polygons_zone.myvectors = [self.leftbank, self.riverbed, self.rightbank] #inverse order to be up -> down

            #création des polygones de rivière
            self.polygons_zone.create_polygon_from_parallel(ds)

            self.polygons_zone = self.get_zone(-1)
            self.polygons_curvi = {}
            for curvert in self.polygons_zone.myvectors:
                self.polygons_curvi[curvert.myname] = curvert.myvertices[0].z

            for vec in self.polygons_zone.myvectors:
                vec.myprop.used=False # cache les polygones pour ne pas surcharger l'affichage éventuel

    def colorize(self):
        """Colorisation des polygones pour l'interface graphique"""

        if self.centralpart is not None and self.upstream is not None and self.downstream is not None:

            self.centralpart.myprop.color = getIfromRGB((0,255,0))
            self.upstream.myprop.color = getIfromRGB((255,0,0))
            self.downstream.myprop.color = getIfromRGB((0,0,255))

    def get_distance(self, x:float, y:float):
        """
        Compute the distance in-between x,y and the center of the deck
        """
        return np.sqrt(np.power(self.centerx-x,2)+np.power(self.centery-y,2))

    def highlighting(self, rgb=(255,0,0), linewidth=3):
        """
        Mise en évidence
        """
        self.centralpart.highlighting(rgb,linewidth)

    def withdrawal(self):
        """
        Mise en retrait
        """
        self.centralpart.withdrawal()

    def compute_distance(self, poly:LineString):
        """
        Compute the curvilinear distance along a support polyline
        """
        self.curvi = poly.project(Point([self.centerx,self.centery]))
        for curvert in self.polygons_zone.myvectors:
            centerx = np.sum(np.asarray([cur.x for cur in curvert.myvertices[:4]]))/4.
            centery = np.sum(np.asarray([cur.y for cur in curvert.myvertices[:4]]))/4.
            self.polygons_curvi[curvert.myname] = poly.project(Point([centerx,centery]))

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """Plot into GUI"""

        super().plot(sx, sy, xmin, ymin, xmax, ymax, size)

        # self.centralpart.plot()
        # self.upstream.plot()
        # self.downstream.plot()
        # self.leftbank.plot()
        # self.rightbank.plot()
        # self.riverbed.plot()

    def find_values_inside_parts(self, linked_arrays):
        """
        Récupère les valeurs à l'intérieur :
         - des parties du pont (amont, centrale, aval)
         - de la discrétisation rivière en polygones

        Retour :
         - dictionnaire dont la clé est le nom (ou l'index) du polygone dans la zone --> parties centrale, amont ou aval
         - chaque entrée est un dictionnaire dont la clé 'values' contient un dictionnaire pour chaque matrice du projet
         - chaque élément de ce sous-dictionnaire est un tuple contenant toutes les valeurs utiles


        ATTENTION : si linked_arrays est un dictionnaire, alors un niveau supérieur est ajouté sur base des clés de ce dictionnaire, dans ce cas, self.linked est un dict et non une liste

        """
        curzone = self.get_zone(zones_in_file_fr_vec.PARTS.value)

        if isinstance(linked_arrays, dict):

            self.parts_values={}
            self.linked={}

            for curkey, curgroup in linked_arrays.items():
                self.parts_values[curkey] = curzone.get_all_values_linked_polygon(curgroup, key_idx_names='name')
                self.linked[curkey] = [(curlink.idx, type(curlink)) for curlink in curgroup]

        elif isinstance(linked_arrays, list):

            self.parts_values = curzone.get_all_values_linked_polygon(linked_arrays, key_idx_names='name')
            self.linked = [(curlink.idx, type(curlink)) for curlink in linked_arrays]

        # récupération des valeurs danbs les polygones "rivière"
        curzone = self.polygons_zone
        if curzone is not None:
            if isinstance(linked_arrays, dict):
                self.river_values={}
                for curkey, curgroup in linked_arrays.items():
                    self.river_values[curkey] = curzone.get_all_values_linked_polygon(curgroup, key_idx_names='name')
            elif isinstance(linked_arrays, list):
                self.river_values = curzone.get_all_values_linked_polygon(linked_arrays, key_idx_names='name')

    def get_diff(self,
                 which_value=Literal[stored_values_unk.DIFFERENCE_Z_UP_DOWN, stored_values_unk.DIFFERENCE_HEAD_UP_DOWN],
                 operator:operators=operators.MEDIAN,
                 which_group=None):
        """Compute Head or Elevation differences"""
        diffs = {}

        up_Z   = self.get_values(parts_values.UPSTREAM, stored_values_unk.WATERLEVEL, which_group)
        down_Z = self.get_values(parts_values.DOWNSTREAM, stored_values_unk.WATERLEVEL, which_group)

        if which_value==stored_values_unk.DIFFERENCE_HEAD_UP_DOWN:
            up_UNorm   = self.get_values(parts_values.UPSTREAM, stored_values_unk.UNORM, which_group)
            down_UNorm = self.get_values(parts_values.DOWNSTREAM, stored_values_unk.UNORM, which_group)

            upvals={}
            downvals={}

            for curkey, cur_z, curunorm,  in zip(up_Z.keys(), up_Z.values(), up_UNorm.values()):
                upvals[curkey] = cur_z + np.power(curunorm,2)/(2*9.81)

            for curkey, cur_z, curunorm,  in zip(up_Z.keys(), down_Z.values(), down_UNorm.values()):
                downvals[curkey] = cur_z + np.power(curunorm,2)/(2*9.81)
        else:
            upvals  = up_Z
            downvals= down_Z

        if len(upvals) == len(downvals):
            for curkey, cur_up, cur_down in zip(upvals.keys(), upvals.values(), downvals.values()):

                if operator == operators.MEDIAN:
                    up = np.median(cur_up)
                    down = np.median(cur_down)
                elif operator == operators.MIN:
                    up = np.min(cur_up)
                    down = np.min(cur_down)
                elif operator == operators.MAX:
                    up = np.max(cur_up)
                    down = np.max(cur_down)
                elif operator == operators.PERCENTILE95:
                    up = np.percentile(cur_up,95)
                    down = np.percentile(cur_down,95)
                elif operator == operators.PERCENTILE5:
                    up = np.percentile(cur_up, 5)
                    down = np.percentile(cur_down, 5)

                diffs[curkey] = up - down

        return diffs

    def _get_heads(self,
                 which_part:parts_values,
                 which_group=None):
        """Compute Head"""
        head = {}

        z   = self.get_values(which_part, stored_values_unk.WATERLEVEL, which_group)
        unorm   = self.get_values(which_part, stored_values_unk.UNORM, which_group)

        for curkey, cur_z, curunorm,  in zip(z.keys(), z.values(), unorm.values()):
            head[curkey] = cur_z + np.power(curunorm,2)/(2*9.81)

        return head

    def _get_river_heads(self,
                       which_group=None):
        """Compute Head"""
        head = {}

        z   = self.get_river_values(stored_values_unk.WATERLEVEL, which_group)
        unorm   = self.get_river_values(stored_values_unk.UNORM, which_group)

        for curkey, cur_z, curunorm  in zip(z.keys(), z.values(), unorm.values()):
            curdict = head[curkey] = {}

            for curgroup, zpoly, unormpoly in zip(cur_z.keys(), cur_z.values(), curunorm.values()):
                curdict[curgroup] = zpoly + np.power(unormpoly,2)/(2*9.81)
        return head

    def get_values(self,
                   which_part:parts_values,
                   which_value:Union[stored_values_unk,stored_values_pos],
                   which_group=None) -> dict:
        """
        Get values for a specific part

        La donnée retournée est un dictionnaire --> dépend du typage de "self.linked" (cf "find_values_inside_parts)" pour plus d'infos)

        Soit il n'y a qu'un projet à traiter --> le dictionnaire reprend les différentes valeurs pour chaque matrice/simulation du projet
        Soit il y a plusiuers projets à traiter --> le dictionnaire contient autant d'entrées que de projet et chaque sous-dictionnaire reprend les différentes valeurs pour chaque matrice/simulation du projet
        """

        if self.parts_values is None:
            raise Warning(_('Firstly call find_values_inside_parts with linked_arrays as argument -- Retry !'))

        def fillin(pos1, pos2, part_values, part_names):
            locvalues={}
            if which_part == parts_values.CENTRAL:
                curpoly = part_values[ self.centralpart.myname ]
            elif which_part == parts_values.UPSTREAM:
                curpoly = part_values[ self.upstream.myname ]
            elif which_part == parts_values.DOWNSTREAM:
                curpoly = part_values[ self.downstream.myname ]

            curarrays = curpoly['values']

            create=False
            for curarray in curarrays.values():
                if len(curarray)>0:
                    create=True

            if create:
                for idarray, curarray in enumerate(curarrays.values()):
                    if len(curarray)>0:
                        vallist = [curval[pos1][pos2] for curval in curarray]
                        locvalues[part_names[idarray][0]] = vallist

            return locvalues

        if isinstance(self.linked, dict):
            if which_group in self.parts_values.keys():
                if which_value in stored_values_unk:
                    if which_value is stored_values_unk.HEAD:
                        values = self._get_heads(which_part, which_group=which_group)
                    elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                        raise Warning(_('Please use get_diff instead of get_values for differences'))
                    else:
                        values = fillin(0, which_value.value[0], self.parts_values[which_group], self.linked[which_group])
                    return values
                elif which_value in stored_values_pos:
                    values = fillin(1, which_value.value[0], self.parts_values[which_group], self.linked[which_group])
                    return values
                else:
                    return None
            else:
                values={}
                for (curkey, curgroup), curnames in zip(self.parts_values.items(), self.linked.values()):
                    if which_value in stored_values_unk:
                        if which_value is stored_values_unk.HEAD:
                            values[curkey] = self._get_heads(which_part, which_group=curgroup)
                        elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                            raise Warning(_('Please use get_diff instead of get_values for differences'))
                        else:
                            values[curkey] = fillin(0, which_value.value[0], curgroup, curnames)
                    elif which_value in stored_values_pos:
                        values[curkey] = fillin(1, which_value.value[0], curgroup, curnames)
                return values
        else:
            if which_value in stored_values_unk:
                if which_value is stored_values_unk.HEAD:
                    values = self._get_heads(which_part)
                elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                    raise Warning(_('Please use get_diff instead of get_values for differences'))
                else:
                    values = fillin(0, which_value.value[0], self.parts_values, self.linked)
                return values
            elif which_value in stored_values_pos:
                values = fillin(1, which_value.value[0], self.parts_values, self.linked)
                return values
            else:
                return None

    def get_river_values(self,
                         which_value:Union[stored_values_unk,stored_values_pos],
                         which_group=None) -> dict:
        """
        Get values for the river polygons

        La donnée retournée est un dictionnaire --> dépend du typage de "self.linked" (cf "find_values_inside_parts)" pour plus d'infos)

        Soit il n'y a qu'un projet à traiter --> le dictionnaire contient une entrée pour chaque polygone et les différentes valeurs pour chaque matrice/simulation du projet dans chaque polygone
        Soit il y a plusiuers projets à traiter --> le dictionnaire contient autant d'entrées que de projet et chaque sous-dictionnaire reprend les différentes valeurs comme ci-dessus
        """

        if self.river_values is None:
            raise Warning(_('Firstly call find_values_inside_parts with linked_arrays as argument -- Retry !'))

        def fillin(pos1, pos2, river_values, part_names):
            locvalues={}

            for curkey, curpoly in river_values.items():
                curdict = locvalues[curkey]={}

                curarrays = curpoly['values']

                create=False
                for curarray in curarrays.values():
                    if len(curarray)>0:
                        create=True

                if create:
                    for idarray, curarray in enumerate(curarrays.values()):
                        if len(curarray)>0:
                            vallist = [curval[pos1][pos2] for curval in curarray]
                            curdict[part_names[idarray][0]] = vallist

            return locvalues

        if isinstance(self.linked, dict):
            if which_group in self.river_values.keys():
                if which_value in stored_values_unk:
                    if which_value is stored_values_unk.HEAD:
                        values = self._get_river_heads(which_group=which_group)
                    elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                        raise Warning(_('Please use get_diff instead of get_values for differences'))
                    else:
                        values = fillin(0, which_value.value[0], self.river_values[which_group], self.linked[which_group])
                    return values
                elif which_value in stored_values_pos:
                    values = fillin(1, which_value.value[0], self.river_values[which_group], self.linked[which_group])
                    return values
                else:
                    return None
            else:
                values={}
                for (curkey, curgroup), curnames in zip(self.river_values.items(), self.linked.values()):
                    if which_value in stored_values_unk:
                        if which_value is stored_values_unk.HEAD:
                            values[curkey] = self._get_river_heads(which_group=curkey)
                        elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                            raise Warning(_('Please use get_diff instead of get_values for differences'))
                        else:
                            values[curkey] = fillin(0, which_value.value[0], curgroup, curnames)
                    elif which_value in stored_values_pos:
                        values[curkey] = fillin(1, which_value.value[0], curgroup, curnames)
                return values
        else:
            if which_value in stored_values_unk:
                if which_value is stored_values_unk.HEAD:
                    values = self._get_river_heads()
                elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                    raise Warning(_('Please use get_diff instead of get_values for differences'))
                else:
                    values = fillin(0, which_value.value[0], self.river_values, self.linked)
                return values
            elif which_value in stored_values_pos:
                values = fillin(1, which_value.value[0], self.river_values, self.linked)
                return values
            else:
                return None

    def get_values_op(self,
                      which_part:parts_values,
                      which_value:Union[stored_values_unk,stored_values_pos],
                      which_group=None,
                      operator:operators=operators.MEDIAN) -> dict:

        def extract_info(vals):
            vals_ret={}
            for curkey, curvals in vals.items():
                if curvals is not None:
                    if operator == operators.MEDIAN:
                        vals_ret[curkey] = np.median(curvals)
                    elif operator == operators.MIN:
                        vals_ret[curkey] = np.min(curvals)
                    elif operator == operators.MAX:
                        vals_ret[curkey] = np.max(curvals)
                    elif operator == operators.PERCENTILE95:
                        vals_ret[curkey] = np.percentile(curvals,95)
                    elif operator == operators.PERCENTILE5:
                        vals_ret[curkey] = np.percentile(curvals,5)
                    elif operator == operators.ALL:
                        vals_ret[curkey] =  (np.median(curvals), np.min(curvals), np.max(curvals), np.percentile(curvals,95), np.percentile(curvals,5))
            return vals_ret

        vals = self.get_values(which_part, which_value, which_group)

        if isinstance(self.linked, dict):
            if which_group in self.parts_values.keys():
                vals_ret = extract_info(vals)
            else:
                vals_ret={}
                for curkey, curvals in vals.items():
                    vals_ret[curkey] = extract_info(curvals)
        else:
            vals_ret = extract_info(vals)

        return vals_ret

    def get_river_values_op(self,
                            which_value:Union[stored_values_unk,stored_values_pos],
                            which_group=None,
                            operator:operators=operators.MEDIAN) -> dict:

        def extract_info(vals):
            vals_ret={}
            for curkeypoly, curpoly in vals.items():
                curdict = vals_ret[curkeypoly]={}
                for curkey, curvals in curpoly.items():
                    if curvals is not None:
                        if operator == operators.MEDIAN:
                            curdict[curkey] = np.median(curvals)
                        elif operator == operators.MIN:
                            curdict[curkey] = np.min(curvals)
                        elif operator == operators.MAX:
                            curdict[curkey] = np.max(curvals)
                        elif operator == operators.PERCENTILE95:
                            curdict[curkey] = np.percentile(curvals,95)
                        elif operator == operators.PERCENTILE5:
                            curdict[curkey] = np.percentile(curvals,5)
                        elif operator == operators.ALL:
                            curdict[curkey] =  (np.median(curvals), np.min(curvals), np.max(curvals), np.percentile(curvals,95), np.percentile(curvals,5))
            return vals_ret

        vals = self.get_river_values(which_value, which_group)

        if isinstance(self.linked, dict):
            if which_group in self.parts_values.keys():
                vals_ret = extract_info(vals)
            else:
                vals_ret={}
                for curkey, curvals in vals.items():
                    vals_ret[curkey] = extract_info(curvals)
        else:
            vals_ret = extract_info(vals)

        return vals_ret

    def plot_unk(self,
                 figax = None,
                 which_value:Union[stored_values_unk,stored_values_pos]=stored_values_unk.WATERLEVEL,
                 which_group=None,
                 operator:operators=operators.MEDIAN,
                 options:dict=None,
                 label=True,
                 show=False):

        if figax is None:
            fig,ax = plt.subplots(1,1)
        else:
            fig,ax = figax

        curmark='None'
        curcol = 'black'
        curlw = 1
        curls = 'solid'
        if options is not None:
            if isinstance(options,dict):
                if 'marker' in options.keys():
                    curmark=options['marker']
                if 'color' in options.keys():
                    curcol=options['color']
                if 'linestyle' in options.keys():
                    curls=options['linestyle']
                if 'linewidth' in options.keys():
                    curlw=options['linewidth']

        myval = self.get_river_values_op(which_value, which_group, operator)

        if which_group is not None:
            curproj = self.river_values[which_group]
            firstpoly = curproj[list(curproj.keys())[0]]

            nb_mod = len(firstpoly['values'])
            for curmodkey, curmod in firstpoly['values'].items():

                labelstr=''
                if label: labelstr=curmodkey

                if nb_mod>1:
                    if which_value!= stored_values_unk.TOPOGRAPHY:
                        curcol = None

                s=[]
                val=[]

                for curkey, curval in myval.items():
                    if len(curval)>0 and curmodkey in curval.keys():
                            val.append(curval[curmodkey])
                            s.append(self.polygons_curvi[curkey])

                if len(s)>0:
                    ax.plot(s, val, linewidth = curlw, linestyle=curls, marker=curmark, color=curcol, label=labelstr)
        else:

            curcol=None

            for keyproj, curproj in self.river_values.items():
                firstpoly = curproj[list(curproj.keys())[0]]
                for curmodkey, curmod in firstpoly['values'].items():

                    labelstr=''
                    if label: labelstr=curmodkey

                    if nb_mod>1:
                        if which_value!= stored_values_unk.TOPOGRAPHY:
                            curcol = None

                    s=[]
                    val=[]

                    for curkey, curval in myval[keyproj].items():
                        if len(curval)>0 and curmodkey in curval.keys():
                                val.append(curval[curmodkey])
                                s.append(self.polygons_curvi[curkey])

                    if len(s)>0:
                        ax.plot(s, val, linewidth = curlw, linestyle=curls, marker=curmark, color=curcol, label=labelstr)
        if show:
            fig.show()

        return fig,ax

    def plot_waterline(self,
                       figax=None,
                       which_group=None,
                       operator:operators=operators.MEDIAN,
                       show=False):

        fig,ax = self.plot_unk(figax, stored_values_unk.TOPOGRAPHY, which_group, operator, options={'color':'black', 'linewidth':2}, label=False, show=False)
        figax=(fig,ax)
        self.plot_unk(figax, stored_values_unk.WATERLEVEL, which_group, operator, options={'color':'blue', 'linewidth':2}, show=False)

        ax.set_ylabel(_('Water leval [mDNG]'))
        ax.set_xlabel(_('Abscissa from upstream [m]'))
        fig.suptitle(self.myname + ' -- ' +_('Water surface profile'))

        if show:
            fig.show()

        return fig,ax

    def plot_waterhead(self,
                       figax=None,
                       which_group=None,
                       operator:operators=operators.MEDIAN,
                       show=False):

        fig,ax = self.plot_unk(figax, stored_values_unk.HEAD, which_group, operator, options={'color':'blue', 'linewidth':2}, show=False)

        ax.set_ylabel(_('Water head [m_water]'))
        ax.set_xlabel(_('Abscissa from upstream [m]'))
        fig.suptitle(self.myname + ' -- ' +_('Water head profile'))

        if show:
            fig.show()

        return fig,ax

    def plot_deck(self, ax, width, height, lower_level):

        s = self.curvi

        x = [s-width/2, s+width/2, s+width/2, s-width/2]
        z = [lower_level, lower_level, lower_level+height, lower_level+height]

        ax.fill(x, z, color= 'black', lw = 2, hatch = _('///'), edgecolor = 'black')

class Bridges(Element_To_Draw):

    def __init__(self, directory:str, idx: str = '', plotted: bool = True, mapviewer=None, need_for_wx: bool = False, TypeObj = Bridge) -> None:

        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self.myelts = {}
        self.mysites = {}

        self.active_elt = None
        self.active_site= None

        self.keys_values = None

        self._directory = directory

        self.xmin = 0.
        self.xmax = 0.
        self.ymin = 0.
        self.ymax = 0.

        if exists(directory):
            for filename in scandir(directory):
                # checking if it is a file
                if filename.is_file():
                    if filename.path.endswith('.vec') or filename.path.endswith('.vecz'):
                        self.myelts[filename] = TypeObj(filename.path, idx=Path(filename).stem, parent=mapviewer)

            self.find_minmax(True)

    def addnew(self, idx: str = ''):
        """
        Add a new bridge
        """

        if idx in self.myelts.keys():
            logging.warning(_('Bridge {} already exists'.format(idx)))
            logging.warning(_('Please choose another name'))
            return

        newbridge = Bridge.new_bridge(idx)

        newbridge.filename = self._directory + '/' + idx + '.vecz'

        self.myelts[idx] = newbridge

        self.find_minmax(True)

        return newbridge

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot elements inside PyDraw
        """
        for curbridge in self.myelts.values():
            curbridge:Bridge
            curbridge.plot()

    def find_minmax(self, update=False):
        """
        Find Min and Max for graphical/GUI needs
        """
        if update:
            for curbridge in self.myelts.values():
                curbridge:Bridge
                curbridge.find_minmax(update)

        if len(self.myelts)>0:
            self.xmin = np.min(np.asarray([curbridge.xmin for curbridge in self.myelts.values()]))
            self.xmax = np.max(np.asarray([curbridge.xmax for curbridge in self.myelts.values()]))
            self.ymin = np.min(np.asarray([curbridge.ymin for curbridge in self.myelts.values()]))
            self.ymax = np.max(np.asarray([curbridge.ymax for curbridge in self.myelts.values()]))
        else:
            self.xmin = -99999
            self.xmax = -99999
            self.ymin = -99999
            self.ymax = -99999

    def _get_list(self, site) -> list[Bridge]:
        if site is None:
            curlist = list(self.myelts.values())
        else:
            if site in self.mysites.keys():
                curlist = self.mysites[site]

        self.active_site=site

        return curlist

    def get_elts(self, site) ->list[Bridge]:

        return self._get_list(site)

    def find_nearest(self, x:float, y:float, site:str=None) -> Bridge:
        """
        Find the nearest bridge

        site : (optional) key name of a site
        """
        self.active_elt:Bridge

        if self.active_elt is not None:
            self.active_elt.withdrawal()

        dist = np.argmin([curbridge.get_distance(x,y) for curbridge in self._get_list(site)])
        self.active_elt = self._get_list(site)[dist]

        if self.active_elt is not None:
            self.active_elt.highlighting()

        return self.active_elt

    def find_inside_poly(self, vec:vector)->list:
        """
        Find bridges inside polygon/vector
        """
        polyls = vec.polygon
        bridges = list(self.myelts.values())

        mysel=[]
        for curbridge in bridges:
            xy = Point([curbridge.centerx, curbridge.centery])
            if polyls.contains(xy):
                mysel.append(curbridge)

        return mysel

    def select_inside_contour(self, contours:Zones):
        """
        Sort bridges inside "contour" stored in multiple zones

        Fill-in dict "self.sites" with key names based on names of zones
        """
        for curzone in contours.myzones:
            curzone:zone
            contour = curzone.get_vector('contour')

            if contour is not None:
                self.mysites[curzone.myname] = self.find_inside_poly(contour)

    def compute_distances(self, poly:vector, site:str=None):
        """
        Compute the curvilinear distance along a support polyline

        site : (optional) key name of a site
        """
        polyls = poly.asshapely_ls()

        for curbridge in self._get_list(site):
            curbridge.compute_distance(polyls)

    def get_curvis(self, site:str=None)->list:
        """
        Crée une liste contenant les coordonnées curviligne des ponts
        """
        curvis = [curbridge.curvi for curbridge in self._get_list(site)]

        return curvis

    def get_centralparts(self, site:str=None)-> zone:
        """
        Crée une nouvelle zone avec tous les tabliers de ponts
        """
        mydecks = zone(name='central parts')

        for curbridge in self._get_list(site):
            mydecks.add_vector(curbridge.centralpart)

        return mydecks

    def get_upstreams(self, site:str=None)-> zone:
        """
        Crée une nouvelle zone avec tous les zones amont de ponts
        """
        myupstreams = zone(name='upstreams')

        for curbridge in self._get_list(site):
            myupstreams.add_vector(curbridge.upstream)

        return myupstreams

    def get_downstreams(self, site:str=None)-> zone:
        """
        Crée une nouvelle zone avec tous les zones aval de ponts
        """
        mydownstreams = zone(name='downstreams')

        for curbridge in self._get_list(site):
            mydownstreams.add_vector(curbridge.downstream)

        return mydownstreams

    def find_values_inside_parts(self, linked_arrays, site:str=None):
        """
        Récupère les valeurs à l'intérieur des parties du pont

        Stockage dans chaque ouvrage
        On retient par contre dans l'objet courant les clés des matrices sur lesquelles on travaille   --> keys_values
        """
        for curbridge in self._get_list(site):
            curbridge:Bridge
            curbridge.find_values_inside_parts(linked_arrays)

        if isinstance(linked_arrays, dict):
            self.keys_values = list(linked_arrays.keys())
        else:
            self.keys_values = None

    def get_values(self,
                   which_part:parts_values,
                   which_value:Union[stored_values_unk, stored_values_pos],
                   which_group=None,
                   site:str=None) -> dict:

        values = {}
        for curbridge in self._get_list(site):
            curbridge:Bridge
            values[curbridge.myname] = curbridge.get_values(which_part, which_value, which_group)

        return values

    def get_diff(self, which_value, which_group=None, operator:operators=operators.MEDIAN, site:str=None) -> dict:

        values = {}
        for curbridge in self._get_list(site):
            curbridge:Bridge
            values[curbridge.myname] = curbridge.get_diff(which_value, operator, which_group)

        return values

    def get_river_values(self,
                         which_value:Union[stored_values_unk, stored_values_pos],
                         which_group=None,
                         site:str=None) -> dict:

        values = {}
        for curbridge in self._get_list(site):
            curbridge:Bridge
            values[curbridge.myname] = curbridge.get_river_values(which_value, which_group)

        return values

    def plot_landmarks(self,landmarks, s_landmarks, ax, ypos, plot_text=True):

        for (name, (x,y)), s in zip(landmarks, s_landmarks):
            if plot_text:
                ax.text(s, ypos, name, rotation=90, horizontalalignment='left')

            ax.plot([s,s], [0,ypos-.1])

    def plot_group(self,
                   which_part:parts_values=None,
                   which_value:Union[stored_values_unk, stored_values_pos]=None,
                   which_group=None,
                   operator:operators=operators.MEDIAN,
                   options:dict=None,
                   fig=None, ax=None,
                   ybounds=None,
                   site:str=None,
                   show=True):

        if ax is None:
            fig, ax = plt.subplots(1,1)
            fig.set_size_inches(25,10)
        ax.set_title(which_group)

        curmark='.'
        curcol = 'black'
        if options is not None:
            if isinstance(options,dict):
                if 'marker' in options.keys():
                    curmark=options['marker']
                if 'color' in options.keys():
                    curcol=options['color']

        curvi = self.get_curvis(site)

        if which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN,stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
            z_dict = self.get_diff(which_value, which_group, operator, site)

            for idx, curpol in enumerate(z_dict.values()):
                if curpol is not None:
                    #bouclage sur les éléments

                    #curpol est un dictionnaire qui peut contenir plusieurs entrées si le pont appartient à plusieurs simulations
                    for curkey, curvals in enumerate(curpol.values()):
                        if curvals is not None:
                            ax.scatter(curvi[idx], curvals, marker=curmark, c=curcol)
                        else:
                            test=1
        else:
            z_dict = self.get_values(which_part, which_value, which_group, site)

            for idx, curpol in enumerate(z_dict.values()):
                #bouclage sur les éléments

                #curpol est un dictionnaire qui peut contenir plusieurs entrées si le pont appartient à plusieurs simulations
                for curkey, curvals in enumerate(curpol.values()):
                    if curvals is not None:
                        if operator == operators.MEDIAN:
                            ax.scatter(curvi[idx], np.median(curvals), marker=curmark, c=curcol)
                        elif operator == operators.MIN:
                            ax.scatter(curvi[idx], np.min(curvals), marker=curmark, c=curcol)
                        elif operator == operators.MAX:
                            ax.scatter(curvi[idx], np.max(curvals), marker=curmark, c=curcol)
                        elif operator == operators.PERCENTILE95:
                            ax.scatter(curvi[idx], np.percentile(curvals,95), marker=curmark, c=curcol)
                        elif operator == operators.PERCENTILE5:
                            ax.scatter(curvi[idx], np.percentile(curvals,5), marker=curmark, c=curcol)
                        elif operator == operators.ALL:
                            ax.scatter(curvi[idx], np.median(curvals), marker=curmark, c=curcol)
                            ax.scatter(curvi[idx], np.min(curvals), marker=curmark, c=curcol)
                            ax.scatter(curvi[idx], np.max(curvals), marker=curmark, c=curcol)
                            ax.scatter(curvi[idx], np.percentile(curvals,95), marker=curmark, c=curcol)
                            ax.scatter(curvi[idx], np.percentile(curvals,5), marker=curmark, c=curcol)

        if ybounds is not None:
            ax.set_ylim(ybounds[0], ybounds[1])

        # ax.plot([0,np.max(curvi)],[1,1], c='gray')

        ax.set_xlabel('Abscissa [m] from upstream')
        ax.set_ylabel(which_value.value[1])

        fig.tight_layout()

        if show:
            plt.show()

        return fig,ax

    def plot_part_vs_part_group(self,
                                which_parts:list=None,
                                which_value:Union[stored_values_unk, stored_values_pos]=None,
                                which_group=None,
                                operator:operators=operators.MEDIAN,
                                options:dict=None,
                                fig=None, ax=None,
                                ybounds=None,
                                site:str=None,
                                show=True):

        assert isinstance(which_parts, list), _('It is not a list')
        assert len(which_parts)==2, _('The list must conatins 2 elements and only 2')

        if ax is None:
            fig, ax = plt.subplots(1,1)
            fig.set_size_inches(25,10)

        ax.set_title(which_group + ' - ' + which_parts[0].value +' vs '+which_parts[1].value )

        z_dict_1 = self.get_values(which_parts[0], which_value, which_group, site)
        z_dict_2 = self.get_values(which_parts[1], which_value, which_group, site)

        ax.set_xlabel(_(which_parts[0].value))
        ax.set_ylabel(_(which_parts[1].value))

        curmark='.'
        curcol = 'black'
        if options is not None:
            if isinstance(options,dict):
                if 'marker' in options.keys():
                    curmark=options['marker']
                if 'color' in options.keys():
                    curcol=options['color']

        for curpol1, curpol2 in zip(z_dict_1.values(), z_dict_2.values()):
            #bouclage sur les éléments

            #curpol est un dictionnaire qui peut contenir plusieurs entrées si le pont appartient à plusieurs simulations
            for curvals1, curvals2 in zip(curpol1.values(), curpol2.values()):
                if (curvals1 is not None) and (curvals2 is not None):

                    if operator == operators.MEDIAN:
                        ax.scatter(np.median(curvals1), np.median(curvals2), marker=curmark, c=curcol)
                    elif operator == operators.MIN:
                        ax.scatter(np.min(curvals1), np.min(curvals2), marker=curmark, c=curcol)
                    elif operator == operators.MAX:
                        ax.scatter(np.max(curvals1), np.max(curvals2), marker=curmark, c=curcol)
                    elif operator == operators.PERCENTILE95:
                        ax.scatter(np.percentile(curvals1,95), np.percentile(curvals2,95), marker=curmark, c=curcol)
                    elif operator == operators.PERCENTILE5:
                        ax.scatter(np.percentile(curvals1,5), np.percentile(curvals2,5), marker=curmark, c=curcol)
                    elif operator == operators.ALL:
                        ax.scatter(np.median(curvals1), np.median(curvals2), marker=curmark, c=curcol)
                        ax.scatter(np.min(curvals1), np.min(curvals2), marker=curmark, c=curcol)
                        ax.scatter(np.max(curvals1), np.max(curvals2), marker=curmark, c=curcol)
                        ax.scatter(np.percentile(curvals1,95), np.percentile(curvals2,95), marker=curmark, c=curcol)
                        ax.scatter(np.percentile(curvals1,5), np.percentile(curvals2,5), marker=curmark, c=curcol)

        if ybounds is not None:
            ax.set_xlim(ybounds[0], ybounds[1])
            ax.set_ylim(ybounds[0], ybounds[1])

            ax.plot([ybounds[0],ybounds[1]],[ybounds[0],ybounds[1]],c='gray')
            ax.plot([ybounds[0],ybounds[1]],[1,1],c='gray')

            ax.plot([1,1],[ybounds[0],ybounds[1]],c='gray')

            ax.set_aspect('equal')

        fig.tight_layout()

        if show:
            plt.show()

        return fig,ax

    def plot_part_group_vs_group(self,
                                 which_part:parts_values=None,
                                 which_value:Union[stored_values_unk, stored_values_pos]=None,
                                 which_groups:list=None,
                                 operator:operators=operators.MEDIAN,
                                 options:dict=None,
                                 fig=None, ax=None,
                                 ybounds=None,
                                 site:str=None,
                                 show=True):

        assert isinstance(which_groups, list), _('It is not a list')
        assert len(which_groups)==2, _('The list must conatins 2 elements and only 2')

        if ax is None:
            fig, ax = plt.subplots(1,1)
            fig.set_size_inches(25,10)

        ax.set_xlabel(_(which_groups[0]))
        ax.set_ylabel(_(which_groups[1]))

        curmark='.'
        curcol = 'black'
        if options is not None:
            if isinstance(options,dict):
                if 'marker' in options.keys():
                    curmark=options['marker']
                if 'color' in options.keys():
                    curcol=options['color']

        if which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN,stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
            z_dict_1 = self.get_diff(which_value, which_groups[0], operator, site)
            z_dict_2 = self.get_diff(which_value, which_groups[1], operator, site)

            for curpol1, curpol2 in zip(z_dict_1.values(), z_dict_2.values()):
                #bouclage sur les éléments
                if curpol1 is not None and curpol2 is not None:
                    #curpol est un dictionnaire qui peut contenir plusieurs entrées si le pont appartient à plusieurs simulations
                    for curvals1, curvals2 in zip(curpol1.values(), curpol2.values()):
                        if (curvals1 is not None) and (curvals2 is not None):
                                ax.scatter(curvals1, curvals2, marker=curmark, c=curcol)
        else:
            ax.set_title(which_part.value + ' - ' + which_groups[0] + ' vs ' + which_groups[1])

            z_dict_1 = self.get_values(which_part, which_value, which_groups[0], site)
            z_dict_2 = self.get_values(which_part, which_value, which_groups[1], site)


            for curpol1, curpol2 in zip(z_dict_1.values(), z_dict_2.values()):
                #bouclage sur les éléments

                #curpol est un dictionnaire qui peut contenir plusieurs entrées si le pont appartient à plusieurs simulations
                for curvals1, curvals2 in zip(curpol1.values(), curpol2.values()):
                    if (curvals1 is not None) and (curvals2 is not None):

                        if operator == operators.MEDIAN:
                            ax.scatter(np.median(curvals1), np.median(curvals2), marker=curmark, c=curcol)
                        elif operator == operators.MIN:
                            ax.scatter(np.min(curvals1), np.min(curvals2), marker=curmark, c=curcol)
                        elif operator == operators.MAX:
                            ax.scatter(np.max(curvals1), np.max(curvals2), marker=curmark, c=curcol)
                        elif operator == operators.PERCENTILE95:
                            ax.scatter(np.percentile(curvals1,95), np.percentile(curvals2,95), marker=curmark, c=curcol)
                        elif operator == operators.PERCENTILE5:
                            ax.scatter(np.percentile(curvals1,5), np.percentile(curvals2,5), marker=curmark, c=curcol)
                        elif operator == operators.ALL:
                            ax.scatter(np.median(curvals1), np.median(curvals2), marker=curmark, c=curcol)
                            ax.scatter(np.min(curvals1), np.min(curvals2), marker=curmark, c=curcol)
                            ax.scatter(np.max(curvals1), np.max(curvals2), marker=curmark, c=curcol)
                            ax.scatter(np.percentile(curvals1,95), np.percentile(curvals2,95), marker=curmark, c=curcol)
                            ax.scatter(np.percentile(curvals1,5), np.percentile(curvals2,5), marker=curmark, c=curcol)

        if ybounds is not None:
            ax.set_xlim(ybounds[0], ybounds[1])
            ax.set_ylim(ybounds[0], ybounds[1])

            ax.plot([ybounds[0],ybounds[1]],[ybounds[0],ybounds[1]],c='gray')
            ax.plot([ybounds[0],ybounds[1]],[1,1],c='gray')

            ax.plot([1,1],[ybounds[0],ybounds[1]],c='gray')

            ax.set_aspect('equal')

        fig.tight_layout()

        if show:
            plt.show()

        return fig,ax

    def plot_all_groups(self,
                        which_part:parts_values=None,
                        which_value:Union[stored_values_unk, stored_values_pos]=None,
                        operator:operators=operators.MEDIAN,
                        options:dict=None,
                        fig=None, ax=None,
                        ybounds=None,
                        site:str=None,
                        show=True):

        """Graphique de toutes les valeurs associées aux éléments"""
        if self.keys_values is not None:
            if len(self.keys_values)>1:
                if ax is None:
                    fig, axes = plt.subplots(len(self.keys_values),1)
                else:
                    axes=ax

                for idx, curgroup in enumerate(self.keys_values):
                    self.plot_group(which_part, which_value, curgroup, operator, options, fig, axes[idx], ybounds, site, False)
                if show:
                    plt.show()
            else:
                fig, axes = self.plot_group(which_part, which_value, self.keys_values[0], operator, options, ybounds= ybounds, site=site, show=show)
        else:
            fig, axes = self.plot_group(which_part, which_value, None, operator, options, ybounds= ybounds, site=site, show=show)

        return fig,axes

    def plot_vs_all_groups(self,
                           which_part_source:parts_values=None,
                           which_value:Union[stored_values_unk, stored_values_pos]=None,
                           operator:operators=operators.MEDIAN,
                           options:dict=None,
                           fig=None, ax=None,
                           ybounds=None,
                           site:str=None,
                           show=True):
        """Graphique de toutes les valeurs associées aux éléments"""

        if self.keys_values is not None:
            if len(self.keys_values)>1:
                if ax is None:
                    fig, axes = plt.subplots(len(self.keys_values),len(parts_values))
                else:
                    axes=ax

                for idx, curgroup in enumerate(self.keys_values):
                    for idx2, curpart in enumerate(parts_values):

                        self.plot_part_vs_part_group([which_part_source, curpart], which_value, curgroup, operator, options, fig, axes[idx, idx2], ybounds, site, False)

                if show:
                    plt.show()
            else:
                if ax is None:
                    fig, axes = plt.subplots(1,len(parts_values))
                else:
                    axes=ax

                for idx2, curpart in enumerate(parts_values):
                    self.plot_part_vs_part_group([which_part_source, curpart], which_value, self.keys_values[0], operator, options, fig, axes[idx2], ybounds= ybounds, site=site, show=show)
        else:
            if ax is None:
                fig, axes = plt.subplots(1,len(parts_values))
            else:
                axes=ax
            for idx2, curpart in enumerate(parts_values):
                self.plot_part_vs_part_group([which_part_source, curpart], which_value, None, operator, options, fig, axes[idx2], ybounds= ybounds, site=site, show=show)

        return fig,axes

    def plot_all_vs_groups(self,
                           which_part:parts_values=None,
                           which_value:Union[stored_values_unk, stored_values_pos]=None,
                           which_group_source=None,
                           operator:operators=operators.MEDIAN,
                           options:dict=None,
                           fig=None, ax=None,
                           ybounds=None,
                           site:str=None,
                           show=True):
        """Graphique de toutes les valeurs associées aux éléments"""

        if self.keys_values is not None:
            if len(self.keys_values)>1:

                if ax is None:
                    fig, axes = plt.subplots(1,len(self.keys_values))
                else:
                    axes=ax

                for idx, curgroup in enumerate(self.keys_values):
                    self.plot_part_group_vs_group(which_part, which_value, [which_group_source, curgroup], operator, options, fig, axes[idx], ybounds, site, False)

                if show:
                    plt.show()

                return fig,axes
            else:
                return None
        else:
            return None

class Weir(Bridge):

    def __init__(self, myfile='', ds: float = 5,
                 ox: float = 0, oy: float = 0,
                 tx: float = 0, ty: float = 0,
                 parent=None, is2D=True,
                 idx='',
                 wx_exists: bool = False):

        super().__init__(myfile, ds, ox, oy, tx, ty, parent, is2D, idx, wx_exists)

    def colorize(self):
        self.centralpart.myprop.color = getIfromRGB((102,102,255))
        self.upstream.myprop.color    = getIfromRGB((255,0,127))
        self.downstream.myprop.color  = getIfromRGB((102,0,204))

class Weirs(Bridges):

    def __init__(self, directory: str,
                 idx:str='', plotted:bool=True,
                 mapviewer=None, need_for_wx: bool = False,
                 TypeObj = Weir) -> None:

        super().__init__(directory, idx, plotted, mapviewer, need_for_wx= need_for_wx, TypeObj=TypeObj)

    def _get_list(self, site) -> list[Weir]:
        if site is None:
            curlist = list(self.myelts.values())
        else:
            if site in self.mysites.keys():
                curlist = self.mysites[site]

        self.active_site=site

        return curlist

    def get_elts(self, site) ->list[Weir]:

        return self._get_list(site)
