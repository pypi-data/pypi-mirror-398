from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

import pyomo.environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational

if TYPE_CHECKING:
    from eta_components.milp_component_library.environments import DryAir
    from eta_components.milp_component_library.networks import AlternatingCurrent, CoolingFluid, _ThermalFluid
    from eta_components.milp_component_library.systems import _BaseSystem


class BaseCompressionChiller(BaseOperational, ABC):
    """Converter model for a vapor compression chiller."""

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: AlternatingCurrent,
        cooling_network: CoolingFluid,
    ):
        """Constructor method. Extends the base method by requiring an electrical network and a thermal fluid network
        which the compression chiller is connected to.

        The key "eta" in the argument "data" represents the energy efficiency ratio (EER), which is the cooling output
        capacity divided by the electric input capacity under nominal conditions.
        """
        self._electrical_net: AlternatingCurrent = electrical_network
        self._cooling_net: CoolingFluid = cooling_network
        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._cooling_net.register_unit(self, self.p_cool_out, PowerSign.NEGATIVE)
        self._electrical_net.register_unit(self, self.p_el_in, PowerSign.NEGATIVE)

    def _unregister_at_networks(self):
        self._cooling_net.unregister_unit(self)
        self._electrical_net.unregister_unit(self)

    @staticmethod
    def _rule_p_out(m: pyo.Model, *idx: int) -> pyo.Expression:
        """Rule for generating an expression for the output capacity. Overrides the base method by inverting the sign
        of the output capacity, as cooling capacity is negative."""
        return -1 * m.p_out_nom * m.plr[idx]

    @property
    def p_cool_out(self) -> pyo.Expression:
        """The cooling output capacity."""
        return self._p_out

    @property
    def p_el_in(self) -> pyo.Expression:
        """The electrical input capacity."""
        return self._p_in


# noinspection DuplicatedCode
class AirWaterCompressionChiller(BaseCompressionChiller):
    """Converter model for an air-water vapor compression chiller.

    Taken from Baumgärtner (2020): "Optimization of low-carbon energy systems from industrial to national scale" from
    p. 128 ff.
    """

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        cooling_network: CoolingFluid,
        electrical_network: AlternatingCurrent,
        ambient_environment: DryAir,
    ):
        """Constructor method. Extends the base method by requiring an ambient environment in which the compression
        chiller is located.
        """
        self._ambient_env = ambient_environment
        super().__init__(name, data, system, cooling_network=cooling_network, electrical_network=electrical_network)


class WaterWaterCompressionChiller(BaseCompressionChiller):
    """Converter model for a water-water vapor compression chiller.

    Taken from Baumgärtner (2020): "Optimization of low-carbon energy systems from industrial to national scale" from
    p. 128 ff.
    """

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        cooling_network: CoolingFluid,
        electrical_network: AlternatingCurrent,
        hot_network: _ThermalFluid,
    ):
        """Constructor method. Extends the base method by requiring a heating network the compression chiller is
        connected to.
        """
        self._hot_net: _ThermalFluid = hot_network
        super().__init__(name, data, system, cooling_network=cooling_network, electrical_network=electrical_network)

    def _init_expressions(self):
        super()._init_expressions()

        def p_heat_out(m, *idx: int):
            # Energy balance is Q_heat + Q_cool + P_el = 0 --> Q_heat = -Q_cool - P_el
            return -m.p_in[idx] - m.p_out[idx]

        self.model.p_heat_out = pyo.Expression(*self._system.sets, rule=p_heat_out)

    def _register_at_networks(self):
        super()._register_at_networks()
        self._hot_net.register_unit(self, self.p_heat_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        super()._unregister_at_networks()
        self._hot_net.unregister_unit(self)

    @property
    def p_heat_out(self) -> pyo.Expression:
        """The heating output capacity."""
        return self.model.p_heat_out
