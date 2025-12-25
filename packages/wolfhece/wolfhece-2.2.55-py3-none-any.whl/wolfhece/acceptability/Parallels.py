"""
Author: University of Liege, HECE, LEMA
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""
#import _add_path #AP
from .func import clip_layer, data_modification, vector_to_raster, compute_vulnerability, match_vulnerability2sim, compute_acceptability, shp_to_raster, Accept_Manager
import geopandas as gpd
import multiprocessing
from functools import partial
import os
from pathlib import Path

def parallel_gpd_clip(layer:list[str],
                      file_path:str,
                      Study_Area:str,
                      output_dir:str,
                      number_procs:int = 1):
    """
    Clip the layers to the study area.

    Process the layers in parallel.

    FIXME: The GPKG driver is it totally parallel compliant?

    :param layer: List of layers to clip
    :param file_path: The path to the file
    :param Study_Area: The study area
    :param output_dir: The output directory where the clipped layers are stored
    :param number_procs: The number of processors to use

    """
    file_path = str(file_path)
    Study_Area = str(Study_Area)
    output_dir = str(output_dir)

    if number_procs == 1:

        for curlayer in layer:
            clip_layer(curlayer, file_path, Study_Area, output_dir)

    else:
        pool = multiprocessing.Pool(processes=number_procs)
        prod_x=partial(clip_layer,
                    file_path=file_path,
                    Study_Area=Study_Area,
                    output_dir=output_dir)
        result_list = pool.map(prod_x, layer)
        pool.close()
        pool.join()

def parallel_v2r(manager:Accept_Manager,
                 attribute:str,
                 pixel:float,
                 number_procs:int = 1,
                 convert_to_sparse:bool = False):
    """
    Convert the vector layers to raster.

    Process the layers in parallel.

    :remark: It is permitted to execute this function in multiprocessing because we write separate files.

    :param manager: The Accept_Manager object
    :param attribute: The attribute to convert to raster
    :param pixel: The pixel size of the raster
    :param number_procs: The number of processors to use

    """

    attribute = str(attribute)
    layers = manager.get_layers_in_codevulne()

    if number_procs == 1:
        result_list=[]
        for curlayer in layers:
            result_list.append(vector_to_raster(curlayer, manager, attribute, pixel, convert_to_sparse))

    else:
        pool = multiprocessing.Pool(processes=number_procs)
        prod_x=partial(vector_to_raster,
                       manager=manager,
                       attribute=attribute,
                       pixel_size=pixel,
                       convert_to_sparse=convert_to_sparse)

        result_list = pool.map(prod_x, layers)
        pool.close()
        pool.join()

def parallel_datamod(manager:Accept_Manager,
                     picc:gpd.GeoDataFrame,
                     capa:gpd.GeoDataFrame,
                     number_procs:int = 1):
    """
    Apply the data modification to the layers.

    Process the layers in parallel.

    :remark: It is permitted to execute this function in multiprocessing because we write separate files.

    :param manager: The Accept_Manager object
    :param number_procs: The number of processors to use

    """

    layers = manager.get_layers_in_clipgdb()

    if number_procs == 1:
        for curlayer in layers:
            data_modification(curlayer, manager, picc, capa)
    else:
        pool = multiprocessing.Pool(processes=number_procs)
        prod_x=partial(data_modification,
                          manager=manager,
                          picc=picc,
                          capa=capa)

        result_list = pool.map(prod_x, layers)
        pool.close()
        pool.join()

