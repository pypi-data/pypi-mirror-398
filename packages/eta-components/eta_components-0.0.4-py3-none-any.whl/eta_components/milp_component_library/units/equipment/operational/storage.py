from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.equipment.base_equipment import (
    BaseBattery,
    BaseColdStorage,
    BaseHeatStorage,
    BaseHydrogenStorage,
    BaseStorage,
)

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import _BaseNetwork
    from eta_components.milp_component_library.systems import _BaseSystem


class BaseOperationalStorage(BaseStorage, ABC):
    """Converter model for a storage.

    The model is the following:
        Parameters:
            E_nom   Capacity of the storage,
            c_in_max    Relative charge rate limit,
            c_out_max   Relative discharge rate limit
            loss    Constant loss to the environment
            eta[]   Charge and discharge loss
            delta_t Time step length
            bigM    Large value
        Variables:
            y   Binary, buying decision,
            x[] Binary, discharge decision, 0 if charging
            E[]   NonNegativeReal, energy content,
            pfr[]   [0, 1], relative charge rate,
            plr[]   [0, 1], relative discharge rate,
        Expressions:
            P_out[] = plr[] * E_nom * c_out_max
            P_in[] = - pfr[] * E_nom * c_in_max
        Constraints:
            0 <= E[] <= E_max
            P_in[] <= -1 * (1 - x[]) * bigM
            P_out[] <= x[] * bigM
            E[t] = E[t-1] * (1 - loss*delta_t) + eta[t] * P_in[t] - 1/eta[t] * P_out[t]
    """

    _param_names: ClassVar[list[str]] = [
        "E_nom",
        "eta",
        "c_in_max",
        "c_out_max",
        "loss",
    ]
    _optional_params: ClassVar[dict[str, object]] = {
        **BaseStorage._optional_params,
        **{
            "pfr_plr_bpts": ((0, 0), (1, 1)),
            "maintenance_cost": 0,
        },
    }

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method.

        Extends the base method by allowing more properties to be passed in the data argument and requiring a network
        which the storage is connected to.

        Replaces the allowed parameter names of the base class with the following.
        - E_nom: the maximum/nominal energy capacity.
        - eta: The charge and discharge loss. Defaults to 1.
        - c_in_max: The maximum specific charge rate in reference to the maximum energy capacity. Scalar.
            Defaults to 1, enabling a complete charge or discharge in 1 time_step.
        - c_out_max: The maximum specific discharge rate in reference to the maximum energy capacity.
            Scalar. Defaults to 1.
        - loss: The specific energy loss to the environment over time in relation to the maximum energy capacity.
            Scalar. Defaults to 0.
        """
        super().__init__(name, data, system, network=network)
        if self._sign == PowerSign.POSITIVE and data["E_nom"] < 0:
            raise ValueError(
                f"The nominal capacity E_nom for unit {self.name} must be non-negative. It was {data['E_nom']}."
            )
        if self._sign == PowerSign.NEGATIVE and data["E_nom"] > 0:
            raise ValueError(
                f"The nominal capacity E_nom for unit {self.name} must be non-positive. It was {data['E_nom']}."
            )

    def _init_params(self):
        super()._init_params()
        self.model.p_out_nom = self._create_scalar_param(self._data["E_nom"])
        self.model.maintenance_cost = self._create_indexed_param(
            self._data["maintenance_cost"], sets=self._system.years_set
        )
        self.model.onetime_cost = self._create_scalar_param(0)

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.p_out_nom, self._data["E_nom"])
        self.model.maintenance_cost = self._create_indexed_param(
            self._data["maintenance_cost"], sets=self._system.years_set
        )
        if self._sign == PowerSign.POSITIVE:
            self.model.e.bounds = (0, self.model.e_nom)
        elif self._sign == PowerSign.NEGATIVE:
            self.model.e.bounds = (self.model.e_nom, 0)

    def _init_variables(self):
        """Initializes the variables. Extends the base method by introducing an energy capacity variable and setting
        the bounds for pfr and plr to [0, 1].
        """
        if not self._data["allow_simultaneous_charging_and_discharging"]:
            self.model.x = pyo.Var(*self._system.sets, within=pyo.Binary)
        self.model.plr = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals, bounds=(0, 1))
        self.model.pfr = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals, bounds=(0, 1))
        if self._sign == PowerSign.POSITIVE:
            self.model.e = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals, bounds=(0, self.model.p_out_nom))
        elif self._sign == PowerSign.NEGATIVE:
            self.model.e = pyo.Var(*self._system.sets, within=pyo.NonPositiveReals, bounds=(self.model.p_out_nom, 0))

    def _init_expressions(self):
        def rule_p_in(m, *idx: int):
            return -1 * m.p_out_nom * m.c_in_max * m.pfr[idx]

        self.model.p_in = pyo.Expression(*self._system.sets, rule=rule_p_in)

        def rule_p_out(m, *idx: int):
            return m.p_out_nom * m.c_out_max * m.plr[idx]

        self.model.p_out = pyo.Expression(*self._system.sets, rule=rule_p_out)

    def _init_constraints(self):
        self.model.energy_balance = pyo.Constraint(*self._system.sets, rule=self._energy_balance())

        if not self._data["allow_simultaneous_charging_and_discharging"]:

            def supply_xor_demand_1(m, *idx: int):
                if self._sign == PowerSign.POSITIVE:
                    return m.p_out[idx] <= m.p_out_nom * m.c_out_max * m.x[idx]
                if self._sign == PowerSign.NEGATIVE:
                    return m.p_out[idx] >= m.p_out_nom * m.c_out_max * m.x[idx]
                raise ValueError(f"Unexpected PowerSign: {self._sign}")

            self.model.supply_xor_demand_1 = pyo.Constraint(*self._system.sets, rule=supply_xor_demand_1)

            def supply_xor_demand_2(m, *idx: int):
                if self._sign == PowerSign.POSITIVE:
                    return -1 * m.p_in[idx] <= m.p_out_nom * m.c_in_max * (1 - m.x[idx])
                if self._sign == PowerSign.NEGATIVE:
                    return -1 * m.p_in[idx] >= m.p_out_nom * m.c_in_max * (1 - m.x[idx])
                raise ValueError(f"Unexpected PowerSign: {self._sign}")

            self.model.supply_xor_demand_2 = pyo.Constraint(*self._system.sets, rule=supply_xor_demand_2)

    @property
    def time_step_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The operating cost of the unit per step length indexed over the years, periods and time steps."""
        return self.model.time_step_cost

    @property
    def annual_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The annual cost of the unit indexed over the years."""
        return self.model.maintenance_cost

    @property
    def onetime_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The capital cost of the unit."""
        return self.model.onetime_cost

    @property
    def emissions(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The emissions of the unit per step length indexed over the years, periods and time steps."""
        return self.model.emissions


class Battery(BaseBattery, BaseOperationalStorage):
    """Converter model for a battery. Refer to the base class for implementation details."""


class HeatStorage(BaseHeatStorage, BaseOperationalStorage):
    """Converter model for a thermal heat storage. Refer to the base class for implementation details."""


class ColdStorage(BaseColdStorage, BaseOperationalStorage):
    """Converter model for a thermal cold storage. Refer to the base class for implementation details."""


class HydrogenStorage(BaseHydrogenStorage, BaseOperationalStorage):
    """Converter model for a gas storage. Refere to the base class for implementation details."""
