"""数据库连接类"""
import asyncio
from typing import Union, List, Iterable, TYPE_CHECKING

import pandas as pd
from cachetools import TTLCache

from deepfos.api.datatable import ClickHouseAPI
from deepfos.cache import Manager
from deepfos.lib.utils import cachedclass, split_dataframe
from deepfos.lib.decorator import singleton, cached_property
from deepfos.options import OPTION
from .dbkits import BaseSqlParser, SyncMeta, T_DataInfo
from .connector import ClickHouseAPIConnector, ClickHouseDirectAccess
from .mysql import _AbsAsyncMySQLClient, MySQLConvertor  # noqa


__all__ = [
    'ClickHouseClient',
    'AsyncClickHouseClient',
    'ClickHouseConvertor',
]


@singleton
class SqlParser(BaseSqlParser):
    api_cls = ClickHouseAPI

    @cached_property
    def datatable_cls(self):
        from deepfos.element.datatable import AsyncDataTableClickHouse
        return AsyncDataTableClickHouse


class ClickHouseConvertor(MySQLConvertor):
    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        if updatecol is not None:
            raise NotImplementedError("`updatecol` is not yet implemented for ClickHouseDB.")

        return super().build_sql(columns, values_in_line, tablename, updatecol, **opts)


# -----------------------------------------------------------------------------
# core
class APIBasedClient(_AbsAsyncMySQLClient):
    convertor = ClickHouseConvertor(quote_char='`')

    def __init__(self, version: Union[float, str] = None):  # noqa
        self.parser = SqlParser()
        self.connector = ClickHouseAPIConnector(version)
        self.connector.trxn_execute = self.connector.execute_many


class DirectAccessClient:
    def __init__(self, version: Union[float, str] = None):
        self.parser = SqlParser()
        self.connector = ClickHouseDirectAccess(version)

    async def exec_sqls(
        self,
        sqls: Union[str, Iterable[str]],
        table_info: T_DataInfo = None
    ):
        """执行多句sql

        Args:
            sqls: 要执行的sql语句，str或多句sql的list
            table_info: sql中表名占位符对应的数据表元素信息。

        """

        if isinstance(sqls, str):
            sqls = [sqls]

        parsed_sql = await self.parser.parse(sqls, table_info)
        return await self.connector.execute_many(parsed_sql)

    async def query_dfs(
        self,
        sqls: Union[str, Iterable[str]],
        table_info: T_DataInfo = None
    ) -> Union[pd.DataFrame, List[pd.DataFrame]]:
        """执行sql查询语句

        获取DataFrame格式的二维表

        Args:
            sqls: 执行的sql，表名可以通过${table_name}占位
            table_info: sql中表名占位符对应的数据表元素信息。

        Notes:
            如果执行的sql中没有任何表名占位符，sql将直接执行。
            如果有占位符, 例如 ``${table1}``，那么要求 ``table_info`` 有
            key值为 ``table1`` , 对应键值为包含
            ``elementName, elementType, folderId/path`` 的字典，
            或者 :class:`DataTableMySQL` 类型，或者 :class:`ElementModel` 类型

        Returns:
            :class:`DataFrame` 格式的二维数据表

        """
        if isinstance(sqls, str):
            sql_list = await self.parser.parse([sqls], table_info)
            return await self.connector.query_dataframe(sql_list[0])
        else:
            sqls = await self.parser.parse(sqls, table_info)
            return await asyncio.gather(*[
                self.connector.query_dataframe(sql) for sql in sqls
            ])

    async def insert_df(
        self,
        dataframe: pd.DataFrame,
        element_name: str = None,
        table_name: str = None,
        table_info: T_DataInfo = None,
        chunksize: int = None,
    ):
        """将 :class:`DataFrame` 的插入数据表

        Args:
            dataframe: 入库数据
            element_name: 数据表元素名
            table_name: 数据表的 **实际表名**
            table_info: 数据表元素信息，使用table
            chunksize: 单次插库的数据行数

        """
        if table_name is not None:
            tbl_name = table_name
        elif element_name is not None:
            tbl_name = (await self.parser.parse(["${%s}" % element_name], table_info))[0]
        else:
            raise ValueError("Either 'element_name' or 'table_name' must be presented.")

        return await asyncio.gather(*[
            self.connector.insert_dataframe(tbl_name, df)
            for df in split_dataframe(dataframe, chunksize)
        ])


if OPTION.general.db_direct_access:
    ClientBase = DirectAccessClient
else:
    ClientBase = APIBasedClient


@cachedclass(Manager.create_cache(TTLCache, maxsize=5, ttl=3600))
class AsyncClickHouseClient(ClientBase):
    pass


@cachedclass(Manager.create_cache(TTLCache, maxsize=5, ttl=3600))
class ClickHouseClient(ClientBase, metaclass=SyncMeta):
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
            table_info: T_DataInfo = None,
            chunksize: int = None,
        ):
            ...
