from .. import utils
from .species import Species
from ..quantities import Energy, Entropy


class NH3(Species):
    CLASS = "inorganic_hydride"
    H_ATOMS = 3
    N_ATOMS = 1
    MOL_WEIGHT = 17
    HF_298_GAS = Energy(kJmol=-45.9)
    S_298_GAS = Entropy(JmolK=192.77)
    NIST_THERMO_PARAMS = [
        {
            "min_temp_K": 298,
            "max_temp_K": 1400,
            "phase": "gas",
            "A": 19.99563,
            "B": 49.77119,
            "C": -15.37599,
            "D": 1.921168,
            "E": 0.189174,
            "F": -53.30667,
            "G": 203.8591,
            "H": -45.89806,
        }
    ]

    # @classmethod
    # def Hf_gas(cls, T):
    #     thermo_params = cls._get_thermo_params(T)
    #     return eqn.Hf_shomate(T, thermo_params)
    @classmethod
    def Hf_gas(cls, T):
        return eqn.Hf_shomate(T, cls.NIST_THERMO_PARAMS[0])

    @classmethod
    def S_gas(cls, T):
        thermo_params = cls._get_thermo_params(T)
        return eqn.S_shomate(T, thermo_params)

    @classmethod
    def Cp_gas(cls, T):
        thermo_params = cls._get_thermo_params(T)
        return eqn.Cp_shomate(T, thermo_params)
