from dataclasses import dataclass


@dataclass
class Measurements:
    solar: int
    house: int
    wallbox: int
    soc: int
    utc: float
