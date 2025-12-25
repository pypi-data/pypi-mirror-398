import numpy as np

def junction_q_lagrangemult(q:np.ndarray):
    """ Compute the junction flow rate q_junction
    from the flow rates q of the branches.

    :param q: np.ndarray, estimated signed flow rates of the branches
    """

    # Number of incoming branches
    n = q.size
    
    # Compute the flow rate ensuring mass conservation
    # using the Lagrange multiplier method 
    #
    # We minimize the following function:
    #   sum_{i=1}^{n} 1/2 * (qnew_i - q_i) ** 2 
    # subject to the constraint:
    #   sum_{i=1}^{n} qnew_i
    #
    # The solution is given by inversing the matrix A
    # A = [1 1 1 ... 1 0]
    #     [1 0 0 ... 0 1]
    #     [0 1 0 ... 0 1]
    #     [0 0 1 ... 0 1]
    #     ...
    #     [0 0 0 ... 1 1]
    # 
    # [lambda qnew] = A^(-1) * [0 q1 q2 ... qn]

    # Create the matrix A
    A = np.zeros((n+1, n+1))
    A[0, :-1] = 1
    A[1:, :-1] = np.eye(n)
    A[1:, -1] = 1

    # Compute the inverse of A
    A_inv = np.linalg.inv(A)

    # Compute the new flow rates
    qnew = A_inv @ np.concatenate(([0], q))

    # Return the junction flow rates and the lambda
    return qnew[:n], qnew[-1]

def junction_wse_head_lagrangemult(q:np.ndarray, 
                                     a:np.ndarray, 
                                     h_width_froma, 
                                     z:np.ndarray, 
                                     epsilon:float=1e-6,
                                     energy:bool=False):
    """ Compute the new area at the junction a_junction
    from the flow rates q of the branches and the area a.

    We ensure a same water elevation (z+h) at the junction in each branch
    or a same head if energy is True.

    :param q: np.ndarray, estimated signed flow rates of the branches
    :param a: np.ndarray, estimated area of the branches
    :param h_l_froma: function converting area to water height and width
    :param z: np.ndarray, elevation of the branches
    :param epsilon: float, tolerance of the method
    :param energy: bool, if True, ensure the same energy at the junction
    """

    n = q.size

    # Compute the area ensuring the same water elevation at the junction
    # using the Lagrange multiplier method
    #
    # We minimize the following function:
    #   sum_{i=1}^{n} 1/2 * (anew_i - a_i) ** 2
    # subject to the constraint:
    #   (Z_i + h_i) - (Z_i+1 + h_i+1) = 0
    # or
    #   (Z_i + h_i + 1/2 * (q_i / a_i) ^2 / g) - (Z_i+1 + h_i+1 + 1/2 * (q_i+1 / a_i+1) ^2 / g) = 0
    #
    # The problem is generally non-linear, we use the Newton-Raphson method to solve it.
    #
    # The Jacobian of the system is:
    #   dH_i / da_i = 1 / width_i
    #   dH_i / da_i+1 = -1 / width_i+1
    #   dZ_i / da_i = 0
    #   dZ_i / da_i+1 = 0
    # if energy is True:
    #   d1/2 * (q_i / a_i) ^2 / g) / da_i = -q_i^2 / (a_i^3 * g)
    #   d1/2 * (q_i+1 / a_i+1) ^2 / g) / da_i+1 = q_i+1^2 / (a_i+1^3 * g)
    #
    # The system is solved iteratively using the Newton-Raphson method.


    KITERMAX=100
    GRAVITY = 9.81

    ncompl  = 2*n-1

    # !Mise en correspondance deux par deux des altitudes de surface ou des énérgies
    kiter = 0
    error = 1.

    while error > epsilon and kiter<KITERMAX:

        A = np.zeros((ncompl, ncompl))
        A[:n, :n] = np.eye(n)
        b = np.zeros(ncompl)

        kiter=kiter+1
        if kiter>100:
            print('Max iteration in junction')

        h, width = h_width_froma(a)

        # imposition des contraintes
        if energy:
            for i in range(n-1):
                ipos = n + i
                jpos = i + 1

                # Termes suppl si égalisation d'énergie
                v1_carre = (q[i]    / a[i])**2.    / GRAVITY
                v2_carre = (q[jpos] / a[jpos])**2. / GRAVITY

                A[ipos,i]       =    1./width[i]      - v1_carre / a[i]
                A[ipos,jpos]    =   -1./width[jpos]   + v2_carre / a[jpos]
                A[i,ipos]       =   -A[ipos,i]
                A[jpos,ipos]    =   -A[ipos,jpos]

                b[ipos]         =   (v2_carre/2.0 + z[jpos] + h[jpos]) - (v1_carre/2.0 + z[i] + h[i])

        else:
            for i in range(n-1):
                ipos = n + i
                jpos = i + 1

                # !dérivée de H vis-à-vis de la section --> largeur courante
                A[ipos,i]       =    1.0/width[i]
                A[ipos,jpos]    =   -1.0/width[jpos]
                A[i,ipos]       =   -A[ipos,i]
                A[jpos,ipos]    =   -A[ipos,jpos]

                # membre de droite --> delta d'altitude de fond
                b[ipos]         =   (z[jpos]+h[jpos]) - (z[i]+h[i])

        # résolution du système
        incr = np.linalg.solve(A, b)

        # mise à jour de l'inconnue de section sur base des incréments
        a = a + incr[:n]

        # mise à jour des propriétés indirectes
        h, width = h_width_froma(a)

        # calcul de l'erreur résiduelle
        error = np.sum(np.abs(incr[:n]))

    return a

if __name__ == "__main__":
    # Test the function
    q = np.array([-1, 2, 3, -4])
    q_junction, lambda_ = junction_q_lagrangemult(q)
    print("q_junction:", q_junction)
    print("lambda:", lambda_)

    # Test the function
    q = np.array([-1.1, 2.2, 3.001, -3.99])
    q_junction, lambda_ = junction_q_lagrangemult(q)
    print("q_junction:", q_junction)
    print("lambda:", lambda_)

    def h_width_froma(a:np.ndarray):
        L = 5.
        h = a / L
        dl = np.ones(a.shape) * L
        return h, dl
    
    a = np.array([1, 2, 3, 4])
    z = np.array([0, 0, 0, 0])

    a_junction = junction_wse_head_lagrangemult(q, a, h_width_froma, z, energy=False)
    print("a_junction:", a_junction + z)

    a = a_junction
    a_junction = junction_wse_head_lagrangemult(q, a, h_width_froma, z, energy=True)
    print("a_junction:", a_junction)

    L = 5.
    z = np.array([0, -1, .5, -.5])
    a = (1. - z) * L

    a_junction = junction_wse_head_lagrangemult(q, a, h_width_froma, z, energy=False)
    h, width = h_width_froma(a_junction)
    print("wse:", h + z)

    z = np.array([0, -1, .5, -.5])
    a = (1. - z)*5.
    a[0] += 0.1
    a[1] += 0.1
    a[2] -= 0.1
    a[3] -= 0.1

    a_junction = junction_wse_head_lagrangemult(q, a, h_width_froma, z, energy=False)
    h, width = h_width_froma(a_junction)
    print("wse:", h + z)
    pass
