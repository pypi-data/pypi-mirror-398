import numpy as np
import scipy.integrate as integrate
from numpy.typing import NDArray
from scipy.optimize import minimize_scalar

from .. import species, quantities as quant


class Reaction:
    EQUATION: str
    STOICH_COEFF: NDArray
    REACTANTS: dict[str, type[species.Species]]
    PRODUCTS: dict[str, type[species.Species]]
    COMPONENTS: dict[str, type[species.Species]]
    DEFAULT_LIMITING_REACTANT: str
    DH_RXN_298: quant.Energy
    DS_RXN_298: quant.Entropy
    DG_RXN_298: quant.Energy
    DH_RXN_298_GAS: quant.Energy
    DS_RXN_298_GAS: quant.Entropy
    DG_RXN_298_GAS: quant.Energy
    K_EQ_298: float

    def __init_subclass__(cls):
        T_298 = quant.Temperature(K=298)
        try:
            cls.COMPONENTS = {**cls.REACTANTS, **cls.PRODUCTS, "inert": species.Inert}

            cls.DH_RXN_298_GAS = quant.Energy(
                si=np.sum(
                    [
                        comp.HF_298_GAS.si * stoich_coeff
                        for comp, stoich_coeff in zip(
                            cls.COMPONENTS.values(), cls.STOICH_COEFF
                        )
                    ]
                )
            )

            cls.DS_RXN_298_GAS = quant.Entropy(
                si=np.sum(
                    [
                        comp.S_298_GAS.si * stoich_coeff
                        for comp, stoich_coeff in zip(
                            cls.COMPONENTS.values(), cls.STOICH_COEFF
                        )
                    ]
                )
            )

            cls.DG_RXN_298_GAS = cls.DH_RXN_298_GAS - T_298 * cls.DS_RXN_298_GAS
            cls.DG_RXN_298 = cls.DH_RXN_298 - T_298 * cls.DS_RXN_298
            # cls.K_EQ_298 = np.exp(-cls.DG_RXN_298 / (quant.R * T_298)).si
        except AttributeError:
            pass

    @classmethod
    def min_temp_for_gas_phase(cls) -> quant.Temperature:
        boiling_temp_K = [
            comp.BOILING_TEMP.K
            for comp in cls.COMPONENTS.values()
            if hasattr(comp, "BOILING_TEMP")
        ]
        max_boiling_temp_K = np.array(boiling_temp_K).max()
        return quant.Temperature(K=max_boiling_temp_K)

    @classmethod
    def dCp_gas_JmolK(cls, T_K) -> float:
        T = quant.Temperature(K=T_K)
        dCp = [
            comp.Cp_gas(T).JmolK * stoich_coeff
            for comp, stoich_coeff in zip(cls.COMPONENTS.values(), cls.STOICH_COEFF)
        ]
        return np.sum(dCp)

    @classmethod
    def dH_rxn(cls, T: quant.Temperature) -> quant.Energy:
        if T.K > cls.min_temp_for_gas_phase().K:
            dHr_Jmol = (
                cls.DH_RXN_298_GAS.Jmol + integrate.quad(cls.dCp_gas_JmolK, 298, T.K)[0]
            )
            return quant.Energy(Jmol=dHr_Jmol)
        raise ValueError("Temperature too low, not all components in gas phase.")

    @classmethod
    def dS_rxn(cls, T: quant.Temperature) -> quant.Entropy:
        if T.K > cls.min_temp_for_gas_phase().K:
            integrand = lambda T_K: cls.dCp_gas_JmolK(T_K) / T_K
            dSr_JmolK = (
                cls.DS_RXN_298_GAS.JmolK + integrate.quad(integrand, 298, T.K)[0]
            )
            return quant.Entropy(JmolK=dSr_JmolK)
        raise ValueError("Temperature too low, not all components in gas phase.")

    # @classmethod
    # def dH_rxn_gas_shomate(cls, T: quant.Temperature) -> quant.Energy:
    #     dHr = np.sum(
    #         [
    #             species.Hf_gas_shomate(T).si * stoich_coeff
    #             for species, stoich_coeff in zip(
    #                 cls.COMPONENTS.values(), cls.STOICH_COEFF
    #             )
    #         ]
    #     )
    #     return quant.Energy(si=dHr)

    # @classmethod
    # def dS_rxn_gas_shomate(cls, T: quant.Temperature) -> quant.Entropy:
    #     dSr = np.sum(
    #         [
    #             species.S_gas_shomate(T).si * stoich_coeff
    #             for species, stoich_coeff in zip(
    #                 cls.COMPONENTS.values(), cls.STOICH_COEFF
    #             )
    #         ]
    #     )
    #     return quant.Entropy(si=dSr)

    # @classmethod
    # def dG_rxn_gas_shomate(cls, T: quant.Temperature) -> quant.Energy:
    #     return cls.dH_rxn_gas_shomate(T) - T * cls.dS_rxn_gas_shomate(T)

    # @classmethod
    # def Keq_gas_shomate(cls, T: quant.Temperature) -> float:
    #     return np.exp(-cls.dG_rxn_gas_shomate(T) / (quant.R * T)).si

    @property
    def limiting_reactant(self):
        try:
            return self._limiting_reactant
        except AttributeError:
            return self.DEFAULT_LIMITING_REACTANT

    @limiting_reactant.setter
    def limiting_reactant(self, value):
        self._limiting_reactant = value

    @classmethod
    def comp_list(cls):
        return list(cls.COMPONENTS.keys())

    # @classmethod
    # def active_components(cls):
    #     # return {key: cls.COMPONENTS[key] for key in cls.COMPONENTS if key != "inert"}
    #     return {**cls.REACTANTS, **cls.PRODUCTS}

    # @classmethod
    # def stoich_coeff_active(cls):
    #     stoich_si = np.asarray(cls.STOICH_COEFF)
    #     return quant.Dimensionless(
    #         si=stoich_si[stoich_si != 0],
    #         keys=list(cls.active_components().keys()),
    #     )

    # @classmethod
    # def dH_rxn_gas(cls, T: quant.Temperature) -> quant.Energy:
    #     dCp = lambda temp_K: temp_K
    #     dHr_gas = cls.dH_rxn_298_gas().si + integrate.quad(dCp, 298, T.K)[0]
    #     return quant.Energy(si=dHr_gas)

    # @classmethod
    # def dS_rxn_gas(cls, T):
    #     S_gas = np.array(
    #         [cls.COMPONENTS[key].S_gas(T).si for key in cls.active_components()]
    #     )
    #     dSr_gas = np.sum(S_gas * cls.stoich_coeff_active().si)
    #     return quant.Entropy(si=dSr_gas)

    # @classmethod
    # def dG_rxn_gas(cls, T):
    #     return cls.dH_rxn_gas(T) - T * cls.dS_rxn_gas(T)

    # @classmethod
    # def dH_rxn_Cp(cls, T: quant.Temperature) -> quant.Energy:
    #     raise NotImplementedError

    @classmethod
    def dG_rxn(cls, T: quant.Temperature) -> quant.Energy:
        return cls.dH_rxn(T) - T * cls.dS_rxn(T)

    @classmethod
    def Keq(cls, T: quant.Temperature) -> float:
        return np.exp(-cls.dG_rxn(T).si / (quant.R.si * T.si))  # type: ignore

    @classmethod
    def check_components(cls, p0, allow_component_mismatch):
        if p0.keys != list(cls.COMPONENTS.keys()) and not allow_component_mismatch:
            raise ValueError("Partial pressure keys do not match reaction components.")

    def equilibrate(
        self,
        p0: quant.Pressure,
        T: quant.Temperature,
        Keq: float | None = None,
        fug_coeff: NDArray | None = None,
        allow_component_mismatch: bool = False,
        limiting_reactant: str | None = None,
    ):
        """
        Pressure in bar
        """
        if limiting_reactant is None:
            limiting_reactant = self.DEFAULT_LIMITING_REACTANT
        self.check_components(p0, allow_component_mismatch=allow_component_mismatch)

        if allow_component_mismatch:
            p0_bar = np.array([p0[comp].bar for comp in self.comp_list()])
            p0 = quant.Pressure(bar=p0_bar.astype(float), keys=self.comp_list())

        # remove inert
        # p0_bar = np.array([p0[comp].bar for comp in p0.keys if comp != "inert"])
        # p0 = quant.Pressure(
        #     bar=p0_bar.astype(float), keys=[key for key in p0.keys if key != "inert"]
        # )

        P_bar = np.sum(p0.bar)
        initial_total_moles = 100.0
        initial_molfrac = p0.bar / P_bar
        initial_moles = initial_molfrac * initial_total_moles

        std_state_fugacity_bar = quant.Pressure(
            atm=np.ones(len(self.COMPONENTS)).astype(float)
        ).bar
        if fug_coeff is None:
            fug_coeff = np.ones(len(self.COMPONENTS)).astype(float)

        stoich_coeff = self.STOICH_COEFF
        if Keq is None:
            Keq = type(self).Keq(T=T)

        def objective(extent):
            moles = initial_moles + extent * stoich_coeff
            if np.any(moles < 0):
                return 1e10
            total_moles = np.sum(moles)
            molfrac = moles / total_moles
            fugacity = molfrac * fug_coeff * P_bar
            activity = fugacity / std_state_fugacity_bar
            Ka = np.prod(activity**stoich_coeff)
            if Ka <= 0:
                return 1e10
            log_error = np.log(Ka) - np.log(Keq)  # type: ignore
            return log_error * log_error

        # Calculate extent bounds from stoichiometry
        # Maximum extent limited by complete consumption of any reactant
        adj_init_mol_reactants = np.array(
            [
                mol / stoich
                for mol, stoich in zip(initial_moles, stoich_coeff)
                if stoich < 0
            ]
        )
        min_extent = 1e-5  # Small positive value to avoid numerical issues
        max_extent = np.min(-adj_init_mol_reactants) * 0.999  # Leave small margin

        # Use bounded scalar minimization - more efficient and robust for 1D problems
        result = minimize_scalar(
            objective,
            bounds=(min_extent, max_extent),
            method="bounded",
            options={"xatol": 1e-8, "maxiter": 500},
        )

        if result.success:
            self.extent = quant.Moles(si=result.x)
            initial_moles = quant.Moles(si=initial_moles, keys=self.comp_list())
            moles = initial_moles + self.extent * self.STOICH_COEFF
            self.eq_conversion = (
                initial_moles[limiting_reactant] - moles[limiting_reactant]
            ) / initial_moles[limiting_reactant]
            total_moles = quant.Moles(si=np.sum(moles.si))
            self.eq_molfrac = moles / total_moles
        else:
            raise ValueError("Optimization failed: " + result.message)
