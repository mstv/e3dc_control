from dataclasses import dataclass
from enum import Enum, unique


@unique
class BatteryCharge(Enum):
    Suppressed = 's'
    Automatic = 'a'
    Default = 'd'
    WallboxActive = 'w'
    Maximum = 'm'


@dataclass
class ChargeControlDirectives:
    battery_charge: BatteryCharge or int
    battery_min_soc: int
    battery_to_car_until_soc: int or None
    all_solar_excess_to_car: bool
    max_wallbox_current_override: int or None
    min_wallbox_current: int or None
