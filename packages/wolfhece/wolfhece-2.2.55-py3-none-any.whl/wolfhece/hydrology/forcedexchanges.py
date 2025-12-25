
"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os import path
from pathlib import Path

#from ..color_constants import *
from ..PyVertexvectors import *
from ..PyVertex import cloud_vertices,wolfvertex
from ..PyTranslate import _

class forced_exchanges:
    """ Forced exchanges For Hydrological model.

    A forced exchange is a pair of vertices that are coupled together.
    The first vertex is the upper one, the second is the lower one.
    """

    def __init__(self, workingdir='', fname='', mapviewer=None) -> None:

        self.mapviewer = mapviewer
        self._workingdir = Path(workingdir)

        self._color_up = (0, 238, 0)  # Green
        self._color_down = (255, 52, 179)  # Pink

        self.type='COORDINATES'
        self._mycloudup  = cloud_vertices(mapviewer=self.mapviewer)
        self._myclouddown= cloud_vertices(mapviewer=self.mapviewer)
        self._mysegs = Zones(mapviewer=self.mapviewer)

        tmp_zone = zone(name='temporary')
        self._mysegs.add_zone(tmp_zone, forceparent=True)
        tmpvec = vector(name='temporary')
        tmpvec.myprop.color = getIfromRGB((0, 0, 128))
        tmpvec.myprop.width = 2
        tmp_zone.add_vector(tmpvec, forceparent=True)

        self._myzone = zone(name='segments_fe')
        self._mysegs.add_zone(self._myzone, forceparent=True)

        self._mycloudup.myprop.color   = getIfromRGB((0,238,0))
        self._mycloudup.myprop.filled  = True
        self._myclouddown.myprop.color = getIfromRGB((255,52,179))
        self._myclouddown.myprop.filled= True

        if fname:
            if isinstance(fname, str):
                if fname == 'N-O':
                    fname = self._workingdir / 'Coupled_pairs.txt'
                else:
                    fname = self._workingdir / fname
                    if not fname.exists():
                        logging.error(f"The file {fname} does not exist.")

        self._filename = fname if fname else self._workingdir / 'Coupled_pairs.txt'

        try:
            self._read_file()
        except:
            logging.error(f"Could not read the file {self._filename}. It may not be in the correct format or may be corrupted.")

        self._myzone.find_minmax(True)

    def is_empty(self):
        """ Check if the forced exchanges are empty. """
        return self._mysegs['segments_fe'].nbvectors == 0

    @property
    def pairs(self):
        """ Get the list of pairs of vertices. """
        seg_zone = self._mysegs['segments_fe']
        if not seg_zone:
            raise ValueError("The segments zone is not initialized or does not exist.")

        return [[vec[0].x, vec[0].y, vec[-1].x, vec[-1].y] for vec in seg_zone.myvectors]

    @property
    def temporary_vector(self):
        """ Get the temporary vector used for forced exchanges. """
        return self._mysegs[('temporary', 'temporary')]

    @property
    def color_up_integer(self):
        """ Get the color of the upper vertices as an integer. """
        return getIfromRGB(self._color_up)

    @property
    def color_down_integer(self):
        """ Get the color of the lower vertices as an integer. """
        return getIfromRGB(self._color_down)

    @property
    def color_up_rgb(self):
        """ Get the color of the upper vertices as an RGB tuple. """
        return self._color_up

    @property
    def color_down_rgb(self):
        """ Get the color of the lower vertices as an RGB tuple. """
        return self._color_down

    @color_up_rgb.setter
    def color_up_rgb(self, value):
        """ Set the color of the upper vertices from an RGB tuple. """
        if isinstance(value, tuple) and len(value) == 3:
            self._color_up = value
            self._mycloudup.myprop.color = getIfromRGB(value)
        else:
            raise ValueError("color_up_rgb must be a tuple of three integers (R, G, B).")

    @color_down_rgb.setter
    def color_down_rgb(self, value):
        """ Set the color of the lower vertices from an RGB tuple. """
        if isinstance(value, tuple) and len(value) == 3:
            self._color_down = value
            self._myclouddown.myprop.color = getIfromRGB(value)
        else:
            raise ValueError("color_down_rgb must be a tuple of three integers (R, G, B).")

    @color_up_integer.setter
    def color_up_integer(self, value):
        """ Set the color of the upper vertices from an integer. """
        if isinstance(value, int):
            self._color_up = getRGBfromI(value)
            self._mycloudup.myprop.color = value
        else:
            raise ValueError("color_up_integer must be an integer representing a color.")

    @color_down_integer.setter
    def color_down_integer(self, value):
        """ Set the color of the lower vertices from an integer. """
        if isinstance(value, int):
            self._color_down = getRGBfromI(value)
            self._myclouddown.myprop.color = value
        else:
            raise ValueError("color_down_integer must be an integer representing a color.")

    def _read_file(self):
        """ Read the forced exchanges from a file. """

        if not self._filename.exists():
            logging.error(f"The file {self._filename} does not exist.")
            return

        with open(self._filename, 'rt') as f:
            content = f.read().splitlines()

        self.type = content[0]
        idx=1
        for curline in content[1:]:
            coords=curline.split('\t')
            coords = [float(x) for x in coords]

            vert1 = wolfvertex(coords[0],coords[1])
            vert2 = wolfvertex(coords[2],coords[3])

            myseg = vector(name='fe'+str(idx))
            myseg.myprop.width = 2
            myseg.myprop.color = getIfromRGB((0,0,128))
            myseg.add_vertex([vert1,vert2])
            self._myzone.add_vector(myseg, forceparent=True)

            self._mycloudup.add_vertex(vert1)
            self._myclouddown.add_vertex(vert2)
            idx+=1

    def _save_file(self):
        """ Save the forced exchanges to a file. """

        with open(self._filename, 'wt') as f:
            f.write(f"{self.type}\n")
            for pair in self.pairs:
                f.write(f"{pair[0]}\t{pair[1]}\t{pair[2]}\t{pair[3]}\n")

        logging.info(f"Forced exchanges saved to {self._filename}.")

    def save(self):
        """ Save the forced exchanges to the file. """
        if not self._filename:
            raise ValueError("Filename is not set. Cannot save forced exchanges.")

        self._save_file()

    def add_pair_dict(self, pair:dict):
        """ Add a pair of vertices to the forced exchanges from a dictionary.

        :param pair: A dictionary with 'up' and 'down' keys containing the vertices.
        :type pair: dict
        """

        if not isinstance(pair, dict):
            raise TypeError("pair must be a dictionary with 'up' and 'down' keys.")

        if 'up' not in pair or 'down' not in pair:
            raise KeyError("The dictionary must contain 'up' and 'down' keys.")

        self.add_pair(pair['up'], pair['down'])

    def add_pair_XY(self, x1, y1, x2, y2, reset_ogl:bool = False):
        """ Add a pair of coordinates to the forced exchanges. """

        if not isinstance(x1, (int, float)) or not isinstance(y1, (int, float)):
            raise TypeError("x1 and y1 must be numeric values.")
        if not isinstance(x2, (int, float)) or not isinstance(y2, (int, float)):
            raise TypeError("x2 and y2 must be numeric values.")

        vertex_up = wolfvertex(x1, y1)
        vertex_down = wolfvertex(x2, y2)

        vec = vector(name= self._find_first_available_name())
        vec.add_vertex([vertex_up, vertex_down])
        self._myzone.add_vector(vec, forceparent=True)

        self._mycloudup.add_vertex(vertex_up)
        self._myclouddown.add_vertex(vertex_down)

        if reset_ogl:
            self.reset_listogl()

    def add_pairs_XY(self, ups: list[list[float, float]], downs: list[float, float]):
        """ Add multiple upstreams to one downstream as forced exchanges.

        :param ups: A list of lists containing the coordinates of the upstream vertices.
        :type ups: list[list[float, float]]
        :param downs: A pair containing the coordinates of the downstream vertex.
        """
        if not isinstance(ups, list) or not all(isinstance(coord, list) and len(coord) == 2 for coord in ups):
            raise TypeError("ups must be a list of lists with two numeric values each.")
        if not isinstance(downs, list) or len(downs) != 2:
            raise TypeError("downs must be a list with two numeric values.")

        x_down, y_down = downs
        for up in ups:
            x_up, y_up = up
            self.add_pair_XY(x_up, y_up, x_down, y_down)

        self.reset_listogl()

    def add_pair(self, vertex_up, vertex_down):
        """ Add a pair of vertices to the forced exchanges. """

        if not isinstance(vertex_up, wolfvertex) or not isinstance(vertex_down, wolfvertex):
            raise TypeError("Both vertices must be of type wolfvertex.")

        vec = vector(name= self._find_first_available_name())
        vec.add_vertex([vertex_up, vertex_down])
        self._myzone.add_vector(vec, forceparent=True)

        self._mycloudup.add_vertex(vertex_up)
        self._myclouddown.add_vertex(vertex_down)

        self.reset_listogl()

    def reset_listogl(self):
        """ Reset the OpenGL lists for the forced exchanges. """

        if not self._myclouddown or not self._mycloudup:
            raise ValueError("Clouds for down and up vertices are not initialized.")

        self._myclouddown.reset_listogl()
        self._mycloudup.reset_listogl()

        if not self._mysegs:
            raise ValueError("Segments zone is not initialized.")

        self._mysegs.reset_listogl()

    def _find_nearest_pair(self, x, y):
        """ Find the nearest pair of vertices to the given coordinates. """

        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError("x and y must be numeric values.")

        if not self.pairs:
            return None

        min_dist = float('inf')
        nearest_pair = None

        for pair in self.pairs:
            dist = ((pair[0] - x) ** 2 + (pair[1] - y) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest_pair = pair

        return nearest_pair

    def get_nearest_pair(self, x:float, y:float) -> dict:
        """ Get the nearest pair of vertices to the given coordinates.

        :return: A dictionary with 'up' and 'down' keys containing the nearest vertices.
        :rtype: dict
        """

        nearest_pair = self._find_nearest_pair(x, y)

        if nearest_pair is None:
            return None

        return {
            'up': wolfvertex(nearest_pair[0], nearest_pair[1]),
            'down': wolfvertex(nearest_pair[2], nearest_pair[3])
        }

    def get_nearest_pair_as_vector(self, x:float, y:float) -> vector:
        """ Get the nearest pair of vertices as a vector. """

        nearest_index = self._find_nearest_pair_index(x, y)
        vec = self._myzone[f'fe{nearest_index}'] if nearest_index != -1 else None

        return vec

    def _find_nearest_pair_index(self, x, y):
        """ Find the index of the nearest pair of vertices to the given coordinates. """

        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError("x and y must be numeric values.")

        if not self.pairs:
            return -1

        min_dist = float('inf')
        nearest_index = -1

        for idx, pair in enumerate(self.pairs):
            dist = ((pair[0] - x) ** 2 + (pair[1] - y) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest_index = idx

        return nearest_index

    def remove_nearest_pair(self, x, y):
        """ Remove the nearest pair of vertices to the given coordinates. """

        nearest_index = self._find_nearest_pair_index(x, y)

        if nearest_index != -1:
            self._myclouddown.remove_vertex(nearest_index)
            self._mycloudup.remove_vertex(nearest_index)
            self._myzone.myvectors.pop(nearest_index)

        self.reset_listogl()

    def remove_nearest_pairs(self, xy:list[list[float, float]]):
        """ Remove the nearest pairs of vertices to the given coordinates. """

        if not isinstance(xy, list) or not all(isinstance(coord, list) and len(coord) == 2 for coord in xy):
            raise TypeError("xy must be a list of lists with two numeric values each.")

        idx_to_remove = list(set([self._find_nearest_pair_index(coords[0], coords[1]) for coords in xy]))

        for i in reversed(idx_to_remove):
            if i != -1:
                self._myclouddown.remove_vertex(i)
                self._mycloudup.remove_vertex(i)
                self._myzone.myvectors.pop(i)

        self.reset_listogl()

    def remove_pairs_inside_vector(self, vec:vector):
        """ Remove pairs of vertices that are inside the given vector.

        :param vec: The vector to check against.
        :type vec: vector
        """

        if not isinstance(vec, vector):
            raise TypeError("vec must be an instance of vector.")

        idx_to_remove = []
        for idx, pair in enumerate(self.pairs):
            if vec.isinside(pair[0], pair[1]) or vec.isinside(pair[2], pair[3]):
                idx_to_remove.append(idx)

        idx_to_remove = list(set(idx_to_remove))

        for idx in reversed(idx_to_remove):
            self._myclouddown.remove_vertex(idx)
            self._mycloudup.remove_vertex(idx)
            self._myzone.myvectors.pop(idx)

        self.reset_listogl()

    def _find_first_available_name(self):
        """ Find the first available name for a new forced exchange. """

        idx = 1
        names = [v.myname for v in self._myzone.myvectors]
        while True:
            name = f'fe{idx}'
            if name not in self._myzone.myvectors:
                return name
            idx += 1

    def paint(self):
        self._mycloudup.plot()
        self._myclouddown.plot()
        self._mysegs.plot()

    def reset(self):
        """ Reset the forced exchanges. """
        self.reset_listogl()

        self._mycloudup = cloud_vertices(mapviewer=self.mapviewer)
        self._myclouddown = cloud_vertices(mapviewer=self.mapviewer)
        self._mysegs = Zones(mapviewer=self.mapviewer)

        tmp_zone = zone(name='temporary')
        self._mysegs.add_zone(tmp_zone, forceparent=True)
        tmpvec = vector(name='temporary')
        tmpvec.myprop.color = getIfromRGB((0, 0, 128))
        tmpvec.myprop.width = 2
        tmp_zone.add_vector(tmpvec, forceparent=True)

        self._myzone = zone(name='segments_fe')
        self._mysegs.add_zone(self._myzone, forceparent=True)

        self._mycloudup.myprop.color = getIfromRGB((0, 238, 0))
        self._mycloudup.myprop.filled = True
        self._myclouddown.myprop.color = getIfromRGB((255, 52, 179))
        self._myclouddown.myprop.filled = True

