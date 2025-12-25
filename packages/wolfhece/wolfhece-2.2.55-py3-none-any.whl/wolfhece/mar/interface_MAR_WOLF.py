
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 16:31:47 2023

@author: jbrajkovic
"""

import numpy as np
import matplotlib.pyplot as plt
import commontools as ct
import xarray as xr
import matplotlib as mpl
import matplotlib.cm as cm
import glob as glob
import pyproj
import geopandas as gpd
from shapely.geometry import Polygon
from fiona.crs import from_epsg
import datetime
import os



class MAR_input_data:
    def __init__(self,xsummits,ysummits,date_debut,date_fin,directory,var):
        self.var=var
        self.xsummits=xsummits
        self.ysummits=ysummits
        self.date_debut=date_debut
        self.date_fin=date_fin
        self.directory=directory
        self.fn=fn = glob.glob(self.directory+"*"+str(date_debut.year)+"**nc")
        self.ds=xr.open_dataset(fn[0])
        self.lons=np.transpose(np.array(self.ds.LON))
        self.lats=np.transpose(np.array(self.ds.LAT))
        self.Lb72=pyproj.Proj(projparams='epsg:31370')
        self.x_Lb72, self.y_Lb72 = self.Lb72(self.lons,self.lats)


    def mask_rectangles(self):
       i=0
       xmin=np.min(self.xsummits);xmax=np.max(self.xsummits)
       ymin=np.min(self.ysummits);ymax=np.max(self.ysummits)
       x=self.x_Lb72;y=self.y_Lb72
       mask=np.zeros([x.shape[0],x.shape[1]])


       while i<3:
           # print(i)
           j=i+1
           while j<4:
               # print(i,xsummits)
               # print(j)
               if self.xsummits[j]<self.xsummits[i]:
                   tempx=self.xsummits[i]
                   tempy=self.ysummits[i]
                   self.xsummits[i]=self.xsummits[j]
                   self.ysummits[i]=self.ysummits[j]
                   self.xsummits[j]=tempx
                   self.ysummits[j]=tempy
                   j=i+1
               j=j+1

           i=i+1
       print(self.xsummits);print(self.ysummits)

       if (self.xsummits[0]-self.xsummits[1])>0.01:
           pab=((self.ysummits[1]-self.ysummits[0])/(self.xsummits[1]-self.xsummits[0]))
           pac=((self.ysummits[2]-self.ysummits[0])/(self.xsummits[2]-self.xsummits[0]))
           pbd=((self.ysummits[3]-self.ysummits[1])/(self.xsummits[3]-self.xsummits[1]))
           pcd=((self.ysummits[3]-self.ysummits[2])/(self.xsummits[3]-self.xsummits[2]))

           for i in range(0,x.shape[0]):
                   for j in range(0,y.shape[1]):

                       #cas 1 en dehors de la grande zone
                       xp=x[i,j];yp=y[i,j]
                       if xp>xmax or xp<xmin or yp>ymax or yp<ymin:
                           # print(i,j)
                           continue
                       if self.ysummits[1]>self.ysummits[0]:
                           # print(i,j)
                           if xp>self.xsummits[0] and xp<self.xsummits[1]:
                               yhaut=self.ysummits[0]+pab*(xp-self.xsummits[0])
                               ybas=self.ysummits[0]+pac*(xp-self.xsummits[0])
                               if yp<=yhaut and yp>=ybas:mask[i,j]=1
                               else:continue
                           elif xp>self.xsummits[1] and xp<self.xsummits[2]:
                               # print(i,j)
                               yhaut=self.ysummits[1]+pbd*(xp-self.xsummits[1])
                               ybas=self.ysummits[0]+pac*(xp-self.xsummits[0])
                               if yp<=yhaut and yp>=ybas:mask[i,j]=1
                               else:continue
                           else:
                               ybas=self.ysummits[2]+pcd*(xp-self.xsummits[2])
                               yhaut=self.ysummits[1]+pbd*(xp-self.xsummits[1])
                               if yp<=yhaut and yp>=ybas:mask[i,j]=1
                               else:continue
                       else:
                           # if i==20:print(i,j)
                           if xp>self.xsummits[0] and xp<self.xsummits[1]:
                               # print('Hajmo')
                               ybas=self.ysummits[0]+pab*(xp-self.xsummits[0])
                               yhaut=self.ysummits[0]+pac*(xp-self.xsummits[0])
                               if yp<=yhaut and yp>=ybas:mask[i,j]=1
                               else:continue
                           elif xp>self.xsummits[1] and xp<self.xsummits[2]:
                               # print(i,j)
                               ybas=self.ysummits[1]+pbd*(xp-self.xsummits[1])
                               yhaut=self.ysummits[0]+pac*(xp-self.xsummits[0])
                               if yp<=yhaut and yp>=ybas:mask[i,j]=1
                               else:continue
                           elif xp>self.xsummits[2] and xp<self.xsummits[3] :
                               # print('Hajde')
                               yhaut=self.ysummits[2]+pcd*(xp-self.xsummits[2])
                               ybas=self.ysummits[1]+pbd*(xp-self.xsummits[1])
                               if yp<=yhaut and yp>=ybas:mask[i,j]=1;#print(i,j)
                               else:continue
       else:
           mask=((x>=xmin)&(x<=xmax))&((y>=ymin)&(y<=ymax))
       mask=mask==1
       return(mask)


    "Séléction des données entre les deux dates pour le masque rectangulaire"

    def select_MARdata(self):
         """
         Input : var:nom de la variable hydro MAR (string)
                 date_debut:date initiale (vecteur[heure,jour,mois,année]
                 date_fin:idem pour date finale
                 directory:répertoire avec simus MAR (en fonction du GCM/scénario)
                 mask: masque spatiale(matrice de 0 et 1 de la zone d'intéret)
         Description : Sélectionne la variable hydro MAR, pour les pixels du masque.
         Retourne une matrice 2D avec toutes les valeurs MAR pour tous les pas de temps
         exemple: 5 pas de temps et 100 pixels , output = matrice de dimensions(100,5)
         """

         varnames=['MBRR','MBSF','MBRO1','MBRO2','MBRO3','MBRO4',
                  'MBRO5','MBRO6','MBCC','MBEP','MBET','MBSL','MBSC','MBM','MBSN']
         var=self.var
         mask=self.mask_rectangles()
         for i in range(0,np.size(varnames)):
             if var==varnames[i]:var_index=i
         var_subpixel_cover="FRV"
         covers=xr.open_dataset(glob.glob(self.directory+"*1986**nc*")[0])
         covers=np.transpose(np.array(covers[var_subpixel_cover]))/100.
         if self.date_debut.year==self.date_fin.year:
             year=self.date_debut.hour;day=self.date_debut.day;month=self.month
             fn = glob.glob(self.directory+"*"+str(year)+"**nc*")
             ds=xr.open_dataset(fn[0])
             JJ=ct.date2JJ(day, month, year)
             MAR_time_step=np.transpose(np.array(ds['MBRR'])).shape[2]
             if ct.isbis(year)==1:ndays=366
             else:ndays=365
             MAR_time_step=float(MAR_time_step)/ndays
             MAR_time_step_hours=(MAR_time_step*24)
             if MAR_time_step==1.:
                 indice_debut=JJ-1
                 indice_fin=ct.date2JJ(self.date_fin.day,month,year)-1
             else:
                 indice_debut=JJ*(int(24/MAR_time_step_hours))-1+(int(self.date_debut[0]\
                             /MAR_time_step_hours))
                 indice_fin=ct.date2JJ(self.date_fin.day,month,year)*\
                           (int(24/MAR_time_step_hours))-1+(int(self.date_fin.hour\
                           /MAR_time_step_hours))-1
             if var_index>1:
                values1=np.transpose(np.array(ds[var]))[:,:,0,indice_debut:indice_fin+1]
                values2=np.transpose(np.array(ds[var]))[:,:,1,indice_debut:indice_fin+1]
                values3=np.transpose(np.array(ds[var]))[:,:,2,indice_debut:indice_fin+1]
                for j in range(0,np.shape(values1)[2]):
                    # print(j,np.shape(values1))
                    values1[:,:,j]=values1[:,:,j]*covers[:,:,0]
                    values2[:,:,j]=values2[:,:,j]*covers[:,:,1]
                    values3[:,:,j]=values3[:,:,j]*covers[:,:,2]
                values=values1+values2+values3
             else:
                values=np.transpose(np.array(ds[var]))[:,:,indice_debut:indice_fin+1]
             values=values[mask]
         else:
             year=self.date_debut.year;day=self.date_debut.day;month=self.date_debut.month;hour=self.date_debut.hour
             fn = glob.glob(self.directory+"*"+str(year)+"**nc*")
             ds=xr.open_dataset(fn[0])
             JJ=ct.date2JJ(day, month, year)
             MAR_time_step=np.transpose(np.array(ds['MBRR'])).shape[2]
             if ct.isbis(year)==1:ndays=366
             else:ndays=365
             MAR_time_step=float(MAR_time_step)/ndays
             MAR_time_step_hours=(MAR_time_step*24)
             if MAR_time_step==1.:
                 indice_debut=JJ-1
                 indice_fin=ct.date2JJ(self.date_fin.day,month,year)-1
             else:
                 indice_debut=JJ*(int(24/MAR_time_step_hours))-1+(int(hour\
                             /MAR_time_step_hours))
                 indice_fin=ct.date2JJ(self.date_fin.day,month,year)*\
                           (int(24/MAR_time_step_hours))-1+(int(self.date_fin.hour\
                           /MAR_time_step_hours))-1
             if var_index>1:
                    values1=np.transpose(np.array(ds[var]))[:,:,0,indice_debut:]
                    values2=np.transpose(np.array(ds[var]))[:,:,1,indice_debut:]
                    values3=np.transpose(np.array(ds[var]))[:,:,2,indice_debut:]
                    for j in range(0,np.shape(values1)[2]):
                        # print(j,np.shape(values1))
                        values1[:,:,j]=values1[:,:,j]*covers[:,:,0]
                        values2[:,:,j]=values2[:,:,j]*covers[:,:,1]
                        values3[:,:,j]=values3[:,:,j]*covers[:,:,2]
                    values=values1+values2+values3
                    values=values[mask]
                    for y in range(year+1,self.date_fin.year+1):
                        if y<self.date_fin.year:
                            fn = glob.glob(self.directory+"*"+str(y)+"**nc*")
                            ds=xr.open_dataset(fn[0])
                            values1=np.transpose(np.array(ds[var]))[:,:,0,:]
                            values2=np.transpose(np.array(ds[var]))[:,:,1,:]
                            values3=np.transpose(np.array(ds[var]))[:,:,2,:]
                            for j in range(0,np.shape(values1)[2]):
                                # print(j,np.shape(values1))
                                values1[:,:,j]=values1[:,:,j]*covers[:,:,0]
                                values2[:,:,j]=values2[:,:,j]*covers[:,:,1]
                                values3[:,:,j]=values3[:,:,j]*covers[:,:,2]
                            values=np.append(values,(values1+values2+values3)[mask],axis=1)
                        else:
                            fn = glob.glob(self.directory+"*"+str(y)+"**nc*")
                            ds=xr.open_dataset(fn[0])
                            values1=np.transpose(np.array(ds[var]))[:,:,0,:indice_fin+1]
                            values2=np.transpose(np.array(ds[var]))[:,:,1,:indice_fin+1]
                            values3=np.transpose(np.array(ds[var]))[:,:,2,:indice_fin+1]
                            for j in range(0,np.shape(values1)[2]):
                                # print(j,np.shape(values1))
                                values1[:,:,j]=values1[:,:,j]*covers[:,:,0]
                                values2[:,:,j]=values2[:,:,j]*covers[:,:,1]
                                values3[:,:,j]=values3[:,:,j]*covers[:,:,2]
                            values=np.append(values,(values1+values2+values3)[mask],axis=1)
             else:
                 print(mask)
                 values=np.transpose(np.array(ds[var]))[:,:,indice_debut:][mask]
                 for y in range(year+1,self.date_fin.year+1):
                     if y<self.date_fin.year:
                         values=np.append(values,
                                          np.transpose(np.array(ds[var]))[:,:,:][mask],
                                          axis=1)
                     else:
                         values=np.append(values,
                                          np.transpose(np.array(ds[var]))[:,:,:indice_fin+1][mask],
                                          axis=1)
         return(values)

    "Definition of the mar time-step"
    "A modifier par la suite si le pas temporel du MAR est inférieur à l'heure"

    def find_timestep(self):
        """
        Routine qui trouve le time step de MAR en heures
        """
        year=self.date_debut.year
        fn = glob.glob(self.directory+"*"+str(year)+"**nc*")
        ds=xr.open_dataset(fn[0])
        vec_out=['','']
        MAR_time_step=np.transpose(np.array(ds['MBRR'])).shape[2]
        if ct.isbis(year)==1:ndays=366
        else:ndays=365
        MAR_time_step=MAR_time_step/ndays
        MAR_time_step_hours=24*MAR_time_step
        if MAR_time_step_hours<1:vec_out[1]='mins';vec_out[0]=str(int(MAR_time_step_hours*60))
        else:vec_out[1]='hours';vec_out[0]=str(int(MAR_time_step_hours))
        return(vec_out)

    def make_time(self):
         """
         formatte une matrice avec la date pour chaque pas de temps en heure,jour,mois,année
         à redévelopper si pas de temps inférieurs à l'heure
         """
         time_step=self.find_timestep()
         if time_step[1]=='hours':
             time_step=int(time_step[0])
             date=np.array([self.date_debut])
             end_month=[31,28,31,30,31,30,31,31,30,31,30,31]
             i=0
             datec=np.array(self.date_debut)
             # print(datec,date_fin)
             while ((self.date_fin[0] != datec[0]) or (self.date_fin[1] != datec[1]) \
                    or (self.date_fin[2] != datec[2]) or (self.date_fin[3] != datec[3])):
                 print(datec)
                 if i!=0:datec=date[i,:]
                 print(i)
                 new_hour=datec[0]+time_step
                 print(new_hour)
                 if new_hour>=24.:new_day=datec[1]+1;new_hour=new_hour-24
                 else:new_day=datec[1]
                 if datec[2]==2.:
                     if ct.isbis(datec[3]):end_month[1]=29
                     else:end_month[1]=28
                 if new_day>end_month[int(datec[2])-1]:
                     new_month=datec[2]+1
                     new_day=1
                     if new_month>12:
                         new_year=datec[3]+1
                         new_month=1
                 else:new_month=datec[2];new_year=datec[3]
                 new_vec=np.array([[new_hour,new_day,new_month,new_year]])
                 date=np.append(date,new_vec,axis=0)
                 datec=np.array([new_hour,new_day,new_month,new_year])
                 i=i+1
             date=np.append(date,np.array([self.date_fin]),axis=0)
         return(date)

    "Calcul des sommets des pixels MAR"

    def MAR_summits(self):
        """
        utilise les longitudes et latitudes des centres des pixels MAR
        pour calculer les coordonnées des sommets des pixels en Lambert 72
        outputs: deux matrices contenant pour chaque pixels les 4 coordonnées des 4 sommets

        """
        summits_lon=np.zeros([self.lons.shape[0],self.lons.shape[1],4])
        summits_lat=np.zeros([self.lons.shape[0],self.lons.shape[1],4])
        summits_x=np.zeros([self.lons.shape[0],self.lons.shape[1],4])
        summits_y=np.zeros([self.lons.shape[0],self.lons.shape[1],4])
        for i in range(1,self.lons.shape[0]-1):
            for j in range(1,self.lons.shape[1]-1):
                summits_lon[i,j,0]=(self.lons[i,j]+self.lons[i-1,j]+self.lons[i-1,j-1]+self.lons[i,j-1])/4
                summits_lon[i,j,1]=(self.lons[i,j]+self.lons[i-1,j]+self.lons[i-1,j+1]+self.lons[i,j+1])/4
                summits_lon[i,j,2]=(self.lons[i,j]+self.lons[i,j+1]+self.lons[i+1,j]+self.lons[i+1,j+1])/4
                summits_lon[i,j,3]=(self.lons[i,j]+self.lons[i,j-1]+self.lons[i+1,j-1]+self.lons[i+1,j])/4
                summits_lat[i,j,0]=(self.lats[i,j]+self.lats[i-1,j]+self.lats[i-1,j-1]+self.lats[i,j-1])/4
                summits_lat[i,j,1]=(self.lats[i,j]+self.lats[i-1,j]+self.lats[i-1,j+1]+self.lats[i,j+1])/4
                summits_lat[i,j,2]=(self.lats[i,j]+self.lats[i,j+1]+self.lats[i+1,j]+self.lats[i+1,j+1])/4
                summits_lat[i,j,3]=(self.lats[i,j]+self.lats[i,j-1]+self.lats[i+1,j-1]+self.lats[i+1,j])/4
        summits_x,summits_y=self.Lb72(summits_lon,summits_lat)
        return(summits_x,summits_y)

    "Sortie shapefile"

    def MAR_shapefile(self,name,dirout1):
        """
        cette routine sort les piwels MAR au format shapefile le nom donné
        dans le sous-dossier GRID

        """
        MASK=self.mask_rectangles()
        sommets_x,sommets_y=self.MAR_summits()
        xs=np.array([sommets_x[:,:,0][MASK]])
        ys=np.array([sommets_y[:,:,0][MASK]])
        for i in range(1,4):
            xs=np.append(xs,np.array([sommets_x[:,:,i][MASK]]),axis=0)
            ys=np.append(ys,np.array([sommets_y[:,:,i][MASK]]),axis=0)
        xs=np.transpose(xs);ys=np.transpose(ys)
        newdata = gpd.GeoDataFrame()
        newdata['geometry'] = None
        for i in range(0,xs.shape[0]):
            coordinates=[(xs[i,0],ys[i,0]),(xs[i,1],ys[i,1]),
                         (xs[i,2],ys[i,2]),(xs[i,3],ys[i,3])]
            poly = Polygon(coordinates)
            newdata.loc[i, 'geometry'] = poly
            newdata.loc[i, 'polyID'] = str(i+1)
        newdata.crs = from_epsg(31370)
        print(newdata.crs)
        if os.path.exists(dirout1+'GRID/')==False:os.mkdir(dirout1+'GRID/')
        outfp=dirout1+'GRID/'+name
        newdata.to_file(outfp)

    "sortie fichiers textes"

    def MAR_TextOutputs(self,dirout1):
        """
        sortie au format texte
        1 fichier par polygone
        nom du fichier = ID du polygone.rain
        """
        time_step=self.find_timestep()
        vec_data=self.select_MARdata()
        date_debut=self.date_debut

        if os.path.exists(dirout1+'DATA/')==False:os.mkdir(dirout1+'DATA/')
        date_debut=self.date_debut
        if time_step[1]=='hours': MAR_timestep=datetime.timedelta(hours=int(time_step[0]))
        elif time_step[1]=='minutes': MAR_timestep=datetime.timedelta(minutes=int(time_step[0]))

        print(vec_data.shape)
        for i in range(0,vec_data.shape[0]):
            filename=str(i+1)+'.rain'
            f=open(dirout1+"DATA/"+filename,'w')
            print(f)
            date_move=date_debut
            for j in range(0,vec_data.shape[1]):

                if j!=0:date_move=date_move+MAR_timestep
                lines=[str(date_move.day),str(date_move.month),str(date_move.year),
                      str(date_move.hour),str(date_move.minute),str(date_move.second),
                      "{:.3f}".format(vec_data[i,j])]
                line=""
                for k in range(0,np.size(lines)):
                    line=line+lines[k]+" "
                f.write(line)
                f.write('\n')
            f.close()


"Test de l'objet"

if __name__ == "__main__":
    dir_ds="/phypc11_tmp3/MARv3.12-EUa-ERA5-7.5km/" #dossier avec sortie MAR au format Netcdf
    dirout="/srv7_tmp1/jbrajkovic/These/forWOLF/" #dossier outputs
    filenameshp="essai_shapefile.shp" #nom du shapefile en sortie
    var='MBRO3' #nom de la variable MAR

    "dates entre lesquels sélectionner les données (Heures,jour,mois,annee"
    "code à retravailler si simulations futures avec pas de temps inférieur à l'heure"

    date_debut1=datetime.datetime(1982,2,11,0)
    date_fin1=datetime.datetime(1983,2,14,0)

    "Définition d'un rectangle"

    xs=[214483.7080517296,214483.7080517296,
        279889.2010234059,279889.2010234059]
    ys=[121177.71725134458,173365.95575146656,
        173365.95575146656,121177.71725134458]


    objet_MAR=MAR_input_data(xs,ys,date_debut1,date_fin1,dir_ds,'MBRO3')


    objet_MAR.MAR_shapefile(filenameshp,dirout)
    objet_MAR.MAR_TextOutputs(dirout)

    "Tests outputs"

    MBRO3_mask=objet_MAR.select_MARdata()[:,0]
    MSK=objet_MAR.mask_rectangles()
    fig=plt.figure(figsize=(6,6))
    ax=plt.subplot()
    m=ct.map_belgium_zoom(ax, objet_MAR.lons, objet_MAR.lats)
    lons_w=objet_MAR.lons[MSK==True];lats_w=objet_MAR.lats[MSK]
    MBRO3=np.array(objet_MAR.lons)
    for k in range(0,np.size(MBRO3_mask)):
        for i in range(0,MBRO3.shape[0]):
            for j in range(0,MBRO3.shape[1]):
                if lons_w[k]==objet_MAR.lons[i,j] and lats_w[k]==objet_MAR.lats[i,j]:
                    MBRO3[i,j]=MBRO3_mask[k]
    vmax=np.max(MBRO3)
    MBRO3[MSK==False]=float("nan")
    x,y=m(objet_MAR.lons,objet_MAR.lats)


    bounds=ct.makebounds(MBRO3,vmax/100.)
    cmap = cm.jet
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    mapa=m.pcolormesh(x,y,MBRO3)
    cbar=m.colorbar(norm=norm,cmap=cmap,location='left',pad=0.6)
