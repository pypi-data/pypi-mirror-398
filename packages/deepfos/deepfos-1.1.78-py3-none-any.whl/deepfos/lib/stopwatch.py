"""计时器"""

import functools
import time
from collections import OrderedDict
from deepfos.lib.utils import CIEnum
from loguru import logger


class TimeUnit(CIEnum):
    ns = 'ns'
    us = 'us'
    ms = 'ms'
    s = 's'
    m = 'm'
    h = 'h'


TIME_MAP = {
    'ns': 1,
    'us': 1_000,
    'ms': 1_000_000,
    's': 1_000_000_000,
    'm': 60_000_000_000,
    'h': 3_600_000_000_000,
}


class Stopwatch(object):
    """计时器

    Args:
        unit: 计时单位
        sink: 耗时信息的输出函数，默认为 ``logger.info``

    >>> watch = Stopwatch(unit='s', sink=print)
    >>> import time
    >>> with watch('[task - sleep]'):
    ...    time.sleep(0)
    [task - sleep]:0.00s
    """
    __slots__ = (
        'runtimes', 'start_stack', 'rec_count', 'name',
        '_unit_repr', '_unit', '_sink'
    )

    def __init__(self, unit: str = 'ns', sink=logger.info):
        self.runtimes = OrderedDict()
        self.start_stack = []
        self.rec_count = 0
        self.name = []
        self._unit_repr = _unit = TimeUnit[unit]
        self._unit = TIME_MAP[_unit]
        self._sink = sink

    def __call__(self, name=None):
        self.name.append(name)
        return self

    def __enter__(self):
        self.rec_count += 1
        self.start_stack.append(time.perf_counter_ns())

    def __exit__(self, exc_type, exc_val, exc_tb):
        time_gap = time.perf_counter_ns() - self.start_stack.pop(-1)
        if self.name and self.name[-1] is not None:
            key = self.name.pop(-1)
        else:
            key = f"task{self.rec_count}"
        self._sink(f"{key}:{time_gap / self._unit :.2f}{self._unit_repr}")
        self.runtimes[key] = time_gap

    def get_all_runtime(self):
        return list(self.runtimes.values())

    def clear(self):
        self.runtimes.clear()
        self.rec_count = 0

    def __repr__(self):
        return ', '.join(
            f"{name}:{t / self._unit :.2f}{self._unit_repr}"
            for name, t in self.runtimes.items()
        )


def stopwatch(func=None, unit: str = 's'):  # pragma: no cover
    if func is None:
        return functools.partial(stopwatch, unit=unit)

    watch = Stopwatch(unit)

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        with watch(func.__qualname__):
            rtn = func(*args, **kwargs)

        return rtn
    return wrap
