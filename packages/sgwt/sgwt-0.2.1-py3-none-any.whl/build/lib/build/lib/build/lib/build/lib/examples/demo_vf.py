
from sgwt import Convolve, impulse
from sgwt.library import IMPEDANCE_EASTWEST, COORD_EASTWEST, MODIFIED_MORLET
import numpy as np
from demo_plot import plot_signal

# Graph & Kernel
L = IMPEDANCE_EASTWEST.get()
K = MODIFIED_MORLET.get()
C = COORD_EASTWEST.get()

# Signal Input
X = impulse(L, n=-1000)

# TODO kernel scaling
K.Q /= 2000  #  g.scale_kern(...)
K.R /= 2000

with Convolve(L) as g:

    Y = g.convolve(X, K)
    
plot_signal(Y[:,0,0], C, 'Spectral')
