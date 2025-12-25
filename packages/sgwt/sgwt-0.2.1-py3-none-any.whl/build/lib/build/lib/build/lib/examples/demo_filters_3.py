from sgwt import Convolve, impulse
from sgwt.library import DELAY_USA, COORD_USA
import numpy as np

from demo_plot import plot_signal

# Graph
L = DELAY_USA.get()
C = COORD_USA.get()

# Impulse
X  = impulse(L, n=15000)

# Scales
s = [3e0]

# Memory Efficient Context
with Convolve(L) as conv:

    BP = conv.bandpass(X, s)[0]
    BP = conv.bandpass(BP, s)[0]
    BP = conv.bandpass(BP, s)[0]

plot_signal(BP[:,0], C, 'coolwarm')




