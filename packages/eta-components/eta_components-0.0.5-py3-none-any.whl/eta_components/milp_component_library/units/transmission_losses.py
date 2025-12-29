from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.systems import _BaseSystem
from eta_components.milp_component_library.units.base_unit import BaseAuxiliaryUnit, BaseUnit

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import _BaseNetwork


class TransmissionLoss(BaseAuxiliaryUnit):
    _has_investment_decision = False

    _param_names: ClassVar[list[str]] = [*BaseAuxiliaryUnit._param_names, "loss"]

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        network: _BaseNetwork,
    ):
        """

        :param name:
        :param data:
        :param system:
        :param network:
        """
        self._net: _BaseNetwork = network
        self._units: list[BaseUnit] = []
        self._powers: dict[BaseUnit, pyo.Param | pyo.Var | pyo.Expression] = {}
        self._net.register_loss(self)

        super().__init__(name, data, system)

        self._is_constructed: bool = False

    def _populate_model(self):
        self.model.loss = self._create_indexed_param(self.data["loss"])

        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.annual_cost = self._create_indexed_param(0, sets=self._system.years_set)
        self.model.onetime_cost = self._create_scalar_param(0)
        self.model.emissions = self._create_indexed_param(0)

    def _reinitialize_params(self):
        self._update_param(self.model.loss, self.data["loss"])

    def construct_model(self):
        from eta_components.milp_component_library.networks import PowerSign

        def rule_total_power(m, *idx):
            if self._units:
                return sum(power[idx] for power in self._powers.values())
            # No units are registered
            return 0

        self.model.total_power = pyo.Expression(*self._system.sets, rule=rule_total_power)

        def rule_transmission_loss(m, *idx):
            return -1 * m.total_power[idx] * m.loss[idx]

        self.model.transmission_loss = pyo.Expression(*self._system.sets, rule=rule_transmission_loss)

        self._net.register_unit(self, self.model.transmission_loss, PowerSign.UNDEFINED)

        self._is_constructed = True

    def deconstruct_model(self):
        self._is_constructed = False

        self.model.del_component("total_power")
        self.model.del_component("total_power_index")
        self.model.del_component("transmission_loss")
        self.model.del_component("transmission_loss_index")

        self._net.unregister_unit(self)

    def unregister(self):
        self._net.unregister_loss(self)
        try:
            self._net.unregister_unit(self)
        except ValueError:  # is not registered because loss model has not been constructed
            pass

    def add_unit(self, unit: BaseUnit, power: pyo.Param | pyo.Var | pyo.Expression):
        """Adds a unit which power is reduced due to network losses."""

        if unit in self._units:
            raise ValueError(
                f"Unit {unit.name} is already registered with this pump. Note that you can only add one "
                f"power per unit per loss. If you have multiple powers (e. g. storage inlet and outlet), "
                f"use multiple losses."
            )

        if unit not in self._net.units():
            raise ValueError(
                f"Unit {unit.name} is not registered in network {self._net.name}. Cannot add a "
                f"unit to a loss which is not registered with this network."
            )

        if power not in self._net.powers(unit):
            raise ValueError(
                f"Power {power.local_name} of unit {unit.name} is not registered in network {self._net.name}."
            )

        self._is_constructed = False

        self._units.append(unit)
        self._powers[unit] = power

    @property
    def transmission_loss(self) -> pyo.Expression:
        if not self._is_constructed:
            raise ValueError("Cannot access transmission_loss expression before calling construct_model(...).")
        return self._transmission_loss

    @property
    def _transmission_loss(self) -> pyo.Expression:
        # No check if transmission_loss can be accessed
        return self.model.transmission_loss

    @property
    def time_step_cost(self) -> pyo.Param:
        return self.model.time_step_cost

    @property
    def annual_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The annual cost of the unit indexed over the years."""
        return self.model.annual_cost

    @property
    def onetime_cost(self) -> pyo.Param:
        return self.model.onetime_cost

    @property
    def emissions(self) -> pyo.Param:
        return self.model.emissions
