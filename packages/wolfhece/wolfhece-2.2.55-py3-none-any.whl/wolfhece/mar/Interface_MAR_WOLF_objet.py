
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
import pandas as pd
from zipfile import ZipFile
import struct


class MAR_input_data:   
    
    def __init__(self,xsummits=np.zeros(0),ysummits=np.zeros(0),
                 date_debut=datetime.datetime(2020,7,11,5),
                 date_fin=datetime.datetime(2020,7,11,5),
                 directory='~/BUP_srv7/',
                 directory_hist_sim='~/BUP_srv7/',
                 model_name='MIROC6',
                 var='MBRR',
                 var_unb='E',
                 UnborNot=0,
                 syu=1981,eyu=2010,
                 mod_ydays=1,
                 generate_quantiles=1):
        
        
        """
        xsummits : abscisses Lambert 72 du rectangle d'extraction'
        ysummits : idem pour ordonnées
        
        date_debut : Date de début de la série temporelle extraite
        date_fin : idem pour la date de fin
        
        directory : répertoire des fichier Netcdfs annuels
        directory_hist_sim : répertoire des fichiers Netcdfs annuels de la période historique de simulation
        (pour débiaisage)
        
        var : nom de la variable MAR à extraire, si on veut l'evapotranspiration totale (toutes les composantes),il
              faut noter MBEP'
        
        var_unb : nom de la variable qui sert au débiasage dans les fichiers Netcdfs de l'IRM '
        
        UnborNot : 1 si débiaisage, 0 si données brutes
        
        syu et eyu : année de début et de fin de la période future utilisée pour comparer modèle et observations
        
        mod_ydays: 1 si modèel avec années bissextiles, 0 sinon 1
        """
        
        self.directory_hist_sim=directory_hist_sim
        self.UnborNot=UnborNot
        self.var_unb=var_unb
        self.var=var
        self.xsummits=xsummits
        self.ysummits=ysummits
        self.date_debut=date_debut
        self.date_fin=date_fin
        self.directory=directory
        self.mod_ydays=mod_ydays
        self.fn= glob.glob(self.directory+"*"+str(date_debut.year)+"**nc*")
        if 'IRM_grid' in self.fn[0]:
            print('Hajde Hajduce')
            self.fn= glob.glob(self.directory+"*MAR_grid*"+str(date_debut.year)+"**nc*")
            
        print(self.directory,date_debut.year)
        print(self.fn)
        
        self.ds=xr.open_dataset(self.fn[0])
        
        self.lons=np.transpose(np.array(self.ds.LON))
        self.lats=np.transpose(np.array(self.ds.LAT))
        
        self.Lb72=pyproj.Proj(projparams='epsg:31370')
        self.x_Lb72, self.y_Lb72 = self.Lb72(self.lons,self.lats)
        
        self.mask=self.mask_rectangles()
        
        # self.plot_mask()
        self.vec_data=self.select_MARdata()
        # self.historical_matrix=
        
        self.directory_unbiasing="/srv7_tmp1/jbrajkovic/These/IRM/"
        
        self.fn_quant_ev='/srv7_tmp1/jbrajkovic/These/Unbiasing/evapotranspiration_quantiles_1981_2010.nc'
        self.fn_quant_pr='/srv7_tmp1/jbrajkovic/These/Unbiasing/precipitation_quantiles_1981_2010.nc'
        
        self.syu=syu;self.eyu=eyu
        
        self.generate_quantiles=generate_quantiles
        self.model_name=model_name
        

    def mask_rectangles(self):
        """
        Creates the rectangular mask
        so MAR values can be extracted only for the 
        precised zone

  
        """
      
         
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
        #print(self.xsummits);print(self.ysummits)
 
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
        print(mask[mask==True].shape)
        return(mask)
    
    def plot_mask(self):
        mask1=np.zeros_like(self.mask)
        mask1[self.mask]=1
        mask1[self.mask==False]=0
        bounds=np.arange(0,1.5,.5)
        cmap=cm.Greens
        MSK=np.zeros_like(mask1)
        ct.quick_map_plot(self.lons, self.lats, mask1, bounds, cmap, MSK)
        # plt.show()
        # plt.savefig('mask.png')
        

    "Séléction des données entre les deux dates pour le masque rectangulaire"
    
    def select_MARdata(self):
         '''
         Input : var:nom de la variable hydro MAR (string)
                 date_debut:date initiale (vecteur[heure,jour,mois,année]
                 date_fin:idem pour date finale
                 directory:répertoire avec simus MAR (en fonction du GCM/scénario)
                 mask: masque spatiale(matrice de 0 et 1 de la zone d'intéret)
         Description : Sélectionne la variable hydro MAR, pour les pixels du masque.
         Retourne une matrice 2D avec toutes les valeurs MAR pour tous les pas de temps
         exemple: 5 pas de temps et 100 pixels , output = matrice de dimensions(100,5)
         '''
         
         varnames=['PRECIP_QUANTITY','E','MBRR','MBSF','MBRO1','MBRO2','MBRO3','MBRO4',
                  'MBRO5','MBRO6','MBCC','MBEP','MBET','MBSL','MBSC','MBM','MBSN']
         
         
         var=self.var
         mask=self.mask
         for i in range(0,np.size(varnames)):
             if var==varnames[i]:var_index=i   
             
         if var_index>3:
             "To take into account the occupied fraction by subpixels"
             var_subpixel_cover="FRV"
             covers=xr.open_dataset(glob.glob(self.directory+"*"+str(self.date_debut.year)+"**nc*")[0])
             covers=np.transpose(np.array(covers[var_subpixel_cover]))/100.
             covers=covers[mask]
             
             
         if self.date_debut.year==self.date_fin.year:       
             year=self.date_debut.year;day=self.date_debut.day;month=self.date_debut.month         
             fn = glob.glob(self.directory+"*"+str(year)+"**nc*")
             if 'IRM_grid' in fn[0]:
                fn = glob.glob(self.directory+"*MAR_grid*"+str(year)+"**nc*") 
             print(fn[0])
             ds=xr.open_dataset(fn[0])
             JJ=ct.date2JJ(day, month, year)
             MAR_time_step=np.transpose(np.array(ds['MBRR'])).shape[2]
             
             if ct.isbis(year)==1:ndays=366
             else:ndays=365
             MAR_time_step=float(ndays)/float(MAR_time_step)
             MAR_time_step_hours=(MAR_time_step*24)
             
             if MAR_time_step==1.:
                 indice_debut=JJ-1
                 indice_fin=ct.date2JJ(self.date_fin.day,month,year)-1
             else:
                 indice_debut=JJ*(int(24/MAR_time_step_hours))-1+(int(self.date_debut.hour\
                             /MAR_time_step_hours))
                 indice_fin=ct.date2JJ(self.date_fin.day,month,year)*\
                           (int(24/MAR_time_step_hours))+(int(self.date_fin.hour\
                           /MAR_time_step_hours))-1
            
            
             if var_index>3:
                 if var=='MBEP':
                     
                    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                    "**************Attention***************"
                    "Definition evapotranspiration dans MAR"
                    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" 
                    
                    values1=(np.transpose(np.array(ds[var]))[:,:,0,indice_debut:indice_fin+1])[mask] +\
                            (np.transpose(np.array(ds['MBET']))[:,:,0,indice_debut:indice_fin+1])[mask]+\
                            (np.transpose(np.array(ds['MBSL']))[:,:,0,indice_debut:indice_fin+1])[mask]
                    values2=(np.transpose(np.array(ds[var]))[:,:,1,indice_debut:indice_fin+1])[mask]+\
                            (np.transpose(np.array(ds['MBET']))[:,:,1,indice_debut:indice_fin+1])[mask]+\
                            (np.transpose(np.array(ds['MBSL']))[:,:,1,indice_debut:indice_fin+1])[mask]
                            
                    values3=(np.transpose(np.array(ds[var]))[:,:,2,indice_debut:indice_fin+1])[mask] +\
                            (np.transpose(np.array(ds['MBET']))[:,:,2,indice_debut:indice_fin+1])[mask]+\
                            (np.transpose(np.array(ds['MBSL']))[:,:,2,indice_debut:indice_fin+1])[mask]
                            
                    for j in range(np.shape(values1)[2]):
                       
                        values1[:,:,j]=values1[:,:,j]*covers[:,:,0]
                        values2[:,:,j]=values2[:,:,j]*covers[:,:,1]
                        values3[:,:,j]=values3[:,:,j]*covers[:,:,2]
                    values=values1+values2+values3
                 else:
                    values1=np.transpose(np.array(ds[var]))[:,:,0,indice_debut:indice_fin+1][mask]        
                    values2=np.transpose(np.array(ds[var]))[:,:,1,indice_debut:indice_fin+1][mask]
                    values3=np.transpose(np.array(ds[var]))[:,:,2,indice_debut:indice_fin+1] [mask]
                    for j in range(np.shape(values1)[2]):
                        
                        values1[:,j]=values1[:,j]*covers[:,0]
                        values2[:,j]=values2[:,j]*covers[:,1]
                        values3[:,j]=values3[:,j]*covers[:,2]
                    values=values1+values2+values3
              
                    
             else:
                values=np.transpose(np.array(ds[var]))[:,:,indice_debut:indice_fin+1][mask]
         
         else:
             year=self.date_debut.year;day=self.date_debut.day;month=self.date_debut.month;hour=self.date_debut.hour  
             print(year,month,day,hour)
             print(self.date_fin)
             fn = glob.glob(self.directory+"*"+str(year)+"**nc*")
             if 'IRM_grid' in fn[0]:
                fn = glob.glob(self.directory+"*MAR_grid*"+str(year)+"**nc*") 
             ds=xr.open_dataset(fn[0])
             JJ=ct.date2JJ(day, month, year,type_mod=self.mod_ydays)
             
             MAR_time_step=np.transpose(np.array(ds[self.var])).shape[-1]
             if self.mod_ydays==1:
                 if ct.isbis(year)==1:ndays=366
                 else:ndays=365
             else:
                 ndays=365
             MAR_time_step=ndays/float(MAR_time_step)
             MAR_time_step_hours=(MAR_time_step*24)
             
             if MAR_time_step==1.:
                 indice_debut=JJ-1
                 indice_fin=ct.date2JJ(self.date_fin.day,self.date_fin.month,self.date_fin.year,type_mod=self.mod_ydays)
             else:
                 indice_debut=(JJ-1)*(int(24/MAR_time_step_hours))+(int(hour\
                             /MAR_time_step_hours))
                 indice_fin=(ct.date2JJ(self.date_fin.day,self.date_fin.month,self.date_fin.year,type_mod=self.mod_ydays)-1)*\
                           (int(24/MAR_time_step_hours))+(int(self.date_fin.hour\
                           /MAR_time_step_hours))+1
                               
             print("indices début et fin",MAR_time_step_hours,indice_debut,indice_fin)                   
                               
             if var_index>3:
                    if var=='MBEP':
                        
                       "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                       "**************Attention***************"
                       "Definition evapotranspiration dans MAR"
                       "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" 
                       
                       values1=(np.transpose(np.array(ds[var]))[:,:,0,indice_debut:])[mask] +\
                               (np.transpose(np.array(ds['MBET']))[:,:,0,indice_debut:])[mask]+\
                               (np.transpose(np.array(ds['MBSL']))[:,:,0,indice_debut:])[mask]
                       values2=(np.transpose(np.array(ds[var]))[:,:,1,indice_debut:])[mask]+\
                               (np.transpose(np.array(ds['MBET']))[:,:,1,indice_debut:])[mask]+\
                               (np.transpose(np.array(ds['MBSL']))[:,:,1,indice_debut:])[mask]
                       values3=(np.transpose(np.array(ds[var]))[:,:,2,indice_debut:])[mask] +\
                               (np.transpose(np.array(ds['MBET']))[:,:,2,indice_debut:])[mask]+\
                               (np.transpose(np.array(ds['MBSL']))[:,:,2,indice_debut:])[mask]
                               
                       for j in range(np.shape(values1)[-1]):
                          
                           values1[:,j]=values1[:,j]*covers[:,0]
                           values2[:,j]=values2[:,j]*covers[:,1]
                           values3[:,j]=values3[:,j]*covers[:,2]
                       values=(values1+values2+values3)
                 
   
                       for y in range(year+1,self.date_fin.year+1):
                           print(y)
                           if y<self.date_fin.year:
                            fn = glob.glob(self.directory+"*"+str(y)+"**nc*")
                            if 'IRM_grid' in fn[0]:
                               fn = glob.glob(self.directory+"*MAR_grid*"+str(year)+"**nc*") 
                            ds=xr.open_dataset(fn[0])
                            values1=(np.transpose(np.array(ds[var]))[:,:,0,:])[mask]+\
                                    (np.transpose(np.array(ds['MBET']))[:,:,0,:])[mask]+\
                                    (np.transpose(np.array(ds['MBSL']))[:,:,0,:])[mask]
                            
                            values2=(np.transpose(np.array(ds[var]))[:,:,1,:])[mask]+\
                                    (np.transpose(np.array(ds['MBET']))[:,:,1,:])[mask]+\
                                    (np.transpose(np.array(ds['MBSL']))[:,:,1,:])[mask]
                                    
                            values3=(np.transpose(np.array(ds[var]))[:,:,2,:])[mask]+\
                                    (np.transpose(np.array(ds['MBET']))[:,:,2,:])[mask]+\
                                    (np.transpose(np.array(ds['MBSL']))[:,:,2,:])[mask]
                                    
                            for j in range(0,np.shape(values1)[-1]):
                                
                                # print(j,np.shape(values1))
                                values1[:,j]=values1[:,j]*covers[:,0]
                                values2[:,j]=values2[:,j]*covers[:,1]
                                values3[:,j]=values3[:,j]*covers[:,2]
                            values=np.append(values,(values1+values2+values3),axis=1)
                           else:
                            fn = glob.glob(self.directory+"*"+str(y)+"**nc*")
                            if 'IRM_grid' in fn[0]:
                               fn = glob.glob(self.directory+"*MAR_grid*"+str(year)+"**nc*") 
                            ds=xr.open_dataset(fn[0])
                            values1=(np.transpose(np.array(ds[var]))[:,:,0,:indice_fin])[mask] +\
                                    (np.transpose(np.array(ds['MBET']))[:,:,0,:indice_fin])[mask]+\
                                    (np.transpose(np.array(ds['MBSL']))[:,:,0,:indice_fin])[mask]         
                            values2=(np.transpose(np.array(ds[var]))[:,:,1,:indice_fin])[mask]+\
                                    (np.transpose(np.array(ds['MBET']))[:,:,1,:indice_fin])[mask]+\
                                    (np.transpose(np.array(ds['MBSL']))[:,:,1,:indice_fin])[mask] 
                            values3=(np.transpose(np.array(ds[var]))[:,:,2,:indice_fin])[mask]+\
                                    (np.transpose(np.array(ds['MBET']))[:,:,2,:indice_fin])[mask]+\
                                    (np.transpose(np.array(ds['MBSL']))[:,:,2,:indice_fin])[mask]
                                    
                            for j in range(0,np.shape(values1)[-1]):
                                # print(j,np.shape(values1))
                                values1[:,j]=values1[:,j]*covers[:,0]
                                values2[:,j]=values2[:,j]*covers[:,1]
                                values3[:,j]=values3[:,j]*covers[:,2]
                            values=np.append(values,(values1+values2+values3),axis=1)
                    else:
                        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                        "**************Attention***************"
                        "Definition evapotranspiration dans MAR"
                        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" 
                        
                        values1=np.transpose(np.array(ds[var]))[:,:,0,indice_debut:][mask]
                        values2=np.transpose(np.array(ds[var]))[:,:,1,indice_debut:][mask]
                        values3=np.transpose(np.array(ds[var]))[:,:,2,indice_debut:][mask]
                                
                        for j in range(np.shape(values1)[-1]):
                           
                            values1[:,j]=values1[:,j]*covers[:,0]
                            values2[:,j]=values2[:,j]*covers[:,1]
                            values3[:,j]=values3[:,j]*covers[:,2]
                        values=(values1+values2+values3)
                  
                        print(self.var,values.shape)
                        for y in range(year+1,self.date_fin.year+1):
                            print(y)
                            if y<self.date_fin.year:
                             fn = glob.glob(self.directory+"*"+str(y)+"**nc*")
                             if 'IRM_grid' in fn[0]:
                                fn = glob.glob(self.directory+"*MAR_grid*"+str(year)+"**nc*") 
                             ds=xr.open_dataset(fn[0])
                             values1=np.transpose(np.array(ds[var]))[:,:,0,:][mask]
                             values2=np.transpose(np.array(ds[var]))[:,:,1,:][mask]      
                             values3=np.transpose(np.array(ds[var]))[:,:,2,:][mask]
                             for j in range(np.shape(values1)[-1]):
                                 
                                 # print(j,np.shape(values1))
                                 # print(values1.shape,covers.shape)
                                 values1[:,j]=values1[:,j]*covers[:,0]
                                 values2[:,j]=values2[:,j]*covers[:,1]
                                 values3[:,j]=values3[:,j]*covers[:,2]
                             values=np.append(values,(values1+values2+values3),axis=1)
                             print(self.var,values.shape)
                            else:
                             fn = glob.glob(self.directory+"*"+str(y)+"**nc*")
                             if 'IRM_grid' in fn[0]:
                                fn = glob.glob(self.directory+"*MAR_grid*"+str(year)+"**nc*") 
                             ds=xr.open_dataset(fn[0])
                             values1=np.transpose(np.array(ds[var]))[:,:,0,:indice_fin][mask]     
                             values2=np.transpose(np.array(ds[var]))[:,:,1,:indice_fin][mask]
                             values3=np.transpose(np.array(ds[var]))[:,:,2,:indice_fin][mask]
                             print(np.shape(values1)[-1])
                             for j in range(np.shape(values1)[-1]):
                                 # print(j,np.shape(values1))
                                 values1[:,j]=values1[:,j]*covers[:,0]
                                 values2[:,j]=values2[:,j]*covers[:,1]
                                 values3[:,j]=values3[:,j]*covers[:,2]
                             values=np.append(values,(values1+values2+values3),axis=1)
                             print(self.var,values.shape)
                             
                            
             else:
                 #print(mask)
                 
                 values=np.transpose(np.array(ds[var]))[:,:,indice_debut:][mask]
                 print(self.var,values.shape)
                 for y in range(year+1,self.date_fin.year+1):
                      
                     fn = glob.glob(self.directory+"*"+str(y)+"**nc*")
                     if 'IRM_grid' in fn[0]:
                       fn = glob.glob(self.directory+"*MAR_grid*"+str(year)+"**nc*") 
                     ds=xr.open_dataset(fn[0])
                     print(y)
                     if y<self.date_fin.year:
                         values=np.append(values,
                                          np.transpose(np.array(ds[var]))[:,:,:][mask],
                                          axis=1)
                     else: 
                         values=np.append(values,
                                          np.transpose(np.array(ds[var]))[:,:,:indice_fin][mask],
                                          axis=1)
                     print(self.var,values.shape)
                        
                         
         return(values)
     
    "Definition of the mar time-step"
    "A modifier par la suite si le pas temporel du MAR est inférieur à l'heure"
    
    def MAR_unbiasing(self):
        th_drizzle=.1
        print("letsgo")
        
        "**********************************************************"
        "Lecture des données sur la période historiqe de simulation"
        "**********************************************************"
        if self.generate_quantiles==1:
            historical_matrix_unbias=MAR_input_data(xsummits=self.xsummits, ysummits=self.ysummits,
                                            date_debut=datetime.datetime(1981,1,1,0),
                                             date_fin=datetime.datetime(2010,12,31,23),
                                             directory=self.directory_unbiasing, var=self.var_unb).vec_data
        
        
        
        date_debutu=datetime.datetime(self.syu,1,1,0)
        date_finu=datetime.datetime(self.eyu,12,31,23)
            
        
        
        if self.var_unb=='PRECIP_QUANTITY':
            
            if self.generate_quantiles==1:
                print('on va le faire')
                historical_matrix_bias=MAR_input_data(xsummits=self.xsummits, ysummits=self.ysummits,
                                                 date_debut=datetime.datetime(1981,1,1,0),
                                                 date_fin=datetime.datetime(2010,12,31,23),
                                                 directory=self.directory, var='MBRR',mod_ydays=self.mod_ydays).vec_data+\
                                        MAR_input_data(xsummits=self.xsummits,ysummits= self.ysummits,
                                                                         date_debut=datetime.datetime(1981,1,1,0),
                                                                         date_fin=datetime.datetime(2010,12,31,23),
                                                                         directory=self.directory, var='MBSF',
                                                                         mod_ydays=self.mod_ydays).vec_data
                                        
            biased_data=MAR_input_data(xsummits=self.xsummits, ysummits=self.ysummits,
                                             date_debut=self.date_debut,
                                             date_fin=self.date_fin,
                                             directory=self.directory, var='MBRR',mod_ydays=self.mod_ydays).vec_data+\
                        MAR_input_data(xsummits=self.xsummits,ysummits= self.ysummits,
                                                        date_debut=self.date_debut,
                                                        date_fin=self.date_fin,
                                                        directory= self.directory,var= 'MBSF',mod_ydays=self.mod_ydays).vec_data
                        
            
                        
            print(self.date_debut,self.date_fin)                    
            print('biased data shape',biased_data.shape)
                                    
            
            FutUnb=MAR_input_data(xsummits=self.xsummits, ysummits=self.ysummits,
                                             date_debut=date_debutu,
                                             date_fin=date_finu,
                                                     directory=self.directory, var='MBRR',
                                                     mod_ydays=self.mod_ydays).vec_data+\
                    MAR_input_data(xsummits=self.xsummits, ysummits=self.ysummits,
                                                         date_debut=date_debutu,
                                                         date_fin=date_finu,
                                                                 directory=self.directory, var='MBSF',
                                                                 mod_ydays=self.mod_ydays).vec_data
                    

        elif self.var_unb=='E':
           if self.generate_quantiles==1: 
               historical_matrix_bias=MAR_input_data(xsummits=self.xsummits, ysummits=self.ysummits,
                                                date_debut=datetime.datetime(1981,1,1,0),
                                                date_fin=datetime.datetime(2010,12,31,23),
                                                        directory=self.directory, var='MBEP', 
                                                        mod_ydays=self.mod_ydays).vec_data
           biased_data=MAR_input_data(xsummits=self.xsummits, ysummits=self.ysummits,
                                            date_debut=self.date_debut,
                                            date_fin=self.date_fin,
                                                    directory=self.directory, var='MBEP',
                                                    mod_ydays=self.mod_ydays).vec_data
           
           FutUnb=MAR_input_data(xsummits=self.xsummits, ysummits=self.ysummits,
                                            date_debut=date_debutu,
                                            date_fin=date_finu,
                                                    directory=self.directory, var='MBEP', 
                                                    mod_ydays=self.mod_ydays).vec_data  
                        
        "****************************************************"
        "Calcul des quantiles historiques simulés et observés"
        "****************************************************"   
        
        quant_mat=np.zeros([biased_data.shape[0],101])
        quant_mat_bias=np.zeros([biased_data.shape[0],101])
        quant_coeffs=np.zeros([biased_data.shape[0],101])
        
        
        
        
        
        if self.generate_quantiles==1:
            
            historical_matrix_unbias[historical_matrix_unbias<th_drizzle]=0
            if self.find_timestep()[1]=='hours':
                tsd=24
                historical_matrix_bias_d=np.zeros([historical_matrix_bias.shape[0],
                                                   int(historical_matrix_bias.shape[1]/tsd)])
                for i in range(historical_matrix_bias_d.shape[0]):
                    for d in range(historical_matrix_bias_d.shape[1]):
                        historical_matrix_bias_d[i,d]=np.sum(historical_matrix_bias[i,d*tsd:(d+1)*tsd])
                    historical_matrix_bias_d[historical_matrix_bias_d<th_drizzle]=0
                # print(historical_matrix_unbias.shape,historical_matrix_bias_d.shape)    
                
                for i in range(historical_matrix_unbias.shape[0]):
                    
                    quant_mat_bias[i,:]=np.quantile(historical_matrix_bias_d[i,:]\
                                                    [historical_matrix_bias_d[i,:]>th_drizzle],np.arange(0,1.01,0.01))
                    quant_mat[i,:]=np.quantile(historical_matrix_unbias[i,:][historical_matrix_unbias[i,:]>th_drizzle],np.arange(0,1.01,0.01))
                    for j in range(quant_mat.shape[1]):quant_coeffs[i,j]=quant_mat[i,j]/quant_mat_bias[i,j]
                    
        else:
            if self.var_unb=='E':fn_quant=self.fn_quant_ev
            else:fn_quant=self.fn_quant_pr
            quant_mat_bias=ct.marray(xr.open_dataset(fn_quant),self.model_name)[self.mask]
            quant_mat=ct.marray(xr.open_dataset(fn_quant),'IRM')[self.mask]
            for i in range(quant_mat.shape[0]):
                for j in range(quant_mat.shape[1]):quant_coeffs[i,j]=quant_mat[i,j]/quant_mat_bias[i,j]
        # biased_data_var=np.array(self.vec_data)
 
        "******************************************"
        "****Débiaisage des données daily**********"
        "******************************************"
        
        "Future quantiles to assess value location"

        if self.find_timestep()[1]=='hours':
            tsd=24
            FutUnb_d=np.zeros([biased_data.shape[0],
                                               int(FutUnb.shape[1]/tsd)])
            for i in range(biased_data.shape[0]):
                for d in range(FutUnb_d.shape[1]):
                    FutUnb_d[i,d]=np.sum(FutUnb[i,d*tsd:(d+1)*tsd]) 
                    
            
        quant_mat_fut=np.zeros_like(quant_mat)
        for i in range(FutUnb.shape[0]):
            quant_mat_fut[i,:]=np.quantile(FutUnb_d[i,:]\
                                            [FutUnb_d[i,:]>th_drizzle],np.arange(0,1.01,0.01))
        
        
        
        print(self.find_timestep()[1])
        if self.find_timestep()[1]=='hours':
            biased_data_d=np.zeros([biased_data.shape[0],
                                      int(biased_data.shape[1]/24)+1])
            for i in range(biased_data.shape[0]):
                for d in range(biased_data_d.shape[1]):
                    biased_data_d[i,d]=np.sum(biased_data[i,d*tsd:(d+1)*tsd])
                    
        for i in range(self.vec_data.shape[0]):
            for j in range(biased_data_d.shape[1]):
                if biased_data_d[i,j]>th_drizzle:
                    for k in range(quant_mat.shape[1]):
                        if k==quant_mat.shape[1]-1:
                            if biased_data_d[i,j]>=quant_mat_fut[i,k]:
                                biased_data_d[i,j]=biased_data[i,j]*quant_coeffs[i,k]                            
                        elif k<quant_mat.shape[1]-1:
                            if biased_data_d[i,j]>=quant_mat_fut[i,k] and biased_data_d[i,j]<=quant_mat_fut[i,k+1]:
                                biased_data_d[i,j]=(quant_coeffs[i,k]*(biased_data_d[i,j]-quant_mat_fut[i,k])/\
                                    (quant_mat_fut[i,k+1]-quant_mat_fut[i,k])+quant_coeffs[i,k+1]*(quant_mat_fut[i,k+1]-biased_data_d[i,j])/\
                                        (quant_mat_fut[i,k+1]-quant_mat_fut[i,k]))*biased_data_d[i,j] 
                                break
                    
                else:
                    biased_data_d[i,j]=0
                    
                if pd.isna(biased_data_d[i,j]):
                    biased_data_d[i,j]=0.
        Unbiased_data_d=np.array(biased_data_d)
        
        "*****************************************"
        "**Redistribution au pas de temps horaire**"
        "*****************************************"
        
        ydays=biased_data_d.shape[1]
        Unbiased_data=np.zeros_like(biased_data)
        
        print ("redistributing on the daily time-step")
        if self.var_unb=='PRECIP_QUANTITY':
            
            "Si ce sont les pluies qui sont débiasées"
            "On débiaise sur tout l'événement et non pas jour après jour"
            
            for i in range(self.vec_data.shape[0]):
                # print(i)
                d=0  
                while d<ydays:
                    # if i==67:print(d,Unbiased_data_d[i,d])
                    # if d%100==0:print(d)
                    if Unbiased_data_d[i,d]<=0.1:d+=1
     
                    else:
                        
                        d1=d
                        ndays=0
                        
                        while d1<ydays and Unbiased_data_d[i,d1]>.1 :
                            d1+=1;ndays+=1
                        
                 
                        precip_sum_d=np.sum(Unbiased_data_d[i,d:d+ndays])
                        biased_sum=np.sum(biased_data\
                                           [i,d*tsd:(d+ndays)*tsd])
                        biased_hourly=(biased_data)\
                                           [i,d*tsd:(d+ndays)*tsd]
              
                        weights=biased_hourly/biased_sum
                        
                        Unbiased_data[i,d*tsd:(d+ndays)*tsd]=\
                            precip_sum_d*weights
                       
                        # print(d,PRECIP_IRM[i,j,d])
            
                        d+=ndays
        else:
            "Débiai<-sage jour après jour pour l'évapotranspiration notamment"
            for i in range(self.vec_data.shape[0]):
                # print(i)
                d=0  
                while d<ydays:
                    # if i==67:print(d,Unbiased_data_d[i,d])
                    # if d%100==0:print(d)
                    if Unbiased_data_d[i,d]<=0.1:d+=1
     
                    else:
                        

                        precip_sum_d=Unbiased_data_d[i,d]
                        biased_sum=np.sum(biased_data\
                                           [i,d*tsd:(d+1)*tsd])
                        biased_hourly=(biased_data)\
                                           [i,d*tsd:(d+1)*tsd]
              
                        weights=biased_hourly/biased_sum
                        
                        Unbiased_data[i,d*tsd:(d+1)*tsd]=\
                            precip_sum_d*weights
                       
                        # print(d,PRECIP_IRM[i,j,d])
            
                        d+=1
            
        
        if self.var=='MBRO3' or self.var=='MBRR' or self.var=='MBSF':
            # biased_data_var=np.array(self.vec_data)
            biased_data_var=self.vec_data
            
            print("biased data var shape ",biased_data_var.shape)
            print('unbiased data shape' ,Unbiased_data.shape)
            propor2var=(biased_data_var/biased_data)
            Unbiased_data=Unbiased_data*propor2var
        
        "**** 2 méthodes******"
        Unbiased_data[pd.isna(Unbiased_data)]=0.
        return(Unbiased_data)
        
    
    def find_timestep(self):
        """
        Routine qui trouve le time step de MAR en heures
        """    
        year=self.date_debut.year
        fn = glob.glob(self.directory+"*"+str(year)+"**nc*")
        ds=xr.open_dataset(fn[0])
        vec_out=['','']
        MAR_time_step=np.transpose(np.array(ds['MBRR'])).shape[2]
        if self.mod_ydays==1:
            if ct.isbis(year)==1:ndays=366
            else:ndays=365 
        else:
            ndays=365
            
        MAR_time_step=ndays/MAR_time_step
        MAR_time_step_hours=24*MAR_time_step
        if MAR_time_step_hours<1:vec_out[1]='minutes';vec_out[0]=str(int(MAR_time_step_hours*60))
        else:vec_out[1]='hours';vec_out[0]=str(int(MAR_time_step_hours))
        # print(vec_out)
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
                 #print(datec)
                 if i!=0:datec=date[i,:]
                 #print(i)
                 new_hour=datec[0]+time_step
                 #print(new_hour)
                 if new_hour>=24.:new_day=datec[1]+1;new_hour=new_hour-24
                 else:new_day=datec[1]
                 if datec[2]==2.:
                     if self.mod_ydays==1:
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
        cette routine sort les pixels MAR au format shapefile le nom donné
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
        newdata.crss=from_epsg(31370)
        #(newdata.crs).to_byte(byteorder='little'))
        if os.path.exists(dirout1)==False:os.mkdir(dirout1)
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
        if not self.UnborNot:vec_data=self.vec_data
        else:vec_data=self.MAR_unbiasing()
        
        date_debut=self.date_debut

        if os.path.exists(dirout1+'DATA/')==False:os.mkdir(dirout1+'DATA/')
        date_debut=self.date_debut
        if time_step[1]=='hours': MAR_timestep=datetime.timedelta(hours=int(time_step[0]))
        elif time_step[1]=='minutes': MAR_timestep=datetime.timedelta(minutes=int(time_step[0]))

        for i in range(0,vec_data.shape[0]):
            filename=str(i+1)+'.rain'
            f=open(dirout1+"DATA/"+filename,'w')
            date_move=date_debut
            for j in range(0,vec_data.shape[1]):
                
                if j!=0:date_move=date_move+MAR_timestep
                lines=[str(date_move.day),str(date_move.month),str(date_move.year),
                      str(date_move.hour),str(date_move.minute),str(date_move.second),
                      "{:.3f}".format(vec_data[i,j])]
                line=""
                for k in range(0,np.size(lines)):
                    line=line+lines[k]+"\t"

                f.write(line)
                f.write('\n')
            f.close()  
    def MAR_BinaryOutputs(self,dirout1):
        """
        sortie au format texte
        1 fichier par polygone
        nom du fichier = ID du polygone.rain
        """       
        time_step=self.find_timestep()
        if not self.UnborNot:vec_data=self.vec_data
        else:vec_data=self.MAR_unbiasing()
        date_debut=self.date_debut
        if os.path.exists(dirout1)==False:os.mkdir(dirout1)
        if os.path.exists(dirout1+'DATA/')==False:os.mkdir(dirout1+'DATA/')
        date_debut=self.date_debut
        if time_step[1]=='hours': MAR_timestep=datetime.timedelta(hours=int(time_step[0]))
        elif time_step[1]=='minutes': MAR_timestep=datetime.timedelta(minutes=int(time_step[0]))

        for i in range(0,vec_data.shape[0]):
            filename=str(i+1)+'.rain'
            f=open(dirout1+"DATA/"+filename,'wb')

            date_move=date_debut   

            for j in range(0,vec_data.shape[1]):
                
                if j!=0:date_move=date_move+MAR_timestep
                dayb=date_move.day.to_bytes(1,byteorder='little',signed=False)
                monthb=date_move.month.to_bytes(1,byteorder='little',signed=False)    
                yearb=date_move.year.to_bytes(2,byteorder='little',signed=False)
                hourb=date_move.hour.to_bytes(1,byteorder='little',signed=False)
                minuteb=date_move.minute.to_bytes(1,byteorder='little',signed=False)                
                secondb=date_move.second.to_bytes(1,byteorder='little',signed=False)
                valb=bytearray(struct.pack("f", round(vec_data[i,j],3)))# .to_bytes(1,byteorder='little',signed=False)
                f.write(dayb);f.write(monthb);f.write(yearb);f.write(hourb)
                f.write(minuteb);f.write(secondb);f.write(valb)
                # print(struct.unpack('f',valb),date_move.day)
        
"Test de l'objet"

if __name__ == "__main__":
  
    dir_ds='/phypc11_tmp3/MARv3.14/MARv3.14-EUi-MIROC6-5km-ssp585/'
    dir_hist='/phypc11_tmp3/MARv3.14/MARv3.14-EUi-MIROC6-5km-ssp585/'
    
    dir_stock='/srv1_tmp6/fettweis/MARv3.14/'
    dir_ins=['MARv3.14-EUh-MPI-ESM1-2-HR-5km-',
    'MARv3.14-EUi-MIROC6-5km-',
    'MARv3.14-EUm-EC-Earth3-Veg-5km-',
    'MARv3.14-EUk-NorESM2-MM-5km-',
    'MARv3.14-EUq-CMCC-CM2-SR5-5km-',
    'MARv3.14-EUl-IPSL-CM6A-LR-5km-'
    
              ]
    
    mod_names=['MPI-ESM1',
               'MIROC6',
               'EC3',
               'NorESM2',
               'CMCC-CM2-SR5',
               'IPSL'
               ]
    
    mod_racs=['MPI','MIR','EC3','NOR','CMC','IPSL']
    
    scens=['ssp126','ssp245','ssp370','ssp585']


    dirout="/srv7_tmp1/jbrajkovic/These/forWOLF/evapo"#-MPI_1981-2010/" #dossier outputs
    filenameshp="grid.shp" #nom du shapefile en sortie
    
    
    "dates entre lesquelles sélectionner les données (Heures,jour,mois,annee"
    "code à retravailler si simulations futures avec pas de temps inférieur à l'heure"
    
    date_debut1=datetime.datetime(1981,1,1,0)
    date_fin1=datetime.datetime(2010,12,31,23)
    
    "Définition d'un rectangle"
    
    xs=np.array([200000,200000,
                  272000,272000.])
    ys=np.array([63000,152000,
                  152000,63000])
    
    dat_types=[1,1,1,0,0,1]
    
    sc=3
    
    for mod in range(6):
        # for sc in range(4):
            dirin=dir_stock+dir_ins[mod]+scens[sc]+'/'
            print(dirin)
            objet_MAR=MAR_input_data(xsummits=xs,ysummits=ys,
                            date_debut=date_debut1,
                            date_fin=date_fin1,
                            directory=dirin,
                            directory_hist_sim=dir_hist,
                            var='MBEP',
                            var_unb='E',
                            UnborNot=1,
                            syu=date_debut1.year,
                            eyu=date_fin1.year,
                            mod_ydays=dat_types[mod],
                            model_name=mod_names[mod],
                            generate_quantiles=0)
           
        
            print('ok')
            if date_fin1.year>2015:
                dirout1=dirout+'-'+mod_racs[mod]+'_'+scens[sc]+'_'+str(date_debut1.year)+'-'+\
                    str(date_fin1.year)+'/'
            else:
                
                dirout1=dirout+'-'+mod_racs[mod]+'_'+str(date_debut1.year)+'-'+\
                    str(date_fin1.year)+'/'
            
            objet_MAR.MAR_shapefile(filenameshp,dirout1)
            objet_MAR.MAR_BinaryOutputs(dirout1)
            
            
            
    "*************************************"
    "**Tests pour améliorer le programme***"
    "*************************************"

    xs=np.array([200000,200000,
                  210000,210000.])
    ys=np.array([63000,73000,
                  73000,63000])
    dirin=dir_hist      
    
    date_debut1=datetime.datetime(2016,1,1,0)
    date_fin1=datetime.datetime(2019,12,31,23)  
            
    objet_MAR=MAR_input_data(xsummits=xs,ysummits=ys,
                            date_debut=date_debut1,
                            date_fin=date_fin1,
                            directory=dirin,
                            directory_hist_sim=dir_hist,
                            var='MBRO3',
                            model_name='MIROC6',
                            var_unb='PRECIP_QUANTITY',
                            UnborNot=1,
                            syu=2016,
                            eyu=2017,
                            mod_ydays=1,
                            generate_quantiles=0)
    
    dirout1='/srv7_tmp1/jbrajkovic/These/forWOLF/test/'
    filenameshp='test.shp'
    objet_MAR.MAR_shapefile(filenameshp,dirout1)
    objet_MAR.MAR_BinaryOutputs(dirout1)
    
    # "Tests outputs"
    cmap=ct.IPCC_cmap()
    objet_MAR.plot_mask()
    
    matrice1=objet_MAR.vec_data
    matrice=objet_MAR.MAR_unbiasing()
    matrice=matrice-matrice1
  
    MBRO3_mask=np.sum(matrice[:,:],axis=1)
    
    maxs=np.array(abs(np.min(MBRO3_mask)),np.max(MBRO3_mask))
    maxi=np.max(maxs)
  
    
    # bounds=np.arange(-maxi,maxi+20,20)
    # norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    
    
    # MSK=objet_MAR.mask_rectangles()
    # fig=plt.figure(figsize=(6,6))
    # ax=plt.subplot()
    # m=ct.map_belgium_zoom(ax, objet_MAR.lons, objet_MAR.lats)
    # lons_w=objet_MAR.lons[MSK==True];lats_w=objet_MAR.lats[MSK]
    # MBRO3=np.array(objet_MAR.lons)
    # for k in range(0,np.size(MBRO3_mask)):
    #     for i in range(0,MBRO3.shape[0]):
    #         for j in range(0,MBRO3.shape[1]):
    #             if lons_w[k]==objet_MAR.lons[i,j] and lats_w[k]==objet_MAR.lats[i,j]:
    #                 MBRO3[i,j]=MBRO3_mask[k]
    # vmax=np.max(MBRO3[pd.isna(MBRO3)==False])                
    # MBRO3[MSK==False]=float("nan")
    # x,y=m(objet_MAR.lons,objet_MAR.lats)
    # mapa=m.pcolormesh(x,y,MBRO3,norm=norm,cmap=cmap)
    # cbar=m.colorbar()
    # plt.savefig('fig.png',bbox_inches='tight')
