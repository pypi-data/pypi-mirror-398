from importlib.resources import files
from pathlib import Path
from enum import Enum

import numpy as np
import logging

import ftplib

from eccodes import codes_grib_new_from_file, codes_get, codes_get_values, codes_release, codes_keys_iterator_new, codes_keys_iterator_next, codes_keys_iterator_get_name

from datetime import datetime as dt, timedelta as td
from datetime import timezone as timezone

from shapely.geometry import Polygon, Point
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import wx

from .pydownloader import DATADIR, toys_dataset
from .Coordinates_operations import transform_coordinates
from .wolf_array import header_wolf, WolfArray
from .PyVertexvectors import Zones, zone, vector, wolfvertex as wv
from .PyTranslate import _

OPENDATA_FORECASTS = 'forecasts'
OPENDATA_FTP_SERVER = 'opendata.meteo.be'
OPENDATA_ALARO_40L = 'alaro_40l'
FILE_PREFIX = 'alaro40l'

# Date Format : YYYYMMDDHH with HH in [00, 06, 12, 18]

def _convert_col2date_str(col:str) -> str:
    """ Create a string representation of the date from the column name. """

    if col is None:
        return "No data"

    parts = col.split('_')
    run_date = dt.strptime(parts[0], '%Y%m%d%H').strftime('%Y-%m-%d %H:%M')
    real_date = dt.strptime(parts[1], '%Y%m%d').strftime('%Y-%m-%d')
    hour = parts[2]

    date_str = _(f'Forecast date : {real_date}, Hour : {hour} - Run : {run_date}')

    return date_str

def _extract_dates_from_columnstr(col:str) -> list[dt]:
    """ Extract the run date and forecast date from the column name. """

    if col is None:
        return [None, None]

    parts = col.split('_')
    run_date = dt.strptime(parts[0], '%Y%m%d%H')
    real_date = dt.strptime(parts[1], '%Y%m%d')
    hour = int(parts[2])

    # set timezone as UTC
    run_date = run_date.replace(tzinfo=timezone.utc)
    real_date = real_date.replace(tzinfo=timezone.utc)

    forecast_date = real_date + td(hours=hour)

    return [run_date, forecast_date]

def ArrayBelgium() -> WolfArray:
    """
    Create a WolfArray for the Belgium domain.
    """

    # Define the spatial extent for Belgium
    h = header_wolf()
    h.set_origin(17_000., 20_000.)
    h.set_resolution(4_000., 4_000.)
    h.shape = (int((296_000.-17_000.)//4_000.), int((245_000.-20_000.)//4_000.))

    # Create the WolfArray
    return WolfArray(srcheader=h)


class GribFiles(Enum):
    """
    Enum for Grib files used in IRM Alaro data.
    """

    # FIXME : check the units and descriptions

    FILE_10U = '10U.grb' # 10m U-component of wind [m/s]
    FILE_10V = '10V.grb' # 10m V-component of wind [m/s]
    FILE_MaxT2 = 'MaxT2.grb' # Maximum 2m temperature [K]
    FILE_MinT2 = 'MinT2.grb' # Minimum 2m temperature [K]
    FILE_2D = '2D.grb' # 2m dew point temperature [K]
    FILE_2T = '2T.grb' # 2m temperature [K]
    FILE_RH2M = 'RH2M.grb' # 2m relative humidity [0-1]
    FILE_CR = 'CR.grb' # Convective rain [mm] or [kg/m²]
    FILE_CS = 'CS.grb' # Convective snow [mm] or [kg/m²]
    FILE_Z = 'Z.grb' # Geopotential height [m]
    FILE_IFCCC = 'IFCCC.grb' # Instant fluctuation convective cloud cover [0-1]
    FILE_IFHCC = 'IFHCC.grb' # Instant fluctuation high cloud cover [0-1]
    FILE_IFLCC = 'IFLCC.grb' # Instant fluctuation low cloud cover [0-1]
    FILE_IFMCC = 'IFMCC.grb' # Instant fluctuation medium cloud cover [0-1]
    FILE_IFTCC = 'IFTCC.grb' # Instant fluctuation total cloud cover [0-1]
    FILE_LSR = 'LSR.grb' # Large scale rain [mm] or [kg/m²]
    FILE_LSS = 'LSS.grb' # Large scale snow [mm] or [kg/m²]
    FILE_MSLP = 'MSLP.grb' # Mean sea level pressure [Pa]

    FILE_R = 'R.grb' # Relative humidity [0-1] ??
    FILE_Q = 'Q.grb' # Relative humidity isobaric [0-1] ??

    FILE_MerGust = 'MerGust.grb' # SBL Medidian gust [m/s]
    FILE_ZonGust = 'ZonGust.grb' # SBL Zonal gust [m/s]
    FILE_SurfSWrad = 'SurfSWrad.grb' # Surface shortwave radiation [W/m²]
    FILE_SurfLWrad = 'SurfLWrad.grb' # Surface longwave radiation [W/m²]
    FILE_SurfCape = 'SurfCape.grb' # Surface CAPE [J/kg]
    FILE_ST = 'ST.grb' # Surface temperature [K]
    FILE_ORO = 'ORO.grb' # Surface orography [m]
    FILE_T = 'T.grb' # Temperature [K]
    FILE_TotPrecip = 'TotPrecip.grb'  # Total precipitation [m_water_equivalent]
    FILE_U = 'U.grb' # U-component of wind [m/s]
    FILE_V = 'V.grb' # V-component of wind [m/s]
    FILE_W = 'W.grb' # Vertical velocity [Pa/s]
    FILE_WBPT = 'WBPT.grb' # Wet bulb potential temperature [K]
    FILE_fzht = 'fzht.grb' # Freezing leveml (0°C isotherm) [m]

class IRM_Alaro():
    """
    Class for handling IRM Alaro forecasts.
    """

    def __init__(self, ftp_server: str = OPENDATA_FTP_SERVER, ftp_path: str = OPENDATA_FORECASTS):
        """
        Initialize the IRM_Alaro class with FTP server and path.
        """

        self.ftp_server = ftp_server
        self.ftp_path = ftp_path
        self._gdf = None
        self._gdf_cache = None
        self._gdf_diff = None
        self._zones = None
        self._array = ArrayBelgium()
        self._available_run_dates = []

        self._colormap = plt.get_cmap('Blues')

        self._cities = gpd.read_file(toys_dataset('Communes_Belgique', 'PDS__COMMUNES.shp'))

    def _ftp_init(self):
        """ Initialize the FTP connection. """
        self.ftp = ftplib.FTP(self.ftp_server,)
        self.ftp.login()
        self.ftp.cwd(self.ftp_path + '/' + OPENDATA_ALARO_40L)

    def _ftp_close(self):
        """
        Close the FTP connection.
        """
        try:
            self.ftp.close()
        except Exception as e:
            logging.error(f"Error closing FTP connection: {e}")

    def list_run_dates_cached(self) -> list:
        """
        Return the cached list of available run dates.
        """
        all_grib_files = self.data_directory.rglob('*.grb')
        dates = [f.stem.split('_')[1] for f in all_grib_files if f.is_file() and len(f.stem.split('_')) == 3]
        return sorted(list(set(dates)))

    def list_run_dates(self) -> list:
        """
        List available data files on the FTP server.
        """

        today = dt.now()
        possible_run_dates = []

        # hours
        hours = ['00', '06', '12', '18']

        date_format = '%Y%m%d'
        # Generate forecast strings for the last 3 days
        for i in range(3):
            forecast_time = today - td(days=i)
            forecast_str = forecast_time.strftime(date_format)
            possible_run_dates.append([forecast_str + hour for hour in hours])
        # flatten the list of lists
        possible_run_dates = [item for sublist in possible_run_dates for item in sublist]

        try:

            self._ftp_init()

            for poss in possible_run_dates:
                try:
                    self.ftp.cwd(poss)
                    files = self.ftp.nlst()
                    if files:
                        self._available_run_dates.append(poss)
                        self.ftp.cwd('..')  # Go back to the parent directory
                except ftplib.error_perm:
                    continue

            self._ftp_close()

            self._available_run_dates.sort()
            return self._available_run_dates

        except ftplib.error_perm as e:
            logging.error(f"Error listing files: {e}")
            return []

    @property
    def run_dates(self) -> list:
        """ Return the available forecasts run dates. """
        if len(self._available_run_dates) == 0:
            self.list_run_dates()

        return self._available_run_dates

    @property
    def run_dates_str(self) -> str:
        """ Return the available forecasts run dates as a string. """
        return [dt.strptime(run, '%Y%m%d%H').strftime('%Y-%m-%d %H:%M') for run in self.run_dates]

    def list_files_for_forecast(self, run_date: str) -> list:
        """
        List files for a specific forecast.

        :param run_date: The forecast time.
        """
        try:
            self._ftp_init()
            self.ftp.cwd(f"{run_date}")
            files = self.ftp.nlst()
            self._ftp_close()

            # check if all files are present
            missing_files = [file for file in GribFiles if self._get_filename(file, run_date) not in files]
            if missing_files:
                logging.warning(f"Missing files for forecast {run_date}: {missing_files}")

            return files
        except ftplib.error_perm as e:
            logging.error(f"Error listing files for forecast {run_date}: {e}")
            return []

    def _get_filename(self, file: GribFiles, run_date: str) -> str:
        """
        Generate the filename for a given Grib file and forecast.

        :param file: The Grib file enum.
        :param run_date: The forecast time.
        """
        return f"{FILE_PREFIX}_{run_date}_{file.value}"

    @property
    def data_directory(self) -> Path:
        """ Return the data directory path. """
        return Path(DATADIR) / 'forecasts'

    def download_data(self, filename: GribFiles | str, run_date: str) -> Path:
        """
        Download data from the FTP server.

        :param filename: The Grib file to download or a specific filename.
        :param run_date: The forecast time.
        """
        if isinstance(filename, str):
            fn = filename
        else:
            fn = self._get_filename(filename, run_date)
        local_path = self.data_directory / f'{fn}'
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if run_date not in self.run_dates:
            if not local_path.exists():
                logging.info(f"Run date {run_date} not available on FTP server nor locally.")
                return local_path

            else:
                logging.info(f"Run date {run_date} not available on FTP server, but file exists locally.")
                return local_path

        self._ftp_init()
        self.ftp.cwd(f"{run_date}")

        # Get size of the file
        try:
            remote_size = self.ftp.size(fn)
            if local_path.exists():
                local_size = local_path.stat().st_size
                if local_size == remote_size:
                    logging.info(f"File {fn} already exists and is complete. Skipping download.")
                else:
                    logging.info(f"File {fn} exists but is incomplete. Re-downloading.")

                    with open(local_path, 'wb') as f:
                        self.ftp.retrbinary(f'RETR {fn}', f.write)

            else:
                logging.info(f"File {fn} does not exist. Re-downloading.")

                with open(local_path, 'wb') as f:
                    self.ftp.retrbinary(f'RETR {fn}', f.write)

        except ftplib.error_perm as e:
            logging.error(f"Could not get size for file {fn}: {e}")

            # Proceed to download the file anyway
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary(f'RETR {fn}', f.write)

        self._ftp_close()

        return local_path

    def download_TotalPrecipitations_available_files(self) -> list[Path]:
        """
        Download Cumulated rain, Temperature et 2m - files available on the FTP server.
        """

        to_download = [GribFiles.FILE_TotPrecip, GribFiles.FILE_2T]

        rundates = self.run_dates

        downloaded_files = []

        for rundate in rundates:
            for file in self.list_files_for_forecast(rundate):
                for selection in to_download:
                    if selection.value in file:
                        local_path = self.download_data(file, rundate)
                        downloaded_files.append(local_path)

        return downloaded_files

    def download_all_available_files(self) -> list[Path]:
        """
        Download all files available on the FTP server.
        """

        rundates = self.run_dates

        downloaded_files = []

        for rundate in rundates:
            for file in self.list_files_for_forecast(rundate):
                local_path = self.download_data(file, rundate)
                downloaded_files.append(local_path)

        return downloaded_files

    def _get_center_coordinates(self, filename: GribFiles,
                                 run_date: str,
                                 EPSG:str = 'EPSG:31370') -> tuple[np.ndarray, np.ndarray]:
        """
        Load GRIB data and compute coordinates.

        :param filename: The GRIB file to process.
        :param forecast: The forecast time.
        :param download: Whether to download the file if it doesn't exist.
        :param EPSG: The target EPSG code for the output coordinates.
        :return: The center coordinates (x, y) for the given GRIB file and forecast.
        """

        file_path = self.download_data(filename, run_date)

        if not file_path.exists():
            logging.error(f"File {file_path} does not exist.")
            return np.array([])

        with open(file_path, 'rb') as f:
            gid = codes_grib_new_from_file(f)

            # Type de grille
            grid_type = codes_get(gid, "gridType")
            logging.info("Type de grille :", grid_type)

            # Dimensions de la grille
            Ni = codes_get(gid, "Ni")  # nombre de points en longitude
            Nj = codes_get(gid, "Nj")  # nombre de points en latitude
            logging.info(f"Dimensions : {Ni} x {Nj}")

            # Coordonnées du premier et dernier point
            lat1 = codes_get(gid, "latitudeOfFirstGridPointInDegrees")
            lon1 = codes_get(gid, "longitudeOfFirstGridPointInDegrees")
            lat2 = codes_get(gid, "latitudeOfLastGridPointInDegrees")
            lon2 = codes_get(gid, "longitudeOfLastGridPointInDegrees")
            logging.info(f"Grille de ({lat1}, {lon1}) à ({lat2}, {lon2})")

            # Incréments
            dlat = codes_get(gid, "jDirectionIncrementInDegrees")
            dlon = codes_get(gid, "iDirectionIncrementInDegrees")
            logging.info(f"Incréments : {dlon}° en longitude, {dlat}° en latitude")

            # Reconstruire les coordonnées
            lats = np.linspace(lat1, lat2, Nj)
            lons = np.linspace(lon1, lon2, Ni)

            # ---------------
            # ATTENTION : data are enumerated longitude first, then latitude
            # We need to use meshgrid to get the correct order
            lon_grid, lat_grid = np.meshgrid(lons, lats)
            # ---------------

            # Convert to numpy arrays
            lats = lat_grid.flatten()
            lons = lon_grid.flatten()

            # Convert to Lambert 72 E
            xy = transform_coordinates(np.vstack([lons, lats]).T, "EPSG:4326", EPSG, chunk_size= 50_000)
#
            x, y = xy[:, 0], xy[:, 1]
            # reshape the coordinates
            x_grid = np.reshape(x, (Nj, Ni))
            y_grid = np.reshape(y, (Nj, Ni))

        return (x_grid, y_grid)

    def _get_corners_coordinates(self, filename: GribFiles,
                                 run_date: str,
                                 EPSG:str = 'EPSG:31370') -> tuple[tuple[np.ndarray, np.ndarray]]:
        """
        Load GRIB data and compute coordinates.

        :param filename: The GRIB file to process.
        :param forecast: The forecast time.
        :param download: Whether to download the file if it doesn't exist.
        :param EPSG: The target EPSG code for the output coordinates.
        :return: The coordinates (x, y) for (center, lower-left, lower-right, upper-right, upper-left).
        """

        CHUNK_SIZE = 200_000

        file_path = self.download_data(filename, run_date)

        if not file_path.exists():
            logging.error(f"File {file_path} does not exist.")
            return np.array([])

        with open(file_path, 'rb') as f:
            gid = codes_grib_new_from_file(f)

            # Type de grille
            grid_type = codes_get(gid, "gridType")
            logging.info(f"Type de grille : {grid_type}")

            # Dimensions de la grille
            Ni = codes_get(gid, "Ni")  # nombre de points en longitude
            Nj = codes_get(gid, "Nj")  # nombre de points en latitude
            logging.info(f"Dimensions : {Ni} x {Nj}")

            # Coordonnées du premier et dernier point
            lat1 = codes_get(gid, "latitudeOfFirstGridPointInDegrees")
            lon1 = codes_get(gid, "longitudeOfFirstGridPointInDegrees")
            lat2 = codes_get(gid, "latitudeOfLastGridPointInDegrees")
            lon2 = codes_get(gid, "longitudeOfLastGridPointInDegrees")
            logging.info(f"Grille de ({lat1}, {lon1}) à ({lat2}, {lon2})")

            # Incréments
            dlat = codes_get(gid, "jDirectionIncrementInDegrees")
            dlon = codes_get(gid, "iDirectionIncrementInDegrees")
            logging.info(f"Incréments : {dlon}° en longitude, {dlat}° en latitude")

            # Reconstruire les coordonnées
            lats = np.linspace(lat1, lat2, Ni)
            lons = np.linspace(lon1, lon2, Nj)

            # ---------------
            # ATTENTION : data are enumerated longitude first, then latitude
            # We need to use meshgrid to get the correct order
            lon_grid, lat_grid = np.meshgrid(lons, lats)
            # ---------------

            lat_corners_ll = lat_grid.copy()
            lat_corners_ul = lat_grid.copy()

            lon_corners_ll = lon_grid.copy()
            lon_corners_lr = lon_grid.copy()

            # Estimate Corners by averaging the nearest neighbors
            lat_corners_ll[1:, :] = (lat_grid[:-1, :] + lat_grid[1:, :]) / 2
            lat_corners_ul[:-1, :] = (lat_grid[:-1, :] + lat_grid[1:, :]) / 2

            lat_corners_ll[0, :] = lat_grid[0, :] - dlat / 2
            lat_corners_ul[-1, :] = lat_grid[-1, :] + dlat / 2

            lat_corners_lr = lat_corners_ll.copy()
            lat_corners_ur = lat_corners_ul.copy()

            lon_corners_ll[:, 1:] = (lon_grid[:, :-1] + lon_grid[:, 1:]) / 2
            lon_corners_lr[:, :-1] = (lon_grid[:, :-1] + lon_grid[:, 1:]) / 2

            lon_corners_ll[:, 0] = lon_grid[:, 0] - dlon / 2
            lon_corners_lr[:, -1] = lon_grid[:, -1] + dlon / 2

            lon_corners_ul = lon_corners_ll.copy()
            lon_corners_ur = lon_corners_lr.copy()

            # Convert to numpy arrays
            lats = lat_grid.flatten()
            lons = lon_grid.flatten()
            lat_corners_ll = lat_corners_ll.flatten()
            lon_corners_ll = lon_corners_ll.flatten()
            lat_corners_ul = lat_corners_ul.flatten()
            lon_corners_ul = lon_corners_ul.flatten()
            lat_corners_lr = lat_corners_lr.flatten()
            lon_corners_lr = lon_corners_lr.flatten()
            lat_corners_ur = lat_corners_ur.flatten()
            lon_corners_ur = lon_corners_ur.flatten()

            # Convert to Lambert 72 E
            xy_center = transform_coordinates(np.vstack([lons, lats]).T, "EPSG:4326", EPSG, chunk_size= CHUNK_SIZE)

            # concatenate
            all_corners = np.concatenate((np.vstack([lon_corners_ll, lat_corners_ll]).T,
                                         np.vstack([lon_corners_ul, lat_corners_ul]).T,
                                         np.vstack([lon_corners_lr, lat_corners_lr]).T,
                                         np.vstack([lon_corners_ur, lat_corners_ur]).T))
            all_corners = transform_coordinates(all_corners, "EPSG:4326", EPSG, chunk_size= CHUNK_SIZE)

            # split
            xy_corners_ll = all_corners[0:Ni*Nj, :]
            xy_corners_ul = all_corners[Ni*Nj:2*Ni*Nj, :]
            xy_corners_lr = all_corners[2*Ni*Nj:3*Ni*Nj, :]
            xy_corners_ur = all_corners[3*Ni*Nj:4*Ni*Nj, :]
#
            x, y = xy_center[:, 0], xy_center[:, 1]
            # reshape the coordinates
            x_grid = np.reshape(x, (Nj, Ni))
            y_grid = np.reshape(y, (Nj, Ni))

            x_ll, y_ll = xy_corners_ll[:, 0], xy_corners_ll[:, 1]
            x_ul, y_ul = xy_corners_ul[:, 0], xy_corners_ul[:, 1]
            x_lr, y_lr = xy_corners_lr[:, 0], xy_corners_lr[:, 1]
            x_ur, y_ur = xy_corners_ur[:, 0], xy_corners_ur[:, 1]

            x_ll = np.reshape(x_ll, (Nj, Ni))
            y_ll = np.reshape(y_ll, (Nj, Ni))
            x_ul = np.reshape(x_ul, (Nj, Ni))
            y_ul = np.reshape(y_ul, (Nj, Ni))
            x_lr = np.reshape(x_lr, (Nj, Ni))
            y_lr = np.reshape(y_lr, (Nj, Ni))
            x_ur = np.reshape(x_ur, (Nj, Ni))
            y_ur = np.reshape(y_ur, (Nj, Ni))

        return (x_grid, y_grid), (x_ll, y_ll), (x_lr, y_lr), (x_ur, y_ur), (x_ul, y_ul)

    def _prepare_gdf_from_grib(self, filename: GribFiles,
                           run_date: str,
                           EPSG:str = 'EPSG:31370') -> gpd.GeoDataFrame:
        """
        Prepare a GeoDataFrame from grib file.

        :param filename: The GRIB file to process.
        :param forecast: The forecast time.
        :param EPSG: The target EPSG code for the output coordinates.
        :return: The GeoDataFrame with polygons for each grid cell.
        """

        file_path = self.download_data(filename, run_date)

        if not file_path.exists():
            logging.error(f"File {file_path} does not exist.")
            return np.array([])

        (x_grid, y_grid), (x_ll, y_ll), (x_lr, y_lr), (x_ur, y_ur), (x_ul, y_ul) = self._get_corners_coordinates(filename, run_date, EPSG)

        # Create polygons around the grid points
        # Corners are between grid points, so we need to create polygons

        Ni, Nj = x_grid.shape
        polygons = [Polygon([(x_ll[i, j], y_ll[i, j]),
                                (x_lr[i, j], y_lr[i, j]),
                                (x_ur[i, j], y_ur[i, j]),
                                (x_ul[i, j], y_ul[i, j])])
                        for i in range(Ni) for j in range(Nj)]

        data = {}
        data['centroid_x'] = x_grid.flatten()
        data['centroid_y'] = y_grid.flatten()
        self._gdf = gpd.GeoDataFrame(data, geometry=polygons, crs=EPSG)

        self._gdf_cache = self._gdf.copy()

        return self._gdf

    def _prepare_Zones_from_grib(self, filename: GribFiles,
                           run_date: str,
                           EPSG:str = 'EPSG:31370') -> Zones:
        """
        Prepare a Zones from brib file.

        :param filename: The GRIB file to process.
        :param forecast: The forecast time.
        :param EPSG: The target EPSG code for the output coordinates.
        :return: The Zones with polygons for each grid cell.
        """
        file_path = self.download_data(filename, run_date)

        if not file_path.exists():
            logging.error(f"File {file_path} does not exist.")
            return np.array([])

        (x_grid, y_grid), (x_ll, y_ll), (x_lr, y_lr), (x_ur, y_ur), (x_ul, y_ul) = self._get_corners_coordinates(filename, run_date, EPSG)

        # Create polygons around the grid points
        # Corners are between grid points, so we need to create polygons

        self._zones = Zones(idx = 'Alaro forecasts')

        Ni, Nj = x_grid.shape
        polygons = [Polygon([(x_ll[i, j], y_ll[i, j]),
                                (x_lr[i, j], y_lr[i, j]),
                                (x_ur[i, j], y_ur[i, j]),
                                (x_ul[i, j], y_ul[i, j])])
                        for i in range(Ni) for j in range(Nj)]

        for i in range(Ni):
            for j in range(Nj):
                loczone = zone(name=f"Alaro_{i}_{j}")
                self._zones.add_zone(loczone, forceparent = True)
                locvec = vector(name=f"Alaro_{i}_{j}_polygon")
                loczone.add_vector(locvec, forceparent=True)
                locvec.add_vertex([wv(x_ll[i, j], y_ll[i, j]),
                                   wv(x_lr[i, j], y_lr[i, j]),
                                   wv(x_ur[i, j], y_ur[i, j]),
                                   wv(x_ul[i, j], y_ul[i, j])])
                locvec.force_to_close()

        return self._zones

    def _load_grib_data(self, filename: GribFiles,
                       run_dates: str | list[str],
                       ) -> gpd.GeoDataFrame:
        """
        Load GRIB data from a file and add it to the GeoDataFrame.

        :param filename: The GRIB file to process.
        :param run_dates: The forecast run dates.
        :return: The GeoDataFrame with added data.
        """

        if isinstance(run_dates, str):
            run_dates = [run_dates]

        new_data = {}

        for run_date in run_dates:
            file_path = self.download_data(filename, run_date)

            if not file_path.exists():
                logging.error(f"File {file_path} does not exist.")
                return self._gdf

            with open(file_path, 'rb') as f:
                while True:
                    gid = codes_grib_new_from_file(f)

                    if gid is None:
                        break

                    # Dimensions de la grille
                    Ni = codes_get(gid, "Ni")  # nombre de points en longitude
                    Nj = codes_get(gid, "Nj")  # nombre de points en latitude

                    validityDate = codes_get(gid, "validityDate")
                    validityTime = codes_get(gid, "validityTime") // 100

                    # Valeurs du champ (ex. température, pression)
                    values = codes_get_values(gid)

                    # Reshape des valeurs si nécessaire
                    # data = np.reshape(values, (Nj, Ni))

                    new_data[f"{run_date}_{validityDate}_{validityTime:02d}"] = values

                    codes_release(gid)

        return new_data

    def reset_gdf(self):
        """ Reset the GeoDataFrame. """

        self._gdf = self._gdf_cache.copy() if self._gdf_cache is not None else None
        self._gdf_diff = None

    def load_grib_data_to_gdf(self, filename: GribFiles,
                       run_dates: str | list[str],
                       ) -> gpd.GeoDataFrame:
        """
        Load GRIB data from a file and add it to the GeoDataFrame.

        :param filename: The GRIB file to process.
        :param run_dates: The forecast run dates.
        :return: The GeoDataFrame with added data.
        """

        if isinstance(run_dates, str):
            run_dates = [run_dates]

        new_data = self._load_grib_data(filename, run_dates)

        if new_data is None:
            logging.error(f"No data found for {run_dates}.")
            return self._gdf

        if self._gdf is None:
            self._prepare_gdf_from_grib(filename, run_dates[0])

        if len(new_data) == 0:
            logging.error(f"No data found for {run_dates}.")
            return self._gdf

        new_gdf = gpd.GeoDataFrame(new_data)

        # Concatenate gdf and new_gdf
        self._gdf = pd.concat([self._gdf, new_gdf], axis=1)

        return self._gdf

    def load_grib_data_to_Zones(self, filename: GribFiles,
                                run_dates: str | list[str],
                                ) -> gpd.GeoDataFrame:
        """
        Load GRIB data from a file and add it to the Zones.

        :param filename: The GRIB file to process.
        :param run_dates: The forecast run dates.
        :return: The Zones with added data.
        """

        new_data = self._load_grib_data(filename, run_dates)

        if self._zones is None:
            self._prepare_zones_from_grib(filename, run_dates[0])

        if len(new_data) == 0:
            logging.error(f"No data found for {run_dates}.")
            return self._zones

        # Put values in zones
        for key, values in new_data.items():
            self._zones.add_values(key, values)

        return self._zones

    def forecasts_to_arrays(self, forecasts: str | list[str] = None) -> list[WolfArray]:
        """ Set the forecasts to the WolfArray.

        :param forecasts: List of forecast columns to convert to WolfArray. If None, all forecast columns are used.
        """

        if forecasts is None:
            forecasts = self.get_forecast_columns()

        elif isinstance(forecasts, str):
            forecasts = [forecasts]

        # Create a numpy array from centroid and values from forecast column
        xyz = np.zeros((self._gdf.shape[0], 3))
        xyz[:,0] = self._gdf["centroid_x"].values
        xyz[:,1] = self._gdf["centroid_y"].values

        arrays = []
        for forecast in forecasts:
            if not forecast in self._gdf.columns:
                logging.error(f"Forecast {forecast} not found in GeoDataFrame columns.")
                continue

            xyz[:,2] = self._gdf[forecast].values

            new_array = WolfArray(mold=self._array, idx=forecast)
            new_array.fillin_from_xyz(xyz)
            arrays.append(new_array)

        return arrays

    def get_forecast_columns(self, diff:bool = False) -> list[str]:
        """ Get the list of forecast columns in the GeoDataFrame.

        Exclude 'geometry', 'centroid_x', 'centroid_y' columns.

        :param diff: If True, get columns from the diff GeoDataFrame.
        """

        if diff:
            if self._gdf_diff is None:
                self._compute_diff()
            columns = self._gdf_diff.columns
            # pop 'geometry', 'centroid_x', 'centroid_y'
            columns = columns[columns != 'centroid_x']
            columns = columns[columns != 'centroid_y']
            columns = columns[columns != 'geometry']
            columns = [col for col in columns if col is not None]

        else:
            if self._gdf is None:
                logging.error("No data loaded. Please load GRIB data first.")
                return []

            columns = self._gdf.columns
            # pop 'geometry', 'centroid_x', 'centroid_y'
            columns = columns[columns != 'centroid_x']
            columns = columns[columns != 'centroid_y']
            columns = columns[columns != 'geometry']
            columns = [col for col in columns if col is not None]

        return list(columns)

    def _compute_diff(self):
        """ Compute local rain by difference in total cumulated rainfall """

        if self._gdf is None:
            logging.error("No data loaded. Please load GRIB data first.")
            return None

        self._gdf_diff = self._gdf.copy()

        columns = self.get_forecast_columns(diff=True)
        # all date and hours
        dates_hours = list(set([col.split('_')[1] + '_' + col.split('_')[2] for col in columns]))
        rundates = list(set([col.split('_')[0] for col in columns]))
        rundates.sort()
        dates_hours.sort()

        columns_lists = []
        for datehour in dates_hours:
            columns_lists.append([f"{rundate}_{datehour}" if f"{rundate}_{datehour}" in columns else None for rundate in rundates])

        # Diff all columns
        ref = columns_lists[0]
        for cols in columns_lists[1:]:
            for loccol, locref in zip(cols, ref):
                self._gdf_diff[loccol] = 0.0
                if loccol is not None and locref is not None:
                    self._gdf_diff[locref] = self._gdf[loccol] - self._gdf[locref]

                    if self._gdf_diff[locref].min() < 0.:
                        logging.debug(f"Negative values found in column {loccol} : {self._gdf_diff[locref].min()}")
            ref = cols


    def _load_grib_metadata(self, filename: GribFiles, run_date: str) -> np.ndarray:
        """
        Load GRIB metadata from a file.

        :param filename: The GRIB file to process.
        :param run_date: The forecast run date.
        """
        file_path = self.download_data(filename, run_date)

        if not file_path.exists():
            logging.error(f"File {file_path} does not exist.")
            return np.array([])

        i=0
        with open(file_path, 'rb') as f:
            while True:
                gid = codes_grib_new_from_file(f)

                if gid is None:
                    break

                keys_iter = codes_keys_iterator_new(gid)
                while codes_keys_iterator_next(keys_iter):
                    key = codes_keys_iterator_get_name(keys_iter)
                    if "validity" in key:
                        print(key)

                print(i)
                i+=1


                # Dimensions de la grille
                Ni = codes_get(gid, "Ni")  # nombre de points en longitude
                Nj = codes_get(gid, "Nj")  # nombre de points en latitude
                time = codes_get(gid, "validityDate") * 10000 + codes_get(gid, "validityTime")
                date = codes_get(gid, "year"), codes_get(gid, "month"), codes_get(gid, "day"), codes_get(gid, "hour")
                name = codes_get(gid, "parameterName")
                units = codes_get(gid, "parameterUnits")
                step_units = codes_get(gid, "stepUnits")
                units2 = codes_get(gid, "units")
                start_step = codes_get(gid, "startStep")
                end_step = codes_get(gid, "endStep")

                dataDate = codes_get(gid, "dataDate")
                dataTime = codes_get(gid, "dataTime")
                # forecastTime = codes_get(gid, "forecastTime")
                stepRange = codes_get(gid, "stepRange")

                codes_release(gid)
        return

    def _create_animation(self, filename: GribFiles,
                     run_date: str,
                     bounds: list[list[float], list[float]] | str = 'Belgium',
                     vmin: float = None,
                     vmax: float = None,
                     factor: float = 1.0
                     ) -> animation.FuncAnimation:
        """
        Create a video from the GeoDataFrame data.

        :param filename: The GRIB file to process.
        :param run_date: The forecast run date to visualize.
        :param bounds: Bounds for the plot. Can be 'Belgium' or a list of [xlim, ylim].
        :param vmin: Minimum value for color scaling.
        :param vmax: Maximum value for color scaling.
        :param factor: Factor to multiply the data values for scaling.
        :return: The animation object.
        """

        self.load_grib_data_to_gdf(filename, run_date)

        from matplotlib.collections import PatchCollection
        from matplotlib.patches import Polygon as MplPolygon
        from matplotlib.cm import ScalarMappable
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        fig, ax = plt.subplots(figsize=(10, 10))

        columns = self.get_forecast_columns()

        # Filter columns containing the "run_date" string
        columns = [col for col in columns if col.startswith(run_date)]

        if vmin is None:
            vmin = self._gdf[columns].min().min()
        if vmax is None:
            vmax = self._gdf[columns].max().max()

        vmin *= factor
        vmax *= factor

        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        colors = self._colormap(norm(self._gdf[columns[0]].values * factor))

        # Création d'un axe pour la colorbar sans modifier ax
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)

        # Ajout de la colorbar
        sm = ScalarMappable(norm=norm, cmap=self._colormap)
        cbar = fig.colorbar(sm, cax=cax,)

        patches = [MplPolygon(geom.exterior.coords, closed=True) for geom in self._gdf.geometry]
        collection = PatchCollection(patches, facecolor=colors, edgecolor='black')

        ax.add_collection(collection)
        self._cities.plot(ax=ax, facecolor = 'none', edgecolor='black', linewidth=0.5)

        if bounds == 'Belgium':
            ax.set_xlim(self._cities.total_bounds[[0, 2]])
            ax.set_ylim(self._cities.total_bounds[[1, 3]])
        elif isinstance(bounds, list) and len(bounds) == 4:
            ax.set_xlim(bounds[0][0], bounds[0][1])
            ax.set_ylim(bounds[1][0], bounds[1][1])
        else:
            ax.set_xlim(self._gdf.total_bounds[[0, 2]])
            ax.set_ylim(self._gdf.total_bounds[[1, 3]])

        def update(column):
            new_colors = self._colormap(norm(self._gdf[column].values * factor))
            collection.set_color(new_colors)

            ax.set_title(f"Total Precip. for {_convert_col2date_str(column)} - [mm] - time UTC")
            if wx.GetApp() is not None:
                wx.GetApp().Yield()  # Allow GUI to update

        ani = animation.FuncAnimation(fig, update, frames=columns, repeat=False)

        return ani

    def _create_comparison_animation(self, filename: GribFiles,
                                     run_dates: list[str],
                                     size = 10,
                                     bounds: list[list[float], list[float]] | str = 'Belgium',
                                     vmin:float = None,
                                     vmax:float = None,
                                     factor: float = 1.0) -> animation.FuncAnimation:
        """
        Create a video from the GeoDataFrame data.

        :param filename: The GRIB file to process.
        :param run_dates: List of forecast run dates to compare.
        :param size: Size of each subplot.
        :param bounds: Bounds for the plot. Can be 'Belgium' or a list of [xlim, ylim].
        :param vmin: Minimum value for color scaling.
        :param vmax: Maximum value for color scaling.
        :param factor: Factor to multiply the data values for scaling.
        :return: The animation object.
        """

        assert len(run_dates) > 1, "At least two forecasts must be provided."

        self.load_grib_data_to_gdf(filename, run_dates)

        from matplotlib.collections import PatchCollection
        from matplotlib.patches import Polygon as MplPolygon
        from matplotlib.cm import ScalarMappable
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        fig, axes = plt.subplots(ncols=len(run_dates), figsize=(len(run_dates) * size, size))

        fig.suptitle(_('Rain intensity [mm/h]'))

        columns = self.get_forecast_columns(diff=False)
        # all date and hours
        dates_hours = list(set([col.split('_')[1] + '_' + col.split('_')[2] for col in columns]))
        dates_hours.sort()

        columns_lists = []
        for datehour in dates_hours:
            columns_lists.append([f"{forecast}_{datehour}" if f"{forecast}_{datehour}" in columns else None for forecast in run_dates])

        if vmin is None:
            vmin = self._gdf[columns].min().min()
        if vmax is None:
            vmax = self._gdf[columns].max().max()

        vmin *= factor
        vmax *= factor

        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        colors = self._colormap(norm(self._gdf[columns[0]].values * factor))

        # Création d'un axe pour la colorbar sans modifier ax
        divider = make_axes_locatable(axes[-1])
        cax = divider.append_axes("right", size="5%", pad=0.1)

        # Ajout de la colorbar
        sm = ScalarMappable(norm=norm, cmap=self._colormap)
        cbar = fig.colorbar(sm, cax=cax,)

        patches = []
        collection = []
        for idx, forecast in enumerate(run_dates):
            patches.append([MplPolygon(geom.exterior.coords, closed=True) for geom in self._gdf.geometry])
            collection.append(PatchCollection(patches[idx], facecolor=colors, edgecolor='black'))

            ax = axes[idx]
            ax.add_collection(collection[idx])
            # Plot cities but just the edges
            self._cities.plot(ax=ax, facecolor = 'none', edgecolor='black', linewidth=0.5)

            if bounds == 'Belgium':
                ax.set_xlim(self._cities.total_bounds[[0, 2]])
                ax.set_ylim(self._cities.total_bounds[[1, 3]])
            elif isinstance(bounds, list) and len(bounds) == 4:
                ax.set_xlim(bounds[0][0], bounds[0][1])
                ax.set_ylim(bounds[1][0], bounds[1][1])
            else:
                ax.set_xlim(self._gdf.total_bounds[[0, 2]])
                ax.set_ylim(self._gdf.total_bounds[[1, 3]])
            ax.set_aspect('equal')

        fig.tight_layout()

        def update(column):
            for idx, ax in enumerate(axes):
                if column[idx] is None:
                    # All white
                    new_colors = np.ones((self._gdf.shape[0], 4))
                else:
                    new_colors = self._colormap(norm(self._gdf[column[idx]].values * factor))
                collection[idx].set_color(new_colors)
                ax.set_title(f"{_convert_col2date_str(column[idx])} - time UTC")

                if wx.GetApp() is not None:
                    wx.GetApp().Yield()  # Allow GUI to update

            # ax.set_title(f"Data for {column}")

        ani = animation.FuncAnimation(fig, update, frames=columns_lists, repeat=False)

        return ani

    def _create_comparison_animation_diff(self, filename: GribFiles,
                                     run_dates: list[str],
                                     size = 10,
                                     bounds: list[list[float], list[float]] | str = 'Belgium',
                                     vmin:float = None,
                                     vmax:float = None,
                                     factor: float = 1.0) -> animation.FuncAnimation:
        """
        Create a video from the GeoDataFrame data.

        :param filename: The GRIB file to process.
        :param run_dates: List of forecast run dates to compare.
        :param size: Size of each subplot.
        :param bounds: Bounds for the plot. Can be 'Belgium' or a list of [xlim, ylim].
        :param vmin: Minimum value for color scaling.
        :param vmax: Maximum value for color scaling.
        :param factor: Factor to multiply the data values for scaling.
        :return: The animation object.
        """

        assert len(run_dates) > 1, "At least two forecasts must be provided."

        self.load_grib_data_to_gdf(filename, run_dates)
        self._compute_diff()

        from matplotlib.collections import PatchCollection
        from matplotlib.patches import Polygon as MplPolygon
        from matplotlib.cm import ScalarMappable
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        fig, axes = plt.subplots(ncols=len(run_dates), figsize=(len(run_dates) * size, size))

        fig.suptitle(_('Rain intensity [mm/h]'))

        columns = self.get_forecast_columns(diff=True)
        # all date and hours
        dates_hours = list(set([col.split('_')[1] + '_' + col.split('_')[2] for col in columns]))
        dates_hours.sort()

        columns_lists = []
        for datehour in dates_hours:
            columns_lists.append([f"{forecast}_{datehour}" if f"{forecast}_{datehour}" in columns else None for forecast in run_dates])

        if vmin is None:
            vmin = self._gdf_diff[columns].min().min()
        if vmax is None:
            vmax = self._gdf_diff[columns].max().max()

        vmin *= factor
        vmax *= factor

        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        colors = self._colormap(norm(self._gdf_diff[columns[0]].values * factor))

        # Création d'un axe pour la colorbar sans modifier ax
        divider = make_axes_locatable(axes[-1])
        cax = divider.append_axes("right", size="5%", pad=0.1)

        # Ajout de la colorbar
        sm = ScalarMappable(norm=norm, cmap=self._colormap)
        cbar = fig.colorbar(sm, cax=cax,)

        patches = []
        collection = []
        for idx, forecast in enumerate(run_dates):
            patches.append([MplPolygon(geom.exterior.coords, closed=True) for geom in self._gdf_diff.geometry])
            collection.append(PatchCollection(patches[idx], facecolor=colors, edgecolor='black'))

            ax = axes[idx]
            ax.add_collection(collection[idx])
            # Plot cities but just the edges
            self._cities.plot(ax=ax, facecolor = 'none', edgecolor='black', linewidth=0.5)

            if bounds == 'Belgium':
                ax.set_xlim(self._cities.total_bounds[[0, 2]])
                ax.set_ylim(self._cities.total_bounds[[1, 3]])
            elif isinstance(bounds, list) and len(bounds) == 4:
                ax.set_xlim(bounds[0][0], bounds[0][1])
                ax.set_ylim(bounds[1][0], bounds[1][1])
            else:
                ax.set_xlim(self._gdf_diff.total_bounds[[0, 2]])
                ax.set_ylim(self._gdf_diff.total_bounds[[1, 3]])
            ax.set_aspect('equal')

        fig.tight_layout()

        def update(column):
            for idx, ax in enumerate(axes):
                if column[idx] is None:
                    # All white
                    new_colors = np.ones((self._gdf_diff.shape[0], 4))
                else:
                    new_colors = self._colormap(norm(self._gdf_diff[column[idx]].values * factor))
                collection[idx].set_color(new_colors)
                ax.set_title(_convert_col2date_str(column[idx]))

                if wx.GetApp() is not None:
                    wx.GetApp().Yield()  # Allow GUI to update

        ani = animation.FuncAnimation(fig, update, frames=columns_lists, repeat=False)

        return ani

    def __del__(self):
        """
        Destructor to ensure the FTP connection is closed.
        """
        try:
            self._ftp_close()
        except Exception as e:
            logging.error(f"Error closing FTP connection: {e}")

    def video_cumulated_rain(self, run_date:str, output_file:Path, fps:int = 2):
        """
        Create a MP4 video comparison of cumulated rain forecasts.

        :param forecast: The forecast date string.
        :param output_file: The output MP4 file path.
        :param fps: Frames per second for the video.
        """

        output_file = Path(output_file)

        if output_file.suffix != '.mp4':
            output_file = output_file.with_suffix('.mp4')

        ani = self._create_animation(GribFiles.FILE_TotPrecip, run_date, factor=1000.)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        ani.save(output_file, writer='ffmpeg', fps=fps)

        return output_file

    def videos_cumulated_rain_allforecasts(self, output_dir:Path, fps:int = 2, run_dates: str | list[str] = None) -> list[Path] | None:
        """
        Create a MP4 video comparison of cumulated rain forecasts.

        :param output_dir: The output directory for the MP4 files.
        :param fps: Frames per second for the video.
        """
        output_dir = Path(output_dir)

        if run_dates is not None:
            if isinstance(run_dates, str):
                files = [run_dates]
            files = run_dates
        else:
            files = self.run_dates

        if files:
            videos_out = []
            output_dir.mkdir(parents=True, exist_ok=True)
            for forecast in files:
                output_file = output_dir / f"Alaro_cumulated_rain_{forecast}.mp4"
                self.video_cumulated_rain(forecast, output_file, fps=fps)
                videos_out.append(output_file)

            return videos_out
        return None

    def video_gradient_cumulated_rain_compare(self, output_file:Path, fps:int = 2, run_dates: str | list[str] = None) -> Path | None:
        """
        Create a MP4 video comparison of cumulated rain forecasts.

        :param output_file: The output MP4 file path.
        :param fps: Frames per second for the video.
        """

        output_file = Path(output_file)

        if output_file.suffix != '.mp4':
            output_file = output_file.with_suffix('.mp4')

        if run_dates is None:
            files = self.list_run_dates()
        elif isinstance(run_dates, str):
            files = [run_dates]
        else:
            files = run_dates

        if files:
            ani = self._create_comparison_animation_diff(GribFiles.FILE_TotPrecip, files, factor=1000.)

            output_file.parent.mkdir(parents=True, exist_ok=True)
            ani.save(output_file, writer='ffmpeg', fps=fps)

            return output_file
        return None

    def convert_gdf2dataframe(self, X:float, Y:float, use_diff:bool = False) -> pd.DataFrame:
        """
        Convert the GeoDataFrame to a Pandas DataFrame for a given point (X, Y).

        :param X: The X coordinate.
        :param Y: The Y coordinate.
        :return: The Pandas DataFrame with the data for the nearest grid cell.
        """

        if self._gdf is None:
            logging.error("No data loaded. Please load GRIB data first.")
            return pd.DataFrame()

        if use_diff and self._gdf_diff is None:
            self._compute_diff()

        gdf = self._gdf_diff if use_diff else self._gdf

        point = Point(X, Y)
        # Find the nearest polygon
        distances = gdf.geometry.distance(point)
        idx_min = distances.idxmin()

        # The data are currently stored columns wise, we want to return a Dataframe with 3 columns:
        # 'forecast_date', 'value', 'run_date'
        # where 'forecast_date' is the date of the forecast, 'value' is the
        # value of the forecast, and 'run_date' is the date of the run.
        # The index of the dataframe is a combination of 'run_date'_'forecast_date'

        columns = self.get_forecast_columns()
        df = pd.DataFrame({
            'forecast_date': [_extract_dates_from_columnstr(col)[1] for col in columns],
            'value': [gdf.loc[idx_min][col] for col in columns],
            'run_date': [_extract_dates_from_columnstr(col)[0] for col in columns]
        })

        return df

    def _plot4XY(self, X:float, Y:float, factor:float = 1., size:tuple[int, int]=(10, 5), use_diff:bool = False, figax:tuple[plt.Figure, plt.Axes] = None) -> plt.Figure:
        """
        Plot the data for a given point (X, Y).

        :param X: The X coordinate.
        :param Y: The Y coordinate.
        :param factor: The factor to multiply the data values for scaling.
        :param size: The size of the plot.
        :return: The Matplotlib Figure object.
        """

        df = self.convert_gdf2dataframe(X, Y, use_diff=use_diff)

        if df.empty:
            logging.error("No data available for the given point.")
            return None

        if figax is not None:
            fig, ax = figax
        else:
            fig, ax = plt.subplots(figsize=size)

        # Pivot the dataframe to have 'forecast_date' as index and 'run_date' as columns
        df_pivot = df.pivot(index='forecast_date', columns='run_date', values='value')

        # Plot each run_date as a separate line
        for run_date in df_pivot.columns:
            ax.plot(df_pivot.index, df_pivot[run_date] * factor, marker='o', label=run_date)

        ax.set_title(f"Total precipitation at point ({X}, {Y})")
        ax.set_xlabel("Forecast Date (time zone: UTC)")
        ax.set_ylabel("Total precipitation [mm]")
        ax.legend(title="Run Date")
        ax.grid(True)

        # Set xticks every rounded 6 hours
        import matplotlib.dates as mdates
        ax.set_xlim([df_pivot.index.min(), df_pivot.index.max()])
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H+00'))

        fig.autofmt_xdate()

        return fig

    def _bar4XY(self, X:float, Y:float, factor:float = 1., size:tuple[int, int]=(10, 5), use_diff:bool = False, figax:tuple[plt.Figure, plt.Axes] = None) -> plt.Figure:
        """
        Plot the data for a given point (X, Y).

        :param X: The X coordinate.
        :param Y: The Y coordinate.
        :param factor: The factor to multiply the data values for scaling.
        :param size: The size of the plot.
        :return: The Matplotlib Figure object.
        """

        df = self.convert_gdf2dataframe(X, Y, use_diff=use_diff)

        if df.empty:
            logging.error("No data available for the given point.")
            return None

        if figax is not None:
            fig, ax = figax
        else:
            fig, ax = plt.subplots(figsize=size)

        # Pivot the dataframe to have 'forecast_date' as index and 'run_date' as columns
        df_pivot = df.pivot(index='forecast_date', columns='run_date', values='value')

        # Plot each run_date as a separate line
        for run_date in df_pivot.columns:
            # Filter Nan value
            used_range = df_pivot[run_date].notna()
            ax.bar(df_pivot.index[used_range], df_pivot[run_date][used_range] * factor, width=td(seconds=3600), label=run_date, align='edge', alpha=0.7)

        ax.set_title(f"Rain intensity at point ({X}, {Y})")
        ax.set_xlabel("Forecast Date (time zone: UTC)")
        ax.set_ylabel("Rain intensity [mm/h]")

        # Set xticks every rounded 6 hours
        import matplotlib.dates as mdates
        ax.set_xlim([df_pivot.index.min(), df_pivot.index.max()])
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H+00'))

        ax.legend(title="Run Date")
        ax.grid(True)

        fig.autofmt_xdate()

        return fig

    def plot_TotPrec4XY(self, X:float, Y:float, size:tuple[int, int]=(10, 5)) -> plt.Figure:
        """
        Plot the total precipitation data for a given point (X, Y).

        :param X: The X coordinate.
        :param Y: The Y coordinate.
        :param size: The size of the plot.
        :return: The Matplotlib Figure object.
        """

        if self._gdf is None:
            self.load_grib_data_to_gdf(GribFiles.FILE_TotPrecip, self.run_dates)

        return self._plot4XY(X, Y, factor=1000., size=size)

    def plot_RainIntensity4XY(self, X:float, Y:float, size:tuple[int, int]=(10, 5)) -> plt.Figure:
        """
        Plot the rain intensity data for a given point (X, Y).

        :param X: The X coordinate.
        :param Y: The Y coordinate.
        :param size: The size of the plot.
        :return: The Matplotlib Figure object.
        """

        if self._gdf is None:
            self.load_grib_data_to_gdf(GribFiles.FILE_TotPrecip, self.run_dates)

        fig = self._bar4XY(X, Y, factor=1000., size=size, use_diff=True)

        return fig

    def plot_Rain_and_TotPrecip4XY(self, X:float, Y:float, size:tuple[int, int]=(10, 10)) -> plt.Figure:
        """
        Plot the rain intensity and total precipitation data for a given point (X, Y).

        :param X: The X coordinate.
        :param Y: The Y coordinate.
        :param size: The size of the plot.
        :return: The Matplotlib Figure object.
        """

        if self._gdf is None:
            self.load_grib_data_to_gdf(GribFiles.FILE_TotPrecip, self.run_dates)

        fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=size)

        self._plot4XY(X, Y, factor=1000., size=size, use_diff=False, figax=(fig, ax1))
        self._bar4XY(X, Y, factor=1000., size=size, use_diff=True, figax=(fig, ax2))

        fig.tight_layout()

        return fig