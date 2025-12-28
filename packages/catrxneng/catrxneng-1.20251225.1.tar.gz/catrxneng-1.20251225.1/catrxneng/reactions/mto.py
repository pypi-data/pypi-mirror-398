import scipy.integrate as integrate

from .reaction import Reaction
from ..quantities import Dimensionless
from ..species import CH3OH, C2H4, H2O, Ar


class MTO(Reaction):
    COMPONENTS = {
        "ch3oh": CH3OH,
        "c2h4": C2H4,
        "h2o": H2O,
        "inert": Ar,
    }
    STOICH_COEFF = Dimensionless(si=[-2.0, 1.0, 2.0, 0.0], keys=list(COMPONENTS.keys()))
    DEFAULT_LIMITING_REACTANT = "ch3oh"

    DH_RXN_298 = C2H4.HF_298_GAS + 2 * H2O.HF_298_LIQ - 2 * CH3OH.HF_298_LIQ
    DS_RXN_298 = C2H4.S_298_GAS + 2 * H2O.S_298_LIQ - 2 * CH3OH.S_298_LIQ
    DH_RXN_298_GAS = C2H4.HF_298_GAS + 2 * H2O.HF_298_GAS - 2 * CH3OH.HF_298_GAS
    DS_RXN_298_GAS = C2H4.S_298_GAS + 2 * H2O.S_298_GAS - 2 * CH3OH.S_298_GAS

    # @staticmethod
    # def dCp_1(T_K):
    #     T = Temperature(K=T_K)
    #     dCp = CH3OH.Cp_liq(T) + H2O.Cp_liq(T) - CO2.Cp_gas(T) - 3 * H2.Cp_gas(T)
    #     return dCp.JmolK

    # @staticmethod
    # def dCp_2(T_K):
    #     T = Temperature(K=T_K)
    #     dCp = CH3OH.Cp_gas(T) + H2O.Cp_liq(T) - CO2.Cp_gas(T) - 3 * H2.Cp_gas(T)
    #     return dCp.JmolK

    # @staticmethod
    # def dCp_3(T_K):
    #     T = Temperature(K=T_K)
    #     dCp = CH3OH.Cp_gas(T) + H2O.Cp_gas(T) - CO2.Cp_gas(T) - 3 * H2.Cp_gas(T)
    #     return dCp.JmolK

    # @classmethod
    # def dH_rxn(cls, T):
    #     Tb_ch3oh = CH3OH.BOILING_TEMP.K
    #     Tb_h2o = H2O.BOILING_TEMP.K
    #     if T.K < Tb_ch3oh:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, T.K)[0]
    #         return Energy(Jmol=dHr)
    #     if Tb_ch3oh <= T.K < Tb_h2o:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, Tb_ch3oh)[0]
    #         dHr += CH3OH.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_2, Tb_ch3oh, T.K)[0]
    #         return Energy(Jmol=dHr)
    #     if T.K >= Tb_h2o:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, Tb_ch3oh)[0]
    #         dHr += CH3OH.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_2, Tb_ch3oh, Tb_h2o)[0]
    #         dHr += H2O.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_3, Tb_h2o, T.K)[0]
    #         return Energy(Jmol=dHr)

    # @classmethod
    # def dS_rxn(cls, T):
    #     Tb_ch3oh = CH3OH.BOILING_TEMP.K
    #     Tb_h2o = H2O.BOILING_TEMP.K
    #     integrand1 = lambda T_K: cls.dCp_1(T_K) / T_K
    #     integrand2 = lambda T_K: cls.dCp_2(T_K) / T_K
    #     integrand3 = lambda T_K: cls.dCp_3(T_K) / T_K
    #     if T.K < Tb_ch3oh:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, T.K)[0]
    #         return Entropy(JmolK=dSr)
    #     if Tb_ch3oh <= T.K < Tb_h2o:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, Tb_ch3oh)[0]
    #         dSr += CH3OH.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand2, Tb_ch3oh, T.K)[0]
    #         return Entropy(JmolK=dSr)
    #     if T.K >= Tb_h2o:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, Tb_ch3oh)[0]
    #         dSr += CH3OH.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand2, Tb_ch3oh, Tb_h2o)[0]
    #         dSr += H2O.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand3, Tb_h2o, T.K)[0]
    #         return Entropy(JmolK=dSr)
