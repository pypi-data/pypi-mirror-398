import numpy as np

from .reaction import Reaction
from .. import species


class MeohDehydration(Reaction):
    EQUATION = "2CH₃OH ⇌ CH₃OCH₃ + H₂O"
    REACTANTS = {
        "ch3oh": species.CH3OH,
    }
    PRODUCTS = {
        "dme": species.DME,
        "h2o": species.H2O,
    }
    STOICH_COEFF = np.array([-2.0, 1.0, 1.0, 0.0])
    DEFAULT_LIMITING_REACTANT = "ch3oh"
    DH_RXN_298 = (
        species.DME.HF_298_GAS + species.H2O.HF_298_LIQ - 2 * species.CH3OH.HF_298_LIQ
    )
    DS_RXN_298 = (
        species.DME.S_298_GAS + species.H2O.S_298_LIQ - 2 * species.CH3OH.S_298_LIQ
    )

    # @staticmethod
    # def dCp_1(T_K):
    #     T = quant.Temperature(K=T_K)
    #     dCp = (
    #         species.DME.Cp_gas(T) + species.H2O.Cp_liq(T) - 2 * species.CH3OH.Cp_liq(T)
    #     )
    #     return dCp.JmolK

    # @staticmethod
    # def dCp_2(T_K):
    #     T = quant.Temperature(K=T_K)
    #     dCp = (
    #         species.DME.Cp_gas(T) + species.H2O.Cp_liq(T) - 2 * species.CH3OH.Cp_gas(T)
    #     )
    #     return dCp.JmolK

    # @staticmethod
    # def dCp_gas_JmolK(T_K):
    #     T = quant.Temperature(K=T_K)
    #     dCp = (
    #         species.DME.Cp_gas(T) + species.H2O.Cp_gas(T) - 2 * species.CH3OH.Cp_gas(T)
    #     )
    #     return dCp.JmolK

    # @classmethod
    # def dH_rxn_Cp(cls, T: quant.Temperature) -> quant.Energy:
    #     Tb_ch3oh = species.CH3OH.BOILING_TEMP.K
    #     Tb_h2o = species.H2O.BOILING_TEMP.K
    #     if T.K < Tb_ch3oh:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, T.K)[0]
    #         return quant.Energy(Jmol=dHr)
    #     elif Tb_ch3oh <= T.K < Tb_h2o:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, Tb_ch3oh)[0]
    #         dHr -= 2 * species.CH3OH.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_2, Tb_ch3oh, T.K)[0]
    #         return quant.Energy(Jmol=dHr)
    #     else:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, Tb_ch3oh)[0]
    #         dHr -= 2 * species.CH3OH.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_2, Tb_ch3oh, Tb_h2o)[0]
    #         dHr += species.H2O.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_3, Tb_h2o, T.K)[0]
    #         return quant.Energy(Jmol=dHr)

    # @classmethod
    # def dS_rxn(cls, T: quant.Temperature) -> quant.Entropy:
    #     Tb_ch3oh = species.CH3OH.BOILING_TEMP.K
    #     Tb_h2o = species.H2O.BOILING_TEMP.K
    #     integrand1 = lambda T_K: cls.dCp_1(T_K) / T_K
    #     integrand2 = lambda T_K: cls.dCp_2(T_K) / T_K
    #     integrand3 = lambda T_K: cls.dCp_3(T_K) / T_K
    #     if T.K < Tb_ch3oh:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, T.K)[0]
    #         return quant.Entropy(JmolK=dSr)
    #     elif Tb_ch3oh <= T.K < Tb_h2o:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, Tb_ch3oh)[0]
    #         dSr -= 2 * species.CH3OH.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand2, Tb_ch3oh, T.K)[0]
    #         return quant.Entropy(JmolK=dSr)
    #     else:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, Tb_ch3oh)[0]
    #         dSr -= 2 * species.CH3OH.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand2, Tb_ch3oh, Tb_h2o)[0]
    #         dSr += species.H2O.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand3, Tb_h2o, T.K)[0]
    #         return quant.Entropy(JmolK=dSr)
