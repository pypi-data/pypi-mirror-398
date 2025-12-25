"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from math import pi

class chamber():

    def __init__(self) -> None:

        self.area = 10. # m^2
        self.elevation = 0. # m
        self._volume = 100. # m^3
        self._height = 10. # m

        self.q_in  = []
        self.q_out = []

        self.is_bc = False
        self.bc_value = 0.

    def reset_q(self):
        self.q_in = []
        self.q_out = []

    def add_qin(self, q):
        self.q_in.append(q)

    def add_qout(self, q):
        self.q_out.append(q)

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value
        self.solve_height()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self.solve_volume()

    def solve_volume(self):
        self._volume = self.area * self.height
        return self._volume

    def solve_height(self):
        self._height = self.volume / self.area
        return self._height

    def update(self, dt:float):

        if self.is_bc:
            self.head = self.bc_value
        else:
            self.volume += (np.sum(np.asarray(self.q_in)) - np.sum(np.asarray(self.q_out))) * dt
            self.solve_height()

    @property
    def head(self):
        return self.elevation + self.height

    @head.setter
    def head(self, value):
        self.height = value - self.elevation
        self.solve_volume()

class junction(chamber):

    def __init__(self) -> None:
        super().__init__()
        self.area = 1.e-2
        self.volume = 0.
        self.height = 0.
        self.elevation = 0.

        self._head = 0.

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, value):
        self._head = value

    def update(self, dt:float):

        self.head += (np.sum(np.asarray(self.q_in)) - np.sum(np.asarray(self.q_out))) * dt
