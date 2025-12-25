"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from osgeo import gdal
import logging
from pathlib import Path

from .PyTranslate import _
from .wolf_array import WolfArray, WolfArrayMB
from .PyVertexvectors import zone,Zones,vector, wolfvertex


class ImagesTiles(Zones):
    """ Class to manage images tiles.

    Images must be stored in the same directory.
    """

    def __init__(self,
                 filename = '',
                 ox = 0, oy = 0,
                 tx = 0, ty = 0,
                 parent=None, is2D=True,
                 idx = '', plotted = True,
                 mapviewer=None, need_for_wx = False,
                 bbox = None, find_minmax = True,
                 shared = False, colors = None):

        super().__init__(filename, ox, oy, tx, ty, parent, is2D, idx, plotted, mapviewer, need_for_wx, bbox, find_minmax, shared, colors)

    def scan_dir(self, directory:Path, extensions:list[str] = ['tif', 'tiff']):
        """ Scan directory for images tiles.

        :param directory: directory to scan.
        :param extensions: list of extensions to search for.
        """

        self.myzones = []
        for ext in extensions:
            self.myzones += self.scan_dir_ext(directory, ext)

        self.find_minmax(True)

    def scan_dir_ext(self, directory:Path, ext:str, force_visible:bool = False):
        """ Scan directory for images tiles with a specific extension.

        :param directory: directory to scan.
        :param ext: extension to search for.
        """

        all_files = directory.glob(f'*.{ext}')

        zones = []
        for file in all_files:
            try:
                ds:gdal.Dataset
                ds = gdal.Open(str(file))
                if ds is None:
                    logging.error(f'Could not open {file}')
                    continue

                ulx, xres, xskew, uly, yskew, yres  = ds.GetGeoTransform()
                lrx = ulx + (ds.RasterXSize * xres)
                lry = uly + (ds.RasterYSize * yres)

                xmin, xmax = min(ulx, lrx), max(ulx, lrx)
                ymin, ymax = min(uly, lry), max(uly, lry)

                loczone = zone(name = file, parent= self)
                vect = vector(name='image', parentzone=loczone)
                loczone.add_vector(vect)

                vect.myprop.attachedimage = Path(file)
                vect.myprop.imagevisible = True if ds.RasterXSize * ds.RasterYSize < 8_000_000 or force_visible else False

                vect.add_vertex(wolfvertex(xmin, ymin))
                vect.add_vertex(wolfvertex(xmax, ymin))
                vect.add_vertex(wolfvertex(xmax, ymax))
                vect.add_vertex(wolfvertex(xmin, ymax))
                vect.close_force()

                zones.append(loczone)

            except Exception as e:
                logging.error(f'Error while opening {file}: {e}')

        return zones
