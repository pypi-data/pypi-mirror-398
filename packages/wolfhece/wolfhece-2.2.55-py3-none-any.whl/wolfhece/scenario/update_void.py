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

class Update_Sim:
    """
    Mise à jour par script des donnees de topographie/bathymetrie et de coefficient de frottement
    """

    def update_topobathy(self, topobahty:WolfArray):
        """
        FR

        Cette fonction doit être particularisée afin d'appliquer des modifications
        à la topographie du lit majeur ou à la bathymétrie du lit mineur.

        L'information de base se trouve dans le paramètre  'topobahty' de classe 'WolfArray'.

        La matrice Numpy, en <Float32>, (avec masque - cf np.ma ) est accessible via :
          - topobahty.array[:,:]
          - topobahty.array.mask[:,:]
          - topobahty.array.data[:,:]

        Il n'est pas permis de remplacer la matrice (création d'une nouvelle matrice et/ou pointage d'una autre matrice). Toutes les operations doivent se faire dans l'espace alloué.

        EN

        This function must be customized to apply modifications to the topography of the main bed or the bathymetry of the minor bed.

        The basic information is located in the 'topobahty' parameter ('WolfArray' class).

        The Numpy array, in <Float32>, (with a mask - see np.ma), can be accessed via:
          - topobahty.array[:,:]
          - topobahty.array.mask[:,:]
          - topobahty.array.data[:,:]

        It is not allowed to replace the array (creating a new array and/or pointing an other array). All operations must be performed within the allocated space.
        """
        pass

    def update_manning(self, manning:WolfArray):
        """
        FR

        Cette fonction doit être particularisée afin d'appliquer des modifications
        à la distribution du coefficient de Manning.

        L'information de base se trouve dans le paramètre 'manning' de classe 'WolfArray'.

        La matrice Numpy, en <Float32>, (avec masque - cf np.ma ) est accessible via :
          - manning.array[:,:]
          - manning.array.mask[:,:]
          - manning.array.data[:,:]

        Il n'est pas permis de remplacer la matrice (création d'une nouvelle matrice et/ou pointage d'una autre matrice). Toutes les operations doivent se faire dans l'espace alloué.

        EN

        This function must be customized to apply modifications to the Manning roughness parameter.

        The basic information is located in the 'manning' parameter ('WolfArray' class).

        The Numpy array, in <Float32>, (with a mask - see np.ma), can be accessed via:
          - manning.array[:,:]
          - manning.array.mask[:,:]
          - manning.array.data[:,:]

        It is not allowed to replace the array (creating a new array and/or pointing an other array). All operations must be performed within the allocated space.
        """
        pass

    def update_infiltration(self, infiltration_zones:WolfArray):
        """
        FR

        Cette fonction doit être particularisée afin d'appliquer des modifications
        à la distribution des zones d'infiltration (matrice en Int32)

        L'information de base se trouve dans le paramètre 'infiltration_zones' de classe 'WolfArray'.

        La matrice Numpy, en <Int3232>, (avec masque - cf np.ma ) est accessible via :
          - infiltration_zones.array[:,:]
          - infiltration_zones.array.mask[:,:]
          - infiltration_zones.array.data[:,:]

        Il n'est pas permis de remplacer la matrice (création d'une nouvelle matrice et/ou pointage d'una autre matrice). Toutes les operations doivent se faire dans l'espace alloué.

        EN

        This function must be customized to apply modifications to the Infiltration zones parameter.

        The basic information is located in the 'infiltration_zones' parameter ('WolfArray' class).

        The Numpy array, in <Int32>, (with a mask - see np.ma), can be accessed via:
          - infiltration_zones.array[:,:]
          - infiltration_zones.array.mask[:,:]
          - infiltration_zones.array.data[:,:]

        It is not allowed to replace the array (creating a new array and/or pointing an other array). All operations must be performed within the allocated space.
        """
        pass

    def update_roof(self, roof:WolfArray):
        """
        FR

        Cette fonction doit être particularisée afin d'appliquer des modifications
        à l'altimétrie des ponts et ponceaux (toits)'.

        L'information de base se trouve dans le paramètre  'roof' de classe 'WolfArray'.

        La matrice Numpy, en <Float32>, (avec masque - cf np.ma ) est accessible via :
          - roof.array[:,:]
          - roof.array.mask[:,:]
          - roof.array.data[:,:]

        Il n'est pas permis de remplacer la matrice (création d'une nouvelle matrice et/ou pointage d'una autre matrice). Toutes les operations doivent se faire dans l'espace alloué.

        EN

        This function must be customized to apply modifications to the roof elevation of bridges/culverts.

        The basic information is located in the 'roof' parameter ('WolfArray' class).

        The Numpy array, in <Float32>, (with a mask - see np.ma), can be accessed via:
          - roof.array[:,:]
          - roof.array.mask[:,:]
          - roof.array.data[:,:]

        It is not allowed to replace the array (creating a new array and/or pointing an other array). All operations must be performed within the allocated space.
        """
        pass

    def update_deck(self, deck:WolfArray):
        """
        FR

        Cette fonction doit être particularisée afin d'appliquer des modifications
        à l'altimétrie des ponts et ponceaux (toits)'.

        L'information de base se trouve dans le paramètre  'deck' de classe 'WolfArray'.

        La matrice Numpy, en <Float32>, (avec masque - cf np.ma ) est accessible via :
          - deck.array[:,:]
          - deck.array.mask[:,:]
          - deck.array.data[:,:]

        Il n'est pas permis de remplacer la matrice (création d'une nouvelle matrice et/ou pointage d'una autre matrice). Toutes les operations doivent se faire dans l'espace alloué.

        EN

        This function must be customized to apply modifications to the deck elevation of bridges/culverts.

        The basic information is located in the 'deck' parameter ('WolfArray' class).

        The Numpy array, in <Float32>, (with a mask - see np.ma), can be accessed via:
          - deck.array[:,:]
          - deck.array.mask[:,:]
          - deck.array.data[:,:]

        It is not allowed to replace the array (creating a new array and/or pointing an other array). All operations must be performed within the allocated space.
        """
        pass

def create_empty_method(method_name, method_signature, docstring, imports):
    # Fonction utilitaire pour créer des méthodes vides avec la même signature, la documentation et les importations
    imports_str = '\n'.join(f'import {module}' for module in imports)
    args_str = ', '.join(str(param) for param in method_signature.parameters.values())

    # FIXME I don't know why, but the following line is necessary to avoid a bug in the import of the module
    # On remplace la définition complète du paramètre car la référance à la classe parente est empêche le chargement dynamique du module
    args_str = args_str.replace('wolfhece.wolf_array.','')
    empty_method_code = f'{imports_str}\n\tdef {method_name}({args_str}):\n\t\t"""{docstring}"""\n\t\tpass\n'
    return empty_method_code

# def get_imports(source_code:str):
#     # Fonction utilitaire pour extraire les importations d'un code source
#     tree = ast.parse(source_code.strip())
#     imports = {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)}
#     return imports

def create_new_file(filepath:Path):
    # Récupérer le code source de la classe parente
    # classe_source = inspect.getsource(Update_Sim)

    # Récupérer les signatures, la documentation et les importations des méthodes de la classe parente
    methods_info = inspect.getmembers(Update_Sim, predicate=inspect.isfunction)
    method_signatures = {name: inspect.signature(method) for name, method in methods_info}
    method_docstrings = {name: method.__doc__ for name, method in methods_info}
#    method_imports = {name: get_imports(inspect.getsource(method)) for name, method in methods_info}

    # Générer le code pour la classe dérivée avec les méthodes vides, la documentation et les importations
    derivee_code = "from wolfhece.scenario.update_void import Update_Sim\n"
    derivee_code += "from wolfhece.wolf_array import WolfArray\n"
    derivee_code += "from wolfhece.PyVertexvectors import Zones, zone, vector, wolfvertex\n\n"
    derivee_code += "class Update_Sim_Scenario(Update_Sim):\n"

    for method_name, method_signature in method_signatures.items():
        docstring = method_docstrings.get(method_name, "Documentation manquante.")
 #       imports = method_imports.get(method_name, set())
        derivee_code += create_empty_method(method_name, method_signature, docstring, [])

    # Écrire le code généré dans un fichier Python
    with open(filepath.with_suffix('.py'), 'w', encoding='utf-8') as file:
        file.write(derivee_code.replace('\t', '    '))
