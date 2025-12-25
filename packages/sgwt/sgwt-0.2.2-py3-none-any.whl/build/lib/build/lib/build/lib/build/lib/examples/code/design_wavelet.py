"""
design.py

An example to demonstrate how to design the SGWT kernel.

Author: Luke Lowery (lukel@tamu.edu)
"""

from sgwt.kernel import KernelFactory, KernelSmoothRational

# General Kernel Specifications
factory = KernelFactory(
    spectrum_range = (1e-8, 1e3),
    nsamples = 500,
)

# VF Based Kernel Model
kern = factory.make_wavelet(
    kernfuncs   = KernelSmoothRational(),
    scale_range = (1e2, 3e5),#(1e2, 5e5), # (5e3, 1e5),
    nscales     = 65,
    pole_min    = 1e-8,
    npoles      = 65 # 45
)

# Write
FNAME = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\kernels\kernel_model'
kern.to_file(FNAME)