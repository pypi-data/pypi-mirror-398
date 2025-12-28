from scipy.optimize import fsolve
from .reaction import Reaction
from ..species import CO, H2, CH4, H2O, Ar
from ..quantities import Dimensionless


class COMethanation(Reaction):
    def __init__(self, limiting_reactant="CO"):
        self.components = {
            "CO": CO(),
            "H2": H2(),
            "CH4": CH4(),
            "H2O": H2O(),
            "inert": Ar(),
        }
        self.stoich_coeff = Dimensionless(
            si=[-1.0, -3.0, 1.0, 2.0, 0.0], keys=list(self.components.keys())
        )
        super().__init__(limiting_reactant=limiting_reactant)
