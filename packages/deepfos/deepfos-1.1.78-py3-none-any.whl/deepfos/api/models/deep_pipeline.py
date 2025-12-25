from typing import Any, Optional

from .base import BaseModel

__all__ = [
    "RunInfo", "FlowInfo", "RunInfoWithParam",
]


class RunInfo(BaseModel):
    #: 元素名/编码
    elementName: str
    #: 元素类型
    elementType: str = "DPL"
    #: 文件路径
    path: Optional[str] = None
    #: 文件夹id
    folderId: Optional[str] = None
    # 是否在同一个进程执行
    inProcess: bool = False


class RunInfoWithParam(BaseModel):
    #: 元素名/编码
    elementName: str
    #: 元素类型
    elementType: str = "DPL"
    #: 执行参数
    parameter: Any
    #: 文件路径
    path: Optional[str] = None
    #: 文件夹id
    folderId: Optional[str] = None
    # 是否在同一个进程执行
    inProcess: bool = False


class Revision(BaseModel):
    #: 版本号
    version: str
    #: 版本名
    name: str


class Configure(BaseModel):
    #: 公共脚本
    prelude: Optional[str] = None
    #: 实例名称
    runNameTemplate: Optional[str] = None
    #: 版本
    revision: Revision
    #: 状态
    status: str


class FlowInfo(BaseModel):
    #: 元素名/编码
    elementName: str
    #: 元素类型
    elementType: str
    #: 文件夹id
    folderId: Optional[str] = None
    #: 元素id
    elementId: Optional[str] = None
    #: 数据流配置
    configure: Configure
