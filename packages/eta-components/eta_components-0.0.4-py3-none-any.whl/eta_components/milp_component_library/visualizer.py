import itertools

import matplotlib.pyplot as plt
import pyomo.environ as pyo

from eta_components.milp_component_library.networks import _BaseNetwork
from eta_components.milp_component_library.systems import _BaseSystem


class Visualizer:
    def __init__(self, system: _BaseSystem):
        self._system = system

    def visualize_all(self):
        for year, period in itertools.product(self._system.years_set, self._system.periods_set):
            self.visualize_period(year, period)

    def visualize_period(self, year: int, period: int):
        for network in self._system.networks:
            fig, ax = plt.subplots(dpi=300)
            fig.suptitle(network.name)
            ax.set_title(f"Year {year}, Period {period}")
            for unit, power in network.unit_power_pairs():
                values = list(pyo.value(power[year, period, :]))
                ax.plot(self._system.time_set, values, label=f"{unit.name}: {power.local_name}")

            ax.legend()
            ax.autoscale(enable=True, axis="x", tight=True)
            fig.tight_layout()

    def visualize_network(self, network: _BaseNetwork):
        for year, period in itertools.product(self._system.years_set, self._system.periods_set):
            fig, ax = plt.subplots(dpi=300)
            fig.suptitle(network.name)
            ax.set_title(f"Year {year}, Period {period}")
            for unit, power in network.unit_power_pairs():
                values = list(pyo.value(power[year, period, :]))
                ax.plot(self._system.time_set, values, label=f"{unit.name}: {power.local_name}")

            ax.legend()
            ax.autoscale(enable=True, axis="x", tight=True)
            fig.tight_layout()
