import numpy as np
from numpy.typing import NDArray

from ..kinetic_model import KineticModel
from ... import species as species
from ...utils import equations as eqn
from ... import quantities as quant
from ...reactions import MTO


class Ghosh2022(KineticModel):
    T_REF = quant.Temperature(C=320)
    LIMITING_REACTANT = "ch3oh"
    REACTANTS = {
        "ch3oh": species.CH3OH,
        "h2": species.H2,
    }
    PRODUCTS = {
        "h2o": species.H2O,
        "c2h4": species.C2H4,
        "c3h6": species.C3H6,
        "c4h8": species.C4H8,
        "c2h6": species.C2H6,
        "c3h8": species.C3H8,
        "c4h10": species.C4H10,
        "c58": species.Species(C_ATOMS=6.5),
        "c9+": species.Species(C_ATOMS=10.5),
    }
    COMPONENTS = {**REACTANTS, **PRODUCTS, "inert": species.Inert}
    C_ATOMS = np.array([comp.C_ATOMS for comp in COMPONENTS.values()])
    REACTIONS = {"mto": MTO}
    F8 = {
        "c2h4": 5e-2,
        "c3h6": 1.0,
        "c4h8": 2.6e-1,
    }
    F9 = {
        "c2h4": 5.5e-1,
        "c3h6": 1.0,
        "c4h8": 4.5e-1,
    }
    # ORDER = np.array([1, 2, 2, 2, 2, 1, 1, 2])
    ORDER = np.array([1, 1, 1, 1, 1, 1, 1, 1])
    KREF_MOLSKGCATBAR = np.array(
        [5.9e-1, 7e-2, 6e-1, 5.9e-2, 8e-2, 8.3e-1, 6e-2, 8.2e-1]
    )
    EA_KJMOL = np.array([70.0, 16.0, 17.0, 69.0, 109.0, 150.0, 170.0, 25.0])
    K_ADS_REF_CH3OH = 1.3e1
    K_ADS_REF_H2O = 1.3e1
    DH_ADS_CH3OH_KJMOL = -2.0e-1
    DH_ADS_H2O_KJMOL = -2.0e-1

    def __init__(
        self,
        T: quant.Temperature | None = None,
        kref: np.typing.NDArray | None = None,
        Ea: quant.Energy | None = None,
    ):
        self.kref = kref
        if self.kref is None:
            self.kref = self.KREF_MOLSKGCATBAR
        self.Ea = Ea
        if self.Ea is None:
            self.Ea = self.EA_KJMOL
        super().__init__(T)

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
        self.k = np.array(
            [
                quant.RateConstant(
                    molskgcatbar=kref,
                    Ea=quant.Energy(kJmol=Ea),
                    Tref=self.T_REF,
                    order=order,
                )(self.T).molhgcatbar
                for kref, Ea, order in zip(self.kref, self.Ea, self.ORDER)
            ]
        )

    def get_2d_reaction_rate_array(self, p: quant.Pressure) -> quant.ReactionRate:
        return quant.ReactionRate(
            molhgcat=self.get_reaction_rates_molhgcat(p_array=p.bar),
            keys=self.comp_list,
        )

    def get_reaction_rates_molhgcat(self, p_array: NDArray) -> NDArray:
        p_ch3oh = p_array[0]
        p_h2 = p_array[1]
        p_h2o = p_array[2]
        p_c2h4 = p_array[3]
        p_c3h6 = p_array[4]
        p_c4h8 = p_array[5]
        p_c58 = p_array[9]

        inhib = 1 + self.Kads_ch3oh * p_ch3oh + self.Kads_h2o * p_h2o

        n = 4
        r4 = self.k[4 - n] * p_ch3oh / inhib
        r5 = self.k[5 - n] * p_ch3oh * p_c2h4 / inhib
        r6 = self.k[5 - n] * p_ch3oh * p_c3h6 / inhib
        r7 = self.k[5 - n] * p_ch3oh * p_c4h8 / inhib
        r8_1 = self.k[8 - n] * p_c2h4 * p_h2 / inhib * self.F8["c2h4"]
        r8_2 = self.k[8 - n] * p_c3h6 * p_h2 / inhib * self.F8["c3h6"]
        r8_3 = self.k[8 - n] * p_c4h8 * p_h2 / inhib * self.F8["c4h8"]
        r9_1 = self.k[9 - n] * p_c2h4 / inhib * self.F9["c2h4"]
        r9_2 = self.k[9 - n] * p_c3h6 / inhib * self.F9["c3h6"]
        r9_3 = self.k[9 - n] * p_c4h8 / inhib * self.F9["c4h8"]
        r10_1 = self.k[10 - n] * p_c58 / inhib * self.F9["c2h4"]
        r10_2 = self.k[10 - n] * p_c58 / inhib * self.F9["c3h6"]
        r10_3 = self.k[10 - n] * p_c58 / inhib * self.F9["c4h8"]
        r11_1 = self.k[11 - n] * p_c2h4 * p_c58 / inhib * self.F9["c2h4"]
        r11_2 = self.k[11 - n] * p_c3h6 * p_c58 / inhib * self.F9["c3h6"]
        r11_3 = self.k[11 - n] * p_c4h8 * p_c58 / inhib * self.F9["c4h8"]

        return np.array(
            [
                -9 * r4 - 2 * r5 - 3 * r6 - 4 * r7,  # ch3oh
                -1 * r8_1 - r8_2 - r8_3,  # h2
                9 * r4 + 2 * r5 + 3 * r6 + 4 * r7,  # h2o
                r4 + r5 - r8_1 - r9_1 + r10_1 - r11_1,  # c2h4
                r4 + r6 - r8_2 - r9_2 + r10_2 - r11_2,  # c3h6
                r4 + r7 - r8_3 - r9_3 + r10_3 - r11_3,  # c4h8
                r8_1,  # c2h6
                r8_2,  # c3h8
                r8_3,  # c4h10
                0.307 * r9_1
                + 0.461 * r9_2
                + 0.615 * r9_3
                - 0.307 * r10_1
                - 0.461 * r10_2
                - 0.615 * r10_3
                - r11_1
                - r11_2
                - r11_3,  # c58
                0.809 * r11_1 + 0.904 * r11_2 + r11_3,  # c9+
                0.0 * r4,  # inert
            ]
        )
