"""Dameng客户端"""
import asyncio
from typing import Union, List, Iterable, TYPE_CHECKING

import pandas as pd

from deepfos.api.datatable import DaMengAPI
from deepfos.cache import Manager, SpaceSeperatedTTLCache
from deepfos.lib.utils import cachedclass
from deepfos.lib.decorator import singleton, cached_property
from deepfos.db.oracle import OracleDFSQLConvertor
from .dbkits import SyncMeta, T_DataInfo, BaseSqlParser
from .connector import DaMengAPIConnector
from .mysql import _AbsAsyncMySQLClient  # noqa


__all__ = [
    'DaMengClient',
    'AsyncDaMengClient',
]


@singleton
class SqlParser(BaseSqlParser):
    api_cls = DaMengAPI

    @cached_property
    def datatable_cls(self):
        from deepfos.element.datatable import AsyncDataTableDaMeng
        return AsyncDataTableDaMeng

    @staticmethod
    async def query_table_names(api: DaMengAPI, query_table):  # pragma: no cover
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
class _AsyncDaMengClient(_AbsAsyncMySQLClient):
    convertor = OracleDFSQLConvertor(quote_char='"')

    def __init__(self, version: Union[float, str] = None):  # noqa
        self.parser = SqlParser()
        self.connector = DaMengAPIConnector(version)


class _DaMengClient(_AsyncDaMengClient, metaclass=SyncMeta):
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
class AsyncDaMengClient(_AsyncDaMengClient):
    pass


@cachedclass(Manager.create_cache(SpaceSeperatedTTLCache, maxsize=5, ttl=3600))
class DaMengClient(_DaMengClient):
    pass
