from __future__ import annotations

from typing import TYPE_CHECKING

from pyomo import environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import AlternatingCurrent, DirectCurrent
    from eta_components.milp_component_library.systems import _BaseSystem


class Inverter(BaseOperational):
    """Converter model for an inverter.

    Allows for the bidirectional conversion of alternating to direct current and vice versa. The conversion is only
    possible in one direction for every time step. The conversion is affected by the conversion efficiency and the
    part load ratio. The equations governing the inverter's behavior are:

    P_*_out[] = P_out_nom * plr_*[]
    P_*_in[] = -P_out_nom/eta[] * pfr_*[]
    plr_ac[] = pwlf(pfr_dc[])
    plr_dc[] = pwlf(pfr_ac[])

    Only either plr_ac or plr_dc can be larger than zero for any time step.
    """

    def __init__(
        self,
        name: str,
        data: dict,
        system: _BaseSystem,
        *,
        alternating_current_network: AlternatingCurrent,
        direct_current_network: DirectCurrent,
    ):
        """Constructor method.

        Extends the base method by requiring an alternating and a direct current network to connect the inverter to.
        """
        self._ac_net: AlternatingCurrent = alternating_current_network
        self._dc_net: DirectCurrent = direct_current_network

        super().__init__(name, data, system)

    def _register_at_networks(self):
        self._ac_net.register_unit(self, self.p_ac_in, PowerSign.NEGATIVE)
        self._ac_net.register_unit(self, self.p_ac_out, PowerSign.POSITIVE)
        self._dc_net.register_unit(self, self.p_dc_in, PowerSign.NEGATIVE)
        self._dc_net.register_unit(self, self.p_dc_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._ac_net.unregister_unit(self)
        self._dc_net.unregister_unit(self)

    def _init_variables(self):
        self.model.x = pyo.Var(*self._system.sets, within=pyo.Binary)
        self.model.el_flowing_from_dc_to_ac = pyo.Var(*self._system.sets, within=pyo.Binary)
        self.model.plr_ac = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals, bounds=(0, 1))
        self.model.plr_dc = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals, bounds=(0, 1))
        self.model.pfr_ac = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)
        self.model.pfr_dc = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_expressions(self):
        def p_ac_in(m: pyo.Model, *idx: int) -> pyo.Expression:
            return -1 * m.p_out_nom / m.eta[idx] * m.pfr_ac[idx]

        def p_dc_in(m: pyo.Model, *idx: int) -> pyo.Expression:
            return -1 * m.p_out_nom / m.eta[idx] * m.pfr_dc[idx]

        def p_out_ac(m: pyo.Model, *idx: int) -> pyo.Expression:
            return m.p_out_nom * m.plr_ac[idx]

        def p_out_dc(m: pyo.Model, *idx: int) -> pyo.Expression:
            return m.p_out_nom * m.plr_dc[idx]

        self.model.p_ac_in = pyo.Expression(*self._system.sets, rule=p_ac_in)
        self.model.p_dc_in = pyo.Expression(*self._system.sets, rule=p_dc_in)
        self.model.p_ac_out = pyo.Expression(*self._system.sets, rule=p_out_ac)
        self.model.p_dc_out = pyo.Expression(*self._system.sets, rule=p_out_dc)

    def _init_constraints(self):
        self.model.plr_pfr_ac_to_dc = self._rule_pfr_plr(pfr_var=self.model.pfr_ac, plr_var=self.model.plr_dc)
        self.model.plr_pfr_dc_to_ac = self._rule_pfr_plr(pfr_var=self.model.pfr_dc, plr_var=self.model.plr_ac)

        def plr_lb_dc_to_ac(m, *idx: int):
            return m.el_flowing_from_dc_to_ac[idx] * m.plr_min <= m.plr_ac[idx]

        self.model.plr_lb_dc_to_ac = pyo.Constraint(*self._system.sets, rule=plr_lb_dc_to_ac)

        def plr_ub_dc_to_ac(m, *idx: int):
            return m.plr_ac[idx] <= m.el_flowing_from_dc_to_ac[idx]

        self.model.plr_ub_dc_to_ac = pyo.Constraint(*self._system.sets, rule=plr_ub_dc_to_ac)

        def plr_lb_ac_to_dc(m, *idx: int):
            return (1 - m.el_flowing_from_dc_to_ac[idx]) * m.plr_min <= m.plr_dc[idx]

        self.model.plr_lb_ac_to_dc = pyo.Constraint(*self._system.sets, rule=plr_lb_ac_to_dc)

        def plr_ub_ac_to_dc(m, *idx: int):
            return m.plr_dc[idx] <= (1 - m.el_flowing_from_dc_to_ac[idx])

        self.model.plr_ub_ac_to_dc = pyo.Constraint(*self._system.sets, rule=plr_ub_ac_to_dc)

        def shutoff_ac_to_dc(m, *idx: int):
            return m.plr_dc[idx] <= m.x[idx]

        self.model.shutoff_ac_to_dc = pyo.Constraint(*self._system.sets, rule=shutoff_ac_to_dc)

        def shutoff_dc_to_ac(m, *idx: int):
            return m.plr_ac[idx] <= m.x[idx]

        self.model.shutoff_dc_to_ac = pyo.Constraint(*self._system.sets, rule=shutoff_dc_to_ac)

    @property
    def p_ac_in(self) -> pyo.Expression:
        """The alternating current input capacity."""
        return self.model.p_ac_in

    @property
    def p_ac_out(self) -> pyo.Expression:
        """The alternating current output capacity."""
        return self.model.p_ac_out

    @property
    def p_dc_in(self) -> pyo.Expression:
        """The direct current input capacity."""
        return self.model.p_dc_in

    @property
    def p_dc_out(self) -> pyo.Expression:
        """The direct current output capacity."""
        return self.model.p_dc_out
