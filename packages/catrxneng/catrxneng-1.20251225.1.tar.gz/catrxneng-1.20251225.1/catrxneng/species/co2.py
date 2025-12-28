from ..utils import equations as eqn
from .. import quantities as quant
from .species import Species


class CO2(Species):
    CLASS = "carbon_oxide"
    C_ATOMS = 1
    O_ATOMS = 2
    MOL_WEIGHT = 44
    HF_298_GAS = quant.Energy(kJmol=-393.51)
    S_298_GAS = quant.Entropy(JmolK=213.79)
    NIST_THERMO_PARAMS = [
        {
            "min_temp_K": 298,
            "max_temp_K": 1200,
            "phase": "gas",
            "A": 24.99735,
            "B": 55.18696,
            "C": -33.69137,
            "D": 7.948387,
            "E": -0.136638,
            "F": -403.6075,
            "G": 228.2431,
            "H": -393.5224,
        }
    ]

    @classmethod
    def Hf_gas_shomate(cls, T) -> quant.Energy:
        return eqn.Hf_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def S_gas_shomate(cls, T) -> quant.Entropy:
        return eqn.S_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def Cp_gas(cls, T) -> quant.HeatCapacity:
        return eqn.Cp_shomate(T, cls.NIST_THERMO_PARAMS[0])
