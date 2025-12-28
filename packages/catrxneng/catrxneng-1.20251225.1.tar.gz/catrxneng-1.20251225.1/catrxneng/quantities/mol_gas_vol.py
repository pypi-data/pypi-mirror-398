from .quantity import Quantity


class MolarGasVolume():
    def __init__(self):
        self.STP = Quantity(Lmol=22.4)
        self.STP.m3mol = self.STP.Lmol / 1000
        self.STP.si = self.STP.m3mol
        self.NTP = Quantity(Lmol=24.05)
        self.NTP.m3mol = self.NTP.Lmol / 1000
        self.NTP.si = self.NTP.m3mol
    

