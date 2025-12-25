import asyncio
import re
from enum import Enum
from itertools import chain
from typing import (
    List, Dict, Optional, Union,
    Tuple, Iterable, TYPE_CHECKING, Any, Set, Literal
)

import numpy as np
import pandas as pd
from pydantic import Field
from loguru import logger
import datetime
from multidict import MultiDict

from deepfos.api.models import compat_parse_obj_as as parse_obj_as
from .base import ElementBase, SyncMeta
from .dimension import AsyncDimension, Dimension
from .datatable import (
    DataTableClickHouse, AsyncDataTableClickHouse, get_table_class,
    AsyncDataTableMySQL, DataTableMySQL, T_DatatableInstance, T_AsyncDatatableInstance
)
from deepfos.api.app import AppAPI
from deepfos.lib.asynchronous import future_property
from deepfos.lib.utils import (
    unpack_expr, dict_to_expr, LazyDict, expr_to_dict,
    dict_to_sql, find_str, concat_url, CIEnumMeta, ChunkAlert,
    split_dataframe_alert,
)
from deepfos.lib.sysutils import complete_cartesian_product
from deepfos.lib.constant import (
    DFLT_DATA_COLUMN, VIEW, VIEW_DICT,
    HIERARCHY, DECIMAL_COL, STRING_COL,
    DFLT_COMMENT_COLUMN, COLUMN_USAGE_FIELD,
    USED_FOR_COMMENT, USED_FOR_DATA
)
from deepfos.boost import pandas as bp
from deepfos.api.financial_model import FinancialModelAPI
from deepfos.api.models.financial_model import (
    FinancialModelDto as CubeModel,
    CubeQueryForOutVo, ReactSpreadsheetSaveForm,
    SpreadsheetSingleData, ResultObj,
    PcParams, CopyCalculateDTO,
    TaskExecutionParam,
    ParameterDefineDto,  # noqa
    FinancialDataDto,
    SyncClearDataDto,
)
from deepfos.api.models.base import BaseModel
from deepfos.options import OPTION
from deepfos.lib.decorator import cached_property
from deepfos.exceptions import MDXExecuteTimeout, MDXExecuteFail

__all__ = [
    'AsyncFinancialCube',
    'FinancialCube',
    'RoundType',
]


# -----------------------------------------------------------------------------
# utils
def is_valid_pov(body: str):
    """维度表达式花括号内是否可以转化为pov"""
    return not (';' in body or '(' in body)


def need_query(body: str):
    return "(" in body


# -----------------------------------------------------------------------------
# models
TypeDimensionExpr = Union[str, Dict[str, Union[List[str], str]]]


class Description(BaseModel):
    zh_cn: Optional[str] = Field(None, alias='zh-cn')
    en: Optional[str] = None


class DimensionInfo(BaseModel):
    name: str
    dimensionType: int
    id: str
    moduleId: str
    table_closure: str
    table_dimension: str
    description: Description = Field(None, alias='multilingual')
    folderId: str


class CubeInfo(BaseModel):
    cubeFolderId: str
    cubeName: str


class DataTableInfo(BaseModel):
    name: str
    actual_name: str


class MDXVariableParameter(ParameterDefineDto):
    type: int = 0


class MDXCubeParameter(ParameterDefineDto):
    type: int = 1


class RoundType(int, Enum, metaclass=CIEnumMeta):
    """小数位数保留类型"""
    #: 去尾法
    floor = 0
    #: 进一法
    ceil = 1
    #: 四舍五入
    round = 2


_RE_USE_SECTION = re.compile(r'.*USE\s+\w+;', re.I | re.S)

# 可直接转为mdx member或简单集合函数方法的维度表达式
# 维度名由字母数字下划线和中划线组成，或者等于#root
_RE_SIMPLE_EXPR = re.compile(
    r'(?P<hierarchy>i?(base|descendant|children))'
    r'\s*\((?P<mbr>(\x23root)|([\w\.\-\[\]]+))\s*,'
    r'\s*[01]\s*(,\s*(?P<with_parent>[01])\s*)?\)',
    re.I
)
RE_NAME_WITH_PARENT = re.compile(r'\[(.+)]\.\[(.+)]')


# -----------------------------------------------------------------------------
# core classes
class AsyncFinancialCube(ElementBase[FinancialModelAPI]):
    """财务模型

    Args:
        entry_object: 数据来源名模板，支持替换的字段为脚本元素名称或脚本全名，默认为python
        entry_mode: 数据来源类型，影响显示的icon，默认为1
            1: Python
            2: 电子表格
            3: 可视化计算脚本
            4: 数据流3.0

    Note:

        例如当前脚本元素名为demo，则如下初始化方式可在保存时，显示数据来源将为 ``Script for: demo``

        .. code-block:: python

            cube = FinancialCube(
                element_name='test_cube', 
                entry_object='Script for: {script_name}'
            )

        entry_object的自定义命名逻辑实际实现：

        通过 .format 将 full_name 替换为 ``OPTION.general.task_info['script_name']``，
        将 ``script_name`` 替换为 full_name 被'.' split 后的最后一个名称

        本地测试时，可通过增加如下语句为OPTION.general.task_info赋值

        .. code-block:: python

            from deepfos.options import OPTION

            OPTION.general.task_info = {'script_name': 'python.tt', 'task_id': ''}

        其中的值可以通过在平台上运行如下得到：

        .. code-block:: python

            print(OPTION.general.task_info)


    """
    def __init__(
        self,
        element_name: str,
        folder_id: Optional[str] = None,
        path: Optional[str] = None,
        entry_object='python',
        entry_mode=1,
        server_name: Optional[str] = None,
        before_chunk: ChunkAlert = None,
        after_chunk: ChunkAlert = None,
    ):
        full_name = OPTION.general.task_info.get('script_name', 'python')
        self.entry_object = entry_object.format(script_name=full_name.split('.')[-1],
                                                full_name=full_name)
        self.entry_mode = entry_mode
        self.before_chunk = before_chunk
        self.after_chunk = after_chunk
        super().__init__(element_name, folder_id, path, server_name)

    @future_property(on_demand=True)
    async def meta(self) -> CubeModel:
        """财务Cube的元数据信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.cube.data(
            cubeName=self.element_name,
            folderId=ele_info.folderId,
        )

    @future_property
    async def _meta(self) -> FinancialDataDto:
        """财务Cube的元数据信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.cube.find_cube_data(
            cubeName=self.element_name,
            folderId=ele_info.folderId,
        )

    @cached_property
    def dimensions(self) -> Dict[str, DimensionInfo]:
        """财务Cube的维度信息"""
        dim_memo = {}
        for dim in self.meta.dimensions:
            dim_info = parse_obj_as(DimensionInfo, dim["dimensionInfo"])
            dim_memo[dim_info.name] = dim_info

        return dim_memo

    @cached_property
    def account_col(self) -> str:
        for dim in self._meta.cubeDimensionList:
            if dim.dimensionUsage == 4:
                return dim.datatableColumn

    @cached_property
    def dim_elements(self) -> LazyDict[str, AsyncDimension]:
        """财务Cube的维度元素

        维度名 -> 维度元素的字典，延迟初始化，
        只会在使用时创建维度元素
        """
        dims = LazyDict[str, AsyncDimension]()
        for dim in self._meta.cubeDimensionList or []:
            if dim.dimensionName is None:
                continue
            dims[dim.dimensionName] = (
                AsyncDimension,
                dim.dimensionName,
                dim.dimensionFolderId,
                dim.dimensionPath,
                False,
                dim.dimensionServerName,
            )
        return dims

    @cached_property
    def dim_col_map(self) -> MultiDict[str]:
        """维度名 -> 数据列名的字典"""
        dc_map = MultiDict[str]()

        for dim in self._meta.cubeDimensionList:
            if dim.dimensionName is not None:
                dc_map.add(dim.dimensionName, dim.datatableColumn)
        return dc_map

    @cached_property
    def col_dim_map(self) -> Dict[str, str]:
        """数据列名 -> 维度名的字典"""
        return {
            dim.datatableColumn: dim.dimensionName
            for dim in self._meta.cubeDimensionList
            if dim.dimensionName is not None
        }

    @cached_property
    def fact_table(self) -> T_AsyncDatatableInstance:
        """事实表对应的数据表"""
        table_info = self._meta.datatable
        init_args = dict(
            element_name=table_info.name,
            folder_id=table_info.folderId,
            path=table_info.path,
            table_name=table_info.actualTableName,
            server_name=self._meta.datatableServerName
        )
        if (server_name := self._meta.datatableServerName) is None:
            if self._meta.dataSync == 1:
                return AsyncDataTableClickHouse(**init_args)
            else:
                return AsyncDataTableMySQL(**init_args)

        return get_table_class(server_name, sync=False)(**init_args)

    def _split_expr(
        self,
        cube_expr: str,
        pov: Dict[str, str],
        default_hierarchy: str = 'Base',
        validate_expr: bool = True,
    ) -> Tuple[str, Dict[str, str]]:
        """解析维度表达式和pov

        取出维度表达式中的pov部分和当前pov合并，
        返回完整的表达式及pov
        """
        full_pov = {**pov}
        exprs = []

        if validate_expr:
            get_colname = self._get_column_from_dim
            all_cols = set(self.dim_col_map.values())
        else:
            get_colname = lambda x: x
            all_cols = set()

        cols_appeared = set(pov.keys())
        for expr in cube_expr.split('->'):
            dim, body = unpack_expr(expr)
            dim = get_colname(dim)
            cols_appeared.add(dim)
            if is_valid_pov(body):
                full_pov[dim] = body
            else:
                exprs.append(expr)

        if validate_expr and self._meta.autoCalculation and VIEW not in cols_appeared:
            raise ValueError(f"Missing dimension: '{VIEW}' in expression and pov.")

        if default_hierarchy not in HIERARCHY:
            raise ValueError(
                f"Unknown hirerachy: {default_hierarchy}. "
                f"Supported hierarchies are {list(HIERARCHY.values())}")

        hierarchy = HIERARCHY[default_hierarchy]
        exprs += [
            "%s{%s(#root,0)}" % (dim, hierarchy)
            for dim in all_cols - cols_appeared
        ]
        return '->'.join(exprs), full_pov

    def _get_column_from_dim(self, dim: str) -> str:
        """把维度名转化为数据表列名"""
        dc_map = self.dim_col_map
        if dim in dc_map.values():
            return dim
        if dim in dc_map:
            return dc_map[dim]
        if self._meta.autoCalculation and dim in VIEW_DICT:
            return VIEW_DICT[dim]

        raise ValueError(f"Dimension: '{dim}' does not belong to cube: '{self.element_name}'.")

    def _maybe_get_column_from_dim(self, dim: str) -> str:
        try:
            return self._get_column_from_dim(dim)
        except ValueError:
            return dim

    def _resolve_pov_as_dict(
        self,
        pov: Union[str, Dict[str, str]],
        reslove_dim: bool = True,
    ) -> Dict[str, str]:
        """把pov转换为字典格式"""
        if not pov:
            return {}

        new_pov = {}
        if reslove_dim:
            get_colname = self._get_column_from_dim
        else:
            get_colname = lambda x: x

        def set_pov(dim, body):
            if not is_valid_pov(body):
                raise ValueError(f"Cannot convert expression: '{body}' to pov.")
            new_pov[get_colname(dim)] = body

        if isinstance(pov, str):
            for expr in pov.split('->'):
                set_pov(*unpack_expr(expr))
        else:
            for k, v in pov.items():
                set_pov(k, v)
        return new_pov

    async def query(
        self,
        expression: str,
        pov: Optional[Union[str, Dict[str, str]]] = None,
        compact: bool = True,
        pivot_dim: Optional[str] = None,
        validate_expr: bool = True,
        verify_access: bool = False,
        include_ignored: bool = False,
        normalize_view: bool = False,
        pivot_members: List[str] = None,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Dict[str, str]]]:
        """
        根据维度表达式以及pov获取cube数据

        Args:
            expression: 维度表达式
            pov: Point Of View，维度表达式或者KV键值对格式，仅取一个维度成员。
            compact: 是否将pov与查询数据分开输出以减少数据量
            pivot_dim: 需要pivot的维度，将该维度的成员pivot到列上
            validate_expr: 是否需要python校验/修改表达式，开启可能会导致额外的接口请求
            verify_access: 是否带权限查询
            include_ignored: 包含多版本实体维时，是否在结果中包含无效数据(即i列为1的数据)
            normalize_view: 是否把大小写View统一成"View"
            pivot_members: 如有透视维度，可指定透视成员列表，在透视列成员不存在时补全列

        .. admonition:: 示例

            .. code-block:: python
                :emphasize-lines: 3,4

                expr = 'Year{2021;2022}->Entiy{Base(TotalEntity,0)}'
                cube = FinancialCube('example')
                data, pov = cube.query(expr)
                data = cube.query(expr, compact=False)

            **注意最后2行的区别！**


        Important:
            如果开启 ``validate_expr`` ，入参中的维度表达式（expression）
            将能够同时支持维度名和维度在事实表的数据列列名。
            但由于方法内部依赖的财务模型HTTP接口只支持数据列名，所以目前返回的
            ``DataFrame`` 的列名将与数据列列名保持一致。

        Returns:
            如果 ``compact=True`` (默认)，返回 ``(DataFrame, dict)``
            格式的二元组，其中 ``DataFrame`` 为查询的主数据， ``dict`` 部分是pov

            如果指定 ``compact=False`` ，则会将pov部分的数据复制到主数据中，
            只返回一个 ``DataFrame``

        """
        pov = self._resolve_pov_as_dict(pov, validate_expr)
        expression, full_pov = self._split_expr(
            expression, pov, validate_expr=validate_expr
        )
        pov_expr = dict_to_expr(full_pov)

        if not expression:  # only pov
            expression, pov_expr = pov_expr, expression
            full_pov = {}

        query_info = CubeQueryForOutVo(
            cubeName=self.element_name,
            folderId=self.element_info.folderId,
            needAccess=verify_access,
            commonScript=pov_expr,
            script=expression
        )
        logger.debug(f"Query cube with expression: {expression}, pov: {pov_expr}")
        rslt = await self.async_api.data.query(query_info)
        data = pd.DataFrame(rslt['data'])

        # i列为无效列
        if 'i' in data.columns and not include_ignored:
            data = data[data['i'] != 1]
            data = data.drop(columns=['i'])

        if data.empty:
            columns = [*expr_to_dict(expression).keys(), DFLT_DATA_COLUMN]
            data = pd.DataFrame(columns=columns)
            data[DFLT_DATA_COLUMN] = data[DFLT_DATA_COLUMN].astype(float)

        if normalize_view:
            if (view := VIEW.lower()) in data.columns:
                if VIEW in data.columns:
                    data[view] = np.where(data[VIEW].isnull(), data[view], data[VIEW])
                    data = data.drop(columns=[VIEW])
            data = data.rename(columns=VIEW_DICT)

        if pivot_dim is not None:
            pivot_col = self._get_column_from_dim(pivot_dim)
            has_mbrs = isinstance(pivot_members, list)
            if has_mbrs and any(not isinstance(c, str) for c in pivot_members):
                raise ValueError(
                    f"Pivot members must be a list of string, got: {pivot_members}"
                )
            if pivot_col in full_pov:
                val = full_pov.pop(pivot_col)
                if not has_mbrs or val in pivot_members:
                    data = data.rename(columns={DFLT_DATA_COLUMN: val})
                else:
                    data = data.drop(columns=[DFLT_DATA_COLUMN])
            elif pivot_col not in data.columns:
                raise ValueError(
                    f"Pivot dimension: {pivot_dim} does not "
                    f"belong to cube: {self.element_name}.")
            elif data.empty:
                data = data.drop(columns=[pivot_col, DFLT_DATA_COLUMN])
            else:
                index = data.columns.difference({DFLT_DATA_COLUMN, pivot_col}).tolist()
                drop_index = not index

                data = data.pivot_table(
                    index=index, values=DFLT_DATA_COLUMN,
                    columns=pivot_col, aggfunc='first', fill_value=None
                ).reset_index(drop=drop_index)
                data.columns.name = None
                if has_mbrs:
                    data = data.drop(columns=filter(
                        lambda c: c not in pivot_members and c not in index,
                        data.columns
                    ))
            if has_mbrs:
                mbr_assigns = {m: None for m in pivot_members if m not in data.columns}
                data = data.assign(**mbr_assigns)
        if not compact:
            return data.assign(**full_pov)
        return data, full_pov

    def _build_dataframe_for_save(
        self,
        data: pd.DataFrame,
        pov: Optional[Union[str, Dict[str, str]]] = None,
        data_column: str = DFLT_DATA_COLUMN,
        comment_column: str = DFLT_COMMENT_COLUMN,
    ) -> Tuple[pd.DataFrame, Dict[str, str]]:
        if data.empty:
            logger.info("Will not save to cube because dataframe is empty.")
            return pd.DataFrame(), {}

        if data_column not in data.columns:
            raise ValueError(f"Missing data column: {data_column}.")

        # set data column
        if data_column != DFLT_DATA_COLUMN:
            data = data.rename(columns={data_column: DFLT_DATA_COLUMN})

        # set comment column
        if comment_column != DFLT_COMMENT_COLUMN:
            data = data.rename(columns={comment_column: DFLT_COMMENT_COLUMN})

        # convert pov to dict
        pov = self._resolve_pov_as_dict(pov)
        # rename dimension columns to datatable columns
        data = data.rename(columns=self._maybe_get_column_from_dim)
        # check if all dimensions are presented
        required_cols = set(self.dim_col_map.values()).\
            union({DFLT_DATA_COLUMN}).difference(pov.keys())

        if self._meta.autoCalculation:
            # add column "view/View" to required columns
            if VIEW in data.columns:
                required_cols.add(VIEW)
            elif not find_str(VIEW, pov, ignore_case=True):
                raise ValueError(f"Missing column: '{VIEW}' in dataframe.")

        if missing_dims := required_cols - set(data.columns):
            raise ValueError(
                f"Cannot save data because following columns are missing: {missing_dims}"
            )

        # include comment col if provided
        if DFLT_COMMENT_COLUMN in data:
            # use cmt col as data col for cmt data
            cmt_data = data.drop(columns=[DFLT_DATA_COLUMN]).rename(
                columns={DFLT_COMMENT_COLUMN: DFLT_DATA_COLUMN}
            )
            cmt_data = cmt_data.assign(**{COLUMN_USAGE_FIELD: USED_FOR_COMMENT})

            data = data.drop(columns=[DFLT_COMMENT_COLUMN]).assign(
                **{COLUMN_USAGE_FIELD: USED_FOR_DATA}
            )
            data = pd.concat([data, cmt_data])
            required_cols.add(COLUMN_USAGE_FIELD)

        return data[list(required_cols)], pov

    async def save(
        self,
        data: pd.DataFrame,
        pov: Optional[Union[str, Dict[str, str]]] = None,
        data_column: str = DFLT_DATA_COLUMN,
        need_check: bool = True,
        data_audit: bool = True,
        chunksize: Optional[int] = None,
        callback: bool = True,
        comment_column: str = DFLT_COMMENT_COLUMN,
        auth_mode: Literal[0, 1, 2, 3] = 0,
    ):
        """
        将DataFrame的数据保存至cube。

        Args:
            data: 需要保存的数据
            pov: Point Of View，维度表达式或者KV键值对格式。
            data_column: 数据列的列名
            need_check: 是否需要java接口校验脏数据
            data_audit: 是否需要记录到数据审计
            chunksize: 单次调用保存接口时最大的dataframe行数。
              当data的行数超过此值时，将会分多次进行保存。
            callback: 是否回调
            comment_column: 备注列的列名，默认为VirtualMeasure_220922
            auth_mode: 数据保存权鉴模式，默认为0，模式对应如下:
                - 0: 继承财务模型权鉴模式
                - 1: 宽松模式
                - 2: 严格模式
                - 3: 普通模式

        Note:
            此方法会对落库数据做以下处理：

            - 列名重命名：维度名->数据表列名
            - 忽略多余数据列

        See Also:
            :meth:`save_unpivot`
            :meth:`complement_save`
            :meth:`complement_save_unpivot`

        """
        data, pov = self._build_dataframe_for_save(data, pov, data_column, comment_column)
        if data.empty:
            return

        return await self._save_impl(
            data, pov, need_check, data_audit, chunksize, callback, auth_mode
        )

    def _complement(
        self,
        data: pd.DataFrame,
        expression: str,
        default_hierarchy: str = 'Base',
        pov: Dict[str, str] = None,
    ):
        if isinstance(expression, dict):
            expression = dict_to_expr(expression)
        expr, pov = self._split_expr(expression, pov or {}, default_hierarchy)
        full_expr = {**expr_to_dict(expr), **pov}
        folders = {col: dim.folderId for col, dim in self.dimensions.items()}
        data_comp = complete_cartesian_product(
            full_expr,
            data,
            folder_ids=folders,
            col_dim_map=self.col_dim_map,
        )
        return data_comp

    async def complement_save(
        self,
        data: pd.DataFrame,
        expression: Union[str, Dict[str, Union[List[str], str]]],
        default_hierarchy: str = "Base",
        pov: Optional[Union[str, Dict[str, str]]] = None,
        data_column: str = DFLT_DATA_COLUMN,
        comment_column: str = DFLT_COMMENT_COLUMN,
        **kwargs
    ):
        """覆盖指定维度范围并保存数据

        相比于 :meth:`save` ，在保存前，会将`data`按照`expression`补全笛卡尔积。
        并且不在`data`范围的数据以`None`填充

        Note:
            逻辑上等价于两次调用

            .. code-block:: python

                cube.delete(expression)
                cube.save(data, pov, data_column, comment_column, **kwargs)

        Args:
            data: 需要保存的数据
            expression: 需要覆盖的范围（维度表达式）
            default_hierarchy: 当expression中没指定对应维度时，默认取的层级函数，
                即填充为 `default_hierarchy(#root,0)`
            pov: Point Of View，维度表达式或者KV键值对格式。
            data_column: 数据列的列名
            comment_column: 备注列的列名，默认为VirtualMeasure_220922
            **kwargs: 其他可传给 :meth:`save`的参数

        See Also:
            :meth:`save`
            :meth:`save_unpivot`
            :meth:`complement_save_unpivot`

        """
        if not self._backend_del_availiable:
            return await self._legacy_complement_save(
                data=data,
                expression=expression,
                default_hierarchy=default_hierarchy,
                pov=pov,
                data_column=data_column,
                comment_column=comment_column,
                **kwargs
            )

        await self.delete(
            expression,
            data_audit=False,
            default_hierarchy=default_hierarchy
        )
        await self.save(
            data=data,
            pov=pov,
            data_column=data_column,
            comment_column=comment_column,
            **kwargs,
        )


    async def _legacy_complement_save(
        self,
        data: pd.DataFrame,
        expression: Union[str, Dict[str, Union[List[str], str]]],
        default_hierarchy: str = "Base",
        pov: Optional[Union[str, Dict[str, str]]] = None,
        data_column: str = DFLT_DATA_COLUMN,
        comment_column: str = DFLT_COMMENT_COLUMN,
        **kwargs
    ):
        data, pov = self._build_dataframe_for_save(data, pov, data_column, comment_column)
        if data.empty:
            return

        data_comp = self._complement(data, expression, default_hierarchy, pov)
        return await self._save_impl(data_comp, pov, **kwargs)

    def _build_dataframe_for_save_unpivot(
        self,
        data: pd.DataFrame,
        unpivot_dim: str,
        pov: Optional[Union[str, Dict[str, str]]] = None,
        save_nan: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, str]]:
        if data.empty:
            logger.info("Will not save to cube because dataframe is empty.")
            return pd.DataFrame(), {}

        data = data.rename(columns=self._maybe_get_column_from_dim)
        dim = self._get_column_from_dim(unpivot_dim)
        pov = self._resolve_pov_as_dict(pov)
        data_cols = set(data.columns)
        unpivot_cols = data_cols.difference(pov.keys(), self.dim_col_map.values())
        if self._meta.autoCalculation:
            unpivot_cols.discard(VIEW)
        id_cols = data_cols - unpivot_cols
        data = data.melt(
            id_vars=id_cols, value_vars=unpivot_cols,
            var_name=dim, value_name=DFLT_DATA_COLUMN
        )
        if not save_nan:
            data = data.dropna()
            if data.empty:
                logger.info("Will not save to cube because dataframe is empty.")
                return pd.DataFrame(), {}
        return data, pov

    async def save_unpivot(
        self,
        data: pd.DataFrame,
        unpivot_dim: str,
        pov: Optional[Union[str, Dict[str, str]]] = None,
        need_check: bool = True,
        data_audit: bool = True,
        chunksize: Optional[int] = None,
        save_nan: bool = False,
        callback: bool = True
    ):
        """保存有某个维度所有成员在列上的 ``DataFrame``

        为了方便后续计算，在调用 :meth:`query` 时，经常会指定
        ``povit_dim='Account'`` 把科目维度成员转到列上，
        此方法可以方便地保存这类 ``DataFrame`` 。如果使用
        :meth:`save`，则需要使用者重新把科目列转到行上。

        Args:
            data: 需要保存的数据
            unpivot_dim: 成员在列上的维度
            pov: Point Of View，维度表达式或者KV键值对格式。
            need_check: 是否需要java接口校验脏数据
            data_audit: 是否需要记录到数据审计
            chunksize: 单次调用保存接口时最大的dataframe行数。
              当data的行数超过此值时，将会分多次进行保存。
            save_nan: 当把数据列成员转换到行上时，data为空的数据是否保存
            callback: 是否回调

        Warnings:
            由于数据完整性等原因，此方法接收的dataframe数据列经常会有一些额外的空值。
            这些空值一般由计算带入，你并不希望保存它们，因此 ``save_nan`` 默认值为
            ``False`` 。假如你确实需要保存nan值，请显式声明 ``save_nan=True``，
            注意，这实际会删除对应单元格的数据！

        Note:
            出于性能考虑，此方法并不会查询 ``unpivot_dim`` 维度的所有成员，
            在保存的data中除去cube的所有维度后，剩下的数据列都会被认为是属于
            ``unpivot_dim`` 维度的，因此为了确保正常保存且不引入垃圾数据，
            使用者需要保证传入的dataframe不含有多余数据列。

        See Also:
            | :meth:`query`
            | :meth:`save`

        """
        data, pov = self._build_dataframe_for_save_unpivot(
            data, unpivot_dim, pov, save_nan
        )
        if data.empty:
            return

        return await self._save_impl(
            data, pov, need_check, data_audit, chunksize, callback
        )

    async def complement_save_unpivot(
        self,
        data: pd.DataFrame,
        unpivot_dim: str,
        expression: Union[str, Dict[str, Union[List[str], str]]],
        default_hierarchy: str = "Base",
        pov: Optional[Union[str, Dict[str, str]]] = None,
        save_nan: bool = False,
        **kwargs
    ):
        """覆盖指定维度范围并保有某个维度所有成员在列上的 ``DataFrame``

        相比于:meth:`save_unpivot`，在保存前，会将`data`按照`expression`补全笛卡尔积。
        并且不在`data`范围的数据以`None`填充

        Note:
            逻辑上等价于两次调用

            .. code-block:: python

                cube.delete(expression)
                cube.save_unpivot(data, unpivot_dim, **kwargs)

        Args:
            data: 需要保存的数据
            unpivot_dim: 成员在列上的维度
            expression: 需要覆盖的范围（维度表达式）
            default_hierarchy: 单expression中没指定对应维度时，默认取的层级函数，
                即填充为 `default_hierarchy(#root,0)`
            pov: Point Of View，维度表达式或者KV键值对格式。
            save_nan: 当把数据列成员转换到行上时，data为空的数据是否保存
            **kwargs: 其他可传给 :meth:`save_unpivot`的参数

        See Also:
            :meth:`save`
            :meth:`save_unpivot`
            :meth:`complement_save`

        """
        if not self._backend_del_availiable:
            return await self._legacy_complement_save_unpivot(
                data=data,
                unpivot_dim=unpivot_dim,
                expression=expression,
                default_hierarchy=default_hierarchy,
                pov=pov,
                save_nan=save_nan,
                **kwargs
            )

        await self.delete(
            expression,
            data_audit=False,
            default_hierarchy=default_hierarchy
        )
        await self.save_unpivot(
            data=data,
            unpivot_dim=unpivot_dim,
            pov=pov,
            save_nan=save_nan,
            **kwargs,
        )

    async def _legacy_complement_save_unpivot(
        self,
        data: pd.DataFrame,
        unpivot_dim: str,
        expression: Union[str, Dict[str, Union[List[str], str]]],
        default_hierarchy: str = "Base",
        pov: Optional[Union[str, Dict[str, str]]] = None,
        save_nan: bool = False,
        **kwargs
    ):
        data, pov = self._build_dataframe_for_save_unpivot(
            data, unpivot_dim, pov, save_nan
        )
        if data.empty:
            return

        data_comp = self._complement(data, expression, default_hierarchy, pov)
        return await self._save_impl(data_comp, pov, **kwargs)

    async def _save_impl(
        self,
        data: pd.DataFrame,
        pov: Optional[Dict[str, str]] = None,
        need_check: bool = True,
        data_audit: bool = True,
        chunksize: Optional[int] = None,
        callback: bool = True,
        auth_mode: Literal[0, 1, 2, 3] = 0,
    ):
        # replace NaN to standard None
        # NB: replace twice in case of infer None to nan happened in 2.x pandas
        data[DFLT_DATA_COLUMN] = data[DFLT_DATA_COLUMN].replace({None: np.nan})
        data[DFLT_DATA_COLUMN] = data[DFLT_DATA_COLUMN].replace({np.nan: None})
        # ensure view is capitalized
        if self._meta.autoCalculation:
            data = data.rename(columns=VIEW_DICT)

        cols = list(data.columns)
        if dup_cols := set([c for c in cols if cols.count(c) > 1]):
            raise ValueError(f"Duplicate columns:{dup_cols} found in data.")

        # save data
        resp = []

        for batch_data, alert in split_dataframe_alert(
            data, chunksize, self.before_chunk, self.after_chunk
        ):
            with alert:
                row_data = [
                    {"columnDimensionMemberMap": row}
                    for row in bp.dataframe_to_dict(batch_data)
                ]
                payload = ReactSpreadsheetSaveForm(
                    entryObject=self.entry_object,
                    sheetDatas=[SpreadsheetSingleData(
                        cubeName=self.element_info.elementName,
                        cubeFolderId=self.element_info.folderId,
                        rowDatas=row_data,
                        commonMember=pov,
                    )],
                    needCheck=need_check,
                    dataAuditSwitch=data_audit,
                    entryMode=self.entry_mode,
                    validateDimensionMember=need_check,
                    callback=callback,
                    saveDataAuthMode=auth_mode
                )
                r = await self.async_api.reactspreadsheet.save(
                    payload.dict(exclude_unset=True)
                )
                resp.append(r)
        return resp

    async def delete_with_mdx(
        self,
        expression: Union[str, Dict[str, Union[List[str], str]]]
    ):
        """通过MDX脚本删除数据

        根据维度表达式删除Cube数据

        Warnings:
            此方法将根据维度表达式生成对应的MDX脚本并执行MDX的Cleardata
            对于只有成员和单集合方法的表达式，可以直接转换为MDX的成员集合或集合函数表达式
            如为复杂表达式(例如包含聚合方法)，则会查询实际对应的成员后，再组成MDX的成员集合

        Args:
            expression: 维度表达式

        .. admonition:: 示例

            两种调用方式等价：

            .. code-block:: python
                :emphasize-lines: 3,8

                cube = FinancialCube('example')
                expr = 'Year{2021;2022}->Entiy{Base(TotalEntity,0)}'
                r = cube.delete_with_mdx(expr)
                expr_dict = {
                    "Year": ['2021', '2022'],
                    "Entity": "Base(TotalEntity,0)"
                }
                r = cube.delete_with_mdx(expr_dict)

        Returns:
            MDX执行结果

        See Also:
            :meth:`insert_null` :meth:`delete`

        """
        if isinstance(expression, dict):
            expression = dict_to_expr(expression)

        query_dims = []
        all_cols = set(self.dim_col_map.values())
        dimexprs = {}
        cols_appeared = set()

        def normalize_name(name_: str) -> str:
            if RE_NAME_WITH_PARENT.match(name_):
                return name_
            return f'[{name_}]'

        async def query_dim(
            col_: str,
            part_: str,
            dim_name_: str
        ) -> Tuple[str, Set[str]]:
            result: List[Dict[str, Any]] = await self.dim_elements[dim_name_].query(
                part_, fields=['name'], as_model=False
            )
            mbrs_ = set()
            for item in result:
                if (name := item.get('expectedName')) is not None:
                    mbrs_.add(f"[{col_}].{normalize_name(name)}")
                else:
                    mbrs_.add(f"[{col_}].{normalize_name(item['name'])}")
            return col_, mbrs_

        for expr in expression.split('->'):
            dim, body = unpack_expr(expr)
            col = self._get_column_from_dim(dim)

            for part in body.split(';'):
                part = part.replace(' ', '')
                if not part:
                    continue

                cols_appeared.add(col)

                if is_valid_pov(part):
                    dimexprs.setdefault(col, set()).add(
                        f"[{col}].{normalize_name(part)}"
                    )
                elif match := _RE_SIMPLE_EXPR.match(part):
                    mbr = match.group('mbr')
                    hier = match.group('hierarchy').capitalize()
                    with_parent = match.group('with_parent')

                    if with_parent == '1':
                        dimexprs.setdefault(col, set()).add(
                            f"{hier}([{col}].{normalize_name(mbr)},WITH_PARENT)"
                        )
                    else:
                        dimexprs.setdefault(col, set()).add(
                            f"{hier}([{col}].{normalize_name(mbr)})"
                        )
                else:
                    dim_name = self.col_dim_map.get(col, col)
                    query_dims.append(query_dim(col, part, dim_name))

        for col in all_cols - cols_appeared:
            dimexprs[col] = {f"Base([{col}].[#root])"}

        dim_mbrs = await asyncio.gather(*query_dims)

        for col, mbrs in dim_mbrs:
            dimexprs.setdefault(col, set())
            dimexprs[col] = dimexprs[col].union(mbrs)

        # ClearData方法的维度范围优先使用科目维度
        if account_col := self.account_col:
            clear_data_expr = dimexprs.pop(account_col)
            scope_expr = chain(*dimexprs.values())
        else:
            expr_list = list(dimexprs.values())
            clear_data_expr = expr_list[0]
            scope_expr = chain(*expr_list[1::])

        script = """Scope(%s);\nCleardata(%s);\nEnd Scope;
        """ % (','.join(scope_expr), ','.join(clear_data_expr))

        return await self.mdx_execution(script)

    @future_property
    async def _server_version(self) -> Tuple[int, ...]:
        api: FinancialModelAPI = await self.wait_for('async_api')
        version = await api.extra.git_version()
        if version.lower().startswith('v'):
            version = version[1:]
        parts = []
        for part in version.split('.'):
            try:
                parts.append(int(part))
            except (TypeError, ValueError):
                continue
        return tuple(parts)

    @future_property
    async def _backend_del_availiable(self):
        version = await self.__class__._server_version.wait_for(self)
        return version >= (1, 1, 1, 2, 1)

    async def delete(
        self,
        expression: Union[TypeDimensionExpr, List[TypeDimensionExpr]],
        chunksize: Optional[int] = None,
        use_mdx: bool = False,
        callback: bool = False,
        data_audit: bool = True,
        default_hierarchy: str = "Base",
    ):
        """删除数据

        根据维度表达式删除Cube数据。

        Warnings:
            此方法首先查询数据，并且替换为null再调用保存接口。
            因此如果要删除的数据量大，可能导致内存不足等问题。
            如果不需要数据审计功能，请使用 :meth:`insert_null`

        Args:
            expression: 维度表达式
            chunksize: 单次调用保存接口时最大的dataframe行数。
              当data的行数超过此值时，将会分多次进行保存。
            use_mdx: 是否使用MDX脚本实现，默认为否，等效于调用 :meth:`delete_with_mdx`
            callback: 是否回调
            data_audit: 是否记录审计日志
            default_hierarchy: 当expression中没指定对应维度时，默认取的层级函数，
                即填充为 `default_hierarchy(#root,0)`

        .. admonition:: 示例

            两种调用方式等价：

            .. code-block:: python
                :emphasize-lines: 3,8

                cube = FinancialCube('example')
                expr = 'Year{2021;2022}->Entiy{Base(TotalEntity,0)}'
                r = cube.delete(expr)
                expr_dict = {
                    "Year": ['2021', '2022'],
                    "Entity": "Base(TotalEntity,0)"
                }
                r = cube.delete(expr_dict)

        Returns:
            删除结果

        See Also:
            :meth:`insert_null` :meth:`delete_with_mdx`

        """
        if (
            not self._backend_del_availiable
            or use_mdx
            or callback
        ):
            if isinstance(expression, list):
                raise ValueError(
                    f"pass expresssion as list is not yet supported. "
                    f"backend version: {self._server_version}")
            return await self._legacy_delete(
                expression,
                chunksize=chunksize,
                use_mdx=use_mdx,
                callback=callback,
                data_audit=data_audit,
            )

        if not isinstance(expression, list):
            expression = [expression]

        clear_scopes = []
        for expr in expression:
            if isinstance(expr, dict):
                expr = dict_to_expr(expr)

            expr_str, pov = self._split_expr(
                expr, {},
                default_hierarchy=default_hierarchy,
                validate_expr=True
            )
            expr_parts = []
            if expr_str:
                expr_parts.append(expr_str)
            if pov:
                expr_parts.append(dict_to_expr(pov))

            clear_scopes.append("->".join(expr_parts))

        return await self.async_api.calculate.clear_data_ex(
            SyncClearDataDto(
                cubeName=self.element_name,
                folderId=self.element_info.folderId,
                clearScriptList=clear_scopes,
                entryMode=self.entry_mode,
                entryObject='python',
                dataAuditSwitch=data_audit
            )
        )

    async def _legacy_delete(
        self,
        expression: Union[str, Dict[str, Union[List[str], str]]],
        chunksize: Optional[int] = None,
        use_mdx: bool = False,
        callback: bool = True,
        data_audit: bool = True,
    ):
        if use_mdx:
            return await self.delete_with_mdx(expression)

        if self._meta.autoCalculation:
            if isinstance(expression, str):
                expression = expr_to_dict(expression)
            expression = {**expression}

        if isinstance(expression, dict):
            expression = dict_to_expr(expression)

        data, pov = await self.query(expression)
        data[DFLT_DATA_COLUMN] = None
        return await self.save(
            data, pov, data_audit=data_audit, chunksize=chunksize, callback=callback
        )

    async def queries(
        self,
        expressions: Iterable[str],
        drop_duplicates: bool = True,
        normalize_view: bool = False,
    ) -> pd.DataFrame:
        """查询多个表达式

        协程并发查询多个维度表达式，并且将查询结果合并为一个
        :obj:`DataFrame` 。

        Args:
            expressions: 待查询的维度表达式列表
            drop_duplicates: 是否需要去重
            normalize_view: 是否把大小写View统一成"View"

        Returns:
            查询结果

        """
        if isinstance(expressions, str):
            return await self.query(
                expressions, compact=False, normalize_view=normalize_view)

        expressions = list(expressions)
        if len(expressions) == 1:
            return await self.query(
                expressions[0], compact=False, normalize_view=normalize_view)

        df_list = await asyncio.gather(*(
            self.query(expr, compact=False, normalize_view=True)
            for expr in expressions
        ))

        if not df_list:
            dflt_cols = list(self.dim_col_map.values()) + [DFLT_DATA_COLUMN]
            data = pd.DataFrame(columns=dflt_cols)
            data[DFLT_DATA_COLUMN] = data[DFLT_DATA_COLUMN].astype(float)
        else:
            data = pd.concat(df_list, sort=False)
            if drop_duplicates:
                dim_cols = data.columns.difference([DFLT_DATA_COLUMN])
                data = data.drop_duplicates(dim_cols)
        if not normalize_view:
            data = data.rename(columns={VIEW: "view"})
        return data

    async def pc_init(
        self,
        process_map: Optional[Dict[str, str]] = None,
        data_block_map: Optional[Dict[str, str]] = None,
        block_name: Optional[str] = None,
        block_list: Optional[list] = None,
        status: Optional[str] = None,
    ) -> ResultObj:
        """
        cube权限初始化

        Args:
            process_map: 流程控制字段(key:字段名，value:维度表达式)
            data_block_map: 审批单元(key:字段名，value:维度表达式) -- 自动创建
            block_name: 审批单元名称 -- 非自动创建
            block_list: 审批单元集合 -- 非自动创建
            status: 初始化后的审批状态

        Returns:
            初始化结果

        .. admonition:: 示例

            .. code-block:: python

                cube = FinancialCube('example')
                process_map = {'Year': 'Year{2021;2022}'}
                data_block_map = {'Entity': 'Entity{Base(T01,0)}'}
                r = cube.pc_init(process_map=process_map, data_block_map=data_block_map, status='1')

        """
        return await self.async_api.block.pc_init(PcParams(
            blockList=block_list,
            blockName=block_name,
            cubeFolderId=self.element_info.folderId,
            cubeName=self.element_name,
            datablockMap=data_block_map,
            processMap=process_map,
            status=status))

    async def pc_update(
        self,
        status: str,
        process_map: Optional[Dict[str, str]] = None,
        data_block_map: Optional[Dict[str, str]] = None,
        block_name: Optional[str] = None,
        block_list: Optional[list] = None,
    ) -> Any:
        """
        cube权限状态更新

        与 :meth:`pc_upsert` 区别在于，此方法调用的接口为 /block/pc-status，
        该接口对指定范围的数据块权限进行update操作，无则不做更改和新增，有则更新状态

        Args:
            process_map: 流程控制字段(key:字段名，value:维度表达式)
            data_block_map: 审批单元(key:字段名，value:维度表达式) -- 自动创建
            block_name: 审批单元名称 -- 非自动创建
            block_list: 审批单元集合 -- 非自动创建
            status: 更新后的审批状态

        Returns:
            更新结果

        .. admonition:: 示例

            .. code-block:: python

                cube = FinancialCube('example')
                process_map = {'Year': 'Year{2021;2022}'}
                data_block_map = {'Entity': 'Entity{T0101}'}
                r = cube.pc_update(process_map=process_map, data_block_map=data_block_map, status='2')

        See Also:
            :meth:`pc_upsert`

        """
        return await self.async_api.block.pc_status(PcParams(
            blockList=block_list,
            blockName=block_name,
            cubeFolderId=self.element_info.folderId,
            cubeName=self.element_name,
            datablockMap=data_block_map,
            processMap=process_map,
            status=status))

    async def pc_upsert(
        self,
        status: str,
        process_map: Optional[Dict[str, str]] = None,
        data_block_map: Optional[Dict[str, str]] = None,
        block_name: Optional[str] = None,
        block_list: Optional[list] = None,
    ) -> Any:
        """
        cube权限状态upsert更新

        与 :meth:`pc_update` 区别在于，此方法调用的接口为 /block/pc-status-upsert，
        该接口对指定范围的数据块权限进行upsert操作，无则新增，有则更新状态

        Args:
            process_map: 流程控制字段(key:字段名，value:维度表达式)
            data_block_map: 审批单元(key:字段名，value:维度表达式) -- 自动创建
            block_name: 审批单元名称 -- 非自动创建
            block_list: 审批单元集合 -- 非自动创建
            status: 更新后的审批状态

        Returns:
            更新结果

        .. admonition:: 示例

            .. code-block:: python

                cube = FinancialCube('example')
                process_map = {'Year': 'Year{2021;2022}'}
                data_block_map = {'Entity': 'Entity{T0101}'}
                r = cube.pc_upsert(process_map=process_map, data_block_map=data_block_map, status='2')

        See Also:
            :meth:`pc_update`

        """
        return await self.async_api.block.pc_status_upsert(PcParams(
            blockList=block_list,
            blockName=block_name,
            cubeFolderId=self.element_info.folderId,
            cubeName=self.element_name,
            datablockMap=data_block_map,
            processMap=process_map,
            status=status))

    async def copy_calculate(self, formula: str, fix_members: str):
        """
        cube copy计算接口

        Args:
            formula: 维度成员来源和目的的表达式
            fix_members: 维度成员的筛选表达式

        Returns:
            更新结果

        .. admonition:: 示例

            .. code-block:: python

                cube = FinancialCube('test')
                r = cube.copy_calculate(formula="Account{a1}=Account{a2}",
                                        fix_members="Entity{e1}->Year{y1}")

        将把Entity{e1}->Year{y1}->Account{a2}的数据复制一份到Entity{e1}->Year{y1}->Account{a1}

        """
        return await self.async_api.extra.copyCalculate(
            CopyCalculateDTO(
                cubeFolderId=self.element_info.folderId,
                cubeName=self.element_name,
                cubePath=self._path,
                formula=formula,
                fixMembers=fix_members,
                entryObject="python"
            )
        )

    async def insert_null(
        self,
        expression: Union[str, Dict[str, Union[List[str], str]]],
        query_all: bool = False,
    ):
        """使用insert null方式删除数据

        根据维度表达式删除Cube数据。
        入参与 :meth:`delete` 相同，
        在使用clickhouse作事实表时推荐使用本方法，
        在使用MySQL作事实表时，等同于调用 :meth:`delete` 。

        Args:
            expression: 维度表达式
            query_all: 是否查询所有维度，在事实表为clickhouse时起作用

        .. admonition:: 示例

            两种调用方式等价：

            .. code-block:: python
                :emphasize-lines: 3,8

                cube = FinancialCube('example')
                expr = 'Year{2021;2022}->Entiy{Base(TotalEntity,0)}'
                r = cube.insert_null(expr)
                expr_dict = {
                    "Year": ['2021', '2022'],
                    "Entity": "Base(TotalEntity,0)"
                }
                r = cube.insert_null(expr_dict)

        Returns:
            insert sql的执行结果

        See Also:
            :meth:`delete`

        """
        if not isinstance(
            self.fact_table, 
            (AsyncDataTableClickHouse, DataTableClickHouse)
        ):
            return await self.delete(expression)

        if isinstance(expression, str):
            expression = expr_to_dict(expression)

        if self._meta.autoCalculation:
            expression = {**expression}
            expression.pop(VIEW, None)

        member_dict = {}
        coros = []
        columns = []

        for dim, expr in expression.items():
            col = self.dim_col_map.get(dim, dim)
            dim = self.col_dim_map.get(dim, dim)

            if isinstance(expr, list):
                member_dict[col] = expr
            elif query_all or need_query(expr):
                coros.append(self.dim_elements[dim].query(
                    expr, fields=['name'], as_model=False
                ))
                columns.append(col)
            else:
                member_dict[col] = expr.split(';')

        for col, rslt in zip(columns, await asyncio.gather(*coros)):
            member_dict[col] = [item['name'] for item in rslt]

        where = dict_to_sql(member_dict, '=', bracket=False)
        fact_table = self.fact_table

        all_dims = ','.join(f"`{col}`" for col in self.dim_col_map.values())
        decimal_val = f"if(" \
                      f"argMax(ifNull(toString({DECIMAL_COL}),'isnull'),createtime)='isnull'," \
                      f"null," \
                      f"argMax({DECIMAL_COL},createtime)" \
                      f") as `{DECIMAL_COL}`"
        string_val = f"if(" \
                     f"argMax(ifNull({STRING_COL},'isnull'),createtime)='isnull'," \
                     f"null," \
                     f"argMax({STRING_COL},createtime)" \
                     f") AS `{STRING_COL}`"

        sub_query = f"SELECT " \
                    f"{all_dims},{decimal_val},{string_val} " \
                    f"from {fact_table.table_name} " \
                    f"where {where} " \
                    f"GROUP BY {all_dims}"

        sub_dims = ','.join(f"main_table.{col}" for col in self.dim_col_map.values())
        # now = int(datetime.datetime.now().timestamp() * 1000) + OPTION.api.clock_offset
        now = "toUnixTimestamp64Milli(now64(3))"
        main_query = f"SELECT * from ({sub_query}) sub_table " \
                     f"where `{DECIMAL_COL}` is not null or `{STRING_COL}` is not null"
        replace_null = f"SELECT {sub_dims},null as {DECIMAL_COL},null as {STRING_COL},{now} " \
                       f"from ({main_query}) main_table " \

        sql = f"INSERT INTO {fact_table.table_name} " \
              f"({all_dims},{DECIMAL_COL},{STRING_COL}, createtime) {replace_null};"
        return await fact_table.run_sql(sql)

    async def mdx_execution(
        self,
        script: str,
        parameters: Optional[Dict[str, str]] = None,
        precision: Optional[int] = None,
        timeout: Optional[int] = None,
        round_type: Union[RoundType, str] = RoundType.floor,
    ):
        """执行MDX计算语句

        Args:
            script: MDX计算语句
            parameters: MDX执行所需的标量参数信息键值对
            precision: 计算精度，默认为财务模型小数精度
            timeout: 超时时间(ms)，默认为180秒(与OPTION.api.timeout保持一致)，
                     如为None，则为接口的默认值60秒，
                     目前该接口不支持设置为无限等待执行结果
            round_type: 小数保留类型，默认为去尾法

        .. admonition:: 示例

            .. code-block:: python

                cube = FinancialCube('example')

                # 用2022年每个月份所有产品的销售量
                # 乘以各产品设定在Begbalance期间成员上的单价
                # 得到各个产品的销售额
                script = '''
                    Scope(strToMember($scenario),
                            [Version].[V1],
                            [Year].[2022],
                            MemberSet(strToMember('Period',$period)),
                            Base([Product].[TotalProduct]),
                            Base([Entity].[TotalEntity])
                    );
                    [Account].[Total_Sales] = [Account].[Volume]*[Account].[Price]->[Period].[Begbalance];
                    End Scope;
                '''

                # 执行MDX语句，并指定参数scenario为'[Scenario].[actual]'，period为'Q1'
                # 小数保留类型为四舍五入
                cube.mdx_execution(
                    script=script,
                    parameters={'scenario': '[Scenario].[actual]','period': 'Q1'},
                    round_type='round'
                )


        Returns:
            执行结果

        Important:
            script不可包含use section部分，use的Cube固定为当前Financial Cube

        """
        if _RE_USE_SECTION.match(script.upper()):
            raise ValueError(
                'MDX语句中发现use section，在FinancialCube中使用时，'
                '固定为当前Cube，不支持指定其他Cube'
            )

        if timeout is None:
            timeout = OPTION.api.timeout * 1000

        business_id = (
            f"PythonScript_{OPTION.general.task_info.get('script_name', '')}_MDX"
            f"-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        )
        params = []

        if parameters is not None:
            if not isinstance(parameters, dict):
                raise TypeError('parameters参数应为字典')

            for key, value in parameters.items():
                params.append(MDXVariableParameter(key=key, value=value))

        path = self._path

        if path is None:
            path = await AppAPI(sync=False).folder.get_folder_full(
                self.element_info.folderId
            )

        path = path.replace('\\', '/')

        params.append(
            MDXCubeParameter(
                key=self.element_name,
                value=concat_url(path, f"{self.element_name}.cub")
            )
        )

        res = await self.async_api.mdxtask.execution(
            TaskExecutionParam(
                businessId=business_id,
                decimalDigitsType=RoundType[round_type],
                parameters=params,
                precision=precision,
                script=f'Use {self.element_name};\n{script}',
                timeout=timeout
            )
        )

        if res.status == 1:
            raise MDXExecuteTimeout(f'MDX执行超时，具体响应:\n{res}')

        if res.result is False:
            raise MDXExecuteFail(
                f'MDX执行失败，失败原因:\n{res.failReason}'
            )

        return res

    async def mdx_execution_with_code(
        self,
        script_code: str,
        parameters: Optional[Dict[str, str]] = None,
        precision: Optional[int] = None,
        timeout: Optional[int] = None,
        round_type: Union[RoundType, str] = RoundType.floor,
    ):
        """通过提供MDX计算脚本编码执行对应的MDX计算脚本

        Args:
            script_code: MDX计算脚本编码
            parameters: MDX执行所需的标量参数信息键值对
            precision: 计算精度，默认为财务模型小数精度
            timeout: 超时时间(ms)，默认为180秒(与OPTION.api.timeout保持一致)，
                     如为None，则为接口的默认值60秒，
                     目前该接口不支持设置为无限等待执行结果
            round_type: 小数保留类型，默认为去尾法

        Returns:
            执行结果

        """

        if timeout is None:
            timeout = OPTION.api.timeout * 1000

        params = []

        if parameters is not None:
            if not isinstance(parameters, dict):
                raise TypeError('parameters参数应为字典')

            for key, value in parameters.items():
                params.append(MDXVariableParameter(key=key, value=value))

        path = self._path

        if path is None:
            path = await AppAPI(sync=False).folder.get_folder_full(
                self.element_info.folderId
            )

        path = path.replace('\\', '/').rstrip('/') + '/'

        res = await self.async_api.mdxtask.execution(
            TaskExecutionParam(
                businessId=script_code,
                decimalDigitsType=RoundType[round_type],
                parameters=params,
                precision=precision,
                timeout=timeout,
                scriptCode=script_code,
                cubeName=self.element_info.elementName,
                cubeFolderId=self.element_info.folderId,
                cubePath=path
            )
        )

        if res.status == 1:
            raise MDXExecuteTimeout(f'MDX执行超时，具体响应:\n{res}')

        if res.result is False:
            raise MDXExecuteFail(f'MDX执行失败，失败原因:\n{res.failReason}')

        return res


class FinancialCube(AsyncFinancialCube, metaclass=SyncMeta):
    synchronize = (
        'query',
        'queries',
        'save',
        'complement_save',
        'save_unpivot',
        'complement_save_unpivot',
        'delete',
        'delete_with_mdx',
        'pc_init',
        'pc_update',
        'pc_upsert',
        'insert_null',
        'copy_calculate',
        'mdx_execution',
        'mdx_execution_with_code',
    )

    if TYPE_CHECKING:   # pragma: no cover
        def queries(
            self,
            expressions: Iterable[str],
            drop_duplicates: bool = True,
            normalize_view: bool = False,
        ) -> pd.DataFrame:
            ...

        def query(
            self,
            expression: str,
            pov: Optional[Union[str, Dict[str, str]]] = None,
            compact: bool = True,
            pivot_dim: Optional[str] = None,
            validate_expr: bool = True,
            verify_access: bool = False,
            include_ignored: bool = False,
            normalize_view: bool = False,
            pivot_members: List[str] = None,
        ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Dict[str, str]]]:
            ...

        def save(
            self,
            data: pd.DataFrame,
            pov: Optional[Union[str, Dict[str, str]]] = None,
            data_column: str = DFLT_DATA_COLUMN,
            need_check: bool = True,
            data_audit: bool = True,
            chunksize: Optional[int] = None,
            callback: bool = True,
            comment_column: str = DFLT_COMMENT_COLUMN,
            auth_mode: Literal[0, 1, 2, 3] = 0,
        ):
            ...

        def complement_save(
            self,
            data: pd.DataFrame,
            expression: Union[str, Dict[str, Union[List[str], str]]],
            pov: Optional[Union[str, Dict[str, str]]] = None,
            data_column: str = DFLT_DATA_COLUMN,
            comment_column: str = DFLT_COMMENT_COLUMN,
            **kwargs
        ):
            ...

        def save_unpivot(
            self,
            data: pd.DataFrame,
            unpivot_dim: str,
            pov: Optional[Union[str, Dict[str, str]]] = None,
            need_check: bool = True,
            data_audit: bool = True,
            chunksize: Optional[int] = None,
            save_nan: bool = False,
            callback: bool = True
        ):
            ...

        def complement_save_unpivot(
            self,
            data: pd.DataFrame,
            unpivot_dim: str,
            expression: Union[str, Dict[str, Union[List[str], str]]],
            default_hierarchy: str = "Base",
            pov: Optional[Union[str, Dict[str, str]]] = None,
            save_nan: bool = False,
            **kwargs
        ):
            ...

        def delete(
            self,
            expression: Union[str, Dict[str, Union[List[str], str]]],
            chunksize: Optional[int] = None,
            use_mdx: bool = False,
            callback: bool = True,
            data_audit: bool = True,
            default_hierarchy: str = "Base",
        ):
            ...

        def delete_with_mdx(
            self,
            expression: Union[str, Dict[str, Union[List[str], str]]]
        ):
            ...

        def pc_init(
            self,
            process_map: Optional[Dict[str, str]] = None,
            data_block_map: Optional[Dict[str, str]] = None,
            block_name: Optional[str] = None,
            block_list: Optional[list] = None,
            status: Optional[str] = None,
        ):
            ...

        def pc_update(
            self,
            status: str,
            process_map: Optional[Dict[str, str]] = None,
            data_block_map: Optional[Dict[str, str]] = None,
            block_name: Optional[str] = None,
            block_list: Optional[list] = None,
        ):
            ...

        def pc_upsert(
            self,
            status: str,
            process_map: Optional[Dict[str, str]] = None,
            data_block_map: Optional[Dict[str, str]] = None,
            block_name: Optional[str] = None,
            block_list: Optional[list] = None,
        ) -> Any:
            ...

        def insert_null(
            self,
            expression: Union[str, Dict[str, Union[List[str], str]]],
            query_all: bool = False,
        ):
            ...

        def copy_calculate(self, formula: str, fix_members: str):
            ...

        def mdx_execution(
            self,
            script: str,
            parameters: Optional[Dict[str, str]] = None,
            precision: Optional[int] = None,
            timeout: Optional[int] = OPTION.api.timeout * 1000,
            round_type: Union[RoundType, str] = RoundType.floor,
        ):
            ...

        def mdx_execution_with_code(
            self,
            script_code: str,
            parameters: Optional[Dict[str, str]] = None,
            precision: Optional[int] = None,
            timeout: Optional[int] = None,
            round_type: Union[RoundType, str] = RoundType.floor,
        ):
            ...

    @cached_property
    def dim_elements(self) -> LazyDict[str, Dimension]:
        """财务Cube的维度元素

        维度名 -> 维度元素的字典，延迟初始化，
        只会在使用时创建维度元素
        """
        dims = LazyDict()
        for dim in self._meta.cubeDimensionList:
            if dim.dimensionName is None:
                continue
            dims[dim.dimensionName] = (
                Dimension,
                dim.dimensionName,
                dim.dimensionFolderId,
                dim.dimensionPath,
                False,
                dim.dimensionServerName,
            )
        return dims

    @cached_property
    def fact_table(self) -> T_DatatableInstance:
        """事实表对应的数据表"""
        table_info = self._meta.datatable
        init_args = dict(
            element_name=table_info.name,
            folder_id=table_info.folderId,
            path=table_info.path,
            table_name=table_info.actualTableName,
            server_name=self._meta.datatableServerName
        )

        if (server_name := self._meta.datatableServerName) is None:
            if self._meta.dataSync == 1:
                return DataTableClickHouse(**init_args)
            else:
                return DataTableMySQL(**init_args)

        return get_table_class(server_name)(**init_args)
