"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2025

Copyright (c) 2025 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""


""" This module provides a downloader for the WOLFHECE dataset and other files freely available on the web. """

import re
import requests
import ftplib
from pathlib import Path
from enum import Enum
from typing import Union, Optional, List
from collections import namedtuple
import logging
import urllib.parse

class DownloadType(Enum):
    """ Enum to define the type of download. """
    HTTP = 'http'
    HTTPS = 'https'
    FTP = 'ftp'

class DownloadFiles(Enum):
    """ Enum to define the files to download. """
    WOLFARRAYS = ('bin', 'bin.txt')
    TIFARRAYS = ('tif',)
    TIFFARRAYS = ('tiff',)
    SHPFILES = ('shp', 'dbf', 'shx', 'prj', 'cpg', 'sbn', 'sbx')
    GPKGFILES = ('gpkg',)
    VECFILES = ('vec', 'vec.extra')
    VECZFILES = ('vecz', 'vecz.extra')
    PROJECTFILES = ('proj',)
    NUMPYFILES = ('npy',)
    NPZFILES = ('npz',)
    JSONFILES = ('json',)
    TXTFILES = ('txt',)
    CSVFILES = ('csv',)
    DXFFILES = ('dxf',)
    ZIPFILES = ('zip',)
    LAZFILES = ('laz',)
    LISTFILES = ('lst',)
    LAZBIN = ('bin',)

class DonwloadDirectories(Enum):
    """ Enum to define the directories for downloads. """
    GDBFILES = ('gdb',)


GITLAB_EXAMPLE = 'https://gitlab.uliege.be/HECE/wolf_examples/-/raw/main'
GITLAB_EXAMPLE_GPU = 'https://gitlab.uliege.be/HECE/wolfgpu_examples/-/raw/main'

GITLAB_MODREC_DATA_VESDRE = 'https://gitlab.uliege.be/api/v4/projects/4933'
GITLAB_MODREC_DATA_VESDRE_FILES = 'https://gitlab.uliege.be/api/v4/projects/4933/repository/files/'

GITLAB_INJECTORS_GPU = 'https://gitlab.uliege.be/HECE/wolfgpu_injectors/-/raw/main/src/'

DATADIR = Path(__file__).parent / 'data' / 'downloads'

def clean_url(url: str) -> str:
    """ Clean the URL by removing any query parameters or fragments.

    :param url: The URL to clean.
    :type url: str
    :return: The cleaned URL.
    :rtype: str
    """
    # Remove query parameters and fragments
    cleaned_url = re.sub(r'\?.*|#.*', '', url)
    # Remove trailing slashes
    cleaned_url = re.sub(r'/+$', '', cleaned_url)
    # Remove any leading or trailing whitespace
    cleaned_url = cleaned_url.strip()
    # Ensure slashes are consistent
    cleaned_url = re.sub(r'(?<!:)//+', '/', cleaned_url)
    # Convert Backslashes to forward slashes
    cleaned_url = cleaned_url.replace('\\', '/')

    cleaned_url = cleaned_url.replace(':/', '://')
    cleaned_url = cleaned_url.replace(':///', '://')

    # Ensure the URL starts with http:// or https://
    if not cleaned_url.startswith(('http://', 'https://', 'ftp://')):
        raise ValueError(f"Invalid URL: {url}. Must start with http://, https://, or ftp://")
    return cleaned_url.strip()

def download_file(url: str,
                  destination: Union[str, Path] = None,
                  download_type: DownloadType = DownloadType.HTTP,
                  load_from_cache:bool = True,
                  token:str = None,
                  file_type:DownloadType = None) -> Path:
    """ Download a file from the specified URL to the destination path.

    :param url: The URL of the file to download.
    :param destination: The path where the file will be saved.
    :param download_type: The type of download (HTTP, HTTPS, FTP).
    :type url: str
    :type destination: Union[str, Path]
    :type download_type: DownloadType
    :return: None
    :raises requests.HTTPError: If the HTTP request fails.
    """

    url = str(url).strip()
    # Clean the URL
    if file_type is None:
        url = clean_url(url)

    if destination is None:
        try:
            url_cleaned = url.replace('/raw?ref=main', '').replace('%2F', '/')
            destination = DATADIR / Path(url_cleaned).parent.name / Path(url_cleaned).name
        except:
            destination = DATADIR / Path(url).name
    # create the directory if it does not exist
    destination.parent.mkdir(parents=True, exist_ok=True)

    suffix = Path(url).suffix.lower()
    # remove point from the suffix for matching
    if suffix.startswith('.'):
        suffix = suffix[1:]

    if file_type is None:
        # Find the download type based on the URL suffix
        for file_type_enum in DownloadFiles:
            if suffix in file_type_enum.value:

                if suffix == 'bin' and '_xyz.bin' in url:
                    # special case for LAZ bin files
                    file_type_enum = DownloadFiles.LAZBIN

                file_type = file_type_enum
                break
    else:
        suffix = file_type.value[0]

    # Create a list of files to download based on the download type
    # by replacing suffix in the url with the appropriate file extensions
    to_download = []
    to_destination = []
    for ext in file_type.value:
        if ext.startswith('.'):
            ext = ext[1:]
        to_download.append(url.replace(suffix, f'{ext}'))

        to_destination.append(destination.with_suffix(f'.{ext}'))


    if download_type == DownloadType.HTTP or download_type == DownloadType.HTTPS:

        for url, destination in zip(to_download, to_destination):

            if token is not None:
                # Requête HTTP avec le token
                headers = {
                    "PRIVATE-TOKEN": token
                }
            else:
                headers = {}


            if load_from_cache and destination.exists():
                logging.info(f"File {destination} already exists. Skipping download.")
                continue

            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL: {url}. Must start with http:// or https://")

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                with open(destination, 'wb') as file:
                    file.write(response.content)
            except requests.HTTPError as e:
                logging.error(f"HTTP error occurred while downloading {url}: {e}")

    elif download_type == DownloadType.FTP:

        for url, destination in zip(to_download, to_destination):

            if load_from_cache and destination.exists():
                logging.info(f"File {destination} already exists. Skipping download.")
                continue

            if not url.startswith('ftp://'):
                raise ValueError(f"Invalid URL: {url}. Must start with ftp://")

            try:
                parsed_url = ftplib.parse_ftp_url(url)
                with ftplib.FTP(parsed_url.hostname) as ftp:
                    ftp.login()
                    with open(destination, 'wb') as file:
                        ftp.retrbinary(f'RETR {parsed_url.path}', file.write)
            except ftplib.all_errors as e:
                logging.error(f"FTP error occurred while downloading {url}: {e}")
    else:
        raise ValueError(f"Unsupported download type: {download_type}")

    return to_destination[0]

def toys_dataset(dir:str, file:str, load_from_cache:bool = True):
    """ Download toy files from the WOLFHECE dataset.

    :param dir: The directory where the file will be saved.
    :param file: The name of the file to download.
    :type dir: str
    :type file: str
    :return: The path to the downloaded file.
    """
    url = f"{GITLAB_EXAMPLE}/{dir}/{file}"
    destination = DATADIR / dir / file
    return download_file(url, destination, load_from_cache=load_from_cache)

def download_gpu_simulation(url:str, destination:str | Path, load_from_cache:bool = True):
    """ Download a GPU simulation file from the WOLFHECE dataset.

    :param url: The URL of the GPU simulation file to download.
    :param destination: The path where the file will be saved.
    :param load_from_cache: If True, will not download the file if it already exists.
    :type url: str
    :type destination: str | Path
    :type load_from_cache: bool
    """

    url = str(url).strip()
    url = clean_url(url)
    destination = Path(destination)

    files = ['NAP.npy', 'bathymetry.npy', 'bridge_roof.npy', 'bridge_deck.npy', 'h.npy', 'manning.npy', 'qx.npy', 'qy.npy', 'parameters.json']
    dir_res = 'simul_gpu_results'
    res_files = ['metadata.json', 'nap.npz', 'nb_results.txt', 'sim_times.csv']

    try:
        for file in files:
            try:
                download_file(f"{url}/{file}", destination / file, load_from_cache=load_from_cache)
            except Exception as e:
                logging.error(f"Error downloading file {file} from {url}: {e}")

        url = url + '/' + dir_res
        destination = destination / dir_res
        for file in res_files:
            try:
                download_file(f"{url}/{file}", destination / file, load_from_cache=load_from_cache)
            except Exception as e:
                logging.error(f"Error downloading result file {file} from {url}: {e}")

        with open(destination / 'nb_results.txt', 'r') as f:
            nb_results = int(f.read().strip())

        for i in range(1,nb_results+1):
            # h_0000001.npz
            # qx_0000001.npz
            # qy_0000001.npz
            for file in ['h', 'qx', 'qy']:
                try:
                    download_file(f"{url}/{file}_{i:07d}.npz", destination / f'{file}_{i:07d}.npz', load_from_cache=load_from_cache)
                except Exception as e:
                    logging.error(f"Error downloading result file {file}_{i:07d}.npz from {url}: {e}")

        from wolfgpu.results_store import ResultsStore
        rs = ResultsStore(destination)

    except Exception as e:
        logging.error(f"Error downloading GPU dataset {dir}: {e}")
        rs = None

    return rs

def toys_gpu_dataset(dir:str, dirweb:str = None, load_from_cache:bool = True):
    """ Download toy simulatoin files from the WOLFHECE dataset for GPU.

    :param dir: The directory where the file will be saved.
    :param dirweb: The directory of the files to download.
    :type dir: str
    :type dirweb: str
    :return: The path to the downloaded file.
    """

    if dirweb is None:
        dirweb = dir

    return download_gpu_simulation(f"{GITLAB_EXAMPLE_GPU}/{dirweb}", DATADIR / dir, load_from_cache=load_from_cache)

def toys_injector_gpu(file:str, load_from_cache:bool = True):
    """ Download toy GPU injector files from the WOLFHECE dataset.

    :param file: The name of the file to download.
    :type file: str
    :return: The path to the downloaded file.
    """
    url = f"{GITLAB_INJECTORS_GPU}{file}"
    destination = DATADIR / 'injectors_gpu' / file
    return download_file(url, destination, load_from_cache=load_from_cache)

def toys_laz_grid(dir:str, file:str, load_from_cache:bool = True):
    """ Download toy LAZ or GRIDWOLF files from the WOLFHECE dataset.

    :param dir: The directory where the file will be saved.
    :param file: The name of the file to download.
    :type dir: str
    :type file: str
    :return: The path to the downloaded directory.
    """
    url = f"{GITLAB_EXAMPLE}/{dir}/{file}"
    destination = DATADIR / dir / file
    lst = download_file(url, destination, load_from_cache=load_from_cache)

    with open(lst, 'r') as f:
        lines = f.read().splitlines()

    for line in lines:
        line = line.strip().replace('\\', '/')
        if line:
            url = f"{GITLAB_EXAMPLE}/{dir}/{line}"
            destination = DATADIR / dir / line
            download_file(url, destination, load_from_cache=load_from_cache)

    return DATADIR / dir

def laz_grid_from_url(url:str, dir:str, file:str, load_from_cache:bool = True):
    """ Download toy LAZ or GRIDWOLF files from an external URL.

    :param url: The base URL where the files are located.
    :param dir: The directory where the file will be saved.
    :param file: The name of the file to download.
    :type url: str
    :type dir: str
    :type file: str
    :return: The path to the downloaded directory.
    """
    url = f"{url}/{dir}/{file}"
    destination = DATADIR / dir / file
    lst = download_file(url, destination, load_from_cache=load_from_cache)

    if not Path(lst).exists():
        raise FileNotFoundError(f"The file {lst} does not exist. -- Check the URL and file name.")

    with open(lst, 'r') as f:
        lines = f.read().splitlines()

    for line in lines:
        line = line.strip().replace('\\', '/')
        if line:
            url = f"{GITLAB_EXAMPLE}/{dir}/{line}"
            destination = DATADIR / dir / line
            download_file(url, destination, load_from_cache=load_from_cache)

    return DATADIR / dir

def check_status(url:str, token:str = None) -> bool:
    """ Check the status of a URL.

    :param url: The URL to check.
    :param token: The private token for authentication (if required).
    :type url: str
    :type token: str
    :return: True if the URL is accessible, False otherwise.
    :rtype: bool
    """
    url = str(url).strip()
    url = clean_url(url)

    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL: {url}. Must start with http:// or https://")

    try:
        if token is not None:
            headers = {
                "PRIVATE-TOKEN": token
            }
        else:
            headers = {}

        response = requests.head(url, headers=headers)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error(f"Error checking URL {url}: {e}")
        return False

def download_modrec_vesdre_file(directory:str, filename:str,
                                token:str = None, load_from_cache:bool = True,
                                file_type:DownloadFiles = None) -> Path:

    """ Download a file from the ModRec Vesdre dataset.

    :param directory: The directory where the file is located (relative to the repository root).
    :param filename: The name of the file to download.
    :param token: The private token for authentication (if required).
    :param load_from_cache: If True, will not download the file if it already exists.
    :type directory: str
    :type filename: str
    :type token: str
    :type load_from_cache: bool
    :return: The path to the downloaded file.
    :rtype: Path
    """

    # Find the download type based on the URL suffix
    if file_type is None:
        suffix = Path(filename).suffix.lower().replace('.', '')

        for file_type_enum in DownloadFiles:
            if suffix in file_type_enum.value:

                if suffix == 'bin' and '_xyz.bin' in filename:
                    # special case for LAZ bin files
                    file_type_enum = DownloadFiles.LAZBIN

                file_type = file_type_enum
                break

    file_path_encoded = urllib.parse.quote_plus(directory + '/' + filename)
    url = f"{GITLAB_MODREC_DATA_VESDRE_FILES}{file_path_encoded}/raw?ref=main"
    destination = DATADIR / 'Vesdre' / file_path_encoded.replace('%2F', '/')
    return download_file(url, destination, token=token, load_from_cache=load_from_cache, file_type=file_type)

if __name__ == "__main__":
    token = '' # Add your GitLab private token here if needed
    dir = 'LAZ_Vesdre/2023/grids_flt32/237500_145500'
    file_path = "237500_145500_237500_145000_xyz.bin"
    print(download_modrec_vesdre_file(dir, file_path, token=token, load_from_cache=False))

    # Example usage
    print(download_file(r'https:\\gitlab.uliege.be\HECE\wolf_examples\-\raw\main\Extract_part_array\extraction.vec'))
    print(download_file('https://gitlab.uliege.be/HECE/wolf_examples/-/raw/main/Extract_part_array/extraction.vec'))
    print(download_file('https://gitlab.uliege.be/HECE/wolf_examples/-/raw/main/Extract_part_array/Array_vector.proj'))
    print(download_file('https://gitlab.uliege.be/HECE/wolf_examples/-/raw/main/Array_Theux_Pepinster/mnt.bin'))
    print(download_file('https://gitlab.uliege.be/HECE/wolf_examples/-/raw/main/Array_Theux_Pepinster/mnt.tif'))
    print(download_file('https://gitlab.uliege.be/HECE/wolf_examples/-/raw/main/PICC/PICC_Vesdre.shp'))
    print(toys_dataset('Extract_part_array', 'extraction.vec'))
    rs = toys_gpu_dataset('channel_w_archbridge_fully_man004')
