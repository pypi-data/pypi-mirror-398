import numpy as np
from .co2_to_meoh import Co2ToMeoh
from .reaction import Reaction
from ..quantities import Dimensionless
from ..species import CH3OH, H2O, CO2, H2, Ar


class MeohToCo2(Reaction):
    COMPONENTS = {
        "ch3oh": CH3OH,
        "h2o": H2O,
        "co2": CO2,
        "h2": H2,
        "inert": Ar,
    }
    STOICH_COEFF = Dimensionless(
        si=[-1.0, -1.0, 1.0, 3.0, 0.0], keys=list(COMPONENTS.keys())
    )
    DEFAULT_LIMITING_REACTANT = "ch3oh"

    @staticmethod
    def Keq(T):
        return np.reciprocal(Co2ToMeoh.Keq(T))
