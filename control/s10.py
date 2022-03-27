from array import array
from charge_control import ChargeControl, CONFIG
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
        # previous control state for change detection
        self._controls = None
        self._idle_active = None
        self._idle_end = None

    def get_info(self) -> Info:
        data = self._e3dc.poll(keepAlive=True)
        pvi_data = self._e3dc.get_pvi_data(keepAlive=True)
        solar_data = pvi_data['strings']
        dt_utc = data['time']
        measurements = Measurements(solar=data['production']['solar'],
                                    house=data['consumption']['house'],
                                    wallbox=data['consumption']['wallbox'],
                                    soc=data['stateOfCharge'],
                                    utc=dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600)
        info = Info(dt_utc,
                    measurements,
                    solar_delta=int(solar_data[0]['power'] - solar_data[1]['power']),
                    batt=data['consumption']['battery'],
                    grid=data['production']['grid'],
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

        if verbose:
            print(solar_data)

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
        self.set_idle(idle)
        self._e3dc.set_power_limits(enable=True,
                                    max_charge=max_charge,
                                    max_discharge=info.controls.battery_max_discharge,
                                    discharge_start=CONFIG.battery_min_dis_charge,
                                    keepAlive=True)

    def teardown(self):
        self.set_idle(CONFIG.default_idle_charge_active,
                      CONFIG.default_idle_charge_end)
        self._e3dc.set_power_limits(enable=True,
                                    max_charge=CONFIG.default_battery_max_charge,
                                    max_discharge=CONFIG.battery_max_discharge,
                                    discharge_start=CONFIG.battery_min_dis_charge,
                                    keepAlive=False)

    def set_idle(self, active: bool, end: array = [23, 59]) -> bool:
        if self._idle_active is active and self._idle_end == end:
            return False
        self._idle_active = active
        self._idle_end = end
        try:
            print(f"SETTING IDLE = {active} {end}")
        except:
            pass  # ignore exceptions on exception exit
        start = [0, 0]
        d_end = [0, 1]
        idle_periods = \
            {
                "idleCharge":
                [
                    {
                        "day": 0, "start": start, "end": end, "active": active
                    },
                    {
                        "day": 1, "start": start, "end": end, "active": active
                    },
                    {
                        "day": 2, "start": start, "end": end, "active": active
                    },
                    {
                        "day": 3, "start": start, "end": end, "active": active
                    },
                    {
                        "day": 4, "start": start, "end": end, "active": active
                    },
                    {
                        "day": 5, "start": start, "end": end, "active": active
                    },
                    {
                        "day": 6, "start": start, "end": end, "active": active
                    }
                ],
                "idleDischarge":
                [
                    {
                        "day": 0, "start": start, "end": d_end, "active": False
                    },
                    {
                        "day": 1, "start": start, "end": d_end, "active": False
                    },
                    {
                        "day": 2, "start": start, "end": d_end, "active": False
                    },
                    {
                        "day": 3, "start": start, "end": d_end, "active": False
                    },
                    {
                        "day": 4, "start": start, "end": d_end, "active": False
                    },
                    {
                        "day": 5, "start": start, "end": d_end, "active": False
                    },
                    {
                        "day": 6, "start": start, "end": d_end, "active": False
                    }
                ]
            }
        self._e3dc.set_idle_periods(idle_periods, keepAlive=True)
        return True


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
