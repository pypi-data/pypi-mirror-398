import json
import os
from functools import lru_cache
from typing import List

import pandas as pd
from deepfos.core.cube._base import CubeBase
from deepfos.core.cube.constants import DATACOL_DFLT
from deepfos.core.dimension import Dimension
from deepfos.lib.decorator import cached_property
from loguru import logger


class Cube(CubeBase):
    def __init__(
        self,
        data_src,
        cube_name=None,
        data_col=DATACOL_DFLT,
        dim_maps=None,
        **options
    ):
        super().__init__(cube_name, data_col, **options)

        self.dimensions = dim_maps or {}
        self._data_src = data_src

    @cached_property
    def fact_tbl(self):
        return self._data_src

    def _dim_check(self):
        dimensions = set(self._data_src.columns) - {self.data_col}
        remain = dimensions - self.dimensions.keys()
        if remain:
            raise ValueError(f"Failed to create cube. Missing dimensions: {remain}.")

    @classmethod
    def load(cls, folder, cube_name='cube', data_col=DATACOL_DFLT):
        """
        从文件夹中加载cube

        Args:
            folder: cube存放的文件夹
            cube_name: cube名
            data_col: 数据列名称

        Returns: Cube对象

        Notes:
            文件夹中需要包含以下文件:

                1. data.csv用于存放cube的数据源，其中有一列是data_col指定的数据列；
                2. data.csv中除数据列外的所有列均有与列名对应的json文件；
                3. json文件能够被正确读取为Dimension

        """
        if not os.path.isdir(folder):
            raise FileNotFoundError(f"Folder: {folder} does not exist.")

        data_src = pd.read_csv(os.path.join(folder, 'data.csv'))
        dim_maps = {}

        for dim in set(data_src.columns) - {data_col}:
            js_path = os.path.join(folder, f"{dim}.json")
            with open(js_path, 'rt', encoding='utf8') as f:
                dim_maps[dim] = Dimension.from_json(dim, json.load(f), extra_info=('weight',))
                data_src[dim] = data_src[dim].astype(str)

        return cls(data_src, cube_name, data_col, dim_maps=dim_maps)

    # -----------------------------------------------------------------------------
    # Cube 聚合逻辑
    @staticmethod
    def __split_pb_nodes(base_nodes, parent_nodes, members):
        """区分节点为聚合节点和叶子节点"""
        for mbr in members:
            if mbr.is_leaf:
                base_nodes.add(mbr.name)
            else:
                parent_nodes.append(mbr)

    def _get_full_data(self, data_src):
        pov = self.pov

        # 先处理定维度，减小事实表的规模
        data, base_pov = self.loc(tbl=data_src, return_pov=True, expand=True, **pov)

        # 对含有维度表达式的维度进行处理
        for dimname in self.dimensions.keys() - pov.keys():
            dim = self.dimensions[dimname]
            if not dim.activated:
                continue

            tmp_data_list = []

            members, mbr_containers = dim.classify_selected()
            base_nodes = set()
            par_nodes = []
            # 钻取深度
            drilldwon = {}

            self.__split_pb_nodes(base_nodes, par_nodes, members)

            for mbrc in mbr_containers:
                agg_tbl = None
                anchor = mbrc.anchor_mbrs[0]

                if anchor.is_leaf:
                    if mbrc.hierarchy.startswith('I'):
                        base_nodes.add(anchor.name)
                    continue

                # 将当前节点的所有后代节点都做一次聚合，然后把所有表连接起来
                if mbrc.hierarchy == 'IDescendant':
                    agg_tbl = self.aggregate_bottom_up(data, dimname, anchor.name, incl_top=True)
                elif mbrc.hierarchy == 'Descendant':
                    agg_tbl = self.aggregate_bottom_up(data, dimname, anchor.name, incl_top=False)
                elif mbrc.hierarchy == 'Base':
                    base_nodes.update(set(mbrc.data))
                elif mbrc.hierarchy == 'IBase':
                    self.__split_pb_nodes(base_nodes, par_nodes, mbrc.members)
                elif mbrc.hierarchy == 'Children':
                    self.__split_pb_nodes(base_nodes, par_nodes, [anchor])
                    drilldwon[dimname] = (1, False)
                elif mbrc.hierarchy == 'IChildren':
                    self.__split_pb_nodes(base_nodes, par_nodes, [anchor])
                    drilldwon[dimname] = (1, True)

                if agg_tbl is not None:
                    tmp_data_list.append(agg_tbl)

            # 叶子节点，不需要聚合，优先处理
            if base_nodes:
                tmp_data_list.append(data.loc[data[dimname].isin(base_nodes)])

            # 聚合节点
            if par_nodes:
                tmp_data_list.append(self._aggregate_pnode(data, dimname, par_nodes, drilldwon))

            if not tmp_data_list:
                logger.warning(
                    f"No data remained after filtered by dimension: {dim.to_expr()}. "
                    f"Return empty dataframe.")
                return pd.DataFrame()

            data = pd.concat(tmp_data_list, sort=False)
        return data.reset_index(drop=True)

    @lru_cache()
    def at(self, **kwargs):
        """
        查询在某些维度组合下的聚合值
        """
        rslt = self.fact_tbl

        for dimname, mbr in kwargs.items():
            dim = self.dimensions[dimname][mbr]
            if dim.is_leaf:
                rslt = rslt.loc[rslt[dimname] == mbr]
            else:
                rslt = rslt.loc[rslt[dimname].isin(set(dim.Base.data))]

        return rslt[self.data_col].sum()

    def loc(self, tbl=None, dig_level=None, return_pov=False, expand=False, **views):
        """
        展示指定维度组合下的数据行信息

        Args:
            tbl: 事实表，包含所有元数据。默认使用自身数据源。
            dig_level: 向下钻取的深度
            return_pov: 是否返回pov，pov为 :class:`dict` 格式
            expand: 对于未指定的维度，是否展开显示。不展开时将自动作聚合处理。
            **views: 维度名=维度成员 的维度组合

        Returns:
            DataFrame

        """
        if tbl is None:
            tbl = self.fact_tbl.copy()
        else:
            tbl = tbl.copy()

        # 去除decimal_val列
        dig_level = dig_level or {}
        drillable = set(tbl.columns) - {self.data_col}

        need_groupby = False

        pov = {}

        # 当所有的指定维度都筛选完以后，相当于对所有条件进行交集，此时tbl保存的是只包含需要用的到数据
        for dimname, mbr_name in views.items():
            # 取出对应维度树
            dimension = self.dimensions[dimname]
            # 取出对应维度树中的指定维度成员
            mbr = dimension[mbr_name]

            if mbr.is_leaf:  # 叶子节点
                # 针对当前维度的值进行实际表的筛选，并修改加载的事实表
                tbl = tbl.loc[tbl[dimname] == mbr_name]
                pov[dimname] = mbr_name
                # 叶子节点不需要进行钻取
                drillable.remove(dimname)
            else:
                if dimname in dig_level:
                    drill_down = {dimname: dig_level[dimname]}
                else:
                    drill_down = {}
                tbl = self._aggregate_pnode(tbl, dimname, [mbr], drill_down)

        for dimname in drillable - views.keys():
            if not expand:
                tbl = self.agg_single_dim(tbl, dimname, '#root')
                tbl[dimname] = "#ALL#"

        if return_pov:
            return tbl, pov
        return tbl.reset_index(drop=True)

    def aggregate_bottom_up(self, tbl, dimname, top, incl_base=True, incl_top=True):
        """
        Args:
            tbl: 事实表
            dimname: 维度
            top: 顶层聚合节点
            incl_base: 返回的表是否包含叶子节点数据
            incl_top: 返回的表是否包含顶层聚合节点数据
        """
        # 取出聚合节点
        dim = self.dimensions[dimname][top]

        base_names = set(dim.Base.data)

        data = tbl.loc[tbl[dimname].isin(base_names)]
        agg = self.agg_single_dim(data, dimname, top, dig_level=-1, keep_top=True, return_datas=True)
        if not incl_base:
            agg.pop(0)
        if not incl_top:
            agg.pop(-1)
        if not agg:
            return pd.DataFrame()
        return pd.concat(reversed(agg), sort=False)

    def _aggregate_pnode(self, tbl, dimname, pnodes, drilldown=None):
        """
        Args:
            tbl: 事实表
            dimname: 处理的维度
            pnodes: 聚合节点
            drilldown:

        Returns:

        """
        # 连接数据表
        datas = []

        for node in pnodes:
            # 聚合节点的叶子节点
            dim_bases_name = set(node.Base.data)
            # 筛选是聚合节点叶子节点的数据，并复制
            tmp_tbl = tbl.loc[tbl[dimname].isin(dim_bases_name)].copy()
            # 取出聚合节点名
            node_name = node.name

            if dimname in drilldown:
                level, keep_top = drilldown[dimname]
                # 挖掘层的深度
                dig_level = node.depth + level
                """不论挖掘层数有多深，都只会返回最下层的聚合节点，没有叶子节点数据"""
                tmp_tbl = self.agg_single_dim(tmp_tbl, dimname, node_name, keep_top=keep_top, dig_level=dig_level)
            else:
                tmp_tbl = self.agg_single_dim(tmp_tbl, dimname, node_name)
            datas.append(tmp_tbl)
        return pd.concat(datas, sort=False).reset_index(drop=True)

    def agg_single_dim(self, tbl, dim_name, agg_node_name, keep_top=False, dig_level=None, return_datas=False):
        """
        对单一维度进行聚合

        Args:
            tbl: 事实表
            dim_name: 维度名
            agg_node_name: 聚合节点名
            keep_top: 是否保留聚合过程数据
            dig_level: 挖掘层的深度
            return_datas: 是否返回连接表列表格式

        Returns:
            聚合完成的事实表

        """
        dim = self.dimensions[dim_name]

        # 获取当前处理维度的最大深度，空表直接返回
        try:
            max_bases_depth = max([dim[mbr].depth for mbr in tbl[dim_name]])
        except ValueError:
            if dig_level == -1:
                return [tbl]
            return tbl

        # 连接表库
        datas = []
        # 设置挖掘层的深度
        dig_level = dim[agg_node_name].depth if not dig_level else dig_level
        # 挖掘深度多过深，不需要keep_top则直接返回，否则将叶子节点数据加入
        if dig_level == -1 or max_bases_depth <= dig_level:
            if keep_top:
                datas.append(tbl)
            else:
                return tbl

        # 分组列表
        group_by = tbl.columns.drop(self.data_col).tolist()
        # 取出聚合深度
        agg_node_depth = dim[agg_node_name].depth

        def contribute(row):
            node = dim[row[dim_name]]
            # 只针对于当前最大深度的节点进行聚合
            if node.depth == max_bases_depth:
                # 获取节点的权重值和贡献计算函数
                data = node.contribute(row[self.data_col])
                # 每个数据行的维度名应该在cal之后变为其父节点的名字
                row[dim_name] = node.parent[0].name
                # 修改data
                row[self.data_col] = data
                return row
            return row

        def calculate(group):
            # 从相应维度树中取出当前组内的聚合节点
            agg_node = dim[group[dim_name]].members[0]
            # 收集该组中的父节点计算自身data的所有参数，子节点名与其计算出的贡献形成字典
            args = dict(zip(group['Extra'], group[self.data_col]))
            # 向父节点汇聚
            group[self.data_col] = agg_node.calculate(**args)
            # 取出添加的extra行
            return group.iloc[0][:-1]

        # 一直合并直到达到聚合深度
        while max_bases_depth > agg_node_depth:
            # extra列记录计算前维度值
            tbl = tbl.assign(Extra=tbl[dim_name])
            # 事实表按行计算data
            tbl = tbl.apply(contribute, axis=1)
            # 维度分组，将会聚合的数据行分在一起
            tbl = tbl.groupby(group_by, as_index=False, sort=False).apply(calculate)
            # 将当前最大深度减一
            max_bases_depth -= 1
            # 判断当前最大深度是否已经到达挖掘层深度
            if max_bases_depth <= dig_level:
                # 判断是否需要将聚合过程表存储
                if keep_top:
                    datas.append(tbl.copy())
                else:   # 不需要存储时，直接返回当前层的结果即可
                    return tbl
            elif dig_level == -1:   # dig_level==-1时是由IDescendant或者Descendant调来，此时keep_top一定为True
                datas.append(tbl.copy())
        if return_datas:
            return datas
        else:
            return pd.concat(datas, sort=False)

    @property
    def data(self):
        return self._get_full_data(self.fact_tbl)

    def dump(self, folder):
        """
        将cube的事实表和所有维度导出至本地目录

        Args:
            folder: cube数据的存放目录

        """

        if not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)

        data = self.fact_tbl or self.data
        data.assign(**self.pov).to_csv(os.path.join(folder, 'data.csv'), index=False)

        for name, dim in self.dimensions.items():
            if not isinstance(dim, Dimension):
                raise TypeError(f"Dimension type: {type(dim)} is not dumpable.")
            fpath = os.path.join(folder, f"{name}.json")
            dim.to_json(path=fpath)

    def _load_fix_single(self, fix: str) -> pd.DataFrame:
        self.load_expr(fix)
        return self.data

    def _load_fix_data(self, fix_exprs: List[str]) -> pd.DataFrame:
        expr_bak = self.to_expr()
        try:
            datas = [self._load_fix_single(fix) for fix in fix_exprs]
        finally:
            if expr_bak:
                self.load_expr(expr_bak)
            else:
                self.reset_dimensions()
        return pd.concat(datas, sort=False)

