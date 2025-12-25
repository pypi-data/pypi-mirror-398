"""
main.py

Analytical and Vector Fitting methods of GSP & SGWT Convolution

Author: Luke Lowery (lukel@tamu.edu)
"""

from .cholesky import CholWrapper, CholeskyContextManager
from .fitted import VFKern

import numpy as np
from scipy.sparse import csc_matrix

from ctypes import byref
from typing import Any


def impulse(lap, n=0, ntime=1):
    '''
    Description
        Returns a numpy array dirac impulse at vertex n of compatible shape with L
    Parameters
        n: Index of vertex to impulse
        ntime: number of columns in signal
    '''
    b = np.zeros((lap.shape[0],ntime), order='F')
    b[n] = 1

    return b

class Convolve(CholeskyContextManager):

    def __init__(self, L:csc_matrix) -> None:
        
        # Handles symb factor when entering context
        self.chol = CholWrapper(L)

    def __call__(self, B, K: VFKern) -> Any:
        return self.convolve(B, K)

    def convolve(self, B, K: VFKern):
        '''
        Description
            This versatile function can perform many convolutions,
            either with a single function (i.e., smoothing) or for
            a whole transformation (Compute the SGWT)
        Parameters
            X: 2D Array (nVertex, nTime) with column major ordering (F)
            K: Kernel function to generate convolution
        '''

        # List, malloc, numpy, etc.
        nDim = K.R.shape[1]
        X1, Xset = self.X1, self.Xset
        Y, E   = self.Y, self.E

        W = np.zeros((*B.shape, nDim))
        B  = byref(self.chol.numpy_to_chol_dense(B))

        for q, r in zip(K.Q, K.R):

            # Step 1 -> Numeric Factorization
            self.chol.num_factor(q)

            # Step 2 -> Solve Linear System (A + qI) X1 = B
            self.chol.solve2(B,  None, X1, Xset, Y, E) 

            # Before Residue
            Z = self.chol.chol_dense_to_numpy(X1)

            # Cross multiply with residual (SLOW)
            W += Z[:, :, None]*r  

        # TODO add K.D per dimension

        return W
    
    def lowpass(self, B, scales=[1], Bset=None):
        '''
        Description
            Scaling coefficnets at indicated scales using the analytical form
            I/(aL+I)
        Parameters
            f: Signal array (numVerticies x numFeatures) to calculate scaling coeffs.
            fset: Used to solve for a sparse subset of coeffs. ncol must be 1
            scales: list (numScales) of scales to compute scaling coefficents for.
        Returns
            Scaling coefficients for each scale (numVerticies x numScales)
        '''

        # List, malloc, numpy, etc.
        W = []
        X1, X2 = self.X1, self.X2 
        Xset   = self.Xset
        Y, E   = self.Y, self.E

        # Pointer to b (The function being convolved)
        B    = byref(self.chol.numpy_to_chol_dense(B))

        # Using this requires the number of columns in f to be 1
        if Bset is not None:
            Bset = byref(self.chol.numpy_to_chol_sparse_vec(Bset))


        # Calculate Scaling Coefficients of 'f' for each scale
        for i, scale in enumerate(scales):

            # Step 1 -> Numeric Factorization
            self.chol.num_factor(1/scale)
            
            # Step 2 -> Solve Linear System (A + beta*I) X1 = B
            self.chol.solve2(B,  Bset, X1, Xset, Y, E) 

            # Step 3 ->  Divide by scale  X1 = X1/scale
            self.chol.sdmult(X1,  X1, 0.0,  1/scale)

            # Save
            W.append(
                self.chol.chol_dense_to_numpy(X1)
            )

        return W
    
    def bandpass(self, B, scales=[1]):
        '''
        Description
            Wavelet  coeffs of indicated scale using the analytical form.
            (1/s)  L/(L+I/s)^2  located only at a subset of buses
        Parameters
            f: Signal array (numVerticies x numFeatures) to calculate wavelet coeffs.
            fset: (nVerticies x 1) Sparse vector indicator function of nodes 
            where the wavelet coeffs need to be solved. Much faster than calculating
            coefficients for every vertex localization. Default: None, does not consider fset.
            scales: list (numScales) of scales to compute wavelet coefficents for.
        Returns
            Wavelet coefficients for each scale (numVerticies x numScales)
            Solved accurately only for buses indicated by fset
        '''

        # List, malloc, numpy, etc.
        W = []
        X1, X2 = self.X1, self.X2 
        Xset   = self.Xset
        Y, E   = self.Y, self.E

        # Pointer to b (The function being convolved)
        B    = byref(self.chol.numpy_to_chol_dense(B))

        # Calculate Scaling Coefficients of 'f' for each scale
        for i, scale in enumerate(scales):

            # Step 1 -> Numeric Factorization
            self.chol.num_factor(1/scale)
            
            # Step 2 -> Solve Linear System (A + beta*I)^2 x = B
            self.chol.solve2( B, None, X2, Xset, Y, E) 
            self.chol.solve2(X2, None, X1, Xset, Y, E) 

            # Step 3 ->  Divide by scale for normalization
            self.chol.sdmult(
                matrix_ptr = X1, 
                out_ptr =X2,  
                alpha = 4/scale, 
                beta  = 0.0
            )

            W.append(
                self.chol.chol_dense_to_numpy(X2)
            )


        return W

    def highpass(self, B, scales=[1]):
        '''
        Description
            High-pass coefficnets at indicated scales using the analytical form
            aL/(aL+I). Bset parameter not defined for HP filter
        Parameters
            f: Signal array (numVerticies x numFeatures) to calculate HP coeffs.
            fset: Pattern vector 
            scales: list (numScales) of scales to compute  HP coefficents for.
        Returns
            High-pass coefficients for each scale (numVerticies x numScales)
        '''
      
        # List, malloc, numpy, etc.
        W = []
        X1, X2 = self.X1, self.X2 
        Xset   = self.Xset
        Y, E   = self.Y, self.E

        # Pointer to b (The function being convolved)
        B    = byref(self.chol.numpy_to_chol_dense(B))

        # Calculate Scaling Coefficients of 'f' for each scale
        for i, scale in enumerate(scales):

            # Step 1 -> Numeric Factorization
            self.chol.num_factor(1/scale)
            
            # Need to ensure X2 Initialized
            if i==0:
                self.chol.solve2(B, None, X2, Xset, Y, E) 

            # Step 2 -> Solve Linear System (L + I/scale) x = B
            self.chol.solve2(B, None, X1, Xset, Y, E) 

            # Step 3 ->  X2 = L@X1
            self.chol.sdmult(
                matrix_ptr = X1, 
                out_ptr = X2,  
                alpha = 1.0, 
                beta  = 0.0
            )

            # Save
            W.append(
                self.chol.chol_dense_to_numpy(X2)
            )

        return W