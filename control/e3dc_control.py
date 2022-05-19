from charge_control import ChargeControl, ControlsSM
from tools import MovingAverage
from data import BatteryCharge, Config, ControlInfo, ControlState, Measurements
from e3dc_direct import E3dcDirect
from print import one_line


class E3dcControl:
    def __init__(self, config: Config):
        self._control = ChargeControl(config)
        self._controls_sm = ControlsSM()
        self._ma_solar = MovingAverage(1)
        self._ma_house = MovingAverage(3)
        self._ma_wallbox = MovingAverage(2)
        self._ignore_consumption_counter = 0
        self._wb_on_utc = None

    @property
    def config(self) -> Config:
        return self._control.config

    def get_local_delta_hours(self, dt_utc) -> int:
        delta_seconds = self.config.timezone.utcoffset(dt_utc).total_seconds()
        return int(delta_seconds) // 3600

    def get_info(self, e3dc: E3dcDirect, ignore_consumption: bool = False) -> ControlInfo:
        info = e3dc.get_info()

        self._ma_solar.add(info.measurements.solar)
        if not ignore_consumption:
            self._ma_house.add(info.measurements.house)
            self._ma_wallbox.add(info.measurements.wallbox)
        averaged = Measurements(solar=self._ma_solar.get(),
                                house=self._ma_house.get(),
                                wallbox=self._ma_wallbox.get(),
                                soc=info.measurements.soc,
                                utc=info.measurements.utc)

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
            averaged=averaged,
            max_solar=self._control._charge_sm._max_solar,
            controls=None,
            control_state=ControlState.NotUpdated)
        return control_info

    def update(self, e3dc: E3dcDirect, dry_run: bool, battery_charge: BatteryCharge or int):
        if self._ignore_consumption_counter > 0:
            self._ignore_consumption_counter -= 1
        info = self.get_info(e3dc, self._ignore_consumption_counter > 0)

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
            elif controls_var.wallbox_current == 0 and self._wb_on_utc is not None:
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

        battery_max_charge_override = None
        if type(battery_charge) == int:
            battery_max_charge_override = int(battery_charge)
        elif battery_charge == BatteryCharge.Suppressed.value:
            battery_max_charge_override = 0
        elif battery_charge == BatteryCharge.Automatic.value:
            pass
        elif battery_charge == BatteryCharge.Default.value:
            battery_max_charge_override = self.config.default_battery_max_charge
        elif battery_charge == BatteryCharge.WallboxActive.value:
            if info.measurements.wallbox > 0 \
                    or info.car_connected and controls_var.wallbox_current == 0 \
                    or info.measurements.soc == 100:
                battery_max_charge_override = self.config.battery_max_charge
        elif battery_charge == BatteryCharge.Full.value:
            battery_max_charge_override = self.config.battery_max_charge
        else:
            raise NotImplementedError(f"BatteryCharge value {battery_charge}")

        if battery_max_charge_override is not None:
            controls_0.battery_max_charge \
                = controls_var.battery_max_charge \
                = battery_max_charge_override

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
        if any_changed:
            # ignore misleading drop/peak in house consumption
            self._ignore_consumption_counter = 4
        if changed.battery_max_charge or changed.battery_max_discharge:
            assert info.controls.battery_max_discharge == self.config.battery_max_discharge
            if info.controls.battery_max_charge == 0:
                e3dc.set_charge_idle(True)
            else:
                e3dc.set_power_limits(enable=True,
                                      max_charge=info.controls.battery_max_charge,
                                      max_discharge=info.controls.battery_max_discharge,
                                      discharge_start=self.config.battery_min_discharge)
                e3dc.set_charge_idle(False)
        may_charge = info.controls.wallbox_current > 0
        if changed.wallbox_current or (info.car_may_charge and not may_charge):
            if may_charge:
                e3dc.set_wallbox_max_current(0, info.controls.wallbox_current)
            if info.car_may_charge != may_charge:
                e3dc.toggle_wallbox_charging()
                e3dc.set_battery_to_car_mode(battery_to_car_mode)
                self._wb_on_utc = info.measurements.utc if may_charge else None

    def teardown(self, e3dc: E3dcDirect):
        e3dc.set_charge_idle(self.config.default_idle_charge_active,
                             self.config.default_idle_charge_end)
        e3dc.set_power_limits(enable=True,
                              max_charge=self.config.default_battery_max_charge,
                              max_discharge=self.config.battery_max_discharge,
                              discharge_start=self.config.battery_min_discharge)
        e3dc.set_wallbox_max_current(0,
                                     max(self.config.wallbox_power_by_current.keys()))
        e3dc.set_battery_to_car_mode(False)
