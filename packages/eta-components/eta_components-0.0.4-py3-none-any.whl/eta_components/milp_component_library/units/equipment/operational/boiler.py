from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

import pyomo.environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import Electrical, Gas, _Thermal
    from eta_components.milp_component_library.systems import _BaseSystem


class BaseBoiler(BaseOperational, ABC):
    """Converter model for a boiler."""

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, heating_network: _Thermal):
        """Constructor method. Extends the base method by requiring a heating network which the boiler is connected
        to."""
        self._heating_net: _Thermal = heating_network
        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._heating_net.register_unit(self, self.p_heat_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._heating_net.unregister_unit(self)

    @property
    def p_heat_out(self) -> pyo.Expression:
        """The heat output capacity."""
        return self._p_out


class ElectrodeBoiler(BaseBoiler):
    """Converter model for an electrode boiler."""

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: Electrical,
        heating_network: _Thermal,
    ):
        """Constructor method. Extends the base method by requiring an electrical network which the boiler is connected
        to."""
        self._electrical_net = electrical_network
        super().__init__(name, data, system, heating_network=heating_network)

    def _register_at_networks(self):
        super()._register_at_networks()
        self._electrical_net.register_unit(self, self.p_el_in, PowerSign.NEGATIVE)

    @property
    def p_el_in(self) -> pyo.Expression:
        """The electric input capacity."""
        return self._p_in


class GasBoiler(BaseBoiler):
    """Converter model for a gas boiler."""

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        gas_network: Gas,
        heating_network: _Thermal,
    ):
        """Constructor method. Extends the base method by requiring a gas network which the boiler is connected
        to."""
        self._gas_net: Gas = gas_network
        super().__init__(name, data, system, heating_network=heating_network)

    def _register_at_networks(self):
        super()._register_at_networks()
        self._gas_net.register_unit(self, self.p_gas_in, PowerSign.NEGATIVE)

    @property
    def p_gas_in(self) -> pyo.Expression:
        """The gas input capacity."""
        return self._p_in
