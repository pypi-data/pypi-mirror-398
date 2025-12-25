from pathlib import Path
import sys
import os
import shutil
import logging

"""
Mandatory DLLs for MKL and Fortran.

MKL package and Fortran package installezd by pip
copy the DLLs to the Library/bin folder of Python.

This folder may not be in the PATH, so we need
to copy the DLLs to the wolfhece's libs folder.

Depending on the Python installation, the Library/bin
folder may be in different locations. We search for it
in the main directory of the Python interpreter and
in the different site-packages folder.

"""
MKL_DLLS = ['libiomp5md.dll',
            'mkl_core.2.dll',
            'mkl_intel_thread.2.dll',
            'mkl_rt.2.dll']
FORTRAN_DLLS = ['libifcoremd.dll',
                'libifcoremdd.dll',
                'libmmd.dll',
                'libifportmd.dll',
                'libmmdd.dll',
                'svml_dispmd.dll',
                'libiomp5md.dll']

from site import getsitepackages, getusersitepackages

def find_Librarybin(which, test):
    """ Searching Library/bin folder """

    interpreter_path = Path(sys.executable).parent
    sites = sys.path

    candidate = interpreter_path / 'Library/bin'
    logging.debug(f'Searching {which} in {candidate}')
    if candidate.exists():
        if (candidate/test).exists():
            logging.debug(f"Found {which} in {candidate}")
            return candidate

    candidate = interpreter_path.parent / 'Library/bin'
    logging.debug(f'Searching {which} in {candidate}')
    if candidate.exists():
        if (candidate/test).exists():
            logging.debug(f"Found {which} in {candidate}")
            return candidate

    for cursite in sites:
        if 'site-packages' in cursite:
            candidate = Path(cursite).parent.parent / 'Library/bin'
            logging.debug(f'Searching {which} in {candidate}')
            if candidate.exists():
                if (candidate/test).exists():
                    logging.debug(f"Found {which} in {candidate}")
                    return candidate

    return None

mkl_path = find_Librarybin('MKL', MKL_DLLS[0])
fortran_path = find_Librarybin('FORTRAN', FORTRAN_DLLS[0])

if mkl_path is None:
    logging.error("MKL package not found -- Please install MKL with 'pip install mkl'")
if fortran_path is None:
    logging.error("Fortran package not found -- Please install Intel Fortran RunTime with 'pip install intel_fortran_rt'")

if mkl_path is None or fortran_path is None:
    raise FileNotFoundError("Missing MKL or Fortran package. Please check the output above.")

mydir = Path(__file__).parent

error = False
if mkl_path.exists():
    for dll in MKL_DLLS:
        dll_path = mkl_path / dll
        if not dll_path.exists():
            error = True
            logging.error(f"Missing DLL: {dll} in {mkl_path}")
        else:
            if not (mydir / dll).exists():
                shutil.copy(dll_path, mydir / dll)

for dll in FORTRAN_DLLS:
    dll_path = fortran_path / dll
    if not dll_path.exists():
        error = True
        logging.error(f"Missing DLL: {dll} in {fortran_path}")
    else:
        if not (mydir / dll).exists():
            shutil.copy(dll_path, mydir / dll)

if error:
    raise FileNotFoundError("Missing DLLs. Please check the output above.")