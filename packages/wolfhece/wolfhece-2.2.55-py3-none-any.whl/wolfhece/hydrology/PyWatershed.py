"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import os
from scipy.interpolate import interpolate
from scipy.spatial import KDTree
from matplotlib import figure as mplfig
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import logging
from tqdm import tqdm
import numpy as np

from ..PyTranslate import _
from ..PyVertex import wolfvertex, cloud_vertices
from ..PyVertexvectors import Zones, zone, vector
from ..wolf_array import *
from ..PyCrosssections import crosssections as CrossSections
from ..GraphNotebook import PlotNotebook
from .read import *
from ..PyParams import Wolf_Param

LISTDEM=['dem_before_corr','dem_after_corr','dem_10m','dem_20m','crosssection']
#LISTDEM=['dem_after_corr']

class Node_Watershed:
    """Noeud du modèle hydrologique maillé"""
    i:int   #indice i dans la matrice
    j:int   #indice j dans la matrice

    x:float # coordonnée X
    y:float # coordonnée Y

    index:int  # Numérotation de la maille dans la liste de l'objet Watershed qui l'a initialisé

    dem:dict[str,float] # dictionnaire des valeurs d'altitudes
    demdelta:float      # correction apportée dans la phase de prépro

    crosssections:list  # sections en travers sontenues dans la maille

    time:float      # temps de propagation - cf Drainage_basin.time
    slope:float     # pente calculée ne prépro
    sloped8:float   # pente selon les 8 voisins

    slopecorr:dict  # pente corrigée
    demcorr:dict    # dictionnaire d'alrtitude corrigées

    river:bool      # maille rivière => True
    reach:int       # index du bief
    sub:int         # inde du sous-bassin
    forced:bool     # maille d'échange forcé
    uparea:float    # surface drainée - cf Drainage_basin.cnv

    strahler:int    # indice de Strahler - cf "create_index"
    reachlevel:int  # Niveau du bief - cf "create_index"

    cums:float      # longueur curviligne cumulée **depuis l'aval** -- cf "incr_curvi"
    incrs:float     # incrément de longueur curvi - dx ou sqrt(2)*dx si voisin en crois ou en diagonale

    down:"Node_Watershed"           # pointeur vers le noeud aval
    up:list["Node_Watershed"]       # pointeurs vers le(s) noeud(s) amont
    upriver:list["Node_Watershed"]  # pointeurs vers le(s) noeud(s) **rivière** amont

    flatindex:int = -1  # index de la zone de plat

    def __init__(self):
        self.cums=0.
        self.up=None
        self.down=None

    def incr_curvi(self):
        """Incrémentation de la longueur curviligne"""

        if self.down is None:
            self.cums=0.
        else:
            self.cums = self.down.cums+self.incrs
        for curup in self.up:
            curup.incr_curvi()

    def mean_slope_up(self, threshold:float)-> float:
        """Pente moyenne sur depuis les mailles amont"""
        curnode: Node_Watershed
        meanslope=0.
        nbmean=0
        for curnode in self.up:
            if curnode.slope>threshold:
                nbmean+=1.
                meanslope+=curnode.slope
        if nbmean>0:
            meanslope=meanslope/nbmean

        return meanslope

    def slope_down(self, threshold:float)->float:
        """
        Recherche d'une pente supérieure à un seuil
        Parcours vers l'aval
        """
        slopedown=0.
        curnode=self
        while curnode.slope < threshold:
            if curnode.down is None:
                break
            curnode=curnode.down

        slopedown = curnode.slope
        return slopedown

    def slope_upriver(self,threshold:float)->float:
        """
        Recherche d'une pente supérieure à un seuil
        Parcours vers l'amont uniquement selon les rivières
        """
        slopeup=0.
        if self.slope<threshold:
            if len(self.upriver)>0:
                slopeup=self.upriver[0].slope_upriver(threshold)
            else:
                slopeup=-1.
        else:
            slopeup = self.slope

        return slopeup

    def set_strahler(self, strahler:int):
        """

        """
        self.strahler = strahler

    def distance(self, x:float, y:float) -> float:
        """ Distance euclidienne """

        return np.sqrt(pow(self.x-x,2)+pow(self.y-y,2))

    def get_up_nodes(self, excluded_node:list["Node_Watershed"]=[]):
        """
        Get all upstream nodes
        """

        all_up = [self]
        all_rivers = [self] if self.river else []
        all_runoff = [] if self.river else [self]

        for curup in self.up:

            if curup in excluded_node:
                continue

            all_up.append(curup)
            if curup.river:
                all_rivers.append(curup)
            else:
                all_runoff.append(curup)

            up, river, runoff = curup.get_up_nodes(excluded_node)
            all_up.extend(up)
            all_rivers.extend(river)
            all_runoff.extend(runoff)

        return all_up, all_rivers, all_runoff

    def get_up_nodes_same_sub(self, excluded_node:list["Node_Watershed"]=[]):
        """
        Get all upstream nodes in the same sub-basin
        """

        all_up = [self]
        all_rivers = [self] if self.river else []
        all_runoff = [] if self.river else [self]

        for curup in self.up:

            if curup in excluded_node:
                continue

            added = False
            if curup.sub == self.sub:
                all_up.append(curup)
                added = True

            if curup.river:
                all_rivers.append(curup)
            else:
                all_runoff.append(curup)

            if added:
                up, river, runoff = curup.get_up_nodes_same_sub(excluded_node)
                all_up.extend(up)
                all_rivers.extend(river)
                all_runoff.extend(runoff)

        return all_up, all_rivers, all_runoff

    def get_up_runoff_nodes(self):
        """
        Get all upstream runoff nodes
        """

        all_up = [self]
        for curup in self.up:
            if not curup.river:
                all_up += curup.get_up_runoff_nodes()

        return all_up

    def get_up_runoff_nodes_same_sub(self):
        """
        Get all upstream runoff nodes in the same sub-basin
        """

        all_up = [self]
        for curup in self.up:
            if curup.sub == self.sub and not curup.river:
                all_up += curup.get_up_runoff_nodes_same_sub()

        return all_up


    def get_up_rivernodes(self):
        """
        Get all upstream river nodes
        """

        all_up = [self]
        for curup in self.upriver:
            all_up += curup.get_up_rivernodes()

        return all_up

    def get_up_rivernodes_same_sub(self):
        """
        Get all upstream river nodes in the same sub-basin
        """

        all_up = [self]
        for curup in self.upriver:
            if curup.sub == self.sub:
                all_up += curup.get_up_rivernodes_same_sub()

        return all_up

    def get_up_reaches_same_sub(self) -> list[int]:
        """
        Get all upstream reaches in the same sub-basin
        """

        all_up = [self.reach]
        for curup in self.upriver:
            if curup.sub == self.sub:
                all_up += curup.get_up_reaches_same_sub()

        return np.unique(all_up).tolist()

    def get_down_reaches_same_sub(self) -> list[int]:
        """
        Get all downstream reaches in the same sub-basin
        """

        all_down = [self.reach]
        if self.down is not None:
            if self.down.sub == self.sub:
                all_down += self.down.get_down_reaches_same_sub()

        return np.unique(all_down).tolist()

    def get_down_nodes(self):
        """
        Get all downstream nodes
        """

        all_down = [self]
        if self.down is not None:
            all_down += self.down.get_down_nodes()

        return all_down

    def get_down_nodes_same_sub(self):
        """
        Get all downstream nodes in the same sub-basin
        """

        all_down = [self]
        if self.down is not None:
            if self.down.sub == self.sub:
                all_down += self.down.get_down_nodes_same_sub()

        return all_down

class RiverSystem:
    """
    Classe du réseau de rivières d'un modèle hydrologique WOLF
    """
    nbreaches:int   # nombre de biefs

    #  reaches
    #  |__['reaches']
    #  |  |__[idx]
    #  |     |__['upstream']        # all reaches in upstream
    #  |     |__['baselist']        # list of nodes in the reach
    #  |     |__['up']              # **if upstream** node in upstream
    #  |     |__['fromuptodown']    # **if upstream** list of nodes from upstream to downstream
    #  |__['indexed']
    #  |__['strahler']

    reaches:dict    # dictionnaire des biefs

    kdtree:KDTree   # structure de recherche de voisinage

    upmin:dict      # cf slope_correctionmin
    upmax:dict      # cf slope_correctionmax

    parent:"Watershed"  # objet Watershed parent
    upstreams:dict      # dictionnaire des noeuds en amont

    maxlevels:int       # nombre total de niveaux
    maxstrahler:int     # indice de Strahler max

    tslopemin:float =None   # seuil de pente minimale
    tslopemax:float =None   # seuil de pente maximale

    plotter:PlotNotebook = None # gestionnaire de graphiques
    savedir:str         # répertoire de sauvegarde

    def __init__(self,
                 rivers:list[Node_Watershed],
                 parent:"Watershed",
                 thslopemin:float,
                 thslopemax:float,
                 savedir:str='',
                 computecorr:bool=False,
                 *args,
                 **kwargs):

        self.savedir = savedir
        self.parent  = parent

        self.all_nodes = rivers

        self.init_kdtree(self.all_nodes)

        self.nbreaches = max([x.reach for x in rivers])
        self.reaches   = {}
        self.reaches['reaches'] = {}

        self.upstreams = {}
        self.upstreams['list'] = []

        for curreach in range(1,self.nbreaches+1):
            # attention numérotation 1-based
            listreach, curup = parent.find_rivers(whichreach=curreach)

            if len(curup.upriver) == 0:
                # on est en tête de réseau
                self.upstreams['list'].append(curup)

            self.reaches['reaches'][curreach]={}
            curdict=self.reaches['reaches'][curreach]
            curdict['upstream']=curup
            curdict['baselist']=listreach

        self.create_index() # index et Strahler

        if computecorr:
            self.tslopemin=thslopemin
            self.tslopemax=thslopemax
            self.slope_correctionmin()
            self.slope_correctionmax()

        return super().__init__(*args, **kwargs)

    def init_kdtree(self, nodes:list[Node_Watershed]):
        """Create a KDTree structure from coordinates"""
        xy = [[curnode.x, curnode.y]  for curnode in nodes]
        self.kdtree = KDTree(xy)

    def get_nearest_nodes(self, xy:np.ndarray | vector, nb:int = 1) -> tuple[np.ndarray | float, list[Node_Watershed] | Node_Watershed]:
        """
        Return the distance and the  nearest Node_Watershed

        :param xy = np.ndarray - shape (n,2)
        :param nb = number of neighbors

        return
        """

        if isinstance(xy, vector):
            centroid = xy.centroid
            xy = np.array([[centroid.x, centroid.y]])

        dd, ii = self.kdtree.query(xy, nb)

        if isinstance(ii, int | np.int64):
            return dd, self.all_nodes[ii]
        elif isinstance(ii, np.ndarray | list):
            if len(ii) == 1:
                return dd[0], self.all_nodes[ii[0]]
            else:
                return dd, [self.all_nodes[curi] for curi in ii]

    def get_nodes_in_reaches(self, reaches:list[int])->list[Node_Watershed]:
        """
        Get nodes in a reaches
        """
        all_nodes = []
        for cur_reach in reaches:
            all_nodes.extend(self.reaches['reaches'][cur_reach]['baselist'])

        return all_nodes

    def get_downstream_node_in_reach(self, reach:int)->Node_Watershed:
        """
        Get downstream node in a reach
        """

        return self.reaches['reaches'][reach]['baselist'][0]

    def get_upstream_node_in_reach(self, reach:int)->Node_Watershed:
        """
        Get upstream node in a reach
        """

        return self.reaches['reaches'][reach]['baselist'][-1]

    def get_downstream_reaches(self, node:Node_Watershed)->list[int]:
        """
        Get index of downstream reaches
        """

        curnode = node
        downreaches = []
        while not curnode is None:
            downreaches.append(curnode.reach)
            curnode = curnode.down

        return list(np.unique(downreaches))

    def get_kdtree_downstream(self, node:Node_Watershed)-> tuple[list[Node_Watershed], KDTree]:
        """
        Get KDTree of downstream reaches
        """

        downreaches = self.get_downstream_reaches(node)
        return self.get_kdtree_from_reaches(downreaches)

    def get_kdtree_from_reaches(self, reaches:list[int])->tuple[list[Node_Watershed], KDTree]:
        """
        Get KDTree from a list of reaches
        """

        nodes = self.get_nodes_in_reaches(reaches)
        xy = [[curnode.x, curnode.y]  for curnode in nodes]
        return nodes, KDTree(xy)

    def get_downstream_reaches_excluded(self, node:Node_Watershed, excluded:list[int])->list[int]:
        """
        Get index of downstream reaches, excepted the excluded ones
        """

        list_reaches = self.get_downstream_reaches(node)

        for cur in excluded:
            if cur in list_reaches:
                list_reaches.remove(cur)

        return list_reaches

    def go_downstream_until_reach_found(self, node:Node_Watershed, reach:int | list[int])->Node_Watershed:
        """ Go downstream until a reach is found """

        curnode = node
        if isinstance(reach, int):
            while not curnode is None:
                if curnode.reach == reach:
                    break
                curnode = curnode.down
        elif isinstance(reach, list):
            while not curnode is None:
                if curnode.reach in reach:
                    break
                curnode = curnode.down

        return curnode

    def get_cums(self, whichreach:int=None, whichup:int=None):
        """
        Récupération de la position curvi
        """
        curnode:Node_Watershed
        if whichreach is not None:
            nodeslist=self.reaches['reaches'][whichreach]['baselist']
            x=[curnode.cums for curnode in nodeslist]
        elif whichup is not None:
            x=[]
            curnode=self.upstreams['list'][whichup]
            while curnode is not None:
                x.append(curnode.cums)
                curnode=curnode.down
        else:
            x=[]

        return x

    def get_dem(self, whichdem:str, whichreach:int=None, whichup:int=None):
        """
        Récupération de l'altitude pour une matrice spécifique
        """
        if whichreach is not None:
            nodeslist=self.reaches['reaches'][whichreach]['baselist']
            dem=[curnode.dem[whichdem] for curnode in nodeslist]
        elif whichup is not None:
            curnode:Node_Watershed
            dem=[]
            curnode=self.upstreams['list'][whichup]
            while curnode is not None:
                dem.append(curnode.dem[whichdem])
                curnode=curnode.down
        return dem

    def get_dem_corr(self, whichdem:str, whichreach:int=None, whichup:int=None):
        """
        Récupération de l'altitude corrigée pour une matrice spécifique
        """
        if whichreach is not None:
            nodeslist=self.reaches['reaches'][whichreach]['baselist']
            dem=[curnode.demcorr[whichdem] for curnode in nodeslist]
        elif whichup is not None:
            curnode:Node_Watershed
            dem=[]
            curnode=self.upstreams['list'][whichup]
            while curnode is not None:
                dem.append(curnode.dem[whichdem])
                curnode=curnode.down
        return dem

    def get_slope(self, whichslope:str=None, whichreach:int=None, whichup:int=None):
        """
        Récupération de la pente
        """
        if whichslope is None:
            if whichreach is not None:
                nodeslist=self.reaches['reaches'][whichreach]['baselist']
                slope=[curnode.slope for curnode in nodeslist]
            elif whichup is not None:
                curnode:Node_Watershed
                slope=[]
                curnode=self.upstreams['list'][whichup]
                while curnode is not None:
                    slope.append(curnode.slope)
                    curnode=curnode.down
        else:
            if whichreach is not None:
                nodeslist=self.reaches['reaches'][whichreach]['baselist']
                slope=[curnode.slopecorr[whichslope]['value'] for curnode in nodeslist]
            elif whichup is not None:
                curnode:Node_Watershed
                slope=[]
                curnode=self.upstreams['list'][whichup]
                while curnode is not None:
                    slope.append(curnode.slopecorr[whichslope]['value'])
                    curnode=curnode.down

        return slope

    def get_upstreams_coords(self):
        """
        Récupération des coordonnées des amonts
        """

        xy = [[curnode.x, curnode.y]  for curnode in self.upstreams['list']]
        return np.array(xy)

    def get_nearest_upstream(self, xy:np.ndarray, nb:int) -> tuple[np.ndarray, list[Node_Watershed]]:
        """
        Recherche des amonts les plus proches
        """

        xy_up = self.get_upstreams_coords()
        loc_kd = KDTree(xy_up)
        dd, ii =loc_kd.query(xy, nb)

        return dd, [self.upstreams['list'][curi] for curi in ii]

    def create_index(self):
        """
        Incrément d'index depuis l'amont jusque l'exutoire final
        Parcours des mailles rivières depuis tous les amonts et Incrémentation d'une unité
        Résultat :
            - tous les biefs en amont sont à 1
            - Les autres biefs contiennent le nombre de biefs en amont

        Indice de Strahler
        """
        for curup in self.upstreams['list']:
            curnode:Node_Watershed
            curnode=curup
            while not curnode is None:
                curnode.reachlevel +=1
                curnode=curnode.down

        #recherche de l'index max --> à l'exutoire
        self.maxlevels = self.parent.outlet.reachlevel

        if self.maxlevels == 0:
            logging.warning(_("No reaches found in the watershed. Please check the model configuration and the outlet's position."))
        else:
            self.maxstrahler=0
            self.reaches['indexed']={}
            for i in range(1,self.maxlevels+1):
                self.reaches['indexed'][i]=[]

            #création de listes pour chaque niveau
            for curreach in self.reaches['reaches']:
                curdict=self.reaches['reaches'][curreach]
                listreach=curdict['baselist']
                curlevel=listreach[0].reachlevel
                self.reaches['indexed'][curlevel].append(curreach)

        #création de listes pour chaque amont
        #  on parcourt toutes les mailles depuis chaque amont et on ajoute les index de biefs qui sont différents
        for idx,curup in enumerate(self.upstreams['list']):
            curdict=self.upstreams[idx]={}
            curdict['up']=curup
            curdict['fromuptodown']=[]
            curdict['fromuptodown'].append(curup.reach)
            curnode=curup.down
            while not curnode is None:
                if curnode.reach!=curdict['fromuptodown'][-1]:
                    curdict['fromuptodown'].append(curnode.reach)
                curnode=curnode.down

        if self.maxlevels > 0:
            #création de l'indice de Strahler
            self.reaches['strahler']={}
            #on commence par ajouter les biefs de 1er niveau qui sont à coup sûr d'indice 1
            self.reaches['strahler'][1]=self.reaches['indexed'][1]
            for curreach in self.reaches['strahler'][1]:
                self.set_strahler_in_nodes(curreach,1)

            #on parcourt les différents niveaux
            for i in range(2,self.maxlevels+1):
                listlevel=self.reaches['indexed'][i]
                for curreach in listlevel:
                    curup:Node_Watershed
                    curup=self.reaches['reaches'][curreach]['upstream']
                    upidx=list(x.strahler for x in curup.upriver)
                    sameidx=upidx[0]==upidx[-1]
                    maxidx=max(upidx)

                    curidx=maxidx
                    if sameidx:
                        curidx+=1
                        if not curidx in self.reaches['strahler'].keys():
                            #création de la liste du niveau supérieur
                            self.reaches['strahler'][curidx]=[]
                            self.maxstrahler=curidx

                    self.reaches['strahler'][curidx].append(curreach)
                    self.set_strahler_in_nodes(curreach,curidx)


            myarray=WolfArray(mold=self.parent.subs_array)
            myarray.reset()
            curnode:Node_Watershed
            for curreach in self.reaches['reaches']:
                curdict=self.reaches['reaches'][curreach]
                listreach=curdict['baselist']
                for curnode in listreach:
                    i=curnode.i
                    j=curnode.j
                    myarray.array[i,j]=curnode.strahler
            myarray.filename = self.parent.directory+'\\Characteristic_maps\\Drainage_basin.strahler'
            myarray.write_all()
            myarray.reset()
            for curreach in self.reaches['reaches']:
                curdict=self.reaches['reaches'][curreach]
                listreach=curdict['baselist']
                for curnode in listreach:
                    i=curnode.i
                    j=curnode.j
                    myarray.array[i,j]=curnode.reachlevel
            myarray.filename = self.parent.directory+'\\Characteristic_maps\\Drainage_basin.reachlevel'
            myarray.write_all()

    def set_strahler_in_nodes(self, whichreach:int, strahler:int):
        """
        Mise à jour de la propriété dans chaque noeud du bief
        """
        listnodes = self.reaches['reaches'][whichreach]['baselist']

        curnode:Node_Watershed
        for curnode in listnodes:
            curnode.set_strahler(strahler)

    def plot_dem(self, which:int=-1):
        """
        Graphiques
        """
        mymarkers=['x','+','1','2','3','4']
        if which==-1:
            fig=self.plotter.add('All Reaches')

            ax=fig.add_ax()

            for curreach in self.reaches['reaches']:
                x=np.array(self.get_cums(whichreach=curreach))
                for idx,curdem in enumerate(LISTDEM):
                    y=np.array(self.get_dem(curdem,whichreach=curreach))

                    xmask=np.ma.masked_where(y==99999.,x)
                    ymask=np.ma.masked_where(y==99999.,y)

                    ax.scatter(xmask,ymask,marker=mymarkers[idx],label=curdem)
            ax.legend()
            fig.canvas.draw()

        elif which==-99:
            size=int(np.ceil(np.sqrt(self.nbreaches)))

            fig=self.plotter.add('reaches')

            for index,curreach in enumerate(self.reaches['reaches']):
                #curax=ax[int(np.floor(index/size)),int(np.mod(index,size))]
                curax=fig.add_ax()

                curdict=self.reaches['reaches'][curreach]
                x=np.array(self.get_cums(whichreach=curreach))

                for idx,curdem in enumerate(LISTDEM):
                    y=np.array(self.get_dem(curdem,whichreach=curreach))

                    xmask=np.ma.masked_where(y==99999.,x)
                    ymask=np.ma.masked_where(y==99999.,y)

                    curax.scatter(xmask,ymask,marker=mymarkers[idx],label=curdem)
            curax.legend()
            fig.canvas.draw()

        elif which==-98:
            size=int(np.ceil(np.sqrt(len(self.upstreams['list']))))

            fig=self.plotter.add('reaches')

            for idxup,curup in enumerate(self.upstreams['list']):
                curax=fig.add_ax()

                x=np.array(self.get_cums(whichup=idxup))

                for idx,curdem in enumerate(LISTDEM):
                    y=np.array(self.get_dem(curdem,whichup=idxup))

                    xmask=np.ma.masked_where(y==99999.,x)
                    ymask=np.ma.masked_where(y==99999.,y)
                    curax.scatter(xmask,ymask,marker=mymarkers[idx],label=curdem)

            curax.legend()
            fig.canvas.draw()

        elif which>-1:
            if which<len(self.upstreams['list']):
                if not self.plotter is None:
                    fig=self.plotter.add('Upstream n°'+str(which))
                else:
                    fig=plt.figure()

                ax=fig.add_ax()

                x=np.array(self.get_cums(whichup=which))
                for idx,curdem in enumerate(LISTDEM):
                    y=np.array(self.get_dem(curdem,whichup=which))

                    xmask=np.ma.masked_where(y==99999.,x)
                    ymask=np.ma.masked_where(y==99999.,y)
                    ax.scatter(xmask,ymask,marker=mymarkers[idx],label=curdem)

            ax.legend()
            fig.canvas.draw()

    def plot_dem_and_corr(self, which:int=-1, whichdem:str='dem_after_corr'):
        """
        Graphiques
        """

        if which<len(self.upstreams['list']):
            if not self.plotter is None:
                fig=self.plotter.add('Upstream n°'+str(which))
            else:
                fig=plt.figure()
                fig.suptitle('Upstream n°'+str(which))

            ax=fig.add_ax()

            x=np.array(self.get_cums(whichup=which))
            y=np.array(self.get_dem(whichdem,whichup=which))

            xcorr=self.upmin[which][whichdem][0]
            ycorr=self.upmin[which][whichdem][1]

            xmask=np.ma.masked_where(y==99999.,x)
            ymask=np.ma.masked_where(y==99999.,y)

            ax.scatter(xmask,ymask,marker='x',label=whichdem)
            ax.scatter(xcorr,ycorr,marker='+',label='selected points')

            ax.legend()
            fig.canvas.draw()

            if not self.savedir=='':
                plt.savefig(self.savedir+'\\Up'+str(which)+'_'+whichdem+'.png')

    def plot_slope(self, which:int=-1):
        """
        Graphiques
        """
        mymarkers=['x','+','1','2','3','4']
        if which==-1:
            fig=self.plotter.add('reaches')
            ax=fig.add_ax()

            for curreach in self.reaches['reaches']:
                x=self.get_cums(whichreach=curreach)
                for idx,curdem in enumerate(LISTDEM):
                    y=self.get_slope(curdem,whichreach=curreach)
                    ax.scatter(x,y,marker=mymarkers[idx],label=curdem)
            fig.canvas.draw()

        elif which==-99:
            size=int(np.ceil(np.sqrt(self.nbreaches)))
            fig=self.plotter.add('reaches')

            for index,curreach in enumerate(self.reaches['reaches']):
                curax=fig.add_ax()

                x=self.get_cums(whichreach=curreach)

                for idx,curdem in enumerate(LISTDEM):
                    y=self.get_slope(curdem,whichreach=curreach)
                    curax.scatter(x,y,marker=mymarkers[idx],label=curdem)
            curax.legend()
            fig.canvas.draw()

        elif which==-98:
            size=int(np.ceil(np.sqrt(len(self.upstreams['list']))))

            fig=self.plotter.add('reaches')

            for idxup,curup in enumerate(self.upstreams['list']):
                curax=fig.add_ax()
                x=self.get_cums(whichup=idxup)

                for idx,curdem in enumerate(LISTDEM):
                    y=self.get_slope(curdem,whichup=idxup)
                    curax.scatter(x,y,marker=mymarkers[idx],label=curdem)
            curax.legend()
            fig.canvas.draw()

    def write_slopes(self):
        """
        Ecriture sur disque
        """
        #Uniquement les pentes rivières
        for curlist in LISTDEM:
            slopes= WolfArray(self.parent.directory+'\\Characteristic_maps\\Drainage_basin.slope')
            slopes.reset()
            for curreach in self.reaches['reaches']:
                curdict=self.reaches['reaches'][curreach]
                listreach=curdict['baselist']

                curnode:Node_Watershed
                ijval = np.asarray([[curnode.i, curnode.j, curnode.slopecorr[curlist]['value']]  for curnode in listreach])
                slopes.array[np.int32(ijval[:,0]),np.int32(ijval[:,1])]=ijval[:,2]

            slopes.filename = self.parent.directory+'\\Characteristic_maps\\Drainage_basin.slope_corr_riv_'+curlist
            slopes.write_all()

    def slope_correctionmin(self):
        """
        Correction pente minimale
        """
        if self.tslopemin is not None:
            logging.info(_('select min - river'))
            self.selectmin()
            logging.info(_('slope correction min - river'))
            self.compute_slopescorr(self.upmin)

    def slope_correctionmax(self):
        """
        Correction pente maximale
        """
        if self.tslopemax is not None:
            logging.info(_('select max - river'))
            self.selectmax()
            logging.info(_('slope correction max - river'))
            self.compute_slopescorr(self.upmax)

    def selectmin(self):
        """
        Sélection des valeurs minimales afin de conserver une topo décroissante vers l'aval --> une pente positive
        """
        self.upmin={}

        #on initialise le dictionnaire de topo min pour chaque amont
        for idx,curup in enumerate(self.upstreams['list']):
            self.upmin[idx]={}

        curnode:Node_Watershed
        for curdem in LISTDEM:
            logging.info(_('Current DEM : {}'.format(curdem)))
            for idx,curup in enumerate(self.upstreams['list']):
                #on part de l'amont
                curnode=curup
                x=[]
                y=[]

                x.append(curnode.cums)

                if curdem=='crosssection':
                    basey=min(curnode.dem[curdem],curnode.dem['dem_after_corr'])
                else:
                    basey=curnode.dem[curdem]

                y.append(basey)
                curnode=curnode.down

                locs= self.parent.resolution
                while not curnode is None:
                    if curdem=='crosssection':
                        yloc=min(curnode.dem[curdem],curnode.dem['dem_after_corr'])
                    else:
                        yloc=curnode.dem[curdem]

                    #on ajoute la maille si la pente est suffisante, sinon cekla créera un trou dans le parcours
                    if (basey-yloc)/locs>self.tslopemin:
                        x.append(curnode.cums)
                        y.append(yloc)
                        basey=yloc
                        locs= self.parent.resolution
                    else:
                        locs+= self.parent.resolution

                    #if curnode.i==232 and curnode.j==226:
                    #    a=1

                    curnode=curnode.down

                #on stocke les vecteurs de coordonnées curvi et d'altitudes pour les zones respectant les critères
                self.upmin[idx][curdem]=[x,y]

    def selectmax(self):
        """
        Sélection des valeurs maximales afin de conserver une topo décroissante vers l'aval --> une pente positive
        """
        # on travaille sur base de la topo corrigée min
        self.upmax={}

        #on initialise le dictionnaire de topo max pour chaque amont
        for idx,curup in enumerate(self.upstreams['list']):
            self.upmax[idx]={}

        ds=self.parent.resolution
        curnode:Node_Watershed
        for curdem in LISTDEM:
            logging.info(_('Current DEM : {}'.format(curdem)))
            for idx,curup in enumerate(self.upstreams['list']):
                curnode=curup
                x=[]
                y=[]

                basey=curnode.demcorr[curdem]['value']

                x.append(curnode.cums)
                y.append(basey)
                curnode=curnode.down

                locs= ds
                while not curnode is None:
                    yloc=curnode.demcorr[curdem]['value']

                    if (basey-yloc)/locs>self.tslopemax:
                        while len(x)>1 and (basey-yloc)/locs>self.tslopemax:
                            x.pop()
                            y.pop()
                            basey=y[-1]
                            locs+=ds

                    if yloc<y[-1]:
                        x.append(curnode.cums)
                        y.append(yloc)
                        basey=yloc
                        locs=ds

                    curnode=curnode.down

                self.upmax[idx][curdem]=[x,y]

    def compute_slopescorr(self, whichdict:dict):
        """
        Calcul des pents corrigées
        """
        curnode:Node_Watershed
        for curdem in LISTDEM:
            logging.info(_('Current DEM : {}'.format(curdem)))
            for idx,curup in enumerate(self.upstreams['list']):
                curdict=whichdict[idx][curdem]
                xmin=curdict[0]
                if len(xmin)>1:
                    ymin=curdict[1]
                    x=self.get_cums(whichup=idx)

                    #on cale une fonction d'interpolation sur la sélection dans lequalle on a oublié les pentes faibles --> à trou
                    f=interpolate.interp1d(xmin,ymin, fill_value='extrapolate')
                    #on interpole sur tous les x --> on remplit les trous
                    y=f(x)
                    #calcul des pentes sur base des noeuds aval
                    slopes=self.compute_slope_down(x,y)

                    #on remplit le dictionnaire de résultat
                    curnode=curup
                    i=0
                    while not curnode is None:
                        #if curnode.i==232 and curnode.j==226:
                        #    a=1
                        curnode.demcorr[curdem]['parts'].append(y[i])
                        curnode.slopecorr[curdem]['parts'].append(slopes[i])
                        i+=1
                        curnode=curnode.down

        #calcul de la moyenne sur base des valeurs partielles
        for curdem in LISTDEM:
            for curreach in self.reaches['reaches']:
                nodeslist=self.reaches['reaches'][curreach]['baselist']
                for curnode in nodeslist:
                    #if curnode.i==232 and curnode.j==226:
                    #    a=1
                    if len(nodeslist)<2:
                        if not self.tslopemin is None:
                            curnode.slopecorr[curdem]['value']=max(self.tslopemin,curnode.slope)
                        else:
                            curnode.slopecorr[curdem]['value']=self.tslopemin=1.e-4

                        if not self.tslopemax is None:
                            curnode.slopecorr[curdem]['value']=min(self.tslopemax,curnode.slope)
                    else:
                        curnode.demcorr[curdem]['value']=np.mean(curnode.demcorr[curdem]['parts'])
                        curnode.slopecorr[curdem]['value']=np.mean(curnode.slopecorr[curdem]['parts'])

                    #on vide les parts
                    curnode.demcorr[curdem]['parts']=[]
                    curnode.slopecorr[curdem]['parts']=[]

    def compute_slope_down(self, x, y):
        """
        Calcul de pente sur base de x et y
        """
        slope=[]
        for i in range(len(x)-1):
            slope.append((y[i+1]-y[i])/(x[i+1]-x[i]))
        slope.append(slope[-1])
        return slope

    def plot_all_in_notebook(self):
        """
        Graphiques
        """
        self.plotter = PlotNotebook()

        for i in range(self.nbreaches):
            self.plot_dem_and_corr(i,whichdem='crosssection')
        self.plot_dem()
        self.plot_slope(-98)
        self.plot_dem(-98)

class RunoffSystem:
    """Classe de l'ensemble des mailles de ruissellement d'un modèle hydrologique WOLF"""
    nodes:list[Node_Watershed]  # liste de noeuds

    parent:"Watershed"
    upstreams:dict

    tslopemin:float
    tslopemax:float

    upmin:dict
    upmax:dict

    def __init__(self,
                 runoff:list[Node_Watershed],
                 parent:"Watershed",
                 thslopemin:float = None,
                 thslopemax:float = None,
                 computecorr:bool=False,
                 *args,
                 **kwargs):

        self.parent  = parent
        self.nodes = runoff
        self.upstreams={}

        #sélection des mailles qui ont une surface unitaire comme surface drainée
        areaup = pow(parent.resolution,2)/1.e6
        self.upstreams['list']=list(filter(lambda x: (x.uparea-areaup)<1.e-6 ,runoff))

        if computecorr:
            self.tslopemin = thslopemin
            self.tslopemax = thslopemax

            self.slope_correctionmin()
            self.slope_correctionmax()

        return super().__init__(*args, **kwargs)

    def get_oneup(self, idx:int) -> Node_Watershed:
        """
        Récupération d'un amont sur base de l'index
        """
        return self.upstreams['list'][idx]

    def get_cums(self,whichup:int=None):

        if not whichup is None:
            curnode:Node_Watershed
            x=[]
            curnode=self.get_oneup(whichup)
            while not curnode.river:
                x.append(curnode.cums)
                curnode=curnode.down
            if len(x)==1:
                x.append(curnode.cums)
        else:
            x=[]

        return x

    def get_dem(self, whichdem:str, whichup:int=None):
        if not whichdem in LISTDEM:
            return

        if not whichup is None:
            curnode:Node_Watershed
            dem=[]
            curnode=self.get_oneup(whichup)
            while not curnode.river:
                dem.append(curnode.dem[whichdem])
                curnode=curnode.down
        return dem

    def get_dem_corr(self, whichdem:str, whichup:int=None):
        if not whichdem in LISTDEM:
            return

        if not whichup is None:
            curnode:Node_Watershed
            dem=[]
            curnode=self.get_oneup(whichup)
            while not curnode.river:
                dem.append(curnode.dem[whichdem])
                curnode=curnode.down
        return dem

    def get_slope(self, whichslope:str=None, whichup:int=None):

        if whichslope is None:
            if not whichup is None:
                curnode:Node_Watershed
                slope=[]
                curnode=self.get_oneup(whichup)
                while not curnode.river:
                    slope.append(curnode.slope)
                    curnode=curnode.down
        else:
            if not whichup is None:
                curnode:Node_Watershed
                slope=[]
                curnode=self.get_oneup(whichup)
                while not curnode.river:
                    slope.append(curnode.slopecorr[whichslope]['value'])
                    curnode=curnode.down

        return slope

    def plot_dem(self, which:int=-1):

        mymarkers=['x','+','1','2','3','4']
        if which>-1:
            if which<len(self.upstreams['list']):
                fig=plt.figure()
                fig.suptitle('Upstream n°'+str(which))

                x=np.array(self.get_cums(whichup=which))
                for idx,curdem in enumerate(LISTDEM):
                    y=np.array(self.get_dem(curdem,whichup=which))

                    xmask=np.ma.masked_where(y==99999.,x)
                    ymask=np.ma.masked_where(y==99999.,y)
                    plt.scatter(xmask,ymask,marker=mymarkers[idx],label=curdem)

            plt.legend()
        plt.show()

    def plot_dem_and_corr(self, which:int=-1, whichdem:str='dem_after_corr'):

        if which<len(self.upstreams['list']):
            fig=plt.figure()
            fig.suptitle('Upstream n°'+str(which))

            x=np.array(self.get_cums(whichup=which))
            y=np.array(self.get_dem(whichdem,whichup=which))

            xcorr=self.upmin[which][whichdem][0]
            ycorr=self.upmin[which][whichdem][1]

            xmask=np.ma.masked_where(y==99999.,x)
            ymask=np.ma.masked_where(y==99999.,y)

            plt.scatter(xmask,ymask,marker='x',label=whichdem)
            plt.scatter(xcorr,ycorr,marker='+',label='selected points')

            plt.legend()
            plt.savefig(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\Simulations\Hydrologie\Up'+str(which)+'_'+whichdem+'.png')
            #plt.show()

    def write_slopes(self):
        #Uniquement les pentes runoff
        for curlist in LISTDEM:
            slopes= WolfArray(self.parent.directory+'\\Characteristic_maps\\Drainage_basin.slope')
            slopes.reset()
            curnode:Node_Watershed
            for curnode in self.nodes:
                i=curnode.i
                j=curnode.j
                slopes.array[i,j]=curnode.slopecorr[curlist]['value']

            slopes.filename = self.parent.directory+'\\Characteristic_maps\\Drainage_basin.slope_corr_run_'+curlist
            slopes.write_all()

    def slope_correctionmin(self):
        if not self.tslopemin is None:
            logging.info(_('select min - runoff'))
            self.selectmin()
            logging.info(_('slope correction min - runoff'))
            self.compute_slopescorr(self.upmin)

    def slope_correctionmax(self):
        if not self.tslopemax is None:
            logging.info(_('select max - runoff'))
            self.selectmax()
            logging.info(_('slope correction max - runoff'))
            self.compute_slopescorr(self.upmax)

    def selectmin(self):
        #Sélection des valeurs minimales afin de conserver une topo décroissante vers l'aval --> une pente positive
        self.upmin={}

        #on initialise le dictionnaire de topo min pour chaque amont
        for idx,curup in enumerate(self.upstreams['list']):
            self.upmin[idx]={}

        ds=self.parent.resolution
        curnode:Node_Watershed
        for curdem in LISTDEM:
            logging.info(_('Current DEM : {}'.format(curdem)))
            for idx,curup in enumerate(self.upstreams['list']):
                curnode=curup
                x=[]
                y=[]

                if curdem=='crosssection':
                    basey=min(curnode.dem[curdem],curnode.dem['dem_after_corr'])
                else:
                    basey=curnode.dem[curdem]

                x.append(curnode.cums)
                y.append(basey)
                curnode=curnode.down

                locs=ds
                while not curnode is None:
                    if curdem=='crosssection':
                        yloc=min(curnode.dem[curdem],curnode.dem['dem_after_corr'])
                    else:
                        yloc=curnode.dem[curdem]

                    if (basey-yloc)/locs>self.tslopemin:
                        x.append(curnode.cums)
                        y.append(yloc)
                        basey=yloc
                        locs=ds
                        if curnode.river:
                            break
                    else:
                        locs+=ds
                    curnode=curnode.down

                self.upmin[idx][curdem]=[x,y]

    def selectmax(self):
        #Sélection des valeurs minimales afin de conserver une topo décroissante vers l'aval --> une pente positive
        self.upmax={}

        #on initialise le dictionnaire de topo min pour chaque amont
        for idx,curup in enumerate(self.upstreams['list']):
            self.upmax[idx]={}

        ds=self.parent.resolution
        curnode:Node_Watershed
        for curdem in LISTDEM:
            logging.info(_('Current DEM : {}'.format(curdem)))
            for idx,curup in enumerate(self.upstreams['list']):
                curnode=curup
                x=[]
                y=[]

                """
                if curdem=='crosssection':
                    basey=min(curnode.demcorr[curdem]['value'],curnode.demcorr['dem_after_corr']['value'])
                else:
                    basey=curnode.demcorr[curdem]['value']
                """
                basey=curnode.demcorr[curdem]['value']

                x.append(curnode.cums)
                y.append(basey)
                curnode=curnode.down

                locs= ds
                while not curnode is None:
                    """
                    if curdem=='crosssection':
                        yloc=min(curnode.demcorr[curdem]['value'],curnode.demcorr['dem_after_corr']['value'])
                    else:
                        yloc=curnode.demcorr[curdem]['value']
                    """
                    yloc=curnode.demcorr[curdem]['value']

                    if (basey-yloc)/locs>self.tslopemax:
                        while len(x)>1 and (basey-yloc)/locs>self.tslopemax:
                            x.pop()
                            y.pop()
                            basey=y[-1]
                            locs+=ds

                    if yloc<y[-1]:
                        x.append(curnode.cums)
                        y.append(yloc)
                        basey=yloc
                        locs=ds
                        if curnode.river:
                            break

                    curnode=curnode.down
                    #if curnode.i==187 and curnode.j==207:
                    #    a=1

                self.upmax[idx][curdem]=[x,y]

    def compute_slopescorr(self, whichdict:dict):
        curnode:Node_Watershed
        for curdem in LISTDEM:
            logging.info(_('Current DEM : {}'.format(curdem)))
            for idx,curup in enumerate(self.upstreams['list']):
                curdict=whichdict[idx][curdem]
                xmin=curdict[0]
                if len(xmin)>1:
                    ymin=curdict[1]
                    x=self.get_cums(whichup=idx)

                    f=interpolate.interp1d(xmin,ymin, fill_value='extrapolate')
                    y=f(x)
                    slopes=self.compute_slope_down(x,y)

                    curnode=curup
                    i=0
                    while not curnode.river:
                        #if curnode.i==187 and curnode.j==207:
                        #    a=1
                        curnode.demcorr[curdem]['parts'].append(y[i])
                        curnode.slopecorr[curdem]['parts'].append(slopes[i])
                        i+=1
                        curnode=curnode.down
        #calcul de la moyenne sur base des valeurs partielles
        for curdem in LISTDEM:
            for curnode in self.nodes:
                #if curnode.i==187 and curnode.j==207:
                #    a=1
                if len(curnode.slopecorr[curdem]['parts'])<2:
                    #Ce cas particulier peut arriver si des mailles BV sont remplies par une zone plate qui s'étend en rivière
                    # Comme on ne recherche de mailles plus basses que dans la partie BV, il n'est pas possible de corriger les pentes
                    if not self.tslopemin is None:
                        curnode.slopecorr[curdem]['value']=max(self.tslopemin,curnode.slope)
                    else:
                        curnode.slopecorr[curdem]['value']=1.e-4

                    if not self.tslopemax is None:
                        curnode.slopecorr[curdem]['value']=min(self.tslopemax,curnode.slope)
                else:
                    curnode.demcorr[curdem]['value']=np.mean(curnode.demcorr[curdem]['parts'])
                    curnode.slopecorr[curdem]['value']=np.mean(curnode.slopecorr[curdem]['parts'])

                curnode.demcorr[curdem]['parts']=[]
                curnode.slopecorr[curdem]['parts']=[]

    def compute_slope_down(self, x, y):
        """
        Calcul de la pente sur base de listes X et Y
        """
        slope=[]
        for i in range(len(x)-1):
            slope.append((y[i+1]-y[i])/(x[i+1]-x[i]))
        slope.append(slope[-1])
        return slope

class SubWatershed:
    """ Classe sous-bassin versant """
    def __init__(self,
                 parent:"Watershed",
                 name:str,
                 idx:int,
                 mask:WolfArray,
                 nodes:list[Node_Watershed],
                 runoff:list[Node_Watershed],
                 rivers:list[Node_Watershed]) -> None:

        self.parent:"Watershed" = parent
        self.index:int          = idx  # index of subwatershed - **NOT** sorted like in the array
        self.name:str           = name # name of the subwatershed
        self.mask:WolfArray     = mask # WolfArray of the subwatershed -- All nodes are masked except the subwatershed
        self.mask.count()

        self.nodes:list[Node_Watershed]  = nodes    # all nodes in the subwatershed
        self.rivers:list[Node_Watershed] = rivers   # only rivers - sorted by dem value --> outlet is the first one
        self.runoff:list[Node_Watershed] = runoff

        self.idx_reaches = np.unique(np.asarray([x.reach for x in rivers]))

        self._index_sorted = idx

        self._is_virtual:bool        = False
        self._src_sub:"SubWatershed" = None

    @property
    def is_virtual(self) -> bool:
        """ Vérification si le sous-bassin est virtuel """

        return self._is_virtual

    @property
    def surface(self) -> float:
        """ Surface du bassin versant en m² """
        return self.mask.nbnotnull * self.mask.dx * self.mask.dy

    @property
    def area(self) -> float:
        """ Surface du bassin versant en km² """
        return self.surface / 1.e6

    @property
    def area_outlet(self) -> float:
        """ Surface du bassin à l'exutoire """

        return self.outlet.uparea

    @property
    def outlet(self) -> Node_Watershed:
        """ Outlet of the subbasin """

        return self.rivers[0]

    def is_reach_in_sub(self, idx_reach:int) -> bool:
        """ Vérification si un bief est dans le sous-bassin """

        return idx_reach in self.idx_reaches

    def is_in_rivers(self, node:Node_Watershed) -> bool:
        """ Vérification si un noeud est dans les rivières """

        return node in self.rivers

    def get_list_nodes_river(self, idx_reach:int) -> list[Node_Watershed]:
        """
        Récupération des noeuds d'une rivière
        """

        return [x for x in self.rivers if x.reach==idx_reach]

    def get_nearest_river(self, x, y) -> Node_Watershed:
        """
        Récupération du noeud de rivière le plus proche
        """

        return min(self.rivers, key=lambda x: x.distance(x,y))

    def get_max_area_in_reach(self, idx_reach:int) -> float:
        """
        Récupération de la surface maximale dans un bief
        """

        return max([x.uparea for x in self.get_list_nodes_river(idx_reach)])

    def get_min_area_in_reach(self, idx_reach:int) -> float:
        """
        Récupération de la surface minimale dans un bief
        """

        return min([x.uparea for x in self.get_list_nodes_river(idx_reach)])

    def get_min_area_along_reaches(self, reaches:list[int], starting_node:Node_Watershed = None) -> float:
        """ Aire drainée à la limite amont du ss-bassin """

        if starting_node is None:
            starting_node = self.outlet

        upriver = starting_node.upriver

        area_min = []

        idx_reach = 0
        for curnode in upriver:
            if curnode.reach in reaches:
                idx_reach = curnode.reach
                area_min.append(self.get_min_area_in_reach(idx_reach))

        if len(area_min) == 0:
            return None
        else:
            return min(area_min)

    def get_up_rivernode_outside_sub(self, starting_node:Node_Watershed, reaches:list[int]) -> Node_Watershed:
        """ Récupération du noeud de rivière en amont du sous-bassin """

        def up_in_reaches(node:Node_Watershed, reaches:list[int]) -> Node_Watershed:

            if len(node.upriver) == 0:
                # No upstream node
                return node
            else:
                # Iterate over upriver nodes
                for curup in node.upriver:
                    if curup.reach in reaches:
                        # If the reach is in the list, return the node
                        return curup

                # No node found in the list of reaches
                return node

        if self._is_virtual:
            return self._src_sub.get_up_rivernode_outside_sub(starting_node, reaches)

        up = up_in_reaches(starting_node, reaches)
        loc_up = None
        while up is not starting_node and up.sub == starting_node.sub and up is not loc_up:
            # bouclage parfois utile en fonction de la superposition ou non du tracé
            # vectoriel de lit mineur vis-à-vis de la discrétsation hydrologique
            loc_up = up
            up = up_in_reaches(up, reaches)

        return up if up is not loc_up else None

    def get_area_outside_sub_if_exists(self, starting_node:Node_Watershed, reaches:list[int]) -> float:
        """ Aire drainée en amont du sous-bassin """

        up_outside = self.get_up_rivernode_outside_sub(starting_node, reaches)

        if up_outside is None:
            return 0.
        else:
            return up_outside.uparea

    def get_river_nodes_from_upareas(self, min_area:float, max_area:float) -> list[Node_Watershed]:
        """
        Récupération des noeuds de rivière entre deux surfacesde BV.

        Les surfaces sont exprimées en km².

        Les bornes sont incluses.

        :param min_area: surface minimale
        :param max_area: surface maximale
        """

        return [x for x in self.rivers if x.uparea>=min_area and x.uparea<=max_area]

    def is_in_subwatershed(self, vec:vector) -> bool:
        """ Vérification si un vecteur est dans le sous-bassin """

        centroid = vec.centroid

        i, j = self.mask.get_ij_from_xy(centroid.x, centroid.y)

        return self.mask.array.mask[i,j] == False

    def filter_zones(self, zones_to_filter:Zones, force_virtual_if_any:bool = False) -> list[vector]:
        """
        Filtrage des zones pour ne garder que celle se trouvant dans le sous-bassin
        """

        if self._is_virtual and not force_virtual_if_any:
            return self._src_sub.filter_zones(zones_to_filter)

        return [curvec for curzone in zones_to_filter.myzones for curvec in curzone.myvectors if self.is_in_subwatershed(curvec)]

    def get_virtual_subwatershed(self, outlet:Node_Watershed, excluded_nodes:list[Node_Watershed] = []) -> "SubWatershed":
        """
        Création d'un sous-bassin virtuel sur base d'une maille rivière aval
        """

        if not outlet.river:
            logging.error(_('The outlet should be a river node'))
            return None

        mymask = WolfArray(mold = self.mask)
        mymask.array.mask[:,:] = True

        all, river, runoff = outlet.get_up_nodes_same_sub(excluded_nodes)

        for curnode in all:
            mymask.array.mask[curnode.i,curnode.j] = False

        newsub = SubWatershed(self.parent,
                            self.name + '_virtual',
                            self.parent.nb_subs + 1,
                            mymask,
                            all,
                            runoff,
                            river,
                            )

        newsub._is_virtual = True
        newsub._src_sub = self

        return newsub

    def get_downstream_node_in_reach(self, reach:int) -> Node_Watershed:
        """
        Récupération du noeud aval dans un bief
        """

        # rivers are sorted by dem value, so the first one is the outlet
        return self.get_list_nodes_river(reach)[0]

class Watershed:
    """Classe bassin versant"""

    header:header_wolf  # header_wolf of "Drainage_basin.sub" wolf_array

    directory: str            # Répertoire de modélisation

    outlet:Node_Watershed   # exutoire

    subs_array: WolfArray # "Drainage_basin.sub" wolf_array

    nodes:list[Node_Watershed] # all nodes
    nodesindex:np.ndarray # indirect access to mynodes, contains index of instance in list
    rivers:list[Node_Watershed] # all river nodes
    runoff:list[Node_Watershed] # all runoff nodes

    couplednodes:list # forced exchanges

    subcatchments: list[SubWatershed]
    virtualcatchments : list[SubWatershed]
    statisticss: dict

    couplednodesxy:list[float,float,float,float]
    couplednodesij:list[tuple[int,int],tuple[int,int]]

    riversystem:RiverSystem     # réseau de rivières
    runoffsystem:RunoffSystem   # écoulement diffus/hydrologique

    to_update_times:bool        # switch to detect if the time matrix should be updated

    def __init__(self,
                 directory:str,
                 thzmin:float=None,
                 thslopemin:float=None,
                 thzmax:float=None,
                 thslopemax:float=None,
                 crosssections:CrossSections=None,
                 computestats:bool=False,
                 computecorr:bool=False,
                 plotstats:bool=False,
                 plotriversystem=False,
                 dir_mnt_subpixels:str=None,
                 *args, **kwargs):

        self.rivers = []
        self.runoff = []
        self.nodes = []
        self.subcatchments = []
        self.statisticss = {}
        self.header = None
        self.couplednodesij = []
        self.couplednodesxy = []
        self.couplednodes = []

        self.virtualcatchments = []

        logging.info(_('Read files...'))

        self.directory = os.path.normpath(directory)
        self.dir_mnt_subpixels = dir_mnt_subpixels if dir_mnt_subpixels is not None else self.directory

        self.subs_array   = WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basin.sub')

        self.header = header_wolf.read_header((self.directory+'\\Characteristic_maps\\Drainage_basin.b'))

        if self.subs_array.nbx == 0 or self.subs_array.nby == 0:
            logging.error(_('The Watershed sub file is empty or not valid.'))
            return

        # Use params to get the directory and filename of forced exchanges
        _mainparams = Wolf_Param(filename = os.path.join(self.directory, "Main_model.param"), init_GUI= False, toShow= False)
        dir_fe = _mainparams[('Forced Exchanges', 'Directory')]
        fn_fe = _mainparams[('Forced Exchanges', 'Filename')]

        isOk, fe_file = check_path(os.path.join(self.directory, dir_fe, fn_fe), prefix=self.directory)
        self.couplednodesxy=[]
        self.couplednodesij=[]

        if isOk>=0:
            f = open(fe_file, 'r')
            lines = f.read().splitlines()
            f.close()

            if len(lines) > 1:

                if lines[0]=='COORDINATES':
                    for xy in enumerate(lines[1:]):
                        xy_split = xy[1].split('\t')
                        if len(xy_split)==4:
                            xup,yup,xdown,ydown=xy_split
                        else:
                            xup,yup,xdown,ydown=xy_split[:4]
                        self.couplednodesxy.append([float(xup),float(yup),float(xdown),float(ydown)])
                        self.couplednodesij.append([self.subs_array.get_ij_from_xy(float(xup),float(yup)),self.subs_array.get_ij_from_xy(float(xdown),float(ydown))])
                else:
                    logging.warning(_('Unknown format in Coupled_pairs.txt'))

        logging.info(_('Initialization of nodes...'))
        self.nodesindex = np.zeros([self.subs_array.nbx,self.subs_array.nby], dtype=int)
        self.outlet = None
        self.up = None
        self.init_nodes()

        logging.info(_('Initialization of subwatersheds...'))
        self.init_subs()

        if not crosssections is None:
            logging.info(_('Cross sections...'))
            self.crosssections = crosssections
            self.attrib_cs_to_nodes()
        else:
            self.crosssections = None

        logging.info(_('Slopes corrections...'))
        self.riversystem  = RiverSystem(self.rivers , self,thslopemin=thslopemin, thslopemax=thslopemax, computecorr=computecorr)
        self.runoffsystem = RunoffSystem(self.runoff, self,thslopemin=thslopemin, thslopemax=thslopemax, computecorr=computecorr)

        if computestats or plotstats:
            logging.info(_('Statistics...'))
            self.compute_stats(plotstats)

        #Ecriture des résultats de correction des pentes
        if computecorr:
            logging.info(_('Writing data to disk'))
            self.write_dem()
            self.write_slopes()

        if plotriversystem:
            logging.info(_('Plot rivers'))
            self.riversystem.plot_all_in_notebook()

        self.to_update_times = False

        logging.info(_('Done!'))

    @property
    def nb_subs(self):
        """ Nombre de sous-bassins """

        if self.subs_array is None:
            return 0
        if self.subs_array.array is None:
            return 0

        return int(ma.max(self.subs_array.array))

    @property
    def resolution(self):
        return self.header.dx

    # def impose_sorted_index_subbasins(self, new_idx=list[int]):
    #     """
    #     Tri des sous-bassins
    #     """

    #     for cursub in self.subcatchments:
    #         cursub._index_sorted = new_idx[cursub.index]

    def set_names_subbasins(self, new_names:list[tuple[int,str]]):
        """
        Renommage des sous-bassins
        """

        for cursub, curname in new_names:
            self.get_subwatershed(cursub).name  = curname

    def add_virtual_subwatershed(self, subwater:SubWatershed):
        """
        Ajout d'un sous-bassin virtuel
        """

        self.virtualcatchments.append(subwater)

        subwater.name += str(len(self.virtualcatchments))

    def create_virtual_subwatershed(self, outlet:Node_Watershed, excluded_nodes:list[Node_Watershed] = []):
        """
        Création d'un sous-bassin virtuel
        """

        newsub = self.get_subwatershed(outlet.sub).get_virtual_subwatershed(outlet, excluded_nodes=excluded_nodes)

        self.add_virtual_subwatershed(newsub)

        return newsub

    def get_xy_downstream_node(self,
                               starting_node:Node_Watershed,
                               limit_to_sub:bool = False):
        """
        Récupération des coordonnées du noeud aval
        """

        if limit_to_sub:
            down = starting_node.get_down_nodes_same_sub()
        else:
            down = starting_node.get_down_nodes()

        return [[cur.x, cur.y] for cur in down]

    def get_xy_upstream_node(self,
                             starting_node:Node_Watershed,
                             limit_to_sub:bool = False,
                             limit_to_river:bool = False,
                             limit_to_runoff:bool = False) -> list[list[float]]:
        """
        Récupération des coordonnées des noeuds amont
        """

        if limit_to_sub:

            if limit_to_river:
                up = starting_node.get_up_rivernodes_same_sub()
            elif limit_to_runoff:
                up = starting_node.get_up_runoff_nodes_same_sub()
            else:
                up, all_river, all_runoff = starting_node.get_up_nodes_same_sub()

        else:
            if limit_to_river:
                up = starting_node.get_up_rivernodes()
            elif limit_to_runoff:
                up = starting_node.get_up_runoff_nodes()
            else:
                up, all_river, all_runoff = starting_node.get_up_nodes()

        return [[cur.x, cur.y] for cur in up]

    def get_array_from_upstream_node(self,
                                     starting_node:Node_Watershed,
                                     limit_to_sub:bool = False):
        """
        Récupération de l'array à partir d'un noeud amont
        """

        up = self.get_xy_upstream_node(starting_node, limit_to_sub=limit_to_sub)

        xmin = min([x[0] for x in up])
        xmax = max([x[0] for x in up])
        ymin = min([x[1] for x in up])
        ymax = max([x[1] for x in up])

        newhead = header_wolf()
        newhead.dx = self.header.dx
        newhead.dy = self.header.dy

        newhead.origx = xmin - self.header.dx/2. - self.header.dx
        newhead.origy = ymin - self.header.dy/2. - self.header.dy

        newhead.nbx = int(np.ceil((xmax - xmin) / self.header.dx) + 3)
        newhead.nby = int(np.ceil((ymax - ymin) / self.header.dy) + 3)

        if newhead.nbx == 0 or newhead.nby == 0:
            logging.error(_('No upstream nodes found!'))
            return None

        newarray = WolfArray(srcheader=newhead)
        newarray.array[:,:] = 0.

        ij = newhead.xy2ij_np(up)

        newarray.array[ij[:,0], ij[:,1]] = 1.

        newarray.mask_data(0.)

        return newarray

    def get_vector_from_upstream_node(self,
                                      starting_node:Node_Watershed,
                                      limit_to_sub:bool = False):
        """ Return a vector contouring the upstream area """

        up_array = self.get_array_from_upstream_node(starting_node, limit_to_sub=limit_to_sub)

        if up_array is None:
            return None

        __, __, vect, __ = up_array.suxsuy_contour()

        vect.find_minmax()
        return vect

    def get_vector_from_xy_to_outlet(self,
                                      x:float,
                                      y:float) -> vector:

        down_to_outlet = self.get_node_from_xy(x, y)

        if down_to_outlet is None:
            logging.error(_('No node found at coordinates ({}, {})').format(x, y))
            return None

        vec_to_outlet = vector(name='Vector from ({}, {}) to outlet'.format(down_to_outlet.i, down_to_outlet.j))

        while down_to_outlet is not None:
            vec_to_outlet.add_vertex(wolfvertex(down_to_outlet.x, down_to_outlet.y, down_to_outlet.dem['dem_after_corr']))
            down_to_outlet = down_to_outlet.down

        return vec_to_outlet

    def get_subwatershed(self, idx_sorted_or_name:int | str) -> SubWatershed:
        """
        Récupération d'un sous-bassin sur base de l'index trié
        """

        if isinstance(idx_sorted_or_name, str):
            for cur_sub in self.subcatchments:
                if cur_sub.name == idx_sorted_or_name:
                    return cur_sub

            if len(self.virtualcatchments)>0:
                for cur_sub in self.virtualcatchments:
                    if cur_sub.name == idx_sorted_or_name:
                        return cur_sub

        elif isinstance(idx_sorted_or_name, int):
            for cur_sub in self.subcatchments:
                if cur_sub._index_sorted+1 == idx_sorted_or_name:
                    return cur_sub

            if len(self.virtualcatchments)>0:
                for cur_sub in self.virtualcatchments:
                    if cur_sub._index_sorted+1 == idx_sorted_or_name:
                        return cur_sub
        else:
            logging.error(_('Index must be an integer or a string!'))

        return None

    def get_node_from_ij(self, i:int,j:int) -> Node_Watershed:
        """
        Récupération d'un objet Node_Watershed sur base des indices (i,j)
        """
        shape = self.nodesindex.shape
        if i<0 or i>=shape[0]:
            return None
        if j<0 or j>=shape[1]:
            return None
        idx = self.nodesindex[i,j]
        if idx<0 or idx >= len(self.nodes):
            return None

        return self.nodes[idx]

    def get_node_from_xy(self, x:float, y:float) -> Node_Watershed:
        """
        Récupération d'un objet Node_Watershed sur base des coordonnées (x,y)
        """
        i,j = self.header.get_ij_from_xy(x,y)
        return self.get_node_from_ij(i,j)

    def write_slopes(self):
        """
        Ecriture sur disque
        """
        for curlist in LISTDEM:
            curpath=self.directory+'\\Characteristic_maps\\corrslopes\\'+curlist
            os.makedirs(curpath,exist_ok=True)
            slopes= WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basin.slope')

            ijval = np.asarray([[curnode.i, curnode.j, curnode.slopecorr[curlist]['value']]  for curnode in self.nodes])
            slopes.array[np.int32(ijval[:,0]),np.int32(ijval[:,1])]=ijval[:,2]

            slopes.filename = curpath +'\\Drainage_basin.slope_corr'
            slopes.write_all()

    def write_dem(self):
        """
        Ecriture sur disque
        """
        for curlist in LISTDEM:
            curpath=self.directory+'\\Characteristic_maps\\corrdem\\'+curlist
            os.makedirs(curpath,exist_ok=True)
            dem= WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basincorr.b')

            ijval = np.asarray([[curnode.i, curnode.j, curnode.demcorr[curlist]['value']]  for curnode in self.nodes])
            dem.array[np.int32(ijval[:,0]),np.int32(ijval[:,1])]=ijval[:,2]

            dem.filename = curpath +'\\Drainage_basincorr.b'
            dem.write_all()

    @property
    def crosssections(self):
        return self._cs

    @crosssections.setter
    def crosssections(self, value:CrossSections):
        self._cs = value

    def attrib_cs_to_nodes(self):
        """
        Attribution des sections en travers aux noeuds
        """
        if self.crosssections is not None:
            for curlist in self.crosssections:
                for namecs in curlist.myprofiles:
                    curvert:wolfvertex
                    curcs=curlist.myprofiles[namecs]

                    try:
                        curvert=curcs['bed']
                    except:
                        curvert=curlist.get_min(whichprofile=curcs)

                    i,j=self.subs_array.get_ij_from_xy(curvert.x,curvert.y)
                    curnode:Node_Watershed
                    curnode =self.nodes[self.nodesindex[i,j]]

                    if curnode.river:
                        if curnode.crosssections is None:
                            curnode.crosssections=[]
                        curnode.crosssections.append(curcs)
                        curnode.dem['crosssection']=min(curnode.dem['crosssection'],curvert.z)

    def init_nodes(self):
        """
        Initialisation des noeuds
        """

        self.nodes=[Node_Watershed() for i in range(self.subs_array.nbnotnull)]

        dem_before_corr= WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basin.b')
        dem_after_corr= WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basincorr.b')
        #Tests of the existance of the delta dem
        isOk,demdeltaFile = check_path(os.path.join(self.directory,'Characteristic_maps\\Drainage_basindiff.b'))
        if isOk<0:
            logging.error("The ...dif.b file is not present! Please check the reason or launch again the hydrological preprocessing! A Null diff matrix will then be considered for the next steps.")
            demdelta = WolfArray(mold=dem_after_corr)
            demdelta.array = 0.0
        else:
            demdelta = WolfArray(demdeltaFile)
        #
        if (Path(self.directory) / 'Characteristic_maps' /'Drainage_basin.slope').exists():
            # If the slope file exists, read it
            slopes = WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basin.slope', masknull=False)
        else:
            slopes = None
            logging.error(_('The slope file is not present! Please check the reason or launch again the hydrological preprocessing! A Null slope matrix will then be considered for the next steps.'))

        if (Path(self.directory) / 'Characteristic_maps' /'Drainage_basin.reachs').exists():
            # If the reaches file exists, read it
            reaches = WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basin.reachs')
        else:
            reaches = None
            logging.error(_('The reaches file is not present! Please check the reason or launch again the hydrological preprocessing! A Null reaches matrix will then be considered for the next steps.'))

        if (Path(self.directory) / 'Characteristic_maps' /'Drainage_basin.cnv').exists():
            # If the cnv file exists, read it
            cnv = WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basin.cnv')
        else:
            cnv = None
            logging.error(_('The cnv file is not present! Please check the reason or launch again the hydrological preprocessing! A Null cnv matrix will then be considered for the next steps.'))

        if (Path(self.directory) / 'Characteristic_maps' /'Drainage_basin.time').exists():
            # If the time file exists, read it
            times = WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basin.time')
        else:
            times = None
            logging.error(_('The time file is not present! Please check the reason or launch again the hydrological preprocessing! A Null time matrix will then be considered for the next steps.'))

        dem_after_corr.array.mask = self.subs_array.array.mask

        # Efficiently fill nodesindex using numpy where and flat indexing
        indices = np.argwhere(self.subs_array.array > 0)
        position = np.arange(len(indices))
        self.nodesindex[indices[:, 0], indices[:, 1]] = position

        def init_node(i, j):
            """ Initialisation d'un noeud
            """
            curnode:Node_Watershed
            x, y = self.header.get_xy_from_ij(i,j)
            curnode =self.nodes[self.nodesindex[i,j]]

            curnode.i = i
            curnode.j = j

            curnode.x = x
            curnode.y = y

            curnode.crosssections = None
            curnode.down = None

            curnode.index=self.nodesindex[i,j]
            curnode.dem={}
            curnode.dem['dem_before_corr']=dem_before_corr.array[i,j]
            curnode.dem['dem_after_corr']=dem_after_corr.array[i,j]
            curnode.dem['crosssection']=99999.
            curnode.demdelta=demdelta.array[i,j]
            curnode.slope=slopes.array[i,j] if slopes is not None else 0.0

            curnode.slopecorr={}
            for curlist in LISTDEM:
                curnode.slopecorr[curlist]={}
                curnode.slopecorr[curlist]['parts']=[]
                curnode.slopecorr[curlist]['value']=curnode.slope

            curnode.demcorr={}
            for curlist in LISTDEM:
                curnode.demcorr[curlist]={}
                curnode.demcorr[curlist]['parts']=[]
                curnode.demcorr[curlist]['value']=curnode.dem['dem_after_corr']

            curnode.sub=int(self.subs_array.array[i,j])
            curnode.time=times.array[i,j] if times is not None else 0.0
            curnode.uparea=cnv.array[i,j] if cnv is not None else 0.0

            if reaches is not None:
                curnode.river=not reaches.array.mask[i,j]
                if curnode.river:
                    curnode.reach=int(reaches.array[i,j])
            else:
                curnode.river=False
                curnode.reach=0

            curnode.forced=False

            curnode.up=[]
            curnode.upriver=[]
            curnode.strahler=0
            curnode.reachlevel=0
            # nb+=1

        all_init = list(map(lambda p: init_node(*p), tqdm(indices, 'Initialization')))

        curdown:Node_Watershed
        #Liaison échanges forcés
        incr=self.header.dx
        for curexch in self.couplednodesij:
            i=int(curexch[0][0])
            j=int(curexch[0][1])
            curnode=self.nodes[self.nodesindex[i,j]]
            curnode.forced=True
            idown = int(curexch[1][0])
            jdown = int(curexch[1][1])
            curdown = self.nodes[self.nodesindex[idown,jdown]]
            curnode.down = curdown
            curdown.up.append(curnode)
            if curnode.river:
                curdown.upriver.append(curnode)
            curnode.incrs = incr * np.sqrt(pow(curdown.i-i,2)+pow(curdown.j-j,2))

        #Liaison hors échanges forcés
        for curnode in tqdm(self.nodes, 'Linking'):
            if not curnode.forced:
                i=curnode.i
                j=curnode.j

                curtop=curnode.dem['dem_after_corr']

                neigh = [[i-1,j],[i+1,j],[i,j-1], [i,j+1]]
                diff = [dem_after_corr.array[curi,curj]-curtop if not dem_after_corr.array.mask[curi,curj] else 100000. for curi,curj in neigh]
                mindiff = np.min(diff)
                if mindiff<0:
                    index = diff.index(mindiff)
                    if index==0:
                        curdown = self.nodes[self.nodesindex[i-1,j]]
                    elif index==1:
                        curdown = self.nodes[self.nodesindex[i+1,j]]
                    elif index==2:
                        curdown = self.nodes[self.nodesindex[i,j-1]]
                    else:
                        curdown = self.nodes[self.nodesindex[i,j+1]]

                    curnode.down = curdown
                    curdown.up.append(curnode)
                    if curnode.river:
                        curdown.upriver.append(curnode)
                    curnode.incrs=incr
                else:
                    if self.outlet is None:
                        self.outlet = curnode

        # Recherche de la pente dans les voisins en croix dans la topo non remaniée
        import concurrent.futures

        def compute_sloped8(args):
            curnode, dem_before_corr, resolution = args
            if not curnode.forced:
                i = curnode.i
                j = curnode.j

                curtop = curnode.dem['dem_before_corr']

                neigh = [
                    [i-1, j], [i+1, j], [i, j-1], [i, j+1],
                    [i-1, j-1], [i+1, j+1], [i+1, j-1], [i-1, j+1]
                ]
                diff = [
                    dem_before_corr.array[curi, curj] - curtop
                    if not dem_before_corr.array.mask[curi, curj] else 100000.
                    for curi, curj in neigh
                ]
                mindiff = np.min(diff)

                fact = 1.
                if mindiff < 0:
                    index = diff.index(mindiff)
                    if index > 3:
                        fact = np.sqrt(2)
                return curnode, -mindiff / (resolution * fact)
            else:
                return curnode, 0.0

        # # Prepare arguments for multiprocessing
        # args_list = [(curnode, dem_before_corr, self.resolution) for curnode in self.nodes]

        # with concurrent.futures.ProcessPoolExecutor() as executor:
        #     results = list(tqdm(executor.map(compute_sloped8, args_list), total=len(args_list), desc='Finding slope'))

        # # Assign results back to nodes
        # for curnode, sloped8 in results:
        #     curnode.sloped8 = sloped8

        for curnode in tqdm(self.nodes, 'Finding slope'):
            curnode.sloped8 = compute_sloped8((curnode, dem_before_corr, self.resolution))[1]

        self.rivers=list(filter(lambda x: x.river,self.nodes))
        self.rivers.sort(key=lambda x: x.dem['dem_after_corr'])

        # FIXME : Caution the following iterative function can induce a RecursionError in Debug for bigger systems
        sys.setrecursionlimit(len(self.nodes))
        self.outlet.incr_curvi()

        self.find_dem_subpixels()

        self.runoff=self.find_runoffnodes()

    def find_rivers(self, whichsub:int=0, whichreach:int=0) -> tuple[list[Node_Watershed], Node_Watershed]:
        """
        Recherche des mailles rivières
        :param whichsub : numéro du sous-bassin à traiter
        :param whicreach : numéro du tronçon à identifier
        """
        if whichsub>0 and whichsub<=self.nb_subs:
            if whichreach>0:
                myrivers=list(filter(lambda x: x.river and x.sub==whichsub and x.reach==whichreach,self.rivers))
            else:
                myrivers=list(filter(lambda x: x.river and x.sub==whichsub,self.rivers))
        else:
            if whichreach>0:
                myrivers=list(filter(lambda x: x.river and x.reach==whichreach,self.rivers))
            else:
                myrivers=list(filter(lambda x: x.river,self.rivers))

        myrivers.sort(key=lambda x: x.dem['dem_after_corr'])

        up=None
        if len(myrivers)>0:
            up=myrivers[-1]

        return myrivers,up

    def find_sub(self, whichsub:int=0) -> list[Node_Watershed]:
        """
        Recherche des mailles du sous-bassin versant
        :param whichsub : numéro du sous-bassin à traiter
        """
        if whichsub>0 and whichsub<=self.nb_subs:
            mysub=list(filter(lambda x: x.sub==whichsub, self.nodes))
        else:
            mysub=self.nodes.copy()

        mysub.sort(key=lambda x: x.dem['dem_after_corr'])

        return mysub

    def init_subs(self):
        """
        Initialize Sub-Catchments
        """
        self.subcatchments=[]

        #Initialisation de la matrice de mask (d'une extension et d'une résolution similaire aux données radar)
        for i in tqdm(range(1,self.nb_subs+1), 'Subwatershed'):
            curmask = WolfArray(mold=self.subs_array)
            curmask.mask_allexceptdata(float(i))
            all_river_nodes, _ = self.find_rivers(i)

            cursub = SubWatershed(self,
                                  name = 'sub n'+str(i),
                                  idx=i-1,
                                  mask = curmask,
                                  nodes = self.find_sub(i),
                                  runoff=self.find_runoffnodes(i),
                                  rivers=all_river_nodes,
                                  )

            self.subcatchments.append(cursub)

    def find_runoffnodes(self, whichsub:int=0) -> list[Node_Watershed]:
        """
        Recherche des mailles du bassin versant seul (sans les rivières)
        :param whichsub : numéro du sous-bassin à traiter
        """
        if whichsub>0 and whichsub<=self.nb_subs:
            myrunoff=list(filter(lambda x: not x.river and x.sub==whichsub,self.nodes))
        else:
            myrunoff=list(filter(lambda x: not x.river,self.nodes))

        myrunoff.sort(key=lambda x: x.dem['dem_after_corr'])

        return myrunoff

    def index_flatzone(self, listofsortednodes:list, threshold:float):
        """
        Indexation des zones de plat
        """

        curnode:Node_Watershed
        curflat:Node_Watershed

        curindex=0
        for curnode in listofsortednodes[-1:1:-1]:
            addone=False
            while curnode.slope<threshold and curnode.flatindex==-1:
                addone=True
                curnode.flatindex=curindex
                if curnode.down is None:
                    break
                curnode=curnode.down
            if addone:
                curindex+=1

        return curindex

    def find_flatnodes(self, listofsortednodes:list):
        """
        Recherche des mailles dans des zones de faibles pentes
        :param listofsortednodes : liste triée de mailles
        """
        myflatnodes=list(filter(lambda x: x.flatindex>-1,listofsortednodes))

        return myflatnodes

    def find_flatzones(self, listofsortednodes:list, maxindex:int):
        """
        Recherche des mailles dans des zones de faibles pentes
        :param listofsortednodes : liste triée de mailles
        """
        myflatzones=[[]] * maxindex
        for i in range(maxindex):
            myflatzones[i]=list(filter(lambda x: x.flatindex==i,listofsortednodes))

        return myflatzones

    def find_dem_subpixels(self):
        """
        Recherche des altitudes dans un mnt plus dense
        """
        demsubs = {}

        file_10m = os.path.join(self.dir_mnt_subpixels,'mnt10m.bin')
        isOk, file_10m = check_path(file_10m, prefix=self.directory)
        if isOk>=0:
            dem_10m=WolfArray(file_10m)
            demsubs["dem_10m"] = dem_10m
        else:
            logging.warning(_('No 10m DEM found'))

        file_20m = os.path.join(self.dir_mnt_subpixels,'mnt20m.bin')
        isOk, file_20m = check_path(file_20m, prefix=self.directory)
        if isOk>=0:
            dem_20m=WolfArray(file_20m)
            demsubs["dem_20m"] = dem_20m
        else:
            logging.warning(_('No 20m DEM found'))

        # demsubs={'dem_10m':dem_10m,'dem_20m':dem_20m}
        if len(demsubs)==0:
            logging.info(_('No subpixel DEM found'))
            return

        curnode:Node_Watershed
        for curdem in tqdm(demsubs, 'Sub-pixeling'):
            locdem=demsubs[curdem]
            dx=locdem.dx
            dy=locdem.dy

            for curnode in tqdm(self.nodes):
                curi=curnode.i
                curj=curnode.j

                curx,cury=self.subs_array.get_xy_from_ij(curi,curj)

                decalx=(self.resolution-dx)/2.
                decaly=(self.resolution-dy)/2.
                x1=curx-decalx
                y1=cury-decaly
                x2=curx+decalx
                y2=cury+decaly

                i1,j1=locdem.get_ij_from_xy(x1,y1)
                i2,j2=locdem.get_ij_from_xy(x2,y2)

                curnode.dem[curdem]=np.min(locdem.array[i1:i2+1,j1:j2+1])

    def compute_stats(self, plot:bool=False):
        """
        Calcul des statistiques de pente
        """
        self.statisticss={}

        slopes=np.array(list(x.slope for x in self.nodes))
        slopesrunoff=np.array(list(x.slope for x in list(filter(lambda x: not x.river,self.nodes))))
        slopesriver=np.array(list(x.slope for x in list(filter(lambda x: x.river,self.nodes))))

        curdict=self.statisticss
        curdict['slopemin'] = np.min(slopes)
        curdict['slopemax'] = np.max(slopes)
        curdict['slopemedian'] = np.median(slopes)
        curdict['slopemean'] = np.mean(slopes)
        curdict['hist'] = slopes
        curdict['hist_watershed'] = slopesrunoff
        curdict['hist_reaches'] = slopesriver
        curdict['count_neg'] = np.count_nonzero(slopes < 0.)

        logging.info(_('Min : {}'.format(curdict['slopemin'])))
        logging.info(_('Max : {}'.format(curdict['slopemax'])))
        logging.info(_('Median : {}'.format(curdict['slopemedian'])))
        logging.info(_('Mean : {}'.format(curdict['slopemean'])))
        logging.info(_('Non Zero : {}'.format(curdict['count_neg'])))

        for curlist in LISTDEM:
            curdict=self.statisticss[curlist]={}

            slopes=np.array(list(x.slopecorr[curlist]['value'] for x in self.nodes))
            slopesrunoff=np.array(list(x.slopecorr[curlist]['value'] for x in list(filter(lambda x: not x.river,self.nodes))))
            slopesriver=np.array(list(x.slopecorr[curlist]['value'] for x in list(filter(lambda x: x.river,self.nodes))))

            curdict['slopemin'] = np.min(slopes)
            curdict['slopemax'] = np.max(slopes)
            curdict['slopemedian'] = np.median(slopes)
            curdict['slopemean'] = np.mean(slopes)
            curdict['hist'] = slopes
            curdict['hist_watershed'] = slopesrunoff
            curdict['hist_reaches'] = slopesriver
            curdict['count_neg'] = np.count_nonzero(slopes < 0.)

            logging.info(_('Current list : '.format(curlist)))
            logging.info(_('Min : {}'.format(curdict['slopemin'])))
            logging.info(_('Max : {}'.format(curdict['slopemax'])))
            logging.info(_('Median : {}'.format(curdict['slopemedian'])))
            logging.info(_('Mean : {}'.format(curdict['slopemean'])))
            logging.info(_('Non Zero : {}'.format(curdict['count_neg'])))

        if plot:
            self.plot_stats()

    def plot_stats(self):

        self.myplotterstats = PlotNotebook()

        bin1=np.array([1.e-8,1.e-7,1.e-6,5.e-6])
        bin2=np.linspace(1.e-5,1e-3,num=20)
        bin3=np.linspace(2.e-3,1e-1,num=20)
        bin4=np.linspace(.11,1,num=100)
        bins=np.concatenate((bin1,bin2,bin3,bin4))

        fig=self.myplotterstats.add(_('Slope distribution - log'))

        ax = fig.add_ax()
        ax.hist(self.statisticss['hist'],bins,cumulative=True,density=True,histtype=u'step',label='base')
        ax.set_xscale('log')
        ax.set_xlabel(_('All meshes'))

        for curlist in LISTDEM:
            curdict=self.statisticss[curlist]
            ax.hist(curdict['hist'],bins,cumulative=True,density=True,histtype=u'step',label=curlist)

        ax = fig.add_ax()
        ax.hist(self.statisticss['hist_watershed'],bins,cumulative=True,density=True,histtype=u'step',label='base')
        ax.set_xscale('log')
        ax.set_xlabel(_('Watershed'))

        for curlist in LISTDEM:
            curdict=self.statisticss[curlist]
            ax.hist(curdict['hist_watershed'],bins,cumulative=True,density=True,histtype=u'step',label=curlist)

        ax = fig.add_ax()
        ax.hist(self.statisticss['hist_reaches'],bins,cumulative=True,density=True,histtype=u'step',label='base')
        ax.set_xscale('log')
        ax.set_xlabel(_('River'))

        for curlist in LISTDEM:
            curdict=self.statisticss[curlist]
            ax.hist(curdict['hist_reaches'],bins,cumulative=True,density=True,histtype=u'step',label=curlist)

        ax.legend()
        fig.canvas.draw()

        fig=self.myplotterstats.add(_('Slope distribution'))
        ax:plt.axis

        ax = fig.add_ax()
        ax.hist(self.statisticss['hist'],bins,cumulative=True,density=True,histtype=u'step',label='base')
        ax.set_xlabel(_('All meshes'))

        for curlist in LISTDEM:
            curdict=self.statisticss[curlist]
            ax.hist(curdict['hist'],bins,cumulative=True,density=True,histtype=u'step',label=curlist)

        ax = fig.add_ax()
        ax.hist(self.statisticss['hist_watershed'],bins,cumulative=True,density=True,histtype=u'step',label='base')
        ax.set_xlabel(_('Watershed'))

        for curlist in LISTDEM:
            curdict=self.statisticss[curlist]
            ax.hist(curdict['hist_watershed'],bins,cumulative=True,density=True,histtype=u'step',label=curlist)

        ax = fig.add_ax()
        ax.hist(self.statisticss['hist_reaches'],bins,cumulative=True,density=True,histtype=u'step',label='base')
        ax.set_xlabel(_('River'))

        for curlist in LISTDEM:
            curdict=self.statisticss[curlist]
            ax.hist(curdict['hist_reaches'],bins,cumulative=True,density=True,histtype=u'step',label=curlist)

        ax.legend()
        fig.canvas.draw()

    def analyze_flatzones(self):
        """
        Analyse des zones de plat
        """
        self.myplotterflat = PlotNotebook()

        ### Flat zones
        eps=1e-7
        #indexation des zones "indépendantes" de plats - ruissellement
        maxindex=self.index_flatzone(self.runoff,eps)
        #identification des mailles dans les zones
        myflatnodes=self.find_flatnodes(self.runoff)
        #création de listes avec les noeuds dans chaque zone
        myflats=self.find_flatzones(myflatnodes,maxindex)

        #calcul de la longueur de la zone de plat --> sommation du nombre de mailles
        lenflats=np.zeros((maxindex),dtype=np.int32)
        for i in range(maxindex):
            lenflats[i]=len(myflats[i])

        #indexation des zones "indépendantes" de plats - rivières
        maxindexrivers=self.index_flatzone(self.rivers,eps)
        #création de listes avec les noeuds dans chaque zone - rivières
        myflatsrivers=self.find_flatzones(self.rivers,maxindexrivers)

        #calcul de la longueur de la zone de plat --> sommation du nombre de mailles
        lenflatsrivers=np.zeros((maxindexrivers),dtype=np.int32)
        for i in range(maxindexrivers):
            lenflatsrivers[i]=len(myflatsrivers[i])

        fig:mplfig.Figure
        fig=self.myplotterflat.add("Nb nodes in flat area")
        ax=fig.add_ax()
        mybins=np.arange(0.5,np.max(lenflats),1.)
        myticks=np.arange(1,np.ceil(np.max(lenflats)),1)
        ax.hist(lenflats,bins=mybins)
        ax.set_xlabel(_('Nb nodes in flat area - runoff'))
        ax.set_xticks(myticks)
        ax.set_xbound(.5,np.max(lenflats))
        ax.set_ylabel('Nb flat areas')
        ax.set_yscale('log')

        ax=fig.add_ax()
        mybinsrivers=np.arange(0.5,np.max(lenflatsrivers),1.)
        myticksrivers=np.arange(1,np.ceil(np.max(lenflatsrivers)),1)
        ax.hist(lenflatsrivers,bins=mybinsrivers)
        ax.set_xlabel(_('Nb nodes in flat area - rivers'))
        ax.set_xticks(myticksrivers)
        ax.set_xbound(.5,np.max(lenflatsrivers))
        ax.set_ylabel('Nb flat areas')
        ax.set_yscale('log')

        fig=self.myplotterflat.add("Nb nodes in flat area")
        ax=fig.add_ax()
        ax.hist(lenflats,bins=mybins,cumulative=True,density=True)
        ax.set_xlabel(_('Nb nodes in flat area - runoff'))
        ax.set_xticks(myticks)
        ax.set_xbound(.5,np.max(lenflats))
        ax.set_ylabel('Cumulative flat areas')
        #ax.set_yscale('log')

        ax=fig.add_ax()
        ax.hist(lenflatsrivers,bins=mybinsrivers,cumulative=True,density=True)
        ax.set_xlabel(_('Nb nodes in flat area - rivers'))
        ax.set_xticks(myticksrivers)
        ax.set_xbound(.5,np.max(lenflatsrivers))
        ax.set_ylabel('Cumulative flat areas')
        #ax.set_yscale('log')
        fig.canvas.draw()

        #Tri des pentes dans différentes listes

        #toutes les mailles
        sdown=[]
        sup=[]
        for curflat in myflats:
            for curnode in curflat:
                #recherche de la pente aval plus grande que le seuil
                sdown.append(curnode.slope_down(eps))
                #recherche de la pente amont moyenne - uniquement pour les mailles qui ont une pente supérieure au seuil
                sup.append(curnode.mean_slope_up(eps))

        sflat=[]
        sdownraw=[]
        for curflat in myflats:
            for curnode in curflat:
                #pente de la maille aval
                sdownraw.append(curnode.down.slope)
                #pente courante
                sflat.append(curnode.slope)

        #mailles rivières
        sdownriv=[]
        supriv=[]
        suponlyriv=[]
        for curflat in myflatsrivers:
            for curnode in curflat:
                #recherche de la pente aval plus grande que le seuil
                sdownriv.append(curnode.slope_down(eps))
                #recherche de la pente amont moyenne - uniquement pour les mailles qui ont une pente supérieure au seuil
                supriv.append(curnode.mean_slope_up(eps))
                #recherche de la pente amont > seuil
                suponlyriv.append(curnode.slope_upriver(eps))

        sdownd8=[]
        suponlyriv1=[]
        for curflat in myflatsrivers:
            for curnode in curflat:
                #pente aval selon voisines D8
                sdownd8.append(curnode.sloped8)
                #recherche de la pente amont > seuil
                suponlyriv1.append(curnode.slope_upriver(eps))

        sflatriver=[]
        sdownrawriver=[]
        sd8rawriver=[]
        for curflat in myflatsrivers:
            if len(curflat)==1:
                for curnode in curflat:
                    if not curnode.down is None:
                        sd8rawriver.append(curnode.sloped8)
                        sdownrawriver.append(curnode.down.slope)
                        sflatriver.append(curnode.slope)


        #tracage des graphiques
        fig=self.myplotterflat.add("Scatter plots")
        ax=fig.add_ax()
        ax.scatter(sdownrawriver,sflatriver,marker='o',label='slope down vs flat slope')
        ax.scatter(sdownriv,suponlyriv,marker='+',label='slope down vs slope d8')
        ax=fig.add_ax()
        ax.scatter(sdownraw,sflat,marker='0',label='slope down vs flat slope')
        ax.scatter(sdown,sup,marker='+',label='slope down vs slope up')
        fig.canvas.draw()

        fig=self.myplotterflat.add("Scatter plots 2")
        curax=fig.add_ax()
        curax.scatter(sdown,sup,marker='+')
        curax.set_xlabel(_('Slope down [-]'))
        curax.set_ylabel(_('Mean slope up [-]'))
        curax.set_aspect('equal','box')
        curax.set_xbound(0,.55)
        curax.set_ybound(0,.55)
        curax.set_title('Runoff')

        curax=fig.add_ax()
        curax.scatter(sdownriv,supriv,marker='+')
        curax.set_xlabel(_('Slope down [-]'))
        curax.set_ylabel(_('Mean slope up [-]'))
        curax.set_aspect('equal','box')
        curax.set_xbound(0,.55)
        curax.set_ybound(0,.55)
        curax.set_title('River')

        curax=fig.add_ax()
        curax.scatter(sdownriv,suponlyriv,marker='+')
        curax.set_xlabel(_('Slope down [-]'))
        curax.set_ylabel(_('Slope up only river [-]'))
        curax.set_aspect('equal','box')
        curax.set_xbound(0,.55)
        curax.set_ybound(0,.55)
        curax.set_title('River')

        curax=fig.add_ax()
        curax.scatter(sdownd8,suponlyriv1,marker='+')
        curax.set_xlabel(_('Slope D8 [-]'))
        curax.set_ylabel(_('Slope up only river [-]'))
        curax.set_aspect('equal','box')
        curax.set_xbound(0,.3)
        curax.set_ybound(0,.3)
        curax.set_title('River')
        fig.canvas.draw()

    def update_times(self, wolf_time=None):

        if wolf_time is None:
            wolf_time = WolfArray(self.directory+'\\Characteristic_maps\\Drainage_basin.time')

        for cur_node in self.nodes:
            cur_node.time = wolf_time[cur_node.i, cur_node.j]

        self.to_update_times = False

    def get_subwatershed_from_ij(self, i:int, j:int) -> SubWatershed:
        """
        Récupération d'un sous-bassin sur base des indices (i,j)

        :return: SubWatershed : sous-bassin or None
        """

        if self.subs_array.array.mask[i,j]:
            return None

        idx_sub = self.subs_array.array[i,j]

        return self.subcatchments[idx_sub-1]

    def get_subwatershed_from_xy(self, x:float, y:float) -> SubWatershed:
        """
        Récupération d'un sous-bassin sur base des coordonnées (x,y)

        :return: SubWatershed : sous-bassin or None
        """

        i,j = self.header.get_ij_from_xy(x,y)
        return self.get_subwatershed_from_ij(i,j)

    def get_subwatershed_from_vector(self, vec:vector) -> tuple[SubWatershed, bool, list[SubWatershed]]:
        """
        Récupération d'un sous-bassin sur base d'un vecteur.

        Recherche sur base du centroid du vecteur

        :param vec: vecteur

        :return: tuple(SubWatershed, bool, list[SubWatershed]) : sous-bassin, entièrement dans le sous-bassin, autres sous-bassins
        """

        centroid = vec.centroid

        sub = self.get_subwatershed_from_xy(centroid.x, centroid.y)

        entirely = True
        others = []
        for curvert in vec.myvertices:
            cursub = self.get_subwatershed_from_xy(curvert.x, curvert.y)
            if cursub is not None and cursub != sub:
                logging.warning(_('The vector is not entirely in the same subcatchment'))
                entirely = False
                others.append(cursub)

        return sub, entirely, others