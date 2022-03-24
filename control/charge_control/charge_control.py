from data import Config, Controls, Measurements
from .charge_sm import ChargeSM


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

    def update(self, measurements: Measurements) -> Controls:
        controls = Controls(
            wallbox_current=self._get_wallbox_current(measurements),
            battery_max_discharge=self.config.battery_max_discharge,
            battery_max_charge=self._charge_sm.update(measurements))
        return controls

    def _get_wallbox_current(self, measurements: Measurements) -> int:
        max_wallbox = measurements.solar \
            - (measurements.house + self.config.variation_margin)
        return _lookup(max_wallbox, self.config.wallbox_power_by_current)
