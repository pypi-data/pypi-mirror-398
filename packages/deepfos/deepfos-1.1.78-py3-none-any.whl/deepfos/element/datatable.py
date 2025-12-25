import re
import warnings
from contextvars import ContextVar
import pprint
from contextlib import contextmanager, asynccontextmanager
from typing import (
    Iterable, List, Dict, Union, Type,
    Tuple, TypeVar, Any, Sequence, Optional,
    TYPE_CHECKING,
)

import pandas as pd
import numpy as np
from loguru import logger
from pypika import Field, Query, Table, ClickHouseQuery, Order, OracleQuery, MSSQLQuery, PostgreSQLQuery
from pypika.terms import Term, EmptyCriterion
from pypika.utils import format_quotes, format_alias_sql
from requests.utils import CaseInsensitiveDict

from .base import ElementBase, SyncMeta
from deepfos.api.datatable import (
    MySQLAPI, ClickHouseAPI, SQLServerAPI,
    OracleAPI, KingBaseAPI, GaussAPI, DaMengAPI,
    PostgreSQLAPI, DeepEngineAPI, DeepModelAPI,
    DeepModelKingBaseAPI
)
from deepfos.api.models.datatable_mysql import (
    CustomSqlRespDTO, MiscModel, DatatableDataDeleteDTO
)
from deepfos.lib.utils import FrozenClass, split_dataframe
from deepfos.lib.asynchronous import future_property, evloop
from deepfos.lib.decorator import flagmethod, cached_property
from deepfos.lib.constant import UNSET
from deepfos.db.dbkits import null, Skip, DataframeSQLConvertor, escape_string, escape_mysql_string, escape_pg_string
from deepfos.db.oracle import OracleDFSQLConvertor  # noqa
from deepfos.db.clickhouse import ClickHouseConvertor
from deepfos.db.postgresql import PostgreSQLConvertor
from deepfos.db.sqlserver import SQLServerDFSQLConvertor
from deepfos.db.deepengine import DeepEngineDFSQLConvertor
from deepfos.options import OPTION

__all__ = [
    'Datatable',
    'AsyncDataTableMySQL',
    'DataTableMySQL',
    'AsyncDataTableClickHouse',
    'DataTableClickHouse',
    'AsyncDataTableOracle',
    'DataTableOracle',
    'AsyncDataTableSQLServer',
    'DataTableSQLServer',
    'AsyncDataTableKingBase',
    'DataTableKingBase',
    'AsyncDataTableGauss',
    'DataTableGauss',
    'AsyncDataTableDaMeng',
    'DataTableDaMeng',
    'AsyncDataTablePostgreSQL',
    'DataTablePostgreSQL',
    'AsyncDataTableDeepEngine',
    'DataTableDeepEngine',
    'AsyncDataTableDeepModel',
    'DataTableDeepModel',
    'AsyncDataTableDeepModelKingBase',
    'DataTableDeepModelKingBase',
    'null',
    'Skip',
    'Field',
    'get_table_class',
    'T_DatatableClass',
    'T_DatatableInstance',
    'T_AsyncDatatableClass',
    'T_AsyncDatatableInstance'
]

SQL_LOG_MAX_LEN = 1024
# -----------------------------------------------------------------------------
# typing
KT = TypeVar('KT', Field, str)
VT = TypeVar('VT', str, int)
T_DictLike = Union[Dict[KT, VT], Iterable[Tuple[KT, VT]]]


# -----------------------------------------------------------------------------
# Columns
class BaseColumn:
    null_val = UNSET
    dtype = UNSET

    def __init__(self, column: MiscModel):
        self.column = column
        self.col_name = column.name
        self.col_type = column.type
        self.nullable = column.whetherEmpty

    def fit(self, df: pd.DataFrame, column: str):
        """
        使 :class:`Dataframe` 对应的列符合列的限制条件。
        一般在需要把df的数据登录至DB时使用。包含两部分工作:

        1. 填充空值。前提是子类 :attr:`nullable` 为 ``False``，\
        并且子类定义了类属性 :attr:`null_val` 作为填充值。
        2. 其他转换工作。子类通过实现 :meth:`extra_fit` 定义。

        Args:
            df: 待转换的 :class:`Dataframe`
            column: 需要转化的列名
        """
        if not self.nullable and self.null_val is not UNSET:
            df[column] = df[column].fillna(self.null_val)
        self.extra_fit(df, column)

    def extra_fit(self, df: pd.DataFrame, column: str):
        # df[self.col_name] = df[self.col_name].astype(self.dtype, errors='ignore')
        pass

    def cast(self, df: pd.DataFrame, column: str):
        """
        对 :class:`Dataframe` 对应的列作类型转换。
        一般在获取 :class:`Dataframe` 时使用。
        """
        pass

    def __repr__(self):    # pragma: no cover
        return self.__class__.__name__


class ColumnFloat(BaseColumn):
    dtype = 'float'


class ColumnDateTime(BaseColumn):
    dtype = 'datetime64[ns]'

    def cast(self, df, column: str):
        df[column] = pd.to_datetime(df[column])

    @staticmethod
    def format_datetime(dt):
        if not isnull(dt):
            return "'" + dt.strftime("%Y-%m-%d %H:%M:%S") + "'"
        return pd.NaT

    def extra_fit(self, df: pd.DataFrame, column: str):
        df[column] = df[column].apply(self.format_datetime)


class ColumnOracleDateTime(ColumnDateTime):
    dtype = 'datetime64[ns]'

    def cast(self, df, column: str):
        df[column] = pd.to_datetime(df[column])

    @staticmethod
    def format_datetime(dt):
        if not isnull(dt):
            return f"TO_DATE('{dt.strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS')"
        return pd.NaT

    def extra_fit(self, df: pd.DataFrame, column: str):
        df[column] = df[column].apply(self.format_datetime)


class ColumnInt(BaseColumn):
    dtype = 'int'


class ColumnString(BaseColumn):
    null_val = 'null'
    dtype = 'object'

    @staticmethod
    def escape_string(string):
        if string is null:
            return null
        if string:
            return f"'{escape_string(string)}'"
        return "''"

    def extra_fit(self, df: pd.DataFrame, column: str):
        if self.nullable:
            df[column] = df[column].fillna(null)
        df[column] = df[column].apply(self.escape_string)


class MySQLColumnString(ColumnString):
    null_val = 'null'
    dtype = 'object'

    @staticmethod
    def escape_string(string):
        if string is null:
            return null
        if string:
            return f"'{escape_mysql_string(string)}'"
        return "''"


class PGColumnString(ColumnString):
    null_val = 'null'
    dtype = 'object'

    @staticmethod
    def escape_string(string):
        if string is null:
            return null
        if string:
            return f"'{escape_pg_string(string)}'"
        return "''"


class ColumnDecimal(BaseColumn):
    dtype = 'float'

    def extra_fit(self, df, column: str):
        digits = self.column.length.rsplit(',')[1]
        df[column] = np.where(
            df[column].isna(),
            df[column], df[column].fillna(0).round(int(digits)))


class ColumnFactory:
    col_map = {
        "datetime": ColumnDateTime,
        "oracle_datetime": ColumnOracleDateTime,
        "date": ColumnDateTime,
        "int": ColumnInt,
        "smallint": ColumnInt,
        "tinyint": ColumnInt,
        "bigint": ColumnInt,
        "integer": ColumnInt,
        "varchar": ColumnString,
        "pg_varchar": PGColumnString,
        "mysql_varchar": MySQLColumnString,
        "pg_text": PGColumnString,
        "mysql_text": MySQLColumnString,
        "text": ColumnString,
        "float": ColumnFloat,
        "double": ColumnFloat,
        "decimal": ColumnDecimal,
    }

    def __new__(cls, column: MiscModel):
        col_class = cls.col_map.get(cls.get_col_key(column.type), BaseColumn)
        return col_class(column)

    @staticmethod
    def get_col_key(col_type):
        return col_type.lower()


class MySQLColumnFactory(ColumnFactory):
    @staticmethod
    def get_col_key(col_type):
        if col_type.lower() == 'varchar':
            return "mysql_varchar"
        if col_type.lower() == 'text':
            return "mysql_text"
        return col_type.lower()


class ClickHouseColumnFactory(ColumnFactory):
    @staticmethod
    def get_col_key(col_type):
        if col_type.lower() == 'varchar':
            return "mysql_varchar"
        if col_type.lower() == 'text':
            return "mysql_text"
        if col_type == 'LowCardinality(String)':
            return "mysql_varchar"
        return col_type.lower()


class OracleColumnFactory(ColumnFactory):
    @staticmethod
    def get_col_key(col_type):
        if col_type.lower() == 'datetime':
            return "oracle_datetime"
        return col_type.lower()


class PGColumnFactory(ColumnFactory):
    @staticmethod
    def get_col_key(col_type):
        if col_type.lower() == 'varchar':
            return "pg_varchar"
        if col_type.lower() == 'text':
            return "pg_text"
        return col_type.lower()


class TableStructure:
    """
    表结构

    Args:
        meta_info: 表的元数据，包含各个列的列名及数据类型

    """
    ColumnFactory = ColumnFactory

    def __init__(self, meta_info: List[MiscModel]):
        self.columns = CaseInsensitiveDict({
            col.name: self.ColumnFactory(col)
            for col in meta_info
        })

    def fit(self, df: pd.DataFrame, columns: Iterable[str] = None):
        """
        对传入的DataFrame的指定数据列执行fit操作。
        直接影响DataFrame数据。

        Args:
            df: 数据源
            columns: 数据列

        See Also:
            :meth:`BaseColumn.fit`

        """
        if columns is None:
            columns = self.columns

        valid_cols = []
        for col in columns:
            if col in self.columns:
                valid_cols.append(col)
                self.columns[col].fit(df, col)
        return df[valid_cols]

    def fit_single(self, df: pd.DataFrame, column: str):    # pragma: no cover
        """
        对传入的DataFrame的某一指定列执行fit操作。
        直接影响DataFrame数据。

        Args:
            df: 数据源
            column: 数据列名

        See Also:
            :meth:`fit` , :meth:`BaseColumn.fit`

        """
        if column not in self.columns:
            raise KeyError(f"Given column: {column} doesn't exist.")
        self.columns[column].fit(df)

    def cast(self, df: pd.DataFrame):
        """
        对传入的DataFrame的所有列执行cast操作。
        直接影响DataFrame数据。

        Args:
            df: 数据源

        See Also:
            :meth:`BaseColumn.cast`

        """
        for col in df.columns:
            if col in self.columns:
                self.columns[col].cast(df, col)

    def __repr__(self):    # pragma: no cover
        return pprint.pformat(self.columns)


class MySQLTableStructure(TableStructure):
    ColumnFactory = MySQLColumnFactory


class OracleTableStructure(TableStructure):
    ColumnFactory = OracleColumnFactory


class PGTableStructure(TableStructure):
    ColumnFactory = PGColumnFactory


class ClickHouseTableStructure(TableStructure):
    ColumnFactory = ClickHouseColumnFactory


# -----------------------------------------------------------------------------
# utils
class _DataTableDFConvertor(DataframeSQLConvertor):
    def convert(
        self,
        dataframe: pd.DataFrame,
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ) -> str:
        """
        DataFrame对象转换为插库sql
        如果不传updatecol，用作INSERT INTO语法；
        如果传了updatecol，用作INSERT INTO ON DUPLICATE语法，
        无主键重复时作为插入，主键相同时更新指定列

        Args:
            dataframe: 待插入数据
            tablename: 数据库表名
            updatecol: 更新的列

        Returns:
            sql语句
        """
        if dataframe.empty:
            return ''

        data_df = dataframe.fillna(null).astype(str, errors='ignore')
        data_series = "(" + pd.Series(data_df.values.tolist()).str.join(',') + ")"
        columns = self.build_column_string(dataframe.columns)

        return self.build_sql(columns, data_series, tablename, updatecol)


class _OracleDFConvertor(_DataTableDFConvertor):
    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        return OracleDFSQLConvertor(self.quote_char).build_sql(columns, values_in_line, tablename, updatecol, **opts)

    def build_column_string(self, columns):
        return ','.join(columns.map(
            lambda x: f'"{x.upper()}"'
        ))


class _ClickHouseDFConvertor(_DataTableDFConvertor):
    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        return ClickHouseConvertor(self.quote_char).build_sql(columns, values_in_line, tablename, updatecol, **opts)


class _SQLServerDFConvertor(_DataTableDFConvertor):
    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        return SQLServerDFSQLConvertor(self.quote_char).build_sql(columns, values_in_line, tablename, updatecol, **opts)


class _DeepEngineDFConvertor(_DataTableDFConvertor):
    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        return DeepEngineDFSQLConvertor(self.quote_char).build_sql(columns, values_in_line, tablename, updatecol, **opts)


class _PostgreSQLDFConvertor(PostgreSQLConvertor):
    def convert(
        self,
        dataframe: pd.DataFrame,
        tablename: str,
        updatecol: Iterable[str] = None,
        conflict_target: Iterable[str] = None,
        **opts
    ) -> str:
        """
        DataFrame对象转换为插库sql
        如果不传updatecol，用作INSERT INTO语法；
        如果传了updatecol，用作INSERT INTO ON CONFLICT语法，
        无主键重复时作为插入，主键相同时更新指定列

        Args:
            dataframe: 待插入数据
            tablename: 数据库表名
            updatecol: 更新的列
            conflict_target: 使用INSERT INTO ON CONFLICT语法时的conflict基准列信息

        Returns:
            sql语句
        """
        if dataframe.empty:
            return ''

        data_df = dataframe.fillna(null).astype(str, errors='ignore')
        data_series = "(" + pd.Series(data_df.values.tolist()).str.join(',') + ")"
        columns = self.build_column_string(dataframe.columns)

        return self.build_sql(columns, data_series, tablename, updatecol, conflict_target=conflict_target, **opts)


def isnull(obj: Any) -> bool:
    return (obj is null) or pd.isna(obj)


def ensure_pikafield(table: Table, fields: Iterable[Union[str, int, Field, Term]]):
    for fld in fields:
        if isinstance(fld, str):
            yield table.__getattr__(fld)
        elif isinstance(fld, int):
            yield table.__getattr__(str(fld))
        else:
            yield fld


txn_support = flagmethod('_txn_support_')


class _TxnConfig:
    __slots__ = ('async_api', 'sql', 'in_txn', 'txn_support', 'flatten')

    def __init__(self):
        self.async_api = None
        self.sql = [[]]
        self.in_txn = [False]
        self.txn_support = False
        self.flatten = False


DOC_TEMPLATE = """{DB}数据表

提供单表的增删改查操作

Args:
    table_name: 数据表的真实表名，已知的情况下，可以避免内部重复查询表名。能提高性能。
"""

DOC_START_TX_TEMPLATE = """开启事务

上下文管理器，使用with语法开启上下文，上下文中的sql将作为事务执行。
退出with语句块后，事务将立即执行，执行过程中如果报错会直接抛出，
执行结果可通过 :attr:`transaction_result` 查询。

.. admonition:: 示例

    .. code-block:: python

        tbl = %s('table_example')
        t = tbl.table
        with tbl.start_transaction():
            tbl.insert({'key': 101, 'value': 'txn'})
            tbl.update({'value': 'new_txn'}, where=t.key == 101)
            tbl.delete(where=t.key >= 99)
        result = tbl.transaction_result

Args:
    flatten: 是否拉平嵌套事务，如果开启，嵌套的事务将会作为一个事务执行

Important:
    仅 ``insert/delete/update`` **系列** (包括 :meth:`insert_df`,
    :meth:`copy_rows` 等)的sql支持在事务中执行，
        支持事务运行的方法可以通过源码查看，带有 ``@txn_support``
        装饰器的方法即支持事务。

    如果在事务中执行select，查询结果也将立刻返回。

"""

# -----------------------------------------------------------------------------
# core


class AsyncDataTableMySQL(ElementBase):
    __doc__ = DOC_TEMPLATE.format(DB='MySQL')
    api_class = MySQLAPI
    api: MySQLAPI
    query = Query
    quote_char = '`'
    convertor = _DataTableDFConvertor(quote_char=quote_char)

    _txn_ = ContextVar('TXN')
    #: 事务执行结果
    transaction_result = None

    def __init__(
        self,
        element_name: str,
        folder_id: str = None,
        path: str = None,
        table_name: str = None,
        server_name: str = None,
    ):
        self.__tbl_name = table_name
        super().__init__(element_name, folder_id, path, server_name)

    def _safe_get_txn_conf(self) -> _TxnConfig:
        try:
            config = self._txn_.get()
        except LookupError:
            config = _TxnConfig()
            self._txn_.set(config)
        return config

    @property
    def _txn_support_(self):
        return self._safe_get_txn_conf().txn_support

    @_txn_support_.setter
    def _txn_support_(self, val):
        self._safe_get_txn_conf().txn_support = val

    @future_property
    async def meta(self):
        """数据表的元配置信息"""
        api = await self.wait_for('async_api')
        element_info = await self.wait_for('element_info')
        r = await api.dml.table_info_field([element_info])
        return r[0]

    @cached_property
    def table_name(self) -> str:
        """数据表真实表名"""
        if self.__tbl_name is None:
            self.__tbl_name = self.meta.datatableInfo.actualTableName
        return self.__tbl_name

    @cached_property
    def table(self) -> Table:
        """pipyka的Table对象

        主要用于创建查询条件

        .. admonition:: 示例

            .. code-block:: python

                tbl = DataTableMySQL("test")
                t = tbl.table
                where = (
                    ((t.f1 > 1) | (t.f2 == '23'))
                    &
                    (t.f3.isin([1, 2, 3]) | t.f4.like('f%'))
                )
                tbl.select(where=where)

            将执行sql：

            .. code-block:: sql

                SELECT
                    *
                FROM
                    test
                WHERE
                    (`f1`>1 OR `f2`='23')
                    AND
                    (`f3` IN (1,2,3) OR `f4` LIKE 'f%')

        See Also:
            关于table的更多使用方法，可以查看
            `pypika的github <https://github.com/kayak/pypika#tables-columns-schemas-and-databases>`_

        """
        return Table(self.table_name)

    @cached_property
    def _quoted_table_name(self):
        return self.table.get_sql(quote_char=self.quote_char)

    @cached_property
    def structure(self) -> MySQLTableStructure:
        """数据表的表结构

        主要包含了所有列的列名和类型信息，用于
        在查询和保存时对数据做类型转化的预处理。
        """
        return MySQLTableStructure(self.meta.datatableColumn)

    @cached_property
    def _field_map_templates(self) -> Tuple[Dict[str, None], Dict[str, Type[null]]]:
        base_tmpl = {}
        incr_cols = {}

        for col in self.meta.datatableColumn:
            if col.whetherIncrement:
                incr_cols[col.name] = null
            else:
                base_tmpl[col.name] = None

        return base_tmpl, incr_cols

    async def select(
        self,
        columns: Iterable[Union[str, Term]] = None,
        where: Union[str, Term, EmptyCriterion] = None,
        distinct: bool = False,
        groupby: Iterable[Union[str, int, Term]] = None,
        having: Iterable[Union[Term, EmptyCriterion]] = None,
        orderby: Iterable[Union[str, Field]] = None,
        order: Union[Order, str] = Order.asc,
        limit: int = None,
        offset: int = None,
    ) -> pd.DataFrame:
        """从数据表获取 ``DataFrame`` 格式的数据

        根据查询条件返回 ``DataFrame`` 类型的二维数据表，
        会根据列类型作自动数据转换。如 ``DATETIME`` 字段将会转换为日期类型。

        Important:
            使用方法与 :meth:`select_raw` 完全相同，使用示例请参考 :meth:`select_raw`
            的文档。

        Args:
            columns: 查询字段
            where: 查询条件（聚合条件也可以）
            distinct: 是否使用select distinct语法
            groupby: 用于groupby的列
            having: 用于having语句的条件
            orderby: 用于orderby的列
            order: orderby的顺序，ASC/DESC
            limit: limit限制返回数据量
            offset: offset偏移量

        Returns:
            查询的二维数据表

        See Also:
            如果希望获取原始数据，可以使用 :meth:`select_raw`

        """
        raw_data = await self.select_raw(
            columns,
            where=where,
            distinct=distinct,
            groupby=groupby,
            having=having,
            orderby=orderby,
            order=order,
            limit=limit,
            offset=offset
        )
        data = pd.DataFrame.from_records(raw_data)
        self.structure.cast(data)
        if data.empty:
            if columns:
                add_cols = self._get_valid_columns(columns)
            else:
                add_cols = self.structure.columns.keys()
            return pd.DataFrame(columns=add_cols)
        return data

    async def select_raw(
        self,
        columns: Iterable[Union[str, Term]] = None,
        where: Union[str, Term, EmptyCriterion] = None,
        distinct: bool = False,
        groupby: Iterable[Union[str, int, Term]] = None,
        having: Iterable[Union[Term, EmptyCriterion]] = None,
        orderby: Iterable[Union[str, Field]] = None,
        order: Union[Order, str] = Order.asc,
        limit: int = None,
        offset: int = None,
    ) -> List[dict]:
        """根据查询条件从数据表获取数据

        根据查询条件查询数据表接口并返回。
        数据类型将只含有 **JSON基本数据类型**

        Args:
            columns: 查询字段
            where: 查询条件（聚合条件也可以）
            distinct: 是否使用select distinct语法
            groupby: 用于groupby的列
            having: 用于having语句的条件
            orderby: 用于orderby的列
            order: orderby的顺序，ASC/DESC
            limit: limit限制返回数据量
            offset: offset偏移量


        .. admonition:: 示例

            .. code-block:: python

                import pypika.functions as pf
                tbl = DataTableMySQL("example")
                t = tbl.table

            #. 执行全表查询

                .. code-block:: python

                    tbl.select()

            #. 指定列查询，对数据列使用公式

                .. code-block:: python

                    columns = [
                        'col_a',
                        pf.Max('col_b'),
                        t.col_c,
                        t.col_d + 25,
                        pf.Avg(t.col_e)
                    ]
                    tbl.select(columns)

                将执行sql：

                .. code-block:: sql

                    SELECT
                        `col_a`,
                        MAX('col_b'),
                        `col_c`,
                        `col_d`+ 25,
                        AVG(`col_e`)
                    FROM
                        `example`

            #. 指定查询条件

                .. code-block:: python

                    where = (
                        ((t.col_a > 1) | (t.col_b == '23'))
                        &
                        (t.col_c.isin([1, 2, 3]) | t.col_d.like('f%'))
                    )
                    tbl.select(where=where)

                将执行sql：

                .. code-block:: sql

                    SELECT
                        *
                    FROM
                        `example`
                    WHERE
                        (`col_a`>1
                        OR `col_b`= '23')
                        AND (`col_c` IN (1, 2, 3)
                        OR `col_d` LIKE 'f%')

            #. 聚合条件等

                .. code-block:: python

                    tbl.select(
                        [pf.Max('col_a')],
                        groupby=[t.col_c],
                        limit=10,
                        offset=5,
                    )

                将执行sql：

                .. code-block:: sql

                    SELECT
                        MAX('col_a')
                    FROM
                        `example`
                    GROUP BY
                        `col_c`
                    LIMIT 10 OFFSET 5

        Warnings:
            虽然目前参数where可以接收str类型，但这种支持会在将来被移除。
            因为这会导致最终执行SQL：
                ``"SELECT {distinct} {fields} FROM {table_name} WHERE {where}"``
            即groupby，limit等参数都将失效，虽然可以写在where条件中，
            但这种方式会使你的代码可读性下降，因此并不被推荐。
            请务必按照示例中的写法使用本方法，否则您可能在代码中看到一些
            warning甚至在将来无法使用。

        See Also:
            如果希望返回 ``DataFrame`` 的数据，可以使用 :meth:`select`

        Returns:
            形如 [{column -> value}, ... , {column -> value}] 的数据。

            例如原始数据为

            +------+------+
            | col1 | col2 |
            +======+======+
            |   1  | 2    |
            +------+------+
            |   3  | 4    |
            +------+------+

            则返回 ``[{'col1': 1, 'col2': 2}, {'col1': 3, 'col2': 4}]`` 。

        """
        sql = self._build_select_sql(
            columns,
            where=where,
            distinct=distinct,
            groupby=groupby,
            having=having,
            orderby=orderby,
            order=order,
            limit=limit,
            offset=offset
        )
        r = await self._run_sql(sql)
        return r.selectResult

    def _build_select_sql(
        self,
        columns: Iterable[Union[str, Term]] = None,
        where: Union[str, Term, EmptyCriterion] = None,
        distinct: bool = False,
        groupby: Iterable[Union[str, int, Term]] = None,
        having: Iterable[Union[Term, EmptyCriterion]] = None,
        orderby: Iterable[Union[str, Field]] = None,
        order: Union[Order, str] = Order.asc,
        limit: int = None,
        offset: int = None,
    ) -> str:
        q = self.query.from_(self.table)
        if distinct:
            q = q.distinct()

        if columns is None:
            q = q.select('*')
        else:
            q = q.select(*ensure_pikafield(self.table, columns))

        if isinstance(where, str):
            warnings.warn(
                "使用字符串类型作为where条件入参将被弃用。推荐方式请参考此方法的文档。",
                DeprecationWarning)
            sql = f"{q.get_sql(quote_char=self.quote_char)} WHERE {where}"
        else:
            if where is not None:
                q = q.where(where)
            if groupby is not None:
                q = q.groupby(*ensure_pikafield(self.table, groupby))
            if having is not None:
                q = q.having(*having)
            if orderby is not None:
                if isinstance(order, str):
                    order = Order[order.lower()]
                q = q.orderby(*ensure_pikafield(self.table, orderby), order=order)
            if limit is not None:
                q = q.limit(limit)
            if offset is not None:
                q = q.offset(offset)
            sql = q.get_sql(quote_char=self.quote_char)
        return sql

    @staticmethod
    def _get_valid_columns(columns: Iterable[Union[str, Term]]):
        res = []
        for c in columns:
            if isinstance(c, str):
                res.append(c)
            elif isinstance(c, Term):
                if c.alias is not None:
                    res.append(c.alias)
                else:
                    res.append(c.get_sql(quote_char=''))
            else:
                res.append(str(c))
        return res

    @txn_support
    async def insert_df(
        self,
        dataframe: pd.DataFrame,
        updatecol: Iterable = None,
        chunksize: int = 5000,
        auto_fit: bool = True,
    ) -> Union[CustomSqlRespDTO, Dict, None]:
        """将 ``DataFrame`` 的数据插入当前数据表

        入库前会对DataFrame的数据作以下处理:

            #. （强制）所有空值变更为 null，确保能正常入库
            #. （非强制）对于 **不可为空** 的字符串类型数据列，会填充 ``'null'`` 字符串（未来可能会修改，不要依赖这个逻辑）
            #. （非强制）对于decimal类型，自动 ``round`` 至规定小数位

        上述 **（非强制）** 逻辑，可以通过指定 ``auto_fit=False`` 关闭。

        Args:
            dataframe: 待插入数据
            updatecol: 更新的列 (用于INSERT INTO ON DUPLICATE)
            chunksize: 单次插库的数据行数
            auto_fit: 是否自动进行数据调整

        Hint:
            如果单次入库数据过多，导致超出数据库的单条sql语句的上限，可以降低
            chuncksize，此方法将把一条较大的sql拆分成多条执行。

        Returns:
            执行的操作记录

        """
        if dataframe.empty:
            return

        if auto_fit:
            dataframe = dataframe.copy()
            dataframe = self.structure.fit(dataframe, dataframe.columns)
        else:
            dataframe = dataframe[dataframe.columns.intersection(self.structure.columns)]

        sqls = self.convertor.iter_sql(dataframe, self.table.get_table_name(), updatecol, chunksize)
        return await self._maybe_submit_in_txn(sqls)

    async def _maybe_submit_in_txn(self, sqls: Iterable[str]):
        if self._txn_.get().in_txn[-1]:
            for sql in sqls:
                await self.run_sql(sql)
        else:
            return await self._trxn_execute(self, list(sqls))

    def _parse_where(self, where: Union[None, Term, EmptyCriterion]) -> str:
        if isinstance(where, (Term, EmptyCriterion)):
            return where.get_sql(quote_char=self.quote_char)
        if isinstance(where, str):
            return where
        raise TypeError(f"Unsupported type: {type(where)} for where.")

    @txn_support
    async def delete(
        self,
        where: Union[str, Term, EmptyCriterion],
    ) -> CustomSqlRespDTO:
        """删除数据表的数据

        Args:
            where: 删除条件

        .. admonition:: 示例

            .. code-block:: python

                tbl = DataTableMySQL("example")
                t = tbl.table
                where = (
                    ((t.col_a > 1) | (t.col_b == '23'))
                    &
                    (t.col_c.isin([1, 2, 3]) | t.col_d.like('f%'))
                )
                tbl.delete(where)

            将执行sql：

            .. code-block:: sql

                DELETE
                FROM
                    `example`
                WHERE
                    (`col_a`>1
                    OR `col_b`= '23')
                    AND (`col_c` IN (1, 2, 3)
                    OR `col_d` LIKE 'f%')

        Warnings:
            where参数对 ``str`` 格式的支持会在将来移除，请按照示例中的调用方式使用。

        """
        sql = f"DELETE FROM {self._quoted_table_name} WHERE {self._parse_where(where)}"
        return await self.run_sql(sql)

    @txn_support
    async def update(
        self,
        assignment_list: T_DictLike,
        where: Union[None, Term, EmptyCriterion]
    ):
        """
        更新数据表的数据

        Args:
            assignment_list: 更新的字段与对应的更新值
            where: 更新行满足的条件

        .. admonition:: 示例

            .. code-block:: python

                tbl = DataTableMySQL("example")
                t = tbl.table
                tbl.update({'col1': 'val1', 'col2':  t.col2 + 1}, where=t.key == 101)
                tbl.update([('col1', 'val1'), ('col2', t.col2 + 1)], where=t.key == 101)

            两个 ``update`` 是一样的，将执行sql：

            .. code-block:: sql

                UPDATE
                    `example`
                SET
                    `col1`= 'val1',
                    `col2`=`col2`+ 1
                WHERE
                    `KEY`= 101

        Important:
            为了避免使用者忘记指定where条件而执行了全表更新，
            此方法中where为必须参数，如果确实需要执行全表更新，
            请显式传入 ``where = None`` 。

        """

        q = self.query.update(self.table)

        if isinstance(assignment_list, Dict):
            iter_items = assignment_list.items()
        else:
            iter_items = assignment_list

        for field, value in iter_items:
            if isinstance(field, str):
                field = self.table.__getattr__(field)
            q = q.set(field, value)

        if where is not None:
            q = q.where(where)
        return await self.run_sql(q.get_sql(quote_char=self.quote_char))

    @txn_support
    async def update_from_dataframe(
        self,
        source: pd.DataFrame,
        chucksize: Optional[int] = None
    ):
        """使用 :class:`DataFrame` 更新数据表

        Args:
            source: 更新数据源
            chucksize: 每批更新最大使用的DataFrame行数

        Important:
            :class:`DataFrame` ``source`` 必须包含 ``where`` 列，
            其列类型可以为字符串，也可以是pypika的条件语句。
            该列指明每行数据对应的更新条件。为了防止条件缺失而进行了全表更新，
            该列所有数据不允许为空。

            如果有部分行不想进行所有字段的更新，可在对应单元格内填充Skip值。

        .. admonition:: 示例

            .. code-block:: python

                from deepfos.element.datatable import Skip

                df = pd.DataFrame(data=[
                    [1, 'Foo', 'Foo@x.com'],
                    [2, 'Bar', 'bar@x.com'],
                    [3, 'Jack', Skip]
                ], columns=['id', 'name', 'email'])

                df['where'] = pd.Series(f"id='{i + 1}'" for i in range(3))

                tbl = DataTableMySQL("example")
                tbl.update_from_dataframe(df)

            将执行以下SQL:

            .. code-block:: SQL

                UPDATE `example`
                SET `id`=1,`name`='Foo',`email`='Foo@x.com'
                WHERE
                    id = 1;
                UPDATE `example`
                SET `id`=2,`name`='Bar',`email`='bar@x.com'
                WHERE
                    id = 2;
                UPDATE `example`
                    SET `id`=3,`name`='Jack'  -- email字段值为Skip，因此不更新
                WHERE
                    id = 3;

        """
        key_where = 'where'
        if key_where not in source.columns:
            raise ValueError(f"Column <{key_where}> is missing in source dataframe.")

        valid_columns = source.columns.intersection(self.structure.columns.keys())
        table = self.table

        def yield_sql(df):
            where_col = df[key_where]
            for idx, upd_data in enumerate(df[valid_columns].to_dict(orient='records')):
                q = self.query.update(table)

                any_updates = False
                for field, value in upd_data.items():
                    if value is Skip:
                        continue

                    any_updates = True
                    if isinstance(field, str):
                        field = table.__getattr__(field)
                    q = q.set(field, value)

                if not any_updates:
                    continue

                if isnull(where := where_col.iloc[idx]):
                    raise ValueError(
                        f"The where condition in [row: {idx}] is null, "
                        f"which is strictly prohibited.")

                if isinstance(where, str):
                    yield f"{q.get_sql(quote_char=self.quote_char)} WHERE {where}"
                elif isinstance(where, (Term, EmptyCriterion)):
                    q = q.where(where)
                    yield q.get_sql(quote_char=self.quote_char)

        ret = []
        for dataframe in split_dataframe(source, chucksize):
            r = await self._maybe_submit_in_txn(yield_sql(dataframe))
            ret.append(r)
        return ret

    async def count(
        self,
        where: Union[str, Term, EmptyCriterion],
    ) -> int:
        """
        查询数据记录数

        查询满足给定查询条件的数据记录数量。

        Args:
            where: 查询条件

        """
        sql = f"SELECT COUNT(1) FROM {self._quoted_table_name} WHERE {self._parse_where(where)};"
        resp = await self._run_sql(sql)
        return list(resp.selectResult[0].values())[0]

    def _format_field(
        self,
        field_map: Dict[str, Union[str, int, FrozenClass, Term]]
    ) -> Tuple[str, str]:
        base, incr = self._field_map_templates
        fmap = {**base, **field_map, **incr}

        field_strings = []

        for field, value in fmap.items():
            if value is None:
                field_strings.append(f"{self.quote_char}{field}{self.quote_char}")
            elif isinstance(value, Term):
                value = value.get_sql(quote_char=self.quote_char)
                field_strings.append(f"{value} as {self.quote_char}{field}{self.quote_char}")
            else:
                field_strings.append(f"{value!r} as {self.quote_char}{field}{self.quote_char}")

        return ','.join(f"{self.quote_char}{k}{self.quote_char}" for k in fmap), ','.join(field_strings)

    @txn_support
    async def copy_rows(
        self,
        where: Union[str, Term, EmptyCriterion],
        field_map: Dict[str, Union[str, int, FrozenClass, Term]] = None,
        distinct: bool = False,
    ) -> CustomSqlRespDTO:
        """拷贝当前表的数据行

        按照指定where条件，copy数据到本表，
        可以通过field_map更新或者指定部分字段的值。（常用于版本拷贝）

        Args:
            where: 需要复制的数据行的筛选条件
            field_map: key：需要复制的字段，value：需要复制的值
            distinct: select是否增加distinct

        .. admonition:: 示例

            .. code-block:: python

                import pypika.functions as pf

                tbl = DataTableMySQL("test")
                t = tbl.table
                tbl.copy_rows(
                    where=(t.f1 >= 1) & (t.f2 == 2) | (t.f3 > 1),
                    field_map={
                        "f1": t.f1 + 1,
                        "f2": 3,
                        "f4": t.f5,
                        "f6": pf.Max(t.f6)
                    }
                )

            将执行sql：

            .. code-block:: sql

                INSERT INTO
                    test
                SELECT
                    `f1` + 1 as f1,
                    3 as f2,
                    `f3`,
                    `f5` as f4,
                    `f5`,
                    Max(`f6`) as `f6`
                FROM
                    test
                WHERE
                    `f1`>=1 AND `f2`==2 OR `f3`>1

        """
        field_map = field_map or {}
        fields, field_str = self._format_field(field_map)
        sql = "INSERT INTO {table} ({fields}) SELECT {distinct} {field_str} FROM {table} WHERE {where}".format(
            table=self._quoted_table_name,
            fields=fields,
            field_str=field_str,
            where=self._parse_where(where),
            distinct='DISTINCT' if distinct else ''
        )
        return await self.run_sql(sql)

    async def _run_sql(self, sql: str) -> Optional[CustomSqlRespDTO]:
        txn_conf = self._safe_get_txn_conf()

        if txn_conf.in_txn[-1] and self._txn_support_:
            txn_conf.sql[-1].append(sql)
            if txn_conf.async_api is None:
                txn_conf.async_api = self.async_api
            return

        def trim_sql():    # pragma: no cover
            if len(sql) > SQL_LOG_MAX_LEN:
                return sql[:SQL_LOG_MAX_LEN-4] + "..."
            else:
                return sql

        logger.opt(lazy=True).debug("Execute SQL: [{sql}].", sql=trim_sql)
        return await self.async_api.dml.run_sql(sql)

    @txn_support
    async def run_sql(self, sql: str) -> Optional[CustomSqlRespDTO]:
        """执行sql

        直接执行sql，sql中出现的表名必须为实际表名。

        Hint:
            实际表名可以通过 :attr:`table_name` 获取。

        Args:
            sql: 执行的sql语句

        Returns:
            执行结果

        """
        return await self._run_sql(sql)

    @txn_support
    async def insert(
        self,
        value_map: Dict[str, Any] = None,
        value_list: Iterable[Sequence[Any]] = None,
        columns: Iterable[Union[str, Term]] = None,
    ):
        """
        插入数据，数据量极少时推荐使用

        Args:
            value_map: 以键值对（列名 -> 插入值）提供的入库数据
            value_list: 入库数据（不包含列数据）
            columns: 入库数据对应的列，不提供则默认使用全部列

        .. admonition:: 示例

            .. code-block:: python

                tbl = DataTableMySQL("test")
                tbl.insert(value_map={'a': 1, 'b': 2})
                tbl.insert(value_list=[[1, 2]], columns=['a', 'b'])

            两个 ``insert`` 是一样的，将执行sql：

            .. code-block:: sql

                INSERT INTO `test`
                    (`a`,`b`)
                VALUES
                    (1,2)

        """

        q = self.query.into(self.table)

        if value_map is not None:
            q = q.columns(*value_map.keys()).insert(*value_map.values())
        elif value_list is None:
            raise ValueError('None of argumnet [value_map, value_list] is set.')
        else:
            if columns:
                column_num = len(list(columns))
                q = q.columns(*columns)
            else:
                column_num = len(self.structure.columns.keys())

            for value in value_list:
                if len(value) != column_num:
                    raise ValueError(
                        'Value number mismatch with column number.'
                        f'values: {value}, number: {len(value)}, '
                        f'columns number: {column_num}.')
                q = q.insert(*value)

        return await self.run_sql(q.get_sql(quote_char=self.quote_char))

    @classmethod
    @asynccontextmanager
    async def start_transaction(cls, flatten: bool = False):
        """
        开启事务

        上下文管理器，使用with语法开启上下文，上下文中的sql将作为事务执行。
        退出with语句块后，事务将立即执行，执行过程中如果报错会直接抛出，
        执行结果可通过 :attr:`transaction_result` 查询。

        .. admonition:: 示例

            .. code-block:: python

                tbl = DataTableMySQL('table_example')
                t = tbl.table
                async with tbl.start_transaction():
                    await tbl.insert({'key': 101, 'value': 'txn'})
                    await tbl.update({'value': 'new_txn'}, where=t.key == 101)
                    await tbl.delete(where=t.key >= 99)
                result = tbl.transaction_result

        Args:
            flatten: 是否拉平嵌套事务，如果开启，嵌套的事务将会作为一个事务执行

        Important:
            仅 ``insert/delete/update`` **系列** (包括 :meth:`insert_df`,
            :meth:`copy_rows` 等)的sql支持在事务中执行，
                支持事务运行的方法可以通过源码查看，带有 ``@txn_support``
                装饰器的方法即支持事务。

            如果在事务中执行select，查询结果也将立刻返回。

        """
        try:
            cls._txn_.get()
        except LookupError:
            cls._txn_.set(_TxnConfig())
        bak_flatten = cls._txn_.get().flatten
        cls._txn_.get().in_txn.append(True)

        if flatten and not cls._txn_.get().flatten:
            force_submit = True
        else:
            force_submit = False

        cls._txn_.get().flatten = bak_flatten or flatten

        if not cls._txn_.get().flatten:
            cls._txn_.get().sql.append([])

        try:
            yield
            if force_submit or not cls._txn_.get().flatten:
                await cls.__submit_txn()
        finally:
            cls._txn_.get().in_txn.pop()
            cls._txn_.get().flatten = bak_flatten

    @classmethod
    async def __submit_txn(cls):
        if sql := cls._txn_.get().sql.pop():
            resp = await cls._trxn_execute(cls._txn_.get(), sql)
            cls.transaction_result = resp

    @staticmethod
    async def _trxn_execute(self, sqls: List[str]):
        return await self.async_api.dml.execute_batch_sql(sqls)


class DataTableSyncMixin:
    synchronize = (
        'count',
        'select',
        'select_raw',
        'insert',
        'insert_df',
        'delete',
        'update',
        'update_from_dataframe',
        'copy_rows',
        'run_sql',
    )
    if TYPE_CHECKING:  # pragma: no cover
        def count(
            self,
            where: Union[str, Term, EmptyCriterion],
        ) -> int:
            ...

        def select(
            self,
            columns: Iterable[Union[str, Term]] = None,
            where: Union[str, Term, EmptyCriterion] = None,
            distinct: bool = False,
            groupby: Iterable[Union[str, int, Term]] = None,
            having: Iterable[Union[Term, EmptyCriterion]] = None,
            orderby: Iterable[Union[str, Field]] = None,
            order: Union[Order, str] = Order.asc,
            limit: int = None,
            offset: int = None,
        ) -> pd.DataFrame:
            ...

        def select_raw(
            self,
            columns: Iterable[Union[str, Term]] = None,
            where: Union[str, Term, EmptyCriterion] = None,
            distinct: bool = False,
            groupby: Iterable[Union[str, int, Term]] = None,
            having: Iterable[Union[Term, EmptyCriterion]] = None,
            orderby: Iterable[Union[str, Field]] = None,
            order: Union[Order, str] = Order.asc,
            limit: int = None,
            offset: int = None,
        ) -> List[dict]:
            ...

        def insert(
            self,
            value_map: Dict[str, Any] = None,
            value_list: Iterable[Sequence[Any]] = None,
            columns: Iterable[Union[str, Term]] = None,
        ):
            ...

        def insert_df(
            self,
            dataframe: pd.DataFrame,
            updatecol: Iterable = None,
            chunksize: int = 5000,
            auto_fit: bool = True,
        ) -> Union[CustomSqlRespDTO, Dict, None]:
            ...

        def delete(
            self,
            where: Union[str, Term, EmptyCriterion],
        ) -> CustomSqlRespDTO:
            ...

        def update(
            self,
            assignment_list: T_DictLike,
            where: Union[None, Term, EmptyCriterion]
        ):
            ...

        def copy_rows(
            self,
            where: Union[str, Term, EmptyCriterion],
            field_map: Dict[str, Union[str, int, FrozenClass, Term]] = None,
            distinct: bool = False,
        ) -> CustomSqlRespDTO:
            ...

        def run_sql(self, sql: str) -> Optional[CustomSqlRespDTO]:
            ...

        def update_from_dataframe(
                self,
                source: pd.DataFrame,
                chucksize: Optional[int] = None
        ):
            ...


class DataTableSyncMeta(SyncMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        @contextmanager
        def start_transaction(cls, flatten: bool = False):
            try:
                cls._txn_.get()
            except LookupError:
                cls._txn_.set(_TxnConfig())

            bak_flatten = cls._txn_.get().flatten
            cls._txn_.get().in_txn.append(True)

            if flatten and not cls._txn_.get().flatten:
                force_submit = True
            else:
                force_submit = False

            cls._txn_.get().flatten = bak_flatten or flatten

            if not cls._txn_.get().flatten:
                cls._txn_.get().sql.append([])

            try:
                yield
                if force_submit or not cls._txn_.get().flatten:
                    cls.__submit_txn()
            finally:
                cls._txn_.get().in_txn.pop()
                cls._txn_.get().flatten = bak_flatten

        start_transaction.__doc__ = DOC_START_TX_TEMPLATE % name

        def __submit_txn(cls):
            if sql := cls._txn_.get().sql.pop():
                resp = evloop.run(cls._trxn_execute(cls._txn_.get(), sql))
                cls.transaction_result = resp

        cls.start_transaction = classmethod(start_transaction)
        cls.__submit_txn = classmethod(__submit_txn)

        return cls


class DataTableMySQL(
    AsyncDataTableMySQL,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDirectAccessDataTableMySQL(AsyncDataTableMySQL):
    async def select(
        self,
        columns: Iterable[Union[str, Term]] = None,
        where: Union[str, Term, EmptyCriterion] = None,
        distinct: bool = False,
        groupby: Iterable[Union[str, int, Term]] = None,
        having: Iterable[Union[Term, EmptyCriterion]] = None,
        orderby: Iterable[Union[str, Field]] = None,
        order: Union[Order, str] = Order.asc,
        limit: int = None,
        offset: int = None,
    ) -> pd.DataFrame:
        from deepfos.db import damysql
        sql = self._build_select_sql(
            columns,
            where=where,
            distinct=distinct,
            groupby=groupby,
            having=having,
            orderby=orderby,
            order=order,
            limit=limit,
            offset=offset
        )
        return await damysql.query_dataframe(sql)

    async def select_raw(
        self,
        columns: Iterable[Union[str, Term]] = None,
        where: Union[str, Term, EmptyCriterion] = None,
        distinct: bool = False,
        groupby: Iterable[Union[str, int, Term]] = None,
        having: Iterable[Union[Term, EmptyCriterion]] = None,
        orderby: Iterable[Union[str, Field]] = None,
        order: Union[Order, str] = Order.asc,
        limit: int = None,
        offset: int = None,
    ) -> List[dict]:
        raw_data = await self.select(
            columns,
            where=where,
            distinct=distinct,
            groupby=groupby,
            having=having,
            orderby=orderby,
            order=order,
            limit=limit,
            offset=offset
        )
        return raw_data.to_dict(orient='records')

    @txn_support
    async def run_sql(self, sql: str):
        from deepfos.db import damysql
        ctx = self._txn_
        if ctx.get().in_txn[-1] and self._txn_support_:
            ctx.get().sql[-1].append(sql)
            return
        if len(sql) > SQL_LOG_MAX_LEN:    # pragma: no cover
            sql_log = sql[:SQL_LOG_MAX_LEN - 4] + "..."
        else:
            sql_log = sql
        logger.debug(f"Execute SQL: [{sql_log}].")    # pragma: no cover
        return await damysql.execute(sql)

    @staticmethod
    async def _trxn_execute(self, sqls: List[str]):
        from deepfos.db import damysql
        return await damysql.trxn_execute(sqls)

    async def count(
            self,
            where: Union[str, Term, EmptyCriterion],
    ) -> int:
        from deepfos.db import damysql
        sql = f"SELECT COUNT(1) FROM {self._quoted_table_name} WHERE {self._parse_where(where)};"
        res = await damysql.select(sql)
        return res[0][0]


class DirectAccessDataTableMySQL(
    AsyncDirectAccessDataTableMySQL,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDataTableClickHouse(AsyncDataTableMySQL):
    __doc__ = DOC_TEMPLATE.format(DB='ClickHouse')
    api_class = ClickHouseAPI
    api: ClickHouseAPI
    query = ClickHouseQuery
    convertor = _ClickHouseDFConvertor(quote_char=AsyncDataTableMySQL.quote_char)

    @cached_property
    def structure(self) -> ClickHouseTableStructure:
        """数据表的表结构

        主要包含了所有列的列名和类型信息，用于
        在查询和保存时对数据做类型转化的预处理。
        """
        columns = self.meta.datatableColumn
        columns.append(MiscModel(name='createtime', type='int', whetherEmpty=False))
        columns.append(MiscModel(name='createdate', type='datetime', whetherEmpty=False))
        return ClickHouseTableStructure(columns)

    async def delete(self, where: Dict[str, Union[VT, List[VT]]]):
        """
        删除数据表的数据

        Args:
            where: 删除条件。列名-> 要删除的值

        .. admonition:: 示例

            .. code-block:: python

                tbl = DataTableClickHouse("example")
                tbl.delete({
                    "col_a": 1,
                    "col_b": ["x", "y"]
                })

            将执行sql：

            .. code-block:: sql

                ALTER TABLE example
                DELETE
                WHERE
                    `col_a` IN (1)
                    AND `col_b` IN ('x', 'y')

        Warnings:
            由于ClickHouse数据库的特性， ``delete`` 可能不会立即生效，
            所以不要依赖此方法保证数据一致性。并且不推荐频繁使用。

        """
        del_cols = {}
        for k, v in where.items():
            if isinstance(v, str):
                del_cols[k] = [v]
            else:
                del_cols[k] = v

        return await self.async_api.dml.delete_data(
            DatatableDataDeleteDTO.construct_from(
                self.element_info,
                columnList=del_cols
            ))

    def _format_field(
        self,
        field_map: Dict[str, Union[str, int, FrozenClass, Term]]
    ) -> Tuple[str, str]:
        base, incr = self._field_map_templates
        fmap = {**base, **field_map, **incr}

        field_strings = []

        for field, value in fmap.items():
            if value is None:
                field_strings.append(f"`{field}`")
            elif isinstance(value, Term):
                value = value.get_sql(quote_char=self.quote_char)
                field_strings.append(value)
            else:
                field_strings.append(repr(value))

        return ','.join(f"`{k}`" for k in fmap), ','.join(field_strings)

    @classmethod
    @asynccontextmanager
    async def start_transaction(cls, flatten: bool = False):
        """不可用

        ClickHouse不支持事务
        """
        try:
            yield
        finally:
            raise NotImplementedError('ClickHouse does not support transaction.')


class DataTableClickHouse(
    AsyncDataTableClickHouse,
    DataTableSyncMixin,
    metaclass=SyncMeta
):
    @classmethod
    def start_transaction(cls, flatten: bool = False):
        """不可用

        ClickHouse不支持事务
        """
        raise NotImplementedError('ClickHouse does not support transaction.')


class AsyncDirectAccessDataTableClickHouse(AsyncDirectAccessDataTableMySQL):
    __doc__ = DOC_TEMPLATE.format(DB='ClickHouse')
    api_class = ClickHouseAPI
    api: ClickHouseAPI
    query = ClickHouseQuery

    @classmethod
    @asynccontextmanager
    async def start_transaction(cls, flatten: bool = False):
        """不可用

        ClickHouse不支持事务
        """
        try:
            yield
        finally:
            raise NotImplementedError('ClickHouse does not support transaction.')

    async def run_sql(self, sql: str):   # pragma: no cover
        from deepfos.db import daclickhouse
        if len(sql) > SQL_LOG_MAX_LEN:
            sql_log = sql[:SQL_LOG_MAX_LEN - 4] + "..."
        else:
            sql_log = sql
        logger.debug(f"Execute SQL: [{sql_log}].")
        return await daclickhouse.execute(sql)

    async def insert_df(
            self,
            dataframe: pd.DataFrame,
            updatecol: Iterable = None,
            chunksize: int = 5000,
            auto_fit: bool = True,
    ) -> List:
        from deepfos.db import daclickhouse
        if updatecol is not None:
            warnings.warn("CK数据表不支持INSERT INTO ON DUPLICATE语法，将忽略该入参地组织sql", Warning)
        r = []
        for df in split_dataframe(dataframe, chunksize):
            res = await daclickhouse.insert_dataframe(self.table_name, df)
            r.append(res)
        return r

    async def select(
            self,
            columns: Iterable[Union[str, Term]] = None,
            where: Union[str, Term, EmptyCriterion] = None,
            distinct: bool = False,
            groupby: Iterable[Union[str, int, Term]] = None,
            having: Iterable[Union[Term, EmptyCriterion]] = None,
            orderby: Iterable[Union[str, Field]] = None,
            order: Union[Order, str] = Order.asc,
            limit: int = None,
            offset: int = None,
    ) -> pd.DataFrame:
        from deepfos.db import daclickhouse
        sql = self._build_select_sql(
            columns,
            where=where,
            distinct=distinct,
            groupby=groupby,
            having=having,
            orderby=orderby,
            order=order,
            limit=limit,
            offset=offset
        )
        return await daclickhouse.query_dataframe(sql)

    async def count(
            self,
            where: Union[str, Term, EmptyCriterion],
    ) -> int:
        from deepfos.db import daclickhouse
        sql = f"SELECT COUNT(1) FROM {self._quoted_table_name} WHERE {self._parse_where(where)};"
        res = await daclickhouse.select(sql)
        return res[0][0]

    async def delete(self, where: Dict[str, Union[VT, List[VT]]]):
        """
        删除数据表的数据

        Args:
            where: 删除条件。列名-> 要删除的值

        .. admonition:: 示例

            .. code-block:: python

                tbl = DataTableClickHouse("example")
                tbl.delete({
                    "col_a": 1,
                    "col_b": ["x", "y"]
                })

            将执行sql：

            .. code-block:: sql

                ALTER TABLE example
                DELETE
                WHERE
                    `col_a` IN (1)
                    AND `col_b` IN ('x', 'y')

        Warnings:
            由于ClickHouse数据库的特性， ``delete`` 可能不会立即生效，
            所以不要依赖此方法保证数据一致性。并且不推荐频繁使用。

        """
        t = self.table

        q = self.query.from_(t).delete()

        for k, v in where.items():
            if isinstance(v, List):
                q = q.where(getattr(t, k).isin(v))
            else:
                q = q.where(getattr(t, k) == v)

        sql = q.get_sql(quote_char=self.quote_char)
        return await self.run_sql(sql)


class DirectAccessDataTableClickHouse(
    AsyncDirectAccessDataTableClickHouse,
    DataTableSyncMixin,
    metaclass=SyncMeta
):
    @classmethod
    def start_transaction(cls, flatten: bool = False):
        """不可用

        ClickHouse不支持事务
        """
        raise NotImplementedError('ClickHouse does not support transaction.')


if OPTION.general.db_direct_access:
    AsyncDataTableMySQL = AsyncDirectAccessDataTableMySQL
    AsyncDataTableClickHouse = AsyncDirectAccessDataTableClickHouse
    DataTableMySQL = DirectAccessDataTableMySQL
    DataTableClickHouse = DirectAccessDataTableClickHouse

Datatable = DataTableMySQL


class _OracleField(Field):
    def get_sql(self, **kwargs: Any) -> str:
        with_alias = kwargs.pop("with_alias", False)
        with_namespace = kwargs.pop("with_namespace", False)
        quote_char = kwargs.pop("quote_char", '"')

        field_sql = format_quotes(self.name, quote_char)
        field_sql = field_sql.upper()
        # Need to add namespace if the table has an alias
        if self.table and (with_namespace or self.table.alias):
            table_name = self.table.get_table_name()
            field_sql = "{namespace}.{name}".format(
                namespace=format_quotes(table_name, quote_char),
                name=field_sql,
            )

        field_alias = getattr(self, "alias", None)
        if with_alias:
            return format_alias_sql(field_sql, field_alias, quote_char=quote_char, **kwargs)
        return field_sql


class OracleTable(Table):
    def field(self, name: str) -> Field:
        return _OracleField(name, table=self, alias=name)


class AsyncDataTableOracle(AsyncDataTableMySQL):
    __doc__ = DOC_TEMPLATE.format(DB='Oracle')
    api: OracleAPI
    api_class = OracleAPI
    quote_char = '"'
    convertor = _OracleDFConvertor(quote_char='"')
    query = OracleQuery

    @cached_property
    def table(self) -> Table:
        return OracleTable(self.table_name.upper())

    @cached_property
    def structure(self) -> OracleTableStructure:
        return OracleTableStructure(self.meta.datatableColumn)

    @cached_property
    def _field_map_templates(self) -> Tuple[Dict[str, None], Dict[str, Type[null]]]:
        base_tmpl = {}
        incr_cols = {}

        for col in self.meta.datatableColumn:
            if col.whetherIncrement:
                continue
            base_tmpl[col.name.upper()] = None

        return base_tmpl, incr_cols

    @txn_support
    async def copy_rows(
            self,
            where: Union[str, Term, EmptyCriterion],
            field_map: Dict[str, Union[str, int, FrozenClass, Term]] = None,
            distinct: bool = False,
    ):
        new_field_map = None
        if field_map is not None:
            new_field_map = {k.upper(): v for k, v in field_map.items()}
        return await super().copy_rows(where, new_field_map, distinct)

    @txn_support
    async def insert(
            self,
            value_map: Dict[str, Any] = None,
            value_list: Iterable[Sequence[Any]] = None,
            columns: Iterable[Union[str, Term]] = None,
    ):
        insert_line = f"INTO {self._quoted_table_name} ({{cols}}) VALUES ({{vals}})"

        def quote_string(s):
            return f'"{s.upper()}"'

        if value_map is not None:
            insert = insert_line.format(
                cols=','.join(map(quote_string, value_map.keys())),
                vals=','.join(map(repr, value_map.values()))
            )
        elif value_list is None:
            raise ValueError('None of argumnet [value_map, value_list] is set.')
        else:
            columns = columns or list(self.structure.columns.keys())
            column_num = len(list(columns))
            cols = ','.join(map(quote_string, columns))

            insert_list = []
            for value in value_list:
                if len(value) != column_num:
                    raise ValueError(
                        'Value number mismatch with column number.'
                        f'values: {value}, number: {len(value)}, '
                        f'columns number: {column_num}.')
                insert_list.append(insert_line.format(
                    cols=cols,
                    vals=','.join(map(repr, value))
                ))
            insert = '\n'.join(insert_list)
        return await self.run_sql(f"INSERT ALL {insert} SELECT 1 FROM DUAL")


class DataTableOracle(
    AsyncDataTableOracle,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDataTableSQLServer(AsyncDataTableMySQL):
    __doc__ = DOC_TEMPLATE.format(DB='SQLServer')
    api: SQLServerAPI
    api_class = SQLServerAPI
    quote_char = ''
    convertor = _SQLServerDFConvertor(quote_char=quote_char)
    query = MSSQLQuery

    @cached_property
    def structure(self) -> MySQLTableStructure:
        return MySQLTableStructure(self.meta.datatableColumn)

    async def select_raw(
            self,
            columns: Iterable[Union[str, Term]] = None,
            where: Union[str, Term, EmptyCriterion] = None,
            distinct: bool = False,
            groupby: Iterable[Union[str, int, Term]] = None,
            having: Iterable[Union[Term, EmptyCriterion]] = None,
            orderby: Iterable[Union[str, Field]] = None,
            order: Union[Order, str] = Order.asc,
            limit: int = None,
            offset: int = None,
    ):
        if limit is not None or offset is not None:
            if not orderby:
                raise ValueError("orderby must not be empty when "
                                 "limit or offset is provided.")
        return await super().select_raw(
            columns,
            where=where,
            distinct=distinct,
            groupby=groupby,
            having=having,
            orderby=orderby,
            order=order,
            limit=limit,
            offset=offset
        )


class DataTableSQLServer(
    AsyncDataTableSQLServer,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDataTablePostgreSQL(AsyncDataTableMySQL):
    __doc__ = DOC_TEMPLATE.format(DB='PostgreSQL')
    api: PostgreSQLAPI
    api_class = PostgreSQLAPI
    quote_char = '"'
    convertor = _PostgreSQLDFConvertor(quote_char=quote_char)
    query = PostgreSQLQuery

    @cached_property
    def structure(self) -> PGTableStructure:
        return PGTableStructure(self.meta.datatableColumn)

    @txn_support
    async def insert_df(
        self,
        dataframe: pd.DataFrame,
        updatecol: Iterable = None,
        chunksize: int = 5000,
        auto_fit: bool = True,
        conflict_target: Iterable[str] = None,
    ) -> Union[CustomSqlRespDTO, Dict, None]:
        """将 ``DataFrame`` 的数据插入当前数据表

        入库前会对DataFrame的数据作以下处理:

            #. （强制）所有空值变更为 null，确保能正常入库
            #. （非强制）对于 **不可为空** 的字符串类型数据列，会填充 ``'null'`` 字符串（未来可能会修改，不要依赖这个逻辑）
            #. （非强制）对于decimal类型，自动 ``round`` 至规定小数位

        上述 **（非强制）** 逻辑，可以通过指定 ``auto_fit=False`` 关闭。

        Args:
            dataframe: 待插入数据
            updatecol: 更新的列 (用于INSERT INTO ON CONFLICT)
            chunksize: 单次插库的数据行数
            auto_fit: 是否自动进行数据调整
            conflict_target: 使用INSERT INTO ON CONFLICT语法时的conflict基准列信息，如不提供，则试图使用主键列

        Hint:
            如果单次入库数据过多，导致超出数据库的单条sql语句的上限，可以降低
            chuncksize，此方法将把一条较大的sql拆分成多条执行。

        Returns:
            执行的操作记录

        """
        if dataframe.empty:
            return

        if auto_fit:
            dataframe = dataframe.copy()
            dataframe = self.structure.fit(dataframe, dataframe.columns)
        else:
            dataframe = dataframe[dataframe.columns.intersection(self.structure.columns)]

        if conflict_target is None:
            conflict_target = [col.name for col in self.meta.datatableColumn if col.whetherPrimary] or None

        sqls = self.convertor.iter_sql(dataframe, self.table_name, updatecol, chunksize, conflict_target=conflict_target)
        return await self._maybe_submit_in_txn(sqls)

    @cached_property
    def _field_map_templates(self) -> Tuple[Dict[str, None], Dict[str, Type[null]]]:
        base_tmpl = {}
        incr_cols = {}

        for col in self.meta.datatableColumn:
            if col.whetherIncrement:
                continue
            base_tmpl[col.name] = None

        return base_tmpl, incr_cols


class DataTablePostgreSQL(
    AsyncDataTablePostgreSQL,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDataTableKingBase(AsyncDataTablePostgreSQL):
    __doc__ = DOC_TEMPLATE.format(DB='KingBase')
    api: KingBaseAPI
    api_class = KingBaseAPI


class DataTableKingBase(
    AsyncDataTableKingBase,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDataTableGauss(AsyncDataTablePostgreSQL):
    __doc__ = DOC_TEMPLATE.format(DB='Gauss')
    api: GaussAPI
    api_class = GaussAPI


class DataTableGauss(
    AsyncDataTableGauss,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDataTableDaMeng(AsyncDataTableOracle):
    __doc__ = DOC_TEMPLATE.format(DB='DaMeng')
    api: DaMengAPI
    api_class = DaMengAPI


class DataTableDaMeng(
    AsyncDataTableDaMeng,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDataTableDeepEngine(AsyncDataTableClickHouse):
    __doc__ = DOC_TEMPLATE.format(DB='DeepEngine')
    api: DeepEngineAPI
    api_class = DeepEngineAPI
    convertor = _DeepEngineDFConvertor(quote_char=AsyncDataTableClickHouse.quote_char)

    @classmethod
    @asynccontextmanager
    async def start_transaction(cls, flatten: bool = False):
        """不可用

        DeepEngine不支持事务
        """
        try:
            yield
        finally:
            raise NotImplementedError('DeepEngine does not support transaction.')


class DataTableDeepEngine(
    AsyncDataTableDeepEngine,
    DataTableSyncMixin,
    metaclass=SyncMeta
):
    @classmethod
    def start_transaction(cls, flatten: bool = False):
        """不可用

        DeepEngine不支持事务
        """
        raise NotImplementedError('DeepEngine does not support transaction.')


class AsyncDataTableDeepModel(AsyncDataTablePostgreSQL):
    __doc__ = DOC_TEMPLATE.format(DB='DeepModel')
    api: DeepModelAPI
    api_class = DeepModelAPI


class DataTableDeepModel(
    AsyncDataTableDeepModel,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


class AsyncDataTableDeepModelKingBase(AsyncDataTableKingBase):
    __doc__ = DOC_TEMPLATE.format(DB='DeepModelKingBase')
    api: DeepModelKingBaseAPI
    api_class = DeepModelKingBaseAPI


class DataTableDeepModelKingBase(
    AsyncDataTableDeepModelKingBase,
    DataTableSyncMixin,
    metaclass=DataTableSyncMeta
):
    pass


_RE_PARSE_SERVER = re.compile(r"data[-]?table-(.*?)-server[\d]-[\d]")


TO_MODULE_TYPE = CaseInsensitiveDict(
    {
        'mysql': MySQLAPI.module_type,
        'clickhouse': ClickHouseAPI.module_type,
        'sqlserver': SQLServerAPI.module_type,
        'oracle': OracleAPI.module_type,
        'kingbase': KingBaseAPI.module_type,
        'gauss': GaussAPI.module_type,
        'dameng': DaMengAPI.module_type,
        'postgresql': PostgreSQLAPI.module_type,
        'deepengine': DeepEngineAPI.module_type,
        'deepmodel': DeepModelAPI.module_type,
        'deepmodelkingbase': DeepModelKingBaseAPI.module_type,
    }
)

TABLE = CaseInsensitiveDict(
    {
        MySQLAPI.module_type: (DataTableMySQL, AsyncDataTableMySQL),
        ClickHouseAPI.module_type: (DataTableClickHouse, AsyncDataTableClickHouse),
        SQLServerAPI.module_type: (DataTableSQLServer, AsyncDataTableSQLServer),
        OracleAPI.module_type: (DataTableOracle, AsyncDataTableOracle),
        KingBaseAPI.module_type: (DataTableKingBase, AsyncDataTableKingBase),
        GaussAPI.module_type: (DataTableGauss, AsyncDataTableGauss),
        DaMengAPI.module_type: (DataTableDaMeng, AsyncDataTableDaMeng),
        PostgreSQLAPI.module_type: (DataTablePostgreSQL, AsyncDataTablePostgreSQL),
        DeepEngineAPI.module_type: (DataTableDeepEngine, AsyncDataTableDeepEngine),
        DeepModelAPI.module_type: (DataTableDeepModel, AsyncDataTableDeepModel),
        DeepModelKingBaseAPI.module_type: (DataTableDeepModelKingBase, AsyncDataTableDeepModelKingBase),
    }
)

T_DatatableClass = Union[
    Type[DataTableMySQL],
    Type[DataTableClickHouse],
    Type[DataTableOracle],
    Type[DataTableSQLServer],
    Type[DataTableKingBase],
    Type[DataTableGauss],
    Type[DataTableDaMeng],
    Type[DataTablePostgreSQL],
    Type[DataTableDeepEngine],
    Type[DataTableDeepModel],
    Type[DataTableDeepModelKingBase],
]

T_AsyncDatatableClass = Union[
    Type[AsyncDataTableMySQL],
    Type[AsyncDataTableClickHouse],
    Type[AsyncDataTableOracle],
    Type[AsyncDataTableSQLServer],
    Type[AsyncDataTableKingBase],
    Type[AsyncDataTableGauss],
    Type[AsyncDataTableDaMeng],
    Type[AsyncDataTablePostgreSQL],
    Type[AsyncDataTableDeepEngine],
    Type[AsyncDataTableDeepModel],
    Type[AsyncDataTableDeepModelKingBase],
]

T_DatatableInstance = Union[
    DataTableMySQL,
    DataTableClickHouse,
    DataTableOracle,
    DataTableSQLServer,
    DataTableKingBase,
    DataTableGauss,
    DataTableDaMeng,
    DataTablePostgreSQL,
    DataTableDeepEngine,
    DataTableDeepModel,
    DataTableDeepModelKingBase,
]

T_AsyncDatatableInstance = Union[
    AsyncDataTableMySQL,
    AsyncDataTableClickHouse,
    AsyncDataTableOracle,
    AsyncDataTableSQLServer,
    AsyncDataTableKingBase,
    AsyncDataTableGauss,
    AsyncDataTableDaMeng,
    AsyncDataTablePostgreSQL,
    AsyncDataTableDeepEngine,
    AsyncDataTableDeepModel,
    AsyncDataTableDeepModelKingBase,
]


def get_table_class(
    element_type: str,
    sync: bool = True
) -> Union[
    T_DatatableClass,
    T_AsyncDatatableClass
]:
    """
    根据元素类型获取对应的数据表元素类

    Args:
        element_type: module type或server name
        sync: 同步或异步元素类，默认同步

    """
    if sync:
        index = 0
    else:
        index = 1

    if element_type is None:
        raise ValueError("`element_type` should be a string value.")

    module_type = element_type

    if match := _RE_PARSE_SERVER.match(element_type):
        server_name = match.group(1)
        module_type = TO_MODULE_TYPE.get(server_name)

        if module_type is None:
            raise ValueError(f"{element_type} is not a known datatable server.")

    table = TABLE.get(module_type)

    if table is None:
        raise TypeError(f"Unknown datatable type: {element_type}")

    return table[index]
