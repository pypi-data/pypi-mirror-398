"""数据库连接类"""
import asyncio

from cachetools import TTLCache

from deepfos.lib.decorator import cached_property
from typing import Union, List, Iterable, TYPE_CHECKING

import pandas as pd

from deepfos.api.datatable import MySQLAPI
from deepfos.lib.utils import cachedclass
from deepfos.lib.decorator import singleton
from deepfos.cache import Manager
from deepfos.options import OPTION
from .dbkits import BaseSqlParser, SyncMeta, DataframeSQLConvertor, T_DataInfo, escape_mysql_string
from .connector import MySQLAPIConnector, MySQLDirectAccess


__all__ = [
    'MySQLClient',
    'AsyncMySQLClient',
]


@singleton
class SqlParser(BaseSqlParser):
    api_cls = MySQLAPI

    @cached_property
    def datatable_cls(self):
        from deepfos.element.datatable import AsyncDataTableMySQL
        return AsyncDataTableMySQL


class MySQLConvertor(DataframeSQLConvertor):
    escape_string = escape_mysql_string


# -----------------------------------------------------------------------------
# core
class _AbsAsyncMySQLClient:
    connector_cls = None
    convertor = MySQLConvertor(quote_char='`')

    def __init__(self, version: Union[float, str] = None):
        self.parser = SqlParser()
        self.connector = self.connector_cls(version)

    async def exec_sqls(
        self,
        sqls: Union[str, Iterable[str]],
        table_info: T_DataInfo = None
    ):
        """以事务执行多句sql

        Args:
            sqls: 要执行的sql语句，str或多句sql的list
            table_info: sql中表名占位符对应的数据表元素信息。

        """

        if isinstance(sqls, str):
            sqls = [sqls]

        parsed_sql = await self.parser.parse(sqls, table_info)
        resp = await self.connector.trxn_execute(parsed_sql)
        return resp

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
            dfs = await asyncio.gather(
                *(self.connector.query_dataframe(sql) for sql in sqls)
            )
            return list(dfs)

    async def insert_df(
        self,
        dataframe: pd.DataFrame,
        element_name: str = None,
        table_name: str = None,
        updatecol: Iterable[str] = None,
        table_info: T_DataInfo = None,
        chunksize: int = None,
    ):
        """将 :class:`DataFrame` 的插入数据表

        Args:
            dataframe: 入库数据
            element_name: 数据表元素名
            table_name: 数据表的 **实际表名**
            updatecol: 更新的列 (用于INSERT INTO ON DUPLICATE)
            table_info: 数据表元素信息，使用table
            chunksize: 单次插库的数据行数

        """
        if table_name is not None:
            tbl_name = table_name
        elif element_name is not None:
            tbl_name = (await self.parser.parse(["${%s}" % element_name], table_info))[0]
        else:
            raise ValueError("Either 'element_name' or 'table_name' must be presented.")

        sqls = list(self.convertor.iter_sql(
            dataframe, tbl_name, updatecol=updatecol, chunksize=chunksize
        ))
        return await self.connector.trxn_execute(sqls)


class _AbsMySQLClient(_AbsAsyncMySQLClient, metaclass=SyncMeta):
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


if OPTION.general.db_direct_access:
    CONN_CLS = MySQLDirectAccess
else:
    CONN_CLS = MySQLAPIConnector


@cachedclass(Manager.create_cache(TTLCache, maxsize=5, ttl=3600))
class AsyncMySQLClient(_AbsAsyncMySQLClient):
    connector_cls = CONN_CLS


@cachedclass(Manager.create_cache(TTLCache, maxsize=5, ttl=3600))
class MySQLClient(_AbsMySQLClient):
    connector_cls = CONN_CLS
