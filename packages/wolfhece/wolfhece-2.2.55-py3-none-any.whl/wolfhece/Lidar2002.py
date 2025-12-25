
"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from os.path import normpath,exists,join,basename
from os import listdir,scandir
import numpy as np
import numpy.ma as ma
import laspy

from .wolf_array import WolfArray

class Lidar2002(WolfArray):
    
    def test_bounds(self,bounds):
        
        x1=bounds[0][0]
        x2=bounds[0][1]
        y1=bounds[1][0]
        y2=bounds[1][1]
        
        mybounds = self.get_bounds()

        test = not(x2 < mybounds[0][0] or x1 > mybounds[0][1] or y2 < mybounds[1][0] or y1 > mybounds[1][1])
    
        return test

class ASC_file(Lidar2002):
    def __init__(self, fname=None, mold=None, masknull=True):
        
        super().__init__(None, mold, masknull)      
        
        basefile = basename(fname)
        self.origx = float(basefile[0:3])*1000.
        self.origy = float(basefile[3:6])*1000.
        
        self.nbx = 2000
        self.nby = 2000
        self.dx = 1.
        self.dy = 1.
        
        self.filename = fname
    
    def read_data_XYZ(self):
        with open(self.filename,'r') as f:
            self.data=np.loadtxt(f,dtype=np.float32) 
        return 

    def get_xyz(self,which='all'):
        if which=='first':
            return self.data[:,:3]
        elif which=='second':
            return np.column_stack([self.data[:,:2],self.data[:,3]])
        else:
            return np.concatenate((self.get_xyz('first'),self.get_xyz('second')),axis=0)

class BSQ_file(Lidar2002):
    
    def __init__(self, fname=None, mold=None, masknull=True):
        
        super().__init__(None, mold, masknull)      
        
        basefile = basename(fname)
        self.origx = float(basefile[0:3])*1000.
        self.origy = float(basefile[3:6])*1000.
        
        self.nbx = 2000
        self.nby = 2000
        self.dx = 1.
        self.dy = 1.
        
        self.filename = fname
    
    def read_data(self):
        with open(self.filename,'rb') as f:
            locarray = np.fromfile(f, dtype=np.uint16)
            self.array = ma.masked_array(np.float32(locarray)/100., dtype=np.float32)
            self.array = np.flip(self.array.reshape(self.nbx, self.nby),axis=0)
            self.mask_data(0.)         
        return 

def lidar_scandir(mydir,bounds):
    
    first=[]
    second=[]
    for curfile in listdir(mydir):
        if curfile.endswith('.asc'):
            mydata = ASC_file(join(mydir,curfile))
            if mydata.test_bounds(bounds):
                print(curfile)
                mydata.read_data_XYZ()
                first.append(mydata.get_xyz())
                second.append(mydata.get_xyz('second'))

        elif curfile.endswith('.bsq'):
            mydata = BSQ_file(join(mydir,curfile))
            if mydata.test_bounds(bounds):
                print(curfile)
                mydata.read_data()
                if curfile.endswith('fp.bsq'):
                    first.append(mydata.get_xyz())            
                elif curfile.endswith('lp.bsq'):
                    second.append(mydata.get_xyz())            
    
    for entry in scandir(mydir):
        if entry.is_dir():
            locf,locs=lidar_scandir(entry,bounds)
            if len(locf)>0:
                first.append(locf)
            if len(locs)>0:
                second.append(locs)
    
    retfirst=[]
    retsecond=[]

    if len(first)>0 or len(second)>0:
        if len(first)>0:
            retfirst=find_points(np.concatenate(first),bounds)
        if len(second)>0:
            retsecond=find_points(np.concatenate(second),bounds)

    return retfirst,retsecond
            
def create_laz(mydirs,bounds,fnout=''):
    
    first=[]
    second=[]
    for mydir in mydirs:    
        if exists(mydir):    
            myfirst,mysecond=lidar_scandir(mydir,bounds)
            if len(myfirst)>0:
                first.append(myfirst)
            if len(mysecond)>0:
                second.append(mysecond)
    
    first=np.concatenate(first)        
    second=np.concatenate(second)        
    mydata=np.vstack([first,second])

    #Create a new header
    header = laspy.LasHeader(point_format=3, version="1.2")
    header.offsets = np.min(first, axis=0)
    header.scales = np.array([0.1, 0.1, 0.1])
    header.point_count = len(mydata)

    #Create a Las
    las = laspy.LasData(header)
    #Classification
    clas = np.ones(len(mydata),dtype=np.uint8)
    clas[:len(first)]=4
    # clas[len(first):]=1

    las.x = mydata[:, 0]
    las.y = mydata[:, 1]
    las.z = mydata[:, 2]
    las.classification = clas

    if fnout!='':
        las.write(fnout)  
    
    return first,second  

def find_points(xyz,bounds):
    
    xb=bounds[0]
    yb=bounds[1]
    # Get arrays which indicate invalid X, Y, or Z values.
    X_valid = (xb[0] <= xyz[:,0]) & (xb[1] >= xyz[:,0])
    Y_valid = (yb[0] <= xyz[:,1]) & (yb[1] >= xyz[:,1])
    good_indices = np.where(X_valid & Y_valid)[0]          
    return xyz[good_indices]

def create_wolfarray(myxyz,fn_out='',bounds=None):

    if bounds is None:
        return
       
    myarray = WolfArray()
    myarray.dx=1.
    myarray.dy=1.
    myarray.origx = bounds[0][0]
    myarray.origy = bounds[1][0]
    myarray.nbx = int(bounds[0][1]-bounds[0][0])
    myarray.nby = int(bounds[1][1]-bounds[1][0])
        
    locarray=np.ma.zeros([myarray.nbx,myarray.nby],dtype=np.float32)
    
    locarray[myarray.get_ij_from_xy(myxyz[:,0],myxyz[:,1])]=np.float32(myxyz[:,2])
    
    myarray.array = locarray
    myarray.mask_data(0.)
    
    if fn_out!='':
        myarray.filename = fn_out
        myarray.write_all()
    
    return myarray

    
    