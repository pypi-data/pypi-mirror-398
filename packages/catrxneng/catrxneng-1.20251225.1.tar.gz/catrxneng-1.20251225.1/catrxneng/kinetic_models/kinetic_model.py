import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares
from typing import cast, TYPE_CHECKING

from .. import quantities as quant
from ..species import Species, Inert
from ..utils import divide

if TYPE_CHECKING:
    from ..reactions import Reaction


class KineticModel:
    KREF_UNITS: str
    EA_UNITS: str
    LIMITING_REACTANT: str
    T_REF: quant.Temperature
    REACTANTS: dict[str, type[Species] | Species]
    PRODUCTS: dict[str, type[Species] | Species]
    REACTIONS: dict[str, type["Reaction"]]
    STOICH_COEFF: NDArray
    ORDER: NDArray
    KREF: NDArray
    EA: NDArray

    kref: NDArray
    Ea: NDArray
    k: NDArray

    def __init_subclass__(cls):
        super().__init_subclass__()
        try:
            cls.COMPONENTS = {**cls.REACTANTS, **cls.PRODUCTS, "inert": Inert}
            cls.C_ATOMS = np.array([comp.C_ATOMS for comp in cls.COMPONENTS.values()])
            cls.COMP_IDX = {comp: i for i, comp in enumerate(cls.COMPONENTS)}
            cls.RXN_IDX = {rxn: i for i, rxn in enumerate(cls.REACTIONS)}
        except AttributeError:
            pass

    def __init__(
        self,
        T: quant.Temperature | None = None,
        kref: np.typing.NDArray | None = None,
        Ea: quant.Energy | None = None,
        rate_units: str = "molhgcat",
        pressure_units: str = "bar",
    ):
        self._T = None
        self.kref = kref
        if self.kref is None:
            self.kref = self.KREF
        self.Ea = Ea
        if self.Ea is None:
            self.Ea = self.EA
        self.rate_units = rate_units
        self.pressure_units = pressure_units
        self.rate_constant_units = rate_units + pressure_units
        self.fugacity_coeff = np.ones(len(self.COMPONENTS))
        self.T = T

    def get_rate_constant_array(self) -> np.typing.NDArray:
        k = [
            getattr(
                quant.RateConstant(
                    **{self.KREF_UNITS: kref},
                    Ea=quant.Energy(**{self.EA_UNITS: Ea}),
                    Tref=self.T_REF,
                    order=order,
                )(self.T),
                self.rate_constant_units,
            )
            for kref, Ea, order in zip(self.kref, self.Ea, self.ORDER)
        ]
        return np.array(k)

    def compute_temp_dependent_constants(self):
        raise NotImplementedError(
            "Child class must implement compute_temp_dependent_constants."
        )

    def get_2d_reaction_rate_array(self, p: quant.Pressure) -> quant.ReactionRate:
        return quant.ReactionRate(
            **{
                self.rate_units: self.get_reaction_rates_molhgcat(
                    p_array=getattr(p, self.pressure_units)
                )
            },
            keys=self.comp_list(),
        )

    def get_reaction_rates_molhgcat(self, p_array: NDArray) -> NDArray:
        raise NotImplementedError("Child class must implement method.")

    @classmethod
    def comp_list(cls):
        return list(cls.COMPONENTS.keys())

    @property
    def T(self):
        return self._T

    @T.setter
    def T(self, value):
        if value is None:
            self._T = value
        elif self._T is None or self._T.si != value.si:
            self._T = value
            self.compute_temp_dependent_constants()

    def _compute_final_molfrac(
        self, initial_moles: NDArray, extent: NDArray
    ) -> tuple[NDArray, NDArray]:
        delta_moles = self.STOICH_COEFF.T @ extent
        final_moles = initial_moles + delta_moles
        total_final_moles = np.sum(final_moles)
        molfrac = final_moles / total_final_moles
        return molfrac, delta_moles

    def _compute_extent_bounds(self, initial_moles):
        lower_bounds = [0] * len(self.REACTIONS)
        upper_bounds = []
        for i in range(len(self.REACTIONS)):
            stoich_lim = self.STOICH_COEFF[i][self.COMP_IDX[self.LIMITING_REACTANT]]
            max_extent = initial_moles[self.COMP_IDX[self.LIMITING_REACTANT]] / abs(
                stoich_lim
            )
            upper_bounds.append(max_extent)
        return (lower_bounds, upper_bounds)

    def _equilibrium_objective(self, extent, P_bar, initial_moles, Keq):
        molfrac = self._compute_final_molfrac(initial_moles, extent)[0]
        molfrac[molfrac < 0] = 0.00001
        p = molfrac * P_bar
        fugacity = self.fugacity_coeff * p
        activity = fugacity / quant.STD_STATE_FUGACITY.bar
        K_calc = np.prod(activity**self.STOICH_COEFF, axis=1)
        return (np.log(K_calc) - np.log(Keq)) ** 2

    def equilibrate(
        self,
        p0: quant.Pressure,
        T: quant.Temperature,
        Keq: NDArray[np.number] | None = None,
        initial_guesses=None,
        allow_component_mismatch=False,
    ):
        self.T = T
        if Keq is None:
            Keq = self.Keq
        initial_total_moles = 100
        if allow_component_mismatch:
            p0_bar = [p0[comp].bar for comp in self.comp_list()]
            p0 = quant.Pressure(bar=p0_bar, keys=self.comp_list())
        P = quant.Pressure(si=np.sum(p0.si))
        initial_molfrac = p0 / P
        initial_moles = cast(NDArray, initial_molfrac.si * initial_total_moles)
        if not initial_guesses:
            num_rxns = len(self.REACTIONS)
            initial_guess = (
                initial_moles[self.COMP_IDX[self.LIMITING_REACTANT]] / num_rxns
            )
            initial_guesses = np.ones(num_rxns) * initial_guess / 2

        def objective(extent):
            return self._equilibrium_objective(extent, P.bar, initial_moles, Keq)

        solution = least_squares(
            objective,
            initial_guesses,
            bounds=self._compute_extent_bounds(initial_moles),
            method="trf",
            ftol=1e-10,
            max_nfev=1000,
        )
        extent = solution.x
        eq_molfrac, delta_moles = self._compute_final_molfrac(initial_moles, extent)
        self.initial_moles = quant.Moles(si=initial_moles, keys=p0.keys)
        self.eq_delta_moles = quant.Moles(si=delta_moles, keys=p0.keys)
        delta = delta_moles[self.COMP_IDX[self.LIMITING_REACTANT]]
        initial = initial_moles[self.COMP_IDX[self.LIMITING_REACTANT]]
        self.eq_conversion = quant.Fraction(si=-delta / initial)
        self.eq_molfrac = quant.Fraction(si=eq_molfrac, keys=self.comp_list())
        self.eq_partial_pressure = self.eq_molfrac * P

    @classmethod
    def carbon_balance(cls, reactor):
        carbon_in = np.sum(reactor.F0.si * cls.C_ATOMS)
        carbon_out = np.sum(reactor.F.si * cls.C_ATOMS[:, np.newaxis], axis=0)
        c_bal = divide(carbon_out, carbon_in)
        return quant.Fraction(si=c_bal)
