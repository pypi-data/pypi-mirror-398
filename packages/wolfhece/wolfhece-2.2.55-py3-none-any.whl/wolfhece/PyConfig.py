"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import os
import json
from enum import Enum
from pathlib import Path
import logging

import wx
from .PyTranslate import _

class ConfigurationKeys(Enum):
    """ Using enumerated keys make sure we
    can check value names at code write time
    (i.e. we don't use string which are brittle)
    """
    VERSION = "Version"
    PLAY_WELCOME_SOUND = "PlayWelcomeSound"
    TICKS_SIZE = "TicksSize"
    TICKS_BOUNDS = "TicksBounds"
    TICKS_XROTATION = "TicksXRotation"
    TICKS_FONTSIZE = "TicksFontSize"
    COLOR_BACKGROUND = "ColorBackground"
    ACTIVE_ARRAY_PALETTE_FOR_IMAGE = "Use active array palette for image"
    ACTIVE_RES2D_PALETTE_FOR_IMAGE = "Use active result palette for image"
    ASSEMBLY_IMAGES = "AssemblyImages"
    DIRECTORY_DEM = "Default DEM directory"
    DIRECTORY_DTM = "Default DTM directory"
    DIRECTORY_LAZ = "Default LAZ directory"
    ACTIVE_VECTOR_COLOR = "Active vector color"
    ACTIVE_VECTOR_SIZE_SQUARE = "Active vector square size"
    XLSX_HECE_DATABASE = "Hece Database XLSX file"
    EPSG_CODE = "Default EPSG code"

class WolfConfiguration:
    """ Holds the PyWolf configuration """

    def __init__(self, path=None):
        # We make sure we use a standard location
        # to store the configuration
        if path is None:
            if os.name == "nt":
                # On Windows NT, LOCALAPPDATA is expected to be defined.
                # (might not be true in the future, who knows)
                self._options_file_path = Path(os.getenv("LOCALAPPDATA")) / "wolf.conf"
            else:
                self._options_file_path = Path("wolf.conf")
        else:
            self._options_file_path = path

        #Set default -- useful if new options are inserted
        # --> ensuring that default values are created even if not stored in the options file
        self.set_default_config()
        if self._options_file_path.exists():
            self.load()
        else:
            # self.set_default_config()
            # This save is not 100% necessary but it helps
            # to make sure a config file exists.
            self.save()

    @property
    def path(self) -> Path:
        """ Where the configuration is read/saved."""
        return self._options_file_path

    def set_default_config(self):
        self._config = {
            ConfigurationKeys.VERSION.value: 1,
            ConfigurationKeys.PLAY_WELCOME_SOUND.value: True,
            ConfigurationKeys.TICKS_SIZE.value: 500.,
            ConfigurationKeys.ACTIVE_ARRAY_PALETTE_FOR_IMAGE.value: True,
            ConfigurationKeys.ACTIVE_RES2D_PALETTE_FOR_IMAGE.value: False,
            ConfigurationKeys.TICKS_BOUNDS.value: True,
            ConfigurationKeys.COLOR_BACKGROUND.value: [255, 255, 255, 255],
            ConfigurationKeys.ASSEMBLY_IMAGES.value: 0,
            ConfigurationKeys.TICKS_XROTATION.value: 30.,
            ConfigurationKeys.TICKS_FONTSIZE.value: 12,
            ConfigurationKeys.DIRECTORY_DEM.value: "",
            ConfigurationKeys.DIRECTORY_DTM.value: "",
            ConfigurationKeys.DIRECTORY_LAZ.value: "",
            ConfigurationKeys.ACTIVE_VECTOR_COLOR.value: [0, 0, 0, 255],
            ConfigurationKeys.ACTIVE_VECTOR_SIZE_SQUARE.value: 5,
            ConfigurationKeys.XLSX_HECE_DATABASE.value: "",
            ConfigurationKeys.EPSG_CODE.value: "EPSG:31370"
        }
        self._types = {
            ConfigurationKeys.VERSION.value: int,
            ConfigurationKeys.PLAY_WELCOME_SOUND.value: bool,
            ConfigurationKeys.TICKS_SIZE.value: float,
            ConfigurationKeys.ACTIVE_ARRAY_PALETTE_FOR_IMAGE.value: bool,
            ConfigurationKeys.ACTIVE_RES2D_PALETTE_FOR_IMAGE.value: bool,
            ConfigurationKeys.TICKS_BOUNDS.value: bool,
            ConfigurationKeys.COLOR_BACKGROUND.value: list,
            ConfigurationKeys.ASSEMBLY_IMAGES.value: int,
            ConfigurationKeys.TICKS_XROTATION.value: float,
            ConfigurationKeys.TICKS_FONTSIZE.value: int,
            ConfigurationKeys.DIRECTORY_DEM.value: str,
            ConfigurationKeys.DIRECTORY_DTM.value: str,
            ConfigurationKeys.DIRECTORY_LAZ.value: str,
            ConfigurationKeys.ACTIVE_VECTOR_COLOR.value: list,
            ConfigurationKeys.ACTIVE_VECTOR_SIZE_SQUARE.value: int,
            ConfigurationKeys.XLSX_HECE_DATABASE.value: str,
            ConfigurationKeys.EPSG_CODE.value: str
        }

        self._check_config()

    def _check_config(self):
        assert self._config.keys() == self._types.keys()
        for idx, (key,val) in enumerate(self._config.items()):
            assert isinstance(val, self._types[key])

    def load(self):
        with open(self._options_file_path, "r", encoding="utf-8") as configfile:
            filecfg = json.loads(configfile.read())

        for curkey in filecfg.keys():
            if curkey in self._config.keys():
                self._config[curkey] = filecfg[curkey]

        self._check_config()

    def save(self):
        # Make sure to write the config file only if it can
        # be dumped by JSON.
        txt = json.dumps(self._config, indent=1)
        with open(self._options_file_path, "w", encoding="utf-8") as configfile:
            configfile.write(txt)

    def __getitem__(self, key: ConfigurationKeys):
        assert isinstance(key, ConfigurationKeys), "Please only use enum's for configuration keys."
        return self._config[key.value]

    def __setitem__(self, key: ConfigurationKeys, value):
        # A half-measure to ensure the config structure
        # can be somehow validated before run time.
        assert isinstance(key, ConfigurationKeys), "Please only use enum's for configuration keys."

        self._config[key.value] = value
        self._check_config()


class GlobalOptionsDialog(wx.Dialog):
    """ A dialog to set global options for a WolfMapViewer. """

    def __init__(self, *args, **kw):
        super(GlobalOptionsDialog, self).__init__(*args, **kw)

        self.InitUI()
        self.SetSize((600, 600))
        self.SetTitle(_("Global options"))

    def push_configuration(self, configuration):
        self.cfg_welcome_voice.SetValue(configuration[ConfigurationKeys.PLAY_WELCOME_SOUND])
        self.cfg_ticks_size.SetValue(str(configuration[ConfigurationKeys.TICKS_SIZE]))
        self.cfg_ticks_bounds.SetValue(configuration[ConfigurationKeys.TICKS_BOUNDS])
        self.cfg_bkg_color.SetColour(configuration[ConfigurationKeys.COLOR_BACKGROUND])
        self.cfg_active_array_pal.SetValue(configuration[ConfigurationKeys.ACTIVE_ARRAY_PALETTE_FOR_IMAGE])
        self.cfg_active_res_pal.SetValue(configuration[ConfigurationKeys.ACTIVE_RES2D_PALETTE_FOR_IMAGE])
        self.cfg_assembly_images.SetSelection(configuration[ConfigurationKeys.ASSEMBLY_IMAGES])
        self.cfg_ticks_xrotation.SetValue(str(configuration[ConfigurationKeys.TICKS_XROTATION]))
        self.cfg_ticks_fontsize.SetValue(str(configuration[ConfigurationKeys.TICKS_FONTSIZE]))
        self.cfg_directory_dem.SetValue(str(configuration[ConfigurationKeys.DIRECTORY_DEM]))
        self.cfg_directory_dtm.SetValue(str(configuration[ConfigurationKeys.DIRECTORY_DTM]))
        self.cfg_directory_laz.SetValue(str(configuration[ConfigurationKeys.DIRECTORY_LAZ]))
        self.cfg_vector_color.SetColour(configuration[ConfigurationKeys.ACTIVE_VECTOR_COLOR])
        self.cfg_square_size.SetValue(str(configuration[ConfigurationKeys.ACTIVE_VECTOR_SIZE_SQUARE]))
        self.cfg_xlsx_hece_database.SetValue(str(configuration[ConfigurationKeys.XLSX_HECE_DATABASE]))
        self.cfg_epsg_code.SetValue(str(configuration[ConfigurationKeys.EPSG_CODE]))

    def pull_configuration(self, configuration):
        configuration[ConfigurationKeys.PLAY_WELCOME_SOUND] = self.cfg_welcome_voice.IsChecked()
        configuration[ConfigurationKeys.TICKS_SIZE] = float(self.cfg_ticks_size.Value)
        configuration[ConfigurationKeys.TICKS_BOUNDS] = self.cfg_ticks_bounds.IsChecked()
        configuration[ConfigurationKeys.COLOR_BACKGROUND] = list(self.cfg_bkg_color.GetColour())
        configuration[ConfigurationKeys.ACTIVE_ARRAY_PALETTE_FOR_IMAGE] = self.cfg_active_array_pal.IsChecked()
        configuration[ConfigurationKeys.ACTIVE_RES2D_PALETTE_FOR_IMAGE] = self.cfg_active_res_pal.IsChecked()
        configuration[ConfigurationKeys.ASSEMBLY_IMAGES] = self.cfg_assembly_images.GetSelection()
        configuration[ConfigurationKeys.TICKS_XROTATION] = float(self.cfg_ticks_xrotation.Value)
        configuration[ConfigurationKeys.TICKS_FONTSIZE] = int(self.cfg_ticks_fontsize.Value)
        configuration[ConfigurationKeys.DIRECTORY_DEM] = str(self.cfg_directory_dem.Value)
        configuration[ConfigurationKeys.DIRECTORY_DTM] = str(self.cfg_directory_dtm.Value)
        configuration[ConfigurationKeys.DIRECTORY_LAZ] = str(self.cfg_directory_laz.Value)
        configuration[ConfigurationKeys.ACTIVE_VECTOR_COLOR] = list(self.cfg_vector_color.GetColour())
        configuration[ConfigurationKeys.ACTIVE_VECTOR_SIZE_SQUARE] = int(self.cfg_square_size.Value)
        configuration[ConfigurationKeys.XLSX_HECE_DATABASE] = str(self.cfg_xlsx_hece_database.Value)

        epsg = str(self.cfg_epsg_code.Value)
        if not epsg.upper().startswith("EPSG:"):
            epsg = epsg.strip().lower()
            if 'belgium 2008' in epsg or 'belgique 2008' in epsg:
                epsg = "EPSG:3812"
            elif 'belgium 1972' in epsg or 'belgium' in epsg or 'belgique 1972' in epsg or 'belgique' in epsg:
                epsg = "EPSG:31370"
            elif 'rgf93' in epsg or 'france' in epsg:
                epsg = "EPSG:2154"
            elif 'wgs 84' in epsg:
                epsg = "EPSG:4326"
            elif 'germany' in epsg or 'allemagne' in epsg:
                epsg = "EPSG:25832"
            else:
                try:
                    code = int(epsg)
                    epsg = f"EPSG:{code}"
                except:
                    logging.warning(_('Could not interpret EPSG code: {} -- keeping original value').format(epsg))
                    return

        configuration[ConfigurationKeys.EPSG_CODE] = epsg

    def InitUI(self):

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Panel 'Miscellaneous'
        pnl = wx.ScrolledWindow(self)

        sb = wx.StaticBox(pnl, label=_('Miscellaneous'))
        sbs = wx.StaticBoxSizer(sb , orient=wx.VERTICAL)

        self.cfg_welcome_voice = wx.CheckBox(pnl, label=_('Welcome voice'))
        self.cfg_welcome_voice.SetToolTip(_('Play a welcome message when opening the application'))
        sbs.Add(self.cfg_welcome_voice)

        sbs.AddSpacer(5)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_background_color = wx.StaticText(pnl, label=_('Background color'))
        self.cfg_bkg_color = wx.ColourPickerCtrl(pnl, colour=(255,255,255,255))
        self.cfg_bkg_color.SetToolTip(_('Background color for the viewer'))

        hsizer.Add(self.label_background_color, 1, wx.EXPAND)
        hsizer.Add(self.cfg_bkg_color, 1, wx.EXPAND)

        sbs.Add(hsizer, 1, wx.EXPAND)

        sbs.AddSpacer(5)

        pnl.SetSizer(sbs)
        pnl.Layout()

        vbox.Add(pnl, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)

        ### Panel 'Copy to clipboard'
        pnl = wx.ScrolledWindow(self)

        sb = wx.StaticBox(pnl, label=_('Copy to clipboard'))
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)

        hboxticks = wx.BoxSizer(wx.HORIZONTAL)
        self.label_ticks_size = wx.StaticText(pnl, label=_('Default ticks size [m]'))
        self.cfg_ticks_size = wx.TextCtrl(pnl, value='500.',style = wx.TE_CENTRE )

        self.label_ticks_xrotation = wx.StaticText(pnl, label=_('X rotation of ticks [°]'))
        self.cfg_ticks_xrotation = wx.TextCtrl(pnl, value='30.',style = wx.TE_CENTRE )

        self.label_ticks_fontsize = wx.StaticText(pnl, label=_('Font size of ticks'))
        self.cfg_ticks_fontsize = wx.TextCtrl(pnl, value='12',style = wx.TE_CENTRE )

        hboxticks.Add(self.label_ticks_size, 1, wx.EXPAND)
        hboxticks.Add(self.cfg_ticks_size, 1, wx.EXPAND, 5)
        sbs.Add(hboxticks, 1, wx.EXPAND,5)

        hboxticksxrotation = wx.BoxSizer(wx.HORIZONTAL)
        hboxticksxrotation.Add(self.label_ticks_xrotation, 1, wx.EXPAND)
        hboxticksxrotation.Add(self.cfg_ticks_xrotation, 1, wx.EXPAND, 5)
        sbs.Add(hboxticksxrotation, 1, wx.EXPAND,5)

        hboxticksfontsize = wx.BoxSizer(wx.HORIZONTAL)
        hboxticksfontsize.Add(self.label_ticks_fontsize, 1, wx.EXPAND)
        hboxticksfontsize.Add(self.cfg_ticks_fontsize, 1, wx.EXPAND, 5)
        sbs.Add(hboxticksfontsize, 1, wx.EXPAND,5)

        self.cfg_ticks_bounds = wx.CheckBox(pnl, label=_('Add bounds to ticks'))
        self.cfg_ticks_bounds.SetToolTip(_('If not checked, the extreme values of the ticks will not be displayed'))
        sbs.Add(self.cfg_ticks_bounds, 1, wx.EXPAND, 5)

        self.cfg_active_array_pal = wx.CheckBox(pnl, label=_('Use active array palette for image'))
        self.cfg_active_array_pal.SetToolTip(_('If checked, the active array palette will be used for the image'))
        sbs.Add(self.cfg_active_array_pal, 1, wx.EXPAND, 5)

        self.cfg_active_res_pal = wx.CheckBox(pnl, label=_('Use active result palette for image'))
        self.cfg_active_res_pal.SetToolTip(_('If checked, the active result palette will be used for the image (but priority to active array palette if checked)'))
        sbs.Add(self.cfg_active_res_pal, 1, wx.EXPAND, 5)

        locsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_assembly_images = wx.StaticText(pnl, label=_('Assembly mode for images (if linked viewers)'))
        self.cfg_assembly_images = wx.ListBox(pnl, choices=['horizontal', 'vertical', 'square'], style=wx.LB_SINGLE)
        self.cfg_assembly_images.SetToolTip(_('Choose the assembly mode for images -- horizontal, vertical or square'))

        locsizer.Add(self.label_assembly_images, 1, wx.EXPAND, 2)
        locsizer.Add(self.cfg_assembly_images, 1, wx.EXPAND,5)

        sbs.Add(locsizer, 3, wx.EXPAND, 5)

        # DEM directory
        dir_dem = wx.BoxSizer(wx.HORIZONTAL)
        self.label_directory_dem = wx.StaticText(pnl, label=_('Default DEM directory'))
        self.cfg_directory_dem = wx.TextCtrl(pnl, value='',style = wx.TE_CENTRE )
        self.btn_choose_dem = wx.Button(pnl, label=_('Choose'))
        self.btn_choose_dem.Bind(wx.EVT_BUTTON, self.OnChooseDem)

        dir_dem.Add(self.label_directory_dem, 1, wx.EXPAND, 2)
        dir_dem.Add(self.cfg_directory_dem, 1, wx.EXPAND, 5)
        dir_dem.Add(self.btn_choose_dem, 1, wx.EXPAND, 5)

        # DTM directory
        dir_dtm = wx.BoxSizer(wx.HORIZONTAL)
        self.label_directory_dtm = wx.StaticText(pnl, label=_('Default DTM directory'))
        self.cfg_directory_dtm = wx.TextCtrl(pnl, value='',style = wx.TE_CENTRE )
        self.btn_choose_dtm = wx.Button(pnl, label=_('Choose'))
        self.btn_choose_dtm.Bind(wx.EVT_BUTTON, self.OnChooseDtm)

        dir_dtm.Add(self.label_directory_dtm, 1, wx.EXPAND, 2)
        dir_dtm.Add(self.cfg_directory_dtm, 1, wx.EXPAND, 5)
        dir_dtm.Add(self.btn_choose_dtm, 1, wx.EXPAND, 5)

        # LAZ directory
        dir_laz = wx.BoxSizer(wx.HORIZONTAL)
        self.label_directory_laz = wx.StaticText(pnl, label=_('Default LAZ directory'))
        self.cfg_directory_laz = wx.TextCtrl(pnl, value='',style = wx.TE_CENTRE )
        self.btn_choose_laz = wx.Button(pnl, label=_('Choose'))
        self.btn_choose_laz.Bind(wx.EVT_BUTTON, self.OnChooseLaz)

        dir_laz.Add(self.label_directory_laz, 1, wx.EXPAND, 2)
        dir_laz.Add(self.cfg_directory_laz, 1, wx.EXPAND, 5)
        dir_laz.Add(self.btn_choose_laz, 1, wx.EXPAND, 5)

        # XLSX HECE database
        dir_xlsx = wx.BoxSizer(wx.HORIZONTAL)
        self.label_xlsx_hece_database = wx.StaticText(pnl, label=_('HECE Database file'))
        self.cfg_xlsx_hece_database = wx.TextCtrl(pnl, value='', style=wx.TE_CENTRE)
        self.btn_choose_xlsx = wx.Button(pnl, label=_('Choose'))
        self.btn_choose_xlsx.Bind(wx.EVT_BUTTON, self.OnChooseXLSX)
        dir_xlsx.Add(self.label_xlsx_hece_database, 1, wx.EXPAND, 2)
        dir_xlsx.Add(self.cfg_xlsx_hece_database, 1, wx.EXPAND, 5)
        dir_xlsx.Add(self.btn_choose_xlsx, 1, wx.EXPAND, 5)

        sbs.Add(dir_dem, 1, wx.EXPAND, 5)
        sbs.Add(dir_dtm, 1, wx.EXPAND, 5)
        sbs.Add(dir_laz, 1, wx.EXPAND, 5)
        sbs.Add(dir_xlsx, 1, wx.EXPAND, 5)

        # Vector color
        color_vector = wx.BoxSizer(wx.HORIZONTAL)
        self.label_vector_color = wx.StaticText(pnl, label=_('Default vector color'))
        self.cfg_vector_color = wx.ColourPickerCtrl(pnl, colour=(0, 0, 0, 255))
        self.cfg_vector_color.SetToolTip(_('Color for active vector in the viewer'))

        self.cfg_square_size = wx.TextCtrl(pnl, value='5', style=wx.TE_CENTRE)
        self.cfg_square_size.SetToolTip(_('Size of the square for active vector in the viewer'))

        color_vector.Add(self.label_vector_color, 1, wx.EXPAND, 2)
        color_vector.Add(self.cfg_vector_color, 1, wx.EXPAND, 5)
        color_vector.Add(self.cfg_square_size, 1, wx.EXPAND, 5)
        sbs.Add(color_vector, 1, wx.EXPAND, 5)

        self.cfg_epsg_code = wx.TextCtrl(pnl, value='EPSG:31370', style=wx.TE_CENTRE)
        self.cfg_epsg_code.SetToolTip(_('Default EPSG code for new arrays added to the viewer\nExamples: EPSG:31370, EPSG:2154, EPSG:4326\nor simply the code number: 31370, 2154, 4326\nor a descriptive name: Belgium 1972, Belgium 2008, France RGF93, WGS 84'))

        epsg_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_epsg_code = wx.StaticText(pnl, label=_('Default EPSG code'))
        epsg_sizer.Add(self.label_epsg_code, 1, wx.EXPAND, 2)
        epsg_sizer.Add(self.cfg_epsg_code, 1, wx.EXPAND, 5)
        sbs.Add(epsg_sizer, 1, wx.EXPAND, 5)

        pnl.SetSizer(sbs)
        pnl.Layout()

        vbox.Add(pnl, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)

        # Buttons
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, label=_('Ok'))
        okButton.SetDefault()
        closeButton = wx.Button(self, label=_('Close'))
        hbox2.Add(okButton)
        hbox2.Add(closeButton, flag=wx.LEFT, border=5)

        vbox.Add(hbox2, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        self.SetSizer(vbox)
        self.Layout()

        okButton.Bind(wx.EVT_BUTTON, self.OnOk)
        closeButton.Bind(wx.EVT_BUTTON, self.OnClose)

    def OnChooseDem(self, e):
        """ Choose a directory for DEM files """
        dlg = wx.DirDialog(self, _("Choose a directory"), style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.cfg_directory_dem.SetValue(str(dlg.GetPath()))
        dlg.Destroy()

    def OnChooseDtm(self, e):
        """ Choose a directory for DTM files """
        dlg = wx.DirDialog(self, _("Choose a directory"), style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.cfg_directory_dtm.SetValue(str(dlg.GetPath()))
        dlg.Destroy()

    def OnChooseLaz(self, e):
        """ Choose a directory for LAZ files """
        dlg = wx.DirDialog(self, _("Choose a directory"), style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.cfg_directory_laz.SetValue(str(dlg.GetPath()))
        dlg.Destroy()

    def OnChooseXLSX(self, e):
        """ Choose a XLSX file for HECE database """
        dlg = wx.FileDialog(self, _("Choose a HECE database file"), style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        dlg.SetWildcard("Excel files (*.xlsx)|*.xlsx")
        if dlg.ShowModal() == wx.ID_OK:
            self.cfg_xlsx_hece_database.SetValue(str(dlg.GetPath()))
        dlg.Destroy()

    def OnOk(self, e):
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Close()

    def OnClose(self, e):
        self.Destroy()

def handle_configuration_dialog(wxparent, configuration):
    dlg = GlobalOptionsDialog(wxparent)
    try:
        dlg.push_configuration(configuration)

        if dlg.ShowModal() == wx.ID_OK:
            # do something here
            dlg.pull_configuration(configuration)
            configuration.save()
            logging.info(_('Configuration saved in {}').format(str(configuration.path)))
        else:
            # handle dialog being cancelled or ended by some other button
            pass
    finally:
        # explicitly cause the dialog to destroy itself
        dlg.Destroy()


if __name__ == "__main__":
    cfg = WolfConfiguration(Path("test.conf"))
    cfg[ConfigurationKeys.PLAY_WELCOME_SOUND] = False
    print(cfg._config)
    cfg.save()
    cfg = WolfConfiguration(Path("test.conf"))
    cfg.load()
    print(cfg[ConfigurationKeys.PLAY_WELCOME_SOUND])
