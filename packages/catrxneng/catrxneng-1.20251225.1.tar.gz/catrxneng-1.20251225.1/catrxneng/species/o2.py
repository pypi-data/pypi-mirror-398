from .species import Species
from ..quantities import Energy, Entropy


class O2(Species):
    CLASS = "diatomic_gas"
    O_ATOMS = 2
    MOL_WEIGHT = 32
    HF_298_GAS = Energy(kJmol=0)
    S_298_GAS = Entropy(JmolK=205.15)
    NIST_THERMO_PARAMS = [
        {
            "min_temp_K": 100,
            "max_temp_K": 700,
            "A": 31.32,
            "B": -20.24,
            "C": 57.87,
            "D": -36.51,
            "E": -0.007374,
            "F": -8.903,
            "G": 246.79,
            "H": 0,
        },
        {
            "min_temp_K": 700,
            "max_temp_K": 2000,
            "A": 30.03,
            "B": 8.773,
            "C": -3.988,
            "D": 0.7883,
            "E": -0.7416,
            "F": -11.32,
            "G": 236.17,
            "H": 0,
        },
    ]
