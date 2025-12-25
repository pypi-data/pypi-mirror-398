"""python作为图表组件数据源"""
import collections
import functools
import asyncio
from inspect import isfunction
from pandas import DataFrame
from typing import *
import pandas as pd
from pydantic import Field

from deepfos.api.models import compat_parse_obj_as as parse_obj_as
from deepfos.lib.asynchronous import evloop
from deepfos.api.models import BaseModel
from deepfos.api.dimension import DimensionAPI
from deepfos.api.smartlist import SmartListAPI
from deepfos.element.base import ElementBase
from deepfos.lib.decorator import cached_property
from deepfos.lib.filterparser import set_date_type_fields, set_dt_precision, Parameter, TimeType, FilterParser, \
    FieldType, Sql
from deepfos.lib.utils import unpack_expr, dict_to_expr

__all__ = [
    'BaseField',
    'BoundField',
    'Text',
    'Number',
    'Date',
    'Dimension',
    'SmartList',
    'Person',
    'Struct',
    'as_datasource',
    'StructMeta',
    'ChartEngine',
    'HandleExpr',
    'Filter'
]

FLAG_FOR_META = 'describe'


class DimElement(ElementBase):
    api_class = DimensionAPI
    api: DimensionAPI


class SmlElement(ElementBase):
    api_class = SmartListAPI
    api: SmartListAPI


def as_dict(self=None, exclude_none: bool = True) -> Dict:
    # will be bound to NamedTuple, self is actually positional
    result = {}
    for k, v in self._asdict().items():
        if v is not None or (v is None and not exclude_none):
            try:
                result[k] = v.as_dict(exclude_none)  # noqa
            except AttributeError:
                result[k] = v
    return result


# 字段名
COLUMN_NAME = 'columnName'
# 字段描述
DESC = 'description'
# 字段逻辑信息
LOGIC_INFO = 'logicInfo'
# 表示元素字段的类型
VALUE_KEY = 'valueKey'
# 表示值列表的选中值
VALUE_FIELD = 'valueField'


# -----------------------------------------------------------------------------
# Data Source Struct
class ElementDetail(NamedTuple):
    elementName: str
    elementType: str
    folderId: str = None
    path: str = None
    serverName: str = None
    absoluteTag: bool = True

    as_dict = as_dict


class LogicInfo(NamedTuple):
    valueType: int
    valueKey: str = None
    elementDetail: ElementDetail = None

    as_dict = as_dict


class BaseField(BaseModel):
    code: Optional[int] = None
    columnName: Optional[str] = None
    description: Optional[str] = None
    value_key: Optional[str] = None

    def __init__(self, name: str = None, description: str = None, **data):
        super().__init__(columnName=name, description=description, **data)

    @property
    def logic_info(self) -> LogicInfo:
        return LogicInfo(valueType=self.code)

    def to_dict(self) -> Dict:
        if self.description is None:
            self.description = self.columnName
        result = self.dict(include={COLUMN_NAME, DESC})
        result.update({LOGIC_INFO: self.logic_info.as_dict()})
        return result

    @property
    def name(self):
        return self.columnName

    def __setattr__(self, name, value):
        if name == 'name':
            self.columnName = value
        else:
            super().__setattr__(name, value)


class Text(BaseField):
    code: int = 1


class Date(BaseField):
    code: int = 11
    # 前端时间筛选器颗粒度字段；4：最宽泛的颗粒度
    value_key: str = '4'
    precision: TimeType = TimeType.day

    @property
    def logic_info(self) -> LogicInfo:
        return LogicInfo(valueType=self.code, valueKey=self.value_key)


class Number(BaseField):
    code: int = 15


class Person(BaseField):
    code: int = 12


class BoundField(BaseField):
    code: int = None
    element_name: str = None
    folder_id: str = None
    path: str = None
    bound_class: Type[ElementBase] = None
    value_field: List[Any] = Field(default_factory=list)

    def __init__(
            self,
            element_name: str,
            folder_id: str = None,
            path: str = None,
            value_key: str = None,
            value_field: list = None,
            name: str = None,
            description: str = None,
            **data
    ):
        super().__init__(name=name, description=description, **data)
        self.element_name = element_name
        self.folder_id = folder_id
        self.path = path
        self.value_field = value_field or []

    async def get_element_detail(self) -> ElementDetail:
        ele = await self.bound_class(  # noqa
            element_name=self.element_name,
            folder_id=self.folder_id,
            path=self.path
        )._get_element_info()
        return ElementDetail(
            elementName=self.element_name,
            elementType=ele.elementType,
            folderId=ele.folderId,
            path=self.path,
            serverName=ele.serverName
        )

    async def async_to_dict(self) -> Dict:
        result = super().to_dict()
        element_detail = await self.get_element_detail()
        logic_info = self.logic_info._replace(elementDetail=element_detail)
        result.update({LOGIC_INFO: logic_info.as_dict()})
        return result


class SmartList(BoundField):
    code: int = 3
    bound_class: Type[ElementBase] = SmlElement

    async def async_to_dict(self) -> Dict:
        result = super().to_dict()
        element_detail = await self.get_element_detail()
        logic_info = self.logic_info._replace(elementDetail=element_detail)
        result.update({LOGIC_INFO: logic_info.as_dict()})
        result[VALUE_KEY] = logic_info.elementDetail.elementName
        result[VALUE_FIELD] = self.value_field
        return result


class Dimension(BoundField):
    code: int = 8
    bound_class: Type[ElementBase] = DimElement


class StructMeta(type):
    def __new__(mcs, cls_name, bases, namespace: dict):
        fields = []

        for field_name, anno in namespace.get('__annotations__', {}).items():
            if issubclass(anno, BoundField):
                if field_name not in namespace:
                    raise ValueError(f"Bound field: <{field_name}> must have a default value.")

                field = namespace.pop(field_name)
                if field.columnName is None:
                    field.columnName = field_name
                if not isinstance(field, anno):
                    raise TypeError(
                        f"Expect type {anno} for field: <{field_name}>, but got {type(field)}")
                fields.append(field)

            elif issubclass(anno, BaseField):
                if field_name not in namespace:
                    fields.append(anno(name=field_name))

        collected = []

        for k, v in namespace.items():
            if isinstance(v, BaseField):
                collected.append(k)
                if v.columnName is None:  # 如果name字段赋值了，就取name字段的值
                    v.columnName = k
                fields.append(v)

        for k in collected:
            namespace.pop(k)

        namespace['fields'] = fields

        return super().__new__(mcs, cls_name, bases, namespace)

    def to_dict(cls):
        columns_meta = []
        sml_or_dim = []
        futures = []
        for field in cls.fields:
            if isinstance(field, BoundField):
                sml_or_dim.append(field)
            elif isinstance(field, BaseField):
                columns_meta.append(field.to_dict())

        for field in sml_or_dim:
            future = evloop.apply(field.async_to_dict())
            futures.append(future)

        for future in futures:
            columns_meta.append(future.result())

        return {
            "__AsSource__": True,
            "columns": columns_meta
        }

    def get_dim_fields(cls):
        result = {}
        for field in cls.fields:
            if isinstance(field, Dimension):
                result[field.columnName] = (field.path, field.folder_id)
        return result


class Struct(metaclass=StructMeta):
    """help class"""


def _agg_to_dict(agg_func_col, df, column_name_to_alias):
    """针对只有聚合操作但是没有分组的情况做处理：
    1.先求聚合
    2.将结果按照'分组且聚合的方式'转为dict
    3.支持返回字段为alias的形式
    """
    df = df.agg(agg_func_col)
    res = dict()
    for col in df.columns:
        for ind in df.index:
            if str(df.loc[ind, col]) == 'nan':
                continue
            res[f'{col}#{ind}'] = df.loc[ind, col]

    for k, v in column_name_to_alias.items():
        if v in res:
            value = res.pop(v)
            res[k] = value
    return [res]


def _batch_get_mbrs_by_expr(
    fix: Dict[str, Union[str, list]],
    paths: Union[str, Dict[str, Tuple[str, str]]] = None,
) -> dict:
    """根据批量维度表达式异步调用获取解析结果"""
    from deepfos.element.dimension import AsyncDimension

    if isinstance(paths, dict):
        path_getter = paths.__getitem__
    else:
        path_getter = lambda _: (paths, None)

    # 遍历fix，如果fix的值为str，则认为是维度表达式，将表达式转换为成员list
    mbrs = {}
    futures = []

    for dim, exp in fix.items():
        if isinstance(exp, str):
            if "(" not in exp:
                exp = exp.strip(dim)
                exp = exp.strip('{').strip('}')
                mbrs[dim] = exp.split(';')
            else:
                path, folder_id = path_getter(dim)
                future = evloop.apply(AsyncDimension(element_name=dim, path=path, folder_id=folder_id).query(
                    expression=exp, fields=['name'], as_model=False
                ))

                futures.append((dim, future))
        else:
            mbrs[dim] = exp

    for dim, future in futures:
        mbrs[dim] = [item['name'] for item in future.result()]
    return mbrs


class Filter:
    def __init__(
        self,
        params: Union[Dict, Parameter],
        struct: Type[Struct] = None,
        all_enable_dim_columns=None,
        date_round=False
    ):
        if isinstance(params, dict):
            params = parse_obj_as(Parameter, params)
        self.params = params
        self.struct = struct
        self._all_enable_dim_columns = all_enable_dim_columns
        self.date_round = date_round

    def apply(
        self,
        df: pd.DataFrame,
        exclude_dim_expr: bool = True
    ) -> pd.DataFrame:
        """根据筛选条件对数据源进行过滤处理

        Args:
            df: 需要过滤的数据源
            exclude_dim_expr: 是否排除维度表达式，默认为True，只对维度类型之外的字段进行条件过滤
        """
        where = self.as_pandas_sql(exclude_dim_expr=exclude_dim_expr)
        if not where:
            return df

        return df.query(where)

    def _axis_where(self, sql_type, exclude_dim_expr: bool = True):
        if len(self.params.queryInfo.axisRanges) == 0:
            return ''

        parser = FilterParser(
            self.params.queryInfo.axisRanges[0],
            self._all_enable_dim_columns,
            exclude_dim_expr=exclude_dim_expr,
            date_round=self.date_round
        )
        parser.parse()
        dim_mbrs = {}

        if not exclude_dim_expr and parser.axis_dim_fields_to_expr:
            # 如果不排除维度，则需要在获取where表达式之前解析所有维度表达式
            # 异步请求获取批量维度表达式的解析结果
            # 多组合中可能出现多个相同的维度，将list中 多个维度处理为或（;）的关系
            _axis_dim_fields_to_expr = collections.defaultdict(list)
            dim_expr = {}  # 存储维度元素的元素名和表达式的映射
            column_name_to_dim_name = {}  # 存储字段列名和对应的维度元素名称的映射

            for column_name, expr_list in parser.axis_dim_fields_to_expr.items():
                # 同column_name对应的表达式为同一个维度的，dim_name不变，以第一个为准即可
                dim_name = None
                for expr in expr_list:
                    _dim_name, v = unpack_expr(expr)

                    if dim_name is None:
                        dim_name = _dim_name
                        if dim_name != column_name:
                            column_name_to_dim_name[column_name] = dim_name
                            self._all_enable_dim_columns[dim_name] = self._all_enable_dim_columns[column_name]

                    _axis_dim_fields_to_expr[dim_name].append(v)

                single_dim_expr = dict_to_expr(_axis_dim_fields_to_expr)
                dim_expr[dim_name] = single_dim_expr
                _axis_dim_fields_to_expr.clear()

            dim_mbrs = _batch_get_mbrs_by_expr(fix=dim_expr, paths=self._all_enable_dim_columns)
            empty_dim_mbrs = [dim for dim, member in dim_mbrs.items() if not member]

            if empty_dim_mbrs:
                raise ValueError(f"({','.join(empty_dim_mbrs)})解析维度成员结果为空!")

            # 将键为维度名，值为维度成员的字典替换为键为列名，值为维度成员的字典
            for c, d in column_name_to_dim_name.items():
                if d in dim_mbrs:
                    dim_mbrs[c] = dim_mbrs.pop(d)

        return parser.make_query(dim_mbrs=dim_mbrs, sql=sql_type)

    def _pov_where(self, sql_type=Sql.PANDAS_SQL):
        parser = FilterParser(self.params.queryInfo.selected.selectedFilter, date_round=self.date_round)
        parser.parse()
        # 兼容2023-02-20迭代前，前置format date
        # 导致SelectGroup和filterGroup内时间信息取自timeColumns的逻辑
        date_fields = {group.columnName: group.formatType for group in self.params.queryInfo.timeColumns}
        return parser.make_query(date_fields=date_fields, sql=sql_type)

    def _generate_where(self, sql_type=Sql.PANDAS_SQL, exclude_dim_expr: bool = True):
        # pov:where条件
        pov_where = self._pov_where(sql_type)
        # axis:where条件
        axis_where = self._axis_where(sql_type, exclude_dim_expr=exclude_dim_expr)

        if pov_where and axis_where:
            return f'{axis_where} and ({pov_where})'
        if axis_where:
            return axis_where
        if pov_where:
            return f'({pov_where})'

    def as_sql(self, exclude_dim_expr: bool = True) -> str:
        """获取MySql格式的过滤条件"""
        return self._generate_where(Sql.SQL, exclude_dim_expr)

    def as_pandas_sql(self, exclude_dim_expr: bool = True) -> str:
        """组装符合pandas格式的sql"""
        return self._generate_where(exclude_dim_expr=exclude_dim_expr)

    def agg(self, df: pd.DataFrame) -> pd.DataFrame:
        """对df 进行分组，聚合，重命名处理"""
        # 分组，聚合，排序，重命名alias
        group_by_col = []
        agg_func_col = {}
        column_name_to_alias = {}

        # 分组普通字段
        for group in self.params.queryInfo.columns:
            group_by_col.append(group.columnName)
            column_name_to_alias[group.alias] = group.columnName

        # 分组时间类型字段
        for group in self.params.queryInfo.timeColumns:
            column_name = group.columnName
            group_by_col.append(column_name)
            column_name_to_alias[group.alias] = group.columnName

        # 聚合字段
        for column in self.params.queryInfo.measures:
            column_name = column.columnName
            alias = column.alias
            collect_method = column.collectMethod
            # 聚合操作中:会有一个字段多个不同类型的聚合，会有一个字段多次同种聚合类型的运算
            if collect_method:
                column_alias = f'{column_name}#{collect_method.lower()}'
                # alias设为key，因为column_alias可能存在重复
                column_name_to_alias[alias] = column_alias
                if column_name in agg_func_col:
                    agg_func_col[column_name].append(collect_method.lower())
                else:
                    agg_func_col[column_name] = [collect_method.lower()]

        # 分组字段：处理存在为空的列重新赋值为 ''，防止记录丢失
        for item in group_by_col:
            if item in df:
                df[item] = df[item].fillna('')

        if group_by_col and agg_func_col:
            df = df.groupby(group_by_col, as_index=False, sort=False).agg(agg_func_col)
        elif agg_func_col:
            data = _agg_to_dict(agg_func_col, df, column_name_to_alias)
            return pd.DataFrame(data)
        elif group_by_col:
            raise ValueError('数据分组后，缺少聚合函数')

        # 将df的MultiIndex转为Index，并且调整列名格式
        columns = ['#'.join(col).strip().rstrip('#') for col in df.columns.values]
        for k, v in column_name_to_alias.items():
            if v in columns:
                columns[columns.index(v)] = k

        df.columns = columns

        return df


class HandleExpr:
    def __init__(self, params: Union[Dict, Parameter], struct: Type[Struct] = None, all_enable_dim_columns=None):
        if isinstance(params, dict):
            params = parse_obj_as(Parameter, params)
        self.params = params
        self.struct = struct
        self._all_enable_dim_columns = all_enable_dim_columns
        self.parser = None
        self._load_axis_expr()

    def _load_axis_expr(self):
        """将组合（axisRanges)中的字段进行解析"""
        if self.params.queryInfo.axisRanges:
            parser = FilterParser(self.params.queryInfo.axisRanges[0], self._all_enable_dim_columns)
            parser.parse()  # 此解析过程会将维度类型字段和对应的维度表达式进行映射
            self.parser = parser

    def as_string(self) -> str:
        """将维度表达式作为字符串返回"""
        result = collections.defaultdict(list)
        expr_pov = self.get_pov()
        expr_axis = self.get_axis()

        for k, v in expr_pov.items():
            result[k].extend(v)

        for column_name, values in expr_axis.items():
            # 同一个维度可能会同时出现在多个行列组合中，故在axis中也会存在一个字段多个维度表达式的情况
            for value in values:
                k, v = unpack_expr(value)
                # 维度表达式拼接是的字段列名+表达式（筛选器和行列都是都是如此）
                result[column_name].append(v)

        result = dict_to_expr(result)
        return result

    def get_dim_expr_dict(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """将维度表达式以字典形式返回"""
        result = {
            'selectedFilter': self.get_pov(),
            'axisRanges': self.get_axis()
        }
        return result

    def get_pov(self, include_variable: bool = False) -> Dict[str, Union[List[str]]]:
        """只获取筛选器上的维度表达式

        在组合行列中出现的字段如果是被@cur替换过了，
        那么筛选器上的该相同字段的值就失效了，
        此处根据参数决定是否仍然获取失效的字段值

        Args:
            include_variable: 是否获取@cur替换后的失效的字段值，默认False不获取
        """
        expr_dict = collections.defaultdict(list)
        selected = self.params.queryInfo.selected

        if param := selected.selectedFilter:
            for item in param.selectGroups:
                if item.columnName in self._all_enable_dim_columns:
                    expr_dict[item.columnName].extend(item.real_conditions[0].value)

        if not include_variable:
            return expr_dict

        if param := selected.selectedParam:
            for item in param.selectGroups:
                if item.columnName in self._all_enable_dim_columns:
                    expr_dict[item.columnName].extend(item.real_conditions[0].value)

        return expr_dict

    def get_axis(self) -> Dict[str, Union[List[str]]]:
        """只获取组合中的维度表达式"""
        if self.parser:  # 有组合类型（axisRanges）数据
            expr_dict = self.parser.axis_dim_fields_to_expr
        else:
            expr_dict = collections.defaultdict(list)
        return expr_dict


class ChartEngine:
    def __init__(self, params: Dict, struct: Type[Struct] = None, before_return=None, date_round=False):
        self.raw_params = params
        self.params = parse_obj_as(Parameter, params)
        self.struct = struct
        self.all_enable_dim_columns = struct.get_dim_fields()
        self.before_return = before_return
        self.date_round = date_round
        self.init_parser_env()

    def init_parser_env(self):
        set_date_type_fields(
            {col.columnName: col.formatType
             for col in self.params.queryInfo.timeColumns}
        )
        set_dt_precision(
            {col.columnName: col.precision
             for col in self.struct.fields if isinstance(col, Date)}
        )

    @cached_property
    def filter(self) -> Filter:
        return Filter(self.params, self.struct, self.all_enable_dim_columns, self.date_round)

    @cached_property
    def expr(self) -> HandleExpr:
        return HandleExpr(self.params, self.struct, self.all_enable_dim_columns)

    def get_dim_expr_dict(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """以字典格式获取维度表达式结果"""
        return self.expr.get_dim_expr_dict()

    def get_dim_expr_str(self) -> str:
        """以字符串格式获取维度表达式结果"""
        return self.expr.as_string()

    def get_pov(self, include_variable: bool = False) -> Dict[str, Union[List[str]]]:
        """只获取筛选器上的维度表达式

        在组合行列中出现的字段如果是被@cur替换过了，
        那么筛选器上的该相同字段的值就失效了，
        此处根据参数决定是否仍然获取失效的字段值

        Args:
            include_variable: 是否获取@cur替换后的失效的字段值，默认False不获取
        """
        return self.expr.get_pov(include_variable)

    def get_axis(self) -> Dict[str, Union[List[str]]]:
        """获取行列组合上的维度表达式"""
        return self.expr.get_axis()

    def get_sql(self, exclude_dim_expr: bool = True) -> str:
        """获取MySql格式的where条件表达式

        Args:
            exclude_dim_expr: 过滤时是否去除维度表达式，默认True:去除
        """
        return self.filter.as_sql(exclude_dim_expr=exclude_dim_expr)

    def apply_filter(
        self,
        df: pd.DataFrame,
        exclude_dim_expr: bool = True
    ) -> pd.DataFrame:
        """根据筛选条件对数据源进行过滤处理

        Args:
            df: 要进行过滤的数据源
            exclude_dim_expr: 过滤时是否去除维度表达式，默认True:去除
        """
        df = self.filter.apply(df, exclude_dim_expr=exclude_dim_expr)
        return self._format_date(df)

    def apply_agg(self, df: pd.DataFrame, date_formated: bool = False) -> pd.DataFrame:
        """根据分组和聚合函数进行聚合处理"""
        if not date_formated:
            df = self._format_date(df)
        return self.filter.agg(df)

    def _format_date(self, df: pd.DataFrame):
        """对日期类型进行格式化处理"""
        for column in self.params.queryInfo.timeColumns:
            column_name = column.columnName
            if column_name in df.columns:
                df[column_name] = pd.to_datetime(df[column_name])

                if column.formatType == FieldType.year:
                    df[column_name] = df[column_name].dt.strftime('%Y')
                elif column.formatType == FieldType.month:
                    df[column_name] = df[column_name].dt.strftime('%Y-%m')
                elif column.formatType == FieldType.day:
                    df[column_name] = df[column_name].dt.strftime('%Y-%m-%d')
                elif column.formatType == FieldType.quarter:
                    year_col = df[column_name].dt.strftime('%Y-')
                    quarter_col = df[column_name].dt.quarter.astype('str')
                    df[column_name] = year_col + 'Q' + quarter_col

                df[column_name] = df[column_name].fillna('')
        return df

    def _main(self, df: DataFrame):
        """入口函数"""
        after_where_df = self.apply_filter(df, exclude_dim_expr=False)
        df = self.apply_agg(after_where_df, True)
        if self.before_return:
            df = self.before_return(df, self.raw_params)
        return df


# -----------------------------------------------------------------------------
# main decorator
def _resolve_param(args: tuple):
    if len(args) == 2:
        return args[1]
    if len(args) == 1:
        return args[0]
    raise ValueError("Bad signature for main function.")


def as_datasource(
    func=None,
    struct: Type[Struct] = None,
    engine: Optional[Type[ChartEngine]] = ChartEngine,
    before_return: Optional[Callable[[pd.DataFrame, Dict], pd.DataFrame]] = None,
    date_round: bool = False
):
    """用作图表数据源的main函数装饰器

    Args:
        func: main方法
        struct: 定义字段及其字段类型的类名称，必填
        engine: 用于处理结果DataFrame的engine, 默认为ChartEngine;
                如需自定义, 需继承ChartEngine;
                为None时, 不对结果DataFrame作处理
        before_return: 自定义同步function，作为ChartEngine处理的后置逻辑
                        接受处理后的DataFrame和来自图表原始参数为入参
        date_round: 是否允许低精度日期值与筛选条件内高精度日期值进行比较，默认不允许；
                    允许后则精度缺失（例如2012与2012-10，缺失了月份部分，而2011与2012-10本身在年份可比，不属于精度缺失）时，
                    除了相等以外，统一判定为不符合条件

    """
    if func is None:
        return functools.partial(as_datasource,
                                 before_return=before_return,
                                 engine=engine,
                                 struct=struct)

    if struct is None:
        raise ValueError("需定义图表数据源的字段信息")

    if engine and not issubclass(engine, ChartEngine):
        raise TypeError(f"engine参数应为ChartEngine子类")

    if before_return is not None and not isfunction(before_return):
        raise TypeError(f"before_return参数应为函数")

    if asyncio.iscoroutinefunction(func):
        async def wrapper(*args):
            param = _resolve_param(args)
            if param == FLAG_FOR_META:
                return struct.to_dict()

            df = await func(*args)
            if engine is not None:
                handler = engine(param, struct=struct, before_return=before_return, date_round=date_round)
                df = handler._main(df)  # noqa

            return df.to_dict('records')
    else:
        def wrapper(*args):
            param = _resolve_param(args)
            if param == FLAG_FOR_META:
                return struct.to_dict()

            df = func(*args)
            if engine is not None:
                handler = engine(param, struct=struct, before_return=before_return, date_round=date_round)
                df = handler._main(df)  # noqa

            return df.to_dict('records')

    return functools.wraps(func)(wrapper)
