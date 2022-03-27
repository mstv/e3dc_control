from array import array
from dataclasses import dataclass


@dataclass
class Config:
    solar_peak_utc: float
    variation_margin: int
    wallbox_power_by_current: dict
    default_idle_charge_active: bool
    default_idle_charge_end: array
    default_battery_max_charge: int
    battery_max_discharge: int
    battery_max_charge: int
    battery_min_dis_charge: int
    battery_watthours: int
    solar_max: int
    grid_max: int
