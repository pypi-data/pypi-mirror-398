"""Oracle客户端"""
import asyncio
from deepfos.lib.decorator import cached_property
from typing import Union, List, Iterable, TYPE_CHECKING

import pandas as pd

from deepfos.api.datatable import OracleAPI
from deepfos.cache import Manager, SpaceSeperatedTTLCache
from deepfos.lib.utils import cachedclass
from deepfos.lib.decorator import singleton
from .dbkits import BaseSqlParser, SyncMeta, T_DataInfo, DataframeSQLConvertor
from .connector import OracleAPIConnector
from .mysql import _AbsAsyncMySQLClient  # noqa


__all__ = [
    'OracleClient',
    'AsyncOracleClient',
    'OracleDFSQLConvertor'
]


class OracleDFSQLConvertor(DataframeSQLConvertor):
    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        if updatecol is not None:
            raise NotImplementedError("`updatecol` is not yet implemented for OracleDB.")

        inserts = '\n'.join(
            f'INTO {self.quote_char}{tablename.upper()}{self.quote_char} ({columns}) VALUES {value}'
            for value in values_in_line
        )

        return f'INSERT ALL {inserts} SELECT 1 FROM DUAL'

    def build_column_string(self, columns):
        return ','.join(columns.map(lambda x: f'"{x.upper()}"'))

    @staticmethod
    def format_datetime(maybe_datetime):
        return f'TO_DATE(\'' + \
               maybe_datetime.dt.strftime("%Y-%m-%d %H:%M:%S") + \
               '\', \'YYYY-MM-DD HH24:MI:SS\')'


@singleton
class SqlParser(BaseSqlParser):
    api_cls = OracleAPI

    @cached_property
    def datatable_cls(self):
        from deepfos.element.datatable import AsyncDataTableOracle
        return AsyncDataTableOracle

    @staticmethod
    async def query_table_names(api: OracleAPI, query_table):
        async def query_single(tbl_ele):
            return tbl_ele.elementName, await api.dml.get_tablename(tbl_ele)

        tablenames = await asyncio.gather(*(
            query_single(table)
            for table in query_table
        ))

        if len(tablenames) != len(query_table):
            missing = set(t.elementName for t in query_table).difference(
                set(t[0] for t in tablenames))

            raise ValueError(f"Cannot resolve actual table names for element: {missing}")
        return dict(tablenames)


# -----------------------------------------------------------------------------
# core
class _AsyncOracleClient(_AbsAsyncMySQLClient):
    convertor = OracleDFSQLConvertor(quote_char='"')

    def __init__(self, version: Union[float, str] = None):  # noqa
        self.parser = SqlParser()
        self.connector = OracleAPIConnector(version)


class _OracleClient(_AsyncOracleClient, metaclass=SyncMeta):
    synchronize = (
        'exec_sqls',
        'query_dfs',
        'insert_df',
    )

    if TYPE_CHECKING:  # pragma: no cover
        def exec_sqls(
            self,
            sqls: Union[str, Iterable[str]],
            table_info: T_DataInfo = None
        ):
            ...

        def query_dfs(
            self,
            sqls: Union[str, Iterable[str]],
            table_info: T_DataInfo = None
        ) -> Union[pd.DataFrame, List[pd.DataFrame]]:
            ...

        def insert_df(
            self,
            dataframe: pd.DataFrame,
            element_name: str = None,
            table_name: str = None,
            updatecol: Iterable[str] = None,
            table_info: T_DataInfo = None,
            chunksize: int = None,
        ):
            ...


@cachedclass(Manager.create_cache(SpaceSeperatedTTLCache, maxsize=5, ttl=3600))
class AsyncOracleClient(_AsyncOracleClient):
    pass


@cachedclass(Manager.create_cache(SpaceSeperatedTTLCache, maxsize=5, ttl=3600))
class OracleClient(_OracleClient):
    pass
