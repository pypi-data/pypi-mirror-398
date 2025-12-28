from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class Temperature(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | np.ndarray] = None,
        K: Optional[float | np.ndarray] = None,
        C: Optional[float | np.ndarray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, K, C]) > 1:
            raise ValueError(
                "Only one temperature unit (si, K, or C) should be specified"
            )
        if si is not None:
            self.si = si
        elif K is not None:
            self.K = K
        elif C is not None:
            self.C = C
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def K(self):
        return self.si

    @K.setter
    def K(self, value: float | NDArray):
        self.si = value

    @property
    def C(self):
        return self.si - 273

    @C.setter
    def C(self, value):
        self.si = value + 273

    def __mul__(self, other):
        from .energy import Energy
        from .entropy import Entropy

        if isinstance(other, Entropy):
            si = self.si * other.si
            return Energy(si=si)
        else:
            return super().__mul__(other)

    def __rmul__(self, other):
        from .energy import Energy
        from .entropy import Entropy

        if isinstance(other, Entropy):
            si = other.si * self.si
            return Energy(si=si)
        else:
            return super().__rmul__(other)
