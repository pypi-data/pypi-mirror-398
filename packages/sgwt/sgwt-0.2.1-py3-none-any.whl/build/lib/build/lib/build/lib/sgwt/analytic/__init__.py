'''

sgwt.methods

Contains different implementations
of the SGWT/GSP 

# Implementations:

- Analytical
    - CHOLMOD (scikit)
    - CHOLMOD (DLL)
- Vector Fit
    - CHOLMOD (scikit)
    - CHOLMOD (DLL)
- Chebyshev Fit
    - scipy.sparse

'''

from .analytic_dll import FiltersDLL
from .analytic_scikit import FiltersScikit