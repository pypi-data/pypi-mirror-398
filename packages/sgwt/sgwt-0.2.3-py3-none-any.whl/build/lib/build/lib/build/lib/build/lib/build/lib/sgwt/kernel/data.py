
'''
Kernel Data Classes for Serializations
 
'''

from dataclasses import dataclass
from typing import TypeVar, Type
from numpy import load, savez
import numpy.typing as npt

# Python <3.10 type hinting
T = TypeVar('T', bound='VFKernelData')

@dataclass
class VFKernelData:

    # Residual Matrix (nPoles x nScales)
    R: npt.NDArray

    # Poles Vector (nPoles x 1)
    Q: npt.NDArray

    # Scales (nScales x 1)
    S: npt.NDArray

    @classmethod
    def from_file(cls: Type[T], file_path: str) -> T:
        '''
        Description:
            Loads kernel data from .npz file
        Parameters:
            fname: Filename/directory if needed
        Returns:
            VFKernel instance
        '''

        # Load Data File
        data = load(file_path)

        # Create instance of class
        kern = cls(
            R = data['R'],
            Q = data['Q'],
            S = data['S']
        )

        # Close file
        data.close()

        return kern
    
    def to_file(self, fname):
        '''
        Description:
            Writes poles & residue model to npz file format.
            Post-fix .npz not needed, just write desired name.
        Parameters:
            fname: Filename/directory if needed
        Returns:
            None
        '''
        savez(f'{fname}.npz', R=self.R, Q=self.Q, S=self.S)

        
