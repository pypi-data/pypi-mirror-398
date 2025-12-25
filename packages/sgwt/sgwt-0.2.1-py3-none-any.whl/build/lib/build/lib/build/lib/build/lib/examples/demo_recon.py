
'''
Description

Reconstructs the geographical coordinates of the buses
from a subset of measurments.

Used to construct a oneline!

'''

from sgwt import Convolve
from sgwt.library import IMPEDANCE_WECC
import matplotlib.pyplot as plt
import numpy as np


'''
# Bus Number, Latitude (Y), Longitude (X)
DATA = np.array([
    [5001, 46.719, -122.45], # RED
    [6201, 46.5, -101.33],   # RED
    [1401, 32.52, -112.24],  # RED
    [3903, 39.59, -121.58],  # RED
    [4002, 41.395, -110.107], # RED
    [2401, 35.14, -116.778], # RED
    [4203, 44.34, -123.14]   # RED
])

GRAPHS IN LIBRARY WITH PROBLEMS
- They are either not fully connected
- or there are some zero values/massive values.
- causes big issues in the convolutions

PROBLEMATIC:
- LENGTH, WECC

WORKING:
- IMPEDANCE, WECC

'''

# Graph
L = IMPEDANCE_WECC.get()
nbus = L.shape[0]


# Bus Index, Longitude, Latitude
MEASURMENTS = [
    [ 191    ,-122.45    ,46.719],
    [ 202    ,-101.33    ,46.5  ],
    [  17    ,-112.24    ,32.52 ],
    [ 131    ,-121.58    ,39.59 ],
    [159    ,-110.107   ,41.395],
    [33      ,-116.778   ,35.14 ],
    [187     ,-123.14    ,44.34 ]
]

X = np.zeros((nbus, 2)) # Signal, Sparse
Xh = np.zeros_like(X) # Reconstruction, Dense

# Load Sparse Signal
for idx, long, lat in MEASURMENTS:
    X[idx] = long, lat

# Sampling operator
J = np.diagflat(X[:,0]!=0)

# Scale of Recon
s = 5

with Convolve(L) as conv:

    for i in range(7000):

        B = (X - J@Xh).copy(order='F')

        dX = conv.lowpass(B, [s])

        Xh += s * dX[0]


plt.scatter(Xh[:,0], Xh[:,1] , c='k', edgecolors='none')
plt.scatter(X[:,0][X[:,0]!=0], X[:,1][X[:,1]!=0], c='r')
plt.axis('scaled')   
plt.show()




