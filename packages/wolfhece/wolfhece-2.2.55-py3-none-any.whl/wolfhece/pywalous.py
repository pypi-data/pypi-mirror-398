"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from osgeo import ogr, gdal
import geopandas as gpd
from os.path import exists, join, dirname, basename
from os import getcwd, chdir
from typing import Union, Literal
import numpy as np
from pathlib import Path
import logging

import wx
import wx.grid

from .PyTranslate import _
from .PyPalette import wolfpalette
from .wolf_array import WolfArray, header_wolf


"""
Hydrology classification for Land Use in Wallonia:
1 = forêt
2 = prairie
3 = culture
4 = pavés/urbain
5 = rivière
6 = plan d'eau
"""

HYDROLOGY_LANDUSE_FR = {"forêt" : 1.,
                        "prairie" : 2.,
                        "culture" : 3.,
                        "pavés/urbain" : 4.,
                        "rivière" : 5.,
                        "plan d'eau" : 6.,
                     }

HYDROLOGY_LANDUSE_EN = {"forest" : 1.,
                        "meadow" : 2.,
                        "crop" : 3.,
                        "paved/urban" : 4.,
                        "river" : 5.,
                        "water body" : 6.,
                        }

# WALOUS OCS
# ----------

"""
Extrait de https://metawal.wallonie.be/geonetwork/srv/api/records/86462606-4a21-49c8-ab9e-564ccba681b7/attachments/DescriptionLegende_WALOUS_OCS.pdf

1. Revêtement artificiel du sol: cette classe reprend tous les revêtements artificiels du sol
de nature peu ou pas perméable (ex béton, le bitume ou les pavés). Ceci comprend le réseau routier, les trottoirs, les terrasses, les parkings (les emplacements de parking semiperméables non végétalisés sont également dans cette catégorie) et les terrains ou pistes de sport en matériaux synthétiques.
2. Constructions artificielles hors sol : cette classe reprend tous les bâtiments et autres constructions s'élevant au-dessus du sol.
3. Réseau ferroviaire : cette classe reprend les rails et ballasts des chemins de fer encore en activité (les RaVEL entre dans la classe 1). Cette classe se différencie de la classe 1 par sa grande perméabilité.
4. Sols nus : cette classe inclut tout type de roche mère n'étant couverte par des végétaux supérieurs à aucun moment de l'année. Ces sols sont soit naturels (roches affleurantes, falaises, berges caillouteuses…), soit générés par l'activité humaine (extraction, sols compactés, coupe à blanc de l'année…)
5. Eaux de surface : cette classe comprend toutes les surfaces d'eau libre, naturelles ou artificielles. Ceci inclut donc à la fois les cours d'eau (rivières, fleuves et canaux) et les plans d'eau (mares, étangs, lacs, bassins de décantation, piscines extérieures).
6. Couvert herbacé en rotation : cette classe reprend les parcelles combinant un couvert herbacé une partie de l'année et un sol nu temporairement mis à nu. On y retrouve toutes les cultures annuelles, ainsi que les prairies temporaires succédant à une culture annuelle.
7. Couvert herbacé continu : cette classe reprend tous les sols recouverts par de la végétation herbacée tout au long de l'année. Cette végétation peut être d'origine naturelle (landes, mégaphorbiaies, tourbières, pelouses naturelles, végétation rudérale recolonisant une friche ou une ancienne coupe à blanc…), agricole (prés et prairies non labourés dans la saison) ou artificielle (jardin, terrains de sport, parcs…)
8. Arbres résineux : cette classe comprend tous les arbres de plus de 3 m (isolés, en haie ou en peuplement) du groupe des résineux (gymnosperme).
9. Arbres feuillus : cette classe comprend tous les arbres de plus de 3 m (isolés, en haie ou en peuplement) du groupe des feuillus (angiosperme).
80. Arbustes résineux : cette classe comprend tous les arbres et arbustes de moins de 3 m (isolés, en haie ou en peuplement) du groupe des résineux (gymnosperme).
90. Arbustes feuillus : cette classe comprend tous les arbres et arbuste de moins de 3 m (isolés, en haie ou en peuplement) du groupe des feuillus (angiosperme).


<paletteEntry color="#8a8a8a" value="1" alpha="255" label="Revêtement artificiel au sol"/>
<paletteEntry color="#dc0f0f" value="2" alpha="255" label="Constructions artificielles hors sol"/>
<paletteEntry color="#4e4e4e" value="3" alpha="255" label="Réseau ferroviaire"/>
<paletteEntry color="#d0d0d0" value="4" alpha="255" label="Sols nus"/>
<paletteEntry color="#2461f7" value="5" alpha="255" label="Eaux de surface"/>
<paletteEntry color="#ffff73" value="6" alpha="255" label="Couvert herbacé en rotation dans l'année (ex: culture annuelle)"/>
<paletteEntry color="#e9ffbe" value="7" alpha="255" label="Couvert herbacé toute l'année"/>
<paletteEntry color="#003200" value="8" alpha="255" label="Résineux (> 3m)"/>
<paletteEntry color="#007800" value="80" alpha="255" label="Résineux (≤ 3m)"/>
<paletteEntry color="#28c828" value="9" alpha="255" label="Feuillus (> 3m)"/>
<paletteEntry color="#b7e8b0" value="90" alpha="255" label="Feuillus (≤ 3m)"/>
<paletteEntry color="#e5ea3f" value="0" alpha="0" label="Pas de données"/>
"""

WALOUS_OCS = { "Revêtement artificiel au sol": 1.,
              "Constructions artificielles hors sol": 2.,
              "Réseau ferroviaire": 3.,
              "Sols nus": 4.,
              "Eaux de surface": 5.,
              "Couvert herbacé en rotation dans l'année": 6.,
              "Couvert herbacé toute l'année": 7.,
              "Arbres résineux (>= 3m)": 8.,
              "Arbres feuillus (>= 3m)": 9.,
              "Arbustes résineux (< 3m)": 80.,
              "Arbustes feuillus (< 3m)": 90.}

WALOUS_OCS_COLORMAP = {
    0.: (229, 234, 63, 0),       # #e5ea3f Pas de données
    1.: (138, 138, 138, 255),    # #8a8a8a Revêtement artificiel au sol
    2.: (220, 15, 15, 255),      # #dc0f0f Constructions artificielles hors sol
    3.: (78, 78, 78, 255),       # #4e4e4e Réseau ferroviaire
    4.: (208, 208, 208, 255),    # #d0d0d0 Sols nus
    5.: (36, 97, 247, 255),      # #2461f7 Eaux de surface
    6.: (255, 255, 115, 255),    # #ffff73 Couvert herbacé en rotation
    7.: (233, 255, 190, 255),    # #e9ffbe Couvert herbacé continu
    8.: (0, 50, 0, 255),         # #003200 Arbres résineux (> 3m)
    9.: (40, 200, 40, 255),      # #28c828 Arbres feuillus (> 3m)
    80.: (0, 120, 0, 255),       # #007800 Arbustes résineux (≤ 3m)
    90.: (183, 232, 176, 255),   # #b7e8b0 Arbustes feuillus (≤ 3m)
}

WALOUS_OCS2MANNING = {1.: 0.02, # Revêtement artificiel au sol
                     2.: 0.025, # Constructions artificielles hors sol
                     3.: 0.04,  # Réseau ferroviaire
                     4.: 0.04,  # Sols nus
                     5.: 0.033,  # Eaux de surface
                     6.: 0.04,  # Couvert herbacé en rotation dans l'année
                     7.: 0.03,  # Couvert herbacé toute l'année
                     8.: 0.04, # Résineux (> 3m)
                     9.: 0.04,  # Feuillus (> 3m)
                     80.: 0.03, # Résineux (≤ 3m)
                     90.: 0.03, # Feuillus (≤ 3m)
                     }


WALOUS_OCS2HYDROLOGY = {1.: 4., # Revêtement artificiel au sol
                    2.: 4., # Constructions artificielles hors sol
                    3.: 4., # Réseau ferroviaire
                    4.: 4., # Sols nus
                    5.: 5., # Eaux de surface
                    6.: 3., # Couvert herbacé en rotation dans l'année
                    7.: 2., # Couvert herbacé toute l'année
                    8.: 1., # Résineux (> 3m)
                    9.: 1., # Feuillus (> 3m)
                    80.: 3., # Arbustes résineux (< 3m)
                    90.: 3.  # Arbustes feuillus (< 3m)
                    }

# WALOUS UTS
# ----------

WALOUS_UTS_MAJ_NIV1 = {'Production primaire': 1.,
                   'Production secondaire': 2.,
                   'Production tertiaire': 3.,
                   'Réseaux de transport, Logistique et réseaux d\'utilité publique': 4.,
                   'Usage résidentiel': 5.,
                   'Autres usages': 6.,
                   'Zones naturelles': 7.}

WALOUS_UTS_MAJ_NIV2 = {'Agriculture': 11.,
                   'Sylviculture': 12.,
                   'Industries Extractives': 13.,
                   'Aquaculture et pêche':14,
                   'Production secondaire non définie': 20.,
                   'Industrie de matières premières': 21.,
                   'Industrie lourde': 22.,
                   'Industrie légère': 23.,
                   'Production d\'énergie': 24.,
                   'Service commerciaux': 31.,
                   'Services financiers, spécialisés et d\'information': 32.,
                   'Services publics': 33.,
                   'Services culturels, Services de loisirs et Services récréatifs': 34.,
                   'Réseaux de transport': 41.,
                   'Services Logistiques et d\'entreposage': 42.,
                   'Réseau d\'utilité publique': 43.,
                   'Usage résidentiel permanent': 51.,
                   'Usage résidentiel avec d\'autres usages compatibles': 52.,
                   'Autres usages résidentiels': 53.,
                   'Zones abandonnées': 62.,
                   'Usage inconnu': 66.,
                   'Zones naturelles': 70.}

WALOUS_UTS_COLORMAP_MAJ_NIV1 = {1.: (181,230,90,255),
                            2.: (99,99,99,255),
                            3.: (159,187,215,255),
                            4.: (181,121,241,255),
                            5.: (241,121,99,255),
                            6.: (221,221,221,255),
                            7.: (255,255,190,255)}

WALOUS_UTS_COLORMAP_MAJ_NIV2 = {11.: (153,230,0,255),
                            12.: (55,168,0,255),
                            13.: (142,181,180,255),
                            14.: (172,250,192,255),
                            20.: (179,179,179,255),
                            21.: (0,0,0,255),
                            22.: (157,157,157,255),
                            23.: (225,225,225,255),
                            24.: (79,79,79,255),
                            31.: (0,133,168,255),
                            32.: (186,236,245,255),
                            33.: (71,214,242,255),
                            34.: (102,154,171,255),
                            41.: (169,0,230,255),
                            42.: (213,196,245,255),
                            43.: (180,135,247,255),
                            51.: (255,0,0,255),
                            52.: (168,0,0,255),
                            53.: (255,127,127,255),
                            62.: (136,69,69,255),
                            66.: (206,136,102,255),
                            70.: (255,255,190,255)}

WALOUS_UTS2MANNING_MAJ_NIV1 = {1.: 0.04, # Production primaire
                           2.: 0.02, # Production secondaire
                           3.: 0.02, # Production tertiaire
                           4.: 0.03, # Réseaux de transport, Logistique et réseaux d'utilité publique
                           5.: 0.025,# Usage résidentiel
                           6.: 0.04, # Autres usages
                           7.: 0.05} # Zones naturelles

WALOUS_UTS2MANNING_MAJ_NIV2 = {11.: 0.04, # Agriculture
                           12.: 0.04, # Sylviculture
                           13.: 0.04, # Industries Extractives
                           14.: 0.04, # Aquaculture et pêche
                           20.: 0.03, # Production secondaire non définie
                           21.: 0.03, # Industrie de matières premières
                           22.: 0.03, # Industrie lourde
                           23.: 0.03, # Industrie légère
                           24.: 0.03, # Production d'énergie
                           31.: 0.02, # Service commerciaux
                           32.: 0.02, # Services financiers, spécialisés et d'information
                           33.: 0.02, # Services publics
                           34.: 0.02, # Services culturels, Services de loisirs et Services récréatifs
                           41.: 0.025, # Réseaux de transport
                           42.: 0.02, # Services Logistiques et d'entreposage
                           43.: 0.025, # Réseau d'utilité publique
                           51.: 0.025, # Usage résidentiel permanent
                           52.: 0.025, # Usage résidentiel avec d'autres usages compatibles
                           53.: 0.025, # Autres usages résidentiels
                           62.: 0.04, # Zones abandonnées
                           66.: 0.04, # Usage inconnu
                           70.: 0.05} # Zones naturelles


def get_palette_walous_uts(which:Literal['MAJ_NIV1', 'MAJ_NIV2']) -> wolfpalette:
    """
    Get the palette for WALOUS

    :return : palette
    """

    locpal = wolfpalette()
    locpal.interval_cst = True
    locpal.automatic = False

    if which == 'MAJ_NIV1':
        locpal.set_values_colors(values = list(WALOUS_UTS_MAJ_NIV1.values()),
                                 colors = list(WALOUS_UTS_COLORMAP_MAJ_NIV1.values()))
    elif which == 'MAJ_NIV2':
        locpal.set_values_colors(values = list(WALOUS_UTS_MAJ_NIV2.values()),
                                 colors = list(WALOUS_UTS_COLORMAP_MAJ_NIV2.values()))
    else:
        logging.error('Unknown WALOUS level')

    return locpal

def get_palette_walous_ocs() -> wolfpalette:
    """
    Get the palette for WALOUS OCS

    :return : palette
    """

    locpal = wolfpalette()
    locpal.interval_cst = True
    locpal.automatic = False

    locpal.set_values_colors(values = list(WALOUS_OCS_COLORMAP.keys()),
                             colors = list(WALOUS_OCS_COLORMAP.values()))

    return locpal

def update_palette_walous_uts(which:Literal['UTS_MAJ_NIV1', 'UTS_MAJ_NIV2'], pal:wolfpalette):
    """
    Update the palette for WALOUS MAJ_NIV1

    :param pal : palette to update
    :return : updated palette
    """

    if which in ['UTS_MAJ_NIV1', 'MAJ_NIV1']:
        for k, v in WALOUS_UTS_COLORMAP_MAJ_NIV1.items():
            pal.set_values_colors(values = [val - 1e-6 for val in list(WALOUS_UTS_MAJ_NIV1.values())],
                                 colors = list(WALOUS_UTS_COLORMAP_MAJ_NIV1.values()))
    elif which in ['UTS_MAJ_NIV2', 'MAJ_NIV2']:
        for k, v in WALOUS_UTS_COLORMAP_MAJ_NIV2.items():
            pal.set_values_colors(values = [val - 1e-6 for val in list(WALOUS_UTS_MAJ_NIV2.values())],
                                 colors = list(WALOUS_UTS_COLORMAP_MAJ_NIV2.values()))

    pal.interval_cst = True
    pal.automatic = False

    return 0

def update_palette_walous_ocs(pal:wolfpalette):
    """
    Update the palette for WALOUS OCS

    :param pal : palette to update
    :return : updated palette
    """

    for k, v in WALOUS_OCS_COLORMAP.items():
        pal.set_values_colors(values = [val - 1e-6 for val in list(WALOUS_OCS_COLORMAP.keys())],
                             colors = list(WALOUS_OCS_COLORMAP.values()))

    pal.interval_cst = True
    pal.automatic = False

    return 0


class Walous_data():
    """
    La donnée Walous est liée à l'utilisation des sols en Wallonie

    source : https://geoportail.wallonie.be/walous

    Cette classe permet la manipulation de la donnée dans le cadre du projet MODREC
    et plus spécifiquement la distribution d'un coefficient de frottement sur base
    de la donnée Walous.

    """

    def __init__(self,
                 dir_data:str = '',
                 fn:str = 'WAL_UTS__2018_L72',
                 extension:str = '.shp',
                 bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]] = None) -> None:
        """
        Constructor

        :param dir_data : directory of the data
        :param fn : filename without extension
        :param extension : extension of the file (.shp, .gpkg, ...)
        :param bounds : Two ways to set spatial bounds -- [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]

        """

        self._dir = str(dir_data)    # directory of the data
        self._fn  = str(fn)          # filename without extension
        self._extension = extension # extension of the file
        self._gdf = None        # geopandas dataframe

        if bounds is not None:
            # Bounds are set -> read file
            self.read(True, bounds=bounds)

    def read(self,
             force:bool = False,
             bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]] = None):
        """
        Read data from file

        :param force : force to read even read was done before
        :param bounds : [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]
        """

        if self._gdf is None or force:
            assert self._dir!="" and self._fn != ''

            filepath = (Path(self._dir)/ self._fn).with_suffix(self._extension)

            if filepath.exists():
                if bounds is not None:
                    if len(bounds)==2:
                        # [[xmin, xmax], [ymin, ymax]]
                        xmin = bounds[0][0]
                        xmax = bounds[0][1]
                        ymin = bounds[1][0]
                        ymax = bounds[1][1]
                    else:
                        # [xmin, ymin, xmax, ymax]
                        xmin = bounds[0]
                        xmax = bounds[2]
                        ymin = bounds[1]
                        ymax = bounds[3]

                    # read part of the file
                    self._gdf = gpd.read_file(str(filepath), bbox=(xmin,ymin,xmax,ymax))
                else:
                    # read all
                    self._gdf = gpd.read_file(str(filepath))

                # self._gdf['MAJ_NIV2'] = np.asarray(self._gdf['MAJ_NIV2'], dtype=int)
                # self._gdf['MAJ_NIV3'] = np.asarray(self._gdf['MAJ_NIV3'], dtype=int) # ne fonctionne pas car le niveau 3 contient des lettres --> à généraliser
            else:
                self._gdf = None

    def write(self, fnout:str='out_clip.shp'):
        """
        Write _gdf to file

        :param fnout : output filename
        """

        try:
            curdir = getcwd()
            detsdir = dirname(fnout)

            chdir(detsdir)

            fnout = str((Path(fnout)).with_suffix(self._extension))

            self._gdf.to_file(basename(fnout))

            chdir(curdir)
            return 0

        except:
            logging.error('Error in writing data - Walous module')
            return -1


    def to_file(self, fn:str='out_clip.shp'):
        """
        Alias to write

        :param fn : output filename
        """

        self.write(fn)

    def rasterize(self,
                  bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]],
                  layer:Literal['UTS_MAJ_NIV1','UTS_MAJ_NIV2'] = 'UTS_MAJ_NIV1',
                  fn_out:str = 'out.tif',
                  pixel_size:float = 0.5,
                  NoData_value:float = -99999.,
                  num_type = gdal.GDT_Float32,
                  ):

        """
        Rasterization of polygon data to tif.

        :param bounds : [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]
        :param layer : layer to rasterize
        :param fn_out : output filename
        :param pixel_size : pixel size
        :param NoData_value : NoData value
        :param num_type : type of the number
        """

        layer = layer.upper().replace('UTS_', '')

        if bounds is None:
            logging.error('Bounds must be set')
            return None
        else:
            if len(bounds)==4:
                # [[xmin, xmax], [ymin, ymax]]
                bounds = [[bounds[0], bounds[2]], [bounds[1], bounds[3]]]

        if self._gdf is None:
            logging.info('Reading data')
            self.read(bounds=bounds)
            logging.info('End of reading data')

        if self._gdf is None:
            logging.error('No data to rasterize')
            return None

        if layer not in self._gdf.keys():
            logging.error('Layer not found in the data')
            return None

        ret = self.write(str(fn_out) + '.shp')

        if ret !=0:
            logging.error('An error occured in writing the data to file')
            return -1

        try:

            # Add a new column for mapping based on the desired layer
            if layer == 'MAJ_NIV2':
                self._gdf['Mapping'] = np.float32(self._gdf[layer].replace('_', ''))
            else:
                self._gdf['Mapping'] = np.float32(self._gdf[layer])

            source_ds:ogr.DataSource
            source_layer:ogr.Layer

            source_ds = ogr.Open(self._gdf.to_json())

            # source_srs:ogr.
            source_layer = source_ds.GetLayer()
            source_srs = source_layer.GetSpatialRef()

            # Create the destination data source
            x_res = int((bounds[0][1] - bounds[0][0]) / pixel_size)
            y_res = int((bounds[1][1] - bounds[1][0]) / pixel_size)

            driver:gdal.Driver
            driver = gdal.GetDriverByName('GTiff')
            target_ds = driver.Create(str(fn_out), x_res, y_res, 1, num_type)

            target_ds:gdal.Dataset
            band:gdal.Band
            target_ds.SetGeoTransform((bounds[0][0], pixel_size, 0, bounds[1][1], 0, -pixel_size))
            band = target_ds.GetRasterBand(1)
            band.SetNoDataValue(NoData_value)

            target_ds.SetProjection(source_srs.ExportToWkt())

            # Rasterize
            gdal.RasterizeLayer(target_ds,
                                [1], source_layer,
                                options = ["ALL_TOUCHED=TRUE", "ATTRIBUTE=Mapping"])

            target_ds = None

            return fn_out

        except:
            logging.error('Error in rasterization')
            return -2


class  DlgMapWalous2Manning(wx.Dialog):
    """ Modal dialog for mapping WALOUS value to another ones """

    def __init__(self, parent, title:str = _("Mapping WALOUS value to ..."), which:Literal['UTS_MAJ_NIV1', 'UTS_MAJ_NIV2', 'OCS_MANNING', 'OCS_HYDROLOGY'] = 'UTS_MAJ_NIV1'):

        super(DlgMapWalous2Manning, self).__init__(parent, title=title, size=(450, 400))

        panel = wx.Panel(self)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._table = wx.grid.Grid(panel)

        if which == 'UTS_MAJ_NIV1':
            self._table.CreateGrid(len(WALOUS_UTS_MAJ_NIV1), 3)
            self._table.SetColLabelValue(0, _("Name"))
            self._table.SetColLabelValue(1, _("Value - UTS"))
            self._table.SetColLabelValue(2, _("Manning 'n'"))
            self._table.HideRowLabels()

            for i, (k, v) in enumerate(WALOUS_UTS_MAJ_NIV1.items()):
                self._table.SetCellValue(i, 0, str(k))
                self._table.SetCellValue(i, 1, str(v))
                self._table.SetCellValue(i, 2, str(WALOUS_UTS2MANNING_MAJ_NIV1[v]))
                self._table.SetCellAlignment(i, 1, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                self._table.SetCellAlignment(i, 2, wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        elif which == 'UTS_MAJ_NIV2':
            self._table.CreateGrid(len(WALOUS_UTS_MAJ_NIV2), 3)
            self._table.SetColLabelValue(0, _("Name"))
            self._table.SetColLabelValue(1, _("Value - UTS"))
            self._table.SetColLabelValue(2, _("Manning 'n'"))
            self._table.HideRowLabels()

            for i, (k, v) in enumerate(WALOUS_UTS_MAJ_NIV2.items()):
                self._table.SetCellValue(i, 0, str(k))
                self._table.SetCellValue(i, 1, str(v))
                self._table.SetCellValue(i, 2, str(WALOUS_UTS2MANNING_MAJ_NIV2[v]))
                self._table.SetCellAlignment(i, 1, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                self._table.SetCellAlignment(i, 2, wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        elif which == 'OCS_MANNING':
            self._table.CreateGrid(len(WALOUS_OCS2MANNING), 3)
            self._table.SetColLabelValue(0, _("Name"))
            self._table.SetColLabelValue(1, _("Value - OCS"))
            self._table.SetColLabelValue(2, _("Manning 'n'"))
            self._table.HideRowLabels()
            for i, (k, v) in enumerate(WALOUS_OCS.items()):
                self._table.SetCellValue(i, 0, str(k))
                self._table.SetCellValue(i, 1, str(v))
                self._table.SetCellValue(i, 2, str(WALOUS_OCS2MANNING[v]))
                self._table.SetCellAlignment(i, 1, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                self._table.SetCellAlignment(i, 2, wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        elif which == 'OCS_HYDROLOGY':
            self._table.CreateGrid(len(WALOUS_OCS2HYDROLOGY), 3)
            self._table.SetColLabelValue(0, _("Name"))
            self._table.SetColLabelValue(1, _("Value - OCS"))
            self._table.SetColLabelValue(2, _("LandUse - Hydrology"))
            self._table.HideRowLabels()
            for i, (k, v) in enumerate(WALOUS_OCS2HYDROLOGY.items()):
                self._table.SetCellValue(i, 0, str(k))
                self._table.SetCellValue(i, 1, str(v))
                self._table.SetCellValue(i, 2, str(WALOUS_OCS2HYDROLOGY[v]))
                self._table.SetCellAlignment(i, 1, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                self._table.SetCellAlignment(i, 2, wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        self._table.SetColFormatFloat(1, 2, 0)
        self._table.SetColFormatFloat(2, 6, 4)
        self._table.SetColSize(0, 250)
        self._table.SetColSize(1, 50)
        self._table.SetColSize(2, 100)


        sizer.Add(self._table, 1, wx.EXPAND)
        panel.SetSizer(sizer)

        sizer_btns = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK, _("OK"))
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, _("Cancel"))
        sizer_btns.Add(btn_ok, 0, wx.ALL, 5)
        sizer_btns.Add(btn_cancel, 0, wx.ALL, 5)

        sizer.Add(sizer_btns, 0, wx.ALIGN_CENTER)

        self.Bind(wx.EVT_BUTTON, self.on_ok, btn_ok)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, btn_cancel)

        self.Center()

    def on_ok(self, event):
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def get_mapping(self) -> dict:

        retdict = {}

        try:
            for i in range(self._table.GetNumberRows()):
                retdict[float(self._table.GetCellValue(i, 1))] = float(self._table.GetCellValue(i, 2))
        except:
            retdict = -1
            logging.error('Error in getting mapping')

        return retdict

class  DlgMapWalousOCS2Manning(DlgMapWalous2Manning):
    """ Modal dialog for mapping WALOUS value to another ones

    This dialog is used to map WALOUS values to hydrology values.
    It inherits from DlgMapWalous2Manning and overrides the initialization
    to set the correct column labels and values.
    """

    def __init__(self, parent, title:str = _("Mapping WALOUS value to ...")):

        super(DlgMapWalousOCS2Manning, self).__init__(parent, title= title, which='OCS_MANNING')

        self._table.SetColLabelValue(2, _("Land Use - OCS"))

        for i, (k, v) in enumerate(WALOUS_OCS2MANNING.items()):
            self._table.SetColLabelValue(1, _("Value - OCS"))
            self._table.SetCellValue(i, 2, str(v))

class  DlgMapWalous2Hydrology(DlgMapWalous2Manning):
    """ Modal dialog for mapping WALOUS value to another ones

    This dialog is used to map WALOUS values to hydrology values.
    It inherits from DlgMapWalous2Manning and overrides the initialization
    to set the correct column labels and values.
    """

    def __init__(self, parent, title:str = _("Mapping WALOUS value to ...")):

        super(DlgMapWalous2Hydrology, self).__init__(parent, title= title, which='OCS_HYDROLOGY')

        self._table.SetColLabelValue(2, _("Land Use - OCS"))

        for i, (k, v) in enumerate(WALOUS_OCS2HYDROLOGY.items()):
            self._table.SetColLabelValue(1, _("Value - OCS"))
            self._table.SetCellValue(i, 2, str(v))

class Walous_UTS_Legend(wx.Dialog):
    """ Show the legend of WALOUS """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw, size = (400, 650))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._text_v1 = wx.StaticText(panel, label=_("WALOUS MAJ_NIV1"))
        self._text_v2 = wx.StaticText(panel, label=_("WALOUS MAJ_NIV2"))

        self._legend_v1 = wx.grid.Grid(panel)
        self._legend_v1.CreateGrid(len(WALOUS_UTS_MAJ_NIV1), 3)
        self._legend_v1.SetColSize(0, 200)
        self._legend_v1.SetColLabelValue(0, _("Name"))
        self._legend_v1.SetColLabelValue(1, _("Value"))
        self._legend_v1.SetColLabelValue(2, _("Color"))
        self._legend_v1.HideRowLabels()

        for i, (k, v) in enumerate(WALOUS_UTS_MAJ_NIV1.items()):
            self._legend_v1.SetCellValue(i, 0, str(k))
            self._legend_v1.SetCellValue(i, 1, str(v))
            self._legend_v1.SetCellBackgroundColour(i, 2, WALOUS_UTS_COLORMAP_MAJ_NIV1[v])

        self._legend_v2 = wx.grid.Grid(panel)
        self._legend_v2.CreateGrid(len(WALOUS_UTS_MAJ_NIV2), 3)
        self._legend_v2.SetColLabelValue(0, _("Name"))
        self._legend_v2.SetColSize(0, 200)
        self._legend_v2.SetColLabelValue(1, _("Value"))
        self._legend_v2.SetColLabelValue(2, _("Color"))
        self._legend_v2.HideRowLabels()

        for i, (k, v) in enumerate(WALOUS_UTS_MAJ_NIV2.items()):
            self._legend_v2.SetCellValue(i, 0, str(k))
            self._legend_v2.SetCellValue(i, 1, str(v))
            self._legend_v2.SetCellBackgroundColour(i, 2, WALOUS_UTS_COLORMAP_MAJ_NIV2[v])

        sizer.Add(self._text_v1, 0, wx.EXPAND, border=5)
        sizer.Add(self._legend_v1, 1, wx.EXPAND, border=5)
        sizer.Add(self._text_v2, 0, wx.EXPAND, border=5)
        sizer.Add(self._legend_v2, 1, wx.EXPAND, border=5)

        panel.SetSizer(sizer)
        self.Center()

        self.Show()

    def __del__(self):
        self.Destroy()

    def close(self):
        self.Destroy()

class Walous_OCS_Legend(wx.Dialog):
    """ Show the legend of WALOUS OCS """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw, size = (400, 650))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._text = wx.StaticText(panel, label=_("WALOUS OCS"))

        self._legend = wx.grid.Grid(panel)
        self._legend.CreateGrid(len(WALOUS_OCS_COLORMAP), 3)
        self._legend.SetColSize(0, 200)
        self._legend.SetColLabelValue(0, _("Name"))
        self._legend.SetColLabelValue(1, _("Value"))
        self._legend.SetColLabelValue(2, _("Color"))
        self._legend.HideRowLabels()

        for i, (k, v) in enumerate(WALOUS_OCS_COLORMAP.items()):
            self._legend.SetCellValue(i, 0, str(k))
            self._legend.SetCellValue(i, 1, str(v))
            self._legend.SetCellBackgroundColour(i, 2, v)

        sizer.Add(self._text, 0, wx.EXPAND, border=5)
        sizer.Add(self._legend, 1, wx.EXPAND, border=5)

        panel.SetSizer(sizer)
        self.Center()

        self.Show()

    def __del__(self):
        self.Destroy()

    def close(self):
        self.Destroy()


def get_array_WALOUS_OCS(fname:Path, spatial_res:float, bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]]) -> Union[WolfArray, None]:
    """ Get WALOUS OCS as WolfArray

    :param fname: path to the WALOUS OCS file
    :param spatial_res: desired spatial resolution (in m)
    :param bounds: [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]
    :return: WolfArray or None if error
    """

    if not fname.exists():
        logging.error(_('WALOUS OCS file not found: {}').format(fname))
        return None

    # Convert bounds to [[xmin, xmax], [ymin, ymax]] if needed
    if len(bounds)==4:
        bounds = [[bounds[0], bounds[2]], [bounds[1], bounds[3]]]

    # Convert bvounds to list to be able to modify it
    bounds = [list(bounds[0]), list(bounds[1])]

    bounds_copy = [list(bounds[0]), list(bounds[1])]

    header_OCS = header_wolf.read_header(fname)
    if header_OCS.dx != spatial_res:
        # Adapt bounds to ensure that the rebin will be correct.
        # If spatial_res is a multiple of header_OCS.dx, no need to change bounds.
        # If not, change the bounds to ensure that the crop will include data in all footprints.

        if (bounds[0][0] - header_OCS.origx) % header_OCS.dx != 0:
            bounds[0][0] = header_OCS.origx + ((bounds[0][0] - header_OCS.origx) // header_OCS.dx) * header_OCS.dx
        if (bounds[0][1] - bounds[0][0]) % header_OCS.dx != 0:
            bounds[0][1] = bounds[0][0] + ((bounds[0][1] - bounds[0][0]) // header_OCS.dx + 1) * header_OCS.dx
        if (bounds[1][0] - header_OCS.origy) % header_OCS.dy != 0:
            bounds[1][0] = header_OCS.origy + ((bounds[1][0] - header_OCS.origy) // header_OCS.dy) * header_OCS.dy
        if (bounds[1][1] - bounds[1][0]) % header_OCS.dy != 0:
            bounds[1][1] = bounds[1][0] + ((bounds[1][1] - bounds[1][0]) // header_OCS.dy + 1) * header_OCS.dy

    locwalous = WolfArray(fname=fname, crop = [bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]])

    if locwalous.dx != spatial_res:
        locwalous.rebin(spatial_res / locwalous.dx, operation='min')
        logging.info(_('Rebin to {} m because original data are {} m').format(spatial_res, locwalous.dx))
        locwalous = WolfArray(mold=locwalous, crop = bounds_copy)

    return locwalous

def get_array_WALOUS_OCS_2023_10m(spatial_res:float, bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]]) -> Union[WolfArray, None]:
    """ Get WALOUS OCS 2023 as WolfArray

    :param spatial_res: desired spatial resolution (in m)
    :param bounds: [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]
    :return: WolfArray or None if error
    """

    from wolfhece.pydownloader import toys_dataset

    fname = toys_dataset(dir='Walous_OCS', file='WALOUS_2023_lbt72_10m.tif')

    return get_array_WALOUS_OCS(fname, spatial_res, bounds)

def get_array_WALOUS_OCS_2023_4m(spatial_res:float, bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]]) -> Union[WolfArray, None]:
    """ Get WALOUS OCS 2023 as WolfArray

    :param spatial_res: desired spatial resolution (in m)
    :param bounds: [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]
    :return: WolfArray or None if error
    """

    from wolfhece.pydownloader import toys_dataset

    fname = toys_dataset(dir='Walous_OCS', file='WALOUS_2023_lbt72_4m.tif')

    return get_array_WALOUS_OCS(fname, spatial_res, bounds)

def get_array_WALOUS_OCS_2020_10m(spatial_res:float, bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]]) -> Union[WolfArray, None]:
    """ Get WALOUS OCS 2020 as WolfArray

    :param spatial_res: desired spatial resolution (in m)
    :param bounds: [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]
    :return: WolfArray or None if error
    """

    from wolfhece.pydownloader import toys_dataset

    fname = toys_dataset(dir='Walous_OCS', file='WALOUS_2020_lbt72_10m.tif')

    return get_array_WALOUS_OCS(fname, spatial_res, bounds)

def get_array_WALOUS_OCS_2020_4m(spatial_res:float, bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]]) -> Union[WolfArray, None]:
    """ Get WALOUS OCS 2020 as WolfArray

    :param spatial_res: desired spatial resolution (in m)
    :param bounds: [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]
    :return: WolfArray or None if error
    """

    from wolfhece.pydownloader import toys_dataset

    fname = toys_dataset(dir='Walous_OCS', file='WALOUS_2020_lbt72_4m.tif')

    return get_array_WALOUS_OCS(fname, spatial_res, bounds)

def get_array_WALOUS_UTS(fname:Path, fnout:Path, spatial_res:float, bounds:Union[list[float, float, float, float],list[list[float, float], list[float, float]]], which:Literal['UTS_MAJ_NIV1', 'UTS_MAJ_NIV2'] = 'UTS_MAJ_NIV1') -> Union[WolfArray, None]:
    """ Get WALOUS UTS as WolfArray

    :param fname: path to the WALOUS UTS file
    :param spatial_res: desired spatial resolution (in m)
    :param bounds: [xmin, ymin, xmax, ymax] or [[xmin, xmax], [ymin, ymax]]
    :param which: which level to use ('UTS_MAJ_NIV1' or 'UTS_MAJ_NIV2')
    :return: WolfArray or None if error
    """

    fname = Path(fname)
    fnout = Path(fnout)

    if not fname.exists():
        logging.error(_('WALOUS UTS file not found: {}').format(fname))
        return None

    # Convert bounds to [[xmin, xmax], [ymin, ymax]] if needed
    if len(bounds)==4:
        bounds = [[bounds[0], bounds[2]], [bounds[1], bounds[3]]]

    # Convert bvounds to list to be able to modify it
    bounds = [list(bounds[0]), list(bounds[1])]

    bounds_copy = [list(bounds[0]), list(bounds[1])]

    locwalous = Walous_data(fname.parent, fname.name, extension=fname.suffix, bounds=bounds)
    ret = locwalous.rasterize(bounds=bounds, layer= which, fn_out=fnout.with_suffix('.tif'), pixel_size=spatial_res)

    ret = Path(ret)

    if ret.exists():
        locwalous_array = WolfArray(fname=ret)
        return locwalous_array
    else:
        return None