"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from shapely.geometry import Polygon, Point, MultiPolygon, LineString
from shapely.wkt import dumps, loads
from typing import Literal, Union
import logging
import json
from pathlib import Path

class Clock_Emitter():

    def __init__(self, times:Union[list[float], np.ndarray]=None):
        """
        Time manager for the emitter.

        :param times: list of time intervals during which the emitter is active -- [[t_start1, t_end1], [t_start2, t_end2], ...]
        """
        if isinstance(times, np.ndarray):
            assert times.ndim == 2, "times must be a 2D array - first line contains t_start, second line contains t_end"
            assert times.dtype == np.float64, "times must be a 2D array of float64 - first line contains t_start, second line contains t_end"
            times = times.tolist()

        self.times = times

    def is_active(self, t:float) -> bool:
        """
        Check if the emitter is active at time t.
        """
        for t_start, t_end in self.times:
            if t_start <= t < t_end:
                return True
        return False

    def serialize(self) -> dict:
        """
        Serialize the object.
        """
        return {'times':self.times}

    def deserialize(self, data:dict) -> "Clock_Emitter":
        """
        Deserialize the object.
        """
        self.times = data['times']
        return self

    def to_str(self) -> list[str]:
        """ Return a list of string representing the time intervals. """
        return ['[{}'.format(t_start) + '->{}'.format(t_end) + '[' for t_start, t_end in self.times]

    def from_str(self, times:list[str]) -> None:
        """ Set the time intervals from a list of string. """
        self.times = [[float(cur.split('->')[0][1:]), float(cur.split('->')[1][:-1])] for cur in times]
class Emitter():

    def __init__(self,
                 area:Union[Polygon, LineString, np.ndarray, list[int], tuple[int]] = None,
                 how_many:int=0,
                 every_seconds:float=0.,
                 clock:Clock_Emitter=None,
                 header:tuple[float] = (0., 0., 1., 1.)) -> None:

        assert type(area) in [Polygon, MultiPolygon, LineString, np.ndarray, list, tuple, type(None)], "area must be a Polygon, MultiPolygon, LineString, a 2D array or a list/tuple of length 2"

        # header -> useful only if indices are used
        self.origx, self.origy, self.dx, self.dy, *rest = header

        if isinstance(area, np.ndarray):
            # check if area is a 2D array --> first line contains x indices, second line contains y indices
            assert area.ndim == 2, "area must be a 2D array - first line contains x indices, second line contains y indices"
        elif type(area) in [list,tuple]:
            # check if area is a list or tuple of length 2 --> first line contains x indices, second line contains y indices
            assert len(area) == 2 or len(area[0])==2, "area must be a list or tuple of length 2 - [i1, i2... in], [j1, j2... jn]"
            # convert to numpy array
            if len(area)==2:
                area = np.array(area)
            else:
                area = np.array([[cur[0] for cur in area], [cur[1] for cur in area]])

        if isinstance(area, np.ndarray):
            # we are here if area is a 2D array --> first line contains x indices, second line contains y indices
            self._indices = area

            ox, oy, dx, dy = self.origx, self.origy, self.dx, self.dy

            # create a Multipolygon from indices --> used to check if a point is inside the area
            area = MultiPolygon([Polygon([(i*dx+ox, j*dy+oy), ((i+1)*dx+ox, j*dy+oy), ((i+1)*dx+ox, (j+1)*dy+oy), (i*dx+ox, (j+1)*dy+oy)]) for i,j in zip(area[0], area[1])])

        else:
            # Set default value for indices
            self._indices = np.array([[],[]])

        self.area = area                    # Polygon containing particles | converted arrays of indices (e.g. as returned by np.where)

        self.how_many = how_many            # Numer of particles

        # Clock_Emitter object
        if clock is None:
            self.clock = Clock_Emitter([[0., np.inf]])
        else:
            self.clock = clock

        self.every_seconds = every_seconds  # Emit nb particles every seconds

        self._last_emit = 0.                # Time [s] of last emission

        self.active = True                  # If False, no more particles are emitted

        self.color_area = (0., 0., 0., 1.)  # Color of the area
        self.color_particles = (0., 0., 0., 1.) # Color of the particles

    def reset(self) -> None:
        """
        Reset the emitter.
        """
        self._last_emit = 0.

    def check(self) -> tuple[bool, str]:
        """
        Check if the emitter is valid.
        """
        check = True
        msg = ''

        if self.area is None:
            check = False
            msg += 'area is None\n'

        if self.how_many <= 0:
            check = False
            msg += 'how_many <= 0\n'

        if self.every_seconds <= 0.:
            check = False
            msg += 'every_seconds <= 0.\n'

        if self.dx <= 0.:
            check = False
            msg += 'dx <= 0.\n'

        if self.dy <= 0.:
            check = False
            msg += 'dy <= 0.\n'

        if not type(self.area) in [Polygon, MultiPolygon, LineString]:
            check = False
            msg += 'area must be a Polygon, MultiPolygon or a LineString\n'

        return check, msg

    def set_clock(self, times:Union[list[float], np.ndarray]) -> None:
        """
        Set the clock of the emitter.
        """
        self.clock = Clock_Emitter(times)

    @property
    def bounds(self) -> tuple[float]:
        """
        Return the bounds of the emitter.
        """
        if type(self.area) in [Polygon, MultiPolygon]:
            return self.area.bounds
        elif isinstance(self.area, np.ndarray):
            return (self.area[0].min() * self.dx + self.origx,
                    self.area[1].min() * self.dy + self.origy,
                    self.area[0].max() * self.dx + self.origx + self.dx,
                    self.area[1].max() * self.dy + self.origy + self.dy)
        else:
            logging.error('Emitter: bounds not implemented for the type {}'.format(type(self.area)))

    def serialize(self) -> dict:
        """
        Serialize the object.
        """
        return {'active':self.active,
                'area': self.area.wkt,
                'how_many':self.how_many,
                'every_seconds':self.every_seconds,
                'color_area':self.color_area,
                'color_particles':self.color_particles,
                'clock':self.clock.serialize(), # Clock_Emitter object
                'header':(self.origx, self.origy, self.dx, self.dy),
                'indices_i':[int(cur) for cur in self._indices[0]], # if not force to int, list will be converted to int64 which is not json serializable
                'indices_j':[int(cur) for cur in self._indices[0]],
                }

    def deserialize(self, data:dict) -> None:
        """
        Deserialize the object.
        """
        self.active = data['active']
        self.area = loads(data['area'])
        self.how_many = data['how_many']
        self.every_seconds = data['every_seconds']
        try:
            self.color_area = data['color_area']
        except:
            self.color_area = (0., 0., 0., 1.)
        try:
            self.color_particles = data['color_particles']
        except:
            self.color_particles = (0., 0., 0., 1.)
        self.origx, self.origy, self.dx, self.dy = data['header']
        self._indices = [np.array(data['indices_i']), np.array(data['indices_j'])]
        self.origx, self.origy, self.dx, self.dy = data['header']

        try:
            self.clock = Clock_Emitter().deserialize(data['clock']) # Clock_Emitter object
        except:
            self.clock = Clock_Emitter([[0., np.inf]])

    def save(self, f:str) -> str:
        """
        Save the emitter to file.
        """
        f = Path(f).with_suffix('.json')
        with open(f, 'w') as fp:
            json.dump(self.serialize(), fp, indent=2)

        return f.name

    def load(self, f:str) -> "Emitter":
        """
        Load the emitter from file.
        """
        f = Path(f).with_suffix('.json')
        with open(f, 'r') as fp:
            self.deserialize(json.load(fp))

        return self

    def _emit(self) -> tuple[np.ndarray]:
        """
        Emit particles.
        """

        if not self.active:
            return np.array([]), np.array([])

        unsatisfied = True
        factor = int(2)


        if isinstance(self.area, MultiPolygon):
            # As the area is a MultiPolygon, we need to emit particles in each polygon
            # To be more realistic and more rapid, we use a multinomial distribution to emit particles in each polygon
            # The number of particles to emit in each polygon is proportional to the area of the polygon

            nbpoly = self.area.geoms.__len__()
            area_tot = np.sum([cur.area for cur in self.area.geoms])
            how_many_per_poly = np.random.multinomial(self.how_many, [cur.area/area_tot for cur in self.area.geoms])

            x_all = np.array([])
            y_all = np.array([])

            for idx, curpoly in enumerate(self.area.geoms):
                unsatisfied = True
                while unsatisfied:
                    x1, y1, x2, y2 = curpoly.bounds
                    x = np.random.uniform(x1, x2, how_many_per_poly[idx])
                    y = np.random.uniform(y1, y2, how_many_per_poly[idx])

                    inside = np.asarray([curpoly.contains(Point(xi, yi)) for xi, yi in zip(x, y)])
                    useful = np.where(inside)[0][:how_many_per_poly[idx]]

                    if len(useful) == how_many_per_poly[idx]:
                        unsatisfied = False
                    else:
                        factor += 1

                x_all = np.concatenate((x_all, x[useful]))
                y_all = np.concatenate((y_all, y[useful]))

            return np.require(x_all, requirements='F'), np.require(y_all, requirements='F')
        else:
            while unsatisfied:
                x1, y1, x2, y2 = self.bounds

                x = np.random.uniform(x1, x2, factor*self.how_many)
                y = np.random.uniform(y1, y2, factor*self.how_many)

                inside = np.asarray([self.area.contains(Point(xi, yi)) for xi, yi in zip(x, y)])
                useful = np.where(inside)[0][:self.how_many]

                if len(useful) == self.how_many:
                    unsatisfied = False
                else:
                    factor += 1

            return np.require(x[useful], requirements='F'), np.require(y[useful], requirements='F')

    def emit(self, t:float) -> tuple[np.ndarray]:
        """
        Emit particles at the given time.
        """

        if self.clock.is_active(t):
            if t - self._last_emit >= self.every_seconds or t == 0.:
                self._last_emit = t
                return self._emit()
            else:
                return np.array([]), np.array([])