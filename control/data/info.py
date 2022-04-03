from .controls import Controls
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, unique
from .measurements import Measurements


@unique
class ControlState(Enum):
    NotUpdated = '.'
    Unchanged = '='
    Changed = '!'


@dataclass
class Info:
    dt_utc: datetime
    measurements: Measurements
    averaged: Measurements
    max_solar: int
    solar_delta: int
    batt: int
    grid: int
    car_connected: bool
    car_may_charge: bool
    car_charging: bool
    car_soc: int
    car_total: int
    car_grid: int
    controls: Controls
    control_state: ControlState
