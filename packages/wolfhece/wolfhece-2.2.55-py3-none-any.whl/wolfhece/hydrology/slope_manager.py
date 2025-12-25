"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os import path
import matplotlib.pyplot as plt
import numpy.ma as ma
import numpy as np

from ..wolf_array import WolfArray
from ..PyTranslate import _

class slope_stats():
    
    mydir: str
    reaches: WolfArray
    slopes: WolfArray
    subs: WolfArray
    times: WolfArray

    mysubs: dict
    nbsubs: int

    mystats: dict

    def __init__(self,dir_charact, *args, **kwargs):

        self.mydir=path.normpath(dir_charact)

        self.reaches= WolfArray(self.mydir+'\\Drainage_basin.reachs')
        self.slopes= WolfArray(self.mydir+'\\Drainage_basin.slope')
        self.subs= WolfArray(self.mydir+'\\Drainage_basin.sub')
        self.times= WolfArray(self.mydir+'\\Drainage_basin.time')

        return super().__init__(*args, **kwargs)


    def init_subs(self):

        self.nbsubs = int(np.max(self.subs.array))
        self.mysubs={}

        #Initialisation de la matrice de mask (d'une extension et d'une résolution similaire aux données radar)
        for i in range(1,self.nbsubs+1):
            self.mysubs[i]={}
            self.mysubs[i]['name'] = 'sub n'+str(i)
            self.mysubs[i]['mask'] = WolfArray(mold=self.subs)
            self.mysubs[i]['mask'].mask_allexceptdata(float(i))
            self.mysubs[i]['surface'] = self.mysubs[i]['mask'].nbnotnull * self.mysubs[i]['mask'].dx * self.mysubs[i]['mask'].dy

    def compute_stats(self):
        
        self.mystats={}
        self.mystats['slopemin'] = ma.min(self.slopes.array)
        self.mystats['slopemax'] = ma.max(self.slopes.array)
        self.mystats['slopemedian'] = ma.median(self.slopes.array)
        self.mystats['slopemean'] = ma.mean(self.slopes.array)
        self.mystats['hist'] = self.slopes.array.data[self.slopes.array.mask == False]
        
        self.slopes.array.mask = np.logical_or(self.slopes.array.mask,np.logical_not(self.reaches.array.mask))
        self.mystats['hist_watershed'] = self.slopes.array.data[self.slopes.array.mask == False]

        self.slopes.array.mask = self.reaches.array.mask
        self.mystats['hist_reaches'] = self.slopes.array.data[self.slopes.array.mask == False]

        for i in range(1,self.nbsubs+1):
            self.mysubs[i]['stats']={}

            self.slopes.array.mask = self.mysubs[i]['mask'].array.mask
            self.mysubs[i]['stats']['slopemin'] = ma.min(self.slopes.array)
            self.mysubs[i]['stats']['slopemax'] = ma.max(self.slopes.array)
            self.mysubs[i]['stats']['slopemedian'] = ma.median(self.slopes.array)
            self.mysubs[i]['stats']['slopemean'] = ma.mean(self.slopes.array)
            
            self.mysubs[i]['stats']['hist'] = self.slopes.array.data[self.slopes.array.mask == False]

            self.slopes.array.mask = np.logical_or(self.slopes.array.mask,self.reaches.array.mask)
            self.mysubs[i]['stats']['hist_reaches'] = self.slopes.array.data[self.slopes.array.mask == False]

            self.slopes.array.mask = self.mysubs[i]['mask'].array.mask
            self.slopes.array.mask = np.logical_or(self.slopes.array.mask,np.logical_not(self.reaches.array.mask))
            self.mysubs[i]['stats']['hist_watershed'] = self.slopes.array.data[self.slopes.array.mask == False]

        self.slopes.mask_data(0.)

    def plot_stats(self):

        bins=[0,1e-8,1e-7,1e-5,1e-2,1e-1,2e-1,3e-1,4e-1,5e-1,6e-1,7e-1,8e-1,9e-1,1]
        fig,ax = plt.subplots(3)
        ax[0].hist(self.mystats['hist'],bins,cumulative=True,density=True)
        ax[0].set_xscale('log')
        #ax[0].set_yscale('log')
        ax[0].set_xlabel('All meshes')
        ax[1].hist(self.mystats['hist_watershed'],bins,cumulative=True,density=True)
        ax[1].set_xscale('log')
        #ax[1].set_yscale('log')
        ax[1].set_xlabel('Watershed')
        ax[2].hist(self.mystats['hist_reaches'],bins,cumulative=True,density=True)
        ax[2].set_xscale('log')
        #ax[2].set_yscale('log')
        ax[2].set_xlabel('River')


        nblines = int(np.ceil(np.sqrt(self.nbsubs+1)))

        fig,ax=plt.subplots(nblines,nblines)
        fig.suptitle('All meshes')
        for i in range(1,self.nbsubs+1):
            curax = ax[int(np.floor((i-1)/nblines)),int(np.mod((i-1),nblines))]
            curax.hist(self.mysubs[i]['stats']['hist'],bins,cumulative=True,density=True)
            curax.set_xscale('log')
            #curax.set_yscale('log')

        fig,ax=plt.subplots(nblines,nblines)
        fig.suptitle('River reaches')
        for i in range(1,self.nbsubs+1):
            curax = ax[int(np.floor((i-1)/nblines)),int(np.mod((i-1),nblines))]
            curax.hist(self.mysubs[i]['stats']['hist_reaches'],bins,cumulative=True,density=True)
            curax.set_xscale('log')
            #curax.set_yscale('log')

        fig,ax=plt.subplots(nblines,nblines)
        fig.suptitle('Watershed')
        for i in range(1,self.nbsubs+1):
            curax = ax[int(np.floor((i-1)/nblines)),int(np.mod((i-1),nblines))]
            curax.hist(self.mysubs[i]['stats']['hist_watershed'],bins,cumulative=True,density=True)
            curax.set_xscale('log')
            #curax.set_yscale('log')

        plt.show()
