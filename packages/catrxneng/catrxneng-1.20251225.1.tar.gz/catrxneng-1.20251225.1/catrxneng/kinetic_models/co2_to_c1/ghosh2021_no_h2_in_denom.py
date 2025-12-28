import numpy as np

from .ghosh2021 import Ghosh2021


class Ghosh2021NoH2InDenom(Ghosh2021):

    def get_reaction_rates_molhgcat(self, p_array: np.ndarray) -> np.array:
        """
        Calculate reaction rates from partial pressures.

        Pressure in bar
        Rates in mol/h/gcat

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
        p_co = p_array[4]  # co

        base = 1 + self.K_co2 * p_co2 + np.sqrt(self.K_h2 * p_h2)
        inhib = base * base

        # Reaction 1: CO2 + 3H2 -> CH3OH + H2O (CO2-to-MeOH)
        fwd = p_co2 * p_h2
        rev = p_ch3oh * p_h2o / self.K_co2_to_meoh
        r1 = self.k[0] * (fwd - rev) / inhib

        # Reaction 2: CO2 + H2 -> CO + H2O (RWGS)
        fwd = p_co2 * np.sqrt(p_h2)
        rev = p_co * p_h2o / self.K_rwgs
        r2 = self.k[1] * (fwd - rev) / inhib

        return np.array(
            [
                -r1 - r2,  # co2
                -3 * r1 - r2,  # h2
                r1,  # ch3oh
                r1 + r2,  # h2o
                r2,  # co
                0.0 * r1,  # inert
            ]
        )
