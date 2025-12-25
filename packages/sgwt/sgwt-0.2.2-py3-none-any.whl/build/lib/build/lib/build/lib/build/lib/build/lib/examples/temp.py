
from sgwt import Convolve, impulse
from sgwt.library import IMPEDANCE_TEXAS


# Graph
L = IMPEDANCE_TEXAS.get()

# Impulse
X  = impulse(L, n=1200)
X += impulse(L, n=600)

# Scales
s = [1e-5, 1e-1]

# Memory Efficient Context
with Convolve(L) as conv:

    LP = conv.lowpass(X, s)
    BP = conv.bandpass(X, s)
    HP = conv.highpass(X, s)


