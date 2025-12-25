from typing import Union, Any, Awaitable

from deepfos.lib.decorator import cached_property
from .base import DynamicRootAPI, ChildAPI, get, post
from .models.deep_pipeline import *

__all__ = ['DeepPipelineAPI']


class RunAPI(ChildAPI):
    """数据流的执行、获取执行信息等逻辑"""
    endpoint = '/'

    @post('run')
    def run_async(self, run_info: Union[RunInfo, RunInfoWithParam]) -> Union[str, Awaitable[str]]:
        """
        异步执行数据流
        异步执行数据流，返回任务id
        """
        return {'body': run_info}

    @get('run')
    def result(self, task_id: str, timeout: int = None) -> Union[Any, Awaitable[Any]]:
        """获取执行结果"""
        return {'param': {'timeout': timeout}, 'path': f'{task_id}/result'}


class FlowAPI(ChildAPI):
    """数据流定义相关接口"""
    endpoint = '/flow'

    @get('')
    def open(self, element_name: str, folder_id: str, version: str) -> Union[FlowInfo, Awaitable[FlowInfo]]:
        """查看数据流"""
        return {
            'param': {
                'elementName': element_name,
                'folderId': folder_id,
                'version': version
            }
        }


class DeepPipelineAPI(DynamicRootAPI, builtin=True):
    """DeepPipeline组件接口"""
    module_type = 'DPL'
    default_version = (3, 0)
    multi_version = False
    cls_name = 'DeepPipelineAPI'
    module_name = 'deepfos.api.deep_pipeline'
    api_version = (3, 0)

    @cached_property
    def run(self) -> RunAPI:
        """数据流的执行、获取执行信息等逻辑"""
        return RunAPI(self)

    @cached_property
    def flow(self) -> FlowAPI:
        """数据流定义相关接口"""
        return FlowAPI(self)
