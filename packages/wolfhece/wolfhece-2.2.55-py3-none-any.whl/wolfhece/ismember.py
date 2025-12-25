import numpy as np

"""
example :

import numpy as np
import time

from wolfhece.ismember import ismember,ismembertol

nb=1000000
imax=10000
a=np.random.randint(1,imax,2*nb)
a=a.reshape((nb,2))
b=np.random.randint(1,imax,2*nb)
b=b.reshape((nb,2))

st = time.process_time()
c=ismember(a,b)
et = time.process_time()
res = et - st
print('ismember int - CPU Execution time:', res, 'seconds')

a=np.random.rand(nb,2)
b=np.random.rand(nb,2)

st = time.process_time()
d=ismember(a,b)
et = time.process_time()
res = et - st
print('ismember float - CPU Execution time:', res, 'seconds')

st = time.process_time()
dtol=ismembertol(a,b,3)
et = time.process_time()
res = et - st
print('ismember float tolerance - CPU Execution time:', res, 'seconds')
"""

"""
Process time:

import numpy as np
import time
import matplotlib.pyplot as plt

from wolfhece.ismember import ismember,ismembertol

timeint=[]
timef=[]
timeftol=[]

maxnbe=8
for nbe in range(1,maxnbe):
    print(nbe)
    nb=10**nbe
    imax=10000
    a=np.random.randint(1,imax,2*nb)
    a=a.reshape((nb,2))
    b=np.random.randint(1,imax,2*nb)
    b=b.reshape((nb,2))

    st = time.process_time_ns()
    c=ismember(a,b)
    et = time.process_time_ns()
    res = et - st

    timeint.append(res)

    a=np.random.rand(nb,2)
    b=np.random.rand(nb,2)

    st = time.process_time_ns()
    d=ismember(a,b)
    et = time.process_time_ns()
    res = et - st
    timef.append(res)

    st = time.process_time_ns()
    dtol=ismembertol(a,b,3)
    et = time.process_time_ns()
    res = et - st
    timeftol.append(res)

plt.plot(range(1,maxnbe),timeint,label='integer')
plt.plot(range(1,maxnbe),timef,label='float')
plt.plot(range(1,maxnbe),timeftol,label='float with tolerance')
plt.legend()
plt.yscale('log')
plt.xlabel('Number of elements [power of 10]')
plt.ylabel('Total process time [ns]')
plt.show()


"""

def ismember(a,b,nbdecimal=6):
    """trouve les éléments uniques dans les listes a et b"""
    unel,counts = np.unique(np.concatenate((a,b)),return_counts=True,axis=0)
    #trouve les éléments dont le comptage est supérieur à 1 --> les doublons
    return unel[np.where(counts>1)]

def ismembertol(a,b,nbdecimal=6):
    """trouve les éléments uniques dans les listes a et b avec un arrondi à nbdecimal"""
    aa = np.asarray(a).round(nbdecimal)
    bb = np.asarray(b).round(nbdecimal)
    return ismember(aa,bb)