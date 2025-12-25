from typing import Union

import pandas as pd

from deepfos.core.logictable import MetaTable
from deepfos.lib.utils import unpack_expr
from deepfos.element.dimension import Dimension as EleDimension
from deepfos.element.datatable import DataTableClickHouse, DataTableMySQL
from ._base import DimensionBase, MemberBase, MemberContainer, NAME_DFLT
from .dimexpr import DimExprAnalysor

# -----------------------------------------------------------------------------
# typing
T_AbsDataTable = Union[DataTableMySQL, DataTableClickHouse]


# -----------------------------------------------------------------------------
# core
class AsMbrContainer:
    def __init__(self, func, include_self=False):
        self.func = func
        self.include_self = include_self

    def __get__(self, instance, owner=None):
        with instance.tbl_dim.temporary_lock(name__in=instance.name_list):
            with self.func(instance):
                rslt = instance.data_tbl.data
        if self.include_self:
            # noinspection PyProtectedMember
            rslt = rslt.append(instance._data)
        return SysDimMemberContainer(rslt, *instance.split(), hierarchy=self.name)

    def __set_name__(self, owner, name):
        self.name = name


class SysDimension(DimensionBase):
    """
    系统维度

    绕过维度元素，使用维度底层数据表创建的维度

    Args:
        dimname: 维度名称
        tbl_closure: 维度绑定的closure表，记录维度层级关系
        tbl_dim: 维度数据表
        name_only: 是否仅需要维度名 (Cube用)
        folder_id: 维度所在文件夹ID
        path: 维度所在绝对路径

    """
    def __init__(
        self,
        dimname: str,
        tbl_closure: T_AbsDataTable = None,
        tbl_dim: T_AbsDataTable = None,
        name_only: bool = False,
        folder_id: str = None,
        path: str = None,
        server_name: str = None,
    ):
        super().__init__(dimname)
        self._name_only = name_only
        if tbl_closure is None or tbl_dim is None:
            tbl_dim, tbl_closure = self._get_datatable(folder_id, path, server_name)

        self._create_tree(tbl_closure, tbl_dim, name_only)

    def _create_tree(self, tbl_closure, tbl_dim, name_only: bool):
        # 组建table_dimension和table_closure的关联关系
        # 父表为table_closure，以不同字段关联两张table_dimension
        self.tbl_closure = MetaTable(tbl_closure.table_name, tuple(), {"datatable": tbl_closure})
        self.tbl_dim = MetaTable(
            tbl_dim.table_name, tuple(),
            {"datatable": tbl_dim, "parent": {"cls": self.tbl_closure, 'on': ('id',), "alias": ('ancestor',)}}
        )
        self.data_tbl = MetaTable(
            tbl_dim.table_name + '_data', tuple(),
            {
                "datatable": tbl_dim,
                "parent": {"cls": self.tbl_closure, 'alias': ('descendants',), 'on': ('id',)}
            }
        )
        if name_only:
            self.data_tbl.fields = (NAME_DFLT,)

    def _get_datatable(self, folder_id: str, path: str, server_name: str = None):
        # 获取table_dimension和table_closure的真实表名
        dim = EleDimension(self.name, folder_id=folder_id, path=path, server_name=server_name)
        return dim.table_dimension, dim.table_closure

    def __getitem__(self, item):
        if self._name_only:
            data = pd.DataFrame(data={NAME_DFLT: [item]})
            return SysDimMember(item, self.tbl_closure, self.tbl_dim, self.data_tbl, data)
        return SysDimMember(item, self.tbl_closure, self.tbl_dim, self.data_tbl)


_base = lambda self: self.data_tbl.temporary_lock(is_base__eq=1)
_children = lambda self: self.tbl_closure.temporary_lock(distance__eq=1)
_descendant = lambda self: self.tbl_closure.temporary_lock(distance__ne=0)


class SysDimMember(MemberBase):
    def __init__(self, name, tbl_closure, tbl_dim, data_tbl, data=None):
        super().__init__(name)
        self.tbl_closure = tbl_closure
        self.tbl_dim = tbl_dim
        self.data_tbl = data_tbl
        self.name_list = (name, ) if isinstance(name, str) else name
        if data is None:
            self._data = self._fetch_data()
        else:
            self._data = data
        if len(self.name_list) != len(self._data):
            unknown = set(self.name_list) - set(self._data.name)
            raise ValueError(f"Dimension {unknown!r} does not exist.")

    def _fetch_data(self):
        with self.tbl_dim.temporary_lock(name__in=self.name_list):
            return self.tbl_dim.data

    Base = AsMbrContainer(_base)
    IBase = AsMbrContainer(_base, include_self=True)
    Children = AsMbrContainer(_children)
    IChildren = AsMbrContainer(_children, include_self=True)
    Descendant = AsMbrContainer(_descendant)
    IDescendant = AsMbrContainer(_descendant, include_self=True)

    @property
    def members(self):
        return list(self._data.itertuples(index=False))

    def __str__(self):
        return ';'.join(self.name_list)

    def where(self, method, **kwargs):
        return SysDimMemberContainer(self._data, *self.split()).where(method, **kwargs)

    def remove(self, *to_remove):
        return SysDimMemberContainer(self._data, *self.split()).remove(*to_remove)

    def split(self):
        """分解为仅行单个成员的SysDimMember"""
        if len(self.name_list) == 1:
            return [self]

        rtn = []
        for idx, name in enumerate(self.name_list):
            rtn.append(self.__class__(
                name, self.tbl_dim, self.tbl_closure, self.data_tbl,
                data=self._data.iloc[idx:idx+1]))
        return rtn


class SysDimMemberContainer(MemberContainer):
    def __init__(self, data, *anchor_mbr, hierarchy=None):
        super().__init__(*anchor_mbr, hierarchy=hierarchy)
        self.__data = data

    def _get_all_member(self):
        return list(self.__data.itertuples(index=False))


def read_expr(dim_expr):
    dimname, expr = unpack_expr(dim_expr)
    dim = SysDimension(dimname)
    return DimExprAnalysor(dim, expr).solve()
