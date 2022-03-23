from data import Config


def _get() -> Config:
    config = Config(
        variation_margin = 300,
        wallbox_power_by_current =
        {
            16: 10500,
            15:  9350,
            14:  8450,
            13:  7800,
            12:  6950,
            11:  6400,
            10:  5550,
             9:  4850,
             8:  2000
        },
        battery_max_discharge = 4500,
        battery_max_charge = 4500,
        battery_min_dis_charge = 65,
        solar_max = 11400,
        grid_max = None)
    config.grid_max = config.solar_max * 70 // 100
    return config


CONFIG = _get()
