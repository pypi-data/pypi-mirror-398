from ..utils import equations as eqn
from .. import quantities as quant
from .species import Species


class CO(Species):
    CLASS = "carbon_oxide"
    C_ATOMS = 1
    O_ATOMS = 1
    MOL_WEIGHT = 28
    HF_298_GAS = quant.Energy(kJmol=-110.53)
    S_298_GAS = quant.Entropy(JmolK=197.66)
    NIST_THERMO_PARAMS = [
        {
            "min_temp_K": 298,
            "max_temp_K": 1300,
            "phase": "gas",
            "A": 25.56759,
            "B": 6.096130,
            "C": 4.054656,
            "D": -2.671301,
            "E": 0.131021,
            "F": -118.0089,
            "G": 227.3665,
            "H": -110.5271,
        }
    ]

    @classmethod
    def Hf_gas_shomate(cls, T):
        return eqn.Hf_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def S_gas_shomate(cls, T):
        return eqn.S_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def Cp_gas(cls, T) -> quant.HeatCapacity:
        return eqn.Cp_shomate(T, cls.NIST_THERMO_PARAMS[0])
