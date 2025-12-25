from deepfos.api.base import get, post, DynamicRootAPI, ChildAPI
from .models.journal_model import *
from deepfos.lib.decorator import cached_property
from typing import Union, Awaitable

__all__ = ['JournalModelAPI']


class JournalModelData(ChildAPI):
    endpoint = '/business/model'

    @get('/config')
    def get_config(self, base: ElementDetailDTO) -> Union[JournalModelConfig, Awaitable[JournalModelConfig]]:
        return {'param': base}

    @post('data/sync/batch/save')
    def save(self, batch: ModelDataBatchDTO) -> Union[CommonResultDTO, Awaitable[CommonResultDTO]]:
        """
        【★】凭证模型-数据-异步-批量保存-只支持保存，不支持更新
    
        基于凭证模型的数据批量保存
        """
        return {'body': batch}

    @post('/data/batch/save')
    def sync_save(self, batch: ModelDataBatchDTO) -> Union[CommonResultDTO, Awaitable[CommonResultDTO]]:
        """
        【★】凭证模型-数据-同步-批量保存-只支持保存，不支持更新

        基于凭证模型的数据批量保存
        """
        return {'body': batch}

    @post('/data/update')
    def update(self, batch: ModelDataBatchDTO) -> Union[CommonResultDTO, Awaitable[CommonResultDTO]]:
        """
        【★】凭证模型-数据-单条更新-只支持头行更新及行插入和删除

        基于凭证模型的数据更新
        """
        return {'body': batch}

    @post('data/calc/net/amount')
    def calc_net_amount(self, param: JmPostParamVO) -> Union[JmPostResultVO, Awaitable[JmPostResultVO]]:
        """
        【★】凭证模型-数据-净额计算
    
        """
        return {'body': param}
    
    @post('data/check')
    def check(self, param: CheckStandardVO) -> Union[CommonResultDTO, Awaitable[CommonResultDTO]]:
        """
        【★】凭证模型-数据-标准校验
    
        标准校验
        """
        return {'body': param}
    
    @post('data/check/dc/balance')
    def check_dc_balance(self, param: JmPostParamVO) -> Union[CommonResultDTO, Awaitable[CommonResultDTO]]:
        """
        【★】凭证模型-数据-借贷平衡校验
    
        """
        return {'body': param}
    
    @post('data/delete')
    def delete(self, model_data: ModelDataDeleteDTO) -> Union[CommonResultDTO, Awaitable[CommonResultDTO]]:
        """
        【★】凭证模型-数据-删除
    
        基于凭证模型的数据删除。应用场景：清单表关联凭证模型进行数据删除
        """
        return {'body': model_data}
    
    @post('data/query/by/where')
    def query(self, param: ModelDataQueryVO) -> Union[dict, Awaitable[dict]]:
        """
        【★】凭证模型-数据-查询
    
        基于凭证模型的数据查询
        """
        return {'body': param}

    @post('deal/posting')
    def posting(self, param: JmPostParamVO) -> Union[CommonResultDTO, Awaitable[CommonResultDTO]]:
        """
        【★】凭证模型-数据-过账

        基于凭证模型的数据过账
        """
        return {'body': param}

    @post('deal/cancel-post')
    def cancel_post(self, param: JmPostParamVO) -> Union[CommonResultDTO, Awaitable[CommonResultDTO]]:
        """
        【★】凭证模型-数据-取消过账

        基于凭证模型的数据取消过账
        """
        return {'body': param}


class JournalModelAPI(DynamicRootAPI, builtin=True):
    """凭证组件接口"""
    module_type = 'JM'
    default_version = (1, 0)
    multi_version = False
    cls_name = 'JournalModelAPI'
    module_name = 'deepfos.api.journal_model'
    api_version = (1, 0)

    @cached_property
    def journal_model_data(self) -> JournalModelData:
        """
        凭证模型数据相关接口
        """
        return JournalModelData(self)
