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
        soc = 0
        utc = 0.0
        return self._charge_control.update(Measurements(solar, house, wallbox, soc, utc))

    def assert_battery_max_charge(self, solar, house, wallbox, expected):
        c = self.update(solar, house, wallbox)
        assert c.battery_max_charge == expected


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


def test_update_grid_max(t):
    t.assert_battery_max_charge(t.config.grid_max, 0, 0, 0)
    t.assert_battery_max_charge(t.config.grid_max + 1, 0, 0, t.config.battery_min_dis_charge)
    t.assert_battery_max_charge(t.config.grid_max + t.config.battery_min_dis_charge, 0, 0, t.config.battery_min_dis_charge)
    t.assert_battery_max_charge(t.config.grid_max + t.config.battery_max_charge, 0, 0, t.config.battery_max_charge)
    t.assert_battery_max_charge(t.config.grid_max + t.config.battery_max_charge + 1, 0, 0, t.config.battery_max_charge)

    battery_charge = (t.config.battery_max_charge + t.config.battery_min_dis_charge) // 2
    solar = t.config.grid_max + battery_charge
    t.assert_battery_max_charge(solar + 0, 0, 0, battery_charge)
    t.assert_battery_max_charge(solar + 1, 1, 0, battery_charge)
    t.assert_battery_max_charge(solar + 1, 0, 1, battery_charge)
    t.assert_battery_max_charge(solar + 2, 1, 1, battery_charge)
