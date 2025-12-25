"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from wolfhece.lagrangian.velocity_field import Velocity_Field, Velocity_Field_numba, Velocity_2Fields_numba

import numpy as np
from numba import jit
from typing import Union, Literal

@jit(nopython=True)
def advection_xy(start_x:np.ndarray,
                 start_y:np.ndarray,
                 end_x:np.ndarray,
                 end_y:np.ndarray,
                 uv_field:Velocity_Field_numba,
                 dt:float,
                 scheme:Literal['Euler_expl', 'RK22', 'RK4', 'RK45']) -> float:
    """
    Update the position of the particles.
    """
    x,y = start_x, start_y
    xstar, ystar = end_x, end_y
    if scheme == 'Euler_expl':
        u, v = uv_field.interpolate(x, y)
        end_x[:] = x + u * dt
        end_y[:] = y + v * dt

    elif scheme == 'RK22':
        u1, v1 = uv_field.interpolate(x, y)
        xstar[:] = x + u1 * dt
        ystar[:] = y + v1 * dt
        u2, v2 = uv_field.interpolate(xstar, ystar)
        xstar[:] = x + (u1 + u2)/2. * dt
        ystar[:] = y + (v1 + v2)/2. * dt

    elif scheme== 'RK4':
        u1, v1 = uv_field.interpolate(x, y)
        xstar[:] = x + u1 *.5 * dt
        ystar[:] = y + v1 *.5 * dt
        u2, v2 = uv_field.interpolate(xstar, ystar)
        xstar[:] = x + u2 *.5 * dt
        ystar[:] = y + v2 *.5 * dt
        u3, v3 = uv_field.interpolate(xstar, ystar)
        xstar[:] = x + u3 * dt
        ystar[:] = y + v3 * dt
        u4, v4 = uv_field.interpolate(xstar, ystar)
        xstar[:] = x + u3 * dt
        ystar[:] = y + v3 * dt

        xstar[:] = x + (u1 + 2*u2 + 2*u3 + u4) / 6. * dt
        ystar[:] = y + (v1 + 2*v2 + 2*v3 + v4) / 6. * dt

    elif scheme == 'RK45':
        """Advection of particles using adaptive Runge-Kutta 4/5 integration.

        Times-step dt is halved if error is larger than tolerance, and doubled
        if error is smaller than 1/10th of tolerance, with tolerance set to
        1e-5 * dt by default.
        """
        rk45tol = 1e-5
        min_dt = 1e-3
        # c = [1./4., 3./8., 12./13., 1., 1./2.]
        A = [[1./4., 0., 0., 0., 0.],
            [3./32., 9./32., 0., 0., 0.],
            [1932./2197., -7200./2197., 7296./2197., 0., 0.],
            [439./216., -8., 3680./513., -845./4104., 0.],
            [-8./27., 2., -3544./2565., 1859./4104., -11./40.]]
        b4 = [25./216., 0., 1408./2565., 2197./4104., -1./5.]
        b5 = [16./135., 0., 6656./12825., 28561./56430., -9./50., 2./55.]

        u1, v1 = uv_field.interpolate(x, y)
        xstar[:] = x + u1 * A[0][0] * dt
        ystar[:] = y + v1 * A[0][0] * dt

        u2, v2 = uv_field.interpolate(xstar, ystar)
        xstar[:] = x + (u1 * A[1][0] + u2 * A[1][1]) * dt
        ystar[:] = y + (v1 * A[1][0] + v2 * A[1][1]) * dt

        u3, v3 = uv_field.interpolate(xstar, ystar)
        xstar[:] = x + (u1 * A[2][0] + u2 * A[2][1] + u3 * A[2][2]) * dt
        ystar[:] = y + (v1 * A[2][0] + v2 * A[2][1] + v3 * A[2][2]) * dt

        u4, v4 = uv_field.interpolate(xstar, ystar)
        xstar[:] = x + (u1 * A[3][0] + u2 * A[3][1] + u3 * A[3][2] + u4 * A[3][3]) * dt
        ystar[:] = y + (v1 * A[3][0] + v2 * A[3][1] + v3 * A[3][2] + v4 * A[3][3]) * dt

        u5, v5 = uv_field.interpolate(xstar, ystar)
        xstar[:] = x + (u1 * A[4][0] + u2 * A[4][1] + u3 * A[4][2] + u4 * A[4][3] + u5 * A[4][4]) * dt
        ystar[:] = y + (v1 * A[4][0] + v2 * A[4][1] + v3 * A[4][2] + v4 * A[4][3] + v5 * A[4][4]) * dt

        u6, v6 = uv_field.interpolate(xstar, ystar)

        x_4th = (u1 * b4[0] + u2 * b4[1] + u3 * b4[2] + u4 * b4[3] + u5 * b4[4]) * dt
        y_4th = (v1 * b4[0] + v2 * b4[1] + v3 * b4[2] + v4 * b4[3] + v5 * b4[4]) * dt
        x_5th = (u1 * b5[0] + u2 * b5[1] + u3 * b5[2] + u4 * b5[3] + u5 * b5[4] + u6 * b5[5]) * dt
        y_5th = (v1 * b5[0] + v2 * b5[1] + v3 * b5[2] + v4 * b5[3] + v5 * b5[4] + v6 * b5[5]) * dt

        kappa2 = np.power(x_5th - x_4th, 2) + np.power(y_5th - y_4th, 2)
        if np.all(kappa2 <= np.power(np.abs(dt * rk45tol), 2)) or dt < min_dt:
            xstar[:] = x + x_4th  # noqa
            ystar[:] = y + y_4th  # noqa
            if np.all(kappa2 <= np.power(np.abs(dt * rk45tol / 10), 2)):
                return dt * 2
            else:
                return dt
        else:
            return dt / 2

    return dt

@jit(nopython=True)
def advection_xy_2fields(start_x:np.ndarray,
                         start_y:np.ndarray,
                         end_x:np.ndarray,
                         end_y:np.ndarray,
                         uv_fields:Velocity_2Fields_numba,
                         current_time:float,
                         dt:float,
                         scheme:Literal['Euler_expl', 'RK22', 'RK4', 'RK45']) -> float:
    """
    Update the position of the particles.
    """
    x,y = start_x, start_y
    xstar, ystar = end_x, end_y
    if scheme == 'Euler_expl':
        u, v = uv_fields.interpolate(x, y, current_time)
        end_x[:] = x + u * dt
        end_y[:] = y + v * dt

    elif scheme == 'RK22':
        u1, v1 = uv_fields.interpolate(x, y, current_time)
        xstar[:] = x + u1 * dt
        ystar[:] = y + v1 * dt
        u2, v2 = uv_fields.interpolate(xstar, ystar, current_time + dt)
        xstar[:] = x + (u1 + u2)/2. * dt
        ystar[:] = y + (v1 + v2)/2. * dt

    elif scheme== 'RK4':
        u1, v1 = uv_fields.interpolate(x, y, current_time)
        xstar[:] = x + u1 *.5 * dt
        ystar[:] = y + v1 *.5 * dt
        u2, v2 = uv_fields.interpolate(xstar, ystar, current_time + dt/2.)
        xstar[:] = x + u2 *.5 * dt
        ystar[:] = y + v2 *.5 * dt
        u3, v3 = uv_fields.interpolate(xstar, ystar, current_time + dt/2.)
        xstar[:] = x + u3 * dt
        ystar[:] = y + v3 * dt
        u4, v4 = uv_fields.interpolate(xstar, ystar, current_time + dt)
        xstar[:] = x + u3 * dt
        ystar[:] = y + v3 * dt

        xstar[:] = x + (u1 + 2*u2 + 2*u3 + u4) / 6. * dt
        ystar[:] = y + (v1 + 2*v2 + 2*v3 + v4) / 6. * dt

    elif scheme == 'RK45':
        """Advection of particles using adaptive Runge-Kutta 4/5 integration.

        Times-step dt is halved if error is larger than tolerance, and doubled
        if error is smaller than 1/10th of tolerance, with tolerance set to
        1e-5 * dt by default.
        """
        rk45tol = 1e-5
        min_dt = 1e-3
        c = [1./4., 3./8., 12./13., 1., 1./2.]
        A = [[1./4., 0., 0., 0., 0.],
            [3./32., 9./32., 0., 0., 0.],
            [1932./2197., -7200./2197., 7296./2197., 0., 0.],
            [439./216., -8., 3680./513., -845./4104., 0.],
            [-8./27., 2., -3544./2565., 1859./4104., -11./40.]]
        b4 = [25./216., 0., 1408./2565., 2197./4104., -1./5.]
        b5 = [16./135., 0., 6656./12825., 28561./56430., -9./50., 2./55.]

        u1, v1 = uv_fields.interpolate(x, y, current_time)
        xstar[:] = x + u1 * A[0][0] * dt
        ystar[:] = y + v1 * A[0][0] * dt

        u2, v2 = uv_fields.interpolate(xstar, ystar, current_time + c[0] * dt)
        xstar[:] = x + (u1 * A[1][0] + u2 * A[1][1]) * dt
        ystar[:] = y + (v1 * A[1][0] + v2 * A[1][1]) * dt

        u3, v3 = uv_fields.interpolate(xstar, ystar, current_time + c[1] * dt)
        xstar[:] = x + (u1 * A[2][0] + u2 * A[2][1] + u3 * A[2][2]) * dt
        ystar[:] = y + (v1 * A[2][0] + v2 * A[2][1] + v3 * A[2][2]) * dt

        u4, v4 = uv_fields.interpolate(xstar, ystar, current_time + c[2] * dt)
        xstar[:] = x + (u1 * A[3][0] + u2 * A[3][1] + u3 * A[3][2] + u4 * A[3][3]) * dt
        ystar[:] = y + (v1 * A[3][0] + v2 * A[3][1] + v3 * A[3][2] + v4 * A[3][3]) * dt

        u5, v5 = uv_fields.interpolate(xstar, ystar, current_time + c[3] * dt)
        xstar[:] = x + (u1 * A[4][0] + u2 * A[4][1] + u3 * A[4][2] + u4 * A[4][3] + u5 * A[4][4]) * dt
        ystar[:] = y + (v1 * A[4][0] + v2 * A[4][1] + v3 * A[4][2] + v4 * A[4][3] + v5 * A[4][4]) * dt

        u6, v6 = uv_fields.interpolate(xstar, ystar, current_time + c[4] * dt)

        x_4th = (u1 * b4[0] + u2 * b4[1] + u3 * b4[2] + u4 * b4[3] + u5 * b4[4]) * dt
        y_4th = (v1 * b4[0] + v2 * b4[1] + v3 * b4[2] + v4 * b4[3] + v5 * b4[4]) * dt
        x_5th = (u1 * b5[0] + u2 * b5[1] + u3 * b5[2] + u4 * b5[3] + u5 * b5[4] + u6 * b5[5]) * dt
        y_5th = (v1 * b5[0] + v2 * b5[1] + v3 * b5[2] + v4 * b5[3] + v5 * b5[4] + v6 * b5[5]) * dt

        kappa2 = np.power(x_5th - x_4th, 2) + np.power(y_5th - y_4th, 2)
        if np.all(kappa2 <= np.power(np.abs(dt * rk45tol), 2)) or dt < min_dt:
            xstar[:] = x + x_4th  # noqa
            ystar[:] = y + y_4th  # noqa
            if np.all(kappa2 <= np.power(np.abs(dt * rk45tol / 10), 2)):
                return dt * 2
            else:
                return dt
        else:
            return dt / 2

    return dt