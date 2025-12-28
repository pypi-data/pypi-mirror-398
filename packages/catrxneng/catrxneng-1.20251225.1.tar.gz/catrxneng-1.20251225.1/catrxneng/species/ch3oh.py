from .species import Species
from ..quantities import Energy, Entropy, Temperature


class CH3OH(Species):
    CLASS = "alcohol"
    C_ATOMS = 1
    H_ATOMS = 4
    O_ATOMS = 1
    MOL_WEIGHT = 32
    HF_298_LIQ = Energy(kJmol=-238.4)
    S_298_LIQ = Entropy(JmolK=127.19)
    HF_298_GAS = Energy(kJmol=-205)
    S_298_GAS = Entropy(JmolK=239.7)
    DH_VAP_298 = HF_298_GAS - HF_298_LIQ
    DS_VAP_298 = S_298_GAS - S_298_LIQ
    # DH_VAP = Energy(kJmol=37.6)
    # DS_VAP = Entropy(JmolK=104.6)
    BOILING_TEMP = Temperature(C=64.7)

    # def __init__(self, T=None):
    #     super().__init__(T)

    # @classmethod
    # def Hf_gas_shomate(cls, T: Temperature) -> Energy:
    #     return cls.HF_298_GAS

    # @classmethod
    # def S_gas_shomate(cls, T: Temperature) -> Entropy:
    #     return cls.S_298_GAS

    @staticmethod
    def Cp_liq(T):
        from ..quantities import HeatCapacity

        # cp = 0.1955 * T.K + 22.419 # EngineeringToolbox.com
        cp = 0.2577 * T.K + 4.09  # NIST
        return HeatCapacity(JmolK=cp)

    @staticmethod
    def Cp_gas(T):
        from ..quantities import HeatCapacity

        cp = 0.0656 * T.K + 26.21  # NIST
        return HeatCapacity(JmolK=cp)
