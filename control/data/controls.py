from dataclasses import dataclass


@dataclass
class Controls:
    wallbox_current: int
    # fix yet: battery_discharge_for_wallbox: bool = False
    battery_max_discharge: int
    battery_max_charge: int
