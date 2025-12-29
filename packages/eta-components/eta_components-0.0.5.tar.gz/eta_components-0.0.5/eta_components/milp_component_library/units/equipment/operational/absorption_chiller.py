from __future__ import annotations

from typing import TYPE_CHECKING

import pyomo.environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import _ThermalFluid
    from eta_components.milp_component_library.systems import _BaseSystem


class AbsorptionChiller(BaseOperational):
    """Converter model for an absorption chiller."""

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        heating_network: _ThermalFluid,
        cooling_network: _ThermalFluid,
    ):
        """Constructor method. Extends the base method by requiring a heating network and a cooling network which the
        absorption chiller is connected to.
        """
        self._heating_net: _ThermalFluid = heating_network
        self._cooling_net: _ThermalFluid = cooling_network

        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._cooling_net.register_unit(self, self.p_cool_out, PowerSign.NEGATIVE)
        self._heating_net.register_unit(self, self.p_heat_in, PowerSign.NEGATIVE)

    def _unregister_at_networks(self):
        self._cooling_net.unregister_unit(self)
        self._heating_net.unregister_unit(self)

    @staticmethod
    def _rule_p_out(m: pyo.Model, *idx: int) -> pyo.Expression:
        return -1 * m.p_out_nom * m.plr[idx]

    @property
    def p_cool_out(self) -> pyo.Expression:
        """The cooling output capacity."""
        return self._p_out

    @property
    def p_heat_in(self) -> pyo.Expression:
        """The heating input capacity."""
        return self._p_in
