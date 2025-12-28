from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class Energy(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        Jmol: Optional[float | NDArray] = None,
        kJmol: Optional[float | NDArray] = None,
        kcalmol: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, Jmol, kJmol, kcalmol]) > 1:
            raise ValueError(
                "Only one energy unit (si, Jmol, kJmol, or kcalmol) should be specified"
            )
        if si is not None:
            self.si = si
        elif Jmol is not None:
            self.Jmol = Jmol
        elif kJmol is not None:
            self.kJmol = kJmol
        elif kcalmol is not None:
            self.kcalmol = kcalmol
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def Jmol(self):
        return self.si

    @Jmol.setter
    def Jmol(self, value):
        self.si = value

    @property
    def kJmol(self):
        return self.si / 1000

    @kJmol.setter
    def kJmol(self, value):
        self.si = value * 1000

    @property
    def kcalmol(self):
        return self.si / 4184

    @kcalmol.setter
    def kcalmol(self, value):
        self.si = value * 4184
