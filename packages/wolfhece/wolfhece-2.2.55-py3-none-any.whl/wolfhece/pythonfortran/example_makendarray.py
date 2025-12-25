import numpy as np
import ctypes as ct
from tools import make_nd_array


def main():
    """
    Création d'un matrice numpy depui un buffer/adresse mémoire
    """

    a = np.zeros((10,10))

    # a.ctypes.data => int, buffer's memory address
    # see : https://numpy.org/doc/stable/reference/generated/numpy.ndarray.ctypes.html
    q = make_nd_array(a.ctypes.data, a.shape)

    #  récupération de la structure ct.pointer pointant vers l'espace de stockage de l'objet numpy "a"'
    p = a.ctypes.data_as(ct.POINTER(ct.c_double))
    #  récupération de l'adresse mémoire dans la structure ctypes.pointer
    addr_p = list(p.contents._b_base_._objects.values())[0].value
    # mais il y a plus simple ...
    addr_p_2 = ct.addressof(p.contents)

    assert addr_p == addr_p_2

    #  comparaison avec l'adresse mémoire du buffer de a
    print(addr_p, a.ctypes.data)
    assert a.ctypes.data == addr_p, 'Not the same address'

    c=make_nd_array(addr_p, [10,10], dtype=np.float64, own_data=False, readonly=False, order='F')
    d=make_nd_array(addr_p, [10,10], dtype=np.float64, own_data=True , readonly=False, order='F')

    e=make_nd_array(addr_p, [10,10], dtype=np.float64, own_data=False, readonly=True, order='F')
    f=make_nd_array(addr_p, [10,10], dtype=np.float64, own_data=True , readonly=True, order='F')
    g=make_nd_array(addr_p, [10,10], dtype=np.float64, own_data=True , readonly=False, order='F')

    assert c.ctypes.data == a.ctypes.data, 'Not the same address'
    assert d.ctypes.data != a.ctypes.data, 'Same address'

    assert e.flags.writeable == False, 'Array "e" is in read/write mode'
    assert f.flags.writeable == False, 'Array "f" is in read/write mode'
    assert g.flags.writeable == True,  'Array "g" is in read only mode'


    # Initialisation d'une Numpy array as 'C' order or 'F' order
    a = np.zeros((10,10), dtype=np.float64, order='C') # default order == 'C'
    a[:,1:]=3.

    h=make_nd_array(a.ctypes.data, [10,1], dtype=np.float64, own_data=True , readonly=False, order='F') # première ligne
    # h = [0,3,3,3,3,3,3,3,3,3,3]

    assert h.shape==(10,1)
    assert (h == np.asarray([[0.],[3.],[3.],[3.],[3.],[3.],[3.],[3.],[3.],[3.]])).all()

    a = np.zeros((10,10), dtype=np.float64, order='F')
    a[:,1:]=3.

    i=make_nd_array(a.ctypes.data, [10,1], dtype=np.float64, own_data=True , readonly=False, order='F') # première colonne
    # i = [0,0,0,0,0,0,0,0,0,0]

    assert i.shape==(10,1)
    assert (i == np.asarray([0.,0.,0.,0.,0.,0.,0.,0.,0.,0.])).all()
    assert (i == np.asarray([[0.],[0.],[0.],[0.],[0.],[0.],[0.],[0.],[0.],[0.]])).all()

if __name__ == '__main__':
    main()