"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from operator import mod
import requests
import pandas as pd
import numpy as np
from calendar import monthrange
from datetime import timedelta, date
import matplotlib.pyplot as plt
import datetime as dt
from os.path import join,normpath,exists
import re
import time

from .PyTranslate import _

#Liste des stations SPW-MI en date du 05/2022
STATIONS_MI_FLOW="""6228	CHAUDFONTAINE
1951	TUBIZE
2341	CLABECQ
2371	RONQUIERES
2473	OISQUERCQ
2483	RONQUIERES Bief Aval
2536	GOUY
2537	GOUYCanal
2707	LESSINESBiefAmont
2713	PAPIGNIESBiefAval
2952	IRCHONWELZ
2971	ATHDENDREORIENTALE
3274	KAIN Avnt Bar-Ecl
3282	TOURNAI
3561	BOUSSOIT
3643	HYON
3778	SAINT-DENIS
3884	COMINES Aval Bar-Ecl
3886	COMINES Amont
3891	PLOEGSTEERT
5291	KELMIS
5436	LIXHE Aval
5447	LIXHE Bief Amont
5572	BERGILERS Amont
5771	HACCOURT
5796	MAREXHE
5804	ANGLEUR GR
5806	ANGLEUR GR
5826	SAUHEID
5857	MERy
5904	COMBLAIN-AU-PONT
5921	TABREUX
5922	HAMOIR
5953	DURBUY
5962	HOTTON
5991	NISRAMONT
6021	MABOMPRe
6122	ORTHO
6228	CHAUDFONTAINE
6387	EUPEN
6517	POLLEUR
6526	BELLEHEID
6621	MARTINRIV
6651	REMOUCHAMPS
6671	TARGNON
6732	STAVELOT
6753	LASNENVILLE
6803	CHEVRON
6832	TROIS-PONTS
6933	MALMEDY
6946	BEVERCE
6971	WIRTZFELD
6981	BULLINGEN
6991	MALMEDY
7117	IVOZ-RAMET
7132	AMAY
7137	AMPSIN
7139	HUYUS
7141	HUY
7228	MODAVE
7242	MOHA
7244	HUCCORGNE
7319	SALZINNES
7394	MONCEAU_Aval_Bar-EcL
7396	MONCEAU_AmBar-Ecl
7466	FONT-VALMON_Am B-E
7474	LABUISSIERE__Av B-E
7487	SOLRE
7711	JAMIOUL
7781	WALCOURT
7784	WALCOURT
7812	WALCOURT-VOGENEE
7831	SILENRIEUX
7843	BOUSSU-LEZ-WALCOURT
7863	SILENRIEUX
7883	SOUMOY
7891	CERFONTAINE
7944	WIHERIES
7978	BERSILLIES-L'ABBAYE
8017	PROFONDEVILLE
8022	LUSTIN
8059	DINA
8067	ANSEREMME Monia
8134	YVOIR
8163	WARNANT
8166	SOSOYE
8181	FOY
8221	GENDRON
8231	HOUYET
8341	DAVERDISSE
8527	JEMELLE
8622	HASTIERE
8661	FELENNE
8702	CHOOZ
9021	TREIGNES
9071	COUVIN
9081	NISMES
9111	MARIEMBOURG
9201	COUVIN Ry de Rome
9221	PETIGNY Ry de Rome
9223	PETIGNY Ermitage
9224	PETIGNY Fd Serpents
9232	BRULY RY PERNELLE
9434	MEMBRE Pont
9435	MEMBRE Amont
9461	BOUILLON
9531	LACUISINE
9541	CHINY
9561	TINTIGNY
9571	SAINTE-MARIE
9651	STRAIMONT
9741	TORGNY
9914	REULAND
9926	SCHOENBERG
"""

STATS_HOURS_IRM=np.asarray([1,2,3,6,12,24,2*24,3*24,4*24,5*24,7*24,10*24,15*24,20*24,25*24,30*24],dtype=np.int32)
STATS_MINUTES_IRM=np.asarray(STATS_HOURS_IRM)*60

def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)

def is_bissextile(years):
    if(years%4==0 and years%100!=0 or years%400==0):
        return True
    else:
        return False

class SPW_MI_flows():
    """
    Gestion des données pluviographiques du SPW-MI au travers de l'ancien site web "voies-hydrauliques.be"
    http://voies-hydrauliques.wallonie.be/opencms/opencms/fr/hydro/Archive/
    """

    def __init__(self) -> None:
        """Création de 2 dictionnaires de recherche sur base de la chaîne"""
        self.code2name={}
        self.name2code={}
        self.db_flows=None

        for mystations in STATIONS_MI_FLOW.splitlines():
            mycode,myname=mystations.split("\t")

            #Code pour les débits
            mycodeQ=mycode+'1002'
            self.code2name[mycodeQ]=myname
            self.name2code[myname.lower()]=mycodeQ

            #Code pour les hauteurs
            mycodeH=mycode+'1011'
            self.code2name[mycodeH]=myname
            self.name2code['h_'+myname.lower()]=mycodeH

    def get_names(self):
        """Nom des stations"""
        return list(self.name2code.keys())

    def get_namesQ(self):
        """Nom des stations de débit"""
        mylistN = self.get_names()
        mylistQ = self.get_codes()
        myQ=[]
        for curQ,curN in zip(mylistQ,mylistN):
            if mod(int(curQ),2)==0:
                myQ.append(curN)
        return myQ

    def get_namesH(self):
        """Nom des stations de hauteur"""
        mylistN = self.get_names()
        mylistQ = self.get_codes()
        myQ=[]
        for curQ,curN in zip(mylistQ,mylistN):
            if mod(int(curQ),2)!=0:
                myQ.append(curN)
        return myQ

    def get_codes(self):
        """Code des stations"""
        return list(self.code2name.keys())

    def get_codesQ(self):
        """Code des stations pour la variable Débit [m³/s]"""
        mylistQ = self.get_codes()
        myQ=[]
        for curQ in mylistQ:
            if mod(int(curQ),2)==0:
                myQ.append(curQ)
        return myQ

    def get_codesH(self):
        """Code des stations pour la variable Hauteur [m]"""
        mylistQ = self.get_codes()
        myQ=[]
        for curQ in mylistQ:
            if mod(int(curQ),2)!=0:
                myQ.append(curQ)
        return myQ

    def get_dailyflow_fromweb(self,year=2021,code='',name=''):
        """Récupération de données journalières"""
        station=code
        if name!="":
            station=self.name2code[name.lower()]

        #il faut chercher les mois
        name_month=12
        url="http://voies-hydrauliques.wallonie.be/opencms/opencms/fr/hydro/Archive/annuaires/statjourtab.do?code="+station+ "&annee="+str(year)

        res=requests.get(url)
        html_tables = pd.read_html(res.content, match='.+')

        try:
            if mod(int(station),2)==0:
                Tableau=html_tables[12].to_numpy()[0:31,1:name_month+1].astype('float')
            else:
                Tableau=html_tables[13].to_numpy()[0:31,1:name_month+1].astype('float')

            Tableau=Tableau.transpose().tolist()

            remove = []
            for j in range(12):
                if j==1:
                    i=28
                    if is_bissextile(year):
                        remove+=[[j,29]]
                        remove+=[[j,30]]
                        del Tableau[j][29]
                        del Tableau[j][29]
                    else:
                        remove+=[[j,28]]
                        remove+=[[j,29]]
                        remove+=[[j,30]]
                        for l in range(3):
                            del Tableau[j][28]
                else:
                    i=30
                    if j in [3,5,8,10]:
                        remove += [[j,30]]
                        del Tableau[j][30]
            data=[]
            for i in Tableau:
                data += i

            startdate = dt.date(year,1,1)
            enddate = startdate+pd.DateOffset(year=1)
            flow = pd.Series(data,index=pd.date_range(startdate,enddate,inclusive='left',freq='1D'))
            return flow
        except:
            pass

    def get_flow_fromweb(self,fromyear,toyear,code='',name='',filterna=True):
        """Récupération de plusieurs années"""
        flow=[]
        for curyear in range(fromyear,toyear+1):
            flow.append(self.get_yearflow_fromweb(curyear,code,name,filterna))

        try:
            return pd.concat(flow)
        except:
            return None

    def get_yearflow_fromweb(self,year=2021,code='',name='',filterna=True):
        """Récupération d'une année complète"""
        flow=[]
        for curmonth in range(1,13):
            flow.append(self.get_hourlyflow_fromweb(curmonth,year,code,name))

        try:
            flow = pd.concat(flow)

            if filterna:
                flow[flow.isna()]=0.

            return flow

        except:
            return None

    def get_hourlyflow_fromweb(self,month='',year='',code='',name='',mysleep=0.2):
        """récupération des données au pas horaire depuis le site SPW-MI VH
        http://voies-hydrauliques.wallonie.be/opencms/opencms/fr/hydro/Archive/"""

        station=code
        if name!="":
            station=self.name2code[name.lower()]

        nbdays = monthrange(year, month)[1]

        url="http://voies-hydrauliques.wallonie.be/opencms/opencms/fr/hydro/Archive/annuaires/stathorairetab.do?code="+station+"&mois="+str(month)+"&annee="+str(year)

        res=requests.get(url)
        html_tables = pd.read_html(res.content, match='.+')

        try:
            if mod(int(station),2)==0:
                flow = html_tables[12].to_numpy()[0:24,1:nbdays+1].astype('float').reshape(24*nbdays,order='F')
            else:
                flow = html_tables[13].to_numpy()[0:24,1:nbdays+1].astype('float').reshape(24*nbdays,order='F')

            startdate = dt.date(year,month,1)
            enddate = startdate+pd.DateOffset(months=1)
            flow = pd.Series(flow,index=pd.date_range(startdate,enddate,inclusive='left',freq='1H'))
            return flow
        except:
            pass

        time.sleep(mysleep)

    def plot_years(self,name,years=np.arange(2008,2022),fromcsv=False):
        """
        Graphique d'une ou de plusieurs années pour une station unique
        Si plusieurs années, elles sont superposées car l'axe des X est calé sur une année seulement
        """
        STATS_days_SPW=np.linspace(0,365,365)
        STATS_daysbis_SPW= np.linspace(0,366,366)

        STATS_hours_SPW=np.linspace(0,365*24,365*24)
        STATS_hoursbis_SPW= np.linspace(0,366*24,366*24)

        if fromcsv:
            myflows=self.fromcsv(stationame=name,fromdate=dt.datetime(years[0],1,1,1),todate=dt.datetime(years[-1]+1,1,1,0))

        fig,ax = plt.subplots(1,1,figsize=(10,8))

        for curyear in years:
            if fromcsv:
                myflow=myflows[dt.datetime(curyear,1,1,1):dt.datetime(curyear+1,1,1,0)]
            else:
                myflow=self.get_yearflow_fromweb(year=curyear,name=name)

            if len(myflow)==365:
                ax.plot(STATS_days_SPW,myflow,'.',label='Year:{:.0f}'.format(curyear))
            elif len(myflow)==366:
                ax.plot(STATS_daysbis_SPW,myflow,'.',label='Year:{:.0f}'.format(curyear))
            elif len(myflow)==365*24 :
                ax.plot(STATS_hours_SPW,myflow,'.',label='Year:{:.0f}'.format(curyear))
            elif len(myflow)==366*24 :
                ax.plot(STATS_hoursbis_SPW,myflow,'.',label='Year:{:.0f}'.format(curyear))
            elif len(myflow)==365*24-1:
                ax.plot(STATS_hours_SPW[:-1],myflow,'.',label='Year:{:.0f}'.format(curyear))
            elif len(myflow)==366*24-1:
                ax.plot(STATS_hoursbis_SPW[:-1],myflow,'.',label='Year:{:.0f}'.format(curyear))

        if len(myflow)<=366:
            ax.set_xticks(np.arange(0, 366, 31),['Jan','Feb','Mrch','April','May','June','July','August','Sep','Oct','Nov','Dec'])
        else:
            ax.set_xticks(np.arange(0, 366*24, 31*24),['Jan','Feb','Mrch','April','May','June','July','August','Sep','Oct','Nov','Dec'])

        ax.set_xlabel(_('Time (days)'))
        ax.set_ylabel(_('Flow  (m3/s) '))
        ax.set_title(name,loc='center')
        ax.legend().set_draggable(True)
        ax.grid()

        return fig,ax

    def plot_hydrolyears(self,name,years=np.arange(2008,2022),startmonth=10):
        """
        Graphique d'une ou de plusieurs années hydrologique pour une station unique
        Si plusieurs années, elles sont superposées car l'axe des X est calé sur une année seulement
        """
        from calendar import month_abbr,month_name

        STATS_hours_SPW=np.linspace(0,365*24,365*24)
        STATS_hoursbis_SPW= np.linspace(0,366*24,366*24)
        monthnames=[]
        for x in range(startmonth,13):
            monthnames.append(month_name[x])
        for x in range(1,startmonth):
            monthnames.append(month_name[x])

        if startmonth>1:
            myflows=self.fromcsv(stationame=name,fromdate=dt.datetime(years[0]-1,startmonth,1,1),todate=dt.datetime(years[-1],startmonth,1,0))
        else:
            myflows=self.fromcsv(stationame=name,fromdate=dt.datetime(years[0],1,1,1),todate=dt.datetime(years[-1]+1,1,1,0))

        fig,ax = plt.subplots(1,1,figsize=(10,8))

        for curyear in years:
            if startmonth>1:
                myflow=myflows[dt.datetime(curyear-1,startmonth,1,1):dt.datetime(curyear,startmonth,1,0)]
            else:
                myflow=myflows[dt.datetime(curyear,1,1,1):dt.datetime(curyear+1,1,1,0)]

            if len(myflow)==365*24 :
                ax.plot(STATS_hours_SPW,myflow,'.',label='Year:{:.0f}'.format(curyear))
            elif len(myflow)==366*24 :
                ax.plot(STATS_hoursbis_SPW,myflow,'.',label='Year:{:.0f}'.format(curyear))
            elif len(myflow)==365*24-1:
                ax.plot(STATS_hours_SPW[:-1],myflow,'.',label='Year:{:.0f}'.format(curyear))
            elif len(myflow)==366*24-1:
                ax.plot(STATS_hoursbis_SPW[:-1],myflow,'.',label='Year:{:.0f}'.format(curyear))

        ax.set_xticks(np.arange(0, 366*24, 31*24),monthnames)

        ax.set_xlabel(_('Time (days)'))
        ax.set_ylabel(_('Flow  (m3/s) '))
        ax.set_title(name,loc='center')
        ax.legend().set_draggable(True)
        ax.grid()

        return fig,ax

    def plot_hydrolyears_HQ(self,name,years=np.arange(2008,2022),startmonth=10):
        """
        Graphique HQ d'une ou de plusieurs années hydrologique pour une station unique
        Si plusieurs années, elles sont superposées car l'axe des X est calé sur une année seulement
        """
        from calendar import month_abbr,month_name

        if startmonth>1:
            myflowsq=self.fromcsv(stationame=name,fromdate=dt.datetime(years[0]-1,startmonth,1,1),todate=dt.datetime(years[-1],startmonth,1,0))
            myflowsh=self.fromcsv(stationame='h_'+name,fromdate=dt.datetime(years[0]-1,startmonth,1,1),todate=dt.datetime(years[-1],startmonth,1,0))
        else:
            myflowsq=self.fromcsv(stationame=name,fromdate=dt.datetime(years[0],1,1,1),todate=dt.datetime(years[-1]+1,startmonth,1,0))
            myflowsh=self.fromcsv(stationame='h_'+name,fromdate=dt.datetime(years[0],1,1,1),todate=dt.datetime(years[-1]+1,startmonth,1,0))

        fig,ax = plt.subplots(1,1,figsize=(10,8))

        for curyear in years:
            if startmonth>1:
                myflowq=myflowsq[dt.datetime(curyear-1,startmonth,1,1):dt.datetime(curyear,startmonth,1,0)]
                myflowh=myflowsh[dt.datetime(curyear-1,startmonth,1,1):dt.datetime(curyear,startmonth,1,0)]
            else:
                myflowq=myflowsq[dt.datetime(curyear,startmonth,1,1):dt.datetime(curyear+1,startmonth,1,0)]
                myflowh=myflowsh[dt.datetime(curyear,startmonth,1,1):dt.datetime(curyear+1,startmonth,1,0)]

            ax.plot(myflowh,myflowq,'.',label='Year:{:.0f}'.format(curyear))

        ax.set_xlabel(_('Water depth [m]'))
        ax.set_ylabel(_('Flow  [m3/s] '))
        ax.set_title(name,loc='center')
        ax.legend().set_draggable(True)
        ax.grid()

        return fig,ax

    def saveas(self,flow:pd.Series,filename:str):
        """Sauvegarde d'une series pandas dans un fichier .csv"""
        flow.to_csv(filename,header=['Data'])

    def fromcsv(self,stationame='',stationcode=0,filename:str='',fromdate:dt.datetime=None,todate:dt.datetime=None):
        """
        Lecture depuis un fichier csv créé depuis un import précédent
        Les fichiers doivent être disponibles depuis un sous-répertoire spw
        """
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
        """Lecture de plusieurs fichiers Excel en autant de séries de débit/hauteur
        Renvoi d'un dictionnaire avec les séries
        Le paramètre create_db permet de conserver un pointeur vers les séries complètes afin d'éviter à devoir relire les fichiers
        pour des traitements sur plusieurs stations ou répétitifs
        """

        from os import listdir

        if dir =='' and self.db_flows is None:
            return None

        def read_xls_rainSPW(dir,filename=''):
            """Lecture du fichier Excel"""
            if filename=='':
                return None

            myflow = pd.read_excel(join(dir,filename))
            myflow = myflow.dropna(how='all').dropna(how='all', axis=1)
            myflow.columns=myflow.iloc[0]
            myflow=myflow.iloc[1:]
            myflow=myflow.set_index('Date')

            #On supprimme les espaces multiples pour avoir une en-tête de colonne correcte
            newnames = [re.sub(' +',' ',curstat) for curstat in myflow.keys()]
            myflow.columns=newnames

            return myflow

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

        if self.db_flows is None:
            filenames=[]
            for file in listdir(dir):
                if file.endswith(".xlsx"):
                    filenames.append(file)

            myrains=pd.concat([read_xls_rainSPW(dir,filename) for filename in filenames],sort=True)
            myser =split_series(myrains)

            if create_db:
                self.db_flows = myser
        else:
            myser = self.db_flows

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

    def import_all(self,dirout,fromyear=2002,toyear=2021,fromstation=0):
        """
        Import de tout ce qui est possible depuis le site web http://voies-hydrauliques.wallonie.be/
        Si des données sont manquantes et/ou inaccessibles, la gestion d'erreur "Try/Except" ne doit normalement pas faire planter le code
        Le résultat est écrit dans des fichiers .csv dans le répertoire passé en argument
        Il est possible de restreindre le téléchargement entre deux années passées en argument
        Il est également possible de redémarrer le téléchargement depuis un index de station si l'opération s'est interrompue
        :param
        """
        dirout=normpath(dirout)
        mystations = list(self.code2name.keys())
        for curstation in mystations[fromstation:]:
            myflow = self.get_flow_fromweb(fromyear,toyear,curstation)
            if not myflow is None:
                self.saveas(myflow,join(dirout,curstation+'.csv'))
            print(curstation)

if __name__=="__main__":
    #exemple
    my = SPW_MI_flows()
    my.import_all(r'D:\Programmation2\wolf_oo\Sources\Python\PyPi\spw')
    myflow=my.get_yearflow_fromweb(name="Jalhay")
