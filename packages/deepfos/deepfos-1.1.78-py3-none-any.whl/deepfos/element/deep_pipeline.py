import asyncio
import time
import warnings
from math import ceil
from typing import Any, TYPE_CHECKING, List

from deepfos import OPTION
from deepfos.api.deep_pipeline import DeepPipelineAPI
from deepfos.api.models.deep_pipeline import RunInfo, FlowInfo, RunInfoWithParam
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.exceptions import (
    APIResponseError, RunIdInvalid, RunTerminated,
    ReleaseFlowTimeout, RunFailedError, ReleaseFlowNotExists,
)
from deepfos.lib.asynchronous import future_property
from deepfos.lib.constant import UNSET
from deepfos.lib.decorator import cached_property

errcode_map = {
    42030002: ReleaseFlowTimeout,
    42030003: RunIdInvalid,
    42030009: RunFailedError,
    42030010: RunTerminated,
}


# -----------------------------------------------------------------------------
# core
class AsyncDeepPipeline(ElementBase[DeepPipelineAPI]):
    """数据流3.0"""

    @future_property
    async def release(self) -> FlowInfo:
        """发布版信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.flow.open(
            folder_id=ele_info.folderId,
            element_name=ele_info.elementName,
            version='release'
        )

    @cached_property
    def has_approved_release(self) -> bool:
        return (
            self.release is not None
            and self.release.configure.status == 'APPROVED'
        )

    async def run(
        self,
        parameter: Any = UNSET,
        timeout: int = None,
        in_process: bool = True,
    ) -> Any:
        """
        同步启动数据流

        Args:
            parameter: 执行参数
            timeout: 超时时间(秒)
            in_process: 是否在同一个进程执行（仅作新旧兼容，实际只会在同一个进程执行，即不带启停启动）

        Returns:
            执行结果
        """
        if not in_process:
            warnings.warn(
                '同步启动固定为同一个进程执行(不带启停启动)，in_process参数为False不会影响该行为'
            )
        run_id = await self.run_async(parameter, True)
        return await self.result(run_id, timeout)

    async def run_async(
        self,
        parameter: Any = UNSET,
        in_process: bool = False,
    ) -> str:
        """
        异步启动数据流

        Args:
            parameter: 执行参数
            in_process: 是否在同一个进程执行，默认False，即带启停启动

        Returns:
            执行ID
        """
        if not self.has_approved_release:
            raise ReleaseFlowNotExists('暂无启用中状态的数据流版本')

        if parameter is UNSET:
            payload = RunInfo(
                elementName=self.element_name,
                folderId=self.element_info.folderId,
                inProcess=in_process
            )
        else:
            payload = RunInfoWithParam(
                elementName=self.element_name,
                parameter=parameter,
                folderId=self.element_info.folderId,
                inProcess=in_process
            )

        return await self.async_api.run.run_async(payload)

    async def result(self, run_id: str, timeout: int = None) -> Any:
        """
        获取异步执行结果

        Args:
            run_id: 执行ID
            timeout: 超时时间(秒)

        Returns:
            执行结果

        """
        start_time = time.time()
        remaining_time = interval = min(max(OPTION.api.timeout - 1, 1), 5)
        if timeout is not None:
            remaining_time = min(interval, timeout)

        while timeout is None or remaining_time > 0:
            try:
                return await self.async_api.run.result(
                    run_id,
                    timeout=remaining_time
                )
            except APIResponseError as e:
                if e.code not in errcode_map:
                    raise

                err_cls = errcode_map[e.code]
                if err_cls is not ReleaseFlowTimeout:
                    raise errcode_map[e.code](str(e)) from None

                delta_time = time.time() - start_time
                remaining_time = (
                    ceil(min(interval, timeout - delta_time))
                    if timeout is not None else interval
                )

        raise ReleaseFlowTimeout() from None

    async def run_batch(
        self,
        parameters: List[Any],
        in_process: bool = False,
    ) -> List[str]:
        """
        批量异步启动数据流

        Args:
            parameters: 执行参数列表
            in_process: 是否在同一个进程执行，默认False，即带启停启动

        Returns:
            执行ID列表
        """
        if not self.has_approved_release:
            raise ReleaseFlowNotExists('暂无启用中状态的数据流版本')

        result = await asyncio.gather(*(
            self.run_async(parameter, in_process)
            for parameter in parameters
        ))
        return list(result)


class DeepPipeline(AsyncDeepPipeline, metaclass=SyncMeta):
    synchronize = ('run', 'run_async', 'result', 'run_batch')

    if TYPE_CHECKING:  # pragma: no cover
        def run(
            self,
            parameter: Any = UNSET,
            timeout: int = None,
            in_process: bool = True,
        ) -> Any:
            ...

        def run_async(
            self,
            parameter: Any = UNSET,
            in_process: bool = False,
        ) -> str:
            ...

        def result(self, run_id: str, timeout: int = None) -> Any:
            ...

        def run_batch(
            self,
            parameters: List[Any],
            in_process: bool = False,
        ):
            ...
