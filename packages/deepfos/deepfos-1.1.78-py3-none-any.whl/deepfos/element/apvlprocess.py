from typing import List, Dict, Optional, Union, Tuple, TYPE_CHECKING, Any  # noqa

from .base import ElementBase, SyncMeta
from .datatable import (DataTableMySQL, get_table_class, AsyncDataTableMySQL,
                        T_AsyncDatatableInstance, T_DatatableInstance)
from deepfos.lib.decorator import cached_property
from deepfos.lib.constant import UNSET
from deepfos.api.approval_process import ApprovalProcessAPI
from deepfos.api.models.approval_process import (
    ProcessOperationDto, OperationRecordDto,
    ApprovalRecordVo, QueryRecordDto, ProcessConfigureVo, OperationRecordVo
)
from deepfos.lib.asynchronous import future_property


__all__ = [
    'AsyncApprovalProcess',
    'ApprovalProcess',
]


class AsyncApprovalProcess(ElementBase[ApprovalProcessAPI]):
    """审批流"""
    @future_property
    async def meta(self) -> ProcessConfigureVo:
        """审批流的元配置信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        meta = await api.configure.query(
            folderId=ele_info.folderId,
            elementName=self.element_name
        )
        del meta.processInfo.controlInfo.style
        return meta

    @cached_property
    def record_table(self) -> T_DatatableInstance:
        """审批记录表"""
        ctrl_info = self.meta.processInfo.controlInfo
        if (ele_type := ctrl_info.approvalRecordTableElementType) is None:
            cls = DataTableMySQL
        else:
            cls = get_table_class(ele_type)
        return cls(
            element_name=ctrl_info.approvalRecordTableName,
            folder_id=ctrl_info.approvalRecordTableFolderId,
            path=ctrl_info.approvalRecordTablePath
        )

    @cached_property
    def async_record_table(self) -> T_AsyncDatatableInstance:
        """审批记录表"""
        ctrl_info = self.meta.processInfo.controlInfo
        if (ele_type := ctrl_info.approvalRecordTableElementType) is None:
            cls = AsyncDataTableMySQL
        else:
            cls = get_table_class(ele_type, sync=False)
        return cls(
            element_name=ctrl_info.approvalRecordTableName,
            folder_id=ctrl_info.approvalRecordTableFolderId,
            path=ctrl_info.approvalRecordTablePath
        )

    @cached_property
    def _name2opinfo(self) -> Dict[str, ProcessOperationDto]:
        return {
            op_info.name: op_info
            for op_info in self.meta.processInfo.operationInfo
        }

    def get_operation_id(
        self,
        operation: str,
        default: Any = UNSET,
    ) -> str:
        """获取审批操作id

        根据审批操作编码获取操作id，当查询的审批操作
        不存在时，如果传入default，将返回default值，
        否则抛出 `KeyError` 。

        Args:
            operation: 审批操作编码
            default: 默认值

        Returns:
            审批操作id

        """
        if operation not in self._name2opinfo:
            if default is not UNSET:
                return default
            raise KeyError(
                f"Unknown operation: {operation} "
                f"for approval process: {self.element_name}")
        return self._name2opinfo[operation].id

    async def operate(
        self,
        primary_kv: Dict[str, Union[str, int]],
        operation: str = None,
        operation_id: str = None,
        remark: str = '',
        roles: List[str] = None,
        origin_status: str = None,
    ) -> OperationRecordVo:
        """操作审批流

        根据审批数据和审批操作来操作审批流，如果不提供初始审批状态，
        会查询当前的审批状态作为初始状态。

        Args:
            primary_kv: 审批数据的键值对
            operation: 审批操作编码（界面可获取）
            operation_id: 审批操作id
            remark: 备注
            roles: 角色方案
            origin_status: 初始审批状态

        Returns:
            审批操作结果

        """
        if operation_id is not None:
            op_id = operation_id
        elif operation is not None:
            op_id = self.get_operation_id(operation)
        else:
            raise ValueError('None of argumnet [operation_id, operation] is set.')

        if roles is None:
            roles = [-1]

        if origin_status is None:
            records = await self.get_record(primary_kv, roles)
            origin_status = records[0].result_status

        return await self.async_api.operation.record(OperationRecordDto(
            folderId=self.element_info.folderId,
            pcName=self.element_name,
            processOperationId=op_id,
            primaryKeyValue=primary_kv,
            remark=remark,
            roles=roles,
            originStatus=origin_status
        ))

    async def get_record(
        self,
        primary_kv: Dict[str, Any],
        roles: List[str] = None,
    ) -> List[ApprovalRecordVo]:
        """获取审批记录列表

        根据审批数据获取所有审批记录，
        审批记录按时间倒序排列

        Args:
            primary_kv: 审批数据键值对
            roles: 角色

        Returns:
            审批记录列表

        """
        if roles is None:
            roles = [-1]

        return await self.async_api.operation.get_record(QueryRecordDto(
            folderId=self.element_info.folderId,
            pcName=self.element_name,
            roles=roles,
            primaryKeyValue=primary_kv
        ))

    def get_operation_info(self, operation: str) -> ProcessOperationDto:
        """获取审批操作所有信息

        根据审批操作编码获取操作信息，当查询的审批操作
        不存在时，会报错

        Args:
            operation: 审批操作编码

        Returns:
            审批操作id

        """
        return self._name2opinfo[operation]


class ApprovalProcess(AsyncApprovalProcess, metaclass=SyncMeta):
    synchronize = (
        'operate',
        'get_record',
    )

    if TYPE_CHECKING:
        def operate(
            self,
            primary_kv: Dict[str, Union[str, int]],
            operation: str = None,
            operation_id: str = None,
            remark: str = '',
            roles: List[str] = None,
            origin_status: str = None,
        ) -> OperationRecordVo:  # pragma: no cover
            ...

        def get_record(
            self,
            primary_kv: Dict[str, Any],
            roles: List[str] = None,
        ) -> List[ApprovalRecordVo]:  # pragma: no cover
            ...
