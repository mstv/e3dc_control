from dataclasses import dataclass, fields
from copy import deepcopy


class MovingAverage:
    def __init__(self, n: int):
        self._n = n
        self._queue = []

    @property
    def n(self):
        return self._n

    def add(self, data):
        if len(self._queue) >= self.n:
            self._queue.pop(0)
        self._queue.append(data)

    def get(self):
        n = len(self._queue)
        if n == 0:
            raise Exception("no average without data")
        if type(self._queue[0]) == int:
            return sum(self._queue) // n
        accu = deepcopy(self._queue[0])
        for data in self._queue[1:]:
            for field in fields(accu):
                setattr(accu, field.name,
                        getattr(accu, field.name) + getattr(data, field.name))
        for field in fields(accu):
            total = getattr(accu, field.name)
            if field.type == int:
                avg = total // n
            else:
                avg = total / n
            setattr(accu, field.name, avg)
        return accu
