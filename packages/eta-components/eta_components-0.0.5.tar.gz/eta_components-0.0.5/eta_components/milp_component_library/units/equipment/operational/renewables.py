from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, ClassVar

from pyomo import environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational

if TYPE_CHECKING:
    from eta_components.milp_component_library.environments import DryAir, SolarIrradiance
    from eta_components.milp_component_library.networks import DirectCurrent, Electrical, Hydrogen, _ThermalFluid
    from eta_components.milp_component_library.systems import _BaseSystem


class Photovoltaic(BaseOperational):
    """Converter model for photovoltaics"""

    _param_names: ClassVar[list[str]] = [
        "P_out_nom",
    ]
    _optional_params: ClassVar[dict[str, float]] = {
        "T_coefficient": -0.0045,
        "T_module_st": 25 + 273.15,
        "solar_irradiance_st": 1,  # 1 kW/m2
        "maintenance_cost": 0,
    }

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: DirectCurrent,
        ambient_environment: DryAir,
        solar_irradiance: SolarIrradiance,
    ):
        """Constructor method

        The additional valid keys for the data argument are the following:
        - eta_th: The thermal efficiency under full load for converting the gas inlet to the thermal outlet. Indexed or
            scalar. Note that the electrical efficiency is calculated by eta_el = eta - eta_th.
        """
        self._electrical_net: DirectCurrent = electrical_network
        self._ambient_env: DryAir = ambient_environment
        self._solar_irradiance: SolarIrradiance = solar_irradiance
        super().__init__(name, data, system)
        self._check_air_temperature()

    def _check_air_temperature(self):
        for idx in itertools.product(*self._system.sets):
            temp = self._ambient_env.temp_db[idx]
            if pyo.value(1 + self.data["T_coefficient"] * (self.data["T_module_st"] - temp)) < 0:
                raise ValueError(
                    f"The ambient temperature for photovoltaics {self.name} for index {idx} is too low with "
                    f"{temp - 273.15}°C, making the model unsolvable. Choose a lower ambient temperature."
                )

    def _register_at_networks(self):
        self._electrical_net.register_unit(self, self.p_el_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._electrical_net.unregister_unit(self)

    def _init_params(self):
        self.model.p_out_nom = self._create_scalar_param(self._data["P_out_nom"])
        self.model.temp_coefficient = self._create_scalar_param(self._data["T_coefficient"])
        self.model.temp_module_st = self._create_scalar_param(self._data["T_module_st"])
        self.model.solar_irradiance_st = self._create_scalar_param(self._data["solar_irradiance_st"])
        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.maintenance_cost = self._create_indexed_param(
            self._data["maintenance_cost"], sets=self._system.years_set
        )
        self.model.onetime_cost = self._create_scalar_param(0)
        self.model.emissions = self._create_indexed_param(0)

    def _reinitialize_params(self):
        self._update_param(self.model.p_out_nom, self._data["P_out_nom"])
        self._update_param(self.model.temp_coefficient, self._data["T_coefficient"])
        self._update_param(self.model.temp_module_st, self._data["T_module_st"])
        self._update_param(self.model.solar_irradiance_st, self._data["solar_irradiance_st"])
        self._update_param(self.model.maintenance_cost, self._data["maintenance_cost"])

    def _init_variables(self):
        self.model.x = pyo.Var(*self._system.sets, within=pyo.Binary)
        self.model.p_out = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_expressions(self):
        def plr_max(m, *idx: int):
            g_quotient = self._solar_irradiance.solar_irradiance[idx] / m.solar_irradiance_st
            temp_difference = self._ambient_env.temp_db[idx] - m.temp_module_st
            return g_quotient * (1 + m.temp_coefficient * temp_difference)

        self.model.specific_power_max = pyo.Expression(*self._system.sets, rule=plr_max)

    def _init_constraints(self):
        def limit_p_el_out(m, *idx: int):
            return m.p_out[idx] <= m.specific_power_max[idx] * m.p_out_nom * m.x[idx]

        self.model.limit_p_el_out = pyo.Constraint(*self._system.sets, rule=limit_p_el_out)

    def update_data(self, new_data: dict):
        super().update_data(new_data)
        self._check_air_temperature()

    @property
    def p_el_out(self) -> pyo.Expression:
        """The electrical input capacity."""
        return self._p_out


class Electrolyzer(BaseOperational):
    """Converter model for an electrolyzer.

    The electrolyzer transforms an input electrical power to an output hydrogen fuel power by using the standard
    converter model. During this process it also generates usable waste heat. The amount of waste heat is defined by
    the additional parameter 'eta_waste_heat' during initialization.

    P_waste_heat <= eta_waste_heat * (P_electrical - P_hydrogen)

    The waste heat can be utilized to its maximum. If it is not fully utilized, it is dissipated into the environment.
    """

    _optional_params: ClassVar[dict[str, float]] = dict(
        BaseOperational._optional_params,
        **{
            "eta_waste_heat": 0,
        },
    )

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        electrical_network: Electrical,
        waste_heat_network: _ThermalFluid,
        hydrogen_network: Hydrogen,
    ):
        """Constructor method.

        Extends the base method by allowing more properties to be passed in the data argument and requiring a network
        to connect the waste heat output to.

        The additional valid keys for the data argument are the following.
        - eta_waste_heat: The efficiency of the maximum usable waste heat,
            defined by P_waste_heat <= eta_waste_heat * (P_el - P_hydrogen). Scalar or indexed, defaults to 0.
        """
        self._electrical_net: Electrical = electrical_network
        self._hydrogen_network: Hydrogen = hydrogen_network
        self._waste_heat_network: _ThermalFluid = waste_heat_network

        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._electrical_net.register_unit(self, self.p_el_in, PowerSign.NEGATIVE)
        self._hydrogen_network.register_unit(self, self.p_hydrogen_out, PowerSign.POSITIVE)
        self._waste_heat_network.register_unit(self, self.p_waste_heat_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._electrical_net.unregister_unit(self)
        self._hydrogen_network.unregister_unit(self)
        self._waste_heat_network.unregister_unit(self)

    def _init_params(self):
        super()._init_params()
        self.model.eta_waste_heat = self._create_indexed_param(self.data["eta_waste_heat"])

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.eta_waste_heat, self.data["eta_waste_heat"])

    def _init_variables(self):
        super()._init_variables()
        self.model.p_waste_heat_out = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_constraints(self):
        super()._init_constraints()

        def limit_waste_heat(m, *idx: int):
            return m.p_waste_heat_out[idx] <= m.eta_waste_heat[idx] * (
                -1 * self.p_el_in[idx] - self.p_hydrogen_out[idx]
            )

        self.model.limit_waste_heat = pyo.Constraint(*self._system.sets, rule=limit_waste_heat)

    @property
    def p_el_in(self) -> pyo.Expression:
        """The electric input capacity."""
        return self._p_in

    @property
    def p_hydrogen_out(self) -> pyo.Expression:
        """The hydrogen output capacity."""
        return self._p_out

    @property
    def p_waste_heat_out(self) -> pyo.Expression:
        """The waste heat output capacity."""
        return self._model.p_waste_heat_out
