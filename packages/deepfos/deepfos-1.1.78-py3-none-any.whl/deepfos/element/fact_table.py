from contextlib import asynccontextmanager
from datetime import datetime
from typing import Union, Iterable, Dict, Any, Sequence, List, TYPE_CHECKING, Optional

import pandas as pd
from pypika import ClickHouseQuery, Order
from pypika.queries import QueryBuilder, Table
from pypika.terms import Term, EmptyCriterion, Field, CustomFunction, ValueWrapper

from deepfos.api.datatable import ClickHouseAPI
from deepfos.api.models.datatable_mysql import CustomSqlRespDTO
from deepfos.element.datatable import AsyncDataTableClickHouse, T_DictLike, AsyncDirectAccessDataTableClickHouse  # noqa
from deepfos.lib.constant import DECIMAL_COL, STRING_COL
from deepfos.element.base import SyncMeta
from deepfos.lib.utils import FrozenClass
from deepfos.lib.decorator import cached_property

__all__ = ['AsyncFactTable', 'FactTable']


class AsyncFactTable(AsyncDataTableClickHouse):
    """事实表"""
    api_class = ClickHouseAPI
    api: ClickHouseAPI
    query = ClickHouseQuery

    @cached_property
    def dim_cols(self):
        return sorted([col.name for col in self.meta.datatableColumn if col.whetherPrimary])

    async def insert_null(self, where: Union[Term, EmptyCriterion] = None):
        """
        删除事实表的数据

        Args:
            where: 删除条件。列名-> 要删除的值


        Hint:
            实际通过insert除createdate、createtime外，皆为NULL的数据实现

        """

        main_query = self._build_query_with_valid_data(sub_query_col=self.dim_cols, where=where)

        main_table = Table("main_table")

        createtime = _timestamp()
        createdate = _format_dt()
        insert_null = self.query.into(self.table) \
            .columns(*self.dim_cols, DECIMAL_COL, STRING_COL, 'createtime', 'createdate') \
            .from_(main_query.as_("main_table")) \
            .select(*[main_table.field(dim) for dim in self.dim_cols], None, None,
                    ValueWrapper(createtime), ValueWrapper(createdate))

        sql = insert_null.get_sql(quote_char='`')

        return await self.run_sql(sql)

    delete = insert_null

    def _build_select_sql(
            self,
            columns: Iterable[Union[str, Term]] = None,
            where: Union[Term, EmptyCriterion] = None,
            distinct: bool = False,
            groupby: Iterable[Union[str, int, Term]] = None,
            having: Iterable[Union[Term, EmptyCriterion]] = None,
            orderby: Iterable[Union[str, Field]] = None,
            order: Union[Order, str] = Order.asc,
            limit: int = None,
            offset: int = None,
    ) -> str:
        col = []
        if columns is None:
            col = [*self.dim_cols]
        else:
            for c in columns:
                col.append(self._gen_col(c))
        col = sorted(list(set(col).union(self.dim_cols)))

        if DECIMAL_COL in col:
            col.remove(DECIMAL_COL)
        if STRING_COL in col:
            col.remove(STRING_COL)
        main_query = self._build_query_with_valid_data(col, columns, where, distinct, groupby, having, orderby, order,
                                                       limit, offset)
        sql = main_query.get_sql(quote_char='`')
        return sql

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

        """
        if value_map is not None:
            for v in value_map:
                if not isinstance(value_map[v], List):
                    value_map[v] = [value_map[v]]
            df = pd.DataFrame(value_map)
        elif value_list is None:
            raise ValueError('None of argumnet [value_map, value_list] is set.')
        else:
            if columns:
                df = pd.DataFrame(value_list, columns=list(columns))
            else:
                df = pd.DataFrame(value_list, columns=self.structure.columns.keys())

        return await self.insert_df(df)

    async def insert_df(
            self,
            dataframe: pd.DataFrame,
            updatecol: Iterable = None,
            chunksize: int = 5000,
            auto_fit: bool = True,
    ) -> Union[CustomSqlRespDTO, Dict, List, None]:
        """将 ``DataFrame`` 的数据插入当前事实表

        入库前会对DataFrame的数据作以下处理:

            #. （强制）所有空值变更为 null，确保能正常入库
            #. （强制）以当前时间信息覆盖createdate和createtime列
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
        dataframe = dataframe.copy()
        dataframe['createtime'] = _timestamp()
        dataframe['createdate'] = pd.to_datetime(_format_dt())

        return await super().insert_df(dataframe, updatecol, chunksize, auto_fit)

    async def update(
            self,
            assignment_list: T_DictLike,
            where: Union[None, Term, EmptyCriterion]
    ):
        """
        更新事实表的数据

        Args:
            assignment_list: 更新的字段与对应的更新值
            where: 更新行满足的条件

        Important:
            实现上使用了insert createtime和createdate 为当前时间，且数据为原最新数据更新了update内容的数据的方式

        """
        if not isinstance(assignment_list, Dict):
            assignment_list = dict(assignment_list)

        main_query = self._build_query_with_valid_data(sub_query_col=self.dim_cols, where=where)

        update_col = {e: e for e in [*self.dim_cols, DECIMAL_COL, STRING_COL]}

        main_table = Table('main_table')

        for k, value in assignment_list.items():
            # for constant str, use ValueWrapper to differ with field
            if isinstance(value, str) and value not in [*self.dim_cols, DECIMAL_COL, STRING_COL]:
                value = ValueWrapper(value)
            if isinstance(value, Term):
                value = value.replace_table(self.table, main_table)
            update_col[self._gen_col(k)] = value

        insert = self.query.into(self.table) \
            .columns(*update_col.keys(), 'createtime', 'createdate') \
            .from_(main_query.as_("main_table")) \
            .select(*update_col.values(),
                    ValueWrapper(_timestamp()), ValueWrapper(_format_dt()))

        sql = insert.get_sql(quote_char='`')

        return await self.run_sql(sql)

    @classmethod
    @asynccontextmanager
    async def start_transaction(cls, flatten: bool = False):
        """不可用

        FactTable不支持事务
        """
        try:
            yield
        finally:
            raise NotImplementedError('事实表不支持事务.')

    async def count(
            self,
            where: Union[str, Term, EmptyCriterion],
    ) -> int:
        raise NotImplementedError('事实表未实现方法：count.')

    async def copy_rows(
            self,
            where: Union[str, Term, EmptyCriterion],
            field_map: Dict[str, Union[str, int, FrozenClass, Term]] = None,
            distinct: bool = False,
    ) -> CustomSqlRespDTO:
        raise NotImplementedError('事实表未实现方法：copy_rows.')

    async def update_from_dataframe(
            self,
            source: pd.DataFrame,
            chucksize: Optional[int] = None
    ):
        raise NotImplementedError('事实表未实现方法：update_from_dataframe.')

    _arg_max = CustomFunction('argMax', ['arg', 'val'])
    _ck_if = CustomFunction('if', ['condition', 'if', 'else'])
    _if_null = CustomFunction('ifNull', ['condition', 'val'])
    _to_string = CustomFunction('toString', ['val'])

    def get_latest_val(self, table, colname):
        return self._ck_if(self._arg_max(self._if_null(self._to_string(table.field(colname)), 'isnull'),
                                         table.createtime) == 'isnull',
                           None,
                           self._arg_max(table.field(colname), table.createtime))

    @staticmethod
    def _gen_col(col):
        if isinstance(col, Term):
            field = col.fields_().copy().pop()
            return field.name
        else:
            return col

    def _build_query_with_valid_data(
            self,
            sub_query_col: Iterable[Union[str, Term]] = None,
            columns: Iterable[Union[str, Term]] = None,
            where: Union[Term, EmptyCriterion] = None,
            distinct: bool = False,
            groupby: Iterable[Union[str, int, Term]] = None,
            having: Iterable[Union[Term, EmptyCriterion]] = None,
            orderby: Iterable[Union[str, Field]] = None,
            order: Union[Order, str] = Order.asc,
            limit: int = None,
            offset: int = None) -> QueryBuilder:
        if where is not None and not isinstance(where, (Term, EmptyCriterion)):
            raise TypeError('事实表只支持使用Pypika Term或EmptyCriterion作为where条件入参')
        # generate sub query from original table , result is the latest data
        ori_table = Table("ori_table")
        sub_query = self.query.from_(self.table.as_("ori_table")) \
            .select(*sub_query_col,
                    self.get_latest_val(ori_table, DECIMAL_COL).as_(DECIMAL_COL),
                    self.get_latest_val(ori_table, STRING_COL).as_(STRING_COL))

        if where is not None:
            sub_query = sub_query.where(where.replace_table(self.table, ori_table))

        sub_query = sub_query.groupby(*sub_query_col)
        sub_table = Table('sub_table')

        # generate main query from sub query , result is the notnull data
        main_query = self.query.from_(sub_query.as_("sub_table"))

        if distinct:
            main_query = main_query.distinct()

        if columns is None:
            columns = [*self.dim_cols, DECIMAL_COL, STRING_COL]

        main_query = main_query.select(*columns)

        main_query = main_query.where(
            (sub_table.field(DECIMAL_COL).isnotnull() | sub_table.field(STRING_COL).isnotnull())
        )

        if groupby is not None:
            main_query = main_query.groupby(*groupby)
        if having is not None:
            main_query = main_query.having(*having)
        if orderby is not None:
            if isinstance(order, str):
                order = Order[order.lower()]
            main_query = main_query.orderby(*orderby, order=order)
        if limit is not None:
            main_query = main_query.limit(limit)
        if offset is not None:
            main_query = main_query.offset(offset)

        return main_query.replace_table(self.table, sub_table)


def _timestamp():  # pragma: no cover
    return int(datetime.now().timestamp() * 1000)


def _format_dt():  # pragma: no cover
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class FactTable(AsyncFactTable, metaclass=SyncMeta):
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
        'insert_null'
    )

    @classmethod
    def start_transaction(cls, flatten: bool = False):
        """不可用

        FactTable不支持事务
        """
        raise NotImplementedError('FactTable does not support transaction.')

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

        def insert_null(self, where: Union[str, Term, EmptyCriterion] = None):
            ...
