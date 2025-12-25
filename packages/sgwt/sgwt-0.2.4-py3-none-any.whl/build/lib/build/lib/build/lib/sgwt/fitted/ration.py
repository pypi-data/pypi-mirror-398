from dataclasses import dataclass
from typing import TypeVar, Type
from numpy import array
import numpy.typing as npt

T = TypeVar('T', bound='VFKern')

@dataclass
class VFKern:

    # Residual Matrix (nPoles x nScales)
    R: npt.NDArray

    # Poles Vector (nPoles x 1)
    Q: npt.NDArray

    # Offset (nDim x 1)
    D: npt.NDArray

    @classmethod
    def from_json(cls: Type[T], data) -> T:
        '''
        Description:
            Loads kernel data from json/dict
        Parameters:
            data: the dict containing rational data
        Returns:
            VFKernelData instance
        '''

        
        R = []
        Q = []
        D = data['d']

        for pole in data['poles']:
        
            R.append(pole['r'])
            Q.append(pole['q'])

        R = array(R)
        Q = array(Q)
        D = array(D)

        return cls(R, Q, D)
    