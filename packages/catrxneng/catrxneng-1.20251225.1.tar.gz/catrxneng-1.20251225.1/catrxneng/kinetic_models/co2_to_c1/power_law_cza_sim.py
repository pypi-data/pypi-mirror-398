import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares
from typing import TYPE_CHECKING, cast

from ..kinetic_model import KineticModel
from ...reactions import Co2ToMeoh
from ... import species as species
from ... import quantities as quant
from ... import utils

if TYPE_CHECKING:
    from ...reactors import Reactor


class PowerLawCzaSim:
    kref: list[quant.RateConstant]
    T_REF = quant.Temperature(C=250)
    LIMITING_REACTANT = "co2"
    REACTANTS = {
        "co2": species.CO2,
        "h2": species.H2,
    }
    PRODUCTS = {
        "ch3oh": species.CH3OH,
        "h2o": species.H2O,
    }
    COMPONENTS = {**REACTANTS, **PRODUCTS, "inert": species.Inert}
    C_ATOMS = np.array([comp.C_ATOMS for comp in COMPONENTS.values()])
    COMP_IDX = {comp: i for i, comp in enumerate(COMPONENTS)}
    REACTIONS = {
        "co2_to_meoh": Co2ToMeoh,
    }
    RXN_IDX = {rxn: i for i, rxn in enumerate(REACTIONS)}
    STOICH_COEFF = np.array(
        [
            [-1, -3, 1, 1, 0],
        ]
    )
    H2_ORDER = 0.5
    CO2_ORDER = 0.5
    KREF = [
        quant.RateConstant(
            molhgcatbar=0.000373,
            Ea=quant.Energy(kJmol=100),
            order=H2_ORDER + CO2_ORDER,
            Tref=T_REF,
        )
    ]

    @classmethod
    def comp_list(cls):
        return list(cls.COMPONENTS.keys())

    @property
    def T(self):
        return self._T

    @T.setter
    def T(self, value: quant.Temperature | None):
        if value is None:
            self._T = value
        elif self._T is None or self._T.si != value.si:
            self._T = value
            self.compute_temp_dependent_constants()

    @classmethod
    def carbon_balance(cls, reactor: "Reactor"):
        carbon_in_molh = np.sum(reactor.F0.molh * cls.C_ATOMS)
        carbon_out_molh = np.sum(reactor.F.molh * cls.C_ATOMS[:, np.newaxis], axis=0)
        c_bal = utils.divide(carbon_out_molh, carbon_in_molh)
        return quant.Fraction(si=c_bal)

    def __init__(
        self,
        T: quant.Temperature | None = None,
        kref: list[quant.RateConstant] | None = None,
    ):
        self.fugacity_coeff = np.ones(len(self.COMPONENTS))
        self._T = None
        self.kref = kref
        if kref is None:
            self.kref = self.KREF
        self.T = T

    def get_rate_constant_array(self, units: str) -> list[float]:
        """
        returns a list of rate constants
        """
        return [getattr(kref(self.T), units) for kref in self.kref]

    def compute_temp_dependent_constants(self):
        self.Keq_co2_to_meoh = Co2ToMeoh.Keq(self.T)
        self.Keq = np.array([self.Keq_co2_to_meoh])
        self.k_molhgcatbar = self.get_rate_constant_array("molhgcatbar")

    def get_reaction_rate_array_molhgcat(
        self, p_array_bar: NDArray[np.number]
    ) -> NDArray[np.number]:
        """
        p_array in bar.
        Returns an array of reaction rates in molhgcat.
        """
        p_co2_bar = p_array_bar[0]  # co2
        p_h2_bar = p_array_bar[1]  # h2
        p_ch3oh_bar = p_array_bar[2]  # ch3oh
        p_h2o_bar = p_array_bar[3]  # h2o

        # Reaction 1: CO2 + 3H2 -> CH3OH + H2O (CO2-to-MeOH)
        p_h2_3_bar = p_h2_bar * p_h2_bar * p_h2_bar
        beta = (
            1 / self.Keq_co2_to_meoh * p_ch3oh_bar * p_h2o_bar / p_co2_bar / p_h2_3_bar
        )
        r1 = (
            self.k_molhgcatbar[0]
            * p_h2_bar**self.H2_ORDER
            * p_co2_bar**self.CO2_ORDER
            * (1 - beta)
        )

        rate = np.array([r1])
        # return np.array(
        #     [
        #         -r1,  # co2
        #         -3 * r1,  # h2
        #         r1,  # ch3oh
        #         r1,  # h2o
        #         0.0 * r1,  # inert
        #     ]
        # )
        return self.STOICH_COEFF.T @ rate

    def get_2d_reaction_rate_array(
        self, p: quant.Pressure, zero_rate=False
    ) -> quant.ReactionRate:
        if zero_rate:
            molhgcat = np.zeros(p.bar.shape)
        else:
            molhgcat = self.get_reaction_rate_array_molhgcat(p_array_bar=p.bar)
        return quant.ReactionRate(
            molhgcat=molhgcat,
            keys=self.comp_list(),
        )

    @classmethod
    def get_yield(cls, reactor: "Reactor") -> dict[str, NDArray[np.number]]:
        product_yield_frac = {
            prod_id: (reactor.F[prod_id].molh - reactor.F0[prod_id].molh)
            / reactor.F0[cls.LIMITING_REACTANT].molh
            for prod_id in cls.PRODUCTS
        }
        return product_yield_frac

    def get_equilibrium_yield(self) -> dict[str, quant.Fraction]:
        product_yield_frac = {
            prod_id: self.eq_delta_moles[prod_id]
            / self.initial_moles[self.LIMITING_REACTANT]
            for prod_id in self.PRODUCTS
        }
        return product_yield_frac  # type: ignore

    def _get_final_molfrac(
        self, initial_moles: NDArray[np.number], extent: NDArray[np.number]
    ) -> tuple[NDArray[np.number], NDArray[np.number]]:
        delta_moles = self.STOICH_COEFF.T @ extent
        final_moles = initial_moles + delta_moles
        total_final_moles = np.sum(final_moles)
        molfrac = final_moles / total_final_moles
        return molfrac, delta_moles

    def _get_extent_bounds(
        self, initial_moles: NDArray[np.number]
    ) -> tuple[list[float], list[float]]:
        lower_bounds = [0.0] * len(self.REACTIONS)
        upper_bounds = []
        for i in range(len(self.REACTIONS)):
            stoich_lim = self.STOICH_COEFF[i][self.COMP_IDX[self.LIMITING_REACTANT]]
            max_extent = initial_moles[self.COMP_IDX[self.LIMITING_REACTANT]] / abs(
                stoich_lim
            )
            upper_bounds.append(max_extent)
        return (lower_bounds, upper_bounds)

    def _equilibrium_objective(self, extent, P_bar, initial_moles, Keq) -> float:
        molfrac = self._get_final_molfrac(initial_moles, extent)[0]
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
            bounds=self._get_extent_bounds(initial_moles),
            method="trf",
            ftol=1e-10,
            max_nfev=1000,
        )
        extent = solution.x
        eq_molfrac, delta_moles = self._get_final_molfrac(initial_moles, extent)
        self.initial_moles = quant.Moles(si=initial_moles, keys=p0.keys)
        self.eq_delta_moles = quant.Moles(si=delta_moles, keys=p0.keys)
        delta = delta_moles[self.COMP_IDX[self.LIMITING_REACTANT]]
        initial = initial_moles[self.COMP_IDX[self.LIMITING_REACTANT]]
        self.eq_conversion = quant.Fraction(si=-delta / initial)
        self.eq_molfrac = quant.Fraction(si=eq_molfrac, keys=self.comp_list())
        self.eq_partial_pressure = self.eq_molfrac * P
