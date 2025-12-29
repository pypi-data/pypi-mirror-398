from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import ClassVar

import numpy as np
import pyomo.environ as pyo

from eta_components.milp_component_library.environments import DryAir
from eta_components.milp_component_library.networks import (
    CoolingFluid,
    DirectCurrent,
    Electrical,
    Gas,
    HeatingFluid,
    PowerSign,
    _BaseNetwork,
    _ThermalFluid,
)
from eta_components.milp_component_library.systems import _BaseSystem
from eta_components.milp_component_library.units.base_unit import BaseStandaloneUnit


class BaseEquipment(BaseStandaloneUnit, ABC):
    """"""


class BaseConverter(BaseEquipment, ABC):
    """Converters are equipment which convert certain energy inputs into one or multiple energy outputs. They have
    one or multiple degrees of freedom regarding their energy input and output.
    """

    @property
    def is_operating(self) -> pyo.Var:
        """The operating decision for the converter."""
        return self.model.x

    @property
    def _p_in(self) -> pyo.Var | pyo.Expression:
        """The input capacity of the converter."""
        return self.model.p_in

    @property
    def _p_out(self) -> pyo.Var | pyo.Expression:
        """The output capacity of the converter."""
        return self.model.p_out

    @property
    def _p_out_nom(self) -> pyo.Param | pyo.Var | pyo.Expression:
        """The nominal output capacity of the converter."""
        return self.model.p_out_nom


class BaseStorage(BaseEquipment, ABC):
    _sign = PowerSign.POSITIVE
    _optional_params: ClassVar[dict] = {
        **BaseEquipment._optional_params,
        **{"allow_simultaneous_charging_and_discharging": False},
    }

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method."""
        self._net: _BaseNetwork = network
        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._net.register_unit(self, self._p_in, PowerSign.NEGATIVE)
        self._net.register_unit(self, self._p_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._net.unregister_unit(self)

    def _init_params(self):
        self.model.c_in_max = self._create_scalar_param(self._data["c_in_max"])
        self.model.c_out_max = self._create_scalar_param(self._data["c_out_max"])
        self.model.eta = self._create_indexed_param(self._data["eta"])
        self.model.loss = self._create_scalar_param(self._data["loss"])
        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.emissions = self._create_indexed_param(0)

    def _reinitialize_params(self):
        self._update_param(self.model.c_in_max, self._data["c_in_max"])
        self._update_param(self.model.c_out_max, self._data["c_out_max"])
        self._update_param(self.model.loss, self._data["loss"])
        self._update_param(self.model.eta, self._data["eta"])
        self._update_param(self.model.maintenance_factor, self._data["maintenance_factor"])

    def _energy_balance(self):
        def rule(m, *idx: int):
            time_idx = idx[-1]
            other_indices = idx[:-1]
            previous_energy = m.e[other_indices, self._system.time_set.prevw(time_idx)] * (
                1 - m.loss * self._system.step_length
            )
            # p_in is negative, so it must be multiplied with -1 to yield a positive inlet energy
            inlet_energy = (
                -self._system.step_length * m.eta[idx] * m.p_in[other_indices, self._system.time_set.prevw(time_idx)]
            )
            # Changes from Baumgärtner: The outlet flow must be divided by the efficiency
            outlet_energy = (
                self._system.step_length / m.eta[idx] * m.p_out[other_indices, self._system.time_set.prevw(time_idx)]
            )
            return m.e[idx] == previous_energy + inlet_energy - outlet_energy

        return rule

    @property
    def e_nom(self) -> pyo.Param | pyo.Var:
        """The nominal energy content of the storage."""
        return self.model.p_out_nom

    @property
    def e(self) -> pyo.Var:
        """The energy content of the storage."""
        return self.model.e

    @property
    def is_operating(self) -> pyo.Var:
        """The operating decision for the converter."""
        if not self._data["allow_simultaneous_charging_and_discharging"]:
            raise ValueError(
                f"Operating state of storage {self.name} is not available because "
                f"'allow_simultaneous_charging_and_discharging' was set to True during initialization"
            )
        return self.model.x

    @property
    def _p_in(self) -> pyo.Var | pyo.Expression:
        """The input capacity of the converter."""
        return self.model.p_in

    @property
    def _p_out(self) -> pyo.Var | pyo.Expression:
        """The output capacity of the converter."""
        return self.model.p_out


class BaseElectricalStorage(BaseStorage, ABC):
    def __init__(self, name: str, data: dict, system: _BaseSystem, *, electrical_network: Electrical):
        super().__init__(name, data, system, network=electrical_network)


class BaseBattery(BaseElectricalStorage, ABC):
    def __init__(self, name: str, data: dict, system: _BaseSystem, *, electrical_network: DirectCurrent):
        super().__init__(name, data, system, electrical_network=electrical_network)

    @property
    def p_el_in(self) -> pyo.Expression:
        """The electrical input capacity."""
        return self._p_in

    @property
    def p_el_out(self) -> pyo.Expression:
        """The electrical output capacity."""
        return self._p_out


class BaseThermalStorage(BaseStorage, ABC):
    """Converter model for a thermal storage. Refer to the base class for implementation details."""

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, thermal_network: _ThermalFluid):
        super().__init__(name, data, system, network=thermal_network)


class BaseFuelStorage(BaseStorage, ABC):
    """Converter model for a fuel storage. Refer to the base class for implementation details."""

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, fuel_network: Gas):
        super().__init__(name, data, system, network=fuel_network)


class BaseHeatStorage(BaseThermalStorage, ABC):
    """Converter model for a thermal heat storage. Refer to the base class for implementation details."""

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, heating_network: HeatingFluid):
        super().__init__(name, data, system, thermal_network=heating_network)

    @property
    def p_heat_in(self) -> pyo.Expression:
        """The heat input capacity."""
        return self._p_in

    @property
    def p_heat_out(self) -> pyo.Expression:
        """The heat output capacity."""
        return self._p_out


class BaseColdStorage(BaseThermalStorage, ABC):
    _sign = PowerSign.NEGATIVE

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, cooling_network: CoolingFluid):
        super().__init__(name, data, system, thermal_network=cooling_network)

    @property
    def p_cool_in(self) -> pyo.Expression:
        """The cooling input capacity."""
        return self._p_in

    @property
    def p_cool_out(self) -> pyo.Expression:
        """The cooling output capacity."""
        return self._p_out


class BaseHydrogenStorage(BaseFuelStorage, ABC):
    def __init__(self, name: str, data: dict, system: _BaseSystem, *, hydrogen_network: Gas):
        super().__init__(name, data, system, fuel_network=hydrogen_network)

    @property
    def p_charge(self) -> pyo.Expression:
        """The cooling input capacity."""
        return self._p_in

    @property
    def p_discharge(self) -> pyo.Expression:
        """The cooling output capacity."""
        return self._p_out


class BaseHeatExchanger(BaseConverter, ABC):
    _param_names: ClassVar[list[str]] = ["heat_transfer_coefficient"]
    _optional_params: ClassVar[dict[str, float]] = {
        "plr_min": 0.0,
        "eta": 1.0,
    }

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        hot_network: _ThermalFluid,
        cold_network: _ThermalFluid,
    ):
        """Constructor method.

        Extends the base method by allowing more properties to be passed in the data argument and requiring a hot and
        cold network which the heat exchanger is connected to.
        """
        self._hot_network: _ThermalFluid = hot_network
        self._cold_network: _ThermalFluid = cold_network

        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._hot_network.register_unit(self, self.p_in, PowerSign.NEGATIVE)
        self._cold_network.register_unit(self, self.p_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._hot_network.unregister_unit(self)
        self._cold_network.unregister_unit(self)

    def _log_mean_temp_diff(self) -> dict:
        """Calculates the log mean temperature difference with the formula from
        https://en.wikipedia.org/wiki/Logarithmic_mean_temperature_difference.
        """
        log_mean_temp_diff = {}
        for index in itertools.product(*self._system.sets):
            delta_temp_a = self._delta_temp_a(*index)
            delta_temp_b = self._delta_temp_b(*index)
            if pyo.value(delta_temp_a) <= 0 or pyo.value(delta_temp_b) <= 0:
                log_mean_temp_diff[index] = 0
            elif np.isclose(pyo.value(delta_temp_a), pyo.value(delta_temp_b)):
                log_mean_temp_diff[index] = delta_temp_a
            else:
                log_mean_temp_diff[index] = (delta_temp_a - delta_temp_b) / (
                    pyo.log(delta_temp_a) - pyo.log(delta_temp_b)
                )
        return log_mean_temp_diff

    @abstractmethod
    def _delta_temp_a(self, *idx: int):
        """The temperature difference between the hot fluid inlet and either the cold fluid inlet or outlet, depending
        on the heat exchanger type, see https://en.wikipedia.org/wiki/Logarithmic_mean_temperature_difference.
        """

    @abstractmethod
    def _delta_temp_b(self, *idx: int):
        """The temperature difference between the hot fluid outlet and either the cold fluid inlet or outlet, depending
        on the heat exchanger type, see https://en.wikipedia.org/wiki/Logarithmic_mean_temperature_difference.
        """

    @property
    def area(self) -> pyo.Expression:
        """The surface area."""
        return self.model.p_out_nom

    @property
    def p_in(self) -> pyo.Expression:
        """The thermal input capacity."""
        return self._p_in

    @property
    def p_out(self) -> pyo.Expression:
        """The thermal output capacity."""
        return self._p_out


class BaseParallelFlowHeatExchanger(BaseHeatExchanger, ABC):
    """Converter model for a parallel flow heat exchanger. Refer to the base class for implementation details."""

    def _delta_temp_a(self, *idx: int):
        return self._hot_network.t_hot[idx] - self._cold_network.t_cold[idx]

    def _delta_temp_b(self, *idx: int):
        return self._hot_network.t_cold[idx] - self._cold_network.t_hot[idx]


class BaseCounterFlowHeatExchanger(BaseHeatExchanger, ABC):
    """Converter model for a counter flow heat exchanger. Refer to the base class for implementation details."""

    def _delta_temp_a(self, *idx: int):
        return self._hot_network.t_hot[idx] - self._cold_network.t_hot[idx]

    def _delta_temp_b(self, *idx: int):
        return self._hot_network.t_cold[idx] - self._cold_network.t_cold[idx]


class BaseHeatPump(BaseConverter, ABC):
    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: Electrical,
        heating_network: HeatingFluid,
    ):
        """Constructor method. Extends the base method by requiring an electrical network and a thermal fluid network
        which the heat pump is connected to.

        The key "eta" in the argument "data" represents the coefficient of performance (COP), which is the heat output
        capacity divided by the electric input capacity under nominal conditions.
        """
        self._electrical_net: Electrical = electrical_network
        self._heating_net: HeatingFluid = heating_network
        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._heating_net.register_unit(self, self.p_heat_out, PowerSign.POSITIVE)
        self._electrical_net.register_unit(self, self.p_el_in, PowerSign.NEGATIVE)

    def _unregister_at_networks(self):
        self._heating_net.unregister_unit(self)
        self._electrical_net.unregister_unit(self)

    @property
    def p_heat_out(self) -> pyo.Var:
        """The heating output capacity."""
        return self._p_out

    @property
    def p_heat_out_nom(self) -> pyo.Var:
        """The nominal heating output capacity."""
        return self._p_out_nom

    @property
    def p_el_in(self) -> pyo.Expression:
        """The electrical input capacity."""
        return self._p_in


class BaseAirWaterHeatPump(BaseHeatPump, ABC):
    """Converter model for an air-water heat pump."""

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: Electrical,
        heating_network: HeatingFluid,
        ambient_environment: DryAir,
    ):
        """Constructor method. Extends the base method by requiring an ambient environment in which the heat pump is
        located.
        """
        self._ambient_env = ambient_environment
        super().__init__(name, data, system, heating_network=heating_network, electrical_network=electrical_network)


class BaseWaterWaterHeatPump(BaseHeatPump, ABC):
    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: Electrical,
        heating_network: HeatingFluid,
        cold_network: _ThermalFluid,
    ):
        """Constructor method. Extends the base method by requiring a cold network the heat pump is connected to."""
        self._cold_net = cold_network
        super().__init__(name, data, system, heating_network=heating_network, electrical_network=electrical_network)

    def _init_expressions(self):
        super()._init_expressions()

        def p_cool_out(m, *idx: int):
            return -m.p_out[idx] - m.p_in[idx]

        self.model.p_cool_out = pyo.Expression(*self._system.sets, rule=p_cool_out)

    def _register_at_networks(self):
        super()._register_at_networks()
        self._cold_net.register_unit(self, self.p_cool_out, PowerSign.NEGATIVE)

    def _unregister_at_networks(self):
        super()._unregister_at_networks()
        self._cold_net.unregister_unit(self)

    @property
    def p_cool_out(self) -> pyo.Expression:
        """The cooling output capacity."""
        return self.model.p_cool_out
