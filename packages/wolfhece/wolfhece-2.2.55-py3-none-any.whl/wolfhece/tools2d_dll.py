from pathlib import Path
import numpy as np
import ctypes as ct
import logging

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


class Tools2DFortran:
    """
    Fortran routines/functions available in "2d_cpu_tools.f90" in Wolf_OO

    Ref : https://docs.python.org/3/library/ctypes.html et https://gcc.gnu.org/onlinedocs/gfortran/Interoperability-with-C.html
    Ref : https://stackoverflow.com/questions/59330863/cant-import-dll-module-in-python
    """

    def __init__(self, fn_simul:str | Path, debugmode:bool = False, path_to_dll:Path = None):

        if debugmode:
            if path_to_dll is None:
                # wolflibs directory
                self.dll_file = Path(wolf_libs.__path__[0]) / "Wolf_tools_debug.dll"
                # self.dll_file = Path(__file__).parent / "libs" / "Wolf_tools_debug.dll"
            else:
                self.dll_file = path_to_dll / "Wolf_tools_debug.dll"
        else:
            if path_to_dll is None:
                # wolflibs directory
                self.dll_file = Path(wolf_libs.__path__[0]) / "Wolf_tools.dll"
                # self.dll_file = Path(__file__).parent / "libs" / "Wolf_tools.dll"
            else:
                self.dll_file = path_to_dll / "Wolf_tools.dll"

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

        fn_simul = Path(fn_simul).absolute()

        self.fn_simul = str(fn_simul)

        if not Path(self.fn_simul).exists():
            logging.error(f"File {self.fn_simul} does not exist.")
            return

        # Convert to ANSI encoding - this is important for Fortran on Windows and Latin-1 encoding
        self.fn_simul = self.fn_simul.encode('ansi')

        # res2D_init
        self.lib.r2D_init.restype = None
        self.lib.r2D_init.argtypes = [ct.c_char_p, ct.c_int]

        self.lib.r2D_nbblocks.restype = ct.c_int
        self.lib.r2D_nbblocks.argtypes = []

        self.lib.r2D_header_block.restype = ct.c_int
        self.lib.r2D_header_block.argtypes = [
            ct.POINTER(ct.c_int),  # nbx
            ct.POINTER(ct.c_int),  # nby
            ct.POINTER(ct.c_double),  # ox
            ct.POINTER(ct.c_double),  # oy
            ct.POINTER(ct.c_double),  # tx
            ct.POINTER(ct.c_double),  # ty
            ct.POINTER(ct.c_double),  # dx
            ct.POINTER(ct.c_double),  # dy
            ct.c_int  # which_block
        ]

        self.lib.r2D_getsizes.restype = None
        self.lib.r2D_getsizes.argtypes = [
            ct.POINTER(ct.c_int),  # nbx
            ct.POINTER(ct.c_int),  # nby
            ct.c_int  # which_block
        ]

        self.lib.r2D_getnbresults.restype = ct.c_int
        self.lib.r2D_getnbresults.argtypes = []

        self.lib.r2D_getresults.restype = None
        self.lib.r2D_getresults.argtypes = [
            ct.c_int,  # which
            ct.c_int,  # nbx
            ct.c_int,  # nby
            ct.POINTER(ct.c_float),  # waterdepth
            ct.POINTER(ct.c_float),  # qx
            ct.POINTER(ct.c_float),  # qy
            ct.c_int  # which_block
        ]

        self.lib.r2D_getturbresults.restype = None
        self.lib.r2D_getturbresults.argtypes = [
            ct.c_int,  # which
            ct.c_int,  # nbx
            ct.c_int,  # nby
            ct.POINTER(ct.c_float),  # k
            ct.POINTER(ct.c_float),  # e
            ct.c_int  # which_block
        ]

        self.lib.r2D_get_times_steps.restype = None
        self.lib.r2D_get_times_steps.argtypes = [
            ct.POINTER(ct.c_float),  # times
            ct.POINTER(ct.c_int),  # steps
            ct.c_int  # nb
        ]

        self.lib.r2D_get_conv_border.restype = None
        self.lib.r2D_get_conv_border.argtypes = [
            ct.c_char_p,  # ptr_fnsim
            ct.c_char_p,  # ptr_fnvec
            ct.c_int,  # simul_type
            ct.c_char_p,  # ptr_fnres
            ct.c_char_p,  # ptr_fncut
            ct.c_int,  # len_fnsim
            ct.c_int,  # len_fnvec
            ct.c_int,  # len_fnres
            ct.c_int  # len_fncut
        ]


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

    def _r2D_init(self):
        """
        Alias for the Fortran function r2D_init.

        subroutine r2D_init(ptr_path, len_path) bind(C, name="r2d_init")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2d_init
            type(c_ptr), value, intent(in)          :: ptr_path
            integer(c_int), value, intent(in)       :: len_path

        end subroutine
        """
        self.lib.r2D_init(self.fn_simul, ct.c_int(len(self.fn_simul)))

    def r2D_get_number_of_blocks(self):
        """
        Alias for the Fortran function r2D_nbblocks.

        function r2D_nbblocks() result(nb_blocks) bind(C, name="r2D_nbblocks")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2D_nbblocks
            integer(c_int) :: nb_blocks

        end function
        """
        self._r2D_init()
        nb_blocks = self.lib.r2D_nbblocks()
        return nb_blocks

    def r2D_get_header_one_block(self, which_block:int):
        """
        Alias for the Fortran function r2D_header_block.

        function r2D_header_block(nbx, nby, dx,dy,ox,oy,tx,ty,which_block) result(ret) bind(C, name="r2D_header_block")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2D_header_block
            !DEC$ attributes REFERENCE :: nbx, nby
            !DEC$ attributes REFERENCE :: dx, dy, ox, oy, tx, ty
            !DEC$ attributes VALUE :: which_block
            integer(c_int) :: nbx,nby, ret
            double precision :: ox,oy,tx,ty,dx,dy
            integer(c_int), intent(in) :: which_block

        end function
        """

        self._r2D_init()
        nbx = ct.c_int()
        nby = ct.c_int()
        ox = ct.c_double()
        oy = ct.c_double()
        tx = ct.c_double()
        ty = ct.c_double()
        dx = ct.c_double()
        dy = ct.c_double()
        self.lib.r2D_header_block(ct.byref(nbx), ct.byref(nby), ct.byref(dx), ct.byref(dy),
                                    ct.byref(ox), ct.byref(oy), ct.byref(tx), ct.byref(ty), ct.c_int(which_block))

        return (nbx.value, nby.value, dx.value, dy.value, ox.value, oy.value, tx.value, ty.value)

    def _r2D_get_header_block_python(self, which_block:int) -> header_wolf:
        """ Return a header_wolf object with the header of the block number which_block."""
        nbx, nby, dx, dy, ox, oy, tx, ty = self.r2D_get_header_one_block(which_block)
        newhead = header_wolf()
        newhead.nbx = nbx
        newhead.nby = nby
        newhead.dx = dx
        newhead.dy = dy
        newhead.origin = ox, oy
        newhead.translation = tx, ty

        return newhead

    def r2D_get_header_allblocks(self):

        nbblocks = self.r2D_get_number_of_blocks()
        blocks = {}

        for i in range(1, nbblocks+1):
            key = getkeyblock(i, addone=False)
            blocks[key] = self._r2D_get_header_block_python(i)

        return blocks

    def r2D_get_shape(self, which_block:int):
        """
        Alias for the Fortran function r2D_getsizes.

        subroutine r2D_getsizes(nbx,nby,which_block) bind(C, name="r2D_getsizes")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2D_getsizes
            integer(c_int), intent(out) :: nbx,nby
            integer(c_int), intent(in) :: which_block

        end subroutine
        """

        self._r2D_init()
        nbx = ct.c_int()
        nby = ct.c_int()
        self.lib.r2D_getsizes(ct.byref(nbx), ct.byref(nby), ct.c_int(which_block))

        return nbx.value, nby.value


    def r2D_get_number_of_results(self):
        """
        Alias for the Fortran function r2D_getnbresults.

        function r2D_getnbresults() result(nb) bind(C, name="r2D_getnbresults")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2D_getnbresults
            integer(c_int) :: nb

        end function
        """

        self._r2D_init()
        nb = self.lib.r2D_getnbresults()
        return nb

    def r2D_get_one_result(self, which:int, which_block:int):
        """
        Alias for the Fortran function r2D_getresults.

        subroutine r2D_getresults(which,nbx,nby,waterdepth,qx,qy,which_block) bind(C, name="r2D_getresults")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2D_getresults
            integer(c_int), intent(in) :: nbx,nby,which
            integer(c_int), intent(in) :: which_block
            real, dimension(nbx,nby), intent(out) :: waterdepth,qx,qy

        end subroutine
        """

        self._r2D_init()

        nbx, nby = self.r2D_get_shape(which_block)
        waterdepth = np.zeros((nbx, nby), dtype=np.float32, order='F')
        qx = np.zeros((nbx, nby), dtype=np.float32, order='F')
        qy = np.zeros((nbx, nby), dtype=np.float32, order='F')

        self.lib.r2D_getresults(ct.c_int(which), ct.c_int(nbx), ct.c_int(nby),
                                waterdepth.ctypes.data_as(ct.POINTER(ct.c_float)),
                                qx.ctypes.data_as(ct.POINTER(ct.c_float)),
                                qy.ctypes.data_as(ct.POINTER(ct.c_float)),
                                ct.c_int(which_block))

        return waterdepth, qx, qy

    def r2D_get_one_turbulent_result(self, which:int, which_block:int):
        """
        Alias for the Fortran function r2D_getturbresults.

        subroutine r2D_getturbresults(which,nbx,nby,k,e,which_block) bind(C, name="r2D_getturbresults")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2D_getturbresults
            integer(c_int), intent(in) :: nbx,nby,which
            integer(c_int), intent(in) :: which_block
            real, dimension(nbx,nby), intent(out) :: k,e

        end subroutine
        """

        self._r2D_init()

        nbx, nby = self.r2D_get_shape(which_block)
        k = np.zeros((nbx, nby), dtype=np.float32, order='F')
        e = np.zeros((nbx, nby), dtype=np.float32, order='F')
        self.lib.r2D_getturbresults(ct.c_int(which), ct.c_int(nbx), ct.c_int(nby),
                                    k.ctypes.data_as(ct.POINTER(ct.c_float)),
                                    e.ctypes.data_as(ct.POINTER(ct.c_float)),
                                    ct.c_int(which_block))

        return k, e

    def r2D_get_times_steps(self):
        """
        Alias for the Fortran function get_times_steps.

        subroutine get_times_steps(times, steps, nb) bind(C, name="get_times_steps")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2D_gettimes_steps
            integer(c_int), intent(in) :: nb
            real, dimension(nb), intent(out) :: times
            integer, dimension(nb), intent(out) :: steps

        end subroutine
        """

        self._r2D_init()
        nb = self.r2D_get_number_of_results()
        times = np.zeros((nb), dtype=np.float32, order='F')
        steps = np.zeros((nb), dtype=np.int32, order='F')
        self.lib.r2D_get_times_steps(times.ctypes.data_as(ct.POINTER(ct.c_float)),
                                        steps.ctypes.data_as(ct.POINTER(ct.c_int)),
                                        ct.c_int(nb))
        return times, steps

    def r2D_create_convergence_border(self, vec:str='', simtype:int=0, res:str='', cutcell:str=''):
        """
        Alias for the Fortran function get_conv_border.

        subroutine get_conv_border(ptr_fnsim, ptr_fnvec, simul_type, ptr_fnres, ptr_fncut, len_fnsim, len_fnvec, len_fnres, len_fncut) bind(C, name="get_conv_border")
            !DEC$ ATTRIBUTES DLLEXPORT :: r2D_get_conv_border
            type(c_ptr), value, intent(in)          :: ptr_fnsim, ptr_fnvec, ptr_fnres, ptr_fncut
            integer(c_int), value, intent(in)       :: len_fnsim, len_fnvec, len_fnres, len_fncut

        end subroutine
        """

        fn_vec = str(vec).encode('ansi')
        fn_res = str(res).encode('ansi')
        fn_cutcell = str(cutcell).encode('ansi')

        self._r2D_init()
        self.lib.r2D_get_conv_border(self.fn_simul, fn_vec, simtype, fn_res, fn_cutcell,
                                      ct.c_int(len(self.fn_simul)),
                                      ct.c_int(len(fn_vec)),
                                      ct.c_int(len(fn_res)),
                                      ct.c_int(len(fn_cutcell)))

        return 0