import numpy as np
from numpy.typing import NDArray
from typing import Optional, cast, Any

from .. import kinetic_models, quantities as quant, utils
from .catalyst import Catalyst
from ..kinetic_models import KineticModel, co2_to_c1


class CzaCatalyst:
    kref_molhgcatbar: list[float]
    Ea_kJmol: list[float]

    KINETIC_MODEL_CLASS = kinetic_models.co2_to_c1.PowerLawCzaSim
    T_REF = KINETIC_MODEL_CLASS.T_REF
    # kinetic_model: KINETIC_MODEL_CLASS

    def __init__(
        self,
        T_cal: quant.Temperature,
        ZnO_wtpct: float,
        co2_order=np.array([0.5]),
        h2_order=np.array([0.5]),
        common_name: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.T_cal = T_cal
        self.ZnO_wtpct = ZnO_wtpct
        self.T_cal_norm = (T_cal.C - 320) / 60
        self.ZnO_norm = (ZnO_wtpct - 25) / 10
        self.co2_order = co2_order
        self.h2_order = h2_order
        self.order = co2_order + h2_order
        if common_name is None:
            self.common_name = f"60Cu{ZnO_wtpct:.0f}/Al2O3-{T_cal.C:.0f}"
        else:
            self.common_name = common_name
        self.project_id = project_id
        self.date = utils.Time()
        self.compute_kinetic_constants()

    def to_dict(self) -> dict[str, Optional[Any]]:
        return {
            # **super().to_dict(),
            "material_class_name": type(self).__name__,
            "common_name": self.common_name,
            "project_id": self.project_id,
            "_date": self.date.UET,
            "kinetic_model_module_name": "co2_to_c1",
            "kinetic_model_class_name": "PowerLawCzaSim",
            "T_cal_C": self.T_cal.C,
            "ZnO_wtpct": self.ZnO_wtpct,
            "kref_molhgcatbar": self.kref_molhgcatbar[0],
            "Ea_kJmol": self.Ea_kJmol[0],
            "co2_order": self.co2_order[0],
            "h2_order": self.h2_order[0],
        }

    @property
    def kref(self) -> list[quant.RateConstant]:
        return [
            quant.RateConstant(
                molhgcatbar=kref_molhgcatbar,
                Ea=quant.Energy(kJmol=Ea_kJmol),
                order=order,
                Tref=self.T_REF,
            )
            for kref_molhgcatbar, Ea_kJmol, order in zip(
                self.kref_molhgcatbar, self.Ea_kJmol, self.order
            )
        ]

    def get_kinetic_model(
        self, T: quant.Temperature
    ) -> KineticModel | co2_to_c1.PowerLawCzaSim:
        return self.KINETIC_MODEL_CLASS(T=T, kref=self.kref)

    def compute_kinetic_constants(self):
        self.compute_kref()
        self.compute_Ea()

    def compute_kref(self):
        """
        Reference rate constant for CO2 hydrogenation to methanol at 250°C

        Power law kinetics: r = k · P_CO2^α · P_H2^β · (1 - Q/K_eq)

        Parameters:
        -----------
        T_calc : float or array
                Calcination temperature in °C (range: 260-380°C)
        ZnO_wt : float or array
                ZnO weight percentage (range: 15-35 wt%)
        noise_level : float
                Relative noise to add (default 8%)

        Returns:
        --------
        k_ref : float or array
                Reference rate constant in mol/(g_cat·h·bar^(α+β)) at 250°C
                With α=0.5, β=0.5: units are mol/(g_cat·h·bar)
        """

        # Coefficients for realistic range
        # Peak activity ~2e-4 mol/(g·h·bar) at optimal conditions
        # beta_0 = 6.5e-4
        # beta_1 = -2e-6
        # beta_2 = 3e-5
        # beta_3 = -2.5e-4
        # beta_4 = -3e-4
        # beta_5 = -2e-5
        # multiplier = 0.5
        beta_0 = 1.5e-4
        beta_1 = -2e-5
        beta_2 = 3e-5
        beta_3 = -5e-5
        beta_4 = -4e-5
        beta_5 = -2e-5
        multiplier = 1

        # Linear combination
        self.kref_molhgcatbar = [
            (
                beta_0
                + beta_1 * self.T_cal_norm
                + beta_2 * self.ZnO_norm
                + beta_3 * self.T_cal_norm**2
                + beta_4 * self.ZnO_norm**2
                + beta_5 * self.T_cal_norm * self.ZnO_norm
            )
            * multiplier
        ]

        # Physical bounds
        # k_ref = np.clip(k_ref, 1e-5, 3e-4)

    def compute_Ea(self):
        """
        Activation energy for CO2-to-methanol in kJ/mol

        Literature range: 75-105 kJ/mol
        """
        # Coefficients
        gamma_0 = 88.0
        gamma_1 = 2.0
        gamma_2 = -1.5
        gamma_3 = 5.5
        gamma_4 = 6.5
        gamma_5 = 2.5

        self.Ea_kJmol = [
            (
                gamma_0
                + gamma_1 * self.T_cal_norm
                + gamma_2 * self.ZnO_norm
                + gamma_3 * self.T_cal_norm**2
                + gamma_4 * self.ZnO_norm**2
                + gamma_5 * self.T_cal_norm * self.ZnO_norm
            )
        ]
        # Ea = np.clip(Ea, 75, 105)

    @staticmethod
    def K_eq_methanol(T):
        """
        Equilibrium constant for CO2 + 3H2 ⇌ CH3OH + H2O

        Based on Graaf et al. (1988)

        Parameters:
        -----------
        T : float or array
                Temperature in K

        Returns:
        --------
        K_eq : float or array
                Equilibrium constant (bar^-2 basis for fugacity/pressure)
        """
        # Graaf correlation
        log10_K_eq = -3066 / T + 10.592
        K_eq = 10**log10_K_eq

        return K_eq

    # def reaction_rate_methanol(
    #     self,
    #     P_CO2,
    #     P_H2,
    #     P_H2O,
    #     P_MeOH,
    #     k_ref,
    #     Ea,
    #     T,
    #     alpha=0.5,
    #     beta=0.5,
    #     T_ref=523.15,
    # ):
    #     """
    #     Power law rate expression with approach to equilibrium factor

    #     CO2 + 3H2 ⇌ CH3OH + H2O

    #     r = k(T) · P_CO2^α · P_H2^β · (1 - Q/K_eq)

    #     Parameters:
    #     -----------
    #     P_CO2, P_H2, P_H2O, P_MeOH : float or array
    #             Partial pressures in bar
    #     k_ref : float
    #             Rate constant at reference T in mol/(g_cat·h·bar^(α+β))
    #     Ea : float
    #             Activation energy in kJ/mol
    #     T : float or array
    #             Temperature in K
    #     alpha : float
    #             Reaction order for CO2 (default 0.5)
    #     beta : float
    #             Reaction order for H2 (default 0.5)
    #     T_ref : float
    #             Reference temperature in K (default 523.15 K = 250°C)

    #     Returns:
    #     --------
    #     r : float or array
    #             Reaction rate in mol/(g_cat·h)
    #     """
    #     R = 8.314e-3  # kJ/(mol·K)

    #     # Arrhenius temperature dependence
    #     k = k_ref * np.exp(-Ea / R * (1 / T - 1 / T_ref))

    #     # Forward rate with power law
    #     r_forward = k * P_CO2**alpha * P_H2**beta

    #     # Equilibrium constant
    #     K_eq = self.K_eq_methanol(T)

    #     # Reaction quotient Q = (P_MeOH · P_H2O) / (P_CO2 · P_H2^3)
    #     Q = (P_MeOH * P_H2O) / (P_CO2 * P_H2**3 + 1e-10)

    #     # Approach to equilibrium factor (beta factor)
    #     beta_factor = 1 - Q / K_eq

    #     # Net rate
    #     r = r_forward * beta_factor

    #     # Ensure non-negative (only consider forward reaction)
    #     r = np.maximum(r, 0.0)

    #     return r
