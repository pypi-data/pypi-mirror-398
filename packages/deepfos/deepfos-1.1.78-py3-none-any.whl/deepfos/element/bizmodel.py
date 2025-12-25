import datetime

from collections import UserDict, defaultdict
from typing import (
    List, Dict, Optional, Union, TYPE_CHECKING, Any
)
from itertools import zip_longest
from pypika.terms import Term, EmptyCriterion
import pandas as pd
from enum import Enum, IntFlag

from .base import ElementBase, SyncMeta
from .apvlprocess import AsyncApprovalProcess
from deepfos.lib.decorator import cached_property, deprecated
from deepfos.lib.utils import SettableOnce, LazyList, FrozenClass, dict_to_sql
from deepfos.lib.constant import UNSET
from deepfos.api.business_model import BusinessModelAPI
from deepfos.api.models.business_model import (
    BusinessModelDTORes as BizModel,
    StructureDTO as TableStructure,
    PartitionDTO, AuthorityDTO,
    BusinessModelApproveDTO
)
from deepfos.api.V1_1.models.business_model import (
    ModelDataSaveDTO, ModelDataTableDTO, ModelDataNoChildTableDTO,
    ModelDataReturnDTO, ModelDataColumnsDTO,
)
from deepfos.core.logictable import MetaTable, BaseTable
from deepfos.options import OPTION
from deepfos.db.utils import get_client_class
from .datatable import txn_support  # noqa
from deepfos.lib.asynchronous import future_property
from deepfos.exceptions import ElementVersionIncompatibleError

__all__ = [
    'BusinessModel',
    'AsyncBusinessModel',
    'CopyConfig'
]


# -----------------------------------------------------------------------------
# utils
def dataframe_to_records(
    df: pd.DataFrame,
    column_key: str = "columnName",
    value_key: str = "value",
) -> Dict[int, List[Dict[str, Any]]]:
    tr = df.T.reset_index()
    width = len(tr.columns)
    tr.columns = [column_key] + [value_key] * (width - 1)
    records = (
        tr.iloc[:, [0, i]].to_dict('records')
        for i in range(1, width)
    )
    return dict(zip(df.index, records))


class TableNode(MetaTable):
    table_structure: Optional[TableStructure] = None
    name: Optional[str] = None


def create_table(struct: TableStructure, parent: BaseTable = None) -> TableNode:
    tbl_element = struct.dataTableInfo.elementDetail
    attr = {'table_info': {
        'element_name': tbl_element.elementName,
        'element_type': tbl_element.elementType,
        'folder_id': tbl_element.folderId,
        'path': tbl_element.path,
        'table_name': struct.dataTableInfo.actualTableName,
        'server_name': tbl_element.serverName,
    }}
    if parent is not None:
        attr.update({
            'parent': {
                "cls": parent,
                "on": tuple(asoc.logicTableFk for asoc in struct.associations),
                "alias": tuple(asoc.parentPk for asoc in struct.associations),
            }
        })
    tbl = TableNode(f"{struct.dataTableName}_{struct.uuid}", (), attr)
    tbl.table_structure = struct
    tbl.name = struct.dataTableName
    return tbl


class Operator(str, Enum):
    ADD = 'ADD'
    DEL = 'DELETE'
    UPD = 'UPDATE'


class AllowDetach(IntFlag):
    none = 0
    data = 1
    table = 1 << 1
    all = data | table


class CopyConfig(UserDict):
    """业务模型数据拷贝的配置类"""
    def load_config(self, conf: Dict[str, Dict]):
        for table, copy_conf in conf.items():
            self.data[table] = tbl_conf = {}
            if "where" not in copy_conf:
                raise KeyError("Field 'where' is missing in copy configure.")
            tbl_conf["where"] = copy_conf["where"]
            tbl_conf["field_map"] = copy_conf.get("field_map")
        return self.data

    def set_config(
        self,
        table: str,
        where: Union[str, Term, EmptyCriterion],
        field_map: Dict[str, Union[str, int, FrozenClass, Term]] = None
    ):
        """
        设置单表数据行的拷贝配置

        Args:
            table: 表名
            where: 配置条件
            field_map: key：需要复制的字段，value：需要复制的值

        Note:
            配置用作 :meth:`.DataTableMySQL.copy_rows` 的入参

        See Also:
             :meth:`.DataTableMySQL.copy_rows`

        """
        self.data[table] = tbl_conf = {}
        tbl_conf["where"] = where
        tbl_conf["field_map"] = field_map


# -----------------------------------------------------------------------------
# core classes
class LogicTable(UserDict):
    if TYPE_CHECKING:
        data: Dict[str, TableNode] = {}

    def __getitem__(self, item: str) -> TableNode:
        """for type hint only"""
        try:
            return super().__getitem__(item)
        except KeyError:
            raise KeyError(f'No datatable named: {item}.') from None

    def release_all(self):
        for tbl in self.data.values():
            if tbl.locked:
                tbl.release()

    root: TableNode = SettableOnce()


class AsyncBusinessModel(ElementBase[BusinessModelAPI]):
    """业务模型"""
    if TYPE_CHECKING:
        from deepfos.api.V1_1.business_model import BusinessModelAPI as V1_1  # noqa
        api: Union[BusinessModelAPI, V1_1]

    approval_class = AsyncApprovalProcess

    def __init__(
        self,
        element_name: str,
        folder_id: str = None,
        path: str = None,
        server_name: str = None,
    ):
        self.__tables: Dict[str, TableNode] = {}
        self.__logic_tables = LogicTable()
        self.__dflt_ptn_id = UNSET
        super().__init__(element_name, folder_id, path, server_name)

    @cached_property
    def default_partition_id(self) -> Optional[str]:
        """默认分区id

        **最后一个** 配置了审批流的审批区域id，如果没有配置
        审批流，则返回 `None`
        """
        if self.__dflt_ptn_id is UNSET:
            _ = self.approval_process
        return self.__dflt_ptn_id

    @future_property
    async def meta(self) -> BizModel:
        """业务模型的元数据信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        r = await api.model.query(
            folderId=ele_info.folderId,
            elementName=self.element_name
        )
        return r.businessModel

    @future_property
    async def _meta_logic_table(self) -> TableStructure:
        """内部逻辑使用：业务模型的元数据信息-主表信息(logicTable)"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        r = await api.configure.structure_top(
            folderId=ele_info.folderId,
            elementName=self.element_name
        )
        return r

    @future_property
    async def _meta_sub_models(self) -> List[PartitionDTO]:
        """内部逻辑使用：业务模型的元数据信息-子模型信息(subModels)"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        r = await api.configure.partitions(
            folderId=ele_info.folderId,
            elementName=self.element_name
        )
        return r

    @cached_property
    def logic_tables(self) -> LogicTable:
        """以逻辑表格式存储的业务模型数据表

        每个数据表都继承自 :class:`MetaTable` ，
        并且各个数据表之间已经按照业务模型配置设置好了关联关系。
        """
        if not self.__logic_tables:
            self._table_init()
        return self.__logic_tables

    @cached_property
    def table_memo(self) -> Dict[str, TableNode]:
        """数据表uuid -> 逻辑表表节点的字典

        See Also:
            :attr:`logic_tables`
        """
        if not self.__tables:
            self._table_init()
        return self.__tables

    @future_property
    async def permission(self) -> AuthorityDTO:
        """权限配置信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.permission.query(
            elementName=self.element_name,
            folderId=ele_info.folderId
        )

    def _table_init(self):
        """
        根据业务模型的配置，初始化所有数据表信息
        """
        # bfs
        tbl_to_visit = [(None, self._meta_logic_table)]
        while tbl_to_visit:
            parent, tbl = tbl_to_visit.pop(0)
            table = create_table(tbl, parent)
            if not self.__logic_tables:
                # set root
                self.__logic_tables.root = table
            self.__logic_tables[tbl.dataTableName] = table
            self.__tables[tbl.uuid] = table
            tbl_to_visit.extend(zip_longest([], tbl.children, fillvalue=table))

    @cached_property
    def sub_models(self) -> Dict[str, PartitionDTO]:
        """子模型信息

        模型id -> 子模型详细配置
        """
        return {
            model.partitionId: model
            for model in self._meta_sub_models
        }

    @cached_property
    def approval_process(self) -> Dict[str, LazyList[AsyncApprovalProcess]]:
        """模型配置的审批流信息"""
        candidates = {}
        self.__dflt_ptn_id = None
        apvl_cls = self.__class__.approval_class
        for partition in self.permission.statusColumn:
            partition_id = partition.partitionId
            for status_info in partition.statusInfo:
                if status_info.pcName:
                    appv_list = candidates.setdefault(partition_id, LazyList())
                    appv_list.append(
                        apvl_cls,
                        element_name=status_info.pcName,
                        folder_id=status_info.pcFolderId,
                    )
                    # 有有效的审批流配置，把当前id设为默认的partition id
                    self.__dflt_ptn_id = partition_id
        return candidates

    @cached_property
    def _partition_map(self) -> Dict[str, str]:
        return {
            part.partitionName: part.partitionId
            for part in self.permission.statusColumn
        }

    def _get_table_from_partition(
        self,
        partition_id: str
    ) -> TableStructure:
        if partition_id in self.sub_models:
            model = self.sub_models[partition_id]
            return self.table_memo[model.uuid].table_structure
        else:
            return self.logic_tables.root.table_structure

    async def set_approval(
        self,
        primary: Union[str, Dict[str, str]],
        operation: str = None,
        operation_id: str = None,
        partition_name: str = None,
        partition_id: str = None,
        remark: str = '',
        roles: List[str] = None,
        origin_status: str = None,
        main_primary_kv: Dict[str, str] = None,
    ):
        """
        设置审批流

        Args:
            primary: 审批模型主表的业务主键值或者键值对，用于定位审批数据
            operation: 审批操作编码（界面可获取）
            operation_id: 审批操作id
            partition_name: 审批分区编码（如子模型编码，无子模型可不传）
            partition_id: 分区id
            remark: 备注
            roles: 角色
            origin_status: 初始审批状态
            main_primary_kv: 主模型业务主键值或者键值对

        Hint:
            关于入参有以下注意点：

            - 审批的模型的业务主键仅一个字段时，primary可以仅提供一个值，
              超过一个字段时，必须以字典格式提供。
            - ``operation`` 和 ``operation_id`` 二选一，``operation``
              可直接在界面获取，``operation_id`` 则需要通过F12查看具体数据，
            - ``partition_name`` 和 ``partition_id`` 可二选一，也可都不提供。
              不提供的情况下，会以 **最后一个** 配置了审批流的审批区域为默认值。
              可以通过 :attr:`default_partition_id` 查看分区id。
            - ``origin_status`` 在已知情况下推荐填写，不填则会导致额外的接口请求，
              使用当前最后一条审批记录对应的审批状态。
            - ``main_primary_pk`` 参数在审批主模型时不需要填写。如果审批的是子模型，
              并且子模型主表与主模型主表的关联字段包含所有主模型的业务主键，也可以不提供。
              其余情况，必须提供此参数。

        Attention:
            partition_id默认会加入primary中用于审批流操作

        """
        # -----------------------------------------------------------------------------
        # resolve partition_id
        ptn_id = self._resolve_partition_id(partition_id, partition_name)
        # -----------------------------------------------------------------------------
        # format argument primary
        is_sub = ptn_id in self.sub_models
        main_table = self.logic_tables.root
        main_logic_keys = main_table.table_structure.logicKeyList or []

        if is_sub:
            appv_table = self.table_memo[self.sub_models[ptn_id].uuid]
            logic_keys = appv_table.table_structure.logicKeyList or []
        else:
            appv_table = main_table
            logic_keys = main_logic_keys

        primary = self._ensure_primary_kv_dict(appv_table, logic_keys, primary)
        # 加入分区信息
        primary.update(partition_id=ptn_id)

        # -----------------------------------------------------------------------------
        # create main_primary_kv
        if main_primary_kv is None:
            if not is_sub:
                main_primary_kv = {**primary}
            elif missing_keys := (set(main_logic_keys) - set(logic_keys)):
                raise ValueError(f"Missing primary keys for main model: {missing_keys}. ")
            else:
                main_primary_kv = {k: primary[k] for k in main_logic_keys}

        # -----------------------------------------------------------------------------
        # get operation id and orignal status for approval
        if operation_id is None and operation is None:
            raise ValueError('None of argumnet [operation_id, operation] is set.')

        if operation_id is None or origin_status is None:
            if len(self.approval_process[ptn_id]) != 1:
                raise ValueError(f"Only one approval process is supported.")
            appv = self.approval_process[ptn_id][0]

            if origin_status is None:
                appv_records = await appv.get_record(primary, roles)
                origin_status = appv_records[0].result_status
            if operation_id is None:
                operation_id = appv.get_operation_id(operation)

        return await self.async_api.approval.operation(BusinessModelApproveDTO(
            businessModelName=self.element_name,
            businessModelFolderId=self.element_info.folderId,
            originStatus=origin_status,
            partitionId=ptn_id,
            primaryKeyValue=primary,
            mainModelPrimaryKey=main_primary_kv,
            remark=remark,
            processOperationId=operation_id
        ))

    @staticmethod
    def _ensure_primary_kv_dict(
            table: TableNode,
            primary_keys: List[str],
            primary_kv: Union[Any, Dict[str, Any]],
            copy: bool = True
    ) -> Dict[str, Any]:
        if isinstance(primary_kv, str):
            if len(primary_keys) == 1:
                primary_kv = {primary_keys[0]: primary_kv}
            else:
                raise ValueError(
                    f"Table: {table.name} has more than one primary key: {primary_keys}. "
                    f"Thus argument: `primary` must be type of dict[field, value]."
                )
        elif copy:
            primary_kv = {**primary_kv}
        return primary_kv

    async def copy_rows(
        self,
        config: Union[CopyConfig, Dict]
    ):
        """
        对模型表做数据拷贝

        Args:
            config: 拷贝的配置

        Example:
            入参config可以为字典类型，满足以下格式：

            .. code-block:: python

                config = {
                    "table_name": {
                        "where": WhereCondition,
                        "field_map": {k: v, ...}
                    },
                    ...
                }

            也可以使用 :class:`CopyConfig`

            .. code-block:: python

                config = CopyConfig()
                config.set_config(
                    table="table_name",
                    where=WhereCondition,
                    field_map={k: v, ...}
                )

        Note:
            本方法实际循环调用了数据表元素的 :meth:`.DataTableMySQL.copy_rows`
            方法，入参配置应当符合该方法

        See Also:
            :meth:`.DataTableMySQL.copy_rows`

        """

        if isinstance(config, Dict):
            config = CopyConfig().load_config(config)

        for table, conf in config.items():
            dt = self.logic_tables[table].async_datatable
            await dt.copy_rows(**conf)

    @deprecated(
        replacement='set_approval_ex',
        version=(1, 0, 38)
    )
    async def set_approval_batch(
        self,
        operation_name: Union[str, List[str]],
        main_primary_kv: Union[
            pd.DataFrame,
            Dict[str, list],
            Dict[str, Union[str, int]],
            List[Dict[str, str]]
        ],
        partition_name: str = None,
        partition_id: str = None,
        remark: str = None,
        origin_status: str = None
    ) -> Dict[str, pd.DataFrame]:
        """设置审批流（已废弃）

        Args:
            operation_name: 审批操作编码
            main_primary_kv: 主模型业务主键值或者键值对
            partition_name: 审批分区编码（如子模型编码，无子模型可不传）
            partition_id: 分区id
            remark: 备注
            origin_status: 初始审批状态

        Hint:
            关于入参有以下注意点：

            - ``operation`` 和 ``operation_id`` 二选一，``operation``
              可直接在界面获取，``operation_id`` 则需要通过F12查看具体数据.
              尽量不要使用operation_id，根据审批流operation_id会变化
            - ``partition_name`` 和 ``partition_id`` 可二选一，也可都不提供.
              不提供的情况下，会以 **最后一个** 配置了审批流的审批区域为默认值.
              可以通过 :attr:`default_partition_id` 查看分区id.
            - ``origin_status`` 审批流初始化可以不传递，其他审批操作必须传.
              传入``'start', 'init', '0'`` 也会认为是初始化，如果不需要该特性，
              请使用 :meth:`set_approval_ex`
            - ``main_primary_pk`` 必须提供此参数.

        Attention:
            注意本方法不会调用审批流前后置python

        Example:
            .. code-block:: python

                init_process = BusinessModel(name='a', path='/')
                ids = '001'
                ids = ['001','002']   # (批量）
                res = init_process.set_approval_batch(
                    operation_name=['start','staff_submit'],
                    main_primary_key={"PaymentApplyCode": ids}
                )

        See Also:
            :meth:`set_approval_ex`

        """
        # -----------------------------------------------------------------------------
        if origin_status in ('0', 'start', 'init'):
            origin_status = None
        return await self.set_approval_ex(
            operation_name=operation_name,
            main_primary_kv=main_primary_kv,
            partition_name=partition_name,
            partition_id=partition_id,
            remark=remark,
            origin_status=origin_status
        )

    async def set_approval_ex(
        self,
        operation_name: Union[str, List[str]],
        main_primary_kv: Union[
            pd.DataFrame,
            Dict[str, list],
            Dict[str, Union[str, int]],
            List[Dict[str, str]]
        ],
        partition_name: str = None,
        partition_id: str = None,
        remark: str = None,
        origin_status: str = None
    ) -> Dict[str, pd.DataFrame]:
        """设置审批流

        Args:
            operation_name: 审批操作编码
            main_primary_kv: 主模型业务主键值或者键值对
            partition_name: 审批分区编码（如子模型编码，无子模型可不传）
            partition_id: 分区id
            remark: 备注
            origin_status: 初始审批状态

        Hint:
            关于入参有以下注意点：

            - ``operation`` 和 ``operation_id`` 二选一，``operation``
              可直接在界面获取，``operation_id`` 则需要通过F12查看具体数据.
              尽量不要使用operation_id，根据审批流operation_id会变化
            - ``partition_name`` 和 ``partition_id`` 可二选一，也可都不提供.
              不提供的情况下，会以 **最后一个** 配置了审批流的审批区域为默认值.
              可以通过 :attr:`default_partition_id` 查看分区id.
            - ``origin_status`` 审批流初始化可以不传递，其他审批操作必须传.
            - ``main_primary_pk`` 必须提供此参数.

        Attention:
            注意本方法不会调用审批流前后置python

        Example:
            .. code-block:: python

                init_process = BusinessModel(name='a', path='/')
                ids = '001'
                ids = ['001','002']   # (批量）
                res = init_process.set_approval_ex(
                    operation_name=['start','staff_submit'],
                    main_primary_key={"PaymentApplyCode": ids}
                )
        """
        # -----------------------------------------------------------------------------
        if isinstance(operation_name, str):
            operation_name = [operation_name]
        elif not isinstance(operation_name, list):
            raise TypeError("operation_name参数只能为str或list类型")

        if not isinstance(main_primary_kv, pd.DataFrame):
            if isinstance(main_primary_kv, dict):
                val = list(main_primary_kv.values())[0]
                if not isinstance(val, list):
                    main_primary_kv = [main_primary_kv]
            elif not isinstance(main_primary_kv, list):
                raise TypeError("main_primary_key参数只能为pd.DataFrame或dict或list类型")
            try:
                main_primary_kv = pd.DataFrame(main_primary_kv)
            except Exception:  # noqa
                raise TypeError("main_primary_keys参数数据结构异常") from None
        if main_primary_kv.empty:
            raise ValueError('main_primary_keys参数不能为空')
        # -----------------------------------------------------------------------------
        # 获取partition_id
        ptn_id = self._resolve_partition_id(partition_id, partition_name)
        pc = self.approval_process[ptn_id][0]
        tbl_pc = pc.async_record_table

        # -----------------------------------------------------------------------------
        main_primary_kv.dropna(inplace=True)
        df_main_key = main_primary_kv.copy()
        key_cols = main_primary_kv.columns.to_list()
        col, where_sql, on_sql = self._create_sql(main_primary_kv, tbl_pc.quote_char)
        df_operation = pd.DataFrame()
        for operation in operation_name:
            operation_info = pc.get_operation_info(operation)
            df_row = pd.DataFrame([{'process_operation_id': operation_info.id,
                                    'origin_status': operation_info.originStatusList,
                                    'target_status': operation_info.targetStatus}])
            df_operation = pd.concat([df_operation, df_row])
        df_operation.reset_index(drop=True, inplace=True)
        if len(df_operation) > 1:
            df_operation['target_status_shift'] = df_operation['target_status'].shift(1)
            if not (df_operation.loc[1:, 'target_status_shift'] ==  # noqa
                    df_operation.loc[1:, 'origin_status']).all():
                raise ValueError('多个审批操作operation_name不连续')
        if origin_status != df_operation.loc[0, 'origin_status']:
            raise ValueError('当前审批操作与origin_status状态不匹配')
        user = OPTION.api.header['user']
        sql = f"""
        SELECT
            a.* 
        FROM
        {tbl_pc.table_name} a
        INNER JOIN ( SELECT {tbl_pc.quote_char}{col}{tbl_pc.quote_char}, 
        max(line_no) AS line_no FROM {tbl_pc.table_name} 
        WHERE {where_sql} GROUP BY {tbl_pc.quote_char}{col}{tbl_pc.quote_char} ) b 
        ON {on_sql} AND a.line_no = b.line_no;
        """
        actual_cli = get_client_class(tbl_pc.api.module_type, sync=False)()
        df_query = await actual_cli.query_dfs(sql)
        if origin_status is None:
            # 初始化的处理
            if df_query.empty:
                df_success = df_main_key
                df_failure = pd.DataFrame()
            else:
                df_success = df_main_key.merge(df_query, how='left', on=key_cols)
                df_failure = df_success.loc[~df_success['line_no'].isnull()]
                df_success = df_success.loc[df_success['line_no'].isnull()]
            df_success['line_no'] = 0
        else:
            if df_query.empty:
                df_success = pd.DataFrame()
                df_failure = df_main_key
            else:
                df_success = df_query.loc[df_query['result_status'] == origin_status]
                df_failure = df_query.loc[df_query['result_status'] != origin_status]
        time = datetime.datetime.now()
        if not df_success.empty:
            partition = self.models_permission[ptn_id]
            partition_id = partition['partition_id']
            pc_field = partition['pc_field']
            main_tbl_name = partition['main_tbl_name']
            df_success = df_success.assign(pc_remark=remark, operate_user=user, operate_time=time,
                                           partition_id=partition_id)
            df_insert = pd.DataFrame()
            for ind, row in df_operation.iterrows():
                # 取出当前状态正确的行，补齐新状态后，行号加一，插库
                df_success['line_no'] += 1
                df_success['result_status'] = row['target_status']
                df_success['process_operation_id'] = row['process_operation_id']
                df_insert = pd.concat([df_insert, df_success])

            tbl_main = self.logic_tables[main_tbl_name].async_datatable
            if not df_failure.empty:
                _, where_sql, _ = self._create_sql(df_success[key_cols], tbl_main.quote_char)
            sql_update = f"update {tbl_main.table_name} set " \
                         f"{tbl_main.quote_char}{pc_field}{tbl_main.quote_char}={row['target_status']!r} " \
                         f"where {where_sql}"
            async with tbl_main.start_transaction():
                await tbl_pc.insert_df(df_insert)
                await txn_support(tbl_main.__class__.run_sql)(tbl_main, sql_update)
            df_success = df_insert
        return {'success': df_success, 'failure': df_failure}

    def _resolve_partition_id(self, partition_id, partition_name):
        if partition_id is not None:
            ptn_id = partition_id
        elif partition_name is not None:
            ptn_id = self._partition_map.get(partition_name, None)
            if ptn_id is None:
                raise ValueError(
                    f"Cannot resolve partition_id from "
                    f"given partition_name: {partition_name}"
                )
        else:
            ptn_id = self.default_partition_id
            if ptn_id is None:
                raise ValueError(
                    "Cannot resolve partition_id because no approval "
                    "process has been set for current model."
                )
        return ptn_id

    @staticmethod
    def _create_sql(df, quote_char):
        # 统一repr一下
        df = df.applymap(lambda x: repr(x))
        if df.shape[1] == 1:
            col = df.columns[0]
            in_val = ",".join(df[col])
            where_sql = f"{quote_char}{col}{quote_char} IN ({in_val})"
            on_sql = f"a.{quote_char}{col}{quote_char}=b.{quote_char}{col}{quote_char}"
        else:
            col = f"{quote_char},{quote_char}".join(df.columns)
            df = df.apply(lambda x: quote_char + x.name + f'{quote_char}=' + x, axis=0)
            df.iloc[:, :-1] += ' AND '  # 除了最后一列，每列尾加AND
            data_series = "(" + df.sum(axis=1) + ")"
            where_sql = " | ".join(data_series)
            on_sql = " AND ".join([f"a.{quote_char}{col}{quote_char}=b.{quote_char}{col}{quote_char}" for col in df.columns])
        return col, where_sql, on_sql

    @cached_property
    def models_permission(self) -> Dict[str, Dict[str, str]]:
        """ 模型审批对象 """
        result = {}
        columns = self.permission.statusColumn
        for status_column in columns:
            res_row = {'partition_id': status_column.partitionId}
            for status_info in status_column.statusInfo:
                if (status_info.isStatusColumn == 1) and (status_info.pcName is not None):
                    res_row['pc_field'] = status_info.columnName
                    res_row['main_tbl_name'] = status_info.dataTableName
                    res_row['main_tbl_folder_id'] = status_info.tableFolderId
                    break
            if status_column.partitionName == "主模型":
                result['0'] = res_row
            else:
                result[status_column.partitionId] = res_row

        return result

    def _ensure_version_greater_than(self, target):
        if self.api.version < target:
            ver_str = '.'.join(map(str, target))
            raise ElementVersionIncompatibleError(
                f'Expect version > {ver_str}, got {self.api.version}')

    @staticmethod
    def _structurize_dataframe(
        table: TableNode,
        data: pd.DataFrame,
        operator: Operator = Operator.ADD,
    ) -> Dict[int, ModelDataTableDTO]:
        if (parent := table.parent) is None:
            parent_info = None
        else:
            struct: TableStructure = parent.table_structure
            parent_info = ModelDataNoChildTableDTO(
                dataTableFolderId=struct.folderId,
                dataTableName=struct.dataTableName,
            )
        return {
            idx: ModelDataTableDTO(
                operateType=Operator.ADD,
                children=[],
                columns=columns,  # noqa
                dataTableFolderId=table.table_structure.folderId,
                dataTableName=table.table_structure.dataTableName,
                parentTableInfo=parent_info,
            )
            for idx, columns in dataframe_to_records(data).items()
        }

    @staticmethod
    def _validate_detached(
        data_map: Dict[str, pd.DataFrame],
        attached_idxes: Dict[TableNode, List[int]],
        allow_detached_data: bool = True,
        allow_detached_table: bool = False,
    ):
        allow_detached = AllowDetach.none
        if allow_detached_data:
            allow_detached |= AllowDetach.data
        if allow_detached_table:
            allow_detached |= AllowDetach.table

        if (
            not (AllowDetach.table in allow_detached)
            and (detached := (data_map.keys() - set(t.name for t in attached_idxes)))
        ):
            raise ValueError(f"Cannot attach table: {detached}")

        if not (AllowDetach.data in allow_detached):
            for tbl, indexes in attached_idxes.items():
                orig_df = data_map[tbl.name]

                if len(indexes) != len(orig_df):
                    detached_idx = orig_df.index.difference(indexes)
                    raise ValueError(
                        f"Cannot attach following data for table {tbl.name}:\n"
                        f"{orig_df.loc[detached_idx]}"
                    )

    def build_save_data(
        self,
        data_map: Dict[str, pd.DataFrame],
        table: TableNode = None,
        attached_idxes: Dict[TableNode, List[int]] = None,
        allow_detached_data: bool = True,
        allow_detached_table: bool = False,
    ) -> List[ModelDataTableDTO]:
        if table is None:
            table = self.logic_tables.root
        model_data = self._structurize_dataframe(table, data_map[table.name])

        if attached_idxes is None:
            attached_idxes: Dict[TableNode, List[int]] = defaultdict(list)

        attached_idxes[table].extend(data_map[table.name].index)

        def visit(node: TableNode, data_wrapper: Dict[int, ModelDataTableDTO]):
            orig_df = data_map[node.name]
            child: TableNode

            for idx, data in data_wrapper.items():
                df_record = orig_df.iloc[idx, :]

                for child in node.children:
                    if (child_df := data_map.get(child.name)) is None:
                        continue

                    rel_parent_cols = list(node.rel_info[child])
                    rel_child_val = tuple(df_record.loc[rel_parent_cols])
                    rel_child_cols = child.rel_info[node]

                    rel_child = dict(zip(rel_child_cols, rel_child_val))
                    query = dict_to_sql(rel_child, eq='==', bracket=False)
                    picked_child_df = child_df.query(query)

                    if not picked_child_df.empty:
                        attached_idxes[child].extend(picked_child_df.index)
                        child_dw = self._structurize_dataframe(child, picked_child_df)
                        data.children.extend(child_dw.values())
                        visit(child, child_dw)

        visit(table, model_data)
        self._validate_detached(
            data_map, attached_idxes,
            allow_detached_table=allow_detached_table,
            allow_detached_data=allow_detached_data,
        )
        return list(model_data.values())

    async def save(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        allow_detached_data: bool = True,
        allow_detached_table: bool = False,
        auto_format: bool = True,
        check_db: bool = True,
        check_logical: bool = True,
        check_field: bool = True,
        enable_pre_save: bool = True,
        enable_post_save: bool = True,
    ) -> List[ModelDataReturnDTO]:
        """保存数据

        使用业务模型数据保存接口进行数据保存，相较于直接操作数据表，
        可以使用业务模型自带的数据和权限校验，并且可以触发保存前后置逻辑（可选）

        Args:
            data: 保存数据
            allow_detached_data: 是否允许data中存在无合法关联关系的数据
            allow_detached_table: 是否允许data中存在无法关联的数据表
            auto_format: 是否需要处理关联关系、冗余字段等（接口功能）
            check_db: 是否需要数据库属性校验（接口功能）
            check_logical: 是否需要逻辑属性校验（接口功能）
            check_field: 是否需要进行字段权限校验（接口功能）
            enable_pre_save: 是否开启保存前置逻辑（接口功能）
            enable_post_save:  是否开启保存后置逻辑（接口功能）

        .. admonition:: 示例

            例如有业务模型结构如下：

            .. code-block::

                <ROOT>
                    ├── <A>
                    |   └── <A1>
                    └── <B>

            4张数据表均包含2个字段 ``name, parent``，
            其中子表的 ``parent`` 与父表的 ``name`` 字段关联。

            如果需要保存 ``<ROOT>, <A>`` 表的数据：

            .. code-block:: python

                df_ROOT = pd.DataFrame([
                    {'name': "R0"}, {'name': "R1"},
                ])

                df_A = pd.DataFrame([
                    {'name': "A00", "parent": "R0"},
                    {'name': "A10", "parent": "R1"},
                    {'name': "A11", "parent": "R1"},
                ])

                model = BusinessModel('Tree')
                model.save({'ROOT': df_ROOT, 'A': df_A})

        Note:
            - 如果业务模型仅一张数据表，``data`` 可以是 :class:`DataFrame` 格式，
              其余情况，必须是 ``数据表名 -> 保存数据`` 的字典结构
            - 此方法要求保存数据完整，即数据必须由模型主表（根节点）开始，如果需要追加数据，
              请使用 :meth:`attach`
            - 参数中的 ``allow_detached_xxx`` ，所谓 ``detached`` 是指数据或数据表没有合理归属

                以示例中的业务模型结构为例，假如传入的 ``data`` 只包含 ``<ROOT>, <A1>`` 两张表，
                由于缺乏 ``A`` 表延续关联关系，``A1`` 表会被认为是 ``detached table`` 。
                类似地，如果示例中保存的 ``A`` 表数据中，有一行 ``parent = 'R2'``，由于 ``<ROOT>``
                中并没有对应数据，这一行数据就会被认为是 ``detached data``

        Returns:
            保存结果

        See Also:
            :meth:`attach`

        """
        self._ensure_version_greater_than((1, 1))

        logic_tables = self.logic_tables
        root_tblname = logic_tables.root.name

        if isinstance(data, pd.DataFrame):
            if len(logic_tables.data) > 1:
                raise ValueError(
                    "'data' of type 'Dataframe' is only supported "
                    "on model containing single datatable.")
            else:
                data = {logic_tables.root.name: data}

        if root_tblname not in data:
            raise ValueError(
                f"Missing root table {root_tblname!r} in data")

        # ------------------------------------------------------------
        # normalize index
        normalized_data = {
            table: df.reset_index(drop=True)
            for table, df in data.items()
        }

        payload = ModelDataSaveDTO(
            data=self.build_save_data(
                normalized_data,
                allow_detached_table=allow_detached_table,
                allow_detached_data=allow_detached_data,
            ),
            databaseCheck=check_db,
            formatData=auto_format,
            logicCheck=check_logical,
            fieldCheck=check_field,
            savePre=enable_pre_save,
            savePost=enable_post_save,
            elementName=self.element_name,
            folderId=self.element_info.folderId,
        ).dict(exclude_none=True)

        return await self.async_api.data.save(payload)  # noqa

    async def attach(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        primary_kv: Union[Any, Dict[str, Any]],
        parent_kv: Union[Any, Dict[str, Any]] = None,
        allow_detached_data: bool = True,
        allow_detached_table: bool = False,
        check_db: bool = True,
        check_logical: bool = True,
        check_field: bool = True,
        enable_pre_save: bool = True,
        enable_post_save: bool = True,
    ) -> List[ModelDataReturnDTO]:
        """追加数据

        使用业务模型数据保存接口进行数据保存，
        允许将数据作为明细数据追加至已有的主数据上。

        Args:
            data: 保存数据
            primary_kv: 主表业务主键值或者键值对
            parent_kv: 追加数据所属父级表的业务主键值或者键值对
                （父级表不是模型主表时必须提供）
            allow_detached_data: 是否允许data中存在无合法关联关系的数据
            allow_detached_table: 是否允许data中存在无法关联的数据表
            check_db: 是否需要数据库属性校验（接口功能）
            check_logical: 是否需要逻辑属性校验（接口功能）
            check_field: 是否需要进行字段权限校验（接口功能）
            enable_pre_save: 是否开启保存前置逻辑（接口功能）
            enable_post_save:  是否开启保存后置逻辑（接口功能）


        .. admonition:: 示例

            例如有业务模型结构如下：

            .. code-block::

                <ROOT>
                    ├── <A>
                    |   └── <A1>
                    └── <B>

            4张数据表均包含2个字段 ``name, parent``，
            其中子表的 ``parent`` 与父表的 ``name`` 字段关联。

            如果需要保存 ``<A>, <A1>`` 表的数据、作为 ``<ROOT>`` 表 ``name=R0``
            的明细数据：

            .. code-block:: python

                df_A = pd.DataFrame([
                    {'name': "A00"},
                    {'name': "A10"},
                    {'name': "A11"}
                ])
                df_A1 = pd.DataFrame([
                    {'name': "A00_1", "parent": "A00"},
                    {'name': "A10_1", "parent": "A10"},
                ])

                model = BusinessModel('Tree')
                model.attach({'A': df_A, 'A1': df_A1}, {'name': 'R0'})

            其中，由于指定 ``A`` 表数据挂在 ``<ROOT>`` 表 ``name=R0`` 上，
            其关联字段 ``parent`` 的数据可以省略（即使提供也不会生效，固定以 ``R0`` 落库）

        Returns:
            保存结果

        See Also:
            :meth:`save`

        """
        self._ensure_version_greater_than((1, 1))

        logic_tables = self.logic_tables
        root = logic_tables.root

        if isinstance(data, pd.DataFrame):
            if len(logic_tables.data) != 2:
                raise ValueError(
                    "'data' of type 'Dataframe' is only supported "
                    "on model containing 2 datatables.")
            else:
                data = {root.children[0].name: data}

        # ------------------------------------------------------------
        # check primary kv
        pks = root.table_structure.logicKeyList
        primary_kv = self._ensure_primary_kv_dict(root, pks, primary_kv, copy=False)

        if missing_pk := set(pks) - primary_kv.keys():
            raise ValueError(f"Missing primary key: {missing_pk} in 'primary_kv'")

        # -----------------------------------------------------------------------------
        # set parent kv
        data_root = sorted(
            (logic_tables[n] for n in data),
            key=lambda t: t.depth
        )[0].parent

        if data_root is root:
            parent_kv = primary_kv
        elif parent_kv is None:
            raise ValueError("Missing 'parent_kv' while attaching to a non-root table.")
        else:
            parent_kv = self._ensure_primary_kv_dict(
                data_root,
                data_root.table_structure.logicKeyList,
                parent_kv, copy=False
            )

        # ------------------------------------------------------------
        # normalize index
        normalized_data: Dict[str, pd.DataFrame] = {
            table: df.reset_index(drop=True)
            for table, df in data.items()
        }

        attached_idxes = defaultdict(list)
        save_data = []

        for child in data_root.children:
            if (child_df := normalized_data.get(child.name)) is None:
                continue
            drop_cols = [
                c for c in child.rel_info[data_root]
                if c in child_df.columns
            ]
            normalized_data[child.name] = child_df.drop(columns=drop_cols)

            save_data.extend(self.build_save_data(
                normalized_data,
                table=child,
                attached_idxes=attached_idxes,
                allow_detached_table=True,
                allow_detached_data=True,
            ))

        self._validate_detached(
            normalized_data, attached_idxes,
            allow_detached_table=allow_detached_table,
            allow_detached_data=allow_detached_data,
        )

        # ---------------------------------------------------------------
        # attach parentLogicKeyColumns
        attach_at = [
            ModelDataColumnsDTO(
                columnName=k,
                value=v
            )
            for k, v in parent_kv.items()
        ]
        for sd in save_data:
            sd.parentLogicKeyColumns = attach_at

        payload = ModelDataSaveDTO(
            data=save_data,
            databaseCheck=check_db,
            formatData=True,
            logicCheck=check_logical,
            fieldCheck=check_field,
            savePre=enable_pre_save,
            savePost=enable_post_save,
            elementName=self.element_name,
            folderId=self.element_info.folderId,
            mainKeyList=[primary_kv]
        ).dict(exclude_none=True)

        return await self.async_api.data.save(payload)  # noqa


class BusinessModel(AsyncBusinessModel, metaclass=SyncMeta):
    synchronize = (
        'set_approval',
        'set_approval_batch',
        'set_approval_ex',
        'save',
        'attach',
        'copy_rows'
    )

    if TYPE_CHECKING:  # pragma: no cover
        def set_approval(
            self,
            primary: Union[str, Dict[str, str]],
            operation: str = None,
            operation_id: str = None,
            partition_name: str = None,
            partition_id: str = None,
            remark: str = '',
            roles: List[str] = None,
            origin_status: str = None,
            main_primary_kv: Dict[str, str] = None,
        ):
            ...

        def set_approval_batch(
            self,
            operation_name: Union[str, List[str]],
            main_primary_kv: Union[
                pd.DataFrame,
                Dict[str, list],
                Dict[str, Union[str, int]],
                List[Dict[str, str]]
            ],
            partition_name: str = None,
            partition_id: str = None,
            remark: str = None,
            origin_status: str = None
        ) -> Dict[str, pd.DataFrame]:
            ...

        def set_approval_ex(
            self,
            operation_name: Union[str, List[str]],
            main_primary_kv: Union[
                pd.DataFrame,
                Dict[str, list],
                Dict[str, Union[str, int]],
                List[Dict[str, str]]
            ],
            partition_name: str = None,
            partition_id: str = None,
            remark: str = None,
            origin_status: str = None
        ) -> Dict[str, pd.DataFrame]:
            ...

        def save(
            self,
            data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
            allow_detached_data: bool = True,
            allow_detached_table: bool = False,
            auto_format: bool = True,
            check_db: bool = True,
            check_logical: bool = True,
            check_field: bool = True,
            enable_pre_save: bool = True,
            enable_post_save: bool = True,
        ) -> List[ModelDataReturnDTO]:
            ...

        def attach(
            self,
            data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
            primary_kv: Union[Any, Dict[str, Any]],
            parent_kv: Union[Any, Dict[str, Any]] = None,
            allow_detached_data: bool = True,
            allow_detached_table: bool = False,
            check_db: bool = True,
            check_logical: bool = True,
            check_field: bool = True,
            enable_pre_save: bool = True,
            enable_post_save: bool = True,
        ) -> List[ModelDataReturnDTO]:
            ...

        def copy_rows(
            self,
            config: Union[CopyConfig, Dict]
        ):
            ...
