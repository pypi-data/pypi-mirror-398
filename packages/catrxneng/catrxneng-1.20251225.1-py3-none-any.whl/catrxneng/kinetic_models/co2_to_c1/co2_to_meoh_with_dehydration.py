import numpy as np
from numpy.typing import NDArray

from ..kinetic_model import KineticModel
from ...utils import equations as eqn
from ... import reactions
from ... import species as species
from ... import quantities as quant


class Co2ToMeohWithDehydration(KineticModel):
    LIMITING_REACTANT = "co2"
    # T_REF = quant.Temperature(C=400)
    REACTANTS = {
        "co2": species.CO2,
        "h2": species.H2,
    }
    PRODUCTS = {
        "ch3oh": species.CH3OH,
        "h2o": species.H2O,
        "dme": species.DME,
    }
    COMPONENTS = {**REACTANTS, **PRODUCTS, "inert": species.Inert}
    C_ATOMS = np.array([comp.C_ATOMS for comp in COMPONENTS.values()])
    REACTIONS = {
        "co2_to_meoh": reactions.Co2ToMeoh,
        "meoh_dehydration": reactions.MeohDehydration,
    }
    # ORDER = np.array([0.78, 1.5])
    STOICH_COEFF = np.array(
        [
            [-1, -3, 1, 1, 0, 0],
            [0, 0, -2, 1, 1, 0],
        ]
    )
    # KREF_MOLSKGCATBAR = np.array([0.000373, 1.8e-3])
    # EA_KJMOL = np.array([100.1, 54.5])

    def __init__(
        self,
        T: quant.Temperature | None = None,
        kref: NDArray | None = None,
        Ea: quant.Energy | None = None,
    ):
        self.kref = kref
        # if self.kref is None:
        #     self.kref = self.KREF_MOLSKGCATBAR
        self.Ea = Ea
        # if self.Ea is None:
        #     self.Ea = self.EA_KJMOL
        super().__init__(T)

    def compute_temp_dependent_constants(self):
        self.Keq_co2_to_meoh = reactions.Co2ToMeoh.Keq(self.T)
        self.Keq_meoh_dehydration = reactions.MeohDehydration.Keq(self.T)
        self.Keq = np.array([self.Keq_co2_to_meoh, self.Keq_meoh_dehydration])
