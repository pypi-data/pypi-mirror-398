from collections import deque
from contextlib import contextmanager
from typing import Dict, List, Sequence, Optional, Union, Deque, ContextManager

import numpy as np
import pandas as pd
from loguru import logger

from .formula import CubeFixer, _ConditionWrapper, FormulaContainer
from .typing import TD_Str_ListStr, T_MaybeCondition
from .utils import dict_to_sql, dicts_to_sql, create_df_by_cproduct, Options
from .constants import Instruction
from deepfos.core.dimension import Dimension, SysDimension
from deepfos.lib.decorator import cached_property
from deepfos.lib.utils import ConcealableAttr, MultiKeyDict, unpack_expr, dict_to_expr, expr_to_dict
from deepfos.element.finmodel import FinancialCube


class CalcSet:
    def __init__(self, data_src: pd.DataFrame, drop_cols, cube: 'CubeBase'):
        self.data_col = cube.data_col
        self.__dropped_cols = set(drop_cols)
        self._data_src = data_src
        self.__data_proxy = None
        self._cube_dim_state: TD_Str_ListStr = cube.dim_state.copy()
        self._filters = []
        self._rslt_filter: Dict[str, set] = cube.formulas.left.copy()
        self._cube_expr = cube.to_expr()
        #: 非pov的维度
        self._columns = data_src.columns.difference([self.data_col])
        self._instruction = []
        # cube fix条件对应的dataframe索引
        self._fix_index = None

    def add_instruction(self, instruction: Instruction):
        self._instruction.append(instruction)

    def add_filter(self, fltr):
        self.__data_proxy = None
        self._filters.append(fltr)

    def pop_filter(self):
        self.__data_proxy = None
        self._filters.pop()

    @property
    def data_proxy(self) -> pd.DataFrame:
        # data_src 的代理
        if self.__data_proxy is None:
            self.__data_proxy = self._data_src.copy()
            # self.__data_src_cache = pipe(
            #     map(attrgetter('filter'), self._filters),
            #     self.__data_src)
        return self.__data_proxy

    @cached_property
    def pov(self) -> Dict[str, str]:
        return {
            c: self._cube_dim_state[c][0]
            for c in self.__dropped_cols
        }

    @cached_property
    def pov_str(self) -> str:
        return dict_to_expr(self.pov)

    @property
    def full_data(self) -> pd.DataFrame:
        """包含pov列的完整数据"""
        return self._data_src.assign(**self.pov)

    def pivot(self, dim):
        """把需要计算的维度转移到列上"""
        data = self._data_src
        index_cols = self._columns.difference([dim]).tolist()

        if data.empty:
            self._data_src = data.drop(columns=[dim, self.data_col])
        else:
            data = data.pivot_table(
                index=index_cols, values=self.data_col, columns=dim,
                aggfunc='first', dropna=False, fill_value=np.NaN
            ).reset_index(drop=not index_cols)
            data.columns.name = None
            self._data_src = data

        self._set_fix_index(dim)

    def unpivot(self, dim: str):
        """把计算完成的维度成员转移到行上"""
        data = self._data_src
        index_cols = self._columns.difference([dim]).tolist()
        total_mbr_cols = data.columns.difference(index_cols)
        melted_data = data.melt(
            id_vars=index_cols, value_vars=total_mbr_cols,
            var_name=dim, value_name=self.data_col
        )
        # 去除除零导致的inf数据
        melted_data[np.isinf(melted_data[self.data_col])] = np.NaN
        self._data_src = melted_data.dropna()

    def load_fixes(
        self,
        column: str,
        dimension: str,
        on: Dict[str, Union[Sequence[str], str]],
        name: str,
    ):
        """
        加载需要计算的列，内部调用

        Args:
            column: 当前计算节点对应的数据列
            dimension: 当前计算节点所属维度
            on: 当前计算节点的on条件
            name: 存在on条件时，merge出的column名

        Returns:

        """
        data = self.data_proxy
        on = {
            k: v for k, v in on.items()
            if k not in self.__dropped_cols
        }

        if not on or column not in data.columns:
            return

        # 去除on条件列及自身列后，其余列作为merge on的列
        index_cols = self._columns.difference([*on.keys(), dimension]).tolist()
        # 根据fix条件筛出数据
        fix_sql = dict_to_sql(on, eq='==', bracket=False)
        on_data = data.query(fix_sql)[index_cols + [column]].rename(columns={column: name})
        if not index_cols:
            # 没有index_cols，代表on条件包含了所有维度，原则上应当只有一个数据
            if len(on_data) != 1:
                raise RuntimeError("Cannot proceed calculation due to an unexpected error.")
            self.__data_proxy[name] = on_data[name][0]
        else:
            # 修改data
            self.__data_proxy = data.merge(on_data, on=index_cols, how='left')

    def handle_instruction(
        self,
        column: str,
        dimension: str,
    ):
        if not self._instruction:
            return
        insto = self._instruction.pop(-1)
        if insto is Instruction.cproduct:
            product_cols = self._columns.difference([dimension])
            dim_state = self._cube_dim_state
            idx = pd.MultiIndex.from_product((dim_state[col] for col in product_cols), names=product_cols)
            df_template = pd.Series(np.NaN, index=idx, name=column).to_frame()
            data = self.data.set_index(product_cols.tolist()).combine_first(df_template)
            self.__data_proxy = data.reset_index()

    def __repr__(self):
        return f"POV: {self.pov_str}\nData:\n {self._data_src}"

    def get_submit_data(self, compact=True):
        """
        可能需要提交的计算部分。
        """
        pov = self.pov
        dicts = []

        for dim, mbrs in self._rslt_filter.items():
            dim_states = {**self._cube_dim_state, dim: mbrs}

            for k in pov:
                dim_states.pop(k, None)
            dicts.append(dim_states)

        sql = dicts_to_sql(dicts)
        logger.debug(f"Filter submit data with sql: {sql}")

        if compact:
            return self._data_src.query(sql), pov
        return self.full_data.query(sql)

    def submit(self, cube: FinancialCube):
        """保存计算结果"""
        data, pov = self.get_submit_data(compact=True)
        cube.save(data, pov=pov, data_column=self.data_col)

    def set_value(self, column, value):
        self._data_src.loc[self._fix_index, column] = value
        self.__data_proxy = None

    def _set_fix_index(self, dim):
        fix = {
            k: v for k, v in self._cube_dim_state.items()
            if k != dim and k not in self.__dropped_cols
        }
        if not fix:
            self._fix_index = self.data_proxy.index
        else:
            sql = dict_to_sql(fix, "==", bracket=False)
            self._fix_index = self.data_proxy.query(sql).index


class CubeBase:
    #: cube名
    cube_name: str
    #: cube数据列
    data_col: str
    #: 维度名->维度对象
    dimensions: MultiKeyDict[str, Union[Dimension, SysDimension]]
    #: 计算结果集
    calc_set: Optional[CalcSet]

    def __init__(self, cube_name, data_col, **options):
        self.calc_dim = []  # 需要进行计算的维度
        self.formulas = FormulaContainer(self)  # Cube的筛选条件列表，每个元素都是一个_Condition对象
        self.data_col = data_col  # decimal_val
        self.cube_name = cube_name
        self.dimensions = MultiKeyDict()
        self.calc_set = None
        self._default_option = Options(**options)
        self._option_index = 0

    dim_state: TD_Str_ListStr = ConcealableAttr({})
    option_stack: Deque[Options] = ConcealableAttr(deque())
    """当前维度表达式下的维度状态

    维度名 -> 维度成员列表。
    仅在进入 :meth:`fix` 语句块中时会产生有效值。
    
    仅供内部调用。
    """

    def reset_dimensions(self):
        """清空维度选择的成员

        即所有维度回到未选择成员的状态"""
        for dim in self.dimensions.values():
            if dim.activated:
                dim.clear()

    @property
    def pov(self) -> Dict[str, str]:
        """Point of View

        维度 -> 维度成员。
        在当前维度锁定状态下，维度成员仅一个的维度会被加入至 :attr:`pov`

        See Also:
            | :meth:`load_expr`
            | :meth:`to_expr`

        """
        pov = {}

        for dim in self.dimensions.values():
            if not dim.activated:  # 判断当前维度树是否选择了维度成员
                continue
            if len(data := dim.data) == 1:  # 维度固定，则加入POV中
                pov[dim.name] = data[0]

        return pov

    def to_expr(self) -> str:
        """
        当前的维度锁定状态转化为表达式
        """
        dims_exprs = (dim.to_expr() for dim in self.dimensions.values() if dim.activated)
        return "->".join(dims_exprs)

    def load_expr(self, cube_expr: str):
        """
        读取维度表达式

        会改变维度的锁定状态

        Args:
            cube_expr: 维度表达式

        Returns:
            self

        """
        self.reset_dimensions()

        for dim_expr in cube_expr.split('->'):
            dimname, expr = unpack_expr(dim_expr)
            if dimname not in self.dimensions:
                raise ValueError(f"Given Dimension '{dimname}' doesn't belong to cube.")
            self.dimensions[dimname].load_expr(expr)
        return self

    # -----------------------------------------------------------------------------
    # Cube 成员公式相关
    # noinspection PyUnresolvedReferences
    @contextmanager
    def fix(
        self,
        general_fix: str = None,
        on_dim: str = None,
    ) -> ContextManager[CubeFixer]:
        """
        执行成员公式

        上下文管理器，在fix上下文中可以写成员公式，
        所有计算将在退出fix语句块时执行，
        计算结果将保存在 :attr:`calc_set` 中。

        Args:
            general_fix: 锁定当前维度的维度表达式
            on_dim: 计算成员所属的维度

        """
        if general_fix is not None:
            self.load_expr(general_fix)

        dim_locked = False
        if on_dim is not None and on_dim in self.dimensions:
            self.calc_dim.append(on_dim)
            dim_locked = True

        __class__.dim_state.expose(self)
        __class__.option_stack.expose(self)
        self._dump_dim_state()

        try:
            self.option_stack.append(self._default_option)
            yield CubeFixer(self)
            self.formulas.solve()
        finally:
            if dim_locked:
                self.calc_dim.pop()
            self.dim_state.clear()
            self.option_stack.clear()
            __class__.dim_state.conceal(self)
            __class__.option_stack.conceal(self)

    def make_condition(self, condition: T_MaybeCondition) -> _ConditionWrapper:
        """创建筛选条件，用于成员公式"""
        return _ConditionWrapper(self.formulas, condition)

    def _dump_dim_state(self):
        """导出当前维度的 `fix` 状态

        影响 :attr:`dim_state` 的值，仅在内部使用。
        由于 :attr:`dim_state` 的特性，外部调用可能会直接引发报错。
        """
        for name, dim in self.dimensions.items():
            if dim.activated and (data := dim.data):
                self.dim_state[name] = data

    def _load_fix_data(self, fix_exprs: List[str]) -> pd.DataFrame:
        raise NotImplementedError

    def _load_calc_set(
        self,
        fix_exprs: List[str],
        fix_mbrs: List[TD_Str_ListStr]
    ):
        """
        加载计算集。仅供内部使用。
        """
        drop_cols = self._resolve_drop_cols(fix_mbrs)
        data = self._load_fix_data(fix_exprs).drop(columns=drop_cols)

        dim_columns = data.columns.difference([self.data_col])
        data = data.drop_duplicates(dim_columns)

        col_map = {
            k: v for k, v in self.dim_state.items()
            if k not in drop_cols
        }

        df_tmpls = []
        for dim, mbrs in self.formulas.left.items():
            df_tmpls.append(create_df_by_cproduct({**col_map, dim: mbrs}))

        df_tmpl = pd.concat(df_tmpls).drop_duplicates(dim_columns)
        data = df_tmpl.merge(data, how='outer', on=dim_columns.tolist())
        self.calc_set = CalcSet(data, drop_cols, self)

    def _resolve_drop_cols(self, fixes: List[TD_Str_ListStr]):
        """查找可以在计算中drop的列

        根据所有计算单元的fix条件（包括等号左边）。
        结合顶部的fix条件，获取可以在后续计算中drop的列。

        可以在计算集中移除是只fix了一个成员的维度。

        Args:
            fixes: 所有维度对应的fix成员列表.

        Returns:
            可移除的列名列表

        """
        dim_state = self.dim_state
        candiates = [k for k, v in dim_state.items() if len(v) == 1]

        for dim in candiates[:]:
            for fix in fixes:
                if dim in fix:
                    fix_mbrs = set(fix[dim] + dim_state[dim])
                    if len(fix_mbrs) > 1:
                        candiates.remove(dim)
                        break

        return candiates

    @contextmanager
    def set_options(self, **kwargs):
        """修改cube设置"""
        if not self.option_stack:
            raise RuntimeError("set_options is only allowed within `fix` function.")

        option = self.option_stack[self._option_index].replace(**kwargs)

        try:
            self.option_stack.append(option)
            self.formulas.append(self.option_stack.popleft)
            self._option_index += 1
            yield
        finally:
            self._option_index -= 1


def _get_remap_bottom_up(dimension, bases, top_level=0, drilldown=0):
    """
    获取聚合节点向下挖掘后，挖掘曾的节点名

    Args:
        dimension: 维度对象
        bases: 聚合节点的叶子节点名
        top_level: 聚合节点深度
        drilldown: 向下挖掘的深度

    Returns:
        返回挖掘层的节点名字典

    """
    # 挖掘到的节点深度
    target_level = top_level + drilldown
    # 使用字典存储，是为了去重
    re_map = {}

    for base in bases:
        # 取出每个叶子节点
        node = dimension[base]

        # 叶子节点距挖掘节点的深度差
        up_cnt = node.depth - target_level
        if up_cnt <= 0:
            continue
        node_name = node.name
        while up_cnt > 0:
            node = node.parent
            up_cnt -= 1
        # 向上找到了挖掘节点
        re_map[node_name] = node.name

    return re_map
