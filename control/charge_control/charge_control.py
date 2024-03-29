from data import Config, Controls, Measurements
from typing import Callable
from .charge_sm import ChargeSM


def limit(value, min_positive, max):
    if value <= 0:
        return 0
    elif value < min_positive:
        return min_positive
    elif value > max:
        return max
    return value


def lookup_below(max_power: int, power_by_current: dict) -> int:
    for current, power in power_by_current.items():
        if max_power >= power:
            return current
    return 0


def lookup_above(min_power: int, power_by_current: dict) -> int:
    if min_power <= 0:
        return 0
    for current, power in reversed(power_by_current.items()):
        if min_power <= power:
            return current
    return max(power_by_current.keys())


def _get_wallbox_current(measurements: Measurements, variation_margin: int, lookup: Callable[[int], int]) -> int:
    max_wallbox = measurements.solar \
        - (measurements.house + variation_margin)
    return lookup(max_wallbox)


class ChargeControl:
    def __init__(self, config: Config):
        self._charge_sm = ChargeSM(config)

    @property
    def config(self) -> Config:
        return self._charge_sm.config

    def limit(self, controls: Controls) -> Controls:
        controls.battery_max_charge = limit(controls.battery_max_charge,
                                            self.config.battery_min_charge,
                                            self.config.battery_max_charge)
        controls.battery_max_discharge = limit(controls.battery_max_discharge,
                                               self.config.battery_min_discharge,
                                               self.config.battery_max_discharge)
        return controls

    def update(self, measurements: Measurements, variation_margin: int, battery_to_car: int, lookup_current: Callable[[int], int]) -> Controls:
        controls = Controls(
            wallbox_current=_get_wallbox_current(measurements,
                                                 variation_margin - battery_to_car,
                                                 lookup_current),
            battery_max_discharge=self.config.battery_max_discharge,
            battery_max_charge=self._charge_sm.update(measurements,
                                                      variation_margin))
        return self._adapt(controls)

    def _adapt(self, controls: Controls) -> Controls:
        if controls.battery_max_charge != 0:
            controls.battery_max_charge \
                = limit(self.config.battery_charge_adapt_offset
                        + round(self.config.battery_charge_adapt_factor
                                * controls.battery_max_charge),
                        0, self.config.battery_max_charge)
        return controls
