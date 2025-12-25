

from .structs import cholmod_dense, cholmod_sparse
from .wrapper import CholWrapper
from ctypes import POINTER

class CholeskyContextManager:

    chol: CholWrapper

    # Context Manager for using CHOLMOD
    def __enter__(self):

        # Start Cholmod
        self.chol.start()

        # Safe Symbolic Factorization
        self.chol.sym_factor()

        # Workspace for operations in solve2
        self.X1    = POINTER(cholmod_dense)()
        self.X2    = POINTER(cholmod_dense)()
        self.Xset  = POINTER(cholmod_sparse)()

        # Provide solve2 with re-usable workspace
        self.Y    = POINTER(cholmod_dense)()
        self.E    = POINTER(cholmod_dense)()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        # Free the factored matrix object
        self.chol.free_factor()

        # Free working memory used in solve2
        self.chol.free_dense(self.X1)
        self.chol.free_dense(self.X2)
        self.chol.free_sparse(self.Xset)

        # Free Y & E (workspacce for solve2)
        self.chol.free_dense(self.Y)
        self.chol.free_dense(self.E)

        # Finish cholmod
        self.chol.finish()