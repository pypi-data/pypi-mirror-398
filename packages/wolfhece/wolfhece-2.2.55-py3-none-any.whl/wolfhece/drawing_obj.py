"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from wx import App
import logging

from .PyTranslate import _

class Element_To_Draw:
    """
    Base class of element to add into WolfMapViewer or another GUI
    """

    def __init__(self, idx:str = '', plotted:bool = True, mapviewer = None, need_for_wx:bool = False) -> None:
        """
        Constructor of the class

        :param idx: identifier
        :param plotted: boolean if plotting action must be processed
        :param mapviewer: WolfMapViewer instance attached to the object
        :param need_for_wx: test if wx App is running. If not, raise an error

        """

        self.idx = idx  # identifier
        self.xmin=0.    # spatial extension - lower left corner X
        self.ymin=0.    # spatial extension - lower left corner Y
        self.xmax=0.    # spatial extension - upper right corner X
        self.ymax=0.    # spatial extension - upper right corner Y

        self.plotted = plotted  # boolean if plotting action must be processed
        self.plotting = False   # plotting operations are underway

        self.mapviewer = mapviewer  # WolfMapViewer instance attached to the object
        self.wx_exists = App.Get() is not None  # test if wx App is running

        # *********************************
        # For specific objects
        self._filename_vector:str = ''
        self._filename_points:str = ''
        # *********************************

        if need_for_wx and (not self.wx_exists):
            raise NameError(_('wx App is not running or you need it --> check your code and retry !'))

    #FIXME : checked and plotted are the same thing ?? -- YES but conserve for retro-compatibility
    @property
    def checked(self) -> bool:
        """
        Return the checked status.
        """
        return self.plotted

    @checked.setter
    def checked(self, value:bool) -> None:
        """
        Set the checked status.
        """
        self.plotted = value

    def get_mapviewer(self):
        """
        Return the mapviewer
        """
        return self.mapviewer

    def set_mapviewer(self, newmapviewer = None):
        """
        Attach a (new) mapviewer to the object
        """
        self.mapviewer = newmapviewer

    def check_plot(self):
        """
        Generic function responding to check operation from mapviewer
        """
        self.plotted = True

    def uncheck_plot(self, unload:bool = True):
        """
        Generic function responding to uncheck operation from mapviewer
        """
        self.plotted = False

    def show_properties(self):
        """
        Generic function to show properties of the object
        """
        logging.warning('No properties to show for this object !')
        pass

    def hide_properties(self):
        """
        Generic function to hide properties of the object
        """
        logging.warning('No properties to hide for this object !')
        pass

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot data in OpenGL context
        """
        if self.plotted:

            self.plotting = True

            # do something in OpenGL...

            self.plotting = False

    def find_minmax(self, update=False):
        """
        Generic function to find min and max spatial extent in data

        example : a WolfMapViewer instance needs spatial extent to zoom or test if
                  element must be plotted
        """

        self.xmin=0.    # spatial extension - lower left corner X
        self.ymin=0.    # spatial extension - lower left corner Y
        self.xmax=0.    # spatial extension - upper right corner X
        self.ymax=0.    # spatial extension - upper right corner Y

        pass

    @property
    def has_OGLContext(self):
        """
        Test if the object has a canvas
        """
        if self.mapviewer is None:
            return False

        return self.mapviewer.SetCurrentContext()

    def reset_listogl(self):
        """
        Reset the OpenGL list of the object
        """

        pass