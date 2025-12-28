from typing import Any, Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class MolarFlowRate(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        mols: Optional[float | NDArray] = None,
        molmin: Optional[float | NDArray] = None,
        molh: Optional[float | NDArray] = None,
        mmolh: Optional[float | NDArray] = None,
        smLmin: Optional[float | NDArray] = None,
        smLh: Optional[float | NDArray] = None,
        nmLmin: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if (
            sum(
                x is not None
                for x in [si, mols, molmin, molh, mmolh, smLmin, smLh, nmLmin]
            )
            > 1
        ):
            raise ValueError("Only one molar flow rate unit should be specified")
        if si is not None:
            self.si = si
        elif mols is not None:
            self.mols = mols
        elif molmin is not None:
            self.molmin = molmin
        elif molh is not None:
            self.molh = molh
        elif mmolh is not None:
            self.mmolh = mmolh
        elif smLmin is not None:
            self.smLmin = smLmin
        elif smLh is not None:
            self.smLh = smLh
        elif nmLmin is not None:
            self.nmLmin = nmLmin
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def mols(self) -> NDArray[np.number[Any]] | float:
        return self.si

    @mols.setter
    def mols(self, value):
        self.si = value

    @property
    def molmin(self) -> NDArray[np.number[Any]] | float:
        return self.si * 60

    @molmin.setter
    def molmin(self, value):
        self.si = value / 60

    @property
    def molh(self) -> NDArray[np.number[Any]] | float:
        return self.si * 3600

    @molh.setter
    def molh(self, value):
        self.si = value / 3600

    @property
    def mmolh(self) -> NDArray[np.number[Any]] | float:
        return self.si * 3600 * 1000

    @mmolh.setter
    def mmolh(self, value):
        self.si = value / 3600 / 1000

    @property
    def smLmin(self) -> NDArray[np.number[Any]] | float:
        return self.si * 60 * 22.4 * 1000

    @smLmin.setter
    def smLmin(self, value):
        self.si = value / 60 / 22.4 / 1000

    @property
    def smLh(self) -> NDArray[np.number[Any]] | float:
        return self.si * 3600 * 22.4 * 1000

    @smLh.setter
    def smLh(self, value):
        self.si = value / 3600 / 22.4 / 1000

    @property
    def nmLmin(self) -> NDArray[np.number[Any]] | float:
        return self.si * 60 * 24.05 * 1000

    @nmLmin.setter
    def nmLmin(self, value):
        self.si = value / 60 / 24.05 / 1000
