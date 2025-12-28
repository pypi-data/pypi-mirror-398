import numpy as np
import pandas as pd

from ..kinetic_model import KineticModel
from ... import quantities as quant


class MtoKineticModel(KineticModel):
    LIMITING_REACTANT = "ch3oh"

    @classmethod
    def compute_olefin_paraffin_c_basis_flow_rates(
        cls, F: quant.MolarFlowRate
    ) -> pd.DataFrame:
        df = pd.DataFrame()
        olefins = {
            id: species
            for id, species in cls.PRODUCTS.items()
            if species.CLASS == "alkene"
        }
        paraffins = {
            id: species
            for id, species in cls.PRODUCTS.items()
            if species.CLASS == "alkane" and species.C_ATOMS > 1
        }
        olefins_molh = [F[id].molh * species.C_ATOMS for id, species in olefins.items()]
        df["olefins"] = np.sum(
            np.array(olefins_molh),
            axis=0,
        )
        paraffins_molh = [
            F[id].molh * species.C_ATOMS for id, species in paraffins.items()
        ]
        df["paraffins"] = np.sum(
            np.array(paraffins_molh),
            axis=0,
        )
        return df
