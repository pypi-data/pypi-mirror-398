from __future__ import annotations

import warnings
from abc import ABC
from collections.abc import Sequence
from typing import ClassVar

import pyomo.environ as pyo
from pydantic import BaseModel

from eta_components.milp_component_library.systems import _BaseSystem


class BaseObject(BaseModel, ABC):
    """Provides a generic structure for models in energy supply systems."""

    _param_names: ClassVar[list[str]] = []
    _optional_params: ClassVar[dict] = {}
    _forbidden_updates: ClassVar[list[str]] = []

    def __init__(self, name: str, data: dict, system: _BaseSystem):  # aggregation
        """Constructor method.

        :param name: The name for this object. str.
        :param data: The data used for the Pyomo model. dict.
        :param system: The system where this instance will be registered. BaseFramework.
        """
        self._validate_name(name)
        self._name = name

        self._model: pyo.Model = pyo.ConcreteModel()
        self._system: _BaseSystem = system

        self._data: dict = data

    @staticmethod
    def _validate_name(name: str):
        if not name.isidentifier():
            warnings.warn(
                f"The name '{name}' is not a valid identifier. For better access to the optimization "
                f"results, choose a valid Python variable identifier as a name.",
                stacklevel=2,
            )

    @staticmethod
    def _create_scalar_param(value: float):
        """Adds or updates a scalar Pyomo parameter in the model.

        Checks whether a component with the supplied name already exists and then calls the corresponding methods to
        either initialize a new parameter with the supplied data or updates the existing parameter with the new data.

        :param value: The scalar value for the parameter. int or float.
        """
        if not isinstance(value, int | float):
            raise TypeError(f"Argument data is of type {type(value)}, should be an int or float.")
        return pyo.Param(default=value, mutable=True)

    def _create_indexed_param(self, value: float | dict, sets: pyo.Set | Sequence[pyo.Set] = None):
        """Adds or updates an indexed Pyomo parameter in the model.

        Checks whether a component with the supplied name already exists and then calls the corresponding methods to
        either initialize a new parameter with the supplied data or updates the existing parameter with the new data.

        :param value: The value or values for the parameter. int, float or dict.
        """
        if not (isinstance(value, int | float | dict)):
            raise TypeError(f"Argument data is of type {type(value)}, should be int, float or dict.")

        if sets is None:
            sets = self._system.sets
        elif isinstance(sets, pyo.Set | pyo.RangeSet):
            sets = (sets,)

        if isinstance(value, int | float):
            value = pyo.Param(*sets, default=value, mutable=True)
        elif isinstance(value, dict):
            value = pyo.Param(*sets, initialize=value, default=0, mutable=True)
        else:
            raise TypeError
        return value

    @staticmethod
    def _update_param(param: pyo.Param, value: float | dict):
        """Updates an existing parameter with the new value."""
        param.store_values(value)

    @property
    def name(self) -> str:
        """The name of this object."""
        return self._name

    @property
    def data(self) -> dict:
        """The data values supplied to this object during initialization and updates."""
        return self._data

    @property
    def model(self) -> pyo.Model:
        """The Pyomo model of this object."""
        return self._model
