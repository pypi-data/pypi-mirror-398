import re
import textwrap
import threading

import numpy as np
from asyncpg.connection import connect as pg_conn
import json
import uuid
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from itertools import count, chain
from typing import (
    List, TYPE_CHECKING, Any, Dict, Union, NamedTuple,
    Iterable, Optional, Literal
)

import edgedb
import pandas as pd
from loguru import logger
from pydantic import BaseModel, ValidationError, Field

from deepfos import OPTION
from deepfos.api.models import compat_parse_obj_as as parse_obj_as
from deepfos.api.deepmodel import DeepModelAPI
from deepfos.api.models.deepmodel import (
    ObjectBasicDTO, ObjectParam,
    QueryResultObjectInfo, QueryResult
)
from deepfos.cache import SpaceSeperatedLRUCache
from deepfos.db.edb import create_async_client
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.exceptions import (
    RequiredFieldUnfilled, ObjectNotExist,
    ExternalObjectReadOnly, MultiLinkTargetNotUnique,
    SingleLinkInRelation
)
from deepfos.lib import serutils
from deepfos.lib.asynchronous import future_property, evloop
from deepfos.lib.decorator import flagmethod, cached_property, lru_cache
from deepfos.lib.utils import (
    AliasGenerator, to_version_tuple,
)

__all__ = ['AsyncDeepModel', 'DeepModel', 'to_fields', 'QueryWithArgs']

OBJECT_QUERY = \
    """
with module schema
select ObjectType {
    id,
    name,
    links: {
        id,
        name,
        cardinality,
        required,
        properties: { id, name, target: {name} } filter .name not in {'source', 'target'},
        target: { id, name, external, annotations: {name, value := @value}, 
                    properties: { id, name } filter .name != 'id' },
        expr,
        constraints: { name, expr, finalexpr, subjectexpr },
        source_property: {name}, 
        target_property: {name},
        annotations: {name, value := @value},
    } filter .name != '__type__',
    properties: {
        id, 
        name,
        cardinality,
        required,
        target: { name },
        expr,
        constraints: { name, expr, finalexpr, subjectexpr },
        annotations: {name, value := @value},
    } filter .name != 'id',
    annotations: {name, value := @value},
    constraints: { name, expr, finalexpr, subjectexpr },
    external
}
    """
BUSINESS_KEY = 'business_key'
BATCH_INSERT_KW = 'data'

# pandas to_json精度最大为15
# 为避免精度缺失，如下类型需转换为string
NEED_CAST_STR = ['std::decimal']

DOC_ARGS_KWARGS = """
        Hint:
        
            kwargs语法:
            
                select User{name, is_active} 
                filter .name=<std::str>$name and is_active=<std::bool>$active
            
            .. admonition:: 使用示例
            
                .. code-block:: python
                
                    dm = DeepModel()
                    
                    dm.execute(
                        '''delete User filter .name=<std::str>$name 
                        and is_active=<std::bool>$active''', 
                        name='Alice', active='True'
                    )
            
            此处 `$` 为以kwargs的方式指定参数的特殊符号，
            且需在参数前增加相应类型提示，参数值只支持str和int类型
"""

NOT_SCALAR = "default::object"

dm_type_to_edb_scalar = {
    'str': 'std::str',
    'int': 'std::int64',
    'bool': 'std::bool',
    'multilingual': 'std::str',
    'float': 'std::decimal',
    'datetime': 'cal::local_datetime',
    'file': 'std::str',
    'uuid': 'std::str',
    'json': 'std::json',
}
TAB = ' ' * 4


class ObjectElement(ObjectParam):
    @property
    def links(self):
        return {link.code: link for link in self.linkParamList}


class QueryWithArgs(BaseModel):
    commands: str
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    globals: Dict[str, Any] = Field(default_factory=dict)


class MainField(NamedTuple):
    business_key: str
    is_multi: bool
    props: Iterable[Optional[str]]
    # 目前业务主键创建的类型只会为std::str
    type: str = 'std::str'


class MainPgCol(NamedTuple):
    target_bkey_col: str
    target_col: str


class ConstraintField(BaseModel):
    name: str
    expr: str
    finalexpr: Optional[str] = None
    subjectexpr: Optional[str] = None


class NamedField(BaseModel):
    name: Optional[str] = None


class NameIdField(BaseModel):
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None


class TargetField(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    external: bool = False
    annotations: List[Dict[str, str]] = Field(default_factory=list)
    properties: Optional[List[NameIdField]] = None

    @property
    def is_scalar(self) -> bool:
        return self.name.startswith('std::') or self.name == 'cal::local_datetime'

    @property
    def info(self):
        return {e['name'].rpartition('::')[-1]: e['value'] for e in self.annotations}

    @property
    def normalized_name(self):
        return self.name.rpartition('::')[-1]

    @property
    def props(self):
        return {p.name: p for p in self.properties}


class LinkPropField(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    target: NamedField

    @property
    def type(self) -> str:
        return self.target.name


class PtrInfo(BaseModel):
    id: Optional[Union[uuid.UUID, Literal['id']]] = None
    name: str
    target: TargetField
    properties: List[LinkPropField] = Field(default_factory=list)
    expr: Optional[str] = None
    source_property: Optional[NamedField] = None
    target_property: Optional[NamedField] = None
    required: Optional[bool] = False
    cardinality: Optional[str] = None
    constraints: List[ConstraintField] = Field(default_factory=list)
    annotations: List[Dict[str, str]] = Field(default_factory=list)

    @property
    def type(self) -> str:
        return self.target.name

    @property
    def is_link(self):
        return not self.target.is_scalar

    @property
    def is_multi_link(self):
        return self.is_link and self.cardinality == 'Many'

    @property
    def is_multi(self):
        return self.cardinality == 'Many'

    @property
    def computable(self):
        return self.expr is not None

    @property
    def external(self):
        return self.target.external

    @property
    def props(self):
        return [p.name for p in self.properties]

    @property
    def prop_type(self):
        return {p.name: p.type for p in self.properties}

    @property
    def target_col(self):
        if self.target_property:
            return self.target_property.name

    @property
    def info(self):
        return {e['name'].rpartition('::')[-1]: e['value'] for e in self.annotations}


_RE_CONSTRAINT_FIELDS = re.compile(r'\((((\.\w+)(,\s+)?)+)\)')


class ObjectTypeFrame(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    links: List[PtrInfo] = Field(default_factory=list)
    properties: List[PtrInfo] = Field(default_factory=list)
    external: bool
    annotations: List[Dict[str, str]] = Field(default_factory=list)
    constraints: List[ConstraintField] = Field(default_factory=list)

    @property
    def fields(self):
        return {ptr.name: ptr for ptr in [*self.links, *self.properties]}

    @property
    def info(self):
        return {e['name'].rpartition('::')[-1]: e['value'] for e in self.annotations}
    
    @property
    def normalized_name(self):
        return self.name.rpartition('::')[-1]

    @property
    def exclusive_fields(self):
        exclusive = [
            field.name
            for field in self.fields.values()
            if field.name != 'id' and any([
                const.expr and (
                    const.name == 'std::exclusive'
                    and const.subjectexpr is None
                )
                for const in field.constraints
            ])
        ]
        for const in self.constraints:
            if (
                const.name == 'std::exclusive'
                and const.subjectexpr and (
                    m := _RE_CONSTRAINT_FIELDS.match(const.subjectexpr)
                )
            ):
                found = m.group(1)
                exclusive.append({f.strip()[1:] for f in found.split(',')})
        return exclusive


def _format_link(link_df_fit: pd.DataFrame, link_name: str):
    if link_df_fit.empty:
        return pd.Series(dtype=object), False

    if link_df_fit.duplicated(subset=['source', 'target']).any():
        raise MultiLinkTargetNotUnique(
            f'Multi Link: [{link_name}] relation dataframe中'
            f'source与target对应存在不唯一性'
        )

    prop_cols = [col for col in link_df_fit.columns if col not in ['source', 'target']]
    has_props = bool(prop_cols)

    if has_props:
        sources = link_df_fit['source'].values
        targets = link_df_fit['target'].values
        unique_sources, source_indices = np.unique(sources, return_inverse=True)
        
        prop_arrays = {col: link_df_fit[col].values for col in prop_cols}
        result = {}

        for i in range(len(unique_sources)):
            idx = source_indices == i
            source = unique_sources[i]
            source_targets = targets[idx]

            indices = np.where(idx)[0]
            prop_dict = {
                source_targets[j]: {col: prop_arrays[col][indices[j]] for col in prop_cols}
                for j in range(len(source_targets))
            }
            result[source] = {'target': source_targets.tolist(), 'prop': prop_dict}
        link = pd.Series(result, dtype=object)
    else:
        link = link_df_fit.groupby('source')['target'].agg(list)

    return link, has_props


class BaseField(PtrInfo):
    def fit(self, df: pd.DataFrame, field_name: str, raw_pg: bool = False):
        """使 :class:`Dataframe` 对应的列符合字段的限制条件

        Args:
            df: 待转换的 :class:`Dataframe`
            field_name: 需要转化的列名
            raw_pg: 是否在为pg插入做fit
        """
        pass

    def cast(self, df: pd.DataFrame, field_name: str, direct_access: bool = True):
        """
        对 :class:`Dataframe` 对应的列作类型转换。
        一般在获取 :class:`Dataframe` 时使用。
        """
        pass


class FieldDateTime(BaseField):
    @staticmethod
    def format_datetime(dt):
        if pd.isna(dt):
            return pd.NA
        return pd.to_datetime(dt).strftime("%Y-%m-%dT%H:%M:%S")

    def fit(self, df: pd.DataFrame, field_name: str, raw_pg: bool = False):
        df[field_name] = df[field_name].apply(self.format_datetime)

    def cast(self, df: pd.DataFrame, field_name: str, direct_access: bool = True):
        df[field_name] = pd.to_datetime(df[field_name], errors='ignore')


class FieldString(BaseField):
    def format_string(self, data):
        if pd.isna(data):
            return pd.NA
        return str(data)

    def fit(self, df: pd.DataFrame, field_name: str, raw_pg: bool = False):
        df[field_name] = df[field_name].apply(self.format_string)


class FieldJson(BaseField):
    def format_json(self, data):
        if pd.isna(data):
            return data
        return json.dumps(data)

    def fit(self, df: pd.DataFrame, field_name: str, raw_pg: bool = False):
        # std::json needed to be fit only when data is for pg batch insert
        # because json-object (dict in pd series) will be encoded correctly
        # by pandas to_json
        if raw_pg:
            df[field_name] = df[field_name].apply(self.format_json)

    def cast(self, df: pd.DataFrame, field_name: str, direct_access: bool = True):
        pass


class FieldInt(BaseField):
    def fit(self, df: pd.DataFrame, field_name: str, raw_pg: bool = False):
        df[field_name] = df[field_name].astype(pd.Int64Dtype(), errors='ignore')

    def cast(self, df: pd.DataFrame, field_name: str, direct_access: bool = True):
        df[field_name] = df[field_name].astype(pd.Int64Dtype(), errors='ignore')


class FieldDecimal(FieldString):
    def cast(self, df: pd.DataFrame, field_name: str, direct_access: bool = True):
        df[field_name] = df[field_name].astype(float, errors='ignore')


class FieldBool(BaseField):
    def format_bool(self, data):
        if isinstance(data, bool) or pd.isna(data):
            return data
        return str(data).lower() == 'true'

    def fit(self, df: pd.DataFrame, field_name: str, raw_pg: bool = False):
        df[field_name] = df[field_name].apply(self.format_bool)

    def cast(self, df: pd.DataFrame, field_name: str, direct_access: bool = True):
        pass


class FieldFactory:
    field_map = {
        'std::bool': FieldBool,
        'std::int64': FieldInt,
        'std::bigint': FieldInt,
        'std::decimal': FieldDecimal,
        'std::json': FieldJson,
        'std::str': FieldString,
        'cal::local_datetime': FieldDateTime,
    }

    def __new__(cls, field: Union[PtrInfo, LinkPropField]) -> BaseField:
        field_class = cls.field_map.get(field.type, BaseField)
        return field_class(**field.dict())


class ObjectStructure:
    fields: Dict[str, BaseField]

    def __init__(self, name, structure: Iterable[PtrInfo], include_id=False):
        self.name = name
        self.fields = {
            field.name: FieldFactory(field)
            for field in structure
            if not field.computable and field.name != 'id'
        }
        # Make one for batch insert pg
        if include_id:
            self.fields['id'] = BaseField(
                name='id', id='id', cardinality='One',
                target=TargetField(name='std::uuid')
            )
        self.self_link_fields = []
        for name, field in list(self.fields.items()):
            if field.type == self.name:
                self.self_link_fields.append(name)
            if field.is_multi_link:
                continue
            if not field.is_link:
                continue
            for prop in field.properties:
                self.fields[f'{name}@{prop.name}'] = FieldFactory(prop)

    def fit(self, df: pd.DataFrame, raw_pg=False) -> pd.DataFrame:
        """
        对传入的DataFrame的指定数据列执行fit操作。
        直接影响DataFrame数据。

        Args:
            df: 数据源
            raw_pg: 是否在为pg插入做fit

        """
        valid_fields = []
        for field in df.columns:
            if field in self.fields:
                valid_fields.append(field)
                self.fields[field].fit(df, field, raw_pg)

        return df[valid_fields]

    def cast(self, df: pd.DataFrame, direct_access: bool = True):
        for field in df.columns:
            if field in self.fields:
                self.fields[field].cast(df, field, direct_access)


def _iter_link_prop_assign(link, business_key, prop_name, prop_type, is_multi):
    assign_string = f"@{prop_name} := <{prop_type}>"
    if prop_type in NEED_CAST_STR:
        assign_string += '<std::str>'
    if is_multi:
        return f"{assign_string}(json_get(item, '{link}', 'prop', .{business_key}, '{prop_name}'))"

    return f"{assign_string}(json_get(item, '{link}@{prop_name}'))"


def _iter_single_assign(
    field: PtrInfo,
    cast_type: str,
    target_main_field: Dict[str, MainField],
    error_on_empty_link: bool = False
) -> str:
    """
    生成单字段赋值语句

    Args:
        field: 字段信息
        cast_type: 字段类型
        target_main_field: 目标字段信息
        error_on_empty_link: 链接字段值不存在时是否抛出异常

    Returns:
        赋值语句
    """
    assign = f"\n{field.name} := "
    # 设置标量值
    if field.name not in target_main_field:
        if field.is_multi:
            return assign + f"json_array_unpack(item['{field.name}'])"

        assign += f"<{cast_type}>"

        if cast_type in NEED_CAST_STR:
            assign += '<std::str>'

        return assign + f"item['{field.name}']"

    # 设置link target值
    link = field.name
    main_field = target_main_field[link]

    if main_field.props:
        prop_assigns = ','.join(
            _iter_link_prop_assign(link, main_field.business_key, name,
                                   field.prop_type[name], main_field.is_multi)
            for name in main_field.props
        )
        prop_block = f" {{{prop_assigns}}}"
    else:
        prop_block = ""

    if main_field.is_multi:
        link_value = f"each_{link}"
    else:
        link_value = f"(json_get(item, '{link}'))"

    if error_on_empty_link:
        link_expr = f"(<{cast_type}><std::str>{link_value}){prop_block}"
    else:
        link_expr = f"(select detached {cast_type}{prop_block}\nfilter .{main_field.business_key} = <std::str>{link_value})"

    if main_field.is_multi:
        if main_field.props:
            target_source = f"json_get(item, '{link}', 'target')"
        else:
            target_source = f"item['{link}']"
        
        assign += 'distinct (\n' + textwrap.indent(textwrap.dedent(f"""\
        for each_{link} in json_array_unpack({target_source})
        union (
            {link_expr}
        )"""), TAB) + '\n)'
    else:
        assign += link_expr

    return assign


def bulk_insert_by_fields(
    object_name: str,
    field_type: List[PtrInfo],
    target_main_field: Dict[str, MainField],
    error_on_empty_link: bool = False,
):
    insert_assign_body = ','.join([
        _iter_single_assign(field, field.type, target_main_field, error_on_empty_link)
        for field in field_type
    ])
    return textwrap.dedent(f"""
        with raw_data := <json>to_json(<std::str>${BATCH_INSERT_KW}),
        for item in json_array_unpack(raw_data) union (
            insert {object_name} {{{textwrap.indent(insert_assign_body, TAB * 4)}
            }}
        )""")


def bulk_upsert_by_fields(
    object_name: str,
    field_type: List[PtrInfo],
    target_main_field: Dict[str, MainField],
    exclusive_fields: Iterable[str],
    update_fields: Iterable[str],
    error_on_empty_link: bool = False,
):
    conflict_on_fields = map(lambda n: f'.{n}', exclusive_fields)
    insert_assign_body = ','.join([
        _iter_single_assign(field, field.type, target_main_field, error_on_empty_link)
        for field in field_type
    ])
    update_assign_body = ','.join(
        [
            _iter_single_assign(field, field.type, target_main_field, error_on_empty_link)
            for field in field_type if field.name in update_fields
        ]
    )
    return textwrap.dedent(f"""
        with raw_data := <json>to_json(<std::str>${BATCH_INSERT_KW}),
        for item in json_array_unpack(raw_data) union (
            insert {object_name} {{{textwrap.indent(insert_assign_body, TAB * 4)}
            }}
            unless conflict on ({','.join(conflict_on_fields)})
            else (
                update {object_name} set {{{textwrap.indent(update_assign_body, TAB * 5)}
                }}
            )
        )""")


def bulk_update_by_fields(
    object_name: str,
    field_type: List[PtrInfo],
    target_main_field: Dict[str, MainField],
    match_fields: Iterable[str],
    update_fields: Iterable[str],
    error_on_empty_link: bool = False,
):
    update_assign_body = ','.join([
        _iter_single_assign(field, field.type, target_main_field, error_on_empty_link)
        for field in field_type if field.name in update_fields
    ])

    field_type_map = {field.name: field.type for field in field_type}
    match_str = " and ".join(
        [
            f".{name} = <{field_type_map.get(name, 'std::str')}>item['{name}']"
            for name in match_fields
        ]
    )
    return textwrap.dedent(f"""
    with raw_data := <json>to_json(<std::str>${BATCH_INSERT_KW}),
    for item in json_array_unpack(raw_data) union (
        update {object_name} 
        filter {match_str}
        set {{{textwrap.indent(update_assign_body, TAB * 3)}
        }}
    )
    """)


def format_obj(obj: edgedb.Object) -> ObjectTypeFrame:
    if not isinstance(obj, edgedb.Object):
        raise TypeError("预期obj为edgedb.Object")

    serialized = serutils.serialize(obj)

    try:
        return parse_obj_as(ObjectTypeFrame, serialized)
    except ValidationError:
        raise TypeError("预期obj为ObjectType查询得到的结构信息")


def to_fields(obj: edgedb.Object) -> Dict[str, PtrInfo]:
    return format_obj(obj).fields


def collect_query_result_structure(
    object_info: QueryResultObjectInfo
):
    fields = [
        PtrInfo(
            name=f.name,
            target=TargetField(name=dm_type_to_edb_scalar.get(f.type, NOT_SCALAR))
        )
        for f in object_info.fields
    ]
    include_id = len(fields) == 1 and fields[0].name == 'id'
    return ObjectStructure(name='', structure=fields, include_id=include_id)


def collect_frame_desc_structure(desc: Dict[str, str]):
    fields = [
        PtrInfo(
            name=name if isinstance(name, str) else name[0],
            target=TargetField(
                name=tname
                if isinstance(tname, str) else NOT_SCALAR
            )
        )
        for name, tname in desc.items()
    ]
    include_id = len(fields) == 1 and fields[0].name == 'id'
    return ObjectStructure(name='', structure=fields, include_id=include_id)


# Copied from edb/pgsql/types.py base_type_name_map
base_type_name_map = {
    'std::str': ('text',),
    'std::int64': ('int8',),
    'std::decimal': ('numeric',),
    'std::bool': ('bool',),
    # for id col only
    'std::uuid': ('uuid',),
    'std::json': ('jsonb',),
    'cal::local_datetime': ('edgedb', 'timestamp_t')
}


def quote_ident(string: Union[str, uuid.UUID]) -> str:
    return '"' + str(string).replace('"', '""') + '"'


def pg_type_cast(edb_type: str):
    if edb_type in base_type_name_map:
        return '::' + '.'.join(base_type_name_map[edb_type])
    return ''


def _iter_value(
    field: PtrInfo,
    idx: int,
    target_info: Dict[str, MainPgCol],
    alias: AliasGenerator
):
    if field.name not in target_info:
        if field.type == 'std::decimal':
            return f'/*{field.name}*/"edgedb"."str_to_decimal"(${idx})'
        if field.type == 'cal::local_datetime':
            return f'/*{field.name}*/"edgedb"."local_datetime_in"(${idx})'
        return f'/*{field.name}*/${idx}{pg_type_cast(field.type)}'

    main_col = target_info[field.name]
    tmp_table = quote_ident(alias.get('t'))
    bkey = quote_ident(main_col.target_bkey_col)
    # bkey is std::str
    return (f"/*{field.name}*/\n"
            f"(select {tmp_table}.{quote_ident(main_col.target_col)} "
            f"from edgedbpub.{quote_ident(field.target.id)} as {tmp_table} "
            f"where {tmp_table}.{bkey} = ${idx}{pg_type_cast('std::str')})")


def batch_insert_pg(
    object_id: str,
    fields: List[PtrInfo],
    target_info: Dict[str, MainPgCol],
    exclusive_fields: List[PtrInfo] = None,
    update_fields: List[PtrInfo] = None
):
    upd_fields = list(map(lambda f: quote_ident(f.id), update_fields or []))

    alias = AliasGenerator()
    idx = count(1).__next__
    col_assign = {}
    for field in fields:
        col = quote_ident(field.id)
        col_assign[col] = _iter_value(field, idx(), target_info, alias)

    insert_main_tbl = (
        f'INSERT INTO edgedbpub.{quote_ident(object_id)}'
        f'({", ".join(col_assign.keys())})'
        f' VALUES ({", ".join(col_assign.values())})'
    )
    if exclusive_fields and upd_fields:
        conflicts = ','.join(quote_ident(ef.id) for ef in exclusive_fields)
        insert_main_tbl += (
            f' ON CONFLICT ({conflicts}) DO UPDATE SET ' +
            ','.join([f'{col} = EXCLUDED.{col}' for col in upd_fields])
        )
    return insert_main_tbl


txn_support = flagmethod('_txn_support_')


class _TxnConfig:
    __slots__ = ('qls', 'in_txn', 'txn_support', 'flatten')

    def __init__(self):
        self.qls = [[]]
        self.in_txn = [False]
        self.txn_support = False
        self.flatten = False


@lru_cache(maxsize=128, cache_factory=SpaceSeperatedLRUCache)
async def get_element_info():
    from deepfos.api.space import SpaceAPI
    from deepfos.api.models.app import ElementRelationInfo
    from deepfos.exceptions import ElementTypeMissingError
    modules = await SpaceAPI(sync=False).module.get_usable_module()
    target_module = ['MAINVIEW', 'DM']
    for mdl in modules:
        if mdl.moduleType in target_module and mdl.status == 1:
            return ElementRelationInfo.construct_from(mdl)
    raise ElementTypeMissingError('DeepModel组件在空间内不可用')


# -----------------------------------------------------------------------------
# core
class AsyncDeepModel(ElementBase[DeepModelAPI]):
    """DeepModel元素

    Args:
        direct_access: 是否使用直连模式，默认为True
            会结合OPTION.edgedb.dsn是否有值决定是否使用直连模式，如无值，则仍为非直连模式
            直连模式下，会使用edgedb-python库直连edgedb server，
            否则会使用DeepModel组件API进行操作
        pg_dsn: PG连接信息

    """
    __mangle_docs__ = False

    def __init__(
        self,
        direct_access: bool = True,
        pg_dsn: str = None,
        **kwargs
    ):
        self._txn_ = ContextVar('QLTXN')
        self.appmodule = f"app{OPTION.api.header['app']}"
        self.spacemodule = f"space{OPTION.api.header['space']}"
        self.direct_access = direct_access and bool(OPTION.edgedb.dsn)
        if not self.direct_access:
            logger.debug('当前DeepModel为非直连模式')
        self.alias = AliasGenerator()
        self.pg_dsn = pg_dsn
        self._globals = None
        self._clients = threading.local()

    @future_property
    async def _internal_dbname(self):
        if not self.direct_access:
            # N.B: only retrieved when direct access is enabled
            return
        api = await self.wait_for('async_api')
        ver = await api.extra.version()
        if to_version_tuple(ver, 4) < (3, 0, 18, 8, 0):
            return
        db_info = await api.sharding.database()
        space = OPTION.api.header['space']
        if db_info.space != space:
            raise ValueError(
                f'Space id in sharding database info invalid. '
                f'Expected space id: {space}, actual: {db_info.space}'
            )
        return db_info.edgedbName

    @property
    def client(self):
        if not self.direct_access:
            self._globals = {}
            return

        if (client := getattr(self._clients, 'value', None)) is not None:
            return client

        client = create_async_client(
            default_module=self.appmodule,
            dbname=self._internal_dbname
        )
        if user_id := OPTION.api.header.get('user'):
            default_globals = {
                f'{self.spacemodule}::current_user_id':
                user_id
            }
            client = client.with_globals(**default_globals)
        if self._globals is None:
            self._globals = client._options.state._globals
        self._clients.value = client
        return client

    @future_property
    async def element_info(self):
        """元素信息"""
        return await get_element_info()

    @future_property
    async def async_api(self):
        """异步API对象"""
        return await self._init_api()

    def _safe_get_txn_conf(self) -> _TxnConfig:
        try:
            config = self._txn_.get()
        except LookupError:
            config = _TxnConfig()
            self._txn_.set(config)
        return config

    @property
    def _txn_support_(self):
        return self._safe_get_txn_conf().txn_support

    @_txn_support_.setter
    def _txn_support_(self, val):
        self._safe_get_txn_conf().txn_support = val

    @future_property(on_demand=True)
    async def model_objects(self) -> Dict[str, ObjectParam]:
        """MainView中的所有对象详情"""
        api = await self.wait_for('async_api')
        res = await api.object.get_all()
        return {obj.code: obj for obj in res.objectList}

    @future_property(on_demand=True)
    async def model_object_list(self) -> List[ObjectBasicDTO]:
        """MainView中的所有对象列表"""
        api = await self.wait_for('async_api')
        return await api.object.list()

    @future_property(on_demand=True)
    async def user_objects(self) -> Dict[str, edgedb.Object]:
        """当前app下所有的用户对象"""
        objects = await AsyncDeepModel.query_object(
            self,
            f"{OBJECT_QUERY} filter .name like '{self.appmodule}::%'",
        )
        return {obj.name.rpartition('::')[-1]: obj for obj in objects}

    @future_property(on_demand=True)
    async def system_objects(self) -> Dict[str, edgedb.Object]:
        """当前space下所有的系统对象"""
        objects = await AsyncDeepModel.query_object(
            self,
            f"{OBJECT_QUERY} filter .name like '{self.spacemodule}::%'",
        )
        return {obj.name.rpartition('::')[-1]: obj for obj in objects}

    @cached_property
    def objects(self) -> Dict[str, ObjectTypeFrame]:
        result = {name: format_obj(obj) for name, obj in self.user_objects.items()}
        for name, obj in self.system_objects.items():
            # In case of duplicate name both in app obj& space obj
            if name in result:
                result[f'{self.spacemodule}::{name}'] = format_obj(obj)
            else:
                result[name] = format_obj(obj)

        return result

    @staticmethod
    def _prepare_variables(kwargs):
        variables = {}
        for k, v in kwargs.items():
            variables[str(k)] = v
        return variables

    async def query_object(self, ql: str, **kwargs) -> List[Any]:
        """执行ql查询语句，得到原始结果返回

        如有变量，以kwargs的方式提供

        Args:
            ql: 执行的ql
        
        See Also:
        
            :func:`query`, 执行ql查询语句，得到序列化后的结果
            :func:`query_df`, 执行ql查询语句，获取DataFrame格式的二维表
            
        """

        if self.direct_access:
            logger.opt(lazy=True).debug(f"Query: [{ql}],\n"
                                        f"kwargs: [{kwargs}],\n"
                                        f"globals: [{self._globals}].")
            client = self.client
            client._options.state._globals = self._globals
            _, result = await client.query(ql, **kwargs)
            return result

        result = await self._http_query(ql, **kwargs)
        field_info = {
            fi.name: fi.type if fi.fields is None else fi.fields
            for fi in result.objectInfos[0].fields
        } if result.objectInfos else {}
        return serutils.deserialize(result.json_, field_info)

    async def query(self, ql: str, **kwargs) -> List[Any]:
        """执行ql查询语句，得到序列化后的结果

        如有变量，以args, kwargs的方式提供

        Args:
            ql: 执行的ql


        .. admonition:: 示例

            .. code-block:: python

                dm = DeepModel()

                # 以变量name 查询User对象
                dm.query(
                    'select User{name, is_active} filter .name=<std::str>$name',
                    name='Alice'
                )

        See Also:
        
            :func:`query_df`, 执行ql查询语句，获取DataFrame格式的二维表
            :func:`query_object`, 执行ql查询语句，得到原始结果返回

        """
        if self.direct_access:
            logger.opt(lazy=True).debug(f"Query: [{ql}],\n"
                                        f"kwargs: [{kwargs}],\n"
                                        f"globals: [{self._globals}].")
            client = self.client
            client._options.state._globals = self._globals
            frame_desc, result = await client.query(ql, **kwargs)
            return serutils.serialize(
                result, ctx=serutils.Context(frame_desc=frame_desc)
            )

        result = await self._http_query(ql, **kwargs)
        return result.json_

    async def _http_query(self, ql: str, **kwargs) -> QueryResult:
        logger.opt(lazy=True).debug(f"Query: [{ql}], \nkwargs: [{kwargs}].")
        result = await self.async_api.deepql.query(
            module=self.appmodule,
            query=ql,
            variables=self._prepare_variables(kwargs)
        )
        self._maybe_handle_error(result.json_)
        return result

    async def query_df(self, ql: str, **kwargs) -> pd.DataFrame:
        """执行ql查询语句

        获取DataFrame格式的二维表
        如有变量，以kwargs的方式提供

        Args:
            ql: 执行的ql


        .. admonition:: 示例

            .. code-block:: python

                dm = DeepModel()

                # 以变量name 查询User对象，得到DataFrame
                dm.query_df(
                    'select User{name, is_active} filter .name=<std::str>$name',
                    name='Alice'
                )
        
        See Also:
        
            :func:`query`, 执行ql查询语句，得到序列化后的结果
            :func:`query_object`, 执行ql查询语句，得到原始结果返回
        
        """
        if self.direct_access:
            client = self.client
            client._options.state._globals = self._globals
            frame_desc, data = await client.query(ql, **kwargs)
            # set of unnamed tuple
            if isinstance(frame_desc, list):
                return pd.DataFrame(
                    data=serutils.serialize(
                        data, ctx=serutils.Context(frame_desc=frame_desc, query_df=True)
                    ),
                    columns=[str(i) for i in range(len(frame_desc))]
                )

            data = pd.DataFrame(data=serutils.serialize(
                data, ctx=serutils.Context(frame_desc=frame_desc, query_df=True)
            ))
            # Not records for dict-like
            if not isinstance(frame_desc, dict):
                return data

            structure = collect_frame_desc_structure(frame_desc)
        else:
            result = await self._http_query(ql, **kwargs)
            # No object structure info
            if not result.objectInfos:
                return pd.DataFrame(data=result.json_)

            data = pd.DataFrame(
                data=result.json_,
                columns=[f.name for f in result.objectInfos[0].fields]
            )

            structure = collect_query_result_structure(result.objectInfos[0])

        if data.empty:
            return pd.DataFrame(columns=structure.fields.keys())

        structure.cast(data, self.direct_access)
        return data

    query.__doc__ = query.__doc__ + DOC_ARGS_KWARGS
    query_object.__doc__ = query_object.__doc__ + DOC_ARGS_KWARGS
    query_df.__doc__ = query_df.__doc__ + DOC_ARGS_KWARGS

    def _ensure_client(self):
        self.client # noqa

    @txn_support
    async def execute(
        self,
        qls: Union[str, List[str], List[QueryWithArgs]],
        **kwargs
    ) -> Optional[List]:
        """以事务执行多句ql

        Args:
            qls: 要执行的若干ql语句
                 可通过提供QueryWithArgs对象ql的方式定制每句ql的参数信息
                 亦可直接以kwargs的形式提供参数信息
                 会自动用作所有string形式ql的参数

        """
        qls_with_args = self._collect_execute_qls(qls, kwargs)
        return await self._maybe_exec_qls(qls_with_args)

    def _collect_execute_qls(self, qls, kwargs):
        self._ensure_client()
        if isinstance(qls, str):
            qls_with_args = [QueryWithArgs(
                commands=qls, kwargs=kwargs, globals=self._globals
            )]
        else:
            qls_with_args = []
            seen_kwargs_key = set()
            for ql in qls:
                if isinstance(ql, QueryWithArgs):
                    if (
                        not self.direct_access
                        and ql.kwargs
                        and seen_kwargs_key.intersection(ql.kwargs.keys())
                    ):
                        raise NotImplementedError('非直连模式不支持重名variables')

                    qls_with_args.append(ql)
                    if ql.kwargs:
                        seen_kwargs_key = seen_kwargs_key.union(ql.kwargs.keys())

                elif isinstance(ql, str):
                    qls_with_args.append(QueryWithArgs(
                        commands=ql, kwargs=kwargs, globals=self._globals
                    ))
                else:
                    raise TypeError(f'qls参数中出现类型非法成员：{type(ql)}')
        return qls_with_args

    execute.__doc__ = execute.__doc__ + DOC_ARGS_KWARGS

    async def _execute(self, qls_with_args: List[QueryWithArgs]) -> List:
        self.alias.reset(BATCH_INSERT_KW)
        if not self.direct_access:
            kwargs = {}
            seen_kwargs_key = set()

            for ql in qls_with_args:
                if ql.kwargs and seen_kwargs_key.intersection(ql.kwargs.keys()):
                    raise NotImplementedError('非直连模式不支持重名variables')
                if ql.kwargs:
                    kwargs.update(ql.kwargs)
                    seen_kwargs_key = seen_kwargs_key.union(ql.kwargs.keys())

            commands = ';'.join([ql.commands for ql in qls_with_args])

            logger.opt(lazy=True).debug(
                f"Execute QL: [{commands}], \nkwargs: [{kwargs}]."
            )
            res = await self.async_api.deepql.execute(
                module=self.appmodule,
                query=commands,
                variables=self._prepare_variables(kwargs)
            )
            affected = res.get('json')
            self._maybe_handle_error(affected)
            return affected

        result = []
        client = self.client
        client._options.state._globals = self._globals
        async for tx in client.transaction():
            async with tx:
                for ql in qls_with_args:
                    logger.opt(lazy=True).debug(
                        f"Execute QL: [{ql.commands}],"
                        f"\nkwargs: [{ql.kwargs}],"
                        f"\nglobals: [{ql.globals}]."
                    )
                    if ql.globals:
                        bak_cli = tx._client
                        tx._client = tx._client.with_globals(**ql.globals)
                        try:
                            desc, affected = await tx.execute(ql.commands, **ql.kwargs)
                            result.append(serutils.serialize(
                                affected, ctx=serutils.Context(frame_desc=desc)
                            ))
                        finally:
                            tx._client = bak_cli
                    else:
                        desc, affected = await tx.execute(ql.commands, **ql.kwargs)
                        result.append(serutils.serialize(
                            affected, ctx=serutils.Context(frame_desc=desc)
                        ))
        if len(result) == 1:
            return result[0]
        return result

    @staticmethod
    def _maybe_handle_error(res):
        if not isinstance(res, dict):
            return

        if error := res.get('errors'):  # pragma: no cover
            ex_msg = error['message'].strip()
            ex_code = int(error['code'])
            raise edgedb.EdgeDBError._from_code(ex_code, ex_msg)  # noqa

    async def _maybe_exec_qls(
        self,
        qls_with_args: List[QueryWithArgs]
    ) -> Optional[List]:
        txn_conf = self._safe_get_txn_conf()

        if txn_conf.in_txn[-1] and self._txn_support_:
            txn_conf.qls[-1].extend(qls_with_args)
            return

        return await self._execute(qls_with_args)

    @staticmethod
    def _valid_data(data, object_name, relation, structure, check_required=True):
        if check_required:
            required_fields = set(map(
                lambda f: f.name,
                filter(lambda f: f.required, structure.fields.values())
            ))
            if missing_fields := (required_fields - set(data.columns).union(relation)):
                raise RequiredFieldUnfilled(f'缺少必填字段: {missing_fields}')

        if not relation:
            return

        for name, link_df in relation.items():
            if name not in structure.fields:
                continue
            field = structure.fields[name]
            if not field.is_multi_link:
                if name in data.columns:
                    continue

                raise SingleLinkInRelation(
                    f'对象[{object_name}]的Link:[{name}]非multi link, '
                    f'请直接作为入参data的{name}列提供, '
                    f'值为对象{structure.fields[name].type}的业务主键'
                )

            if not {'source', 'target'}.issubset(link_df.columns):
                raise ValueError("关联表必须包含source和target列")

    @staticmethod
    def _valid_upsert(
        obj: ObjectTypeFrame,
        field_names: Iterable[str],
        bkey: str,
        exclusive_fields: List[str] = None,
        update_fields: List[str] = None
    ):
        if (
            update_fields
            and (missing := (set(update_fields) - set(field_names)))
        ):
            raise ValueError(f"update fields: {missing} 不在提供的数据中")

        if exclusive_fields:
            if missing := (set(exclusive_fields) - set(field_names)):
                raise ValueError(f"exclusive fields: {missing} 不在提供的数据中")

            valid_exclusive = [*obj.exclusive_fields, bkey]
            exclusive = (
                exclusive_fields[0]
                if len(exclusive_fields) == 1 else set(exclusive_fields)
            )
            if exclusive not in valid_exclusive:
                raise ValueError(f"exclusive fields: {exclusive_fields} 没有相应唯一约束")

    async def _get_bkey(
        self,
        obj: Union[ObjectTypeFrame, TargetField],
        source: str = None,
        name: str = None
    ) -> str:
        # 如可在object结构的annotations中取业务主键，则优先取，否则走接口
        if obj.info and BUSINESS_KEY in obj.info:
            return obj.info[BUSINESS_KEY]
        elif (code := obj.normalized_name) in self.model_objects:
            return self.model_objects[code].businessKey

        assert isinstance(obj, TargetField)
        # Link 至非本应用对象，需单独查询
        tgt = ObjectElement.construct_from(self.model_objects[source]).links[name]
        tgt_model_info = await self.async_api.object.info(
            app=tgt.targetApp, object_code=tgt.targetObjectCode
        )
        return tgt_model_info.businessKey

    async def _collect_bulk_field_info(self, object_name, structure, data, relation):
        field_info = []
        tgt_main_field = {}
        for field in structure.fields.values():
            if field.name not in data.columns:
                continue

            field_info.append(field)

            if not field.is_link:
                continue

            is_multi = field.is_multi_link
            name = field.name
            # 链接至其他对象，记录目标对象信息
            if is_multi:
                if name not in relation:
                    raise ValueError(
                        f'对象[{object_name}]的多选链接:[{name}]未定义在relation中'
                    )
                link_props = set(relation[name].columns).intersection(field.props)
            else:
                link_props = set(
                    c[len(f'{name}@')::]
                    for c in data.columns if c.startswith(f'{name}@')
                ).intersection(field.props)
            tgt_bkey = await self._get_bkey(field.target, object_name, name)
            tgt_main_field[name] = MainField(tgt_bkey, is_multi, link_props)
        return field_info, tgt_main_field

    def _ql_payload(self, data: pd.DataFrame, ql: str,):
        self._ensure_client()
        kw_name = self.alias.get(BATCH_INSERT_KW)
        return QueryWithArgs(
            commands=ql.replace(f'${BATCH_INSERT_KW}', f'${kw_name}'),
            kwargs={kw_name: data.to_json(
                orient='records', double_precision=15,
                force_ascii=False, default_handler=str
            )},
            globals=self._globals,
        )

    @staticmethod
    def _split_self_link(data, relation, structure, bkey):
        self_link_dfs = {}
        for name in structure.self_link_fields:
            field = structure.fields[name]
            if (link_df := relation.get(name)) is not None:
                link_props = set(link_df.columns).intersection(field.props)
                self_link_dfs[name] = (
                    structure.fit(data[[bkey, name]]),
                    MainField(bkey, field.is_multi_link, link_props)
                )
                data = data.drop(columns=[name])
            elif name in data.columns:
                link_prop_cols = []
                link_props = []

                for col in data.columns:
                    if (
                        col.startswith(f'{name}@')
                        and ((prop_name := col[len(f'{name}@')::]) in field.props)
                    ):
                        link_prop_cols.append(col)
                        link_props.append(prop_name)

                self_link_dfs[name] = (
                    structure.fit(data[[bkey, name, *link_prop_cols]]),
                    MainField(bkey, field.is_multi_link, link_props)
                )
                data = data.drop(columns=[name, *link_prop_cols])
        return data, self_link_dfs

    @staticmethod
    def _merge_relation(data, relation, structure, bkey):
        for name, link_df in relation.items():
            link_df = link_df.dropna(how='any', subset=['target', 'source'])
            if name not in structure.fields:
                continue
            field = structure.fields[name]
            valid_cols = list({'source', 'target', *field.props} & set(link_df.columns))
            link_df = link_df[valid_cols]
            # for fit only
            temp_structure = ObjectStructure(
                field.type,
                [
                    PtrInfo(name='source', target=TargetField(name='std::str')),
                    PtrInfo(name='target', target=TargetField(name='std::str')),
                    *[PtrInfo(**prop.dict()) for prop in field.properties]
                ]
            )
            link_df = temp_structure.fit(link_df)
            link, has_props = _format_link(link_df, name)

            if not has_props:
                data = data.drop(columns=[name], errors='ignore')
                data = data.join(link.to_frame(name), on=bkey, how='left')
                mask = data[name].isna()
                if mask.any():
                    empty_series = pd.Series([[]] * mask.sum(), index=data[mask].index, dtype=object)
                    data.loc[mask, name] = empty_series
            else:
                bkey_values = data[bkey].values
                mapped_values = np.array([link.get(key, []) for key in bkey_values], dtype=object)
                data[name] = mapped_values
            
        return data

    async def _collect_bulk_qls(
        self,
        object_name: str,
        data: pd.DataFrame,
        relation: Dict[str, pd.DataFrame] = None,
        chunk_size: int = 500,
        enable_upsert: bool = False,
        update_fields: Iterable[str] = None,
        exclusive_fields: Iterable[str] = None,
        match_fields: Iterable[str] = None,
        insert: bool = True,
        error_on_empty_link: bool = False
    ) -> List[List[QueryWithArgs]]:
        if object_name in self.objects:
            obj = self.objects[object_name]
        else:
            raise ObjectNotExist(
                f'DeepModel对象[{object_name}]在当前应用不存在，无法插入数据'
            )
        if obj.external:
            raise ExternalObjectReadOnly('外部对象只可读')

        structure = ObjectStructure(name=obj.name, structure=obj.fields.values())
        relation = relation or {}
        self._valid_data(data, object_name, relation, structure, check_required=insert)

        bkey = await self._get_bkey(obj)
        if bkey not in data.columns:
            raise RequiredFieldUnfilled(f'缺少业务主键[{bkey}]')

        # data拼接relation df
        data = self._merge_relation(data, relation, structure, bkey)
        # 从data中分离出self-link更新信息
        data, self_link_dfs = self._split_self_link(data, relation, structure, bkey)
        field_info, tgt_main_field = await self._collect_bulk_field_info(
            object_name, structure, data, relation
        )
        field_names = set(map(lambda f: f.name, field_info))
        if insert:
            if enable_upsert:
                self._valid_upsert(obj, field_names, bkey, exclusive_fields, update_fields)

            exclusive_fields = set(exclusive_fields or {bkey}) & set(field_names)
            update_fields = set(update_fields or (field_names - {bkey})) & set(field_names)
            if enable_upsert and update_fields:
                bulk_ql = bulk_upsert_by_fields(
                    object_name, field_info, tgt_main_field,
                    exclusive_fields, update_fields, error_on_empty_link
                )
            else:
                bulk_ql = bulk_insert_by_fields(object_name, field_info, tgt_main_field, error_on_empty_link)
        else:
            if missing := (set(match_fields or [bkey]) - set(field_names)):
                raise ValueError(f"match fields: {missing} 不在提供的数据中")

            match_fields = set(match_fields or [bkey]) & set(field_names)
            if to_upd := (field_names - match_fields):
                bulk_ql = bulk_update_by_fields(
                    object_name, field_info, tgt_main_field,
                    match_fields, to_upd, error_on_empty_link
                )
            else:
                bulk_ql = None
        qls = []
        self._ensure_client()
        if chunk_size is None:
            chunk_size = len(data)
        for i in range(0, len(data), chunk_size):
            part = structure.fit(data.iloc[i: i + chunk_size])
            ql_chunk = []
            # Ignore bulk_ql when only update multi links
            if bulk_ql is not None:
                ql_chunk = [self._ql_payload(part, bulk_ql)]
            for update_field, (update_df, main_field) in self_link_dfs.items():
                field = structure.fields[update_field]
                update_ql = bulk_update_by_fields(
                    object_name, [field], {update_field: main_field},
                    [bkey], [update_field]
                )
                update_part = update_df.iloc[i: i + chunk_size]
                ql_chunk.append(self._ql_payload(update_part, update_ql))
            qls.append(ql_chunk)
        return qls

    @txn_support
    async def insert_df(
        self,
        object_name: str,
        data: pd.DataFrame,
        relation: Dict[str, pd.DataFrame] = None,
        chunksize: int = 500,
        enable_upsert: bool = False,
        update_fields: Iterable[str] = None,
        exclusive_fields: Iterable[str] = None,
        commit_per_chunk: bool = False,
        error_on_empty_link: bool = False,
    ) -> None:
        """以事务执行基于DataFrame字段信息的批量插入数据

        Args:
            object_name: 被插入数据的对象名，需属于当前应用
            data: 要插入的数据，若有single link property，
                  则以列名为link_name@link_property_name的形式提供
            relation: 如有multi link，提供该字典用于补充link target信息，
                    键为link字段名，值为映射关系的DataFrame
                    DataFrame中的source列需为插入对象的业务主键，
                    target列需为link target的业务主键，
                    若有link property，则以property名为列名，提供在除source和target的列中
            chunksize: 单次最大行数
            enable_upsert: 是否组织成upsert句式
            update_fields: upsert句式下update的update fields列表，
                            涉及的fields需出现在data或relation中，
                            默认为提供的data列中除业务主键以外的fields
            exclusive_fields: upsert句式下update的exclusive fields列表，
                            涉及的fields需出现在data或relation中，
                            默认为业务主键
            commit_per_chunk: 每次插入后是否提交事务，
                            默认为False，即所有数据插入后再提交事务
                            该参数仅在非start transaction上下文中生效
            error_on_empty_link: 链接字段值不存在时是否抛出异常，
                            默认为False，即不检查链接目标是否存在
                            当设置为True时，会检查链接目标是否存在，不存在则抛出异常

        Notes:

            由于批量insert实现方式为组织 for-union clause 的 insert 语句，
            而在其中查询self link只能查到已有数据，
            无法查到 for-union clause 之前循环插入的结果，self link字段的数据将被单独抽出，
            在 insert 后再用 for-union clause 的 update 语句更新


        .. admonition:: 示例(不涉及multi link)

            .. code-block:: python

                import pandas as pd
                from datetime import datetime

                dm = DeepModel()

                data = pd.DataFrame(
                    {
                        'p_bool': [True, False],
                        'p_str': ['Hello', 'World'],
                        'p_local_datetime': [
                            datetime(2021, 1, 1, 0, 0, 0),
                            datetime(2021, 2, 1, 0, 0, 0),
                        ],
                    }
                )
                # 将data插入Demo对象
                dm.insert_df('Demo', data)

        .. admonition:: 示例(涉及multi link)

            .. code-block:: python

                import pandas as pd

                dm = DeepModel()
                # 对象主数据
                data = pd.DataFrame(
                    {
                        'name': ['Alice', 'Bob', 'Carol']
                    }
                )
                # 主数据的multi link字段target信息
                relation = {
                    'deck': pd.DataFrame(
                        {
                            # 一对多可用多行source与target的关联表示
                            'source': ['Alice', 'Alice', 'Bob', 'Carol'],
                            'target': [
                                'Dragon',
                                'Golem',
                                'Golem',
                                'Imp'
                            ]
                        }
                    ),
                    'awards': pd.DataFrame(
                        {
                            'source': ['Alice', 'Bob', 'Carol'],
                            'target': ['1st', '2nd', '3rd'],
                        }
                    )
                }
                dm.insert_df('User', data, relation=relation)

        """
        if data.empty:
            logger.info("data为空，无DML执行")
            return

        qls = await self._collect_bulk_qls(
            object_name, data, relation, chunksize,
            enable_upsert, update_fields, exclusive_fields,
            insert=True, error_on_empty_link=error_on_empty_link
        )
        if commit_per_chunk:
            for ql_chunk in qls:
                await self.execute(ql_chunk)
        else:
            await self.execute(list(chain(*qls)))

    async def get_object(
        self,
        object_name: str,
        raw: bool = True
    ) -> Optional[Union[ObjectTypeFrame, edgedb.Object]]:
        """获取指定对象名的对象

        Args:
            object_name: 对象名，如对象名未提供module name部分，则默认module name为当前app module
                        如需查询其他module的对象，应以 module_name::object_name 的形式提供
            raw: 是否获取edgedb.Object数据，为False时将转换为ObjectTypeFrame数据
                默认为True

        """
        if '::' not in object_name:
            object_name = f'{self.appmodule}::{object_name}'
        objs = await AsyncDeepModel.query_object(
            self,
            f"{OBJECT_QUERY} filter .name = '{object_name}'",
        )
        if len(objs) == 0:
            return

        if raw:
            return objs[0]

        return format_obj(objs[0])

    async def insert_df_pg(
        self,
        object_name: str,
        data: pd.DataFrame,
        chunk_size: int = 500,
        enable_upsert: bool = False,
        exclusive_fields: Iterable[str] = None,
        update_fields: Iterable[str] = None,
    ) -> None:
        """以事务直连pg执行基于DataFrame字段信息的批量插入数据

        Args:
            object_name: 被插入数据的对象名，需属于当前应用
            data: 要插入的数据，只支持single property/link，且single link不可包含link property
            chunk_size: 单次最大行数
            enable_upsert: 是否组织成insert-on conflict do update 句式
            exclusive_fields: enable_upsert为True时的conflict字段，默认为business key
            update_fields: enable_upsert为True时的update字段，默认为除business key外所有已提供的字段

        """
        if self.pg_dsn is None:
            raise ValueError('pg_dsn未提供')

        if data.empty:
            return

        if object_name in self.objects:
            obj = self.objects[object_name]
        else:
            raise ObjectNotExist(
                f'DeepModel对象[{object_name}]在当前应用不存在，无法插入数据'
            )
        if obj.external:
            raise ExternalObjectReadOnly('外部对象只可读')

        structure = ObjectStructure(
            name=obj.name,
            structure=obj.fields.values(),
            include_id=True
        )
        self._valid_data(data, object_name, {}, structure)

        field_info = []
        tgt_info = {}
        field_map = structure.fields
        bkey = await self._get_bkey(obj)

        data = data.drop(columns=['id'], errors='ignore')
        data = data.assign(id=[uuid.uuid4() for _ in data.index], index=data.index)

        for name, field in field_map.items():
            if name not in data.columns:
                continue
            if '@' in name:
                raise NotImplementedError('不支持插入包含link property的数据')
            if field.props:
                raise NotImplementedError('不支持插入有link property的link数据')

            field_info.append(field)
            if not field.is_link:
                continue

            if field.is_multi:
                raise NotImplementedError('不支持插入包含multi link/property的数据')

            tgt = field.target
            tgt_bkey = await self._get_bkey(field.target, object_name, name)
            tgt_bkey_col = str(tgt.props[tgt_bkey].id)
            if tgt_col := tgt.props.get(field.target_col):
                tgt_info[name] = MainPgCol(
                    target_bkey_col=tgt_bkey_col,
                    target_col=str(tgt_col.id),
                )
            else:
                tgt_info[name] = MainPgCol(target_bkey_col=tgt_bkey_col, target_col='id')

        # field_names will be used for data col order
        # so here use field_set as the set for field_names
        field_names = list(map(lambda f: f.name, field_info))
        field_set = set(field_names)

        if enable_upsert:
            self._valid_upsert(obj, field_set, bkey, exclusive_fields, update_fields)

        exclusive_fields = set(exclusive_fields or {bkey}) & field_set
        update_fields = (
            set(update_fields or (field_set - {bkey})) & field_set
        ) - {'id'}

        update_fields = list(map(lambda uf: field_map[uf], update_fields))
        exclusive_fields = list(map(lambda ex: field_map[ex], exclusive_fields))

        if enable_upsert:
            main_sql = batch_insert_pg(
                str(obj.id), field_info, tgt_info,
                exclusive_fields, update_fields
            )
        else:
            main_sql = batch_insert_pg(str(obj.id), field_info, tgt_info)

        data = structure.fit(data, raw_pg=True)
        data = data.fillna(np.nan)
        data = data.replace([np.nan], [None])
        conn = await pg_conn(dsn=self.pg_dsn)
        try:
            async with conn.transaction():
                logger.debug(f"Prepare SQL: [{main_sql}]")
                main_sql_st = await conn.prepare(main_sql)
                data = data[field_names]
                for i in range(0, len(data), chunk_size):
                    part = data.iloc[i: i + chunk_size]
                    await main_sql_st.executemany(part.itertuples(index=False, name=None))
        finally:
            await conn.close()

    @txn_support
    async def update_df(
        self,
        object_name: str,
        data: pd.DataFrame,
        relation: Dict[str, pd.DataFrame] = None,
        chunksize: int = 500,
        match_fields: Iterable[str] = None,
        commit_per_chunk: bool = False,
    ) -> None:
        """以事务执行基于DataFrame字段信息的批量更新数据

        将以业务主键作为匹配条件，除业务主键以外的字段将为update fields

        Args:
            object_name: 被更新数据的对象名，需属于当前应用
            data: 要更新的数据，若有single link property，
                  则以列名为link_name@link_property_name的形式提供
            relation: 如有multi link，提供该字典用于补充link target信息，
                    键为link字段名，值为映射关系的DataFrame
                    DataFrame中的source列需为插入对象的业务主键，
                    target列需为link target的业务主键，
                    若有link property，则以property名为列名，提供在除source和target的列中
            chunksize: 单次最大行数
            match_fields: update的匹配列表，涉及的fields需出现在data或relation中，默认为业务主键
            commit_per_chunk: 每次插入后是否提交事务，
                            默认为False，即所有数据插入后再提交事务
                            该参数仅在非start transaction上下文中生效
        """
        if data.empty:
            logger.info("data为空，无DML执行")
            return

        qls = await self._collect_bulk_qls(
            object_name, data, relation, chunksize,
            match_fields=match_fields, insert=False
        )
        if commit_per_chunk:
            for ql_chunk in qls:
                await self.execute(ql_chunk)
        else:
            await self.execute(list(chain(*qls)))

    @asynccontextmanager
    async def start_transaction(self, flatten: bool = False):
        """开启事务

        上下文管理器，使用with语法开启上下文，上下文中的ql将作为事务执行
        退出with语句块后，事务将立即执行，执行过程中如果报错会直接抛出

        .. admonition:: 示例

            .. code-block:: python

                import pandas as pd

                dm = DeepModel()

                data = pd.DataFrame(
                    {
                        'name': ['Alice', 'Bob', 'Carol'],
                        'deck': [
                            "Dragon",
                            "Golem",
                            "Imp"
                        ],
                        'awards': [
                            "1st",
                            "2nd",
                            "3rd"
                        ],
                    }
                )

                async with dm.start_transaction():
                    await dm.execute("delete User")
                    await dm.insert_df("User", data)


        Important:

            仅 :func:`insert_df` :func:`update_df` :func:`execute` 方法支持在事务中执行

        """
        try:
            self._txn_.get()
        except LookupError:
            self._txn_.set(_TxnConfig())

        bak_flatten = self._txn_.get().flatten
        self._txn_.get().in_txn.append(True)

        if flatten and not self._txn_.get().flatten:
            force_submit = True
        else:
            force_submit = False

        self._txn_.get().flatten = bak_flatten or flatten

        if not self._txn_.get().flatten:
            self._txn_.get().qls.append([])

        try:
            yield
            if force_submit or not self._txn_.get().flatten:
                if qls := self._txn_.get().qls.pop():
                    await self._execute(qls)
        finally:
            self._txn_.get().in_txn.pop()
            self._txn_.get().flatten = bak_flatten

    @contextmanager
    def with_globals(self, globals_):
        if not self.direct_access:
            try:
                yield
            finally:
                raise NotImplemented('非直连模式不支持设置state信息')
        else:
            if self._globals is None:
                bak_globals = self.client._options.state._globals
            else:
                bak_globals = self._globals
            try:
                client = self.client
                client._options.state._globals = bak_globals
                client = client.with_globals(**globals_)
                self._globals = client._options.state._globals
                yield
            finally:
                self._globals = bak_globals

    @contextmanager
    def without_globals(self, *global_names):
        if not self.direct_access:
            try:
                yield
            finally:
                raise NotImplemented('非直连模式不支持设置state信息')
        else:
            if self._globals is None:
                bak_globals = self.client._options.state._globals
            else:
                bak_globals = self._globals
            try:
                client = self.client
                client._options.state._globals = bak_globals
                client = client.without_globals(*global_names)
                self._globals = client._options.state._globals
                yield
            finally:
                self._globals = bak_globals


class DeepModel(AsyncDeepModel, metaclass=SyncMeta):
    synchronize = (
        'query_object', 'query', 'query_df',
        'execute', 'get_object',
        'insert_df', 'insert_df_pg',
        'update_df',
    )

    if TYPE_CHECKING:  # pragma: no cover
        def query_object(self, ql: str, **kwargs) -> List[Any]:
            ...

        def query(self, ql: str, **kwargs) -> List[Any]:
            ...

        def query_df(self, ql: str, **kwargs) -> pd.DataFrame:
            ...

        def execute(
            self,
            qls: Union[str, List[str], List[QueryWithArgs]],
            **kwargs
        ) -> Optional[List]:
            ...

        def get_object(
            self,
            object_name: str,
            raw: bool = True
        ) -> Optional[Union[ObjectTypeFrame, edgedb.Object]]:
            ...

        def insert_df(
            self,
            object_name: str,
            data: pd.DataFrame,
            relation: Dict[str, pd.DataFrame] = None,
            chunksize: int = 500,
            enable_upsert: bool = False,
            update_fields: Iterable[str] = None,
            exclusive_fields: Iterable[str] = None,
            commit_per_chunk: bool = False,
            error_on_empty_link: bool = False,
        ) -> None:
            ...

        def insert_df_pg(
            self,
            object_name: str,
            data: pd.DataFrame,
            chunk_size: int = 500,
            enable_upsert: bool = False,
            exclusive_fields: List[str] = None,
            update_fields: List[str] = None,
        ) -> None:
            ...

        def update_df(
            self,
            object_name: str,
            data: pd.DataFrame,
            relation: Dict[str, pd.DataFrame] = None,
            chunksize: int = 500,
            match_fields: Iterable[str] = None,
            commit_per_chunk: bool = False,
        ) -> None:
            ...

    @contextmanager
    def start_transaction(self, flatten: bool = False):
        """开启事务

        上下文管理器，使用with语法开启上下文，上下文中的ql将作为事务执行
        退出with语句块后，事务将立即执行，执行过程中如果报错会直接抛出

        .. admonition:: 示例

            .. code-block:: python

                import pandas as pd

                dm = DeepModel()

                data = pd.DataFrame(
                    {
                        'name': ['Alice', 'Bob', 'Carol'],
                        'deck': [
                            "Dragon",
                            "Golem",
                            "Imp"
                        ],
                        'awards': [
                            "1st",
                            "2nd",
                            "3rd"
                        ],
                    }
                )

                with dm.start_transaction():
                    dm.execute("delete User")
                    dm.insert_df("User", data)


        Important:

            仅 :func:`insert_df` :func:`execute` 方法支持在事务中执行

        """
        try:
            self._txn_.get()
        except LookupError:
            self._txn_.set(_TxnConfig())

        bak_flatten = self._txn_.get().flatten
        self._txn_.get().in_txn.append(True)

        if flatten and not self._txn_.get().flatten:
            force_submit = True
        else:
            force_submit = False

        self._txn_.get().flatten = bak_flatten or flatten

        if not self._txn_.get().flatten:
            self._txn_.get().qls.append([])

        try:
            yield
            if force_submit or not self._txn_.get().flatten:
                if qls := self._txn_.get().qls.pop():
                    evloop.run(self._execute(qls))
        finally:
            self._txn_.get().in_txn.pop()
            self._txn_.get().flatten = bak_flatten
