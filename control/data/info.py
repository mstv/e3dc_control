from dataclasses import dataclass
from datetime import datetime
from enum import IntFlag, unique
from .measurements import Measurements


@unique
class Status(IntFlag):
    DcDcAlive = 1 << 0
    PowerMeterAlive = 1 << 1
    BatteryModuleAlive = 1 << 2
    PvModuleAlive = 1 << 3
    PvInverterInited = 1 << 4
    ServerConnectionAlive = 1 << 5
    PvDerated = 1 << 6

    PvAlive = DcDcAlive | PowerMeterAlive | BatteryModuleAlive \
        | PvModuleAlive | PvInverterInited


@dataclass
class Info:
    dt_utc: datetime
    measurements: Measurements
    solar_delta: int
    batt: int
    grid: int
    status: Status
    car_connected: bool
    car_may_charge: bool
    car_charging: bool
    car_max_current: int
    car_soc: int
    car_total: int
    car_grid: int
