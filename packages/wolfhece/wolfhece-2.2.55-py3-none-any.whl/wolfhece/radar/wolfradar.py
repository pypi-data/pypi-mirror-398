"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wradlib as wrl
import wx
from math import floor
from ..PyVertexvectors import *
from ..hydrology.read import *
from datetime import datetime as date
from datetime import timedelta as tdelta
from datetime import timezone
from os import path
from osgeo import gdal, osr
from ..drawing_obj import Element_To_Draw
from tqdm import tqdm

RADQPE = 1
RADCLIM = 2
RADFLOOD = 3

FILL_NONE = 0
FILL_ZERO = 1
FILL_NAN = 2
FILL_INTERP = 3

class L08L72:
    epsgL08:osr.SpatialReference
    epsgL72:osr.SpatialReference
    _conv_L08_2_L72:osr.CoordinateTransformation
    _conv_L72_2_L08:osr.CoordinateTransformation

    def __init__(self) -> None:
        self.epsgL08 = osr.SpatialReference()
        self.epsgL72 = osr.SpatialReference()
        self.epsgL08.ImportFromEPSG(3812)
        self.epsgL72.ImportFromEPSG(31370)

        self._conv_L08_2_L72 = osr.CoordinateTransformation(self.epsgL08,self.epsgL72)
        self._conv_L72_2_L08 = osr.CoordinateTransformation(self.epsgL72,self.epsgL08)

    def L08_2_72(self, x:float, y:float):
        return self._conv_L08_2_L72.TransformPoint(x, y)[0:2]

    def L72_2_08(self, x:float, y:float):
        return self._conv_L72_2_L08.TransformPoint(x, y)[0:2]



class RadarIRM(Element_To_Draw):
    def __init__(self, idx: str = '', plotted: bool = True, mapviewer=None, need_for_wx: bool = False) -> None:
        super().__init__(idx=idx, plotted=plotted, mapviewer=mapviewer, need_for_wx=need_for_wx)
        pass


    def convert2rain(self, coordMin:tuple, coordMax:tuple, dateBegin:date, dateEnd:date, deltaT:tdelta, 
                     dirIn:str="", dirOut:str="", file_name_conv:str=".radclim.accum", type_rain:int=RADCLIM, recursive_dir="",
                     check_all_polygons:bool=False, fill_data:int=FILL_NONE):
        
        # =================
        # ALL VERIFICATIONS :
        logging.info("Starting the conversion of IRM data to rain data ...")
        logging.info("Verification ongoing ...")

        # Checking the validity of the repository to read and write :
        isOk, dirIn = check_path(dirIn, applyCWD=True)
        if not isOk:
            logging.error("The directory chosen for IRM data does not exist. Please check your path! ")
            return 
        
        isOk, dirOut = check_path(dirOut, applyCWD=True)
        if not isOk:
            logging.error("The directory chosen for IRM data does not exist. Please check your path! ")
            return

        
        # Checking the validity of the dates :
        dt = deltaT.total_seconds()
        nb_intervals = floor((dateEnd - dateBegin).total_seconds() / dt)
        time = [dateBegin + tdelta(seconds=dt*i) for i in range(nb_intervals + 1)]
        if recursive_dir == "":
            # Prefix for dates -> only if it's not a recursive directory
            dt_str = "{:.0f}d".format(deltaT.days)*(deltaT.days>0) \
                    + "{:.0f}h".format(floor(deltaT.seconds)/3600)*(floor(deltaT.seconds/3600)>0) \
                    + "{:.0f}m".format(floor(deltaT.seconds%3600)/60)*(floor(deltaT.seconds%3600)/60>0)
            suffix = "".join([file_name_conv, dt_str, ".hdf"])
            all_files = [os.path.join(dirIn,"".join([t.strftime("%Y%m%d%H%M%S"),suffix])) for t in time]
        else:
            suffix = "".join([file_name_conv, ".hdf"])
            all_files = [os.path.join(dirIn, 
                                      t.strftime("%Y"),
                                      t.strftime("%m"),
                                      t.strftime("%d"),
                                      recursive_dir,
                                      "".join([t.strftime("%Y%m%d%H%M%S"),suffix])) for t in time]
        # are_present = np.all(np.array( \
        #             [os.path.exists(os.path.join(dirIn,"".join([t.strftime("%Y%m%d%H%M%S"),suffix]))) for t in time] \
        #             ))
        
        are_present = np.all(np.array( \
                    [os.path.exists(el) for el in all_files] \
                    ))
        
        if not are_present:
            logging.error("Rain files present in the selected directory are does not contain all the information between the desired interval.")
            i_problem = np.where(np.array([os.path.exists(el) for el in all_files]) == False)[0]
            logging.error("The following files are missing :")
            for i in i_problem:
                logging.error(all_files[i])
            if fill_data == FILL_NONE:
                logging.error("The process stops because there are missing files!")
                logging.error("To make an linear interpolation set to False 'no_missing_files' argument.")
                return
        
        # Creating the direcory results
        # Directory of the shapefile
        shpDir = os.path.join(dirOut,'Grid')
        if not os.path.exists(shpDir):
            try:
                os.mkdir(shpDir)
            except OSError:
                print ("Creation of the directory %s failed" % shpDir)
                return
            else:
                print ("Successfully created the directory %s" % shpDir)
                shpFile = "Grid_radar.shp"
                fileOut = os.path.join(shpDir, shpFile)
        else:
            shpFile = "Grid_radar.shp"
            fileOut = os.path.join(shpDir, shpFile)
        # # Directory of the of the time series
        timeSeriesDir = os.path.join(dirOut,'IRM')
        if not os.path.exists(timeSeriesDir):
            try:
                os.mkdir(timeSeriesDir)
            except OSError:
                print ("Creation of the directory %s failed" % timeSeriesDir)
            else:
                print ("Successfully created the directory %s" % timeSeriesDir)

        logging.info("Verification validated!")

        # =================
        # CORE PROCEDURE
        # After all verifications, the core procedure can now start :
        # extract all the points in all the .hdf files and their values -> check whether to crop during this process of after

        logging.info("Creation of the shapefile ongoing ...")

        # Definition of the domaine zone
        limits = vector()
        limits.add_vertex(wolfvertex(coordMin[0],coordMin[1]))
        limits.add_vertex(wolfvertex(coordMax[0],coordMin[1]))
        limits.add_vertex(wolfvertex(coordMax[0],coordMax[1]))
        limits.add_vertex(wolfvertex(coordMin[0],coordMax[1]))

        # The shape file will be based on the first file read
        cur_file = all_files[0]
        hdf_ds = gdal.Open(cur_file, gdal.GA_ReadOnly)
        values, coord, proj = wrl.georef.raster.extract_raster_dataset(hdf_ds, mode="edge", nodata=0.0)

        # project the Lambert 2008 in Lambert 1972 coordinates -> let the possibility to crop either points or polygons
        coord72 = np.zeros_like(coord)
        proj72 = L08L72()
        nbI, nbJ, nbC = np.shape(coord)
        for i in range(nbI):
            for j in range(nbJ):
                coord72[i,j] = np.array(proj72.L08_2_72(coord[i,j,0],coord[i,j,1]))


        # Creation of a list of polygons containing a list of vertices grouped in tuples
        all_i, all_j = np.meshgrid(range(nbI-1),range(nbJ-1), indexing='ij')
        polygons_list = [
                    [tuple(coord72[i][j]), tuple(coord72[i+1][j]), 
                     tuple(coord72[i+1][j+1]), tuple(coord72[i][j+1]),
                     tuple(coord72[i][j])]

                    for i,j,v in zip(all_i.reshape(-1),all_j.reshape(-1),coord72[:-1, :-1].reshape(-1))
                    ]

        # create polygons out of the given points
        polygons = zone()
        zones_indices = []
        i_zone = 0
        for cur_poly in polygons_list:
            cur_vec = vector(name=" ".join(["Zone", str(polygons.nbvectors+1)]))
            is_inside = False
            for cur_point in cur_poly:
                cur_vec.add_vertex(wolfvertex(cur_point[0],cur_point[1]))
                if limits.isinside(cur_point[0], cur_point[1]):
                    is_inside = True
            if is_inside:
                polygons.add_vector(cur_vec)
                zones_indices.append(i_zone)
            i_zone += 1

        # save the polygons in .shp shapefile
        polygons.export_shape(fileOut)
        logging.info("Creation of the shapefile finished !")

        logging.info("Creation of polygon time series ongoing ...")
        # Create a folder with the time serie for each polygone
        timeStps = [[str(t.day), str(t.month), str(t.year), str(t.hour), str(t.minute), str(t.second)] for t in time]

        all_values = np.zeros((len(all_files), polygons.nbvectors))
        for i in tqdm(range(len(all_files))):
            cur_file = all_files[i]
            exists = os.path.exists(cur_file)
            try:
                if exists:
                    hdf_ds = gdal.Open(cur_file, gdal.GA_ReadOnly)
                    values, coord, proj = wrl.georef.raster.extract_raster_dataset(hdf_ds, mode="edge", nodata=0.0)
                    vec_values = values.reshape(-1)
                    all_values[i,:] = np.nan_to_num([vec_values[i] for i in zones_indices], copy=False, nan=0.0)
                    # FIXME this following line -> to check !!!! -> Convert [mm/h] to accumulated rain [mm] at each time step
                    # radflood
                    if type_rain == RADFLOOD or type_rain == RADCLIM:
                        all_values[i,:] = all_values[i,:]
                    elif type_rain == RADQPE:
                        # radqpe
                        # TODO : check the conversion for radclim
                        all_values[i,:] = all_values[i,:]*(dt/3600.0)
                    # all_values[i,:] = all_values[i,:]*(dt/3600.0)
                else:
                    if fill_data == FILL_ZERO:
                        all_values[i,:] = 0.0
                    else:
                        all_values[i,:] = np.nan
            except:
                logging.error("".join(["Something bad happened while reading hdf file :", cur_file]))
                all_values[i,:] = 0.0
        logging.info("Creation of polygon time series finished !")

        logging.info("Writing polygon time series ongoing ...")
        # Writing the file
        for iVec in tqdm(range(polygons.nbvectors)):
            # Clean the nan value with linear interpolation
            # FIXME : to check the interpolation
            if(fill_data == FILL_INTERP):
                logging.warning('Interpolating missing values in the time series -> Still to test!')
                valid = ~np.isnan(all_values[:,iVec])
                invalid = np.isnan(all_values[:,iVec])
                all_values[invalid,iVec] = np.interp(np.flatnonzero(invalid), np.flatnonzero(valid), all_values[valid,iVec])
            # write in the file
            with open(os.path.join(timeSeriesDir,"".join([str(iVec+1),".rain"])), 'w') as f:
                f.write("".join([str(iVec+1),"\n"]))
                f.write("".join([str(1),"\n"]))
                f.write("".join([str(7),"\n"]))
                f.write("".join([str(len(all_files)),"\n"]))
                for cur_t in range(len(timeStps)):
                    f.write("\t".join(timeStps[cur_t] + [str(all_values[cur_t,iVec])]) + "\n")
        logging.info("Writing polygon time series finished !")
                
        print(are_present)

    # def plot(self):
    #     pass

    def _shapefile(fileName:str):
        pass

    


if __name__ == "__main__":

    app = wx.App()
    # Selection of the working directory
    idir=wx.DirDialog(None,"Please choose a IRM rain directory")
    if idir.ShowModal() == wx.ID_CANCEL:
        print("Operation cancelled!")
        idir.Destroy()
    
    readDir = idir.GetPath()
    idir.Destroy()

    idir=wx.DirDialog(None,"Please a directory to write results")
    if idir.ShowModal() == wx.ID_CANCEL:
        print("Operation cancelled!")
        idir.Destroy()
    
    writeDir = idir.GetPath()
    idir.Destroy()

    irm = RadarIRM()
    coord_min = (0.0, 0.0)
    coord_max = (0.0, 0.0)
    db = date(year=2021, month=7, day=1, tzinfo=timezone.utc)
    de = date(year=2021, month=7, day=31, hour=23, minute=55, tzinfo=timezone.utc)
    dt = tdelta(minutes=5)
    print(db)

    irm.convert2rain(coord_min, coord_max, dateBegin=db, dateEnd=de, deltaT=dt, dirIn=readDir, dirOut=writeDir)

    print("The End!")
