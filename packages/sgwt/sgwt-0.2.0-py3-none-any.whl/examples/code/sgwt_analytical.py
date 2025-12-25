
import time
from scipy.sparse import load_npz
from numpy import save
from pandas import read_csv

from sgwt import FastSGWT, VFKern

KERNEL = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\kernels\kernel_model.npz'
LAP_NAME    = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\laplacians\TX2000.npz'
SIGNAL_NAME = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\signals\TX2000\frequency.csv'

# Load laplacian, old coefficients, and signal
L = load_npz(LAP_NAME)

# Data and format for use # (Bus x Time)
f = (read_csv(SIGNAL_NAME).set_index('Time').to_numpy()-1).T

# Kernel File NOTE not actually using here
kern = VFKern.from_file(KERNEL)

# Load SGWT Object from kernel file
sgwt = FastSGWT(L, kern)

# Time and execute
print('SGWT: ')
start = time.time()

# Preliminary tests on 2k bus case shows ~90% speedup
W = sgwt.analytical_wavelet_coeffs(f, scales= kern.S)

end = time.time()
dt = (end - start) 
print(f'{dt:.4f} s')



SAVE_SGWT = False
if SAVE_SGWT:
    fname = 'coefficients.npy'
    print('Writing....', end='')
    save(fname, W)
    print(f'Complete!\n Saved to {fname}')
