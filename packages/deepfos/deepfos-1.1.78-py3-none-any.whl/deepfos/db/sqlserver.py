"""SQLServer客户端"""
from deepfos.lib.decorator import cached_property
from typing import Union, List, Iterable, TYPE_CHECKING

import pandas as pd

from deepfos.api.datatable import SQLServerAPI
from deepfos.cache import Manager, SpaceSeperatedTTLCache
from deepfos.lib.utils import cachedclass
from deepfos.lib.decorator import singleton
from .dbkits import BaseSqlParser, SyncMeta, T_DataInfo
from .connector import SQLServerAPIConnector
from .mysql import _AbsAsyncMySQLClient, MySQLConvertor  # noqa


__all__ = [
    'SQLServerClient',
    'AsyncSQLServerClient',
    'SQLServerDFSQLConvertor',
]


@singleton
class SqlParser(BaseSqlParser):
    api_cls = SQLServerAPI

    @cached_property
    def datatable_cls(self):
        from deepfos.element.datatable import AsyncDataTableSQLServer
        return AsyncDataTableSQLServer


class SQLServerDFSQLConvertor(MySQLConvertor):
    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        if updatecol is not None:
            raise NotImplementedError("`updatecol` is not yet implemented for SQLServerDB.")

        return super().build_sql(columns, values_in_line, tablename, None, **opts)


# -----------------------------------------------------------------------------
# core
class _AsyncSQLServerClient(_AbsAsyncMySQLClient):
    convertor = SQLServerDFSQLConvertor(quote_char="")

    def __init__(self, version: Union[float, str] = None):  # noqa
        self.parser = SqlParser()
        self.connector = SQLServerAPIConnector(version)


class _SQLServerClient(_AsyncSQLServerClient, metaclass=SyncMeta):
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
class AsyncSQLServerClient(_AsyncSQLServerClient):
    pass


@cachedclass(Manager.create_cache(SpaceSeperatedTTLCache, maxsize=5, ttl=3600))
class SQLServerClient(_SQLServerClient):
    pass
