import numpy as np
from typing import Optional
from numpy.typing import NDArray

from . import Quantity, Temperature, Energy


class RateConstant(Quantity):
    # _UNITS_EXCLUDE_ATTRS = {
    #     "Ea",
    #     "order",
    #     "Tref",
    #     "T",
    #     "kref_si",
    #     "k0_si",
    # }

    def __init__(
        self,
        Ea: Energy,
        order: float,
        Tref: Temperature,
        *,
        si: Optional[float | NDArray | list[float]] = None,
        molskgcatPa: Optional[float | NDArray | list[float]] = None,
        molhgcatbar: Optional[float | NDArray | list[float]] = None,
        molmingcatbar: Optional[float | NDArray | list[float]] = None,
        molskgcatbar: Optional[float | NDArray | list[float]] = None,
        Lgcatmin: Optional[float | NDArray | list[float]] = None,
        keys: Optional[list[str]] = None,
    ):
        self.Ea = Ea
        self.order = order
        self.Tref = Tref
        # if self.Tref:
        #     self.T: Temperature = self.Tref
        # else:
        #     self.T = Temperature(K=298)

        if (
            sum(
                x is not None
                for x in [
                    si,
                    molskgcatPa,
                    molhgcatbar,
                    molmingcatbar,
                    molskgcatbar,
                    Lgcatmin,
                ]
            )
            > 1
        ):
            raise ValueError("Only one rate constant unit should be specified")
        if si is not None:
            self.si = si
        elif molskgcatPa is not None:
            self.molskgcatPa = molskgcatPa
        elif molhgcatbar is not None:
            self.molhgcatbar = molhgcatbar
        elif molmingcatbar is not None:
            self.molmingcatbar = molmingcatbar
        elif molskgcatbar is not None:
            self.molskgcatbar = molskgcatbar
        elif Lgcatmin is not None:
            self.Lgcatmin = Lgcatmin
        else:
            self.si = np.zeros(len(keys)) if keys else 0

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

        # if self.Tref:
        #     self.kref_si = self.si
        # else:
        #     self.k0_si = self.si

    @property
    def molskgcatPa(self):
        return self.si

    @molskgcatPa.setter
    def molskgcatPa(self, value):
        self.si = value

    @property
    def molhgcatbar(self):
        return self.si * 3600 / 1000 * (100000**self.order)

    @molhgcatbar.setter
    def molhgcatbar(self, value):
        self.si = value / 3600 * 1000 / (100000**self.order)

    @property
    def molmingcatbar(self):
        return self.si * 60 / 1000 * (100000**self.order)

    @molmingcatbar.setter
    def molmingcatbar(self, value):
        self.si = value / 60 * 1000 / (100000**self.order)

    @property
    def molskgcatbar(self):
        return self.si * (100000**self.order)

    @molskgcatbar.setter
    def molskgcatbar(self, value):
        self.si = value / (100000**self.order)

    @property
    def Lgcatmin(self):
        from . import R

        return self.molmingcatbar * (R.LbarKmol * self.T.K) ** self.order

    @Lgcatmin.setter
    def Lgcatmin(self, value):
        from . import R

        self.molmingcatbar = value / ((R.LbarKmol * self.T.K) ** self.order)

    def __call__(self, T: Temperature) -> "RateConstant":
        from . import R

        self.T = T
        # if self.Tref is not None:
        si = self.si * np.exp(-self.Ea.si / R.si * (1 / T.si - 1 / self.Tref.si))
        # else:
        #     si = self.si * np.exp(-self.Ea.si / R.si / T.si)
        new_rate_constant = RateConstant(
            si=si, Ea=self.Ea, order=self.order, Tref=self.Tref
        )
        new_rate_constant.T = T
        return new_rate_constant

    # def set_temp(self, T):
    #     self.T = T
    #     return self
