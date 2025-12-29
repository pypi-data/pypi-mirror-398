from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.exceptions import InvalidParameterValueError, InvalidPwlfValuesError
from eta_components.milp_component_library.units.equipment.base_equipment import BaseConverter


class BaseDimensioning(BaseConverter, ABC):
    """Dimensioning converters are equipment which convert certain energy inputs into one or multiple energy outputs.
    They have one or multiple degrees of freedom regarding their energy input and output and also have a variable
    nominal power and investment cost. The efficiency of Dimensioning Converters does not change under part load.

    The generic model is the following and might be changed in subclasses. It was taken from Baumgärtner (2020):
    "Optimization of low-carbon energy systems from industrial to national scale" from p. 128 ff.

        \bParameters:
            P_nom_out_min, The minimum permissible nominal input power,
            P_nom_out_max, The maximum permissible nominal output power,
            eta[], The efficiency,
            plr_min, The minimum permissible part load ratio,
            I_B, The reference investment cost,
            K, The investment exponent,
            P_out_nom_support, The supporting points for the piecewise linearization of the investment curve. Must be
                within the maximum and minimum nominal output power.
        Variables:
            I_N, NonNegativeReal, The investment cost,
            P_nom_out, NonNegativeReal, Nominal output power,
            P_out[], NonNegativeReal, Output power,
            y, Binary, Investment decision,
            x[], Binary, Operating decision,
            xi[], NonNegativeReal, Helper for Glover's reformulation of bilinear term.
        Expressions:
            P_in[] = - P_out / eta[]
        Constraints:
            y * P_nom_out_min <= P_nom_out <= y * P_nom_out_max
            P_out[] <= P_nom_out,
            plr_min * xi[] <= P_out[] <= x * P_nom_out_max,
            P_nom_out - (1 - x[]) * P_nom_out_max <= xi[] <= P_nom_out,
            I_N = I_ref * P_out_nom^K, linearized at the supporting points P_out_nom_support.
    """

    _has_investment_decision = True
    _param_names: ClassVar[list[str]] = [
        "eta",
        "I_B",
        "K",
        "P_out_nom_support",
    ]
    _optional_params: ClassVar[dict[str, float]] = {
        "plr_min": 0.0,
        "maintenance_factor": 0.0,
    }
    _forbidden_updates: ClassVar[list[str]] = [*BaseConverter._forbidden_updates, "P_out_nom_support", "I_B", "K"]

    def _init_params(self):
        self.model.p_out_nom_min = self._create_scalar_param(self._data["P_out_nom_support"][0])
        self.model.p_out_nom_max = self._create_scalar_param(self._data["P_out_nom_support"][-1])
        self.model.plr_min = self._create_scalar_param(self._data["plr_min"])
        self.model.eta = self._create_indexed_param(self._data["eta"])
        self.model.maintenance_factor = self._create_indexed_param(
            self._data["maintenance_factor"], sets=self._system.years_set
        )
        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.emissions = self._create_indexed_param(0)

    def _reinitialize_params(self):
        self._update_param(self.model.plr_min, self._data["plr_min"])
        self._update_param(self.model.eta, self._data["eta"])
        self._update_param(self.model.maintenance_factor, self._data["maintenance_factor"])

    def _init_variables(self):
        self.model.y = pyo.Var(within=pyo.Binary)
        self.model.x = pyo.Var(*self._system.sets, within=pyo.Binary)
        self.model.p_out_nom = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, self._data["P_out_nom_support"][-1]))
        self.model.p_out = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)
        self.model.investment_cost = pyo.Var(within=pyo.NonNegativeReals)
        self.model.xi = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_expressions(self):
        self.model.p_in = pyo.Expression(*self._system.sets, rule=self._rule_p_in)

        def rule_maintenance_cost(m, year):
            return m.maintenance_factor[year] * m.investment_cost

        self.model.maintenance_cost = pyo.Expression(self._system.years_set, rule=rule_maintenance_cost)

    @staticmethod
    def _rule_p_in(m: pyo.Model, *idx: int) -> pyo.Expression:
        """Rule for generating an expression for the output capacity."""
        return -1 * m.p_out[idx] / m.eta[idx]

    def _init_constraints(self):
        def p_out_nom_min(m):
            return m.y * m.p_out_nom_min <= m.p_out_nom

        self.model.limit_p_out_nom_1 = pyo.Constraint(rule=p_out_nom_min)

        def p_out_nom_max(m):
            return m.p_out_nom <= m.y * m.p_out_nom_max

        self.model.limit_p_out_nom_2 = pyo.Constraint(rule=p_out_nom_max)

        def p_out_max(m, *idx: int):
            return m.p_out[idx] <= m.p_out_nom

        self.model.p_out_max = pyo.Constraint(*self._system.sets, rule=p_out_max)

        def force_p_out_zero(m, *idx: int):
            return m.p_out[idx] <= m.p_out_nom_max * m.x[idx]

        self.model.force_p_out_zero = pyo.Constraint(*self._system.sets, rule=force_p_out_zero)

        def force_plr_min(m, *idx: int):
            return m.plr_min * m.xi[idx] <= m.p_out[idx]

        self.model.force_plr_min = pyo.Constraint(*self._system.sets, rule=force_plr_min)

        def glover_reformulation_1(m, *idx: int):
            return m.p_out_nom - (1 - m.x[idx]) * m.p_out_nom_max <= m.xi[idx]

        def glover_reformulation_2(m, *idx: int):
            return m.xi[idx] <= m.p_out_nom

        self.model.glover_reformulation_1 = pyo.Constraint(*self._system.sets, rule=glover_reformulation_1)
        self.model.glover_reformulation_2 = pyo.Constraint(*self._system.sets, rule=glover_reformulation_2)

        self.model.investment_curve = self._rule_investment_curve(self._data["P_out_nom_support"])

    def _rule_investment_curve(self, support_pts: Sequence) -> pyo.Piecewise:
        self._check_investment_support_points(support_pts)
        pts = []
        if support_pts[0] > 0:
            eps = 0.99
            first = (0, 0)
            # This breakpoint must be a bit below the actual first bpt
            second = (0, support_pts[0] * eps)
            pts.insert(0, first)
            pts.insert(1, second)

        for p_support_i in support_pts:
            invest = self._data["I_B"] * (p_support_i ** self._data["K"])
            pts.append((invest, p_support_i))

        invest_bpts, p_bpts = [val[0] for val in pts], [val[1] for val in pts]
        return pyo.Piecewise(
            self.model.investment_cost,
            self.model.p_out_nom,
            pw_pts=p_bpts,
            f_rule=invest_bpts,
            pw_constr_type="EQ",
        )

    @staticmethod
    def _check_investment_support_points(support_pts: Sequence):
        if len(support_pts) < 2:
            raise InvalidParameterValueError(
                f"The number of support points for the investment curve must be at least two."
                f"{len(support_pts)} points were passed."
            )
        if not all(val_n < val_n_plus_1 for val_n, val_n_plus_1 in zip(support_pts, support_pts[1:])):
            raise InvalidPwlfValuesError(
                f"The sequence of support points for the investment curve must be strictly"
                f"increasing. Was {support_pts}."
            )

    @property
    def is_bought(self) -> pyo.Var:
        """The investment decision for the converter."""
        return self.model.y

    @property
    def _p_out_nom(self) -> pyo.Var:
        """The nominal output capacity of the converter."""
        return self.model.p_out_nom

    @property
    def time_step_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The operating cost of the unit per step length indexed over the years, periods and time steps."""
        return self.model.time_step_cost

    @property
    def annual_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The annual cost of the unit indexed over the years."""
        return self.model.maintenance_cost

    @property
    def onetime_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The capital cost of the unit."""
        return self.model.investment_cost

    @property
    def emissions(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The emissions of the unit per step length indexed over the years, periods and time steps."""
        return self.model.emissions
