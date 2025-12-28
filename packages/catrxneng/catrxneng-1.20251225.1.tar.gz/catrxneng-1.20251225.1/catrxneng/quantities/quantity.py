from typing import Any, Optional
import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .. import utils


class Quantity:
    si: NDArray[np.number[Any]] | float
    keys: list
    _parent: "Quantity"
    _index: int

    def __init__(self, keys: Optional[list] = None) -> None:
        if keys:
            self.keys = keys
            self.key_index_map = {key: index for index, key in enumerate(self.keys)}
        else:
            self.keys = []

    def to_df(self, units: str) -> pd.DataFrame:
        return pd.DataFrame(getattr(self, units), columns=self.keys)

    @staticmethod
    def get_keys(obj1, obj2):
        keys = None
        if getattr(obj1, "keys", None) == getattr(obj2, "keys", None):
            keys = getattr(obj1, "keys", None)
        if getattr(obj1, "keys", None) not in (None, []):
            keys = obj1.keys
        if getattr(obj2, "keys", None) not in (None, []):
            keys = obj2.keys
        try:
            if keys is None:
                return None
            else:
                return keys.copy()
        except NameError:
            raise ValueError("Quantities have mismatching keys.")

    @property
    def size(self):
        if isinstance(self.si, np.ndarray):
            return self.si.size
        return 1

    def __getitem__(self, index):
        if isinstance(index, (tuple, list)) and all(isinstance(i, str) for i in index):
            try:
                indices = [self.keys.index(k) for k in index]
            except ValueError:
                raise KeyError("Some keys not found.")
            except AttributeError:
                raise KeyError("Keys not available.")
            si = np.asarray(self.si)[indices]
            keys = list(index)
            return type(self)(si=si, keys=keys)
        if isinstance(index, (int, np.integer)) and len(np.asarray(self.si).shape) == 2:
            si = np.asarray(self.si)[:, index]
            return type(self)(si=si, keys=self.keys.copy())
        if isinstance(index, str):
            # index = self.keys.index(index)
            idx = self.key_index_map[index]
            result = type(self)(si=self.si[idx])
            result._parent = self
            result._index = idx
            return result
        return type(self)(si=self.si[index])

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "si" and hasattr(self, "_parent") and hasattr(self, "_index"):
            assert isinstance(self._parent.si, np.ndarray)
            self._parent.si[self._index] = value

    def __delitem__(self, key):
        if isinstance(key, str):
            idx = self.key_index_map[key]
            self.si = np.delete(self.si, idx, axis=0)
            self.keys.pop(idx)
            self.key_index_map = {k: index for index, k in enumerate(self.keys)}

    def delete(self, key):
        del self[key]

    def __add__(self, other):
        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = self.si + value
        return type(self)(si=si, keys=keys)

    def __radd__(self, other):
        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = value + self.si
        return type(self)(si=si, keys=keys)

    def __sub__(self, other):
        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = self.si - value
        return type(self)(si=si, keys=keys)

    def __rsub__(self, other):
        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = value - self.si
        return type(self)(si=si, keys=keys)

    def __mul__(self, other):
        from .dimensionless import Dimensionless
        from .fraction import Fraction

        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = self.si * value
        if isinstance(other, (Dimensionless, Fraction, int, float, np.number)):
            return type(self)(si=si, keys=keys)
        if isinstance(self, (Dimensionless, Fraction, int, float, np.number)):
            try:
                return type(other)(si=si, keys=keys)
            except TypeError:
                return si
        return Quantity(si=si, keys=keys)

    def __rmul__(self, other):
        from .dimensionless import Dimensionless
        from .fraction import Fraction

        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = value * self.si
        if isinstance(other, (Dimensionless, Fraction, int, float, np.number)):
            return type(self)(si=si, keys=keys)
        if isinstance(self, Dimensionless):
            try:
                return type(other)(si=si, keys=keys)
            except TypeError:
                return si
        return Quantity(si=si, keys=keys)

    def __truediv__(self, other):
        from .fraction import Fraction
        from .dimensionless import Dimensionless

        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = utils.divide(self.si, value)
        if isinstance(other, Fraction):
            return type(self)(si=si, keys=keys)

        if isinstance(other, (int, float, np.number, Fraction, Dimensionless)):
            return type(self)(si=si, keys=keys)

        if type(other) is type(self) and not type(self) is Quantity:
            return Fraction(si=si, keys=keys)
        return Quantity(si=si, keys=keys)

    def __rtruediv__(self, other):
        from .fraction import Fraction

        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = np.divide(value, self.si)
        if isinstance(other, Fraction):
            return type(self)(si=si, keys=keys)
        if type(other) is type(self):
            return Fraction(si=si, keys=keys)
        return Quantity(si=si, keys=keys)

    def __pow__(self, other):
        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = self.si**value
        return Quantity(si=si, keys=keys)

    def __rpow__(self, other):
        keys = self.get_keys(self, other)
        try:
            value = other.si
        except AttributeError:
            value = other
        si = value**self.si
        return Quantity(si=si, keys=keys)

    def __neg__(self):
        return type(self)(si=-self.si, keys=self.keys)

    # def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
    #     from .dimensionless import Dimensionless

    #     if ufunc == np.power:
    #         base, exp = inputs
    #         if isinstance(base, Quantity) and isinstance(exp, (int, float, np.ndarray)):
    #             return Quantity(si=np.power(base.si, exp), keys=base.keys)
    #         elif isinstance(exp, Quantity) and isinstance(
    #             base, (int, float, np.ndarray)
    #         ):
    #             return Quantity(si=np.power(base, exp.si), keys=exp.keys)
    #         elif isinstance(exp, Quantity) and isinstance(base, Quantity):
    #             keys = self.get_keys(exp, base)
    #             return Quantity(si=np.power(base.si, exp.si), keys=keys)
    #         else:
    #             raise TypeError("Invalid types for np.power with Quantity.")
    #     elif ufunc == np.add and method == "reduce":
    #         si = ufunc.reduce(inputs[0].si, **kwargs)
    #         return type(self)(si=si, keys=self.keys)
    #     elif ufunc == np.multiply and method == "reduce":
    #         si = ufunc.reduce(inputs[0].si, **kwargs)
    #         return Quantity(si=si, keys=self.keys)
    #     elif ufunc == np.exp:
    #         si = ufunc(inputs[0].si)
    #         if isinstance(inputs[0], Dimensionless):
    #             return Dimensionless(si=si, keys=self.keys)
    #         return Quantity(si=si, keys=self.keys)
    #     elif ufunc == np.log:
    #         si = ufunc(inputs[0].si)
    #         if isinstance(inputs[0], Dimensionless):
    #             return Dimensionless(si=si, keys=self.keys)
    #         return Quantity(si=si, keys=self.keys)
    #     return NotImplemented
