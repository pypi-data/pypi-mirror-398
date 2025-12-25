from collections.abc import Iterable
from functools import reduce, wraps

from deepfos.lib.decorator import cached_property
from ._operator import *


class CachedProperty(cached_property):
    cached_names = set()

    def __init__(self, func):
        self.__class__.cached_names.add(func.__name__)
        super().__init__(func)


class SqlCondError(Exception):
    pass


def _df2cond(df, quote_char):
    return ' AND '.join(df.apply(
        lambda s: s.op.to_sql_template(quote_char=quote_char).format(s.field),
        axis=1
    ))


def _df2pandascond(df):
    return ' and '.join(
        df.apply(lambda s: s.op.to_pandasql().format(s.field), axis=1))


def _df2str(df, strfunc=repr):
    col_str = '#'.join(map(repr, df.columns))
    if df.empty:
        return col_str
    return col_str + '#' + df.applymap(lambda x: strfunc(x) + '#').sum().sum()


def _op_and(s):
    return reduce(lambda x, y: x & y, s, BaseOperator(1))


def _op_agg(df_grp):
    op_list = df_grp.apply(lambda x: OpFactory(x.op, x.value), axis=1).values
    return pd.DataFrame(
        [[df_grp['field'].iat[0], _op_and(op_list)]],
        columns=['field', 'op'])


def merge_conditions(val_list: pd.DataFrame, sta_cond: pd.DataFrame):
    """
    将 |联合查询条件| 与 |固定查询条件| 合并，即进行and运算。

    Args:
        val_list: |SQLCND| 中的联合查询条件
        sta_cond: |SQLCND| 中的固定查询条件

    Returns:
        合并后的 |联合查询条件| 及 |固定查询条件|

    >>> vl = pd.DataFrame({'f1': range(5), 'f2': range(5)})
    >>> sc = pd.DataFrame([['f1', OpEqual(1)], ['f3', OpEqual(2)]], columns=['field', 'op'])
    >>> r1, r2 = merge_conditions(vl, sc)
    >>> r1  # 由于固定条件sc中f1==1，联合条件中所有f1!=1的行被删除
       f1  f2
    0   1   1
    >>> r2  # 联合条件中已体现f1==1，固定条件中f1==1被删除，避免重复
      field  op
    0    f3  =2

    """
    if val_list.empty:
        return val_list, sta_cond
    common_fields = set(val_list.columns).intersection(set(sta_cond['field']))
    if not common_fields:
        return val_list, sta_cond

    for index, field, op in sta_cond[sta_cond['field'].isin(common_fields)].itertuples(name=None):
        if isinstance(op, (OpIn, OpEqual, OpMultiInterval)):
            op_in = OpIn
            op_eq = OpEqual
        else:
            op_in = OpStrIn
            op_eq = OpStrEqual

        remain = op & op_in(val_list[field].values)
        if isinstance(remain, op_eq):
            val_list = val_list[val_list[field] == remain.value]
        else:
            val_list = val_list[val_list[field].isin(remain.value)]
        sta_cond.loc[index, 'op'] = None

    return val_list.reset_index(drop=True), sta_cond.dropna().reset_index(drop=True)


class SQLCondition:
    """SQL查询条件

    .. |联合查询条件| replace:: :ref:`联合查询条件<comb-query>`
    .. |固定查询条件| replace:: :ref:`固定查询条件<fix-query>`
    .. |SQLCND| replace:: :class:`SQLCondition`

    记录SQL的查询条件，主要功能：

    * 输出对应的SQL查询语句
    * 进行不同条件的and运算
    * 取出部分字段条件

    在这个类中，查询条件被分为两种：

    .. _comb-query:

    1.联合查询条件
        | 指多个字段与一个值列表的值同时对应相等。
        | 例如有字段:  ``f1, f2`` ，值列表:

        == ==
        f1 f2
        == ==
        1  4
        2  5
        3  6
        == ==

        | 联合查询条件即：
        | ``(f1=1 and f2=4) or (f1=2 and f2=5) or (f1=3 and f2=6)``

    .. _fix-query:

    2.固定查询条件：
        | 除联合查询条件外，其余查询条件均归类为固定查询条件。例如：
        | ``f1>=1, f2 in (1, 2, 3), f1!=2`` 等等。

    Args:
        fields: 联合查询字段
        value_list: 联合查询的值列表
        quote_char: 转义字符
        **kwargs: 其余关键字参数，一般用于指定固定查询条件

    Example:
        >>> SQLCondition(fields=['a', 'b'], value_list=[[1, 4], [2, 5], [3, 6]])
        (a=1 AND b=4) OR (a=2 AND b=5) OR (a=3 AND b=6)
        >>> # kwargs 部分也可以提供联合查询字段。
        >>> SQLCondition(a=range(1, 4), b=range(4, 7))
        (a=1 AND b=4) OR (a=2 AND b=5) OR (a=3 AND b=6)
        >>> # 同时，kwargs部分可以提供一些固定条件
        >>> SQLCondition(a__eq=1, b__in=(1, 2), c__lt=2)
        `a`=1 AND `b` IN (1, 2) AND `c`<2

    Warnings:
        ``kwargs`` 部分虽然也可以提供联合查询字段，
        但是仅当 ``fields, value_list`` 未提供时有效。
        两者同时存在时，``kwargs`` 的联合查询字段会被无视。

    Note:
        固定查询条件的入参规则为 ``{字段名}__{条件字符}={值}``
        所有支持的条件字符为：

        +----------+------------------+---------------------+
        |          |                  |       是否支持      |
        | 条件字符 |       全称       +--------+------------+
        |          |                  | 字符串 | 数字，日期 |
        +----------+------------------+--------+------------+
        |    eq    |       equal      |    ✓   |      ✓     |
        +----------+------------------+--------+------------+
        |    ne    |     not equal    |    ✓   |      ✓     |
        +----------+------------------+--------+------------+
        |    in    |        in        |    ✓   |      ✓     |
        +----------+------------------+--------+------------+
        |    ni    |      not in      |    ✓   |      ✓     |
        +----------+------------------+--------+------------+
        |    lt    |     less than    |    ×   |      ✓     |
        +----------+------------------+--------+------------+
        |    le    |    less equal    |    ×   |      ✓     |
        +----------+------------------+--------+------------+
        |    gt    |   greater than   |    ×   |      ✓     |
        +----------+------------------+--------+------------+
        |    ge    | greater or equal |    ×   |      ✓     |
        +----------+------------------+--------+------------+

    """
    def __init__(self, fields=None, value_list=None, quote_char='`', **kwargs):
        self.fields = []
        self.quote_char = quote_char
        self.__static_cond = pd.DataFrame()

        if fields is not None and value_list is not None:
            self.fields = list(fields)
            if isinstance(value_list, pd.DataFrame):
                self.val_list = value_list.rename(
                    dict(zip(value_list.columns, fields)), axis='columns')
            else:
                self.val_list = pd.DataFrame(value_list, columns=fields)
            self._parse_static_cond(kwargs)
        elif not kwargs:
            raise ValueError("Init failed. Either provide `fields` and `value_list`, or provide kwargs.")
        else:
            self._parse_kwargs(**kwargs)

        # 合并val_list和static_cond
        self.val_list, self.__static_cond = merge_conditions(self.val_list, self.__static_cond)
        if not self.val_list.empty:
            self.val_list.drop_duplicates(inplace=True)
        else:
            self.fields = []

    @cached_property
    def all_fields(self):
        """set: 查询条件涉及的所有字段"""
        return set(self.__static_cond['field'].tolist()) | self.field_set

    @CachedProperty
    def cond_template(self):
        """当前的 |联合查询条件| 模板"""
        return "(" + " AND ".join(f"{k}={{!r}}" for k in self.fields) + ")"

    @CachedProperty
    def field_set(self):
        """set: |联合查询条件| 的字段"""
        return set(self.fields)

    @CachedProperty
    def static_cond(self):
        """ |固定查询条件| 字符串"""
        if self.__static_cond.empty:
            return ''
        return _df2cond(self.__static_cond, self.quote_char)

    def rename_field(self, field_map: dict):
        """重命名字段，将引起类中所有字符串缓存失效"""
        self.fields = [field_map.get(f, f) for f in self.fields]
        self.val_list.rename(field_map, axis=1, inplace=True)
        self.__static_cond['field'].replace(field_map, inplace=True)
        self._clear_cached_property()

    def _clear_cached_property(self):
        for key in CachedProperty.cached_names & self.__dict__.keys():
            del self.__dict__[key]

    def _parse_kwargs(self, **kwargs):
        self._parse_static_cond(kwargs)

        for field in kwargs.keys():
            self.fields.append(field)
        self.val_list = pd.DataFrame(
            list(zip(*kwargs.values())), columns=self.fields)

    def _parse_static_cond(self, kwargs):
        data = []

        for key in list(kwargs.keys()):
            if key.rfind('__') != -1:
                field, op = key.rsplit('__', maxsplit=1)
                data.append([field, op, kwargs[key]])
                kwargs.pop(key)

        self.__check_static_cond_valid(
            pd.DataFrame(data, columns=['field', 'op', 'value']))

    @staticmethod
    def _iter_single_valset(value_list):
        if isinstance(value_list, pd.DataFrame):
            for val in value_list.itertuples(index=False, name=None):
                yield val
        elif isinstance(value_list, Iterable):  # pragma: no cover
            for val in value_list:
                yield val
        else:  # pragma: no cover
            raise TypeError(f"Expect Iterable or DataFrame, got: {type(value_list)}")

    @staticmethod
    def _cal_len(x):
        if isinstance(x, str):
            return len(x) + 3
        else:
            return len(str(x)) + 1

    def to_sql(self, max_len=10E6):
        """
        将所有查询条件转化为符合sql语法的查询条件字符串。

        Args:
            max_len: 单次输出的条件字符串的最大长度

        Returns:
            查询条件字符串的生成器

        Raises:
            ValueError: 给定的max_len太小以至于无法产生sql语句

        Example:
            >>> sc = SQLCondition(f1=range(1, 4), f2=range(4, 7), a__eq=1, b__in=(1, 2), c__lt=2)
            >>> next(sc.to_sql())
            '`a`=1 AND `b` IN (1, 2) AND `c`<2 AND ((f1=1 AND f2=4) OR (f1=2 AND f2=5) OR (f1=3 AND f2=6))'
            >>> for sql in sc.to_sql(max_len=80):
            ...    print(sql)
            `a`=1 AND `b` IN (1, 2) AND `c`<2 AND ((f1=1 AND f2=4) OR (f1=2 AND f2=5))
            `a`=1 AND `b` IN (1, 2) AND `c`<2 AND ((f1=3 AND f2=6))
        """
        fix_cond = self.static_cond  # 本地变量减少引用消耗
        val_list = self.val_list
        qc = self.quote_char

        # 如果只有一列，可以用IN代替
        if len(self.fields) == 1:
            field = self.fields[0]
            cond_tmpl = f"{qc}{field}{qc} IN ({{}})"

            if fix_cond == '':
                fix_part = ''
            else:
                fix_part = fix_cond + ' AND '

            max_len -= len(fix_part) + 8  # 8 is the length of '`` IN ()'

            len_cum = val_list.iloc[:, 0].apply(self._cal_len).cumsum()
            start = end = 0
            vl_len = len(val_list)
            while end < vl_len:
                ses_to_use = len_cum.loc[len_cum <= max_len]
                if ses_to_use.empty:
                    raise ValueError(f"Given max length: [{max_len+len(fix_part)+8}] is too small.")

                used_len = ses_to_use.iat[-1]
                end = ses_to_use.index[-1] + 1
                del ses_to_use
                len_cum = len_cum.loc[len_cum > max_len]
                len_cum -= used_len
                sql_cond = cond_tmpl.format(','.join(map(repr, val_list.loc[start: end-1, field])))
                yield fix_part + sql_cond
                start = end
        else:
            cond_tmpl = self.cond_template
            tmp = []  # 临时保存不超过max_len的值对
            tmp_len = 0  # 记录当前sql语句的长度
            if fix_cond == '':
                fix_form = '{}'
            else:
                fix_form = fix_cond + ' AND ({})'

            max_len -= len(fix_form) - 2  # 2 is the length of '{}'

            for val in self._iter_single_valset(val_list):
                str_to_add = cond_tmpl.format(*val)
                len_to_add = len(str_to_add)
                if len_to_add > max_len:
                    raise ValueError(f"Given max length: [{max_len+len(fix_form)-2}] is too small.")

                tmp_len += 4 + len_to_add  # 4 is the length of ' OR '

                if tmp_len - 4 > max_len:
                    yield fix_form.format(' OR '.join(tmp))
                    tmp = [str_to_add]
                    tmp_len = 4 + len_to_add
                else:
                    tmp.append(str_to_add)
            if not tmp:
                yield fix_cond
            else:
                yield fix_form.format(' OR '.join(tmp))

    def to_pandasql(self):
        """
        将 |固定查询条件| 转换成符合 :meth:`Dataframe.query` 要求的字符串，
        用于缓存查询。 |联合查询条件| 不在此输出。

        Note:
            这个方法主要用于 :class:`Dataframe` 的缓存查询。
            而 |联合查询条件| 可以由 :class:`Dataframe` 之间的运算直接完成。
            因此此处不作输出。
        """
        if self.__static_cond.empty:
            return None
        return _df2pandascond(self.__static_cond)

    def __check_static_cond_valid(self, df):
        """合并同字段的 |固定查询条件| ，如果条件间存在矛盾会抛出OpCombineError"""
        df = df.groupby(['field'], as_index=False).apply(_op_agg).reset_index(drop=True)
        if df.empty:
            self.__static_cond = pd.DataFrame(columns=['field', 'op'])
        else:
            self.__static_cond = df

    def __repr__(self):  # pragma: no cover
        return '\n'.join(self.to_sql())

    def __copy__(self):
        cp = SQLCondition(
            fields=self.fields,
            value_list=self.val_list.copy(),
            quote_char=self.quote_char,
        )
        cp.__static_cond = self.__static_cond.copy()
        return cp

    def __and__(self, other):
        """
        取出两个查询条件的“交集”，如果两个条件没有交，则报错。

        Raises:
            SqlCondError: |联合查询条件| 之间存在矛盾
            OpCombineError: 联合vs固定，固定vs固定之间存在矛盾
        """
        fd_me = self.field_set
        fd_other = other.field_set

        if not fd_me:
            val_list = other.val_list.copy()
        elif not fd_other:
            val_list = self.val_list.copy()
        elif 1 == len(fd_me) == len(fd_other):
            val_list = pd.DataFrame()
            self.__static_cond = pd.concat([
                self.__static_cond,
                pd.DataFrame(data={
                    'field': self.fields[0],
                    'op': [OpFactory(IN, self.val_list.iloc[:, 0])]
                })
            ])
            other.__static_cond = pd.concat([
                other.__static_cond,
                pd.DataFrame(data={
                    'field': other.fields[0],
                    'op': [OpFactory(IN, other.val_list.iloc[:, 0])]
                })
            ])
        else:
            # 字段越多，限制条件越多，一般数据量越小，定义为sub
            if fd_me.issubset(fd_other):
                main = self
                sub = other
            elif fd_me.issuperset(fd_other):
                main = other
                sub = self

            else:
                # 如果两个Condition的字段不存在包含关系，无法判断两个查询集的大小
                raise SqlCondError("One of the condition's fields must be the other one's subset or superset.")
            # todo 设置index，用join替代merge以提高性能
            val_list = main.val_list.merge(sub.val_list, on=main.fields, how='inner')
            if val_list.empty:
                raise SqlCondError(
                    f"Failed to calculate:\n{main.val_list!r}"
                    f"\n>>> & <<<\n{sub.val_list!r}"
                    f"\nconfliction detected."
                )

        static_cond = pd.concat((self.__static_cond, other.__static_cond))
        static_cond = static_cond.groupby('field', as_index=False).agg(_op_and).reset_index(drop=True)
        val_list, static_cond = merge_conditions(val_list, static_cond)
        if val_list.empty:
            cond = SQLCondition([], pd.DataFrame(), quote_char=self.quote_char)
        else:
            cond = SQLCondition(val_list.columns.values, val_list, quote_char=self.quote_char)

        cond.__static_cond = static_cond

        return cond

    def __eq__(self, other):
        return self.serialized == other.serialized

    def __le__(self, other: 'SQLCondition'):
        try:
            return (self & other) == self
        except (SqlCondError, OpCombineError):
            return False

    @CachedProperty
    def serialized(self):
        fields = self.fields
        val_list = self.val_list

        if len(fields) == 1:
            # 将条件归类至sta_cond
            static_cond = pd.concat(
                [
                    self.__static_cond,
                    pd.DataFrame(data={
                        'field': fields,
                        'op': [OpFactory(IN, val_list.iloc[:, 0])]
                    })
                ]
            ).sort_values('field').reset_index(drop=True)
            val_list = pd.DataFrame()
        else:
            static_cond = self.__static_cond.sort_values('field')
            if self.fields:
                fields = sorted(fields)
                val_list = val_list.sort_values(fields)[fields]
        return _df2str(val_list) + _df2str(static_cond, strfunc=str)

    def __getitem__(self, fields):
        """
        根据字段取出当前条件的子条件

        Args:
            fields: 待查字段

        Example:
            >>> sc = SQLCondition(f1=range(1, 4), f2=range(4, 7), a__eq=1, b__in=(1, 2), c__lt=2)
            >>> sc['a']
            `a`=1
            >>> sc['b', 'c', 'notin']
            `b` IN (1, 2) AND `c`<2
            >>> sc['f1']
            `f1` IN (1,2,3)
            >>> sc['f1', 'f2']
            (f1=1 AND f2=4) OR (f1=2 AND f2=5) OR (f1=3 AND f2=6)

        Raises:
            KeyError: 传入的字段全都不在 :attr:`SQLCondition.all_fields` 中

        Note:
            只要有待查字段在 :attr:`SQLCondition.all_fields` 中，调用就能成功。多余字段会被忽视。
        """
        if isinstance(fields, str):
            fields = {fields}
        else:
            fields = set(fields)
        valist_fields = []
        fix_fields = []

        for fld in fields:
            if fld in self.field_set:
                valist_fields.append(fld)
            elif fld in self.all_fields:
                fix_fields.append(fld)

        if not valist_fields and not fix_fields:
            raise KeyError(f"None of fields: {fields!r} is found.")

        rtn = SQLCondition(
            fields=valist_fields,
            value_list=self.val_list[valist_fields].copy(),
            quote_char=self.quote_char,
        )
        if fix_fields:
            rtn.__static_cond = self.__static_cond[self.__static_cond['field'].isin(fix_fields)].copy()
        return rtn


def update_cache(*attrs):
    def deco(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attr in attrs:
                if attr in self.__dict__:
                    delattr(self, attr)
            return func(self, *args, **kwargs)
        return wrapper
    return deco


class ConditionManager:
    def __init__(self):
        self.__main_conds = []
        self.__tmp_conds = []
        self.__altered = False
        self.__valid = False

    altered = property(lambda self: self.__altered)
    valid = property(lambda self: self.__valid)

    def mark_as_valid(self):
        self.__valid = True

    @update_cache('condition')
    def add_main_cond(self, condition: SQLCondition):
        self.__main_conds.append(condition)
        self.__altered = True
        self.__valid = False

    @update_cache('condition')
    def add_tmp_cond(self, condition: SQLCondition):
        self.__tmp_conds.append(condition)
        self.__valid = False

    @update_cache('condition')
    def clear_tmp(self):
        self.__tmp_conds.clear()
        self.__valid = False

    @update_cache('condition')
    def pop_main(self):
        self.__main_conds.pop()
        self.__altered = True
        self.__valid = False

    @cached_property
    def condition(self):
        if not self:
            return None
        conds = self.__main_conds + self.__tmp_conds
        return reduce(lambda x, y: x & y, conds[1:], conds[0])

    def __bool__(self):
        return bool(self.__main_conds + self.__tmp_conds)

    def has_main(self):
        return bool(self.__main_conds)

    @staticmethod
    def any_changed(group):
        changed = False
        for cm in group:
            changed = changed or cm.__altered
            cm.__altered = False
        return changed
