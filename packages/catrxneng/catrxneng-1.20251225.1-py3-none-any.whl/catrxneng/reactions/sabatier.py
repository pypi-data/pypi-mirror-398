import numpy as np

from .reaction import Reaction
from .. import species
from .. import quantities as quant


class Sabatier(Reaction):
    REACTANTS = {
        "co2": species.CO2,
        "h2": species.H2,
    }
    PRODUCTS = {
        "ch4": species.CH4,
        "h2o": species.H2O,
    }
    STOICH_COEFF = np.array([-1.0, -4.0, 1.0, 2.0, 0.0])
    DH_RXN_298 = (
        species.CH4.HF_298_GAS
        + 2 * species.H2O.HF_298_LIQ
        - species.CO2.HF_298_GAS
        - 4 * species.H2.HF_298_GAS
    )
    DS_RXN_298 = (
        species.CH4().S_298_GAS
        + 2 * species.H2O().S_298_LIQ
        - species.CO2().S_298_GAS
        - 4 * species.H2().S_298_GAS
    )
    DEFAULT_LIMITING_REACTANT = "co2"

    # def __init__(self, limiting_reactant="co2"):
    # self.components = {
    #     "co2": CO2(),
    #     "h2": H2(),
    #     "ch4": CH4(),
    #     "h2o": H2O(),
    #     "inert": Ar(),
    # }
    # self.stoich_coeff = Unitless(
    #     si=[-1.0, -4.0, 1.0, 2.0, 0.0], keys=list(self.components.keys())
    # )
    # super().__init__(limiting_reactant=limiting_reactant)

    # @staticmethod
    # def dCp_1(T_K):
    #     T = Temperature(K=T_K)
    #     dCp = CH4.Cp_gas(T) + 2 * H2O.Cp_liq(T) - CO2.Cp_gas(T) - 4 * H2.Cp_gas(T)
    #     return dCp.JmolK

    # @staticmethod
    # def dCp_2(T_K):
    #     T = Temperature(K=T_K)
    #     dCp = CH4.Cp_gas(T) + 2 * H2O.Cp_gas(T) - CO2.Cp_gas(T) - 4 * H2.Cp_gas(T)
    #     return dCp.JmolK

    # @classmethod
    # def dH_rxn_Cp(cls, T):
    #     Tb_h2o = H2O.BOILING_TEMP.K
    #     if T.K < Tb_h2o:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, T.K)[0]
    #         return Energy(Jmol=dHr)
    #     if T.K >= Tb_h2o:
    #         dHr = cls.DH_RXN_298.Jmol
    #         dHr += integrate.quad(cls.dCp_1, 298, Tb_h2o)[0]
    #         dHr += H2O.DH_VAP.Jmol
    #         dHr += integrate.quad(cls.dCp_2, Tb_h2o, T.K)[0]
    #         return Energy(Jmol=dHr)

    # @classmethod
    # def dS_rxn(cls, T):
    #     Tb_h2o = H2O.BOILING_TEMP.K
    #     integrand1 = lambda T_K: cls.dCp_1(T_K) / T_K
    #     integrand2 = lambda T_K: cls.dCp_2(T_K) / T_K
    #     if T.K < Tb_h2o:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, T.K)[0]
    #         return Entropy(JmolK=dSr)
    #     if T.K >= Tb_h2o:
    #         dSr = cls.DS_RXN_298.JmolK
    #         dSr += integrate.quad(integrand1, 298, Tb_h2o)[0]
    #         dSr += H2O.DS_VAP.JmolK
    #         dSr += integrate.quad(integrand2, Tb_h2o, T.K)[0]
    #         return Entropy(JmolK=dSr)
