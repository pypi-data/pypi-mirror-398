"""DeepUX组件数据源"""
import asyncio
import functools
from typing import Dict, Type, List, Union, Tuple, Optional

import numpy as np
import pandas as pd
from pydantic import Field

from deepfos import OPTION
from deepfos.api.models import BaseModel
from deepfos.api.models.dimension import DimensionMemberBean

__all__ = [
    'BaseField',
    'String',
    'Integer',
    'Boolean',
    'Json',
    'Float',
    'DateTime',
    'UUID',
    'as_datasource',
    'Struct',
    'NodeStruct',
    'EdgeStruct',
    'to_desc'
]

FLAG_FOR_META = "describe"
FIELDS = "fields"
STRUCT_FIELD = "objectInfos"
ELE_INFO_FIELD = "elementInfo"
DATA_FIELD = "json"
DESC_FIELD = "description"

NODES = "nodes"
EDGES = "edges"
OBJECT_TYPE = "object[]"


class BaseField(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None

    def __init__(self, name: str = None, **data):
        super().__init__(name=name, **data)

    def to_dict(self) -> Dict:
        return self.dict()


class ScalarField(BaseField):
    def fit(self, df: pd.DataFrame, field_name: str):
        pass


class String(ScalarField):
    """文本"""
    type: str = 'str'

    def fit(self, df: pd.DataFrame, field_name: str):
        df[field_name] = np.where(
            df[field_name].isna(),
            df[field_name],
            df[field_name].astype(str, errors='ignore')
        )


class Integer(ScalarField):
    """整数"""
    type: str = 'int'

    def fit(self, df: pd.DataFrame, field_name: str):
        df[field_name] = np.where(
            df[field_name].isna(),
            df[field_name],
            pd.to_numeric(df[field_name], errors='ignore', downcast='signed')
        )


class Boolean(ScalarField):
    """布尔"""
    type: str = 'bool'

    def fit(self, df: pd.DataFrame, field_name: str):
        df[field_name] = np.where(
            df[field_name].isna(),
            df[field_name],
            df[field_name].astype(bool, errors='ignore')
        )


class Json(ScalarField):
    """多语言文本（json）"""
    type: str = 'json'


class Float(ScalarField):
    """小数"""
    type: str = 'float'

    def fit(self, df: pd.DataFrame, field_name: str):
        df[field_name] = np.where(
            df[field_name].isna(),
            df[field_name],
            pd.to_numeric(df[field_name], errors='ignore')
        )


class DateTime(ScalarField):
    """日期时间"""
    type: str = 'datetime'


class UUID(ScalarField):
    """uuid"""
    type: str = 'uuid'


class ObjectField(BaseField):
    """表示对象类型的结构信息, 图格式数据源专用"""
    type: str = OBJECT_TYPE
    fields: List[ScalarField] = Field(default_factory=list)


class StructMeta(type):
    def __new__(mcs, cls_name, bases, namespace: dict):
        namespace['fields'] = mcs.collect_fields(bases, namespace)
        return type.__new__(mcs, cls_name, bases, namespace)

    @staticmethod
    def collect_fields(bases, ns):
        fields = {}
        if len(bases) > 0:
            for parent in bases:
                if (
                    issubclass(parent, Struct)
                    and hasattr(parent, 'fields')
                ):
                    fields.update(parent.fields)

        for field_name, anno in ns.get('__annotations__', {}).items():
            if (
                isinstance(anno, type)
                and issubclass(anno, ScalarField)
                and field_name not in ns
            ):
                fields.update({field_name: anno(name=field_name)})

        for k, v in dict(ns).items():
            if isinstance(v, ScalarField):
                ns.pop(k)
                if v.name is None:
                    v.name = k
                fields.update({v.name: v})

        return fields


class Struct(metaclass=StructMeta):
    """数据源字段信息结构

    .. admonition:: 示例

        .. code-block:: python

            from deepfos.lib.deepux import Struct

            class Data(Struct):
                # 声明字段 text 为str类型
                text = String()
                # 声明字段 int1 为int类型
                integer = Integer('int1')
                # 声明字段 float_ 为float类型
                float_: Float
                # 声明字段 dt 为datetime类型
                datetime = DateTime(name='dt')

    See Also:
        :meth:`as_datasource`
        :class:`NodeStruct`
        :class:`EdgeStruct`

    """
    @classmethod
    def structure(cls):
        return [field.to_dict() for field in cls.fields.values()] # noqa

    @classmethod
    def to_dict(cls):
        return {
            ELE_INFO_FIELD: {
                DESC_FIELD: OPTION.general.task_info.get('element_desc', {})
            },
            STRUCT_FIELD: [
                {FIELDS: cls.structure()}
            ]
        }


class NodeStruct(Struct):
    """图格式的数据源Node字段信息结构

    默认的_id(节点主键)和label(节点描述)字段已设置，
    继承后即可声明其他节点键信息

    .. admonition:: 示例

        .. code-block:: python

            from deepfos.lib.deepux import NodeStruct

            class NodeData(NodeStruct):
                # 声明节点键 text 为str类型
                text = String()
                # 声明节点键 int1 为int类型
                integer = Integer('int1')
                # 声明节点键 float_ 为float类型
                float_: Float
                # 声明节点键 dt 为datetime类型
                datetime = DateTime(name='dt')

    See Also:
        :meth:`as_datasource`
        :class:`Struct`
        :class:`EdgeStruct`

    """
    _id: String
    label: String


class EdgeStruct(Struct):
    """图格式的数据源Edge字段信息结构

    默认的source(关系的来源)和target(关系的目标)字段已设置，
    继承后即可声明其他节点关系信息

    .. admonition:: 示例

        .. code-block:: python

            from deepfos.lib.deepux import EdgeStruct

            class EdgeData(EdgeStruct):
                # 声明节点关系 color 字段为str类型
                color = String()
                # 声明节点关系 size 字段为int类型
                size = Integer('size')

    See Also:
        :meth:`as_datasource`
        :class:`Struct`
        :class:`NodeStruct`

    """
    source: String
    target: String


class GraphStruct(Struct):
    node: NodeStruct
    edge: EdgeStruct

    @classmethod
    def structure(cls):
        return [
            ObjectField(
                name=NODES,
                fields=list(cls.node.fields.values())  # noqa
            ).to_dict(),
            ObjectField(
                name=EDGES,
                fields=list(cls.edge.fields.values())  # noqa
            ).to_dict(),
        ]


def to_desc(data: List[DimensionMemberBean]):
    desc = {}
    for dim in data:
        desc[dim.name] = dim.multilingual.get(
            OPTION.api.header.get('language', 'en'),
            dim.name
        )
    return desc


def _resolve_param(args: tuple):
    if len(args) == 2:
        return args[1]
    if len(args) == 1:
        return args[0]
    raise ValueError("main函数入参数非法")


def _check_str_dict(data: Dict[str, Union[Dict, str]], value_type):
    if any(not isinstance(k, str) for k in data):
        raise ValueError("字段描述格式非法")

    if any(not isinstance(v, value_type) for v in data.values()):
        raise ValueError("字段描述格式非法")

    if value_type == str:
        return

    for v in data.values():
        _check_str_dict(v, str)


def valid_df(df, struct: Dict[str, ScalarField]):
    if lacked := (set(struct).difference(df.columns)):
        raise ValueError(f'字段: {lacked} 缺失')

    df = df[list(struct.keys())]
    df = df.replace({None: np.nan})
    df = df.replace({np.nan: None})
    for field_name, field_type in struct.items():
        field_type.fit(df, field_name)
    return df


def _resolve_return_value(
    return_value,
    struct: Union[Type[Struct], Tuple[Type[Struct], Type[Struct]]],
    graph_struct: bool,
    node_edge: bool
) -> Tuple[Dict, Dict]:
    is_two_tuples = isinstance(return_value, tuple) and len(return_value) == 2
    desc = {}
    if graph_struct:
        if (
            not is_two_tuples
            and any([not isinstance(each, pd.DataFrame) for each in return_value])
        ):
            raise ValueError(
                "图结构的数据源预期main函数返回值为"
                "nodes和edges内容组成的pandas DataFrame"
            )
        node_struct, edge_struct = struct
        if node_edge:
            nodes, edges = return_value
        else:
            edges, nodes = return_value
        nodes = valid_df(nodes, node_struct.fields)
        edges = valid_df(edges, edge_struct.fields)
        data = [{NODES: nodes.to_dict('records'), EDGES: edges.to_dict('records')}]
    elif is_two_tuples:
        df, desc = return_value
        if not isinstance(df, pd.DataFrame):
            raise TypeError('通用结构的数据源预期main函数返回的第一个值为pandas DataFrame')

        if not isinstance(desc, dict):
            raise TypeError("通用结构的数据源预期main函数返回的第二个值为字段描述，类型为字典")

        _check_str_dict(desc, dict)
        df = valid_df(df, struct.fields) # noqa
        data = df.to_dict('records')
    elif isinstance(return_value, pd.DataFrame):
        df = valid_df(return_value, struct.fields) # noqa
        data = df.to_dict('records')
    else:
        raise ValueError(
            "通用结构的数据源预期main函数返回值为pandas DataFrame"
            "或pandas DataFrame与字段描述字典组成的元组"
        )

    return data, desc


def _resolve_struct_desc(
    struct: Union[Type[Struct], Tuple[Type[Struct], Type[Struct]]],
    graph_struct: bool
) -> Dict:
    if graph_struct:
        # order preprared outside
        node_struct, edge_struct = struct
        helper_struct = GraphStruct
        helper_struct.node, helper_struct.edge = node_struct, edge_struct
        return helper_struct.to_dict()
    else:
        return struct.to_dict()


def as_datasource(
    func=None,
    struct: Union[Type[Struct], Tuple[Type[Struct], Type[Struct]]] = None,
):
    """用作DeepUX数据源的main函数装饰器

    Args:
        func: 返回pandas DataFrame和字段描述（可选）的main方法
        struct: 定义字段及其字段类型的类名称，必填

    .. admonition:: 用法示例

        .. code-block:: python

            from deepfos.lib.deepux import as_datasource, Struct

            # 声明结构信息
            class Data(Struct):
                ...

            @as_datasource(struct=Data)
            def main(p2):
                ...

    See Also:
        :class:`Struct`
        :class:`NodeStruct`
        :class:`EdgeStruct`

    """
    if func is None:
        return functools.partial(as_datasource, struct=struct)

    if struct is None:
        raise ValueError("需定义DeepUX数据源的字段信息")

    struct_is_tuple = isinstance(struct, tuple)
    graph_struct = (
        struct_is_tuple and len(struct) == 2
        and (
            (issubclass(struct[0], NodeStruct) and issubclass(struct[1], EdgeStruct))
            or
            (issubclass(struct[0], EdgeStruct) and issubclass(struct[1], NodeStruct))
        )
    )

    if not struct_is_tuple and not issubclass(struct, Struct):
        raise ValueError(
            "DeepUX数据源的字段信息需为Struct的子类"
            "或EdgeStruct和NodeStruct的子类组成的元组"
        )

    if struct_is_tuple and not graph_struct:
        raise ValueError(
            "DeepUX图结构数据源的字段信息需为EdgeStruct和NodeStruct的子类组成的元组"
        )

    node_edge = True
    if graph_struct and issubclass(struct[1], NodeStruct): # noqa
        node_edge = False
        struct = struct[1], struct[0] # noqa

    if asyncio.iscoroutinefunction(func):
        async def wrapper(*args):
            param = _resolve_param(args)

            if param == FLAG_FOR_META:
                return _resolve_struct_desc(struct, graph_struct)

            maybe_df_desc = await func(*args)

            data, desc = _resolve_return_value(
                maybe_df_desc, struct, graph_struct, node_edge
            )

            return {DATA_FIELD: data, DESC_FIELD: desc}
    else:
        def wrapper(*args):
            param = _resolve_param(args)

            if param == FLAG_FOR_META:
                return _resolve_struct_desc(struct, graph_struct)

            maybe_df_desc = func(*args)

            data, desc = _resolve_return_value(
                maybe_df_desc, struct, graph_struct, node_edge
            )

            return {DATA_FIELD: data, DESC_FIELD: desc}

    return functools.wraps(func)(wrapper)
