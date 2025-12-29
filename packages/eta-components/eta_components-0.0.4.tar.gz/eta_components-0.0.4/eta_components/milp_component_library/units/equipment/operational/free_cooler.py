from __future__ import annotations

import abc
import warnings
from abc import ABC
from typing import TYPE_CHECKING, ClassVar

from pyomo import environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational

if TYPE_CHECKING:
    from eta_components.milp_component_library.environments import DryAir, HumidAir, _Air
    from eta_components.milp_component_library.networks import CoolingFluid, Electrical, Water, _ThermalFluid
    from eta_components.milp_component_library.systems import _BaseSystem


class FreeCooler(BaseOperational, ABC):
    """Base model for free coolers"""

    _bigm = 1e3
    _optional_params: ClassVar[dict[str, float]] = dict(BaseOperational._optional_params, **{"approach_min": 0})

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: Electrical,
        cooling_network: CoolingFluid,
        ambient_environment: _Air,
    ):
        """Constructor method"""
        self._electrical_net: Electrical = electrical_network
        self._cold_net: _ThermalFluid = cooling_network
        self._env: _Air = ambient_environment
        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._cold_net.register_unit(self, self.p_cool_out, PowerSign.NEGATIVE)
        self._electrical_net.register_unit(self, self.p_el_in, PowerSign.NEGATIVE)

    def _unregister_at_networks(self):
        self._cold_net.unregister_unit(self)
        self._electrical_net.unregister_unit(self)

    def _init_params(self):
        super()._init_params()
        self.model.approach_min = self._create_scalar_param(self._data["approach_min"])

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.approach_min, self._data["approach_min"])

    def _init_constraints(self):
        super()._init_constraints()

        def restrict_operation_when_ambient_temperature_too_high(m: pyo.Model, *idx: int):
            """Rule for restricting the free cooler operation if the relevant ambient temperature is above the cooling
            flow temperature.
            """
            if pyo.value(self._cold_net.t_cold[idx]) < pyo.value(self._approach_temperature[idx] + m.approach_min):
                warnings.warn(
                    f"{self.__class__.__name__} {self.name} cannot reach the cooling network flow temperature for "
                    f"index {idx}. The flow temperature is {pyo.value(self._cold_net.t_cold[idx])}, the air "
                    f"temperature {pyo.value(self._approach_temperature[idx])} and the minimum approach "
                    f"{pyo.value(m.approach_min)}.",
                    stacklevel=2,
                )
            return -(1 - m.x[idx]) * self._bigm <= self._cold_net.t_cold[idx] - (
                self._approach_temperature[idx] + m.approach_min
            )

        self.model.restrict_operation = pyo.Constraint(
            *self._system.sets, rule=restrict_operation_when_ambient_temperature_too_high
        )

    @property
    @abc.abstractmethod
    def _approach_temperature(self) -> pyo.Param:
        """The approach temperature of the free cooler. Can be either the dry- or wet-bulb-temperature."""

    @staticmethod
    def _rule_p_out(m, *idx: int) -> pyo.Expression:
        return -1 * m.p_out_nom * m.plr[idx]

    @property
    def p_cool_out(self) -> pyo.Expression:
        """The cooling output capacity."""
        return self._p_out

    @property
    def p_el_in(self) -> pyo.Expression:
        """The electrical input capacity."""
        return self._p_in


class DryCooler(FreeCooler):
    """Converter model for a dry cooler.

    Taken from Baumgärtner (2020): "Optimization of low-carbon energy systems from industrial to national scale" from
    p. 128 ff.
    """

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: Electrical,
        cooling_network: CoolingFluid,
        ambient_environment: DryAir,
    ):
        """Constructor method. Extends the base method by requiring an electrical and a cooling network which the
        dry cooler is connected to and an ambient environment where it is located in.

        Extends the allowed parameter names of the base class with the following.
        - approach_min: The minimum permissible difference between the cold network flow temperature and the
            wet-bulb air temperature. This can be set to a large negative value in order to deactivate the constraint
            that the unit cannot operate if the ambient temperature is above the cold temperature.
            Scalar. Defaults to 0 Kelvin.
        """
        super().__init__(
            name,
            data,
            system,
            electrical_network=electrical_network,
            cooling_network=cooling_network,
            ambient_environment=ambient_environment,
        )

    @property
    def _approach_temperature(self) -> pyo.Param:
        return self._env.temp_db


class HybridCooler(FreeCooler):
    """Converter model for a hybrid cooler."""

    _param_names: ClassVar[list[str]] = [*BaseOperational._param_names, "specific_water_consumption"]

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: Electrical,
        cooling_network: CoolingFluid,
        ambient_environment: HumidAir,
        water_network: Water,
    ):
        """Constructor method. Extends the base method by requiring an electrical, cooling and water network which the
        hybrid cooler is connected to and an ambient environment where it is located in.

        Extends the allowed parameter names of the base class with the following.
        - specific_water_consumption: The water consumption in m3/s per W of cooling output. Scalar or indexed.
        - approach_min: The minimum permissible difference between the cold network flow temperature and the
            wet-bulb air temperature. This can be set to a large negative value in order to deactivate the constraint
            that the unit cannot operate if the ambient temperature is above the cold temperature.
            Scalar. Defaults to 0 Kelvin.
        """
        self._water_net: Water = water_network
        super().__init__(
            name,
            data,
            system,
            electrical_network=electrical_network,
            cooling_network=cooling_network,
            ambient_environment=ambient_environment,
        )

    def _init_params(self):
        super()._init_params()
        self.model.specific_water_consumption = self._create_indexed_param(self.data["specific_water_consumption"])

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.specific_water_consumption, self.data["specific_water_consumption"])

    def _init_expressions(self):
        super()._init_expressions()

        def water_consumption(m, *idx: int):
            # Water consumption should be negative, as water is taken out of the network
            return m.p_out[idx] * m.specific_water_consumption[idx]

        self.model.water_consumption = pyo.Expression(*self._system.sets, rule=water_consumption)

    @property
    def _approach_temperature(self) -> pyo.Param:
        return self._env.temp_wb

    def _register_at_networks(self):
        super()._register_at_networks()
        self._water_net.register_unit(self, self.water_consumption, PowerSign.NEGATIVE)

    def _unregister_at_networks(self):
        super()._unregister_at_networks()
        self._water_net.unregister_unit(self)

    @property
    def water_consumption(self) -> pyo.Expression:
        """The water consumption."""
        return self.model.water_consumption
