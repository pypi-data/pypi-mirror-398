from typing import Optional
from numpy.typing import NDArray
import numpy as np
from .quantity import Quantity


class Concentration(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        molm3: Optional[float | NDArray] = None,
        molL: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, molm3, molL]) > 1:
            raise ValueError(
                "Only one concentration unit (si, molm3, or molL) should be specified"
            )
        if si is not None:
            self.si = si
        elif molm3 is not None:
            self.molm3 = molm3
        elif molL is not None:
            self.molL = molL
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def molm3(self):
        return self.si

    @molm3.setter
    def molm3(self, value):
        self.si = value

    @property
    def molL(self):
        return self.si / 1000

    @molL.setter
    def molL(self, value):
        self.si = value * 1000
