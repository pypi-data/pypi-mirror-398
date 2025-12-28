import numpy as np

from ... import species as species
from ...reactions import RWGS, FTS
from ...reactions import RWGS, FTS
from ... import quantities as quant


class Brubach2022:
    LIMITING_REACTANT = "co2"
    T_REF = quant.Temperature(C=300)
    COMPONENTS = {
        "co2": species.CO2,
        "h2": species.H2,
        "co": species.CO,
        "h2o": species.H2O,
        "c2h4": species.C2H4,
        "inert": species.Inert,
    }
    REACTIONS = {
        "rwgs": RWGS,
        "fts": FTS,
    }
    ORDER = np.array([1.5, 2.0])
    STOICH_COEFF = np.array(
        [
            [-1, -1, 1, 1, 0, 0],
            [0, -4, 2, 2, 1, 0],
        ]
    )
    a_rwgs = quant.Dimensionless(si=16.3)
    a_ft = quant.Dimensionless(si=9.07)
    b_ft = quant.InversePressure(inv_bar=2.44)

    def __init__(self, T=None, kref=None, Ea=None):
        self.kref = kref
        if self.kref is None:
            self.kref = np.array([8.13e-2, 6.39e-2])
        self.Ea = Ea
        if self.Ea is None:
            self.Ea = np.array([115, 67.8])  # kJ/mol
        super().__init__(T)

    def k_rwgs(self, T):
        return rate_const(T=T, Ea=self.Ea_rwgs, kref=self.kref_rwgs, Tref=self.Tref)

    def k_ft(self, T):
        return rate_const(T=T, Ea=self.Ea_ft, kref=self.kref_ft, Tref=self.Tref)

    def r_rwgs(self, T, p):
        fwd = p["co2"] * p["h2"] ** 0.5
        rev = p["co"] * p["h2o"] / (RWGS(T).Keq * p["h2"] ** 0.5)
        num = self.k_rwgs(T) * (fwd - rev)
        denom = (1 + self.a_rwgs * p["h2o"] / p["h2"]) ** 2
        rate = num / denom
        return quant.ReactionRate(si=rate.si)

    def r_ft(self, T, p):
        num = self.k_ft(T) * p["h2"] * p["co"]
        denom = (1 + self.a_ft * p["h2o"] / p[1] + self.b_ft * p["co"]) ** 2
        rate = num / denom
        return quant.ReactionRate(si=rate.si)

    @property
    def reaction_rate(self):
        return {
            "co2": lambda T, p: -self.r_rwgs(T, p),
            "h2": lambda T, p: -self.r_rwgs(T, p) - 2 * self.r_ft(T, p),
            "co": lambda T, p: self.r_rwgs(T, p) - self.r_ft(T, p),
            "h2o": lambda T, p: self.r_rwgs(T, p) + self.r_ft(T, p),
            "inert": lambda T, p: quant.ReactionRate(si=0),
        }
