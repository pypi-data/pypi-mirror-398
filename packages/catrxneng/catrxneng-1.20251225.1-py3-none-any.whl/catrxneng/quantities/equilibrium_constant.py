from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class EquilibriumConstant(Quantity):
    def __init__(
        self,
        order: float,
        *,
        si: Optional[float | NDArray] = None,
        Pa: Optional[float | NDArray] = None,
        bar: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        self.order = order

        if sum(x is not None for x in [si, Pa, bar]) > 1:
            raise ValueError("Only one equilibrium constant unit should be specified")
        if si is not None:
            self.si = si
        elif Pa is not None:
            self.Pa = Pa
        elif bar is not None:
            self.bar = bar
        else:
            self.si = np.zeros(len(keys)) if keys else 0

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def Pa(self):
        return self.si

    @Pa.setter
    def Pa(self, value):
        self.si = value

    @property
    def bar(self):
        return self.si * (100000**self.order)

    @bar.setter
    def bar(self, value):
        self.si = value / (100000**self.order)
