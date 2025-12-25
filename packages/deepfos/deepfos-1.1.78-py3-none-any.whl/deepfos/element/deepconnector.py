import base64
import binascii
import os

from deepfos.api.deepconnector import DeepConnectorAPI
from deepfos.api.models import BaseModel
from deepfos.db.cipher import AES
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.lib.asynchronous import future_property
from deepfos.lib.decorator import cached_property

__all__ = ['AsyncDeepConnector', 'DeepConnector', 'ConnectionInfo']


def decrypt(secret, cipher_text, encoding='utf8'):
    pwd_padded = b''
    for i in range(len(cipher_text))[::32]:
        pwd_padded += AES(secret).decrypt(
            base64.b16decode(cipher_text[i: i + 32])
        )
    if pwd_padded[-1] in range(1, 17):
        pad_length = pwd_padded[-1]
        pad_char = chr(pwd_padded[-1])
        guess_pad = pad_char * pwd_padded[-1]

        if pwd_padded.decode(encoding).endswith(guess_pad):
            return pwd_padded.decode(encoding)[:-pad_length:]
    return pwd_padded.decode(encoding)


class ConnectionInfo(BaseModel):
    host: str
    port: int
    db: str
    user: str
    password: str
    dbtype: str


# -----------------------------------------------------------------------------
# core
class AsyncDeepConnector(ElementBase[DeepConnectorAPI]):
    """连接器"""

    @cached_property
    def api(self):
        """同步API对象"""
        api = self.api_class(sync=True)
        return api

    @future_property
    async def async_api(self):
        """异步API对象"""
        return await self._init_api()

    async def _init_api(self):
        return self.api_class(sync=False)

    @future_property
    async def connection_info(self) -> ConnectionInfo:
        """当前连接器元素的连接信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        info = await api.datasource.connection_info(
            element_info=ele_info,
        )
        if info.encryptType == 'AES':
            try:
                password = decrypt(
                    os.environ.get('EXPORT_DEEPFOS_AES_KEY', '!ABCD-EFGH-IJKL@').encode(),
                    info.password,
                    encoding='utf-8'
                )
            except ValueError:
                raise ValueError(
                    '连接器连接信息解密失败，请检查公共环境变量：EXPORT_DEEPFOS_AES_KEY'
                ) from None
        else:
            try:
                password = base64.decodebytes(info.password.encode()).decode()
            except binascii.Error:
                password = info.password
        return ConnectionInfo(
            host=info.connectionHost,
            port=info.connectionPort,
            db=info.dbName,
            user=info.username,
            password=password,
            dbtype=info.serviceName,
        )


class DeepConnector(AsyncDeepConnector, metaclass=SyncMeta):
    pass
