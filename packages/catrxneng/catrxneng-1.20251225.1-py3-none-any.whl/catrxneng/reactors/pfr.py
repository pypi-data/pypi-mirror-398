import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp
from typing import cast, Any, Optional

from .reactor import Reactor
from ..kinetic_models import KineticModel, co2_to_c1
from ..phases.gas_mixture import GasMixture
from .. import utils, quantities as quant
from ..material import Catalyst, CzaCatalyst


class PFR(Reactor):
    def __init__(
        self,
        # kinetic_model_class: type[KineticModel],
        kinetic_model: KineticModel | co2_to_c1.PowerLawCzaSim,
        T: quant.Temperature,
        p0: quant.Pressure,
        whsv: Optional[quant.WHSV] = None,
        mcat: Optional[quant.Mass] = None,
        F0: Optional[quant.MolarFlowRate] = None,
        catalyst: Catalyst | CzaCatalyst = Catalyst(),
        # kinetic_model_kwargs: dict[str, Any] = {},
    ):
        # super().__init__()
        # self.kinetic_model_class = kinetic_model_class
        # self.kinetic_model = kinetic_model_class(T=T)
        self.kinetic_model = kinetic_model
        self.T = T
        self.p0 = p0
        feed = GasMixture(components=self.kinetic_model.COMPONENTS, p=self.p0)
        self.P = quant.Pressure(si=np.sum(p0.si))
        # self.P_bar = self.P.bar
        self.y0 = utils.divide(p0, self.P)
        self.whsv = whsv
        self.mcat = quant.Mass(g=1) if mcat is None else mcat
        if self.whsv is not None:
            if self.whsv.gas_mixture is None:
                self.whsv.gas_mixture = feed
            self.Ft0_active = self.whsv * self.mcat
            self.Ft0 = self.Ft0_active / (1 - self.y0["inert"])
            self.F0 = self.y0 * self.Ft0
        elif F0 is not None:
            self.F0 = F0
            self.Ft0 = quant.MolarFlowRate(molh=np.sum(self.F0.molh))
            self.Ft0_active = self.Ft0 - self.F0["inert"]
            self.whsv = quant.WHSV(
                molhgcat=self.Ft0_active.molh / self.mcat.g, gas_mixture=feed
            )
        else:
            raise ValueError("whsv and F0 cannot both be None.")
        self.catalyst = catalyst
        self.check_components()

    def dFdw(self, x, F: NDArray[np.number]) -> NDArray[np.number]:
        # p_array = F / np.sum(F) * getattr(self.P, self.kinetic_model.pressure_units)
        p_array_bar = F / np.sum(F) * self.P.bar
        return self.kinetic_model.get_reaction_rate_array_molhgcat(p_array_bar)

    def dFdw_zero_rate(self, x, F: NDArray[np.number]) -> NDArray[np.number]:
        return np.zeros(F.size)

    def dfdx_zero_rate(self, x, f: NDArray[np.number]) -> NDArray[np.number]:
        return np.zeros(f.size)

    def dfdx(self, x, f: NDArray[np.number]) -> NDArray[np.number]:
        Ft = np.sum(self.Ft0_active.si * f)
        p = self.P.si * self.Ft0_active.si * f / Ft
        p = quant.Pressure(si=p, keys=self.p0.keys.copy())
        return (
            self.mcat.si
            / self.Ft0_active.si
            * np.array(
                [
                    rate(p, self.T).si
                    for rate in self.kinetic_model.get_reaction_rates_molhgcat.values()
                ]
            )
        )

    def _solve_dimensional(self, points: int, method: str, zero_rate: bool = False):
        w_span = (0, self.mcat.g)
        w_eval = np.linspace(0, self.mcat.g, points)
        F0_molh = self.F0.molh
        dFdw = self.dFdw_zero_rate if zero_rate else self.dFdw
        solution = solve_ivp(dFdw, w_span, F0_molh, t_eval=w_eval, method=method)
        self.w = quant.Mass(g=solution.t)
        self.F = quant.MolarFlowRate(molh=solution.y, keys=self.F0.keys)

    def _solve_dimensionless(
        self,
        points: int,
        method: str,
        rtol: float = 1e-3,
        atol: float = 1e-6,
        zero_rate: bool = False,
    ):
        x_span = (0, 1)
        x_eval = np.linspace(x_span[0], x_span[1], points)
        f0 = self.F0.si / self.Ft0_active.si
        dfdx = self.dfdx_zero_rate if zero_rate else self.dfdx
        solution = solve_ivp(
            dfdx, x_span, f0, t_eval=x_eval, method=method, rtol=rtol, atol=atol
        )
        self.x = solution.t
        self.f = solution.y
        self.w = quant.Mass(si=(self.x * self.mcat.si))
        F = self.Ft0_active.si * self.f
        self.F = quant.MolarFlowRate(si=F, keys=self.F0.keys)

    def solve(
        self,
        points: int = 1000,
        nondimensionalize: bool = False,
        method: str = "LSODA",
        zero_rate=False,
    ):
        if nondimensionalize:
            self._solve_dimensionless(points=points, method=method, zero_rate=zero_rate)
        else:
            self._solve_dimensional(points=points, method=method, zero_rate=zero_rate)
        y_si = np.divide(self.F.si, np.sum(self.F.si, axis=0))
        self.y = quant.Fraction(si=y_si, keys=self.F0.keys)
        self.Ft = quant.MolarFlowRate(si=np.sum(self.F.si, axis=0))
        self.Ft_active = self.Ft - self.F["inert"]
        self.y_active = self.F / self.Ft_active
        self.y_active.delete("inert")
        self.dF_limiting_reactant = (
            self.F[self.kinetic_model.LIMITING_REACTANT]
            - self.F0[self.kinetic_model.LIMITING_REACTANT]
        )
        rate_limiting_reactant_molhgcat = (
            -self.dF_limiting_reactant[-1].molh / self.mcat.g
        )
        self.rate_limiting_reactant = quant.ReactionRate(
            molhgcat=rate_limiting_reactant_molhgcat
        )
        self.conversion = utils.divide(
            -self.dF_limiting_reactant,
            self.F0[self.kinetic_model.LIMITING_REACTANT],
        )
        spacetime = utils.divide(self.w.g, self.Ft0_active.smLh)
        self.spacetime = quant.SpaceTime(hgcatsmL=spacetime)
        self.whsv_array = quant.WHSV(smLhgcat=utils.divide(1, spacetime))
        vol_flow_rate = self.Ft0.si * quant.R.si * self.T.si / self.P.si
        self.vol_flow_rate = quant.VolumetricFlowRate(si=vol_flow_rate)
        self.p = self.y * self.P
        self.rate_matrix = self.kinetic_model.get_2d_reaction_rate_array(
            self.p, zero_rate=zero_rate
        )
        self.generate_df()

    @property
    def conversion_relative_to_equil_conversion(self):
        self.kinetic_model.equilibrate(p0=self.p0, T=self.T)
        return self.conversion[-1] / self.kinetic_model.eq_conversion

    def compute_carbon_basis_selectivity(self):
        prod_carbon_molh = np.zeros(self.F.si.shape[1])
        for species_id, species in self.kinetic_model.PRODUCTS.items():
            prod_carbon_molh += self.F[species_id].molh * species.C_ATOMS
        sel = np.array(
            [
                self.F[species_id].molh * species.C_ATOMS / prod_carbon_molh  # type: ignore
                for species_id, species in self.kinetic_model.PRODUCTS.items()
            ]
        )
        self.carbon_basis_selectivity = quant.Fraction(
            si=sel, keys=list(self.kinetic_model.PRODUCTS.keys())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalyst_common_name": self.catalyst.common_name,
            "rate_limiting_reactant_molhgcat": self.rate_limiting_reactant.molhgcat,
            "conversion_pct": self.conversion[-1].pct,
        }
