import os
from importlib import import_module
from typing import cast
import numpy as np
from numpy.typing import NDArray
import pandas as pd
from math import log10, floor
from typing import TYPE_CHECKING

from .notebook import Notebook

if TYPE_CHECKING:
    from ..kinetic_models import KineticModel


def divide(x, y):
    if isinstance(y, (np.ndarray, pd.Series)):
        y_safe = y.copy()
        y_safe[y_safe == 0] = np.nan
    else:
        y_safe = np.nan if y == 0 else y

    return x / y_safe


def getconf(conf_name, variable):
    conf_module_path = os.getenv("CONF_MODULE_PATH")
    module_path = f"{conf_module_path}.{conf_name}"
    conf_module = import_module(module_path)
    return getattr(conf_module, variable)


def filter_df(df: pd.DataFrame, col: str, range: list) -> pd.DataFrame:
    filtered_df = df[(df[col] > range[0]) & (df[col] < range[1])]
    return cast(pd.DataFrame, filtered_df.reset_index(drop=True))


def get_unique_values(series: pd.Series, tol: float) -> np.typing.NDArray:
    rounded = (series / tol).round() * tol
    return rounded.unique()


def apply_sig_figs(x: float, n: int = 3) -> str:
    if n < 1:
        raise ValueError("n must be a positive integer.")
    if x == 0 or np.isnan(x):
        return str(x)
    magnitude = floor(log10(abs(x)))

    # Use scientific notation with exponents as multiples of 3 (millions, billions, trillions, micrometers, etc.)
    if magnitude >= 6 or magnitude <= -6:
        exponent = (magnitude // 3) * 3
        mantissa = abs(x) / (10**exponent)
        mantissa_magnitude = floor(log10(mantissa))
        mantissa_precision = max(0, n - 1 - mantissa_magnitude)
        sign = "-" if x < 0 else ""
        exp_sign = "+" if exponent >= 0 else ""
        return f"{sign}{mantissa:.{mantissa_precision}f}e{exp_sign}{exponent}"

    rounded = round(x, -magnitude + (n - 1))
    precision = max(0, n - magnitude - 1)
    return f"{rounded:.{precision}f}"
    return f"{rounded:.{precision}f}"


def apply_sig_figs_to_df(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    float_cols = df.select_dtypes(include=["float64", "float32"]).columns
    df.loc[:, float_cols] = df[float_cols].map(lambda x: apply_sig_figs(x, n))
    return df


def compute_aggregate_species_value(
    df: pd.DataFrame,
    species_class: str,
    value_type: str,  # e.g. "dnstr_molfrac"
    KM: "KineticModel",
    incl_methane: bool = False,
) -> NDArray:
    """
    Compute things like total olefin partial pressure from individual olefin partial pressures.
    """
    species_list = [
        species_id
        for species_id, species in KM.COMPONENTS.items()
        if species.CLASS == species_class
    ]
    if not incl_methane:
        try:
            species_list.remove("ch4")
        except ValueError:
            pass

    filtered_df = df[[col for col in df.columns if f"_{value_type}" in col]]
    cols = [
        col
        for col in filtered_df.columns
        if col.replace(f"_{value_type}", "") in species_list
    ]
    filtered_df = filtered_df[cols]
    return cast(NDArray, filtered_df.sum(axis=1).values)


def compute_molfracs_from_molar_flowrates(
    df: pd.DataFrame, kinetic_model: "KineticModel"
) -> pd.DataFrame:
    total_dnstr_molh = df.filter(like="_dnstr_molh").sum(axis=1)
    for col in df.columns:
        if "_dnstr_molh" in col:
            species_id = col.replace("_dnstr_molh", "")
            if species_id in kinetic_model.COMPONENTS:
                df[f"{species_id}_dnstr_molfrac"] = (
                    df[f"{species_id}_dnstr_molh"] / total_dnstr_molh
                )
    return df


def compute_partial_pressures_from_molfracs(
    df: pd.DataFrame, kinetic_model: "KineticModel"
):
    for col in df.columns:
        if "_dnstr_molfrac" in col:
            species_id = col.replace("_dnstr_molfrac", "")
            if species_id in kinetic_model.COMPONENTS:
                df[f"{species_id}_dnstr_bar"] = (
                    df[f"{species_id}_dnstr_molfrac"] * df["pressure"]
                )
    return df


from .influx import Influx
from .time import Time, time_format, date_format
