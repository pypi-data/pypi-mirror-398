import pandas as pd, numpy as np

from .step import Step
from .. import utils
from .. import quantities as quant


class TandemStep(Step):

    def __init__(self, step_name, step_num, start, end):
        super().__init__(step_name, step_num, start, end)

    def attach_reactor(self, reactor_class, kinetic_model, T, p0, whsv, mcat):
        self.reactor = reactor_class(
            kinetic_model=kinetic_model,
            p0=p0,
            whsv=whsv,
            T=T,
            limiting_reactant="co2",
            mcat=mcat,
        )

    def simulate(self, dt_sec, std_dev=None):
        # if std_dev is None:
        #     std_dev = {"temp": 0.3, "pressure": 0.1, "mfc": 0.5, "gc": 0.005}
        df = pd.DataFrame()
        df["timestamp"] = np.arange(self.start.UET, self.end.UET + dt_sec, dt_sec)
        num_points = df["timestamp"].size
        df["step_name"] = self.step_name
        df["step_num"] = self.step_num
        self.reactor.solve()
        df["bed_temp"] = self.reactor.T.C + np.random.normal(
            loc=0, scale=std_dev["temp"], size=num_points
        )
        df["pressure"] = self.reactor.P.bar + np.random.normal(
            loc=0, scale=std_dev["pressure"], size=num_points
        )
        df["n2_mfc_smLmin"] = self.reactor.F0["inert"].smLmin + np.random.normal(
            loc=0, scale=std_dev["mfc"], size=num_points
        )
        df["co2_mfc_smLmin"] = self.reactor.F0["co2"].smLmin + np.random.normal(
            loc=0, scale=std_dev["mfc"], size=num_points
        )
        df["h2_mfc_smLmin"] = self.reactor.F0["h2"].smLmin + np.random.normal(
            loc=0, scale=std_dev["mfc"], size=num_points
        )

        for component in self.reactor.y.keys:
            df[f"{component}_gc_conc_pct"] = self.reactor.y[-1][
                component
            ].pct * np.random.normal(loc=1, scale=std_dev["gc"], size=num_points)
            if component == "inert":
                df = df.rename(columns={"inert_gc_conc_pct": "n2_gc_conc_pct"})

        self.time_series_data = df
