import asyncio.exceptions
import json
import threading
import time
from abc import ABC
from contextlib import contextmanager
from importlib import import_module
from math import ceil
from typing import Any, Dict, Tuple
from urllib.parse import quote_plus

from loguru import logger

from deepfos import OPTION
from deepfos.api.app import AppAPI
from deepfos.api.models.python import PyRunInfo
from deepfos.api.python import PythonAPI
from deepfos.element.base import ElementBase
from deepfos.exceptions import (
    ResultTimeOutError,
    PyTaskRevokedError,
    PyTaskRunTimeError,
    PyTaskInvalidError,
    PyTaskConcurrencyExceed,
    PyTaskTimeLimitExceed,
    APIResponseError,
)
from deepfos.lib.asynchronous import future_property
from deepfos.lib.constant import UNSET
from deepfos.lib.redis import RedisCli

__all__ = [
    'PythonScript',
    'OnlineTask',
    'LocalTask',
]

ONLINE_MODE = (
    OPTION.module.src_task is not None
    and OPTION.module.src_celeryapp is not None
    and OPTION.module.src_options is not None
    and OPTION.module.src_errors_classes is not None
)

if ONLINE_MODE:  # pragma: no cover
    try:
        import celery.states as cstates    # noqa
        from celery.exceptions import TaskRevokedError, TimeoutError    # noqa
        from celery.result import allow_join_result    # noqa
    except ImportError:
        ONLINE_MODE = False

if ONLINE_MODE:  # pragma: no cover
    try:
        pyrunner = import_module(OPTION.module.src_task).run    # noqa
        AsyncResult = import_module(OPTION.module.src_celeryapp).celery_app.AsyncResult    # noqa
        SERVER_OPTION = import_module(OPTION.module.src_options).OPTION    # noqa
        PyExecutionError = import_module(OPTION.module.src_errors_classes).PyExecutionError    # noqa

        assert SERVER_OPTION.redis.mode == 'single', 'Only supported in redis single mode'

        redis_addr = SERVER_OPTION.redis.addr
        redis_password = quote_plus(SERVER_OPTION.redis.password)

        CONCURRENCY_KEY_PREFIX = f'celery_concurrency_task:{OPTION.general.task_info.get("worker_name")}'
        redis_cli = RedisCli(f"redis://:{redis_password}@{redis_addr}/13")
        CONCURRENCY_KEY = None
        GLOBAL_LOCK = None

    except (ImportError, AssertionError):
        ONLINE_MODE = False

LOCAL_LOCK = threading.Lock()

WAITING_TASKS = 0

_on_const = {
    'NaN': None
}.__getitem__


def maybe_prepare_redis_lock():
    global CONCURRENCY_KEY
    global GLOBAL_LOCK
    if CONCURRENCY_KEY is None:
        CONCURRENCY_KEY = redis_cli.lock(
            f'{CONCURRENCY_KEY_PREFIX}:{OPTION.general.task_info["task_id"]}',
            renew_interval=2, expire_sec=4, blocking_timeout=None
        )
    if GLOBAL_LOCK is None:
        GLOBAL_LOCK = redis_cli.lock(
            CONCURRENCY_KEY_PREFIX,
            renew_interval=1, expire_sec=2, blocking_timeout=None
        )


class AbstractPythonTask(ABC):
    task_id = UNSET

    def get_result(self, timeout: int = None):  # pragma: no cover
        """获取当前脚本执行结果

        Args:
            timeout: 获取等待超时时间，默认为None，意味着会等待直到有结果

        """
        raise NotImplementedError

    def terminate(self):  # pragma: no cover
        """取消当前脚本

        Important:
            只有非结束状态的脚本可以被取消

        """
        raise NotImplementedError


errcode_map = {
    28030001: PyTaskRunTimeError,
    28030003: PyTaskRevokedError,
    28030005: ResultTimeOutError,
    28030006: PyTaskTimeLimitExceed,
    28040001: PyTaskInvalidError,
}


class LocalTask(AbstractPythonTask):
    """本地任务实例

    Args:
        parameter: 任务入参
        manager: PythonScript实例，用于提供元素信息


    """

    def __init__(self, parameter, manager: 'PythonScript'):
        self.manager = manager
        self.task_id = manager.api.script.run(
            PyRunInfo.construct_from(manager.element_info, parameter=parameter)
        )
        logger.debug(f'python脚本[id:{self.task_id}]任务信息已发送')

    def get_result(self, timeout: int = None):
        start_time = time.time()
        remaining_time = interval = min(max(OPTION.api.timeout - 1, 1), 5)
        if timeout is not None:
            remaining_time = min(interval, timeout)

        while timeout is None or remaining_time > 0:
            try:
                return self.manager.api.script.result(
                    self.task_id,
                    timeout=remaining_time
                )
            except APIResponseError as e:
                if e.code not in errcode_map:
                    raise

                err_cls = errcode_map[e.code]
                if err_cls is not ResultTimeOutError:
                    raise errcode_map[e.code](str(e)) from None

                delta_time = time.time() - start_time
                remaining_time = (
                    ceil(min(interval, timeout - delta_time))
                    if timeout is not None else interval
                )

        raise ResultTimeOutError() from None

    def terminate(self):
        return self.manager.api.script.terminate(self.task_id)


class OnlineTask(AbstractPythonTask):
    """线上任务实例

    Args:
        parameter: 任务入参
        manager: PythonScript实例，用于提供元素信息


    """

    def __init__(self, parameter, manager: 'PythonScript'):
        if not ONLINE_MODE:
            raise NotImplementedError('OnlineTask实例只能在线上环境使用')

        task = pyrunner.apply_async(
            args=(parameter,
                  *manager.env)
        )
        self.task_id = task.id

        logger.debug(f'python脚本[id:{self.task_id}]任务信息已发送')

    def _get_valid_task(self):
        task = AsyncResult(self.task_id)
        if task.status is cstates.PENDING:  # pragma: no cover
            raise PyTaskInvalidError()

        return task

    @contextmanager
    def _ensure_valid_concurrency(self):
        global WAITING_TASKS
        maybe_prepare_redis_lock()
        global CONCURRENCY_KEY
        global GLOBAL_LOCK

        with LOCAL_LOCK:
            if not CONCURRENCY_KEY.locked() and WAITING_TASKS == 0: # noqa
                with GLOBAL_LOCK:
                    con_num = len(list(redis_cli.client.scan_iter(f'{CONCURRENCY_KEY_PREFIX}:*')))

                if (SERVER_OPTION.celery.autoscale_max_concurreny - con_num) <= OPTION.general.preserve_concurrency:
                    raise PyTaskConcurrencyExceed(
                        OPTION.general.task_info.get("worker_name"),
                        con_num
                    )

                with GLOBAL_LOCK:
                    CONCURRENCY_KEY.do_hold() # noqa

            WAITING_TASKS = WAITING_TASKS + 1
        try:
            yield
        finally:
            with LOCAL_LOCK:
                WAITING_TASKS = WAITING_TASKS - 1
                if WAITING_TASKS == 0:
                    with GLOBAL_LOCK:
                        CONCURRENCY_KEY.release() # noqa

    def get_result(self, timeout: int = None):
        task = self._get_valid_task()

        with self._ensure_valid_concurrency():
            with allow_join_result():
                try:
                    ret, *std = task.get(timeout=timeout)
                    return json.loads(ret, parse_constant=_on_const)
                except TimeoutError:
                    raise ResultTimeOutError() from None
                except TaskRevokedError:
                    raise PyTaskRevokedError() from None
                except PyExecutionError as e:
                    raise PyTaskRunTimeError(e.stderr) from None
                except Exception as e:
                    raise PyTaskRunTimeError(e) from None

    def terminate(self):
        task = self._get_valid_task()

        if task.status in cstates.READY_STATES:
            logger.warning('python脚本已结束')
            return

        task.revoke(terminate=True)
        logger.info(f'python脚本[id:{self.task_id}]已取消')

    def status(self):
        return self._get_valid_task().status


class PythonScript(ElementBase[PythonAPI]):
    """Python脚本对象

    Args:
        task_name: 任务名称
        should_log: 仅在线上执行时有效，脚本是否记录执行日志，
                    线下执行时，该值与脚本元素配置项“记录执行日志”保持一致


    """
    def __init__(
        self,
        element_name: str,
        folder_id: str = None,
        path: str = None,
        task_name: str = None,
        should_log: bool = False
    ):
        self.should_log = should_log
        self.task_name = task_name
        super().__init__(
            element_name=element_name, folder_id=folder_id, path=path
        )

    @future_property
    async def env(self) -> Tuple[str, str, Dict]:
        if not ONLINE_MODE:
            raise NotImplementedError('只在线上环境中可获得env值')

        ele_info = await self.wait_for('element_info')
        python_path = '/'.join([
            SERVER_OPTION.general.py_root,
            OPTION.api.header['space'],
            OPTION.api.header['app']]
        )
        if self._path is not None:
            folder = self._path.strip('\\/') \
                .replace('/', '.').replace('\\', '.')
        else:
            path = await AppAPI(sync=False).folder.get_folder_full(ele_info.folderId)
            folder = path.strip('\\/').replace('/', '.').replace('\\', '.')

        if not folder:
            module = self.element_name
        else:
            module = '.'.join([folder, self.element_name])

        return (
            module,
            python_path,
            {
                'header': OPTION.api.header,
                'server': SERVER_OPTION.server.to_dict(),
                'element_desc': {},
                'should_log': self.should_log,
                'compressed_flag': False,
                'task_type': "NATIVE",
                'return_structure_data': None,
                'return_structure_type': None,
                'enable_return_structure': False,
                'task_name': self.task_name,
                'use_eureka': OPTION.discovery.enabled
            }
        )

    def run(self, parameter: Any = None, timeout: int = None):
        """发送python脚本任务信息并获取执行结果

        Args:
            parameter: 脚本入参
            timeout: 获取等待超时时间，默认为None，意味着会等待直到有结果

        .. admonition:: 示例

            .. code-block:: python

                from deepfos.element.pyscript import PythonScript

                script = PythonScript(element_name='test_task',
                                      path='/',
                                      should_log=True)

                script.run(parameter={'a': 1})

            线上执行时，将执行发送当前空间内元素路径为'/'，元素名为test_task的python脚本的任务，
            并等待结果，且由于初始化时should_log为True，其在作业管理中将更新作业信息


        See Also:
            :meth: `run_async`
            :class:`LocalTask`
            :class:`OnlineTask`

        """
        task = self.run_async(parameter)
        return task.get_result(timeout)

    def run_async(self, parameter: Any = None) -> AbstractPythonTask:
        """发送python脚本任务信息并返回Task实例

        该方法不会等待任务执行结果，任务信息将被提交至celery任务队列，
        待有可用并发数时执行，执行结果可通过Task实例的 `get_result` 方法得到

        Args:
            parameter: 脚本入参


        Returns: python脚本任务id

        .. admonition:: 示例

            .. code-block:: python

                from deepfos.element.pyscript import PythonScript

                script = PythonScript(element_name='test_task',
                                      path='/',
                                      should_log=True)

                script.run_async(parameter={'a': 1})

            线上执行时，将执行发送当前空间内元素路径为'/'，
            元素名为test_task的python脚本的任务，且由于初始化时should_log为True，
            其在作业管理中将更新作业信息

            可通过如下代码等待并获得结果，如不使用，任务亦会照常执行，如记录了任务id，
            可通过python组件的/script/result/{任务id}接口得到结果

            .. code-block:: python

                res = script.get_result()


        See Also:
            :meth:`run`
            :class:`LocalTask`
            :class:`OnlineTask`

        """
        if not ONLINE_MODE:
            task = LocalTask(parameter, self)
        else:
            task = OnlineTask(parameter, self)

        return task
