import time
from reprlib import aRepr
import warnings

from loguru import logger
from cachetools import TTLCache
import clickhouse_driver
import threading

from deepfos import OPTION
from deepfos.api.datatable import ClickHouseAPI
from deepfos.lib.constant import UNSET
from deepfos.lib.asynchronous import register_on_loop_shutdown
from .utils import (
    decrypt, AbsLeaseManager, ACCOUNT_EXPIRE,
    PENDING, INITIALIZED, INITIALIZING, DBConnecetionError
)

aRepr.maxstring = 200


# cdef class ClientCH:
#     cdef:
#         object  conn
#         int status
#         object  inited
#         object  lease
#         bytes secret

class ClientCH:
    def __init__(self):
        self.conn = UNSET
        self.status = PENDING
        self.inited = threading.Event()
        self.lease = LeaseManagerCH(ACCOUNT_EXPIRE / 3)
        self.secret = "!ABCD-EFGH-IJKL@".encode()

    async def establish_conn(self):
        if self.status == INITIALIZED:
            return self.conn

        if self.status == PENDING:
            self.status = INITIALIZING
        else:
            self.inited.wait()
            if self.status != INITIALIZED:
                raise RuntimeError("Failed to initialze connection pool.")
            return self.conn

        conf = await self.lease.renew()
        self.lease.schedule(slow_start=True)
        register_on_loop_shutdown(self.close)

        conn_info = {
            'host': conf.host,
            'database': conf.dbName,
            'user': conf.name,
            'password': decrypt(self.secret, conf.password),
            'port': conf.port,
            'settings': {'use_numpy': True}
        }

        try:
            self.conn = clickhouse_driver.Client(**conn_info)
            self.conn.connection.force_connect()
        except Exception as e:
            self.status = PENDING
            raise DBConnecetionError(e) from None
        if not self.conn.connection.connected:
            self.status = PENDING
            raise DBConnecetionError("Not a valid connection")

        self.status = INITIALIZED
        self.inited.set()
        return self.conn

    async def ensure_connected(self):
        max_retry = 3
        retries = 0
        interval = 0.5

        while self.conn is UNSET or not self.conn.connection.connected:
            try:
                await self.establish_conn()
            except DBConnecetionError:
                retries += 1
                if retries > max_retry:
                    self.inited.set()
                    raise
                logger.exception(f'Failed to establish connection, '
                                 f'starting {retries} times retry.')
                time.sleep(interval)
                interval *= 2
            except Exception:
                self.inited.set()
                self.status = PENDING
                raise

        return self.conn

    async def execute(self, sql):
        conn = await self.ensure_connected()
        logger.opt(lazy=True).debug("Run sql: {sql}", sql=lambda: aRepr.repr(sql))
        return conn.execute(sql)

    async def select(self, sql):
        conn = await self.ensure_connected()
        logger.opt(lazy=True).debug("Run sql: {sql}", sql=lambda: aRepr.repr(sql))
        return conn.execute(sql)

    async def query_dataframe(self, sql):
        conn = await self.ensure_connected()
        logger.opt(lazy=True).debug("Run sql: {sql}", sql=lambda: aRepr.repr(sql))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            return conn.query_dataframe(sql)

    async def insert_dataframe(self, table, dataframe):
        query = f"INSERT INTO `{table}` VALUES"
        conn = await self.ensure_connected()
        logger.debug(f"Run sql : {query} ...")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            return conn.insert_dataframe(query, dataframe)

    def close(self):
        self.lease.cancel()
        self.status = PENDING

        if self.conn is not UNSET:
            self.conn.disconnect()
            self.conn = UNSET


# cdef class ClientManager:
class ClientManager:
    cache = TTLCache(maxsize=10, ttl=1800)

    def new_client(self):
        key = (
            OPTION.api.header.get('space'),
            OPTION.api.header.get('app'),
        )

        if key not in self.cache:
            self.cache[key] = ClientCH()

        return self.cache[key]


class LeaseManagerCH(AbsLeaseManager):
    DB = 'clickhouse'

    async def new_api(self):
        return await ClickHouseAPI(version=1.0, sync=False)


async def select(sql):
    return await ClientManager().new_client().select(sql)


async def execute(sql):
    return await ClientManager().new_client().execute(sql)


async def query_dataframe(sql):
    return await ClientManager().new_client().query_dataframe(sql)


async def insert_dataframe(table, dataframe):
    return await ClientManager().new_client().insert_dataframe(table, dataframe)
