import logging

import numpy as np
from shapely.geometry import Point, LineString
from typing import Literal
import pandas as pd
import geopandas as gpd
from pathlib import Path

from .PyTranslate import _
from .drawing_obj import Element_To_Draw
from .PyVertexvectors import Triangulation, vector,Zones, zone, Polygon
from .wolf_array import WolfArray, header_wolf

class Array_analysis_onepolygon():
    """ Class for values analysis of an array based on a polygon.

    This class select values insides a polygon and plot statistics of the values.

    The class is designed to be used with the WolfArray class and the vector class from the PyVertexvectors module.

    Plots of the values distribution can be generated using seaborn or plotly.
    """

    def __init__(self, wa:WolfArray, polygon:vector, buffer_size:float = 0.0):

        self._wa = wa

        if buffer_size > 0.0:
            self._polygon = polygon.buffer(buffer_size, inplace=False)
        elif buffer_size == 0.0:
            self._polygon = polygon
        else:
            raise ValueError("Buffer size must be greater than or equal to 0.0.")

        self._selected_cells = None
        self._values = None

    @ property
    def centroid(self) -> Point:
        """ Get the centroid of the polygon as a Point object.

        :return: Shapely Point object representing the centroid of the polygon
        """
        return self._polygon.centroid

    def values(self, which:Literal['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Values', 'Area']) -> pd.DataFrame | float:
        """ Get the values as a pandas DataFrame

        :param which: Mean, Std, Median, Sum, Volume, Values
        """

        authorized = ['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Values', 'Area']
        if which not in authorized:
            raise ValueError(f"Invalid value for 'which'. Must be one of {authorized}.")

        if self._values is None:
            self.compute_values()

        if which == 'Area' and 'Area' not in self._values:
            self._add_area2values()

        if self._values is None:
            raise ValueError("No values computed. Please call compute_values() first.")

        if which == 'Values':
            return pd.DataFrame(self._values[_(which)], columns=[self._polygon.myname])
        else:
            return self._values[which]

    def as_vector(self, add_values:bool = True):
        """ Return a copy of the polygon with the values as attributes. """

        newvec = self._polygon.deepcopy()

        if add_values:
            if self._values is None:
                self.compute_values()
                self._add_area2values()

            if self._values is None:
                raise ValueError("No values computed. Please call compute_values() first.")

            for key, value in self._values.items():
                newvec.add_value(key, value)

        newvec.myname = self._polygon.myname
        return newvec

    def select_cells(self, mode:Literal['polygon', 'buffer'] = 'polygon', **kwargs):
        """Select the cells inside the polygon.

        :param mode: 'polygon' or 'buffer'
        :param kwargs: 'polygon' for polygon selection or 'buffer' for buffer size

        For polygon selection, the polygon must be provided in kwargs or use the polygon set during initialization.
        For buffer selection, the buffer size in meter must be provided in kwargs.
        """

        if mode == 'polygon':
            if 'polygon' in kwargs:
                self._polygon = kwargs['polygon']
            elif self._polygon is None:
                raise ValueError("No polygon provided. Please provide a polygon to select cells.")
            self._select_cells_polygon(self._polygon)

        elif mode == 'buffer':
            if 'buffer' in kwargs and self._polygon is not None:
                self._select_cells_buffer(kwargs['buffer'])
            else:
                raise ValueError("No buffer size provided. Please provide a buffer size to select cells.")
        else:
            raise ValueError("Invalid mode. Please use 'polygon' or 'buffer'.")

    def _select_cells_polygon(self, selection_poly:vector = None):
        """ Select the cells inside the polygon """

        if selection_poly is None:
            if self._polygon is None:
                raise ValueError("No polygon provided. Please provide a polygon to select cells.")
            selection_poly = self._polygon
        else:
            self._polygon = selection_poly

        self._selected_cells = self._wa.get_xy_inside_polygon(selection_poly)

    def _select_cells_buffer(self, buffer_size:float = 0.0):
        """ Select the cells inside the buffer of the polygon """

        if buffer_size > 0.0:
            selection_poly = self._polygon.buffer(buffer_size, inplace=False)
        elif buffer_size == 0.0:
            selection_poly = self._polygon
        else:
            raise ValueError("Buffer size must be greater than or equal to 0.0.")

        self._selected_cells = self._wa.get_xy_inside_polygon(selection_poly)

    def compute_values(self):
        """ Get the values of the array inside the polygon """

        if self._selected_cells is None:
            if self._polygon is None:
                raise ValueError("No polygon provided. Please provide a polygon to select cells.")

            self._values = self._wa.statistics(self._polygon)
        else:
            self._values = self._wa.statistics(self._selected_cells)

    def _add_area2values(self):
        """ Add the area of the polygon to the values """

        if self._selected_cells is None:
            if self._polygon is None:
                raise ValueError("No polygon provided. Please provide a polygon to select cells.")

            self._values['Area'] = self._polygon.area
            centroid = self._polygon.centroid
            self._values['X'] = centroid.x
            self._values['Y'] = centroid.y
        else:
            self._values['Area'] = len(self._selected_cells) * self._wa.dx * self._wa.dy
            self._values['X'] = np.mean(self._selected_cells[:, 0])
            self._values['Y'] = np.mean(self._selected_cells[:, 1])

    @property
    def n_selected_cells(self) -> int:
        """ Get the number of selected cells """
        if self._selected_cells is None:
            return 0

        return len(self._selected_cells)

    def get_selection(self) -> np.ndarray:
        """ Get the selected cells as a numpy array of coordinates.

        :return: numpy array of shape (n, 2) with the coordinates of the selected cells
        """
        if self._selected_cells is None:
            raise ValueError("No cells selected. Please call select_cells() first.")

        return np.array(self._selected_cells)

    def reset_selection(self):
        """ Reset the selection of cells """
        self._selected_cells = None
        self._values = None

    def plot_values(self, show:bool = True, bins:int = 100,
                    engine:Literal['seaborn', 'plotly'] = 'seaborn'):
        """ Plot a histogram of the values """

        if engine == 'seaborn':
            return self.plot_values_seaborn(show=show, bins=bins)
        elif engine == 'plotly':
            return self.plot_values_plotly(show=show, bins=bins)

    def plot_values_seaborn(self, bins:int = 100, show:bool = True):
        """ Plot a histogram of the values """

        import seaborn as sns
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        sns.histplot(self.values('Values'), bins=bins,
                     kde=True, ax=ax,
                     stat="density")

        # Add mean, std, median values on plot
        mean = self.values('Mean')
        # std = self.values('Std').values[0]
        median = self.values('Median')

        # test noen and masked value
        if mean is not None and mean is not np.ma.masked:
            ax.axvline(mean, color='r', linestyle='--', label=f'Mean: {mean:.2f}')
        if median is not None and median is not np.ma.masked:
            ax.axvline(median, color='b', linestyle='--', label=f'Median: {median:.2f}')

        ax.legend()
        ax.set_xlabel('Values')
        ax.set_ylabel('Frequency')
        ax.set_title('Values distribution')

        if show:
            plt.show()

        return (fig, ax)

    def plot_values_plotly(self, bins:int = 100, show:bool = True):
        """ Plot a histogram of the values """

        import plotly.express as px

        fig = px.histogram(self.values('Values'), x=self._polygon.myname,
                           nbins=bins, title='Values distribution',
                           histnorm='probability density')

        # Add mean, std, median values on plot
        mean = self.values('Mean')
        median = self.values('Median')

        if mean is not None and mean is not np.ma.masked:
            fig.add_vline(x=mean, line_color='red', line_dash='dash', annotation_text=f'Mean: {mean:.2f}')
        if median is not None and median is not np.ma.masked:
            fig.add_vline(x=median, line_color='blue', line_dash='dash', annotation_text=f'Median: {median:.2f}')

        fig.update_layout(xaxis_title='Values', yaxis_title='Frequency')

        if show:
            fig.show(renderer='browser')

        return fig

    @property
    def has_values(self) -> bool:
        """ Check if there useful values """
        if self._values is None:
            self.compute_values()

        return len(self.values('Values')) > 0

    @property
    def has_strictly_positive_values(self) -> bool:
        """ Check if there useful values """
        if self._values is None:
            self.compute_values()

        return len(self.values('Values') > 0) > 0

    def distribute_values(self, bins:list[float]):
        """ Distribute the values in bins

        :param bins: list of bin edges
        :return: pandas DataFrame with the counts of values in each bin
        """

        if self._values is None:
            self.compute_values()

        if self._values is None:
            raise ValueError("No values computed. Please call compute_values() first.")

        values = self.values('Values')
        if values is None or len(values) == 0:
            raise ValueError("No values to distribute. Please compute values first.")

        counts, __ = np.histogram(values, bins=bins)
        return pd.DataFrame({'Bin Edges': bins[:-1], 'Counts': counts})

class Array_analysis_polygons():
    """ Class for values analysis of an array based on a polygon.

    This class select values insides a polygon and plot statistics of the values.

    The class is designed to be used with the WolfArray class and the vector class from the PyVertexvectors module.

    Plots of the values distribution can be generated using seaborn or plotly.
    """

    def __init__(self, wa:WolfArray, polygons:zone, buffer_size:float = 0.0):
        """ Initialize the class with a WolfArray and a zone of polygons """

        self._wa = wa
        self._polygons = polygons # pointer to the original zone of polygons
        self._check_names()

        self._has_buffer = buffer_size > 0.0

        self._zone = {polygon.myname: Array_analysis_onepolygon(self._wa, polygon, buffer_size) for polygon in self._polygons.myvectors if polygon.used}

        self._active_categories = self.all_categories

    def as_zone(self, add_values:bool = True) -> zone:
        """ Convert the analysis to a zone of polygons """

        ret_zone = zone(name=self._polygons.myname)
        for name, poly in self._zone.items():
            if name.split('___')[0] in self._active_categories:
                if poly.has_values:
                    ret_zone.add_vector(poly.as_vector(add_values), forceparent=True)

        return ret_zone

    @property
    def _areas(self) -> list[float]:
        """ Get the areas of the polygons in the zone """
        return [poly.area for poly in self.polygons.myvectors if poly.used]

    @property
    def all_categories(self) -> list[str]:
        """ Get the name of the building categories from the Polygons """

        return list(set([v.myname.split('___')[0] for v in self._polygons.myvectors if v.used]))

    @property
    def active_categories(self) -> list[str]:
        """ Get the active categories for the analysis """
        return self._active_categories

    @active_categories.setter
    def active_categories(self, categories:list[str]):
        """ Set the active categories for the analysis

        :param categories: list of categories to activate
        """
        if not categories:
            raise ValueError("The list of categories must not be empty.")

        all_categories = self.all_categories
        for cat in categories:
            if cat not in all_categories:
                logging.debug(f"Category '{cat}' is not a valid category.")

        self._active_categories = categories

    def activate_category(self, category_name:str):
        """ Activate a category for the analysis

        :param category_name: name of the category to activate
        """
        if category_name not in self.all_categories:
            raise ValueError(f"Category '{category_name}' is not a valid category. Available categories: {self.all_categories}")

        if category_name not in self._active_categories:
            self._active_categories.append(category_name)

    def deactivate_category(self, category_name:str):
        """ Deactivate a category for the analysis

        :param category_name: name of the category to deactivate
        """
        if category_name not in self._active_categories:
            raise ValueError(f"Category '{category_name}' is not active. Active categories: {self._active_categories}")

        self._active_categories.remove(category_name)

    def _check_names(self):
        """ Check if the names of the polygons are unique """
        names = [poly.myname for poly in self._polygons.myvectors if poly.used]
        if len(names) != len(set(names)):
            raise ValueError("Polygon names must be unique. Please rename the polygons in the zone.")

    def __getitem__(self, key:str) -> Array_analysis_onepolygon:
        """ Get the polygon by name """
        if key in self._zone:
            return self._zone[key]
        else:
            raise KeyError(f"Polygon {key} not found in zone.")

    def reset_selection(self):
        """ Reset the selection of cells in all polygons """
        for poly in self._zone.values():
            poly.reset_selection()

    def get_values(self) -> pd.DataFrame:
        """ Get the values of all polygons in the zones as a pandas DataFrame.

          One column per polygon with the values."""

        lst = [pol.values('Values') for key, pol in self._zone.items() if pol.has_values and key.split('___')[0] in self._active_categories]
        return pd.concat(lst, axis=1)

    def get_geometries(self) -> pd.DataFrame:
        """ Get the centroids of all polygons in the zone as a pandas DataFrame.

        :return: pandas DataFrame with the centroids of the polygons
        """
        centroids = {key: {'Centroid' : poly.centroid, 'X': poly.centroid.x, 'Y' : poly.centroid.y, 'Geometry': poly._polygon.polygon} for key, poly in self._zone.items() if poly.has_values and key.split('___')[0] in self._active_categories}
        return pd.DataFrame.from_dict(centroids, orient='index')

    def get_geodataframe_with_values(self, epsg:int = 31370) -> 'gpd.GeoDataFrame':
        """ Create a GeoDataFrame with the centroids and values of the polygons.

        Values are added as a column named 'Values' as Numpy array."""

        import geopandas as gpd

        geom = self.get_geometries()
        # Add values as numpy arrays to the DataFrame
        geom['Values'] = None
        geom['Values'] = geom['Values'].astype(object)

        # Get values for each polygon and add them to the DataFrame
        for key, poly in self._zone.items():
            if poly.has_values and key.split('___')[0] in self._active_categories:
                values = poly.values('Values')
                geom.at[key, 'Values'] = values.to_numpy().ravel()

        # Create a GeoDataFrame
        gdf = gpd.GeoDataFrame(geom, geometry='Geometry', crs=f'EPSG:{epsg}')
        return gdf

    @property
    def polygons(self) -> zone:
        """ Get the zone of polygons """
        if self._has_buffer:
            # return a new zone with the polygons and their buffers
            ret_zone = zone(name = self._polygons.myname)
            for name, poly in self._zone.items():
                if name.split('___')[0] in self._active_categories:
                    ret_zone.add_vector(poly._polygon)

            return ret_zone
        else:
            # return the original zone of polygons
            return self._polygons

    @property
    def keys(self) -> list[str]:
        """ Get the names of the polygons in the zone """
        return list(self._zone.keys())

    def update_values(self):
        """ Update the polygons values in the zone """
        for poly in self._zone.values():
            poly.compute_values()

    def plot_values(self, show:bool = True, bins:int = 100,
                    engine:Literal['seaborn', 'plotly'] = 'seaborn'):
        """ Plot a histogram of the values """

        if engine == 'seaborn':
            return self.plot_values_seaborn(show=show, bins=bins)
        elif engine == 'plotly':
            return self.plot_values_plotly(show=show, bins=bins)

    def plot_values_seaborn(self, bins:int = 100, show:bool = True):
        """ Plot a histogram of the values """
        return {key: pol.plot_values_seaborn(bins=bins, show=show) for key, pol in self._zone.items() if key.split('___')[0] in self._active_categories}

    def plot_values_plotly(self, bins:int = 100, show:bool = True):
        """ Plot a histogram of the values """

        return {key: pol.plot_values_plotly(bins=bins, show=show) for key, pol in self._zone.items() if key.split('___')[0] in self._active_categories}

    def count_strictly_positive(self) -> int:
        """ Count the number of polygons with values greater than zero """
        nb = 0
        for key, poly in self._zone.items():
            if key.split('___')[0] not in self._active_categories:
                continue
            if poly.has_strictly_positive_values:
                nb += 1
        return nb

    def values(self, which:Literal['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Area']) -> pd.Series:
        """ Get the values as a pandas DataFrame

        :param which: Mean, Std, Median, Sum, Volume
        :return: pandas DataFrame with the values for each polygon
        """

        authorized = ['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Area']
        if which not in authorized:
            raise ValueError(f"Invalid value for 'which'. Must be one of {authorized}.")

        values = {name: poly.values(which) for name, poly in self._zone.items() if poly.has_values and name.split('___')[0] in self._active_categories}

        if not values:
            raise ValueError("No values computed. Please compute values first.")

        return pd.Series(values)

    def distribute_polygons(self, bins:list[float], operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area']) -> pd.DataFrame:
        """ Distribute the values of each polygon in bins

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :return: pandas DataFrame with the counts of values in each bin for each polygon
        """

        values = np.asarray([poly.values(operator) for key, poly in self._zone.items() if poly.has_values and key.split('___')[0] in self._active_categories] )

        if values.size == 0:
            raise ValueError("No values to distribute. Please compute values first.")

        counts, __ = np.histogram(values, bins=bins)
        distribution = pd.DataFrame({'Bin Edges': bins[:-1], 'Counts': counts})

        return distribution

    def plot_distributed_values(self, bins:list[float],
                                operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'],
                                show:bool = True,
                             engine:Literal['seaborn', 'plotly'] = 'seaborn'):
        """ Plot the distribution of values in bins for each polygon

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :param show: whether to show the plot
        :param engine: 'seaborn' or 'plotly'
        """

        distribution = self.distribute_polygons(bins, operator)

        if engine == 'seaborn':
            fig, ax = self.plot_distribution_seaborn(distribution, show=show)
        elif engine == 'plotly':
            fig, ax = self.plot_distribution_plotly(distribution, show=show)

        ax.set_title(f'Distribution of Values ({operator})')

        return fig, ax

    def plot_distribution_seaborn(self, distribution:pd.DataFrame, show:bool = True):
        """ Plot the distribution of values in bins using seaborn

        :param distribution: pandas DataFrame with the counts of values in each bin
        :param show: whether to show the plot
        """

        import seaborn as sns
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        sns.barplot(x='Bin Edges', y='Counts', data=distribution, ax=ax)

        ax.set_xlabel('Bin Edges')
        ax.set_ylabel('Counts')
        ax.set_title('Distribution of Values')

        if show:
            plt.show()

        return (fig, ax)

    def plot_distribution_plotly(self, distribution:pd.DataFrame, show:bool = True):
        """ Plot the distribution of values in bins using plotly

        :param distribution: pandas DataFrame with the counts of values in each bin
        :param show: whether to show the plot
        """

        import plotly.express as px

        fig = px.bar(distribution, x='Bin Edges', y='Counts',
                     title='Distribution of Values')

        fig.update_layout(xaxis_title='Bin Edges', yaxis_title='Counts')

        if show:
            fig.show(renderer='browser')

        return fig

    def clustering(self, n_clusters:int = 5, operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'] = 'Mean'):
        """ Perform clustering on the polygons based on their values. """
        from sklearn.cluster import KMeans
        import geopandas as gpd

        # Get the values of the polygons
        values = self.values(operator)
        geometries = self.get_geodataframe_with_values()

        xy = geometries[['X', 'Y']].copy()

        if values.empty:
            raise ValueError("No values to cluster. Please compute values first.")

        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters)

        kmeans.fit(xy[['X', 'Y']].values)
        labels = kmeans.labels_
        geometries['Cluster'] = labels

        centroids = kmeans.cluster_centers_
        cluster_centroids = [Point(xy) for xy in centroids]

        # Find footprints of the clusters
        footprints = []
        for label in np.unique(labels):
            geom_cluster = geometries[geometries['Cluster'] == label]
            footprint = geom_cluster.geometry.unary_union.convex_hull
            footprints.append(footprint)

        return geometries, (cluster_centroids, footprints)


class Array_analysis_zones():
    """ Class for values analysis of an array based on a Zones instance.

    This class select values insides a zone of polygons and plot statistics of the values.
    """

    def __init__(self, wa:WolfArray, zones:Zones, buffer_size:float = 0.0):
        """ Initialize the class with a Wolf Zones """

        self._wa = wa
        self._zones = zones

        self._polygons = {zone.myname: Array_analysis_polygons(self._wa, zone, buffer_size) for zone in self._zones.myzones if zone.used}

    def as_zones(self, add_values:bool = True) -> Zones:
        """ Convert the analysis to a Zones instance """

        newzones = Zones(idx=self._zones.idx)
        for name, pol in self._polygons.items():
            newzones.add_zone(pol.as_zone(add_values), forceparent=True)

        return newzones


    def __getitem__(self, key:str) -> Array_analysis_polygons:
        """ Get the zone by name """
        if key in self._polygons:
            return self._polygons[key]
        else:
            raise KeyError(f"Zone {key} not found in zones.")

    def reset_selection(self):
        """ Reset the selection of cells in all polygons """
        for poly in self._polygons.values():
            poly.reset_selection()

    @property
    def keys(self) -> list[str]:
        """ Get the names of the polygons in the zones """
        return list(self._polygons.keys())

    def update_values(self):
        """ Update the polygons values in the zones """
        for pol in self._polygons.values():
            pol.update_values()

    def get_values(self) -> dict[str, pd.DataFrame]:
        """ Get the values of all polygons in the zones as a dictionary of pandas DataFrames """

        return {key: pol.get_values() for key, pol in self._polygons.items()}

    def plot_values(self, show:bool = True, bins:int = 100,
                    engine:Literal['seaborn', 'plotly'] = 'seaborn'):
        """ Plot a histogram of the values """
        if engine == 'seaborn':
            return self.plot_values_seaborn(show=show, bins=bins)
        elif engine == 'plotly':
            return self.plot_values_plotly(show=show, bins=bins)

    def plot_values_seaborn(self, bins:int = 100, show:bool = True):
        """ Plot a histogram of the values """
        return {key: pol.plot_values_seaborn(bins=bins, show=show) for key, pol in self._polygons.items()}

    def plot_values_plotly(self, bins:int = 100, show:bool = True):
        """ Plot a histogram of the values """
        return {key: pol.plot_values_plotly(bins=bins, show=show) for key, pol in self._polygons.items()}

    def distribute_zones(self, bins:list[float],
                         operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area']) -> dict[str, pd.DataFrame]:
        """ Distribute the values of each zone in bins

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :return: pandas DataFrame with the counts of values in each bin for each zone
        """

        return {key: pol.distribute_polygons(bins, operator) for key, pol in self._polygons.items()}

    def values(self, which:Literal['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Area']) -> dict[str, pd.Series]:
        """ Get the values as a dictionnary of pandas Series

        :param which: Mean, Std, Median, Sum, Volume
        :return: pandas DataFrame with the values for each polygon
        """

        authorized = ['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Area']
        if which not in authorized:
            raise ValueError(f"Invalid value for 'which'. Must be one of {authorized}.")

        values = {name: pol.values(which) for name, pol in self._polygons.items()}

        if not values:
            raise ValueError("No values computed. Please compute values first.")

        return values

class Arrays_analysis_zones():
    """
    Class for analysis multiples arrays based on a Zones instance.
    Each array must have the same shape.
    """

    def __init__(self, arrays:dict[str, WolfArray], zones:Zones, buffer_size:float = 0.0):
        """ Initialize the class with a list of WolfArray and a Zones instance """
        if not arrays:
            raise ValueError("The list of arrays must not be empty.")

        self._arrays = arrays
        self._zones = zones
        self._xlabel = 'Value'

        # Check that all arrays have the same shape
        ref = next(iter(arrays.values()))
        for array in arrays.values():
            if not array.is_like(ref):
                raise ValueError("All arrays must have the same shape.")

        self._polygons = {zone.myname: {key: Array_analysis_polygons(array, zone, buffer_size) for key, array in self._arrays.items()}
                          for zone in self._zones.myzones if zone.used }

        self._active_categories = self.all_categories
        self._active_arrays = self.all_arrays

    def __getitem__(self, key:str | tuple) -> Array_analysis_polygons:
        """ Get the zone by name """
        if isinstance(key, tuple):
            if len(key) != 2:
                raise ValueError("Key must be a tuple of (zone_name, array_name).")
            zone_name, array_name = key
            if zone_name not in self._polygons or array_name not in self._polygons[zone_name]:
                raise KeyError(f"Zone {zone_name} or array {array_name} not found in zones.")
            return self._polygons[zone_name][array_name]

        elif isinstance(key, str):
            if len(self._polygons) == 1:
                # If there is only one zone, return the first array in that zone
                zone_name = next(iter(self._polygons))
                if key in self._polygons[zone_name]:
                    return self._polygons[zone_name][key]
                else:
                    raise KeyError(f"Array {key} not found in the only zone available.")
            else:
                if key in self._polygons:
                    return self._polygons[key]
                else:
                    raise KeyError(f"Zone {key} not found in zones.")

    def as_zones(self, add_values:bool = True) -> Zones:
        """ Convert the analysis to a Zones instance """

        newzones = Zones(idx=self._zones.idx)
        for name, dct in self._polygons.items():
            for array_name, pols in dct.items():
                if array_name not in self._active_arrays:
                    continue

                newzone = pols.as_zone(add_values)
                newzone.myname = f"{array_name}"

                newzones.add_zone(newzone, forceparent=True)

        return newzones

    @property
    def _areas(self) -> dict[str, list[float]]:
        """ Get the areas of the polygons in the zones """
        return {polygons.myname: [poly.area for poly in polygons.myvectors if poly.used]
                for polygons in self._zones.myzones}

    @property
    def all_categories(self) -> list[str]:
        """ Get the name of the building categories from the Zones """

        return sorted(list(set([v.myname.split('___')[0] for z in self._zones.myzones for v in z.myvectors])))

    @property
    def all_arrays(self) -> list[str]:
        """ Get the names of all arrays """
        return list(self._arrays.keys())

    def activate_array(self, array_name:str):
        """ Activate an array for the analysis

        :param array_name: name of the array to activate
        """
        if array_name not in self.all_arrays:
            raise ValueError(f"Array '{array_name}' is not a valid array. Available arrays: {self.all_arrays}")

        if array_name not in self._active_arrays:
            self._active_arrays.append(array_name)

    def deactivate_array(self, array_name:str):
        """ Deactivate an array for the analysis

        :param array_name: name of the array to deactivate
        """
        if array_name not in self._active_arrays:
            raise ValueError(f"Array '{array_name}' is not active. Active arrays: {self._active_arrays}")

        self._active_arrays.remove(array_name)

    def activate_category(self, category_name:str):
        """ Activate a category for the analysis

        :param category_name: name of the category to activate
        """
        if category_name not in self.all_categories:
            raise ValueError(f"Category '{category_name}' is not a valid category. Available categories: {self.all_categories}")

        if category_name not in self._active_categories:
            self._active_categories.append(category_name)

        for zone_name, dct in self._polygons.items():
            for array_name, poly in dct.items():
                poly.active_categories = self._active_categories

    def deactivate_category(self, category_name:str):
        """ Deactivate a category for the analysis

        :param category_name: name of the category to deactivate
        """
        if category_name not in self._active_categories:
            raise ValueError(f"Category '{category_name}' is not active. Active categories: {self._active_categories}")

        self._active_categories.remove(category_name)

        for zone_name, dct in self._polygons.items():
            for array_name, poly in dct.items():
                poly.active_categories = self._active_categories

    @property
    def active_arrays(self) -> list[str]:
        """ Get the active arrays for the analysis """
        return self._active_arrays

    @active_arrays.setter
    def active_arrays(self, arrays:list[str]):
        """ Set the active arrays for the analysis

        :param arrays: list of arrays to activate
        """
        if not arrays:
            raise ValueError("The list of arrays must not be empty.")

        all_arrays = self.all_arrays
        for arr in arrays:
            if arr not in all_arrays:
                raise ValueError(f"Array '{arr}' is not a valid array. Available arrays: {all_arrays}")

        self._active_arrays = arrays

    @property
    def active_categories(self) -> list[str]:
        """ Get the active categories for the analysis """
        return self._active_categories

    @active_categories.setter
    def active_categories(self, categories:list[str]):
        """ Set the active categories for the analysis

        :param categories: list of categories to activate
        """
        if not categories:
            raise ValueError("The list of categories must not be empty.")

        all_categories = self.all_categories
        for cat in categories:
            if cat not in all_categories:
                raise ValueError(f"Category '{cat}' is not a valid category. Available categories: {all_categories}")

        self._active_categories = categories

        for zone_name, dct in self._polygons.items():
            for array_name, poly in dct.items():
                poly.active_categories = self._active_categories

    def get_values(self) -> dict[str, dict[str, pd.DataFrame]]:
        """ Get the values of all polygons in the zones as a dictionary of pandas DataFrames """

        values = {}
        for zone_name, polygons in self._polygons.items():
            values[zone_name] = {}
            for array_name, polygon in polygons.items():
                values[zone_name][array_name] = polygon.get_values()

        return values

    def values(self, which:Literal['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Area']) -> dict[str, dict[str, pd.Series]]:
        """ Get the values of all polygons in the zones as a dictionary of pandas Series

        :param which: Mean, Std, Median, Sum, Volume, Area
        :return: dictionary with zone names as keys and dictionaries of array names and their values as values
        """

        authorized = ['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Area']
        if which not in authorized:
            raise ValueError(f"Invalid value for 'which'. Must be one of {authorized}.")

        values = {}
        for zone_name, polygons in self._polygons.items():
            values[zone_name] = {}
            for array_name, polygon in polygons.items():
                if array_name not in self._active_arrays:
                    continue
                values[zone_name][array_name] = polygon.values(which)

        return values

    def update_values(self):
        """ Update the polygons values in the zones for all arrays """
        for polygons in self._polygons.values():
            for polygon in polygons.values():
                polygon.update_values()

    def count_strictly_positive(self) -> dict[str, int]:
        """ Count the number of polygons with values greater than zero for each array """
        import concurrent.futures

        counts = {}
        for zone_name, polygons in self._polygons.items():
            counts[zone_name] = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {}
                for array_name, polygon in polygons.items():
                    if array_name not in self._active_arrays:
                        continue
                    futures[array_name] = executor.submit(polygon.count_strictly_positive)
                for array_name, future in futures.items():
                    counts[zone_name][array_name] = future.result()

        return counts

    def count_strictly_positive_as_df(self, merge_zones: bool = False) -> pd.DataFrame:
        """ Count the number of polygons with strictly positive values for each array as a pandas DataFrame

        :return: pandas DataFrame with the counts of strictly positive values for each array in each zone
        """

        counts = self.count_strictly_positive()

        df = pd.DataFrame({'Zone': zone_name, 'Array': array_name, 'Count': count}
                            for zone_name, arrays in counts.items()
                            for array_name, count in arrays.items())
        if merge_zones:
            # Sum counts across zones for each array
            df = df.groupby('Array', as_index=False).sum()
            # remove the 'Zone' column
            df = df.drop(columns=['Zone'])

        return df

    def distribute_zones(self, bins:list[float],
                         operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area']) -> dict[str, dict[str, pd.DataFrame]]:
        """ Distribute the values of each zone in bins for each array

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :return: dictionary with zone names as keys and dictionaries of array names and their distributions as values
        """

        distributions = {}
        for zone_name, polygons in self._polygons.items():
            distributions[zone_name] = {}
            for array_name, polygon in polygons.items():
                if array_name not in self._active_arrays:
                    continue
                distributions[zone_name][array_name] = polygon.distribute_polygons(bins, operator)

        return distributions

    def distribute_zones_as_df(self, bins:list[float],
                               operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'],
                               merge_zones:bool =  False) -> pd.DataFrame:
        """ Distribute the values of each zone in bins for each array as a pandas DataFrame.

        Date are tabulated in a DataFrame with columns 'Zone', 'Array', 'Bin Edges', 'Count'.
        It is more convenient for plotting and analysis.

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :return: pandas DataFrame with the counts of values in each bin for each array in each zone
        """

        distributions = self.distribute_zones(bins, operator)
        df = pd.DataFrame({'Zone': zone_name, 'Array': array, 'Bin Edges': bin, 'Count': count}
                          for zone_name, arrays in distributions.items()
                            for array, bins_counts in arrays.items()
                            for bin, count in zip(bins_counts['Bin Edges'], bins_counts['Counts']))
        if merge_zones:
            # Sum counts across zones for each array
            df = df.groupby(['Array', 'Bin Edges'], as_index=False).sum()
            # remove the 'Zone' column
            df = df.drop(columns=['Zone'])
        return df

    def _values_as_df(self, which:Literal['Mean', 'Std', 'Median', 'Sum', 'Volume', 'Area'],
                      merge_zones:bool = False) -> pd.DataFrame:
        """ Get a full DataFrame with all arrays, zones and values for each polygon.

        :param merge_zones: whether to merge the zones in the DataFrame
        :return: pandas DataFrame with the counts of strictly positive values for each array in each zone
        """
        dct = self.values(which)

        df = pd.DataFrame({'Zone': zone_name, 'Array': array_name, 'Value': value}
                          for zone_name, arrays in dct.items()
                            for array_name, value in arrays.items()
                            for value in value.values)
        if merge_zones:
            # remove the 'Zone' column
            df = df.drop(columns=['Zone'])

        return df

    def plot_count_strictly_positive(self, show:bool = True,
                                 engine:Literal['seaborn', 'plotly'] = 'seaborn',
                                 merge_zones:bool = False):
        """ Plot the count of strictly positive values for each array in each zone

        :param show: whether to show the plot
        :param engine: 'seaborn' or 'plotly'
        """

        if engine == 'seaborn':
            return self._plot_count_strictly_positive_seaborn(show=show, merge_zones=merge_zones)
        elif engine == 'plotly':
            return self._plot_count_strictly_positive_plotly(show=show, merge_zones=merge_zones)

    def save_plot_count_strictly_positive(self, filepath:Path | str,
                                         merge_zones:bool = False,
                                         dpi:int = 300):
        """ Save the plot of the count of strictly positive values for each array in each zone.
        :param filepath: path to the image file (png)
        :param merge_zones: whether to merge the zones in the plot
        :param dpi: resolution of the saved plot
        :return: None
        """
        import matplotlib.pyplot as plt
        # Force Agg backend for saving the plot
        old_back = plt.get_backend()
        plt.switch_backend('Agg')
        fig, ax = self.plot_count_strictly_positive(show=False, merge_zones=merge_zones, engine='seaborn')
        fig.savefig(filepath, bbox_inches='tight', dpi=dpi)
        plt.close(fig)
        # Restore the previous backend
        plt.switch_backend(old_back)

    def _plot_count_strictly_positive_seaborn(self, show:bool = True, merge_zones:bool = False):
        """ Plot the count of strictly positive values for each array in each zone using seaborn

        :param counts: dictionary with zone names as keys, and dictionaries of array names and their counts as values
        :param show: whether to show the plot
        """

        import seaborn as sns
        import matplotlib.pyplot as plt

        df = self.count_strictly_positive_as_df(merge_zones=merge_zones)

        fig, ax = plt.subplots()

        if merge_zones:
            # If merging zones, we only have 'Array' and 'Count' columns
            sns.barplot(x='Array', y='Count', data=df, ax=ax)
        else:
            sns.barplot(x='Array', y='Count', hue='Zone', data=df, ax=ax)

        ax.set_xlabel('Array')
        ax.set_ylabel('Count of strictly positive values')
        ax.set_title('Count of strictly positive values')
        plt.tight_layout()

        if show:
            plt.show()

        return (fig, ax)

    def _plot_count_strictly_positive_plotly(self, show:bool = True, merge_zones:bool = False):
        """ Plot the count of strictly positive values for each array in each zone using plotly

        :param counts: dictionary with zone names as keys, and dictionaries of array names and their counts as values
        :param show: whether to show the plot
        """

        import plotly.express as px

        df = self.count_strictly_positive_as_df(merge_zones=merge_zones)

        if merge_zones:
            fig = px.bar(df, x='Array', y='Count', title='Count of strictly positive values',
                         labels={'Count': 'Count of strictly positive values'})
        else:
            fig = px.bar(df, x='Array', y='Count', color='Zone',
                         title='Count of strictly positive values',
                         labels={'Count': 'Count of strictly positive values'})

        fig.update_layout(xaxis_title='Array', yaxis_title='Count of strictly positive values')

        if show:
            fig.show(renderer='browser')

        return fig

    def plot_distributed_values(self, bins:list[float]= [0., .3, 1.3, -1.],
                                operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'] = 'Median',
                                show:bool = True,
                                engine:Literal['seaborn', 'plotly'] = 'seaborn',
                                merge_zones:bool = False):
        """ Plot the distribution of values in bins for each array in each zone or merged zones.
        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :param show: whether to show the plot
        :param engine: 'seaborn' or 'plotly'
        :param merge_zones: whether to merge the zones in the plot
        """

        if engine == 'seaborn':
            return self._plot_distributed_values_seaborn(bins, operator, show=show, merge_zones=merge_zones)
        elif engine == 'plotly':
            return self._plot_distributed_values_plotly(bins, operator, show=show, merge_zones=merge_zones)
        else:
            raise ValueError(f"Invalid engine '{engine}'. Must be 'seaborn' or 'plotly'.")

    def save_plot_distributed_values(self, filepath:Path | str,
                                     bins:list[float]= [0., .3, 1.3, -1],
                                     operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'] = 'Median',
                                     merge_zones:bool = False,
                                     dpi:int = 300):
        """ Save the plot of the distribution of values in bins for each array in each zone or merged zones.

        :param filepath: path to the image file (png)
        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area
        :param merge_zones: whether to merge the zones in the plot
        :return: None
        """
        import matplotlib.pyplot as plt

        # Force Agg backend for saving the plot
        old_back = plt.get_backend()
        plt.switch_backend('Agg')

        fig, ax = self.plot_distributed_values(bins, operator, show=False, merge_zones=merge_zones, engine='seaborn')

        fig.savefig(filepath, bbox_inches='tight', dpi=dpi)
        plt.close(fig)
        # Restore the previous backend
        plt.switch_backend(old_back)

    def _plot_distributed_values_seaborn(self, bins:list[float],
                                         operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'],
                                         show:bool = True,
                                         merge_zones:bool = False):
        """ Plot the distribution of values in bins for each array in each zone using seaborn

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :param show: whether to show the plot
        :param merge_zones: whether to merge the zones in the plot
        """

        import seaborn as sns
        import matplotlib.pyplot as plt

        # Check which engine is used by matplotlib
        backend = plt.get_backend()
        if backend in ['Agg']:
            show = False

        df = self._values_as_df(operator, merge_zones=merge_zones)

        if bins[-1] == -1:
            bins[-1] = df['Value'].max()

        if merge_zones:
            fig, ax = plt.subplots()
            sns.histplot(df, x='Value', hue='Array', multiple='stack', bins = bins, ax=ax)

            # set ticks
            ax.set_xticks(bins)
            ax.set_xticklabels([f"{b:.2f}" for b in bins])
            ax.set_xlabel(self._xlabel)
            if show:
                plt.show()

            return (fig, ax)
        else:
            # 1 plot per zone
            figs, axs = [], []
            for i, zone_name in enumerate(self._polygons.keys()):
                fig, ax = plt.subplots()
                sns.histplot(df[df['Zone'] == zone_name],
                             x='Value',
                             hue='Array',
                             multiple='stack', bins=bins, ax=ax)

                ax.set_xlabel(self._xlabel)
                ax.set_ylabel('Counts')
                ax.set_title(f'Distribution of Values ({zone_name})')

                # set ticks
                ax.set_xticks(bins)
                ax.set_xticklabels([f"{b:.2f}" for b in bins])
                fig.tight_layout()

                figs.append(fig)
                axs.append(ax)

            if show:
                plt.show()

            return (figs, axs)

    def _get_distributed_values(self,
                                bins:list[float],
                                operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'],
                                merge_zones:bool = False):

        """ Save the distribution of values in bins for each array in each zone as a CSV file.

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area
        :param merge_zones: whether to merge the zones in the plot
        """

        df = self._values_as_df(operator, merge_zones=merge_zones)
        if bins[-1] == -1:
            bins[-1] = df['Value'].max()

        # Bin and count for each array
        result = []
        for array in df['Array'].unique():
            values = df[df['Array'] == array]['Value']
            counts, edges = np.histogram(values, bins=bins)
            for edge, count in zip(edges[:-1], counts):
                result.append({'Array': array, 'Rightmost edge': edge, 'Count': count})

        return pd.DataFrame(result)

    def save_distributed_values(self,
                                filepath:Path | str,
                                bins:list[float],
                                operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'],
                                merge_zones:bool = False):

        """ Save the distribution of values in bins for each array in each zone as a CSV file.

        :param filepath: path to the CSV file
        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area
        :param merge_zones: whether to merge the zones in the plot
        """

        # Ensure CSV extension
        filepath = Path(filepath)
        if filepath.suffix != '.csv':
            filepath = filepath.with_suffix('.csv')

        result = self._get_distributed_values(bins, operator, merge_zones=merge_zones)

        result.to_csv(filepath, index=False)

    def save_distributed_values_table(self,
                                        filepath:Path | str,
                                        bins:list[float],
                                        operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'],
                                        merge_zones:bool = False):
        """ Create a table of the distribution of values in bins for each array in each zone.

        :param filepath: path to the image file (png)
        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area
        :param merge_zones: whether to merge the zones in the plot
        :return: pandas DataFrame with the counts of values in each bin for each array in each zone
        """

        # Ensure PNG extension
        filepath = Path(filepath)
        if filepath.suffix != '.png':
            filepath = filepath.with_suffix('.png')

        results = self._get_distributed_values(bins, operator, merge_zones=merge_zones)

        # Calculer la borne inférieure en décalant la colonne
        results["Bin Lower Edge"] = results.groupby("Array")["Rightmost edge"].shift(1).fillna(0)

        # Créer la chaîne de caractère de l'intervalle
        results[_("Bounds [m]")] = "]" + results["Bin Lower Edge"].map(lambda x: f"{x:.2f}") + "–" + results["Rightmost edge"].map(lambda x: f"{x:.2f}") + "]"
        # Ensure 'Count' is integer
        results['Count'] = results['Count'].astype(int)

        table = results.pivot_table(index=_("Bounds [m]"), columns='Array', values='Count', fill_value=0, sort=False)
        # Force values as integers
        table = table.astype(int)

        table.reset_index(inplace=True)


        # table.columns = pd.MultiIndex.from_tuples([(_('Arrays'),col) for col in table.columns])

        import dataframe_image as dfi

        # Place the column labels (Array) on the same line as the row label (Intervalle)
        styled_df = table.style.format(precision=1) \
            .set_caption(_('Count')) \
            .set_properties(**{
            'text-align': 'center',
            'font-size': '12px',
            'border': '1px solid black',
            }) \
            .set_table_styles([
            {
                'selector': 'th.col_heading.level0',
                'props': [('vertical-align', 'middle')],
            },
            {
                'selector': 'thead th.row_heading.level0',
                'props': [('vertical-align', 'middle')],
            },
            {
                'selector': 'thead th',
                'props': [('text-align', 'center'), ('background-color', '#d9edf7'), ('color', '#31708f')],
            },
            ])
        styled_df = styled_df.hide(axis="index")

        # Export the styled DataFrame as an image

        # Convert to html table image
        dfi.export(styled_df, filename=filepath, dpi = 300)

    def _plot_distributed_values_plotly(self, bins:list[float],
                                        operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'],
                                        show:bool = True,
                                        merge_zones:bool = False):
        """ Plot the distribution of values in bins for each array in each zone using plotly

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :param show: whether to show the plot
        :param merge_zones: whether to merge the zones in the plot
        """

        import plotly.graph_objects as go

        logging.warning("In plotly engine, the bins will be ignored and replaced by 10 automatic bins.")

        df = self._values_as_df(operator, merge_zones=merge_zones)

        if bins[-1] == -1:
            bins[-1] = df['Value'].max()

        if merge_zones:
            fig = go.Figure()
            for array_name in df['Array'].unique():
                fig.add_trace(go.Histogram(x=df[df['Array'] == array_name]['Value'],
                                            name=array_name,
                                            histnorm='',
                                            xbins=dict(start=bins[0], end=bins[-1], size=(bins[-1] - bins[0]) / 10)))
        else:
            fig = go.Figure()
            for zone_name in df['Zone'].unique():
                for array_name in df['Array'].unique():
                    fig.add_trace(go.Histogram(x=df[(df['Zone'] == zone_name) & (df['Array'] == array_name)]['Value'],
                                                name=f"{zone_name} - {array_name}",
                                                histnorm='',
                                                xbins=dict(start=bins[0], end=bins[-1], size=(bins[-1] - bins[0]) / 10)))

        if show:
            fig.show(renderer='browser')

        return fig

    def _plot_distributed_areas_seaborn(self, bins:list[float],
                                         operator:Literal['Mean', 'Median', 'Sum', 'Volume', 'Area'],
                                         show:bool = True,
                                         merge_zones:bool = False):
        """ Plot the distribution of values in bins for each array in each zone using seaborn

        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area'
        :param show: whether to show the plot
        :param merge_zones: whether to merge the zones in the plot
        """

        import seaborn as sns
        import matplotlib.pyplot as plt

        df = self._values_as_df(operator, merge_zones=merge_zones)
        df_area = self._values_as_df('Area', merge_zones=merge_zones)

        # # Multiply the values by the area to get the weighted distribution
        # df['Value'] = df['Value'] * df_area['Value']

        if bins[-1] == -1:
            if df['Value'].max() > bins[-2]:
                bins[-1] = df['Value'].max()
            else:
                bins[-1] = bins[-2] + (bins[-2] - bins[-3])

        if merge_zones:
            fig, ax = plt.subplots()
            sns.histplot(df, x='Value', hue='Array',
                         multiple='stack', bins = bins, ax=ax,
                         weights= df_area['Value'])

            # set ticks
            ax.set_xticks(bins)
            ax.set_xticklabels([f"{b:.2f}" for b in bins])
            ax.set_xlabel(self._xlabel)
            ax.set_ylabel('Area [m²]')
            if show:
                plt.show()

            return (fig, ax)
        else:
            # 1 plot per zone
            figs, axs = [], []
            for i, zone_name in enumerate(self._polygons.keys()):
                fig, ax = plt.subplots()
                sns.histplot(df[df['Zone'] == zone_name],
                             x='Value',
                             hue='Array',
                             multiple='stack', bins=bins, ax=ax,
                             weights=df_area[df_area['Zone'] == zone_name]['Value'])

                ax.set_xlabel(self._xlabel)
                ax.set_ylabel('Area [m²]')
                ax.set_title(f'Distribution of Values ({zone_name})')

                # set ticks
                ax.set_xticks(bins)
                ax.set_xticklabels([f"{b:.2f}" for b in bins])
                fig.tight_layout()

                figs.append(fig)
                axs.append(ax)

            if show:
                plt.show()

            return (figs, axs)

class Building_Waterdepth_analysis(Arrays_analysis_zones):
    """ Class for water depth analysis of multiple arrays based on a Zones instance.

    This class is designed to analyze water depth data from multiple arrays and zones.
    It inherits from Arrays_analysis_zones and provides additional methods specific to water depth analysis.
    """

    def __init__(self, arrays:dict[str, WolfArray],
                 zones:Zones | Path | str,
                 buffer_size:float = 0.0,
                 merge_zones:bool = False,
                 thershold_area:float = 0.0):
        """ Initialize the class with a list of WolfArray and a Zones instance.

        :param arrays: dictionary of WolfArray instances to analyze
        :param zones: Zones instance or path to a zones file
        :param buffer_size: size of the buffer around the zones (default is 0.0)
        :param merge_zones: whether to merge all zones into a single zone (default is False)
        :param thershold_area: minimum area of the polygon to consider (default is 0.0)
        :raises ValueError: if the arrays are empty or have different shapes
        :raises FileNotFoundError: if the zones file does not exist
        """

        if isinstance(zones, (Path, str)):

            zones = Path(zones)
            if not zones.exists():
                raise FileNotFoundError(f"Zones file {zones} does not exist.")

            [xmin, xmax], [ymin, ymax] = arrays[next(iter(arrays))].get_bounds()
            logging.info(f"Using bounds from the first array: {xmin}, {xmax}, {ymin}, {ymax}")
            bbox = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)])
            logging.info(f"Creating zones from {zones} with bounding box {bbox}")
            zones = Zones(zones, bbox=bbox)
            logging.info(f"Zones loaded from {zones}")

        if merge_zones:
            # copy all vectors in an unique zone
            newz = Zones(idx='all')
            merged_zone = zone(name='all')
            newz.add_zone(merged_zone, forceparent= True)

            for z in zones.myzones:
                if z.used:
                    merged_zone.myvectors.extend(z.myvectors)

            # Rename vectors adding the index position inside the zone
            for i, v in enumerate(merged_zone.myvectors):
                v.myname = f"{v.myname}___{i}"

            zones = newz

        for z in zones.myzones:
            if z.used:
                for v in z.myvectors:
                    if v.area < thershold_area:
                        logging.dbg(f"Polygon {v.myname} has an area of {v.area} which is below the threshold of {thershold_area}. It will be ignored.")
                        v.used = False

        super().__init__(arrays, zones, buffer_size)

        self._xlabel = _('Water Depth [m]')

    def plot_distributed_areas(self, bins = [0, 0.3, 1.3, -1],
                                operator = 'Median',
                                show = True,
                                engine = 'seaborn',
                                merge_zones = False):

        return super()._plot_distributed_areas_seaborn(bins, operator, show=show, merge_zones=merge_zones)

    def save_plot_distributed_areas(self, filepath,
                                    bins = [0, 0.3, 1.3, -1],
                                    operator = 'Median',
                                    merge_zones = False,
                                    dpi = 300):
        """ Save the plot of the distribution of areas in bins for each array in each zone or merged zones.
        :param filepath: path to the image file (png)
        :param bins: list of bin edges
        :param operator: 'Mean', 'Median', 'Sum', 'Volume', 'Area
        :param merge_zones: whether to merge the zones in the plot
        :param dpi: resolution of the saved plot
        :return: None
        """

        import matplotlib.pyplot as plt
        # Force Agg backend for saving the plot
        old_back = plt.get_backend()
        plt.switch_backend('Agg')
        fig, ax = self.plot_distributed_areas(bins, operator, show=False, merge_zones=merge_zones, engine='seaborn')
        fig.savefig(filepath, bbox_inches='tight', dpi=dpi)
        plt.close(fig)
        # Restore the previous backend
        plt.switch_backend(old_back)


class Slope_analysis:
    """ Class for slope analysis of in an array based on a trace vector.

    This class allows to select cells inside a polygon or a buffer around a trace vector
    and compute the slope of the dike. The slope is computed as the difference in elevation
    between the trace and the cell divided by the distance to the trace.

    The slope is computed for each cell inside the polygon or buffer and accessed in a Pandas Dataframe.

    Plots of the slope distribution can be generated using seaborn or plotly.

    The class is designed to be used with the WolfArray class and the vector class from the PyVertexvectors module.
    """

    def __init__(self, wa:WolfArray, trace:vector):

        self._wa = wa
        self._trace = trace

        self._selection_poly = None
        self._buffer_size = 0.0

        self._selected_cells = None
        self._slopes = None

    @property
    def slopes(self) -> pd.DataFrame:
        """ Get the slopes as a pandas DataFrame """

        if self._slopes is None:
            self.compute_slopes()

        if self._slopes is None:
            raise ValueError("No slopes computed. Please call compute_slopes() first.")

        return pd.DataFrame(self._slopes, columns=['Slope [m/m]'])

    def select_cells(self, mode:Literal['polygon', 'buffer'] = 'polygon', **kwargs):
        """ Select the cells inside the trace """

        if mode == 'polygon':
            if 'polygon' in kwargs:
                self._selection_poly = kwargs['polygon']
                self._select_cells_polygon(self._selection_poly)
            else:
                raise ValueError("No polygon provided. Please provide a polygon to select cells.")
        elif mode == 'buffer':
            if 'buffer' in kwargs:
                self._buffer_size = kwargs['buffer']
                self._select_cells_buffer(self._buffer_size)
            else:
                raise ValueError("No buffer size provided. Please provide a buffer size to select cells.")
        else:
            raise ValueError("Invalid mode. Please use 'polygon' or 'buffer'.")

    def _select_cells_buffer(self, buffer_size:float = 0.0):
        """ Select the cells inside the buffer of the trace """

        self._buffer_size = buffer_size
        self._selection_poly = self._trace.buffer(self._buffer_size, inplace=False)
        self._select_cells_polygon(self._selection_poly)

    def _select_cells_polygon(self, selection_poly:vector):
        """ Select the cells inside the polygon """

        self._selection_poly = selection_poly
        self._selected_cells = self._wa.get_xy_inside_polygon(self._selection_poly)

    def compute_slopes(self):
        """ Get the slope of the dike """

        if self._selected_cells is None:
            self.select_cells()
        if self._selected_cells is None:
            raise ValueError("No cells selected. Please call select_cells() first.")

        trace_ls = self._trace.linestring

        def compute_cell_slope(curxy):
            i, j = self._wa.get_ij_from_xy(curxy[0], curxy[1])
            pt = Point(curxy[0], curxy[1])
            distance_to_trace = trace_ls.distance(pt)
            elevation_on_trace = trace_ls.interpolate(trace_ls.project(pt, normalized=True), normalized=True).z
            if distance_to_trace == 0.0:
                return 0.0
            if elevation_on_trace == -99999.0:
                return 0.0

            return (elevation_on_trace - self._wa.array[i, j]) / distance_to_trace

        self._slopes = [compute_cell_slope(curxy) for curxy in self._selected_cells]

    def plot_slopes(self, show:bool = True, bins:int = 100,
                    engine:Literal['seaborn', 'plotly'] = 'seaborn'):
        """ Plot a histogram of the slopes """

        if engine == 'seaborn':
            return self.plot_slopes_seaborn(show=show, bins=bins)
        elif engine == 'plotly':
            return self.plot_slopes_plotly(show=show, bins=bins)

    def plot_slopes_seaborn(self, bins:int = 100, show:bool = True):
        """ Plot a histogram of the slopes """

        import seaborn as sns
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        sns.histplot(self.slopes, bins=bins,
                     kde=True, ax=ax,
                     stat="density")

        ax.set_xlabel('Slope [m/m]')
        ax.set_ylabel('Frequency')
        ax.set_title('Slope distribution')

        if show:
            plt.show()

        return (fig, ax)

    def plot_slopes_plotly(self, bins:int = 100, show:bool = True):
        """ Plot a histogram of the slopes """

        import plotly.express as px

        fig = px.histogram(self.slopes, x='Slope [m/m]',
                           nbins=bins, title='Slope distribution',
                           histnorm='probability density')

        fig.update_layout(xaxis_title='Slope [m/m]', yaxis_title='Frequency')

        if show:
            fig.show(renderer='browser')

        return fig