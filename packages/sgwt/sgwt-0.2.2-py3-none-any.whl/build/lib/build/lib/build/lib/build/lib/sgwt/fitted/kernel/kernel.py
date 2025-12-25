
'''
Analytical representations of wavelet 
scaling and generating functions to pass to
the KernelFactory
'''

from abc import ABC, abstractmethod

class AbstractKernel:
    '''
    An Abstract SGWT Kernel with callable functions g(x) and h(x)
    that have can be evaluated in the spectrum of the graph laplacian.
    '''

    def __init__(self) -> None:
        pass

    @abstractmethod
    def h(self, x):
        '''
        Description:
            The scaling kerenl h(x) evaluating the 'DC-like' spectrum
        Parameters:
            Vector x, the spectrum domain to evaluate.
        Returns:
            Spectral domain scaling kerenel
        '''

    @abstractmethod
    def g(self, x):
        '''
        Description:
            The wavelet generating kernel g(x) evaluating the un-scaled wavelet
        Parameters:
            Vector x, the spectrum domain to evaluate.
        Returns:
            Spectral domain wavelet kerenel
        '''

class KernelSmoothRational(AbstractKernel):
    '''
    A specific SGWT analytical function representation.
    '''

    def __init__(self, order=1) -> None:
        self.order = order
        super().__init__()
    
    def g(self, x):
        '''
        Description:
            Default kernel function evaluator
        Parameters:
            x: domain to evaluate (array)
            order: higher order -> narrower bandwidth
        Returns:
            g(x): same shape as x
        '''
        f = 2*x/(1+x**2)
        return f**self.order
    
    def h(self, x):
        '''
        Description:
            The scaling kerenl h(x) evaluating the 'DC-like' spectrum
        Parameters:
            x: domain to evaluate (array)
        Returns:
           h(x): same shape as x
        '''
        # NOTE
        # The scaling function CAN still have negative parts in the vertex-domain,
        # at the edge, making it look slightly ac.
        f = 1/(1+x**2)

        # NOTE the above should theoretically be better but wow the below
        # works SO much better in practice. Probably
        # related to the fact that 'x' here is actually k^2
        # so the above is functionally k^4 which is not ideal
        #f = 1/(1+x)
        return f
