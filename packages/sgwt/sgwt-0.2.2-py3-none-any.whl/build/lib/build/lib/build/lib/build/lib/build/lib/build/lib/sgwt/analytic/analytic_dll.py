

from .analytic import AnalyticFilters

from ..cholesky import CholWrapper, CholeskyContextManager
from ctypes import byref


class FiltersDLL(AnalyticFilters, CholeskyContextManager):
    '''
    A sparse memory efficient implementation
    that uses cholmod_solve2
    '''

    '''
    Abstract Function Definitions
    '''

    def _allocate_results(self, b, scales):
        return []
    
    def _format_rhs(self, b, bset):

        # Pointer to b (The function being convolved)
        B    = byref(self.chol.numpy_to_chol_dense(b))

        # Using this requires the number of columns in f to be 1
        if bset is not None:
            Bset = byref(self.chol.numpy_to_chol_sparse_vec(bset))
        else:
            Bset = None
        
        return B, Bset

    def _symbolic_factorization(self, L):
        self.chol = CholWrapper(L)
    
    def _numeric_factorization(self, beta):
        self.chol.num_factor(beta)

    def _solve(self, b, bset):
        self.chol.solve2(
            b, 
            bset, 
            self.X1, 
            self.Xset, 
            self.Y, 
            self.E
        ) 
        return self.X1
    
    def _solve_twice(self, b, bset):

        # Solve (L+beta*I) X2 = B
        self.chol.solve2(
            b, 
            bset, 
            self.X2, 
            self.Xset, 
            self.Y, 
            self.E
        ) 

        # Solve (L+beta*I) X1 = X2
        self.chol.solve2(
            self.X2, 
            None, 
            self.X1, 
            self.Xset, 
            self.Y, 
            self.E
        ) 

        return self.X1

    def _mult(self, x, scalar):
        
        # x = beta * x
        self.chol.sdmult(
            x,  # n/a
            x,  # beta  * x 
            alpha = 0.0, 
            beta  = scalar
        )

        return x
    
    def _mult_lap(self, x, scalar):
        self.chol.sdmult(
            matrix_ptr = x, 
            out_ptr = self.X2,  
            alpha = scalar, 
            beta  = 0.0
        )
        return self.X2

    def _save_to_results(self, x, index):
        self.results.append(
            self.chol.chol_dense_to_numpy(x)
        )
