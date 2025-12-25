from reprlib import aRepr
import asyncio

from loguru import logger
from cachetools import TTLCache
import pandas as pd
import aiomysql
from pymysql.constants import FIELD_TYPE

from deepfos import OPTION
from deepfos.api.datatable import MySQLAPI
from deepfos.lib.constant import UNSET
from deepfos.lib.asynchronous import register_on_loop_shutdown
from .utils import (
    decrypt, AbsLeaseManager, ACCOUNT_EXPIRE,
    PENDING, INITIALIZED, INITIALIZING, DBConnecetionError
)

aRepr.maxstring = 200


# cdef class Client:
#     cdef:
#         object  pool
#         int status
#         object  inited
#         object  lease
#         bytes secret
class Client:
    def __init__(self):
        self.pool = UNSET
        self.status = PENDING
        self.inited = asyncio.Event()
        self.lease = LeaseManager(ACCOUNT_EXPIRE / 3)
        self.secret = "!ABCD-EFGH-IJKL@".encode()
        register_on_loop_shutdown(self.close, True)

    async def init_pool(self):
        if self.status == INITIALIZED:
            return self.pool

        if self.status == PENDING:
            self.status = INITIALIZING
        else:
            await self.inited.wait()
            if self.status != INITIALIZED:
                raise RuntimeError("Failed to initialze connection pool.")
            return self.pool

        conf = await self.lease.renew()
        self.lease.schedule(slow_start=True)

        try:
            self.pool = await aiomysql.create_pool(
                minsize=5,
                maxsize=10,
                host=conf.host,
                port=conf.port,
                user=conf.name,
                password=decrypt(self.secret, conf.password),
                db=conf.dbName,
            )
        except Exception as e:
            self.status = PENDING
            raise DBConnecetionError(e) from None
        else:
            self.status = INITIALIZED
            self.inited.set()
            return self.pool

    async def ensure_connected(self):
        max_retry = 3
        retries = 0
        interval = 0.5

        while self.pool is UNSET or self.pool._closed:  # noqa
            retries += 1
            try:
                await self.init_pool()
            except DBConnecetionError:
                if retries > max_retry:
                    self.inited.set()
                    raise
                logger.exception(f'Failed to get connection pool, '
                                 f'starting {retries} times retry.')
                await asyncio.sleep(interval)
                interval *= 2
            except Exception:
                self.inited.set()
                self.status = PENDING
                raise

        return self.pool

    async def execute(self, sql):
        pool = await self.ensure_connected()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                logger.opt(lazy=True).debug("Run sql: {sql}",
                                            sql=lambda: aRepr.repr(sql))
                await cur.execute(sql)
            await conn.commit()
            return conn.affected_rows()

    async def select(self, sql):
        pool = await self.ensure_connected()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                logger.opt(lazy=True).debug("Run sql: {sql}",
                                            sql=lambda: aRepr.repr(sql))
                await cur.execute(sql)
                return await cur.fetchall()

    async def query_dataframe(self, sql):
        pool = await self.ensure_connected()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                logger.opt(lazy=True).debug("Run sql: {sql}",
                                            sql=lambda: aRepr.repr(sql))
                await cur.execute(sql)
                columns = [d[0] for d in cur.description]
                decimal_cols = [
                    d[0] for d in cur.description
                    if d[1] == FIELD_TYPE.NEWDECIMAL
                ]
                data = await cur.fetchall()
                df = pd.DataFrame(data=data, columns=columns)
                for col in decimal_cols:
                    df[col] = pd.to_numeric(df[col], downcast='float')
                return df

    async def trxn_execute(self, sqls):
        pool = await self.ensure_connected()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                logger.opt(lazy=True).debug("Run sql: {sql}",
                                            sql=lambda: aRepr.repr(sqls))
                for sql in sqls:
                    await cur.execute(sql)
            await conn.commit()
            return conn.affected_rows()

    async def close(self):
        self.lease.cancel()
        self.status = PENDING

        if self.pool is not UNSET:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = UNSET


# cdef class ClientManager:
class ClientManager:
    cache = TTLCache(maxsize=10, ttl=1800)

    def new_client(self):
        key = (
            OPTION.api.header.get('space'),
            OPTION.api.header.get('app'),
        )

        if key not in self.cache:
            self.cache[key] = Client()

        return self.cache[key]


class LeaseManager(AbsLeaseManager):
    DB = 'mysql'

    async def new_api(self):
        return await MySQLAPI(version=1.0, sync=False)


async def select(sql):
    return await ClientManager().new_client().select(sql)


async def execute(sql):
    return await ClientManager().new_client().execute(sql)


async def query_dataframe(sql):
    return await ClientManager().new_client().query_dataframe(sql)


async def trxn_execute(sqls):
    return await ClientManager().new_client().trxn_execute(sqls)
