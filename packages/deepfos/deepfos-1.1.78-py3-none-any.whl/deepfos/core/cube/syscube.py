import asyncio
from typing import Optional, List, Union, Iterable, Container, Dict, Any, Callable, Set
from enum import Enum, auto
import pandas as pd
from loguru import logger

from ._base import CubeBase, CalcSet
from .constants import NAME_DFLT, PNAME_DFLT, WEIGHT
from .utils import Zero, dict_to_sql
from deepfos.core.dimension import Dimension, SysDimension, DimMember, ElementDimension
from deepfos.api.models.dimension import ElementQueryBaseDto
from deepfos.api.dimension import DimensionAPI
from deepfos.element.finmodel import FinancialCube
from deepfos.lib.constant import DFLT_DATA_COLUMN, VIEW, ROOT, SHAREDMEMBER
from deepfos.lib.utils import get_ignore_case, dict_to_expr, unpack_expr, CIEnum, expr_to_dict
from deepfos.lib.asynchronous import evloop
from deepfos.lib.concurrency import ThreadCtxExecutor

T_IStr = Union[str, Iterable[str]]
T_AggFunc = Callable[
    [pd.DataFrame, DimMember, Container[str], Set[str]],
    Optional[pd.Series]
]


class DimensionType(CIEnum):
    element = 'element'
    lazy = 'lazy'
    complete = 'complete'


class ClearStrategy(Enum):
    recursive = auto()
    non_recursvie = auto()


class SysCube(CubeBase):
    """系统财务Cube

    包含成员公式，自动汇总功能。

    Args:
        cube_name: 财务模型名称
        folder_id: 元素所在的文件夹id
        path: 元素所在的文件夹绝对路径
        fetch_dim: 是否提前获取完整维度树
        extra_dim_attrs: 维度需要额外查询的属性
        data_col: 数据列列名
        use_dim_element: 是否使用维度元素，在仅使用fix功能时，开启此选项会大幅提高性能

    Note:
        :class:`SysCube` 需要在 ``python`` 中解析维度表达式以实现它的一些算法。
        因此在实例化时，会尝试获取所有维度的成员信息。
        为了减少网络及内存开销，默认在查询维度时，只会查询
        ``name, parent_name, aggweight`` 三个属性。这种情况下，
        如果你在 ``fix`` 表达式中使用了 ``ud`` 作为维度的筛选条件，
        例如 ``fix`` 中包含:

            ``Entity{AndFilter(Base(#root,0),Attr(ud1,"WL"))}``

        将导致报错。为了解决上述问题，引入 ``extra_dim_attrs`` 用于指定维度需要额外查询的属性。
        传入如下参数即可：

            .. code-block:: python

                extra_dim_attrs = {
                    "Entity": ["ud1"]
                }

    """
    def __init__(
        self,
        cube_name: str,
        folder_id: str = None,
        path: str = None,
        fetch_dim: bool = True,
        extra_dim_attrs: Dict[str, List[str]] = None,
        data_col: str = DFLT_DATA_COLUMN,
        use_dim_element: bool = False,
        **options
    ):
        super().__init__(cube_name, data_col, **options)

        self.cube = FinancialCube(cube_name, folder_id, path)
        extra_dim_attrs = extra_dim_attrs or {}
        if use_dim_element:
            self.dim_type = DimensionType.element
        elif fetch_dim:
            self.dim_type = DimensionType.complete
        else:
            self.dim_type = DimensionType.lazy

        evloop.run(self._initialize_dimensions(extra_dim_attrs))

    async def _initialize_dimensions(self, extra_dim_attrs):
        cube = self.cube
        jobs = [
            self._dim_init(dim_name, cube, self.dim_type, extra_dim_attrs.get(dim_name, []))
            for dim_name in cube.dim_elements.keys()
        ]
        jobs.append(self._dim_init_view(cube))

        await asyncio.gather(*jobs)

    async def _dim_init(self, dim_name: str, cube: FinancialCube, dim_type: DimensionType, extra_attr: List[str]):
        dim_column = cube.dim_col_map[dim_name]
        dim_element = cube.dim_elements[dim_name]

        if dim_type == DimensionType.complete:
            data = await dim_element.table_dimension.select_raw(
                [NAME_DFLT, PNAME_DFLT, SHAREDMEMBER, WEIGHT] + extra_attr
            )
            dim = Dimension.from_json(dim_name, data, extra_info=extra_attr)
            dim.root.name = ROOT
        elif dim_type == DimensionType.lazy:
            dim = SysDimension(
                dim_name,
                tbl_closure=dim_element.table_closure,
                tbl_dim=dim_element.table_dimension,
                name_only=True
            )
        else:
            dim = ElementDimension(dim_element)

        self.dimensions[dim_name, dim_column] = dim

    async def _dim_init_view(self, cube: FinancialCube):
        """初始化View维度"""
        if not cube._meta.autoCalculation:
            return

        period = get_ignore_case(cube.dimensions, 'Period', None)
        if period is None:
            raise ValueError(
                "Cannot not initialize dimension 'View' because "
                "no dimension named 'Period'.")

        api = await DimensionAPI(module_id=period.moduleId, sync=False)
        view_info = await api.query.get_view_by_period(ElementQueryBaseDto(
            elementName=period.name,
            folderId=period.folderId,
            showAll=True
        ))

        view = Dimension(dim_name=VIEW, root=DimMember(ROOT))
        root = view.root
        for item in view_info:
            view.attach(DimMember(item.name), root)

        self.dimensions[VIEW, VIEW] = view

    def _load_fix_single(self, fix: str) -> pd.DataFrame:
        return self.cube.query(fix, compact=False)

    def submit_calc_result(self):
        """提交计算结果

        将fix上下文中成员公式的计算结果提交至系统。
        会清空计算结果。
        """
        if self.calc_set is None:
            return
        self.calc_set.submit(self.cube)
        self.calc_set: Optional[CalcSet] = None

    def _load_fix_data(self, fix_exprs: List[str]) -> pd.DataFrame:
        return self.cube.queries(fix_exprs, drop_duplicates=False)

    def load_expr(self, cube_expr: str):
        if self.dim_type != DimensionType.element:
            return super().load_expr(cube_expr)
        for dim_expr in cube_expr.split('->'):
            dimname, expr = unpack_expr(dim_expr)
            if dimname not in self.dimensions:
                raise ValueError(f"Given Dimension '{dimname}' doesn't belong to cube.")

            self.dimensions[dimname].load_expr(expr)

        return self

    # -----------------------------------------------------------------------------
    # 聚合逻辑
    def _find_parent_mbrs(
            self,
            dimname: str,
            members: T_IStr,
            strategy: ClearStrategy
    ) -> Dict[str, List[str]]:
        dim = self.dimensions[dimname]
        if isinstance(members, str):
            members = [members]

        parent_mbs = set()
        for mbr in members:
            if strategy is ClearStrategy.recursive:
                if mbr == ROOT:
                    all_mbrs = dim[mbr].Descendant
                else:
                    all_mbrs = dim[mbr].IDescendant
                parent_mbs.update(all_mbrs.where('and', is_leaf=False).data)
            else:
                parent_mbs.add(mbr)

        return {dimname: list(parent_mbs)}

    def _agg_impl(
        self,
        dim2mbr: Dict[str, T_IStr],
        hierarchy: str,
        agg: T_AggFunc,
        fix: str,
        submit: bool,
        clear_strategy: ClearStrategy = None,
    ):
        """汇总函数实现

        因为idescendant和ichildren逻辑太像，
        简单抽出这个实现函数，没有设计。
        """
        fix_as_dict = expr_to_dict(fix)

        def merge_fix(dim: str, mbr: T_IStr):
            if dim in fix_as_dict:
                new_fix = fix_as_dict.copy()
                new_fix.pop(dim)
                fix_str = dict_to_expr(new_fix)
            else:
                fix_str = fix
            return f"{fix_str}->{dict_to_expr({dim: mbr}, hierarchy=hierarchy)}"

        def get_clear_expr(dim: str, mbr: T_IStr):
            expr_dict = self._find_parent_mbrs(dim, mbr, clear_strategy)

            for dimname, expr in fix_as_dict.items():
                if dimname == dim:
                    continue
                dimension = self.dimensions[dimname]
                with dimension.load_expr_temporary(expr):
                    expr_dict[dimname] = dimension.data

            return expr_dict

        if len(dim2mbr) == 1:
            dim, mbr = list(dim2mbr.items())[0]
            expr = merge_fix(dim, mbr)
            data = self.cube.query(expr, compact=False)
            if clear_strategy:
                self.cube.insert_null(get_clear_expr(dim, mbr))
        else:
            exprs = (
                merge_fix(k, v)
                for k, v in dim2mbr.items()
            )
            data = self.cube.queries(exprs, drop_duplicates=True)

            if clear_strategy:
                with ThreadCtxExecutor() as executor:
                    for k, v in dim2mbr.items():
                        executor.submit(self.cube.insert_null, get_clear_expr(k, v))

        if data.empty:
            if not submit:
                return data
            return

        # 用于过滤父节点，即最后要提交的数据
        filter_map = {}
        dim_col_map = self.cube.dim_col_map

        for dim, members in dim2mbr.items():
            if isinstance(members, str):
                members = [members]

            # 维度名需要转化为列名
            filter_key = dim_col_map.get(dim, dim)
            filter_map[filter_key] = pnodes = set()
            for member in members:
                data = self._agg_single(
                    agg, data,
                    self.dimensions[dim], pnodes, member
                )

        query = f"`{self.data_col}` != @Zero  and " + \
            dict_to_sql(filter_map, '==', concat='or', bracket=True)

        logger.debug(f"Filter submit data with condition: {query}")
        save_data = data.query(query, engine='python')
        if not submit:
            return save_data
        return self.cube.save(save_data)

    def _agg_single(
        self,
        agg: T_AggFunc,
        data: pd.DataFrame,
        dimension: Dimension,
        parent_nodes: Set[str],
        from_member: str = ROOT,
    ) -> pd.DataFrame:
        """单维度聚合

        Args:
            agg: 聚合函数
            data: cube数据
            dimension: 聚合维度
            parent_nodes: 空集合，存储聚合过程中产生的父节点
            from_member: 聚合的目标成员
        """
        pivot_col = self.cube.dim_col_map[dimension.name]
        index_cols = data.columns.difference({DFLT_DATA_COLUMN, pivot_col}).tolist()

        data = data.pivot_table(
            index=index_cols, values=DFLT_DATA_COLUMN,
            columns=pivot_col, aggfunc='first', fill_value=Zero
        ).reset_index()

        mbr_cols = data.columns.difference(index_cols)
        # inplace 聚合data
        agg(data, dimension[from_member], mbr_cols, parent_nodes)

        # ---------------------------- unpivot ----------------------------------
        # 有新增的父节点列，需要更新
        total_mbr_cols = data.columns.difference(index_cols)
        data = data.melt(
            id_vars=index_cols, value_vars=total_mbr_cols,
            var_name=pivot_col, value_name=DFLT_DATA_COLUMN
        )
        return data

    def _agg_top_down(
        self,
        data: pd.DataFrame,
        mbr: DimMember,
        valid_cols: Container[str],
        parent_nodes: Set[str],
    ) -> Optional[pd.Series]:
        """自顶向下递归聚合父节点

        Important:
            这段代码的执行顺序很重要，不要乱改。
            自定义Zero用于处理不存在数据的成员，避免算出多余的0
        """
        name = mbr.name

        if mbr.is_leaf:
            if name in valid_cols:
                return data[name]
            else:
                return Zero

        # 算过的共享节点不需要再次计算
        if name in parent_nodes:
            logger.debug(f"Skip member: {name}. As it has been calculated.")
            return data[name]

        series = [
            self._agg_top_down(data, child, valid_cols, parent_nodes)
            *
            getattr(child, WEIGHT, 1.0)
            for child in mbr.children
        ]
        # root节点应该隐藏
        if mbr.is_root:
            return

        sum_ = sum(series, Zero)
        if sum_ is not Zero:
            data[name] = sum_
            parent_nodes.add(name)
        return sum_

    def idescendant(
        self,
        fix: str,
        dimensions: Union[T_IStr, Dict[str, T_IStr]],
        submit: bool = True,
        clear_agg_nodes: bool = False,
    ) -> Union[pd.DataFrame, Any]:
        """递归汇总维度

        根据维度表达式确定的数据范围、以及需要汇总的维度和成员。
        按顺序递归汇总所有目标节点下的非叶子节点。

        Args:
            fix: 维度表达式，确定汇总涉及的数据范围
            dimensions: 需要汇总的维度
            submit: 是否将汇总结果直接入库
            clear_agg_nodes: 是否在保存前先删除汇总节点的数据

        Hint:
            入参 ``dimension`` 支持三种格式

            - :obj:`str` : 维度名称，表示汇总至该维度的根节点
            - :obj:`Iterable[str]` : 多个维度名称，表示按顺序进行汇总，汇总至根节点
            - :obj:`Dict` : 维度名称 -> 维度成员(可多个)，表示按顺序汇总到指定的单个或多个成员

        Important:
            - 对于 ``fix`` 中没有出现的维度，会以 ``Base(#root,0)`` 自动补全表达式。
            - 最终保存的数据将只包含本次参与汇总的父节点，叶子（Base）节点不会参与保存。

        .. admonition:: 示例

            .. code-block:: python

                fix = 'Year{2021;2022}->Entiy{Base(TotalEntity,0)}'
                cube = SysCube('example')
                # 汇总至Account维度根节点
                cube.idescendant(fix, 'Account')
                # 依次汇总Account维度，Version维度至根节点
                cube.idescendant(fix, ['Account', 'Version'])
                # 先汇总Account至CostA, CostB，再汇总Version维度至Version1
                cube.idescendant(fix, {
                    'Account': ['CostA', 'CostB'],
                    'Version': 'Version1'
                })

        Returns:
            - 如果不提交汇总结果，将返回汇总结果，无汇总数据返回空 :obj:`DataFrame`
            - 如果提交汇总结果，将返回数据保存结果，无汇总数据返回 :obj:`None`

        See Also:
            如果不需要递归汇总，请使用 :meth:`ichildren`

        """
        if self.dim_type != DimensionType.complete:
            raise RuntimeError(
                "Failed to call 'idescendant' because dimension tree "
                "is not properly fetched. Set `fetch_dim=True` "
                "while instantiate a SysCube.")

        if isinstance(dimensions, dict):
            dim2mbr = dimensions
        elif isinstance(dimensions, str):
            dim2mbr = {dimensions: ROOT}
        else:
            dim2mbr = {dim: ROOT for dim in dimensions}

        return self._agg_impl(
            dim2mbr,
            'Base',
            self._agg_top_down,
            fix,
            submit,
            clear_strategy=ClearStrategy.recursive if clear_agg_nodes and submit else None
        )

    # noinspection PyMethodMayBeStatic
    def _agg_children(
        self,
        data: pd.DataFrame,
        mbr: DimMember,
        valid_cols: Container[str],
        parent_nodes: Set[str],
    ) -> Optional[pd.Series]:
        """聚合父节点"""
        if mbr.is_root:
            raise RuntimeError("Cannot execute ichildren for root member.")

        series = []

        for child in mbr.children:
            if (cname := child.name) in valid_cols:
                series.append(data[cname] * getattr(child, WEIGHT, 1.0))
            else:
                series.append(Zero)

        sum_ = sum(series, Zero)
        if sum_ is not Zero:
            data[mbr.name] = sum_
            parent_nodes.add(mbr.name)
        return sum_

    def ichildren(
        self,
        fix: str,
        dimensions: Dict[str, T_IStr],
        submit: bool = True,
        clear_agg_nodes: bool = False,
    ) -> Union[pd.DataFrame, Any]:
        """维度自动汇总

        根据维度表达式确定的数据范围、以及需要汇总的维度和成员。
        按顺序汇总所有目标节点。汇总依据仅为目标节点的子节点，
        如果子节点无数据，则不触发汇总，不会递归向下寻找叶子节点。

        Args:
            fix: 维度表达式，确定汇总涉及的数据范围
            dimensions: 需要汇总的维度
            submit: 是否将汇总结果直接入库
            clear_agg_nodes: 是否在保存前先删除汇总节点的数据

        Hint:
            入参 ``dimension`` 需符合格式：
                维度名称 -> 维度成员(可多个)，表示按顺序汇总到指定的单个或多个成员

        Important:
            - 对于 ``fix`` 中没有出现的维度，会以 ``Base(#root,0)`` 自动补全表达式。
            - 最终保存的数据将只包含本次参与汇总的父节点。

        .. admonition:: 示例

            .. code-block:: python

                fix = 'Year{2021;2022}->Entiy{Base(TotalEntity,0)}'
                cube = SysCube('example')
                # 先汇总Account至CostA, CostB，再汇总Version维度至Version1
                cube.ichildren(fix, {
                    'Account': ['CostA', 'CostB'],
                    'Version': 'Version1'
                })

        Returns:
            - 如果不提交汇总结果，将返回汇总结果，无汇总数据返回空 :obj:`DataFrame`
            - 如果提交汇总结果，将返回数据保存结果，无汇总数据返回 :obj:`None`

        See Also:
            如果需要递归汇总，请使用 :meth:`idescendant`
        """
        if self.dim_type != DimensionType.complete:
            raise RuntimeError(
                "Failed to call 'ichildren' because dimension tree "
                "is not properly fetched. Set `fetch_dim=True` "
                "while instantiate a SysCube.")

        return self._agg_impl(
            dimensions,
            'Children',
            self._agg_children,
            fix,
            submit,
            clear_strategy=ClearStrategy.non_recursvie if clear_agg_nodes and submit else None
        )
