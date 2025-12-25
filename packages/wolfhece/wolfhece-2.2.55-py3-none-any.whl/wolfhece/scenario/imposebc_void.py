"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import inspect
import ast
import importlib.util
from pathlib import Path
import tempfile
import logging

try:
    from wolfhece.wolf_array import WolfArray
    from wolfhece.PyVertexvectors import Zones, zone, vector, wolfvertex
except:
    logging.error('WOLF not installed !')

try:
    from wolfgpu.simple_simulation import SimpleSimulation, BoundaryConditionsTypes, Direction
except:
    logging.error('WOLFGPU not installed !')

class Impose_Boundary_Conditions:
    """
    Impose_Boundary_Conditions
    """

    def impose_bc(self, simul:"SimpleSimulation"):
        """
        FR

        Cette fonction doit être particularisée afin d'appliquer des conditions aux limites à la simulation.
        L'instance de simulation est passée en argument et ne doit pas être créee/modifiée.

        Les conditions limites sont imposées en énumérant les cellules de la grille de calcul. La convention est "1-based" (i.e. la première cellule, en bas à gauche, est la cellule (1,1)).

        Les types de CL supportées sont dans la classe "BoundaryConditionsTypes" (voir wolfgpu/simple_simulation.py).

        Les directions de CL supportées sont dans la classe "Direction" (voir wolfgpu/simple_simulation.py).
        Il s'agit de conditions faibles -> imposées sur le bord de la cellule.
        Les directions sont soit "LEFT" ou "BOTTOM". L'énumération d'une cellule (i,j) permet donc d'imposer la condition sur le bord gauche de la cellule (i-1/2,j) et sur le bord bas de la cellule (i,j-1/2).

        EN

        This function must be specialized in order to apply boundary conditions to the simulation.
        The simulation is passed as an argument and must not be created/modified.

        Boundary conditions are imposed by enumerating the cells of the computation grid. The convention used is "1-based" (i.e., the first cell, at the bottom left, is cell (1,1)).

        The supported boundary condition types are in the "BoundaryConditionsTypes" class (see wolfgpu/simple_simulation.py).

        The supported boundary condition directions are in the "Direction" class (see wolfgpu/simple_simulation.py).
        These are weak conditions imposed on the cell's edge.
        The directions are either "LEFT" or "BOTTOM." Enumerating a cell (i, j) thus imposes the condition on the left edge of cell (i-1/2, j) and on the bottom edge of cell (i, j-1/2).

        Exemple :

        # Weak Normal Froude condition (value 0.3) on the left edge of the cell (3,997) -> (3,1002)
        for j in range(997,1003):
            simul.add_boundary_condition(i=3, j=j, bc_type=BoundaryConditionsTypes.FROUDE_NORMAL, bc_value=.3, border=Direction.LEFT)

        """
        pass

def create_empty_method(method_name, method_signature, docstring, imports):
    # Fonction utilitaire pour créer des méthodes vides avec la même signature, la documentation et les importations
    imports_str = '\n'.join(f'import {module}' for module in imports)
    args_str = ', '.join(str(param) for param in method_signature.parameters.values())

    # FIXME I don't know why, but the following line is necessary to avoid a bug in the import of the module
    # On remplace la définition complète du paramètre car la référance à la classe parente est empêche le chargement dynamique du module
    args_str = args_str.replace('wolfgpu.simple_simulation.','')
    empty_method_code = f'{imports_str}\n\tdef {method_name}({args_str}):\n\t\t"""{docstring}"""\n\t\tpass\n'
    return empty_method_code

def create_new_file(filepath:Path):
    # Récupérer le code source de la classe parente
    # classe_source = inspect.getsource(Update_Sim)

    # Récupérer les signatures, la documentation et les importations des méthodes de la classe parente
    methods_info = inspect.getmembers(Impose_Boundary_Conditions, predicate=inspect.isfunction)
    method_signatures = {name: inspect.signature(method) for name, method in methods_info}
    method_docstrings = {name: method.__doc__ for name, method in methods_info}
#    method_imports = {name: get_imports(inspect.getsource(method)) for name, method in methods_info}

    # Générer le code pour la classe dérivée avec les méthodes vides, la documentation et les importations
    derivee_code = "from wolfhece.scenario.imposebc_void import Impose_Boundary_Conditions\n"
    derivee_code += "from wolfhece.wolf_array import WolfArray\n"
    derivee_code += "from wolfgpu.simple_simulation import SimpleSimulation, BoundaryConditionsTypes, Direction\n"
    derivee_code += "from wolfhece.PyVertexvectors import Zones, zone, vector, wolfvertex\n\n"
    derivee_code += "class Impose_BC_Scenario(Impose_Boundary_Conditions):\n"

    for method_name, method_signature in method_signatures.items():
        docstring = method_docstrings.get(method_name, "Documentation manquante.")
 #       imports = method_imports.get(method_name, set())
        derivee_code += create_empty_method(method_name, method_signature, docstring, [])

    # Écrire le code généré dans un fichier Python
    with open(filepath.with_suffix('.py'), 'w', encoding='utf-8') as file:
        file.write(derivee_code.replace('\t', '    '))
