import numpy as np
import ctypes as ct
from tools import make_nd_array

def main():
    """
    Les matrices Numpy gardent-elles le même espace mémoire (buffer) lors des opérations méthématiques ??
    Une tentative d'analyse sur base de quelques exemples simples ...

    ATTENTION notammment à :
    - la diférence de comportement entre "a += 3" et "a = a + 3"
    - la diférence de comportement entre "a[:,:] = a[:,:] + 3" et "a = a + 3"

    Lire : https://numpy.org/doc/stable/reference/ufuncs.html
    """
    a = np.zeros((10,10))
    b = a # b is an alias --> share memory
    c = a.copy() # c is a copy --> not share memory

    id_a = id(a) # memory address
    id_b = id(b) # memory address
    id_c = id(c) # memory address

    if id(b) == id(a):
        print('1) a vs b - egalize -- Same memory address')

    if id(c) != id(a):
        print('2) a vs c - egalize copy -- Not the same memory address')

    c+=4
    a=c.copy()
    if id_a != id(c):
        print('3) a vs a (from c) - egalize copy -- Not the same memory address')

    # reset
    a=b

    a += 3
    id_newa = id(a) # memory address
    if id_newa == id_a:
        print('4) a vs a - += 3 -- Same memory address')

    a[:,:] = a[:,:] + 3
    id_newa = id(a) # memory address

    if id_newa == id_a:
        print('5) a vs a - [:,:] + 3 -- Same memory address')

    a = a + 3
    id_newa2 = id(a) # memory address
    if id_newa2 != id_a:
        print('6) a vs new_a_2 - = +3 -- Not the same memory address')

    b = a + 3
    if id(b) != id(a):
        print('7) a vs b - addition -- Not the same memory address')

    # Adresse mémoire

    a = np.zeros((10,10), dtype=np.float64)
    mem_a = a.ctypes.data
    a[:,1:]=3.
    assert mem_a == a.ctypes.data


    # Créez deux matrices numpy distinctes avec des buffers mémoire séparés
    matrix1 = np.array([[1, 2], [3, 4]])
    matrix2 = np.array([[5, 6], [7, 8]])

    buf_m1 = matrix1.ctypes.data
    buf_m2 = matrix2.ctypes.data

    # Copiez le contenu de matrix1 dans matrix2 (les buffers de matrix2 ne sont pas affectés)
    matrix2[:] = matrix1

    assert buf_m1 == matrix1.ctypes.data
    assert buf_m2 == matrix2.ctypes.data
    assert (matrix1 ==matrix2).all()

    matrix1 = np.array([[1, 2], [3, 4]])
    matrix2 = np.array([[5, 6], [7, 8]])

    buf_m1 = matrix1.ctypes.data
    buf_m2 = matrix2.ctypes.data

    # Copiez le contenu de matrix1 dans matrix2 (les buffers de matrix2 ne sont pas affectés)
    matrix2[:] = matrix1.copy()

    assert buf_m1 == matrix1.ctypes.data
    assert buf_m2 == matrix2.ctypes.data
    assert (matrix1 ==matrix2).all()

    matrix1 = np.array([[1, 2], [3, 4]])
    matrix2 = np.array([[5, 6], [7, 8]])

    buf_m1 = matrix1.ctypes.data
    buf_m2 = matrix2.ctypes.data

    # Copiez le contenu de matrix1 dans matrix2 (les buffers de matrix2 SONT affectés)
    matrix2 = matrix1.copy()

    assert buf_m1 == matrix1.ctypes.data
    assert buf_m2 != matrix2.ctypes.data
    assert matrix2.ctypes.data != matrix1.ctypes.data
    assert (matrix1 ==matrix2).all()

    matrix1 = np.array([[1, 2], [3, 4]])
    matrix2 = np.array([[5, 6], [7, 8]])

    buf_m1 = matrix1.ctypes.data
    buf_m2 = matrix2.ctypes.data

    # Copiez le contenu de matrix1 dans matrix2 (les buffers de matrix2 SONT affectés)
    matrix2 = matrix1

    assert buf_m1 == matrix1.ctypes.data
    assert buf_m2 != matrix2.ctypes.data
    assert matrix2.ctypes.data == matrix1.ctypes.data
    assert (matrix1 ==matrix2).all()

if __name__ == "__main__":
    main()