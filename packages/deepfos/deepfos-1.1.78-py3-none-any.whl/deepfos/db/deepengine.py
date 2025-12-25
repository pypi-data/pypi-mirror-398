"""DeepEngine客户端"""
from typing import Union, List, Iterable, TYPE_CHECKING

import pandas as pd

from deepfos.api.datatable import DeepEngineAPI
from deepfos.cache import Manager, SpaceSeperatedTTLCache
from deepfos.lib.utils import cachedclass
from deepfos.lib.decorator import singleton, cached_property
from .dbkits import BaseSqlParser, SyncMeta, T_DataInfo
from .connector import DeepEngineAPIConnector
from .mysql import _AbsAsyncMySQLClient, MySQLConvertor  # noqa


__all__ = [
    'DeepEngineClient',
    'AsyncDeepEngineClient',
    'DeepEngineDFSQLConvertor',
]


@singleton
class SqlParser(BaseSqlParser):
    api_cls = DeepEngineAPI

    @cached_property
    def datatable_cls(self):
        from deepfos.element.datatable import AsyncDataTableDeepEngine
        return AsyncDataTableDeepEngine


class DeepEngineDFSQLConvertor(MySQLConvertor):
    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        if updatecol is not None:
            raise NotImplementedError("`updatecol` is not yet implemented for DeepEngineDB.")

        return super().build_sql(columns, values_in_line, tablename, updatecol, **opts)


# -----------------------------------------------------------------------------
# core
class _AsyncDeepEngineClient(_AbsAsyncMySQLClient):
    convertor = DeepEngineDFSQLConvertor(quote_char='`')

    def __init__(self, version: Union[float, str] = None):  # noqa
        self.parser = SqlParser()
        self.connector = DeepEngineAPIConnector(version)
        self.connector.trxn_execute = self.connector.execute_many


class _DeepEngineClient(_AsyncDeepEngineClient, metaclass=SyncMeta):
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
class AsyncDeepEngineClient(_AsyncDeepEngineClient):
    pass


@cachedclass(Manager.create_cache(SpaceSeperatedTTLCache, maxsize=5, ttl=3600))
class DeepEngineClient(_DeepEngineClient):
    pass
