import numpy as np
from numpy.typing import NDArray

from ..kinetic_model import KineticModel
from ...utils import equations as eqn
from ... import reactions
from ... import species as species
from ... import quantities as quant


class CoToMeohWithDehydration(KineticModel):
    LIMITING_REACTANT = "co"
    T_REF = quant.Temperature(C=400)
    REACTANTS = {
        "co": species.CO2,
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
        "co_to_meoh": reactions.CoToMeoh,
        "meoh_dehydration": reactions.MeohDehydration,
    }
    # ORDER = np.array([0.78, 1.5])
    STOICH_COEFF = np.array(
        [
            [-1, -2, 1, 0, 0, 0],
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
        self.Keq_co_to_meoh = reactions.CoToMeoh.Keq(self.T)
        self.Keq_meoh_dehydration = reactions.MeohDehydration.Keq(self.T)
        self.Keq = np.array([self.Keq_co_to_meoh, self.Keq_meoh_dehydration])
        # self.k = np.array(
        #     [
        #         quant.RateConstant(
        #             molskgcatbar=kref,
        #             Ea=quant.Energy(kJmol=Ea),
        #             Tref=self.T_REF,
        #             order=order,
        #         )(self.T).molhgcatbar
        #         for kref, Ea, order in zip(self.kref, self.Ea, self.ORDER)
        #     ]
        # )

    # def calculate_rates(self, p: quant.Pressure) -> quant.ReactionRate:
    #     return quant.ReactionRate(
    #         molhgcat=self.rate_equations(p_array=p.bar), keys=self.comp_list()
    #     )

    # def rate_equations(self, p_array: np.ndarray) -> NDArray:
    #     """
    #     Calculate reaction rates from partial pressures.

    #     Pressure in bar
    #     Rates in mol/h/gcat

    #     Parameters
    #     ----------
    #     p_array : array-like
    #         Partial pressures. Can be:
    #         - 1D array of shape (7,) for a single point
    #         - 2D array of shape (7, n) for n points

    #     Returns
    #     -------
    #     rates : ndarray
    #         Reaction rates with the same shape as input.
    #         - 1D array of shape (7,) if input is 1D
    #         - 2D array of shape (7, n) if input is 2D
    #     """
    #     p_co2 = p_array[0]  # co2
    #     p_h2 = p_array[1]  # h2
    #     p_ch3oh = p_array[2]  # ch3oh
    #     p_h2o = p_array[3]  # h2o
    #     p_co = p_array[4]  # co

    #     base = 1 + self.Kads_co2 * p_co2 + np.sqrt(self.Kads_h2 * p_h2)
    #     inhib = base * base

    #     # Reaction 1: CO2 + 3H2 -> CH3OH + H2O (CO2-to-MeOH)
    #     p_h2_3 = p_h2 * p_h2 * p_h2
    #     beta_co2_to_meoh = 1 / self.Keq_co2_to_meoh * p_ch3oh * p_h2o / p_co2 / p_h2_3
    #     r1 = self.k[0] * p_h2**0.91 * p_co2**-0.13 * (1 - beta_co2_to_meoh)

    #     # Reaction 2: CO2 + H2 -> CO + H2O (RWGS)
    #     fwd = p_co2 * p_h2
    #     rev = p_co * p_h2o / self.Keq_rwgs
    #     numerator = self.k[1] * (fwd - rev) / np.sqrt(p_h2)
    #     r2 = numerator / inhib

    #     return np.array(
    #         [
    #             -r1 - r2,  # co2
    #             -3 * r1 - r2,  # h2
    #             r1,  # ch3oh
    #             r1 + r2,  # h2o
    #             r2,  # co
    #             0.0 * r1,  # inert
    #         ]
    #     )
