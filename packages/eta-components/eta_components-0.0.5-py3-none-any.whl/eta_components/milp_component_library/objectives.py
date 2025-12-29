from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from pyomo import environ as pyo

from eta_components.milp_component_library.base_object import BaseObject

if TYPE_CHECKING:
    from eta_components.milp_component_library.systems import _BaseSystem


class _BaseObjective(BaseObject, ABC):
    """Abstract base class for system objectives."""

    _param_names: ClassVar[list] = []
    _optional_params: ClassVar[dict] = {"sense": "minimize"}

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Options for data:
        sense: "minimize" or "maximize", defaults to "minimize".
        """
        super().__init__(name, data, system)
        self._populate_model()

        self._is_constructed: bool = False

    def _populate_model(self):
        """Hook for subclasses to add params/vars/exprs to the objective model."""
        return

    @abstractmethod
    def _repopulate_model(self):
        pass

    @abstractmethod
    def construct_objective(self):
        """Construct the objective"""

    def _reinitialize_params(self):
        self._is_constructed = False
        self._repopulate_model()

    def deactivate(self):
        self.function.deactivate()

    @classmethod
    def _sense_str_to_sense_pyo(cls, sense: str) -> pyo.minimize | pyo.maximize:
        if sense == "minimize":
            sense = pyo.minimize
        elif sense == "maximize":
            sense = pyo.maximize
        else:
            raise ValueError(
                f"Unknown value for argument sense: {sense}. Valid arguments are 'minimize' or 'maximize'."
            )
        return sense

    @staticmethod
    def is_numeric_type():
        """Deprecated. Use pyo.value(objective.function) instead of pyo.value(objective).
        This is a method needed to enable using pyo.value(objective) to retrieve the objective value."""
        return True

    def is_expression_type(self):
        """Deprecated. Use pyo.value(objective.function) instead of pyo.value(objective).
        This is a method needed to enable using pyo.value(objective) to retrieve the objective value."""
        return self.is_numeric_type()

    @property
    def function(self) -> pyo.Objective:
        """The objective expression of the model."""
        if not self._is_constructed:
            raise ValueError("Cannot access objective expression before calling construct_objective(...).")
        return self.model.objective

    def __call__(self, **kwargs):
        return pyo.value(self.function)


class _SingleObjective(_BaseObjective, ABC):
    pass


class DummyObjective(_SingleObjective):
    """"""

    def _populate_model(self):
        pass

    def _repopulate_model(self):
        pass

    def construct_objective(self):
        pass

    @_BaseObjective.function.setter
    def function(self, function: pyo.Objective):
        self.model.objective = function
        self._is_constructed = True


class _WeightedObjective(_SingleObjective, ABC):
    _param_names: ClassVar[list] = [*_SingleObjective._param_names, "weights"]

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Options for data:
        sense: "minimize" or "maximize"
        weights: dict with (year, period) as keys and weights as values. Defaults to 1.
        """
        super().__init__(name, data, system)

    def _populate_model(self):
        super()._populate_model()
        self.model.weights = self._create_indexed_param(
            self.data["weights"], (self._system.years_set, self._system.periods_set)
        )

    def _repopulate_model(self):
        super()._repopulate_model()
        self._update_param(self.model.weights, self.data["weights"])

    @property
    def weights(self) -> pyo.Param:
        """Weights for the years and periods."""
        return self.model.weights


class StaticCost(_WeightedObjective):
    _optional_params: ClassVar[dict] = {
        **_BaseObjective._optional_params,
        "additional_opex": None,
        "additional_capex": None,
        "emission_cost": 0,
    }

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Options for data:
        sense: "minimize" or "maximize"
        weights: dict with (year, period) as keys and weights as values. Defaults to 1.
        additional_opex: pyo.Expression indexed over the years, periods and time steps that gets added to the
            opex. Defaults to None.
        additional_capex: scalar pyo.Expression that gets added to the capex. Defaults to None.
        emission_cost: scalar CO2-cost. Defaults to 0
        """
        super().__init__(name, data, system)

    def construct_objective(self):
        self._construct_annual_opex(additional_opex=self.data["additional_opex"])
        self._construct_capex(additional_capex=self.data["additional_capex"])

        def objective_rule(_):
            return self.model.capex + sum(self.model.opex[year] for year in self._system.years_set)

        self.model.del_component("objective")
        self.model.objective = pyo.Objective(
            rule=objective_rule, sense=self._sense_str_to_sense_pyo(self.data["sense"])
        )

        self._is_constructed = True

    def _construct_annual_opex(self, additional_opex):
        self.__construct_time_step_cost(additional_opex=additional_opex)
        self.__construct_annual_cost()

        def annual_opex(m, year: int):
            opex = sum(
                self.model.time_step_cost[year, period, time_step] * self.model.weights[year, period]
                for period, time_step in itertools.product(self._system.periods_set, self._system.time_set)
            )
            opex += self.model.annual_cost[year]
            return opex

        self.model.del_component("opex")
        self.model.del_component("opex_index")
        self.model.opex = pyo.Expression(self._system.years_set, rule=annual_opex)

    def __construct_time_step_cost(self, additional_opex):
        self.model.del_component("emission_cost")
        self.model.emission_cost = pyo.Param(initialize=self.data["emission_cost"])

        def rule_time_step_cost(m, *idx: int):
            time_step_cost = 0
            for unit in self._system.units:
                time_step_cost += unit.time_step_cost[idx]
                time_step_cost += unit.emissions[idx] * self.model.emission_cost
            if additional_opex is not None:
                time_step_cost += additional_opex[idx]
            time_step_cost *= self._system.step_length
            return time_step_cost

        self.model.del_component("time_step_cost")
        self.model.del_component("time_step_cost_index")
        self.model.time_step_cost = pyo.Expression(*self._system.sets, rule=rule_time_step_cost)

    def __construct_annual_cost(self):
        self.model.del_component("annual_cost")

        def rule_annual_cost(m, year: int):
            annual_cost = 0
            for unit in self._system.units:
                annual_cost += unit.annual_cost[year]
            return annual_cost

        self.model.del_component("annual_cost")
        self.model.del_component("annual_cost_index")
        self.model.annual_cost = pyo.Expression(self._system.years_set, rule=rule_annual_cost)

    def _construct_capex(self, additional_capex):
        def rule_capex(m):
            capex = 0
            for unit in self._system.units:
                capex += unit.onetime_cost
            if additional_capex is not None:
                capex += additional_capex
            return capex

        self.model.del_component("capex")
        self.model.capex = pyo.Expression(rule=rule_capex)

    @property
    def opex(self) -> pyo.Var:
        """The operational expenditures indexed over the years."""
        return self.model.opex

    @property
    def capex(self) -> pyo.Var:
        """The capital expenditures."""
        return self.model.capex


class NetPresentValue(StaticCost):
    _param_names: ClassVar[list[str]] = [*StaticCost._param_names, "interest"]

    def _populate_model(self):
        super()._populate_model()
        self.model.interest = self._create_indexed_param(self.data["interest"], (self._system.years_set,))

    def _repopulate_model(self):
        super()._repopulate_model()
        self._update_param(self.model.interest, self.data["interest"])

    def construct_objective(self):
        self._construct_annual_opex(additional_opex=self.data["additional_opex"])
        self._construct_capex(additional_capex=self.data["additional_capex"])

        def objective_rule(_):
            return self.model.capex + sum(
                self.model.opex[year] / ((1 + self.model.interest[year]) ** (year + self._system.year_length - 1))
                for year in self._system.years_set
            )

        self.model.del_component("objective")
        self.model.objective = pyo.Objective(
            rule=objective_rule, sense=self._sense_str_to_sense_pyo(self.data["sense"])
        )

        self._is_constructed = True


class Emissions(_WeightedObjective):
    def construct_objective(self):
        def rule_emissions(m, *idx: int):
            emissions = 0
            for unit in self._system.units:
                emissions += unit.emissions[idx]
            emissions *= self._system.step_length
            return emissions

        self.model.del_component("emissions")
        self.model.del_component("emissions_index")
        self.model.emissions = pyo.Expression(*self._system.sets, rule=rule_emissions)

        def objective_rule(_):
            return sum(
                self.model.emissions[year, period, time] * self.model.weights[year, period]
                for year, period, time in itertools.product(*self._system.sets)
            )

        self.model.del_component("objective")
        self.model.objective = pyo.Objective(
            rule=objective_rule, sense=self._sense_str_to_sense_pyo(self.data["sense"])
        )

        self._is_constructed = True

    @property
    def emissions(self) -> pyo.Var:
        """The total emissions indexed over the years, periods and time steps.

        Note: These emissions are already multiplied by the step_length, whereas the emissions of individual units are
            per step_length.
        """
        return self.model.emissions


class MultiObjective(_BaseObjective):
    _param_names: ClassVar[list] = [*_BaseObjective._param_names, "first_objective", "second_objective"]
    _optional_params: ClassVar[dict] = {**_BaseObjective._optional_params, "first_weight": 1.0, "second_weight": 1.0}
    _forbidden_updates: ClassVar[list] = [*_BaseObjective._forbidden_updates, "first_objective", "second_objective"]

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        super().__init__(name, data, system)

        self._first_objective: _SingleObjective = data["first_objective"]
        self._second_objective: _SingleObjective = data["second_objective"]

    def _populate_model(self):
        self.model.first_weight = self._create_scalar_param(self.data["first_weight"])
        self.model.second_weight = self._create_scalar_param(self.data["second_weight"])

    def _repopulate_model(self):
        self._update_param(self.model.first_weight, self.data["first_weight"])
        self._update_param(self.model.second_weight, self.data["second_weight"])

    def construct_objective(self):
        self._first_objective.construct_objective()
        self._second_objective.construct_objective()
        self._first_objective.function.deactivate()
        self._second_objective.function.deactivate()

        def objective_rule(m):
            return m.first_weight * self._first_objective.function + m.second_weight * self._second_objective.function

        self.model.del_component("objective")
        self.model.objective = pyo.Objective(
            rule=objective_rule, sense=self._sense_str_to_sense_pyo(self.data["sense"])
        )

        self._is_constructed = True
