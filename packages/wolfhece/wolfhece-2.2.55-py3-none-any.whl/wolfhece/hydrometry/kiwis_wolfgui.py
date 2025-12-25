"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
import logging

from ..drawing_obj import Element_To_Draw

try:
    # Trying to import the hydrometry_hece module from the hydrometry_hece package
    # containing the KEY access to the SPW server
    from ..hydrometry_hece.kiwis_hece import hydrometry_hece as hydrometry
except:
    # If the hydrometry_hece module is not found, we import the hydrometry module from the hydrometry package
    from .kiwis import hydrometry

from .kiwis_gui import hydrometry_gui
from ..PyVertex import cloud_vertices, wolfvertex, Cloud_Styles, getIfromRGB, getRGBfromI

class hydrometry_wolfgui(Element_To_Draw):

    def __init__(self, idx:str = '', plotted:bool = True, mapviewer = None, need_for_wx:bool = False, dir:str = '', **kwargs) -> None:
        """
        Constructor of the class

        :param idx: identifier
        :param plotted: boolean if plotting action must be processed
        :param mapviewer: WolfMapViewer instance attached to the object
        :param need_for_wx: test if wx App is running. If not, raise an error

        """
        Element_To_Draw.__init__(self, idx, plotted, mapviewer, need_for_wx)

        self.hydrometry = hydrometry(dir=dir)
        self.cloud_stations_real = cloud_vertices(idx = 'real stations', mapviewer = mapviewer)

        self.cloud_stations_real.myprop.style = Cloud_Styles.CIRCLE.value
        self.cloud_stations_real.myprop.width = 10
        self.cloud_stations_real.myprop.color = getIfromRGB([0,0,255])
        self.cloud_stations_real.myprop.filled = True
        self.cloud_stations_real.myprop.legendvisible = True
        self.cloud_stations_real.myprop.legendfontsize = 12
        self.cloud_stations_real.myprop.legendrelpos = 8

        self._init_cloud()

        self.find_minmax(True)

        self.gui_hydrometry = None

    def _init_cloud(self):
        """
        Initialize the cloud of stations
        """
        real = self.hydrometry.get_names_xy()

        real_dict = {}

        for i in range(len(real[0])):
            if not np.isnan(real[1][i]) and not np.isnan(real[2][i]):
                real_dict[real[0][i]] = {'vertex' : wolfvertex(real[1][i], real[2][i])}
            else:
                logging.debug(f'Real station {real[0][i]} has no coordinates')
        self.cloud_stations_real.add_vertex(cloud = real_dict)

    def show_properties(self):
        """
        Show the properties of the object
        """
        if self.gui_hydrometry is None:
            self.gui_hydrometry = hydrometry_gui(self.hydrometry.credential, dir = self.hydrometry.dir)
        else:
            try:
                self.gui_hydrometry.Show()
            except:
                self.gui_hydrometry = hydrometry_gui(self.hydrometry.credential, dir = self.hydrometry.dir)

        self.cloud_stations_real.show_properties()

    def plot(self, **kwargs):
        """
        Plot the object
        """

        self.cloud_stations_real.plot(**kwargs)

    def plot_legend(self, **kwargs):
        """
        Plot the legend of the object
        """
        self.cloud_stations_real.plot_legend(**kwargs)

    def find_minmax(self, update=False):
        """
        Find the minimum and maximum values of the object
        """
        if update:
            real = self.hydrometry.get_names_xy()

            if len(real[0]) > 0:
                x_real = real[1][np.isnan(real[1]) == False]
                y_real = real[2][np.isnan(real[2]) == False]

                self.xmin = np.min(x_real)
                self.ymin = np.min(y_real)
                self.xmax = np.max(x_real)
                self.ymax = np.max(y_real)