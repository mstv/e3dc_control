from ..charge_control import limit, ChargeControl
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

    def assert_adapt(self, max_charge, expected):
        controls = Controls(None, None, max_charge)
        controls = self._charge_control._adapt(controls)
        assert controls.wallbox_current is None
        assert controls.battery_max_discharge is None
        assert controls.battery_max_charge == expected

    def update(self, solar, house, wallbox, variation_margin=0) -> Controls:
        soc = 0
        utc = 0.0
        return self._charge_control.update(Measurements(solar, house, wallbox, soc, utc),
                                           variation_margin)

    def assert_battery_max_charge(self, solar, house, wallbox, variation_margin, expected):
        soc = 0
        utc = 0.0
        measurements = Measurements(solar, house, wallbox, soc, utc)
        max_charge = self._charge_control._charge_sm.update(measurements,
                                                            variation_margin)
        assert max_charge == expected


@pytest.fixture
def t(charge_control: ChargeControl) -> Tester:
    yield Tester(charge_control)


def test_adapt(config):
    config.battery_charge_adapt_offset = 42
    config.battery_charge_adapt_factor = 1.1
    config.battery_max_charge = 42 + 220 - 1
    t = Tester(ChargeControl(config))
    t.assert_adapt(0, 0)
    t.assert_adapt(1, 42 + 1)
    t.assert_adapt(4, 42 + 4)
    t.assert_adapt(5, 42 + 6)
    t.assert_adapt(6, 42 + 7)
    t.assert_adapt(10, 42 + 11)
    t.assert_adapt(100, 42 + 110)
    t.assert_adapt(198, 42 + 218)
    t.assert_adapt(199, 42 + 219)
    t.assert_adapt(200, 42 + 220 - 1)
    t.assert_adapt(201, 42 + 220 - 1)


def test_limit():
    assert limit(-1, 5, 10) == 0
    assert limit(0, 5, 10) == 0
    assert limit(1, 5, 10) == 5
    assert limit(4, 5, 10) == 5
    assert limit(5, 5, 10) == 5
    assert limit(6, 5, 10) == 6
    assert limit(9, 5, 10) == 9
    assert limit(10, 5, 10) == 10
    assert limit(11, 5, 10) == 10


def test_update_wallbox_current(t):
    for wallbox_power in (0, 1000, 5000, 11000, 22000):  # no influence
        for variation_margin in (0, 100, 300, 100):
            wallbox_current = max(t.config.wallbox_power_by_current.keys())
            solar = t.config.solar_max
            house = solar \
                - t.config.wallbox_power_by_current[wallbox_current] \
                - variation_margin

            c = t.update(solar, house, wallbox_power, variation_margin)
            assert c.wallbox_current == wallbox_current
            assert c.battery_max_discharge == t.config.battery_max_discharge

            solar -= 1
            c = t.update(solar, house, wallbox_power, variation_margin)
            assert c.wallbox_current == wallbox_current - 1
            assert c.battery_max_discharge == t.config.battery_max_discharge


def test_update_grid_max(t):
    t.assert_battery_max_charge(0, 0, 0, 0, 0)
    t.assert_battery_max_charge(t.config.grid_max - 1, 0, 0, 0, 0)
    t.assert_battery_max_charge(t.config.grid_max, 0, 0, 0, 0)
    t.assert_battery_max_charge(
        t.config.grid_max + 1, 0, 0, 0, 1)
    t.assert_battery_max_charge(
        t.config.grid_max + t.config.battery_min_charge, 0, 0, 0, t.config.battery_min_charge)
    t.assert_battery_max_charge(
        t.config.grid_max + t.config.battery_max_charge, 0, 0, 0, t.config.battery_max_charge)
    t.assert_battery_max_charge(
        t.config.grid_max + t.config.battery_max_charge + 1, 0, 0, 0, t.config.battery_max_charge + 1)

    battery_charge = (t.config.battery_max_charge +
                      t.config.battery_min_charge) // 2
    solar = t.config.grid_max + battery_charge
    t.assert_battery_max_charge(solar + 0, 0, 0, 0, battery_charge)
    t.assert_battery_max_charge(solar + 1, 1, 0, 0, battery_charge)
    t.assert_battery_max_charge(solar + 1, 0, 1, 0, battery_charge)
    t.assert_battery_max_charge(solar + 2, 1, 1, 0, battery_charge)
    t.assert_battery_max_charge(solar - 1, 0, 0, 1, battery_charge)
    t.assert_battery_max_charge(solar, 1, 0, 1, battery_charge)
    t.assert_battery_max_charge(solar, 0, 1, 1, battery_charge)
    t.assert_battery_max_charge(solar + 1, 1, 1, 1, battery_charge)
