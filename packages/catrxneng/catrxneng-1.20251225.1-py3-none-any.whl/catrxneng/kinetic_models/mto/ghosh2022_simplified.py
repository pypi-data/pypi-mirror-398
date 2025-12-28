from typing import TYPE_CHECKING
import numpy as np
from numpy.typing import NDArray

from ... import species
from ... import reactions
from ..mto import MtoKineticModel
from ...utils import equations as eqn
from ... import quantities as quant

if TYPE_CHECKING:
    from ...reactors import Reactor


class Ghosh2022Simplified(MtoKineticModel):
    KREF_UNITS = "molskgcatbar"
    EA_UNITS = "kJmol"
    T_REF = quant.Temperature(C=320)
    REACTANTS = {
        "ch3oh": species.CH3OH,
        "h2": species.H2,
    }
    PRODUCTS = {
        "h2o": species.H2O,
        "c2h4": species.C2H4,
        "c3h6": species.C3H6,
        "c4h8": species.C4H8,
        "c5h10": species.C5H10,
        "c2h6": species.C2H6,
        "c3h8": species.C3H8,
        "c4h10": species.C4H10,
        "c5h12": species.C5H12,
    }
    REACTIONS = {"mto": reactions.MTO}
    ORDER = np.array([1, 1, 1, 1, 2, 2, 2, 2])
    KREF = np.array([5.9e-1, 7e-2, 6e-1, 5.9e-2, 8e-2, 8.3e-1, 6e-2, 8.2e-1])
    # KREF_MOLSKGCATBAR = np.array(
    #     [1000.0, 800.0, 600.0, 400.0, 0.001, 0.001, 0.001, 0.001]
    # )
    EA = np.array([70.0, 16.0, 17.0, 69.0, 109.0, 150.0, 170.0, 25.0])
    # EA_KJMOL = np.array(
    #     [
    #         70.0,
    #         70.0,
    #         70.0,
    #         70.0,
    #         110.0,
    #         110.0,
    #         110.0,
    #         110.0,
    #     ]
    # )
    K_ADS_REF_CH3OH = 1.3e1
    K_ADS_REF_H2O = 1.3e1
    DH_ADS_CH3OH_KJMOL = -2.0e-1
    DH_ADS_H2O_KJMOL = -2.0e-1

    def compute_temp_dependent_constants(self):
        self.Kads_ch3oh = eqn.vant_hoff_eqn(
            self.K_ADS_REF_CH3OH,
            quant.Energy(kJmol=self.DH_ADS_CH3OH_KJMOL),
            self.T,
            self.T_REF,
        ).si
        self.Kads_h2o = eqn.vant_hoff_eqn(
            self.K_ADS_REF_H2O,
            quant.Energy(kJmol=self.DH_ADS_H2O_KJMOL),
            self.T,
            self.T_REF,
        ).si
        self.k = self.get_rate_constant_array()

    def get_reaction_rates_molhgcat(self, p_array_bar: NDArray) -> NDArray:
        p_ch3oh = p_array_bar[0]
        p_h2 = p_array_bar[1]
        p_h2o = p_array_bar[2]
        p_c2h4 = p_array_bar[3]
        p_c3h6 = p_array_bar[4]
        p_c4h8 = p_array_bar[5]
        p_c5h10 = p_array_bar[6]
        inhib = 1 + self.Kads_ch3oh * p_ch3oh + self.Kads_h2o * p_h2o

        r_c2h4 = self.k[0] * p_ch3oh / inhib
        r_c3h6 = self.k[1] * p_ch3oh / inhib
        r_c4h8 = self.k[2] * p_ch3oh / inhib
        r_c5h10 = self.k[3] * p_ch3oh / inhib
        r_c2h6 = self.k[4] * p_c2h4 * p_h2 / inhib
        r_c3h8 = self.k[5] * p_c3h6 * p_h2 / inhib
        r_c4h10 = self.k[6] * p_c4h8 * p_h2 / inhib
        r_c5h12 = self.k[7] * p_c5h10 * p_h2 / inhib

        return np.array(
            [
                -2 * r_c2h4 - 3 * r_c3h6 - 4 * r_c4h8 - 5 * r_c5h10,  # ch3oh
                -r_c2h4 - r_c3h6 - r_c4h8 - r_c5h10,  # h2
                2 * r_c2h4 + 3 * r_c3h6 + 4 * r_c4h8 + 5 * r_c5h10,  # h2o
                r_c2h4 - r_c2h6,  # c2h4
                r_c3h6 - r_c3h8,  # c3h6
                r_c4h8 - r_c4h10,  # c4h8
                r_c5h10 - r_c5h12,  # c5h10
                r_c2h6,  # c2h6
                r_c3h8,  # c3h8
                r_c4h10,  # c4h10
                r_c5h12,  # c5h12
                0.0 * r_c2h4,  # inert
            ]
        )
