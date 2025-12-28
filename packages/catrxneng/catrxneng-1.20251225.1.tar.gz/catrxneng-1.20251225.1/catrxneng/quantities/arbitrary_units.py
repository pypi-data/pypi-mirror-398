from typing import Optional
from numpy.typing import NDArray
import numpy as np
from .quantity import Quantity


class ArbitraryUnits(Quantity):

    def __init__(
        self,
        value: Optional[float | NDArray] = None,
        units: Optional[str] = None,
        units_pwr: Optional[float] = None,
        *,
        si: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        self.value = value
        self.units = units
        self.units_pwr = units_pwr

        if si is not None:
            self.si = si
        elif value is not None:
            self.si = value
        else:
            self.si = np.zeros(len(keys)) if keys else 0

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)
