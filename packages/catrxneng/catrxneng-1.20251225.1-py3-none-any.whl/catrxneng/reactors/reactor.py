import pandas as pd

from ..kinetic_models import KineticModel
from .. import quantities as quant


class Reactor:

    F0: quant.MolarFlowRate
    F: quant.MolarFlowRate
    # kinetic_model_class: type[KineticModel]
    kinetic_model: KineticModel
    aggregate_flow_rates: pd.DataFrame

    @property
    def molar_flowrate_df_molh(self):
        try:
            return self.molar_flowrate_df_molh_cache
        except AttributeError:
            molar_flowrate_dict = {
                key: value for key, value in zip(self.F.keys, self.F.molh)
            }
            self.molar_flowrate_df_molh_cache = molar_flowrate_dict
            return self.molar_flowrate_df_molh_cache

    @molar_flowrate_df_molh.setter
    def molar_flowrate_df_molh(self, value):
        self.molar_flowrate_df_molh_cache = value

    def check_components(self):
        if self.p0.size != len(self.kinetic_model.COMPONENTS):
            raise ValueError(
                "Number of components for reactor and rate model do not match."
            )

    def generate_df(self):
        from catrxneng.utils import compute_molfracs_from_molar_flowrates

        self.df = pd.DataFrame(
            {f"{key}_dnstr_molh": self.F[key].molh for key in self.F.keys}
        )
        self.df = compute_molfracs_from_molar_flowrates(
            df=self.df, kinetic_model=self.kinetic_model
        )
        for key in self.p.keys:
            self.df[f"{key}_dnstr_bar"] = self.df[f"{key}_dnstr_molfrac"] * self.P.bar
