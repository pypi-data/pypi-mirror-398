from __future__ import annotations

from abc import ABC
from typing import ClassVar

import numpy as np
import pyomo.environ as pyo

from eta_components.milp_component_library.exceptions import InvalidPwlfValuesError
from eta_components.milp_component_library.units.equipment.base_equipment import BaseConverter


class BaseOperational(BaseConverter, ABC):
    """Operational converters are equipment which convert certain energy inputs into one or multiple energy outputs.
    They have one or multiple degrees of freedom regarding their energy input and output but have a fixed nominal
    output and buying decision.

        \bParameters:
            P_nom_out,
            eta[],
            plr_min,
        Variables:
            x[] Binary, operating decision,
            plr[]   NonNegativeReal, Part load ratio,
            pfr[]   NonNegativeReal, Power factor ratio,
        Expressions:
            P_out[] = plr[] * P_nom_out
            P_in[] = - pfr[] / eta[] * P_nom_out
        Constraints:
            x[] * plr_min <= plr[] <= x[]   Part load ratio must be within [plr_min, 1] or 0
            pfr[] == pwlf(plr[])    Piecewise linear function
    """

    _param_names: ClassVar[list[str]] = [
        "P_out_nom",
        "eta",
    ]
    _optional_params: ClassVar[dict[str, object]] = {
        "pfr_plr_bpts": ((0, 0), (1, 1)),
        "maintenance_cost": 0,
    }
    _forbidden_updates: ClassVar[list[str]] = [*BaseConverter._forbidden_updates, "pfr_plr_bpts"]

    def _init_params(self):
        self.model.p_out_nom = self._create_scalar_param(self._data["P_out_nom"])
        self.model.plr_min = self._create_scalar_param(self._data["pfr_plr_bpts"][0][1])
        self.model.eta = self._create_indexed_param(self._data["eta"])
        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.maintenance_cost = self._create_indexed_param(
            self._data["maintenance_cost"], sets=self._system.years_set
        )
        self.model.onetime_cost = self._create_scalar_param(0)
        self.model.emissions = self._create_indexed_param(0)

    def _reinitialize_params(self):
        self._update_param(self.model.p_out_nom, self._data["P_out_nom"])
        self._update_param(self.model.eta, self._data["eta"])
        self._update_param(self.model.maintenance_cost, self._data["maintenance_cost"])

    def _init_variables(self):
        self.model.x = pyo.Var(*self._system.sets, within=pyo.Binary)
        self.model.plr = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals, bounds=(0, 1))
        self.model.pfr = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_expressions(self):
        self.model.p_out = pyo.Expression(*self._system.sets, rule=self._rule_p_out)
        self.model.p_in = pyo.Expression(*self._system.sets, rule=self._rule_p_in)

    @staticmethod
    def _rule_p_in(m: pyo.Model, *idx: int) -> pyo.Expression:
        """Rule for generating an expression for the input capacity."""
        return -1 * m.p_out_nom / m.eta[idx] * m.pfr[idx]

    @staticmethod
    def _rule_p_out(m: pyo.Model, *idx: int) -> pyo.Expression:
        """Rule for generating an expression for the output capacity."""
        return m.p_out_nom * m.plr[idx]

    def _init_constraints(self):
        self.model.plr_pfr = self._rule_pfr_plr()

        def x_plr_lb(m, *idx: int):
            return m.x[idx] * m.plr_min <= m.plr[idx]

        self.model.x_plr_lb = pyo.Constraint(*self._system.sets, rule=x_plr_lb)

        def x_plr_ub(m, *idx: int):
            return m.plr[idx] <= m.x[idx]

        self.model.x_plr_ub = pyo.Constraint(*self._system.sets, rule=x_plr_ub)

    def _rule_pfr_plr(self, pfr_var: pyo.Var = None, plr_var: pyo.Var = None) -> pyo.Constraint | pyo.Piecewise:
        """Rule for building a linear or piecewise linear constraint between the power factor ratio and part load ratio.

        If the power factor efficiency ana the part load efficiency is the same, it returns a Constraint forcing
        equality between pfr and plr. Otherwise, a piecewise linear constraint is constructed and returned.
        First, the supplied breakpoints are taken from the instance attributes. If the lowest plr value is above 0,
        the list of pfr-plr-pairs is extended to cover the entire domain [0, 1] for the part load ratio, otherwise
        Pyomo will throw warnings. Afterwards, the list of breakpoints is used to construct the constraint.
        """
        if plr_var is None:
            plr_var = self.model.plr
        if pfr_var is None:
            pfr_var = self.model.pfr

        self._check_pfr_plr_bpts()
        pfr_plr_bpts = list(self._data["pfr_plr_bpts"])

        if self._pfr_is_equal_plr_efficiency():

            def pfr_equal_plr(m, *idx: int):
                return pfr_var[idx] == plr_var[idx]

            pwlf = pyo.Constraint(*self._system.sets, rule=pfr_equal_plr)
        else:
            if self.model.plr_min.value > 0:
                self._extend_pfr_plr_bpts(pfr_plr_bpts)
            pfr_bpts, plr_bpts = [val[0] for val in pfr_plr_bpts], [val[1] for val in pfr_plr_bpts]
            pwlf = pyo.Piecewise(
                *self._system.sets,
                pfr_var,
                plr_var,
                pw_pts=plr_bpts,
                f_rule=pfr_bpts,
                pw_constr_type="EQ",
            )
        return pwlf

    def _check_pfr_plr_bpts(self):
        pfr_plr_bpts = list(self._data["pfr_plr_bpts"])
        if not pfr_plr_bpts[-1][1] == 1:
            raise InvalidPwlfValuesError(f"Last plr-value in pfr_plr_bpts must be 1, was {pfr_plr_bpts[-1][1]}.")
        if (np.array(pfr_plr_bpts) < 0).any():
            raise InvalidPwlfValuesError(f"All pfr-plr-values must be non-negative, was {pfr_plr_bpts}.")

    def _pfr_is_equal_plr_efficiency(self) -> bool:
        """Checks if the efficiency for the power factor ratio and part load ratio is the same for all breakpoints."""
        return all((np.isclose(pfr, plr) for pfr, plr in self._data["pfr_plr_bpts"]))

    def _extend_pfr_plr_bpts(self, pfr_plr_bpts: list[tuple[float, float]]):
        """Extend the pfr_plr_pairs to plr=0. The scheme used for this is the following:
        [(0.3, 0.2), (1, 1)] --> [(0, 0), (0, 0.2*eps), (0.3, 0.2), (1, 1)].
        """
        eps = 0.99
        first = (0, 0)
        second = (0, pyo.value(self.model.plr_min) * eps)
        pfr_plr_bpts.insert(0, first)
        pfr_plr_bpts.insert(1, second)

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
        return self.model.onetime_cost

    @property
    def emissions(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The emissions of the unit per step length indexed over the years, periods and time steps."""
        return self.model.emissions
