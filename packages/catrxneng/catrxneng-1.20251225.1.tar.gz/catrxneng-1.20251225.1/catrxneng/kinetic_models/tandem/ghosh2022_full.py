import numpy as np

from ..kinetic_model import KineticModel
from ...utils import equations as eqn
from ...reactions import RWGS, Co2ToMeoh, Sabatier
from ... import quantities as quant


class Ghosh2022Full(KineticModel):
    def __init__(self, limiting_reactant="co2", T=None):
        self.Tref = quant.Temperature(C=320)
        self.components = [
            "co2",
            "h2",
            "ch3oh",
            "h2o",
            "co",
            "ch4",
            "c2h4",
            "c3h6",
            "c4h8",
            "c2h6",
            "c3h8",
            "c4h10",
            "c58",
            "c9+",
            "inert",
        ]
        self.f8 = {
            "c2h4": 5e-2,
            "c3h6": 1.0,
            "c4h8": 2.6e-1,
        }
        self.f9 = {
            "c2h4": 5.5e-1,
            "c3h6": 1.0,
            "c4h8": 4.5e-1,
        }
        self.kref = np.array(
            [
                8.8e-4,
                2.6e-3,
                1.4e-4,
                5.9e-1,
                7e-2,
                6e-1,
                5.9e-2,
                8e-2,
                8.3e-1,
                6e-2,
                8.2e-1,
            ]
        )
        self.Ea = np.array(
            [35.7, 54.5, 42.5, 70.0, 16.0, 17.0, 69.0, 109.0, 150.0, 170.0, 25.0]
        )
        self.order = np.array([2, 1.5, 1, 1, 2, 2, 2, 2, 1, 1, 2])
        self.COMP_IDX = {comp: i for i, comp in enumerate(self.components)}
        self.reactions = {
            "co2_to_meoh": Co2ToMeoh(),
            "rwgs": RWGS(),
            "sabatier": Sabatier(),
        }
        super().__init__(limiting_reactant, T)

    def compute_temp_dependent_constants(self):
        self.K_co2 = eqn.vant_hoff_eqn(
            6.7e-1, quant.Energy(kJmol=-2.6e1), self.T, self.Tref
        ).si
        self.K_h2 = eqn.vant_hoff_eqn(
            7e-1, quant.Energy(kJmol=-1.2e1), self.T, self.Tref
        ).si
        self.K_ch3oh = eqn.vant_hoff_eqn(
            1.3e1, quant.Energy(kJmol=-2e-1), self.T, self.Tref
        ).si
        self.K_co2_to_meoh = self.reactions["co2_to_meoh"].Keq(self.T)
        self.K_rwgs = self.reactions["rwgs"].Keq(self.T)
        self.K_sabatier = self.reactions["sabatier"].Keq(self.T)
        self.Keq = np.array([self.K_co2_to_meoh, self.K_rwgs, self.K_sabatier])
        self.k = np.array(
            [
                quant.RateConstant(
                    molskgcatbar=kref,
                    Ea=quant.Energy(kJmol=Ea),
                    Tref=self.Tref,
                    order=order,
                )(self.T).molhgcatbar
                for kref, Ea, order in zip(self.kref, self.Ea, self.order)
            ]
        )

    def get_reaction_rates_molhgcat(self, p_array):
        p_co2 = p_array[self.COMP_IDX["co2"]]
        p_h2 = p_array[self.COMP_IDX["h2"]]
        p_ch3oh = p_array[self.COMP_IDX["ch3oh"]]
        p_h2o = p_array[self.COMP_IDX["h2o"]]
        p_co = p_array[self.COMP_IDX["co"]]
        p_ch4 = p_array[self.COMP_IDX["ch4"]]
        p_c2h4 = p_array[self.COMP_IDX["c2h4"]]
        p_c3h6 = p_array[self.COMP_IDX["c3h6"]]
        p_c4h8 = p_array[self.COMP_IDX["c4h8"]]
        p_c58 = p_array[self.COMP_IDX["c58"]]

        n = 1

        # CO2 hydrogenation reactions
        inhib = (1 + self.K_co2 * p_co2 + np.sqrt(self.K_h2 * p_h2)) ** 2
        fwd = p_co2 * p_h2**3
        rev = p_ch3oh * p_h2o / self.K_co2_to_meoh
        numerator = self.k[1 - n] * (fwd - rev) / (p_h2**2)
        r1 = numerator / inhib

        fwd = p_co2 * p_h2
        rev = p_co * p_h2o / self.K_rwgs
        numerator = self.k[2 - n] * (fwd - rev) / np.sqrt(p_h2)
        r2 = numerator / inhib

        numerator = p_ch4 * p_h2o**2
        denom = p_co2 * p_h2**4 * self.K_sabatier
        frac = (1 - numerator / denom) / inhib
        r3 = self.k[3 - n] * np.sqrt(p_co2 * p_h2) * frac

        # MTO reactions
        inhib = 1 + self.K_ch3oh * (p_ch3oh + p_h2o)
        r4 = self.k[4 - n] * p_ch3oh / inhib
        r5 = self.k[5 - n] * p_ch3oh * p_c2h4 / inhib
        r6 = self.k[6 - n] * p_ch3oh * p_c3h6 / inhib
        r7 = self.k[7 - n] * p_ch3oh * p_c4h8 / inhib
        r8_1 = self.k[8 - n] * p_c2h4 * p_h2 / inhib * self.f8["c2h4"]
        r8_2 = self.k[8 - n] * p_c3h6 * p_h2 / inhib * self.f8["c3h6"]
        r8_3 = self.k[8 - n] * p_c4h8 * p_h2 / inhib * self.f8["c4h8"]
        r9_1 = self.k[9 - n] * p_c2h4 / inhib * self.f9["c2h4"]
        r9_2 = self.k[9 - n] * p_c3h6 / inhib * self.f9["c3h6"]
        r9_3 = self.k[9 - n] * p_c4h8 / inhib * self.f9["c4h8"]
        r10_1 = self.k[10 - n] * p_c58 / inhib * self.f9["c2h4"]
        r10_2 = self.k[10 - n] * p_c58 / inhib * self.f9["c3h6"]
        r10_3 = self.k[10 - n] * p_c58 / inhib * self.f9["c4h8"]
        r11_1 = self.k[11 - n] * p_c2h4 * p_c58 / inhib * self.f9["c2h4"]
        r11_2 = self.k[11 - n] * p_c3h6 * p_c58 / inhib * self.f9["c3h6"]
        r11_3 = self.k[11 - n] * p_c4h8 * p_c58 / inhib * self.f9["c4h8"]

        return np.array(
            [
                -r1 - r2 - r3,  # co2
                -3 * r1 - r2 - 4 * r3 - r8_1 - r8_2 - r8_3,  # h2
                r1 - 9 * r4 - 2 * r5 - 3 * r6 - 4 * r7,  # ch3oh
                r1 + r2 + 2 * r3 + 9 * r4 + 2 * r5 + 3 * r6 + 4 * r7,  # h2o
                r2,  # co
                r3,  # ch4
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
                0.0,  # inert
            ]
        )
