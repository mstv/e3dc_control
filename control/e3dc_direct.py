from array import array
from data import Info, Measurements
from datetime import datetime
from e3dc import E3DC


class E3dcDirect:
    def __init__(self, e3dc: E3DC):
        self._e3dc = e3dc
        # previously requested state for change detection
        self._idle_active = None
        self._idle_end = None

    # facade functions

    def get(self, tag: str) -> object:
        return self._e3dc.sendRequestTag(tag, keepAlive=True)

    def send_request(self, request: tuple):
        return self._e3dc.sendRequest(request, keepAlive=True)

    def get_battery_data(self):
        return self._e3dc.get_battery_data(keepAlive=True)

    def get_db_data(self):
        return self._e3dc.get_db_data(keepAlive=True)

    def get_idle_periods(self):
        return self._e3dc.get_idle_periods(keepAlive=True)

    def get_power_settings(self):
        return self._e3dc.get_power_settings(keepAlive=True)

    def get_pvi_data(self):
        return self._e3dc.get_pvi_data(keepAlive=True)

    def get_system_info(self):
        return self._e3dc.get_system_info(keepAlive=True)

    def get_system_status(self):
        return self._e3dc.get_system_status(keepAlive=True)

    def poll(self):
        return self._e3dc.poll(keepAlive=True)

    def poll_switches(self):
        return self._e3dc.poll_switches(keepAlive=True)

    def set_power_limits(self,
                         enable: bool,
                         max_charge: int,
                         max_discharge: int,
                         discharge_start: int):
        return self._e3dc.set_power_limits(enable=enable,
                                           max_charge=max_charge,
                                           max_discharge=max_discharge,
                                           discharge_start=discharge_start)

    # control functions

    def send(self, request: str, data: array) -> object:
        return self.send_request((request, "Container", data))

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
        status = self.get("EMS_REQ_SYS_STATUS")

        wb = self.get_wb_info()
        wb_status = wb['status']
        wb_solar = wb['solar']
        car_connected = wb_status['plugged'] and wb_status['locked']
        car_may_charge = not wb_status['canceled'] and car_connected
        info = Info(dt_utc=datetime.utcfromtimestamp(utime),
                    measurements=measurements,
                    solar_delta=solar_delta,
                    batt=batt,
                    grid=grid,
                    status=status,
                    car_connected=car_connected,
                    car_may_charge=car_may_charge,
                    car_charging=wb_status['charging'],
                    car_max_current=wb_status['max A'],
                    car_soc=wb_solar[2],
                    car_total=wb_solar[5],
                    car_grid=wb['grid'][0])
        return info

    def get_solar_power(self, pvi_index: int, pv_string_index: int) -> float:
        power = self.send("PVI_REQ_DATA",
                          [
                              ("PVI_INDEX", "Uint16", pvi_index),
                              ("PVI_REQ_DC_POWER", "Uint16", pv_string_index),
                          ])
        return power[2][1][2][1][2]

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

    def set_battery_to_car_mode(self, enabled: bool):
        _ = self.send_request(
            ('EMS_REQ_SET_BATTERY_TO_CAR_MODE', "UChar8", 1 if enabled else 0))

    def set_charge_idle(self, active: bool, end: array = [23, 59]) -> bool or None:
        if self._idle_active is active and self._idle_end == end:
            return None
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
