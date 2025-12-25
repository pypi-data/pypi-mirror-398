
from tests.analytic import Filters
from sgwt.data import IMPEDANCE_EASTWEST as graph
import numpy as np

# Graph
L = graph.laplacian()
ntime = 20
nscales = 5

# Signal Input
shape = (L.shape[0], ntime)
b = np.zeros(shape, order="F")
b[50] = 1

# Scales
scales = np.logspace(1e-2, 1e1, nscales)

# Memory Efficient Context
with Filters(L, scales) as gsp:

    LP = gsp.scaling_coeffs(b)

    BP = gsp.wavelet_coeffs(b)

    HP = gsp.highpass_coeffs(b)





