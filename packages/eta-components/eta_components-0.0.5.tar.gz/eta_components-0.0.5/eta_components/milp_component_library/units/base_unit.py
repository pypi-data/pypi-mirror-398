from __future__ import annotations

import abc
from abc import abstractmethod

import pyomo.environ as pyo
from pydantic.fields import ModelPrivateAttr, PydanticUndefined

from eta_components.milp_component_library.base_object import BaseObject
from eta_components.milp_component_library.systems import _BaseSystem


class BaseUnit(BaseObject):
    """A unit consumes or produces quantities in an energy supply system and can have multiple degrees of freedom.

    As a convention, any quantity that is consumed by the unit should have a negative sign, while quantities that are
    produced by the unit and fed into the supply system should have a positive sign. E.g. gas consumption <= 0,
    heating output >= 0. Note that when consuming cooling energy, the heat flow is in the reverse direction. Therefore,
    cooling output <= 0 and cooling input >= 0.
    """

    _has_investment_decision: bool = False

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Constructor method. Extends the base class by populating the Pyomo model with the supplied data and
        registers at the networks it is connected to.
        """
        super().__init__(name, data, system)
        self._populate_model()
        system.register_unit(self)

    @abstractmethod
    def unregister(self):
        pass

    def has_investment_decision(self) -> bool:
        flag = getattr(type(self), "_has_investment_decision", False)
        # Pydantic v2 may replace leading-underscore class attrs with ModelPrivateAttr
        if isinstance(flag, ModelPrivateAttr):
            flag = flag.get_default()
        if flag is PydanticUndefined:
            return False
        return bool(flag)

    @property
    @abstractmethod
    def time_step_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The time step cost, such as gas consumption cost, of the unit per step length indexed over the years,
        periods and time steps.
        """

    @property
    @abstractmethod
    def annual_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The annual cost, such as maintenance or capacity cost, of the unit per indexed over the years."""

    @property
    @abstractmethod
    def onetime_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The onetime cost, such as investment cost, of the unit."""

    @property
    @abstractmethod
    def emissions(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The emissions of the unit per step length indexed over the years, periods and time steps."""


class BaseAuxiliaryUnit(BaseUnit, abc.ABC):
    """BaseAuxiliaries are connected to networks and their models depend on other units."""

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Constructor method. Extends the base class by populating the Pyomo model with the supplied data and
        registers at the networks it is connected to.
        """
        super().__init__(name, data, system)


class BaseStandaloneUnit(BaseUnit, abc.ABC):
    """BaseEquipments are connected to networks and do not directly depend on other equipments for their models."""

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        super().__init__(name, data, system)
        self._register_at_networks()

    def _populate_model(self):
        """Populates the existing model by filling it with parameters, variables, expressions and constraints in the
        stated order.
        """
        self._init_params()
        self._init_variables()
        self._init_expressions()
        self._init_constraints()

    @abstractmethod
    def _register_at_networks(self):
        pass

    def unregister(self):
        self._unregister_at_system()
        self._unregister_at_networks()

    @abstractmethod
    def _unregister_at_networks(self):
        pass

    def _unregister_at_system(self):
        self._system.unregister_unit(self)

    @abstractmethod
    def _init_params(self):
        """Initializes all parameters that are needed for the model."""
        pass

    @abstractmethod
    def _init_variables(self):
        """Initializes all variables that are needed for the model."""
        pass

    @abstractmethod
    def _init_expressions(self):
        """Initializes all expressions that are needed for the model."""
        pass

    @abstractmethod
    def _init_constraints(self):
        """Initializes all constraints that are needed for the model."""
        pass
