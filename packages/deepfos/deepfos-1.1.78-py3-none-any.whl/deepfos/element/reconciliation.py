from functools import cached_property
from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING

from deepfos.api.models.reconciliation_engine import (
    QueryColumnDataItem,
    CanDoParam,
    ElementBaseInfoParam,
    AccountInfoParam,
    ConfirmItem,
    ReconciliationExecDto,
    OffTaskItem,
    OnTaskItem,
    DeleteTaskItem,
    ReconSignByHand,
    CancelSignByHand,
    CancelReconMatch,
    ReconciliationExecCreate,
    CancelItem,
    DeleteDsItem
)
from deepfos.api.reconciliation_engine import ReconcilationAPI, ReconcilationmsAPI
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.lib.asynchronous import future_property


__all__ = [
    'ReconciliationEngine',
    'AsyncReconciliationEngine',
    'ReconciliationMsEngine',
    'AsyncReconciliationMsEngine',
    'AccountInfoParam'
]


class AsyncReconciliationEngine(ElementBase[ReconcilationAPI]):
    """对账引擎-数据集"""

    @future_property
    async def _base_info(self) -> ElementBaseInfoParam:
        """对账引擎的元素信息"""
        api = await self.wait_for('async_api')
        element_info = await self.wait_for('element_info')
        return ElementBaseInfoParam(
            elementName=self.element_name,
            elementType=element_info.elementType,
            folderId=element_info.folderId,
            moduleId=api.module_id
        )

    async def extract_data(
        self,
        param: List[Union[AccountInfoParam, Dict]] = None,
        cleanup: Optional[bool] = False,
        auto_confirm: Optional[bool] = False,
        batch_id: str = None,
        batch_name: str = None
    ) -> int:
        """抽取业务数据

        Args:
            param: 执行参数
            cleanup: 是否清理数据
            auto_confirm: 是否执行完自动确认
            batch_id: 执行批次ID
            batch_name: 执行批次名称

        .. admonition:: 示例

            1.以自定义数据选取参数执行

            .. code-block:: python

                auto_process = ReconciliationEngines('ds_bank')
                auto_process.extract_data(param=[
                    {'code':'day','defaultValue':'day01',"valueType":1}
                ])


            2.以默认参数执行

            .. code-block:: python

                auto_process.extract_data()

        """
        return await self.async_api.data_get.get_column_data(QueryColumnDataItem(
            canDoParam=CanDoParam(isClean=cleanup, isConfirm=auto_confirm),
            dsBatchId=batch_id,
            dsBatchName=batch_name,
            elementBaseInfoParamTable=self._base_info,
            params=param or []
        ))

    async def confirm(self, *ids: str) -> Any:
        """确认批次
        
        Args:
            ids: 未确认的批次id

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationEngines('ds_bank')
                auto_process.confirm('D20230413161618371', 'D20230413161615376')

        """
        return await self.async_api.data_get.confirm_ds_batch(ConfirmItem(
            dsIds=','.join(ids),
            elementBaseInfoParamData=self._base_info
        ))

    async def cancel(self, *ids: str) -> Any:
        """取消批次
            
        Args:
            ids: 已确认的批次id

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationEngines('ds_bank')
                auto_process.cancel('D20230413161618371', 'D20230413161615376')
        
        """
        return await self.async_api.data_get.cancel_ds(CancelItem(
            dsIds=','.join(ids),
            elementBaseInfoParamData=self._base_info
        ))

    async def delete(self, *ids: str) -> Any:
        """删除批次
        
        Args:
            ids: 未确认批次id

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationEngines('ds_bank')
                auto_process.delete('D20230413161618371', 'D20230413161615376')
        
        """
        return await self.async_api.data_get.delete_ds_batch(DeleteDsItem(
            dsIds=','.join(ids),
            elementBaseInfoParamData=self._base_info
        ))


class ReconciliationEngine(AsyncReconciliationEngine, metaclass=SyncMeta):
    synchronize = (
        'extract_data',
        'confirm',
        'cancel',
        'delete',
    )
    if TYPE_CHECKING:
        def extract_data(
            self,
            param: List[AccountInfoParam, Dict] = None,
            cleanup: Optional[bool] = False,
            auto_confirm: Optional[bool] = False,
            batch_id: str = None,
            batch_name: str = None
        ) -> int:
            ...

        def confirm(self, *ids: str) -> Any:
            ...

        def cancel(self, *ids: str) -> Any:
            ...

        def delete(self, *ids: str) -> Any:
            ...


class AsyncReconciliationMsEngine(ElementBase[ReconcilationmsAPI]):
    """对账引擎_数据集"""
    @cached_property
    def _base_info(self) -> ElementBaseInfoParam:
        """对账引擎的元素信息"""
        return ElementBaseInfoParam(
            elementName=self.element_name,
            elementType=self.element_info.elementType,
            folderId=self.element_info.folderId,
            moduleId=self.api.module_id
        )

    async def execute(
        self,
        pov: Dict[str, str],
        params: AccountInfoParam = None,
        task_id: str = None,
        task_name: str = None
    ) -> int:
        """创建对账任务并执行
        
        Args:
            pov: 开启分块pov信息
            params: 执行参数，创建必填
            task_id: 对账任务id，不为空表示执行旧的对账
            task_name: 对账任务名称，对账id为空，用来新建对账任务

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.execute(pov={'entity': "S001"})

        See Also:
            如果需要分布执行创建和执行任务，可以使用：

                - 创建任务： :meth:`create_task`
                - 执行任务： :meth:`exec_task`

        """
        return await self.async_api.reconcil.reconciliation(ReconciliationExecDto(
            elementBaseInfoParam=self._base_info,
            params=params or [],
            povParams=pov,
            rcTaskId=task_id,
            rcTaskName=task_name
        ))

    async def create_task(
        self,
        pov: Dict[str, str] = None,
        auto_run: bool = False,
        params: AccountInfoParam = None,
        task_id: str = None,
        task_name: str = None
    ) -> int:
        """创建对账任务

        Args:
            pov: 开启分块pov信息，开启必传
            auto_run: 是否开启后自动执行
            params: 执行参数，创建必填
            task_id: 对账任务id，不为空表示执行旧的对账
            task_name: 对账任务名称，对账id为空，用来新建对账任务

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.create_task(
                    pov={'entity': "S001"},
                    auto_run=False,
                    task_name="testc042301"
                )

        """
        return await self.async_api.reconcil.create_task(ReconciliationExecCreate(
            autoRunning=auto_run,
            elementBaseInfoParam=self._base_info,
            params=params or [],
            povParams=pov,
            rcTaskId=task_id,
            rcTaskName=task_name
        ))

    async def exec_task(
        self,
        task_id: str,
        pov: Dict[str, str] = None,
        params: AccountInfoParam = None,
        task_name: str = None
    ) -> int:
        """执行对账

        Args:
            pov: 开启分块pov信息，开启必传
            params: 执行参数，创建必填
            task_id: 对账任务id，不为空表示执行旧的对账
            task_name: 对账任务名称，对账id为空，用来新建对账任务

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.exec_task('T20230423102835188')

        See Also:
            如果想创建并执行对账任务，可以使用 :meth:'execute'

        """
        return await self.async_api.reconcil.exec_task(ReconciliationExecDto(
            elementBaseInfoParam=self._base_info,
            params=params or [],
            povParams=pov,
            rcTaskId=task_id,
            rcTaskName=task_name
        ))

    async def close_task(self, *task_ids: str) -> Any:
        """关闭对账任务

        Args:
            task_ids: 对账任务id

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.close_task("T20230417171442358")

        """
        return await self.async_api.reconcil.off_task(OffTaskItem(
            rcTaskIds=list(task_ids),
            reconElement=self._base_info
        ))

    async def open_task(self, task_id: str) -> Any:
        """打开对账任务

        Args:
            task_id: 对账任务id

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.open_task("T20230417171442358")

        """
        return await self.async_api.reconcil.on_task(OnTaskItem(
            rcTaskId=task_id,
            reconElement=self._base_info
        ))

    async def delete_task(self, *task_ids: str) -> Any:
        """删除对账任务

        Args:
            task_ids: 对账任务id

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.delete_task("T20230417171442358")

        """
        return await self.async_api.reconcil.delete_task(DeleteTaskItem(
            rcTaskIds=list(task_ids),
            reconElement=self._base_info
        ))

    async def mark_by_hand(
        self,
        task_id: str,
        type: int,
        reason: str,
        base_data_ids: List[str] = None,
        cpr_data_ids: List[str] = None,
        description: str = None,
    ) -> bool:
        """手工标记对账集

        Args:
            task_id: 匹配批次id
            type: 操作类型
            reason: 原因
            description: 说明
            base_data_ids: 选择的基础数据ids
            cpr_data_ids: 选择的对比数据集ids

        Hint:
            ``type`` 可选值如下

            +------+------------+
            | 参数 | 说明       |
            +======+============+
            | 4    | 手工匹配   |
            +------+------------+
            | 6    | 暂挂       |
            +------+------------+
            | 5    | 不参与匹配 |
            +------+------------+


        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.mark_by_hand(
                    'T20230417181208780',
                    type='6',
                    reason='timing_difference',
                    base_data_ids=["08GTWH000002", "08GTWH000003"],
                    description='说明'
                )

        """
        return await self.async_api.balance.mark_by_hand(ReconSignByHand(
            baseDataIds=base_data_ids or [],
            cprDataIds=cpr_data_ids or [],
            rcTaskId=task_id,
            description=description,
            reason=reason,
            reconElement=self._base_info,
            type=str(type)
        ))

    async def cancel_by_hand(
        self,
        task_id: str,
        type: int,
        base_data_ids: List[str] = None,
        cpr_data_ids: List[str] = None,
    ) -> int:
        """手工取消暂挂或者不参与匹配

        Args:
            task_id: 匹配批次id
            type: 操作类型: 0 取消挂起 1 取消不参与匹配
            base_data_ids: 选择的基础数据ids
            cpr_data_ids: 选择的对比数据集ids

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.cancel_by_hand(
                    'T20230417181208780',
                    type=0,
                    base_data_ids=["08GTWH000002", "08GTWH000003"],
                )
        """
        return await self.async_api.balance.cancel_by_hand(CancelSignByHand(
            baseDataIds=base_data_ids or [],
            cprDataIds=cpr_data_ids or [],
            rcTaskId=task_id,
            reconElement=self._base_info,
            type=type
        ))

    async def cancel_matched(
        self,
        task_id: str,
        match_ids: List[str],
    ) -> int:
        """取消匹配

        Args:
            task_id: 匹配批次id
            match_ids: 匹配id

        .. admonition:: 示例

            .. code-block:: python

                auto_process = ReconciliationMsEngines('ms_3')
                auto_process.cancel_recon_match(
                    'T20230417181208780',
                    match_ids=["M000000033"]
                )

        """
        return await self.async_api.balance.cancel_recon_match(CancelReconMatch(
            matchIds=match_ids,
            rcTaskId=task_id,
            reconElement=self._base_info
        ))


class ReconciliationMsEngine(AsyncReconciliationMsEngine, metaclass=SyncMeta):
    synchronize = (
        'execute',
        'create_task',
        'exec_task',
        'close_task',
        'open_task',
        'delete_task',
        'mark_by_hand',
        'cancel_by_hand',
        'cancel_matched',
    )
    if TYPE_CHECKING:  # pragma: no cover
        def execute(
            self,
            pov: Dict[str, str],
            params: AccountInfoParam = None,
            task_id: str = None,
            task_name: str = None
        ) -> int:
            ...

        def create_task(
            self,
            pov: Dict[str, str] = None,
            auto_run: bool = False,
            params: AccountInfoParam = None,
            task_id: str = None,
            task_name: str = None
        ) -> int:
            ...

        def exec_task(
            self,
            task_id: str,
            pov: Dict[str, str] = None,
            params: AccountInfoParam = None,
            task_name: str = None
        ) -> int:
            ...

        def close_task(self, *task_ids: str) -> Any:
            ...

        def open_task(self, task_id: str) -> Any:
            ...

        def delete_task(self, *task_ids: str) -> Any:
            ...

        def mark_by_hand(
            self,
            task_id: str,
            type: int,
            reason: str,
            base_data_ids: List[str] = None,
            cpr_data_ids: List[str] = None,
            description: str = None,
        ) -> bool:
            ...

        def cancel_by_hand(
            self,
            task_id: str,
            type: int,
            base_data_ids: List[str] = None,
            cpr_data_ids: List[str] = None,
        ) -> int:
            ...

        def cancel_matched(
            self,
            task_id: str,
            match_ids: List[str],
        ) -> int:
            ...
