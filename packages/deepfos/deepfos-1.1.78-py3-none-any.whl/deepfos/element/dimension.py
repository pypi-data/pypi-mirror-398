import functools
from contextlib import contextmanager
from itertools import chain
from typing import List, Dict, Iterable, Any, Union, Type, Tuple, Optional, TYPE_CHECKING
from collections import Counter

import pandas as pd
from loguru import logger

from deepfos.element.rolestrategy import RoleStrategy, AsyncRoleStrategy
from multidict import CIMultiDict

from deepfos.api.models import compat_parse_obj_as as parse_obj_as
from .base import ElementBase, SyncMeta
from .datatable import AsyncDataTableMySQL, get_table_class, T_AsyncDatatableClass
from deepfos.algo.graph import DAGraph
from deepfos.lib.decorator import cached_property
from deepfos.api.dimension import DimensionAPI
from deepfos.api.models.dimension import (
    DimensionMembersDto,
    DimensionInfoSw,
    DimensionMemberChangeSaveSw,
    DimensionMemberOperationSw,
    DimensionMemberSaveDto as DimMemberSave,
    DimensionMemberListDto as DimInfo,
    Dimension as DimensionModel,
    DimensionMemberByNameFunctionDto as DimQueryExpr,
    DimensionMemberBean,
)
from deepfos.api.V1_2.models.dimension import (
    DimensionMemberByNameFunctionDto as DimQueryExpr1_2,
    MultiEntityConfigResult,
    DimensionMemberTreeSaveDto,
    DimensionMemberOperationDto
)
from deepfos.exceptions import DimensionSaveError, MemberNotFoundError
from deepfos.lib.utils import unpack_expr, CIEnum, get_language_key_map
from deepfos.lib.asynchronous import future_property
from deepfos.lib.constant import (
    ROOT, ACCEPT_LANS, DFLT_NAME_COLUMN,
    DFLT_PNAME_COLUMN, SHAREDMEMBER, INDEX_FIELD,
    SHAREDMEMBERV12, DFLT_PNAME_COLUMN_V12
)

__all__ = [
    'DimMember',
    'DimMemberV12',
    'Dimension',
    'AsyncDimension'
]


class Strategy(CIEnum):
    full_replace = 'full_replace'
    incr_replace = 'incr_replace'
    keep_old = 'keep_old'


class DimMember(DimensionMemberOperationSw):
    is_active: bool = True
    is_modula: bool = False
    aggweight: int = 1.0
    sharedmember: bool = False
    datatype: str = "NUMBER"
    parent_name: str = ROOT


class DimMemberV12(DimensionMemberOperationDto):
    isActive: bool = True
    aggweight: int = 1.0
    sharedMember: bool = False
    dataType: str = "NUMBER"
    parentName: str = ROOT

    @property
    def parent_name(self):
        return self.parentName

    @property
    def sharedmember(self):
        return self.sharedMember

    @property
    def origin_name(self):
        return self.originName

    @property
    def origin_parent_name(self):
        return self.originParentName

    @property
    def is_active(self):
        return self.isActive

    @property
    def accounttype(self):
        return self.accountType

    @property
    def datatype(self):
        return self.dataType

    @property
    def end_period(self):
        return self.endPeriod

    @property
    def end_year(self):
        return self.endYear

    @property
    def flowtype(self):
        return self.flowType

    @property
    def halfyear(self):
        return self.halfYear

    @property
    def local_currency(self):
        return self.localCurrency

    @property
    def period_level(self):
        return self.periodLevel

    @property
    def start_year(self):
        return self.startYear

    @property
    def start_period(self):
        return self.startPeriod

    @property
    def sort_col(self):
        return self.sortCol


ADD = 'add'
UPD = 'update'
DEL = 'delete'

OPE = 'operation'

V10_TO_V12 = {
    'accounttype': 'accountType',
    'datatype': 'dataType',
    'end_period': 'endPeriod',
    'end_year': 'endYear',
    'flowtype': 'flowType',
    'halfyear': 'halfYear',
    'is_active': 'isActive',
    'local_currency': 'localCurrency',
    'parent_name': 'parentName',
    'period_level': 'periodLevel',
    'origin_name': 'originName',
    'origin_parent_name': 'originParentName',
    'sharedmember': 'sharedMember',
    'start_period': 'startPeriod',
    'start_year': 'startYear',
    'sort_col': 'sortCol',
    'is_modula': 'is_modula',
    'is_base': 'is_base',
    'is_calculated': 'is_calculated',
    'formula': 'formula',
}


# -----------------------------------------------------------------------------
# core
class AsyncDimension(ElementBase[DimensionAPI]):
    """维度

    Args:
        strict: 是否开启严格校验模式。如果开启，会查询系统中存在的所有维度，并且基于系统维度作完整性校验。会损失性能
    """
    api: DimensionAPI

    def __init__(
        self,
        element_name: str,
        folder_id: str = None,
        path: str = None,
        strict: bool = False,
        server_name: str = None,
    ):
        self._add_memo = CIMultiDict()
        self._del_memo = CIMultiDict()
        self._upd_memo = CIMultiDict()
        self.__member_memo = None if strict else CIMultiDict()
        self._strict = strict
        super().__init__(element_name, folder_id, path, server_name)

    @cached_property
    def _datatable_class(self) -> T_AsyncDatatableClass:
        if (server_name := self.meta.databaseServerName) is None:
            return AsyncDataTableMySQL

        return get_table_class(server_name, sync=False)

    @cached_property
    def table_closure(self):
        """维度层级关系表

        Warnings:
            储存维度的层级关系，不要随意修改此表数据！

        """
        meta = self.meta
        return self._datatable_class(
            element_name=meta.tcServerName,
            folder_id=meta.tcFolderId,
            table_name=meta.table_closure,
            server_name=meta.databaseServerName
        )

    @cached_property
    def table_dimension(self):
        """维度数据表

        Warnings:
            储存维度的主数据，不要随意修改此表数据！
        """
        meta = self.meta
        return self._datatable_class(
            element_name=meta.tdServerName,
            folder_id=meta.tdFolderId,
            table_name=meta.table_dimension,
            server_name=meta.databaseServerName
        )

    @property
    def _member_memo(self) -> CIMultiDict[DimensionMemberOperationSw]:
        if self.__member_memo is None:
            self.__member_memo = memo = CIMultiDict()

            for mbr in self.members:
                memo.add(mbr.name, mbr)

        return self.__member_memo

    @cached_property
    def is_v1_0_api(self) -> bool:
        return self.api.version == (1, 0)

    @future_property(on_demand=True)
    async def members(self) -> List[DimensionMembersDto]:
        """当前维度的所有成员

        Note:
            只会返回系统中存在的维度成员。通过 :meth:`add_member`
            或 :meth:`delete_member` 本地修改维度成员并不会会影响此属性的值。
        """
        api = await self.wait_for('async_api')
        element_info = await self.wait_for('element_info')
        dim_info = DimInfo.construct_from(
            element_info,
            name=self.element_name
        )
        if api.version == api.default_version:
            mbr = await api.custom.select_dimension_member_list(dim_info)
        else:
            mbr = await api.extra.dimension_custom_select_dimension_member_list(dim_info)
        return parse_obj_as(List[DimensionMembersDto], mbr['memberList'])

    @future_property
    async def meta(self) -> DimensionModel:
        """
        当前维度的元信息
        """
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        if api.version == api.default_version:
            return await api.query.open_dimension_info_by_id(ele_info)
        return await api.extra.dimension_query_open_dimension_info_by_id(ele_info)

    def add_member(
        self, 
        *members: Union[DimMember, DimMemberV12], 
        silent: bool = False
    ) -> 'AsyncDimension':
        """增加维度成员，

        新增的维度成员暂时维护在当前的维度对象中，
        调用 :meth:`save` 之后生效。

        Args:
            *members: 要增加的维度成员
            silent: 当维度成员名重复时，是报错还是静默处理。
                默认False，即报错处理。

        Returns:
            self
        """
        name_conflict = []
        for mbr in members:
            name = mbr.name
            if name in self._member_memo or name in self._add_memo:
                if not mbr.sharedmember:
                    name_conflict.append(name)
                else:
                    mbr.operation = ADD
                    self._add_memo.add(name, mbr)
            else:
                mbr.operation = ADD
                self._add_memo.add(name, mbr)

        if not silent and name_conflict:
            raise NameError(f"Member: {name_conflict} already exists.")
        return self

    def delete_member(self, *members: str, silent: bool = True) -> 'AsyncDimension':
        """删除维度成员

        如果删除的成员是共享节点，将删除所有共享节点。
        调用 :meth:`save` 之后生效。

        Args:
            *members: 要删除的维度 **成员名**
            silent: 当维度成员不存在时，是报错还是静默处理。
                默认True, 即静默处理。

        Returns:
            self

        See Also:
            :meth:`delete_shared_memeber`

        """
        mbr_not_found = []

        for member in members:
            self._del_memo.add(member, DimMember(name=member, operation=DEL))

            if member in self._member_memo:
                del self._member_memo[member]
            elif member in self._upd_memo:
                del self._upd_memo[member]
            elif member in self._add_memo:
                del self._add_memo[member]
            else:
                mbr_not_found.append(member)

        if self._strict and (not silent) and mbr_not_found:
            raise MemberNotFoundError(f"Member {mbr_not_found} does not exist.")
        return self

    def delete_shared_memeber(
        self,
        member: str,
        parent_name: Union[str, List[str]] = ROOT,
        silent: bool = True
    ) -> 'AsyncDimension':
        """删除共享维度成员

        删除指定父节点下的共享成员节点，
        调用 :meth:`save` 之后生效。

        Args:
            member: 要删除的维度 **成员名**
            parent_name: 共享节点的父节点名，默认为#root
            silent: 当维度成员不存在时，是报错还是静默处理。
                默认True, 即静默处理。

        """
        target_found = False
        new_value = []
        if isinstance(parent_name, str):
            parent_name = [parent_name]

        for dim_mbr in self._member_memo.getall(member, []):
            if dim_mbr.parent_name in parent_name:
                target_found = True
            else:
                new_value.append((member, dim_mbr))

        if not target_found and not silent:
            raise MemberNotFoundError(
                f"Cannot find shared member {member} with parent name: {parent_name}.")

        del self._member_memo[member]
        self._member_memo.extend(new_value)
        return self

    def reorder_members(
        self, 
        memo: CIMultiDict[Union[DimMember, DimMemberV12]], 
        complete: bool
    ) -> CIMultiDict[Union[DimMember, DimMemberV12]]:
        """成员重排序

        对维度成员按照先父节点后子节点的顺序排序

        Args:
            memo: 需要重排序的维度成员
            complete: memo里的成员是否是全部维度成员
        """
        parents = set(mbr.parent_name for mbr in memo.values())
        parents.discard(ROOT)
        all_mbr = set(memo.keys())
        unknown = parents - all_mbr

        if unknown and complete:
            raise DimensionSaveError(f"Missing parent node: {unknown}.")

        if self._strict:
            mbr_memo = self._member_memo
            if any((node := item) not in mbr_memo for item in unknown):
                raise DimensionSaveError(f"Missing parent node: {node}.")

        to_reorder = {}
        for member in memo.values():
            if member.parent_name == ROOT:
                to_reorder[member.name] = []
            else:
                to_reorder.setdefault(member.name, []).append(member.parent_name)

        ordered_keys = reversed(DAGraph(list(to_reorder.items())).topsort())

        ordered_mbrs = CIMultiDict()

        for k in ordered_keys:
            if k not in memo:
                continue

            for v in memo.getall(k):
                ordered_mbrs.add(k, v)

        # 补充孤立成员
        for k in set(memo.keys()).difference(set(ordered_mbrs.keys())):
            for v in memo.getall(k):
                ordered_mbrs.add(k, v)

        return ordered_mbrs

    async def save(
        self,
        reorder: bool = False
    ):
        """保存维度

        将对当前维度的修改保存至系统。

        Args:
            reorder: 是否对保存的元素进行重排序，将会损失性能。

        Note:
            由于目前维度保存接口的缺陷，如果保存数据中，父节点出现在
            子节点之后，父节点将不会被正常识别，从而导致保存失败。
            此方法最终调用保存接口的维度顺序将会和 :meth:`add_member` 的顺序一致，
            因此如果使用者自身能够保证维度的出现顺序，那么可以不使用reorder，
            否则应当开启。

        """
        if reorder:
            self._add_memo = self.reorder_members(self._add_memo, complete=False)

        await self._finalize_update()

        dim_members = []
        for v in chain(
            self._add_memo.values(),
            self._upd_memo.values(),
            self._del_memo.values()
        ):
            mbr = v
            if self.is_v1_0_api:
                mbr.index = mbr.index or 0
            else:
                mbr = self._maybe_rename_fields(v)
            dim_members.append(mbr.dict(exclude_none=True))

        if len(dim_members) > 0:
            if self.is_v1_0_api:
                payload = DimensionMemberChangeSaveSw.construct_from(
                    dimensionInfo=DimensionInfoSw(
                        name=self.element_info.elementName,
                        folderId=self.element_info.folderId,
                        isOnlyCheck='0'
                    ),
                    dimensionMemberList=dim_members
                )
                r = await self._incr_save_members(payload)
            else:
                r = await self._save_tree(
                    parse_obj_as(List[DimensionMemberOperationDto], dim_members)
                )
            self._add_memo.clear()
            self._del_memo.clear()
            self._upd_memo.clear()
            return r

    def _maybe_rename_fields(
        self,
        mbr: Union[
            DimensionMemberOperationSw,
            DimensionMemberOperationDto,
            Dict[str, str]
        ]
    ) -> Union[
        DimensionMemberOperationSw,
        DimensionMemberOperationDto,
        Dict[str, str]
    ]:
        """
        Maybe rename fields in V1.0 dimension mbr model
        to v1.1 & v1.2 model when current api is v1.1 or v1.2
        """
        if self.is_v1_0_api:
            return mbr

        if isinstance(mbr, DimensionMemberOperationDto):
            return mbr

        return_model = False
        if isinstance(mbr, DimensionMemberOperationSw):
            return_model = True
            mbr = mbr.dict(exclude_none=True)

        for old, new in V10_TO_V12.items():
            if old in mbr:
                mbr[new] = mbr.pop(old)

        if return_model:
            return DimMemberV12.construct_from(**mbr)

        return mbr

    async def _incr_save_members(self, payload: DimensionMemberChangeSaveSw):
        resp = await self.async_api.save.incremental(payload)
        if resp.errors:
            raise DimensionSaveError(f"Failed to save dimension. Detail: {resp}")
        return resp

    async def query(
        self,
        expression: str,
        fields: Union[List[str], Tuple[str]] = None,
        as_model: bool = True,
        role: Union[RoleStrategy, str] = None,
        role_name: str = None,
        role_group: str = None,
        multi_entity_config: List[Dict] = None
    ) -> Union[
        List[DimensionMemberBean], List[Dict[str, Any]], List[MultiEntityConfigResult]
    ]:
        """查询成员

        根据维度表达式查询维度成员

        Args:
            expression: 维度表达式
            fields: 需要查询的字段
            as_model: 是否把返回的结果转化为pydantic model
            role: 权限方案元素对象或权限方案名，提供时将带权限方案信息查询
            role_name: 角色名，默认为当前用户的角色信息
            role_group: 角色组名，默认为当前用户的角色信息
            multi_entity_config: 实体维度配置表过滤条件

        Important:
            - ``expression`` 可以不包含维度名，即: 如果当前维度是Entity，
              ``Entity{Base(#root,0)}`` 和 ``Base(#root,0)`` 是等价的。
            - 为保证接口正常调用， ``fields`` 将自动包含 ``name`` 属性。
            - ``as_model`` 参数可以影响本方法的返回类型，可以根据使用需要指定。

        .. admonition:: 示例

            如果希望将查询出的成员作为对象操作，推荐使用默认参数查询：

            .. code-block:: python

                dim = Dimension('dim_example')
                mbrs = dim.query('Base(#root,0)', fields=['ud1'])
                mbr = mbrs[0]
                ud1 = mbr.ud1
                name = mbr.name
                ...

            **注意：未查询的属性也能访问，但值固定是None**

            .. code-block:: python
                :emphasize-lines: 1

                assert mbrs.ud2 is None

            可以把上述查询结果转换为dataframe：

            .. code-block:: python
                :emphasize-lines: 1

                data = (mbr.dict(exclude_unset=True) for mbr in mbrs)
                df = pd.DataFrame(data=data)

            注意需要参数 ``exclude_unset=True`` 排除未查询到的数据。

            如果希望把查询数据转换为dataframe，更推荐使用以下方式：

            .. code-block:: python
                :emphasize-lines: 1,2

                dim = Dimension('dim_example')
                mbrs = dim.query('Base(#root,0)', fields=['ud1'], as_model=False)
                # 注意此时返回的数据类型不同
                assert isinstance(mbrs, List[dict])
                df = pd.DataFrame(data=mbrs)

            如果希望带权限方案查询，可用 ``role`` 、 ``role_name`` 以及 ``role_group`` 参数表示权限方案信息

            .. code-block:: python

                dim = Dimension('component')
                mbrs = dim.query('Descendant(East,0)', role='test_role', role_name='nonsense')

            此时会以权限方案test_role中的nonsense角色作为查询的角色信息，查询维度表达式：component{Descendant(East,0)}

            **注意：role_name和role_group若提供，则提供其一即可**

        Returns:
            - 如果 ``as_model == True``， 返回 :obj:`List[DimensionMemberBean]` 类型，
              不在查询fields中的属性将会被设置为None。
            - 如果 ``as_model == False``，返回 :obj:`List[Dict[str, Any]]` 类型，
              内部的字典将不包含未查询的属性

        """
        payload = self._get_query_payload(
            expression, fields, role, role_name, role_group, multi_entity_config
        )
        if self.is_v1_0_api:
            api_call = self.async_api.query.select_dimension_member_by_name_function
        elif (
            self.api.version == (1, 2)
            and as_model and multi_entity_config is not None
        ):
            api_call = functools.partial(
                self.async_api.extra.dimension_query_select_dimension_member_by_name_function,
                resp_model=List[MultiEntityConfigResult]
            )
        else:
            api_call = self.async_api.extra.dimension_query_select_dimension_member_by_name_function
        if as_model:
            return await api_call(payload)
        else:
            return await api_call(payload, resp_model=List[dict])

    def _get_query_payload(
        self,
        expression,
        fields,
        role=None,
        role_name=None,
        role_group=None,
        multi_entity_config=None
    ):
        if self.api.version == (1, 2):
            payload_cls = DimQueryExpr1_2
        else:
            payload_cls = DimQueryExpr

        role_params = {}

        if role is not None:
            if isinstance(role, str):
                role = AsyncRoleStrategy(element_name=role)

            rs_mapping = 1
            for dim in role.meta.dimensions:
                if (
                    dim.elementName == self.element_name
                    and dim.folderId == self.element_info.folderId
                ):
                    break
                rs_mapping += 1
            if rs_mapping > len(role.meta.dimensions):
                raise ValueError(
                    f"Current Dimension: {self.element_name} doesn't exist in "
                    f"role strategy: {role.element_name}."
                )

            role_params.update({'roleFolderId': role.element_info.folderId,
                                'rsMapping': rs_mapping,
                                'rsName': role.element_name})

            if role_name or role_group:
                role_params.update({'role': role_name, 'rolegroup': role_group})

        multi_entity_config_list = {}
        if multi_entity_config is not None and self.api.version == (1, 2):
            multi_entity_config_list['multiEntityConfigSearchDTOList'] = multi_entity_config

        if fields is not None:
            fields = set(fields).union([DFLT_NAME_COLUMN])
        else:
            fields = []
        dim, body = unpack_expr(expression, silent=True)
        if dim is None:
            dim = self.element_name
        expr = "%s{%s}" % (dim, body)
        payload = payload_cls.construct_from(
            dimensionMemberNames=expr,
            duplicate=True,
            ignoreIllegalMember=True,
            resultString=','.join(fields),
            web=False,
            folderId=self.element_info.folderId,
            reverse_order='0',
            **role_params,
            **multi_entity_config_list
        )
        return payload

    def update(self, member_name: str, **attrs: Any):
        """更新维度成员

        调用 :meth:`save` 之后生效。

        Args:
            member_name: 维度成员名

            **attrs: 成员属性，可接受参数参考:

                - 维度1.0 : :class:`DimMember`
                - 维度1.1或1.2 : :class:`DimMemberV12`

        Returns:
            self
        """
        attrs = self._maybe_rename_fields(attrs)
        if member_name in self._add_memo:
            upd_mbr = self._add_memo[member_name]
            if isinstance(upd_mbr, DimensionMemberOperationSw):
                self._add_memo[member_name] = DimMember.construct_from(
                    upd_mbr, **attrs
                )
            else:
                self._add_memo[member_name] = DimMemberV12.construct_from(
                    upd_mbr, **attrs
                )
        elif member_name in self._del_memo:
            raise MemberNotFoundError(f"Member: {member_name} does not exist.")
        elif self._strict and member_name not in self._member_memo:
            raise MemberNotFoundError(f"Member: {member_name} does not exist.")
        else:
            self._upd_memo.add(member_name, attrs)

        return self

    async def load_dataframe(
        self,
        dataframe: pd.DataFrame,
        strategy: Union[Strategy, str] = Strategy.incr_replace,
        reorder: bool = False,
        **langugage_keys: str
    ):
        """保存 ``DataFrame`` 数据至维度

        此方法不同于 :meth:`add_member`，:meth:`delete_member`
        等方法，保存结果将直接反映至系统，不需要再调用save。

        Args:
            dataframe: 包含维度数据的DataFrame
            strategy: 数据保存策略
            reorder: 是否对保存的元素进行重排序，将会损失性能。
            **langugage_keys: 维度成员描述（多语言）对应的列名

        Note:
            1. 数据保存策略可选参数如下：

            +--------------+--------------------------------------------+
            |     参数     |                    说明                    |
            +==============+============================================+
            | full_replace | 完全替换所有维度成员。                     |
            |              | 此策略将会删除所有已有维度成员，           |
            |              | 以dataframe为数据源新建维度成员。          |
            +--------------+--------------------------------------------+
            | incr_replace | 增量替换维度成员。                         |
            |              | 此策略不会删除已有维度成员。               |
            |              | 在保存过程中，如果遇到成员名重复的情况，   |
            |              | 会以dataframe数据为准，覆盖已有成员。      |
            +--------------+--------------------------------------------+
            |   keep_old   | 保留已有维度成员。                         |
            |              | 此策略在保存过程中，遇到成员名重复的情况， |
            |              | 会保留已有成员。其他与incr_replace相同。   |
            +--------------+--------------------------------------------+

            2. 目前描述支持两种语言: ``zh-cn, en``，此方法默认会在dataframe中寻找
            名为 ``'language_zh-cn', 'language_en'`` 的列，将其数据作为对应
            语言的描述。如果想改变这种默认行为，比如希望用'name'列作为中文语言描述，
            可以传入关键字参数: ``language_zh_cn='name'``。

        Warnings:
            - 目前由于技术原因，如果要保存共享维度成员，必须使用full_replace策略。
            - 如果传入的dataframe不含index列，将自动以0填充该列。

        """
        if dataframe.empty:
            return

        strategy = Strategy[strategy]
        df = dataframe.copy().reset_index(drop=True)
        if INDEX_FIELD not in df.columns and self.is_v1_0_api:
            df[INDEX_FIELD] = 0

        # validate dataframe
        _validate_df_for_dimension(df)

        # create language columns
        language_map = get_language_key_map(langugage_keys)
        for lan, key in language_map.items():
            if key in df.columns:
                df[lan] = df[key]

        # 合并描述列
        lan_columns = list(set(df.columns).intersection(ACCEPT_LANS))
        if lan_columns:
            df['multilingual'] = df[lan_columns].to_dict(orient='records')

        mbrcls = DimMember if self.is_v1_0_api else DimMemberV12

        if not self.is_v1_0_api:
            df = df.rename(columns=V10_TO_V12)

        # pick up valid columns
        valid_columns = list(
            set(mbrcls.__fields__).intersection(df.columns)
        )

        # save replace
        if strategy is Strategy.full_replace:
            member_list = df[valid_columns].to_dict(orient='records')
            return await self._save_replace(reorder, member_list)

        # split dataframe by existed data
        upd_df, add_df = await self._split_dimension_df(df[valid_columns])

        # modify operation column
        with self._local_memo():
            if strategy is Strategy.incr_replace:
                for record in upd_df.to_dict(orient='records'):
                    self._upd_memo.add(record[DFLT_NAME_COLUMN], record)

            for record in add_df.to_dict(orient='records'):
                self._add_memo.add(
                    record[DFLT_NAME_COLUMN],
                    mbrcls.construct_from(**record, operation=ADD)
                )

            return await self.save(reorder=reorder)

    async def _save_replace(
        self, reorder: bool, member_list: List[Dict[str, str]]
    ):
        mbrcls = DimMember if self.is_v1_0_api else DimMemberV12

        if reorder:
            mbrs = CIMultiDict()
            for rec in member_list:
                mbrs.add(rec[DFLT_NAME_COLUMN], mbrcls.construct_from(**rec))
            mbrs = self.reorder_members(mbrs, complete=True)
            member_list = [mbr.dict(exclude_none=True) for mbr in mbrs.values()]

        payload = DimMemberSave.construct_from(
            self.element_info,
            dimensionName=self.element_name,
            increment=0,
            dimensionMemberList=member_list
        )
        if self.is_v1_0_api:
            resp = await self.async_api.member.save(payload)
        elif self.api.version == (1, 1):
            resp = await self.async_api.save.save(payload)
        else:
            resp = await self.async_api.member.refactor_dimension_member_save(payload)

        if not resp.success:
            raise DimensionSaveError(f"Failed to save dimension. Detail: {resp}")

        return resp

    async def _finalize_update(self):
        upd_memo = self._upd_memo
        if not upd_memo:
            mbrs = []
        else:
            mbrs = await self.query(";".join(upd_memo.keys()))
        new_memo = CIMultiDict()

        for mbr in mbrs:
            # Use DimMember since query response model fits
            upd_mbr = DimMember.construct_from(mbr)
            upd_mbr.operation = UPD
            upd_mbr.origin_name = upd_mbr.name
            upd_mbr.origin_parent_name = upd_mbr.parent_name

            upd_mbr = self._maybe_rename_fields(upd_mbr)

            for attrs in upd_memo.getall(upd_mbr.name, []):
                if DFLT_NAME_COLUMN in attrs:
                    # 移除被改名的原始成员
                    self._member_memo.pop(upd_mbr.origin_name, None)

                # 更新属性
                for attr, val in attrs.items():
                    origin = getattr(upd_mbr, attr, None)
                    if isinstance(origin, dict):
                        if not isinstance(val, dict):
                            raise TypeError(
                                f"Update {attr} failed. "
                                f"Expect dict type, got {type(val)}.")
                        origin.update(val)
                    else:
                        setattr(upd_mbr, attr, val)

                new_memo.add(upd_mbr.name, upd_mbr)

        self._upd_memo = new_memo

    @contextmanager
    def _local_memo(self):
        upd_bak = self._upd_memo
        add_bak = self._add_memo
        del_bak = self._del_memo
        self._upd_memo = CIMultiDict()
        self._add_memo = CIMultiDict()
        self._del_memo = CIMultiDict()
        try:
            yield
        finally:
            self._upd_memo = upd_bak
            self._add_memo = add_bak
            self._del_memo = del_bak

    async def _split_dimension_df(
        self,
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        shared_mbr_col = SHAREDMEMBER
        pname_col = DFLT_PNAME_COLUMN
        if not self.is_v1_0_api:
            shared_mbr_col = SHAREDMEMBERV12
            pname_col = DFLT_PNAME_COLUMN_V12

        if shared_mbr_col not in df.columns:
            if self._strict:
                existed_mbrs = self._member_memo
            else:
                name_col = getattr(self.table_dimension.table, DFLT_NAME_COLUMN)
                dim_names = await self.table_dimension.select(
                    [DFLT_NAME_COLUMN],
                    distinct=True,
                    where=name_col.isin(df[DFLT_NAME_COLUMN].tolist())
                )
                existed_mbrs = set(dim_names[DFLT_NAME_COLUMN])
            existed_idx = df[DFLT_NAME_COLUMN].isin(existed_mbrs)
            return df.loc[existed_idx], df.loc[~existed_idx]

        # -----------------------------------------------------------------------------
        # has shared member
        df_shared: pd.DataFrame = df[df[shared_mbr_col].astype(bool)]
        if self._strict:
            existed_mbrs = self._member_memo

            dup_sharedmbrs = []
            for idx, row in df_shared.iterrows():
                for mbr in self._member_memo.getall(row[DFLT_NAME_COLUMN], []):
                    if mbr.sharedmember and mbr.parent_name == row[pname_col]:
                        dup_sharedmbrs.append(idx)
                        break
        else:
            name_col = getattr(self.table_dimension.table, DFLT_NAME_COLUMN)
            existed_df = await self.table_dimension.select(
                [DFLT_NAME_COLUMN, DFLT_PNAME_COLUMN, SHAREDMEMBER],
                distinct=True,
                where=name_col.isin(df[DFLT_NAME_COLUMN].tolist())
            )
            existed_mbrs = set(existed_df[DFLT_NAME_COLUMN].tolist())

            existed_shared: pd.DataFrame = existed_df.loc[
                existed_df[SHAREDMEMBER],
                [DFLT_NAME_COLUMN, DFLT_PNAME_COLUMN]
            ]

            shared_memo = set(tuple(item) for item in existed_shared.to_numpy())
            dup_sharedmbrs = []
            for idx, row in df_shared.iterrows():
                if (row[DFLT_NAME_COLUMN], row[pname_col]) in shared_memo:
                    dup_sharedmbrs.append(idx)

        # 在df中丢弃系统中已存在的共享节点
        df_shared_remain = df_shared[~df_shared.index.isin(dup_sharedmbrs)]

        df_not_shared = df[~df[shared_mbr_col].astype(bool)]
        existed_idx = df_not_shared[DFLT_NAME_COLUMN].isin(existed_mbrs)
        return df_not_shared.loc[existed_idx], \
            pd.concat([df_not_shared.loc[~existed_idx], df_shared_remain])

    async def to_deepmodel_object(
        self,
        object_name: str,
        expression: str = None,
        field_map: Dict[str, str] = None,
        full_replace: bool = False
    ):
        """维度成员导入至已有DeepModel对象

        Args:
            object_name: DeepModel对象名
            expression: 可选，维度成员表达式，默认为维度成员全集
            field_map: 可选，维度成员属性名与DeepModel对象字段名的映射关系
            full_replace: 是否全量替换，是，则会先清空DeepModel对象内数据后再导入

        """
        if expression is None:
            expression = "Descendant(#root,0)"

        data = await self.query(expression, as_model=False)
        data = pd.DataFrame(data)
        if field_map:
            data = data.rename(columns=field_map)

        # 父子关系与aggweight为层级关系所需信息
        parent = data[[DFLT_NAME_COLUMN, DFLT_PNAME_COLUMN, 'aggweight']]
        # parent_name为#root，即只作parent的记录
        parent = parent[~(parent[DFLT_PNAME_COLUMN] == '#root')]
        # 共享成员的父子关系重复，去重
        # 保证source -> target关系唯一性
        parent = parent.drop_duplicates(
            subset=[DFLT_NAME_COLUMN, DFLT_PNAME_COLUMN],
            keep='first'
        )
        parent = parent.rename(
            columns={DFLT_NAME_COLUMN: 'source', DFLT_PNAME_COLUMN: 'target'}
        )
        # 主数据排除共享成员
        data = data.drop_duplicates(subset=[DFLT_NAME_COLUMN], keep='first')
        from deepfos.element.deepmodel import AsyncDeepModel
        dm = AsyncDeepModel()
        async with dm.start_transaction():
            if full_replace:
                await dm.execute(f"delete {object_name}")
            await dm.insert_df(object_name, data, {'parent': parent})

    async def sync_data(self):
        """等效于调用DeepModel创建的维度的数据同步"""
        if self.async_api.version == (1, 2):
            return await self.async_api.object.sync_data(
                folderId=self.element_info.folderId,
                name=self.element_name
            )

        logger.warning("Only supported when Element Version is 1.2")

    async def update_parent(
        self,
        member_name: str,
        origin_parent: str,
        new_parent: str,
        shared_member: bool = False
    ):
        """修改系统已有维度成员的父级成员

        此方法不同于 :meth:`add_member`，:meth:`delete_member`
        等方法，保存结果将直接反映至系统，不需要再调用save。

        Args:
            member_name: 成员名
            origin_parent: 原父级成员名
            new_parent: 新父级成员名
            shared_member: 是否为共享成员，默认否


        """
        mbrs = [
            DimensionMemberOperationDto.construct_from(
                originParentName=origin_parent,
                originName=member_name,
                name=member_name,
                parentName=new_parent,
                operation=UPD,
                sharedMember=shared_member
            )
        ]
        return await self._save_tree(mbrs)

    async def update_parent_batch(
        self,
        dataframe: pd.DataFrame
    ):
        """批量修改系统已有维度成员的父级成员

        此方法不同于 :meth:`add_member`，:meth:`delete_member`
        等方法，保存结果将直接反映至系统，不需要再调用save。

        Args:
            dataframe: 批量修改信息的dataframe

        Note:
             dataframe需包含的信息：

            - member_name: 成员名
            - origin_parent: 原父级成员名
            - new_parent: 新父级成员名

            如需指定共享成员，则提供shared_member列用于区分是否为共享成员


        """
        if dataframe.empty:
            return

        required_cols = {'member_name', 'origin_parent', 'new_parent'}
        if lacked := required_cols.difference(dataframe.columns):
            raise DimensionSaveError(
                f"Required cols for update parent: {lacked} lacked."
            )

        fields = required_cols.union({'shared_member'})
        if 'shared_member' not in dataframe.columns:
            dataframe = dataframe.assign(shared_member=False)

        records = dataframe[list(fields)].to_dict(orient="records")
        mbrs = []
        for record in records:
            mbrs.append(
                DimensionMemberOperationDto.construct_from(
                    originParentName=record['origin_parent'],
                    originName=record['member_name'],
                    name=record['member_name'],
                    parentName=record['new_parent'],
                    operation=UPD,
                    sharedMember=record['shared_member']
                )
            )
        return await self._save_tree(mbrs)

    async def _save_tree(self, mbrs: List[DimensionMemberOperationDto]):
        if self.async_api.version == (1, 1):
            call_api = self.async_api.save.tree_save
        elif self.async_api.version == (1, 2):
            call_api = self.async_api.member.refactor_dimension_member_tree_save
        else:
            logger.warning("Only supported when Element Version is 1.1 or 1.2")
            return

        payload = DimensionMemberTreeSaveDto.construct_from(
            self.element_info,
            dimensionName=self.element_name,
            dimensionMemberList=mbrs
        )
        resp = await call_api(payload)
        if resp.errors:
            raise DimensionSaveError(f"Failed to save dimension. Detail: {resp}")


def _validate_df_for_dimension(df: pd.DataFrame):
    if DFLT_NAME_COLUMN not in df.columns:
        raise ValueError(f"Missing column [{DFLT_NAME_COLUMN}] in dataframe.")

    if df[DFLT_NAME_COLUMN].hasnans:
        null_index = df.loc[df[DFLT_NAME_COLUMN].isna()].index.values
        raise ValueError(
            f"You have null value in dataframe. "
            f"column: [{DFLT_NAME_COLUMN}], index: {null_index}.")

    col_parent_name = None
    col_shared_member = None

    if DFLT_PNAME_COLUMN in df.columns:
        col_parent_name = DFLT_PNAME_COLUMN
    elif DFLT_PNAME_COLUMN_V12 in df.columns:
        col_parent_name = DFLT_PNAME_COLUMN_V12

    if SHAREDMEMBER in df.columns:
        col_shared_member = SHAREDMEMBER
    elif SHAREDMEMBERV12 in df.columns:
        col_shared_member = SHAREDMEMBERV12

    if col_parent_name is None:
        raise ValueError(f"Missing column [{DFLT_PNAME_COLUMN}] or [{DFLT_PNAME_COLUMN_V12}] in dataframe.")

    if col_shared_member is not None:
        unique_df = df.groupby(
            [DFLT_NAME_COLUMN, col_parent_name, col_shared_member],
            as_index=False
        ).size()
        duplicated = unique_df[unique_df['size'] > 1]
        if not duplicated.empty:
            raise ValueError(
                f"Duplicated member name for: {duplicated.to_dict(orient='records')}"
            )
    else:
        if df[DFLT_NAME_COLUMN].nunique() != len(df):
            counter = Counter(df[DFLT_NAME_COLUMN])
            duplicated = [k for k, v in counter.items() if v > 1]
            raise ValueError(f"Duplicated member name for: {duplicated}")


class Dimension(AsyncDimension, metaclass=SyncMeta):
    synchronize = (
        'save',
        'load_dataframe',
        'query',
        'to_deepmodel_object',
        'sync_data',
        'update_parent',
        'update_parent_batch',
    )

    if TYPE_CHECKING:
        def save(
            self,
            reorder: bool = False
        ):  # pragma: no cover
            ...

        def load_dataframe(
            self,
            dataframe: pd.DataFrame,
            strategy: Union[Strategy, str] = Strategy.incr_replace,
            reorder: bool = False,
            **langugage_keys: str
        ):  # pragma: no cover
            ...

        def query(
            self,
            expression: str,
            fields: Union[List[str], Tuple[str]] = None,
            as_model: bool = True,
            role: Union[RoleStrategy, str] = None,
            role_name: str = None,
            role_group: str = None,
            multi_entity_config: List[Dict] = None
        ) -> Union[
            List[DimensionMemberBean],
            List[Dict[str, Any]],
            List[MultiEntityConfigResult]
        ]:  # pragma: no cover
            ...

        def to_deepmodel_object(
            self,
            object_name: str,
            expression: str = None,
            field_map: Dict[str, str] = None,
            full_replace: bool = False
        ):  # pragma: no cover
            ...

        def sync_data(self):  # pragma: no cover
            ...

        def update_parent(
            self,
            member_name: str,
            origin_parent: str,
            new_parent: str,
            shared_member: bool = False
        ):  # pragma: no cover
            ...

        def update_parent_batch(
            self,
            dataframe: pd.DataFrame
        ):  # pragma: no cover
            ...
        