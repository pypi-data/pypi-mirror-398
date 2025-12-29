from __future__ import annotations

from eta_components.milp_component_library.units.equipment.base_equipment import (
    BaseAirWaterHeatPump,
    BaseWaterWaterHeatPump,
)
from eta_components.milp_component_library.units.equipment.operational.base_operational import BaseOperational


class AirWaterHeatPump(BaseAirWaterHeatPump, BaseOperational):
    pass


class WaterWaterHeatPump(BaseWaterWaterHeatPump, BaseOperational):
    pass
