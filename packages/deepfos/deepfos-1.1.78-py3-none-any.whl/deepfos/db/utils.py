import asyncio
import base64

from deepfos.api.python import PythonAPI
from deepfos.api.models.python import WorkerRegistry

from deepfos.lib.utils import retry, Wait
from deepfos.lib.constant import UNSET
from deepfos.lib.asynchronous import evloop
from deepfos.options import OPTION
from deepfos.exceptions import APIResponseError
from .cipher import AES
from deepfos.api.datatable import (MySQLAPI, ClickHouseAPI, SQLServerAPI, OracleAPI, KingBaseAPI,
                                   GaussAPI, DaMengAPI, PostgreSQLAPI, DeepEngineAPI)

# -----------------------------------------------------------------------------
# constants
PENDING = 0
INITIALIZING = 1
INITIALIZED = 2
#: 账号失效时间
ACCOUNT_EXPIRE = 3600 * 8


class DBConnecetionError(Exception):
    pass


class AbsLeaseManager:
    DB = None

    def __init__(self, interval):
        self._last_renewal = None
        self._interval = interval
        self._task = UNSET
        self._info = UNSET
        self._renew_fn = None

    async def new_api(self):  # pragma: no cover
        raise NotImplementedError

    async def _try_renewal(self, api, raises=False):
        try:
            return True, await api.dml.create_account()
        except APIResponseError as e:
            if raises:
                raise
            py_api = await PythonAPI(version=2.0, sync=False)
            await py_api.worker.register(WorkerRegistry(
                hostname=OPTION.general.task_info['worker_name'],
                db=[self.DB]
            ))
            return False, e

    @retry(wait=Wait(0.5, 'exp_backoff', 2), retries=4)
    async def renew(self):
        api = await self.new_api()

        flag, account = await self._try_renewal(api)
        if flag is False:  # retry once
            _, account = await self._try_renewal(api, raises=True)

        self._info = account
        return account

    async def loop(self, slow_start=True):
        if slow_start:
            await asyncio.sleep(self._interval)
        while True:
            await self.renew()
            await asyncio.sleep(self._interval)

    def schedule(self, slow_start=True):
        if self._task is UNSET:
            try:
                asyncio.get_running_loop()
                self._task = asyncio.create_task(
                    self.loop(slow_start))
            except RuntimeError:
                self._task = evloop.create_task(
                    self.loop(slow_start))

    def cancel(self):
        if self._task is not UNSET:
            self._task.cancel()
            self._task = UNSET


def decrypt(secret, cipher_text, encoding='utf8'):
    return AES(secret).decrypt(
        base64.b16decode(cipher_text)
    ).rstrip().decode(encoding)


def get_client_class(
    element_type: str,
    sync: bool = True
):
    """
    根据元素类型获取对应的数据表元素类

    Args:
        element_type: 元素类型
        sync: 同步或异步元素类，默认同步

    """
    from deepfos.db import (MySQLClient, AsyncMySQLClient,
                            ClickHouseClient, AsyncClickHouseClient,
                            OracleClient, AsyncOracleClient,
                            SQLServerClient, AsyncSQLServerClient,
                            KingBaseClient, AsyncKingBaseClient,
                            GaussClient, AsyncGaussClient,
                            DaMengClient, AsyncDaMengClient,
                            PostgreSQLClient, AsyncPostgreSQLClient,
                            DeepEngineClient, AsyncDeepEngineClient)
    if sync:
        index = 0
    else:
        index = 1
    cli = {
        MySQLAPI.module_type: (MySQLClient, AsyncMySQLClient),
        ClickHouseAPI.module_type: (ClickHouseClient, AsyncClickHouseClient),
        SQLServerAPI.module_type: (SQLServerClient, AsyncSQLServerClient),
        OracleAPI.module_type: (OracleClient, AsyncOracleClient),
        KingBaseAPI.module_type: (KingBaseClient, AsyncKingBaseClient),
        GaussAPI.module_type: (GaussClient, AsyncGaussClient),
        DaMengAPI.module_type: (DaMengClient, AsyncDaMengClient),
        PostgreSQLAPI.module_type: (PostgreSQLClient, AsyncPostgreSQLClient),
        DeepEngineAPI.module_type: (DeepEngineClient, AsyncDeepEngineClient),
    }.get(element_type.upper())

    if cli is None:
        raise TypeError(f"Unknown module type: {element_type}")
    else:
        return cli[index]
