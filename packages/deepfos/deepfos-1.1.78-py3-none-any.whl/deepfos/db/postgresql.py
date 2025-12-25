"""PostgreSQL客户端"""
from functools import cached_property
from typing import Union, List, Iterable, TYPE_CHECKING

import pandas as pd

from deepfos.api.datatable import PostgreSQLAPI
from deepfos.cache import Manager, SpaceSeperatedTTLCache
from deepfos.lib.utils import cachedclass
from deepfos.lib.decorator import singleton
from .dbkits import BaseSqlParser, SyncMeta, T_DataInfo, DataframeSQLConvertor, escape_pg_string
from .connector import PostgreSQLAPIConnector
from .mysql import _AbsAsyncMySQLClient  # noqa


__all__ = [
    'PostgreSQLClient',
    'AsyncPostgreSQLClient',
    '_AsyncPostgreSQLClient',
    'PostgreSQLConvertor',
]


@singleton
class SqlParser(BaseSqlParser):
    api_cls = PostgreSQLAPI

    @cached_property
    def datatable_cls(self):
        from deepfos.element.datatable import AsyncDataTablePostgreSQL
        return AsyncDataTablePostgreSQL


class PostgreSQLConvertor(DataframeSQLConvertor):
    escape_string = escape_pg_string

    def iter_sql(
        self,
        dataframe: pd.DataFrame,
        tablename: str,
        updatecol: Iterable = None,
        chunksize: int = None,
        conflict_target: Iterable[str] = None,
        **opts
    ) -> Iterable[str]:
        """ :class:`DataFrame` 对象转换为sql生成器

        如果传了updatecol，将使用 ``INSERT INTO ON CONFLICT`` 语法

        Args:
            dataframe: 待插入数据
            tablename: 数据库表名
            updatecol: 更新的列
            chunksize: 单条sql对应的最大dataframe行数
            conflict_target: 使用INSERT INTO ON CONFLICT语法时的conflict基准列信息

        Returns:
            sql语句生成器

        See Also:
            :func:`df_to_sql`

        """
        # 获取sql
        return super().iter_sql(dataframe, tablename, updatecol, chunksize, conflict_target=conflict_target, **opts)

    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        conflict_target: Iterable[str] = None,
        **opts
    ):
        values = ','.join(values_in_line)
        if updatecol is None:
            return f'INSERT INTO {self.quote_char}{tablename}{self.quote_char} ({columns}) VALUES {values}'

        update_str = ','.join([
            f"{self.quote_char}{x}{self.quote_char}="
            f"EXCLUDED.{self.quote_char}{x}{self.quote_char}"
            for x in updatecol
        ])
        if not update_str:
            return f'INSERT INTO {self.quote_char}{tablename}{self.quote_char} ({columns}) VALUES {values}'

        if conflict_target is None:
            raise ValueError('如需使用ON CONFLICT DO UPDATE语法，'
                             '需提供有唯一约束的列作为conflict_target列信息')

        conflict_target_clause = ",".join([
            f"{self.quote_char}{x}{self.quote_char}"
            for x in conflict_target
        ])

        if conflict_target_clause:
            conflict_target_clause = f"({conflict_target_clause})"

        return f'INSERT INTO {self.quote_char}{tablename}{self.quote_char} ({columns}) ' \
               f'VALUES {values} ' \
               f'ON CONFLICT {conflict_target_clause} ' \
               f'DO UPDATE SET {update_str}'


# -----------------------------------------------------------------------------
# core
class _AsyncPostgreSQLClient(_AbsAsyncMySQLClient):
    convertor = PostgreSQLConvertor(quote_char='"')

    def __init__(self, version: Union[float, str] = None):  # noqa
        self.parser = SqlParser()
        self.connector = PostgreSQLAPIConnector(version)

    async def insert_df(
        self,
        dataframe: pd.DataFrame,
        element_name: str = None,
        table_name: str = None,
        updatecol: Iterable[str] = None,
        table_info: T_DataInfo = None,
        chunksize: int = None,
        conflict_target: Iterable[str] = None,
    ):
        """将 :class:`DataFrame` 的插入数据表

        Args:
            dataframe: 入库数据
            element_name: 数据表元素名
            table_name: 数据表的 **实际表名**
            updatecol: 更新的列 (用于INSERT INTO ON CONFLICT)
            table_info: 数据表元素信息，使用table
            chunksize: 单次插库的数据行数
            conflict_target: 使用INSERT INTO ON CONFLICT语法时的约束列信息

        """
        if table_name is not None:
            tbl_name = table_name
        elif element_name is not None:
            tbl_name = (await self.parser.parse(["${%s}" % element_name], table_info))[0]
        else:
            raise ValueError("Either 'element_name' or 'table_name' must be presented.")

        sqls = list(self.convertor.iter_sql(
            dataframe, tbl_name, updatecol=updatecol, chunksize=chunksize, conflict_target=conflict_target
        ))
        return await self.connector.trxn_execute(sqls)


class _PostgreSQLClient(_AsyncPostgreSQLClient, metaclass=SyncMeta):
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
class AsyncPostgreSQLClient(_AsyncPostgreSQLClient):
    pass


@cachedclass(Manager.create_cache(SpaceSeperatedTTLCache, maxsize=5, ttl=3600))
class PostgreSQLClient(_PostgreSQLClient):
    pass
