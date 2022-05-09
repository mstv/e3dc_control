from array import array
from dataclasses import dataclass
from pytz import timezone


@dataclass
class Config:
    timezone: timezone
    max_wallbox_start: float  # local time
    max_wallbox_end: float  # local time
    solar_peak_start_utc: float
    solar_peak_end_utc: float
    variation_margin: int
    additional_solar_variation_margin: int
    wallbox_min_current_hold_minutes: int
    wallbox_power_by_current: dict
    default_idle_charge_active: bool
    default_idle_charge_end: array  # local time
    default_battery_max_charge: int
    battery_charge_adapt_offset: int
    battery_charge_adapt_factor: float
    battery_max_discharge: int
    battery_min_discharge: int
    battery_max_charge: int
    battery_min_charge: int
    battery_watthours: int
    solar_max: int
    grid_max: int
