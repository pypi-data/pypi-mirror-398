import numpy as np

from .reaction import Reaction
from .. import species
from ..quantities import Dimensionless
from .rwgs import RWGS


class WGS(Reaction):
    COMPONENTS = {
        "co": species.CO,
        "h2o": species.H2O,
        "co2": species.CO2,
        "h2": species.H2,
        "inert": species.Ar,
    }
    STOICH_COEFF = Dimensionless(
        si=[-1.0, -1.0, 1.0, 1.0, 0.0], keys=list(COMPONENTS.keys())
    )
    DEFAULT_LIMITING_REACTANT = "co"

    @staticmethod
    def Keq(T):
        # return 1 / RWGS.Keq(T)
        return np.reciprocal(RWGS.Keq(T))
