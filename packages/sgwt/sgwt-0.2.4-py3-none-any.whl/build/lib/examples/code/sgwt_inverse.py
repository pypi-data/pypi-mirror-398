
from scipy.sparse import load_npz
from numpy import load, save
from sgwt import FastSGWT, VFKern


KERNEL = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\kernels\kernel_model.npz'
LAP_NAME    = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\laplacians\TX2000.npz'

# Kernel File & Laplacian
kern = VFKern.from_file(KERNEL)
L    = load_npz(LAP_NAME)

# SGWT Model
sgwt = FastSGWT(L, kern)

# Load Coeficients
W = load(f'coefficients.npy') # (Bus, Time, Scale)

# Perform Reconstruction, measure performance
f_recon = sgwt.inv(W)

# Save reconstructed signal, if indicated
SAVE_INV = False
if SAVE_INV:
    print('Writing....', end='')
    save('sig_recon.npy', f_recon)
    print('Complete!')
