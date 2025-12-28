from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class ReactionRate(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        molskgcat: Optional[float | NDArray] = None,
        molhgcat: Optional[float | NDArray] = None,
        mmolhgcat: Optional[float | NDArray] = None,
        molhkgcat: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if (
            sum(x is not None for x in [si, molskgcat, molhgcat, mmolhgcat, molhkgcat])
            > 1
        ):
            raise ValueError("Only one reaction rate unit should be specified")
        if si is not None:
            self.si = si
        elif molskgcat is not None:
            self.molskgcat = molskgcat
        elif molhgcat is not None:
            self.molhgcat = molhgcat
        elif mmolhgcat is not None:
            self.mmolhgcat = mmolhgcat
        elif molhkgcat is not None:
            self.molhkgcat = molhkgcat
        else:
            self.si = np.zeros(len(keys))

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
        return self.si * 3600 / 1000

    @molhgcat.setter
    def molhgcat(self, value):
        self.si = value / 3600 * 1000

    @property
    def mmolhgcat(self):
        return self.si * 3600

    @mmolhgcat.setter
    def mmolhgcat(self, value):
        self.si = value / 3600

    @property
    def molhkgcat(self):
        return self.si * 3600

    @molhkgcat.setter
    def molhkgcat(self, value):
        self.si = value / 3600

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
