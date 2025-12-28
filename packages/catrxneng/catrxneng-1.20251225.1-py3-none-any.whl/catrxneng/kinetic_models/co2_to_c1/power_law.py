import numpy as np
from numpy.typing import NDArray

from ..kinetic_model import KineticModel
from ...utils import equations as eqn
from ...reactions import RWGS, Co2ToMeoh
from ... import species as species
from ... import quantities as quant


class PowerLaw(KineticModel):
    KREF_UNITS = "molskgcatbar"
    EA_UNITS = "kJmol"
    LIMITING_REACTANT = "co2"
    T_REF = quant.Temperature(C=300)
    REACTANTS = {
        "co2": species.CO2,
        "h2": species.H2,
    }
    PRODUCTS = {
        "ch3oh": species.CH3OH,
        "h2o": species.H2O,
        "co": species.CO,
    }
    REACTIONS = {
        "co2_to_meoh": Co2ToMeoh,
        "rwgs": RWGS,
    }
    ORDER = np.array([0.78, 1.5])
    STOICH_COEFF = np.array(
        [
            [-1, -3, 1, 1, 0, 0],
            [-1, -1, 0, 1, 1, 0],
        ]
    )
    KREF = np.array([0.000373, 1.8e-3])
    EA = np.array([100.1, 54.5])
    K_ADS_REF_H2 = 0.76
    K_ADS_REF_CO2 = 0.79
    DH_ADS_H2_KJMOL = -12.5
    DH_ADS_CO2_KJMOL = -25.9

    def compute_temp_dependent_constants(self):
        self.Kads_h2 = eqn.vant_hoff_eqn(
            self.K_ADS_REF_H2,
            quant.Energy(kJmol=self.DH_ADS_H2_KJMOL),
            self.T,
            self.T_REF,
        )
        self.Kads_co2 = eqn.vant_hoff_eqn(
            self.K_ADS_REF_CO2,
            quant.Energy(kJmol=self.DH_ADS_CO2_KJMOL),
            self.T,
            self.T_REF,
        )
        self.Keq_co2_to_meoh = Co2ToMeoh.Keq(self.T)
        self.Keq_rwgs = RWGS.Keq(self.T)
        self.Keq = np.array([self.Keq_co2_to_meoh, self.Keq_rwgs])
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
        p_co = p_array[4]  # co

        base = 1 + self.Kads_co2 * p_co2 + np.sqrt(self.Kads_h2 * p_h2)
        inhib = base * base

        # Reaction 1: CO2 + 3H2 -> CH3OH + H2O (CO2-to-MeOH)
        p_h2_3 = p_h2 * p_h2 * p_h2
        beta_co2_to_meoh = 1 / self.Keq_co2_to_meoh * p_ch3oh * p_h2o / p_co2 / p_h2_3
        r1 = self.k[0] * p_h2**0.91 * p_co2**-0.13 * (1 - beta_co2_to_meoh)

        # Reaction 2: CO2 + H2 -> CO + H2O (RWGS)
        fwd = p_co2 * p_h2
        rev = p_co * p_h2o / self.Keq_rwgs
        numerator = self.k[1] * (fwd - rev) / np.sqrt(p_h2)
        r2 = numerator / inhib

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
