from data import Config, Measurements
from math import sqrt


class ChargeSM:
    def __init__(self, config: Config):
        self._config = config
        self._update_solar_parabola(utc=None, solar=0)

    @property
    def config(self) -> Config:
        return self._config

    def update(self, measurements: Measurements, variation_margin: int) -> int:
        self._update_solar_parabola(measurements.utc, measurements.solar)

        max_charge = 0
        max_charge = max(max_charge,
                         self._get_grid_denied(measurements,
                                               variation_margin))
        max_charge = max(max_charge,
                         self._get_charge_by_solar_parabola
                         (self._get_max_grid_denied_watthours(measurements.utc),
                          self._get_max_charge_watthours(measurements.soc)))
        return max_charge

    def _get_grid_denied(self, measurements: Measurements, variation_margin):
        variation_margin += self.config.additional_solar_variation_margin
        excess = measurements.solar \
            - measurements.house \
            - measurements.wallbox \
            + variation_margin  # rather route too much to battery now, it can be discarded later
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
        if utc < self.config.solar_peak_start_utc:
            return None  # future grid_denied integral cannot be estimated yet
        hours_after_peak_end = utc - self.config.solar_peak_end_utc  # right side of parabola
        hours_before_peak_end = -hours_after_peak_end  # plateau
        max_grid_denied = self._max_solar - self.config.grid_max
        if max_grid_denied <= 0 or self._half_grid_max_utc is None:
            return 0
        # s(t) = a * (t - t_peak) ^ 2 + s_peak
        # with a < 0 and s_peak approximated using self._max_solar
        #      s(t) - s_peak
        # a = ----------------
        #     (t - t_peak) ^ 2
        # (t - t_peak) = sqrt( (s(t) - s_peak) / a )
        # Integral (a * x ^ 2 + b) dx = a / 3 * x ^ 3 + b * x + constant
        a = (self.config.grid_max / 2 - self._max_solar) \
            / pow(self._half_grid_max_utc - self.config.solar_peak_start_utc, 2)
        stop_hours_after_peak_end = sqrt(-max_grid_denied / a)
        if hours_after_peak_end >= stop_hours_after_peak_end:
            return 0
        watthours = max_grid_denied * max(0, hours_before_peak_end) \
            + round(a / 3 * (pow(stop_hours_after_peak_end, 3)
                             - pow(hours_after_peak_end, 3))
                    + max_grid_denied * (stop_hours_after_peak_end
                                         - hours_after_peak_end))
        return watthours

    def _update_solar_parabola(self, utc: float, solar: int):
        if solar == 0:
            # wait for next sunrise
            self._max_solar = 0
            self._half_grid_max_utc = None
        else:
            if self._max_solar < solar:
                self._max_solar = solar
            if self._half_grid_max_utc is None \
                    and solar >= self.config.grid_max // 2 \
                    and utc is not None \
                    and utc < self.config.solar_peak_start_utc:
                self._half_grid_max_utc = utc
