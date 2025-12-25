from pathlib import Path
import numpy as np
import ctypes as ct
import logging
import shutil

import wolf_libs
from .wolf_array import header_wolf, getkeyblock

from .os_check import isWindows

# Check if the platform is Windows
if not isWindows():
    raise OSError("This module is only compatible with Windows.")

try:
    import pefile
except ImportError:
    logging.warning("pefile module not found. Exported functions will not be listed.")


class ToolsHydrologyFortran:
    """
    Fortran routines/functions available in "WolfHydrology.f90" in Wolf_OO

    Ref : https://docs.python.org/3/library/ctypes.html et https://gcc.gnu.org/onlinedocs/gfortran/Interoperability-with-C.html
    Ref : https://stackoverflow.com/questions/59330863/cant-import-dll-module-in-python
    """

    def __init__(self, dir_simul:str | Path, debugmode:bool = False, path_to_dll:Path = None):

        if debugmode:
            if path_to_dll is None:
                # wolflibs directory
                self.dll_file = Path(wolf_libs.__path__[0]) / "WolfHydrology_debug.dll"
                # self.dll_file = Path(__file__).parent / "libs" / "WolfHydrology_debug.dll"
            else:
                self.dll_file = path_to_dll / "WolfHydrology_debug.dll"
        else:
            if path_to_dll is None:
                # wolflibs directory
                self.dll_file = Path(wolf_libs.__path__[0]) / "WolfHydrology.dll"
                # self.dll_file = Path(__file__).parent / "libs" / "WolfHydrology.dll"
            else:
                self.dll_file = path_to_dll / "WolfHydrology.dll"

            self.dll_file = self.dll_file.absolute()

        if not Path(self.dll_file).exists():
            logging.error(f"File {self.dll_file} does not exist.")
            return

        # Load the DLL
        try:
            self.lib = ct.CDLL(str(self.dll_file))
        except OSError as e:
            logging.error(f"Could not load the DLL: {e}")
            return

        dir_simul = Path(dir_simul).absolute()

        self.dir_simul = str(dir_simul)

        if not Path(self.dir_simul).exists():
            logging.error(f"File {self.dir_simul} does not exist.")
            return

        self._dir = Path(self.dir_simul)

        # Convert to ANSI encoding - this is important for Fortran on Windows and Latin-1 encoding
        self.dir_simul = self.dir_simul.encode('ansi')

        # Set the directory for the Fortran routines
        self.lib.set_directory_filename.restype = None
        self.lib.set_directory_filename.argtypes = [ct.c_char_p, ct.c_char_p, ct.c_char_p, ct.c_char_p,
                                                    ct.c_int, ct.c_int, ct.c_int, ct.c_int]

        self.lib.write_default_parameters.restype = None
        self.lib.write_default_parameters.argtypes = None

        self.lib.init_hydrological_model.restype = None
        self.lib.init_hydrological_model.argtypes = None

    def set_directory(self):
        """
        Set the directory and filename for the Fortran routines.
        """

        dir_simul = self.dir_simul
        file_name = 'simul'.encode('ansi')
        dir_results = dir_simul
        file_results = file_name

        self.lib.set_directory_filename(dir_simul, file_name,
                                        dir_results, file_results,
                                        ct.c_int(len(dir_simul)),
                                        ct.c_int(len(file_name)),
                                        ct.c_int(len(dir_results)),
                                        ct.c_int(len(file_results)))

    def create_default_parameters(self):
        """
        Write the default parameters for the Fortran routines.
        This will create a file named "test_opti.param" in the working directory.
        """
        self.set_directory()
        self.lib.write_default_parameters()

        default = 'Main_model.param.default'
        default = self._dir / default
        if default.exists():
            # Make a copy wihout the .default extension
            new_default = default.with_suffix('')
            shutil.copyfile(default, new_default)
            logging.info(f"Default parameters copied to {new_default}")
        else:
            logging.warning(f"Default parameters file {default} does not exist. No copy made.")

        default = 'Drainage_basin.param.default'
        default = self._dir / 'Characteristic_maps' / default
        if default.exists():
            # Make a copy wihout the .default extension
            new_default = default.with_suffix('')
            shutil.copyfile(default, new_default)
            logging.info(f"Default DB parameters copied to {new_default}")
        else:
            logging.warning(f"Default DB parameters file {default} does not exist. No copy made.")

    def run_preprocessing(self):
        """
        Run the preprocessing of the hydrology model.
        This will create the characteristic maps and the whole basin data.
        """
        self.set_directory()
        self.lib.init_hydrological_model()

    def _list_exported_functions(self):
        """
        Fortran routines/functions available in
        """

        pe = pefile.PE(self.dll_file)

        if not hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
            print("No exported functions found.")
            return

        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            print(f"Function: {exp.name.decode('utf-8') if exp.name else 'None'}, Address: {hex(exp.address)}")
