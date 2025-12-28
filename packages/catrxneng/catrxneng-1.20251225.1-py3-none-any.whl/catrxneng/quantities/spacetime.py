from typing import TYPE_CHECKING, Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity

if TYPE_CHECKING:
    from ..phases.gas_mixture import GasMixture


class SpaceTime(Quantity):

    def __init__(
        self,
        gas_mixture: "GasMixture" = None,
        *,
        si: Optional[float | NDArray] = None,
        skgcatmol: Optional[float | NDArray] = None,
        hgcatmol: Optional[float | NDArray] = None,
        hgcatsmL: Optional[float | NDArray] = None,
        hr: Optional[float | NDArray] = None,
        sec: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        self.gas_mixture = gas_mixture

        if sum(x is not None for x in [si, skgcatmol, hgcatmol, hgcatsmL, hr, sec]) > 1:
            raise ValueError("Only one spacetime unit should be specified")
        if si is not None:
            self.si = si
        elif skgcatmol is not None:
            self.skgcatmol = skgcatmol
        elif hgcatmol is not None:
            self.hgcatmol = hgcatmol
        elif hgcatsmL is not None:
            self.hgcatsmL = hgcatsmL
        elif hr is not None:
            self.hr = hr
        elif sec is not None:
            self.sec = sec
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def skgcatmol(self):
        return self.si

    @skgcatmol.setter
    def skgcatmol(self, value):
        self.si = value

    @property
    def hgcatmol(self):
        return self.si / 3600 * 1000

    @hgcatmol.setter
    def hgcatmol(self, value):
        self.si = value * 3600 / 1000

    @property
    def hgcatsmL(self):
        return self.si / 3600 / 22.4

    @hgcatsmL.setter
    def hgcatsmL(self, value):
        self.si = value * 3600 * 22.4

    @property
    def hr(self):
        try:
            return self.si * 1000 / self.gas_mixture.avg_mol_weight / 3600
        except TypeError:
            raise AttributeError("Spacetime has no gas mixture assigned.")

    @hr.setter
    def hr(self, value):
        try:
            self.si = value / 1000 * self.gas_mixture.avg_mol_weight * 3600
        except TypeError:
            raise AttributeError("Spacetime has no gas mixture assigned.")

    @property
    def sec(self):
        try:
            return self.si * 1000 / self.gas_mixture.avg_mol_weight
        except TypeError:
            raise AttributeError("Spacetime has no gas mixture assigned.")

    @sec.setter
    def sec(self, value):
        try:
            self.si = value / 1000 * self.gas_mixture.avg_mol_weight
        except TypeError:
            raise AttributeError("Spacetime has no gas mixture assigned.")
