from data import Config, Measurements


class ChargeSM:
    def __init__(self, config: Config):
        self._config = config
        self._update_solar_parabola(utc=None, solar=0)
        self._init_max_charge()

    @property
    def config(self) -> Config:
        return self._config

    def _init_max_charge(self):
        self._max_charge = 0

    def _apply_charge(self, charge: int):
        if charge <= 0:
            return
        charge = max(charge, self.config.battery_min_dis_charge)
        charge = min(charge, self.config.battery_max_charge)
        if self._max_charge < charge:
            self._max_charge = charge

    def update(self, measurements: Measurements) -> int:
        self._update_solar_parabola(measurements.utc, measurements.solar)

        self._init_max_charge()
        self._apply_charge(self._get_grid_denied(measurements))
        self._apply_charge(self._get_charge_by_solar_parabola
                           (self._get_max_grid_denied_watthours(measurements.utc),
                            self._get_max_charge_watthours(measurements.soc)))
        return self._max_charge

    def _get_grid_denied(self, measurements: Measurements):
        excess = measurements.solar - measurements.house - measurements.wallbox
        grid_denied = excess - self.config.grid_max
        return grid_denied

    def _get_max_charge_watthours(self, soc: int) -> int:
        return self.config.battery_watthours * (100 - soc) // 100

    def _get_charge_by_solar_parabola(self, max_grid_denied_watthours: int,
                                      max_charge_watthours: int) -> int:
        if max_grid_denied_watthours is not None:
            if max_grid_denied_watthours < max_charge_watthours:
                # charge as much as possible
                return self.config.battery_max_charge
        # wait (or charge the grid_denied, which is handled separately)
        return 0

    def _get_max_grid_denied_watthours(self, utc: float) -> int or None:
        hours_after_peak = utc - self.config.solar_peak_utc
        if hours_after_peak < 0:
            return None  # future grid_denied integral cannot be estimated yet
        max_grid_denied = self._max_solar - self.config.grid_max
        if max_grid_denied <= 0 or self._half_grid_max_utc is None:
            return 0
        # rough preliminary estimate: rectangle of max_grid_denied for 2 hours
        watthours = int((2.0 - hours_after_peak) * max_grid_denied)
        return watthours

    def _update_solar_parabola(self, utc: float, solar: int):
        if solar == 0:
            # wait for next sunrise
            self._max_solar = 0
            self._half_grid_max_utc = None
        else:
            if self._max_solar < solar:
                self._max_solar = solar
            if self._half_grid_max_utc is None and solar >= self.config.grid_max // 2:
                self._half_grid_max_utc = utc
