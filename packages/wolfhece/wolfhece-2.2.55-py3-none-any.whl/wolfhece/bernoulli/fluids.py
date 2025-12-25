"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from enum import Enum

class Water():

    rho:float = 1000.
    mu:float  = 1e-3

    @property
    def nu(self) -> float:
        return self.mu / self.rho