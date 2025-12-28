from .species import Species
from ..quantities import Energy, Entropy, Temperature

from ..utils import equations as eqn


class H2O(Species):
    CLASS = "polar_solvent"
    H_ATOMS = 2
    O_ATOMS = 1
    MOL_WEIGHT = 18
    HF_298_LIQ = Energy(kJmol=-285.83)
    S_298_LIQ = Entropy(JmolK=69.95)
    HF_298_GAS = Energy(kJmol=-241.83)
    S_298_GAS = Entropy(JmolK=188.84)
    BOILING_TEMP = Temperature(C=100)
    # DH_VAP = Energy(kJmol=40.657)
    # DS_VAP = Entropy(JmolK=109)
    DH_VAP_298 = HF_298_GAS - HF_298_LIQ
    DS_VAP_298 = S_298_GAS - S_298_LIQ
    NIST_THERMO_PARAMS = [
        {
            "min_temp_K": 298,
            "max_temp_K": 500,
            "phase": "liq",
            "A": -203.606,
            "B": 1523.29,
            "C": -3196.413,
            "D": 2474.455,
            "E": 3.855326,
            "F": -256.5487,
            "G": -488.7163,
            "H": -285.8304,
        },
        {
            "min_temp_K": 500,
            "max_temp_K": 1700,
            "phase": "gas",
            "A": 30.09200,
            "B": 6.832514,
            "C": 6.793435,
            "D": -2.534480,
            "E": 0.082139,
            "F": -250.8810,
            "G": 223.3967,
            "H": -241.8264,
        },
    ]

    @classmethod
    def Hf_gas_shomate(cls, T):
        return eqn.Hf_shomate(T, cls.NIST_THERMO_PARAMS[1])

    @classmethod
    def S_gas_shomate(cls, T):
        return eqn.S_shomate(T, cls.NIST_THERMO_PARAMS[1])

    @classmethod
    def Cp_gas(cls, T):
        from ..quantities import HeatCapacity

        params = cls.NIST_THERMO_PARAMS[1]
        if params["min_temp_K"] <= T.K <= params["max_temp_K"]:
            return eqn.Cp_shomate(T, params)
        elif 298 <= T.K <= 500:
            # EngineeringToolbox.com
            # cp = 1e-6 * T.K**3 - 0.0013 * T.K**2 + 0.4405 * T.K + 25.914

            cp_JmolK = 35.2
            return HeatCapacity(JmolK=cp_JmolK)
        else:
            raise ValueError("Invalid temperature for H2O Cp_gas.")

    @classmethod
    def Cp_liq(cls, T):
        params = cls.NIST_THERMO_PARAMS[0]
        if params["min_temp_K"] <= T.K <= params["max_temp_K"]:
            return eqn.Cp_shomate(T, params)
        else:
            raise ValueError("Invalid temperature for H2O Cp_liq.")
