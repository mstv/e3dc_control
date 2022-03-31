from data import Config, Controls, Measurements
from .charge_sm import ChargeSM


def limit(value, min_positive, max):
    if value <= 0:
        return 0
    elif value < min_positive:
        return min_positive
    elif value > max:
        return max
    return value


def _lookup(max_power: int, power_by_current: dict) -> int:
    for current, power in power_by_current.items():
        if max_power >= power:
            return current
    return 0


class ChargeControl:
    def __init__(self, config: Config):
        self._charge_sm = ChargeSM(config)

    @property
    def config(self) -> Config:
        return self._charge_sm.config

    def limit(self, controls: Controls) -> Controls:
        controls.battery_max_charge = limit(controls.battery_max_charge,
                                            self.config.battery_min_dis_charge,
                                            self.config.battery_max_charge)
        controls.battery_max_discharge = limit(controls.battery_max_discharge,
                                               self.config.battery_min_dis_charge,
                                               self.config.battery_max_discharge)
        return controls

    def update(self, measurements: Measurements, variation_margin: int) -> Controls:
        controls = Controls(
            wallbox_current=self._get_wallbox_current(measurements,
                                                      variation_margin),
            battery_max_discharge=self.config.battery_max_discharge,
            battery_max_charge=self._charge_sm.update(measurements,
                                                      variation_margin))
        return controls

    def _get_wallbox_current(self, measurements: Measurements, variation_margin: int) -> int:
        max_wallbox = measurements.solar \
            - (measurements.house + variation_margin)
        return _lookup(max_wallbox, self.config.wallbox_power_by_current)
