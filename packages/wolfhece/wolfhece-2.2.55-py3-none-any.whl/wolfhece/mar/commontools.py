  #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Dec  5 09:03:34 2022

@author: jbrajkovic
"""

import numpy as np
import matplotlib.pyplot as plt
import commontools as ct
import xarray as xr
import matplotlib as mpl
import pandas as pd
import glob as glob
import matplotlib.cm as cm
#import fiona
#import geopandas as gpd
import rasterio
from PIL import Image
import pyproj
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import matplotlib.colors
import h5py
from pyproj import Proj, transform
import matplotlib.patheffects as pe
import os
import csv
def openfile(fileloc,col):
    f=open(fileloc,mode='r')
    V=[]
    for line in f:
            lines=line.strip()
            columns=lines.split()
            V=np.append(V,float(columns[col]))
    return(V)

def openfileh(fileloc,col):
    f=open(fileloc,mode='r')
    V=[]
    r=0
    for line in f:
        if r>0:
            lines=line.strip()
            columns=lines.split()
            V=np.append(V,float(columns[col]))
        r=r+1
    return(V)

def isbis(year):
    if((year%4==0 and year%100!=0)or(year%4==0 and year%400==0 and year%100==0)):
        t=1
    else:
        t=0
    return(t)

def seasonalmeans(fileloc,col,start_year,end_year,mod,season):
    years=openfile(fileloc,0)
    var=openfile(fileloc,col)
    T=[]
    # T=np.zeros(end_year-start_year+1)


    for y in range(start_year,end_year+1):
        beg_summer=np.array([173,173,170]);end_summer=np.array([264,264,259])
        beg_falls=end_summer+1;end_falls=np.array([355,355,359])
        beg_winter=end_falls+1;end_winter=np.array([80,80,69])
        beg_spring=end_winter+1;end_spring=beg_summer-1
        end_year=np.array([365,365,360])

        if(isbis(y)==1 and mod==0):
            beg_summer=beg_summer+1;end_summer=end_summer+1
            beg_falls=beg_falls+1;end_falls=end_falls+1
            beg_winter=beg_winter+1;end_winter=end_winter+1
            beg_spring=beg_spring+1;end_spring=beg_summer-1
            end_year=end_year+1
        # ind=y-start_year
        if season=="Summer":
            MASK=years==y
            T=np.append(T,np.mean(var[MASK][beg_summer[mod]-1:end_summer[mod]-1]))
            # T[ind]=np.mean(var[MASK][beg_summer[mod]-1:end_summer[mod]-1])
        elif season=="Falls":
            MASK=years==y
            T=np.append(T,np.mean(var[MASK][beg_falls[mod]-1:end_falls[mod]-1]))
            # T[ind]=np.mean(var[MASK][beg_falls[mod]-1:end_falls[mod]-1])
        elif season=="Winter":
            MASK1=years==y;MASK2=years==y+1
            V1=var[MASK1][beg_winter[mod]-1:end_year[mod]-1];V2=var[MASK2][0:end_winter[mod]-1]
            V=np.append(V1,V2)
            T=np.append(T,np.mean(V))
            # T[ind]=np.mean(V)
        elif season=="Spring":
            MASK=years==y
            T=np.append(T,np.mean(var[MASK][beg_spring[mod]-1:end_spring[mod]-1]))
            # T[ind]=np.mean(var[MASK][beg_spring[mod]-1:end_spring[mod]-1])
        elif season=="year":
            MASK=years==y
            T=np.append(T,np.mean(var[MASK][0:end_year[mod]-1]))
            # T[ind]=np.mean(var[MASK][0:end_year[mod]-1])
    return(T)


def seasonalsums(fileloc,col,start_year,end_year,mod,season):
    years=openfile(fileloc,0)
    var=openfile(fileloc,col)
    T=[]
    # T=np.zeros(end_year-start_year+1)


    for y in range(start_year,end_year+1):
        beg_summer=np.array([173,173,170]);end_summer=np.array([264,264,259])
        beg_falls=end_summer+1;end_falls=np.array([355,355,359])
        beg_winter=end_falls+1;end_winter=np.array([80,80,69])
        beg_spring=end_winter+1;end_spring=beg_summer-1
        end_year=np.array([365,365,360])

        if(isbis(y)==1 and mod==0):
            beg_summer=beg_summer+1;end_summer=end_summer+1
            beg_falls=beg_falls+1;end_falls=end_falls+1
            beg_winter=beg_winter+1;end_winter=end_winter+1
            beg_spring=beg_spring+1;end_spring=beg_summer-1
            end_year=end_year+1
        # ind=y-start_year
        if season=="Summer":
            MASK=years==y
            T=np.append(T,np.sum(var[MASK][beg_summer[mod]-1:end_summer[mod]-1]))
            # T[ind]=np.mean(var[MASK][beg_summer[mod]-1:end_summer[mod]-1])
        elif season=="Falls":
            MASK=years==y
            T=np.append(T,np.sum(var[MASK][beg_falls[mod]-1:end_falls[mod]-1]))
            # T[ind]=np.mean(var[MASK][beg_falls[mod]-1:end_falls[mod]-1])
        elif season=="Winter":
            MASK1=years==y;MASK2=years==y+1
            V1=var[MASK1][beg_winter[mod]-1:end_year[mod]-1];V2=var[MASK2][0:end_winter[mod]-1]
            V=np.append(V1,V2)
            T=np.append(T,np.sum(V))
            # T[ind]=np.mean(V)
        elif season=="Spring":
            MASK=years==y
            T=np.append(T,np.sum(var[MASK][beg_spring[mod]-1:end_spring[mod]-1]))
            # T[ind]=np.mean(var[MASK][beg_spring[mod]-1:end_spring[mod]-1])
        elif season=="year":
            MASK=years==y
            T=np.append(T,np.sum(var[MASK][0:end_year[mod]-1]))
            # T[ind]=np.mean(var[MASK][0:end_year[mod]-1])
    return(T)

def text_into_matrix(model_name,scenario,mx,my,sy,ey):
    """
    This function reads precipitation
    text files to put all of it in a
    3D matrix of yearly precipitation
    """
    directory='/srv7_tmp1/jbrajkovic/These/TS_ppp2/'

    mat_ret=np.zeros([mx,my,1])
    if scenario=='ssp585':
        y1=1980;y2=2100
    else:
        y1=2015;y2=2100
    isuiv=1
    isuiv2=0
    for i in range(1,mx*my+1):
        fn=directory+'Pr'+str(i)+model_name+'_'+scenario+'_'+str(y1)+'-'+str(y2)+'.txt'
        if os.path.exists(fn)==False:
            isuiv+=1
            # print('File doesn\'t exist',fn)
            continue
        else:
            isuiv2+=1

            if isuiv<=my:
                    ii=0;jj=isuiv
            else:
                    jj=int(isuiv%my)-1
                    ii=int((isuiv-jj)/my)

            if jj==0:j=my-1;ii=ii-1
            else:jj=jj-1
            if isuiv2==1:
                with open (fn, 'r') as f:
                    yys = [float(row[0]) for row in csv.reader(f,delimiter='\t')]
                with open (fn, 'r') as f:
                    pr= [float(row[2]) for row in csv.reader(f,delimiter='\t')]
            else:
                with open (fn, 'r') as f:
                    pr= [float(row[0]) for row in csv.reader(f,delimiter='\t')]

            if isuiv2==1:
                mat_ret=np.zeros([mx,my,ey-sy+1])*float('nan')
            for yy in range(sy,ey+1):
                msk=np.array(yys)==float(yy)
                # print(yys)
                mat_ret[ii,jj,yy-sy]=np.sum(np.array(pr)[msk])
            if isuiv2%200==0:print(isuiv2, mat_ret[ii,jj,0])
            isuiv+=1
    return(mat_ret)







def slidingmeans(TS,interval,std_or_mean=1):
    int2=int((interval-1)/2)
    s=np.size(TS)
    newTS=np.zeros(s)
    for i in range(0,s):
        if i<int2:
            if std_or_mean: newTS[i]=np.mean(TS[0:i+int2])
            else:newTS[i]=np.std(TS[0:i+int2])
        elif i>(s-int2-1):
            if std_or_mean: newTS[i]=np.mean(TS[i-int2:s-1])
            else:newTS[i]=np.std(TS[i-int2:s-1])
        else:
            if std_or_mean:newTS[i]=np.mean(TS[i-int2:i+int2])
            else:newTS[i]=np.std(TS[i-int2:i+int2])
    return(newTS)


def RGPD(vec,shape,scale,pu,teta,th):
    # print(th)
    r=th+(scale/shape)*((vec*pu*teta)**shape-1)
    return (r)

def GPD_frequency(valu,shape,scale,pu,teta,th,events_per_year):
    ret_p=((round((1+shape*((valu-th)/scale)),2)**(round((1/shape),2)))/(teta*pu*events_per_year))
    # if(pd.isna(ret_p)):print(round((1+shape*((valu-th)/scale)),2),shape,(round((1/shape),2)),)
    return(ret_p)

def RGPDI_values(vec,shape,scale,th):

    vals=((((1-vec)**(-shape))-1)*scale)/shape+th
    return (vals)

def RGPD_values(vec,shape,scale):
    vals=1-(1+shape*vec/scale)**(-1/shape)
    return (vals)


def CIGPD(vec,shape,scale,pu,teta,th,varsc,varsh,cov):
    T1=(((vec*pu*teta)**shape-1)/shape)**2*varsc
    T2=((scale*(-(vec*teta*pu)**shape+shape*(vec*teta*pu)**shape*np.log(vec*teta*pu)+1)/shape**2))**2*varsh
    T3=2*(((vec*pu*teta)**shape-1)/shape)*\
        ((scale*(-(vec*teta*pu)**shape+shape*(vec*teta*pu)**shape*np.log(vec*teta*pu)+1)/shape**2))*cov
    CI=np.sqrt(T1+T2+T3)*1.645
    return(CI)



def JJ2date(day,year):
    end_month=[31,28,31,30,31,30,31,31,30,31,30,31]
    end_monthcum=np.zeros(12);end_monthcum[0]=end_month[0]
    monthlab=np.arange(1,13,1)
    jj=0;m=0
    if ct.isbis(year):end_month[1]=29
    else:end_month=[31,28,31,30,31,30,31,31,30,31,30,31]

    for i in range(1,12):
        end_monthcum[i]=end_monthcum[i-1]+end_month[i]

    for i in range(0,12):
        if i > 0:
            if (day<=end_monthcum[i] and day>end_monthcum[i-1]):
                m=monthlab[i]
                jj=day-end_monthcum[i-1]
        else:
            if (day<=end_monthcum[i] and day>0):
                m=monthlab[i]
                jj=day
    # jj+=1
    date=np.array([jj,m,year]);date.astype(int)
    return(date)

def date2JJ(day,month,year,fn1='__',type_mod=2):
    end_month=[31,28,31,30,31,30,31,31,30,31,30,31]
    end_monthcum=np.zeros(12);
    if type_mod==1:
        if (ct.isbis(year)==1):end_month[1]=29


    for i in range(1,12):
        end_monthcum[i]=end_monthcum[i-1]+end_month[i]

    jj=int(end_monthcum[int(month-1)])+day
    # print(day,month,year,jj)
    return(jj)

def makebounds(mat,step):
    mat1=np.array(mat)
    mask1=pd.isna(mat1)==False
    maxi=np.max(mat1[mask1])
    # print(maxi)
    print(maxi,step)
    bounds=np.arange(0,maxi+step,step)
    return(bounds)

def map_belgium(ax,lons,lats):
    from mpl_toolkits.basemap import Basemap

    lat_0=50.6;lon_0=4.73
    m = Basemap(width=55000,height=50000,
                rsphere=(649328.00,665262.0),\
                area_thresh=1000.,projection='lcc',\
                lat_1=49.83,lat_2=51.17,lat_0=lat_0,lon_0=lon_0,resolution='i')
    m.drawcountries()
    m.drawcoastlines()
    return(m)

def map_belgium_J21(ax,lons,lats):
    from mpl_toolkits.basemap import Basemap
    lat_0=50.15;lon_0=5.83
    m = Basemap(width=15000,height=18000,
                rsphere=(649328.00,665262.0),\
                area_thresh=1000.,projection='lcc',\
                lat_1=49.83,lat_2=51.17,lat_0=lat_0,lon_0=lon_0,resolution='i')
    m.drawcountries(linewidth=3)
    m.drawcoastlines(linewidth=4)
    return(m)


def map_Vesdre(ax,lons,lats):
    from mpl_toolkits.basemap import Basemap
    lat_0=50.55;lon_0=5.93
    m = Basemap(width=6000,height=3800,
                rsphere=(649328.00,665262.0),\
                area_thresh=1000.,projection='lcc',\
                lat_1=49.83,lat_2=51.17,lat_0=lat_0,lon_0=lon_0,resolution='i')
    m.drawcountries()
    m.drawcoastlines()
    return(m)





def map_belgium_zoom(ax,lons,lats):
    from mpl_toolkits.basemap import Basemap
    lat_0=50.6;lon_0=4.73

    m = Basemap(width=34000,height=30000,
                rsphere=(649328.00,665262.0),\
                area_thresh=1000.,projection='lcc',\
                lat_1=49.83,lat_2=51.17,lat_0=lat_0,
                lon_0=lon_0,resolution='h')
    m.drawcountries(linewidth=1)
    m.drawcoastlines()
    # m.drawrivers()
    # m.drawmapboundary(fill_color='dodgerblue')
    # m.fillcontinents(color='gainsboro',lake_color='aqua')
    # m.bluemarble()
    return(m)

def map_Europe(ax,lons,lats):
    from mpl_toolkits.basemap import Basemap

    print(np.mean(lats))
    m = Basemap(width=6000,height=150000,
                rsphere=(649328.00,665262.0),\
                area_thresh=1000.,projection='lcc',\
                lat_1=35,lat_2=65,lat_0=52.,lon_0=10.,resolution='i')
    m.drawcountries()
    m.drawcoastlines()
    # m.drawrivers()
    # m.drawmapboundary(fill_color='dodgerblue')
    # m.fillcontinents(color='gainsboro',lake_color='aqua')
    # m.bluemarble()
    return(m)

def mean_netcdf_alldomain(start_year,end_year,direct,var):
    for y in range(start_year,end_year+1):
        # print(y)
        fn=glob.glob(direct+'*'+str(y)+'**nc*')[0]

        if y==start_year:
            matrice=np.average(np.transpose((np.array(xr.open_dataset(fn)[var]))),axis=2)
        else:
            mat2add=np.average(np.transpose((np.array(xr.open_dataset(fn)[var]))),axis=2)
            matrice=np.append(matrice,mat2add,axis=2)
    meant=np.mean(matrice)
            # for i in range(dimx):
            #     for j in range(dimy):
            #         for k in range(dimt):
            #             matdaily[i,j,k]=np.mean(matrice[i,j,:,k])
        # else:
           # mat2add=np.zeros([dimx,dimy,dimt])
           # for i in range(dimx):
           #      for j in range(dimy):
           #          for k in range(dimt):
           #              mat2add[i,j,k]=np.mean(matrice[i,j,:,k])
           # matdaily=np.append(matdaily,mat2add,axis=2)


    return(meant)

def quick_map_plot(lons,lats,mat,bounds,cmap,MSK=np.zeros(0),nticks=4):
    from mpl_toolkits.basemap import Basemap
    # filemask="/srv7_tmp1/jbrajkovic/These/EU-7.5km.nc"
    # ds_mask=xr.open_dataset(filemask)
    # mask=np.transpose(np.array(ds_mask.MASK[:,:]))
    # MSK=mask==1
    if MSK.shape[0]==0:
        MSK=np.zeros_like(mat)==0

    lon_center=4.96
    # lon_center=np.mean(lats)
    lat_center=50.56
    fig=plt.figure(figsize=(6,5))
    ax=fig.add_subplot()
    m = Basemap(width=50000,height=40000,
                rsphere=(649328.00,665262.0),\
                area_thresh=1000.,projection='lcc',\
                lat_1=49.83,lat_2=51.17,lat_0=lat_center,lon_0=lon_center,resolution='i')
    m.drawcountries(linewidth=1.0)
    m.drawcoastlines(linewidth=2.0)
    # m.drawrivers(linewidth=1.5,color='aqua')
    vmax=np.max(mat[pd.isna(mat)==False])
    step=vmax/10.
    # bounds = bounds=np.arange(0,105,5)
    # cmap=cm.jet
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    x,y=m(lons,lats)
    # print(x,y)
    mapa=m.pcolormesh(x,y,mat,norm=norm,cmap=cmap)
    # mapa=m.contourf(x,y,mat,norm=norm,cmap=cmap)
    # m.contour(x,y,MSK,levels=0,linewidth=3.0)

    # ds_mask=xr.open_dataset(filemask)
    # mask=np.transpose(np.array(ds_mask.MASK[:,:]))
    # MSK=mask==1
    Pr_Vesdre=mat[MSK]
    MPRV=np.mean(Pr_Vesdre[pd.isna(Pr_Vesdre)==False])
    text="CM:\n"+"{:.1f}".format(MPRV)
    # text1="{:.1f}".format(np.mean())
    # plt.annotate(text, xy=(0.9, 0.5), xycoords='axes fraction',
    #                             xytext=(0.95, 0.60), textcoords='axes fraction',
    #                             color='black',
    #                             arrowprops=dict(arrowstyle='Simple', color='black'),
    #                             fontsize=24,weight='bold')
    # plt.annotate(text1, xy=(0.9, 0.1), xycoords='axes fraction',
    #                             color='black',
    #                             fontsize=24,weight='bold')
    # m.contourf(x,y,mat,norm=norm,cmap=cmap)
    # m.colorbar(norm=norm,cmap=cmap,location='left',pad=0.6)
    # cities=np.array(['Bruxelles','Charleroi','Liège','Antwerpen','Ghent','LUX.','FRANCE','GERMANY','NETHER-\nLANDS'])
    # xv=np.array([4.354,4.439,5.58,4.402,3.732,5.75,5.371,6.52,4.82])
    # yv=np.array([50.851,50.428,50.634,51.211,51.043,49.785,49.137,50.482,51.821])
    # pos=['top','top','top','top','bottom','bottom','bottom','bottom','bottom']
    # ps1=['left','left','left','left','right','left','left','left','left']
    # decalage=[+500,+500,+500,+500,-500,+500,+500,+500,+500]
    # xv,yv=m(xv,yv)
    # # m.drawmapscale(5.5,49.2,5.5, 49)
    # for i in range(np.size(cities)):
    #     if i<=4:
    #         plt.text(xv[i], yv[i]-decalage[i], cities[i],fontsize=10,
    #                         ha=ps1[i],va=pos[i],color='k')
    #     else:
    #         plt.text(xv[i], yv[i]-decalage[i], cities[i],fontsize=10,
    #                         ha=ps1[i],va=pos[i],color='k',weight='bold')
    #     if i<=4:plt.scatter(xv[i], yv[i],marker='+',color='black',s=8)
    # for item in [fig, ax]:
    #     item.patch.set_visible(False)
    ax.axis("off")
    cbar_ax = fig.add_axes([-0.01, 0.25, 0.05, 0.35])
    cbar=fig.colorbar(mapa,norm=norm, cmap=cmap,pad = 0.6,cax=cbar_ax,orientation="vertical",
                      ticks=np.arange(bounds[0],bounds[np.size(bounds)-1]+(bounds[1]-bounds[0]),(bounds[1]-bounds[0])*nticks),drawedges=True)
    cbar.ax.tick_params(labelsize=10)
    # cbar.set_label('Height (m)',fontsize=14,labelpad=10)
    # cbar.solids.set_edgecolor("face")

def quick_map_plot2(lons,lats,mat,bounds,cmap,ax):
    from mpl_toolkits.basemap import Basemap
    lat_0=50.6;lon_0=4.73
    lon_center=lon_0
    # lon_center=np.mean(lats)
    lat_center=lat_0
    m = Basemap(width=34000,height=30000,
                rsphere=(649328.00,665262.0),\
                area_thresh=1000.,projection='lcc',\
                lat_1=49.83,lat_2=51.17,lat_0=lat_center,
                lon_0=lon_center,resolution='h')
    m.drawcountries(linewidth=1.0)
    m.drawcoastlines(linewidth=2.0)
    # m.drawrivers(linewidth=1.5,color='aqua')
    vmax=np.max(mat[pd.isna(mat)==False])
    step=vmax/10.
    # bounds = bounds=np.arange(0,105,5)
    # cmap=cm.jet
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    x,y=m(lons,lats)
    mapa=m.pcolormesh(x,y,mat,norm=norm,cmap=cmap    )
    return(mapa)

# def get_coordinates(path_to_file):

#     with fiona.open(path_to_file) as shapefile:
#         # Iterate over the records
#         for record in shapefile:
#             # Print the record
#             print(record)
#     # Read the shapefile
#     gdf = gpd.read_file(path_to_file)

#     # Print the first few rows of the GeoDataFrame
#     print(gdf.head())

def mask_belgium(lon,lat,path_in,path_out,center_or_all=2):

    """This routine takes as arguments:
        -The longitudes and latitudes of the netcdf (gridded)
        -a .tif file of the mask we want to create (tif must be in epsg:31370 lambbert 72)
       and creates a mask at the resolution of the input netcdf which is saved as netcdf in path_out

       L'option center_or_all precise si l'on souhaite qu'un des 4 coins des pixels chosisis soient à l'intérieur
       de la zone ou si on regarde uniquement le centre.
       Si center_or_all vaut 1, on ragarde uniquement le centre et donc le masque sera plus petit

       conseil : raster d'une résolution 100 mètres en input'
    """

    "Projecting lon lat to Lambert"
    discheck=300000
    lb=pyproj.Proj(projparams='epsg:31370')
    xlb,ylb=lb(lon,lat)
    if center_or_all!=0:
        xlb_ur=np.zeros([xlb.shape[0],xlb.shape[1]])
        ylb_ur=np.zeros([xlb.shape[0],xlb.shape[1]])

        xlb_ul=np.zeros([xlb.shape[0],xlb.shape[1]])
        ylb_ul=np.zeros([xlb.shape[0],xlb.shape[1]])


        xlb_bl=np.zeros([xlb.shape[0],xlb.shape[1]])
        ylb_bl=np.zeros([xlb.shape[0],xlb.shape[1]])

        xlb_br=np.zeros([xlb.shape[0],xlb.shape[1]])
        ylb_br=np.zeros([xlb.shape[0],xlb.shape[1]])

        "Calcul des sommets des pixels"

        for i in range(1,xlb.shape[0]-1):
            for j in range(1,xlb.shape[1]-1):
                xlb_ur[i,j]=np.mean(lon[i-1:i+1,j:j+2]);ylb_ur[i,j]=np.mean(lat[i-1:i+1,j:j+2])
                xlb_ul[i,j]=np.mean(lon[i-1:i+1,j-1:j+1]);ylb_ul[i,j]=np.mean(lat[i-1:i,j-1:j+1])
                xlb_bl[i,j]=np.mean(lon[i:i+2,j-1:j+1]);ylb_bl[i,j]=np.mean(lat[i:i+2,j-1:j+1])
                xlb_br[i,j]=np.mean(lon[i:i+2,j:j+2]);ylb_br[i,j]=np.mean(lat[i:i+2,j:j+2])

        xlb_ur,ylb_ur=lb(xlb_ur,ylb_ur)
        xlb_ul,ylb_ul=lb(xlb_ul,ylb_ul)
        xlb_bl,ylb_bl=lb(xlb_bl,ylb_bl)
        xlb_br,ylb_br=lb(xlb_br,ylb_br)




    # print (ylb_ur[1:]-ylb[1:])
    "Opening the raster file"

    im = Image.open(path_in)
    imarray = np.array(im)

    file_name = path_in
    with rasterio.open(file_name) as src:
         band1 = src.read(1)
         print('Band1 has shape', band1.shape)
         height = band1.shape[0]
         width = band1.shape[1]
         cols, rows = np.meshgrid(np.arange(width), np.arange(height))
         xs, ys = rasterio.transform.xy(src.transform, rows, cols)
         lons= np.array(xs)
         lats = np.array(ys)
         print('lons shape', lons.shape)
    # print(ys,ylb)
    lats=lats[imarray!=0]
    lons=lons[imarray!=0]
    print(lats)
    MSK=np.zeros(xlb.shape)

    print(np.max(xs),np.max(ys))

    "Finding the pixels which are in the zone"

    "perimetre de recherche"
    maxi_lat=np.max(lats)
    mini_lat=np.min(lats)
    mini_lon=np.min(lons)
    maxi_lon=np.max(lons)
    print(maxi_lat,mini_lat)
    disrech=10000000000
    disu=disrech
    disb=disrech
    disl=disrech
    disr=disrech
    for i in range(xlb.shape[0]):
        # print(i)
        for j in range(xlb.shape[1]):
            if abs(ylb[i,j]-maxi_lat)<disu and ylb[i,j]-maxi_lat>=0 :
                iu=i
                disu=abs(ylb[i,j]-maxi_lat)

            if abs( ylb[i,j]-mini_lat)<disb and ylb[i,j]-mini_lat<=0:
                ib=i
                disb=abs( ylb[i,j]-mini_lat)

            if abs(xlb[i,j]-mini_lon)<disl and xlb[i,j]-mini_lon <=0 :
                # print(xlb[i,j]-mini_lon)
                jl=j
                disl=abs(xlb[i,j]-mini_lon)
            if abs(xlb[i,j]-maxi_lon)<disr and xlb[i,j]-maxi_lon >=0 :
                jr=j
                disr=abs(xlb[i,j]-maxi_lon)

    print(disu,disr,disb,disl)
    print(iu,ib,jl,jr)
    # if iu==ib or jl==jr:
    # iu=1;ib=xlb.shape[0]-1
    # jl=1;jr=xlb.shape[1]-1
    print(iu,ib,jl,jr)
    print('aire latitudinale de recherche : '+"{:.0f}".format(ylb[int(ib),int(jl)])+' '+"{:.0f}".format(ylb[int(iu),int(jl)]))
    for i in range(iu-2,ib+2):
        print(i,np.mean(ylb[i,:]))
        for j in range(jl-2,jr+2):
                # print(xlb[i,j],ylb[i,j])
                # msk_stp=lons[((abs(lons-xlb_ur[i,j])<100)&(abs(lats-ylb_ur[i,j])<100))]
                if center_or_all==1:
                    msk_stp=lons[((abs(lons-xlb[i,j])<discheck)&(abs(lats-ylb[i,j])<discheck))|
                             ((abs(lons-xlb_ur[i,j])<discheck)&(abs(lats-ylb_ur[i,j])<discheck))|
                             ((abs(lons-xlb_ul[i,j])<discheck)&(abs(lats-ylb_ul[i,j])<discheck))|
                             ((abs(lons-xlb_bl[i,j])<discheck)&(abs(lats-ylb_bl[i,j])<discheck))|
                             ((abs(lons-xlb_br[i,j])<discheck)&(abs(lats-ylb_br[i,j])<discheck))]

                else:
                    msk_stp=lons[((abs(lons-xlb[i,j])<discheck)&(abs(lats-ylb[i,j])<discheck))]

                # print(i,j)
                # if i%10==0 and j==jl:
                # print(i,j)
                if np.size(msk_stp)!=0:#print('ok');
                    print(i,j)
                    MSK[i,j]=1
                # print(msk_stp,i,j)
                # if xlb[i,j]-lons[k]<100. and ylb[i,j]-lats[k]<100:
                #     MSK[i,j]=1.

    # MSK
    # time=[1]

    "writing the output netcdf with the mask"

    coords=dict(
        LON=(["y","x"],np.transpose(xlb)),
        LAT=(["y","x"],np.transpose(ylb)),
        )
    Mar_ds=xr.DataArray(
        data=np.transpose(np.zeros([xlb.shape[0],xlb.shape[1]])),
        dims=["y","x"],
        coords=coords,
        )
    Mar_rain=xr.DataArray(
        data=np.transpose(MSK),
        dims=["y","x"],
        coords=coords,
        attrs=dict(
            description='MSK',
            units=''))

    Mar_ds['MSK']=Mar_rain
    format1='NETCDF4'
    Mar_ds.to_netcdf(path_out,mode='w',format=format1)
    MSK=[MSK==1]
    return (ylb)
        # return(coords)

def mask_belgiumV2(lon,lat,path_in,path_out,center_or_all=2,discheck=300000,buffer=2):
    """This routine takes as arguments:
        -The longitudes and latitudes of the netcdf (gridded)
        -a .tif file of the mask we want to create (tif must be in epsg:31370 lambbert 72)
       and creates a mask at the resolution of the input netcdf which is saved as netcdf in path_out

       L'option center_or_all precise si l'on souhaite qu'un des 4 coins des pixels chosisis soient à l'intérieur
       de la zone ou si on regarde uniquement le centre.
       Si center_or_all vaut 1, on ragarde uniquement le centre et donc le masque sera plus petit

       conseil : raster d'une résolution 100 mètres en input'
    """

    "Projecting lon lat to Lambert"
    # discheck=300000
    print('Check distance = '+str(discheck) + 'meters')
    lb=pyproj.Proj(projparams='epsg:31370')

    if center_or_all!=0:
        xlb_ur=np.zeros_like(lon)
        ylb_ur=np.zeros_like(lon)

        xlb_ul=np.zeros_like(lon)
        ylb_ul=np.zeros_like(lon)


        xlb_bl=np.zeros_like(lon)
        ylb_bl=np.zeros_like(lon)

        xlb_br=np.zeros_like(lon)
        ylb_br=np.zeros_like(lon)

        "Calcul des sommets des pixels"

        for i in range(1,lon.shape[0]-1):
            for j in range(1,lon.shape[1]-1):
                xlb_ur[i,j]=np.mean(lon[i-1:i+1,j:j+2]);ylb_ur[i,j]=np.mean(lat[i-1:i+1,j:j+2])
                xlb_ul[i,j]=np.mean(lon[i-1:i+1,j-1:j+1]);ylb_ul[i,j]=np.mean(lat[i-1:i,j-1:j+1])
                xlb_bl[i,j]=np.mean(lon[i:i+2,j-1:j+1]);ylb_bl[i,j]=np.mean(lat[i:i+2,j-1:j+1])
                xlb_br[i,j]=np.mean(lon[i:i+2,j:j+2]);ylb_br[i,j]=np.mean(lat[i:i+2,j:j+2])




    # print (ylb_ur[1:]-ylb[1:])
    "Opening the raster file"

    im = Image.open(path_in)
    imarray = np.array(im)

    file_name = path_in
    with rasterio.open(file_name) as src:
         band1 = src.read(1)
         print('Band1 has shape', band1.shape)
         height = band1.shape[0]
         width = band1.shape[1]
         cols, rows = np.meshgrid(np.arange(width), np.arange(height))
         xs, ys = rasterio.transform.xy(src.transform, rows, cols)
         lons= np.array(xs)
         lats = np.array(ys)
         print('lons shape', lons.shape)

    inProj=Proj(init='epsg:31370')
    outProj = Proj(init='epsg:4326')

    lons,lats=transform(inProj,outProj,lons,lats)

    # print(ys,ylb)
    # plt.imshow(imarray);plt.colorbar()
    # plt.show()
    lats=lats[imarray>0]
    lons=lons[imarray>0]

    print(lats)
    MSK=np.zeros(lon.shape)

    print(np.max(xs),np.max(ys))

    "Finding the pixels which are in the zone"

    "perimetre de recherche"
    maxi_lat=np.max(lats)
    mini_lat=np.min(lats)
    mini_lon=np.min(lons)
    maxi_lon=np.max(lons)
    me_lat=np.mean(lats)
    print(maxi_lat,mini_lat)
    disrech=10000000000
    disu=disrech
    disb=disrech
    disl=disrech
    disr=disrech

    print('lon max ',maxi_lon,mini_lon,me_lat,maxi_lat,mini_lat)
    for i in range(lon.shape[0]):
        # print(i)
        for j in range(lon.shape[1]):
            if ct.dis2pix(lat[i,j], lon[i,j], maxi_lat, lon[i,j])<disu and lat[i,j]>=maxi_lat:
                iu=i
                disu=ct.dis2pix(lat[i,j], lon[i,j], maxi_lat, lon[i,j])

            if ct.dis2pix(lat[i,j], lon[i,j], mini_lat, lon[i,j])<disb and lat[i,j]<=mini_lat:
                ib=i
                disb=ct.dis2pix(lat[i,j], lon[i,j], mini_lat, lon[i,j])

            if ct.dis2pix(lat[i,j], lon[i,j], me_lat, mini_lon)<disl and lon[i,j]<=mini_lon:
                jl=j
                disl=ct.dis2pix(lat[i,j], lon[i,j], me_lat, mini_lon)

            if ct.dis2pix(lat[i,j], lon[i,j], me_lat, maxi_lon)<disr and lon[i,j]>=maxi_lon:

                jr=j
                disr=ct.dis2pix(lat[i,j], lon[i,j], me_lat, maxi_lon)

    print(disu,disr,disb,disl)
    print(iu,ib,jl,jr)
    print('aire latitudinale de recherche : '+"{:.0f}".format(lat[int(ib),int(jl)])+' '+"{:.0f}".format(lat[int(iu),int(jl)]))
    ide=iu-2;ifi=ib+2
    if ide<0:ide=0;
    if ifi>lon.shape[0]:ifi=lon.shape[0]

    jde=jl-2;jfi=jr+2
    if jde<0:jde=0
    if jr>lon.shape[0]:jfi=lon.shape[1]
    center_pixel_lon=np.mean(lons)
    center_pixel_lat=np.mean(lats)
    min_dist1=100000
    for i in range(ide,ifi):
        print(i,np.mean(lat[i,:]))
        for j in range(jde,jfi):
                # print(xlb[i,j],ylb[i,j])
                # msk_stp=lons[((abs(lons-xlb_ur[i,j])<100)&(abs(lats-ylb_ur[i,j])<100))]
                if center_or_all !=2:
                    if center_or_all==1:

                        msk_stp=lons[((ct.dis2pix(lats, lons, lat[i,j], lon[i,j])<discheck)|
                                     ((ct.dis2pix(lats, lons, ylb_ur[i,j], xlb_ur[i,j]))<discheck)|
                                     ((ct.dis2pix(lats, lons, ylb_ul[i,j], xlb_ul[i,j]))<discheck)|
                                     (ct.dis2pix(lats, lons, ylb_bl[i,j], xlb_bl[i,j])<discheck)|
                                    ((ct.dis2pix(lats, lons, ylb_br[i,j], xlb_br[i,j]))<discheck))]


                    else:
                        msk_stp=lons[(ct.dis2pix(lats, lons, lat[i,j], lon[i,j])<discheck)]

                    if np.size(msk_stp)!=0:#print('ok');
                        print(i,j)
                        MSK[i,j]=1

                else:
                    dists=np.matrix([ct.dis2pix(center_pixel_lat, center_pixel_lon, lat[i,j], lon[i,j]),
                                 ct.dis2pix(center_pixel_lat, center_pixel_lon, ylb_ur[i,j], xlb_ur[i,j]),
                                 ct.dis2pix(center_pixel_lat, center_pixel_lon, ylb_ul[i,j], xlb_ul[i,j]),
                                 ct.dis2pix(center_pixel_lat, center_pixel_lon, ylb_bl[i,j], xlb_bl[i,j]),
                                 ct.dis2pix(center_pixel_lat, center_pixel_lon, ylb_br[i,j], xlb_br[i,j])])
                    min_dist=np.min(dists)

                    if min_dist<min_dist1:
                        min_dist1=min_dist
                        iic=i;jjc=j
    if center_or_all==2:
        MSK[iic-buffer:iic+buffer+1,jjc-buffer:jjc+buffer+1]=1


    "writing the output netcdf with the mask"

    coords=dict(
        LON=(["y","x"],np.transpose(lon)),
        LAT=(["y","x"],np.transpose(lat)),
        )
    Mar_ds=xr.DataArray(
        data=np.transpose(np.zeros([lon.shape[0],lat.shape[1]])),
        dims=["y","x"],
        coords=coords,
        )
    Mar_rain=xr.DataArray(
        data=np.transpose(MSK),
        dims=["y","x"],
        coords=coords,
        attrs=dict(
            description='MSK',
            units=''))

    Mar_ds['MSK']=Mar_rain
    format1='NETCDF4'
    Mar_ds.to_netcdf(path_out,mode='w',format=format1)
    MSK=[MSK==1]
    return (MSK)

def dis2pix(lat1,lon1,lat2,lon2):
    lat1,lon1,lat2,lon2=np.deg2rad(lat1),np.deg2rad(lon1),np.deg2rad(lat2),np.deg2rad(lon2)
    dis=np.arccos(np.sin(lat1)*np.sin(lat2)+np.cos(lat1)*np.cos(lat2)*np.cos(abs(lon1-lon2)))*6371000
    return(dis)

def anomaly_cmap():
    cdict = {'blue':   [[0.0,  0.0, 0.0]],
         'red':    [[0.0,  0.0, 0.0]],
         'green':  [[0.0,  0.0, 0.0]]}
    newcmp = LinearSegmentedColormap('testCmap', segmentdata=cdict, N=256)
    return(newcmp)

def grid_mean(folder,year,var,season,sum_or_mean=0,nts=24,lev=0,nf=0,fn1='__'):
    # fn=glob.glob(folder+'*'+str(year)+'*')[nf]
    fn=folder
    # print(fn)
    seasons_names=['SP','SU','F','W','DJF','MAM','JJA','SON']
    if season!='Y':

        beg_seas=[81,173,265,356,335,60,152,244]
        end_seas=[172,264,355,80,59,151,243,334]
        for i in range(8):
            if seasons_names[i]==season:
                bs=beg_seas[i]
                es=end_seas[i]
                break
    else:
        bs=1;es=365
        # print(bs,es)

    if var=='MBRR':
        if sum_or_mean:
            if season!='W' and season!='DJF':
                Ds=np.sum(np.transpose(np.array(xr.open_dataset(fn)['MBRR'])+\
                            np.array(xr.open_dataset(fn)['MBSF']))\
                            [:,:,(bs-1)*nts+1:es*nts+nts],axis=2)
            else:
                # fn1=glob.glob(folder+'*'+str(year-1)+'*')[nf]
                Ds=np.sum(np.transpose(np.array(xr.open_dataset(fn)['MBRR'])+\
                            np.array(xr.open_dataset(fn)['MBSF']))\
                            [:,:,0:es*nts+nts],axis=2)\
                    +np.sum(np.transpose(np.array(xr.open_dataset(fn1)['MBRR'])+\
                                np.array(xr.open_dataset(fn1)['MBSF']))\
                                [:,:,(bs-1)*nts+1:],axis=2)
        else:
            if season!='W' and season !='DJF':
                Ds=np.average(np.transpose(np.array(xr.open_dataset(fn)['MBRR'])+\
                            np.array(xr.open_dataset(fn)['MBSF']))\
                            [:,:,(bs-1)*nts+1: es*nts+nts],axis=2)
            else:
                fn1=glob.glob(folder+'*'+str(year-1)+'*')[0]
                Ds=(np.transpose(np.array(xr.open_dataset(fn)['MBRR'])+\
                            np.array(xr.open_dataset(fn)['MBSF']))\
                            [:,:,0:es*nts+nts])
                Ds=np.append(Ds,np.transpose(np.array(xr.open_dataset(fn1)['MBRR'])+\
                                np.array(xr.open_dataset(fn1)['MBSF']))\
                                [:,:,(bs-1)*nts+1:],axis=2)
                Ds=np.average(Ds,axis=2)
    else:
        mat=np.array(xr.open_dataset(fn)[var])
        # fn1=glob.glob(folder+'*'+str(year-1)+'*')[nf]
        if np.size(mat.shape)==4:
            axis=3
            if season=='W' or season=='DJF':
               mat=np.append(np.transpose(mat)\
                            [:,:,lev,0:es*nts+nts],
                            np.transpose(np.array(xr.open_dataset(fn1)[var]))[:,:,lev,(bs-1)*nts+1:],axis=2)
            elif season=='Y'  :
                mat=np.transpose(mat)\
                        [:,:,lev,:]
            else:
                mat=np.transpose(mat)\
                        [:,:,lev,(bs-1)*nts+1: es*nts+nts]
        else:
            axis=2
            if season=='W' or season=='DJF':
               mat=np.append(np.transpose(mat)\
                            [:,:,0:es*nts+nts],
                            np.transpose(np.array(xr.open_dataset(fn1)[var]))[:,:,(bs-1)*nts+1:],axis=2)
            elif season=='Y'  :
                mat=np.transpose(mat)\
                        [:,:,:]

            else:
                mat=np.transpose(mat)\
                        [:,:,(bs-1)*nts+1: es*nts+nts]


        if sum_or_mean:

                Ds=np.sum(mat,axis=2)

        else:
                print(axis)
                Ds=np.average(mat,axis=2)


    return(Ds)

def find_pix_be(lon_p,lat_p,lons,lats):
    Lb72=pyproj.Proj(projparams='epsg:31370')
    xl,yl=Lb72(lon_p,lat_p)
    xls,yls=Lb72(lons,lats)
    mat_dis=((xls-xl)**2+(yls-yl)**2)**0.5
    dists=10**12
    for j in range(mat_dis.shape[0]):
        for k in range(mat_dis.shape[1]):
                if mat_dis[j,k]<=dists:
                    i_s=j;j_s=k;dists=mat_dis[j,k]
    return([i_s,j_s])
    # return(mat_dis)

def find_MARs_closest_pixel(lonsm,latsm,lonsi,latsi,neighbours=1):
    Lb72=pyproj.Proj(projparams='epsg:31370')
    xi,yi=Lb72(lonsi,latsi)
    xm,ym=Lb72(lonsm,latsm)
    dis2pixels=np.zeros([xm.shape[0],ym.shape[1],xi.shape[0],yi.shape[1]])
    output=np.zeros([xm.shape[0],ym.shape[1],neighbours,3])
    for i in range(xm.shape[0]):
        for j in range(xm.shape[1]):
            for n in range(neighbours):
                dists=np.zeros(neighbours)
                dists[:]=10E12
                for k in range(xi.shape[0]):
                    for l in range(xi.shape[1]):
                        dis2pixels[i,j,k,l]=((xm[i,j]-xi[k,l])**2+(ym[i,j]-yi[k,l])**2)**0.5
                        if n==0:
                            if dis2pixels[i,j,k,l]<dists[0]:
                                dists[n]=dis2pixels[i,j,k,l]
                                output[i,j,n,0]=k
                                output[i,j,n,1]=l
                                output[i,j,n,2]=1/dists[n]
                        else:
                            if dis2pixels[i,j,k,l]<dists[n] and\
                                dis2pixels[i,j,k,l]>dists[n-1]:
                                dists[n]=dis2pixels[i,j,k,l]
                                output[i,j,n,0]=k
                                output[i,j,n,1]=l
                                output[i,j,n,2]=1/(dists[n]/1000)
    return(output)

def IPCC_cmap():
    cmap = mpl.colors.LinearSegmentedColormap.from_list("", [(84/256, 48/256, 5/256),
                                                             (245/256,245/256,245/256),
                                                             (0/256,60/256,48/256)])
    return(cmap)

def draw_cities(m,fs_c=14,fs_C=16):
    fs=10
    cities=np.array(['Bruxelles','Charleroi','Liège',
                     'Antwerpen','Ghent',
                     'LUX.','FRANCE','GERMANY','NETHER-\nLANDS'])
    plot_or_not=[0,0,1,0,0,1,0,0,0]
    xv=np.array([4.354,4.439,5.58,4.402,3.732,5.81,5.371,6.52,4.82])
    yv=np.array([50.851,50.428,50.634,51.211,51.043,49.785,49.137,50.482,51.821])
    pos=['top','top','bottom','top','bottom','bottom','bottom','bottom','bottom']
    ps1=['left','left','right','left','right','left','left','left','left']
    decalage=np.array([+500,+500,+0,+500,-500,+500,+500,+500,+500])
    decalage[:]=0
    xv,yv=m(xv,yv)
    # m.drawmapscale(5.5,49.2,5.5, 49)
    for i in range(np.size(cities)):
        if plot_or_not[i]:
            if i<=4:
                plt.gca()
                plt.scatter(xv[i], yv[i],color='black',s=25)
                plt.text(xv[i], yv[i]-decalage[i], cities[i],fontsize=fs_c,
                                ha=ps1[i],va=pos[i],color='k',weight='bold',
                                path_effects=[pe.withStroke(linewidth=4, foreground="white")])

            else:
                plt.text(xv[i], yv[i]-decalage[i], cities[i],fontsize=fs_C,
                                ha=ps1[i],va=pos[i],color='k',weight='bold')



def draw_stations(m,n_id=1,fs=8):


       stations_lons=[6.07960,5.912,6.228,
                            5.594,5.405,5.255,
                            4.591,4.653,4.471,
                            5.453,4.667,3.780,
                            4.359,5.421,4.486,
                            3.799,3.664,3.115,
                            4.539,5.470,5.072,
                            4.470,4.381,3.208,
                            2.856,2.668     ]

       stations_lats=[50.511,50.478,50.459,
                            49.647,50.037,50.207,
                            50.094,50.226,50.478,
                            50.653,50.593,50.581,
                            50.799,50.903,50.895,
                            50.993,50.943,50.892,
                            51.064,51.170,51.270,
                            51.219,51.322
                            ,51.322,51.200,51.126]

       stations_names=['Mont-Rigi','Spa','Elsenborn',
                              'Buzenol','Saint-Hubert','Humain',
                              'Dourbes','Florennes','Gosselies',
                              'Bierset','Ernage','Chièvres',
                              'Uccle','Diepenbeek','Zaventem',
                              'Melle','Semmerzake','Beitem',
                              'Sint-Katelijne','Kleine-Brogel','Retie',
                              'Deurne','Stabroek','Zeebrugge',
                              'Middelkerke','Koksijde']

       stations_index=['06494','06490','06496',
                        '06484','06476','06472',
                        '06455','06456','06449',
                        '06478','06459','06432',
                        '06447','06477','06451',
                        '06434','06428','06414',
                        '06439','06479','06464',
                        '06450','06438','06418',
                        '_','06400']
       if n_id:te=stations_names
       else:te=stations_index
       xv,yv=m(stations_lons,stations_lats)
       # m.drawmapscale(5.5,49.2,5.5, 49)
       for i in range(np.size(stations_lons)):
               plt.text(xv[i], yv[i], te[i],fontsize=fs,
                               color='k',weight='bold')


def box_plot(data, edge_color, fill_color,ax):
    bp = ax.boxplot(data, patch_artist=True)

    for element in ['boxes', 'whiskers', 'fliers', 'means', 'medians', 'caps']:
        plt.setp(bp[element], color=edge_color)

    for patch in bp['boxes']:
        patch.set(facecolor=fill_color)

    return bp


def endmonth(year):
    if ct.isbis(year):
        em=[31,29,31,30,31,30,31,31,30,31,30,31]
    else:
        em=[31,28,31,30,31,30,31,31,30,31,30,31]
    return(em)

def radar_coord():

    radar='/srv5_tmp3/RADCLIM/2021/20210714230000.radclim.accum1h.hdf'
    f = h5py.File(radar, "r")

    ul_x=f['dataset1']['where'].attrs['UL_x']
    ul_y=f['dataset1']['where'].attrs['UL_y']
    xsize=f['dataset1']['where'].attrs['xsize']
    ysize=f['dataset1']['where'].attrs['ysize']
    xscale=f['dataset1']['where'].attrs['xscale']
    yscale=f['dataset1']['where'].attrs['yscale']

    lr_x = ul_x + (xsize*xscale)
    lr_x = ul_x + (xsize*xscale)
    lr_y = ul_y - (ysize*yscale)

    x=np.arange(ul_x, lr_x, xscale) + xscale/2
    y=np.arange(lr_y, ul_y, yscale) - yscale/2

    xx,yy = np.meshgrid(x,y)

    yy= np.flip(yy)

    inProj=Proj(r'+proj=lcc +lat_1=49.83333333333334 +lat_2=51.16666666666666 +lat_0=50.797815 +lon_0=4.359215833333333 +x_0=649328 +y_0=665262 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs ')
    outProj = Proj(init='epsg:4326')

    lon,lat=transform(inProj,outProj,xx,yy)
    return(lon,lat)

def marray(ds,var):
    return(np.transpose(np.array(ds[var])))

def marrayV2(ds,var):
    return(np.transpose(np.array(ds[var]),axes=(1,2,0)))
    print('ok')

def RGEV(retp,nyears,loc,sca,sha):
    prob=1/(retp)
    ret=loc-(sca/sha)*(1-(-np.log(1-prob))**(-sha))
    return(ret)

def GEV_frequency(value,loc,sca,sha):
    prob=1-np.exp(-(1-(((loc-value)*sha)/sca))**(-1/sha))

    ret=(1/prob)
    return(ret)

def GEVCI(retp,loc,sc,sh,
          varloc,varsc,varsh,
          covlocsc,covlocsh,covscsh):
    prob=1/(retp)
    derloc=1
    dersc=-(1-(-np.log(1-prob))**(-sh))
    dersh=sc*(((1-sh)*np.log(1-prob))/(sh*(1-sh))+(1-(-np.log(1-prob))**(-sh))/sh**2)
    S2T=derloc**2*varloc+dersc**2*varsc+dersh**2*varsh\
        +2*derloc*dersc*covlocsc+2*derloc*dersh*covlocsh+2*dersc*dersh*covscsh
    CI=S2T**0.5*1.645
    return(CI)





def gumCI(retp,loc,sc,
          varloc,varsc,
          covlocsc):
    prob=1/(retp)
    derloc=1
    dersc=-np.log(-np.log(1-prob))
    S2T=derloc**2*varloc+dersc**2*varsc+2*derloc*dersc*covlocsc
    CI=S2T**0.5*1.645
    return(CI)


def RGum(retp,nyears,loc,sca):
    prob=1/(retp)#*nyears)
    ret=loc-sca*np.log(-np.log(1-prob))
    return(ret)

def Gum_frequency(value,loc,sca):
    prob=1-np.exp(-np.exp((loc-value)/sca))
    ret=1/prob
    return(ret)

def extreme_matrix(fn,ret_per=20,value=50,mx=80,my=50,abs_or_retour=1,ydays=365,start_year=2011,end_year=2040,nts=24,gpd_gev_gum=0):
    # print('ok')

    f=open(fn,'r')
    indice_suivi=0

    mat=np.zeros([mx,my])*float('nan')
    mv=np.array(ret_per*ydays)
    for line in f:
        if indice_suivi>0:
            lines=line.strip()
            columns=lines.split()
            # print(indice_suivi)
            # print(columns[0])
            if int(columns[0])<=my:
                i=0;j=int(columns[0])
            else:
                j=int(int(columns[0])%my)-1
                i=int((int(columns[0])-j)/my)
            # if int(columns[0])<1000:print(int(columns[0]),i,j)
            # print(i,j)
            if j==0:j=my-1;i=i-1
            else:j=j-1
            if gpd_gev_gum==0:
                sca=float(columns[1])
                sha=float(columns[2])
                ne=float(columns[7])
                ncl=float(columns[8])
                th=float(columns[9])
                varsh=float(columns[4])
                varsc=float(columns[3])
                cov=float(columns[5])
                pu=ne/(ydays*(end_year-start_year+1));teta=ncl/ne
                if abs_or_retour:

                    if sha==0:
                        continue
                    mat[i,j]=ct.RGPD(mv,sha,sca,pu,teta,th)
                elif abs_or_retour==0:
                    if sha==0:
                        continue
                    if pd.isna(value[i,j])==False:
                        mat[i,j]=ct.GPD_frequency(value[i,j], sha ,sca, pu, teta, th, ydays)
                elif abs_or_retour==2:
                    mat[i,j]=ct.CIGPD(mv, sha, sca, pu, teta, th, varsc, varsh, cov)
            elif gpd_gev_gum==1:
                  loc=float(columns[10])
                  sca=float(columns[11])
                  sha=float(columns[12])
                  if sha==0:continue;indice_suivi+=1
                  nye=end_year-start_year+1
                  if abs_or_retour: mat[i,j]=ct.RGEV(ret_per,nye,loc,sca,sha)
                  else:mat[i,j]=ct.GEV_frequency(value[i,j],loc,sca, sha)

            elif gpd_gev_gum==2:
                nye=end_year-start_year+1
                loc=float(columns[13])
                sca=float(columns[14])
                if abs_or_retour: mat[i,j]=ct.RGum(ret_per,nye,loc,sca)
                else:mat[i,j]=ct.Gum_frequency(value[i,j],loc,sca)
        indice_suivi+=1
    return(mat)

def extreme_matrix_V2(fn,ret_per=20,value=50,mx=80,my=50,
                      abs_or_retour=1,ydays=365,
                      start_year=2011,end_year=2040,
                      nts=24,
                      gpd_gev_gum=0,unst_st=0,var_unst='MKam',y_unst=2021):
    # print('ok')


    data=ct.df_from_file(fn)
    mat=np.zeros([mx,my])*float('nan')
    mv=np.array(ret_per*ydays)

    for p in range(data.shape[0]):
    # for line in f:

            ind_pix=data['indice'][p]
            if ind_pix<=my:
                i=0;j=ind_pix
            else:
                j=int(ind_pix%my)-1
                i=int((ind_pix-j)/my)
            # if int(columns[0])<1000:print(int(columns[0]),i,j)
            # print(i,j)
            if j==0:j=my-1;i=i-1
            else:j=j-1
            if unst_st==0:

                if gpd_gev_gum==0:
                    sca=data['sc'][p]
                    sha=data['sh'][p]
                    ne=data['ne'][p]
                    ncl=data['nc'][p]
                    th=data['th'][p]
                    varsh=data['varsh'][p]
                    varsc=data['varsc'][p]
                    cov=data['cov'][p]
                    pu=ne/(ydays*(end_year-start_year+1));teta=ncl/ne
                    if abs_or_retour:
                        if sha==0:
                            continue
                        mat[i,j]=ct.RGPD(mv,sha,sca,pu,teta,th)
                    elif abs_or_retour==0:
                        if sha==0:
                            continue
                        if pd.isna(value[i,j])==False:
                            mat[i,j]=ct.GPD_frequency(value[i,j], sha ,sca, pu, teta, th, ydays)
                    elif abs_or_retour==2:
                        mat[i,j]=ct.CIGPD(mv, sha, sca, pu, teta, th, varsc, varsh, cov)
                elif gpd_gev_gum==1:
                      loc=data['GEVloc'][p]
                      sca=data['GEVscale'][p]
                      sha=data['GEVshape'][p]
                      if sha==0:continue
                      nye=end_year-start_year+1
                      if abs_or_retour: mat[i,j]=ct.RGEV(ret_per,nye,loc,sca,sha)
                      else:mat[i,j]=ct.GEV_frequency(value[i,j],loc,sca, sha)

                elif gpd_gev_gum==2:
                    nye=end_year-start_year+1
                    loc=data['GUMshape'][p]
                    sca=data['GUMscale'][p]
                    if abs_or_retour: mat[i,j]=ct.RGum(ret_per,nye,loc,sca)
                    else:mat[i,j]=ct.Gum_frequency(value[i,j],loc,sca)
            elif unst_st==2:
                mat[i,j]=data[var_unst][p]
            else:
                if gpd_gev_gum==0:
                    sca=data['sc'][p]
                    sha=data['sh'][p]
                    ne=data['ne'][p]
                    ncl=data['nc'][p]
                    th=data['th'][p]
                    varsh=data['varsh'][p]
                    varsc=data['varsc'][p]
                    cov=data['cov'][p]
                    slam=data['slam'][p]
                    th=th+(y_unst-start_year)*slam
                    sca=sca+(y_unst-start_year)*slam
                    if abs_or_retour:
                        if sha==0:
                            continue
                        mat[i,j]=ct.RGPD(mv,sha,sca,pu,teta,th)
                    elif abs_or_retour==0:
                        if sha==0:
                            continue
                        if pd.isna(value[i,j])==False:
                            mat[i,j]=ct.GPD_frequency(value[i,j], sha ,sca, pu, teta, th, ydays)
                    elif abs_or_retour==2:
                        mat[i,j]=ct.CIGPD(mv, sha, sca, pu, teta, th, varsc, varsh, cov)
                elif gpd_gev_gum==1:
                       loc=data['GEVloc'][p]
                       sca=data['GEVscale'][p]
                       sha=data['GEVshape'][p]
                       slam=data['slam'][p]
                       loc=loc+(y_unst-start_year)*slam
                       sca=sca+(y_unst-start_year)*slam
                       if sha==0:continue
                       nye=end_year-start_year+1
                       if abs_or_retour: mat[i,j]=ct.RGEV(ret_per,nye,loc,sca,sha)
                       else:mat[i,j]=ct.GEV_frequency(value[i,j],loc,sca, sha)

                elif gpd_gev_gum==2:
                     nye=end_year-start_year+1
                     loc=data['GUMshape'][p]
                     sca=data['GUMscale'][p]
                     if abs_or_retour: mat[i,j]=ct.RGum(ret_per,nye,loc,sca)
                     else:mat[i,j]=ct.Gum_frequency(value[i,j],loc,sca)






    return(mat)

def find_clusters(TS1):
    clss=np.zeros(0)
    indexes=np.zeros(0)
    t=0
    r=7
    qu=np.quantile(TS1, 0.99)
    TS=np.array(TS1)
    TS[TS1<qu]=float('nan')
    while t < np.size(TS):
        # print(t)
        if pd.isna(TS[t])==False:
            cl_maxima=TS[t]
            t1=t+1
            suiv=0
            cl_ind=t
            while suiv<r and t1<np.size(TS):
                suiv+=1

                # print(t1)
                if pd.isna(TS[t1])==False:
                    # print('ok')
                    suiv=0
                    if TS[t1]>cl_maxima:cl_maxima=TS[t1];cl_ind=t1
                    # print(suiv)
                t1+=1

            clss=np.append(clss,cl_maxima)
            indexes=np.append(indexes,cl_ind)
            # print(cls_dates.shape)

            t=t1

        t+=1
    return(clss,indexes)


def df_from_file(fn):
    f=open(fn,mode='r')
    suiv=-1
    for line in f:
        suiv+=1
        lines=line.strip()
        lines=lines.split()
        if suiv>0:


            dat=lines[0]
            vappend=np.zeros([1,np.size(lines[:])])
            # dates=np.append(dates,dat[1:-1])
            for i in range(vappend.shape[1]):
                vappend[0,i]=float(lines[i])

            if suiv==1:
                data=vappend
            else:
                data=np.append(data,vappend,axis=0)
        else:
            vnames=lines

    data=pd.DataFrame(data)
    data.columns=vnames
    return(data)
