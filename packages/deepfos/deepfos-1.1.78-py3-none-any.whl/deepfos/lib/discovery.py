import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from functools import partial
from itertools import chain
from random import randint
from typing import Dict, List

from loguru import logger

from deepfos import OPTION
from deepfos.exceptions import APIRequestError
from deepfos.lib.asynchronous import evloop


async def poll_event(
    event: asyncio.Event,
    interval: int
):
    fut = asyncio.ensure_future(event.wait())

    async def poller():
        done, _ = await asyncio.wait(
            [fut],
            timeout=interval
        )
        return bool(done)

    while not (await poller()):
        yield


class AbstractServiceCache(ABC):
    @abstractmethod
    def add(self, item): pass

    @abstractmethod
    def delete(self, item): pass

    @abstractmethod
    def punish(self, item): pass

    @abstractmethod
    def reward(self, item): pass

    @abstractmethod
    def pick_best(self): pass

    @abstractmethod
    def __len__(self) -> int: pass

    @abstractmethod
    def __iter__(self): pass


class RankedCache(AbstractServiceCache):
    def __init__(self):
        self.__rank: Dict[str, int] = {}

    def add(self, item):
        """
        将instace增加到缓存中：对实例的add和update操作都适用
        """
        if item in self.__rank:
            return
        self.__rank[item] = 0

    def delete(self, item):
        """
        将instance从缓存中删除
        """
        if item not in self.__rank:
            return
        del self.__rank[item]

    def punish(self, item):
        if item not in self.__rank:
            return
        self.__rank[item] = -1

    def reward(self, item):
        if item not in self.__rank:
            return
        self.__rank[item] += 1

    def pick_best(self):
        ordered = sorted(self.__rank.items(), key=lambda x: x[1])
        return ordered[-1][0]

    def __len__(self):
        return len(self.__rank)

    def __bool__(self):
        return bool(self.__rank)

    def __iter__(self):
        return self.__rank.keys().__iter__()


class RoundRobinCache(AbstractServiceCache):
    def __init__(self):
        self._active: List[str] = []
        self._dead_time: Dict[str, int] = defaultdict(int)
        self._next_idx = -1

    def add(self, item):
        if item not in self._active:
            self._active.append(item)
        self._dead_time.pop(item, None)

    def delete(self, item):
        if item in self._active:
            self._active.remove(item)
        self._dead_time.pop(item, None)

    def _change_idx(self):
        # len(self._active) should be larger than 0 since pick-best only be called
        # when bool(self) is true
        self._next_idx = (self._next_idx + 1) % len(self._active)

    def punish(self, item):
        self._dead_time[item] += 1

        if self._dead_time[item] >= 3:
            if item in self._active:
                self._active.remove(item)
            self._dead_time.pop(item, None)

    def reward(self, item):
        self._dead_time.pop(item, None)

    def pick_best(self):
        self._change_idx()
        return self._active[self._next_idx]

    def __len__(self):
        return len(self._active)

    def __bool__(self):
        return bool(self._active)

    def __iter__(self):
        return self._active.__iter__()


class RandomCache(RoundRobinCache):
    def _change_idx(self):
        # len(self._active) should be larger than 0 since pick-best only be called
        # when bool(self) is true
        self._next_idx = randint(0, len(self._active) - 1)


CACHE_STRATEGY = {
    'ranked': RankedCache,
    'roundrobin': RoundRobinCache,
    'random': RandomCache,
}


class ServiceDiscovery(ABC):
    __ins__: Dict[str, 'ServiceDiscovery'] = {}

    def __init__(self, **kwargs):
        self.server_cache: Dict[str, AbstractServiceCache] = defaultdict(
            CACHE_STRATEGY.get(OPTION.discovery.cache_strategy, RankedCache)
        )
        self.interval = 5
        self._closed = None

    @property
    def closed(self):
        if self._closed is None:
            return True
        return self._closed.is_set()

    async def on_close(self):
        pass

    async def close(self):
        logger.opt(lazy=True).debug('Closing service discovery ...')
        if self._closed is not None:
            self._closed.set()
        await self.on_close()

    async def init(self):
        """will block util close is called"""
        if not self.closed:
            logger.warning(f"{self.__class__.__name__} already running.")
            return

        self._closed = closed = asyncio.Event()
        await self.on_startup()

        async for _ in poll_event(closed, self.interval):
            try:
                await self.on_interval()
            except Exception:  # noqa
                logger.exception('Exception occurs on interval.')

        logger.opt(lazy=True).debug(f'{self.__class__.__name__} stopped.')

    @abstractmethod
    async def on_interval(self): pass

    @abstractmethod
    async def on_startup(self): pass

    @abstractmethod
    async def update_service_cache(self, server_name: str): pass

    @abstractmethod
    async def update_instance_cache(self, server_name: str): pass

    def on_failure(self, server_name: str, addr):
        self.server_cache[server_name].punish(addr)

    def on_success(self, server_name: str, addr):
        self.server_cache[server_name].reward(addr)

    async def get_url(self, server_name: str, include_cb: bool = False):
        if server_name not in self.server_cache:
            await self.update_service_cache(server_name)

        if server_name not in self.server_cache:
            raise APIRequestError(f"Cannot find instance for server: {server_name}")

        server_list = self.server_cache[server_name]
        if not server_list:
            await self.update_instance_cache(server_name)

        if not server_list:
            raise APIRequestError(f"Cannot find instance for server: {server_name}")

        url = server_list.pick_best()

        if include_cb:
            return (
                partial(self.on_success, server_name, url),
                partial(self.on_failure, server_name, url),
                url
            )

        return url

    def sync_get_url(self, server_name: str, include_cb: bool = False):
        return evloop.run(self.get_url(server_name, include_cb))

    @classmethod
    def instantiate(cls):
        impl = OPTION.discovery.implementation

        if impl not in cls.__ins__:
            if impl == 'eureka':
                from deepfos.lib.eureka import Eureka
                cls.__ins__[impl] = Eureka
            elif impl == 'nacos':
                from deepfos.lib.nacos import Nacos
                cls.__ins__[impl] = Nacos
            elif impl == 'k8s':
                from deepfos.lib.k8s import K8s
                cls.__ins__[impl] = K8s

        return cls.__ins__[impl]

    @classmethod
    async def start(cls):
        await cls.instantiate().init()
        await asyncio.sleep(0)

    @classmethod
    async def stop(cls):
        for impl in cls.__ins__:
            if cls.__ins__[impl].closed:
                continue

            await cls.__ins__[impl].close()
