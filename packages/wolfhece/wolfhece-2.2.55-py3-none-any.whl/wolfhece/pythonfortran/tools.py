import numpy as np
import ctypes as ct


def make_nd_array(memory_address_ptr, shape, dtype=np.float64, order='F', own_data=False, readonly=False):
    """
    Creating a Numpy object from a memory address (int)
    Using a function that creates a "buffer" structure from the memory address
    To complete the initialization, you also need to have the element arrangement "shape" and the memory size of an element "dtype"
    --
    Création d'un objet Numpy depuis une adresse mémoire (int)
    Utilisation d'une fonction qui crée une structure "buffer" depuis l'adresse mémoire
    Pour terminer l'initialisation, il faut également disposer de la disposition des éléments "shape" et de la taille mémoire d'un élément "dtype"

    --

    Args:
        memory_address_ptr (int): memory address - position of the first buffer element
        shape (integer): shape of the array
        dtype (numpy type, optional):  Defaults to np.float64.
        order (str, optional): 'C' row major order or 'F' column major order. Defaults to 'C'.
        own_data (bool, optional): If True, make a copy of the buffer. Defaults to True.
        readonly (bool, optional): If True, activate the Numpy writeable flag. Defaults to False.

    Returns:
        Numpy.ndarray
    """

    arr_size = np.prod(shape[:]) * np.dtype(dtype).itemsize # taille du buffer

    buf_from_mem = ct.pythonapi.PyMemoryView_FromMemory # pointage de la fonction PyMemoryView_FromMemory (see : https://docs.python.org/3/c-api/memoryview.html)
    buf_from_mem.restype = ct.py_object
    buf_from_mem.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
    if readonly:
        buffer = buf_from_mem(memory_address_ptr, arr_size, 0x100) # buffer en lecture seule, pointant sur l'adresse c_pointer
    else:
        buffer = buf_from_mem(memory_address_ptr, arr_size, 0x200) # buffer en lecture/écriture, pointant sur l'adresse c_pointer

    arr = np.ndarray(tuple(shape[:]), dtype, buffer, order=order,) # création d'un objet numpy exploitant le buffer précédent
    if own_data and not arr.flags.owndata:
        ret_arr = arr.copy()
        if readonly:
            ret_arr.flags.writeable = False

        return ret_arr # retour d'une copie --> NE PARTAGE PAS le même espace mémoire mais a été initialisé sur base des valeurs de la mémoire
    else:
        return arr # retour de l'objet Numpy --> PARTAGE le même espace mémoire