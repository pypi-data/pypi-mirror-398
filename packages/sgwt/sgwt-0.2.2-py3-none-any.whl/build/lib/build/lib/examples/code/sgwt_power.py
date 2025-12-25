

'''
Description

    This script uses nodal voltage and nodal current
    to calculate the nodal power injected by the network.
    Then, the SGWT coefficients are calculated for this time-varying
    nodal power.

    The core idea here is that static power (omega=0) is the dispatch,
    while the oscillating power (omega > 0) corresponds to losses
    and can identify sources. Some research shows that
    the dispatch typically does not follow a given pattern
    for the power, because it is 'random' in the spatial sense.

    The mismatch/losses of a non-synchrnous source however
    will follow a SGWT pattern since it is a sigular unstable source.
    (that is the hypothesis, atleast)

'''

from scipy.sparse import load_npz
from numpy import save, sin, cos, pi, load
from pandas import read_csv

from sgwt import FastSGWT

# Files
DIR = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples'
SCALES_NAME = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\kernels\scales.npy'
LAP_NAME    = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\laplacians\TX2000.npz'
YBUS_NAME    = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\laplacians\TX_Ybus.npz'
VMAG_NAME = f'{DIR}\signals\TX2000\\forced\\fo_bus_vmag.csv'
VANG_NAME = f'{DIR}\signals\TX2000\\forced\\fo_bus_vang.csv'

# Load laplacian, old coefficients, and signal
L = load_npz(LAP_NAME)
Y = load_npz(YBUS_NAME)

# Load Bus Signal (Bus x Time)
Vmag = (read_csv(VMAG_NAME).set_index('Time').to_numpy()).T
Vang = (read_csv(VANG_NAME).set_index('Time').to_numpy()).T
Vang *= pi/180

# Transform to complex format
V = Vmag*(cos(Vang) + 1j*sin(Vang))
I = Y@V

# Power Flow
S = V * I.conj()

# Scales (loaded from file for consistancy here)
scales = load(SCALES_NAME)

# Load SGWT Object from kernel file
sgwt = FastSGWT(L)

# This works so much faster.
W_P = sgwt.analytical_wavelet_coeffs(S.real, scales)
W_Q = sgwt.analytical_wavelet_coeffs(S.imag, scales)

print(f'Complete!')

save('P.npy', W_P)
save('Q.npy', W_Q)

print(f'Written.')
