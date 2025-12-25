"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from numba import float64, float32, int32, int64, char
from numba import jit
from numba.experimental import jitclass
from pathlib import Path
import json

import logging
numba_logger = logging.getLogger('numba')
numba_logger.setLevel(logging.WARNING)

spec = [
    ('origx', float64),
    ('origy', float64),
    ('dx', float64),
    ('dy', float64),
    ('u', float64[:,:]),
    ('v', float64[:,:])
]

spec2 = [
    ('origx', float64),
    ('origy', float64),
    ('dx', float64),
    ('dy', float64),
    ('u1', float64[:,:]),
    ('v1', float64[:,:]),
    ('u2', float64[:,:]),
    ('v2', float64[:,:]),
    ('start_time', float64),
    ('dt', float64),
    ('pond1', float64)
]

@jit(nopython=True)
def interpolate(u:np.ndarray, v:np.ndarray, x:np.ndarray, y:np.ndarray, car:tuple[float]) -> tuple[np.ndarray]:

    origx, origy, dx, dy = car

    i = ((x - origx) // dx).astype(np.int32)
    j = ((y - origy) // dy).astype(np.int32)
    ksi = np.mod(x - origx, dx) / dx
    eta = np.mod(y - origy, dy) / dy

    uloc = np.asarray([u[i,j]*(1.-pond) + pond * u[i+1,j] for i,j, pond in zip(i,j,ksi)])
    vloc = np.asarray([v[i,j]*(1.-pond) + pond * v[i,j+1] for i,j, pond in zip(i,j,eta)])

    return uloc, vloc

@jit(nopython=True)
def interpolate2fields(u1:np.ndarray, v1:np.ndarray,
                       u2:np.ndarray, v2:np.ndarray,
                       x:np.ndarray, y:np.ndarray,
                       car:tuple[float]) -> tuple[np.ndarray]:

    origx, origy, dx, dy = car

    i = ((x - origx) // dx).astype(np.int32)
    j = ((y - origy) // dy).astype(np.int32)
    ksi = np.mod(x - origx, dx) / dx
    eta = np.mod(y - origy, dy) / dy

    uloc1 = np.asarray([u1[i,j]*(1.-pond) + pond * u1[i+1,j] for i,j, pond in zip(i,j,ksi)])
    vloc1 = np.asarray([v1[i,j]*(1.-pond) + pond * v1[i,j+1] for i,j, pond in zip(i,j,eta)])

    uloc2 = np.asarray([u2[i,j]*(1.-pond) + pond * u2[i+1,j] for i,j, pond in zip(i,j,ksi)])
    vloc2 = np.asarray([v2[i,j]*(1.-pond) + pond * v2[i,j+1] for i,j, pond in zip(i,j,eta)])

    return uloc1, vloc1, uloc2, vloc2

@jit(nopython=True)
def interpolate2fields_time(u1:np.ndarray, v1:np.ndarray,
                            u2:np.ndarray, v2:np.ndarray,
                            x:np.ndarray, y:np.ndarray,
                            car:tuple[float], pond1:float) -> tuple[np.ndarray]:

    origx, origy, dx, dy = car

    i = ((x - origx) // dx).astype(np.int32)
    j = ((y - origy) // dy).astype(np.int32)
    ksi = np.mod(x - origx, dx) / dx
    eta = np.mod(y - origy, dy) / dy

    uloc1 = np.asarray([u1[i,j]*(1.-pond_ij) + pond_ij * u1[i+1,j] for i,j, pond_ij in zip(i,j,ksi)])
    vloc1 = np.asarray([v1[i,j]*(1.-pond_ij) + pond_ij * v1[i,j+1] for i,j, pond_ij in zip(i,j,eta)])

    uloc2 = np.asarray([u2[i,j]*(1.-pond_ij) + pond_ij * u2[i+1,j] for i,j, pond_ij in zip(i,j,ksi)])
    vloc2 = np.asarray([v2[i,j]*(1.-pond_ij) + pond_ij * v2[i,j+1] for i,j, pond_ij in zip(i,j,eta)])

    return uloc1 * pond1 + uloc2 * (1.-pond1), vloc1 * pond1 + vloc2 * (1.-pond1)

@jitclass(spec)
class Velocity_Field_numba():

    def __init__(self,
                u:np.ndarray,
                v:np.ndarray,
                origx:float = 0.,
                origy:float = 0.,
                dx:float = 1.,
                dy:float = 1.) -> None:

        self.origx, self.origy = origx, origy
        self.dx, self.dy = dx, dy

        self.u = u
        self.v = v

    def interpolate(self, x:np.ndarray, y:np.ndarray) -> tuple[np.ndarray]:

        u, v = interpolate(self.u, self.v, x, y, (self.origx, self.origy, self.dx, self.dy))

        return u, v

    def interpolate2(self, x:np.ndarray, y:np.ndarray) -> tuple[np.ndarray]:

        i = ((x - self.origx) // self.dx).astype(np.int32)
        j = ((y - self.origy) // self.dy).astype(np.int32)
        ksi = np.mod(x - self.origx, self.dx) / self.dx
        eta = np.mod(y - self.origy, self.dy) / self.dy

        uloc = np.asarray([self.u[i,j]*(1.-pond) + pond * self.u[i+1,j] for i,j, pond in zip(i,j,ksi)])
        vloc = np.asarray([self.v[i,j]*(1.-pond) + pond * self.v[i,j+1] for i,j, pond in zip(i,j,eta)])

        return uloc, vloc

@jitclass(spec2)
class Velocity_2Fields_numba():

    # def __init__(self,
    #             u1:np.ndarray,
    #             v1:np.ndarray,
    #             u2:np.ndarray,
    #             v2:np.ndarray,
    #             origx:float = 0.,
    #             origy:float = 0.,
    #             dx:float = 1.,
    #             dy:float = 1.,
    #             start_time:float = 0.,
    #             dt:float = 1.) -> None:

    #     self.origx, self.origy = origx, origy
    #     self.dx, self.dy = dx, dy

    #     self.dt = dt
    #     self.start_time = start_time
    #     self.pond1 = 1.

    #     self.u1 = u1
    #     self.v1 = v1

    #     self.u2 = u2
    #     self.v2 = v2

    def __init__(self,
                 uv1:Velocity_Field_numba,
                 uv2:Velocity_Field_numba,
                 start_time:float,
                 delta_time:float) -> None:
        """
        :param uv1 is the velocity field at time start_time
        :param uv2 is the velocity field at time start_time + delta_time
        :param start_time is the time of uv1
        :param delta_time is the time between uv1 and uv2
        """

        self.origx, self.origy = uv1.origx, uv1.origy
        self.dx, self.dy = uv1.dx, uv1.dy

        self.dt = delta_time
        self.start_time = start_time
        self.pond1 = 1.

        self.u1 = uv1.u
        self.v1 = uv1.v

        self.u2 = uv2.u
        self.v2 = uv2.v

    def interpolate(self, x:np.ndarray, y:np.ndarray, time:float) -> tuple[np.ndarray]:

        u, v = interpolate2fields_time(self.u1, self.v1,
                                       self.u2, self.v2,
                                       x, y,
                                       (self.origx, self.origy, self.dx, self.dy),
                                       1. - (time - self.start_time)/self.dt)

        return u, v

class Velocity_Field():

    def __init__(self,
                 u:np.ndarray=None,
                 v:np.ndarray=None,
                 origx:float = 0.,
                 origy:float = 0.,
                 dx:float = 1.,
                 dy:float = 1.) -> None:

        if u is not None and v is not None:
            self.set_uv(u, v, origx, origy, dx, dy)

        self.filename = ''

    def set_uv(self,
               u:np.ndarray,
               v:np.ndarray,
               origx:float=0.,
               origy:float=0.,
               dx:float=1.,
               dy:float=1.) -> None:

        self._vf_numba = Velocity_Field_numba(u, v, origx, origy, dx, dy)

    @property
    def fields(self) -> Velocity_Field_numba:
        return self._vf_numba

    @property
    def origx(self) -> float:
        return self._vf_numba.origx

    @property
    def origy(self) -> float:
        return self._vf_numba.origy

    @property
    def dx(self) -> float:
        return self._vf_numba.dx

    @property
    def dy(self) -> float:
        return self._vf_numba.dy

    @property
    def u(self) -> np.ndarray:
        return self._vf_numba.u

    @property
    def v(self) -> np.ndarray:
        return self._vf_numba.v

    def check(self) -> tuple[bool, str]:
        """
        Check if the velocity field is valid.
        """
        check = True
        msg=''

        if self.u is None:
            check = False
            msg += 'u is None\n'

        if self.v is None:
            check = False
            msg += 'v is None\n'

        if self.u.shape != self.v.shape:
            check = False
            msg += 'u and v have different shapes\n'

        if self.dx <= 0.:
            check = False
            msg += 'dx <= 0.\n'

        if self.dy <= 0.:
            check = False
            msg += 'dy <= 0.\n'

        if self.origx is None:
            check = False
            msg += 'origx is None\n'

        if self.origy is None:
            check = False
            msg += 'origy is None\n'

        if self.dx != self.dy:
            check = False
            msg += 'dx != dy\n'

        if self._vf_numba is None:
            check = False
            msg += 'numba object is None\n'

        return check, msg

    def get_header(self) -> tuple[float]:
        return self.origx, self.origy, self.dx, self.dy, self.u.shape[0], self.u.shape[1]

    def serialize(self) -> dict:
        """
        Serialize the object.
        """
        return {'uv':self.filename,
                'header':(self.origx, self.origy, self.dx, self.dy)}

    def deserialize(self, data:dict) -> None:
        """
        Deserialize the object.
        """
        origx, origy, dx, dy = data['header']
        self.filename = data['uv']

        with np.load(self._dir / self.filename) as data:
            u = data['u']
            v = data['v']

        self.set_uv(u, v, origx, origy, dx, dy)

    def save(self, f:str) -> str:
        """
        Save the velocity field to file.
        """
        f = Path(f).with_suffix('.npz')
        np.savez_compressed(f, u=self.u, v=self.v)
        self.filename = f.name

        f = Path(f).with_suffix('.json')
        with open(f, 'w') as fp:
            json.dump(self.serialize(), fp, indent=2)

        return f.name

    def load(self, f:str) -> "Velocity_Field":
        """
        Load the velocity field from file.
        """
        f = Path(f).with_suffix('.json')
        self._dir = f.parent
        with open(f, 'r') as fp:
            self.deserialize(json.load(fp))

        return self

    def interpolate(self, x:np.ndarray, y:np.ndarray) -> tuple[np.ndarray]:

        u, v = self._vf_numba.interpolate(x, y)

        return u, v

    def interpolate2(self, x:np.ndarray, y:np.ndarray) -> tuple[np.ndarray]:

        uloc, vloc = self._vf_numba.interpolate2(x, y)

        return uloc, vloc
