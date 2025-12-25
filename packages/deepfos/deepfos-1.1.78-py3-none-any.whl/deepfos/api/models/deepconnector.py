from typing import Optional, Dict

from .base import BaseModel

__all__ = [
    "ConnectionInfoVo"
]


class ConnectionInfoVo(BaseModel):
    authMethod: Optional[str] = None
    connectionHost: str
    connectionPort: int
    dbName: str
    elementName: Optional[str] = None
    encryption: bool
    extraParam: Optional[str] = None
    folderId: str
    folderPath: str
    i18nName: Optional[Dict[str, str]] = None
    id: str
    password: str
    serviceCode: Optional[str] = None
    serviceName: str
    serviceType: Optional[int] = None
    serviceTypeName: Optional[str] = None
    serviceVersion: Optional[str] = None
    username: str
    encryptType: Optional[str] = None
