from pyproj import Transformer
from pyproj.transformer import TransformerGroup
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from osgeo import gdal
import os
import logging

from .PyTranslate import _

def transform_chunk_coordinates(inputEPSG:str, outputEPSG:str, chunk:np.ndarray):
    """
    Transforms a chunk of coordinates

    :param inputEPSG: input EPSG code (e.g. "EPSG:3812")
    :type inputEPSG: str
    :param outputEPSG: output EPSG code (e.g. "EPSG:31370")
    :type outputEPSG: str
    :param chunk: list of points to be transformed
    :type chunk: np.ndarray
    """
    COO_TRANSFORMER = Transformer.from_crs(inputEPSG, outputEPSG, always_xy=True)
    ret = COO_TRANSFORMER.transform(chunk[:, 0], chunk[:, 1])
    return ret

def transform_coordinates(points:np.ndarray, inputEPSG:str="EPSG:3812", outputEPSG:str="EPSG:31370", chunk_size:int=1000):
    """
        Transforms coordinates in batches using multiprocessing. If more than chunk_size points are provided, the
        function will split the points into chunks and transform them in parallel => requiring in the main script
        to use the statement if __name__ == '__main__':.

    :param points: Array of coordinates to be transformed
    :type points: numpy.ndarray
    :param inputEPSG: (optional) Input EPSG code. Defaults to "EPSG:3812"
    :type inputEPSG: str
    :param outputEPSG: (optional) Output EPSG code. Defaults to "EPSG:31370"
    :type outputEPSG: str
    :param chunk_size: (optional) Size of each batch for transformation. Defaults to 100000
    :type chunk_size: int

    :return numpy.ndarray: Transformed coordinates
    """

    # sanitize inputs
    inputEPSG = str(inputEPSG)
    outputEPSG = str(outputEPSG)

    if not "EPSG" in inputEPSG or not "EPSG" in inputEPSG:
        logging.error(_("EPSG code must be in the format 'EPSG:XXXX'"))
        return

    num_points = len(points)
    results = []

    total_steps = (num_points + chunk_size - 1) // chunk_size

    if total_steps == 1:
        result_x, result_y = transform_chunk_coordinates(inputEPSG, outputEPSG, points)
        return np.vstack((result_x, result_y)).T

    with ProcessPoolExecutor() as executor:
        futures = []
        for i in range(0, num_points, chunk_size):
            chunk = points[i:i + chunk_size]
            futures.append(executor.submit(transform_chunk_coordinates, inputEPSG, outputEPSG, chunk))

        for step, future in enumerate(futures):
            result_x, result_y = future.result()
            results.append(np.vstack((result_x, result_y)).T)

    return np.vstack(results)

def reproject_and_resample_raster(input_raster_path:str, output_raster_path:str,
                                  input_srs:str='EPSG:3812', output_srs:str='EPSG:31370',
                                  resampling_method:str|int=gdal.GRA_Bilinear,
                                  xRes:float=0.5, yRes:float=0.5, debug:bool=False):
    """
    Use gdal to open a tiff raster in a given input EPSG 'inputEPSG' and transforms the raster into another EPSG system 'outputEPSG'.
    The resolution can be forced through xRes and yRes (the origin will be rounded to the nearest multiple of the resolution). The
    resampling method can be chosen among the gdal GRA_* constants (gdal.GRA_Average; gdal.GRA_Bilinear; gdal.GRA_Cubic; gdal.GRA_CubicSpline;
    gdal.GRA_Lanczos; gdal.GRA_Mode; gdal.GRA_NearestNeighbor).

    :param input_raster_path: the path to the input raster file (.tif or .tiff)
    :type input_raster_path: str
    :param output_raster_path: the path to the output raster file (.tif or .tiff) that will be created
    :type output_raster_path: str
    :param input_srs: Input EPSG code. Defaults to Lambert 2008 "EPSG:3812"
    :type input_srs: str
    :param output_srs: Output EPSG code. Defaults to Lambert 72 "EPSG:31370"
    :type output_srs: str
    :param resampling_method: Resampling method. Defaults to gdal.GRA_Bilinear
    :type resampling_method: int, str
    :param xRes: Resolution along X. Defaults to 0.5
    :type xRes: float
    :param yRes: Resolution along Y. Defaults to 0.5
    :type yRes: float
    :param debug: If True, print debug information. Defaults to False
    :type debug: bool
    """
    from osgeo import osr

    # santitize inputs
    input_raster_path = str(input_raster_path)
    output_raster_path = str(output_raster_path)

    # ATTENTION: mask values should be negative in the tiff corresponding to input_raster_path!
    if not(input_raster_path.endswith('.tif') or input_raster_path.endswith('.tiff')):
        logging.error(_("Input raster must be a GeoTIFF file"))
        return
    if not(output_raster_path.endswith('.tif') or output_raster_path.endswith('.tiff')):
        logging.error(_("Output raster must be a GeoTIFF file"))
        return

    # check the output file
    if os.path.exists(output_raster_path):
        try:
            os.remove(output_raster_path)
        except PermissionError as e:
            logging.error(_(f"Permission denied while trying to delete {output_raster_path}. Ensure the file is not open in another program and you have sufficient privileges."))
            return
        except Exception as e:
            logging.error(_(f"An unexpected error occurred while trying to delete {output_raster_path}: {str(e)}"))
            return

    # Open the input raster
    input_raster = gdal.Open(input_raster_path)
    if input_raster is None:
        logging.error(_(f"Unable to open input raster: {input_raster_path}"))
        return

    # Get the source SRS from the input raster
    source_srs = osr.SpatialReference()
    if debug:
        print('Initial projection: ',input_raster.GetProjection())
        print('set projection init: ',int(input_srs.split(':')[1]))
    source_srs.ImportFromEPSG(int(input_srs.split(':')[1]))

    # Create the target SRS
    target_srs = osr.SpatialReference()
    if debug:
        print('set projection out: ',int(output_srs.split(':')[1]))
    target_srs.ImportFromEPSG(int(output_srs.split(':')[1]))

    # Define the options for the reprojection
    # Load the initial array to obtain the origin and the limits
    ulx, xres, xskew, uly, yskew, yres  = input_raster.GetGeoTransform()
    Orig = np.array([[ulx,uly],
                     [ulx+input_raster.RasterXSize*xres, uly+input_raster.RasterYSize*yres]])
    Orig.sort(0)

    # Transform the origin and the limits into the new projection 'Lambert 72'
    Orig_out = transform_coordinates(Orig, inputEPSG=input_srs, outputEPSG=output_srs)

    if xRes is None or xRes <= 0:
        xRes = xres
    if yRes is None or yRes <= 0:
        yRes = yres

    # Round each coordinate to the nearest multiple of the wanted resolution
    Orig_out[:,0] = np.round(Orig_out[:,0]/xRes)*xRes
    Orig_out[:,1] = np.round(Orig_out[:,1]/yRes)*yRes
    if debug:
        print(Orig_out)
        print(tuple(Orig_out.reshape(-1)))

    # Define the reprojection options
    # outputBounds=tuple(Orig_out.reshape(-1)),
    # xRes=xRes, yRes=yRes,
    reproject_options = gdal.WarpOptions(
        outputBounds=tuple(Orig_out.reshape(-1)),  # Output bounds: (minX, minY, maxX, maxY)
        xRes=xRes, yRes=yRes,
        srcSRS=source_srs.ExportToWkt(),
        dstSRS=target_srs.ExportToWkt(),
        resampleAlg=resampling_method
    )

    # Reproject and resample the input raster
    output_raster = gdal.Warp(
        destNameOrDestDS=output_raster_path,
        srcDSOrSrcDSTab=input_raster,
        options=reproject_options
    )

    if output_raster is None:
        logging.error(_(f"Reprojection failed for input raster: {input_raster_path}"))
        return

    # Flush cache to ensure the output is written to disk
    output_raster.FlushCache()

    # Close the datasets IMPORTANT to set to None in order to close them
    input_raster = None
    output_raster = None

    if debug:
        print(f"Reprojection and resampling completed successfully. Output saved to: {output_raster_path}")
