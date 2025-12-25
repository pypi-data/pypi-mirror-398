"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import pandas as pd
import os
from datetime import datetime as dt

from pandas.core.tools.datetimes import to_datetime
from .PyTranslate import _

class dcenn_data():

    def __init__(self,dir) -> None:
        
        self.mydir=dir
        self.series={}
        self.series['data']=None

        for file in os.listdir(dir):
            if file.endswith('.xls') or file.endswith('.xlsx') :
                print(file)

                strings=file.split('_')
                start=dt.strptime(strings[2],'%Y%m%d')
                end=dt.strptime(strings[3],'%Y%m%d')

                data = pd.read_excel(os.path.join(dir,file), index_col=0,header=0,parse_dates=True,dtype={'Débit (m3/s)': str},squeeze=True)        
                
                data = data.str.replace(',','.').astype('float')
                self.series[file]={}

                self.series[file]['start']=start
                self.series[file]['end']=end
                self.series[file]['data']=data

                if self.series['data'] is None:
                    self.series['data']=data
                else:
                    self.series['data']=pd.concat([self.series['data'],data])
        
        pass

