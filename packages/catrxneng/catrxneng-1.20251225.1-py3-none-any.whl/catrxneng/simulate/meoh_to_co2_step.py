import pandas as pd, numpy as np

from .step import Step


class MeohToCo2Step(Step):

    def simulate(self, dt_sec, std_dev=None):
        super().simulate(dt_sec, std_dev)
        df = self.time_series_data
        df["n2_mfc_smLmin"] = self.reactor.F0["inert"].smLmin * np.random.normal(
            loc=1, scale=self.std_dev["mfc"], size=self.num_points
        )
        df["co2_mfc_smLmin"] = self.reactor.F0["co2"].smLmin * np.random.normal(
            loc=1, scale=self.std_dev["mfc"], size=self.num_points
        )
        df["h2_mfc_smLmin"] = self.reactor.F0["h2"].smLmin * np.random.normal(
            loc=1, scale=self.std_dev["mfc"], size=self.num_points
        )
        df["ch3oh_mfc_smLmin"] = self.reactor.F0["ch3oh"].smLmin * np.random.normal(
            loc=1, scale=self.std_dev["mfc"], size=self.num_points
        )
        df["h2o_mfc_smLmin"] = self.reactor.F0["h2o"].smLmin * np.random.normal(
            loc=1, scale=self.std_dev["mfc"], size=self.num_points
        )

        df = df.rename(
            columns={"inert_gc_conc_pct": "n2_gc_conc_pct", "p_inert": "p_n2"}
        )
        df["dme_gc_conc_pct"] = 0.0
        if "ch4_gc_conc_pct" not in df.columns:
            df["ch4_gc_conc_pct"] = 0.0
        self.time_series_data = df
