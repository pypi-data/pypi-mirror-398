from numpy import sort, abs
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.cm as cm


def plot_signal(f, C, cmap='Spectral'):
    '''
    Parameters
        f: Signal to plot, (nVertex, nTime)
        C: Coordinats
    '''

    L1, L2 = C['longitude'], C['latitude']

    mx = sort(abs(f))[-20] 
    norm = Normalize(-mx, mx)
    plt.scatter(L1, L2 , c=f, edgecolors='none', cmap=cm.get_cmap(cmap), norm=norm)
    plt.axis('scaled')   
    plt.show()

