"""
Hydrogramme Synthétique MonoFréquance - HSMF
Mono Frequency Synthetic Hydrograph - MFSH

@author : Pierre Archambeau - ULiege - HECE
@date   : 2023
"""
from scipy import optimize
import numpy as np
import matplotlib.pyplot as plt


def _objectif(x,hyd,nbsteps,dt,istart,iend,vobj):
    """
    Fonction objectif à minimiser : écart entre volume attendu (vobj) et calculé (maximum sur base d'une convolution sur l'ensemble de l'hydrogramme)
    variable : débit à l'heure courante (x)

    On ajoute tout de même la convolution de la fin d'intervalle dans la fonction obj car si le vrai maximum est indépedant de x,
     l'algo d'optimisation pourrait ne pas converger correctement, autrement cela ne change pas la position de l'optimum
    """
    hyd[istart:iend]=x

    a = np.ones(nbsteps)
    conv=np.convolve(a,hyd)*dt
    res = np.max(conv)

    obj = (res-vobj)**2 + (conv[iend-1]-vobj)**2

    # print(obj)
    return obj

class Hydro_HSMF():

    def __init__(self,Q, durees, temps_montee, dt, label='') -> None:
        """
        Args:
            Q (np.array): Tableau des débits respectant les QDF pour une période de retour donnée
            durees (np.array): durées en heures relatives aux Q
            temps_montee (Integer): Nombre d'heures pour la montée en crue
            dt (Float): Pas de temps de discrétisation en heures -- doit être l'heure ou un diviseur de l'heure
            label (str)
        """
        self.debit = np.asarray(Q)
        self.durees = np.asarray(durees)

        self.volume = self.debit*self.durees
        self.temps_montee = temps_montee
        self.dt = dt
        self.id_pic = int(temps_montee/dt)
        self.label=label

        self._init_HSMF()

    def _init_HSMF(self):

        self.temps_base = float(np.max(self.durees)+self.temps_montee)
        self.temps = np.arange(self.temps_base,step=self.dt)
        self.hydro = np.zeros(int(self.temps_base/self.dt))
        self.hydro[:self.id_pic+1]=np.linspace(0.,self.debit[0],num=self.id_pic+1,endpoint=True)
        self.hydro[self.id_pic:(self.id_pic+int(1/self.dt))]=self.hydro[self.id_pic]

    def plot(self):
        volume = self.debit*self.durees

        volhydro=[]

        for curdur in durees:
            duree_steps = int(curdur/self.dt)
            a = np.ones(duree_steps)
            conv=np.convolve(a,self.hydro)
            volhydro.append(np.max(conv)*self.dt)

        fig,ax = plt.subplots(1,1)
        ax.plot([0,1],[0,1],'k')
        ax.plot(volume/np.max(volume),volhydro/np.max(volume))
        ax.set_xlabel('Volume théorique / Volume max [-]')
        ax.set_ylabel('Volume hydrogramme / Volume max [-]')

        fig,ax = plt.subplots(1,1)
        ax.plot([0]+list(durees),[0]+list(volume/np.max(volume)),label="Volume")
        ax.step(list(durees-1)+[durees[-1]],list(Q/np.max(Q))+[Q[-1]/np.max(Q)],where='post', label="Débit")
        ax.set_xlabel('Temps [h]')
        ax.set_ylabel('V/V_max ou Q/Q_max [-]')
        ax.set_xticks([0]+list(durees))
        ax.grid()
        ax.legend()

        fig,ax = plt.subplots(1,1)
        self._plot_Q(ax)
        plt.show()

    def _plot_Q(self, ax:plt.Axes, decal=0, label=None, lw=2, xup_bound=None):

        ax.step(list(self.temps+decal)+[self.temps[-1]+decal+1],list(self.hydro)+[0.],where='post',label=label,lw=lw)
        ax.set_xlabel('Temps [h]')
        ax.set_ylabel('Débit [$m^3s^{-1}$]')

        if xup_bound is None:
            ax.set_xticks(np.arange(0,self.temps_base+1,1))
            ax.set_xbound(0,self.temps_base)
        else:
            ax.set_xticks(np.arange(0,xup_bound+1,1))
            ax.set_xbound(0,xup_bound)
        ax.grid()

    def opt_hydro(self, opti_method = 'brent'):
        """
        Calcul de l'hydrogramme par optimisation progressive

        Hypothèse : les débits sont donnés avec une résolution maximale horaire

        Méthode :
            - la phase d'initialisation crée une montée en crue linéaire sur base du temps de montée et du premier débit horaire
            - on recherche ensuite le débit suivant:
                - suppoosé constant sur une durée correspondant à l'intervalle de discrétisation de durée
                - par résolution d'un problème de minimisation de l'écart de volume vis-à-vis du volume théorique
                - le volume peut apparaître n'importe où dans l'hydrogramme entre 0 et iend (recherche par np.max du produit de convolution)
            - une fois le problème résolu, on incrémente l'espace par identification de l'index du maximum

        Constat :
            - il n'y a aucune garantie que l'hydrogramme total respecte le temps de base
            - le temps de base réel peut en effet être plus court si au moins un volume n'est pas totalement situé sur un inervalle d'intégration à droite du pic
            - plus le temps de montée est long, plus le point précédent sera rencontré
        """

        # Bornes de variation du débit
        bmin = 0.
        bmax = 2*np.max(self.debit)

        istart= self.id_pic
        for i, duree_h in enumerate(self.durees):

            # volume objectif pour la duree courante
            vobj=self.volume[i]

            #nombre de pas de temps correspondant à la duree en heures
            nbsteps = int(np.ceil(duree_h / self.dt))

            #valeur initiale
            x0=bmax

            if duree_h>1:
                delta_duree = duree_h - self.durees[i-1]
            else:
                delta_duree = 1

            iend = istart+int(delta_duree/self.dt)

            if opti_method == 'brent':
                res = optimize.minimize_scalar(_objectif,
                                args=(self.hydro,nbsteps,self.dt,istart,iend,vobj),
                                bracket=[bmin,bmax],method='brent',
                                )
            else:
                res = optimize.minimize_scalar(_objectif,
                                args=(self.hydro,nbsteps,self.dt,istart,iend,vobj),
                                bounds=[bmin,bmax],method='bounded',
                                )


            if not res.success:
                raise Exception('Mauvaise convergence !!')

            # recherche de la position du max par une dernière convolution
            a = np.ones(nbsteps)
            conv=np.convolve(a,self.hydro)*self.dt
            obj = (conv-vobj)**2
            istart=max(istart,np.argmin(obj)+1) # on ne s'autorise pas à revenir sur nos pas
            # print(istart)
            self.hydro[istart+1:]=0.

if __name__=='__main__':

    """
    Exemple d'utilisation
    S'éxécute lorsque le module est appelé seul --> __main__
    """

    dt = 1
    tempsmontee=17 # heures

    Q = np.asarray([207.33851772, 208.46446432, 205.85676334, 205.52208722,
       202.30904999, 199.84962431, 195.58210152, 190.75065285,
       185.64035991, 181.26944843, 177.7397113 , 175.56787637,
       174.19528593, 172.98132568, 171.9939246 , 171.27350152,
       170.59878148, 169.77843312, 168.37898793, 167.52280078,
       167.19280491, 168.13523496, 169.15874283, 169.51676553,
       169.67776545, 170.04264047, 170.2771057 , 170.4201083 ,
       170.2434686 , 169.62974382, 168.74963501, 167.50036656,
       165.94279162, 164.2659497 , 162.18776759, 159.76241739,
       156.76334139, 153.76184211, 150.86970543, 148.18140668,
       146.14996746, 144.1462274 , 141.99705659, 139.68050718,
       137.38151134, 134.93303242, 132.54817242, 130.25078043])

    # Exemple avec variation linéaire du débit
    # Q = np.linspace(207,130,len(Q))

    durees = np.asarray([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17,
       18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,
       35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48])

    myhydro = Hydro_HSMF(Q,durees,tempsmontee,dt)
    myhydro.opt_hydro()
    myhydro.plot()