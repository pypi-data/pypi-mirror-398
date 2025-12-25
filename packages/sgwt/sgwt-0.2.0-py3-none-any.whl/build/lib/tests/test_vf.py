
import sgwt
from sgwt.library import LENGTH_EASTWEST, COORD_EASTWEST, MODIFIED_MORLET
import numpy as np
import time

# Graph & Kernel
L = LENGTH_EASTWEST.get()
K = MODIFIED_MORLET.get()
C = COORD_EASTWEST.get()

def plot_signal(f):

    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    import matplotlib.cm as cm

    # Coordinates
    L1, L2 = C['longitude'], C['latitude']

    mx = np.sort(np.abs(f))[-20] 
    norm = Normalize(-mx, mx)
    plt.scatter(L1, L2 , c=f, edgecolors='none', cmap=cm.get_cmap('Spectral'), norm=norm)
    plt.axis('scaled')   
    plt.show()

# Signal Input
ntime = 200
X = np.zeros(
    shape=(L.shape[0], ntime), 
    order="F"
)
X[-10000] = 1

K.Q /= 20000000 # TODO kernel scaling g.scale_kern(...)


fsgwt = sgwt.VFConvolve(L, K)
start = time.time()
H1 = fsgwt.convolve(X)
vf_time_sk = time.time() - start 

# Memory Efficient Context
with sgwt.Convolve(L) as g:

    start = time.time()
    H2 = g.convolve(X, K)
    vf_time = time.time() - start 

print(f"         (scikit)  \t (solve2) \t Rel. Speed \t Max Err")
print(f"HP Time: {vf_time_sk*1000:.3f} ms \t {vf_time*1000:.3f} ms ")


plot_signal(H2[:,0,0])
