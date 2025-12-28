import pandas as pd, numpy as np

from .step import Step
from .. import utils
from .. import quantities as quant


class Co2FtsStep(Step):

    def __init__(self, step_name, step_num, start, end):
        super().__init__(step_name, step_num, start, end)

    def attach_reactor(self, reactor_class, kinetic_model, T, p0, whsv, mcat):
        self.reactor = reactor_class(kinetic_model, T, p0, whsv, "co2", mcat=mcat)

    def simulate(self, dt_sec, std_dev=None):
        if std_dev is None:
            std_dev = {"temp": 0.3, "pressure": 0.1, "mfc": 0.5, "gc": 0.005}
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

        ch4_sel = 0.3
        olefins_sel = 0.4
        paraffins_sel = 1 - ch4_sel - olefins_sel
        F_hydrocarbons = (
            self.reactor.F0["co2"]
            - self.reactor.F["co2"][-1]
            - self.reactor.F["co"][-1]
        )

        F_out = self.reactor.F[:, -1]
        F_out.keys[F_out.keys.index("inert")] = "n2"
        F_out["ch4"] = F_hydrocarbons * ch4_sel
        F_out["c2h4"] = F_hydrocarbons * olefins_sel / 4 / 2
        F_out["c3h6"] = F_hydrocarbons * olefins_sel / 4 / 3
        F_out["c4h8"] = F_hydrocarbons * olefins_sel / 4 / 4
        F_out["c5h10"] = F_hydrocarbons * olefins_sel / 4 / 5
        F_out["c2h6"] = F_hydrocarbons * paraffins_sel / 4 / 2
        F_out["c3h8"] = F_hydrocarbons * paraffins_sel / 4 / 3
        F_out["c4h10"] = F_hydrocarbons * paraffins_sel / 4 / 4
        F_out["c5h12"] = F_hydrocarbons * paraffins_sel / 4 / 5

        y_out = F_out / self.reactor.Ft[-1]

        for component in y_out.keys:
            df[f"{component}_gc_conc_pct"] = y_out[component].pct * np.random.normal(
                loc=1, scale=std_dev["gc"], size=num_points
            )

        delta_co2 = self.reactor.F0["co2"] - F_out["co2"]
        self.co2_conv = utils.divide(delta_co2, self.reactor.F0["co2"])
        conf = utils.getconf("co2_fts", "components")
        carbon_out = np.sum(
            [F_out[comp_id].si * conf[comp_id].get("C_ATOMS", 0) for comp_id in conf]
        )
        carbon_out = quant.MolarFlowRate(si=carbon_out)
        self.carbon_bal = carbon_out / self.reactor.F0["co2"]

        self.time_series_data = df
