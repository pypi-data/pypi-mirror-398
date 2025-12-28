from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity
from .. import utils


class TimeDelta(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        sec: Optional[float | NDArray] = None,
        min: Optional[float | NDArray] = None,
        hr: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, sec, min, hr]) > 1:
            raise ValueError(
                "Only one time unit (si, sec, min, or hr) should be specified"
            )
        if si is not None:
            self.si = si
        elif sec is not None:
            self.sec = sec
        elif min is not None:
            self.min = min
        elif hr is not None:
            self.hr = hr
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def sec(self):
        return self.si

    @sec.setter
    def sec(self, value):
        self.si = value

    @property
    def min(self):
        return utils.divide(self.si, 60)

    @min.setter
    def min(self, value):
        self.si = value * 60

    @property
    def hr(self):
        return utils.divide(self.si, 3600)

    @hr.setter
    def hr(self, value):
        self.si = value * 3600
