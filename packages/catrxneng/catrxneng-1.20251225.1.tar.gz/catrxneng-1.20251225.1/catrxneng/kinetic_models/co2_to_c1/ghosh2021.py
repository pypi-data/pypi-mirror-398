import numpy as np
from numpy.typing import NDArray

from ..kinetic_model import KineticModel
from ...utils import equations as eqn
from ...reactions import RWGS, Co2ToMeoh, Sabatier
from ... import quantities as quant
from ... import species as species


class Ghosh2021(KineticModel):
    KREF_UNITS = "molskgcatbar"
    EA_UNITS = "kJmol"
    T_REF = quant.Temperature(C=300)
    LIMITING_REACTANT = "co2"
    REACTANTS = {
        "co2": species.CO2,
        "h2": species.H2,
    }
    PRODUCTS = {
        "ch3oh": species.CH3OH,
        "h2o": species.H2O,
        "co": species.CO,
        "ch4": species.CH4,
    }
    REACTIONS = {
        "co2_to_meoh": Co2ToMeoh,
        "rwgs": RWGS,
        "sabatier": Sabatier,
    }
    ORDER = np.array([2.0, 1.5, 1.0])
    STOICH_COEFF = np.array(
        [
            [-1, -3, 1, 1, 0, 0, 0],
            [-1, -1, 0, 1, 1, 0, 0],
            [-1, -4, 0, 2, 0, 1, 0],
        ]
    )
    KREF = np.array([6.9e-4, 1.8e-3, 1.1e-4])
    EA = np.array([35.7, 54.5, 42.5])
    K_ADS_REF_H2 = 0.76
    K_ADS_REF_CO2 = 0.79
    DH_ADS_H2_KJMOL = -12.5
    DH_ADS_CO2_KJMOL = -25.9

    def __init__(
        self,
        site_model="single",
        T: quant.Temperature | None = None,
        kref: np.typing.NDArray | None = None,
        Ea: quant.Energy | None = None,
    ):
        self.site_model = site_model
        super().__init__(T=T, kref=kref, Ea=Ea)

    def compute_temp_dependent_constants(self):
        self.K_h2 = eqn.vant_hoff_eqn(
            self.K_ADS_REF_H2,
            quant.Energy(kJmol=self.DH_ADS_H2_KJMOL),
            self.T,
            self.T_REF,
        )
        self.K_co2 = eqn.vant_hoff_eqn(
            self.K_ADS_REF_CO2,
            quant.Energy(kJmol=self.DH_ADS_CO2_KJMOL),
            self.T,
            self.T_REF,
        )
        self.K_co2_to_meoh = Co2ToMeoh.Keq(self.T)
        self.K_rwgs = RWGS.Keq(self.T)
        self.K_sabatier = Sabatier.Keq(self.T)
        self.Keq = np.array([self.K_co2_to_meoh, self.K_rwgs, self.K_sabatier])
        self.k = self.get_rate_constant_array()

    def get_reaction_rates_molhgcat(self, p_array: np.ndarray) -> np.ndarray:
        """
        Calculate reaction rates from partial pressures.
        """

        p_co2 = p_array[0]  # co2
        p_h2 = p_array[1]  # h2
        p_ch3oh = p_array[2]  # ch3oh
        p_h2o = p_array[3]  # h2o
        p_co = p_array[4]  # co
        p_ch4 = p_array[5]  # ch4

        base = 1 + self.K_co2 * p_co2 + np.sqrt(self.K_h2 * p_h2)
        inhib = base * base

        # Reaction 1: CO2 + 3H2 -> CH3OH + H2O (CO2-to-MeOH)
        fwd = p_co2 * p_h2 * p_h2 * p_h2
        rev = p_ch3oh * p_h2o / self.K_co2_to_meoh
        numerator = self.k[0] * (fwd - rev) / (p_h2 * p_h2)
        r1 = numerator / inhib

        # Reaction 2: CO2 + H2 -> CO + H2O (RWGS)
        fwd = p_co2 * p_h2
        rev = p_co * p_h2o / self.K_rwgs
        numerator = self.k[1] * (fwd - rev) / np.sqrt(p_h2)
        r2 = numerator / inhib

        # Reaction 3: CO2 + 4H2 -> CH4 + 2H2O (Sabatier)
        numerator = p_ch4 * (p_h2o * p_h2o)
        p_h2_4 = p_h2 * p_h2 * p_h2 * p_h2
        denom = p_co2 * p_h2_4 * self.K_sabatier

        if np.ndim(denom) == 0:
            if denom == 0:
                frac = 0.0
            else:
                div = numerator / denom
                frac = (1.0 - div) / inhib
        else:
            div = np.zeros_like(denom, dtype=float)
            np.divide(numerator, denom, out=div, where=denom != 0)
            frac = np.zeros_like(div, dtype=float)
            np.divide(1.0 - div, inhib, out=frac, where=denom != 0)

        r3 = self.k[2] * np.sqrt(p_co2 * p_h2) * frac

        return np.array(
            [
                -r1 - r2 - r3,  # co2
                -3 * r1 - r2 - 4 * r3,  # h2
                r1,  # ch3oh
                r1 + r2 + 2 * r3,  # h2o
                r2,  # co
                r3,  # ch4
                0.0 * r1,  # inert
            ]
        )
