from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.exceptions import InvalidParameterNameError, MissingParameterError
from eta_components.milp_component_library.systems import _BaseSystem


class BaseObject(ABC):
    """Provides a generic structure for models in energy supply systems."""

    _param_names: ClassVar[list] = []
    _optional_params: ClassVar[dict] = {}
    _forbidden_updates: ClassVar[list] = []

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

        self._validate_data(data)
        data = self._fill_missing_optional_parameters(data)
        self._data: dict = data

    @staticmethod
    def _validate_name(name: str):
        if not name.isidentifier():
            warnings.warn(
                f"The name '{name}' is not a valid identifier. For better access to the optimization "
                f"results, choose a valid Python variable identifier as a name.",
                stacklevel=2,
            )

    def _validate_data(self, data: dict):
        """Validates the data if its keys match the values in _param_names and _optional_params
        or if any keys in data are missing."""
        invalid_keys = list(set(data.keys()) - set(self._param_names) - set(self._optional_params))
        missing_keys = list(set(self._param_names) - set(data.keys()))

        if len(invalid_keys) > 0:
            raise InvalidParameterNameError(
                f"Received invalid parameter names: {invalid_keys}.\n"
                f"Valid required key values for the argument 'data' are: {self._param_names}.\n"
                f"Valid optional key values for the argument 'data' are: {list(self._optional_params.keys())}"
            )
        if len(missing_keys) > 0:
            raise MissingParameterError(
                f"Missing data for the parameters: {missing_keys}. Add these keys with values to the argument 'data'."
            )

    def _fill_missing_optional_parameters(self, data: dict) -> dict:
        """Copies the passed data argument and fills it with any missing optional parameters and their default
        values."""
        data_ = data.copy()
        for optional_param, default_value in self._optional_params.items():
            if optional_param not in data_:
                data_[optional_param] = default_value
        return data_

    @abstractmethod
    def _populate_model(self):
        """Populate the Pyomo model with parameters, variables, expressions and constraints. Gets called automatically
        during initialization of the class.
        """
        pass

    def update_data(self, new_data: dict):
        """Update the Pyomo model with new values.

        Updates the current used values with the new values in data. The keys in data must be a (sub-)set of the keys
        used in the initialization method.

        :param new_data: The new data replacing the previously used values.
        """
        for forbidden_param in self._forbidden_updates:
            if forbidden_param in new_data:
                raise ValueError(f"The parameter {forbidden_param} cannot be updated.")

        self._validate_data(self._data | new_data)
        self._data = self._data | new_data
        self._reinitialize_params()

    @abstractmethod
    def _reinitialize_params(self):
        """Reinitializes the Pyomo model after the data was updated. This method must update all parameters of the
        pyomo model which are not in the classes forbidden_updates.
        """
        pass

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
