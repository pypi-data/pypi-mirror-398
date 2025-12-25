'''

Library 

Access to laplacians, signals, and kernels.

TODO simplify access to files, too many steps at the moment

'''

from importlib_resources import files, as_file

from ..fitted.ration import VFKern

from numpy import load as npload
from json import load as jsonload
from scipy.sparse import load_npz
from dataclasses import dataclass




@dataclass(frozen=True)
class SignalID:
    kind: str
    region: str

    def get(self):
        
        # Weight Type
        B = self.kind

        # Name/Region
        N = self.region

        with as_file(files("sgwt").joinpath(f"library/data/SIGNALS/{N}_{B}.npz")) as sig_path:
            return npload(sig_path)


@dataclass(frozen=True)
class LapID:
    kind: str
    region: str

    def get(self):
            # Weight Type
        B = self.kind

        # Name/Region
        N = self.region

        with as_file(files("sgwt").joinpath(f"library/data/{B}/{N}_{B}.npz")) as lap_path:
            return load_npz(lap_path)


@dataclass(frozen=True)
class KernID:
    name: str

    def get(self):
        N = self.name

        with as_file(files("sgwt").joinpath(f"library/data/KERNELS/{N}.json")) as kern_path:
            with open(kern_path) as f:
                return VFKern.from_json(jsonload(f))

'''
KERNELS
'''
MEXICAN_HAT     = KernID("MEXICAN_HAT")
GAUSSIAN_WAV    = KernID("GAUSSIAN_WAV")
MODIFIED_MORLET = KernID("MODIFIED_MORLET")
SHANNON         = KernID("SHANNON")

'''
LAPLACIANS
'''
DELAY_EASTWEST = LapID("DELAY", "EASTWEST")    # VERIFIED
DELAY_HAWAII = LapID("DELAY", "HAWAII")        # VERIFIED
DELAY_TEXAS = LapID("DELAY", "TEXAS")          # VERIFIED
DELAY_USA = LapID("DELAY", "USA")              # VERIFIED
DELAY_WECC = LapID("DELAY", "WECC")

IMPEDANCE_EASTWEST = LapID("IMPEDANCE", "EASTWEST")
IMPEDANCE_HAWAII = LapID("IMPEDANCE", "HAWAII")
IMPEDANCE_TEXAS = LapID("IMPEDANCE", "TEXAS")   # VERIFIED
IMPEDANCE_USA = LapID("IMPEDANCE", "USA")
IMPEDANCE_WECC = LapID("IMPEDANCE", "WECC")     # VERIFIED

# BUG All length laps broken for some odd reason. Unsure what I did
LENGTH_EASTWEST = LapID("LENGTH", "EASTWEST")
LENGTH_HAWAII = LapID("LENGTH", "HAWAII")
LENGTH_TEXAS = LapID("LENGTH", "TEXAS")        
LENGTH_USA = LapID("LENGTH", "USA")         
LENGTH_WECC = LapID("LENGTH", "WECC")          

'''
SIGNALS
'''
COORD_EASTWEST = SignalID("COORDS", "EASTWEST")
COORD_HAWAII = SignalID("COORDS", "HAWAII")
COORD_TEXAS = SignalID("COORDS", "TEXAS")
COORD_USA = SignalID("COORDS", "USA")
