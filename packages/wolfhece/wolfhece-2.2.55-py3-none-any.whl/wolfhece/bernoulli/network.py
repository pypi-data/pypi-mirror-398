
"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
import matplotlib.pyplot as plt

from .pipe import pipe
from .chamber import chamber, junction

class network():

    def __init__(self) -> None:

        self.chambers:list[chamber] = []
        self.pipes:list[pipe] = []
        self.links:list[tuple[chamber,chamber,pipe]] = []

    def add_chamber(self, chamber):
        self.chambers.append(chamber)

    def add_pipe(self, pipe):
        self.pipes.append(pipe)

    def link(self, chamber1, chamber2, pipe):
        self.links.append((chamber1, chamber2, pipe))

    def update(self, dt:float):

        for chamber in self.chambers:
            chamber.reset_q()

        for chamber1, chamber2, pipe in self.links:
            pipe.head_up = chamber1.head
            pipe.head_down = chamber2.head
            pipe.solve_flowrate()

            chamber1.add_qout(pipe.flowrate)
            chamber2.add_qin(pipe.flowrate)

        for chamber in self.chambers:
            chamber.update(dt)

if __name__ == "__main__":

    def test_simplenetwork():

        chamber1 = chamber()
        chamber2 = chamber()
        pipe1 = pipe()

        net = network()
        net.add_chamber(chamber1)
        net.add_chamber(chamber2)
        net.add_pipe(pipe1)
        net.link(chamber1, chamber2, pipe1)

        chamber1.elevation = 0.
        chamber2.elevation = 0.
        chamber1.area = 1.
        chamber2.area = 1.

        chamber1.head = 10.
        chamber2.head = 0.

        pipe1.viscosity = 1.e-6
        pipe1.density = 1000.
        pipe1.gravity = 9.81

        pipe1.length = 100.
        pipe1.diameter = 0.5

        pipe1.k = 0.0001

        net.update(1.)

    def test_simplenetwork_w_junction(dt:float = 1.):

        chamber1 = chamber()
        chamber2 = chamber()
        junc = junction()
        pipe1 = pipe()
        pipe2 = pipe()

        net = network()
        net.add_chamber(chamber1)
        net.add_chamber(chamber2)
        net.add_chamber(junc)

        net.add_pipe(pipe1)
        net.add_pipe(pipe2)

        net.link(chamber1, junc, pipe1)
        net.link(junc, chamber2, pipe2)

        chamber1.elevation = 0.
        chamber2.elevation = 0.

        chamber1.area = 1.
        chamber2.area = 1.

        chamber1.is_bc = True
        chamber1.bc_value = 10.

        chamber2.is_bc = True
        chamber2.bc_value = 0.

        chamber1.head = 10.
        chamber2.head = 0.
        junc.head = 4.

        for curpipe in [pipe1, pipe2]:

            curpipe.viscosity = 1.e-6
            curpipe.density = 1000.
            curpipe.gravity = 9.81

            curpipe.length = 50.
            curpipe.diameter = 0.5

            curpipe.k = 0.0001

        evol = [junc.head]
        old_head = 4.1
        while abs(junc.head - old_head) > 1e-6:
            old_head = junc.head
            net.update(dt)
            evol.append(junc.head)

        plt.plot(evol)
        plt.show()
