from .species import Species
from ..quantities import Energy, Entropy


class Graphite(Species):
    CLASS = "solid_carbon"
    C_ATOMS = 1
    MOL_WEIGHT = 12
    S_298 = Entropy(JmolK=5.6)

    def Cp(self, T):
        return HeatCapacity(JmolK=8.23)
