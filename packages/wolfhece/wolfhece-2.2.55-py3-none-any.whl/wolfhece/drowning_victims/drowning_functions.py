import numpy as np
from numpy import random as rnd
import math
from scipy.stats import beta
from scipy.optimize import fsolve
import random
from pathlib import Path
import json
import wx
import queue
import os
import logging

try:
    from wolfgpu.results_store import ResultsStore
except ImportError:
    print("wolfgpu not available")

EPS = 0.15
G = [0, 0, -9.81]
P_ATM = 101325  # Pa
RHO_F = 1000

def beta_find(x, *data):
    """
    Iterative function that finds the parameters alpha and beta defining a beta distribution and scales it in a range.
    The function fits the parameters based on two given percentiles of the data.

    :param x: Array containing initial guesses for alpha and beta.
    :param data: Tuple containing (down, up, mini, maxi, perc1, perc2).
    :return: Array containing the differences between the calculated and given percentiles.
    """

    ##Conversion of data into understandable parameters
    down = data[0]
    up = data[1]
    mini = data[2]
    maxi = data[3]
    perc1 = data[4]
    perc2 = data[5]
    data = (down, up, mini, maxi, perc1, perc2)

    ## Initialisation of the iterative array with alpha and beta values into F[0] and F[1]
    F = np.zeros((2))

    ## Calculation of the beta distribution with the given parameters
    F[0] = beta.cdf((down - mini) / (maxi - mini), x[0], x[1]) - perc1
    F[1] = beta.cdf((up - mini) / (maxi - mini), x[0], x[1]) - perc2

    return F

def Body_motion(a_RK, batch_turb, CFL, Delta, epsilon, H_pre, H_post, Human, k, NbX, NbY, Pos_bp, resurface, sinking, time_b, t_Wolf_pre, t_Wolf_post, time_goal, U_bp, Ux_pre, Ux_post, Uy_pre, Uy_post, Z_param):
    """
    Function calculating the motion of the body at each time step using a Runge-Kutta method.
    From body position, velocity and flow environment, the function determines the flow velocity at the body position and calculates its new velocities, checking for collisions with walls.

    :param a_RK: Runge-Kutta coefficient.
    :param batch_turb: Batch turbulence.
    :param CFL: Courant-Friedrichs-Lewy number.
    :param Delta: Array of delta values.
    :param epsilon: Epsilon value.
    :param H_pre: Pre-update water depth.
    :param H_post: Post-update water depth.
    :param Human: Human parameters array.
    :param k: Turbulence kinetic energy.
    :param NbX: Number of cells in X direction.
    :param NbY: Number of cells in Y direction.
    :param Pos_bp: Body position array for calculations.
    :param resurface: Resurface array.
    :param sinking: Sinking array.
    :param time_b: Time array for savings.
    :param t_Wolf_pre: Pre-update Wolf time.
    :param t_Wolf_post: Post-update Wolf time.
    :param time_goal: Time goal.
    :param U_bp: Body velocity array for calculations.
    :param Ux_pre: Pre-update X velocity.
    :param Ux_post: Post-update X velocity.
    :param Uy_pre: Pre-update Y velocity.
    :param Uy_post: Post-update Y velocity.
    :param Z_param: Z parameters array.
    :return: Updated Human, Pos_b, resurface, sinking, time_b, U_b arrays.
    """

    ##Global parameters and conersion of some parameters to give them an explicit name

    vertical = Z_param[0,3]
    turb_type = 1
    z_0 = Z_param[0,2]
    T_w = Z_param[:,5]

    dt_Wolf = t_Wolf_post - t_Wolf_pre
    t_Wolf_perc = (time_b - t_Wolf_pre)/dt_Wolf
    t_Wolf_perc_insta = t_Wolf_perc + Delta[3]/dt_Wolf

    ## Body parameters

    m_b = Human[:,16] + Human[:,7]

    BSA_Ken = 2.4631 #[m²]

    CAM = Human[:,3]
    CDA = Human[:,4] * Human[:,2]/BSA_Ken
    CLA = Human[:,5] * Human[:,2]/BSA_Ken
    CSA = np.random.choice([-1, 1], size=len(Human[:,23]))*Human[:,23] * Human[:,2]/BSA_Ken

    mu_stat = Z_param[:,3]

    ## Initisalisation of the Runge-Kutta variables as variables at the time t for both columns

    Pos_RK = np.array([Pos_bp.copy(),Pos_bp.copy()])
    U_RK = np.array([U_bp.copy(),U_bp.copy()])
    acc_RK = np.zeros((2,U_bp.shape[0],U_bp.shape[1]))

    for i in range(2): #RK loop

        j = abs(i-1)

        index_bp = ((np.floor(Pos_RK[j,:,:].T / Delta[0:3,None])).T).astype(int) #Body position converted into index in the input matrix of U and H

        ## Get the velocity at exact time and horizontal position of each run, most time consuming function of the drowning calculation
        [du_insta,_,_,H_f,k_f,U_x_vec,U_y_vec,walls] = interp_mailles_mat(Delta,epsilon,H_pre,H_post,index_bp,k,NbX,NbY,Pos_RK[j,:,:],t_Wolf_perc,t_Wolf_perc_insta,Ux_pre,Ux_post,Uy_pre,Uy_post)

        ## Parameters and calculations to have the velocity at the body vertical position and its relative velocity
        l_tilde = EPS/H_f
        z = np.clip(Pos_RK[j, :, -1],EPS, H_f)
        z_tilde = np.maximum(z/H_f,l_tilde)
        mu = np.minimum(mu_stat * ((1-z_tilde)/z_tilde * l_tilde/(1-l_tilde))**3,mu_stat)

        U_max = np.sqrt(U_x_vec**2 + U_y_vec**2)
        dt = np.clip(np.divide(CFL * Delta[4],np.where(U_max!=0,U_max,Delta[3])), 0.00001, Delta[3]) #to be used if turb_type == 2 or 3 in Flow_time_t
        U_x_dif,U_x_sign,U_y_dif,U_y_sign = Flow_time_t(batch_turb,dt,EPS,H_f,k_f,turb_type,U_RK[j,:,:],U_x_vec,U_y_vec,z,z_0)
        norm_U = np.sqrt((U_x_dif**2 + U_y_dif**2))

        dt = np.clip(np.divide(CFL * Delta[4],np.where(norm_U!=0, norm_U, Delta[3])), 0.0001, Delta[3]).T

        V_b = Body_volume_variation(Z_param[:,7],Human[:,2],Human[:,14],H_f,Human[:,16],time_b,T_w,1.5*Human[:,15],Human[:,18],Human[:,20],Human[:,21],z)

        acc_RK[i,:,:],U_RK[i,:,:] = Motion_equations(CAM,CDA,CLA,CSA,dt,du_insta,m_b,mu,U_RK[j,:,:],U_x_dif,U_x_sign,U_y_dif,U_y_sign,V_b,vertical)
        Pos_RK[i,:,:] += U_RK[i,:,:]*dt[:,None]

        mask_bottom = ((U_RK[i, :, 2] < 0) & (Pos_RK[i, :, 2] < EPS)) #Mask to consider if the body goes down while it is on the bottom
        Pos_RK[i, :, 2][mask_bottom] = EPS #Prevents the body from going under the bottom
        U_RK[i, :, 2][mask_bottom] = 0

        mask_up = ((U_RK[i, :, 2] > 0) & (Pos_RK[i, :, 2] > H_f)) #Mask to consider if the body goes down while it is on the bottom
        Pos_RK[i, :, 2][mask_up] = H_f[mask_up] #Prevents the body from going under the bottom
        U_RK[i, :, 2][mask_up] = 0

        t_Wolf_perc += dt/dt_Wolf


    U_b = (1-a_RK)*U_RK[0,:,:] + a_RK*U_RK[1,:,:]
    Pos_b = (1-a_RK)*Pos_RK[0,:,:] + a_RK*Pos_RK[1,:,:]

    time_b += dt

    ## Check and corrections for collisions with walls
    index_b = ((np.floor(Pos_b[:,:2].T / Delta[0:2,None])).T).astype(int)
    walls = (H_pre[index_b[:,1], index_b[:,0]] < EPS)
    ind_walls = np.where(walls)[0]
    if ind_walls.size!=0:
        [Pos_b[ind_walls,0:2],U_b[ind_walls,0:2]] = Collision(Delta,Pos_b[ind_walls,0:2],Pos_bp[ind_walls,0:2],U_b[ind_walls,0:2],walls)
        index_b = ((np.floor(Pos_b[:,:2].T / Delta[0:2,None])).T).astype(int)
        walls = (H_pre[index_b[:,1], index_b[:,0]] < EPS)
        ind_walls = np.where(walls)[0]
        U_b[ind_walls,0:2] = 0


    ## Storage of times when bodies sank and resurfaced
    sinking[:,0] = sinking[:,0] + (sinking[:,0]==0)*(Pos_b[:,2] == EPS)*(U_b[:,2]==0) * Pos_b[:,0]
    sinking[:,1] = sinking[:,1] + (sinking[:,1]==0)*(Pos_b[:,2] == EPS)*(U_b[:,2]==0) * time_b

    H_f = H_f.ravel()
    V_b = V_b.ravel()
    resurface[:,0] = resurface[:,0] + (resurface[:,0]==0)*(Pos_b[:,2] >= H_f-0.5)*(m_b/V_b/RHO_F<1) * Pos_b[:,0]
    resurface[:,1] = resurface[:,1] + (resurface[:,1]==0)*(Pos_b[:,2] >= H_f-0.5)*(m_b/V_b/RHO_F<1) * time_b

    return Human,Pos_b,resurface,sinking,time_b,U_b

def Body_temperature(BSA, mass, T_w, t):
    """
    Gives the body temperature at time t considering ONLY the conduction.

    :param BSA: Body surface area [m²].
    :param mass: Body mass [kg].
    :param T_w: Water temperature [°C].
    :param t: Time from the beginning.
    :return: ADD (Accumulated Degree Days) and body temperature.
    """
    T_body_ini = 37

    # c_b = 3500  # J/kg/K
    # t_skin = 4.6e-3  # Average thickness of the skin in meters
    # k_skin = 0.21  # Thermal conductivity of the skin W/m K

    # R_cond = t_skin / (k_skin * BSA)

    # Res = R_cond * mass * c_b

    Res = 3000

    T_b = T_w + (T_body_ini - T_w)*np.exp(-t/Res)

    ADD = ((T_body_ini - T_w) * Res * (1 - np.exp(-t / Res)) + T_w * t)/3600/24 #Integral of the body temperature as a function of time, ADD in [°C.day]

    return ADD,T_b

def Body_volume_variation(alpha_1, BSA, FRC, H_f, m_b, time_b, T_w, TLC, V_b0, V_clothes1, V_clothes2, z):
    """
    Function calculating the body volume variation due to the putrefaction gases.
    The method is described in Delhez et al. 2025, "Predicting the buoyancy and Postmortem Submersion Interval of victims of river drowning".

    :param alpha_1: Alpha parameter.
    :param BSA: Body surface area.
    :param FRC: Functional residual capacity.
    :param H_f: Water depth.
    :param m_b: Body mass.
    :param time_b: Time array for savings.
    :param T_w: Water temperature.
    :param TLC: Total lung capacity.
    :param V_b0: Initial body volume.
    :param V_clothes1: Clothes volume for temperature < 15°C.
    :param V_clothes2: Clothes volume for temperature >= 15°C.
    :param z: Depth array.
    :return: Body volume.
    """

    p_hydro = np.maximum(H_f - z,0.00001)*(-G[2])*1000
    p_ext = P_ATM+p_hydro
    V_s = V_b0 - FRC #fraction of FRC on the whole body volume
    n_0 = P_ATM*FRC/(8.3144621*(37+273.15)) #initial amount of gas in the lungs, perfect gas law

    ADD = time_b/60/60/24 * T_w
    _,T_b = Body_temperature(BSA,m_b,T_w,time_b) #Consideration of the actual body temperature
    ratio_ADD = ADD/alpha_1

    n_1 = 2*P_ATM * TLC/(8.3144621*(T_w+273.15))
    coef_eta = [10,-15,6]
    eta = n_1*(coef_eta[2]*(ratio_ADD)**5+coef_eta[1]*(ratio_ADD)**4+coef_eta[0]*(ratio_ADD)**3)
    eta = np.minimum(eta,n_1)

    V_clothes = np.where(T_w < 15, V_clothes1, V_clothes2)

    V_comp = (n_0+eta/n_1*(n_1-n_0))*8.3144621*(T_b+273.15)/(p_ext) #Compressible Volume
    V_b = V_s + V_comp + V_clothes

    return V_b

def Collision(Delta, Pos, Pos_p, U, walls):
    """
    Correct the bodies that hit a wall by correcting its velocity and replace it on the wall (+marge).

    :param Delta: Array of delta values.
    :param Pos: Body position array for calculations.
    :param Pos_p: Previous body position array.
    :param U: Body velocity array for calculations.
    :param walls: Walls array.
    :return: Corrected position and velocity arrays.
    """
    marge = Delta[0:2]/100 * (25)
    elasticite = 0.1

    Correction_pos_val = Pos%Delta[0:2]-Delta[0:2]/2 #Detection of body position in the cell
    Correction_pos_sign = ((Pos%Delta[0:2]>Delta[0:2]/2) != (Pos_p%Delta[0:2]>Delta[0:2]/2)) #1 for right or below, 0 for left and above
    # which_direction = (U>0 and walls[1:3]==0) #if 1, collision with wall right and/or above; if 0, collision with a wall left and/or below

    adjust_sign = (1-2*(Correction_pos_sign))

    #Correction of body position and velocity
    U = (U * adjust_sign)*(elasticite)*Correction_pos_sign + U * (Correction_pos_sign==0)
    Pos += (np.sign(Correction_pos_val)*(Correction_pos_sign==1)*((Delta[0:2]/2-np.abs(Correction_pos_val))+marge))

    return Pos,U

def Flow_time_t(batch_turb, dt, epsilon, H_f, k, turb_type, U_bp, U_x_vec, U_y_vec, z, z_0):
    """
    Calculates the difference between the body velocity and the flow velocity (-> relative body velocity) and its sign before and after evaluating the turbulences.

    :param batch_turb: Batch turbulence.
    :param dt: Time step.
    :param epsilon: Epsilon value.
    :param H_f: Water depth.
    :param k: Turbulence kinetic energy.
    :param turb_type: Turbulence type.
    :param U_bp: Body velocity array for calculations.
    :param U_x_vec: X velocity vector.
    :param U_y_vec: Y velocity vector.
    :param z: Depth array.
    :param z_0: Roughness length.
    :return: U_x_dif, U_x_sign, U_y_dif, U_y_sign arrays.
    """
    U_x_dif = (U_x_vec-U_bp[:,0])
    U_y_dif = (U_y_vec-U_bp[:,1])
    U_x_vec,U_y_vec = U_turbulence(batch_turb,dt,epsilon,H_f,k,turb_type,U_x_vec,U_x_dif,U_y_vec,U_y_dif,z,z_0)
    U_x_dif = (U_x_vec-U_bp[:,0])
    U_y_dif = (U_y_vec-U_bp[:,1])
    U_x_sign = np.sign(U_x_dif)
    U_y_sign = np.sign(U_y_dif)

    return U_x_dif,U_x_sign,U_y_dif,U_y_sign

def interp_mailles_mat(Delta, epsilon, H_0, H_1, index_b, k, NbX, NbY, Pos_b, t_WOLF_perc, t_Wolf_perc_insta, Ux_0, Ux_1, Uy_0, Uy_1):
    """
    Determines the flow velocity and height at the body position based on the value of the cells in which the body is and the next cells in x, y and xy.
    It is a spatial bi-linear and temporal linear interpolation.
    Method described in Delhez et al. 2025, Lagrangian modelling of the drift of a victim of river drowning.

    :param Delta: Array of delta values.
    :param epsilon: Epsilon value.
    :param H_0: Pre-update water depth.
    :param H_1: Post-update water depth.
    :param index_b: Body position indices.
    :param k: Turbulence kinetic energy.
    :param NbX: Number of cells in X direction.
    :param NbY: Number of cells in Y direction.
    :param Pos_b: Body position array for savings.
    :param t_WOLF_perc: Percentage of Wolf time.
    :param t_Wolf_perc_insta: Instantaneous percentage of Wolf time.
    :param Ux_0: Pre-update X velocity.
    :param Ux_1: Post-update X velocity.
    :param Uy_0: Pre-update Y velocity.
    :param Uy_1: Post-update Y velocity.
    :return: du_insta, epsilon_v, ind_walls, H_v, k_v, Ux_v, Uy_v, walls arrays.
    """

    # Calculate the position within the cell
    x_rel = (Pos_b[:, 0] % Delta[0]) - Delta[0] / 2
    y_rel = (Pos_b[:, 1] % Delta[1]) - Delta[1] / 2

    # Determine next cell indices
    index_bo_x = np.array(index_b[:, 0] + np.sign(x_rel),dtype=int)
    index_bo_y = np.array(index_b[:, 1] + np.sign(y_rel),dtype=int)

    # Normalize x and y to the range [0, 0.5]
    x = np.abs(x_rel) / Delta[0]
    y = np.abs(y_rel) / Delta[1]

    # Check for non-zero Ux values
    walls = np.column_stack((Ux_0[index_b[:,1], index_b[:,0]] != 0.0,Ux_0[index_b[:,1], index_bo_x] != 0.0,Ux_0[index_bo_y, index_b[:,0]] != 0.0,Ux_0[index_bo_y, index_bo_x] != 0.0))
    ind_walls = np.where(~np.all(walls, axis=1))[0]

    fact_cell = (1 - x) * (1 - y)
    fact_next_x = x * (1 - y)
    fact_next_y = (1 - x) * y
    fact_next_xy = x * y

    # Interpolate values (spatially)
    def interp(var):
        return (var[index_b[:,1],index_b[:,0]] * fact_cell +
                          var[index_b[:,1],index_bo_x] * fact_next_x +
                          var[index_bo_y,index_b[:,0]] * fact_next_y +
                          var[index_bo_y,index_bo_x] * fact_next_xy)

    interp_Ux_0 = interp(Ux_0)
    interp_Ux_1 = interp(Ux_1)
    interp_Uy_0 = interp(Uy_0)
    interp_Uy_1 = interp(Uy_1)

    # Temporal interpolation
    Ux_v = interp_Ux_0*(1-t_WOLF_perc) + interp_Ux_1*t_WOLF_perc
    Uy_v = interp_Uy_0*(1-t_WOLF_perc) + interp_Uy_1*t_WOLF_perc
    H_v = interp(H_0)*(1-t_WOLF_perc) + interp(H_1)*t_WOLF_perc
    k_v = 0 #interp(k)
    epsilon_v = 0 #interp(epsilon)

    first_part = np.array(Ux_v - (interp_Ux_0*(1 - t_Wolf_perc_insta) + interp_Ux_1*t_Wolf_perc_insta))
    second_part = np.array(Uy_v - (interp_Uy_0*(1 - t_Wolf_perc_insta) + interp_Uy_1*t_Wolf_perc_insta))
    du_insta = np.column_stack((first_part, second_part))

    # Variant if a body is next to a wall
    if ind_walls.size != 0:
        active_cells = np.maximum(np.sum(walls, axis=1), 1)

        def sum_vars(var):
            return (var[index_b[ind_walls,1],index_b[ind_walls,0]] +
                                var[index_b[ind_walls,1],index_bo_x[ind_walls]] +
                                var[index_bo_y[ind_walls],index_b[ind_walls,0]] +
                                var[index_bo_y[ind_walls],index_bo_x[ind_walls]])

        # sum_vars = lambda var: (var[index_b[ind_walls,1],index_b[ind_walls,0]] +
        #                         var[index_b[ind_walls,1],index_bo_x[ind_walls]] +
        #                         var[index_bo_y[ind_walls],index_b[ind_walls,0]] +
        #                         var[index_bo_y[ind_walls],index_bo_x[ind_walls]))

        Ux_v[ind_walls] = sum_vars(Ux_0) / active_cells[ind_walls]
        Uy_v[ind_walls] = sum_vars(Uy_0) / active_cells[ind_walls]
        H_v[ind_walls] = sum_vars(H_0) / active_cells[ind_walls]
        # k_v[ind_walls] = sum_vars(k) / active_cells[ind_walls]
        # epsilon_v[ind_walls] = sum_vars(epsilon) / active_cells[ind_walls]

        # limit_layer = lambda var: (var[index_cell[ind_walls]]*(0.5-x[ind_walls])*(walls[ind_walls,1]==0) +
        #                         var[index_cell[ind_walls]]*(0.5-y[ind_walls])*(walls[ind_walls,2]==0))

        # Ux_v[ind_walls] = limit_layer(Ux)
        # Uy_v[ind_walls] = limit_layer(Uy)
        # H_v[ind_walls] = limit_layer(H)
        # H_v[ind_walls] = (H_v[ind_walls]!=0)*H_v[ind_walls] + (H_v[ind_walls]==0)*1
        # k_v[ind_walls] = limit_layer(k)
        # epsilon_v[ind_walls] = limit_layer(epsilon)

        H_v = np.maximum(H_v,EPS*2)

        ind_walls = np.where(walls[:, 0] == 0)[0]

    return du_insta,epsilon_v,ind_walls, H_v, k_v, Ux_v, Uy_v,walls[ind_walls,:]

def known_1(g, mini, maxi, down, up, perc1, perc2):
    """
    Used in the fit of the beta parameters alpha and beta by iteration.

    :param g: Guess array.
    :param mini: Minimum value.
    :param maxi: Maximum value.
    :param down: Lower percentile value.
    :param up: Upper percentile value.
    :param perc1: Lower percentile.
    :param perc2: Upper percentile.
    :return: Tuple containing alpha and beta.
    """
    x0 = np.array([1, 1])
    data = (down, up, mini, maxi, perc1, perc2)
    x = fsolve(beta_find, x0, args=data)
    a = x[0]
    b = x[1]
    return (a, b)

def Loading(Path_loading, Pos_b, time_b, U_b):
    """
    Loads the results of a previous simulation and returns the data needed to start from these results.

    :param Path_loading: Path to the loading file.
    :param Pos_b: Body position array for savings.
    :param time_b: Time array for savings.
    :param U_b: Body velocity array for savings.
    :return: count_initial, Human, n_loaded, Pos_b, time_b, U_b, Z_param arrays.
    """
    n_b_wanted = np.size(Pos_b,0)
    n_wanted = np.size(Pos_b,2)

    Human = data["Human"]
    Pos_b = data["Pos_b"]
    time_b = data["time_b"]
    U_b = data["U_b"]
    Z_param = data["Z_param"]

    n_b_loaded = np.size(Pos_b,0)
    n_loaded = np.size(Pos_b,2)

    count_initial = n_loaded-1

    data = np.load(Path_loading)

    if n_b_wanted != n_b_loaded:
        print(f"Error: Size of the sample loaded is different from the new one, the new one must be made of {n_b_loaded} bodies")
        return

    Pos_b[:][:][n_loaded+1] = np.zeros((n_b_wanted,3,int(n_wanted-n_loaded)))
    time_b[:][:][n_loaded+1] = np.zeros((n_b_wanted,3,int(n_wanted-n_loaded)))
    U_b[:][:][n_loaded+1] = np.zeros((n_b_wanted,3,int(n_wanted-n_loaded)))

    return count_initial,Human,n_loaded,Pos_b,time_b,U_b,Z_param

def Loop_management(progress_queue, process_id, a_RK, BC_cells, count, count_Wolf, CFL, Delta, Human_np, i_initial, n_b, n_saved, n_t, NbX, NbY, Path_Saving, Path_Wolf, Pos, Pos_b, resurface, sinking, time, time_b, time_goal, U, U_b, wanted_time, wanted_Wolf, Z_param_np):
    """
    Main loop of the code. Calculates the motion of each body at each time in the loop and updates the flow when needed.
    Everything is based on the array "still" which contains the index of all the bodies that need more calculations, as we work with variable time step for each body.
    If a body is out of the domain, it is out of still; if a body reaches a time for which we need a save, it is out of still;
    if a body reaches a time for which the flow needs to be updated, it is out of still.

    :param progress_queue: Queue for progress updates.
    :param process_id: Process ID.
    :param a_RK: Runge-Kutta coefficient.
    :param BC_cells: Boundary condition cells.
    :param count: Count of saved states.
    :param count_Wolf: Count of Wolf states.
    :param CFL: Courant-Friedrichs-Lewy number.
    :param Delta: Array of delta values.
    :param Human_np: Human parameters array.
    :param i_initial: Initial index.
    :param n_b: Number of bodies.
    :param n_saved: Number of saved states.
    :param n_t: Number of time steps.
    :param NbX: Number of cells in X direction.
    :param NbY: Number of cells in Y direction.
    :param Path_Saving: Path to save results.
    :param Path_Wolf: Path to Wolf results.
    :param Pos: Body position array for calculations.
    :param Pos_b: Body position array for savings.
    :param resurface: Resurface array.
    :param sinking: Sinking array.
    :param time: Time array for calculations.
    :param time_b: Time array for savings.
    :param time_goal: Time goal.
    :param U: Body velocity array for calculations.
    :param U_b: Body velocity array for savings.
    :param wanted_time: Array of wanted times.
    :param wanted_Wolf: Array of wanted Wolf times.
    :param Z_param_np: Z parameters array.
    :return: Updated Pos_b, resurface, sinking, time_b, U_b arrays.
    """

    # Initialisation of some of the function variables
    batch_turb = rnd.normal(0,1,n_b) # Vector with random values following a normal distribution used to avoid using rnd.normal at each iteration
    still = np.arange(n_b)
    i = i_initial+1
    count_Wolf_ini = count_Wolf

    # Loading of the first flow between t_initial and t_initial + dt_Wolf (often 1h)
    H_pre,Ux_pre,Uy_pre = Read_Wolf_GPU_mat(count_Wolf+1,Path_Wolf)
    H_post,Ux_post,Uy_post = Read_Wolf_GPU_mat(count_Wolf+2,Path_Wolf)

    epsilon = H_pre*0
    k = H_pre*0

    # Main loop of the model
    while count<(n_saved):
        t_for = wanted_time[count]
        t_Wolf = wanted_Wolf[count_Wolf]
        s = 1 - i%2
        sp = 0 + i%2

        # Body position calculation at each time step
        (Human_np[still,:],Pos[still,:,s],resurface[still,:],sinking[still,:],time[still],U[still,:,s]) = Body_motion(a_RK,batch_turb,CFL,Delta,epsilon,H_pre,H_post,Human_np[still,:],k,NbX,NbY,Pos[still,:,sp],resurface[still,:],sinking[still,:],time[still],t_Wolf-wanted_Wolf[count_Wolf_ini],wanted_Wolf[count_Wolf+1]-wanted_Wolf[count_Wolf_ini],t_for,U[still,:,sp],Ux_pre,Ux_post,Uy_pre,Uy_post,Z_param_np[still,:])
        index = np.floor_divide(Pos[:, :2, s], Delta[:2]).astype(int)
        still = np.where((time < t_for) & (time < t_Wolf) & (~np.any(np.all(index[:, None] == BC_cells, axis=2), axis=1)))[0]

        # Save of calculations from the working variables (size(n,n,2) with index s being the time t and sp time t-dt to size(n,n,n_saved)) or need to update the flow
        if still.size==0:
            if np.any(time<t_Wolf-wanted_Wolf[count_Wolf_ini]):#Save data
                Pos_b[:,:,count] = Pos[:,:,s]
                U_b[:,:,count] = U[:,:,s]
                time_b[:,count] = time

                count += 1
                t_for = wanted_time[count]
                still = np.where((time < t_for) & (time < t_Wolf) & (~np.any(np.all(index[:, None] == BC_cells, axis=2), axis=1)))[0]
            elif np.any(time<t_for): # Update flow
                H_pre,Ux_pre,Uy_pre = Read_Wolf_GPU_mat(count_Wolf+1,Path_Wolf)
                H_post,Ux_post,Uy_post = Read_Wolf_GPU_mat(count_Wolf+2,Path_Wolf)
                count_Wolf += 1

                t_Wolf = wanted_Wolf[count_Wolf]
                still = np.where((time < t_for) & (time < t_Wolf) & (~np.any(np.all(index[:, None] == BC_cells, axis=2), axis=1)))[0]
            else: # Save data and update flow
                Pos_b[:,:,count] = Pos[:,:,s]
                U_b[:,:,count] = U[:,:,s]
                time_b[:,count] = time

                count += 1
                t_for = wanted_time[count]
                if t_for > wanted_Wolf[count_Wolf+1]-wanted_Wolf[count_Wolf_ini]:
                    count_Wolf += 1
                    t_Wolf = wanted_Wolf[count_Wolf]
                    H_pre,Ux_pre,Uy_pre = Read_Wolf_GPU_mat(count_Wolf,Path_Wolf)
                    H_post,Ux_post,Uy_post = Read_Wolf_GPU_mat(count_Wolf+1,Path_Wolf)
                still = np.where((time < t_for) & (time < t_Wolf) & (~np.any(np.all(index[:, None] == BC_cells, axis=2), axis=1)))[0]

            if process_id != -1: #To not enter when we do not work in multiprocess
                progress_queue.put((process_id, time[0])) #Sends the id and the time of this process to the main one
            else:
                Path_save = os.path.join(Path_Saving,'Results')
                os.makedirs(Path_save,exist_ok=True)
                Save_wanted_time(Path_save,Pos[:,:,s],U[:,:,s],count-1)

            if still.size==0: #End of the loop
                Pos_b[:, :, count:] = np.repeat(Pos[:, :, 0:1], repeats=n_saved-count, axis=2)
                # time_b[:, count:] = np.repeat(time[:], repeats=n_saved-count, axis=2)
                print(f"[Process {process_id}] End of simulation")
                count = n_saved + 1
                break

        # pbar.update(int(time[0] - pbar.n))
        i += 1

    return Pos_b,resurface,sinking,time_b,U_b

def Motion_equations(CAM, CDA, CLA, CSA, dt, du_insta, m_b, mu, U_bp, U_x_dif, U_x_sign, U_y_dif, U_y_sign, V_b, vertical):
    """
    Calculates the body acceleration and velocity based on the motion equation with the Flow to the body forces (Drag, Side and Lift), Gravity and Buoyancy, Friction with the bottom and added mass effect.
    Equations described in Delhez et al., 2025 "Lagrangian modelling of the drift of a victim of river drowning"

    :param CAM: Added mass coefficient.
    :param CDA: Drag coefficient.
    :param CLA: Lift coefficient.
    :param CSA: Side force coefficient.
    :param dt: Time step.
    :param du_insta: Instantaneous velocity difference.
    :param m_b: Body mass.
    :param mu: Friction coefficient.
    :param U_bp: Body velocity array for calculations.
    :param U_x_dif: X velocity difference.
    :param U_x_sign: X velocity sign.
    :param U_y_dif: Y velocity difference.
    :param U_y_sign: Y velocity sign.
    :param V_b: Body volume.
    :param vertical: Vertical position.
    :return: Body acceleration and velocity arrays.
    """

    n_b = len(m_b)
    half_rho_f = 0.5 * RHO_F
    zeros_n_b_3 = np.zeros((n_b, 3))

    m_added = (CAM * RHO_F * V_b).T
    # m_added = ((1+CAM) * RHO_F * V_b).T

    # Initialisation of the forces arrays
    F_fb = zeros_n_b_3.copy()
    F_g = zeros_n_b_3.copy()
    F_fr = zeros_n_b_3.copy()
    F_A = zeros_n_b_3.copy()

    #Rotation matrix to apply to the hydrodynamic coefficients, see article Delhez et al., 2025 for the detail computation of the resultant matrix
    angle_rel = np.arctan2(U_y_dif, U_x_dif)
    angle_rel[(U_y_dif == 0) & (U_x_dif == 0)] = 0

    cos_angle_rel_2 = np.cos(2*angle_rel)
    sin_angle_rel_2 = np.sin(2*angle_rel)

    #Application of the rotation matrix to the hydrodynamic coefficients. To be way more efficient in time, we calculate the values of the matrix analytically instead of algebrically
    C = np.zeros((n_b,2,2))
    C[:,0,0] = (CDA - sin_angle_rel_2*CSA)#*0+CDA
    C[:,0,1] = (CSA*cos_angle_rel_2)#*0+CSA
    C[:,1,0] = C[:,0,1]
    C[:,1,1] = (CDA + sin_angle_rel_2*CSA)#*0+CDA

    # Fluid forces (hydrodynamic forces: drag, side and lift)
    F_fb[:, 0] = U_x_sign * half_rho_f * C[:,0,0] * U_x_dif**2 + U_y_sign * half_rho_f * C[:,0,1] * U_y_dif**2
    F_fb[:, 1] = U_y_sign * half_rho_f * C[:,1,1] * U_y_dif**2 + U_x_sign * half_rho_f * C[:,1,0] * U_x_dif**2
    F_fb[:, 2] = half_rho_f * CLA * (U_x_dif**2 + U_y_dif**2) * vertical

    F_D_z = -np.sign(U_bp[:,2])*half_rho_f*(CDA*2)*U_bp[:,2]**2 * vertical #Consider the vertical drag to be consistent (if we consider the lift, we have to consider the drag)
    F_fb[:,2] += F_D_z

    # Gravitational forces
    F_g[:, 2] = (m_b - RHO_F * V_b) * G[2] * vertical

    #Instationnary flow added mass force
    F_A[:,:2] = m_added[:,None] * du_insta

    Forces_but_friction = F_fb + F_g + F_A #Used to reproduce the threshold of the friction force (as it can't create motion)
    abs_Forces_but_friction = np.hypot(Forces_but_friction[:, 0], Forces_but_friction[:, 1])
    sign_U_bp = np.sign(U_bp[:,:2])

    # Friction forces, calculation of value and direction
    F_fr_tot = mu * np.abs(Forces_but_friction[:,2]) * (Forces_but_friction[:,2]<0) #mu depends on the depth (activating the friction only at the bottom)
    angle = np.arctan2(U_bp[:,1], U_bp[:,0])
    angle[(U_bp[:, 1] == 0) & (U_bp[:, 0] == 0)] = np.arctan2(Forces_but_friction[(U_bp[:, 1] == 0) & (U_bp[:, 0] == 0), 1], Forces_but_friction[(U_bp[:, 1] == 0) & (U_bp[:, 0] == 0), 0])  #Force the angle to be 0 also when both speed are -0.0 which gives -pi by convention
    cos_angle = np.abs(np.cos(angle))# + 1*(angle*180/pi==90)
    sin_angle = np.abs(np.sin(angle))# + 1*(angle*180/pi==0)
    pourcentage = np.divide(F_fr_tot, np.where(abs_Forces_but_friction != 0, abs_Forces_but_friction, 1))
    cos_angle = cos_angle*(pourcentage<=1) + (pourcentage>1)
    sin_angle = sin_angle*(pourcentage<=1) + (pourcentage>1)
    F_fr[:, 0] = np.abs(Forces_but_friction[:,0])*pourcentage*cos_angle * -(sign_U_bp[:, 0] + (sign_U_bp[:, 0] == 0) * np.sign(Forces_but_friction[:, 0]))
    F_fr[:, 1] = np.abs(Forces_but_friction[:,1])*pourcentage*sin_angle * -(sign_U_bp[:, 1] + (sign_U_bp[:, 1] == 0) * np.sign(Forces_but_friction[:, 1]))

    # Newton second law and motion equation
    acc_b = (Forces_but_friction + F_fr) / (m_b + m_added)[:,None]

    U_b = U_bp + acc_b*dt[:,None]
    corr_friction = (np.abs(F_fr[:, :2]) < np.abs(Forces_but_friction[:, :2]))
    U_b[:,:2] *= corr_friction

    return acc_b,U_b

def Parallel_loop(args):
    """
    Used to run the code in Multiprocess.

    :param args: Arguments for the Loop_management function.
    :return: Result of the Loop_management function.
    """
    result = Loop_management(*args)
    return result

def Preparation_parallelisation(progress_queue, a_RK, BC_cells, count, count_Wolf, CFL, Delta, Human_np, i_initial, n_b, n_saved, n_parallel, n_t, NbX, NbY, Path_saving, Path_Wolf, Pos, Pos_b, resurface, sinking, time, time_b, time_goal, U, U_b, wanted_time, wanted_Wolf, Z_param_np):
    """
    Splits the arrays in the number we want to be ran in MultiProcess.

    :param progress_queue: Queue for progress updates.
    :param a_RK: Runge-Kutta coefficient.
    :param BC_cells: Boundary condition cells.
    :param count: Count of saved states.
    :param count_Wolf: Count of Wolf states.
    :param CFL: Courant-Friedrichs-Lewy number.
    :param Delta: Array of delta values.
    :param Human_np: Human parameters array.
    :param i_initial: Initial index.
    :param n_b: Number of bodies.
    :param n_saved: Number of saved states.
    :param n_parallel: Number of parallel processes.
    :param n_t: Number of time steps.
    :param NbX: Number of cells in X direction.
    :param NbY: Number of cells in Y direction.
    :param Path_saving: Path to save results.
    :param Path_Wolf: Path to Wolf results.
    :param Pos: Body position array for calculations.
    :param Pos_b: Body position array for savings.
    :param resurface: Resurface array.
    :param sinking: Sinking array.
    :param time: Time array for calculations.
    :param time_b: Time array for savings.
    :param time_goal: Time goal.
    :param U: Body velocity array for calculations.
    :param U_b: Body velocity array for savings.
    :param wanted_time: Array of wanted times.
    :param wanted_Wolf: Array of wanted Wolf times.
    :param Z_param_np: Z parameters array.
    :return: List of tasks for parallel processing.
    """
    chunk_size = n_b // n_parallel  # Taille des sous-ensembles
    TASKS = []

    if n_parallel > 1:
        for i in range(n_parallel):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size if i != n_parallel - 1 else n_b  # Prend tout jusqu'à la fin au dernier

            # Préparation des arguments pour chaque processus avec sous-vecteurs
            task = (progress_queue,i,a_RK,BC_cells, count,count_Wolf, CFL, Delta, Human_np[start_idx:end_idx,:], i_initial, chunk_size, n_saved, n_t, NbX, NbY,
                    Path_saving,Path_Wolf, Pos[start_idx:end_idx,:,:], Pos_b[start_idx:end_idx,:,:], resurface[start_idx:end_idx],
                    sinking[start_idx:end_idx,:], time[start_idx:end_idx], time_b[start_idx:end_idx,:], time_goal,
                    U[start_idx:end_idx,:,:], U_b[start_idx:end_idx,:,:], wanted_time, wanted_Wolf, Z_param_np[start_idx:end_idx,:])
            TASKS.append(task)

    return TASKS

def Read_Wolf_GPU_mat(i_Wolf, Path_Wolf):
    """
    Reads the results of WolfGPU at a particular time and returns the water depth and velocities' matrix.

    :param i_Wolf: Index of the WolfGPU result.
    :param Path_Wolf: Path to the WolfGPU results.
    :return: Water depth and velocities' matrix.
    """
    dir_sim = Path(Path_Wolf)
    dir_sim_gpu = Path(dir_sim)# / 'simul/simulations/sim_Hydrogram'

    store = ResultsStore(dir_sim_gpu / 'Results', mode='r')

    _,_,_, _, h_store,qx_store,qy_store = store.get_result(i_Wolf)

    h_store = np.where(h_store == 0, 10**-7, h_store)

    Ux = np.nan_to_num(qx_store/h_store, nan=0)

    Uy = np.nan_to_num(qy_store/h_store, nan=0)

    return h_store,Ux,Uy

def Read_Wolf_GPU_metadata(Path_Wolf):
    """
    Reads the parameters of the WolfGPU simulation and returns the relevant ones.

    :param Path_Wolf: Path to the WolfGPU results.
    :return: Boundary condition cells, Wolf time step, grid spacing, water depth, number of cells in X and Y directions, and total simulation time.
    """
    dir_sim = Path(Path_Wolf)
    dir_sim_gpu = Path(dir_sim)# / 'simul/simulations/sim_Hydrogram'

    with open(dir_sim_gpu / 'parameters.json','r') as file:
        parameters = json.load(file)

    param = parameters["parameters"]
    DX = param["dx"]
    DY = param["dy"]
    NbX = param["nx"]
    NbY = param["ny"]

    dur = param["duration"]
    t_tot = dur["duration"]

    dur_dt = param["report_period"]
    dt_WOLF = dur_dt["duration"]

    BC = parameters["boundary_conditions"]

    BC_cells = np.array([(bc['i'], bc['j']) for bc in BC])

    store = ResultsStore(dir_sim_gpu / 'Results', mode='r')

    _,_,_, _, h_store,_,_ = store.get_result(1)

    return BC_cells,dt_WOLF,DX,DY,h_store,NbX,NbY,t_tot

def Save_wanted_time(Path, Pos_b, U_b, count):
    """
    Saves the body positions and velocities at a given time.

    :param Path: Path to save the results.
    :param Pos_b: Body position array for savings.
    :param U_b: Body velocity array for savings.
    :param count: Count of saved states.
    """
    Path_Pos = os.path.join(Path,f'Pos_{count:04d}')
    Path_U = os.path.join(Path,f'U_{count:04d}')
    np.savez(Path_Pos,Pos_b=Pos_b)
    np.savez(Path_U,U=U_b)

def Skinfold(n_b, known, Human):
    """
    Determines the body density based on its age and BMI using Siri's equation. An error percentage body fat is also set, according to Meeuwsen et al., 2010.

    :param n_b: Number of bodies.
    :param known: Known parameter.
    :param Human: Human parameters array.
    :return: Updated Human parameters and error percentage body fat.
    """
    std_perc_fat_m = [8.1, 7.6, 7.0, 6.4, 6.2, 6.7, 6.8] #Meeuwsen et al
    std_perc_fat_w = [8, 8.1, 8.4, 8.4, 8.4, 8.3, 8.3, 9.4]
    error_perc_fat = np.zeros((n_b))

    ind_20_m = np.where((Human.Age.to_numpy()<=20) & (Human.gender.to_numpy()==1))
    ind_30_m = np.where((Human.Age.to_numpy()<=30)&(Human.Age.to_numpy()>20) & (Human.gender.to_numpy()==1))
    ind_40_m = np.where((Human.Age.to_numpy()<=40)&(Human.Age.to_numpy()>30) & (Human.gender.to_numpy()==1))
    ind_50_m = np.where((Human.Age.to_numpy()<=50)&(Human.Age.to_numpy()>40) & (Human.gender.to_numpy()==1))
    ind_max_m = np.where((Human.Age.to_numpy()>50) & (Human.gender.to_numpy() ==1))

    ind_20_w = np.where((Human.Age.to_numpy()<=20) & (Human.gender.to_numpy()==2))
    ind_30_w = np.where((Human.Age.to_numpy()<=30)&(Human.Age.to_numpy()>20) & (Human.gender.to_numpy()==2))
    ind_40_w = np.where((Human.Age.to_numpy()<=40)&(Human.Age.to_numpy()>30) & (Human.gender.to_numpy()==2))
    ind_50_w = np.where((Human.Age.to_numpy()<=50)&(Human.Age.to_numpy()>40) & (Human.gender.to_numpy()==2))
    ind_max_w = np.where((Human.Age.to_numpy()>50) & (Human.gender.to_numpy() ==2))

    ind_20 = np.where(Human.Age.to_numpy()<=24)
    ind_30 = np.where((Human.Age.to_numpy()<=34)&(Human.Age.to_numpy()>24))
    ind_40 = np.where((Human.Age.to_numpy()<=44)&(Human.Age.to_numpy()>34))
    ind_50 = np.where((Human.Age.to_numpy()<=54)&(Human.Age.to_numpy()>44))
    ind_60 = np.where((Human.Age.to_numpy()<=64)&(Human.Age.to_numpy()>54))
    ind_70 = np.where((Human.Age.to_numpy()<=74)&(Human.Age.to_numpy()>64))
    ind_max = np.where(Human.Age.to_numpy()>74)

    BMI_25 = [20, 21.3, 22.5, 23.3, 22.9, 23.7, 23.1]
    BMI_50 = [21.7, 23.4, 24.8, 25.7, 25.9, 26.3, 25.3]
    BMI_75 = [24.3, 26.4, 28, 29, 29.1, 29.7, 28]


    change = [ind_20,ind_30,ind_40,ind_50,ind_60,ind_70,ind_max]

    ind_Age = np.minimum(math.floor(np.mean(Human.Age.to_numpy())/10)-1,6)

    if known == 0:

        for i in range(7):
            ind = np.array((change[i]))
            (aBMI,bBMI) = known_1(3,16,40,BMI_25[i],BMI_50[i],0.25,0.5)
            Human.loc[ind[0,:],'BMI'] = rnd.beta(aBMI,bBMI,size=(len(ind[:][0])))*(40-16)+16

        error_perc_fat = (rnd.beta(2,2,size=(n_b))*(2*std_perc_fat_m[ind_Age]+2*std_perc_fat_m[ind_Age])-2*std_perc_fat_m[ind_Age])*(Human.gender.to_numpy()==1) + (rnd.beta(2,2,size=(n_b))*(2*std_perc_fat_w[ind_Age]+2*std_perc_fat_w[ind_Age])-2*std_perc_fat_w[ind_Age])*(Human.gender.to_numpy()==2)

        Human.loc[:,'mass'] = Human.BMI * Human.height**2

        perc_fat = -32.515 + 12.409*(Human.gender.to_numpy()-1) + 3.306*Human.BMI.to_numpy() - 0.03*Human.BMI.to_numpy()**2 - 0.006*Human.Age.to_numpy() + 0.033*Human.Age.to_numpy()*(Human.gender.to_numpy()-1) - 0.001*Human.Age.to_numpy()*Human.BMI.to_numpy() #Meeuwsen et al
        perc_fat = perc_fat*(perc_fat+error_perc_fat<45) + (perc_fat-(perc_fat+error_perc_fat-45-random.randint(-100,200))/100)*(perc_fat+error_perc_fat>=45)
        perc_fat = np.maximum(perc_fat+error_perc_fat,8)
        Human.rho = 4.95/(perc_fat/100+4.5) * 1000#Siri's equation
        Human.Volume = Human.mass/Human.rho

    else: #if known != 3:

        ind_Age = np.minimum(math.floor(np.mean(Human.Age.to_numpy())/10)-1,6)

        error_perc_fat = rnd.beta(2,2,size=(n_b))*(2*std_perc_fat_m[ind_Age]+2*std_perc_fat_m[ind_Age])-(2*std_perc_fat_m[ind_Age])*(Human.gender.to_numpy()==1) + (rnd.beta(2,2,size=(n_b))*(2*std_perc_fat_w[ind_Age]+2*std_perc_fat_w[ind_Age])-2*std_perc_fat_w[ind_Age])*(Human.gender.to_numpy()==2)

        perc_fat = -32.515 + 12.409*(Human.gender.to_numpy()-1) + 3.306*Human.BMI.to_numpy() - 0.03*Human.BMI.to_numpy()**2 - 0.006*Human.Age.to_numpy() + 0.033*Human.Age.to_numpy()*(Human.gender.to_numpy()-1) - 0.001*Human.Age.to_numpy()*Human.BMI.to_numpy() #Meeuwsen et al
        perc_fat = perc_fat*(perc_fat+error_perc_fat<45) + (perc_fat-(perc_fat+error_perc_fat-45-random.randint(-100,200))/100)*(perc_fat+error_perc_fat>=45)
        perc_fat = np.maximum(perc_fat+error_perc_fat,8)
        Human.rho = 4.95/(perc_fat/100+4.5) * 1000;#Siri's equation
        Human.Volume = Human.mass.to_numpy()/Human.rho.to_numpy()

    return Human,error_perc_fat

def state_of_run(progress_queue, frame, interval):
    """
    Monitoring function that displays progress every `interval` seconds.

    :param progress_queue: Queue for progress updates.
    :param frame: Frame object for GUI updates.
    :param interval: Time interval for updates.
    """
    progress_dict = {i: None for i in range(frame.n_processes)}  # Initialize the progress dictionary
    while True:
        # Get the progress updates from the queue
        try:
            progress_update = progress_queue.get(timeout=interval)  # Timeout after interval second if no updates
            process_id, progress = progress_update
            progress_dict[process_id] = progress
            wx.CallAfter(frame.update_progress,progress_dict)  # Update GUI safely from a thread
        except queue.Empty:
            continue  # Pas de mise à jour dispo, on continue
        except (EOFError, BrokenPipeError):
            break

        # Close window when all processes are done
        # if all(value is not None for value in progress_dict.values()):
        #     wx.CallAfter(frame.Close)  # Close the frame after all tasks are complete
        #     break

def U_turbulence(batch, dt, epsilon, H, k, turb_type, U_x, U_x_dif, U_y, U_y_dif, z, z_0):
    """
    Adjust the flow velocity with turbulence. 4 different evaluations are proposed but each uses a log law of the wall to go from depth-averaged velocity to velocity related to the body vertical position.

    :param batch: Batch turbulence.
    :param dt: Time step.
    :param epsilon: Epsilon value.
    :param H: Water depth.
    :param k: Turbulence kinetic energy.
    :param turb_type: Turbulence type.
    :param U_x: X velocity.
    :param U_x_dif: X velocity difference.
    :param U_y: Y velocity.
    :param U_y_dif: Y velocity difference.
    :param z: Depth array.
    :param z_0: Roughness length.
    :return: Adjusted X and Y velocities.
    """
    n = 0.027 #To be taken from WOLF
    kappa = 0.41 #Von Karman constant

    U_shear_x = np.zeros_like(H)
    U_shear_y = np.zeros_like(H)
    U_x_sign = np.zeros_like(H)
    U_y_sign = np.zeros_like(H)
    ln_z_z0 = np.zeros_like(H)

    mask_zero = (H >= 0) & (z >= 0)

    U_shear_x[mask_zero] = np.abs(U_x[mask_zero])*n*np.sqrt(9.81)/(H[mask_zero]**(1/6)) #based on the combination of Manning equation and definition of bed shear stress and shear velocity
    U_shear_y[mask_zero] = np.abs(U_y[mask_zero])*n*np.sqrt(9.81)/(H[mask_zero]**(1/6))

    U_x_sign[mask_zero] = np.sign(U_x[mask_zero])
    U_y_sign[mask_zero] = np.sign(U_y[mask_zero])

    ln_z_z0[mask_zero] = np.log(z[mask_zero] / z_0)

    if turb_type == 0: #No turbulence

        ln_H_z0 = np.log(H / z_0)
        factor = ln_H_z0# + z / H - 1 #see Eq. 7.2.12 of Principles of sediment transport in rivers, estuaries and coastal seas (Leo van Rijn)

        U_x = (U_x / factor) * ln_z_z0
        U_y = (U_y / factor) * ln_z_z0

    elif turb_type==1: #Based on a random parameter

        percentage = 5 *10**-2

        n_b = len(U_x)

        index_x = np.random.randint(0,len(batch), n_b) #Trick to not make a rnd.normal at each iteration (faster)
        index_y = np.roll(index_x,-1) #Trick to avoid using two randint
        # index = np.random.choice(len(batch), n_b) # Numba
        R_x = batch[index_x] #Number choosen randomly from a gaussian distribution of mean 0 and std 1
        R_y = batch[index_y]

        U_xy = np.hypot(U_shear_x,U_shear_y)/kappa * ln_z_z0

        U_x = U_shear_x/ kappa * ln_z_z0  #Formula derived from the log velocity profile used in boundary layer theory for turbulent open-channel flow
        U_x_turb = R_x*percentage*U_x
        U_x = U_x_sign*U_x + U_x_turb

        U_y = U_shear_y/ kappa * ln_z_z0
        U_y_turb = R_y*percentage*U_y
        U_y = U_y_sign*U_y + U_y_turb

    elif turb_type==2: #See Garcia et al. (2013), page 214, based on the shear velocity, I think this is false as it is applied on floating particles and on the position itself, can't work applied on the velocity and with friction with the bottom

        n_b = len(U_x)

        index = np.random.randint(0,len(batch), n_b) #Trick to not make a rnd.normal at each iteration
        # index = np.random.choice(len(batch), n_b) # Numba
        R = batch[index] #Constant used in the definition of U_prime

        #U_shear_glob = np.sqrt(U_x**2+U_y**2)*n*np.sqrt(9.81)/(H**(1/6))


        #U_x_shear = (U_x / factor) * ln_z_z0 #Log law of the wall
        K_H = 0.6*H*np.abs(U_shear_x)#np.abs(U_x_shear) #Turbulent diffusion coefficient (or turbulent diffusivity coefficient)
        U_x_turb = R*np.sqrt(2*K_H*dt) #In the original formula (Garcia et al. (2013), Eq. 6), we have R*np.sqrt(2*K_H*dt) but as we multiply by dt after that, we have to divide by dt before
        U_x = U_shear_x/ kappa * ln_z_z0 + U_x_turb/dt

        #U_y_shear = (U_y / factor) * ln_z_z0 #Log law of the wall
        K_H = 0.6*H*np.abs(U_shear_y)#np.abs(U_y_shear) #Turbulent diffusion coefficient (or turbulent diffusivity coefficient)
        U_y_turb = R*np.sqrt(2*K_H*dt)
        U_y = U_shear_y/ kappa * ln_z_z0 + U_y_turb/dt

    elif turb_type ==3: #See Bocksell & Loth (2001), Eqs. 16 to 21, based on k-eps

        n_b = len(U_x)
        epsilon = np.maximum(epsilon,10**-10) #Because the correction of collision is done after, trick to avoid to divide by 0 when out of the domain

        index = np.random.randint(0,len(batch), n_b) #Trick to not make a rnd.normal at each iteration
        # index = np.random.choice(len(batch), n_b) # Numba
        R = batch[index] #Same as psi in the reference
        eps_01_09 = index/n_b/10*8+0.1 #Explanation just after Eq. 17

        C_c_x = 1 + np.sign(U_x_dif) #Eq. 17
        C_c_y = 1 + np.sign(U_y_dif) #Eq. 17
        C_delta = 1.6 #Table 2 of the reference
        C_mu = 0.09 #After Eq. 17 of reference
        C_tau = 0.27 #Table 2 of the reference

        Delta = np.array([C_c_x,C_c_y])*C_delta*C_mu**(3/4)*(k**(3/2)/epsilon) #Eq. 17

        tau_delta = C_tau*eps_01_09*(k/epsilon) #Eq. 17
        tau_t_abs = np.abs(Delta/np.array([U_x_dif,U_y_dif])) #Eq. 17
        tau_t_sign = np.sign(Delta/np.array([U_x_dif,U_y_dif])) #Eq. 17
        tau_t_sign[tau_t_sign==0]=1
        tau_int = np.maximum(np.maximum(tau_delta,tau_t_abs),10**-10) #Eq. 16, problem, if we keep min, we have 0 and so U_y = inf, we test with max

        alpha = np.exp(-dt/tau_int)*tau_t_sign #Eq. 20
        sigma_u = np.sqrt(2/3*k) #Eq. 20

        U_x = alpha[0,:]*U_x + np.sqrt((1-alpha[0,:]**2)*sigma_u**2)*R# + U_x #Eq. 18
        U_y = alpha[1,:]*U_y + np.sqrt((1-alpha[1,:]**2)*sigma_u**2)*R# + U_y #Eq. 18

        ##At this time, compatible only with Wolf CPU because no k-eps given by GPU

    return U_x,U_y
