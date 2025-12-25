"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import os
import glob
from osgeo import osr, gdal
import logging
from pathlib import Path

from .PyVertexvectors import Zones

def create_vrt(wdir:str, fout:str='out.vrt', format:str='tif'):
    """
    Agglomération de tous les fichiers .tif dans un layer virtuel .vrt

    :param wdir: working directory
    :type wdir: str
    :param fout: output file
    :type fout: str
    :param format: format of the files to process
    :type format: str
    """

    curdir = os.getcwd()
    os.chdir(wdir)

    if not fout.endswith('.vrt'):
        fout+='.vrt'

    myvrt = gdal.BuildVRT(os.path.join(wdir,fout) , glob.glob(os.path.join(wdir,'*.'+format)))
    myvrt = None

    os.chdir(curdir)

def _get_diverged_relative_path(path: Path, base: Path) -> Path:
    """
    Get relative path from base to path, even if they only share part of their paths.
    More general than the next function "_get_relative_path", especially for not "child/parents paths"
    """

    # Parts of the paths
    relative_path_parts = path.parts
    base_parts = base.parts
    # Where do they diverge ?
    i = 0
    while i < min(len(relative_path_parts), len(base_parts)) and relative_path_parts[i] == base_parts[i]:
        i += 1

    # Building of the relative path, by adding ".." from the divergence point
    return Path(*(['..'] * (len(base_parts) - i) + list(relative_path_parts[i:])))


def _get_relative_path(path:Path, base:Path):
    """
    Get relative path from base to path

    :param path: path to get relative path
    :type path: Path
    :param base: base path
    :type base: Path
    """

    if base in path.parents:
        return path.relative_to(base)
    elif path.parent in base.parents:
        pos=''
        for curpos in range(len(base.relative_to(path.parent).parents)):
            pos += '../'
        return Path(pos+path.name)

def create_vrt_from_files(files:list[Path]=[], fout:Path='assembly.vrt'):
    """
    Agglomération de tous les fichiers énumérés dans files dans un layer virtuel .vrt

    :param files: list of files to process
    :type files: list[Path]
    :param fout: output file
    :type fout: Path
    """

    if isinstance(fout, str):
        fout = Path(fout)

    if isinstance(files[0], str):
        files = [Path(file) for file in files]

    # retain current working directory
    oldcwd = os.getcwd()
    # change working directory to the parent of the output file
    os.chdir(fout.parent)
    # work with relative paths

    myvrt = gdal.BuildVRT(str(fout.with_suffix('.vrt').name) , [str(_get_diverged_relative_path(file, fout.parent)) for file in files])
    # close the dataset -- force to write on disk
    myvrt = None
    # restore working directory
    os.chdir(oldcwd)

def create_vrt_from_files_first_based(files:list[Path]=[], fout:Path='assembly.vrt', Nodata:float=99999.):
    """
    Agglomération de tous les fichiers énumérés dans files dans un layer virtuel .vrt

    Restreint l'emprise et force la résolution sur le premier fichier listé
    """

    if isinstance(fout, str):
        fout = Path(fout)

    if isinstance(files[0], str):
        files = [Path(file) for file in files]

    first = files[0]
    raster:gdal.Dataset
    raster = gdal.Open(str(first))
    geotr = raster.GetGeoTransform()

    # Dimensions
    nbx = raster.RasterXSize
    nby = raster.RasterYSize

    xmin = geotr[0]
    xmax = geotr[0]+geotr[1]*float(nbx)

    if geotr[5]>0:
        ymin = geotr[3]
        ymax = geotr[3]+geotr[5]*float(nby)
    else:
        ymin = geotr[3]+geotr[5]*float(nby)
        ymax = geotr[3]

    locNoData = raster.GetRasterBand(1).GetNoDataValue()

    # options of BuildVRT defined on properties of "files[0]"
    options = gdal.BuildVRTOptions(resolution='user',
                                   xRes=abs(geotr[1]),
                                   yRes=abs(geotr[5]),
                                   outputBounds=[xmin,ymin,xmax,ymax],
                                   resampleAlg='bilinear',
                                   srcNodata=Nodata)

    # retain current working directory
    oldcwd = os.getcwd()
    # change working directory to the parent of the output file
    os.chdir(fout.parent.absolute())
    # work with relative paths
    myvrt = gdal.BuildVRT(str(fout.with_suffix('.vrt').name),[str(_get_diverged_relative_path(file, fout.parent)) for file in files], options=options) #str(_get_diverged_relative_path(file, fout.parent)) for file in files

    # close the dataset -- force to write on disk
    myvrt = None
    # restore working directory
    os.chdir(oldcwd)


def create_vrt_from_diverged_files(files:list[Path]=[], fout:Path='assembly.vrt'):
    """
    Agglomération de tous les fichiers énumérés dans files dans un layer virtuel .vrt

    :param files: list of files to process
    :type files: list[Path]
    :param fout: output file
    :type fout: Path
    """

    if isinstance(fout, str):
        fout = Path(fout)

    if isinstance(files[0], str):
        files = [Path(file) for file in files]

    # retain current working directory
    oldcwd = os.getcwd()
    # change working directory to the parent of the output file
    os.chdir(fout.parent)
    # work with relative paths

    myvrt = gdal.BuildVRT(str(fout.with_suffix('.vrt').name) , [str(_get_diverged_relative_path(file, fout.parent)) for file in files])
    # close the dataset -- force to write on disk
    myvrt = None
    # restore working directory
    os.chdir(oldcwd)

def create_vrt_from_diverged_files_first_based(files:list[Path]=[], fout:Path='assembly.vrt', Nodata:float=99999.):
    """
    Agglomération de tous les fichiers énumérés dans files dans un layer virtuel .vrt

    Restreint l'emprise et force la résolution sur le premier fichier listé
    """

    if isinstance(fout, str):
        fout = Path(fout)

    if isinstance(files[0], str):
        files = [Path(file) for file in files]

    first = files[0]
    raster:gdal.Dataset
    raster = gdal.Open(str(first))
    geotr = raster.GetGeoTransform()

    # Dimensions
    nbx = raster.RasterXSize
    nby = raster.RasterYSize

    xmin = geotr[0]
    xmax = geotr[0]+geotr[1]*float(nbx)

    if geotr[5]>0:
        ymin = geotr[3]
        ymax = geotr[3]+geotr[5]*float(nby)
    else:
        ymin = geotr[3]+geotr[5]*float(nby)
        ymax = geotr[3]

    locNoData = raster.GetRasterBand(1).GetNoDataValue()

    # options of BuildVRT defined on properties of "files[0]"
    options = gdal.BuildVRTOptions(resolution='user',
                                   xRes=abs(geotr[1]),
                                   yRes=abs(geotr[5]),
                                   outputBounds=[xmin,ymin,xmax,ymax],
                                   resampleAlg='bilinear',
                                   srcNodata=Nodata)

    # retain current working directory
    oldcwd = os.getcwd()
    # change working directory to the parent of the output file
    os.chdir(fout.parent.absolute())
    # work with relative paths
    myvrt = gdal.BuildVRT(str(fout.with_suffix('.vrt').name),[str(_get_diverged_relative_path(file, fout.parent)) for file in files], options=options) #str(_get_diverged_relative_path(file, fout.parent)) for file in files

    # close the dataset -- force to write on disk
    myvrt = None
    # restore working directory
    os.chdir(oldcwd)

def translate_vrt2tif(fn:str, fout:str=None):
    """
    Translate vrt file to tif file

    :param fn: (str) '.vrt' file to translate
    :param fout: (str, optional) '.tif' file out. Defaults to None --> fn+'.tif'
    """
    if isinstance(fn,Path):
        fn = str(fn)
    if isinstance(fout,Path):
        fout = str(fout)

    if os.path.exists(fn):

        if not fn.endswith('.vrt'):
            logging.warning('Bad file -- not .vrt extension !')
            return

        if fout is None:
            fout = fn +'.tif'

        if not fout.endswith('.tif'):
            fout+='.tif'

        options = gdal.TranslateOptions(format='GTiff', creationOptions=['COMPRESS=LZW', 'TILED=YES', 'BIGTIFF=YES'])
        gdal.Translate(fout, fn, options=options)

    else:
        logging.warning('The file does not exist !')

def crop_vrt(fn:str, crop:list, fout:str=None):
    """
    Crop vrt file

    :param fn: (str) '.vrt' file to crop
    :type fn: str
    :param crop: (list) Bounds [[xmin, xmax], [ymin,ymax]] aka [[xLL, xUR], [yLL,yUR]]
    :type crop: list
    :param fout: (str, optional) '.tif' file out. Defaults to None --> fn+'_crop.tif'
    :type fout: str
    """
    if os.path.exists(fn):

        if not fn.endswith('.vrt'):
            logging.warning('Bad file -- not .vrt extension !')
            return

        [xmin, xmax], [ymin, ymax] = crop

        if fout is None:
            fout = fn +'_crop.tif'

        if not fout.endswith('.tif'):
            fout+='.tif'

        gdal.Translate(fout, fn, projWin=[xmin, ymax, xmax, ymin])

    else:
        logging.warning('The file does not exist !')

def create_contours(files:list[Path]=[],
                   fout:Path = 'assembly.vec',
                   color_exterior:tuple=(255,0,0),
                   color_interior:tuple=(0,0,255),
                   width:int=3,
                   ignore_first:bool=True,
                   create_extern:bool = True,
                   create_intern:bool = True,
                   force_mask_border:bool = True) -> Zones:
    """
    Create contour/footprint from files

    :param files: list of files to process
    :type files: list[Path]
    :param fout: output file
    :type fout: Path - if None, no output file
    :param color_exterior: RGB color for exterior contour
    :type color_exterior: tuple
    :param color_interior: RGB color for interior contour
    :type color_interior: tuple
    :param width: width of the contour
    :type width: int
    :param ignore_first: ignore the first file in the list
    :type ignore_first: bool
    :param create_extern: create exterior contour
    :type create_extern: bool
    :param create_intern: create interior contour
    :type create_intern: bool
    :param force_mask_border: force masked data along borders -- [0,:], [-1,:], [:,0], [:,-1
    :type force_mask_border: bool

    """

    from tqdm import tqdm
    from .wolf_array import WolfArray
    from .PyVertexvectors import Zones, zone, vector, wolfvertex, getIfromRGB

    if isinstance(fout, str):
        fout = Path(fout)

    if not(create_extern or create_intern):
        logging.warning('No contour to create !')
        return None

    emprises = Zones()

    start = 1 if ignore_first else 0

    for file in tqdm(files[start:]):

        curzone = zone(name = str(file.name))
        emprises.add_zone(curzone, forceparent=True)

        curarray = WolfArray(str(file))

        if force_mask_border:
            curarray.array.mask[0,:] = True
            curarray.array.mask[-1,:] = True
            curarray.array.mask[:,0] = True
            curarray.array.mask[:,-1] = True
        else:
            print_name = False
            if (~curarray.array.mask[0,:]).any():
                logging.warning('\nNon masked data along border -- [0,:]\n')
                print_name = True

            if (~curarray.array.mask[-1,:]).any():
                pre = '' if print_name else '\n'
                logging.warning(pre+'Non masked data along border -- [-1,:]\n')
                print_name = True

            if (~curarray.array.mask[:,0]).any():
                pre = '' if print_name else '\n'
                logging.warning(pre+'Non masked data along border -- [:,0]\n')
                print_name = True

            if (~curarray.array.mask[:,-1]).any():
                pre = '' if print_name else '\n'
                logging.warning(pre+'Non masked data along border -- [:,-1]\n')
                print_name = True

            if print_name:
                logging.warning(f'File: {file}\n')

        if create_intern:
            ret = curarray.suxsuy_contour(abs = True)

            curvec = ret[2]
            curvec.myname = 'contour_utile'
            curzone.add_vector(curvec, forceparent=True)

            curvec.myprop.color = getIfromRGB(color_interior)
            curvec.myprop.width = width

        if create_extern:

            bounds = curarray.get_bounds(True)
            vecrect = vector(name = 'contour_externe')

            curzone.add_vector(vecrect, forceparent=True)

            vecrect.add_vertex((wolfvertex(bounds[0][0], bounds[1][0])))
            vecrect.add_vertex((wolfvertex(bounds[0][1], bounds[1][0])))
            vecrect.add_vertex((wolfvertex(bounds[0][1], bounds[1][1])))
            vecrect.add_vertex((wolfvertex(bounds[0][0], bounds[1][1])))
            vecrect.close_force()

            vecrect.myprop.color = getIfromRGB(color_exterior)
            vecrect.myprop.width = width
            vecrect.myprop.legendvisible = True
            vecrect.myprop.legendtext = file.name

            sh = vecrect.asshapely_ls()
            vecrect.myprop.legendx = sh.centroid.x
            vecrect.myprop.legendy = sh.centroid.y

    if fout is not None:
        emprises.saveas(str(fout))

    return emprises

if __name__=='__main__':

    dir = r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\GeoTif\encours\MNT_Bati+Muret'
    file_vrt = r'AllData_MNT_BatiMuret_50cm.vrt'

    create_vrt(dir, fout=file_vrt)
    crop_vrt(os.path.join(dir, file_vrt), [[251000,253400],[135500,141300]], os.path.join(dir, 'Theux-Pepinster.tif'))