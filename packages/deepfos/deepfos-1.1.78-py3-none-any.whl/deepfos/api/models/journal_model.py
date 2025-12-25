"""
Models used by /journal-model-server1-0
"""

from deepfos.api.models.base import BaseModel
from typing import List, Optional, Any, Dict

__all__ = [
    'CheckStandardDataVO',
    'CheckStandardVO',
    'ColumnAliasDTO',
    'ElementDetailDTO',
    'MessageDTO',
    'ModelDataColumnDTO',
    'ModelDataQueryVO',
    'QueryWhereDTO',
    'JmPostParamVO',
    'JmPostResultVO',
    'JournalModelExecCallbackPythonDTO',
    'CommonResultDTO',
    'ModelDataBatchDTO',
    'ModelDataDeleteDTO',
    'ModelDataDTO',
    'JournalModelConfig',
    'ModelColumnVO',
    'ModelDataTableVO',
    'ModelTableVO',
    'JournalModelTypeVo',
    'JournalSortConfig'
]


class ElementDetailDTO(BaseModel):
    #: 是否绝对路径
    absoluteTag: Optional[bool] = None
    #: 多语言
    description: Any = None
    #: 元素名称
    elementName: Optional[str] = None
    #: 元素类型
    elementType: Optional[str] = None
    #: 目录id
    folderId: Optional[str] = None
    #: 多语言使用的key
    languageKey: Optional[str] = None
    #: 元素对应组件版本
    moduleVersion: Optional[str] = None
    #: 元素绝对路径
    path: Optional[str] = None
    #: 元素相对路径
    relativePath: Optional[str] = None
    #: 组件id
    serverName: Optional[str] = None
    #: 凭证类型代码
    vmTypeCode: Optional[str] = None


class ModelColumnVO(BaseModel):
    name: Optional[str] = None
    operation: Optional[str] = None


class ModelDataTableVO(BaseModel):
    id: Optional[str] = None
    #: 元素编码
    name: Optional[str] = None
    #: 真实表名
    actualTableName: Optional[str] = None
    #: 文件夹ID
    folderId: Optional[str] = None
    #: 元素详细信息
    elementDetail: Optional[ElementDetailDTO] = None
    #: 子表
    children: Optional[List[Any]] = None


class ModelTableVO(BaseModel):
    #: 表的uuid
    tableUuid: Optional[str] = None
    #: 父表的uuid
    parentUuid: Optional[str] = None
    #: 数据表信息
    dataTableInfo: Optional[ModelDataTableVO] = None
    #: 字段列集合
    columns: Optional[List[ModelColumnVO]] = None
    #: 子表集合
    children: Optional[List['ModelTableVO']] = None


class JournalModelTypeVo(BaseModel):
    #: 凭证Tag
    journalTag: Optional[str] = None
    #: 凭证类型代码
    typeCode: Optional[str] = None


class JournalModelConfig(BaseModel):
    #: 逻辑表信息
    logicTable: Optional[ModelTableVO] = None
    #: 层级，0为顶层
    level: Optional[int] = None
    #:
    type: Optional[str] = None
    #: 凭证基础信息
    baseInfo: Optional[Any] = None
    #: 凭证自定义逻辑
    customLogic: Optional[Any] = None
    #: 报错集合
    errorList: Optional[Any] = None
    #: 警告集合
    warningList: Optional[Any] = None
    #: 凭证类型集合
    journalModelType: Optional[List[JournalModelTypeVo]] = None


class CheckStandardDataVO(BaseModel):
    #: mainId
    mainId: Optional[str] = None
    #: 凭证id
    journalId: Optional[str] = None
    #: 凭证类型代码
    journalTypeCode: Optional[str] = None


class CheckStandardVO(BaseModel):
    #: 凭证id和凭证类型代码集合
    dataList: Optional[List[CheckStandardDataVO]] = None
    #: 凭证模型名称
    elementName: Optional[str] = None
    #: 凭证模型文件夹ID
    folderId: Optional[str] = None
    #: 凭证模型路径
    path: Optional[str] = None
    # 筛选条件
    whereStr: Optional[str] = None


class ColumnAliasDTO(BaseModel):
    #: field
    field: Optional[str] = None
    #: id
    id: Optional[str] = None
    #: sort
    sort: Optional[str] = None
    #: viewKey
    viewKey: Optional[str] = None


class MessageDTO(BaseModel):
    #: 别名
    alias: Optional[ColumnAliasDTO] = None
    #: 描述
    description: Optional[str] = None
    #: msg
    msg: Optional[str] = None
    #: title
    title: Optional[str] = None


class ModelDataColumnDTO(BaseModel):
    #: 权限值
    accessRight: Optional[int] = None
    #: 字段别名,用于定位字段在明细表中位置
    alias: Optional[ColumnAliasDTO] = None
    #: 字段名
    columnName: Optional[str] = None
    #: 原始字段值
    oldValue: Optional[Any] = None
    #: 操作类型
    operateType: Optional[str] = None
    #: 字段值
    value: Optional[Any] = None


class JournalSortConfig(BaseModel):
    #: 字段名
    col: Optional[str] = None
    #: 排序类型 ：ASC 或 DESC, 默认为 ASC
    type: Optional[str] = None


class ModelDataQueryVO(BaseModel):
    #: 数据表目录id
    dataTableFolderId: Optional[str] = None
    #: 数据表名称(从该数据表开始查,此时对应mainKeys为该表业务主键)
    dataTableName: Optional[str] = None
    #: 数据表目录(与dataTableFolderId传一个即可)
    dataTablePath: Optional[str] = None
    #: 凭证模型名称
    elementName: Optional[str] = None
    #: 返回结果中排除指定表的目录id
    excludeDataTableFolderId: Optional[str] = None
    #: 返回结果中排除指定表的表名(返回结果中排除指定表下子表的数据)
    excludeDataTableName: Optional[str] = None
    #: 返回结果中排除指定表的目录
    excludeDataTablePath: Optional[str] = None
    #: 凭证模型所在目录id(与path传一个即可)
    folderId: Optional[str] = None
    #: 返回结果中是否包含字段权限信息 默认值:false
    includeAccess: Optional[bool] = None
    #: 凭证模型主表（或传入表）的业务主键的值集合
    mainKeys: Optional[List[Dict]] = None
    #: 凭证模型所在路径
    path: Optional[str] = None
    #: 数据查询时的where条件
    whereStr: Optional[str] = None
    #: 返回的头表列名 集合，不指定，则取头表所有字段
    headQueryCols: Optional[List[str]] = None
    #: 返回的行表列名 集合，不指定，则取行表所有字段
    lineQueryCols: Optional[List[str]] = None
    #: 返回的列名 集合
    sortConfig: Optional[List[JournalSortConfig]] = None



class QueryWhereDTO(BaseModel):
    #: 字段名
    columnName: Optional[str] = None
    #: 操作符
    operationCode: Optional[str] = None
    #: 字段值
    value: Optional[Any] = None


class JmPostParamVO(BaseModel):
    #: 需过账|取消过账数据ID集合
    dataIds: Optional[List[str]] = None
    #: 凭证模型名称
    elementName: Optional[str] = None
    #: 凭证模型文件夹ID
    folderId: Optional[str] = None
    #: 凭证模型路径
    path: Optional[str] = None
    #: 筛选条件
    whereStr: Optional[str] = None


class JmPostResultVO(BaseModel):
    #: fmPostMsg
    fmPostMsg: Optional[Any] = None
    #: msg
    msg: Optional[str] = None
    #: 过账结果
    postResult: Optional[Any] = None
    #: success
    success: Optional[bool] = None


class JournalModelExecCallbackPythonDTO(BaseModel):
    #: PY所在路径，与folderId二选一
    path: Optional[str] = None
    #: PY所在文件夹ID，与path二选一
    folderId: Optional[str] = None
    #: PY的元素名称
    elementName: str
    #: 类型 默认值 PY
    elementType: Optional[str] = None
    #: Python服务名，如：python-server2-0
    serverName: Optional[str] = None
    #: 传给回调的参数，{key1:value1,key2:value2}
    callbackParams: Optional[Dict] = None


class CommonResultDTO(BaseModel):
    #: errors
    errors: Optional[List[MessageDTO]] = None
    #: success
    success: Optional[bool] = True
    #: warnings
    warnings: Optional[List[MessageDTO]] = None
    # infos
    infos: Optional[List[MessageDTO]] = None
    # successInfo
    successInfo: Optional[List[MessageDTO]] = None
    #: error_refresh
    errorRefresh: Optional[bool] = None
    # 业务主键
    mainKey: Optional[Dict] = None


class ModelDataBatchDTO(BaseModel):
    #: 数据集合
    dataMap: Optional[Any] = None
    #: 是否启用创建人、创建时间自动赋值，默认为True
    enableCreate: Optional[bool] = None
    #: 是否启用字段值为空时使用默认值填充，默认为False
    enableDefaultValue: Optional[bool] = None
    #: 是否启用业务主键重复的校验，默认为True
    enableRepeatCheck: Optional[bool] = None
    #: 是否启用必填字段的校验，默认为False
    enableRequired: Optional[bool] = None
    #: 是否启用有效性范围的校验，默认为True
    enableValidRange: Optional[bool] = None
    #: 是否启用一次性校验所有规则和数据，默认为True
    enableAllErrors: Optional[bool] = None
    #: 是否启用凭证行表至少需要一条数据的校验，默认为True
    enableNeedOneLine: Optional[bool] = None
    #: modelInfo
    modelInfo: Optional[ElementDetailDTO] = None
    #: 执行参数值列表{key1:value1,key2:value2}
    paramValueMap: Optional[Any] = None
    #: 回调信息
    callbackInfo: Optional[JournalModelExecCallbackPythonDTO] = None


class ModelDataDeleteDTO(BaseModel):
    #: 元素名
    elementName: Optional[str] = None
    #: 所属目录id
    folderId: Optional[str] = None
    #: 业务字段数据集合
    mainKeyList: Optional[List[Dict]] = None
    #: 子模型分区ID
    partitionId: Optional[str] = None
    #: 所属目录
    path: Optional[str] = None
    #: 数据删除时的where条件
    whereList: Optional[List[QueryWhereDTO]] = None
    #: 数据删除时的where条件
    whereStr:  Optional[str] = None



class ModelDataDTO(BaseModel):
    #: 子数据信息
    children: Optional[List['ModelDataDTO']] = None
    #: 数据表字段及值
    columns: Optional[List[ModelDataColumnDTO]] = None
    #: 数据表目录编码
    dataTableFolderId: Optional[str] = None
    #: 数据表名（元素名）
    dataTableName: Optional[str] = None
    #: 数据表目录
    dataTablePath: Optional[str] = None
    #: mainId
    mainId: Optional[str] = None



ModelTableVO.update_forward_refs()
ModelDataDTO.update_forward_refs()
