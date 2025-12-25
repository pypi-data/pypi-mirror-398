
from .structs import *

from ..library import get_cholmod_dll

from ctypes import byref, cast, POINTER, c_int32
import numpy as np


CHOLMOD_A    =0 #  solve Ax=b    */
CHOLMOD_LDLt =1 #  solve LDL'x=b */
CHOLMOD_LD   =2 # /* solve LDx=b   */
CHOLMOD_DLt  =3 # /* solve DL'x=b  */
CHOLMOD_L    =4 # /* solve Lx=b    */
CHOLMOD_Lt   =5 # /* solve L'x=b   */
CHOLMOD_D    =6 # /* solve Dx=b    */
CHOLMOD_P    =7 # /* permute x=Px  */
CHOLMOD_Pt   =8 # /* permute x=P'x */

class CholWrapper:
    '''
    A wrapper class for interacting with CHOLMOD DLL

    WARNING: Should only be used indirectly through SGWT Object
    otherwise memory leaks may occur.
    '''

    def __init__(self, A) -> None:
        ''' 
        A: csc_matrix - the matrix to be symbolically factored
        '''
        self.dll = get_cholmod_dll()
        
        # DLL Setup    
        self.config_function_args(self.dll)
        self.config_return_types(self.dll)
        

        # Parse matrix to cholmod_sparse
        self.A = self.numpy_to_chol_sparse(A) # Parse to Cholmod format
        
        # Make choldmod_common struct
        self.common = cholmod_common()

        # TODO Support other solve types
        self.MODE = CHOLMOD_A

    def status(self):
        ''' 
        Description
            Cholmod Status
        Returns
             0 -> OK
            -4 -> Invalid Input
            -2 -> Out of Mem
        '''
        return self.common.status

    '''
    Factorizations
    '''

    def sym_factor(self):
        ''' 
        Performs symbolic factorization using cholmod_analyze
        '''
        self.fact_ptr = self.dll.cholmod_analyze(
            byref(self.A),  
            byref(self.common)
        )
        
    def num_factor(self, beta):
        ''' 
        Description
            Equivilent to choldmod_factorize_p in CHOLMOD.
            The matrix is assumed to be the same that underwent symbolic factorization.
        Parameters
            beta: real number (for the GSP application, must be positive)
        '''
        # Must be complex for DLL use
        beta_cmplx = (c_double * 2)(beta, 0.0) 

        self.dll.cholmod_factorize_p(
            byref(self.A),    # Matrix to factor
            beta_cmplx,
            None, # fset
            0,    # fisze
            self.fact_ptr,  # (In/Out)
            byref(self.common)
        )

    '''
    Solving
    '''

    def solve2(self, B_ptr, Bset_ptr, X_ptr, Xset_ptr, Y_ptr, E_ptr):
        '''
        Description
            Equivilent to choldmod_solve2 in CHOLMOD
        Parameters
            B: Pointer to (N, M) cholmod dense matrix
            Bset_ptr: Pointer to (Nx!) vector Bset where sol is desired, if None will not use Bset feature.
            X_ptr: cholmod_dense pointer to output data into, if None, malloc
        Returns:
            ok: 1 True, 0 False
        '''
        return self.dll.cholmod_solve2(
            self.MODE,       # (In ) int ---- Ax=b
            self.fact_ptr,   # (In ) chol_factor *L 
            B_ptr,           # (In ) chol_dense  *B 
            Bset_ptr,        # (In ) chol_sparse *Bset 
            byref(X_ptr),    # (Out) cholmod_dense **X_Handle (where sol is stored)
            byref(Xset_ptr), # (Out) cholmod_sparse **Xset_Handle, byref(Xset_ptr)
            byref(Y_ptr),    # (Workspace)  **Y
            byref(E_ptr),    # (Workspace) **E
            byref(self.common)
        )

    def solve(self, b_ptr):
        '''
        Description
            Equivilent to choldmod_solve in CHOLMOD
        Parameters
            b_ptr: pointer to cholmod_dense object
        Returns
            x_ptr: pointer to solution, cholmod_dense
        '''
        return self.dll.cholmod_solve(
            self.MODE, 
            self.fact_ptr, 
            b_ptr, 
            byref(self.common)
        )

    '''
    Matrix Operations
    '''
    def sdmult(self, matrix_ptr, out_ptr, alpha=1.0, beta=0.0):
        '''
        out = alpha * (Laplacian @ matrix) + beta * matrix
        '''
        Alpha = (c_double * 2)(alpha, 0.0) 
        Beta  = (c_double * 2)(beta, 0.0) 

        self.dll.cholmod_sdmult(
            byref(self.A), # Left matrix always Laplacian
            0,            # Do not Transpose = 0
            Alpha,       # out += Alpha * (Lap @ matrix)
            Beta,        # out += Beta * matrix
            matrix_ptr,  # Input
            out_ptr,     # Output
            byref(self.common) 
        )

 
    '''
    Data Structures
    '''
        
    def numpy_to_chol_sparse(self, A, itype=0, dtype=0) -> cholmod_sparse:
        """
        Convert a 2D NumPy array A into a cholmod_sparse struct.
        
        Parameters:
            A : csc_matrix sparse vector/matrix
                Dense or 2D array to convert.
            itype : int
                0=int32 indices, 1=int64 indices
            dtype : int
                0=double (real), 1=float (single), 2=complex
        
        Returns:
            cholmod_sparse instance.
        """

        #  Get Shape
        nrow, ncol = A.shape
        
        # Prepare contiguous arrays
        x = np.asfortranarray(A.data, dtype=np.float64)
        i = np.asfortranarray(A.indices, dtype=np.int32 if itype==0 else np.int64)
        p = np.asfortranarray(A.indptr, dtype=np.int32 if itype==0 else np.int64)
        
        # Cast to void pointers for ctypes
        x_ptr = x.ctypes.data_as(c_void_p)
        i_ptr = i.ctypes.data_as(c_void_p)
        p_ptr = p.ctypes.data_as(c_void_p)
        
        # Initialize struct
        cholA = cholmod_sparse()
        cholA.nrow = nrow
        cholA.ncol = ncol
        cholA.nzmax = len(x)
        cholA.p = p_ptr
        cholA.i = i_ptr
        cholA.x = x_ptr
        cholA.z = None             # None if real
        cholA.stype = 1            # 0 = general, 1 = symmetric store upper part
        cholA.itype = itype
        cholA.xtype = 1            # 1 = real
        cholA.dtype = dtype
        cholA.sorted = 1           # columns sorted
        cholA.packed = 1           # packed
        
        return cholA
    
    def numpy_to_chol_sparse_vec(self, A, itype=0, dtype=0):
        """
        Specifically for Bset conversion to cholmod_sparse
        """
        #  Get Shape
        nrow, ncol = A.shape
        
        # Prepare contiguous arrays
        x = np.asfortranarray(A.data, dtype=np.float64)
        i = np.asfortranarray(A.indices, dtype=np.int32 if itype==0 else np.int64)
        p = np.asfortranarray(A.indptr, dtype=np.int32 if itype==0 else np.int64)
        
        # Cast to void pointers for ctypes
        x_ptr = x.ctypes.data_as(c_void_p)
        i_ptr = i.ctypes.data_as(c_void_p)
        p_ptr = p.ctypes.data_as(c_void_p)
        
        # Initialize struct
        bset = cholmod_sparse()
        bset.nrow = nrow
        bset.ncol = ncol
        bset.nzmax = len(x)
        bset.p = p_ptr
        bset.i = i_ptr
        bset.x = x_ptr
        bset.z = None             # None if real
        bset.stype = 0            # 0 = general, 1 = symmetric store upper part
        bset.itype = itype
        bset.xtype = 0            # 0 = pattern, 1 = real 
        bset.dtype = dtype
        bset.sorted = 0           # NOTE FALSE for Bset
        bset.packed = 1           
        
        return bset
    
    def numpy_to_chol_dense(self, b: np.ndarray) -> cholmod_dense:
        '''
        Description
            Converts numpy to choldmod_dense struct
        Returns
            ctype struct (not a pointer)
        '''

        if not isinstance(b, np.ndarray):
            raise TypeError("values must be a numpy.ndarray")

        # Ensure correct dtype
        if b.dtype != np.float64:
            b = b.astype(np.float64, copy=False)

        # Ensure contiguous memory
        if not b.flags["F_CONTIGUOUS"]:
            raise ValueError("b must be Fortran-contiguous for zero-copy CHOLMOD dense")
        #    b = np.ascontiguousarray(b)
        #b = np.asfortranarray(b)

        # Ensure 2D
        if b.ndim != 2:
            raise ValueError("values must be a 2D array")

        # TODO use new constructor

        # Zero Copy into CHOLMOD dense format
        D = cholmod_dense()
        D.nrow = b.shape[0] # Row Size
        D.ncol = b.shape[1] # Column Size
        D.nzmax = b.size    # Max Count of Non-Zero Elements
        D.d = b.shape[0]    # Leading Dimension
        D.x = b.ctypes.data_as(c_void_p) # Pointer to numpy memory
        D.xtype = 1         # real
        D.dtype = 0         # c_double, real

        # Return ctype.Structure
        return D

    def chol_dense_to_numpy(self, x_ptr):
        ''' 
        Description
            Creates numpy array from choldmod_dense ptr.
            Also, frees memory of the ptr.
            Copy must occur, unless context manager is used
         Parameters
            x_ptr: cholmod_dense* pointer to data struct
            copy: False uses shared memory and cholmod must now be 
            responsible for freeing mem. This is very difficult here.
            for now we just copy, to be safe. will be slow tho
        '''

        # Create a View
        nrow = x_ptr.contents.nrow
        ncol = x_ptr.contents.ncol
        d    = x_ptr.contents.d
        buf = cast(x_ptr.contents.x, POINTER(c_double))
        
        # NOTE The order 'F' is crucial for correct reading of memory
        # CHOLMOD stores in fortran order (col-major)
        # Numpy stores C-Order (row-major)
        x_view = np.ndarray(
            shape=(nrow, ncol),
            dtype=np.float64,
            buffer=np.ctypeslib.as_array(buf, shape=(d * ncol,)),
            order="F",
        )


        # Copy Cholmod Mem (Must still be freed)
        return x_view.copy(order='F')


    '''    
    Cholmod Context
    '''

    def start(self):
        '''
        Starts cholmod.
        '''
        self.dll.cholmod_start(
            byref(self.common)
        )

    def finish(self):
        '''
        Finish the cholmod usage.
        '''

        self.dll.cholmod_finish(
            byref(self.common)
        )

    '''    
    Memory
    '''

    def free_factor(self):
        '''
        Convenience method for freeing choldmod_dense matricies/vecs
        '''
        self.dll.cholmod_free_factor(
            byref(self.fact_ptr), 
            byref(self.common)
        )

    def free_dense(self, dense_ptr):
        '''
        Convenience method for freeing choldmod_dense matricies/vecs
        '''
        self.dll.cholmod_free_dense(
            dense_ptr, 
            byref(self.common)
        )

    def free_sparse(self, sparse_ptr):
        '''
        Convenience method for freeing choldmod_sparse matricies/vecs
        '''
        self.dll.cholmod_free_sparse(
            sparse_ptr, 
            byref(self.common)
        )

    def allocate_dense(self, nrow, ncol):
        return self.dll.cholmod_allocate_dense(
            nrow,
            ncol,
            nrow,
            1, # real?
            byref(self.common)
        )
    
    def zeros(self, nrow, ncol):
        return self.dll.cholmod_zeros(
            nrow,
            ncol,
            1, # real?
            byref(self.common)
        )

    '''
    Configuration Functions
    '''

    def config_function_args(self, dll):

        dll.cholmod_start.argtypes = [POINTER(cholmod_common)]
        dll.cholmod_finish.argtypes = [POINTER(cholmod_common)]

        dll.cholmod_allocate_sparse.argtypes = [
            c_size_t, # nrow
            c_size_t, # ncol
            c_size_t, # nzmax
            c_int,   # sorted (T=1,F=0)
            c_int, # packed (T=1,F=0)
            c_int,  # stype
            c_int, # x dtype
            POINTER(cholmod_common)
        ]

        # Symbolic Factorization
        dll.cholmod_analyze.argtypes = [
            POINTER(cholmod_sparse),
            POINTER(cholmod_common)
        ]

        dll.cholmod_zeros.argtypes = [
            c_size_t, # nrow
            c_size_t,   # ncol
            c_int, # xdtipe
            POINTER(cholmod_common)
        ]

        # Numeric factorization w/ Shifting
        dll.cholmod_factorize_p.argtypes = [
            POINTER(cholmod_sparse),          # A
            POINTER(c_double),                # beta[2]
            POINTER(c_int32),                  # fset (int32_t*)
            c_size_t,                          # fsize
            POINTER(cholmod_factor),           # L
            POINTER(cholmod_common)            # Common
        ]

        # For a general 'b' vector, lots of data
        dll.cholmod_solve.argtypes = [
            c_int,                   # Solution Mode
            POINTER(cholmod_factor), # Pointer to factor
            POINTER(cholmod_dense),  # Pointer to dense vec
            POINTER(cholmod_common)  # Pointer to common
        ]

        # For sparse 'b' vector, like an impulse
        dll.cholmod_spsolve.argtypes = [
            c_int,
            POINTER(cholmod_factor),
            POINTER(cholmod_dense),
            POINTER(cholmod_common)
        ]

        # Reused workspace and specified locality/sparisty
        # best for subset of wavelet coefficients
        dll.cholmod_solve2.argtypes = [
            c_int,                                 # sys
            POINTER(cholmod_factor),               # L
            POINTER(cholmod_dense),                # B
            POINTER(cholmod_sparse),               # Bset
            POINTER(POINTER(cholmod_dense)),       # X_Handle
            POINTER(POINTER(cholmod_sparse)),      # Xset_Handle
            POINTER(POINTER(cholmod_dense)),       # Y_Handle
            POINTER(POINTER(cholmod_dense)),       # E_Handle
            POINTER(cholmod_common),               # Common
        ]


        dll.cholmod_allocate_dense.argtypes = [
            c_size_t, c_size_t, c_size_t, c_int,
            POINTER(cholmod_common)
        ]
        dll.cholmod_free_sparse.argtypes = [
            POINTER(POINTER(cholmod_sparse)),
            POINTER(cholmod_common)
        ]
        dll.cholmod_free_dense.argtypes = [
            POINTER(POINTER(cholmod_dense)),
            POINTER(cholmod_common)
        ]
        dll.cholmod_free_factor.argtypes = [
            POINTER(POINTER(cholmod_factor)),
            POINTER(cholmod_common)
        ]
        dll.cholmod_norm_sparse.argtypes = [
            POINTER(cholmod_sparse),  # A
            c_int,                    # norm type: 0=inf, 1=1
            POINTER(cholmod_common)   # Common
        ]

        dll.cholmod_sdmult.argtypes = [
            POINTER(cholmod_sparse),   # A
            c_int,                     # transpose
            POINTER(c_double),         # alpha[2]
            POINTER(c_double),         # beta[2]
            POINTER(cholmod_dense),    # X
            POINTER(cholmod_dense),    # Y
            POINTER(cholmod_common),   # Common
        ]

    def config_return_types(self, dll):
        dll.cholmod_start.restype = None
        dll.cholmod_finish.restype = None
        dll.cholmod_allocate_sparse.restype = POINTER(cholmod_sparse)

        dll.cholmod_analyze.restype = POINTER(cholmod_factor)
        dll.cholmod_factorize_p.restype = c_int
        dll.cholmod_solve.restype = POINTER(cholmod_dense)
        dll.cholmod_spsolve.restype = POINTER(cholmod_sparse)
        dll.cholmod_solve2.restype = c_int  # TRUE (1) or FALSE (0)

        dll.cholmod_allocate_dense.restype = POINTER(cholmod_dense)
        dll.cholmod_free_sparse.restype = None
        dll.cholmod_free_dense.restype = None
        dll.cholmod_free_factor.restype = None
        dll.cholmod_norm_sparse.restype = c_double

        dll.cholmod_sdmult.restype = c_int

        dll.cholmod_zeros.restype = POINTER(cholmod_dense)


    


