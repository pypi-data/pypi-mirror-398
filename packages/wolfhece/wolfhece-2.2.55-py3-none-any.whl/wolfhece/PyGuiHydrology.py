"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
from pathlib import Path

from .PyTranslate import _
from .PyDraw import WolfMapViewer, draw_type
from .RatingCurve import *
from .PyVertexvectors import vector, Zones, zone, getIfromRGB, getRGBfromI, wolfvertex as wv
from .wolf_array import WolfArray

import logging


class selectpoint(wx.Dialog):

    def __init__(self, parent=None, title="Default Title", w=500, h=200, SPWstations: SPWMIGaugingStations = None,
                 DCENNstations: SPWDCENNGaugingStations = None):
        wx.Dialog.__init__(self, parent, title=title, size=(w, h), style=wx.DEFAULT_DIALOG_STYLE)

        self.SPWMI = SPWstations
        self.SPWDCENN = DCENNstations

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerv = wx.BoxSizer(wx.VERTICAL)

        self.buttonOK = wx.Button(self, label="OK")
        self.buttonOK.Bind(wx.EVT_BUTTON, self.Apply)

        lblList = [_('Coordinates'), _('Code station'), _('River/Name')]
        self.rbox = wx.RadioBox(self, label='Which', choices=lblList, majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        self.rbox.Bind(wx.EVT_RADIOBOX, self.onRadioBox)

        x_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tcoordx = wx.StaticText(self, label="X: ")
        self.coordx = wx.TextCtrl(self, value=_("X coordinate"), size=(140, -1), style=wx.TE_CENTER)
        x_sizer.Add(self.tcoordx, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        x_sizer.Add(self.coordx, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        y_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tcoordy = wx.StaticText(self, label="Y: ")
        self.coordy = wx.TextCtrl(self, value=_("Y coordinate"), size=(140, -1), style=wx.TE_CENTER)
        y_sizer.Add(self.tcoordy, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        y_sizer.Add(self.coordy, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.coords = [self.tcoordx, self.coordx, self.tcoordy, self.coordy]

        mycodes = [str(x) for x, val in SPWstations.mystations.items() if val.x !=0. and val.y != 0.] + [str(x) for x, val in DCENNstations.mystations.items() if val.x !=0. and val.y != 0.]
        # Sort codes alphabetically
        mycodes.sort()

        myrivers = [*list(SPWstations.myrivers.keys()), *list(DCENNstations.myrivers.keys())]
        # Sort rivers alphabetically
        myrivers.sort()

        station_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tcodestation = wx.StaticText(self, label=_("Code station: "))
        self.codestation = wx.ComboBox(self, size=(95, -1), choices=mycodes, style=wx.CB_DROPDOWN)
        station_sizer.Add(self.tcodestation, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        station_sizer.Add(self.codestation, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.codes = [self.tcodestation, self.codestation]

        river_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.triverstation = wx.StaticText(self, label=_("River: "))
        self.riverstation = wx.ComboBox(self, size=(95, -1), choices=myrivers, style=wx.CB_DROPDOWN | wx.CB_SORT)
        river_sizer.Add(self.triverstation, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        river_sizer.Add(self.riverstation, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tnamestation = wx.StaticText(self, label=_("Station name: "))
        self.namestation = wx.ComboBox(self, size=(95, -1), choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT)
        name_sizer.Add(self.tnamestation, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        name_sizer.Add(self.namestation, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.riverstation.Bind(wx.EVT_COMBOBOX, self.onComboRiver)

        self.riversname = [self.tnamestation, self.namestation, self.triverstation, self.riverstation]

        self.sizerv.Add(self.rbox, 0, wx.EXPAND)

        self.sizerv.Add(x_sizer, 1, wx.EXPAND)
        self.sizerv.Add(y_sizer, 1, wx.EXPAND)
        self.sizerv.Add(station_sizer, 1, wx.EXPAND)
        self.sizerv.Add(river_sizer, 1, wx.EXPAND)
        self.sizerv.Add(name_sizer, 1, wx.EXPAND)

        for item in self.codes:
            item.Hide()
        for item in self.riversname:
            item.Hide()

        self.sizer.Add(self.sizerv, 1, wx.EXPAND)
        self.sizer.Add(self.buttonOK, 0, wx.EXPAND)

        # ajout du sizer à la page
        self.SetSizer(self.sizer)
        # self.SetSize(w,h)
        self.SetAutoLayout(1)

        # affichage de la page
        self.Show(True)

    def Apply(self, event):
        self.Hide()

    def onComboRiver(self, evt):
        str = self.riverstation.GetStringSelection()

        namestation = []
        if str in self.SPWMI.myrivers.keys():
            namestation += list(self.SPWMI.myrivers[str].keys())
        if str in self.SPWDCENN.myrivers.keys():
            namestation += list(self.SPWDCENN.myrivers[str].keys())

        self.namestation.SetItems(namestation)

        pass

    def onRadioBox(self, evt):
        """ Switch between the different options in the radio box """

        str = self.rbox.GetStringSelection()

        if str == _('Coordinates'):
            for item in self.coords:
                item.Show()
            for item in self.codes:
                item.Hide()
            for item in self.riversname:
                item.Hide()
        elif str == _('Code station'):
            for item in self.coords:
                item.Hide()
            for item in self.codes:
                item.Show()
            for item in self.riversname:
                item.Hide()
        elif str == _('River/Name'):
            for item in self.coords:
                item.Hide()
            for item in self.codes:
                item.Hide()
            for item in self.riversname:
                item.Show()

        self.sizerv.Layout()


class GuiHydrology(WolfMapViewer):
    """ Mapviewer of the hydrology model -- see HydrologyModel in PyGui.py """

    def __init__(self, parent=None, title='WOLF Hydrological model - viewer', w=500, h=500, treewidth=200, wolfparent=None, wxlogging=None):
        """ Constructor

        :param parent: parent window - wx.Frame
        :param title: title of the window - str
        :param w: width of the window - int
        :param h: height of the window - int
        :param treewidth: width of the tree - int
        :param wolfparent: wolf parent instance -- PyGui.HydrologyModel
        :type wolfparent: HydrologyModel
        :param wxlogging: logging instance -- PyGui.WolfLog
        """

        super(GuiHydrology, self).__init__(parent, title=title, w=w, h=h,
                                           treewidth=treewidth,
                                           wolfparent=wolfparent,
                                           wxlogging=wxlogging)

        from .PyGui import HydrologyModel

        self.wolfparent:HydrologyModel

        # self.filemenu.Insert(0, wx.ID_ANY, _('New from scratch'), _('Create a new simulation from scratch...'))

        self._hydrol_modelmenu = wx.Menu()
        self.menubar.Append(self._hydrol_modelmenu, _('&Hydrological model'))

        self._wizard = self._hydrol_modelmenu.Append(wx.ID_ANY, _('Wizard'), _('Wizard for hydrological model'))

        self._dtm_menu = wx.Menu()
        self._prepro_menu = wx.Menu()
        self._outlet_menu = wx.Menu()
        self._ip_menu = wx.Menu()

        self._forced_exchanges_menu = wx.Menu()

        self._prepro_menu.Append(wx.ID_ANY, _('Outlet...'), self._outlet_menu)
        self._prepro_menu.Append(wx.ID_ANY, _('Interior points...'), self._ip_menu)
        self._prepro_menu.Append(wx.ID_ANY, _('Forced exchanges...'), self._forced_exchanges_menu)

        self._params_menu = wx.Menu()

        self._toolsmenu = wx.Menu()

        self._hydrol_modelmenu.Append(wx.ID_ANY, _('DTM...'), self._dtm_menu)
        self._hydrol_modelmenu.Append(wx.ID_ANY, _('Preprocessing...'), self._prepro_menu)
        self._hydrol_modelmenu.Append(wx.ID_ANY, _('Parameters...'), self._params_menu)
        self._hydrol_modelmenu.Append(wx.ID_ANY, _('Tools...'), self._toolsmenu)

        # DTM, outlet, interior points, parameters, preprocessing

        self._dtm_menu.Append(wx.ID_ANY, _('Use active array as DTM'), _('Set the active array as DTM'))
        self._dtm_menu.Append(wx.ID_ANY, _('Crop active array on zoom'), _('Crop the active array on the current zoom and use it as DTM'))
        self._dtm_menu.Append(wx.ID_ANY, _('Crop active array using active vector'), _('Crop the active array based on the active vector and use it as DTM'))

        # self._outlet_menu.Append(wx.ID_ANY, _('Choose outlet'), _('Outlet - local or general - from database'))
        self._outlet_menu.Append(wx.ID_ANY, _('Pick outlet'), _('Outlet - local or general - by mouse'))
        self._outlet_menu.Append(wx.ID_ANY, _('Convert selection'), _('Outlet - local or general - by mouse'))

        # self._ip_menu.Append(wx.ID_ANY, _('Choose interior point'), _('Interior point - local or general - from database'))
        self._ip_menu.Append(wx.ID_ANY, _('Pick interior point'), _('Interior point - local or general - by mouse'))
        self._ip_menu.Append(wx.ID_ANY, _('Convert selections'), _('Interior point - local or general - by mouse'))
        self._ip_menu.Append(wx.ID_ANY, _('Edit points'), _('Edit interior points...'))

        self._params_menu.Append(wx.ID_ANY, _('Main model'), _('General parameters'))
        self._params_menu.Append(wx.ID_ANY, _('Basin'), _('Basin parameters'))
        self._params_menu.Append(wx.ID_ANY, _('Subbasins'), _('Sub-Basin parameters'))

        self._prepro_menu.Append(wx.ID_ANY, _('Run preprocessing'), _('Run the preprocessing of the hydrology model'))
        # self._prepro_menu.Append(wx.ID_ANY, _('Topology'), _('Show the topology inside the active vector'))

        # Forced exchanges menu

        self._forced_exchanges_menu.Append(wx.ID_ANY, _('Pick Forced exchanges'), _('Manage the forced exchanges...'))
        self._forced_exchanges_menu.Append(wx.ID_ANY, _('Convert selection to Forced exchanges'), _('Convert selection to Forced exchanges...'))
        self._forced_exchanges_menu.AppendSeparator()
        self._forced_exchanges_menu.Append(wx.ID_ANY, _('Remove Forced exchanges'), _('Remove Forced exchanges...'))
        self._forced_exchanges_menu.Append(wx.ID_ANY, _('Remove Forced exchanges inside vector'), _('Remove Forced exchanges...'))
        # self._forced_exchanges_menu.AppendSeparator()
        # self._forced_exchanges_menu.Append(wx.ID_ANY, _('Edit Forced exchanges'), _('Edit Forced exchanges...'))

        # self._toolsmenu.Append(wx.ID_ANY, _('Crop MNT/MNS'), _('Cropping data...'))
        # self._toolsmenu.Append(wx.ID_ANY, _('Crop land use (COSW)'), _('Cropping data...'))
        # self._toolsmenu.Append(wx.ID_ANY, _('Analyze slope'), _('Slope analyzer...'))
        # self._toolsmenu.Append(wx.ID_ANY, _('IRM - QDF'), _('Manage data...'))

        # self._toolsmenu.AppendSeparator()

        self._toolsmenu.Append(wx.ID_ANY, _('Find upstream watershed'), _('Find upstream watershed based on click...'))
        self._toolsmenu.Append(wx.ID_ANY, _('Find upstream watershed - limit to sub'), _('Find upstream watershed based on click but limit to subbasin...'))

        self._toolsmenu.AppendSeparator()

        self._toolsmenu.Append(wx.ID_ANY, _('Select upstream watershed'), _('Select upstream watershed based on click...'))
        self._toolsmenu.Append(wx.ID_ANY, _('Select upstream watershed - limit to sub'), _('Select upstream watershed based on click but limit to subbasin...'))
        self._toolsmenu.Append(wx.ID_ANY, _('Select upstream rivers'), _('Select upstream rivers based on click...'))
        self._toolsmenu.Append(wx.ID_ANY, _('Select upstream rivers - limit to sub'), _('Select upstream rivers based on click but limit to subbasin...'))
        self._toolsmenu.Append(wx.ID_ANY, _('Select downstream rivers'), _('Select downstream rivers based on click...'))

        self._toolsmenu.AppendSeparator()

        self._toolsmenu.Append(wx.ID_ANY, _('Find Path to outlet'), _('Find path to outlet based on click...'))

        # self.computemenu = wx.Menu()
        # paramgen = self.computemenu.Append(1300,_('Calibration/Optimisation'),_('Parameters calibration of the model'))
        # paramgen = self.computemenu.Append(1301,_('Run'),_('Run simulation !'))
        # self.menubar.Append(self.computemenu,_('&Computation'))

        # self.resultsmenu = wx.Menu()
        # paramgen = self.resultsmenu.Append(1400,_('Assemble'),_('Run postprocessing !'))
        # paramgen = self.resultsmenu.Append(1401,_('Plot'),_('Plot'))
        # self.menubar.Append(self.resultsmenu,_('&Results'))

        self._tmp_vector_exchanges = vector(name='Temporary forced exchanges vector')

    @property
    def watershed(self):

        if self.wolfparent is None:
            return None

        if self.wolfparent.mycatchment is None:
            return None

        return self.wolfparent.mycatchment.charact_watrshd

    @property
    def header(self):
        """ Return the header of the watershed """

        if self.wolfparent is None:
            return None

        return self.wolfparent.header

    def _choose_outlet(self):
        """ Choose the outlet of the watershed """

        myselect = selectpoint(title=_('Outlet'),
                                SPWstations=self.wolfparent.SPWstations,
                                DCENNstations=self.wolfparent.DCENNstations)

        ret = myselect.ShowModal()
        if myselect.rbox.GetStringSelection() == _('Coordinates'):
            try:
                x = float(myselect.coordx.GetValue())
                y = float(myselect.coordy.GetValue())
            except ValueError:
                logging.error(_('Invalid coordinates! Please enter valid numbers.'))
                return

            self.wolfparent.set_outlet(x, y)

        elif myselect.rbox.GetStringSelection() == _('Code station'):
            try:
                code = myselect.codestation.GetValue()
            except ValueError:
                logging.error(_('Invalid code! Please enter a valid code.'))
                return

            if code in self.wolfparent.SPWstations.mystations:
                station = self.wolfparent.SPWstations.mystations[code]
            elif code in self.wolfparent.DCENNstations.mystations:
                station = self.wolfparent.DCENNstations.mystations[code]
            else:
                logging.error(_('Invalid code! Please enter a valid code.'))
                return

            x, y = station.x, station.y
            if x ==0. or y == 0.:
                logging.error(_('Invalid coordinates for the selected code!'))
                return

            self.wolfparent.set_outlet(x, y)

        elif myselect.rbox.GetStringSelection() == _('River/Name'):
            try:
                river = myselect.riverstation.GetValue()
                name = myselect.namestation.GetValue()
            except ValueError:
                logging.error(_('Invalid river or name! Please enter valid values.'))
                return

            if river in self.wolfparent.SPWstations.myrivers:
                if name in self.wolfparent.SPWstations.myrivers[river]:
                    x, y = self.wolfparent.SPWstations.myrivers[river][name].x, self.wolfparent.SPWstations.myrivers[river][name].y
                else:
                    logging.error(_('Invalid name for the selected river!'))
                    return
            elif river in self.wolfparent.DCENNstations.myrivers:
                if name in self.wolfparent.DCENNstations.myrivers[river]:
                    x, y = self.wolfparent.DCENNstations.myrivers[river][name].x, self.wolfparent.DCENNstations.myrivers[river][name].y
                else:
                    logging.error(_('Invalid name for the selected river!'))
                    return
            else:
                logging.error(_('Invalid river! Please enter a valid river.'))
                return
            if x ==0. or y == 0.:
                logging.error(_('Invalid coordinates for the selected river!'))
                return

            self.wolfparent.set_outlet(x, y)

        myselect.Destroy()

    def OnMenubar(self, event):
        """ Event handler for the menubar """

        # Call the parent event handler
        super().OnMenubar(event)

        # If not handled by the parent, handle it here

        id = event.GetId()
        item = self.menubar.FindItemById(id)
        if item is None:
            return

        itemlabel = item.ItemLabel

        if itemlabel == _('Choose outlet'):
            self._choose_outlet()

        elif itemlabel == _('Pick outlet'):
            self.action = 'Pick outlet'

        elif itemlabel == _('Pick interior point'):
            self.action = 'Pick interior point'

        elif itemlabel == _('Convert selection'):
            # Convert the selection to a general outlet
            if self.active_array is not None:

                xy = self.active_array.SelectionData.myselection

                if xy is not None and len(xy) == 1:
                    x, y = xy[0]
                    self.wolfparent.set_outlet(x, y)
                else:
                    logging.warning(_('No/Too many selections to convert to general outlet!'))
            else:
                logging.warning(_('No active array to convert selection from!'))

        elif itemlabel == _('Edit points'):
            # Edit interior points
            if self.wolfparent.interior_points is not None:
                self.wolfparent.interior_points.edit_points()
            else:
                logging.warning(_('No interior points to edit!'))

        elif itemlabel == _('Convert selections'):
            # Convert the selection to interior point
            if self.active_array is not None:

                xy = self.active_array.SelectionData.myselection

                if xy is not None and len(xy) > 0:
                    for x,y in xy:
                        self.wolfparent.add_interior_point(x, y)
                else:
                    logging.warning(_('No/Too many selections to convert to interior point!'))
            else:
                logging.warning(_('No active array to convert selection from!'))

        elif itemlabel == _('Use active array as DTM'):

            if self.active_array is not None:
                self.wolfparent.set_active_array_as_dtm(self.active_array)
            else:
                logging.warning(_('No active array to set as DTM!'))

        elif itemlabel == _('Crop active array on zoom'):

            if self.active_array is not None:
                [x1, x2], [y1, y2] = self.get_bounds()
                dx = self.active_array.dx

                x1 = int(x1 / dx) * dx - dx / 2
                x2 = int(x2 / dx) * dx + dx / 2
                y1 = int(y1 / dx) * dx - dx / 2
                y2 = int(y2 / dx) * dx + dx / 2
                anew = WolfArray(mold= self.active_array, crop= [[x1, x2], [y1, y2]])
                self.wolfparent.set_active_array_as_dtm(anew)
            else:
                logging.warning(_('No active array to crop on zoom!'))

        elif itemlabel == _('Crop active array using active vector'):

            if self.active_array is not None and self.active_vector is not None:
                bbox = self.active_vector.get_bounds_xx_yy()
                newarray = self.active_array.crop_array(bbox)

                newarray.mask_outsidepoly(self.active_vector)

                newarray.nullify_border(width=1)
                self.wolfparent.set_active_array_as_dtm(newarray)
            else:
                logging.warning(_('No active array or active vector to crop!'))

        elif itemlabel == _('Run preprocessing'):

            self.wolfparent.set_only_preprocess_data()
            self.wolfparent.run_preprocessing()

        elif itemlabel == _('Pick interior points'):
            self.action = 'Pick interior point'

        elif itemlabel == _('Topology'):

            if self.active_vector is None:
                logging.warning(_('No active vector to show topology!'))
                return

            file = self.wolfparent.mycatchment.save_flow_chart()
            self.active_vector.myprop.attachedimage = Path(file)
            self.active_vector.myprop.imagevisible = True
            self.active_vector._reset_listogl()


        elif itemlabel == _('Main model'):
            self.wolfparent.mainparams.Show()

        elif itemlabel == _('Basin'):
            self.wolfparent.basinparams.Show()

        elif itemlabel == _('Subbasins'):
            logging.warning(_('Not yet implemented !'))

        elif itemlabel == _('Pick Forced exchanges'):
            self.action = 'Pick Forced exchanges'
            self.check_id('Forced exchanges')
            self.check_id('Up nodes - FE')
            self.check_id('Down nodes - FE')

            raw_data_elev:WolfArray = None
            raw_data_elev = self.get_obj_from_id('Raw elevation [m]', drawing_type= draw_type.ARRAYS)
            if raw_data_elev is None:
                logging.error(_('No raw elevation array found! Forced exchanges cannot be picked without it.'))
                self.action = None

        elif itemlabel == _('Convert selection to Forced exchanges'):
            # Convert the selection to Forced exchanges
            if self.active_array is not None:

                xy_down = self.active_array.SelectionData.myselection
                xy_mem1= self.active_array.SelectionData.selections['1']

                if xy_down is not None and len(xy_down) ==1 and len(xy_mem1) > 0:
                    self.wolfparent.myexchanges.add_pairs_XY(xy_mem1, xy_down)
                else:
                    logging.warning(_('No/Too many selections to convert to Forced exchanges!'))
            else:
                logging.warning(_('No active array to convert selection from!'))

        elif itemlabel == _('Remove Forced exchanges'):
            # Remove Forced exchanges
            if self.wolfparent.myexchanges is not None:
                if self.wolfparent.myexchanges.is_empty():
                    logging.warning(_('No Forced exchanges to remove!'))
                else:
                    self.action = 'Remove Forced exchanges'
            else:
                logging.warning(_('No Forced exchanges to remove!'))

        elif itemlabel == _('Remove Forced exchanges inside vector'):
            # Remove Forced exchanges inside the active vector

            if self.active_vector is None:
                logging.warning(_('No active vector to remove Forced exchanges from!'))
                return

            if self.wolfparent.myexchanges is not None:
                self.wolfparent.myexchanges.remove_pairs_inside_vector(self.active_vector)
            else:
                logging.warning(_('No Forced exchanges or active vector to remove from!'))

        elif itemlabel == _('Crop MNT/MNS'):
            logging.warning(_('Not yet implemented !'))

        elif itemlabel == _('Crop land use (COSW)'):
            logging.warning(_('Not yet implemented !'))

        elif itemlabel == _('Analyze slope'):
            logging.warning(_('Not yet implemented !'))

        elif itemlabel == _('IRM - QDF'):
            logging.warning(_('Not yet implemented !'))

        elif itemlabel == _('Find upstream watershed'):
            self.action = 'Find upstream watershed'

        elif itemlabel == _('Find upstream watershed - limit to sub'):
            self.action = 'Find upstream watershed - limit to sub'

        elif itemlabel == _('Find Path to outlet'):
            self.action = 'Find Path to outlet'

        elif itemlabel == _('Select upstream watershed'):
            self.action = 'Select upstream watershed'

        elif itemlabel == _('Select upstream watershed - limit to sub'):
            self.action = 'Select upstream watershed - limit to sub'

        elif itemlabel == _('Select upstream rivers'):
            self.action = 'Select upstream rivers'

        elif itemlabel == _('Select upstream rivers - limit to sub'):
            self.action = 'Select upstream rivers - limit to sub'

        elif itemlabel == _('Select downstream rivers'):
            self.action = 'Select downstream rivers'


    def On_Mouse_Right_Down(self, e: wx.MouseEvent):

        # Call the parent event handler
        super().On_Mouse_Right_Down(e)

        if self.action is None:
            logging.info(_('No action selected !'))
            return

        if self.action == '':
            logging.info(_('No action selected !'))
            return

        pos = e.GetPosition()
        x, y = self.getXY(pos)

        alt = e.AltDown()
        ctrl = e.ControlDown()
        shiftdown = e.ShiftDown()

        if self.active_array is None:
            logging.warning(_('No active array !'))
            return

        if self.header is None:
            logging.error(_('No header defined. Cannot retrieve geolocalisation !'))
            return

        if self.header.dx != 0. and self.header.dy != 0:
            if not (self.active_array.dx == self.header.dx and self.active_array.dy == self.header.dy):
                logging.warning(_('Active array and watershed do not have the same resolution !'))
                return

        if self.action == 'Pick Forced exchanges':
            tmp_vec = self.wolfparent.myexchanges.temporary_vector
            if tmp_vec.nbvertices == 0:
                tmp_vec.add_vertex(wv(x,y))
                tmp_vec.add_vertex(wv(x,y))
            elif tmp_vec.nbvertices == 2:
                tmp_vec.myvertices[-1].x = x
                tmp_vec.myvertices[-1].y = y

                raw_data_elev:WolfArray = None
                raw_data_elev = self.get_obj_from_id('Raw elevation [m]', drawing_type= draw_type.ARRAYS)
                if raw_data_elev is not None:
                    zup = raw_data_elev.get_value(tmp_vec.myvertices[0].x, tmp_vec.myvertices[0].y)
                    zdown = raw_data_elev.get_value(tmp_vec.myvertices[1].x, tmp_vec.myvertices[1].y)

                txt = _('Do you want to add this forced exchange ?\n\n')
                txt += _('Up node: {:.2f} m\n').format(zup)
                txt += _('Down node: {:.2f} m').format(zdown)

                dlg = wx.MessageDialog(self, txt,
                                       _('Forced exchange'),
                                       wx.YES_NO | wx.ICON_QUESTION)

                if dlg.ShowModal() == wx.ID_YES:
                    # Add the forced exchange to the list
                    self.wolfparent.myexchanges.add_pair(tmp_vec.myvertices[0].copy(),
                                                         tmp_vec.myvertices[1].copy())
                    # Reset the temporary vector
                    tmp_vec.reset()

        elif self.action == 'Pick interior point':
            # Add an interior point to the watershed
            self.wolfparent.add_interior_point(x, y)

        elif self.action == 'Remove Forced exchanges':
            # Remove Forced exchanges
            if self.wolfparent.myexchanges is not None:
                if self.wolfparent.myexchanges.is_empty():
                    logging.warning(_('No Forced exchanges to remove!'))
                else:
                    self.wolfparent.myexchanges.remove_nearest_pair(x, y)
                    self.Refresh()
            else:
                logging.warning(_('No Forced exchanges to remove!'))


        elif 'Find upstream watershed' in self.action:

            if self.active_array is None:
                logging.warning(_('No active array - Please select an active array first!'))
                return

            if self.watershed is None:
                logging.warning(_('No watershed defined - Please define a watershed first!'))
                return

            starting_node = self.watershed.get_node_from_xy(x,y)
            up_vect = self.watershed.get_vector_from_upstream_node(starting_node, limit_to_sub='limit to sub' in self.action)

            if up_vect is None:
                logging.warning(_('No upstream watershed found !'))
                return

            def props_vec(vec:vector):
                vec.myprop.color = getIfromRGB((255,0,0))
                vec.myprop.width = 3
                vec.myprop.transparent = False
                vec.myprop.alpha = 122
                vec.myprop.filled = False

            if self.active_array.Operations is not None:
                newzone = zone(name = str(starting_node.sub))

                self.active_array.Operations.show_structure_OpsVectors()
                self.active_array.Operations.myzones.add_zone(newzone, forceparent=True)
                newzone.add_vector(up_vect, forceparent=True)

                props_vec(up_vect)

                self.active_array.Operations.myzones.prep_listogl()
                self.active_array.Operations.myzones.fill_structure()

                self.Refresh()
            else:
                logging.warning(_('No operations frame in the active array!'))

        elif 'Find Path to outlet' in self.action:

            if self.active_array is None:
                logging.warning(_('No active array - Please select an active array first!'))
                return

            if self.watershed is None:
                logging.warning(_('No watershed defined - Please define a watershed first!'))
                return

            down_vect = self.watershed.get_vector_from_xy_to_outlet(x, y)

            if down_vect is None:
                logging.warning(_('No downstream path found !'))
                return

            def props_vec(vec:vector):
                vec.myprop.color = getIfromRGB((255,128,192))
                vec.myprop.width = 3
                vec.myprop.transparent = False
                vec.myprop.alpha = 122
                vec.myprop.filled = False

            if self.active_array.Operations is not None:
                newzone = zone(name = down_vect.myname)

                self.active_array.Operations.show_structure_OpsVectors()
                self.active_array.Operations.myzones.add_zone(newzone, forceparent=True)
                newzone.add_vector(down_vect, forceparent=True)

                props_vec(down_vect)

                self.active_array.Operations.myzones.prep_listogl()
                self.active_array.Operations.myzones.fill_structure()

                self.Refresh()
            else:
                logging.warning(_('No operations frame in the active array!'))

        elif 'Select upstream watershed' in self.action:

            if self.active_array is None:
                logging.warning(_('No active array - Please select an active array first!'))
                return

            if self.watershed is None:
                logging.warning(_('No watershed defined - Please define a watershed first!'))
                return

            xy = self.watershed.get_xy_upstream_node(self.watershed.get_node_from_xy(x,y), limit_to_sub='limit to sub' in self.action)
            self.active_array.SelectionData.set_selection_from_list_xy(xy)
            self.Refresh()

        elif 'Select upstream rivers' in self.action:

            if self.active_array is None:
                logging.warning(_('No active array - Please select an active array first!'))
                return

            if self.watershed is None:
                logging.warning(_('No watershed defined - Please define a watershed first!'))
                return

            xy = self.watershed.get_xy_upstream_node(self.watershed.get_node_from_xy(x,y),
                                                     limit_to_sub='limit to sub' in self.action,
                                                     limit_to_river=True)

            self.active_array.SelectionData.set_selection_from_list_xy(xy)
            self.Refresh()

        elif 'Select downstream rivers' in self.action:

            if self.active_array is None:
                logging.warning(_('No active array - Please select an active array first!'))
                return

            if self.watershed is None:
                logging.warning(_('No watershed defined - Please define a watershed first!'))
                return

            xy = self.watershed.get_xy_downstream_node(self.watershed.get_node_from_xy(x,y))
            self.active_array.SelectionData.set_selection_from_list_xy(xy)
            self.Refresh()

        elif 'Pick outlet' in self.action:

            # Set the outlet in the watershed
            self.wolfparent.set_outlet(x, y)
            self.Refresh()

        elif 'Pick interior point' in self.action:

            # Set the interior point in the watershed
            self.wolfparent.add_interior_point(x, y)
            self.Refresh()

    def On_Mouse_Motion(self, e: wx.MouseEvent):
        """ Handle mouse motion events """

        # Call the parent event handler
        super().On_Mouse_Motion(e)

        if self.action is None:
            return

        pos = e.GetPosition()
        x, y = self.getXY(pos)

        if self.action == 'Pick Forced exchanges':
            tmp_vec = self.wolfparent.myexchanges.temporary_vector
            if tmp_vec.nbvertices == 2:
                tmp_vec.myvertices[-1].x = x
                tmp_vec.myvertices[-1].y = y

            self.Refresh()

    def Paint(self):
        """ Paint the map viewer """

        # Call the parent paint method
        super().Paint()
