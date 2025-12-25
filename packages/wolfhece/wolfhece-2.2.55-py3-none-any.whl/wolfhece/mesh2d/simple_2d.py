import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm
from numba import jit
from scipy.optimize import root_scalar
from typing import Literal
from enum import Enum
import logging

"""
Calcul des equations shallow water en 1D section rectangulaire avec frottement selon Manning

Continuity : dh/dt + d(q)/dx = 0
Momentum   : dq/dt + d(q^2/h + 1/2 g h^2)/dx + g h dz/dx = -g h J
Friction Slope : J = n^2 (q/h)^2 / h^(4/3)

Discretisation :

J = n^2 q_t2 q_t1 / h^(10/3)
ghJ = q_t2 (g n^2 q_t1 / h^(7/3))

h_t2 = h_t1 - dt/dx (q_t,r - q_t,l)
q_t2 = 1/(1 + dt g n^2 q_t1 / h^(7/3)) * (q_t1 - dt/dx (q_t,r^2/h_t,r - q_t,l^2/h_t,l + 1/2 g (h_t,r^2 - h_t,l^2) + g h_center_mean (z_t,r - z_t,l))

"""

class Scenarios(Enum):
    unsteady_downstream_bc = 0
    hydrograph = 1
    hydrograph_2steps = 2
    Gauss = 3
    water_lines = 4

def domain(length:float, dx:float, slope:float) -> np.ndarray:
    """ Create the domain

    :param length: Length of the domain
    :param dx:     Space step
    :param slope:  Slope of the domain
    """

    nb = int(length/dx)
    dom = np.zeros(nb+2)
    x = [-dx/2.] + [(float(i)+.5)*dx for i in range(0,nb)] + [length + dx/2.]
    z = -slope * np.array(x)
    return dom, x, z

def _init_conditions(dom:np.ndarray, h0:float, q0:float) -> np.ndarray:
    """ Initial conditions

    :param dom: Domain
    :param h0:  Initial water depth [m]
    :param q0:  Initial discharge [m^2/s]
    """

    h = np.zeros_like(dom)
    h[1:-1] = h0
    q = np.zeros_like(dom)
    q[1:-1] = q0
    return h, q

def get_friction_slope_2D_Manning(q:float, h:float, n:float) -> float:
    """ Friction slope based on Manning formula

    :param q: Discharge [m^2/s]
    :param h: Water depth [m]
    :param n: Manning coefficient [m^(1/3)/s]
    """
    return n**2 * q**2 / h**(10/3)

def compute_dt(dx:float, h:np.ndarray, q:np.ndarray, CN:float) -> float:
    """ Compute the time step according to the Courant number anf the maximum velocity

    :param dx: Space step
    :param h:  Water depth
    :param q:  Discharge
    :param CN: Courant number
    """

    h_pos = np.where(h > 0)[0]
    dt = CN * dx / (np.max(np.abs(q[h_pos]/h[h_pos]) + np.sqrt(h[h_pos]*9.81)))
    return dt

def all_unk_border(dom:np.ndarray, h0:float, q0:float) -> tuple[np.ndarray]:
    """ Initialize all arrays storing unknowns at center and borders

    :param dom: Domain
    :param h0:  Initial water depth
    :param q0:  Initial discharge
    """

    h, q = _init_conditions(dom, h0, q0)
    h_pred = np.zeros_like(dom)
    h_corr = np.zeros_like(dom)
    q_pred = np.zeros_like(dom)
    q_corr = np.zeros_like(dom)

    q_border = np.zeros((len(dom), 2))
    h_border = np.zeros((len(dom), 2))
    z_border = np.zeros((len(dom), 2))

    u_border = np.zeros(len(dom))
    h_center = np.zeros(len(dom)-2)
    u_center = np.zeros(len(dom)-2)

    return h, q, h_pred, q_pred, h_corr, q_corr, q_border, h_border, z_border, u_border, h_center, u_center

def uniform_waterdepth(slope:float, q:float, n:float):
    """ Compute the uniform water depth for a given slope, discharge and Manning coefficient

    :param slope: Slope
    :param q:     Discharge [m^2/s]
    :param n:     Manning coefficient
    """

    if n==0. or slope==0.:
        logging.error("Manning coefficient or slope cannot be null")
        logging.warning("Return 99999.")
        return 99999.

    return root_scalar(lambda h: slope - get_friction_slope_2D_Manning(q, h, n), bracket=[0.1, 100.]).root

# -----------------
# LOSS Coefficients
# -----------------

def k_abrupt_enlargment(asmall:float, alarge:float) -> float:
    """ Compute the local head loss coefficient of the abrupt enlargment

    :params asmall: float, area of the section 1 -- smaller section
    :params alarge: float, area of the section 2 -- larger section
    """

    return (1 - asmall/alarge)**2

def k_abrupt_contraction(alarge:float, asmall:float) -> float:
    """ Compute the local head loss coefficient of the abrupt contraction

    :params alarge: float, area of the section 1 -- larger section
    :params asmall: float, area of the section 2 -- smaller section
    """

    return .5*(1 - asmall/alarge)

def head_loss_enlargment(q:float, asmall:float, alarge:float) -> float:
    """ Compute the head loss of the enlargment.

    Reference velocity is the velocity in the smaller section.

    :params q: float, discharge
    :params asmall: float, area of the section 1 -- smaller section
    :params alarge: float, area of the section 2 -- larger section
    """

    return k_abrupt_enlargment(asmall, alarge) * (q/asmall)**2 / 2 / 9.81

def head_loss_contraction(q:float, alarge:float, asmall:float) -> float:
    """ Compute the head loss of the contraction.

    Reference velocity is the velocity in the smaller section.

    :params q: float, discharge
    :params alarge: float, area of the section 1 -- larger section
    :params asmall: float, area of the section 2 -- smaller section
    """

    return k_abrupt_contraction(alarge, asmall) * (q/asmall)**2 / 2 / 9.81

def head_loss_contract_enlarge(q:float, a_up:float, asmall:float, a_down:float) -> float:
    """ Compute the head loss of the contraction/enlargment.

    Reference velocity is the velocity in the smaller section.

    :params q: float, discharge
    :params a_up: float, area of the section 1 -- larger section
    :params asmall: float, area of the section 2 -- smaller section
    :params a_down: float, area of the section 3 -- larger section
    """

    return (k_abrupt_enlargment(asmall, a_down) + k_abrupt_contraction(a_up, asmall)) * (q/asmall)**2 / 2 / 9.81

# ----------------------------
# START JIT compiled functions
# ----------------------------

@jit(nopython=True)
def get_friction_slope_2D_Manning_semi_implicit(u:np.ndarray, h:np.ndarray, n:float) -> np.ndarray:
    """ Friction slope based on Manning formula -- Only semi-implicit formulea for the friction slope

    :param u: Velocity [m/s]
    :param h: Water depth [m]
    :param n: Manning coefficient [m^(1/3)/s]
    """

    return n**2 * np.abs(u) / h**(7/3)

@jit(nopython=True)
def Euler_RK(h_t1:np.ndarray, h_t2:np.ndarray,
          q_t1:np.ndarray, q_t2:np.ndarray,
          h:np.ndarray, q:np.ndarray,
          h_border:np.ndarray, q_border:np.ndarray,
          z:np.ndarray, z_border:np.ndarray,
          dt:float, dx:float,
          CL_h:float, CL_q:float,
          n:float, u_border:np.ndarray,
          h_center:np.ndarray, u_center:np.ndarray) -> None:
    """ Solve the mass and momentum equations using a explicit Euler/Runge-Kutta scheme (only 1 step)

    :param h_t1: Water depth at time t
    :param h_t2: Water depth at time t+dt (or t_star or t_doublestar if RK)
    :param q_t1: Discharge at time t
    :param q_t2: Discharge at time t+dt (or t_star or t_doublestar if RK)
    :param h:    Water depth at the mesh center
    :param q:    Discharge at the mesh center
    :param h_border: Water depth at the mesh border
    :param q_border: Discharge at the mesh border
    :param z:    Bed elevation
    :param z_border: Bed elevation at the mesh border
    :param dt:   Time step
    :param dx:   Space step
    :param CL_h: Downstream boudary condition for water depth
    :param CL_q: Upstream boundary condition for discharge
    :param n:    Manning coefficient
    :param u_border: Velocity at the mesh border
    :param h_center: Water depth at the mesh center
    :param u_center: Velocity at the mesh center
    """

    g = 9.81

    slice_mesh = slice(1,-1)
    slice_right_border = slice(2,None)
    slice_left_border = slice(1,-1)

    up = 0
    do = 1

    # valeur à gauche du bord
    q_border[slice_right_border, up] = q[1:-1]
    q_border[1,up]  = CL_q

    h_border[slice_right_border, up] = h[1:-1]
    h_border[1,up]  = h[1]

    z_border[slice_right_border, up] = z[1:-1]
    z_border[1,up]  = z[1]

    # valeur à droite du bord
    q_border[slice_left_border, do] = q[1:-1]
    q_border[-1,do] = q[-2]

    h_border[slice_left_border, do] = h[1:-1]
    h_border[-1,do] = CL_h

    z_border[slice_left_border, do] = z[1:-1]
    z_border[-1,do] = z[-2]

    u_border[1:] = q_border[1:,up]/h_border[1:,up]

    h_center = (h_border[slice_right_border,do] + h_border[slice_left_border,do])/2.
    u_center = q[slice_mesh]/h[slice_mesh]

    #Continuity
    h_t2[slice_mesh] = h_t1[slice_mesh] - dt/dx * (q_border[slice_right_border,up] - q_border[slice_left_border,up])

    # Momentum

    J = get_friction_slope_2D_Manning_semi_implicit(u_center, h[slice_mesh], n)
    qm_right = u_border[slice_right_border]*q_border[slice_right_border,up]
    qm_left  = u_border[slice_left_border]*q_border[slice_left_border,up]

    press_right = 0.5 * g * h_border[slice_right_border,do]**2
    press_left  = 0.5 * g * h_border[slice_left_border,do]**2

    bed_right = g * h_center * z_border[slice_right_border,do]
    bed_left  = g * h_center * z_border[slice_left_border,do]

    q_t2[slice_mesh] = 1./(1. + dt * g *h[slice_mesh] * J) * (q_t1[slice_mesh] - dt/dx * (qm_right - qm_left + press_right - press_left + bed_right - bed_left))

    limit_h_q(h_t2, q_t2, hmin=1e-3, Froudemax=3.)

@jit(nopython=True)
def Euler_RK_hedge(h_t1:np.ndarray, h_t2:np.ndarray,
          q_t1:np.ndarray, q_t2:np.ndarray,
          h:np.ndarray, q:np.ndarray,
          h_border:np.ndarray, q_border:np.ndarray,
          z:np.ndarray, z_border:np.ndarray,
          dt:float, dx:float,
          CL_h:float, CL_q:float,
          n:float, u_border:np.ndarray,
          h_center:np.ndarray, u_center:np.ndarray,
          theta:np.ndarray, theta_border:np.ndarray) -> None:
    """ Solve the mass and momentum equations using a explicit Euler/Runge-Kutta scheme (only 1 step)

    :param h_t1: Water depth at time t
    :param h_t2: Water depth at time t+dt (or t_star or t_doublestar if RK)
    :param q_t1: Discharge at time t
    :param q_t2: Discharge at time t+dt (or t_star or t_doublestar if RK)
    :param h:    Water depth at the mesh center
    :param q:    Discharge at the mesh center
    :param h_border: Water depth at the mesh border
    :param q_border: Discharge at the mesh border
    :param z:    Bed elevation
    :param z_border: Bed elevation at the mesh border
    :param dt:   Time step
    :param dx:   Space step
    :param CL_h: Downstream boudary condition for water depth
    :param CL_q: Upstream boundary condition for discharge
    :param n:    Manning coefficient
    :param u_border: Velocity at the mesh border
    :param h_center: Water depth at the mesh center
    :param u_center: Velocity at the mesh center
    """

    g = 9.81

    slice_mesh = slice(1,-1)
    slice_right_border = slice(2,None)
    slice_left_border = slice(1,-1)

    up = 0
    do = 1

    # valeur à gauche du bord
    # -----------------------

    q_border[slice_right_border, up] = q[1:-1]
    q_border[1,up]  = CL_q

    h_border[slice_right_border, up] = h[1:-1]
    h_border[1,up]  = h[1]

    z_border[slice_right_border, up] = z[1:-1]
    z_border[1,up]  = z[1]

    theta_border[slice_right_border, up] = theta[1:-1]
    theta_border[1,up]  = theta[1]

    # valeur à droite du bord
    # ------------------------

    q_border[slice_left_border, do] = q[1:-1]
    q_border[-1,do] = q[-2]

    h_border[slice_left_border, do] = h[1:-1]
    h_border[-1,do] = CL_h

    z_border[slice_left_border, do] = z[1:-1]
    z_border[-1,do] = z[-2]

    theta_border[slice_left_border, do] = theta[1:-1]
    theta_border[-1,do] = theta[-2]


    u_border[1:] = q_border[1:,up]/(h_border[1:,up] * theta_border[1:,up])

    h_center = (theta_border[slice_right_border,do] * h_border[slice_right_border,do] + theta_border[slice_left_border,do] * h_border[slice_left_border,do])/2.
    u_center = q[slice_mesh]/(h[slice_mesh]*theta[slice_mesh])

    #Continuity
    h_t2[slice_mesh] = h_t1[slice_mesh] - dt/dx * (q_border[slice_right_border,up] - q_border[slice_left_border,up])

    # Momentum

    J = get_friction_slope_2D_Manning_semi_implicit(u_center, h[slice_mesh], n)
    qm_right = u_border[slice_right_border]*q_border[slice_right_border,up]
    qm_left  = u_border[slice_left_border ]*q_border[slice_left_border,up]

    press_right = 0.5 * g * (theta_border[slice_right_border,do] * h_border[slice_right_border,do])**2
    press_left  = 0.5 * g * (theta_border[slice_left_border ,do] * h_border[slice_left_border ,do])**2

    bed_right = g * h_center * (z_border[slice_right_border,do] + (1-theta_border[slice_right_border,do]) * h_border[slice_right_border,do])
    bed_left  = g * h_center * (z_border[slice_left_border,do]  + (1-theta_border[slice_left_border,do])  * h_border[slice_left_border,do])

    q_t2[slice_mesh] = 1./(1. + dt * g *h[slice_mesh] * J) * (q_t1[slice_mesh] - dt/dx * (qm_right - qm_left + press_right - press_left + bed_right - bed_left))

    limit_h_q(h_t2, q_t2, hmin=1e-3, Froudemax=3.)


@jit(nopython=True)
def splitting(q_left:np.float64, q_right:np.float64,
              h_left:np.float64, h_right:np.float64,
              z_left:np.float64, z_right:np.float64,
              z_bridge_left:np.float64, z_bridge_right:np.float64) -> np.ndarray:
    """ Splitting of the unknowns at border between two nodes
    -- Based on the WOLF HECE original scheme

    :param q_left: Discharge at the left-side of the border
    :param q_right: Discharge at the right-side of the border
    :param h_left: Water depth at the left-side of the border
    :param h_right: Water depth at the right-side of the border
    :param z_left: Bed elevation at the left-side of the border
    :param z_right: Bed elevation at the right-side of the border
    :param z_bridge_left: Bridge elevation at the left-side of the border
    :param z_bridge_right: Bridge elevation at the right-side of the border
    :return: Array of the unknowns according to the WOLF HECE scheme
    """

    prod_q = q_left * q_right
    sum_q = q_left + q_right

    if prod_q > 0.:
        if q_left > 0.:
            return np.asarray([q_left,  min(h_left, z_bridge_left-z_left),    h_right, z_right, z_bridge_right], dtype=np.float64)
        else:
            return np.asarray([q_right, min(h_right, z_bridge_right-z_right), h_left,  z_left,  z_bridge_left], dtype=np.float64)
    elif prod_q < 0.:
        if sum_q > 0.:
            return np.asarray([q_left,  min(h_left, z_bridge_left-z_left),    h_right, z_right, z_bridge_right], dtype=np.float64)
        elif sum_q < 0.:
            return np.asarray([q_right, min(h_right, z_bridge_right-z_right), h_left,  z_left,  z_bridge_left], dtype=np.float64)
        else:
            return np.asarray([0., 1., (h_left + h_right) / 2., (z_left + z_right) / 2., (z_bridge_left + z_bridge_right) / 2.], dtype=np.float64)
    else:
        if q_left<0.:
            return np.asarray([np.float64(0.), np.float64(1.), h_left,  z_left,  z_bridge_left], dtype=np.float64)
        elif q_right<0.:
            return np.asarray([np.float64(0.), np.float64(1.), h_right, z_right, z_bridge_right], dtype=np.float64)
        else:
            return np.asarray([sum_q / 2.,              # q
                               (min(h_left, z_bridge_left-z_left) + min(h_right, z_bridge_right-z_right)) / 2.,  # h_vel
                               (h_left + h_right) / 2., # h
                               (z_left + z_right) / 2., # z
                               (z_bridge_left + z_bridge_right) / 2.], dtype=np.float64) # z_bridge


@jit(nopython=True)
def Euler_RK_bridge(h_t1:np.ndarray, h_t2:np.ndarray,
          q_t1:np.ndarray, q_t2:np.ndarray,
          h:np.ndarray, q:np.ndarray,
          h_border:np.ndarray, q_border:np.ndarray,
          z:np.ndarray, z_border:np.ndarray,
          dt:float, dx:float,
          CL_h:float, CL_q:float,
          n:float, u_border:np.ndarray,
          h_center:np.ndarray, u_center:np.ndarray,
          z_bridge:np.ndarray, z_bridge_border:np.ndarray,
          infil_exfil=None) -> None:
    """
    Solve the mass and momentum equations using a explicit Euler/Runge-Kutta scheme (only 1 step)
    applying source terms for infiltration/exfiltration and pressure at the roof.

    :param h_t1: Water depth at time t
    :param h_t2: Water depth at time t+dt (or t_star or t_doublestar if RK)
    :param q_t1: Discharge at time t
    :param q_t2: Discharge at time t+dt (or t_star or t_doublestar if RK)
    :param h:    Water depth at the mesh center
    :param q:    Discharge at the mesh center
    :param h_border: Water depth at the mesh border
    :param q_border: Discharge at the mesh border
    :param z:    Bed elevation
    :param z_border: Bed elevation at the mesh border
    :param dt:   Time step
    :param dx:   Space step
    :param CL_h: Downstream boudary condition for water depth
    :param CL_q: Upstream boundary condition for discharge
    :param n:    Manning coefficient
    :param u_border: Velocity at the mesh border
    :param h_center: Water depth at the mesh center
    :param u_center: Velocity at the mesh center
    :param z_bridge: Bridge elevation at the mesh center
    :param z_bridge_border: Bridge elevation at the mesh border
    :param infil_exfil: Infiltration/exfiltration parameters
    """
    g = 9.81

    slice_mesh = slice(1,-1)

    #    L           R      L = Left border, R = Right border
    #   l|r         l|r     l = left value, r = right value
    #    |     i     |      i = node indice
    #    |           |
    #    i          i+1     i, i+1 = associated borders
    slice_right_border = slice(2,None) # right border - left value - slice associated to the center values
    slice_left_border = slice(1,-1)    # left border  - right value - slice associated to the center values

    up = 0
    do = 1

    # altitude du pont
    z_bridge_copy = z_bridge.copy()

    fs_cells    = np.where(h <= z_bridge - z)[0] # mailles à surface libre
    press_cells = np.where(h > z_bridge - z)[0]  # mailles sous-pression

    z_bridge_copy[fs_cells] = z[fs_cells] + h[fs_cells] # on recopie l'altitude de SL

    # valeur à gauche du bord
    # -----------------------

    # altitude du fond
    z_border[slice_right_border, up] = z[1:-1]
    z_border[1,up] = z[1]  # tout en amont, recopie de la valeur intérieure

    h_border[slice_right_border, up] = h[1:-1]
    h_border[1,up] = h[1]  # tout en amont, recopie de la valeur intérieure

    q_border[slice_right_border, up] = q[1:-1]
    q_border[1,up] = CL_q  # condition limite de debit

    z_bridge_border[slice_right_border, up] = z_bridge_copy[1:-1]
    z_bridge_border[1,up] = z_bridge_copy[1]

    # valeur à droite du bord
    # ------------------------

    z_border[slice_left_border, do] = z[1:-1]
    z_border[-1,do] = z[-2] # tout en aval, recopie de la valeur intérieure

    h_border[slice_left_border, do] = h[1:-1]
    h_border[-1,do] = CL_h  # condition limite de hauteur

    q_border[slice_left_border, do] = q[1:-1]
    q_border[-1,do] = q[-2] # tout en aval, recopie de la valeur intérieure

    z_bridge_border[slice_left_border, do] = z_bridge_copy[1:-1]
    z_bridge_border[-1,do] = CL_h + z_border[-1,do] # z_bridge_copy[-2]

    for i in range(1, len(h)-1):

        qc_right, h4u_right, hc_right, zc_right, zbc_right = splitting(q_border[i+1,up], q_border[i+1, do], h_border[i+1,up], h_border[i+1,do], z_border[i+1,up], z_border[i+1,do], z_bridge_border[i+1,up], z_bridge_border[i+1,do])
        qc_left,  h4u_left,  hc_left,  zc_left,  zbc_left  = splitting(q_border[i,up], q_border[i, do], h_border[i,up], h_border[i,do], z_border[i,up], z_border[i,do], z_bridge_border[i,up], z_bridge_border[i,do])

        # Continuity
        # ++++++++++

        h_t2[i] = h_t1[i] - dt/dx * (qc_right - qc_left)

        # Momentum
        # ++++++++

        # Limited section at the right border and at the left border -- decentred downstream
        d_right = zbc_right - zc_right
        d_left  = zbc_left  - zc_left

        # Pressure on the roof -- 0. if free surface
        press_roof_right = hc_right - d_right
        press_roof_left  = hc_left  - d_left

        # Pressure integral at the right border and at the left border
        press_right = 0.5 * g * (hc_right**2. - press_roof_right**2)
        press_left  = 0.5 * g * (hc_left**2.  - press_roof_left**2)

        # Friction slope based on center values
        u_center = q[i] / (z_bridge_copy[i] - z[i])
        #   Number of surfaces
        nb_frott = 2. if h[i] > z_bridge[i] - z[i] else 1.
        #   Integration water depth
        h_frott = min(h[i], z_bridge[i] - z[i])
        #   Slope
        J = get_friction_slope_2D_Manning_semi_implicit(u_center, h_frott/nb_frott, n)

        # Velocity at the right border and at the left border -- decentred upstream
        u_right = qc_right / h4u_right
        u_left  = qc_left  / h4u_left

        # Momentum at the right border and at the left border
        qm_right = u_right * qc_right
        qm_left  = u_left  * qc_left

        # Mean pressure impacting bed reaction
        h_mean = (hc_right + hc_left)/2.
        bed_right = g * h_mean * zc_right
        bed_left  = g * h_mean * zc_left

        # Mean pressure impacting roof reaction
        h_roof_right = max(hc_right + zc_right - zbc_right, 0.)
        h_roof_left  = max(hc_left  + zc_left  - zbc_left , 0.)
        h_roof_mean = (h_roof_right + h_roof_left) / 2.

        roof_right = g * h_roof_mean * zbc_right
        roof_left  = g * h_roof_mean * zbc_left

        rhs = (qm_right - qm_left + press_right - press_left + bed_right - bed_left - roof_right + roof_left)

        if rhs !=0.:
            pass

        q_t2[i] = 1./(1. + dt * g * h_frott * J) * (q_t1[i] - dt/dx * rhs)

    if infil_exfil is not None:
        idx_up, idx_do, q_infil_exfil, u_infil_exfil, pond, k = infil_exfil

        i = idx_up

        qc_right, h4u_right, hc_right, zc_right, zbc_right = splitting(q_border[i+1,up], q_border[i+1, do], h_border[i+1,up], h_border[i+1,do], z_border[i+1,up], z_border[i+1,do], z_bridge_border[i+1,up], z_bridge_border[i+1,do])
        qc_left,  h4u_left,  hc_left,  zc_left,  zbc_left  = splitting(q_border[i,up], q_border[i, do], h_border[i,up], h_border[i,do], z_border[i,up], z_border[i,do], z_bridge_border[i,up], z_bridge_border[i,do])

        # Limited section at the right border and at the left border -- decentred downstream
        d_right = zbc_right - zc_right
        d_left  = zbc_left  - zc_left

        # Pressure on the roof -- 0. if free surface
        press_roof_right = hc_right - d_right
        press_roof_left  = hc_left  - d_left

        # Pressure integral at the right border and at the left border
        press_right = 0.5 * g * (hc_right**2. - press_roof_right**2)
        press_left  = 0.5 * g * (hc_left**2.  - press_roof_left**2)

        # Friction slope based on center values
        u_center = q[i] / (z_bridge_copy[i] - z[i])
        #   Number of surfaces
        nb_frott = 2. if h[i] > z_bridge[i] - z[i] else 1.
        #   Integration water depth
        h_frott = min(h[i], z_bridge[i] - z[i])
        #   Slope
        J = get_friction_slope_2D_Manning_semi_implicit(u_center, h_frott/nb_frott, n)

        # Velocity at the right border and at the left border -- decentred upstream
        u_right = qc_right / h4u_right
        u_left  = qc_left  / h4u_left

        # Momentum at the right border and at the left border
        qm_right = u_right * qc_right
        qm_left  = u_left  * qc_left

        # Mean pressure impacting bed reaction
        h_mean = (hc_right + hc_left)/2.
        bed_right = g * h_mean * zc_right
        bed_left  = g * h_mean * zc_left

        # Mean pressure impacting roof reaction
        h_roof_right = max(hc_right + zc_right - zbc_right, 0.)
        h_roof_left  = max(hc_left  + zc_left  - zbc_left , 0.)
        h_roof_mean = (h_roof_right + h_roof_left) / 2.

        roof_right = g * h_roof_mean * zbc_right
        roof_left  = g * h_roof_mean * zbc_left

        h_t2[i] = h_t1[i] - dt/dx * (qc_right - qc_left + q_infil_exfil)
        q_t2[i] = 1./(1. + dt * g * h_frott * J) * (q_t1[i] - dt/dx * (qm_right - qm_left + \
                                                press_right - press_left + \
                                                bed_right - bed_left - \
                                                roof_right + roof_left + \
                                                u_infil_exfil * q_infil_exfil))

        i = idx_do

        qc_right, h4u_right, hc_right, zc_right, zbc_right = splitting(q_border[i+1,up], q_border[i+1, do], h_border[i+1,up], h_border[i+1,do], z_border[i+1,up], z_border[i+1,do], z_bridge_border[i+1,up], z_bridge_border[i+1,do])
        qc_left,  h4u_left,  hc_left,  zc_left,  zbc_left  = splitting(q_border[i,up], q_border[i, do], h_border[i,up], h_border[i,do], z_border[i,up], z_border[i,do], z_bridge_border[i,up], z_bridge_border[i,do])

        # Limited section at the right border and at the left border -- decentred downstream
        d_right = zbc_right - zc_right
        d_left  = zbc_left  - zc_left

        # Pressure on the roof -- 0. if free surface
        press_roof_right = hc_right - d_right
        press_roof_left  = hc_left  - d_left

        # Pressure integral at the right border and at the left border
        press_right = 0.5 * g * (hc_right**2. - press_roof_right**2)
        press_left  = 0.5 * g * (hc_left**2.  - press_roof_left**2)

        # Friction slope based on center values
        u_center = q[i] / (z_bridge_copy[i] - z[i])
        #   Number of surfaces
        nb_frott = 2. if h[i] > z_bridge[i] - z[i] else 1.
        #   Integration water depth
        h_frott = min(h[i], z_bridge[i] - z[i])
        #   Slope
        J = get_friction_slope_2D_Manning_semi_implicit(u_center, h_frott/nb_frott, n)

        # Velocity at the right border and at the left border -- decentred upstream
        u_right = qc_right / h4u_right
        u_left  = qc_left  / h4u_left

        # Momentum at the right border and at the left border
        qm_right = u_right * qc_right
        qm_left  = u_left  * qc_left

        # Mean pressure impacting bed reaction
        h_mean = (hc_right + hc_left)/2.
        bed_right = g * h_mean * zc_right
        bed_left  = g * h_mean * zc_left

        # Mean pressure impacting roof reaction
        h_roof_right = max(hc_right + zc_right - zbc_right, 0.)
        h_roof_left  = max(hc_left  + zc_left  - zbc_left , 0.)
        h_roof_mean = (h_roof_right + h_roof_left) / 2.

        roof_right = g * h_roof_mean * zbc_right
        roof_left  = g * h_roof_mean * zbc_left

        h_t2[i] = h_t1[i] - dt/dx * (qc_right - qc_left - q_infil_exfil)
        q_t2[i] = 1./(1. + dt * g * h_frott * J) * (q_t1[i] - dt/dx * (qm_right - qm_left + \
                                                press_right - press_left + \
                                                bed_right - bed_left - \
                                                roof_right + roof_left -\
                                                u_infil_exfil * q_infil_exfil))

    limit_h_q(h_t2, q_t2, hmin=1e-3, Froudemax=3.)

@ jit(nopython=True)
def limit_h_q(h:np.ndarray, q:np.ndarray, hmin:float = 0., Froudemax:float = 3.) -> None:
    """ Limit the water depth and the discharge

    :param h: Water depth [m]
    :param q: Discharge [m^2/s]
    :param hmin: Minimum water depth [m]
    :param Froudemax: Maximum Froude number [-]
    """

    # retrieve positive and negative values
    hpos = np.where(h > hmin)
    hneg = np.where(h <= hmin)

    # limit water depth
    h[hneg] = hmin
    q[hneg] = 0.

    # limit discharge based on Froude number
    Fr = np.zeros_like(h)
    Fr[hpos] = np.abs(q[hpos]) / h[hpos] / np.sqrt(9.81 * h[hpos])
    q[Fr > Froudemax] = Froudemax * np.sqrt(9.81 * h[Fr > Froudemax]) * h[Fr > Froudemax] * np.sign(q[Fr > Froudemax])

# --------------------------
# END JIT compiled functions
# --------------------------

# ----------------------
# START Problems section
# ----------------------

def problem(dom:np.ndarray, z:np.ndarray, h0:float, q0:float, dx:float, CN:float, n:float):
    """ Solve the mass and momentum equations using a explicit Runge-Kutta scheme (2 steps - 2nd order)

    **NO BRIDGE**
    """

    h, q, h_pred, q_pred, h_corr, q_corr, q_border, h_border, z_border, u_border, h_center, u_center = all_unk_border(dom, h0, q0)

    totaltime = 4*3600
    eps=1.

    with tqdm(total=totaltime) as pbar:
        t = 0.
        while eps > 1e-12:
            dt = compute_dt(dx, h, q, CN)
            # Predictor step
            Euler_RK(h, h_pred, q, q_pred, h, q, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center)
            # Corrector step
            Euler_RK(h, h_corr, q, q_corr, h_pred, q_pred, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center)

            # Update -- Mean for second order in time
            h = (h_pred + h_corr)/2.
            q = (q_pred + q_corr)/2.
            t+=dt

            eps = np.sum(np.abs(q - q_pred))

            pbar.update(dt)

    print("Total time : ", t)
    print("Residual : ", eps)

    return h, q

def problem_hedge(dom:np.ndarray, z:np.ndarray, h0:float, q0:float, dx:float, CN:float, n:float):
    """ Solve the mass and momentum equations using a explicit Runge-Kutta scheme (2 steps - 2nd order)

    **NO BRIDGE but HEDGE in the middle**
    """

    h, q, h_pred, q_pred, h_corr, q_corr, q_border, h_border, z_border, u_border, h_center, u_center = all_unk_border(dom, h0, q0)

    theta = np.ones_like(h)
    theta_border = np.ones_like(h_border)

    slice_hedge = slice(len(h) // 2-1, len(h) // 2+2)
    theta_val = 0.5
    theta[slice_hedge] = theta_val

    totaltime = 4*3600
    eps=1.

    with tqdm(total=totaltime) as pbar:
        t = 0.
        while eps > 1e-12:
            dt = compute_dt(dx, h, q, CN)
            # Predictor step
            Euler_RK_hedge(h, h_pred, q, q_pred, h, q, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center, theta, theta_border)
            # Corrector step
            Euler_RK_hedge(h, h_corr, q, q_corr, h_pred, q_pred, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center, theta, theta_border)

            # Update -- Mean for second order in time
            h = (h_pred + h_corr)/2.
            q = (q_pred + q_corr)/2.
            t+=dt

            eps = np.sum(np.abs(q - q_pred))

            pbar.update(dt)

    print("Total time : ", t)
    print("Residual : ", eps)

    return h, q, theta

def problem_bridge(dom:np.ndarray, z:np.ndarray, z_bridge:np.ndarray,
                   h0:float, q0:float,
                   dx:float, CN:float, n:float,
                   h_ini:np.ndarray = None, q_ini:np.ndarray = None) -> tuple[np.ndarray]:
    """ Solve the mass and momentum equations using a explicit Rung-Kutta scheme (2 steps - 2nd order)

    **WITH BRIDGE and NO OVERFLOW**
    """

    h, q, h_pred, q_pred, h_corr, q_corr, q_border, h_border, z_border, u_border, h_center, u_center = all_unk_border(dom, h0, q0)
    z_bridge_border = np.zeros_like(z_border)

    if h_ini is not None:
        h[:] = h_ini[:]
    if q_ini is not None:
        q[:] = q_ini[:]

    totaltime = 4*3600
    eps=1.

    with tqdm(total=totaltime) as pbar:
        t = 0.
        while eps > 1e-7:
            dt = compute_dt(dx, h, q, CN)
            # Predictor step
            Euler_RK_bridge(h, h_pred, q, q_pred, h, q, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center, z_bridge, z_bridge_border)
            # Corrector step
            Euler_RK_bridge(h, h_corr, q, q_corr, h_pred, q_pred, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center, z_bridge, z_bridge_border)

            # Update -- Mean for second order in time
            h = (h_pred + h_corr)/2.
            q = (q_pred + q_corr)/2.
            t+=dt

            eps = np.sum(np.abs(q - q_pred))

            pbar.update(dt)

    print("Total time : ", t)
    print("Residual : ", eps)

    return h, q

def problem_bridge_multiple_steadystates(dom:np.ndarray, z:np.ndarray, z_bridge:np.ndarray,
                                         h0:float, qmin:float, qmax:float,
                                         dx:float, CN:float, n:float,
                                         ) -> list[tuple[float, np.ndarray, np.ndarray]]:
    """ Solve multiple steady states for a given discharge range """

    all_q = np.arange(qmin, qmax+.1, (qmax-qmin)/10)

    ret = []
    h = None
    for curq in all_q:
        h, q = problem_bridge(dom, z, z_bridge, h0, curq, dx, CN, n, h_ini=h, q_ini=None)
        ret.append((0., h.copy(), q.copy()))

    return ret

def problem_bridge_unsteady(dom:np.ndarray, z:np.ndarray, z_bridge:np.ndarray,
                            h0:float, q0:float,
                            dx:float, CN:float, n:float,
                            ):
    """ Solve the mass and momentum equations using a explicit Runge-Kutta scheme (2 steps - 2nd order).

    **WITH BRIDGE and NO OVERFLOW**

    The downstream boundary condition rises temporarily.

    Firstly, we stabilize the flow with a constant downstream boundary condition.
    Then, we increase the downstream boundary condition.

    """

    h, q, h_pred, q_pred, h_corr, q_corr, q_border, h_border, z_border, u_border, h_center, u_center = all_unk_border(dom, h0, q0)
    z_bridge_border = np.zeros_like(z_border)

    totaltime = 4*3600
    eps=1.

    # Compute steady state
    with tqdm(total=totaltime) as pbar:
        t = 0.
        while eps > 1e-7:
            dt = compute_dt(dx, h, q, CN)
            # Predictor step
            Euler_RK_bridge(h, h_pred, q, q_pred, h, q, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center, z_bridge, z_bridge_border)
            # Corrector step
            Euler_RK_bridge(h, h_corr, q, q_corr, h_pred, q_pred, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center, z_bridge, z_bridge_border)

            # Update -- Mean for second order in time
            h = (h_pred + h_corr)/2.
            q = (q_pred + q_corr)/2.
            t+=dt

            eps = np.sum(np.abs(q - q_pred))

            pbar.update(dt)

    print("Total time : ", t)
    print("Residual : ", eps)

    res = []

    totaltime = 2*3600
    k=0
    with tqdm(total=totaltime) as pbar:
        t = 0.
        while t < totaltime:

            dt = compute_dt(dx, h, q, CN)

            if t < totaltime/2:
                h_cl = h0 + 7. * t/totaltime*2
            else:
                h_cl = h0 + 7. - 7. * (t - totaltime/2)/totaltime*2

            # Predictor step
            Euler_RK_bridge(h, h_pred, q, q_pred, h, q, h_border, q_border, z, z_border, dt, dx, h_cl, q0, n, u_border, h_center, u_center, z_bridge, z_bridge_border)
            # Corrector step
            Euler_RK_bridge(h, h_corr, q, q_corr, h_pred, q_pred, h_border, q_border, z, z_border, dt, dx, h_cl, q0, n, u_border, h_center, u_center, z_bridge, z_bridge_border)

            # Update -- Mean for second order in time
            h = (h_pred + h_corr)/2.
            q = (q_pred + q_corr)/2.

            if t > 300*k:
                res.append((t, h.copy(), q.copy()))
                k+=1

            t+=dt
            pbar.update(dt)


    return res

def problem_bridge_unsteady_topo(dom:np.ndarray, z:np.ndarray,
                                 z_roof:np.ndarray, z_deck:np.ndarray, z_roof_null:float,
                                 h0:float, q0:float,
                                 dx:float, CN:float, n:float,
                                 motion_duration:float = 300.,
                                 scenario_bc:Literal['unsteady_downstream_bc',
                                                     'hydrograph',
                                                     'hydrograph_2steps',
                                                     'Gauss'] = 'unsteady_downstream_bc',
                                 min_overflow:float = 0.05,
                                 updating_time_interval:float = 0.
                                 ):
    """ Solve the mass and momentum equations using a explicit Rung-Kutta scheme (2 steps - 2nd order).

    **WITH BRIDGE and OVERFLOW**
    """

    h, q, h_pred, q_pred, h_corr, q_corr, q_border, h_border, z_border, u_border, h_center, u_center = all_unk_border(dom, h0, q0)
    z_roof_border = np.zeros_like(z_border)

    totaltime = 3600 #4*3600
    eps=1.

    # Compute steady state
    with tqdm(total=totaltime) as pbar:
        t = 0.
        while eps > 1e-7:
            dt = compute_dt(dx, h, q, CN)
            # Predictor step
            Euler_RK_bridge(h, h_pred, q, q_pred, h, q, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center, z_roof, z_roof_border)
            # Corrector step
            Euler_RK_bridge(h, h_corr, q, q_corr, h_pred, q_pred, h_border, q_border, z, z_border, dt, dx, h0, q0, n, u_border, h_center, u_center, z_roof, z_roof_border)

            # Update -- Mean for second order in time
            h = (h_pred + h_corr)/2.
            q = (q_pred + q_corr)/2.
            t+=dt

            eps = np.sum(np.abs(q - q_pred))

            pbar.update(dt)

    print("Total time : ", t)
    print("Residual : ", eps)

    g = 9.81

    res = []

    # Functions to evaluate the head and the local head loss coefficient
    def compute_head(z,h,q):
        return z+h+(q/h)**2/2/g

    def compute_delta_head(zup,hup,qup,zdo,hdo,qdo):
        return compute_head(zup,hup,qup) - compute_head(zdo,hdo,qdo)

    def compute_k_mean(zup,hup,qup,zdo,hdo,qdo,A_bridge):
        delta = compute_delta_head(zup,hup,qup,zdo,hdo,qdo)
        q_mean = (qup+qdo)/2
        return delta/((q_mean/A_bridge)**2/2/g)

    def compute_losses(q, A_bridge, k):
        """ Compute the losses based on the flow rate and the local head loss coefficient

        :return: k * |Q| * Q / A^2 / 2 / g
        :unit: [m]
        """
        return k * q * np.abs(q) / A_bridge**2. /2. / g

    def compute_losses_semi_implicit(q, A_bridge, k):
        """ Compute part of the losses based on the flow rate and the local head loss coefficient
        to use in the semi-implicit scheme.

        :return: k * |Q| / A / 2.
        :unit: [s/m²]
        """
        return k * np.abs(q) / A_bridge /2.

    def compute_q_wo_inertia(zup,hup,qup,zdo,hdo,qdo,A_bridge,k):
        """ Compute the flow rate based on Bernoulli equation
        without inertia term """

        delta = compute_delta_head(zup,hup,qup,zdo,hdo,qdo)
        return np.sqrt(2*g*np.abs(delta)/k)*A_bridge*np.sign(delta), delta

    def compute_q_w_inertia(zup:float, hup:float, qup:float,
                            zdo:float, hdo:float, qdo:float,
                            A_bridge:float, k:float, q_prev:float,
                            dt:float, length:float):
        """ Compute the flow rate based on Bernoulli equation
        with inertia term

        $ \frac{\partial Q}{\partial t} + \frac {g A}{L} (Head_do - Head_up + Losses) = 0 $

        $ Losses = k \frac {U^2}{2 g} = k \frac {Q |Q|}{A^2 2 g} $
        """

        # new_q, delta = compute_q_wo_inertia(zup,hup,qup,zdo,hdo,qdo,A_bridge,k)

        delta = compute_delta_head(zup,hup,qup,zdo,hdo,qdo)

        if delta > 1.:
            pass

        inv_dt = 1./ dt
        return (inv_dt * q_prev + g * A_bridge * delta / length) / (inv_dt + compute_losses_semi_implicit(q_prev, A_bridge, k) / length)

    def _update_top(z_start:np.ndarray, z_end:np.ndarray, move_time:float, move_totaltime:float, reverse:bool=False):

        if reverse:
            pond = (move_totaltime - move_time) / move_totaltime
        else:
            pond = move_time / move_totaltime

        loc_z = z_end * pond + z_start * (1.-pond)

        return pond, loc_z

    def update_top_q(z:np.ndarray, h:np.ndarray, q:np.ndarray, z_bridge:np.ndarray,
                     idx_up:int, idx_do:int,
                     survey_up:int, survey_do:int,
                     A:float, k:float, q_prev:float, dt:float,
                     move_time:float, move_totaltime:float, move_restore:bool,
                     z_roof_start:np.ndarray, z_roof_end:np.ndarray,
                     z_bath_start:np.ndarray, z_bath_end:np.ndarray,
                     update_top:bool=True, stop_motion:bool = False):

        if stop_motion:
            move_time = move_totaltime

        zup = z[survey_up]
        zdo = z[survey_do]

        hup = h[survey_up]
        hdo = h[survey_do]

        qup = q[survey_up]
        qdo = q[survey_do]

        # Update the flow rate considering inertia (generalized Bernoulli)
        qtot_infil_exfil = compute_q_w_inertia(zup, hup, qup,
                                                zdo, hdo, qdo,
                                                A, k, q_prev, dt,
                                                length=dx *(idx_do-idx_up-1))

        if update_top:

            pond, z_bridge[bridge] = _update_top(z_roof_start, z_roof_end, move_time, move_totaltime, move_restore)
            pond, z[bridge]        = _update_top(z_bath_start, z_bath_end, move_time, move_totaltime, move_restore)

            # if move_restore:
            #     zref_up = zup + hup - .15
            #     z[bridge] = np.minimum(z[bridge], zref_up)

        else:
            pond = 0. if move_restore else 1.


        if stop_motion and move_restore:
            infil_exfil = None
        else:
            # Applying the infiltration/exfiltration linearly according to the topo-bathymetry evolution
            q_infil_exfil = qtot_infil_exfil * pond
            infil_exfil = (idx_up, idx_do, q_infil_exfil, qup/hup, pond, k)

        return infil_exfil, z_bridge, z, qtot_infil_exfil

    bridge = np.where(z_roof != z_roof_null)[0]

    idx_up = bridge[0]-1
    idx_do = bridge[-1]+1

    survey_up = idx_up-1
    survey_do = idx_do+1

    z_overflow = z_deck[bridge].max() + min_overflow

    totaltime = 2*3600
    total_compute = totaltime + 1800 + 2.

    infil_exfil = None

    bridge_in_motion = False
    filled_bridge = False
    emptying_bridge = False
    motion_completed = True
    local_motion_time = 0.
    total_motion_time = motion_duration

    q_infil_t_current = 0.

    delta_res_time_def = 30.

    if scenario_bc == 'unsteady_downstream_bc':
        dh_cl = 7.
        dq_cl = 0.

    elif scenario_bc == 'unsteady_downstream_bc_culvert':
        dh_cl = 2.
        dq_cl = 0.5

    elif scenario_bc == 'hydrograph_culvert':
        dh_cl = 1.
        dq_cl = 3.

    elif scenario_bc == 'hydrograph':
        dh_cl = 2.
        dq_cl = 8.

    elif scenario_bc == 'hydrograph_2steps':
        dh_cl = 2.
        dq_cl = 8.

    elif scenario_bc == 'hydrograph_2steps_culvert':
        dh_cl = 1.
        dq_cl = 10.

    elif scenario_bc == 'Gauss':
        dh_cl = 2.
        dq_cl = 8.

    with tqdm(total=total_compute, desc=scenario_bc) as pbar:
        t = 0.

        res_time = 0.
        update_time = 0.

        delta_res_time = delta_res_time_def

        z_roof_start = None
        z_roof_end   = None
        z_bath_start = None
        z_bath_end   = None

        while t < total_compute:

            dt = compute_dt(dx, h, q, CN)

            if scenario_bc == 'unsteady_downstream_bc' or scenario_bc == 'unsteady_downstream_bc_culvert':
                # The downstream boundary condition evolves linearly
                # from h0 to h0 + dh_cl in totaltime/2 seconds
                # keeps the value h0 + dh_cl during 1000 seconds
                # and then from h0 + dh_cl to h0 in totaltime/2 seconds
                #
                #                                          ____
                #                                         /    \
                #                                        /      \
                # ------                                /        \
                #                                     _/          \____

                if t < totaltime/2:
                    h_cl = h0 + dh_cl * t/totaltime*2
                    q_cl = q0 + dq_cl * t/totaltime*2
                else:
                    if t < totaltime/2 + 1000.:
                        h_cl = h0 + dh_cl
                        q_cl = q0 + dq_cl
                    else:
                        h_cl = h0 + dh_cl - dh_cl * (t - (totaltime/2+1000.))/(totaltime/2 - 1000.)
                        q_cl = q0 + dq_cl - dq_cl * (t - (totaltime/2+1000.))/(totaltime/2 - 1000.)

            elif scenario_bc == 'hydrograph' or scenario_bc == 'hydrograph_culvert':
                # The downstream boundary condition evolves linearly
                # from h0 to h0 + dh_cl in totaltime/2 seconds
                # keeps the value h0 + dh_cl during 1000 seconds
                # and then from h0 + dh_cl to h0 - dh_cl/2 in totaltime/2 seconds
                #
                # The upstream boundary condition evolves linearly
                # from q0 to q0 + dq_cl in totaltime/2 seconds
                # keeps the value q0 + dq_cl during 1000 seconds
                # and then from q0 + dq_cl to q0 - dq_cl/2 in totaltime/2 seconds
                #
                #      _____                                  ____
                #     /     \                                /    \
                #    /       \                              /      \
                #   /         \                            /        \
                # _/           \                        __/          \
                #               \                                     \
                #                \______                               \____

                if t < totaltime/2:
                    h_cl = h0 + dh_cl * t/totaltime*2
                    q_cl = q0 + dq_cl * t/totaltime*2
                else:
                    if t < totaltime/2 + 1000.:
                        h_cl = h0 + dh_cl
                        q_cl = q0 + dq_cl
                    elif t < totaltime:
                        h_cl = h0 + dh_cl - dh_cl * (t - (totaltime/2+1000.))/(totaltime/2 - 1000.) * 1.5
                        q_cl = q0 + dq_cl - dq_cl * (t - (totaltime/2+1000.))/(totaltime/2 - 1000.) * 1.5
                    else:
                        h_cl = h0 - dh_cl / 2.
                        q_cl = q0 - dq_cl / 2.

            elif scenario_bc == 'hydrograph_2steps' or scenario_bc == 'hydrograph_2steps_culvert':
                # Same as hydrograph but the downstream boundary condition
                # evolves linearly a second time during peek flow

                if t < totaltime/2:
                    h_cl = h0 + dh_cl * t/totaltime*2
                    q_cl = q0 + dq_cl * t/totaltime*2
                else:
                    if t < totaltime/2 + 500.:
                        h_cl = h0 + dh_cl + dh_cl * (t - (totaltime/2))/(500.)
                        q_cl = q0 + dq_cl
                    elif t < totaltime/2 + 1000.:
                        h_cl = h0 + 2* dh_cl - dh_cl * (t - (totaltime/2+500.))/(500.)
                        q_cl = q0 + dq_cl
                    elif t < totaltime:
                        h_cl = h0 + dh_cl - dh_cl * (t - (totaltime/2+1000.))/(totaltime/2 - 1000.) * 1.5
                        q_cl = q0 + dq_cl - dq_cl * (t - (totaltime/2+1000.))/(totaltime/2 - 1000.) * 1.5
                    else:
                        h_cl = h0 - dh_cl / 2.
                        q_cl = q0 - dq_cl / 2.

            elif scenario_bc == 'Gauss':
                # The downstream and upstream boundary conditions evolve
                # according to a Gaussian function

                h_cl = h0 + dh_cl * np.exp(-((t-totaltime/2)**.5)/3600)
                q_cl = q0 + dq_cl * np.exp(-((t-totaltime/2)**.5)/3600)

            # Predictor step
            Euler_RK_bridge(h, h_pred, q, q_pred, h, q, h_border, q_border, z, z_border,
                            dt, dx, h_cl, q_cl,
                            n, u_border, h_center, u_center, z_roof, z_roof_border,
                            infil_exfil)

            # Corrector step
            Euler_RK_bridge(h, h_corr, q, q_corr, h_pred, q_pred, h_border, q_border, z, z_border,
                            dt, dx, h_cl, q_cl,
                            n, u_border, h_center, u_center, z_roof, z_roof_border,
                            infil_exfil)

            # Update -- Mean for second order in time
            h = (h_pred + h_corr)/2.
            q = (q_pred + q_corr)/2.

            if t >= res_time:
                res.append((t, h.copy(), q.copy(), z.copy(), z_roof.copy(), infil_exfil if infil_exfil is not None else (idx_up, idx_do, 0., 0., 0., 0.)))
                res_time += delta_res_time

            if updating_time_interval == 0. or t> update_time:
                update_time += updating_time_interval

                if z[survey_up] + h[survey_up] > z_overflow:
                    # Overflow

                    # Convert Bridge into topography
                    # add infiltration/exfiltration
                    if not bridge_in_motion and motion_completed and not filled_bridge:

                        # Movement must be initiated...

                        # Decreasing the interval of time for the
                        # saving to be more precise when plotting
                        delta_res_time = delta_res_time_def / 5.

                        bridge_in_motion = True
                        emptying_bridge = False
                        motion_completed = False

                        local_motion_time = 0.
                        starting_time = t

                        # Keeping the old values -- Can be useful when restoring
                        old_z_roof = z_roof.copy()
                        old_z = z.copy()

                        # Reference section of the bridge...
                        # Keeping the minimum distance between the bridge and the floor
                        A_bridge = np.min(z_roof[bridge] - z[bridge])


                        # Computing global head loss coefficient associated to the bridge and the reference section
                        k_bridge = compute_k_mean(z[survey_up], h[survey_up], q[survey_up],
                                                z[survey_do], h[survey_do], q[survey_do],
                                                A_bridge)

                        # Starting the motion...
                        #   - the bridge's roof is going up
                        #   - the bridge's floor is going up

                        z_roof_start = old_z_roof[bridge]
                        z_roof_end   = z_roof_null
                        z_bath_start = old_z[bridge]
                        z_bath_end   = z_deck[bridge]

                        # Mean Flow rate under the bridge
                        q_infil_t_current = np.mean(q[bridge])

                        infil_exfil, z_roof, z, q_infil_t_current = update_top_q(z, h, q, z_roof,
                                                                                idx_up, idx_do,
                                                                                survey_up, survey_do,
                                                                                A_bridge, k_bridge, q_infil_t_current,
                                                                                dt,
                                                                                local_motion_time, total_motion_time,
                                                                                emptying_bridge,
                                                                                z_roof_start, z_roof_end, z_bath_start, z_bath_end)

                    else:
                        if not motion_completed:
                            # Movement is initiated but not finished...

                            # Updating the local time
                            # local_motion_time += dt
                            local_motion_time = t - starting_time

                            if local_motion_time > total_motion_time:
                                # Total time is reached...
                                # ... so terminate the movement

                                delta_res_time = delta_res_time_def

                                bridge_in_motion = False
                                motion_completed = True
                                filled_bridge = not filled_bridge

                                infil_exfil, z_roof, z, q_infil_t_current = update_top_q(z, h, q, z_roof,
                                                                                        idx_up, idx_do,
                                                                                        survey_up, survey_do,
                                                                                        A_bridge, k_bridge, q_infil_t_current, dt,
                                                                                        local_motion_time, total_motion_time, emptying_bridge,
                                                                                        z_roof_start, z_roof_end, z_bath_start, z_bath_end,
                                                                                        stop_motion= True)

                                local_motion_time = 0.
                            else:
                                # Total time is not reached...
                                #   ... so continue the movement

                                infil_exfil, z_roof, z, q_infil_t_current = update_top_q(z, h, q, z_roof,
                                                                                        idx_up, idx_do,
                                                                                        survey_up, survey_do,
                                                                                        A_bridge, k_bridge, q_infil_t_current, dt,
                                                                                        local_motion_time, total_motion_time, emptying_bridge,
                                                                                        z_roof_start, z_roof_end, z_bath_start, z_bath_end)
                        else:
                            # Movement is done...

                            if infil_exfil is not None:

                                # Updating the infiltration discharge according to head difference
                                infil_exfil, z_roof, z, q_infil_t_current = update_top_q(z, h, q, z_roof,
                                                                                        idx_up, idx_do,
                                                                                        survey_up, survey_do,
                                                                                        A_bridge, k_bridge, q_infil_t_current, dt,
                                                                                        local_motion_time, total_motion_time, emptying_bridge,
                                                                                        z_roof_start, z_roof_end, z_bath_start, z_bath_end,
                                                                                        update_top=False)


                else:
                    # No overflow

                    if bridge_in_motion:
                        # But movement is initiated...
                        # local_motion_time += dt
                        local_motion_time = t - starting_time

                        if local_motion_time > total_motion_time:

                            delta_res_time = delta_res_time_def

                            # Total time is reached...
                            # ... so terminate the movement

                            bridge_in_motion = False
                            motion_completed = True
                            filled_bridge = not filled_bridge

                            infil_exfil, z_roof, z, q_infil_t_current = update_top_q(z, h, q, z_roof,
                                                                                    idx_up, idx_do,
                                                                                    survey_up, survey_do,
                                                                                    A_bridge, k_bridge, q_infil_t_current, dt,
                                                                                    local_motion_time, total_motion_time, emptying_bridge,
                                                                                    z_roof_start, z_roof_end, z_bath_start, z_bath_end,
                                                                                    stop_motion= True)

                            local_motion_time = 0.

                        else:
                            # Total time is not reached...
                            #   ... so continue the movement

                            infil_exfil, z_roof, z, q_infil_t_current = update_top_q(z, h, q, z_roof,
                                                                                    idx_up, idx_do,
                                                                                    survey_up, survey_do,
                                                                                    A_bridge, k_bridge, q_infil_t_current, dt,
                                                                                    local_motion_time, total_motion_time, emptying_bridge,
                                                                                    z_roof_start, z_roof_end, z_bath_start, z_bath_end)

                    else:

                        if infil_exfil is not None:

                            if motion_completed:
                                # The bridge is not moving and the infiltration/exfiltration exists

                                # We can start to restore the bridge as it was before the overflow...

                                delta_res_time = delta_res_time_def / 5.

                                bridge_in_motion = True
                                local_motion_time = 0.
                                motion_completed = False

                                emptying_bridge = True
                                starting_time = t

                                infil_exfil, z_roof, z, q_infil_t_current = update_top_q(z, h, q, z_roof,
                                                                                        idx_up, idx_do,
                                                                                        survey_up, survey_do,
                                                                                        A_bridge, k_bridge, q_infil_t_current, dt,
                                                                                        local_motion_time, total_motion_time, emptying_bridge,
                                                                                        z_roof_start, z_roof_end, z_bath_start, z_bath_end,
                                                                                            )

            t+=dt
            pbar.update(dt)


    return res


# --------------------
# END Problems section
# --------------------


# ----------------
# PLOTTING SECTION
# ----------------
import matplotlib.animation as animation

def plot_bridge(ax:plt.Axes, x:np.ndarray,
         h1:np.ndarray, h2:np.ndarray,
         q1:np.ndarray, q2:np.ndarray,
         z:np.ndarray, z_bridge:np.ndarray,
         hu:float):

    u1=np.zeros_like(q1)
    u2=np.zeros_like(q1)

    u1[1:-1] = q1[1:-1]/h1[1:-1]
    u2[1:-1] = q2[1:-1]/np.minimum(h2[1:-1],z_bridge[1:-1]-z[1:-1])

    ax.plot(x[1:-1], z[1:-1], label = 'z')
    ax.plot(x[1:-1], z_bridge[1:-1], label = 'bridge')

    ax.plot(x[1:-1], z[1:-1] + h1[1:-1], label = 'z + h1')
    ax.plot(x[1:-1], z[1:-1] + h2[1:-1], label = 'z + h2')

    ax.plot(x[1:-1], q1[1:-1], label = 'q')

    under_bridge = np.where(h2 > z_bridge - z)[0]
    free_surface = np.where(h2 <= z_bridge - z)[0]

    ax.plot(x[1:-1], z[1:-1] + h1[1:-1] + u1[1:-1]**2/2/9.81, label = 'head1')

    ax.plot(x[1:-1], z[1:-1] + h2[1:-1] + u2[1:-1]**2/2/9.81, label = 'head2')
    # ax.plot(x[free_surface], (z[free_surface] + h2[free_surface] + u2[free_surface]**2/2/9.81) * h2[free_surface], label = 'head2 free surface')

    if hu != 99999.:
        ax.plot(x[1:-1], z[1:-1]+hu, linestyle='--', label = 'h uniform')
    ax.legend()

def plot_hedge(ax:plt.Axes, x:np.ndarray,
         h1:np.ndarray, h2:np.ndarray,
         q1:np.ndarray, q2:np.ndarray,
         z:np.ndarray, hu:float,
         theta:np.ndarray):

    u1=np.zeros_like(q1)
    u2=np.zeros_like(q1)

    u1[1:-1] = q1[1:-1]/h1[1:-1]
    u2[1:-1] = q2[1:-1]/(h2[1:-1]*theta[1:-1])

    ax.plot(x[1:-1], z[1:-1], label = 'z')

    ax.plot(x[1:-1], z[1:-1] + h1[1:-1], label = 'z + h1')
    ax.plot(x[1:-1], z[1:-1] + h2[1:-1], label = 'z + h2')

    ax.plot(x[1:-1], u1[1:-1], label = 'u1')
    ax.plot(x[1:-1], u2[1:-1], label = 'u2')

    # ax.plot(x[1:-1], z[1:-1] + h1[1:-1] + u1[1:-1]**2/2/9.81, label = 'head1')
    # ax.plot(x[1:-1], z[1:-1] + h2[1:-1] + u2[1:-1]**2/2/9.81, label = 'head2')

    ax.plot(x[1:-1], z[1:-1]+hu, linestyle='--', label = 'h uniform')
    ax.legend()


def animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y,  res:list[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray, tuple[int,int,float,float,float]],
                                x:np.ndarray, z_ini:np.ndarray, hu:float, z_null:float, length:float, title:str= "Bridge", motion_duration=300.):
    fig, axes = plt.subplots(2,1)

    all_q_middle = [cur[2][len(dom)//2] for cur in res]
    all_q_inf_ex = [cur[5][2] for cur in res]

    all_q_up = [cur[2][1] for cur in res]
    all_q_down = [cur[2][-2] for cur in res]

    all_times = [cur[0] for cur in res]
    idx_Froude = [int(len(dom)*cur) for cur in np.linspace(0,100,11,True)/100]
    idx_Froude[0]  += 5
    idx_Froude[-1] -= 5
    x_Froude = x[idx_Froude]
    Froude = np.zeros_like(x_Froude)

    def update(frame):
        ax:plt.Axes
        ax = axes[0]
        ax.clear()

        z:np.ndarray
        t, h, q, z, z_roof, inf_ex = res[frame]

        for i, idx in enumerate(idx_Froude):
            if h[idx]==0.:
                Froude[i] = 0.
            else:
                Froude[i] = q[idx] / h[idx] /np.sqrt(9.81*h[idx])

        ax.fill_between(x[1:-1], z[1:-1], z[1:-1] + h[1:-1], color='blue', alpha=0.5)
        ax.plot(x[1:-1], z[1:-1] + h[1:-1], label='water level [m]', color='blue')

        ax.fill_between(x[1:-1], np.ones(z.shape)[1:-1] * z.min(), z[1:-1], color='brown', alpha=0.5)
        ax.plot(x[1:-1], z[1:-1], label='bottom level [m]', color='brown')

        slice_roof = z_roof != z_null
        ax.fill_between(x[slice_roof], z_roof[slice_roof], np.ones(z.shape)[slice_roof] * z_null, color='grey', alpha=0.5)
        ax.plot(x[slice_roof], z_roof[slice_roof], label='roof level [m]', color='grey')

        # ax.plot(x[1:-1], z_ini[1:-1] + hu, linestyle='--', label='h uniform')
        ax.plot(x[1:-1], q[1:-1], linestyle='-', label='flow rate [$m^2/s$]', color='black', linewidth=1.5)
        ax.legend(loc='upper right')

        ax.fill(poly_bridge_x, poly_bridge_y, color='black', alpha=0.8)

        q_middle = q[len(dom)//2]
        q_inf_ex = inf_ex[2]

        txt = f'Total flow rate {q_middle+q_inf_ex:.2f} $m^2/s$'
        txt += f'\nOverflow  = {q_middle:.2f} $m^2/s$ - {q_middle/(q_inf_ex+q_middle)*100:.2f} %'
        txt += f'\nUnderflow = {q_inf_ex:.2f} $m^2/s$ - {q_inf_ex/(q_inf_ex+q_middle)*100:.2f} %'

        in_txt = '$k_{loss}$ ='
        txt += f'\n\nMotion time = {motion_duration:.1f} s -- {in_txt} {inf_ex[-1]:.2f}'

        ax.text(x[len(dom)//2+8], 11., txt, fontsize=9)

        for posFroude, curFroude in zip(x_Froude, Froude):
            ax.text(posFroude, 8., f'Fr = {curFroude:.2f}', fontsize=9, horizontalalignment='center')

        ax.set_xlim(0, 500)
        ax.set_xticks(np.arange(0, 501, 50))

        ax.grid(axis='x')

        ax.set_ylim(0, 20)
        ax.set_title(f'{title} - Length = {length:.1f} m - Time = {t:.1f} s')

        ax = axes[1]
        ax.clear()

        ax.plot(all_times[:frame], all_q_middle[:frame], label='Overflow', color='blue')
        ax.plot(all_times[:frame], all_q_inf_ex[:frame], label='Underflow', color='red')
        ax.plot(all_times[:frame], [qinf + qmiddle for qinf, qmiddle in zip(all_q_inf_ex[:frame], all_q_middle[:frame])], label='Total', color='black')

        ax.plot(all_times[:frame], all_q_up[:frame], label='Upstream', color='black', linestyle='--', linewidth=1.)
        ax.plot(all_times[:frame], all_q_down[:frame], label='Downstream', color='black', linestyle='-.', linewidth=1.)

        ax.legend(loc='upper right')
        ax.set_title('Flow rate')
        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Flow rate [$m^2/s$]')

        ax.set_ylim(0, 20)
        ax.set_xlim(0, all_times[-1])
        ax.set_xticks(np.arange(0, all_times[-1]+10, 900))
        ax.grid()

    fig.set_size_inches(20,8)
    update(0)
    fig.tight_layout()

    ani = animation.FuncAnimation(fig, update, frames=len(res), repeat=True)

    return ani


# -------------
# REAL PROBLEMS
# -------------

def lake_at_rest():
    """ Compute Lake at rest problem

    The problem is a simple steady state problem with a bridge in the middle of the domain.
    The bridge is a simple flat bridge with a height of 2 m.

    No discharge and no water movement is expected.
    """

    length = 500.
    dx = 1.
    CN = 0.4
    h0 = 4. # Initial water depth
    q0 = 0. # Initial discharge
    n  = 0.025
    slope = 0 #1e-4

    hu = 0

    dom, x, z = domain(length, dx, slope)
    x = np.array(x)

    # Bridge roof level is 10 m everywhere except in the middle of the domain
    z_bridge = np.ones_like(z) * 10.
    z_bridge[len(dom)//2-5:len(dom)//2+5] = z[len(dom)//2-5:len(dom)//2+5] + 2.

    fig, axes = plt.subplots(3,1)

    # free surface flow
    h1, q1 = problem(dom, z, h0, q0, dx, CN, n)
    # partially pressurized flow
    h2, q2 = problem_bridge(dom, z, z_bridge, h0, q0, dx, CN, n)

    assert np.allclose(h1[1:-1], h0), 'Free surface flow is not steady state'
    assert np.allclose(q1[1:-1], q0), 'Free surface flow is not steady state'
    assert np.allclose(h2[1:-1], h0), 'Partially pressurized flow is not steady state'
    assert np.allclose(q2[1:-1], q0), 'Partially pressurized flow is not steady state'

    plot_bridge(axes[0], x, h1, h2, q1, q2, z, z_bridge, hu)

    # increasing water depth
    h0 += 1.

    # free surface flow
    h1, q1 = problem(dom, z, h0+1., q0, dx, CN, n)
    # partially pressurized flow
    h2, q2 = problem_bridge(dom, z, z_bridge, h0, q0, dx, CN, n)

    assert np.allclose(h1[1:-1], h0+1.), 'Free surface flow is not steady state'
    assert np.allclose(q1[1:-1], q0), 'Free surface flow is not steady state'
    assert np.allclose(h2[1:-1], h0), 'Partially pressurized flow is not steady state'
    assert np.allclose(q2[1:-1], q0), 'Partially pressurized flow is not steady state'

    plot_bridge(axes[1], x, h1, h2, q1, q2, z, z_bridge, hu)

    # increasing water depth
    h0 += 1.

    # free surface flow
    h1, q1 = problem(dom, z, h0+2., q0, dx, CN, n)
    # partially pressurized flow
    h2, q2 = problem_bridge(dom, z, z_bridge, h0, q0, dx, CN, n)

    assert np.allclose(h1[1:-1], h0+2.), 'Free surface flow is not steady state'
    assert np.allclose(q1[1:-1], q0), 'Free surface flow is not steady state'
    assert np.allclose(h2[1:-1], h0), 'Partially pressurized flow is not steady state'
    assert np.allclose(q2[1:-1], q0), 'Partially pressurized flow is not steady state'

    plot_bridge(axes[2], x, h1, h2, q1, q2, z, z_bridge, hu)

    fig.set_size_inches(15, 10)
    fig.tight_layout()

    return fig, axes


def water_line():
    """ Compute Water line problems

    Length = 500 m
    dx = 1 m
    CN = 0.4
    h0 = 4 m
    q0 = 7 m^2/s
    n  = 0.025
    slope = 1e-4
    """

    length = 500.
    dx = 1.
    CN = 0.4
    h0 = 4.
    q0 = 7.
    n  = 0.025
    slope = 1e-4

    dom, x, z = domain(length, dx, slope)
    x = np.array(x)

    hu = uniform_waterdepth(slope, q0, n)

    # bridge roof level is 10 m everywhere except in the middle of the domain
    # where the bridge is located.
    # The bridge is a flat bridge with a height of 2 m.
    z_bridge = np.ones_like(z) * 10.
    z_bridge[len(dom)//2-5:len(dom)//2+5] = z[len(dom)//2-5:len(dom)//2+5] + 2.

    fig, axes = plt.subplots(3,1)

    h1, q1 = problem(dom, z, h0, q0, dx, CN, n)
    h2, q2 = problem_bridge(dom, z, z_bridge, h0, q0, dx, CN, n)

    plot_bridge(axes[0], x, h1, h2, q1, q2, z, z_bridge, hu)

    h1, q1 = problem(dom, z, h0+1., q0, dx, CN, n)
    h2, q2 = problem_bridge(dom, z, z_bridge, h0+1., q0, dx, CN, n)

    plot_bridge(axes[1], x, h1, h2, q1, q2, z, z_bridge, hu)

    h1, q1 = problem(dom, z, h0+2., q0, dx, CN, n)
    h2, q2 = problem_bridge(dom, z, z_bridge, h0+2., q0, dx, CN, n)

    plot_bridge(axes[2], x, h1, h2, q1, q2, z, z_bridge, hu)

    fig.set_size_inches(20, 10)
    fig.tight_layout()

    return fig, axes

def water_line_noloss_noslope():
    """ Compute Water line problems

    Length = 500 m
    dx = 1 m
    CN = 0.4
    h0 = 4 m
    q0 = 7 m^2/s
    n  = 0.0
    slope = 0.0
    """

    length = 500.
    dx = 1.
    CN = 0.4
    h0 = 4.
    q0 = 7.
    n  = 0.
    slope = 0.

    dom, x, z = domain(length, dx, slope)
    x = np.array(x)

    hu = uniform_waterdepth(slope, q0, n)

    # bridge roof level is 10 m everywhere except in the middle of the domain
    # where the bridge is located.
    # The bridge is a flat bridge with a height of 2 m.
    z_bridge = np.ones_like(z) * 10.
    z_bridge[len(dom)//2-5:len(dom)//2+5] = z[len(dom)//2-5:len(dom)//2+5] + 2.

    fig, axes = plt.subplots(3,1)

    h1, q1 = problem(dom, z, h0, q0, dx, CN, n)
    h2, q2 = problem_bridge(dom, z, z_bridge, h0, q0, dx, CN, n)

    plot_bridge(axes[0], x, h1, h2, q1, q2, z, z_bridge, hu)

    h1, q1 = problem(dom, z, h0+1., q0, dx, CN, n)
    h2, q2 = problem_bridge(dom, z, z_bridge, h0+1., q0, dx, CN, n)

    plot_bridge(axes[1], x, h1, h2, q1, q2, z, z_bridge, hu)

    h1, q1 = problem(dom, z, h0+2., q0, dx, CN, n)
    h2, q2 = problem_bridge(dom, z, z_bridge, h0+2., q0, dx, CN, n)

    plot_bridge(axes[2], x, h1, h2, q1, q2, z, z_bridge, hu)

    fig.set_size_inches(20, 10)
    fig.tight_layout()

    return fig, axes

def water_lines():
    """ Compute multiple water lines problems.

    Evaluate the head loss due to the bridge and compare
    to theoretical fomula.
    """

    length = 500.
    dx = 1.
    CN = 0.4
    h0 = 4.
    q0 = 7.
    n  = 0. #0.025
    slope = 0 #1e-4

    dom, x, z = domain(length, dx, slope)
    x = np.array(x)

    hu = 0. #uniform_waterdepth(slope, q0, n)

    b_bridge = 2.

    z_bridge = np.ones_like(z) * 10.
    z_bridge[len(dom)//2-5:len(dom)//2+5] = z[len(dom)//2-5:len(dom)//2+5] + b_bridge

    idx_before_bridge = len(dom)//2-5 -2
    idx_after_bridge  = len(dom)//2+5 +2
    idx_bridge = len(dom)//2

    h0 = 4.5
    res = problem_bridge_multiple_steadystates(dom, z, z_bridge, h0, 3.5, 20., dx, CN, n)

    fig, axes = plt.subplots(2,1)

    ax:plt.Axes

    ax = axes[0]
    for cur in res:
        ax.plot(x[1:-1], z[1:-1]+cur[1][1:-1], label = f't = {cur[0]:.1f}')
    ax.plot(x[1:-1], z[1:-1]+hu, linestyle='--', label = 'h uniform')
    ax.plot(x[1:-1], z_bridge[1:-1], label = 'bridge')
    ax.plot(x[1:-1], z[1:-1], label = 'z')
    ax.legend()


    # Head losses

    # pressure before, after and at the bridge
    press_before = [cur[1][idx_before_bridge] for cur in res]
    press_after  = [cur[1][idx_after_bridge] for cur in res]
    press_bridge = [cur[1][idx_bridge] for cur in res]

    h_bridge = np.minimum(press_bridge, z_bridge[idx_bridge] - z[idx_bridge])

    # flow rate before, after and at the bridge
    q_before = [cur[2][idx_before_bridge] for cur in res]
    q_after  = [cur[2][idx_after_bridge] for cur in res]
    q_bridge = [cur[2][idx_bridge] for cur in res]

    # velocity before, after and at the bridge
    u_before = [q/h for q,h in zip(q_before, press_before)]
    u_after  = [q/h for q,h in zip(q_after,  press_after)]
    u_bridge = [q/h for q,h in zip(q_bridge, h_bridge)]

    # head before, after and at the bridge
    head_before = [z[idx_before_bridge] + press_before[i] + u_before[i]**2/2/9.81 for i in range(len(res))]
    head_after  = [z[idx_after_bridge]  + press_after[i]  + u_after[i]**2/2/9.81  for i in range(len(res))]
    head_bridge = [z[idx_bridge]        + press_bridge[i] + u_bridge[i]**2/2/9.81 for i in range(len(res))]

    # head losses
    delta_head_total = [head_before[i] - head_after[i] for i in range(len(res))]
    delta_head_up    = [head_before[i] - head_bridge[i] for i in range(len(res))]
    delta_head_do    = [head_bridge[i] - head_after[i] for i in range(len(res))]

    ax = axes[1]

    ax.plot(delta_head_up, [head_loss_contraction(q, h1, h2) for q,h1,h2 in zip(q_bridge, press_before, h_bridge)], marker='*', label = 'Contraction Loss')
    ax.plot(delta_head_do, [head_loss_enlargment(q, h1, h2)  for q,h1,h2 in zip(q_bridge,  h_bridge, press_after)],  marker='o', label = 'Enlargment Loss')
    ax.plot(delta_head_total, [head_loss_contract_enlarge(q,h1,h2,h3) for q,h1,h2,h3 in zip(q_bridge, press_before, h_bridge, press_after)], marker='x', label = 'Total Loss')

    ax.set_xlabel('Computed $\Delta H$ [m]')
    ax.set_ylabel('Theoretical $\Delta H$ [m]')

    ax.plot([0,1],[0,1], linestyle='-', linewidth=2, color='black')
    ax.set_aspect('equal')
    ax.legend()

    fig.set_size_inches(20, 10)
    fig.tight_layout()

    return fig, axes


def unsteady_without_bedmotion():
    """
    Compute unsteady problem without bed motion.

    The downstream boundary condition rises and decreases.
    """

    length = 500.
    dx = 1.
    CN = 0.4
    h0 = 4.
    q0 = 7.
    n  = 0. #0.025
    slope = 0 #1e-4

    dom, x, z = domain(length, dx, slope)
    x = np.array(x)

    hu = 0. #uniform_waterdepth(slope, q0, n)

    b_bridge = 2.

    z_bridge = np.ones_like(z) * 10.
    z_bridge[len(dom)//2-5:len(dom)//2+5] = z[len(dom)//2-5:len(dom)//2+5] + b_bridge

    idx_before_bridge = len(dom)//2-5 -2
    idx_after_bridge  = len(dom)//2+5 +2
    idx_bridge = len(dom)//2

    h0 = 1.5
    res = problem_bridge_unsteady(dom, z, z_bridge, h0, q0, dx, CN, n)

    fig, axes = plt.subplots(2,1)

    ax:plt.Axes

    ax = axes[0]
    for cur in res:
        ax.plot(x[1:-1], z[1:-1]+cur[1][1:-1], label = f't = {cur[0]:.1f}')
    ax.plot(x[1:-1], z[1:-1]+hu, linestyle='--', label = 'h uniform')
    ax.plot(x[1:-1], z_bridge[1:-1], label = 'bridge')
    ax.plot(x[1:-1], z[1:-1], label = 'z')
    ax.legend()

    press_before = [cur[1][idx_before_bridge] for cur in res]
    press_after  = [cur[1][idx_after_bridge] for cur in res]
    press_bridge = [cur[1][idx_bridge] for cur in res]

    h_bridge = np.minimum(press_bridge, z_bridge[idx_bridge] - z[idx_bridge])

    q_before = [cur[2][idx_before_bridge] for cur in res]
    q_after  = [cur[2][idx_after_bridge] for cur in res]
    q_bridge = [cur[2][idx_bridge] for cur in res]

    u_before = [q/h for q,h in zip(q_before, press_before)]
    u_after  = [q/h for q,h in zip(q_after,  press_after)]
    u_bridge = [q/h for q,h in zip(q_bridge, h_bridge)]

    head_before = [z[idx_before_bridge] + press_before[i] + u_before[i]**2/2/9.81 for i in range(len(res))]
    head_after  = [z[idx_after_bridge]  + press_after[i]  + u_after[i]**2/2/9.81  for i in range(len(res))]
    head_bridge = [z[idx_bridge]        + press_bridge[i] + u_bridge[i]**2/2/9.81 for i in range(len(res))]

    delta_head_total = [head_before[i] - head_after[i] for i in range(len(res))]
    delta_head_up    = [head_before[i] - head_bridge[i] for i in range(len(res))]
    delta_head_do    = [head_bridge[i] - head_after[i] for i in range(len(res))]

    ax = axes[1]

    ax.plot(delta_head_up, [head_loss_contraction(q, h1, h2) for q,h1,h2 in zip(q_bridge, press_before, h_bridge)], marker='*', label = 'Contraction Loss')
    ax.plot(delta_head_do, [head_loss_enlargment(q, h1, h2)  for q,h1,h2 in zip(q_bridge,  h_bridge, press_after)],  marker='o', label = 'Enlargment Loss')
    ax.plot(delta_head_total, [head_loss_contract_enlarge(q,h1,h2,h3) for q,h1,h2,h3 in zip(q_bridge, press_before, h_bridge, press_after)], marker='x', label = 'Total Loss')

    ax.set_xlabel('Computed $\Delta H$ [m]')
    ax.set_ylabel('Theoretical $\Delta H$ [m]')

    ax.plot([0,1],[0,1], linestyle='-', linewidth=2, color='black')
    ax.set_aspect('equal')
    ax.legend()

    fig.set_size_inches(20, 10)
    fig.tight_layout()

    return fig, axes


def unsteady_with_bedmotion(problems:list[int], save_video:bool = False) -> list[animation.FuncAnimation]:
    """
    Unsteady problem with bed motion if overflowing occurs.

    :param problems: list of problems to solve

    Problems :
        2 - Rectangular bridge - Length = 20 m  (will compute 21, 22 and 23)
        6 - Rectangular bridge - Length = 60 m  (will compute 61, 62 and 63)
        7 - V-shape bridge - Length = 20 m      (will compute 71, 72 and 73)
        8 - U-shape bridge - Length = 20 m      (will compute 81, 82 and 83)
        9 - Culvert - Length = 100 m            (will compute 91, 92 and 93)

        21 - Rectangular bridge - Length = 20 m - Unsteady downstream bc
        22 - Rectangular bridge - Length = 20 m - Hydrograph
        23 - Rectangular bridge - Length = 20 m - Hydrograph 2 steps

        61 - Rectangular bridge - Length = 60 m - Unsteady downstream bc
        62 - Rectangular bridge - Length = 60 m - Hydrograph
        63 - Rectangular bridge - Length = 60 m - Hydrograph 2 steps

        71 - V-shape bridge - Length = 20 m - Unsteady downstream bc
        72 - V-shape bridge - Length = 20 m - Hydrograph
        73 - V-shape bridge - Length = 20 m - Hydrograph 2 steps

        81 - U-shape bridge - Length = 20 m - Unsteady downstream bc
        82 - U-shape bridge - Length = 20 m - Hydrograph
        83 - U-shape bridge - Length = 20 m - Hydrograph 2 steps

        91 - Culvert - Length = 100 m - Unsteady downstream bc
        92 - Culvert - Length = 100 m - Hydrograph
        93 - Culvert - Length = 100 m - Hydrograph 2 steps

    """
    length = 500.
    dx = 1.
    CN = 0.4
    h0 = 4.
    q0 = 7.
    n  = 0.025
    slope = 0 #1e-4

    dom, x, z = domain(length, dx, slope)
    x = np.array(x)

    hu = uniform_waterdepth(slope, q0, n)

    anims=[]

    if 2 in problems or 21 in problems or 22 in problems or 23 in problems or 24 in problems:
        # Rectangular bridge - Lenght = 20 m

        CN = 0.4

        if 2 in problems:
            scenarios = ['unsteady_downstream_bc',
                         'hydrograph',
                         'hydrograph_2steps',
                        #  'Gauss',
                         ]
        elif 21 in problems:
            scenarios = ['unsteady_downstream_bc']
        elif 22 in problems:
            scenarios = ['hydrograph']
        elif 23 in problems:
            scenarios = ['hydrograph_2steps']
        elif 24 in problems:
            scenarios = ['Gauss']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            motion_duration = 300.
            len_bridge = 20
            z_roof_null = 10.
            min_overflow = 0.25

            h0 = 1.5

            h_under_bridge = 3.5
            h_deck_bridge = 0.75

            slice_bridge = slice(int(len(dom)//2-len_bridge//2),int(len(dom)//2+len_bridge//2))
            slice_bridge_up = slice(int(len(dom)//2+(len_bridge//2-1)),int(len(dom)//2-(len_bridge//2+1)),-1)

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck = np.ones_like(z) * z_roof_null

            for idx in range(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2):
                z_bridge[idx] = z[idx] + h_under_bridge
                z_deck[idx] = z_bridge[idx] + h_deck_bridge

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z,
                                               z_bridge, z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration= motion_duration,
                                               scenario_bc= scenario,
                                               min_overflow= min_overflow)

            ani = animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y, res, x, z_ini, hu, z_roof_null, len_bridge, motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'bridge_L20_{scenario}.mp4',
                        writer='ffmpeg', fps=5,
                        progress_callback=update_func)

            anims.append(ani)

    if 6 in problems or 61 in problems or 62 in problems or 63 in problems or 64 in problems:
        # Rectangular bridge - Lenght = 60 m

        CN = 0.2

        if 6 in problems:
            scenarios = ['unsteady_downstream_bc',
                         'hydrograph',
                         'hydrograph_2steps',
                        #  'Gauss',
                         ]

        elif 61 in problems:
            scenarios = ['unsteady_downstream_bc']
        elif 62 in problems:
            scenarios = ['hydrograph']
        elif 63 in problems:
            scenarios = ['hydrograph_2steps']
        elif 64 in problems:
            scenarios = ['Gauss']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            motion_duration = 300.
            z_roof_null = 10.
            min_overflow = 0.25

            h_under_bridge = 3.5
            h_deck_bridge = 0.75
            len_bridge = 60
            q0 = 6.
            h0 = 1.5

            slice_bridge = slice(int(len(dom)//2-len_bridge//2),int(len(dom)//2+len_bridge//2))
            slice_bridge_up = slice(int(len(dom)//2+(len_bridge//2-1)),int(len(dom)//2-(len_bridge//2+1)),-1)

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck = np.ones_like(z) * z_roof_null

            for idx in range(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2):
                z_bridge[idx] = z[idx] + h_under_bridge
                z_deck[idx] = z_bridge[idx] + h_deck_bridge

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z, z_bridge,
                                               z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration=motion_duration,
                                               scenario_bc=scenario,
                                               min_overflow=min_overflow)

            ani = animate_bridge_unsteady_topo(dom, res, x, z_ini, hu, z_roof_null, len_bridge, motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'bridge_L60{scenario}.mp4',
                        writer='ffmpeg', fps=5,
                        progress_callback=update_func)

            anims.append(ani)

    if 9 in problems or 91 in problems or 92 in problems or 93 in problems or 94 in problems:
        # Culvert

        CN = 0.4

        if 9 in problems:
            scenarios = ['unsteady_downstream_bc_culvert',
                         'hydrograph_culvert',
                         'hydrograph_2steps_culvert',
                        #  'Gauss',
                         ]

        elif 91 in problems:
            scenarios = ['unsteady_downstream_bc_culvert']
        elif 92 in problems:
            scenarios = ['hydrograph_culvert']
        elif 93 in problems:
            scenarios = ['hydrograph_2steps_culvert']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            motion_duration = 300.
            z_roof_null = 10.
            min_overflow = 0.25

            h_under_bridge = 1.5
            h_deck_bridge = 4.0
            len_bridge = 100
            h0 = 0.8
            q0 = 1.

            slice_bridge = slice(int(len(dom)//2-len_bridge//2),int(len(dom)//2+len_bridge//2))
            slice_bridge_up = slice(int(len(dom)//2+(len_bridge//2-1)),int(len(dom)//2-(len_bridge//2+1)),-1)

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck = np.ones_like(z) * z_roof_null

            for idx in range(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2):
                z_bridge[idx] = z[idx] + h_under_bridge
                z_deck[idx] = z_bridge[idx] + h_deck_bridge

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z, z_bridge,
                                               z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration=motion_duration,
                                               scenario_bc=scenario,
                                               min_overflow=min_overflow)

            ani = animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y,  res, x, z_ini, hu, z_roof_null, len_bridge, title='Culvert', motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'culvert_{scenario}.mp4',
                            writer='ffmpeg', fps=5,
                            progress_callback=update_func)

            anims.append(ani)

    if 7 in problems or 71 in problems or 72 in problems or 73 in problems or 74 in problems:
        # V-shape Bridge

        CN = 0.4

        if 7 in problems:
            scenarios = ['unsteady_downstream_bc',
                         'hydrograph',
                         'hydrograph_2steps',
                        #  'Gauss',
                         ]
        elif 71 in problems:
            scenarios = ['unsteady_downstream_bc']
        elif 72 in problems:
            scenarios = ['hydrograph']
        elif 73 in problems:
            scenarios = ['hydrograph_2steps']
        elif 74 in problems:
            scenarios = ['Gauss']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            motion_duration = 300.
            z_roof_null = 10.
            min_overflow = 0.25

            h_under_bridge = 3.5
            h_deck_bridge = 0.75
            len_bridge = 20

            h0 = 1.5

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck   = np.ones_like(z) * z_roof_null

            slice_bridge = slice(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2)
            slice_bridge_up = slice(len(dom)//2+(len_bridge//2-1),len(dom)//2-(len_bridge//2+1),-1)

            for idx in range(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2):
                decal = abs(idx - (len(dom)//2))
                z_bridge[idx] = z[idx] + h_under_bridge + 0.05 * decal
                z_deck[idx] = h_under_bridge + h_deck_bridge

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z,
                                               z_bridge, z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration=motion_duration,
                                               scenario_bc=scenario,
                                               min_overflow= min_overflow)

            ani = animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y,  res, x, z_ini, hu, z_roof_null, len_bridge, motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'bridge_Vshape{scenario}.mp4',
                        writer='ffmpeg', fps=5,
                        progress_callback=update_func)

            anims.append(ani)

    if 8 in problems or 81 in problems or 82 in problems or 83 in problems or 84 in problems:
        # U-shape Bridge

        CN = 0.4

        if 8 in problems:
            scenarios = ['unsteady_downstream_bc',
                         'hydrograph',
                         'hydrograph_2steps',
                        #  'Gauss',
                         ]
        elif 81 in problems:
            scenarios = ['unsteady_downstream_bc']
        elif 82 in problems:
            scenarios = ['hydrograph']
        elif 83 in problems:
            scenarios = ['hydrograph_2steps']
        elif 84 in problems:
            scenarios = ['Gauss']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            motion_duration = 300.
            z_roof_null = 10.
            min_overflow = 0.25

            h_under_bridge = 3.5
            h_deck_bridge = 0.4
            len_bridge = 20

            h0 = 1.5

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck   = np.ones_like(z) * z_roof_null

            slice_bridge = slice(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2)
            slice_bridge_up = slice(len(dom)//2+(len_bridge//2-1),len(dom)//2-(len_bridge//2+1),-1)

            z_bridge[slice_bridge] = z[slice_bridge] + h_under_bridge
            z_deck[slice_bridge]   = z_bridge[slice_bridge] + h_deck_bridge

            idx_up = len(dom)//2-len_bridge//2
            idx_down = len(dom)//2+len_bridge//2-1

            z_bridge[idx_up] -= .4
            z_bridge[idx_up+1] -= .4

            z_bridge[idx_down] -= .4
            z_bridge[idx_down-1] -= .4

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z,
                                               z_bridge, z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration=motion_duration,
                                               scenario_bc=scenario,
                                               min_overflow= min_overflow)

            ani = animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y,  res, x, z_ini, hu, z_roof_null, len_bridge, motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'bridge_Ushape{scenario}.mp4',
                        writer='ffmpeg', fps=5,
                        progress_callback=update_func)

            anims.append(ani)

    return anims

def unsteady_with_bedmotion_interval(problems:list[int], save_video:bool = False, update_interval:float = 0., motion_duration:float = 300.) -> list[animation.FuncAnimation]:
    """
    Unsteady problem with bed motion if overflowing occurs.

    :param problems: list of problems to solve

    Problems :
        2 - Rectangular bridge - Length = 20 m  (will compute 21, 22 and 23)
        6 - Rectangular bridge - Length = 60 m  (will compute 61, 62 and 63)
        7 - V-shape bridge - Length = 20 m      (will compute 71, 72 and 73)
        8 - U-shape bridge - Length = 20 m      (will compute 81, 82 and 83)
        9 - Culvert - Length = 100 m            (will compute 91, 92 and 93)

        21 - Rectangular bridge - Length = 20 m - Unsteady downstream bc
        22 - Rectangular bridge - Length = 20 m - Hydrograph
        23 - Rectangular bridge - Length = 20 m - Hydrograph 2 steps

        61 - Rectangular bridge - Length = 60 m - Unsteady downstream bc
        62 - Rectangular bridge - Length = 60 m - Hydrograph
        63 - Rectangular bridge - Length = 60 m - Hydrograph 2 steps

        71 - V-shape bridge - Length = 20 m - Unsteady downstream bc
        72 - V-shape bridge - Length = 20 m - Hydrograph
        73 - V-shape bridge - Length = 20 m - Hydrograph 2 steps

        81 - U-shape bridge - Length = 20 m - Unsteady downstream bc
        82 - U-shape bridge - Length = 20 m - Hydrograph
        83 - U-shape bridge - Length = 20 m - Hydrograph 2 steps

        91 - Culvert - Length = 100 m - Unsteady downstream bc
        92 - Culvert - Length = 100 m - Hydrograph
        93 - Culvert - Length = 100 m - Hydrograph 2 steps

    """
    length = 500.
    dx = 1.
    CN = 0.4
    h0 = 4.
    q0 = 7.
    n  = 0.025
    slope = 0 #1e-4

    dom, x, z = domain(length, dx, slope)
    x = np.array(x)

    hu = uniform_waterdepth(slope, q0, n)

    anims=[]

    if 2 in problems or 21 in problems or 22 in problems or 23 in problems or 24 in problems:
        # Rectangular bridge - Lenght = 20 m

        CN = 0.4

        if 2 in problems:
            scenarios = ['unsteady_downstream_bc',
                         'hydrograph',
                         'hydrograph_2steps',
                        #  'Gauss',
                         ]
        elif 21 in problems:
            scenarios = ['unsteady_downstream_bc']
        elif 22 in problems:
            scenarios = ['hydrograph']
        elif 23 in problems:
            scenarios = ['hydrograph_2steps']
        elif 24 in problems:
            scenarios = ['Gauss']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            len_bridge = 20
            z_roof_null = 10.
            min_overflow = 0.25

            h0 = 1.5

            h_under_bridge = 3.5
            h_deck_bridge = 0.75

            slice_bridge = slice(int(len(dom)//2-len_bridge//2),int(len(dom)//2+len_bridge//2))
            slice_bridge_up = slice(int(len(dom)//2+(len_bridge//2-1)),int(len(dom)//2-(len_bridge//2+1)),-1)

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck = np.ones_like(z) * z_roof_null

            for idx in range(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2):
                z_bridge[idx] = z[idx] + h_under_bridge
                z_deck[idx] = z_bridge[idx] + h_deck_bridge

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z,
                                               z_bridge, z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration= motion_duration,
                                               scenario_bc= scenario,
                                               min_overflow= min_overflow,
                                               updating_time_interval=update_interval)

            ani = animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y, res, x, z_ini, hu, z_roof_null, len_bridge, motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'bridge_L20_{scenario}.mp4',
                        writer='ffmpeg', fps=5,
                        progress_callback=update_func)

            anims.append(ani)

    if 6 in problems or 61 in problems or 62 in problems or 63 in problems or 64 in problems:
        # Rectangular bridge - Lenght = 60 m

        CN = 0.2

        if 6 in problems:
            scenarios = ['unsteady_downstream_bc',
                         'hydrograph',
                         'hydrograph_2steps',
                        #  'Gauss',
                         ]

        elif 61 in problems:
            scenarios = ['unsteady_downstream_bc']
        elif 62 in problems:
            scenarios = ['hydrograph']
        elif 63 in problems:
            scenarios = ['hydrograph_2steps']
        elif 64 in problems:
            scenarios = ['Gauss']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            z_roof_null = 10.
            min_overflow = 0.25

            h_under_bridge = 3.5
            h_deck_bridge = 0.75
            len_bridge = 60
            q0 = 6.
            h0 = 1.5

            slice_bridge = slice(int(len(dom)//2-len_bridge//2),int(len(dom)//2+len_bridge//2))
            slice_bridge_up = slice(int(len(dom)//2+(len_bridge//2-1)),int(len(dom)//2-(len_bridge//2+1)),-1)

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck = np.ones_like(z) * z_roof_null

            for idx in range(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2):
                z_bridge[idx] = z[idx] + h_under_bridge
                z_deck[idx] = z_bridge[idx] + h_deck_bridge

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z, z_bridge,
                                               z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration=motion_duration,
                                               scenario_bc=scenario,
                                               min_overflow=min_overflow,
                                               updating_time_interval=update_interval)

            ani = animate_bridge_unsteady_topo(dom, res, x, z_ini, hu, z_roof_null, len_bridge, motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'bridge_L60{scenario}.mp4',
                        writer='ffmpeg', fps=5,
                        progress_callback=update_func)

            anims.append(ani)

    if 9 in problems or 91 in problems or 92 in problems or 93 in problems or 94 in problems:
        # Culvert

        CN = 0.4

        if 9 in problems:
            scenarios = ['unsteady_downstream_bc_culvert',
                         'hydrograph_culvert',
                         'hydrograph_2steps_culvert',
                        #  'Gauss',
                         ]

        elif 91 in problems:
            scenarios = ['unsteady_downstream_bc_culvert']
        elif 92 in problems:
            scenarios = ['hydrograph_culvert']
        elif 93 in problems:
            scenarios = ['hydrograph_2steps_culvert']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            z_roof_null = 10.
            min_overflow = 0.25

            h_under_bridge = 1.5
            h_deck_bridge = 4.0
            len_bridge = 100
            h0 = 0.8
            q0 = 1.

            slice_bridge = slice(int(len(dom)//2-len_bridge//2),int(len(dom)//2+len_bridge//2))
            slice_bridge_up = slice(int(len(dom)//2+(len_bridge//2-1)),int(len(dom)//2-(len_bridge//2+1)),-1)

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck = np.ones_like(z) * z_roof_null

            for idx in range(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2):
                z_bridge[idx] = z[idx] + h_under_bridge
                z_deck[idx] = z_bridge[idx] + h_deck_bridge

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z, z_bridge,
                                               z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration=motion_duration,
                                               scenario_bc=scenario,
                                               min_overflow=min_overflow,
                                               updating_time_interval=update_interval)

            ani = animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y,  res, x, z_ini, hu, z_roof_null, len_bridge, title='Culvert', motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'culvert_{scenario}.mp4',
                            writer='ffmpeg', fps=5,
                            progress_callback=update_func)

            anims.append(ani)

    if 7 in problems or 71 in problems or 72 in problems or 73 in problems or 74 in problems:
        # V-shape Bridge

        CN = 0.4

        if 7 in problems:
            scenarios = ['unsteady_downstream_bc',
                         'hydrograph',
                         'hydrograph_2steps',
                        #  'Gauss',
                         ]
        elif 71 in problems:
            scenarios = ['unsteady_downstream_bc']
        elif 72 in problems:
            scenarios = ['hydrograph']
        elif 73 in problems:
            scenarios = ['hydrograph_2steps']
        elif 74 in problems:
            scenarios = ['Gauss']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            z_roof_null = 10.
            min_overflow = 0.25

            h_under_bridge = 3.5
            h_deck_bridge = 0.75
            len_bridge = 20

            h0 = 1.5

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck   = np.ones_like(z) * z_roof_null

            slice_bridge = slice(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2)
            slice_bridge_up = slice(len(dom)//2+(len_bridge//2-1),len(dom)//2-(len_bridge//2+1),-1)

            for idx in range(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2):
                decal = abs(idx - (len(dom)//2))
                z_bridge[idx] = z[idx] + h_under_bridge + 0.05 * decal
                z_deck[idx] = h_under_bridge + h_deck_bridge

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z,
                                               z_bridge, z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration=motion_duration,
                                               scenario_bc=scenario,
                                               min_overflow= min_overflow,
                                               updating_time_interval=update_interval)

            ani = animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y,  res, x, z_ini, hu, z_roof_null, len_bridge, motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'bridge_Vshape{scenario}.mp4',
                        writer='ffmpeg', fps=5,
                        progress_callback=update_func)

            anims.append(ani)

    if 8 in problems or 81 in problems or 82 in problems or 83 in problems or 84 in problems:
        # U-shape Bridge

        CN = 0.4

        if 8 in problems:
            scenarios = ['unsteady_downstream_bc',
                         'hydrograph',
                         'hydrograph_2steps',
                        #  'Gauss',
                         ]
        elif 81 in problems:
            scenarios = ['unsteady_downstream_bc']
        elif 82 in problems:
            scenarios = ['hydrograph']
        elif 83 in problems:
            scenarios = ['hydrograph_2steps']
        elif 84 in problems:
            scenarios = ['Gauss']

        for scenario in scenarios:

            # UNSTEADY WITH TOPOGRAPHY ADAPTATION
            z_roof_null = 10.
            min_overflow = 0.25

            h_under_bridge = 3.5
            h_deck_bridge = 0.4
            len_bridge = 20

            h0 = 1.5

            z_bridge = np.ones_like(z) * z_roof_null
            z_deck   = np.ones_like(z) * z_roof_null

            slice_bridge = slice(len(dom)//2-len_bridge//2,len(dom)//2+len_bridge//2)
            slice_bridge_up = slice(len(dom)//2+(len_bridge//2-1),len(dom)//2-(len_bridge//2+1),-1)

            z_bridge[slice_bridge] = z[slice_bridge] + h_under_bridge
            z_deck[slice_bridge]   = z_bridge[slice_bridge] + h_deck_bridge

            idx_up = len(dom)//2-len_bridge//2
            idx_down = len(dom)//2+len_bridge//2-1

            z_bridge[idx_up] -= .4
            z_bridge[idx_up+1] -= .4

            z_bridge[idx_down] -= .4
            z_bridge[idx_down-1] -= .4

            poly_bridge_x = np.concatenate((x[slice_bridge], x[slice_bridge_up]))
            poly_bridge_y = np.concatenate((z_bridge[slice_bridge], z_deck[slice_bridge_up]))

            z_ini = z.copy()

            res = problem_bridge_unsteady_topo(dom, z,
                                               z_bridge, z_deck, z_roof_null,
                                               h0, q0, dx, CN, n,
                                               motion_duration=motion_duration,
                                               scenario_bc=scenario,
                                               min_overflow= min_overflow,
                                               updating_time_interval=update_interval)

            ani = animate_bridge_unsteady_topo(dom, poly_bridge_x, poly_bridge_y,  res, x, z_ini, hu, z_roof_null, len_bridge, motion_duration=motion_duration)

            if save_video:
                update_func = lambda _i, _n: progress_bar.update(1)
                with tqdm(total=len(res), desc='Saving video') as progress_bar:
                    ani.save(f'bridge_Ushape{scenario}.mp4',
                        writer='ffmpeg', fps=5,
                        progress_callback=update_func)

            anims.append(ani)

    return anims


def hedge():
    """ Compute Water line problems with hedge

    Length = 500 m
    dx = 1 m
    CN = 0.4
    h0 = 4 m
    q0 = 7 m^2/s
    n  = 0.025
    slope = 1e-4
    """

    length = 500.
    dx = 1.
    CN = 0.4
    h0 = 4.
    q0 = 7.
    n  = 0.025
    slope = 1e-4

    dom, x, z = domain(length, dx, slope)
    x = np.array(x)

    hu = uniform_waterdepth(slope, q0, n)

    # bridge roof level is 10 m everywhere except in the middle of the domain
    # where the bridge is located.
    # The bridge is a flat bridge with a height of 2 m.
    z_bridge = np.ones_like(z) * 10.
    z_bridge[len(dom)//2-5:len(dom)//2+5] = z[len(dom)//2-5:len(dom)//2+5] + 2.

    fig, axes = plt.subplots(3,1)

    h1, q1 = problem(dom, z, h0, q0, dx, CN, n)
    h2, q2, theta = problem_hedge(dom, z, h0, q0, dx, CN, n)

    plot_hedge(axes[0], x, h1, h2, q1, q2, z, hu, theta)

    h1, q1 = problem(dom, z, h0+1., q0, dx, CN, n)
    h2, q2, theta = problem_hedge(dom, z, h0+1., q0, dx, CN, n)

    plot_hedge(axes[1], x, h1, h2, q1, q2, z, hu, theta)

    h1, q1 = problem(dom, z, h0+2., q0, dx, CN, n)
    h2, q2, theta = problem_hedge(dom, z, h0+2., q0, dx, CN, n)

    plot_hedge(axes[2], x, h1, h2, q1, q2, z, hu, theta)

    fig.set_size_inches(20, 10)
    fig.tight_layout()

    return fig, axes

if __name__  == '__main__':

    # anim = lake_at_rest()
    anim = water_line()
    # anim = water_lines()
    # anim = unsteady_without_bedmotion()
    # anim = unteaady_with_bedmotion([2, 6, 7, 8, 9])
    # anim = hedge()
    # anim = water_line_noloss_noslope()

    # anim1 = unsteady_with_bedmotion([2])
    # anim2 = unsteady_with_bedmotion_interval([21], update_interval=2., motion_duration=300.)

    plt.show()

    pass