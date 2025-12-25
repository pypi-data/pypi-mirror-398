"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import matplotlib.pyplot as plt
import math
import numpy as np
from scipy.optimize import root_scalar
from typing import Literal
import logging

from .friction_law import f_barr_bathurst, f_colebrook, f_colebrook_pure

RHO_PUREWATER = 1000. # kg/m3
RHO_SEAWATER = 1025.  # kg/m3
RHO_SEDIMENT = 2650. # kg/m3
KIN_VISCOSITY = 1.e-6 # m2/s
GRAVITY = 9.81 # m/s2

BED_LOAD=1
SUSPENDED_LOAD_50=2
SUSPENDED_LOAD_100=3
WASH_LOAD=4

"""
@author : Pierre Archambeau
@date : 2022

Chezy : u = C (RJ)**.5
Strickler : C = K R**(1/6)

 --> u = K R**(2/3) J**.5

 en 2D : R = h

 --> u = K h**(2/3) J**.5

 J = u**2 / K**2 / h**(4/3)

 mais aussi

 J = f/D * u**2 /2 /g
     avec D = 4h

 --> J = f/(4h) *u**2 /2 /g
 --> tau = J * rho * h * g

 Shields :
   Theta = tau / ((rhom-rho) * g * d)
   Theta = tau / rho / ((s-1) * g * d)  avec s = rhom/rho

   Theta = J * h / ((s-1) * d)

 Strickler :
   J = u**2 / K**2 / h**(4/3)
   tau = J * rho * h * g

   tau = (q/K)**2 / h**(7/3) * rho  * g

Autres :
   J = f/(4h) *u**2 /2 /g
   tau = J * rho * h * g

   tau = f/8 * (q/h)**2 * rho

 References:
      Telemac-Mascaret, https://gitlab.pam-retd.fr/otm/telemac-mascaret/-/blob/main/sources/gaia/shields.f

      Yalin, Ferraira da Silva (2001), Fluvial Processes, IAHR Monograph

      Fredsoe,  Jorgen and Deigaard Rolf. (1992). Mechanics of Coastal Sediment.
            Sediment Transport. Advanced Series on Ocean Engineering - Vol. 3.
            World Scientific. Singapure.

      Madsen, Ole S., Wood, William. (2002).  Sediment Transport Outside the
            Surf Zone. In: Vincent, L., and Demirbilek, Z. (editors),
            Coastal Engineering Manual, Part III, Combined wave and current
            bottom boundary layer flow, Chapter III-6,
            Engineer Manual 1110-2-1100, U.S. Army Corps of Engineers,
            Washington, DC.

      Nielsen, Peter. (1992). Coastal Bottom Boundary Layers and
            Sediment Transport. Advanced Series on Ocean Engineering - Vol. 4.
            World Scientific. Singapure.

"""

def get_sadim(d:float, rhom:float = RHO_SEDIMENT, rho:float =RHO_PUREWATER) -> float:
      """
      s_adim = d**(3/2) * ((s-1) * g)**.5 / (4 * nu)

      [-] = [m^1.5 ] * [m^.5 s^-1] / [m^2 s^-1]
      """
      s=rhom/rho
      return d**(3./2.) * ((s-1) * GRAVITY)**.5 / (4 * KIN_VISCOSITY)

def get_dstar(d:float, rhom:float = RHO_SEDIMENT, rho:float=RHO_PUREWATER) -> float:
      """ compute d* """
      s = rhom/rho
      return d*(GRAVITY*(s-1)/KIN_VISCOSITY**2)**(1./3.) #VanRijn Formula

def sadim2dstar(sadim:float) -> float:
      return (4*sadim)**(2/3)

def dstar2sadim(dstar:float) -> float:
      return dstar**(3./2.) / 4

def get_d_from_sadim(sadim:float, rhom:float= RHO_SEDIMENT, rho:float=RHO_PUREWATER) -> float:
      """
      s_adim = d**(3/2) * ((s-1) * g)**.5 / (4 * nu)

      [-] = [m^1.5 ] * [m^.5 s^-1] / [m^2 s^-1]
      """
      s=rhom/rho
      return (sadim*(4*KIN_VISCOSITY)/math.sqrt((s-1)*GRAVITY))**(2/3)

def get_d_from_dstar(dstar:float, rhom:float= RHO_SEDIMENT, rho:float=RHO_PUREWATER) -> float:
      """
      d_star = d * (g * (s-1) / nu**2)**(1/3)

      [-] = [m] * ([m s^-2] / [m^4 s^-2])^(1/3)
      """
      s=rhom/rho
      return dstar / (GRAVITY*(s-1)/KIN_VISCOSITY**2)**(1./3.)

def get_psi_cr(s_adim:float) -> float:
      """
      https://nl.mathworks.com/matlabcentral/fileexchange/97447-modified-shields-diagram-and-criterion?tab=reviews
      """
      if s_adim<0.8:
            psicr = 0.1*(s_adim**(-2/7))
      elif s_adim >= 300:
            psicr = 0.06
      elif ( s_adim>=0.8 ) and ( s_adim<300 ):
            polpsi = _poly(math.log10(s_adim))
            psicr = 10**polpsi

      return psicr

def get_psi_cr2(dstar:float) -> float:
      """
      http://docs.opentelemac.org/doxydocs/v8p2r0/html/shields_8f_source.html
      """
      if dstar <= 4.0:
            psicr = 0.24/dstar
      elif dstar <= 10.:
            psicr= 0.14*dstar**(-0.64)
      elif dstar <= 20.:
            psicr= 0.04*dstar**(-0.1)
      elif dstar <= 72.:
            psicr= 0.013*dstar**0.29
      else:
            psicr= 0.045
      return psicr

def get_psi_cr3(dstar:float) -> float:
      """
      Fluvial Processes, IAHR 2001, pp 6-9
      """

      psicr = 0.13*dstar**-0.392*math.exp(-0.015*dstar**2.)+0.045*(1-math.exp(-0.068*dstar))
      return psicr

def get_shields_cr(d, rhom = RHO_SEDIMENT, rho = RHO_PUREWATER, which=2):
      """
      :param d: grain diameter [m]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]
      :param which: which formula to use (default 2) -- see funcs = [(get_sadim, get_psi_cr), (get_dstar, get_psi_cr2), (get_dstar, get_psi_cr3)]

      :return: [critical_shear_velocity, tau_cr, xadim_val, psicr]

       Example:
        [critical_shear_velocity, tau_cr, xadim_val, psicr] = get_shields_cr(0.2E-3, 2650)
      """

      assert which in [0, 1, 2], "which must be 0, 1 or 2"

      funcs = [(get_sadim,get_psi_cr),
               (get_dstar,get_psi_cr2),
               (get_dstar,get_psi_cr3)]

      # % Getting the sediment-fluid parameter
      s = rhom/rho # [-]
      denom_shields= (s-1)*GRAVITY*d  # [m²/s²] en réalité denom/rho

      xadim_val = funcs[which][0](d,rhom,rho)
      psicr = funcs[which][1](xadim_val)

      # Using the critical value of Shields parameter
      # Knowing the maximum bottom shear stress
      tau_cr = rho * denom_shields * psicr  # Pa
      critical_shear_velocity = math.sqrt(denom_shields * psicr) # m/s

      return [critical_shear_velocity, tau_cr, xadim_val, psicr]

def _poly(x:float) -> float:
      return ((0.002235*x**5)-(0.06043*x**4)+(0.20307*x**3)+ \
                   (0.054252*x**2)-(0.636397*x)-1.03167)

def _dpolydx(x:float) -> float:
      """ derivative of _poly """
      return ((0.002235*5*x**4)-(0.06043*4*x**3)+(0.20307*3*x**2)+ \
                   (0.054252*2*x)-(0.636397))

def get_sadim_min() -> float:
      return root_scalar(_dpolydx, method='bisect', bracket=[10, 20]).root

def get_tau_from_psiadim(psiadim, d:float, rhom:float=2650, rho:float=RHO_PUREWATER) -> float:
      s=rhom/rho
      denom_shields= (s-1)*GRAVITY*d  ## en réalité denom/rho
      return rho * denom_shields * psiadim

def get_d_min(rhom:float = RHO_SEDIMENT, rho:float=RHO_PUREWATER) -> float:
      return get_d_from_sadim(get_sadim_min(),rhom,rho)

def _d_cr(x:float, tau_obj:float, rhom:float, rho:float, xadim:float, yadim:float) -> float:
      """ Equation to solve to get d_cr """
      s=rhom/rho
      denom_shields= (s-1)*GRAVITY*x  ## en réalité denom/rho
      psi_obj = tau_obj/denom_shields/rho
      psi_cr=yadim(xadim(x,rhom,rho))
      return psi_obj-psi_cr

def _get_d_cr(tau_cr, rhom = RHO_SEDIMENT, rho=RHO_PUREWATER, which=2) -> float:
      """ Critical diameter d_cr for Shields criterion

      :param tau_cr: critical shear stress [Pa]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]
      :param which: which formula to use (default 2) -- see funcs = [(get_sadim, get_psi_cr), (get_dstar, get_psi_cr2), (get_dstar, get_psi_cr3)]
      """

      assert which in [0, 1, 2], "which must be 0, 1 or 2"

      dminabs = 1.e-100
      dmaxabs = 20
      funcs = [(get_sadim, get_psi_cr),
               (get_dstar, get_psi_cr2),
               (get_dstar, get_psi_cr3)]

      d_cr = root_scalar(_d_cr,(tau_cr, rhom, rho, funcs[which][0],funcs[which][1]), 'bisect', bracket=[dminabs, dmaxabs])

      return d_cr.root

def get_d_cr(q:float, h:float, K:float,
             rhom:float = RHO_SEDIMENT, rho:float=RHO_PUREWATER,
             method='brenth', which=2,
             friction_law:Literal['Strickler', 'Colebrook'] = 'Strickler') -> list[float]:
      """
      Diamètre critique d'emportement par :
            - Shields
            - Izbach

      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param K: Strickler friction coefficient [m1/3/s]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]
      :param method: method to solve the equation (default 'brenth')
      :param which: which formula to use (default 2)  -- see funcs = [(get_sadim,get_psi_cr),(get_dstar,get_psi_cr2),(get_dstar,get_psi_cr3)]
      """

      assert which in [0, 1, 2], "which must be 0, 1 or 2"
      assert friction_law in ['Strickler', 'Colebrook'], "friction_law must be 'Strickler' or 'Colebrook'"

      if q==0.:
            return 0.,0.

      # tau_cr = (q/K)**2 / h**(7/3) * rho  * GRAVITY # rho*g*h*J
      if friction_law == 'Strickler':
            tau_cr = get_friction_slope_2D_Manning(q, h, 1/K)  * rho * GRAVITY * h # rho*g*h*J
      elif friction_law == 'Colebrook':
            tau_cr = get_friction_slope_2D_Colebrook(q, h, K) * rho * GRAVITY * h

      dminabs = 1.e-100
      dmaxabs = 20

      funcs = [(get_sadim, get_psi_cr),(get_dstar, get_psi_cr2),(get_dstar, get_psi_cr3)]

      try:
            d_cr = root_scalar(_d_cr,(tau_cr,rhom,rho,funcs[which][0],funcs[which][1]), method, bracket=[dminabs, dmaxabs], rtol = 1e-2)
            return d_cr.root, izbach_d_cr(q,h,rhom,rho)
      except:
            izbach = izbach_d_cr(q,h,rhom,rho)
            return izbach,izbach

def get_settling_vel(d:float, rhom:float= RHO_SEDIMENT, rho:float=RHO_PUREWATER) -> float:
      """
      Vitesse de chute

      :param d: grain diameter [m]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]
      """
      dstar = get_dstar(d,rhom,rho)
      ws = KIN_VISCOSITY/d*(math.sqrt(25+1.2*dstar**2.)-5)**(3./2.)
      return ws

def get_Rouse(d:float, q:float, h:float, K:float, rhom:float= RHO_SEDIMENT, rho:float=RHO_PUREWATER) -> float:
      """
      Vitesse de chute

      :param d: grain diameter [m]
      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param K: Strickler friction coefficient [m1/3/s]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]
      """
      # tau_cr = (q/K)**2 / h**(7/3) * rho  * GRAVITY
      # shear_vel = math.sqrt(tau_cr/rho)
      shear_vel = q/K / h**(7./6.)* math.sqrt(GRAVITY)
      ws = get_settling_vel(d,rhom,rho)
      # von Kármán constant
      k = 0.40

      return ws/(k*shear_vel)

def _get_Rouse(d:float, q:float, h:float, K:float, rhom:float= RHO_SEDIMENT, rho:float=RHO_PUREWATER, frac:float=50) -> float:
      """
      Settling velocity function -- used in root_scalar

      :param d: grain diameter [m]
      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param K: Strickler friction coefficient [m1/3/s]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]
      """
      # tau_cr = (q/K)**2 / h**(7/3) * rho  * GRAVITY
      # shear_vel = math.sqrt(tau_cr/rho)
      shear_vel = q/K / h**(7/6)* math.sqrt(GRAVITY)
      ws = get_settling_vel(d,rhom,rho)
      # von Kármán constant
      k = 0.40
      denom = k*shear_vel
      if denom>0.:
            rouse = ws/(k*shear_vel)
      else:
            rouse = 0.

      if frac==50:
            return rouse-2.5
      elif frac==100:
            return rouse-1.2

def get_transport_mode(d:float, q:float, h:float, K:float, rhom:float= RHO_SEDIMENT, rho:float=RHO_PUREWATER): # -> BED_LOAD | SUSPENDED_LOAD_50 | SUSPENDED_LOAD_100 | WASH_LOAD:
      """
      Transport mode

      return in [BED_LOAD, SUSPENDED_LOAD_50, SUSPENDED_LOAD_100, WASH_LOAD]

      :param d: grain diameter [m]
      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param K: Strickler friction coefficient [m1/3/s]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]

      """

      rouse = get_Rouse(d,q,h,K,rhom,rho)
      if rouse>=2.5:
            return BED_LOAD
      elif rouse>=1.2:
            return SUSPENDED_LOAD_50
      elif rouse>=0.8:
            return SUSPENDED_LOAD_100
      else:
            return WASH_LOAD

def get_d_cr_susp(q:float, h:float, K:float, rhom:float= RHO_SEDIMENT, rho:float=RHO_PUREWATER, method='brenth', which=50) -> float:
      """
      Diamètre critique d'emportement par suspension à 50% --> cf Rouse 1.2

      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param K: Strickler friction coefficient [m1/3/s]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]

      """
      if q==0.:
            return 0.

      dminabs = 1.e-100
      dmaxabs = 20
      try:
            d_cr = root_scalar(_get_Rouse,(q,h,K,rhom,rho,which),method,bracket=[dminabs, dmaxabs],rtol = 1e-2)
            return d_cr.root
      except:
            return 0.

def shieldsdia_sadim(s_psicr=None, dstar_psicr=None, figax=None) -> tuple[plt.Figure,plt.Axes]:
      """ Plot Shields diagram with sadim as x-axis

      :param s_psicr: tuple (S, psicr) for a specific point to plot on the diagram
      :param dstar_psicr: tuple (dstar, psicr) for a specific point to plot on the diagram
      :param figax: tuple (fig, ax) to plot on a specific figure and axes
      """

      smax = 1000
      rangoS = np.arange(0.1,smax,0.1)
      psicri = np.asarray([get_psi_cr(curx) for curx in rangoS])
      psicri2 = np.asarray([get_psi_cr2(sadim2dstar(curx)) for curx in rangoS])
      psicri3 = np.asarray([get_psi_cr3(sadim2dstar(curx)) for curx in rangoS])

      if figax is None:
            fig, ax = plt.subplots(1,1)
            ax.set_title('Modified Shields diagram')
      else:
            fig, ax = figax

      ax.plot(rangoS,psicri,linewidth=4,color=[0,0,.8],label='Madsen and Grant, 1976')
      ax.plot(rangoS,psicri2,linewidth=4,color=[0.8,0,.8],label='Telemac-Mascaret, 2022')
      ax.plot(rangoS,psicri3,linewidth=4,color=[0.5,0,.8],label='Yalin and Ferreira da Silva, 2001')

      ylabel=r'$ {\theta}_{cr} =  \frac{u^*}{g \left( s-1 \right) d}$'
      xlabel = r'$ {S^*} = d^{3/2} \frac{ {\left( \left( s-1 \right) g \right)}^{1/2}}{4 \nu} $'

      ax.set_ylabel('Critical shields '+ylabel+'  (dimensionless)')
      ax.set_xlabel('Sediment - fluid parameter  '+xlabel+ ' (dimensionless)')

      if s_psicr is not None:
            S = s_psicr[0]
            psicr = s_psicr[1]
            x = [S,0.1,S]
            y = [psicr,psicr,.01]
            ax.scatter(x,y,50,c='red')

            ax.plot([0.8, 0.8],[0.01,1],color=[0.75,0.75,0.75],linestyle=':')
            ax.text(S+.005,psicr+0.005,'$S^*$')

      if dstar_psicr is not None:
            S = dstar2sadim(dstar_psicr[0])
            psicr = dstar_psicr[1]
            x = [S,0.1,S]
            y = [psicr,psicr,.01]
            ax.scatter(x,y,50,c='red')

            ax.plot([0.8, 0.8],[0.01,1],color=[0.75,0.75,0.75],linestyle=':')
            ax.text(S+.005,psicr+0.005,'$S^*$')

      ax.set_xlim([.1,smax])
      ax.set_ylim([0.01,1])
      ax.set_xscale('log')
      ax.set_yscale('log')
      ax.grid(True,'both',axis='both')
      ax.legend()

      # plt.show()

      return fig,ax

def shieldsdia_dstar(s_psicr=None, dstar_psicr=None, figax=None) -> tuple[plt.Figure,plt.Axes]:
      """ Plot Shields diagram with dstar as x-axis

      :param s_psicr: tuple (S, psicr) for a specific point to plot on the diagram
      :param dstar_psicr: tuple (dstar, psicr) for a specific point to plot on the diagram
      :param figax: tuple (fig, ax) to plot on a specific figure and axes
      """

      smax = 1000
      d_stars = np.arange(0.1,smax,0.1)
      diams = np.asarray([get_d_from_dstar(curx) for curx in d_stars])
      rangoS = np.asarray([get_sadim(curx) for curx in diams])

      psicri = np.asarray([get_psi_cr(curx) for curx in rangoS])

      psicri2 = np.asarray([get_psi_cr2(curx) for curx in d_stars])
      psicri3 = np.asarray([get_psi_cr3(curx) for curx in d_stars])

      if figax is None:
            fig, ax = plt.subplots(1,1)
            ax.set_title('Modified Shields diagram')
      else:
            fig, ax = figax

      ax.plot(d_stars,psicri,linewidth=4,color=[0,0,.8],label='Madsen and Grant, 1976')
      ax.plot(d_stars,psicri2,linewidth=4,color=[0.8,0,.8],label='Telemac-Mascaret, 2022')
      ax.plot(d_stars,psicri3,linewidth=4,color=[0.5,0,.8],label='Yalin and Ferreira da Silva, 2001')

      ylabel=r'$ {\theta}_{cr} =  \frac{u^*}{g \left( s-1 \right) d}$'
      xlabel = r'$ {D^*} = d \left( \frac{\rho_s g}{\rho \nu^2} \right) ^{1/3} $'

      ax.set_ylabel('Critical shields '+ylabel+'  (dimensionless)')
      ax.set_xlabel('Sediment - fluid parameter  '+xlabel+ ' (dimensionless)')

      if s_psicr is not None:
            S = s_psicr[0]
            psicr = s_psicr[1]
            S = sadim2dstar(S)
            x = [S,0.1,S]
            y = [psicr,psicr,.01]
            ax.scatter(x,y,50,c='red')
            ax.plot([0.8, 0.8],[0.01,1],color=[0.75,0.75,0.75],linestyle=':')
            ax.text(S+.005,psicr+0.005,'$S^*$')

      if dstar_psicr is not None:
            S = dstar_psicr[0]
            psicr = dstar_psicr[1]
            x = [S,0.1,S]
            y = [psicr,psicr,.01]
            ax.scatter(x,y,50,c='red')
            ax.plot([0.8, 0.8],[0.01,1],color=[0.75,0.75,0.75],linestyle=':')
            ax.text(S+.005,psicr+0.005,'$S^*$')

      ax.set_xlim([.1,smax])
      ax.set_ylim([0.01,1])
      ax.set_xscale('log')
      ax.set_yscale('log')
      ax.grid(True,'both',axis='both')
      ax.legend()

      # plt.show()

      return fig,ax

def shieldsdia_dim(figax=None) -> tuple[plt.Figure,plt.Axes]:
      """ Plot Shields diagram with dimensional values"""

      smax=1e6
      rangoS = np.concatenate([np.arange(0.1,300,0.1),np.arange(300.,smax,5.)])
      psicri = np.asarray([get_psi_cr(curx) for curx in rangoS])
      psicri2 = np.asarray([get_psi_cr2(sadim2dstar(curx)) for curx in rangoS])
      psicri3 = np.asarray([get_psi_cr3(sadim2dstar(curx)) for curx in rangoS])

      if figax is None:
            fig, ax = plt.subplots(1,1)
            ax.set_title('Modified Shields diagram')
      else:
            fig, ax = figax

      d = get_d_from_sadim(rangoS)
      tau = [get_tau_from_psiadim(psi,curd) for psi,curd in zip(psicri,d)]
      tau2 = [get_tau_from_psiadim(psi,curd) for psi,curd in zip(psicri2,d)]
      tau3 = [get_tau_from_psiadim(psi,curd) for psi,curd in zip(psicri3,d)]

      ax.plot(d,tau,linewidth=4,color=[0,0,.8],label='Madsen and Grant, 1976')
      ax.plot(d,tau2,linewidth=4,color=[0.8,0,.8],label='Telemac-Mascaret, 2022')
      ax.plot(d,tau3,linewidth=4,color=[0.5,0,.8],label='Yalin and Ferreira da Silva, 2001')

      ax.set_ylabel('Critical shear stress [Pa]')
      ax.set_xlabel('Sediment diameter [m]')

      ax.set_xlim([np.min(d),np.max(d)])
      ax.set_ylim([np.min(tau),np.max(tau)])
      ax.set_xscale('log')
      ax.set_yscale('log')
      ax.grid(True,'both',axis='both')
      ax.legend()

      # plt.show()

      return fig,ax

def get_friction_slope_2D_Manning(q:float, h:float, n:float) -> float:
      """
      Compute friction slope j for 2D flow with Manning/Strickler friction law

      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param n: Manning friction coefficient [m^{-1/3}.s]
      """

      denom = h**(4./3.)
      if denom > 0.:
            j = (q/h * n)**2.0 / denom
      else:
            j = 0.

      return j

def get_friction_slope_2D_Strickler(q:float, h:float, K:float) -> float:
      """
      Compute friction slope j for 2D flow with Strickler friction law

      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param K: Strickler friction coefficient [m^{1/3}/s]
      """

      return get_friction_slope_2D_Manning(q, h, 1./K)  # n = 1/K

def get_friction_slope_2D_Colebrook(q:float, h:float, K:float) -> float:
      """
      Compute friction slope j for 2D flow with Colebrook-White friction law

      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param K: height of roughness [m] - will be used to compute k/D or k/(4h) in 2D flow
      """

      four_hydraulic_radius = 4.0 * h

      if four_hydraulic_radius > 0.:
            reynolds = (q/h) * four_hydraulic_radius / KIN_VISCOSITY # u*4h/nu == 4q/nu
            k_sur_D = K / four_hydraulic_radius
            j = f_colebrook(k_sur_D, reynolds) / four_hydraulic_radius * (q/h)**2.0/2.0/GRAVITY
      else:
            j = 0.

      return j

def get_shear_velocity_2D_Manning(q:float, h:float, n:float) -> float:
      """
      Compute shear velocity u_* for 2D flow with Manning/Strickler friction law

      :param j: friction slope [-]
      :param h: water depth [m]
      :param q: discharge [m3/s]
      :param n: Manning friction coefficient [m-1/3.s]
      """

      j = get_friction_slope_2D_Manning(q,h,n)

      ushear = (GRAVITY*h*j)**0.5

      return ushear

def get_shear_velocity_2D_Colebrook(q:float, h:float, K:float) -> float:
      """
      Compute shear velocity u_* for 2D flow with Colebrook-White friction law

      :param j: friction slope [-]
      :param h: water depth [m]
      :param q: discharge [m3/s]
      :param K: Colebrook-White friction coefficient [m]
      """

      j = get_friction_slope_2D_Colebrook(q,h,K)

      ushear = (GRAVITY*h*j)**0.5

      return ushear

def get_Shields_2D_Manning(s:float, d:float, q:float, h:float, n:float) -> float:
      """
      Compute Shields dimensionless parameter for 2D flow with Manning/Strickler friction law

      :param s: sediment density / water density [-]
      :param d: sediment diameter [m]
      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param n: Manning friction coefficient [m-1/3.s]

      See also get_Shields_2D_Strickler
      """
      # calcul de terme de pente de frottement

      # j = (q/h)**2.0 / K**2. / h**(4./3.)
      j = get_friction_slope_2D_Manning(q,h,n)

      shields = j*h / (d*(s-1))

      return shields

def get_Shields_2D_Strickler(s:float, d:float, q:float, h:float, K:float) -> float:
      """
      Compute Shields dimensionless parameter for 2D flow with Manning/Strickler friction law

      :param s: sediment density / water density [-]
      :param d: sediment diameter [m]
      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param K: Strickler friction coefficient [m1/3/s]

      See also get_Shields_2D_Manning
      """
      # calcul de terme de pente de frottement

      n = 1./K
      return get_Shields_2D_Manning(s, d, q, h, n)


def izbach_d_cr(q:float, h:float, rhom:float=2650, rho:float=RHO_PUREWATER, method='ridder') -> float:
      """
      https://en.wikipedia.org/wiki/Izbash_formula

      u_c/ ((s-1) * g * d)**.5 = 1.7

      avec  :
            (s-1) = (rho_m - rho) / rho
            u_c = 85% u_moyen)

      --> d = u_c**2 / ((s-1) * g) / 1.7**2

      --> d = (0.85 * q/h)**2 / ((s-1) * g) / 1.7**2

      :param q: discharge [m3/s]
      :param h: water depth [m]
      :param rhom: sediment density [kg/m3]
      :param rho: water density [kg/m3]
      :param method: method to solve the equation (default 'ridder')
      """
      s = rhom/rho
      #      (0.85 * q/h)**2. / ((s-1.) * GRAVITY) / 1.7**2.
      # avec (2 / 1.7**2) = 0.692041... = 0.7
      # <=>  0.7 * (0.85 * q/h)**2. / (2 * GRAVITY) / (s-1.)
      # <=>  (q/h)**2. / (2 * GRAVITY) / (s-1.) / 1.406**2

      return (q/h)**2. / (2 * GRAVITY) / (s-1.) / 1.2**2 # We are using 1.2 instead of 1.406 -- see GCIV2035-1 - Hydrodynamique fluviale


## Portage de WOLF2D - Fortran pour Barr-Bathurst

# def get_Shields_2D_pw(s:float, d:float, q_abs:float, h:float, k_rough:float, which_law = 'Manning'):
#       """
#       """
#       # calcul de terme de pente de frottement
#       if which_law == 'Manning':

#             j = (q_abs/h)**2.0 / k_rough**2. / h**(4./3.)

#       elif which_law == 'Barr_Bathurst':
#             k_sur_h = k_rough/(4.0*h)
#             Reynolds = 4.0 * q_abs /KIN_VISCOSITY # u*4h/nu == 4q/nu
#             j = f_barr_bathurst(k_sur_h,Reynolds)/(4.0*h) * (q_abs/h)**2.0/2.0/GRAVITY

#       shields = j*h / (d*(s-1))

#       # shields = f/4 * u**2 /2 /g /(d * (rho_s-rho_w) / rho_w)
#       # shields = tau / (rho_s - rho_w) /g /d
#       # tau = f/8 * rho_w * u**2

#       return shields

# def get_effective_d_2D(s:float, theta_cr:float, q_abs:float, h:float, k_rough:float):
#       """
#       Calcul du diamètre de grain emporté par une approche basée sur une tension efficace

#       Portage du code de calcul de WOLF2D
#       @authors : Pierre Archambeau (2022)
#       """

#       #if which_friction_law#=rough_Barr_Bathurst:
#        ##les autres lois de frottement ne sont pas implémentées mais aucune difficulté particulière
#       ##ne devraient empêcher cela

#       my_exp = [0.0, 0.10, 0.20, 0.30, 0.40, 0.420, 0.440, 0.460, 0.480,
#                 0.50, 0.52, 0.54, 0.56, 0.58,
#                 0.6, 0.62, 0.64, 0.66, 0.68,
#                 0.7, 0.71, 0.72, 0.73, 0.74, 0.75]

#       ##calcul du coefficient de frottement (point de vue de l'écoulement)
#       u_abs = q_abs/h
#       Reynolds = q_abs * 4 / KIN_VISCOSITY
#       k_sur_h = k_rough/(4*h)
#       f_flow = f_barr_bathurst(k_sur_h,Reynolds)

#       #valeur initiale (pas de tension efficace)
#       exp = my_exp[0]
#       d = f_flow**(1-exp)*u_abs**2/(8*(s-1)*GRAVITY*theta_cr)
#       #boucle pour approcher les exposants requis
#       for cur_exponent in range(1,25):
#             exp = my_exp[cur_exponent]
#             #partie constante du rapport d = lamda'^(3/4)*lambda^(1/4)*U^2/8/(s-1)/g/theta_cr
#             cst = f_flow**(1-exp)*u_abs**2/(8*(s-1)*GRAVITY*theta_cr)
#             #boucle pour converger sur un diamètre qui respecte l'égalité
#             k_sur_h = d/(4*h)
#             f_grain = f_barr_bathurst(k_sur_h,Reynolds)
#             f_obj = d-f_grain**exp*cst
#             nb_ite = 0
#             while abs(f_obj) > 1.e-6 and nb_ite < 20:
#                   #calcul de la dérivée numérique
#                   k_sur_h = (d+1.e-6)/(4*h)
#                   f_pert1 = f_barr_bathurst(k_sur_h,Reynolds)
#                   k_sur_h = (d-1.e-6)/(4*h)
#                   f_pert2 = f_barr_bathurst(k_sur_h,Reynolds)
#                   dfdd = 1-cst*exp*f_grain**(exp-1)*(f_pert1-f_pert2)/2.e-6
#                   frac = f_obj/dfdd
#                   #modifiation de d
#                   if abs(frac) > 0.5*d:
#                         if frac>0:
#                               frac = 0.5*d
#                         else:
#                               frac = -0.5*d
#                   d = d - frac
#                   #calcul de la nouvelle donction objectif
#                   k_sur_h = d/(4*h)
#                   f_grain = f_barr_bathurst(k_sur_h,Reynolds)
#                   f_obj = d-f_grain**exp*cst
#                   nb_ite = nb_ite + 1

#       return d
