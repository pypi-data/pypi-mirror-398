import logging
from pathlib import Path
import numpy as np
from typing import Union, Literal
import matplotlib.pyplot as plt

from ..wolf_array import WOLF_ARRAY_FULL_LOGICAL, WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_UINTEGER8
from ..wolf_array import WolfArray, header_wolf
from ..PyTranslate import _
from ..PyVertexvectors import vector, zone, Zones
# from wolfgpu.simple_simulation import SimpleSimulation

class infiltration_GPU():
    def __init__(self, parent:"Sim_2D_GPU") -> None:
        self.parent:"Sim_2D_GPU" = parent

    @property
    def infiltrations_chronology(self) -> list[float]:
        chronos = self.parent.sim.infiltrations_chronology
        if len(chronos) == 0:
            return []
        else:
            return [[cur[0]]+cur[1] for cur in chronos]

    @infiltrations_chronology.setter
    def infiltrations_chronology(self, value:np.ndarray) -> None:

        simple_chronology = [(cur[0], list(cur[1:])) for cur in value]
        self.parent.sim.infiltrations_chronology = simple_chronology

    @property
    def nb_steps(self) -> int:
        chronos = self.parent.sim.infiltrations_chronology
        if len(chronos) == 0:
            return 0
        else:
            return len(chronos)

    @property
    def nb_zones(self) -> Zones:
        chronos = self.parent.sim.infiltrations_chronology
        if len(chronos) == 0:
            return 0
        else:
            if len(chronos[0]) == 0:
                return 0
            else:
                return len(chronos[0][1])

    def plot_plt(self, figax=None, show=True):
        """ Plot the infiltration data """

        if figax is None:
            fig, ax = plt.subplots(1, 1)
        else:
            fig,ax = figax

        chronos = self.parent.sim.infiltrations_chronology
        times = [cur[0] for cur in chronos]

        for zone in range(self.nb_zones):
            ax.plot(times, [cur[1][zone] for cur in chronos], label=f'Zone {zone+1}')

        ax.set_xlabel(_('Time [s]'))
        ax.set_ylabel(_('Infiltration [$m^3/s$]'))
        ax.legend()
        fig.tight_layout()

        if show:
            fig.show()

        return fig,ax


class Sim_2D_GPU():
    """ Simulation 2D GPU -- Interface """

    def __init__(self, directory:Union[str,Path] = '') -> None:

        try:
            from wolfgpu.simple_simulation import SimpleSimulation
        except:
            logging.error(_("Unable to import wolfgpu.simple_simulation.SimpleSimulation. Please install wolfgpu package or add a symlink to the wolfgpu package in the wolfhece directory"))

        self.dir = Path(directory)
        self._sim:SimpleSimulation = None
        self._cached_arrays = {}
        self.magnetic_grid:header_wolf = None

        if (self.dir /'parameters.json').exists():
            try:
                self._sim = SimpleSimulation.load(self.dir)
            except Exception as e:
                logging.error(_("Error loading simulation from directory {dir}: {error}").format(dir=self.dir, error=str(e)))
                logging.error(_("Please check your files and try again."))
                return

            try:
                self.infiltration = infiltration_GPU(self)
            except Exception as e:
                logging.error(_("Error initializing infiltration GPU: {error}").format(error=str(e)))

        # Fine arrays with type
        self.files_array={'Characteristics':[
            ('nap','Mask [-]',WOLF_ARRAY_FULL_UINTEGER8),
            ('bathymetry','Bed Elevation [m]',WOLF_ARRAY_FULL_SINGLE),
            ('manning','Roughness coefficient [law dependent]',WOLF_ARRAY_FULL_SINGLE),
            ('infiltration_zones','Infiltration zone [-]',WOLF_ARRAY_FULL_INTEGER),
            ('h','Initial water depth [m]',WOLF_ARRAY_FULL_SINGLE),
            ('qx','Initial discharge along X [m^2/s]',WOLF_ARRAY_FULL_SINGLE),
            ('qy','Initial discharge along Y [m^2/s]',WOLF_ARRAY_FULL_SINGLE),
            ('bridge_roof','Bridge/Culvert (roof el.) [m]',WOLF_ARRAY_FULL_SINGLE),
            ('water_surface_elevation','Water surface elevation [m]',WOLF_ARRAY_FULL_SINGLE),
        ]}

        self.files_ic=['Initial water depth [m]',
                       'Initial discharge along X [m^2/s]',
                       'Initial discharge along Y [m^2/s]']

        # Files for the simulation
        self.files_others={'Generic file':[
            ('parameters.json','Parametric file'),
            ]}

        pass

    @property
    def boundary_condition(self):
        return self.sim.boundary_condition

    @property
    def is_loaded(self) -> bool:
        return self.sim is not None

    def unload(self) -> None:
        """ Unload the simulation """
        if self.is_loaded:
            del self._sim
            self._sim = None

    @property
    def sim(self):
        return self._sim

    @sim.setter
    def sim(self, value) -> None:
        self._sim = value

    def __str__(self) -> str:
        ret = f"Simulation 2D GPU: {self.dir.name}\n"
        if self.is_loaded:
            ret += str(self.sim)
        return ret

    def __repr__(self) -> str:
        return self.__str__()

    def _get_name_arrays(self) -> list[str]:
        """ Get the name of the arrays """
        return [cur[0] for cur in self.files_array['Characteristics']]

    def _get_description_arrays(self) -> list[str]:
        """ Get the description of the arrays """
        return [cur[1] for cur in self.files_array['Characteristics']]

    def get_header(self) -> header_wolf:
        """ Get the header of the simulation """
        if self.is_loaded:
            new_header = header_wolf()
            new_header.nbx = self.sim.param_nx
            new_header.nby = self.sim.param_ny
            new_header.dx = self.sim.param_dx
            new_header.dy = self.sim.param_dy
            new_header.origx = self.sim.param_base_coord_ll_x
            new_header.origy = self.sim.param_base_coord_ll_y

            return new_header
        else:
            return None

    def __getitem__(self, key:Literal['nap', 'bathymetry',
                                      'manning', 'infiltration_zones',
                                      'h', 'qx', 'qy',
                                      'bridge_roof',
                                      'water_surface_elevation']) -> WolfArray:
        """ Get an array from the simulation """

        if self.is_loaded:
            if key in self._get_name_arrays():
                descr = self._get_description_arrays()[self._get_name_arrays().index(key)]

                if key not in self._cached_arrays:
                    if key in ['water_surface_elevation']:

                        top = self['bathymetry']
                        h = self['h']

                        locarray = top + h
                        locarray.idx = descr
                        locarray.nullvalue = self.nullvalues[key]

                        def wse_write_all():
                            top = self['bathymetry']
                            new_h = self['water_surface_elevation'] - top

                            # Filter negative values
                            new_h.array.data[new_h.array.data < 0.] = 0.

                            new_h.write_all(str(self.dir / "h.npy"))

                        locarray.write_all = wse_write_all

                    else:
                        locarray = WolfArray(srcheader=self.get_header(),
                                            np_source=self.sim.__getattribute__(key),
                                            idx= descr,
                                            nullvalue=self.nullvalues[key],
                                            whichtype=self.files_array['Characteristics'][self._get_name_arrays().index(key)][2],
                                            masknull=False)
                    locarray.loaded = True
                    locarray.filename = str(self.dir / f"{key}.npy")

                    self._cached_arrays[key] = locarray
                    return locarray
                else:
                    return self._cached_arrays[key]
            else:
                return None
        else:
            return None

    def get_arraysasdict(self) -> dict[str,WolfArray]:
        """ Get all the arrays from the simulation """

        ret= {key:self[key] for key in self._get_name_arrays()}
        self.mimic_mask(ret['nap'], [cur for key,cur in ret.items() if key != 'nap'])

        return ret


    def mimic_mask(self, source:WolfArray, dest:list[WolfArray]):
        """ Mimic the mask """

        for cur in dest:
            cur.array.mask[:,:] = source.array.mask[:,:]
            cur.set_nullvalue_in_mask()

    def create_arrays_from(self, source:WolfArray):
        """ Create arrays from a source """

        try:
            from wolfgpu.simple_simulation import SimpleSimulation
        except:
            logging.error(_("Unable to import wolfgpu.simple_simulation.SimpleSimulation. Please install wolfgpu package or add a symlink to the wolfgpu package in the wolfhece directory"))

        if self.is_loaded:
            logging.error(_("Simulation exists, cannot create arrays from source or delete simulation first !"))
        else:
            try:
                self._sim = SimpleSimulation(source.nbx, source.nby)
                self._sim.param_dx = source.dx
                self._sim.param_dy = source.dy
                self._sim.param_base_coord_ll_x = source.origx
                self._sim.param_base_coord_ll_y = source.origy
                self.infiltration = infiltration_GPU(self)
            except Exception as e:
                logging.error(_("Unable to create simulation  -- {e}"))
                return

            # Float32 arrays
            loc_array = np.zeros((source.nbx, source.nby), dtype=np.float32)
            self.sim.h = loc_array.copy()
            self.sim.qx = loc_array.copy()
            self.sim.qy = loc_array.copy()

            self.sim.manning = loc_array.copy()
            self.sim.manning[np.logical_not(source.array.mask)] = 0.04

            loc_array[source.array.mask] = 99999.
            self.sim.bathymetry = loc_array.copy()

            # UInteger8 arrays
            loc_array = np.ones((source.nbx, source.nby), dtype=np.uint8)
            loc_array[source.array.mask] = 0
            self.sim.nap = loc_array.copy()

            # Integer arrays
            loc_array = np.zeros((source.nbx, source.nby), dtype=np.int32)
            self.sim.infiltration_zones = loc_array.copy()


    def create_from_vector(self, vector:vector, dx:float, dy:float):
        """ Create a simulation from a vector """

        if vector is None:
            logging.warning(_("Vector is None"))
            return None
        elif self.magnetic_grid is None:
            logging.error(_("Magnetic grid not set"))
            return None
        else:
            vector.find_minmax()
            xmin, ymin = vector.xmin, vector.ymin
            xmax, ymax = vector.xmax, vector.ymax

            xmin, ymin = self.align2grid(xmin, ymin)
            xmax, ymax = self.align2grid(xmax, ymax)

            xmin -= 2*dx
            ymin -= 2*dy
            xmax += 2*dx
            ymax += 2*dy

            src_header = header_wolf()
            src_header.dx = dx
            src_header.dy = dy
            src_header.origx = xmin
            src_header.origy = ymin
            src_header.nbx = int((xmax-xmin)/src_header.dx)
            src_header.nby = int((ymax-ymin)/src_header.dy)

            tmp_array = WolfArray(srcheader=src_header)
            ij = tmp_array.get_ij_inside_polygon(vector, usemask=False)

            tmp_array.mask_reset()
            tmp_array.mask_outsidepoly(vector)
            self.create_arrays_from(tmp_array)

    def create_from_array(self, array:WolfArray):
        """ Create a simulation from an array """
        if array is None:
            logging.warning(_("Array is None"))
            return None
        else:
            self.create_arrays_from(array)

    def create_from_header(self, header:header_wolf) -> 'Sim_2D_GPU':
        """ Create a simulation from a header """
        if header is None:
            logging.warning(_("Header is None"))
            return None
        else:
            tmp_array = WolfArray(srcheader=header)
            tmp_array.array[:,0] = 0
            tmp_array.array[0,:] = 0
            tmp_array.array[-1,:] = 0
            tmp_array.array[:,-1] = 0
            tmp_array.masknull()
            self.create_arrays_from(tmp_array)

    def set_mesh_size(self, dx, dy):
        """ Set the mesh size """
        if self.is_loaded:
            self.sim.param_dx = dx
            self.sim.param_dy = dy
        else:
            logging.error(_("Simulation not loaded"))

    def set_magnetic_grid(self, dx:float, dy:float, origx:float, origy:float):
        """
        Définition de la grille magnétique

        :param dx: taille de maille selon X
        :type dx: float
        :param dy: taille de maille selon Y
        :type dy: float
        :param origx: origine selon X (coordonnée du noeud d'intersection)
        :type origx: float
        :param origy: origine selon Y (coordonnée du noeud d'intersection)
        :type origy: float
        """

        self.magnetic_grid = header_wolf()
        self.magnetic_grid.dx = dx
        self.magnetic_grid.dy = dy

        self.magnetic_grid.origx = origx
        self.magnetic_grid.origy = origy

    def align2grid(self, x:float, y:float):
        """ Alignement sur la grille magnétique """

        if self.magnetic_grid is None:
            return x,y

        x, y = self.magnetic_grid.align2grid(x, y)

        return x,y

    @property
    def nullvalues(self) -> dict[str,int]:
        """ Define null values for the arrays """

        return {'nap':0,
                'bathymetry':99999.,
                'manning':0,
                'infiltration_zones':0,
                'h':0.,
                'qx':0.,
                'qy':0.,
                'bridge_roof':99999.,
                'water_surface_elevation':0.}

    def verify_files(self):
        """ Verify the files """

        if self.is_loaded:
            header = self.get_header()
            ref_mask= self.sim.nap == 0
            for cur in self.files_array['Characteristics']:
                tmparray = self.sim.__getattribute__(cur[0])
                if tmparray is None:
                    logging.error(_("Missing array: {0}".format(cur[0])))
                    return False
                if tmparray.shape != (header.nbx, header.nby):
                    logging.error(_("Bad shape for array {0}".format(cur[0])))
                    return False
                if np.any(tmparray[np.logical_not(ref_mask)] == self.nullvalues[cur[0]]):
                    logging.error(_("Null value found in array {0}".format(cur[0])))
                    return False
            return True
        else:
            return False


    def get_wizard_text(self, lang:str = 'en') -> str:
        """ Get the wizard text """

        wizard_steps_page1 =[
            '',
            '',
            '',
            _('Welcome to the wizard'),
            '',
            '',
            '',
            _('This wizard will guide you through the creation\nof a new simple GPU WOLF2D model'),
            '',
        ]

        wizard_steps_page2 = [
            _('First of all, you need to define the model domain'),
            '',
            _('You can create a new polygon or select an existing one'),
            '',
            _('You can also create a polygon from a footprint by defining : \n   - the origin (ox, oy)\n   - the resolution (dx, dy)\n   - the number of nodes along X and Y (nbx, nby)'),
            '',
            _('Or you can use a mask from the active array  (e.g. a topography array)'),
            "",
            _('Remember that the extrnal contour cells will be forced as masked'),
        ]


        wizard_steps_page3 = [
            _('If you are working with a polygon, you must set the magnetic grid'),
            '',
            _('The magnetic grid is a virtual grid on which the array bounds are aligned'),
            '',
            _('The xmin, ymin, xmax, ymax of the polygon will be aligned on the magnetic grid'),
            '',
            _('It could be useful to have consistent boundaries between different simulations\n(e.g. successive river reaches)'),
        ]


        wizard_steps_page4 = [
            _('Then the model will be meshed and the arrays will be created'),
            '',
            _('Meshing is the process of creating the mesh of the model'),
            '',
            _('The mesh is the grid of nodes and elements on which the model will be solved'),
            '',
            _('Resulting mesh is stored in the NAP.npy file'),
            '',
            _('1 is an active cell and 0 is an inactive cell'),
        ]

        wizard_steps_page5 = [
            _('Then you can modify the arrays'),
            '',
            _('Arrays are the main data of the model'),
            '',
            _('They are created from the meshing results (bathymetry, manning, h, qx, qy, infiltration_zones)'),
            '',
            _('They are stored in the binary files\nExtensions .npy'),
            '',
            _('Specific types are used for each array :'),
            _('  - nap : Unsigned integer - 8 bits'),
            _('  - bathymetry, manning, h, qx, qy : Float 32 bits (Single precision)'),
            _('  - infiltration_zones : Signed integer - 16 bits'),
            '',
            _('Arrays can be edited in the GUI'),
        ]

        wizard_steps_page6 = [
            _('Set the boundary conditions'),
            '',
            _('You can set the boundary conditions for the model'),
            '',
            _('Borders of the NAP array are identified as boundaries'),
            '',
            _('By mouse, you can select borders one by one (right click), or by using dynamic rectangle (right click and drag)'),
            '',
            _('Select type and values for the selected borders in the BC Manager associated to the simulation'),
        ]

        wizard_steps_page7 = [
            _('Set the infiltrations'),
            '',
            _('Infiltrations must be defined spatially and temporally'),
            '',
            _('Spatially, you must edit the infiltration zones array and set an index for the cells in each zone'),
            '',
            _('Temporally, you must define the chronology of the infiltrations of each zone'),
            '',
            _('The discharge is defined in m3/s'),

        ]

        wizard_steps_page8 = [
            _('Set the parameters'),
            '',
            _('You can set the parameters for the model'),
        ]

        wizard_steps_page9 = [
            _('Check errors and write the files'),
            '',
            _('The warnings and errors are displayed in the text area'),
            '',
            _('You can write the files if no errors are found'),
        ]

        wizard_steps_page10 = [
            _('Run the code'),
            '',
            _('You can run the code in a subprocess or manually (more flexible to choose cli options)'),
        ]

        wizard_steps_page11 = [
            _('View/Check the results'),
        ]

        wizard_steps_page12 = [
            _('That\'s all folks !'),
        ]

        return [wizard_steps_page1, wizard_steps_page2, wizard_steps_page3, wizard_steps_page4, wizard_steps_page5, wizard_steps_page6, wizard_steps_page7, wizard_steps_page8, wizard_steps_page9, wizard_steps_page10, wizard_steps_page11, wizard_steps_page12]

    def bc2txt(self) -> str:
        """" Get the text for the boundary conditions Manager """

        txt = str(len(self.boundary_condition)) +"\n"
        for curbc in self.boundary_condition:
            txt += f"{curbc.i}\t{curbc.j}\t{curbc.direction.value}\t{curbc.ntype.value}\t{curbc.val}\n"

        return txt

    def check_infiltration(self) -> str:
        """
        Informations sur les zones d'infiltration :
          - nombre de zones dans la simulation
          - nombre de cellules de chaque zone
          - première maille de chaque zone
          - nombre de temps énumérés dans le fichier .fil
          - Warning si le nombre de zones est différent entre les fichiers .inf et .fil

        """

        ret =  _('inside file') + '\n'
        ret +=  ('-----------') + '\n'

        inf = self.sim.infiltration_zones

        maxinf = inf.max()
        ret += _('Maximum infiltration zone : ') + str(maxinf) + '\n'
        for i in range(1,maxinf+1):

            nb = np.sum(inf == i)
            if nb>0:
                indices = np.where(inf == i)
                ret += f"Zone {i} : {nb} cells -- Indices (i,j) of the zone's first cell ({indices[0][0]+1} ; {indices[1][0]+1}) (1-based)\n"
            else:
                ret += f"Zone {i} : 0 cells\n"

        ret += '\n'

        ret += _('inside chronology') + '\n'
        ret +=  ('-----------------') + '\n'

        ret += f"Zones : {self.infiltration.nb_zones}" + '\n'
        ret += f"Time steps : {self.infiltration.nb_steps}" + '\n'

        if maxinf != self.infiltration.nb_zones:
            ret += _('Warning : number of zones in chronology and array are different') + '\n'

        return ret

    def check_environment(self) -> list[str]:
        # Info on Python Environment and wolfgpu Path and version
        # -------------------------------------------------------

        import sys
        # Python Environment
        ret = []
        ret.append('  - Python version : {}'.format(sys.version))
        ret.append('  - Python path : {}'.format(sys.executable))
        ret.append('  - Python version info : {}'.format(sys.version_info))

        # Test if wolfgpu.exe exists in script directory
        # wolfgpu Path and version
        PythonPath = Path(sys.executable)
        site_packages = PythonPath.parent.parent / 'Lib' / 'site-packages'
        wolfgpu_path = PythonPath.parent / 'wolfgpu.exe'
        if wolfgpu_path.exists():
            ret.append('  - Wolfgpu.exe found in : {}'.format(wolfgpu_path))
        else:
            ret.append('  - Wolfgpu.exe not found !')

        if (site_packages / 'wolfgpu').exists():
            ret.append('  - Wolfgpu package found in : {}'.format(site_packages / 'wolfgpu'))
        else:
            ret.append('  - Wolfgpu package not found in : {}!'.format(site_packages))

        return ret

    def run(self, limit_dryuploops:int= -1):
        """ run the simulation in a subprocess """
        from subprocess import run, Popen

        if self.is_loaded:
            if limit_dryuploops > 0:
                Popen(['wolfgpu', '-quickrun', str(self.dir), '-limit_dryuploops', str(limit_dryuploops)], shell=False)
            else:
                Popen(['wolfgpu', '-quickrun', str(self.dir)], shell=False)
            pass
        else:
            logging.error(_("Simulation not loaded"))

    def write_initial_condition_from_record(self, recpath:Path = None, id_rec:int = None, destpath:Path = None):
        """ Write the initial condition from a record

        :param recpath: the path to the records. if None, the default path is used and 'simul_gpu_results' as result directory.
        :param id_rec: the index of the record you want to start from.
        :param destpath: the path where to save the initial condition. If None, the current path is used.

        """

        if self.is_loaded:
            self.sim.write_initial_condition_from_record(recpath, id_rec, destpath)
        else:
            logging.error(_("Simulation not loaded"))

    def copy2dir(self, destpath:Path):
        """ Copy the simulation to a directory """

        if self.is_loaded:
            try:
                self.sim.save(destpath)
            except Exception as e:
                logging.error(_("Unable to copy simulation -- {e}"))
        else:
            logging.error(_("Simulation not loaded"))


    def reload_ic(self):
        """ Reload the initial conditions from the disk and store ir in the same memory space. """
        tmp = np.load(self.dir / "h.npy")
        self.sim._h[:,:]= tmp[:,:]

        tmp = np.load(self.dir / "qx.npy")
        self.sim._qx[:,:]= tmp[:,:]

        tmp = np.load(self.dir / "qy.npy")
        self.sim._qy[:,:]= tmp[:,:]

    def reload_all(self):
        """ Reload all the data from the disk and store them in the same memory space. """
        tmp = np.load(self.dir / "h.npy")
        self.sim._h[:,:] = tmp[:,:]

        tmp = np.load(self.dir / "qx.npy")
        self.sim._qx[:,:] = tmp[:,:]

        tmp = np.load(self.dir / "qy.npy")
        self.sim._qy[:,:]= tmp[:,:]

        tmp = np.load(self.dir / "bathymetry.npy")
        self.sim._bathymetry[:,:]= tmp[:,:]

        tmp = np.load(self.dir / "manning.npy")
        self.sim._manning[:,:]= tmp[:,:]

        tmp = np.load(self.dir / "infiltration_zones.npy")
        self.sim._infiltration_zones[:,:]= tmp[:,:]

        tmp = np.load(self.dir / "NAP.npy")
        self.sim._nap[:,:]= tmp[:,:]