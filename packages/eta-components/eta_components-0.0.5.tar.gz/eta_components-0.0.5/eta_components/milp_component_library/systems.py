from __future__ import annotations

import itertools
import logging
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import pyomo.environ as pyo
from pyomo.core.base.set import FiniteScalarRangeSet

from eta_components.milp_component_library.exceptions import InfeasibleProblemError, UnboundedProblemError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from eta_components.milp_component_library.environments import _BaseEnvironment
    from eta_components.milp_component_library.networks import _BaseNetwork
    from eta_components.milp_component_library.objectives import _BaseObjective
    from eta_components.milp_component_library.units.base_unit import BaseUnit


class _BaseSystem:
    """A system that connects all model instances and provides the Pyomo-sets for these model instances.

    Each created model (equipment, network, trader, environment, ...) can register at the system and access its
    Pyomo sets. After each individual model has been created and registered, the system can then connect all these
    models to a single main model, which can then be solved. Each individual model must be registered at the system,
    otherwise the Pyomo model cannot be solved.

    """

    def __init__(self, n_years: int, n_periods: int, n_time_steps: int, step_length: float = 1, year_length: int = 1):
        """Constructor method.

        :param n_years: The cardinality of the set for the years, int.
        :param n_periods: The cardinality of the set for the typical periods per year, int.
        :param n_time_steps: The cardinality of the set for the time steps per typical period, int.
        :param step_length: The time difference between time steps in seconds. Int | float, defaults to 1 second.
        :param year_length: The number of years each data point is valid for. E. g. if the data for one period spans
            two years, year_length should be 2. In this case, the index for year is (1, 3, 5, ...). Defaults to 1 year.
        """
        from eta_components.milp_component_library.objectives import DummyObjective

        self._n_years: int = n_years
        self._n_periods: int = n_periods
        self._n_time_steps: int = n_time_steps
        self._step_length: int = step_length
        self._year_length: int = year_length
        self._model: pyo.ConcreteModel = self._create_model()

        self._units: list[BaseUnit] = []
        self._networks: list[_BaseNetwork] = []
        self._environments: list[_BaseEnvironment] = []

        self._objective: _BaseObjective = DummyObjective("placeholder_objective", {}, self)  # composition

        self._is_joined: bool = False
        self._is_objective_set: bool = False

    def _create_model(self) -> pyo.ConcreteModel:
        model = pyo.ConcreteModel()

        model.step_length = pyo.Param(initialize=self._step_length)  # The difference between two time steps in seconds
        model.year_length = pyo.Param(initialize=self._year_length)
        end_year = self._n_years * pyo.value(model.year_length)

        model.years_set = FiniteScalarRangeSet(1, end_year, model.year_length)  # The index for the years
        model.periods_set = FiniteScalarRangeSet(self._n_periods)  # The index for the typical periods
        model.time_set = FiniteScalarRangeSet(self._n_time_steps)  # The index for the time step

        model.units = pyo.Block()
        model.networks = pyo.Block()
        model.environments = pyo.Block()
        return model

    def register_unit(self, unit: BaseUnit):
        """Register a unit with the system."""
        self._check_if_already_registered(unit, self._units)
        self._detach_models_if_joined()
        self._units.append(unit)

    @staticmethod
    def _check_if_already_registered(
        component: BaseUnit | _BaseNetwork | _BaseEnvironment,
        registered_components: list[BaseUnit | _BaseNetwork | _BaseEnvironment],
    ):
        if (
            next(
                (
                    component
                    for registered_component in registered_components
                    if component.name == registered_component.name
                ),
                None,
            )
            is not None
        ):
            raise ValueError(f"A component with the name {component.name} has already been registered.")

    def _detach_models_if_joined(self):
        if self._is_joined:
            self._detach_models()

    def unregister_unit(self, unit: BaseUnit):
        """Unregisters the unit. Throws an error if the unit is not registered."""
        self._detach_models_if_joined()
        self._units.remove(unit)

    def get_unit(self, name: str):
        """Returns the unit of the given name. Throws an error if the unit is not registered."""
        return self._get_component(name, self._units)

    @staticmethod
    def _get_component(name: str, registered_components: list[BaseUnit | _BaseNetwork | _BaseEnvironment]):
        try:
            return next(component for component in registered_components if component.name == name)
        except StopIteration as err:
            raise ValueError(f"No component with the name {name} found.") from err

    def register_network(self, network: _BaseNetwork):
        """Register a network with the system."""
        self._check_if_already_registered(network, self._networks)
        self._detach_models_if_joined()
        self._networks.append(network)

    def get_network(self, name: str):
        """Returns the network of the given name. Throws an error if the network is not registered."""
        return self._get_component(name, self._networks)

    def register_environment(self, environment: _BaseEnvironment):
        """Register an environment with the system."""
        self._check_if_already_registered(environment, self._environments)
        self._detach_models_if_joined()
        self._environments.append(environment)

    def get_environment(self, name: str):
        """Returns the environment of the given name. Throws an error if the environment is not registered."""
        return self._get_component(name, self._environments)

    def join_models(self):
        """Joins all models of registered objects into a single Pyomo model.

        This method is called automatically when calling System.solve(...).

        In order to solve a pyomo model, all variables, constraints, parameters etc. need to be attributes of that
        model. In this library each object (unit, network, etc.) has its own model, describing its internal behavior
        and exposing the necessary interface for other objects. This method collects all these models and adds them
        to the global model of the system. If this method was called previously, all models are removed from the global
        model beforehand.
        """
        self._detach_models_if_joined()

        for unit in self._units:
            self._model.units.add_component(unit.name, unit.model)
        for network in self._networks:
            network.build_constraints()
            self._model.networks.add_component(network.name, network.model)
        for environment in self._environments:
            self._model.environments.add_component(environment.name, environment.model)

        self._is_joined = True

    def _detach_models(self):
        self._is_joined = False

        for unit in self._units:
            self.model.units.del_component(unit.name)
        for network in self._networks:
            network.remove_constraints()
            self.model.networks.del_component(network.name)
        for environment in self._environments:
            self.model.environments.del_component(environment.name)

    def set_objective(
        self,
        objective: str | pyo.Var | pyo.Expression | _BaseObjective,
        weights: dict[tuple[int, int], int | float] | None = None,
        sense: str = "minimize",
        **kwargs,
    ):
        """Add the objective to the system.

        This sets the objective as the new active objective of the system. Previous objectives will be overwritten.
        """

        from eta_components.milp_component_library.objectives import DummyObjective, StaticCost, _BaseObjective

        if isinstance(objective, _BaseObjective):
            self._objective = objective

        else:
            warnings.warn(
                "Specifying the objective with a string or supplying a pyomo expression is deprecated. "
                "Use objectives.StaticCost instead of supplying 'cost' or obj = objectives.DummyObjective and then "
                "set your custom objective with obj.function = custom_objective. Afterwards call "
                "system.set_objective(obj).",
                DeprecationWarning,
                stacklevel=2,
            )
            if isinstance(objective, pyo.Var | pyo.Expression):
                self.model.weights = None
                self._objective = DummyObjective("custom_objective", {}, self)
                self._objective.model.objective = pyo.Objective(
                    expr=objective, sense=_BaseObjective._sense_str_to_sense_pyo(sense)
                )
            elif objective == "cost":
                if weights is None:
                    weights = {
                        (year, period): 1 for year, period in itertools.product(self.years_set, self.periods_set)
                    }
                self.model.weights = weights
                self._objective = StaticCost("cost_objective", {"sense": sense, "weights": weights, **kwargs}, self)
            else:
                raise ValueError(f"Unknown objective type specified: {objective} of type {type(objective)}.")

        self.model.del_component("objective")
        self.model.objective = self.objective.model

        self._is_objective_set = True

    def solve(self, solver: str = "gurobi", tee: bool = False, options: dict | None = None, model_export: bool = False):
        """Solve the model.

        Solves the global Pyomo model of the system. This method calls .join_models() and
        .objective.construct_objective() automatically before solving.

        :param solver: The solver to be used. Str, defaults to "cplex".
        :param tee: Flag for verbose solver output. Bool, defaults to False.
        :param options:
        """
        self.join_models()

        if model_export:
            scenario_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            export_dir = Path.cwd()
            lp_file = export_dir / f"{scenario_id}.lp"
            txt_file = export_dir / f"{scenario_id}_pprint.txt"

            self.model.write(lp_file, format="lp", io_options={"symbolic_solver_labels": True})
            with Path.open(txt_file, "w") as f:
                self.model.pprint(ostream=f)

        self.objective.construct_objective()

        self._check_ready_to_be_solved()
        if options is None:
            options = {}
        keepfiles = options.pop("keepfiles", False)
        warmstart = options.pop("warmstart", False)

        solver = pyo.SolverFactory(solver)
        if options:
            solver.options = options
        res = solver.solve(self.model, tee=tee, keepfiles=keepfiles, warmstart=warmstart)
        if tee:
            logger.info(
                "Solver status: %s\tTermination condition: \\%s", res.solver.status, res.solver.termination_condition
            )
        if res.solver.termination_condition == "infeasible":
            raise InfeasibleProblemError(f"Optimization problem with name {self.model.name} has no feasible solution.")
        if res.solver.termination_condition == "unbounded":
            raise UnboundedProblemError(f"Optimization problem with name {self.model.name} is unbounded.")
        self.last_results = res
        return res

    def _check_ready_to_be_solved(self):
        if not self._is_joined:
            raise RuntimeError(
                "All models of the system must be joined before setting the objective and solving. "
                "Call .join_models() after having created all your components."
            )
        if not self._is_objective_set:
            raise RuntimeError("No objective has been set for the system. Call .set_objective(...) first.")

    @property
    def sets(self) -> tuple[FiniteScalarRangeSet, FiniteScalarRangeSet, FiniteScalarRangeSet]:
        """A tuple containing all indices in order of increasing resolution."""
        return self.years_set, self.periods_set, self.time_set

    @property
    def years_set(self) -> FiniteScalarRangeSet:
        """The set of the years."""
        return self.model.years_set

    @property
    def periods_set(self) -> FiniteScalarRangeSet:
        """The set of the typical periods."""
        return self.model.periods_set

    @property
    def time_set(self) -> FiniteScalarRangeSet:
        """The set of the time steps."""
        return self.model.time_set

    @property
    def step_length(self) -> pyo.Param:
        """The time difference between two time steps in seconds."""
        return self.model.step_length

    @property
    def year_length(self) -> pyo.Param:
        """The number of years each period is valid for."""
        return self.model.year_length

    @property
    def model(self) -> pyo.Model:
        """The Pyomo model."""
        return self._model

    @property
    def objective(self) -> _BaseObjective:
        """The objective of the model."""
        if self._objective is None:
            raise RuntimeError("Accessing unset objective.")
        return self._objective

    @property
    def weights(self) -> pyo.Param:
        """The weights of the years and periods used for the objective function"""
        return self.model.weights

    @property
    def units(self) -> list[BaseUnit]:
        return self._units

    @property
    def networks(self) -> list[_BaseNetwork]:
        """List of all registered networks."""
        return self._networks

    @property
    def environments(self) -> list[_BaseEnvironment]:
        """List of all registered environments."""
        return self._environments


class BasicSystem(_BaseSystem):
    """System for basic optimization."""
