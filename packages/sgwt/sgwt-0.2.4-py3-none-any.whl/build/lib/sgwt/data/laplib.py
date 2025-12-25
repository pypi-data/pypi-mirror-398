from importlib_resources import files, as_file
from scipy.sparse import load_npz
from numpy import zeros

from dataclasses import dataclass


@dataclass(frozen=True)
class LapID:
    kind: str
    region: str

    def laplacian(self):
            # Weight Type
        B = self.kind

        # Name/Region
        N = self.region

        with as_file(files("sgwt").joinpath(f"data/{B}/{N}_{B}.npz")) as lap_path:
            return load_npz(lap_path)


#class LapLib(Enum):
DELAY_EASTWEST = LapID("DELAY", "EASTWEST")
DELAY_HAWAII = LapID("DELAY", "HAWAII")
DELAY_TEXAS = LapID("DELAY", "TEXAS")
DELAY_USA = LapID("DELAY", "USA")
DELAY_WECC = LapID("DELAY", "WECC")

IMPEDANCE_EASTWEST = LapID("IMPEDANCE", "EASTWEST")
IMPEDANCE_HAWAII = LapID("IMPEDANCE", "HAWAII")
IMPEDANCE_TEXAS = LapID("IMPEDANCE", "TEXAS")
IMPEDANCE_USA = LapID("IMPEDANCE", "USA")
IMPEDANCE_WECC = LapID("IMPEDANCE", "WECC")

LENGTH_EASTWEST = LapID("LENGTH", "EASTWEST")
LENGTH_HAWAII = LapID("LENGTH", "HAWAII")
LENGTH_TEXAS = LapID("LENGTH", "TEXAS")
LENGTH_USA = LapID("LENGTH", "USA")
LENGTH_WECC = LapID("LENGTH", "WECC")




def impulse(lap, n=0):
    '''
    Returns a numpy array dirac impulse at vertex n of compatible shape with L
    '''
    b = zeros((lap.shape[0],1))
    b[n] = 1

    return b