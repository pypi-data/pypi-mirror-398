from .kinetic_model import KineticModel
from .. import quantities as quant


class ReverseKineticModel(KineticModel):
    FORWARD_MODEL: type[KineticModel]

    forward_model: KineticModel

    def __init_subclass__(cls):
        cls.REACTANTS = cls.FORWARD_MODEL.PRODUCTS
        cls.PRODUCTS = cls.FORWARD_MODEL.REACTANTS
        cls.REACTIONS = cls.FORWARD_MODEL.REACTIONS
        cls.STOICH_COEFF = -1.0 * cls.FORWARD_MODEL.STOICH_COEFF
        cls.KREF = cls.FORWARD_MODEL.KREF
        cls.EA = cls.FORWARD_MODEL.EA
        super().__init_subclass__()

    def __init__(self, T: quant.Temperature = None, **forward_model_kwargs):
        self.forward_model = self.FORWARD_MODEL(T=T, **forward_model_kwargs)
        super().__init__(T)

    def compute_temp_dependent_constants(self) -> None:
        self.forward_model.compute_temp_dependent_constants()

    def get_2d_reaction_rate_array(self, p: quant.Pressure) -> quant.ReactionRate:
        return -1.0 * self.forward_model.get_2d_reaction_rate_array(p)  # type: ignore

    def get_reaction_rates_molhgcat(self, p_array):
        return -1.0 * self.forward_model.get_reaction_rates_molhgcat(p_array)
