"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from math import pi
from scipy.optimize import fsolve

from .losses import f_colebrook_white
from .fluids import Water

GRAVITY = 9.81 # m/s^2
class pipe():
    """ Pipe class for Bernoulli's equation """

    def __init__(self) -> None:

        self._head_up:float = 0.    # upstream head         [m]
        self._head_down:float = 0.  # downstream head       [m]
        self._flowrate:float = 0.   # flowrate              [$m^3s^{-1}$]
        self._k:float = 0.          # roughness of the pipe [m]

        self.length:float = 0.      # Length of the pipe [m]
        self.diameter:float = 0.    # Diameter of the pipe [m]

        self.fluid = Water()

        self.f = 0.02 # Initial guess for the friction factor

    @property
    def head_up(self):
        return self._head_up

    @head_up.setter
    def head_up(self, value):
        self._head_up = value

    @property
    def head_down(self):
        return self._head_down

    @head_down.setter
    def head_down(self, value):
        self._head_down = value

    @property
    def flowrate(self):
        return self._flowrate

    @flowrate.setter
    def flowrate(self, value):
        self._flowrate = value
        self._solve_friction_factor()

    @property
    def k(self):
        return self._k

    @k.setter
    def k(self, value):
        self._k = value
        self._solve_friction_factor()

    @property
    def area(self):
        return pi * (self.diameter/2.)**2.

    @property
    def velocity(self):
        return self.flowrate / self.area

    @property
    def perimeter(self):
        return pi * self.diameter

    @property
    def epsilon(self):
        return self.k / self.diameter

    @property
    def reynolds(self):
        return self.velocity * self.diameter / self.fluid.nu

    @property
    def head_loss_k(self):
        return self.length / self.diameter * self.friction_factor

    @property
    def head_loss(self):
        return self.head_loss_k * self.velocity**2. / (2. * GRAVITY)

    def _solve_friction_factor(self):
        """ Update the friction factor using the Colebrook-White equation """

        if self.reynolds==0.: # No flow
            self.f = 0.
        else:
            if self.f ==0.:
                self.f = 0.02
            self.f = f_colebrook_white(self.f, self.k, self.diameter, self.reynolds)

        return self.f

    @property
    def friction_factor(self):
        return self.f

    @property
    def bernoulli_error(self):
        return self.head_up - self.head_down - self.head_loss

    def solve_flowrate(self):

        def loc_bernoulli(flowrate):
            self.flowrate = flowrate[0]
            return self.bernoulli_error

        flowrate_solution = fsolve(loc_bernoulli, self.flowrate)

        self.flowrate = flowrate_solution[0]

        return self.flowrate

    def solve_head_up(self):

        def loc_bernoulli(head_up):
            self.head_up = head_up
            return self.bernoulli_error

        head_up_solution = fsolve(loc_bernoulli, self.head_up)

        self.head_up = head_up_solution[0]

        return self.head_up

    def solve_head_down(self):

        def loc_bernoulli(head_down):
            self.head_down = head_down
            return self.bernoulli_error

        head_down_solution = fsolve(loc_bernoulli, self.head_down)

        self.head_down = head_down_solution[0]

        return self.head_down

    def solve_k(self):

        def loc_bernoulli(k):
            self.k = k
            return self.bernoulli_error

        k_solution = fsolve(loc_bernoulli, self.k)

        self.k = k_solution[0]

        return self.k


if __name__ == '__main__':


    def test_pipe():
        pipe1 = pipe()

        pipe1.head_up = 10.
        pipe1.head_down = 0.
        pipe1.length = 100.
        pipe1.diameter = 0.5

        pipe1.k = 0.0001
        pipe1.flowrate = 1.

        print(pipe1.reynolds)

        print(pipe1.head_loss)

        assert abs(pipe1.head_loss - 3.737978364) < 1e-6

        print(pipe1.solve_flowrate())
        assert abs(pipe1.flowrate - 1.644579263) < 1e-6

        pipe1.flowrate = 1.
        pipe1.head_up = 10.
        print(pipe1.solve_head_down())

        assert abs(pipe1.head_down - 6.262021636) < 1e-6

        pipe1.flowrate = 1.
        pipe1.head_down = 0.
        print(pipe1.solve_head_up())

        assert abs(pipe1.head_up - 3.737978364) < 1e-6

        pipe1.flowrate = 1.
        pipe1.head_up = 10.
        pipe1.head_down = 0.
        print(pipe1.solve_k())

        assert abs(pipe1.k - 4.95827141E-03) < 1e-9

    pass
