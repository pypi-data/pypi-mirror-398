
"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import glob
from os.path import join, exists
from os import remove
from osgeo import gdal
import logging

from .PyTranslate import _
from .wolf_array import WolfArray, WolfArrayMB
from .PyVertexvectors import zone,Zones,vector


class Tiles(Zones):
    """
    Gestion de données, par ex. topographiques, par tuiles (fichiers .tif indépendants)

    Besoin d'un répertoire contenant les tuiles et d'un shapefile de référencement
    Si le répertoire ne contient qu'un seul fichier tif général, les fichiers par tuile seront créés à la volée et stocké sur disque

    ** SURCHARGE ** de la classe "Zones" pour récupérer les routines graphiques
    """

    def __init__(self,
                 filename='',
                 ox: float = 0,
                 oy: float = 0,
                 tx: float = 0,
                 ty: float = 0,
                 parent=None,
                 is2D=True,
                 idx: str = '',
                 plotted: bool = True,
                 mapviewer=None,
                 need_for_wx: bool = False,
                 linked_data_dir=None) -> None:
        """
        :param filename: le fichier de forme (ShapeFile) de tuilage
        :param linked_data_dir: le répertoire des données .tif
        """
        super().__init__(filename, ox, oy, tx, ty, parent, is2D, idx, plotted, mapviewer, need_for_wx)

        self.linked_data_dir      = linked_data_dir # Réprtoire de données source
        self.linked_data_dir_comp = linked_data_dir

        self.loaded_tiles = [] # liste des tuiles déjà chargées - noms des fichiers, pas les données

    def set_comp_dir(self, comp_dir:str = None):
        """
        Ajout d'un répertoire de comparaison.
        Si le répertoire de comparaison est différent de celui des données alors la valeur renvoyée sera le différentiel.

        Delta = comparaison - source
        """

        if (comp_dir is not None):
            if len(comp_dir.strip())>0:
                self.linked_data_dir_comp = comp_dir.strip()

    def get_array(self, boundvector:vector = None, forceupdate = True):
        """
        Récupération de la matrice

        boundvector : vecteur duquel les bornes seront extraites -> polygon du shapefile de tuilage
        forceupdate : force la MAJ même si le fichier a déjà été chargé précédemment

        """
        if boundvector is None:
            logging.warning(_('Click inside a polygon, not outside :-) !'))
            return
        #objet de retour
        retarray  = None
        # récupération des bornes
        bbox      = boundvector.get_bounds()
        # nom du vecteur --> utile pour idx
        boundname = boundvector.myname
        # instance de comparaison
        comp      = None
        src       = None

        if self.linked_data_dir == self.linked_data_dir_comp:
            # pas de comparaison car répertoire source et comp identique

            # récupération du fichier .tif avec le nom associé au vecteur
            if boundname.endswith('.tif'):
                boundname = boundname[:-4]
            file = glob.glob(join(self.linked_data_dir,'*{}*.tif').format(boundname))

            if len(file)>0:
                # le fichier existe
                if not file[0] in self.loaded_tiles or forceupdate:
                    # on ne le lit que si pas déjà chargé ou forcé
                    retarray = WolfArray(fname=file[0],
                                         mapviewer=self.mapviewer,
                                         idx=boundname,
                                         plotted=True)


                    if retarray.array.shape != (int(abs(bbox[1][0]-bbox[0][0])/retarray.dx), int(abs(bbox[1][1]-bbox[0][1])/retarray.dy)):
                        # test des bornes réelles vis-à-vis des dimensions de la matrice
                        logging.warning(_('Bad shape according to real coordinates -- Verify {}'.format(file[0])))
                        logging.warning(_('Return value is None'))
                        return None

                    self.loaded_tiles.append(file[0])
            else:
                # recherche des fichiers .tif
                file = glob.glob(join(self.linked_data_dir,'*.tif'))
                file_vrt = glob.glob(join(self.linked_data_dir,'*.vrt'))

                if len(file)>0 or len(file_vrt)>0:
                    # des fichiers tif existent

                    # si ce sont des tuiles, alors on a supposé que "-" est dans le nom de fichier
                    # s'il existe un fichier global alors le nom ne doit pas contenir "-" et il doit être listé en premier
                    if '-' in file[0] and len(file_vrt)==0:
                        logging.info(_('No file with {}'.format(boundname)))
                        return None
                    elif '-' in file[0] and len(file_vrt)>0:
                        file[0] = file_vrt[0]
                        logging.info(_('Using vrt file to extract {}'.format(boundname)))
                    elif '-' in file[0]:
                        logging.info(_('No file from which exract {}'.format(boundname)))
                        return None

                    # A partir d'ici, si le fichier de tuile existait sur disque, la première partie du test aurait dû être vérifiée
                    # Il existe un fichier global, càd sans "-"

                    # on va créer le fichier de tuile
                    newname = file[0] + '-' + str(int(bbox[0][0])) + '_' + str(int(bbox[1][1])) + '.tif'

                    gdal.Translate(newname, file[0], projWin = [bbox[0][0], bbox[1][1], bbox[1][0], bbox[0][1]])
                    retarray = WolfArray(fname=newname, mapviewer=self.mapviewer, idx=boundname, plotted=True)
                    retarray.count() # identification des valeurs non nulles
                else:
                    return None

            assert(isinstance(retarray, WolfArray)), 'Bad type'
        else:
            # comparaison car répertoire source et comp différents

            # recherche des fichiers de tuile dans les 2 répertoires
            file1 = glob.glob(join(self.linked_data_dir,'*{}*.tif').format(boundname))
            file2 = glob.glob(join(self.linked_data_dir_comp,'*{}*.tif').format(boundname))

            # Lecture ou création du fichier source
            if len(file1)>0:
                src = WolfArray(fname = file1[0], mapviewer = self.mapviewer, idx = file1[0])
            else:
                file1 = glob.glob(join(self.linked_data_dir,'*.tif'))
                file1_vrt = glob.glob(join(self.linked_data_dir,'*.vrt'))

                if len(file1)>0 or len(file1_vrt)>0:
                    if '-' in file1[0]  and len(file1_vrt)==0:
                        logging.info(_('No file with {}'.format(boundname)))
                        return None
                    elif '-' in file1[0] and len(file1_vrt)>0:
                        file1[0] = file1_vrt[0]
                        logging.info(_('Using vrt file to extract {}'.format(boundname)))
                    elif '-' in file1[0]:
                        logging.info(_('No file from which exract {}'.format(boundname)))
                        return None

                    newname = file1[0] + '-' + str(int(bbox[0][0])) + '_' + str(int(bbox[1][1])) + '.tif'
                    gdal.Translate(newname, file1[0], projWin = [bbox[0][0], bbox[1][1], bbox[1][0], bbox[0][1]])
                    src = WolfArray(fname = newname, mapviewer = self, idx = file1[0])

            if src.array.shape != (int(abs(bbox[1][0]-bbox[0][0])/src.dx), int(abs(bbox[1][1]-bbox[0][1])/src.dy)):
                logging.warning(_('Bad shape according to real coordinates -- Verify {}'.format(file1[0])))
                logging.warning(_('Return value is None'))
                return None

            # Lecture ou création du fichier de comparaison
            if len(file2)>0:
                comp = WolfArray(fname = file2[0], mapviewer = self.mapviewer, idx = file2[0])
            else:
                file2 = glob.glob(join(self.linked_data_dir_comp,'*.tif'))
                file2_vrt = glob.glob(join(self.linked_data_dir_comp,'*.vrt'))

                if len(file2)>0 or len(file2_vrt)>0:

                    if '-' in file2[0]  and len(file2_vrt)==0:
                        logging.info(_('No comp file with {}'.format(boundname)))
                        return None
                    elif '-' in file2[0] and len(file1_vrt)>0:
                        file2[0] = file2_vrt[0]
                        logging.info(_('Using vrt file to extract {}'.format(boundname)))
                    elif '-' in file2[0]:
                        logging.info(_('No file from which exract comparaison {}'.format(boundname)))
                        return None

                    newname = file2[0] + '-' + str(int(bbox[0][0])) + '_' + str(int(bbox[1][1])) + '.tif'
                    gdal.Translate(newname, file2[0], projWin = [bbox[0][0], bbox[1][1], bbox[1][0], bbox[0][1]])
                    comp = WolfArray(fname = newname, mapviewer = self, idx = file2[0])

            if comp is None or src is None:
                logging.info(_('At least one file is missing --  Nothing to do ! -- Retry or Debug !'))
                return None

            if comp.dx != src.dx:
                logging.info(_('Different spatial resolution --> rebin comparison array'))
                comp.rebin(src.dx/comp.dx)


            if comp.array.shape == src.array.shape:
                retarray = comp-src
                retarray.count()
                assert(isinstance(retarray, WolfArray)), 'Bad type'
            else:
                logging.info(_('Bad shape for {}'.format(boundname)))
                try:
                    if exists(newname):
                        remove(newname)
                except:
                    pass
                retarray = None

        return retarray