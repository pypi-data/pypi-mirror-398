
"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import ctypes
myappid = 'wolf_hece_uliege' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from ..PyTranslate import _


import numpy as np
from math import *
import sys
import matplotlib.pyplot as plt

def INTERSEC(x1,y1,x2,y2,el):
    xx=1.0e10
    if 0.0<abs(y2-y1):
        a=(y2-y1)/(x2-x1)
        b=(x2*y1-x1*y2)/(x2-x1)
        xx=(el-b)/a
    return xx

data_sect="""-138 100
-114 90
-70 80
-45 70
-32 62
0 61.5
32 62
60 70
80 80
98 84
120 87"""

def Manning_Q(nManning,slope,data='',x:np.ndarray=None,y:np.ndarray=None):
    if data!='':
        x=[]
        y=[]
        for curline in data.splitlines():
            values=curline.split(' ')
            x.append(float(values[0]))
            y.append(float(values[1]))
        x=np.asarray(x)
        y=np.asarray(y)

    nn=len(x)

    ymin=min(y)
    ymax=max(y)
    dy=.1 #(ymax-ymin)/100
    yy=np.arange(ymin,ymax+dy,dy)

    nb=len(yy)
    q=np.zeros(nb)
    a=np.zeros(nb)
    s=np.zeros(nb)
    wsw=np.zeros(nb)
    r=np.zeros(nb)
    h=np.zeros(nb)

    k=0
    for k in range(nb):
        xxl=0.0
        xxr=0.0
        for i in range(0,nn-1):
            x1=x[i]
            y1=y[i]
            x2=x[i+1]
            y2=y[i+1]
            xx=INTERSEC(x1,y1,x2,y2,yy[k])
            dS=0.0
            dA=0.0
            if y1<yy[k] and y2<yy[k]:
                dS=sqrt((x2-x1)**2+(y2-y1)**2)
                dA=0.5*(2.0*yy[k]-y1-y2)*(x2-x1)
            if x1<=xx and xx<=x2:
                if y2<=yy[k] and yy[k]<=y1:
                    dS=sqrt((x2-xx)**2+(y2-yy[k])**2)
                    dA=0.5*(x2-xx)*(yy[k]-y2)
                    xxl=xx
                if y1<=yy[k] and yy[k]<=y2:
                    dS=sqrt((xx-x1)**2+(yy[k]-y1)**2)
                    dA=0.5*(xx-x1)*(yy[k]-y1)
                    xxr=xx
            s[k]+=dS
            a[k]+=dA
        if 0.0<s[k]:
            r[k]=a[k]/s[k]
            v=1.0/nManning*r[k]**(2/3)*sqrt(slope)
            q[k]=a[k]*v

        h[k]=yy[k]-ymin
        wsw[k]=xxr-xxl
        k+=1

    return q,yy

def plot_rel(q,el,n,i):
    qmin=0.0;qmax=10000.0;dq=1000
    emin=60.0;emax=90.0;de=2.0
    # Plot
    #fig=plt.figure()
    plt.plot(q,el,color='black',lw=1.0,label='PS (n='+str(n)+', i='+str(i)+')')
    plt.xlabel('Discharge (m$^3$/s)')
    plt.ylabel('Elevation (EL.m)')
    plt.xlim(qmin,qmax)
    plt.ylim(emin,emax)
    plt.xticks(np.arange(qmin,qmax+dq,dq))
    plt.yticks(np.arange(emin,emax+de,de))
    plt.grid()
    plt.legend(shadow=True,loc='upper left',handlelength=3)
    #plt.savefig(fnameF,dpi=200,, bbox_inches="tight", pad_inches=0.2)
    #plt.show()

def plot_sect(x,y,fwl):
    # plot
    xmin=-150
    xmax=150.0
    ymin=50.0
    ymax=100
    fig = plt.figure()
    ax=fig.add_subplot(111)
    ax.plot(x,y,color='black',lw=1.0,label='ground surface')
    ax.fill_between(x,y,fwl,where=y<=fwl,facecolor='cyan',alpha=0.3,interpolate=True)
    #ax.set_title(strt)
    ax.set_xlabel('Distance (m)')
    ax.set_ylabel('Elevation (EL.m)')
    ax.set_xlim(xmin,xmax)
    ax.set_ylim(ymin,ymax)
    aspect=1.0*(ymax-ymin)/(xmax-xmin)*(ax.get_xlim()[1] - ax.get_xlim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[0])
    ax.set_aspect(aspect)
    #plt.savefig(fnameF,dpi=200,, bbox_inches="tight", pad_inches=0.2)
    #plt.show()

def main():
    x=[]
    y=[]
    for curline in data_sect.splitlines():
        values=curline.split(' ')
        x.append(float(values[0]))
        y.append(float(values[1]))
    x=np.asarray(x)
    y=np.asarray(y)

    nManning=np.linspace(.02,.05,num=10)
    slope=.001

    fig=plt.figure()
    for n in nManning:
        q,yy=Manning_Q(n,slope,x=x,y=y)
        plot_rel(q,yy,n,slope)
    plot_sect(x,y,90)
    plt.show()
    a=1

if __name__=='__main__':
    main()