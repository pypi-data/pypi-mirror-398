"""子任务相关"""
import asyncio
import itertools
import json
import re
from collections import deque
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Optional, Any, Iterable, Iterator, Dict, Sequence
from threading import Lock
import warnings

from loguru import logger

from deepfos.options import OPTION
from deepfos.lib.decorator import cached_class_property
from deepfos.lib.utils import retry
from deepfos.lib.asynchronous import evloop
from deepfos.api.models.system import JobContentDto, UpdateJobCurrentDto
from deepfos.api.system import SystemAPI

from dip.client import Client as WorkerClient

__all__ = [
    'TaskContainer', 'Task', 'create_tasks'
]

# -----------------------------------------------------------------------------
# constants
_RE_HAS_COUNTER = re.compile('.*{counter:?[0-9]*}')
WAIT = 'WAIT'
START = 'GO'
SUCCESS = 'SUCCESS'
FAIL = 'FAIL'
FINISHED = (SUCCESS, FAIL)
COUNTER = itertools.count().__next__


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class TaskManager:
    #: 子任务id -> 子任务状态
    _task_info: Dict[str, JobContentDto] = {}
    _lock = Lock()
    #: 实例缓存，用于实现基于子任务id的单例
    _ins_cache: dict = {}
    #: 更新任务的协程
    _schedule = None
    #: 更新任务的sleep间隔
    _interval: int = 2
    #: 当前还未结束的任务数量
    _pending_tasks: int = 0

    def __new__(cls, task_id: str):
        try:
            with cls._lock:
                return cls._ins_cache[task_id]
        except KeyError:
            pass  # key not found
        ins = super().__new__(cls)
        ins._id = task_id
        ins._status = JobContentDto(key=task_id)
        cls._pending_tasks += 1
        cls.setup()
        # in case of a race, prefer the item already in the cache
        try:
            with cls._lock:
                return cls._ins_cache.setdefault(task_id, ins)
        except ValueError:  # pragma: no cover
            return ins  # value too large

    @classmethod
    def all_done(cls):
        cls._pending_tasks = 0

    def set_status(self, status: str) -> 'TaskManager':
        """更新任务状态

        Args:
            status: 任务状态
        """
        self._status.status = status
        if status in FINISHED:
            self._status.endTime = _now()
            self.__class__._pending_tasks -= 1
            self._ins_cache.pop(self._id, None)  # remov self from cache

        # add self to class's task_info
        self.__class__._task_info[self._id] = self._status
        return self

    def set_name(self, name):
        self._status.jobContentNameEn = \
            self._status.jobContentNameZhcn = \
            self._status.jobContentNameZhtw = name

    def init(self, name) -> 'TaskManager':
        self.set_name(name)
        return self.set_status(WAIT)

    @classmethod
    def setup(cls):
        if cls._schedule is None:
            cls._schedule = evloop.create_task(cls._periodic_submit_status())

    @classmethod
    @retry(retries=5, wait=3)
    async def _update_status(cls):
        if task_info := cls._task_info:
            try:
                # 清空_task_info因为await时_task_info可能被其他协程更新
                cls._task_info = {}
                cls._meta_task.jobContents = list(task_info.values())
                await cls._api.extra.job_update(cls._meta_task.dict())  # noqa
            except Exception:   # pragma: no cover
                # 把没有提交成功的_task_info重新放入
                cls._task_info = {**task_info, **cls._task_info}
                raise

    @classmethod
    async def _periodic_submit_status(cls):
        """定时提交子任务状态"""
        logger.debug("Scheduled a background coroutine to update task status.")
        while cls._pending_tasks > 0:
            await cls._update_status()
            await asyncio.sleep(cls._interval)

        # we need double check here because task_info may increase in last loop
        if cls._task_info:
            await cls._update_status()

        cls._schedule = None
        logger.debug("Background coroutine finished.")

    @cached_class_property
    def _api(self):
        return SystemAPI(sync=False)

    @cached_class_property
    def _meta_task(self):
        meta_task_id = OPTION.general.task_info['task_id']
        return UpdateJobCurrentDto(id=meta_task_id)

    @classmethod
    def set_task_status(cls, task_id, status, arg=None) -> 'TaskManager':
        return cls(task_id).set_status(status)

    @classmethod
    def init_tasks(cls, tasks: Iterable['Task']):
        for task in tasks:
            task_mgr = cls(task.task_id)
            task_mgr.init(task.task_name)

    @classmethod
    def wait(cls, timeout=5):
        if cls._schedule is None:
            return

        try:
            cls._schedule.result(timeout)
        except Exception: # noqa  # pragma: no cover
            pass


class TaskManagerSocket:
    #: 子任务id -> 子任务状态
    _task_info: Dict[str, Dict[str, str]] = {}
    _lock = Lock()
    #: 实例缓存，用于实现基于子任务id的单例
    _ins_cache: dict = {}
    #: 更新任务的协程
    _schedule = None
    #: 更新任务的sleep间隔
    _interval: int = 2
    #: 当前还未结束的任务数量
    _pending_tasks: int = 0

    # NB: set port to avoid init args err on win system
    _client = WorkerClient(
        port=None,
        sockname=OPTION.general.socket_name,
        loop=evloop.loop,
        id=OPTION.general.task_info.get('task_id'),
        timeout=2
    )

    def __new__(cls, task_id: str, arg: str):
        try:
            with cls._lock:
                return cls._ins_cache[task_id]
        except KeyError:
            pass  # key not found
        ins = super().__new__(cls)
        ins._id = task_id
        ins._status = {'key': task_id, 'arg': arg}
        cls._pending_tasks += 1
        cls.setup()
        # in case of a race, prefer the item already in the cache
        try:
            with cls._lock:
                return cls._ins_cache.setdefault(task_id, ins)
        except ValueError:  # pragma: no cover
            return ins  # value too large

    @classmethod
    def all_done(cls):
        cls._pending_tasks = 0

    def set_status(self, status: str) -> 'TaskManagerSocket':
        """更新任务状态

        Args:
            status: 任务状态
        """
        self._status.update({'status': status, 'endTime': ''})
        if status in FINISHED:
            self._status.update({'endTime': _now()})
            self.__class__._pending_tasks -= 1
            self._ins_cache.pop(self._id, None)  # remove self from cache

        # add self to class's task_info
        self.__class__._task_info[self._id] = self._status
        return self

    def set_name(self, name):
        self._status.update({'name': name})

    def init(self, name) -> 'TaskManagerSocket':
        self.set_name(name)
        return self.set_status(WAIT)

    @classmethod
    def setup(cls):
        if cls._schedule is None:
            cls._schedule = evloop.create_task(cls._periodic_submit_status())

    @classmethod
    @retry(retries=5, wait=1)
    async def _update_status(cls):
        if task_info := cls._task_info:
            try:
                # 清空_task_info因为await时_task_info可能被其他协程更新
                cls._task_info = {}
                logger.debug(f'Send msg to Master with task info:\n{list(task_info.values())}...')
                await cls._client.send_msg(
                    "U",
                    list(task_info.values())
                )
                logger.debug(f'Send msg to Master with task info:\n{list(task_info.values())} done.')
            except Exception:   # pragma: no cover
                # 把没有提交成功的_task_info重新放入
                cls._task_info = {**task_info, **cls._task_info}
                raise

    @classmethod
    async def _periodic_submit_status(cls):
        """定时提交子任务状态"""
        logger.debug("Scheduled a background coroutine to update task status.")
        while cls._pending_tasks > 0:
            await cls._update_status()
            await asyncio.sleep(cls._interval)
        # we need double-check here because task_info may increase in last loop
        if cls._task_info:
            await cls._update_status()
        cls._schedule = None
        logger.debug("Background coroutine finished.")

    @classmethod
    def set_task_status(cls, task_id, status, arg=None) -> 'TaskManagerSocket':
        return cls(task_id, json.dumps(arg, default=str)).set_status(status)

    @classmethod
    def init_tasks(cls, tasks: Iterable['Task']):
        for task in tasks:
            task_mgr = cls(task.task_id, json.dumps(task.arg, default=str))
            task_mgr.init(task.task_name)

    @classmethod
    def wait(cls, timeout=5):
        logger.debug('Wait called.')
        if cls._schedule is None:
            cls._client.close()
            return

        try:
            cls._schedule.result(timeout)
        except Exception: # noqa  # pragma: no cover
            logger.exception('Exception occurs while wait.')
        finally:
            cls._client.close()


if OPTION.general.socket_communication:
    TaskRealManager = TaskManagerSocket
else:
    TaskRealManager = TaskManager


class TaskIdGenerator:
    __cache__ = {}

    def __new__(cls,):
        base_id = OPTION.general.task_info.get("task_id")

        if base_id not in cls.__cache__:
            ins = super().__new__(cls)
            ins._id = base_id
            ins._counter = itertools.count().__next__
            cls.__cache__[base_id] = ins

        return cls.__cache__[base_id]

    def next(self):
        return f'{self._id}-{self._counter()}'


class _AbsTask:
    def __init__(
        self,
        arg: Optional[Any] = None,
        task_name_tmpl: Optional[str] = 'Task - {counter:03}',
        swallow_exc: Optional[bool] = False
    ):
        self.arg = arg
        self.swallow_exc = swallow_exc
        self.task_name_format = task_name_tmpl.format(counter=COUNTER(), arg=arg)
        self.is_called = False

    def get_arg(self):
        return self

    def __enter__(self):
        self.is_called = True
        return self.arg

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return self.swallow_exc
        else:
            return True


class _AbsTaskContainer:
    def __init__(
        self, args: Iterable[Any],
        task_name_tmpl: Optional[str] = 'Task - {counter:03}',
        swallow_exc: Optional[bool] = False
    ):
        self.arg: Iterator = iter(args)
        self.task_name_format = task_name_tmpl
        self.swallow_exc = swallow_exc
        self.tasks = deque([])
        self._init_tasks(task_name_tmpl)

    def _init_tasks(self, task_name_format):
        for arg in self.arg:
            self.tasks.append(_AbsTask(arg, task_name_format, self.swallow_exc))

    def __iter__(self):
        return self

    def __next__(self) -> _AbsTask:
        if self.tasks:
            return self.tasks.popleft()
        raise StopIteration


class Task(AbstractContextManager):
    """子任务对象

    Args:
        arg: 执行参数
        task_name_tmpl: 任务名模板，支持替换的字段为counter（自增任务编号）
           和 arg（任务使用的参数），默认以 Task-{counter:03} 格式产生
        swallow_exc: 在任务出现异常时是否忽略（不中断程序执行）
        check_started: 是否检查任务启动过

    .. admonition:: 示例

        .. code-block:: python

            with Task():
                time.sleep(1)

            with Task(swallow_exc=True):
                raise ValueError('an error occurs')

            with Task(task_name_tmpl="Your task name"):
                time.sleep(1)

    Note:
        - 若不通过 :class:`TaskContainer` 或 :function:`create_tasks`，
           而是直接实例化Task对象，则只有其中任务被执行时，
           记录才会创建更新，作业界面进度条不能反映实际运行进度
        - 如需看到稳定进度条的情况，建议从 :class:`TaskContainer` 调用或使用
           :function:`create_tasks` 方法

    See Also:
        :class:`TaskContainer`
        :func:`create_tasks`

    """
    __slots__ = (
        '_check_started', 'arg', 'task_id', 'swallow_exc',
        'task_name', '_started', 'initialized'
    )

    def __init__(
        self,
        arg: Optional[Any] = None,
        task_name_tmpl: Optional[str] = 'Task - {counter:03}',
        swallow_exc: Optional[bool] = False,
        check_started: Optional[bool] = True,
    ):
        self._check_started = check_started
        self.arg = arg
        self.task_id = TaskIdGenerator().next()
        self.swallow_exc = swallow_exc
        if _RE_HAS_COUNTER.match(task_name_tmpl):
            self.task_name = task_name_tmpl.format(counter=COUNTER(), arg=arg)
        else:
            self.task_name = task_name_tmpl.format(arg=arg)
        self._started = False
        self.initialized = False

    def get_arg(self):
        return self

    def __enter__(self):
        self._started = True
        mgr = TaskRealManager.set_task_status(self.task_id, START, self.arg)
        if not self.initialized:
            mgr.set_name(self.task_name)
        return self.arg

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            TaskRealManager.set_task_status(self.task_id, FAIL, self.arg)
            if self.swallow_exc:
                logger.exception('')
            else:
                # 后续子任务不会再执行，因此提前通知TaskManger结束任务更新
                TaskRealManager.all_done()
            return self.swallow_exc
        else:
            TaskRealManager.set_task_status(self.task_id, SUCCESS, self.arg)
            return True

    def __del__(self):
        if not self._started and self._check_started:
            warnings.warn(f'Task: {self.task_name} never started!')


class TaskContainer:
    """创建子任务容器

    将提供的执行参数包装为当前脚本的子任务，在循环的不同时刻更新状态

    Args:
        args: 执行参数
        task_name_tmpl: 任务名模板，支持替换的字段为counter（自增任务编号）
           和arg（任务使用的参数），默认以 Task-{counter:03} 格式产生
        swallow_exc:  在任务出现异常时是否忽略（不中断程序执行）

    Note:
        - 在循环开始前，基于此迭代方法创建并初始化所有子任务，状态为“等待”
        - 在每次循环开始时，更新当前子任务状态为“运行中”
        - 结束时，视结果及是否忽略异常（swallow_exc）更新状态为“成功”或“失败”

    .. admonition:: 示例

        例如原先有如下代码结构：

        .. code-block:: python

            for arg in range(10):
                do_something(arg)

        如果希望每次循环能作为子任务在作业管理中查看，
        可以对代码作如下修改：

        .. code-block:: python
            :emphasize-lines: 1,2

            for task in TaskContainer(range(10)):
                with task.get_arg() as arg:
                    do_something(arg)

    See Also:
        - :class:`Task`
        - :func:`create_tasks`

    """

    def __init__(
        self,
        args: Iterable[Any],
        task_name_tmpl: Optional[str] = 'Task - {counter:03}',
        swallow_exc: Optional[bool] = True
    ):
        self.arg: Iterator = iter(args)
        self.swallow_exc = swallow_exc
        self.tasks = deque()
        self._init_tasks(task_name_tmpl)

    def _init_tasks(self, task_name_tmpl):
        for arg in self.arg:
            task = Task(
                arg, task_name_tmpl, self.swallow_exc,
                check_started=self.swallow_exc
            )
            task.initialized = True
            self.tasks.append(task)
        TaskRealManager.init_tasks(self.tasks)

    def __iter__(self):
        return self

    def __next__(self) -> Task:
        if self.tasks:
            return self.tasks.popleft()
        raise StopIteration


def create_tasks(
    task_count: int,
    task_name_tmpl: Optional[str] = 'Task - {counter:03}',
    swallow_exc: Optional[bool] = False
) -> Sequence[Task]:
    """创建多个任务，获取子任务对象

    Args:
        task_count: 生成任务数
        task_name_tmpl: 任务名模板，支持替换的字段为counter（自增任务编号）
           和arg（任务使用的参数），默认以 Task-{counter:03} 格式产生
        swallow_exc:  在任务出现异常时是否忽略（不中断程序执行）

    .. admonition:: 示例

        为当前脚本创建2个子任务：

        .. code-block:: python

            task_a, task_b = create_tasks(2)

            with task_a:
                do_something()

            with task_b:
                do_something()

    See Also:
        :class:`TaskContainer`
        :class:`Task`

    """
    if task_count <= 0:
        raise ValueError("The task_count should be a positive number!")
    task_container = TaskContainer(
        args=range(task_count),
        task_name_tmpl=task_name_tmpl,
        swallow_exc=swallow_exc
    )

    return task_container.tasks


if OPTION.general.dev_mode or not OPTION.general.task_info.get('should_log', True):
    TaskContainer = _AbsTaskContainer
    Task = _AbsTask
