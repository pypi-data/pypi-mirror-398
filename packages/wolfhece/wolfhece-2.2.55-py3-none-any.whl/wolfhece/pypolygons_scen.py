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
from .wolfresults_2D import views_2D, Wolfresults_2D
from .Results2DGPU import wolfres2DGPU
from .pybridges import stored_values_pos, stored_values_unk, parts_values, operators, stored_values_coords

from zipfile import ZIP_DEFLATED, ZipFile

class ZipFileWrapper(ZipFile):
    def open(self, name="data", mode="r", pwd=None, **kwargs):
        return super().open(name=name, mode=mode, pwd=pwd, **kwargs)

    def read(self):
        return super().read(name="data")

class Extracting_Zones(Zones):
    """
    Classe permettant de récupérer les valeurs à l'intérieur des polygones
    définis dans plusieurs zones.

    Ces polygones ne sont pas nécessairement ordonnés ou relatifs au lit mineur.

    """

    def __init__(self, filename='', ox: float = 0, oy: float = 0, tx: float = 0, ty: float = 0, parent=None, is2D=True, idx: str = '', plotted: bool = True, mapviewer=None, need_for_wx: bool = False) -> None:
        super().__init__(filename, ox, oy, tx, ty, parent, is2D, idx, plotted, mapviewer, need_for_wx)

        self.parts:dict = None # Store the values inside the polygons - dict[dict] or dict[list]
        self.linked:Union[dict, list] = None # Object from which the values are extracted - dict or list

    def cache_data(self, outputfile:str):
        """
        Serialize the values in a file
        """
        self._serialize_values(outputfile)

    def load_data(self, inputfile:str):
        """
        Deserialize the values from a file
        """
        self._deserialize_values(inputfile)

    def _serialize_values(self, outputfile:str):
        """
        Serialize the values in a file
        """

        import json
        from codecs import getwriter
        from typing import IO

        class NumpyArrayEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif obj == Wolfresults_2D:
                    return 'CPU'
                elif obj == wolfres2DGPU:
                    return 'GPU'

                return json.JSONEncoder.default(self, obj)

        def _json_dump_bytes(fp: IO, obj):
            StreamWriter = getwriter("utf-8")
            return json.dump(fp=StreamWriter(fp), obj=obj, cls=NumpyArrayEncoder, indent=4)

        def json_dump_zip(fp: IO, obj):
            with ZipFileWrapper(fp, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as zip_file:
                with zip_file.open(mode="w") as _fp:
                    _json_dump_bytes(fp=_fp, obj=obj)


        with open(outputfile, 'wb') as f:

            json_dump_zip(fp = f, obj = {'linked' : self.linked, 'values': self.parts})


    def _deserialize_values(self, inputfile:str):
        """
        Deserialize the values from a file
        """

        import json
        from codecs import getwriter
        from typing import IO

        def json_load_zip(fp: IO):
            with ZipFileWrapper(fp, mode="r") as zip_file:
                return json.load(zip_file)

        inputfile = Path(inputfile)
        if not inputfile.exists():
            logging.error(_('File {0} does not exist').format(inputfile))
            return

        with open(inputfile, 'rb') as f:
            data = json_load_zip(f) #json.load(f)

        tmp_linked = data['linked']
        if isinstance(tmp_linked, dict):
            self.linked = {}
            for curkey, curgroup in tmp_linked.items():
                self.linked[curkey] = [(curlink[0], Wolfresults_2D if curlink[1] == 'CPU' else wolfres2DGPU) for curlink in curgroup]

            tmp_values = data['values']
            self.parts = {}

            for cuzone, curparts in tmp_values.items():
                self.parts[cuzone] = {}

                for curproj, curdict in curparts.items():
                    self.parts[cuzone][curproj] = {}
                    for curpoly, curval in curdict.items():
                        self.parts[cuzone][curproj][curpoly] = {}
                        for curgroup, curarray in curval.items():
                            locdict = self.parts[cuzone][curproj][curpoly][curgroup] = {}

                            for cursim, curnparray in curarray.items():
                                locdict[cursim] = np.array([np.array([ tuple(lst1), np.array(lst2, dtype= np.int32)], dtype=object ) for lst1, lst2 in curnparray], dtype=object)

        elif isinstance(tmp_linked, list):
            self.linked = [(curlink[0], Wolfresults_2D if curlink[1] == 'CPU' else wolfres2DGPU) for curlink in tmp_linked]

            tmp_values = data['values']
            self.parts = {}

            for cuzone, curparts in tmp_values.items():
                self.parts[cuzone] = {}

                for curpoly, curval in curparts.items():
                    self.parts[cuzone][curpoly] = {}
                    for curgroup, curarray in curval.items():
                            locdict = self.parts[cuzone][curpoly][curgroup] = {}

                            for cursim, curnparray in curarray.items():
                                locdict[cursim] = np.array([np.array([ tuple(lst1), np.array(lst2, dtype= np.int32)], dtype=object ) for lst1, lst2 in curnparray], dtype=object)


    def find_values_inside_parts(self, linked_arrays: dict | list):
        """
        Get values inside the polygons defined in the zones.

        :param linked_arrays: list or dict of arrys/simulations to link with the polygons.

        ***
        ATTENTION : si linked_arrays est un dictionnaire, alors un niveau supérieur est ajouté sur base des clés de ce dictionnaire, dans ce cas, self.linked est un dict et non une liste
        ***

        """
        if isinstance(linked_arrays, dict):

            self.linked = {}
            for curkey, curgroup in linked_arrays.items():
                self.linked[curkey] = [(curlink.idx, type(curlink)) for curlink in curgroup]

        elif isinstance(linked_arrays, list):

            self.linked = [(curlink.idx, type(curlink)) for curlink in linked_arrays]

        self.parts = {}
        for curzone in self.myzones:
            if isinstance(linked_arrays, dict):
                locparts = self.parts[curzone.myname] = {}
                for curkey, curgroup in linked_arrays.items():
                    locparts[curkey] = curzone.get_all_values_linked_polygon(curgroup, key_idx_names='name', getxy=True)

            elif isinstance(linked_arrays, list):
                self.parts[curzone.myname]  = curzone.get_all_values_linked_polygon(linked_arrays, key_idx_names='name', getxy=True)

    def _get_heads(self,
                 which_vec:str,
                 which_group=None):
        """Compute Head"""
        head = {}

        z   = self.get_values(which_vec, stored_values_unk.WATERLEVEL, which_group)
        unorm   = self.get_values(which_vec, stored_values_unk.UNORM, which_group)

        for curkey, cur_z, curunorm,  in zip(z.keys(), z.values(), unorm.values()):
            head[curkey] = cur_z + np.power(curunorm,2)/(2*9.81)

        return head

    def get_values(self,
                   which_vec:str,
                   which_value:Union[stored_values_unk, stored_values_pos, stored_values_coords],
                   which_group=None) -> dict:
        """
        Get values for a specific part

        La donnée retournée est un dictionnaire --> dépend du typage de "self.linked" (cf "find_values_inside_parts)" pour plus d'infos)

        Soit il n'y a qu'un projet à traiter --> le dictionnaire reprend les différentes valeurs pour chaque matrice/simulation du projet
        Soit il y a plusiuers projets à traiter --> le dictionnaire contient autant d'entrées que de projet et chaque sous-dictionnaire reprend les différentes valeurs pour chaque matrice/simulation du projet
        """

        loc_parts_values = None

        if which_group is not None:
            for cur_parts in self.parts.values():
                if which_vec in cur_parts[which_group].keys():
                    loc_parts_values = cur_parts
                    break

        if loc_parts_values is None:
            return {}

        def fillin(pos1, pos2, part_values, part_names):
            locvalues={}

            curpoly = part_values[ which_vec ]
            curarrays = curpoly['values']

            create=False
            for curarray in curarrays.values():
                if isinstance(curarray, tuple):
                    # on a également repris les coordonnées
                    if len(curarray[0])>0:
                        create=True
                else:
                    if len(curarray)>0:
                        create=True

            if create:
                for idarray, curarray in enumerate(curarrays.values()):
                    if isinstance(curarray, tuple):
                        if pos1==-1:
                            if len(curarray[1])>0:
                                vallist = [curval[pos2] for curval in curarray[1]]
                                locvalues[part_names[idarray][0]] = vallist
                        else:
                            if len(curarray[0])>0:
                                vallist = [curval[pos1][pos2] for curval in curarray[0]]
                                locvalues[part_names[idarray][0]] = vallist
                    else:
                        if len(curarray)>0:
                            vallist = [curval[pos1][pos2] for curval in curarray]
                            locvalues[part_names[idarray][0]] = vallist

            return locvalues

        if isinstance(self.linked, dict):
            if which_group in loc_parts_values.keys():
                if which_value in stored_values_unk:
                    if which_value is stored_values_unk.HEAD:
                        values = self._get_heads(which_vec, which_group=which_group)
                    elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                        raise Warning(_('Please use get_diff instead of get_values for differences'))
                    else:
                        values = fillin(0, which_value.value[0], loc_parts_values[which_group], self.linked[which_group])
                    return values
                elif which_value in stored_values_pos:
                    values = fillin(1, which_value.value[0], loc_parts_values[which_group], self.linked[which_group])
                    return values
                elif which_value in stored_values_coords:
                    values = fillin(-1, which_value.value[0], loc_parts_values[which_group], self.linked[which_group])
                    return values
                else:
                    return None
            else:
                values={}
                for (curkey, curgroup), curnames in zip(loc_parts_values.items(), self.linked.values()):
                    if which_value in stored_values_unk:
                        if which_value is stored_values_unk.HEAD:
                            values[curkey] = self._get_heads(which_vec, which_group=curgroup)
                        elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                            raise Warning(_('Please use get_diff instead of get_values for differences'))
                        else:
                            values[curkey] = fillin(0, which_value.value[0], curgroup, curnames)
                    elif which_value in stored_values_pos:
                        values[curkey] = fillin(1, which_value.value[0], curgroup, curnames)
                    elif which_value in stored_values_coords:
                        values[curkey] = fillin(-1, which_value.value[0], curgroup, curnames)
                return values
        else:
            if which_value in stored_values_unk:
                if which_value is stored_values_unk.HEAD:
                    values = self._get_heads(which_vec)
                elif which_value in [stored_values_unk.DIFFERENCE_HEAD_UP_DOWN, stored_values_unk.DIFFERENCE_Z_UP_DOWN]:
                    raise Warning(_('Please use get_diff instead of get_values for differences'))
                else:
                    values = fillin(0, which_value.value[0], loc_parts_values, self.linked)
                return values
            elif which_value in stored_values_pos:
                values = fillin(1, which_value.value[0], loc_parts_values, self.linked)
                return values
            elif which_value in stored_values_coords:
                values = fillin(-1, which_value.value[0], loc_parts_values, self.linked)
                return values
            else:
                return None

    def get_values_op(self,
                      which_vec:str,
                      which_value:Union[stored_values_unk, stored_values_pos, stored_values_coords],
                      which_group=None,
                      operator:operators=operators.MEDIAN) -> dict:

        loc_parts_values = None

        if which_group is not None:
            for cur_parts in self.parts.values():
                if which_vec in cur_parts[which_group].keys():
                    loc_parts_values = cur_parts
                    break

        if loc_parts_values is None:
            return {}

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

        vals = self.get_values(which_vec, which_value, which_group)

        if isinstance(self.linked, dict):
            if which_group in loc_parts_values.keys():
                vals_ret = extract_info(vals)
            else:
                vals_ret={}
                for curkey, curvals in vals.items():
                    vals_ret[curkey] = extract_info(curvals)
        else:
            vals_ret = extract_info(vals)

        return vals_ret

class Polygons_Analyze(Zones):
    """
    Classe permettant de récupérer les valeurs à l'intérieur des polygones
    définis dans la dernière zone d'une fichier .vecz.

    Ce fichier est typiquement le résultat de la création de polygones
    sur base de parallèles via l'interface graphique.

    Utile notamment dans l'analyse de modélisations 2D (CPU et/ou GPU).

    """

    def __init__(self, myfile='', ds:float=5.,
                 ox: float = 0, oy: float = 0,
                 tx: float = 0, ty: float = 0,
                 parent=None, is2D=True, wx_exists:bool = False):

        super().__init__(myfile, ox, oy, tx, ty, parent, is2D, wx_exists)

        self.myname = splitext(basename(myfile))[0]

        self.linked:Union[dict,list] = None # type is depending on the type of linked arrays
        self.river_values:dict = None

        # The riverbed axis is the second vector of the first zone
        self.riverbed = self.get_zone(0).myvectors[1]
        self.riverbed.prepare_shapely()

        self.polygons_zone:zone
        self.polygons_zone = self.get_zone(-1)

        # The curvilinear distance of the polygons is stored in the 'z' attribute of the vertices
        self.polygons_curvi = {}
        for curvert in self.polygons_zone.myvectors:
            self.polygons_curvi[curvert.myname] = curvert.myvertices[0].z

        # The mean center of the polygons
        self.polygons_meanxy = {}
        for curvert in self.polygons_zone.myvectors:
            # Centre du polygone
            centroid = curvert.centroid
            self.polygons_meanxy[curvert.myname] = (centroid.x, centroid.y)

        for vec in self.polygons_zone.myvectors:
            vec.myprop.used=False # cache les polygones pour ne pas surcharger l'affichage éventuel

    def cache_data(self, outputfile:str):
        """
        Serialize the values in a json file -- zipped
        """

        self._serialize_values(outputfile)

    def load_data(self, inputfile:str):
        """
        Deserialize the values from a json file -- zipped
        """

        self._deserialize_values(inputfile)

    def _serialize_values(self, outputfile:str):
        """
        Serialize the values in a file
        """

        import json
        from codecs import getwriter
        from typing import IO

        class NumpyArrayEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, tuple):
                    return [list(lst1) for lst1 in obj]
                elif obj == Wolfresults_2D:
                    return 'CPU'
                elif obj == wolfres2DGPU:
                    return 'GPU'

                return json.JSONEncoder.default(self, obj)

        def _json_dump_bytes(fp: IO, obj):
            StreamWriter = getwriter("utf-8")
            return json.dump(fp=StreamWriter(fp), obj=obj, cls=NumpyArrayEncoder, indent=4)

        def json_dump_zip(fp: IO, obj):
            with ZipFileWrapper(fp, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as zip_file:
                with zip_file.open(mode="w") as _fp:
                    _json_dump_bytes(fp=_fp, obj=obj)


        with open(outputfile, 'wb') as f:

            json_dump_zip(fp = f, obj = {'linked' : self.linked, 'values': self.river_values})


    def _deserialize_values(self, inputfile:str):
        """
        Deserialize the values from a file
        """

        import json
        from codecs import getwriter
        from typing import IO

        def json_load_zip(fp: IO):
            with ZipFileWrapper(fp, mode="r") as zip_file:
                return json.load(zip_file)

        inputfile = Path(inputfile)
        if not inputfile.exists():
            logging.error(_('File {0} does not exist').format(inputfile))
            return

        with open(inputfile, 'rb') as f:
            data = json_load_zip(f) #json.load(f)

        tmp_linked = data['linked']
        if isinstance(tmp_linked, dict):
            self.linked = {}
            for curkey, curgroup in tmp_linked.items():
                self.linked[curkey] = [(curlink[0], Wolfresults_2D if curlink[1] == 'CPU' else wolfres2DGPU) for curlink in curgroup]

            tmp_values = data['values']
            self.river_values = {}
            for curproj, curdict in tmp_values.items():
                self.river_values[curproj] = {}
                for curpoly, curval in curdict.items():
                    self.river_values[curproj][curpoly] = {}
                    for curgroup, curarray in curval.items():
                        locdict = self.river_values[curproj][curpoly][curgroup] = {}

                        for cursim, curnparray in curarray.items():
                            vals = curnparray[0]
                            xy   = curnparray[1]
                            locdict[cursim] = (np.array([np.array([ tuple(lst1), np.array(lst2, dtype= np.int32)], dtype=object ) for lst1, lst2 in vals], dtype=object), np.array(xy))

        elif isinstance(tmp_linked, list):
            self.linked = [(curlink[0], Wolfresults_2D if curlink[1] == 'CPU' else wolfres2DGPU) for curlink in tmp_linked]

            tmp_values = data['values']
            self.river_values = {}
            for curpoly, curval in tmp_values.items():
                self.river_values[curpoly] = {}
                for curgroup, curarray in curval.items():
                        locdict = self.river_values[curpoly][curgroup] = {}

                        for cursim, curnparray in curarray.items():
                            vals = curnparray[0]
                            xy   = curnparray[1]
                            locdict[cursim] = (np.array([np.array([ tuple(lst1), np.array(lst2, dtype= np.int32)], dtype=object ) for lst1, lst2 in vals], dtype=object), np.array(xy))


    def compute_distance(self, poly:LineString | vector):
        """
        Compute the curvilinear distance along a support polyline

        :param poly: vector or LineString Shapely object
        """

        if isinstance(poly, vector):
            poly = poly.asshapely_ls()

        for curvert in self.polygons_zone.myvectors:
            # Centre du polygone
            centroid = curvert.centroid
            self.polygons_curvi[curvert.myname] = poly.project(Point([centroid.x, centroid.y]))

    def find_values_inside_parts(self, linked_arrays:Union[dict,list]):
        """
        Récupère les valeurs à l'intérieur des polygones - dernière zone du fichier

        Stockage :
         - dictionnaire dont la clé est le nom (ou l'index) du polygone dans la zone
         - chaque entrée est un dictionnaire dont la clé 'values' contient un dictionnaire pour chaque matrice du projet
         - chaque élément de ce sous-dictionnaire est un tuple contenant toutes les valeurs utiles

        ***
        ATTENTION : si linked_arrays est un dictionnaire, alors un niveau supérieur est ajouté sur base des clés de ce dictionnaire, dans ce cas, self.linked est un dict et non une liste
        ***

        """

        if isinstance(linked_arrays, dict):

            self.linked={}

            for curkey, curgroup in linked_arrays.items():
                self.linked[curkey] = [(curlink.idx, type(curlink)) for curlink in curgroup]

        elif isinstance(linked_arrays, list):

            self.linked = [(curlink.idx, type(curlink)) for curlink in linked_arrays]

        # récupération des valeurs danbs les polygones "rivière"
        curzone = self.polygons_zone
        if curzone is not None:
            if isinstance(linked_arrays, dict):
                self.river_values={}
                for curkey, curgroup in linked_arrays.items():
                    self.river_values[curkey] = curzone.get_all_values_linked_polygon(curgroup, key_idx_names='name', getxy=True)

            elif isinstance(linked_arrays, list):

                self.river_values = curzone.get_all_values_linked_polygon(linked_arrays, key_idx_names='name', getxy=True)

    def _get_river_heads(self, which_group= None):
        """Compute Head

        :param which_group: group to get
        """

        head = {}

        z   = self.get_river_values(stored_values_unk.WATERLEVEL, which_group)
        unorm   = self.get_river_values(stored_values_unk.UNORM, which_group)

        for curkey, cur_z, curunorm  in zip(z.keys(), z.values(), unorm.values()):
            curdict = head[curkey] = {}

            for curgroup, zpoly, unormpoly in zip(cur_z.keys(), cur_z.values(), curunorm.values()):
                curdict[curgroup] = zpoly + np.power(unormpoly,2)/(2*9.81)

        return head

    def get_river_values(self,
                         which_value:Union[stored_values_unk,
                                           stored_values_pos,
                                           stored_values_coords],
                         which_group=None) -> dict:
        """
        Get values for the river polygons

        La donnée retournée est un dictionnaire
        --> dépend du typage de "self.linked" (cf "find_values_inside_parts)" pour plus d'infos)

        Soit il n'y a qu'un projet à traiter
        --> le dictionnaire contient une entrée pour chaque polygone et
            les différentes valeurs pour chaque matrice/simulation du projet dans chaque polygone

        Soit il y a plusiuers projets à traiter
        --> le dictionnaire contient autant d'entrées que de projet et
            chaque sous-dictionnaire reprend les différentes valeurs comme ci-dessus

        :param which_value: value to get
        :param which_group: group to get
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
                    # if len(curarray)>0:
                    #     create=True
                    if isinstance(curarray, tuple):
                        # on a également repris les coordonnées
                        if len(curarray[0])>0:
                            create=True
                    else:
                        if len(curarray)>0:
                            create=True

                if create:
                    for idarray, curarray in enumerate(curarrays.values()):
                        # if len(curarray)>0:
                        #     vallist = [curval[pos1][pos2] for curval in curarray]
                        #     curdict[part_names[idarray][0]] = vallist

                        if isinstance(curarray, tuple):
                            if pos1==-1:
                                if len(curarray[1])>0:
                                    vallist = [curval[pos2] for curval in curarray[1]]
                                    curdict[part_names[idarray][0]] = vallist
                            else:
                                if len(curarray[0])>0:
                                    vallist = [curval[pos1][pos2] for curval in curarray[0]]
                                    curdict[part_names[idarray][0]] = vallist
                        else:
                            if len(curarray)>0:
                                vallist = [curval[pos1][pos2] for curval in curarray]
                                curdict[part_names[idarray][0]] = vallist
            return locvalues

        if isinstance(self.linked, dict):
            if which_group in self.river_values.keys():
                if which_value in stored_values_unk:
                    if which_value is stored_values_unk.HEAD:
                        values = self._get_river_heads(which_group=which_group)
                    else:
                        values = fillin(0, which_value.value[0], self.river_values[which_group], self.linked[which_group])
                    return values
                elif which_value in stored_values_pos:
                    values = fillin(1, which_value.value[0], self.river_values[which_group], self.linked[which_group])
                    return values
                elif which_value in stored_values_coords:
                    values = fillin(-1, which_value.value[0], self.river_values[which_group], self.linked[which_group])
                    return values
                else:
                    return None
            else:
                values={}
                for (curkey, curgroup), curnames in zip(self.river_values.items(), self.linked.values()):
                    if which_value in stored_values_unk:
                        if which_value is stored_values_unk.HEAD:
                            values[curkey] = self._get_river_heads(which_group=curkey)
                        else:
                            values[curkey] = fillin(0, which_value.value[0], curgroup, curnames)
                    elif which_value in stored_values_pos:
                        values[curkey] = fillin(1, which_value.value[0], curgroup, curnames)
                    elif which_value in stored_values_coords:
                        values[curkey] = fillin(-1, which_value.value[0], curgroup, curnames)
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
            elif which_value in stored_values_coords:
                values = fillin(-1, which_value.value[0], self.river_values, self.linked)
            else:
                return None

    def get_river_values_op(self,
                            which_value:Union[stored_values_unk,
                                              stored_values_pos,
                                              stored_values_coords],
                            which_group=None,
                            operator:operators=operators.MEDIAN) -> dict:
        """
        Get values for the river polygons with an operator

        :param which_value: value to get
        :param which_group: group to get
        :param operator: MEDIAN, MIN, MAX, PERCENTILE95, PERCENTILE5, ALL
        """

        def extract_info(vals):
            vals_ret={}
            for curkeypoly, curpoly in vals.items():
                curdict = vals_ret[curkeypoly]={}
                for curkey, curvals in curpoly.items():
                    if curvals is not None:
                        try:
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
                        except:
                            logging.error(_('Error in extract_info for key {0}').format(curkey))
                            curdict[curkey] = -1.

            return vals_ret

        vals = self.get_river_values(which_value, which_group)

        if isinstance(self.linked, dict) and which_group is None:
            vals_ret={}
            for curkey, curvals in vals.items():
                vals_ret[curkey] = extract_info(curvals)
        else:
            vals_ret = extract_info(vals)

        return vals_ret

    def list_groups(self):
        """ List the groups of the river polygons """

        return list(self.river_values.keys())

    def list_sims(self, which_group=None):
        """ List the sims for a specific group
        or for all the groups of the river polygons """

        if which_group is not None:
            if which_group in self.river_values.keys():
                return list(self.river_values[which_group].keys())
            else:
                logging.error(_('Group {0} not found').format(which_group))
                return []
        else:
            ret = {}
            for curgroup, curdict in self.river_values.items():
                first_poly = curdict[list(curdict.keys())[0]]
                values_dict = first_poly['values']
                ret[curgroup] = list(values_dict.keys())
            return ret

    def get_s_values(self,
                     which_value:Union[stored_values_unk,
                                       stored_values_pos,
                                       stored_values_coords]=stored_values_unk.WATERLEVEL,
                     which_group:str=None,
                     which_sim:str=None,
                     operator:operators=operators.MEDIAN):

        """ Get the values of the river polygons for a specific simulation

        :param which_value: value to get
        :param which_group: group to get
        :param which_sim: simulation to get
        :param operator: operator to use
        """

        s=[]
        val=[]

        myval = self.get_river_values_op(which_value, which_group, operator)

        for curkey, curval in myval.items():
            if len(curval)>0 and which_sim in curval.keys():
                val.append(curval[which_sim])
                s.append(self.polygons_curvi[curkey])

        if len(s) != len(val):
            logging.error(_('Error in get_s_values'))
            return [], []

        # Tri des valeurs selon l'absisse curviligne
        ret = sorted(zip(s, val))

        # Séparation des listes triées
        s, val = zip(*ret)

        return s, val

    def get_s_xy(self):
        """ Get the centroids of the river polygons """

        s = []
        x = []
        y = []

        for curval in self.polygons_curvi.values():
            s.append(curval)

        for curval in self.polygons_meanxy.values():
            x.append(curval[0])
            y.append(curval[1])

        if len(s) != len(x) or len(s) != len(y):
            logging.error(_('Error in get_s_centroidsxy'))
            return [], [], []

        # Tri des valeurs selon l'absisse curviligne
        ret = sorted(zip(s, x, y))

        # Séparation des listes triées
        s, x, y = zip(*ret)

        return s, x, y

    def get_s_xy4sim(self, which_group:str, which_sim:str, operator:operators=operators.MEDIAN):
        """ Get the position for a specific simulation """

        s1, x = self.get_s_values(which_value= stored_values_coords.X, which_group= which_group, which_sim= which_sim, operator= operator)
        s2, y = self.get_s_values(which_value= stored_values_coords.Y, which_group= which_group, which_sim= which_sim, operator= operator)

        assert s1 == s2, _('Error in get_s_xy4sim')

        return s1, x, y

    def save_xy_s_tofile(self, outputfile:str):
        """ Save the centroids of the river polygons to a file """

        s, x, y = self.get_s_xy()

        with open(outputfile, 'w') as f:
            f.write('x,y,s\n')
            for curs, curx, cury in zip(s, x, y):
                f.write('{0},{1},{2}\n'.format(curx, cury, curs))

    def save_xy_s_tofile_4sim(self, outputfile:str, which_group:str, which_sim:str):
        """ Save the centroids of the river polygons to a file """

        s, x, y = self.get_s_xy4sim(which_group= which_group, which_sim= which_sim)

        with open(outputfile, 'w') as f:
            f.write('x,y,s\n')
            for curs, curx, cury in zip(s, x, y):
                f.write('{0},{1},{2}\n'.format(curx, cury, curs))

    def export_as(self, outputfile:Path, unks:list[stored_values_unk | stored_values_coords], which_group:str, which_sim:str, operator:operators=operators.MEDIAN):
        """ Export the values of the river polygons to a file

        :param outputfile: output file (supported formats: csv, xlsx)
        :param unks: list of values to export
        :param which_group: group to export
        :param which_sim: simulation to export
        :param operator: operator to use for values (coordinates will be exported as MEDIAN)
        """

        outputfile = Path(outputfile)
        if not (outputfile.suffix == '.csv' or outputfile.suffix == '.xlsx'):
            logging.error(_('Unsupported format for export -- Must be csv or xlsx'))
            return

        import pandas as pd

        s,x,y = self.get_s_xy4sim(which_group, which_sim, operators.MEDIAN)

        vals = {curunk.value[1]:self.get_s_values(which_value= curunk,
                                                  which_group = which_group,
                                                  which_sim= which_sim,
                                                  operator= operator)[1] for curunk in unks}

        cols_names = ['s [m]', 'x centroid [m]', 'y centroid [m]']
        vals[cols_names[0]] = s
        vals[cols_names[1]] = x
        vals[cols_names[2]] = y

        df = pd.DataFrame(vals, columns = [cur for cur in cols_names] + [curunk.value[1] for curunk in unks])

        if outputfile.suffix == '.csv':
            df.to_csv(outputfile, index=False)
        elif outputfile.suffix == '.xlsx':
            df.to_excel(outputfile, index=False)

    def plot_unk(self,
                 figax = None,
                 which_value:Union[stored_values_unk,stored_values_pos]=stored_values_unk.WATERLEVEL,
                 which_group=None,
                 operator:operators=operators.MEDIAN,
                 options:dict=None,
                 label=True,
                 show=False,
                 which_sim:str=None):
        """ Plot the values of the river polygons

        :param figax: tuple (fig, ax) for the plot
        :param which_value: value to plot
        :param which_group: group to plot
        :param operator: operator to use
        :param options: options for the plot
        :param label: show the labels or not
        :param show: show the plot or not
        :param which_sim: simulation to plot (if None, all simulations are plotted)
        :return: tuple (fig, ax) of the plot
        """

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

                ax.plot(s, val, linewidth = curlw, linestyle=curls, marker=curmark, color=curcol, label=labelstr)
        else:

            for keyproj, curproj in self.river_values.items():
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

                    for curkey, curval in myval[keyproj].items():
                        if len(curval)>0 and curmodkey in curval.keys():
                                val.append(curval[curmodkey])
                                s.append(self.polygons_curvi[curkey])

                    ax.plot(s, val, linewidth = curlw, linestyle=curls, marker=curmark, color=curcol, label=labelstr)
        if show:
            fig.show()

        return fig,ax

    def plot_waterline(self,
                       figax=None,
                       which_group=None,
                       operator:operators=operators.MEDIAN,
                       show=False):
        """ Plot the waterline

        :param figax: tuple (fig, ax) for the plot
        :param which_group: group to plot
        :param operator: operator to use
        :param show: show the plot or not
        """

        fig,ax = self.plot_unk(figax, stored_values_unk.TOPOGRAPHY, which_group, operator, options={'color':'black', 'linewidth':2}, label=False, show=False)
        figax=(fig,ax)
        self.plot_unk(figax, stored_values_unk.WATERLEVEL, which_group, operator, options={'color':'blue', 'linewidth':2}, label=True, show=False)

        ax.set_ylabel(_('Water surface elevation [mDNG]'))
        ax.set_xlabel(_('Abscissa from upstream [m]'))
        fig.suptitle(self.myname + ' -- ' +_('Water surface elevation'))

        if show:
            fig.show()

        return fig,ax

    def plot_bedelevation(self,
                       figax=None,
                       which_group=None,
                       operator:operators=operators.MEDIAN,
                       show=False):
        """ Plot the bed elevation

        :param figax: tuple (fig, ax) for the plot
        :param which_group: group to plot
        :param operator: operator to use
        :param show: show the plot or not
        """

        fig,ax = self.plot_unk(figax, stored_values_unk.TOPOGRAPHY, which_group, operator, options={'color':'black', 'linewidth':2}, label=False, show=False)

        ax.set_ylabel(_('Bed elevation [mDNG]'))
        ax.set_xlabel(_('Abscissa from upstream [m]'))

        if show:
            fig.show()

        return fig,ax

    def plot_stage(self,
                   figax=None,
                   which_group=None,
                   operator:operators=operators.MEDIAN,
                   show=False):
        """ Plot the water stage /water level

        :param figax: tuple (fig, ax) for the plot
        :param which_group: group to plot
        :param operator: operator to use
        :param show: show the plot or not
        """

        fig,ax = self.plot_unk(figax, stored_values_unk.WATERLEVEL, which_group, operator, options={'color':'blue', 'linewidth':2}, show=False)

        ax.set_ylabel(_('Water stage [mDNG]'))
        ax.set_xlabel(_('Abscissa from upstream [m]'))

        if show:
            fig.show()

        return fig,ax

    def plot_waterhead(self,
                       figax=None,
                       which_group=None,
                       operator:operators=operators.MEDIAN,
                       show=False):
        """ Plot the water head

        :param figax: tuple (fig, ax) for the plot
        :param which_group: group to plot
        :param operator: operator to use
        :param show: show the plot or not
        """

        fig,ax = self.plot_unk(figax, stored_values_unk.HEAD, which_group, operator, options={'color':'blue', 'linewidth':2}, show=False)

        ax.set_ylabel(_('Water head [m_water]'))
        ax.set_xlabel(_('Abscissa from upstream [m]'))
        fig.suptitle(self.myname + ' -- ' +_('Water head profile'))

        if show:
            fig.show()

        return fig,ax
