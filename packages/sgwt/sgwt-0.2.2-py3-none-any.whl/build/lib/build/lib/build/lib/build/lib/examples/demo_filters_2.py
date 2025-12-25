
from sgwt import Convolve, impulse
from sgwt.library import DELAY_EASTWEST, COORD_EASTWEST
from demo_plot import plot_signal

# Graph
L = DELAY_EASTWEST.get()
C = COORD_EASTWEST.get()

# Impulse
X  = impulse(L, n=65000)

# Scales
s = [3e0]

# Memory Efficient Context
with Convolve(L) as conv:

    BP = conv.bandpass(X, s)[0]
    BP = conv.bandpass(BP, s)[0]
    BP = conv.bandpass(BP, s)[0]

plot_signal(BP[:,0], C, 'coolwarm')

