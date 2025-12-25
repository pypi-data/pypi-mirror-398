from typing import Union, Awaitable

from deepfos.element.base import T_ElementInfoWithServer
from deepfos.lib.decorator import cached_property

from .base import ChildAPI, RootAPI, post
from .models.deepconnector import *


__all__ = ['DeepConnectorAPI']


class DataSourceAPI(ChildAPI):
    """连接信息相关接口"""
    endpoint = '/apis/v3/ds/spaces/{space}/apps/{app}'

    @post('connection-info/query', data_wrapped=False)
    def connection_info(self, element_info: T_ElementInfoWithServer) -> Union[ConnectionInfoVo, Awaitable[ConnectionInfoVo]]:
        return {
            'body': {
                'elementName': element_info.elementName,
                'folderId': element_info.folderId
            }
        }


class DeepConnectorAPI(RootAPI):
    """连接器组件接口"""
    prefix = lambda: 'http://deep-connector-server'
    url_need_format = True
    module_type = 'CONN'

    @cached_property
    def datasource(self) -> DataSourceAPI:
        """连接信息相关接口"""
        return DataSourceAPI(self)
