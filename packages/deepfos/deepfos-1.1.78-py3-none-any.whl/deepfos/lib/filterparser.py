import collections
import re
from enum import Enum, IntEnum
from typing import *
from pydantic import Field

from deepfos.api.models import BaseModel, compat_parse_obj_as as parse_obj_as
from deepfos.core.logictable.nodemixin import NodeMixin, TreeRenderer
from deepfos.lib.utils import CIEnum, CIEnumMeta


class ConnectType(Enum):
    and_ = "AND"
    or_ = "OR"


class OperateType(Enum):
    equal = "EQUAL"
    not_equal = "NOT_EQUAL"
    in_list = "IN_LIST"
    not_in_list = "NOT_IN_LIST"
    in_expression = "IN_EXPRESSION"
    contains = "MIDDLE"
    start_with = "START_WITH"
    end_with = "END_WITH"
    is_null = "IS_NULL"
    not_null = "NOT_NULL"
    greater_than = "GREATER_THAN"
    less_than = "LESS_THAN"
    greater_equal = "GREATER_THAN_OR_EQUAL"
    less_equal = "LESS_THAN_OR_EQUAL"


class TimeType(IntEnum, metaclass=CIEnumMeta):
    year = 1
    quarter = 2
    month = 3
    day = 4


class FieldType(CIEnum):
    unset = 'UNSET'
    year = 'YEAR'
    month = 'MONTH'
    day = 'DAY'
    quarter = 'QUARTER'

    @classmethod
    def is_date(cls, type_):
        return type_ in (cls.year, cls.month, cls.day, cls.quarter)


class ConditionItem(BaseModel):
    operate: OperateType = None
    value: Any = None


class ColumnItem(BaseModel):
    alias: str = None
    columnName: str = None


class SelectColumnItem(ColumnItem):
    conditions: ConditionItem = None
    formatType: FieldType = FieldType.unset

    @property
    def real_conditions(self):
        return [self.conditions]


class SelectItem(BaseModel):
    connectType: ConnectType = None
    selectGroups: List[SelectColumnItem] = Field(default_factory=list)


class SelectDetail(BaseModel):
    selectedFilter: SelectItem = None
    selectedParam: SelectItem = None


class FilterItem(BaseModel):
    connectType: ConnectType = None
    filterGroups: List['FilterItem'] = Field(default_factory=list)
    alias: str = None
    columnName: str = None
    conditions: List[ConditionItem] = None
    operateType: ConnectType = None
    formatType: FieldType = FieldType.unset


FilterItem.update_forward_refs()


class MeasuresColumnItem(ColumnItem):
    collectMethod: str = None


class TimeColumnItem(ColumnItem):
    formatType: FieldType = None


class QueryInfo(BaseModel):
    selected: SelectDetail = None
    axisRanges: List[FilterItem] = Field(default_factory=list)
    columns: List[ColumnItem] = Field(default_factory=list)
    measures: List[MeasuresColumnItem] = Field(default_factory=list)
    orders: List = Field(default_factory=list)
    timeColumns: List[TimeColumnItem] = Field(default_factory=list)


class Parameter(BaseModel):
    queryInfo: QueryInfo = None
    chartInfo: Any = None


class Sql(str, Enum):
    SQL = 'sql'
    PANDAS_SQL = 'pandas_sql'


def string_replace(s):
    result = s.maketrans('[]', '()')
    value = s.translate(result)
    return value


def _add_func_to_sql(format_type, key, value, operator):
    """为拼接sql条件增加函数"""
    format_type = FieldType[format_type]
    if operator != " in " and operator != " not in ":
        value = f"'{value}'"
    if format_type == FieldType.year:
        return f"CONCAT(YEAR({key})){operator}{value}"
    elif format_type == FieldType.month:
        return f"CONCAT(YEAR({key}),'-',RIGHT(100+MONTH({key}),2)){operator}{value}"
    elif format_type == FieldType.day:
        return f"CONCAT(DATE({key})){operator}{value}"
    elif format_type == FieldType.quarter:
        return f"CONCAT(YEAR({key}),'-Q',QUARTER({key})){operator}{value}"


_RE_DATE_TYPE = re.compile('(?P<year>[0-9]{4})(?:-Q(?P<quarter>[0-9]))?'
                           '(?:-0?(?P<month>[0-9]{1,2}))?(?:-0?(?P<day>[0-9]{1,2}))?')


def _equal_with_pandas_dt(field_info: 'FieldNode', value: str, equal=True):
    dt_series = f"`{field_info.name}`.astype('datetime64[ns]').dt"
    precise = field_info.precise
    if equal:
        connect_type, op = 'and', '=='
    else:
        connect_type, op = 'or', '!='

    year, quarter, month, day = _RE_DATE_TYPE.match(value).groups()

    query_year = f"{dt_series}.year {op} {year}"
    query_month = f"{dt_series}.month {op} {month}"
    query_day = f"{dt_series}.day {op} {day}"
    # 兼容format date逻辑置后以后
    # 与原逻辑先format date后组织selectGroup中的筛选条件相比
    # 隐含的可能导致selectGroup中的条件中的日期格式
    # 与format date的时间格式不匹配的情况
    if month and day:
        if precise == TimeType.day:
            return f"({query_year} {connect_type} {query_month} {connect_type} {query_day})"
        if precise == TimeType.month:
            return f"({query_year} {connect_type} {query_month})"
        if precise == TimeType.quarter:
            query_quarter = f"{dt_series}.quarter {op} {to_quarter(month)}"
            return f"({query_year} {connect_type} {query_quarter})"

    if quarter:
        if precise >= TimeType.quarter:
            query_quarter = f"{dt_series}.quarter {op} {quarter}"
            return f"({query_year} {connect_type} {query_quarter})"

    if month:
        if precise >= TimeType.month:
            return f"({query_year} {connect_type} {query_month})"
        if precise == TimeType.quarter:
            query_quarter = f"{dt_series}.quarter {op} {to_quarter(month)}"
            return f"({query_year} {connect_type} {query_quarter})"

    return query_year


def to_quarter(month):
    return int((int(month) - 1) / 3) + 1


def _compare_with_pandas_dt(field_info: 'FieldNode', op: str, value: str):
    precise = field_info.precise
    dt_series = f"`{field_info.name}`.astype('datetime64[ns]').dt"
    year, quarter, month, day = _RE_DATE_TYPE.match(value).groups()
    query_year = f"{dt_series}.year {op} {year}"
    # 兼容format date逻辑置后以后
    # 与原逻辑先format date后组织selectGroup中的筛选条件相比
    # 隐含的可能导致selectGroup中的条件中的日期格式
    # 与format date的时间格式不匹配的情况
    if month and day:
        if precise == TimeType.day:
            return f"({dt_series}.year {op[0]} {year} or " \
                   f"({dt_series}.year == {year} and {dt_series}.month {op[0]} {month}) or " \
                   f"({dt_series}.year == {year} and {dt_series}.month == {month} and {dt_series}.day {op} {day}))"

        if precise == TimeType.month:
            return f"({dt_series}.year {op[0]} {year} or " \
                   f"({dt_series}.year == {year} and {dt_series}.month {op} {month}))"

        if precise == TimeType.quarter:
            return f"({dt_series}.year {op[0]} {year} or " \
                   f"({dt_series}.year == {year} and {dt_series}.quarter {op} {to_quarter(month)}))"

    if quarter:
        if precise >= TimeType.quarter:
            return f"({dt_series}.year {op[0]} {year} or " \
                   f"({dt_series}.year == {year} and {dt_series}.quarter {op} {quarter}))"

    if month:
        if precise >= TimeType.month:
            return f"({dt_series}.year {op[0]} {year} or " \
                   f"({dt_series}.year == {year} and {dt_series}.month {op} {month}))"

        if precise == TimeType.quarter:
            return f"({dt_series}.year {op[0]} {year} or " \
                   f"({dt_series}.year == {year} and {dt_series}.quarter {op} {to_quarter(month)}))"

    return query_year


dim_members, date_type_fields, dt_precision = {}, {}, {}


def set_dim_members(new_members):
    global dim_members
    dim_members = new_members


def set_date_type_fields(new_fields):
    global date_type_fields
    date_type_fields = new_fields


def set_dt_precision(new_precisions):
    global dt_precision
    dt_precision = new_precisions


def maybe_adapt_real_field_type(column_name, field_type):
    # 兼容2023-02-20迭代前，时间信息取自timeColumns的逻辑
    if field_type == FieldType.unset and column_name in date_type_fields:
        maybe_timetype = date_type_fields[column_name]
        field_type = FieldType[maybe_timetype]
    return field_type


class _BaseOperatorNode(NodeMixin):
    """
    逻辑操作节点基类
    """

    def __init__(self, op):
        self.op = op

    def __str__(self):  # pragma: no cover
        return f"<{self.op}>"

    def get_where_expression(self, sql):
        """
        获取df.query()条件表达式
        """
        if sql == Sql.SQL:
            return self.op.to_sql()
        if sql == Sql.PANDAS_SQL:
            return self.op.to_pandas_sql()

    def to_pandas_sql(self):
        """
        组装不同逻辑操作的条件表达式
        """
        raise NotImplementedError


class LogicalOrOP(_BaseOperatorNode):
    """or 操作"""

    def to_pandas_sql(self):
        result = ' or '.join(filter(lambda x: x not in ('', '()'),
                                    [child.to_pandas_sql() for child in self.children]))
        return f"({result})" if result else ''

    def to_sql(self):
        result = ' or '.join(filter(lambda x: x not in ('', '()'),
                                    [child.to_sql() for child in self.children]))
        return f"({result})" if result else ''


class LogicalAndOP(_BaseOperatorNode):
    """and 操作"""

    def to_pandas_sql(self):
        result = ' and '.join(filter(lambda x: x not in ('', '()'),
                                     [child.to_pandas_sql() for child in self.children]))
        return f"({result})" if result else ''

    def to_sql(self):
        result = ' and '.join(filter(lambda x: x not in ('', '()'),
                                     [child.to_sql() for child in self.children]))
        return f"({result})" if result else ''


class LogicalEqualOP(_BaseOperatorNode):
    """==(equal)操作"""

    def to_pandas_sql(self):
        value = self.children[1].value
        column_name = self.children[0].name

        if FieldType.is_date(self.children[0].type):
            return _equal_with_pandas_dt(self.children[0], value)

        if isinstance(value, str):
            return f"`{column_name}` == '{value}'"

        return f"`{column_name}` == {value}"

    def to_sql(self):
        column_name = self.children[0].name
        value = string_replace(str(self.children[1].value))
        field_type = self.children[0].type

        if FieldType.is_date(field_type):
            sql = _add_func_to_sql(field_type, column_name, value, "=")
            return sql

        if isinstance(self.children[1].value, str):
            return f"{column_name} = '{value}'"

        return f"{column_name} = {value}"


class LogicalNotEqualOP(_BaseOperatorNode):
    """!=(NotEqual)操作"""

    def to_pandas_sql(self):
        value = self.children[1].value
        column_name = self.children[0].name

        if FieldType.is_date(self.children[0].type):
            return _equal_with_pandas_dt(self.children[0], value, False)

        if isinstance(value, str):
            return f"`{column_name}` != '{value}'"

        return f"`{column_name}` != {value}"

    def to_sql(self):
        column_name = self.children[0].name
        value = string_replace(str(self.children[1].value))
        field_type = self.children[0].type

        if FieldType.is_date(field_type):
            sql = _add_func_to_sql(field_type, column_name, value, "!=")
            return sql

        if isinstance(self.children[1].value, str):
            return f"{column_name} != '{value}'"

        return f"{column_name} != {value}"


class LogicalInListOP(_BaseOperatorNode):
    """in(InList) 操作"""

    def to_pandas_sql(self):
        column_name = self.children[0].name

        if FieldType.is_date(self.children[0].type):
            filters = []
            for each in self.children[1].value:
                filters.append(_equal_with_pandas_dt(self.children[0], each))

            return f"({' or '.join(filters)})"

        return f"`{column_name}` in {self.children[1].value}"

    def to_sql(self):
        column_name = self.children[0].name
        value = string_replace(str(self.children[1].value))
        field_type = self.children[0].type

        if FieldType.is_date(field_type):
            sql = _add_func_to_sql(field_type, column_name, value, " in ")
            return sql

        return f"{self.children[0].name} in {value}"


class LogicalNotInListOP(_BaseOperatorNode):
    """not in(NotInList) 操作"""

    def to_pandas_sql(self):
        column_name = self.children[0].name

        if FieldType.is_date(self.children[0].type):
            filters = []
            for each in self.children[1].value:
                filters.append(_equal_with_pandas_dt(self.children[0], each, False))

            return f"({' and '.join(filters)})"

        return f"`{column_name}` not in {self.children[1].value}"

    def to_sql(self):
        column_name = self.children[0].name
        value = string_replace(str(self.children[1].value))
        field_type = self.children[0].type

        if FieldType.is_date(field_type):
            sql = _add_func_to_sql(field_type, column_name, value, " not in ")
            return sql

        return f"{self.children[0].name} not in {value}"


class LogicalInExpressionOP(_BaseOperatorNode):
    """维度表达式操作, 经dim query后等同于 in dim members"""

    def to_pandas_sql(self):
        name = self.children[0].name
        if dim_members and name in dim_members:
            return f"`{name}` in {dim_members[name]}"

        return ""

    def to_sql(self):
        name = self.children[0].name
        if dim_members and name in dim_members:
            value = string_replace(str(dim_members[name]))
            return f"{name} in {value}"

        return ""


class LogicalContainsOP(_BaseOperatorNode):
    """contains 操作：df['col'].str.contains('xxx')"""

    def to_pandas_sql(self):
        return f"`{self.children[0].name}`.str.contains('{self.children[1].value}')"

    def to_sql(self):
        return f"{self.children[0].name} like '%{self.children[1].value}%'"


class LogicalStartWithOP(_BaseOperatorNode):
    """StartWith 操作:df['col'].str.startswith('xxx')"""

    def to_pandas_sql(self):
        return f"`{self.children[0].name}`.str.startswith('{self.children[1].value}')"

    def to_sql(self):
        return f"{self.children[0].name} like '{self.children[1].value}%'"


class LogicalEndWithOP(_BaseOperatorNode):
    """EndWith 操作:df['col'].str.endswith('xxx')"""

    def to_pandas_sql(self):
        return f"`{self.children[0].name}`.str.endswith('{self.children[1].value}')"

    def to_sql(self):
        return f"{self.children[0].name} like '%{self.children[1].value}'"


class LogicalIsNullOP(_BaseOperatorNode):
    """IsNull 操作:df['col'].isnull()"""

    def to_pandas_sql(self):
        return f"`{self.children[0].name}`.isnull()"

    def to_sql(self):
        return f"{self.children[0].name} is null"


class LogicalNotNullOP(_BaseOperatorNode):
    """IsNotNull 操作:df['col'].notnull()"""

    def to_pandas_sql(self):
        return f"`{self.children[0].name}`.notnull()"

    def to_sql(self):
        return f"{self.children[0].name} is not null"


class LogicalGreaterThanOP(_BaseOperatorNode):
    """> (GREATER_THAN)"""

    def to_pandas_sql(self):
        value = self.children[1].value
        column_name = self.children[0].name

        if FieldType.is_date(self.children[0].type):
            return _compare_with_pandas_dt(self.children[0], '>', value)

        if isinstance(value, str):
            return f"`{column_name}` > '{value}'"

        return f"`{column_name}` > {value}"

    def to_sql(self):
        column_name = self.children[0].name
        value = string_replace(str(self.children[1].value))
        field_type = self.children[0].type

        if FieldType.is_date(field_type):
            sql = _add_func_to_sql(field_type, column_name, value, ">")
            return sql

        if isinstance(self.children[1].value, str):
            return f"{column_name} > '{value}'"

        return f"{column_name} > {value}"


class LogicalLessThanOP(_BaseOperatorNode):
    """< (LESS_THAN)"""

    def to_pandas_sql(self):
        value = self.children[1].value
        column_name = self.children[0].name

        if FieldType.is_date(self.children[0].type):
            return _compare_with_pandas_dt(self.children[0], '<', value)

        if isinstance(value, str):
            return f"`{column_name}` < '{value}'"

        return f"`{column_name}` < {value}"

    def to_sql(self):
        column_name = self.children[0].name
        value = string_replace(str(self.children[1].value))
        field_type = self.children[0].type

        if FieldType.is_date(field_type):
            sql = _add_func_to_sql(field_type, column_name, value, "<")
            return sql

        if isinstance(self.children[1].value, str):
            return f"{column_name} < '{value}'"

        return f"{column_name} < {value}"


class LogicalGreaterEqualOP(_BaseOperatorNode):
    """>= (GREATER_THAN_OR_EQUAL)"""

    def to_pandas_sql(self):
        value = self.children[1].value
        column_name = self.children[0].name

        if FieldType.is_date(self.children[0].type):
            return _compare_with_pandas_dt(self.children[0], '>=', value)

        if isinstance(value, str):
            return f"`{column_name}` >= '{value}'"

        return f"`{column_name}` >= {value}"

    def to_sql(self):
        column_name = self.children[0].name
        value = string_replace(str(self.children[1].value))
        field_type = self.children[0].type

        if FieldType.is_date(field_type):
            sql = _add_func_to_sql(field_type, column_name, value, ">=")
            return sql

        if isinstance(self.children[1].value, str):
            return f"{column_name} >= '{value}'"

        return f"{column_name} >= {value}"


class LogicalLessEqualOP(_BaseOperatorNode):
    """<= (LESS_THAN_OR_EQUAL)"""

    def to_pandas_sql(self):
        value = self.children[1].value
        column_name = self.children[0].name

        if FieldType.is_date(self.children[0].type):
            return _compare_with_pandas_dt(self.children[0], '<=', value)

        if isinstance(value, str):
            return f"`{column_name}` <= '{value}'"

        return f"`{column_name}` <= {value}"

    def to_sql(self):
        column_name = self.children[0].name
        value = string_replace(str(self.children[1].value))
        field_type = self.children[0].type

        if FieldType.is_date(field_type):
            sql = _add_func_to_sql(field_type, column_name, value, "<=")
            return sql

        if isinstance(self.children[1].value, str):
            return f"{column_name} <= '{value}'"

        return f"{column_name} <= {value}"


class FieldNode(NodeMixin):
    def __init__(self, name, type_=FieldType.unset, precise=None):
        self.name = name
        self.type = maybe_adapt_real_field_type(name, type_)
        self.precise = precise

    def __str__(self):  # pragma: no cover
        return self.name


class ComparisonVal(NodeMixin):
    def __init__(self, value):
        self.value = value

    def __str__(self):  # pragma: no cover
        return str(self.value)


class LogicalOpFactory:
    """逻辑操作类的匹配工厂"""
    cls_map = {
        ConnectType.or_: LogicalOrOP,
        ConnectType.and_: LogicalAndOP,
        OperateType.equal: LogicalEqualOP,
        OperateType.not_equal: LogicalNotEqualOP,
        OperateType.in_list: LogicalInListOP,
        OperateType.not_in_list: LogicalNotInListOP,
        OperateType.in_expression: LogicalInExpressionOP,
        OperateType.contains: LogicalContainsOP,
        OperateType.start_with: LogicalStartWithOP,
        OperateType.end_with: LogicalEndWithOP,
        OperateType.is_null: LogicalIsNullOP,
        OperateType.not_null: LogicalNotNullOP,
        OperateType.greater_than: LogicalGreaterThanOP,
        OperateType.less_than: LogicalLessThanOP,
        OperateType.greater_equal: LogicalGreaterEqualOP,
        OperateType.less_equal: LogicalLessEqualOP
    }

    def __new__(cls, value) -> NodeMixin:
        target_cls = cls.cls_map.get(value)
        if target_cls is None:  # pragma: no cover
            raise ValueError(f"Unknown Value for python chart: {value}")
        return target_cls(value)


class ASTRoot(NodeMixin):
    pass


class FilterParser:
    """筛选逻辑树解析类"""
    def __init__(
        self,
        source: Union[Dict, FilterItem, SelectItem],
        _all_enable_dim_columns: list = None,
        exclude_dim_expr: bool = False,
        date_round: bool = False
    ):
        if isinstance(source, dict):
            source = parse_obj_as(FilterItem, source)
        self.source = source
        self.root = ASTRoot()
        self._all_enable_dim_columns = _all_enable_dim_columns or []
        self.axis_dim_fields_to_expr = collections.defaultdict(list)
        # 解析时是否去除维度表达式(维度类型字段)
        self.exclude_dim_expr = exclude_dim_expr
        self.date_round = date_round

    def parse(self):
        self.parse_node(self.source).set_parent(self.root)

    def parse_node(self, source: Union[FilterItem, SelectItem]) -> NodeMixin:
        if source.connectType:
            logic_node_obj = LogicalOpFactory(source.connectType)

            if isinstance(source, FilterItem):
                for node_source in source.filterGroups:
                    node = self.parse_node(node_source)
                    if node:
                        node.set_parent(logic_node_obj)
                return logic_node_obj
            else:
                for node_source in source.selectGroups:
                    node = self.parse_condition(node_source)
                    if node:
                        node.set_parent(logic_node_obj)
                return logic_node_obj
        else:
            return self.parse_condition(source)

    def parse_condition(self, source: Union[FilterItem, SelectColumnItem]) -> Optional[NodeMixin]:
        if self.date_round is False:
            if FieldType.is_date(source.formatType) and (precise := dt_precision.get(source.columnName)):
                if precise < TimeType[source.formatType]:
                    raise ValueError('筛选条件包含了低精度日期值与高精度日期值的比较操作\n'
                                     f'当前数据列名: <{source.columnName}>, 配置精度: {precise.name}')

        conditions = source.conditions if isinstance(source, FilterItem) else source.real_conditions
        # FilterItem中的维度列特殊处理
        if isinstance(source, FilterItem) and source.columnName in self._all_enable_dim_columns:
            # 维度类型字段只有一个条件
            self.axis_dim_fields_to_expr[source.columnName].append(conditions[0].value)
            # 如果该字段是维度类型且本次解析需要去除维度表达式，则无需解析
            if self.exclude_dim_expr:
                return

        # 如果有多个条件，使用新的子级逻辑连接
        if len(conditions) > 1:
            logical_op = LogicalOpFactory(source.operateType)
            for cond in conditions:
                comp_op = LogicalOpFactory(cond.operate)
                comp_op.set_parent(logical_op)
                FieldNode(source.columnName, source.formatType, dt_precision.get(source.columnName)).set_parent(comp_op)
                if cond.value is not None:
                    ComparisonVal(cond.value).set_parent(comp_op)
        # 如果只有一个条件，不创建新的子级，使用父级的逻辑连接
        else:
            logical_op = LogicalOpFactory(conditions[0].operate)
            FieldNode(source.columnName, source.formatType, dt_precision.get(source.columnName)).set_parent(logical_op)
            if conditions[0].value is not None:
                ComparisonVal(conditions[0].value).set_parent(logical_op)

        return logical_op

    def debug(self):  # pragma: no cover
        TreeRenderer().show(self.root)

    def make_query(self, dim_mbrs=None, date_fields=None, sql: Enum = Sql.PANDAS_SQL) -> str:
        query = _BaseOperatorNode(self.root.children[0])
        global dim_members, date_type_fields
        if dim_mbrs is not None:
            dim_members = dim_mbrs
        if date_fields is not None:
            date_type_fields = date_fields
        return query.get_where_expression(sql)
