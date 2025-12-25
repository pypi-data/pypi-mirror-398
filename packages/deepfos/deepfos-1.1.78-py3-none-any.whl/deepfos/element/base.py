import inspect
import contextvars
from functools import wraps


from deepfos import OPTION
from deepfos.api.app import AppAPI
from deepfos.api.base import DynamicRootAPI
from deepfos.api.models.app import (
    QueryElementInfoByTypeDto as ElementModel,
    ElementRelationInfo, ModuleServerNameVO
)
from deepfos.exceptions import *
from deepfos.lib.asynchronous import evloop, future_property, FuturePropertyMeta
from deepfos.lib.constant import RE_SERVER_NAME_PARSER, RE_MODULEID_PARSER
from deepfos.lib.decorator import cached_property
from deepfos.lib.concurrency import ParallelProxy
from typing import (
    Type, Union, Dict, List, Generic, TypeVar,
    get_origin, get_args
)

__all__ = ['ElementBase', 'SyncMeta', 'synchronize']


_HINT = """
    如果不提供folder_id和path，将会使用元素名和元素类型进行全局搜索。
    如果找到 **唯一匹配** 的元素，那么一切正常，否则将会报错。
"""

_ARGS = {
    "element_name": "元素名",
    "folder_id": "元素所在的文件夹id",
    "path": "元素所在的文件夹绝对路径",
}

T_ElementInfoWithServer = Union[ModuleServerNameVO, ElementRelationInfo]
T_ApiClass = TypeVar('T_ApiClass', bound=DynamicRootAPI)


class _ElementMeta(FuturePropertyMeta):
    __mangle_docs__ = True

    def __new__(mcs, name, bases, namespace, **kwargs):
        if '__doc__' not in namespace:
            for base in bases:
                if base.__doc__ is not None:
                    namespace['__doc__'] = base.__doc__
                    break

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if cls.__mangle_docs__:
            cls_doc = mcs._split_doc(cls.__doc__)
            cls.__doc__ = mcs._recover_doc(cls_doc)

        if "api_class" not in namespace and ElementBase in bases:
            for base in cls.__orig_bases__:  # noqa
                if get_origin(base) is ElementBase:
                    cls.api_class = get_args(base)[0]
                    break
            else:
                raise RuntimeError(f'Cannot resolve api class for {cls}')

        return cls

    @staticmethod
    def _split_doc(doc: str):
        cur_directive = 'main'
        parsed = {
            cur_directive: []
        }

        if not doc:
            return {
                **parsed,
                "Args": _ARGS,
                "Hint": [_HINT]
            }

        directives = ['Args:', 'Hint:', 'Warnings:', 'Note:']

        in_args = False
        cur_directive = 'main'
        parsed = {
            cur_directive: []
        }
        last_arg = ''

        for line in doc.splitlines():
            if (striped_line := line.strip()) in directives:
                cur_directive = striped_line[:-1]

                if cur_directive == 'Args':
                    in_args = True
                    parsed[cur_directive] = {}

                else:
                    in_args = False
                    parsed[cur_directive] = []

                continue

            if in_args:
                if striped_line:
                    k, _, v = striped_line.partition(':')
                    if _:
                        parsed[cur_directive][k.strip()] = v.strip()
                        last_arg = k
                    else:
                        parsed[cur_directive][last_arg] += striped_line.strip()
            else:
                parsed[cur_directive].append(line)

        args = parsed.pop('Args', {})
        hint = parsed.pop('Hint', [])
        parsed['Args'] = {**_ARGS, **args}

        hint.append(_HINT)
        parsed['Hint'] = hint

        return parsed

    @staticmethod
    def _recover_doc(doc_dict: Dict):
        doc: List[str] = doc_dict.pop('main')
        doc.append('\n')
        args: Dict[str, str] = doc_dict.pop('Args')

        doc.append('Args:')
        doc.extend(f"    {k}: {v}" for k, v in args.items())
        doc.append('\n')

        for k, v in doc_dict.items():
            doc.append(k + ":")
            doc.extend(v)
            doc.append('\n')

        return '\n'.join(doc)


class ElementBase(Generic[T_ApiClass], metaclass=_ElementMeta):
    """deepfos平台元素的基类"""

    #: 元素绑定的api类
    api_class: Type[T_ApiClass] = None
    #: 元素类型
    element_type: str = None

    def __init__(
        self,
        element_name: str,
        folder_id: str = None,
        path: str = None,
        server_name: str = None,
    ):
        self.element_name = element_name
        self._folder_id = folder_id
        self._path = path
        self._server_name = server_name

    @cached_property
    def api(self) -> T_ApiClass:
        """同步API对象"""
        version = self._get_version(self.element_info)
        api = self.api_class(version=version, sync=True, lazy=True)
        api.set_url(self.element_info.serverName)
        return api

    async def _get_element_info(self) -> T_ElementInfoWithServer:
        if (
            OPTION.boost.skip_internal_existence_check
            and self._folder_id is not None
            and self._server_name is not None
            and (match := RE_SERVER_NAME_PARSER.match(self._server_name))
        ):
            return ModuleServerNameVO(
                elementName=self.element_name,
                elementType=self.element_type,
                folderId=self._folder_id,
                serverName=self._server_name,
                moduleVersion=match.group('ver').replace('-', '.')
            )
        ele_info = await self.async_check_exist(
            self.element_name,
            folder=self._folder_id,
            path=self._path,
            silent=False
        )
        return ele_info

    @staticmethod
    def _get_version(ele_info):
        """
        Returns: version_id with format as '1_0' or None if no version_id got
        """
        if match := RE_SERVER_NAME_PARSER.match(ele_info.serverName):
            return match.group('ver').replace('-', '_')

        # Init with path or folderId provided
        if isinstance(ele_info, ModuleServerNameVO):
            # Format example: "2.0"
            if ele_info.moduleVersion:
                return ele_info.moduleVersion.replace('.', '_')
        else:
            # Format example: "MAINVIEW1_0"
            if ele_info.moduleId and (match := RE_MODULEID_PARSER.match(ele_info.moduleId)):
                return match.group('ver')
            # Format example: "2.0"
            if ele_info.moduleVersion:
                return ele_info.moduleVersion.replace('.', '_')

    async def _init_api(self) -> T_ApiClass:
        ele_info = await self.wait_for('element_info')
        version = self._get_version(ele_info)
        api = await self.api_class(version=version, sync=False, lazy=True)
        await api.set_url(ele_info.serverName)
        if isinstance(ele_info, ElementRelationInfo):
            # 更新api_class的缓存
            api.__class__.server_cache[ele_info.moduleId] = \
                ele_info.serverName
            api.module_id = ele_info.moduleId
        else:
            api.module_id = f"{api.module_type}{version}"
        return api

    @future_property
    async def element_info(self) -> T_ElementInfoWithServer:
        """元素信息"""
        return await self._get_element_info()

    @future_property
    async def async_api(self) -> T_ApiClass:
        """异步API对象"""
        return await self._init_api()

    @classmethod
    def check_exist(
        cls,
        ele_name: str,
        ele_type: str = None,
        folder: str = None,
        path: str = None,
        silent: bool = True,
    ) -> Union[T_ElementInfoWithServer, int]:
        """查询元素是否存在

        Args:
            ele_name: 元素名
            ele_type: 元素类型
            folder: 文件夹id
            path: 文件夹路径
            silent: 元素不唯一是是否报错

        Returns:
            - 当指定 ``silent`` 为 ``True`` 时，返回查询到的元素个数（ :obj:`int` 类型）。
            - 当指定 ``silent`` 为 ``False`` 时，如果元素个数唯一，返回该元素
              （ :class:`ModuleServerNameVO` 或 :class:`ElementRelationInfo` 类型），否则将报错。

        """
        return evloop.run(cls.async_check_exist(
            ele_name=ele_name,
            ele_type=ele_type,
            folder=folder,
            path=path,
            silent=silent
        ))

    @classmethod
    async def async_check_exist(
        cls,
        ele_name: str,
        ele_type: str = None,
        folder: str = None,
        path: str = None,
        silent: bool = True,
    ) -> Union[T_ElementInfoWithServer, int]:
        """异步查询元素是否存在

        Args:
            ele_name: 元素名
            ele_type: 元素类型
            folder: 文件夹id
            path: 文件夹路径
            silent: 元素不唯一是是否报错

        Returns:
            - 当指定 ``silent`` 为 ``True`` 时，返回查询到的元素个数（ :obj:`int` 类型）。
            - 当指定 ``silent`` 为 ``False`` 时，如果元素个数唯一，返回该元素
              （ :class:`ModuleServerNameVO` 或 :class:`ElementRelationInfo` 类型），否则将报错。

        """
        if ele_type is None:
            if cls.element_type is None and cls.api_class is None:
                raise ElementTypeMissingError(
                    "Either api_class or module_type should be provided.")

            ele_type = cls.element_type or cls.api_class.module_type

        api = AppAPI(sync=False)

        if path is None and folder is None:
            ele_list = await api.elements.get_element_info_by_name(
                ele_name, ele_type, use_cache=OPTION.api.cache_element_info
            )
        else:
            ele_list = await api.element_info.get_server_names(
                [
                    ElementModel(
                        elementName=ele_name, elementType=ele_type,
                        folderId=folder, path=path
                    )
                ],
                use_cache=OPTION.api.cache_element_info
            )

        ele_no = len(ele_list or [])
        if silent:
            return ele_no

        if ele_no == 0:
            raise ElementNotFoundError(
                f"element name: {ele_name}, element type: {ele_type}.")
        elif ele_no > 1:
            raise ElementAmbiguousError(
                f"Found {ele_no} elements for element name: {ele_name}, "
                f"element type: {ele_type}.")

        return ele_list[0]

    @eliminate_from_traceback
    async def wait_for(self, attr):
        """异步等待成员变量"""
        return await getattr(self.__class__, attr).wait_for(self)


class SyncMeta(_ElementMeta):
    __mangle_docs__ = False

    def __new__(mcs, name, bases, namespace, **kwargs):
        base = bases[0]
        methods = None

        if len(bases) > 1:
            for parent in bases:
                if hasattr(parent, "synchronize"):
                    methods = parent.synchronize
                    break

        if methods is None:
            methods = namespace.pop('synchronize', [])

        for attr in methods:
            namespace[attr] = synchronize(mcs._get_from_bases(base, attr))

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        return cls

    @staticmethod
    def _get_from_bases(base, attr):
        while issubclass(base, ElementBase):
            if attr in base.__dict__:
                return base.__dict__[attr]
            base = base.__base__
        raise AttributeError(attr)


in_sync_ctx = contextvars.ContextVar('call_by_sync')


@eliminate_from_traceback
def synchronize(method):
    assert inspect.iscoroutinefunction(method), \
        "can only synchronize coroutine functions!"

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        coro = method(self, *args, **kwargs)

        if not in_sync_ctx.get(False):
            async def wrap_coro():
                token = in_sync_ctx.set(True)
                res = await coro
                in_sync_ctx.reset(token)
                return res
        else:
            wrap_coro = coro

        if in_sync_ctx.get(False):
            if OPTION.general.parallel_mode:
                return ParallelProxy(coro)
            return coro
        else:
            if OPTION.general.parallel_mode:
                return ParallelProxy(evloop.apply(wrap_coro(), ensure_completed=True))
            return evloop.run(wrap_coro())

    return wrapper
