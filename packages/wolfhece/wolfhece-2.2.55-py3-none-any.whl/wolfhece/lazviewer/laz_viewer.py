import numpy as np
import laspy
from laspy.compression import LazBackend
from PIL import Image
from os.path import exists,join
import matplotlib.pyplot as plt
from os import stat,remove,listdir,scandir, makedirs
from pathlib import Path
import math
from time import sleep
from typing import Literal, Union
import zipfile
import logging
from enum import Enum
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from shapely.geometry import LineString, Point, CAP_STYLE, Polygon
from shapely.ops import prep
import wx
from tqdm import tqdm

from . import viewer
from ..PyWMS import getWalonmap
from ..PyTranslate import _
from ..color_constants import Colors
from ..PyParams import Wolf_Param, Type_Param
from ..matplotlib_fig import Matplotlib_Figure as MplFig, PRESET_LAYOUTS
from ..drawing_obj import Element_To_Draw
from ..CpGrid import CpGrid
from ..PyVertexvectors import vector, Zones, zone, wolfvertex

"""
Importation et visualisation de données LAS et LAZ

@author Pierre Archambeau
"""
class Colors_Lazviewer(Enum):
    ORTHO_2012_2013 = 2013
    ORTHO_2015 = 2015
    ORTHO_2021 = 2021
    ORTHO_2023 = 2023
    ORTHO_2006_2007 = 2006
    CODE_2013 = 0
    CODE_2023 = 2
    CODE_2021_2022 = 3
    FROM_FILE = 1

class Classification_LAZ():

    def __init__(self) -> None:

        self.class_name = 'SPW-Geofit 2023'
        self.classification:dict[str,str,list[float,float,float,float]] = {}
        self.test_wx()

        self._choose_colors = None
        self._viewer = None

    def test_wx(self):
        self.wx_exists = wx.App.Get() is not None

    def init_2013(self):

        self.class_name = 'SPW 2013-2014'
        self.classification={
            0  : ['0', 'Pas de classification', Colors.rgb_withalpha_float('black',.2),],
            1  : ['Hors-sol', 'building, toits et autres', Colors.rgb_withalpha_float('white',.2),],
            2  : ['Sol', 'y compris talus et digues', Colors.rgb_withalpha_float('brown',1.)],
            4  : ['Végétation', 'y compris la végétation linéaire', Colors.rgb_withalpha_float('forestgreen',1.)],
            9  : ['Eau', 'Eau',Colors.rgb_withalpha_float('aqua',1.)],
            10 : ['Ponts', 'Ponts',Colors.rgb_withalpha_float('lightyellow1',1.)]}

    def init_2021_2022(self):

        self.class_name = 'SPW 2021-2022'
        self.classification={
            0  : ['0', 'Pas de classification', Colors.rgb_withalpha_float('black',.2),],
            1  : ['Hors-sol', 'building, toits et autres', Colors.rgb_withalpha_float('white',.2),],
            2  : ['Sol', 'y compris talus et digues', Colors.rgb_withalpha_float('brown',1.)],
            4  : ['Végétation', 'y compris la végétation linéaire', Colors.rgb_withalpha_float('forestgreen',1.)],
            9  : ['Eau', 'Eau',Colors.rgb_withalpha_float('aqua',1.)],
            10 : ['Ponts', 'Ponts',Colors.rgb_withalpha_float('lightyellow1',1.)],
            15 : ['Ligne hautes-tension', 'Ligne hautes-tension',Colors.rgb_withalpha_float('lightcyan1',0.25)]}

    def init_2023(self):

        self.class_name = 'SPW-Geofit 2023'
        self.classification={
            0  : ['0', 'Pas de classification', Colors.rgb_withalpha_float('black',.2),],
            1  : ['Défaut', 'Voiture, câbles électrique, points de végétation diffus, Sursol non utile', Colors.rgb_withalpha_float('white',.2),],
            2  : ['Sol', 'Tous les éléments du sol y compris les descentes de garage en sous-sol', Colors.rgb_withalpha_float('gray',1.)],
            4  : ['Végétation', 'Végétation', Colors.rgb_withalpha_float('forestgreen',1.)],
            6  : ['Bâtiments', 'Bâtiments',Colors.rgb_withalpha_float('lightslategray',1.)],
            9  : ['Eau', 'Points de la surface d\’eau brute mesurés par le scanner 2',Colors.rgb_withalpha_float('royalblue',.3)],
            10 : ['Ponts', 'Les ponts ont été classés à part pour améliorer la définition du MNT. Ils ont été ouverts grâce',Colors.rgb_withalpha_float('lightyellow1',1.)],
            11 : ['Mur de berges', 'Mur et muret en berge de la Vesdre dépassant le sol à des vocation de réaliser une modélisation 3D hydraulique avec ces obstacles.',Colors.rgb_withalpha_float('red1',1.)],
            13 : ['Inconnu', 'A vérifier auSPW', Colors.rgb_withalpha_float('lightslategray',.2)],
            15 : [r'Tranche d\'eau', r'Echo intermédiaire dans l\’eau n\’appartenant ni à la surface d\’eau ni au fond du lit', Colors.rgb_withalpha_float('lightblue',.2)],
            16 : ['Surface bathymétrique', r'Fond du lit de la Vesdre et de ses affluents et des autres surfaces d\’eau mesurées à partir du scanner 3 FWF discrétisé',Colors.rgb_withalpha_float('sandybrown',1.)],
            17 : ['Surface bathymétrique incertaine', 'Surface bathymétrique sur les zones peu profondes principalement sous végétation où les intensités des échos sont parfois trop faibles pour avoir la certitude qu\’ils représentent le fond de rivière. La classe 17 est néanmoins plus certaine que la classe 18. Elle est utilisée dans la génération des MNT par défaut.',Colors.rgb_withalpha_float('rosybrown',.5)],
            19 : [r'Surface d\eau calculée', r'Points sous échantillonnés de la surface d\’eau ayant servis à faire les calculs de correction de réfraction bathymétrique',Colors.rgb_withalpha_float('lightblue',.2)],
            20 : ['Surface bathymétrique incertaine profonde', 'Surface bathymétrique sur les zones plus profondes principalement au centre de la rivière où les intensités des échos sont parfois trop faibles pour avoir la certitude qu\’ils représentent le fond de rivière. Non utilisée dans la génération du MNT. + Surface proche bathy mais potentiellement émergée pour les scanner 1 à 3',Colors.rgb_withalpha_float('lightblue',.5)],
            29 : [r'Surface d\'eau héliportée', r'La hauteur d\’eau du vol héliporté étant largement supérieure (de 30 à 40cm au vol Titan, les points matérialisant cette surface ont été reclassés dans cette classe séparée pour ne pas perturbé le reste du nuage de point.',Colors.rgb_withalpha_float('cyan',.3)]}

    def callback_colors(self):
        """ Update from wx GUI """

        for key, curclass in self.classification.items():
            name, comment, col = curclass
            cur_color = [float(cur)/255. for cur in self._choose_colors[(_('Colors'), name)]]

            self.classification[key] = [name, comment, cur_color]

    def callback_destroy(self):
        self.callback_colors()
        self._choose_colors = None

    def interactive_update_colors(self):
        """ set GUI """
        self.test_wx()

        if self._choose_colors is None and self.wx_exists:
            self._choose_colors = Wolf_Param(None, _('Colors of classification LAZ 2023'), w=600, h=800, to_read=False, withbuttons=True, toShow=False, force_even_if_same_default=True)
            self._choose_colors.callback        = self.callback_colors
            self._choose_colors.callbackdestroy = self.callback_destroy
            self._choose_colors.hide_selected_buttons()

        for key, curclass in self.classification.items():
            name, comment, color = curclass
            self._choose_colors.addparam(_('Colors'), name, [int(cur*255) for cur in color], 'Color', comment, whichdict='All')

        self._choose_colors.Populate()
        self._choose_colors.SetSize((600,500))
        self._choose_colors.Show()


def choices_laz_colormap() -> list[str]:

    choices = [cur.name for cur in Colors_Lazviewer]
    values  = [cur for cur in Colors_Lazviewer]

    return choices, values

class xyz_laz():
    """
    Classe de gestion des fichiers XYZ+Class issus d'un gros fichier laz
    """

    def __init__(self, fn:str='', format:Literal['las', 'numpy']='las', to_read:bool=True) -> None:

        # Emprise spatiale
        self.origx = -99999.
        self.origy = -99999.
        self.endx  = -99999.
        self.endy  = -99999.

        # format de fichier
        self.format = format
        self.dtype = np.float32

        if fn !='':
            self.filename = fn

            if not (exists(self.filename) or exists(self.filename+'.zip')):
                self.data = []
                return

            last_part = Path(fn).name
            parts = last_part.split('_')

            # L'origine est codée dans le nom de fichier
            self.origx = float(parts[-3])
            self.origy = float(parts[-2])

            dx = 2500.
            dy = 3500.

            # Récupération du lien vers le fichier GridInfo.txt
            gridinfo=join(Path(fn).parent,'gridinfo.txt')

            if exists(gridinfo):
                with open(gridinfo,'r') as f:
                    myinfos=f.read().splitlines()

                    myinfos[0]=np.float32(myinfos[0].split(',')) # xmin, xmax
                    myinfos[1]=np.float32(myinfos[1].split(',')) # ymin, ymax
                    myinfos[2]=np.float32(myinfos[2].split(',')) # NbX, NbY

                    # calcul du pas spatial de découpage selon X et Y
                    dx = (myinfos[0][1]-myinfos[0][0])/myinfos[2][0]
                    dy = (myinfos[1][1]-myinfos[1][0])/myinfos[2][1]

                    if len(myinfos)==5:
                        self.dtype = np.float64 if myinfos[4].lower()=='xy_float64' else np.float32

            # extrêmité de fichier
            self.endx = self.origx + dx
            self.endy = self.origy + dy

            if to_read:
                 self.read_bin_xyz()

    @property
    def size(self):
        return len(self.data)

    def split(self, dir_out:str, nbparts:int):
        """ Split file into 'nb' parts along X and Y"""

        xparts = np.linspace(self.origx,self.endx,nbparts+1)
        yparts = np.linspace(self.origy,self.endy,nbparts+1)

        dx = (self.endx-self.origx)/nbparts
        dy = (self.endy-self.origy)/nbparts

        for curx in xparts[:-1]:
            for cury in yparts[:-1]:
                with open(join(dir_out,'LIDAR_2013_2014_'+str(int(curx))+'_'+str(int(cury))+'_xyz.bin'),'wb') as f:

                    curbounds = [[curx,curx+dx],[cury,cury+dy]]
                    mypts = find_pointsXYZ(self.data,curbounds)
                    if len(mypts)>0:
                        f.write(np.int32(mypts.shape[0]))
                        f.write(np.float32(mypts[:,0]).tobytes())
                        f.write(np.float32(mypts[:,1]).tobytes())
                        f.write(np.float32(mypts[:,2]).tobytes())
                        f.write(np.int8(mypts[:,3]).tobytes())

    def get_bounds(self):
        # Return geographic bounds of the file
        return ((self.origx,self.endx),(self.origy,self.endy))

    def test_bounds(self, bounds:list[list[float, float],list[float, float]]):
        # Test current bounds relating to parameter bounds

        x1=bounds[0][0]
        x2=bounds[0][1]
        y1=bounds[1][0]
        y2=bounds[1][1]

        mybounds = self.get_bounds()

        test = not(x2 < mybounds[0][0] or x1 > mybounds[0][1] or y2 < mybounds[1][0] or y1 > mybounds[1][1])

        return test

    def read_bin_xyz(self):
        """
        Lecture d'un fichier binaire de points XYZ+classification généré par la fonction sort_grid_np
        Le format est une succession de trame binaire de la forme :

        nbpoints (np.int32)
        X[nbpoints] (np.float32) ou (np.float64)
        Y[nbpoints] (np.float32) ou (np.float64)
        Z[nbpoints] (np.float32)
        Classif[nbpoints] (np.int8)

        Il est possible de récupérer une matrice numpy shape(nbtot,4)
        ou un objet laspy via l'argument 'out' (par défaut à 'las')
        """
        fn=self.filename

        if exists(fn+'.zip'):
            with zipfile.ZipFile(fn+'.zip','r') as zip_file:
                fn = zip_file.namelist()[0]
                zip_file.extract(fn, path=Path(fn).parent)
                fn = join(Path(fn).parent, fn)
        elif not exists(fn):
            return

        fnsize=stat(fn).st_size

        nb=0
        count=0
        myret=[]

        with open(fn,'rb') as f:
            while count<fnsize:
                nbloc = np.frombuffer(f.read(4),np.int32)[0]
                nb+=nbloc

                dtype_file = self.dtype

                blocsize = nbloc*4 if dtype_file == np.float32 else nbloc*8

                x=np.frombuffer(f.read(blocsize),dtype_file)
                y=np.frombuffer(f.read(blocsize),dtype_file)
                z=np.frombuffer(f.read(nbloc*4),np.float32)
                classi=np.frombuffer(f.read(nbloc),np.int8)

                count+=4+(2*blocsize+nbloc*(4+1))

                if classi.shape[0] != nbloc:
                    logging.warning(_('Bad classification size - file {}'.format(fn)))
                else:
                    if len(myret)==0:
                        # dt=[('x',np.float32),('y',np.float32),('z',np.float32),('classification',np.int8)]
                        myret=np.array([x,y,z,classi]).transpose()
                    else:
                        if len(x)>1:
                            added = np.array([x,y,z,classi]).transpose()

                            if myret.shape[1] == added.shape[1]:
                                myret=np.concatenate((myret,added))
                            else:
                                logging.warning(_('Incompatible shapes'))

        # Format Numpy
        self.data = myret

        if self.format=='las':
            self.to_las()

        # suppressdion du fichier extrait
        if exists(self.filename+'.zip'):
            remove(fn)

    def to_las(self):
        if self.format=='las':
            return
        else:
            # self.data=xyz_to_las(self.data)
            self.format='las'

class xyz_laz_grid():
    """
    Gestion d'un grid de données LAZ
    """

    def __init__(self, mydir:str) -> None:

        # répertoire de stockage des données griddées, y compris fichier 'gridinfo.txt'
        self.mydir = mydir

        gridinfo=join(mydir,'gridinfo.txt')

        self.origx,self.endx, self.origy,self.endy, self.nbx,self.nby, self.genfile = self._read_gridinfo(gridinfo)

        if self.nbx>0 and self.nby>0:
            self.dx = (self.endx-self.origx)/float(self.nbx)
            self.dy = (self.endy-self.origy)/float(self.nby)

    def _read_gridinfo(self, gridinfo:str) -> list:

        if exists(gridinfo):
            with open(gridinfo,'r') as f:
                myinfos=f.read().splitlines()

                origx, endx=np.float32(myinfos[0].split(','))
                origy, endy=np.float32(myinfos[1].split(','))
                nbx, nby=np.int32(myinfos[2].split(','))
                genfile = myinfos[3] # nom à pister avec x1 et y1 comme paramètres

            return [origx, endx, origy, endy, nbx, nby, genfile]
        else:
            return [99999.,99999.,99999.,99999.,0,0,'']

    def scan(self, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]):
        """ Find all points in bounds """
        x1=bounds[0][0]
        x2=bounds[0][1]
        y1=bounds[1][0]
        y2=bounds[1][1]

        file1= self.genfile.split('x1')[0]
        file2= self.genfile.split('y1')[-1]

        data=[]

        for x in range(int(self.origx), int(self.endx), int(self.dx)):
            for y in range(int(self.origy), int(self.endy), int(self.dy)):

                locbounds=np.float64(((x,x+self.dx),(y,y+self.dy)))

                test = not(x2 < locbounds[0][0] or x1 > locbounds[0][1] or y2 < locbounds[1][0] or y1 > locbounds[1][1])

                if test:
                    fxyz = file1+str(int(x))+'_'+str(int(y))+file2

                    fn = join(self.mydir,fxyz)
                    locxyz=xyz_laz(fn)
                    if locxyz.size > 0:
                        data.append(locxyz.data)

        if len(data)>0:
            retdata=find_pointsXYZ(np.concatenate(data), bounds)
        else:
            retdata = np.asarray([])

        return retdata

    def find_files_in_bounds(self, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]):
        """ Find all files in bounds """

        x1=bounds[0][0]
        x2=bounds[0][1]
        y1=bounds[1][0]
        y2=bounds[1][1]

        file1= self.genfile.split('x1')[0]
        file2= self.genfile.split('y1')[-1]

        files=[]

        for x in range(int(self.origx), int(self.endx), int(self.dx)):
            for y in range(int(self.origy), int(self.endy), int(self.dy)):

                locbounds=np.float64(((x,x+self.dx),(y,y+self.dy)))

                test = not(x2 < locbounds[0][0] or x1 > locbounds[0][1] or y2 < locbounds[1][0] or y1 > locbounds[1][1])

                if test:
                    fxyz = file1+str(int(x))+'_'+str(int(y))+file2

                    fn = join(self.mydir,fxyz)
                    if exists(fn):
                        files.append(fn)

        return files

    def _split_xyz(self, dirout:str, nbparts:int = 10):
        """ Split XYZ file into 'nb' parts along X and Y """
        for entry in scandir(self.mydir):
            if entry.is_file():
                if entry.name.endswith('.bin'):

                    myxy = xyz_laz(entry.path)
                    myxy.split(dirout, nbparts)
                    print(entry.name)

    def _sort_grid_np(self,
                     fn_in:str,  # laz file
                     fn_out:str, # generic file name in dir out
                     bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]],
                     gridsize:list[int],
                     chunksize:int=5000000,
                     force_format = np.float64):

        """ Create .bin files from .laz """
        xbounds=bounds[0]
        ybounds=bounds[1]

        xloc = np.linspace(xbounds[0], xbounds[1], gridsize[0]+1)
        yloc = np.linspace(ybounds[0], ybounds[1], gridsize[1]+1)

        dirout = Path(fn_out).parent
        fn=join(dirout,'gridinfo.txt')

        if exists(fn):
            remove(fn)

        with open(fn,'w') as f:
            f.write(str(int(xbounds[0]))+','+str(int(xbounds[1]))+'\n')
            f.write(str(int(ybounds[0]))+','+str(int(ybounds[1]))+'\n')
            f.write(str(int(gridsize[0]))+','+str(int(gridsize[1]))+'\n')
            f.write(Path(fn_out).name+'_'+'x1'+'_'+'y1'+'_xyz.bin'+'\n')
            if force_format == np.float64:
                f.write('xy_float64')
            else:
                f.write('xy_float32')

        k=0
        with laspy.open(fn_in, laz_backend=LazBackend.Laszip) as f:
            nb = (f.header.point_count // chunksize) +1
            print('Points from Header:', f.header.point_count)

            #création des objets d'écriture
            writers=[]
            for i in range(gridsize[0]):
                writers.append([])

                for j in range(gridsize[1]):
                    fn=fn_out+'_'+str(int(xloc[i]))+'_'+str(int(yloc[j]))+'_xyz.bin'
                    if exists(fn):
                        remove(fn)

                    writers[i].append(open(fn, "wb"))

            for las in f.chunk_iterator(chunksize):
                print(k,' / ',nb)
                for i in range(gridsize[0]):
                    for j in range(gridsize[1]):
                        mypts=find_points(las,(xloc[i],xloc[i+1]),(yloc[j],yloc[j+1]))
                        if mypts is not None:
                            print(len(mypts))

                            print(int(xloc[i]),int(yloc[j]))
                            writers[i][j].write(np.int32(len(mypts)))

                            if force_format == np.float64:
                                writers[i][j].write(np.float64(mypts.x).tobytes())
                                writers[i][j].write(np.float64(mypts.y).tobytes())
                            else:
                                writers[i][j].write(np.float32(mypts.x).tobytes())
                                writers[i][j].write(np.float32(mypts.y).tobytes())

                            writers[i][j].write(np.float32(mypts.z).tobytes())
                            writers[i][j].write(np.int8(mypts.classification).tobytes())

                k+=1
                print('--')

        self.origx = xbounds[0]
        self.origy = ybounds[0]
        self.endx = xbounds[1]
        self.endy = ybounds[1]
        self.nbx = gridsize[0]
        self.nby = gridsize[1]

        if self.nbx == 0 or self.nby == 0:
            logging.error(_('Grid size is 0 - abort !'))
            return

        self.dx = (self.endx-self.origx)/float(self.nbx)
        self.dy = (self.endy-self.origy)/float(self.nby)
        self.genfile=fn_out+'_'+'x1'+'_'+'y1'+'_xyz.bin'

        for curwriter in writers:
            for curfile in curwriter:
                curfile.close()

        for i in range(gridsize[0]):
            for j in range(gridsize[1]):
                fn = fn_out+'_'+str(int(xloc[i]))+'_'+str(int(yloc[j]))+'_xyz.bin'
                curstat = stat(fn)
                if curstat.st_size==0:
                    remove(fn)
                else:
                    if force_format == np.float64:
                        fnzip = fn + '.zip'
                        with zipfile.ZipFile(fnzip,'w',zipfile.ZIP_DEFLATED) as zip_file:
                            zip_file.write(fn, Path(fn).name)
                        remove(fn)


class xyz_laz_grids():
    """ Ensemble de grids """

    def __init__(self, dir_grids:str, create:bool=False) -> None:

        dir_grids = str(dir_grids)

        self.grids:list[xyz_laz_grid] = []
        self.colors = Classification_LAZ()
        self.colors.init_2023()

        if exists(dir_grids):
            self.dir = dir_grids
            self.read_dir(dir_grids)
        else:
            if create:
                makedirs(dir_grids, exist_ok=True)
                self.dir = dir_grids
            else:
                self.dir = None

    def scan(self, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]) -> np.ndarray:
        """
        Scan all LAZ to find used data

        :param bounds: [[xmin,xmax], [ymin,ymax]]
        :type bounds: Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]
        :return: np.ndarray
        """
        ret = [cur.scan(bounds) for cur in self.grids]
        ret = [cur for cur in ret if len(cur)>0]

        if len(ret)==0:
            logging.info(_('No data found'))
            return np.asarray([])
        else:
            ret = np.concatenate(ret)
            logging.info(_('Data found -- {:_} points'.format(ret.shape[0])))
            return ret

    def find_files_in_bounds(self, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]):
        """ Find all files in bounds

        :param bounds: [[xmin,xmax], [ymin,ymax]]"""

        ret = [(cur.mydir, cur.find_files_in_bounds(bounds)) for cur in self.grids]
        ret = [cur for cur in ret if len(cur[1])>0]

        if len(ret)==0:
            logging.info(_('No data found'))
            return []
        else:
            logging.info(_('Data found -- {:_} files'.format(len(ret))))
            return ret

    def copy_files_in_bounds(self, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]], dirout:str):
        """ Copy files in bounds to directory

        :param bounds: [[xmin,xmax], [ymin,ymax]]
        :param dirout: output directory
        """

        import shutil

        out = Path(dirout)
        out.mkdir(exist_ok=True)

        files = self.find_files_in_bounds(bounds)

        for curdir, curfiles in files:
            locdir = out / Path(curdir).name
            locdir.mkdir(exist_ok=True)
            for curfile in curfiles:
                shutil.copy(curfile, locdir / Path(curfile).name)

            # copy gridinfo.txt
            shutil.copy(join(curdir,'gridinfo.txt'), locdir / 'gridinfo.txt')

    def read_dir(self, dir_grids):
        """ Read all grids in directory and subdirectories """

        import asyncio

        def init_grid(curdir):
            if (Path(dir_grids) / Path(curdir)).is_dir():
                return xyz_laz_grid(join(dir_grids, curdir))

            return None

        # check if an event loop is running
        # If it is the case, read data in a single thread
        try:
            asyncio.get_running_loop()
            logging.info(_('Event loop detected - reading grids in single thread'))
            use_async = False
        except RuntimeError:
            use_async = True

        if not use_async:
            dirs = listdir(dir_grids)

            logging.info(_('Reading grids information -- {} grids'.format(len(dirs))))

            self.grids = [init_grid(curdir) for curdir in dirs if (Path(dir_grids) / Path(curdir)).is_dir()]
            self.grids = list(filter(None, self.grids))

            logging.info(_('Grids initialized'))
            return

        # else use asyncio to read in parallel
        dirs = listdir(dir_grids)

        logging.info(_('Reading grids information -- {} grids'.format(len(dirs))))

        async def init_grid_async(curdir):
            return init_grid(curdir)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [init_grid_async(curdir) for curdir in dirs]
        self.grids = list(filter(None, loop.run_until_complete(asyncio.gather(*tasks))))
        loop.close()

        logging.info(_('Grids initialized'))

    def scan_around(self, xy:Union[LineString,list[list[float], list[float]]], length_buffer=5.):
        """
        Récupération de points LAZ autour de la section
        """

        if isinstance(xy, LineString):
            myls = xy
        else:
            myls = LineString([Point(x,y) for x,y in xy])

        logging.info(_('Create buffer around polyline'))
        # Création d'un buffer autour de la LineString
        mypoly:Polygon
        mypoly = myls.buffer(length_buffer,cap_style=CAP_STYLE.square)

        logging.info(_('Get bounding box'))
        # Récupération des bornes
        mybounds = ((mypoly.bounds[0],mypoly.bounds[2]),(mypoly.bounds[1],mypoly.bounds[3]))
        logging.info(_('Get LAZ points bounding box'))
        # scan sur base du rectangle
        myxyz = self.scan(mybounds)

        logging.info(_('Select interior points'))
        # Vérification des points intérieurs
        prep_poly = prep(mypoly)
        mytests = [prep_poly.contains(Point(cur[:3])) for cur in myxyz]

        usedlaz = np.asarray(myxyz[mytests])

        logging.info(_('Compute distance along polyline'))
        # Projection des points utiles le long du vecteur
        s = np.asarray([myls.project(Point(cur[:2])) for cur in usedlaz])

        # smax = myls.length
        # usedlaz = usedlaz[np.logical_and((s !=0.),(s != smax))]

        logging.info(_('Compute colors'))
        # couleurs
        colors=np.ones((usedlaz.shape[0],4),dtype=np.float32)

        for key, val in self.colors.classification.items():
            name, comment, color = val
            colors[usedlaz[:,3] == key] = color

        logging.info(_('Compute distance perpendicular to polyline'))
        # distance normale au vecteur --> alpha/transparence
        orig = np.asarray(myls.coords[0])
        extr = np.asarray(myls.coords[-1])
        a    = extr-orig
        s_perp = np.asarray([float(np.cross(a, cur[:3] - orig)[2])  for cur in usedlaz])
        smax = np.max(np.abs(s_perp))

        logging.info(_('Alpha blending'))
        colors[:,3] = 1.-np.abs(s_perp)/smax

        logging.info(_('Find up and Down points'))
        # recherche des points à l'amont
        up=np.where(s_perp[:]<0.)[0]
        # recherche des points à l'aval
        down=np.where(s_perp[:]>=0.)[0]

        up_s = s[up]
        down_s = s[down]

        up_z = usedlaz[up,2]
        down_z = usedlaz[down,2]

        up_colors = colors[up]
        down_colors = colors[down]

        logging.info(_('Number of points upstream : {}'.format(len(up_s))))
        logging.info(_('Number of points downstream : {}'.format(len(down_s))))

        return (up_s, up_z, up_colors), (down_s, down_z, down_colors)

    def plot_laz(self, xy:Union[LineString, list[list[float], list[float]]], length_buffer=5., figax:tuple[Figure, Axes]=None, show=False):
        """
        Dessin des points LAZ sur un graphique Matplotlib
        """

        (up_s, up_z, up_color), (down_s, down_z, down_color) = self.scan_around(xy, length_buffer)

        if figax is None:
            fig = plt.figure()
            ax=fig.add_subplot(111)
        else:
            fig,ax = figax

        logging.info(_('Plotting'))
        ax.scatter(up_s,   up_z,  c=up_color  ,marker='.')
        ax.scatter(down_s, down_z,c=down_color,marker='+')

        if show:
            fig.show()

        return fig,ax

    def plot_laz_wx(self, xy:Union[LineString, list[list[float], list[float]]], length_buffer=5., show=True):
        """
        Dessin des points LAZ sur un graphique Matplotlib
        """

        (up_s, up_z, up_color), (down_s, down_z, down_color) = self.scan_around(xy, length_buffer)

        figmpl = MplFig(PRESET_LAYOUTS.DEFAULT)

        logging.info(_('Plotting'))
        figmpl.scatter(up_s,   up_z,  c=up_color  ,marker='.')
        figmpl.scatter(down_s, down_z,c=down_color,marker='+')

        if show:
            figmpl.Show()

        return figmpl

    def create_from_laz(self, dir_laz:Path, shape:str=None, ds:float = 50, force_format = np.float64):

        try:
            from ..PyVertexvectors import Zones
        except:
            from wolfhece.PyVertexvectors import Zones

        vecs = None
        if shape is not None:
            vecs = Zones(shape)

        dir_laz = Path(dir_laz)

        for entry in tqdm(dir_laz.glob('**/*.laz')):
            if entry.is_file():

                file_wo_suf = entry.stem
                dirname = join(self.dir, file_wo_suf)

                if not exists(dirname):
                    makedirs(dirname, exist_ok=True)

                    newlaz = xyz_laz_grid(mydir=dirname)

                    if vecs is not None:
                        vec = vecs.get_zone(file_wo_suf)
                        bounds = vec.myvectors[0].get_bounds()
                    else:
                        lazdata = laspy.read(entry)
                        bounds = [[lazdata.x.min(), lazdata.y.min()],
                                    [lazdata.x.max(), lazdata.y.max()]]

                    bounds = [[math.floor(bounds[0][0]/ds)*ds, math.floor(bounds[0][1]/ds)*ds],
                                        [math.ceil(bounds[1][0]/ds)*ds, math.ceil(bounds[1][1]/ds)*ds]]

                    dx = bounds[1][0] -bounds[0][0]
                    dy = bounds[1][1] -bounds[0][1]
                    nb = max(int(dx/ds), int(dy/ds))

                    self.grids.append(newlaz._sort_grid_np(entry,
                                                        join(dirname, file_wo_suf),
                                                        bounds=[[bounds[0][0], bounds[1][0]], [bounds[0][1], bounds[1][1]]],
                                                        gridsize=[max(int(dx/ds),1), max(int(dy/ds),1)],
                                                        force_format=force_format))

    def create_bounds_shape(self, dir_laz:str, out_shape:str):
        """ Create shape from laz files """
        try:
            from ..PyVertexvectors import Zones
        except:
            from wolfhece.PyVertexvectors import Zones

        dir_laz = Path(dir_laz)
        out_shape = Path(out_shape)

        vecs = Zones()

        for entry in tqdm(dir_laz.glob('**/*.laz')):
            if entry.is_file():
                lazdata = laspy.read(entry)

                bounds = [[lazdata.x.min(), lazdata.y.min()],
                            [lazdata.x.max(), lazdata.y.max()]]
                loczone = zone(name=entry.stem)
                locvec = vector(name=entry.stem)

                locvec.add_vertex(wolfvertex(bounds[0][0], bounds[0][1]))
                locvec.add_vertex(wolfvertex(bounds[1][0], bounds[0][1]))
                locvec.add_vertex(wolfvertex(bounds[1][0], bounds[1][1]))
                locvec.add_vertex(wolfvertex(bounds[0][0], bounds[1][1]))
                locvec.close_force()

                loczone.add_vector(locvec, forceparent=True)
                vecs.add_zone(loczone, forceparent=True)

        vecs.saveas(Path(self.dir) / out_shape)

class Wolf_LAZ_Data(Element_To_Draw):
    """ Base class for LAZ data which can be imported in Pydraw.Mapviewer.
    """

    def __init__(self, idx:str = '', plotted:bool = False, mapviewer = None, need_for_wx:bool = False) -> None:

        self._filename:Path = Path('') # filename TODO : improve serialization
        self._lazfile:Path = None # Not used

        # Bounds must be set before calling super().__init__() because
        # xmin, xmax, ymin, ymax properties are used and depend on _bounds
        self._bounds = [[0.,0.],[0.,0.]] # [[xmin,xmax],[ymin,ymax]]

        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self._data:np.ndarray = None    # Numpy data array -- to be plotted
        self._colors:np.ndarray = None  # NumPy array of colors for each point --> see viewer attributes for details
        self.classification = Classification_LAZ() # Classification of LAZ data --> defining colors if codification is used
        self.classification.init_2023() # Default classification for LAZ data

        self._associated_color:int = Colors_Lazviewer.CODE_2023 # Associated color type for LAZ data

        self.viewer:viewer = None       # PPTK viewer

        self._point_size = .05 # Point size in viewer -- in user units

        self._flight_memory = [] # Flight position

        self._myprops = None # Properties based on Wolf_Param class

        self._bg_color = [int(0.23*255), int(0.23*255), int(.44*255), 255]  # Background color
        self._bg_color_top = [0, 0, 0, 255]  # Top background color
        self._bg_color_bottom = [int(0.23*255), int(0.23*255), int(.44*255), 255]  # Bottom background color

        self._floor_level = 0.  # Floor level -- user units
        self._floor_color = [int(0.3*255), int(0.3*255), int(.3*255), 127] # Floor color

        self._show_grid = True # Show grid in viewer
        self._show_axis = True # Show axis in viewer
        self._show_info = True # Show info in viewer

        self._select_only_codes = [] # Codes to be selected -- Defined by user

        self._xls:CpGrid = None # Excel grid for selected data
        self._xlsFrame:wx.Frame = None # Frame containing the xls grid

    def serialize(self):
        """ Serialize class : data and attributes """
        return {'bounds':self._bounds, 'data':str(self._filename) + '.npz', 'associated_color':self._associated_color.value,
                'point_size':self._point_size, 'bg_color':self._bg_color, 'bg_color_top':self._bg_color_top,
                'bg_color_bottom':self._bg_color_bottom, 'floor_level':self._floor_level, 'floor_color':self._floor_color,
                'show_grid':self._show_grid, 'show_axis':self._show_axis, 'show_info':self._show_info}

    def deserialize(self, data:dict):
        """ Deserialize class : data and attributes """
        self._bounds = data['bounds']
        self._filename = Path(data['data'])
        self._associated_color = data['associated_color']
        self._point_size = data['point_size']
        self._bg_color = data['bg_color']
        self._bg_color_top = data['bg_color_top']
        self._bg_color_bottom = data['bg_color_bottom']
        self._floor_level = data['floor_level']
        self._floor_color = data['floor_color']
        self._show_grid = data['show_grid']
        self._show_axis = data['show_axis']
        self._show_info = data['show_info']

        self.data = np.load(self._filename)['data']

    def saveas(self, fn:str):
        """ Save class : data and attributes """
        import pickle

        self._filename = Path(fn)

        with open(fn,'wb') as f:
            pickle.dump(self.serialize(),f)

        # save data by numpy
        np.savez(str(fn) + '.npz', data=self._data)

    def load(self, fn:str):
        """ Load class : data and attributes """
        import pickle

        with open(fn,'rb') as f:
            self.deserialize(pickle.load(f))

    @property
    def associated_color(self):
        return self._associated_color

    @associated_color.setter
    def associated_color(self, value:int | Colors_Lazviewer):

        if isinstance(value, int):
            self._associated_color = Colors_Lazviewer(value)
        else:
            self._associated_color = value
        self.set_colors()

    def merge(self, other:"Wolf_LAZ_Data"):
        """ Merge two Wolf_LAZ_Data objects """

        if self._data is None:
            self._data = other._data
        else:
            self._data = np.concatenate((self._data, other._data))

        self.bounds = [[min(self.bounds[0][0],other.bounds[0][0]),max(self.bounds[0][1],other.bounds[0][1])],
                       [min(self.bounds[1][0],other.bounds[1][0]),max(self.bounds[1][1],other.bounds[1][1])]]

    def filter_data(self, codes:list[int]):
        """ Filter data by codes """
        self._data = self._data[np.isin(self._data[:,3],codes)]

    def bg_color(self, value):
        if self.viewer is not None:
            return self.viewer.set(bg_color = value)

    def bg_color_top(self, value):
        if self.viewer is not None:
            return self.viewer.set(bg_color_top = value)

    def bg_color_bottom(self, value):
        if self.viewer is not None:
            return self.viewer.set(bg_color_bottom = value)

    def floor_level(self, value):
        if self.viewer is not None:
            return self.viewer.set(floor_level = float(value))

    def floor_color(self, value):
        if self.viewer is not None:
            return self.viewer.set(floor_color = value)

    def show_grid(self, value:bool):
        if self.viewer is not None:
            return self.viewer.set(show_grid = bool(value))

    def show_axis(self, value:bool):
        if self.viewer is not None:
            return self.viewer.set(show_axis = bool(value))

    def show_info(self, value:bool):
        if self.viewer is not None:
            return self.viewer.set(show_info = bool(value))

    def force_view(self, x, y, z = -1):
        """ Force lookat position """
        if z == -1:
            curx,cury,curz = self.lookat
            self.lookat = [x,y,curz]
        else:
            self.lookat = [x,y,z]
        # self.eye = self._eye_pos()

    @property
    def selected(self):
        if self.viewer is None:
            return None
        return self.viewer.get('selected')

    @property
    def xyz_selected(self) -> np.ndarray:
        """ Extract the selected points from the viewer.

        Filter the selected points by codes if _select_only_codes is not empty."""

        if self.viewer is None:
            return None

        if self.selected.shape[0] == 0:
            return np.ndarray((0,3))

        if len(self._select_only_codes)>0:
            return self.data[self.selected,:3][np.isin(self.data[self.selected,3],self._select_only_codes)]
        else:
            return self.data[self.selected,:3]

    @property
    def code_selected(self) -> np.ndarray:
        if self.viewer is None:
            return None

        if self.selected.shape[0] == 0:
            return np.ndarray((0,1))

        if len(self._select_only_codes)>0:
            return self.data[self.selected,3][np.isin(self.data[self.selected,3],self._select_only_codes)]
        else:
            return self.data[self.selected,3]

    @property
    def num_points(self):
        """ Number of points """

        nb1 = self.data.shape[0]
        if self.viewer is not None:
            try:
                nb2 = self.viewer.get('num_points')[0]
                assert nb1 == nb2, _('Incoherent number of points')
            except:
                # viewer is not initialized or Destroyed
                self.viewer = None
        return nb1

    @property
    def nb_points(self):
        """ Number of points - alias of num_points """
        return self.num_points

    @property
    def nb(self):
        """ Number of points - alias of num_points """
        return self.num_points

    @property
    def right(self):
        """Camera Right vector """
        return self.viewer.get('right')

    @property
    def mvp(self):
        """ Model View Projection matrix

        See https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93projection_matrix for details
        """

        if self.viewer is None:
            return None
        return self.viewer.get('mvp')

    @property
    def eye(self):
        """ eye/camera position """
        if self.viewer is None:
            return None
        return self.viewer.get('eye')

    @property
    def lookat(self):
        """ Lookat position """
        if self.viewer is None:
            return None
        return self.viewer.get('lookat')

    @property
    def phi(self):
        """ Azimuth angle (radians) """
        if self.viewer is None:
            return None
        return self.viewer.get('phi')[0]

    @property
    def theta(self):
        """ Elevation angle (radians) """
        if self.viewer is None:
            return None
        return self.viewer.get('theta')[0]

    @property
    def r(self):
        """ Distance from lookat """
        if self.viewer is None:
            return None
        return self.viewer.get('r')[0]

    @phi.setter
    def phi(self, value):
        if self.viewer is None:
            return None
        self.viewer.set(phi=value)
        self._fill_props()

    @theta.setter
    def theta(self, value):
        if self.viewer is None:
            return None
        self.viewer.set(theta=value)
        self._fill_props()

    @r.setter
    def r(self, value):
        if self.viewer is None:
            return None
        self.viewer.set(r=value)
        self._fill_props()

    @lookat.setter
    def lookat(self, value):
        if self.viewer is None:
            return None
        self.viewer.set(lookat=value)
        # self.viewer.set(lookat=value, phi=self.phi, theta=self.theta, r=self.r)
        self._fill_props()

    def _eye_pos(self):
        """ Compute eye pos from lookat and r, phi, theta.

        phi is the azimuth angle (radians)
        theta is the elevation angle (radians)
        r is the distance from lookat
        """

        lx, ly, lz = self.lookat
        r = self.r
        phi = self.phi
        theta = self.theta

        x = lx + r*np.sin(phi)*np.cos(theta)
        y = ly + r*np.cos(phi)*np.cos(theta)
        z = lz + r*np.sin(theta)

        return [x,y,z]

    @eye.setter
    def eye(self, value):
        if self.viewer is None:
            return None
        x,y,z = value
        lx, ly, lz = self.lookat
        right = self.right

        # Compute phi, theta, r based on eye and lookat and right vector
        r = np.sqrt((x-lx)**2 + (y-ly)**2 + (z-lz)**2)
        self.r =r
        self.theta = np.arcsin((z-lz)/r)
        self.phi = -np.arctan2((x-lx),(y-ly))
        self._fill_props()

    @property
    def point_size(self):
        """ Point size in viewer -- user units """
        return self._point_size

    @point_size.setter
    def point_size(self, value):
        self._point_size = value
        if self.viewer is not None:
            self.viewer.set(point_size=value)
            self._fill_props()

    @property
    def xyz(self):
        return self.data[:,:3]

    @property
    def codes(self):
        return self.data[:,3]

    def codes_unique(self):
        """ Only unique codes """
        return list(np.unique(self.codes).astype(int))

    def create_viewer(self, color_code:Colors_Lazviewer = None, classification:Classification_LAZ = None):
        """ Create a viewer for las data """

        if classification is not None:
            self.classification = classification

        if color_code is not None:
            self.associated_color = color_code

        self._colors = get_colors(self.data, self.associated_color, palette_classif= self.classification)

        self.viewer = viewer(self.xyz, self._colors)
        self.viewer.set(point_size= self._point_size)

        return self.viewer

    def interactive_update_colors(self):
        """ Create a frame to interactively update colors """

        self.classification.interactive_update_colors()

        self.classification._choose_colors.SetTitle(_('Colors of ') + self.idx)

        def new_callback_colors():
            self.classification.callback_colors()
            self.set_colors()

        self.classification._choose_colors.callback = new_callback_colors

    def set_colors(self):
        """ Set colors in viewer --> using attributes method (not colormap) """

        if self.viewer is not None:
            self._colors = get_colors(self.data, self.associated_color, palette_classif= self.classification)
            self.viewer.attributes(self._colors)

    def set_classification(self, classification:str = None):
        """ Set classification of LAZ data

        TODO : Check if 2020-2022 SPW campaign is the same classification as 2013
        """
        if classification is None:
            logging.warning(_('No classification chosen - Abort !'))
        elif classification == 'SPW 2013-2014':
            self.classification.init_2013()
        elif classification == 'SPW 2021-2022':
            self.classification.init_2021_2022()
        else:
            self.classification.init_2023()

    def find_minmax(self, update=False):
        """ Find min and max of data """
        if self.data is not None:
            self.bounds = [[np.min(self.data[:,0]), np.max(self.data[:,0])],[np.min(self.data[:,1]), np.max(self.data[:,1])]]

    @property
    def xmin(self):
        return self.bounds[0][0]

    @xmin.setter
    def xmin(self, value):
        self._bounds[0][0] = value

    @property
    def xmax(self):
        return self.bounds[0][1]

    @xmax.setter
    def xmax(self, value):
        self._bounds[0][1] = value

    @property
    def ymin(self):
        return self.bounds[1][0]

    @ymin.setter
    def ymin(self, value):
        self._bounds[1][0] = value

    @property
    def ymax(self):
        return self.bounds[1][1]

    @ymax.setter
    def ymax(self, value):
        self._bounds[1][1] = value

    @property
    def data(self):
        """ Full data array (x,y,z,code) """
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def bounds(self):
        return self._bounds

    @bounds.setter
    def bounds(self, value):
        self._bounds = value

    def from_grid(self, grid:xyz_laz_grids, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]):
        """ Create data from grid LAZ """
        self.bounds = bounds
        self.data = grid.scan(bounds)

    def from_file(self, fn:str):
        """ Create data from LAZ file """
        laz = read_laz(fn)
        self.data = np.column_stack((laz.x, laz.y, laz.z, laz.classification)).astype(np.float32)
        self.bounds = [[np.min(self.data[:,0]), np.max(self.data[:,0])],[np.min(self.data[:,1]), np.max(self.data[:,1])]]

    def descimate(self, step:int):
        """ Descimate data.

        Conserve only one point every 'step' points.

        :param step: step of descimation
        """
        self.data = self.data[::step]

    def get_data_class(self, key:int):
        """ Get data with a specific code """

        assert isinstance(key, int), _('Key must be an integer')

        return self.data[self.data[:,3] == key]

    def add_pose_in_memory(self, key_time:float = 1.):
        """ Add current pose in flight memory """

        if self.viewer is not None:
            lookat = self.lookat
            new_pose = (lookat[0], lookat[1], lookat[2], self.phi, self.theta, self.r)
            self._flight_memory.append((new_pose, key_time))

    def play_flight(self, tlim=[-np.inf, np.inf], repeat=False, interp='cubic_natural'):
        """ Play flight memory """
        if self.viewer is not None:
            if len(self._flight_memory)>0:
                poses = [cur[0] for cur in self._flight_memory]
                times = [0.]
                for i in range(1,len(self._flight_memory)):
                    times.append(times[-1]+self._flight_memory[i][1])
                self.viewer.play(poses, times, tlim, repeat, interp)

    def set_times(self, times:np.ndarray):
        """ Set times for flight memory """
        if len(self._flight_memory)>0:
            self._flight_memory = [(self._flight_memory[i][0], times[i]) for i in range(len(self._flight_memory))]

    def set_times_increment(self, increment:float):
        if len(self._flight_memory)>0:
            self._flight_memory = [(self._flight_memory[i][0], increment*i) for i in range(len(self._flight_memory))]

    def get_times(self):
        return np.asarray([cur[1] for cur in self._flight_memory])

    def record_flight(self, dirout:str, tlim=[-np.inf, np.inf], interp='cubic_natural', fps=24, prefix:str = 'laz_', ext:str = 'png'):
        """ Record flight memory in multiple images

        FIXME : FREEZE the app --> to debug
        """
        if self.viewer is not None:
            if len(self._flight_memory)>0:
                poses = [cur[0] for cur in self._flight_memory]
                times = [0.]
                for i in range(1,len(self._flight_memory)):
                    times.append(times[-1]+self._flight_memory[i][1])
                self.viewer.record(dirout, poses, times, tlim, interp, fps=fps, prefix=prefix, ext=ext)

    def save_flight(self, fn:str):
        """ Write flight memory to file JSON """

        import json

        if len(self._flight_memory)>0:
            with open(fn,'w') as f:
                json.dump(self._flight_memory, f, indent=2)

    def load_flight(self, fn:str):
        """ Load flight memory from file JSON """
        import json

        if exists(fn):
            with open(fn,'r') as f:
                self._flight_memory = json.load(f)


    def _callback_props(self):

        self._update_viewer()

    def _callback_destroy_props(self):

        if self._myprops is not None:
            # self._callback_props()
            self._myprops.Destroy()
            self._myprops = None

    def _create_props(self):
        """ Create properties Wolf_Param for LAZ data """

        if self._myprops is not None:
            return

        self._myprops = Wolf_Param(None, title=_('Properties of ') + self.idx,
                            to_read=False, force_even_if_same_default= True)

        props = self._myprops

        props.set_callbacks(self._callback_props, self._callback_destroy_props)
        props.hide_selected_buttons()


        ret = props.addparam('Camera', 'X', self.eye[0], Type_Param.Float, 'eye_x')
        ret = props.addparam('Camera', 'Y', self.eye[1], Type_Param.Float, 'eye_y')
        ret = props.addparam('Camera', 'Z', self.eye[2], Type_Param.Float, 'eye_z')

        ret = props.addparam('Look at', 'X', self.lookat[0], Type_Param.Float, 'lookat_x')
        ret = props.addparam('Look at', 'Y', self.lookat[1], Type_Param.Float, 'lookat_y')
        ret = props.addparam('Look at', 'Z', self.lookat[2], Type_Param.Float, 'lookat_z')

        ret = props.addparam('Relative Position', 'Phi', self.phi, Type_Param.Float, 'azimuthal angle (radians) - (phi, theta, r) are spherical coordinates specifying camera position relative to the look at position.')
        ret = props.addparam('Relative Position', 'Theta', self.theta, Type_Param.Float, 'elevation angle (radians) - (phi, theta, r) are spherical coordinates specifying camera position relative to the look at position.')
        ret = props.addparam('Relative Position', 'R', self.r, Type_Param.Float, 'distance to look-at point - (phi, theta, r) are spherical coordinates specifying camera position relative to the look at position.')

        ret = props.addparam('Background', 'Color', self._bg_color, Type_Param.Color, 'Background color')
        ret = props.addparam('Background', 'Top Color', self._bg_color_top, Type_Param.Color, 'Top Background color')
        ret = props.addparam('Background', 'Bottom Color', self._bg_color_bottom, Type_Param.Color, 'Bottom Background color')

        ret = props.addparam('Floor', 'Level', self._floor_level, Type_Param.Float, 'Floor level')
        ret = props.addparam('Floor', 'Color', self._floor_color, Type_Param.Color, 'Floor color')

        # ret = props.addparam('Infos', 'Grid', self._show_grid, Type_Param.Logical, 'Show grid')
        # ret = props.addparam('Infos', 'Axis', self._show_axis, Type_Param.Logical, 'Show axis')
        # ret = props.addparam('Infos', 'values', self._show_info, Type_Param.Logical, 'Show info')

        ret = props.addparam('Points', 'Size', self._point_size, Type_Param.Float, 'Point size')

        codes_sel = ''
        for curcode in self._select_only_codes:
            codes_sel += str(curcode) + ','
        ret = props.addparam('Selection', 'Codes', codes_sel, Type_Param.String, 'Codes to select')

        props.Populate()

        updatebutton = wx.Button(props, label=_('Get from viewer'))
        props.sizerbut.Add(updatebutton,1,wx.EXPAND)
        updatebutton.Bind(wx.EVT_BUTTON, self._fill_props)

        getselection = wx.Button(props, label=_('Edit selection'))
        props.sizerbut.Add(getselection,1,wx.EXPAND)
        getselection.Bind(wx.EVT_BUTTON, self._OnEdit_Selection)

        props.Layout()

    def _set_new_xls(self):
        """ Create a new Excel grid for selected data """

        self._xlsFrame = wx.Frame(None, wx.ID_ANY, _('Selected points - ') + self.idx)
        self._xls = CpGrid(self._xlsFrame, wx.ID_ANY, style = wx.WANTS_CHARS)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._xls, 1, wx.EXPAND)

        nbclass = len(self.classification.classification)
        self._xls.CreateGrid(10, 4)

        # Add a button to plot a histogram
        but_sizer = wx.BoxSizer(wx.HORIZONTAL)
        plotbutton = wx.Button(self._xlsFrame, label=_('Plot histogram (All data)'))
        but_sizer.Add(plotbutton, 1, wx.EXPAND)
        plotbutton.Bind(wx.EVT_BUTTON, self.OnPlot_histogram)

        plotbutton2 = wx.Button(self._xlsFrame, label=_('Plot histogram (Grid data)'))
        but_sizer.Add(plotbutton2, 1, wx.EXPAND)
        plotbutton2.Bind(wx.EVT_BUTTON, self.OnPlot_histogram_grid)

        sizer.Add(but_sizer, 0, wx.EXPAND)

        self._xlsFrame.SetSizer(sizer)
        self._xlsFrame.Layout()
        self._xlsFrame.Show()

        icon = wx.Icon()
        icon_path = Path(__file__).parent.parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        self._xlsFrame.SetIcon(icon)

    def OnPlot_histogram(self, event:wx.MouseEvent):
        """ Plot histogram of selected data """
        self._plot_histogram()

    def OnPlot_histogram_grid(self, event:wx.MouseEvent):
        """ Plot histogram of selected data """
        self._plot_histogram_grid()

    def _plot_histogram_grid(self):
        """ Histogram ONLY of selected data in grid.

        The data are extracted based on the first column of the grid
        untile an empty cell is found.
        """

        xls = self._xls

        if xls is None:
            logging.warning(_('No Excel grid'))
            return

        # Find not null cells
        nbrows = 1

        while xls.GetCellValue(nbrows,0) != '' and nbrows < xls.NumberRows:
            nbrows += 1

        if nbrows == 1:
            logging.warning(_('Nt enough points selected'))
            return

        xyz = np.zeros((nbrows,3))
        codes = np.zeros(nbrows)

        try:
            for i in range(nbrows):
                xyz[i,0] = float(xls.GetCellValue(i,0))
                xyz[i,1] = float(xls.GetCellValue(i,1))
                xyz[i,2] = float(xls.GetCellValue(i,2))
                codes[i] = float(xls.GetCellValue(i,3))
        except Exception as e:
            logging.error(e)
            logging.warning(_('Bad values in grid - Check your input'))
            return

        fig = plt.figure()

        ax = fig.add_subplot(111)

        ax.hist(xyz[:,2], bins=256)

        fig.show()

    def _plot_histogram(self):
        """ """

        xyz = self.xyz_selected

        if xyz.shape[0]==0:
            logging.warning(_('No points selected'))
            return

        fig = plt.figure()

        ax = fig.add_subplot(111)

        ax.hist(xyz[:,2], bins=256)

        fig.show()

    def _selection2vector(self):
        """ FIXME: must use RANSAC to compute a segment from the selected points """

        if self.viewer is None:
            logging.warning(_('No viewer'))
            return

        xyz = self.xyz_selected

        if xyz.shape[0]==0:
            logging.warning(_('No points selected'))
            return

        vect = vector(name = self.idx + '_selection', fromnumpy=xyz)

        return vect


    def _OnEdit_Selection(self, event:wx.MouseEvent):
        """ Get selection from viewer and create a XLS grid """
        self._edit_selection()

    def _edit_selection(self):

        if self.viewer is None:
            logging.warning(_('No viewer'))
            return

        xyz = self.xyz_selected

        if xyz.shape[0]==0:
            logging.warning(_('No points selected'))
            return

        if self._xls is None:
            self._set_new_xls()
        else:
            try:
                self._xls.ClearGrid()
            except:
                #Useful if the grid is already destroyed
                self._set_new_xls()

        nbclass = len(self.classification.classification)
        min_rows = xyz.shape[0] + nbclass +1
        if self._xls.NumberRows < min_rows:
            self._xls.AppendRows(min_rows - self._xls.NumberRows)

        self._xls.SetColLabelValue(0, 'X')
        self._xls.SetColLabelValue(1, 'Y')
        self._xls.SetColLabelValue(2, 'Z')
        self._xls.SetColLabelValue(3, 'Code')

        codes = self.code_selected

        for i in range(xyz.shape[0]):
            self._xls.SetCellValue(i,0,str(xyz[i,0]))
            self._xls.SetCellValue(i,1,str(xyz[i,1]))
            self._xls.SetCellValue(i,2,str(xyz[i,2]))
            self._xls.SetCellValue(i,3,str(codes[i]))

        # Copy classification under the values
        for i, (key, val) in enumerate(self.classification.classification.items()):
            self._xls.SetCellValue(xyz.shape[0]+i+1,0,str(key))
            self._xls.SetCellValue(xyz.shape[0]+i+1,1,val[0])
            self._xls.SetCellValue(xyz.shape[0]+i+1,2,val[1])
            self._xls.SetCellValue(xyz.shape[0]+i+1,3,str(key))

        self._xlsFrame.Show()

        # Mettre la fenêtre au premier plan et centrée
        self._xlsFrame.Raise()
        self._xlsFrame.Center()

    def _update_viewer(self):
        """ Update the viewer with properties """

        if self._myprops is None:
            return

        if self.viewer is None:
            return

        props = self._myprops

        self.lookat = (props[('Look at', 'X')], props[('Look at', 'Y')], props[('Look at', 'Z')])
        # self.eye = (props[('Camera', 'X')], props[('Camera', 'Y')], props[('Camera', 'Z')])

        color = np.asarray(props[('Background', 'Color')])
        self.bg_color(color / 255.)
        color = np.asarray(props[('Background', 'Top Color')])
        self.bg_color_top(color / 255.)
        color = np.asarray(props[('Background', 'Bottom Color')])
        self.bg_color_bottom(color / 255.)

        self.floor_level(props[('Floor', 'Level')])
        color = np.asarray(props[('Floor', 'Color')])
        self.floor_color(color / 255.)

        # self.show_grid(props[('Infos', 'Grid')])
        # self.show_axis(props[('Infos', 'Axis')])
        # self.show_info(props[('Infos', 'values')])

        self.point_size = props[('Points', 'Size')]

        codes_sel = props[('Selection', 'Codes')]
        codes_sel = codes_sel.split(',')
        try:
            self._select_only_codes = list(set([int(curcode) for curcode in codes_sel]))
        except Exception as e:
            logging.error(e)
            logging.warning(_('Nullify selection filter - Check your input - Must be a list of integers separated by commas'))
            self._select_only_codes = []

    def _fill_props(self, full:bool = False):
        """ Fill properties from attributes """
        if self._myprops is None:
            return

        props = self._myprops

        props[('Look at', 'X')] = self.lookat[0]
        props[('Look at', 'Y')] = self.lookat[1]
        props[('Look at', 'Z')] = self.lookat[2]

        props[('Camera', 'X')] = self.eye[0]
        props[('Camera', 'Y')] = self.eye[1]
        props[('Camera', 'Z')] = self.eye[2]

        props[('Relative Position', 'Phi')] = self.phi
        props[('Relative Position', 'Theta')] = self.theta
        props[('Relative Position', 'R')] = self.r

        if full:

            props[('Background', 'Color')] = self._bg_color
            props[('Background', 'Top Color')] = self._bg_color_top
            props[('Background', 'Bottom Color')] = self._bg_color_bottom

            props[('Floor', 'Level')] = self._floor_level
            props[('Floor', 'Color')] = self._floor_color

            # props[('Infos', 'Grid')] = self._show_grid
            # props[('Infos', 'Axis')] = self._show_axis
            # props[('Infos', 'values')] = self._show_info

            props[('Points', 'Size')] = self._point_size

        props.Populate()

    def show_properties(self):
        """ Surcharged method (see Element_To_Draw) to show properties from MapViewer"""
        if self.viewer is None:
            logging.info(_('No viewer / No properties'))
            return

        # test if a connexion exists
        try:
            lookat = self.viewer.get('lookat')
        except:
            self.viewer = None
            logging.info(_('No viewer / No properties'))
            return

        self._create_props()
        self._myprops.Show()

def find_pointsXYZ(xyz:np.ndarray, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]) -> np.ndarray:

    xb=bounds[0]
    yb=bounds[1]
    # Get arrays which indicate invalid X, Y, or Z values.
    X_valid = np.logical_and((xb[0] <= xyz[:,0]), (xb[1] >= xyz[:,0]))
    Y_valid = np.logical_and((yb[0] <= xyz[:,1]), (yb[1] >= xyz[:,1]))
    good_indices = np.where(X_valid & Y_valid)[0]

    return xyz[good_indices]

def find_points(las:laspy.LasData, xb:list[float, float], yb:list[float, float]) -> laspy.LasData:
    """Get arrays which indicate invalid X, Y, or Z values"""

    X_valid = (xb[0] <= las.x) & (xb[1] >= las.x)
    Y_valid = (yb[0] <= las.y) & (yb[1] >= las.y)

    good_indices = np.where(X_valid & Y_valid)[0]
    if len(good_indices)>0:
        return las[good_indices]
    else:
        return None


def read_laz(fn:str, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]] = None) -> Union[np.ndarray,laspy.LasData]:
    """  Lecture d'un fichier LAZ, LAS ou NPZ """
    if exists(fn):

        if fn.endswith('.npz'):
            return np.load(fn)['arr_0']

        elif fn.endswith('.laz') or fn.endswith('.las'):
            if exists(fn):
                with laspy.open(fn,laz_backend=LazBackend.Laszip) as f:
                    laz = f.read()
                    if bounds is None:
                        return laz
                    else:
                        return find_points(laz, bounds[0], bounds[1])
    else:
        return None

def xyzlaz_scandir(mydir:str, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]):
    """ Scan for XYZ files """
    first=[]
    for curfile in listdir(mydir):
        if curfile.endswith('.bin'):
            mydata = xyz_laz(join(mydir,curfile), format='numpy', to_read=False)
            if mydata.test_bounds(bounds):
                print(curfile)
                mydata.read_bin_xyz()
                first.append(mydata.data)

    for entry in scandir(mydir):
        if entry.is_dir():
            locf=xyzlaz_scandir(entry,bounds)
            if len(locf)>0:
                first.append(locf)

    data=[]

    if len(first)>0:
        data=find_pointsXYZ(np.concatenate(first),bounds)

    return data

def laz_scandir(mydir:str, bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]) -> list[laspy.LasData]:
    """  Scan directory and treat .laz files """
    ret=[]

    for curfile in listdir(mydir):
        if curfile.endswith('.laz'):
            print(curfile)

            mydata = read_laz(join(mydir,curfile))
            mydata = find_points(mydata, bounds[0], bounds[1])

            if mydata is not None:
                if mydata.header.point_count>0:
                    ret.append(mydata)

    return ret

def clip_data_xyz(dir_in:str,
                  fn_out:str,
                  bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]]):
    """  Get data and write zip numpy file """

    myxyz = xyzlaz_scandir(dir_in, bounds)

    np.savez_compressed(fn_out,myxyz)

    return fn_out

def clip_data_laz(fn_in:str,
                  fn_out:str,
                  bounds:Union[tuple[tuple[float,float],tuple[float,float]], list[list[float, float],list[float, float]]],
                  chunksize:int=5000000):
    pts=[]
    k=0
    xbounds=bounds[0]
    ybounds=bounds[1]

    with laspy.open(fn_in,laz_backend=LazBackend.Laszip) as f:
        nb = (f.header.point_count // chunksize) +1
        print('Points from Header:', f.header.point_count)
        with laspy.open(fn_out, mode="w", header=f.header) as writer:
            for las in f.chunk_iterator(chunksize):
                print(k,' / ',nb)
                mypts=find_points(las,xbounds,ybounds)
                if len(mypts)>0:
                    pts.append(mypts)
                    print(len(mypts))
                    writer.write_points(mypts)
                k+=1
                print('--')
    pts=[]

def get_concat_h(im1:Image.Image, im2:Image.Image):
    """ Concatenate 2 images horizontally """
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst

def get_concat_v(im1:Image.Image, im2:Image.Image):
    """ Concatenate 2 images vertically """
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst

def get_Orthos_Walonmap(bounds, fn, cat='IMAGERIE/ORTHO_2012_2013',size=3000):
    """
    Récupération des orthos depuis Walonmap
    fn = filename sans extension --> .png sera ajouté automatiquement

    catégories possibles :
     - 'IMAGERIE/ORTHO_2012_2013'
     - 'IMAGERIE/ORTHO_2015'
     - 'IMAGERIE/ORTHO_2021'
     - 'IMAGERIE/ORTHO_2006_2007'
    """

    resmin=.3
    xbounds=bounds[0]
    ybounds=bounds[1]
    dx = xbounds[1]-xbounds[0]
    dy = ybounds[1]-ybounds[0]

    sizex=size
    sizey=size
    if dx>dy:
        sizey=math.ceil(float(size)*float(dy/dx))
    elif dx<dy:
        sizex=math.ceil(float(size)*float(dx/dy))

    resx = dx/float(size)
    resy = dy/float(size)

    if resx<=resmin and resy <=resmin:
        try:
            im = Image.open(getWalonmap(cat,xbounds[0],ybounds[0],xbounds[1],ybounds[1],sizex,sizey,tofile=False))
        except:
            im = Image.open(getWalonmap(cat,xbounds[0],ybounds[0],xbounds[1],ybounds[1],sizex/2,sizey/2,tofile=False))
    elif resx>resmin and resy <=resmin:
        nbx = math.ceil(resx/resmin)
        liste=[]
        x1=xbounds[0]
        dx = dx/float(nbx)
        for i in range(nbx):
            liste.append(Image.open(getWalonmap(cat,x1,ybounds[0],x1+dx,ybounds[1],sizex,sizey,tofile=False)))
            sleep(.5)
            x1+=dx
        im = liste[0]
        for i in range(1,nbx):
            im = get_concat_h(im,liste[i])
    elif resx<=resmin and resy >resmin:
        nby= math.ceil(resy/resmin)
        liste=[]
        y1=ybounds[0]
        dy = dy/float(nby)
        for j in range(nby):
            liste.append(Image.open(getWalonmap(cat,xbounds[0],y1,xbounds[1],y1+dy,sizex,sizey,tofile=False)))
            sleep(.5)
            y1+=dy
        im = liste[0]
        for j in range(1,nby):
            im = get_concat_v(liste[j],im)
    elif resx>resmin and resy >resmin:
        nbx = math.ceil(resx/resmin)
        nby = math.ceil(resy/resmin)

        liste=[]

        x1=xbounds[0]
        y1=ybounds[0]

        dx = dx/float(nbx)
        dy = dy/float(nby)

        print('Awaiting image from Walonmap - be patient !')
        for i in range(nbx):
            liste.append([])
            y1=ybounds[0]
            for j in range(nby):
                liste[i].append(Image.open(getWalonmap(cat,x1,y1,x1+dx,y1+dy,sizex,sizey,tofile=False)))
                y1+=dy
                print(str(i)+'/'+str(nbx-1)+' -- '+str(j)+'/'+str(nby-1))
                sleep(.5)
            x1+=dx
            print('--')

        for i in range(nbx):
            im = liste[i][0]
            for j in range(1,nby):
                im = get_concat_v(liste[i][j],im)
            liste[i][0]=im

        im = liste[0][0]
        for i in range(1,nbx):
            im = get_concat_h(im,liste[i][0])

    Image.Image.save(im,fn +'.png')
    with open(fn+'.png_bounds.txt','w') as f:
        f.write(str(xbounds[0])+','+str(xbounds[1])+'\n')
        f.write(str(ybounds[0])+','+str(ybounds[1]))

def get_colors(las:laspy.LasData, which_colors:Colors_Lazviewer, imsize=2000, fname='', palette_classif: Classification_LAZ = None):

    curlas:laspy.LasData

    if type(las) is laspy.LasData:
        nb = las.header.point_count
    elif type(las) is list:
        nb=0
        for curlas in las:
            nb += curlas.header.point_count
    else:
        nb = len(las)

    colors=np.ones((nb,4),dtype=np.float32)

    if type(which_colors) == Colors_Lazviewer:
        which_colors = which_colors.value

    if which_colors==Colors_Lazviewer.CODE_2013.value:
        """
        - Hors-sol (building, toits et autres) - Code 1;
        - Sol (y compris talus et digues) - Code 2;
        - Végétation haute (y compris la végétation linéaire) - Code 4;
        - Eau - Code 9;
        - Pont – Code 10.
        """
        if type(las) is laspy.LasData:
            myclass = las.classification
        elif type(las) is list:
            myclass=[]
            for curlas in las:
                myclass.append(curlas.classification)
            myclass = np.concatenate(myclass)
        else:
            myclass = np.int8(las[:,3])

        if palette_classif is None:
            palette_classif = Classification_LAZ()
            palette_classif.init_2013()

        for key, value in palette_classif.classification.items():
            name, comment, color = value
            colors[myclass==int(key)] = color

    elif which_colors==Colors_Lazviewer.CODE_2021_2022.value:
        """
        - Rebus/non classés - Code 0;
        - Hors-sol (building, toits et autres) - Code 1;
        - Sol (y compris talus et digues) - Code 2;
        - Végétation haute (y compris la végétation linéaire) - Code 4;
        - Eau - Code 9;
        - Pont – Code 10;
        - Ligne hautes-tension - Code 15.
        """
        if type(las) is laspy.LasData:
            myclass = las.classification
        elif type(las) is list:
            myclass=[]
            for curlas in las:
                myclass.append(curlas.classification)
            myclass = np.concatenate(myclass)
        else:
            myclass = np.int8(las[:,3])

        if palette_classif is None:
            palette_classif = Classification_LAZ()
            palette_classif.init_2021_2022()

        for key, value in palette_classif.classification.items():
            name, comment, color = value
            colors[myclass==int(key)] = color

    elif which_colors==Colors_Lazviewer.CODE_2023.value:

        if palette_classif is None:
            palette_classif = Classification_LAZ()
            palette_classif.init_2023()

        """
        - Defaut                - Code 1;           Voiture, câbles électrique, points de végétation diffus, Sursol non utile…
        - Sol                   - Code 2;           Tous les éléments du sol y compris les descentes de garage en sous-sol
        - Végétation            - Code 4;           Végétation
        - Bâtiments             - Code 6;           Bâtiments
        - Eau                   – Code 9;           Points de la surface d’eau brute mesurés par le scanner 2
        - Ponts                 – Code 10;          Les ponts ont été classés à part pour améliorer la définition du MNT. Ils ont été ouverts grâce
        - Mur de berge          – Code 11;          Mur et muret en berge de la Vesdre dépassant le sol à des vocation de réaliser une modélisation 3D hydraulique avec ces obstacles.
        - Tranche d'eau         – Code 15;          Echo intermédiaire dans l’eau n’appartenant ni à la surface d’eau ni au fond du lit
        - Surface bathymétrique – Code 16;          Fond du lit de la Vesdre et de ses affluents et des autres surfaces d’eau mesurées à partir du scanner 3 FWF discrétisé
        - Surface bathymétrique incertaine - Code 17    Surface bathymétrique sur les zones peu profondes principalement sous végétation où les intensités des échos sont parfois trop faibles pour avoir la certitude qu’ils représentent le fond de rivière. La classe 17 est néanmoins plus certaine que la classe 18. Elle est utilisée dans la génération des MNT par défaut.
        - Surface d'eau calculée - Code 19          Points sous échantillonnés de la surface d’eau ayant servis à faire les calculs de correction de réfraction bathymétrique
        - Surface bathymétrique incertaine profonde – Code 20;  Surface bathymétrique sur les zones plus profondes principalement au centre de la rivière où les intensités des échos sont parfois trop faibles pour avoir la certitude qu’ils représentent le fond de rivière. Non utilisée dans la génération du MNT. + Surface proche bathy mais potentiellement émergée pour les scanner 1 à 3
        - Surface d'eau héliportée – Code 29;       La hauteur d’eau du vol héliporté étant largement supérieure (de 30 à 40cm au vol Titan, les points matérialisant cette surface ont été reclassés dans cette classe séparée pour ne pas perturbé le reste du nuage de point.
        """

        if type(las) is laspy.LasData:
            myclass = las.classification
        elif type(las) is list:
            myclass=[]
            for curlas in las:
                myclass.append(curlas.classification)
            myclass = np.concatenate(myclass)
        else:
            myclass = np.int8(las[:,3])

        for key, value in palette_classif.classification.items():
            name, comment, color = value
            colors[myclass==int(key)] = color

    elif which_colors==Colors_Lazviewer.FROM_FILE.value and fname != '':
        im=Image.open(fname)
        width = im.width
        height = im.height

        if exists(fname+'_bounds.txt'):
            with open((fname+'_bounds.txt'),'r') as f:
                mylines=f.read().splitlines()
                xb = np.float64(mylines[0].split(','))
                yb = np.float64(mylines[1].split(','))

        myPPNC = np.asarray(im)

        if type(las) is laspy.LasData:
            x = las.x
            y = las.y
        elif type(las) is list:
            xy=[]
            for mypts in las:
                xy.append(np.vstack((mypts.x,mypts.y)).transpose())
            xy=np.concatenate(xy)
            x=xy[:,0]
            y=xy[:,1]
        else:
            x = las[:,0]
            y = las[:,1]

        i = np.int16((x-xb[0])/(xb[1]-xb[0])*(width-1))
        j = np.int16((yb[1]-y)/(yb[1]-yb[0])*(height-1))

        jmax,imax,_ = myPPNC.shape
        i[np.where(i<0)]=0
        j[np.where(j<0)]=0
        i[np.where(i>=imax)]=imax-1
        j[np.where(j>=jmax)]=jmax-1

        # print(np.max(i),np.max(j))
        colors[:,:3]=myPPNC[j,i]/255.

    else:
        if which_colors==Colors_Lazviewer.ORTHO_2012_2013.value:
            mycat='IMAGERIE/ORTHO_2012_2013'
        elif which_colors==Colors_Lazviewer.ORTHO_2015.value:
            mycat='IMAGERIE/ORTHO_2015'
        elif which_colors==Colors_Lazviewer.ORTHO_2021.value or which_colors is None:
            mycat='IMAGERIE/ORTHO_2021'
        elif which_colors==Colors_Lazviewer.ORTHO_2006_2007.value:
            mycat='IMAGERIE/ORTHO_2006_2007'
        elif which_colors==Colors_Lazviewer.ORTHO_2023.value:
            mycat='IMAGERIE/ORTHO_2023_ETE'

        if type(las) is laspy.LasData:
            x = las.x
            y = las.y
        elif type(las) is list:
            xy=[]
            for mypts in las:
                xy.append(np.vstack((mypts.x,mypts.y)).transpose())
            xy=np.concatenate(xy)
            x=xy[:,0]
            y=xy[:,1]
        else:
            x = las[:,0]
            y = las[:,1]

        mins = np.amin(np.vstack((x,y)).transpose(),axis=0)
        maxs = np.amax(np.vstack((x,y)).transpose(),axis=0)

        width = min(int((maxs[0]-mins[0])/.3),imsize)
        height = min(int((maxs[1]-mins[1])/.3),imsize)

        im = Image.open(getWalonmap(mycat,mins[0],mins[1],maxs[0],maxs[1],width,height,tofile=False))
        myPPNC = np.asarray(im)

        i = np.int16((x-mins[0])/(maxs[0]-mins[0])*float(width -1))
        j = np.int16((maxs[1]-y)/(maxs[1]-mins[1])*float(height-1))

        jmax,imax,_ = myPPNC.shape
        i[np.where(i<0)]=0
        j[np.where(j<0)]=0
        i[np.where(i>=imax)]=imax-1
        j[np.where(j>=jmax)]=jmax-1

        colors[:,:3]=myPPNC[j,i,:3]/255.

    return colors

def myviewer(las:Union[np.ndarray, list[laspy.LasData], laspy.LasData], which_colors:Colors_Lazviewer, fname='', palette_classif:Classification_LAZ = None):
    """ Get viewer for las data """

    if type(las) is list:
        xyz=[]
        for mypts in las:
            xyz.append(np.vstack((mypts.x,mypts.y,mypts.z)).transpose())

        xyz=np.concatenate(xyz)

    elif type(las) is laspy.LasData:
        xyz = np.vstack((las.x,las.y,las.z)).transpose()

    else:
        assert las.shape[1]>2
        xyz=las[:,:3]

    colors = get_colors(las, which_colors, fname=fname, palette_classif= palette_classif)

    v = viewer(xyz,colors)
    v.set(point_size=.05)
    return v

if __name__ == '__main__':
    # # création des fichiers

    grids = xyz_laz_grids(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\LAZ_Vesdre\2023\grids_flt32', True)

    grids.create_from_laz(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\LAZ_Vesdre\2023\LAZ',
                          shape=r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\2023\Tableau_d_assemblage_v3\Vesdre_Tableau_d_Assemblage_L72.shp',
                          force_format=np.float32)

    # mygrids = xyz_laz_grids(r'D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\LAZ_Vesdre\2023\grids')

    # xyz = mygrids.scan([[252500, 252700],[136400,136500]])
    # newview = myviewer(xyz,2021)
    pass