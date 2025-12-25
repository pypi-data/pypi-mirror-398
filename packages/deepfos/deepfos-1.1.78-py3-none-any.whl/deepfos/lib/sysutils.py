"""系统相关工具类/函数"""
import asyncio
import base64
import gzip
import itertools
import json
import time
from datetime import datetime
from enum import Enum
from io import TextIOWrapper
from typing import Dict, Any, Union, List, IO, TypeVar, Optional
import pandas as pd
import math
import hashlib
from urllib.parse import unquote
from loguru import logger

from ._javaobj import is_java_serialized, JavaDeSerializeHelper
from deepfos.lib.decorator import cached_property, lru_cache
from deepfos.api.deepfos_task import TaskAPI
from deepfos.api.models.deepfos_task import (
    TaskSearchDTO, JobCreateDto,
    PeriodicTaskCreateInfo, ScheduledTaskCreateInfo
)
from deepfos.element.base import ElementBase
from .asynchronous import evloop
from .utils import split_dataframe
from deepfos.options import OPTION
from deepfos.api.models import BaseModel
from deepfos.api.models.space import SpFileBusinessRecordSaveDto
from deepfos.api.platform import PlatformAPI
from deepfos.api.space import SpaceAPI
from deepfos.api.system import SystemAPI
from deepfos.api import account as acc_api
from deepfos.api.models import account as account_model
from deepfos.cache import SpaceSeperatedLRUCache
from deepfos.api.models.account import UserGroupModifyDTO

_VALUE_KEY = 'value'
_DTNAME_KEY = 'dataTableName'
_LOGIC_KEY = 'logicKeys'
_TEMP_MERGE_KEY = '#cartes1an_t3mp0rary_k3y#'


class ValType(int, Enum):
    invalid = 0
    table = 1
    field = 2

    @classmethod
    def classify(cls, value):
        if isinstance(value, dict) and _VALUE_KEY in value:
            return cls.field
        if isinstance(value, list) and value:
            item = value[0]
            if isinstance(item, dict) and _DTNAME_KEY in item:
                return cls.table
        return cls.invalid


class BaseArgParser:  # pragma: no cover
    def parse(self):
        raise NotImplementedError


class BizModelArgParser:
    def __init__(self, arg: Dict[str, Any]):
        self.arg = arg.copy()

    def _parse_row(self, row: Dict[str, Any], memo: Dict):
        classify = ValType.classify

        table_name = row.pop(_DTNAME_KEY)
        parsed_rows = memo.setdefault(table_name, [])
        logic_keys = row.pop(_LOGIC_KEY, [])
        cur_row = {k: row[k] for k in logic_keys}
        parsed_rows.append(cur_row)

        child_tables = []
        for key, val in row.items():
            val_type = classify(val)

            if val_type is ValType.invalid:
                continue
            elif val_type is ValType.table:
                child_tables.append(val)
            elif val_type is ValType.field:
                cur_row[key] = val[_VALUE_KEY]

        for tbl in child_tables:
            for row in tbl:
                self._parse_row(row, memo)

    def parse(self) -> Dict[str, pd.DataFrame]:
        memo = {}
        self._parse_row(self.arg, memo)
        return {
            k: pd.DataFrame(v)
            for k, v in memo.items()
        }


def complete_cartesian_product(
    fix: Dict[str, Union[str, list]],
    df: pd.DataFrame = None,
    paths: Union[str, Dict[str, str]] = None,
    folder_ids: Union[str, Dict[str, str]] = None,
    col_dim_map: Dict[str, str] = None,
) -> pd.DataFrame:
    """
    构造完整的维度成员笛卡尔积

    Args:
        fix: 需要构造笛卡尔积的维度表达式，字典格式，key为维度名，值为维度成员组成的list，或维度表达式字符串
        df: 如果需要为现有DataFrame补全笛卡尔积，传入一个df。如果不传，则是生成fix中维度成员的笛卡尔积。
        paths: fix中维度的path，如果所有维度的目录相同，传同一个path，否则传字典，key为维度名，value为path。
          如果不传，则自动寻找维度对应的path。
        folder_ids: 类似paths, 但值是folder_id
        col_dim_map: data中的列名与实际维度名的映射关系，默认data中的列名与维度名相同

    Returns:
        维度成员笛卡尔积的DataFrame

    .. admonition:: 示例

        .. code-block:: python
            # 不传参数df，将返回cost_center，year，period三列的DataFrame
            df = complete_cartesian_product(fix={
                'cost_center': 'Base(1001,0)',
                'year': ['2021', '2022'],
                'period': 'Base(TotalPeriod,0)'
            })

            # 传参数df，将返回account，data，cost_center，year，period五列的DataFrame
            df1 = pd.DataFrame([
                {'account': '1002', 'data': '111'},
                {'account': '1003', 'data': '444'}
            ])
            df = complete_cartesian_product(
                fix={
                    'cost_center': 'Base(1001,0)',
                    'year': ['2021', '2022'],
                    'period': 'Base(TotalPeriod,0)'
                },
                df=df1
            )

    See Also:
        fix参数的字典value可接受list和维度表达式，但list效率更高
    """
    from deepfos.element.dimension import AsyncDimension
    from .asynchronous import evloop

    if paths is not None:
        loc_key = "path"
        if isinstance(paths, dict):
            loc_getter = paths.get
        else:
            loc_getter = lambda _: paths
    elif folder_ids is not None:
        loc_key = "folder_id"

        if isinstance(folder_ids, dict):
            loc_getter = folder_ids.get
        else:
            loc_getter = lambda _: folder_ids
    else:
        loc_key = "path"
        loc_getter = lambda _: None
    if col_dim_map is None:
        col_dim_map = {}

    # 遍历fix，如果fix的值为str，则认为是维度表达式，将表达式转换为成员list
    mbrs = {}
    futures = []

    for col, exp in fix.items():
        if isinstance(exp, str):
            if "(" not in exp:
                mbrs[col] = exp.split(';')
            else:
                dim = col_dim_map.get(col, col)
                loc = loc_getter(dim)
                future = evloop.apply(AsyncDimension(element_name=dim, **{loc_key: loc}).query(
                    expression=exp, fields=['name'], as_model=False
                ))

                futures.append((col, future))
        else:
            if not isinstance(exp, list):
                raise TypeError('fix参数的value只能为维度表达式(str)或维度成员(list)')
            mbrs[col] = exp

    for col, future in futures:
        dim_mbrs = future.result()
        mbrs[col] = [item['name'] for item in dim_mbrs]

    if df is None:
        df = pd.DataFrame(columns=list(fix.keys()))
    elif df.empty:
        df = pd.DataFrame(columns=list(set(df.columns) | set(fix.keys())))
    df_cartesian = pd.DataFrame(
        list(itertools.product(*mbrs.values())),
        columns=list(mbrs.keys())
    )
    # 如果df与fix的维度没有交集，增加一列临时key
    if temporary_key := not (set(df.columns) & set(fix.keys())):
        df[_TEMP_MERGE_KEY] = 1
        df_cartesian[_TEMP_MERGE_KEY] = 1

    # 补全笛卡尔积
    df = pd.merge(df, df_cartesian, how='right')

    if temporary_key:
        df.drop(columns=[_TEMP_MERGE_KEY], inplace=True)
    return df


SIZE_UNIT = ('B', 'KB', 'MB', 'GB')

AnyStr = TypeVar('AnyStr', bytes, str)


def export_file_for_download(file_name: str, file: Union[str, bytes, TextIOWrapper, IO[AnyStr], memoryview]):
    """导出文件至下载中心

    Args:
        file_name: 文件名
        file: 文件内容

    .. admonition:: 如下几种用法皆可

        .. code-block:: python

            from deepfos.lib.sysutils import export_file_for_download

            # . 直接提供文件内容字符串
            export_file_for_download('t1.txt', 'ttttt')

            # . 提供包含内容的文件
            with open('t.txt', 'r') as fp:
                export_file_for_download('t2.txt', fp)

            # . 提供包含内容的文件的bytes
            with open('t.txt', 'rb') as fp:
                export_file_for_download('t3.txt', fp.read())

            # . 提供buffer
            import io
            import pandas as pd

            buffer = io.BytesIO()
            # 将dataframe内容写入buffer
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                  pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}).to_excel(
                    writer, index=False, encoding='utf-8'
                  )

            # 上传至下载中心
            export_file_for_download('out.xlsx', buffer.getbuffer())


    """
    if hasattr(file, 'read'):
        content = file.read()
    else:
        content = file

    upload_resp = PlatformAPI().file.upload(file_type='DL',
                                            file_name=file_name,
                                            file=content)

    if upload_resp.fileSize == 0:
        logger.warning('Uploading empty file.')
        SpaceAPI().business.save(
            SpFileBusinessRecordSaveDto(
                app=OPTION.api.header['app'],
                space=OPTION.api.header['space'],
                fileName=file_name,
                createTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                fileId=upload_resp.id,
                unit='B',
                fileSize=upload_resp.fileSize,
                status='SUCCESS'
            )
        )
        return

    unit_square = math.floor(math.log(upload_resp.fileSize, 1024))

    size, unit = round(upload_resp.fileSize / (1024 ** unit_square), 2), SIZE_UNIT[unit_square]

    SpaceAPI().business.save(
        SpFileBusinessRecordSaveDto(
            app=OPTION.api.header['app'],
            space=OPTION.api.header['space'],
            fileName=file_name,
            createTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            fileId=upload_resp.id,
            unit=unit,
            fileSize=size,
            status='SUCCESS'
        )
    )


class ParamZipHelper:
    """参数解压/压缩工具

    Args:
        ori_str: 经过压缩及base64加密的str
        encoding: 如果已知原str的编码方式，则以此为准，不使用默认解码逻辑
    """
    ENCODING = ['utf-8', 'gbk', 'iso8859_1']
    _COMPRESS_LEVEL_FAST = 1
    _COMPRESS_LEVEL_TRADEOFF = 6
    _COMPRESS_LEVEL_BEST = 9

    def __init__(self, ori_str: str, encoding: str = None):
        self.ori_str = ori_str
        self.encoding = encoding or 'UTF-8'

    def decompress(self) -> str:
        """解压经过压缩及base64加密的str，返回解压后str

        Returns:
            解压后的str

        """
        original_string = gzip.decompress(base64.b64decode(self.ori_str))

        if is_java_serialized(original_string):  # pragma: no cover
            jsh = JavaDeSerializeHelper(original_string, self.encoding)
            decoded_string = jsh.read_object()
        else:
            if self.encoding:
                decoded_string = original_string.decode(self.encoding)
            else:  # pragma: no cover
                decoded_string = self._try_decode(original_string)
        return decoded_string

    def decompress_json(self) -> Union[str, dict, list]:
        """解压经过压缩及base64加密的str，返回解压后str经过json.loads后的字典

        Returns:
            解压后str经过json.loads后的字典

        """
        decoded_string = self.decompress()
        return json.loads(decoded_string)

    def compress(self, compresslevel: int = _COMPRESS_LEVEL_BEST) -> str:
        """
        将提供的str压缩并进行base64加密，返回str

        Args:
            compresslevel:  压缩率（1,6,9），详见 :class:`CompressLevel`

        Returns:
            经过压缩及base64加密的str

        """
        compressed_string = gzip.compress(self.ori_str.encode(self.encoding), compresslevel)
        return base64.b64encode(compressed_string).decode(self.encoding)

    def _try_decode(self, input_stream: bytes) -> Union[str, bytes]:
        """尝试分别用utf-8、gbk、iso8859_1来解码原bytes值，如果不能解码成功，则返回原bytes值

        Args:
            input_stream: 需解码的bytes值

        Returns:
            解码后的str或原值

        """
        for encoding in self.ENCODING:
            # noinspection PyBroadException
            try:
                decoded = input_stream.decode(encoding)
                return decoded  # pragma: no cover
            except Exception:
                pass
        # if no decode way, return raw bytes
        return input_stream


class BatchInfo:
    """批量执行明细状态类"""
    _arg_dict = {}
    _required_keys = None

    @classmethod
    def set_keys(cls, keys: List[str]):
        """设置更新明细时涉及的明细字段"""
        cls._required_keys = keys

    @classmethod
    def set_success(cls, arg: Dict):
        """设置单个明细执行结果为成功"""
        if cls._required_keys:
            cls._arg_dict[json.dumps({k: arg[k] for k in cls._required_keys})] = True
        else:
            cls._arg_dict[json.dumps(arg)] = True

    @classmethod
    def set_failure(cls, arg: Dict):
        """设置单个明细执行结果为失败"""
        if cls._required_keys:
            cls._arg_dict[json.dumps({k: arg[k] for k in cls._required_keys})] = False
        else:
            cls._arg_dict[json.dumps(arg)] = False

    @classmethod
    def batch_set_success(cls, arg: pd.DataFrame):
        """设置一批明细执行结果为成功"""
        if cls._required_keys:
            arg = arg[cls._required_keys]
        args = arg.to_dict(orient='records')
        for arg in args:
            cls._arg_dict[json.dumps(arg)] = True

    @classmethod
    def batch_set_failure(cls, arg: pd.DataFrame):
        """设置一批明细执行结果为失败"""
        if cls._required_keys:
            arg = arg[cls._required_keys]
        args = arg.to_dict(orient='records')
        for arg in args:
            cls._arg_dict[json.dumps(arg)] = False

    @classmethod
    def value(cls):
        return cls._arg_dict


class PyInfo(BaseModel):
    """任务实例执行的Python元素信息"""
    #: 元素类型
    elementType: str = "PY"
    #: 元素名称
    elementName: str = None
    #: 元素folder id
    folderId: str = None
    #: 元素path
    path: str = None


class TaskMode(str, Enum):
    """任务实例执行类型类"""
    #: 即时执行
    immediate = "immediately"
    #: 周期执行
    period = "period"
    #: 定时执行
    scheduled = "scheduled"


class ScheduledTaskInfo(BaseModel):
    """定时任务实例配置类"""
    #: 执行时间
    executeTime: datetime


class PeriodTaskInfo(BaseModel):
    """周期任务实例配置类"""
    #: 开始时间
    startTime: datetime
    #: 结束时间
    endTime: datetime
    #: 执行周期任务的 Cron 表达式
    cron: str


class TaskUtil:
    """任务实例创建方法类

    Args:
        task_code: 任务配置的唯一标识task code
        py_info: 任务实例对应的python元素信息，如未提供，仍可在 `run_job_contents` 中提供

    """

    def __init__(self, task_code, py_info: PyInfo = None):
        self.task_code = task_code
        self.api = TaskAPI(sync=True)
        if self.meta is None:
            raise ValueError(f"No config for task_code: [{self.task_code}].")
        self.py_info = py_info
        self._chunksize = 200

    @cached_property
    def meta(self):
        res = self.api.task_instance.search(TaskSearchDTO(maxVersionTask=True, taskCode=self.task_code))
        if res is not None and len(res) > 0:
            return res[0]

    info = meta

    def run_job_contents(self,
                         job_contents: Union[List, pd.DataFrame],
                         py_info: PyInfo = None,
                         mode: TaskMode = TaskMode.immediate,
                         config: Union[PeriodTaskInfo, ScheduledTaskInfo] = None
                         ):
        """执行任务实例

        Args:
            job_contents: 任务实例的明细
            py_info: 需执行的Python元素信息
            mode: 执行模式，默认为即时执行，可选周期执行或定时执行，若为后两者，需进一步提供执行配置
            config: 周期执行或定时执行时的任务配置

        """
        self._valid_params(config, job_contents, mode, py_info)

        py_info = py_info or self.py_info

        if job_contents.empty:  # pragma: no cover
            return

        self._deal_with_content_name(job_contents)

        if mode == TaskMode.immediate:
            return self._create_batch_add(job_contents, py_info)

        if mode == TaskMode.period:
            payload = PeriodicTaskCreateInfo(
                cron=config.cron,
                startTime=config.startTime.strftime('%Y-%m-%d %H:%M:%S'),
                endTime=config.endTime.strftime('%Y-%m-%d %H:%M:%S'),
                customParams=py_info.dict(),
                taskId=self.meta.id,
                upStreamIdentity=4,
                lastBatch=False
            )
            call_api = self.api.task_instance.instance_period_create
        else:
            payload = ScheduledTaskCreateInfo(
                executeTime=config.executeTime.strftime('%Y-%m-%d %H:%M:%S'),
                customParams=py_info.dict(),
                taskId=self.meta.id,
                upStreamIdentity=4,
                lastBatch=False
            )
            call_api = self.api.task_instance.instance_scheduled_create

        self._create_task_instance(call_api, job_contents, payload)

    def _valid_params(self, config, job_contents, mode, py_info):
        py_info = py_info or self.py_info

        if py_info is None:
            raise ValueError("py_info is required.")
        if py_info.elementName is None:
            raise ValueError("elementName of py_info is required.")
        if py_info.folderId is None:
            py_info.folderId = ElementBase.check_exist(ele_name=py_info.elementName,
                                                       path=py_info.path, ele_type='PY',
                                                       silent=False).folderId

        if mode == TaskMode.period and not isinstance(config, PeriodTaskInfo):
            raise ValueError('Expected config of PeriodTaskInfo type for task instance with mode: <period>.')

        if mode == TaskMode.scheduled and not isinstance(config, ScheduledTaskInfo):
            raise ValueError('Expected config of ScheduledTaskInfo type for task instance with mode: <scheduled>.')

        if isinstance(job_contents, List):
            try:
                job_contents = pd.DataFrame(job_contents)
            except Exception:
                raise ValueError('Param job_contents is not valid since it can\'t be converted to pandas DataFrame.')
        else:
            job_contents = job_contents.copy()

        not_found_col = []
        for required_col in self.meta.compositeKeys.split(','):
            if required_col not in job_contents:
                not_found_col.append(required_col)
        if not_found_col:
            raise ValueError(f'Required columns:{sorted(not_found_col)} since they are compositeKeys.')

    def _create_task_instance(self, call_api, job_contents, payload):
        if job_contents.shape[0] <= self._chunksize:
            payload.jobContent = job_contents.to_dict(orient='records')
            payload.lastBatch = True
            call_api(payload)
        else:
            payload.jobContent = job_contents.iloc[0:self._chunksize:].to_dict(orient='records')
            payload.batchId = call_api(payload).batchId
            payloads = []

            for batch_contents in split_dataframe(job_contents.iloc[self._chunksize::], self._chunksize):
                payload.jobContent = batch_contents.to_dict(orient='records')
                payloads.append(payload)

            del job_contents

            payloads[-1].lastBatch = True

            for batch_contents in payloads:
                call_api(batch_contents)

    def _create_batch_add(self, job_contents, py_info):
        payload = []
        for batch_contents in split_dataframe(job_contents, self._chunksize):
            payload.append(JobCreateDto(
                customParams=py_info.dict(),
                jobContent=batch_contents.to_dict(orient='records'),
                taskCode=self.task_code,
                upStreamIdentity=4))
        self.api.job.batch_add(payload)

    def _deal_with_content_name(self, job_contents):
        composite_keys = self.meta.compositeKeys.split(',')
        str_param = job_contents[composite_keys].astype('str')

        if self.meta.groupBy:
            groupby = self.meta.groupBy.split(',')
            others = groupby
            others.extend(set(self.meta.compositeKeys.split(',')).difference(groupby))
            job_contents['jobContentNameZhcn'] = str_param[groupby[0]].str.cat([str_param[e] for e in others[1::]],
                                                                               sep='-')
        else:
            job_contents['jobContentNameZhcn'] = str_param[composite_keys[0]].str.cat(
                [str_param[e] for e in composite_keys[1::]], sep='-')


# -----------------------------------------------------------------------------
# helper functions for AccountAPI access

@lru_cache(maxsize=128, cache_factory=SpaceSeperatedLRUCache)
def get_enterprise_code_cached():  # noqa
    return SystemAPI().space.get_tenant_code()


@lru_cache(maxsize=128, cache_factory=SpaceSeperatedLRUCache)
def get_enterprise_id_cached() -> str:
    enterprise_code = get_enterprise_code_cached()

    for enterprise in acc_api.AccountAPI().enterprise.list():
        if enterprise.enterpriseCode == enterprise_code:
            return enterprise.id

    raise ValueError(f"Unknown enterprise: {enterprise_code}")


@lru_cache(maxsize=128, cache_factory=SpaceSeperatedLRUCache)
def get_platform_info_cached() -> account_model.PlatFormSecretVO:
    return acc_api.AccountAPI().platform.secret(
        enterpriseCode=get_enterprise_code_cached()
    )


def calc_account_api_signature(
    timestamp: str,
    secret: str,
    platform_code: str,
    user_id: str = None,
):
    if user_id is None:
        user_id = OPTION.api.header['user']
    s = "&@&".join((timestamp, user_id, platform_code, secret))
    return hashlib.md5(unquote(s).encode()).hexdigest()


@lru_cache(maxsize=128, cache_factory=SpaceSeperatedLRUCache)
def get_platform_code_cached() -> str:
    space = OPTION.api.header['space']
    for enterprise in acc_api.AccountAPI().space.enterprise_space_hierarchy():
        if enterprise.spaceId == space:
            return enterprise.platformCode

    raise ValueError(f"Unknown space: {space}")


def resolve_account_api_extra_header():
    enterprise_id = get_enterprise_id_cached()
    secret = get_platform_info_cached()
    platform_code = secret.platformCode
    platform_secret = secret.platformSecret
    timestamp = str(int(time.time() * 1000))
    return {
        'enterprise-id': enterprise_id,
        'platform-code': platform_code,
        'platform-secret': platform_secret,
        'timestamp': timestamp,
        'sign': calc_account_api_signature(timestamp, platform_secret, platform_code)
    }


def batch_modify_user_group(payloads: List[UserGroupModifyDTO], max_worker: int = None):
    """批量调用用户中心用户组详情修改接口

    Args:
        payloads: 符合UserGroupModifyDTO定义的列表，将直接用作接口请求体
        max_worker: 最大并发数

    Returns: 与请求体顺序一致的返回结果列表

    """
    if max_worker is not None:
        if max_worker <= 0:
            raise ValueError('max_worker must be > 0 ')
    else:
        max_worker = len(payloads)

    result: List[Optional[bool]] = [None] * len(payloads)
    api = acc_api.AccountAPI(sync=False).user_group.space_modify_group

    async def call_api(idx: int, p: UserGroupModifyDTO, sem: asyncio.Semaphore):
        async with sem:
            result[idx] = await api(p)

    async def inner():
        semaphore = asyncio.Semaphore(max_worker)
        await asyncio.gather(*(
            call_api(idx, payload, semaphore)
            for idx, payload in enumerate(payloads)
        ))

    evloop.run(inner())
    return result
