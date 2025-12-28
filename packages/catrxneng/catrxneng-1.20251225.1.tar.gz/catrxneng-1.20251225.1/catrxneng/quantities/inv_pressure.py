from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class InversePressure(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        inv_Pa: Optional[float | NDArray] = None,
        inv_bar: Optional[float | NDArray] = None,
        inv_kPa: Optional[float | NDArray] = None,
        inv_atm: Optional[float | NDArray] = None,
        inv_MPa: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if (
            sum(x is not None for x in [si, inv_Pa, inv_bar, inv_kPa, inv_atm, inv_MPa])
            > 1
        ):
            raise ValueError("Only one inverse pressure unit should be specified")
        if si is not None:
            self.si = si
        elif inv_Pa is not None:
            self.inv_Pa = inv_Pa
        elif inv_bar is not None:
            self.inv_bar = inv_bar
        elif inv_kPa is not None:
            self.inv_kPa = inv_kPa
        elif inv_atm is not None:
            self.inv_atm = inv_atm
        elif inv_MPa is not None:
            self.inv_MPa = inv_MPa
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def inv_Pa(self):
        return self.si

    @inv_Pa.setter
    def inv_Pa(self, value):
        self.si = value

    @property
    def inv_bar(self):
        return self.si * 100000

    @inv_bar.setter
    def inv_bar(self, value):
        self.si = value / 100000

    @property
    def inv_kPa(self):
        return self.si * 1000

    @inv_kPa.setter
    def inv_kPa(self, value):
        self.si = value / 1000

    @property
    def inv_atm(self):
        return self.si * 101325

    @inv_atm.setter
    def inv_atm(self, value):
        self.si = value / 101325

    @property
    def inv_MPa(self):
        return self.si * 1000000

    @inv_MPa.setter
    def inv_MPa(self, value):
        self.si = value / 1000000
