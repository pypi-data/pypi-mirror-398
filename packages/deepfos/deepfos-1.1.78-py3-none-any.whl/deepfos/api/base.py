import enum
import json
import re
from importlib import import_module
from shlex import quote
from typing import (
    Union, Tuple, TYPE_CHECKING, Callable, List, Dict,
    get_args, get_origin, Optional, get_type_hints
)
from collections.abc import Awaitable
from deepfos.lib.decorator import cached_property
from urllib.parse import urlencode
from reprlib import repr

from requests.utils import CaseInsensitiveDict, to_key_val_list
from pydantic import BaseModel as PydanticBaseModel
from cachetools import TTLCache
from loguru import logger

from deepfos.cache import Manager, AppSeperatedLRUCache
from deepfos.api.models import compat_parse_obj_as as parse_obj_as
from deepfos.lib.httpcli import AioHttpCli
from deepfos.lib.utils import concat_url, retry, to_version_tuple, repr_version, trim_text
from deepfos.lib.asynchronous import evloop
from deepfos.lib.discovery import ServiceDiscovery
from deepfos.lib.constant import UNSET, RE_SYS_SERVER_PARSER
from deepfos.options import OPTION
from deepfos.exceptions import APIResponseError, APIRequestError

__all__ = [
    'DynamicRootAPI',
    'RootAPI',
    'ChildAPI',
    'get',
    'post'
]

T_DictPydanticModel = Union[dict, PydanticBaseModel]
VERSIONED_MODULE = "deepfos.api.V{version}.{name}"


class ContentType(str, enum.Enum):
    json = "json"
    bytes = "bytes"
    text = "text"


class RequestInfo:
    """请求参数wrapper，提供参数的展示，合并，构造功能"""
    _repr_attr = ['url', 'method', 'header', 'body']
    _setable_attr = _repr_attr + ['param', 'path']

    def __init__(
        self,
        method: str = None,
        url: str = None,
        body: T_DictPydanticModel = None,
        header: dict = None,
        param: T_DictPydanticModel = None,
        path: str = None,
    ):
        self._method = method
        self._url = url
        self._body = body
        self._header = header
        self._param = param
        self._path = path

    @staticmethod
    def parse_nested(nested_model):
        if not isinstance(nested_model, list):
            return nested_model
        parsed = []
        for model in nested_model:
            if isinstance(model, PydanticBaseModel):
                parsed.append(model.dict(by_alias=True))
            else:
                parsed.append(model)
        return parsed

    @property
    def url(self) -> str:
        """把 attr:`param` 拼接至 attr:`url` ，形成完整的请求地址"""
        if self._path:
            url = concat_url(self._url, self._path)
        else:
            url = self._url

        if param := self._param:
            if isinstance(param, PydanticBaseModel):
                param = param.dict(exclude_none=True)
                return f"{url.rstrip('/')}?{urlencode(param)}"
            else:
                param_list = []
                for k, v in param.items():
                    if v is not None:
                        if not isinstance(v, list):
                            param_list.append((k, v))
                        else:
                            param_list.extend((k, item) for item in v)
                if param_list:
                    url = f"{url.rstrip('/')}?{urlencode(param_list)}"
                return url
        return url

    @cached_property
    def method(self):
        return self._method.upper()

    @cached_property
    def body(self) -> Union[Dict, List]:
        if isinstance(self._body, PydanticBaseModel):
            return self._body.dict(by_alias=True, exclude_none=(self.method == 'GET'))
        return self.parse_nested(self._body)

    @cached_property
    def header(self) -> dict:
        return self._header

    def setdefault(
        self,
        key: str,
        value: Union[str, T_DictPydanticModel]
    ):
        """
        更新可写属性的值。仅在该值为None时被更新

        Args:
            key: 更新属性，必须在 :attr: _setable_attr 中
            value: 需要设置的值
        """
        if key not in self._setable_attr:
            return

        key = '_' + key
        attr = getattr(self, key)
        if attr is None:
            setattr(self, key, value)

    def __str__(self):  # pragma: no cover
        attr_str = []
        for attr in self._repr_attr:
            val = getattr(self, attr)
            if val is not None:
                attr_str.append(f"[{attr}: {repr(val)}]")

        return '\t\t'.join(attr_str)

    def update_default(self, request: Union[dict, 'RequestInfo']):
        """
        从其他 :class:`RequestInfo` 或者 :class:`dict` 中更新属性

        Tips:
            只会更新自身未设置的属性（即值为None的属性）

        Args:
            request: 更新数据源
        """
        if not request:
            return
        if isinstance(request, dict):
            kv_pairs = request.items()
        else:
            kv_pairs = request.__dict__.items()

        for k, v in kv_pairs:
            self.setdefault(k, v)

    def to_curl(self, header: Dict):  # pragma: no cover
        # Curlify not available for form-data
        if 'multipart/form-data' in header['Content-Type']:
            return

        parts = [
            ('curl', None),
            ('-X', self.method),
        ]

        for k, v in sorted(header.items()):
            parts += [('-H', '{0}: {1}'.format(k, v))]

        if self.body:
            if 'Content-Type' in header and 'application/json' in header['Content-Type']:
                body = json.dumps(self.body)
            else:
                body = self._encode_params(self.body)

            if isinstance(body, bytes):
                body = body.decode('utf-8')

            parts += [('-d', body)]

        parts += [(None, self.url)]

        flat_parts = []
        for k, v in parts:
            if k:
                flat_parts.append(quote(k))
            if v:
                flat_parts.append(quote(v))

        curl_str = ' '.join(flat_parts)

        if len(curl_str) > 200 and OPTION.general.dev_mode:
            with open('curl_string.txt', 'a') as fp:
                fp.write(f"{curl_str}\n")
        else:
            logger.debug(f"Curl command: {curl_str}")

    @staticmethod
    def _encode_params(data):
        """Encode parameters in a piece of data.

        Will successfully encode parameters when passed as a dict or a list of
        2-tuples. Order is retained if data is a list of 2-tuples but arbitrary
        if parameters are supplied as a dict.
        """

        if isinstance(data, (str, bytes)):
            return data
        elif hasattr(data, 'read'):
            return data
        elif hasattr(data, '__iter__'):
            result = []
            for k, vs in to_key_val_list(data):
                if isinstance(vs, str) or not hasattr(vs, '__iter__'):
                    vs = [vs]
                for v in vs:
                    if v is not None:
                        result.append(
                            (k.encode('utf-8') if isinstance(k, str) else k,
                             v.encode('utf-8') if isinstance(v, str) else v))
            return urlencode(result, doseq=True)
        else:
            return data

    def __hash__(self):
        return hash((self.url, self.method, json.dumps(self.header), json.dumps(self.body)))


class DummyDeco:
    """装饰器，用于给所有api方法添加标记，方法的替换在metaclass中进行"""

    def __init__(self, method):
        self.method = method

    def __call__(
        self,
        endpoint: str,
        resp_model: PydanticBaseModel = None,
        retries: int = 0,
        allow_none: bool = True,
        raise_false: bool = True,
        data_wrapped: bool = True,
    ):
        def execute(func):
            args = {
                '__method__': self.method,
                'endpoint': endpoint,
                'resp_model': resp_model,
                'retries': retries,
                'allow_none': allow_none,
                'raise_false': raise_false,
                'data_wrapped': data_wrapped,
            }
            setattr(func, '__api_meta__', args)
            return func

        return execute


api_cache = Manager.create_cache(AppSeperatedLRUCache, maxsize=128)


class Route:
    """装饰器，用于简化系统api的封装流程"""
    _RE_CONTENT_TYPE = re.compile(r'^\s*application/(?P<ctype>.*);.*')
    _RE_MULTI_TYPE = re.compile(r'^multipart/form-data; boundary=.*')

    def __init__(self, method: str, sync: bool):
        self.method = method
        self.sync = sync

    @staticmethod
    def resolve_actual_type(_type):
        origin = get_origin(_type)
        if origin is not Union:
            return _type

        args = get_args(_type)
        if len(args) != 2:
            return _type

        maybe_actual_type, await_wrapped_type = args
        wrapped_origin = get_origin(await_wrapped_type)
        if wrapped_origin is not Awaitable:
            return _type

        wrapped_type = get_args(await_wrapped_type)
        if len(wrapped_type) != 1:
            return _type
        if maybe_actual_type is not wrapped_type[0]:
            return _type
        return maybe_actual_type

    def __call__(
        self,
        endpoint: str,
        resp_model: PydanticBaseModel = None,
        retries: int = 0,
        allow_none: bool = True,
        raise_false: bool = True,
        data_wrapped: bool = True,
        content_type: Union[ContentType, str] = ContentType.json
    ):
        """
        装饰器主入口，同时是所有API接口的实际入口。

        Notes:
            这个函数很长，但这是出于性能考虑。由于所有请求都会经过这个函数，
            所以把所有调用的函数都inline处理了，尽管这不如提取出函数容易维护，
            但这是必须的。

        Args:
            endpoint: 请求地址末端路径
            resp_model: 接口的返回模型
            retries: 接口调用失败时的重试次数
            allow_none: 接口返回的data是否允许为None，如果允许，在返回None时，
                将不会试图把response.data解析成resp_model。一般来说，当接口
                返回status=True，data=None时使用。（这种情况一般由于接口编写不规范导致）
            raise_false: 当接口返回status为false时，是否抛出异常
            data_wrapped: 响应的数据是否被data字段包装

        函数调用可选参数:
            resp_model: 接口的返回模型，可覆盖装饰器的同名参数
            retries: 接口调用失败时的重试次数
            use_cache: 是否读取缓存，默认为false

        """

        # noinspection PyPep8Naming
        def execute(func):
            anno = func.__annotations__.get('return', resp_model)
            default_model = self.resolve_actual_type(anno)
            method = self.method
            is_get_request = method == 'get'
            REQUEST = AioHttpCli.get if is_get_request else AioHttpCli.post
            RE_CONTENT_TYPE = self._RE_CONTENT_TYPE

            async def do_request(ins, *args, **kwargs):
                # ---------------------------------------------------------------------
                # handle extra args (多余kwargs在此前pop)
                if 'resp_model' in kwargs:
                    model = kwargs.pop('resp_model')
                else:
                    model = default_model

                if 'content_type' in kwargs:
                    _content_type = ContentType(kwargs.pop('content_type'))
                else:
                    _content_type = content_type

                _retries = kwargs.pop('retries', retries)
                use_cache = kwargs.pop('use_cache', False)

                # ---------------------------------------------------------------------
                # get request info
                base_url = await ins.get_base_url()
                req = RequestInfo(url=concat_url(base_url, endpoint), method=method)
                req.update_default(func(ins, *args, **kwargs))
                url, body, ext_header = req.url, req.body, req.header
                raw_result = model is None

                if ext_header is None:
                    header = ins.header
                else:
                    header = CaseInsensitiveDict(ins.header, **ext_header)

                if use_cache:
                    if ((req_key := hash(req)), raw_result) in api_cache:
                        return api_cache[(req_key, raw_result)]

                if OPTION.api.dump_always:
                    req.to_curl(header)

                # ---------------------------------------------------------------------
                # send request
                if is_get_request:
                    logger.opt(lazy=True).debug(
                        "Sending request by [aiohttp]: GET {url} {params}",
                        url=lambda: url,
                        params=lambda: repr(body)
                    )
                    req_args = {
                        'url': url,
                        'params': body,
                        'headers': header
                    }
                else:
                    logger.opt(lazy=True).debug(
                        "Sending request by [aiohttp]: POST {url} {body}",
                        url=lambda: req.url,
                        body=lambda: repr(req.body)
                    )
                    if ext_header is None:
                        body_key = 'json'
                    else:
                        # ------------------------------------------------------------
                        # parse content type
                        if (ctype := header.get('content-type')) is None:
                            logger.warning('Missing content-type in request header.')
                        elif matched := RE_CONTENT_TYPE.match(ctype):
                            ctype = matched.group('ctype').lower()
                        elif self._RE_MULTI_TYPE.match(ctype):
                            ctype = 'data'
                        else:
                            logger.warning(f'Unknow content-type: {ctype}')

                        body_key = ctype if ctype in ('json', 'data') else 'body'

                    req_args = {
                        'url': url,
                        body_key: body,
                        'headers': header
                    }

                try:
                    if _retries > 0:
                        resp = await retry(
                            func=REQUEST, retries=_retries, name=func.__qualname__
                        )(**req_args)
                    else:
                        resp = await REQUEST(**req_args)
                except OSError as e:  # pragma: no cover
                    if not OPTION.api.dump_always and OPTION.api.dump_on_failure:
                        req.to_curl(header)

                    raise APIRequestError(e) from None

                # -----------------------------------------------------------------------------
                # parse response
                if _content_type is ContentType.bytes:
                    return await resp.read()

                text = await resp.text()
                if _content_type is ContentType.text:
                    return text

                err_code = None

                if not 200 <= (status_code := resp.status) < 300:
                    logger.opt(lazy=True).error(
                        "Call API: {url} failed because status code is not 2XX. "
                        "Detail: {text}.",
                        url=lambda: req.url,
                        code=lambda: status_code,
                        text=lambda: trim_text(text, OPTION.general.response_display_length_on_error),
                    )
                    flag, obj, err = False, None, f"[code: {status_code}] ErrMsg from server: {text}"

                else:
                    try:
                        resp = json.loads(text)
                        if data_wrapped:
                            if 'status' not in resp:
                                logger.opt(lazy=True).error(
                                    "Call API: {url} failed. "
                                    "Bad response because 'status' field is missing.",
                                    url=lambda: req.url,
                                )
                                flag, obj, err = False, None, "status field is missing."

                            elif resp['status'] is False:
                                logger.opt(lazy=True).warning(
                                    "Call API: {url} failed. "
                                    "Bad response because status is False. Detail: {text}.",
                                    url=lambda: req.url,
                                    text=lambda: trim_text(text, OPTION.general.response_display_length_on_error),
                                )
                                flag, obj, err = False, resp.get('data'), resp.get('message', text)
                                err_code = resp.get('code')

                            else:
                                flag, obj, err = True, resp.get('data'), None
                                err_code = resp.get('code')
                        else:
                            flag, obj, err = True, resp, None

                    except (TypeError, ValueError):
                        logger.exception(
                            f'Call API: {req.url} failed.'
                            f'Response << {text} >> cannot be decoded as json.')
                        flag, obj, err = False, text, 'Response cannot be decoded as json'

                if flag is False and raise_false:
                    if not OPTION.api.dump_always and OPTION.api.dump_on_failure:
                        req.to_curl(header)
                    raise APIResponseError(err, code=err_code)

                if raw_result or (allow_none and obj is None):
                    if use_cache:
                        api_cache[(hash(req), raw_result)] = obj
                    return obj

                try:
                    result = parse_obj_as(model, obj)
                    if use_cache:
                        api_cache[(hash(req), raw_result)] = result
                    return result
                except Exception:  # pragma: no cover
                    if not OPTION.api.dump_always and OPTION.api.dump_on_failure:
                        req.to_curl(header)
                    logger.exception(f"Parse model failed.")
                    raise APIResponseError(
                        f"Failed to parse response data. "
                        f"Expect model: '{model}', Got '{repr(obj)}'"
                    ) from None

            if self.sync:
                def sync_request(ins, *args, **kwargs):
                    return evloop.run(do_request(ins, *args, **kwargs))

                return sync_request
            else:
                return do_request

        return execute


get = DummyDeco(method='get')
post = DummyDeco(method='post')


class APIBase:
    endpoint = '/'
    server_name: str = None

    def __init__(
        self,
        header: Union[T_DictPydanticModel, CaseInsensitiveDict] = None,
        prefix: str = '',
    ):
        if isinstance(header, PydanticBaseModel):
            self.header = CaseInsensitiveDict(header.dict(by_alias=True))
        elif isinstance(header, dict):
            self.header = CaseInsensitiveDict(header)
        elif header is None:
            if OPTION.general.for_server_use:
                # noinspection PyUnresolvedReferences
                from starlette_context import context
                self.header = CaseInsensitiveDict(context.data['header'])
            else:
                self.header = CaseInsensitiveDict(OPTION.api.header)
        else:
            self.header = header

        self.prefix = prefix
        self.header.update({
            "Content-Type": "application/json;charset=UTF8",
            "Connection": "close",
        })
        self.base_url = None

    async def get_base_url(self):
        if self.base_url is None:
            if (
                OPTION.discovery.enabled
                and OPTION.discovery.take_over
                and self.server_name is not None
            ):
                discovery = ServiceDiscovery.instantiate()
                self.base_url = await discovery.get_url(self.server_name)
            elif mat := RE_SYS_SERVER_PARSER.match(self.prefix):
                self.base_url = concat_url(OPTION.server.base, mat.group(1))
            else:
                self.base_url = self.prefix
        return self.base_url


class APIMeta(type):
    sync = True

    def __new__(mcs, name, bases, namespace, **kwargs):
        all_attrs = {}
        for base in bases:
            all_attrs.update(base.__dict__)
        all_attrs.update(namespace)

        for _name, attr in all_attrs.items():
            if (schema := getattr(attr, '__api_meta__', None)) is None:
                continue
            schema = schema.copy()
            method = schema.pop('__method__')
            namespace[_name] = Route(method=method, sync=mcs.sync)(**schema)(attr)

        return super().__new__(mcs, name, bases, namespace, **kwargs)


class AysncAPIMeta(APIMeta):
    sync = False


class AsyncAPIBase(APIBase, metaclass=AysncAPIMeta):
    pass


class SyncAPIBase(APIBase, metaclass=APIMeta):
    pass


# noinspection PyUnresolvedReferences
class _DynamicAPIMixin:
    module_id: str
    server_cache = TTLCache(maxsize=128, ttl=3600)
    module_type: str = UNSET
    server_name: str = None
    base_url: str = None
    version = None

    def get_module_id(self, version: Union[float, str], module_id: str):
        if (module_type := self.module_type) is UNSET:
            raise NotImplementedError(f"class variable {module_type} is not implemented.")
        if module_id is not None:
            if not (mid := module_id.upper()).startswith(module_type):
                raise NameError(f"Module id {mid} is not valid for module: {module_type}.")
            return mid
        if version is not None:
            self.version = to_version_tuple(version)
            return f"{module_type}{repr_version(self.version, '_')}"

    def _add_to_memo(self, server_meta):
        if not server_meta:
            raise RuntimeError(f"Module: {self.module_id} is not avaliable")
        server_name = server_meta.serverName
        self.server_cache[self.module_id] = server_name
        return server_name

    async def get_server_name(self):
        if self.server_name is None:
            if self.module_id in self.server_cache:
                self.server_name = self.server_cache[self.module_id]
            else:
                from .space import SpaceAPI
                api = SpaceAPI(self.header, sync=False)
                server_meta = await api.module.detail(self.module_id)  # noqa
                self.server_name = self._add_to_memo(server_meta)
        return self.server_name

    async def get_base_url(self):
        if self.base_url is None:
            server_name = await self.get_server_name()
            if OPTION.discovery.enabled:  # pragma: no cover
                discovery = ServiceDiscovery.instantiate()
                base_url = await discovery.get_url(server_name)
                self.base_url = concat_url(base_url)
            else:
                self.base_url = concat_url(OPTION.server.base, server_name)
        return self.base_url


class DynamicAPIBase(_DynamicAPIMixin, SyncAPIBase):
    def __init__(
        self,
        version: Union[float, str] = None,
        header: T_DictPydanticModel = None,
        module_id: str = None,
        lazy: bool = False
    ):
        super().__init__(header)
        self.module_id = self.get_module_id(version, module_id)

    def set_server_name(self, server_name):
        self.server_name = server_name

    # backward compatibility
    set_url = set_server_name


class ADynamicAPIBase(_DynamicAPIMixin, AsyncAPIBase):
    def __init__(
        self,
        version: Union[float, str] = None,
        header: T_DictPydanticModel = None,
        module_id: str = None,
        lazy: bool = False,  # noqa
    ):
        super().__init__(header)
        self.module_id = self.get_module_id(version, module_id)
        self.lazy = lazy

    def __await__(self):
        return self.init().__await__()

    async def init(self):
        return self

    async def set_server_name(self, server_name):
        self.server_name = server_name

    # backward compatibility
    set_url = set_server_name


class RootAPI:
    """
    API基类。 所有 **固定url** 的API应该继承这个类。

    同时提供同步和异步的http调用方法，根据初始化参数sync，
    对于封装的接口，会自动采取同步或者异步的调用方式。
    """
    prefix: Callable[[], str] = lambda: None
    url_need_format = False
    endpoint = ''
    __cls_cache__ = {}
    multi_version = False
    default_version = None
    api_version = None
    cls_name = None
    module_name = None
    server_name = None
    builtin = True

    if TYPE_CHECKING:  # pragma: no cover
        # 由APIBase带入，此处定义仅用于ide提示
        header: Dict[str, str] = {}
        base_url: str = ''

    @classmethod
    def collect_endpoints(cls) -> List[str]:

        def _resolve_direct_endpoints(cls) -> List[str]:
            eps = []
            for attr in cls.__dict__.values():
                if meta := getattr(attr, '__api_meta__', None):
                    eps.append(meta['endpoint'])
            return eps

        endpoints = _resolve_direct_endpoints(cls)

        for name, attr in cls.__dict__.items():
            if not (
                isinstance(attr, cached_property)
                and (anno := get_type_hints(attr.func))
                and (api := anno.get('return'))
                and issubclass(api, ChildAPI)
            ):
                continue

            tag = api.endpoint
            endpoints.extend(
                concat_url(tag, ep)
                for ep in _resolve_direct_endpoints(api)
            )

        return endpoints

    @classmethod
    def resolve_cls(cls, sync, sync_base, async_base, extra=None):
        if sync:
            base = sync_base
            prefix = "Sync"
        else:
            base = async_base
            prefix = "Async"

        if not isinstance(base, tuple):
            base = (base, )

        class_name = f"_{'_'.join(cls.__module__.split('.'))}_{prefix}{cls.__name__}_"
        if class_name in cls.__cls_cache__:
            clz = RootAPI.__cls_cache__[class_name]
        else:
            extra = extra or {}
            initial = {}

            for parent_cls in cls.__mro__:
                if parent_cls in [DynamicRootAPI, ChildAPI, RootAPI]:
                    break
                initial = {**parent_cls.__dict__, **initial}

            clz = type(class_name, base, {
                **initial, **extra,
                "__new__": base[0].__new__,
            })
            RootAPI.__cls_cache__[class_name] = clz
        return clz

    @classmethod
    def resolve_version_cls(
        cls, sync, sync_base, async_base,
        version: Union[float, str, Tuple[int]] = None,
        extra=None
    ):
        if version is not None and not isinstance(version, tuple):
            version = to_version_tuple(version)

        if sync:
            base = sync_base
            prefix = "Sync"
        else:
            base = async_base
            prefix = "Async"

        if not isinstance(base, tuple):
            base = (base,)

        if version is not None:
            class_name = f"_{'_'.join(cls.__module__.split('.'))}" \
                         f"_{prefix}{cls.__name__}{repr_version(version, '_')}_"
        else:
            class_name = f"_{'_'.join(cls.__module__.split('.'))}_{prefix}{cls.__name__}_"

        if class_name in cls.__cls_cache__:
            return RootAPI.__cls_cache__[class_name]

        extra = extra or {}

        # Called from a multiversion API class
        # And the required version is not default version
        if version is not None and (version != cls.default_version or version != cls.api_version):
            if version < cls.api_version:
                raise ValueError(f'Version of current API class should not be '
                                 f'earlier than {repr_version(cls.api_version)}.')
            try:
                module = import_module(VERSIONED_MODULE.format(version=repr_version(version, "_"),
                                                               name=cls.module_name.rpartition('.')[-1]))
                versioned_cls = getattr(module, cls.cls_name)
                initial = {**versioned_cls.__dict__}

                if not cls.builtin:
                    initial = {**initial, **cls.__dict__}

                clz = type(class_name, base, {
                    **initial, **extra,
                    "__new__": base[0].__new__
                })
            except (ImportError, AttributeError):
                raise NotImplementedError(
                    f"{cls.__name__} with version: V{repr_version(version)} is not implemented.")
        else:
            clz = type(class_name, base, {
                **cls.__dict__, **extra,
                "__new__": base[0].__new__,
            })

        RootAPI.__cls_cache__[class_name] = clz
        return clz

    def __new__(cls, header=None, sync=OPTION.api.io_sync):
        """

        Args:
            header: 请求头
            sync: 是否使用同步方式请求

        """
        clz = cls.resolve_cls(sync, SyncAPIBase, AsyncAPIBase)
        ins = clz(header=header, prefix=cls.prefix())
        ins.sync = sync
        ins.multi_version = cls.multi_version
        ins.default_version = cls.default_version
        ins.cls_name = cls.cls_name
        ins.module_name = cls.module_name
        ins.api_version = cls.api_version
        ins.builtin = cls.builtin
        ins.url_need_format = cls.url_need_format
        return ins


class _ChildAPI:
    """用来做ChildAPi的标识"""
    if TYPE_CHECKING:  # pragma: no cover
        root = None


class ChildAPI(RootAPI):
    def __new__(cls, root: RootAPI):
        clz = cls.resolve_cls(
            root.sync, (SyncAPIBase, _ChildAPI), (AsyncAPIBase, _ChildAPI),
            extra={'get_base_url': cls.get_base_url}
        )
        ins = clz(header=root.header, prefix=root.prefix)
        if root.url_need_format:
            ins.endpoint = ins.endpoint.format(**root.header)
        ins.root = root
        return ins

    async def get_base_url(self):
        if self.base_url is None:
            base_url = await self.root.get_base_url()
            self.base_url = concat_url(base_url, self.endpoint)
        return self.base_url


class DynamicRootAPI(RootAPI):
    """
     动态API基类。 所有 **非固定url** 的API应该继承这个类

     Examples:
         .. code-block:: python

             class ExampleAPI(DynamicRootAPI):
                 module_type = 'EXAMPLE'

                 @get('/test')
                 def test(self):
                     return {}

         对于上述api，存在2种初始化方法。

         .. code-block:: python

             api = ExampleAPI(version='1.0', sync=True)
             api = await ExampleAPI(version='1.0', sync=False)

         当sync=False时，必须使用await初始化。
         以这种方式初始化的api，必须使用await调用，即：

         .. code-block:: python

             await api.test()

         以sync=True初始化的api，可以同步调用，即：

         .. code-block:: python

             api.test()

     """

    module_type = ''
    if TYPE_CHECKING:  # pragma: no cover
        server_cache: TTLCache
        module_id: str
        version: Optional[Tuple[int, int]]

    def __new__(
        cls,
        version: Union[float, str] = None,
        header: dict = None,
        sync: bool = UNSET,
        module_id: str = None,
        lazy: bool = False
    ):
        """

        Args:
            version: 组件版本
            header: 请求头
            sync: 是否使用同步方式请求
            module_id: 组件ID

        """
        if cls.__base__ is not DynamicRootAPI and issubclass(cls.__base__, DynamicRootAPI):
            extra = {k: v for k, v in cls.__base__.__dict__.items() if k not in cls.__dict__}
        else:
            extra = {}

        if getattr(cls, 'multi_version', False):
            clz = cls.resolve_version_cls(sync, DynamicAPIBase, ADynamicAPIBase, version, extra=extra)
        else:
            clz = cls.resolve_cls(sync, DynamicAPIBase, ADynamicAPIBase, extra=extra)
        ins = clz(version=version, header=header, module_id=module_id, lazy=lazy)
        if sync is UNSET:
            ins.sync = OPTION.api.io_sync
        else:
            ins.sync = sync
        ins.multi_version = cls.multi_version
        ins.default_version = cls.default_version
        ins.cls_name = cls.cls_name
        ins.module_name = cls.module_name
        ins.api_version = cls.api_version
        ins.builtin = cls.builtin
        ins.url_need_format = cls.url_need_format
        return ins

    def __init_subclass__(cls, *, builtin=False):
        setattr(cls, 'builtin', builtin)

    def __await__(self):  # pragma: no cover
        # defined here to help ide
        pass
