"""开发用工具类/函数"""

import functools
import asyncio
import os
import sys
import time
import weakref
from collections import UserList, UserDict, defaultdict
from contextlib import contextmanager, nullcontext
from enum import EnumMeta, Enum
import random
from typing import (
    Tuple, Optional, Dict,
    List, Union, Callable, Any,
    TypeVar, MutableMapping, Container,
    Iterator, Iterable, DefaultDict,
)
from itertools import groupby, count

from cachetools.keys import hashkey
from loguru import logger
import pandas as pd

from deepfos.lib.constant import RE_DIMNAME_PARSER, ACCEPT_LANS, UNSET


FORCE_POP = [
    'deepfos.element.datatable',
    'deepfos.db.mysql',
    'deepfos.db.clickhouse',
    'deepfos.lib.subtask',
]

# -----------------------------------------------------------------------------
# typing
KT = TypeVar('KT')
VT = TypeVar('VT')


# -----------------------------------------------------------------------------
# core
def unpack_expr(dim_expr, silent=False) -> Tuple[Optional[str], str]:
    """匹配出维度表达式的维度名和表达式

    Args:
        dim_expr: 维度表达式
        silent: 不符合格式时是否报错

    Returns:
        维度名和表达式

    Raises:
        当维度表达式参数缺失时，抛出异常 `ValueError`

    """
    rslt = RE_DIMNAME_PARSER.match(dim_expr)
    if rslt:
        return rslt.group('name'), rslt.group('body')
    elif silent:
        return None, dim_expr
    else:
        raise ValueError("Failed to resolve dimension name from given expression.")


def dict_to_expr(
    dict_: Dict[str, Union[List[str], str]],
    hierarchy: str = None,
) -> str:
    """字典转化为维度表达式

    Args:
        dict_: 维度名 -> 维度成员(成员列表)
        hierarchy: 层级关系

    Returns:
        维度表达式

    >>> dict_to_expr({
    ...     "Year": ['2021', '2022'],
    ...     "Entity": 'TotalEntity',
    ...     "Version": "Base(NoVersion,0)"
    ... })
    'Year{2021;2022}->Entity{TotalEntity}->Version{Base(NoVersion,0)}'
    >>> dict_to_expr({
    ...     "Year": ['2021', '2022'],
    ...     "Entity": 'TotalEntity',
    ... }, hierarchy='Base')
    'Year{Base(2021,0);Base(2022,0)}->Entity{Base(TotalEntity,0)}'
    """
    exprs = []
    if hierarchy is not None:
        template = hierarchy + "({mbr},0)"
    else:
        template = "{mbr}"

    for dim, mbr in dict_.items():
        if isinstance(mbr, str):
            body = template.format(mbr=mbr)
        else:
            body = ";".join(template.format(mbr=m) for m in mbr)
        exprs.append(f"{dim}{{{body}}}")

    return '->'.join(exprs)


def expr_to_dict(
    expr: str
) -> Dict[str, str]:
    """维度表达式转化为字典

    Args:
        expr: 维度表达式

    Returns:
        字典

    >>> d = expr_to_dict('Year{Base(2021,0);Base(2022,0)}->Entity{Base(TotalEntity,0)}')
    >>> d == {
    ...    'Year': 'Base(2021,0);Base(2022,0)',
    ...    'Entity': 'Base(TotalEntity,0)'
    ... }
    True
    >>> expr = 'Year{Base(2021,0);Base(2022,0)}->Entity{Base(TotalEntity,0)}'
    >>> expr == dict_to_expr(expr_to_dict(expr))
    True
    """
    return dict(unpack_expr(ex, silent=False) for ex in expr.split('->'))


def get_ignore_case(
    dict_: Dict[str, VT],
    key: str,
    default: Any = UNSET
) -> VT:
    """类似于 ``dict.get``，但忽略大小写

    仅在字典很小时推荐使用。
    会首先创建一个和待查字典相比key小写，value相同的字典。
    再在创建出的字典中执行查询。

    Args:
        dict_: 查询的字典
        key: 查询的键
        default: 查询不到时返回的默认值

    Returns:
        在字典中 ``key`` 对应的值

    """
    if key in dict_:
        return dict_.get(key)

    lower_case_dict = {}
    for k, v in dict_.items():
        if not isinstance(k, str):
            continue
        lower_case_dict[k.lower()] = v

    if default is UNSET:
        return lower_case_dict[key.lower()]
    else:
        return lower_case_dict.get(key.lower(), default)


def _concat_url_single(head: str, tail: str):
    slash_count = 0
    if head.endswith('/'):
        slash_count += 1
    if tail.startswith('/'):
        slash_count += 1

    if slash_count == 0:
        return head + '/' + tail
    elif slash_count == 1:
        return head + tail
    else:
        return head[:-1] + '/' + tail[1:]


def concat_url(*parts: str):
    """拼接url"""
    return functools.reduce(_concat_url_single, parts)


def auto_call(caller):
    def deco(func):
        if asyncio.iscoroutinefunction(func):
            async def wrapper(self, *args, **kwargs):
                method = getattr(self, caller)
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
                setattr(self, func.__name__, func.__get__(self, self.__class__))
                return await func(self, *args, **kwargs)
        else:
            def wrapper(self, *args, **kwargs):
                method = getattr(self, caller)
                method()

                setattr(self, func.__name__, func.__get__(self, self.__class__))
                return func(self, *args, **kwargs)

        return functools.wraps(func)(wrapper)

    return deco


auto_setup = auto_call('setup')


@functools.total_ordering
class Inf:
    def __lt__(self, other):
        return False


class Wait:
    INF = Inf()

    def __init__(self, base: float, algo: str, maximum: float = None):
        if base < 0:
            raise ValueError("base < 0 !")
        self.base = base
        self.algo = algo
        if maximum is None:
            self.maximum = self.__class__.INF
        elif maximum < base:
            raise ValueError("maximum < base !")
        else:
            self.maximum = maximum

        self._counter = count().__next__

    def __iter__(self):
        algo = getattr(self.copy(), self.algo)

        while True:
            yield algo()

    def fixed(self):
        return self.base

    def exp_backoff(self):
        w = min(self.base, self.maximum)
        self.base *= 2
        return w

    def random(self):
        if self.maximum is self.__class__.INF:  # pragma: no cover
            return random.uniform(self.base, self.maximum)
        else:
            return random.uniform(0, self.base)

    def copy(self):
        return self.__class__(self.base, self.algo, self.maximum)


def retry(
    func=None,
    retries=2,
    wait: Union[int, Wait] = 5,
    catches=(Exception,),
    fix=None,
    name=None,
    reraise=True,
):
    """
    在被装饰函数执行失败时，重新执行

    Args:
        func: 待执行函数
        retries: 重试次数
        wait: 每次重试的时间间隔
        catches: 仅当函数抛出这些错误时重试
        fix: 可能的补救函数。如果指定，会在每次重试之前调用。
        name: 显示在日志中的函数名
        reraise: 超过重试次数后是否抛出错误

    """
    if func is None:
        return functools.partial(
            retry, retries=retries, wait=wait,
            catches=catches, fix=fix, name=name, reraise=reraise)

    if retries < 0:
        raise ValueError("retries must be positive.")

    if isinstance(wait, int):
        wait = Wait(wait, 'fixed')

    def record_retry(retried, at):
        if retried > 0 and fix is not None and callable(fix):
            fix()
        retried += 1
        logger.exception(
            f"Func: '{name or func.__qualname__}' failed. "
            f"Start {retried} times retry in {at} secs.")
        return retried

    if asyncio.iscoroutinefunction(func):
        async def run_func(*args, **kwargs):
            retried = 0
            waits = iter(wait)
            while True:
                try:
                    return await func(*args, **kwargs)
                except catches:
                    if retried >= retries:  # pragma: no cover
                        if reraise:
                            raise
                        else:
                            break
                    after = next(waits)
                    retried = record_retry(retried, after)
                    await asyncio.sleep(after)
    else:
        def run_func(*args, **kwargs):
            retried = 0
            waits = iter(wait)
            while True:
                try:
                    return func(*args, **kwargs)
                except catches:
                    if retried >= retries:  # pragma: no cover
                        if reraise:
                            raise
                        else:
                            break
                    after = next(waits)
                    retried = record_retry(retried, after)
                    time.sleep(after)

    return functools.wraps(func)(run_func)


def i_am(who):  # pragma: no cover
    """当前执行脚本主入口名"""
    arg0 = sys.argv[0]
    name, *_ = os.path.basename(arg0).rsplit('.', maxsplit=1)
    return name == who


def dict_to_key(dictionary: dict) -> str:
    """字典->键

    把不可哈希的字典转化成可哈希的键（字符串）。

    Args:
        dictionary: 需转化的字典

    Returns:
        键

    """
    kv_pairs = sorted(
        (k, v) for k, v in dictionary.items()
        if isinstance(v, str)
    )
    return "##".join("::".join(pair) for pair in kv_pairs)


def cachedclass(cache, key=hashkey, lock=None):
    """类的缓存装饰器

    基于类的初始化参数将类的实例进行缓存。同初始化参数将返回同一个实例。

    Note:
        相较于普通的缓存装饰器，这个装饰器保证装饰的结果仍然被识别为一个类，
        并且文档能够正常被sphinx获取。
    """

    # noinspection PyPep8Naming
    def decorator(clz):
        if cache is None:
            return clz

        elif lock is None:
            class wrapper:
                def __new__(cls, *args, **kwargs):
                    k = key(*args, **kwargs)
                    try:
                        return cache[k]
                    except KeyError:
                        pass  # key not found
                    v = clz(*args, **kwargs)
                    try:
                        cache[k] = v
                    except ValueError:  # pragma: no cover
                        pass  # value too large
                    return v

        else:
            class wrapper:
                def __new__(cls, *args, **kwargs):
                    k = key(*args, **kwargs)
                    try:
                        with lock:
                            return cache[k]
                    except KeyError:
                        pass  # key not found
                    v = clz(*args, **kwargs)
                    # in case of a race, prefer the item already in the cache
                    try:
                        with lock:
                            return cache.setdefault(k, v)
                    except ValueError:  # pragma: no cover
                        return v  # value too large

        extra_assign = [k for k in dir(clz) if not k.startswith('_')]

        return functools.update_wrapper(
            wrapper, clz,
            assigned=list(functools.WRAPPER_ASSIGNMENTS) + extra_assign,
            updated=[]
        )

    return decorator


class CIEnumMeta(EnumMeta):
    def __getitem__(cls, name):
        try:
            if isinstance(name, cls):
                return name
            if not isinstance(name, str):
                raise KeyError(name)

            return cls._member_map_[name.casefold()]
        except KeyError:
            choices = f"[{', '.join(cls.__members__)}]"
            raise KeyError(
                f"{cls.__name__}: {name!r} is not valid. "
                f"Possible choices are: {choices}") from None


class CIEnum(str, Enum, metaclass=CIEnumMeta):
    """大小写非敏感的枚举类

    经常用于入参为一组可选字符串的情况。
    可以简化参数检查逻辑代码的书写。
    当入参不支持时，提供友好的报错提示。

    >>> class Flag(CIEnum):
    ...     zero = 'zero'
    ...     negative = 'negative'
    ...     positive = 'positive'
    >>> def example(flag: Union[Flag, str]):
    ...     flag = Flag[flag]
    ...     if flag is Flag.zero:
    ...         return '0'
    ...     elif flag is Flag.negative:
    ...         return '-'
    ...     else:
    ...         return '+'
    >>> example('zero')
    '0'
    >>> example('Zero')
    '0'
    >>> example(Flag.negative)
    '-'
    >>> example('unknown')
    Traceback (most recent call last):
    ...
    KeyError: "Flag: 'unknown' is not valid. Possible choices are: [zero, negative, positive]"
    """


class FrozenClass(type):
    """不可修改的类

    元类，指定此元类的类将不可以设置属性，
    不可初始化。

    >>> class Frozen(metaclass=FrozenClass):
    ...     pass
    >>> Frozen.x = 1
    Traceback (most recent call last):
    ...
    NotImplementedError: Frozen is read-only.
    >>> Frozen()
    Traceback (most recent call last):
    ...
    NotImplementedError: Frozen cannot be instantiated.

    """
    def __str__(cls):
        return cls.__name__

    __repr__ = __str__

    def __setattr__(cls, key, value):
        raise NotImplementedError(f'{cls} is read-only.')

    def _init_(self, *args, **kwargs):
        raise NotImplementedError(f'{self.__class__} cannot be instantiated.')

    def __new__(mcs, name, base, namespace):
        namespace['__init__'] = mcs._init_
        cls = super().__new__(mcs, name, base, namespace)
        return cls


class SettableDescriptor:
    """限定写次数的描述符

    可读/写描述符，但是限定写次数。
    用于严格防止属性被使用者错误设置。

    Args:
        limit: 最大允许的写次数
        default: 属性默认值

    See Also:
        :obj:`SettableOnce`

    """
    def __init__(self, limit: int, default: Any = None):
        self._limit = limit
        self._value = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._value

    def __set__(self, instance, value):
        cnt_dict = instance.__dict__.setdefault(
            '__set_count__', {self._attr: 0}
        )
        cnt = cnt_dict[self._attr]

        if cnt >= self._limit:
            attr = f"{instance.__class__.__name__}.{self._attr}"
            if self._limit == 1:
                set_times = "once"
            else:  # pragma: no cover
                set_times = f"{cnt} times"
            raise RuntimeError(f"{attr} can only be set {set_times}.")
        self._value = value
        cnt_dict[self._attr] += 1

    def __set_name__(self, owner, name):
        self._attr = name


#: 只能赋值一次的属性
SettableOnce = functools.partial(SettableDescriptor, 1)


class LazyList(UserList, Container[KT]):
    """元素延迟初始化的列表

    元素的值只会在使用时被计算

    >>> def call(*args):
    ...     print('calc')
    ...     return sum(args)
    >>> ll = LazyList()
    >>> ll.append(call, 1, 2, 3)
    >>> ll.append(call, 4, 5, 6)
    >>> ll[0]
    calc
    6
    >>> ll[0]
    6

    See Also:
        :class:`LazyDict`

    """
    def __getitem__(self, item: int) -> KT:
        value, initialized = super().__getitem__(item)
        if not initialized:
            func, args, kwargs = value
            result = func(*args, **kwargs)
            self.data[item] = (result, True)
            return result
        else:
            return value

    def append(self, func: Callable, *args: Any, **kwargs) -> None:
        self.data.append(((func, args, kwargs), False))


class LazyDict(UserDict, MutableMapping[KT, VT]):
    """元素延迟初始化的字典

    元素的值只会在使用时被计算

    >>> def call(*args):
    ...     print('calc')
    ...     return sum(args)
    >>> ld = LazyDict()
    >>> ld['a'] = (call, 1, 2, 3)
    >>> ld['b'] = (call, 4, 5, 6)
    >>> ld['a']
    calc
    6
    >>> ld['a']
    6

    See Also:
        :class:`LazyList`

    """
    def __getitem__(self, item) -> VT:
        value, initialized = super().__getitem__(item)
        if not initialized:
            func, args = value
            result = func(*args)
            self.data[item] = (result, True)
            return result
        else:
            return value

    def __setitem__(self, key, value: Tuple):
        func, *args = value
        self.data[key] = ((func, args), False)


class Group:
    """
    维护唯一键名信息的集合
    """

    def __init__(self):
        self._keys = set()

    def add(self, k):
        self._keys.add(k)

    def delete(self, k):
        self._keys.remove(k)

    def keys(self):
        return self._keys

    def clear(self):
        self._keys.clear()


class GroupDict(UserDict, MutableMapping[KT, VT]):
    """
    传入唯一键名集合group，在新增字典的键名已存在在group中时，raise KeyError

    >>> shared_key_group = Group()
    >>> a = GroupDict(shared_key_group)
    >>> b = GroupDict(shared_key_group)
    >>> a['a'] = 1
    >>> a,b
    ({'a': 1}, {})
    >>> b['a'] = 2
    Traceback (most recent call last):
      ...
    KeyError: 'Key a has been existed in key_group. Cannot be added to current dict.'

    >>> a['a'] = 'a'
    >>> a
    {'a': 'a'}

    See Also:
        :class:`get_groupdicts`

    """

    def __init__(self, group: Group, **kwargs):
        super().__init__(**kwargs)
        self.group = group

    def __setitem__(self, key: KT, item: VT):
        if key in self.group.keys():
            if key in self.data:
                self.data[key] = item
            else:
                raise KeyError(f"Key {key} has been existed in key_group. Cannot be added to current dict.")
        else:
            self.data[key] = item
            self.group.add(key)

    def __delitem__(self, key: KT):
        self.group.delete(key)
        del self.data[key]


def get_groupdicts(n: int = 1) -> Tuple[GroupDict, ...]:
    """获取 n 个字典，其中的键值共享一个集合，在字典间保持唯一

    >>> a, b, c = get_groupdicts(3)
    >>> a,b,c
    ({}, {}, {})
    >>> a['a'] = 1
    >>> a,b,c
    ({'a': 1}, {}, {})
    >>> a.pop('a')
    1
    >>> b['a'] = 2
    >>> c['a'] = 3
    Traceback (most recent call last):
      ...
    KeyError: 'Key a has been existed in key_group. Cannot be added to current dict.'

    >>> a,b,c
    ({}, {'a': 2}, {})

    See Also:
        :class:`GroupDict`

    """
    group = Group()
    return tuple(GroupDict(group=group) for _ in range(n))


class ConcealableAttr:
    """可隐藏变量

    可读/写描述符，调用 :meth:`expose` 后会暴露变量，
    是该变量可访问。调用 :meth:`conceal` 则会隐藏变量，
    此时访问会引发 :class:`AttributeError`。

    典型应用场景：
        有一个属性值仅在特定上下文中有意义，为了防止在其他
        代码中意外访问到该变量而产生难以debug的错误，可以在
        进入上下文前将该变量暴露，退出上下文时将该变量隐藏。

    >>> class T:
    ...     attr = ConcealableAttr("test")
    >>> t = T()
    >>> T.attr.expose(t)
    >>> t.attr
    'test'
    >>> T.attr.conceal(t)
    >>> t.attr
    Traceback (most recent call last):
     ...
    AttributeError: Attribute 'attr' is concealed.
    """
    def __init__(self, default=None):
        self._value = default
        self.__conceal = weakref.WeakKeyDictionary()

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.__conceal.get(instance, True):
            raise AttributeError(f"Attribute '{self._attr}' is concealed.")
        return self._value

    def __set__(self, instance, value):
        self._value = value

    def __set_name__(self, owner, name):
        self._attr = name

    def conceal(self, inst):
        """隐藏变量"""
        self.__conceal[inst] = True

    def expose(self, inst):
        """暴露变量"""
        self.__conceal[inst] = False


class MultiKeyDict(MutableMapping[KT, VT]):
    """分组字典

    多个key对应一个值，同值的key属于一组，遍历时
    只有“组长”会作为key出现。

    >>> mkd = MultiKeyDict()
    >>> mkd['group1'] = 1
    >>> mkd['v1', 'group1'] = 1
    >>> mkd['v2', 'group1'] = 1
    >>> mkd['v3', 'group2'] = 2
    >>> mkd['v4', 'group2'] = 2
    >>> list(mkd.keys())
    ['group1', 'group2']
    >>> list(mkd.items())
    [('group1', 1), ('group2', 2)]
    >>> mkd['v1']
    1
    >>> mkd['group1']
    1
    >>> 'v3' in mkd
    True

    """
    def __init__(self, *args, **kwargs):
        self.data = dict(*args, **kwargs)
        #: key -> 对应的group
        self._key_group = {}

    def __iter__(self) -> Iterator[KT]:
        return self.data.__iter__()

    def __len__(self) -> int:
        return self.data.__len__()

    def __getitem__(self, k: KT) -> VT:
        return self.data.__getitem__(self._key_group[k])

    def __delitem__(self, v: KT) -> None:
        del self._key_group[v]

    def __setitem__(self, k: Union[Tuple[KT, KT], KT], v: VT) -> None:
        if isinstance(k, tuple):
            key, group = k
        else:
            key = group = k
        self._key_group[key] = group
        if group not in self._key_group:
            self._key_group[group] = group
        return self.data.__setitem__(group, v)

    def __str__(self):
        def item_gen():
            for key, group in groupby(self._key_group.items(), lambda x: x[1]):
                keys = [item[0] for item in group]
                yield f'{keys}: {self.data[key]!r}'

        return "{" + ', '.join(item_gen()) + "}"


def get_language_key_map(language_keys: Dict[str, str]):
    prefix = 'language_'
    lan_map = {}

    for lan in ACCEPT_LANS:
        key = prefix + lan.replace('-', '_')
        lan_map[lan] = language_keys.get(key, prefix + lan)

    return lan_map


def ask_for_kwargs(*keys: str, kwargs: Dict[str, Any]):
    for k in keys:
        if k not in kwargs:
            raise TypeError(f"Missing required keyword argument: {k!r}")
        yield kwargs[k]


def dict_to_sql(
    dict_: Dict[str, Iterable[str]],
    eq: str,
    concat: str = 'and',
    bracket: bool = True,
):
    sql_list = []

    for k, v in dict_.items():
        if isinstance(v, str):
            v = [v]
        else:
            v = tuple(set(v))

        if len(v) == 1:
            sql = f"{k}{eq}{v[0]!r}"
        else:
            mbrs = ','.join(map(repr, v))
            sql = f"{k} in ({mbrs})"

        sql_list.append(sql)

    sql = f" {concat} ".join(sql_list)
    if bracket:
        return '(' + sql + ')'
    return sql


class ChunkAlert:
    def __call__(self, start: int, end: int, exc: Exception = None) -> None: ...


@contextmanager
def chunk_alert(
    start: int, end: int,
    before: ChunkAlert = None,
    after: ChunkAlert = None,
):
    try:
        if before is not None:
            try:
                before(start, end)
            except Exception:
                logger.warning('Error occurs while calling before_chunk.')
        yield
    except Exception as e:
        if after is not None:
            try:
                after(start, end, e)
            except Exception:
                logger.warning('Error occurs while calling after_chunk.')
        raise
    else:
        if after is not None:
            try:
                after(start, end)
            except Exception:
                logger.warning('Error occurs while calling after_chunk.')


def split_dataframe(data: pd.DataFrame, chunksize: int = None):
    nrows = len(data)
    if chunksize is None or chunksize > nrows:
        yield data
    elif chunksize <= 0:
        raise ValueError("chunksize must be greater than 0.")
    else:
        for i in range(0, nrows, chunksize):
            yield data.iloc[i: i + chunksize]


def split_dataframe_alert(
    data: pd.DataFrame,
    chunksize: int = None,
    before_chunk: ChunkAlert = None,
    after_chunk: ChunkAlert = None,
):
    no_alert = before_chunk is None and after_chunk is None

    nrows = len(data)
    if chunksize is None or chunksize > nrows:
        if no_alert:
            yield data, nullcontext()
        else:
            yield data, chunk_alert(0, nrows, before_chunk, after_chunk)
    elif chunksize <= 0:
        raise ValueError("chunksize must be greater than 0.")
    else:
        for i in range(0, nrows, chunksize):
            if no_alert:
                yield data.iloc[i: i + chunksize], nullcontext()
            else:
                yield (
                    data.iloc[i: i + chunksize],
                    chunk_alert(i, min(i + chunksize, nrows), before_chunk, after_chunk)
                )


def find_str(
    target: str,
    candidates: Iterable[str],
    ignore_case: bool = False
) -> Union[None, str]:
    """查找目标字符串

    >>> find_str('foo', ['foo', 'bar'])
    'foo'
    >>> find_str('foo', ['Foo', 'bar']) is None
    True
    >>> find_str('foo', ['Foo', 'bar'], ignore_case=True)
    'Foo'
    """

    if ignore_case:
        match = lambda x, y: x.lower() == y.lower()
    else:
        match = lambda x, y: x == y

    for candidate in candidates:
        if match(target, candidate):
            return candidate


def to_version_tuple(ver: Union[float, str], max_split: int = 1):
    """返回版本元组

    Args:
        ver: 表示版本的字符串或数字，例如'1.0'，'1_0'，1.0
        max_split: 以'.'和'_'分割的最大次数，如为-1，则无限制

    Returns:
        形如(1, 0)的版本元组
    """
    if isinstance(ver, float):
        ver = str(ver)
    version_parts = ver.replace('.', '_').split('_', max_split)
    version_list = [int(part) if part.isdigit() else 0 for part in version_parts]
    return tuple(version_list)


def repr_version(version: Tuple, splitter='.'):
    """显示version信息"""
    return splitter.join([str(e) for e in version])


async def fetch_all_pages(
    fn,
    count_getter,
    page_no_key,
    page_size_key,
    page_size
):
    cur_page_no = count(1).__next__
    cnt = page_size

    rtn = []

    while cnt == page_size:
        kwargs = {
            page_no_key: cur_page_no(),
            page_size_key: page_size
        }
        r = await fn(**kwargs)
        cnt = count_getter(r)
        rtn.append(r)

    return rtn


def prepare_module():
    modules = list(sys.modules.keys())
    for key in modules:
        package, *_ = key.split('.', maxsplit=1)
        if package in FORCE_POP:
            sys.modules.pop(key)
            # for key added by LazyModule _load
            globals().pop(key, None)
        if any(key.startswith(module) for module in FORCE_POP):
            sys.modules.pop(key)
            # for key added by LazyModule _load
            globals().pop(key, None)


def cleanup_module():
    from deepfos.lib.filterparser import set_dt_precision, set_date_type_fields, set_dim_members
    set_dt_precision({})
    set_date_type_fields({})
    set_dim_members({})

    from deepfos.element import pyscript
    pyscript.WAITING_TASKS = 0
    pyscript.CONCURRENCY_KEY = None
    pyscript.GLOBAL_LOCK = None


class SimpleCounter:
    counts: DefaultDict[str, int]

    def __init__(self) -> None:
        self.counts = defaultdict(int)

    def nextval(self, name: str = 'default') -> int:
        self.counts[name] += 1
        return self.counts[name]

    def reset(self, name: str = 'default'):
        self.counts.pop(name, None)


class AliasGenerator(SimpleCounter):
    def get(self, hint: str = '') -> str:
        idx = self.nextval(hint)
        return f'{hint}{idx}'


def trim_text(content: str, limit: Union[int, None], appendor: str = '...') -> str:
    limit = limit or 0
    if 0 < limit < len(content):
        return f"{content[:limit]} {appendor}"
    else:
        return content
