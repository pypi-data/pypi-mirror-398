from typing import TYPE_CHECKING

from .material import Material

if TYPE_CHECKING:
    from ..kinetic_models import KineticModel


class Catalyst(Material):
    KINETIC_MODEL_CLASS: "KineticModel"
    kinetic_model: "KineticModel"

    def __init__(self):
        self.common_name = "Catalyst"
