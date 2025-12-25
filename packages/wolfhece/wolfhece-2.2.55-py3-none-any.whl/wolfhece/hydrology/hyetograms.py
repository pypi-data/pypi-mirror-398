import numpy  as np
import csv
import time as time_mod
import sys                              # module to stop the program when an error is encountered
import json                             # mudule to use json file
import pandas as pd                     # module to write data in Excel file
from datetime import datetime as dt     # module which contains objects treating dates
from datetime import timezone as tz  # module which contains objects treating time zones
from datetime import timedelta as td  # module which contains objects treating time deltas
import matplotlib.pyplot as plt
from dbfread import DBF                 # module to treat DBF files

from pathlib import Path
import logging
from tqdm import tqdm
import matplotlib.pyplot as plt

from functools import cached_property

import geopandas as gpd
from shapely.geometry import Point, Polygon
import seaborn as sns

from .constant import source_point_measurements, source_IRM, source_dist
from .read import check_path
from ..PyVertexvectors import Zones, zone, vector, wolfvertex
from ..PyTranslate import _
from .climate_data import read_all_data, read_historical_year_month, find_first_available_year_month, find_last_available_year_month, read_pixel_positions, convert_pixels_to_squares, read_between

class ClimateData_IRM:
    """
    Class to handle IRM climate data.

    Data are available for academic purposes only on https://opendata.meteo.be/. Please read carefully the terms of use before using this data.
    Without valid data, the class will not work.
    """

    def __init__(self, workingDir: str | Path = Path(r'P:\Donnees\Pluies\IRM\climateGrid')):
        """
        Initialize the ClimateData_IRM class.

        :param workingDir: The directory where the IRM data is stored.
        """

        self.workingDir = Path(workingDir)
        self._data:pd.DataFrame = None

        self._grid: Zones = None
        self._kdtree = None

        # Check if the working directory exists
        if not self.workingDir.exists():
            logging.error(_("The working directory {} does not exist.").format(self.workingDir))
            return

        self._start_time = find_first_available_year_month(self.workingDir)
        self._end_time = find_last_available_year_month(self.workingDir)

    @property
    def variables(self) -> list[str]:
        """
        Return the list of variables available in the IRM data.

        Available variables should be :
        - day
        - temp_max
        - temp_min
        - temp_avg
        - precip_quantity
        - humidity_relative
        - pressure
        - sun_duration
        - short_wave_from_sky
        - evapotrans_ref

        Values are from +0800 of the day, to +0800 of the next day.
        """
        if self._data is not None:
            return self._data.columns.tolist()
        else:
            return []

    @property
    def data(self) -> pd.DataFrame:
        """
        Return the data as a pandas DataFrame.
        If the data is not read yet, return None.
        """
        if self._data is None:
            logging.error(_("Data not read yet. Please call read_data() first."))
            return None

        return self._data

    def __str__(self):
        ret = _("IRM Climate Data\n")
        ret += _(" - Working Directory: {}\n").format(self.workingDir)
        ret += _(" - Data from {} to {}\n").format(self._start_time, self._end_time)
        ret += _(" - Available Variables: {}\n").format(", ".join(self.variables))
        return ret

    def read_data(self, all:bool = True, start_yearmonth:tuple[int, int] = None, end_yearmonth:tuple[int, int] = None):
        """ Read the IRM data from the working directory. """

        if all and (start_yearmonth is not None or end_yearmonth is not None):
            logging.warning(_("You cannot specify start and end year/month when reading all data. Ignoring the specified dates."))

        if all:
            # Read all data from the working directory
            self._data = read_all_data(self.workingDir)
        else:
            if start_yearmonth is None or end_yearmonth is None:
                logging.error(_("You must provide start and end year/month to read data."))
                return

            if start_yearmonth is None:
                start_yearmonth = self._start_time
            if end_yearmonth is None:
                end_yearmonth = self._end_time

            # Read data for the specified year/month
            self._data = read_between(self.workingDir, start_yearmonth[0], start_yearmonth[1], end_yearmonth[0], end_yearmonth[1])

    def _create_zones(self):
        """ Create zones for the pixels and their squares. """

        self.pixels_id, self._xy = read_pixel_positions(self.workingDir)

        if self.pixels_id is None or self._xy is None:
            logging.error(_("No pixel positions found in the working directory {}.").format(self.workingDir))
            return

        squares, self._kdtree = convert_pixels_to_squares(self._xy)

        self._grid = Zones(idx = 'climategrid')
        pixel_zone = zone(name = 'pixels_footprint')
        pixel_center = zone(name = 'pixels_center')

        self._grid.add_zone(pixel_zone, forceparent = True)
        self._grid.add_zone(pixel_center, forceparent = True)

        for i, xy in enumerate(self._xy):
            x, y = xy
            # create a vertex for the pixel center
            vec = vector(name = "Pixel_{}".format(i + 1))
            vec.add_vertex(wolfvertex(x-50, y-50))
            vec.add_vertex(wolfvertex(x+50, y-50))
            vec.add_vertex(wolfvertex(x+50, y+50))
            vec.add_vertex(wolfvertex(x-50, y+50))
            vec.force_to_close()
            vec._simplified_geometry = True
            vec.myprop.color = (0, 0, 255)  # blue color for the pixel center
            vec.myprop.width = 2
            pixel_center.add_vector(vec, forceparent= True)

        # create square vectors
        for i, square in enumerate(squares):
            (x1, y1), (x2, y2), (x3, y3), (x4, y4) = square
            vec = vector(name = "Pixel_{}".format(i + 1))
            vec.add_vertex(wolfvertex(x1, y1))
            vec.add_vertex(wolfvertex(x2, y2))
            vec.add_vertex(wolfvertex(x3, y3))
            vec.add_vertex(wolfvertex(x4, y4))
            vec.force_to_close()

            vec._simplified_geometry = True
            vec.myprop.legendtext = str(i + 1)  # set the legend text to the pixel id
            vec.set_legend_position((x1 + x3)/2., (y1 + y3)/2.)
            vec.myprop.legendvisible = True

            vec.myprop.color = (255, 0, 0)
            pixel_zone.add_vector(vec, forceparent= True)

    def plot(self, figax=None, title:str = None, with_ids:bool = False):
        """ Plot the GRID for IRM data. """

        if self._grid is None:
            self._create_zones()

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        self._grid['pixels_footprint'].set_legend_visible(with_ids)

        if self._grid is not None:
            self._grid.plot_matplotlib(ax=ax)

        if title is None:
            title = _("IRM Climate Data Grid")

        ax.set_aspect('equal')
        ax.set_title(title)
        fig.tight_layout()

        return fig, ax

    def as_zones(self) -> Zones:
        """
        Return the grid as a Zones object.
        If the zones are not created yet, create them.
        """
        if self._grid is None:
            self._create_zones()
        return self._grid

    def get_attribute4date(self, date:dt, variable:str) -> pd.DataFrame:
        """ Return the attribute for a specific date. """
        if self._data is None:
            logging.error(_("No data available. Please read the data first."))
            return None

        if variable not in self.variables:
            logging.error(_("The variable {} is not available in the data.").format(variable))
            return None

        # Check if the date is in the data
        if date not in self._data.day.unique():
            logging.error(_("The date {} is not available in the data.").format(date))
            return None

        return self._data[self._data.day == date][variable]

    def get_attribute4daterange(self, date_start:dt, date_end:dt, variable:str) -> pd.DataFrame:
        """ Return the attribute for a specific date range. """

        if self._data is None:
            logging.error(_("No data available. Please read the data first."))
            return None

        if variable not in self.variables:
            logging.error(_("The variable {} is not available in the data.").format(variable))
            return None

        # Check if the date range is valid
        if date_start > date_end:
            logging.error(_("The start date {} is after the end date {}.").format(date_start, date_end))
            return None

        return self._data[(self._data.day >= date_start) & (self._data.day <= date_end)][['day', variable]]

    def plot_spatial_attribute(self, date:dt, variable:str, figax=None, title:str = None, cmap:str = 'viridis'):
        """ Plot the spatial distribution of the attribute for a specific date. """

        assert variable in self.variables, _("The variable {} is not available in the data.").format(variable)
        assert date in self._data.day.unique(), _("The date {} is not available in the data.").format(date)

        if self._data is None:
            logging.error(_("No data available. Please read the data first."))
            return None, None

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        # Plot the data
        footprints = self._grid['pixels_footprint']
        footprints.add_values(variable, self.get_attribute4date(date, variable).to_numpy())

        footprints.set_colors_from_value(variable, cmap=cmap)
        footprints.set_filled(True)
        footprints.plot_matplotlib(ax)

        # footprints.set_filled(False)
        # footprints.plot_matplotlib(ax)

        if title is None:
            title = _("Spatial distribution of {} at {}").format(variable, date.strftime('%Y-%m-%d'))

        ax.set_title(title)

        return fig, ax

    def animation_spatial_attribute(self, variable:str, figax=None, date_start:dt = 0, date_end:dt = -1, cmap:str = 'viridis'):
        """
        Create an animation of the spatial distribution of a specific attribute over time.
        The animation will show the attribute data for each time step.

        :param figax: A tuple (fig, ax) to use for the animation. If None, a new figure and axes will be created.
        :param date_start: The starting date for the animation.
        :param date_end: The ending date for the animation. If -1, it will use the last date.
        :param cmap: The colormap to use for the attribute data.
        :param interval_days: The interval between frames in days.
        :return: The animation object.
        """

        import matplotlib.animation as animation

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        def update(frame):
            ax.clear()
            self.plot_spatial_attribute(frame, variable, figax=(fig, ax), title=None, cmap=cmap)

        if date_end == -1:
            date_end = self._data.day.max()
        if date_start == 0:
            date_start = self._data.day.min()

        unique_dates = self._data.day.unique()
        all_dates = [date for date in unique_dates if date_start <= date <= date_end]

        ani = animation.FuncAnimation(fig, update, frames=all_dates, interval=100)

        return ani

    def find_pixelid_from_X_Y(self, x:float, y:float) -> int:
        """
        Find the pixel id from the X and Y coordinates.
        :param x: The X coordinate.
        :param y: The Y coordinate.
        :return: The pixel id or None if not found.
        """
        if self._kdtree is None:
            self._create_zones()

        if self._kdtree is None:
            logging.error(_("No pixel positions found. Please read the data first."))
            return None

        return self._kdtree.query((x, y), k=1)[1] + 1

    def plot_hyetogram(self, position:list[float, float] | tuple[float, float], date_start:dt = 0, date_end:dt = -1, figax = None):
        """ Plot the hyetogram for a specific position over a date range.

        :param position: The position (x, y) for which to plot the hyetogram.
        :param date_start: The starting date for the hyetogram.
        :param date_end: The ending date for the hyetogram. If -1, it will use the last date.
        :param figax: A tuple (fig, ax) to use for the plot. If None, a new figure and axes will be created.
        """

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        if date_start == 0:
            date_start = self._data.day.min()
        if date_end == -1:
            date_end = self._data.day.max()

        pixel_id = self.find_pixelid_from_X_Y(position[0], position[1])

        if pixel_id is None:
            logging.error(_("No pixel found for position ({}, {}).").format(position[0], position[1]))
            return


        # Get the hyetogram data for the specified date range
        hyetogram_data = self.get_attribute4daterange(date_start, date_end, variable='precip_quantity')
        hyetogram_data = hyetogram_data[hyetogram_data.index == pixel_id]

        # Plot the hyetogram
        sns.barplot(data=hyetogram_data, x='day', y='precip_quantity',
                    ax=ax, color='blue', )
        hyetogram_data.plot(x='day', y='precip_quantity', ax=ax, kind='bar', align='center', color='blue')
        ax.set_xlabel(_("Date"))
        ax.set_ylabel(_("Precipitation (mm)"))
        ax.set_title(_("Hyetogram for position ({}, {})").format(position[0], position[1]))
        ax.set_xticklabels(hyetogram_data['day'].dt.strftime('%Y-%m-%d'), rotation=45)
        ax.set_ylim(bottom=0)
        fig.tight_layout()

        return fig, ax

class Rainfall_Gridded:
    """
    Class to handle gridded rainfall data.
    It can read gridded rainfall data.

    ATTENTION:
        - The grid is provided as a shapefile in the "Grid" subdirectory of the working directory.
        - The associated data are provided in the "data" or "IRM" subdirectory of the working directory.
        - The link between each polygon and the data is done thorugh the index of the polygon in the shapefile.
          BUT, as we come from Fortran-world, the index is supposed 1-based, not 0-based.
          The increment of the index is done in the "PyVertexvectors" module and checked in the "_read_grid" routine.

    """

    def __init__(self, workingDir: str | Path, type_of_rain:int = source_IRM | source_dist):

        self.workingDir = Path(workingDir)
        self.type_of_rain = type_of_rain
        self.is_binary = False

        self._grid: Zones = None
        self._data: dict[str | int, np.ndarray] = {}
        self._times: list[dt] = []

        assert self.type_of_rain in [source_IRM, source_dist], _("The type of rain is not supported. It should be either source_IRM or source_dist.")

        # Test if "Grid" is a subdirectory of the working directory
        self.gridDir = self.workingDir / "Grid"
        if not self.gridDir.exists():
            logging.warning(_("The directory {} does not exist.").format(self.gridDir))
            logging.info(_("Trying to find the directory in the parent directory."))

            # search the shapefiles in the parent directory
            shps = self.workingDir.parent.rglob("*.shp")
            shps = [x for x in shps if x.is_file() and x.suffix.lower() == '.shp']
            if len(shps) > 0:
                self.gridDir = shps[0].parent
                logging.info(_("The directory {} has been found.").format(self.gridDir))

        self.dataDir = self.workingDir / "data"
        if not self.dataDir.exists():
            logging.warning(_("The directory {} does not exist.").format(self.dataDir))
            logging.info(_("Trying to find the directory containing rain data."))
            # search the data directory in the parent directory
            rains = self.workingDir.parent.rglob("*.rain")
            dats = self.workingDir.parent.rglob("*.dat")

            rains = [x for x in rains if x.is_file() and x.suffix.lower() == '.rain']
            dats = [x for x in dats if x.is_file() and x.suffix.lower() == '.dat']
            if len(rains) > 0:
                self.dataDir = rains[0].parent
                logging.info(_("The directory {} has been found.").format(self.dataDir))
                self.is_binary = False
                logging.info(_("The data are considered in ASCII format."))
            if len(dats) > 0:
                self.dataDir = dats[0].parent
                logging.info(_("The directory {} has been found.").format(self.dataDir))
                self.is_binary = True
                logging.info(_("The data are considered in binary format."))

    def as_zones(self) -> Zones:
        """
        Return the grid as a Zones object.
        """
        if self._grid is None:
            self._read_grid()
        return self._grid

    @property
    def time_steps(self) -> list[td]:
        """
        Return the time step between each data point.
        """
        if len(self._times) < 2:
            return td(seconds=0)

        # Calculate the time difference between the each consecutive times
        return [self._times[i+1] - self._times[i] for i in range(len(self._times)-1)]

    def has_uniform_time_step(self) -> bool:
        """
        Check if the time step is uniform.
        """
        if len(self._times) < 2:
            return True

        # Calculate the time difference between the each consecutive times
        time_deltas = self.time_delta
        return all(td == time_deltas[0] for td in time_deltas)

    @property
    def time_step(self) -> td:
        """
        Return the time step between the two first data.
        """
        if len(self._times) < 2:
            return td(seconds=0)

        # Return the first time delta if uniform
        return self._times[1] - self._times[0]

    def read(self):
        """ Read grid and data from the working directory. """

        try:
            self._read_grid()
            self._read_associated_data()
            return True
        except Exception as e:
            logging.error(_("Error reading grid or data: {}").format(e))
            return False

    def _read_grid(self):
        """
        Read the grid data from the grid directory.
        The grid data should be in a shapefile format.
        """
        if not self.gridDir.exists():
            logging.error(_("The grid directory {} does not exist.").format(self.gridDir))
            return None

        # Read the shapefile
        try:
            shps = list(self.gridDir.glob("*.shp"))
            if len(shps) == 0:
                logging.error(_("No shapefile found in the directory {}.").format(self.gridDir))
                return None
            if len(shps) > 1:
                logging.warning(_("Multiple shapefiles found in the directory {}.").format(self.gridDir))
                logging.warning(_("Using the first shapefile found."))

            self._grid = Zones(shps[0])
            logging.info(_("Grid data read successfully from {}.").format(self.gridDir))

            # check that the zone names are 1-based
            no_error = True
            for i, curzone in enumerate(self._grid.myzones):
                if curzone.myname != str(i+1):
                    logging.error(_("The zone name {} is not 1-based.").format(curzone.myname))
                    logging.info(_("The zone name will be set to {}.").format(i+1))
                    no_error = False
                curzone.myname = str(i+1)  # set the zone name to 1-based index
            if no_error:
                logging.info(_("All zone names are 1-based."))

            return self._grid

        except Exception as e:
            logging.error(_("Error reading grid data: {}").format(e))
            return None

    def _read_associated_data(self):
        """ Read the date associeted to the grid. """

        if not self.dataDir.exists():
            logging.error(_("The data directory {} does not exist.").format(self.dataDir))
            return None

        # Read the data
        try:
            if self.is_binary:
                files = list(self.dataDir.glob("*.dat"))
            else:
                files = list(self.dataDir.glob("*.rain"))

            if len(files) == 0:
                logging.error(_("No data file found in the directory {}.").format(self.dataDir))
                return None

            # we assume the same number of files that the number of grid cells
            if len(files) != self._grid.nbzones:
                logging.error(_("The number of data files ({}) does not match the number of grid cells ({}).").format(len(files), self._grid.nbzones))

            if self.is_binary:
                self._data = [self._read_rain_binary(file) for file in files]
            else:
                self._data = [self._read_rain_ascii(file) for file in files]

            # Check if all times are the same
            times = [data[2] for data in self._data]
            if not all(t == times[0] for t in times):
                logging.error(_("The times in the data files do not match."))
                return None

            self._times = times[0]  # all times are the same, we can take the first one
            # Convert data to dictionnary
            self._data = {data[0]: data[1] for data in self._data}

            # Check if keys are in the grid
            for key in self._data.keys():
                if key not in self._grid.zone_names:
                    logging.error(_("The key {} is not in the grid.").format(key))
                    return None

            logging.info(_("Data read successfully from {}.").format(self.dataDir))
            return self._data

        except Exception as e:
            logging.error(_("Error reading data: {}").format(e))
            return None

    def _read_rain_ascii(self, filename: str | Path) -> tuple[str | int, np.ndarray, list[dt]]:
        """
        Read data from an ASCII file.
        The filename should end with .rain.

        Structure of the ASCII file:
        - 4 Header lines with :
            - The first line is a name of the series.
            - The second line is the number of data columns (n).
            - The third line is the total number of columns (n + 6).
            - The fourth line is the number of rows.
        - Each line represents a time step.
            - The first six columns are the day, month, year, hour, minute, and second.
            - The last column is the rain value.

        :param filename: The name of the file to read.

        """

        filename = Path(filename)

        assert filename.suffix == '.rain', _("The file name must end with .rain")

        with open(filename, 'r') as f:
            lines = f.readlines()

        # Read the header
        name_serie = lines[0].strip()
        ncols = int(lines[1].strip())
        nrows = int(lines[3].strip())

        data = np.zeros((nrows, ncols), dtype=np.float64)
        times = []

        # Read the data
        for i in range(nrows):
            line = lines[i + 4].strip().split('\t')
            day, month, year, hour, minute, second, rain = line
            times.append(dt(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=tz.utc))
            data[i, 0] = float(rain)

        # Convert to a 1D numpy array
        data = data.flatten()

        return name_serie, data, times

    def _read_rain_binary(self, filename: str | Path) -> tuple[int, np.ndarray, list[dt]]:
        """
        Read data from a binary file.
        The filename should end with .dat.

        Structure of the binary file:
        - 4 bytes for a "name" as integer
        - 4 bytes for the number of data columns (n)
        - 4 bytes for the total number of columns (n + 6)
        - 4 bytes for the number of rows
        - For each row:
            - 1 byte for the day
            - 1 byte for the month
            - 2 bytes for the year
            - 1 byte for the hour
            - 1 byte for the minute
            - 1 byte for the second
            - n*8 bytes for the rain value as float

        :param filename: The name of the file to read.
        :return: A numpy array with the rain data.
        """
        import struct

        filename = Path(filename)

        assert filename.suffix == '.dat', _("The file name must end with .dat")

        f = open(filename, 'rb')

        # Read the header
        name_serie = int.from_bytes(f.read(4), byteorder='little', signed=True)
        ncols = int.from_bytes(f.read(4), byteorder='little', signed=True)
        nrows = int.from_bytes(f.read(4), byteorder='little', signed=True)
        n = int.from_bytes(f.read(4), byteorder='little', signed=True)

        data = np.zeros((nrows, n), dtype=np.float64)

        # Create a datetime array
        times = []

        # Read the data
        for i in range(nrows):
            day   = int.from_bytes(f.read(1), byteorder='little', signed=True)
            month = int.from_bytes(f.read(1), byteorder='little', signed=True)
            year  = int.from_bytes(f.read(2), byteorder='little', signed=True)
            hour  = int.from_bytes(f.read(1), byteorder='little', signed=True)
            minute= int.from_bytes(f.read(1), byteorder='little', signed=True)
            second= int.from_bytes(f.read(1), byteorder='little', signed=True)

            times.append(dt(year, month, day, hour, minute, second, tzinfo=tz.utc))

            # Read n floats
            values = f.read(n * 8)
            if len(values) != n * 8:
                raise ValueError(_("The number of values read does not match the expected number."))
            values = struct.unpack('<d' * n, values)
            data[i, :] = values
        f.close()

        # Convert to a 1D numpy array
        data = data.flatten()

        return name_serie, data, times


    def __getitem__(self, item) -> tuple[list[dt], np.ndarray, vector]:
        """
        Get the data for a given item.
        The item should be the name of the zone or the id of the zone.
        """
        if isinstance(item, str) or isinstance(item, int):
            try:
                return self._times, self._data[str(item)], self._grid[item].myvectors[0]
            except KeyError:
                logging.error(_("The item {} is not in the data.").format(item))
                return None, None, None
        else:
            raise ValueError(_("The item must be a string or an integer."))

    def get_rain4index(self, index:int) -> dict[str | int, float]:
        """
        Get the rain data for a given index.
        The index should be an integer representing the time step position.

        :param index: The index time for which to get the rain data (0-based).
        :return: A dictionary with the zone name as key and the rain value as value.
        """
        if not isinstance(index, int):
            raise ValueError(_("The index must be an integer."))

        if index < 0 or index >= len(self._times):
            raise ValueError(_("Index out of range."))

        rains = {}
        for zone_name, rain_values in self._data.items():
            rains[zone_name] = rain_values[index]

        return rains

    def plot_spatial_rain4index(self, index:int, figax=None, title:str = None, cmap:str = 'viridis'):
        """ Plot the spatial distribution of rain for a given index. """

        if not isinstance(index, int):
            raise ValueError(_("The index must be an integer."))

        if index < 0 or index >= len(self._times):
            raise ValueError(_("The index is out of range."))

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        # Plot the data
        self._grid.add_values('rain', self.get_rain4index(index))

        self._grid.set_colors_from_value('rain', cmap=cmap)
        self._grid.set_filled(True)
        self._grid.plot_matplotlib(ax)

        self._grid.set_filled(False)
        self._grid.plot_matplotlib(ax)

        if title is None:
            date = self._times[index]
            title = _("Spatial distribution of rain at {}").format(date.strftime('%Y-%m-%d %H:%M:%S'))

        ax.set_title(title)

        return fig, ax

    def animation_spatial_rain_index(self, figax=None, idx_start:int = 0, idx_end:int = -1, cmap:str = 'viridis', interval:int = 100):
        """
        Create an animation of the spatial distribution of rain over time.
        The animation will show the rain data for each time step.

        :param figax: A tuple (fig, ax) to use for the animation. If None, a new figure and axes will be created.
        :param idx_start: The starting index for the animation (0-based).
        :param idx_end: The ending index for the animation (0-based). If -1, it will use the last index.
        :param cmap: The colormap to use for the rain data.
        :param interval: The interval between frames in milliseconds.
        :return: The animation object.
        """
        import matplotlib.animation as animation

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        def update(frame):
            ax.clear()
            self.plot_spatial_rain4index(frame, figax=(fig, ax), title=None, cmap=cmap)

        if idx_end == -1:
            idx_end = len(self._times)

        ani = animation.FuncAnimation(fig, update, frames=range(idx_start, idx_end), interval=interval)

        return ani

    def animation_spatial_rain_date(self, figax=None, date_start:dt = 0, date_end:int = -1, cmap:str = 'viridis', interval:int = 100):
        """
        Create an animation of the spatial distribution of rain over time.
        The animation will show the rain data for each time step.

        :param figax: A tuple (fig, ax) to use for the animation. If None, a new figure and axes will be created.
        :param idx_start: The starting index for the animation (0-based).
        :param idx_end: The ending index for the animation (0-based). If -1, it will use the last index.
        :param cmap: The colormap to use for the rain data.
        :param interval: The interval between frames in milliseconds.
        :return: The animation object.
        """
        import matplotlib.animation as animation

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        def update(frame):
            ax.clear()
            self.plot_spatial_rain4index(frame, figax=(fig, ax), title=None, cmap=cmap)

        if date_start == 0:
            date_start = self._times[0]
        if date_end == -1:
            date_end = self._times[-1]

        # Convert dates to indices
        idx_start = self._times.index(date_start)
        idx_end = self._times.index(date_end) + 1  # +1 to include the end date
        if idx_end > len(self._times):
            idx_end = len(self._times)

        ani = animation.FuncAnimation(fig, update, frames=range(idx_start, idx_end), interval=interval)

        return ani

class Rainfall_Polygons:
    """

    For source_point_measurements:

        « ind_unique.txt » : contient une matrice avec autant de lignes qu'il y a
        de configurations et autant de colonne qu'il y a de stations.
        Les lignes représentent le numéro de la configuration et les colonnes
        représentent les stations. La variable stockée dans cette matrice est
        l'indice dans la liste de pluies mesurées à une station auquel commencer
        pour cette configuration.

        « nb_ind_unique.txt » : vecteur contenant le nombre de pas de temps à considérer
        pour chaque configuration.

        « unique.txt » : représente le code de la configuration.
        La valeur stockée est la conversion en entier sur 8 bytes du code binaire
        dont le premier élément est la première station et sa valeur est égale à 1
        si celle-ci est utilisée dans la configuration présente.
        Cette définition a pour effet de limiter le nombre de stations exploitable à 64
        éléments par bassin versant étudié. Dans l'attribution des pluies aux mailles,
        toutes les configurations sont parcourues dans l'ordre des lignes de la matrice
        contenue dans le fichier « ind_unique.txt » pour construire progressivement
        les pluies de bassin.

    For source_IRM:
        Une seule configuration spatiale est présente. Pas de fichiers
        « ind_unique.txt » et « nb_ind_unique.txt ».
    """

    def __init__(self, workingDir: str | Path, type_of_rain:int):

        self.workingDir = Path(workingDir)

        self.type_of_rain = type_of_rain

        self.hyetoDict = {}
        self.configs = {}

        self._codes:dict[int, int]  = {}        # key if the Fortran index (1-based) and value is the code
        self._nbsteps4code:dict[int,int] = {}   # dict (code, number of steps)
        self._steps4eachcode = np.array([])     # 2D array with the steps for each code (1-based)
        self._geometries:dict[int, dict[str:Zones]] = {}  # key is the code and value is a dict with 'all_polygons' and 'used_polygons'
        self._hyetograms: dict[str, dict[str, np.ndarray]]= {} # key is the zone name and value is a dict with 'time' and 'rain'

        if not self.type_of_rain  in [source_point_measurements, source_IRM, source_dist]:
            logging.error(_("The type of rain is not supported. It should be either source_point_measurements, source_IRM or source_dist."))
            return

        # Must be treated in this order
        self._read_hyetograms()
        self._read_configurations()
        self._read_geometries()

        self._checks()

    def _checks(self):
        """
        Perform checks on the data.
        """

        lenghts = [len(self.get_computed_steps4code(code)) for code in self._codes.values()]

        assert np.all(lenghts == list(self._nbsteps4code.values())), \
            _("The number of steps for each code does not match the number of steps in the file.")

        # check if all the hyetograms start at the same time
        if len(self._hyetograms) > 0:
            first_time = next(iter(self._hyetograms.values()))['time'][0]
            for hyeto in self._hyetograms.values():
                if hyeto['time'][0] != first_time:
                    raise ValueError(_("The hyetograms do not start at the same time."))


    def get_computed_steps4code(self, code:int, base:int = 0) -> list[int]:
        """
        Get all computed time steps for a given code.

        ATTENTION : it will return index positions. By default, the base is 0 (Python base).

        :param code: The code for which to get the steps.
        :param base: The base to use for the steps (default is 0 == Python, 1 == Fortran).
        """

        codes = list(self._codes.values())
        if code in codes:
            col = codes.index(code)
        else:
            raise ValueError(_("The code {} is not valid.").format(code))

        if col < 0:
            raise ValueError(_("The code {} is not valid.").format(code))

        if col >= len(codes):
            raise ValueError(_("The code {} is not valid.").format(code))

        if self._steps4eachcode.size == 0:
            raise ValueError(_("No steps found for the given code."))

        steps = self._steps4eachcode[:, col]
        # remove the 0
        steps = steps[steps > 0]
        if steps.size == 0:
            raise ValueError(_("No steps found for the given code."))

        if base == 0:
            # Python base (0-based)
            steps = steps - 1
        elif base == 1:
            # Fortran base (1-based)
            steps = steps

        # convert to list
        return steps.tolist()

    def get_config4date(self, date:dt) -> int:
        """
        Get the configuration for a given date.
        The date should be in the format 'datetime.datetime'.

        :param date: The date for which to get the configuration.
        """
        if not isinstance(date, dt):
            raise ValueError(_("The date must be a datetime object."))

        # convert to UTC timestamp
        date = date.replace(tzinfo=tz.utc)  # remove timezone info if present
        timsetamp = int(date.timestamp())

        return self.get_config4timestamp(timsetamp)

    def get_config4timestamp(self, timestamp:int) -> int:
        """
        Get the configuration for a given timestamp.
        The timestamp should be an integer representing the seconds since epoch.

        :param timestamp: The timestamp for which to get the configuration.
        """
        if not isinstance(timestamp, int):
            raise ValueError(_("The timestamp must be an integer."))

        if timestamp < self.timestamps[0] or timestamp > self.timestamps[-1]:
            raise ValueError(_("Timestamp out of range."))

        try:
            idx = self.timestamps.index(timestamp)
            return self.get_config4index(idx)
        except ValueError:
            logging.error(_("Timestamp {} not found in the configurations.").format(timestamp))
            return None

    def get_config4index(self, index:int) -> int:
        """
        Get the configuration for a given index time.
        The index should be an integer representing the position in time (0-based).

        :param index: The index for which to get the configuration (0-based).
        :return: The configuration key for the given index (not the code itself).
        """
        if not isinstance(index, int):
            raise ValueError(_("The index must be an integer."))

        if index < 0 or index >= len(self._config4eachstep):
            raise ValueError(_("Index out of range."))

        return self._config4eachstep[index][1]

    def get_code4index(self, index:int) -> int:
        """
        Get the code for a given index time.
        The index should be an integer representing the position in time (0-based).

        :param index: The index for which to get the code (0-based).
        :return: The configuration code for the given index.
        """
        config = self.get_config4index(index)
        return self._codes[config]

    def get_code4date(self, date:dt) -> int:
        """
        Get the code for a given date.
        The date should be in the format 'datetime.datetime'.

        :param date: The date for which to get the code.
        :return: The configuration code for the given date.
        """
        config = self.get_config4date(date)
        return self._codes[config]

    def get_code4timestamp(self, timestamp:int) -> int:
        """
        Get the code for a given timestamp.
        The timestamp should be an integer representing the seconds since epoch.

        :param timestamp: The timestamp for which to get the code.
        :return: The configuration code for the given timestamp.
        """
        config = self.get_config4timestamp(timestamp)
        return self._codes[config]

    def get_geometry4index(self, index:int, all_polygons:bool = True) -> Zones:
        """
        Get the geometry for a given index.
        The index should be an integer representing the time step position.

        :param index: The index time for which to get the geometry (0-based).
        :param all_polygons: If True, return all polygons, otherwise return only the used polygons.
        :return: The geometry for the given index.
        """

        code = self.get_code4index(index)

        if all_polygons:
            return self._geometries[code]['all_polygons']
        else:
            return self._geometries[code]['used_polygons']

    def get_geometry4code(self, code:int, all_polygons:bool = True) -> Zones:
        """
        Get the geometry for a given configuration code.
        The code should be an integer representing the configuration.

        :param code: The configuration code for which to get the geometry.
        :param all_polygons: If True, return all polygons, otherwise return only the used polygons.
        """
        if not isinstance(code, int):
            raise ValueError(_("The code must be an integer."))
        if code not in self._codes.values():
            raise ValueError(_("The code {} is not valid.").format(code))

        if code in self._geometries:
            if all_polygons:
                return self._geometries[code]['all_polygons']
            else:
                return self._geometries[code]['used_polygons']
        else:
            logging.error(_("Geometry for code {} not found.").format(code))
            return None

    def get_geometry4codeindex(self, code_index:int, all_polygons:bool = True) -> Zones:
        """
        Get the geometry for a given configuration code.
        The code should be an integer representing the configuration.

        :param code_index: The index of the code in the list of codes (1-based index).
        :param all_polygons: If True, return all polygons, otherwise return only the used polygons.
        """
        if not isinstance(code_index, int):
            raise ValueError(_("The code must be an integer."))
        if code_index < 1 or code_index > len(self._codes):
            raise ValueError(_("The code index {} is out of range (1-based).").format(code_index))

        code = self._codes[code_index]
        return self.get_geometry4code(code, all_polygons=all_polygons)

    @property
    def nb_steps4code(self) -> list[tuple[int, int]]:
        """
        Get the number of steps for each code.
        Returns a list of tuples (code, number of steps).
        """
        return [(code, self._nbsteps4code[code]) for code in self._codes.values()]

    @property
    def nb_steps4code_asdict(self) -> dict[int, int]:
        """
        Get the number of steps for each code as a dictionary.
        Returns a dictionary with the code as key and the number of steps as value.
        """
        return self._nbsteps4code

    def get_geometries(self, n_more_frequent:int = 5, all_poygons:bool = False) -> dict[int, Zones]:
        """
        Get the geometries for the most frequent configurations.
        The n_more_frequent parameter defines how many configurations to return.

        :param n_more_frequent: The number of most frequent configurations to return.
        :param all_poygons: If True, return all polygons, otherwise return only the used polygons.
        :return: A dictionary with the configuration code as key and the Zones object as value.
        """

        if not isinstance(n_more_frequent, int) or n_more_frequent <= 0:
            raise ValueError(_("The n_more_frequent parameter must be a positive integer."))

        if n_more_frequent > len(self._codes):
            logging.warning(_("The n_more_frequent parameter is greater than the number of configurations. Returning all configurations."))
        n_more_frequent = min(n_more_frequent, len(self._codes))

        sorted_codes = sorted(self.nb_steps4code, key = lambda x: x[1], reverse=True)

        return {code[0] : self.get_geometry4code(code[0], all_polygons=all_poygons) for code in sorted_codes[:n_more_frequent]}

    def get_most_frequent_code(self, n_more_frequent:int = 5) -> list[int]:
        """
        Get the most frequent configurations codes.
        The n_more_frequent parameter defines how many configurations to return.

        :param n_more_frequent: The number of most frequent configurations to return.
        :return: A list of the most frequent configuration codes.
        """

        if not isinstance(n_more_frequent, int) or n_more_frequent <= 0:
            raise ValueError(_("The n_more_frequent parameter must be a positive integer."))

        if n_more_frequent > len(self._codes):
            logging.warning(_("The n_more_frequent parameter is greater than the number of configurations. Returning all configurations."))
        n_more_frequent = min(n_more_frequent, len(self._codes))

        sorted_codes = sorted(self.nb_steps4code, key = lambda x: x[1], reverse=True)

        return [code[0] for code in sorted_codes[:n_more_frequent]]

    def get_sorted_codes(self) -> list[int]:
        """
        Get the sorted configuration codes based on the number of steps.
        Returns a list of configuration codes sorted by the number of steps in descending order.

        :return: A list of configuration codes sorted by the number of steps.
        """
        return [code for code in sorted(self.nb_steps4code, key=lambda x: x[1], reverse=True)]

    def get_hyetograms4index(self, index:int) -> list:
        """
        Get the hyetograms for a given index time.
        The index should be an integer representing the time step position.

        :param index: The index time for which to get the hyetograms (0-based).
        :return: A list of hyetograms for the given index.
        """

        config = self.get_config4index(index)
        code = self._codes[config]
        keys = self.get_geometry4index(index, all_polygons=False).zone_names

        if len(keys) > 0:
            return [self._hyetograms[int(key)] for key in keys]
        else:
            logging.error(_("Hyetogram for code {} not found.").format(code))
            return None

    def get_rains4index(self, index:int) -> np.ndarray:
        """
        Get the rain data for a given index time.
        The index should be an integer representing the time step position.

        :param index: The index time for which to get the rain data (0-based).
        :return: A numpy array with the rain data for the given index.
        """
        if not isinstance(index, int):
            raise ValueError(_("The index must be an integer."))

        hyetos = self.get_hyetograms4index(index)
        if hyetos is None:
            raise ValueError(_("No hyetograms found for the given index."))

        # Search the value at the good time step
        ts = float(self.get_timestamp_from_index(index) - self.timestamps[0])
        rains = []
        hyeto = hyetos[0]

        idx = -1
        if ts in hyeto['time']:
            idx = np.where(hyeto['time'] == ts)[0][0]
            # It is tha same index for all hyetos because they are aligned
        else:
            raise ValueError(_("The time step {} is not found in the hyetogram.").format(ts))

        rains = [hyeto['rain'][idx] for hyeto in hyetos]

        if len(rains) == 0:
            raise ValueError(_("No rain data found for the given index."))

        # Convert to numpy array
        rains = np.array(rains, dtype=np.float64)

        return rains

    def get_rains4timestamp(self, timestamp:int) -> np.ndarray:
        """
        Get the rain data for a given timestamp.
        The timestamp should be an integer representing the seconds since epoch.

        :param timestamp: The timestamp for which to get the rain data.
        :return: A numpy array with the rain data for the given timestamp.
        """
        if not isinstance(timestamp, int):
            raise ValueError(_("The timestamp must be an integer."))

        index = self.timestamps.index(timestamp)
        return self.get_rains4index(index)

    def get_rains4date(self, date:dt) -> np.ndarray:
        """
        Get the rain data for a given date.
        The date should be in the format 'datetime.datetime'.

        :param date: The date for which to get the rain data.
        :return: A numpy array with the rain data for the given date.
        """
        if not isinstance(date, dt):
            raise ValueError(_("The date must be a datetime object."))

        timestamp = int(date.timestamp())
        return self.get_rains4timestamp(timestamp)

    def get_rains4code(self, code:int) -> np.ndarray:
        """
        Get the rain data for given configuration.

        :param code: The configuration code for which to get the rain data.
        :return: A numpy array with the rain data for the given code.
        """

        if not isinstance(code, int):
            raise ValueError(_("The code must be an integer."))

        if code not in self._codes.values():
            raise ValueError(_("The code {} is not valid.").format(code))

        steps = self.get_computed_steps4code(code)

        hyetos = self.get_hyetograms4index(steps[0])
        if hyetos is None:
            raise ValueError(_("No hyetograms found for the given index."))

        rains = [x['rain'] for x in hyetos]
        if len(rains) == 0:
            raise ValueError(_("No rain data found for the given code."))

        # Select only the steps
        rains = np.asarray([[rain[i] for i in steps] for rain in rains], dtype=np.float64)

        assert rains.shape[1] == len(steps), \
            _("The number of rain values does not match the number of steps for the given code.")
        assert rains.shape[0] == len(hyetos), \
            _("The number of rain values does not match the number of hyetograms for the given code.")
        return rains, steps

    def get_footprint_and_rain4index(self, index:int) -> tuple:
        """
        Get the footprint and rain data for a given index.
        The index should be an integer representing the time step position.

        :param index: The index time for which to get the footprint and rain data (0-based).
        :return: A tuple containing the footprints (as vector objects) and the rain data (as numpy array).
        """
        if not isinstance(index, int):
            raise ValueError(_("The index must be an integer."))

        rains = self.get_rains4time(index)
        footprints = self.get_geometry4index(index, all_polygons=False)
        footprints = [x.myvectors[0] for x in footprints.myzones]

        assert len(footprints) == len(rains), \
            _("The number of footprints does not match the number of rain values.")

        return footprints, rains

    def get_footprint_and_rain4code(self, code:int) -> tuple:
        """
        Get the footprint and rain data for a given configuration code.
        The code should be an integer representing the configuration.

        :param code: The configuration code for which to get the footprint and rain data.
        :return: A tuple containing the footprints (as vector objects), the rain data (as numpy array) and the times.
        """

        if not isinstance(code, int):
            raise ValueError(_("The code must be an integer."))
        if code not in self._codes.values():
            raise ValueError(_("The code {} is not valid.").format(code))

        rains, steps = self.get_rains4code(code)
        footprints = self.get_geometry4index(steps[0], all_polygons=False)
        footprints = [x.myvectors[0] for x in footprints.myzones]

        assert len(footprints) == len(rains), \
            _("The number of footprints does not match the number of rain values.")

        return footprints, rains, [self.times[i] for i in steps]

    def get_most_rainy_code(self, n_most:int = 5) -> int:
        """
        Get the configuration code with the most frequently rain.

        We identify the number of consecutive steps with rain values greater than zero.
        """
        from scipy.ndimage import label

        nb_events = {}
        for code in self._codes.values():
            rains, steps = self.get_rains4code(code)
            # mean the rain values accross all stations
            rains = np.mean(rains, axis=0)

            lab, num = label(rains)
            nb_events[code] = num

        # sort the codes by the number of events
        sorted_codes = sorted(nb_events.items(), key=lambda x: x[1], reverse=True)
        if n_most > len(sorted_codes):
            logging.warning(_("The n_most parameter is greater than the number of configurations. Returning all configurations."))
            n_most = len(sorted_codes)

        if n_most == -1:
            n_most = len(sorted_codes)

        # return the code with the most events
        return {sorted_codes[i][0]: sorted_codes[i][1] for i in range(n_most)}

    def get_most_relative_rainy_code(self, n_most:int = 5) -> int:
        """
        Get the configuration code with the most frequently rain.

        We identify the number of consecutive steps with rain values greater than zero.
        """
        from scipy.ndimage import label

        nb_events = {}
        for code in self._codes.values():
            rains, steps = self.get_rains4code(code)
            # mean the rain values accross all stations
            rains = np.mean(rains, axis=0)

            lab, num = label(rains)
            nb_events[code] = float(num) / float(len(rains))  # relative number of events

        # sort the codes by the number of events
        sorted_codes = sorted(nb_events.items(), key=lambda x: x[1], reverse=True)

        if n_most > len(sorted_codes):
            logging.warning(_("The n_most parameter is greater than the number of configurations. Returning all configurations."))
            n_most = len(sorted_codes)

        if n_most == -1:
            n_most = len(sorted_codes)

        # return the code with the most events
        return {sorted_codes[i][0]: sorted_codes[i][1] for i in range(n_most)}

    @cached_property
    def rain_maximum(self) -> float:
        """
        Returns the maximum rain value across all configurations.
        """
        if not self._hyetograms:
            return 0.0

        max_rain = 0.0
        for hyeto in self._hyetograms.values():
            max_rain = max(max_rain, np.max(hyeto['rain']))
        return max_rain

    @cached_property
    def rain_maxima(self) -> dict[int, float]:
        """
        Returns a dictionary with the maximum rain value for each configuration code.
        The key is the configuration code and the value is the maximum rain value.
        """
        maxima = {}
        for code in self._codes.values():
            rains, __steps = self.get_rains4code(code)
            maxima[code] = np.max(rains)
        return maxima

    @cached_property
    def timestamps(self):
        """
        Returns the timestamps list
        """
        return [x[0] for x in self._config4eachstep]

    def get_timestamp_from_index(self, index:int) -> int:
        """
        Get the timestamp for a given index.
        The index should be an integer representing the time step position.

        :param index: The index time for which to get the timestamp (0-based).
        """
        if not isinstance(index, int):
            raise ValueError(_("The index must be an integer."))

        if index < 0 or index >= len(self._config4eachstep):
            raise ValueError(_("Index out of range."))

        return self._config4eachstep[index][0]

    @property
    def times(self):
        """
        Returns the time list for the first configuration.
        """
        locdate = [dt.fromtimestamp(x[0]).replace(tzinfo=tz.utc) for x in self._config4eachstep]
        return locdate

    @times.setter
    def times(self, value:list[dt]):
        """
        Set the time array.
        The value should be a list of datetime objects.
        """
        if not isinstance(value, list) or not all(isinstance(x, dt) for x in value):
            raise ValueError(_("The value must be a list of datetime objects."))

        self._config4eachstep = [(int(x.timestamp()), 0) for x in value]

    @cached_property
    def time_begin(self):
        """
        Returns the beginning time of the first configuration.
        """
        if len(self._config4eachstep) > 0:
            return dt.fromtimestamp(self._config4eachstep[0][0]).replace(tzinfo=tz.utc)
        else:
            return None

    @cached_property
    def time_end(self):
        """
        Returns the end time of the last configuration.
        """
        if len(self._config4eachstep) > 0:
            return dt.fromtimestamp(self._config4eachstep[-1][0]).replace(tzinfo=tz.utc)
        else:
            return None

    @property
    def number_of_configurations(self):
        """
        Returns the number of unique configurations.
        """
        return len(self._codes)

    @property
    def nb_records(self):
        """
        Returns the number of records (scenarios).
        """
        return self._steps4eachcode.shape[0]

    def _decode_config(self, value:int) -> list:
        """
        Decode the unique configuration from an integer value.
        The value is a binary representation where each bit represents
        whether a station is included in the configuration.
        """
        # convert to int64
        value = np.int64(value)
        # create a list of 0 or 1 for each bit in the binary representation
        config = [(value >> i) & 1 for i in range(64)]
        return config

    def _code_config(self, config:list) -> int:
        """
        Encode a unique configuration from a list of 0s and 1s into an integer.
        The list represents whether each station is included in the configuration.
        """
        # convert the list to a numpy array of int64
        config = np.array(config, dtype=np.int64)
        # calculate the integer value by summing the powers of 2 for each bit
        value = np.sum(config * (2 ** np.arange(len(config))))
        return value

    def _read_geometries(self):
        """
        Read the geometries from the directory.
        The geometries are stored in vector files named as:
        Rain_basin_geom_<code>.vec and Rain_basin_geom_<code>_all_zones.vec
        where <code> is the configuration code.
        """

        dir = self.workingDir / "Whole_basin"

        if self.type_of_rain == source_point_measurements:
            for cur_id in self._codes.values():
                self._geometries[cur_id] = {}
                fileName = dir / f"Rain_basin_geom_{cur_id}.vec"
                if fileName.exists():
                    self._geometries[cur_id]['used_polygons'] = Zones(fileName)
                else:
                    logging.error(_("The file {} does not exist.").format(fileName))

                fileName = dir / f"Rain_basin_geom_{cur_id}_all_zones.vec"
                if fileName.exists():
                    self._geometries[cur_id]['all_polygons'] = Zones(fileName)
                else:
                    logging.error(_("The file {} does not exist.").format(fileName))
        elif self.type_of_rain in [source_IRM, source_dist]:
            fileName = dir / 'Rain_basin_geom.vec'
            if fileName.exists():
                self._geometries[1] = {}
                self._geometries[1]['used_polygons'] = Zones(fileName)
            else:
                logging.error(_("The file {} does not exist.").format(fileName))

            self._geometries[1]['all_polygons'] = None

    def _read_configurations(self):
        """
        Read the unique configurations from a text file.

        The configurations are stored in the following files:
        - unique.txt: contains the unique configurations as integer codes.
        - nb_ind_unique.txt: contains the number of steps for each configuration.
        - ind_unique.txt: contains the steps for each configuration.
        - input_data_gap.txt: contains the gap between the first and the second configuration.
        - scenarios.txt: contains the scenarios (time, configuration).
        The files should be located in the "Whole_basin" directory.
        The working directory should be set to the directory containing the "Whole_basin" directory.
        """

        if self.type_of_rain == source_point_measurements:

            files = ['unique.txt', 'nb_ind_unique.txt', 'ind_unique.txt']
            dir = self.workingDir / "Whole_basin"

            for file in files:
                fileName = dir / file
                if not fileName.exists():
                    logging.error(_("The file {} does not exist.").format(fileName))
                    return None

            fileName = dir / files[0]
            with open(fileName, 'r') as f:
                self._codes = {i+1: int(x.strip()) for i,x in enumerate(f.read().splitlines()[1:])}

            fileName = dir / files[1]
            with open(fileName, 'r') as f:
                self._nbsteps4code = {self._codes[i+1]: int(x.strip()) for i,x in enumerate(f.read().splitlines()[1:])}

            fileName = dir / files[2]
            with open(fileName, 'r') as f:
                content = f.read().split()

            unique = int(content[0].strip())
            assert unique == len(self._codes), "The number of unique configurations does not match the number of unique indices."
            nb_records = int(content[1].strip())

            self._steps4eachcode = np.zeros((nb_records, unique), dtype=int)
            for i in range(nb_records):
                self._steps4eachcode[i,:] = [int(x.strip()) for x in content[2+i*unique:2+(i+1)*unique]]

            fileName = dir / 'input_data_gap.txt'
            if fileName.exists():
                assert self._codes[1] == 0, "The first unique configuration should be 0."
                logging.info(_('The first unique configuration is 0.'))
                with open(fileName, 'r') as f:
                    content = f.read().splitlines()
                nb = int(content[0].strip())
                self._gap = [int(x.strip()) for x in content[1:]]

            fileName = dir / 'scenarios.txt'
            if fileName.exists():
                with open(fileName, 'r') as f:
                    content = f.read().splitlines()
                nb_records = int(content[0].strip())

                assert nb_records == self.nb_records, "The number of scenarios does not match the number of records."
                self._config4eachstep = [line.split() for line in content[1:]]
                # convert scenarios to integer
                self._config4eachstep = [[int(x) for x in scenario] for scenario in self._config4eachstep]

        elif self.type_of_rain in [source_IRM, source_dist]:

            dir = self.workingDir / "Whole_basin"
            self._codes = {1: 1}
            self._gap = None
            times = self._hyetograms[list(self._hyetograms.keys())[0]]['time']
            self._nbsteps4code = {1: len(times)}
            tstamp = [int(self._timestamp_start + t) for t in times]
            self._config4eachstep = [[t, 1] for t in tstamp]
            self._steps4eachcode = np.zeros((len(times), 1), dtype=int)
            for i in range(len(times)):
                self._steps4eachcode[i, 0] = i + 1

    def _read_hyetograms(self):
        """
        Read the hyetograms from the directory.

        The hyetograms are stored in files named as:
        rain<code>.hyeto where <code> is the configuration code.
        The files should be located in the "Whole_basin" directory.
        The working directory should be set to the directory containing the "Whole_basin" directory.
        """

        dir = self.workingDir / "Whole_basin"

        for file in dir.rglob("*rain.hyeto"):
            code = int(file.stem.replace('rain',''))
            with open(file, 'r') as f:
                content = f.read().splitlines()
            time = np.asarray([float(x.split()[0]) for x in content[1:]])
            self._timestamp_start = int(time[0])
            time -= time[0]  # normalize time to start from 0
            rain = np.asarray([float(x.split()[1]) for x in content[1:]])
            self._hyetograms[code] = {'time': time, 'rain': rain}

    def _write_rain_binary(self, name_serie:int, filename: str | Path, data: np.ndarray, times: list[dt] = None):
        """
        Write data to a binary file.
        The filename should end with .dat.

        Structure of the binary file:
        - 4 bytes for a "name" as integer
        - 4 bytes for the number of data columns (n)
        - 4 bytes for the total number of columns (n + 6)
        - 4 bytes for the number of rows
        - For each row:
            - 1 byte for the day
            - 1 byte for the month
            - 2 bytes for the year
            - 1 byte for the hour
            - 1 byte for the minute
            - 1 byte for the second
            - n*8 bytes for the rain value as float

        :param filename: The name of the file to write.
        :param data: The data to write, should be a 1D numpy array.
        """
        import struct

        try:
            name_serie = int(name_serie)
        except ValueError:
            raise ValueError(_("The name of the series must be an integer or could be convert to int."))

        filename = Path(filename)

        assert filename.suffix == '.dat', _("The file name must end with .dat")

        data = data.flatten()  # Ensure data is a 1D array

        assert data.ndim == 1, _("The data must be a 1D numpy array.")

        if times is None:
            times = self.times
        else:
            assert isinstance(times, list) and all(isinstance(t, dt) for t in times), _("The times must be a list of datetime objects.")
            # Check if the all the dates are in UTC
            for t in times:
                if t.tzinfo is None or t.tzinfo.utcoffset(t) is None:
                    raise ValueError(_("All times must be timezone-aware datetime objects in UTC."))
        assert len(times) == data.size, _("The number of time steps does not match the number of data points.")

        f = open(filename,'wb')

        # Write the header
        nameb = name_serie.to_bytes(4, byteorder='little', signed=True)
        n = 1 # Number of data columns (1 for rain)
        ncols = n + 6  # 6 additional columns for date and time
        nrows = len(times)
        ncolsb = ncols.to_bytes(4, byteorder='little', signed=True)
        nrowsb = nrows.to_bytes(4, byteorder='little', signed=True)
        f.write(nameb)
        f.write(ncolsb)
        f.write(nrowsb)
        f.write(n.to_bytes(4, byteorder='little', signed=True))

        # Write the data
        for t, r in zip(times, data):

            dayb   = t.day.to_bytes(1, byteorder='little', signed=True)
            monthb = t.month.to_bytes(1, byteorder='little', signed=True)
            yearb  = t.year.to_bytes(2, byteorder='little', signed=True)
            hourb  = t.hour.to_bytes(1, byteorder='little', signed=True)
            minuteb= t.minute.to_bytes(1, byteorder='little', signed=True)
            secondb= t.second.to_bytes(1, byteorder='little', signed=True)
            valb   = bytearray(struct.pack("<d", float(r)))

            f.write(dayb)
            f.write(monthb)
            f.write(yearb)
            f.write(hourb)
            f.write(minuteb)
            f.write(secondb)
            f.write(valb)

    def _read_rain_binary(self, filename: str | Path) -> tuple[int, np.ndarray, list[dt]]:
        """
        Read data from a binary file.
        The filename should end with .dat.

        Structure of the binary file:
        - 4 bytes for a "name" as integer
        - 4 bytes for the number of data columns (n)
        - 4 bytes for the total number of columns (n + 6)
        - 4 bytes for the number of rows
        - For each row:
            - 1 byte for the day
            - 1 byte for the month
            - 2 bytes for the year
            - 1 byte for the hour
            - 1 byte for the minute
            - 1 byte for the second
            - n*8 bytes for the rain value as float

        :param filename: The name of the file to read.
        :return: A numpy array with the rain data.
        """
        import struct

        filename = Path(filename)

        assert filename.suffix == '.dat', _("The file name must end with .dat")

        f = open(filename, 'rb')

        # Read the header
        name_serie = int.from_bytes(f.read(4), byteorder='little', signed=True)
        ncols = int.from_bytes(f.read(4), byteorder='little', signed=True)
        nrows = int.from_bytes(f.read(4), byteorder='little', signed=True)
        n = int.from_bytes(f.read(4), byteorder='little', signed=True)

        data = np.zeros((nrows, n), dtype=np.float64)

        # Create a datetime array
        times = []

        # Read the data
        for i in range(nrows):
            day   = int.from_bytes(f.read(1), byteorder='little', signed=True)
            month = int.from_bytes(f.read(1), byteorder='little', signed=True)
            year  = int.from_bytes(f.read(2), byteorder='little', signed=True)
            hour  = int.from_bytes(f.read(1), byteorder='little', signed=True)
            minute= int.from_bytes(f.read(1), byteorder='little', signed=True)
            second= int.from_bytes(f.read(1), byteorder='little', signed=True)

            times.append(dt(year, month, day, hour, minute, second, tzinfo=tz.utc))

            # Read n floats
            values = f.read(n * 8)
            if len(values) != n * 8:
                raise ValueError(_("The number of values read does not match the expected number."))
            values = struct.unpack('<d' * n, values)
            data[i, :] = values
        f.close()

        # Convert to a 1D numpy array
        data = data.flatten()

        return name_serie, data, times


    def _write_rain_ascii(self, name_serie:str | int, filename: str | Path, data: np.ndarray, times: list[dt] = None):
        """
        Write data to an ASCII file.
        The filename should end with .rain.

        Structure of the ASCII file:
        - 4 Header lines with :
            - The first line is a name of the series.
            - The second line is the number of data columns (n).
            - The third line is the total number of columns (n + 6).
            - The fourth line is the number of rows.
        - Each line represents a time step.
            - The first six columns are the day, month, year, hour, minute, and second.
            - The last column is the rain value.

        :param name_serie: The name of the series, can be an integer or a string.
        :param filename: The name of the file to write.
        :param data: The data to write, should be a 1D numpy array.
        """

        name_serie = str(name_serie)
        filename = Path(filename)

        assert filename.suffix == '.rain', _("The file name must end with .rain")

        data = data.flatten()  # Ensure data is a 1D array

        assert data.ndim == 1, _("The data must be a 1D numpy array.")

        if times is None:
            times = self.times
        else:
            assert isinstance(times, list) and all(isinstance(t, dt) for t in times), _("The times must be a list of datetime objects.")
            # Check if the all the dates are in UTC
            for t in times:
                if t.tzinfo is None or t.tzinfo.utcoffset(t) is None:
                    raise ValueError(_("All times must be timezone-aware datetime objects in UTC."))
        assert len(times) == data.size, _("The number of time steps does not match the number of data points.")

        with open(filename, 'w') as f:
            # Write the header
            f.write(f"{name_serie}\n")
            f.write(f"{1}\n")
            f.write(f"{1 + 6}\n")
            f.write(f"{len(times)}\n")

            # Write the data
            for t, r in zip(times, data):
                f.write("\t".join([str(t.day), str(t.month), str(t.year), str(t.hour), str(t.minute), str(t.second), str(r)]) + "\n")

    def _read_rain_ascii(self, filename: str | Path) -> tuple[str | int, np.ndarray, list[dt]]:
        """
        Read data from an ASCII file.
        The filename should end with .rain.

        Structure of the ASCII file:
        - 4 Header lines with :
            - The first line is a name of the series.
            - The second line is the number of data columns (n).
            - The third line is the total number of columns (n + 6).
            - The fourth line is the number of rows.
        - Each line represents a time step.
            - The first six columns are the day, month, year, hour, minute, and second.
            - The last column is the rain value.

        :param filename: The name of the file to read.

        """

        filename = Path(filename)

        assert filename.suffix == '.rain', _("The file name must end with .rain")

        with open(filename, 'r') as f:
            lines = f.readlines()

        # Read the header
        name_serie = lines[0].strip()
        ncols = int(lines[1].strip())
        nrows = int(lines[3].strip())

        data = np.zeros((nrows, ncols), dtype=np.float64)
        times = []

        # Read the data
        for i in range(nrows):
            line = lines[i + 4].strip().split('\t')
            day, month, year, hour, minute, second, rain = line
            times.append(dt(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=tz.utc))
            data[i, 0] = float(rain)

        # Convert to a 1D numpy array
        data = data.flatten()

        return name_serie, data, times

    def convert2grid(self, grid: Path | str | Zones,
                     output: Path | str = None,
                     overwrite: bool = True,
                     parallel: bool = True):
        """
        Convert the data to a grid.

        The grid can be a Path or a Zones object.
        If a Path is provided, it should point to a grid file.
        If a Zones object is provided, it should contain the grid polygons.
        The output will be written to the specified output directory.
        If the output directory already exists, it will be overwritten if overwrite is set to True.
        If output is None, the output will be written to the parent directory of the grid file, 'data' subdirectory.
        If parallel is set to True, the computation will be done in parallel using threads.

        :param grid: The grid to convert the data to.
        :param output: The output directory where the data will be written.
        :param overwrite: If True, the output directory will be overwritten if it already exists.
        :param parallel: If True, the computation will be done in parallel using threads.
        """
        import concurrent.futures

        if isinstance(grid, Path | str):
            grid = Path(grid)
            if not grid.exists():
                logging.error(_("The grid file {} does not exist.").format(grid))
                return
            grid = Zones(grid)
        elif not isinstance(grid, Zones):
            logging.error(_("The grid must be a Path, str or Zones object."))
            return

        if output is None:
            output = Path(grid.filename).parent.parent / 'data'
            output.mkdir(parents=True, exist_ok=True)

        if output.exists():
            if not overwrite:
                logging.error(_("The output directory {} already exists and overwrite is set to False.").format(output))
                return
            logging.warning(_("The output directory {} already exists.").format(output))
            logging.warning(_("The data will be overwritten."))

        # For each grid cells, we need the fraction of each polygon for each configuration
        grid_list_polygons = [curzone.myvectors[0].polygon for curzone in grid.myzones]

        fractions = {}
        for idx in tqdm(range(len(self._codes))):

            # Get the geometry for the code
            geometry = self.get_geometry4codeindex(idx+1, all_polygons=False)
            code = self._codes[idx+1]

            if geometry is None:
                logging.error(_("The geometry for code {} is None.").format(code))
                continue

            thiessen_polygons = [curzone.myvectors[0].polygon for curzone in geometry.myzones]

            # Compute the fraction of surface intersection for each polygon
            loc_frac = np.zeros((len(grid_list_polygons), len(thiessen_polygons)), dtype=np.float64)
            for i, grid_polygon in enumerate(grid_list_polygons):
                for j, thiessen_polygon in enumerate(thiessen_polygons):
                    if grid_polygon.intersects(thiessen_polygon):
                        intersection = grid_polygon.intersection(thiessen_polygon)
                        loc_frac[i, j] = intersection.area / grid_polygon.area

            # check if the fractions sum to 1 for each grid cell
            if not np.allclose(np.sum(loc_frac, axis=1), 1.0):
                logging.warning(_("The fractions for code {} do not sum to 1 for all grid cells.").format(code))
                logging.warning(_("The fractions will be normalized."))
            # Normalize the fractions
            non_zeros = np.sum(loc_frac, axis=1) > 0
            loc_frac[non_zeros] = loc_frac[non_zeros] / np.sum(loc_frac, axis=1, keepdims=True)[non_zeros]

            # if all fractions are 0, ignore tghe array
            if np.all(loc_frac == 0):
                logging.warning(_("All fractions for index {} are 0.").format(idx))
                fractions[code] = None
            else:
                # Store the fractions in the dictionary
                fractions[code] = loc_frac

            geometry.reset_linestring()

        # Iterate on each time step, compute and store the rain data
        gridded_rain = np.zeros((grid.nbzones, self.nb_records), dtype=np.float64)

        def compute_gridded_rain(idx):
            rains = self.get_rains4index(idx)
            index_geom = self.get_config4index(idx)
            code = self._codes[index_geom]
            frac = fractions[code]
            if frac is None:
                logging.warning(_("No fractions found for index {}. Skipping.").format(idx))
                return idx, None
            else:
                # Compute the gridded rain data
                return idx, np.dot(frac, rains)

        if parallel:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(tqdm(executor.map(compute_gridded_rain, range(self.nb_records)), total=self.nb_records))
        else:
            results = [compute_gridded_rain(idx) for idx in tqdm(range(self.nb_records))]

        for idx, result in results:
            if result is not None:
                gridded_rain[:, idx] = result

        # write the data to binary files
        for idx in tqdm(range(grid.nbzones)):
            zone_name = grid[idx].myname
            rain_data = gridded_rain[idx, :]

            # Write the data to a binary file
            filename = output / f"{zone_name}.rain.dat"
            self._write_rain_binary(zone_name, filename, rain_data)


    def plot_spatial_rain4index(self, index:int, figax=None, title:str = None, cmap:str = 'viridis'):
        """
        Plot the spatial distribution of rain for a given index.
        The index should be an integer representing the time step position.
        """

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        rains    = self.get_rains4index(index)
        geometry = self.get_geometry4index(index, all_polygons=False)

        if rains is None or geometry is None:
            logging.error(_("No rain data or geometry found for the given index."))
            return

        # Plot the rain data
        geometry.add_values('rain', rains)  # Convert to mm
        geometry.set_colors_from_value('rain', cmap=cmap, vmin = 0., vmax=self.rain_maximum)
        geometry.set_filled(True)
        geometry.plot_matplotlib(ax)

        if title is not None:
            ax.set_title(title)
        else:
            time = dt.fromtimestamp(self.timestamps[index]).replace(tzinfo=tz.utc)
            ax.set_title(_("Rain distribution for {}").format(time.strftime('%Y-%m-%d %H:%M:%S %Z')))

        return fig, ax

    def animation_spatial_rain_index(self, code:int = 1, idx_start:int = 0, idx_end:int = -1, figax=None, cmap:str = 'viridis', interval:int = 100):
        """
        Create an animation of the spatial distribution of rain for all indices.
        The animation will be displayed using matplotlib's FuncAnimation.
        """
        import matplotlib
        from matplotlib.animation import FuncAnimation

        if idx_start < 0:
            idx_start = 0
        if idx_end < 0 or idx_end >= self.nb_records:
            idx_end = self.nb_records

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        def update(index):
            ax.clear()
            self.plot_spatial_rain4index(int(index), figax=(fig, ax), cmap=cmap)

        if code not in self._codes.values():
            logging.error(_("The code {} is not valid.").format(code))
            return

        # Get the indices for the given code
        steps = self.get_computed_steps4code(code)
        if steps is None:
            logging.error(_("No steps found for the given code."))
            return
        if len(steps) == 0:
            logging.error(_("No steps found for the given code."))
            return

        # Remove all steps before idx_start and after idx_end
        steps = [s for s in steps if idx_start <= s <= idx_end]

        # Create the animation
        matplotlib.rcParams['animation.embed_limit'] = 2**128
        ani = FuncAnimation(fig, update, frames=tqdm(steps), interval=interval, repeat=True)

        return ani

    def animation_spatial_rain_date(self, code:int = 1, date_start:dt = 0, date_end:dt = -1, figax=None, cmap:str = 'viridis', interval:int = 100):
        """
        Create an animation of the spatial distribution of rain for all indices within a date range.
        The animation will be displayed using matplotlib's FuncAnimation.
        """
        import matplotlib
        from matplotlib.animation import FuncAnimation

        if date_start is None:
            date_start = self.time_begin
        if date_end is None or date_end >= self.time_end:
            date_end = self.time_end

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        def update(index):
            ax.clear()
            self.plot_spatial_rain4index(int(index), figax=(fig, ax), cmap=cmap)

        if code not in self._codes.values():
            logging.error(_("The code {} is not valid.").format(code))
            return

        # Get the indices for the given code
        steps = self.get_computed_steps4code(code)
        if steps is None:
            logging.error(_("No steps found for the given code."))
            return
        if len(steps) == 0:
            logging.error(_("No steps found for the given code."))
            return

        # Remove all steps before date_start and after date_end
        steps = [s for s in steps if date_start <= dt.fromtimestamp(self.timestamps[s], tz=tz.utc) <= date_end]

        # Create the animation
        matplotlib.rcParams['animation.embed_limit'] = 2**128
        ani = FuncAnimation(fig, update, frames=tqdm(steps), interval=interval, repeat=True)

        return ani