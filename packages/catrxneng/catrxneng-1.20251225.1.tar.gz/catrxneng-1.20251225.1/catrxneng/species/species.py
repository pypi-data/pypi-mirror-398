from .. import quantities as quant


class Species:
    CLASS = "species"
    C_ATOMS = 0
    H_ATOMS = 0
    O_ATOMS = 0
    N_ATOMS = 0
    MOL_WEIGHT = 0.0
    NIST_THERMO_PARAMS: list
    HF_298 = quant.Energy(si=0)
    S_298 = quant.Entropy(si=0)
    HF_298_GAS = quant.Energy(si=0)
    S_298_GAS = quant.Entropy(si=0)
    DH_VAP_298 = quant.Energy(si=0)
    DS_VAP_298 = quant.Entropy(si=0)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def _get_thermo_params(cls, T) -> dict[str, list]:
        for thermo_params in cls.NIST_THERMO_PARAMS:
            if thermo_params["min_temp_K"] <= T.K <= thermo_params["max_temp_K"]:
                return thermo_params
        raise ValueError(
            f"Temperature outside range for {cls.__name__} thermodynamic parameters."
        )

    @classmethod
    def Hf_gas_shomate(cls, T) -> quant.Energy:
        return quant.Energy(si=0)

    @classmethod
    def S_gas_shomate(cls, T):
        return quant.Entropy(si=0)

    @classmethod
    def Cp_gas(cls, T):
        return quant.HeatCapacity(si=0)
