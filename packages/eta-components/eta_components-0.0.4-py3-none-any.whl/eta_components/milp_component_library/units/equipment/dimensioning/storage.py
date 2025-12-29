from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

import pyomo.environ as pyo

from eta_components.milp_component_library.exceptions import InvalidParameterValueError, InvalidPwlfValuesError
from eta_components.milp_component_library.units.equipment.base_equipment import BaseHeatStorage, BaseStorage

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import _BaseNetwork
    from eta_components.milp_component_library.systems import _BaseSystem


class BaseDimensioningStorage(BaseStorage, ABC):
    """Dimensioning converters are equipment which convert certain energy inputs into one or multiple energy outputs.
    They have one or multiple degrees of freedom regarding their energy input and output and also have a variable
    nominal power and investment cost. Simple Dimensioning Converters do not have a part load efficiency.

        \bParameters:
            E_nom_lb, The minimum permissible nominal energy capacity,
            E_nom_ub, The maximum permissible nominal energy capacity,
            c_in_max, Relative charge rate limit,
            c_out_max, Relative discharge rate limit,
            loss, Constant loss to the environment,
            eta[], The efficiency,
            delta_t, Time step length,
            bigM, Large value,
            I_B, The reference investment cost,
            K, The investment exponent,
            E_nom_support, The supporting points for the piecewise linearization of the investment curve. Must be
                within the minimum and maximum nominal energy capacity.
        Variables:
            I_N, NonNegativeReal, The investment cost,
            E_nom, NonNegativeReal, Nominal energy capacity,
            E[], NonNegativeReal, Current energy capacity,
            P_out[], NonNegativeReal, The discharge power,
            P_in[], NonPositiveReal, The charge power
            y, Binary, Investment decision,
            x[], Binary, Discharge decision, 0 if charging,
            xi[], NonNegativeReal, Helper for Glover's reformulation of bilinear term.
        Constraints:
            0 <= P_out[] <= E_nom * c_out_max
            P_out[] <= E_nom_ub * c_out_max * x[]
            -E_nom * c_in_max <= P_in[] <= 0
            -E_nom_ub * c_in_max * (1-x[]) <= P_in[]
            0 <= E[] <= E_nom
            E_nom_lb * y <= E_nom <= E_nom_ub * y
            E[t] = E[t-1] * (1 - loss*delta_t) + eta[t] * P_in[t] - 1/eta[t] * P_out[t]
            I_N = I_ref * E_nom^K, linearized at the supporting points E_nom_support.
    """

    _has_investment_decision = True
    _param_names: ClassVar[list[str]] = ["eta", "c_in_max", "c_out_max", "loss", "I_B", "K", "E_nom_support"]
    _optional_params: ClassVar[dict[str, float]] = {
        **BaseStorage._optional_params,
        "plr_min": 0.0,
        "maintenance_factor": 0.0,
    }

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method.

        Extends the base method by allowing more properties to be passed in the data argument and requiring a network
        which the storage is connected to.

        The valid keys for the data argument are the following. If indexed properties are passed, the keys must follow
        the scheme of the sets stored in the system.
        - eta: The charge and discharge loss.
        - c_in_max: The maximum specific charge rate in reference to the nominal energy capacity. Scalar.
        - c_in_max: The maximum specific discharge rate in reference to the nominal energy capacity. Scalar.
        - loss: The specific energy loss to the environment over time in relation to the nominal energy capacity.
            Scalar.
        - I_B: The reference investment cost. Scalar.
        - K: The investment cost exponent. Scalar.
        - E_nom_support: The supporting points of the nominal capacity for the piecewise linearization of the
            investment curve. The first and the last entry are interpreted as the minimum and maximum nominal energy
            capacity, if the unit is bought. Sequence.
        """
        super().__init__(name, data, system, network=network)

    def _init_params(self):
        super()._init_params()
        self.model.p_out_nom_min = self._create_scalar_param(self._data["E_nom_support"][0])
        self.model.p_out_nom_max = self._create_scalar_param(self._data["E_nom_support"][-1])
        self.model.maintenance_factor = self._create_indexed_param(
            self._data["maintenance_factor"], sets=self._system.years_set
        )

    def _reinitialize_params(self):
        super()._reinitialize_params()

    def _init_variables(self):
        """Initializes the variables."""
        self.model.y = pyo.Var(within=pyo.Binary)
        if not self._data["allow_simultaneous_charging_and_discharging"]:
            self.model.x = pyo.Var(*self._system.sets, within=pyo.Binary)

        self.model.p_out_nom = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, self._data["E_nom_support"][-1]))
        self.model.e = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)
        self.model.p_in = pyo.Var(*self._system.sets, within=pyo.NonPositiveReals)
        self.model.p_out = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)
        self.model.investment_cost = pyo.Var(within=pyo.NonNegativeReals)

    def _init_expressions(self):
        def maintenance_cost(m, year):
            return m.maintenance_factor[year] * m.investment_cost

        self.model.maintenance_cost = pyo.Expression(self._system.years_set, rule=maintenance_cost)

    def _init_constraints(self):
        def limit_p_out(m, *idx: int):
            return m.p_out[idx] <= m.p_out_nom * m.c_out_max

        self.model.limit_p_out = pyo.Constraint(*self._system.sets, rule=limit_p_out)

        def limit_p_in(m, *idx: int):
            return -m.p_out_nom * m.c_in_max <= m.p_in[idx]

        self.model.limit_p_in = pyo.Constraint(*self._system.sets, rule=limit_p_in)

        if not self._data["allow_simultaneous_charging_and_discharging"]:

            def force_p_out_zero_if_not_operating(m, *idx: int):
                return m.p_out[idx] <= m.p_out_nom_max * m.c_out_max * m.x[idx]

            self.model.force_p_out_zero_if_not_operating = pyo.Constraint(
                *self._system.sets, rule=force_p_out_zero_if_not_operating
            )

            def force_p_in_zero_if_operating(m, *idx: int):
                return -m.p_out_nom_max * m.c_in_max * (1 - m.x[idx]) <= m.p_in[idx]

            self.model.force_p_in_zero_if_not_operating = pyo.Constraint(
                *self._system.sets, rule=force_p_in_zero_if_operating
            )

        def limit_e(m, *idx: int):
            return m.e[idx] <= m.p_out_nom

        self.model.limit_e = pyo.Constraint(*self._system.sets, rule=limit_e)

        def limit_e_nom_lb(m):
            return m.p_out_nom_min * m.y <= m.p_out_nom

        self.model.limit_e_nom_lb = pyo.Constraint(rule=limit_e_nom_lb)

        def limit_e_nom_ub(m):
            return m.p_out_nom <= m.p_out_nom_max * m.y

        self.model.limit_e_nom_ub = pyo.Constraint(rule=limit_e_nom_ub)

        self.model.energy_balance = pyo.Constraint(*self._system.sets, rule=self._energy_balance())

        self.model.investment_curve = self._rule_investment_curve(self._data["E_nom_support"])

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
                f"The sequence of support points for the investment curve must be strictly "
                f"increasing. Was {support_pts}."
            )

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


class HeatStorage(BaseHeatStorage, BaseDimensioningStorage):
    """Converter model for a thermal heat storage. Refer to the base class for implementation details."""
