from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from pyomo import environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.base_unit import BaseStandaloneUnit

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import _BaseNetwork
    from eta_components.milp_component_library.systems import _BaseSystem


class _BaseTrader(BaseStandaloneUnit, ABC):
    """Traders represent units in the energy supply system which transfer energy across the supply system's
    boundaries and generate profits/cost and emissions when doing so.
    """

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method.

        Extends the base method by registering the equipment at the system and connecting the trader to a network.
        """
        self._net: _BaseNetwork = network
        super().__init__(name, data, system)

    @property
    @abstractmethod
    def amount(self) -> pyo.Var:
        """The amount transferred."""


class _SimpleTrader(_BaseTrader, ABC):
    """Simple trader with indexed costs and specific emissions.

    Defines a unit for the operating cost:
        operating_cost = sum_t(unit_price_t * amount_t)

    Additionally calculated the occurred emissions:
        emissions = sum_t(emissions_per_unit_t * amount_t)
    """

    _param_names: ClassVar[list[str]] = [
        "unit_price",
    ]
    _optional_params: ClassVar[dict[str, float]] = {
        "emissions_per_unit": 0,
        "capacity_price": 0,
    }

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method.

        Extends the base method by allowing more properties to be passed in the data argument.

        The additional valid keys for the data argument are the following:
        - unit_price: The specific price per transferred unit. Scalar or indexed.
        - emissions_per_unit: The specific emissions per transferred unit. Scalar or indexed. Defaults to 0.
        """
        super().__init__(name, data, system, network=network)

    def _init_params(self):
        self.model.unit_price = self._create_indexed_param(self._data["unit_price"])
        self.model.capacity_price = self._create_scalar_param(self._data["capacity_price"])
        self.model.emissions_per_unit = self._create_indexed_param(self._data["emissions_per_unit"])
        self.model.onetime_cost = self._create_scalar_param(0)

    def _reinitialize_params(self):
        self._update_param(self.model.unit_price, self._data["unit_price"])
        self._update_param(self.model.emissions_per_unit, self._data["emissions_per_unit"])

    def _init_variables(self):
        super()._init_variables()

    def _init_expressions(self):
        def emissions(m, *idx: int):
            return m.amount[idx] * m.emissions_per_unit[idx]

        self.model.emissions = pyo.Expression(*self._system.sets, rule=emissions)

        def time_step_cost(m, *idx: int):
            return m.amount[idx] * m.unit_price[idx]

        self.model.time_step_cost = pyo.Expression(*self._system.sets, rule=time_step_cost)

    def _init_constraints(self):
        super()._init_constraints()

    def _unregister_at_networks(self):
        self._net.unregister_unit(self)

    @property
    def amount(self) -> pyo.Expression:
        return self.model.amount

    @property
    def time_step_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The operating cost of the unit per step length indexed over the years, periods and time steps."""
        return self.model.time_step_cost

    @property
    def annual_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The annual cost of the unit indexed over the years."""
        return self.model.annual_cost

    @property
    def onetime_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The capital cost of the unit."""
        return self.model.onetime_cost

    @property
    def emissions(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The emissions of the unit per step length indexed over the years, periods and time steps."""
        return self.model.emissions


class SimpleBuyer(_SimpleTrader):
    """Simple buyer with indexed costs and specific emissions. Transfers capacity out of the network, so its amount is
    negative.
    """

    def _register_at_networks(self):
        self._net.register_unit(self, self.model.amount, PowerSign.NEGATIVE)

    def _init_params(self):
        super()._init_params()
        self.model.annual_cost = self._create_indexed_param(0, sets=self._system.years_set)

    def _reinitialize_params(self):
        super()._reinitialize_params()

    def _init_variables(self):
        super()._init_variables()
        self.model.amount = pyo.Var(*self._system.sets, within=pyo.NonPositiveReals)


class CapacityCostBuyer(SimpleBuyer):
    """Buyer with operational cost, emissions and capacity cost. Transfers capacity out of the network, so its amount is
    negative.
    """

    _big_m = 1e9

    def _register_at_networks(self):
        self._net.register_unit(self, self.model.amount, PowerSign.NEGATIVE)

    def _init_params(self):
        super()._init_params()
        self.model.del_component("annual_cost")

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self.model.del_component("annual_cost")

    def _init_variables(self):
        super()._init_variables()
        self.model.amount_min = pyo.Var(self._system.years_set, within=pyo.NonPositiveReals)
        self.model.is_max = pyo.Var(*self._system.sets, within=pyo.Binary)

    def _init_constraints(self):
        def minimize_amount_min(m, *idx: int):
            return m.amount_min[idx[0]] <= m.amount[idx]

        self.model.minimize_amount_min = pyo.Constraint(*self._system.sets, rule=minimize_amount_min)

        def maximize_minimum_of_amount_min(m, *idx: int):
            return m.amount_min[idx[0]] >= m.amount[idx] - self._big_m * (1 - m.is_max[idx])

        self.model.maximize_minimum_of_amount_min = pyo.Constraint(
            *self._system.sets, rule=maximize_minimum_of_amount_min
        )

        def only_one_amount_max_per_year(m, year: int):
            return (
                sum(
                    self.model.is_max[year, period, time_step]
                    for period, time_step in itertools.product(self._system.periods_set, self._system.time_set)
                )
                == 1
            )

        self.model.only_one_amount_max = pyo.Constraint(self._system.years_set, rule=only_one_amount_max_per_year)

    def _init_expressions(self):
        super()._init_expressions()

        def annual_cost(m, year):
            return m.amount_min[year] * m.capacity_price

        self.model.annual_cost = pyo.Expression(self._system.years_set, rule=annual_cost)


class SecuredDeliveryBuyer(SimpleBuyer):
    def _register_at_networks(self):
        self._net.register_unit(self, self.model.amount, PowerSign.NEGATIVE)

    def _init_params(self):
        super()._init_params()
        self.model.del_component("annual_cost")

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self.model.del_component("annual_cost")

    def _init_variables(self):
        super()._init_variables()
        self.model.amount_max = pyo.Var(self._system.years_set, within=pyo.NonPositiveReals)

    def _init_constraints(self):
        def minimize_amount_max(m, *idx: int):
            return m.amount_max[idx[0]] >= m.amount[idx]

        self.model.minimize_maximum_amount = pyo.Constraint(*self._system.sets, rule=minimize_amount_max)

    def _init_expressions(self):
        super()._init_expressions()

        def annual_cost(m, year):
            return m.amount_max[year] * m.capacity_price

        self.model.annual_cost = pyo.Expression(self._system.years_set, rule=annual_cost)


class SimpleSeller(_SimpleTrader):
    """Simple seller with indexed costs and specific emissions. Transfers capacity into the network, so its amount is
    positive.

    Defines an additional capacity price for the capital costs:
        capital_cost = capacity_price * max_t (amount_t)
    """

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Extends the base method by allowing more properties to be passed in the data argument.

        The additional valid keys for the data argument are the following:
        - capacity_price: The price per maximum power transferred (e.g. grid connection fee). Defaults to 0.
        """
        super().__init__(name, data, system, network=network)

    def _register_at_networks(self):
        self._net.register_unit(self, self.model.amount, PowerSign.POSITIVE)

    def _init_variables(self):
        super()._init_variables()
        self.model.amount = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)
        self.model.amount_max = pyo.Var(self._system.years_set, within=pyo.NonNegativeReals)

    def _init_expressions(self):
        super()._init_expressions()

        def annual_cost(m, year):
            return m.amount_max[year] * m.capacity_price

        self.model.annual_cost = pyo.Expression(self._system.years_set, rule=annual_cost)

    def _init_constraints(self):
        super()._init_constraints()

        def rule_amount_max(m, *idx: int):
            return m.amount_max[idx[0]] >= m.amount[idx]

        self.model.rule_abs_amount_max = pyo.Constraint(*self._system.sets, rule=rule_amount_max)

    @property
    def onetime_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The capital cost of the unit."""
        return self.model.onetime_cost
