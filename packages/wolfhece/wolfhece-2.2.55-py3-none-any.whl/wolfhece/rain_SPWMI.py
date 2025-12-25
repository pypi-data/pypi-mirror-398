"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os.path import join,exists,normpath
import requests
import pandas as pd
import numpy as np
from calendar import month, monthrange
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from sympy import lowergamma
import time
import re

from .PyTranslate import _

STATIONS_MI_RAIN="""92150015	PETIGNY Barrage
92880015	CUL-DES-SARTS
91370015	BOUSSU-EN-FAGNE
10430015	WAVRE
10810015	BOUSVAL
60480015	RACHAMPS-NOVILLE
61280015	ORTHO
61680015	SAINT-HUBERT aéro
68580015	TAILLES
70030015	SART-TILMAN
70160015	OUFFET
70180015	MEAN
70480015	EREZEE
70870015	MARCHE
10570015	LOUVAIN LA NEUVE
15790015	PERWEZ
15840015	HELECINE
18980015	UCCLE
19540015	TUBIZE
19970015	SOIGNIES
23480015	LILLOIS
23880015	SENEFFE
24590015	DERGNEAU
28920015	ENGHIEN
29930015	CHIEVRES
32770015	KAIN
34760015	MOUSCRON
35340015	WASMUEL
35720015	TRIVIERES
36280015	ROISIN
36470015	ROUVEROY
36490015	BLAREGNIES
37170015	PERUWELZ
38850015	COMINES Barrage-Ecl
52840015	GEMMENICH
55780015	WAREMME
55960015	AWANS
56490015	BATTICE
57570015	LANAYE
64970015	TERNELL
65290015	MONT-RIGI
65380015	SPA aerodrome
65500015	JALHAY
66570015	LOUVEIGNE
67120015	COO INF.
67120115	COO INF.
67180015	COO SUP.
67180115	COO SUP.
68480015	VIELSALM
69580015	ROBERTVILLE
69670015	BUTGENBACH
69670115	BUTGENBACH
71680015	LANDENNE
72280015	MODAVE
72960015	VEDRIN
73350015	MORNIMONT Bar-Ecluse
73690015	CHATELET
73950015	MONCEAU Bar-Ecluse
74850015	SOLRE S/S Bar-Ecluse
75770015	MOMIGNIES
76290015	LIGNY
76780015	GERPINNES
78650015	PLATE TAILLE
78880015	SENZEILLES
79670015	SIVRY
80630015	ANSEREMME
81280015	SAINT-GERARD
81380015	CRUPET
81570015	CINEY
81890015	FLORENNES
83480015	DAVERDISSE
83880015	LIBIN
84680015	BEAURAING
85180015	ROCHEFORT
85380015	NASSOGNE
86770015	GEDINNE
86870015	CROIX-SCAILLE
94360015	VRESSE
94690015	BOUILLON
95740015	FRATIN
95880015	MEIX-LE-TIGE
95960015	ARLON
95960115	ARLON
96170015	SUGNY
96320015	BERTRIX
96520015	STRAIMONT
96980015	NAMOUSSART
97430015	TORGNY
97810015	ATHUS
97940015	AUBANGE
97970015	SELANGE
98160015	ORVAL
99150015	STEFFESHAUSEN
99220015	SANKT-VITH
99480015	BASTOGNE
"""

STATS_HOURS_IRM=np.asarray([1,2,3,6,12,24,2*24,3*24,4*24,5*24,7*24,10*24,15*24,20*24,25*24,30*24],dtype=np.int32)
STATS_MINUTES_IRM=np.asarray(STATS_HOURS_IRM)*60

class SPW_MI_pluvioraphs():
    """
    Gestion des données pluviographiques du SPW-MI au travers de l'ancien site web "voies-hydrauliques.be"
    http://voies-hydrauliques.wallonie.be/opencms/opencms/fr/hydro/Archive/
    """

    def __init__(self) -> None:
        #Création de 2 dictionnaires de recherche sur base de la chaîne
        self.code2name={}
        self.name2code={}
        self.db_rains = None

        for mypluvio in STATIONS_MI_RAIN.splitlines():
            mycode,myname=mypluvio.split("\t")
            self.code2name[mycode]=myname
            self.name2code[myname.lower()]=mycode

    def get_names(self):
        return list(self.name2code.keys())
    def get_codes(self):
        return list(self.code2name.keys())

    def get_rain_fromweb(self,fromyear,toyear,code='',name='',filterna=True):
        rain=[]
        for curyear in range(fromyear,toyear+1):
            rain.append(self.get_yearrain_fromweb(curyear,code,name,filterna))
            print(curyear)
        try:
            return pd.concat(rain)
        except:
            return None

    def get_yearrain_fromweb(self,year=2021,code='',name='',filterna=True):
        rain=[]
        for curmonth in range(1,13):
            rain.append(self.get_monthrain_fromweb(curmonth,year,code,name))

        try:
            rain = pd.concat(rain)

            if filterna:
                rain[rain.isna()]=0.

            return rain
        except:
            return None

    def get_monthrain_fromweb(self,month=7,year=2021,code='',name='',mysleep=.2):
        """Récupération des données au pas horaire depuis le site SPW-MI VH

        On lit les informations pour l'ensemble du mois

        http://voies-hydrauliques.wallonie.be/opencms/opencms/fr/hydro/Archive/
        """

        station=code
        if name!="":
            station=self.name2code[name.lower()]

        #calcul du nombre de jours dans le mois souhaité
        nbdays = monthrange(year, month)[1]

        url="http://voies-hydrauliques.wallonie.be/opencms/opencms/fr/hydro/Archive/annuaires/stathorairetab.do?code="+station+"&mois="+str(month)+"&annee="+str(year)

        res=requests.get(url)
        html_tables = pd.read_html(res.content, match='.+')

        startdate = dt.date(year,month,1)
        enddate = startdate+pd.DateOffset(months=1)
        try:
            #analyse du tableau HTML qui contient les données de pluie
            rain = html_tables[12].to_numpy()[0:24,1:nbdays+1].astype('float').reshape(24*nbdays,order='F')
            rain = pd.Series(rain,index=pd.date_range(startdate,enddate,inclusive='left',freq='1H'))

        except:
            rain=np.zeros(nbdays*24)
            rain = pd.Series(rain,index=pd.date_range(startdate,enddate,inclusive='left',freq='1H'))
            pass

        time.sleep(mysleep)

        return rain

    def compute_stats_Q(self,rain,listhours):
        """
        Calcul des stats des "cumul maximaux" par convolution sur base d'un vecteur de nombre d'heures
        Unité : mm
        """
        mymaxQ=np.zeros(len(listhours),dtype=np.float64)
        k=0

        for locstat in listhours:
            a = np.ones(locstat)
            mymaxQ[k]=np.max(np.convolve(rain,a,'same'))
            k+=1

        return mymaxQ

    def compute_stats_i(self,rain,listhours):
        """
        Calcul des stats des "intensités moyennes maximales" par convolution sur base d'un vecteur de nombre d'heures
        Unité : mm/h
        """
        mymeanQ=self.compute_stats_Q(rain,listhours)/np.asarray(listhours,dtype=np.float64)

        return mymeanQ

    def plot(self,rain:pd.Series,toshow=False,xbounds=None,ticks='M',ExistingFig=None):

        if ExistingFig is None:
            fig,ax = plt.subplots(1,1,figsize=(15,8))
        else:
            fig=ExistingFig[0]
            ax=ExistingFig[1]

        x = rain.index

        if not xbounds is None:
            minyear = xbounds[0].year
            maxyear = xbounds[1].year+1
            if ticks=='M':
                xticks = [xbounds[0]+pd.DateOffset(months=k) for k in range(int((xbounds[1]-xbounds[0]).days/30)+1)]
            elif ticks=='D':
                xticks = [xbounds[0]+pd.DateOffset(days=k) for k in range(int((xbounds[1]-xbounds[0]).days))]
            elif ticks=='2H':
                xticks = [xbounds[0]+pd.DateOffset(hours=k) for k in range(0,int((xbounds[1]-xbounds[0]).days*24),2)]
            elif ticks=='H':
                xticks = [xbounds[0]+pd.DateOffset(hours=k) for k in range(int((xbounds[1]-xbounds[0]).days*24))]
        else:
            minyear = x[0].year
            maxyear = x[-1].year+1

            xticks = [dt.datetime(minyear,1,1)+pd.DateOffset(months=k) for k in range(0,(maxyear-minyear)*12+1,3)]

        ax.fill_between(rain.index,rain.values,step='pre',alpha=0.7)
        ax.step(rain.index,rain.values,where='pre',label=rain.name)
        ax.set_xticks(xticks)

        if ticks=='M':
            ax.set_xticklabels([curtick.strftime('%b/%Y') for curtick in xticks],rotation=45, fontsize=8)
        elif ticks=='D':
            ax.set_xticklabels([curtick.strftime('%d/%m/%Y') for curtick in xticks],rotation=45, fontsize=8)
        elif ticks=='2H' or ticks=='H':
            ax.set_xticklabels([curtick.strftime('%d/%m %H:%M') for curtick in xticks],rotation=45, fontsize=8)

        ax.set_xlabel('Date')
        ax.set_ylabel('Précipitation moyenne horaire [mm/h]')
        ax.legend()

        if not xbounds is None:
            ax.set_xlim(xbounds)

        if toshow:
            plt.show()

        return fig,ax

    def plot_periodic(self,rain:pd.Series,origin:dt.datetime,offset_in_months,toshow=False):
        """Comparaison de plusieurs années sur un même horizon d'une snnée totale"""
        fig,ax = plt.subplots(1,1,figsize=(15,8))

        end = rain.index[-1]

        startdate=origin
        enddate = origin

        offset = pd.DateOffset(months=offset_in_months)

        while enddate<=end:

            enddate = startdate + offset

            locrain = rain[startdate:enddate]

            if len(locrain>0):
                i1=(locrain.index[0]-startdate).days*24
                x = np.arange(i1,i1+len(locrain.values))

                # ax.fill_between(x,locrain.values,step='pre',alpha=0.5)
                ax.step(x,locrain.values,where='pre')

            startdate=enddate

        xticks = [k*30*24 for k in range(offset_in_months+1)]
        ax.set_xticks(xticks)
        ax.set_xticklabels([str(k*30) for k in range(offset_in_months+1)])

        if toshow:
            plt.show()

    def saveas(self,rain:pd.Series,filename:str):
        rain.to_csv(filename,header=['Data'])

    def fromcsv(self,stationame='',stationcode=0,filename:str='',fromdate:dt.datetime=None,todate:dt.datetime=None):

        myname=filename
        if stationame!='':
            myname=stationame
            filename = self.name2code[stationame.lower()]+'.csv'
            filename = join('spw',filename)
        elif stationcode>0:
            myname = self.code2name(stationcode)
            filename = str(stationcode)+'.csv'
            filename = join('spw',filename)

        if exists(filename):
            mydata= pd.read_csv(filename,header=0,index_col=0,parse_dates=True).squeeze("columns")
            mydata.name=myname.upper()
        else:
            return

        if fromdate is None and todate is None:
            return mydata
        elif fromdate is None:
            return mydata[:todate]
        elif todate is None:
            return mydata[fromdate:]
        else:
            return mydata[fromdate:todate]

    def from_xlsx_SPW(self,dir='',stationame='',stationcode=0,fromdate:dt.datetime=None,todate:dt.datetime=None,create_db=False):
        """Lecture de plusieurs fichiers Excel en autant de séries de pluies
        Renvoi d'un dictionnaire avec la série"""

        from os import listdir

        if dir =='' and self.db_rains is None:
            return None

        def read_xls_rainSPW(dir,filename=''):
            """Lecture du fichier Excel"""
            if filename=='':
                return None

            myrains = pd.read_excel(join(dir,filename))
            myrains = myrains.dropna(how='all').dropna(how='all', axis=1)
            myrains.columns=myrains.iloc[0]
            myrains=myrains.iloc[1:]
            myrains=myrains.set_index('Date')

            #On supprimme les espaces multiples pour avoir une en-tête de colonne correcte
            newnames = [re.sub(' +',' ',curstat) for curstat in myrains.keys()]
            myrains.columns=newnames

            return myrains

        def split_series(mydataframe:pd.DataFrame):
            """Split du dataframe général en séries pandas"""
            myseries={}
            for curcol in mydataframe.keys():
                locser=mydataframe[curcol].squeeze()

                #on recherche la première valeur non NaN
                first = locser.first_valid_index()
                #on recherche la dernière valeur non NaN
                last = locser.last_valid_index()
                #on remplit les NaN avec 0.
                myseries[int(curcol.split()[0])] = locser[first:last].fillna(0.)
            return myseries

        if self.db_rains is None:
            filenames=[]
            for file in listdir(dir):
                if file.endswith(".xlsx"):
                    filenames.append(file)

            myrains=pd.concat([read_xls_rainSPW(dir,filename) for filename in filenames],sort=True)
            myser =split_series(myrains)

            if create_db:
                self.db_rains = myser
        else:
            myser = self.db_rains

        if stationame!='' or stationcode!='':
            if stationame!='':
                stationcode = int(self.name2code[stationame.lower()])

            if stationcode in myser.keys():
                mydata = myser[stationcode]

                if fromdate is None and todate is None:
                    return mydata
                elif fromdate is None:
                    return mydata[:todate]
                elif todate is None:
                    return mydata[fromdate:]
                else:
                    return mydata[fromdate:todate]
            else:
                return None
        else:
            return myser

    def import_all(self,dirout,fromyear=2002,toyear=2021):
        dirout=normpath(dirout)
        for curstation in self.code2name.keys():
            myflow = self.get_rain_fromweb(fromyear,toyear,curstation)
            if not myflow is None:
                self.saveas(myflow,join(dirout,curstation+'.csv'))
            print(curstation)

if __name__=="__main__":
    #exemple
    my = SPW_MI_pluvioraphs()
    myrain=my.get_monthrain_fromweb(name="Jalhay")
    mystats=my.compute_stats_Q(myrain,STATS_HOURS_IRM)
    print(mystats)
