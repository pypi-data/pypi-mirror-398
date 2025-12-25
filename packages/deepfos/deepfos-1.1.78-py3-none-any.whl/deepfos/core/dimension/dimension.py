import json
from typing import Tuple, List, Dict

import pandas as pd

from .dimmember import DimMember
from ._base import (
    DimensionBase, MemberContainer,
    NAME_DFLT, PNAME_DFLT, IS_SHARED_DFLT
)
from .dimcreator import *
from deepfos.options import OPTION
from deepfos.core.logictable.nodemixin import bfs, TreeRenderer


class Dimension(DimensionBase):
    """基础维度，拥有完整维度树，对维度成员的查询全部在本地进行。"""

    def __init__(self, dim_name=None, root=None):
        super().__init__(dim_name)
        #: 维度树的根节点
        self.root = root
        #: 维度成员名-成员实例 构成的字典
        self._members_memo = {}
        self._update_member_dict()

    def __get__(self, instance, owner=None):
        return self

    def _update_member_dict(self):
        """更新维度树的维度成员关系字典"""
        if self.root is None:
            return
        self._members_memo = {
            node.name: node
            for node in self.root.family
        }

    def __set_name__(self, owner, name):
        self.name = name

    @classmethod
    def from_df(
        cls,
        dim_name: str,
        df: pd.DataFrame,
        name_col: str = NAME_DFLT,
        parent_name_col: str = PNAME_DFLT,
        is_shared_col: str = IS_SHARED_DFLT,
        extra_info: Tuple = (),
    ):
        """
        从 ``Dataframe`` 创建维度，数据必须至少含有父节点名称列和当前节点名称列。

        Args:
            dim_name: 维度名称
            df: 创建维度的数据源
            name_col: 当前节点名称列的列名
            parent_name_col: 父节点名称列的列名
            is_shared_col: 是否共享节点列的列名
            extra_info: 其他属性列，若提供，会成为维度成员的额外属性

        Returns:
            创建完成的维度对象

        Example:
            .. code-block:: python

                # df 是已经加载好的 DataFrame 数据
                dim = Dimension.from_df('dim', df)

        """
        ins = cls(dim_name)
        tree_creator = DataFrameTreeCreator(
            df, name_col, parent_name_col, is_shared_col, extra_info)
        ins.root, ins._members_memo = tree_creator.create_tree()
        return ins

    @classmethod
    def from_db(
        cls,
        dbconn,
        dim_name: str,
        name_col: str = NAME_DFLT,
        parent_name_col: str = PNAME_DFLT,
        is_shared_col: str = IS_SHARED_DFLT,
        extra_info: Tuple = (),
    ):
        """
        由数据库创建维度，数据必须至少含有父节点名称列和当前节点名称列。

        Args:
            dim_name: 维度名称
            dbconn: 创建维度的数据源
            name_col: 当前节点名称列的列名
            parent_name_col: 父节点名称列的列名
            is_shared_col: 是否共享节点列的列名
            extra_info: 其他属性列，若提供，会成为维度成员的额外属性

        Returns:
            创建完成的维度对象

        Example:
            .. code-block:: python

                # dbconn 是已经创建好的数据库连接对象
                dim = Dimension.from_db(dbconn, 'dim')

        """
        ins = cls(dim_name)
        tree_creator = DBTreeCreator(
            dbconn, dim_name, name_col, parent_name_col, is_shared_col, extra_info)
        ins.root, ins._members_memo = tree_creator.create_tree()
        return ins

    @classmethod
    def from_json(
        cls,
        dim_name: str,
        jsn: List[Dict],
        name_col: str = NAME_DFLT,
        parent_name_col: str = PNAME_DFLT,
        is_shared_col: str = IS_SHARED_DFLT,
        extra_info: Tuple = (),
    ):
        """
        从 ``json`` 中创建维度，数据必须至少含有父节点名称列和当前节点名称列。

        Args:
            dim_name: 维度名称
            jsn: 创建维度的数据源
            name_col: 当前节点名称列的列名
            parent_name_col: 父节点名称列的列名
            is_shared_col: 是否共享节点列的列名
            extra_info: 其他属性列，若提供，会成为维度成员的额外属性

        Returns:
            创建完成的维度对象

        Notes:
            当需要设置额外属性且额外属性只有一个时，也需要使用 ``tuple`` 输入，具体如下例所示。

        Example:
            .. code-block:: python

                # data 为建树所需的 Json 数据
                js = json.loads(data)
                # attribute为唯一的额外属性
                dim = Dimension.from_json('dim', js, extra_info=(attribute,))

        """
        ins = cls(dim_name)
        tree_creator = JsonTreeCreator(
            jsn, name_col, parent_name_col, is_shared_col, extra_info)
        ins.root, ins._members_memo = tree_creator.create_tree()
        return ins

    @classmethod
    def from_api(
        cls,
        dim_name: str,
        api: List[Dict],
        name_col: str = NAME_DFLT,
        parent_name_col: str = PNAME_DFLT,
        is_shared_col: str = IS_SHARED_DFLT,
        extra_info: Tuple = (),
        fetch_all: bool = False
    ):
        """
        从系统的 ``API`` 中创建维度，数据必至少含有父节点名称列和当前节点名称列。

        Args:
            dim_name: 维度名称
            api: 维度接口
            name_col: 当前节点名称列的列名
            parent_name_col: 父节点名称列的列名
            is_shared_col: 是否共享节点列的列名
            extra_info: 其他属性列，若提供，会成为维度成员的额外属性
            fetch_all: 取出从API中获取的全部数据

        Returns:
            创建完成的维度对象

        Example:
            .. code-block:: python

                # api 是需要调用的 API 接口
                dim = Dimension.from_api('dim', api)

        """
        ins = cls(dim_name)
        tree_creator = ApiTreeCreator(
            dim_name, api, name_col, parent_name_col, is_shared_col,
            extra_info, fetch_all)
        ins.root, ins._members_memo = tree_creator.create_tree()
        return ins

    def __getitem__(self, item):
        """
        获取维度成员

        存在两种情况::

            mbr = dim['A']  # 得到DimMember对象
            mbr_container = dim['A', 'B']  # 得到MemberContainer对象

        """
        try:
            if isinstance(item, str):
                return self._members_memo[item]
            else:
                # for better error information
                members = list(item)
                for idx, item in enumerate(members):
                    members[idx] = self._members_memo[item]
                return MemberContainer(*members)
        except KeyError:
            raise KeyError(f"Member '{item}' does not belong to current dimension.") from None

    def resolve_member(self, member):
        """
        返回维度树中指定的维度成员对象。

        Args:
            member: 维度成员，可为成员名或维度成员

        Returns:
            指定的维度成员对象

        Raises:
            ValueError: 维度成员不存在于维度树中或者输入数据类型不符合要求
            KeyError: member为成员名且该成员不存在于维度树中

        """
        if isinstance(member, DimMember):
            if member not in self:
                raise ValueError(f"Member '{member}' does not belong to current dimension.")
            return member
        elif isinstance(member, str):
            if member in self._members_memo:
                return self._members_memo[member]
            else:
                raise KeyError(f"Member '{member}' does not belong to current dimension.")
        else:
            raise TypeError(f"Expect str or {DimMember.__name__}, got {type(member).__name__}.")

    def delete(self, member, update_memo=True):
        """
        删除维度成员及其子树，删除的成员成员维度必须在维度树中。

        Args:
            member: 维度成员，可为成员名或维度成员
            update_memo(bool): 是否更新 ``_members_memo`` 字典

        Notes:
            为确保正常获取成员， ``update_memo`` 需设置为 ``True`` ，
            但如果需要连续删除多个成员时，建议删除最后一个时设置为 ``True`` ，
            其余为 ``False`` 。
            删除的维度成员可以为根节点，删除后树为空。

        """
        self.resolve_member(member).set_parent(None)
        if member is self.root:
            self.root = None
            self._members_memo = {}
            self.selected = {}
        else:
            if update_memo:
                self._update_member_dict()

    def __contains__(self, item):
        """判断节点是否存在于维度树中"""
        return item in self._members_memo.values()

    def attach(self, node, attach_to, update_memo=True):
        """
        将维度成员及其子树接入当前维度树指定节点，接入节点必须存在于维度中。

        Args:
            node(DimMember): 待加入的维度成员
            attach_to(DimMember): 接入的节点
            update_memo(bool): 是否更新 ``_members_memo``

        Notes:
            为确保正常获取成员， ``update_memo`` 需设置为 ``True`` ，
            但如果需要连续加入多个成员时，建议加入最后一个时设置为 ``True`` ，
            其余为 ``False`` 。

        """
        member = self.resolve_member(attach_to)
        node.set_parent(member)
        if update_memo:
            self._update_member_dict()

    def to_multidict(self, *attrs, name=NAME_DFLT, parent_name=PNAME_DFLT,
                     show_all=False, incl_root=True, exclude=None):
        """
        将维度树中的维度成员及其指定属性存储为字典。

        Args:
            *attrs(dict): 字典需要包含的维度成员指定属性
            name(str): 维度成员名
            parent_name(str): 维度成员的父节点名
            incl_root(bool): 是否包含根节点
            show_all(bool): 显示成员的所有属性
            exclude(bool): 需要排除（不输出）的属性

        Returns:
            包含所有维度成员的字典列表

        Example:
              .. code-block:: python

                # 指定 base， children 属性存储在字典中
                dim_dict = dim.to_multidict('base', 'children')
                # 执行上述代码就会生成如下字典列表， 其中 base 和 children 的值为维度成员对象：
                '''
                [{'base': ..., 'children': ..., 'name': ..., 'parent_name': ...}, ...]
                '''

        """
        family = self.root.family if incl_root else self.root.iter_descendants()
        return [member.to_dict(
            *attrs, name=name, parent_name=parent_name,
            show_all=show_all, exclude=exclude
        ) for member in family]

    def to_json(self, *attrs, path):
        """
        将维度对象中的维度成员及其指定属性存储在 ``path`` 中。

        Args:
            *attrs(dict): 需要存储的维度成员指定属性
            path(str): 存储路径

        """
        with open(path, 'wt', encoding='utf8') as f:
            json.dump(self.to_multidict(*attrs), f)

    def save(self, conn=None, mode='replace'):
        """
        保存维度成员

        Args:
            conn: 连接对象
            mode(str): 保存编辑模式， ``replace`` 为增量编辑， ``update`` 为全量编辑

        Raises:
            ValueError: 选择的模式不是 ``replace`` 或 ``update``

        """
        valid_mode = ('replace', 'update')
        if mode not in valid_mode:
            raise ValueError(f"Unknown mode: '{mode}', valid modes are {valid_mode}.")

        conn_info = conn or OPTION.system.conn_info
        from deepfos.api.apifoundation import FoundationApi # noqa
        api = FoundationApi(conn_info)
        dim_data = self.to_multidict(show_all=True, incl_root=False)

        if mode == 'replace':
            api.save_dimension_member(self.name, dim_data, 1)
        else:
            for data in dim_data:
                api.update_dimension_member(self.name, data)

    def render(self):
        return TreeRenderer().render(self.root)


class SortedDimension(Dimension):
    def __init__(self, dim_name):
        super().__init__(dim_name)

    def __getitem__(self, item):
        if not isinstance(item, slice):
            return super().__getitem__(item)

        # start, stop are both None
        if item.start is None and item.stop is None:
            mbrs = list(bfs(self.root))[item]
            return MemberContainer(*mbrs)

        step = item.step or 1

        if item.start and item.stop:
            # none of start, stop is None
            node_start = super().__getitem__(item.start)
            node_stop = super().__getitem__(item.stop)

            if node_start.depth != node_stop.depth:
                raise ValueError(f'{node_start}和{node_stop}不在同一层')

            ancestor = node_start.common_ancestor(node_stop)
            depth = node_start.depth - ancestor.depth
            mbrs_same_depht = list(bfs(ancestor, depth=depth, include=False))
            start = mbrs_same_depht.index(node_start)
            stop = mbrs_same_depht.index(node_stop)
            stop = stop + (1 if step > 0 else -1)
        else:
            # one of start, stop is None
            valid_node = super().__getitem__(item.start or item.stop)
            target_depth = valid_node.depth
            mbrs_same_depht = list(
                node for node in bfs(self.root, depth=target_depth)
                if node.depth == target_depth)
            idx = mbrs_same_depht.index(valid_node)

            if item.stop is None:
                start, stop = idx, None
            else:
                start, stop = None, idx + (1 if step > 0 else -1)

        idx_slice = slice(start, stop, step)
        return MemberContainer(*mbrs_same_depht[idx_slice])

    @classmethod
    def from_db(cls, dbconn, dim_name, name_col=NAME_DFLT, parent_name_col=PNAME_DFLT, extra_info=tuple()):
        ins = cls(dim_name)
        tree_creator = DBTreeCreator(dbconn, dim_name, name_col, parent_name_col, extra_info)
        ins.root, ins._members_memo = tree_creator.create_tree()
        ins.sort()
        return ins

    @classmethod
    def from_df(cls, dim_name, df, name_col=NAME_DFLT, parent_name_col=PNAME_DFLT, extra_info=tuple()):
        ins = cls(dim_name)
        tree_creator = DataFrameTreeCreator(df, name_col, parent_name_col, extra_info)
        ins.root, ins._members_memo = tree_creator.create_tree()
        ins.sort()
        return ins

    @classmethod
    def from_json(cls, dim_name, jsn, name_col=NAME_DFLT, parent_name_col=PNAME_DFLT, extra_info=tuple()):
        ins = cls(dim_name)
        tree_creator = JsonTreeCreator(jsn, name_col, parent_name_col, extra_info)
        ins.root, ins._members_memo = tree_creator.create_tree()
        ins.sort()
        return ins

    @classmethod
    def from_api(cls, dim_name, api, name_col=NAME_DFLT, parent_name_col=PNAME_DFLT,
                 extra_info=tuple(), fetch_all=False):
        ins = cls(dim_name)
        tree_creator = ApiTreeCreator(dim_name, api, name_col, parent_name_col, extra_info, fetch_all)
        ins.root, ins._members_memo = tree_creator.create_tree()
        ins.sort()
        return ins

    def attach(self, node, attach_to, update_memo=True):
        member = self.resolve_member(attach_to)
        node.set_parent(member)
        self.sort(root_node=member)
        if update_memo:
            self._update_member_dict()

    def sort(self, func=lambda x: x.name, root_node=None):
        """
        给指定节点的后继节点进行排序

        Args:
            func(function): 排序方式，默认为按照节点名进行排序
            root_node(DimMember): 需要对后继节点进行排序的节点，默认为根节点

        Returns:
            排序后的维度树
        """
        if not root_node:
            root_node = self.root
        for node in root_node.idescendant:
            if len(node.children) > 1:
                node.children.sort(key=func)
