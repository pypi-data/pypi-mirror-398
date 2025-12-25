"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from math import pi
from scipy.optimize import newton, root, root_scalar, fsolve
import matplotlib.pyplot as plt
# from jax import grad, jit, numpy as jnp, Array
from numba import jit
from jax.scipy.optimize import minimize
import timeit

@jit(nopython=True)
def _colebrook_white(f:float, k:float, diameter:float, reynolds:float) -> float:
    """
    Colebrook-White equation for friction factor

    @param f: float, friction factor [-]
    @param k: float, roughness of the pipe [m]
    @param diameter: float, diameter of the pipe [m]
    @param reynolds: float, Reynolds number [-]
    """
    ret = 1. / np.sqrt(f) + 2. * np.log10(k / (3.7 * diameter) + 2.51 / (reynolds * np.sqrt(f)))
    return ret

@jit(nopython=True)
def _grad_colebrook_white(f, k, diameter, reynolds):

    term1 = -0.5 * f**(-1.5)
    term2 = 2. * (2.51 / (reynolds * np.sqrt(f))) * (-0.5 * f**(-1.5)) / (k / (3.7 * diameter) + 2.51 / (reynolds * np.sqrt(f)))
    return term1 + term2

def f_colebrook_white(f:float, k:float, diameter:float, reynolds:float) -> float:
    """
    Solve the Colebrook-White equation using Newton's method

    @param f: float, initial guess for the friction factor  [-]
    @param k: float, roughness of the pipe [m]
    @param diameter: float, diameter of the pipe [m]
    @param reynolds: float, Reynolds number [-]
    """

    f_sol = fsolve(_colebrook_white, f, args=(k, diameter, reynolds), xtol=1e-14, fprime=_grad_colebrook_white)
    return f_sol[0]

# Test multiple solvers

def test_colebrook_fsolve():
    """ Test the Colebrook-White equation using Scipy fsolve """

    k= 1.e-4
    diam = .5
    viscosity = 1.e-6
    area = pi * (diam/2.)**2.
    discharge = 1.
    velocity = discharge / area
    reynolds = velocity * diam / viscosity

    f_guess = 0.02  # Initial guess for the friction factor
    f_sol = fsolve(_colebrook_white, f_guess, args=(k, diam, reynolds), xtol=1e-6)
    return f_sol[0]

def test_colebrook_root_scalar():
    """ Test the Colebrook-White equation using Scipy root_scalar """

    k= 1.e-4
    diam = .5
    viscosity = 1.e-6
    area = pi * (diam/2.)**2.
    discharge = 1.
    velocity = discharge / area
    reynolds = velocity * diam / viscosity

    f_guess = 0.02  # Initial guess for the friction factor
    f_sol = root_scalar(_colebrook_white, method='brentq', bracket=[1e-10,10.], x0 = f_guess, args=(k, diam, reynolds)) #, fprime = grad_colebrook_white, fprime2 = grad2_colebrook_white, xtol=1e-6)
    return f_sol.root

def test_colebrook_newton():
    """ Test the Colebrook-White equation using Scipy newton """

    k= 1.e-4
    diam = .5
    viscosity = 1.e-6
    area = pi * (diam/2.)**2.
    discharge = 1.
    velocity = discharge / area
    reynolds = velocity * diam / viscosity

    f_guess = 0.02  # Initial guess for the friction factor

    f_sol = newton(_colebrook_white, f_guess, _grad_colebrook_white, args=(k, diam, reynolds), rtol=1e-6)
    return f_sol.item()

@jit(nopython=True)
def dichotomy(f, a:float, b:float, args, tol=1e-10, max_iter=1000):
    def cond_fun(val):
        a, b, i = val
        return (b - a) > tol

    def body_fun(val):
        a, b, i = val
        c = (a + b) / 2.
        k, diameter, reynolds = args
        fa = f(a, k, diameter, reynolds)
        fc = f(c, k, diameter, reynolds)
        if fc == 0:
            return (c, c, i + 1)
        else:
            if fa * fc < 0:
                return (a, c, i + 1)
            else:
                return (c, b, i + 1)

    i=0
    while cond_fun((a, b, i)) and i < max_iter:
        a, b, i = body_fun((a, b, 0))

    return (a + b) / 2

def test_colebrook_dichotomy():
    """ Test the Colebrook-White equation using Scipy root_scalar """

    k= 1.e-4
    diam = .5
    viscosity = 1.e-6
    area = pi * (diam/2.)**2.
    discharge = 1.
    velocity = discharge / area
    reynolds = velocity * diam / viscosity

    f_guess = 0.02  # Initial guess for the friction factor
    f_sol = dichotomy(_colebrook_white, 1e-10, 10., (k, diam, reynolds))
    return f_sol


if __name__ == '__main__':


    sol_newton_ref = f_colebrook_white(.02, 1.e-4, .5, 1/(pi*(.5/2.)**2.)*.5/1.e-6)

    sol_rootscalar = test_colebrook_root_scalar()
    sol_fsolve     = test_colebrook_fsolve()
    sol_newton     = test_colebrook_newton()
    sol_dicho      = test_colebrook_dichotomy()

    tfsolve     = timeit.timeit(test_colebrook_fsolve, number = 10000)
    tnewton     = timeit.timeit(test_colebrook_newton, number = 10000)
    trootscalar = timeit.timeit(test_colebrook_root_scalar, number = 10000)
    tdichotomy  = timeit.timeit(test_colebrook_dichotomy, number = 10000)

    assert abs(sol_newton_ref - sol_newton) < 1e-8
    assert abs(sol_newton_ref - sol_fsolve) < 1e-8
    assert abs(sol_newton_ref - sol_rootscalar) < 1e-8
    assert abs(sol_newton_ref - sol_dicho) < 1e-8

    pass
