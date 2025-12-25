from sgwt import Convolve, impulse
from sgwt.library import LENGTH_TEXAS, COORD_TEXAS
import numpy as np

from plot_points import plot_signal

# Graph
L = LENGTH_TEXAS.get()
C = COORD_TEXAS.get()

# Impulse
X  = impulse(L, n=1200)

# Scales
s = [1e0]

# Memory Efficient Context
with Convolve(L) as conv:

    BP = conv.bandpass(X, s)[0]

plot_signal(BP[:,0], C, 'coolwarm')




