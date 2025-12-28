import numpy as np
from ..reverse_kinetic_model import ReverseKineticModel
from .ghosh2021_no_h2_in_denom import Ghosh2021NoH2InDenom


class Ghosh2021WithoutSabatierRev(ReverseKineticModel):
    FORWARD_MODEL = Ghosh2021NoH2InDenom
    LIMITING_REACTANT = "ch3oh"

    @property
    def Keq(self):
        return 1.0 / self.forward_model.Keq
