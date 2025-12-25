
import numpy as np
from numba import njit, jit
from scipy.optimize import minimize
import logging

""" Using JIT to speed up the functions """
@njit
def sigmoid(x:np.float64, loc:np.float64, scale:np.float64) -> float:
    """ Sigmoid function """
    return 1. / (1. + np.exp(-scale * (x - loc)))

@njit
def sigmoid_derivative(x:np.float64, loc:np.float64, scale:np.float64) -> float:
    """ Derivative of the sigmoid function """
    s = sigmoid(x, loc, scale)
    return scale * s * (1. - s)

@njit
def sigmoid_second_derivative(x:np.float64, loc:np.float64, scale:np.float64) -> float:
    """ Second derivative of the sigmoid function """
    s = sigmoid(x, loc, scale)
    return scale**2. * s * (1. - s) * (1. - 2. * s)

@njit
def one_minus_sigmoid(x:np.float64, loc:np.float64, scale:np.float64) -> float:
    """ 1 - Sigmoid function """
    return 1. - sigmoid(x, loc, scale)

@njit
def extract_xy_binary_search(x_candidate:np.ndarray, x:np.ndarray, y:np.ndarray, nb_elemt:np.int64) -> tuple[np.ndarray, np.ndarray]:
    """ Binary search to find the interval of x values for each x_candidate

    :param x_candidate: np.ndarray values to extract the x and y values
    :param x: np.ndarray, list of floats, x values of the points
    :param y: np.ndarray, list of floats, y values of the points
    :param nb_elemt: int, number of elements to consider around the x_candidate value (must be odd)
    """

    n = len(x) - 1

    if np.mod(nb_elemt, 2) == 0:
        nb_elemt += 1

    nb_elemt = min(n, nb_elemt)

    results = np.zeros_like(x_candidate, dtype=np.int64)

    for idx, cur_x in enumerate(x_candidate):
        if cur_x < x[0]:
            results[idx] = 0
        elif cur_x > x[-1]:
            results[idx] = n - 1
        else:
            left = 0
            right = n - 1

            while right - left > 1:
                mid = (left + right) // 2
                if cur_x < x[mid]:
                    right = mid
                else:
                    left = mid

            results[idx] = left

    new_x = np.zeros((len(x_candidate), nb_elemt), dtype=np.float64)
    new_y = np.zeros((len(x_candidate), nb_elemt), dtype=np.float64)

    for idx, cur_x in enumerate(x_candidate):
        i = results[idx]
        if i < nb_elemt//2:
            new_x[idx,:] = x[:nb_elemt]
            new_y[idx,:] = y[:nb_elemt]
        elif i > n - nb_elemt//2:
            new_x[idx,:] = x[-nb_elemt:]
            new_y[idx,:] = y[-nb_elemt:]
        else:
            new_x[idx,:] = x[i-nb_elemt//2 : i+nb_elemt//2+1]
            new_y[idx,:] = y[i-nb_elemt//2 : i+nb_elemt//2+1]

    return new_x, new_y

@njit
def _piecewise_linear(x_candidate:np.ndarray, x:np.ndarray, y:np.ndarray,
                      scale:np.float64, slope_left:np.float64, slope_right:np.float64) -> np.ndarray:
    """ Piecewise linear function with continuous transition by sigmoids.

    In extrapolation mode, the function is y[0] for x < x[0] and linearly extrapoletd based on the last slope for x > x[-1].

    :param x_candidate: np.ndarray, list or float, x values to evaluate the function
    :param x: np.ndarray, list of floats, x values of the points
    :param y: np.ndarray, list of floats, y values of the points
    :param scale: float, scale of the sigmoid functions
    :param slope_left: float, slope before the first segment - extrapolation mode
    :param slope_right: float, slope after the last segment - extrapolation mode
    """

    # FIXME : Numba.JIT does not like np.concatenate, np.hstack... so we pre-allocate the arrays

    # Extend the x and y values to allow extrapolation based on slope_left and slope_right
    xx = np.zeros(x.shape[0]+1) # add the extrapolation points
    yy = np.zeros(y.shape[0]+1) # add the extrapolation points
    slopes = np.zeros(x.shape[0]+1)

    xx[0] = x[0]
    yy[0] = y[0]
    xx[1:] = x
    yy[1:] = y

    x = xx
    y = yy

    n = len(x) # number of intervals/segments taking into account the extrapolation
    results = np.zeros_like(x_candidate) # pre-allocate the results, force numpy type and not a list

    functions = np.zeros(n) # values of the linear functions for each segment

    sigmoids  = np.ones(n)
    one_minus_sigmoids = np.ones(n)

    # local slopes of the segments -- must be a **function** (no vertical slope, x increasing...)
    slopes[0] = slope_left
    slopes[1:-1] = (y[2:] - y[1:-1]) / (x[2:] - x[1:-1])
    slopes[-1] = slope_right

    for idx, cur_x in enumerate(x_candidate):
        # Copy the x value for each segment
        xvals = np.full(n, cur_x)
        # Compute the value of the linear function for each segment
        functions[:] = slopes[:] * (xvals[:] - x[:]) + y[:]
        # Compute the value of the sigmoid function for each segment (based on the start of the segment)
        sigmoids[1:] = sigmoid(xvals[1:], x[1:], scale)
        # Compute the value of 1 - sigmoid for each segment (based on the end of the segment)
        one_minus_sigmoids[:-1] = 1. - sigmoids[1:]

        """
        Interpolation mode : x[0] <= x_candidate <= x[-1]
        ------------------

        We will combine the results of each segment.
        For each segment, we use a door function that is 1 if we are in the segment and 0 otherwise.

          1      ____________
                 |          |
                 |          |
                 |          |
          0______|          |_______
                x1          x2

        The door function is the product of the sigmoid of the segment and the (1 - sigmoid) of the next segment.

        Door_i = sigmoid_i * (1 - sigmoid_{i+1})

        So, for x, we can compute the value of the function as a sum of the value of the function for each segment multiplied by the door function.

        f(x) = sum_i (functions_i(x) * Door_i)
        """

        results[idx] = np.sum(sigmoids * one_minus_sigmoids * functions)

    return results

@njit
def piecewise_linear(x_candidate:np.ndarray, x:np.ndarray, y:np.ndarray,
                     scale:np.float64, nb_elemt:np.int64,
                     slope_left:np.float64, slope_right:np.float64) -> np.ndarray:
    """ Piecewise linear function with continuous transition by sigmoids

    :param x_candidate: np.ndarray, list or float, x values to evaluate the function
    :param x: np.ndarray, list of floats, x values of the points
    :param y: np.ndarray, list of floats, y values of the points
    :param scale: float, scale of the sigmoid functions
    :param nb_elemt: int, number of elements to consider around the x_candidate value
    """

    results = np.zeros_like(x_candidate)

    if nb_elemt == -1:

        results[:] = _piecewise_linear(x_candidate, x, y, scale, slope_left, slope_right)

    else:
        xx, yy = extract_xy_binary_search(x_candidate, x, y, nb_elemt)

        for idx, cur_x in enumerate(x_candidate):
            results[idx] = _piecewise_linear(np.array([cur_x]), xx[idx], yy[idx], scale, slope_left, slope_right)[0]

    return results

@njit
def _gradient_piecewise_linear(x_candidate:np.ndarray, x:np.ndarray, y:np.ndarray,
                               scale:np.float64, slope_left:np.float64, slope_right:np.float64) -> np.ndarray:
    """ Gradient of the piecewise linear function """

    xx = np.zeros(x.shape[0]+1) # add the extrapolation points
    yy = np.zeros(y.shape[0]+1) # add the extrapolation points
    slopes = np.zeros(x.shape[0]+1)

    xx[0] = x[0]
    yy[0] = y[0]
    xx[1:] = x
    yy[1:] = y

    x = xx
    y = yy

    n = len(x)
    results = np.zeros_like(x_candidate)

    functions = np.zeros(n) # values of the linear functions for each segment

    sigmoids  = np.ones(n)
    one_minus_sigmoids = np.ones(n)

    slopes[0] = slope_left
    slopes[1:-1] = (y[2:] - y[1:-1]) / (x[2:] - x[1:-1])
    slopes[-1] = slope_right

    for idx, cur_x in enumerate(x_candidate):
        # Copy the x value for each segment
        xvals = np.full(n, cur_x)
        # Compute the value of the linear function for each segment
        functions[:] = slopes[:] * (xvals[:] - x[:]) + y[:]
        # Compute the value of the sigmoid function for each segment (based on the start of the segment)
        sigmoids[1:] = sigmoid(xvals[1:], x[1:], scale)
        # Compute the value of 1 - sigmoid for each segment (based on the end of the segment)
        one_minus_sigmoids[:-1] = 1. - sigmoids[1:]

        def derivative_sigmoid(sig, scale):
            return scale * sig * (1. - sig)

        def derivative_oneminussigmoid(oneminussig, scale):
            return -derivative_sigmoid(oneminussig, scale)

        result = 0.0
        for i in range(n):
            result += sigmoids[i] * one_minus_sigmoids[i] * slopes[i]
            result += (derivative_sigmoid(sigmoids[i], scale) * one_minus_sigmoids[i] + sigmoids[i] * derivative_oneminussigmoid(one_minus_sigmoids[i], scale)) * functions[i]

        results[idx] = result

    return results

@njit
def gradient_piecewise_linear(x_candidate:np.ndarray, x:np.ndarray, y:np.ndarray,
                              scale:np.float64, nb_elemt:np.int64,
                              slope_left:np.float64, slope_right:np.float64) -> np.ndarray:
    """ Gradient of the piecewise linear function """

    results = np.zeros_like(x_candidate)

    if nb_elemt == -1:

        results[:] = _gradient_piecewise_linear(x_candidate, x, y, scale, slope_left, slope_right)

    else:
        xx, yy = extract_xy_binary_search(x_candidate, x, y, nb_elemt)

        for idx, cur_x in enumerate(x_candidate):
            results[idx] = _gradient_piecewise_linear(np.array([cur_x]), xx[idx], yy[idx], scale, slope_left, slope_right)[0]

    return results

@njit
def _gradient_piecewise_linear_approx(x_candidate:np.ndarray, x:np.ndarray, y:np.ndarray,
                                      scale:np.float64, slope_left:np.float64, slope_right:np.float64):
    """ Approximative gradient of the piecewise linear function.

    The derivative contribution of the sigmoids is ignored.
    """

    x = np.hstack((x[0], x)) # add the extrapolation points
    y = np.hstack((y[0], y)) # add the extrapolation points

    n = len(x)
    results = np.zeros_like(x_candidate)

    functions = np.zeros(n) # values of the linear functions for each segment

    sigmoids  = np.ones(n)
    one_minus_sigmoids = np.ones(n)

    slopes = np.concatenate([ [slope_left], (y[2:] - y[1:-1]) / (x[2:] - x[1:-1]), [slope_right]])

    for idx, cur_x in enumerate(x_candidate):
        # Copy the x value for each segment
        xvals = np.full(n, cur_x)
        # Compute the value of the linear function for each segment
        functions[:] = slopes[:] * (xvals[:] - x[:]) + y[:]
        # Compute the value of the sigmoid function for each segment (based on the start of the segment)
        sigmoids[1:] = sigmoid(xvals[1:], x[1:], scale)
        # Compute the value of 1 - sigmoid for each segment (based on the end of the segment)
        one_minus_sigmoids[:-1] = 1. - sigmoids[1:]

        results[idx] = np.sum(sigmoids * one_minus_sigmoids * slopes)
        # result = 0.0
        # for i in range(n):
        #     result += sigmoids[i] * one_minus_sigmoids[i] * slopes[i]

        # results[idx] = result

    return results

@njit
def gradient_piecewise_linear_approx(x_candidate:np.ndarray, x:np.ndarray, y:np.ndarray,
                                     scale:np.float64, nb_elemt:np.int64,
                                     slope_left:np.float64, slope_right:np.float64):
    """ Approximative gradient of the piecewise linear function.

    The derivative contribution of the sigmoids is ignored.
    """

    results = np.zeros_like(x_candidate)

    if nb_elemt == -1:

        results[:] = _gradient_piecewise_linear_approx(x_candidate, x, y, scale, slope_left, slope_right)

    else:
        xx, yy = extract_xy_binary_search(x_candidate, x, y, nb_elemt)

        for idx, cur_x in enumerate(x_candidate):
            results[idx] = _gradient_piecewise_linear_approx(np.array([cur_x]), xx[idx], yy[idx], scale, slope_left, slope_right)[0]

    return results

class Piecewise_Linear_Sigmoid():
    """ Piecewise linear function with smooth transitions using sigmoids """

    def __init__(self, x, y, scale:float = 10., slope_left:float = 0., slope_right:float = 99999.):
        """
        :param x: np.ndarray or list of floats, x values of the points
        :param y: np.ndarray or list of floats, y values of the points
        :param scale: float, scale of the sigmoid functions
        """

        self.x:np.ndarray = np.asarray(x, dtype= np.float64).flatten()
        self.y:np.ndarray = np.asarray(y, dtype= np.float64).flatten()
        self.scale:np.float64 = np.float64(scale)
        self.slope_left:np.float64 = slope_left
        self.slope_right:np.float64 = slope_right

        self._checked_x = False
        self._checked_y = False

    @property
    def slope_left(self):
        return self._slope_left

    @property
    def slope_right(self):
        return self._slope_right

    @slope_left.setter
    def slope_left(self, value):
        self._slope_left = np.float64(value)

        if self._slope_left == 99999.:
            self._slope_left = (self.y[1] - self.y[0]) / (self.x[1] - self.x[0])

    @slope_right.setter
    def slope_right(self, value):
        self._slope_right = np.float64(value)

        if self._slope_right == 99999.:
            self._slope_right = (self.y[-1] - self.y[-2]) / (self.x[-1] - self.x[-2])


    def clip_around_x(self, x:np.ndarray, nb_elemt:int = -1) -> tuple[np.ndarray, np.ndarray]:
        """
        Clip the input array x around the existing x values

        :param x: np.ndarray, list or float, x values to clip
        :param nb_elemt: int, number of elements to consider around each x value
        :return: tuple of two np.ndarrays, clipped x and y values
        """
        if not self._checked_x:
            self.check_x()
            self._checked_x = True

        x_array = np.asarray(x, dtype=np.float64).flatten()
        return extract_xy_binary_search(x_array, self.x, self.y, np.int64(nb_elemt))

    def clip_around_y(self, y:np.ndarray, nb_elemt:int = -1) -> tuple[np.ndarray, np.ndarray]:
        """
        Clip the input array y around the existing y values

        :param y: np.ndarray, list or float, y values to clip
        :param nb_elemt: int, number of elements to consider around each y value
        :return: tuple of two np.ndarrays, clipped x and y values
        """
        if not self._checked_y:
            self.check_y()
            self._checked_y = True

        y_array = np.asarray(y, dtype=np.float64).flatten()
        return extract_xy_binary_search(y_array, self.y, self.x, np.int64(nb_elemt))

    def gradient(self, x, approximative:bool = False, nb_elemt:int = -1) -> np.ndarray:
        """ Gradient of the piecewise linear function with smooth transitions using sigmoids

        :param x: np.ndarray, list or float, x values to evaluate the gradient
        :param approximative: bool, if True, use an approximative gradient (ignoring derivative of the sigmoids)
        :param nb_elemt: int, number of elements to consider around the x_candidate value
        """

        if not self._checked_x:
            self.check_x()
            self._checked_x = True

        if approximative:
            if isinstance(x, np.ndarray):
                return gradient_piecewise_linear_approx(x.astype(np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self.slope_left, self._slope_right)
            elif isinstance(x, list):
                return gradient_piecewise_linear_approx(np.array(x, dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self.slope_left, self._slope_right)
            elif isinstance(x, float):
                return gradient_piecewise_linear_approx(np.array([x], dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self.slope_left, self._slope_right)[0]
            elif isinstance(x, int):
                return gradient_piecewise_linear_approx(np.array([float(x)], dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self.slope_left, self._slope_right)[0]
            else:
                raise ValueError('x should be np.ndarray, list or float')
        else:
            if isinstance(x, np.ndarray):
                return gradient_piecewise_linear(x.astype(np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self.slope_left, self._slope_right)
            elif isinstance(x, list):
                return gradient_piecewise_linear(np.array(x, dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self.slope_left, self._slope_right)
            elif isinstance(x, float):
                return gradient_piecewise_linear(np.array([x], dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self.slope_left, self._slope_right)[0]
            elif isinstance(x, int):
                return gradient_piecewise_linear(np.array([float(x)], dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self.slope_left, self._slope_right)[0]
            else:
                raise ValueError('x should be np.ndarray, list or float')

    def check_x(self):
        diff = np.diff(self.x)
        if np.any(diff <= 0):
            raise ValueError('x should be in increasing order')

    def check_y(self):
        diff = np.diff(self.y)
        if np.any(diff <= 0):
            raise ValueError('y should be in increasing order')

    def check(self):
        self.check_x()
        self.check_y()

        return True

    @property
    def n(self):
        """ Number of points """
        return len(self.x)

    @property
    def size(self):
        return self.n

    def __call__(self, x, nb_elemt:int = -1) -> np.ndarray:
        """ Evaluate the piecewise linear function at x

        :param x: np.ndarray, list or float, x values to evaluate the function
        :param nb_elemt: int, number of elements to consider around the x_candidate value
        """

        if not self._checked_x:
            self.check_x()
            self._checked_x = True

        if isinstance(x, np.ndarray):
            return piecewise_linear(x.astype(np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self._slope_left, self._slope_right)
        elif isinstance(x, list):
            return piecewise_linear(np.array(x, dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self._slope_left, self._slope_right)
        elif isinstance(x, float):
            return piecewise_linear(np.array([x], dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self._slope_left, self._slope_right)[0]
        elif isinstance(x, int):
            return piecewise_linear(np.array([float(x)], dtype=np.float64), self.x, self.y, self.scale, np.int64(nb_elemt), self._slope_left, self._slope_right)[0]
        else:
            raise ValueError('x should be np.ndarray, list or float')

    def inverse(self, y, nb_elemt:int = -1) -> np.ndarray:
        """ Evaluate the inverse of the piecewise linear function at y """

        if not self._checked_y:
            self.check_y()
            self._checked_y = True

        if isinstance(y, np.ndarray):
            return piecewise_linear(y.astype(np.float64), self.y, self.x, self.scale, np.int64(nb_elemt), 1./self._slope_left, 1./self._slope_right)
        elif isinstance(y, list):
            return piecewise_linear(np.array(y, dtype=np.float64), self.y, self.x, self.scale, np.int64(nb_elemt), 1./self._slope_left, 1./self._slope_right)
        elif isinstance(y, float):
            return piecewise_linear(np.array([y], dtype=np.float64), self.y, self.x, self.scale, np.int64(nb_elemt), 1./self._slope_left, 1./self._slope_right)[0]
        else:
            raise ValueError('y should be np.ndarray, list or float')

    def get_y(self, x, nb_elemt:int = -1):
        """ Get the value of the piecewise linear function at x """
        return self(x, nb_elemt)

    def get_x(self, y, nb_elemt:int = -1):
        """ Get the inverse of the piecewise linear function at y """
        return self.inverse(y, nb_elemt)

@njit
def _polynomial(coeffs:np.ndarray, x:np.float64):
    """ Polynomial function """
    return np.sum(coeffs * np.power(x, np.arange(len(coeffs))), dtype=np.float64)

@njit
def piecewise_polynomial(x_candidate:np.ndarray, x:np.ndarray, y:np.ndarray, poly_coeff:np.ndarray,
                         scale:np.float64,
                         slope_left:np.float64, slope_right:np.float64) -> np.ndarray:
    """ Piecewise polynomial function.

    :param x_candidate: np.ndarray, list or float, x values to evaluate the function
    :param x: np.ndarray, list of floats, x values of the transition points between polyomials functions
    :param poly_coeff: np.ndarray, list of floats, coefficients of the polynomial functions
    """

    c_left  = np.zeros(poly_coeff.shape[1], dtype=np.float64)
    c_right = np.zeros(poly_coeff.shape[1], dtype=np.float64)

    c_left[0] = y[0] - slope_left * x[0]
    c_left[1] = slope_left

    c_right[0] = y[-1] - slope_right * x[-1]
    c_right[1] = slope_right

    shape_max = max([len(coeffs) for coeffs in poly_coeff])
    polys = np.zeros((len(poly_coeff)+2, shape_max), dtype=np.float64)

    polys[0,:]  = c_left
    polys[-1,:] = c_right
    polys[1:-1,:] = poly_coeff

    # Extend the x and y values to allow extrapolation based on slope_left and slope_right
    xx = np.zeros(x.shape[0]+1) # add the extrapolation points

    xx[0] = x[0]
    xx[1:] = x

    x = xx

    n = len(polys)
    results = np.zeros(len(x_candidate))
    sigmoids  = np.ones(n)
    one_minus_sigmoids = np.ones(n)

    for idx, cur_x in enumerate(x_candidate):
        xvals = np.full(n, cur_x)
        sigmoids[1:] = sigmoid(xvals[1:], x[1:], scale)
        one_minus_sigmoids[:-1] = 1. - sigmoids[1:]

        for i in range(n):
            results[idx] += sigmoids[i] * one_minus_sigmoids[i] * _polynomial(polys[i], cur_x)

    return results


class Piecewise_Polynomial_Sigmoid():
    """ Polynomial function with smooth transitions using sigmoids """

    def __init__(self, x, y, scale:float = 10., degree:int = 3, slope_left:float = 0., slope_right:float = 99999.):

        self.x:np.ndarray = np.asarray(x, dtype= np.float64).flatten()
        self.y:np.ndarray = np.asarray(y, dtype= np.float64).flatten()
        self.scale:np.float64 = np.float64(scale)
        self.degree:int = degree

        self.slope_left:np.float64 = slope_left
        self.slope_right:np.float64 = slope_right

        self._poly_coeff = None
        self._parts_x = None
        self._parts_y = None

        self._checked_x = False
        self._checked_y = False

    @property
    def slope_left(self):
        return self._slope_left

    @property
    def slope_right(self):
        return self._slope_right

    @slope_left.setter
    def slope_left(self, value):
        self._slope_left = np.float64(value)

        if self._slope_left == 99999.:
            self._slope_left = (self.y[1] - self.y[0]) / (self.x[1] - self.x[0])

    @slope_right.setter
    def slope_right(self, value):
        self._slope_right = np.float64(value)

        if self._slope_right == 99999.:
            self._slope_right = (self.y[-1] - self.y[-2]) / (self.x[-1] - self.x[-2])

    def fit(self, forced_passage:np.ndarray, method:str = 'Nelder-Mead') -> np.ndarray:
        """ Convert XY points into nbparts polynomial segments.

        The segments are combined with sigmoids to ensure a smooth transition.

        The routine must find the best transition points to minimize error.
        """

        def error(coeffs, x, y, xx, yy, degree):
            nbparts = len(xx) - 1
            loc_coeffs = np.reshape(coeffs, (nbparts, degree+1))
            return np.sum((y - piecewise_polynomial(x, xx, yy, loc_coeffs, self.scale, self.slope_left, self.slope_right))**2)

        # Fit the polynomals coefficients
        nbparts = forced_passage.shape[0] - 1
        coeffs = np.zeros((nbparts, self.degree+1), dtype=np.float64)
        coeffs[:,0] = 0.
        coeffs[:,1] = 1.

        self._parts_x = forced_passage[:,0]
        self._parts_y = forced_passage[:,1]

        ret = minimize(error, args=(self.x, self.y,
                                    forced_passage[:,0], forced_passage[:,1],
                                    self.degree), x0=coeffs.flatten(),
                       method=method, tol= 1.e-14)

        self._poly_coeff = ret.x.reshape((nbparts, self.degree+1))

        return self._poly_coeff

    def fit_null_first_term(self, forced_passage:np.ndarray, method:str = 'Nelder-Mead') -> np.ndarray:
        """ Convert XY points into nbparts polynomial segments.

        The segments are combined with sigmoids to ensure a smooth transition.

        The routine must find the best transition points to minimize error.
        """

        def error(coeffs, x, y, xx, yy, degree):
            nbparts = len(xx) - 1
            loc_coeffs = np.zeros((nbparts, degree+1), dtype=np.float64).flatten()
            loc_coeffs[1:] = coeffs
            loc_coeffs = np.reshape(loc_coeffs, (nbparts, degree+1))

            return np.sum((y - piecewise_polynomial(x, xx, yy, loc_coeffs, self.scale, self.slope_left, self.slope_right))**2)

        # Fit the polynomals coefficients
        nbparts = forced_passage.shape[0] - 1
        coeffs = np.zeros((nbparts, self.degree+1), dtype=np.float64)
        coeffs[:,1] = (self.y[-1] - self.y[0]) / (self.x[-1] - self.x[0])

        self._parts_x = forced_passage[:,0]
        self._parts_y = forced_passage[:,1]

        ret = minimize(error, args=(self.x, self.y,
                                    forced_passage[:,0], forced_passage[:,1],
                                    self.degree), x0=coeffs.flatten()[1:],
                       method=method, tol= 1.e-14,
                       options={'maxiter': 100000})

        self._poly_coeff = np.zeros((nbparts, self.degree+1), dtype=np.float64).flatten()
        self._poly_coeff[1:] = ret.x
        self._poly_coeff = self._poly_coeff.reshape((nbparts, self.degree+1))

        return self._poly_coeff

    def check_x(self):
        diff = np.diff(self.x)
        if np.any(diff <= 0):
            raise ValueError('x should be in increasing order')

    def check_y(self):
        diff = np.diff(self.y)
        if np.any(diff <= 0):
            raise ValueError('y should be in increasing order')

    def check(self):
        self.check_x()
        self.check_y()

        return True

    @property
    def n(self):
        """ Number of points """
        return len(self.x)

    @property
    def size(self):
        return self.n

    def __call__(self, x, nb_elemt:int = -1) -> np.ndarray:
        """ Evaluate the piecewise linear function at x

        :param x: np.ndarray, list or float, x values to evaluate the function
        :param nb_elemt: int, number of elements to consider around the x_candidate value
        """

        if not self._checked_x:
            self.check_x()
            self._checked_x = True

        if isinstance(x, np.ndarray):
            return piecewise_polynomial(x.astype(np.float64), self._parts_x, self._parts_y, self._poly_coeff, self.scale, self._slope_left, self._slope_right)
        elif isinstance(x, list):
            return piecewise_polynomial(np.array(x, dtype=np.float64), self._parts_x, self._parts_y, self._poly_coeff, self.scale, self._slope_left, self._slope_right)
        elif isinstance(x, float):
            return piecewise_polynomial(np.array([x], dtype=np.float64), self._parts_x, self._parts_y, self._poly_coeff, self.scale, self._slope_left, self._slope_right)[0]
        elif isinstance(x, int):
            return piecewise_polynomial(np.array([float(x)], dtype=np.float64), self._parts_x, self._parts_y, self._poly_coeff, self.scale, self._slope_left, self._slope_right)[0]
        else:
            raise ValueError('x should be np.ndarray, list or float')

    def inverse(self, y, nb_elemt:int = -1) -> np.ndarray:
        """ Evaluate the inverse of the piecewise linear function at y """

        logging.warning('Inverse function not implemented yet')
        pass

    def get_y(self, x, nb_elemt:int = -1):
        """ Get the value of the piecewise linear function at x """
        return self(x, nb_elemt)

    def get_y_symmetry(self, x:np.ndarray, nb_elemt:int = -1):

        idx_sup = np.where(x > self.x[-1])[0]

        xloc = np.where(x <= self.x[-1], x, 2. * self.x[-1] - x)
        yloc = self(xloc, nb_elemt)

        if len(idx_sup) > 0:
            yloc[idx_sup] = 2. * self.y[-1] - yloc[idx_sup]

        return yloc

    def get_x(self, y, nb_elemt:int = -1):
        """ Get the inverse of the piecewise linear function at y """
        return self.inverse(y, nb_elemt)

if __name__ == '__main__':

    import matplotlib.pyplot as plt

    test_sigmoid = sigmoid(0., 0, 10)

    x = np.asarray([-2., 0, 1., 2., 4., 5.], dtype=np.float64)
    y = np.asarray([0., 0., 2., 8., -2., 5.], dtype=np.float64)
    x_test = np.linspace(-2, 6, 1000)

    x = np.arange(1000)
    y = np.sort(np.random.randn(1000))

    newx, newy = extract_xy_binary_search(x_test, x, y, np.int64(100))

    x_test = np.linspace(5, 1000, 100)

    fig, ax = plt.subplots()
    ax.plot(x, y, 'o')

    for scale in [0.01,.1,10.,100.]:
    # for scale in [100.]:
        xy = Piecewise_Linear_Sigmoid(x, y, scale)
        ax.plot(x_test, xy(x_test, nb_elemt= 5), label=f'scale={scale}')
        # ax.plot(x_test, xy.gradient(x_test), label=f'gradient={scale}')
        ax.plot(x_test, xy.gradient(x_test, True, nb_elemt= 5), label=f'gradient_approx={scale}')

    ax.legend()
    fig.show()

    plt.show()

    pass