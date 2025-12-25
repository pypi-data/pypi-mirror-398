

'''
Factory classes to generate numerical models
of the SGWT kernel.

Only used when designing a kernel.

'''


# This is the main class the user interacts with.
from .kernel import AbstractKernel
from .data import VFKernelData
from numpy import log, geomspace, array
from numpy.linalg import norm
from scipy.linalg import pinv

# This is the native vector fitting tool.
# No pole allocation in this version.

class KernelFitting:
    '''
    Native vector fitting tool.

    Determines the residues and poles of a discrete
    set of frequnecy-domain wavelet kernels
    '''

    def __init__(self, domain, samples, initial_poles):
        '''
        Parameters:
            domain: (log spaced) sample points of signal
            samples: (on domain) kernel values, each col is different scale
            initial poles: (log spaced) initial pole locations
        '''

        # location, samples of VF, and initial poles
        self.x = domain
        self.G = samples # scale x lambda
        self.Q0 = initial_poles

    def eval_pole_matrix(self, Q, x):
        '''
        Description:
            Evaluates the 'pole matrix' over some domain x given poles Q
        Parameters:
            Q: Poles array (npoles x 1)
            x: domain to evaluate (nsamp x 1)
        Returns:
            Pole Matrix: shape is  (nsamps x npoles)
        '''
        return 1/(x + Q.T)
    
    def calc_residues(self, V, G):
        '''
        Description:
            Solves least square problem for residues for given set of poles
        Parameters:
            V: 'pole matrix' (use eval_pole_matrix)
            G: function being approximated
        Returns:
            Residue Matrix: shape is  (npoles x nscales)
        '''
        # Solve Equation: V@R = G
        return pinv(V)@G
    
    def fit(self):
        '''
        Description:
            Performs VF procedure on signal G.
        Returns:
            R, Q: shape is  (npoles x nscales), (npoles x 1)
        '''
        
        # (samples x poles)
        self.V = self.eval_pole_matrix(self.Q0, self.x)

        # (pole x scale)
        R = self.calc_residues(self.V, self.G)

        # TODO pole relalocation step here and iterative
        Q = self.Q0

        return R, Q
    

class KernelFactory:
    ''' 
    Class holding the spectral form of the wavelet function
    '''

    def __init__(
            self, 
            spectrum_range = (1e-7, 1e2),
            nsamples       = 300
        ):

        
        # Domain Vector
        self.domain = self.logsamp(*spectrum_range, nsamples)  


        # Meta Information
        self.nsamples = nsamples
        self.spectrum_range = spectrum_range

    def logsamp(self, start, end, N=5):
        '''
        Description:
            Helper sampling function for log scales
        Parameters:
            start: first value
            end: last value
            N: number of log-spaced values between start and end
        Returns:
            Samples array: shape is  (N x 1)
        '''
        return geomspace(start, [end],N)
    
    # TODO REMOVE
    def get_approx(self):

        V, R = self.wf.V, self.kern.R

        return V@R
    
    # Returns a data model for wavelet functions at all scales
    def make_wavelet(
            self,
            kernfuncs: AbstractKernel,
            scale_range               = (1e-2, 1e5),
            pole_min:  float          = 1e-5,
            pole_max:  float          = None,
            nscales                   = 10, 
            npoles:    int            = 10
        ) -> VFKernelData:
        '''
        Description:
            Creates a VF wavelet kernel model based on parameters.
        Returns:
            VFKernelData object, a model that can be used to perform SGWT.
        '''

        # Extract Variables
        x = self.domain 

        ''' SCALE DISCRETIZATION '''

        # Discrete set of scales
        s =  self.logsamp(*scale_range, nscales) 
        self.nscales  = nscales 
        self.scales   = s
        
        # Calculate the interval of scales on log scale
        self.ds = log(self.scales[1]/self.scales[0])[0]

        ''' POLE DISCRETIZATION '''

        if pole_max is None:
            pole_max = self.spectrum_range[1]*2

        # Initial Poles
        Q0 = self.logsamp(
            start = pole_min,
            end   = pole_max, 
            N     = npoles
        ) 

        ''' WAVELET FITTING '''
        
        # Sample the function for all scales (nScales x lambda)
        G = kernfuncs.g(x*s.T)

        # Wavelet Fitting object
        wf = KernelFitting(
            domain        = x, 
            samples       = G, 
            initial_poles = Q0
        )

        # Fit and return pole and residues of apporimation
        R, Q = wf.fit()

        ''' DATA STORAGE '''

        # VF Kernel Dataclass
        kern = VFKernelData(
            R = R,
            Q = Q,
            S = s
        )
        
        # Useful for debugging
        self.G    = G
        self.wf   = wf
        self.kern = kern 

        return kern
    
    # Returns scaling function at default scale
    def make_scaling(
            self,
            kernfuncs:     AbstractKernel,
            scale:    float          = 1,
            pole_min: float          = 1e-5,
            pole_max: float          = None,
            npoles:   int            = 10
        ):

        # Extract Variables
        x = self.domain 
        s = array([scale])

        ''' POLE DISCRETIZATION '''

        if pole_max is None:
            pole_max = self.spectrum_range[1]*2

        # Initial Poles
        Q0 = self.logsamp(
            start = pole_min,
            end   = pole_max, 
            N     = npoles
        ) 

        ''' SCALING KERNEL FITTING '''

        # Fitting object, with domain scaled by base scale
        wf = KernelFitting(
            domain        = x, 
            samples       = kernfuncs.h(x*s.T), 
            initial_poles = Q0
        )

        # Fit and return pole and residues of apporimation
        R, Q = wf.fit()

        ''' DATA STORAGE '''

        # VF Kernel Dataclass
        scaling_kern = VFKernelData(
            R = R,
            Q = Q,
            S = s
        )

        return scaling_kern
  