from .quantity import Quantity
from .temperature import Temperature
from .energy import Energy


class GasConstant(Quantity):

    si = 8.314
    JmolK = si
    m3PaKmol = si
    kJmolK = 0.008314
    LbarKmol = 0.08314

    @classmethod
    def __mul__(cls, other):
        if isinstance(other, Temperature):
            si = cls.si * other.si
            return Energy(si=si)
        return NotImplemented

    @classmethod
    def __rmul__(cls, other):
        if isinstance(other, Temperature):
            si = other.si * cls.si
            return Energy(si=si)
        return NotImplemented
