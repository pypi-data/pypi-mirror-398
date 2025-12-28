from typing import Optional
from numpy.typing import NDArray
import numpy as np
from .quantity import Quantity


class Dimensionless(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if si is not None:
            self.si = si
        else:
            self.si = np.zeros(len(keys)) if keys else 0

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)
