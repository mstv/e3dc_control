from dataclasses import dataclass
from tools import MovingAverage


@dataclass
class Data:
    int: int
    float: float


def test_moving_average():
    avg = MovingAverage(4)
    avg.add(Data(20, .2))
    assert avg.get() == Data(20, .2)
    avg.add(Data(40, .4))
    assert avg.get() == Data(60 // 2, (.2 + .4) / 2)
    avg.add(Data(0, .0))
    assert avg.get() == Data(60 // 3, (.2 + .4 + .0) / 3)
    avg.add(Data(60, .6))
    assert avg.get() == Data(120 // 4, (.2 + .4 + .0 + .6) / 4)
    avg.add(Data(-20, -.2))
    assert avg.get() == Data(80 // 4, (.4 + .0 + .6 -.2) / 4)
