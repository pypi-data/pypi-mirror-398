"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os.path import exists, join, dirname
import logging
import numpy as np
import matplotlib.pyplot as plt
import sys

try:
    from .PyTranslate import _
except:
    from wolfhece.PyTranslate import _

try:
    from .tools2d_dll import Tools2DFortran
except Exception as ex:
    pass

class Hist_file():

    def __init__(self, fn:str = None) -> None:

        self._times = np.void(0)
        self._q = np.void(0)
        self._toolsDll = None

        if fn is None:
            return
        else:
            self.readfile(fn)

    def readfile(self, fn):
        if not exists(fn):
            logging.warning(_('File {} does not exist'.format(fn)))
            return
        with open(fn) as f:
            array = f.read().splitlines()
            nblines=len(array)
            array = np.asarray([float(val.strip()) for cur in array for val in cur.split('\t')[:-1]])
            array = array.reshape(nblines, int(len(array)/nblines))
        self._times = array[:,0]
        self._q = array[:,1:]

    def create_from_sim(self, sim:str='', vec:str='',
                        simtype:int=0, res:str='',
                        cutcell:str=''):

        if not(exists(sim) and exists(vec)):
            logging.warning(_('Check your files'))
            return

        if simtype==2:
            if not exists(cutcell):
                logging.warning(_('Check your cutcell file'))
                return

        try:
            self._toolsDll = Tools2DFortran(fn_simul=sim)
        except Exception as ex:
            logging.error(_('Error loading tools2d_dll: {}').format(ex))
            return

        self._toolsDll.r2D_create_convergence_border(vec, simtype, res, cutcell)

        self.readfile(res)


    @property
    def nb(self):
        return self._q.shape[1]

    def __getitem__(self,id)-> np.ndarray:
        return self._times, self._q[:,id]

    def plot(self, id=None, absolute=True, figax=None, toshow=False):
        if figax is None:
            fig,ax = plt.subplots()
        else:
            fig,ax =figax

        if id is None:
            for i in range(self.nb):
                t,q = self[i]
                if absolute:
                    ax.plot(t,abs(q), label=_('Profile {}'.format(i+1)))
                else:
                    ax.plot(t,q, label=_('Profile {}'.format(i+1)))
        elif isinstance(id,list) or isinstance(id, np.ndarray):
            for i in id:
                t,q = self[id]
                if absolute:
                    ax.plot(t,abs(q), label=_('Profile {}'.format(i+1)))
                else:
                    ax.plot(t,q, label=_('Profile {}'.format(i+1)))
        else:
            t,q = self[id]
            if absolute:
                ax.plot(t,abs(q), label=_('Profile {}'.format(id+1)))
            else:
                ax.plot(t,q, label=_('Profile {}'.format(id+1)))

        fig.legend()

        if toshow:
            fig.show()

        return fig,ax

if __name__=='__main__':

    wdir = r'data\sim_example\wolf_sim_ke'

    myhist = Hist_file(join(wdir,"out.hist"))

    myhist.plot()
    myhist.plot([1,3,5])
    myhist.plot(0)
    myhist.plot(np.arange(0,3))


    pass