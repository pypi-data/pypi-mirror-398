from abc import ABC, abstractmethod
from scipy.sparse import csc_matrix

class AnalyticFilters(ABC):

    def __init__(self,  L: csc_matrix, scales=[1]) -> None:
        super().__init__()

        # Sparse Laplacian
        self.L = L

        # Discrete Scales
        self.scales = scales
        self.nscales = len(scales)

        # Symbolic Factorization
        self._symbolic_factorization(L)

    
    def scaling_coeffs(self, b, bset=None, scales=None):
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

        # Process Scales
        scales = self.scales if scales is None else scales

        # List, malloc, numpy, etc.
        self.results = self._allocate_results(b, scales)

        # Process b and bset if needed
        B, Bset = self._format_rhs(b, bset)

        # Calculate Scaling Coefficients of 'f' for each scale
        for i, scale in enumerate(scales):

            # Step 1 -> Numeric Factorization
            self._numeric_factorization(beta=1/scale)
            
            # Step 2 -> Solve Linear System (A + beta*I) x = B
            x1 = self._solve(B, Bset)

            # Step 3 ->  Divide by scale for normalization
            x2 = self._mult(x1, 1/scale)

            # Save
            self._save_to_results(x2, index=i)

        return self.results

    def wavelet_coeffs(self, b, bset=None, scales=None):
        '''
        Returns
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

        # Process Scales
        scales = self.scales if scales is None else scales

        # List, malloc, numpy, etc.
        self.results = self._allocate_results(b, scales)

        # Process b and bset if needed
        B, Bset = self._format_rhs(b, bset)

        # Calculate Scaling Coefficients of 'f' for each scale
        for i, scale in enumerate(scales):

            # Step 1 -> Numeric Factorization
            self._numeric_factorization(beta=1/scale)
            
            # Step 2 -> Solve Linear System (A + beta*I) x = B
            x = self._solve_twice(B, Bset)

            # Step 3 ->  Divide by scale for normalization
            x = self._mult_lap(x, 4/scale)

            # Save
            self._save_to_results(x, index=i)

        return self.results

    def highpass_coeffs(self, b, bset=None, scales=None):
        '''
        Description
            High-pass coefficnets at indicated scales using the analytical form
            aL/(aL+I)
        Parameters
            f: Signal array (numVerticies x numFeatures) to calculate HP coeffs.
            fset: Pattern vector 
            scales: list (numScales) of scales to compute  HP coefficents for.
        Returns
            High-pass coefficients for each scale (numVerticies x numScales)
        '''
                
        # Process Scales
        scales = self.scales if scales is None else scales

        # List, malloc, numpy, etc.
        self.results = self._allocate_results(b, scales)

        # Process b and bset if needed
        B, Bset = self._format_rhs(b, bset)

        # Calculate Scaling Coefficients of 'f' for each scale
        for i, scale in enumerate(scales):

            # Step 1 -> Numeric Factorization
            self._numeric_factorization(beta=1/scale)
            
            if i==0:
                # BUG this line is only called
                # to gaurentee hidden states are initialized
                self._solve_twice(B, Bset)

            # Step 2 -> Solve Linear System (L + I/scale) x = B
            x = self._solve(B, Bset)

            # Step 3 ->  x = L@x
            x = self._mult_lap(x, 1)

            # Save
            self._save_to_results(x, index=i)

        return self.results

    @abstractmethod
    def _allocate_results(self, b, scales):
        pass
    
    @abstractmethod
    def _format_rhs(self):
        pass

    @abstractmethod
    def _symbolic_factorization(self, L):
        pass

    @abstractmethod
    def _numeric_factorization(self, beta):
        pass

    @abstractmethod
    def _solve(self, b, bset):
        pass

    @abstractmethod
    def _solve_twice(self, b, bset):
        pass

    @abstractmethod
    def _mult(self, x, scalar):
        pass

    @abstractmethod
    def _mult_lap(self, x, scalar):
        pass

    @abstractmethod
    def _save_to_results(self, x, index):
        pass