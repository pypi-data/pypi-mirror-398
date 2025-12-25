import pandas as pd
from deepfos.options import OPTION
from .dimmember import DimMember

__all__ = [
    'TreeCreator',
    'JsonTreeCreator', 'DBTreeCreator',
    'DataFrameTreeCreator', 'ApiTreeCreator'
]


class TreeCreator:
    def __init__(self, raw_data):
        self.raw = raw_data

    def iter_node(self):
        """迭代节点， 取出数据中的每条元数据"""
        raise NotImplementedError()

    def get_node_name(self, node):
        """获取节点名"""
        raise NotImplementedError()

    def get_node_parent_name(self, node):
        """获取父节点名"""
        raise NotImplementedError()

    def get_node_is_shared(self, node):
        """获取父节点名"""
        raise NotImplementedError()

    def set_extra_attrs(self, member, node):
        """设置节点额外属性"""
        raise NotImplementedError()

    def create_tree(self):
        """
        建树

        Raises:
            ValueError: 节点名不为 ``str`` 或者多个根节点
            ValueError: 无根节点
        """
        dim_memo = {}

        root = None
        for node in self.iter_node():
            name = self.get_node_name(node)
            is_shared = self.get_node_is_shared(node)

            if name not in dim_memo:
                dim_memo[name] = DimMember(name)
            member = dim_memo[name]

            if is_shared:
                shared_mbr = DimMember(name)
                self.set_extra_attrs(shared_mbr, node)
                member.add_shared(shared_mbr)
                continue

            self.set_extra_attrs(member, node)

            parent_name = self.get_node_parent_name(node)

            if not isinstance(parent_name, str) or not parent_name:
                if root is not None:
                    raise ValueError("Cannot create tree because there are more than one root in data.")
                root = member
            else:
                if parent_name not in dim_memo:
                    parent = DimMember(parent_name)
                    dim_memo[parent_name] = parent
                member.set_parent(dim_memo[parent_name])

        if root is None:
            raise ValueError("No root found from given data.")

        return root, dim_memo


class DataFrameTreeCreator(TreeCreator):
    def __init__(self, raw_data, name_col, parent_name_col, is_shared_col, extra_attrs=None):
        super().__init__(raw_data)
        self.is_shared_col = is_shared_col
        self.parent_name_col = parent_name_col
        self.name_col = name_col
        self.extra_attrs = extra_attrs

    def iter_node(self):
        for row in self.raw.itertuples(index=False):
            yield row

    def get_node_name(self, node):
        return getattr(node, self.name_col)

    def get_node_parent_name(self, node):
        return getattr(node, self.parent_name_col)

    def get_node_is_shared(self, node):
        return getattr(node, self.is_shared_col)

    def set_extra_attrs(self, member, node):
        """
        设置节点额外属性

        Args:
            member(DimMember): 节点对象
            node: 一条元数据
        """
        extra_attrs = self.extra_attrs or self.raw.columns

        for attr in extra_attrs:
            if hasattr(node, attr):
                val = getattr(node, attr)
            else:
                val = getattr(node, attr.lower(), None)

            setattr(member, attr, val)
        member.extra_attrs = tuple(extra_attrs)


class DBTreeCreator(DataFrameTreeCreator):
    def __init__(self, dbconn, dimname, name_col, parent_name_col, is_shared_col, extra_attrs=None):
        self.dimname = dimname
        self.dbconn = dbconn

        super().__init__(self.get_raw_data(), name_col, parent_name_col, is_shared_col, extra_attrs)

    def get_raw_data(self):
        """从数据库中筛选出数据表建树"""
        return self.dbconn.query_dfs(f"SELECT * FROM {self.get_dim_table()}")

    def get_dim_table(self):
        sql = f"SELECT table_dimension FROM app{OPTION.system.app_id}_dimension_info WHERE name='{self.dimname}'"
        return self.dbconn.query_dfs(sql).iloc[0, 0]


class JsonTreeCreator(DataFrameTreeCreator):
    def iter_node(self):
        for node in self.raw:
            yield node

    def get_node_name(self, node):
        return node.get(self.name_col)

    def get_node_parent_name(self, node):
        return node.get(self.parent_name_col)

    def get_node_is_shared(self, node):
        return node.get(self.is_shared_col)

    def set_extra_attrs(self, member, node):
        if self.extra_attrs is None:
            return

        member.extra_attrs = tuple(self.extra_attrs)

        for attr in self.extra_attrs:
            if attr in node:
                val = node[attr]
            else:
                val = node.get(attr.lower(), None)
            setattr(member, attr, val)


class ApiTreeCreator(DataFrameTreeCreator):
    def __init__(
            self, dimname, api,
            name_col, parent_name_col, is_shared_col,
            extra_attrs=None, fetch_all=False
    ):
        super().__init__(None, name_col, parent_name_col, is_shared_col, extra_attrs)
        self.dimname = dimname
        self.api = api
        self.fetch_all = fetch_all
        self.raw = self.get_raw_data()

    def get_raw_data(self):
        if self.fetch_all:
            cols = ''
        else:
            cols = ','.join((*self.extra_attrs, self.name_col, self.parent_name_col))
        rslt = self.api.api_get_dimmbr(self.dimname + "{IDescendant(#root,0)}", cols, '1')["resultList"]
        return pd.DataFrame(rslt)
