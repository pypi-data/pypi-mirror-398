
"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os.path import exists, join
import json
from enum import Enum
from typing import Literal
from concurrent.futures import ThreadPoolExecutor
import logging
from pathlib import Path
from typing import Union

from .PyParams import Wolf_Param, key_Param
from .PyVertexvectors import Zones, vector, zone
from .PyPalette import wolfpalette
from .PyTranslate import _
from .wolfresults_2D import Wolfresults_2D, views_2D
from .Results2DGPU import wolfres2DGPU

class project_type(Enum):
    GENERIC = 0
    WOLF2D  = 1

class Project(Wolf_Param):
    """
    Projet WOLF

    Il s'agit d'une surcharge d'un objet Wolf_Param qui est organisé en groupes de paramètres
    Chaque paramètre peut être défini par une clé, une valeur et un commentaire (+ éventuellement une chaîne JSON)
    """
    def __init__(self, 
                 wdir='', 
                 parent=None, 
                 title="Default Title", 
                 w=500, h=800, 
                 ontop=False, 
                 to_read=True, 
                 filename='', 
                 withbuttons=True, 
                 DestroyAtClosing=True, 
                 toShow=True,
                 init_GUI:bool = False,
                 force_even_if_same_default:bool = False):
        
        super().__init__(parent, title, w, h, ontop, to_read, filename, withbuttons, DestroyAtClosing, toShow, init_GUI, force_even_if_same_default)
        self.wdir = wdir

class Wolf2D_Project(Project):
    """
    Projet d'analyse de simulations WOLF2D

    Ce projet contient a priori :
        - une liste de simulations  (groupe "wolf2d", "gpu2d")
        - une liste de vecteurs/polylignes afin de restreindre la zone d'analyse et éviter
            autant que possible la superposition des modèles (groupe "vectors")
        - la liaison entre polyligne et modèle (groupe "vector_array_link")
        - des palettes (groupe "palette")
        - la liaison des palettes avec les modèles (groupe "palette-array")

    Chaque simulation est associée à une clé unique
    Chaque vecteur est associé à une clé unique
    Chaque palette est associée à une clé unique

    Les liaisons simulation-vecteur se font par (clé-valeur) = (sim-vector)
    Les liaisons simulation-palette se font par (clé-valeur) = (sim-palette)

    Exemple :

    wolf2d:
    Confluence Wayai - Forges Thiry_B	.\Q25\X1b - Hoegne - Tr 3 - Confluence Wayai - Forges Thiry\simul
    Confluence Wayai - Forges Thiry_A	.\Q25\X1a - Hoegne - Tr 3 - Confluence Wayai - Forges Thiry\simul
    vector:
    polyd5	..\Vecteurs\161 - Vesdre - Tr 3 - Chaudfontaine - Confluence Ourthe\cont_sauv.vec
    polyd4	..\Vecteurs\162 - Vesdre - Tr 3 - Prayon - Chaudfontaine\cont_sauv.vec
    vector_array_link:
    Confluence Wayai - Forges Thiry_B	polyX1
    Confluence Wayai - Forges Thiry_A	polyX1
    palette:
    Q25	q25_alea.pal
    Q50	q50_alea.pal
    Q100	q100_alea.pal
    palette-array:
    Confluence Wayai - Forges Thiry_B	Q25
    Confluence Wayai - Forges Thiry_A	Q25
    """

    def __init__(self, wdir='', parent=None, title="Default Title", w=500, h=800, ontop=False, to_read=True, filename='', withbuttons=True, DestroyAtClosing=True, toShow=False):
        super().__init__(wdir, parent, title, w, h, ontop, to_read, filename, withbuttons, DestroyAtClosing, toShow)

        self.mysims:dict[str,Union[Wolfresults_2D, wolfres2DGPU]]={}
        
        self.mycontours={}
        self.mycolormaps={}
        self.epsilon=5e-4

        self.poly = None
        self.poly_values = None

    @classmethod
    def from_existing(cls, sims:dict[str, Union[str, Wolfresults_2D, wolfres2DGPU]]):
        """
        Create a MultiProjects object from a dictionary of simulations

        :param sims: dict[str, Union[str, Wolfresults_2D, wolfres2DGPU]] -- dictionary of simulations to add
        """

        newmp = cls(to_read=False)
        newmp.add_simulations(sims)

        return newmp

    def __str__(self) -> str:
        """
        Return string representation
        """

        ret = f'Project : {Path(self.wdir)}\n'
        ret += 'Key : Simulations : Type\n'
        for curkey, cursim in self.mysims.items():
            ret+=f'{curkey} : {cursim.filename} : {"GPU" if isinstance(cursim, wolfres2DGPU) else "CPU"}\n'

        return ret
    
    def __getitem__(self, key: tuple[str, str]):
        
        return self.get_simulation(key)

    def pop(self, key: str):
        """
        Remove a simulation from the project

        :param key: str -- key of the simulation to remove
        """

        if key in self.mysims.keys():
            self.mysims.pop(key)
    
    def add(self, 
            key:str, 
            value:Union[Wolfresults_2D, wolfres2DGPU, str], 
            epsilon:float=None, 
            force_read:bool = False):
        """
        Add a key-value pair to the project

        :param key: str -- key of the simulation to add
        :param value: Wolfresults_2D, wolfres2DGPU, str -- simulation to add
        :param epsilon: float -- epsilon value to use for the simulation
        :param force_read: bool -- force reading the last step of the simulation

        """

        if epsilon is  None:
            epsilon = self.epsilon

        if isinstance(value, str):
            
            locpath = Path(self.wdir) / value
            if locpath.exists():

                if 'simul_gpu_results' in locpath.name or (locpath / 'simul_gpu_results').exists():
                    #GPU
                    self.mysims[key] = wolfres2DGPU(locpath, epsilon=self.epsilon, idx=key)
                else:
                    #CPU
                    self.mysims[key] = Wolfresults_2D(locpath, epsilon=self.epsilon, idx=key)

            else:
                logging.warning(f'File {locpath} does not exist !')

        elif isinstance(value, wolfres2DGPU):

            self.mysims[key] = value

        elif isinstance(value, Wolfresults_2D):
                
            self.mysims[key] = value

        if force_read:
            self.mysims[key].read_oneresult()
            
    def add_simulations(self, 
                        sims_to_add:dict[str, Union[str, Wolfresults_2D, wolfres2DGPU]],
                        epsilon:float=None, 
                        force_read:bool = False):
        """
        Add multiple simulations to the project

        :param sims_to_add: dict[str, Union[str, Wolfresults_2D, wolfres2DGPU]] -- dictionary of simulations to add
        """

        for key, value in sims_to_add.items():
            self.add(key, value, epsilon, force_read)

    def load_simulations(self, epsilon:float, verbose:bool=False):
        """
        Load all simulations in current project
        """
        self.epsilon = epsilon
        sims_wolf2d = self.get_group('wolf2d')

        if sims_wolf2d is not None:

            for key,val in sims_wolf2d.items():
                if verbose:
                    print(key)
                    logging.info(f'Loading simulation {key} : {val[key_Param.VALUE]}')

                cursim = self.mysims[key] = Wolfresults_2D(join(self.wdir, val[key_Param.VALUE]), eps=epsilon, idx=key)
                cursim.plotted=True

        sims_gpu2d = self.get_group('gpu2d')

        if sims_gpu2d is not None:
            for key,val in sims_gpu2d.items():
                if verbose:
                    print(key)
                    logging.info(f'Loading simulation {key} : {val[key_Param.VALUE]}')

                cursim = self.mysims[key] = wolfres2DGPU(Path(join(self.wdir, val[key_Param.VALUE])), eps=epsilon, idx=key)
                cursim.plotted=True

        self.set_vectors()
        self.set_colormap()

        if sims_wolf2d is not None:
            for key,val in sims_wolf2d.items():
                cursim = self.mysims[key]
                cursim.read_oneresult()

        if sims_gpu2d is not None:
            for key,val in sims_gpu2d.items():
                cursim = self.mysims[key]
                cursim.read_oneresult()

    def update_simulations(self, epsilon, verbose=False):
        """
        update all simulations in current project
        """
        self.epsilon = epsilon

        for cursim in self.mysims.values():
            cursim.read_oneresult()

    def get_simulation(self, key:Union[str,int]) -> Union[Wolfresults_2D, wolfres2DGPU]:
        """
        Get simulation by key

        :param key: str or int -- key of the simulation to get or index of the simulation to get
        """

        if isinstance(key,int):
            if key >=0 and key <len(self.mysims):
                return self.mysims[self.mysims.keys()[key]]

        elif isinstance(key,str):
            if key in self.mysims.keys():
                return self.mysims[key]

        return None
    
    def get_simulations(self) -> list:
        """
        Return a python list of simulations
        """
        return list(self.mysims.values())

    def set_vectors(self):
        """
        Lie les vecteurs d'un fichier projet et leur liaison potentielle avec les matrices
        """

        vec = self.get_group('vector')
        if vec is  None:
            return

        for curkey,curvec in vec.items():

            filename=''
            if exists(curvec[key_Param.VALUE]):
                filename = curvec
            elif exists(join(self.wdir,curvec[key_Param.VALUE])):
                filename = join(self.wdir,curvec[key_Param.VALUE])

            if filename!='':
                self.mycontours[curkey] = Zones(filename)

        links = self.get_group('vector_array_link')
        if links is not None:
            for curid, curname in links.items():

                locvec = None
                cursim = None

                if curname[key_Param.VALUE] in self.mycontours.keys():
                    locvec = self.mycontours[curname[key_Param.VALUE]]

                if curid in self.mysims.keys():
                    cursim = self.mysims[curid]

                if locvec is not None and cursim is not None:
                    cursim:Wolfresults_2D
                    cursim.linkedvec = locvec.myzones[0].myvectors[0]

    def set_colormap(self):
        """
        Lie les palettes d'un fichier projet et leur liaison potentielle avec les matrices
        """

        pals = self.get_group('palette')
        if pals is None:
            return

        for curid, curname in pals.items():
            filename=''
            if exists(curname[key_Param.VALUE]):
                filename = curname[key_Param.VALUE]
            elif exists(join(self.wdir, curname[key_Param.VALUE])):
                filename=join(self.wdir, curname[key_Param.VALUE])

            if filename!='':
                mypal = wolfpalette(None, '')
                mypal.readfile(filename)
                mypal.automatic = False

                self.mycolormaps[curid] = mypal

        palsarrays = self.get_group('palette-array')
        if palsarrays is not None:
            for curid, curname in palsarrays.items():
                if curname[key_Param.VALUE] in self.set_colormap.keys():
                    if curid in self.mysims.keys():
                        curarray = self.mysims[curid]
                        mypal = self.mycolormaps[curname[key_Param.VALUE]]
                        curarray.mypal = mypal
                        curarray.mypal.automatic = False

    def set_currentview(self, which):
        """
        Change le mode de vue dans une vue possible de "views_2D"
        """

        if which in views_2D:
            with ThreadPoolExecutor() as executor:
                for cursim in self.mysims.values():
                    executor.submit(cursim.set_currentview, which)

    def find_values_inside(self, zonepoly:zone):
        """
        Récupère les valeurs à l'intérieur d'une zone de polygones

        Retour :
         - dictionnaire dont la clé est l'index du polygone dans la zone
         - chaque entrée est un dictionnaire dont la clé 'values' contient une liste pour chaque matrice du projet
         - chaque élément de liste est un tuple contenant toutes les valeurs utiles
        """

        self.poly = zonepoly
        self.poly_values = zonepoly.get_all_values_linked_polygon(self.get_simulations())

    def get_values(self,which_type:Union[views_2D, Literal['i','j','block']]=None):

        if self.poly_values is None:
            raise Warning(_('Firstly call get_values_inside with a zone as argument -- Retry !'))

        simslist = list(self.mysims.keys())

        values = {}

        def fillin(pos1,pos2):
            for idx,curpoly in enumerate(self.poly_values.values()):
                curarrays = curpoly['values']

                create=False
                for curarray in curarrays:
                    if len(curarray)>0:
                        create=True
                if create:
                    locdict = values[idx]={}
                    for idarray, curarray in enumerate(curarrays):
                        if len(curarray)>0:
                            vallist=[curval[pos1][pos2] for curval in curarray]
                            locdict[simslist[idarray]] = vallist

        pos02 = [views_2D.WATERDEPTH,
               views_2D.QX,
               views_2D.QY,
               views_2D.UX,
               views_2D.UY,
               views_2D.UNORM,
               views_2D.FROUDE,
               views_2D.WATERLEVEL,
               views_2D.TOPOGRAPHY]

        pos12 = ['i','j','block']

        if which_type in pos02:
            fillin(0, pos02.index(which_type))
            return values
        elif which_type in pos12:
            fillin(1, pos02.index(which_type))
            return values
        else:
            return None

class MultiProjects():
    """Manager of multiple project files"""

    def __init__(self, wdir='') -> None:

        self.projects:dict[str, Wolf2D_Project]={}
        self.wdir=wdir

    def __getitem__(self, key:Union[str,int]) -> Project:
        """
        Get project by key
        """

        return self.get_project(key)
    
    def get_one_simulation(self, key_project:str, key_sim:str) -> Union[Wolfresults_2D, wolfres2DGPU]:
        """
        Get one simulation by key in a project
        """

        if key_project in self.projects.keys():
            return self.projects[key_project].get_simulation(key_sim)

        return None

    def get_same_simulation_in_projects(self, key_sim:str) -> dict[str, Union[Wolfresults_2D, wolfres2DGPU]]:
        """
        Get simulation by key in all projects
        """

        allsims = {}
        for curkey, curproj in self.projects.items():
            cursim = curproj.get_simulation(key_sim)
            if cursim is not None:
                allsims[curkey + ' - ' + key_sim] = cursim

        return allsims

    def __str__(self) -> str:
        """
        Return string representation
        """

        ret = 'Key : Directory\n'
        for curkey,curproj in self.projects.items():
            ret+=f'{curkey} : {Path(curproj.wdir)}\n'

        return ret

    def add(self, project:Project, key=str, whichtype=project_type.GENERIC):
        """
        Add project to dict
        """

        if isinstance(project,str):
            if exists(project):
                pass
            elif exists(join(self.wdir,project)):
                project = join(self.wdir,project)

            if whichtype == project_type.GENERIC:
                project = Project(wdir=self.wdir, to_read=True, filename=project)
            elif whichtype == project_type.WOLF2D:
                project = Wolf2D_Project(wdir=self.wdir, to_read=True, filename=project)

        self.projects[key]=project

    def get_project(self, key) -> Project:
        """
        Récupération d'un projet sur base du nom ou d'une position
        """

        if isinstance(key,int):
            if key >=0 and key <len(self.projects):
                return self.projects[self.projects.keys()[key]]

        elif isinstance(key,str):
            if key in self.projects.keys():
                return self.projects[key]

        return None
    
    def read(self, filepath:str):
        """
        Read from file
        """

        if exists(filepath):
            with open(filepath,'r') as f:
                self.projects = json.load(f)

    def save(self, filepath:str):
        """
        Write to file
        """

        with open(filepath,'w') as f:
            json.dump(self.projects,f)

    def load_simulations(self, epsilon, verbose=False):
        """
        Load all simulations in projects
        """

        for keyp,valp in self.projects.items():
            print(keyp)
            valp.load_simulations(epsilon, verbose)

    def update_simulations(self, epsilon, verbose=False):
        """
        Update all simulations in projects
        """

        for keyp,valp in self.projects.items():
            print(keyp)
            valp.update_simulations(epsilon, verbose)

    def get_simulations_list(self, which_project:Union[str, list[str]]=None) -> list:
        """
        Return a python list of simulations

        :param which_project: str or list of str -- key(s) of the project(s) to get simulations from
        """

        if which_project is None:
            allsims=[]
            for curproj in self.projects.values():
                if isinstance(curproj, Wolf2D_Project):
                    allsims+=curproj.get_simulations()
            return allsims

        elif isinstance(which_project, list):
            allsims=[]
            for curkey in which_project:
                if curkey in self.projects.keys():
                    curproj = self.projects[curkey]
                    if isinstance(curproj, Wolf2D_Project):
                        allsims+=curproj.get_simulations()
            return allsims

        elif which_project in self.projects.keys():
            curproj = self.projects[which_project]
            if isinstance(curproj, Wolf2D_Project):
                return curproj.get_simulations()

        return None

    def get_simulations_dict(self, which_project:Union[str, list[str]]=None) -> dict:
        """
        Return a python dict of simulations

        :param which_project: str or list of str -- key(s) of the project(s) to get simulations from
        """

        if which_project is None:
            allsims={}
            for curkey, curproj in self.projects.items():
                if isinstance(curproj, Wolf2D_Project):
                    allsims[curkey] = curproj.get_simulations()
            return allsims

        elif isinstance(which_project, list):
            allsims={}
            for curkey in which_project:
                if curkey in self.projects.keys():
                    curproj = self.projects[curkey]
                    if isinstance(curproj, Wolf2D_Project):
                        allsims[curkey] = curproj.get_simulations()
            return allsims

        elif which_project in self.projects.keys():
            curproj = self.projects[which_project]
            if isinstance(curproj, Wolf2D_Project):
                return {which_project: curproj.get_simulations()}

        return None

    def set_currentview(self, which:views_2D):
        """ Change le mode de vue dans une vue possible de 'views_2D' """

        for curproj in self.projects.values():
            if isinstance(curproj, Wolf2D_Project):
                curproj.set_currentview(which)

    def find_values_inside(self, zonepoly:zone, which_project=None):
        """
        Récupère les valeurs à l'intérieur d'une zone de polygones
        """

        if which_project is None:
            for curkey,curproj in self.projects.items():
                if isinstance(curproj, Wolf2D_Project):
                    curproj.find_values_inside(zonepoly)

        elif which_project in self.projects.keys():
            curproj = self.projects[which_project]
            if isinstance(curproj, Wolf2D_Project):
                curproj.find_values_inside(zonepoly)

    def get_values(self, which_type, which_project= None):

        valdict = {}

        if which_project is None:
            for curkey,curproj in self.projects.items():
                if isinstance(curproj, Wolf2D_Project):
                    valdict[curkey] = curproj.get_values(which_type)

        elif which_project in self.projects.keys():
            curproj = self.projects[which_project]
            if isinstance(curproj, Wolf2D_Project):
                valdict[which_project] = curproj.get_values(which_type)

        return valdict