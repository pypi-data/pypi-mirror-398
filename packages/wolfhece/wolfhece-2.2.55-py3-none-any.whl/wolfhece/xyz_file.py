"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

# Fichier xyz
import numpy as np
import matplotlib.pyplot as plt
from os.path import normpath,exists,join,basename
from os import listdir,scandir
import logging

from .PyTranslate import _

class XYZFile:
    """ Classe pour la gestion des fichiers xyz """
    x:np.array
    y:np.array
    z:np.array
    filename:str

    def __init__(self, fname:str, toread:bool= True,
                 folder:str= None, bounds:list= None,
                 delimiter:str=','):
        """ Initialisation du nom du fichier """

        self.filename = fname

        self.x = None
        self.y = None
        self.z = None
        self.xyz = None

        if toread:
            self.read_from_file(folder=folder, bounds=bounds, delimiter=delimiter)

    @property
    def nblines(self):
        if self.x is None:
            return 0
        else:
            return len(self.x)

    def reset(self):
        """ Reset des données """
        self.x = None
        self.y = None
        self.z = None
        self.xyz = None

    def test_bounds(self,bounds):

        if bounds is None:
            return True

        x1=bounds[0][0]
        x2=bounds[0][1]
        y1=bounds[1][0]
        y2=bounds[1][1]

        mybounds = self.get_extent()

        test = not(x2 < mybounds[0][0] or x1 > mybounds[0][1] or y2 < mybounds[1][0] or y1 > mybounds[1][1])

        return test

    def read_from_file(self, folder:str=None, bounds:list=None, delimiter=','):
        """ Lecture d'un fichier xyz et remplissage de l'objet """

        try:
            if folder is None:
                self.xyz = np.genfromtxt(self.filename, delimiter=delimiter, dtype=np.float32)
            else:
                if bounds is None:
                    self.reset()
                    logging.error(_('Bounds must be defined when reading a directory'))
                    return

                self.xyz = xyz_scandir(folder,bounds=bounds,delimiter=delimiter)
                # check if self.xyz is an empty array
                if len(self.xyz) == 0:
                    self.xyz = None
                    return
        except:
            self.reset()
            logging.error(_('Error reading file: {self.filename}'))
            return

        self.x = self.xyz[:,0]
        self.y = self.xyz[:,1]
        self.z = self.xyz[:,2]

    def fill_from_wolf_array(self, myarray,nullvalue=0.):
        """ Création d'un fichier xyz depuis les données d'un WOLF array """

        nbmaxlines = myarray.nbx * myarray.nby
        self.x = np.zeros(nbmaxlines)
        self.y = np.zeros(nbmaxlines)
        self.z = np.zeros(nbmaxlines)

        k=0
        for cury in range(myarray.nby):
            y = cury * myarray.dy + 0.5 * myarray.dy + myarray.origy + myarray.transly
            for curx in range(myarray.nbx):
                z = myarray.array[curx, cury]
                if z != nullvalue:
                    x = curx * myarray.dx + 0.5 * myarray.dx + myarray.origx + myarray.translx
                    self.x[k] = x
                    self.y[k] = y
                    self.z[k] = z
                    k+=1

        # crop the arrays
        self.x = self.x[:k]
        self.y = self.y[:k]
        self.z = self.z[:k]

    def write_to_file(self):
        """ Ecriture des informations dans un fichier """

        with open(self.filename, 'w') as f:
            for i in range(self.nblines):
                f.write('{:.3f},{:.3f},{:.3f}\n'.format(self.x[i], self.y[i], self.z[i]))

    def get_extent(self):
        """ Retourne les limites du rectangle qui encadre le nuage de points """

        xlim = [np.min(self.x), np.max(self.x)]
        ylim = [np.min(self.y), np.max(self.y)]
        return (xlim, ylim)

    def merge(self, xyz_list:list["XYZFile"]):
        """ Merge des fichiers xyz en 1 seul """

        newxyz = np.concatenate([cur.xyz for cur in xyz_list])

        if self.xyz is not None:
            self.xyz = np.concatenate([self.xyz,newxyz])
        else:
            self.xyz = newxyz

        self.x = self.xyz[:,0]
        self.y = self.xyz[:,1]
        self.z = self.xyz[:,2]

    def plot(self):
        """ Représentation graphique des points """

        plt.scatter(self.x, self.y, c=self.z, marker='.', cmap='viridis', edgecolors='none')
        plt.xlabel('x [m]')
        plt.ylabel('y [m]')
        plt.colorbar()
        plt.axis('equal')
        plt.savefig('figure.png',dpi=300)
        plt.ion()
        plt.show()
        plt.pause(0.1)

    def find_points(self,bounds):

        if bounds is None:
            return self.xyz

        xb=bounds[0]
        yb=bounds[1]

        # Get arrays which indicate invalid X, Y, or Z values.
        X_valid = (xb[0] <= self.x) & (xb[1] > self.x)
        Y_valid = (yb[0] <= self.y) & (yb[1] > self.y)
        good_indices = np.where(X_valid & Y_valid)[0]
        return self.xyz[good_indices]

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def xyz_scandir(mydir:str, bounds:list, delimiter:str=',') -> np.ndarray:
    """
    Function that reads all the xyz files in a directory and its subdirectories

    :param mydir: directory to scan
    :dtype mydir: str
    :param bounds: bounds of the area to consider [[x1,x2],[y1,y2]]
    :dtype bounds: list
    :return: list of points
    """

    first=[]
    for curfile in listdir(mydir):
        if curfile.endswith('.xyz'):
            mydata = XYZFile(join(mydir,curfile), delimiter=delimiter)
            if mydata.test_bounds(bounds):
                if isinstance(mydir,str):
                    logging.info(mydir)
                else:
                    logging.info(mydir.path)
                logging.info(curfile)
                first.append(mydata.find_points(bounds))

    # if there is a subdirectory, we go deeper
    for entry in scandir(mydir):
        if entry.is_dir():
            locf=xyz_scandir(entry, bounds, delimiter)
            if len(locf)>0:
                first.append(locf)

    retfirst=[]

    if len(first)>0 :
        retfirst=np.concatenate(first)

    return retfirst
