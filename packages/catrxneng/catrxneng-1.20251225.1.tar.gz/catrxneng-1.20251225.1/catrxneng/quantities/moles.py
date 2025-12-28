from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class Moles(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        mol: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, mol]) > 1:
            raise ValueError("Only one unit (si or mol) should be specified")
        if si is not None:
            self.si = si
        elif mol is not None:
            self.mol = mol
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def mol(self):
        return self.si

    @mol.setter
    def mol(self, value):
        self.si = value
