import pandas as pd
import numpy as np
from typing import TYPE_CHECKING, Optional, Any

from ..reactors import PFR
from ..utils import Time

if TYPE_CHECKING:
    from catrxneng.simulate import Expt
    from ..simulate import Expt


class Step:
    steady_state_step_num: int

    @property
    def lab_notebook_id(self):
        return f"{self.expt.lab_notebook_id}-s{self.steady_state_step_num}"

    def __init__(
        self,
        expt: "Expt",
        step_name: str,
        step_num: int,
        start: Time,
        end: Time,
        reactor: PFR,
    ):
        self.expt = expt
        self.step_name = step_name
        self.step_num = step_num
        self.start = start
        self.end = end
        self.reactor = reactor

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_name": self.step_name,
            "step_num": self.step_num,
            "bed_temp_C": self.reactor.T.C,
            "whsv_smLhgcat": self.reactor.whsv.smLhgcat,
            "pressure_bar": self.reactor.P.bar,
            "conversion_pct": self.reactor.conversion[-1].pct,
            "rate_limiting_reactant_molhgcat": self.reactor.rate_limiting_reactant.molhgcat,
        }

    def simulate(self, dt_sec: int, std_dev: dict[str, float] | None = None):
        self.std_dev = std_dev
        if std_dev is None:
            self.std_dev = {"temp": 0.5, "pressure": 0.05, "mfc": 0.01, "gc": 0.0001}
        df = pd.DataFrame()
        df["timestamp"] = np.arange(self.start.UET, self.end.UET + dt_sec, dt_sec)
        self.num_points = df["timestamp"].size
        df["step_name"] = self.step_name
        df["step_num"] = self.step_num
        self.reactor.solve(zero_rate=self.step_name != "steadyState")
        df["bed_temp_C"] = self.reactor.T.C + np.random.normal(
            loc=0, scale=self.std_dev["temp"], size=self.num_points
        )
        df["pressure_bar"] = self.reactor.P.bar + np.random.normal(
            loc=0, scale=self.std_dev["pressure"], size=self.num_points
        )

        for component in self.reactor.y.keys:
            df[f"{component}_gc_conc_pct"] = self.reactor.y[-1][
                component
            ].pct + np.random.normal(
                loc=0, scale=self.std_dev["gc"], size=self.num_points
            )
        df["total_gc_conc_pct"] = df.filter(like="_gc_conc_pct").sum(axis=1)

        self.time_series_data = df

        # add additional simulate logic in child class simulate method after calling super().simulate

    def populate_inlet_partial_pressures(self):
        df = self.time_series_data
        for component in self.reactor.kinetic_model.comp_list():
            df[f"p_{component}_bar"] = (
                df[f"{component}_gc_conc_pct"] / 100 * df["pressure_bar"]
            )
