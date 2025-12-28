from .species import Species
from .. import quantities as quant
from ..utils import equations as eqn


class H2(Species):
    CLASS = "diatomic_gas"
    H_ATOMS = 2
    MOL_WEIGHT = 2
    HF_298_GAS = quant.Energy(kJmol=0)
    S_298_GAS = quant.Entropy(JmolK=130.68)
    NIST_THERMO_PARAMS = [
        {
            "min_temp_K": 298,
            "max_temp_K": 1000,
            "phase": "gas",
            "A": 33.066178,
            "B": -11.363417,
            "C": 11.432816,
            "D": -2.772874,
            "E": -0.158558,
            "F": -9.980797,
            "G": 172.707974,
            "H": 0,
        }
    ]

    @classmethod
    def Hf_gas_shomate(cls, T):
        return eqn.Hf_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def S_gas_shomate(cls, T):
        return eqn.S_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def Cp_gas(cls, T):
        return eqn.Cp_shomate(T, cls.NIST_THERMO_PARAMS[0])
