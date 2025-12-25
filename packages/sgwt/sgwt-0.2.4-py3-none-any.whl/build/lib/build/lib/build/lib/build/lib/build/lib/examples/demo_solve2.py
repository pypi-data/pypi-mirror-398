import sgwt 
import numpy as np
from sgwt.library import IMPEDANCE_EASTWEST as graph
import time


L = graph.laplacian()


# Dense signal input (nBus x nTime)
ntime = 20
nscales = 40
scales = np.logspace(1e-2, 1e1, nscales)

# Signal Input
b = np.zeros(
    shape = (L.shape[0], ntime),
    order="F"
)
b[50] = 1


# SCIT KIT VERSION
fsgwt     = sgwt.FiltersScikit(L, scales)
start = time.time()
WAVS  = fsgwt.wavelet_coeffs(b)
end   = time.time()

# DLL VERSION
with sgwt.Filters(L, scales) as fsgwt:

    # DLL cholmod_solve
    start2 = time.time()
    WAVS2 = fsgwt.wavelet_coeffs(b)
    end2   = time.time()

# Print Compute Time
print(f"Time: {(end  - start )*1000:.3f} ms (scikit)")
print(f"Time: {(end2 - start2)*1000:.3f} ms (DLL, solve2)")

# Measure Error of DLL solve & scicit
SOLVE_ERR = np.max(np.abs(WAVS[:,:,0]-WAVS2[0]))
print(f"Error: {SOLVE_ERR:.7f}")




