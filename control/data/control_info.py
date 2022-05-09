from .controls import Controls
from dataclasses import dataclass
from enum import Enum, unique
from .info import Info
from .measurements import Measurements


@unique
class ControlState(Enum):
    NotUpdated = '.'
    Unchanged = '='
    Changed = '!'


@dataclass
class ControlInfo(Info):
    averaged: Measurements
    max_solar: int
    controls: Controls
    control_state: ControlState
