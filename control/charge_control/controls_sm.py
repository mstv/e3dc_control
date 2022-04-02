from data import Controls


def _update(current: int, a: int, b: int):
    lower = min(a, b)
    upper = max(a, b)
    changed = current is None or current < lower or upper < current
    if changed:
        current = (a + b) // 2
    return current, changed


class ControlsSM:
    def __init__(self):
        self._controls = Controls(None, None, None)

    def update(self, a: Controls, b: Controls) -> Controls:
        wallbox_current, wb_changed = _update(self._controls.wallbox_current,
                                              a.wallbox_current,
                                              b.wallbox_current)
        battery_max_discharge, d_changed = _update(self._controls.battery_max_discharge,
                                                   a.battery_max_discharge,
                                                   b.battery_max_discharge)
        battery_max_charge, c_changed = _update(self._controls.battery_max_charge,
                                                a.battery_max_charge,
                                                b.battery_max_charge)
        self._controls = Controls(wallbox_current,
                                  battery_max_discharge,
                                  battery_max_charge)
        changed = Controls(wb_changed, d_changed, c_changed)
        return self._controls, changed
