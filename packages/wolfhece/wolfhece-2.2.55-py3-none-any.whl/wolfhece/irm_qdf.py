"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

#Code INS des communes belges
import re
from os import path, mkdir
from pathlib import Path
from time import sleep
from typing import Literal, Union
import logging

import matplotlib as mpl
from tqdm import tqdm
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy.optimize import minimize,curve_fit
from scipy.stats import gumbel_r,genextreme
import numpy as np

# We have tried pymupdf but its license is AGPL so it's more or less a no-go.
import pdfplumber

from .ins import Localities
from .PyTranslate import _
from .pydownloader import toys_dataset, DATADIR
from .PyVertexvectors import Zones, vector, Point, Polygon, wolfvertex as wv, getIfromRGB
from .drawing_obj import Element_To_Draw

Montana_a1 = 'a1'
Montana_a2 = 'a2'
Montana_a3 = 'a3'
Montana_b1 = 'b1'
Montana_b2 = 'b2'
Montana_b3 = 'b3'

RT2 = '2'
RT5 = '5'
RT10 = '10'
RT15 = '15'
RT20 ='20'
RT25 ='25'
RT30 = '30'
RT40 ='40'
RT50 ='50'
RT75 = '75'
RT100 ='100'
RT200  = '200'

RT = [RT2,RT5,RT10,RT15,RT20,RT25,RT30,RT40,RT50,RT75,RT100,RT200]
freqdep=np.array([1./float(x) for x in RT])
freqndep=1.-freqdep

dur10min = '10 min'
dur20min = '20 min'
dur30min = '30 min'
dur1h = '1 h'
dur2h = '2 h'
dur3h = '3 h'
dur6h = '6 h'
dur12h = '12 h'
dur1d = '1 d'
dur2d = '2 d'
dur3d = '3 d'
dur4d = '4 d'
dur5d = '5 d'
dur7d = '7 d'
dur10d = '10 d'
dur15d = '15 d'
dur20d = '20 d'
dur25d = '25 d'
dur30d = '30 d'

durationstext=[dur10min,dur20min,dur30min,dur1h,dur2h,dur3h,dur6h,dur12h,dur1d,
                dur2d,dur3d,dur4d,dur5d,dur7d,dur10d,dur15d,dur20d,dur25d,dur30d]
durations         = np.array([10,20,30,60,120,180,360,720],np.float64)
durationsd        = np.array([1,2,3,4,5,7,10,15,20,25,30],np.float64)*24.*60.

durations = np.concatenate([durations,durationsd])
durations_seconds = durations * 60.  # Convert durations to seconds

class MontanaIRM():
    """ Classe pour la gestion des relations de Montana pour les précipitations """

    def __init__(self,coeff:pd.DataFrame,time_bounds=None) -> None:

        if time_bounds is None:
            self.time_bounds = [25,6000]
        else:
            self.time_bounds = time_bounds

        self.coeff=coeff

    def get_ab(self, dur, T):
        """ Get the Montana coefficients for a given duration and return period

        :param dur: the duration
        :param T: the return period
        """

        curcoeff = self.coeff.loc[float(T)]
        if dur<self.time_bounds[0]:
            a=curcoeff[Montana_a1]
            b=curcoeff[Montana_b1]
        elif dur<=self.time_bounds[1]:
            a=curcoeff[Montana_a2]
            b=curcoeff[Montana_b2]
        else:
            a=curcoeff[Montana_a3]
            b=curcoeff[Montana_b3]

        return a,b

    def get_meanrain(self, dur, T, ab= None):
        """ Get the mean rain for a given duration and return period

        :param dur: the duration
        :param T: the return period
        :param ab: the Montana coefficients
        """

        if ab is None:
            ab = self.get_ab(dur,T)
        return ab[0]*dur**(-ab[1])

    def get_instantrain(self, dur, T, ab= None):
        """ Get the instantaneous rain for a given duration and return period

        :param dur: the duration
        :param T: the return period
        :param ab: the Montana coefficients
        """
        if ab is None:
            ab = self.get_ab(dur,T)
        meani=self.get_meanrain(dur,T,ab)
        return (1.-ab[1])*meani

    def get_Q(self, dur, T):
        """ Get the quantity of rain for a given duration and return period

        :param dur: the duration
        :param T: the return period
        """

        rain = self.get_meanrain(dur,T)
        return rain*dur/60. #to obtains [mm.h^-1] as dur is in [min]

    def get_hyeto(self, durmax, T, r= 0.5):
        """ Get the hyetogram for a given return period

        :param durmax: the maximum duration of the hyetogram
        :param T: the return period
        :param r: Decentration coefficient
        """

        x = np.arange(10,durmax,1,dtype=np.float64)
        # y = [self.get_instantrain(curx,T) for curx in x]

        startpeak=durmax*r-5
        endpeak=durmax*r+5

        if r==1.:
            xbeforepeak = np.zeros(1)
        else:
            xbeforepeak = np.arange(-float(durmax-10)*(1.-r),0,(1.-r))
        if r==0.:
            xafterpeak = endpeak
        else:
            xafterpeak  = np.arange(0,float(durmax-10)*r,r)

        xbeforepeak+= startpeak
        xafterpeak += endpeak

        x_hyeto = np.concatenate([xbeforepeak, [startpeak,endpeak], xafterpeak])
        y_hyeto = np.zeros(len(x_hyeto))
        for k in range(len(x_hyeto)):
            if x_hyeto[k] <= startpeak:
                y_hyeto[k] = self.get_instantrain((startpeak-x_hyeto[k])/(1.-r)+10,T)
            else:
                y_hyeto[k] = self.get_instantrain((x_hyeto[k]-endpeak)/r+10,T)

        if r==0.:
            y_hyeto[-1]=0.
        elif r==1.:
            y_hyeto[0]=0.

        return x_hyeto,y_hyeto

    def plot_hyeto(self, durmax, T, r= 0.5):
        """ Plot the hyetogram for a given return period

        :param durmax: the maximum duration of the hyetogram
        :param T: the return period
        :param r: Decentration coefficient
        """
        x,y = self.get_hyeto(durmax,T,r)

        fig,ax = plt.subplots(1,1,figsize=[15,10], tight_layout=True)
        ax.plot(x,y,label=_("Hyetogram"))

        ax.set_xlabel(_('Time [min]'))
        ax.set_ylabel(_('Intensity [mm/h]'))
        ax.legend().set_draggable(True)

        return fig,ax

    def plot_hyetos(self, durmax, r= 0.5):
        """ Plot the hyetograms for all return periods

        :param durmax: the maximum duration of the hyetograms
        :param r: Decentration coefficient
        """

        fig,ax = plt.subplots(1,1,figsize=[15,10], tight_layout=True)

        for curT in RT:
            x,y = self.get_hyeto(durmax,curT,r)

            ax.plot(x,y,label=curT)

        ax.set_xlabel(_('Time [min]'))
        ax.set_ylabel(_('Intensity [mm/h]'))
        ax.legend().set_draggable(True)

        return fig,ax

class Qdf_IRM():
    """
    Gestion des relations QDF calculées par l'IRM

    Exemple d'utilisation :

    Pour importer les fichiers depuis le site web de l'IRM meteo.be
    from wolfhece.irm_qdf import Qdf_IRM
    qdf = Qdf_IRM(force_import=True)
    qdf =

    Il est possible de spécifier le répertoire de stockage des fichiers Excel
    Par défaut, il s'agit d'un sous-répertoire 'irm' du répertoire courant qui sera créé s'il n'exsiste pas

    Une fois importé/téléchargé, il est possible de charger une commune sur base de l'INS ou de son nom

    myqdf = Qdf_IRM(name='Jalhay')

    Les données sont ensuite disponibles dans les propriétés, qui sont des "dataframes" pandas (https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html) :

        - qdf           : les relation Quantité/durée/fréquence
        - standarddev   : l'écart-type de l'erreur
        - confintlow    : la valeur inférieure de l'intervalle de confiance (-2*stddev)
        - confintup     : la valeur supérieure de l'intervalle de confiance (+2*stddev)
        - montanacoeff  : les coeffciients de Montana

    L'index est le temps (dur10min, dur30min, dur1h, ... -- durationstext) et les colonnes sont les périodes de retour (RT2, RT5, RT10, ... -- RT).

    Il est par exemple possible d'accéder aux coefficients de Montana via l'une de ces lignes ou une combinaison :

    display(myqdf.montanacoeff)
    rt = myqdf.montanacoeff.index
    display(myqdf.montanacoeff.loc[rt[0]])
    display(myqdf.montanacoeff.iloc[0])
    display(myqdf.get_Montanacoeff(qdf.RT2))

    :param force_import: If True, will download all the IRM's QDF files (about 600).
    :param import_as_needed: If True and the IRM's QDF file has not yet been downloaded
       then the file is downloaded.
    """

    def __init__(self, store_path= 'irm',
                 code:int= 0, name= '',
                 force_import= False,
                 ins:Literal['2018', '2019', '2025', 2018, 2019, 2025] = 2018,
                 localities:Localities = None,
                 dataframe:pd.DataFrame = None,
                 import_as_needed = False) -> None:

        if localities is None:

            assert int(ins) in [2018, 2019, 2025], _('Bad INS - Retry !')

            self.myloc = Localities(ins)
        else:
            self.myloc = localities

        self.store = Path(store_path)

        # This one will hold Qdf data of one locality. If it is None it means no
        # data has been loaded.
        self.qdf = None
        self.standarddev = None
        self.confintlow = None
        self.confintup = None
        self.montanacoeff = None
        self.montana = None

        if force_import:
            # Import all QDF's from IRM
            Qdf_IRM.importfromwebsite(store_path, ins=ins)
        elif import_as_needed:
            # Import as needed is helpful in the case of unit tests. They
            # usually require only a handful of QDF curves and so downloading
            # only some of them is much faster.
            if not (self.store / f"{code}.xlsx").exists():
                Qdf_IRM.importfromwebsite(store_path, ins=ins, ins_code=code)

        self._code = None
        self._name = None

        self._qdf_image_table = None
        self._qdf_image_plot = None

        if dataframe is not None:
            """ If a dataframe is provided, we assume it contains the QDF data
            and we set it directly.
            """
            self._code = int(code)
            self._name = self.myloc.get_namefromINS(code)

            # Find columns containing '_Q'
            qdf_columns = ['Duration'] + [col for col in dataframe.columns if '_Q' in col]
            self.qdf = dataframe[qdf_columns].copy()

            #replace duration in seconds with duration texts
            self.qdf['Duration'] = self.qdf['Duration'].apply(lambda x: durationstext[list(durations_seconds).index(x)] if x in durations_seconds else x)
            # replace columns names
            self.qdf.columns = [col.replace('_Q', '') for col in self.qdf.columns]
            # Set duration as index
            self.qdf.set_index('Duration', inplace=True)
            # Remove the name of the index
            self.qdf.index.name = None

            # Convert columns name to string
            self.qdf.columns = [str(col) for col in self.qdf.columns]

            std_columns = ['Duration'] + [col for col in dataframe.columns if '_Std' in col]
            self.standarddev = dataframe[std_columns].copy()
            self.standarddev['Duration'] = self.standarddev['Duration'].apply(lambda x: durationstext[list(durations_seconds).index(x)] if x in durations_seconds else x)
            self.standarddev.set_index('Duration', inplace=True)

            confintlow_columns = ['Duration'] + [col for col in dataframe.columns if '_Low' in col]
            self.confintlow = dataframe[confintlow_columns].copy()
            self.confintlow['Duration'] = self.confintlow['Duration'].apply(lambda x: durationstext[list(durations_seconds).index(x)] if x in durations_seconds else x)
            self.confintlow.set_index('Duration', inplace=True)

            confintup_columns = ['Duration'] + [col for col in dataframe.columns if '_Up' in col]
            self.confintup = dataframe[confintup_columns].copy()
            self.confintup['Duration'] = self.confintup['Duration'].apply(lambda x: durationstext[list(durations_seconds).index(x)] if x in durations_seconds else x)
            self.confintup.set_index('Duration', inplace=True)

            self._read_csv_or_excel_Montana_only(code = self._code)

            self.fit_all()

        elif code !=0:
            if self._read_csv_or_excel(code=str(code)):
                self.fit_all()
                self._code = code
                self._name = self.myloc.get_namefromINS(code)
            else:
                logging.debug(f"INS code {code} not found in the store (see {self.store.absolute()})")
        elif name!='':
            if self._read_csv_or_excel(name=name):
                self.fit_all()
                self._name = name
                self._code = self.myloc.get_INSfromname(name)
            else:
                logging.debug(f"Name {name} not found in the store")

    def has_data_for_locality(self) -> bool:
        """ Has this instance been initialized with data from a locality ?
        """
        return self.qdf is not None

    @property
    def name(self):
        return self._name

    @property
    def code(self):
        return self._code

    @property
    def code_name(self):
        return str(self._code) + '-' + self._name

    @property
    def name_code(self):
        return self._name + '-' + str(self._code)

    def export_allmontana2xls(self):
        """ Export all Montana coefficients to an Excel file """

        newdf = []

        for curcode in self.myloc.get_allcodes():

            self._read_csv_or_excel(code=curcode)
            if self.montanacoeff is not None:
                self.montanacoeff['INS'] = [curcode]*12
                self.montanacoeff['Name'] = [self.myloc.get_namefromINS(int(curcode))]*12

                newdf.append(self.montanacoeff.copy())
                self.montanacoeff=None

        newdf = pd.concat(newdf)

        newdf.to_excel("allmontana.xlsx")


    @classmethod
    def importfromwebsite(cls, store_path:Path = 'irm', verbose:bool= False, waitingtime:float= .01, ins:Literal['2018', '2019', '2025', 2018, 2019, 2025] = 2018, ins_code: int = None):
        """ Import Excel files for one or all municipalities from the IRM website

        :param store_path: Where to store the downloaded data. Directory will be created if it doesn't exist.
        :param verbose: If `True`, will print some progress information.
                        If `False`, will do nothing.
                        If a callable, then will call it with a float in [0, 1].
                        0 means nothing downloaded, 1 means everything downloaded.

        :param waitingtime: How long to wait (in seconds) betwenn the download
                            of each station (will make sure we don't overwhelm IRM's website).

        :param ins: The year of the INS codes to use.
        :param code: Restricts the data download to a specific NIS code. `None` means full download.
        """
        import requests

        myloc = Localities(ins)

        store_path = Path(store_path)

        if ins_code is not None:
            codes_to_load = [ins_code]
        else:
            if not store_path.exists():
                store_path.mkdir(parents=True, exist_ok=True)
            codes_to_load = myloc.inscode2name

        for key,myins in enumerate(codes_to_load):
            #chaîne URL du fichier Excel
            url="https://www.meteo.be//resources//climatology//climateCity//xls//IDF_table_INS"+str(myins)+".xlsx"
            #Obtention du fichiers depuis le site web de l'IRM
            response=requests.get(url)

            if str(response.content).find("not found")==-1:

                # Make sure we create the store path only if we have
                # something to put inside.
                if ins_code is not None and not store_path.exists():
                    store_path.mkdir(parents=True, exist_ok=True)

                file=open(store_path / (str(myins)+".xlsx"), 'wb')
                file.write(response.content)
                file.close()
                if verbose:
                    if callable(verbose):
                        verbose(key/len(codes_to_load))
                    else:
                        print(myins)
            else:
                #logging.error(response.content)
                logging.error(f"Failed to load IRM data: {url} --> {response}")

            sleep(waitingtime)

    def _read_csv_or_excel(self, code='', name=''):
        """ Lecture des caractéristiques d'une commune
        depuis le fichier CSV ou Excel associé au code INS

        :param code: le code INS de la commune
        :param name: le nom de la commune
        """
        import warnings

        if code !='':
            loccode=str(code)
            name = self.myloc.get_namefromINS(int(loccode))
        elif name!='':
            if not name.lower() in self.myloc.insname2code.keys():
                return _('Bad name ! - Retry')
            loccode=str(self.myloc.insname2code[name.lower()])

        self._code = loccode
        self._name = name

        store = self.store

        pathname_xls = store / (loccode+".xlsx")
        pathname_csv = store / 'csv' / loccode

        if pathname_csv.exists():
            self.qdf = pd.read_csv(pathname_csv / 'qdf.csv', index_col=0)
            self.standarddev = pd.read_csv(pathname_csv / 'standarddev.csv', index_col=0)
            self.confintlow = pd.read_csv(pathname_csv / 'confintlow.csv', index_col=0)
            self.confintup = pd.read_csv(pathname_csv / 'confintup.csv', index_col=0)
            self.montanacoeff = pd.read_csv(pathname_csv / 'montanacoeff.csv', index_col=0)
            self.montana = MontanaIRM(self.montanacoeff)
            return True
        else:
            # with warnings.catch_warnings(record=True):
            #     warnings.simplefilter("always")
            if path.exists(pathname_xls):
                self.qdf=pd.read_excel(pathname_xls,"Return level",index_col=0,skiprows=range(7),nrows=19,usecols="A:M",engine='openpyxl', engine_kwargs={'read_only': True})
                self.standarddev=pd.read_excel(pathname_xls,"Standard deviation",index_col=0,skiprows=range(7),nrows=19,usecols="A:M",engine='openpyxl', engine_kwargs={'read_only': True})
                self.confintlow=pd.read_excel(pathname_xls,"Conf. interval, lower bound",index_col=0,skiprows=range(7),nrows=19,usecols="A:M",engine='openpyxl', engine_kwargs={'read_only': True})
                self.confintup=pd.read_excel(pathname_xls,"Conf. interval, upper bound",index_col=0,skiprows=range(7),nrows=19,usecols="A:M",engine='openpyxl', engine_kwargs={'read_only': True})
                self.montanacoeff=pd.read_excel(pathname_xls,"Montana coefficients",index_col=0,skiprows=range(11),nrows=12,usecols="A:G",engine='openpyxl', engine_kwargs={'read_only': True})
                self.montana = MontanaIRM(self.montanacoeff)
                return True
            else:
                logging.warning(f"Can't find montana data. Checked {pathname_csv.absolute()} and {pathname_xls.absolute()}")
                self.qdf=None
                self.standarddev=None
                self.confintlow=None
                self.confintup=None
                self.montanacoeff=None
                self.montana=None
                return False

    def _read_csv_or_excel_Montana_only(self, code='', name=''):
        """ Lecture des caractéristiques d'une commune depuis
        le fichier CSV Excel associé au code INS

        :param code: le code INS de la commune
        :param name: le nom de la commune
        """

        import warnings

        if code !='':
            loccode=str(code)
            name = self.myloc.get_namefromINS(int(loccode))
        elif name!='':
            if not name.lower() in self.myloc.insname2code.keys():
                return _('Bad name ! - Retry')
            loccode=str(self.myloc.insname2code[name.lower()])

        self._code = loccode
        self._name = name

        store = self.store

        pathname_xls = store / (loccode+".xlsx")
        pathname_csv = store / 'csv' / loccode

        if pathname_csv.exists():
            self.montanacoeff = pd.read_csv(pathname_csv / 'montanacoeff.csv', index_col=0)
            self.montana = MontanaIRM(self.montanacoeff)
            return True
        else:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                if path.exists(pathname_xls):
                    self.montanacoeff=pd.read_excel(pathname_xls,"Montana coefficients",index_col=0,skiprows=range(11),nrows=12,usecols="A:G",engine='openpyxl', engine_kwargs={'read_only': True})
                    self.montana = MontanaIRM(self.montanacoeff)
                    return True
                else:
                    self.montanacoeff=None
                    self.montana=None
                    return False

    @classmethod
    def convert_xls2csv(cls, store_path= 'irm', ins:Literal['2018', '2019', '2025', 2018, 2019, 2025] = 2018):
        """ Convert all Excel files to CSV files

        :param store_path: Where to store the downloaded data. Directory will be created if it doesn't exists.
        :param ins: The year of the INS codes to use.
        """

        myloc = Localities(ins)

        store_path = Path(store_path)

        for key,myins in enumerate(myloc.get_allcodes()):
            pathname = store_path / (str(myins)+".xlsx")
            if pathname.exists():
                try:
                    logging.info(f"Converting {pathname} to CSV files")
                    qdf=pd.read_excel(pathname,"Return level",index_col=0,skiprows=range(7),nrows=19,usecols="A:M",engine='openpyxl', engine_kwargs={'read_only': True})
                    standarddev=pd.read_excel(pathname,"Standard deviation",index_col=0,skiprows=range(7),nrows=19,usecols="A:M",engine='openpyxl', engine_kwargs={'read_only': True})
                    confintlow=pd.read_excel(pathname,"Conf. interval, lower bound",index_col=0,skiprows=range(7),nrows=19,usecols="A:M",engine='openpyxl', engine_kwargs={'read_only': True})
                    confintup=pd.read_excel(pathname,"Conf. interval, upper bound",index_col=0,skiprows=range(7),nrows=19,usecols="A:M",engine='openpyxl', engine_kwargs={'read_only': True})
                    montanacoeff=pd.read_excel(pathname,"Montana coefficients",index_col=0,skiprows=range(11),nrows=12,usecols="A:G",engine='openpyxl', engine_kwargs={'read_only': True})

                    store_csv = store_path / 'csv' / str(myins)
                    store_csv.mkdir(exist_ok=True, parents=True)

                    qdf.to_csv(store_csv / 'qdf.csv')
                    standarddev.to_csv(store_csv / 'standarddev.csv')
                    confintlow.to_csv(store_csv / 'confintlow.csv')
                    confintup.to_csv(store_csv / 'confintup.csv')
                    montanacoeff.to_csv(store_csv / 'montanacoeff.csv')
                except Exception as e:
                    logging.error(f"Error processing {pathname}: {e}")
            else:
                logging.warning(f"File {pathname} does not exist, skipping conversion.")
                logging.info(_("If it is a problem, try to reimport the data from the IRM website."))


    def plot_idf(self, T=None, which:Literal['All', 'Montana', 'QDFTable'] = 'All', color=[27./255.,136./255.,245./255.]):
        """
        Plot IDF relations on a new figure

        :param T       : the return period (based on RT constants)
        :param which   : information to plot
            - 'Montana'
            - 'QDFTable'
            - 'All'
        """

        if self.montana is None and which != 'QDFTable':
            logging.error(_("Montana coefficients are not available for this locality."))
            return None, None

        if self.qdf is None and which != 'Montana':
            logging.error(_("QDF data is not available for this locality."))
            return None, None

        fig,ax = plt.subplots(1,1,figsize=(15,10), tight_layout=True)
        ax.set_xscale('log')
        ax.set_yscale('log')

        if T is None:
            for k in range(len(RT)):
                pond = .3+.7*float(k/len(RT))
                mycolor = color+[pond]
                if which=='All' or which=='QDFTable':
                    ax.scatter(durations,self.qdf[RT[k]]/durations*60.,label=RT[k] + _(' QDF Table'),color=mycolor)

                if which=='All' or which=='Montana':
                    iMontana = [self.montana.get_meanrain(curdur,RT[k]) for curdur in durations]
                    ax.plot(durations,iMontana,label=RT[k] + ' Montana',color=mycolor)
        else:
            assert T in RT, _('Bad return period ! - Retry')

            if which=='All' or which=='QDFTable':
                ax.scatter(durations,self.qdf[T],label=T+ _(' QDF Table'),color=color)

            if which=='All' or which=='Montana':
                iMontana = [self.montana.get_instantrain(curdur,T) for curdur in durations]
                ax.plot(durations,iMontana,label=T + ' Montana',color=color)

        ax.legend().set_draggable(True)
        ax.set_xlabel(_('Duration [min]'))
        ax.set_ylabel(_('Intensity [mm/h]'))
        ax.set_xticks(durations)
        ax.set_xticklabels(durationstext,rotation=45)
        ax.set_title(self._name + ' - code : ' + str(self._code))

        return fig,ax

    def plot_qdf(self, T=None, which:Literal['All', 'Montana', 'QDFTable'] = 'All', color=[27./255.,136./255.,245./255.]):
        """
        Plot QDF relations on a new figure
        :param T       : the return period (based on RT constants)
        :param which   : information to plot
            - 'Montana'
            - 'QDFTable'
            - 'All'
        """

        if self.qdf is None and which != 'Montana':
            logging.error(_("QDF data is not available for this locality."))
            return None, None
        if self.montana is None and which != 'QDFTable':
            logging.error(_("Montana coefficients are not available for this locality."))
            return None, None

        fig,ax = plt.subplots(1,1,figsize=(12,8), tight_layout=True)
        ax.set_xscale('log')

        if T is None:
            for k in range(len(RT)):
                pond = .3+.7*float(k/len(RT))
                mycolor = color+[pond]
                if which=='All' or which=='QDFTable':
                    ax.scatter(durations,self.qdf[RT[k]],label=RT[k] + _(' QDF Table'),color=mycolor)

                if which=='All' or which=='Montana':
                    QMontana = [self.montana.get_Q(curdur,RT[k]) for curdur in durations]
                    ax.plot(durations,QMontana,label=RT[k] + ' Montana',color=mycolor)
        else:
            assert T in RT, _('Bad return period ! - Retry')

            if which=='All' or which=='QDFTable':
                ax.scatter(durations,self.qdf[T],label=T+ _(' QDF Table'),color=color)

            if which=='All' or which=='Montana':
                QMontana = [self.montana.get_Q(curdur,T) for curdur in durations]
                ax.plot(durations,QMontana,label=T + ' Montana',color=color)

        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.legend().set_draggable(True)
        ax.set_xlabel(_('Duration [min]'))
        ax.set_ylabel(_('Quantity [mm]'))
        ax.set_xticks(durations)
        ax.set_xticklabels(durationstext,rotation=45)
        ax.set_title(self._name + ' - code : ' + str(self._code))

        return fig,ax

    def plot_cdf(self, dur=None):
        """ Plot the cdf of the QDF data for a given duration """

        if self.qdf is None:
            logging.error(_("QDF data is not available for this locality."))
            return None, None

        fig,ax = plt.subplots(1,1,figsize=(10,10), tight_layout=True)
        if dur is None:
            for k in range(len(durations)):
                pond = .3+.7*float(k/len(durations))
                mycolor = (27./255.,136./255.,245./255.,pond)
                ax.scatter(self.qdf.loc[durationstext[k]],freqndep,marker='o',label=durationstext[k],color=mycolor)
        else:
            assert dur in durationstext, _('Bad duration - Retry !')

            ax.scatter(self.qdf.loc[dur],freqndep,marker='o',label=dur,color=(0,0,1))

        ax.legend().set_draggable(True)
        ax.set_ylabel(_('Cumulative distribution function (cdf)'))
        ax.set_xlabel(_('Quantity [mm]'))
        ax.set_title(self._name + ' - code : ' + str(self._code))

        return fig,ax

    def fit_all(self):
        """ Fit all durations with a Generalized Extreme Value distribution """

        self.load_fits_json()

        if self.popt_all == {}:
            for curdur in durationstext:
                fig,ax,popt,pcov = self.fit_cdf(curdur)
                self.popt_all[curdur]=popt
                # self.pcov_all[curdur]=pcov

            self.save_fits_json()

    def save_fits_json(self):
        """ Save the fits in a csv file """

        with open(self.store / (str(self._code) + '_fits.json'), 'w') as f:
            df = pd.DataFrame(self.popt_all)
            df.to_json(f)

        # with open(path.join(self.store, str(self.code) + '_fits_cov.json'), 'w') as f:
        #     df = pd.DataFrame(self.pcov_all)
        #     df.to_json(f)

    def load_fits_json(self):
        """ Load the fits from a json file """

        import json

        filename = self.store / (str(self._code) + '_fits.json')

        if filename.exists():
            with open(filename, 'r') as f:
                self.popt_all = json.load(f)

            for key in self.popt_all.keys():
                self.popt_all[key] = np.array([val for val in self.popt_all[key].values()])
        else:
            self.popt_all = {}

        # filename = path.join(self.store, str(self.code) + '_fits_cov.json')

        # if path.exists(filename):
        #     with open(filename, 'r') as f:
        #         self.pcov_all = json.load(f)
        # else:
        #     self.pcov_all = {}

    def fit_cdf(self, dur=None, plot=False):
        """ Fit the cdf of the QDF data with a Generalized Extreme Value distribution

        :param dur: the duration to fit
        :param plot: if True, will plot the cdf with the fit
        """

        if dur is None:
            return _('Bad duration - Retry !')
        if dur not in durationstext:
            return _('Bad duration - Retry !')

        x=np.asarray(self.qdf.loc[dur], dtype=np.float64)

        def locextreme(x,a,b,c):
            return genextreme.cdf(x, a, loc=b, scale=c)

        def locextreme2(a):
            LL = -np.sum(genextreme.logpdf(x,a[0],loc=a[1],scale=a[2]))
            return LL

        popt = genextreme.fit(x)
        popt, pcov = curve_fit(locextreme, x, freqndep, p0=popt)

        #ptest = minimize(locextreme2,popt,bounds=[[-10.,0.],[0.,100.],[0.,100.]])

        # perr = np.sqrt(np.diag(pcov))

        fig=ax=None
        if plot:
            fig,ax=self.plot_cdf(dur)
            ax.plot(x,genextreme.cdf(x,popt[0],loc=popt[1],scale=popt[2]),label='fit')
            # ax.plot(x,genextreme.cdf(x,ptest.x[0],loc=ptest.x[1],scale=ptest.x[2]),label='fit_MLE')
            ax.legend().set_draggable(True)

        self.stat = genextreme

        return fig,ax,popt,pcov

    def get_Tfromrain(self, Q, dur=dur1h):
        """ Get the return period for a given quantity of rain

        :param Q: the quantity of rain
        :param dur: the duration
        """

        return 1./self.stat.sf(Q, self.popt_all[dur][0], loc=self.popt_all[dur][1], scale=self.popt_all[dur][2])

    def get_rainfromT(self, T, dur= dur1h):
        """ Get the quantity of rain for a given return period and duration

        :param T: the return period
        :param dur: the duration
        """

        return self.stat.isf(1./T,self.popt_all[dur][0],loc=self.popt_all[dur][1],scale=self.popt_all[dur][2])

    def get_MontanacoeffforT(self, return_period):
        """ Get the Montana coefficients for a given return period

        :param return_period: the return period
        """

        if return_period in RT:
            return self.montanacoeff.loc[float(return_period)]
        else:
            return _('Bad RT - Retry !')

    def plot_hyeto(self, durmax, T, r=.5):
        """ Plot the hyetogram for a given return period

        :param durmax: the maximum duration of the hyetogram
        :param T: the return period
        :param r: the decentration coefficient
        """

        fig,ax = self.montana.plot_hyeto(durmax,T,r)
        ax.set_title(self._name + ' - code : ' + str(self._code))

        return fig

    def plot_hyetos(self, durmax, r=.5):
        """ Plot the hyetograms for all return periods

        :param durmax: the maximum duration of the hyetograms
        :param r: the decentration coefficient
        """

        fig,ax = self.montana.plot_hyetos(durmax,r)
        ax.set_title(self._name + ' - code : ' + str(self._code))

    def __str__(self) -> str:
        """ Return the QDF data as a string """
        return self.qdf.__str__()

    def make_image_qdf_plot(self, T= None, which:Literal['All', 'Montana', 'QDFTable'] = 'All', color=[27./255.,136./255.,245./255.]):
        """ Create an image of the QDF plot.

        We use the `matplotlib` library to create a PNG image of the QDF data.
        The image will be saved in the store path with the name `<code>_qdf_plot.png`.

        :param durmax: the maximum duration of the hyetograms
        :param r: Decentration coefficient
        :return: a PNG image
        """
        import matplotlib

        self._qdf_image_plot = self.store / f"{self.code_name}_qdf_plot.png"
        if self._qdf_image_plot.exists():
            return self._qdf_image_plot

        old_backend = matplotlib.get_backend()
        matplotlib.use('Agg')  # Use a non-interactive backend for saving images
        fig, ax = self.plot_qdf(T=T, which=which, color=color)
        fig.savefig(self._qdf_image_plot, dpi=300)
        plt.close(fig)
        matplotlib.use(old_backend)  # Restore the original backend

        return self._qdf_image_plot

    def make_image_qdf_table(self):
        """ Create an image of the QDF data.

        We use the `dataframe_image` library to create a PNG image of the QDF data.
        Added style to the DataFrame to make it more readable.

        :return: a PNG image
        """

        try:
            import dataframe_image as dfimg
        except ImportError:
            logging.error(_("The 'dataframe_image' library is not installed. Please install it to create QDF table images."))
            return None

        if self.qdf is None:
            logging.error(_("QDF data is not available for this locality."))
            return None

        qdf = self.qdf.copy()

        # Create a styled DataFrame
        # Add a caption to the DataFrame
        qdf.attrs['caption'] = f"QDF data for {self._name} (INS code: {self._code})<br>\
<div style='font-size:8px;'>source : https://www.meteo.be/fr/climat/climat-de-la-belgique/climat-dans-votre-commune<br> \
Data extracted from IRM (Institut Royal Météorologique de Belgique) and processed by Wolf - ULiège"


        qdf.columns = pd.MultiIndex.from_tuples([(f"{_('Return period')}", str(col)) for col in qdf.columns])


        # Style the DataFrame
        # One line per duration, one column per return period
        # We will use light colors for the background and borders
        # to highlight every other line and center the text
        styled_df = qdf.style.format(precision=1) \
            .set_caption(qdf.attrs['caption']) \
            .set_properties(**{
            'text-align': 'center',
            'font-size': '12px',
            'border': '1px solid black',
            # 'background-color': '#f0f0f0',
        }).set_table_styles([
            {
            'selector': 'thead th.row_heading.level0',
            # 'props': [('text-align', 'center'), ('background-color', '#d9edf7'), ('color', '#31708f'),],
            'props': [('color', 'transparent')],
            },
            {
            'selector': 'thead th',
            'props': [('text-align', 'center'), ('background-color', '#d9edf7'), ('color', '#31708f')],
            },
            ])
        # Define the path for the image
        self._qdf_image_table = self.store / f"{self.code_name}_qdf.png"
        # Save the styled DataFrame as an image
        dfimg.export(styled_df, self._qdf_image_table, dpi=300)

    def make_images(self):
        """ Create all images for the QDF data. """

        self.make_image_qdf_table()
        self.make_image_qdf_plot()

        return self._qdf_image_table, self._qdf_image_plot

    @property
    def path_image_plot(self):
        """ Get the path for the QDF plot image. """
        if self._qdf_image_plot is None:
            self.make_image_qdf_plot()
        return self._qdf_image_plot

    @property
    def path_image_table(self):
        """ Get the path for the QDF table image. """
        if self._qdf_image_table is None:
            self.make_image_qdf_table()
        return self._qdf_image_table

class QDF_Belgium():
    """ Class to manage all QDF data for Belgium """

    def __init__(self, store_path= 'irm',
                 ins:Literal['2018', '2019', '2025', 2018, 2019, 2025] = 2018,
                 force_import: bool = False) -> None:

        self.localities = Localities(ins)
        self.store_path = Path(store_path)

        if force_import or len(list(self.store_path.glob('*.xlsx'))) == 0:
            Qdf_IRM.importfromwebsite(store_path=str(self.store_path), verbose=True, ins=ins)
        if len(list(self.store_path.rglob('*.csv'))) == 0:
            Qdf_IRM.convert_xls2csv(store_path=str(self.store_path), ins=ins)

        self.all:dict[int, Qdf_IRM] = {}
        for loc_ins in tqdm(self.localities.get_allcodes()):
            loc = Qdf_IRM(store_path=str(self.store_path),
                          code=loc_ins,
                          localities=self.localities)
            if loc.qdf is not None:
                self.all[loc_ins] = loc

    def make_images(self):
        """ Create all images for all QDF data. """

        for loc in self.all.values():
            loc.make_images()

    def __getitem__(self, key) -> Qdf_IRM:

        if isinstance(key, int):
            if key in self.all:
                return self.all[key]
            else:
                logging.error(f"INS code {key} not found in the data")
                return None

        elif isinstance(key, str):
            key = self.localities.get_INSfromname(key)
            if key is not None:
                if key in self.all:
                    return self.all[key]
                else:
                    logging.error(f"INS code {key} not found in the data")
                    return None
            else:
                logging.error(f"Name {key} not found in the data")
                return None

    def __iter__(self):
        """ Iterate over all localities """
        for qdf_municip in self.all.values():
            yield qdf_municip


TRANSLATION_HEADER = {'année': 'year', 'janv.': 'January', 'févr.': 'February', 'mars': 'March',
            'avr.': 'April', 'mai': 'May', 'juin': 'June',
            'juil.': 'July', 'août': 'August', 'sept.': 'September',
            'oct.': 'October', 'nov.': 'November', 'déc.': 'December'}
RE_REFERENCE = re.compile(r"\([0-9]+\)")

class Climate_IRM():

    def __init__(self, store_path= 'irm', ins:Literal['2018', '2019', '2025', 2018, 2019, 2025] = 2018) -> None:
        self.store_path = Path(store_path)
        self.localities = Localities(ins)

        self._climate_data = {}

    def __getitem__(self, key):
        return self._climate_data[key]

    @classmethod
    def importfromwebsite(cls, store_path= 'irm', verbose:bool= False, waitingtime:float= .01, ins:Literal['2018', '2019', '2025', 2018, 2019, 2025] = 2018, ins_code: int = None, convert=False):
        """ Import Excel files for one or all municipalities from the IRM website

        :param store_path: Where to store the downloaded data. Directory will be created if it doesn't exists.
        :param verbose: If `True`, will print some progress information.
                        If `False`, will do nothing.
                        If a callable, then will call it with a float in [0, 1].
                        0 means nothing downloaded, 1 means everything downloaded.

        :param waitingtime: How long to wait (in seconds) betwenn the download
                            of each station (will make sure we don't overwhelm IRM's website).

        :param ins: The year of the INS codes to use.
        :param code: Restricts the data download to a specific NIS code. `None` means full download.
        :param convert: Converts the downloaded PDF to Excel files.
        """
        import requests

        myloc = Localities(ins)

        if ins_code is not None:
            codes_to_load = [ins_code]
        else:
            if not path.exists(store_path):
                mkdir(store_path)
            codes_to_load = myloc.inscode2name

        for key,myins in enumerate(codes_to_load):
            #chaîne URL du fichier Excel
            url="https://www.meteo.be//resources//climatology//climateCity//pdf//climate_INS"+str(myins)+"_9120_fr.pdf"
            #Obtention du fichiers depuis le site web de l'IRM
            response=requests.get(url)

            if str(response.content).find("Page not found")==-1 :

                # Make sure we create the store path only if we have
                # something to put inside.
                if ins_code is not None and not path.exists(store_path):
                    mkdir(store_path)

                pdf_file = path.join(store_path,str(myins)+".pdf")
                file=open(pdf_file, 'wb')
                file.write(response.content)
                file.close()

                if convert:
                    cls._convert_irm_file(pdf_file)

                if verbose:
                    if callable(verbose):
                        verbose(key/len(codes_to_load))
                    else:
                        print(myins)
            else:
                #logging.error(response.content)
                logging.error(f"Failed to load IRM data: {url} --> {response}")

            if len(codes_to_load) >= 2:
                sleep(waitingtime)

    @classmethod
    def _scrap_table(cls, t):
        """
        Helper method to transform a table represented as a list of list to a
        pandas DataFrame.
        """

        def fix_cid(strings: list[str]):
            # The CID thing is a known issue:
            # https://github.com/euske/pdfminer/issues/122
            return [s.replace('(cid:176)C ', '°C').replace('¢', "'") for s in strings]

        nt = []
        row_headers = []
        for rndx in range(1, len(t)):
            # In the row header, we remove the "references" like "(1)".
            row_headers.append( RE_REFERENCE.sub("", t[rndx][0]) )

            # The PDFs use different "minus" glyph instead of an ASCII one,
            # let's fix it.
            nt.append( list(map(lambda s:float(s.replace("−","-")), t[rndx][1:])))

        columns_headers = map(TRANSLATION_HEADER.get, t[0][1:])
        df = pd.DataFrame(nt, columns=fix_cid(columns_headers), index=fix_cid(row_headers))
        return df

    @classmethod
    def _convert_irm_file(cls, pdf_file: Union[str, Path]):
        """
        Scrap a PDF from IRM into two tables in a single Excel file with two
        sheets.
        """
        pdf_file = Path(pdf_file)
        with pdfplumber.open(pdf_file) as pdf:

            # Rain data
            df = cls._scrap_table(pdf.pages[1].extract_table())

            # Sun data
            df_sun = cls._scrap_table(pdf.pages[4].extract_table())

            dest_file = pdf_file.with_suffix('.xlsx')
            with pd.ExcelWriter(dest_file) as writer:  # doctest: +SKIP
                df.to_excel(writer, sheet_name='Rain')
                df_sun.to_excel(writer, sheet_name='Sun')


PLUVIO_INI = "pluvio.ini"
MATCH_NUM_ZONE_SHAPEFILE_INS_INDEX = "Match_num_zone_shapefile_INS_index.txt"
EXTREME_PRECIP_COMMUNES = "Extreme_rain_ins.txt"
GEOMETRY_MUNICIPALITIES = "PDS__COMMUNES.shp"

class QDF_Hydrology():
    """ Prepare data from IRM website for WOLF hydrology calculations.

    We need :
    - pluvio.ini
    - Match_num_zone_shapefile_INS_index.txt

    "pluvio.ini" contains the path to the rainfall data files for each locality:
    - Extreme_precip_communes.txt

    """

    def __init__(self, store_path= DATADIR / 'irm_qdf',
                 ini_file:str = PLUVIO_INI,
                 ins:Literal['2018', 2018] = 2018,
                 geometry:str = GEOMETRY_MUNICIPALITIES) -> None:

        self.store_path = Path(store_path)
        self._data:dict[int, Qdf_IRM] = {}

        self._ins = ins # INS version to use. IRM has updated the QDF data in 2016, so we force the use of the 2018 version.

        self._extreme_file = EXTREME_PRECIP_COMMUNES
        self._nb_lines_extreme_file = 0
        self._nb_cols_extreme_file = 0

        self.localities = Localities(ins)

        self._ini_file = ini_file

        self._geometry = geometry
        self._geometry_df = None

        if not self.store_path.exists():
            self.store_path.mkdir(parents=True, exist_ok=True)

        if not self.store_path.joinpath(self._geometry).exists():
            # get the municipalities shapefile from HECE Gitlab public repository
            self.download_municipalities_2018()

        try:
            if self.store_path.joinpath(self._geometry).exists():
                self._geometry_df = gpd.read_file(self.store_path / self._geometry)
            else:
                logging.error(f"Geometry file {self._geometry} not found in {self.store_path}.")
                logging.error("Please download the 2018 version of municipalities shapefile from HECE or what you want.")
                return
        except Exception as e:
            logging.error(f"Error reading geometry file {self._geometry}: {e}")
            self._geometry_df = None

        if not self.store_path.joinpath(ini_file).exists():
            self.create_default_data()

        self.read_data()

    def read_data(self):
        """ Read the data from the ini file and the extreme precipitation file. """

        try:
            with open(self.store_path / PLUVIO_INI, 'r') as f:
                lines = f.readlines()
                self._extreme_file = lines[0].strip()
                self._nb_lines_extreme_file = int(lines[1].strip())
                self._nb_cols_extreme_file = int(lines[2].strip())

                _nb_return_periods = int(lines[3].strip())
                _nb_values_per_return_period = int(lines[4].strip())

                rt =[]
                for i in range(_nb_return_periods):
                    try:
                        rt.append(int(lines[5 + i].strip()))
                    except ValueError:
                        logging.error(f"Invalid return period value in ini file: {lines[5 + i].strip()}")
                        rt.append(0)

                if self.store_path.joinpath(self._extreme_file).exists():
                    df = pd.read_csv(self.store_path / self._extreme_file, sep='\t', header=None)
                    # Set column names based on the number of return periods and values per return period
                    columns = ['INS', 'Duration']
                    for rt_value in rt:
                        for value_type in ['Q', 'Std', 'Low', 'Up']:
                            columns.append(f"{rt_value}_{value_type}")
                    df.columns = columns

                    all_ins = df['INS'].astype(int).unique()
                    self._data = {ins: Qdf_IRM(store_path=self.store_path, code=ins, localities=self.localities, dataframe=df[df['INS'] == ins]) for ins in all_ins}

                else:
                    logging.error(f"Extreme precipitation file {self._extreme_file} not found in {self.store_path}.")
                    self._data = {}
        except:
            logging.error(f"Error during reading {self._ini_file} in {self.store_path}.")
            logging.error("Check your data or delete files in the directory to force a new download.")
            self._data = {}
            self._extreme_file = None
            self._nb_lines_extreme_file = 0
            self._nb_cols_extreme_file = 0

    def __getitem__(self, key) -> Qdf_IRM:
        """ Get the QDF data for a given INS code. """

        if isinstance(key, int):
            ins_code = key
        elif isinstance(key, str):
            ins_code = self.localities.get_INSfromname(key)
            if ins_code is None:
                try:
                    # Try to convert the string to an integer (INS code)
                    ins_code = int(key)
                except ValueError:
                    # If it fails, raise an error
                    raise KeyError(f"Locality {key} not found.")
        else:
            raise TypeError("Key must be an integer (INS code) or a string (locality name).")

        if ins_code in self._data:
            return self._data[ins_code]
        else:
            raise KeyError(f"Data for INS code {ins_code} not found.")

    def __iter__(self):
        """ Iterate over all QDF data. """
        for ins_code in self._data:
            yield self._data[ins_code]

    def download_municipalities_2018(self, force:bool = False):
        """ Download the municipalities shapefile from HECE.

        :param force: If `True`, will download the file even if it already exists.
        """
        munic = Path(toys_dataset('Communes_Belgique', 'PDS__COMMUNES.zip'))

        # Unzip the file if it is not already unzipped.
        if munic.exists():
            import zipfile
            with zipfile.ZipFile(munic, 'r') as zip_ref:
                zip_ref.extractall(self.store_path)

        self._geometry = 'PDS__COMMUNES.shp'

    def create_match_num_zone_shapefile(self):
        """ Create the Match_num_zone_shapefile_INS_index.txt file.

        This file contains the mapping between the INS codes and the shapefile
        indices.
        """

        match_file = self.store_path / MATCH_NUM_ZONE_SHAPEFILE_INS_INDEX

        colname = 'INS'
        if colname not in self._geometry_df.columns:
            colname = 'NSI'  # Use NSI if INS is not available
        if colname not in self._geometry_df.columns:
            logging.error(f"Column {colname} not found in the geometry DataFrame.")
            return

        if not match_file.exists():
            with open(match_file, 'w') as f:
                for idx, row in self._geometry_df.iterrows():
                    f.write(f"{row[colname]}\n")

    def create_default_data(self):
        """ Create data from scratch for WOLF hydrology calculations. """
        self.create_match_num_zone_shapefile()
        self.create_extreme_precipitation_file()
        self.create_ini_file()

    def create_extreme_precipitation_file(self):
        """ Create the extreme precipitation file for all localities.

        Each line of the file contains the following data:
        - INS code
        - Duration in seconds
        - Quantity for each return period (RT2, RT5, RT10, RT20, RT50, RT100)
        """
        self.extreme_file = self.store_path / EXTREME_PRECIP_COMMUNES

        if not self.extreme_file.exists():

            all_qdf = QDF_Belgium(store_path=self.store_path, ins=self._ins, force_import=False)

            self._nb_lines_extreme_file = 0
            with open(self.extreme_file, 'w') as f:
                for loc in all_qdf:
                    loc:Qdf_IRM
                    ins = loc.code
                    qdf = loc.qdf
                    low = loc.confintlow
                    up = loc.confintup
                    std = loc.standarddev

                    for (dur_text, dur_s) in zip(durationstext, durations_seconds):
                        data = [ins]
                        data.append(int(dur_s))
                        for rt in RT:
                            data.append(qdf.loc[dur_text, rt])
                            data.append(std.loc[dur_text, rt])
                            data.append(low.loc[dur_text, rt])
                            data.append(up.loc[dur_text, rt])
                        f.write("\t".join(map(str, data)) + "\n")

                        self._nb_lines_extreme_file += 1
                        self._nb_cols_extreme_file = len(data)

    def create_ini_file(self):
        """
        Create a parameter file for the class
        """

        with open(self.store_path / PLUVIO_INI, 'w') as f:
            f.write(f"{self._extreme_file}\n") # name of the file containing the extreme precipitation data

            if self._nb_lines_extreme_file == 0 or self._nb_cols_extreme_file == 0:
                with open(self.store_path / self._extreme_file, 'r') as ef:
                    lines = ef.readlines()
                    self._nb_lines_extreme_file = len(lines)
                    if lines:
                        self._nb_cols_extreme_file = len(lines[0].strip().split('\t'))
                    else:
                        self._nb_cols_extreme_file = 0

            f.write(f"{self._nb_lines_extreme_file}\n") # number of lines in the extreme precipitation file
            f.write(f"{self._nb_cols_extreme_file}\n") # number of columns in the extreme precipitation file
            f.write(f"{len(RT)}\n") # Number of return periods
            f.write("4\n") # Number of values par return period (Q, std, low, up)
            for rt in RT:
                f.write(f"{rt}\n")

    def get_all_ins(self) -> list[int]:
        """ Get a list of all INS codes. """
        return list(self._data.keys())

class QDF_Hydrology_Draw(Element_To_Draw):

    """ Class to draw the QDF hydrology data on a map.

    This class is used to draw the QDF hydrology data on a map using the
    WOLF hydrology calculations.
    """

    def __init__(self, store_path= DATADIR / 'irm_qdf', ins:Literal['2018', 2018] = 2018, idx:str = '', plotted:bool = True, mapviewer = None) -> None:

        super().__init__(idx=idx, plotted=plotted, mapviewer=mapviewer)

        self._qdf_hydrology = QDF_Hydrology(store_path=store_path, ins=ins)

        from .PyPictures import PictureCollection

        self._scale_factor = 1.0  # Default scale factor for images

        self._geometry_zones = Zones('', idx= idx+'_zones', plotted=plotted, mapviewer=mapviewer, parent = mapviewer)
        self._geometry_tables = PictureCollection('', idx= idx, plotted=plotted, mapviewer=mapviewer, parent = mapviewer)
        self._geometry_plots = PictureCollection('', idx= idx, plotted=plotted, mapviewer=mapviewer, parent = mapviewer)

        self._geometry_zones.import_shapefile(self.store_path / self._qdf_hydrology._geometry, colname='NSI')
        self._geometry_zones.prep_listogl()

        self._geometry_tables.import_shapefile(self.store_path / self._qdf_hydrology._geometry, colname='NSI')
        self._geometry_plots.import_shapefile(self.store_path / self._qdf_hydrology._geometry, colname='NSI')
        self._prepare_image_location()

        self._centroids = {curzone[0].centroid: curzone.myname for curzone in self._geometry_tables.myzones}

        self._show_table = False
        self._show_plot = False
        self._reload_images = True
        self._current_images = None

    def _get_vector_tables(self, ins:str | int) -> vector:
        """ Get the vector for a given INS code. """
        return self._geometry_tables[(str(ins), str(ins))]

    def _get_vector_plots(self, ins:str | int) -> vector:
        """ Get the vector for a given INS code. """
        return self._geometry_plots[(str(ins), str(ins))]

    @property
    def store_path(self):
        """ Get the store path for the QDF hydrology data. """
        return self._qdf_hydrology.store_path

    def _prepare_image_location(self):
        """ Set the default size for the images. """

        # plots
        DEFAULT_SIZE = 2000. * self._scale_factor  # Default size for the images
        RAP_W_H = 3600. / 2400.
        WIDTH_PLOTS = DEFAULT_SIZE * RAP_W_H
        HEIGHT_PLOTS = DEFAULT_SIZE

        for curzone in self._geometry_plots.myzones:
            vec = curzone[0]
            vec.myprop.image_attached_pointx = vec.centroid.x
            vec.myprop.image_attached_pointy = vec.centroid.y
            vec.myprop.imagevisible = False

            x, y = vec.centroid.x, vec.centroid.y
            y -= HEIGHT_PLOTS / 2.

            vec.myvertices = [wv(x - WIDTH_PLOTS, y - HEIGHT_PLOTS),
                                wv(x + WIDTH_PLOTS, y - HEIGHT_PLOTS),
                                wv(x + WIDTH_PLOTS, y + HEIGHT_PLOTS),
                                wv(x - WIDTH_PLOTS, y + HEIGHT_PLOTS),
                                wv(x - WIDTH_PLOTS, y - HEIGHT_PLOTS)]
            vec.myprop.color = getIfromRGB([255, 255, 255, 0])  # Transparent color
            vec.find_minmax()

        self._geometry_plots.prep_listogl()


        # tables
        RAP_W_H = 1730. / 2000.
        WIDTH_TABLES = DEFAULT_SIZE * RAP_W_H
        HEIGHT_TABLES = DEFAULT_SIZE
        for curzone in self._geometry_tables.myzones:
            vec = curzone[0]
            vec.myprop.image_attached_pointx = vec.centroid.x
            vec.myprop.image_attached_pointy = vec.centroid.y
            vec.myprop.imagevisible = False

            x, y = vec.centroid.x, vec.centroid.y
            y +=  2. * HEIGHT_TABLES - (HEIGHT_PLOTS / 2.) * 3./4.

            vec.myvertices = [wv(x - WIDTH_TABLES, y - HEIGHT_TABLES),
                                wv(x + WIDTH_TABLES, y - HEIGHT_TABLES),
                                wv(x + WIDTH_TABLES, y + HEIGHT_TABLES),
                                wv(x - WIDTH_TABLES, y + HEIGHT_TABLES),
                                wv(x - WIDTH_TABLES, y - HEIGHT_TABLES)]
            vec.myprop.color = getIfromRGB([255, 255, 255, 0])
            vec.find_minmax()

        self._geometry_tables.prep_listogl()

    def set_images_as_legend(self, plot_or_table:Literal['plot', 'table'] = 'plot', which:list = None):
        """ Set all images in the collection as legend images. """

        DEFAULT_SIZE = 2000. * self._scale_factor  # Default size for the images

        if which is None:
            which = self._qdf_hydrology.get_all_ins()

        if plot_or_table == 'plot':

            RAP_W_H = 3600. / 2400.
            WIDTH = DEFAULT_SIZE * RAP_W_H
            HEIGHT = DEFAULT_SIZE

            for loc_ins in which:
                loc_qdf = self._qdf_hydrology[loc_ins]
                if loc_qdf.path_image_plot is not None:
                    vec = self._get_vector_plots(loc_qdf.code)
                    vec.myprop.image_path = loc_qdf.path_image_plot
                    centroid = vec.centroid
                    vec.myprop.image_attached_pointx, vec.myprop.image_attached_pointy = centroid.x, centroid.y
                    vec.myprop.imagevisible = True

                    vec.myvertices = [wv(centroid.x - WIDTH, centroid.y - HEIGHT),
                                      wv(centroid.x + WIDTH, centroid.y - HEIGHT),
                                      wv(centroid.x + WIDTH, centroid.y + HEIGHT),
                                      wv(centroid.x - WIDTH, centroid.y + HEIGHT),
                                      wv(centroid.x - WIDTH, centroid.y - HEIGHT)]

                    vec.myprop.color = getIfromRGB([255, 255, 255, 0])
                    vec.find_minmax()

            self._geometry_plots.reset_listogl()
            self._geometry_plots.prep_listogl()

        elif plot_or_table == 'table':

            RAP_W_H = 1730. / 2000.
            WIDTH = DEFAULT_SIZE * RAP_W_H
            HEIGHT = DEFAULT_SIZE

            for loc_ins in which:
                loc_qdf = self._qdf_hydrology[loc_ins]
                if loc_qdf.path_image_table is not None:
                    vec = self._get_vector_tables(loc_qdf.code)
                    vec.myprop.image_path = loc_qdf.path_image_table
                    centroid = vec.centroid
                    vec.myprop.image_attached_pointx, vec.myprop.image_attached_pointy = centroid.x, centroid.y
                    vec.myprop.imagevisible = True

                    vec.myvertices = [wv(centroid.x - WIDTH, centroid.y - HEIGHT),
                                      wv(centroid.x + WIDTH, centroid.y - HEIGHT),
                                      wv(centroid.x + WIDTH, centroid.y + HEIGHT),
                                      wv(centroid.x - WIDTH, centroid.y + HEIGHT),
                                      wv(centroid.x - WIDTH, centroid.y - HEIGHT)]

                    vec.myprop.color = getIfromRGB([255, 255, 255, 0])
                    vec.find_minmax()

            self._geometry_tables.reset_listogl()
            self._geometry_tables.prep_listogl()

    def hide_all_images(self):
        """ Hide all images in the collection. """

        for curzone in self._geometry_tables.myzones:
            curzone[0].myprop.imagevisible = False
        self._geometry_tables.reset_listogl()

        for curzone in self._geometry_plots.myzones:
            curzone[0].myprop.imagevisible = False
        self._geometry_plots.reset_listogl()

    def check_plot(self):
        return super().check_plot()

    def find_nearest_centroid(self, x: float, y: float, bounds: tuple[float, float, float, float]):
        """ Pick the municipality at the given coordinates.

        :param x: The x coordinate.
        :param y: The y coordinate.
        :return: The name of the municipality or an empty string if not found.
        """

        centroids = self.find_centroid_in_bounds(bounds)
        if not centroids:
            return ''

        # Find the centroid closest to the given point
        closest_centroid = min(centroids, key=lambda c: c[0].distance(Point(x, y)))
        return closest_centroid[1]

    def pick_municipality(self, x: float, y: float, bounds: tuple[float, float, float, float]):
        """ Activate plot for the nearest municipality to the given coordinates. """

        which = [self.find_nearest_centroid(x, y, bounds)]

        for loc_ins in which:
            loc_qdf = self._qdf_hydrology[loc_ins]
            if loc_qdf.path_image_plot is not None and loc_qdf.path_image_table is not None:
                vec_plt = self._get_vector_plots(loc_qdf.code)
                vec_tables = self._get_vector_tables(loc_qdf.code)

                if vec_plt.myprop.imagevisible or vec_tables.myprop.imagevisible:
                    vec_plt.myprop.imagevisible = False
                    vec_tables.myprop.imagevisible = False
                else:
                    vec_plt.myprop.image_path = loc_qdf.path_image_plot
                    vec_plt.myprop.imagevisible = True
                    vec_tables.myprop.image_path = loc_qdf.path_image_table
                    vec_tables.myprop.imagevisible = True

        # Reset the OpenGL lists to reflect the changes
        self._geometry_plots.reset_listogl()
        self._geometry_plots.prep_listogl()

        self._geometry_tables.reset_listogl()
        self._geometry_tables.prep_listogl()


    def find_centroids_in_polygon(self, polygon: Polygon) -> list[tuple[vector, str]]:
        """ Find all centroids in a given polygon.

        :param polygon: A shapely Polygon object defining the area to search.
        """

        centroids = []
        for centroid, name in self._centroids.items():
            if centroid.within(polygon):
                centroids.append((centroid, name))

        # Sort centroids by distance to the center of the polygon
        center_x, center_y = polygon.centroid.x, polygon.centroid.y
        dist_to_center = lambda c: ((c.x - center_x) ** 2 + (c.y - center_y) ** 2) ** 0.5
        centroids.sort(key=lambda c: dist_to_center(c[0]))

        return centroids

    def find_centroid_in_bounds(self, bounds: tuple[float, float, float, float]) -> list[tuple[vector, str]]:
        """ Find all centroids within the given bounds.

        :param bounds: A tuple of (minx, miny, maxx, maxy) defining the bounding box.
        """

        minx, miny, maxx, maxy = bounds
        centroids = []
        for centroid, name in self._centroids.items():
            if minx <= centroid.x <= maxx and miny <= centroid.y <= maxy:
                centroids.append((centroid, name))

        dist_to_center = lambda c: ((c.x - (minx + maxx) / 2) ** 2 + (c.y - (miny + maxy) / 2) ** 2) ** 0.5
        centroids.sort(key=lambda c: dist_to_center(c[0]))

        return centroids

    @property
    def show_plot(self) -> bool:
        """ Check if the plot is shown. """
        return self._show_plot

    @show_plot.setter
    def show_plot(self, value: bool):
        """ Set whether to show the plot or not. """
        self._show_plot = value
        if not value:
            self.hide_all_images()
        self._reload_images = value

    @property
    def show_table(self) -> bool:
        """ Check if the table is shown. """
        return self._show_table

    @show_table.setter
    def show_table(self, value: bool):
        """ Set whether to show the table or not. """
        self._show_table = value
        if not value:
            self.hide_all_images()
        self._reload_images = value

    def scale_images(self, factor:float = 1.0):
        """ Scale the images in the collection by a given factor.

        :param factor: The scaling factor to apply to the images.
        """
        assert isinstance(factor, (int, float)), "Scaling factor must be a number."

        self._geometry_tables.scale_all_pictures(factor)
        self._geometry_plots.scale_all_pictures(factor)

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """ Plot the QDF hydrology data on the map. """

        NB_MAX = 10  # Maximum number of images to display

        if self.show_plot and self._reload_images:
            _new_images = self.find_centroid_in_bounds((xmin, ymin, xmax, ymax))
            self._reload_images = False

            if len(_new_images) > NB_MAX:
                logging.warning(_(f"Too many images to display. Showing only the first {NB_MAX}."))
                _new_images = _new_images[:NB_MAX]

            if self._current_images is None or len(_new_images) != len(self._current_images):
                self.set_images_as_legend(plot_or_table='plot', which=[img[1] for img in _new_images])

        elif self.show_table and self._reload_images:

            _new_images = self.find_centroid_in_bounds((xmin, ymin, xmax, ymax))
            self._reload_images = False

            if len(_new_images) > NB_MAX:
                logging.warning(_(f"Too many images to display. Showing only the first {NB_MAX}."))
                _new_images = _new_images[:NB_MAX]

            if self._current_images is None or len(_new_images) != len(self._current_images):
                self.set_images_as_legend(plot_or_table='table', which=[img[1] for img in _new_images])

        self._geometry_tables.plot(sx=sx, sy=sy, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, size=size)
        self._geometry_plots.plot(sx=sx, sy=sy, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, size=size)
        self._geometry_zones.plot(sx=sx, sy=sy, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, size=size)
