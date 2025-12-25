"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import inspect
import os
import glob
from pathlib import Path
from typing import Literal, Union
import importlib
import sys
import logging
import types


try:
    # from .update_void import Update_Sim
    # from .imposebc_void import Impose_Boundary_Conditions
    from ..PyTranslate import _
except:
    logging.error('wolfhece.scenario.check_scenario: relative import failed')
    # from update_void import Update_Sim
    # from imposebc_void import Impose_Boundary_Conditions

def list_all_ext(dir:Path, ext:Literal['tif', 'py']):

    # Répertoire racine à partir duquel vous souhaitez lister les fichiers d'extension 'ext'
    repertoire_racine = dir

    res={}

    # Utiliser os.walk pour parcourir récursivement le répertoire
    for repertoire, sous_repertoires, fichiers in os.walk(repertoire_racine):
        # Utiliser glob pour filtrer les fichiers .tif
        fichiers = glob.glob(os.path.join(repertoire, '*.'+ext))

        curlist = res[repertoire]=[]

        # Afficher les fichiers .tif trouvés dans le répertoire actuel
        for fichier in fichiers:
            curlist.append(fichier)

def check_file_update(fichier_py:Path):

    # Nom de la classe parente et de la classe dérivée que vous recherchez
    nom_classe_parente = 'Update_Sim'
    nom_classe_derivee = 'Update_Sim_Scenario'

    # Charger dynamiquement le module à partir du fichier .py
    try:
        sys.path.insert(0, str(fichier_py.parent.absolute()))
        module = __import__(str(fichier_py.name.replace('.py',''))) # Retirer l'extension .py
        sys.path.pop(0)
    except:
        logging.error(f'Le fichier {fichier_py} ne peut pas être importé. Prière de vérifier que l\'encodage est bien en UTF-8 ou supprimer tous les commentaires avec des accents !')
        logging.error(f'The file {fichier_py} can not be imported. Please check if the file is encoded in UTF-8 or remove any accentuated character!')
        return False

    # Récupérer la classe parente et la classe dérivée à partir du module
    classe_parente = getattr(module, nom_classe_parente, None)
    classe_derivee = getattr(module, nom_classe_derivee, None)

    # Vérifier si la classe dérivée existe et hérite de la classe parente
    if classe_derivee and inspect.isclass(classe_derivee) and issubclass(classe_derivee, classe_parente):
        #print(f'Le fichier {fichier_py} contient la classe {nom_classe_derivee} qui hérite de {nom_classe_parente}.')
        return True
    else:
        # print(f'Le fichier {fichier_py} ne contient pas la classe {nom_classe_derivee} qui hérite de {nom_classe_parente}.')
        return False

def check_file_bc(fichier_py:Path):

    # Nom de la classe parente et de la classe dérivée que vous recherchez
    nom_classe_parente = 'Impose_Boundary_Conditions'
    nom_classe_derivee = 'Impose_BC_Scenario'

    # Charger dynamiquement le module à partir du fichier .py
    try:
        sys.path.insert(0, str(fichier_py.parent.absolute()))
        module = __import__(str(fichier_py.name.replace('.py',''))) # Retirer l'extension .py
        sys.path.pop(0)
    except:
        logging.error(_(f'The file {fichier_py} can not be imported. Please check your code and if the file is encoded in UTF-8 or remove any accentuated character!'))
        return False

    # Récupérer la classe parente et la classe dérivée à partir du module
    classe_parente = getattr(module, nom_classe_parente, None)
    classe_derivee = getattr(module, nom_classe_derivee, None)

    # Vérifier si la classe dérivée existe et hérite de la classe parente
    if classe_derivee and inspect.isclass(classe_derivee) and issubclass(classe_derivee, classe_parente):
        #print(f'Le fichier {fichier_py} contient la classe {nom_classe_derivee} qui hérite de {nom_classe_parente}.')
        return True
    else:
        # print(f'Le fichier {fichier_py} ne contient pas la classe {nom_classe_derivee} qui hérite de {nom_classe_parente}.')
        return False

def import_files(module_files:Union[list[Path],list[str]]) -> list[types.ModuleType]:

    # Initialiser une liste pour stocker les modules importés
    modules = []

    # Importer les modules dynamiquement
    for py_file in module_files:
        if isinstance(py_file, str):
            py_file = Path(py_file)

        olddir = os.getcwd()
        sys.path.insert(0, str(py_file.parent.absolute()))
        os.chdir(py_file.parent)

        mod_name = py_file.name.replace('.py','')
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        module = importlib.import_module(mod_name)
        # sys.modules.get('update_top_mann_scen')
        sys.path.pop(0)
        os.chdir(olddir)

        # Test if some routines are missing
        # if "impose_bc" in py_file.name:
        #     to_test = ['impose_bc']

        # elif "update_void" in py_file.name:
        #     to_test = ['update_topobathy', 'update_manning', 'update_infiltration', 'update_roof']

        # for routine in to_test:
        #     if not hasattr(module, routine):
        #         logging.warning(f'Le module {module} ne contient pas la routine {routine}.')

        modules.append(module)

    return modules


if __name__ == '__main__':
    mod = import_files(['update_void'])