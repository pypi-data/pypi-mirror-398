from functools import partial
from typing import *

import pandas as pd

from deepfos.api.models import compat_parse_obj_as as parse_obj_as
from deepfos.api.models.platform import FileUplodRes
from deepfos.api.models.workflow import *
from deepfos.api.workflow import WorkFlowAPI
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.lib.asynchronous import future_property
from deepfos.lib.utils import fetch_all_pages, CIEnum

__all__ = [
    'CompareType',
    'StatusType',
    'AsyncWorkFlow',
    'WorkFlow',
]


class ScopeType(CIEnum):
    all_subscriber = "ALL_SUBSCRIBER"
    process_instance = "PROCESS_INSTANCE"


class CompareType(CIEnum):
    equal = "EQUAL"
    like = "LIKE"


class StatusType(CIEnum):
    #: 进行中
    in_progress = "InProgress"
    #: 已完成
    completed = "Completed"
    #: 已终止
    terminated = "Terminated"


def _get_record_count(response: Union[UnderwayPageInfo, TodoPageInfo, PageInfo]):
    if response.lists is None:
        return 0
    return len(response.lists)


# -----------------------------------------------------------------------------
# core
class AsyncWorkFlow(ElementBase[WorkFlowAPI]):
    """工作流"""
    @future_property
    async def all_version(self) -> List[ProcessVersionVO]:
        """所有版本信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.version_control.list(
            self.element_name,
            ele_info.folderId
        )

    @future_property
    async def msg_list(self) -> List[Message]:
        """消息列表"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.message.list(ele_info)

    @future_property
    async def global_params(self) -> List[Value]:
        """全局变量"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.instance.global_params(ele_info)

    @future_property
    async def launch_params(self) -> List[ProcessLaunchParamsVO]:
        """启动参数"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.process.launch_params(
            self.element_name, ele_info.folderId
        )

    async def _send_msg(
        self,
        msg_code: str,
        msg_body: Dict[str, Any],
        processes: List[str] = None,
        scope: ScopeType = ScopeType.all_subscriber
    ):
        scope_info = MessageScope(type=ScopeType.all_subscriber)

        if scope == ScopeType.process_instance:
            scope_info = MessageScope(
                processInstanceIds=processes,
                type=ScopeType.process_instance
            )

        return await self.async_api.process.send_message(
            SendMessageParam(
                messageInfo=MessageInfo(
                    messageBody=msg_body,
                    messageCode=msg_code,
                    relateProcess=self.element_info
                ),
                scope=scope_info
            )
        )

    async def broadcast(self, msg_code: str, msg_body: Dict[str, Any]):
        """广播发送消息至所有订阅者

        Args:
            msg_code: 消息编码，消息编码全集信息来自消息列表
            msg_body: 消息体，消息体格式信息来自消息列表

        See Also:
            :attr:`msg_list`, 用于查看当前工作流的消息列表
            :func:`send_msg_to_processes`, 发送消息至流程实例列表

        """
        if msg_code is None:
            raise ValueError("msg_code不可为空")

        return await self._send_msg(msg_code, msg_body)

    async def send_msg_to_processes(
        self,
        msg_code: str,
        msg_body: Dict[str, Any],
        processes: List[str]
    ):
        """发送消息至流程实例列表

        Args:
            msg_code: 消息编码，消息编码全集信息来自消息列表
            msg_body: 消息体，消息体格式信息来自消息列表
            processes: 目标流程实例id列表

        See Also:
            :attr:`msg_list`, 用于查看当前工作流的消息列表
            :func:`broadcast`, 广播发送消息至所有订阅者

        """
        if msg_code is None:
            raise ValueError("msg_code不可为空")

        return await self._send_msg(msg_code, msg_body, processes, ScopeType.process_instance)

    async def launch_process(
        self,
        param: Dict = None,
        file_path: str = None,
        comment: str = None
    ) -> LaunchReturnVO:
        """启动流程

        Args:
            param: 启动参数
            file_path: 附件路径
            comment: 备注

        """
        return await self.async_api.process.launch(
            ProcessLaunchDTO(
                paramMap=param,
                filePath=file_path,
                comment=comment,
                elementDetail=self.element_info
            )
        )

    async def batch_launch_process(
        self,
        params: Union[
            List[Dict[str, str]],
            List[ProcessStartMultipleDTO]
        ] = None
    ) -> List[LaunchReturnForBatchVO]:
        """批量启动流程

        Args:
            params: 启动参数集合列表

        """
        if params is not None and not isinstance(params, list):
            raise TypeError('params参数应为List类型')

        if isinstance(params, list):
            params = parse_obj_as(List[ProcessStartMultipleDTO], params)

        return await self.async_api.process.launch_batch(
            ProcessLaunchMultipleDTO(
                multipleParams=params,
                elementDetail=self.element_info
            )
        )

    async def get_process_by_param(
        self,
        param: Dict,
        version: str = None
    ) -> List[ProcessInstanceVO]:
        """通过启动参数查询流程实例

        Args:
            param: 启动参数
            version: 可选，工作流版本，默认为最新版本

        See Also:
            :func:`get_process_by_business_key`

        """
        return await self.async_api.process.process_instance_get_by_launch_params(
            LaunchParamsDTO(elementDetail=self.element_info, paramMap=param, version=version)
        )

    async def get_process_by_business_key(
        self,
        business_key: str,
        compare_type: Union[CompareType, str] = CompareType.equal,
        version: str = None
    ) -> List[ProcessInstanceVO]:
        """通过业务键查询流程实例

        Args:
            business_key: 业务键
            compare_type: 业务键匹配方式为equal还是like，默认为equal
            version: 可选，工作流版本，默认为最新版本

        See Also:
            :func:`get_process_by_param`

        """
        if business_key is None:
            raise ValueError("business_key不可为空")

        return await self.async_api.process.process_instance_get_by_business_key(
            BusinessKeyQueryDTO(
                elementDetail=self.element_info,
                businessKey=BusinessKey(compareType=CompareType[compare_type], key=business_key),
                version=version
            )
        )

    async def get_task_by_param(
        self,
        param: Dict,
        version: str = None
    ) -> List[TaskInstanceVO]:
        """通过启动参数查询任务实例

        Args:
            param: 启动参数
            version: 可选，工作流版本，默认为最新版本

        See Also:
            :func:`get_task_by_business_key`

        """
        return await self.async_api.process.task_instance_get_by_launch_params(
            LaunchParamsDTO(elementDetail=self.element_info, paramMap=param, version=version)
        )

    async def get_task_by_business_key(
        self,
        business_key: str,
        compare_type: Union[CompareType, str] = CompareType.equal,
        version: str = None
    ) -> List[TaskInstanceVO]:
        """通过业务键查询任务实例

        Args:
            business_key: 业务键
            compare_type: 业务键匹配方式为equal还是like，默认为equal
            version: 可选，工作流版本，默认为最新版本

        See Also:
            :func:`get_task_by_param`

        """
        if business_key is None:
            raise ValueError("business_key不可为空")

        return await self.async_api.process.task_instance_get_by_business_key(
            BusinessKeyQueryDTO(
                elementDetail=self.element_info,
                businessKey=BusinessKey(compareType=CompareType[compare_type], key=business_key),
                version=version
            )
        )

    async def complete_task_by_id(
        self,
        task_id: str,
        comment: str = None,
        file_path: str = None,
        outcome: str = None,
        extra_res_params: Dict[str, Any] = None,
        attachments: List[Union[Dict[str, str], FileUplodRes]] = None,
    ) -> bool:
        """完成任务实例

        Args:
            task_id: 任务实例id
            comment: 备注
            file_path: 附件路径(工作流版本在V3.0.4.0后弃用，后续版本请使用attachments参数)
            outcome: 结果选项，在任务可选结果不唯一时，必须提供
            extra_res_params: 完成参数
            attachments: 附件信息列表，
                        内容一般来自文件管理的/files/upload或/files/upload/content响应值


        Returns:
            True: 成功
            False: 失败

        .. admonition:: 示例

            .. code-block:: python

                from deepfos.api.platform import PlatformAPI
                from deepfos.element.workflow import WorkFlow

                # 上传附件't.txt'
                upload_resp = PlatformAPI().file.upload(
                    file_type='DL', file_name='t.txt', file='some text'
                )

                # 以动作approve，参数{"a": 1, "b": "42"}完成任务实例，
                # 并提供附件信息为上传的't.txt'文件，备注为"Completed by SDK"
                test_task = WorkFlow('test_task')
                test_task.complete_task_by_id(
                    task_id='fd94f6a7-3467-47f9-8a3c-ff626e68dcf5',
                    outcome='approve',
                    extra_res_params={'a': 1, 'b': '42'},
                    comment='Completed by SDK',
                    attachments=[upload_resp]
                )

        """
        action_id = None
        if outcome is not None:
            outcomes = await self.async_api.task.outcomes(task_id)
            for o in outcomes:
                if o.code == outcome:
                    action_id = o.id
                    break

        if extra_res_params is None:
            extra_res_params = {}
        if not isinstance(extra_res_params, dict):
            raise TypeError('extra_res_params参数应为字典类型')

        if attachments is not None:
            attachments = parse_obj_as(List[FileUplodRes], attachments)
        else:
            attachments = []
        return await self.async_api.task.express_complete(
            TaskCompleteInstance(
                comment=comment, filePath=file_path, outcome=outcome, taskId=task_id,
                extraResParams=[
                    TaskCompleteParam(name=k, value=v)
                    for k, v in extra_res_params.items()
                ],
                actionId=action_id,
                attachments=attachments
            )
        )

    async def list_process(
        self,
        status: List[Union[str, StatusType]] = None,
        as_dataframe: bool = False
    ) -> Union[pd.DataFrame, List[Optional[FlowInstanceDto]]]:
        """查看流程

        Args:
            status: 筛选列表，默认筛选进行中
                    筛选可选值: 进行中: in_progress; 已完成: completed; 已终止: terminated

            as_dataframe: 是否将结果处理为pd.DataFrame

        Returns:
            - 如果 ``as_dataframe == False``， 返回 :obj:`List[FlowInstanceDto]` 类型
            - 如果 ``as_dataframe == True``，返回 :obj:`DataFrame` 类型

        """
        if status is None:
            status = [StatusType.in_progress]
        else:
            status = [StatusType[s] for s in status]

        fn = partial(
            self._query_process_impl,
            status=','.join(status),
            call_api=self.async_api.instance.monitor_page
        )

        pages = await fetch_all_pages(
            fn,
            count_getter=_get_record_count,
            page_size=200,
            page_no_key='page_no',
            page_size_key='page_size'
        )

        raw_result = [record for page in pages if page.lists for record in page.lists]

        if not as_dataframe:
            return raw_result

        if len(raw_result) == 0:
            return pd.DataFrame(columns=FlowInstanceDto.__fields__)

        return pd.DataFrame([dto.dict() for dto in raw_result])

    @staticmethod
    def _query_task_impl(status, call_api, page_no, page_size):
        return call_api(UserTaskQueryDTO(status=status, pageNo=page_no, pageSize=page_size))

    @staticmethod
    def _query_process_impl(status, call_api, page_no, page_size):
        return call_api(
            processInstanceQueryDTO=FlowInstanceQueryDto(status=status, pageNo=page_no, pageSize=page_size)
        )

    async def list_my_task(
        self,
        status: List[Union[str, StatusType]] = None,
        as_dataframe: bool = False
    ) -> Union[pd.DataFrame, List[UserTaskVO]]:
        """查看我的任务

        Args:
            status: 筛选列表，默认筛选进行中
                    筛选可选值: 进行中: in_progress; 已完成: completed; 已终止: terminated

            as_dataframe: 是否将结果处理为pd.DataFrame

        Returns:
            - 如果 ``as_dataframe == False``， 返回 :obj:`List[UserTaskVO]` 类型
            - 如果 ``as_dataframe == True``，返回 :obj:`DataFrame` 类型

        """
        if status is None:
            status = [StatusType.in_progress]
        else:
            status = [StatusType[s] for s in status]

        fn = partial(
            self._query_task_impl,
            status=','.join(status),
            call_api=self.async_api.task.myTask_list_page
        )

        pages = await fetch_all_pages(
            fn,
            count_getter=_get_record_count,
            page_size=200,
            page_no_key='page_no',
            page_size_key='page_size'
        )

        raw_result = [record for page in pages if page.lists for record in page.lists]

        if not as_dataframe:
            return raw_result

        if len(raw_result) == 0:
            return pd.DataFrame(columns=UserTaskVO.__fields__)

        return pd.DataFrame([dto.dict() for dto in raw_result])

    async def list_claim_task(
        self,
        as_dataframe: bool = False
    ) -> Union[pd.DataFrame, List[UserTaskVO]]:
        """查看待认领任务

        Args:
            as_dataframe: 是否将结果处理为pd.DataFrame

        Returns:
            - 如果 ``as_dataframe == False``， 返回 :obj:`List[UserTaskVO]` 类型
            - 如果 ``as_dataframe == True``，返回 :obj:`DataFrame` 类型

        """
        fn = partial(
            self._query_task_impl,
            status='',
            call_api=self.async_api.task.claim_list_page
        )

        pages = await fetch_all_pages(
            fn,
            count_getter=_get_record_count,
            page_size=200,
            page_no_key='page_no',
            page_size_key='page_size'
        )

        raw_result = [record for page in pages if page.lists for record in page.lists]

        if not as_dataframe:
            return raw_result

        if len(raw_result) == 0:
            return pd.DataFrame(columns=UserTaskVO.__fields__)

        return pd.DataFrame([dto.dict() for dto in raw_result])


class WorkFlow(AsyncWorkFlow, metaclass=SyncMeta):
    synchronize = (
        'broadcast',
        'send_msg_to_processes',
        'launch_process',
        'batch_launch_process',
        'get_process_by_param',
        'get_process_by_business_key',
        'get_task_by_param',
        'get_task_by_business_key',
        'complete_task_by_id',
        'list_process',
        'list_my_task',
        'list_claim_task',
    )
    if TYPE_CHECKING:  # pragma: no cover
        def broadcast(self, msg_code: str, msg_body: Dict[str, Any]):
            ...

        def send_msg_to_processes(
            self,
            msg_code: str,
            msg_body: Dict[str, Any],
            processes: List[str]
        ):
            ...

        def launch_process(
            self,
            param: Dict = None,
            file_path: str = None,
            comment: str = None
        ) -> LaunchReturnVO:
            ...

        def batch_launch_process(
            self,
            params: Union[
                List[Dict[str, str]],
                List[ProcessStartMultipleDTO]
            ] = None
        ) -> List[LaunchReturnForBatchVO]:
            ...

        def get_process_by_param(
            self,
            param: Dict,
            version: str = None
        ) -> List[ProcessInstanceVO]:
            ...

        def get_process_by_business_key(
            self,
            business_key: str,
            compare_type: Union[CompareType, str] = CompareType.equal,
            version: str = None
        ) -> List[ProcessInstanceVO]:
            ...

        def get_task_by_param(
            self,
            param: Dict,
            version: str = None
        ) -> List[TaskInstanceVO]:
            ...

        def get_task_by_business_key(
            self,
            business_key: str,
            compare_type: Union[CompareType, str] = CompareType.equal,
            version: str = None
        ) -> List[TaskInstanceVO]:
            ...

        def complete_task_by_id(
            self,
            task_id: str,
            comment: str = None,
            file_path: str = None,
            outcome: str = None,
            extra_res_params: Dict[str, Any] = None,
            attachments: List[Union[Dict[str, str], FileUplodRes]] = None,
        ) -> bool:
            ...

        def list_process(
            self,
            status: List[Union[str, StatusType]] = None,
            as_dataframe: bool = False
        ) -> Union[pd.DataFrame, List[Optional[FlowInstanceDto]]]:
            ...

        def list_my_task(
            self,
            status: List[Union[str, StatusType]] = None,
            as_dataframe: bool = False
        ) -> Union[pd.DataFrame, List[UserTaskVO]]:
            ...

        def list_claim_task(
            self,
            as_dataframe: bool = False
        ) -> Union[pd.DataFrame, List[UserTaskVO]]:
            ...
