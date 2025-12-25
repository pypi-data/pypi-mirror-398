"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from datetime import datetime as dt # Gestion de dates et heures
from zoneinfo import ZoneInfo       # Gestion de fuseaux horaires

import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate as interp
import sys
import pandas as pd

try:
    from OpenGL.GL import *
except:
    msg=_('Error importing OpenGL library')
    msg+=_('   Python version : ' + sys.version)
    msg+=_('   Please check your version of opengl32.dll -- conflict may exist between different files present on your desktop')
    raise Exception(msg)


from .PyTranslate import _
from .PyVertex import circle,quad,cross,getRGBfromI,getIfromRGB
from .RatingCurveData import *
from .drawing_obj import Element_To_Draw

POLYNOMIAL_LAW=0
POWER_LAW=1

FMTDATEMI='%d-%m-%y'
FMTDATE='%d/%m/%Y %H:%M:%S'
FMTDATEG='%d-%m-%y%H:%M'
FMTDATEG2='%d-%m-%Y %H:%M'
FMTDATE2='%d/%m/%Y'

class href_gaugingstation():
    id:int
    name:str
    basin:str
    hDNG:float

    def __init__(self,id:int,name:str,basin:str,hDNG) -> None:

        self.id=id
        self.name=name
        self.basin=basin

        if hDNG=='inconnu':
            self.hDNG=-99999
        else:
            self.hDNG=float(hDNG)
        pass

class href_gaugingstations():
    myhrefs:list

    def __init__(self,fromxls:str='') -> None:

        self.myhrefs=[]
        lines=fromxls.splitlines()
        for curline in lines:
            locval=curline.replace(' ','').split('\t')
            if len(locval)>1:
                curhref=href_gaugingstation(int(locval[0]),locval[1],locval[2],locval[3])
                self.myhrefs.append(curhref)
        pass

class gauging():
    id:int
    name:str
    basin:str
    Q:float
    H:float
    date:dt

    def __init__(self,id:int,name:str,basin:str,Q:float,H:float,date:dt) -> None:
        self.name=name
        self.basin=basin
        self.id=id
        self.Q=Q
        self.H=H
        self.date=date

        pass

class gaugings():
    mygaugings:list

    def __init__(self,fromxls:str='') -> None:

        self.mygaugings=[]
        lines=fromxls.splitlines()
        for curline in lines:
            locval=curline.replace(' ','').split('\t')
            if len(locval)>1:
                curgauging=gauging(int(locval[0]),locval[1],locval[2],float(locval[3]),float(locval[4]),dt.strptime(locval[5],FMTDATEG))
                self.mygaugings.append(curgauging)
        pass

class coeffratingcurve():
    hmin:float
    hmax:float
    coeffs:np.array
    law:int
    myfunc:interp.PPoly

    def __init__(self,hmin,hmax,law,coeffs:np.ndarray) -> None:
        self.hmin=hmin
        self.hmax=hmax
        self.law=law
        self.coeffs=coeffs

        self.myfunc=interp.PPoly(self.coeffs.reshape((len(self.coeffs),1)),[0,self.hmax],extrapolate=True)

        pass

class ratingcurve():

    startdate:dt
    enddate:dt
    nb:int
    mycoeffs:list[coeffratingcurve]
    myfunc:interp.PPoly

    def __init__(self,start:dt=None,end:dt=None,law:int=POLYNOMIAL_LAW,hmin:np.ndarray=None,hmax:np.ndarray=None,coeffs:np.ndarray=None,fromxls:str='',*args, **kw):

        if not start is None:
            self.startdate=start
        if not end is None:
            self.enddate=end

        self.mycoeffs=[]

        if fromxls!='':
            lines=fromxls.splitlines()

            self.nb=len(lines)
            for curline in lines:
                locval=curline.replace(' ','').split('\t')
                if len(locval)>1:
                    curcoeff=coeffratingcurve(float(locval[0]),float(locval[1]),law,np.asarray(locval[2:],dtype=np.float32))
                    self.mycoeffs.append(curcoeff)
        else:
            self.nb=len(hmin)

            for i in range(len(self.nb)):
                curcoeff=coeffratingcurve(hmin[i],hmax[i],law,coeffs[i,:])
                self.mycoeffs.append(curcoeff)

        super().__init__(*args, **kw)

    def plot(self, factextra=1.,ax=None,lw=1):

        if ax is None:
            fig,ax=plt.subplots(1,1)

        x=[]
        y=[]
        for curpart in self.mycoeffs:
            xmin=curpart.hmin
            xmax=curpart.hmax
            xloc=np.linspace(xmin,xmax,num=50)
            x.append(xloc)
            y.append(curpart.myfunc(xloc))

        #extrapolation
        if factextra>1.:
            xmin=curpart.hmax
            xmax=curpart.hmax * factextra
            xloc=np.linspace(xmin,xmax,num=50)
            x.append(xloc)
            y.append(curpart.myfunc(xloc))

        ax.plot(np.asarray(x).flatten(),np.asarray(y).flatten(),label=self.startdate.strftime(FMTDATE2) +' - '+self.enddate.strftime(FMTDATE2),linewidth=lw)

        extra=4
        for curpart in self.mycoeffs:
            xp=curpart.hmin
            yp=curpart.myfunc(xp)
            ax.plot([xp,xp],[min(yp-extra,yp*.8),max(yp+extra,yp*1.2)],'k-.', linewidth=1)

        xp=curpart.hmax
        yp=curpart.myfunc(xp)
        ax.plot([xp,xp],[min(yp-extra,yp*.8),max(yp+extra,yp*1.2)],'k-.', linewidth=1)

    def _compute_q(self, h):
        found = False
        for cupart in self.mycoeffs:
            if h >= cupart.hmin and h<cupart.hmax:
                found=True
                break

        if not found:
            if h > cupart.hmax:
                found=True

        if found:
            return cupart.myfunc(h)
        else:
            return np.nan

    def compute_q(self, h:pd.Series):

        q = h.copy()
        for idx, curh in enumerate(h):
            q.iloc[idx] = self._compute_q(curh)

        return q

class gaugingstation():
    id:int

    name:str
    name2:str

    river:str
    river2:str

    mycurves:list[ratingcurve]
    mygaugings:list
    myhref:list

    maintainer:str
    startdate:dt
    x:float
    y:float

    weblink:str

    def __init__(self,name:str,id:int,river:str,ratingcurves:list=None,*args, **kw) -> None:

        self.name=name
        self.river=river
        self.id=id
        self.x=0.
        self.y=0.
        self.maintainer=''
        self.startdate=dt(1900,1,1)
        self.weblink=''

        if not ratingcurves is None:
            self.mycurves=ratingcurves

        super().__init__(*args, **kw)
        pass

    def gettype(self)->int:

        if self.maintainer=='SPW/DO223':
            try:
                curid=int(self.id)
                rest=int(curid-int(curid/100)*100)
                if rest==2 or rest==92:
                    #Débit
                    return 1
                if rest==92:
                    #Débit calculé
                    return -1
                elif rest==15:
                    #Pluie
                    return 2
                elif rest==11 or rest==41:
                    #Hauteur d'eau
                    return 3
                else:
                    return 1
            except:
                return 1
        else:
            return 1

    def plot(self,size:float=10.):

        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
        glPointSize(1)

        try:
            curtype=abs(self.gettype())
            if curtype==1:
                #rgb=getRGBfromI(0)
                #glColor3ub(int(rgb[0]),int(rgb[1]),int(rgb[2]))
                glColor3ub(0,0,255)
                quad(self.x,self.y,size/2)
            if curtype==2:
                #rgb=getRGBfromI(0)
                #glColor3ub(int(rgb[0]),int(rgb[1]),int(rgb[2]))
                glColor3ub(255,0,0)
                circle(self.x,self.y,size/2)
            if curtype==3:
                #rgb=getRGBfromI(0)
                #glColor3ub(int(rgb[0]),int(rgb[1]),int(rgb[2]))
                glColor3ub(0,255,0)
                cross(self.x,self.y,size/2)
        except:
            pass

        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)

    def plotRT(self,ax=None,lw=1):
        if ax is None:
            fig,ax=plt.subplots(1,1)
            ax.set_xlabel('Water depth [m]')
            ax.set_ylabel('Discharge [m³/s]')
            ax.set_title('Rating curves - ' + self.name +' - '+ self.river +' - '+str(self.id))

        for curcurve in self.mycurves:
            curcurve.plot(1.1,ax,lw)

        x=list(myg.H for myg in self.mygaugings)
        y=list(myg.Q for myg in self.mygaugings)

        ax.scatter(x,y,marker='+',)
        ax.legend()

class SPWhrefs(href_gaugingstations):

    def __init__(self, fromxls: str='') -> None:
        data="""62281002	Chaudfontaine	Vesdre	77.626
                63021002	Pepinster	Vesdre	inconnu
                65011002	Pepinster	Hoegne	inconnu
                65171002	Polleur	Hoegne	213.814
                65261002	Belleheid	Hoegne	357.317
                64041002	Eupen	Vesdre	inconnu
                5860	Theux	Hoëgne	157.2
                6970	Spixhe	Wayai	137.78
                7150	Verviers	Vesdre	150.01
                7600	Forêt	Magne	94.49
                """
        super().__init__(data)

class SPWGaugings(gaugings):

    def __init__(self, fromxls: str='') -> None:
        data="""62281002	Chaudfontaine	Vesdre	150.634	3.022	14-07-21 07:37
                62281002	Chaudfontaine	Vesdre	144.188	2.787	25-02-02 14:00
                62281002	Chaudfontaine	Vesdre	131.615	2.728	16-03-19 10:24
                62281002	Chaudfontaine	Vesdre	131.158	2.688	20-02-99 11:20
                62281002	Chaudfontaine	Vesdre	125.690	2.730	23-11-84 09:45
                62281002	Chaudfontaine	Vesdre	112.634	2.385	01-06-18 16:44
                62281002	Chaudfontaine	Vesdre	106.265	2.519	14-01-11 12:28
                62281002	Chaudfontaine	Vesdre	101.734	2.330	29-05-84 09:20
                63021002	Pepinster	Vesdre	104.808	2.062	16-03-19 11:05
                63021002	Pepinster	Vesdre	89.022	1.860	01-06-18 15:56
                63021002	Pepinster	Vesdre	59.851	1.395	17-03-19 09:40
                63021002	Pepinster	Vesdre	47.665	1.350	04-06-16 11:12
                63021002	Pepinster	Vesdre	44.025	1.158	18-03-19 09:30
                63021002	Pepinster	Vesdre	36.430	1.022	22-12-17 10:20
                63021002	Pepinster	Vesdre	33.210	0.931	03-02-21 14:30
                63021002	Pepinster	Vesdre	29.490	0.874	20-01-21 08:30
                65011002	Pepinster	Hoegne	64.140	1.298	01-06-18 11:40
                65011002	Pepinster	Hoegne	39.653	0.834	16-03-19 11:39
                65171002	Polleur	Hoegne	12.747	1.388	30-01-21 15:17
                65171002	Polleur	Hoegne	9.110	1.275	14-01-19 12:51
                65171002	Polleur	Hoegne	9.003	1.189	03-06-16 09:50
                65261002	Belleheid	Hoegne	11.759	1.049	20-02-99 08:00
                65261002	Belleheid	Hoegne	10.256	1.008	20-02-02 12:37
                65261002	Belleheid	Hoegne	9.197	0.974	10-12-07 16:05
                65261002	Belleheid	Hoegne	7.040	0.906	21-01-02 12:40
                64041002	Eupen	Vesdre	30.932	1.628	30-01-21 10:20
                64041002	Eupen	Vesdre	7.195	1.179	24-02-16 13:40
                5860	Theux	Hoëgne	170.7	3.75	14-07-20 12:30
                6970	Spixhe	Wayai	92.3	3.1	14-07-21 10:00
                7150	Verviers	Vesdre	115.2	1.9	14-07-21 14:00
                7600	Forêt	Magne	2.1	0.72	10-07-21 09:00
                """
        super().__init__(data)

class SPWMIGaugingStations(Element_To_Draw):

    mystations:dict[int:gaugingstation]
    myrivers:dict
    gaugings:SPWGaugings
    hrefs:SPWhrefs

    def __init__(self, fromxls:str='', idx:str = '', plotted:bool = True, mapviewer = None, need_for_wx:bool = False) -> None:

        super().__init__(idx,plotted,mapviewer,need_for_wx)

        self.gaugings=SPWGaugings()
        self.hrefs=SPWhrefs()

        self.mystations={}
        self.myrivers={}

        existingstation=[]

        mydata=DataGaugingCurves.splitlines()

        k=0
        nbmax=len(mydata)
        idold=0
        while k<nbmax:
            curline=mydata[k]
            if curline!='':

                curvals=curline.split('\t')
                curid=int(curvals[0])

                if not curid in existingstation:
                    if idold>0:
                        curstation=gaugingstation(nameold,idold,basinold,curcurves)
                        self.mystations[idold]=curstation
                    #La station n'existe pas --> on la crée
                    existingstation.append(curid)
                    curcurves=[]
                    idold=curid
                    nameold=curvals[1]
                    basinold=curvals[2]

                spwMI=len(curvals)==13
                startdate=curvals[3]
                if spwMI:
                    enddate=curvals[5]
                else:
                    enddate=curvals[4]

                l=k+1
                nextvals=curvals
                if spwMI:
                    while int(nextvals[0])==curid and nextvals[3]==startdate and nextvals[5]==enddate and l<nbmax-1:
                        l+=1
                        nextvals=mydata[l].split('\t')
                else:
                    while int(nextvals[0])==curid and nextvals[3]==startdate and nextvals[4]==enddate and l<nbmax-1:
                        l+=1
                        nextvals=mydata[l].split('\t')

                if spwMI:
                    #modèle SPW-MI
                    startdate=dt.strptime(curvals[3]+' '+curvals[4]+':00',FMTDATEG2)
                    enddate=dt.strptime(curvals[5]+' '+curvals[6]+':00',FMTDATEG2)
                else:
                    #modèle SPW-DCENN - le format de date change
                    startdate=dt.strptime(curvals[3],FMTDATEG2)
                    enddate=dt.strptime(curvals[4],FMTDATEG2)

                locdata=''
                for m in range(k,l):
                    curvals=mydata[m].split('\t')
                    if spwMI:
                        #modèle SPW-MI
                        locdata+=curvals[7]+'\t'+curvals[8]+'\t'+curvals[9]+'\t'+curvals[10]+'\t'+curvals[11]+'\t'+curvals[12]+'\n'
                    else:
                        #modèle SPW-DCENN - le format de date change
                        locdata+=curvals[5]+'\t'+curvals[6]+'\t'+curvals[7]+'\t'+curvals[8]+'\t'+curvals[9]+'\t'+curvals[10]+'\n'

                curcurve=ratingcurve(startdate,enddate,POLYNOMIAL_LAW,fromxls=locdata)
                curcurves.append(curcurve)

                k=l
            else:
                k+=1

        curstation=gaugingstation(nameold,idold,basinold,curcurves)
        self.mystations[idold]=curstation

        curstat:gaugingstation
        mydata=DataStationsSPWMI.splitlines()
        for curline in mydata:
            if curline!='':
                curvals=curline.split('\t')
                #index=curvals[0]
                maint=curvals[1].replace("'","")
                id=int(curvals[2])
                name2=curvals[3].replace("'","")
                river2=curvals[4].replace("'","")
                startdate=dt.strptime(curvals[5]+'/'+curvals[6]+'/'+curvals[7],'%d/%m/%Y')
                x=float(curvals[8])
                y=float(curvals[9])

                if id in self.mystations.keys():
                    curstat=self.mystations[id]
                else:
                    curstat=gaugingstation(name2,id,river2,curcurves)
                    self.mystations[id]=curstat

                if not river2 in self.myrivers.keys():
                    self.myrivers[river2]={}
                self.myrivers[river2][name2]=curstat

                curstat.x=x
                curstat.y=y
                curstat.maintainer=maint
                curstat.startdate=startdate
                curstat.name2=name2
                curstat.river2=river2

        for curid in self.mystations:
            curstat=self.mystations[curid]
            curstat.mygaugings = list(filter(lambda x: x.id==curid,self.gaugings.mygaugings))
            curstat.myhref = list(filter(lambda x: x.id==curid,self.hrefs.myhrefs))

        pass

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size:float=10.):
        self._plot(size)

    def find_minmax(self,update=False):
        x = [cur.x for cur in self.mystations.values()]
        y = [cur.y for cur in self.mystations.values()]

        self.xmin = min(x)
        self.xmax = max(x)
        self.ymin = min(y)
        self.ymax = max(y)

    def _plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size:float=10.):
        for curstation in self.mystations.values():
            curstation.plot(size)

class SPWDCENNGaugingStations(Element_To_Draw):

    mystations:dict[int:gaugingstation]
    myrivers:dict
    gaugings:SPWGaugings
    hrefs:SPWhrefs

    def __init__(self, fromxls:str='', idx:str = '', plotted:bool = True, mapviewer = None, need_for_wx:bool = False) -> None:

        super().__init__(idx,plotted,mapviewer,need_for_wx)

        self.gaugings=SPWGaugings()
        self.hrefs=SPWhrefs()

        self.mystations={}
        self.myrivers={}

        existingstation=[]

        mydata=DataGaugingCurves.splitlines()

        k=0
        nbmax=len(mydata)
        idold=0
        while k<nbmax:
            curline=mydata[k]
            if curline!='':

                curvals=curline.split('\t')
                curid=int(curvals[0])

                if not curid in existingstation:
                    if idold>0:
                        curstation=gaugingstation(nameold,idold,basinold,curcurves)
                        self.mystations[idold]=curstation
                    #La station n'existe pas --> on la crée
                    existingstation.append(curid)
                    curcurves=[]
                    idold=curid
                    nameold=curvals[1]
                    basinold=curvals[2]

                spwMI=len(curvals)==13
                startdate=curvals[3]
                if spwMI:
                    enddate=curvals[5]
                else:
                    enddate=curvals[4]

                l=k+1
                nextvals=curvals
                if spwMI:
                    while int(nextvals[0])==curid and nextvals[3]==startdate and nextvals[5]==enddate and l<nbmax-1:
                        l+=1
                        nextvals=mydata[l].split('\t')
                else:
                    while int(nextvals[0])==curid and nextvals[3]==startdate and nextvals[4]==enddate and l<nbmax-1:
                        l+=1
                        nextvals=mydata[l].split('\t')

                if spwMI:
                    #modèle SPW-MI
                    startdate=dt.strptime(curvals[3]+' '+curvals[4]+':00',FMTDATEG2)
                    enddate=dt.strptime(curvals[5]+' '+curvals[6]+':00',FMTDATEG2)
                else:
                    #modèle SPW-DCENN - le format de date change
                    startdate=dt.strptime(curvals[3],FMTDATEG2)
                    enddate=dt.strptime(curvals[4],FMTDATEG2)

                locdata=''
                for m in range(k,l):
                    curvals=mydata[m].split('\t')
                    if spwMI:
                        #modèle SPW-MI
                        locdata+=curvals[7]+'\t'+curvals[8]+'\t'+curvals[9]+'\t'+curvals[10]+'\t'+curvals[11]+'\t'+curvals[12]+'\n'
                    else:
                        #modèle SPW-DCENN - le format de date change
                        locdata+=curvals[5]+'\t'+curvals[6]+'\t'+curvals[7]+'\t'+curvals[8]+'\t'+curvals[9]+'\t'+curvals[10]+'\n'

                curcurve=ratingcurve(startdate,enddate,POLYNOMIAL_LAW,fromxls=locdata)
                curcurves.append(curcurve)

                k=l
            else:
                k+=1

        curstation=gaugingstation(nameold,idold,basinold,curcurves)
        self.mystations[idold]=curstation

        curstat:gaugingstation
        mydata=DataStationsDCENN.splitlines()
        for curline in mydata:
            if curline!='':
                curvals=curline.split('\t')
                maint=curvals[3].replace("'","")
                id=int(curvals[0])
                name2=curvals[1].replace("'","")
                river2=curvals[2].replace("'","")
                startdate=dt.strptime(curvals[4],'%Y%m%d%H%M%S')
                x=float(curvals[5])
                y=float(curvals[6])
                fiche=curvals[7]

                if id in self.mystations.keys():
                    curstat=self.mystations[id]
                else:
                    curstat=gaugingstation(name2,id,river2,curcurves)
                    self.mystations[id]=curstat

                if not river2 in self.myrivers.keys():
                    self.myrivers[river2]={}
                self.myrivers[river2][name2]=curstat

                curstat.x=x
                curstat.y=y
                curstat.maintainer=maint
                curstat.startdate=startdate
                curstat.name2=name2
                curstat.river2=river2
                curstat.weblink=fiche

        for curid in self.mystations:
            curstat=self.mystations[curid]
            curstat.mygaugings = list(filter(lambda x: x.id==id,self.gaugings.mygaugings))
            curstat.myhref = list(filter(lambda x: x.id==id,self.hrefs.myhrefs))

        pass

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size:float=10.):
        self._plot(size)

    def find_minmax(self,update=False):
        x = [cur.x for cur in self.mystations.values()]
        y = [cur.y for cur in self.mystations.values()]

        self.xmin = min(x)
        self.xmax = max(x)
        self.ymin = min(y)
        self.ymax = max(y)

    def _plot(self, size:float=10.):
        for curstation in self.mystations.values():
            curstation.plot(size)
