from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class HeatCapacity(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        JmolK: Optional[float | NDArray] = None,
        kJmolK: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, JmolK, kJmolK]) > 1:
            raise ValueError(
                "Only one heat capacity unit (si, JmolK, or kJmolK) should be specified"
            )
        if si is not None:
            self.si = si
        elif JmolK is not None:
            self.JmolK = JmolK
        elif kJmolK is not None:
            self.kJmolK = kJmolK
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def JmolK(self):
        return self.si

    @JmolK.setter
    def JmolK(self, value):
        self.si = value

    @property
    def kJmolK(self):
        return self.si / 1000

    @kJmolK.setter
    def kJmolK(self, value):
        self.si = value * 1000

    # def __mul__(self, other):
    #     keys = self.get_keys(self, other)
    #     if isinstance(other, Temperature):
    #         si = self.si * other.si
    #         return Energy(si=si, keys=keys)
    #     else:
    #         return super().__mul__(other)

    # def __rmul__(self, other):
    #     keys = self.get_keys(self, other)
    #     if isinstance(other, Temperature):
    #         si = other.si * self.si
    #         return Energy(si=si, keys=keys)
    #     else:
    #         return super().__rmul__(other)
