from typing import Union, Awaitable, List, Any, Dict, Literal

from deepfos.lib.decorator import cached_property
from .base import DynamicRootAPI, ChildAPI, get, post
from .models.deepmodel import *

__all__ = ['DeepModelAPI']


class ObjectAPI(ChildAPI):
    """模型对象相关"""
    endpoint = '/object'

    @get('all/get')
    def get_all(self, ) -> Union[ObjectOperationParam, Awaitable[ObjectOperationParam]]:
        return {}

    @get('list')
    def list(self, ) -> Union[List[ObjectBasicDTO], Awaitable[List[ObjectBasicDTO]]]:
        return {}

    @get('info')
    def info(self, app: str = None, object_code: str = None) -> Union[ObjectParam, Awaitable[ObjectParam]]:
        return {'param': {'app': app, 'objectCode': object_code}}


class RuleAPI(ChildAPI):
    """规则清单相关"""
    endpoint = '/rules'

    @get('/')
    def info(self, app: str = None, object_code: str = None, trigger_type: Literal['BEFORE_CREATE_SAVE', 'BEFORE_UPDATE_SAVE'] = None) -> Union[List[RuleInfoRes], Awaitable[List[RuleInfoRes]]]:
        """获取业务规则清单

        Args:
            app: 对象所属app
            object_code: 对象编码
            trigger_type: 规则触发时机(BEFORE_CREATE_SAVE - 数据新建保存前; BEFORE_UPDATE_SAVE - 数据更新保存前)

        """
        return {'param': {'app': app, 'objectCode': object_code, 'triggerType': trigger_type}}


class SeqAPI(ChildAPI):
    """序列生成相关"""
    endpoint = '/sequence'

    @post('/instance/edit')
    def edit(self, current_value: int = None, seq_id: str = None, seq_key: str = None, seq_name: str = None) -> Union[None, Awaitable[None]]:
        """修改序列实例

        Args:
            current_value: 当前值
            seq_id: 序列编号
            seq_key: 序列主键
            seq_name: 序列名称

        """
        return {'body': {"currentValue": current_value, "sequenceId": seq_id, "sequenceKey": seq_key, "sequenceName": seq_name}}

    @get('/instance/next-value')
    def next_value(self, code: str = None, seq_key: str = None) -> Union[int, Awaitable[int]]:
        """获取序列实例的最新值

        Args:
            code: 序列编码
            seq_key: 序列主键

        """
        return {'param': {'code': code, 'sequenceKey': seq_key}}

    @get('/instances')
    def list(self, id: str = None, filter_value: str = None) -> Union[List[SequenceInstance], Awaitable[List[SequenceInstance]]]:
        """获取序列的实例清单

        无入参获取所有序列，有入参按照入参匹配序列编码

        Args:
            id: 序列编号
            filter_value: 过滤值

        """
        return {'param': {'id': id, 'filterValue': filter_value}}


class ShardingAPI(ChildAPI):
    """分库信息"""
    endpoint = '/sharding'

    @get('database')
    def database(self, ) -> Union[SimpleSpaceConnectionConfig, Awaitable[SimpleSpaceConnectionConfig]]:
        return {}


class DeepQLAPI(ChildAPI):
    """查询器"""
    endpoint = '/public/deepql/actions'

    @post('query')
    def query(self, module: str = None, query: str = None, variables: Dict = None) -> Union[QueryResult, Awaitable[QueryResult]]:
        return {'body': {'module': module, 'query': query, 'variables': variables}}

    @post('execute')
    def execute(self, module: str = None, query: str = None, variables: Dict = None) -> Union[Any, Awaitable[Any]]:
        return {'body': {'module': module, 'query': query, 'variables': variables}}


class PresentationAPI(ChildAPI):
    """展示层"""
    endpoint = '/presentation-layer'

    @get('ql-selector/ql-record-info')
    def ql_record_info(self, qlType: str, recordCode: str) -> Union[QlRecordVO, Awaitable[QlRecordVO]]:
        """获取单条记录

        Args:
            qlType: 查询类型 'deepql'|'analysisql'
            recordCode: 查询编码

        """
        return {'param': {'qlType': qlType, 'recordCode': recordCode}}

    @get('ql-selector/ql-records')
    def ql_records(self, qlType: str = None, qlRecordType: str = None) -> Union[List[QlRecordVO], Awaitable[List[QlRecordVO]]]:
        """获取所有的ql记录

        Args:
            qlType: 查询类型 'deepql'|'analysisql'
            qlRecordType: 记录类型：个人PERSONAL /公共：PUBLIC

        Returns:

        """
        return {'param': {'qlType': qlType, 'qlRecordType': qlRecordType}}


class ExtraAPI(ChildAPI):
    """其他接口"""
    endpoint = '/'

    @get('git-version')
    def version(self, ) -> Union[str, Awaitable[str]]:
        return {}


class DeepModelAPI(DynamicRootAPI, builtin=True):
    """DeepModel组件接口"""
    module_type = 'DM'
    default_version = (1, 0)
    multi_version = False
    cls_name = 'DeepModelAPI'
    module_name = 'deepfos.api.deepmodel'
    api_version = (1, 0)

    @cached_property
    def object(self) -> ObjectAPI:
        """模型对象相关"""
        return ObjectAPI(self)

    @cached_property
    def deepql(self) -> DeepQLAPI:
        """查询器"""
        return DeepQLAPI(self)

    @cached_property
    def rule(self) -> RuleAPI:
        """规则清单相关"""
        return RuleAPI(self)

    @cached_property
    def seq(self) -> SeqAPI:
        """序列生成相关"""
        return SeqAPI(self)

    @cached_property
    def sharding(self) -> ShardingAPI:
        """分库信息"""
        return ShardingAPI(self)

    @cached_property
    def presentation(self) -> PresentationAPI:
        """展示层"""
        return PresentationAPI(self)

    @cached_property
    def extra(self) -> ExtraAPI:
        """其他接口"""
        return ExtraAPI(self)
