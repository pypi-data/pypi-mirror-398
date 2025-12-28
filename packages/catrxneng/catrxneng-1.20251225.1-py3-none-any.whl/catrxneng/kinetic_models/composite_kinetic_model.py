import numpy as np
from numpy.typing import NDArray

from .. import species as species
from .kinetic_model import KineticModel
from .. import quantities as quant


class CompositeKineticModel(KineticModel):
    KINETIC_MODEL_CLASSES: list[type[KineticModel]]

    map_child_components_to_parent_components: list[list[int]]
    catalyst_fraction: NDArray

    kinetic_models: list[KineticModel]

    def __init_subclass__(cls):
        cls.REACTIONS = {
            id: REACTION_CLASS
            for KM in cls.KINETIC_MODEL_CLASSES
            for id, REACTION_CLASS in KM.REACTIONS.items()
        }
        super().__init_subclass__()

    def __init__(
        self,
        catalyst_frac: NDArray,
        child_kinetic_models_kwargs: list = [],
        T: quant.Temperature | None = None,
    ):
        self.catalyst_frac = np.asarray(catalyst_frac)
        self.kinetic_models: list[KineticModel] = [
            KM(T=T, **kwargs)
            for KM, kwargs in zip(
                self.KINETIC_MODEL_CLASSES, child_kinetic_models_kwargs
            )
        ]
        self.T = T
        self.map_child_components_to_parent_components = [
            [self.comp_list().index(comp) for comp in KM.comp_list()]
            for KM in self.KINETIC_MODEL_CLASSES
        ]

    @property
    def T(self):
        return self._T

    @T.setter
    def T(self, value):
        self._T = value
        for kinetic_model in self.kinetic_models:
            kinetic_model.T = value
