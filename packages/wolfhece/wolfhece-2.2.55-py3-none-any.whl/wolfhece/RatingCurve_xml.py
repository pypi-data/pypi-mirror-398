"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from scipy.optimize import curve_fit, root_scalar
import xmltodict
import pandas as pd
from sympy import *
from datetime import datetime, timedelta
import glob
import logging
import os.path as path
from typing import Literal, Union
from pathlib import Path
from itertools import cycle
from enum import Enum

from .PyTranslate import _
try:
    from .hydrometry_hece.kiwis_hece import hydrometry_hece as hydrometry
except:
    logging.debug(_('Hydrometry HECE module not found - Load hydrometry instead of hydrometry_hece'))
    from .hydrometry.kiwis import hydrometry

# FONCTIONS UTILES pour FIT
# -------------------------
def get_power_law():
    return lambda x,a,b,c : a*(x-c)**b

def get_power_law_(*args):
    a,b,c = args[0]
    return lambda x : a*(x-c)**b

def get_poly3_law():
    return lambda x,a,b,c,d : a*x**3.+b*x**2.+c*x+d

def get_poly3_law_(*args):
    a,b,c,d = args[0]
    return lambda x : a*x**3.+b*x**2.+c*x+d

def get_poly2_law():
    return lambda x,a,b,c : a*x**2.+b*x+c

def get_poly2_law_(*args):
    a,b,c = args[0]
    return lambda x : a*x**2.+b*x+c

class laws(Enum):
    poly2 = (get_poly2_law , get_poly2_law_)
    poly3 = (get_poly3_law, get_poly3_law_)
    power = (get_power_law, get_power_law_)


class Gauging():
    """ Class pour un jaugeage """

    date:datetime
    waterdepth:float
    discharge:float
    width:float
    wet_area:float
    wet_perimeter:float

    def __init__(self,
                 date:datetime,
                 waterdepth:float,
                 discharge:float,
                 wet_area:float = np.nan,
                 width:float = np.nan,
                 wet_perimeter:float = np.nan ) -> None:
        """ Initialisation d'un jaugeage

        :param date: date du jaugeage
        :param waterdepth: hauteur d'eau
        :param discharge: débit
        :param wet_area: aire mouillée
        :param width: largeur
        :param wet_perimeter: périmètre mouillé

        """
        self.date   = date
        self.waterdepth= waterdepth
        self.discharge  = discharge

        self.wet_area = wet_area
        self.width = width
        self.wet_perimeter = wet_perimeter

class FragmentCurve():
    """ Fragment de courbe de tarage """

    expression:str
    h_min:float
    h_max:float
    river:str

    def __init__(self, expression:Union[str, Function], h_min:float, h_max:float, river:str=None) -> None:
        """ Initialisation d'un fragment de courbe de tarage

        :param expression: expression analytique de la courbe -- chaîne de caractères ou fonction
        :param h_min: hauteur minimale
        :param h_max: hauteur maximale
        :param river: nom de la rivière

        """
        self.h_min = float(h_min)
        self.h_max = float(h_max)
        self.river = river

        if isinstance(expression, str):
            #test si l'expression analytique a la forme d'une puissance
            if expression[0:3]=='rem':
                l=expression.find('=',30)
                expression=expression[l+1:]

            self.expression = expression

            x=symbols('x')
            string_function=expression.replace("^","**")
            strfunc = parse_expr(string_function)
            func = lambdify(x,strfunc)
        else:
            func = expression
            self.expression = None

        self.func = func

    def plot_frag(self, figax=None, ls='solid', color='k'):
        """
        Graphique du fragment de courbe de tarage

        :param figax: figure et axes matplotlib (optionel) -- si non fourni, une nouvelle figure est créée
        :param ls: style de ligne (optionel) -- solide par défaut
        :param color: couleur de la courbe (optionel) -- noir par défaut
        """

        if figax is None:
            fig,ax = plt.subplots(1,1)
        else:
            fig,ax = figax

        m=np.linspace(self.h_min,self.h_max,100)
        y=self.func(m)

        if isinstance(m, float):
            pass
        if isinstance(y, float):
            pass

        #plot courbes de tarage
        ax.plot(m, y, ls=ls, c=color)

        qhmax = self.func(self.h_max)
        ax.plot([self.h_max, self.h_max],[min(qhmax*.9,qhmax-5.), max(qhmax*.9,qhmax+5.)], ls='--', color='k')

        return fig,ax

class RatingCurve():
    """ Class pour les courbes de tarage """

    date_start:datetime
    date_end:datetime
    fragments:list[FragmentCurve]
    active:bool

    def __init__(self, date_start:datetime, date_end:datetime, active:bool=True) -> None:
        """ Initialisation de la courbe de tarage

        :param date_start: date de début de validité
        :param date_end: date de fin de validité
        :param active: courbe active ou non

        """

        self.date_start = date_start
        self.date_end   = date_end
        self.fragments  = []
        self.active     = active

    def add(self, expression:Union[str, Function], h_min:float, h_max:float):
        """
        Ajout d'un fragment de courbe de tarage

        :param expression: expression analytique de la courbe -- chaîne de caractères ou fonction
        :param h_min: hauteur minimale
        :param h_max: hauteur maximale

        """

        self.fragments.append(FragmentCurve(expression, h_min, h_max))

    def plot_curve(self, figax=None, color='k'):
        """
        Graphique de la courbe de tarage

        :param figax: figure et axes matplotlib (optionel) -- si non fourni, une nouvelle figure est créée
        :param color: couleur de la courbe (optionel) -- noir par défaut

        """

        if figax is None:
            fig,ax = plt.subplots(1,1)
        else:
            fig,ax = figax

        ls = 'solid' if self.active else '--'

        for cur_frag in self.fragments:

            cur_frag.plot_frag((fig,ax), ls=ls, color=color)

        ax.get_lines()[-2].set_label(self.date_start.strftime('%Y-%m-%d') + ' - ' + self.date_end.strftime('%Y-%m-%d'))

        return fig,ax

    def compute_q_from_h(self, h:pd.Series) -> pd.Series:
        """
        Conversion mesure de hauteur H en débit Q

        :param h: série Pandas de hauteur H

        :return: série Pandas de débit Q

        """

        q = h.copy(True) #copir de la série
        for curfrag in self.fragments:
            #bouclage sur les fragemets
            q[(h >= curfrag.h_min) & (h <= curfrag.h_max)] = curfrag.func(h[(h >= curfrag.h_min) & (h <= curfrag.h_max)])
        return q

    def compute_h_from_q(self, q:pd.Series) -> pd.Series:
        """
        Conversion mesure de débit Q en Hauteur H

        :param q: série Pandas de débit Q

        :return: série Pandas de hauteur H

        """

        h = q.copy(True)
        for curfrag in self.fragments:
            #bouclage sur les fragemets

            #bornes en terme de Q
            qmin = curfrag.func(curfrag.h_min)
            qmax = curfrag.func(curfrag.h_max)

            # fonction à résoudre
            def hq(h, qobj):
                return curfrag.func(h)-qobj

            # résolution inverse du fragment
            hroots = [root_scalar(hq,
                                args=curq,
                                method='brentq',
                                bracket=[curfrag.h_min, curfrag.h_max]).root
                                for curq in h[(q >= qmin) & (q<=qmax)]]

            h[(q >= qmin) & (q<=qmax)] = hroots
        return h

class StationCurvesGaugings():
    """
    Une station avec courbes de tarage et jaugeages
    """

    curves:list[RatingCurve]
    gaugings:list[Gauging]

    def __init__(self, filename:str | Path = None) -> None:

        filename = str(filename) if filename is not None else None

        self.code = None        # code de la station
        self.href = None        # altitude de référence
        self.hydrometry = None  # lien vers une instance de la classe hydrometry

        self.gaugings = []      # liste des jaugeages
        self.curves   = []      # liste des courbes de tarage

        self.name = ''          # nom de la station
        self.code = ''          # code de la station

        if filename is not None:
            if filename.endswith('.xml'):
                # seul les frichiers xml sont acceptés comme données individuelles (extraction de la BDD Kiwis -> DCENN)
                # le SPW-MI fournit plutôt un Excel regroupant toutes les stations dans un même fichier
                self._read_xml(filename)

    def __str__(self) -> str:
        """ Affichage des infos de la station """

        txt = f'Station {self.name} - {self.code}\n\n'
        txt += f'Courbes de tarage: {len(self.curves)}\n'
        txt += f'Jaugeages: {len(self.gaugings)}\n'
        txt += f'Altitude de référence: {self.href}\n'
        # txt += '\n\n'

        # txt += 'Courbes de tarage:\n'
        # for cur_curve in self.curves:
        #     txt += f'- {cur_curve.date_start.strftime("%Y-%m-%d")} - {cur_curve.date_end.strftime("%Y-%m-%d")}\n'
        # txt += '\nJaugeages:\n'
        # for cur_gauging in self.gaugings:
        #     txt += f'- {cur_gauging.date.strftime("%Y-%m-%d")} - {cur_gauging.waterdepth} - {cur_gauging.discharge}\n'

        return txt

    def get_href(self, hydrometry):
        """ Récupération de l'altitude de référence depuis le site hydrometrie.wallonie.be"""

        self.hydrometry = hydrometry
        if self.hydrometry is not None:
            self.href = self.hydrometry.get_gauge_datum(code = self.code)
        else:
            self.href = None

    def add_ratingcurve(self, rc:RatingCurve):
        """ Ajout d'une courbe de tarage """

        self.curves.append(rc)

    def _read_xml(self, file_xml:str):
        """
        Lecture des infos au format XML --> DCENN export KIWIS

        :remark: Si le format change, il faut adapter cette méthode
        """

        with open(file_xml) as fd:
            m = xmltodict.parse(fd.read())

        idd =m['KISTERSRatingcurve']['Station']['@Number']
        name=m['KISTERSRatingcurve']['Station']['@Name']

        periods = m['KISTERSRatingcurve']['Station']['Parameter']['Periods']['Period']
        if not isinstance(periods, list):
            periods = [periods]

        rc_list  = m['KISTERSRatingcurve']['Station']['Parameter']['Rc']
        if isinstance(rc_list, dict):
            rc_list = [rc_list]

        rc_names = [cur_rc['@Name'] for cur_rc in rc_list]

        for j in range(len(rc_names)-1):

            cur_name = rc_names[j]
            next_name = rc_names[j+1]

            for cur_period in periods:
                try:
                    if cur_period['@RatingName'] == cur_name:
                        break
                except:
                    pass
            for next_period in periods:
                try:
                    if next_period['@RatingName'] == next_name:
                        break
                except:
                    pass

            date_debut = datetime.strptime(cur_period['@Start'], '%Y-%m-%dT%H:%M:%S')
            date_fin   = datetime.strptime(next_period['@Start'], '%Y-%m-%dT%H:%M:%S')


            cur_rc = rc_list[rc_names.index(cur_name)]

            if isinstance(cur_rc['Version'], dict):
                cur_curve = RatingCurve(date_debut, date_fin)
                self.add_ratingcurve(cur_curve)
                parameters = cur_rc['Version']['TableParameterSet']['TableParameters']['TableParameter']

                for curparam in range(int(parameters[-1]['@Value'])):
                    expr = parameters[curparam + 1 + (curparam)*4]['@Value']
                    hmax = parameters[curparam + 1 + (curparam)*4+2]['@Value']
                    hmin = parameters[curparam + 1 + (curparam)*4+3]['@Value']

                    cur_curve.add(expr, hmin, hmax)
            else:
                for i in range(len(cur_rc['Version'])):
                    cur_curve = RatingCurve(date_debut, date_fin)
                    self.add_ratingcurve(cur_curve)
                    parameters = cur_rc['Version'][i]['TableParameterSet']['TableParameters']['TableParameter']

                    for curparam in range(int(parameters[-1]['@Value'])):
                        expr = parameters[curparam + 1 + (curparam)*4]['@Value']
                        hmax = parameters[curparam + 1 + (curparam)*4+2]['@Value']
                        hmin = parameters[curparam + 1 + (curparam)*4+3]['@Value']

                        cur_curve.add(expr, hmin, hmax)
                        cur_curve.active = cur_rc['Version'][i]['@Active'] =='true'

        j = len(rc_names)-1
        cur_name   = rc_names[j]
        for cur_period in periods:
            try:
                if cur_period['@RatingName'] == cur_name:
                    break
            except:
                pass

        date_debut = datetime.strptime(cur_period['@Start'], '%Y-%m-%dT%H:%M:%S')
        date_fin   = datetime.now()

        cur_rc = rc_list[rc_names.index(cur_name)]

        if  isinstance(cur_rc['Version'], dict):
            cur_curve = RatingCurve(date_debut, date_fin)
            self.curves.append(cur_curve)
            parameters = cur_rc['Version']['TableParameterSet']['TableParameters']['TableParameter']
            for curparam in range(int(parameters[-1]['@Value'])):
                expr = parameters[curparam + 1 + (curparam)*4]['@Value']
                hmax = parameters[curparam + 1 + (curparam)*4+2]['@Value']
                hmin = parameters[curparam + 1 + (curparam)*4+3]['@Value']

                cur_curve.add(expr, hmin, hmax)
        else:
            for i in range(len(cur_rc['Version'])):
                cur_curve = RatingCurve(date_debut, date_fin)
                self.curves.append(cur_curve)
                parameters = cur_rc['Version'][i]['TableParameterSet']['TableParameters']['TableParameter']

                for curparam in range(int(parameters[-1]['@Value'])):
                    expr = parameters[curparam + 1 + (curparam)*4]['@Value']
                    hmax = parameters[curparam + 1 + (curparam)*4+2]['@Value']
                    hmin = parameters[curparam + 1 + (curparam)*4+3]['@Value']

                    cur_curve.add(expr, hmin, hmax)
                    cur_curve.active = cur_rc['Version'][i]['@Active'] =='true'

        self.name = name
        self.code = idd

    def _read_gaugings(self, fichier_xls:str):
        """ Récupération des données de jaugeages sur base d'un fichier Excel """

        if not path.exists(fichier_xls):
            return
        if Path(fichier_xls).name[0]=='~':
            return

        doc=pd.read_excel(fichier_xls)

        if doc.iloc[0,0] == 'Date/Heure':
            # format du fichier Excel avec les colonnes Date/Heure, Hauteur, Débit
            doc.columns = ['Date/Heure', 'W [m]', 'Q [m³/s]']
            # pop the first line
            doc = doc.iloc[1:]
            # reindex the DataFrame
            doc.reset_index(drop=True, inplace=True)

        for i in range (len(doc[doc.columns[0]])):
            add_jaugeage=Gauging(doc[doc.columns[0]][i], doc[doc.columns[1]][i], doc[doc.columns[2]][i])
            self.gaugings.append(add_jaugeage)

    def get_periods(self):
        """Récupération des périodes de validité des courbes de tarage"""

        return [(cur_curve.date_start, cur_curve.date_end) for cur_curve in self.curves]

    def get_curves(self, date_debut:datetime=None, date_fin:datetime=None, only_active=True, only_last = False) -> list[RatingCurve]:
        """
        Récupération des courbes sur base de dates

        :param date_debut: date de début d'intervalle
        :param date_fin: date de fin d'intervalle
        :param only_active: ne prendre que les courbes actives (dépend si lu via xml ou xlsx)
        :param only_last: ne prendre que la dernière courbe encodée

        return: liste de courbes de tarage

        """
        if only_last:
            return [self.curves[-1]]
        else:
            if (date_debut is None) and (date_fin is None):
                if only_active:
                    useful_curves = [cur_curve for cur_curve in self.curves if cur_curve.active]
                else:
                    useful_curves = self.curves
            else:
                if only_active:
                    useful_curves = [cur_curve for cur_curve in self.curves if (cur_curve.date_start>= date_debut) and (cur_curve.date_end<= date_fin) and cur_curve.active]
                else:
                    useful_curves = [cur_curve for cur_curve in self.curves if (cur_curve.date_start>= date_debut) and (cur_curve.date_end<= date_fin)]

            return useful_curves

    def get_gaugings(self, date_debut:datetime=None, date_fin:datetime=None) -> list[Gauging]:
        """
        Récupération des jaugeages sur base de dates

        :param date_debut: date de début d'intervalle
        :param date_fin: date de fin d'intervalle

        return: liste de jaugeages

        """

        if (date_debut is None) and (date_fin is None):
            useful_jau = self.gaugings
        else:
            useful_jau = [cur_jau for cur_jau in self.gaugings if (cur_jau.date>= date_debut) and (cur_jau.date<= date_fin)]

        return useful_jau

    def print_gaugings(self, date_debut:datetime=None, date_fin:datetime=None):
        """ Affichage des jaugeages sur base de dates """

        txt = "date - hauteur - débit\n"
        gaug = self.get_gaugings(date_debut, date_fin)
        for curg in gaug:
            txt += f'{curg.date} - {curg.waterdepth} - {curg.discharge}\n'

        return txt

    def get_max_gauging(self, date_debut:datetime=None, date_fin:datetime=None):
        """ Récupération du jaugeage avec le débit le plus élevé """

        useful_jau = self.get_gaugings(date_debut, date_fin)
        if len(useful_jau) == 0:
            return None
        else:
            return max(useful_jau, key=lambda x: x.discharge)

    def plot_curves(self, figax = None, date_debut:datetime = None, date_fin:datetime = None, only_active = True, only_last = False) -> tuple[Figure,Axes]:
        """ Affichage des courbes de tarage

        :param figax: figure et axes matplotlib
        :param date_debut: date de début d'intervalle
        :param date_fin: date de fin d'intervalle
        :param only_active: ne prendre que les courbes actives (dépend si lu via xml ou xlsx)
        :param only_last: ne prendre que la dernière courbe encodée

        return: figure et axes matplotlib

        """

        if figax is None:
            fig,ax = plt.subplots(1,1)
        else:
            fig,ax = figax

        useful_curves = self.get_curves(date_debut, date_fin, only_active=only_active, only_last=only_last)

        colorcycler = cycle(['c', 'm', 'y', 'k'])

        def next_color():
            return next(colorcycler)

        for cur_curve in useful_curves:
            cur_curve.plot_curve((fig,ax), color=next_color())

            ax.set_title(f'Relation entre la hauteur et le débit pour la station {self.name}')
            ax.set_xlabel('Hauteur [m]')
            ax.set_ylabel('Débit [$m^3s^{-1}$]')
            ax.legend()

        return fig,ax

    def plot_gaugings(self,
                      figax = None,
                      date_debut:datetime = None,
                      date_fin:datetime = None,
                      pointsize:float = 1.,
                      confidence_h:float = None,
                      confidence_q:float = None) -> tuple[Figure,Axes]:
        """ Affichage des jaugeages

        :param figax: figure et axes matplotlib
        :param date_debut: date de début d'intervalle
        :param date_fin: date de fin d'intervalle
        :param pointsize: taille des points -- 1 par défaut
        :param confidence_h: incertitude sur la hauteur [m]
        :param confidence_q: pourcentage d'incertitude sur le débit [-] -- 0.1 pour 10%

        return: figure et axes matplotlib

        """

        if figax is None:
            fig,ax = plt.subplots(1,1)
        else:
            fig,ax = figax

        useful_jau = self.get_gaugings(date_debut, date_fin)
        x = [jaugeage.waterdepth for jaugeage in useful_jau]
        y = [jaugeage.discharge   for jaugeage in useful_jau]

        if confidence_h is None and confidence_q is None:
            ax.scatter(x, y, s=pointsize, label='Jaugeages')

        elif confidence_h is not None and confidence_q is not None:
            assert confidence_q < 1 and confidence_q > 0, 'Confidence interval must be between 0 and 1'

            ax.errorbar(x, y, xerr=confidence_h, yerr= [cury * confidence_q for cury in y], fmt='x', label='Jaugeages')

        elif confidence_h is not None:
            ax.errorbar(x, y, xerr=confidence_h, fmt='x', label='Jaugeages')

        elif confidence_q is not None:
            assert confidence_q < 1 and confidence_q > 0, 'Confidence interval must be between 0 and 1'

            ax.errorbar(x, y, yerr= [cury * confidence_q for cury in y], fmt='x', label='Jaugeages')

        return fig,ax

    def fit(self, date_debut:datetime=None, date_fin:datetime=None, which = laws.power):
        """ Ajustement d'une courbe de tarage

        :param date_debut: date de début d'intervalle
        :param date_fin: date de fin d'intervalle
        :param which: type de courbe de tarage (puissance, polynome 2 ou 3) --see laws enum

        """
        mygaugings = self.get_gaugings(date_debut, date_fin)

        h, q, dates = zip(*sorted([(curg.waterdepth, curg.discharge, curg.date) for curg in mygaugings]))

        func = which.value[0]()
        ret = curve_fit(func, h, q, maxfev= 100000)

        curve = RatingCurve(date_start=np.min(np.asarray(dates)), date_end=np.max(np.asarray(dates)))

        curve.add(which.value[1](ret[0]), np.min(np.asarray(h)), np.max(np.asarray(h)))

        self.curves.append(curve)

        fig, ax = self.plot_gaugings()
        curve.plot_curve((fig,ax))

class StationsCurvesGaugings():
    """
    Liste des stations avec courbes de tarage et jaugeages
    """

    stations:dict[str, StationCurvesGaugings]

    def __init__(self, dir:str) -> None:
        """ Initialisation de la liste des stations

        :param dir: répertoire contenant les données avec un répertoire DCENN et DGH

        """

        dir = str(dir)

        try:
            self.hydrometry = hydrometry()
        except:
            self.hydrometry = None

        dcenn = path.join(dir, 'DCENN')
        if path.exists(dcenn):
            logging.debug('DCENN directory found')
            self.add_data_SPWDCENN(path.join(dir, 'DCENN'))
        else:
            logging.warning('DCENN directory not found')

        dgh = path.join(dir, 'DGH')
        if path.exists(dgh):
            logging.debug('DGH directory found')
            self.add_data_SPWMI(  path.join(dir, 'DGH'))
        else:
            logging.warning('DGH directory not found')

    def __getitem__(self, key:str) -> StationCurvesGaugings:
        """ Accès à une station par son code """

        if key in self.stations.keys():
            return self.stations[key]
        else:
            logging.warning('Station not found - {}'.format(key))
            return None

    def __str__(self) -> str:
        """ Affichage des stations """

        txt = 'Stations:\n\n'
        for curstation in self.stations:
            txt += '- ' + curstation + '\n'

        return txt

    def add_data_SPWDCENN(self, dir:str):
        """
        Gestion des stations SPW-DCENN

        1 station = 1 fichier xml

        """

        #récupération de tous les fichiers xml et excel

        fichiers_xml   = glob.glob(dir + '\\*.xml')
        fichiers_excel = glob.glob(dir + '\\*_Jaugeages.xlsx')

        fichiers_xml   = [fich.lower() for fich in fichiers_xml]
        fichiers_excel = [fich.lower() for fich in fichiers_excel]

        self.stations  = {}

        for r in fichiers_xml:
            station_id = r.split('_')[0]
            newstation = StationCurvesGaugings(r)
            newstation.get_href(self.hydrometry)
            self.stations[newstation.code.lower()] = newstation

        for r in fichiers_excel:
            station_id = r.split('_')[-2].split('\\')[-1]
            if station_id in self.stations.keys():
                self.stations[station_id]._read_gaugings(r)
            else:
                logging.warning('Existing gaugings but no station associated - {}'.format(station_id))

    def add_data_SPWMI(self, dir:str):
        """
        Gestion des sttaions SPW-MI

        1 fichier xlsx = plusieurs stations
        """

        #récupération des données
        fichiers_stations_curves = glob.glob(path.join(dir,'*.xlsx'))

        for curfich in fichiers_stations_curves:

            if Path(curfich).name[0]!='~':

                # lecture des courbes de tarage
                dataframe=pd.read_excel(curfich, 'CT', skiprows=2)

                name=''
                m=0
                i=0
                while (i < len(dataframe['Station'])) and (str(dataframe['Code Mesure'].iloc[i]) != 'Nombre total de courbes :'):

                    # parcours de toutes les lignes du fichier Excel
                    if dataframe['Station'].iloc[i]!=name and type(dataframe['Station'].iloc[i])==str:
                        # nouvelle station
                        code = str(dataframe['Code Mesure'].iloc[i])
                        idd  = code[0:4]
                        name = dataframe['Station'].iloc[i]

                        newstation = StationCurvesGaugings()
                        newstation.code = idd
                        newstation.name = name
                        newstation.get_href(self.hydrometry)
                        self.stations[idd.lower()] = newstation

                        #stockage des expressions analytiques
                        z=i
                        while (z<len(dataframe['Station'])) and (dataframe['Station'].iloc[z]==name or type(dataframe['Station'].iloc[z])==float):

                            j=z

                            #conversion de l'heure et de la date en type datetime
                            heure_début = dataframe['Hd'].iloc[z]
                            heure_fin = dataframe['Hf'].iloc[z]

                            delta1 = timedelta(hours=heure_début)
                            delta2 = timedelta(hours=heure_fin)

                            date_debut = dataframe['Début'].iloc[z] + delta1
                            date_fin   = dataframe['Fin'].iloc[z] + delta2

                            curRC = RatingCurve(date_debut, date_fin)
                            newstation.add_ratingcurve(curRC)

                            while j<len(dataframe['Station']) and (type(dataframe['Début'].iloc[j])!=datetime or j==z) and (not np.isnan(dataframe['A x 3'].iloc[j])):

                                a = dataframe['A x 3'].iloc[j]
                                b = dataframe['B x 2'].iloc[j]
                                c = dataframe['C x'].iloc[j]
                                d = dataframe['D'].iloc[j]

                                # create symbolic function
                                x = symbols('x')
                                expression = a * x**3 + b * x**2 + c * x + d

                                # convert to function
                                # curRC.add(lambdify(x, expression), dataframe['H min'].iloc[j], dataframe['H max'].iloc[j])

                                if str(expression) == 'nan':
                                    pass

                                curRC.add(str(expression), dataframe['H min'].iloc[j], dataframe['H max'].iloc[j])

                                j=j+1
                            else :
                                while j<len(dataframe['Station']) and np.isnan(dataframe['A x 3'].iloc[j]):
                                    j=j+1
                                z=j
                                # break
                        i=z

                # lecture des jaugeages
                data_jaugeages=pd.read_excel(curfich, 'Jaugeages', skiprows=2)

                #stockage des points de jaugeages
                name=''
                i=0
                l=0
                while i < len(data_jaugeages['Station']):
                    # parcours de toutes les lignes du fichier Excel
                    if data_jaugeages['Station'].iloc[i]!=name and type(data_jaugeages['Station'].iloc[i])==str:
                        # nouvelle station
                        code = str(data_jaugeages['Stasssat'].iloc[i])
                        idd  = code[0:4].lower()
                        name = data_jaugeages['Station'].iloc[i]

                        if idd in self.stations.keys():
                            curstation = self.stations[idd]
                        else:
                            curstation = None
                            logging.warning('Existing gaugings but no station associated - {}'.format(idd))

                    if curstation is not None:

                        l=i
                        while l<len(data_jaugeages['Station']) and ((data_jaugeages['Station'][l]==name and type(data_jaugeages['Station'][l])==str) or (type(data_jaugeages['Station'][l])!=str)):
                            if str(data_jaugeages['hhmm'][l])=='nan':
                                pass
                            else :
                                delta=datetime.strptime(str(data_jaugeages['hhmm'][l]), '%Hh%M')
                                date = datetime.combine(data_jaugeages['Date'][l],delta.time())
                                add_jaugeage=Gauging(date, data_jaugeages['Hl'][l], data_jaugeages['Débit'][l], data_jaugeages['S'][l], data_jaugeages['L'][l], data_jaugeages['PE'][l])

                            l=l+1
                            curstation.gaugings.append(add_jaugeage)

                        i=l
                    else:
                        i+=1


if __name__=='__main__':

    func = get_power_law()
    ret = func(1., .5, 2., .25)

    all_stations = StationsCurvesGaugings('data\\tarage')
    curstation= all_stations.stations["L5860".lower()]
    curstation.fit(which=laws.poly3)

    h = pd.Series(np.asarray([1.,2,3.]))
    q =curstation.curves[-2].compute_q_from_h(h)
    h2 =curstation.curves[-2].compute_h_from_q(q)

    calibT2 = pd.read_csv(r'data\sim1D\Theux\calibration_T-2.csv')
    calibT25 = pd.read_csv(r'data\sim1D\Theux\calibration_T-25.csv')
    calibT100 = pd.read_csv(r'data\sim1D\Theux\calibration_T-100.csv')
    calibT2021 = pd.read_csv(r'data\sim1D\Theux\calibration_T-2021.csv')

    fig,ax = curstation.plot_curves(only_active=False)
    curstation.plot_gaugings((fig,ax))

    periods = curstation.get_periods()
    whichone = -2
    fig,ax = curstation.plot_curves(date_debut = periods[whichone][0], date_fin = periods[whichone][1])
    curstation.plot_gaugings((fig,ax), date_debut = periods[whichone][0], date_fin = periods[whichone][1])

    fig,ax = curstation.plot_curves(only_active=False)
    curstation.plot_gaugings((fig,ax))

    ax.scatter(calibT2021['h_T-2021'], calibT2021['q_T-2021'], s=1., label='Y2021')
    ax.scatter(calibT100['h_T-100']  , calibT100['q_T-100'],   s=1., label='T100 ans')
    ax.scatter(calibT25['h_T-25']    , calibT25['q_T-25'],     s=1., label='T25 ans')
    ax.scatter(calibT2['h_T-2']      , calibT2['q_T-2'],       s=1., label='T2 ans')

    ax.legend()

    fig.show()

    periods = curstation.get_periods()
    whichone = -2
    fig,ax = curstation.plot_curves(date_debut = periods[whichone][0], date_fin = periods[whichone][1])
    curstation.plot_gaugings((fig,ax), date_debut = periods[whichone][0], date_fin = periods[whichone][1])

    ax.scatter(calibT100['h_T-100']  , calibT100['q_T-100'],   s=1., label='T100 ans')
    ax.scatter(calibT25['h_T-25']    , calibT25['q_T-25'],     s=1., label='T25 ans')
    ax.scatter(calibT2['h_T-2']      , calibT2['q_T-2'],       s=1., label='T2 ans')
    ax.scatter(calibT2021['h_T-2021'], calibT2021['q_T-2021'], s=2., label='Y2021')

    qmax2 = calibT2['q_T-2'].max()
    qmax25 = calibT25['q_T-25'].max()
    qmax100 = calibT100['q_T-100'].max()
    qmax2021 = calibT2021['q_T-2021'].max()
    hmax2 = calibT2['h_T-2'].max()
    hmax25 = calibT25['h_T-25'].max()
    hmax100 = calibT100['h_T-100'].max()
    hmax2021 = calibT2021['h_T-2021'].max()

    ax.hlines(qmax2, 0,hmax2, linestyles='--')
    ax.hlines(qmax25, 0,hmax25, linestyles='--')
    ax.hlines(qmax100, 0,hmax100, linestyles='--')
    ax.hlines(qmax2021, 0,hmax2021, linestyles='--')
    ax.vlines(hmax2, 0,qmax2, linestyles='--')
    ax.vlines(hmax25, 0,qmax25, linestyles='--')
    ax.vlines(hmax100, 0,qmax100, linestyles='--')
    ax.vlines(hmax2021, 0,qmax2021, linestyles='--')

    ax.scatter(160.62-157.203, 130., marker='o', label='2D T25')
    ax.scatter(161.10-157.203, 210., marker='o', label='2D T100')
    ax.scatter(162.-157.203, 380., marker='o', label='2D T1000')
    # ax.scatter(3.1, 130., marker='+', label='2D T25-H')

    ax.legend()

    fig.show()
    pass