from array import array
from charge_control import ChargeControl, CONFIG
from tools import MovingAverage
from data import Controls, ControlState, Info, Measurements
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
    def __init__(self):
        self._control = ChargeControl(CONFIG)
        self._e3dc = E3DC(E3DC.CONNECT_LOCAL,
                          username=E3DC_Config.USERNAME,
                          password=E3DC_Config.PASSWORD,
                          ipAddress=E3DC_Config.IP,
                          key=E3DC_Config.SECRET)
        self._ma_measurements = MovingAverage(4)
        # previous control state for change detection
        self._controls = None
        self._idle_active = None
        self._idle_end = None

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
                                    utc=0)
        batt = self.get('EMS_REQ_POWER_BAT')
        grid = self.get('EMS_REQ_POWER_GRID')
        solar_delta = int(self.get_solar_power(0, 0)
                          - self.get_solar_power(0, 1))

        self._ma_measurements.add(measurements)
        measurements = self._ma_measurements.get()
        measurements.utc = utime / 3600 % 24  # do not average time

        info = Info(dt_utc=datetime.utcfromtimestamp(utime),
                    measurements=measurements,
                    solar_delta=solar_delta,
                    batt=batt,
                    grid=grid,
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

        wb = self.get_wb()[2]
        for p in wb[1:]:
            print(p)

        if verbose:
            print(solar_data)

    def get_wb(self, wb_index: int = 0) -> object:
        return self.send("WB_REQ_DATA",
                         [
                             ("WB_INDEX", "UChar8", wb_index),
                             ("WB_REQ_ENERGY_ALL", "None", None),
                             ("WB_REQ_ENERGY_SOLAR", "None", None),
                             ("WB_REQ_SOC", "None", None),
                             ("WB_REQ_EXTERN_DATA_ALG", "None", None),
                             ("WB_REQ_EXTERN_DATA_SUN", "None", None),
                             ("WB_REQ_EXTERN_DATA_NET", "None", None),
                             ("WB_REQ_PARAM_1", "None", None),
                             ("WB_REQ_APP_SOFTWARE", "None", None)
                         ])

    def update(self, dry_run: bool):
        info = self.get_info()

        # calculate
        info.controls = self._control.update(info.measurements)
        info.control_state = ControlState.Unchanged if self._controls == info.controls else ControlState.Changed
        self._controls = info.controls

        # print
        print(one_line(info))

        # set
        if dry_run:
            return
        idle = info.controls.battery_max_charge == 0
        max_charge = CONFIG.battery_max_charge if idle else info.controls.battery_max_charge
        self.set_charge_idle(idle)
        self._e3dc.set_power_limits(enable=True,
                                    max_charge=max_charge,
                                    max_discharge=info.controls.battery_max_discharge,
                                    discharge_start=CONFIG.battery_min_dis_charge,
                                    keepAlive=True)
        self.set_wallbox_current(info.controls.wallbox_current)

    def teardown(self):
        self.set_charge_idle(CONFIG.default_idle_charge_active,
                             CONFIG.default_idle_charge_end)
        self._e3dc.set_power_limits(enable=True,
                                    max_charge=CONFIG.default_battery_max_charge,
                                    max_discharge=CONFIG.battery_max_discharge,
                                    discharge_start=CONFIG.battery_min_dis_charge,
                                    keepAlive=False)
        self.set_wallbox_current(max(CONFIG.wallbox_power_by_current.keys()))

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

    def set_wallbox_current(self, max_current):
        if max_current == 0:
            self.set_wallbox_max_current(0, max_current)
        else:
            self.set_wallbox_max_current(0, max_current)

    def set_wallbox_max_current(self, wb_index: int, max_current: int):
        _ = self.send_wallbox_request(wb_index,
                                      bytearray([0, 0, max_current, 0, 0, 0]))

    def send_wallbox_request(self, wb_index: int, extern_data: bytearray) -> object:
        param_1 = [
            ("WB_EXTERN_DATA", "ByteArray", extern_data),
            ("WB_EXTERN_DATA_LEN", "UChar8", len(extern_data))
        ]
        return self.send("WB_REQ_DATA",
                         [
                             ("WB_INDEX", "UChar8", wb_index),
                             ("WB_REQ_SET_PARAM_1", "Container", param_1)
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
        opts, _ = getopt.getopt(argv, "vdn:w:it:", ["verbose", "dry-run", "num-loops=", "wait=", "info", "tag="])
    except getopt.GetoptError:
        print('main.py [--verbose] [--dry-run] [--num-loops=n] [--wait=seconds] | [--info] | [--tag=TAG]')
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

    if loop_action is None:
        def loop_action(s10): S10.update(s10, dry_run)
        if not dry_run:
            final_action = S10.teardown

    s10 = S10()
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
