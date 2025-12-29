from __future__ import annotations

import operator
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

import numpy as np
from pydantic.fields import ModelPrivateAttr, PydanticUndefined
from pyomo import environ as pyo

from eta_components.milp_component_library.networks import PowerSign
from eta_components.milp_component_library.units.base_unit import BaseStandaloneUnit

if TYPE_CHECKING:
    from eta_components.milp_component_library.networks import CoolingFluid, Electrical, HeatingFluid, _BaseNetwork
    from eta_components.milp_component_library.systems import _BaseSystem


class _BaseSourceSink(BaseStandaloneUnit, ABC):
    """Sources and sinks are equipment which produce or consume capacities without a conversion process. The amounts
    can either be fixed (parameterized) or variable.
    """

    _sign_of_capacity = None

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method."""
        self._net: _BaseNetwork = network
        super().__init__(name, data, system)

    def _validate_capacity(self, capacity: float | dict):
        sign = getattr(type(self), "_sign_of_capacity", None)

        # Pydantic v2 may turn leading-underscore attrs into ModelPrivateAttr
        if isinstance(sign, ModelPrivateAttr):
            sign = sign.get_default()

        if sign in (None, PydanticUndefined):
            return

        if isinstance(capacity, (int, float)):
            capacity = {None: capacity}

        if not all(sign(val, 0) for val in capacity.values()):
            warnings.warn(
                f"Not all values for {self.name} are {getattr(sign, '__name__', str(sign))} than 0. Check your "
                f"input data again. Note that a positive sign means that the unit is putting that energy "
                f"into the networks whereas a negative sign means it is pulling that energy out of the "
                f"network. This means that e.g. cooling suppliers have a negative sign as they are pulling "
                f"heat out of the network.",
                stacklevel=2,
            )

    def _init_params(self):
        self.model.time_step_cost = self._create_indexed_param(0)
        self.model.annual_cost = self._create_indexed_param(0, sets=self._system.years_set)
        self.model.onetime_cost = self._create_scalar_param(0)
        self.model.emissions = self._create_indexed_param(0)

    def _reinitialize_params(self):
        return

    def _init_variables(self):
        pass

    def _init_expressions(self):
        pass

    def _init_constraints(self):
        pass

    @property
    def time_step_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The operating cost of the unit per step length indexed over the years, periods and time steps."""
        return self.model.time_step_cost

    @property
    def annual_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The annual cost of the unit indexed over the years."""
        return self.model.annual_cost

    @property
    def onetime_cost(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The capital cost of the unit."""
        return self.model.onetime_cost

    @property
    def emissions(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The emissions of the unit per step length indexed over the years, periods and time steps."""
        return self.model.emissions


class _BaseSource(_BaseSourceSink, ABC):
    """Sources are equipment which produce a fixed or variable capacity without a conversion process."""

    @property
    @abstractmethod
    def _p_out(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The output capacity."""


class _SimpleSource(_BaseSource, ABC):
    """Simple sources are equipment which produce a fixed capacity without a conversion process."""

    _sign_of_capacity = operator.ge

    _param_names: ClassVar[list[str]] = [*_BaseSource._param_names, "P_out"]

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method.

        Extends the base method by allowing more properties to be passed in the data argument.

        The additional valid keys for the data argument are the following:
        - P_out: The capacity production, must be non-negative. Scalar or indexed.
        """
        super().__init__(name, data, system, network=network)
        self._validate_capacity(self.data["P_out"])

    def _init_params(self):
        super()._init_params()
        self.model.p_out = self._create_indexed_param(self._data["P_out"])

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.p_out, self._data["P_out"])

    def _register_at_networks(self):
        self._net.register_unit(self, self._p_out, PowerSign.POSITIVE)

    def _unregister_at_networks(self):
        self._net.unregister_unit(self)

    @property
    def _p_out(self) -> pyo.Param:
        return self.model.p_out


class SimpleElectricitySource(_SimpleSource):
    def __init__(self, name: str, data: dict, system: _BaseSystem, *, electrical_network: Electrical):
        super().__init__(name, data, system, network=electrical_network)

    @property
    def p_el_out(self) -> pyo.Param:
        """The electrical output capacity."""
        return self._p_out


class SimpleThermalSource(_SimpleSource):
    pass


class SimpleHeatingSource(SimpleThermalSource):
    def __init__(self, name: str, data: dict, system: _BaseSystem, *, heating_network: HeatingFluid):
        super().__init__(name, data, system, network=heating_network)

    @property
    def p_heat_out(self) -> pyo.Param:
        """The heat output capacity."""
        return self._p_out


class SimpleCoolingSource(SimpleThermalSource):
    _sign_of_capacity = operator.le

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, cooling_network: CoolingFluid):
        super().__init__(name, data, system, network=cooling_network)

    def _register_at_networks(self):
        self._net.register_unit(self, self._p_out, PowerSign.NEGATIVE)

    @property
    def p_cool_out(self) -> pyo.Param:
        """The cooling output capacity."""
        return self._p_out


class _BaseSink(_BaseSourceSink, ABC):
    """Sinks are equipment which consume a fixed or variable capacity without a conversion process."""

    _sign_of_capacity = operator.le

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method. Extends the base method by requiring a network which the sink is connected to."""
        super().__init__(name, data, system, network=network)

    def _register_at_networks(self):
        self._net.register_unit(self, self._p_in, PowerSign.NEGATIVE)

    def _unregister_at_networks(self):
        self._net.unregister_unit(self)

    @property
    @abstractmethod
    def _p_in(self) -> pyo.Var | pyo.Param | pyo.Expression:
        """The input capacity."""
        pass


class _SimpleSink(_BaseSink, ABC):
    """Simple sinks are equipment which consume a fixed capacity without a conversion process."""

    _param_names: ClassVar[list[str]] = [*_BaseSink._param_names, "P_in"]

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method.

        Extends the base method by allowing more properties to be passed in the data argument.

        The additional valid keys for the data argument are the following:
        - P_in: The capacity consumption, must be non-positive. Scalar or indexed.
        """
        super().__init__(name, data, system, network=network)
        self._validate_capacity(self.data["P_in"])

    def _init_params(self):
        super()._init_params()
        self.model.P_in = self._create_indexed_param(self._data["P_in"])

    def _reinitialize_params(self):
        super()._reinitialize_params()
        self._update_param(self.model.P_in, self._data["P_in"])

    @property
    def _p_in(self) -> pyo.Param:
        return self.model.P_in


class SimpleElectricitySink(_SimpleSink):
    def __init__(self, name: str, data: dict, system: _BaseSystem, *, electrical_network: Electrical):
        super().__init__(name, data, system, network=electrical_network)


class SimpleThermalSink(_SimpleSink):
    pass


class SimpleHeatingSink(SimpleThermalSink):
    def __init__(self, name: str, data: dict, system: _BaseSystem, *, heating_network: HeatingFluid):
        super().__init__(name, data, system, network=heating_network)

    @property
    def p_heat_in(self) -> pyo.Param:
        """The heat input capacity."""
        return self._p_in


class SimpleCoolingSink(SimpleThermalSink):
    _sign_of_capacity = operator.ge

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, cooling_network: CoolingFluid):
        super().__init__(name, data, system, network=cooling_network)

    def _register_at_networks(self):
        self._net.register_unit(self, self._p_in, PowerSign.POSITIVE)

    @property
    def p_cool_in(self) -> pyo.Param:
        """The cooling input capacity."""
        return self._p_in


class VariableSourceSink(_BaseSourceSink):
    """VariableSourceSink are equipment which consume and produce a variable capacity without a conversion process."""

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Constructor method."""
        super().__init__(name, data, system, network=network)

    def _register_at_networks(self):
        self._net.register_unit(self, self.p, PowerSign.UNDEFINED)

    def _unregister_at_networks(self):
        self._net.unregister_unit(self)

    def _init_variables(self):
        self.model.p = pyo.Var(*self._system.sets, within=pyo.Reals)

    @property
    def p(self) -> pyo.Var:
        return self.model.p


class _VariableSource(VariableSourceSink, ABC):
    """VariableSource are equipment which produce a variable capacity without a conversion process,
    up to a user-defined limit."""

    _param_names: ClassVar[dict[list]] = [*VariableSourceSink._param_names, "P_out_max"]

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, network: _BaseNetwork):
        """Additional key for data:
        - P_out_max
        """
        super().__init__(name, data, system, network=network)
        self._validate_capacity(self.data["P_out_max"])


class _VariablePositiveSource(_VariableSource, ABC):
    """A VariablePositiveSource consumes a non-negative capacity without a conversion process."""

    _sign_of_capacity = operator.ge

    def _register_at_networks(self):
        self._net.register_unit(self, self.p, PowerSign.POSITIVE)

    def _init_params(self):
        super(_VariableSource, self)._init_params()
        if self._data["P_out_max"] is not None:
            self.model.p_out_max = self._create_indexed_param(self._data["P_out_max"])
        else:
            self.model.p_out_max = self._create_indexed_param(np.inf)

    def _reinitialize_params(self):
        super()._reinitialize_params()
        if self._data["P_out_max"] is not None:
            self._update_param(self.model.p_out_max, self._data["P_out_max"])
        else:
            self._update_param(self.model.p_out_max, np.inf)

    def _init_constraints(self):
        super(_VariableSource, self)._init_constraints()

        def limit_p(m, *idx: int):
            return 0, self.model.p[idx], self.model.p_out_max[idx]

        self.model.limit_p = pyo.Constraint(*self._system.sets, rule=limit_p)


class _VariableNegativeSource(_VariableSource, ABC):
    """A VariableNegativeSource consumes a non-positive capacity without a conversion process."""

    _sign_of_capacity = operator.le

    def _register_at_networks(self):
        self._net.register_unit(self, self.p, PowerSign.NEGATIVE)

    def _init_params(self):
        super(_VariableSource, self)._init_params()
        if self._data["P_out_max"] is not None:
            self.model.p_out_max = self._create_indexed_param(self._data["P_out_max"])
        else:
            self.model.p_out_max = self._create_indexed_param(-np.inf)

    def _reinitialize_params(self):
        super(_VariableSource, self)._reinitialize_params()
        if self._data["P_out_max"] is not None:
            self._update_param(self.model.p_out_max, self._data["P_out_max"])
        else:
            self._update_param(self.model.p_out_max, -np.inf)

    def _init_constraints(self):
        super(_VariableSource, self)._init_constraints()

        def limit_p(m, *idx: int):
            return self.model.p_out_max[idx], self.model.p[idx], 0

        self.model.limit_p = pyo.Constraint(*self._system.sets, rule=limit_p)


class VariableHeatingSource(_VariablePositiveSource):
    @property
    def p_heat_out(self) -> pyo.Var:
        """The heat output capacity."""
        return self.p


class _VariableSink(_BaseSink, ABC):
    """VariableSinks are equipment which consume a variable capacity without a conversion process."""

    def _init_variables(self):
        self.model.buffer = pyo.Var(*self._system.sets, within=pyo.NonNegativeReals)

    def _init_expressions(self):
        self.model.P_in = pyo.Expression(*self._system.sets, rule=self._rule_p_in)

    @staticmethod
    @abstractmethod
    def _rule_p_in(m, *idx: int) -> pyo.Expression:
        """Rule for generating an expression for the input capacity."""

    @property
    def _p_in(self) -> pyo.Expression:
        return self.model.P_in


class _VariablePositiveSink(_VariableSink, ABC):
    """A VariablePositiveSink consumes a non-negative capacity without a conversion process."""

    def _register_at_networks(self):
        self._net.register_unit(self, self._p_in, PowerSign.POSITIVE)

    @staticmethod
    def _rule_p_in(m, *args) -> pyo.Expression:
        return m.buffer[args]


class _VariableNegativeSink(_VariableSink, ABC):
    """A VariableNegativeSink consumes a non-positive capacity without a conversion process."""

    def _register_at_networks(self):
        self._net.register_unit(self, self._p_in, PowerSign.NEGATIVE)

    @staticmethod
    def _rule_p_in(m, *args) -> pyo.Expression:
        return -m.buffer[args]


class VariableHeatingSink(_VariableNegativeSink):
    """VariableHeatingSinks mock a heat consumer that can consume a variable amount of heat."""

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, heating_network: HeatingFluid):
        super().__init__(name, data, system, network=heating_network)

    @property
    def p_heat_in(self) -> pyo.Expression:
        """The heat input capacity."""
        return self._p_in


class VariableCoolingSink(_VariablePositiveSink):
    """VariableCoolingSinks mock a cooling consumer that can consume a variable amount of cooling."""

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, cooling_network: CoolingFluid):
        super().__init__(name, data, system, network=cooling_network)

    @property
    def p_cool_in(self) -> pyo.Expression:
        """The cooling input capacity."""
        return self._p_in


class VariableElectricalSink(_VariableNegativeSink):
    """VariableElectricalSinks mock an electricity consumer that can consume a variable amount of electricity."""

    def __init__(self, name: str, data: dict, system: _BaseSystem, *, electrical_network: Electrical):
        super().__init__(name, data, system, network=electrical_network)

    @property
    def p_el_in(self) -> pyo.Expression:
        """The electrical input capacity."""
        return self._p_in
