import numpy as np
import scipy.integrate as integrate

from .. import quantities as quant, species
from .reaction import Reaction


class RWGS(Reaction):
    REACTANTS = {
        "co2": species.CO2,
        "h2": species.H2,
    }
    PRODUCTS = {
        "co": species.CO,
        "h2o": species.H2O,
    }
    STOICH_COEFF = np.array([-1.0, -1.0, 1.0, 1.0, 0.0])
    DEFAULT_LIMITING_REACTANT = "co2"
    DH_RXN_298 = (
        species.CO.HF_298_GAS
        + species.H2O.HF_298_LIQ
        - species.CO2.HF_298_GAS
        - species.H2.HF_298_GAS
    )
    DS_RXN_298 = (
        species.CO.S_298_GAS
        + species.H2O.S_298_LIQ
        - species.CO2.S_298_GAS
        - species.H2.S_298_GAS
    )

    # @staticmethod
    # def dCp_1(T_K):
    #     T = quant.Temperature(K=T_K)
    #     dCp = (
    #         species.CO.Cp_gas(T)
    #         + species.H2O.Cp_liq(T)
    #         - species.CO2.Cp_gas(T)
    #         - species.H2.Cp_gas(T)
    #     )
    #     return dCp.JmolK

    # @staticmethod
    # def dCp_gas_JmolK(T_K):
    #     T = quant.Temperature(K=T_K)
    #     dCp = (
    #         species.CO.Cp_gas(T)
    #         + species.H2O.Cp_gas(T)
    #         - species.CO2.Cp_gas(T)
    #         - species.H2.Cp_gas(T)
    #     )
    #     return dCp.JmolK

    # @classmethod
    # def dH_rxn(cls, T: quant.Temperature) -> quant.Energy:
    #     if T.K > species.H2O.BOILING_TEMP.K:
    #         dHr_Jmol = (
    #             cls.DH_RXN_298_GAS.Jmol + integrate.quad(cls.dCp_gas_JmolK, 298, T.K)[0]
    #         )
    #         return quant.Energy(Jmol=dHr_Jmol)
    #     raise ValueError("Temperature too low.")

    # @classmethod
    # def dS_rxn(cls, T: quant.Temperature) -> quant.Entropy:
    #     if T.K > species.H2O.BOILING_TEMP.K:
    #         integrand = lambda T_K: cls.dCp_gas_JmolK(T_K) / T_K
    #         dSr_JmolK = (
    #             cls.DS_RXN_298_GAS.JmolK + integrate.quad(integrand, 298, T.K)[0]
    #         )
    #         return quant.Entropy(JmolK=dSr_JmolK)
    #     raise ValueError("Temperature too low.")

    # @classmethod
    # def dH_rxn_Cp(cls, T):
    #     Tb_h2o = species.H2O.BOILING_TEMP.K
    #     if T.K < Tb_h2o:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, T.K)[0]
    #         return quant.Energy(Jmol=dHr)
    #     if T.K >= Tb_h2o:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, Tb_h2o)[0]
    #         dHr += species.H2O.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_2, Tb_h2o, T.K)[0]
    #         return quant.Energy(Jmol=dHr)

    # @classmethod
    # def dS_rxn(cls, T):
    #     Tb_h2o = species.H2O.BOILING_TEMP.K
    #     integrand1 = lambda T_K: cls.dCp_1(T_K) / T_K
    #     integrand2 = lambda T_K: cls.dCp_2(T_K) / T_K
    #     if T.K < Tb_h2o:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, T.K)[0]
    #         return quant.Entropy(JmolK=dSr)
    #     if T.K >= Tb_h2o:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, Tb_h2o)[0]
    #         dSr += species.H2O.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand2, Tb_h2o, T.K)[0]
    #         return quant.Entropy(JmolK=dSr)
