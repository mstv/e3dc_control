from ..charge_sm import ChargeSM
from ..config import CONFIG
from data import Config, Measurements, Controls
import pytest


@pytest.fixture
def config() -> Config:
    yield CONFIG


@pytest.fixture
def sm(config: Config) -> ChargeSM:
    yield ChargeSM(config)


def test_get_max_charge_watthours(sm):
    assert sm._get_max_charge_watthours(0) == sm.config.battery_watthours
    assert sm._get_max_charge_watthours(50) == sm.config.battery_watthours // 2
    assert sm._get_max_charge_watthours(100) == 0


def test_get_charge_by_solar_parabola(sm):
    assert sm._get_charge_by_solar_parabola(
        max_grid_denied_watthours=None, max_charge_watthours=None) == 0
    assert sm._get_charge_by_solar_parabola(
        max_grid_denied_watthours=0, max_charge_watthours=0) == 0
    assert sm._get_charge_by_solar_parabola(
        max_grid_denied_watthours=1, max_charge_watthours=0) == 0
    assert sm._get_charge_by_solar_parabola(
        max_grid_denied_watthours=1, max_charge_watthours=1) == 0
    assert sm._get_charge_by_solar_parabola(
        max_grid_denied_watthours=2, max_charge_watthours=1) == 0
    assert sm._get_charge_by_solar_parabola(
        max_grid_denied_watthours=2, max_charge_watthours=2) == 0
    assert sm._get_charge_by_solar_parabola(
        max_grid_denied_watthours=1, max_charge_watthours=2) == sm.config.battery_max_charge


def test_get_max_grid_denied_watthours(sm):
    peak_utc = (sm.config.solar_peak_start_utc
                + sm.config.solar_peak_end_utc) / 2
    before_peak_utc = sm.config.solar_peak_start_utc - 1.0 / 3600
    after_peak_utc = sm.config.solar_peak_end_utc + 1.0 / 3600
    min_utc = 0.0
    max_utc = 24.0

    sm._update_solar_parabola(utc=None, solar=0)
    assert sm._get_max_grid_denied_watthours(min_utc) is None
    assert sm._get_max_grid_denied_watthours(before_peak_utc) is None
    assert sm._get_max_grid_denied_watthours(peak_utc) == 0
    assert sm._get_max_grid_denied_watthours(after_peak_utc) == 0
    assert sm._get_max_grid_denied_watthours(max_utc) == 0

    sm._update_solar_parabola(utc=None, solar=sm.config.grid_max)
    assert sm._get_max_grid_denied_watthours(min_utc) is None
    assert sm._get_max_grid_denied_watthours(before_peak_utc) is None
    assert sm._get_max_grid_denied_watthours(peak_utc) == 0
    assert sm._get_max_grid_denied_watthours(after_peak_utc) == 0
    assert sm._get_max_grid_denied_watthours(max_utc) == 0

    sm._update_solar_parabola(utc=None, solar=sm.config.grid_max + 1)
    assert sm._get_max_grid_denied_watthours(min_utc) is None
    assert sm._get_max_grid_denied_watthours(before_peak_utc) is None
    assert sm._get_max_grid_denied_watthours(peak_utc) == 0
    assert sm._get_max_grid_denied_watthours(after_peak_utc) == 0
    assert sm._get_max_grid_denied_watthours(max_utc) == 0

    sm._update_solar_parabola(utc=None, solar=0)  # reset
    sm._update_solar_parabola(peak_utc - 3.5, solar=sm.config.grid_max // 2)
    sm._update_solar_parabola(before_peak_utc, solar=sm.config.grid_max + 1800)
    no_grid_denied_utc = peak_utc + 2.25
    between_utc = (peak_utc + no_grid_denied_utc) / 2
    assert sm._get_max_grid_denied_watthours(min_utc) is None
    assert sm._get_max_grid_denied_watthours(before_peak_utc) is None
    at_peak = sm._get_max_grid_denied_watthours(peak_utc)
    after_peak = sm._get_max_grid_denied_watthours(after_peak_utc)
    after_peak2 = sm._get_max_grid_denied_watthours(peak_utc + 2.0 / 3600)
    between = sm._get_max_grid_denied_watthours(between_utc)
    at_no_grid_denied = sm._get_max_grid_denied_watthours(no_grid_denied_utc)
    assert after_peak <= at_peak
    assert after_peak > 0
    assert after_peak2 < at_peak
    assert after_peak2 > 0
    assert between < at_peak / 3
    assert between > 0
    assert at_no_grid_denied < 100
    assert sm._get_max_grid_denied_watthours(max_utc) == 0
