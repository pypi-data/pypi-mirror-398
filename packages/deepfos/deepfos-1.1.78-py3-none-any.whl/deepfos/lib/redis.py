"""Redis相关"""

from threading import Thread, Event
from typing import Optional

import redis
from redis.exceptions import LockError, LockNotOwnedError
from loguru import logger

from deepfos.lib.decorator import cached_property
from deepfos.options import OPTION
from deepfos.exceptions import LockAcquireFailed

__all__ = [
    'RedisLock',
    'RedisCli'
]


class _AbsRedisLock:  # pragma: no cover
    # noinspection PyUnusedLocal
    def __init__(
        self,
        key: str,
        redis_client: redis.Redis = None,
        renew_interval: int = 5,
        expire_sec: int = 10,
        raises: Exception = None,
        blocking_timeout: Optional[int] = 0
    ):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def acquire(self, timeout=0):
        pass

    def release(self):
        pass


def poll_event(
    event: Event,
    interval: int
):
    while not event.wait(interval):
        yield


class RedisLock:
    """通过Redis实现的锁对象

    Args:
        redis_client: Redis对象
        key: 锁名
        renew_interval: 刷新有效时间间隔，默认为5秒
        expire_sec: 有效时间，默认为10秒，需大于刷新间隔，否则刷新无效
        raises: 获取锁失败时抛出的错误，仅使用with时有效
        blocking_timeout: 获取锁的等待时间，默认为0，即不等待，为None时等待至获取到为止

    Notes:
        使用 ``with`` 获取锁时，如果获取失败，将直接报错。
        使用 :meth:`aquire` 获取时，将返回 :class:`bool` 类型，表示是否获取成功。

    .. admonition:: 示例

        .. code-block:: python

            with RedisLock('locked_key_a'):
                do_something()

            lock = RedisLock('locked_key_b')
            if lock.aquire():
                try:
                    do_something()
                finally:
                    lock.release()

    """
    def __init__(
        self,
        key: str,
        redis_client: redis.Redis = None,
        renew_interval: int = 5,
        expire_sec: int = 10,
        raises: Exception = None,
        blocking_timeout: Optional[int] = 0
    ):
        self._closed = None

        if renew_interval > expire_sec:
            raise ValueError("有效时间expire_sec需大于刷新间隔renew_interval，否则刷新无效。")

        self.redis_client = redis_client or RedisCli().client
        self.key = key
        self.blocking_timeout = blocking_timeout
        self.renew_interval = renew_interval
        self.expire_sec = expire_sec
        self.exc = raises

    @property
    def closed(self):
        if self._closed is None:
            return True
        return self._closed.is_set()

    @cached_property
    def lock(self):
        return self.redis_client.lock(
            name=self.key,
            timeout=self.expire_sec,
            blocking_timeout=self.blocking_timeout,
            thread_local=False
        )

    def __enter__(self):
        if not self.closed:
            logger.warning(f"RedisLock[key: {self.key}] already acquired.")
            return

        if self.lock.acquire(blocking=True):
            self._closed = Event()
            Thread(target=self.refresh_key, daemon=True).start()
            return self

        raise self.exc or LockAcquireFailed('Cannot aquire lock.')

    do_hold = __enter__

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self, timeout=0) -> bool:
        """获取当前锁

        Args:
            timeout: 获取等待时间，默认为0，即不等待，为None时一直等待至得到锁
        """
        return self.lock.acquire(blocking=True, blocking_timeout=timeout)

    def release(self):
        """释放当前锁"""
        self.stop_task()
        try:
            self.lock.release()
        except (LockError, LockNotOwnedError):
            logger.exception("")

    def refresh_key(self):
        self.lock.extend(self.expire_sec, replace_ttl=True)

        for _ in poll_event(self._closed, self.renew_interval):
            try:
                self.lock.extend(self.expire_sec, replace_ttl=True)
            except (LockError, LockNotOwnedError):
                break

    def owned(self):
        """key是否被当前锁拥有"""
        return self.lock.owned()

    def locked(self):
        """key是否被某个锁拥有"""
        return self.lock.locked()

    def stop_task(self):
        if self.closed:
            return

        self._closed.set()

    def __del__(self):
        self.stop_task()


if OPTION.general.dev_mode:
    RedisLock = _AbsRedisLock


class RedisCli:
    """Redis对象

    Args:
        redis_url: redis地址，格式: redis://[[username]:[password]]@[host]:[port]/0，
           若未提供，以OPTION.redis.url的值为默认值

    """
    _client: Optional[redis.Redis]

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url
        self._client = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(self.redis_url)
        return self._client

    def close(self):
        if self._client is not None:
            self._client.connection_pool.disconnect()
            self._client = None

    def __del__(self):
        self.close()

    def lock(
        self,
        key,
        renew_interval: int = 5,
        expire_sec: int = 10,
        blocking_timeout: Optional[int] = 0
    ) -> RedisLock:
        """
        提供设置了键名的redis维护锁

        Args:
            key:  键名
            renew_interval: 刷新有效时间间隔，默认为5秒
            expire_sec: 有效时间，默认为10秒，需大于刷新间隔，否则刷新无效
            blocking_timeout: 获取锁的等待时间，默认为0，即不等待，为None时等待至获取到为止

        Returns:
            设置了键名key的RedisLock对象

        .. admonition:: 示例

            .. code-block:: python

                rediscli = RedisCli()
                with rediscli.lock('test_key'):
                    ...

        """
        return RedisLock(key, self.client, renew_interval, expire_sec,
                         blocking_timeout=blocking_timeout)
