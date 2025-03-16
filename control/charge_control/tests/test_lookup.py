from ..charge_control import lookup_below, lookup_above


def test_lookup_below():
    HIGH = 16
    MID = 12
    LOW = 8
    POWER_BY_CURRENT = {HIGH: 11000, MID: 7000, LOW: 2000}
    if True:
        assert lookup_below(POWER_BY_CURRENT[HIGH] * 2, POWER_BY_CURRENT) == HIGH
        assert lookup_below(POWER_BY_CURRENT[HIGH] + 1, POWER_BY_CURRENT) == HIGH
        assert lookup_below(POWER_BY_CURRENT[HIGH] + 0, POWER_BY_CURRENT) == HIGH
        assert lookup_below(POWER_BY_CURRENT[HIGH] - 1, POWER_BY_CURRENT) == MID
        assert lookup_below(POWER_BY_CURRENT[MID] + 1, POWER_BY_CURRENT) == MID
        assert lookup_below(POWER_BY_CURRENT[MID] + 0, POWER_BY_CURRENT) == MID
        assert lookup_below(POWER_BY_CURRENT[MID] - 1, POWER_BY_CURRENT) == LOW
        assert lookup_below(POWER_BY_CURRENT[LOW] + 1, POWER_BY_CURRENT) == LOW
        assert lookup_below(POWER_BY_CURRENT[LOW] + 0, POWER_BY_CURRENT) == LOW
        assert lookup_below(POWER_BY_CURRENT[LOW] - 1, POWER_BY_CURRENT) == 0
        assert lookup_below(0, POWER_BY_CURRENT) == 0
        assert lookup_below(-1, POWER_BY_CURRENT) == 0
        assert lookup_below(POWER_BY_CURRENT[HIGH] * -2, POWER_BY_CURRENT) == 0


def test_lookup_above():
    HIGH = 16
    MID = 12
    LOW = 8
    POWER_BY_CURRENT = {HIGH: 11000, MID: 7000, LOW: 2000}
    if True:
        assert lookup_above(POWER_BY_CURRENT[HIGH] * 2, POWER_BY_CURRENT) == HIGH
        assert lookup_above(POWER_BY_CURRENT[HIGH] + 1, POWER_BY_CURRENT) == HIGH
        assert lookup_above(POWER_BY_CURRENT[HIGH] + 0, POWER_BY_CURRENT) == HIGH
        assert lookup_above(POWER_BY_CURRENT[HIGH] - 1, POWER_BY_CURRENT) == HIGH
        assert lookup_above(POWER_BY_CURRENT[MID] + 1, POWER_BY_CURRENT) == HIGH
        assert lookup_above(POWER_BY_CURRENT[MID] + 0, POWER_BY_CURRENT) == MID
        assert lookup_above(POWER_BY_CURRENT[MID] - 1, POWER_BY_CURRENT) == MID
        assert lookup_above(POWER_BY_CURRENT[LOW] + 1, POWER_BY_CURRENT) == MID
        assert lookup_above(POWER_BY_CURRENT[LOW] + 0, POWER_BY_CURRENT) == LOW
        assert lookup_above(POWER_BY_CURRENT[LOW] - 1, POWER_BY_CURRENT) == LOW
        assert lookup_above(0, POWER_BY_CURRENT) == 0
        assert lookup_above(-1, POWER_BY_CURRENT) == 0
        assert lookup_above(POWER_BY_CURRENT[HIGH] * -2, POWER_BY_CURRENT) == 0
