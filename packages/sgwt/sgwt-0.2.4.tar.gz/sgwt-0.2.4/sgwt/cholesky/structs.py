
"""
structs.py

Contains the ctypes formatted cholmod structs that are used.

Author: Luke Lowery (lukel@tamu.edu)
"""

from ctypes import c_float, c_double, c_int, c_int64, c_size_t, c_void_p
from ctypes import Structure

CHOLMOD_REAL = 0
CHOLMOD_MAXMETHODS = 9
CHOLMOD_HOST_SUPERNODE_BUFFERS = 8  # typical default

# GPU placeholders (when CUDA is not in use)
CHOLMOD_CUBLAS_HANDLE = c_void_p
CHOLMOD_CUDASTREAM = c_void_p
CHOLMOD_CUDAEVENT = c_void_p    

class cholmod_method_struct(Structure):
    _fields_ = [
        ("lnz", c_double),
        ("fl", c_double),
        ("prune_dense", c_double),
        ("prune_dense2", c_double),
        ("nd_oksep", c_double),
        ("other_1", c_double * 4),
        ("nd_small", c_size_t),
        ("other_2", c_double * 4),
        ("aggressive", c_int),
        ("order_for_lu", c_int),
        ("nd_compress", c_int),
        ("nd_camd", c_int),
        ("nd_components", c_int),
        ("ordering", c_int),
        ("other_3", c_size_t * 4),
    ]

class cholmod_common(Structure):
    _fields_ = [
        # primary parameters
        ("dbound", c_double),
        ("grow0", c_double),
        ("grow1", c_double),
        ("grow2", c_size_t),
        ("maxrank", c_size_t),
        ("supernodal_switch", c_double),
        ("supernodal", c_int),
        ("final_asis", c_int),
        ("final_super", c_int),
        ("final_ll", c_int),
        ("final_pack", c_int),
        ("final_monotonic", c_int),
        ("final_resymbol", c_int),
        ("zrelax", c_double * 3),
        ("nrelax", c_size_t * 3),
        ("prefer_zomplex", c_int),
        ("prefer_upper", c_int),
        ("quick_return_if_not_posdef", c_int),
        ("prefer_binary", c_int),

        # printing and error handling
        ("print", c_int),
        ("precise", c_int),
        ("try_catch", c_int),
        ("error_handler", c_void_p),  # pointer to error handler function

        # ordering options
        ("nmethods", c_int),
        ("current", c_int),
        ("selected", c_int),
        ("method", cholmod_method_struct * (CHOLMOD_MAXMETHODS + 1)),
        ("postorder", c_int),
        ("default_nesdis", c_int),

        # METIS workarounds
        ("metis_memory", c_double),
        ("metis_dswitch", c_double),
        ("metis_nswitch", c_size_t),

        # workspace
        ("nrow", c_size_t),
        ("mark", c_int64),
        ("iworksize", c_size_t),
        ("xworkbytes", c_size_t),
        ("Flag", c_void_p),
        ("Head", c_void_p),
        ("Xwork", c_void_p),
        ("Iwork", c_void_p),
        ("itype", c_int),
        ("other_5", c_int),
        ("no_workspace_reallocate", c_int),

        # statistics
        ("status", c_int),
        ("fl", c_double),
        ("lnz", c_double),
        ("anz", c_double),
        ("modfl", c_double),
        ("malloc_count", c_size_t),
        ("memory_usage", c_size_t),
        ("memory_inuse", c_size_t),
        ("nrealloc_col", c_double),
        ("nrealloc_factor", c_double),
        ("ndbounds_hit", c_double),
        ("rowfacfl", c_double),
        ("aatfl", c_double),
        ("called_nd", c_int),
        ("blas_ok", c_int),

        # SuiteSparseQR control/statistics
        ("SPQR_grain", c_double),
        ("SPQR_small", c_double),
        ("SPQR_shrink", c_int),
        ("SPQR_nthreads", c_int),
        ("SPQR_flopcount", c_double),
        ("SPQR_analyze_time", c_double),
        ("SPQR_factorize_time", c_double),
        ("SPQR_solve_time", c_double),
        ("SPQR_flopcount_bound", c_double),
        ("SPQR_tol_used", c_double),
        ("SPQR_norm_E_fro", c_double),
        ("SPQR_istat", c_int64 * 8),

        # CHOLMOD v5.0 additions
        ("nsbounds_hit", c_double),
        ("sbound", c_float),
        ("other_6", c_float),

        # GPU configuration and statistics
        ("useGPU", c_int),
        ("maxGpuMemBytes", c_size_t),
        ("maxGpuMemFraction", c_double),
        ("gpuMemorySize", c_size_t),
        ("gpuKernelTime", c_double),
        ("gpuFlops", c_int64),
        ("gpuNumKernelLaunches", c_int),
        ("cublasHandle", CHOLMOD_CUBLAS_HANDLE),
        ("gpuStream", CHOLMOD_CUDASTREAM * CHOLMOD_HOST_SUPERNODE_BUFFERS),
        ("cublasEventPotrf", CHOLMOD_CUDAEVENT * 3),
        ("updateCKernelsComplete", CHOLMOD_CUDAEVENT),
        ("updateCBuffersFree", CHOLMOD_CUDAEVENT * CHOLMOD_HOST_SUPERNODE_BUFFERS),
        ("dev_mempool", c_void_p),
        ("dev_mempool_size", c_size_t),
        ("host_pinned_mempool", c_void_p),
        ("host_pinned_mempool_size", c_size_t),
        ("devBuffSize", c_size_t),
        ("ibuffer", c_int),
        ("syrkStart", c_double),
        ("cholmod_cpu_gemm_time", c_double),
        ("cholmod_cpu_syrk_time", c_double),
        ("cholmod_cpu_trsm_time", c_double),
        ("cholmod_cpu_potrf_time", c_double),
        ("cholmod_gpu_gemm_time", c_double),
        ("cholmod_gpu_syrk_time", c_double),
        ("cholmod_gpu_trsm_time", c_double),
        ("cholmod_gpu_potrf_time", c_double),
        ("cholmod_assemble_time", c_double),
        ("cholmod_assemble_time2", c_double),
        ("cholmod_cpu_gemm_calls", c_size_t),
        ("cholmod_cpu_syrk_calls", c_size_t),
        ("cholmod_cpu_trsm_calls", c_size_t),
        ("cholmod_cpu_potrf_calls", c_size_t),
        ("cholmod_gpu_gemm_calls", c_size_t),
        ("cholmod_gpu_syrk_calls", c_size_t),
        ("cholmod_gpu_trsm_calls", c_size_t),
        ("cholmod_gpu_potrf_calls", c_size_t),
        ("chunk", c_double),
        ("nthreads_max", c_int),
        # blas_dump omitted (only used if CHOLMOD compiled with -DBLAS_DUMP)
    ]

class cholmod_factor(Structure):
    _fields_ = [
        # Factor size
        ("n", c_size_t),
        ("minor", c_size_t),

        # Symbolic ordering and analysis
        ("Perm", c_void_p),       # int32/int64 array of size n
        ("ColCount", c_void_p),   # int32/int64 array of size n
        ("IPerm", c_void_p),      # int32/int64 array of size n

        # Simplicial factorization
        ("nzmax", c_size_t),      # # entries L->i, L->x, L->z can hold
        ("p", c_void_p),          # int32/int64, size n+1
        ("i", c_void_p),          # int32/int64, size nzmax
        ("x", c_void_p),          # float/double, size nzmax or 2*nzmax
        ("z", c_void_p),          # float/double, size nzmax or empty
        ("nz", c_void_p),         # int32/int64, size ncol
        ("next", c_void_p),       # int32/int64, size n+2
        ("prev", c_void_p),       # int32/int64, size n+2

        # Supernodal factorization
        ("nsuper", c_size_t),     # # supernodes
        ("ssize", c_size_t),      # # integers in L->s
        ("xsize", c_size_t),      # # entries in L->x
        ("maxcsize", c_size_t),   # size of largest update matrix
        ("maxesize", c_size_t),   # max # rows in supernodes excl. triangular
        ("super", c_void_p),      # int32/int64, size nsuper+1
        ("pi", c_void_p),         # int32/int64, size nsuper+1
        ("px", c_void_p),         # int32/int64, size nsuper+1
        ("s", c_void_p),          # int32/int64, size ssize

        # Type of factorization
        ("ordering", c_int),      # fill-reducing ordering method
        ("is_ll", c_int),         # 1 if LL', 0 if LDL'
        ("is_super", c_int),      # 1 if supernodal, 0 if simplicial
        ("is_monotonic", c_int),  # 1 if columns appear 0..n-1
        ("itype", c_int),         # int type for Perm, ColCount, etc.
        ("xtype", c_int),         # pattern, real, complex, zomplex
        ("dtype", c_int),         # double/single
        ("useGPU", c_int),        # symbolic factorization may use GPU
    ]

class cholmod_sparse(Structure):
    _fields_ = [
        ("nrow", c_size_t),     # number of rows
        ("ncol", c_size_t),     # number of columns
        ("nzmax", c_size_t),    # maximum number of entries
        ("p", c_void_p),        # column pointers
        ("i", c_void_p),        # row indices
        ("nz", c_void_p),        # numeric values
        ("x", c_void_p),        # numeric values
        ("z", c_void_p),        # complex values
        ("stype", c_int),       # symmetric flag
        ("itype", c_int),       # index type
        ("xtype", c_int),       # real/pattern/complex
        ("dtype", c_int),       # data type
        ("sorted", c_int),      # columns sorted
        ("packed", c_int)       # packed/unpacked
    ]

class cholmod_dense(Structure):
    _fields_ = [
        ("nrow", c_size_t),     # number of rows
        ("ncol", c_size_t),     # number of columns
        ("nzmax", c_size_t),    # maximum entries
        ("d", c_size_t),        # leading dimension
        ("x", c_void_p),        # values
        ("z", c_void_p),        # complex values
        ("xtype", c_int),       # real/pattern/complex
        ("dtype", c_int)        # data type
    ]
    def __init__(
        self,
        *,
        nrow=0,
        ncol=0,
        nzmax=0,
        d=0,
        x=None,
        z=None,
        xtype=0,
        dtype=0,
    ):
        self.nrow = nrow
        self.ncol = ncol
        self.nzmax = nzmax
        self.d = d

        # Accept None or integer / pointer-compatible values
        self.x = 0 if x is None else x
        self.z = 0 if z is None else z

        self.xtype = xtype
        self.dtype = dtype
