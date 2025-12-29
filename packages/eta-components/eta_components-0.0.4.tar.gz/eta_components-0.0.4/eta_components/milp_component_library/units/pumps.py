from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.exceptions import InvalidParameterValueError, InvalidPwlfValuesError
from eta_components.milp_component_library.systems import _BaseSystem
from eta_components.milp_component_library.units.base_unit import BaseAuxiliaryUnit, BaseUnit

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import Electrical, _ThermalFluid


class _BasePump(BaseAuxiliaryUnit, ABC):
    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        thermal_network: _ThermalFluid,
        electrical_network: Electrical,
    ):
        """

        :param name:
        :param data:
        :param system:
        :param thermal_network:
        :param electrical_network:
        """
        self._thermal_net: _ThermalFluid = thermal_network
        self._electrical_net: Electrical = electrical_network
        self._units: list[BaseUnit] = []
        self._powers: dict[BaseUnit, pyo.Param | pyo.Var | pyo.Expression] = {}
        self._register_at_thermal_network()

        super().__init__(name, data, system)

        self._is_constructed: bool = False

    @abstractmethod
    def construct_model(self):
        pass

    @abstractmethod
    def deconstruct_model(self):
        pass

    def unregister(self):
        self._unregister_at_thermal_network()
        try:
            self._unregister_at_electrical_network()
        except ValueError:  # is not registered because pump model has not been constructed
            pass

    def _register_at_thermal_network(self):
        self._thermal_net.register_pump(self)

    def _unregister_at_thermal_network(self):
        self._thermal_net.unregister_pump(self)

    def _register_at_electrical_network(self):
        from eta_components.milp_component_library.networks import PowerSign

        self._electrical_net.register_unit(self, self._p_el_in, PowerSign.NEGATIVE)

    def _unregister_at_electrical_network(self):
        self._electrical_net.unregister_unit(self)

    def add_unit(self, unit: BaseUnit, power: pyo.Param | pyo.Var | pyo.Expression):
        """Adds a unit which thermal power is transported by this pump.

        Note that the hydraulic power of the pump
        must always be non-negative. This means that the total thermal power of all units must be non-negative in a
        heating network and non-positive in a cooling network. Thus, you should only add heating or cooling producers
        to this pump. If you add consumers, make sure that the thermal power of the producers is always equal or larger
        than the thermal power of the added consumers.
        """

        if unit in self._units:
            raise ValueError(
                f"Unit {unit.name} is already registered with this pump. Note that you can only add one "
                f"power per unit per pump. If you have multiple powers (e. g. storage inlet and outlet), "
                f"use multiple pumps."
            )

        if unit not in self._thermal_net.units():
            raise ValueError(
                f"Unit {unit.name} is not registered in network {self._thermal_net.name}. Cannot add a "
                f"unit to a pump which is not registered with this network."
            )

        if power not in self._thermal_net.powers(unit):
            raise ValueError(
                f"Power {power.local_name} of unit {unit.name} is not registered in network {self._thermal_net.name}."
            )

        self._is_constructed = False

        self._units.append(unit)
        self._powers[unit] = power

    @property
    def time_step_cost(self) -> pyo.Param:
        return self.model.time_step_cost

    @property
    def annual_cost(self) -> pyo.Param:
        return self.model.maintenance_cost

    @property
    def onetime_cost(self) -> pyo.Param | pyo.Var:
        return self.model.onetime_cost

    @property
    def emissions(self) -> pyo.Param:
        return self.model.emissions

    @property
    def p_el_in(self) -> pyo.Expression:
        if not self._is_constructed:
            raise ValueError("Cannot access p_el_in expression before calling construct_model(...).")
        return self._p_el_in

    @property
    def _p_el_in(self) -> pyo.Expression:
        # No check, if p_el_in can be accessed
        return self.model.p_el_in

    @property
    def volume_flow(self) -> pyo.Expression:
        if not self._is_constructed:
            raise ValueError("Cannot access volume_flow expression before calling construct_model(...).")
        return self.model.volume_flow


class PumpOperational(_BasePump):
    _has_investment_decision = True

    _param_names: ClassVar[list[str]] = [*_BasePump._param_names, "eta", "delta_pressure", "volume_flow_max"]
    _optional_params: ClassVar[dict[str, float]] = {**_BasePump._optional_params, "maintenance_cost": 0}

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        thermal_network: _ThermalFluid,
        electrical_network: Electrical,
    ):
        """

        :param name:
        :param data:
        :param system:
        :param thermal_network:
        :param electrical_network:
        """
        super().__init__(name, data, system, thermal_network=thermal_network, electrical_network=electrical_network)

    def _populate_model(self):
        self.model.eta = self._create_indexed_param(self.data["eta"])
        self.model.volume_flow_max = self._create_scalar_param(self.data["volume_flow_max"])
        self.model.delta_pressure = self._create_indexed_param(self.data["delta_pressure"])
        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.maintenance_cost = self._create_indexed_param(
            self._data["maintenance_cost"], sets=self._system.years_set
        )
        self.model.onetime_cost = self._create_scalar_param(0)
        self.model.emissions = self._create_indexed_param(0)

    def _reinitialize_params(self):
        self._update_param(self.model.eta, self.data["eta"])
        self._update_param(self.model.volume_flow_max, self.data["volume_flow_max"])
        self._update_param(self.model.delta_pressure, self.data["delta_pressure"])
        self._update_param(self.model.maintenance_cost, self.data["maintenance_cost"])

    def construct_model(self):
        def rule_thermal_power(m, *idx):
            if self._units:
                return sum(power[idx] for power in self._powers.values())
            # No units are registered
            return 0

        self.model.thermal_power = pyo.Expression(*self._system.sets, rule=rule_thermal_power)

        def rule_volume_flow(m, *idx):
            delta_temp = self._thermal_net.t_flow[idx] - self._thermal_net.t_return[idx]
            return m.thermal_power[idx] / (delta_temp * self._thermal_net.rho * self._thermal_net.cp)

        self.model.volume_flow = pyo.Expression(*self._system.sets, rule=rule_volume_flow)

        def rule_hydraulic_power(m, *idx):
            return m.volume_flow[idx] * m.delta_pressure[idx]

        self.model.hydraulic_power = pyo.Expression(*self._system.sets, rule=rule_hydraulic_power)

        def rule_electrical_power(m, *idx):
            return -1 * m.hydraulic_power[idx] * m.eta[idx]

        self.model.p_el_in = pyo.Expression(*self._system.sets, rule=rule_electrical_power)

        def rule_hydraulic_power_positive(m, *idx):
            return m.hydraulic_power[idx] >= 0

        self.model.hydraulic_power_positive = pyo.Constraint(*self._system.sets, rule=rule_hydraulic_power_positive)

        # volume_flow_max is already constrained to [0, volume_flow_nom_max] during initialization
        def rule_volume_flow_max(m, *idx):
            return m.volume_flow[idx] <= m.volume_flow_max

        self.model.limit_volume_flow = pyo.Constraint(*self._system.sets, rule=rule_volume_flow_max)

        # This cannot be done upon initialization, because p_el_in changes when units are added.
        self._register_at_electrical_network()

        self._is_constructed = True

    def deconstruct_model(self):
        self._is_constructed = False

        self.model.del_component("thermal_power")
        self.model.del_component("volume_flow")
        self.model.del_component("hydraulic_power")
        self.model.del_component("electrical_power")
        self.model.del_component("hydraulic_power_positive")
        self.model.del_component("limit_volume_flow")
        self._unregister_at_electrical_network()


class PumpInvestment(_BasePump):
    _has_investment_decision = True

    _param_names: ClassVar[list[str]] = [*_BasePump._param_names, "eta", "delta_pressure", "volume_flow_max"]
    _optional_params: ClassVar[dict[str, float]] = {
        **_BasePump._optional_params,
        "maintenance_cost": 0,
    }
    _forbidden_updates: ClassVar[list[str]] = [*_BasePump._forbidden_updates, "volume_flow_nom_support", "I_B", "K"]

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        thermal_network: _ThermalFluid,
        electrical_network: Electrical,
    ):
        """

        :param name:
        :param data:
        :param system:
        :param thermal_network:
        :param electrical_network:
        """

        super().__init__(name, data, system, thermal_network=thermal_network, electrical_network=electrical_network)

    def _populate_model(self):
        self.model.eta = self._create_indexed_param(self.data["eta"])
        self.model.delta_pressure = self._create_indexed_param(self.data["delta_pressure"])
        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.maintenance_factor = self._create_indexed_param(0, sets=self._system.years_set)
        self.model.emissions = self._create_indexed_param(0)

        self.model.y = pyo.Var(within=pyo.Binary)  # buying decision
        self.model.investment_cost = pyo.Var(within=pyo.NonNegativeReals)
        self.model.volume_flow_nom_max = self._create_scalar_param(self._data["volume_flow_nom_support"][-1])
        self.model.volume_flow_max = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, self.model.volume_flow_nom_max))

        def rule_capital_cost():
            capital_cost_support_points = []
            for volume_flow_support_i in self._data["volume_flow_nom_support"]:
                capital_cost_i = self._data["I_B"] * (volume_flow_support_i ** self._data["K"])
                capital_cost_support_points.append(capital_cost_i)
            return pyo.Piecewise(
                self.model.investment_cost,
                self.model.volume_flow_max,
                pw_pts=self._data["volume_flow_nom_support"],
                f_rule=capital_cost_support_points,
                pw_constr_type="EQ",
            )

        self._check_investment_support_points(self._data["volume_flow_nom_support"])
        self.model.investment_curve = rule_capital_cost()

    @staticmethod
    def _check_investment_support_points(support_pts: Sequence):
        if support_pts[0] != 0:
            raise InvalidParameterValueError(
                f"The first support point for the nominal volume flow must be 0, was {support_pts[0]}"
            )
        if len(support_pts) < 2:
            raise InvalidParameterValueError(
                f"The number of support points for the investment curve must be at least two."
                f"{len(support_pts)} points were passed."
            )
        if not all(val_n < val_n_plus_1 for val_n, val_n_plus_1 in zip(support_pts, support_pts[1:])):
            raise InvalidPwlfValuesError(
                f"The sequence of support points for the investment curve must be strictly"
                f"increasing. Was {support_pts}."
            )

    def _reinitialize_params(self):
        self._update_param(self.model.eta, self.data["eta"])
        self._update_param(self.model.delta_pressure, self.data["delta_pressure"])
        self._update_param(self.model.maintenance_cost, self._data["maintenance_factor"])

    def construct_model(self):
        def rule_thermal_power(m, *idx):
            if self._units:
                return sum(power[idx] for power in self._powers.values())
            # No units are registered
            return 0

        self.model.thermal_power = pyo.Expression(*self._system.sets, rule=rule_thermal_power)

        def rule_volume_flow(m, *idx):
            delta_temp = self._thermal_net.t_flow[idx] - self._thermal_net.t_return[idx]
            return m.thermal_power[idx] / (delta_temp * self._thermal_net.rho * self._thermal_net.cp)

        self.model.volume_flow = pyo.Expression(*self._system.sets, rule=rule_volume_flow)

        def rule_hydraulic_power(m, *idx):
            return m.volume_flow[idx] * m.delta_pressure[idx]

        self.model.hydraulic_power = pyo.Expression(*self._system.sets, rule=rule_hydraulic_power)

        def rule_electrical_power(m, *idx):
            return -1 * m.hydraulic_power[idx] * m.eta[idx]

        self.model.p_el_in = pyo.Expression(*self._system.sets, rule=rule_electrical_power)

        def rule_maintenance_cost(m, year):
            return m.maintenance_factor[year] * m.investment_cost

        self.model.maintenance_cost = pyo.Expression(self._system.years_set, rule=rule_maintenance_cost)

        def rule_hydraulic_power_positive(m, *idx):
            return m.hydraulic_power[idx] >= 0

        self.model.hydraulic_power_positive = pyo.Constraint(*self._system.sets, rule=rule_hydraulic_power_positive)

        # volume_flow_max is already constrained to [0, volume_flow_nom_max] during initialization
        def rule_volume_flow_max(m, *idx):
            return m.volume_flow[idx] <= m.volume_flow_max

        self.model.limit_volume_flow = pyo.Constraint(*self._system.sets, rule=rule_volume_flow_max)

        def rule_buying_decision(m):
            return m.volume_flow_max <= m.y * m.volume_flow_nom_max

        self.model.buying_decision = pyo.Constraint(rule=rule_buying_decision)

        # This cannot be done upon initialization, because p_el_in changes when units are added.
        self._register_at_electrical_network()

        self._is_constructed = True

    def deconstruct_model(self):
        self._is_constructed = False

        self.model.del_component("thermal_power")
        self.model.del_component("volume_flow")
        self.model.del_component("hydraulic_power")
        self.model.del_component("electrical_power")
        self.model.del_component("hydraulic_power_positive")
        self.model.del_component("limit_volume_flow")
        self._unregister_at_electrical_network()

    @property
    def volume_flow_max(self) -> pyo.Expression:
        if not self._is_constructed:
            raise ValueError("Cannot access volume_flow_max expression before calling construct_model(...).")
        return self.model.volume_flow_max

    @property
    def is_bought(self) -> pyo.Var:
        return self.model.y

    @property
    def onetime_cost(self) -> pyo.Var:
        return self.model.investment_cost


class PumpPipeInvestment(PumpInvestment):
    _has_investment_decision = True

    _param_names: ClassVar[list[str]] = [
        *PumpInvestment._param_names,
        "price_per_m",
        "price_per_m3",
        "velocity_max",
        "length",
    ]

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        thermal_network: _ThermalFluid,
        electrical_network: Electrical,
    ):
        """

        :param name:
        :param data:
        :param system:
        :param thermal_network:
        :param electrical_network:
        """
        super().__init__(name, data, system, thermal_network=thermal_network, electrical_network=electrical_network)

    def _populate_model(self):
        self.model.capital_cost = pyo.Var(within=pyo.NonNegativeReals)

        self.model.eta = self._create_indexed_param(self.data["eta"])
        self.model.delta_pressure = self._create_indexed_param(self.data["delta_pressure"])
        self.model.maintenance_factor = self._create_indexed_param(0, sets=self._system.years_set)

        self.model.pipe = pyo.Block()
        self.model.pipe.price_per_m = self._create_scalar_param(self.data["price_per_m"])
        self.model.pipe.price_per_m3 = self._create_scalar_param(self.data["price_per_m3"])
        self.model.pipe.velocity_max = self._create_scalar_param(self.data["velocity_max"])
        self.model.pipe.length = self._create_scalar_param(self.data["length"])
        self.model.pipe.area = pyo.Var(within=pyo.NonNegativeReals)

        self.model.operating_cost = self._create_indexed_param(0)
        self.model.emissions = self._create_indexed_param(0)

        self.model.pump = pyo.Block()
        self.model.y = pyo.Var(within=pyo.Binary)  # buying decision
        self.model.pump.investment_cost = pyo.Var(within=pyo.NonNegativeReals)
        self.model.volume_flow_nom_max = self._create_scalar_param(self._data["volume_flow_nom_support"][-1])
        self.model.volume_flow_max = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, self.model.volume_flow_nom_max))

        def rule_capital_cost_pipe(m):
            return m.price_per_m * m.length + m.price_per_m3 * m.length * m.area

        self.model.pipe.investment_cost = pyo.Expression(rule=rule_capital_cost_pipe)

        def rule_capital_cost_pump():
            capital_cost_support_points = []
            for volume_flow_support_i in self._data["volume_flow_nom_support"]:
                capital_cost_i = self._data["I_B"] * (volume_flow_support_i ** self._data["K"])
                capital_cost_support_points.append(capital_cost_i)
            return pyo.Piecewise(
                self.model.pump.investment_cost,
                self.model.volume_flow_max,
                pw_pts=self._data["volume_flow_nom_support"],
                f_rule=capital_cost_support_points,
                pw_constr_type="EQ",
            )

        self._check_investment_support_points(self._data["volume_flow_nom_support"])
        self.model.investment_curve_pump = rule_capital_cost_pump()
        self.model.investment_cost = pyo.Expression(
            expr=self.model.pipe.investment_cost + self.model.pump.investment_cost
        )

        def rule_maintenance_cost(m, year):
            return m.maintenance_factor[year] * m.investment_cost

        self.model.maintenance_cost = pyo.Expression(self._system.years_set, rule=rule_maintenance_cost)

        def rule_limit_volume_flow_max_with_pipe_area(m):
            return m.volume_flow_max <= m.pipe.area * m.pipe.velocity_max

        self.model.limit_volume_flow_max_with_pipe_area = pyo.Constraint(rule=rule_limit_volume_flow_max_with_pipe_area)

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.pipe.price_per_m, self.data["price_per_m"])
        self._update_param(self.model.pipe.price_per_m3, self.data["price_per_m3"])
        self._update_param(self.model.pipe.velocity_max, self.data["velocity_max"])
        self._update_param(self.model.pipe.length, self.data["length"])

    @property
    def pipe_area(self) -> pyo.Var:
        return self.model.pipe.area
