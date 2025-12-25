"""DeepModel数据表客户端"""
from deepfos.lib.decorator import cached_property
from typing import Union, List, Iterable, TYPE_CHECKING

import pandas as pd

from deepfos.api.datatable import DeepModelAPI
from deepfos.cache import Manager, SpaceSeperatedTTLCache
from deepfos.lib.utils import cachedclass
from deepfos.lib.decorator import singleton
from .dbkits import BaseSqlParser, SyncMeta, T_DataInfo
from .connector import DeepModelAPIConnector
from .postgresql import _AsyncPostgreSQLClient


__all__ = [
    'DeepModelClient',
    'AsyncDeepModelClient',
]


@singleton
class SqlParser(BaseSqlParser):
    api_cls = DeepModelAPI

    @cached_property
    def datatable_cls(self):
        from deepfos.element.datatable import AsyncDataTableDeepModel
        return AsyncDataTableDeepModel


# -----------------------------------------------------------------------------
# core
class _AsyncDeepModelClient(_AsyncPostgreSQLClient):
    def __init__(self, version: Union[float, str] = None):  # noqa
        self.parser = SqlParser()
        self.connector = DeepModelAPIConnector(version)


class _DeepModelClient(_AsyncDeepModelClient, metaclass=SyncMeta):
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
            conflict_target: Iterable[str] = None,
        ):
            ...


@cachedclass(Manager.create_cache(SpaceSeperatedTTLCache, maxsize=5, ttl=3600))
class AsyncDeepModelClient(_AsyncDeepModelClient):
    pass


@cachedclass(Manager.create_cache(SpaceSeperatedTTLCache, maxsize=5, ttl=3600))
class DeepModelClient(_DeepModelClient):
    pass
