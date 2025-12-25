"""装饰器"""

import threading
import functools
import warnings
import weakref
import inspect

from typing import Any, Callable, TypeVar, Tuple, Generic

from cachetools import LRUCache
from cachetools.keys import hashkey

from deepfos.cache import Manager
from deepfos.exceptions import eliminate_from_traceback
from deepfos.lib.asynchronous import evloop
from deepfos.lib.constant import UNSET
from deepfos.lib.utils import repr_version

__all__ = [
    'cached_property',
    'cached_class_property',
    'singleton',
    'flagmethod',
    'deprecated',
    'lru_cache',
]
F = TypeVar('F', bound=Callable[..., Any])
RT = TypeVar('RT')


# noinspection PyPep8Naming
@eliminate_from_traceback
class cached_property(Generic[RT]):  # pragma: no cover
    def __init__(self, func: Callable[[Any], RT]):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func
        self.attrname = None
        self.lock = threading.RLock()

    def __set_name__(self, owner, name):
        self.attrname = name

    def __get__(self, obj, cls) -> RT:
        if obj is None:
            return self

        try:
            cache = obj.__dict__
        except AttributeError:
            raise TypeError(
                f"No '__dict__' attribute on {type(obj).__name__!r} "
                f"instance to cache {self.attrname!r} property.") from None

        val = cache.get(self.attrname, UNSET)
        if val is UNSET:
            # If in different thread,
            # deadlock may happen when there are future properties in function
            # while being used in other thread in the same time
            if evloop.in_same_thread():
                with self.lock:
                    # check if another thread filled cache while we awaited lock
                    val = cache.get(self.attrname, UNSET)
                    if val is UNSET:
                        val = self.func(obj)
                        setattr(obj, self.attrname, val)
            else:
                val = self.func(obj)
                setattr(obj, self.attrname, val)
        return val


# noinspection PyPep8Naming
class cached_class_property(Generic[RT]):  # pragma: no cover
    def __init__(self, func: Callable[[Any], RT]):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func

    def __get__(self, obj, cls) -> RT:
        value = self.func(obj)
        # set attribute to class
        setattr(cls, self.func.__name__, value)
        return value


# noinspection PydanticTypeChecker
def singleton(cls):
    """单例"""
    cls.__new_original__ = cls.__new__
    singleton_lock = threading.Lock()

    @functools.wraps(cls.__new__)
    def singleton_new(cls_, *args, **kwargs):
        with singleton_lock:
            it = cls_.__dict__.get('__it__')
            if it is not None:
                return it

            cls_.__it__ = it = cls_.__new_original__(cls_)
            it.__init_original__(*args, **kwargs)
            return it

    cls.__new__ = singleton_new
    cls.__init_original__ = cls.__init__
    cls.__init__ = object.__init__
    return cls


class FlagMethod:
    """描述符。进出方法时设置flag。

    类似于 :func:`flagmethod`，但是支持嵌套调用。

    Args:
        flag: 作为标识的属性名
        method: 需要装饰的方法

    >>> def nested_flagmethod(flag):
    ...     def wrapper(method):
    ...         return FlagMethod(flag, method)
    ...     return wrapper

    >>> class Example:
    ...     def __init__(self):
    ...         self.flag = False
    ...
    ...     @nested_flagmethod('flag')
    ...     def foo(self, arg):
    ...         pass
    ...
    ...     def bar(self):
    ...         print(self.flag)
    ...
    >>> example = Example()
    >>> example.foo(example.bar())
    True
    >>> example.flag
    False

    """

    def __init__(self, flag: str, method):
        """

        Args:
            flag:
            method:
        """
        self.flag = flag
        self.method = method

    def __get__(self, instance, owner):
        if instance is None:
            return self
        setattr(instance, self.flag, True)
        self.obj = weakref.ref(instance)
        return self

    def __call__(self, *args, **kwargs):
        try:
            rslt = self.method(self.obj(), *args, **kwargs)
        finally:
            setattr(self.obj(), self.flag, False)
        return rslt


def flagmethod(flag: str) -> Callable[[F], F]:
    """进出方法时设置flag

    用于method的装饰器，当调用被装饰的方法时，会将 `self.flag`
    置为 `True`，结束调用时（包括异常退出），置为 `False`。

    Args:
        flag: 作为标识的属性名

    >>> class Example:
    ...     def __init__(self):
    ...         self.flag = False
    ...
    ...     @flagmethod('flag')
    ...     def foo(self, arg):
    ...         self.bar()
    ...         pass
    ...
    ...     @flagmethod('flag')
    ...     async def async_foo(self, arg):
    ...         self.bar()
    ...         pass
    ...
    ...     def bar(self):
    ...         print(self.flag)
    ...
    >>> example = Example()
    >>> example.foo(1)
    True
    >>> import asyncio
    >>> asyncio.run(example.async_foo(1))
    True
    >>> example.flag
    False

    """

    def deco(method):
        if inspect.iscoroutinefunction(method):
            async def wrapper(self, *args, **kwargs):
                setattr(self, flag, True)
                try:
                    rslt = await method(self, *args, **kwargs)
                finally:
                    setattr(self, flag, False)
                return rslt
        else:
            def wrapper(self, *args, **kwargs):
                setattr(self, flag, True)
                try:
                    rslt = method(self, *args, **kwargs)
                finally:
                    setattr(self, flag, False)
                return rslt
        return functools.wraps(method)(wrapper)

    return deco


def deprecated(
    replacement: str = None,
    version: Tuple[int, int, int] = None,
    reason: str = None
):
    """弃用方法装饰器

    Args:
        replacement: 弃用方法的替代方法名
        version: 开始弃用的版本
        reason: 弃用原因


    """

    def deco(method):
        msg = "This method is deprecated and will be removed in near future"
        docs = "\n" + " " * 8 + f".. deprecated:: {repr_version(version)}\n"

        if replacement:
            msg += f", use [{replacement}] instead."
            docs += f"\n" + " " * 12 + f"请使用 :meth:`{replacement}`\n"
        if reason:
            msg += f"Deprecated reason: {reason}. "
        if version:
            msg += f"Deprecated version: {repr_version(version)}. "

        if method.__doc__:
            method.__doc__ += docs
        else:
            method.__doc__ = docs

        if inspect.iscoroutinefunction(method):
            @functools.wraps(method)
            async def wrapper(*args, **kwargs):
                warnings.warn(msg, DeprecationWarning)
                return await method(*args, **kwargs)
        else:
            @functools.wraps(method)
            def wrapper(*args, **kwargs):
                warnings.warn(msg, DeprecationWarning)
                return method(*args, **kwargs)

        return wrapper

    return deco


def lru_cache(maxsize=128, cache_factory=LRUCache):
    assert isinstance(maxsize, int), 'Expected maxsize to be an integer'

    if maxsize == 0:
        def dummy_deco(fun):
            return fun
        return dummy_deco

    cache = Manager.create_cache(cache_factory, maxsize=maxsize)

    def deco_fun(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                key = hashkey(*args, **kwargs)

                if key in cache:
                    return cache[key]

                result = await func(*args, **kwargs)
                cache[key] = result
                return result
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                key = hashkey(*args, **kwargs)

                if key in cache:
                    return cache[key]

                result = func(*args, **kwargs)
                cache[key] = result
                return result

        return wrapper

    return deco_fun
