from .species import Species
from ..utils import equations as eqn
from .. import quantities as quant


class CH4(Species):
    CLASS = "alkane"
    C_ATOMS = 1
    H_ATOMS = 4
    MOL_WEIGHT = 16
    HF_298_GAS = quant.Energy(kJmol=-74.6)
    S_298_GAS = quant.Entropy(JmolK=186.3)
    NIST_THERMO_PARAMS = [
        {
            "min_temp_K": 298,
            "max_temp_K": 1300,
            "phase": "gas",
            "A": -0.703029,
            "B": 108.4773,
            "C": -42.52157,
            "D": 5.862788,
            "E": 0.678565,
            "F": -76.84376,
            "G": 158.7163,
            "H": -74.87310,
        }
    ]

    @classmethod
    def Hf_gas(cls, T):
        return eqn.Hf_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def S_gas(cls, T):
        return eqn.S_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def Cp_gas(cls, T):
        return eqn.Cp_shomate(T, cls.NIST_THERMO_PARAMS[0])
