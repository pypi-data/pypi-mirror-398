import os
from packaging import version
from enum import Enum
from pathlib import Path
import logging
import wx
import matplotlib.pyplot as plt
from tqdm import tqdm
from typing import Literal
from shapely.geometry import Point, LineString, Polygon

from .. import __version__
from ..PyTranslate import _
from ..PyGui import MapManager, WolfMapViewer, draw_type, Zones, zone, vector, cloud_vertices, wolfvertex
from .reporting import RapidReport
from ..pypolygons_scen import Polygons_Analyze, stored_values_unk, operators, stored_values_coords, stored_values_pos
from ..multiprojects import MultiProjects, project_type, Project


class Directory_Analysis(Enum):
    PROJECTS = "projets"
    REPORTS = "rapports"
    VECTORS = "vecteurs"
    CLOUDS = "nuages_de_points"
    IMAGES = "images"
    CACHE = "cache"

def get_lines_from_ax(ax:plt.Axes) -> list[LineString]:
    """ Get the lines from a Matplotlib Axes object.

    :param ax: The Matplotlib Axes object.
    :return: A list of LineString objects representing the lines in the Axes.
    """

    lines = []
    for line in ax.get_lines():
        xdata, ydata = line.get_xdata(), line.get_ydata()
        if len(xdata) > 1 and len(ydata) > 1:
            lines.append(LineString(zip(xdata, ydata)))
    return lines

def get_labels_from_ax(ax:plt.Axes) -> list[str]:
    """ Get the labels from a Matplotlib Axes object.

    :param ax: The Matplotlib Axes object.
    :return: A list of labels from the Axes.
    """
    labels = []
    for line in ax.get_lines():
        label = line.get_label()
        if label and label not in labels:
            labels.append(label)
    return labels

def set_lines_as_black(ax:plt.Axes, label:str | list[str] = None) -> None:
    """ Set the line with the specified label to black in a Matplotlib Axes object.

    :param ax: The Matplotlib Axes object.
    :param label: The label of the line to set to black.
    """
    for line in ax.get_lines():
        if label is None or line.get_label() == label or (isinstance(label, list) and line.get_label() in label):
            line.set_color('black')
            line.set_linestyle('-')
            line.set_linewidth(1.5)
            line.set_marker('')
            line.set_markersize(0)
            line.set_alpha(1.0)
            logging.info(f"Line with label '{line.get_label()}' set to black.")
        else:
            logging.warning(f"No line found with label '{label}'.")

def change_style_in_ax(ax:plt.Axes, styles:dict[str, dict]) -> None:
    """ Change the style of lines in a Matplotlib Axes object.

    Available style properties:
    - color: The color of the line.
    - linestyle: The style of the line (e.g., '-', '--', '-.', ':').
    - linewidth: The width of the line.
    - marker: The marker style (e.g., 'o', 'x', '^').
    - markersize: The size of the marker.
    - alpha: The transparency of the line (0.0 to 1.0).
    - label: The label for the line in the legend.

    This function will iterate through all lines in the Axes and apply the styles based on the provided dictionary.

    :param ax: The Matplotlib Axes object.
    :param styles: A dict of style where key is the label and value is a tuple with style properties.
    :return: None
    """
    for line in ax.get_lines():
        label = line.get_label()
        if label in styles:
            style = styles[label]
            if 'color' in style:
                line.set_color(style['color'])
            if 'linestyle' in style:
                line.set_linestyle(style['linestyle'])
            if 'linewidth' in style:
                line.set_linewidth(style['linewidth'])
            if 'marker' in style:
                line.set_marker(style['marker'])
            if 'markersize' in style:
                line.set_markersize(style['markersize'])
            if 'alpha' in style:
                line.set_alpha(style['alpha'])
            if 'label' in style:
                line.set_label(style['label'])
            # Log the style change
            logging.info(f"Style changed for label '{label}': {style}")

        else:
            logging.debug(f"No style found for label '{label}'.")

def _sanitize_scenario_name(scenario_name: str | tuple[str,str]) -> str:
    """ Sanitize the scenario name to ensure it is a string.
    This function will strip whitespace and ensure the name is a string.
    :param name: The scenario name to sanitize.
    :return: A sanitized string representing the scenario name.
    """
    if isinstance(scenario_name, str):
        scenario_name = scenario_name.strip()

    elif isinstance(scenario_name, tuple):
        if len(scenario_name) != 2:
            logging.error("Scenario name tuple must contain exactly two elements.")
            raise ValueError("Scenario name tuple must contain exactly two elements.")

        scenario_name = scenario_name[0].strip()

    scenario_name = scenario_name.replace('\\', '_').replace('/', '_')  # Replace slashes with underscores

    return scenario_name

def list_directories(directory: Path) -> list[str]:
    """ List directories in a given path. """
    if not directory.exists():
        logging.error(f"Directory {directory} does not exist.")
        return []
    return [d.name for d in directory.iterdir() if d.is_dir()]

def create_a_report(title, author) -> RapidReport:
    """ Create a RapidReport instance.

    :param title: The title of the report.
    :param author: The author of the report.
    :return: An instance of RapidReport.
    """
    try:
        return RapidReport(main_title=title, author=author)
    except Exception as e:
        logging.error(f"Error creating RapidReport: {e}")
        raise ImportError("Could not create RapidReport instance. Ensure that the RapidReport is properly initialized.")

def create_a_wolf_viewer() -> WolfMapViewer:
    """ Create a WolfMapViewer instance.

    :return: An instance of WolfMapViewer.
    """

    # check if a wx.App instance already exists
    if not wx.GetApp():
        logging.error(_("You need to create a wx.App instance before creating a WolfMapViewer or to call '%gui wx' in your Jupyter Notebook."))
        return None
    else:
        logging.debug("Using existing wx.App instance.")

    try:
        maps = MapManager()
        return maps.get_mapviewer()
    except Exception as e:
        logging.error(f"Error creating WolfMapViewer: {e}")
        raise ImportError("Could not create WolfMapViewer instance. Ensure that the MapManager is properly initialized.")

def find_scenario_directory(base_directory: Path | str, scenario_name: str) -> Path | None:
    """ Find the directory of a specific scenario within the base directory and subdirectories.

    :param base_directory: The base directory where the scenarios are located.
    :param scenario_name: The name of the scenario to find.
    :return: The path to the scenario directory if found, None otherwise.
    """
    base_path = Path(base_directory)

    scen_path = base_path / scenario_name
    # Check if the scenario_name is a direct subdirectory of the base directory
    if scen_path.is_dir():
        return scen_path

    # # search if scenario_name is a directory in the base directory or its subdirectories
    # for dirpath, dirnames, filenames in os.walk(base_path):
    #     if scenario_name in dirnames:
    #         return Path(dirpath) / scenario_name

    # # Search in subdirectories of the base directory
    # for subdir in base_path.iterdir():
    #     if subdir.is_dir() and subdir.name == scenario_name:
    #         return subdir
    return None

def get_scenarios_directories(base_directory: Path | str, scenario_names:list[str]) -> dict:
    """ Get the directories of all scenarios within the base directory.

    :param base_directory: The base directory where the scenarios are located.
    :param scenario_names: A list of scenario names to find.
    :return: A list of paths to the scenario directories.
    """
    base_path = Path(base_directory)
    ret = {_sanitize_scenario_name(scenario_name) : find_scenario_directory(base_path, scenario_name) for scenario_name in scenario_names}

    # check if None is in the list and logging it
    for scenario_name, scenario_path in ret.items():
        if scenario_path is None:
            logging.warning(f"Scenario '{scenario_name}' not found in {base_path}.")
        else:
            logging.info(f"Found scenario '{scenario_name}' at {scenario_path}.")

    return ret

def check_if_scenario_exists(base_directory: Path | str, scenario_name: str) -> bool:
    """ Check if a specific scenario exists within the base directory.

    :param base_directory: The base directory where the scenarios are located.
    :param scenario_name: The name of the scenario to check.
    :return: True if the scenario exists, False otherwise.
    """
    scenario_path = find_scenario_directory(base_directory, scenario_name)
    if scenario_path is None:
        logging.error(f"Scenario '{scenario_name}' not found in {base_directory}.")
        return False
    else:
        logging.info(f"Scenario '{scenario_name}' found at {scenario_path}.")
        return True

def check_if_scenarios_exist(base_directory: Path | str, scenario_names: list[str]) -> bool:
    """ Check if all specified scenarios exist within the base directory.

    :param base_directory: The base directory where the scenarios are located.
    :param scenario_names: A list of scenario names to check.
    :return: True if all scenarios exist, False otherwise.
    """
    all_exist = True
    for scenario_name in scenario_names:
        if not check_if_scenario_exists(base_directory, scenario_name):
            all_exist = False
    return all_exist

def check_analysis_directories(base_directory: Path | str) -> bool:
    """ Check if the necessary directories for analysis exist.

    :param base_directory: The base directory where the analysis directories are located.
    :return: True if all directories exist, False otherwise.
    """
    ret = True
    base_path = Path(base_directory)
    for directory in Directory_Analysis:
        dir_path = base_path / directory.value
        if not dir_path.exists():
            logging.error(f"Directory {dir_path} does not exist.")
            logging.error(f"Please create the directory {dir_path} manually or call 'create_analysis_directories'.")
            ret = False
        else:
            logging.info(f"Directory {dir_path} exists.")
    return ret

def create_analysis_directories(base_directory: Path | str) -> str:
    """ Create the necessary directories for analysis if they do not exist.

    :param base_directory: The base directory where the analysis directories will be created.
    :return: True if directories were created or already exist, False if an error occurred.
    """
    try:
        base_path = Path(base_directory)
        for directory in Directory_Analysis:
            dir_path = base_path / directory.value
            dir_path.mkdir(parents=True, exist_ok=True)
        return _(f"Directories created successfully in {base_path}.")
    except Exception as e:
        return _(f"Error creating directories: {e}")

def get_directories_as_dict(base_directory: Path | str) -> dict:
    """ Get the paths of the analysis directories.

    :param base_directory: The base directory where the analysis directories are located.
    :return: A dictionary with the paths of the analysis directories.
    """
    base_path = Path(base_directory)
    create_analysis_directories(base_path)  # Ensure directories exist
    return {
        Directory_Analysis.PROJECTS: base_path / Directory_Analysis.PROJECTS.value,
        Directory_Analysis.REPORTS: base_path / Directory_Analysis.REPORTS.value,
        Directory_Analysis.VECTORS: base_path / Directory_Analysis.VECTORS.value,
        Directory_Analysis.CLOUDS: base_path / Directory_Analysis.CLOUDS.value,
        Directory_Analysis.IMAGES: base_path / Directory_Analysis.IMAGES.value,
        Directory_Analysis.CACHE: base_path / Directory_Analysis.CACHE.value,
    }

def get_directories_as_list(base_directory: Path | str) -> list:
    """ Get the paths of the analysis directories as a list.

    :param base_directory: The base directory where the analysis directories are located.
    :return: A list with the paths of the analysis directories. Ordered as per Directory_Analysis enum.
    """
    directories = get_directories_as_dict(base_directory)
    return list(directories.values())

def _check_version(min_version: str) -> bool:
    """
    Check if the current version is greater than or equal to the minimum version.

    Args:
        min_version (str): The minimum required version.
        current_version (str): The current version to check against.

    Returns:
        bool: True if the current version is greater than or equal to the minimum version, False otherwise.
    """
    return version.parse(__version__) >= version.parse(min_version)

def check_available_version_on_pypi() -> str:
    """
    Check the latest available version of the package on PyPI.

    Returns:
        str: The latest version available on PyPI.
    """
    import requests
    from packaging import version

    url = "https://pypi.org/pypi/wolfhece/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        latest_version = data['info']['version']
        return latest_version
    else:
        raise Exception(f"Failed to fetch version information from PyPI. Status code: {response.status_code}")

def can_upgrade_wolfhece() -> bool:
    """
    Check if the current version can be upgraded to the minimum required version.

    Args:
        min_version (str): The minimum required version.

    Returns:
        bool: True if the current version can be upgraded, False otherwise.
    """
    latest_version = check_available_version_on_pypi()
    return version.parse(latest_version) >= version.parse(__version__)

def check_version(min_version: str) -> bool:
    """
    Check if the current version is greater than or equal to the minimum version.

    Args:
        min_version (str): The minimum required version.

    Returns:
        bool: True if the current version is greater than or equal to the minimum version, False otherwise.
    """
    try:
        # Permet de tester la version accessible via le PATH
        if _check_version(min_version):
            logging.info(f"Version de wolfhece : {min_version} ou supérieure est installée.")
        else:
            logging.error(f"Version de wolfhece : {min_version} ou supérieure n'est pas installée.")
            logging.info(f"Version available on Pypi {check_available_version_on_pypi()}")
            logging.info(f"Can I upgrade? {can_upgrade_wolfhece()}")
            raise ImportError("Version de wolfhece insuffisante.")
    except:
        logging.error(f"Erreur lors de la vérification de la version de wolfhece. Assurez-vous que wolfhece est installé et accessible dans le PATH.")
        logging.info(f"Version available on Pypi {check_available_version_on_pypi()}")
        raise ImportError("Erreur lors de la vérification de la version de wolfhece.")

class Analysis_Scenarios():

    def __init__(self, base_directory: Path | str, storage_directory: Path | str = None, name:str = ''):

        # Default figure size for plots
        self._fig_size = (20, 10)

        # Name of the analysis scenarios instance
        self.name = name.strip() if name else 'Analysis_Scenarios'

        # Base directory for the analysis scenarios
        # Must contains the directories 'projets', 'rapports', 'vecteurs', 'nuages_de_points', 'images' and 'cache'
        self.base_directory = Path(base_directory)

        # Storage directory for the analysis scenarios - Default is the base directory
        self.storage_directory = storage_directory if storage_directory is not None else self.base_directory

        # Check if the base directory exists and contains the necessary directories
        self.check_directories()
        # Fill the directories attribute with the paths of the analysis directories
        self.directories = get_directories_as_dict(self.base_directory)

        # Initialize the scenarios directories
        self.scenarios_directories:dict[str:Path]
        self.scenarios_directories = {}
        # List of scenario names
        self.scenarios = []

        self.current_scenario = None
        self._return_periods = []

        # RapidReport associated with the analysis scenarios
        self.report:RapidReport = None
        self._report_name = 'analysis_report.docx'
        self._report_saved_once = False

        # Map viewer for the analysis scenarios
        self.mapviewer:WolfMapViewer = None

        # Name of the WMS service
        self._background_images:str = None

        # Polygons associated with the analysis scenarios
        self._polygons:dict[str, Polygons_Analyze] = {}

        self._reference_polygon:Polygons_Analyze = None

        # Modifications associated with the analysis scenarios
        self._modifications = {}

        # MultiProjects associated with the analysis scenarios.
        # One project contains multiple suimulations.
        self._multiprojects = None

        # Landmarks and measures associated with the analysis
        self._landmarks:Zones = None
        self._landmarks_s_label = []

        self._measures:dict[str, Zones] = {}
        self._measures_zones:dict[str, list[str]] = {}
        self._projected_measures:dict[tuple[str], list[vector, dict]] = {}

        self._cloud:list[tuple[float, float, str]] = []  # List of tuples (s, z, label) for point clouds

        self._images = {}

        # Zoom (smin, smax, zmin, zmax) for the analysis
        self._zoom:dict[str, tuple[float,float,float,float]] = {}

        logging.info(f"Analysis directories initialized: {self.directories}")

    @property
    def fig_size(self) -> tuple[float]:
        """ Return the default figure size for plots.

        :return: A tuple (width, height) representing the default figure size.
        """
        return self._fig_size

    @fig_size.setter
    def fig_size(self, size:tuple[float]) -> None:
        """ Set the default figure size for plots.

        :param size: A tuple (width, height) representing the default figure size.
        """
        if not isinstance(size, tuple) or len(size) != 2:
            logging.error("Default figure size must be a tuple of (width, height).")
            raise ValueError("Default figure size must be a tuple of (width, height).")
        self._fig_size = size
        logging.info(f"Default figure size set to {self._fig_size}.")

    def add_zoom(self, label:str, bounds:tuple[float]) -> None:
        """ Add a zoom level to the analysis.

        :param label: The label for the zoom level.
        :param bounds: A tuple (xmin, xmax, ymin, ymax) representing the zoom bounds.
        """
        if label in self._zoom:
            logging.warning(f"Zoom level '{label}' already exists. Overwriting.")

        self._zoom[label] = bounds
        logging.info(f"Zoom memory '{label}' added with bounds {bounds}.")

    def add_zoom_from_XY(self, label:str, xy1:tuple[float], xy2:tuple[float], zmin:float, zmax:float) -> None:
        """ Add a zoom level to the analysis from X and Y coordinates.

        :param label: The label for the zoom level.
        :param xy1: A tuple (x1, y1) representing the first point.
        :param xy2: A tuple (x2, y2) representing the second point.
        :param zmin: The minimum zoom level.
        :param zmax: The maximum zoom level.
        """
        if self.reference_polygon is None:
            logging.error("No reference polygon set for the analysis. Please set a reference polygon first.")
            raise ValueError("No reference polygon set for the analysis. Please set a reference polygon first.")

        ls = self.reference_polygon.riverbed.linestring

        x1,y1 = xy1
        s1 = ls.project(Point(x1, y1))
        x2,y2 = xy2
        s2 = ls.project(Point(x2, y2))

        if s1 < s2:
            self.add_zoom(label, (s1, s2, zmin, zmax))
        else:
            self.add_zoom(label, (s2, s1, zmin, zmax))

        logging.info(f"Zoom memory '{label}' added with bounds ({s1}, {s2}, {zmin}, {zmax}).")

    def get_zoom(self, label:str) -> tuple[float]:
        """ Get the zoom level bounds for a specific label.

        :param label: The label for the zoom level.
        :return: A tuple (xmin, xmax, ymin, ymax) representing the zoom bounds.
        """
        if label not in self._zoom:
            logging.error(f"Zoom level '{label}' does not exist.")
            return (0., self.reference_polygon.riverbed.length2D, 0., 300.)

        return self._zoom[label]

    @property
    def measures(self) -> dict:
        """ Return the measures used in the analysis.

        :return: An instance of Zones or None if not set.
        """
        return self._measures

    def add_cloud(self, cloud:cloud_vertices | list[tuple[float, float, str]] | str = None, label:str = '') -> None:
        """ Add a cloud of points to the analysis.

        :param cloud: A cloud of points as a cloud_vertices instance or a list of tuples (s, z, label).
        """

        if isinstance(cloud, str):
            # If cloud is a string, assume it's a path to a cloud_vertices file
            cloud_path = Path(cloud)
            if not cloud_path.exists():
                # Search in the clouds directory
                cloud_path = self.directories[Directory_Analysis.CLOUDS] / cloud_path

            if not cloud_path.exists():
                logging.error(f"Cloud file '{cloud}' does not exist.")
                raise FileNotFoundError(f"Cloud file '{cloud}' does not exist.")

            cloud = cloud_vertices(fname=cloud_path, header=True)
            self.add_cloud(cloud, label)

        elif isinstance(cloud, cloud_vertices):
            sz_cloud:cloud_vertices
            sz_cloud = cloud.projectontrace(self.reference_polygon.riverbed)
            self._cloud += [(curvert['vertex'].x, curvert['vertex'].y, label) for curvert in sz_cloud.myvertices.values()]
            logging.info(f"Cloud added with {len(cloud.myvertices)} points.")

        elif isinstance(cloud, list) and all(isinstance(pt, tuple) and len(pt) == 3 for pt in cloud):
            self._cloud.extend(cloud)
            logging.info(f"Cloud added with {len(cloud)} points.")
        else:
            logging.error("Invalid cloud format. Must be a cloud_vertices instance or a list of tuples (s, z, label).")
            raise ValueError("Invalid cloud format. Must be a cloud_vertices instance or a list of tuples (s, z, label).")

    def add_cloud_point(self, s: float, z: float, label: str = None) -> None:
        """ Add a point to the cloud in the analysis.

        :param s: The s-coordinate of the point.
        :param z: The z-coordinate of the point.
        :param label: An optional label for the point.
        """
        if self.reference_polygon is None:
            logging.error("No reference polygon set for the analysis. Please set a reference polygon first.")
            raise ValueError("No reference polygon set for the analysis. Please set a reference polygon first.")

        if label is None:
            label = f"Point {len(self._cloud) + 1}"

        self._cloud.append((s, z, label))
        logging.info(f"Point added to cloud: ({s}, {z}, '{label}')")

    def add_cloud_point_XY(self, x: float, y: float, z: float = None, label: str = None) -> None:
        """ Add a point to the cloud in the analysis from X and Y coordinates.

        :param x: The X coordinate of the point.
        :param y: The Y coordinate of the point.
        :param z: The Z coordinate of the point (optional).
        :param label: An optional label for the point.
        """
        if self.reference_polygon is None:
            logging.error("No reference polygon set for the analysis. Please set a reference polygon first.")
            raise ValueError("No reference polygon set for the analysis. Please set a reference polygon first.")

        point = Point(x, y)
        ls = self.reference_polygon.riverbed.linestring
        s = ls.project(point)

        if label is None:
            label = f"Point {len(self._cloud) + 1}"

        self._cloud.append((s, z, label))
        logging.info(f"Point added to cloud: ({s}, {z}, '{label}')")

    def add_measures(self, measures:Zones | str | Path, zones:list[str] = None, style:dict = None, force_all_vectors:bool = False) -> None:
        """ Add measures to the analysis.

        :param measures: A Zones instance or a path to a vector file containing the measures.
        :param zones: A list of zone names to include in the analysis. If None, all zones in the measures will be used.
        :param style: A dictionary containing style properties for the measures.
                      Available properties: 'color', 'linestyle', 'linewidth', 'marker', 'markersize', 'alpha'.
        :param force_all_vectors: If True, all vectors in the zones will be projected on the riverbed, even if they are not used.
        """

        if isinstance(measures, Zones):
            key = measures.idx
            self._measures[key] = measures
        elif isinstance(measures, (str, Path)):
            if not os.path.exists(measures):

                # Search in the vectors directory
                measures = self.directories[Directory_Analysis.VECTORS] / measures
                if not os.path.exists(measures):
                    logging.error(f"Measures file '{measures}' does not exist.")
                    raise FileNotFoundError(f"Measures file '{measures}' does not exist.")

            key = Path(measures).stem
            cur_measure = self._measures[key] = Zones(filename= measures)

        # check if each zone exists in the measures
        if zones is not None:
            if not isinstance(zones, list):
                logging.error("Zones must be a list of strings.")
                raise ValueError("Zones must be a list of strings.")

            for zone in zones:
                if cur_measure[zone] is None:
                    logging.error(f"Zone '{zone}' not found in the measures.")
                    raise ValueError(f"Zone '{zone}' not found in the measures.")

        self._measures_zones[key] = zones if zones is not None else [curz.myname for curz in cur_measure.myzones]

        for zone_name in self._measures_zones[key]:
            curz = cur_measure[zone_name]
            for vec in curz.myvectors:
                if vec.used or force_all_vectors:
                    # create a local key for the projected measures
                    lockey = (key, zone_name, vec.myname)
                    self._projected_measures[lockey] = [vec.projectontrace(self.reference_polygon.riverbed), style]

        logging.info(f"Measures added to the analysis: {self._measures[key].idx}")

    def get_landmarks_labels(self) -> list[str]:
        """ Get the names of the landmarks in the analysis.

        :return: A list of names of the landmarks.
        """
        if self._landmarks_s_label is None:
            logging.warning("No landmarks have been added to the analysis.")
            return []

        return [mark[2] for mark in self._landmarks_s_label]

    @property
    def reference_polygon(self) -> Polygons_Analyze | None:
        """ Return the reference polygon used in the analysis.

        :return: An instance of Polygons_Analyze or None if not set.
        """
        return self._reference_polygon

    @property
    def landmarks(self) -> Zones | None:
        """ Return the landmarks used in the analysis.

        :return: An instance of Zones or None if not set.
        """
        return self._landmarks

    def add_landmarks(self, landmarks:Zones | str | Path) -> None:
        """ Add landmarks to the analysis.

        :param landmarks: A Zones instance or a path to a vector file containing the landmarks.
        """

        if isinstance(landmarks, Zones):
            self._landmarks = landmarks
        elif isinstance(landmarks, (str, Path)):
            if not os.path.exists(landmarks):

                # Search in the vectors directory
                landmarks = self.directories[Directory_Analysis.VECTORS] / landmarks
                if not os.path.exists(landmarks):
                    logging.error(f"Landmarks file '{landmarks}' does not exist.")
                    raise FileNotFoundError(f"Landmarks file '{landmarks}' does not exist.")

            self._landmarks = Zones(filename= landmarks)

        if self.reference_polygon is not None:
            # Compute the distance to the reference polygon
            ls = self.reference_polygon.riverbed.linestring
            self._landmarks_s_label = [(ls.project(Point((curvec.myvertices[0].x+curvec.myvertices[-1].x)/2., (curvec.myvertices[0].y+curvec.myvertices[-1].y)/2.)), None, curvec.myname) for curvec in self._landmarks.myzones[0].myvectors if curvec.used]

        logging.info(f"Landmarks added to the analysis: {self._landmarks.idx}")

    def add_landmark_from_XY(self, x: float, y: float, label: str, z:float = None) -> None:
        """ Add a landmark to the analysis from X and Y coordinates.

        :param x: The X coordinate of the landmark.
        :param y: The Y coordinate of the landmark.
        :param name: The name of the landmark.
        :param z: The Z coordinate of the landmark (optional).
        """

        if self.reference_polygon is None:
            logging.error("No reference polygon set for the analysis. Please set a reference polygon first.")
            raise ValueError("No reference polygon set for the analysis. Please set a reference polygon first.")

        point = Point(x, y)
        ls = self.reference_polygon.riverbed.linestring
        self._landmarks_s_label.append((ls.project(point), z, label))
        logging.info(f"Landmark '{label}' added at coordinates ({x}, {y}).")

    def update_landmark(self, label: str, s_xy:float |tuple[float] = None, z: float = None) -> None:
        """ Update a landmark in the analysis.

        :param label: The label of the landmark to update.
        :param s_xy: The s-coordinate or a tuple (s, xy) to update the landmark's position.
        :param z: The z-coordinate to update the landmark's elevation (optional).
        """

        if self._landmarks is None:
            logging.error("No landmarks have been added to the analysis.")
            raise ValueError("No landmarks have been added to the analysis.")

        if label not in self.get_landmarks_labels():
            logging.error(f"Landmark '{label}' not found in the analysis.")
            raise ValueError(f"Landmark '{label}' not found in the analysis.")

        for i, mark in enumerate(self._landmarks_s_label):
            if mark[2] == label:

                z = mark[1] if mark[1] is not None else z

                if s_xy is not None:
                    if isinstance(s_xy, tuple):
                        if len(s_xy) != 2:
                            logging.error("s_xy must be a tuple of (s, xy) or a single float value.")
                            raise ValueError("s_xy must be a tuple of (s, xy) or a single float value.")
                        x, y = s_xy
                        pt = Point(x, y)
                        ls = self.reference_polygon.riverbed.linestring
                        s_xy = ls.project(pt)

                    if isinstance(s_xy, float):
                        if s_xy < 0 or s_xy > self.reference_polygon.riverbed.length:
                            logging.error(f"s_xy value {s_xy} is out of bounds for the reference polygon.")
                            raise ValueError(f"s_xy value {s_xy} is out of bounds for the reference polygon.")

                    self._landmarks_s_label[i] = (s_xy, z, label)

    def plot_cloud(self, ax: plt.Axes, bounds:tuple[float]) -> plt.Axes:
        """ Trace the cloud of points on an axis Matplotlib

        :param ax: axe Matplotlib
        :param bounds: tuple (xmin, xmax, ymin, ymax) for the plot limits
        :return: The Matplotlib Axes object with the cloud plotted.
        """
        xmin, xmax, ymin, ymax = bounds

        used_cloud = [(s, z, label) for s, z, label in self._cloud if s >= xmin and s <= xmax]
        i=0
        for s, z, label in used_cloud:
            ax.scatter(s, z, label = label if i == 0 else "", c='black', marker='o', s=10, alpha=0.5)
            i += 1

        return ax

    def plot_measures(self, ax:plt.Axes, bounds:tuple[float], style:dict = None) -> plt.Axes:
        """ Trace les mesures sur un axe Matplotlib

        :param ax: axe Matplotlib
        :param bounds: tuple (xmin, xmax, ymin, ymax) for the plot limits
        :param style: Optional style dictionary for the measures. Available properties:
                      - 'color': The color of the line.
                      - 'linestyle': The style of the line (e.g., '-', '--', '-.', ':').

        :return: The Matplotlib Axes object with the measures plotted.
        """
        xmin, xmax, ymin, ymax = bounds
        i=0
        for key, measure in self._projected_measures.items():
            vec = measure[0]
            style = measure[1]
            sz = vec.xy
            s = sz[:,0]
            z = sz[:,1]

            color = 'grey'
            linestyle = '--'

            if style is not None:
                color = style['color'] if 'color' in style else 'grey'
                linestyle = style['linestyle'] if 'linestyle' in style else '--'

            portion = (s > xmin) #& (s < xmax)
            if i==0:
                ax.plot(s[portion], z[portion], color=color, linestyle=linestyle, label = _('Measures') if i == 0 else "")
            else:
                ax.plot(s[portion], z[portion], color=color, linestyle=linestyle)
            i+=1

    def plot_landmarks(self, ax:plt.Axes, bounds:tuple[float], style:dict = None) -> plt.Axes:
        """ Trace les repères sur un axe Matplotlib

        :param ax: axe Matplotlib
        :param bounds: tuple (xmin, xmax, ymin, ymax) for the plot limits
        :param style: Optional style dictionary for the landmarks.
        """

        xmin, xmax, ymin, ymax = bounds

        i=0
        for mark in self._landmarks_s_label:
            s, z, label = mark

            if style is None:
                color = 'black'
                linestyle = '--'
                linewidth = 0.7
                marker = 'x'
            else:
                color = style['color'] if 'color' in style else 'black'
                linestyle = style['linestyle'] if 'linestyle' in style else '--'
                linewidth = style['linewidth'] if 'linewidth' in style else 0.7
                marker = style['marker'] if 'marker' in style else 'x'

            if s < xmin or s > xmax:
                continue
            if z is None:
                ax.vlines(s, ymin, ymax, color=color, linewidth=linewidth, linestyle=linestyle, label=_('Landmarks') if i == 1 else "")
                ax.text(s, ymin, label, rotation=30)
            else:
                ax.scatter(s, z, color=color, marker=marker, label=_('Landmarks') if i == 1 else "")
            i += 1

        return ax

    def plot_waterlines(self, scenario:str | tuple[str, str] | list[str] | list[tuple[str, str]],
                        bounds:tuple[float] | str,
                        operator:operators = operators.MEDIAN,
                        plot_annex:bool = True,
                        save:bool = False,
                        figsize:tuple[float] = None) -> tuple[plt.Figure, plt.Axes]:
        """ Plot the waterlines for a specific scenario.

        :param scenario: The name of the scenario to plot waterlines for or a list of scenarios for comparison.
        :param bounds: A tuple (xmin, xmax, ymin, ymax) representing the zoom bounds or a string label for a zoom level.
        :param operator: The operator to apply on the waterlines.
        :param save: If True, save the plot as an image file.
        :param figsize: A tuple (width, height) representing the size of the figure. If None, uses the default figure size.
        :param plot_annex: If True, plot the cloud of points, measures, and landmarks.
        :return: A tuple (fig, ax) where fig is the matplotlib Figure and ax is the matplotlib Axes object.
        """

        if isinstance(bounds, str):
            # If bounds is a string, assume it's a label for a zoom level
            bounds = self.get_zoom(bounds)
            if bounds is None:
                logging.error(f"Zoom level '{bounds}' does not exist.")
                raise ValueError(f"Zoom level '{bounds}' does not exist.")
        elif isinstance(bounds, tuple):
            if len(bounds) != 4:
                logging.error("Bounds must be a tuple of (xmin, xmax, ymin, ymax).")
                raise ValueError("Bounds must be a tuple of (xmin, xmax, ymin, ymax).")
        xmin, xmax, ymin, ymax = bounds

        if isinstance(scenario, (str, tuple)):

            scenario = _sanitize_scenario_name(scenario)

            fig,ax = plt.subplots(1,1)

            self.get_polygon(scenario).plot_waterline((fig,ax), which_group=scenario, operator=operator.MEDIAN)

            filename = self.directories[Directory_Analysis.IMAGES] / f"{self.name}_{scenario}_{str(xmin)}_{str(xmax)}_waterlines.png"

        elif isinstance(scenario, list):
            # We want to compare multiple scenarios
            if len(scenario) < 2:
                logging.error("At least two scenarios are required to compare waterlines.")
                raise ValueError("At least two scenarios are required to compare waterlines.")

            ref, sim = scenario[0]

            if isinstance(ref, tuple):
                full_name = ref[1]
            ref = _sanitize_scenario_name(ref)

            # plot topography / bed elevation for the reference scenario
            s, z = self.get_polygon(ref).get_s_values(stored_values_unk.TOPOGRAPHY, which_group=ref, operator=operator, which_sim=sim)
            fig, ax = plt.subplots(1, 1)
            ax.plot(s, z, label=f"{full_name} - {_('Bathymetry')}", color='black', linestyle='-', linewidth=2)

            # plot water surface elevation for the reference scenario
            s, z = self.get_polygon(ref).get_s_values(stored_values_unk.WATERLEVEL, which_group=ref, operator=operator, which_sim=sim)
            ax.plot(s, z, label=f"{full_name} - {sim}", color='blue', linestyle='-', linewidth=2)

            # plot topography / bed elevation for the simulation scenarios
            for cur_scenario in scenario[1:]:
                scen_name, sim_name = cur_scenario

                if isinstance(scen_name, tuple):
                    full_name = scen_name[1]
                scen_name = _sanitize_scenario_name(scen_name)
                s, z = self.get_polygon(scen_name).get_s_values(stored_values_unk.TOPOGRAPHY, which_group=scen_name, operator=operator, which_sim=sim_name)
                ax.plot(s, z, label=f"{full_name} - {_('Bathymetry')}", linestyle='--', linewidth=1.5)

            # plot water surface elevation for the simulation scenarios
            for cur_scenario in scenario[1:]:
                scen_name, sim_name = cur_scenario
                if isinstance(scen_name, tuple):
                    full_name = scen_name[1]
                scen_name = _sanitize_scenario_name(scen_name)
                s, z = self.get_polygon(scen_name).get_s_values(stored_values_unk.WATERLEVEL, which_group=scen_name, operator=operator, which_sim=sim_name)
                ax.plot(s, z, label=f"{full_name} - {sim_name}", linestyle='--', linewidth=1.5)

            filename = self.directories[Directory_Analysis.IMAGES] / f"{self.name}_{ref}_{str(xmin)}_{str(xmax)}_waterlines_comparison.png"

        if figsize is not None:
            if not isinstance(figsize, tuple) or len(figsize) != 2:
                logging.error("Figure size must be a tuple of (width, height).")
                raise ValueError("Figure size must be a tuple of (width, height).")
            fig.set_size_inches(figsize)
        else:
            fig.set_size_inches(self.fig_size[0], self.fig_size[1])  # Use the default figure size

        ax.legend()
        #zoomA
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.grid()

        if plot_annex:
            # Plot the cloud of points
            self.plot_cloud(ax, bounds)

            # Plot the measures
            self.plot_measures(ax, bounds)

            # Plot the landmarks
            self.plot_landmarks(ax, bounds)

        fig.tight_layout()

        if save:
            self.save_image(filename, fig=fig, format='png')
            logging.info(f"Waterlines plot saved as {filename}")

        return fig, ax

    def plot_waterheads(self, scenario:str | tuple[str, str],
                        bounds:tuple[float] | str,
                        operator:operators = operators.MEDIAN,
                        plot_annex:bool = True,
                        save:bool = False,
                        figsize:tuple[float] = None) -> tuple[plt.Figure, plt.Axes]:
        """ Plot the heads for a specific scenario.

        :param scenario: The name of the scenario to plot heads for or a list of scenarios for comparison.
        :param bounds: A tuple (xmin, xmax, ymin, ymax) representing the zoom bounds or a string label for a zoom level.
        :param operator: The operator to apply on the heads.
        :param plot_annex: If True, plot the cloud of points, measures, and landmarks.
        :param save: If True, save the plot as an image file.
        :param figsize: A tuple (width, height) representing the figure size. If None, use the default figure size.
        :return: A tuple (fig, ax) representing the figure and axes of the plot
        """
        if isinstance(bounds, str):
            # If bounds is a string, assume it's a label for a zoom level
            bounds = self.get_zoom(bounds)
            if bounds is None:
                logging.error(f"Zoom level '{bounds}' does not exist.")
                raise ValueError(f"Zoom level '{bounds}' does not exist.")
        elif isinstance(bounds, tuple):
            if len(bounds) != 4:
                logging.error("Bounds must be a tuple of (xmin, xmax, ymin, ymax).")
                raise ValueError("Bounds must be a tuple of (xmin, xmax, ymin, ymax).")
        xmin, xmax, ymin, ymax = bounds

        if isinstance(scenario, (str, tuple)):

            scenario = _sanitize_scenario_name(scenario)
            fig, ax = plt.subplots(1, 1)
            self.get_polygon(scenario).plot_waterhead((fig, ax), which_group=scenario, operator=operator.MEDIAN)
            filename = self.directories[Directory_Analysis.IMAGES] / f"{self.name}_{scenario}_{str(xmin)}_{str(xmax)}_heads.png"
        elif isinstance(scenario, list):

            ref, sim = scenario[0]
            ref = _sanitize_scenario_name(ref)
            fig, ax = plt.subplots(1, 1)
            # plot heads for the reference scenario
            s, z = self.get_polygon(ref).get_s_values(stored_values_unk.HEAD, which_group=ref, operator=operator, which_sim=sim)
            ax.plot(s, z, label=f"{ref} - {stored_values_unk.HEAD.value}", color='blue', linestyle='-', linewidth=2)
            # plot heads for the simulation scenarios
            for cur_scenario in scenario[1:]:
                scen_name, sim_name = cur_scenario
                scen_name = _sanitize_scenario_name(scen_name)
                s, z = self.get_polygon(scen_name).get_s_values(stored_values_unk.HEAD, which_group=scen_name, operator=operator, which_sim=sim_name)
                ax.plot(s, z, label=f"{scen_name} - {sim_name}", linestyle='--', linewidth=1.5)
            filename = self.directories[Directory_Analysis.IMAGES] / f"{self.name}_{ref}_{str(xmin)}_{str(xmax)}_heads_comparison.png"

        if figsize is not None:
            if not isinstance(figsize, tuple) or len(figsize) != 2:
                logging.error("Figure size must be a tuple of (width, height).")
                raise ValueError("Figure size must be a tuple of (width, height).")
            fig.set_size_inches(figsize)
        else:
            fig.set_size_inches(self.fig_size[0], self.fig_size[1])  # Use the default figure size

        ax.legend()
        #zoomA
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.grid()
        if plot_annex:
            # Plot the cloud of points
            self.plot_cloud(ax, bounds)

            # Plot the measures
            self.plot_measures(ax, bounds)

            # Plot the landmarks
            self.plot_landmarks(ax, bounds)
        fig.tight_layout()
        if save:
            self.save_image(filename, fig=fig, format='png')
            logging.info(f"Heads plot saved as {filename}")

        return fig, ax

    def plot_Froude(self, scenario:str | tuple[str, str] | list[str] | list[tuple[str, str]],
                        bounds:tuple[float] | str,
                        operator:operators = operators.MEDIAN,
                        plot_annex:bool = True,
                        save:bool = False,
                        figsize:tuple[float] = None) -> tuple[plt.Figure, plt.Axes]:
        """ Plot the Froude for a specific scenario.

        :param scenario: The name of the scenario to plot waterlines for or a list of scenarios for comparison.
        :param bounds: A tuple (xmin, xmax, ymin, ymax) representing the zoom bounds or a string label for a zoom level.
        :param operator: The operator to apply on the waterlines.
        :param save: If True, save the plot as an image file.
        :param figsize: A tuple (width, height) representing the figure size. If None, use the default figure size.
        :param plot_annex: If True, plot the cloud of points, measures, and landmarks.
        :return: A tuple (fig, ax) representing the figure and axes of the plot
        """

        if isinstance(bounds, str):
            # If bounds is a string, assume it's a label for a zoom level
            bounds = self.get_zoom(bounds)
            if bounds is None:
                logging.error(f"Zoom level '{bounds}' does not exist.")
                raise ValueError(f"Zoom level '{bounds}' does not exist.")
        elif isinstance(bounds, tuple):
            if len(bounds) != 4:
                logging.error("Bounds must be a tuple of (xmin, xmax, ymin, ymax).")
                raise ValueError("Bounds must be a tuple of (xmin, xmax, ymin, ymax).")
        xmin, xmax, ymin, ymax = bounds

        if isinstance(scenario, (str, tuple)):

            if isinstance(scenario, tuple):
                full_name = scenario[1]
            scenario = _sanitize_scenario_name(scenario)

            fig,ax = plt.subplots(1,1)
            # plot Froude number for the scenario

            for sim in self.list_sims_in_polygons(scenario):
                # plot Froude number for the reference scenario
                s, z = self.get_polygon(scenario).get_s_values(stored_values_unk.FROUDE, which_group=scenario, operator=operator, which_sim=sim)
                ax.plot(s, z, label=f"{sim}", linestyle='-', linewidth=1.5)

            filename = self.directories[Directory_Analysis.IMAGES] / f"{self.name}_{scenario}_{str(xmin)}_{str(xmax)}_Froude.png"

        elif isinstance(scenario, list):

            # We want to compare multiple scenarios
            if len(scenario) < 2:
                logging.error("At least two scenarios are required to compare waterlines.")
                raise ValueError("At least two scenarios are required to compare waterlines.")

            fig,ax = plt.subplots(1,1)

            ref, sim = scenario[0]

            if isinstance(ref, tuple):
                full_name = ref[1]
            ref = _sanitize_scenario_name(ref)

            # plot water surface elevation for the reference scenario
            s, z = self.get_polygon(ref).get_s_values(stored_values_unk.FROUDE, which_group=ref, operator=operator, which_sim=sim)
            ax.plot(s, z, label=f"{full_name} - {sim}", color='blue', linestyle='-', linewidth=2)

            # plot water surface elevation for the simulation scenarios
            for cur_scenario in scenario[1:]:
                scen_name, sim_name = cur_scenario
                if isinstance(scen_name, tuple):
                    full_name = scen_name[1]
                scen_name = _sanitize_scenario_name(scen_name)
                s, z = self.get_polygon(scen_name).get_s_values(stored_values_unk.FROUDE, which_group=scen_name, operator=operator, which_sim=sim_name)
                ax.plot(s, z, label=f"{full_name} - {sim_name}", linestyle='--', linewidth=1.5)

            filename = self.directories[Directory_Analysis.IMAGES] / f"{self.name}_{ref}_{str(xmin)}_{str(xmax)}_Froude_comparison.png"

        if figsize is not None:
            if not isinstance(figsize, tuple) or len(figsize) != 2:
                logging.error("Figure size must be a tuple of (width, height).")
                raise ValueError("Figure size must be a tuple of (width, height).")
            fig.set_size_inches(figsize)
        else:
            fig.set_size_inches(self.fig_size[0], self.fig_size[1])  # Use the default figure size

        ax.legend()
        #zoomA
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(0, 2.)
        ax.plot([xmin, xmax], [1, 1], color='black', linestyle='--', label=_('Froude = 1'))
        ax.grid()

        if plot_annex:
            # Plot the landmarks
            self.plot_landmarks(ax, (bounds[0], bounds[1], 0, 2.))

        fig.suptitle(_('Froude Number'), fontsize=16)
        fig.tight_layout()

        if save:
            self.save_image(filename, fig=fig, format='png')
            logging.info(f"Waterlines plot saved as {filename}")

        return fig, ax

    def save_image(self, filename: str, fig: plt.Figure = None, dpi: int = 300, format:Literal['png', 'pdf', 'svg'] = 'png') -> None:
        """ Save the current figure as an image file.

        :param filename: The name of the file to save the image to.
        :param fig: The figure to save. If None, uses the current active figure.
        :param dpi: The resolution of the saved image in dots per inch.
        :param format: The format of the saved image (png, pdf, svg). Default is 'png'.
        """
        if fig is None:
            fig = plt.gcf()

        if not format in ['png', 'pdf', 'svg']:
            logging.error(f"Format '{format}' is not supported. Supported formats are 'png', 'pdf', and 'svg'.")
            raise ValueError(f"Format '{format}' is not supported. Supported formats are 'png', 'pdf', and 'svg'.")

        fig.savefig(filename, dpi=dpi, format=format)

        self._images[filename] = filename

        logging.info(f"Image saved as {filename} with dpi={dpi} and format={format}.")

    def export_values_as(self, scenario: str | tuple[str, str] = None,
                         simulation_key:list[str] = None,
                         which_values:list[stored_values_unk] = [stored_values_unk.TOPOGRAPHY,
                                                                 stored_values_unk.WATERDEPTH,
                                                                 stored_values_unk.WATERLEVEL,
                                                                 stored_values_unk.HEAD,
                                                                 stored_values_coords.X,
                                                                 stored_values_coords.Y],
                         operator:operators = operators.MEDIAN,
                         filename: str = None,
                         format:Literal['xlsx', 'csv'] = 'xlsx') -> None:
        """ Export values from polygons for a specific scenario to a file.

        :param scenario: The name of the scenario to export values for. If None, exports values for all scenarios.
        :param simulation_key: The key of the simulation to export values for. If None, exports values for all simulations.
        :param which_values: The type of values to export from the polygons.
        :param operator: The operator to apply on the values extracted from the polygons.
        :param filename: The name of the file to export values to. If None, a default name will be used.
        :param format: The format of the file to export values to (csv or xlsx). Default is 'xlsx'.
        """

        if not format in ['xlsx', 'csv']:
            logging.error(f"Format '{format}' is not supported. Supported formats are 'xlsx' and 'csv'.")
            raise ValueError(f"Format '{format}' is not supported. Supported formats are 'xlsx' and 'csv'.")

        scenario = _sanitize_scenario_name(scenario)

        if filename is None:
            filename = f"{self.name}_{scenario}_values"
        else:
            #remove suffix if it exists
            filename = filename.removesuffix(f'.{format}') if filename.endswith(f'.{format}') else filename

        if scenario is None:
            # Export values for all scenarios
            for key in self._polygons.keys():
                self.export_values_as(key, simulation_key, which_values, operator, filename=f"{self.name}_{key}_values.{format}", format=format)
            return

        if scenario not in self._polygons:
            logging.error(f"Scenario '{scenario}' not found in the analysis.")
            raise ValueError(f"Scenario '{scenario}' not found in the analysis.")


        if simulation_key is None:
            # Export values for all simulations
            simulation_key = self.list_sims_in_polygons(scenario)
            if not simulation_key:
                logging.error(f"No simulations found for scenario '{scenario}'.")
                raise ValueError(f"No simulations found for scenario '{scenario}'.")

            poly = self.get_polygon(scenario)
            for sim_key in simulation_key:
                poly.export_as((self.directories[Directory_Analysis.CACHE] / (filename + '_' + sim_key)).with_suffix(f'.{format}'), which_values, which_group=scenario, operator=operator, which_sim=sim_key)
                logging.info(f"Values exported for simulation '{sim_key}' in scenario '{scenario}' to {filename}_{sim_key}.{format}")

        elif isinstance(simulation_key, list):
            # Export values for a list of simulations
            for sim_key in simulation_key:
                if not sim_key in self.list_sims_in_polygons(scenario):
                    logging.error(f"Simulation key '{sim_key}' not found in the scenario '{scenario}'.")
                    raise ValueError(f"Simulation key '{sim_key}' not found in the scenario '{scenario}'.")

            poly = self.get_polygon(scenario)
            for sim_key in simulation_key:
                poly.export_as((self.directories[Directory_Analysis.CACHE] / (filename + '_' + sim_key)).with_suffix(f'.{format}'), which_values, which_group=scenario, operator=operator, which_sim=sim_key)
                logging.info(f"Values exported for simulation '{sim_key}' in scenario '{scenario}' to {filename}_{sim_key}.{format}")

        else:
            if not simulation_key in self.list_sims_in_polygons(scenario):
                logging.error(f"Simulation key '{simulation_key}' not found in the scenario '{scenario}'.")
                raise ValueError(f"Simulation key '{simulation_key}' not found in the scenario '{scenario}'.")

            self.get_polygon(scenario).export_as((self.directories[Directory_Analysis.CACHE] / (filename + '_' + simulation_key)).with_suffix(f'.{format}'), which_values, which_group= scenario, operator= operator, which_sim=simulation_key)
            logging.info(f"Values exported for simulation '{simulation_key}' in scenario '{scenario}' to {filename}_{simulation_key}.{format}")

    def get_values_from_polygons(self, scenario: str | tuple[str, str] = None, which_value:stored_values_unk = stored_values_unk.HEAD, which_operator:operators = operators.MEDIAN) -> dict:
        """ Get values from polygons for a specific scenario.

        :param scenario: The name of the scenario to get values for. If None, gets values for all scenarios.
        :param which_value: The type of value to extract from the polygons.
        :param which_operator: The operator to apply on the values extracted from the polygons.
        :return: A dictionary with the values extracted from the polygons.
        """

        scenario = _sanitize_scenario_name(scenario)

        if scenario is None:
            # Get values for all scenarios
            return {key: self.get_values_from_polygons(key, which_value, which_operator) for key in self._polygons.keys()}

        if scenario not in self._polygons:
            logging.error(f"Scenario '{scenario}' not found in the analysis.")
            raise ValueError(f"Scenario '{scenario}' not found in the analysis.")

        poly = self.get_polygon(scenario)
        return poly.get_river_values_op(which_value, which_group=scenario, operator= which_operator)

    def list_groups_in_polygons(self, scenario: str | tuple[str, str]) -> list[str]:
        """ List the groups in the polygons used in the analysis.
        :param scenario: The name of the scenario to list groups for. If None, lists groups for all scenarios.
        """
        scenario = _sanitize_scenario_name(scenario)

        return self._polygons[scenario][0].list_groups() if scenario in self._polygons else []

    def list_sims_in_polygons(self, scenario: str | tuple[str, str]) -> list[str]:
        """ List the simulations in the polygons used in the analysis.
        :param scenario: The name of the scenario to list simulations for. If None, lists simulations for all scenarios.
        """
        scenario = _sanitize_scenario_name(scenario)

        if scenario not in self._polygons:
            logging.error(f"Scenario '{scenario}' not found in the analysis.")
            raise ValueError(f"Scenario '{scenario}' not found in the analysis.")

        ret = []
        dct= self._polygons[scenario][0].list_sims()
        for key, value in dct.items():
            ret.extend(value)
        return ret

    def list_sims_in_all_polygons(self) -> dict:
        """ List the simulations in all polygons used in the analysis.

        :return: A dictionary where keys are scenario names and values are lists of simulations.
        """
        ret = {}
        # Append the simulations for each scenario
        for scenario, polygons in self._polygons.items():
            if not isinstance(polygons[0], Polygons_Analyze):
                logging.error(f"Polygons for scenario '{scenario}' are not instances of Polygons_Analyze.")
                raise TypeError(f"Polygons for scenario '{scenario}' are not instances of Polygons_Analyze.")

            dct = polygons[0].list_sims()
            for key, value in dct.items():
                ret[key] = value
        return ret

    def cache_data_to_disk(self) -> None:
        """ Enable or disable caching of extracted data from polygons.

        :param cache: If True, enable caching. If False, disable caching.
        """
        for key, polygons in self._polygons.items():
            if not isinstance(polygons[0], Polygons_Analyze):
                logging.error(f"Polygons for scenario '{key}' are not instances of Polygons_Analyze.")
                raise TypeError(f"Polygons for scenario '{key}' are not instances of Polygons_Analyze.")

            if isinstance(key, tuple):
                key = '_'.join(key)

            key = key.replace('\\', '_')  # Replace backslashes with underscores for file naming

            logging.info(f"Caching data for scenario '{key}' to disk.")
            polygons[0].cache_data((self.directories[Directory_Analysis.CACHE] / (self.name + '_' + key)).with_suffix('.json'))

        logging.info("Data caching to disk completed.")

    def load_cached_data(self) -> None:
        """ Load cached data from polygons if available.

        This will load the cached data from the polygons used in the analysis.
        """
        for key, polygons in self._polygons.items():
            if not isinstance(polygons[0], Polygons_Analyze):
                logging.error(f"Polygons for scenario '{key}' are not instances of Polygons_Analyze.")
                raise TypeError(f"Polygons for scenario '{key}' are not instances of Polygons_Analyze.")

            if isinstance(key, tuple):
                key = '_'.join(key)

            key = key.replace('\\', '_')  # Replace backslashes with underscores for file naming

            cache_file = (self.directories[Directory_Analysis.CACHE] / (self.name + '_' + key)).with_suffix('.json')
            logging.info(f"Loading cached data from {cache_file}")
            polygons[0].load_data(cache_file)

        logging.info("Cached data loaded successfully.")

    def extract_data_from_polygons(self) -> dict:
        """ Extract data from polygons used in the analysis.

        Apply on all projects in the analysis.
        """

        if len(self._polygons) == 0:
            logging.error("No polygons have been set for the analysis.")
            raise ValueError("No polygons have been set for the analysis.")
        if self._multiprojects is None:
            logging.error("MultiProjects instance is not created. Please create a MultiProjects instance first.")
            raise ValueError("MultiProjects instance is not created. Please create a MultiProjects instance first.")

        if not isinstance(self._multiprojects, MultiProjects):
            logging.error("The _multiprojects attribute is not an instance of MultiProjects.")
            raise TypeError("The _multiprojects attribute is not an instance of MultiProjects.")

        # Polygon keys must be the same as the project names in the MultiProjects instance
        for key, polygons in self._polygons.items():
            sims = self._multiprojects.get_simulations_dict(key)
            if len(sims) == 0:
                logging.error(f"No simulations found for scenario '{key}'. Please load simulations first.")
                continue
            logging.info(f"Extracting data from polygons for scenario '{key}' with {len(sims[list(sims.keys())[0]])} simulations.")
            polygons[0].find_values_inside_parts(sims)
        logging.info("Data extraction from polygons completed.")

    def load_results_for_all(self, epsilon:float = 0.001, verbose:bool = True):
        """ Load results for all projects in the analysis.

        :param epsilon: The tolerance for considering wet cells as wet.
        """

        if self._multiprojects is None:
            logging.error("MultiProjects instance is not created. Please create a MultiProjects instance first.")
            raise ValueError("MultiProjects instance is not created. Please create a MultiProjects instance first.")

        self._multiprojects.load_simulations(epsilon= epsilon, verbose= verbose)

    def add_projects(self, projects:list[tuple[str | tuple, str]]) -> None:
        """ Create a MultiProjects instance for managing all scenario results.
        """
        self._multiprojects = MultiProjects(self.directories[Directory_Analysis.PROJECTS])

        # check if projects exist in the projects directory
        if not isinstance(projects, list):
            logging.error("Projects must be a list of tuples (scenario_name, project_name).")
            raise ValueError("Projects must be a list of tuples (scenario_name, project_name).")

        if not all(isinstance(project, tuple) and len(project) == 2 for project in projects):
            logging.error("Each project must be a tuple of (scenario_name, project_name).")
            raise ValueError("Each project must be a tuple of (scenario_name, project_name).")

        if not all(isinstance(scenario, (str, tuple)) and isinstance(project, str) for scenario, project in projects):
            logging.error("Both scenario and project names must be strings.")
            raise ValueError("Both scenario and project names must be strings.")

        # check if project exists in the projects directory
        err = False
        for scenario, project in projects:
            project_path = self.directories[Directory_Analysis.PROJECTS] / project
            if not project_path.exists():
                logging.error(f"Project '{project}' does not exist in the projects directory.")
                err = True
        if err:
            logging.error("One or more projects do not exist in the projects directory.")
            raise FileNotFoundError("One or more projects do not exist in the projects directory.")

        for scenario, project in projects:
            self._multiprojects.add(project, _sanitize_scenario_name(scenario), project_type.WOLF2D)

        logging.info("MultiProjects instance created successfully.")

    @property
    def viewer(self) -> WolfMapViewer | None:
        """ Return the map viewer instance. """
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
        return self.mapviewer

    def autoscale(self) -> None:
        """ Autoscale the map viewer to fit the current bounds. """
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        self.mapviewer.Autoscale()

    @property
    def viewer_bounds(self, rounded:bool = True, decimal:int = 0) -> list:
        """ Return the current bounds of the map viewer.

        :return: A list with [xmin, ymin, xmax, ymax] representing the current bounds.
        """
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        xmin, ymin, xmax, ymax = self.mapviewer.get_canvas_bounds()
        if rounded:
            xmin = round(xmin, decimal)
            ymin = round(ymin, decimal)
            xmax = round(xmax, decimal)
            ymax = round(ymax, decimal)
            return xmin, ymin, xmax, ymax
        else:
            return self.mapviewer.get_canvas_bounds()

    def add_vector2viewer(self, vectorfile: str, id: str) -> None:
        """ Add a vector to the map viewer.

        :param vectorfile: The filename of the vector file to be added.
        :param id: The id of the vector to be displayed in the map viewer.
        """
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        if not isinstance(vectorfile, str):
            logging.error("Vector file must be a string representing the filename.")
            raise ValueError("Vector file must be a string representing the filename.")

        if not isinstance(id, str):
            logging.error("Vector id must be a string.")
            raise ValueError("Vector id must be a string.")

        # check if vectorfile exists
        vector_path = self.directories[Directory_Analysis.VECTORS] / vectorfile
        if not vector_path.exists():
            logging.error(f"Vector file '{vectorfile}' does not exist in the vectors directory.")
            raise FileNotFoundError(f"Vector file '{vectorfile}' does not exist in the vectors directory.")

        # check oif id exists
        ids = self.mapviewer.get_list_keys(drawing_type=draw_type.VECTORS, checked_state=None)
        if id in ids:
            logging.warning(f"Vector with id '{id}' already exists in the map viewer. Choose another id.")
            raise ValueError(f"Vector with id '{id}' already exists in the map viewer. Choose another id.")

        self.mapviewer.add_object('vector', filename = str(self.directories[Directory_Analysis.VECTORS] / vectorfile), id=id)

    def get_polygon(self, scenario: str | tuple[str,str] = None) -> Polygons_Analyze:
        """ Get the polygons for a specific scenario.

        :param scenario: The name of the scenario to get polygons for. If None, returns polygons for all scenarios.
        :return: An instance of Polygons_Analyze.
        """
        scenario = _sanitize_scenario_name(scenario)

        if scenario not in self._polygons:
            logging.error(f"Scenario '{scenario}' not found in the analysis.")
            raise ValueError(f"Scenario '{scenario}' not found in the analysis.")

        return self._polygons[scenario][0]

    def cache_xys(self, scenario: str | tuple[str,str] = None) -> None:
        """ Cache the x and y coordinates of the polygons for a specific scenario.

        :param scenario: The name of the scenario to cache x and y coordinates for. If None, caches for all scenarios.
        """
        if scenario is None:
            # Cache xys for all scenarios
            for key in self._polygons.keys():
                self.cache_xys(key)
            logging.info("Cached x and y coordinates for all scenarios.")
            return

        scenario = _sanitize_scenario_name(scenario)

        if scenario not in self._polygons:
            logging.error(f"Scenario '{scenario}' not found in the analysis.")
            raise ValueError(f"Scenario '{scenario}' not found in the analysis.")

        poly = self.get_polygon(scenario)
        poly.save_xy_s_tofile(self.directories[Directory_Analysis.CACHE] / f"{scenario}_xy_s.csv")
        logging.info(f"Cached x and y coordinates for scenario '{scenario}' to file f'{scenario}_xy_s.csv'.")

    def get_polygons_informations(self, scenario: str | tuple[str,str] = None) -> dict:
        """ Get the information of the polygons for a specific scenario.

        :param scenario: The name of the scenario to get polygons information for. If None, returns information for all scenarios.
        :return: A dictionary with the polygons information.
        """

        if scenario is None:
            # Return information for all scenarios
            return {key: self.get_polygons_informations(key) for key in self._polygons.keys()}
        else:
            scenario = _sanitize_scenario_name(scenario)

        if scenario not in self._polygons:
            logging.error(f"Scenario '{scenario}' not found in the analysis.")
            raise ValueError(f"Scenario '{scenario}' not found in the analysis.")

        poly = self.get_polygon(scenario).myzones[-1]
        return {_("Number of polygons"): poly.nbvectors,
                _("Spacing") : f"{poly.myvectors[1].myvertices[0].z - poly.myvectors[0].myvertices[0].z:.3f} m",}

    @property
    def polygons(self) -> dict:
        """ Return the polygons used in the analysis. """
        return [(key, poly[1]) for key, poly in self._polygons.items()]

    @polygons.setter
    def polygons(self, polygons: list[tuple[str,str]]) -> None:
        """ Set the polygons for the analysis.

        :param polygons: A list of tuples where each tuple contains the scenario name and the polygon name.
        """

        if not isinstance(polygons, list):
            logging.error("Polygons must be a list.")
            raise ValueError("Polygons must be a list.")

        if not all(isinstance(polygon, tuple) and len(polygon) == 2 for polygon in polygons):
            logging.error("Each polygon must be a tuple of (scenario_name, polygon_name).")
            raise ValueError("Each polygon must be a tuple of (scenario_name, polygon_name).")

        # check if all vector files exist
        for polygon in polygons:
            scenario_name, polygon_name = polygon
            scenario_name = _sanitize_scenario_name(scenario_name)

            if scenario_name not in self.scenarios_directories:
                logging.error(f"Scenario '{scenario_name}' not found in the analysis.")
                raise ValueError(f"Scenario '{scenario_name}' not found in the analysis.")

            vector_path = self.directories[Directory_Analysis.VECTORS] / f"{polygon_name}"
            if not vector_path.exists():
                logging.error(f"Polygon vector file '{vector_path}' does not exist.")
                raise ValueError(f"Polygon vector file '{vector_path}' does not exist.")

        self._polygons = {_sanitize_scenario_name(polygon[0]): (Polygons_Analyze(self.directories[Directory_Analysis.VECTORS] / polygon[1]), polygon[1]) for polygon in polygons}
        logging.info(f"Polygons set.")

    def set_reference_riverbed(self, scenario: str | tuple) -> None:
        """ Set the reference riverbed for the analysis.

        :param scenario_name: The name of the scenario to set the reference riverbed for.
        """
        scenario = _sanitize_scenario_name(scenario)

        if scenario not in self._polygons.keys():
            logging.error(f"Scenario '{scenario}' not found in the analysis.")
            raise ValueError(f"Scenario '{scenario}' not found in the analysis.")

        self._reference_polygon = self._polygons[scenario][0]

        for key, polygons in self._polygons.items():
            if key != scenario:
                polygons[0].compute_distance(self._reference_polygon.riverbed.linestring)
        logging.info(f"Reference riverbed set for scenarios from '{scenario}'.")

    @property
    def return_periods(self) -> list:
        """ Return the list of return periods for the analysis. """
        return self._return_periods

    @return_periods.setter
    def return_periods(self, periods: list[str]) -> None:
        """ Set the return periods for the analysis.

        :param periods: A list of return periods to set.
        """
        if not isinstance(periods, list):
            logging.error("Return periods must be a list.")
            raise ValueError("Return periods must be a list.")

        if not all(isinstance(period, str) for period in periods):
            logging.error("All return periods must be string.")
            raise ValueError("All return periods must be string.")

        self._return_periods = periods
        logging.info(f"Return periods set to: {self._return_periods}")

    @property
    def backgrounds(self) -> str | None:
        """ Return the name of the orthophoto. """
        return self._background_images

    @backgrounds.setter
    def backgrounds(self, name: str | list[str]) -> None:
        """ Set the orthophoto for the analysis.

        :param name: The name of the orthophoto
        """
        # check if available in mapviewer
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        backgrounds = self.mapviewer.get_list_keys(drawing_type=draw_type.WMSBACK, checked_state=None)

        err = False

        if isinstance(name, str):
            name = [name]

        for background in name:
            if background not in backgrounds:
                logging.error(f"Background '{background}' not found.")
                err = True

        if err:
            back = '\n'.join(backgrounds)
            logging.info(f"Available backgrounds:\n{back}")
            raise ValueError(f"Orthophoto '{name}' not found in the available backgrounds.")

        self._background_images = name
        logging.info(f"Background images set to: {self._background_images}")

    def list_backgrounds(self) -> list[str]:
        """ List the available backgrounds in the map viewer.

        :return: A list of available background names.
        """
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        backgrounds = self.mapviewer.get_list_keys(drawing_type=draw_type.WMSBACK, checked_state=None)
        return backgrounds

    def list_simulations(self, scenario:str = None) -> list[str]:
        """ List the available simulations in the analysis.

        :param scenario: The name of the scenario to list simulations for. If None, lists all simulations.
        :return: A list of available simulation names.
        """

        if scenario is None:
            return {key : list_directories(dir/'simulations') for key,dir in self.scenarios_directories.items()}
        else:
            if scenario not in self.scenarios_directories:
                logging.error(f"Scenario '{scenario}' not found in the analysis.")
                raise ValueError(f"Scenario '{scenario}' not found in the analysis.")
            return list_directories(self.scenarios_directories[scenario] / 'simulations')

    def check_directories(self) -> bool:
        """ Check if the analysis directories exist.

        :return: True if all directories exist, False otherwise.
        """
        return check_analysis_directories(self.base_directory)

    def add_scenarios(self, scenario_names: list[tuple[str, str]]) -> dict:
        """ Add scenarios to the analysis.

        :param scenario_names: A list of scenario names to add.
        :return: A dictionary with the paths of the added scenarios.
        """

        # check scanerio_names are tuples of (name, title)
        if not all(isinstance(scen, tuple) and len(scen) == 2 for scen in scenario_names):
            logging.error("Scenario names must be a list of tuple (name, title).")
            raise ValueError("Scenario names must be a list of tuple (name, title).")

        # check all scenarios are different
        if len(scenario_names) != len(set(scen[0] for scen in scenario_names)):
            logging.error("Scenario names must be unique.")
            raise ValueError("Scenario names must be unique.")

        # check all titles are different
        if len(scenario_names) != len(set(scen[1] for scen in scenario_names)):
            logging.error("Scenario titles must be unique.")
            raise ValueError("Scenario titles must be unique.")

        if not check_if_scenarios_exist(self.storage_directory, [scen[0] for scen in scenario_names]):
            logging.error(f"You need to check your scenario names or your storage directory.")
            raise ValueError("One or more scenarios do not exist in the specified base directory.")

        self.scenarios_directories = get_scenarios_directories(self.storage_directory, [scen[0] for scen in scenario_names])
        self.scenarios = scenario_names

        # check if simulations exist for each scenario
        for scen in self.scenarios_directories.values():
            if (scen / 'simulations').exists():
                logging.info(f"Scenario '{scen}' has simulations available.")
            else:
                logging.warning(f"Scenario '{scen}' does not have simulations available. You may need to run simulations first.")

    def get_image(self, bounds: list|tuple, ds:float = None) -> tuple[plt.Figure, plt.Axes]:
        """ Get a figure and axes for displaying the map with the specified bounds.

        :param bounds: A list or a tuple with [xmin, ymin, xmax, ymax] defining the bounds to zoom in on.
        """

        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        if not isinstance(bounds, (list, tuple)) or len(bounds) != 4:
            logging.error("Bounds must be a list or tuple with four elements: [xmin, ymin, xmax, ymax].")
            raise ValueError("Bounds must be a list or tuple with four elements: [xmin, ymin, xmax, ymax].")

        xmin, ymin, xmax, ymax = bounds
        self.mapviewer.zoom_on({'xmin':xmin, 'xmax':xmax, 'ymin':ymin, 'ymax':ymax}, forceupdate=True)
        fig, ax = plt.subplots()

        if ds is None:

            ds = int(min(abs(xmax - xmin), abs(ymax - ymin)) / 5)
            if ds < 100:
                # rounded to 10
                ds = 10 * (ds // 10)
            elif ds < 500:
                # rounded to 10
                ds = 100 * (ds // 100)
            elif ds < 1000:
                # rounded to 500
                ds = 500 * (ds // 500)
            elif ds < 10000:
                # rounded to 1000
                ds = 1000 * (ds // 1000)

        else:
            if not isinstance(ds, (int, float)):
                logging.error("ds must be a number.")
                raise ValueError("ds must be a number.")

            if ds <= 0:
                logging.error("ds must be a positive number.")
                raise ValueError("ds must be a positive number.")

        try:
            self.mapviewer.display_canvasogl(fig=fig, ax=ax, ds = ds)
        except Exception as e:
            logging.error(f"Error displaying the map: {e}")
            raise RuntimeError("Error displaying the map. Ensure that the MapViewer is properly initialized and the bounds are valid.")

        return fig, ax

    def check_backgrounds(self):
        """ Check the orthophotos in the map viewer. """
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        for back in self.backgrounds:
            self.mapviewer.check_id(back)
        self.mapviewer.update()

    def uncheck_backgrounds(self):
        """ Uncheck the orthophotos in the map viewer. """
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        for back in self.backgrounds:
            self.mapviewer.uncheck_id(back)
        self.mapviewer.update()

    def create_report(self, title: str, author: str, report_name:str) -> RapidReport:
        """ Create a report for the analysis.

        :param title: The title of the report.
        :param author: The author of the report.
        :return: An instance of RapidReport.
        """
        self.report = create_a_report(title, author)
        self._report_name = Path(report_name).with_suffix('.docx')
        return self.report

    def save_report(self, report_name: str = None) -> None:
        """ Save the report to the specified directory.

        :param report_name: The name of the report file. If None, uses the default report name.
        """
        if self.report is None:
            logging.error("No report has been created yet.")
            raise ValueError("No report has been created yet.")

        if report_name is None:
            report_name = self._report_name

        report_path = self.directories[Directory_Analysis.REPORTS] / f"{Path(report_name).with_suffix('.docx')}"

        if not self._report_saved_once:
            # Check if the report already exists
            if report_path.exists():
                logging.warning(f"Report {report_path} already exists. It will be overwritten.")
            else:
                logging.info(f"Creating new report at {report_path}.")

            self._report_saved_once = True

        self.report.save(report_path)
        logging.info(f"Report saved to {report_path}.")

    def create_wolf_mapviewer(self) -> WolfMapViewer:
        """ Create a WolfMapViewer instance.

        :return: An instance of WolfMapViewer.
        """
        self.mapviewer = create_a_wolf_viewer()
        return self.mapviewer

    def set_current_scenario(self, scenario_name: str) -> None:
        """ Set the current scenario for the analysis.

        :param scenario_name: The name of the scenario to set as current.
        """

        scenario_name = _sanitize_scenario_name(scenario_name)
        if scenario_name not in self.scenarios_directories:
            logging.error(f"Scenario '{scenario_name}' not found in the analysis.")
            raise ValueError(f"Scenario '{scenario_name}' not found in the analysis.")

        self.current_scenario = self.scenarios_directories[scenario_name]
        logging.info(f"Current scenario set to {self.current_scenario}.")

    def __getitem__(self, scenario_name: str) -> Path:
        """ Get the path of a specific scenario.

        :param scenario_name: The name of the scenario to get.
        :return: The path to the scenario directory.
        """

        scenario_name = _sanitize_scenario_name(scenario_name)
        if scenario_name not in self.scenarios_directories:
            logging.error(f"Scenario '{scenario_name}' not found in the analysis.")
            raise KeyError(f"Scenario '{scenario_name}' not found in the analysis.")
        return self.scenarios_directories[scenario_name]

    def get_scenario_names(self) -> list[str]:
        """ Get the names of the scenarios in the analysis.

        :return: A list of scenario names.
        """
        return list(self.scenarios_directories.keys())

    def get_scenarios_titles(self) -> list[str]:
        """ Get the titles of the scenarios in the analysis.

        :return: A list of scenario titles.
        """
        return [scen[1] for scen in self.scenarios]

    def report_introduction_auto(self):
        """ Automatically generate the introduction section of the report."""

        if self.report is None:
            logging.error("No report has been created yet.")
            raise ValueError("No report has been created yet.")

        if len(self.return_periods) == 0:
            logging.error("No return periods have been set for the analysis.")
            raise ValueError("No return periods have been set for the analysis.")

        if len(self.scenarios) == 0:
            logging.error("No scenarios have been added to the analysis.")
            raise ValueError("No scenarios have been added to the analysis.")

        report = self.report

        report.add_title('Scénarios de modélisation')
        report.add_bullet_list(self.return_periods)

        report.add_title("Méthodologie d'analyse")
        report += "L'analyse des simulations est réalisée en plusieurs étapes :"
        report.add_bullet_list(["Préparation des modélisations sur base du 'gestionnaire de scénarios'",
                                "Calcul des modélisations via 'wolfgpu' pour les différentes périodes de retour",
                                "Analyse des lignes d'eau pour chaque scénario",
                                "Comparaison des lignes d'eau pour chaque période de retour",
                                "Analyse des situations de débordement en 2D"])

        report.add_title("Méthode de représentation des lignes d'eau")
        report.add_title("Approche générale",2)
        report += """Le lit mineur de la rivière a été délimité au moyen de polylignes (centre et 2 parallèles RG et RD).
Ces polylignes ont été ensuite découpées en tronçon de 5 mètres pour former des polygones régulièrement répartis.
Dans chaque polygone, les valeurs des inconnues de modélisations (hauteur d'eau et débits spécifiques selon X et Y) peuvent être extraites.
Après avoir fait de même pour l'information topo-bathymétrique, il est possible de calculer l'altitude de surface libre de l'eau en chaque maille.
Cela représente donc une série de valeurs en chaque polygone.
La valeur médiane de cette série est ensuite exploitée et associée à la coordonnée curviligne du centre du polygone.
"""
        report.add_title("Variante de position du lit mineur dans les scénarios",2)
        report += """Si le lit mineur est déplacé dans un scénario, les polygones sont adaptés en fonction de la nouvelle position du lit mineur.
Par contre, afin de procéder à une comparaison des lignes d'eau entre scénarios, il est nécessaire de choisir une référence.
Cette référence servira à évaluer les coordonnées curvilignes de tous les polygones par projection géométrique au point le plus proche.
La distorsion engendrée par cette approche est acceptable pour les scénarios envisagés pour Theux.
L'attention est toutefois attirée sur le fait que cette approche pourrait ne pas être valable pour des déplacements nettement plus importants du lit mineur.
"""

        self.save_report()
        logging.info("Introduction section of the report has been automatically generated.")

    def report_add_figure_from_zoom(self, bounds: list|tuple, caption:str = None, ds:float = None) -> None:
        """ Add a figure to the report from the current zoomed view of the map viewer.

        :param bounds: A list or a tuple with [xmin, ymin, xmax, ymax] defining the bounds to zoom in on.
        :param ds: The distance scale for the figure. If None, it will be calculated automatically.
        :param caption: The caption for the figure. If None, no caption will be added.
        """
        if self.report is None:
            logging.error("No report has been created yet.")
            raise ValueError("No report has been created yet.")

        if ds is None:
            xmin, ymin, xmax, ymax = self.viewer_bounds

            ds = int(min(abs(xmax - xmin), abs(ymax - ymin)) / 5)
            if ds < 100:
                # rounded to 10
                ds = 10 * (ds // 10)
            elif ds < 500:
                # rounded to 10
                ds = 100 * (ds // 100)
            elif ds < 1000:
                # rounded to 500
                ds = 500 * (ds // 500)
            elif ds < 10000:
                # rounded to 1000
                ds = 1000 * (ds // 1000)

        else:
            if not isinstance(ds, (int, float)):
                logging.error("ds must be a number.")
                raise ValueError("ds must be a number.")

            if ds <= 0:
                logging.error("ds must be a positive number.")
                raise ValueError("ds must be a positive number.")

        fig, ax = self.get_image(bounds, ds)
        self.report.add_figure(fig, caption=caption)
        logging.info("Figure added to the report from the current zoomed view of the map viewer.")

        return fig, ax

    def load_modifications(self, ad2viewer:bool = True):
        """ Load modifications for scenarios from vecz files.

        :param ad2viewer: If True, add the modifications to the map viewer.
        :raises ValueError: If the MapViewer is not initialized.
        """

        MODIF = 'bath_assembly.vecz'

        for key, directory in self.scenarios_directories.items():
            modif_path = directory / MODIF

            if modif_path.exists():
                logging.info(f"Loading modifications from {modif_path}")
                self._modifications[key] = Zones(modif_path, mapviewer=self.mapviewer)

                self._modifications[key].myzones[0].myvectors[0].unuse()

                if ad2viewer:
                    if self.mapviewer is None:
                        logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
                        raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

                    self.mapviewer.add_object('vector', newobj= self._modifications[key], id=f'modif_{key}', ToCheck= True)
                    logging.info(f"Modifications for scenario {key} added to the map viewer.")
            else:
                logging.warning(f"No modifications found for scenario {key} at {modif_path}.")
                self._modifications[key] = None

    def uncheck_modifications(self, scenario:str | tuple) -> None:
        """ Uncheck the modifications for a specific scenario in the map viewer.

        :param scenario: The name of the scenario to uncheck modifications for.
        """
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        if isinstance(scenario, tuple):
            scenario = scenario[0].strip()

        if scenario not in self._modifications:
            logging.error(f"Scenario '{scenario}' not found in the modifications.")
            raise KeyError(f"Scenario '{scenario}' not found in the modifications.")

        if self._modifications[scenario] is None:
            logging.error(f"No modifications loaded for scenario '{scenario}'.")
            return

        self.mapviewer.uncheck_id(f'modif_{scenario}')

    def uncheck_all_modifications(self) -> None:
        """ Uncheck all modifications in the map viewer."""
        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        for scenario in self._modifications.keys():
            self.uncheck_modifications(scenario)
        logging.info("All modifications unchecked in the map viewer.")

    def check_modifications(self, scenario:str | tuple) -> bool:
        """ Check if modifications have been loaded for all scenarios.

        :return: True if modifications are loaded for all scenarios, False otherwise.
        """

        if self.mapviewer is None:
            logging.error("MapViewer is not initialized. Please create a WolfMapViewer instance first.")
            raise ValueError("MapViewer is not initialized. Please create a WolfMapViewer instance first.")

        if isinstance(scenario, tuple):
            scenario = scenario[0].strip()

        if scenario not in self._modifications:
            logging.error(f"Scenario '{scenario}' not found in the modifications.")
            raise KeyError(f"Scenario '{scenario}' not found in the modifications.")

        if self._modifications[scenario] is None:
            logging.error(f"No modifications loaded for scenario '{scenario}'.")
            return False

        self.mapviewer.check_id(f'modif_{scenario}')

