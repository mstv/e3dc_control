from dataclasses import dataclass


@dataclass
class Controls:
    wallbox_current: int
    battery_max_discharge: int
    battery_max_charge: int
