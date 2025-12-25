
"""
viewwavelet.py

Generates a coefficient matrix which is technically
coefficients for the dirac function, which of course
results in the wavelet basis functions at one location.

Use another program to visualize the output.

Author: Luke Lowery (lukel@tamu.edu)
"""

from scipy.sparse import load_npz
from numpy import save, arange
from sgwt import FastSGWT, VFKern


KERNEL      = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\kernels\scaling_model.npz'
LAP_NAME    = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\laplacians\TX2000.npz'

# Kernel File & Laplacian
kern = VFKern.from_file(KERNEL)
L = load_npz(LAP_NAME)

# SGWT Model
sgwt = FastSGWT(L, kern)

# Nodes and scale to calculate Scaling Functions
#scale = 1e5
scale = 3e4
anchors = arange(2000)


# Use if a numerical scaling function is used with VF model
# S = sgwt.scaling_funcs(anchors, scale)
# Analytical form version, using a simple pole scaling function.

# Compute Scaling Functions (Total Buses x Num Anchors)
S = sgwt.analytical_scaling_funcs(anchors, scale)
W = sgwt.analytical_wavelet_funcs(anchors, scale)

# Write Scaling Functions
fname = 'scaling_funcs.npy'
save(fname, S)
print(f'Complete!\n Saved to {fname}')

# Write Wavelet Functions
fname = 'wavelet_funcs.npy'
save(fname, W)
print(f'Complete!\n Saved to {fname}')
