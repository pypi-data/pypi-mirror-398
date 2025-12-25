from typing import Union, Tuple, Iterable, Dict, Optional, List

from .nodemixin import MetaNodeMixin
from .sqlcondition import SQLCondition, SqlCondError, ConditionManager
from ._cache import DataProxy
from ._operator import OpCombineError
from loguru import logger
from deepfos.lib.decorator import cached_property
from deepfos.element.datatable import (
    get_table_class, T_DatatableInstance, T_AsyncDatatableInstance
)
from deepfos.api.models.app import ConfirmElementInfoDto
import pandas as pd

from weakref import WeakKeyDictionary
import weakref
from contextlib import contextmanager
from collections import defaultdict
import copy


# -----------------------------------------------------------------------------
# utils
class TableInfo(ConfirmElementInfoDto):
    tableName: Optional[str]
    serverName: Optional[str]


def get_datatable(
    table_info: Union[TableInfo, dict],
    sync=True
) -> Union[T_DatatableInstance, T_AsyncDatatableInstance]:
    if isinstance(table_info, TableInfo):
        init_args = {
            'element_name': table_info.elementName,
            'folder_id': table_info.folderId,
            'path': table_info.path,
            'table_name': table_info.tableName,
            'server_name': table_info.serverName,
        }
        element_type = table_info.elementType
    else:
        init_args = {**table_info}
        element_type = init_args.pop('element_type', None)
        if element_type is None:
            raise ValueError("element_type is needed in table_info")

    return get_table_class(element_type, sync)(**init_args)


class ConditionPassError(Exception):
    pass


class RelationInfo(object):
    """记录table间关联关系"""
    def __init__(self, cls: 'MetaTable'):
        self._rel_info = WeakKeyDictionary()
        self._tbl = weakref.ref(cls)

    def _add_relation(self, tbl: 'MetaTable', on: Tuple[str]):
        if on is not None:
            self._rel_info[tbl] = on
            return self

    add_parent_relation = _add_relation

    def add_child_relation(
        self,
        tbl: 'MetaTable',
        on: Tuple[str],
        alias: Optional[Tuple[str]]
    ):
        if alias is not None:
            on = tuple(
                ko if ka == '=' else ka
                for ko, ka in zip(on, alias)
            )
        return self._add_relation(tbl, on)

    def is_rel_field(self, tbl: 'MetaTable', field: str) -> bool:
        """字段是否为关联字段"""
        return field in self[tbl]

    def has_alias_with(self, other) -> bool:
        """
        与其他表是否存在不同名的关联字段

        Args:
            other: 表，必须为当前表的子节点或父节点

        Returns:
            bool: 存在不同名：True；否则：False
        """
        return any(
            k1 != k2 for k1, k2 in
            zip(self[other], other.rel_info[self._tbl()])
        )

    def __getitem__(self, item) -> Tuple[str]:
        try:
            return self._rel_info.__getitem__(item)
        except KeyError:
            raise KeyError(
                "No realtionship between "
                f"{item!r} and {self._tbl()!r}.") from None

    def __repr__(self):  # pragma: no cover
        return repr({**self._rel_info})


def pass_condition_up(*from_nodes: MetaNodeMixin, to: MetaNodeMixin):
    """
    将所有from节点的查询条件汇总至to节点，
    汇总由树的最底层开始，往上进行。
    """
    depth_dict = defaultdict(set)
    max_depth = min_depth = to.depth

    for node in [*from_nodes, to]:
        depth = node.depth
        depth_dict[depth].add(node)
        max_depth = max(max_depth, depth)

    # 从树的最底层向上汇总，同时将父节点加入depth_dict
    # 确保所有节点在汇总其查询条件时，得到的条件列表总是完整的。
    for dp in range(max_depth, min_depth, -1):
        for node in depth_dict[dp]:
            # noinspection PyProtectedMember
            node._pass_up()
            depth_dict[dp-1].add(node.parent)

    del depth_dict


class MetaTable(MetaNodeMixin):
    """逻辑表表元类

    通过类属性的指定可以自动完成树形结构的搭建。
    同一棵树的不同节点的限制条件会自动传递，最终影响查询结果。

    Note:
        使用元类的目的是为了让类可以像实例一样被使用。
        若要使用实例属性，请通过ClassName.object.attr_or_method访问。

    """
    #: 父子表的关联关系
    rel_info: RelationInfo
    #: 表查询的字段
    fields: Tuple[str]

    def __init__(cls, cls_name: str, supercls: Tuple, attrdict: Dict):
        cls.object = cls()

        cls.__datatable = datatable = attrdict.pop('datatable', None)
        cls.__async_datatable = attrdict.pop('async_datatable', None)
        cls.__table_info = attrdict.pop('table_info', None)

        cls._datatable = datatable
        if 'parent' in attrdict:
            parent = attrdict.pop('parent')
        else:
            parent = {}

        fields = attrdict.get('fields', None)
        if fields is not None:
            if isinstance(fields, str):
                fields = (fields,)
            elif any(f == '*' for f in fields):
                fields = None

        cls.fields = fields
        #: 用于管理查询条件的状态
        cls.__cm = ConditionManager()
        #: 查询数据的缓存
        cls.__data_pxy = DataProxy(max_size=attrdict.pop('cache_size', 5))

        cls.rel_info = RelationInfo(cls)  #: 表与其父子表的关联关系，主要是字段信息
        cls.set_parent_table(
            parent.get('cls'),
            on=parent.get('on'),
            alias=parent.get('alias'),
        )
        super().__init__(cls_name, supercls, attrdict)

    @cached_property
    def datatable(cls) -> T_DatatableInstance:
        """数据表元素"""
        if cls.__datatable is not None:
            return cls.__datatable
        if cls.__table_info is None:
            raise KeyError("Either 'table_info' or 'datatable' should be presented.")
        tbl = get_datatable(cls.__table_info)
        del cls.__table_info
        return tbl

    @cached_property
    def async_datatable(cls) -> T_AsyncDatatableInstance:
        """异步数据表元素"""
        if cls.__async_datatable is not None:
            return cls.__async_datatable
        if cls.__table_info is None:
            raise KeyError("Either 'table_info' or 'async_datatable' should be presented.")
        tbl = get_datatable(cls.__table_info, sync=False)
        del cls.__table_info
        return tbl

    @cached_property
    def name(cls) -> str:
        """表名"""
        return cls.datatable.table_name

    @property
    def data(cls) -> pd.DataFrame:
        """
        从数据库获取当前查询条件下的数据。

        Returns:
            :class:`DataFrame` : 查询结果

        Raises:
            RuntimeError: 树中没有任何一张表有查询条件时

        Note:
            基本查询流程如下：

            1. 找到所有处于 :attr:`locked` 状态的表，查询其和待查表的最小共同祖先。
            2. 把限定条件传递至共同祖先，再将限定条件传递至待查询表

                * | 如果传递过程中出现条件矛盾或者联合条件无数据导致无法继续传递，
                  | 则停止传递过程，直接返回带字段名的空 ``Dataframe`` 。
                * 否则开始查询

            3. 查询前首先在缓存中进行，如果未命中缓存，则执行sql查询数据库。
            4. 当两次查询间树中所有表的 :attr:`locked` 状态无变化，则条件传递过程也会被适当缩减。
        """
        return cls.query(cls.fields)

    def query(cls, fields: Iterable[str] = None) -> pd.DataFrame:

        locked = [node for node in cls.family if node.locked]
        if not locked:
            raise RuntimeError("At least lock one table before query.")

        if not ConditionManager.any_changed(node.__cm for node in cls.family):
            # 距离上次查询，同一棵树的表条件没有变化
            for node in cls.iter_to_root():  # OK if node is cls
                if node.__cm.valid:
                    logger.debug("Condition not changed from last query.")
                    return cls._pass_and_query(node, pass_up=False, fields=fields)

        # 两种情况会导致代码运行到这里
        # 1. condition_changed == True, 这种情况明显需要清空临时查询条件
        # 2. condition_changed == False 但是 all(node.__cm.valid is False)
        # 这种情况是由于先前查询失败于_pass_up阶段，或者先前查询的top不是本次查询的祖先
        # 不论哪种，清空所有临时条件都会引起一定的重复计算，但是不会引起逻辑错误，
        # 不清空虽然也不会导致逻辑错误，但是随着查询次数增加，condition增多，and运算
        # 会消耗更多资源，内存占用也会增加, 因此这里选择清空的方案。
        # todo 对于case2，似乎可以清空当前有临时条件的最高层节点数据，将次高层有条件的作为locked，pass至top
        for node in cls.family:
            node.__cm.clear_tmp()  # 清空所有临时添加的查询条件

        top = cls.common_ancestor(*locked)

        return cls._pass_and_query(top, locked, fields=fields)

    def _pass_and_query(
        cls,
        top: 'MetaTable',
        locked: Iterable['MetaTable'] = None,
        pass_up: bool = True,
        fields: Iterable[str] = None
    ) -> pd.DataFrame:
        try:
            # 把锁定条件传递至共同祖先
            if pass_up:
                pass_condition_up(*locked, to=top)
                top.__cm.mark_as_valid()

            # 将限定条件传递至待查询表
            top.__pass_down_to(cls)
        except (ConditionPassError, SqlCondError, OpCombineError) as e:
            logger.debug(
                f"Condition passing is terminated due to an error. Return empty dataframe. "
                f"Error: {str(e)}")
            return pd.DataFrame(columns=cls.columns)
        else:
            return cls._query(use_cache=True, fields=fields)

    #: 表中是否有通过 :meth:`lock`, :meth:`temporary_lock`,
    #: :meth:`permanent_lock` 带入的条件。
    locked = property(lambda self: self.__cm.has_main())

    #: 所有查询条件，包括条件传递时临时添加的条件。
    condition = property(lambda self: self.__cm.condition)

    @contextmanager
    def temporary_lock(cls, **kwargs):
        cls.lock(**kwargs)
        yield
        cls.release()

    def lock(cls, **kwargs):
        """
        增加当前表的查询条件

        Args:
            **kwargs: 查询条件，传递给 |SQLCND| ，需符合 |SQLCND| 入参要求。
        """
        cls.__cm.add_main_cond(SQLCondition(
            **kwargs, quote_char=cls.datatable.quote_char))

    def permanent_lock(cls, **kwargs):
        cls.lock(**kwargs)
        _ = cls.data
        # cls.__data_pxy.make_cache(cls.condition, data)

    def release(cls):
        try:
            cls.__cm.pop_main()
        except IndexError:
            raise RuntimeError("No lock to release!") from None

    def _query(
        cls,
        use_cache: bool = True,
        unique: bool = False,
        fields: Iterable[str] = None,
        cond: SQLCondition = None
    ) -> pd.DataFrame:
        cond = cond or cls.condition
        if cond is None:
            raise RuntimeError("Cannot execute query without condition.")

        if use_cache:
            df = cls.__data_pxy.get_data(cond, fields)
            if df is not None:
                return df

        df = pd.DataFrame()
        for cd in cond.to_sql():
            df = pd.concat(
                [
                    df,
                    cls.datatable.select(columns=fields, where=cd, distinct=unique)
                ]
            )

        logger.debug(f"Got DATA:\n {df}")

        cls.__data_pxy.make_cache(cond, fields, df)
        return df

    def query_with_condition(
        cls,
        cond: SQLCondition,
        fields: Union[str, Iterable[str]] = None,
        unique: bool = False
    ) -> pd.DataFrame:
        if fields is not None:
            if isinstance(fields, str):
                fields = (fields, )
            elif not isinstance(fields, tuple):
                fields = tuple(fields)
        return cls._query(use_cache=False, unique=unique, fields=fields, cond=cond)

    def _pass_up(cls):
        """向父节点传递当前节点的条件，不会改变ConditionManager状态"""
        parent = cls.parent  # make local ref

        if parent is None:
            return

        logger.debug(f"Start passing up {cls!r} -> {parent!r}.")
        cond = cls.__get_pass_cond(parent)
        parent.__set_query_cond(cond)
        logger.debug(f"Passed UP {cls!r} -> {parent!r}. Condition: {cond}.")

    def __get_pass_cond(cls, to_tbl: 'MetaTable'):
        """获取其他表节点的传递条件，目标节点必须为当前节点的父节点或子节点"""
        cls_cond = cls.condition
        rel_info = cls.rel_info
        # 判断fields是否是待传递对象关联字段的子集，
        # 如果是，可以不做查询，直接传递，否则，查询后传递。
        if all(rel_info.is_rel_field(to_tbl, fd) for fd in cls_cond.all_fields):
            logger.debug("No extra field, pass condition directly.")
            cond = copy.copy(cls_cond)
            # 处理关联字段不同名的情况
            if rel_info.has_alias_with(to_tbl):
                cond.rename_field(dict(zip(rel_info[to_tbl], to_tbl.rel_info[cls])))
        else:
            logger.debug(f"Got extra field, need query.")
            # 如果待传递节点已有关联字段的条件，可以提取到当前节点进行查询
            target_cond = to_tbl.condition
            if target_cond is not None:
                conditioned_flds = [fd for fd in target_cond.all_fields if rel_info.is_rel_field(to_tbl, fd)]
                if conditioned_flds:
                    logger.debug(f"{to_tbl!r}'s fields: {conditioned_flds} is conditioned.")
                    cls_cond &= target_cond[conditioned_flds]
            # 执行查询
            data = cls._query(unique=True, fields=rel_info[to_tbl], cond=cls_cond).dropna()
            if data.empty:
                raise ConditionPassError("Cannot pass condition because no data is fetched.")
            keys = to_tbl.rel_info[cls]
            logger.debug(f"{to_tbl} relate to {cls!r} with fields: {keys}.")
            logger.debug(f"Fields are restrained by:\n{data!r}.")
            cond = SQLCondition(fields=keys, value_list=data, quote_char=cls.datatable.quote_char)
        return cond

    def __set_query_cond(cls, cond: SQLCondition):
        cls.__cm.add_tmp_cond(cond)

    def __pass_down_to(cls, descendant: 'MetaTable'):
        """依次向子节点传递当前节点的条件，直至达到目标后代节点
        所有被传递节点的条件将会被标记为有效，会改变ConditionManager状态，
        """
        parent = cls

        for dsnt in cls.iter_to_descendant(descendant):
            logger.debug(f"Start passing down {parent!r} -> {dsnt!r}.")
            condition = parent.__get_pass_cond(dsnt)
            dsnt.__set_query_cond(condition)
            dsnt.__cm.mark_as_valid()  # 查询条件标记为有效
            logger.debug(f"Passed down {parent!r} -> {dsnt!r}. Condtion: {condition!r}")
            parent = dsnt

    @cached_property
    def columns(cls) -> List[str]:
        """数据表列名序列"""
        return list(cls.datatable.structure.columns.keys())

    def __repr__(self):
        return f"<{self.__name__}>"

    @property
    def all_data(cls) -> pd.DataFrame:
        """获取全表数据，谨慎使用"""
        return cls.datatable.select(columns=cls.fields)

    def set_parent_table(
        cls,
        table: 'MetaTable',
        on: Iterable[str],
        alias: Optional[Iterable[str]] = None,
    ):
        """
        设置父表

        Args:
            table: 父表
            on: 关联的字段名（当前表）
            alias: 关联字段名在父节点的名字（=表示相同，全部相同可以不指定）

        """
        if table is None:
            return

        cls.set_parent(table)
        on = tuple(on)
        if alias is not None:
            alias = tuple(alias)
        table.rel_info.add_child_relation(cls, on, alias)
        cls.rel_info.add_parent_relation(table, on)


class BaseTable(metaclass=MetaTable):
    """
    Helper class, 用于继承

    可定义的类属性:
        .. code-block:: python

            # 与父节点的关联信息
            parent = {
                # 父节点的类名:
                "cls": ObjectInfo,
                 # 关联的字段名:
                "on": ('sys_contract_id', 'sys_object_id', 'sys_sub_id'),
                # 关联字段名在父节点的名字（=表示相同，全部相同可以不指定）:
                "alias": ('=', 'object_id', 'sub_id')
            }
            # 查询字段，默认查询所有字段
            fields = ('id', 'name', 'etc')
            # 最大的查询缓存数
            cache_size = 5
            # 绑定数据表元素
            datatable = table
            # 数据表信息
            table_info: Union[TableInfo, dict] = {
                'element_name': "元素名",
                'element_type': "元素类型",
                'folder_id': "文件夹id（与元素路径二选一即可）",
                'path': "元素路径（与文件夹id二选一即可）",
                'table_name': "真实表名（可选）",
                'server_name': "数据表服务名（可选）",
            }
    """
