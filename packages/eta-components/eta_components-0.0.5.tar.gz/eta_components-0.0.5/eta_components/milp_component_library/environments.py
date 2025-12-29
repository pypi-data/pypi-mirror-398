from abc import ABC, abstractmethod
from typing import ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.base_object import BaseObject
from eta_components.milp_component_library.systems import _BaseSystem
from eta_components.milp_component_library.utils import DeprecatedClassMeta


class _BaseEnvironment(BaseObject, ABC):
    """An environment that defines an interface to access parameter values needed by multiple different sub-models.

    Environments provide an interface to access and share Pyomo parameter values across different sub-models.
    They do not enforce an energy balance across its registered units. Use cases are for example to define an outside
    ambient environment with a temperature and humidity to calculate the efficiency of all cooling producers that are
    placed in this environment.
    """

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Constructor method.

        :param name: The name for this environment, str.
        :param data: The data for this environment with class-specific keys, dict.
        :param system: The system where this environment should be registered.
        """
        super().__init__(name, data, system)
        self._populate_model()
        system.register_environment(self)

    def _populate_model(self):
        self._init_params()

    @abstractmethod
    def _init_params(self):
        """Initializes the parameters in the attribute self.model."""
        pass

    def _reinitialize_params(self):
        self._init_params()


class _Air(_BaseEnvironment, ABC):
    """An abstract air environment."""


class DryAir(_Air):
    """An air environment which defines a dry-bulb air temperature."""

    _param_names: ClassVar[list[str]] = [*_Air._param_names, "T_db"]

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Constructor method.

        Accepts the following keys for the argument data:
        - T_db: The dry-bulb air temperature in Kelvin, scalar or indexed
        """
        super().__init__(name, data, system)

    def _init_params(self):
        self.model.temp_db = self._create_indexed_param(self._data["T_db"])

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.temp_db, self._data["T_db"])

    @property
    def temp_db(self) -> pyo.Param:
        return self.model.temp_db


class Ambient(metaclass=DeprecatedClassMeta):
    _DeprecatedClassMeta__alias = DryAir


class HumidAir(DryAir):
    """A humid air environment which defines a dry-bulb and wet-bulb air temperature.

    Extends the base class DryAir by the following parameters:
        - T_wb: The wet-bulb air temperature in Kelvin, scalar or indexed.
    """

    _param_names: ClassVar[list[str]] = [*DryAir._param_names, "T_wb"]

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Constructor method.

        Extends the base class DryAir by accepting the following additional keys for the argument data:
        - T_wb: The wet-bulb air temperature in Kelvin, scalar or indexed.
        """
        super().__init__(name, data, system)

    def _init_params(self):
        super()._init_params()
        self.model.temp_wb = self._create_indexed_param(self._data["T_wb"])

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.temp_wb, self._data["T_wb"])

    @property
    def temp_wb(self) -> pyo.Param:
        return self.model.temp_wb


class SolarIrradiance(_BaseEnvironment):
    """An environment which defines a solar irradiance."""

    _param_names: ClassVar[list] = [
        "solar_irradiance",
    ]

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Constructor method.

        Accepts the following keys for the argument data:
        - solar_irradiance: The global solar irradiance in power per time, already accounted for the inclinations of
            the units which use this environment, scalar or indexed, non-negative.
        """
        super().__init__(name, data, system)

    def _init_params(self):
        super()._init_params()
        self.model.solar_irradiance = self._create_indexed_param(self._data["solar_irradiance"])
        pass

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.solar_irradiance, self._data["solar_irradiance"])

    @property
    def solar_irradiance(self) -> pyo.Param:
        """decorator to access methods like attributes directly:
        here necessary to access pyomo parameter solar_irradiance
        as a read only

        Returns:
            pyo.Param: solar irradiance as read only
        """
        return self.model.solar_irradiance
