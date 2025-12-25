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
import zipfile
from tqdm import tqdm

def convert_asc2tif(wdir:str, fout:str='out.tif', onlyonefile=True, onlyvrt=False):
    """
    Conversion de tous les fichiers .ASC dans un répertoire en un fichier .vrt et/ou .tif unique (onlyonefile==True/False, onlyvrt=False/True)
    ou
    Conversion de tous les fichiers .ASC dans un répertoire en autant de fichier .tif (ajout pur et simple de l'extension .tif au nom de fichier)
    """
    curdir = os.getcwd()
    os.chdir(wdir)

    if onlyonefile:
        gdal.BuildVRT(os.path.join(wdir,fout+'.vrt') , glob.glob(os.path.join(wdir,'*.asc')))
        if not onlyvrt:
            gdal.Translate(fout, fout+'.vrt')
    else:
        ascfiles = glob.glob(os.path.join(wdir,'*.asc'))
        for curfile in tqdm(ascfiles):
            gdal.Translate(curfile+'.tif', curfile)

    os.chdir(curdir)

def convert_zip2tif(wdir:str, fout:str='out.tif', onlyonefile=True, onlyvrt=False):
    """
    Conversion de tous les fichiers .ZIP contenant un fichier .ASC dans un répertoire en un fichier .vrt et/ou .tif unique (onlyonefile==True/False, onlyvrt=False/True)
    ou
    Conversion de tous les fichiers .ZIP contenant un fichier .ASC dans un répertoire en autant de fichier .tif (ajout pur et simple de l'extension .tif au nom de fichier)
    """
    curdir = os.getcwd()
    os.chdir(wdir)

    if onlyonefile:
        gdal.BuildVRT(os.path.join(wdir,fout+'.vrt') , glob.glob(os.path.join(wdir,'*.tif')))
        if not onlyvrt:
            gdal.Translate(fout, fout+'.vrt')
    else:
        zipfiles = glob.glob(os.path.join(wdir,'*.zip'))
        for curfile in tqdm(zipfiles):
            try:
                with zipfile.ZipFile(curfile, mode='r') as archive:
                    files = archive.namelist()
                    if len(files)==1 and str(files[0]).endswith('.asc'):
                        ascfile = files[0]
                        archive.extract(ascfile, '.')
                        gdal.Translate(ascfile+'.tif', ascfile)
                        os.remove(ascfile)
            except:
                print('Error in : {}'.format(curfile))
    os.chdir(curdir)

if __name__=='__main__':
    # convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\MNT_50cm', onlyonefile=False)
    # convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\MNS_50cm', onlyonefile=False)
    # convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\MNC_50cm', onlyonefile=False)
    # convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v2_reprise\MNT_Bati+Muret', onlyonefile=False)

    # convert_zip2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v4\MNS_50cm', onlyonefile=False)
    # convert_zip2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v4\MNS_50cm', onlyonefile=True, onlyvrt=True)

    # convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v3\MNT_Bati+Muret', onlyonefile=False)
    convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v3\MNT_50cm', onlyonefile=False)
    convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v3\MNS_50cm', onlyonefile=False)
    convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v3\MNC_50cm', onlyonefile=False)
    convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v3\Densite_sol', onlyonefile=False)
    convert_asc2tif(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\v3\Densite_Complet', onlyonefile=False)
