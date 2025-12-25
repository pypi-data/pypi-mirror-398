"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from typing import Literal, Union
from OpenGL.GL  import *
import matplotlib.pyplot as plt
from matplotlib import collections  as mc
import logging
from pathlib import Path

from .advection import advection_xy, advection_xy_2fields

from .velocity_field import Velocity_Field, Velocity_Field_numba, Velocity_2Fields_numba

class Particles():

    def __init__(self, x0:np.ndarray=None, y0:np.ndarray=None, dir:Union[str,Path] = None, verbose:bool=False) -> None:

        self._color         = (0., 0., 0., 1.)
        self._linewidth     = 1.
        self._filename      = None
        self._dir           = Path(dir) if dir is not None else None

        self.blend          = True

        if x0 is None or y0 is None:
            if verbose:
                logging.info('No initial position given, set to 0.')
            return

        self.start_position = [x0, y0]
        self.end_position   = [x0.copy(), y0.copy()] # copy to define new memory storage
        self._is_alive      = np.ones_like(x0, dtype=np.bool)

    def copy_prop_from(self, other:'Particles') -> None:
        """
        Copy the properties from another Particles object.
        """
        self._color = other._color
        self._linewidth = other._linewidth

    def serialize(self) -> dict:
        """
        Serialize the object.
        """
        return {'size' : len(self.start_position[0]),
                'color':self._color,
                'linewidth':self._linewidth,
                'filename':self.filename}

    def deserialize(self, data:dict) -> None:
        """
        Deserialize the object.
        """
        self._color = data['color']
        self._linewidth = data['linewidth']
        self._filename = data['filename']

        if self._filename is None:
            logging.warning('No filename given, cannot load the particles.')
            return

        self.load(self.dir / self._filename)

    @property
    def color(self) -> tuple[float]:
        return self._color

    @color.setter
    def color(self, color:tuple[float]) -> None:
        self._color = color

    @property
    def linewidth(self) -> float:
        return self._linewidth

    @property
    def dir(self) -> Path:
        return Path(self._dir)

    @dir.setter
    def dir(self, dir:Union[str,Path]) -> None:
        self._dir = Path(dir)

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, filename:Union[str,Path]) -> None:
        self._filename = Path(filename).name

    @linewidth.setter
    def linewidth(self, linewidth:float) -> None:
        self._linewidth = linewidth

    def save(self, f:str) -> str:
        """
        Save the particles to file.
        """
        np.savez(f,
                 start_position_x = self.start_position[0],
                 start_position_y = self.start_position[1],
                 end_position_x   = self.end_position[0],
                 end_position_y   = self.end_position[1],
                 is_alive = self._is_alive)
        self._filename = Path(f).name

        return Path(f).name

    def load(self, f:Union[str,Path]) -> None:
        """
        Load the particles from file.
        """
        f = Path(f)

        if not f.exists():
            logging.warning(f'File {f} does not exist. -- Please check or (re)bake your particle system')
            return

        with np.load(f) as data:
            self.start_position = [data['start_position_x'], data['start_position_y']]
            self.end_position   = [data['end_position_x'], data['end_position_y']]
            self._is_alive      = data['is_alive']

        self._filename = Path(f).name

    def update(self,
               uv_field:tuple[Velocity_Field, Velocity_Field, float, float],
               curtime:float,
               dt:float,
               scheme:Union[Literal['Euler_expl', 'RK22', 'RK4', 'RK45'], int]) -> None:
        """
        Update the position of the particles.
        """

        if isinstance(scheme, int):
            if scheme == 0:
                scheme = 'Euler_expl'
            elif scheme == 1:
                scheme = 'RK22'
            elif scheme == 2:
                scheme = 'RK4'
            elif scheme == 3:
                scheme = 'RK45'

        uv1, uv2, t1, t2 = uv_field
        if scheme == 'RK45' or scheme==3:
            newdt = 0.
            start_t= 0.
            end_t = dt
            compute = True

            start_pos_x, start_pos_y = self.start_position[0].copy(), self.start_position[1].copy()
            end_pos_x,   end_pos_y   = self.end_position[0].copy()  , self.end_position[1].copy()

            while start_t < end_t:

                if start_t + newdt > end_t:
                    dt = end_t - start_t

                while compute:
                    if t2==-1.:
                        newdt = advection_xy(start_pos_x, start_pos_y, end_pos_x, end_pos_y,
                                             uv1.fields, dt, scheme)
                    else:
                        newdt = advection_xy_2fields(start_pos_x, start_pos_y, end_pos_x, end_pos_y,
                                                     Velocity_2Fields_numba(uv1.fields, uv2.fields, t1, t2-t1), curtime, dt, scheme)

                    if newdt >= dt:
                        # timestep is ok or has been augmented
                        compute = False
                        # copy the new position to the old one for the next local timestep
                        start_pos_x[:] = end_pos_x[:]
                        start_pos_y[:] = end_pos_y[:]
                    else:
                        # timestep too large, it has been reducded by a factor 2.
                        dt = newdt
                start_t += dt # update the local time with the timestep used to converge
                dt = newdt
                compute = True

            self.end_position[0][:] = end_pos_x[:]
            self.end_position[1][:] = end_pos_y[:]
        else:
            if t2==-1.:
                advection_xy(self.start_position[0], self.start_position[1], self.end_position[0], self.end_position[1],
                             uv1.fields, dt, scheme)
            else:
                advection_xy_2fields(self.start_position[0], self.start_position[1], self.end_position[0], self.end_position[1],
                                     Velocity_2Fields_numba(uv1.fields, uv2.fields, t1, t2-t1), curtime, dt, scheme)
        return

    def _check_alive(self,
                    inside_array:np.ndarray,
                    origx:float = 0.,
                    origy:float = 0.,
                    dx:float = 1.,
                    dy:float = 1.) -> None:
        """
        Check if the particles are still alive.
        """
        i = ((self.end_position[0] - origx) // dx).astype(np.int32)
        j = ((self.end_position[1] - origy) // dy).astype(np.int32)

        self._is_alive = inside_array[i,j]

    def get_alive(self,
                  inside_array:np.ndarray,
                  header:tuple[float] = (0., 0., 1., 1., 1, 1)) -> tuple[np.ndarray]:
        """
        Return the alive particles.
        """
        origx, origy, dx, dy, _, _ = header
        self._check_alive(inside_array, origx, origy, dx, dy)
        return self.end_position[0][self._is_alive], self.end_position[1][self._is_alive]

    def plot_mpl(self, ax:plt.Axes) -> None:
        """
        Plot the particles using matplotlib.
        """
        lines = [[(x1, y1), (x2, y2)] for x1, y1, x2, y2 in zip(self.start_position[0],
                                                                self.start_position[1],
                                                                self.end_position[0],
                                                                self.end_position[1])]
        ax.add_collection(mc.LineCollection(lines, linewidths=1., color='black'))
        ax.autoscale()
        ax.margins(0.1)

    def plot(self, alpha:float=1.):
        """
        Plot the particles.
        """
        vertices = np.vstack((self.start_position[0],
                              self.start_position[1],
                              self.end_position[0],
                              self.end_position[1]))

        vertices = vertices.T.flatten()

        vertices = np.array(vertices, dtype=np.float32)

        glColor4f(self._color[0], self._color[1], self._color[2], alpha)

        if self.blend:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            # glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
        else:
            glDisable(GL_BLEND)

        glEnableClientState(GL_VERTEX_ARRAY)
        # glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices) # 2 vertices per point, 32 bits floats, 0 stride (tightly packed), vertices array
        # glColorPointer(4, GL_FLOAT, 0, color)

        glDrawArrays(GL_LINES, 0, len(vertices) // 2,) # mode, first, count

         # mode in : GL_POINTS, GL_LINE_STRIP, GL_LINE_LOOP, GL_LINES, GL_LINE_STRIP_ADJACENCY, GL_LINES_ADJACENCY, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN, GL_TRIANGLES, GL_TRIANGLE_STRIP_ADJACENCY, GL_TRIANGLES_ADJACENCY and GL_PATCHES

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisable(GL_BLEND)
        # glDisableClientState(GL_COLOR_ARRAY)
