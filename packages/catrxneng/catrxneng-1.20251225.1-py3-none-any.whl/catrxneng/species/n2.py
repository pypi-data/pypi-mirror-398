from .. import utils
from .species import Species
from ..quantities import Energy, Entropy


class N2(Species):
    CLASS = "diatomic_gas"
    N_ATOMS = 2
    MOL_WEIGHT = 28
    HF_298_GAS = Energy(kJmol=0)
    S_298_GAS = Entropy(JmolK=191.61)
    NIST_THERMO_PARAMS = [
        {
            "min_temp_K": 100,
            "max_temp_K": 500,
            "phase": "gas",
            "A": 28.98641,
            "B": 1.853978,
            "C": -9.647459,
            "D": 16.63537,
            "E": 0.000117,
            "F": -8.671914,
            "G": 226.4168,
            "H": 0.0,
        },
        {
            "min_temp_K": 500,
            "max_temp_K": 2000,
            "phase": "gas",
            "A": 19.50583,
            "B": 19.88705,
            "C": -8.598535,
            "D": 1.369784,
            "E": 0.527601,
            "F": -4.935202,
            "G": 212.3900,
            "H": 0.0,
        },
    ]

    @classmethod
    def Hf_gas(cls, T):
        thermo_params = cls._get_thermo_params(T)
        return eqn.Hf_shomate(T, thermo_params)

    @classmethod
    def S_gas(cls, T):
        thermo_params = cls._get_thermo_params(T)
        return eqn.S_shomate(T, thermo_params)

    @classmethod
    def Cp_gas(cls, T):
        thermo_params = cls._get_thermo_params(T)
        return eqn.Cp_shomate(T, thermo_params)
