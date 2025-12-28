import numpy as np

from ..kinetic_model import KineticModel
from ... import quantities as quant
from ... import species as species
from ...reactions import MTO


class Lee2019(KineticModel):
    """
    kref in L/gcat/min
    conversion to normal units with moles and pressure instead of volume involves a
    calculation using the ideal gas law

    Ea in kJ/mol
    """

    TREF = quant.Temperature(C=450)
    COMPONENTS = {
        "ch4": species.CH4,
        "c2h4": species.C2H4,
        "c3h6": species.C3H6,
        "c3h8": species.C3H8,
        "c4h8": species.C4H8,
        "c4": species.Species(C_ATOMS=4),
        "c5+": species.Species(C_ATOMS=5),
        "ch3oh": species.CH3OH,
        "h2o": species.H2O,
        "inert": species.Ar,
    }
    C_ATOMS = np.array([comp.C_ATOMS for comp in COMPONENTS.values()])
    REACTIONS = {"mto": MTO}
    LIMITING_REACTANT = "ch3oh"

    def __init__(self, T=None, kref=None, Ea=None):
        self.kref = kref
        if self.kref is None:
            self.kref = np.array([0.16, 7.16, 7.35, 0.39, 2.26, 0.29, 0.9, 0.53, 0.36])
        self.Ea = Ea
        if self.Ea is None:
            self.Ea = np.array([71.7, 44.15, 14.02, 3.8, 6.24, 6.24, 10.0, 13.02, 4.04])
        self.K_h2o = 6.05
        super().__init__(T)

    def compute_temp_dependent_constants(self):
        self.k = np.array(
            [
                quant.RateConstant(
                    Lgcatmin=kref, Ea=quant.Energy(kJmol=Ea), Tref=self.TREF, order=1.0
                )(self.T).molhgcatbar
                for kref, Ea in zip(self.kref, self.Ea)
            ]
        )

    def get_2d_reaction_rate_array(self, p: quant.Pressure):
        return quant.ReactionRate(
            molhgcat=self.get_reaction_rates_molhgcat(p_array=p.bar),
            keys=self.comp_list(),
        )

    def get_reaction_rates_molhgcat(self, p_array):
        p_ch3oh = p_array[7]
        p_h2o = p_array[8]
        p_c2h4 = p_array[1]
        p_c3h6 = p_array[2]
        P = np.sum(p_array, axis=0)

        # water mol frac calculated based on partial pressure, or set to zero if total pressure is zero
        y_h2o = np.where(P == 0, 0, p_h2o / P)
        theta_w = 1 / (1 + self.K_h2o * y_h2o)

        r = np.array(
            [
                self.k[0] * theta_w * p_ch3oh,
                self.k[1] * theta_w * p_ch3oh,
                self.k[2] * theta_w * p_ch3oh,
                self.k[3] * theta_w * p_ch3oh,
                self.k[4] * theta_w * p_ch3oh,
                self.k[5] * theta_w * p_ch3oh,
                self.k[6] * theta_w * p_ch3oh,
                self.k[7] * theta_w * p_c2h4,
                self.k[8] * theta_w * p_c3h6,
            ]
        )
        return np.array(
            [
                r[0],  # ch4
                (r[1] - r[7]) / 2,  # c2h4
                (r[2] + r[7] - r[8]) / 3,  # c3h6
                r[3] / 3,  # c3h8
                (r[4] + r[8]) / 4,  # c4h8
                r[5] / 4,  # c4
                r[6] / 5,  # c5+
                np.sum([-r[i] for i in range(7)], axis=0),  # meoh
                np.sum([r[i] for i in range(7)], axis=0),  # h2o
                0.0 * r[0],  # inert
            ]
        )
