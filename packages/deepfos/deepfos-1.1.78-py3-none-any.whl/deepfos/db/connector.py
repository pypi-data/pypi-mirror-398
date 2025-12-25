import asyncio
from abc import ABC, abstractmethod
from typing import Union, List

import pandas as pd

from deepfos.api.datatable import MySQLAPI, ClickHouseAPI, OracleAPI, SQLServerAPI, KingBaseAPI, GaussAPI, DaMengAPI, \
    PostgreSQLAPI, DeepEngineAPI, DeepModelAPI, DeepModelKingBaseAPI
from deepfos.lib.asynchronous import cache_async
from .dbkits import APIFinder
from . import daclickhouse
from . import damysql

__all__ = [
    'AbstractConnector',
    'MySQLAPIConnector',
    'MySQLDirectAccess',
    'ClickHouseAPIConnector',
    'ClickHouseDirectAccess',
    'SQLServerAPIConnector',
    'OracleAPIConnector',
    'GaussAPIConnector',
    'KingBaseAPIConnector',
    'DaMengAPIConnector',
    'PostgreSQLAPIConnector',
    'DeepEngineAPIConnector',
    'DeepModelAPIConnector',
    'DeepModelKingBaseAPIConnector',
]


class AbstractConnector(ABC):  # pragma: no cover
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    async def execute(self, sql: str):
        pass

    @abstractmethod
    async def execute_many(self, sqls: List[str]):
        pass

    @abstractmethod
    async def trxn_execute(self, sqls: List[str]):
        pass

    @abstractmethod
    async def select(self, sql: str):
        pass

    @abstractmethod
    async def query_dataframe(self, sql: str) -> pd.DataFrame:
        pass


class MySQLAPIConnector(AbstractConnector):
    def __init__(  # noqa
        self,
        version: Union[float, str] = None,
    ):
        self._v = version

    @cache_async
    async def build_api(self) -> MySQLAPI:
        return await APIFinder().find_api(MySQLAPI, version=self._v)

    async def execute(self, sql: str):
        api = await self.build_api()
        return await api.dml.run_sql(sql)

    async def execute_many(self, sqls: List[str]):
        api = await self.build_api()
        return await asyncio.gather(
            *(api.dml.run_sql(sql) for sql in sqls)
        )

    async def trxn_execute(self, sqls: List[str]):
        api = await self.build_api()
        return await api.dml.execute_batch_sql(sqls)

    select = execute

    async def query_dataframe(self, sql: str) -> pd.DataFrame:
        api = await self.build_api()
        resp = await api.dml.run_sql(sql)
        select_data = [item or {} for item in resp.selectResult]
        return pd.DataFrame.from_records(select_data)


class ClickHouseAPIConnector(MySQLAPIConnector):
    async def trxn_execute(self, sqls: List[str]):
        raise NotImplementedError('ClickHouse does not support transaction')

    @cache_async
    async def build_api(self) -> ClickHouseAPI:
        return await APIFinder().find_api(ClickHouseAPI, version=self._v)


class MySQLDirectAccess(AbstractConnector):
    async def execute(self, sql: str):
        return await damysql.execute(sql)

    async def execute_many(self, sqls: List[str]):
        return await asyncio.gather(
            *(damysql.execute(sql) for sql in sqls)
        )

    async def trxn_execute(self, sqls: List[str]):
        return await damysql.trxn_execute(sqls)

    async def select(self, sql: str):
        return await damysql.select(sql)

    async def query_dataframe(self, sql: str) -> pd.DataFrame:
        return await damysql.query_dataframe(sql)


class ClickHouseDirectAccess(AbstractConnector):
    async def execute(self, sql: str):
        return await daclickhouse.execute(sql)

    async def execute_many(self, sqls: List[str]):
        return await asyncio.gather(
            *(daclickhouse.execute(sql) for sql in sqls)
        )

    async def trxn_execute(self, sqls: List[str]):
        raise NotImplementedError('ClickHouse does not support transaction')

    async def select(self, sql: str):
        return await daclickhouse.select(sql)

    async def query_dataframe(self, sql: str) -> pd.DataFrame:
        return await daclickhouse.query_dataframe(sql)

    async def insert_dataframe(self, table: str, dataframe: pd.DataFrame):  # noqa
        return await daclickhouse.insert_dataframe(table, dataframe)


class SQLServerAPIConnector(MySQLAPIConnector):
    @cache_async
    async def build_api(self) -> SQLServerAPI:
        return await APIFinder().find_api(SQLServerAPI, version=self._v)


class OracleAPIConnector(MySQLAPIConnector):
    @cache_async
    async def build_api(self) -> OracleAPI:
        return await APIFinder().find_api(OracleAPI, version=self._v)


class KingBaseAPIConnector(MySQLAPIConnector):
    @cache_async
    async def build_api(self) -> KingBaseAPI:
        return await APIFinder().find_api(KingBaseAPI, version=self._v)


class GaussAPIConnector(MySQLAPIConnector):
    @cache_async
    async def build_api(self) -> GaussAPI:
        return await APIFinder().find_api(GaussAPI, version=self._v)


class DaMengAPIConnector(MySQLAPIConnector):
    @cache_async
    async def build_api(self) -> DaMengAPI:
        return await APIFinder().find_api(DaMengAPI, version=self._v)


class PostgreSQLAPIConnector(MySQLAPIConnector):
    @cache_async
    async def build_api(self) -> PostgreSQLAPI:
        return await APIFinder().find_api(PostgreSQLAPI, version=self._v)


class DeepEngineAPIConnector(ClickHouseAPIConnector):
    @cache_async
    async def build_api(self) -> DeepEngineAPI:
        return await APIFinder().find_api(DeepEngineAPI, version=self._v)

    async def trxn_execute(self, sqls: List[str]):
        raise NotImplementedError('DeepEngine does not support transaction')


class DeepModelAPIConnector(MySQLAPIConnector):
    @cache_async
    async def build_api(self) -> DeepModelAPI:
        return await APIFinder().find_api(DeepModelAPI, version=self._v)


class DeepModelKingBaseAPIConnector(KingBaseAPIConnector):
    @cache_async
    async def build_api(self) -> DeepModelKingBaseAPI:
        return await APIFinder().find_api(DeepModelKingBaseAPI, version=self._v)
