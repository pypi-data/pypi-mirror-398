import pandas as pd
import geopandas as gpd

import numpy as np
from osgeo import osr, gdal
from pyproj import Proj, Transformer
from pathlib import Path

import matplotlib.pyplot as plt
from scipy.spatial import KDTree
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

DATADIR = Path(r'P:\Donnees\Pluies\IRM\climateGrid') # Path to the IRM climate data directory - To change if needed

def transform_latlon_to_lambert72_list(lat_list:list[float], lon_list:list[float]) -> list[tuple[float, float]]:
    """
    Transform lists of EPSG:4258 coordinates to Lambert 72 coordinates.

    Coordinates from IRM are in EPSG:4258, and we want to convert them to Lambert 72 (EPSG:31370).
    """
    t = Transformer.from_crs('EPSG:4258', 'EPSG:31370', always_xy=True)
    return [t.transform(lon, lat) for lat, lon in zip(lat_list, lon_list)]

def read_pixel_positions(data_dir:Path=DATADIR) -> tuple[list[int], list[tuple[float, float]]]:
    """
    Read pixel positions from the metadata file.
    """

    file = data_dir / 'climategrid_pixel_metadata.csv'

    if not file.exists():
        logging.error(f"Metadata file {file} does not exist.")
        return None, None

    df = pd.read_csv(file,
                        sep=";",
                        header=0,
                        dtype={'PIXEL_ID': int,
                            'PIXEL_LON_CENTER': float,
                            'PIXEL_LAT_CENTER': float},
                        index_col='PIXEL_ID')

    return df.index, transform_latlon_to_lambert72_list(df['PIXEL_LAT_CENTER'].to_list(),
                                                       df['PIXEL_LON_CENTER'].to_list())

def convert_pixels_to_squares(pixels:list[tuple[float, float]]) -> tuple[list[tuple[tuple[float, float], ...]], KDTree]:
    """
    From pixels coordinates, define squares around each pixel center.

    Corners are defined as the average of the pixel center and its neighbors.
    """

    PIXEL_SIZE = 5000
    NB = len(pixels)

    pixels = np.array(pixels)

    # create a KDTree for fast neighbor search
    tree = KDTree(pixels)

    # find the 4 nearest neighbors for each potential corner
    corner1 = [(p[0] - PIXEL_SIZE / 2, p[1] - PIXEL_SIZE / 2) for p in pixels] # lower-left corner
    corner2 = [(p[0] + PIXEL_SIZE / 2, p[1] - PIXEL_SIZE / 2) for p in pixels] # lower-right corner
    corner3 = [(p[0] + PIXEL_SIZE / 2, p[1] + PIXEL_SIZE / 2) for p in pixels] # upper-right corner
    corner4 = [(p[0] - PIXEL_SIZE / 2, p[1] + PIXEL_SIZE / 2) for p in pixels] # upper-left corner

    d1, i1 = tree.query(corner1, k=4, distance_upper_bound=PIXEL_SIZE*1.1)
    d2, i2 = tree.query(corner2, k=4, distance_upper_bound=PIXEL_SIZE*1.1)
    d3, i3 = tree.query(corner3, k=4, distance_upper_bound=PIXEL_SIZE*1.1)
    d4, i4 = tree.query(corner4, k=4, distance_upper_bound=PIXEL_SIZE*1.1)

    squares = []
    for i, pixel in enumerate(pixels):

        used = i1[i][i1[i] != NB]  # filter out the invalid indices
        if len(used) in [1, 3]:
            x1, y1 = pixel[0] - PIXEL_SIZE / 2, pixel[1] - PIXEL_SIZE / 2
        elif len(used) == 2:
            dx = (pixels[used[0], 0] - pixels[used[1], 0])
            dy = (pixels[used[0], 1] - pixels[used[1], 1])
            if abs(dx) < 100:
                x1, y1 = pixel[0] - PIXEL_SIZE / 2, np.asarray([pixels[used,1]]).mean()
            else:
                x1, y1 = np.asarray([pixels[used,0]]).mean(), pixel[1] - PIXEL_SIZE / 2
        else:
            x1, y1 = np.asarray([pixels[used,0]]).mean(), np.asarray([pixels[used,1]]).mean()

        used = i2[i][i2[i] != NB]
        if len(used) in [1, 3]:
            x2, y2 = pixel[0] + PIXEL_SIZE / 2, pixel[1] - PIXEL_SIZE / 2
        elif len(used) == 2:
            dx = (pixels[used[0], 0] - pixels[used[1], 0])
            dy = (pixels[used[0], 1] - pixels[used[1], 1])
            if abs(dx) < 100:
                x2, y2 = pixel[0] + PIXEL_SIZE / 2, np.asarray([pixels[used,1]]).mean()
            else:
                x2, y2 = np.asarray([pixels[used,0]]).mean(), pixel[1] - PIXEL_SIZE / 2
        else:
            x2, y2 = np.asarray([pixels[used,0]]).mean(), np.asarray([pixels[used,1]]).mean()

        used = i3[i][i3[i] != NB]
        if len(used) in [1, 3]:
            x3, y3 = pixel[0] + PIXEL_SIZE / 2, pixel[1] + PIXEL_SIZE / 2
        elif len(used) == 2:
            dx = (pixels[used[0], 0] - pixels[used[1], 0])
            dy = (pixels[used[0], 1] - pixels[used[1], 1])
            if abs(dx) < 100:
                x3, y3 = pixel[0] + PIXEL_SIZE / 2, np.asarray([pixels[used,1]]).mean()
            else:
                x3, y3 = np.asarray([pixels[used,0]]).mean(), pixel[1] + PIXEL_SIZE / 2
        else:
            x3, y3 = np.asarray([pixels[used,0]]).mean(), np.asarray([pixels[used,1]]).mean()

        used = i4[i][i4[i] != NB]
        if len(used) in [1, 3]:
            x4, y4 = pixel[0] - PIXEL_SIZE / 2, pixel[1] + PIXEL_SIZE / 2
        elif len(used) == 2:
            dx = (pixels[used[0], 0] - pixels[used[1], 0])
            dy = (pixels[used[0], 1] - pixels[used[1], 1])
            if abs(dx) < 100:
                x4, y4 = pixel[0] - PIXEL_SIZE / 2, np.asarray([pixels[used,1]]).mean()
            else:
                x4, y4 = np.asarray([pixels[used,0]]).mean(), pixel[1] + PIXEL_SIZE / 2
        else:
            x4, y4 = np.asarray([pixels[used,0]]).mean(), np.asarray([pixels[used,1]]).mean()

        if x1 == pixel[0]:
            x1 = pixel[0] - PIXEL_SIZE / 2
        if y1 == pixel[1]:
            y1 = pixel[1] - PIXEL_SIZE / 2
        if x2 == pixel[0]:
            x2 = pixel[0] + PIXEL_SIZE / 2
        if y2 == pixel[1]:
            y2 = pixel[1] - PIXEL_SIZE / 2
        if x3 == pixel[0]:
            x3 = pixel[0] + PIXEL_SIZE / 2
        if y3 == pixel[1]:
            y3 = pixel[1] + PIXEL_SIZE / 2
        if x4 == pixel[0]:
            x4 = pixel[0] - PIXEL_SIZE / 2
        if y4 == pixel[1]:
            y4 = pixel[1] + PIXEL_SIZE / 2

        squares.append(((x1, y1), (x2, y2), (x3, y3), (x4, y4)))

    return squares, tree

def read_historical_year_month(year:int, month:int,
                               data_dir:Path=DATADIR) -> pd.DataFrame:
    """
    Read a specific year and month from the climate data.

    Available variables are :
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

    From IRM's Metadata description:
    - TEMP_MAX		°C		daily maximum temperature from 08:00LT on DATE_BEGIN to 08:00LT on DATE_END+1
    - TEMP_MIN		°C		daily minimum temperature from 08:00LT on DATE_BEGIN-1 to 08:00LT on DATE_END
    - TEMP_AVG		°C		average temperature (average of TEMP_MAX and TEMP_MIN)
    - PRECIP_QUANTITY		mm		precipitation quantity from 08:00LT on DATE_BEGIN to 08:00LT on DATE_END+1
    - HUMIDITY_RELATIVE	percentage	average relative humidity
    - PRESSURE		hPa		sea level pressure
    - SUN_DURATION				average daily sunshine duration (hours/day)
    - SHORT_WAVE_FROM_SKY			average daily global solar radiation (kWh/m2/day)
    - EVAPOTRANS_REF		mm		reference evapotranspiration ET0

    :param year: Year to read
    :type year: int
    :param month: Month to read
    :type month: int
    :param variable: Variable to read (e.g., 'temperature', 'precipitation')
    :type variable: str
    :param data_dir: Directory where the data is stored
    :type data_dir: Path
    :return: DataFrame containing the data for the specified year and month
    """

    # force month to be two digits
    month = f"{month:02d}"
    file_path = data_dir / f"climategrid_{year}{month:}.csv"

    if file_path.exists():
        logging.info(f"Reading data from {file_path}")
        df = pd.read_csv(file_path, header=0, sep=';', index_col='pixel_id')

        # conevrt 'day' to datetime UTC
        df['day'] = pd.to_datetime(df['day'], format='%Y/%m/%d', utc=True)
        return df
    else:
        logging.warning(f"File {file_path} does not exist.")
        return pd.DataFrame()

def scan_climate_files(data_dir:Path=DATADIR) -> list[Path]:
    """
    Scan the directory for climate data files.

    :param data_dir: Directory where the data is stored
    :type data_dir: Path
    :return: List of paths to climate data files
    """
    all = list(data_dir.glob('climategrid_*.csv'))
    # all.pop(all.index('climategrid_parameters_description.txt'))
    f = [file.stem for file in all]
    all.pop(f.index('climategrid_pixel_metadata'))
    return all

def find_first_available_year_month(data_dir:Path=DATADIR) -> int:
    """
    Find the first available year in the climate data files.

    :param data_dir: Directory where the data is stored
    :type data_dir: Path
    :return: First available year as an integer
    """
    files = scan_climate_files(data_dir)
    years = [int(file.stem.split('_')[1][:4]) for file in files]
    minyear = min(years) if years else None
    if minyear is not None:
        logging.info(f"First available year: {minyear}")
        #find the first month of the first year
        first_month = min([int(file.stem.split('_')[1][4:6]) for file in files if file.stem.startswith(f'climategrid_{minyear}')])
        logging.info(f"First available month: {first_month}")
        return minyear, first_month
    else:
        logging.warning("No climate data files found.")
        return None, None

def find_last_available_year_month(data_dir:Path=DATADIR) -> int:
    """
    Find the last available year in the climate data files.

    :param data_dir: Directory where the data is stored
    :type data_dir: Path
    :return: Last available year as an integer
    """
    files = scan_climate_files(data_dir)
    years = [int(file.stem.split('_')[1][:4]) for file in files]
    maxyear = max(years) if years else None
    if maxyear is not None:
        logging.info(f"Last available year: {maxyear}")
        #find the last month of the last year
        last_month = max([int(file.stem.split('_')[1][4:6]) for file in files if file.stem.startswith(f'climategrid_{maxyear}')])
        logging.info(f"Last available month: {last_month}")
        return maxyear, last_month
    else:
        logging.warning("No climate data files found.")
        return None, None

def read_between(data_dir:Path=DATADIR, start_year:int = 1961, start_month:int = 1, end_year:int = 2025, end_month:int = 6) -> pd.DataFrame:
    """
    Read climate data files into a single DataFrame.

    :param data_dir: Directory where the data is stored
    :type data_dir: Path
    :return: DataFrame containing all climate data
    """

    _start_year, _start_month = find_first_available_year_month(data_dir)
    _end_year, _end_month = find_last_available_year_month(data_dir)

    if start_year < _start_year or (start_year == _start_year and start_month < _start_month):
        logging.warning(f"Start date {start_year}-{start_month} is before the first available data {_start_year}-{_start_month}. Using {_start_year}-{_start_month} instead.")
        start_year, start_month = _start_year, _start_month

    if end_year > _end_year or (end_year == _end_year and end_month > _end_month):
        logging.warning(f"End date {end_year}-{end_month} is after the last available data {_end_year}-{_end_month}. Using {_end_year}-{_end_month} instead.")
        end_year, end_month = _end_year, _end_month

    logging.info(f"Reading data from {start_year}-{start_month} to {end_year}-{end_month}")

    mapped = []
    for year in range(start_year, end_year+1):
        for month in range(1, 13):
            if year == start_year and month < start_month:
                continue
            if year == end_year and month > end_month:
                continue
            mapped.append((year, month))

    df_list = list(map(lambda ym: read_historical_year_month(ym[0], ym[1], data_dir), mapped))

    return pd.concat(df_list, axis=0)

def read_all_data(data_dir:Path=DATADIR) -> pd.DataFrame:
    """
    Read all climate data files into a single DataFrame.

    :param data_dir: Directory where the data is stored
    :type data_dir: Path
    :return: DataFrame containing all climate data
    """

    return read_between(data_dir, 0, 0, 2100, 12)

if __name__ == "__main__":

    print(find_first_available_year_month())
    print(find_last_available_year_month())

    data = read_all_data()
    print(data.head())

    pixel_ids, xy = read_pixel_positions()
    print(f"Pixel IDs: {pixel_ids}")
    print(f"Pixel XY: {xy}")

    squares = convert_pixels_to_squares(xy)

    xy = np.array(xy)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(xy[:, 0], xy[:, 1], s=1)
    ax.set_title("Pixel Positions in Lambert 72")
    ax.set_xlabel("X (Lambert 72)")
    ax.set_ylabel("Y (Lambert 72)")

    # plot squares
    for square in squares:
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = square
        ax.plot([x1, x2, x3, x4, x1], [y1, y2, y3, y4, y1], color='red')
    ax.set_aspect('equal', adjustable='box')
    plt.show()
