from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.units.equipment.base_equipment import (
    BaseCounterFlowHeatExchanger,
    BaseHeatExchanger,
    BaseParallelFlowHeatExchanger,
)
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import _ThermalFluid
    from eta_components.milp_component_library.systems import _BaseSystem


class BaseOperationalHeatExchanger(BaseHeatExchanger, BaseOperational, ABC):
    """Converter model for a heat exchanger.

    The heat exchanger is assumed to be adiabatic and thus the efficiency is always equal to 1. The model is the
    following:
        \bParameters:
            P_nom_out, Area of the heat exchanger,
            plr_min, Minimum part load ratio
            lmtd[], Logarithmic mean temperature difference,
            heat_transfer_coeff, Heat transfer coefficient,
        Variables:
            y   Binary, buying decision,
            x[] Binary, operating decision,
            plr[]   NonNegativeReal, Part load ratio,
        Expressions:
            P_out[] = plr[] * lmtd[] * heat_transfer_coeff * P_nom_out
            P_in[] = - P_out[]
        Constraints:
            x[] <= y    Unit must be bought to operate
            x[] * plr_min <= plr[] <= x[]   Part load ratio must be within [plr_min, 1] or 0
    """

    _param_names: ClassVar[list[str]] = [
        *BaseHeatExchanger._param_names,
        "area",
        "heat_transfer_coefficient",
    ]
    _optional_params: ClassVar[dict[str, float]] = {
        **BaseHeatExchanger._optional_params,
        "maintenance_cost": 0.0,
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

        Replaces the allowed parameter names of the base class with the following.
        - area: The surface area of the heat exchanger in m2. Scalar.
        - plr_min: The minimum possible part load ratio. Scalar.
            Warning: Setting the minimum part load ratio to zero can result in numerical inaccuracies. The solver will
                allow plr to be -10^-12, as it is close to zero. However, for very large P_out_nom values, this will
                result in a reversed energy flow, making P_in positive and P_out negative. It is better to set the
                minimum part load ratio to a small value such as 0.0001.
        - heat_transfer_coefficient: The heat transfer coefficient of the heat exchanger in W/K*m2. Scalar.
        """
        super().__init__(name, data, system, hot_network=hot_network, cold_network=cold_network)

    def _init_params(self):
        """Initializes the parameters. Extends the base method by setting the heat transfer coefficient and also
        calculating the log mean temperature difference within the heat exchanger.
        """
        self._recast_names_to_standard_model()
        super()._init_params()
        self.model.heat_transfer_coefficient = self._create_scalar_param(self._data["heat_transfer_coefficient"])
        self.model.lmtd = self._create_indexed_param(self._log_mean_temp_diff())

    def _recast_names_to_standard_model(self):
        """The heat exchanger model uses different parameter names than the standard model. In order to use the
        standard model, this method adds the parameters P_out_nom, eta and pfr_plr_bpts to the data attribute.
        It uses the values of area, heat_transfer_coefficient and ((plr_min, plr_min), (1, 1)).
        """
        self._data["P_out_nom"] = self._data["area"]
        self._data["pfr_plr_bpts"] = ((self._data["plr_min"], self._data["plr_min"]), (1, 1))

    def _reinitialize_params(self):
        self._recast_names_to_standard_model()
        super()._reinitialize_params()
        self._update_param(self.model.heat_transfer_coefficient, self._data["heat_transfer_coefficient"])
        self._update_param(self.model.lmtd, self._log_mean_temp_diff())

    @staticmethod
    def _rule_p_in(m: pyo.Model, *idx: int) -> pyo.Expression:
        return -1 * m.p_out[idx] / m.eta[idx]

    @staticmethod
    def _rule_p_out(m: pyo.Model, *idx: int) -> pyo.Expression:
        return m.p_out_nom * m.heat_transfer_coefficient * m.lmtd[idx] * m.plr[idx]


class ParallelFlowHeatExchanger(BaseOperationalHeatExchanger, BaseParallelFlowHeatExchanger):
    """Converter model for a parallel flow heat exchanger. Refer to the base class for implementation details.

    Taken from Baumgärtner (2020): "Optimization of low-carbon energy systems from industrial to national scale" from
    p. 128 ff. and p. 135 f.
    """


class CounterFlowHeatExchanger(BaseOperationalHeatExchanger, BaseCounterFlowHeatExchanger):
    """Converter model for a counter-current flow heat exchanger. Refer to the base class for implementation details.

    Taken from Baumgärtner (2020): "Optimization of low-carbon energy systems from industrial to national scale" from
    p. 128 ff. and p. 135 f.
    """


class HeatTransfer(BaseOperational):
    _param_names: ClassVar[list] = []
    _optional_params: ClassVar[dict] = {}
    _forbidden_updates: ClassVar[dict] = {}

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        from_network: _ThermalFluid,
        to_network: _ThermalFluid,
    ):
        self._from_network = from_network
        self._to_network = to_network
        super().__init__(name, data, system)

    def _register_at_networks(self):
        from eta_components.milp_component_library.networks import PowerSign

        self._from_network.register_unit(self, self.p_in, PowerSign.NEGATIVE)
        self._to_network.register_unit(self, self.p_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._from_network.unregister_unit(self)
        self._to_network.unregister_unit(self)

    def _init_params(self):
        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.maintenance_cost = self._create_indexed_param(0, sets=self._system.years_set)
        self.model.onetime_cost = self._create_scalar_param(0)
        self.model.emissions = self._create_indexed_param(0)

    def _reinitialize_params(self):
        return

    def _init_variables(self):
        self.model.amount = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_expressions(self):
        self.model.p_out = pyo.Expression(*self._system.sets, rule=self._rule_p_out)
        self.model.p_in = pyo.Expression(*self._system.sets, rule=self._rule_p_in)

    @staticmethod
    def _rule_p_out(m: pyo.Model, *idx: int) -> pyo.Expression:
        return m.amount[idx]

    @staticmethod
    def _rule_p_in(m: pyo.Model, *idx: int) -> pyo.Expression:
        return -1 * m.p_out[idx]

    def _init_constraints(self):
        return

    @property
    def p_in(self) -> pyo.Expression:
        """The thermal input capacity."""
        return self.model.p_in

    @property
    def p_out(self) -> pyo.Expression:
        """The thermal output capacity."""
        return self.model.p_out
