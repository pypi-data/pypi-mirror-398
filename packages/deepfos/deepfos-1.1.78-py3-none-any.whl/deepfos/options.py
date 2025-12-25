import configparser
import sys
import threading
import warnings
from enum import Enum
from functools import partial
from typing import (
    Iterable, TYPE_CHECKING, TypeVar, Optional,
    Callable, Any, Tuple, Union, List, overload,
    Generic, Type, Dict
)
from contextvars import ContextVar
import locale
import importlib
from loguru import logger

from deepfos.exceptions import (
    OptionTypeError, OptionValueError,
    OptionNotSetError, BaseOptionError,
)
from deepfos.config import USE_CONTEXT_OPTION


__all__ = ['OPTION', 'set_option', 'show_option']


# -----------------------------------------------------------------------------
# utils
class _Action(Enum):
    PASS = 0
    WARN = 1
    RAISE = 2


T_Stub = TypeVar('T_Stub')
T_SingleOrMulti = Union[T_Stub, Iterable[T_Stub]]
T_Opt = TypeVar('T_Opt')
T_Category = TypeVar('T_Category', bound='_Category')


# -----------------------------------------------------------------------------
# extra check / trigger / convertors
def _check_number_range(number, minimum=None, maximum=None):
    if minimum is not None:
        if number < minimum:
            raise ValueError(f"Value should be greater than {minimum}")
    if maximum is not None:
        if number > maximum:
            raise ValueError(f"Value should be less than {maximum}")


def _reset_level(level: str):
    logger.remove()
    if level.upper() == 'DISABLED':
        return
    logger.configure(
        handlers=[{
            "level": level.upper(),
            "sink": sys.stdout,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                      "<yellow>{process}</yellow> | "
                      "<yellow>{thread.name: <10}</yellow> | "
                      "<level>{level: <8}</level> | "
                      "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
                      " - "
                      "<level>{message}</level>",
        }],
    )


def _check_keys(value: dict, keys: Optional[Iterable[str]] = None):
    missing = [
        key for key in keys or []
        if key not in value
    ]
    if missing:
        raise KeyError(f'Missing keys: {missing}')


def _set_locale(value: dict):
    if 'language' in value:
        if _General.locale.unset:
            OPTION.general.locale = value['language']


def _normalize_locale(loc: str) -> str:
    normliazed_locale = locale.normalize(loc.replace('-', '_'))
    return normliazed_locale.split('.', maxsplit=1)[0]


def _load_module(path: str):
    if not path:
        return
    try:
        if path.endswith('.py'):
            path = path[:-3]
        package, sep, module = path.rpartition('.')
        if package:
            importlib.import_module('.' + module, package=package)
        else:
            importlib.import_module(module)
    except (ImportError, TypeError):
        logger.debug(f'Translation file not found in {path}')


def _activate_cache(value: bool):
    if value is True:
        logger.info('Element info cache activated.')


def _ensure_discovery_server_is_set(value):
    if not value:
        return

    impl = OPTION.discovery.implementation
    server_opt = {
        'eureka': OPTION.server.eureka,
        'nacos': OPTION.nacos.server,
        'k8s': OPTION.k8s.namespace,
    }[impl]

    if server_opt is None:
        raise RuntimeError(f"Missing server configure for {impl}")

    from deepfos.lib.discovery import ServiceDiscovery
    from deepfos.lib.asynchronous import evloop
    task = evloop.apply(ServiceDiscovery.start())
    task.die_in_peace = True
    # Will stop per python task because of evloop.stop
    evloop.register_shutdown(ServiceDiscovery.stop, is_coro=True)


def _maybe_set_discovery_enabled(value):
    if value:
        OPTION.discovery.enabled = True


# -----------------------------------------------------------------------------
# Option class
class _Option(Generic[T_Opt]):
    """
    配置项基类

    Args:
        default: 默认值
        val_type: 允许的类型, 多类型时传入tuple of type
        val_choices: 允许的取值
        write_warning: 当配置项被设定为某些值时，抛出对应的warning。
        on_set: 其他的校验，可传入callable，设定值将作为参数传入
        if_unset: 当配置项未设置就被使用时，对应的行为。

            - _Action.PASS: 忽略
            - _Action.WARN: 抛出warning
            - _Action.RAISE: 报错

        depends: 使用该参数依赖的校验函数。
        convertor: 配置值被真正设置前调用的转换函数
        deprecated: 配置项是否已废弃
        replacement: 当前配置项的替代配置，如果当前配置项被设置，
            替代配置也会同步该设置

    Example:
        .. code-block:: python

            class _CubeOption(_Category):
                key = _Option(False, val_type=bool,
                    write_warning=[(True: "warn！！！")])

        `key` 默认值为 `False`, 只能设置为 `bool` 类型。
        并且在设置为 `True` 时会提示warning信息。

    """
    def __init__(
        self,
        default: Optional[T_Opt],
        val_type: Optional[Type[T_Opt]] = None,
        val_choices: Tuple = (),
        write_warning: Optional[List[Tuple[Any, str]]] = None,
        on_set: T_SingleOrMulti[Callable[[Any], None]] = (),
        if_unset: _Action = _Action.PASS,
        depends: T_SingleOrMulti[Callable[[], None]] = (),
        convertor: Optional[Callable[[Any], Any]] = None,
        deprecated: bool = False,
        replacement: Optional['_Option'] = None,
    ):
        if isinstance(on_set, Iterable):
            self.extra_check = on_set
        else:
            self.extra_check = (on_set,)

        self.val_type = val_type
        self.val_choices = val_choices
        self.default = default
        self.warning = write_warning or []
        self.unset_action = if_unset
        if isinstance(depends, Iterable):
            self.depends = list(depends)
        else:
            self.depends = [depends]
        self.convertor = convertor
        self.unset = True
        self.deprecated = deprecated
        self.replacement = replacement
        self._deprecattion_warned = False

    def __set_name__(self, owner, name):
        self._var_name = '__' + name
        self._display_name = name

    @overload
    def __get__(self, instance: None, owner) -> '_Option':
        ...

    @overload
    def __get__(self, instance: Any, owner) -> T_Opt:
        ...

    def __get__(self, instance: Optional[Any], owner) -> Union['_Option', T_Opt]:
        if instance is None:
            return self

        if self.unset_action is _Action.RAISE:
            raise OptionNotSetError(f"Option '{instance}.{self}' has not yet been set.")
        elif self.unset_action is _Action.WARN:
            warnings.warn(
                f"Option '{instance}.{self}' has not yet been set.",
                stacklevel=2
            )

        while self.depends:
            self.depends.pop(-1)()

        self.depends = []

        try:
            rslt = getattr(instance, self._var_name)
        except AttributeError:
            rslt = self.default
            setattr(instance, self._var_name, rslt)
        return rslt

    def __set__(self, instance: Any, value: T_Opt):
        if self.convertor is not None:
            value = self.convertor(value)

        if self.val_type is not None:
            if not isinstance(value, self.val_type):
                raise OptionTypeError(
                    f"'{instance}.{self}' can only be set as type "
                    f"'{self.val_type}', not '{type(value)}'.")

        if self.val_choices:
            if value not in self.val_choices:
                raise OptionValueError(
                    f"'{instance}.{self}' can only be "
                    f"chosen from {self.val_type!r}.")

        for do_check in self.extra_check:
            do_check(value)

        for match, warning_msg in self.warning:
            if (callable(match) and match(value)) or value == match:
                warnings.warn(warning_msg, stacklevel=2)
        setattr(instance, self._var_name, value)
        logger.info(f"Set option: {instance}.{self}={value}")

        if self.deprecated and not self._deprecattion_warned:
            msg = f"Option: '{instance}.{self}' is deprecated."
            if self.replacement is not None:
                msg += f" Use '{instance}.{self.replacement}' instead."
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            self._deprecattion_warned = True

        if self.replacement is not None:
            self.replacement.__set__(instance, value)

        if self.unset_action is not _Action.PASS:
            self.unset_action = _Action.PASS
        self.unset = False

    def _quick_set(self, instance, value):
        setattr(instance, self._var_name, value)
        self.unset = False

    def __str__(self):
        return self._display_name


# -----------------------------------------------------------------------------
# Nested Option
class _Category:
    __id__ = ''

    def __get__(self, instance, owner):
        if instance is None:
            return self
        try:
            inst = getattr(instance, self._var_name)
        except AttributeError:
            inst = self.__class__()
            inst._name = self._name
            setattr(instance, self._var_name, inst)
        return inst

    def __set__(self, instance, value):
        raise TypeError("Category instance cannot be set.")

    def __set_name__(self, owner, name):
        self._name = name
        self._var_name = '__' + name

    def __str__(self):
        return self._name

    def set_default(self, env):
        if (id_ := self.__id__) not in env:
            return

        self.load_dict(env[id_])

    def load_dict(self, env: Dict[str, Any]):
        for k, v in env.items():
            if not hasattr(cls := self.__class__, k):
                continue

            option: _Option = getattr(cls, k)
            if (
                (val_type := option.val_type)
                and val_type is not str
            ):
                v = val_type(v)
            option.__set__(self, v)

    @property
    def _options(self):
        return {
            k: v for k, v in self.__class__.__dict__.items()
            if isinstance(v, _Option)
        }

    def show_options(self, option=None):
        name = self._name
        options = self._options

        if option is None:
            print(f"{name}\n{len(name)*'-'}")
            for opt in options:
                print(f"{opt}: {self._get_option(opt)}")
            print()
        else:
            if option not in options:
                raise KeyError(f"No such option: '{name}.{option}'")
            print(f"{name}.{option}: {self._get_option(option)}")

    def _get_option(self, option) -> _Option:
        try:
            return getattr(self, option)
        except BaseOptionError:
            return getattr(self.__class__, option).default

    def copy_from(self: T_Category, other: T_Category):
        if type(other) is not self.__class__:
            raise TypeError(
                f"Cannot make copy from instance of {type(other)}, "
                f"expect {self.__class__}.")

        if not hasattr(other, '_name'):
            raise ValueError(
                "Could not make a copy because target category is not "
                "properly initialized. Category is supposed to be a class variable.")

        setattr(self, '_name', getattr(other, '_name'))
        for attr, option in self._options.items():
            try:
                option._quick_set(self, getattr(other, attr))  # noqa
            except BaseOptionError:
                continue


class _Server(_Category):
    __id__ = 'server_url'

    base = _Option('http://web-gateway', val_type=str)
    app = _Option('http://app-server', val_type=str)
    account = _Option('http://seepln-account', val_type=str)
    system = _Option('http://system-server', val_type=str)
    space = _Option('http://space-server', val_type=str)
    platform_file = _Option('http://platform-file-server', val_type=str)
    deepfos_task = _Option('http://deepfos-task-server', val_type=str)
    eureka = _Option('http://eureka', val_type=str)

    def __get__(self, instance, owner) -> '_Server':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _API(_Category):
    __id__ = 'api'

    header = _Option({}, val_type=dict, on_set=_set_locale)
    io_sync = _Option(True, val_type=bool)
    verify_ssl = _Option(True, val_type=bool)
    timeout = _Option(180, val_type=int, on_set=partial(
        _check_number_range, minimum=0, maximum=7200))
    dump_on_failure = _Option(False, val_type=bool)
    dump_always = _Option(False, val_type=bool)
    #: server clock offset (in micro seconds)
    clock_offset = _Option(0, val_type=int)
    cache_element_info = _Option(False, val_type=bool, on_set=_activate_cache)

    def __get__(self, instance, owner) -> '_API':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _General(_Category):
    __id__ = 'general'

    log_level = _Option(
        'DISABLED', val_type=str, on_set=_reset_level,
        write_warning=[(lambda v: v.upper() == 'DISABLED', 'logger disabled!')])
    for_server_use = _Option(False, val_type=bool)
    use_eureka = _Option(True, val_type=bool, deprecated=True, on_set=_maybe_set_discovery_enabled)
    coro_graceful_timeout = _Option(5, val_type=int)
    task_info = _Option({}, val_type=dict, on_set=partial(_check_keys, keys=('task_id',)))
    dev_mode = _Option(False, val_type=bool)
    db_direct_access = _Option(False, val_type=bool)
    locale = _Option("en_US", val_type=str, convertor=_normalize_locale)
    preload_module = _Option(None, val_type=str, on_set=_load_module)
    socket_communication = _Option(False, val_type=bool)
    parallel_mode = _Option(False, val_type=bool)
    socket_name = _Option(None, val_type=str)
    preserve_concurrency = _Option(1, val_type=int)
    response_display_length_on_error = _Option(20000, val_type=int)

    def __get__(self, instance, owner) -> '_General':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _Module(_Category):
    __id__ = 'module'

    src_celeryapp = _Option(None, val_type=str)
    src_task = _Option(None, val_type=str)
    src_options = _Option(None, val_type=str)
    src_errors_classes = _Option(None, val_type=str)

    def __get__(self, instance, owner) -> '_Module':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _Redis(_Category):
    __id__ = 'redis'

    url = _Option('', val_type=str)

    def __get__(self, instance, owner) -> '_Redis':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _Edgedb(_Category):
    __id__ = 'edgedb'

    dsn = _Option('', val_type=str)
    timeout = _Option(30, val_type=int)

    def __get__(self, instance, owner) -> '_Edgedb':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _Boost(_Category):
    __id__ = 'boost'

    skip_internal_existence_check = _Option(False, val_type=bool)

    def __get__(self, instance, owner) -> '_Boost':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _ServiceDiscovery(_Category):
    __id__ = 'service_discovery'

    #: 是否使用服务发现功能（仅影响DynamicAPI）
    enabled = _Option(False, val_type=bool, on_set=_ensure_discovery_server_is_set)
    #: 服务注册发现使用的实现
    implementation = _Option('eureka', val_type=str, val_choices=('eureka', 'nacos', 'k8s'))
    #: 服务注册发现使用的缓存策略
    cache_strategy = _Option(
        'ranked',
        val_type=str,
        val_choices=('ranked', 'roundrobin', 'random')
    )
    #: 是否完全使用服务发现获取请求地址（包括Root API）
    take_over = _Option(False, val_type=bool)

    def __get__(self, instance, owner) -> '_ServiceDiscovery':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _Nacos(_Category):
    __id__ = 'nacos'

    server = _Option(None, val_type=str)
    cluster = _Option('DEFAULT', val_type=str)
    namespace = _Option('public', val_type=str)
    group = _Option('DEFAULT_GROUP', val_type=str)

    def __get__(self, instance, owner) -> '_Nacos':
        """defined to help ide"""
        return super().__get__(instance, owner)


class _Kubernets(_Category):
    """Nacos 相关配置"""

    namespace = _Option(None, val_type=str)

    def __get__(self, instance, owner) -> '_Kubernets':
        """defined to help ide"""
        return super().__get__(instance, owner)


# -----------------------------------------------------------------------------
# Options
class _GlobalOptions:
    general = _General()
    server = _Server()
    api = _API()
    redis = _Redis()
    module = _Module()
    boost = _Boost()
    discovery = _ServiceDiscovery()
    nacos = _Nacos()
    edgedb = _Edgedb()
    k8s = _Kubernets()

    def load_file(self, filepath):
        parser = configparser.ConfigParser()
        parser.read(filepath, encoding='utf8')
        self.load_env(parser)

    def load_env(self, env):
        for attr in self._categories.values():
            attr.set_default(env)

    @property
    def _categories(self):
        return {
            k: getattr(self, k) for k, v in self.__class__.__dict__.items()
            if isinstance(v, _Category)
        }

    def show_options(self, category=None):
        categories = self._categories

        if category is None:
            for ctgy in categories.values():
                ctgy.show_options()
        else:
            if category not in categories:
                raise KeyError(f"No such category: '{category}'.")
            categories[category].show_options()

    def __copy__(self):
        cp = self.__class__()
        for attr, category in self._categories.items():
            getattr(cp, attr).copy_from(category)
        return cp


def _get_nested(obj, nested_attr):
    category = obj

    *attrs, option = nested_attr.split('.')
    for attr in attrs:
        category = getattr(category, attr)

    return getattr(category.__class__, option), category


# noinspection PyProtectedMember
def set_option(option, value):
    """
    设定全局配置项。

    Args:
        option: 配置项名称
        value: 设定值

    Raises:
        ValueError: 配置项不存在时
        TypeError: 对目录值进行设定时

    Example:
        全局配置为多层配置，设定时需传入设定值的完整名称。

        .. code-block:: python

            set_option('system.app_id', 2)
            # 等价于
            OPTION.system.app_id = 2

    See Also:
        :meth:`show_option`

    """
    if USE_CONTEXT_OPTION:
        g_option = OPTION._option
    else:
        g_option = OPTION
    try:
        target, category = _get_nested(g_option, option)
        target.__set__(category, value)
    except AttributeError:
        raise ValueError(f"Option: {option!r} is not available.") from None


# noinspection PyProtectedMember
def show_option(category_or_option=None):
    """
    展示目前的配置项及其对应值

    Args:
        category_or_option: 需要展示目录或者具体的配置项，
            为 `None` 时显示全部配置项

    See Also:
        :meth:`set_option`

    """
    if category_or_option is None:
        OPTION.show_options()
        return
    if USE_CONTEXT_OPTION:
        assert isinstance(OPTION, _OptionCTX)
        g_option = OPTION._option
    else:
        g_option = OPTION
    try:
        option, category = _get_nested(g_option, category_or_option)
        category.show_options(str(option))
    except AttributeError:
        raise ValueError(f"Option: {category_or_option!r} is not available.") from None


_option_ctx: ContextVar[_GlobalOptions] = ContextVar('deepfos_global_option')


class _OptionCTX:
    if TYPE_CHECKING:
        general: _General
        server: _Server
        api: _API
        redis: _Redis
        module: _Module
        boost: _Boost
        discovery: _ServiceDiscovery
        nacos: _Nacos
        edgedb: _Edgedb

        def show_options(self, category=None):
            ...

    def __init__(self):
        self._create_at_main = threading.current_thread() is threading.main_thread()
        self._primary_opt = _GlobalOptions()
        self._token = _option_ctx.set(self._primary_opt)

    def create_local(self):
        self._token = _option_ctx.set(_GlobalOptions())

    @property
    def _option(self) -> _GlobalOptions:
        try:
            return _option_ctx.get()
        except LookupError:
            if (
                not self._create_at_main
                and threading.current_thread() is threading.main_thread()
            ):
                _option_ctx.set(self._primary_opt.__copy__())
                return _option_ctx.get()
            raise

    def __getattr__(self, item):
        return getattr(self._option, item)


OPTION: Union[_OptionCTX, _GlobalOptions]


if USE_CONTEXT_OPTION:
    OPTION = _OptionCTX()
else:
    OPTION = _GlobalOptions()
