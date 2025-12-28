import numpy as np

from .reaction import Reaction
from .. import species


class FTS(Reaction):
    COMPONENTS = {
        "CO": species.CO,
        "H2": species.H2,
        "C2H4": species.C2H4,
        "H2O": species.H2O,
        "inert": species.Inert,
    }
    STOICH_COEFF = np.array([-2.0, -4.0, 1.0, 2.0, 0.0])
    DEFAULT_LIMITING_REACTANT = "co"
