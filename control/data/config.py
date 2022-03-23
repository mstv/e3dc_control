from dataclasses import dataclass


@dataclass
class Config:
    variation_margin: int
    wallbox_power_by_current: dict
    battery_max_discharge: int
    battery_max_charge: int
    battery_min_dis_charge: int
    solar_max: int
    grid_max: int
