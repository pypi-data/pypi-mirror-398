import sgwt 
import numpy as np
from sgwt.library import IMPEDANCE_EASTWEST as graph
import time

import analytic_scikit as SK


L = graph.get()


# Dense signal input (nBus x nTime)
ntime = 20
nscales = 40
s = np.logspace(1e-2, 1e1, nscales)

# Signal Input
X = np.zeros(
    shape = (L.shape[0], ntime),
    order="F"
)
X[50] = 1


# SCIT KIT VERSION
conv     = SK.FiltersScikit(L, s)

start = time.time()
LP_SK  = conv.scaling_coeffs(X)
lp_time_sk = time.time() - start

start = time.time()
BP_SK  = conv.wavelet_coeffs(X)
bp_time_sk = time.time() - start

start = time.time()
HP_SK  = conv.highpass_coeffs(X)
hp_time_sk = time.time() - start

# DLL VERSION
with sgwt.Convolve(L) as conv:

    # DLL cholmod_solve
    start = time.time()
    LP = conv.lowpass(X, s)
    lp_time = time.time() - start

    start = time.time()
    BP = conv.bandpass(X, s)
    bp_time = time.time() - start

    start = time.time()
    HP = conv.highpass(X, s)
    hp_time = time.time() - start

# Print Compute Time
LP_ERR = np.max(np.abs(LP_SK[:,:,0]-LP[0]))
BP_ERR = np.max(np.abs(BP_SK[:,:,0]-BP[0]))
HP_ERR = np.max(np.abs(HP_SK[:,:,0]-HP[0]))
print(f"         (scikit)  \t (solve2) \t Rel. Speed \t Max Err")
print(f"LP Time: {lp_time_sk*1000:.3f} ms \t {lp_time*1000:.3f} ms \t {(lp_time_sk-lp_time)/lp_time_sk*100:.1f} % \t {LP_ERR:.7f}")
print(f"BP Time: {bp_time_sk*1000:.3f} ms \t {bp_time*1000:.3f} ms \t {(bp_time_sk-bp_time)/bp_time_sk*100:.1f} % \t {BP_ERR:.7f}")
print(f"HP Time: {hp_time_sk*1000:.3f} ms \t {hp_time*1000:.3f} ms \t {(hp_time_sk-hp_time)/hp_time_sk*100:.1f} % \t {HP_ERR:.7f}")

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
T2 = BP_ERR < tol
T3 = HP_ERR < tol
print(ftest(T1 and T2 and T3))
