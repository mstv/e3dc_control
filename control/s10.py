from array import array
from charge_control import ChargeControl, ControlsSM, CONFIG
from tools import MovingAverage
from data import Config, Controls, ControlState, Info, Measurements
from datetime import datetime
from e3dc import E3DC
import getopt
import os
from print import one_line, readable, filter
import sys
import time

this_path = os.path.dirname(__file__)
config_path = os.path.abspath(os.path.join(this_path, '../../e3dc_config'))
sys.path.append(config_path)

from e3dc_config import E3DC_Config


class S10:
    def __init__(self, config: Config):
        self._control = ChargeControl(config)
        self._controls_sm = ControlsSM()
        self._e3dc = E3DC(E3DC.CONNECT_LOCAL,
                          username=E3DC_Config.USERNAME,
                          password=E3DC_Config.PASSWORD,
                          ipAddress=E3DC_Config.IP,
                          key=E3DC_Config.SECRET)
        self._ma_measurements = MovingAverage(4)
        # previous control state for change detection
        self._idle_active = None
        self._idle_end = None
        self._wb_on_utc = None

    @property
    def config(self) -> Config:
        return self._control.config

    def send(self, request: str, data: array) -> object:
        return self._e3dc.sendRequest((request, "Container", data), keepAlive=True)

    def get(self, tag) -> object:
        return self._e3dc.sendRequestTag(tag, keepAlive=True)

    def get_solar_power(self, pvi_index: int, pv_string_index: int) -> float:
        power = self.send("PVI_REQ_DATA",
                          [
                              ("PVI_INDEX", "Uint16", pvi_index),
                              ("PVI_REQ_DC_POWER", "Uint16", pv_string_index),
                          ])
        return power[2][1][2][1][2]

    def get_info(self) -> Info:
        utime = self.get("INFO_REQ_UTC_TIME")
        measurements = Measurements(solar=self.get('EMS_REQ_POWER_PV'),
                                    house=self.get('EMS_REQ_POWER_HOME'),
                                    wallbox=self.get('EMS_REQ_POWER_WB_ALL'),
                                    soc=self.get('EMS_REQ_BAT_SOC'),
                                    utc=utime / 3600 % 24)
        batt = self.get('EMS_REQ_POWER_BAT')
        grid = self.get('EMS_REQ_POWER_GRID')
        solar_delta = int(self.get_solar_power(0, 0)
                          - self.get_solar_power(0, 1))

        self._ma_measurements.add(measurements)
        averaged = self._ma_measurements.get()
        averaged.utc = measurements.utc  # do not average time

        wb = self.get_wb_info()
        wb_status = wb['status']
        wb_solar = wb['solar']
        car_connected = wb_status['plugged'] and wb_status['locked']
        car_may_charge = not wb_status['canceled'] and car_connected
        info = Info(dt_utc=datetime.utcfromtimestamp(utime),
                    measurements=measurements,
                    averaged=averaged,
                    max_solar=self._control._charge_sm._max_solar,
                    solar_delta=solar_delta,
                    batt=batt,
                    grid=grid,
                    car_connected=car_connected,
                    car_may_charge=car_may_charge,
                    car_charging=wb_status['charging'],
                    car_soc=wb_solar[2],
                    car_total=wb_solar[5],
                    car_grid=wb['grid'][0],
                    controls=None,
                    control_state=ControlState.NotUpdated)
        return info

    def print_all(self, verbose: bool):
        if verbose:
            print('poll')
        data = self._e3dc.poll(keepAlive=True)
        if verbose:
            time = data['time']
            data['time'] = str(time)
            print(readable(data))
            data['time'] = time
        else:
            data['production'].pop('add')
            print(
                readable(filter(data, ['consumption', 'production', 'stateOfCharge'])))

        if verbose:
            print('get_pvi_data')
        pvi_data = self._e3dc.get_pvi_data(keepAlive=True)
        # print(readable(e3dc.get_pvis_data())) as 1-element array
        solar_data = pvi_data['strings']
        solar_powers = {
            f"solar {string}": solar_data[string]['power'] for string in solar_data}
        print(readable(solar_powers))
        print(readable(
            filter(pvi_data, ['deviceState', 'onGrid', 'powerMode', 'systemMode', 'state'])))
        if verbose:
            print(readable(pvi_data))

        if verbose:
            print('get_power_settings')
        powerSettings = self._e3dc.get_power_settings(keepAlive=True)
        print(readable(powerSettings))
        # set_power_limits
        # set_powersave
        # set_weather_regulated_charge

        if verbose:
            print('get_system_status')
        print(readable(self._e3dc.get_system_status(keepAlive=True)))

        # 'deratePower', 'maxBatChargePower', 'maxBatDischargePower', 'installedBatteryCapacity'
        if verbose:
            print('get_system_info')
            print(readable(self._e3dc.get_system_info(keepAlive=True)))

            print('poll_switches (smart home)')
            print(readable(self._e3dc.poll_switches(keepAlive=True)))
            # set_switch_onoff

            print('get_idle_periods')
            print(readable(self._e3dc.get_idle_periods(keepAlive=True)))
            # set_idle_periods

            print('get_db_data (total sums)')
            print(readable(self._e3dc.get_db_data(keepAlive=True)))

            print('get_battery_data')
            print(readable(self._e3dc.get_battery_data(keepAlive=True)))
            # print(readable(self._e3dc.get_batteries_data(keepAlive=True))) as 1-element array

        # broken
        # pmData = self._e3dc.get_powermeter_data(keepAlive=True)
        # pmsData = self._e3dc.get_powermeters_data(keepAlive=True)
        # print(readable(pmData))
        # print(readable(pmsData))

        print('EMS_BATTERY_TO_CAR_MODE:',
              self.get('EMS_REQ_BATTERY_TO_CAR_MODE'))

        for p, v in self.get_wb_info().items():
            print(p, v)

        if verbose:
            print(solar_data)

    def get_wb(self, wb_index: int = 0) -> object:
        return self.send("WB_REQ_DATA",
                         [
                             ("WB_INDEX", "UChar8", wb_index),
                             ("WB_REQ_EXTERN_DATA_ALG", "None", None),
                             ("WB_REQ_EXTERN_DATA_SUN", "None", None),
                             ("WB_REQ_EXTERN_DATA_NET", "None", None),
                             ("WB_REQ_KEY_STATE", "None", None),
                             # ("WB_REQ_GET_KEY_LOCK_MODE", "None", None),
                             # ("WB_REQ_PARAM_1", "None", None),
                             # ("WB_REQ_ENERGY_ALL", "None", None),
                             # ("WB_REQ_ENERGY_SOLAR", "None", None),
                             # ("WB_REQ_SOC", "None", None),
                             # ("WB_REQ_APP_SOFTWARE", "None", None),
                         ])

    def get_wb_info(self, wb_index: int = 0) -> object:
        response = self.get_wb(wb_index)[2][1:]
        alg = response[0][2][1][2]
        sun = response[1][2][1][2]
        net = response[2][2][1][2]
        key = response[3][2]
        sun_w0_power = (int(sun[1]) << 8) | int(sun[0])
        sun_w12_total = (int(sun[5]) << 24) | (int(sun[4]) << 16) \
            | (int(sun[3]) << 8) | int(sun[2])
        sun_w3_soc = (int(sun[7]) << 8) | int(sun[6])
        net_w0_power = (int(net[1]) << 8) | int(net[0])
        net_w12_total = (int(net[5]) << 24) | (int(net[4]) << 16) \
            | (int(net[3]) << 8) | int(net[2])
        net_w3 = (int(net[7]) << 8) | int(net[6])
        alg0_soc = alg[0]
        alg1_phases = alg[1]
        alg2_status = alg[2]
        alg3_max = alg[3]
        alg5_schuko = alg[5]
        status = {
            'sun mode': (alg2_status & 128) != 0,
            'canceled': (alg2_status & 64) != 0,
            'charging': (alg2_status & 32) != 0,
            'locked': (alg2_status & 16) != 0,
            'plugged': (alg2_status & 8) != 0,
            'max A': alg3_max,
            'key': key,
        }
        info = {
            'solar': [sun_w12_total, sun_w0_power, sun_w3_soc, '% of 10kWh',
                      'total', sun_w12_total + net_w12_total],
            'grid': [net_w12_total, net_w0_power, net_w3],
            'status': status,
        }
        others = (alg2_status & 7, alg[4], alg[6], alg[7])
        if others != (0, 0, 0, 0):
            status['alg[o467]'] = others
        if alg1_phases != 3:
            status['phases'] = alg1_phases
        if alg5_schuko != 0:
            status['schuko'] = alg5_schuko
        if alg0_soc != sun_w3_soc:
            info['solar'][3] += f" but {alg0_soc} in ALG[0]!"
        return info

    def get_local_delta_hours(self, dt_utc) -> int:
        delta_seconds = self.config.timezone.utcoffset(dt_utc).total_seconds()
        return int(delta_seconds) // 3600

    def update(self, dry_run: bool):
        info = self.get_info()

        # calculate
        controls_0 = self._control.update(info.averaged,
                                          variation_margin=0)
        controls_var = self._control.update(info.averaged,
                                            self.config.variation_margin)
        battery_to_car_mode = True
        if info.car_connected:
            local_time = info.measurements.utc \
                + self.get_local_delta_hours(info.dt_utc)
            if self.config.max_wallbox_start <= local_time \
                    or local_time <= self.config.max_wallbox_end:
                controls_0.wallbox_current \
                    = controls_var.wallbox_current \
                    = max(self.config.wallbox_power_by_current.keys())
                battery_to_car_mode = False
            if controls_var.wallbox_current == 0 and self._wb_on_utc is not None:
                wb_on_minutes = (info.measurements.utc - self._wb_on_utc) * 60
                if 0 < wb_on_minutes \
                        and wb_on_minutes < self.config.wallbox_min_current_hold_minutes:
                    controls_0.wallbox_current \
                        = controls_var.wallbox_current \
                        = min(self.config.wallbox_power_by_current.keys())
        else:
            controls_0.wallbox_current \
                = controls_var.wallbox_current \
                = 0
        info.controls, changed = self._controls_sm.update(controls_0,
                                                          controls_var)
        any_changed = changed.wallbox_current \
            or changed.battery_max_discharge \
            or changed.battery_max_charge
        info.control_state = ControlState.Changed if any_changed else ControlState.Unchanged
        info.controls = self._control.limit(info.controls)

        # print
        # print("chg:", changed, "->", any_changed)
        # print("ctr:", info.controls)
        print(one_line(info))

        # set
        if dry_run:
            return
        if changed.battery_max_charge or changed.battery_max_discharge:
            assert info.controls.battery_max_discharge == self.config.battery_max_discharge
            if info.controls.battery_max_charge == 0:
                self.set_charge_idle(True)
            else:
                self._e3dc.set_power_limits(enable=True,
                                            max_charge=info.controls.battery_max_charge,
                                            max_discharge=info.controls.battery_max_discharge,
                                            discharge_start=self.config.battery_min_dis_charge,
                                            keepAlive=True)
                self.set_charge_idle(False)
        may_charge = info.controls.wallbox_current > 0
        if changed.wallbox_current or (info.car_may_charge and not may_charge):
            if may_charge:
                self.set_wallbox_max_current(0, info.controls.wallbox_current)
                time.sleep(3.0)  # avoid misleading peak in house consumption
            if info.car_may_charge != may_charge:
                print(
                    f"toggle_wallbox_charging {info.car_may_charge} -> {may_charge}")
                self.toggle_wallbox_charging()
                self.set_battery_to_car_mode(battery_to_car_mode)
                if may_charge:
                    self._wb_on_utc = info.measurements.utc

    def teardown(self):
        self.set_charge_idle(self.config.default_idle_charge_active,
                             self.config.default_idle_charge_end)
        self._e3dc.set_power_limits(enable=True,
                                    max_charge=self.config.default_battery_max_charge,
                                    max_discharge=self.config.battery_max_discharge,
                                    discharge_start=self.config.battery_min_dis_charge,
                                    keepAlive=False)
        self.set_wallbox_max_current(0,
                                     max(self.config.wallbox_power_by_current.keys()))
        self.set_battery_to_car_mode(False)

    def set_battery_to_car_mode(self, enabled: bool):
        _ = self._e3dc.sendRequest(
            ('EMS_REQ_SET_BATTERY_TO_CAR_MODE', "UChar8", 1 if enabled else 0),
            keepAlive=True)

    def set_charge_idle(self, active: bool, end: array = [23, 59]) -> bool or None:
        if self._idle_active is active and self._idle_end == end:
            return None
        try:
            print(f"SETTING IDLE = {active} {end}")
        except:
            pass  # ignore exceptions on exception exit
        periods = []
        for day in range(7):
            data = [
                ("EMS_IDLE_PERIOD_TYPE", "UChar8", 0),  # charge
                ("EMS_IDLE_PERIOD_DAY", "UChar8", day),
                ("EMS_IDLE_PERIOD_ACTIVE", "Bool", active),
                (
                    "EMS_IDLE_PERIOD_START",
                    "Container",
                    [
                        ("EMS_IDLE_PERIOD_HOUR", "UChar8", 0),
                        ("EMS_IDLE_PERIOD_MINUTE", "UChar8", 0)
                    ]
                ),
                (
                    "EMS_IDLE_PERIOD_END",
                    "Container",
                    [
                        ("EMS_IDLE_PERIOD_HOUR", "UChar8", end[0]),
                        ("EMS_IDLE_PERIOD_MINUTE", "UChar8", end[1])
                    ]
                )
            ]
            periods.append(("EMS_IDLE_PERIOD", "Container", data))
        result = self.send("EMS_REQ_SET_IDLE_PERIODS", periods)
        if result[0] != "EMS_SET_IDLE_PERIODS" or result[2] != 1:
            return False
        self._idle_active = active
        self._idle_end = end
        return True

    def toggle_wallbox_charging(self, wb_index: int = 0):
        _ = self.send_wallbox_request(wb_index, 4, 1)

    def set_wallbox_max_current(self, wb_index: int, max_current: int):
        _ = self.send_wallbox_request(wb_index,
                                      data_index=2,
                                      value=max_current,
                                      set_extern=False)

    def send_wallbox_request(self, wb_index: int, data_index: int, value: int, set_extern: bool = True) -> object:
        request = "WB_REQ_SET_EXTERN" if set_extern else "WB_REQ_SET_PARAM_1"
        extern_data = bytearray([0, 0, 0, 0, 0, 0])
        extern_data[data_index] = value
        param_1 = [
            ("WB_EXTERN_DATA", "ByteArray", extern_data),
            ("WB_EXTERN_DATA_LEN", "UChar8", len(extern_data))
        ]
        return self.send("WB_REQ_DATA",
                         [
                             ("WB_INDEX", "UChar8", wb_index),
                             (request, "Container", param_1)
                         ])


# functions


def print_info(s10: S10, verbose: bool):
    s10.print_all(verbose)
    info = s10.get_info()
    info.controls = Controls(-1, -1, -1)
    print(one_line(info))


def send_request(s10: S10, tag: str):
    value = s10._e3dc.sendRequestTag(tag, keepAlive=True)
    print(value)


# main


def main(argv):
    loop_action = None
    def final_action(s10): pass
    verbose = False
    dry_run = False
    num_loops = None  # infinite
    wait = 2

    try:
        opts, _ = getopt.getopt(argv, "vdn:w:it:",
                                ["verbose",
                                 "dry-run",
                                 "num-loops=",
                                 "wait=",
                                 "info",
                                 "tag=",
                                 "wb="])
    except getopt.GetoptError:
        print('main.py [--verbose] [--dry-run] [--num-loops=n] [--wait=seconds]',
              '| [--info]',
              '| [--tag=TAG]',
              '| [--wb=index:value[:extern]]')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-v', '--verbose'):
            verbose = True
        if opt in ('-d', '--dry-run'):
            dry_run = True
        if opt in ('-n', '--num-loops'):
            num_loops = int(arg)
        if opt in ('-w', '--wait'):
            wait = float(arg)
        if opt in ('-i', '--info'):
            def loop_action(s10): print_info(s10, verbose)
        if opt in ('-t', '--tag'):
            def loop_action(s10): send_request(s10, tag=arg)
            if num_loops is None:
                num_loops = 1
        if opt == '--wb':
            def loop_action(s10):
                data = arg.split(':')
                set_extern = True if len(data) < 3 else data[2] != '0'
                print(S10.send_wallbox_request(
                    s10,
                    0,
                    int(data[0]),
                    int(data[1]),
                    set_extern))
                for p in S10.get_wb(s10)[2][1:]:
                    print(p)
                for p, v in S10.get_wb_info(s10).items():
                    print(p, v)
            if num_loops is None:
                num_loops = 1

    if loop_action is None:
        def loop_action(s10): S10.update(s10, dry_run)
        if not dry_run:
            final_action = S10.teardown

    s10 = S10(CONFIG)
    try:
        loop = 0
        while num_loops is None or loop < num_loops:
            loop += 1
            loop_action(s10)
            if loop != num_loops:
                time.sleep(wait)
    finally:
        final_action(s10)


main(sys.argv[1:])
