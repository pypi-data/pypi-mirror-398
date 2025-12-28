from typing import TYPE_CHECKING, Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity

if TYPE_CHECKING:
    from ..phases.gas_mixture import GasMixture


class WHSV(Quantity):
    def __init__(
        self,
        gas_mixture: "GasMixture" = None,
        *,
        si: Optional[float | NDArray] = None,
        molskgcat: Optional[float | NDArray] = None,
        molhgcat: Optional[float | NDArray] = None,
        smLhgcat: Optional[float | NDArray] = None,
        inv_h: Optional[float | NDArray] = None,
        inv_s: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        self.gas_mixture = gas_mixture

        if (
            sum(
                x is not None for x in [si, molskgcat, molhgcat, smLhgcat, inv_h, inv_s]
            )
            > 1
        ):
            raise ValueError("Only one WHSV unit should be specified")
        if si is not None:
            self.si = si
        elif molskgcat is not None:
            self.molskgcat = molskgcat
        elif molhgcat is not None:
            self.molhgcat = molhgcat
        elif smLhgcat is not None:
            self.smLhgcat = smLhgcat
        elif inv_h is not None:
            self.inv_h = inv_h
        elif inv_s is not None:
            self.inv_s = inv_s
        else:
            self.si = np.zeros(len(keys)) if keys else 0

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def molskgcat(self):
        return self.si

    @molskgcat.setter
    def molskgcat(self, value):
        self.si = value

    @property
    def molhgcat(self):
        return self.si * 3.6

    @molhgcat.setter
    def molhgcat(self, value):
        self.si = value / 3.6

    @property
    def smLhgcat(self):
        return self.si * 3600 * 22.4

    @smLhgcat.setter
    def smLhgcat(self, value):
        self.si = value / 3600 / 22.4

    @property
    def inv_h(self):
        try:
            return self.si / 1000 * self.gas_mixture.avg_mol_weight * 3600
        except AttributeError:
            raise AttributeError("WHSV has no gas mixture assigned.")

    @inv_h.setter
    def inv_h(self, value):
        try:
            self.si = value * 1000 / self.gas_mixture.avg_mol_weight / 3600
        except TypeError:
            raise AttributeError("WHSV has no gas mixture assigned.")

    @property
    def inv_s(self):
        try:
            return self.si / 1000 * self.gas_mixture.avg_mol_weight
        except TypeError:
            raise AttributeError("WHSV has no gas mixture assigned.")

    @inv_s.setter
    def inv_s(self, value):
        try:
            self.si = value * 1000 / self.gas_mixture.avg_mol_weight
        except TypeError:
            raise AttributeError("WHSV has no gax mixture assigned.")

    def __mul__(self, other):
        from .mass import Mass
        from .molar_flow_rate import MolarFlowRate

        if isinstance(other, Mass):
            si = self.si * other.si
            return MolarFlowRate(si=si)
        return super().__mul__(other)

    def __rmul__(self, other):
        from .mass import Mass
        from .molar_flow_rate import MolarFlowRate

        if isinstance(other, Mass):
            si = self.si * other.si
            return MolarFlowRate(si=si)
        return super().__rmul__(other)
