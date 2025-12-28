from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class VolumetricFlowRate(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        m3s: Optional[float | NDArray] = None,
        mLs: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, m3s, mLs]) > 1:
            raise ValueError(
                "Only one volumetric flow rate unit (si, m3s, or mLs) should be specified"
            )
        if si is not None:
            self.si = si
        elif m3s is not None:
            self.m3s = m3s
        elif mLs is not None:
            self.mLs = mLs
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def m3s(self):
        return self.si

    @m3s.setter
    def m3s(self, value):
        self.si = value

    @property
    def mLs(self):
        return self.si * 1000 * 1000

    @mLs.setter
    def mLs(self, value):
        self.si = value / 1000 / 1000
