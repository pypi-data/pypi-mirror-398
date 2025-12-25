import sgwt 
import numpy as np
from scipy.sparse import csc_matrix
from sgwt.library import IMPEDANCE_EASTWEST as graph
import time


L = graph.laplacian()

'''
NOTE In this case where we want to use Bset
the signal must have only one column.

Dense Shape: nBus x 1 

'''
ntime = 1
nscales = 20
scales = np.logspace(1e-2, 1e1, nscales)


# Signal
b = np.zeros(
    shape = (L.shape[0], ntime),
    order="F"
)
b[0] = 1

# Bset (sparsity pattern)
bset = np.zeros_like(b)
bset[b!=0] = 1
bset = csc_matrix(bset)


# SCIT KIT VERSION
fsgwt     = sgwt.FiltersScikit(L, scales)
start = time.time()
WAVS  = fsgwt.scaling_coeffs(b)
end   = time.time()

# DLL VERSION
with sgwt.Filters(L, scales) as fsgwt_DLL:

    # DLL cholmod_solve2 (NOTE eventually can speed up by not copying data)
    start3 = time.time()
    WAVS3  = fsgwt_DLL.scaling_coeffs(b, bset)
    end3   = time.time()

# Print Compute Time
print(f"Time: {(end  - start )*1000:.3f} ms (scikit)")
print(f"Time: {(end3 - start3)*1000:.3f} ms (solve2)")

DIFF = WAVS[:,:,0]-WAVS3[0]
DIFF = DIFF[0]

# Measure Error of DLL solve & scicit
SOLVE2_ERR = np.max(np.abs(DIFF))
print(f"Error: {SOLVE2_ERR:.7f} (solve2)")




