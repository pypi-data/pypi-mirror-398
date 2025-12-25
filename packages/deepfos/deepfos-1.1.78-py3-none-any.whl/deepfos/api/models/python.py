from enum import Enum

from .base import BaseModel
from typing import Any, List, Literal, Optional, Union

__all__ = [
    "WorkerRegistry",
    "PyRunInfo",
    "WorkerMetrics",
    "Description",
    "DescriptionBase",
    "ElementDescription",
    "PyBaseInfo",
    "PyParam",
    "ReturnStructureEnum",
    "ReturnStructureError",
    "Structure",
    "PyNewFile",
    "PyNewFileWithError",
]


class WorkerRegistry(BaseModel):
    hostname: str
    db: List[str]


class PyRunInfo(BaseModel):
    #: 元素名/编码
    elementName: str
    #: 元素类型
    elementType: str = "PY"
    #: python的执行参数
    parameter: Any = None
    #: 文件路径
    path: Optional[str] = None
    #: 文件夹id
    folderId: Optional[str] = None
    #: 参数是否被压缩
    compressedFlag: bool = False
    #: 任务名称
    taskName: Optional[str] = None


class WorkerMetrics(BaseModel):
    #: 工作进程名
    worker: str
    #: 工作进程主进程pid
    pid: int
    #: 工作进程当前子进程数量
    currentPoolSize: int
    #: 工作进程最大子进程数量
    maxPoolSize: int
    #: 工作进程最小子进程数量
    minPoolSize: int
    #: 工作进程的资源占用情况
    rusage: Optional[dict] = None
    #: 活跃的工作进程数
    active: int
    #: 空闲的工作进程数
    idle: int
    #: 已运行时间：秒
    uptime: int
    #: 服务器负载：百分比
    loadAverage: int
    #: 已处理任务数
    processed: int


class Description(BaseModel):
    #: 标题
    title: Optional[str] = None
    #: 描述
    description: Optional[str] = None


class DescriptionBase(BaseModel):
    #: 描述
    description: Optional[str] = None


class ElementDescription(BaseModel):
    #: 中文描述
    zh_cn: Optional[str] = None
    #: 英文描述
    en: Optional[str] = None



class PyBaseInfo(BaseModel):
    """Py Base Info

    .. admonition:: 引用接口

        - **get** ``/file/read``
    """

    #: 元素名/编码
    elementName: str
    #: 元素类型
    elementType: Literal["PY"] = "PY"
    #: 文件夹id
    folderId: Optional[str] = None
    #: 文件路径
    path: Optional[str] = None


class PyParam(BaseModel):
    #: 参数名
    name: str
    #: 参数类型
    type: Literal["string"]
    #: 参数默认值
    value: Optional[str] = ""
    #: 描述（多语言）
    description: Optional[ElementDescription] = None
    #: 参数元信息
    meta: Optional[str] = ""


class ReturnStructureEnum(str, Enum):
    notification = "notification"
    structure = "structure"
    notificationV2 = "notification_v2"


class ReturnStructureError(BaseModel):
    #: 错误码，当前错误类型的编码，可以根据编码跳转到对应的文档
    errorCode: Optional[str] = None
    #: 错误信息、弹窗中的列表项信息
    errorMessage: Optional[str] = None
    #: 报错字段名，精确到无限层级，若无为当前对象或属性链接级别的错误
    fieldName: Optional[List[Union[int, str]]] = None
    #: 报错字段的提示信息
    fieldTip: Optional[str] = None


class Structure(BaseModel):
    #: 参数名
    name: str
    #: 参数类型
    type: Literal["string", "integer", "decimal", "boolean", "datetime", "anytype"]
    #: 作为数组
    isArray: bool = False
    #: 不可为空
    notNull: bool = False


class PyNewFile(BaseModel):
    """Py New File

    .. admonition:: 引用接口

        - **POST** ``/file/add``
        - **POST** ``/file/update``
    """

    #: 是否启用输出结构
    enableReturnStructure: bool = False
    #: 输出结构类型
    returnStructureType: Optional[ReturnStructureEnum] = None
    #: 绑定返回信息
    returnStructureData: Optional[List[Structure]] = None
    #: 元素名/编码
    elementName: str
    #: 元素类型
    elementType: Literal["PY"] = "PY"
    #: 文件夹id
    folderId: Optional[str] = None
    #: 文件路径
    path: Optional[str] = None
    #: 描述（多语言）
    description: Optional[ElementDescription] = None
    #: 模块名
    moduleId: str = "PY2_0"
    #: 文件内容
    content: str
    #: 是否记录日志
    shouldLog: bool = True
    #: 是否创建流程
    createBF: bool = False
    #: 绑定参数信息
    parameters: Optional[List[PyParam]] = None


class PyNewFileWithError(BaseModel):
    """Py New File With Error

    .. admonition:: 引用接口

        - **get** ``/file/read``
    """

    #: 元素名/编码
    elementName: str
    #: 元素类型
    elementType: Literal["PY"] = "PY"
    #: 文件夹id
    folderId: Optional[str] = None
    #: 文件路径
    path: Optional[str] = None
    #: 描述（多语言）
    description: Optional[ElementDescription] = None
    #: 模块名
    moduleId: str = "PY2_0"
    #: 文件内容
    content: str
    #: 是否记录日志
    shouldLog: bool = True
    #: 是否创建流程
    createBF: bool = False
    #: 绑定参数信息
    parameters: Optional[List[PyParam]] = None
    #: 是否启用输出结构
    enableReturnStructure: bool = False
    #: 输出结构类型
    returnStructureType: Optional[ReturnStructureEnum] = None
    #: 绑定返回信息
    returnStructureData: Optional[List[Any]] = None
    #: 返回的错误结构
    errorList: Optional[List[ReturnStructureError]] = None
