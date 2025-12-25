import sgwt 
import numpy as np
from scipy.sparse import csc_matrix
from sgwt.library import IMPEDANCE_EASTWEST as graph
import time

# Test only Scikit Implementation
import analytic_scikit as SK


L = graph.get()

'''
NOTE Bset only makes sense for the low-pass filter
(i.e., multiplying by laplacian is undefined for BP and HP sometimes)

NOTE In this case where we want to use Bset
the signal must have only one column.

Dense Shape: nBus x 1 

'''
ntime = 1
nscales = 30
s = np.logspace(1e-2, 1e1, nscales)

# NOTE CRUCIAL -> indicate the indicies that are non-zero
NZ = [0, 120]

# Signal
X = np.zeros(
    shape = (L.shape[0], ntime),
    order="F"
)
X[NZ] = 1

# Bset (sparsity pattern)
bset = np.zeros_like(X)
bset[X!=0] = 1
bset = csc_matrix(bset)


# SCIT KIT VERSION
fsgwt     = SK.FiltersScikit(L, s)

start = time.time()
LP_SK  = fsgwt.scaling_coeffs(X)
lp_time_sk = time.time() - start

# DLL VERSION
with sgwt.Convolve(L) as conv:

    start = time.time()
    LP  = conv.lowpass(X, s, bset)
    lp_time = time.time() - start

MSCALE = 0
LP_ERR = np.max(np.abs(LP_SK[:,:,MSCALE]-LP[MSCALE])[NZ])
print(f"         (scikit)  \t (solve2) \t Rel. Speed \t Max Err")
print(f"LP Time: {lp_time_sk*1000:.3f} ms \t {lp_time*1000:.3f} ms \t   {(lp_time_sk-lp_time)/lp_time_sk*100:.1f} % \t {LP_ERR:.3f}")

def ftest(passed: bool):
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"
    COLOR = GREEN if passed else RED
    TEXT = "PASSED" if passed else "FAILED"
    return f"{COLOR}{TEXT}{RESET}"

# Pass
tol = 1e-5
T1 = LP_ERR < tol
print(ftest(T1))