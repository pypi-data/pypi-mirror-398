from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np
import pyomo.environ as pyo

from eta_components.milp_component_library.networks import PowerSign, _Thermal
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import (
        AlternatingCurrent,
        CoolingFluid,
        Fuel,
        HeatingFluid,
        _ThermalFluid,
    )
    from eta_components.milp_component_library.systems import _BaseSystem


class Chp(BaseOperational):
    """Converter model for a combined heat and power unit.

    The chp's thermal outlets are connected to a high-temperature heating network (exhaust_heat_network),
    a low-temperature heating network (waste_heat_network) and a cooling network. The first one is always required,
    whereas the last two are optional (but always need to be supplied together, if they are supplid).
    The exhaust heat power into the high-temperature network is calculated by:
        P_heat_exhaust = eta_th_exhaust * P_out / eta
    The waste heat power into the low-temperature network and the cooling input from the cooling network are calculated
        by:
        P_motor_heat = eta_th_motor * P_out / eta
        P_waste_heat <= P_motor_heat * motor_heat_usability
        P_cooling = P_motor_heat - P_waste_heat
    So the motor heat can be used to heat the low-temperature heating network. Any remaining motor heat must be cooled
    by the cooling network. If no low-temperature heating network and cooling network are supplied, the motor heat is
    assumed to be zero.

    The electricity output is calculated by:
        eta_el = eta - eta_th_exhaust - eta_th_motor
        P_el_out = eta_el * P_out / eta
    """

    _param_names: ClassVar[list[str]] = [*BaseOperational._param_names, "eta_th_exhaust"]
    _optional_params: ClassVar[dict[str, float]] = dict(
        BaseOperational._optional_params, **{"eta_th_motor": 0, "motor_heat_usability": 1}
    )

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        fuel_network: Fuel,
        electrical_network: AlternatingCurrent,
        exhaust_heat_network: HeatingFluid,
        waste_heat_network: _ThermalFluid = None,
        cooling_network: CoolingFluid = None,
    ):
        """Constructor method.

        Extends the base method by allowing more properties to be passed in the
        data argument and requiring a gas, electrical and heating network which
        the CHP is connected to.

        The additional valid keys for the data argument are the following:
        - eta_th_exhaust: The thermal efficiency under full load for converting
            the gas inlet to the exhaust heat outlet. Indexed or scalar.
            Note that the electrical efficiency is calculated by
                eta_el = eta - eta_th_exhaust - eta_th_motor.
        - eta_th_motor: Optional. The thermal efficieny under full load for
            converting the motor heat outlet. Indexed or scalar. Defaults to 0.
        - motor_heat_usability: Optional. The usable fraction (0 to 1) of the
            motor heat for the waste heat network. Indexed or scalar. Defaults
            to 1.
        """
        self._has_lt_networks: bool = False
        if self._check_lt_networks_supplied_if_eta_th_lt_gt_zero(name, waste_heat_network, cooling_network, data):
            self._has_lt_networks = True

        self._fuel_net: Fuel = fuel_network
        self._heating_net: _Thermal = exhaust_heat_network
        self._electrical_net: AlternatingCurrent = electrical_network
        self._waste_heat_net: _ThermalFluid | None = waste_heat_network
        self._cooling_net: CoolingFluid | None = cooling_network

        super().__init__(name, data, system)

    @staticmethod
    def _check_lt_networks_supplied_if_eta_th_lt_gt_zero(
        name: str,
        waste_heat_network: _ThermalFluid,
        cooling_network: CoolingFluid,
        data: dict,
    ) -> bool:
        eta_th_motor = data.get("eta_th_motor", 0)

        if waste_heat_network is not None and cooling_network is not None:
            # Both networks were supplied
            return True

        if (waste_heat_network is not None) ^ (cooling_network is not None):  # XOR
            # Only one network was supplied
            raise ValueError("Must supply both waste_heat_network and cooling_network or neither of them.")

        if isinstance(eta_th_motor, float):
            if eta_th_motor > 0:
                raise ValueError(
                    f"For unit {name} the supplied eta_th_motor is greater than zero, but no waste_heat_network and "
                    "cooling_network were supplied."
                )
        elif isinstance(eta_th_motor, dict) and (np.asarray(eta_th_motor.values()) > 0).any():
            raise ValueError(
                f"For unit {name} some or all of the supplied eta_th_motor are greater than zero, but no "
                "waste_heat_network and cooling_network were supplied."
            )
        return False

    def _register_at_networks(self):
        self._fuel_net.register_unit(self, self.p_fuel_in, PowerSign.NEGATIVE)
        self._electrical_net.register_unit(self, self.p_el_out, PowerSign.POSITIVE)
        self._heating_net.register_unit(self, self.p_heat_out, PowerSign.POSITIVE)
        if self._has_lt_networks:
            self._waste_heat_net.register_unit(self, self.p_waste_heat_out, PowerSign.POSITIVE)
            self._cooling_net.register_unit(self, self.p_cooling_in, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._fuel_net.unregister_unit(self)
        self._electrical_net.unregister_unit(self)
        self._heating_net.unregister_unit(self)
        if self._has_lt_networks:
            self._waste_heat_net.unregister_unit(self)
            self._cooling_net.unregister_unit(self)

    def _init_params(self):
        super()._init_params()
        self.model.eta_th_exhaust = self._create_indexed_param(self._data["eta_th_exhaust"])
        self.model.eta_th_motor = self._create_indexed_param(self._data["eta_th_motor"])
        self.model.motor_heat_usability = self._create_indexed_param(self._data["motor_heat_usability"])

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.eta_th_exhaust, self._data["eta_th_exhaust"])
        self._update_param(self.model.eta_th_motor, self._data["eta_th_motor"])
        self._update_param(self.model.motor_heat_usability, self._data["motor_heat_usability"])

    def _init_variables(self):
        super()._init_variables()
        self.model.p_waste_heat_out = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_expressions(self):
        """Initializes the expressions. Extends the base method by also implementing expressions for the heat and
        electrical output."""
        super()._init_expressions()

        def p_heat_out(m, *idx: int):
            return m.p_out[idx] * m.eta_th_exhaust[idx] / m.eta[idx]

        def p_el_out(m, *idx: int):
            return m.p_out[idx] * (m.eta[idx] - m.eta_th_exhaust[idx] - m.eta_th_motor[idx]) / m.eta[idx]

        def p_motor_heat_out(m, *idx: int):
            return m.p_out[idx] * m.eta_th_motor[idx] / m.eta[idx]

        def p_cooling_in(m, *idx: int):
            return m.p_motor_heat_out[idx] - m.p_waste_heat_out[idx]

        self.model.p_heat_out = pyo.Expression(*self._system.sets, rule=p_heat_out)
        self.model.p_el_out = pyo.Expression(*self._system.sets, rule=p_el_out)
        self.model.p_motor_heat_out = pyo.Expression(*self._system.sets, rule=p_motor_heat_out)
        self.model.p_cooling_in = pyo.Expression(*self._system.sets, rule=p_cooling_in)

    def _init_constraints(self):
        super()._init_constraints()

        def p_waste_heat_max(m, *idx):
            return m.p_waste_heat_out[idx] <= m.p_motor_heat_out[idx] * m.motor_heat_usability[idx]

        self.model.p_waste_heat_max = pyo.Constraint(*self._system.sets, rule=p_waste_heat_max)

    @property
    def p_heat_out(self) -> pyo.Expression:
        """The exhaust heat output capacity."""
        return self.model.p_heat_out

    @property
    def p_el_out(self) -> pyo.Expression:
        """The electrical output capacity."""
        return self.model.p_el_out

    @property
    def p_fuel_in(self) -> pyo.Expression:
        """The fuel power input capacity."""
        return self._p_in

    @property
    def p_waste_heat_out(self) -> pyo.Var:
        """The waste heat output capacity."""
        return self.model.p_waste_heat_out

    @property
    def p_cooling_in(self) -> pyo.Expression:
        """The cooling input capacity."""
        return self.model.p_cooling_in
