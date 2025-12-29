from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.units.equipment.base_equipment import (
    BaseCounterFlowHeatExchanger,
    BaseHeatExchanger,
    BaseParallelFlowHeatExchanger,
)
from eta_components.milp_component_library.units.equipment.dimensioning.base_dimensioning import BaseDimensioning

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import _ThermalFluid
    from eta_components.milp_component_library.systems import _BaseSystem


class BaseDimensioningHeatExchanger(BaseHeatExchanger, BaseDimensioning, ABC):
    """Converter model for a heat exchanger."""

    _param_names: ClassVar[list[str]] = [
        *BaseHeatExchanger._param_names,
        "I_B",
        "K",
        "area_support",
    ]
    _optional_params: ClassVar[dict[str, float]] = {**BaseHeatExchanger._optional_params, "maintenance_factor": 0.0}

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
        standard model, this method adds the parameters P_out_nom_support and eta to the data attribute.
        It uses the values of area_support and heat_transfer_coefficient.
        """
        self._data["P_out_nom_support"] = self._data["area_support"]

    def _reinitialize_params(self):
        self._recast_names_to_standard_model()
        super()._reinitialize_params()
        self._update_param(self.model.heat_transfer_coefficient, self._data["heat_transfer_coefficient"])
        self._update_param(self.model.lmtd, self._log_mean_temp_diff())

    def _init_variables(self):
        """For the heat exchanger model p_out_nom is the area, p_out_nom_max and p_out_min are the maximum and minimum
        area, p_out is the thermal power and eta is the heat transfer coefficient.
        """
        self.model.y = pyo.Var(within=pyo.Binary)
        self.model.x = pyo.Var(*self._system.sets, within=pyo.Binary)
        self.model.p_out_nom = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, self.model.p_out_nom_max))
        self.model.p_out = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)
        self.model.investment_cost = pyo.Var(within=pyo.NonNegativeReals)
        self.model.xi = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_constraints(self):
        def area_min(m):
            return m.y * m.p_out_nom_min <= m.p_out_nom

        self.model.limit_area_min = pyo.Constraint(rule=area_min)

        def area_max(m):
            return m.p_out_nom <= m.y * m.p_out_nom_max

        self.model.limit_area_max = pyo.Constraint(rule=area_max)

        def p_out_max(m, *idx: int):
            return m.p_out[idx] <= m.p_out_nom * m.lmtd[idx] * m.heat_transfer_coefficient

        self.model.p_out_max = pyo.Constraint(*self._system.sets, rule=p_out_max)

        def force_p_out_zero(m, *idx: int):
            return m.p_out[idx] <= m.p_out_nom_max * m.lmtd[idx] * m.heat_transfer_coefficient * m.x[idx]

        self.model.force_p_out_zero = pyo.Constraint(*self._system.sets, rule=force_p_out_zero)

        def force_plr_min(m, *idx: int):
            return m.plr_min * m.xi[idx] * m.lmtd[idx] * m.heat_transfer_coefficient <= m.p_out[idx]

        self.model.force_plr_min = pyo.Constraint(*self._system.sets, rule=force_plr_min)

        def glover_reformulation_1(m, *idx: int):
            return m.p_out_nom - (1 - m.x[idx]) * m.p_out_nom_max <= m.xi[idx]

        def glover_reformulation_2(m, *idx: int):
            return m.xi[idx] <= m.p_out_nom

        self.model.glover_reformulation_1 = pyo.Constraint(*self._system.sets, rule=glover_reformulation_1)
        self.model.glover_reformulation_2 = pyo.Constraint(*self._system.sets, rule=glover_reformulation_2)

        self.model.investment_curve = self._rule_investment_curve(self._data["area_support"])


class ParallelFlowHeatExchanger(BaseDimensioningHeatExchanger, BaseParallelFlowHeatExchanger):
    """Converter model for a parallel flow heat exchanger. Refer to the base class for implementation details."""


class CounterFlowHeatExchanger(BaseDimensioningHeatExchanger, BaseCounterFlowHeatExchanger):
    """Converter model for a counter flow heat exchanger. Refer to the base class for implementation details."""
