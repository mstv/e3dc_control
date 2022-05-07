from dataclasses import dataclass
from enum import Enum, unique


@unique
class BatteryCharge(Enum):
    Suppressed = 's'
    Automatic = 'a'
    Default = 'd'
    WallboxActive = 'w'
    Full = 'f'


@unique
class Loop(Enum):
    Run = 'r'
    BreakWithoutTeardown = 'b'
    ExitWithTeardown = 'e'


@dataclass
class ControlDirectives:
    loop: Loop or None
    battery_charge: BatteryCharge or int
