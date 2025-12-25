
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely import prepare, is_prepared, destroy_prepared

import wx
import logging
from tqdm import tqdm

from .PyTranslate import _
from .PyVertexvectors import Zones, zone, vector, wolfvertex
from .matplotlib_fig import Matplotlib_Figure as mpl_plot, Matplotlib_ax_properties as mpl_ax, Matplolib_line_properties as mpl_line, Matplotlib_figure_properties as mpl_fig
from .matplotlib_fig import PRESET_LAYOUTS
from .wolf_array import WolfArray
from .wolfresults_2D import Wolfresults_2D
from .Results2DGPU import wolfres2DGPU

class Compare_vectors():
    """ Compare multiple vectors """

    def __init__(self) -> None:

        self.fig:mpl_plot = None

        self._reference:vector = None
        self._reference_ls:LineString = None
        self._ref_s:np.ndarray = None
        self._ref_obj:dict[str, WolfArray | wolfres2DGPU | Wolfresults_2D] = {}
        self._ref_values:zone = None

        self._to_compare:dict[vector, list[WolfArray | wolfres2DGPU | Wolfresults_2D]] = {}
        self._compare_values:dict[vector, zone] = {}

    @property
    def layout(self):
        """ Layout of the figure """
        return self.fig.layout

    @layout.setter
    def layout(self, value:dict | tuple | list | str):
        """ Set layout of the figure """
        self.fig = mpl_plot(value)
        self.fig.Show()

    @property
    def reference(self):
        """ Reference vector """
        return self._reference

    @reference.setter
    def reference(self, value:vector):
        """ Set reference vector """
        if not isinstance(value, vector):
            logging.error(_('Reference must be a vector'))
            return

        self._reference = value
        self._reference_ls = value.asshapely_ls()
        prepare(self._reference_ls)
        self._ref_s = self._reference.get_s2d()

    def __del__(self):
        """ Destructor """

        if self._reference_ls is not None:
            if is_prepared(self._reference_ls):
                destroy_prepared(self._reference_ls)

    def add_ref_values(self, values:WolfArray | wolfres2DGPU | Wolfresults_2D):
        """ Add values to the reference vector """

        self._ref_obj[values.idx] = values

    def del_ref_values(self, which:int | str):
        """ Pop values from the reference vector """

        if isinstance(which, str):
            if which in self._ref_obj:
                self._ref_obj.pop(which)
        elif isinstance(which, int):
            if which < len(self._ref_obj):
                self._ref_obj.pop(list(self._ref_obj.keys())[which])

    def reset_ref_values(self):
        """ Reset reference values """

        self._ref_obj = {}

    def get_ref_values(self):
        """ Retrieve reference values """

        self._ref_values = self.reference.get_values_linked(self._ref_obj)

    def add_compare(self, support:vector, values:list[WolfArray | wolfres2DGPU | Wolfresults_2D] = None):
        """ Add values to compare """

        if not isinstance(support, vector):
            logging.error(_('Support must be a vector'))
            return

        if values is not None:
            if not isinstance(values, list):
                values = [values]

            if isinstance(values, list):
                if not all(isinstance(x, WolfArray | wolfres2DGPU | Wolfresults_2D) for x in values):
                    logging.error(_('Values must be a list of WolfArray, Wolfresults_2D or Wolfres2DGPU'))
                    return

        if support in self._to_compare:
            self._to_compare[support] += values
        else:
            self._to_compare[support] = values

    def reset_compare(self):
        """ Reset comparison values """

        self._to_compare = {}

    def del_compare(self, which:int | str):
        """ Pop values from the comparison vector """

        if isinstance(which, str):
            if which in self._to_compare:
                self._to_compare.pop(which)
        elif isinstance(which, int):
            if which < len(self._to_compare):
                self._to_compare.pop(list(self._to_compare.keys())[which])

    def get_compare_values(self):
        """ Retrieve comparison values """

        for curvect in self._to_compare:
            self._compare_values[curvect] = curvect.get_values_linked({cur.idx: cur for cur in self._to_compare[curvect]})

    def plot_ref(self, axis:int = 0):
        """ Plot reference vector """

        if self.fig is None:
            logging.error(_('No figure layout defined'))
            return

        for curvect in self._ref_values.myvectors:
            xyz = curvect.asnparray3d()
            x = [self._reference_ls.project(Point(x,y)) for x,y in xyz[:,0:2]]
            y = xyz[:,2]

            self.fig.plot(x=x, y=y, ax=axis, label=curvect.myname)

    def plot_compare(self, axis:int = 0):
        """ Plot comparison vectors along reference vector.

        We must project comparison vectors on the reference vector and plot them.
        """

        if self.fig is None:
            logging.error(_('No figure layout defined'))
            return

        for curvect in self._compare_values:
            for curval in self._compare_values[curvect].myvectors:
                xyz = curval.asnparray3d()
                x = [self._reference_ls.project(Point(x,y)) for x,y in xyz[:,0:2]]
                y = xyz[:,2]

                self.fig.plot(x=x, y=y, ax=axis, label=curval.myname)

    def set_x_bounds(self, smin:float, smax:float, axis:int = 0):
        """ Set x bounds for the figure """

        self.fig.set_x_bounds(smin, smax, axis)

    def set_y_bounds(self, ymin:float, ymax:float, axis:int = 0):
        """ Set y bounds for the figure """

        self.fig.set_y_bounds(ymin, ymax, axis)