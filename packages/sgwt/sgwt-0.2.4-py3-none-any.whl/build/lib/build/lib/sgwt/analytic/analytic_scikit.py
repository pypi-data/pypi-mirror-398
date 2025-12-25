

from .analytic import AnalyticFilters

from sksparse.cholmod import analyze
import numpy as np

class FiltersScikit(AnalyticFilters):
    '''
    Description: 
        A class that of analytical versions filters for SGWT and GSP
    Parameters:
        L: sparse csc_matrix form of Graph Laplacian (real valued)
        scales: optional, default scales used
    '''


    '''
    Abstract Method Implementations
    '''

    def _allocate_results(self, b, scales):
        return np.zeros((*b.shape, len(scales)))
    
    def _format_rhs(self, b, bset):
        return b, bset
    
    def _symbolic_factorization(self, L):
        self.factor = analyze(L)
    
    def _numeric_factorization(self, beta):
        self.factor.cholesky_inplace(self.L, beta)

    def _solve(self, b, bset):
        return self.factor(b)

    def _solve_twice(self, b, bset):
        return self.factor(self.factor(b))

    def _mult(self, x, scalar):
        return x*scalar

    def _mult_lap(self, x, scalar):
        return scalar*(self.L@x)

    def _save_to_results(self, x, index):
        self.results[:,:,index] = x

    

    '''
    Local Impulse Responses
    '''

    def scaling_funcs(self, anchor_indecies, scale):
        '''
        Returns
            Scaling functions of indicated scale using the analytical form.
        Parameters:
            anchor_indicies: nodes at which to return scaling functions
            scale: scale of the scaling functions
        '''
        
        F = self.factor
        L = self.L

        # Create the LOCALIZATION VECTOR
        # Number of Rows = Number of true verticies
        # Number of Cols = Number of Reduced vertices
        nLocal = len(anchor_indecies)
        anchors = np.zeros((L.shape[0], nLocal))

        for i, node_idx in enumerate(anchor_indecies):
            anchors[node_idx, i] = 1

        # Analytical solution to scaling function
        F.cholesky_inplace(L, 1/scale)
        S = F(anchors)/scale

        return S
    
    def wavelet_funcs(self, anchor_indecies, scale):
        '''
        Returns
            Wavelet functions of indicated scale using the analytical form.
            L/(L+I/s)^2
        Parameters:
            anchor_indicies: nodes at which to return wavelets
            scale: scale of the wavelet
        '''
        
        F = self.factor
        L = self.L

        # Create the LOCALIZATION VECTOR
        # Number of Rows = Number of true verticies
        # Number of Cols = Number of Reduced vertices
        nLocal = len(anchor_indecies)
        anchors = np.zeros((L.shape[0], nLocal))

        for i, node_idx in enumerate(anchor_indecies):
            anchors[node_idx, i] = 1

        # Analytical solution to scaling function
        F.cholesky_inplace(L, 1/scale)

        # Solve
        S = F(anchors)
        S = L@F(S)/scale

        return S
    

    '''
    Inverse Transformations
    '''
    
    def wavelet_inv(self, W):
        '''
        Description
            The inverse SGWT transformation (only one time point for now)
            And does not support scaling coefficients right now.
        Parameters
            W: ndarray of shape (Bus x Times x Scales)
        Return
            f: reconstructed signal

        WARNING: TODO the reconstructed signal is not normalized
        '''

        F = self.factor
        L = self.L

        # Allocate reconstructed vector (nBus x nFeature)
        f = np.zeros((W.shape[0],W.shape[1]))

        for i, scale in enumerate(self.scales):

            # Coefficients of this scale
            WS = W[:,:,i]

            # Step 1 -> Set Scale
            F.cholesky_inplace(L, 1/scale)

            # Step 2 -> First Sovle (Scaling coeffs!)
            S = F(WS)

            # Step 3 -> Second Solve and Laplacian product
            f += L@F(S)/scale 

        return f