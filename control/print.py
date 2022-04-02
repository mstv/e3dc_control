from data import Info
from json import dumps


def one_line(info: Info) -> str:
    wb_max = max(0, info.measurements.solar - info.measurements.house)
    wb_delta = wb_max - info.measurements.wallbox
    wb_status = '>' if info.car_charging else '-' if info.car_connected else '!'
    return str(info.dt_utc)[0:19] \
        + f" {info.measurements.soc:3}%" \
        + (f" {info.batt:5}>b" if info.batt > 0 else f" {-info.batt:5}<b") \
        + (f" {info.grid:5}<g" if info.grid > 0 else f" {-info.grid:5}>g") \
        + f" {info.measurements.solar:5}<s{info.solar_delta:<+5}" \
        + f" {info.measurements.house:5}>h" \
        + f" {info.measurements.wallbox:5}{wb_status}w" \
        + f" {wb_max:5}" \
        + f" {wb_delta:+6}" \
        + f" {info.controls.wallbox_current:2}A" \
        + f" {'>' if info.car_soc == 100 else ' '}{0.1 * info.car_soc:4.1f}" \
        + f" {(0.001 * info.car_total):6.3f}{0.001 * (-info.car_grid):6.2f} kWh " \
        + f" {info.controls.battery_max_discharge:4}<b<{info.controls.battery_max_charge:<4}" \
        + f" {info.control_state.value}"


def readable(jsonData) -> str:
    return dumps(jsonData, indent=4)


def filter(data: dict, include_keys: list) -> dict:
    return {key: data[key] for key in include_keys}
