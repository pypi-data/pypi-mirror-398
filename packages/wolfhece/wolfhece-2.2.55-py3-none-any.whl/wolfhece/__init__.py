from . import _add_path
from .libs import *
from .PyTranslate import _

try:
    from osgeo import gdal, osr, ogr
    gdal.UseExceptions()
    ogr.UseExceptions()
    osr.UseExceptions()
except ImportError as e:
    # print(e)
    raise Exception(_('Error importing GDAL library\nPlease ensure GDAL is installed and the Python bindings are available\n\ngdal wheels can be found at https://github.com/cgohlke/geospatial-wheels'))

try:
    import pyproj
except ImportError as e:
    raise ImportError(_('pyproj is not installed. Please install it to use this function.')) from e

from .apps.version import WolfVersion
from packaging.version import Version
from pathlib import Path


def ensure_ntv2grid_exists():
    """
    Check if the NTV2 grid file exists in the expected location.
    """

    from shutil import copyfile

    # print('Version de pyproj :', pyproj.__version__)
    files = ['be_ign_bd72lb72_etrs89lb08.tif', 'be_ign_hBG18.tif', 'be_ign_README.txt']

    pyproj_datadir = Path(pyproj.datadir.get_data_dir())
    os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()  # set the PROJ_DATA environment variable to pyproj data directory

    for file in files:
        if not (pyproj_datadir / file).exists():
            # copy the NTV2 grid file to the pyproj data directory
            ntv2_grid_path = Path(__file__).parent / 'lb7208_ntv2' / file
            copyfile(ntv2_grid_path, pyproj_datadir / file)
            print(f"Copied {file} to {pyproj_datadir}")

__version__ = WolfVersion().get_version()
ensure_ntv2grid_exists()

def is_enough(version: str) -> bool:
    """
    Compare the current version of WolfHece to a given version string.

    Args:
        version (str): The version string to compare against.

    Returns:
        bool: True if the current version is greater than or equal to the given version, False otherwise.
    """
    return Version(__version__) >= Version(version)