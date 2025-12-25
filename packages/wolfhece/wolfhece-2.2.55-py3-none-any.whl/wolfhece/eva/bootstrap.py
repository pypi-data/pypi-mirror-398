"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

"""
Boostraping
"""
import numpy as np

class Bootstrap():

    def __init__(self,data,seed=None) -> None:

        # Initilisation d'un générateur aléatoire
        self.rnd = np.random.default_rng(seed)

        self.data=data

    def generate(self,nb):

        self.series = self.rnd.choice(self.data,(nb,len(self.data)),True)
        for i in range(nb):
            self.series[i,:].sort()

if __name__=='__main__':

    mydata = np.arange(10)
    my = Bootstrap(mydata)
    my.generate(100)

    pass


