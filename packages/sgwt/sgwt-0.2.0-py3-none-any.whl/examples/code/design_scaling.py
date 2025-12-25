"""
scaling_design.py

An example to demonstrate how to make a scaling function kernel.

Author: Luke Lowery (lukel@tamu.edu)
"""

from sgwt.kernel import KernelFactory, KernelSmoothRational

# General Kernel Specifications
factory = KernelFactory(
    spectrum_range = (1e-9, 1e1),
    nsamples = 500,
)

# VF Based Scaling Kernel
# NOTE For the kernel 1/(1+x) there is an analytical form. This method should
# only be used if a different form is used.
kern = factory.make_scaling(
    kernfuncs      = KernelSmoothRational(),
    scale          = 1e4, # The default/base scale
    pole_min       = 1e-7,
    pole_max       = 1,
    npoles         = 15 
)

# Write
FNAME = r'C:\Users\wyattluke.lowery\Documents\GitHub\sparse-sgwt\examples\kernels\scaling_model'
kern.to_file(FNAME)