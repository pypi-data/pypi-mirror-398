from __future__ import annotations

from eta_components.milp_component_library.units.equipment.base_equipment import (
    BaseAirWaterHeatPump,
    BaseWaterWaterHeatPump,
)
from eta_components.milp_component_library.units.equipment.dimensioning.base_dimensioning import BaseDimensioning


class WaterWaterHeatPump(BaseWaterWaterHeatPump, BaseDimensioning):
    """Converter model for a water-water heat pump."""


class AirWaterHeatPump(BaseAirWaterHeatPump, BaseDimensioning):
    """Converter model for an air-water heat pump."""
