from typing import Optional
from numpy.typing import NDArray
import numpy as np

from .quantity import Quantity


class Mass(Quantity):

    def __init__(
        self,
        *,
        si: Optional[float | NDArray] = None,
        kg: Optional[float | NDArray] = None,
        g: Optional[float | NDArray] = None,
        keys: Optional[list] = None,
    ):
        if sum(x is not None for x in [si, kg, g]) > 1:
            raise ValueError("Only one mass unit (si, kg, or g) should be specified")
        if si is not None:
            self.si = si
        elif kg is not None:
            self.kg = kg
        elif g is not None:
            self.g = g
        else:
            self.si = np.zeros(len(keys))

        if keys is not None:
            self.keys = keys

        super().__init__(keys=keys)

    @property
    def kg(self):
        return self.si

    @kg.setter
    def kg(self, value):
        self.si = value

    @property
    def g(self):
        return self.si * 1000

    @g.setter
    def g(self, value):
        self.si = value / 1000

    def __mul__(self, other):
        from .whsv import WHSV
        from .molar_flow_rate import MolarFlowRate
        from .reaction_rate import ReactionRate

        if isinstance(other, (WHSV, ReactionRate)):
            si = self.si * other.si
            return MolarFlowRate(si=si)
        return super().__mul__(other)

    def __rmul__(self, other):
        from .whsv import WHSV
        from .molar_flow_rate import MolarFlowRate
        from .reaction_rate import ReactionRate

        if isinstance(other, (WHSV, ReactionRate)):
            si = self.si * other.si
            return MolarFlowRate(si=si)
        return super().__rmul__(other)
