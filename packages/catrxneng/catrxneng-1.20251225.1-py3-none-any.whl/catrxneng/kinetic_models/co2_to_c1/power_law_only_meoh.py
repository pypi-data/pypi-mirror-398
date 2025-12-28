import numpy as np
from numpy.typing import NDArray

from ..kinetic_model import KineticModel
from ...utils import equations as eqn
from ...reactions import RWGS, Co2ToMeoh
from ... import species as species
from ... import quantities as quant


class PowerLawOnlyMeoh(KineticModel):
    KREF_UNITS = "molhgcatbar"
    EA_UNITS = "kJmol"
    LIMITING_REACTANT = "co2"
    T_REF = quant.Temperature(C=250)
    REACTANTS = {
        "co2": species.CO2,
        "h2": species.H2,
    }
    PRODUCTS = {
        "ch3oh": species.CH3OH,
        "h2o": species.H2O,
    }
    REACTIONS = {
        "co2_to_meoh": Co2ToMeoh,
    }
    ORDER = np.array([0.78])
    STOICH_COEFF = np.array(
        [
            [-1, -3, 1, 1, 0, 0],
        ]
    )
    KREF = np.array([0.00018])
    EA = np.array([100.1])

    def compute_temp_dependent_constants(self):
        self.Keq_co2_to_meoh = Co2ToMeoh.Keq(self.T)
        self.Keq = np.array([self.Keq_co2_to_meoh])
        self.k = self.get_rate_constant_array()

    def get_reaction_rates_molhgcat(self, p_array: np.ndarray) -> NDArray:
        """
        Calculate reaction rates from partial pressures.

        Parameters
        ----------
        p_array : array-like
            Partial pressures. Can be:
            - 1D array of shape (7,) for a single point
            - 2D array of shape (7, n) for n points

        Returns
        -------
        rates : ndarray
            Reaction rates with the same shape as input.
            - 1D array of shape (7,) if input is 1D
            - 2D array of shape (7, n) if input is 2D
        """
        p_co2 = p_array[0]  # co2
        p_h2 = p_array[1]  # h2
        p_ch3oh = p_array[2]  # ch3oh
        p_h2o = p_array[3]  # h2o

        # Reaction 1: CO2 + 3H2 -> CH3OH + H2O (CO2-to-MeOH)
        p_h2_3 = p_h2 * p_h2 * p_h2
        beta_co2_to_meoh = 1 / self.Keq_co2_to_meoh * p_ch3oh * p_h2o / p_co2 / p_h2_3
        r1 = self.k[0] * p_h2**0.91 * p_co2**-0.13 * (1 - beta_co2_to_meoh)

        return np.array(
            [
                -r1,  # co2
                -3 * r1,  # h2
                r1,  # ch3oh
                r1,  # h2o
                0.0 * r1,  # inert
            ]
        )
