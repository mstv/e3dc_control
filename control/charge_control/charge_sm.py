from data import Config, Measurements


class ChargeSM:
    def __init__(self, config: Config):
        self._config = config
        self._reset()

    @property
    def config(self) -> Config:
        return self._config

    def _reset(self):
        self._max_solar = 0

    def _clip(self, max_charge: int) -> int:
        max_charge = max(max_charge, self.config.battery_min_dis_charge)
        max_charge = min(max_charge, self.config.battery_max_charge)
        return max_charge

    def update(self, measurements: Measurements) -> int:
        if measurements.solar == 0:
            self._reset()
        elif self._max_solar < measurements.solar:
            self._max_solar = measurements.solar

        excess = measurements.solar - measurements.house - measurements.wallbox
        grid_denied = excess - self.config.grid_max
        if grid_denied > 0:
            max_charge = self._clip(grid_denied)
        else:
            max_charge = 0  # unfinished

        return max_charge
