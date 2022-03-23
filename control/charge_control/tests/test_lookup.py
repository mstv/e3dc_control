from ..charge_control import _lookup


def test_lookup():
    HIGH = 16
    MID = 12
    LOW = 8
    POWER_BY_CURRENT = {HIGH: 11000, MID: 7000, LOW: 2000}
    if True:
        assert _lookup(POWER_BY_CURRENT[HIGH] * 2, POWER_BY_CURRENT) == HIGH
        assert _lookup(POWER_BY_CURRENT[HIGH] + 1, POWER_BY_CURRENT) == HIGH
        assert _lookup(POWER_BY_CURRENT[HIGH] + 0, POWER_BY_CURRENT) == HIGH
        assert _lookup(POWER_BY_CURRENT[HIGH] - 1, POWER_BY_CURRENT) == MID
        assert _lookup(POWER_BY_CURRENT[MID] + 1, POWER_BY_CURRENT) == MID
        assert _lookup(POWER_BY_CURRENT[MID] + 0, POWER_BY_CURRENT) == MID
        assert _lookup(POWER_BY_CURRENT[MID] - 1, POWER_BY_CURRENT) == LOW
        assert _lookup(POWER_BY_CURRENT[LOW] + 1, POWER_BY_CURRENT) == LOW
        assert _lookup(POWER_BY_CURRENT[LOW] + 0, POWER_BY_CURRENT) == LOW
        assert _lookup(POWER_BY_CURRENT[LOW] - 1, POWER_BY_CURRENT) == 0
        assert _lookup(0, POWER_BY_CURRENT) == 0
        assert _lookup(-1, POWER_BY_CURRENT) == 0
        assert _lookup(POWER_BY_CURRENT[HIGH] * -2, POWER_BY_CURRENT) == 0
