import numpy as np
from typing import Any
from .. import utils
from .. import quantities as quant


class GasMixture:

    def __init__(
        self,
        components: dict[str, Any],
        y: quant.Fraction | None = None,
        p: quant.Pressure | None = None,
    ):
        self.components = components
        if y and not p:
            self.y = y
        elif p and not y:
            self.p = p
        else:
            raise ValueError("p or y can be specified, not both.")

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        from ..quantities import Fraction

        if not hasattr(self, "_y") or value.si != self._y.si:
            self._y = value
            active_comp_list = self.y.keys.copy()
            try:
                active_comp_list.remove("inert")
            except ValueError:
                pass
            # self.components = {
            #     comp_id: species.CLASS_MAP[comp_id] for comp_id in self.y.keys
            # }
            y_active = Fraction(
                si=[self.y[comp_id].si for comp_id in active_comp_list],
                keys=active_comp_list,
            )
            y_active_sum = np.sum(y_active.si)
            y_active_normalized = y_active / y_active_sum

            active_components = {
                comp_id: component
                for comp_id, component in self.components.items()
                if comp_id.lower() != "inert"
            }
            self.avg_mol_weight = np.sum(
                [
                    component.MOL_WEIGHT * y_active_normalized[comp_id].si
                    for comp_id, component in active_components.items()
                ]
            )

    @property
    def p(self):
        return self._p

    @p.setter
    def p(self, value):
        from ..quantities import Pressure

        if not hasattr(self, "_p") or value.si != self._p.si:
            self._p = value
            self.P = Pressure(si=np.sum([self._p.si]))
            self.y = utils.divide(self._p, self.P)
