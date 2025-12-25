"""
Author: HECE - University of Liege, Pierre Archambeau, Utashi Ciraane Docile
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

# Libraries
import copy
import enum
import numpy as np
import os
import pandas as pd
import warnings
import matplotlib.pyplot as plt

from datetime import datetime, timedelta
from matplotlib.ticker import MultipleLocator
from matplotlib import animation ,rcParams
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from typing import Literal,Union
from tqdm import tqdm

from .PyVertexvectors import Zones, zone, vector, wolfvertex


class Constants(enum.Enum):
    """
    Contain the constants used throughout
    the module.
    """
    SEPARATOR = '\t'


class Hydrograph(pd.Series):
    '''
    A pandas series containing discharges (values)
    with their respective times of observation (indices).

    @ The class is inherited which means
    all series method are available in this
    class escorted by a few other functions useful in
    the interaction with wolfhece tools.

    '''

    def __init__(self,
                 data=None,
                 index=None,
                 dtype=None,
                 name='Discharge',
                 copy=None,
                 file_path:str ='') -> None:
        if file_path != '':
            data =self.read_from_wolf_file(file_path)
        elif isinstance(data, str):
            data = self.read_from_wolf_file(data)

        super().__init__(data,index,dtype, name, copy)

    def write_as_wolf_file(self,
                           file_path:str,
                           writing_method: Literal['continuous', 'stepwise'] = 'continuous',
                           epsilon:float = 1.
                           ):
        """
        Write the hydrograph on the infiltration format
        of wolf models -> infil[n].tv file.
        """
        lgth = self.size
        if writing_method == 'continuous':
            with open(file_path, 'w') as wolf_file:
                wolf_file.write(f'{lgth}\n')
                for i in range(lgth):
                    wolf_file.write(f'{self.index[i]}{Constants.SEPARATOR.value}{self.values[i]}\n')

        elif writing_method == 'stepwise':
            with open(file_path, 'w') as wolf_file:
                wolf_file.write(f'{2*lgth -1}\n')
                wolf_file.write(f'{self.index[0]}{Constants.SEPARATOR.value}{self.values[0]}\n')
                for a in range(lgth - 1):
                    i = a + 1
                    wolf_file.write(f'{self.index[i] - epsilon}{Constants.SEPARATOR.value}{self.values[i-1]}\n')
                    wolf_file.write(f'{self.index[i]}{Constants.SEPARATOR.value}{self.values[i]}\n')

    def read_from_wolf_file(self,
                            file_path:str,
                            separator: Literal[',',';', '\t'] = Constants.SEPARATOR.value
                            ) -> dict:
        """
        Read a wolf file at the format infil[n].tv and
        return its data as a dictionnary where:
         - keys are times and,
         - values are discharges.

        """
        data = {}
        with open(file_path,'r') as wolf_file:
            for line in wolf_file.readlines()[1:]:
                observation = line.splitlines()[0].split(separator)
                data[float(observation[0])] = float(observation[1])
        return data

    # FIXME right convert to second method
