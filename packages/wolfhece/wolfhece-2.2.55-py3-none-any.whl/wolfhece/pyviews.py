"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import logging

from .drawing_obj import Element_To_Draw
from .wolf_array import WolfArray, WolfArrayMB, VERSION_RGB
from .PyPalette import wolfpalette
from .PyParams import Wolf_Param, key_Param, Type_Param


class WolfViews(Element_To_Draw):
    """ Class to permit complex views, combination of
    different objects which can be plotted.

    Inherits from Element_To_Draw."""

    def __init__(self, idx: str = '', plotted: bool = True, mapviewer=None, need_for_wx: bool = False) -> None:
        """ Constructor of the class WolfViews."""

        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self.view = [] # list of elements to plot
        self.pals = [] # list of palettes to use for the elements
        self.fix  = [] # list of boolean to fix some elements - avoid to delete OpenGL lists during "delete_lists"

    def delete_lists(self):
        """ Delete the lists of elements and palettes."""

        for cur, fix in zip(self.view, self.fix):
            if not fix:
                if isinstance(cur, WolfArray) or isinstance(cur, WolfArrayMB):
                    cur.delete_lists()

    def read_from_file(self, fn):
        myproject = Wolf_Param(None, filename=fn, toShow=False)

        mykeys = ['cross_sections', 'vector', 'array']

        # with wx.BusyInfo(_('Opening project')):
        #     wait = wx.BusyCursor()

        #     if 'cross_sections' in myproject.myparams.keys():
        #         for curid, curname in zip(myproject.myparams['cross_sections'].keys(),
        #                                 myproject.myparams['cross_sections'].values()):
        #             if curid != 'format' and curid != 'dirlaz':
        #                 mycs = crosssections(curname[key_Param.VALUE],
        #                                     format=myproject.myparams['cross_sections']['format'][key_Param.VALUE],
        #                                     dirlaz=myproject.myparams['cross_sections']['dirlaz'][key_Param.VALUE])

        #                 self.add_object('cross_sections', newobj=mycs, id=curid)

        #     if 'vector' in myproject.myparams.keys():
        #         for curid, curname in zip(myproject.myparams['vector'].keys(), myproject.myparams['vector'].values()):
        #             if exists(curname[key_Param.VALUE]):
        #                 myvec = Zones(curname[key_Param.VALUE])
        #                 self.add_object('vector', newobj=myvec, id=curid)
        #             else:
        #                 wx.LogMessage(_('Bad parameter in project file - vector : ')+ curname[key_Param.VALUE])

        #     if 'array' in myproject.myparams.keys():
        #         for curid, curname in zip(myproject.myparams['array'].keys(), myproject.myparams['array'].values()):

        #             if exists(curname[key_Param.VALUE]):
        #                 curarray = WolfArray(curname[key_Param.VALUE])
        #                 self.add_object('array', newobj=curarray, id=curid)
        #             else:
        #                 wx.LogMessage(_('Bad parameter in project file - array : ')+ curname[key_Param.VALUE])

        #     if 'wolf2d' in myproject.myparams.keys():
        #         for curid, curname in zip(myproject.myparams['wolf2d'].keys(), myproject.myparams['wolf2d'].values()):
        #             if exists(curname[key_Param.VALUE]):
        #                 curwolf = Wolfresults_2D(curname[key_Param.VALUE])
        #                 self.add_object('res2d', newobj=curwolf, id=curid)
        #             else:
        #                 wx.LogMessage(_('Bad parameter in project file - wolf2d : ')+ curname[key_Param.VALUE])

        #         self.menu_wolf2d()

        #     if 'palette' in myproject.myparams.keys():
        #         self.project_pal = {}
        #         for curid, curname in zip(myproject.myparams['palette'].keys(), myproject.myparams['palette'].values()):
        #             if exists(curname[key_Param.VALUE]):
        #                 mypal = wolfpalette(None, '')
        #                 mypal.readfile(curname[key_Param.VALUE])
        #                 mypal.automatic = False

        #                 self.project_pal[curid] = mypal
        #             else:
        #                 wx.LogMessage(_('Bad parameter in project file - palette : ')+ curname[key_Param.VALUE])

        #     if 'palette-array' in myproject.myparams.keys():
        #         curarray: WolfArray
        #         if self.project_pal is not None:
        #             for curid, curname in zip(myproject.myparams['palette-array'].keys(),
        #                                     myproject.myparams['palette-array'].values()):
        #                 if curname[key_Param.VALUE] in self.project_pal.keys():
        #                     curarray = self.getobj(curid)
        #                     if curarray is not None:
        #                         mypal:wolfpalette
        #                         mypal = self.project_pal[curname[key_Param.VALUE]]
        #                         curarray.mypal = mypal
        #                         if mypal.automatic:
        #                             curarray.myops.palauto.SetValue(1)
        #                         else:
        #                             curarray.myops.palauto.SetValue(0)
        #                         curarray.updatepalette(0)
        #                         curarray.delete_lists()
        #                     else:
        #                         wx.LogWarning(_('Bad parameter in project file - palette-array : ')+ curid)

        #     if 'cross_sections_link' in myproject.myparams.keys():
        #         if 'linkzones' in myproject.myparams['cross_sections_link'].keys():
        #             idx = myproject.myparams['cross_sections_link']['linkzones'][key_Param.VALUE]

        #             for curvect in self.added['vectors']:
        #                 myzones: Zones
        #                 myzones = self.added['vectors'][curvect]['values']
        #                 if myzones.idx == idx:
        #                     self.active_cs.link_external_zones(myzones)

        #             zonename = ''
        #             vecname = ''

        #             if 'sortzone' in myproject.myparams['cross_sections_link'].keys():
        #                 zonename = myproject.myparams['cross_sections_link']['sortzone'][key_Param.VALUE]
        #             if 'sortname' in myproject.myparams['cross_sections_link'].keys():
        #                 vecname = myproject.myparams['cross_sections_link']['sortname'][key_Param.VALUE]

        #             if zonename != '' and vecname != '':
        #                 names = [cur.myname for cur in myzones.myzones]
        #                 idx = names.index(zonename)
        #                 curzone = myzones.myzones[idx]
        #                 names = [cur.myname for cur in curzone.myvectors]
        #                 idx = names.index(vecname)
        #                 curvec = curzone.myvectors[idx]

        #                 if curvec is not None:
        #                     curvec: vector
        #                     self.active_cs.sort_along(curvec.asshapely_ls(), curvec.myname, False)

        #     if 'vector_array_link' in myproject.myparams.keys():
        #         for curid, curname in zip(myproject.myparams['vector_array_link'].keys(), myproject.myparams['vector_array_link'].values()):

        #             locvec = None
        #             locarray = None
        #             for curvec in self.myvectors:
        #                 if curvec.idx == curname[key_Param.VALUE].lower():
        #                     locvec=curvec
        #                     break

        #             for curarray in self.myarrays:
        #                 if curarray.idx == curid.lower():
        #                     locarray=curarray
        #                     break

        #             if locvec is not None and locarray is not None:

        #                 locarray.linkedvec = locvec.myzones[0].myvectors[0]

        #             else:

        #                 wx.LogWarning(_('Bad vec-array association in project file !'))
        #                 wx.LogWarning(curid)
        #                 wx.LogWarning(curname[key_Param.VALUE])
        #     del wait

    def change_gui(self, newmapviewer):
        """ Change the mapviewer of the view and all its elements."""

        self.mapviewer = newmapviewer

        for cur in self.view:
            if isinstance(cur, WolfArray) or isinstance(cur, WolfArrayMB):
                cur.change_gui(newmapviewer)
            else:
                cur.mapviewer = newmapviewer

    def add_elemt(self, added_elemt, pal= None, fix= False):
        """ Add an element to the view.

        :param added_elemt: Element to add.
        :param pal: Palette to use for the element.
        """

        assert isinstance(added_elemt, Element_To_Draw), 'The element to add must be a subclass of Element_To_Draw'

        self.view.append(added_elemt)
        self.pals.append(pal)
        self.fix.append(fix)

    def add_elemts(self, added_elemts: list, pals=None, fixes=None):
        """ Add a list of elements to the view.

        :param added_elemts: List of elements to add.
        :param pals: List of palettes to use for the elements.
        """

        for cur in added_elemts:
            assert isinstance(cur, Element_To_Draw), 'The element to add must be a subclass of Element_To_Draw'

        self.view += added_elemts

        if pals is None:
            self.pals += [None]*len(added_elemts)
        else:
            if len(pals) != len(added_elemts):
                logging.warning('The number of palettes must be the same as the number of elements.')

                if len(pals) < len(added_elemts):
                    logging.warning('The missing palettes will be set to None.')
                    pals += [None]*(len(added_elemts)-len(pals))
                else:
                    logging.warning('The extra palettes will be ignored.')
                    pals = pals[:len(added_elemts)]

            self.pals += pals

        if fixes is None:
            self.fix += [False]*len(added_elemts)
        else:
            if len(fixes) != len(added_elemts):
                logging.warning('The number of fixes must be the same as the number of elements.')

                if len(fixes) < len(added_elemts):
                    logging.warning('The missing fixes will be set to None.')
                    fixes += [False]*(len(added_elemts)-len(fixes))
                else:
                    logging.warning('The extra fixes will be ignored.')
                    fixes = fixes[:len(added_elemts)]

            self.fix += fixes

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """ Plot the view. """

        if self.plotted:

            for cur, pal in zip(self.view, self.pals):
                # iterate over the elements and their palettes
                pal: wolfpalette

                oldplotted = cur.plotted
                cur.plotted = True

                if isinstance(cur, WolfArray):
                    #
                    if VERSION_RGB == 1:
                        # Will be deprecated in future versions
                        if cur.rgb is None:
                            if pal is not None:
                                cur.rgb = pal.get_rgba(cur.array)
                            else:
                                cur.mypal.defaultgray_minmax(cur.array)
                                cur.rgb = cur.mypal.get_rgba(cur.array)
                        cur.plot(sx, sy, xmin, ymin, xmax, ymax)
                    elif VERSION_RGB in [2,3]:
                        if pal is None:
                            # using the current palette
                            cur.plot(sx, sy, xmin, ymin, xmax, ymax)
                        else:
                            # using the palette passed as argument

                            # memorize the current palette
                            oldpal = cur.mypal
                            # change the palette
                            cur.mypal = pal
                            # plot the array
                            cur.plot(sx, sy, xmin, ymin, xmax, ymax)
                            # restore the palette
                            cur.mypal = oldpal

                else:
                    cur.plot(sx, sy, xmin, ymin, xmax, ymax)

                cur.plotted = oldplotted

    def find_minmax(self):
        """ Find the spatial bounds of the view."""

        xmin = 1.e30
        ymin = 1.e30
        xmax = -1.e30
        ymax = -1.e30

        for cur in self.view:
            if isinstance(cur, WolfArray) or isinstance(cur, WolfArrayMB):
                x, y = cur.get_bounds()
                xmin = min(x[0], xmin)
                xmax = max(x[1], xmax)
                ymin = min(y[0], ymin)
                ymax = max(y[1], ymax)

        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
