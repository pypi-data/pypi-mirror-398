"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import jax
from jax import lax, jit, grad
import jax.numpy as jnp
from jax.scipy.optimize import minimize
from jax._src.scipy.optimize.bfgs import minimize_bfgs
from scipy.optimize import minimize as minimize_scipy
import timeit
from matplotlib import pyplot as plt

def dichotomy(f, abi:jnp.array, args:jnp.array, tol:jnp.array=jnp.array([1e-8]), max_iter:jnp.array=jnp.array([1000])):
    """ Dichotomy algorithm to find the root of a function """

    def cond_fun(val:jnp.array) -> bool:
        """ Condition function for the while loop """
        a, b, i = val
        return jnp.any((b - a) > tol) & jnp.any(i < max_iter)

    def body_fun(val:jnp.array) -> jnp.array:
        """ Body function for the while loop """
        a, b, i = val
        c = (a + b) / 2.
        fa = f(a, args)
        fc = f(c, args)
        return lax.cond(fc == 0,
                        lambda _: jnp.array([c, b, i + 1]),
                        lambda _: lax.cond(fa * fc < 0,
                                           lambda _: jnp.array([a, c, i + 1]),
                                           lambda _: jnp.array([c, b, i + 1]), None), None)

    abi = lax.while_loop(cond_fun, body_fun, abi)
    return (abi[0] + abi[1]) / 2

@jit
def _colebrook_white(f:jnp.array, args:jnp.array) -> jnp.array:
    """
    Colebrook-White equation for friction factor

    @param args: array containing, k = roughness of the pipe [m], diameter of the pipe [m], Reynolds number [-]
    """
    k, diameter, reynolds = args
    ret = 1. / jnp.sqrt(f) + 2. * jnp.log10(k / (3.7 * diameter) + 2.51 / (reynolds * jnp.sqrt(f)))
    return ret

@jit
def _square_colebrook_white(f:jnp.array, args:jnp.array) -> jnp.array:
    """
    Square of Colebrook-White equation for friction factor to be minimized

    @param f: float, friction factor [-]
    @param args: array containing, k = roughness of the pipe [m], diameter of the pipe [m], Reynolds number [-]
    """
    return _colebrook_white(f,args)**2

@jit
def _scalar_exp_square_colebrook_white(g:jnp.array, args:jnp.array) -> jnp.array: #scalar
    """
    Square of Colebrook-White equation for friction factor to be minimized.

    Apply a transformation to the friction factor to avoid negative values.
    Exponential transformation is used.

    @param g: float, friction factor [-]
    @param args: array containing, k = roughness of the pipe [m], diameter of the pipe [m], Reynolds number [-]
    """
    f = jnp.exp(g)
    return jnp.sum(_colebrook_white(f,args)**2)

_grad_scalar_colebrook_white = grad(_scalar_exp_square_colebrook_white)

@jit
def grad_colebrook_white(f:jnp.array, args:jnp.array) -> jnp.array:
    """
    Gradient of the Colebrook-White equation for friction factor

    @param f: float, friction factor [-]
    @param args: array containing, k = roughness of the pipe [m], diameter of the pipe [m], Reynolds number [-]
    """

    # We must apply the exponential transformation to the friction factor
    # See : _scalar_exp_square_colebrook_white
    return _grad_scalar_colebrook_white(jnp.log(f), args)

@jit
def _min_colebrook_white(f:jnp.array, args:jnp.array) -> jnp.array:
    """
    Minimize the Colebrook-White equation using BFGS

    @param f: float, initial guess for the friction factor  [-]
    @param args: array containing, k = roughness of the pipe [m], diameter of the pipe [m], Reynolds number [-]
    """

    return jnp.sum(jnp.exp(minimize(_scalar_exp_square_colebrook_white, jnp.log(f), args=(args,), method='BFGS', tol=1e-8).x))


if __name__ == '__main__':

    args = jnp.array([1.e-4, .5, 1/(jnp.pi*(.5/2.)**2.)*.5/1.e-6])

    # Find the root of the Colebrook-White equation by dichotomy
    root = dichotomy(_colebrook_white, jnp.array([0.,2.,0]), args)
    print(f"The root of the function is approximately: {root}")

    optimum  = _min_colebrook_white(jnp.array([0.03]), args)

    print(f"The optimum of the function is approximately: {optimum}")
    print(f"Delta: {jnp.abs(root - optimum)}")

    # Create a test function to compare the time of execution between dichotomy and BFGS
    @jit
    def test_dichotomy():
        dichotomy(_colebrook_white, jnp.array([0.,2.,0]), args)

    @jit
    def test_bfgs():
        _min_colebrook_white(jnp.array([0.03]), args)

    time_dicho = timeit.timeit(test_dichotomy, number=10000)
    time_bfgs = timeit.timeit(test_bfgs, number=10000)
    print(f"Time for dichotomy: {time_dicho}")
    print(f"Time for BFGS: {time_bfgs}")

    # Plot the function and its gradient
    tested_f = jnp.arange(0.01, 0.03, 0.0001)
    optimum  = _min_colebrook_white(jnp.array([0.03]), args)
    all_f    = _square_colebrook_white(tested_f, args)
    all_grad_ret = grad_colebrook_white(tested_f, args)

    fig,ax = plt.subplots()
    ax.plot(tested_f, all_f)
    ax.plot(tested_f, all_grad_ret)
    ax.scatter(optimum, _square_colebrook_white(optimum, args), color='red', marker='o')
    ax.scatter(root, _colebrook_white(root, args), color='green', marker='X')
    plt.show()
