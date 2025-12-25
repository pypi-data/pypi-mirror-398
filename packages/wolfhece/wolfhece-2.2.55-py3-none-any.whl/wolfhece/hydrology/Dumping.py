"""
Author: HECE - University of Liege, Pierre Archambeau, Christophe Dessers
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import datetime                         # module which contains objects treating dates
from ..PyParams import key_Param

from ..PyTranslate import _

if not '_' in __builtins__:
    import gettext
    _=gettext.gettext

class Dumping:

    def __init__(self, _retentionBasinDict):
        print("Run Dumping")
        self.myType = ''
        self.myRbDict = _retentionBasinDict
        self.nbFlows = 0
        self.flows = []
        self.times = []
        
        self.myType = self.myRbDict['type'][key_Param.VALUE]
        
        if("nb ecretages" in self.myRbDict): 
            self.nbFlows = int(self.myRbDict["nb ecretages"][key_Param.VALUE])

            for i in range(1,self.nbFlows+1):
                self.flows.append(float(self.myRbDict['ecretage '+str(i)][key_Param.VALUE]))
                if(i==1):
                    self.times.append(-1.0)
                else:
                    tmpDate = datetime.datetime.strptime(self.myRbDict['time ecr. '+str(i)][key_Param.VALUE], "%d-%m-%Y %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
                    tmpTime = datetime.datetime.timestamp(tmpDate)
                    self.times.append(tmpTime)


    def compute(self, h, t=-1.0):
        if(self.myType == 'HighwayRB'):
            qLim = 0.0
        elif(self.myType == 'RobiernuRB'):
            qLim = 0.0
        elif(self.myType == 'OrbaisRB' or self.myType == 'ForcedDam' or self.myType == 'HelleRB'):
            if(self.nbFlows>0):
                qLim = self.compute_multistep(h,t)
            else:
                qLim = self.compute_constant()
        else:
            qLim = 0.0
        return qLim


    def compute_constant(self):
        qLim = float(self.myRbDict['ecretage'][key_Param.VALUE])
        return qLim

    
    def compute_multistep(self, h, time):
        
        qlim = self.flows[-1]

        for i in range(self.nbFlows-1):
            if(time<self.times[i+1]):
                qlim = self.flows[i]
                break
        
        return qlim
        