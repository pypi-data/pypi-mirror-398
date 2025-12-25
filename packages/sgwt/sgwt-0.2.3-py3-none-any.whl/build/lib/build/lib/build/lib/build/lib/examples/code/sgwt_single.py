
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

kern = VFKern.from_file(KERNEL)
sgwt = FastSGWT(L, kern)

# Compute coefficients for only one localization
W = sgwt.singleton(f, 1200)

SAVE_SINGLETON = False
if SAVE_SINGLETON:
    fname = 'singleton.npy'
    print('Writing....', end='')
    save(fname, W)
    print(f'Complete!\n Saved to {fname}')
