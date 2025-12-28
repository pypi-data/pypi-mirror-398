from ..quantities import Dimensionless
from .reaction import Reaction
from ..species import CO2, H2, C2H4, H2O, Ar


class CO2FTS(Reaction):
    def __init__(self, limiting_reactant="CO2"):
        self.components = {
            "CO2": CO2(),
            "H2": H2(),
            "C2H4": C2H4(),
            "H2O": H2O(),
            "inert": Ar(),
        }
        self.stoich_coeff = Dimensionless(
            si=[-2.0, -6.0, 1.0, 4.0, 0.0], keys=list(self.components.keys())
        )
        super().__init__(limiting_reactant=limiting_reactant)
