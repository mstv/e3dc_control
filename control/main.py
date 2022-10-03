from _config import CONFIG
from data import ChargeControlDirectives, ControlDirectives, Controls, ControlInfo, ControlState, Loop
from e3dc_control import E3dcControl
from e3dc_direct import E3dcDirect
from e3dc_factory import config_path, create_e3dc
import getopt
import os
from print import one_line, readable, filter
import sys
import time
import traceback
import yaml


# functions


def print_all(e3dc: E3dcDirect, verbose: bool):
    if verbose:
        print('poll')
    data = e3dc.poll()
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
    pvi_data = e3dc.get_pvi_data()
    # print(readable(e3dc._e3dc.get_pvis_data(keepAlive=True)))  # as 1-element array
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
    powerSettings = e3dc.get_power_settings()
    print(readable(powerSettings))
    # set_power_limits
    # set_powersave
    # set_weather_regulated_charge

    if verbose:
        print('get_system_status')
    print(readable(e3dc.get_system_status()))

    # 'deratePower', 'maxBatChargePower', 'maxBatDischargePower', 'installedBatteryCapacity'
    if verbose:
        print('get_system_info')
        print(readable(e3dc.get_system_info()))

        print('poll_switches (smart home)')
        print(readable(e3dc.poll_switches()))
        # set_switch_onoff

        print('get_idle_periods')
        print(readable(e3dc.get_idle_periods()))
        # set_idle_periods

        print('get_db_data (total sums)')
        print(readable(e3dc.get_db_data()))

        print('get_battery_data')
        print(readable(e3dc.get_battery_data()))
        # print(readable(e3dc._e3dc.get_batteries_data(keepAlive=True)))  # as 1-element array

    # broken
    # pmData = e3dc._e3dc.get_powermeter_data(keepAlive=True)
    # pmsData = e3dc._e3dc.get_powermeters_data(keepAlive=True)
    # print(readable(pmData))
    # print(readable(pmsData))

    for p, v in e3dc.get_wb_info().items():
        print(p, v)

    if verbose:
        print(solar_data)


def print_info(e3dc: E3dcDirect, verbose: bool):
    print_all(e3dc, verbose)
    info = e3dc.get_info()
    control_info = ControlInfo(
        dt_utc=info.dt_utc,
        measurements=info.measurements,
        solar_delta=info.solar_delta,
        batt=info.batt,
        grid=info.grid,
        status=info.status,
        car_connected=info.car_connected,
        car_may_charge=info.car_may_charge,
        car_charging=info.car_charging,
        car_max_current=info.car_max_current,
        car_soc=info.car_soc,
        car_total=info.car_total,
        car_grid=info.car_grid,
        battery_to_car=info.battery_to_car,
        averaged=info.measurements,
        max_solar=-1,
        controls=Controls(-1, -1, -1),
        control_state=ControlState.NotUpdated)
    if verbose:
        print('battery_to_car', control_info.battery_to_car)
    print(one_line(control_info))


def send_request(e3dc: E3dcDirect, tag: str):
    value = e3dc.get(tag)
    print(value)


def no_teardown(e3dc: E3dcDirect):
    pass


# main


def main(argv):
    global final_action
    final_action = no_teardown

    loop_action = None
    verbose = False
    dry_run = False
    num_loops = None  # infinite
    wait = 1

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
            def loop_action(e3dc): print_info(e3dc, verbose)
        if opt in ('-t', '--tag'):
            def loop_action(e3dc): send_request(e3dc, tag=arg)
            if num_loops is None:
                num_loops = 1
        if opt == '--wb':
            def loop_action(e3dc):
                data = arg.split(':')
                set_extern = True if len(data) < 3 else data[2] != '0'
                print(e3dc.send_wallbox_request(
                    0,
                    int(data[0]),
                    int(data[1]),
                    set_extern))
                for p in e3dc.get_wb()[2][1:]:
                    print(p)
                for p, v in e3dc.get_wb_info().items():
                    print(p, v)
            if num_loops is None:
                num_loops = 1

    if loop_action is None:
        control = E3dcControl(CONFIG)

        def loop_action(e3dc) -> bool:
            with open(os.path.join(config_path, 'e3dc_directives.yaml'), 'r') as directives_file:
                directives = yaml.safe_load(directives_file)
            directives = ControlDirectives(**directives)
            directives.charge_control = ChargeControlDirectives(**directives.charge_control)
            if directives.loop == Loop.ExitWithTeardown.value:
                return False
            elif directives.loop == Loop.BreakWithoutTeardown.value:
                print("breaking loop without teardown")
                global final_action
                final_action = no_teardown
                return False
            control.update(e3dc, dry_run, directives.charge_control)

        if not dry_run:
            final_action = control.teardown

    try:
        e3dc = None
        loop = 0
        while num_loops is None or loop < num_loops:
            loop += 1
            try:
                if e3dc is None:
                    e3dc = create_e3dc()
                if loop_action(e3dc) is False:
                    break
                loop_wait = wait
            except Exception as ex:
                e3dc = None
                loop_wait = 5
                print('ERROR:', ex)
                traceback.print_exc()
            if loop != num_loops:
                time.sleep(loop_wait)
    finally:
        final_action(e3dc)


main(sys.argv[1:])
