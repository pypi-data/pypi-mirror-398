from .species import Species
from .. import quantities as quant


class DME(Species):
    CLASS = "ether"
    C_ATOMS = 2
    H_ATOMS = 6
    O_ATOMS = 1
    MOL_WEIGHT = 46.069
    HF_298_GAS = quant.Energy(kJmol=-184.1)
    S_298_GAS = quant.Entropy(JmolK=266.5)
    # S_298_LIQ = quant.Entropy(JmolK=146.57)
    # DS_VAP = quant.Entropy(JmolK=86.61)
    # S_298_GAS = S_298_LIQ + DS_VAP

    # @classmethod
    # def Hf_gas(cls, T: quant.Temperature) -> quant.Energy:
    #     return cls.HF_298_GAS

    # @classmethod
    # def S_gas(cls, T: quant.Temperature) -> quant.Entropy:
    #     return cls.S_298_GAS

    @classmethod
    def Cp_gas(cls, T: quant.Temperature) -> quant.HeatCapacity:
        if 298 <= T.K <= 1000:
            cp = -5e-5 * T.K * T.K + 0.173 * T.K + 18.717  # NIST
            return quant.HeatCapacity(JmolK=cp)
        raise ValueError("Temperature is out of range.")
