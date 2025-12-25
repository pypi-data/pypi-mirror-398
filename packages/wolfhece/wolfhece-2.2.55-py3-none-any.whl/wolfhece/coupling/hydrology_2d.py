"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from ..hydrology.Catchment import Catchment, SubBasin
from ..hydrology.PyWatershed import Watershed, Node_Watershed, RiverSystem, SubWatershed
from ..wolf_array import WolfArray, WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_SINGLE
from ..PyVertexvectors import Zones,zone,vector, wolfvertex
from ..PyTranslate import _

from scipy.spatial import KDTree
import pandas as pd
from datetime import datetime
from pathlib import Path
import numpy as np
from typing import Literal, Union
from enum import Enum
import logging
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes


class InjectionType(Enum):
    GLOBAL = 'Global'                   # Global hydrograph - sum of upstream watershed and local hydrograph (hydrological model)
    PARTIAL = 'Partial'                 # Partial hydrograph - local hydrograph only (hydrological model)
    ANTHROPOGENIC = 'Anthropogenic'     # Output of an anthropogenic module (hydrological model)
    CONSTANT = 'Constant'               # Constant value (user input)
    VIRTUAL = 'Virtual'                 # Virtual hydrograph - Combination/Part of hydrographs (computed by the coupling)
    FORCED_UNSTEADY = 'Forced unsteady' # Imposed unsteady flow (user input)

BUILDING_TOLERANCE = 0.05 # Epsilon for the buildings (DEM-DTM) [m]

class Searching_Context():
    """ Part of the hydrological model adapted for seraching tasks """

    def __init__(self,
                 river_axis:vector,
                 kdtree:KDTree,
                 nodes:Node_Watershed,
                 downstream_reaches:list[int],
                 up_node:Node_Watershed) -> None:
        """
        :param river_axis: river axis -- vector
        :param kdtree: KDTree of the downstream reaches
        :param nodes: nodes of the downstream reaches - from Hydrology model
        :param downstream_reaches: downstream reaches - from Hydrology model
        :param up_node: up node - from Hydrology model
        """

        self.river_axis:vector              = river_axis        # river axis -- vector
        self.kdtree:KDTree                  = kdtree            # KDTree of the downstream reaches
        self.nodes:Node_Watershed           = nodes             # nodes of the downstream reaches - from Hydrology model
        self.downstream_reaches:list[int]   = downstream_reaches# downstream reaches - from Hydrology model
        self.up_node:Node_Watershed         = up_node           # up node - from Hydrology model

    def __str__(self) -> str:
        """ Return a string representation of the searching context """

        ret = ''

        ret += f"  Number of reaches: {len(self.downstream_reaches)}\n"
        ret += f"  Downstream reaches: {self.downstream_reaches}\n"
        ret += f"  Number of nodes: {len(self.nodes)}\n"
        ret += f"  Length of the river axis: {self.river_axis.length2D}\n"

        return ret


class Scaled_Infiltration():

    def __init__(self, idx:int, type:InjectionType, colref:str, factor:float, lagtime:float) -> None:
        """ Constructor of the scaled infiltration

        :param idx: index of the infiltration
        :param type: type of the infiltration
        :param colref: reference column
        :param factor: multiplicator factor [-]
        :param lagtime: lag time [s]
        """

        self.index = idx        # index of the infiltration
        self.type = type        # type of the infiltration
        self.colref = colref    # reference column
        self.factor = factor    # multiplicator factor [-]
        self.lagtime = lagtime  # lag time [s]

class Coupling_Hydrology_2D():

    def __init__(self) -> None:


        self._rivers_zones:list[Zones] = []
        self.rivers:dict[str, vector] = {}

        self.upstreams:dict[str, wolfvertex] = {}

        self._locale_injection_zones:Zones = None
        self.locale_injections:dict[str, vector] = {}

        self._hydrology_model:Catchment = None

        self._searching:dict[str, Searching_Context] = {}

        self.hydrographs_total:pd.DataFrame = None
        self.hydrographs_local:pd.DataFrame = None
        self._hydrographs_virtual = []

        self._dem:WolfArray = None  # Digital Elevation Model
        self._dtm:WolfArray = None  # Digital Terrain Model -- Optional -- if exists, no infiltration authorized on buildings (defined as dem > dtm)
        self._buildings:WolfArray = None  # Buildings -- exists if dtm exists

        self._infil_idx:WolfArray = None
        self.counter_zone_infil = 0

        # Les infiltrations sont définies par des zones de mailles.
        # Chaque zone est définie par :
        #  - un type d'infiltration
        #  - un nom d'hydrogramme (ou une valeur constante)
        #  - un facteur podérateur
        #  - un temps de déphasage

        self.infiltrations:list[Scaled_Infiltration] = []
        self.local_infiltrations:dict[vector:int] = {}

        # lists part is a dictionary with the following structure:
        #  - key : river name
        #  - value : tuple with two elements
        #   - first element : list of unique drained areas
        #   - second element : dictionary with the following structure
        #     - key : drained area
        #     - value : list of coordinates of the river points in the dem
        self.lists_part:dict[str, tuple[np.ndarray, dict[float, list[tuple[float, float]]]]] = {}

        self.df_2d = None

        self_along = None
        self._locales = None

    @property
    def dateBegin(self) -> datetime:
        if self._hydrology_model is None:
            logging.error(_("No hydrology model loaded"))
            return None
        return self._hydrology_model.dateBegin

    @property
    def dateEnd(self) -> datetime:
        if self._hydrology_model is None:
            logging.error(_("No hydrology model loaded"))
            return None
        return self._hydrology_model.dateEnd

    def __str__(self) -> str:
        """ Return a string representation of the coupling """

        ret =''

        ret += _("Rivers: {}\n").format(len(self.rivers))
        for curriver in self.rivers:
            ret += f"{curriver}\n"

        ret += _("Local injections: {}\n").format(len(self.locale_injections))
        for curinj in self.locale_injections:
            ret += f"{curinj}\n"


        ret += _("Upstreams: {}\n").format(len(self.upstreams))
        for curup in self.upstreams:
            ret += f"  {curup} :\n"
            ret += f"  X : {self.upstreams[curup][0]}\n"
            ret += f"  Y : {self.upstreams[curup][1]}\n"
            ret += f"  Drained area : {self.river_system.get_nearest_nodes(self.upstreams[curup])[1].uparea}\n"

        for cursearch in self._searching:
            ret += f"{cursearch} : \n{self._searching[cursearch]}\n"

        ret += f"Coupling array: \n{self._infil_idx}\n"

        return ret

    @property
    def number_of_injections(self) -> int:

        if self._infil_idx is None:
            logging.error(_("No infiltration array -- Spread the injections first"))
            return 0

        return self._infil_idx.array.max()

    @property
    def number_of_nodes_per_zone(self) -> dict[int, int]:
        """ Return the number of nodes per zone """

        if self._infil_idx is None:
            logging.error(_("No infiltration array -- Spread the injections first"))
            return {}

        non_zeros = self._infil_idx.array[np.where(self._infil_idx.array > 0)]

        return {i:np.count_nonzero(non_zeros == i) for i in range(1, self.number_of_injections+1)}

    def plot_number_of_nodes_per_zone(self) -> tuple[Figure, Axes]:
        """ Plot the number of nodes per zone """

        if self._infil_idx is None:
            logging.error(_("No infiltration array -- Spread the injections first"))
            return None, None

        fig, ax = plt.subplots()
        ax.hist(self.number_of_nodes_per_zone)
        ax.set_title(_("Number of nodes per zone"))
        ax.set_xlabel(_("Zone index"))
        ax.set_ylabel(_("Number of nodes"))

        return fig, ax

    @property
    def along(self) -> list[str, str]:
        return self._along

    @along.setter
    def along(self, value:list[tuple[str, str]]) -> None:

        for curval in value:

            curcol, currivers = curval

            assert curcol in self.hydrographs_local.columns, f"Column {curcol} not found in hydrographs"

            def check_rivers(currivers):
                if isinstance(currivers, list):
                    for curriver in currivers:
                        check_rivers(curriver)
                else:
                    assert currivers in self.rivers, f"River {currivers} not found"

        self._along = value

    @property
    def locales(self) -> list[str]:
        return self._locales

    @locales.setter
    def locales(self, value:list[tuple[str, str | pd.Series | float, InjectionType]]) -> None:
        """ Set the locales injections """

        for curvect, curcol, curtype in value:
            # Check if the data is correct

            if curtype not in [InjectionType.CONSTANT, InjectionType.FORCED_UNSTEADY]:
                assert curvect in self.locale_injections, f"Vector {curvect} not found"
                assert curcol in list(self.hydrographs_total.columns)+ self._hydrographs_virtual, f"Column {curcol} not found in hydrographs"
            elif curtype == InjectionType.FORCED_UNSTEADY:
                assert isinstance(curcol, pd.Series), "Forced unsteady flow should be a Series"
                # check if the DateFrame has value inside interval of the hydrographs
                assert curcol.index[0] <= self.dateBegin, "Forced unsteady flow should start before the hydrographs"
                assert curcol.index[-1] >= self.dateEnd, "Forced unsteady flow should end after the hydrographs"
            else:
                assert isinstance(curcol, float), "Constant value should be a float"

        self._locales = value

    @property
    def watershed(self) -> Watershed:
        return self._hydrology_model.charact_watrshd

    @property
    def river_system(self) -> RiverSystem:
        return self.watershed.riversystem

    @property
    def subs_array(self) -> WolfArray:
        return self.watershed.subs_array

    def set_array_to_coupling(self, array:WolfArray | Path, dtm:WolfArray | Path = None) -> None:
        """ Set the array to coupling

        :param array: The array to coupling
        :param dtm: The DTM of the array
        """

        if isinstance(array, Path):
            if array.exists():
                self._dem = WolfArray(array)
            else:
                logging.error(_("File {} not found").format(array))
                return

        if isinstance(dtm, Path):
            if dtm.exists():
                self._dtm = WolfArray(dtm)
            else:
                logging.error(_("File {} not found").format(dtm))
                return

        self._dem = array
        self._dtm = dtm

        assert self._dem.get_header().is_like(self._dtm.get_header()), "DEM and DTM should have the same header"

        self._create_infiltration_array()

    def _create_infiltration_array(self):
        """ Create the infiltration array """

        if self._dem is None:
            logging.error(_("No array to coupling"))
            return

        if self._dtm is None:
            logging.info(_("No DTM found -- Infiltration authorized everywhere"))
        else:
            logging.info(_("DTM found -- Infiltration authorized only on the ground"))
            self._buildings = self._dem - self._dtm

            # Buildings are defined as the difference between the DEM and the DTM
            # If the difference is greater than BUILDING_TOLERANCE, the cell is considered as a building
            # Otherwise, the cell is considered as a ground

            # If cell is masked in the DTM, cells is considred as ground
            self._buildings.array[np.logical_and(~self._dem.array.mask,self._dtm.array.mask)] = 0.

            self._buildings.array[self._buildings.array < BUILDING_TOLERANCE] = 0.
            self._buildings.array[self._buildings.array >= BUILDING_TOLERANCE] = 1.
            self._buildings.mask_data(0.)

        self._infil_idx = WolfArray(srcheader=self._dem.get_header(), whichtype=WOLF_ARRAY_FULL_INTEGER)
        self._infil_idx.add_ops_sel()
        self._infil_idx.array[:,:] = 0

        self.counter_zone_infil = 0

    def add_hydrology_model(self, name:str, filename:str | Path) -> None:
        """ Add a hydrology model to the coupling

        :param filename: The filename of the hydrology model
        """

        self._hydrology_model = Catchment(name, str(filename), False, True)

    def get_anthropogenic_names(self) -> list[str]:
        """ Print the names of the anthropogenic hydrographs """

        if self._hydrology_model is None:
            logging.error(_("No hydrology model loaded"))
            return []

        return [" : ".join([cur_anth.name, name])
                    for cur_anth in self._hydrology_model.retentionBasinDict.values()
                    for name in cur_anth.get_outFlow_names()]

    def get_names_areas(self) -> list[str]:
        """ Print the names of the areas """

        if self._hydrology_model is None:
            logging.error(_("No hydrology model loaded"))
            return []

        names= [cur_sub.name for cur_sub in sorted(self._hydrology_model.subBasinDict.values(), key=lambda sub: sub.iDSorted)]
        area_subs = [cur_sub.surfaceDrained for cur_sub in sorted(self._hydrology_model.subBasinDict.values(), key=lambda sub: sub.iDSorted)]
        area_glob = [cur_sub.surfaceDrainedHydro for cur_sub in sorted(self._hydrology_model.subBasinDict.values(), key=lambda sub: sub.iDSorted)]

        return names, area_subs, area_glob

    def create_hydrographs_local_global(self, unit_discharge:float, total_duration:float, anth_discharge:dict = None) -> None:
        """
        Create the hydrographs from the hydrology model .

        Global and local hydrographs are created based on a unit discharge and a total duration.

        You can also add anthropogenic hydrographs from a dictionary.
        The key is the name of the anthropogenic hydrograph and the value is the discharge.
        The keys can be obtained with the method get_anthropogenic_names.

        :param unit_discharge: The discharge per square kilometer [m³/s/km²]
        :param total_duration: The total duration of the hydrographs [s]
        """

        # Extract the column names according to their sorted subbasin indices
        col_time = "Time [s]"
        col_subs, area_subs, area_glob = self.get_names_areas()
        col_anth = [" : ".join([cur_anth.name, name])
                    for cur_anth in self._hydrology_model.retentionBasinDict.values()
                    for name in cur_anth.get_outFlow_names()]

        #Create a dictionnary

        dict_glob = {col_time : [0., total_duration]}

        for cur_sub, cur_area in zip(col_subs, area_glob):
            discharge = cur_area * unit_discharge
            dict_glob[cur_sub] = [discharge, discharge]

        for cur_anth in col_anth:
            dict_glob[cur_anth] = [0., 0.]

        if anth_discharge is not None:
            for cur_anth, cur_discharge in anth_discharge.items():
                dict_glob[cur_anth] = [cur_discharge, cur_discharge]

        dict_loc = {col_time : [0., total_duration]}

        for cur_sub, cur_area in zip(col_subs, area_subs):
            discharge = cur_area * unit_discharge
            dict_loc[cur_sub] = [discharge, discharge]

        self.hydrographs_total = pd.DataFrame(dict_glob)
        self.hydrographs_local = pd.DataFrame(dict_loc)

        self.hydrographs_local.set_index(col_time, inplace=True)
        self.hydrographs_total.set_index(col_time, inplace=True)

    def save_hydrographs(self, directory:str | Path = None, total:str = None, partial:str = None) -> None:
        """ Write the hydrographs from the hydrology model """

        if directory is None:

            if self._hydrology_model is None:
                logging.error(_("No hydrology model loaded"))
                return

            directory = Path(self._hydrology_model.workingDir) / 'PostProcess'

        if total is not None:
            self.hydrographs_total.to_csv(directory / total, sep='\t', decimal='.', encoding='latin1')
        else:
            self.hydrographs_total.to_csv(directory / 'Hydros_2_simul2D.txt', sep='\t', decimal='.', encoding='latin1')

        if partial is not None:
            self.hydrographs_local.to_csv(directory / partial, sep='\t', decimal='.', encoding='latin1')
        else:
            self.hydrographs_local.to_csv(directory / 'HydrosSub_2_simul2D.txt', sep='\t', decimal='.', encoding='latin1')


    def load_hydrographs(self, directory:str | Path = None, total:str = None, partial:str = None) -> None:
        """ Load the hydrographs from the hydrology model

        :param directory: The directory of the hydrology model -- If None, the working directory of the loaded hydrology model is used
        :param total: The filename of the total hydrographs - If None, the default filename is used
        :param partial: The filename of the partial hydrographs - If None, the default filename is used

        """

        if directory is None:

            if self._hydrology_model is None:
                logging.error(_("No hydrology model loaded"))
                return

            directory = Path(self._hydrology_model.workingDir) / 'PostProcess'

            if total is not None:
                total = directory / total
                if total.exists():
                    self.hydrographs_total = pd.read_csv(total, sep='\t', decimal='.', header=0, index_col=0, encoding='latin1')
                else:
                    logging.error(_("File {} not found").format(total))

            else:
                total = directory / 'Hydros_2_simul2D.txt'
                if total.exists():
                    self.hydrographs_total = pd.read_csv(total, sep='\t', decimal='.', header=0, index_col=0, encoding='latin1')
                else:
                    logging.error(_("File {} not found").format(total))

            if partial is not None:
                partial = directory / partial
                if partial.exists():
                    self.hydrographs_local = pd.read_csv(partial, sep='\t', decimal='.', header=0, index_col=0, encoding='latin1')
                else:
                    logging.error(_("File {} not found").format(partial))

            else:
                partial = directory / 'HydrosSub_2_simul2D.txt'
                if partial.exists():
                    self.hydrographs_local = pd.read_csv(partial, sep='\t', decimal='.', header=0, index_col=0, encoding='latin1')
                else:
                    logging.error(_("File {} not found").format(partial))


    def print_hydrographs(self, total:bool = True, partial:bool = True) -> None:
        """ Print the hydrographs from the hydrology model """

        if total:
            print(_("Total hydrographs:"))
            print(self.hydrographs_total.columns)

        if partial:
            print(_("Partial hydrographs:"))
            print(self.hydrographs_local.columns)

    def plot_hydrographs(self, total:bool = True, partial:bool = True) -> tuple[tuple[Figure, Axes],tuple[Figure, Axes]]:
        """ Plot the hydrographs from the hydrology model """

        if total:
            ax1 = self.hydrographs_total.plot()
            fig1 = ax1.figure
            ax1.legend(loc='upper center', ncol=8)
            ax1.set_ylim(0, 1000)
            fig1.set_size_inches(15, 5)
            fig1.tight_layout()
        else:
            fig1, ax1 = None, None

        if partial:
            ax2 = self.hydrographs_local.plot()
            fig2 = ax2.figure
            ax2.legend(loc='upper center', ncol=8)
            ax2.set_ylim(0, 1000)
            fig2.set_size_inches(15, 5)
            fig2.tight_layout()
        else:
            fig2, ax2 = None, None

        return (fig1, ax1), (fig2, ax2)


    def add_virtual_hydrograph(self, name:str, src_hydrograph_name:str, factor:float, lag:float=0.):
        """ Add a virtual hydrograph to the hydrology model """

        self._hydrographs_virtual.append((name, src_hydrograph_name, factor, lag))

    def add_river(self, filename:str | Path) -> None:
        """ Add a river to the hydrology model

        :param filename: The filename of the river
        """

        self._rivers_zones.append(Zones(filename))

    def reset(self) -> None:
        """ Reset the hydrology model """

        self._rivers_zones = []
        self.rivers = {}
        self._locale_injection_zones = None
        self.locale_injections = {}
        self.lists_part = {}
        self.df_2d = None

        self._searching = {}

        self.reset_injections()

    def add_locale_injections(self, filename:str | Path) -> None:
        """ Add a local injection to the hydrology model

        :param filename: The filename of the local injection
        """

        self._locale_injection_zones = Zones(filename)

    def find_river_axis(self):
        """ Find the river axis from Zones """

        for curriver in self._rivers_zones:
            for curzone in curriver.myzones:
                if curzone.nbvectors !=3:
                    logging.error(_("Zone {} has {} vectors, should be 3").format(curzone.myname, curzone.nbvectors))
                else:
                    # Select the river axis
                    curvector = curzone.myvectors[1]
                    if curvector.used:
                        self.rivers[curzone.myname] = curvector
                    else:
                        logging.warning(_("Vector {} in zone {} is not used -- Ignoring it as a river axis").format(curvector.myname, curzone.myname))

    def _add_injection(self, name:str, vect:vector):
        """ Add an injection to the hydrology model

        :param name: The name of the injection
        :param vect: The vector of the injection
        """

        self.locale_injections[name] = vect

    def find_injections(self):
        """ Find the injection points from Zones """

        for curzone in self._locale_injection_zones.myzones:

            names = [curvect.myname for curvect in curzone.myvectors]

            if 'injection' in names:
                vect = curzone.myvectors[names.index('injection')]
                if vect.used:
                    self._add_injection(curzone.myname, vect)
                else:
                    logging.warning(_("Vector {} in zone {} is not used -- Ignoring it as an injection point").format(vect.myname, curzone.myname))
            else:
                logging.error(_("Zone {} does not contain an injection point").format(curzone.myname))

    def find_rivers_upstream(self):
        """ Find the upstreams of the rivers """

        for curriver, curvect in self.rivers.items():
            up = self._find_upstream(curvect)
            self.upstreams[curriver] = (up.x, up.y)

    def _find_upstream(self, curvect:vector) -> wolfvertex:
        """ Find the upstream of a vector

        :param curvect: The river's axis
        """

        vert1 = curvect.myvertices[0]
        vert2 = curvect.myvertices[-1]

        riv1 = self.river_system.get_nearest_nodes([vert1.x, vert1.y])[1]
        riv2 = self.river_system.get_nearest_nodes([vert2.x, vert2.y])[1]

        # Drained area
        area1 = riv1.uparea
        area2 = riv2.uparea

        # Get the minimum
        if area1 > area2:
            return vert2
        else:
            return vert1

    def prepare_search(self, rivers:list[str] = None):
        """
        Prepare the search for the hydrology model.

        The order is important because the reaches will be
        progressively excluded from the search for the next ones.

        So, you have to start with the **main river** and then the **tributaries**.

        :param rivers: The list of rivers to prepare
        """

        excluded = []

        if rivers is None:
            rivers = self.rivers.keys()
        else:
            for curriver in rivers:
                if curriver not in self.rivers:
                    logging.error(f"River {curriver} not found")
                    return
            logging.info(f"Rivers to prepare in thos order: {rivers}")

        for curriver in rivers:

            curvect = self.rivers[curriver]

            # Récupération de la maille rivière la plus proche
            dist, node_up = self.river_system.get_nearest_nodes(self.upstreams[curriver])

            # Récupération de la liste des biefs en aval
            downstream = self.river_system.get_downstream_reaches_excluded(node_up, excluded)

            excluded += downstream

            # Mis en place d'une structure de recherche rapide
            nodes, kdtree = self.river_system.get_kdtree_from_reaches(downstream)

            self._searching[curriver] = Searching_Context(curvect, kdtree, nodes, downstream, node_up)

    def _is_global(self, col_name:str):
        """ Vérifie si la colonne est un hydrogramme global """

        return col_name in self.hydrographs_total.columns

    def _is_partial(self, col_name:str):
        """ Vérifie si la colonne est un hydrogramme partiel """

        return col_name in self.hydrographs_local.columns

    def _is_anthropic(self, col_name:str):
        """
        Vérifie si la colonne est un hydrogramme anthropique
        (c'est-à-dire une colonne de l'hydrogramme total qui n'est pas un hydrogramme partiel)

        """

        return self._is_global(col_name) and not self._is_partial(col_name)

    def _is_virtual(self, col_name:str):
        """ Vérifie si la colonne est un hydrogramme virtuel """

        return col_name in [virtualname for virtualname, src_name, frac, lag in self._hydrographs_virtual]

    def _add_infil(self,
                  type_name:InjectionType,
                  col_name_q:str | float,
                  factor:float,
                  lag:float,
                  index_zone:int = None):
        """
        Ajoute une infiltration à la liste des infiltrations

        :param type_name: nom du type d'infiltration
        :param col_name: nom de la colonne de l'hydrogramme
        :param factor: facteur multiplicatif
        :param lag: déphasage
        """

        if type_name == InjectionType.GLOBAL:
            if not self._is_global(col_name_q):
                raise ValueError(f"Colonne {col_name_q} not found in global hydrographs")
        elif type_name == InjectionType.PARTIAL:
            if not self._is_partial(col_name_q):
                raise ValueError(f"Colonne {col_name_q} not found in partial hydrographs")
        elif type_name == InjectionType.ANTHROPOGENIC:
            if not self._is_anthropic(col_name_q):
                raise ValueError(f"Colonne {col_name_q} not found in anthropic hydrographs")
        elif type_name == InjectionType.VIRTUAL:
            if not self._is_virtual(col_name_q):
                raise ValueError(f"Colonne {col_name_q} not found in virtual hydrographs")

        if index_zone is None:
            self.counter_zone_infil += 1
            index_zone = self.counter_zone_infil

        self.infiltrations.append(Scaled_Infiltration(index_zone, type_name, col_name_q, factor, lag))

        return index_zone

    def _add_local_injecton(self,
                           local_vect:vector,
                           type_name:InjectionType,
                           col_name:str,
                           factor:float,
                           lag:float):

        """
        Ajoute une injection locale à la liste des infiltrations
        et remplissage de la matrice d'infiltration

        :param local_vect: vecteur de la zone d'injection
        :param type_name: nom du type d'injection
        :param col_name: nom de la colonne de l'hydrogramme
        :param factor: facteur multiplicatif
        :param lag: déphasage

        """

        assert type_name in InjectionType, f"Unknown type {type_name}"

        if local_vect not in self.local_infiltrations:
            # Pas encore d'injection dans cette zone

            self.local_infiltrations[local_vect] = self._add_infil(type_name, col_name, factor, lag)

            # Mise à zéro de la sélection dans la matrice d'infiltration
            self._infil_idx.SelectionData.reset()
            # Sélection des mailles à l'intérieur du polygone de la zone d'injection
            self._infil_idx.SelectionData.select_insidepoly(local_vect)

            # Récupération des coordonnées des mailles sélectionnées
            xy = np.array(self._infil_idx.SelectionData.myselection)
            # Conversion des coordonnées en indices de mailles
            ij = self._infil_idx.get_ij_from_xy_array(xy)

            if self._buildings is not None:
                # Vérification de la présence de bâtiments dans la zone d'infiltration
                for i,j in ij:
                    if self._buildings.array[i,j] == 1:
                        logging.warning(f"Building found in infiltration zone {local_vect.myname} -- Maille {i,j} ignored")
                        continue
                    self._infil_idx.array[i,j] = self.local_infiltrations[local_vect]

                assert np.count_nonzero(self._infil_idx.array == self.local_infiltrations[local_vect]) > 0, f"No infiltration in zone {local_vect.parentzone.myname}"

            else:
                # Affectation de l'indice de la zone d'infiltration
                for i,j in ij:
                    self._infil_idx.array[i,j] = self.local_infiltrations[local_vect]

                # Vérification du nombre de mailles affectées
                assert len(ij) == np.count_nonzero(self._infil_idx.array == self.local_infiltrations[local_vect]), "Bad count for {}".format(type_name)

        else:
            # Une injection existe déjà dans cette zone
            # On ajoute une nouvelle infiltration qui sera additionnée à la précédente

            self._add_infil(type_name, col_name, factor, lag, self.local_infiltrations[local_vect])


    def _add_along_injection(self,
                            list_part:list[float, float],
                            type_name:InjectionType,
                            col_name:str,
                            factor:float,
                            lag:float):
        """
        Ajoute une injection le long de la rivière
        et remplissage de la matrice d'infiltration

        :param list_part: liste des coordonnées des points de la rivière
        :param type_name: nom du type d'injection
        :param col_name: nom de la colonne de l'hydrogramme
        :param factor: facteur multiplicatif
        :param lag: déphasage
        """

        idx_zone = self._add_infil(type_name, col_name, factor, lag)

        for x, y in list_part:
            i,j = self._infil_idx.get_ij_from_xy(x,y)
            self._infil_idx.array[i,j] = idx_zone


    def write_infil_array(self, dirout:Path):
        """ Sauvegarde de la matrice d'infiltration """

        self._infil_idx.mask_data(0)
        self._infil_idx.nullvalue = 99999
        self._infil_idx.set_nullvalue_in_mask()
        self._infil_idx.write_all(dirout / f'infiltration.tif')

    def _get_reaches_in_sub(self, subbasin:SubWatershed, rivers_names:list[str]) -> list[list[int]]:
        """
        Retourne une liste de listes des biefs dans le sous-bassin

        :param rivers: liste des noms des rivières
        :return: liste des biefs dans le sous-bassin
        """

        ret = []

        if rivers_names[0] not in self._searching:
            logging.error(f"River {rivers_names[0]} not found")
            return ret

        reaches1 = self._searching[rivers_names[0]].downstream_reaches

        reaches_in_sub = [idx for idx in reaches1 if subbasin.is_reach_in_sub(idx)]

        if len(reaches_in_sub) == 0:
            logging.error(f"No reaches in subbasin for river {rivers_names[0]}")

        ret.append(reaches_in_sub)

        if isinstance(rivers_names[1], list):
            locret = self._get_reaches_in_sub(subbasin, rivers_names[1])

            for loc in locret:
                ret.append(loc)
        else:

            if rivers_names[1] not in self._searching:
                logging.error(f"River {rivers_names[1]} not found")
                return ret

            reaches2 = self._searching[rivers_names[1]].downstream_reaches

            reaches_in_sub = [idx for idx in reaches2 if subbasin.is_reach_in_sub(idx)]
            if len(reaches_in_sub) == 0:
                logging.error(f"No reaches in subbasin for river {rivers_names[1]}")

            ret.append(reaches_in_sub)

        return ret

    def _get_outlet_reaches(self, subbasin:SubWatershed, idx_reaches:list[int]) -> Node_Watershed:
        """
        Retourne le noeud de sortie du sous-bassin

        :param reaches: liste des biefs dans le sous-bassin
        :return: noeud de sortie du sous-bassin
        """

        down_reach = max(idx_reaches)
        return subbasin.get_downstream_node_in_reach(down_reach)

    def _split_subwatershed(self, subbasin:SubWatershed, river_names:list[str, list[str]]):

        reaches = self._get_reaches_in_sub(subbasin, river_names)
        out1 = self._get_outlet_reaches(subbasin, reaches[0])
        out2 = self._get_outlet_reaches(subbasin, reaches[1])

        newsub1 = self.watershed.create_virtual_subwatershed(out1, [out2])
        newsub2 = self.watershed.create_virtual_subwatershed(out2)

        return newsub1, newsub2

    def _split_hydrographs(self, subbasin:SubWatershed | str, river_names:list[str, list[str]]):
        """
        Séparation de l'hydrogramme partiel en fonction
        des surfaces drainées par chaque rivère

        On attend au maximum 2 rivières ou 1 rivière et une liste de rivières.

        Les rivières seront traitées 2 par 2 de façon récursive.

        La seconde rivière et l'affluent de la première rivière.

        """

        if isinstance(subbasin, str):
            subbasin = self.watershed.get_subwatershed(subbasin)

        sub1, sub2 = self._split_subwatershed(subbasin, river_names)

        fraction1 = sub1.area / subbasin.area
        fraction2 = sub2.area / subbasin.area

        assert fraction1 + fraction2 == 1., "Bad fractions"

        self.add_virtual_hydrograph(sub1.name, subbasin.name, fraction1, 0.)
        self.add_virtual_hydrograph(sub2.name, subbasin.name, fraction2, 0.)

        added = []
        added.append((sub1.name, river_names[0]))

        if isinstance(river_names[1], list):
            # Recursive call
            added.extend(self._split_hydrographs(sub2, river_names[1]))
        else:
            added.append((sub2.name, river_names[1]))

        return added

    def get_locale_injection_names(self):
        """ Print the names of the local injections """

        return list(self.locale_injections.keys())

    def get_along_injection_names(self) -> tuple[list[str], list[str]]:
        """ Get the names of the along injections

        :return: The names of the rivers along which the injections are made and the columns of the hydrographs
        """

        return list(self.lists_part.keys()), list(self.hydrographs_local.columns)

    def reset_injections(self):
        """ Reset the injections """

        self.counter_zone_infil = 0

        if self._infil_idx is not None:
            self._infil_idx.array[:,:] = 0

        self._hydrographs_virtual = []

        self.infiltrations = []
        self.local_infiltrations = {}

    def spread_infiltrations(self):
        """ Traite les injections """

        self.reset_injections()

        self.injections_locales()
        self.injections_along()

        self.create_hydrographs()

    def injections_locales(self, couplings:list[tuple[str, str, InjectionType]] = None):
        """ Ajoute les injections locales """

        if couplings is None:
            couplings = self._locales

        if couplings is None:
            logging.error(_("No local injections defined"))
            return

        for curinj in couplings:

            vec_name, col_name, injtype = curinj

            self._add_local_injecton(self.locale_injections[vec_name], injtype, col_name, 1., 0.)


    def link_area2nodes(self):
        """
        Searching cells in dem associated to the river nodes in the hydrological model.

        We use the river axis to select the cells in the dem.

        Then we search the nearest river nodes in the hydrological
        model.

        We create local lists of cells associated to one river node.

        Due to the fact that the river axis is not exactly the same
        as the river nodes (not the same spatial resolution, rester vs vector),
        all river nodes in the hydrological model
        are not necessarely associated to cells in the dem.

        """

        for key_river in self.rivers:

            river_axis = self._searching[key_river].river_axis
            kdtree = self._searching[key_river].kdtree
            nodes = self._searching[key_river].nodes

            # Mise à 0 des zones sélectionnées
            self._dem.SelectionData.reset()
            # Sélection des mailles sur l'axe du lit mineur
            self._dem.SelectionData.select_underpoly(river_axis)

            # Coordonnées XY des mailles sélectionnées
            xy_selected = self._dem.SelectionData.myselection

            # Recherche des mailles rivières les plus proches
            # dans la modélisation hydrologique
            dist, nearest = kdtree.query(xy_selected, k=1)
            # Récupération des noeuds correspondants aux index fournis par l'objet KDTree
            nearest:list[Node_Watershed] = [nodes[i] for i in nearest]

            # Surface drainée par les mailles
            drained_surface = np.array([cur.uparea for cur in nearest])

            # Valeurs de BV uniques
            unique_area = np.unique(drained_surface)

            # Création de listes contenant les mailles associé à chaque BV
            list_part = {}
            for cur_area in unique_area:
                idx = list(np.where(drained_surface == cur_area)[0])
                list_part[cur_area] = [xy_selected[i] for i in idx]

            self.lists_part[key_river] = (unique_area, list_part)

    def injections_along(self, along:list[str, str] = None):
        """ Injections along rivers """

        if along is None:
            along = self._along

        if along is None:
            logging.error(_("No along injections defined"))
            return

        along = along.copy()

        # ## Création de bassins virtuels afin de séparer les hydrogrammes en plusieurs rivières

        # Un sous-BV peut voir son hydrogramme partiel être réparti entre un rivière ou plusieurs rivières.

        # En cas de rivières multiples, la décomposition doit se faire 2 par 2:

        # - rivière principale
        # - rivière secondaire

        # La rivière secondaire peut également être décomposée en plusieurs selon le même principe.

        # **La procédure de calcul est récursive.**
        to_split = [cur for cur in along if isinstance(cur[1], list)]

        replace = []
        for cur in to_split:
            replace.extend(self._split_hydrographs(cur[0], cur[1]))

        for cur in to_split:
            along.remove(cur)

        for cur in replace:
            along.append(cur)

        for cur in along:
            self._injection_along(cur)

    def _injection_along(self, name_subwatershed_river:tuple[str, str]):

        # Nom de colonne et liste de mailles potentielles à utiliser
        # pour la répartition

        name_subwatershed, river = name_subwatershed_river

        list_rivers, used_reaches = self.lists_part[river], self._searching[river].downstream_reaches

        # sous-bassin
        subbasin = self.watershed.get_subwatershed(name_subwatershed)

        # Récupération des surfaces à utiliser pour l'injection en long
        unique_areas, lists = list_rivers
        unique_areas.sort()

        # traitement des injections locales si existantes dans le ss-bv
        # -------------------------------------------------------------

        # Recherche des zones d'injection locales dans le sous-bassin virtuel uniquement
        local_injections = subbasin.filter_zones(self._locale_injection_zones, force_virtual_if_any=True)

        # surfaces traitées par les injections ponctuelles
        local_areas = 0.
        # liste contenant la maille de connection au réseau et la maille d'injection locale
        to_remove:list[tuple[Node_Watershed, Node_Watershed, float]] = []

        for cur_locinj in local_injections:

            # Recherche du noeud rivière le plus proche de la zone d'injection locale
            dist, node_local_injection = self.river_system.get_nearest_nodes(cur_locinj)

            if node_local_injection.reach not in used_reaches:
                # Recherche de la maille rivière en aval
                # qui fait partie de la distribution en long
                down = self.river_system.go_downstream_until_reach_found(node_local_injection, used_reaches)
            else:
                # La zone d'injection ponctuelle est sur un des biefs à traiter
                # On cherche la première maille sur laquelle une distribution en long se fera
                down = node_local_injection
                while down is not None and down.uparea not in unique_areas:
                    down = down.down


            # surface su sous-bassin qui sera injectée localement
            local_area = node_local_injection.uparea - subbasin.get_area_outside_sub_if_exists(node_local_injection, node_local_injection.get_up_reaches_same_sub())

            # on retient la maille aval et la maille d'injection locale
            to_remove.append((down, node_local_injection, local_area))

            local_areas += local_area

            self._add_local_injecton(cur_locinj, InjectionType.PARTIAL if not subbasin._is_virtual else InjectionType.VIRTUAL, name_subwatershed, local_area / subbasin.area, 0.)

        # Incrément de BV à traiter pour l'injection en long
        # c-à-d la différence entre la surface drainée du ss-bv et la somme des surfaces locales
        delta_area = subbasin.area - local_areas

        # aire drainée en aval du sous-bassin
        area_max = subbasin.outlet.uparea

        # aire drainée à la limite amont du ss-bassin, le long de la distribution en long
        up_node = subbasin.get_up_rivernode_outside_sub(subbasin.outlet, used_reaches)

        if up_node is None:
            starting_node = subbasin.get_list_nodes_river(min(used_reaches))[-1]
            area_min = subbasin.get_area_outside_sub_if_exists(starting_node, starting_node.get_up_reaches_same_sub())
        else:
            area_min = up_node.uparea

        # On ne garde que la fraction utile des surfaces à traiter pour le ss-bv
        unique_areas = unique_areas[(unique_areas >= area_min) & (unique_areas<=area_max)]

        if unique_areas[0] != area_min:
            unique_areas = np.insert(unique_areas, 0, area_min)

        frac_sum=0.

        def area_to_remove(node:Node_Watershed) -> float:

            uparea = 0.

            # injections locales
            for node_down, node_inj, loc_area in to_remove:
                if node == node_down:
                    if node_inj.reach in used_reaches:
                        uparea += loc_area
                    else:
                        uparea += node_inj.uparea

            for node_up in node.upriver:
                if node_up.sub == node.sub:
                    if not subbasin.is_in_rivers(node_up):
                        uparea += node_up.uparea

            return uparea

        for idx in range(1,len(unique_areas)-1):

            up_node = subbasin.get_river_nodes_from_upareas(unique_areas[idx], unique_areas[idx])[0]
            delta_loc = unique_areas[idx] - unique_areas[idx-1] - area_to_remove(up_node)

            fraction_loc = delta_loc / delta_area

            if fraction_loc > 0.:

                self._add_along_injection(lists[unique_areas[idx]],
                                    InjectionType.PARTIAL if not subbasin._is_virtual else InjectionType.VIRTUAL,
                                    name_subwatershed,
                                    fraction_loc,
                                    lag =0.)

                frac_sum += fraction_loc
            elif fraction_loc < 0.:
                logging.error(f"Bad fraction {fraction_loc} " + name_subwatershed)

        delta_loc = area_max - unique_areas[-2] - area_to_remove(subbasin.outlet)

        fraction_loc = delta_loc / delta_area

        self._add_along_injection(lists[unique_areas[-1]],
                            InjectionType.PARTIAL if not subbasin._is_virtual else InjectionType.VIRTUAL,
                            name_subwatershed,
                            fraction_loc,
                            lag =0.)

        frac_sum += fraction_loc

        if frac_sum > 1.001 or frac_sum < 0.999:
            logging.error(f"Bad sum of fractions {frac_sum} " + name_subwatershed)


    def create_hydrographs(self):
        """ Création des hydrogrammes

        Les étapes précédentes ont ajouté à la liste "infiltrations" les éléments suivants:

        - l'index de la zone d'infiltration (1-based)
        - l'hydrogramme de référence
        - le facteur pondérateur
        - le temps de déphasage

        Une zone peut contenir plusieurs apports.

        Il faut donc parcourir l'ensemble des zones et sommer les contributions.

        Le fichier final est ordonné comme la matrice d'infiltration.

        Avant de sommer, il faut tout d'abord créer les hydrogrammes associés au BV virtuels (décomposition d'un BV, modélisé comme un tout, en plusieurs rivières distinctes pour la répartition en long)
        """

        dt = self.hydrographs_total.index[1] - self.hydrographs_total.index[0]

        # Création des hydrogrammes virtuels
        # Un hydrograme virtuel ne peut être créé que par des hydrogrammes partiels ou virtuels
        df_virtual = pd.DataFrame()
        df_virtual.index.name = 'Time'
        df_virtual.index = self.hydrographs_total.index

        for cur_vrt in self._hydrographs_virtual:
            name, src_hydrograph_name, factor, lag = cur_vrt

            decal = int(lag / dt)

            if src_hydrograph_name in self.hydrographs_local.columns:
                df_virtual[name] = self.hydrographs_local.shift(decal, fill_value=0.)[src_hydrograph_name] * factor

            elif src_hydrograph_name in df_virtual.columns:
                df_virtual[name] = df_virtual.shift(decal, fill_value=0.)[src_hydrograph_name] * factor

        df_2d_dict = {}
        df_2d_dict['Time'] = self.hydrographs_total.index

        nb_infil = max([cur.index for cur in self.infiltrations])

        counter = np.asarray([cur.index for cur in self.infiltrations])
        counter = [np.count_nonzero(counter == cur) for cur in range(1, nb_infil+1)]

        # FIXME : pas optimisé
        for i in range(1, nb_infil+1):
            # Bouclage sur les zones d'infiltation

            loc_count = 0

            for cur_infil in self.infiltrations:
                # Bouclage sur les infiltrations
                # En effet, plusieurs hydrogrammes peuvent être associés à une même zone

                idx, type_name, col_name, factor, lag = cur_infil.index, cur_infil.type, cur_infil.colref, cur_infil.factor, cur_infil.lagtime

                if idx == i:

                    decal = int(lag / dt)
                    loc_count += 1

                    if type_name == InjectionType.GLOBAL:

                        if loc_count == 1:
                            df_2d_dict[idx]  = self.hydrographs_total.shift(decal, fill_value = 0.)[col_name] * factor
                        else:
                            df_2d_dict[idx] += self.hydrographs_total.shift(decal, fill_value = 0.)[col_name] * factor

                    elif type_name == InjectionType.PARTIAL:

                        if loc_count == 1:
                            df_2d_dict[idx]  = self.hydrographs_local.shift(decal, fill_value = 0.)[col_name] * factor
                        else:
                            df_2d_dict[idx] += self.hydrographs_local.shift(decal, fill_value = 0.)[col_name] * factor

                    elif type_name == InjectionType.ANTHROPOGENIC:

                        if loc_count == 1:
                            df_2d_dict[idx]  = self.hydrographs_total.shift(decal, fill_value = 0.)[col_name] * factor
                        else:
                            df_2d_dict[idx] += self.hydrographs_total.shift(decal, fill_value = 0.)[col_name] * factor

                    elif type_name == InjectionType.VIRTUAL:

                        if loc_count == 1:
                            df_2d_dict[idx]  = df_virtual.shift(decal, fill_value = 0.)[col_name] * factor
                        else:
                            df_2d_dict[idx] += df_virtual.shift(decal, fill_value = 0.)[col_name] * factor

                    elif type_name == InjectionType.CONSTANT:

                        if loc_count == 1:
                            df_2d_dict[idx]  = np.asarray([col_name]*len(df_2d_dict[('Time')])) * factor
                        else:
                            df_2d_dict[idx] += col_name * factor

                    elif type_name == InjectionType.FORCED_UNSTEADY:

                        col_name:pd.Series
                        if loc_count == 1:
                            df_2d_dict[idx]  = col_name.loc[self.dateBegin:self.dateEnd].values * factor
                        else:
                            df_2d_dict[idx] += col_name.loc[self.dateBegin:self.dateEnd].values * factor

                    else:
                        logging.error(f"Unknown type {type_name}")

            if loc_count != counter[i-1]:
                logging.error(f"Bad count for {i}")

        self.df_2d = pd.DataFrame(df_2d_dict)
        self.df_2d.set_index('Time', inplace=True)


    def save_hydrographs(self, dirout:Path, name:str):
        """ Write the hydrographs

        :param dirout: The output directory
        :param name: The name of the output file (if no suffix .txt, it will be added)
        """

        # ensure suffix .txt
        if not name.endswith('.txt'):
            name += '.txt'

        locname = name.replace('.txt', '_infiltration_zones.txt')
        with open(dirout / locname, 'w') as f:
            f.write("Zone\tType\tColonne\tFacteur\tLag\n")
            for cur in self.infiltrations:
                idx, type_name, col_name, factor, lag = cur.index, cur.type.value, cur.colref, cur.factor, cur.lagtime
                f.write(f"{idx}\t{type_name}\t{col_name}\t{factor}\t{lag}\n")

        if self.df_2d is None:
            logging.error("No hydrographs created")
            return

        self.df_2d.to_csv(dirout / name, sep='\t', decimal='.', encoding='latin1')