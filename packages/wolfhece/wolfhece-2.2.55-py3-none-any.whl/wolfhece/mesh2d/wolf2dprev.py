"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import re
import sys

try:
    from OpenGL.GL import *
except:
    msg=_('Error importing OpenGL library')
    msg+=_('   Python version : ' + sys.version)
    msg+=_('   Please check your version of opengl32.dll -- conflict may exist between different files present on your desktop')
    raise Exception(msg)

import numpy as np
import shutil
from os.path import exists
from os import makedirs
import matplotlib.pyplot as plt
import matplotlib.path as mpltPath
import wx
import logging
from enum import Enum
from datetime import datetime as dt
from datetime import timezone as tz
from typing import List, Tuple, Dict, Union, Literal

from ..wolf_array import WOLF_ARRAY_FULL_INTEGER, WOLF_ARRAY_FULL_SINGLE, WolfArray, WolfArrayMB, WolfArrayMNAP, \
    header_wolf, WolfArrayMNAP, WOLF_ARRAY_MB_SINGLE, WOLF_ARRAY_FULL_LOGICAL, WOLF_ARRAY_FULL_SINGLE, getkeyblock, WOLF_ARRAY_MB_INTEGER, WOLF_ARRAY_MNAP_INTEGER

from ..PyVertexvectors import *
from ..PyVertex import getIfromRGB
from ..PyTranslate import _
from ..CpGrid import CpGrid
from ..GraphNotebook import PlotPanel
from ..PyParams import Wolf_Param, new_json, key_Param, Type_Param
from .cst_2D_boundary_conditions import BCType_2D, Direction, BCType_2D_To_BCType_2D_GPU

PREV_INFILTRATION_NULL = 0  #PAS D'INFILTRATION
PREV_INFILTRATION_SIMPLE = 1  #INFILTRATION SIMPLE (RÉPARTITION UNIFORME DU DÉBIT INJECTÉ PAR FICHIER .INF)
PREV_INFILTRATION_MOD_MOMENTUM = 2  #INFILTRATION AVEC MODIFICATION DE LA QT DE MVT (RÉPARTITION NON UNIFORME DU DÉBIT INJECTÉ PAR FICHIER .INF)
PREV_INFILTRATION_MOD_MOMENTUM_IMPOSED = 4  #INFILTRATION AVEC MODIFICATION IMPOSÉE DE LA QT DE MVT (RÉPARTITION NON UNIFORME DU DÉBIT INJECTÉ PAR FICHIER .INF)
PREV_INFILTRATION_VAR_SIMPLE = -1  #INFILTRATION VARIABLE (RÉPARTITION UNIFORME DU DÉBIT INJECTÉ CALCULÉ SUR BASE DE L'ÉTAT HYDRODYNAMIQUE INSTANTANÉ)
PREV_INFILTRATION_VAR_MOD_MOMENTUM = -2  #INFILTRATION VARIABLE AVEC MOD QT MVT (RÉPARTITION NON UNIFORME DU DÉBIT INJECTÉ CALCULÉ SUR BASE DE L'ÉTAT HYDRODYNAMIQUE INSTANTANÉ)
PREV_INFILTRATION_VAR_LINKED_ZONES = -3  #INFILTRATION/EXFILTRATION "INTERNE" VARIABLE (RÉPARTITION UNIFORME DU DÉBIT SUR BASE DE DEUX ZONES D'INFILTRATION)

PREV_INFILTRATION_MODES = [PREV_INFILTRATION_NULL, PREV_INFILTRATION_SIMPLE, PREV_INFILTRATION_MOD_MOMENTUM, PREV_INFILTRATION_MOD_MOMENTUM_IMPOSED, PREV_INFILTRATION_VAR_SIMPLE, PREV_INFILTRATION_VAR_MOD_MOMENTUM, PREV_INFILTRATION_VAR_LINKED_ZONES]

##
PREV_READ_TXT = 1
PREV_READ_FINE = 2
PREV_READ_MB = 3

NOT_USED = _('Not used')

NB_GLOB_GEN_PAR = 36
NB_BLOCK_GEN_PAR = 23
NB_GLOB_DEBUG_PAR = 60
NB_BLOCK_DEBUG_PAR = 60

def find_sep(line:str):
    if ',' in line:
        return ','
    elif ' ' in line:
        return ' '
    elif '\t' in line:
        return '\t'
    elif ';' in line:
        return ';'
    else:
        logging.error(f"Unrecognized separator in line {line}")
        return None

class prev_parameters_blocks:
    """
    Paramètres de calcul propres aux blocs.

    Il y a :
     - 23 paramètres généraux - NB_BLOCK_GEN_PAR
     - 60 paramètres (potentiels) de "debug" - Tous les paramètres debug ne sont pas utilisés pour le moment - NB_BLOCK_DEBUG_PAR.

    :remark : Les noms de variables ne sont pas nécessairement identiques à ceux utilisés dans le code Fortran.

    """

    def __init__(self, parent:"prev_parameters_simul" = None) -> None:
        """
        Constructeur de la classe

        """

        self.parent:"prev_parameters_simul" = parent    # parent de l'objet
        self.computed                       = True      # Bloc à calculer ou non

        self._name                          = ''        # Nom du bloc

        self._has_forcing   = 0  # forcing ou pas
        self._reconstruction_internal   = 0  #=0 si rec constante, 1 si rec linéaire
        self._reconstruction_frontier   = 2  #=0 si rec cst, 1 si rec lin non limitée, 2 si rec lin limitée des bords frontière
        self._reconstruction_free_border= 0  #type de reconstruction des bords libres (0 = cst, 1 = lin limitée (non implémenté), 2 = lin non limitée)

        self._limiting_neighbors    = 5  # nbre de voisins pour la limitation
        self._limiting_h_or_Z       = 0  # =0 si limitation de h, 1 si limitation de h+z

        self._treating_frontier     = 1  # type de traitement des frontières (1 = rien, 0 = moyenne et décentrement unique)

        self._flux_type             = 1  # type de spliting (1 = spliting maison, le reste n'est pas encore implémenté)

        self._number_unknowns       = 4  # nbre d'inconnues du calcul -- Peut rester à 4 car le code Fortran va adapter sur base des autres paramètres
        self._number_equations      = 3  # nbre d'equations à résoudre -- Peut rester à 3 car le code Fortran va adapter sur base des autres paramètres

        self._conflict_resolution   = 0  # gestion des conflits (0), ou juste en centré (1) ou pas (2)
        self._evolutive_domain      = 1  # gestion des éléments couvrants-découvrants ou non
        self._topography_operator   = 1  # type d'agglomération de la topo (1=moy, 2=max, 3=min)

        self._infiltration_mode     = 0  # Infiltration sur base d'hydrogramme ou non, variable ou non...

        # Forcing
        # *******

        self._has_forcing    = 0  # forcing ou pas
        self._mobile_forcing = 0  # Forcing mobile ou non

        # Collapsible buildings
        # *********************

        self._collapsible_building = 0  # Effacement de mailles (bâtiments) dans le bloc ou pas

        # Mobile polygon
        # **************

        self._mobile_polygon = 0  # Contour mobile ou non

        # Ponts/Bridges
        # *************

        self._bridge_activated      = 0  # présence ou non de ponts=

        # Danger maps
        # *********

        self._danger_map_activated    = 0  # carte de risque activée ou non
        self._danger_map_delta_hmin   = 0  # hauteur minimale pour la carte de risque

        # Infiltration
        # *************

        self._infil_type    = 0  # infiltration modifiée (=2) ou non (=1)

        # Sediment infiltration
        self._infil_sed     = 0  # infiltration de débit solide ou non

        # Variable infiltration
        self._infil_a       = 0.  # coefficient a de l'équation de calcul de l'infiltration variable
        self._infil_b       = 0.  # coefficient b de l'équation de calcul de l'infiltration variable
        self._infil_c       = 0.  # coefficient c de l'équation de calcul de l'infiltration variable

        self._infil_zref    = 0.  # hauteur de référence pour infiltration modifiée

        # weir
        self._infil_dev_cd      = 0.  # coefficient de type déversoir de l'infiltration variable --> see Modules_wolf/2D/Wolf2D-DonneesInst.f90
        self._infil_dev_zseuil  = 0.  # hauteur seuil de l'infiltration variable --> see Modules_wolf/2D/Wolf2D-DonneesInst.f90
        self._infil_dev_width   = 0.  # largeur du seuil de l'infiltration variable --> see Modules_wolf/2D/Wolf2D-DonneesInst.f90

        # Cd - polynomial third degree
        self._infil_dev_a = 0.
        self._infil_dev_b = 0.
        self._infil_dev_c = 0.
        self._infil_dev_d = 0.

        # Power law
        self._infil_var_d   = 0. # hauteur minimale de l'infiltration variable --> see Modules_wolf/2D/Wolf2D-DonneesInst.f90
        self._infil_var_e   = 0. # coefficient de l'infiltration variable --> see Modules_wolf/2D/Wolf2D-DonneesInst.f90

        # fixed momentum correction
        self._infil_correction_ux = 0.
        self._infil_correction_vy = 0.

        # Axis inclination
        # ****************

        self._axis_inclination_type = 0  #type d'inclinaison d'axe (0 si pas d'inclinaison)

        # Options
        # *******

        self._egalize_z     = 0  # =1 si égalisation d'altitude
        self._egalize_zref  = 0.  # altitude de surface libre à laquelle égaliser

        self._stop_steady   = 0  # arrêt stationnaire
        self._stop_eps      = 0.  # epsilon à vérifier pour l'arrêt stationnaire

        self._froude_max    = 20.  # froude max pour limitation des résultats

        self._uneven_speed_distribution  = 0  #inégale répartition de vitesse

        # Variable topo-bathymetry
        # ************************

        self._topo_isvariable   = 0  #topo variable ou non

        # Turbulence
        # **********

        self._turbulence_type   = 0  #type de modèle de turbulence (1 = prandtl, ...)

        # paramètres du modèle de turbulence --> see Wolf2D-Preprocessing.f90
        self._nu_water      = 0.    # vdebug_bloc(3) --> paramétrabmle
        self._turb_cnu      = 0.    # vdebug_bloc(2) --> paramétrabmle
        self._turb_max_nut  = 0.    # vdebug_bloc(32) --> viscosité turbulente max paramétrable
        self._turb_c3e      = 0.8   # vdebug_bloc(46) --> coefficient c3e du modèle k-eps (HECE)
        self._turb_clk      = 1.e-4 # vdebug_bloc(47) --> coefficient clk du modèle k-eps (HECE)
        self._turb_cle      = 10.   # vdebug_bloc(48) --> coefficient cle du modèle k-eps (HECE)

        # paramètres du modèle k-eps : cmu, c1e, c2e, sigmak, sigmae, vminediv, vminkdiv
        # paremètres du modèle k     : cd1, cd2, cmu, cnu, sigmak, vminkdiv, vnu_eau, vmaxvnut
        # paremètres du modèle k-eps (HECE) : cmu, cnu, c1e, c2e, c3e, clk, sigmak, sigmae, vminediv, vminkdiv, vnu_eau, vmaxvnut

        self._turb_cmu            = 0.09  # constante du modèle k-e
        self._turb_c1e            = 1.44  # )
        self._turb_c2e            = 1.92  # )
        self._turb_cd1            = 0.55  # )
        self._turb_cd2            = self._turb_cd1**3.   # )
        self._turb_sigmak         = 1.  # )
        self._turb_sigmae         = 1.3  # )
        self._turb_cdk            = 0.  # paramètre du modèle k pour la turbulence
        self._turb_minediv       = 1.e-10  # valeur min de e pour la division
        self._turb_minkdiv       = 1.e-10  # valeur min de k pour la division

        # paramètres de turbulence VAM5
        self._vam5_nu_vertical      = 0.# viscosité verticale pour VAM5
        self._vam5_turbulence_model = 0 # modèle de turbulence pour VAM5

        # Sediment
        # ********

        self._sed_model    = 0  #type de modèle sédimentaire (1 = charriage, 2 = charriage + suspension)

        self._sed_porosity      = 0.  # Porosité
        self._sed_d_mean        = 0.  # diamètre moyen
        self._sed_s             = 0.  # Densité relative des sédiments
        self._sed_thetacr       = 0.  # Tension adimensionnelle critique pour la mise en mouvement
        self._sed_drifting_mode = 0  # Type de loi de transport par charriage
        self._sed_eps_stabbed   = 0. # Epsilon pour l'arrêt stationnaire sur base de la variation de la topo de fond
        self._sed_eps_h         = 0. # Epsilon sur h pour recalculer le fond

        self._sed_gravity_discharge = 0  #
        self._sed_gamma_critic   = 0.  # pente critique
        self._sed_gamma_natural  = 0.  # pente naturelle

        self._sed_reduced_slope  = 0.  # )
        self._sed_d30            = 0.  # )
        self._sed_d90            = 0.  # )

        # Topo variable
        self._topo_inst     = 0  # topo variable dans le temps

        # Steady equilibrium
        self._write_topo = 0  # écriture de la topo ou pas
        self._hmin_compute_equilibrium = 0  # calcul de la hauteur minimale pour l'équilibre sédimentaire

        # Friction
        # ********

        # Friction evaluation
        self._friction_law = 0  # Loi et Type de calcul de la surface mouillée (0 = classique, 1 = surface mouillée réelle)

        self._friction_implicit         = 1.  # frottement implicite (1) ou pas (0)
        self._friction_implicit_coeff   = 0.  # coeff du pondération du frotement implicite

        # Bathurst coefficient
        self._bathurst_coeff  = 0.  # coefficient de la loi de Bathurst FIXME : used??

        # Lateral friction
        self._lateral_manning = 0.  # Coefficient de Manning latéral

        # Paramètres fluide Bingham
        self._bingham_rho           = 0.  # masse volumique du mélange (modèle de Bingham)

        # Paramètres fluide frictionnel
        self._frictional_hs         = 0.  # hauteur de la couche de sol saturé
        self._frictional_cv         = 0.  # coefficient de consolidation
        self._frictional_ru0        = 0.  # valeur initiale du coefficient de pression interstitielle à la base = ru0

        # Stockage dans une liste des valeurs par défaut
        self._default_gen_par   = self._get_general_params()
        self._default_debug_par = self._get_debug_params()

        # création d'un objet wolf_param
        self._params = None

        self._set_block_params(toShow=False)

    def _set_general_debug_params(self, gen:list, debug:list):
        """ Définit les paramètres généraux et de debug """

        self._set_general_params(gen)
        self._set_debug_params(debug)

        self._set_block_params(toShow=False, force=True)

    @property
    def filegen(self) -> str:
        return self.parent.parent.filenamegen

    @property
    def has_turbulence(self):
        return self._turbulence_type != 0

    @property
    def has_variable_infiltration(self):
        return self._infiltration_mode < 0

    @property
    def has_infiltration(self):
        return self._infiltration_mode > 0 or self._infiltration_mode < 0

    @property
    def has_unknown_topo(self):
        return self._topo_isvariable != 0

    @property
    def has_modified_surface_friction(self):
        return self._friction_law in [2, 3, 5, 6, 7]

    @property
    def has_lateral_friction(self):
        return self._friction_law in [1,4,-34,-44,3,5,7]

    @property
    def has_danger_map(self):
        return self._danger_map_activated != 0

    @property
    def has_bridge(self):
        return self._bridge_activated != 0

    @property
    def has_mobile_forcing(self):
        return self._mobile_forcing != 0

    @property
    def has_pressure_fluxes(self):
        return self._flux_type in [8, 9]

    @property
    def has_unsteady_topo(self):
        return self._topo_inst != 0

    @property
    def has_sediment_model(self):
        return self._sed_model != 0

    @property
    def has_gravity_discharge(self):
        return self._sed_gravity_discharge != 0

    # General parameters
    # *******************

    def set_params_topography_operator(self, op:Literal['Mean', 'Max', 'Min', 1, 2, 3] = 'Mean'):
        """ Définit le type d'opérateur topographique """

        if isinstance(op, str):
            if op.lower() in ['mean', 'average']:
                self._topography_operator = 1
            elif op.lower() in ['max', 'maximum']:
                self._topography_operator = 2
            elif op.lower() in ['min', 'minimum']:
                self._topography_operator = 3
            else:
                logging.error(f"Unknown topography operator {op} -- Set Mean by default")
                self._topography_operator = 1
        else:
            if op in [1, 2, 3]:
                self._topography_operator = op
            else:
                logging.error(f"Unknown topography operator {op} -- Set Mean by default")
                self._topography_operator = 1

    def get_params_topography_operator(self) -> tuple[int,str]:
        """ Retourne le type d'opérateur topographique """

        if self._topography_operator == 1:
            return self._topography_operator, _('Mean')

        elif self._topography_operator == 2:
            return self._topography_operator, _('Maximum')

        elif self._topography_operator == 3:
            return self._topography_operator, _('Minimum')

        else:
            return self._topography_operator, _('Unknown')

    def check_params_topography_operator(self) -> tuple[bool, str]:
        """ Check topography operator """

        ret = "\nTopography operator\n*******************\n"
        valid = True

        if self._topography_operator == 1:
            ret += _("Info : Mean operator\n")
        elif self._topography_operator == 2:
            ret += _("Info : Maximum operator\n")
        elif self._topography_operator == 3:
            ret += _("Info : Minimum operator\n")
        else:
            ret += _("Error : Unknown topography operator\n")
            valid = False

        return valid, ret

    def reset_params_topography_operator(self):
        """ Réinitialise l'opérateur topographique à Mean """

        self._topography_operator = 1



    def set_params_reconstruction_type(self,
                                       reconstruction_intern:Literal['constant rec', 'linear rec', 0, 1] = 0,
                                       reconstruction_frontier:Literal['constant rec', 'linear limited', 'linear not limited', 0,2,1] = 2,
                                       reconstruction_free:Literal['constant rec', 'linear limited', 'linear not limited', 0,2,1] = 0,
                                       limiter_variable:Literal['h', '(h+z)', 0,1] = 0,
                                       frontier_treatment:Literal['Nothing', 'Average', 1, 0] = 1,
                                       number_neighbors_in_limiting_phase:int = 5
                                       ):
        """
        Définit le type de reconstruction pour différents types de bords

        :param reconstruction_intern: Reconstruction interne
        :param reconstruction_frontier: Reconstruction des bords frontière
        :param reconstruction_free: Reconstruction des bords libres
        :param limiter_variable: Limiter la hauteur 'h' ou ou la surface libre 'h+z'
        :param frontier_treatment: Traitement des frontières
        :param number_neighbors_in_limiting_phase: Nombre de voisins pour la limitation

        """

        if isinstance(reconstruction_intern, str):
            if reconstruction_intern.lower() in ['constant rec', 'constant reconstruction', 'constant']:
                self._reconstruction_internal = 0
            elif reconstruction_intern.lower() in ['linear rec', 'linear reconstruction', 'linear']:
                self._reconstruction_internal = 1
            else:
                logging.error(f"Unknown internal reconstruction type {reconstruction_intern} -- Set constant by default")
                self._reconstruction_internal = 0
        else:
            if reconstruction_intern in [0, 1]:
                self._reconstruction_internal = reconstruction_intern
            else:
                logging.error(f"Unknown internal reconstruction type {reconstruction_intern} -- Set constant by default")
                self._reconstruction_internal = 0

        if isinstance(reconstruction_frontier, str):
            if reconstruction_frontier.lower() in ['constant rec', 'constant reconstruction', 'constant']:
                self._reconstruction_frontier = 0
            elif reconstruction_frontier.lower() in ['linear limited', 'linear reconstruction', 'linear']:
                self._reconstruction_frontier = 2
            elif reconstruction_frontier.lower() in ['linear not limited', 'linear not limited reconstruction']:
                self._reconstruction_frontier = 1
            else:
                logging.error(f"Unknown frontier reconstruction type {reconstruction_frontier} -- Set linear limited by default")
                self._reconstruction_frontier = 2
        else:
            if reconstruction_frontier in [0, 1, 2]:
                self._reconstruction_frontier = reconstruction_frontier
            else:
                logging.error(f"Unknown frontier reconstruction type {reconstruction_frontier} -- Set linear limited by default")
                self._reconstruction_frontier = 2

        if isinstance(reconstruction_free, str):
            if reconstruction_free.lower() in ['constant rec', 'constant reconstruction', 'constant']:
                self._reconstruction_free_border = 0
            elif reconstruction_free.lower() in ['linear limited', 'linear reconstruction', 'linear']:
                self._reconstruction_free_border = 2
            elif reconstruction_free.lower() in ['linear not limited', 'linear not limited reconstruction']:
                self._reconstruction_free_border = 1
            else:
                logging.error(f"Unknown free border reconstruction type {reconstruction_free} -- Set constant by default")
                self._reconstruction_free_border = 0
        else:
            if reconstruction_free in [0, 1, 2]:
                self._reconstruction_free_border = reconstruction_free
            else:
                logging.error(f"Unknown free border reconstruction type {reconstruction_free} -- Set constant by default")
                self._reconstruction_free_border = 0

        if isinstance(limiter_variable, str):
            if limiter_variable.lower() in ['h']:
                self._limiting_h_or_Z = 0
            elif limiter_variable.lower() in ['(h+z)', 'h+z']:
                self._limiting_h_or_Z = 1
            else:
                logging.error(f"Unknown limiting h or h+z type {limiter_variable} -- Set h by default")
                self._limiting_h_or_Z = 0
        else:
            if limiter_variable in [0, 1]:
                self._limiting_h_or_Z = limiter_variable
            else:
                logging.error(f"Unknown limiting h or h+z type {limiter_variable} -- Set h by default")
                self._limiting_h_or_Z = 0

        if isinstance(frontier_treatment, str):
            if frontier_treatment.lower() in ['nothing']:
                self._treating_frontier = 1
            elif frontier_treatment.lower() in ['average']:
                self._treating_frontier = 0
            else:
                logging.error(f"Unknown treating frontier type {frontier_treatment} -- Set nothing by default")
                self._treating_frontier = 1
        else:
            if frontier_treatment in [0, 1]:
                self._treating_frontier = frontier_treatment
            else:
                logging.error(f"Unknown treating frontier type {frontier_treatment} -- Set nothing by default")
                self._treating_frontier = 1

        if isinstance(number_neighbors_in_limiting_phase, int):
            if number_neighbors_in_limiting_phase in [5,9]:
                self._limiting_neighbors = number_neighbors_in_limiting_phase
            else:
                logging.error(f"Unknown limiting neighbors {number_neighbors_in_limiting_phase} -- Set 5 by default")
                self._limiting_neighbors = 5
        else:
            logging.error(f"Unknown limiting neighbors {number_neighbors_in_limiting_phase} -- Set 5 by default")
            self._limiting_neighbors = 5

    def get_params_reconstruction_type(self) -> dict:
        """ Retourne le type de reconstruction """

        ret = {}

        if self._reconstruction_internal == 0:
            ret[_('Internal'): _('Constant reconstruction')]
        elif self._reconstruction_internal == 1:
            ret[_('Internal'): _('Linear reconstruction')]
        else:
            ret[_('Internal'): _('Unknown')]

        if self._reconstruction_frontier == 0:
            ret[_('Frontier'): _('Constant reconstruction')]
        elif self._reconstruction_frontier == 1:
            ret[_('Frontier'): _('Linear reconstruction without limitation')]
        elif self._reconstruction_frontier == 2:
            ret[_('Frontier'): _('Linear reconstruction with limitation')]
        else:
            ret[_('Frontier'): _('Unknown')]

        if self._reconstruction_free_border == 0:
            ret[_('Free border'): _('Constant reconstruction')]
        elif self._reconstruction_free_border == 1:
            ret[_('Free border'): _('Linear reconstruction without limitation')]
        elif self._reconstruction_free_border == 2:
            ret[_('Free border'): _('Linear reconstruction with limitation')]
        else:
            ret[_('Free border'): _('Unknown')]

        ret[_('Number of neighbors for limitation')] = self._limiting_neighbors
        ret[_('Limitation of h or h+z')]             = _('h+z') if self._limiting_h_or_Z == 1 else _('h')
        ret[_('Treatment of frontiers')]             = _('Nothing') if self._treating_frontier == 1 else _('Average and unique shift')

        return ret

    def reset_params_reconstruction_type(self):
        """ Réinitialise le type de reconstruction """

        self._reconstruction_internal = 0
        self._reconstruction_frontier = 2
        self._reconstruction_free_border = 0
        self._limiting_neighbors = 5
        self._limiting_h_or_Z = 0
        self._treating_frontier = 1

    def check_params_reconstruction_type(self) -> tuple[bool, str]:
        """ Check reconstruction type """

        ret = "\nReconstruction type\n********************\n"
        valid = True

        if self._reconstruction_internal == 0:
            ret += _("Info : Internal reconstruction is constant\n")
        elif self._reconstruction_internal == 1:
            ret += _("Info : Internal reconstruction is linear\n")
        else:
            ret += _("Error : Unknown internal reconstruction type\n")
            valid = False

        if self._reconstruction_frontier == 0:
            ret += _("Info : Frontier reconstruction is constant\n")
        elif self._reconstruction_frontier == 1:
            ret += _("Info : Frontier reconstruction is linear without limitation\n")
        elif self._reconstruction_frontier == 2:
            ret += _("Info : Frontier reconstruction is linear with limitation\n")
        else:
            ret += _("Error : Unknown frontier reconstruction type\n")
            valid = False

        if self._reconstruction_free_border == 0:
            ret += _("Info : Free border reconstruction is constant\n")
        elif self._reconstruction_free_border == 1:
            ret += _("Info : Free border reconstruction is linear without limitation\n")
        elif self._reconstruction_free_border == 2:
            ret += _("Info : Free border reconstruction is linear with limitation\n")
        else:
            ret += _("Error : Unknown free border reconstruction type\n")
            valid = False

        if self._limiting_neighbors in [5, 9]:
            ret += _("Info : Number of neighbors for limitation is correct\n")
        else:
            ret += _("Error : Number of neighbors for limitation is incorrect\n")
            valid = False

        if self._limiting_h_or_Z in [0, 1]:
            ret += _("Info : Limitation of h or h+z is correct\n")
        else:
            ret += _("Error : Limitation of h or h+z is incorrect\n")
            valid = False

        if self._treating_frontier in [0, 1]:
            ret += _("Info : Treatment of frontiers is correct\n")
        else:
            ret += _("Error : Treatment of frontiers is incorrect\n")
            valid = False

        return valid, ret



    def set_params_flux_type(self, flux_type:Literal['HECE original', 'VAM-5', 'VAM-5 with vertical velocites', 'VAM-5 with vertical velocites and solid transport',
                                                     'HECE in terms of h, u, v', 'HECE in terms of Volume, qx, qy', 'HECE with H "energy formulation" in slope term',
                                                     'HECE under pressure (H)', 'HECE under pressure (Volume instead of H)',1,2,3,4,5,6,7,8,9]):

        if isinstance(flux_type, str):
            if flux_type.lower() in ['hece original', 'hece']:
                self._flux_type = 1
            elif flux_type.lower() in ['vam-5', 'vam5']:
                self._flux_type = 2
            elif flux_type.lower() in ['vam-5 with vertical velocites', 'vam5 with vertical velocities']:
                self._flux_type = 3
            elif flux_type.lower() in ['vam-5 with vertical velocites and solid transport', 'vam5 with vertical velocities and solid transport']:
                self._flux_type = 4
            elif flux_type.lower() in ['hece in terms of h, u, v']:
                self._flux_type = 5
            elif flux_type.lower() in ['hece in terms of volume, qx, qy']:
                self._flux_type = 6
            elif flux_type.lower() in ['hece with h "energy formulation" in slope term']:
                self._flux_type = 7
            elif flux_type.lower() in ['hece under pressure (h)']:
                self._flux_type = 8
            elif flux_type.lower() in ['hece under pressure (volume instead of h)']:
                self._flux_type = 9
            else:
                logging.error(f"Unknown flux type {flux_type} -- Set HECE original by default")
                self._flux_type = 1
        else:
            if flux_type in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                self._flux_type = flux_type
            else:
                logging.error(f"Unknown flux type {flux_type} -- Set HECE original by default")
                self._flux_type = 1

    def get_params_flux_type(self) -> tuple[int, str]:
        """
        Retourne le type de flux

        See : ntypflux in Modules_wolf/2D/Wolf2D-Preprocessing.f90

        """

        if self._flux_type == 1:
            return 1, _('HECE original')
        elif self._flux_type == 2:
            return 2, _('VAM-5')
        elif self._flux_type == 3:
            return 3, _('VAM-5 with vertical velocites')
        elif self._flux_type == 4:
            return 4, _('VAM-5 with vertical velocites and solid transport')
        elif self._flux_type == 5:
            return 5, _('HECE in terms of h, u, v')
        elif self._flux_type == 6:
            return 6, _('HECE in terms of Volume, qx, qy')
        elif self._flux_type == 7:
            return 7, _('HECE with H "energy formulation" in slope term')
        elif self._flux_type == 8:
            return 8, _('HECE under pressure (H)')
        elif self._flux_type == 9:
            return 9, _('HECE under pressure (Volume instead of H)')
        else:
            return 99999, _('Unknown')

    def reset_params_flux_type(self):
        """ Réinitialise le type de flux """

        self._flux_type = 1

    def check_params_flux_type(self) -> tuple[bool, str]:
        """ Check flux type """

        ret = "\nFlux type\n**********\n"
        valid = True

        if self._flux_type == 1:
            ret += _("Info : HECE original\n")
        elif self._flux_type == 2:
            ret += _("Info : VAM-5\n")
        elif self._flux_type == 3:
            ret += _("Info : VAM-5 with vertical velocities\n")
        elif self._flux_type == 4:
            ret += _("Info : VAM-5 with vertical velocities and solid transport\n")
        elif self._flux_type == 5:
            ret += _("Info : HECE in terms of h, u, v\n")
        elif self._flux_type == 6:
            ret += _("Info : HECE in terms of Volume, qx, qy\n")
        elif self._flux_type == 7:
            ret += _("Info : HECE with H 'energy formulation' in slope term\n")
        elif self._flux_type == 8:
            ret += _("Info : HECE under pressure (H)\n")
        elif self._flux_type == 9:
            ret += _("Info : HECE under pressure (Volume instead of H)\n")
        else:
            ret += _("Error : Unknown value for flux type\n")
            valid = False

        return valid, ret


    def set_params_froud_max(self, froude_max:float):
        """
        Définit le Froude maximum

        Si, localement, le Froude maximum est dépassé, le code limitera
        les inconnues de débit spécifique à la valeur du Froude maximum
        en conservant inchangée la hauteur d'eau.

        Valeur par défaut : 20.

        """

        if isinstance(froude_max, (int, float)):
            self._froude_max = float(froude_max)
        else:
            logging.error(f"Unknown Froude max {froude_max} -- Set 20. by default")
            self._froude_max = 20.

    def get_params_froud_max(self) -> float:
        """ Retourne le Froude max """

        return self._froude_max

    def reset_params_froud_max(self):
        """ Réinitialise le Froude max """

        self._froude_max = 20.

    def check_params_froud_max(self) -> tuple[bool, str]:
        """ Check Froude max """

        ret = "\nFroude max\n**********\n"
        valid = True

        if self._froude_max > 0.:
            ret += f"Info : Froude max is {self._froude_max}\n"
        else:
            ret += f"Error : Froude max is incorrect\n"
            valid = False

        if self._froude_max > 3.:
            ret += f"Warning : Froude max is high -- Is it useful ?\n"

        return valid, ret


    def set_params_conflict_resolution(self, mode:Literal['Original', 'Centered', 'Nothing', 0, 1, 2]):
        """ Définit la résolution des conflits """

        if isinstance(mode, str):
            mode = mode.lower()

        assert mode in ['original', 'centered', 'nothing', 0, 1, 2], f"Unknown conflict resolution {mode}"

        if mode in ['original', 0]:
            self._conflict_resolution = 0
        elif mode in ['centered', 1]:
            self._conflict_resolution = 1
        elif mode in ['nothing', 2]:
            self._conflict_resolution = 2

    def get_params_conflict_resolution(self) -> tuple[int, str]:
        """ Retourne la résolution des conflits """

        if self._conflict_resolution == 0:
            return self._conflict_resolution, _('Original')
        elif self._conflict_resolution == 1:
            return self._conflict_resolution, _('Centered')
        elif self._conflict_resolution == 2:
            return self._conflict_resolution, _('Nothing')
        else:
            return 99999, _('Unknown')

    def reset_params_conflict_resolution(self):
        """ Réinitialise la résolution des conflits """

        self._conflict_resolution = 0

    def check_params_conflict_resolution(self) -> tuple[bool, str]:
        """ Check conflict resolution """

        ret = "\nConflict resolution\n********************\n"
        valid = True

        if self._conflict_resolution == 0:
            ret += _("Info : Original conflict resolution\n")
        elif self._conflict_resolution == 1:
            ret += _("Info : Centered conflict resolution\n")
        elif self._conflict_resolution == 2:
            ret += _("Info : No conflict resolution\n")
        else:
            ret += _("Error : Unknown conflict resolution\n")
            valid = False

        return valid, ret


    def set_evolutive_domain(self, evolutive_domain:Literal['No', 'Yes', 0, 1]):
        """ Définit le domaine évolutif """

        if isinstance(evolutive_domain, str):
            evolutive_domain = evolutive_domain.lower()

        assert evolutive_domain in ['no', 'yes', 0, 1], f"Unknown evolutive domain {evolutive_domain}"

        self._evolutive_domain = evolutive_domain

    def reset_evolutive_domain(self):
        """ Réinitialise le domaine évolutif -- Domaine fixe """

        self._evolutive_domain = 0

    # Sediment
    # ********

    def set_params_sediment(self,
                           model:Literal['No sediment model', 'Drifting', 'Drifting and suspension', 0, 1, 2] = 'No sediment model',
                           drifting_model:Literal['No drifting', 'Meyer-Peter-Muller', 'Rickemann', 0, 1, 2] = 'No drifting',
                           porosity:float = 0.,
                           d_mean:float = 0.,
                           s_sedim:float = 2.65,
                           vthetacr:float = 0.,
                           reduced_slope:float = 0.,
                           d30:float = 0,
                           d90:float = 0.,
                           ):
        """
        Définit le modèle sédimentaire

        :param model: Modèle sédimentaire
        :param drifting_model: Modèle de transport par charriage
        :param porosity: Porosité
        :param d_mean: Diamètre moyen
        :param s_sedim: Densité relative des sédiments
        :param vthetacr: Tension adimensionnelle critique pour la mise en mouvement
        :param reduced_slope: Pente réduite
        :param d30: D30
        :param d90: D90

        """

        if isinstance(model, str):
            if model.lower() in ['no sediment model', 'no sediment', 'no', 'none']:
                self._sed_model = 0
            elif model.lower() in ['drifting']:
                self._sed_model = 1
            elif model.lower() in ['drifting and suspension']:
                self._sed_model = 2
            else:
                logging.error(f"Unknown sediment model {model} -- Set No sediment model by default")
                self._sed_model = 0
        else:
            if model in [0, 1, 2]:
                self._sed_model = model
            else:
                logging.error(f"Unknown sediment model {model} -- Set No sediment model by default")
                self._sed_model = 0


        if isinstance(drifting_model, str):
            if drifting_model.lower() in ['no drifting', 'no']:
                self._sed_drifting_mode = 0
            elif drifting_model.lower() in ['meyer-peter-muller', 'meyer-peter', 'meyer', 'muller']:
                self._sed_drifting_mode = 1
            elif drifting_model.lower() in ['rickemann']:
                self._sed_drifting_mode = 2
            else:
                if self._sed_model == 0:
                    logging.error(f"Unknown drifting model {drifting_model} -- Set No drifting by default")
                    self._sed_drifting_mode = 0
                else:
                    logging.error(f"Unknown drifting model {drifting_model} -- Set Meyer-Peter-Muller by default")
                    self._sed_drifting_mode = 1
        else:
            if drifting_model in [0, 1, 2]:
                self._sed_drifting_mode = drifting_model
            else:
                if self._sed_model == 0:
                    logging.error(f"Unknown drifting model {drifting_model} -- Set No drifting by default")
                    self._sed_drifting_mode = 0
                else:
                    logging.error(f"Unknown drifting model {drifting_model} -- Set Meyer-Peter-Muller by default")
                    self._sed_drifting_mode = 1

        self._sed_porosity = porosity
        self._sed_d_mean = d_mean
        self._sed_s = s_sedim
        self._sed_thetacr = vthetacr

        self._sed_reduced_slope = reduced_slope
        self._sed_d30 = d30
        self._sed_d90 = d90

        if self._sed_drifting_mode == 1:
            # Meyer-Peter et Müller
            if self._sed_reduced_slope <=0. :
                self._sed_reduced_slope = 1.
        elif self._sed_drifting_mode == 2:
            # Rickemann
            if self._sed_reduced_slope <1. or self._sed_reduced_slope > 2.:
                self._sed_reduced_slope = 1.3

            # test sur d30 et d90
            # if D30 > 0. and D90 > 0.:
            #     facteur_cst1 = D90 / D30
            # else:
            #     D90 = D_MOYEN
            #     facteur_cst1 = 1.

    def _get_params_sediment_model(self)-> tuple[int,str]:
        """ Retourne le modèle sédimentaire """

        if self._sed_model == 0:
            return self._sed_model, _("No sediment model")
        elif self._sed_model == 1:
            return self._sed_model, _("Drifting")
        elif self._sed_model == 2:
            return self._sed_model, _("Drifting and suspension")
        else:
            return 99999, _("Unknown")

    def _get_params_sediment_drifting_model(self) -> tuple[int,str]:
        """ Retourne le modèle de dérive """

        if self._sed_drifting_mode == 0:
            return self._sed_drifting_mode, _("No drifting")
        elif self._sed_drifting_mode == 1:
            return self._sed_drifting_mode, _("Meyer-Peter-Muller")
        elif self._sed_drifting_mode == 2:
            return self._sed_drifting_mode, _("Rickenmann")
        else:
            return 99999, _("Unknown")

    def get_params_sediment(self) -> dict:
        """ Retourne les paramètres du modèle sédimentaire """

        return {_('Model'): self._get_params_sediment_model(),
                _('Drifting model'): self._get_params_sediment_drifting_model(),
                _('Porosity'): self._sed_porosity,
                _('Mean diameter'): self._sed_d_mean,
                _('Sediment density'): self._sed_s,
                _('Critical adimensional tension'): self._sed_thetacr,
                _('Reduced slope'): self._sed_reduced_slope,
                _('D30'): self._sed_d30,
                _('D90'): self._sed_d90}

    def reset_params_sediment(self):
        """ Désactive le modèle sédimentaire """

        self._sed_model = 0
        self._sed_drifting_mode = 0
        self._sed_porosity = 0.
        self._sed_d_mean = 0.
        self._sed_s = 0.
        self._sed_thetacr = 0.

        self._sed_reduced_slope = 0.
        self._sed_d30 = 0.
        self._sed_d90 = 0.

    def check_params_sediment(self) -> tuple[bool, str]:
        """ Check sediment model """

        ret = "\nSediment model\n**************\n"
        valid = True

        if self._sed_model == 0:
            ret += _("Info : Sediment model not activated\n")
        elif self._sed_model == 1:
            ret += _("Info : Drifting activated\n")
        elif self._sed_model == 2:
            ret += _("Info : Drifting and suspension activated\n")
        else:
            ret += _("Error : Unknown value for sediment model\n")
            valid = False

        if self._sed_drifting_mode == 0:
            ret += _("Info : No drifting\n")
        elif self._sed_drifting_mode == 1:
            ret += _("Info : Meyer-Peter-Muller\n")
        elif self._sed_drifting_mode == 2:
            ret += _("Info : Rickemann\n")
        else:
            ret += _("Error : Unknown value for drifting model\n")
            valid = False

        if self._sed_model !=0:
            if self._sed_porosity == 0.:
                ret += _("Error : Porosity not defined\n")
                valid = False

            if self._sed_d_mean == 0.:
                ret += _("Error : Mean diameter not defined\n")
                valid = False

            if self._sed_s == 0.:
                ret += _("Error : Sediment density not defined\n")
                valid = False

            if self._sed_thetacr == 0.:
                ret += _("Error : Critical adimensional tension not defined\n")
                valid = False

        return valid, ret



    def set_params_gravity_discharge(self,
                                     activated:bool,
                                     critical_slope:float,
                                     natural_slope:float):
        """
        Définit si le modèle de décharge solide gravitaire est activé

        :param activated: booléen indiquant si le modèle de décharge solide gravitaire doit être activé
        :param critical_slope: Pente critique
        :param natural_slope: Pente naturelle

        """

        assert isinstance(activated, bool), "activated must be a boolean"

        self._sed_gravity_discharge = 1 if activated else 0

        self._sed_gamma_critic = critical_slope
        self._sed_gamma_natural  = natural_slope

    def reset_params_gravity_discharge(self):
        """ Désactive le modèle de décharge solide gravitaire """

        self._sed_gravity_discharge = 0
        self._sed_gamma_critic = 0.
        self._sed_gamma_natural = 0.

    def get_params_gravity_discharge(self) -> dict:
        """ Retourne les paramètres du modèle de décharge solide gravitaire """

        if self._sed_gravity_discharge == 1:
            return {_('Activated'): _('Yes'),
                    _('Critical slope'): self._sed_gamma_critic,
                    _('Natural slope'): self._sed_gamma_natural}
        else:
            return {_('Activated'): _('No')}

    def check_params_gravity_discharge(self) -> tuple[bool, str]:
        """ Check gravity discharge """

        ret = "\nGravity discharge\n*****************\n"
        valid = True

        if self._sed_gravity_discharge == 1:
            ret += _("Info : Gravity discharge activated\n")
        elif self._sed_gravity_discharge == 0:
            ret += _("Info : Gravity discharge not activated\n")
        else:
            ret += _("Error : Unknown value for gravity discharge\n")
            valid = False

        if self._sed_gravity_discharge == 1:
            if self._sed_gamma_critic == 0.:
                ret += _("Error : Critical slope not defined\n")
                valid = False

            if self._sed_gamma_natural == 0.:
                ret += _("Error : Natural slope not defined\n")
                valid = False

        return valid, ret



    def set_params_steady_sediment(self,
                                   porosity:float,
                                   d_mean:float,
                                   s_sedim:float = 2.65,
                                   vthetacr:float = 0.,
                                   drifting_mode:Literal['Meyer-Peter-Muller', 'Rickemann', 1, 2] = 'Meyer-Peter-Muller',
                                   epssedim:float = 1.e-10,
                                   epsstabbed:float = 1.e-10,
                                   reduced_slope:float = 1.):
        """
        Définit les paramètres du modèle sédimentaire

        Loi de Meyer-Peter et Müller pour le charriage :
            - $ Q = C * sqrt{s * g * d^3} * (s - Rcr)^{3/2} $
            - $ s = rho_sedim / rho_eau $
            - $ Rcr = vthetacr $
            - $ d = d_moyen $

        :param porosity: Porosité
        :param d_moyen: Diamètre moyen
        :param s_sedim: Densité relative des sédiments
        :param vthetacr: Tension adimensionnelle critique pour la mise en mouvement
        :param ntype_charriage: Type de loi de transport par charriage
        :param epssedim: Epsilon sur h pour recalculer le fond
        :param epsstabfond: Epsilon pour l'arrêt stationnaire sur base de la variation de la topo de fond
        :param pente_reduite: Pente réduite -- si <= 0, forcé à 1 càd "sans bedforms"

        """

        self._sed_porosity = porosity
        self._sed_d_mean = d_mean
        self._sed_s = s_sedim
        self._sed_thetacr = vthetacr
        self._sed_drifting_mode = drifting_mode

        self._topo_isvariable = 1

        self._sed_eps_stabbed = epsstabbed
        self._sed_eps_h = epssedim

        self._sed_reduced_slope = reduced_slope

        if isinstance(drifting_mode, str):
            if drifting_mode.lower() in ['meyer-peter-muller', 'meyer-peter', 'meyer', 'muller']:
                self._sed_drifting_mode = 1
            elif drifting_mode.lower() in ['rickemann']:
                self._sed_drifting_mode = 2
            else:
                logging.error(f"Unknown drifting model {drifting_mode} -- Set Meyer-Peter-Muller by default")
                self._sed_drifting_mode = 1
        else:
            if drifting_mode in [1, 2]:
                self._sed_drifting_mode = drifting_mode
            else:
                logging.error(f"Unknown drifting model {drifting_mode} -- Set Meyer-Peter-Muller by default")
                self._sed_drifting_mode = 1

        if self._sed_drifting_mode == 1:
            # Meyer-Peter et Müller
            if self._sed_reduced_slope <=0. :
                self._sed_reduced_slope = 1.

        elif self._sed_drifting_mode == 2:
            # Rickemann
            if self._sed_reduced_slope <1. or self._sed_reduced_slope > 2.:
                self._sed_reduced_slope = 1.3

    def get_params_steady_sediment(self) -> dict:
        """ Retourne les paramètres du modèle sédimentaire """

        if self._topo_isvariable == 1:
            return {'Porosity': self._sed_porosity,
                    'Diameter': self._sed_d_mean,
                    'Sediment density': self._sed_s,
                    'Critical adimensional tension': self._sed_thetacr,
                    'Transport law (drifting)': self._get_params_sediment_drifting_model(),
                    'Epsilon on h': self._sed_eps_h,
                    'Epsilon on bed': self._sed_eps_stabbed,
                    'Reduced slope': self._sed_reduced_slope}
        else:
            return {}

    def reset_params_steady_sediment(self):
        """ Réinitialise les paramètres du modèle sédimentaire """

        self._sed_porosity = 0.
        self._sed_d_mean = 0.
        self._sed_s = 0.
        self._sed_thetacr = 0.
        self._sed_drifting_mode = 0
        self._sed_eps_h = 0.
        self._sed_eps_stabbed = 0.
        self._sed_reduced_slope = 0.

        self._topo_isvariable = 0

    def check_params_steady_sediment(self) -> tuple[bool, str]:
        """ Check steady sediment """

        ret = "\nSteady sediment\n****************\n"
        ret += _('Info : Not yet implemented -- Feel free to complete the code -- check_params_steady_sediment\n')

        return True, ret

    # Unsteady topo bathymetry
    # ************************

    def set_params_unsteady_topo_bathymetry(self, activated:bool, model:int):
        """
        Définit si la topo est variable ou non

        - sur base d'une succession de matrices de topo
        - sur base d'une triangulation dynamique

        see : Modules_wolf/2D/Wolf2D-DonneesInst.f90 "!GESTION DE LA TOPO INSTATIONNAIRE" for more information

        """

        assert isinstance(activated, bool), "activated must be a boolean"

        self._topo_inst = model if activated else 0

        if activated:

            if abs(self._topo_inst) == 3:
                file_topipar = Path(self.filegen) / '.topipar'

                if file_topipar.exists():
                    logging.info(_("File .topipar found\n"))
                else:
                    logging.error(_("File .topipar not found\n"))
            else:
                logging.warning(_('Info : Please check if all required files are present in the simulation directory\n'))

    def get_params_unsteady_topo_bathymetry(self) -> dict:
        """
        Retourne les paramètres de la topo variable

        Les paramètres sont globaux, pas spécifiques à un bloc --> voir les paramètres globaux associés

        """

        if self._topo_inst == 0:
            return {_('Unsteady topo'): self._topo_inst}
        else:
            return {_('Unsteady topo'): self._topo_inst}

    def reset_params_unsteady_topo_bathymetry(self):
        """ Désactive la topo variable """

        self._topo_inst = 0

    def check_params_unsteady_topo_bathymetry(self) -> tuple[bool, str]:
        """ Check unsteady topo """

        ret = "\nUnsteady topo_bathymetry\n***********************\n"
        valid = True

        if self._topo_inst == 0:
            ret += _("Info : Unsteady topo not activated\n")
        else:
            ret += _("Info : Unsteady topo activated\n")

            if abs(self._topo_inst) == 3:
                file_topipar = Path(self.filegen) / '.topipar'

                if file_topipar.exists():
                    ret += _("Info : File .topipar found\n")
                else:
                    ret += _("Error : File .topipar not found\n")
                    valid = False
            else:
                ret += _('Info : Please check if all required files are present in the simulation directory\n')

        return valid, ret


    # Buildings
    # *********

    def set_params_collapse_building(self, activated:bool):
        """ Définit si les bâtiments sont effacés ou non """

        assert isinstance(activated, bool), "activated must be a boolean"

        self._collapsible_building = 1 if activated else 0

    def get_params_collapse_building(self) -> dict:
        """
        Retourne les paramètres de l'effacement des bâtiments

        Les paramètres sont globaux, pas spécifiques à un bloc --> voir les paramètres globaux associés

        """

        if self._collapsible_building == 0:
            return {_('Collapse building'): self._collapsible_building}

        elif self._collapsible_building == 1:
            return {_('Collapse building'): self._collapsible_building, **self.parent.get_params_collapsible_building()}

        else:
            return 99999, _("Unknown")

    def reset_params_collapse_building(self):
        """ Désactive l'effacement des bâtiments """

        self._collapsible_building = 0

    def check_params_collapse_building(self) -> tuple[bool, str]:
        """ Check collapse building """

        ret = "\nCollapse building\n*****************\n"
        valid = True

        if self._collapsible_building == 0:
            ret += _("Info : Collapse building not activated\n")
        else:
            ret += _("Info : Collapse building activated in the block\n")
            ret += _('       The paramaters are globals, not block dependent\n')
            ret += _('       Thus, please check the global parameters\n')

        return valid, ret



    # Forcing
    # *******

    def set_params_mobile_contour(self, activated:bool, which:Literal[1,-1]=1):
        """
        Définit si le contour est mobile ou non

        CMCH
        ****

        - text file
        - first line : number of points
        - next lines : time, x, y, acm

        CMXY
        ****

        - text file
        - first line : number of polygons, max number of points (in a polygon)
        - for each polygon
            - first line : number of points, index of the polygon
            - next lines : x, y

        :remark Only support 1 polygon for now

        """

        assert isinstance(activated, bool), "activated must be a boolean"

        if self._flux_type in [6, 9]:
            # see /Modules_wolf/2D/Wolf2D-Preprocessing.f90 for more information
            # used in "Lanaye lock study" for example
            self._mobile_polygon = which if activated else 0
        else:
            self._mobile_polygon = 1 if activated else 0

        if activated:

            file_cmch = Path(self.filegen) / '.cmch' # fichier contenant le chemin de parcours du bloc
            file_cmxy = Path(self.filegen) / '.cmxy' # fichier contenant le vecteur du bloc

            if file_cmch.exists():
                logging.info("File .cmch found")
            else:
                logging.warning("File .cmch not found")

            if file_cmxy.exists():
                logging.info("File .cmxy found")
            else:
                logging.warning("File .cmxy not found")

    def get_params_mobile_contour(self) -> dict:
        """ Retourne les paramètres du contour mobile """

        if abs(self._mobile_polygon) == 1:
            return {_('Mobile contour'): _('Yes')}
        else:
            return {_('Mobile contour'): _('No')}

    def reset_params_mobile_contour(self):
        """ Désactive le contour mobile """

        self._mobile_polygon = 0

    def check_params_mobile_contour(self) -> tuple[bool, str]:
        """ Check mobile contour """

        ret = "\nMobile Contour\n**************\n"
        valid = True

        if abs(self._mobile_polygon) == 1:
            ret += _("Info : Mobile contour activated\n")

            if self._flux_type not in [6, 9]:
                ret += _("Info FORTRAN : CONTOUR_FIXE = .true. and CONTOUR_FIXE_GLOB = .true.\n")
            elif self._mobile_polygon == 1:
                ret += _("Info FORTRAN : CONTOUR_MOB_GLOB = .true. and CONTOUR_MOB = .true.\n")
            elif self._mobile_polygon == -1:
                ret += _("Info FORTRAN : CONTOUR = .true. and CONTOUR_GLOB = .false.\n")

            file_cmch = Path(self.filegen) / '.cmch'
            file_cmxy = Path(self.filegen) / '.cmxy'

            if file_cmch.exists():
                ret += _("Info : File .cmch found\n")
            else:
                ret += _("Error : File .cmch not found\n")
                valid = False

            if file_cmxy.exists():
                ret += _("Info : File .cmxy found\n")
            else:
                ret += _("Error : File .cmxy not found\n")
                valid = False

        elif self._mobile_polygon == 0:
            ret += _("Info : Mobile contour not activated\n")
        else:
            ret += _("Error : Unknown value for mobile contour\n")
            valid = False

        return valid, ret



    def set_params_mobile_forcing(self, activated:bool):
        """
        Définit si le forcing mobile est activé ou non

        see: Modules_wolf/2D/Wolf2D-DonneesInst.f90 -- FORCING_MOB for more information

        .fmpar file must be present in the simulation directory
        .fm file must be present in the simulation directory
        .fmch file must be present in the simulation directory

        FMPAR
        *****

        - text file
        - first line : dx, dy
        - second line : nx, ny

        FM
        **

        - binary file
        - sequential arrays of forcing along X, Y and Z -- shape of one array = (nx, ny)
        - series of 3 arrays for each time

        FMCH
        ****

        - text file
        - on each line : time, origx, origy

        Track 'FORCING_MOB' in the Fortran code for more information

        """

        assert isinstance(activated, bool), "activated must be a boolean"

        self._mobile_forcing = 1 if activated else 0

        file_par = Path(self.filegen) / '.fmpar'
        file_fm = Path(self.filegen) / '.fm'
        file_fmch = Path(self.filegen) / '.fmch'

        if activated:
            if not file_par.exists():
                logging.warning("Mobile forcing activated but file .fmpar not found")
            if not file_fm.exists():
                logging.warning("Mobile forcing activated but file .fm not found")
            if not file_fmch.exists():
                logging.warning("Mobile forcing activated but file .fmch not found")

    def reset_params_mobile_forcing(self):
        """ Désactive le forcing mobile """

        self._mobile_forcing = 0

    def check_params_mobile_forcing(self) -> tuple[bool, str]:
        """ Check mobile forcing """

        ret = "\nMobile Forcing\n**************\n"
        valid = True

        file_par = Path(self.filegen) / '.fmpar'
        file_fm = Path(self.filegen) / '.fm'
        file_fmch = Path(self.filegen) / '.fmch'

        if self._mobile_forcing == 1:

            if file_par.exists():
                ret += _("Info : File .fmpar found\n")
            else:
                ret += _("Error : File .fmpar not found\n")
                valid = False

            if file_fm.exists():
                ret += _("Info : File .fm found\n")
            else:
                ret += _("Error : File .fm not found\n")
                valid = False

            if file_fmch.exists():
                ret += _("Info : File .fmch found\n")
            else:
                ret += _("Error : File .fmch not found\n")
                valid = False

        else:
            ret += _("Info : Mobile forcing not activated\n")

        return valid, ret


    def check_params_forcing(self) -> tuple[bool, str]:
        """
        Vérifie les paramètres de forcing et la présence du fichier associé

        """

        ret = '\nForcing\n*******\n'
        valid = True

        if self._has_forcing == 0:
            ret += _('Info: No forcing\n')

            fileforc = Path(self.parent.parent.filenamegen) / '.forc'
            if fileforc.exists():
                ret += _('Warning: Forcing file found but not used\n')

        elif self._has_forcing == 1:
            ret += _('Info: Forcing activated\n')

            fileforc = Path(self.parent.parent.filenamegen) / '.forc'
            if fileforc.exists():
                ret += _('Info: Forcing file found\n')
            else:
                ret += _('Error: Forcing file not found\n')
                valid = False

        return valid, ret


    # Bridges
    # *******

    def set_params_bridges(self, activated:bool):
        """ Définit si les ponts sont activés ou non """

        assert isinstance(activated, bool), "activated must be a boolean"

        self._bridge_activated = 1 if activated else 0

    def get_params_bridges(self) -> dict:
        """ Retourne les paramètres des ponts """

        if self._bridge_activated == 0:
            return {_('Bridges'): _('No')}
        else:
            return {_('Bridges'): _('Yes')}

    def reset_params_bridges(self):
        """ Désactive les ponts """

        self._bridge_activated = 0

    def check_params_bridges(self) -> tuple[bool, str]:
        """ Vérifie si les ponts sont activés """

        ret = "\nBridges\n*******\n"
        valid = True

        file = Path(self.filegen) / '.bridge'

        if self._bridge_activated == 1:
            ret += _("Info : Bridges activated\n")

            if file.exists():
                ret += _("Info : Bridges file found\n")
            else:
                ret += _("Error : Bridges file not found\nYou must create it with Z level under the deck\n")
                valid = False

        else:
            ret += _("Info : Bridges not activated\n")

            if file.exists():
                ret += _("Warning : Bridges file found\nDelete it to avoid misinformation?\n")
            else:
                ret += _("Info : Bridges file not found\n")

        return valid, ret


    # Danger maps
    # *********

    def set_params_danger_map(self, activated:bool, hmin:float, which:Literal['(Toa + H), Qx, Qy', 'with Z and toa_q', 'with Z, toa_q, v, toa_v'] = '(Toa + H), Qx, Qy'):
        """
        Définit si la carte de risque est activée ou non

        :param activated: booléen indiquant si la carte de risque doit être calculée
        :param hmin: incrément de hauteur minimale pour activer la carte de risque de temps d'arrivée

        """

        if activated:
            if which == '(Toa + H), Qx, Qy':
                self._danger_map_activated = 1
            elif which == 'with Z and toa_q':
                self._danger_map_activated = 2
            elif which == 'with Z, toa_q, v, toa_v':
                self._danger_map_activated = 3
            else:
                logging.error(f"Unknown danger map type {which} -- Set (Toa + H), Qx, Qy by default")
                self._danger_map_activated = 1
        else:
            self._danger_map_activated = 0

        self._danger_map_delta_hmin = hmin

    def get_params_danger_maps(self) -> dict:
        """ Retourne les paramètres de la carte de risque """

        if self._danger_map_activated == 0:
            return {_('Danger map'): _('No')}
        elif self._danger_map_activated == 1:
            return {_('Danger map'): _('Yes'), _('Type'): '(Toa + H), Qx, Qy', _('Delta hmin'): self._danger_map_delta_hmin}
        elif self._danger_map_activated == 2:
            return {_('Danger map'): _('Yes'), _('Type'): 'with Z and toa_q', _('Delta hmin'): self._danger_map_delta_hmin}
        elif self._danger_map_activated == 3:
            return {_('Danger map'): _('Yes'), _('Type'): 'with Z, toa_q, v, toa_v', _('Delta hmin'): self._danger_map_delta_hmin}
        else:
            return 99999, _('Unknown')

    def reset_params_danger_map(self):
        """ Désactive la carte de risque """

        self._danger_map_activated = 0
        self._danger_map_delta_hmin = 0.

    def check_params_danger_map(self) -> tuple[bool, str]:
        """ Check Danger map """

        ret = "\nDanger map\n*********\n"
        valid = True

        if self._danger_map_activated == 0:
            ret += _("Info : Danger map not activated\n")
        elif self._danger_map_activated == 1:
            ret += _("Info : Danger map activated\n")
            ret += _("Info : Type (Toa + H), Qx, Qy\n")
            ret += f"Info : Delta hmin = {self._danger_map_delta_hmin}\n"
        elif self._danger_map_activated == 2:
            ret += _("Info : Danger map activated\n")
            ret += _("Info : Type with Z and toa_q\n")
            ret += f"Info : Delta hmin = {self._danger_map_delta_hmin}\n"
        elif self._danger_map_activated == 3:
            ret += _("Info : Danger map activated\n")
            ret += _("Info : Type with Z, toa_q, v, toa_v\n")
            ret += f"Info : Delta hmin = {self._danger_map_delta_hmin}\n"
        else:
            ret += _("Error : Unknown value for danger map\n")
            valid = False

        return valid, ret


    # Friction
    # ********

    def get_lateral_friction_coefficient(self) -> float:
        """ Returns the lateral friction coefficient """
        return self._lateral_manning

    def set_lateral_friction_coefficient(self, lateral_friction_coefficient:float):
        """ Set the lateral friction coefficient """

        assert isinstance(lateral_friction_coefficient, float), "lateral_friction_coefficient must be a float"
        assert lateral_friction_coefficient >= 0., "lateral_friction_coefficient must be >= 0"

        self._lateral_manning = lateral_friction_coefficient

    def set_params_surface_friction(self, model_type:Literal['Horizontal',
                                                            'Modified surface corrected 2D (HECE)',
                                                            'Modified surface corrected 2D + Lateral external borders (HECE)',
                                                            'Horizontal and Lateral external borders',
                                                            'Modified surface (slope)',
                                                            'Modified surface (slope) + Lateral external borders',
                                                            'Horizontal and Lateral external borders (HECE)',
                                                            'Modified surface (slope) + Lateral external borders (HECE)',
                                                            'Horizontal -- Bathurst',
                                                            'Horizontal -- Bathurst-Colebrook',
                                                            'Horizontal -- Chezy',
                                                            'Horizontal -- Colebrook',
                                                            'Horizontal -- Barr',
                                                            'Horizontal -- Bingham',
                                                            'Horizontal -- Frictional fluid',
                                                            'Horizontal and Lateral external borders (Colebrook)',
                                                            'Horizontal and Lateral external borders (Barr)',
                                                            ]):

        """ Définit le mode de calcul de surface de friction à utiliser """

        if model_type == 'Horizontal':
            self._friction_law = 0
        elif model_type == 'Horizontal and Lateral external borders':
            self._friction_law = 1
        elif model_type == 'Modified surface (slope)':
            self._friction_law = 2
        elif model_type == 'Modified surface (slope) + Lateral external borders':
            self._friction_law = 3
        elif model_type == 'Horizontal and Lateral external borders (HECE)':
            self._friction_law = 4
        elif model_type == 'Modified surface (slope) + Lateral external borders (HECE)':
            self._friction_law = 5
        elif model_type == 'Modified surface corrected 2D (HECE)':
            self._friction_law = 6
        elif model_type == 'Modified surface corrected 2D + Lateral external borders (HECE)':
            self._friction_law = 7

        elif model_type == 'Horizontal -- Chezy':
            self._friction_law = -1
        elif model_type == 'Horizontal -- Bathurst':
            self._friction_law = -2
        elif model_type == 'Horizontal -- Colebrook':
            self._friction_law = -3
        elif model_type == 'Horizontal -- Barr':
            self._friction_law = -4
        elif model_type == 'Horizontal -- Bathurst-Colebrook':
            self._friction_law = -5
        elif model_type == 'Horizontal -- Bingham':
            self._friction_law = -6
        elif model_type == 'Horizontal and Lateral external borders (Colebrook)':
            self._friction_law = -34
        elif model_type == 'Horizontal and Lateral external borders (Barr)':
            self._friction_law = -44
        elif model_type == 'Horizontal -- Frictional fluid':
            self._friction_law = -61
        else:
            logging.error(f"Unknown surface friction model {model_type}")

        if self.has_modified_surface_friction:
            if self.parent._scheme_centered_slope !=2:
                # La modification des surfaces frottantes n"est pas implementee en reconstruction decentree!
                logging.warning("Setting nderdec to 2")

            self.parent._scheme_centered_slope = 2

    @property
    def is_Manning_surface_friction(self) -> bool:
        """ Retourne True si le modèle de surface de friction est de type Manning-Strickler """
        i, name = self.get_params_surface_friction()
        if i in [0, 1, 2, 3, 4, 5, 6, 7]:
            return True
        else:
            return False

    @property
    def is_manning_strickler(self) -> bool:
        """ Retourne True si le modèle de surface de friction est de type Manning-Strickler """
        return self.is_Manning_surface_friction

    @property
    def is_Colebrook_surface_friction(self) -> bool:
        """ Retourne True si le modèle de surface de friction est de type Colebrook """
        i, name = self.get_params_surface_friction()
        if i in [-3, -34, -5]:
            return True
        else:
            return False

    def get_params_surface_friction(self) -> tuple[int, str]:

            if self._friction_law == 0:
                return 0, 'Horizontal'
            elif self._friction_law == 1:
                return 1, 'Horizontal and Lateral external borders'
            elif self._friction_law == 2:
                return 2, 'Modified surface (slope)'
            elif self._friction_law == 3:
                return 3, 'Modified surface (slope) + Lateral external borders'
            elif self._friction_law == 4:
                return 4, 'and Lateral external borders (HECE)'
            elif self._friction_law == 5:
                return 5, 'Modified surface (slope) + Lateral external borders (HECE)'
            elif self._friction_law == 6:
                return 6, 'Modified surface corrected 2D (HECE)'
            elif self._friction_law == 7:
                return 7, 'Modified surface corrected 2D + Lateral external borders (HECE)'

            elif self._friction_law == -1:
                return -1, 'Horizontal -- Chezy'
            elif self._friction_law == -2:
                return -2, 'Horizontal -- Bathurst'
            elif self._friction_law == -3:
                return -3, 'Horizontal -- Colebrook'
            elif self._friction_law == -4:
                return -4, 'Horizontal -- Barr'
            elif self._friction_law == -5:
                return -5, 'Horizontal -- Bathurst-Colebrook'
            elif self._friction_law == -6:
                return -6, 'Horizontal -- Bingham'
            elif self._friction_law == -34:
                return -34, 'Horizontal and Lateral external borders (Colebrook)'
            elif self._friction_law == -44:
                return -44, 'Horizontal and Lateral external borders (Barr)'
            elif self._friction_law == -61:
                return -61, 'Horizontal -- Frictional fluid'
            else:
                return 99999, 'Unknown'

    def reset_params_surface_friction(self):
        """ Réinitialise le modèle de surface de friction """

        self._friction_law = 0

    def chech_params_surface_friction(self) -> tuple[bool, str]:
        """ Check surface friction model """

        ret = "\nSurface friction model\n**********************\n"
        valid = True

        if self._friction_law == 0:
            ret += _("Info : Horizontal\n")
        elif self._friction_law == 1:
            ret += _("Info : Horizontal and Lateral external borders\n")
        elif self._friction_law == 2:
            ret += _("Info : Modified surface (slope)\n")
        elif self._friction_law == 3:
            ret += _("Info : Modified surface (slope) + Lateral external borders\n")
        elif self._friction_law == 4:
            ret += _("Info : Horizontal and Lateral external borders (HECE)\n")
        elif self._friction_law == 5:
            ret += _("Info : Modified surface (slope) + Lateral external borders (HECE)\n")
        elif self._friction_law == 6:
            ret += _("Info : Modified surface corrected 2D (HECE)\n")
        elif self._friction_law == 7:
            ret += _("Info : Modified surface corrected 2D + Lateral external borders (HECE)\n")

        elif self._friction_law == -1:
            ret += _("Info : Horizontal -- Chezy\n")
        elif self._friction_law == -2:
            ret += _("Info : Horizontal -- Bathurst\n")
        elif self._friction_law == -3:
            ret += _("Info : Horizontal -- Colebrook\n")
        elif self._friction_law == -4:
            ret += _("Info : Horizontal -- Barr\n")
        elif self._friction_law == -5:
            ret += _("Info : Horizontal -- Bathurst-Colebrook\n")
        elif self._friction_law == -6:
            ret += _("Info : Horizontal -- Bingham\n")
        elif self._friction_law == -34:
            ret += _("Info : Horizontal and Lateral external borders (Colebrook)\n")
        elif self._friction_law == -44:
            ret += _("Info : Horizontal and Lateral external borders (Barr)\n")
        elif self._friction_law == -61:
            ret += _("Info : Horizontal -- Frictional fluid\n")
        else:
            ret += _("Error : Unknown value for surface friction model\n")
            valid = False

        return valid, ret


    # Turbulence
    # **********

    def set_params_turbulence(self,
                              model_type:Literal['k-eps HECE', 'No', 'Smagorinski', 'Fisher', 'k-eps', 'k',0,1,2,3,4,6],
                              nu_water:float=1.0e-6,
                              cnu:float=0.09,
                              maximum_nut:float=1.0e-3,
                              c3e:float=0.8,
                              clk:float=1.0e-4,
                              cle:float=10.0):

        """
        Définit le modèle de turbulence à utiliser

        :param model_type: type de modèle de turbulence
        :param nu_water: viscosité cinématique de l'eau
        :param cnu: coefficient de viscosité turbulente
        :param maximum_nut: valeur maximale de la viscosité turbulente -- A utiliser pour éviter les valeurs trop élevées mais une valeur trop basse influencera le résultat
        :param c3e: coefficient c3e
        :param clk: coefficient clk
        :param cle: coefficient cle
        """

        assert model_type in ['k-eps HECE', 'No', 'Smagorinski', 'Fisher', 'k-eps', 'k',0,1,2,3,4,6], "Unknown turbulence model"

        if model_type in ['No',0]:
            self._turbulence_type = 0
        elif model_type in ['k-eps HECE',6]:
            self._turbulence_type = 6
        elif model_type in ['Smagorinski']:
            self._turbulence_type = 1
        elif model_type in ['Fisher']:
            self._turbulence_type = 2
        elif model_type in ['k-eps']:
            self._turbulence_type = 3
        elif model_type in ['k']:
            self._turbulence_type = 4

        self._nu_water = nu_water
        self._turb_cnu = cnu
        self._turb_max_nut = maximum_nut
        self._turb_c3e = c3e
        self._turb_clk = clk
        self._turb_cle = cle

    def _get_params_turbulence_modelname(self) -> str:

        if self._turbulence_type == 0:
            return 'No'
        elif self._turbulence_type == 1:
            return 'Smagorinski'
        elif self._turbulence_type == 2:
            return 'Fisher'
        elif self._turbulence_type == 3:
            return 'k-eps'
        elif self._turbulence_type == 4:
            return 'k'
        elif self._turbulence_type == 6:
            return 'k-eps HECE'

    def get_params_turbulence(self) -> dict:
        """ Retourne les paramètres de turbulence """

        if self._turbulence_type == 0:
            return {}
        elif self._turbulence_type == 1:
            # Smagorinsky
            return {'Model': self._get_params_turbulence_modelname(),
                    'cnu': self._turb_cnu,
                    'vnu_eau': self._nu_water}
        elif self._turbulence_type == 2:
            # Fisher
            return {'Model': self._get_params_turbulence_modelname(),
                    'cnu': self._turb_cnu,
                    'vnu_eau': self._nu_water}
        elif self._turbulence_type == 3:
            # k-eps
            # cmu, c1e, c2e, sigmak, sigmae, vminediv, vminkdiv
            return {'Model': self._get_params_turbulence_modelname(),
                    'cmu': self._turb_cmu,
                    'vnu_eau': self._nu_water,
                    'c1e': self._turb_c1e,
                    'c2e': self._turb_c2e,
                    'sigmak': self._turb_sigmak,
                    'sigmae': self._turb_sigmae,
                    'vminediv': self._turb_minediv,
                    'vminkdiv': self._turb_minkdiv}
        elif self._turbulence_type == 4:
            # k
            # cd1, cd2, cmu, cnu, sigmak, vminkdiv, vnu_eau, vmaxvnut
            return {'Model': self._get_params_turbulence_modelname(),
                    'cd1': self._turb_cd1,
                    'cd2': self._turb_cd2,
                    'cmu': self._turb_cmu,
                    'cnu': self._turb_cnu,
                    'sigmak': self._turb_sigmak,
                    'vminkdiv': self._turb_minkdiv,
                    'vnu_eau': self._nu_water,
                    'vmaxnut': self._turb_max_nut}

        elif self._turbulence_type == 6:
            # k-eps HECE
            # cmu, cnu, c1e, c2e, c3e sigmak, sigmae, vminediv, vminkdiv, vnu_eau, vmaxvnut
            return {'Model': self._get_params_turbulence_modelname(),
                    'cmu': self._turb_cmu,
                    'cnu': self._turb_cnu,
                    'c1e': self._turb_c1e,
                    'c2e': self._turb_c2e,
                    'c3e': self._turb_c3e,
                    'clk': self._turb_clk,
                    'sigmak': self._turb_sigmak,
                    'sigmae': self._turb_sigmae,
                    'vminediv': self._turb_minediv,
                    'vminkdiv': self._turb_minkdiv,
                    'vnu_eau': self._nu_water,
                    'vmaxnut': self._turb_max_nut}

    def reset_params_turbulence(self):
        """ Réinitialise les paramètres de turbulence """

        self._turbulence_type = 0
        self._nu_water = 1.0e-6
        self._turb_cnu = 0.09
        self._turb_max_nut = 1.0e-3
        self._turb_c3e = 0.8
        self._turb_clk = 1.0e-4
        self._turb_cle = 10.0

    def check_params_turbulence(self) -> tuple[bool, str]:
        """ Vérifie les paramètres de turbulence """

        ret = '\nTurbulence\n**********\n'
        valid = True

        if self._turbulence_type == 0:
            ret += _('Info: No turbulence model selected\n')
            return valid, ret

        elif self._turbulence_type == 1:
            ret += _('Info: Smagorinski model selected\n')

        elif self._turbulence_type == 2:
            ret += _('Info: Fisher model selected\n')

        elif self._turbulence_type == 3:
            ret += _('Info: k-eps model selected\n')

        elif self._turbulence_type == 4:
            ret += _('Info: k model selected\n')

        elif self._turbulence_type == 6:
            ret += _('Info: HECE k-eps model selected\n')

        if self._turb_cnu < 0.:
            ret += _('Warning: cnu < 0 -- Forcing 8.e-2\n')
            self._turb_cnu = 8.e-2

        elif self._turb_cnu == 0.:

            if self._turbulence_type in [1,2]:
                ret += _('Error: alpha must be strictly positive\n')
                valid = False

        else:
            if self._turbulence_type in [1]:
                ret += _('Info: Turbulent viscosity will be evaluated using eq. (IV-22) in Erpicum (2006) \n')
            elif self._turbulence_type in [2]:
                ret += _('Info: Turbulent viscosity will be evaluated using eq. (IV-20) in Erpicum (2006) \n')

        if self._nu_water < 0.:
            ret += _('Warning: Kinematic viscosity < 0 -- Forcing 1.e-6\n')
            self._nu_water = 1.e-6

        if self._turbulence_type in [4,6] and self._turb_max_nut == 0.:
            ret += _('Error: You must defined a maximum value for the turbulent viscosity\n')
            valid = False

        if self._turbulence_type in [4,6] and self._turb_max_nut > 0.:
            ret += _('Warning : a too low value of "max_nut" can influence the results -- To be checked by the user in the results \n')

        if self._turbulence_type in [6]:

            if self._turb_c3e <= 0.:
                ret += _('Warning: c3e must be strictly positive -- Force to 0.8\n')
                self._turb_c3e = 0.8

            if self._turb_clk <= 0.:
                ret += _('Warning: clk must be strictly positive -- Force to 1.e-4\n')
                self._turb_clk = 1.e-4

            if self._turb_cle <= 0.:
                ret += _('Warning: cle must be strictly positive -- Force to 10.\n')
                self._turb_cle = 10.

        return valid, ret



    def set_params_vam5_turbulence(self, nu_vertical:float, turbulence_model:int):
        """
        Définit les paramètres du modèle VAM5

        :param nu_vertical: viscosité verticale pour VAM5
        :param turbulence_model: modèle de turbulence pour VAM5

        """

        self._vam5_nu_vertical = nu_vertical
        self._vam5_turbulence_model = turbulence_model

        if self._vam5_nu_vertical < 0.:
            self._vam5_nu_vertical = 0.1

        if self._vam5_turbulence_model < 1:
            self._vam5_turbulence_model = 1

    def get_params_vam5_turbulence(self) -> dict:
        """ Retourne les paramètres du modèle VAM5 """

        return {'nu_vertical': self._vam5_nu_vertical,
                'turbulence_model': self._vam5_turbulence_model}

    def reset_params_vam5_turbulence(self):
        """ Réinitialise les paramètres du modèle VAM5 """

        self._vam5_nu_vertical = 0.
        self._vam5_turbulence_model = 0



    # Infiltration
    # ************

    def get_params_infiltration(self) -> dict:
        """ Retourne les paramètres d'infiltration """

        if self._infiltration_mode < 0:
            return {'a': self._infil_a,
                    'b': self._infil_b,
                    'c': self._infil_c,
                    'cd': self._infil_dev_cd,
                    'zseuil': self._infil_dev_zseuil,
                    'width': self._infil_dev_width,
                    'd': self._infil_var_d,
                    'e': self._infil_var_e,
                    'cd_a': self._infil_dev_a,
                    'cd_b': self._infil_dev_b,
                    'cd_c': self._infil_dev_c,
                    'cd_d': self._infil_dev_d}

        elif self._infiltration_mode == PREV_INFILTRATION_MOD_MOMENTUM_IMPOSED:
            return self.get_params_infiltration_momentum_correction()

        else:
            return {}

    def get_infiltration_mode(self) -> int:
        """ Retourne le mode d'infiltration """
        return self._infiltration_mode

    def set_infiltration_mode(self, mode:int) -> None:
        """ Définit le mode d'infiltration

        0 : PREV_INFILTRATION_NULL  - PAS D'INFILTRATION
        1 : PREV_INFILTRATION_SIMPLE - INFILTRATION SIMPLE (RÉPARTITION UNIFORME DU DÉBIT INJECTÉ PAR FICHIER .INF)
        2 : PREV_INFILTRATION_MOD_MOMENTUM - INFILTRATION AVEC MODIFICATION DE LA QT DE MVT (RÉPARTITION NON UNIFORME DU DÉBIT INJECTÉ PAR FICHIER .INF)
        4 : PREV_INFILTRATION_MOD_MOMENTUM_IMPOSED - INFILTRATION AVEC MODIFICATION IMPOSÉE DE LA QT DE MVT (RÉPARTITION NON UNIFORME DU DÉBIT INJECTÉ PAR FICHIER .INF)
        -1 : PREV_INFILTRATION_VAR_SIMPLE - INFILTRATION VARIABLE (RÉPARTITION UNIFORME DU DÉBIT INJECTÉ CALCULÉ SUR BASE DE L'ÉTAT HYDRODYNAMIQUE INSTANTANÉ)
        -2 : PREV_INFILTRATION_VAR_MOD_MOMENTUM - INFILTRATION VARIABLE AVEC MOD QT MVT (RÉPARTITION NON UNIFORME DU DÉBIT INJECTÉ CALCULÉ SUR BASE DE L'ÉTAT HYDRODYNAMIQUE INSTANTANÉ)
        -3 : PREV_INFILTRATION_VAR_LINKED_ZONES - INFILTRATION/EXFILTRATION "INTERNE" VARIABLE (RÉPARTITION UNIFORME DU DÉBIT SUR BASE DE DEUX ZONES D'INFILTRATION)

        :param mode: mode d'infiltration
        """
        assert isinstance(mode, int), "mode must be an integer"
        assert mode in PREV_INFILTRATION_MODES, f"mode must be in {PREV_INFILTRATION_MODES}"
        self._infiltration_mode = mode

    def reset_infiltration_mode(self) -> None:
        """ Réinitialise le mode d'infiltration """
        self._infiltration_mode = PREV_INFILTRATION_NULL


    def check_params_infiltration(self) -> tuple[bool, str]:
        """ Vérifie les paramètres d'infiltration """

        ret = '\nInfiltration\n************\n'
        valid = True

        if self._infiltration_mode == PREV_INFILTRATION_NULL:
            ret += _('Info: No infiltration\n')
        elif self._infiltration_mode == PREV_INFILTRATION_SIMPLE:
            ret += _('Info: Simple infiltration\n')
        elif self._infiltration_mode == PREV_INFILTRATION_MOD_MOMENTUM:
            ret += _('Info: Infiltration with momentum modification\n')
        elif self._infiltration_mode == PREV_INFILTRATION_MOD_MOMENTUM_IMPOSED:
            ret += _('Info: Infiltration with imposed momentum modification\n')
        elif self._infiltration_mode == PREV_INFILTRATION_VAR_SIMPLE:
            ret += _('Info: Variable infiltration\n')
        elif self._infiltration_mode == PREV_INFILTRATION_VAR_MOD_MOMENTUM:
            ret += _('Info: Variable infiltration with momentum modification\n')
        elif self._infiltration_mode == PREV_INFILTRATION_VAR_LINKED_ZONES:
            ret += _('Info: Variable infiltration/exfiltration (linked zone)\n')

        if self._infiltration_mode < 0:
            ret += _('Info: Coefficients a={self._infil_a}, b={self._infil_b}, c={self._infil_c}\n')

            if self._infiltration_mode != PREV_INFILTRATION_VAR_LINKED_ZONES and self._infil_a == 0. and self._infil_b == 0. and self._infil_c == 0.:
                ret += _('Warning: No polynomial infiltration\n')

            if self._infiltration_mode == PREV_INFILTRATION_VAR_LINKED_ZONES and self._infil_a == 0.:
                ret += _('Warning: No infiltration/exfiltration under bridge\n')

            ret += _('Info: Coefficients Cd={self._infil_dev_cd}, width={self._infil_dev_width}\n, zseuil={self._infil_dev_zseuil}')

            if self._infiltration_mode != PREV_INFILTRATION_VAR_LINKED_ZONES and self._infil_dev_cd == 0. or self._infil_dev_width == 0.:
                ret += _('Warning: No weir exfiltration\n')

            if self._infiltration_mode == PREV_INFILTRATION_VAR_LINKED_ZONES and (self._infil_dev_cd == 0. or self._infil_dev_width == 0.):
                ret += _('Warning: No weir over bridge\n')

            ret += _('Info: Coefficients d={self._infil_var_d}, e={self._infil_var_e}\n')

            if self._infil_var_d == 0.:
                ret += _('Warning: No power infiltration\n')

            ret += _('Info: Coefficients a={self._infil_dev_a}, b={self._infil_dev_b}, c={self._infil_dev_c}, d={self._infil_dev_d}\n')

            if self._infil_dev_a == 0. and self._infil_dev_b == 0. and self._infil_dev_c == 0. and self._infil_dev_d == 0.:
                ret += _('Warning: No polynomial weir exfiltration\n')

            if self._infil_dev_cd != 0. and (self._infil_dev_a != 0. or self._infil_dev_b != 0. or self._infil_dev_c != 0. or self._infil_dev_d != 0.):
                ret += _('Error: Both weir and polynomial exfiltration defined\n')
                valid = False

        return valid, ret



    def set_params_infiltration_momentum_correction(self, ux:float, vy:float):
        """ Définit les corrections de moment pour l'infiltration """

        self._infil_correction_ux = ux
        self._infil_correction_vy = vy

        if self._infiltration_mode != PREV_INFILTRATION_MOD_MOMENTUM_IMPOSED:
            logging.warning("To apply, you must set ninfil to 4")
        else:
            logging.info("Infiltration momentum correction applied")

    def get_params_infiltration_momentum_correction(self) -> dict:
        """ Retourne les corrections de moment pour l'infiltration """

        if self._infiltration_mode == PREV_INFILTRATION_MOD_MOMENTUM_IMPOSED:
            return {'ux': self._infil_correction_ux,
                    'vy': self._infil_correction_vy}
        else:
            return {}

    def reset_params_infiltration_momentum_correction(self):
        """ Réinitialise les corrections de moment pour l'infiltration """

        self._infil_correction_ux = 0.
        self._infil_correction_vy = 0.



    def set_params_infiltration_bridge(self, a:float, cd:float, zseuil:float, width:float):
        """
        Définit les paramètres de transfert entre 2 zones d'infiltration/exfiltration de
        part et d'autre d'un pont

        Le débit échangé est calculé sur base de la somme de 2 contributions :
            - un écoulement sous pression Q_1 = sqrt{a * |Z_1 - Z_2|} * sign(Z_1 - Z_2)
            - un écoulement de type déversoir Q_2 = cd * sqrt{2 * g * (Z_1 + U^2 / {2g} - Zseuil)^3} * width

        La somme des 2 débits est ensuite répartie sur les mailles des 2 zones d'infiltration/exfiltration.

        Il est prélevé dans les zones impaires et injecté dans les zones paires suivantes.

        see : Modules_wolf/2D/Wolf2D-DonneesInst.f90 - CALC_CHARGE_ET_DEBIT_2

        """

        self._infil_dev_cd = cd
        self._infil_dev_zseuil = zseuil
        self._infil_dev_width = width
        self._infil_a = a

    def reset_params_infiltration_bridges(self):
        """ Réinitialise les paramètres de transfert entre 2 zones d'infiltration/exfiltration de part et d'autre d'un pont """

        self._infil_dev_cd = 0.
        self._infil_dev_zseuil = 0.
        self._infil_dev_width = 0.
        self._infil_a = 0.



    def set_params_infiltration_weir(self, cd:float, zseuil:float, width:float):
        """
        Définit les paramètres d'un déversoir pour l'exfiltration variable

        $ Q = cd * sqrt{2 * g * (Z + U^2 / {2g} - Zseuil)^3} * width $

        avec :
            - Z : altitude de surface libre moyenne sur la zone d'infiltration
            - U : vitesse moyenne sur la zone d'infiltration
            - cd : coefficient de débit
            - zseuil : altitude du seuil
            - width : largeur du déversoir

        Le débit est ensuite réparti sur les mailles de la zone d'exfiltration (retrait de matière si Q>0).

        """

        self._infil_dev_cd = cd
        self._infil_dev_zseuil = zseuil
        self._infil_dev_width = width

    def reset_params_infiltration_weir(self):
        """ Réinitialise les paramètres du déversoir """

        self._infil_dev_cd = 0.
        self._infil_dev_zseuil = 0.
        self._infil_dev_width = 0.



    def set_params_infiltration_weir_poly3(self,
                                    a:float,
                                    b:float,
                                    c:float,
                                    d:float,
                                    zseuil:float,
                                    width:float):
        """
        Définit les paramètres d'un déversoir pour l'exfiltration variable de type polynomiale

        $ H = Z - Z_seuil $

        $ Cd = a * H^3 + b * H^2 + c * H + d $

        $ Q = 2/3 * Cd * sqrt{2 * g * H^3} * width $

        avec :
            - Z : altitude de surface libre moyenne sur la zone d'infiltration
            - a, b, c, d : coefficients
            - zseuil : altitude du seuil
            - width : largeur du déversoir

        Le débit est ensuite réparti sur les mailles de la zone d'exfiltration (retrait de matière si Q>0).

        """

        self._infil_dev_zseuil = zseuil
        self._infil_dev_a = a
        self._infil_dev_b = b
        self._infil_dev_c = c
        self._infil_dev_d = d
        self._infil_dev_width = width

    def reset_params_infiltration_weir_poly3(self):
        """ Réinitialise les paramètres du déversoir """

        self._infil_dev_a = 0.
        self._infil_dev_b = 0.
        self._infil_dev_c = 0.
        self._infil_dev_d = 0.
        self._infil_dev_zseuil = 0.
        self._infil_dev_width = 0.



    def set_params_infiltration_polynomial2(self, a:float, b:float, c:float):
        """
        Définit les paramètres d'une infiltration variable de type polynomiale

        $ Q = a * Z^2 + b * Z + c $

        avec
            - Z : altitude de surface libre moyenne sur la zone d'infiltration
            - a, b, c : coefficients

        Le débit est ensuite réparti sur les mailles de la zone d'infiltration (apport de matière si Q>0).

        """

        self._infil_a = a
        self._infil_b = b
        self._infil_c = c

    def reset_params_infiltration_polynomial2(self):
        """ Réinitialise les paramètres de l'infiltration polynomiale """

        self._infil_a = 0.
        self._infil_b = 0.
        self._infil_c = 0.



    def set_params_infiltration_power(self, d:float, e:float):
        """
        Définit les paramètres d'une infiltration variable de type puissance

        $ Q = d * sqrt{Z-e} $

        avec :
            - Z : altitude de surface libre moyenne sur la zone d'infiltration
            - d : coefficient
            - e : hauteur minimale de l'infiltration variable (si Z <= e, l'infiltration est nulle)

        Le débit est ensuite réparti sur les mailles de la zone d'infiltration (apport de matière si Q>0).
        """

        self._infil_var_d = d
        self._infil_var_e = e

    def reset_params_infiltration_power(self):
        """ Réinitialise les paramètres de l'infiltration de type puissance """

        self._infil_var_d = 0.
        self._infil_var_e = 0.


    # Material
    # ********


    def set_params_bingham_model(self, rho:float):
        """
        Définit les paramètres du modèle de Bingham

        :param rho: viscosité plastique

        """

        self._bingham_rho = rho
        self._friction_law = -6

        logging.warning(_('Bingham model activated'))

    def reset_params_bingham_model(self):
        """
        Réinitialise les paramètres du modèle de Bingham
        """

        self._bingham_rho = 0.
        self._friction_law = 0

        logging.warning(_('Bingham model deactivated - Default friction model activated'))



    def set_params_frictional_model(self,
                             hs:float,
                             cv:float,
                             ru0:float):
        """
        Set the frictional model parameters
        """

        self._frictional_hs = hs
        self._frictional_cv = cv
        self._frictional_ru0 = ru0

        self._friction_law = -61

        logging.warning(_('Frictional model activated'))

    def get_params_frictional(self) -> dict:
        """
        Get the frictional model parameters
        """

        return {'rho': self._bingham_rho,
                'hs': self._frictional_hs,
                'cv': self._frictional_cv,
                'ru0': self._frictional_ru0}

    def reset_params_frictional_model(self):
        """
        Reset the frictional model parameters
        """

        self._frictional_hs = 0.
        self._frictional_cv = 0.
        self._frictional_ru0 = 0.

        self._friction_law = 0

        logging.warning(_('Frictional model deactivated - Default friction model activated'))


    # ****

    def _get_debug_params(self) -> list:
        return [self._turbulence_type,  # 1
                self._turb_cnu,         # 2
                self._nu_water,           # 3
                0.,                     # 4 - FIXME : Plus utilisé ?
                self._has_forcing,      # 5
                self._infil_a,          # 6
                self._infil_b,          # 7
                self._infil_c,          # 8
                self._sed_porosity,     # 9
                self._sed_d_mean,      # 10
                self._sed_s,            # 11
                self._sed_thetacr,      # 12
                self._sed_drifting_mode, # 13
                self._sed_eps_stabbed,   # 14
                self._sed_eps_h,          # 15
                self._vam5_nu_vertical,   # 16
                self._vam5_turbulence_model,# 17
                self._lateral_manning,      # 18
                self._friction_law,         # 19
                self._danger_map_activated,   # 20
                self._danger_map_delta_hmin,  # 21
                self._bridge_activated,     # 22
                self._infil_dev_cd,         # 23
                self._infil_dev_zseuil,     # 24
                self._infil_var_d,      # 25
                self._infil_var_e,      # 26
                self._mobile_forcing,   # 27
                self._infil_dev_width,  # 28
                self._mobile_polygon,   # 29
                self._bathurst_coeff,   # 30 - FIXME : Plus utilisé ?
                self._topo_inst,        # 31
                self._turb_max_nut,     # 32
                self._sed_model,        # 33
                self._infil_sed,        # 34
                self._write_topo,       # 35
                self._hmin_compute_equilibrium, # 36
                self._sed_gravity_discharge,    # 37
                self._sed_gamma_critic,       # 38
                self._sed_gamma_natural,        # 39
                self._infil_correction_ux,      # 40
                self._infil_correction_vy,      # 41
                self._infil_dev_a,              # 42
                self._infil_dev_b,      # 43
                self._infil_dev_c,      # 44
                self._infil_dev_d,      # 45
                self._turb_c3e,         # 46
                self._turb_clk,         # 47
                self._turb_cle,         # 48
                self._collapsible_building,  # 49
                self._sed_reduced_slope,    # 50
                self._sed_d30,          # 51
                self._sed_d90,          # 52
                self._bingham_rho,      # 53
                self._frictional_hs,    # 54
                self._frictional_cv,    # 55
                self._frictional_ru0,   # 56
                0.,    # 57
                0.,    # 58
                0.,    # 59
                0.]    # 60

    def _set_debug_params(self, values:list):
        """ Définition des paramètres de débogage sur base d'une liste de valeurs """

        assert len(values)==NB_BLOCK_DEBUG_PAR, "Bad length of values"

        for i in range(NB_BLOCK_DEBUG_PAR):
            curgroup = self.debug_groups[i]
            curparam = self.debug_names[i]

            if curgroup != NOT_USED:
                if self._params.get_param_dict(curgroup, curparam)[key_Param.TYPE] == Type_Param.Float:
                    values[i] = float(values[i])
                else:
                    values[i] = int(values[i])
            else:
                values[i] = 0

        self._turbulence_type = values[0]
        self._turb_cnu        = values[1]
        self._nu_water    = values[2]

        #FIXME debug4 not used

        self._has_forcing   = values[4]

        self._infil_a   = values[5]
        self._infil_b   = values[6]
        self._infil_c   = values[7]

        self._sed_porosity  = values[8]
        self._sed_d_mean   = values[9]
        self._sed_s   = values[10]
        self._sed_thetacr  = values[11]
        self._sed_drifting_mode = values[12]
        self._sed_eps_stabbed = values[13]
        self._sed_eps_h = values[14]

        self._vam5_nu_vertical = values[15]
        self._vam5_turbulence_model = values[16]

        self._lateral_manning = values[17]
        self._friction_law = values[18]

        self._danger_map_activated = values[19]
        self._danger_map_delta_hmin = values[20]

        self._bridge_activated = values[21]

        self._infil_dev_cd      = values[22]
        self._infil_dev_zseuil  = values[23]
        self._infil_var_d       = values[24]
        self._infil_var_e       = values[25]

        self._mobile_forcing    = values[26]

        self._infil_dev_width   = values[27]

        self._mobile_polygon    = values[28]

        self._bathurst_coeff    = values[29] #FIXME not used ?

        self._topo_inst         = values[30]

        self._turb_max_nut           = values[31]

        self._sed_model = values[32]

        self._infil_sed = values[33]

        self._write_topo = values[34]

        self._hmin_compute_equilibrium = values[35]
        self._sed_gravity_discharge = values[36]

        self._sed_gamma_critic = values[37]
        self._sed_gamma_natural = values[38]

        self._infil_correction_ux = values[39]
        self._infil_correction_vy = values[40]

        self._infil_dev_a = values[41]
        self._infil_dev_b = values[42]
        self._infil_dev_c = values[43]
        self._infil_dev_d = values[44]

        self._turb_c3e = values[45]
        self._turb_clk = values[46]
        self._turb_cle = values[47]

        self._collapsible_building = values[48]

        self._sed_reduced_slope = values[49]

        self._sed_d30 = values[50]
        self._sed_d90 = values[51]

        self._bingham_rho = values[52]
        self._frictional_hs = values[53]
        self._frictional_cv = values[54]
        self._frictional_ru0 = values[55]

        # FIXME debug 57, 58, 59, 60 not used

        # This call will update the GUI if exists
        self._set_block_params()

    def _get_general_params(self) -> list:
        """ Liste des 23 paramètres généraux - NB_BLOCK_GEN_PAR """

        return [self._reconstruction_internal,
                self._reconstruction_frontier,
                self._reconstruction_free_border,
                self._limiting_neighbors,
                self._limiting_h_or_Z,
                self._treating_frontier,
                self._flux_type,
                self._number_unknowns,
                self._number_equations,
                self._froude_max,
                self._uneven_speed_distribution,
                self._conflict_resolution,
                self._evolutive_domain,
                self._topography_operator,
                self._friction_implicit,
                self._infiltration_mode,
                self._infil_zref,
                self._axis_inclination_type,
                self._egalize_z,
                self._egalize_zref,
                self._stop_steady,
                self._stop_eps,
                self._topo_isvariable]

    def _set_general_params(self, values:list):
        """ Définition des 23 paramètres généraux sur base d'une liste de valeurs """
        assert len(values)==NB_BLOCK_GEN_PAR, "Bad length of values"

        for i in range(NB_BLOCK_GEN_PAR):
            curgroup = self.gen_groups[i]
            curparam = self.gen_names[i]

            if curgroup != NOT_USED:

                if self._params.get_param_dict(curgroup, curparam)[key_Param.TYPE] == Type_Param.Float:
                    values[i] = float(values[i])
                else:
                    values[i] = int(values[i])

            else:
                values[i] = 0

        self._reconstruction_internal       = values[0]
        self._reconstruction_frontier       = values[1]
        self._reconstruction_free_border    = values[2]
        self._limiting_neighbors            = values[3]
        self._limiting_h_or_Z               = values[4]
        self._treating_frontier             = values[5]
        self._flux_type                     = values[6]
        self._number_unknowns               = values[7]
        self._number_equations              = values[8]
        self._froude_max                    = values[9]
        self._uneven_speed_distribution     = values[10]
        self._conflict_resolution           = values[11]
        self._evolutive_domain              = values[12]
        self._topography_operator           = values[13]
        self._friction_implicit             = values[14]
        self._infiltration_mode             = values[15]
        self._infil_zref                    = values[16]
        self._axis_inclination_type         = values[17]
        self._egalize_z                     = values[18]
        self._egalize_zref                  = values[19]
        self._stop_steady                   = values[20]
        self._stop_eps                      = values[21]
        self._topo_isvariable               = values[22]

        # This call will update the GUI if exists
        self._set_block_params()

    def write_file(self,f):
        """
        Writing the general parameters in a file

        :remark The order of the parameters is important
        """
        ##reconstruction et limitation
        f.write('{:g}\n'.format(self._reconstruction_internal))
        f.write('{:g}\n'.format(self._reconstruction_frontier))
        f.write('{:g}\n'.format(self._reconstruction_free_border))
        f.write('{:g}\n'.format(self._limiting_neighbors))
        f.write('{:g}\n'.format(self._limiting_h_or_Z))
        f.write('{:g}\n'.format(self._treating_frontier))
        f.write('{:g}\n'.format(self._flux_type))
        # paramètres de calcul
        f.write('{:g}\n'.format(self._number_unknowns))
        f.write('{:g}\n'.format(self._number_equations))
        f.write('{:g}\n'.format(self._froude_max))
        f.write('{:g}\n'.format(self._uneven_speed_distribution))
        # options
        f.write('{:g}\n'.format(self._conflict_resolution))
        f.write('{:g}\n'.format(self._evolutive_domain))
        f.write('{:g}\n'.format(self._topography_operator))
        # options
        f.write('{:g}\n'.format(self._friction_implicit))
        #			 [-1,0[ = impl complet pondéré par ||
        f.write('{:g}\n'.format(self._infiltration_mode))
        f.write('{:g}\n'.format(self._infil_zref))
        f.write('{:g}\n'.format(self._axis_inclination_type))
        f.write('{:g}\n'.format(self._egalize_z))
        f.write('{:g}\n'.format(self._egalize_zref))
        f.write('{:g}\n'.format(self._stop_steady))
        f.write('{:g}\n'.format(self._stop_eps))
        f.write('{:g}\n'.format(self._topo_isvariable))

    def write_debug(self,f):
        """
        Writing the debug parameters in a file

        :param f: file to write in

        :remark The order of the parameters is important
        """

        vdebug = self._get_debug_params()

        for curdebug in vdebug:
            f.write('{:g}\n'.format(curdebug))

    def apply_changes_to_memory(self):
        """
        Apply the changes made in the GUI to the memory.

        This method is called when the user clicks on the "Apply" button in the GUI.

        Effective transfer will be done in the _callback_param_from_gui method.

        """

        if self._params is None:
            logging.error(_('No GUI block parameters available'))
        else:
            # Transfer the parameters from the GUI to the memory in the PyParams instance
            self._params.apply_changes_to_memory()

    def _callback_param_from_gui(self):
        """
        Set the parameters from the Wolf_Param object.

        Callback routine set in the PyParams instance.

        """

        if self._params is None:
            logging.error(_('No GUI block parameters available'))
        else:
            # Transfer the parameters from the memory to the prev_parameters_simul instance
            self._set_general_params([self._params[(self.gen_groups[i], self.gen_names[i])] for i in range(NB_BLOCK_GEN_PAR)])

            debug = []
            for curgroup, curname in zip(self.debug_groups, self.debug_names):
                if curgroup != NOT_USED:
                    debug.append(self._params[(curgroup, curname)])
                else:
                    debug.append(0.)

            self._set_debug_params(debug)

    def get_parameter(self, group:str, name:str) -> Union[int,float]:
        """ Get a parameter value """

        if group in self.gen_groups:
            if name in self.gen_names:
                idx = self.gen_names.index(name)

                if group == self.gen_groups[idx]:

                    vals = self._get_general_params()
                    return vals[idx]

                else:
                    logging.error(_('Bad group/name in parameters'))
                    return

        if group in self.debug_groups:
            if name in self.debug_names:
                idx = self.debug_groups.index(group)

                if group == self.debug_groups[idx]:
                    vals = self._get_debug_params()

                    idx_par = self.debug_names.index(name)
                    return vals[idx_par]

                else:
                    logging.error(_('Bad group/name in parameters'))
                    return

        logging.error(_('Group not found in parameters'))


    def set_parameter(self, group:str, name:str, value:Union[int,float]) -> None:
        """ Set a parameter value """

        if group in self.gen_groups:
            if name in self.gen_names:
                idx = self.gen_names.index(name)

                if group == self.gen_groups[idx]:

                    vals = self._get_general_params()
                    vals[idx] = value

                    self._set_general_params(vals)
                    return
                else:
                    logging.error(_('Bad group/name in parameters'))
                    return

        if group in self.debug_groups:
            if name in self.debug_names:
                idx = self.debug_groups.index(group)

                if group == self.debug_groups[idx]:
                    vals = self._get_debug_params()

                    idx_par = self.debug_names.index(name)
                    vals[idx_par] = value

                    self._set_debug_params(vals)
                    return
                else:
                    logging.error(_('Bad group/name in parameters'))
                    return

        logging.error(_('Group not found in parameters'))

    def _get_groups(self) -> list[str]:
        """ Retourne la liste des groupes de paramètres """

        unique_groups = list(set(self.gen_groups + self.debug_groups))

        if NOT_USED in unique_groups:
            unique_groups.remove(NOT_USED)

        unique_groups.sort()

        return unique_groups

    def _get_param_names(self) -> list[str]:
        """ Retourne la liste des noms de paramètres """

        names = self.gen_names + self.debug_names
        names.sort()

        return names

    def _get_groups_and_names(self) -> list[tuple[str,str]]:
        """ Retourne la liste des couples (group, name) """

        group_names = [(self.gen_groups[i], self.gen_names[i]) for i in range(NB_BLOCK_GEN_PAR) if self.gen_groups[i] != NOT_USED] + [(self.debug_groups[i], self.debug_names[i]) for i in range(NB_BLOCK_DEBUG_PAR) if self.debug_groups[i] != NOT_USED]

        group_names.sort(key=lambda x: x[0])

        return group_names

    def get_active_params(self) -> dict:
        """ Retourne les paramètres qui sont différents des valeurs par défaut """

        active_params = {}

        _genpar = self._get_general_params()
        for i in range(NB_BLOCK_GEN_PAR):
            if self._default_gen_par[i] != _genpar[i]:
                active_params[(self.gen_groups[i], self.gen_names[i])] = _genpar[i]

        _dbg_par = self._get_debug_params()
        for i in range(NB_BLOCK_DEBUG_PAR):
            if self._default_debug_par[i] != _dbg_par[i]:
                active_params[(self.debug_groups[i], self.debug_names[i])] = _dbg_par[i]

        active_params = {k: v for k, v in sorted(active_params.items(), key=lambda item: item[0])}

        active_params2 = {}
        for k,v in active_params.items():
            if k[0] not in active_params2:
                active_params2[k[0]] = {}
            active_params2[k[0]][k[1]] = v

        return active_params, active_params2

    def get_all_params(self) -> dict:
        """ Retourne tous les paramètres, y compris les valeurs par défaut """

        all_params = {}

        _genpar = self._get_general_params()
        for i in range(NB_BLOCK_GEN_PAR):
            all_params[(self.gen_groups[i], self.gen_names[i])] = _genpar[i]

        _dbg_par = self._get_debug_params()
        for i in range(NB_BLOCK_DEBUG_PAR):
            all_params[(self.debug_groups[i], self.debug_names[i])] = _dbg_par[i]

        all_params = {k: v for k, v in sorted(all_params.items(), key=lambda item: item[0])}

        all_params2={}
        for k,v in all_params.items():
            if k[0] not in all_params2:
                all_params2[k[0]]={}
            all_params2[k[0]][k[1]] = v

        return all_params, all_params2

    def _set_block_params(self, toShow = True, force=False) -> Wolf_Param:
        """
        Création d'un objet Wolf_Param et, si souhaité, affichage des paramètres via GUI wxPython

        :param toShow: booléen indiquant si les paramètres doivent être affichés via GUI wxPython
        """

        if self._params is None or force:
            self._params = Wolf_Param(parent=None,
                                          title=self._name + _(' Parameters'),
                                          to_read=False,
                                          withbuttons=True,
                                          DestroyAtClosing=True,
                                          toShow=toShow,
                                          init_GUI=toShow)

            self._params.set_callbacks(self._callback_param_from_gui, self._callback_param_from_gui)

        self._fillin_general_parameters()
        self._fillin_debug_parameters()

        self._params.Populate()

    def _fillin_general_parameters(self):
        """
        General parameters

        Create list of groups ans parameter names to be used in the GUI/Wolf_Params object

        :remark The order of the parameters is important

        """

        if self._params is None:
            logging.error(_('No block parameters available'))
            return

        myparams = self._params

        self.gen_groups=[]
        self.gen_names=[]

        active_vals = self._get_general_params()

        # 1
        self.gen_groups.append(_('Reconstruction'))
        self.gen_names.append(_('Reconstruction method'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Variable\'s reconstruction method to the borders (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Constant'):0,
                                            _('Linear'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 2
        self.gen_groups.append(_('Reconstruction'))
        self.gen_names.append(_('Interblocks reconstruction method'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Variable\'s reconstruction method to the borders at the interblock (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Constant'):0,
                                            _('Non limited linear'):1,
                                            _('Limited linear'):2}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 3
        self.gen_groups.append(_('Reconstruction'))
        self.gen_names.append(_('Free border reconstruction method'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Variable\'s reconstruction method to the free borders (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Constant'):0,
                                            _('Non limited linear'):2}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 4
        self.gen_groups.append(_('Reconstruction'))
        self.gen_names.append(_('Number of neighbors'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Number of neighbors to take into account during limitation (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 5
        self.gen_groups.append(_('Reconstruction'))
        self.gen_names.append(_('Limit water depth or water level'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Limit water depth or water level (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Water depth (H)'):0,
                                            _('Water level (H+Z)'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 6
        self.gen_groups.append(_('Reconstruction'))
        self.gen_names.append(_('Frontier'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Frontier (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('None'):1,
                                            _('Mean and unique'):0}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 7
        self.gen_groups.append(_('Splitting'))
        self.gen_names.append(_('Splitting type'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Splitting type (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('HECE'):1,
                                            _('VAM-5'):2,
                                            _('VAM-5 with vertical velocities'):3,
                                            _('VAM-5 with vertical velocites and solid transport'):4,
                                            _('HECE in terms of h, u, v'):5,
                                            _('HECE in terms of Volume, qx, qy'):6,
                                            _('HECE with H "energy formulation" in slope term'):7,
                                            _('HECE under pressure (H)'):8,
                                            _('HECE under pressure (Volume instead of H)'):9
                                            }),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 8
        self.gen_groups.append(_('Problem'))
        self.gen_names.append(_('Number of unknowns'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Number of unknowns (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Pure water'):4}, fullcomment=_('If a turbulence model is selected, the number of unknowns will be increased by the computation code accordingly to the number of additional equations')),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 9
        self.gen_groups.append(_('Problem'))
        self.gen_names.append(_('Number of equations'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Number of equations to solve (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Pure water'):3}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 10
        self.gen_groups.append(_('Reconstruction'))
        self.gen_names.append(_('Froude maximum'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Float',
                          comment=_('Froude maximum (Float) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 11
        self.gen_groups.append(_('Problem'))
        self.gen_names.append(_('Unequal speed distribution'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Unequal speed distribution (Integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('No'):0}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 12
        self.gen_groups.append(_('Problem'))
        self.gen_names.append(_('Conflict resolution'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Conflict resolution (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('HECE'):0,
                                            _('Centered'):1,
                                            _('Nothing'):2}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 13
        self.gen_groups.append(_('Problem'))
        self.gen_names.append(_('Fixed/Evolutive domain'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Fixed/Evolutive domain (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Fixed'):0,
                                            _('Evolutive'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 14
        self.gen_groups.append(_('Options'))
        self.gen_names.append(_('Topography'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Operation on toppography (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Mean'):1,
                                            _('Min'):3,
                                            _('Max'):2}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 15
        self.gen_groups.append(_('Options'))
        self.gen_names.append(_('Friction slope'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Friction slope (Integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Explicit'):0,
                                            _('Implicit (simple)'):1,
                                            _('Implicit (full)'):-1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 16
        self.gen_groups.append(_('Options'))
        self.gen_names.append(_('Modified infiltration'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Modified infiltration (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Imposed with momentum correction'):2,
                                            _('Variable with momentum correction'):-2,
                                            _('Linked zones'):-3,
                                            _('Imposed wo momentum correction'):1,
                                            _('Variable wo momentum correction'):-1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 17
        self.gen_groups.append(_('Options'))
        self.gen_names.append(_('Reference water level for infiltration'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Float',
                          comment=_('Reference water level for infiltration (Float) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 18
        self.gen_groups.append(_('Options'))
        self.gen_names.append(_('Inclined axes'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Inclined axes (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Classique avec topo'):1,
                                           'courbure':2,
                                           'courbure + vit verticale':3,
                                           'classique sans topo':4
                                           }),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 19
        self.gen_groups.append(_('Initial condition'))
        self.gen_names.append(_('To egalize'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('To egalize (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 20
        self.gen_groups.append(_('Initial condition'))
        self.gen_names.append(_('Water level to egalize'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Float',
                          comment=_('Water level to egalize (Float) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 21
        self.gen_groups.append(_('Stopping criteria'))
        self.gen_names.append(_('Stop computation on'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Stop computation if (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('Nothing'):0,
                                            _('Water depth'):2,
                                            _('Speed'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 22
        self.gen_groups.append(_('Stopping criteria'))
        self.gen_names.append(_('Epsilon'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Float',
                          comment=_('Epsilon (Float) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

        # 23
        self.gen_groups.append(_('Options'))
        self.gen_names.append(_('Variable topography'))
        idx = len(self.gen_groups)-1
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx],
                          type='Integer',
                          comment=_('Variable topography (integer) - default = {}'.format(self._default_gen_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx]

    def _fillin_debug_parameters(self):
        """
        Debug parameters

        Create list of groups ans parameter names to be used in the GUI/Wolf_Params object

        :remark The order of the parameters is important
        """

        if self._params is None:
            logging.error(_('No block parameters available'))
            return

        myparams = self._params

        #DEBUG
        self.debug_groups = []
        self.debug_names = []
        active_debug = self._get_debug_params()

        # DEBUG 1
        self.debug_groups.append(_('Turbulence'))
        self.debug_names.append(_('Model type'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Choice of turbulence model (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Smagorinski model (wo added equation)'):1,
                                            _('Fisher model (wo added equation)'):2,
                                            _('k-eps model (with 2 added equations)'):3,
                                            _('k model (with 1 added equation)'):4,
                                            _('Integrated k-eps model (with 2 added equations)'):6,
                                            }, fullcomment='If Smagorinski or Fisher model is selected, you must set alpha coefficient > 0.\nFisher is independant of the spatial resolution\nSmagorinski is dependant of the spatial resolution'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 2
        self.debug_groups.append(_('Turbulence'))
        self.debug_names.append(_('alpha coefficient'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('alpha coefficient (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Coefficient alpha [-]\nMultiplying the turbulent viscosity\nMust be greater than 0.\n',),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 3
        self.debug_groups.append(_('Turbulence'))
        self.debug_names.append(_('Kinematic viscosity'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Kinematic viscosity (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Kinematic viscosity [m²/s] added to turbulent viscosity\n',),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 4
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('4'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Integer',
        #                   comment=_(' (Integer) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 5
        self.debug_groups.append(_('Forcing'))
        self.debug_names.append(_('Activate'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Activate forcing (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1}, fullcomment='If yes, the forcing will be activated.\nAn unknown will be added to the system.\nA file ".forc" must be available in the directory of the simulation.'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 6
        self.debug_groups.append(_('Variable infiltration'))
        self.debug_names.append(_('a'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Variable infiltration coefficient a [-] in $a h^2 + b h + c$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 7
        self.debug_groups.append(_('Variable infiltration'))
        self.debug_names.append(_('b'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Variable infiltration coefficient b [-] in $a h^2 + b h + c$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 8
        self.debug_groups.append(_('Variable infiltration'))
        self.debug_names.append(_('c'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Variable infiltration coefficient c [-] in $a h^2 + b h + c$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 9
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Porosity'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Porosity [-] (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 10
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Mean diameter'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Mean diameter [m] (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 11
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Relative density'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Relative density $ \rho_s / rho_water $ [-] (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 12
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Theta critical velocity'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Theta critical velocity (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 13
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Drifting model'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Drifting model (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Meyer-Peter-Müller'):1,
                                            _('Rickenmann'):2,
                                            }),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 14
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Convergence criteria - bottom'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Convergence criteria - bottom (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 15
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Convergence criteria - sediment'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Convergence criteria - sediment (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 16
        self.debug_groups.append(_('VAM5 - Turbulence'))
        self.debug_names.append(_('Vertical viscosity'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Vertical viscosity (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 17
        self.debug_groups.append(_('VAM5 - Turbulence'))
        self.debug_names.append(_('Model type'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Model type (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 18
        self.debug_groups.append(_('Friction'))
        self.debug_names.append(_('Lateral Manning coefficient'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Lateral Manning coefficient (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 19
        self.debug_groups.append(_('Friction'))
        self.debug_names.append(_('Surface computation method'))
        idx = len(self.debug_groups)-1

        models_surf = {'Horizontal':0,
                        'Modified surface corrected 2D (HECE)':6,
                        'Modified surface corrected 2D + Lateral external borders (HECE)':7,
                        'Horizontal and Lateral external borders':1,
                        'Modified surface (slope)':2,
                        'Modified surface (slope) + Lateral external borders':3,
                        'Horizontal and Lateral external borders (HECE)':4,
                        'Modified surface (slope) + Lateral external borders (HECE)':5,
                        'Horizontal -- Bathurst':-2,
                        'Horizontal -- Bathurst-Colebrook':-5,
                        'Horizontal -- Chezy':-1,
                        'Horizontal -- Colebrook':-3,
                        'Horizontal -- Barr':-4,
                        'Horizontal -- Bingham':-6,
                        'Horizontal -- Frictional fluid':-61,
                        'Horizontal and Lateral external borders (Colebrook)':-34,
                        'Horizontal and Lateral external borders (Barr)':-44,
                        }

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Surface computation method (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(models_surf),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 20
        self.debug_groups.append(_('Danger map'))
        self.debug_names.append(_('Compute'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('To compute or not (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes (Toa + H + Qx + Qy)'):1,
                                            _('Yes with danger maps (Z + Toa_qmax)'):2,
                                            _('Yes with danger maps (Z + Toa_qmax + Vmax + Toa_vmax)'):3,
                                            },
                                           fullcomment=_('If yes, the danger maps will be computed (Time of arrival, H, QX, QY).\nIf needed, you can computed a second danger map with maximum water level and time of arrival of of QMAX\nor a third one with maximum velocity\n\nsee .risk, .risk2, .risk3 result files.')),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 21
        self.debug_groups.append(_('Danger map'))
        self.debug_names.append(_('Minimal water depth'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Minimal water depth where compute danger map (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Minimal increment of water depth [m] where compute danger map\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 22
        self.debug_groups.append(_('Bridge'))
        self.debug_names.append(_('Activate'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Activate or not the bridges (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1},
                                           fullcomment='If yes, the informations on bridges will be taken into account.\n\nNeed a .bridge file in the simulation directory.\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 23
        self.debug_groups.append(_('Infiltration weirs'))
        self.debug_names.append(_('Cd'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Discharge corfficient (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Discharge coefficient Cd [-] in $Cd L racine{2g (H - Z)^3}$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 24
        self.debug_groups.append(_('Infiltration weirs'))
        self.debug_names.append(_('Z'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Level of the weir (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Level of the weir Z [m] in $Cd L racine{2g (H - Z)^3}$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 25
        self.debug_groups.append(_('Variable infiltration 2'))
        self.debug_names.append(_('d'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Coefficient d (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Variable infiltration coefficient d [-] in $d racine{h - e}$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 26
        self.debug_groups.append(_('Variable infiltration 2'))
        self.debug_names.append(_('e'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Coefficient e (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Variable infiltration coefficient e [-] in $d racine{h - e}$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 27
        self.debug_groups.append(_('Mobile forcing'))
        self.debug_names.append(_('Activate'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Activate mobile forcing (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1},
                                           fullcomment='If yes, the mobile forcing will be activated.\nAn unknown will be added to the system.\nFile ".fmpar, .fm and .fmch" must be available in the directory of the simulation.'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 28
        self.debug_groups.append(_('Infiltration weirs'))
        self.debug_names.append(_('L'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Width of the weir [m] (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Width of the weir L [m] in $Cd L racine{2g (H - Z)^3}$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 29
        self.debug_groups.append(_('Mobile contour'))
        self.debug_names.append(_('Active'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Active (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes (1)'):1,
                                            _('Yes (-1)'):-1},
                                           fullcomment='If yes, the mobile contour will be activated.\nFiles ".cmch and .cmxy" must be available in the directory of the simulation.'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 30
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('30'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Integer',
        #                   comment=_(' (Integer) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 31
        self.debug_groups.append(_('Unsteady topo-bathymetry'))
        self.debug_names.append(_('Model type'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_(' (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Classical (via files)'):1,
                                            _('Dike (erosion by slices)'):2,
                                            _('Delayed erosion'):-1,
                                            _('Triangulation'):3,
                                            _('Triangulation (delayed)'):-3,
                                              },
                                           fullcomment='If yes, the unsteady topo-bathymetry will be activated.\nFiles ".topipar and ..." must be available in the directory of the simulation.'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 32
        self.debug_groups.append(_('Turbulence'))
        self.debug_names.append(_('Maximum value of the turbulent viscosity'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Max. turbulent viscosity (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 33
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Model type'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Model type (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Drifting (Exner)'):1,
                                            _('Drifting and suspension'):2,
                                            }),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 34
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Active infiltration'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Active infiltration (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1,
                                            }),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 35
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Write topography'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Write topography at each iteration (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1,
                                            }),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 36
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Hmin for computation'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Minimal water depth to compute equilibrium (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Minimal water depth [m] to compute equilibrium\nSee Wolf2D-Flux-Sedim.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 37
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('With gravity discharge'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('With gravity discharge or not (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1,
                                            }),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 38
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Critical slope'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Critical slope for gravity discharge (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 39
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Natural slope'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Natural slope for gravity discharge (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 40
        self.debug_groups.append(_('Infiltration'))
        self.debug_names.append(_('Forced correction ux'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Forced ux for momentum correction (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 41
        self.debug_groups.append(_('Infiltration'))
        self.debug_names.append(_('Forced correction vy'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Forced vy for momentum correction (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 42
        self.debug_groups.append(_('Infiltration weir poly3'))
        self.debug_names.append(_('a'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Coefficient a (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Coefficient a [-] in $Cd = a h^3 + b h^2 + c h + d with h = Z - Z_weir$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 43
        self.debug_groups.append(_('Infiltration weir poly3'))
        self.debug_names.append(_('b'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Coefficient b (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Coefficient b [-] in $Cd = a h^3 + b h^2 + c h + d with h = Z - Z_weir$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 44
        self.debug_groups.append(_('Infiltration weir poly3'))
        self.debug_names.append(_('c'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Coefficient c (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Coefficient c [-] in $Cd = a h^3 + b h^2 + c h + d with h = Z - Z_weir$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 45
        self.debug_groups.append(_('Infiltration weir poly3'))
        self.debug_names.append(_('d'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Coefficient d (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Coefficient d [-] in $Cd = a h^3 + b h^2 + c h + d with h = Z - Z_weir$\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 46
        self.debug_groups.append(_('Turbulence'))
        self.debug_names.append(_('C3E coefficient'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('C3E [-] (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 47
        self.debug_groups.append(_('Turbulence'))
        self.debug_names.append(_('CLK coefficient'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('CLK [-] (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 48
        self.debug_groups.append(_('Turbulence'))
        self.debug_names.append(_('CLE coefficient'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('CLE [-] (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 49
        self.debug_groups.append(_('Buildings'))
        self.debug_names.append(_('Collapsable'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Collapsable (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1,
                                            }),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 50
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('Reduction slope'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Reduction slope (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 51
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('D30'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Diameter 30% (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Diameter 30% [m] of the sediment\nRickemann model\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 52
        self.debug_groups.append(_('Sediment'))
        self.debug_names.append(_('D90'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Diameter 90% (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Diameter 90% [m] of the sediment\nRickemann model\nSee Wolf2D-DonneesInst.f90 for more information'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 53
        self.debug_groups.append(_('Frictional fluid'))
        self.debug_names.append(_('Density of the fluid'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 54
        self.debug_groups.append(_('Frictional fluid'))
        self.debug_names.append(_('Saturated height'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Saturated height (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 55
        self.debug_groups.append(_('Frictional fluid'))
        self.debug_names.append(_('Consolidation coefficient'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 56
        self.debug_groups.append(_('Frictional fluid'))
        self.debug_names.append(_('Interstitial pressure (t=0)'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Initial value of the interstitial pressure coefficient at the floor (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 57
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('57'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Integer',
        #                   comment=_(' (Integer) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 58
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('58'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Integer',
        #                   comment=_(' (Integer) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 59
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('59'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Integer',
        #                   comment=_(' (Integer) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 60
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('60'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Integer',
        #                   comment=_(' (Integer) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        return self._params


    def check_all(self) -> tuple[bool, str]:
        """ Call all check_params* routines in this class """

        valid, ret = True, ''

        for name, value in self.__class__.__dict__.items():
            if name.startswith('check_params') and callable(value):
                locvalid, locret = value(self)

                valid = valid and locvalid
                ret += locret

        return valid, ret

    def show(self, show_in_active_if_default:bool = False):
        """ Show the parameters of the block in a WX frame """

        # Not necessary the right place to put this, but it's the only place where we can put it
        # for now.

        if self._params is None:
            self._set_block_params(toShow = True)
            self._params.show_in_active_if_default = show_in_active_if_default
        else:
            if self._params.has_gui:
                self._params.show_in_active_if_default = show_in_active_if_default
                self._params.Populate()
                self._params.Show()

            else:
                self._params._set_gui(None, "Block parameters - {}".format(self._name), ontop=True, to_read = False, DestroyAtClosing=False, toShow = True, full_style=True)
                self._params.show_in_active_if_default = show_in_active_if_default
                self._params.hide_selected_buttons()
                self._params.Populate()

    def is_like(self, other:"prev_parameters_blocks") -> bool:
        """ Check if two prev_parameters_blocks are similar """

        src_gen = self._get_general_params()
        src_dbg = self._get_debug_params()

        oth_gen = other._get_general_params()
        oth_dbg = other._get_debug_params()

        return src_gen == oth_gen and src_dbg == oth_dbg

    def copy(self, other:"prev_parameters_blocks") -> None:
        """ Copy the parameters of another prev_parameters_blocks """

        oth_gen = other._get_general_params()
        oth_dbg = other._get_debug_params()

        self._set_general_params(oth_gen)
        self._set_debug_params(oth_dbg)

    def diff(self, other:Union["prev_parameters_blocks", list["prev_parameters_blocks"]]) -> dict:
        """ Return the differences between two prev_parameters_blocks """

        groups = self.gen_groups + self.debug_groups # Les fcts _get_groups firltrent les groupes inutiles --> autant passer par les variabes
        names  = self.gen_names + self.debug_names   # Les fcts _get_names filtrent les noms inutiles --> autant passer par les variabes

        src_gen = self._get_general_params()
        src_dbg = self._get_debug_params()

        src_all = src_gen + src_dbg

        if isinstance(other, list):
            if len(other) == 1 :
                other = other[0]

        if isinstance(other, list):

            others = [oth._get_general_params() + oth._get_debug_params() for oth in other]

            comp = [[cur[idx] for cur in others] for idx in range(len(src_all))]

            ret = {}

            for curgroup, curname, src, oth in zip(groups, names, src_all, comp):

                if not all([src == cur for cur in oth]):
                    ret[(curgroup, curname)] = (src, *oth)

        else:

            oth_gen = other._get_general_params()
            oth_dbg = other._get_debug_params()
            oth_all = oth_gen + oth_dbg

            ret = {}

            for curgroup, curname, src, oth in zip(groups, names, src_all, oth_all):

                if src != oth:
                    ret[(curgroup, curname)] = (src, oth)

        return ret

    def diff_print(self, other:Union["prev_parameters_blocks", list["prev_parameters_blocks"]]) -> str:
        """ Return the differences between two prev_parameters_blocks as a string """

        ret = self.diff(other)

        if not ret:
            return "No differences found"

        retstr = ""

        if isinstance(other, list):
            if len(other) == 1 :
                other = other[0]

        if isinstance(other, list):

            for (group, name), vals in ret.items():
                retstr += f"{group} - {name} : {vals[0]} -> {vals[1:]}\n"

        else:

            for (group, name), (src, oth) in ret.items():
                retstr += f"{group} - {name} : {src} -> {oth}\n"

        return retstr


class boundary_condition_2D:
    '''
	Type des CL générales, faibles et fortes
	@author Pierre Archambeau
    '''
    vec: vector

    def __init__(self, i: int, j: int, ntype: int, val: float, direction: int = 1) -> None:
        self.i = i  # indice de colonne dans le plus petit maillage
        self.j = j  # indice de ligne   dans le plus petit maillage
        self.ntype = ntype  # type de cl (h=1,qx=2,qy=3,rien=4,qbx=5,qby=6,hmod=7,fr=8)
        self.val = val  # valeur à imposer
        self.direction = direction

        self.vec = vector(name='bc' + str(i) + '-' + str(j))
        self.vec.myprop.width = 4
        self.vec.myprop.color = getIfromRGB([255, 128, 125])


class prev_boundary_conditions():
    """
    Classe pour le stockage des CL générales, faibles et fortes

    @author pierre archambeau

    """

    # The BC's data as they are encoded in the files
    mybc: list[boundary_condition_2D]
    # Vectors representing the geometry of the BC.
    # For weak conditions, these are the borders.
    # For strong conditions, there's no representation
    # as they covers an entire cell (instead of a single border)
    myzones: Zones

    @property
    def nb_bc(self):
        return len(self.mybc)

    def __init__(self, parent:"prev_parameters_simul") -> None:
        self.parent = parent
        self.reset()

    @property
    def dx(self):
        return self.parent._fine_mesh_dx

    @property
    def dy(self):
        return self.parent._fine_mesh_dy

    @property
    def origx(self):
        return self.parent._fine_mesh_origx

    @property
    def origy(self):
        return self.parent._fine_mesh_origy

    @property
    def translx(self):
        return self.parent._fine_mesh_translx

    @property
    def transly(self):
        return self.parent._fine_mesh_transly

    def reset(self):
        self.mybc = []
        self.myzones = Zones()
        self.myzones.add_zone(zone(name='BC_X'))
        self.myzones.add_zone(zone(name='BC_Y'))

    def fillgrid(self, gridto: CpGrid):

        gridto.SetColLabelValue(0, 'i')
        gridto.SetColLabelValue(1, 'j')
        gridto.SetColLabelValue(2, _('Type'))
        gridto.SetColLabelValue(3, _('Value'))
        gridto.SetColLabelValue(4, _('Self value'))
        gridto.SetColLabelValue(5, _('Old value'))
        gridto.SetColLabelValue(6, _('Water depth'))
        gridto.SetColLabelValue(7, _('Bottom level'))

        k = 0
        for curbc in self.mybc:
            gridto.SetCellValue(k, 0, str(curbc.i))
            gridto.SetCellValue(k, 1, str(curbc.j))
            gridto.SetCellValue(k, 2, str(curbc.ntype))
            gridto.SetCellValue(k, 3, str(curbc.val))
            gridto.SetCellValue(k, 5, str(curbc.val))
            k += 1

    def add(self, i:int, j:int, ntype:BCType_2D, value:float, orient:str):
        """ Add a new constraint
        i,j : indices
        ntype: type of the constraint
        orient: oritentation, used for drawing
        """
        assert orient in ('x','y','strongbc')

        if type(ntype) == BCType_2D:
            ntype = ntype.value[0]

        if orient == 'x':
            direction = Direction.LEFT.value
        elif orient == 'y':
            direction = Direction.BOTTOM.value
        else:
            direction = 0

        locbc = boundary_condition_2D(i, j, ntype, value, direction=direction)
        x1, y1, x2, y2 = self.get_xy(i, j, orient, True)
        locbc.vec.add_vertex(wolfvertex(x1, y1))
        locbc.vec.add_vertex(wolfvertex(x2, y2))

        self.mybc.append(locbc)
        if orient in 'x':
            self.myzones.myzones[0].add_vector(locbc.vec)
        elif orient == 'y':
            self.myzones.myzones[1].add_vector(locbc.vec)
        elif orient == 'strongbc':
            # Strong boundary conditions are not vectors.
            pass

    def read_file(self, lines: list, orient):
        """ Lecture du fichier de paramètres"""

        for curline in lines:

            tmp = curline.split(find_sep(curline))

            i = int(tmp[0])
            j = int(tmp[1])
            ntype = int(tmp[2])
            value = float(tmp[3])

            if orient == 'x':
                direction = Direction.LEFT.value
            elif orient == 'y':
                direction = Direction.BOTTOM.value
            else:
                direction = 0

            locbc = boundary_condition_2D(i, j, ntype, value, direction=direction)
            self.mybc.append(locbc)

            x1, y1, x2, y2 = self.get_xy(i, j, orient, True)

            locbc.vec.add_vertex(wolfvertex(x1, y1))
            locbc.vec.add_vertex(wolfvertex(x2, y2))

            if orient == 'x':
                self.myzones.myzones[0].add_vector(locbc.vec)
            elif orient == 'y':
                self.myzones.myzones[1].add_vector(locbc.vec)
            elif orient == 'strongbc':
                # Strong boundary conditions are not vectors.
                pass
            else:
               logging.error(f"Unrecognized orientation {orient}")

    def get_xy(self, i, j, orient, aswolf=False):

        if aswolf:
            i -= 1
            j -= 1

        if orient == 'x':
            x1 = np.float64(i) * self.dx + self.origx + self.translx
            y1 = np.float64(j) * self.dy + self.origy + self.transly
            x2 = x1
            y2 = y1 + self.dy

        elif orient == 'y':
            x1 = np.float64(i) * self.dx + self.origx + self.translx
            y1 = np.float64(j) * self.dy + self.origy + self.transly
            x2 = x1 + self.dx
            y2 = y1

        elif orient == 'strongbc':
            # I put the strong BC in the middle of a cell.
            x1 = np.float64(i) * self.dx + self.origx + self.translx + self.dx/2
            y1 = np.float64(j) * self.dy + self.origy + self.transly + self.dy/2
            x2, y2 = x1, y1

        else:
            raise Exception(f"Unrecognized orientation {orient}")

        return x1, y1, x2, y2

    def list_bc(self):
        """ Liste des CL existantes """

        return self.mybc

    def bc2text(self):
        """ Convert the BC's to a text representation """

        txt = ''
        for curbc in self.mybc:
            txt += f"{curbc.i}\t{curbc.j}\t{curbc.direction}\t{curbc.ntype}\t{curbc.val}\n"

        return txt

    def list_bc_ij(self):
        """
        Liste des indices CL existantes

        :return : 2 listes distinctes avec les indices i et j des CL
        """

        return [bc.i for bc in self.mybc], [bc.j for bc in self.mybc]

    def exists(self, i:int, j:int):
        """ Vérifie si une CL existe aux indices i et j """

        nb = 0
        for bc in self.mybc:
            if bc.i == i and bc.j == j:
                nb += 1

        return nb

    def get_bc(self, i:int, j:int):
        """ Récupère la/les CL aux indices i et j """

        curbc = []
        for bc in self.mybc:
            if bc.i == i and bc.j == j:
                curbc.append(bc)

        return curbc

    def remove(self, i:int, j:int):
        """ Supprime une CL existante """

        notfound = True

        # Il faut retenir les CL à supprimer
        # car on boucle cur les éléments de la liste.
        #
        # Une suppression en direct provoquerait un saut d'élément.
        to_remove = []
        for bc in self.mybc:
            if bc.i == i and bc.j == j:

                if bc.direction == Direction.LEFT.value:
                    self.myzones.myzones[0].myvectors.remove(bc.vec)
                elif bc.direction == Direction.BOTTOM.value:
                    self.myzones.myzones[1].myvectors.remove(bc.vec)

                to_remove.append(bc)

                notfound = False

        if notfound:
            logging.error(f"Boundary condition not found at {i},{j}")
        else:
            for curbc in to_remove:
                self.mybc.remove(curbc)

            logging.info(f"Removed {len(to_remove)} boundary conditions at {i},{j}")

    def change(self, i:int, j:int, ntype:BCType_2D, value:float):
        """ Remplace une CL existante """

        for bc in self.mybc:
            if bc.i == i and bc.j == j:
                bc.ntype = ntype.value[0]
                bc.val = value
                return

        logging.error(f"Boundary condition not found at {i},{j}")


class prev_parameters_simul:
    """
    Paramètres de simulation d'un modèle WOLF2D original

    @author pierre archambeau
    """

    blocks: list[prev_parameters_blocks]

    # FIXME Strong bc are on cell, not on borders, so their type should differ
    # from the one of clfbx/y.
    strong_bc: prev_boundary_conditions
    weak_bc_x: prev_boundary_conditions
    weak_bc_y: prev_boundary_conditions

    def check_all(self, verbosity = 0) -> tuple[bool, str]:
        """
        Call all check_params* routines in this class and all blocks

        :param verbosity: 0 = errors only, 1 = errors and warnings, 2 = everything, 3 = everything + group names

        """

        valid, ret = True, ''

        title = f'Checking Global Parameters'
        ret += f"\n\n{title}\n"
        ret += f"{'-'*(len(title))}\n"

        for name, value in self.__class__.__dict__.items():
            if name.startswith('check_params') and callable(value):
                locvalid, locret = value(self)

                valid = valid and locvalid
                ret += locret

        for block in self.blocks:

            title = f'Checking {block._name}'
            ret += f"\n\n{title}\n"
            ret += f"{'-'*(len(title))}\n"

            locvalid, locret = block.check_all()

            valid = valid and locvalid
            ret += locret

        if verbosity == 0:
            # keep only errors
            ret = '\n'.join([line for line in ret.split('\n') if 'error' in line.lower() and ':' in line])
        elif verbosity == 1:
            # keep only errors and warnings
            ret = '\n'.join([line for line in ret.split('\n') if 'error' in line.lower() or 'warning' in line.lower() and ':' in line])
        elif verbosity == 2:
            # keep everything except group names
            ret = '\n'.join([line for line in ret.split('\n') if ':' in line])
        else:
            # keep everything
            pass

        return valid, ret

    @property
    def dx(self):
        return self._fine_mesh_dx

    @property
    def dy(self):
        return self._fine_mesh_dy

    @dx.setter
    def dx(self, value):
        self._fine_mesh_dx = value

    @dy.setter
    def dy(self, value):
        self._fine_mesh_dy = value

    @property
    def nbx(self):
        return self._fine_mesh_nbx

    @property
    def nby(self):
        return self._fine_mesh_nby

    @nbx.setter
    def nbx(self, value):
        self._fine_mesh_nbx = value

    @nby.setter
    def nby(self, value):
        self._fine_mesh_nby = value

    @property
    def origx(self):
        return self._fine_mesh_origx

    @origx.setter
    def origx(self, value):
        self._fine_mesh_origx = value

    @property
    def origy(self):
        return self._fine_mesh_origy

    @origy.setter
    def origy(self, value):
        self._fine_mesh_origy = value

    @property
    def translx(self):
        return self._fine_mesh_translx

    @translx.setter
    def translx(self, value):
        self._fine_mesh_translx = value

    @property
    def transly(self):
        return self._fine_mesh_transly

    @transly.setter
    def transly(self, value):
        self._fine_mesh_transly = value

    @property
    def nblocks(self):
        return len(self.blocks)

    @property
    def nb_computed_blocks(self):
        """ Nombre de blocs calculés """
        nb = 0
        for idx in range(self.nblocks):
            if self.blocks[idx].computed:
                nb+=1
        return nb

    @property
    def partial_calculation(self):
        return self.nb_computed_blocks < self.nblocks

    @property
    def bc_nb_strong(self):
        return self.strong_bc.nb_bc

    @property
    def bc_nbx_weak(self):
        return self.weak_bc_x.nb_bc

    @property
    def bc_nby_weak(self):
        return self.weak_bc_y.nb_bc

    # For FORTRAN compatibility
    @property
    def clf(self):
        return self.strong_bc

    # For FORTRAN compatibility
    @property
    def clfbx(self):
        return self.weak_bc_x

    # For FORTRAN compatibility
    @property
    def clfby(self):
        return self.weak_bc_y

    @property
    def has_turbulence(self):
        """
        Check if the simulation has turbulence

        **Remark** : Turbulence is a bloc parameter, so we need to check all blocks
        """

        for block in self.blocks:
            if block.has_turbulence:
                return True

        return False


    def set_mesh_only(self):
        """
        Set the mesher only flag

        When launched, the Fortran program will only generate the mesh and stop.

        """

        self._mesher_only = 1

    def unset_mesh_only(self):
        self._mesher_only = 0

    def add_block(self, block: prev_parameters_blocks = None, name:str = ''):

        if block is None:
            block = prev_parameters_blocks(self)
            block._name = name if name else f"Block {self.nblocks+1}"
        else:
            assert isinstance(block, prev_parameters_blocks)

        self.blocks.append(block)

    def __init__(self, parent:"prev_sim2D"=None) -> None:

        self.parent = parent

        self._params = None

        # infos générales
        self._nb_timesteps = 1000  # nbre de pas de simulation à réaliser
        self._timestep_duration = 0.1  #durée souhaitée d'un pas de temps
        self._writing_frequency = 1.  #fréquence de sortie des résultats
        self._writing_mode = 0  #type de fréquence de sortie des résultats (en temps ou en pas)
        self._writing_type = 3  #format d'écriture des résultats (1 = texte, 2 = binaire, 3=csr)
        self._initial_cond_reading_mode = 2  #format de lecture des données (1 = texte, 2 = binaire, 3 = binaire par blocs)
        self._writing_force_onlyonestep = 0  #ecriture d'un seul résu ou pas

        # maillage fin
        self._fine_mesh_dx = 0.  #dx du maillage le + fin = maillage sur lequel sont données
        self._fine_mesh_dy = 0.  #dy    les caract de topo, frot,...
        self._fine_mesh_nbx = 0  #nbre de noeuds selon x du maillage le + fin
        self._fine_mesh_nby = 0  #nbre de noeuds selon y du maillage le + fin
        self._fine_mesh_origx = 0.  #coordonnées absolues inf droites de la matrice des données
        self._fine_mesh_origy = 0.  ##<(maillage le plus fin : dxfin et dyfin)

        self._fine_mesh_translx = 0.
        self._fine_mesh_transly = 0.

        self.strong_bc = prev_boundary_conditions(self)
        self.weak_bc_x = prev_boundary_conditions(self)
        self.weak_bc_y = prev_boundary_conditions(self)

        # stabilité et schéma
        self._scheme_rk = 0.3  #indicateur du type de schéma r-k
        self._scheme_cfl = 0.25 # nbre de courant souhaité

        # lecture du fichier de paramètresvncsouhaite=0.
        self._scheme_dt_factor = 100.  #facteur mult du pas de temps pour vérif a posteriori
        self._scheme_optimize_timestep = 1  #=1 si optimisation du pas de temps
        self._scheme_maccormack = 0  #mac cormack ou non

        # limiteurs
        self._scheme_limiter = 2  #0 si pas de limiteur, 1 si barth jesperson, 2 si venkatakrishnan, 3 si superbee, 4 si van leer, 5 si van albada, 6 si minmod
        self._scheme_k_venkatakrishnan = 1.  #k de venkatakrishnan et des limiteurs modifiés

        # constantes de calcul
        self._num_h_division = 1.e-4  #hauteur min de division
        self._num_h_min = 0.  #hauteur d'eau min sur 1 maille
        self._num_h_min_computed = 0.  #hauteur d'eau min sur 1 maille pour la calculer
        self._num_exp_epsq = 14  #epsilon relatif pour la dtm de q nul sur les bords

        # paramètres de calcul
        self._scheme_centered_slope = 2  #=2 si dérivées centrées, 1 sinon
        self._scheme_hmean_centered = 0  #pente centrée ou non
        self._num_latitude = 0.  #latitude pour le calcul de la force de coriolis

        # options
        self._mesher_only = 0  #1 si uniquement maillage
        self._mesher_remeshing = 0  #=1 si remaillage
        self._num_truncate = 0  #troncature des variables
        self._num_smoothing_friction = 0  #=1 si smoothing arithmétique, =2 si smoothing géométrique
        self._bc_unsteady = 0  #cl instationnaires ou pas

        # blocs
        self.blocks: list  #paramètres de blocs
        self.blocks = list()  #paramètres de blocs

        # Debug parameters
        self._tags_computation = 0 #
        self._extension_rate = 1 # Number of cells to extend the computation domain at each time step at the boundaries
        self._drying_mode = 0
        self._delete_unconnected_cells = 0 # Delete unconnected cells every time step
        self._global_friction_coefficient = 0. # Global friction coefficient
        self._non_erodible_area = 0     # Non-erodible area
        self._local_timestepping = 0    # Local time stepping

        # Collapsable buildings
        self._hmax_bat = 0. # hauteur max des batiments
        self._vmax_bat = 0. # vitesse max des batiments
        self._qmax_bat = 0. # vitesse max du vent

        # Stockage dans une liste des valeurs par défaut
        self._default_gen_par   = self._get_general_params()
        self._default_debug_par = self._get_debug_params()

        self._set_sim_params(toShow = False)

    def show(self, show_in_active_if_default = False):
        """ Show the parameters of the simulation in a WX frame """

        # Not necessary the right place to put this, but it's the only place where we can put it
        # for now.

        if self._params is None:
            self._set_sim_params(toShow = True)
            self._params.show_in_active_if_default = show_in_active_if_default
        else:
            if self._params.has_gui:
                self._params.show_in_active_if_default = show_in_active_if_default
                self._params.Populate()
                self._params.Show()

            else:
                self._params._set_gui(None, "Global parameters", ontop=True, to_read = False, DestroyAtClosing=False, toShow = True, full_style=True)
                self._params.show_in_active_if_default = show_in_active_if_default
                self._params.hide_selected_buttons()
                self._params.Populate()


    def is_like(self, other:"prev_parameters_simul") -> bool:
        """ Check if two prev_parameters_simul are similar """

        src_gen = self._get_general_params()
        src_dbg = self._get_debug_params()

        oth_gen = other._get_general_params()
        oth_dbg = other._get_debug_params()

        return src_gen == oth_gen and src_dbg == oth_dbg

    def copy(self, other:"prev_parameters_simul") -> None:
        """ Copy the parameters of another prev_parameters_simul """

        oth_gen = other._get_general_params()
        oth_dbg = other._get_debug_params()

        self._set_general_params(oth_gen)
        self._set_debug_params(oth_dbg)

        self.weak_bc_x = other.weak_bc_x
        self.weak_bc_y = other.weak_bc_y
        self.strong_bc = other.strong_bc

    def diff(self, other:"prev_parameters_simul") -> dict:
        """ Return the differences between two prev_parameters_simul """

        src_gen = self._get_general_params()
        src_dbg = self._get_debug_params()

        oth_gen = other._get_general_params()
        oth_dbg = other._get_debug_params()

        groups = self.gen_groups + self.debug_groups # Les fcts _get_groups firltrent les groupes inutiles --> autant passer par les variabes
        names  = self.gen_names + self.debug_names   # Les fcts _get_names filtrent les noms inutiles --> autant passer par les variabes

        ret = {}

        for curgroup, curname, src, oth in zip(groups, names, src_gen+src_dbg, oth_gen+oth_dbg):

            if src != oth:
                ret[(curgroup, curname)] = (src, oth)

        return ret

    def diff_print(self, other:"prev_parameters_simul") -> str:
        """ Return the differences between two prev_parameters_simul as a string """

        ret = self.diff(other)

        if not ret:
            return "No differences found"

        retstr = ""

        for (group, name), (src, oth) in ret.items():
            retstr += f"{group} - {name} : {src} -> {oth}\n"

        return retstr


    # Geometry
    # ********

    def set_params_geometry(self, dx:float, dy:float, nbx:int, nby:int, origx:float, origy:float, translx:float = 0., transly:float = 0.):
        """ Set the geometry parameters of the simulation. """

        assert isinstance(dx, (int, float)), f"dx must be a number, not {type(dx)}"
        assert isinstance(dy, (int, float)), f"dy must be a number, not {type(dy)}"
        assert isinstance(nbx, int), f"nbx must be an integer, not {type(nbx)}"
        assert isinstance(nby, int), f"nby must be an integer, not {type(nby)}"
        assert isinstance(origx, (int, float)), f"origx must be a number, not {type(origx)}"
        assert isinstance(origy, (int, float)), f"origy must be a number, not {type(origy)}"
        assert isinstance(translx, (int, float)), f"translx must be a number, not {type(translx)}"
        assert isinstance(transly, (int, float)), f"transly must be a number, not {type(transly)}"

        self._fine_mesh_dx = dx
        self._fine_mesh_dy = dy
        self._fine_mesh_nbx = nbx
        self._fine_mesh_nby = nby
        self._fine_mesh_origx = origx
        self._fine_mesh_origy = origy
        self._fine_mesh_translx = translx
        self._fine_mesh_transly = transly


    # Time/Iterations
    # ***************
    def set_params_time_iterations(self,
                                   nb_timesteps: int = 1000,
                                   optimize_timestep:bool = True,
                                   first_timestep_duration: float = 0.1,
                                   writing_frequency: Union[int,float] = 1,
                                   writing_mode: Literal['Iterations', 'Seconds', 0 ,1] = 0,
                                   writing_type: Literal['Binary compressed', 'Binary Full', 'Text', 1, 2, 3] = 3,
                                   initial_cond_reading_mode: Literal['Binary', 'Binary per blocks', 'Text', 0,1,2] = 2,
                                   writing_force_onlyonestep: bool = False):

        """
        Set the time/iterations parameters of the simulation.

        :param nb_timesteps: Number of timesteps to perform
        :param optimize_timestep: Optimize the timestep
        :param first_timestep_duration: Duration of the first timestep
        :param writing_frequency: Writing frequency of the results
        :param writing_mode: Writing mode of the results
        :param writing_type: Writing type of the results
        :param initial_cond_reading_mode: Initial condition reading mode
        :param writing_force_onlyonestep: Force writing only one step

        """

        assert isinstance(nb_timesteps, int), f"nb_timesteps must be an integer, not {type(nb_timesteps)}"
        assert isinstance(optimize_timestep, bool), f"optimize_timestep must be a boolean, not {type(optimize_timestep)}"
        assert isinstance(first_timestep_duration, (int, float)), f"first_timestep_duration must be a number, not {type(first_timestep_duration)}"
        assert isinstance(writing_frequency, (int, float)), f"writing_frequency must be a number, not {type(writing_frequency)}"
        assert writing_mode in (0, 1, 'Iterations', 'Seconds'), f"writing_mode must be 'Iterations', 'Seconds', 0 or 1, not {writing_mode}"
        assert writing_type in (1, 2, 3, 'Text', 'Binary Full', 'Binary compressed'), f"writing_type must be 'Text', 'Binary Full', 'Binary compressed', 1, 2 or 3, not {writing_type}"
        assert initial_cond_reading_mode in (0, 1, 2, 'Text', 'Binary', 'Binary per blocks'), f"initial_cond_reading_mode must be 'Text', 'Binary', 'Binary per blocks', 0, 1 or 2, not {initial_cond_reading_mode}"
        assert isinstance(writing_force_onlyonestep, bool), f"writing_force_onlyonestep must be a boolean, not {type(writing_force_onlyonestep)}"

        self._nb_timesteps = nb_timesteps
        self._timestep_duration = first_timestep_duration
        self._writing_frequency = writing_frequency
        self._writing_mode = 1 if writing_mode == 'Seconds' else 0
        self._writing_type = 1 if writing_type == 'Text' else 2 if writing_type == 'Binary Full' else 3
        self._initial_cond_reading_mode = 1 if initial_cond_reading_mode == 'Text' else 3 if initial_cond_reading_mode == 'Binary per blocks' else 2
        self._writing_force_onlyonestep = 1 if writing_force_onlyonestep else 0
        self._scheme_optimize_timestep = 1 if optimize_timestep else 0

    def get_params_time_iterations(self) -> dict:
        """ Get the time/iterations parameters of the simulation. """

        return {'nb_timesteps': self._nb_timesteps,
                'optimize_timestep': self._scheme_optimize_timestep,
                'first_timestep_duration': self._timestep_duration,
                'writing_frequency': self._writing_frequency,
                'writing_mode': 'Seconds' if self._writing_mode == 1 else 'Iterations',
                'writing_type': 'Text' if self._writing_type == 1 else 'Binary Full' if self._writing_type == 2 else 'Binary compressed',
                'initial_cond_reading_mode': 'Text' if self._initial_cond_reading_mode == 1 else 'Binary per blocks' if self._initial_cond_reading_mode == 3 else 'Binary',
                'writing_force_onlyonestep': self._writing_force_onlyonestep}

    def reset_params_time_iterations(self):
        """ Reset the time/iterations parameters of the simulation. """

        self._nb_timesteps = 1000
        self._timestep_duration = 0.1
        self._writing_frequency = 1
        self._writing_mode = 0
        self._writing_type = 3
        self._initial_cond_reading_mode = 2
        self._writing_force_onlyonestep = 0
        self._scheme_optimize_timestep = 1

    def check_params_time_iterations(self) -> tuple[bool, str]:
        """ Check the time/iterations parameters of the simulation. """

        ret = "\nTime/Iterations\n****************\n"
        valid = True

        if self._nb_timesteps <= 0:
            valid = False
            ret += _('Error : Number of timesteps is negative\n')

        if self._timestep_duration <= 0:
            valid = False
            ret += _('Error : Timestep duration is negative\n')

        if self._writing_frequency <= 0:
            valid = False
            ret += _('Error : Writing frequency is negative\n')

        if self._writing_mode not in (0, 1):
            valid = False
            ret += _('Error : Writing mode is not valid\n')

        if self._writing_type not in (1, 2, 3):
            valid = False
            ret += _('Error : Writing type is not valid\n')

        if self._initial_cond_reading_mode not in (0, 1, 2):
            valid = False
            ret += _('Error : Initial condition reading mode is not valid\n')

        if self._nb_timesteps > 10000 and self._writing_mode == 0:
            ret += _('Warning : Writing mode is in iterations but the number of timesteps is high -- Are you agree ?\n')

        return valid, ret


    # Temporal scheme
    # ***************

    def set_params_temporal_scheme(self,
                                   RungeKutta: Literal['RK21', 'RK22', 'RK31a', 'RK31b', 'RK31c', 'RK41a', 'RK41b', 'RK44', 'Euler'] = 0.3,
                                   CourantNumber: float = 0.25,
                                   dt_factor: float = 100.):
        """ Set the temporal scheme parameters of the simulation. """

        assert isinstance(RungeKutta, (str, float, int)), 'RungeKutta must be a string, float or integer'

        # 'Euler explicit = 1.0\nRunge-Kutta 22 = 0.5\nRunge-Kutta 21 = 0.3\nRunge-Kutta 31a = 3.0\nRunge-Kutta 31b = 3.3\nRunge-Kutta 31c = 3.6\nRunge-Kutta 41a = 4.0\nRunge-Kutta 41b = 4.5\nRunge-Kutta 44 = 5.0\n\nSee GESTION_RUNGE_KUTTA in the code for more details.')),

        if isinstance(RungeKutta, str):
            if RungeKutta.lower() == 'euler':
                self._scheme_rk = 1.0
            elif RungeKutta.lower() == 'rk21':
                self._scheme_rk = 0.3
            elif RungeKutta.lower() == 'rk22':
                self._scheme_rk = 0.5
            elif RungeKutta.lower() == 'rk31a':
                self._scheme_rk = 3.0
            elif RungeKutta.lower() == 'rk31b':
                self._scheme_rk = 3.3
            elif RungeKutta.lower() == 'rk31c':
                self._scheme_rk = 3.6
            elif RungeKutta.lower() == 'rk41':
                self._scheme_rk = 4.0
            elif RungeKutta.lower() == 'rk41b':
                self._scheme_rk = 4.5
            elif RungeKutta.lower() == 'rk44':
                self._scheme_rk = 5.0
        elif isinstance(RungeKutta, (float, int)):

            RunkeKutta = float(RungeKutta)

            if RungeKutta>=1.:
                assert RungeKutta in (1.0, 0.3, 0.5, 3.0, 3.3, 3.6, 4.0, 4.5, 5.0), 'RungeKutta must be 1.0, 0.3, 0.5, 3.0, 3.3, 3.6, 4.0, 4.5 or 5.0'

                self._scheme_rk = RungeKutta
            elif RungeKutta>0.:

                if RungeKutta not in [0.3, 0.5]:
                    logging.warning(f"RungeKutta is not a standard value, it is {RungeKutta}")

                self._scheme_rk = RungeKutta

            else:
                logging.error(f"RungeKutta must be a positive number, not {RungeKutta}")

        else:
            logging.error(f"RungeKutta must be a string, float or integer, not {type(RungeKutta)} -- Set RK21 by default")
            self._scheme_rk = 0.3

        assert isinstance(CourantNumber, float), 'CourantNumber must be a float'

        if CourantNumber > 0. and CourantNumber <= 1.:
            self._scheme_cfl = CourantNumber
        else:
            logging.error(f"CourantNumber must be a positive number and lower than 1., not {CourantNumber} -- Set 0.25 by default")
            self._scheme_cfl = 0.25

        assert isinstance(dt_factor, float), 'dt_factor must be a float'

        if dt_factor > 0.:
            self._scheme_dt_factor = dt_factor
        else:
            logging.error(f"dt_factor must be a positive number, not {dt_factor} -- Set 100. by default")
            self._scheme_dt_factor = 100.

    def get_params_temporal_scheme(self) -> dict:
        """ Get the temporal scheme parameters of the simulation. """

        return {'RungeKutta': self._scheme_rk,
                'CourantNumber': self._scheme_cfl,
                'dt_factor': self._scheme_dt_factor}

    def reset_params_temporal_scheme(self):
        """ Reset the temporal scheme parameters of the simulation. """

        self._scheme_rk = 0.3
        self._scheme_cfl = 0.25
        self._scheme_dt_factor = 100.

    def check_params_temporal_scheme(self) -> tuple[bool, str]:
        """ Check the temporal scheme parameters of the simulation. """

        ret = "\nTemporal scheme\n****************\n"
        valid = True

        if self._scheme_rk in (1.0, 0.3, 0.5, 3.0, 3.3, 3.6, 4.0, 4.5, 5.0):
            ret += _('Runge-Kutta is valid : {}\n'.format(self._scheme_rk))
        elif self._scheme_rk > 0. and self._scheme_rk < 1.:
            ret += _('Warning : Runge-Kutta is not a standard value, it is {}\n'.format(self._scheme_rk))
        else:
            valid = False
            ret += _('Error : Runge-Kutta is not valid, it is {}\n'.format(self._scheme_rk))

        if self._scheme_cfl > 0. and self._scheme_cfl <= 1.:
            ret += _('Courant number is valid : {}\n'.format(self._scheme_cfl))
        else:
            valid = False
            ret += _('Error : Courant number is not valid, it is {}\n'.format(self._scheme_cfl))

        if self._scheme_dt_factor > 0.:
            ret += _('dt factor is valid : {}\n'.format(self._scheme_dt_factor))
        else:
            valid = False

        return valid, ret



    # Buildings
    # *********

    def set_params_collapsible_building(self, hmax_bat: float = 7., vmax_bat: float = 2., qmax_bat: float = 7.):
        """
        Set the parameters for the collapsible buildings.

        """

        self._hmax_bat = hmax_bat
        self._vmax_bat = vmax_bat
        self._qmax_bat = qmax_bat

        logging.info(_('Do not forget to activate the collapsible buildings in at least one block'))

    def get_params_collapsible_building(self) -> dict:

        return {'hmax_bat': self._hmax_bat, 'vmax_bat': self._vmax_bat, 'qmax_bat': self._qmax_bat}

    def check_params_collapsible_building(self) -> tuple[bool, str]:
        """ Check the collapsible building  parameters. """

        ret = "\nCollapsible building (only global values -- activation depends on the block's param)\n********************\n"
        valid = True

        if self._hmax_bat<0.:
            valid = False
            ret += _('Error : Hmax is negative\n')
        else:
            ret += _('Hmax is valid : {}\n'.format(self._hmax_bat))

        if self._vmax_bat<0.:
            valid = False
            ret += _('Error : Vmax is negative\n')
        else:
            ret += _('Vmax is valid : {}\n'.format(self._vmax_bat))

        if self._qmax_bat<0.:
            valid = False
            ret += _('Error : Qmax is negative\n')
        else:
            ret += _('Qmax is valid : {}\n'.format(self._qmax_bat))

        return valid, ret




    def reset_all_boundary_conditions(self):
        """
        Resets strong as well as weak boundary conditions.
        """

        self.strong_bc.reset()
        self.weak_bc_x.reset()
        self.weak_bc_y.reset()

    def reset_blocks(self):
        self.blocks.clear()
        # self.nblocs = 0

    def setvaluesbc(self, event):

        k = 0
        for curbc in self.weak_bc_x.mybc:
            curbc.val = float(self.bcgridx.GetCellValue(k, 3))
            k += 1

        k = 0
        for curbc in self.weak_bc_y.mybc:
            curbc.val = float(self.bcgridy.GetCellValue(k, 3))
            k += 1

        dlg = wx.MessageDialog(None,
                               _('Do you want to save you .par file? \n A backup of the current file will be available in .par_back if needed.'),
                               style=wx.YES_NO)
        ret = dlg.ShowModal()

        if ret == wx.ID_YES:
            self.write_file()

        dlg.Destroy()

    def getvaluesx(self, event):
        for curmodel in self.mysimuls:
            if curmodel.checked:
                locmodel = curmodel

                curcol = 3
                if locmodel is self.parent:
                    curcol = 4

                k = 0
                for curbc in self.weak_bc_x.mybc:
                    x1, y1, x2, y2 = self.weak_bc_x.get_xy(curbc.i, curbc.j, 'x', True)

                    values1 = locmodel.get_values_from_xy(x1 - self._fine_mesh_dx / 2., y1)
                    values2 = locmodel.get_values_from_xy(x1 + self._fine_mesh_dx / 2., y1)

                    if values1[1][0] == '-' and values2[1][0] == '-':
                        self.bcgridx.SetCellValue(k, curcol, _('No neighbor !!'))
                    elif values1[1][0] == '-':
                        self.bcgridx.SetCellValue(k, curcol, str(values2[0][7]))
                        self.bcgridx.SetCellValue(k, 6, str(values2[0][0]))
                        self.bcgridx.SetCellValue(k, 7, str(values2[0][8]))
                    elif values2[1][0] == '-':
                        self.bcgridx.SetCellValue(k, curcol, str(values1[0][7]))
                        self.bcgridx.SetCellValue(k, 6, str(values1[0][0]))
                        self.bcgridx.SetCellValue(k, 7, str(values1[0][8]))
                    else:
                        self.bcgridx.SetCellValue(k, curcol, str((values1[0][7] + values2[0][7]) / 2.))
                        self.bcgridx.SetCellValue(k, 6, str((values1[0][0] + values2[0][0]) / 2.))
                        self.bcgridx.SetCellValue(k, 7, str((values1[0][8] + values2[0][8]) / 2.))
                    k += 1

    def getvaluesy(self, event):
        for curmodel in self.mysimuls:
            if curmodel.checked:
                locmodel = curmodel

                curcol = 3
                if locmodel is self.parent:
                    curcol = 4

                k = 0
                for curbc in self.weak_bc_y.mybc:
                    x1, y1, x2, y2 = self.weak_bc_y.get_xy(curbc.i, curbc.j, 'y', True)

                    values1 = locmodel.get_values_from_xy(x1, y1 - self._fine_mesh_dy / 2.)
                    values2 = locmodel.get_values_from_xy(x1, y1 + self._fine_mesh_dy / 2.)

                    if values1[1][0] == '-' and values2[1][0] == '-':
                        self.bcgridy.SetCellValue(k, curcol, _('No neighbor !!'))
                        self.bcgridy.SetCellValue(k, 6, '-')
                        self.bcgridy.SetCellValue(k, 7, '-')
                    elif values1[1][0] == '-':
                        self.bcgridy.SetCellValue(k, curcol, str(values2[0][7]))
                        self.bcgridy.SetCellValue(k, 6, str(values2[0][0]))
                        self.bcgridy.SetCellValue(k, 7, str(values2[0][8]))
                    elif values2[1][0] == '-':
                        self.bcgridy.SetCellValue(k, curcol, str(values1[0][7]))
                        self.bcgridy.SetCellValue(k, 6, str(values1[0][0]))
                        self.bcgridy.SetCellValue(k, 7, str(values1[0][8]))
                    else:
                        self.bcgridy.SetCellValue(k, curcol, str((values1[0][7] + values2[0][7]) / 2.))
                        self.bcgridy.SetCellValue(k, 6, str((values1[0][0] + values2[0][0]) / 2.))
                        self.bcgridy.SetCellValue(k, 7, str((values1[0][8] + values2[0][8]) / 2.))
                    k += 1

    def editing_bc(self, mysimuls):

        self.mysimuls = mysimuls
        self.myeditor = wx.Frame(None, id=wx.ID_ANY, title='BC editor')

        self.edit_bc = wx.Notebook(self.myeditor, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize)

        self.bcx = wx.Panel(self.edit_bc, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.bcy = wx.Panel(self.edit_bc, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)

        self.edit_bc.AddPage(self.bcx, _("Boundary conditions X"), True)
        self.edit_bc.AddPage(self.bcy, _("Boundary conditions Y"), True)

        self.bcgridx = CpGrid(self.bcx, wx.ID_ANY, style=wx.WANTS_CHARS | wx.TE_CENTER)
        self.bcgridx.CreateGrid(len(self.weak_bc_x.mybc), 8)

        self.bcgridy = CpGrid(self.bcy, wx.ID_ANY, style=wx.WANTS_CHARS | wx.TE_CENTER)
        self.bcgridy.CreateGrid(len(self.weak_bc_y.mybc), 8)

        gensizer = wx.BoxSizer(wx.VERTICAL)

        sizerbcx = wx.BoxSizer(wx.VERTICAL)
        sizerbcy = wx.BoxSizer(wx.VERTICAL)
        getvalx = wx.Button(self.bcx, id=wx.ID_ANY, label=_('Get Values X'))
        getvaly = wx.Button(self.bcy, id=wx.ID_ANY, label=_('Get Values Y'))

        sizerbcx.Add(getvalx, 1, wx.EXPAND, border=5)
        sizerbcx.Add(self.bcgridx, 1, wx.EXPAND)

        sizerbcy.Add(getvaly, 1, wx.EXPAND, border=5)
        sizerbcy.Add(self.bcgridy, 1, wx.EXPAND)

        getvalx.Bind(wx.EVT_BUTTON, self.getvaluesx)
        getvaly.Bind(wx.EVT_BUTTON, self.getvaluesy)

        setval = wx.Button(self.myeditor, id=wx.ID_ANY, label=_('Set Values'))
        setval.Bind(wx.EVT_BUTTON, self.setvaluesbc)

        self.bcx.SetSizer(sizerbcx)
        self.bcy.SetSizer(sizerbcy)

        gensizer.Add(setval, 1, wx.EXPAND | wx.ALL, border=5)
        gensizer.Add(self.edit_bc, 1, wx.EXPAND | wx.ALL)

        self.bcx.Layout()
        self.bcy.Layout()

        self.weak_bc_x.fillgrid(self.bcgridx)
        self.weak_bc_y.fillgrid(self.bcgridy)

        self.myeditor.SetSizer(gensizer)
        self.myeditor.Layout()
        self.myeditor.Show()

    def get_help(self, group, name):
        """ Récupère l'aide associée à un paramètre """

        self._set_sim_params()

        ret = self._params.get_help(group, name)

        if ret is None:

            self.blocks[0]._set_block_params()

            ret = self.blocks[0]._params.get_help(group, name)

            if ret is None:
                return _('No help available')
            else:
                ret = ['Block'] + ret

        else:

            ret = ['Global'] + ret

        return ret

    def is_global(self, group, name):
        """ Indique si un paramètre est global ou non """

        self._set_sim_params()

        if group in self.gen_groups and name in self.gen_names[name]:
            return True
        elif group in self.debug_groups and name in self.debug_names:
            return True
        else:
            return False

    def is_general(self, group, name):
        """ Indique si un paramètre est général ou non """

        self._set_sim_params()

        if group in self.gen_groups and name in self.gen_names:
            return True
        else:
            tmp_block = prev_parameters_blocks()
            if group in tmp_block.gen_groups and name in tmp_block.gen_names:
                return True
            else:
                return False

    def is_debug(self, group, name):
        """ Indique si un paramètre est de débogage ou non """

        self._set_sim_params()

        if group in self.debug_groups and name in self.debug_names:
            return True
        else:
            tmp_block = prev_parameters_blocks()
            if group in tmp_block.debug_groups and name in tmp_block.debug_names:
                return True
            else:
                return False

    def is_block(self, group, name):
        """ Indique si un paramètre est associé à un bloc ou non """

        tmp_block = prev_parameters_blocks()

        if group in tmp_block.gen_groups and name in tmp_block.gen_names:
            return True
        elif group in tmp_block.debug_groups and name in tmp_block.debug_names:
            return True
        else:
            return False

    def get_json_values(self, group, name):
        """ Récupère les valeurs possibles associées à un paramètre """

        self._set_sim_params()

        ret = self._params.get_json_values(group, name)

        if ret is None or ret == {}:
            self.blocks[0]._set_block_params()
            ret = self.blocks[0]._params.get_json_values(group, name)

        return ret

    def read_file(self, fn=''):
        """ Lecture du fichier de paramètres """

        if fn == '' and self.parent is None:
            return

        # MERGE Not sure about this
        if not exists(fn + '.par'):
            if fn == '':
                fn = self.parent.filenamegen

        if exists(fn + '.trl'):
            with open(fn + '.trl') as f:
                lines = f.read().splitlines()
                self._fine_mesh_translx = float(lines[1])
                self._fine_mesh_transly = float(lines[2])

        if exists(fn + '.par'):

            with open(fn + '.par') as f:
                lines = f.read().splitlines()

                # Lecture des PARAMETRES GLOBAUX
                # Durée de la simulation et résultats
                self._nb_timesteps = np.int64(float(lines[0]))  # nbre de pas de simulation à réaliser
                self._timestep_duration = float(lines[1])  # durée souhaitée d'un pas de temps
                self._writing_frequency = float(lines[2])  # fréquence de sortie des résultats
                self._writing_mode = int(lines[3])  # type de fréquence de sortie des résultats (en temps ou en pas)
                self._writing_type = int(lines[4])  # format d'écriture des résultats (1 = texte, 2 = binaire, 3=csr)
                self._initial_cond_reading_mode = int(lines[5])  # format de lecture des données (1 = texte, 2 = binaire, 3 = binaire par blocs)
                self._writing_force_onlyonestep = int(lines[6])  # ecriture d'un seul résu ou pas
                # maillage fin
                self._fine_mesh_dx = float(lines[7])  # dx du maillage le + fin = maillage sur lequel sont données
                self._fine_mesh_dy = float(lines[8])  # dy    les caract de topo, frot,...
                self._fine_mesh_nbx = int(lines[9])  # nbre de noeuds selon x du maillage le + fin
                self._fine_mesh_nby = int(lines[10])  # y
                self._fine_mesh_origx = float(lines[11])  # coordonnées absolues inf droites de la matrice des données
                self._fine_mesh_origy = float(lines[12])  # (maillage le plus fin : dxfin et dyfin)
                # conditions limites
                _bc_nb_strong = int(lines[13])  # nbre de cl fortes
                _impfbxgen = int(lines[14])  # nbre de cl faibles sur les bords x
                _impfbygen = int(lines[15])  # nbre de cl faibles sur les bords y
                # stabilité et schéma
                self._scheme_rk = float(lines[16])  # indicateur du type de schéma r-k
                self._scheme_cfl = float(lines[17])  # nbre de courant souhaité
                self._scheme_dt_factor = float(lines[18])  # facteur mult du pas de temps pour vérif a posteriori
                self._scheme_optimize_timestep = int(lines[19])  # =1 si optimisation du pas de temps
                self._scheme_maccormack = int(lines[20])  # mac cormack ou non
                # limiteurs
                self._scheme_limiter = int(lines[21])  # 0 si pas de limiteur, 1 si barth jesperson, 2 si venkatakrishnan
                # 3 si superbee, 4 si van leer, 5 si van albada, 6 si minmod
                self._scheme_k_venkatakrishnan = float(lines[22])  # k de venkatakrishnan et des limiteurs modifiés
                # constantes de calcul
                self._num_h_division = float(lines[23])  # hauteur min de division
                self._num_h_min = float(lines[24])  # hauteur d'eau min sur 1 maille
                self._num_h_min_computed = float(lines[25])  # hauteur d'eau min sur 1 maille pour la calculer
                self._num_exp_epsq = int(lines[26])  # epsilon relatif pour la dtm de q nul sur les bords
                # paramètres de calcul
                self._scheme_centered_slope = int(lines[27])  # =2 si dérivées centrées, 1 sinon
                self._scheme_hmean_centered = int(lines[28])  # pente centrée ou non
                self._num_latitude = float(lines[29])  # latitude pour le calcul de la force de coriolis
                # options
                self._mesher_only = int(lines[30])  # 1 si uniquement maillage
                self._mesher_remeshing = int(lines[31])  # =1 si remaillage
                self._num_truncate = int(lines[32])  # troncature des variables
                self._num_smoothing_friction = int(lines[33])  # =1 si smoothing arithmétique, =2 si smoothing géométrique
                self._bc_unsteady = int(lines[34])  # cl instationnaires ou pas
                # nbre de blocs
                nblocks = int(lines[35])  # nombre de blocs

                # allocation des espaces mémoire pour le stockage des param de blocs
                self.blocks:list[prev_parameters_blocks] = []

                # lecture des parametres propres aux blocs
                decal = NB_GLOB_GEN_PAR

                general_params_blocks = {}
                for i_block in range(nblocks):

                    curparambl = prev_parameters_blocks(parent = self)

                    general_params_blocks[i_block] = [lines[cur] for cur in range(decal,decal + NB_BLOCK_GEN_PAR)]
                    self.blocks.append(curparambl)

                    decal += NB_BLOCK_GEN_PAR

                self.strong_bc.read_file(lines[decal:decal + _bc_nb_strong], 'strongbc')
                decal += self.bc_nb_strong
                self.weak_bc_x.read_file(lines[decal:decal + _impfbxgen], 'x')
                decal += self.bc_nbx_weak
                self.weak_bc_y.read_file(lines[decal:decal + _impfbygen], 'y')
                decal += self.bc_nby_weak

                # lecture des paramètres debug globaux
                vdebug = []
                for i in range(NB_GLOB_DEBUG_PAR):
                    vdebug.append(float(lines[decal + i]))

                self._set_debug_params(vdebug)

                decal += NB_GLOB_DEBUG_PAR

                # lecture des paramètres debug par blocs
                for i_block in range(nblocks):

                    locdebug = []
                    for i in range(NB_BLOCK_DEBUG_PAR):
                        locdebug.append(float(lines[decal + i]))

                    self.blocks[i_block]._set_general_debug_params(general_params_blocks[i_block], locdebug)

                    decal += NB_BLOCK_DEBUG_PAR

                # lecture index des blocs calculés
                if vdebug[0]>0:
                    for idx in range(int(vdebug[0])):
                        idx_block = int(lines[decal])-1
                        self.blocks[idx_block].computed = True
                        decal+=1

                # lecture des noms de chaque bloc
                try:
                    for idx in range(nblocks):
                        self.blocks[idx]._name = lines[decal]
                        decal+=1
                except :
                    pass
        else:
            logging.warning(_('.par file not found !'))

    def write_file(self, fn=''):
        """Ecriture du fichier de paramètres"""

        if fn == '' and self.parent is None:
            return

        if fn == '':
            fn = self.parent.filenamegen

        fnback = fn + '.par_back'
        while exists(fnback):
            fnback += '_'

        from  pathlib import Path
        if Path(fn+".par").exists():
            shutil.copyfile(fn + '.par', fnback)

        with open(fn, 'w') as f:
            f.write('Even void, this file is necessary for the simulation\n')

        with open(fn + '.trl', 'w') as f:
            f.write(_('Translational coordinates to convert the world reference frame into a local reference frame and vice-versa - Block contours are expressed in local coordinates\n'))
            f.write('{}\n'.format(self._fine_mesh_translx))
            f.write('{}\n'.format(self._fine_mesh_transly))

        with open(fn + '.par', 'w') as f:
            # for i in range(14):
            #     f.write(mylines[i] + '\n')

            f.write('{}\n'.format(self._nb_timesteps))
            f.write('{}\n'.format(self._timestep_duration))
            f.write('{}\n'.format(self._writing_frequency))
            f.write('{}\n'.format(self._writing_mode))
            f.write('{}\n'.format(self._writing_type))
            f.write('{}\n'.format(self._initial_cond_reading_mode))
            f.write('{}\n'.format(self._writing_force_onlyonestep))
            # maillage fin
            f.write('{}\n'.format(self._fine_mesh_dx))
            f.write('{}\n'.format(self._fine_mesh_dy))
            f.write('{}\n'.format(self._fine_mesh_nbx))
            f.write('{}\n'.format(self._fine_mesh_nby))
            f.write('{}\n'.format(self._fine_mesh_origx))
            f.write('{}\n'.format(self._fine_mesh_origy))

            f.write('{}\n'.format(self.bc_nb_strong))
            f.write(str(self.bc_nbx_weak) + '\n')
            f.write(str(self.bc_nby_weak) + '\n')
            # stabilité et schéma
            f.write('{}\n'.format(self._scheme_rk))
            f.write('{}\n'.format(self._scheme_cfl))
            f.write('{}\n'.format(self._scheme_dt_factor))
            f.write('{}\n'.format(self._scheme_optimize_timestep))
            f.write('{}\n'.format(self._scheme_maccormack))
            # limiteurs
            f.write('{}\n'.format(self._scheme_limiter))
            # 3 si superbee, 4 si van leer, 5 si van albada, 6 si minmod
            f.write('{}\n'.format(self._scheme_k_venkatakrishnan))
            # constantes de calcul
            f.write('{}\n'.format(self._num_h_division))
            f.write('{}\n'.format(self._num_h_min))
            f.write('{}\n'.format(self._num_h_min_computed))
            f.write('{}\n'.format(self._num_exp_epsq))
            # paramètres de calcul
            f.write('{}\n'.format(self._scheme_centered_slope))
            f.write('{}\n'.format(self._scheme_hmean_centered))
            f.write('{}\n'.format(self._num_latitude))
            # options
            f.write('{}\n'.format(self._mesher_only))
            f.write('{}\n'.format(self._mesher_remeshing))
            f.write('{}\n'.format(self._num_truncate))
            f.write('{}\n'.format(self._num_smoothing_friction))
            f.write('{}\n'.format(self._bc_unsteady))
            # nbre de blocs
            f.write('{}\n'.format(self.nblocks))

            for curbloc in self.blocks:
                curbloc.write_file(f)

            for i in range(len(self.strong_bc.mybc)):
                curbc = self.weak_bc_x.mybc[i]
                f.write('{i},{j},{type},{val}\n'.format(i=str(curbc.i), j=str(curbc.j), type=str(curbc.ntype),
                                                        val=str(curbc.val)))

            for i in range(len(self.weak_bc_x.mybc)):
                curbc = self.weak_bc_x.mybc[i]
                f.write('{i},{j},{type},{val}\n'.format(i=str(curbc.i), j=str(curbc.j), type=str(curbc.ntype),
                                                        val=str(curbc.val)))
            for i in range(len(self.weak_bc_y.mybc)):
                curbc = self.weak_bc_y.mybc[i]
                f.write('{i},{j},{type},{val}\n'.format(i=str(curbc.i), j=str(curbc.j), type=str(curbc.ntype),
                                                        val=str(curbc.val)))

            vdebug = self._get_debug_params()

            vdebug[0]=self.nb_computed_blocks

            # paramètres debug globaux
            for curdebug in vdebug:
                f.write('{:g}\n'.format(curdebug))

            # paramètres debug par blocs
            for curbloc in self.blocks:
                curbloc.write_debug(f)

            # écriture des blocs à calculer
            for idx in range(self.nblocks):
                if self.blocks[idx].computed:
                    f.write('{}\n'.format(idx+1))

            # écriture des noms de chaque bloc
            for idx in range(self.nblocks):

                if self.blocks[idx]._name == '' or self.blocks[idx]._name is None:
                    # au cas où le nom n'a pas été défini
                    self.blocks[idx]._name = f"Block {idx+1}"

                if self.blocks[idx]._name[0]=='"':
                    f.write(self.blocks[idx]._name+'\n')
                else:
                    f.write('"'+self.blocks[idx]._name+'"\n')

    def add_weak_bc_x(self,
                      i: int,
                      j: int,
                      ntype: BCType_2D,
                      value: float):
        """
        Add a boundary condition  on a left vertical border of cell.
        i,j: coordinate of the cell where the left border must be set
             as a boundary. i,j are 1-based (grid coordinates.)
        """
        # FIXME float may not be correct, it should be `np.float32` to match
        # wolfarray's accuracy
        # FIXME Why do we accept "strongbc", isn't clfbx weak conditions ?
        # FIXME We should check that the BC is put at the border of
        # the computation domain, that may help the user to set its coordinates
        # right.
        assert i >= 1 and i <= self._fine_mesh_nbx, f"1 <= i:{i} <= {self._fine_mesh_nbx+1}"
        assert j >= 1 and j <= self._fine_mesh_nby, f"1 <= j:{j} <= {self._fine_mesh_nby+1}"
        self.weak_bc_x.add(i,j,ntype,value,orient="x")

    def add_weak_bc_y(self,
                      i: int,
                      j: int,
                      ntype: BCType_2D,
                      value: float):
        """
        Add a boundary condition  on a bottom horizontal border of cell.
        i,j: coordinate of the cell where the left border must be set
             as a boundary. i,j are 1-based (grid coordinates.)
        """
        # FIXME float may not be correct, it should be `np.float32` to match
        # wolfarray's accuracy
        # FIXME Why do we accept "strongbc", isn't clfbx weak conditions ?
        # FIXME We should check that the BC is put at the border of
        # the computation domain, that may help the user to set its coordinates
        # right.
        assert i >= 1 and i <= self._fine_mesh_nbx, f"1 <= i:{i} <= {self._fine_mesh_nbx+1}"
        assert j >= 1 and j <= self._fine_mesh_nby, f"1 <= j:{j} <= {self._fine_mesh_nby+1}"
        self.weak_bc_y.add(i,j,ntype,value,orient='y')

    def to_yaml(self):
        global_params =  f"""\
dxfin: {self._fine_mesh_dx} # dx du maillage le + fin = maillage sur lequel sont données
dxfin: {self._fine_mesh_dy} # dy    les caract de topo, frot,...
npas: {self._nb_timesteps} # nbre de pas de simulation à réaliser
dur: {self._timestep_duration} # durée souhaitée d'un pas de temps
noptpas: {self._scheme_optimize_timestep}  # =1 si optimisation du pas de temps
ntypefreq: {self._writing_mode} # type de fréquence de sortie des résultats (en temps ou en pas)
freq: {self._writing_frequency} # fréquence de sortie des résultats
ntypewrite: {self._writing_type} # format d'écriture des résultats (1 = texte, 2 = binaire, 3=csr)
ntyperead: {self._initial_cond_reading_mode} # format de lecture des données (1 = texte, 2 = binaire, 3 = binaire par blocs)
nun_seul_resu: {self._writing_force_onlyonestep} # ecriture d'un seul résu ou pas
nblocs: {self.nblocs} # nombre de blocs
impfbxgen: {self.bc_nbx_weak} # nbre de cl faibles sur les bords x
impfbygen: {self.bc_nby_weak} # nbre de cl faibles sur les bords y
ponderation: {self._scheme_rk} # indicateur du type de schéma r-k
nxfin: {self._fine_mesh_nbx} #
nyfin: {self._fine_mesh_nby} #
xminfin: {self._fine_mesh_origx} # coordonnées absolues inf droites de la matrice des données
yminfin: {self._fine_mesh_origy} # ??? AKA origx/origy
translx: {self._fine_mesh_translx} # ??? To Lamberts coordinates
transly: {self._fine_mesh_transly}
# conditions limites
impfgen: {self.bc_nb_strong} # nbre de cl fortes
impfbxgen: {self.bc_nbx_weak} # nbre de cl faibles sur les bords x
impfbygen: {self.bc_nby_weak} # nbre de cl faibles sur les bords y
# stabilité et schéma
vncsouhaite: {self._scheme_cfl} # nbre de courant souhaité
mult_dt: {self._scheme_dt_factor}  # facteur mult du pas de temps pour vérif a posteriori
nmacc: {self._scheme_maccormack} # mac cormack ou non
# limiteurs
ntyplimit: {self._scheme_limiter} # 0 si pas de limiteur, 1 si barth jesperson, 2 si venkatakrishnan
# 3 si superbee, 4 si van leer, 5 si van albada, 6 si minmod
vkvenka: {self._scheme_k_venkatakrishnan} # k de venkatakrishnan et des limiteurs modifiés
# constantes de calcul
vminhdiv: {self._num_h_division} # hauteur min de division
vminh: {self._num_h_min} # hauteur d'eau min sur 1 maille
vminh2: {self._num_h_min_computed} # hauteur d'eau min sur 1 maille pour la calculer
nepsrel: {self._num_exp_epsq} # epsilon relatif pour la dtm de q nul sur les bords
# paramètres de calcul
nderdec: {self._scheme_centered_slope} # =2 si dérivées centrées, 1 sinon
npentecentree: {self._scheme_hmean_centered} # pente centrée ou non
vlatitude: {self._num_latitude} # latitude pour le calcul de la force de coriolis
# options
mailonly: {self._mesher_only} # 1 si uniquement maillage
nremaillage: {self._mesher_remeshing} # =1 si remaillage
ntronc: {self._num_truncate} # troncature des variables
nsmooth: {self._num_smoothing_friction} # =1 si smoothing arithmétique, =2 si smoothing géométrique
nclinst: {self._bc_unsteady} # cl instationnaires ou pas
"""

        bloc_params=[]
        for nbblocs in range(self.nblocs):
            p = self.blocks[nbblocs]
            bloc_params.append("blocks_params:")
            bloc_params.append(f"   - nconflit: {p._conflict_resolution} #gestion des conflits (0), ou juste en centré (1) ou pas (2)")
            bloc_params.append(f"     ntraitefront: {p._treating_frontier} #type de traitement des frontières (1 = rien, 0 = moyenne et décentrement unique)")

        return global_params + "\n".join(bloc_params)

    def apply_changes_to_memory(self):
        """
        Apply the changes made in the GUI to the memory.

        This method is called when the user clicks on the "Apply" button in the GUI.

        Effective transfer will be done in the _callback_param_from_gui method.

        """

        if self._params is None:
            logging.error(_('No GUI block parameters available'))
        else:
            # Transfer the parameters from the GUI to the memory in the PyParams instance
            self._params.apply_changes_to_memory()

    def _callback_param_from_gui(self):
        """
        Set the parameters from the Wolf_Param object.

        Callback routine set in the Wolf_Param object.

        """

        if self._params is None:
            logging.error(_('No GUI block parameters available'))
        else:
            # Transfer the parameters from the memory to the prev_parameters_simul instance
            self._set_general_params([self._params[(self.gen_groups[i], self.gen_names[i])] for i in range(NB_GLOB_GEN_PAR)])
            debug = []
            for curgroup, curname in zip(self.debug_groups, self.debug_names):
                if curgroup != NOT_USED:
                    debug.append(self._params[(curgroup, curname)])
                else:
                    debug.append(0.)

            self._set_debug_params(debug)

    def _set_sim_params(self, toShow = True) -> Wolf_Param:
        """
        Création d'un objet Wolf_Param et, si souhaité, affichage des paramètres via GUI wxPython

        :param toShow: booléen indiquant si les paramètres doivent être affichés via GUI wxPython
        """

        if self._params is None:
            self._params = Wolf_Param(parent=None,
                                          title=_(' Parameters'),
                                          to_read=False,
                                          withbuttons=True,
                                          DestroyAtClosing=True,
                                          toShow=toShow,
                                          init_GUI=toShow)

            self._params.set_callbacks(self._callback_param_from_gui, self._callback_param_from_gui)

        self._fillin_general_parameters()
        self._fillin_debug_parameters()

        self._params.Populate()

    def _get_debug_params(self) -> list:
        return [self.nb_computed_blocks,            # 1
                self._tags_computation,           # 2
                self._extension_rate,               # 3
                self._drying_mode,                  # 4
                self._delete_unconnected_cells,     # 5
                self._global_friction_coefficient,  # 6
                self._non_erodible_area,            # 7
                self._hmax_bat,                     # 8
                self._vmax_bat,                     # 9
                self._qmax_bat,                     # 10
                0,                                  # 11
                0,                                  # 12
                0,                                  # 13
                0,                                  # 14
                0,                                  # 15
                0,                                  # 16
                0,                                  # 17
                0,                                  # 18
                0,                                  # 19
                0,                                  # 20
                0,                                  # 21
                0,                                  # 22
                0,                                  # 23
                0,                                  # 24
                0,                                  # 25
                0,                                  # 26
                0,                                  # 27
                0,                                  # 28
                0,                                  # 29
                0,                                  # 30
                0,                                  # 31
                0,                                  # 32
                0,                                  # 33
                0,                                  # 34
                0,                                  # 35
                0,                                  # 36
                0,                                  # 37
                0,                                  # 38
                0,                                  # 39
                0,                                  # 40
                0,                                  # 41
                0,                                  # 42
                0,                                  # 43
                0,                                  # 44
                0,                                  # 45
                0,                                  # 46
                0,                                  # 47
                0,                                  # 48
                0,                                  # 49
                0,                                  # 50
                0,                                  # 51
                0,                                  # 52
                0,                                  # 53
                0,                                  # 54
                0,                                  # 55
                0,                                  # 56
                0,                                  # 57
                0,                                  # 58
                0,                                  # 59
                self._local_timestepping]           # 60

    def _set_debug_params(self, values:list):

        assert len(values)==NB_GLOB_DEBUG_PAR, "Bad length of values"

        for i in range(NB_GLOB_DEBUG_PAR):
            curgroup = self.debug_groups[i]
            curparam = self.debug_names[i]

            if curgroup != NOT_USED:
                if self._params.get_param_dict(curgroup, curparam)[key_Param.TYPE] == Type_Param.Float:
                    values[i] = float(values[i])
                else:
                    values[i] = int(values[i])
            else:
                values[i] = 0

        # debug 1 -- not used beacause calculated -- nbre de blocs calculés
        self._tags_computation = values[1]  # 1 si calcul avec balises
        self._extension_rate = values[2]  # taux d'extension
        self._drying_mode = values[3]  # mode de gestion de l'assèchement
        self._delete_unconnected_cells = values[4]  # suppression des mailles non connectées
        self._global_friction_coefficient = values[5]  # coefficient de frottement global
        self._non_erodible_area = values[6]  # gestion des surfaces non érodables
        self._hmax_bat = values[7]  # hauteur max
        self._vmax_bat = values[8]  # vitesse max
        self._qmax_bat = values[9]  # débit max
        self._local_timestepping = values[59]

        # FIXME debug 11 -> 59 not used

        # This call will update the GUI if exists
        self._set_sim_params()

    def _get_general_params(self) -> list:
        """ Liste des 36 paramètres généraux -- NB_GLOB_GEN_PAR"""

        return [self._nb_timesteps,
                self._timestep_duration,
                self._writing_frequency,
                self._writing_mode,
                self._writing_type,
                self._initial_cond_reading_mode,
                self._writing_force_onlyonestep,
                self._fine_mesh_dx,
                self._fine_mesh_dy,
                self._fine_mesh_nbx,
                self._fine_mesh_nby,
                self._fine_mesh_origx,
                self._fine_mesh_origy,
                self.bc_nb_strong,
                self.bc_nbx_weak,
                self.bc_nby_weak,
                self._scheme_rk,
                self._scheme_cfl,
                self._scheme_dt_factor,
                self._scheme_optimize_timestep,
                self._scheme_maccormack,
                self._scheme_limiter,
                self._scheme_k_venkatakrishnan,
                self._num_h_division,
                self._num_h_min,
                self._num_h_min_computed,
                self._num_exp_epsq,
                self._scheme_centered_slope,
                self._scheme_hmean_centered,
                self._num_latitude,
                self._mesher_only,
                self._mesher_remeshing,
                self._num_truncate,
                self._num_smoothing_friction,
                self._bc_unsteady,
                self.nblocks]

    def _set_general_params(self, values:list):
        """ Définition des 36 paramètres généraux sur base d'une liste de valeurs """
        assert len(values)==NB_GLOB_GEN_PAR, "Bad length of values"

        for i in range(NB_GLOB_GEN_PAR):
            curgroup = self.gen_groups[i]
            curparam = self.gen_names[i]

            if curgroup != NOT_USED:
                if self._params.get_param_dict(curgroup, curparam)[key_Param.TYPE] == Type_Param.Float:
                    values[i] = float(values[i])
                else:
                    values[i] = int(values[i])
            else:
                values[i] = 0

        self._nb_timesteps = values[0]
        self._timestep_duration = values[1]
        self._writing_frequency = values[2]
        self._writing_mode = values[3]
        self._writing_type = values[4]
        self._initial_cond_reading_mode = values[5]
        self._writing_force_onlyonestep = values[6]
        self._fine_mesh_dx = values[7]
        self._fine_mesh_dy = values[8]
        self._fine_mesh_nbx = values[9]
        self._fine_mesh_nby = values[10]
        self._fine_mesh_origx = values[11]
        self._fine_mesh_origy = values[12]
        # self.bc_nb_strong = values[13]
        # self.bc_nbx_weak = values[14]
        # self.bc_nby_weak = values[15]
        self._scheme_rk = values[16]
        self._scheme_cfl = values[17]
        self._scheme_dt_factor = values[18]
        self._scheme_optimize_timestep = values[19]
        self._scheme_maccormack = values[20]
        self._scheme_limiter = values[21]
        self._scheme_k_venkatakrishnan = values[22]
        self._num_h_division = values[23]
        self._num_h_min = values[24]
        self._num_h_min_computed = values[25]
        self._num_exp_epsq = values[26]
        self._scheme_centered_slope = values[27]
        self._scheme_hmean_centered = values[28]
        self._num_latitude = values[29]
        self._mesher_only = values[30]
        self._mesher_remeshing = values[31]
        self._num_truncate = values[32]
        self._num_smoothing_friction = values[33]
        self._bc_unsteady = values[34]
        # self.nblocks = values[35]

        # This call will update the GUI if exists
        self._set_sim_params()

    def _fillin_general_parameters(self):
        """
        General parameters

        Create list of groups ans parameter names to be used in the GUI/Wolf_Params object

        :remark The order of the parameters is important

        """

        if self._params is None:
            logging.error(_('No parameters stock available'))
            return

        myparams = self._params

        self.gen_groups=[]
        self.gen_names=[]

        active_vals = self._get_general_params()

        # 1
        idx_gen = 1
        self.gen_groups.append(_('Duration of simulation'))
        self.gen_names.append(_('Total steps'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Total number of time steps (Integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json(fullcomment=_('Total number of time steps to be computed.\nIt is not a total time duration.\nYou must choose it large enough to reach the desired time duration.\nThe simulation will end when the total number of steps is reached.')),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 2
        idx_gen+=1
        self.gen_groups.append(_('Duration of simulation'))
        self.gen_names.append(_('Time step'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Fixed time step value (or at least the first one) [s] (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 3
        idx_gen+=1
        self.gen_groups.append(_('Results'))
        self.gen_names.append(_('Writing interval'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Writing frequency [step] or [s] (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json(fullcomment=_('Frequency of writing results in the output files.\nIt can be expressed in number of steps or in seconds.\nDepending on the value of the --Writing interval mode-- parameter.')),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 4
        idx_gen+=1
        self.gen_groups.append(_('Results'))
        self.gen_names.append(_('Writing interval mode'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Writing mode (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('Number of steps'):0,
                                            _('Time interval'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 5
        idx_gen+=1
        self.gen_groups.append(_('Results'))
        self.gen_names.append(_('Writing mode'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Writing mode on disk (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('Text'):1,
                                            _('Binary Full'):2,
                                            _('Binary Compressed'):3}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 6
        idx_gen+=1
        self.gen_groups.append(_('Initial conditions'))
        self.gen_names.append(_('Reading mode'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('File reading mode (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('Text'):1,
                                            _('Binary Full'):2,
                                            _('Binary by Blocks'):3}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 7
        idx_gen+=1
        self.gen_groups.append(_('Results'))
        self.gen_names.append(_('Only one result'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Keep only one result (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 8
        idx_gen+=1
        self.gen_groups.append(_('Geometry'))
        self.gen_names.append(_('Dx'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Spatial resolution along X [m] (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 9
        idx_gen+=1
        self.gen_groups.append(_('Geometry'))
        self.gen_names.append(_('Dy'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Spatial resolution along Y [m] (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 10
        idx_gen+=1
        self.gen_groups.append(_('Geometry'))
        self.gen_names.append(_('Nx'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Number of node along X [-] (Integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 11
        idx_gen+=1
        self.gen_groups.append(_('Geometry'))
        self.gen_names.append(_('Ny'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Number of nodes along Y [-] (Integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 12
        idx_gen+=1
        self.gen_groups.append(_('Geometry'))
        self.gen_names.append(_('Origin X'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('X coordinate of the lower-left corner [m] (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 13
        idx_gen+=1
        self.gen_groups.append(_('Geometry'))
        self.gen_names.append(_('Origin Y'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Y coordinate of the lower-left corner [m] (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 14
        idx_gen+=1
        self.gen_groups.append(_('Boundary conditions'))
        self.gen_names.append(_('Nb strong BC (not editable)'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Number of strong boundary conditions (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 15
        idx_gen+=1
        self.gen_groups.append(_('Boundary conditions'))
        self.gen_names.append(_('Nb weak BC X (not editable)'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Number of weak boundary conditions along X (Integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 16
        idx_gen+=1
        self.gen_groups.append(_('Boundary conditions'))
        self.gen_names.append(_('Nb weak BC Y (not editable)'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[15],
                          type='Integer',
                          comment=_('Number of weak boundary conditions along Y (Integer) - default = {}'.format(self._default_gen_par[15])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 17
        idx_gen+=1
        self.gen_groups.append(_('Temporal scheme'))
        self.gen_names.append(_('Runge-Kutta'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Choice of Runge-Kutta scheme (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json(fullcomment=_('Euler explicit = 1.0\nRunge-Kutta 22 = 0.5\nRunge-Kutta 21 = 0.3\nRunge-Kutta 31a = 3.0\nRunge-Kutta 31b = 3.3\nRunge-Kutta 31c = 3.6\nRunge-Kutta 41a = 4.0\nRunge-Kutta 41b = 4.5\nRunge-Kutta 44 = 5.0\n\nSee GESTION_RUNGE_KUTTA in the code for more details.')),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 18
        idx_gen+=1
        self.gen_groups.append(_('Temporal scheme'))
        self.gen_names.append(_('Courant number'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Courant number for optimizing time step (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 19
        idx_gen+=1
        self.gen_groups.append(_('Temporal scheme'))
        self.gen_names.append(_('Factor for verification'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Multiplication factor to verify the current time step (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json(fullcomment=_('The optimized time step is computed at the end of each step.\nIt is then multiplied by this factor to verify if it is still valid.\nIf not, the time step is reduced and the computation is redone.')),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 20
        idx_gen+=1
        self.gen_groups.append(_('Temporal scheme'))
        self.gen_names.append(_('Optimized time step'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Optimize the time step or not (Integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 21
        idx_gen+=1
        self.gen_groups.append(_('Temporal scheme'))
        self.gen_names.append(_('Mac Cormack (deprecated)'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Use Mac Cormack strategy (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('No'):0}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 22
        idx_gen+=1
        self.gen_groups.append(_('Spatial scheme'))
        self.gen_names.append(_('Limiter type'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Limiter type for linear reconstruction (Integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('None'):0,
                                            _('Barth-Jesperson'):1,
                                            _('Venkatakrishnan'):2,
                                            _('Superbee'):3,
                                            _('Van Leer'):4,
                                            _('Van Albada'):5,
                                            _('Minmod'):6}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 23
        idx_gen+=1
        self.gen_groups.append(_('Spatial scheme'))
        self.gen_names.append(_('Venkatakrishnan k'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Venkatakrishnan parameter k - Tolerance (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 24
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('Water depth min for division'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Minimal water depth used for division [m] (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 25
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('Water depth min'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Minimal water depth everywhere [m] (Float) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 26
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('Water depth min to compute'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Minimal water depth to compute the node [m] (Integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 27
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('Exponent Q null on borders'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Power of ten to compute null discharge (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json(fullcomment=_('The discharge is considered as null if its absolute value is lower than 10^(-n) m³/s.\nThis parameter is used to compute the null discharge on the borders of the domain during splitting phase\nIf 0, the code will consider 14.')),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 28
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('Reconstruction slope mode'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Computing reconstruction slope as centered or non-centered (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('Centered'):2,
                                            _('Non-centered'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 29
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('H computation mode (deprecated)'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Compute H as node value or ratio of balances in the elevation slope term (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('Ratio'):0,
                                            _('Node'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 30
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('Latitude position'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Float',
                          comment=_('Latitude for Coriolis effect (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 31
        idx_gen+=1
        self.gen_groups.append(_('Mesher'))
        self.gen_names.append(_('Mesh only'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('During the execution of the Fortran code, compute mesh and stop (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 32
        idx_gen+=1
        self.gen_groups.append(_('Mesher'))
        self.gen_names.append(_('Remeshing mode'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Remeshing (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json(fullcomment=_('If greater than 0, the code will remesh the domain regarding the ".int" file.\nIf 0, the block sizes will be used to compute the mesh.')),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 33
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('Troncature (deprecated)'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Ignoring a few digits from numerical values (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 34
        idx_gen+=1
        self.gen_groups.append(_('Numerical options'))
        self.gen_names.append(_('Smoothing mode (deprecated)'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Smoothing the friction term on neighbors cells (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('No'):0,
                                            _('Arithmetic mean'):1,
                                            _('Geometric mean'):2,}),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 35
        idx_gen+=1
        self.gen_groups.append(_('Boundary conditions'))
        self.gen_names.append(_('Unsteady BC'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Unsteady boundary conditions or not (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1},
                                           fullcomment=_('See ".cli" file and "DONNEES_INST" in the code for more details.')),
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

        # 36
        idx_gen+=1
        self.gen_groups.append(_('Mesher'))
        self.gen_names.append(_('Number of blocks (not editable)'))
        myparams.addparam(groupname=self.gen_groups[-1],
                          name=self.gen_names[-1],
                          value=self._default_gen_par[idx_gen-1],
                          type='Integer',
                          comment=_('Number of blocks (integer) - default = {}'.format(self._default_gen_par[idx_gen-1])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.gen_groups[-1],self.gen_names[-1])] = active_vals[idx_gen-1]

    def _fillin_debug_parameters(self):
        """
        Debug parameters

        Create list of groups ans parameter names to be used in the GUI/Wolf_Params object

        :remark The order of the parameters is important
        """

        if self._params is None:
            logging.error(_('No block parameters available'))
            return

        myparams = self._params

        #DEBUG
        self.debug_groups = []
        self.debug_names = []
        active_debug = self._get_debug_params()

        # DEBUG 1
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('1'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Integer',
        #                   comment=_('Choice of turbulence model (Integer) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=new_json({_('No'):0,
        #                                     _('Smagorinski model (wo added equation)'):1,
        #                                     _('Fisher model (wo added equation)'):2,
        #                                     _('k-eps model (with 2 added equations)'):3,
        #                                     _('k model (with 1 added equation)'):4,
        #                                     _('Integrated k-eps model (with 2 added equations)'):6,
        #                                     }, fullcomment='If Smagorinski or Fisher model is selected, you must set alpha coefficient > 0.\nFisher is independant of the spatial resolution\nSmagorinski is dependant of the spatial resolution'),
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 2
        self.debug_groups.append(_('Computation domain'))
        self.debug_names.append(_('Using tags'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Using tags to compute some blocks (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('No'):0,
                                            _('Yes'):1}),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 3
        self.debug_groups.append(_('Computation domain'))
        self.debug_names.append(_('Strip width for extension'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Number of cells to be used when extending the calculation domain at borders (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='Set -1 to automatically adapt to RK scheme.\n0 will be converted to 1 by the Fortran code.',),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 4
        self.debug_groups.append(_('Spatial scheme'))
        self.debug_names.append(_('Wetting-Drying mode'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('How compute wetting-drying phase? (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json({_('None'):0,
                                            _('Simple'):1,
                                            _('Iterative'):-1}),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 5
        self.debug_groups.append(_('Computation domain'))
        self.debug_names.append(_('Delete unconnected cells every'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Delete unconnected cells every time steps (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 6
        self.debug_groups.append(_('Friction'))
        self.debug_names.append(_('Global friction coefficient'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Global friction coefficient instead of the ".frot" array (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 7
        self.debug_groups.append(_('Spatial scheme'))
        self.debug_names.append(_('Non-erodible area'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Integer',
                          comment=_('Number of iterations to limit erosion (Integer) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment='If lower than 0, the limiter is iteratively applied until convergence or n steps.\nIf 0, the limiter is not applied.\nIf greater than 0, the limiter is applied a fixed number of times.'),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 8
        self.debug_groups.append(_('Collapsible buildings'))
        self.debug_names.append(_('H max'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Maximum water depth (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 9
        self.debug_groups.append(_('Collapsible buildings'))
        self.debug_names.append(_('V max'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Maximum velocity (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 10
        self.debug_groups.append(_('Collapsible buildings'))
        self.debug_names.append(_('Q max'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Maximum discharge (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=None,
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 11
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('11'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 12
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('12'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 13
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('13'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 14
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('14'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 15
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('15'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 16
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('16'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 17
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('17'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 18
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('18'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 19
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('19'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 20
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('20'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 21
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('21'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 22
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('22'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 23
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('23'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 24
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('24'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 25
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('25'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 26
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('26'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 27
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('27'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 28
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('28'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 29
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('29'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 30
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('30'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 31
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('31'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 32
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('32'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 33
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('33'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 34
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('34'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 35
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('35'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 36
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('36'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 37
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('37'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 38
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('38'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 39
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('39'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 40
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('40'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 41
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('41'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 42
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('42'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 43
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('43'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 44
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('44'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 45
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('45'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 46
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('46'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 47
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('47'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 48
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('48'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 49
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('49'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 50
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('50'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 51
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('51'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 52
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('52'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 53
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('53'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 54
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('54'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 55
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('55'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 56
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('56'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 57
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('57'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 58
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('58'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 59
        self.debug_groups.append(NOT_USED)
        self.debug_names.append(_('59'))
        idx = len(self.debug_groups)-1

        # myparams.addparam(groupname=self.debug_groups[idx],
        #                   name=self.debug_names[idx],
        #                   value=self._default_debug_par[idx],
        #                   type='Float',
        #                   comment=_(' (Float) - default = {}'.format(self._default_debug_par[idx])),
        #                   jsonstr=None,
        #                   whichdict='Default')

        # myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        # DEBUG 60
        self.debug_groups.append(_('Temporal scheme'))
        self.debug_names.append(_('Local time step factor'))
        idx = len(self.debug_groups)-1

        myparams.addparam(groupname=self.debug_groups[idx],
                          name=self.debug_names[idx],
                          value=self._default_debug_par[idx],
                          type='Float',
                          comment=_('Local time step (Float) - default = {}'.format(self._default_debug_par[idx])),
                          jsonstr=new_json(fullcomment=_('If greater than 0, a local time step is calculated.\nThe used time step is the minimum between this local step and the global minimum multiplied by this factor.')),
                          whichdict='Default')

        myparams[(self.debug_groups[idx],self.debug_names[idx])] = active_debug[idx]

        return self._params

    def _get_groups(self) -> list[str]:
        """ Retourne la liste des groupes de paramètres """

        unique_groups = list(set(self.gen_groups + self.debug_groups))

        if NOT_USED in unique_groups:
            unique_groups.remove(NOT_USED)

        unique_groups.sort()

        return unique_groups

    def _get_param_names(self) -> list[str]:
        """ Retourne la liste des noms de paramètres """

        names = []
        for curgroup, curname in zip(self.gen_groups, self.gen_names):
            if curgroup != NOT_USED:
                names.append(curname)

        for curgroup, curname in zip(self.debug_groups, self.debug_names):
            if curgroup != NOT_USED:
                names.append(curname)

        names.sort()

        return names

    def _get_groups_and_names(self, sort = True) -> list[tuple[str,str]]:
        """ Retourne la liste des couples (group, name) """

        group_names = [(self.gen_groups[i], self.gen_names[i]) for i in range(36) if self.gen_groups[i] != NOT_USED] + [(self.debug_groups[i], self.debug_names[i]) for i in range(NB_GLOB_DEBUG_PAR) if self.debug_groups[i] != NOT_USED]

        if sort:
            group_names.sort(key=lambda x: x[0])

        return group_names

    def get_active_params(self) -> tuple[dict, dict]:
        """ Retourne les paramètres qui sont différents des valeurs par défaut """

        active_params = {}

        _genpar = self._get_general_params()
        for i in range(23):
            if self.gen_groups[i] != NOT_USED:
                if self._default_gen_par[i] != _genpar[i]:
                    active_params[(self.gen_groups[i], self.gen_names[i])] = _genpar[i]

        _dbgpar = self._get_debug_params()
        for i in range(NB_GLOB_DEBUG_PAR):
            if self.debug_groups[i] != NOT_USED:
                if self._default_debug_par[i] != _dbgpar[i]:
                    active_params[(self.debug_groups[i], self.debug_names[i])] = _dbgpar[i]

        active_params = {k: v for k, v in sorted(active_params.items(), key=lambda item: item[0])}

        active_params2={}
        for k,v in active_params.items():
            if k[0] not in active_params2.keys():
                active_params2[k[0]]={}
            active_params2[k[0]][k[1]]=v

        return active_params, active_params2

    def get_all_params(self) -> tuple[dict, dict]:
        """ Retourne tous les paramètres, y compris les valeurs par défaut """

        all_params = {}

        _genpar = self._get_general_params()
        for i in range(23):
            if self.gen_groups[i] != NOT_USED:
                all_params[(self.gen_groups[i], self.gen_names[i])] = _genpar[i]

        _dbgpar = self._get_debug_params()
        for i in range(NB_GLOB_DEBUG_PAR):
            if self.debug_groups[i] != NOT_USED:
                all_params[(self.debug_groups[i], self.debug_names[i])] = _dbgpar[i]

        all_params = {k: v for k, v in sorted(all_params.items(), key=lambda item: item[0])}

        all_params2={}
        for k,v in all_params.items():
            if k[0] not in all_params2.keys():
                all_params2[k[0]]={}
            all_params2[k[0]][k[1]]=v

        return all_params, all_params2

    def get_active_params_extended(self) -> dict:
        """ Retourne tous les paramètres actifs aisi que ceux des blocs dans une clé spécifique à chaque bloc """

        tmp, active_params = self.get_active_params()

        for i, block in enumerate(self.blocks):
            tmp, active_params[f'Block {i}'] = block.get_active_params()

        return active_params

    def get_all_params_extended(self) -> dict:
        """ Retourne tous les paramètres aisi que ceux des blocs dans une clé spécifique à chaque bloc """

        tmp, all_params = self.get_all_params()

        for i, block in enumerate(self.blocks):
            tmp, all_params[f'Block {i+1}'] = block.get_all_params()

        return all_params

    def get_active_params_block(self, i_block:int) -> dict:
        """ Retourne les paramètres actifs du bloc i_block (1-based) """

        if i_block <= 0 and i_block > len(self.blocks):
            logging.error(_('Block number out of range'))
            return {}

        block = self.blocks[i_block-1]
        tmp, active_params = block.get_active_params()

        return active_params

    def get_all_params_block(self, i_block:int) -> dict:
        """ Retourne tous les paramètres du bloc i_block (1-based) """

        if i_block <= 0 and i_block > len(self.blocks):
            logging.error(_('Block number out of range'))
            return {}

        block = self.blocks[i_block-1]
        tmp, all_params = block.get_all_params()

        return all_params


    def get_parameter(self, group:str, name:str) -> Union[int,float]:
        """ Set a parameter value """

        if group in self.gen_groups:
            if name in self.gen_names:
                idx = self.gen_names.index(name)

                if group == self.gen_groups[idx]:

                    vals = self._get_general_params()
                    return vals[idx]

                else:
                    logging.error(_('Bad group/name in parameters'))
                    return

        if group in self.debug_groups:
            if name in self.debug_names:
                idx = self.debug_groups.index(group)

                if group == self.debug_groups[idx]:
                    vals = self._get_debug_params()
                    return vals[idx]

                else:
                    logging.error(_('Bad group/name in parameters'))
                    return

        logging.error(_('Group not found in parameters'))

    def set_parameter(self, group:str, name:str, value:Union[int,float]) -> None:
        """ Set a parameter value """

        if group in self.gen_groups:
            if name in self.gen_names:
                idx = self.gen_names.index(name)

                if group == self.gen_groups[idx]:

                    vals = self._get_general_params()
                    vals[idx] = value

                    self._set_general_params(vals)
                    return
                else:
                    logging.error(_('Bad group/name in parameters'))
                    return

        if group in self.debug_groups:
            if name in self.debug_names:
                idx = self.debug_groups.index(group)

                if group == self.debug_groups[idx]:
                    vals = self._get_debug_params()
                    vals[idx] = value

                    self._set_debug_params(vals)
                    return
                else:
                    logging.error(_('Bad group/name in parameters'))
                    return

        logging.error(_('Group not found in parameters'))

    def show_params(self, which:Literal['all','simulation','block i']):

        wx_exists = wx.GetApp() is not None

        if not wx_exists:
            logging.warning(_('No wxPython available --> no display'))
            return

        if which == 'all':

            self._params.ensure_gui()

            for curblock in self.blocks:
                curblock._params.ensure_gui()

                curblock._params.Show()

            self._params.Show()

        elif which == 'simulation':

            self._params.ensure_gui()

            self._params.Show()

        elif 'blocks' in which.lower():

            i_block = int(which.split(' ')[1])

            self.blocks[i_block]._params.ensure_gui()

            self.blocks[i_block]._params.Show()

    def help(self, group:str, name:str) -> list[str]:
        """ Retourne l'aide associée à un paramètre """

        # Remplissage des paramètres
        self._set_sim_params()

        assert self._params is not None, 'No simulation parameters defined'

        return self._params.get_help(group, name)

    def frequent_params(self) -> list[tuple[str,str]]:
        """ Retourne les paramètres fréquemment utilisés """

        glob_gen = [1,3,4,6,17,18]
        glob_dbg = [4,5]

        block_gen = [10,12,13,15,16,17]
        block_dbg = [1,2,3,4,6,7,8,18,19,20,21,22,23,24,25,26,28,32,42,43,44,45,46,47,48]

        self._set_sim_params()
        self.blocks[0]._set_block_params()

        frequent_params_glob = []

        for i in glob_gen:
            frequent_params_glob.append((self.gen_groups[i-1],
                                    self.gen_names[i-1]))

        for i in glob_dbg:
            frequent_params_glob.append((self.debug_groups[i-1],
                                    self.debug_names[i-1]))

        frequent_params_block = []

        for i in block_gen:
            frequent_params_block.append((self.blocks[0].gen_groups[i-1],
                                          self.blocks[0].gen_names[i-1]))

        for i in block_dbg:
            frequent_params_block.append((self.blocks[0].debug_groups[i-1],
                                            self.blocks[0].debug_names[i-1]))

        return frequent_params_glob, frequent_params_block, (glob_gen, glob_dbg, block_gen, block_dbg)


class prev_infiltration():
    """Infiltration

    Gère à la fois le fichier '.fil' (quantités au cours du temps)
    et accès au '.inf' (matrice) via 'parent' ou en autonomie

    :author: Pierre Archambeau

    """

    _infiltrations_chronology: np.ndarray  # débits injectés par zone

    def __init__(self, parent:"prev_sim2D"=None, fn:str='', to_read:bool=True) -> None:

        self.parent = parent
        self._zoning = None # Useful only if parent is None

        if self.parent is not None:
            logging.info(_('(Infiltration) Parent found --> using its filename'))
            self._fn = self.parent.filenamegen

        elif fn != '':
            logging.info(_('(Infiltration) No parent found --> using the filename provided'))
            self._fn = fn
        else:
            raise Exception(_('Bad initialisation of "prev_infiltration" object in wolf2dprev.py -- check your code'))

        self._infiltrations_chronology:np.ndarray = None

        if to_read:
            self.read_file()

    @property
    def nb_zones(self):
        """ Number of infiltration zones """

        if self._infiltrations_chronology is None:
            return 0

        return self._infiltrations_chronology.shape[1]-1

    @property
    def nb_steps(self):
        """ Number of time steps """

        if self._infiltrations_chronology is None:
            return 0

        return self._infiltrations_chronology.shape[0]

    def _read_zoning(self):
        """ Lecture du fichier .inf -- en mode "autonome" si parent n'est pas défini """

        if self.parent is None:
            if Path(self._fn + '.inf').exists():
                self._zoning = WolfArray(fname = self._fn + '.inf')

                assert self._zoning.wolftype == WOLF_ARRAY_FULL_INTEGER, _('Infiltration array must be of type WOLF_ARRAY_FULL_INTEGER')
        else:
            self._zoning = self.parent._inf

    @property
    def zoning(self):
        """ Return the zoninf array """

        if self.parent is None:
            # Instance "autonome"

            if self._zoning is None:
                self._read_zoning()

            return self._zoning

        else:
            return self.parent.inf


    @zoning.setter
    def zoning(self, value:WolfArray):
        """ Set the zoning array """

        assert value.wolftype == WOLF_ARRAY_FULL_INTEGER, _('Infiltration array must be of type WOLF_ARRAY_FULL_INTEGER')

        if self.parent is None:
            self._zoning = value

        else:
            self.parent._inf = value
            self._zoning = self.parent._inf

    def read_file(self):
        """ Lecture du fichier .fil """

        if self._fn is None:
            logging.warning(_('No filename provided'))
            return

        if not exists(self._fn + '.fil'):
            logging.warning(_('No infiltration file found'))
            return

        # Lecture du fichier
        with open(self._fn + '.fil', 'r') as f:
            lines = f.read().splitlines()

        """
        line 1: nb_zones
        line 2: start time 1, zone1 value , zone2 value, zone3 value,...
        line 3: start time 2, zone1 value , zone2 value, zone3 value,...
        """
        nb_zones = int(lines[0])
        nb_steps = len(lines) - 1

        if nb_steps > 0:

            # Detect separator
            sep = find_sep(lines[1])

            if sep is None:
                logging.error(_("Values in the '.fil' file are not separated by comma, semi-comma or tabulation -- Check your file -- Continuing with zero values"))
                self._infiltrations_chronology = np.zeros((nb_steps, nb_zones))

            else:
                locarray = [[float(val) for val in lines[i].strip().split(sep)[:nb_zones + 1]] for i in range(1, len(lines))]
                self._infiltrations_chronology = np.asarray(locarray)

    def write_file(self):
        """ Ecriture du fichier .fil """

        if self._infiltrations_chronology is None:
            logging.warning(_('No infiltration data to write'))

        with open(self._fn + '.fil', 'w') as f:
            f.write(str(self.nb_zones) + '\n')
            for i in range(self.nb_steps):
                f.write(','.join([str(val) for val in self._infiltrations_chronology[i]]) + '\n')

    def __getitem__(self, time):

        return self.zones_values_at_time(time)

    def zones_values_at_time(self, t):
        """ Retourne les valeurs des zones à un temps donné """

        for i in range(self.nb_steps-1):
            if self._infiltrations_chronology[i,0] <= t < self._infiltrations_chronology[i+1,0]:

                pond = (t - self._infiltrations_chronology[i,0]) / (self._infiltrations_chronology[i+1,0] - self._infiltrations_chronology[i,0])

                return self._infiltrations_chronology[i,1:] * (1-pond) + self._infiltrations_chronology[i+1,1:] * pond

        return self._infiltrations_chronology[-1,1:]

    def plot_plt(self, figax=None, show=True):
        """ Plot the infiltration data """

        if figax is None:
            fig, ax = plt.subplots(1, 1)
        else:
            fig,ax = figax

        sequence, nb_zones = self._infiltrations_chronology.shape
        for zone in range(1,nb_zones):
            ax.plot(self._infiltrations_chronology[:, 0], self._infiltrations_chronology[:, zone], label=f'Zone {zone}')

        ax.set_xlabel(_('Time [s]'))
        ax.set_ylabel(_('Infiltration [$m^3/s$]'))
        ax.legend()
        fig.tight_layout()

        if show:
            fig.show()

        return fig,ax


    def add_infiltration(self, time_start: float, zones_values: list[float]):
        """ Add an infiltration point in the infiltration chronology.

        :param: time_start start time of the infiltration (in seconds)
        :param: zones_values an array representing the quantity of water per second
          to add to each infiltration zones, starting at time_start.
          The first item corrsesponds to the zone 1, second item corresponds
          to zone 2 and so on.
        """

        if self._infiltrations_chronology is None:
            self._infiltrations_chronology = np.asarray([[time_start] + zones_values])

        else:
            assert len(zones_values) == self.nb_zones, _('Number of zones in the infiltration chronology and the number of zones in the new infiltration do not match')

            self._infiltrations_chronology = np.concatenate([self._infiltrations_chronology, np.asarray([[time_start] + zones_values])])

    def clear_infiltration_chronology(self):
        """ Clear the infiltration chronology. Useful if one wants to build
        a new simulation starting with an existing one.
        """
        self._infiltrations_chronology = None

    @property
    def infiltrations_chronology(self) -> np.ndarray:
        return self._infiltrations_chronology


    @property
    def _chronology_for_gpu(self) -> list[float, list[float]]:

        newchronology = []
        for i in range(self.nb_steps):
            newchronology.append([self._infiltrations_chronology[i,0], self._infiltrations_chronology[i,1:].tolist()])

        return newchronology

    @infiltrations_chronology.setter
    def infiltrations_chronology(self, infiltrations_chronology:np.ndarray):

        self._infiltrations_chronology = infiltrations_chronology.copy()

class prev_suxsuy():

    """
    Enumération des bords potentiellement conditions limites selon X et Y

    Dans WOLF, un bord X est un segment géométrique orienté selon Y --> le débit normal au bord est orienté selon X
    Dans WOLF, un bord Y est un segment géométrique orienté selon X --> le débit normal au bord est orienté selon Y

    La logique d'appellation est donc "hydraulique"

    @remark Utile pour l'interface VB6/Python pour l'affichage

    """
    myborders: Zones
    mysux: zone
    mysuy: zone

    def __init__(self, parent:"prev_sim2D") -> None:

        self.parent = parent

        self.reset()

    @property
    def filenamesux(self) -> str:
        if self.parent.filenamegen is not None:
            return self.parent.filenamegen + '.sux'
        else:
            return None

    @property
    def filenamesuy(self) -> str:
        if self.parent.filenamegen is not None:
            return self.parent.filenamegen + '.suy'
        else:
            return None

    def reset(self):

        self.is_read = False

        self.myborders = Zones()
        self.mysux = zone(name='sux')
        self.mysuy = zone(name='sux')

        self.sux_ij = []
        self.suy_ij = []

        self.myborders.add_zone(self.mysux)
        self.myborders.add_zone(self.mysuy)

    def read_file(self):
        """ Read the SUX/SUY files """

        if self.myborders.nbzones > 0:
            self.reset()

        if not (exists(self.filenamesux) and exists(self.filenamesuy)):
            logging.warning(_('No SUX/SUY files found'))
            return

        with open(self.filenamesux, 'r') as f:
            linesX = f.read().splitlines()
        with open(self.filenamesuy, 'r') as f:
            linesY = f.read().splitlines()

        linesX = [np.float64(curline.split(find_sep(curline))) for curline in linesX]
        linesY = [np.float64(curline.split(find_sep(curline))) for curline in linesY]

        dx = self.parent.dx
        dy = self.parent.dy
        ox = self.parent.origx
        oy = self.parent.origy
        tx = self.parent.translx
        ty = self.parent.transly

        k = 1
        for curline in linesX:
            x1 = (curline[0] - 1.) * dx + tx + ox
            y1 = (curline[1] - 1.) * dy + ty + oy
            x2 = x1
            y2 = y1 + dy

            self.sux_ij.append([int(curline[0]), int(curline[1])])

            vert1 = wolfvertex(x1, y1)
            vert2 = wolfvertex(x2, y2)

            curborder = vector(name='b' + str(k))

            self.mysux.add_vector(curborder)
            curborder.add_vertex([vert1, vert2])

            k += 1

        k = 1
        for curline in linesY:
            x1 = (curline[0] - 1.) * dx + tx + ox
            y1 = (curline[1] - 1.) * dy + ty + oy
            x2 = x1 + dx
            y2 = y1

            self.suy_ij.append([int(curline[0]), int(curline[1])])

            vert1 = wolfvertex(x1, y1)
            vert2 = wolfvertex(x2, y2)

            curborder = vector(name='b' + str(k))

            self.mysuy.add_vector(curborder)
            curborder.add_vertex([vert1, vert2])

            k += 1

        self.myborders.find_minmax(True)

        self.is_read = True

    def is_like(self, other:"prev_suxsuy") -> tuple[bool, str]:
        """ Compare two prev_suxsuy objects """

        ret = ''
        valid = True

        if self.mysux.nbvectors != other.mysux.nbvectors:
            ret   +=_('Different number of vectors in SUX') + '\n'
            valid = False

        if self.mysuy.nbvectors != other.mysuy.nbvectors:
            ret  +=_('Different number of vectors in SUY') + '\n'
            valid = False

        return valid, ret

    def list_pot_bc_x(self) -> list[int, int]:
        """
        Liste des conditions limites potentielles sur le bord X
        """

        if not self.is_read:
            self.read_file()

        return self.sux_ij

    def list_pot_bc_y(self) -> list[int, int]:
        """
        Liste des conditions limites potentielles sur le bord X
        """

        if not self.is_read:
            self.read_file()

        return self.suy_ij

    @property
    def Zones(self):
        return self.myborders


class blocks_file():
    """
    Objet permettant la lecture et la manipulation d'un fichier .BLOC

    ***

    Objectif :
     - fournir l'information nécessaire au code Fortran pour mailler le domaine en MB
     - contient des informations géométriques
        - domaine de calcul
        - contour de bloc
     - contient des informations de résolution de maillage
        - tailles de maille souhaitées selon X et Y pour chaque bloc

    ***

    Contenu du fichier :
     - nombre de blocs, nombre maximum de vertices contenu dans les polygones présents (soit contour extérieur, soit contour de bloc)
     - nombre de vertices à lire pour le contour général (une valeur négative indique que 3 colonnes sont à lire)
        - liste de vertices du contour général (sur 2 -- X,Y -- ou 3 colonnes -- X,Y, flag -- la 3ème colonne ne devrait contenir que 0 ou 1 -- 1==segment à ignorer dans les calcul d'intersection du mailleur)

            @remark En pratique, le "flag" sera stocké dans la propriété "z" du vertex --> sans doute pas optimal pour la compréhension --> à modifier ??

     - informations pour chaque bloc
        - nombre de vertices du polygone de contour
        - liste de vertices (2 colonnes -- X et Y)
        - extension du bloc calé sur la grille magnétique et étendu afin de permettre le stockage des relations de voisinage (2 lignes avec 2 valeurs par ligne)
            - xmin, xmax
            - ymin, ymax

            @remark L'extension, sur tout le pourtour, vaut 2*dx_bloc+dx_max_bloc selon X et 2*dy_bloc+dy_max_bloc selon Y
            @remark Pour une taille de maille uniforme on ajoute donc l'équivalent de 6 mailles selon chaque direction (3 avant et 3 après)

     - résolution pour chaque bloc ("nb_blocs" lignes)
        - dx, dy

    ***

    Remarques :
        - nb_blocs n'est pas un invariant. Il faut donc faire attention lors de la création/manipulation de l'objet --> A fixer?
        - pour les simulations existantes, la taille de la grille magnétique n'est pas une information sauvegardée dans les fichiers mais provient du VB6 au moment de la création de la simulation
          @TODO : coder/rendre une grille magnétique et sans doute définir où stocker l'info pour garantir un archivage correct
        -

    """

    # bloc extents are polygons delimiting the area of each block. These
    # rectangle have the same proportion as the block arrays (but of course
    # are in world coordinates)
    my_blocks: list["block_description"]

    # self.my_vec_blocks.myzones (class: Zones) has two `zone`:
    #  [0] + General Zone
    #         + external border : representing the global contour (an arbitrary polygon)
    #  [1] + Block extents
    #         +-> myvectors: representing the extents (rectangles around the blocks)
    my_vec_blocks: Zones

    @property
    def nb_blocks(self) -> int:
        return len(self.my_blocks)

    @property
    def dx_dy(self) -> tuple[list[float], list[float]]:
        if self.nb_blocks == 0:
            return 0., 0.
        else:
            dx = [cur.dx for cur in self.my_blocks]
            dy = [cur.dy for cur in self.my_blocks]

            return dx, dy

    @property
    def dx_max(self) -> float:
        return max([curblock.dx for curblock in self.my_blocks])

    @property
    def dy_max(self) -> float:
        return max([curblock.dy for curblock in self.my_blocks])

    @property
    def filename(self) -> str:

        if self.parent.filenamegen is not None:
            return self.parent.filenamegen + '.bloc'
        else:
            return None

    @property
    def Zones(self):
        return self.my_vec_blocks

    def __init__(self, parent:Union["prev_sim2D"]= None) -> None:

        self.parent:"prev_sim2D" = parent
        self.translate_origin2zero = True


        if self.filename is not None and exists(self.filename):

            self.translate_origin2zero = False

            self.my_blocks:list[block_description] = []

            self.read_file()

            self.force_legends()

        else:
            # If there's no bloc file then assume we're creating a new one,
            # therefore we give it a name (so it can be saved later).
            self.my_blocks:list[block_description] = []

            self.my_vec_blocks = Zones(parent=parent.get_mapviewer())  # vecteur des objets blocs
            self.my_vec_blocks.add_zone(zone(name='General',parent=self.my_vec_blocks))
            self.my_vec_blocks.add_zone(zone(name='Blocks extents',parent=self.my_vec_blocks))

    def force_legends(self):
        """Force the legends of the zones"""

        self.blocks_extents_zone.set_legend_to_centroid()
        # self.general_contour_zone.set_legend_to_centroid()

    def align2grid(self, x:float, y:float):
        """Aligns a point to the grid"""

        x, y = self.parent.align2grid(x, y)
        return x, y

    def set_external_border(self, contour:vector):
        """ Set the external contour -- Replace the existing one if any """

        extern_zone = self.general_contour_zone

        if extern_zone.nbvectors>0:
            extern_zone.myvectors = []

        extern_zone.add_vector(contour.deepcopy_vector(name = 'external border', parentzone = extern_zone))

        if self.translate_origin2zero:
            contour.find_minmax()
            xmin = contour.xmin
            ymin = contour.ymin

            self.parent.translx = xmin
            self.parent.transly = ymin

    def reset_external_border(self):
        """Reset the external contour"""

        self.general_contour_zone.myvectors = []

    def add_block(self, contour:zone, dx:float, dy:float):
        """Add a block to the list of blocks"""

        if contour is None:
            logging.error(_('No contour zone available for block creation - Create a contour first'))
            return

        new_block = block_description(self, idx = self.nb_blocks+1)
        new_block.setup(contour, dx, dy)
        self.my_blocks.append(new_block)
        self.blocks_extents_zone.add_vector(new_block.contour, forceparent=True)

        # Update the wx UI if exists
        self.my_vec_blocks.fill_structure()

        logging.info(_('Block n° {} added').format(self.nb_blocks))

    def reset_blocks(self):
        """Reset the list of blocks"""

        self.my_blocks = []
        self.blocks_extents_zone.myvectors = []

        logging.info(_('Blocks reset'))

    def delete_block(self, idx:int):
        """
        Delete a block from the list

        :param idx: index of the block to delete - 1-based

        """

        if idx > 0 and idx <= self.nb_blocks:
            self.my_blocks.pop(idx-1)
            self.blocks_extents_zone.myvectors.pop(idx-1)

            logging.info(_('Block n° {} deleted').format(idx))
        else:
            logging.error(_('Invalid index for block deletion'))

    def insert_block(self, idx:int, contour:zone, dx:float, dy:float):
        """
        Insert a block in the list

        :param idx: index where to insert the block - 1-based

        """

        if idx > 0 and idx <= self.nb_blocks:
            new_block = block_description(self, idx = idx)
            new_block.setup(contour, dx, dy)

            self.my_blocks.insert(idx-1, new_block)
            self.blocks_extents_zone.add_vector(new_block.contour, idx-1, forceparent=True)

            for added, curvec in enumerate(self.blocks_extents_zone.myvectors[idx:]):
                curvec.myname = f'block n° {idx + 1 + added}'

            logging.info(_('Block inserted at index {}').format(idx))
        else:
            logging.error(_('Invalid index for block insertion'))

    @property
    def general_contour_zone(self) -> zone:
        return self.my_vec_blocks.myzones[0]

    @property
    def blocks_extents_zone(self) -> zone:
        return self.my_vec_blocks.myzones[1]

    @property
    def external_border(self) -> vector:
        """ Return the external border of the simulation """
        if self.general_contour_zone.nbvectors == 0:
            return None

        return self.general_contour_zone.myvectors[0]

    def search_magnetic_grid(self):
        """ Search the magnetic grid properties """

        all_dx, all_dy = self.dx_dy

        all_dx = list(set(all_dx))
        all_dy = list(set(all_dy))

        dxmax = self.dx_max
        dymax = self.dy_max

        all_dx = list(set(all_dx + all_dy + [dxmax, dymax] + [1., 2., 4., 5., 10.]))
        all_dx.sort(reverse=True)

        potential = []
        for curblock in self.my_blocks:

            xmin = curblock.xmin
            ymin = curblock.ymin
            xmax = curblock.xmax
            ymax = curblock.ymax

            vec_xmin = curblock.contour.xmin
            vec_ymin = curblock.contour.ymin
            vec_xmax = curblock.contour.xmax
            vec_ymax = curblock.contour.ymax

            aligned_xmin = xmin + dxmax + 2. * curblock.dx
            aligned_ymin = ymin + dymax + 2. * curblock.dy
            aligned_xmax = xmax - dxmax - 2. * curblock.dx
            aligned_ymax = ymax - dymax - 2. * curblock.dy

            for curdx in all_dx:

                test_magn = header_wolf()
                test_magn.dx = curdx
                test_magn.dy = curdx
                test_magn.origx = 0.
                test_magn.origy = 0.

                test_xmin, test_ymin = test_magn.align2grid(vec_xmin, vec_ymin)
                test_xmax, test_ymax = test_magn.align2grid(vec_xmax, vec_ymax)

                if np.isclose(aligned_xmin, test_xmin) and np.isclose(aligned_ymin, test_ymin) and np.isclose(aligned_xmax, test_xmax) and np.isclose(aligned_ymax, test_ymax):
                    potential.append(curdx)
                    break

        potential = list(set(potential))
        potential.sort(reverse=True)

        if len(potential) > 0:
            self.parent.set_magnetic_grid(curdx, curdx, 0., 0.)


    def get_contour_block(self, idx:int) -> vector:
        """ Get the contour of a block """

        if idx > 0 and idx <= self.nb_blocks:
            return self.my_blocks[idx-1].contour
        else:
            logging.error(_('Invalid index for block contour'))

    def read_file(self):
        """ Lecture du fichier .bloc """

        if self.filename is None:
            return

        if not exists(self.filename):
            return

        self.my_vec_blocks = Zones(parent=self.parent.get_mapviewer())  # vecteur des objets blocs

        trlx, trly = self.parent.translx, self.parent.transly

        general = zone(name='General',parent=self.my_vec_blocks)
        self.my_vec_blocks.add_zone(general)

        external_border = block_contour(is2D=True, name='external border')  #vecteur du contour externe - polygone unique entourant la matrice "nap", y compris les zones internes reliées par des segments doublés (aller-retour)
        general.add_vector(external_border, forceparent=True)

        myextents = zone(name='Blocks extents',parent=self.my_vec_blocks)
        self.my_vec_blocks.add_zone(myextents)

        # #ouverture du fichier
        with open(self.filename, 'r') as f:
            lines = f.read().splitlines()

        # #lecture du nombre de blocs et de la taille maximale du contour
        tmpline = lines[0].split(find_sep(lines[0]))
        nb_blocks = int(tmpline[0])
        max_size_cont = int(tmpline[1])

        # lecture du nombre de points du contour extérieur
        nb = int(lines[1])

        # Si nb est négatif, il existe une troisième colonne qui dit si le segment est utile ou pas
        # (maillage de zones intérieures)
        # ATTENTION:
        #   - cette 3ème valeur est soit 0 ou 1
        #   - 0 = segment à utiliser dans les calculs
        #   - 1 = segment à ignorer
        #   - le segment est défini sur base du point courant et du point précédent
        interior = nb < 0

        nb = np.abs(nb)

        # lecture des données du contour extérieur
        decal = 2
        if interior:
            for i in range(decal, nb + decal):
                tmpline = lines[i].split(find_sep(lines[i]))
                # FIXME no *dx, *dy ??? I think it's i,j : cell coordinates
                # It is local coordinates, not world coordinates
                # Adding the translation will give the world coordinates
                x = float(tmpline[0]) + trlx
                y = float(tmpline[1]) + trly
                in_use = float(tmpline[2])
                curvert = wolfvertex(x, y, in_use)

                # Ici le test est sur 0, toute autre valeur est donc acceptée
                #  mais en pratique seul 1 doit être utilisé afin de pouvoir être
                #  utilisé dans le code Fortran ou le VB6
                # @TODO : Il serait sans doute plus rigoureux de rendre un message d'erreur si autre chose que 0 ou 1 est trouvé
                assert in_use == 0. or in_use == 1., f"Invalid value for 'in_use' in bloc file: {in_use}"

                curvert.in_use = in_use == 0.

                external_border.add_vertex(curvert)
        else:
            for i in range(decal, nb + decal):
                tmpline = lines[i].split(find_sep(lines[i]))
                x = float(tmpline[0]) + trlx
                y = float(tmpline[1]) + trly
                curvert = wolfvertex(x, y)

                external_border.add_vertex(curvert)

        external_border.close_force() # assure que le contour est fermé

        # lecture des données par bloc
        decal = nb + 2
        for i in range(nb_blocks):

            cur_description = block_description(self, lines[decal:], i+1)
            myextents.add_vector(cur_description.contour, forceparent=True)

            self.my_blocks.append(cur_description)

            decal += int(lines[decal]) + 3

        # lecture des tailles de maille pour tous les blocs
        for i in range(nb_blocks):
            tmp = lines[decal].split(find_sep(lines[decal]))
            self.my_blocks[i].dx = float(tmp[0])
            self.my_blocks[i].dy = float(tmp[1])
            decal += 1

        self.my_vec_blocks.find_minmax(True)

    def write_file(self):
        """ Writing bloc file """

        for curblock in self.my_blocks:
            curblock.set_bounds()

        trlx, trly = self.parent.translx, self.parent.transly

        general:zone
        general = self.my_vec_blocks.myzones[0]
        external_border:block_contour
        external_border = general.myvectors[0]

        # ouverture du fichier
        with open(self.filename, 'w') as f:

            # écriture du nombre de blocs et de la taille maximale du contour
            f.write('{},{}\n'.format(self.nb_blocks,self.max_size_cont))

            # #lecture du nombre de points du contour extérieur
            if self.has_interior :
                f.write('{}\n'.format(-external_border.nbvertices))
                xyz=external_border.asnparray3d()
                xyz[:,0] -= trlx # Les coordonnées sont stockées en absolu, il faut donc retrancher la translation X
                xyz[:,1] -= trly # Les coordonnées sont stockées en absolu, il faut donc retrancher la translation XY
                xyz[:,2] = [0 if cur.in_use else 1 for cur in external_border.myvertices]

                np.savetxt(f,xyz,fmt='%f,%f,%u')
            else:
                f.write('{}\n'.format(external_border.nbvertices))
                xy=external_border.asnparray()
                xy[:,0] -= trlx # Les coordonnées sont stockées en absolu, il faut donc retrancher la translation X
                xy[:,1] -= trly # Les coordonnées sont stockées en absolu, il faut donc retrancher la translation Y

                np.savetxt(f,xy,fmt='%f,%f')

            # écriture des données par bloc
            for i in range(self.nb_blocks):
                curbloc:block_description
                curvec:vector

                curbloc = self.my_blocks[i]

                curvec = curbloc.contour
                curvec.verify_limits()

                xy=curvec.asnparray()
                xy[:,0] -= trlx # Les coordonnées sont stockées en absolu, il faut donc retrancher la translation X
                xy[:,1] -= trly # Les coordonnées sont stockées en absolu, il faut donc retrancher la translation Y

                f.write('{}\n'.format(curvec.nbvertices))
                np.savetxt(f,xy,fmt='%f,%f')
                f.write('{:.6f},{:.6f}\n'.format(curbloc.xmin - trlx,curbloc.xmax - trlx))
                f.write('{:.6f},{:.6f}\n'.format(curbloc.ymin - trly,curbloc.ymax - trly))

            # écriture des tailles de maille pour tous les blocs
            for i in range(self.nb_blocks):
                f.write('{:g},{:g}\n'.format(self.my_blocks[i].dx,self.my_blocks[i].dy))

    def modify_extent(self):

        self.my_vec_blocks.find_minmax(True)

    @property
    def max_size_cont(self):
        """ Maximal number of vertices in a contour """

        nb = [len(cur.myvertices) for cur in self.blocks_extents_zone.myvectors]
        nb += [len(self.general_contour_zone.myvectors[0].myvertices)]
        return np.max(nb)

    @property
    def has_interior(self):
        """ Check if the bloc file has interior segments """

        extern = self.general_contour_zone.myvectors[0]

        all_used = True
        for curv in extern.myvertices:
            all_used &= curv.in_use

        return not all_used

    def is_like(self, other:"blocks_file") -> tuple[bool, str]:
        """ Check if the bloc file is like another one """

        ret   = ''
        valid = True

        if self.nb_blocks != other.nb_blocks:
            ret = _('Bad number of blocks\n')
            valid = False

        if self.has_interior != other.has_interior:
            ret = _('Bad interior segments\n')
            valid = False

        for i in range(self.nb_blocks):

            if self.my_blocks[i].dx != other.my_blocks[i].dx or self.my_blocks[i].dy != other.my_blocks[i].dy:
                ret = _('Bad resolution\n')
                valid = False

            if not (np.isclose(self.my_blocks[i].xmin, other.my_blocks[i].xmin) and np.isclose(self.my_blocks[i].xmax, other.my_blocks[i].xmax) and \
                np.isclose(self.my_blocks[i].ymin, other.my_blocks[i].ymin) and np.isclose(self.my_blocks[i].ymax, other.my_blocks[i].ymax)):
                ret = _('Bad extents -- Aligned on the magnetic grid\n')
                valid = False

            if self.my_blocks[i].contour.nbvertices != other.my_blocks[i].contour.nbvertices:
                ret = _('Bad number of vertices in the contour {}\n'.format(i+1))
                valid = False

            for idx, (curvert1, curvert2) in enumerate(zip(self.my_blocks[i].contour.myvertices, other.my_blocks[i].contour.myvertices)):
                if not curvert1.is_like(curvert2):
                    ret = _('Bad vertex in the contour {} at position {}\n'.format(i+1, idx+1))
                    valid = False

        extern1 = self.external_border
        extern2 = other.external_border

        if extern1.nbvertices != extern2.nbvertices:
            ret = _('Bad number of vertices in the external border\n')
            valid = False

        for idx, (curvert1, curvert2) in enumerate(zip(extern1.myvertices, extern2.myvertices)):
            if not curvert1.is_like(curvert2):
                ret = _('Bad vertex in the external border at position {}\n'.format(idx+1))
                valid = False

        return valid, ret

    def __getitem__(self, idx:int) -> "block_description":
        """ Get a block by its index (1-based) """

        if idx > 0 and idx <= self.nb_blocks:
            return self.my_blocks[idx-1]
        else:
            logging.error(_('Invalid index for block'))
            return None


class block_contour(vector):
    """

    Extension d'un vecteur afin de stocker un polygone
    de contour soit du domaine de calcul, soit d'un bloc

    L'extension est utile pour définir la propriété :
        - mylimits

    et les routines:
        - set_limits
        - verify_limits

    """

    def __init__(self, lines: list = ..., is2D=True, name='', parentzone=None) -> None:
        super().__init__(lines, is2D, name, parentzone)


    def verify_limits(self):
        """ Verify that the current vertices are inside the set block's limits """

        if self._mylimits is None:
            return

        self.find_minmax()

        if self.xmin < self._mylimits[0][0] or self.xmax > self._mylimits[0][1] or \
                self.ymin < self._mylimits[1][0] or self.ymax > self._mylimits[1][1]:

            for curv in self.myvertices:
                curv: wolfvertex
                # Force the vertex inside self.mylimits
                curv.limit2bounds(self._mylimits)


COLOURS_BLOCKS=[(0,0,255),(255,0,0),(0,255,0),(255,255,0),(255,0,255),(0,255,255),(0,125,255),(255,125,0),(125,0,255),(25,25,255)]


class block_description:

    parent:blocks_file
    # Contour externe du bloc (en coordonnées réelles, c-à-d non
    # translatée vis-à-vis du bloc général)
    contour:block_contour

    # Please note that both these values will be read
    # in the block file (not in this class)

    dx: float  #taille de discrétisation selon X
    dy: float  #taille de discrétisation selon Y

    # In the following, "une fois qu'il a été "accroché" sur le grid
    # magnétique" means that xmin is in fact xmin - (dxmax + 2*dx),
    # xmax is xmax + (dxmax + 2*dx) and the same for ymin and ymax.

    xmin: float  #position minimale selon X du contour une fois qu'il a été "accroché" sur le grid magnétique
    xmax: float  #position maximale selon X du contour une fois qu'il a été "accroché" sur le grid magnétique
    ymin: float  #position minimale selon Y du contour une fois qu'il a été "accroché" sur le grid magnétique
    ymax: float  #position maximale selon Y du contour une fois qu'il a été "accroché" sur le grid magnétique
    """

    Classe permettant de contenir:
        - le polygone de définition du bloc
        - les bornes de l'étendue augmentée

    Ici xmin, xmax, ymin, ymax sont à dissocier des propriétés du vecteur
    contour et ne représentent donc pas les coordonnées min et max des vertices
    mais bien une zone rectangulaire contenant tout le bloc

    """
    def __init__(self, parent:blocks_file, lines=[], idx:int=0) -> None:
        """ Initialisation de la classe

        :param parent: objet parent
        :param lines: lignes du fichier .bloc
        :param idx: index du bloc - 1-based
        """

        self.parent = parent  # objetparent

        trlx, trly = parent.parent.translx, parent.parent.transly

        self.xmin = 0.  #position minimale selon X du contour une fois qu'il a été "accroché" sur le grid magnétique
        self.xmax = 0.  #position maximale selon X du contour une fois qu'il a été "accroché" sur le grid magnétique
        self.ymin = 0.  #position minimale selon Y du contour une fois qu'il a été "accroché" sur le grid magnétique
        self.ymax = 0.  #position maximale selon Y du contour une fois qu'il a été "accroché" sur le grid magnétique

        self.dx = 0.  #taille de discrétisation selon X
        self.dy = 0.  #taille de discrétisation selon Y

        self.contour = block_contour(name='block n° ' + str(idx), lines=None)  # contour externe du bloc (en coordonnées réelles, c-à-d non translatée vis-à-vis du bloc général)

        self.contour.myprop.color=getIfromRGB(COLOURS_BLOCKS[idx % 9])

        if not lines:
            # lines is None or [] means we're creating a new bloc_extent from scratch.
            pass
        else:

            ##lecture du nombre de points du contour extérieur
            nb = int(lines[0])

            ##lecture des données
            for i in range(nb):
                tmp = lines[i + 1].split(find_sep(lines[i+1]))

                x = float(tmp[0]) + trlx
                y = float(tmp[1]) + trly

                curvert = wolfvertex(x, y)
                self.contour.add_vertex(curvert)

            self.contour.close_force()  ##on force la fermeture du contour extérieur des blocs
            self.contour._set_limits() # on retient les limites en cas de modifications

            ##emprise du bloc en accord avec le grid magnétique et
            # l'extension de surface utile pour les relations de voisinage entre blocs
            tmp = lines[nb + 1].split(find_sep(lines[nb + 1]))
            self.xmin = float(tmp[0])
            self.xmax = float(tmp[1])
            tmp = lines[nb + 2].split(find_sep(lines[nb + 2]))
            self.ymin = float(tmp[0])
            self.ymax = float(tmp[1])

    def align2grid(self, x:float, y:float):
        """Aligns a point to the grid"""

        x, y = self.parent.align2grid(x, y)
        return x, y

    def setup(self, contour:vector, dx:float, dy:float):
        """
        Fill in the block with a given value

        :param contour: vector representing the block contour
        :param dx: resolution along X
        :param dy: resolution along Y

        """

        # make a copy of the contour
        copy_contour = contour.deepcopy_vector()

        # set the block contour
        self.contour.myvertices = copy_contour.myvertices

        # Find extrema
        self.contour.find_minmax()

        # Align extrema to the magnetic grid
        #
        # Ce n'est toutefois pas l'extension définitive car il faut pour cela disposer de la
        # taille maximale des blocs de la simulation
        self.xmin, self.ymin = self.align2grid(self.contour.xmin, self.contour.ymin)
        self.xmax, self.ymax = self.align2grid(self.contour.xmax, self.contour.ymax)

        # set the resolution
        self.dx = dx
        self.dy = dy

    def set_bounds(self):
        """ Retain current limits before any modification """

        dx_max = self.parent.dx_max
        dy_max = self.parent.dy_max

        # align extrema to the magnetic grid
        self.xmin, self.ymin = self.align2grid(self.contour.xmin, self.contour.ymin)
        self.xmin -= dx_max + 2*self.dx
        self.ymin -= dy_max + 2*self.dy

        self.xmax, self.ymax = self.align2grid(self.contour.xmax, self.contour.ymax)
        self.xmax += dx_max + 2*self.dx
        self.ymax += dy_max + 2*self.dy

        pass

    def set_dx_dy(self, dx:float, dy:float):
        """ Set the resolution of the block """

        self.dx = dx
        self.dy = dy


class xy_file():
    """
    Contour du domaine

    Les infos de cette classe sont redondantes avec le contour contenu dans le fichier .bloc
    Dans l'interface VB6, il est cependant généré avant le fichier .bloc

    @remark Le fichier n'est pas utilisé par le code de calcul Fortran --> principalement pré-traitement/visualisation

    """
    myzones: Zones

    def __init__(self, simparent:Union["prev_sim2D"]=None):

        self.parent = simparent

        self.myzones = Zones(parent=self.parent)

        myzone = zone(name='contour', parent=self.myzones)
        myvect = vector(name='xy', parentzone=myzone)

        self.myzones.add_zone(myzone)
        myzone.add_vector(myvect)

        self.read_file()

    @property
    def filename(self):
        if self.parent.filenamegen is None:
            return None
        else:
            return self.parent.filenamegen + '.xy'

    @property
    def translx(self):
        return self.parent.translx

    @property
    def transly(self):
        return self.parent.transly

    @property
    def contour_zone(self):
        assert self.myzones.nbzones == 1

        self.myzones.myzones[0]

    @property
    def contour_vector(self):
        assert self.myzones.nbzones == 1
        assert self.myzones.myzones[0].nbvectors == 1

        return self.myzones.myzones[0].myvectors[0]

    def read_file(self):
        """ Lecture du fichier .xy """

        if self.filename is None:
            return

        # MERGE In some cases there's no xy file
        if exists(self.filename):

            trlx, trly = self.translx, self.transly

            with open(self.filename, 'r') as f:
                lines = f.read().splitlines()

            nb = int(lines[0])

            # Choose the right split char
            splitchar = ' '
            if lines[1].find(',') > 0:
                splitchar = ','

            for i in range(nb):
                tmp = re.sub('\\s+', ' ', lines[i + 1].strip()).split(splitchar)
                x = float(tmp[0])
                y = float(tmp[1])

                curvert = wolfvertex(x + trlx, y + trly)
                self.contour_vector.add_vertex(curvert)

            self.myzones.find_minmax(True)

    @property
    def Zones(self):
        return self.myzones




class prev_lst_file:

    def __init__(self, parent:"prev_sim2D" = None) -> None:

        self.parent:"prev_sim2D" = parent

        self._topography    = []
        self._buildings     = []
        self._friction      = []
        self._infiltration  = []
        self._bridges       = []
        self._watedepth     = []
        self._dischargeX    = []
        self._dischargeY    = []


    @property
    def filename(self):

        if self.parent.filenamegen is None:
            return None
        else:
            return self.parent.filenamegen + '.lst'

    @property
    def filenamegen(self):
        return self.parent.filenamegen

    def read_file(self, forcefilename:str = None):
        """ Lecture du fichier .lst """

        if forcefilename is not None:
            filename = forcefilename
        else:
            filename = self.filename
            if filename is None:
                logging.debug(_('No filename for lst file'))
                return

        if not exists(filename):
            logging.info(_('File {} not found').format(filename))
            return

        with open(filename, 'r') as f:
            lines = f.read().splitlines()

        # Lecture des données
        decal = 0

        for curlist in [self._topography, self._buildings, self._friction, self._infiltration, self._bridges, self._watedepth, self._dischargeX, self._dischargeY]:

            try:

                nb = int(lines[decal])
                decal += 1

                for j in range(nb):
                    # Pour chaque fichier on dispose de :
                    #  - chemin d'accès
                    #  - Nbx
                    #  - Nby
                    #  - Origx
                    #  - Origy
                    #  - Dx
                    #  - Dy
                    #  - Nombre de blocs touchés
                    #  - Index du/des blocs

                    filename = lines[decal]
                    if filename[0] == "'":
                        filename = filename[1:-1]
                    if filename[0] == '"':
                        filename = filename[1:-1]
                    if filename[-1] == "'":
                        filename = filename[:-1]
                    if filename[-1] == '"':
                        filename = filename[:-1]

                    nbx = int(lines[decal + 1])
                    nby = int(lines[decal + 2])
                    origx = float(lines[decal + 3]) # You must add the simulation translation to get Wolrd coordinates
                    origy = float(lines[decal + 4]) # You must add the simulation translation to get Wolrd coordinates
                    dx = float(lines[decal + 5])
                    dy = float(lines[decal + 6])
                    nb_blocks = int(lines[decal + 7])
                    idx_bloxks = [int(cur) for cur in lines[decal + 8 : decal + 8 + nb_blocks]]

                    locheader = header_wolf()
                    locheader.nbx = nbx
                    locheader.nby = nby
                    locheader.dx = dx
                    locheader.dy = dy
                    locheader.origx = origx
                    locheader.origy = origy

                    if self.parent is None:
                        locheader.translx = 0.
                        locheader.transly = 0.
                    else:
                        locheader.translx = self.parent.translx
                        locheader.transly = self.parent.transly

                    curlist.append([filename, locheader, idx_bloxks])

                    decal += 8 + nb_blocks

            except:
                logging.error(_('Error while reading lst file'))

    def write_file(self, forcefilename:str = None):
        """ Writing lst file """

        def write_part(f, cur:list[str, header_wolf, list[int]]):

            fname:str = cur[0]

            if fname[0] not in  ["'", '"']:
                fname = f'"{fname}"'

            locheader:header_wolf = cur[1]
            idx:list[int] = cur[2]

            f.write(fname + '\n')
            f.write(f'{locheader.nbx}\n')
            f.write(f'{locheader.nby}\n')
            f.write(f'{locheader.origx}\n')
            f.write(f'{locheader.origy}\n')
            f.write(f'{locheader.dx}\n')
            f.write(f'{locheader.dy}\n')
            f.write(f'{len(idx)}\n')
            for curblock in idx:
                f.write(f'{curblock}' + '\n')


        if forcefilename is not None:
            filename = forcefilename
        else:
            filename = self.filename
            if filename is None:
                logging.error(_('No filename for lst file'))
                return

        with open(filename, 'w') as f:
            f.write(f'{len(self._topography)}\n')
            for cur in self._topography:
                write_part(f, cur)

            f.write(f'{len(self._buildings)}\n')
            for cur in self._buildings:
                write_part(f, cur)

            f.write(f'{len(self._friction)}\n')
            for cur in self._friction:
                write_part(f, cur)

            f.write(f'{len(self._infiltration)}\n')
            for cur in self._infiltration:
                write_part(f, cur)

            f.write(f'{len(self._bridges)}\n')
            for cur in self._bridges:
                write_part(f, cur)

            f.write(f'{len(self._watedepth)}\n')
            for cur in self._watedepth:
                write_part(f, cur)

            f.write(f'{len(self._dischargeX)}\n')
            for cur in self._dischargeX:
                write_part(f, cur)

            f.write(f'{len(self._dischargeY)}\n')
            for cur in self._dischargeY:
                write_part(f, cur)

    def check(self):
        """ Check the lst file """

        ret = True

        for curlist in [self._topography, self._buildings, self._friction, self._infiltration, self._bridges, self._watedepth, self._dischargeX, self._dischargeY]:

            for cur in curlist:

                path2file = Path(self.filenamegen).parent / cur[0]
                if (path2file).exists():

                    locarray = WolfArray(fname = path2file)

                    locheader = locarray.get_header()
                    lstheader = cur[1]

                    locret = True

                    locret &= locheader.nbx == lstheader.nbx
                    locret &= locheader.nby == lstheader.nby
                    locret &= locheader.dx == lstheader.dx
                    locret &= locheader.dy == lstheader.dy
                    locret &= locheader.origx == lstheader.origx + self.parent.parameters._fine_mesh_translx
                    locret &= locheader.origy == lstheader.origy + self.parent.parameters._fine_mesh_transly

                    if not locret:
                        logging.error(f'Error in {cur[0]}')

                    ret &= locret

        return ret


class prev_sim2D():
    """
    Modélisation 2D CPU -- version 2D originale non OO

    Cette classe est en construction et ne contient pas encore toutes les fonctionnalités.

    Elle devrait à terme être utilisée dans l'objet Wolf2DModel de PyGui afin de séparer
    le stockage des données de la visualisation et interface WX.

    """

    def __init__(self, fname:Union[str, Path] = None, parent = None, clear=False) -> None:
        """
        Initialisation de la classe

        :param fname: nom du fichier générique de simulation - sans extension
        :param parent: objet parent
        :param clear: effacer les données existantes du répertoire avant toute autre chose
        """

        from pathlib import Path

        self.filename = None
        self.mydir = None

        # Multiblocks arrays with type
        self.files_MB_array={'Initial Conditions':[
            ('.topini','MB - Bed elevation [m]',WOLF_ARRAY_MB_SINGLE),
            ('.hbinb','MB - Water depth [m]',WOLF_ARRAY_MB_SINGLE),
            ('.qxbinb','MB - Discharge X [m²/s]',WOLF_ARRAY_MB_SINGLE),
            ('.qybinb','MB - Discharge Y [m²/s]',WOLF_ARRAY_MB_SINGLE),
            ('.frotini','MB - Roughness coeff',WOLF_ARRAY_MB_SINGLE),
            ('.epsbinb','MB - Rate of dissipation [m²/s³]',WOLF_ARRAY_MB_SINGLE),
            ('.kbinb','MB - Turbulent kinetic energy [m²/s²]',WOLF_ARRAY_MB_SINGLE)
        ],
                             'Characteristics':[
            ('.mnap','MB Mask [-]', WOLF_ARRAY_MNAP_INTEGER)]}

        # Fine arrays with type
        self.files_fine_array={'Characteristics':[
            ('.napbin','Mask [-]',WOLF_ARRAY_FULL_LOGICAL),
            ('.top','Bed Elevation [m]',WOLF_ARRAY_FULL_SINGLE),
            ('.topini_fine','Bed Elevation - computed [m]',WOLF_ARRAY_FULL_SINGLE),
            ('.frot','Roughness coefficient [law dependent]',WOLF_ARRAY_FULL_SINGLE),
            ('.inf','Infiltration zone [-]',WOLF_ARRAY_FULL_INTEGER),
            ('.hbin','Initial water depth [m]',WOLF_ARRAY_FULL_SINGLE),
            ('.qxbin','Initial discharge along X [m^2/s]',WOLF_ARRAY_FULL_SINGLE),
            ('.qybin','Initial discharge along Y [m^2/s]',WOLF_ARRAY_FULL_SINGLE),
            ('.epsbin','Rate of dissipation [m²/s³]',WOLF_ARRAY_FULL_SINGLE),
            ('.kbin','Turbulent kinetic energy [m²/s²]',WOLF_ARRAY_FULL_SINGLE),
            ('.bridge','Z level under the deck of the bridge [m]',WOLF_ARRAY_FULL_SINGLE),
        ],
        'Forcing':[
            ('.forc','Forcing [m²/s²]  - 3 arrays in one file', WOLF_ARRAY_FULL_SINGLE),
        ],
        'Axis inclination':[
            ('.inc','Axis inclination [-] - 2 arrays in one file', WOLF_ARRAY_FULL_SINGLE),
        ]}

        # Files for the simulation
        self.files_others={'Generic file':[
            ('','First parametric file - historical'),
            ('.par','Parametric file - multiblocks')],
                        'Characteristics':[
            ('.fil','Infiltration hydrographs [m³/s]'),
            ('.mnap','Resulting mesh [-]'),
            ('.trl','Translation to real world [m]')
            ]}

        # Geometry files for the simulation
        self.files_vectors={'Block file':[
            ('.bloc','Blocks geometry')],
                            'Borders':[
            ('.sux','X borders'),
            ('.suy','Y borders')],
                            'Contour':[
            ('.xy','General contour')
        ]}

        self.part_arrays:prev_lst_file = None
        self._mnap:WolfArrayMNAP= None

        self._hbin:WolfArray    = None
        self._qxbin:WolfArray   = None
        self._qybin:WolfArray   = None
        self._frot:WolfArray    = None
        self._inf:WolfArray     = None
        self._top:WolfArray     = None
        self._napbin:WolfArray  = None
        self._epsbin:WolfArray  = None
        self._kbin:WolfArray    = None
        self._zbin:WolfArray    = None

        self._topini:WolfArrayMB  = None
        self._hbinb:WolfArrayMB   = None
        self._qxbinb:WolfArrayMB  = None
        self._qybinb:WolfArrayMB  = None
        self._frotini:WolfArrayMB = None
        self._epsbinb:WolfArrayMB = None
        self._kbinb:WolfArrayMB   = None
        self._zbinb:WolfArrayMB   = None

        if fname is not None:
            fname = str(fname)
            self.filename = fname # Generic filename (aka without extension) but with complete path
            self.mydir = Path(fname).parent.as_posix() # Directory of the generic filename

        self.parent = parent # parent object for insertion in GUI

        if clear:
            # force the clearing of the directory -- Useful for testing and new simulations
            self.clear_directory()

        # Parameters of the simulation
        self.parameters = prev_parameters_simul(parent = self)

        # Read the parameters from file if exists
        self.read_parameters()

        # Read meshes from file is exists
        self.read_mnap()

        # Read the listing file
        self.read_lst()

        # Fichier .XY
        self.xyfile = xy_file(self)

        # Infiltration
        self.infiltration = prev_infiltration(parent = self)

        # Description of the block geometries
        self.bloc_description = blocks_file(parent = self)

        # Virtual grid for contour alignment
        self.magnetic_grid:header_wolf = None

        # # Shared mask for fine arrays (from napbin)
        # self.common_mask = None

        # SUX and SUY files
        self.sux_suy = prev_suxsuy(self)

        self.verify_files()

    @property
    def common_mask_MB(self) -> list[np.ndarray]:
        """ Common mask for multiblock arrays """

        if self.mymnap is not None:
            return self.mymnap.get_all_masks()
        else:
            return None

    @property
    def common_mask(self) -> np.ndarray:
        """ Common mask for fine arrays """

        if self._napbin is not None:
            return self._napbin.array.mask
        else:
            return None

    @common_mask.setter
    def common_mask(self, value):
        """ Set the common mask for fine arrays """

        if self._napbin is not None:
            self._napbin.array.mask = value.copy()

    @property
    def fine_arrays(self) -> list[WolfArray]:
        """ List of fine arrays """

        return [self._hbin, self._qxbin, self._qybin, self._frot, self._inf, self._top, self._napbin, self._epsbin, self._kbin]

    @property
    def MB_arrays(self) -> list[WolfArrayMB]:
        """ List of multiblock arrays """

        return [self._topini, self._hbinb, self._qxbinb, self._qybinb, self._frotini, self._epsbinb, self._kbinb]

    def get_Zones_from_extension(self, extension:str) -> Zones:
        """ Get the Zones from the extension """

        if extension.lower() in '.bloc':
            return self.bloc_description.Zones
        elif extension.lower() in '.xy':
            return self.xyfile.Zones
        elif extension.lower() in ['.sux', '.suy']:
            return self.sux_suy.Zones
        else:
            return None

    def get_wolf_array(self, extension:str) -> WolfArray:
        """ Get the WolfArray from the extension """

        if extension.lower() in '.hbin':
            return self.hbin
        elif extension.lower() in '.qxbin':
            return self.qxbin
        elif extension.lower() in '.qybin':
            return self.qybin
        elif extension.lower() in '.frot':
            return self.frot
        elif extension.lower() in '.inf':
            return self.inf
        elif extension.lower() in '.top':
            return self.top
        elif extension.lower() in '.napbin':
            return self.napbin
        elif extension.lower() in '.epsbin':
            return self.epsbin
        elif extension.lower() in '.kbin':
            return self.kbin
        elif extension.lower() in '.zbin':
            return self.zbin
        elif extension.lower() in '.topini':
            return self.topini
        elif extension.lower() in '.hbinb':
            return self.hbinb
        elif extension.lower() in '.qxbinb':
            return self.qxbinb
        elif extension.lower() in '.qybinb':
            return self.qybinb
        elif extension.lower() in '.frotini':
            return self.frotini
        elif extension.lower() in '.epsbinb':
            return self.epsbinb
        elif extension.lower() in '.kbinb':
            return self.kbinb
        elif extension.lower() in '.mnap':
            return self.mnap
        else:
            return None

    def force_reload(self, which_one:Union[str, WolfArray, WolfArrayMB]):
        """ Force the reload of the WolfArray """

        if which_one is None:
            logging.error(_('No WolfArray to reload'))
            return

        if isinstance(which_one, str):

            locarray = self.get_wolf_array(which_one)

        locarray.read_data()

        assert type(locarray) in [WolfArray, WolfArrayMB], _('Invalid type for WolfArray')

        if 'napbin' in locarray.filename.lower():
            locarray.mask_data(0)

        if issubclass(type(locarray), WolfArrayMB):
            if self.mnap is not None:
                for curblock, curmask in locarray.myblocks.values(), self.common_mask_MB:
                    curblock.array.mask = curmask.copy()

        elif isinstance(locarray, WolfArray):
            if self.common_mask is not None:
                locarray.array.mask = self.common_mask.copy()

    @property
    def mymnap(self) -> WolfArrayMNAP:
        return self.mnap

    @property
    def mnap(self) -> WolfArrayMNAP:

        if self._mnap is None:
            self._mnap = self.read_mnap()
        return self._mnap

    @property
    def hbinb(self):

        if self._hbinb is None:
            self._hbinb = self.read_MB_array('.hbinb')
        return self._hbinb

    @property
    def qxbinb(self):

        if self._qxbinb is None:
            self._qxbinb = self.read_MB_array('.qxbinb')
        return self._qxbinb

    @property
    def qybinb(self):

        if self._qybinb is None:
            self._qybinb = self.read_MB_array('.qybinb')
        return self._qybinb

    @property
    def frotini(self):

        if self._frotini is None:
            self._frotini = self.read_MB_array('.frotini')
        return self._frotini

    @property
    def epsbinb(self):

        if self._epsbinb is None:
            self._epsbinb = self.read_MB_array('.epsbinb')
        return self._epsbinb

    @property
    def kbinb(self):

        if self._kbinb is None:
            self._kbinb = self.read_MB_array('.kbinb')
        return self._kbinb

    @property
    def topini(self):

        if self._topini is None:
            self._topini = self.read_MB_array('.topini')
        return self._topini

    @property
    def hbin(self):

        if self._hbin is None:
            self._hbin = self.read_fine_array('.hbin')
        return self._hbin


    @property
    def zbin(self):

        def new_write_all_zbin(self:"prev_sim2D", newpath:str = None):

            self.zbin2hbin()
            self.hbin.write_all(newpath)

            logging.info(_('zbin is not written - hbin is written instead'))

        if self._zbin is None:

            h = self.hbin
            top = self.top

            if h is not None and top is not None:

                self._zbin = self.hbin + self.top

                self._zbin.write_all = new_write_all_zbin.__get__(self, type(self))

            else:
                self._zbin = None

        return self._zbin

    @property
    def zbinb(self):

        def new_write_all_zbinb(self:"prev_sim2D", newpath:str = None):

            self.zbinb2hbinb()
            self.hbinb.write_all(newpath)

            logging.info(_('zbinb is not written - hbinb is written instead'))

        if self._zbinb is None:

            hbinb = self.hbinb
            topini = self.topini

            if hbinb is not None and topini is not None:
                self._zbinb = self.hbinb + self.topini

                self._zbinb.write_all = new_write_all_zbinb.__get__(self, type(self))

            else:
                self._zbinb = None

        return self._zbinb

    def zbinb2hbinb(self):
        """ Convert the zbinb to hbinb """

        for zblock, hblock, topblock in zip(self.zbinb.myblocks.values(), self.hbinb.myblocks.values(), self.topini.myblocks.values()):
            hblock.array.data[:,:] = zblock.array.data[:,:] - self.topini.array.data[:,:]
            hblock.array.data[hblock.array.data < 0.] = 0.

    def hbinb2zbinb(self):
        """ Convert the hbinb to zbinb """

        for zblock, hblock, topblock in zip(self.zbinb.myblocks.values(), self.hbinb.myblocks.values(), self.topini.myblocks.values()):
            zblock.array.data[:,:] = hblock.array.data[:,:] + topblock.array.data[:,:]
            zblock.array.data[zblock.array.data < topblock.array.data] = topblock.array.data[zblock.array.data < topblock.array.data]

    def zbin2hbin(self):
        """ Convert the zbin to hbin """

        self.hbin.array.data[:,:] = self.zbin.array.data[:,:] - self.top.array.data[:,:]
        self.hbin.array.data[self.hbin.array.data < 0.] = 0.

    def hbin2zbin(self):
        """ Convert the hbin to zbin """

        self.zbin.array.data[:,:] = self.hbin.array.data[:,:] + self.top.array.data[:,:]
        self.zbin.array.data[self.zbin.array.data < self.top.array.data] = self.top.array.data[self.zbin.array.data < self.top.array.data]

    @property
    def qxbin(self):

        if self._qxbin is None:
            self._qxbin = self.read_fine_array('.qxbin')
        return self._qxbin

    @property
    def qybin(self):

        if self._qybin is None:
            self._qybin = self.read_fine_array('.qybin')
        return self._qybin

    @property
    def frot(self):

        if self._frot is None:
            self._frot = self.read_fine_array('.frot')
        return self._frot

    @property
    def inf(self):

        if self._inf is None:
            self._inf = self.read_fine_array('.inf')
        return self._inf

    @property
    def top(self):

        if self._top is None:
            self._top = self.read_fine_array('.top')
        return self._top

    @property
    def napbin(self):

        if self._napbin is None:
            self._napbin = self.read_fine_array('.napbin')
        return self._napbin

    @property
    def epsbin(self):

        if self._epsbin is None:
            self._epsbin = self.read_fine_array('.epsbin')
        return self._epsbin

    @property
    def kbin(self):

        if self._kbin is None:
            self._kbin = self.read_fine_array('.kbin')
        return self._kbin

    def force_mask(self):
        """ Copy mask """

        for cur in self.fine_arrays:
            if cur is not None:
                cur.array.mask[:,:] = self.common_mask[:,:]
                if cur.plotted:
                    cur.reset_plot()

        for curMB in self.MB_arrays:
            if curMB is not None:
                for curblock, curmask in zip(curMB.myblocks.values(), self.common_mask_MB):
                    curblock.array.mask[:,:] = curmask[:,:]

                if curMB.plotted:
                    curMB.reset_plot()


    def force_load(self, force_reload = False):
        """
        Force the (re)loading of the fine arrays

        :params force_reload: force the reloading of the fine arrays

        """

        if force_reload:
            self.force_unload()

        if self.filenamegen is None:

            if self._napbin is None:
                self.create_napbin()

            self.create_fine_arrays()
        else:

            ext  = ['napbin','top','hbin','qxbin','qybin','frot','inf','epsbin','kbin']
            dest = [self._napbin, self._top, self._hbin, self._qxbin, self._qybin, self._frot, self._inf, self._epsbin, self._kbin]

            if self.parameters.has_turbulence:
                for curext, curdest in zip(ext, dest):
                    if curdest is None:
                        curdest = self.read_fine_array('.' + curext)
            else:
                for curext, curdest in zip(ext[:6], dest[:6]):
                    if curdest is None:
                        curdest = self.read_fine_array('.' + curext)

    def force_unload(self):
        """ Force the unloading of the fine arrays """

        self._napbin = None
        self._top = None
        self._hbin = None
        self._qxbin = None
        self._qybin = None
        self._frot = None
        self._inf = None
        self._epsbin = None
        self._kbin = None
        self._zbin = None

        self._hbinb = None
        self._qxbinb = None
        self._qybinb = None
        self._frotini = None
        self._epsbinb = None
        self._kbinb = None
        self._zbinb = None


    def save_arrays_modifications(self):
        """ Save the modifications of the arrays """

        for curarray in self.fine_arrays:
            if curarray is not None:
                curarray.write_all()
                logging.debug(f'Array {curarray.filename} saved')

        if self._zbin is not None:
            if self._zbin.plotted:
                self.zbin2hbin()
                self._hbin.write_all()
                logging.info(f'Array {self._hbin.filename} saved from zbin')

        for curarray in self.MB_arrays:
            if curarray is not None:
                curarray.write_all()
                logging.debug(f'Array {curarray.filename} saved')

        if self._zbinb is not None:
            if self._zbinb.plotted:
                self.zbinb2hbinb()
                self._hbinb.write_all()
                logging.info(f'Array {self.hbinb.filename} saved from zbinb')

    @property
    def translate_origin2zero(self):
        """ Translate the origin to zero """

        self.bloc_description.translate_origin2zero

    @translate_origin2zero.setter
    def translate_origin2zero(self, value:bool):
        self.bloc_description.translate_origin2zero = value

    @property
    def filenamegen(self):
        return self.filename

    @filenamegen.setter
    def filenamegen(self, value:str):
        self.filename = str(value)

    @property
    def dx(self):
        return self.parameters._fine_mesh_dx

    @dx.setter
    def dx(self, value:float):
        self.parameters._fine_mesh_dx = value

    @property
    def dy(self):
        return self.parameters._fine_mesh_dy

    @dy.setter
    def dy(self, value:float):
        self.parameters._fine_mesh_dy = value

    @property
    def origx(self):
        return self.parameters._fine_mesh_origx

    @origx.setter
    def origx(self, value:float):
        self.parameters._fine_mesh_origx = value

    @property
    def endx(self):
        return self.parameters._fine_mesh_origx + float(self.parameters._fine_mesh_nbx) * self.parameters._fine_mesh_dx

    @property
    def endy(self):
        return self.parameters._fine_mesh_origy + float(self.parameters._fine_mesh_nby) * self.parameters._fine_mesh_dy

    @property
    def origy(self):
        return self.parameters._fine_mesh_origy

    @origy.setter
    def origy(self, value:float):
        self.parameters._fine_mesh_origy = value

    @property
    def nbx(self):
        return self.parameters._fine_mesh_nbx

    @nbx.setter
    def nbx(self, value:int):
        self.parameters._fine_mesh_nbx = value

    @property
    def nby(self):
        return self.parameters._fine_mesh_nby

    @property
    def translx(self):
        return self.parameters._fine_mesh_translx

    @translx.setter
    def translx(self, value:float):
        self.parameters._fine_mesh_translx = value

    @property
    def transly(self):
        return self.parameters._fine_mesh_transly

    @transly.setter
    def transly(self, value:float):
        self.parameters._fine_mesh_transly = value

    @property
    def external_border(self) -> vector:
        """ Return the external border of the simulation """

        return self.bloc_description.external_border

    @property
    def is_multiblock(self):
        return self.mnap.nb_blocks>1

    @property
    def nb_blocks(self):

        if self.mnap is None:
            if self.bloc_description is None:
                return 0
            else:
                return self.bloc_description.nb_blocks
        else:
            assert self.bloc_description.nb_blocks == self.mnap.nb_blocks, 'Incoherent number of blocks'
            return self.mnap.nb_blocks


    def search_magnetic_grid(self):
        """ Search the magnetic grid properties """

        # Search the dimension in the bloc file
        self.bloc_description.search_magnetic_grid()

        dx_max = self.bloc_description.dx_max
        dy_max = self.bloc_description.dy_max

        if self.magnetic_grid is None:
            logging.error('Magnetic grid not found -- Please check it manually')
            self.magnetic_grid = None
            return

        #Verify the magnetic grid on the external border

        vec_xmin = self.external_border.xmin
        vec_xmax = self.external_border.xmax
        vec_ymin = self.external_border.ymin
        vec_ymax = self.external_border.ymax

        ox = self.parameters._fine_mesh_origx
        oy = self.parameters._fine_mesh_origy
        dx = self.parameters._fine_mesh_dx
        dy = self.parameters._fine_mesh_dy
        nx = self.parameters._fine_mesh_nbx
        ny = self.parameters._fine_mesh_nby


        aligne_xmin = ox + dx_max + 2. * dx
        aligne_ymin = oy + dy_max + 2. * dy
        aligne_xmax = ox + float(nx) * dx  - dx_max - 2. * dx
        aligne_ymax = oy + float(ny) * dy  - dy_max - 2. * dy

        test_xmin, test_ymin = self.align2grid(vec_xmin, vec_ymin)
        test_xmax, test_ymax = self.align2grid(vec_xmax, vec_ymax)

        if np.isclose(aligne_xmin, test_xmin) and np.isclose(aligne_ymin, test_ymin) and np.isclose(aligne_xmax, test_xmax) and np.isclose(aligne_ymax, test_ymax):
            pass
        else:
            logging.error('Magnetic grid not found -- Please check it manually')
            self.magnetic_grid = None

    def create_fine_arrays(self, default_frot:float=0.04, with_tubulence = False):
        """
        Create the fine arrays

        :param default_frot: default value for the roughness coefficient
        :param with_tubulence: create the turbulence arrays (epsbin and kbin)

        """

        if self.napbin is None:
            self.create_napbin()

        if self.common_mask is None:
            logging.error('Common mask not defined -- Please check it manually')
            return

        head = self.get_header()

        ext_sng = ['.top', '.hbin', '.qxbin', '.qybin', '.frot']
        dest_sng = [self._top, self._hbin, self._qxbin, self._qybin, self._frot]

        for curext, curdest in zip(ext_sng, dest_sng):
            curdest = WolfArray(srcheader=head, whichtype=WOLF_ARRAY_FULL_SINGLE, nullvalue=99999.)
            curdest.array.mask = self.common_mask.copy()

            if curext == '.frot':
                curdest.array.data[:,:] = default_frot
            else:
                curdest.array.data[:,:] = 0.

            curdest.set_nullvalue_in_mask()

            if self.filenamegen is not None:
                curdest.write_all(self.filenamegen + curext)

        ext_int = ['.inf']
        dest_int = [self._inf]

        for curext, curdest in zip(ext_int, dest_int):
            curdest = WolfArray(srcheader=head, whichtype=WOLF_ARRAY_FULL_INTEGER)
            curdest.array.mask = self.common_mask.copy()

            curdest.array.data[:,:] = 0

            if self.filenamegen is not None:
                curdest.write_all(self.filenamegen + curext)

        if with_tubulence:
            ext_sng = ['.epsbin', '.kbin']
            dest_sng = [self._epsbin, self._kbin]

            for curext, curdest in zip(ext_sng, dest_sng):
                curdest = WolfArray(srcheader=head, whichtype=WOLF_ARRAY_FULL_SINGLE, nullvalue=99999.)
                curdest.array.mask = self.common_mask.copy()

                curdest.array.data[:,:] = 0.
                curdest.set_nullvalue_in_mask()

                if self.filenamegen is not None:
                    curdest.write_all(self.filenamegen + curext)

    def create_napbin(self):
        """
        Create the napbin file

        Based on the external border, it will create a napbin file
        with fine mesh size.

        """

        # Tests
        # *****

        if self.bloc_description.external_border is None:
            logging.error('External border not defined')
            return

        myhead = self.get_header()

        if myhead.nbx == 0 or myhead.nby == 0:
            logging.error('Invalid grid size -- Check your parameters')
            return

        if myhead.dx == 0 or myhead.dy == 0:
            logging.error('Invalid grid size -- Check your parameters')
            return

        # Create
        # ******

        # New wolfarray from header
        self._napbin = WolfArray(srcheader=myhead, whichtype=WOLF_ARRAY_FULL_LOGICAL)

        # Mask outside the external border
        self._napbin.mask_outsidepoly(self.bloc_description.external_border, eps=1.e-6)

        # Write on disk
        if self.filenamegen is not None:
            self._napbin.write_all(self.filenamegen + '.napbin')

        # self.common_mask = self._napbin.array.mask.copy()

    def create_sux_suy(self):
        """
        Create the X and Y borders

        """

        napbin = self.read_fine_array('.napbin')

        if napbin is None:
            logging.error('Napbin file not found')
            return

        ret = napbin.suxsuy_contour(self.filename) #, abs=True)

        self.sux_suy.read_file()

    def set_mesh_fine_size(self, dx:float, dy:float):
        """
        Set the mesh size and origin

        :param dx: mesh size along X
        :param dy: mesh size along Y

        """

        self.parameters._fine_mesh_dx = dx
        self.parameters._fine_mesh_dy = dy

    def set_external_border_vector(self, contour:vector):
        """ Add the external border to the bloc file """

        self.bloc_description.set_external_border(contour)

    def set_external_border_xy(self, xmin:float, xmax:float, ymin:float, ymax:float):
        """ Set the external border to the bloc file """

        curborder = vector(name='external border')

        vert1 = wolfvertex(xmin, ymin)
        vert2 = wolfvertex(xmax, ymin)
        vert3 = wolfvertex(xmax, ymax)
        vert4 = wolfvertex(xmin, ymax)

        curborder.add_vertex([vert1, vert2, vert3, vert4])
        curborder.close_force()

        self.set_external_border_vector(curborder)

    def set_external_border_nxny(self, xmin:float, ymin:float, nbx:int, nby:int, dx:float, dy:float):
        """ Set the external border to the bloc file """

        curborder = vector(name='external border')

        vert1 = wolfvertex(xmin, ymin)
        vert2 = wolfvertex(xmin + dx*float(nbx), ymin)
        vert3 = wolfvertex(xmin + dx*float(nbx), ymin + dy*float(nby))
        vert4 = wolfvertex(xmin, ymin + dy*float(nby))

        curborder.add_vertex([vert1, vert2, vert3, vert4])
        curborder.close_force()

        self.set_external_border_vector(curborder)

    def set_external_border_header(self, header:header_wolf):
        """ Set the external border to the bloc file """

        self.set_external_border_nxny(header.origx, header.origy, header.nbx, header.nby, header.dx, header.dy)

    def set_external_border_wolfarray(self, src_array:WolfArray, mode:Literal['header', 'contour'], abs:bool=True):
        """
        Set the external border to the bloc file

        :param src_array: source array
        :param mode: mode to use
        :param abs: if True, use the World coordinates -- (ox+trlx, oy+trly), else use the local coordinates -- (ox, oy)

        """

        assert isinstance(src_array, WolfArray), 'Invalid array type'

        if isinstance(mode, str):
            mode = mode.lower()

        assert mode in ['header', 'contour'], 'Invalid mode'

        if mode == 'header':
            header = src_array.get_header()
            self.set_external_border_nxny(header.origx, header.origy, header.nbx, header.nby, header.dx, header.dy)

        else:

            sux, suy, vect, interior = contour = src_array.suxsuy_contour(abs = abs)

            self.set_external_border_vector(vect)


    def add_block(self, contour:vector, dx:float, dy:float, name:str=''):
        """ Add a block to the bloc file """

        self.bloc_description.add_block(contour, dx, dy)

        self.parameters.add_block(name = name)

    def modify_block(self, idx:int, contour:vector, dx:float, dy:float):
        """ Modify a block in the bloc file """

        assert idx > 0 and idx <= self.nb_blocks, f'Invalid block index: {idx}'

        self.bloc_description.my_blocks[idx-1].contour.myvertices = contour.myvertices.copy()
        self.bloc_description.my_blocks[idx-1].dx = dx
        self.bloc_description.my_blocks[idx-1].dy = dy

    def reset_blocks(self):
        """ Reset the bloc file """

        self.bloc_description.reset_blocks()

    def reset_external_border(self):
        """ Reset the external border """

        self.bloc_description.reset_external_border()

    def set_mesh_only(self):
        """ Set the simulation to mesh only """

        self.parameters.set_mesh_only()

    def unset_mesh_only(self):
        """ Unset the simulation to mesh only """

        self.parameters.unset_mesh_only()

    def clear_directory(self):
        """ Clear the directory """

        import shutil

        if exists(self.mydir):
            shutil.rmtree(self.mydir)

        makedirs(self.mydir, exist_ok=True)

    def _set_nbx_nby(self):
        """ Set the number of cells along X and Y """

        if self.bloc_description.external_border is None:
            logging.error('External border not defined')
            return

        if self.nb_blocks ==0:
            logging.error('No block defined -- Add a block first')
            return

        if self.parameters._fine_mesh_dx == 0 or self.parameters._fine_mesh_dy == 0:
            logging.error('Invalid mesh size -- Use set_mesh_fine_size first')
            return

        if self.magnetic_grid is None:
            logging.warning('Magnetic grid not defined -- Force to (dx,dy) = (1.,1.) and (ox,oy) = (0.,0.)')
            self.set_magnetic_grid(1., 1., 0., 0.)

        # Contour externe
        extern = self.bloc_description.external_border

        # Borne minimale et maximale du contour externe alignée sur le grid magnétique
        xmin, ymin = self.align2grid(extern.xmin, extern.ymin)
        xmax, ymax = self.align2grid(extern.xmax, extern.ymax)

        dxmax = self.bloc_description.dx_max
        dymax = self.bloc_description.dy_max

        dxfin = self.parameters._fine_mesh_dx
        dyfin = self.parameters._fine_mesh_dy

        trlx = self.parameters._fine_mesh_translx
        trly = self.parameters._fine_mesh_transly

        xmin -= trlx + (dxmax + 2*dxfin)
        ymin -= trly + (dymax + 2*dyfin)

        xmax += -trlx + (dxmax + 2*dxfin)
        ymax += -trly + (dymax + 2*dyfin)

        self.parameters._fine_mesh_origx = xmin
        self.parameters._fine_mesh_origy = ymin

        # np.round is choosen to avoid numerical issues
        # Remark : Fortran will mesh in Float32, not in Float64
        self.parameters._fine_mesh_nbx = int(np.round((xmax - xmin) / dxfin))
        self.parameters._fine_mesh_nby = int(np.round((ymax - ymin) / dyfin))

    @classmethod
    def check_wolfcli(cls):
        """ Check if wolfcli is available """

        import distutils.spawn

        wolfcli = distutils.spawn.find_executable("wolfcli.exe")

        if wolfcli is None:
            logging.error('wolfcli.exe not found')

        return wolfcli

    def run_wolfcli(self, command:str=''):
        """ Run wolfcli """

        import subprocess

        wolfcli = self.check_wolfcli()

        if wolfcli:

            if command == '':
                subprocess.Popen(['start',
                                  'cmd.exe',
                                  '/k',
                                  wolfcli,
                                  'run_wolf2d_prev',
                                  'genfile=' + Path(self.filenamegen).name],
                                 cwd=Path(self.filenamegen).parent,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            else:
                ret = subprocess.run([wolfcli,command],
                                 shell=False,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)

            pass


    def mesh(self, force_meshonly = True):
        """ Mesh the domain """

        import subprocess
        import shlex

        wolfcli = self.check_wolfcli()

        if wolfcli is None:
            return False

        if force_meshonly:
            self.set_mesh_only()

        self.reset_mnap()

        self.bloc_description.modify_extent()

        self.bloc_description.write_file()

        self._set_nbx_nby()

        self.parameters.write_file()

        # launch wolfcli
        ret = subprocess.run([wolfcli, 'run_wolf2d_prev', 'genfile=' + Path(self.filenamegen).name], cwd=Path(self.filenamegen).parent, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if ret.returncode != 0:
            logging.error(f'Error in wolfcli: {ret.stderr.decode()}')
            return False

        self.read_mnap()

        self.create_napbin()

        if force_meshonly:
            self.unset_mesh_only()

        return True

    def set_magnetic_grid(self, dx:float, dy:float, origx:float, origy:float):
        """
        Définition de la grille magnétique

        :param dx: taille de maille selon X
        :type dx: float
        :param dy: taille de maille selon Y
        :type dy: float
        :param origx: origine selon X (coordonnée du noeud d'intersection)
        :type origx: float
        :param origy: origine selon Y (coordonnée du noeud d'intersection)
        :type origy: float
        """

        self.magnetic_grid = header_wolf()
        self.magnetic_grid.dx = dx
        self.magnetic_grid.dy = dy

        self.magnetic_grid.origx = origx
        self.magnetic_grid.origy = origy

    def align2grid(self, x:float, y:float):
        """ Alignement sur la grille magnétique """

        if self.magnetic_grid is None:
            return x,y

        x, y = self.magnetic_grid.align2grid(x, y)

        return x,y


    def read_infil(self):
        """ Lecture du fichier .fil si présent """

        if self.filenamegen is not None:
            if exists(self.filenamegen + '.fil'):
                self.infiltration.read_file()
        else:
            logging.debug('No filenamegen defined')

    def read_lst(self):
        """ Lecture du fichier .lst si présent """

        self.part_arrays = prev_lst_file(parent=self)
        self.part_arrays.read_file()

    def read_mnap(self):
        """ Lecture du fichier .mnap si présent """

        if self.filenamegen is not None:
            if exists(self.filenamegen + '.mnap') :
                self._mnap = WolfArrayMNAP(self.filenamegen)
            else:
                self._mnap = None
        else:
            logging.debug('No filenamegen defined')

    def reset_mnap(self):
        """ Réinitialisation du fichier .mnap """

        self._mnap = None

    def read_parameters(self):
        """
        Lecture des paramètres de simulation
        """

        if self.filenamegen is not None:
            if exists(self.filenamegen + '.par') :
                self.parameters.read_file()
            else:
                logging.info(f'File {self.filenamegen + ".par"} not found')
        else:
            logging.debug('No filenamegen defined')

    def save_parameters(self):
        """
        Sauvegarde des paramètres de simulation

        Les conditions limites sont contenues dans le fichier .par
        """

        self.parameters.write_file()

    def save(self):
        """ Sauvegarde des données """

        if self.filenamegen is not None:

            self.bloc_description.write_file()
            self.save_parameters()
            self.infiltration.write_file()
            self.part_arrays.write_file()
            self.save_arrays_modifications()

        else:
            logging.debug('No filenamegen defined')

    def get_parameters_groups(self):
        """
        Renvoi des groupes de paramètres de simulation
        """

        groups_sim = self.parameters._get_groups()

        if self.nb_blocks > 0:
            groups_blocks = self.parameters.blocks[0]._get_groups()
        else:
            tmp_block = prev_parameters_blocks()
            groups_blocks = tmp_block._get_groups()

        groups = list(set(groups_sim + groups_blocks))

        groups.sort()

        return groups

    def get_parameters_in_group(self, group:str):
        """
        Renvoi des paramètres d'un groupe de paramètres de simulation
        """

        groups = self.get_parameters_groups()
        groups = [cur.lower() for cur in groups]

        if group.lower() not in groups:
            logging.error(f'Group {group} not found')
            return

        all = self.get_parameters_groups_and_names()

        params = [cur[1] for cur in all if cur[0].lower() == group.lower()]

        return params

    def get_parameters_groups_and_names(self):
        """
        Renvoi des groupes et des noms de paramètres de simulation
        """

        groups_sim = self.parameters._get_groups_and_names()

        if self.nb_blocks > 0:
            groups_blocks = self.parameters.blocks[0]._get_groups_and_names()
        else:
            tmp_block = prev_parameters_blocks()
            groups_blocks = tmp_block._get_groups_and_names()

        groups_and_names = groups_sim + groups_blocks

        groups_and_names.sort(key=lambda x: x[0])

        return groups_and_names

    def get_active_parameters(self):
        """ Renvoi des paramètres de simulation actifs """

        tmp, params = self.parameters.get_active_params()
        return params

    def get_active_parameters_block(self, block:int):
        """ Renvoi des paramètres de simulation actifs pour un bloc donné """

        if block > 0 and block <= self.nb_blocks:
            params = self.parameters.get_active_params_block(block)

            return params

        else:
            logging.error(f'Block {block} does not exist')
            return {}

    def get_active_parameters_extended(self):
        """ Renvoi des paramètres de simulation actifs """

        return self.parameters.get_active_params_extended()

    def get_all_parameters(self):
        """ Renvoi de tous les paramètres de simulation """

        return self.parameters.get_all_params_extended()

    def get_all_parameters_block(self, block:int):
        """ Renvoi de tous les paramètres de simulation pour un bloc donné """

        if block > 0 and block <= self.nb_blocks:
            return self.parameters.get_all_params_block(block)
        else:
            logging.error(f'Block {block} does not exist')
            return {}

    def get_parameter(self, group:str, name:str, block:int=None):
        """
        Renvoi d'un paramètre de simulation

        :param group: groupe du paramètre
        :type group: str
        :param name: nom du paramètre
        :type name: str
        :param block: numéro du bloc (1-based)
        :type block: int
        """

        if isinstance(block, str):
            if block.lower() == 'all':
                block = -1
            else:
                block = int(block)

                assert block > 0 and block <= self.nb_blocks, 'Invalid block index'
        elif block is not None:
            assert isinstance(block, int),  'invalid block index type'

        assert isinstance(group, str), 'invalid group type'
        assert isinstance(name, str), 'invalid name type'

        sanit_group, sanit_name = self.sanitize_group_name(group, name)

        if sanit_group is None or sanit_name is None:
            logging.error(f'Parameter {group} - {name} not found')

        if self.parameters.is_block(sanit_group, sanit_name) and block is None:
            logging.error(f'Parameter {name} is a block parameter -- Please specify a block')

        if block is None:
            return self.parameters.get_parameter(sanit_group, sanit_name)

        else:
            if block > 0 and block <= self.nb_blocks:
                return self.parameters.blocks[block-1].get_param(sanit_group, sanit_name)
            elif block == -1:
                return [self.parameters.blocks[i].get_parameter(sanit_group, sanit_name) for i in range(self.nb_blocks)]
            else:
                logging.error(f'Block {block} does not exist')
                return None


    def set_parameter(self, group:str, name:str, value:Union[float, int], block:int=None):
        """
        Modification d'un paramètre de simulation

        :param group: groupe du paramètre
        :type group: str
        :param name: nom du paramètre
        :type name: str
        :param value: valeur du paramètre
        :type value: Union[float, int]
        :param block: numéro du bloc (1-based) -- -1 == all blocks
        :type block: int

        """

        if isinstance(block, str):
            if block.lower() == 'all':
                block = -1
            else:
                block = int(block)

                assert block > 0 and block <= self.nb_blocks, 'Invalid block index'
        elif block is not None:
            assert isinstance(block, int),  'invalid block index type'

        assert isinstance(group, str), 'invalid group type'
        assert isinstance(name, str), 'invalid name type'

        assert isinstance(value, (int, float)), 'invalid value type'

        sanit_group, sanit_name = self.sanitize_group_name(group, name)

        if sanit_group is None or sanit_name is None:
            logging.error(f'Parameter {group} - {name} not found')
            return

        if self.parameters.is_block(sanit_group, sanit_name) and block is None:
            logging.error(f'Parameter {name} is a block parameter -- Please specify a block')
            return


        if 'not editable' in name:
            logging.error(f'Parameter {name} is not editable')
            return

        if block is None:
            self.parameters.set_parameter(sanit_group, sanit_name, value)
        else:
            if block > 0 and block <= self.nb_blocks:
                self.parameters.blocks[block-1].set_parameter(sanit_group, sanit_name, value)
            elif block == -1:
                for i in range(self.nb_blocks):
                    self.parameters.blocks[i].set_parameter(sanit_group, sanit_name, value)
            else:
                logging.error(f'Block {block} does not exist')

    def get_group_name_from_list(self,
                                 target:Literal['Global', 'Block'] = 'Global',
                                 which:Literal['General', 'Debug'] = 'General'):
        """
        Get group and name from a list for VB6 nostalgia / specialist mode

        """

        assert isinstance(target, str), 'Invalid target type'
        assert isinstance(which, str), 'Invalid which type'

        assert target.lower() in ['global', 'block'], 'Invalid target'
        assert which.lower() in ['general', 'debug'], 'Invalid which'

        if target.lower() == 'global':

            if which.lower() == 'general':

                return [(group, name) for group, name in zip(self.parameters.gen_groups, self.parameters.gen_names)]

            else:

                return [(group, name) for group, name in zip(self.parameters.debug_groups, self.parameters.debug_names)]

        else:
            if which.lower() == 'general':
                return [(group, name) for group, name in zip(prev_parameters_blocks().gen_groups, prev_parameters_blocks().gen_names)]
            else:
                return [(group, name) for group, name in zip(prev_parameters_blocks().debug_groups, prev_parameters_blocks().debug_names)]

    def get_parameters_from_list(self,
                                 target:Literal['Global', 'Block'] = 'Global',
                                 which:Literal['General', 'Debug'] = 'General',
                                 idx_block:int=0):
        """
        Get parameters from a list for VB6 nostalgia / specialist mode

        :param target: target of the parameters
        :type target: Literal['Global', 'Block']
        :param which: which parameters to get
        :type which: Literal['General', 'Debug']
        :param idx_block: index of the block (1-based)
        :type idx_block: int

        """

        assert isinstance(idx_block, int), 'Invalid block index type'
        assert isinstance(target, str), 'Invalid target type'
        assert isinstance(which, str), 'Invalid which type'

        assert target.lower() in ['global', 'block'], 'Invalid target'
        assert which.lower() in ['general', 'debug'], 'Invalid which'

        if target.lower() == 'global':

            if which.lower() == 'general':

                return self.parameters._get_general_params()

            else:

                return self.parameters._get_debug_params()

        else:

            assert idx_block > 0 and idx_block <= self.nb_blocks, 'Invalid block index'

            if which.lower() == 'general':

                return self.parameters.blocks[idx_block-1]._get_general_params()

            else:

                return self.parameters.blocks[idx_block-1]._get_debug_params()

    def set_parameters_from_list(self,
                                 target:Literal['Global', 'Block'] = 'Global',
                                 which:Literal['General', 'Debug'] = 'General',
                                 values:list[int, float] = [],
                                 idx_block:int=0):
        """
        Set parameters from a list for VB6 nostalgia / specialist mode

        :param target: target of the parameters
        :type target: Literal['Global', 'Block']
        :param which: which parameters to set
        :type which: Literal['General', 'Debug']
        :param values: list of values
        :type values: list[int, float]
        :param idx_block: index of the block (1-based)
        :type idx_block: int

        """

        assert isinstance(values, list), 'Invalid parameter type'
        assert isinstance(idx_block, int), 'Invalid block index type'
        assert isinstance(target, str), 'Invalid target type'
        assert isinstance(which, str), 'Invalid which type'

        assert target.lower() in ['global', 'block'], 'Invalid target'
        assert which.lower() in ['general', 'debug'], 'Invalid which'

        if target.lower() == 'global':

            if which.lower() == 'general':
                gen = self.parameters._get_general_params()
                assert len(gen) == len(values), 'Invalid number of parameters -- You must provide {} parameters'.format(len(gen))

                self.parameters._set_general_params(values)

            else:
                dbg = self.parameters._get_debug_params()
                assert len(dbg) == len(values), 'Invalid number of parameters -- You must provide {} parameters'.format(len(dbg))

                self.parameters._set_debug_params(values)

        else:

            assert idx_block > 0 and idx_block <= self.nb_blocks, 'Invalid block index'

            if which.lower() == 'general':
                gen = self.parameters.blocks[0]._get_general_params()
                assert len(gen) == len(values), 'Invalid number of parameters -- You must provide {} parameters'.format(len(gen))

                self.parameters.blocks[idx_block-1]._set_general_params(values)

            else:
                dbg = self.parameters.blocks[0]._get_debug_params()
                assert len(dbg) == len(values), 'Invalid number of parameters -- You must provide {} parameters'.format(len(dbg))

                self.parameters.blocks[idx_block-1]._set_debug_params(values)

    def get_mapviewer(self):
        if self.parent is None:
            return None

        return self.parent.get_mapviewer()

    def get_header(self, abs=False):
        """
        Renvoi d'un header avec les infos géométriques de la simulation

        Version monobloc et résolution fine

        :param abs: si True, les origines sont décalées des translations et les translations sont mises à 0
        :type abs: bool
        """

        curhead = header_wolf()

        curhead.nbx = self.parameters._fine_mesh_nbx
        curhead.nby = self.parameters._fine_mesh_nby

        curhead.dx = self.parameters._fine_mesh_dx
        curhead.dy = self.parameters._fine_mesh_dy

        curhead.origx = self.parameters._fine_mesh_origx
        curhead.origy = self.parameters._fine_mesh_origy

        curhead.translx = self.parameters._fine_mesh_translx
        curhead.transly = self.parameters._fine_mesh_transly

        if abs:
            curhead.origx += curhead.translx
            curhead.origy += curhead.transly
            curhead.translx = 0.
            curhead.transly = 0.

        return curhead

    def get_header_MB(self,abs=False):
        """
        Renvoi d'un header avec les infos multi-blocs

        :param abs: si True, les origines sont décalées des translations et les translations sont mises à 0
        :type abs: bool
        """

        myheader:header_wolf

        if self.mnap is None:
            return header_wolf()

        myheader = self.mnap.get_header(abs=abs)
        for curblock in self.mnap.myblocks.values():
            myheader.head_blocks[getkeyblock(curblock.blockindex)] = curblock.get_header(abs=abs)
        return  myheader

    def verify_files(self):
        """
        Vérification de la présence des en-têtes dans les différents fichiers présents sur disque.

        Cette routine est nécessaire pour s'assurer de la cohérence des headers. Certaines versions de l'interface VB6
        présentaient un bug lors de la sauvegarde des fichiers ce qui peut avoir comme conséquence de décaler les données
        (double application des translations vers le monde réel).

        """

        if self.nb_blocks == 0:
            logging.debug('No block defined -- Add a block first')
            return

        fhead = self.get_header()
        mbhead = self.get_header_MB()

        fine = self.files_fine_array['Characteristics']
        for curextent,text,wolftype in fine:
            fname = self.filenamegen + curextent
            if exists(fname):
                logging.debug(f'Verifying header for {fname}')
                fname += '.txt'
                fhead.write_txt_header(fname, wolftype, forceupdate=True)

        mb = self.files_MB_array['Initial Conditions']
        for curextent,text,wolftype in mb:
            fname = self.filenamegen + curextent
            if exists(fname):
                logging.debug(f'Verifying header for {fname}')
                fname += '.txt'
                mbhead.write_txt_header(fname, wolftype, forceupdate=True)

        fname = self.filenamegen + '.lst'
        if not exists(fname):
            logging.warning(f'File {fname} does not exist -- Creating it')
            with open(fname,'w') as f:
                f.write('0\n'*8)

    def get_filepath(self, which:Literal['.top',
                                         '.hbin',
                                         '.qxbin',
                                         '.qybin',
                                         '.napbin',
                                         '.topini_fine',
                                         '.frot',
                                         '.inf',
                                         '.kbin',
                                         '.epsbin',
                                         '.hbinb',
                                         '.qxbinb',
                                         '.qybinb',
                                         '.kbinb',
                                         '.epsbinb',
                                         '.topini',
                                         '.frotini']=''):
        """ Renvoi du chemin complet d'un fichier """

        if not which.startswith('.'):
            which = '.' + which

        return self.filenamegen + str(which)

    def exists_file(self, which:Literal['.top',
                                        '.hbin',
                                        '.qxbin',
                                        '.qybin',
                                        '.napbin',
                                        '.topini_fine',
                                        '.frot',
                                        '.inf',
                                        '.kbin',
                                        '.epsbin',
                                        '.hbinb',
                                        '.qxbinb',
                                        '.qybinb',
                                        '.kbinb',
                                        '.epsbinb',
                                        '.topini',
                                        '.frotini',
                                        ]='') -> bool:
        """ Vérification de l'existence d'un fichier """

        return Path(self.get_filepath(which)).exists()

    def last_modification_date(self, which:Literal['.top',
                                                   '.hbin',
                                                   '.qxbin',
                                                   '.qybin',
                                                   '.napbin',
                                                   '.topini_fine',
                                                   '.frot',
                                                   '.inf',
                                                   '.kbin',
                                                   '.epsbin',
                                                   '.hbinb',
                                                   '.qxbinb',
                                                   '.qybinb',
                                                   '.kbinb',
                                                   '.epsbinb',
                                                   '.topini',
                                                   '.frotini',
                                                   ]='', tz = tz.utc) -> str:
        """ Renvoi de la date de dernière modification d'un fichier """

        return dt.fromtimestamp(Path(self.get_filepath(which)).stat().st_mtime, tz=tz)

    def read_fine_array(self, which:Literal['.top',
                                            '.hbin',
                                            '.qxbin',
                                            '.qybin',
                                            '.napbin',
                                            '.topini_fine',
                                            '.frot',
                                            '.inf',
                                            '.kbin',
                                            '.epsbin',
                                            ]='') -> WolfArray:
        """
        Lecture d'une matrice fine

        :param which: suffixe du fichier
        :type which: str -- extension with point (e.g. '.hbin')
        :return: WolfArray
        """

        which = str(which).lower()
        if not which.startswith('.'):
            which = '.' + which

        #FIXME : replace by checking the dictionnary
        wolftype = WOLF_ARRAY_FULL_SINGLE

        if which == '.inf':
            wolftype = WOLF_ARRAY_FULL_INTEGER

        if self.filenamegen is None:
            # Instance de simulation en mémoire, sans fichier

                myarray = WolfArray(whichtype=wolftype, srcheader=self.get_header())

                if which == '.napbin':
                    # self.common_mask = myarray.array.mask.copy()
                    myarray.mask_data(0)
                else:
                    myarray.nullvalue = 99999.
                    if self.common_mask is not None:
                        myarray.array.mask[:,:] = self.common_mask[:,:]
                    else:
                        myarray.mask_reset()

        elif Path(self.filenamegen + which).exists():
                myarray = WolfArray(fname = self.filenamegen + which, whichtype=wolftype)

                if which == '.napbin':
                    # self.common_mask = myarray.array.mask.copy()
                    myarray.mask_data(0)
                else:
                    myarray.nullvalue = 99999.
                    if self.common_mask is not None:
                        myarray.array.mask[:,:] = self.common_mask[:,:]
                    else:
                        myarray.mask_reset()

        else:
            logging.warning(f"File {self.filenamegen + which} does not exist")
            myarray = None

        return myarray

    def read_MB_array(self, which:Literal['.hbinb',
                                          '.qxbinb',
                                          '.qybinb',
                                          '.frotini',
                                          '.topini',
                                          '.epsbinb',
                                          '.kbinb',
                                          ]='') -> WolfArrayMB:
        """
        Lecture d'une matrice MB

        :param which: suffixe du fichier
        :type which: str -- extension with point (e.g. '.hbinb')
        :return: WolfArrayMB
        """

        which = str(which)
        if not which.startswith('.'):
            which = '.' + which

        if Path(self.filenamegen + which).exists():
            myarray = WolfArrayMB()
            myarray.set_header(self.get_header_MB())
            myarray.filename = self.filenamegen+which
            myarray.read_data()

            for curblock, curmask in zip(myarray.myblocks.values(), self.common_mask_MB):
                curblock.array.mask = curmask.copy()
        else:
            logging.warning(f"File {self.filenamegen + which} does not exist")
            myarray = None

        return myarray

    def help_files(self) -> str:
        """
        Informations sur les fichiers et les types de données qu'ils contiennent.
        """

        ret=  _('Text files\n')
        ret+=  ('----------\n')

        for key, val in self.files_others['Characteristics']:
            ret += f"{val} : {key}\n"

        ret +='\n\n'

        ret += _('Fine array - monoblock\n')
        ret +=  ('----------------------\n')

        for key, val, dtype in self.files_fine_array['Characteristics']:

            if dtype == WOLF_ARRAY_FULL_LOGICAL:
                ret += f"{val} : {key} [int16]\n"
            elif dtype == WOLF_ARRAY_FULL_INTEGER:
                ret += f"{val} : {key} [int32]\n"
            elif dtype == WOLF_ARRAY_FULL_SINGLE:
                ret += f"{val} : {key} [float32]\n"
            else:
                ret += f"{val} : {key} error - check code\n"

        ret +='\n\n'

        ret += _('Multiblock arrays\n')
        ret +=  ('-----------------\n')

        for key, val, dtype in self.files_MB_array['Initial Conditions']:

            if dtype == WOLF_ARRAY_MB_INTEGER:
                ret += f"{val} : {key} [int32]\n"
            elif dtype == WOLF_ARRAY_MB_SINGLE:
                ret += f"{val} : {key} [float32]\n"
            else:
                ret += f"{val} : {key} error - check code\n"

        return ret

    def check_infiltration(self) -> str:
        """
        Informations sur les zones d'infiltration :
          - nombre de zones dans le fichier .inf et .fil
          - nombre de cellules de chaque zone
          - première maille de chaque zone
          - nombre de temps énumérés dans le fichier .fil
          - Warning si le nombre de zones est différent entre les fichiers .inf et .fil

        """

        ret =  _('inside .inf binary file') + '\n'
        ret +=  ('-----------------------') + '\n'

        inf = self.read_fine_array('.inf')

        maxinf = inf.array.data.max()
        ret += _('Maximum infiltration zone : ') + str(maxinf) + '\n'
        for i in range(1,maxinf+1):

            nb = np.sum(inf.array.data == i)
            if nb>0:
                indices = np.where(inf.array.data == i)
                ret += f"Zone {i} : {nb} cells -- Indices (i,j) of the zone's first cell ({indices[0][0]+1} ; {indices[1][0]+1}) (1-based)\n"
            else:
                ret += f"Zone {i} : 0 cells\n"

        ret += '\n'

        ret += _('inside .fil text file') + '\n'
        ret +=  ('----------------------') + '\n'

        ret += f"Zones : {self.infiltration.nb_zones}" + '\n'
        ret += f"Time steps : {self.infiltration.nb_steps}" + '\n'

        if maxinf != self.infiltration.nb_zones:
            ret += _('Warning : number of zones in .inf and .fil files are different') + '\n'

        return ret


    def copy2gpu(self, dirout:str='') -> str:
        """
        Copie des matrices d'une simulation CPU pour le code GPU

        :param dirout: répertoire de sortie
        :type dirout: str
        """

        def to_absolute(array:WolfArray):
            array.origx += array.translx
            array.origy += array.transly
            array.translx = 0.
            array.transly = 0.

        ret = ''

        dirout = Path(dirout)
        makedirs(dirout, exist_ok=True)

        inf = self.read_fine_array('.inf')
        to_absolute(inf)
        inf.write_all(dirout / 'infiltration_zones.npy')
        del(inf)

        ret += '.inf --> infiltration_zones.npy [np.int32]\n'

        frot = self.read_fine_array('.frot')
        to_absolute(frot)
        frot.write_all(dirout / 'manning.npy')
        del(frot)

        ret += '.frot --> manning.npy [np.float32]\n'

        hbin = self.read_fine_array('.hbin')
        to_absolute(hbin)
        hbin.write_all(dirout / 'h.npy')
        del(hbin)

        ret += '.hbin --> h.npy [np.float32]\n'

        qxbin = self.read_fine_array('.qxbin')
        to_absolute(qxbin)
        qxbin.write_all(dirout / 'qx.npy')
        del(qxbin)

        ret += '.qxbin --> qx.npy [np.float32]\n'

        qybin = self.read_fine_array('.qybin')
        to_absolute(qybin)
        qybin.write_all(dirout / 'qy.npy')
        del(qybin)

        ret += '.qybin --> qy.npy [np.float32]\n'

        nap = self.read_fine_array('.napbin')
        napgpu = np.zeros_like(nap.array.data, dtype = np.uint8)
        napgpu[np.where(nap.array.data != 0)] = 1
        np.save(dirout / 'nap.npy', napgpu)

        ret += '.napbin --> nap.npy [np.uint8]\n'

        top = self.read_fine_array('.top')
        to_absolute(top)
        top.array.data[np.where(napgpu != 1)] = 99999.
        top.nullvalue = 99999.
        top.write_all(dirout / 'bathymetry.npy')

        ret += '.top --> bathymetry.npy [np.float32]\n'
        ret += _('Force a value 99999. outside nap') + '\n'

        nb = np.sum(top.array.data != 99999.)
        assert  nb == np.sum(napgpu == 1), 'Error in couting active cells'

        ret += f'\n{nb} active cells in bathymetry.npy'+ '\n'

        from wolfgpu.simple_simulation import SimpleSimulation, InfiltrationInterpolation, SimulationDuration, Direction

        simplesim = SimpleSimulation(top.nbx, top.nby)

        simplesim.manning = np.load(dirout / 'manning.npy')
        simplesim.bathymetry = np.load(dirout / 'bathymetry.npy')

        if self.infiltration.nb_steps>0:
            simplesim.infiltration_zones = np.load(dirout / 'infiltration_zones.npy')
            simplesim.param_infiltration_lerp = InfiltrationInterpolation.LINEAR
            simplesim.infiltrations_chronology = self.infiltration._chronology_for_gpu

        simplesim.qx = np.load(dirout / 'qx.npy')
        simplesim.qy = np.load(dirout / 'qy.npy')
        simplesim.nap = np.load(dirout / 'nap.npy')
        simplesim.h = np.load(dirout / 'h.npy')

        simplesim.param_froude_max = self.parameters.blocks[0]._froude_max
        simplesim.param_base_coord_ll_x = top.origx
        simplesim.param_base_coord_ll_y = top.origy
        simplesim.param_dx = top.dx
        simplesim.param_dy = top.dy
        simplesim.param_courant = self.parameters._scheme_cfl
        simplesim.param_duration = SimulationDuration.from_seconds(self.parameters._timestep_duration)
        simplesim.param_report_period = SimulationDuration.from_steps(self.parameters._writing_frequency)
        simplesim.param_runge_kutta = .5


        for cur in self.parameters.weak_bc_x.mybc:

            simplesim.add_boundary_condition(cur.i, cur.j, cur.ntype, cur.val, Direction.LEFT)

        for cur in self.parameters.weak_bc_y.mybc:

            simplesim.add_boundary_condition(cur.i, cur.j, cur.ntype, cur.val, Direction.BOTTOM)

        retgpu = simplesim.check_errors()

        if retgpu is None:
            ret += _('All files copied successfully')

            simplesim.save(Path(dirout))

        return ret


    def copy_parameters(self, other:"prev_sim2D"):
        """
        Copie des paramètres d'une simulation à une autre

        :param other: autre simulation
        :type other: prev_sim2D
        """

        if self.nb_blocks != other.nb_blocks:
            logging.error('Number of blocks are different')
            return

        active = other.parameters._get_general_params()
        self.parameters._set_general_params(active)

        dbg = other.parameters._get_debug_params()
        self.parameters._set_debug_params(dbg)

        for i in range(other.nb_blocks):
            active = other.parameters.blocks[i]._get_general_params()
            self.parameters.blocks[i]._set_general_params(active)

            dbg = other.parameters.blocks[i]._get_debug_params()
            self.parameters.blocks[i]._set_debug_params(dbg)

    def is_like(self, other:"prev_sim2D") -> tuple[bool, str]:
        """
        Vérification de la similarité de deux simulations

        :param other: autre simulation
        :type other: prev_sim2D
        :return: True si les simulations sont similaires
        """

        log, ret = self.bloc_description.is_like(other.bloc_description)

        if not self.get_header().is_like(other.get_header()):
            ret += _('Fine mesh header is different') + '\n'
            log = False

        if not self.get_header_MB().is_like(other.get_header_MB()):
            ret += _('Multi-block header is different') + '\n'
            log = False

        self.sux_suy.read_file()
        other.sux_suy.read_file()

        log2, ret2 = self.sux_suy.is_like(other.sux_suy)

        log = log and log2
        ret += ret2

        active1 = self.parameters._get_general_params()
        active2 = other.parameters._get_general_params()

        if active1 != active2:
            log = False
            ret += _('General parameters are different') + '\n'

        dbg1 = self.parameters._get_debug_params()
        dbg2 = other.parameters._get_debug_params()

        if dbg1 != dbg2:
            log = False
            ret += _('Debug parameters are different') + '\n'

        if self.parameters.weak_bc_x.nb_bc != other.parameters.weak_bc_x.nb_bc:
            log = False
            ret += _('Number of weak BC along X are different') + '\n'

        if self.parameters.weak_bc_y.nb_bc != other.parameters.weak_bc_y.nb_bc:
            log = False
            ret += _('Number of weak BC along Y are different') + '\n'

        if self.parameters.strong_bc.nb_bc != other.parameters.strong_bc.nb_bc:
            log = False
            ret += _('Number of strong BC are different') + '\n'

        if self.nb_blocks != other.nb_blocks:
            ret += _('Number of blocks are different -- Can not compare block parameters') + '\n'
            log = False
        else:
            for i in range(self.nb_blocks):
                active1 = self.parameters.blocks[i]._get_general_params()
                active2 = other.parameters.blocks[i]._get_general_params()

                if active1 != active2:
                    log = False
                    ret += f'General parameters for block {i+1} are different\n'

                dbg1 = self.parameters.blocks[i]._get_debug_params()
                dbg2 = other.parameters.blocks[i]._get_debug_params()

                if dbg1 != dbg2:
                    log = False
                    ret += f'Debug parameters for block {i+1} are different\n'


        nap1 = self.read_fine_array('.napbin')
        nap2 = other.read_fine_array('.napbin')

        if nap1.array.data.shape != nap2.array.data.shape:
            log = False
            ret += _('Fine mesh size is different') + '\n'

        if not np.all(np.abs(nap1.array.data) == np.abs(nap2.array.data)):
            log = False
            ret += _('Fine mesh is different') + '\n'

        return log, ret

    def add_weak_bc_x(self,
                      i: int,
                      j: int,
                      ntype: BCType_2D,
                      value: float):
        """
        Ajout d'une condition limite faible sur le bord X

        Alias de myparam.add_weak_bc_x
        """

        lst = self.list_pot_bc_x()

        if len(lst) == 0:
            logging.warning('No potential BC found -- Test can not be performed -- I continue anyway')
        else:
            candidate_cells = list(zip(lst[0], lst[1]))
            if (i, j) not in candidate_cells:
                logging.error(f'Invalid indices ({i},{j}) - BC not added')
                return

        self.parameters.add_weak_bc_x(i, j, ntype, value)

    def add_weak_bc_y(self,
                      i: int,
                      j: int,
                      ntype: BCType_2D,
                      value: float):
        """
        Ajout d'une condition limite faible sur le bord Y

        Alias de myparam.add_weak_bc_y
        """

        lst = self.list_pot_bc_y()

        if len(lst) == 0:
            logging.warning('No potential BC found -- Test can not be performed -- I continue anyway')
        else:
            candidate_cells = list(zip(lst[0], lst[1]))
            if (i, j) not in candidate_cells:
                logging.error(f'Invalid indices ({i},{j}) - BC not added')
                return

        self.parameters.add_weak_bc_y(i, j, ntype, value)

    def remove_weak_bc_x(self, i:int, j:int):
        """
        Suppression d'une condition limite faible sur le bord X

        Alias de myparam.weak_bc_x.remove
        """

        self.parameters.weak_bc_x.remove(i, j)

    def remove_weak_bc_y(self, i:int, j:int):
        """
        Suppression d'une condition limite faible sur le bord Y

        Alias de myparam.weak_bc_y.remove
        """

        self.parameters.weak_bc_y.remove(i, j)

    def change_weak_bc_x(self, i:int, j:int, ntype:BCType_2D, value:float):
        """
        Modification d'une condition limite faible sur le bord X

        Alias de myparam.weak_bc_x.change
        """

        self.parameters.weak_bc_x.change(i, j, ntype, value)

    def change_weak_bc_y(self, i:int, j:int, ntype:BCType_2D, value:float):
        """
        Modification d'une condition limite faible sur le bord Y

        Alias de myparam.weak_bc_y.change
        """

        self.parameters.weak_bc_y.change(i, j, ntype, value)

    def exists_weak_bc_x(self, i:int, j:int) -> bool:
        """
        Vérification de l'existence d'une condition limite faible sur le bord X

        Alias de myparam.weak_bc_x.exists
        """

        return self.parameters.weak_bc_x.exists(i, j)

    def exists_weak_bc_y(self, i:int, j:int) -> bool:
        """
        Vérification de l'existence d'une condition limite faible sur le bord Y

        Alias de myparam.weak_bc_y.exists
        """

        return self.parameters.weak_bc_y.exists(i, j)

    @property
    def nb_weak_bc_x(self) -> int:
        """
        Nombre de conditions limites faibles sur le bord X

        Alias de myparam.weak_bc_x.nb_bc
        """

        return self.parameters.weak_bc_x.nb_bc

    @property
    def nb_weak_bc_y(self) -> int:
        """
        Nombre de conditions limites faibles sur le bord Y

        Alias de myparam.weak_bc_y.nb_bc
        """

        return self.parameters.weak_bc_y.nb_bc

    def list_bc_x(self) -> list[boundary_condition_2D]:
        """
        Liste des conditions limites existantes sur les bords X

        """

        return self.parameters.weak_bc_x.list_bc()

    def list_bc_y(self) -> list[boundary_condition_2D]:
        """
        Liste des conditions limites existantes sur les bords X

        """

        return self.parameters.weak_bc_x.list_bc()

    def list_bc_x_ij(self) -> tuple[list[int], list[int]]:
        """
        Liste des conditions limites existantes sur les bords X

        """

        return self.parameters.weak_bc_x.list_bc_ij()

    def list_bc_y_ij(self) -> tuple[list[int], list[int]]:
        """
        Liste des conditions limites existantes sur les bords X

        """

        return self.parameters.weak_bc_x.list_bc_ij()

    def list_bc_ij(self) -> tuple[tuple[list[int], list[int]], tuple[list[int], list[int]]]:
        """
        Liste des conditions limites existantes sur les bords X et Y

        :return: tuple avec les indices des conditions limites [entiers 32 bits]

        """

        return self.list_bc_x_ij(), self.list_bc_y_ij()

    def list_bc(self) -> tuple[list[boundary_condition_2D], list[boundary_condition_2D]]:
        """
        Liste des conditions limites existantes sur les bords X et Y

        :return: tuple avec instances "boundary_condition_2D"

        """

        return self.list_bc_x(), self.list_bc_y()

    def get_bc_x(self, i:int, j:int) -> list[boundary_condition_2D]:
        """
        Renvoi d'une condition limite faible sur le bord X

        Alias de myparam.weak_bc_x.get_bc
        """

        return self.parameters.weak_bc_x.get_bc(i, j)

    def get_bc_y(self, i:int, j:int) -> list[boundary_condition_2D]:
        """
        Renvoi d'une condition limite faible sur le bord Y

        Alias de myparam.weak_bc_y.get_bc
        """

        return self.parameters.weak_bc_y.get_bc(i, j)

    def list_pot_bc_x(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Liste des conditions limites potentielles sur le bord X

        :return i,j: indices des conditions limites potentielles [entiers 32 bits]
        """

        ij = self.sux_suy.list_pot_bc_x()

        i = np.asarray([cur[0] for cur in ij], dtype=np.int32)
        j = np.asarray([cur[1] for cur in ij], dtype=np.int32)

        return i,j

    def list_pot_bc_y(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Liste des conditions limites potentielles sur le bord X

        :return i,j: indices des conditions limites potentielles [entiers 32 bits]
        """

        ij = self.sux_suy.list_pot_bc_y()

        i = np.asarray([cur[0] for cur in ij], dtype=np.int32)
        j = np.asarray([cur[1] for cur in ij], dtype=np.int32)

        return i,j

    def get_borders_x(self):
        """ Compute segments coordinates for borders along X """

        head = self.get_header()

        lst = self.list_pot_bc_x()

        # removing 1 to get 0-based indices
        ij = np.vstack([lst[0]-1, lst[1]-1]).T

        x, y = head.convert_ij2xy_np(ij)

        x -= head.dx / 2.
        y1 = y - head.dy / 2.
        y2 = y + head.dy / 2.

        return [x, x], [y1, y2]

    def get_borders_y(self):
        """ Compute segments coordinates for borders along Y """

        head = self.get_header()

        lst = self.list_pot_bc_y()

        # removing 1 to get 0-based indices
        ij = np.vstack([lst[0]-1 , lst[1]-1]).T

        x, y = head.convert_ij2xy_np(ij)

        y -= head.dy / 2.
        x1 = x - head.dx / 2.
        x2 = x + head.dx / 2.

        return [x1, x2], [y, y]

    def plot_borders(self, xy_or_ij:Literal['xy', 'ij'] ='xy', figax:tuple[plt.Figure, plt.Axes]=None, xcolor:str='b', ycolor:str='r'):
        """ Plot the borders """

        assert xy_or_ij in ['xy', 'ij'], 'Invalid argument'

        if figax is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figax

        if xy_or_ij == 'ij':

            x, y = self.list_pot_bc_x()
            for i in range(len(x)):
                locx = [x[i]-.5, x[i]-.5]
                locy = [y[i]-.5, y[i]+.5]
                ax.plot(locx, locy, xcolor)

            x, y = self.list_pot_bc_y()
            for i in range(len(x)):
                locx = [x[i]-.5, x[i]+.5]
                locy = [y[i]-.5, y[i]-.5]
                ax.plot(locx, locy, ycolor)

                ax.set_xlabel('i (1-based)')
                ax.set_ylabel('j (1-based)')

        else:

            x, y = self.get_borders_x()
            for i in range(len(x[0])):
                locx = [x[0][i], x[1][i]]
                locy = [y[0][i], y[1][i]]
                ax.plot(locx, locy, xcolor)

            x, y = self.get_borders_y()
            for i in range(len(x[0])):
                locx = [x[0][i], x[1][i]]
                locy = [y[0][i], y[1][i]]
                ax.plot(locx, locy, ycolor)

                ax.set_xlabel('X [m]')
                ax.set_ylabel('Y [m]')

        ax.set_aspect('equal')

        return fig, ax

    def help_bc_type(self):
        """ Aide sur les types de conditions limites """

        ret = _('Types of boundary conditions') + '\n'
        ret += ('---------------------------') + '\n'

        for cur in BCType_2D:
            key = cur.name
            val = cur.value
            ret += f"Key : {key} - Associacted value : {val[0]} - {val[1]}\n"

        return ret

    def _sanitize_group(self, group:str):
        """ Sanitize group name """

        groups = self.get_parameters_groups()

        groups_low = [cur.lower() for cur in groups]

        if group.lower() in groups_low:

            return groups[groups_low.index(group.lower())]

        else:

            return None

    def _sanitize_parameter(self, name:str):
        """ Sanitize parameter name """

        all = self.get_parameters_groups_and_names()

        all_low = [cur[1].lower() for cur in all]

        if name.lower() in all_low:

            return all[all_low.index(name.lower())][1]

        else:

            return None

    def sanitize_group_name(self, group:str, name:str):

        sanit_group, sanit_name = self._sanitize_group(group), self._sanitize_parameter(name)

        if sanit_group is None or sanit_name is None:
            logging.error(f'Group {group} or parameter {name} not found')

        return sanit_group, sanit_name


    def get_frequent_parameters(self) -> tuple[list[tuple[str,str]], list[tuple[str,str]], tuple[list[int], list[int], list[int], list[int]]]:
        """
        Renvoi des paramètres de simulation fréquents

        Les valeurs retournées sont :
            - les groupes et noms des paramètres globaux
            - les groupes et noms des paramètres de blocs
            - les indices des paramètres globaux (generaux et debug) et de blocs (generaux et debug)

        """

        return self.parameters.frequent_params()

    def check_all(self, verbosity = 0) -> str:
        """
        Vérification de la cohérence des paramètres de simulation.

        Si les tests ne passent pas, un log d'erreur est généré.

        :param verbosity: 0 = errors only, 1 = errors and warnings, 2 = everything, 3 = everything + group names
        :return: message de log
        :rtype: str

        """

        valid, ret = self.parameters.check_all(verbosity)

        if valid:
            logging.info('All parameters are valid !')
            if verbosity > 0:
                return ret
            else:
                return 0
        else:
            logging.error('Some parameters are not valid !')
            return ret


    def help_parameter(self, group:str, name:str):
        """ Aide sur les paramètres de simulation """

        sanit_group, sanit_name = self.sanitize_group_name(group, name)

        if sanit_group is None or sanit_name is None:
            return ['-', '-', '-']

        return self.parameters.get_help(sanit_group, sanit_name)


    def help_values_parameter(self, group:str, name:str):
        """ Aide sur les valeurs possibles des paramètres de simulation """

        sanit_group, sanit_name = self.sanitize_group_name(group, name)

        if sanit_group is None or sanit_name is None:
            return {}

        return self.parameters.get_json_values(sanit_group, sanit_name)

    def help_useful_fct(self) -> tuple[str, dict[str:dict[str, list[str]]]]:
        """
        Useful functions/routines for parameters manipulation

        :return (ret, dict) : ret is a string with the description of the function, dict is a dictionary with the function names sorted by category (Global, Block) and type (set, get, reset, check)

        """

        ret = _('Useful functions can be found to set, get, reset and check parameters.') + '\n\n'
        ret+= _('Here is a list of implemented functions :') + '\n\n'

        ret += 'Setter in global parameters\n'
        ret += '***************************\n\n'

        fcts = {}

        dict_global = fcts['Global']= {}
        dict_block  = fcts['Block'] = {}

        for curdict in [dict_global, dict_block]:
            curdict['set'] = []
            curdict['get'] = []
            curdict['reset'] = []
            curdict['check'] = []

        for name, value in prev_parameters_simul().__class__.__dict__.items():
            if name.startswith('set_params') and callable(value):
                ret += f'    {name}\n'
                dict_global['set'].append(name)

        ret += '\n'
        ret += 'Getter in global parameters\n'
        ret += '***************************\n\n'

        for name, value in prev_parameters_simul().__class__.__dict__.items():
            if name.startswith('get_params') and callable(value):
                ret += f'    {name}\n'
                dict_global['get'].append(name)

        ret += '\n'
        ret += 'Setter in block parameters\n'
        ret += '**************************\n\n'

        for name, value in prev_parameters_blocks().__class__.__dict__.items():
            if name.startswith('set_params') and callable(value):
                ret += f'    {name}\n'
                dict_block['set'].append(name)

        ret += '\n'
        ret += 'Getter in block parameters\n\n'
        ret += '**************************\n\n'

        for name, value in prev_parameters_blocks().__class__.__dict__.items():
            if name.startswith('get_params') and callable(value):
                ret += f'    {name}\n'
                dict_block['get'].append(name)

        ret += '\n'
        ret += 'Resetter in global parameters\n\n'
        ret += '*****************************\n\n'

        for name, value in prev_parameters_simul().__class__.__dict__.items():
            if name.startswith('reset_params') and callable(value):
                ret += f'    {name}\n'
                dict_global['reset'].append(name)

        ret += '\n'
        ret += 'Resetter in block parameters\n\n'
        ret += '****************************\n\n'

        for name, value in prev_parameters_blocks().__class__.__dict__.items():
            if name.startswith('reset_params') and callable(value):
                ret += f'    {name}\n'
                dict_block['reset'].append(name)

        ret += '\n'
        ret += 'Checker in global parameters\n\n'
        ret += '****************************\n\n'

        for name, value in prev_parameters_simul().__class__.__dict__.items():
            if name.startswith('check_params') and callable(value):
                ret += f'    {name}\n'
                dict_global['check'].append(name)

        ret += '\n'
        ret += 'Checker in block parameters\n\n'
        ret += '***************************\n\n'

        for name, value in prev_parameters_blocks().__class__.__dict__.items():
            if name.startswith('check_params') and callable(value):
                ret += f'    {name}\n'
                dict_block['check'].append(name)

        return ret, fcts

    def __iter__(self) -> prev_parameters_blocks:
        """ Iteration over the parameters blocks """

        return iter(self.parameters.blocks)

    def __next__(self) -> prev_parameters_blocks:
        """ Next block """

        return next(self.parameters.blocks)

    def __getitem__(self, key:int):
        """ Get block by index (1-bsed) """

        assert isinstance(key, int), 'Invalid index type -- Must be integer'

        assert key >= 0 and key <= self.nb_blocks, 'Invalid index -- The index must be between 1 and the number of blocks {}'.format(self.nb_blocks)

        if key == 0:
            logging.debug('Returning global parameters')
            return self.parameters
        else:
            logging.debug(f'Returning block {key}')
            return self.parameters.blocks[key-1]

    def _from_params_gpu(self, imported_params: prev_parameters_simul = None):

        """ This is a __init__ helper. This will be used in the constructor
        to create a mono-block model from scratch (i.e. not reading from disk;
        providing base matrices).

        :param myparam: The parameters to build the model with.

        """

        from os.path import exists, join, isdir, isfile, dirname, normpath, splitext
        import numpy.ma as ma

        if imported_params.nblocks == 0:
            # Il faut au moins un bloc
            imported_params.blocks.append(prev_parameters_blocks())

        # Rather then pointing to the same object, we want to copy the parameters
        self.parameters._set_general_params(imported_params._get_general_params())
        self.parameters._set_debug_params(imported_params._get_debug_params())

        # Create a polygon for the external border
        external_border = block_contour(is2D=True, name='external border')  ##< vecteur du contour externe

        external_border.add_vertex(wolfvertex(self.dx, self.dy))
        external_border.add_vertex(wolfvertex(self.dx * float(self.nbx-1), self.dy))
        external_border.add_vertex(wolfvertex(self.dx * float(self.nbx-1), self.dy * float(self.nby-1)))
        external_border.add_vertex(wolfvertex(self.dx, self.dy * float(self.nby-1)))
        external_border.close_force()

        # Add the external border to the general contour zone
        general = self.bloc_description.general_contour_zone
        general.add_vector(external_border)

        self.add_block(external_border, dx = self.dx, dy = self.dy)

        # Header useful to set the arrays
        header = self.get_header()

        self.create_napbin()
        self.create_fine_arrays()

    def set_gpu_test(self,
                     dt:float = None,
                     n_timesteps:int = None,
                     writing_frequency:Union[int,float] = None,
                     reset_bc:bool = False,
                     optimize_dt:bool = None,
                     Runge_Kutta_pond:float = None,
                     Courant_number:float = None,
                     max_Froude:float = None,
                     writing_mode:Literal['seconds', 'timesteps', 0, 1] = None,
                     ):

        """ Usual settings for a GPU test """

        if n_timesteps is not None:
            assert isinstance(n_timesteps, int), 'Invalid number of timesteps'
            self.parameters._nb_timesteps = n_timesteps

        if writing_frequency is not None:
            assert isinstance(writing_frequency, (int, float)), 'Invalid writing frequency'
            self.parameters._writing_frequency = writing_frequency

        if reset_bc:
            self.parameters.reset_all_boundary_conditions()

        if dt is not None:
            assert isinstance(dt, float), 'Invalid timestep'
            self.parameters._timestep_duration = dt

        if optimize_dt is not None:
            assert isinstance(optimize_dt, bool), 'Invalid optimize_dt'
            self.parameters._scheme_optimize_timestep = 1 if optimize_dt else 0

        if Runge_Kutta_pond is not None:
            assert isinstance(Runge_Kutta_pond, float), 'Invalid Runge_Kutta_pond'
            self.parameters._scheme_rk = Runge_Kutta_pond

        if Courant_number is not None:
            assert isinstance(Courant_number, float), 'Invalid Courant_number'
            self.parameters._scheme_cfl = Courant_number

        if max_Froude is not None:
            assert isinstance(max_Froude, float), 'Invalid max_Froude'
            self[1]._froude_max = max_Froude

        if writing_mode is not None:
            assert writing_mode in ['seconds', 'timesteps', 0, 1], 'Invalid writing mode'
            self.parameters._writing_mode = 1 if writing_mode in ['seconds', 1] else 0

    def reset_all_boundary_conditions(self):
        """ Reset all boundary conditions """

        self.parameters.reset_all_boundary_conditions()
        logging.info(_('All boundary conditions have been reset'))

    def add_boundary_condition(self, i: int, j: int, bc_type:BCType_2D,  bc_value: float, border:Direction):
        """ Add a *weak* boundary condition to the model.

        :param i: i-position of the boundary condition (1-based)
        :param j: j-position of the boundary condition (1-based)
        :param bc_type: type of boundary condition
        :param bc_value: value/parameter of the boundary condition
        :param border: mesh's border on which the boundary condtion applies

        """

        assert bc_type in BCType_2D, 'Invalid boundary condition type'

        if border in [Direction.X, Direction.LEFT]:

            self.add_weak_bc_x(i, j, bc_type, bc_value)

        elif border in [Direction.Y, Direction.BOTTOM]:

            self.add_weak_bc_y(i, j, bc_type, bc_value)

        else:
            logging.error('Invalid Direction - {}'.format(border))

    def setup_oneblock(self,
                       contour:Union[vector, WolfArray, tuple, dict, header_wolf],
                       block_spatial_stepsize: float,
                       friction_coefficient:float = 0.04,
                       translate_contour:bool = True,):
        """
        Setup a single block model

        :param contour: contour of the model
        :type contour: Union[vector, WolfArray, tuple, dict, header_wolf]
        :param dx: spatial step [m]
        :type block_spatial_stepsize: float
        :param frot: friction coefficient
        :type frot: float
        :param translate_contour: translate the contour to have the first point at (0, 0)
        :type translate_contour: bool

        """

        # Grille magnétique - dx et dy sont les pas de la grille [m], origx et origy sont les coordonnées du premier point de la grille.
        self.set_magnetic_grid(dx=block_spatial_stepsize, dy=block_spatial_stepsize, origx=0., origy=0.)

        # Transfert de l'information de contour externe
        if isinstance(contour, vector):

            self.set_external_border_vector(contour)

        elif isinstance(contour, WolfArray):

            self.set_external_border_wolfarray(contour, mode='contour', abs = True)

        elif isinstance(contour, header_wolf):

            self.set_external_border_header(contour)

        elif isinstance(contour, tuple):

            if len(contour) == 6:
                ox,oy,nbx,nby,block_spatial_stepsize,dy = contour
                self.set_external_border_nxny(ox,oy,nbx,nby,block_spatial_stepsize,dy)
            else:
                logging.error('Invalid tuple - Must contains (ox,oy,nbx,nby,dx,dy), no more, no less')

        elif isinstance(contour, dict):

            keys = ['ox', 'oy', 'nbx', 'nby', 'dx', 'dy']
            if all([cur in contour for cur in keys]):

                ox,oy,nbx,nby,block_spatial_stepsize,dy = [contour[cur] for cur in keys]
                self.set_external_border_nxny(ox,oy,nbx,nby,block_spatial_stepsize,dy)

            else:

                logging.error('Invalid dictionary - Must at least contains (ox,oy,nbx,nby,dx,dy) as keys, no less')

        # Par défaut, les coordonnées du polygone seront translatées pour le que point (xmin, ymin) soit en (0, 0).
        self.translate_origin2zero = translate_contour

        # Choix du pas spatial de maillage fin [m].
        self.set_mesh_fine_size(dx=block_spatial_stepsize, dy=block_spatial_stepsize)

        # Ajout d'un bloc avec son pas spatial spécifique [m].
        self.add_block(self.external_border, dx=block_spatial_stepsize, dy=block_spatial_stepsize)

        # Maillage du problème
        if self.mesh():
            ret = 'Meshing done !'
        else:
            ret = 'Meshing failed !'
            return 1, ret

        # Si "with_tubulence" est True, les fichiers ".kbin" et ".epsbin" seront créés en plus et contiendront l'énergie cinétique turbulente.
        self.create_fine_arrays(default_frot=friction_coefficient, with_tubulence=False)

        # Recherches des bords conditions aux limites potentiels sur base de la matrice ".napbin" et écriture des fichiers ".sux" et ".suy"
        self.create_sux_suy()

        return 0, ret

    def get_wizard_text(self, lang:str = 'en') -> str:
        """ Get the wizard text """

        wizard_steps_page1 =[
            '',
            '',
            '',
            _('Welcome to the wizard'),
            '',
            '',
            '',
            _('This wizard will guide you through the creation\nof a new multiblock WOLF2D model'),
            '',
        ]

        wizard_steps_page2 = [
            _('First of all, you need to define a polygon as external border'),
            '',
            _('You can create a new polygon or select an existing one'),
            '',
            _('You can also create a polygon from a footprint by defining : \n   - the origin (ox, oy)\n   - the resolution (dx, dy)\n   - the number of nodes along X and Y (nbx, nby)'),
            '',
            _('Or you can use a mask from the active array  (e.g. a topography array)'),
        ]


        wizard_steps_page3 = [
            _('Then you can set the magnetic grid'),
            '',
            _('The magnetic grid is a virtual grid on which the array bounds (data and blocks) are aligned'),
            '',
            _('It is useful to have consistent boundaries between different simulations\n(e.g. successive river reaches)'),
        ]


        wizard_steps_page4 = [
            _('Then you can set the fine resolution of the model'),
            '',
            _('The fine resolution is the spatial resolution of the main data arrays\n(topography, friction, etc.)'),
            '',
            _('If you set the external border from the active array, the fine resolution\nis preset to the resolution of the array'),
            '',
            _('You can change the fine resolution if needed'),
            '',
            _('Bounds of these arrays will be computed according to the magnetic grid\nand the maximum resolution of the blocks (see next page)'),
        ]

        wizard_steps_page5 = [
            _('Then you can add blocks to the model (see + button)'),
            '',
            _('Blocks are the main structure of the model'),
            '',
            _('They are defined by a polygon and a spatial resolution'),
            '',
            _('The polygon can overlap with other blocks - Last block will have the\npriority in the meshing process'),
            '',
            _('You can add as many blocks as you want'),
            '',
            _('You can set the resolution of each block (dx, dy) but the resolutions\nmust be a multiple of the fine resolution'),
            '',
            _('At each limit between two blocks, the resolution must be a multiple of\nthe finer resolution of the two blocks'),
            '',
            _('Final size of the blocks is a result of the meshing process (see next page)'),
        ]

        wizard_steps_page6 = [
            _('Then you can mesh the model'),
            '',
            _('Meshing is the process of creating the mesh of the model'),
            '',
            _('The mesh is the grid of nodes and elements on which the model will be solved'),
            '',
            _('Resulting mesh is stored in the .MNAP file'),
            '',
            _('It contains the fine mesh and the mesh of each block including relations\nbetween blocks at the limits'),
        ]

        wizard_steps_page7 = [
            _('Then you can create the fine arrays or should I say\nthe code will do it for you'),
            '',
            _('Fine arrays are the main data arrays of the model'),
            '',
            _('They are created from the meshing results'),
            '',
            _('They are stored in the binazy files\nExtensions .TOP, .FROT, .HBIN, .QXBIN, .QYBIN'),
            '',
            _('Arrays can be edited in the GUI'),
        ]

        wizard_steps_page8 = [
            _('Set the boundary conditions'),
            '',
            _('You can set the boundary conditions for the model'),
            '',
        ]

        wizard_steps_page9 = [
            _('Set the parameters'),
            '',
            _('You can set the parameters for the model (Global parameters)'),
            '',
            _('You can set parameters for each block (Block parameters)'),
            '',
        ]

        wizard_steps_page10 = [
            _('Run the code'),
            '',
        ]

        wizard_steps_page11 = [
            _('Check the results'),
        ]

        wizard_steps_page12 = [
            _('That\'s all folks !'),
        ]

        return [wizard_steps_page1, wizard_steps_page2, wizard_steps_page3, wizard_steps_page4, wizard_steps_page5, wizard_steps_page6, wizard_steps_page7, wizard_steps_page8, wizard_steps_page9, wizard_steps_page10, wizard_steps_page11, wizard_steps_page12]

    def bc2txt(self) -> str:
        """" Get the text for the boundary conditions Manager """

        txt = str(self.nb_weak_bc_x + self.nb_weak_bc_y) +"\n"

        txt += self.parameters.weak_bc_x.bc2text()
        txt += self.parameters.weak_bc_y.bc2text()

        return txt

    def mimic_mask(self, source:WolfArray):
        """ Copy the mask of the source array to all arrays in the model. """

        logging.info(_('Copying mask to all arrays'))
        self.common_mask = source.array.mask.copy()

        for curarray in self.fine_arrays:
            if curarray is not None:
                if curarray is not source:
                    curarray.copy_mask_log(self.common_mask, link=False)

        logging.info(_('Updating mask array and .nap file'))
        self.napbin.array.data[np.where(np.logical_not(self.common_mask))] = 1
        self.napbin.write_all()
