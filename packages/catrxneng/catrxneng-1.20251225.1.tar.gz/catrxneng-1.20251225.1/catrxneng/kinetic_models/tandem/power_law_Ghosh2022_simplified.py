import numpy as np

from ... import kinetic_models
from ... import species as species
from ..composite_kinetic_model import CompositeKineticModel
from ... import quantities as quant


class PowerLawGhosh2022Simplified(CompositeKineticModel):
    KREF_UNITS = "molskgcatbar"
    EA_UNITS = "kJmol"
    LIMITING_REACTANT = "co2"
    REACTANTS = {
        "co2": species.CO2,
        "h2": species.H2,
    }
    PRODUCTS = {
        "ch3oh": species.CH3OH,
        "h2o": species.H2O,
        "co": species.CO,
        "c2h4": species.C2H4,
        "c3h6": species.C3H6,
        "c4h8": species.C4H8,
        "c5h10": species.C5H10,
        "c2h6": species.C2H6,
        "c3h8": species.C3H8,
        "c4h10": species.C4H10,
        "c5h12": species.C5H12,
    }
    KINETIC_MODEL_CLASSES = [
        kinetic_models.co2_to_c1.PowerLaw,
        kinetic_models.mto.Ghosh2022Simplified,
    ]

    def get_2d_reaction_rate_array(self, p: quant.Pressure):
        return quant.ReactionRate(
            molhgcat=self.get_reaction_rates_molhgcat(p_array=p.bar),
            keys=self.comp_list(),
        )

    def get_reaction_rates_molhgcat(self, p_array):
        r1 = self.kinetic_models[0].get_reaction_rates_molhgcat(
            p_array[self.map_child_components_to_parent_components[0]]
        )
        r1 = r1 * self.catalyst_frac[0]
        r2 = self.kinetic_models[1].get_reaction_rates_molhgcat(
            p_array[self.map_child_components_to_parent_components[1]]
        )
        r2 = r2 * self.catalyst_frac[1]
        return np.array(
            [
                r1[0],  # co2
                r1[1] + r2[1],  # h2
                r1[2] + r2[0],  # ch3oh
                r1[3] + r2[2],  # h2o
                r1[4],  # co
                r2[3],  # c2h4
                r2[4],  # c3h6
                r2[5],  # c4h8
                r2[6],  # c5h10
                r2[7],  # c2h6
                r2[8],  # c3h8
                r2[9],  # c4h10
                r2[10],  # c5h12
                0.0 * r1[0],  # inert
            ]
        )
