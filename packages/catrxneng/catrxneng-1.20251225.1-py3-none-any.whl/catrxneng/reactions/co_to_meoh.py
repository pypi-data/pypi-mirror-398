import numpy as np

from .reaction import Reaction
from .. import species
from .. import quantities as quant


class CoToMeoh(Reaction):
    EQUATION = "CO + 2H₂ ⇌ CH₃OH"
    COMPONENTS = {
        "co": species.CO,
        "h2": species.H2,
        "ch3oh": species.CH3OH,
        "inert": species.Ar,
    }
    STOICH_COEFF = np.array([-1.0, -2.0, 1.0, 0.0])
    DEFAULT_LIMITING_REACTANT = "co"
    DH_RXN_298 = (
        species.CH3OH.HF_298_LIQ - species.CO.HF_298_GAS - 2 * species.H2.HF_298_GAS
    )
    DS_RXN_298 = (
        species.CH3OH.S_298_LIQ - species.CO.S_298_GAS - 2 * species.H2.S_298_GAS
    )

    # @staticmethod
    # def dCp_1(T_K):
    #     T = quant.Temperature(K=T_K)
    #     dCp = species.CH3OH.Cp_liq(T) - species.CO.Cp_gas(T) - 2 * species.H2.Cp_gas(T)
    #     return dCp.JmolK

    # @staticmethod
    # def dCp_2(T_K):
    #     T = quant.Temperature(K=T_K)
    #     dCp = species.CH3OH.Cp_gas(T) - species.CO2.Cp_gas(T) - 2 * species.H2.Cp_gas(T)
    #     return dCp.JmolK

    # @classmethod
    # def dH_rxn_Cp(cls, T):
    #     Tb_ch3oh = species.CH3OH.BOILING_TEMP.K
    #     if T.K < Tb_ch3oh:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, T.K)[0]
    #         return quant.Energy(Jmol=dHr)
    #     else:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, Tb_ch3oh)[0]
    #         dHr += species.CH3OH.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_2, Tb_ch3oh, T.K)[0]
    #         return quant.Energy(Jmol=dHr)

    # @classmethod
    # def dS_rxn(cls, T):
    #     Tb_ch3oh = species.CH3OH.BOILING_TEMP.K

    #     def integrand1(T_K):
    #         return cls.dCp_1(T_K) / T_K

    #     def integrand2(T_K):
    #         return cls.dCp_2(T_K) / T_K

    #     if T.K < Tb_ch3oh:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, T.K)[0]
    #         return quant.Entropy(JmolK=dSr)
    #     else:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, Tb_ch3oh)[0]
    #         dSr += species.CH3OH.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand2, Tb_ch3oh, T.K)[0]
    #         return quant.Entropy(JmolK=dSr)
