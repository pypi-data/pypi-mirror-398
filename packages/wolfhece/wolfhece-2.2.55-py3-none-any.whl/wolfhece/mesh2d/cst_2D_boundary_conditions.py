"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from enum import Enum
from typing import Union, Literal
import logging

if not '_' in __builtins__:
    import gettext
    _=gettext.gettext

"""
Please note that integer values must conform to FORTRAN Wolf modules
They can not be changed freely by the Python user/developer
"""
class Direction(Enum):
    LEFT  = 1
    BOTTOM= 2
    X     = 1
    Y     = 2

class BCType_2D_GPU(Enum):
    """ Boundary conditions for 2D simulations with wolfgpu """

    # The numbers match the numbers in Wolf's simulations parameters.
    H    = (1,_('Water level [m]'))
    QX   = (2,_('Flow rate along X [m²/s]'))
    QY   = (3,_('Flow rate along Y [m²/s]'))
    NONE = (4,_('None'))
    HMOD = (7,_('Water level [m] / impervious if entry point'))
    FROUDE_NORMAL = (8,_('Froude normal to the border [-]'))

class BCType_2D(Enum):
    """ Boundary conditions for 2D simulations """

    # The numbers match the numbers in Wolf's 2D simulations parameters.
    # The values can not be changed freely by the Python user/developer
    H    = (1,_('Water level [m]'))
    QX   = (2,_('Flow rate along X [m²/s]'))
    QY   = (3,_('Flow rate along Y [m²/s]'))
    NONE = (4,_('None'))
    QBX  = (5,_('Sediment flow rate along X [m²/s]'))
    QBY  = (6,_('Sediment flow rate along Y [m²/s]'))
    HMOD = (7,_('Water level [m] / impervious if entry point'))
    FROUDE_NORMAL = (8,_('Froude normal to the border [-]'))
    ALT1 = (9,_('to check'))
    ALT2 = (10,_('to check'))
    ALT3 = (11,_('to check'))
    DOMAINE_BAS_GAUCHE = (12,_('to check'))
    DOMAINE_DROITE_HAUT = (13,_('to check'))
    SPEED_X = (14,_('Speed along X [m/s]'))
    SPEED_Y = (15,_('Speed along Y [m/s]'))
    FROUDE_ABSOLUTE = (16,_('norm of Froude in the cell [-]'))

class BCType_2D_OO(Enum):
    """ Boundary conditions for 2D simulations with Object-Oriented approach """

    # The numbers match the numbers in Wolf's 2D simulations parameters.
    # The values can not be changed freely by the Python user/developer
    WATER_DEPTH       = (1, _('Water depth [m]'))
    WATER_LEVEL       = (2, _('Water level [m]'))
    FROUDE_NORMAL     = (4, _('Froude normal to the border [-]'))
    FREE_NONE         = (5, _('Free border'))
    CONCENTRATION     = (7, _('Concentration [-]'))
    IMPERVIOUS        = (99, _('Impervious'))
    NORMAL_DISCHARGE     = (31, _('Normal discharge [m²/s]'))
    TANGENT_DISCHARGE    = (32, _('Tangent discharge [m²/s]'))
    MOBILE_DAM_POWER_LAW = (127, _('Mobile dam with power law'))
    CLOSE_CONDUIT_QNORMAL     = (61, _('Close conduit - normal discharge [m²/s]'))
    CLOSE_CONDUIT_QTANGET     = (62, _('Close conduit - tangent discharge [m²/s]'))
    CLOSE_CONDUIT_H_FOR_SPEED = (63, _('Close conduit - h for speed [m]'))


def BCType_2D_To_BCType_2D_GPU(bc_type:BCType_2D) -> BCType_2D_GPU:

    if bc_type in [BCType_2D.H, BCType_2D.H.value[0], BCType_2D.HMOD, BCType_2D.HMOD.value[0]]:
        return BCType_2D_GPU.HMOD
    elif bc_type in [BCType_2D.QX, BCType_2D.QX.value[0]]:
        return BCType_2D_GPU.QX
    elif bc_type in [BCType_2D.QY, BCType_2D.QY.value[0]]:
        return BCType_2D_GPU.QY
    elif bc_type in [BCType_2D.NONE, BCType_2D.NONE.value[0]]:
        return BCType_2D_GPU.NONE
    elif bc_type in [BCType_2D.FROUDE_NORMAL, BCType_2D.FROUDE_NORMAL.value[0]]:
        return BCType_2D_GPU.FROUDE_NORMAL
    else:
        logging.error(f"BCType_2D_To_BCType_2D_GPU: {bc_type} not found")
        return None


def revert_bc_type(bc_type:Union[BCType_2D,BCType_2D_OO,BCType_2D_GPU], val:int):
    """
    Return the BCType corresponding to the given value

    Useful for GUI or scripts
    """

    if bc_type == BCType_2D:
        for bc in BCType_2D:
            if bc.value[0] == val:
                return bc
    elif bc_type == BCType_2D_OO:
        for bc in BCType_2D_OO:
            if bc.value[0] == val:
                return bc
    elif bc_type == BCType_2D_GPU:
        for bc in BCType_2D_GPU:
            if bc.value[0] == val:
                return bc

    return None


def choose_bc_type(version:Literal[1,2,3, 'prev', 'oo', 'gpu'] = 1):
    """
    Choose the version of the boundary conditions to use

    Useful for GUI
    """

    if version==1 or version =='prev':
        return BCType_2D
    elif version==2 or version =='oo':
        return BCType_2D_OO
    elif version==3 or version =='gpu':
        return BCType_2D_GPU

# Color associated to a number of BC per border
ColorsNb = {1 : (0.,0.,1.),
            2 : (1.,.5,0.),
            3 : (0.,1.,0.),
            4 : (1.,0.,1.),
            5 : (0.,1.,1.)}
