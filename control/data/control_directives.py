from .charge_control_directives import ChargeControlDirectives
from dataclasses import dataclass
from enum import Enum, unique


@unique
class Loop(Enum):
    Run = 'r'
    BreakWithoutTeardown = 'b'
    ExitWithTeardown = 'e'


@dataclass
class ControlDirectives:
    loop: Loop or None
    charge_control: ChargeControlDirectives
