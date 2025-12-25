"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from OpenGL.GL  import *
import logging
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import json
from pathlib import Path
from typing import Union
from multiprocessing import Pool

# from wxasync import StartCoroutine
# import asyncio

from .advection import advection_xy

from .emitter import Emitter
from .particles import Particles
from .velocity_field import Velocity_Field
from ..PyVertexvectors import vector, wolfvertex


# async def _async_load_particle_file(x:tuple[float, int, dict, Path]) -> tuple[float, int, Particles]:
#     """
#     Asynchronous function to load the particles from file.
#     """
#     time, key, part, dir = x

#     mypart = Particles(dir=dir)
#     mypart.deserialize(part)

#     return time, key, mypart


def _load_particles_files(x:tuple[float, int, dict, Path]) -> tuple[float, int, Particles]:
    """
    Parallel/Multiprocessor function to load the particles from file.
    """
    time, key, part, dir = x

    mypart = Particles(dir=dir)
    mypart.deserialize(part)

    return time, key, mypart

class Particle_system():

    def __init__(self,
                 domain:np.ndarray = None,
                 emitters:list[Emitter] = None,
                 uv:list[Velocity_Field] = None,
                 times:list[float] = None) -> None:

        if times is None:
            times = [0.]
        else:
            assert len(times) == len(uv), 'times and uv must have the same length.'
            return

        self._filename = None

        self._time = 0.
        self._particles:dict[float, dict[int, Particles]] = {}

        self.totaltime = 0.
        self.dt = 0.
        self.scheme = 'RK22'

        self._current = None
        self._previous = None

        self._current_step = 0.
        self._current_step_idx = 0

        self._dir = None

        self.origx, self.origy = 0., 0.
        self.dx, self.dy = 1., 1.
        self.nbx, self.nby = 1, 1

        self._emitters = emitters
        self._inside_array = domain == 1 if domain is not None else None
        self._velocity_fields:dict[float:Velocity_Field] = {}

        if uv is not None:
            onefield = uv[0]

            self.origx, self.origy, self.dx, self.dy = onefield.origx, onefield.origy, onefield.dx, onefield.dy
            self.nbx, self.nby = onefield.u.shape

            self._velocity_fields = { curtime:curuv for curtime, curuv in zip(times,uv) }
            self.sort_vf()


    def reset(self) -> None:
        """
        Reset the particles.
        """
        self._time = 0.
        self._particles = {}
        self._current = None
        self._previous = None

    def check(self) -> tuple[bool, str]:
        """
        Check if the particle system is valid.
        """
        check = True
        message = ''

        if len(self._velocity_fields) == 0 :
            check = False
            message += 'No velocity field found.\n'

        if self._emitters is None:
            check = False
            message += 'No emitter found.\n'

        if self._inside_array is None:
            check = False
            message += 'No domain found.\n'

        if len(self._velocity_fields) >0:
            for idx, (keytime, field) in enumerate(self._velocity_fields.items()):
                loccheck, msg = field.check()
                if not loccheck:
                    check = False
                    message += f'Velocity field {idx} is not valid.\n' + msg

        if self.domain.shape != self.u.shape:
            check = False
            message += 'Domain and velocity field must have the same shape.\n'

        if self.get_header() != (self.origx, self.origy, self.dx, self.dy, self.nbx, self.nby):
            check = False
            message += 'Header of the velocity field is not valid.\n'

        for curtime, curfield in self._velocity_fields.items():
            if self.get_header() != curfield.get_header():
                check = False
                message += 'Header of the velocity field is not valid.\n'

        if self._emitters is not None:
            for idx, emitter in enumerate(self._emitters):
                loccheck, msg = emitter.check()
                if not loccheck:
                    check = False
                    message += f'Emitter {idx+1} is not valid.\n'+ msg

        if self.totaltime <= 0.:
            check = False
            message += 'totaltime <= 0.\n'

        if self.dt <= 0.:
            check = False
            message += 'dt <= 0.\n'

        if self.dt > self.totaltime:
            check = False
            message += 'dt > totaltime\n'

        if self.scheme not in ['Euler_expl', 'RK22', 'RK4', 'RK45']:
            check = False
            message += 'scheme not in [Euler_expl, RK22, RK4, RK45]\n'

        return check, message

    def append_velocity_field(self, uv:Velocity_Field, time:float) -> None:
        """
        Append a velocity field to the list.
        """
        self._velocity_fields[time] = uv
        self.sort_vf()

    def load_domain_uv_from_npz(self, filename:str):
        """
        Init the particle system from a npz file.

        the file must contain:
            - u: x velocity component - np.ndarray - float64
            - v: y velocity component - np.ndarray - float64
            - domain: array containing the domain - np.ndarray - int8
            - (optionl) header: tuple containing the header of the file (origx, origy, dx, dy, nbx, nby) - tuple[float]

        If haeder is not found, the header is set to (0., 0., 1., 1., u.shape[0], u.shape[1]).

        All arrays must have the same shape.

        After that, you have to define the emitters before baking the particles.
        """
        with np.load(filename) as data:
            if 'u' not in data.keys():
                raise KeyError('u not found in the npz file.')
                return
            if 'v' not in data.keys():
                raise KeyError('v not found in the npz file.')
                return
            if 'domain' not in data.keys():
                raise KeyError('domain not found in the npz file.')
                return

            assert data['u'].shape == data['v'].shape, 'u and v must have the same shape.'
            assert data['u'].shape == data['domain'].shape, 'u and domain must have the same shape.'

            if 'header' in data.keys():
                header = data['header']
                self.origx, self.origy, self.dx, self.dy, self.nbx, self.nby = header
            else:
                self.origx, self.origy = 0., 0.
                self.dx, self.dy = 1., 1.
                self.nbx, self.nby = data['u'].shape

            u = data['u']
            v = data['v']
            domain = data['domain']

            self.domain = domain
            self._velocity_fields = {0.: Velocity_Field(u, v, origx=self.origx, origy=self.origy, dx=self.dx, dy=self.dy)}

    @property
    def domain(self) -> np.ndarray:
        """
        Return the domain.
        """
        return self._inside_array

    @domain.setter
    def domain(self, domain:np.ndarray) -> None:
        """
        Set the domain.
        """
        self._inside_array = domain.copy()

    @property
    def u(self) -> np.ndarray:
        """
        Return the u component of the velocity field at time 0.
        """
        return self._velocity_fields[0.].u

    @property
    def v(self) -> np.ndarray:
        """
        Return the v component of the velocity field at time 0.
        """
        return self._velocity_fields[0.].v

    @property
    def blend(self) -> bool:
        """
        Return the blend property.
        """
        blending = np.asarray([part.blend for particles in self._particles.values() for part in particles.values()])
        return blending.all()

    @blend.setter
    def blend(self, value:bool) -> None:
        """
        Set the blend property.
        """
        for particles in self._particles.values():
            for part in particles.values():
                part.blend = value

    @property
    def times_vf(self):
        """ Return the times of the velocity fields. """
        return list(self._velocity_fields.keys())

    @property
    def times(self) -> np.ndarray:
        """
        Return the times.
        """
        return np.asarray(list(self._particles.keys()))

    @property
    def sorted_times_vf(self):
        """ Return the times of the velocity fields sorted. """
        return sorted(self._velocity_fields.keys())

    def find_uv1_uv2_t1_t2(self, curtime:float, first_idx:int=0) -> tuple[Velocity_Field, Velocity_Field, float, float, int]:
        """ Find the two closest velocity fields. """
        times = self.times_vf

        if len(times) == 1:
            return self._velocity_fields[times[0]], self._velocity_fields[times[0]], times[0], -1., 0
        else:
            idx = min(first_idx, len(times))
            while curtime >= times[idx]:
                idx += 1
                if idx == len(times):
                    idx -= 1
                    break

            if idx == len(times) - 1:
                return self._velocity_fields[times[idx]], self._velocity_fields[times[idx]], times[idx], -1., idx
            else:
                return self._velocity_fields[times[idx-1]], self._velocity_fields[times[idx]], times[idx-1], times[idx], idx

    def sort_vf(self):
        """ Sort the velocity fields and update times. """
        self._velocity_fields = {curtime:curvf for curtime, curvf in sorted(self._velocity_fields.items(), key=lambda item: item[0])}

    @property
    def colors(self) -> list[tuple[float]]:
        """
        Return the colors of the particles.
        """
        return [(step, key, part.color) for step, particles in self._particles.items() for key,part in particles.items()]

    @colors.setter
    def colors(self, colors:list[tuple[float, int, tuple[float]]]) -> None:
        """
        Set the colors of the particles.
        """
        for step, key, color in colors:
            try:
                self._particles[step][key].color = color
            except:
                logging.warning(f'Particles color not found at step {step} and key {key}.')

    @property
    def nb_steps(self) -> int:
        """
        Return the number of steps.
        """
        return len(self._particles)

    @property
    def keys(self) -> list[float]:
        """
        Return the keys of the particles.
        """
        return list(self._particles.keys())

    @property
    def number_of_vf(self) -> int:
        """
        Return the number of velocity fields.
        """
        return len(self._velocity_fields)

    @property
    def number_of_emitters(self) -> int:
        """
        Return the number of emitters.
        """
        if self._emitters is None:
            return 0
        return len(self._emitters)

    @property
    def current_step(self) -> float:
        """
        Return the current step.
        """
        return self._current_step

    @property
    def current_step_idx(self) -> int:
        """
        Return the current step index.
        """
        return self._current_step_idx

    @current_step.setter
    def current_step(self, value:Union[float, int]) -> None:
        """
        Set the current step.
        """

        if isinstance(value, int):
            if value < 0:
                value = 0

            if value >= len(self.keys):
                value = len(self.keys) - 1

            key = self.keys[value]
            self._current_step_idx = value

        elif isinstance(value, float):
            assert value in self.keys, f'Key {value} not found.'

            key = value
            self._current_step_idx = self.keys.index(key)
        else:
            raise TypeError('value must be an int or a float.')

        self._current_step = key

        self._current = self._particles[key]

    @current_step_idx.setter
    def current_step_idx(self, value:int) -> None:
        """
        Set the current step index.
        """
        self.current_step = int(value)

    @property
    def previous_step(self) -> float:
        """
        Return the previous step.
        """
        idx = self.current_step_idx
        idx -= 1
        if idx < 0:
            idx = 0

        return self.keys[idx]

    def n_previous_step(self, n:int=1) -> list[float]:
        """
        Return n previous steps.
        """
        prev=[]
        if len(self.keys)==0:
            return prev

        idx = self.current_step_idx
        for i in range(n):
            idx -= 1
            if idx < 0:
                idx = 0

            prev.append(self.keys[idx])

        return prev

    @property
    def dir(self) -> str:
        """
        Return the directory.
        """
        if dir is None:
            return ''
        else:
            return str(self._dir)

    @dir.setter
    def dir(self, dir:Union[str,Path]) -> None:
        """
        Set the directory.
        """
        self._dir = Path(dir)

    @property
    def bounds(self) -> tuple[float]:
        """
        Return the bounds of the object.
        """
        ox,oy,dx,dy,nbx,nby = self.get_header()
        return (ox, oy, ox+dx*float(nbx), oy+dy*float(nby))

    @property
    def path_emit(self) -> Path:
        """
        Return the path of the emitters.
        """
        return Path(self.dir) / 'emitters'

    @property
    def path_vf(self) -> Path:
        """
        Return the path of the velocity field.
        """
        return Path(self.dir) / 'velocity_fields'

    @property
    def path_particles(self) -> Path:
        """
        Return the path of the particles.
        """
        return Path(self.dir) / 'particles'

    @property
    def path_domain(self) -> Path:
        """
        Return the path of the domain.
        """
        return Path(self.dir) / 'domain.npz'

    def serialize(self) -> dict:
        """
        Serialize the object.
        """
        np.savez_compressed(self.path_domain, domain=self._inside_array)

        self.path_emit.mkdir(parents=True, exist_ok=True)
        self.path_vf.mkdir(parents=True, exist_ok=True)

        return {#'dir':self.dir,
                'origx':self.origx,
                'origy':self.origy,
                'dx':self.dx,
                'dy':self.dy,
                'nbx':self.nbx,
                'nby':self.nby,
                'totaltime':self.totaltime,
                'dt':self.dt,
                'scheme':self.scheme,
                'nb_emitters':self.number_of_emitters,
                'emitters':{idx:emitter.save(self.path_emit / 'emitter_{}'.format(idx))
                            for idx, emitter in enumerate(self._emitters)},
                'nb_vf':self.number_of_vf,
                'velocity_fields':{idx:vf.save(self.path_vf / 'vf_{}'.format(idx))
                                   for idx, vf in enumerate(self._velocity_fields.values())},
                'times_vf': list(self._velocity_fields.keys()),
                'particles':{time: {key: part.serialize() for key, part in allparts.items()}
                             for time, allparts in self._particles.items()}
                }

    def deserialize(self, data:dict) -> None:
        """
        Deserialize the object.
        """

        self._particles = {}
        self._current = None
        self._previous = None

        # self.dir = data['dir']
        self.origx = data['origx']
        self.origy = data['origy']
        self.dx = data['dx']
        self.dy = data['dy']
        self.nbx = data['nbx']
        self.nby = data['nby']
        try:
            self.totaltime = data['totaltime']
        except:
            pass
        try:
            self.dt = data['dt']
        except:
            pass
        try:
            self.scheme = data['scheme']
        except:
            pass

        self._inside_array = np.load(self.path_domain)['domain']

        self._emitters = [Emitter().load(self.path_emit / data['emitters'][str(idx)]) for idx in range(data['nb_emitters'])]

        times = data['times_vf']

        uv = [Velocity_Field().load(self.path_vf / data['velocity_fields'][str(idx)]) for idx in range(data['nb_vf'])]

        self._velocity_fields = { curtime:curuv for curtime, curuv in zip(times,uv) }

        # for time, allparts in data['particles'].items():
        #     self._particles[float(time)] = {}
        #     for key, part in allparts.items():
        #         self._particles[float(time)][int(key)] = Particles(dir=self.path_particles)
        #         self._particles[float(time)][int(key)].deserialize(part)

        locdir = self.path_particles

        #FIXME: this is not working
        # # asynchoronous loading of the particles
        # self.tasks = [asyncio.create_task(_async_load_particle_file((time, key, part, locdir))) for time, allparts in data['particles'].items() for key, part in allparts.items()]
        # loop = asyncio.get_event_loop()
        # self.async_load = [await task for task in self.tasks]

        # multiprocess loading of the particles
        with Pool() as pool:
            all_parts = pool.map(_load_particles_files, [(time, key, part, locdir) for time, allparts in data['particles'].items() for key, part in allparts.items()])

        self._particles = {float(time):{int(key):part} for time, key, part in all_parts}

        pass


    def save(self, f:str='', save_particles:bool = True)-> None:
        """
        Save the particles to file.
        """
        if f == '' and self._filename is None:
            return

        if f == '':
            f = self._filename
        else:
            self._filename = f

        self.dir = Path(f).parent

        self.path_particles.mkdir(parents=True, exist_ok=True)
        f_only = Path(f).name

        if save_particles:
            # save the particles in multiple files
            for time, particles in self._particles.items():
                for idx, particle in particles.items():
                    particle.save(self.path_particles / f'{f_only}_{time}_{idx}.npz')

        #serialize the object and save it
        serdict = self.serialize()

        f = Path(f).with_suffix('.json')
        json.dump(serdict, open(f'{f}', 'w'),indent=2)

    def load(self, f:str) -> None:
        """
        Load the particles from file.
        """

        f = Path(f).with_suffix('.json')
        self.dir = f.parent
        # load data and deserialize it to the object
        serdict = json.load(open(f'{f}', 'r'))
        self.deserialize(serdict)
        self._filename = f

    def get_header(self) -> tuple[float]:
        """
        Return the header of the file.
        """
        return (self.origx,
                self.origy,
                self.dx,
                self.dy,
                self.nbx,
                self.nby)

    def bake(self, total_time:float, dt:float, scheme:str = None, callback = None) -> None:
        """
        Bake the particles.
        """

        # sort velocity fields
        self.sort_vf()

        self._time = 0.

        self.totaltime = total_time
        self.dt = dt

        if scheme is not None:
            assert isinstance(scheme, str), 'scheme must be a string in [Euler_expl, RK22, RK4, RK45].'
            self.scheme = scheme

        assert isinstance(self.scheme, str), 'scheme must be a string in [Euler_expl, RK22, RK4, RK45].'

        # first step
        self._current = self._particles[self._time] = {}
        # pointer to the previous step
        self._previous = self._current
        # emit the particles
        for idx, emitter in enumerate(self._emitters):
             self._current[idx] = Particles(*emitter.emit(self._time))

        # iterate over the time

        time_reportin = total_time / 100.
        idx_time = 0
        while self._time < total_time:

            if self._time % time_reportin < dt:
                logging.info(f'Time: {self._time} / {total_time}')
                if callback is not None:
                    callback(self._time)

            uv1, uv2, t1, t2, idx_time = self.find_uv1_uv2_t1_t2(self._time, idx_time)

            # update the particles
            for particles in self._current.values():
                particles:Particles

                # test if there are particles
                if len(particles.start_position[0]) > 0:
                    particles.update((uv1, uv2, t1, t2), self._time, dt, self.scheme)

            # update the time
            self._time += dt

            # create particles for the next time step
            self._current = self._particles[self._time] = {}
            for idx, particles in enumerate(self._previous.values()):
                # copy the particles that are still alive
                x, y = particles.get_alive(self._inside_array, self.get_header())
                # emit new particles if any
                xnew, ynew = self._emitters[idx].emit(self._time)
                # concatenate the arrays
                self._current[idx] = Particles(np.concatenate((x, xnew)), np.concatenate((y, ynew)))

            # update the pointers
            self._previous = self._current

            # copy the properties of the previous step to the particles of the current one
            for cur, prev in zip(self._current.values(), self._previous.values()):
                cur:Particles
                cur.copy_prop_from(prev)

    def plot(self, time:float = -1., alpha:float=1.) -> None:
        """
        Plot the particles.
        """

        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
        glLineWidth(float(1.))

        if time == -1.:
            curdict = self._current
        else:
            if time not in self.keys:
                logging.warning('Time not found.')
                return

            curdict = self._particles[time]

        for particles in curdict.values():
            particles:Particles
            particles.plot(alpha=alpha)

        # glFlush()

    def plot_mpl(self, time:float = -1.) -> tuple[Figure, Axes]:
        """
        Plot the particles using Matplotlib.
        """
        fig, ax = plt.subplots()

        if time == 'all':
            for curdict in self._particles.values():
                for particles in curdict.values():
                    particles:Particles
                    particles.plot_mpl(ax)

            return fig, ax

        elif time == -1.:
            curdict = self._current
        else:
            if time not in list(self._particles.keys()):
                logging.warning('Time not found.')
                return

            curdict = self._particles[time]

        for particles in curdict.values():
            particles:Particles
            particles.plot_mpl(ax)

        ax.set_aspect('equal')
        fig.tight_layout()

        return fig, ax
