from .base import DynamicRootAPI, ChildAPI, get, post
from .models.python import *
from deepfos.lib.decorator import cached_property
from typing import List, Dict, Union, Any, Awaitable

__all__ = ['PythonAPI']


class WorkerAPI(ChildAPI):
    """python工作进程相关接口"""
    endpoint = '/worker'

    @post('register')
    def register(self, worker_info: WorkerRegistry) -> Union[bool, Awaitable[bool]]:
        return {'body': worker_info}

    @get('metrics')
    def metrics(self, ) -> Union[List[WorkerMetrics], Awaitable[List[WorkerMetrics]]]:
        return {}


class ScriptAPI(ChildAPI):
    """python脚本的运行，关闭，进度查询等逻辑"""
    endpoint = '/script'

    @post('run')
    def run(self, run_info: PyRunInfo) -> Union[str, Awaitable[str]]:
        return {'body': run_info}

    @get('result')
    def result(self, task_id: str, timeout: int = None) -> Union[Any, Awaitable[Any]]:
        return {'param': {'timeout': timeout}, 'path': task_id}

    @post('terminate')
    def terminate(self, task_id: str) -> Union[Any, Awaitable[Any]]:
        return {'body': {"taskId": task_id}}


class FileAPI(ChildAPI):
    """python文件的新建，上传，更新逻辑"""
    endpoint = '/file'

    @post('add')
    def add(self, file: PyNewFile) -> Union[bool, Awaitable[bool]]:
        """
        新建python文件

        """
        return {'body': file}

    @post('update')
    def update(self, file: PyNewFile) -> Union[bool, Awaitable[bool]]:
        """
        更新文件内容

        """
        return {'body': file}

    @get('read')
    def read(self, info: PyBaseInfo) -> Union[PyNewFileWithError, Awaitable[PyNewFileWithError]]:
        """
        读取文件内容

        """
        return {'param': info}


class PythonAPI(DynamicRootAPI, builtin=True):
    """Python组件"""
    module_type = 'PY'
    default_version = (2, 0)
    multi_version = False
    cls_name = 'PythonAPI'
    module_name = 'deepfos.api.python'
    api_version = (2, 0)

    @cached_property
    def worker(self) -> WorkerAPI:
        """python工作进程相关接口"""
        return WorkerAPI(self)

    @cached_property
    def script(self) -> ScriptAPI:
        """python脚本的运行，关闭，进度查询等逻辑"""
        return ScriptAPI(self)

    @cached_property
    def file(self) -> FileAPI:
        """python文件的新建，上传，更新逻辑"""
        return FileAPI(self)
