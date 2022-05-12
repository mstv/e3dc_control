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
    max_wallbox_current: int or None
    min_wallbox_current: int or None
