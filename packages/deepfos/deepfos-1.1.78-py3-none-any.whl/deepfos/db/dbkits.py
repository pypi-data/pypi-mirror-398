import re
from typing import Dict, Union, List, Iterable, Tuple
from typing_extensions import Protocol

from deepfos.cache import Manager
from deepfos.lib.decorator import cached_property

from cachetools import TTLCache
from pandas.core.dtypes.common import is_datetime64_dtype, is_numeric_dtype
import numpy as np
import pandas as pd

from deepfos.options import OPTION
from deepfos.api.models.app import ModuleServerNameVO as ElementModel
from deepfos.api.models.datatable_mysql import BaseElementInfo
from deepfos.lib.asynchronous import cache_async
from deepfos.lib.decorator import singleton
from deepfos.lib.utils import FrozenClass
from deepfos.api.space import SpaceAPI


class DataTable(Protocol):
    table_name: str


T_DataInfo = Dict[str, Union[Dict, DataTable, BaseElementInfo]]


@singleton
class APIFinder:
    async def modules(self):
        mdl = await SpaceAPI(sync=False).module.get_usable_module()
        return mdl or []

    async def find_api(self, api_cls, version=None):
        if version is not None:
            return await api_cls(version=version, sync=False)

        modules = await self.modules()
        target_module = api_cls.module_type

        for mdl in modules:
            if mdl.moduleType == target_module and mdl.status == 1:
                api = api_cls(sync=False)
                # noinspection PyUnresolvedReferences
                await api.set_url(mdl.serverName)
                api.__class__.server_cache[mdl.moduleId] = mdl.serverName
                return api

        raise RuntimeError(  # pragma: no cover
            f"Cannot find a valid {api_cls.__name__} "
            f"in space: {OPTION.api.header['space']}.")


class BaseSqlParser:
    _RE_TABLE_PLACEHOLDER = re.compile(r"\${(.*?)}")
    api_cls = None

    def __init__(self):
        self.table_cache = Manager.create_cache(TTLCache, maxsize=100, ttl=3600)

    async def build_api(self):
        return await APIFinder().find_api(self.api_cls, version=1.0)

    @cached_property
    def datatable_cls(self):  # pragma: no cover
        raise NotImplementedError

    async def parse(
        self,
        sql_list: Iterable[str],
        table_info: T_DataInfo
    ) -> List[str]:
        tbl_placeholders = set()
        api = await self.build_api()

        for sql in sql_list:
            tbl_placeholders.update(self._RE_TABLE_PLACEHOLDER.findall(sql))

        table_info = table_info or {}
        ph_to_actualname = {}  # 占位符中的“表名” -> 实际表名（最终替换占位符的依据）
        #: 待查询表名的数据表的元素信息
        query_info: List[Tuple[str, Union[BaseElementInfo, ElementModel]]] = []
        #: 占位符中的“表名” -> 元素名，用于处理同表不同占位符的特情况
        ph_to_elename = {}

        for table in tbl_placeholders:
            if table not in table_info:
                element = await self.datatable_cls(table)._get_element_info()   # noqa
                query_info.append((table, element))
                ph_to_elename[table] = element.elementName
            else:
                info = table_info[table]

                if isinstance(info, BaseElementInfo):
                    query_info.append((table, info))
                    ph_to_elename[table] = info.elementName
                elif isinstance(info, self.datatable_cls):
                    ph_to_actualname[table] = info.table_name
                else:
                    ele = BaseElementInfo(**info)
                    query_info.append((table, ele))
                    ph_to_elename[table] = ele.elementName

        query_table, known = self._resolve_query(query_info)
        ph_to_actualname.update(known)

        if query_table:
            tables = await self.query_table_names(api, query_table)
            if not tables or tables.pop('errorMessageList', None):
                raise ValueError("One or more table is not found.")

            self._update_cache(query_table, tables)

            ph_to_actualname.update({
                placeholder: tables[elename]
                for placeholder, elename in ph_to_elename.items()
                if elename in tables
            })

        return [
            self._RE_TABLE_PLACEHOLDER.sub(
                lambda m: ph_to_actualname[m.group(1)],
                sql
            ) for sql in sql_list
        ]

    @staticmethod
    async def query_table_names(api, query_table):
        return await api.dml.batch_tablename(query_table)

    def _resolve_query(
        self,
        query_info: List[Tuple[str, Union[BaseElementInfo, ElementModel]]]
    ) -> Tuple[List[Union[BaseElementInfo, ElementModel]], Dict[str, str]]:
        need_query = []
        known_tables = {}
        table_cache = self.table_cache

        for placeholder, tbl in query_info:
            key = (tbl.elementName, tbl.folderId)
            if key in table_cache:
                known_tables[placeholder] = table_cache[key]
            else:
                need_query.append(tbl)

        return need_query, known_tables

    def _update_cache(
        self,
        query_table: List[Union[BaseElementInfo, ElementModel]],
        table_names: Dict[str, str]
    ):
        for tbl in query_table:
            key = (tbl.elementName, tbl.folderId)
            if tbl.elementName in table_names:
                self.table_cache[key] = table_names[tbl.elementName]


class SyncMeta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        base = bases[0]
        methods = namespace.pop('synchronize', [])
        from deepfos.element.base import synchronize

        for attr in methods:
            namespace[attr] = synchronize(mcs._get_from_bases(base, attr))

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        return cls

    @staticmethod
    def _get_from_bases(base, attr):
        while base is not object:
            if attr in base.__dict__:
                return base.__dict__[attr]
            base = base.__base__
        raise AttributeError(attr)


_escape_table = [chr(x) for x in range(128)]
_escape_table[ord("'")] = u"''"

_escape_table_mysql = list(_escape_table)
_escape_table_mysql[ord('\\')] = u'\\\\'

_escape_table_pg = list(_escape_table)
_escape_table_pg[0] = ''


def escape_string(value):
    return value.translate(_escape_table)


def escape_mysql_string(value):
    # for mysql & ck & deepengine & sqlserver
    return value.translate(_escape_table_mysql)


def escape_pg_string(value):
    # for pg & kingbase & gauss
    return value.translate(_escape_table_pg)


# noinspection PyPep8Naming
class null(metaclass=FrozenClass):
    """mysql数据库中的null"""

    @classmethod
    def translate(cls, *args):  # noqa
        # 模仿string的translate
        return cls


class Skip(metaclass=FrozenClass):
    """在更新dataframe中跳过更新的字段"""


class DataframeSQLConvertor:
    escape_string = escape_string

    def __init__(self, quote_char=None):
        self.quote_char = quote_char

    def iter_sql(
        self,
        dataframe: pd.DataFrame,
        tablename: str,
        updatecol: Iterable = None,
        chunksize: int = None,
        **opts
    ) -> Iterable[str]:
        """ :class:`DataFrame` 对象转换为sql生成器

        如果传了updatecol，将使用 ``INSERT INTO ON DUPLICATE`` 语法，
        无主键重复时作为插入，主键相同时更新指定列。

        Args:
            dataframe: 待插入数据
            tablename: 数据库表名
            updatecol: 更新的列
            chunksize: 单条sql对应的最大dataframe行数

        Returns:
            sql语句生成器

        Attention:
            当单个DataFrame生成的sql太长导致无法入库，可以指定 ``chuncksize`` ，
            使DataFrame生成多条sql。

        """
        # 获取sql
        if (nrows := len(dataframe)) == 0:
            return

        if chunksize is None or chunksize > nrows:
            yield self.convert(dataframe, tablename, updatecol, **opts)
        elif chunksize <= 0:
            raise ValueError("chunksize must be greater than 0.")
        else:
            for i in range(0, nrows, chunksize):
                yield self.convert(dataframe.iloc[i: i + chunksize], tablename, updatecol, **opts)

    @classmethod
    def _quote_escape(cls, value):
        if pd.isna(value):
            return value
        if not isinstance(value, str):
            return str(value)
        return f"'{cls.escape_string(value)}'"
    
    @staticmethod
    def format_datetime(maybe_datetime: pd.Series) -> pd.Series:
        return "'" + maybe_datetime.dt.strftime("%Y-%m-%d %H:%M:%S") + "'"

    @classmethod
    def format_series(cls, series: pd.Series) -> pd.Series:
        """格式化Series以适合sql语句
        
        1. 日期型重置格式到秒级别
        2. 字符串型列转义、加引号

        Args:
            series (pd.Series): 需要格式化的Series

        Returns:
            pd.Series: 格式化后的新的Series，不影响原Series
        """
        # 对日期型重置格式到秒级别
        if is_datetime64_dtype(series.dtype):
            return cls.format_datetime(series)
        # 对字符串型列转义，加引号
        elif not is_numeric_dtype(series.dtype):
            return series.apply(cls._quote_escape)
        return series.copy()

    def convert(
        self,
        dataframe: pd.DataFrame,
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ) -> str:
        """ :class:`DataFrame` 对象转换为插库sql

        如果传了updatecol，将使用 ``INSERT INTO ON DUPLICATE`` 语法，
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
        # 格式化Series以适合sql语句
        data_df = dataframe.apply(self.format_series)
        # 空值填充
        data_df = data_df.fillna(null)
        # 全部转化为字符串类型
        data_df = data_df.astype(str, errors='ignore')
        values = "(" + pd.Series(data_df.values.tolist()).str.join(',') + ")"
        columns = self.build_column_string(dataframe.columns)
        return self.build_sql(columns, values, tablename, updatecol, **opts)

    def build_column_string(self, columns: pd.Index) -> str:
        if self.quote_char:
            columns = ','.join(columns.map(
                lambda x: f'{self.quote_char}{x}{self.quote_char}'
            ))
        else:
            columns = ','.join(columns)
        return columns

    def build_sql(
        self,
        columns: str,
        values_in_line: Iterable[str],
        tablename: str,
        updatecol: Iterable[str] = None,
        **opts
    ):
        values = ','.join(values_in_line)
        if updatecol is None:
            return f'INSERT INTO {self.quote_char}{tablename}{self.quote_char} ({columns}) VALUES {values}'

        update_str = ','.join([f"{self.quote_char}{x}{self.quote_char}="
                               f"VALUES({self.quote_char}{x}{self.quote_char})" for x in updatecol])
        if not update_str:
            return f'INSERT INTO {self.quote_char}{tablename}{self.quote_char} ({columns}) VALUES {values}'

        return f'INSERT INTO {self.quote_char}{tablename}{self.quote_char} ({columns}) ' \
               f'VALUES {values} ' \
               f'ON DUPLICATE KEY UPDATE {update_str}'
