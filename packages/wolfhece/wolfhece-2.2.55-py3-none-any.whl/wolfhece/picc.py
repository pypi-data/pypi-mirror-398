"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import geopandas as gpd
from pathlib import Path
from typing import List, Union
from shapely.geometry import Polygon, Point
import logging
import wx
import geopandas as gpd
import numpy as np
from .PyTranslate import _
from .PyVertexvectors import Zones, zone, vector, wolfvertex
from .PyVertex import cloud_vertices, getRGBfromI, getIfromRGB
from .drawing_obj import Element_To_Draw
from .wolf_array import WolfArray

def bbox_creation(study_area_path):
    
    gdf = gpd.read_file(study_area_path)
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    minx, miny, maxx, maxy = bounds

    points = [
        (minx, miny),  # coin inférieur gauche
        (minx, maxy),  # coin supérieur gauche
        (maxx, maxy),  # coin supérieur droit
        (maxx, miny),  # coin inférieur droit
        (minx, miny)   # contour fermé
    ]
    bbox = Polygon(points)
    return bbox

def adding_layer_to_zone(fn:Path, bbox:Polygon = None, ZonesPicc: Zones = None):
    """
    Add other layers informations to the picc zones
    ! Need GEOREF_ID as principal "name" of the zone !
    """
    content = gpd.read_file(fn, bbox=bbox)
    if bbox is not None:
        # filter content
        content = content.cx[bbox.bounds[0]:bbox.bounds[2], bbox.bounds[1]:bbox.bounds[3]]
        
    for row in content.iterrows(): #lire picc
        _, row = row
        keys = list(row.keys())
        keys.remove('geometry') #already into vectors (.myvectors)
        keys = ['GEOREF_ID', 'NATUR_CODE', 'NATUR_DESC']
        for zones in ZonesPicc.myzones: #lire Zones
            for vector in zones.myvectors: 
                if str(vector) == str(row['GEOREF_ID']) : #si le même id, alors compléter
                    for key in keys:
                        read_value = []
                        read_value.append(row[key])
                        arr = np.array(read_value, dtype=str)
                        zones.add_values(key=str(key), values=arr)
    return print("Traitement des layers spécifiques du PICC terminé")
    
class Picc_data(Element_To_Draw):
    """
    Read and show PICC data -- see https://geoportail.wallonie.be/georeferentiel/PICC
    """

    def __init__(self,
                 idx:str = '',
                 plotted:bool = True,
                 mapviewer = None,
                 need_for_wx:bool = False,
                 data_dir:Path = Path(r'./data/PICC'),
                 bbox:Union[Polygon, list[float]] = None,
                 filename_vector:str='PICC_Vesdre.shp',
                 filename_point:str='PICC_Vesdre_points.shp') -> None:

        super().__init__(idx = idx, plotted = plotted, mapviewer = mapviewer, need_for_wx= need_for_wx)

        self.data_dir = data_dir
        self._filename_vector = filename_vector
        self._filename_points = filename_point
        self.zones = None
        self.cloud = None
        self._colors = {'Habitation': [255, 0, 0], 'Annexe': [0, 255, 0], 'Culture, sport ou loisir': [0, 0, 255], 'Autre': [10, 10, 10]}

        self.active_vector = None
        self.active_zone = None

        return None

    def read_data(self, data_dir:Path = None, bbox:Union[Polygon, list[float]] = None, colorize:bool = True) -> None:
        """
        Read data from PICC directory

        :param data_dir: directory where PICC data are stored
        :param bbox: bounding box to select data

        """
        if data_dir is None:
            data_dir = self.data_dir

        data_dir = Path(data_dir)

        datafile = data_dir / self._filename_vector

        if datafile.exists() and datafile.is_file():
            self.zones = Zones(data_dir / self._filename_vector, bbox = bbox, mapviewer=self.mapviewer, colors= self._colors)
        else:
            logging.info(_('File not found : {}').format(datafile))

            if self.mapviewer is not None:
                dlg = wx.SingleChoiceDialog(None, _('Would you like to select a Shape file or a GDB database ?'), _('Choose data source'), ['Shape file/GPKG', 'GDB database'], wx.CHOICEDLG_STYLE)
                ret = dlg.ShowModal()

                if ret == wx.ID_CANCEL:
                    dlg.Destroy()

                choice = dlg.GetStringSelection()
                dlg.Destroy()

                if choice == 'Shape file/GPKG':
                    with wx.FileDialog(None, _('Select a file'), wildcard="Shapefile (*.shp)|*.shp|Gpkg (*.gpkg)|*.gpkg", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

                        if fileDialog.ShowModal() == wx.ID_CANCEL:
                            return

                        pathname = fileDialog.GetPath()

                        try:
                            self.data_dir = Path(pathname).parent
                            data_dir = self.data_dir
                            self._filename_vector = Path(pathname).name
                            self.zones = Zones(pathname, bbox = bbox, mapviewer=self.mapviewer, parent=self, colors=self._colors)
                        except:
                            logging.error(_('File not found : {}').format(pathname))

                elif choice == 'GDB database':
                    with wx.DirDialog(None, _("Choose a directory"), style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dirDialog:
                        if dirDialog.ShowModal() == wx.ID_CANCEL:
                            return

                        pathname = dirDialog.GetPath()

                        try:
                            self.data_dir = Path(pathname).parent
                            data_dir = self.data_dir
                            self._filename_vector = ''
                            self.zones = Zones(pathname, bbox = bbox, mapviewer=self.mapviewer, parent=self, colors= self._colors)

                        except:
                            logging.error(_('Dirrectory not a gdb : {}').format(pathname))

        if self._filename_points != '':
            pointfile = data_dir / self._filename_points

            if pointfile.exists():
                self.cloud = cloud_vertices(data_dir / self._filename_points, bbox = bbox, mapviewer=self.mapviewer)
                self.cloud.myprop.width = 3
                self.cloud.myprop.color = getIfromRGB([0, 0, 255])
            else:
                logging.error(_('Point file not found : {}').format(pointfile))
                
                if self.mapviewer is not None:
                    dlg = wx.FileDialog(None, _('Select a point file'), wildcard="Shapefile (*.shp)|*.shp|Gpkg (*.gpkg)|*.gpkg", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
                    if dlg.ShowModal() == wx.ID_CANCEL:
                        dlg.Destroy()
                        return

                    pathname = dlg.GetPath()
                    dlg.Destroy()

                    try:
                        self._filename_points = Path(pathname)

                        self.cloud = cloud_vertices(pathname, bbox = bbox, mapviewer=self.mapviewer)
                        self.cloud.myprop.width = 3
                        self.cloud.myprop.color = getIfromRGB([0, 0, 255])
                    except:
                        logging.error(_('File not found : {}').format(pathname))

        

    def read_vectors_cloud_picc(self, data_dir:Path = None, path_vector:str = r"PICC_Vesdre.shp", path_points:str = r"PICC_Vesdre_points.shp", 
                                bbox:Union[Polygon, list[float]] = None, column:str = "GEOREF_ID", additional_layers:bool = None) -> None:
        """
        Complete reading of the PICC files : vectors (.shp) and clouds (.shp). For the vectors, read any attributes that exist, a priori :
        ['NATUR_CODE', 'NATUR_DESC', 'PRECIS_XY', 'PRECIS_Z', 'TECH_LEVE','DATE_LEVE', 'DATE_CREAT', 'DATE_MODIF', 'DATE_TRANS', 'CODE_WALTO']
        Pay attention, this uses directly Zone() but may be slow for a large raster. Use "create_zone_picc"
        """
        if data_dir is None:
            data_dir = self.data_dir
            
        logging.info('*PICC reading and Zone creation')
        self._filename_vector = path_vector 
        vector_file = data_dir / self._filename_vector
        if  vector_file.exists():
            #Charger la Zones contenants les zone (GEOREF_ID, vectors)
            self.zones = Zones(data_dir / self._filename_vector, bbox = bbox, colname = column)
            #Ajouter des attributs du PICC ['GEOREF_ID', 'NATUR_CODE', 'NATUR_DESC', 'PRECIS_XY', 'PRECIS_Z', 'TECH_LEVE', 'DATE_LEVE', 'DATE_CREAT', 'DATE_MODIF', 'DATE_TRANS', 'CODE_WALTO']
            if additional_layers == True:
                adding_layer_to_zone(data_dir / self._filename_vector, bbox = bbox, ZonesPicc=self.zones)
        else :
            print('Not existing vector file at the given paths!')
            self.zones = None
    
        self._filename_points = path_points
        pointfile = data_dir / self._filename_points
        
        #if pointfile.exists():
        #    self.cloud = cloud_vertices(data_dir / self._filename_points, bbox = bbox)
        #else:
        #    self.cloud = None
        #    print('Not existing point file at the given paths!')
        
        return self.zones, self.cloud
        
    def filter_by_name(self, path_vector:str, path_points:str, name:str="Habitation", 
                        bbox:Union[Polygon, list[float]] = None):
        """
        Filter the PICC by a name of 'NATUR_DESC' attribute, and only keeps properties ['GEOREF_ID', 'NATUR_CODE', 'NATUR_DESC']
        """
        
        if  path_vector.exists():
            gdf = gpd.read_file(path_vector, include_fields=["geometry", 'GEOREF_ID', 'NATUR_CODE', 'NATUR_DESC'], bbox=bbox)
            self.gdf_filtered = gdf[gdf["NATUR_DESC"] == name]
            
        else :
            print('Not existing vector file at the given paths!')
            self.zones = None
    
        #self._filename_points = path_points
        #pointfile = data_dir / self._filename_points

        return self.gdf_filtered
    
    def create_zone_picc(self, path_vector:str = r"PICC_Vesdre.shp", path_points:str = r"PICC_Vesdre_points.shp", name:str="Habitation",
                                bbox:Union[Polygon, list[float]] = None, column:str = "GEOREF_ID"):
        
        """Complete reading of the PICC files : vectors (.shp) and clouds (.shp). For the vectors, read any attributes that exist, among
        ['NATUR_CODE', 'NATUR_DESC', 'PRECIS_XY', 'PRECIS_Z', 'TECH_LEVE','DATE_LEVE', 'DATE_CREAT', 'DATE_MODIF', 'DATE_TRANS', 'CODE_WALTO']
        For now, path_points not used but may be useful later
        """
        
        #Filtering from the start
        self.gdf_filtered = self.filter_by_name(path_vector, path_points, name, bbox)
        
        #Creating the Zone with desired attributes
        Zones_picc = Zones()
        Zones_picc.import_GeoDataFrame(self.gdf_filtered, bbox, colname=column)
        return Zones_picc
                
                        
    
    
    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """ Plot data in OpenGL context

        :param sx: x scaling factor
        :param sy: y scaling factor
        :param xmin: minimum x value
        :param ymin: minimum y value
        :param xmax: maximum x value
        :param ymax: maximum y value
        :param size: size of the points
        """

        if self.zones is not None:
           self.zones.plot(sx=sx, sy=sy, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, size=size)
        if self.cloud is not None:
            self.cloud.plot(sx=sx, sy=sy, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, size=size)


    def check_plot(self):
        """ Generic function responding to check operation from mapviewer """

        super().check_plot()

        from .PyDraw import WolfMapViewer
        self.mapviewer:WolfMapViewer

        if self.mapviewer is not None:

            xmin, xmax, ymin, ymax = self.mapviewer.xmin, self.mapviewer.xmax, self.mapviewer.ymin, self.mapviewer.ymax

            bbox = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)])
            self.read_data(bbox = bbox)

            self.mapviewer.Refresh()

    def uncheck_plot(self, unload: bool = True, reset_filename: bool = False):
        """ Generic function responding to uncheck operation from mapviewer """

        super().uncheck_plot(unload = unload)

        if unload:
            self.zones = None
            self.cloud = None

        if reset_filename:
            self._filename_vector = ''
            self._filename_points = ''
            self.data_dir = Path(r'./data/PICC')

    def show_properties(self):
        """ Showing properties of the object """

        if self.zones is not None:
            self.zones.show_properties()
        else:
            logging.warning(_('No zones properties to show !'))

        if self.cloud is not None:
            self.cloud.show_properties()
        else:
            logging.warning(_('No cloud properties to show !'))

    def Active_vector(self, vector_to_activate:vector):
        """ Activate a vector """

        self.active_vector = vector_to_activate
        self.active_zone = vector_to_activate.parentzone

        if self.mapviewer is not None:
            self.mapviewer.Active_vector(vector_to_activate)

        else:
            logging.warning(_('No mapviewer to activate vector !'))

    def Active_zone(self, zone_to_activate:zone):
        """ Activate a zone """

        self.active_zone = zone_to_activate

        if len(zone_to_activate.myvectors) > 0:
            self.active_vector = zone_to_activate.myvectors[0]

        if self.mapviewer is not None:
            self.mapviewer.Active_vector(self.active_vector)

        else:
            logging.warning(_('No mapviewer to activate zone !'))
    
    def extrude_polygons(self, dest_array):
        """ Extrude the active polygon along the z-axis """

        if self.zones is not None:
            for curzone in self.zones.myzones:
                dest_array.interpolate_on_polygons(curzone, keep = 'above')

class Cadaster_data(Picc_data):
    """ Read and show cadaster data """

    def __init__(self,
                 idx:str = '',
                 plotted:bool = True,
                 mapviewer = None,
                 need_for_wx:bool = False,
                 data_dir:Path = Path(r'./data/Cadastre'),
                 bbox:Union[Polygon, list[float]] = None) -> None:

        super().__init__(idx = idx, plotted = plotted, mapviewer = mapviewer, need_for_wx= need_for_wx, data_dir = data_dir, bbox = bbox)

        self._filename_vector = 'Cadastre.shp'
        self._filename_points = ''

    def read_data(self, data_dir: Path = None, bbox:Union[Polygon, List[float]] = None, colorize: bool = True) -> None:

        super().read_data(data_dir, bbox, colorize=False)
        if self.zones is not None:
            self.zones.set_width(3)
