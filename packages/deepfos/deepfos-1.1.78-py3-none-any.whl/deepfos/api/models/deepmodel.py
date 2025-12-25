from typing import List, Optional, Dict, Any

from pydantic import Field

from .base import BaseModel

__all__ = [
    "ObjectBasicDTO",
    "ObjectInfo",
    "ObjectLinkParam",
    "ObjectPropertyParamRes",
    "ObjectParam",
    "ObjectOperationParam",
    "QueryResult",
    "QueryResultObjectInfo",
    "FieldInfo",
    "ParamElement",
    "RuleInfoRes",
    "RuleErrorMsg",
    "RuleParam",
    "SequenceInstance",
    "_IndexParam",
    "SimpleSpaceConnectionConfig",
    "QlGlobalVariableVO",
    "QlRecordVO"
]


class ObjectBasicDTO(BaseModel):
    #: 对象所属应用
    app: Optional[str] = None
    #: 对象所属应用名称
    appName: Optional[str] = None
    #: 对象编码
    code: Optional[str] = None
    #: 对象名称
    name: Optional[Dict[str, Optional[str]]] = None
    #: 对象范围 1：应用级对象 2：空间级对象
    objectScope: Optional[int] = None


class ObjectInfo(BaseModel):
    #: 链接目标对象所在应用id,如果传过来的是_system代表链接的是空间级对象
    app: Optional[str] = None
    #: 链接目标对象所在应用名称
    appName: Optional[str] = None
    #: 链接对象的编码
    code: Optional[str] = None
    #: 引用对象当前语种名称
    objectName: Optional[str] = None
    #: 是否为引用对象的链接
    whetherQuotedRelation: Optional[bool] = None
    #: 是否是为对象指向的链接
    whetherSelfRelation: Optional[bool] = None


class ObjectLinkParam(BaseModel):
    app: Optional[str] = None
    code: Optional[str] = None
    currentObjectUnique: Optional[bool] = None
    deleteCategory: Optional[str] = None
    inferBase: Optional[str] = None
    inferType: Optional[str] = None
    linkId: Optional[str] = None
    linkObjectOption: Optional[int] = None
    linkObjectRequired: Optional[bool] = None
    linkType: Optional[int] = None
    name: Optional[Dict[str, Optional[str]]] = None
    sourceObjectCode: Optional[str] = None
    state: Optional[int] = None
    targetApp: Optional[str] = None
    targetObject: Optional['ObjectParam'] = None
    targetObjectCode: Optional[str] = None
    targetObjectInfo: Optional[ObjectInfo] = None
    whetherSystem: Optional[bool] = None


class ObjectPropertyParamRes(BaseModel):
    #: 应用id
    app: Optional[str] = None
    #: 是否自动赋值
    autoValue: Optional[bool] = None
    #: 属性编码
    code: str
    #: 约束
    constraint: Optional[str] = None
    #: 默认值 默认值类型（0 无,1 定值，2 当前时间 3 枚举）
    defaultValue: Optional[str] = None
    #: 默认值类型 默认值类型（0 无,1 定值）
    defaultValueType: Optional[int] = None
    #: 推断基数: AT_LEAST_ONE, AT_MOST_ONE, MANY, ONE
    inferBase: Optional[str] = None
    #: 最大长度
    maxLength: Optional[int] = None
    #: 最大数量
    maxNum: Optional[int] = None
    #: 最大值
    maxValue: Optional[str] = None
    #: 最大值条件，枚举值 LESS_OR_EQUALS 小于等于；LESS 小于
    maxValueCondition: Optional[str] = None
    #: 最小值
    minValue: Optional[str] = None
    #: 最小值条件 GREATER_OR_EQUALS 大于等于；GREATER大于
    minValueCondition: Optional[str] = None
    #: 属性名称
    name: Dict[str, Optional[str]] = None
    #: 对象编码
    objectCode: Optional[str] = None
    #: 是否是业务主键
    whetherBusinessKey: bool
    #: 是否是计算属性
    whetherCalculation: bool
    #: 是否唯一
    whetherOnly: bool
    #: 是否只读
    whetherReadOnly: bool
    #: 是否必填
    whetherRequired: bool
    #: 是否系统属性
    whetherSystemProperties: bool
    propertyId: Optional[str] = None


class _IndexParam(BaseModel):
    objectIndexId: Optional[str] = None
    objectCode: Optional[str] = None
    indexType: Optional[str] = None
    indexFieldList: Optional[List[str]] = None
    indexFieldIdList: Optional[List[str]] = None


class ObjectParam(BaseModel):
    app: Optional[str] = None
    appName: Optional[str] = None
    code: Optional[str] = None
    linkCodes: Optional[List[str]] = None
    linkParamList: Optional[List[ObjectLinkParam]] = None
    name: Optional[Dict[str, Optional[str]]] = None
    objectId: Optional[str] = None
    objectScope: Optional[int] = None
    objectTypeList: Optional[List[str]] = None
    propertyCodes: Optional[List[str]] = None
    propertyParamList: Optional[List[ObjectPropertyParamRes]] = None
    selfLinkOrder: Optional[int] = None
    state: Optional[int] = None
    #: 对象类型: BUILTIN, STANDARD, VIEW
    type: Optional[str] = None
    whetherSelfReference: Optional[bool] = None
    businessKey: Optional[str] = None
    indexParamList: Optional[List[_IndexParam]] = None
    unitedOnlyList: Optional[List[_IndexParam]] = None


class ObjectOperationParam(BaseModel):
    objectList: List[ObjectParam]


class FieldInfo(BaseModel):
    name: str
    type: str
    fields: Optional[List] = None


class QueryResultObjectInfo(BaseModel):
    objectKey: str
    fields: List[FieldInfo]


class QueryResult(BaseModel):
    objectInfos: Optional[List[QueryResultObjectInfo]] = None
    json_: Any = Field(alias='json')


class RuleErrorMsg(BaseModel):
    errorCode: Optional[str] = None
    errorMessage: Optional[str] = None
    fieldTip: Optional[str] = None
    fieldName: Optional[List[Any]] = None


class ParamElement(BaseModel):
    # 规则参数类型为SEQUENCE时使用
    sequenceCode: Optional[str] = None
    # 规则参数类型为SEQUENCE时使用
    sequenceKeyType: Optional[str] = None
    # 规则参数类型为SEQUENCE时使用
    valueFormat: Optional[str] = None
    # 规则参数类型为SEQUENCE时使用
    sequenceId: Optional[str] = None
    # 规则参数类型为RANDOM_CHARACTER/SEQUENCE时使用
    length: Optional[int] = None
    # 规则参数类型为CURRENT_TIME时使用
    dateFormat: Optional[str] = None
    # 规则参数类型为OBJECT_PROPERTY时使用
    propertyLinkId: Optional[str] = None
    # 规则参数类型为OBJECT_PROPERTY时使用
    propertyLinkCode: Optional[str] = None


class RuleParam(BaseModel):
    #: 规则名称
    code: str
    #: 规则参数编号
    id: Optional[str] = None
    #: 规则标识
    key: Optional[str] = None
    #: 参数内容
    paramContent: Optional[ParamElement] = None
    #: 参数内容 json
    paramContentJson: Optional[str] = None
    #: 规则编号
    ruleId: Optional[str] = None
    #: 规则参数类型 [ "CURRENT_TIME", "OBJECT_PROPERTY", "RANDOM_CHARACTER", "SEQUENCE"]
    ruleParamType: str
    #: 排序
    sort: Optional[int] = None


class RuleInfoRes(BaseModel):
    #: 规则名称
    code: str
    #: 启用状态
    enable: Optional[bool] = None
    #: 执行条件,可用值:ALWAYS_EXECUTE,NULL_EXECUTE
    executeCondition: Optional[str] = None
    #: 规则编号
    id: Optional[str] = None
    #: 规则所属对象id
    objectCode: str
    #: 赋值属性
    propertyCode: Optional[str] = None
    #: 赋值属性id
    propertyId: Optional[str] = None
    #: 规则类型 [SYSTEM_RULE-系统规则、TEXT_PROPERTY_ASSIGNMENT-文本属性赋值]
    ruleType: str
    #: 排序
    sort: Optional[int] = None
    #: 触发时机 [BEFORE_CREATE_SAVE-新建保存前、BEFORE_UPDATE_SAVE-更新保存前]
    triggerType: str
    uniqueKey: Optional[str] = None
    #: 赋值内容
    valueContent: Optional[str] = None
    #: 校验错误列表
    errorMsgList: List[RuleErrorMsg]
    #: 规则参数
    ruleParams: Optional[List[RuleParam]] = None


class SequenceInstance(BaseModel):
    #: 当前值
    currentValue: Optional[int] = None
    #: 序列编号
    sequenceId: Optional[str] = None
    #: 序列主键
    sequenceKey: Optional[str] = None
    #: 序列名称
    sequenceName: Optional[str] = None


class SimpleSpaceConnectionConfig(BaseModel):
    space: str
    dbType: Optional[str] = None
    dbName: Optional[str] = None
    schema_: Optional[str] = Field(default=None, alias='schema')
    edgedbName: str
    edgedbSchema: Optional[str] = None
    createTime: Optional[str] = None
    updateTime: Optional[str] = None


class QlGlobalVariableVO(BaseModel):
    #: 编码
    code: Optional[str] = None
    #: 类型
    type: Optional[str] = None
    #: 值
    value: Any


class QlRecordVO(BaseModel):
    #: 应用标识
    app: Optional[str] = None
    #: 空间标识
    space: Optional[str] = None
    #: 用户id
    userId: Optional[str] = None
    #: 创建时间
    createTime: Optional[str] = None
    #: 应用标识
    globalVariables: Optional[List[QlGlobalVariableVO]] = None
    #: 主键标识
    qlRecordId: Optional[str] = None
    #: QL类型：deepql|graphql|analysisql
    qlType: Optional[str] = None
    #: ql编码
    recordCode: Optional[str] = None
    #: 记录内容
    recordContent: Optional[str] = None
    #: 记录名称
    recordName: Optional[str] = None
    #: 记录类型：个人PERSONAL /公共：PUBLIC
    recordType: Optional[str] = None
    #: 变量
    variables: Any


ObjectParam.update_forward_refs()
ObjectLinkParam.update_forward_refs()
