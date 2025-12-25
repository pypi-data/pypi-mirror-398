"""
main.py

Will be abstracted eventually. Core class for now, implementing
the VF version of the SGWT.

Author: Luke Lowery (lukel@tamu.edu)
"""

from abc import ABC, abstractmethod
from sksparse.cholmod import analyze
from scipy.sparse import csc_matrix

import numpy as np

class VFConvolve:
    '''
    Description
        A class that computes rational-approximation approach to the SGWT
        and various analytical versions of filters.
    Parameters
        L: sparse csc_matrix form of Graph Laplacian (real valued)
        kern: optional, VF data of spectral function
    '''

    def __init__(self, L: csc_matrix, K):
        '''
        Parameters
            K: json/dict of poles and residues
        '''

        # Sparse Laplacian
        self.L = L

        # Kernel Function
        self.R = K.R 
        self.Q = K.Q
        self.D = K.D
        self.ndim = self.R.shape[1]

        # Symbolic Factorization
        self.factor = analyze(L)

    def allocate(self, f):
        return np.zeros((*f.shape, self.ndim))
    
    # TODO we can also 'scale' any given function very easily

    def convolve(self, f):
        '''
        Description
            General convolution of function f
        Returns
            W:  (nVertex, nTime, nDim)
        '''
        
        W = self.allocate(f)
        F = self.factor
        L = self.L

        for q, r in zip(self.Q, self.R):

            F.cholesky_inplace(L, q) 
            W += F(f)[:, :, None]*r  
            
        # TODO add self.D per dimension

        return W
    