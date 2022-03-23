from ..charge_control import ChargeControl
from ..config import CONFIG
from data import Config, Measurements, Controls
import pytest


@pytest.fixture
def config() -> Config:
    yield CONFIG


@pytest.fixture
def charge_control(config: Config) -> ChargeControl:
    yield ChargeControl(config)


class Tester:
    def __init__(self, charge_control: ChargeControl):
        self._charge_control = charge_control

    @property
    def config(self) -> Config:
        return self._charge_control.config

    def update(self, solar, house, wallbox) -> Controls:
        return self._charge_control.update(Measurements(solar, house, wallbox))


@pytest.fixture
def t(charge_control: ChargeControl) -> Tester:
    yield Tester(charge_control)


def test_update_wallbox_current(t):
    for wallbox_power in (0, 1000, 5000, 11000, 22000):  # no influence
        wallbox_current = max(t.config.wallbox_power_by_current.keys())
        solar = t.config.solar_max
        house = solar \
            - t.config.wallbox_power_by_current[wallbox_current] \
            - t.config.variation_margin

        c = t.update(solar, house, wallbox_power)
        assert c.wallbox_current == wallbox_current
        assert c.battery_max_discharge == t.config.battery_max_discharge

        solar -= 1
        c = t.update(solar, house, wallbox_power)
        assert c.wallbox_current == wallbox_current - 1
        assert c.battery_max_discharge == t.config.battery_max_discharge
