import contextvars
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import copy

from deepfos.lib.constant import UNSET
from deepfos.local import Proxy


class ThreadCtxExecutor(ThreadPoolExecutor):
    def __init__(
        self,
        max_workers=None,
        thread_name_prefix='',
        initargs=()
    ):
        self.context = contextvars.copy_context()
        super().__init__(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            initializer=self._set_context,
            initargs=initargs
        )

    def _set_context(self):
        for var, value in self.context.items():
            var.set(value)


class _Local:
    __slots__ = ('_thread_local', 'default')

    def __init__(self):
        self.default = None
        self._thread_local = {}

    def set_current(self, value):
        key = threading.get_ident()
        self._thread_local[key] = value

    def get_current(self):
        key = threading.get_ident()
        if key not in self._thread_local:
            self._thread_local[key] = copy.deepcopy(self.default)
        return self._thread_local[key]

    def set_default(self, value):
        if threading.get_ident() not in self._thread_local:
            self.default = value


class _LocalMemo:
    __slots__ = '_memo'

    def __init__(self):
        self._memo = defaultdict(_Local)

    def get(self, attr):
        if attr not in self._memo:
            raise AttributeError(attr)
        return self._memo[attr]

    def set(self, attr, value):
        tlocal = self._memo[attr]
        tlocal.set_default(copy.deepcopy(value))
        tlocal.set_current(value)

    def __contains__(self, item):
        return item in self._memo


class ThreadLocal:
    """定义线程隔离的变量"""
    def __init__(self):
        self.__dict__['_memo'] = _LocalMemo()

    def __setattr__(self, key, value):
        self._memo.set(key, value)

    def __getattr__(self, item):
        _local = self._memo.get(item)
        return _local.get_current()


class ParallelProxy(Proxy):
    def __init__(self, payload):
        object.__setattr__(self, '_ParallelProxy__result', UNSET)
        object.__setattr__(self, '_ParallelProxy__payload', payload)

    def __await__(self):
        coro = self.__payload
        return coro.__await__()

    def _get_current_object(self):
        if self.__result is not UNSET:
            return self.__result

        object.__setattr__(self, '_ParallelProxy__result', self.__payload.result())
        return self.__result


def compute(obj):
    try:
        return obj._get_current_object()    # noqa
    except AttributeError:
        return obj
