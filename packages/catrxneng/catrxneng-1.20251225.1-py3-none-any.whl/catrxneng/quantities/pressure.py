from typing import Any, Optional
from numpy.typing import NDArray
import numpy as np
import pandas as pd

from .quantity import Quantity


class Pressure(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        Pa: Optional[float | NDArray] = None,
        bar: Optional[float | NDArray] = None,
        kPa: Optional[float | NDArray] = None,
        atm: Optional[float | NDArray] = None,
        MPa: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, Pa, bar, kPa, atm, MPa]) > 1:
            raise ValueError(
                "Only one pressure unit (si, Pa, bar, kPa, atm, or MPa) should be specified"
            )
        if si is not None:
            self.si = si
        elif Pa is not None:
            self.Pa = Pa
        elif bar is not None:
            self.bar = bar
        elif kPa is not None:
            self.kPa = kPa
        elif atm is not None:
            self.atm = atm
        elif MPa is not None:
            self.MPa = MPa
        else:
            self.si = np.zeros(len(keys))

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
    def bar(
        self,
    ) -> pd.Series | NDArray[np.number[Any]] | float:
        return self.si / 100000

    @bar.setter
    def bar(self, value):
        self.si = value * 100000

    @property
    def kPa(self):
        return self.si / 1000

    @kPa.setter
    def kPa(self, value):
        self.si = value * 1000

    @property
    def atm(self):
        return self.si / 101325

    @atm.setter
    def atm(self, value):
        self.si = value * 101325

    @property
    def MPa(self):
        return self.si / 1000000

    @MPa.setter
    def MPa(self, value):
        self.si = value * 1000000
