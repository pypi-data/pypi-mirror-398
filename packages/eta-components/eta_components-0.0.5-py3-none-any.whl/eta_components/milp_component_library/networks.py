from __future__ import annotations

import abc
import itertools
import logging
import warnings
from abc import ABC
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

import tabulate
from pyomo import environ as pyo

from eta_components.milp_component_library.base_object import BaseObject
from eta_components.milp_component_library.units.pumps import _BasePump
from eta_components.milp_component_library.units.transmission_losses import TransmissionLoss

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from eta_components.milp_component_library.systems import _BaseSystem
    from eta_components.milp_component_library.units.base_unit import BaseUnit


class PowerSign(Enum):
    UNDEFINED = 1
    POSITIVE = 2
    NEGATIVE = 3


class _BaseNetwork(BaseObject, ABC):
    """A network that provides an interface for parameters and enforces an energy balance constraint.

    Networks provide an interface to access and share the same Pyomo parameters from different sub-models without
    duplication. Different sub-models can be added to the network with corresponding Pyomo variables or parameters.
    The network then enforces an energy balance constraint across all added sub-models.
    """

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Constructor method.

        The valid keys for the data argument are the following.
        - transmission_loss: The fraction of lost producer power. Scalar or indexed between 0 and 1, defaults to 0.
        - power_transfer_max: The maximum permissible generation of the producers. Scalar, defaults to 10**12.
        """
        super().__init__(name, data, system)
        system.register_network(self)

        self._positive_powers: list[tuple[BaseUnit, pyo.Var | pyo.Param | pyo.Expression]] = []
        self._negative_powers: list[tuple[BaseUnit, pyo.Var | pyo.Param | pyo.Expression]] = []
        self._undefined_powers: list[tuple[BaseUnit, pyo.Var | pyo.Param | pyo.Expression]] = []

        self._losses: list[TransmissionLoss] = []

        self._populate_model()

    def register_unit(self, unit: BaseUnit, power: pyo.Var | pyo.Param | pyo.Expression, kind: PowerSign):
        """Add a unit to this network with its power value to consider in the energy balance.

        :param unit: The unit to add to this network. BaseUnit.
        :param power: The Pyomo value of the unit to add to the energy balance of this network.
            pyo.Var | pyo.Param | pyo.Expression.
        :param kind: The type of power, e.g. producer or consumer.
        """
        if kind == PowerSign.UNDEFINED:
            self._undefined_powers.append((unit, power))
        elif kind == PowerSign.POSITIVE:
            self._positive_powers.append((unit, power))
        elif kind == PowerSign.NEGATIVE:
            self._negative_powers.append((unit, power))
        else:
            raise ValueError(f"Unknown power kind {kind.name} for unit {unit.name} and power {power.local_name}.")

    def unregister_unit(self, unit: BaseUnit):
        found = True
        for kind in self._undefined_powers, self._positive_powers, self._negative_powers:
            for unit_, power in kind:
                if unit_ == unit:
                    kind.remove((unit_, power))
                    found = True

        if not found:
            raise ValueError(f"Unit {unit.name} is not registered in network {self.name}.")

    def register_loss(self, loss: TransmissionLoss):
        self._losses.append(loss)

    def unregister_loss(self, loss: TransmissionLoss):
        try:
            self._losses.remove(loss)
        except ValueError as err:
            raise ValueError(f"Transmission loss {loss.name} is not registered in network {self.name}.") from err

    def _populate_model(self):
        self._init_params()

    def build_constraints(self):
        """Build the energy balance constraint of this network. This is called automatically be the system."""
        self._init_losses()
        self._init_expressions()
        self._init_constraints()

    def _init_losses(self):
        for loss in self._losses:
            loss.construct_model()

    def _init_params(self):
        """Initialize the parameters of this network."""
        return

    def _reinitialize_params(self):
        self._init_params()

    def _init_expressions(self):
        pass

    def _init_constraints(self):
        """Initialize the constraints of this network."""
        self._enforce_power_balance()

    def _enforce_power_balance(self):
        def power_balance(m, *idx: int):
            return (
                sum(power[idx] for _, power in self._producers)
                + sum(power[idx] for _, power in self._consumers)
                + sum(power[idx] for _, power in self._prosumers)
                == 0
            )

        if len(self.units()):  # If there are no units, the power_balance will result in 0 == 0, causing Pyomo to fail
            self.model.power_balance = pyo.Constraint(*self._system.sets, rule=power_balance)

    def remove_constraints(self):
        self.model.del_component("power_balance")
        self.model.del_component("power_balance_index")

        for loss in self._losses:
            loss.deconstruct_model()

    @property
    def _producers(self):
        return self._positive_powers

    @property
    def _consumers(self):
        return self._negative_powers

    @property
    def _prosumers(self):
        return self._undefined_powers

    def display(self):
        """Displays information about the units of the network."""
        logger.info("Producers")
        producers_table = tabulate.tabulate(
            [[unit.name, power.local_name] for unit, power in self._producers], headers=["Name", "Power"]
        )
        logger.info("\n%s", producers_table)

        logger.info("\nConsumers")
        consumers_table = tabulate.tabulate(
            [[unit.name, power.local_name] for unit, power in self._consumers], headers=["Name", "Power"]
        )
        logger.info("\n%s", consumers_table)

        if self._prosumers:
            logger.info("\nProsumers")
            prosumers_table = tabulate.tabulate(
                [[unit.name, power.local_name] for unit, power in self._prosumers], headers=["Name", "Power"]
            )
            logger.info("\n%s", prosumers_table)

    def units(self) -> tuple[BaseUnit]:
        """The units of this network."""
        return tuple(
            unit_power_pair[0]
            for unit_power_pair in itertools.chain(self._undefined_powers, self._positive_powers, self._negative_powers)
        )

    def powers(self, unit: BaseUnit) -> tuple[pyo.Param | pyo.Var | pyo.Expression, ...]:
        if unit not in self.units():
            raise ValueError(f"Unit {unit.name} is not registered in network {self.name}.")

        powers = []
        for kind in self._undefined_powers, self._positive_powers, self._negative_powers:
            for unit_, power in kind:
                if unit_ == unit:
                    powers.append(power)
        return tuple(powers)

    def unit_power_pairs(self) -> list[tuple[BaseUnit, pyo.Var | pyo.Param | pyo.Expression]]:
        "Return (unit, power) pairs for all registered units."
        return list(itertools.chain(self._undefined_powers, self._positive_powers, self._negative_powers))


class _Thermal(_BaseNetwork, ABC):
    pass


class _ThermalFluid(_Thermal, ABC):
    """A network subclass for thermal networks.

    Extends the base class by thermal fluid properties. Two sides of the network are modeled, one hot and one cold side,
    where each either represents the flow or the return side of the fluid network. The properties are passed in the
    init-method through the data-argument.
    """

    _param_names: ClassVar[list[str]] = ["T_hot", "T_cold"]
    _optional_params: ClassVar[dict[str, float]] = {
        "rho": 997,  # kg/m3
        "cp": 4.19,  # kJ/kgK
    }

    def __init__(self, name: str, data: dict, system: _BaseSystem):
        """Constructor method. Extends the base method by allowing more properties to be passed in the data argument.

        Extends the valid keys for the data argument with the following.
        If indexed properties are passed, the keys must follow the scheme of the sets stored in the system.
        - T_hot: The hot temperature of the fluid in Kelvin. Indexed or scalar.
        - T_cold: The cold temperature of the fluid in Kelvin. Indexed or scalar.
        - rho: The density of the fluid. Scalar. Defaults to 997 kg/m3.
        - cp: The specific thermal capacity of the fluid. Scalar. Defaults to 4.19 kJ/kgK.
        - p_delta: The pressure difference from the producers to the consumers back to the producers.
            Scalar. Defaults to 1 bar.

        Pay attention that the units of the passed values match with the following formula:
            [P_out_nom] = Kelvin* [cp] * [rho] * [volume_flow_max]
        This works out if P_out_nom of the converters is in kW, rho in kg/m3, cp in kJ/kgK and volume_flow_max in m3/h.
        """
        super().__init__(name, data, system)

        self._pumps: list[_BasePump] = []

    def _init_params(self):
        """Initialize the class-specific parameters and check that their values are valid."""
        self.model.t_hot = self._create_indexed_param(self._data["T_hot"])
        self.model.t_cold = self._create_indexed_param(self._data["T_cold"])
        self.model.rho = self._create_scalar_param(self._data["rho"])
        self.model.cp = self._create_scalar_param(self._data["cp"])
        self._check_params()

    def _reinitialize_params(self):
        self._update_param(self.model.t_hot, self._data["T_hot"])
        self._update_param(self.model.t_cold, self._data["T_cold"])
        self._update_param(self.model.rho, self._data["rho"])
        self._update_param(self.model.cp, self._data["cp"])

    def register_pump(self, pump: _BasePump):
        self._pumps.append(pump)

    def unregister_pump(self, pump: _BasePump):
        try:
            self._pumps.remove(pump)
        except ValueError as err:
            raise ValueError(f"Pump {pump.name} is not registered in network {self.name}.") from err

    def build_constraints(self):
        """Build the energy balance constraint of this network."""
        self._build_pump_models()
        super().build_constraints()

    def _build_pump_models(self):
        for pump in self._pumps:
            pump.construct_model()

    def _init_expressions(self):
        return

    def remove_constraints(self):
        super().remove_constraints()
        for pump in self._pumps:
            pump.deconstruct_model()

    def _check_params(self):
        """Check that for every index the hot temperature is larger than the cold temperature and print a warning if
        that is not the case.
        """
        for index in itertools.product(*self._system.sets):
            if pyo.value(self.model.t_hot[index] <= self.model.t_cold[index]):
                # If t_hot is not larger than t_cold, the calculation of the volume flow becomes ambiguous.
                raise ValueError(
                    f"Hot temperature of thermal network {self.name} equal or less the cold temperature for "
                    f"index {index}. The hot temperature must always be larger than the cold temperature."
                )
            if pyo.value(self.model.t_hot[index] <= 273.15) or pyo.value(self.model.t_cold[index] <= 273.15):
                warnings.warn(
                    f"The hot or cold temperature of thermal network {self.name} for index {index} is below 273.15 "
                    f"Kelvin. Check that you have entered the network temperature in Kelvin.",
                    stacklevel=2,
                )

    @property
    def t_cold(self) -> pyo.Param:
        """The cold fluid temperature in Kelvin."""
        return self.model.t_cold

    @property
    def t_hot(self) -> pyo.Param:
        """The hot fluid temperature in Kelvin."""
        return self.model.t_hot

    @property
    @abc.abstractmethod
    def t_flow(self) -> pyo.Param:
        """The flow temperature in Kelvin."""
        pass

    @property
    @abc.abstractmethod
    def t_return(self) -> pyo.Param:
        """The return temperature in Kelvin."""
        pass

    @property
    def rho(self) -> pyo.Param:
        """The density of the fluid."""
        return self.model.rho

    @property
    def cp(self) -> pyo.Param:
        """The specific heat capacity of the fluid."""
        return self.model.cp


class HeatingFluid(_ThermalFluid):
    """A thermal fluid heating network."""

    @property
    def t_flow(self) -> pyo.Param:
        return self.t_hot

    @property
    def t_return(self) -> pyo.Param:
        return self.t_cold


class CoolingFluid(_ThermalFluid):
    """A thermal fluid cooling network. Differs from other networks in the way that producers generate feed in negative
    power into the network, as cooling is treated as removing heat, and consumers feed in positive power.
    """

    @property
    def _producers(self):
        return self._negative_powers

    @property
    def _consumers(self):
        return self._positive_powers

    @property
    def t_flow(self) -> pyo.Param:
        return self.t_cold

    @property
    def t_return(self) -> pyo.Param:
        return self.t_hot


class Fuel(_BaseNetwork, ABC):
    """A network transporting fuel."""


class Gas(Fuel):
    """A network transporting gas."""


class Hydrogen(Fuel):
    """A network transporting hydrogen."""


class Electrical(_BaseNetwork):
    """A network subclass for electrical networks."""


class AlternatingCurrent(Electrical):
    """An alternating current electrical network."""


class DirectCurrent(Electrical):
    """A direct current electrical network."""


class Water(_BaseNetwork):
    """A water supply network. This network does not enforce an energy but a mass balance."""
