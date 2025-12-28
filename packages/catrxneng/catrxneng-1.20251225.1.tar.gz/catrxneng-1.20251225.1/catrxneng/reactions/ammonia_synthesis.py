from .reaction import Reaction
from .. import species
from ..quantities import Dimensionless


class AmmoniaSynthesis(Reaction):
    COMPONENTS = {
        "n2": species.N2,
        "h2": species.H2,
        "nh3": species.NH3,
        "inert": species.Inert,
    }
    # STOICH_COEFF = Unitless(si=[-0.5, -1.5, 1, 0], keys=list(COMPONENTS.keys()))
    STOICH_COEFF = Dimensionless(si=[-1, -3, 2, 0], keys=list(COMPONENTS.keys()))
    DEFAULT_LIMITING_REACTANT = "n2"

    @classmethod
    def dH_rxn_Cp(cls, T):
        return cls.dH_rxn_gas(T)

    @classmethod
    def dS_rxn(cls, T):
        return cls.dS_rxn_gas(T)
