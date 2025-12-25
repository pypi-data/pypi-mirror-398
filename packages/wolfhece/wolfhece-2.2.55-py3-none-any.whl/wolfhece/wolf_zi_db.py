"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import geopandas as gpd
import pandas as pd
from PIL import Image,ImageDraw,ImageFont
import numpy as np
import logging
from enum import Enum
from pathlib import Path
from typing import Literal, Union
import wx
from tqdm import tqdm
import re

from shapely.geometry import Polygon

from .PyVertexvectors import Zones, zone, vector, wolfvertex
from .textpillow import Font_Priority
from .wolf_texture import genericImagetexture
from .PyPictures import PictureCollection
from .PyTranslate import _

class ColNames_PlansTerriers(Enum):
    """ Enum for the column names in the database """

    KEY   = 'Clé primaire'
    ORIGX = 'Origine x'
    ORIGY = 'Origine y'
    ENDX  = 'Xsup'
    ENDY  = 'Ysup'
    WIDTH = 'Largeur'
    HEIGHT= 'Hauteur'
    FULLRES = 'Acces'
    LOWRES  = 'Acces2'
    RIVER   = 'River'

class ColNames_Ouvrages(Enum):
    """ Enum for the column names in the database """

    KEY   = 'Clé primaire'
    X1 = 'X Lambert gauche'
    X2 = 'X Lambert droit'
    Y1  = 'Y Lambert gauche'
    Y2  = 'Y Lambert droit'
    REMARK = 'Remarques'
    RIVER = 'Lieu'
    PHOTO1 = 'Photo1'
    PHOTO2 = 'Photo2'
    PHOTO3 = 'Photo3'
    PHOTO4 = 'Photo4'
    PHOTO5 = 'Photo5'
    PHOTO6 = 'Photo6'
    PHOTO7 = 'Photo7'
    PHOTO8 = 'Photo8'
    PHOTO9 = 'Photo9'
    PHOTO10 = 'Photo10'
    DATE = 'Date'

class ColNames_Particularites(Enum):
    """ Enum for the column names in the database """

    KEY   = 'Clé primaire'
    X = 'Xlambert'
    Y = 'Ylambert'
    REMARK = 'Commentaires'
    RIVER = 'Rivière'
    PHOTO1 = 'Photo 1'
    PHOTO2 = 'Photo 2'
    PHOTO3 = 'Photo 3'
    PHOTO4 = 'Photo 4'
    PHOTO5 = 'Photo 5'
    ORIENTATION = 'Orientation'
    DATE = 'Date'

class ColNames_Enquetes(Enum):
    """ Enum for the column names in the database """

    KEY   = 'Clé primaire'
    X = 'XLambert'
    Y = 'YLambert'
    RIVER = 'Rivière'
    PHOTO = 'Photo'
    ORIENTATION = 'Orientation'
    DATE = 'Date'

class ColNames_Profils(Enum):
    """ Enum for the column names in the database """

    KEY   = 'Clé primaire'
    X = 'XLambert'
    Y = 'YLambert'
    PHOTO = 'FichierImage'
    RIVER   = 'Rivière'
    DATE = 'DateModif'

def _test_bounds(x:float, y:float, bounds:list[list[float, float], list[float, float]]) -> bool:
    """ Test if the coordinates are inside the bounds

    :param x: The x coordinate
    :type x: float
    :param y: The y coordinate
    :type y: float
    :param bounds: The bounds to test against - [ [xmin, xmax], [ymin, ymax] ]
    :type bounds: list[list[float, float], list[float, float]]
    :return: True if the coordinates are inside the bounds, False otherwise
    :rtype: bool
    """

    if bounds is None:
        return True

    xmin, xmax = bounds[0]
    ymin, ymax = bounds[1]

    return xmin <= x <= xmax and ymin <= y <= ymax


def _sanitize_legendtext(text:str) -> str:
    """ Sanitize the legend text by replacing newlines and special characters

    :param text: The text to sanitize
    :type text: str
    :return: The sanitized text
    :rtype: str
    """
    text = str(text)
    # replace newlines and special characters
    text = re.sub(r'(_x000D_\n|\n)', ' - ', text)

    return text.strip()
class ZI_Databse_Elt():
    """ Class to store the database elements """

    def __init__(self,
                 origx:float,
                 origy:float,
                 endx:float,
                 endy:float,
                 width:float,
                 height:float,
                 fullpath:Path,
                 lowpath:Path) -> None:

        """ Constructor for the class

        :param origx: The x coordinate of the origin (Lower-left corner)
        :type origx: float
        :param origy: The y coordinate of the origin (Lower-left corner)
        :type origy: float
        :param endx: The x coordinate of the end (Upper-right corner)
        :type endx: float
        :param endy: The y coordinate of the end (Upper-right corner)
        :type endy: float
        :param width: The width of the image [m]
        :type width: float
        :param height: The height of the image [m]
        :type height: float
        :param fullpath: The full path to the full resolution image
        :type fullpath: Path
        :param lowpath: The full path to the low resolution image
        :type lowpath: Path
        """

        self.origx = origx
        self.origy = origy
        self.endx = endx
        self.endy = endy
        self.width = width
        self.height = height
        self.fullpath = fullpath
        self.lowpath = lowpath

class PlansTerrier(Zones):
    """
    Class to handle the "Plans Terriers" -- Black and white scanned tif files from SPW.

    Override the Zones class to handle the 'plans terriers' contours. In the "myzones" list, the object will store the contours for each river.

    Elements will be stored in the self.maps dictionary, with the key being the name of the river and the name of the file.

    The textures (images) will be stored in the self.textures dictionary, with the key being the ZI_Databse_Elt object.

    In the mapviewer, the user can choose the rivers to display, and the images will be loaded/unloaded on the fly when the user clicks on the map.

    During import of the images, the system will apply transparency based on a color and a tolerance, and,
    if necessary, will replace the other colors with another one (self.color). If self.color is None, no replacement will be done.

    :param parent: The wx parent of the object
    :type parent: wx.Window
    :param idx: The index of the object
    :type idx: str
    :param plotted: If the object is plotted
    :type plotted: bool
    :param mapviewer: The mapviewer object
    :type mapviewer: MapViewer
    :param rivers: The list of rivers to display
    :type rivers: list[str]

    """

    def __init__(self,
                 parent=None,
                 idx: str = '',
                 plotted: bool = True,
                 mapviewer=None,
                 rivers:list[str] = ['Vesdre', 'Hoegne']) -> None:

        super().__init__('', 0., 0., 0., 0., parent, True, idx, plotted, mapviewer, True, None, False)

        self.maps:dict[str, ZI_Databse_Elt] = {}
        self.textures:dict[ZI_Databse_Elt, genericImagetexture] = {}

        self.color = np.asarray([0,0,0,255])
        self.tolerance = 0
        self.transparent_color = [255, 255, 255]

        self.rivers = rivers

        self.initialized = False

        self.wx_exists = wx.GetApp() is not None

    def set_tolerance(self, tol:int):
        """
        Set the tolerance for the transparency

        Color will be considered transparent if the difference between the color and the transparent color is less than the tolerance.

        """

        self.tolerance = tol

    def set_transparent_color(self, color:list[int, int, int]):
        """
        Set the transparent color.

        Color is a list of 3 integers, representing the RGB color (0 -> 255).

        """

        self.transparent_color = color

    def set_color(self, color:tuple[int, int, int]):
        """
        Set the color of the image.

        As the provided images are black and white, the color will be used to replace the black color.

        If the images are not black and white, the color will be used to replace all non-transparent colors.

        """

        self.color = np.asarray(color)

    def check_plot(self):
        """ Activate the plot if the object is initialized """

        if not self.initialized:
            self.read_db(self.filename)

        if self.initialized:
            super().check_plot()

    def _create_zones(self):

        """
        Create the zones for the selected rivers.

        Each river will be a zone, and the vectors will be the contours of the images.

        """

        for curriver in self.rivers:
            curzone = zone(name=curriver, parent=self)
            self.add_zone(curzone)

    def read_db(self, filename:Union[str,Path], sel_rivers: list[str] = None):
        """ Read the database (Excel file) and create the zones and the vectors.

        The user will be prompted to select the rivers to display.

        """

        self.filename = Path(filename)

        if not self.filename.exists() or filename == '':

            if self.wx_exists:

                dlg= wx.FileDialog(None, _("Choose a file"), defaultDir= "", wildcard="Excel (*.xlsx)|*.xlsx", style = wx.FD_OPEN)
                ret = dlg.ShowModal()
                if ret == wx.ID_OK:
                    self.filename = Path(dlg.GetPath())
                    dlg.Destroy()
                else:
                    logging.error('No file selected')
                    dlg.Destroy()
                    return

            else:
                logging.error('No file selected or the file does not exist.')
                return

        logging.info(f'Reading database from {self.filename}')
        self.db = pd.read_excel(self.filename, sheet_name='Plans_Terriers')
        logging.info(f'Database read successfully from {self.filename}')

        rivers = list(self.db[ColNames_PlansTerriers.RIVER.value].unique())
        rivers.sort()

        self.rivers = []

        if sel_rivers is None and self.wx_exists:

            with wx.MessageDialog(None, _("Choose the rivers to display"), _("Rivers"), wx.YES_NO | wx.ICON_QUESTION) as dlg:

                if dlg.ShowModal() == wx.ID_YES:

                    with wx.MultiChoiceDialog(None, _("Choose the rivers to display"), _("Rivers"), rivers) as dlg_river:
                        ret = dlg_river.ShowModal()

                        if ret == wx.ID_OK:
                            for curidx in dlg_river.GetSelections():
                                self.rivers.append(rivers[curidx])
                else:
                    self.rivers = rivers

        elif sel_rivers is not None:

            for curruver in sel_rivers:
                if curruver in rivers:
                    self.rivers.append(curruver)
                else:
                    logging.error(f'River {curruver} not found in the database -- Ignoring !')

        self._create_zones()
        self._filter_db()

        self.initialized = True

    def _filter_db(self):

        for curline in self.db.iterrows():

            fullpath:str
            lowpath:str
            fullpath = curline[1][ColNames_PlansTerriers.FULLRES.value]
            lowpath = curline[1][ColNames_PlansTerriers.LOWRES.value]

            for curriver in self.rivers:
                curzone = self.get_zone(curriver)

                if curriver in fullpath:

                    fullpath = fullpath.replace(r'\\192.168.2.185\Intranet\Data\Données Topographiques\Plans Terriers\Full resu',
                                                str(self.filename.parent) +r'\Plans_Terriers\Fullresu')
                    lowpath = lowpath.replace(r'\\192.168.2.185\Intranet\Data\Données Topographiques\Plans Terriers\Low resu',
                                                str(self.filename.parent) + r'\Plans_Terriers\Lowresu')
                    fullpath = Path(fullpath)
                    lowpath = Path(lowpath)

                    if fullpath.exists() and lowpath.exists():

                        curelt = ZI_Databse_Elt(curline[1][ColNames_PlansTerriers.ORIGX.value],
                                                curline[1][ColNames_PlansTerriers.ORIGY.value],
                                                curline[1][ColNames_PlansTerriers.ENDX.value],
                                                curline[1][ColNames_PlansTerriers.ENDY.value],
                                                curline[1][ColNames_PlansTerriers.WIDTH.value],
                                                curline[1][ColNames_PlansTerriers.HEIGHT.value],
                                                fullpath,
                                                lowpath)

                        self.maps[curriver + fullpath.name] = curelt

                        curvector = vector(parentzone=curzone, name=fullpath.name)
                        curzone.add_vector(curvector)

                        curvector.add_vertex(wolfvertex(x=curelt.origx, y=curelt.origy))
                        curvector.add_vertex(wolfvertex(x=curelt.endx, y=curelt.origy))
                        curvector.add_vertex(wolfvertex(x=curelt.endx, y=curelt.endy))
                        curvector.add_vertex(wolfvertex(x=curelt.origx, y=curelt.endy))
                        curvector.close_force()
                    else:
                        logging.debug(f'File {fullpath} does not exist')

                    break

        self.find_minmax(True)


    def _find_map(self, x:float, y:float):

        for curzone in self.myzones:
            for curvector in curzone.myvectors:
                if curvector.isinside(x, y):
                    return self.maps[curzone.myname+curvector.myname]

        return None

    def load_texture(self, x:float, y:float, which:Literal['full', 'low'] = 'low'):

        curmap = self._find_map(x, y)

        if curmap is not None:
            if curmap not in self.textures:

                if which == 'full':
                    curpath= curmap.fullpath
                else:
                    curpath = curmap.lowpath

                self.textures[curmap] = genericImagetexture(which = which,
                                                            label=curmap.fullpath,
                                                            mapviewer=self.mapviewer,
                                                            xmin=curmap.origx,
                                                            ymin=curmap.origy,
                                                            xmax=curmap.endx,
                                                            ymax=curmap.endy,
                                                            imageFile=curpath,
                                                            transparent_color=self.transparent_color,
                                                            tolerance=self.tolerance,
                                                            replace_color=self.color
                                                            )

            else:
                self.unload_textture(x, y)

            # return self.textures[curmap]
        else:
            return None

    def unload_textture(self, x:float, y:float):
        curmap = self._find_map(x, y)
        if curmap is not None:
            if curmap in self.textures:
                self.textures[curmap].unload()
                del self.textures[curmap]

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        super().plot(sx, sy, xmin, ymin, xmax, ymax, size)

        for curtexture in self.textures.values():
            curtexture.plot(sx, sy, xmin, ymin, xmax, ymax, size)


class Ouvrages(PictureCollection):
    """ Class to handle the "Ouvrages" -- Pictures of the structures in the ZI. """

    def __init__(self, parent=None, idx: str = '', plotted: bool = True, mapviewer=None, rivers:list[str] = None) -> None:
        """
        Constructor for the Ouvrages class.

        :param parent: The wx parent of the object
        :type parent: wx.Window
        :param idx: The index of the object
        :type idx: str
        :param plotted: If the object is plotted
        :type plotted: bool
        :param mapviewer: The mapviewer object
        :type mapviewer: MapViewer
        :param rivers: The list of rivers to display
        :type rivers: list[str]
        """

        super().__init__(parent = parent, idx = idx, plotted = plotted, mapviewer = mapviewer)

        self.wx_exists = wx.GetApp() is not None
        self.db = None
        self.rivers = rivers
        self.initialized = False

        self._columns = ColNames_Ouvrages

    def check_plot(self):
        """ Activate the plot if the object is initialized """

        if self.initialized:
            # Ask if the user wants to reload the database
            if self.wx_exists:
                dlg = wx.MessageDialog(None, _("Do you want to reload the database?"), _("Reload Database"),
                                       wx.YES_NO | wx.ICON_QUESTION)
                ret = dlg.ShowModal()
                if ret == wx.ID_YES:
                    self.initialized = False
                dlg.Destroy()

        if not self.initialized:

            # try to get the filename from the parent mapviewer
            if self.mapviewer is not None:
                self.filename = self.mapviewer.default_hece_database
                bounds = self.mapviewer.get_bounds()

            if 'bridge' in self.idx.lower() or 'pont' in self.idx.lower():
                self.read_db(self.filename, sel_rivers=self.rivers, sheet_name='Ponts', bounds=bounds)
            elif 'weir' in self.idx.lower() or 'seuil' in self.idx.lower():
                self.read_db(self.filename, sel_rivers=self.rivers, sheet_name='Seuils', bounds=bounds)
            elif 'survey' in self.idx.lower() or 'enquete' in self.idx.lower():
                self.read_db(self.filename, sel_rivers=self.rivers, sheet_name='Photos', bounds=bounds)
            elif 'features' in self.idx.lower() or 'particularit' in self.idx.lower():
                self.read_db(self.filename, sel_rivers=self.rivers, sheet_name='Particularités', bounds=bounds)
            elif 'cross' in self.idx.lower() or 'section' in self.idx.lower():
                self.read_db(self.filename, sel_rivers=self.rivers, sheet_name='Sections transversales scannées', bounds=bounds)

        if self.initialized:
            super().check_plot()

    def read_db(self, filename:str | Path,
                sel_rivers: list[str] = None,
                sheet_name: str = 'Ponts',
                bounds: list[list[float, float], list[float, float]] = None):
        """ Read the database (Excel file) and create the zones and the vectors.

        The user will be prompted to select the rivers to display.

        :param filename: The path to the Excel file containing the database
        :type filename: str | Path
        :param sel_rivers: The list of rivers to display, if None, the user will be prompted to select the rivers
        :type sel_rivers: list[str] | None
        :param sheet_name: The name of the sheet in the Excel file to read
        :type sheet_name: str
        :param bounds: The bounds of the area to display, if None, no test on coordinates will be done - [ [xmin, xmax], [ymin, ymax] ]
        :type bounds: list[list[float, float], list[float, float]] | None
        """

        self.filename = Path(filename)

        if not self.filename.exists() or filename == '':

            if self.wx_exists:

                dlg= wx.FileDialog(None, _("Choose a file"), defaultDir= "", wildcard="Excel (*.xlsx)|*.xlsx", style = wx.FD_OPEN)
                ret = dlg.ShowModal()
                if ret == wx.ID_OK:
                    self.filename = Path(dlg.GetPath())
                    dlg.Destroy()
                else:
                    logging.error('No file selected')
                    dlg.Destroy()
                    return

            else:
                logging.error('No file selected or the file does not exist.')
                return

        try:
            logging.info(f'Reading database from {self.filename}')
            self.db = pd.read_excel(self.filename, sheet_name=sheet_name)
            logging.info(f'Database read successfully from {self.filename}')
        except ValueError as e:
            logging.error(f"Error reading the Excel file: {e}")
            return

        rivers = list(self.db[ColNames_Ouvrages.RIVER.value].unique())
        rivers.sort()

        self.rivers = []

        if sel_rivers is None and self.wx_exists:

            with wx.MessageDialog(None, _("Choose the rivers to display"), _("Rivers"), wx.YES_NO | wx.ICON_QUESTION) as dlg:

                if dlg.ShowModal() == wx.ID_YES:

                    with wx.MultiChoiceDialog(None, _("Choose the rivers to display"), _("Rivers"), rivers) as dlg_river:
                        ret = dlg_river.ShowModal()

                        if ret == wx.ID_OK:
                            for curidx in dlg_river.GetSelections():
                                self.rivers.append(rivers[curidx])
                else:
                    self.rivers = rivers

        elif sel_rivers is not None:

            for curruver in sel_rivers:
                if curruver in rivers:
                    self.rivers.append(curruver)
                else:
                    logging.error(f'River {curruver} not found in the database -- Ignoring !')

        self._filter_db(bounds)

        self.initialized = True

    def _filter_db(self, bounds: list[list[float, float], list[float, float]] = None):
        """ Filter the database based on the selected rivers and bounds.

        :param bounds: The bounds of the area to display, if None, no test on coordinates will be done - [ [xmin, xmax], [ymin, ymax] ]
        :type bounds: list[list[float, float], list[float, float]] | None
        """

        if len(self.rivers) == 0:
            locdb = self.db
        else:
            locdb = self.db[self.db[ColNames_Ouvrages.RIVER.value].isin(self.rivers)]

        for id, curline in tqdm(locdb.iterrows()):
            river = curline[ColNames_Ouvrages.RIVER.value]

            paths = []
            for col in [ColNames_Ouvrages.PHOTO1,
                        ColNames_Ouvrages.PHOTO2,
                        ColNames_Ouvrages.PHOTO3,
                        ColNames_Ouvrages.PHOTO4,
                        ColNames_Ouvrages.PHOTO5,
                        ColNames_Ouvrages.PHOTO6,
                        ColNames_Ouvrages.PHOTO7,
                        ColNames_Ouvrages.PHOTO8,
                        ColNames_Ouvrages.PHOTO9,
                        ColNames_Ouvrages.PHOTO10]:

                fullpath = curline[col.value]

                fullpath = fullpath.replace(r'\\192.168.2.185\Intranet\Data\Données et Photos de crues\Ouvrages',
                                            str(self.filename.parent) +r'\Ouvrages')
                if fullpath == '0':
                    break

                fullpath = Path(fullpath)

                if fullpath.exists():
                    paths.append(fullpath)
                else:
                    logging.debug(f'File {fullpath} does not exist')

            if not paths:
                logging.debug(f'No valid paths found for river {river} in the database')
                continue

            nb = len(paths)
            x1 = curline[ColNames_Ouvrages.X1.value]
            x2 = curline[ColNames_Ouvrages.X2.value]
            y1 = curline[ColNames_Ouvrages.Y1.value]
            y2 = curline[ColNames_Ouvrages.Y2.value]

            keyzone = river.strip() + '_' + paths[0].stem
            # make a mosaic - max 3 pictures per row

            xref = (x1 + x2) / 2
            yref = (y1 + y2) / 2

            if bounds is not None and not _test_bounds(xref, yref, bounds):
                logging.debug(f'Coordinates are out of bounds -- Skipping line {id}')
                continue

            for i in range(nb):
                picture = paths[i]

                x = xref + (i % 3)  * self._default_size
                y = yref + (i // 3) * self._default_size

                if x < 1000. and y < 1000.:
                    logging.error(f'Coordinates for river {river} are not set -- Skipping picture {picture}')
                    continue

                self.add_picture(picture, x=x, y=y, name=picture.stem, keyzone=keyzone)

                pic = self[(keyzone, picture.stem)]
                pic.myprop.legendtext = _sanitize_legendtext(curline[ColNames_Ouvrages.REMARK.value])
                pic.myprop.legendx = pic.centroid.x
                pic.myprop.legendy = pic.centroid.y
                pic.myprop.legendpriority = Font_Priority.WIDTH
                pic.myprop.legendlength = 100

        self.find_minmax(True)

class Particularites(Ouvrages):
    """ Class to handle the "Particularités" -- Pictures of the particularities in the ZI. """

    def __init__(self, parent=None, idx = '', plotted = True, mapviewer=None, rivers = None):
        super().__init__(parent = parent, idx = idx, plotted = plotted, mapviewer = mapviewer, rivers = rivers)

        self._columns = ColNames_Particularites

    def read_db(self, filename:str | Path,
                sel_rivers: list[str] = None,
                sheet_name: str = 'Particularités',
                bounds: list[list[float, float], list[float, float]] = None):
        """ Read the database (Excel file) and create the zones and the vectors.

        The user will be prompted to select the rivers to display.

        :param filename: The path to the Excel file containing the database
        :type filename: str | Path
        :param sel_rivers: The list of rivers to display, if None, the user will be prompted to select the rivers
        :type sel_rivers: list[str] | None
        :param sheet_name: The name of the sheet in the Excel file to read
        :type sheet_name: str
        :param bounds: The bounds of the area to display, if None, no test on coordinates will be done - [ [xmin, xmax], [ymin, ymax] ]
        :type bounds: list[list[float, float], list[float, float]] | None
        """

        self.filename = Path(filename)

        if not self.filename.exists() or filename == '':

            if self.wx_exists:

                dlg= wx.FileDialog(None, _("Choose a file"), defaultDir= "", wildcard="Excel (*.xlsx)|*.xlsx", style = wx.FD_OPEN)
                ret = dlg.ShowModal()
                if ret == wx.ID_OK:
                    self.filename = Path(dlg.GetPath())
                    dlg.Destroy()
                else:
                    logging.error('No file selected')
                    dlg.Destroy()
                    return

            else:
                logging.error('No file selected or the file does not exist.')
                return

        try:
            logging.info(f'Reading database from {self.filename}')
            self.db = pd.read_excel(self.filename, sheet_name=sheet_name)
            logging.info(f'Database read successfully from {self.filename}')
        except ValueError as e:
            logging.error(f"Error reading the Excel file: {e}")
            return

        rivers = list(self.db[ColNames_Particularites.RIVER.value].unique())
        rivers.sort()

        self.rivers = []

        if sel_rivers is None and self.wx_exists:

            with wx.MessageDialog(None, _("Choose the rivers to display"), _("Rivers"), wx.YES_NO | wx.ICON_QUESTION) as dlg:

                if dlg.ShowModal() == wx.ID_YES:

                    with wx.MultiChoiceDialog(None, _("Choose the rivers to display"), _("Rivers"), rivers) as dlg_river:
                        ret = dlg_river.ShowModal()

                        if ret == wx.ID_OK:
                            for curidx in dlg_river.GetSelections():
                                self.rivers.append(rivers[curidx])
                else:
                    self.rivers = rivers

        elif sel_rivers is not None:

            for curruver in sel_rivers:
                if curruver in rivers:
                    self.rivers.append(curruver)
                else:
                    logging.error(f'River {curruver} not found in the database -- Ignoring !')

        self._filter_db(bounds)

        self.initialized = True

    def _filter_db(self, bounds: list[list[float, float], list[float, float]] = None):
        """ Filter the database based on the selected rivers and bounds.

        :param bounds: The bounds of the area to display, if None, no test on coordinates will be done - [ [xmin, xmax], [ymin, ymax] ]
        :type bounds: list[list[float, float], list[float, float]] |
        """

        if len(self.rivers) == 0:
            locdb = self.db
        else:
            locdb = self.db[self.db[ColNames_Particularites.RIVER.value].isin(self.rivers)]

        for id, curline in tqdm(locdb.iterrows()):
            river = curline[ColNames_Particularites.RIVER.value]

            paths = []
            for col in [ColNames_Particularites.PHOTO1,
                        ColNames_Particularites.PHOTO2,
                        ColNames_Particularites.PHOTO3,
                        ColNames_Particularites.PHOTO4,
                        ColNames_Particularites.PHOTO5]:

                fullpath = curline[col.value]

                fullpath = fullpath.replace(r'\\192.168.2.185\Intranet\Data\Données et Photos de crues',
                                            str(self.filename.parent))
                fullpath = Path(fullpath)

                if fullpath.exists():
                    paths.append(fullpath)
                else:
                    logging.debug(f'File {fullpath} does not exist')

            if not paths:
                logging.debug(f'No valid paths found for river {river} in the database')
                continue

            nb = len(paths)
            xref = curline[ColNames_Particularites.X.value]
            yref = curline[ColNames_Particularites.Y.value]

            keyzone = river.strip() + '_' + paths[0].stem
            # make a mosaic - max 3 pictures per row

            if bounds is not None and not _test_bounds(xref, yref, bounds):
                logging.info(f'Coordinates are out of bounds -- Skipping line {id}')
                continue

            for i in range(nb):
                picture = paths[i]
                x = xref + (i % 3)  * self._default_size
                y = yref + (i // 3) * self._default_size

                self.add_picture(picture, x=x, y=y, name=picture.stem, keyzone=keyzone)

                pic = self[(keyzone, picture.stem)]
                pic.myprop.legendtext = _sanitize_legendtext(curline[ColNames_Particularites.REMARK.value])
                pic.myprop.legendx = pic.centroid.x
                pic.myprop.legendy = pic.centroid.y
                pic.myprop.legendpriority = Font_Priority.WIDTH
                pic.myprop.legendlength = 100


        self.find_minmax(True)

class Enquetes(Ouvrages):
    """ Class to handle the "Enquêtes" -- Pictures of the surveys in the ZI. """
    def __init__(self, parent=None, idx = '', plotted = True, mapviewer=None, rivers = None):
        super().__init__(parent = parent, idx = idx, plotted = plotted, mapviewer = mapviewer, rivers = rivers)

        self._columns = ColNames_Enquetes

    def read_db(self, filename:str | Path,
                sel_rivers: list[str] = None,
                sheet_name: str = 'Photos',
                bounds: list[list[float, float], list[float, float]] = None):
        """ Read the database (Excel file) and create the zones and the vectors.

        The user will be prompted to select the rivers to display.

        :param filename: The path to the Excel file containing the database
        :type filename: str | Path
        :param sel_rivers: The list of rivers to display, if None, the user will be prompted to select the rivers
        :type sel_rivers: list[str] | None
        :param sheet_name: The name of the sheet in the Excel file to read
        :type sheet_name: str
        :param bounds: The bounds of the area to display, if None, no test on coordinates will be done - [ [xmin, xmax], [ymin, ymax] ]
        :type bounds: list[list[float, float], list[float, float]] |
        """

        self.filename = Path(filename)

        if not self.filename.exists() or filename == '':

            if self.wx_exists:

                dlg= wx.FileDialog(None, _("Choose a file"), defaultDir= "", wildcard="Excel (*.xlsx)|*.xlsx", style = wx.FD_OPEN)
                ret = dlg.ShowModal()
                if ret == wx.ID_OK:
                    self.filename = Path(dlg.GetPath())
                    dlg.Destroy()
                else:
                    logging.error('No file selected')
                    dlg.Destroy()
                    return

            else:
                logging.error('No file selected or the file does not exist.')
                return

        try:
            logging.info(f'Reading database from {self.filename}')
            self.db = pd.read_excel(self.filename, sheet_name=sheet_name)
            logging.info(f'Database read successfully from {self.filename}')
        except ValueError as e:
            logging.error(f"Error reading the Excel file: {e}")
            return

        rivers = list(self.db[ColNames_Enquetes.RIVER.value].unique())
        rivers.sort()

        self.rivers = []

        if sel_rivers is None and self.wx_exists:

            with wx.MessageDialog(None, _("Choose the rivers to display"), _("Rivers"), wx.YES_NO | wx.ICON_QUESTION) as dlg:

                if dlg.ShowModal() == wx.ID_YES:

                    with wx.MultiChoiceDialog(None, _("Choose the rivers to display"), _("Rivers"), rivers) as dlg_river:
                        ret = dlg_river.ShowModal()

                        if ret == wx.ID_OK:
                            for curidx in dlg_river.GetSelections():
                                self.rivers.append(rivers[curidx])
                else:
                    self.rivers = rivers

        elif sel_rivers is not None:

            for curruver in sel_rivers:
                if curruver in rivers:
                    self.rivers.append(curruver)
                else:
                    logging.error(f'River {curruver} not found in the database -- Ignoring !')

        self._filter_db(bounds)

        self.initialized = True

    def _filter_db(self, bounds: list[list[float, float], list[float, float]] = None):
        """ Filter the database based on the selected rivers and bounds.

        :param bounds: The bounds of the area to display, if None, no test on coordinates will be done - [ [xmin, xmax], [ymin, ymax] ]
        :type bounds: list[list[float, float], list[float, float]] |
        """

        if len(self.rivers) == 0:
            locdb = self.db
        else:
            locdb = self.db[self.db[ColNames_Enquetes.RIVER.value].isin(self.rivers)]

        for id, curline in tqdm(locdb.iterrows()):
            river = curline[ColNames_Enquetes.RIVER.value]

            fullpath = curline[ColNames_Enquetes.PHOTO.value]

            fullpath = fullpath.replace(r'\\192.168.2.185\Intranet\Data\Données et Photos de crues',
                                        str(self.filename.parent))
            fullpath = Path(fullpath)

            if not fullpath.exists():
                logging.debug(f'File {fullpath} does not exist')
                continue

            x = curline[ColNames_Enquetes.X.value]
            y = curline[ColNames_Enquetes.Y.value]

            if bounds is not None and not _test_bounds(x, y, bounds):
                logging.info(f'Coordinates are out of bounds -- Skipping line {id}')
                continue

            keyzone = river.strip()

            picture = fullpath
            self.add_picture(picture, x=x, y=y, name=picture.stem, keyzone=keyzone)

            pic = self[(keyzone, picture.stem)]
            pic.myprop.legendtext = _sanitize_legendtext(curline[ColNames_Enquetes.DATE.value])
            pic.myprop.legendx = pic.centroid.x
            pic.myprop.legendy = pic.centroid.y
            pic.myprop.legendpriority = Font_Priority.WIDTH
            pic.myprop.legendlength = 100


        self.find_minmax(True)

class Profils(Ouvrages):
    """ Class to handle the "Profils en travers" -- Pictures of the corss-sections in the ZI. """

    def __init__(self, parent=None, idx = '', plotted = True, mapviewer=None, rivers = None):
        super().__init__(parent = parent, idx = idx, plotted = plotted, mapviewer = mapviewer, rivers = rivers)

        self._columns = ColNames_Profils

    def read_db(self, filename:str | Path,
                sel_rivers: list[str] = None,
                sheet_name: str = 'Sections transversales scannées',
                bounds: list[list[float, float], list[float, float]] = None):
        """ Read the database (Excel file) and create the zones and the vectors.

        The user will be prompted to select the rivers to display.

        :param filename: The path to the Excel file containing the database
        :type filename: str | Path
        :param sel_rivers: The list of rivers to display, if None, the user will be prompted to select the rivers
        :type sel_rivers: list[str] | None
        :param sheet_name: The name of the sheet in the Excel file to read
        :type sheet_name: str
        :param bounds: The bounds of the area to display, if None, no test on coordinates will be done - [ [xmin, xmax], [ymin, ymax] ]
        :type bounds: list[list[float, float], list[float, float]] |
        """

        self.filename = Path(filename)

        if not self.filename.exists() or filename == '':

            if self.wx_exists:

                dlg= wx.FileDialog(None, _("Choose a file"), defaultDir= "", wildcard="Excel (*.xlsx)|*.xlsx", style = wx.FD_OPEN)
                ret = dlg.ShowModal()
                if ret == wx.ID_OK:
                    self.filename = Path(dlg.GetPath())
                    dlg.Destroy()
                else:
                    logging.error('No file selected')
                    dlg.Destroy()
                    return

            else:
                logging.error('No file selected or the file does not exist.')
                return

        try:
            logging.info(f'Reading database from {self.filename}')
            self.db = pd.read_excel(self.filename, sheet_name=sheet_name)
            logging.info(f'Database read successfully from {self.filename}')
        except ValueError as e:
            logging.error(f"Error reading the Excel file: {e}")
            return

        rivers = list(self.db[ColNames_Profils.RIVER.value].unique())
        rivers.sort()

        self.rivers = []

        if sel_rivers is None and self.wx_exists:

            with wx.MessageDialog(None, _("Choose the rivers to display"), _("Rivers"), wx.YES_NO | wx.ICON_QUESTION) as dlg:

                if dlg.ShowModal() == wx.ID_YES:

                    with wx.MultiChoiceDialog(None, _("Choose the rivers to display"), _("Rivers"), rivers) as dlg_river:
                        ret = dlg_river.ShowModal()

                        if ret == wx.ID_OK:
                            for curidx in dlg_river.GetSelections():
                                self.rivers.append(rivers[curidx])
                else:
                    self.rivers = rivers

        elif sel_rivers is not None:

            for curruver in sel_rivers:
                if curruver in rivers:
                    self.rivers.append(curruver)
                else:
                    logging.error(f'River {curruver} not found in the database -- Ignoring !')

        self._filter_db(bounds)

        self.initialized = True

    def _filter_db(self, bounds: list[list[float, float], list[float, float]] = None):
        """ Filter the database based on the selected rivers and bounds.

        :param bounds: The bounds of the area to display, if None, no test on coordinates will be done - [ [xmin, xmax], [ymin, ymax] ]
        :type bounds: list[list[float, float], list[float, float]] |
        """

        if len(self.rivers) == 0:
            locdb = self.db
        else:
            locdb = self.db[self.db[ColNames_Profils.RIVER.value].isin(self.rivers)]

        for id, curline in tqdm(locdb.iterrows()):
            river = curline[ColNames_Profils.RIVER.value]

            fullpath = curline[ColNames_Profils.PHOTO.value]

            fullpath = fullpath.replace(r'\\192.168.2.185\Intranet\Data\Données et Photos de crues\Données Profils',
                                        str(self.filename.parent) + r'\Profils')
            fullpath = Path(fullpath)

            if not fullpath.exists():
                logging.debug(f'File {fullpath} does not exist')
                continue

            x = curline[ColNames_Profils.X.value]
            y = curline[ColNames_Profils.Y.value]

            if bounds is not None and not _test_bounds(x, y, bounds):
                logging.info(f'Coordinates are out of bounds -- Skipping line {id}')
                continue

            keyzone = river.strip()

            picture = fullpath
            self.add_picture(picture, x=x, y=y, name=picture.stem, keyzone=keyzone)

            pic = self[(keyzone, picture.stem)]
            pic.myprop.legendtext = _sanitize_legendtext(curline[ColNames_Profils.DATE.value])
            pic.myprop.legendx = pic.centroid.x
            pic.myprop.legendy = pic.centroid.y
            pic.myprop.legendpriority = Font_Priority.WIDTH
            pic.myprop.legendlength = 100


        self.find_minmax(True)