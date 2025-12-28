from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class Fraction(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        pct: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, pct]) > 1:
            raise ValueError("Only one fraction unit (si or pct) should be specified")
        if si is not None:
            self.si = si
        elif pct is not None:
            self.pct = pct
        else:
            self.si = np.zeros(len(keys)) if keys else 0

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def pct(self):
        return self.si * 100

    @pct.setter
    def pct(self, value):
        self.si = value / 100
