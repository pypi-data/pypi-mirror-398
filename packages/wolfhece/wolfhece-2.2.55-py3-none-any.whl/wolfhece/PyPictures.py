# from PIL import Image,ExifTags
"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import os.path as path
from os import curdir, listdir
from exif import Image
from osgeo import ogr
from osgeo import osr
import wx
from pathlib import Path
import logging
import PIL.Image
from PIL import ExifTags

from shapely.geometry import Polygon
import numpy as np

from .PyTranslate import _
from .PyVertexvectors import Zones, zone, vector, wolfvertex as wv
from .Coordinates_operations import transform_coordinates

"""
Ajout des coordonnées GPS d'une photo en Lambert72 si n'existe pas

!!! A COMPLETER !!!

"""
# class Picture(wx.Frame):

#     def __init__(self, *args, **kw):
#         super().__init__(*args, **kw)

def find_gps_in_file(picture: str | Path) -> tuple[float, float, float]:
    """
    Find GPS coordinates in the picture file.
    Returns a tuple (latitude, longitude, altitude).
    If not found, returns (None, None, None).
    """
    try:
        with PIL.Image.open(picture) as img:
            if 'gps_latitude' in img.info and 'gps_longitude' in img.info:
                lat = img.info['gps_latitude']
                lon = img.info['gps_longitude']
                alt = img.info.get('gps_altitude', 0.0)
                return lat, lon, alt
            else:
                # Try to read EXIF data
                exif_data = img._getexif()
                if exif_data is not None:
                    for tag, value in exif_data.items():
                        if ExifTags.TAGS.get(tag) == 'GPSInfo':
                            gps_info = value

                            allgps = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_info.items() if k in ExifTags.GPSTAGS}

                            lat = allgps['GPSLatitude']
                            lon = allgps['GPSLongitude']
                            alt = allgps['GPSAltitude']
                            if lat and lon:
                                return lat, lon, alt

    except Exception as e:
        logging.error(f"Error reading GPS data from {picture}: {e}")
    return None, None, None

def find_exif_in_file(picture: str | Path) -> dict:
    """
    Find EXIF data in the picture file.
    Returns a dictionary of EXIF data.
    If not found, returns an empty dictionary.
    """
    try:
        with PIL.Image.open(picture) as img:
            exif_data = img._getexif()
            if exif_data is not None:
                return {ExifTags.TAGS.get(tag, tag): value for tag, value in exif_data.items()}
    except Exception as e:
        logging.debug(f"Error reading EXIF data from {picture}: {e}")
    return {}

def find_Lambert72_in_file(picture: str | Path) -> tuple[float, float]:
    """
    Find Lambert72 coordinates in the picture file.
    Returns a tuple (Lambert72X, Lambert72Y).
    If not found, returns (None, None).
    """
    try:
        with PIL.Image.open(picture) as img:
            x = img.get('Lambert72X')
            y = img.get('Lambert72Y')
            if x is not None and y is not None:
                return x, y
    except Exception as e:
        logging.debug(f"Error reading Lambert72 data from {picture}: {e}")
    return None, None

class PictureCollection(Zones):
    """
    PictureCollection is a collection of pictures, inheriting from Zones.
    """

    def __init__(self,
                 filename:str | Path='',
                 ox:float=0.,
                 oy:float=0.,
                 tx:float=0.,
                 ty:float=0.,
                 parent=None,
                 is2D=True,
                 idx: str = '',
                 plotted: bool = True,
                 mapviewer=None,
                 need_for_wx: bool = False,
                 bbox:Polygon = None,
                 find_minmax:bool = True,
                 shared:bool = False,
                 colors:dict = None):

        super().__init__(filename=filename,
                         ox=ox,
                         oy=oy,
                         tx=tx,
                         ty=ty,
                         parent=parent,
                         is2D=is2D,
                         idx=idx,
                         plotted=plotted,
                         mapviewer=mapviewer,
                         need_for_wx=need_for_wx,
                         bbox=bbox,
                         find_minmax=find_minmax,
                         shared=shared,
                         colors=colors)

        self._default_size = 200 # Taille par défaut des photos in meters

    def hide_all_pictures(self):
        """
        Hide all pictures in the collection.
        """
        for zone in self.myzones:
            for vector in zone.myvectors:
                vector.myprop.imagevisible = False
        self.reset_listogl()
        self.find_minmax(True)

    def show_all_pictures(self):
        """
        Show all pictures in the collection.
        """
        for zone in self.myzones:
            for vector in zone.myvectors:
                vector.myprop.imagevisible = True
        self.reset_listogl()
        self.find_minmax(True)

    def extract_pictures(self, directory: str | Path):
        """
        Extract all visible pictures from the collection to a directory.
        """
        directory = Path(directory)
        if not directory.exists():
            logging.error(f"Directory {directory} does not exist.")
            return

        import shutil

        for loczone in self.myzones:
            for vector in loczone.myvectors:
                if vector.myprop.imagevisible and vector.myprop.attachedimage:
                    picture_path = Path(vector.myprop.attachedimage)
                    if picture_path.exists():
                        new_path = directory / picture_path.name
                        # copy the picture file to the new path
                        shutil.copy(picture_path, new_path)
                        logging.info(f"Extracted {picture_path} to {new_path}")
                    else:
                        logging.error(f"Picture {picture_path} does not exist.")

        extracted = Zones(idx = 'extract')

        for loczone in self.myzones:
            newzone = zone(name = loczone.myname)

            for vector in loczone.myvectors:
                if vector.myprop.imagevisible and vector.myprop.attachedimage:

                    picture_path = Path(vector.myprop.attachedimage)
                    new_path = directory / picture_path.name
                    newvec = vector.deepcopy()
                    newzone.add_vector(newvec, forceparent=True)
                    newvec.myprop.attachedimage = new_path

            if newzone.nbvectors > 0:
                extracted.add_zone(newzone, forceparent=True)

        extracted.saveas(directory / 'extracted_pictures.vec')

    def add_picture(self, picture: str | Path, x:float = None, y:float = None, name:str='', keyzone:str = None):
        """
        Add a picture to the collection at coordinates (x, y).
        """

        picture = Path(picture)

        if not picture.exists():
            logging.error(f"Picture {picture} does not exist.")
            return

        with PIL.Image.open(picture) as img:
            width, height = img.size
            scale = width / height
            if width > height:
                width = self._default_size
                height = width / scale
            else:
                height = self._default_size
                width = height * scale

        if x is None or y is None:
            x, y = self._find_coordinates_in_file(picture)
        if x is None or y is None:
            logging.error(f"Could not find coordinates in {picture}. Please provide coordinates.")
            return

        if keyzone is None:
            keyzone = _('New gallery')

        if keyzone not in self.mynames:
            self.add_zone(zone(name= keyzone, parent=self))

        if name == '':
            name = picture.stem

        vec = vector(name=name)
        self[keyzone].add_vector(vec, forceparent=True)


        vec.add_vertices_from_array(np.asarray([(x - width /2., y - height /2.),
                                     (x + width /2., y - height /2.),
                                     (x + width /2., y + height /2.),
                                     (x - width /2., y + height /2.)]))

        vec.closed = True

        vec.myprop.image_attached_pointx = x
        vec.myprop.image_attached_pointy = y
        vec.myprop.attachedimage = picture

    def _find_coordinates_in_file(self, picture: str | Path) -> tuple[float, float]:
        """
        Find coordinates in the picture file.
        Returns a tuple (x, y).
        If not found, returns (None, None).
        """
        lat, lon, alt = find_gps_in_file(picture)
        x, y = find_Lambert72_in_file(picture)

        def _santitize_coordinates(coord):
            """
            Sanitize coordinates to ensure they are valid floats.
            Convert tuple with degrees, minutes, seconds to float if needed.
            """
            if isinstance(coord, (list, tuple)):
                try:
                    coord = float(sum(c / (60 ** i) for i, c in enumerate(coord)))
                    return coord
                except (ValueError, TypeError):
                    logging.error(f"Invalid coordinate format: {coord}. Expected a list or tuple of numbers.")
                    return None

            return float(coord)

        if lat is not None and lon is not None and x is None and y is None:
            xy = transform_coordinates(np.asarray([[_santitize_coordinates(lon), _santitize_coordinates(lat)]]), inputEPSG='EPSG:4326', outputEPSG='EPSG:31370')
            return xy[0,0], xy[0,1]
        elif lat is None and lon is None and x is not None and y is not None:
            return x, y
        elif lat is not None and lon is not None and x is not None and y is not None:
            # If both GPS and Lambert72 coordinates are found, prefer Lambert72
            xy = transform_coordinates(np.asarray([[_santitize_coordinates(lon), _santitize_coordinates(lat)]]), inputEPSG='EPSG:4326', outputEPSG='EPSG:31370')
            xtest, ytest = xy[0,0], xy[0,1]
            if abs(x - xtest) < 1e-3 and abs(y - ytest) < 1e-3:
                return x, y
            else:
                logging.warning(f"GPS coordinates ({lat}, {lon}) do not match Lambert72 coordinates ({x}, {y}). Using GPS coordinates.")
                return xtest, ytest
        else:
            logging.error(f"Could not find coordinates in {picture}.")
            return None, None

    def load_from_url_zipfile(self, url: str):
        """
        Load pictures from a zip file at a given URL.
        The zip file should contain images with names that can be used as picture names.
        """

        import requests
        from zipfile import ZipFile
        from io import BytesIO
        from .pydownloader import DATADIR

        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"Failed to download zip file from {url}. Status code: {response.status_code}")
            return

        # Extract images from the zip file and store them ion the DATADIR
        with ZipFile(BytesIO(response.content)) as zip_file:
            zip_file.extractall(DATADIR / 'pictures' / url.split('/')[-1].replace('.zip', ''))
        directory = DATADIR / 'pictures' / url.split('/')[-1].replace('.zip', '')
        if not directory.is_dir():
            logging.error(f"Directory {directory} does not exist after extracting zip file.")
            return

        self.load_from_directory_georef_pictures(directory, keyzone=_('url'))

    def load_from_directory_with_excel(self, excel_file: str | Path, sheet_name: str = 'Pictures'):
        """
        Load pictures from an Excel file.
        The Excel file should have columns for picture path, x, y, and name.
        """
        import pandas as pd

        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        for __, row in df.iterrows():
            picture = row['Picture']
            x = row.get('X', None)
            y = row.get('Y', None)
            name = row.get('Name', '')

            self.add_picture(picture, x, y, name)

    def load_from_directory_georef_pictures(self, directory: str | Path, keyzone: str = None):
        """
        Load pictures from a directory.
        The directory should contain images with names that can be used as picture names.
        """

        directory = Path(directory)
        if not directory.is_dir():
            logging.error(f"Directory {directory} does not exist.")
            return

        if keyzone is None:
            keyzone = _('New gallery')

        if keyzone not in self.mynames:
            self.add_zone(zone(name=keyzone, parent=self))

        for picture in directory.glob('*'):
            if picture.is_file() and picture.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                x,y = self._find_coordinates_in_file(picture)
                if x is None or y is None:
                    logging.error(f"Could not find coordinates in {picture}. Please provide coordinates.")
                    continue
                self.add_picture(picture, keyzone=keyzone)

    def load_from_directory_with_shapefile(self,
                                           directory: str | Path,
                                           shapefile: str | Path = None,
                                           keyzone: str = None):
        """ Load pictures from a directory and associate them with a shapefile. """

        directory = Path(directory)
        if not directory.is_dir():
            logging.error(f"Directory {directory} does not exist.")
            return

        if shapefile is None:
            shapefile = directory / 'SHP'
            # list all shapefiles in the directory
            shapefiles = list(shapefile.glob('*.shp'))
            if not shapefiles:
                logging.error(f"No shapefiles found in {directory}.")
                return
            shapefile = shapefiles[0]
            logging.info(f"Using shapefile {shapefile}.")

        shapefile = Path(shapefile)
        if not shapefile.is_file():
            logging.error(f"Shapefile {shapefile} does not exist.")
            return

        import geopandas as gpd
        gdf = gpd.read_file(shapefile)
        if gdf.empty:
            logging.error(f"Shapefile {shapefile} is empty.")
            return

        possible_columns = ['name', 'path']

        for col in possible_columns:
            for idx, column in enumerate(gdf.columns):
                if col.lower() == column.lower():
                    name_column = column
                    break

        for __, row in gdf.iterrows():
            picture_path = row[name_column]
            if not isinstance(picture_path, str):
                logging.error(f"Invalid picture path in shapefile: {picture_path}")
                continue

            picture_path = Path(picture_path).name

            picture_path = directory / picture_path
            if not picture_path.exists():
                logging.error(f"Picture {picture_path} does not exist.")
                continue

            x, y = row.geometry.x, row.geometry.y

            if x < -100_000. or y < -100_000.:
                logging.warning(f"Invalid coordinates ({x}, {y}) for picture {picture_path}. Skipping.")
                logging.warning(f"Trying to find coordinates in the picture file {picture_path}.")
                x, y = self._find_coordinates_in_file(picture_path)
                if x is None or y is None:
                    continue

            name = picture_path.stem

            self.add_picture(picture_path, x, y, name, keyzone=keyzone)

    def scale_all_pictures(self, scale_factor: float):
        """ Scale all vectors in the collection by a scale factor. """

        for zone in self.myzones:
            for vector in zone.myvectors:
                # Move each point from the centroid to the new position
                centroid = vector.centroid

                for vertex in vector:
                    vertex.x = centroid.x + (vertex.x - centroid.x) * scale_factor
                    vertex.y = centroid.y + (vertex.y - centroid.y) * scale_factor
                vector.reset_linestring()
        self.reset_listogl()
        self.find_minmax(True)

def main():
    # Spatial Reference System
    inputEPSG = 4326 #WGS84
    outputEPSG = 31370 #Lambert72

    # create coordinate transformation
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(inputEPSG)

    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(outputEPSG)

    coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

    dir = path.normpath(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\3 noeuds critiques\tronçon 34')

    for curfile in listdir(dir):
        filename,fileextent = path.splitext(curfile)
        if fileextent.lower()=='.jpg':
            img = Image(path.join(dir,curfile))

            if img.get('Lambert72X'):
                x = img.get('Lambert72X')
                y = img.get('Lambert72Y')

            elif img.get('gps_latitude'):
                lat=img.gps_latitude
                lon=img.gps_longitude
                alt=img.gps_altitude

                # create a geometry from coordinates
                point = ogr.Geometry(ogr.wkbPoint)
                if len(lat)==3:
                    lat = lat[0]+lat[1]/60+lat[2]/(60*60)
                    lon = lon[0]+lon[1]/60+lon[2]/(60*60)
                point.AddPoint(lat, lon)
                # transform point
                point.Transform(coordTransform)
                # print point in EPSG 31370
                print(point.GetX(), point.GetY())
                img.set('Lambert72X',point.GetX())
                img.set('Lambert72Y',point.GetY())

                with open(path.join(dir,'modified_image.jpg'), 'wb') as new_image_file:
                    new_image_file.write(img.get_file())

if __name__ == '__main__':
    main()