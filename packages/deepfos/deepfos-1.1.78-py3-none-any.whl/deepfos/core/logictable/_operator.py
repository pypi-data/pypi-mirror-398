"""
sql操作符相关类
OpStr开头的类属于字符类型支持的操作符
其余Op开头的用于数字,日期等支持比较运算符的对象。

同类操作符在__and__函数下是完整的域，
即任意两个操作符进行&运算后，产生的结果仍属于这类操作符。
"""
import operator
import datetime

from collections.abc import Sequence, Set

import pandas as pd

IN = "in"
NOT_IN = "ni"
EQUAL = "eq"
NOT_EQ = "ne"
GREAT_THAN = "gt"
GREAT_EQ = "ge"
LESS_THAN = "lt"
LESS_EQ = "le"

TYPE_TIME = (datetime.datetime, pd.Timestamp)


class _Largest(object):  # pragma: no cover
    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __le__(self, other):
        return self == other

    def __lt__(self, other):
        return False

    def __gt__(self, other):
        return True

    def __ge__(self, other):
        return True

    def __repr__(self):
        return "<PINF>"


class _Smallest(object):  # pragma: no cover
    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __le__(self, other):
        return True

    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return self == other

    def __repr__(self):
        return "<NINF>"


PINF = _Largest()
NINF = _Smallest()


class OpCombineError(Exception):
    def __init__(self, op1, op2):
        self.err = f"Cannot combine {op1!r} with {op2!r}."
        super().__init__(self.err)


def _str_init(op, value):
    if op == EQUAL:
        return OpStrEqual(value)
    if op == NOT_EQ:
        return OpStrNotEqual(value)
    if op == IN:
        return OpStrIn(value)
    if op == NOT_IN:
        return OpStrNotIn(value)
    raise TypeError(f"Unknown operator type for string: {op!r}.")


def _common_init(op, value):
    if op == EQUAL:
        return OpEqual(value)
    if op == NOT_EQ:
        return OpMultiInterval(
            Interval(NINF, value, False, False),
            Interval(value, PINF, False, False)
        )
    if op == IN:
        return OpIn(value)

    if op == NOT_IN:
        vals = [NINF, *sorted(value), PINF]
        return OpMultiInterval(*[
            Interval(lb, ub, False, False) for
            lb, ub in zip(vals[:-1], vals[1:])
        ])

    if op == GREAT_THAN:
        return OpMultiInterval(
            Interval(value, PINF, False, False)
        )
    if op == GREAT_EQ:
        return OpMultiInterval(
            Interval(value, PINF, True, False)
        )

    if op == LESS_THAN:
        return OpMultiInterval(
            Interval(NINF, value, False, False)
        )
    if op == LESS_EQ:
        return OpMultiInterval(
            Interval(NINF, value, False, True)
        )
    raise TypeError(f"Unknown operator type: {op!r}.")


class OpFactory:
    def __new__(cls, op, value):
        if isinstance(value, str):
            return _str_init(op, value)
        elif isinstance(value, (Sequence, Set)):
            if len(value) == 0:
                raise ValueError("Value must not be an empty [sequence|set].")
            if isinstance(value, Set):
                value = list(value)
            if isinstance(value[0], str):
                return _str_init(op, value)
        return _common_init(op, value)


def _tuple_repr(tup, tail_comma=False):
    if isinstance(tup[0], TYPE_TIME):
        tup = tuple(dt.strftime('%Y-%m-%d %H:%M:%S') for dt in tup)
    if len(tup) == 1 and not tail_comma:
        return f"({tup[0]!r})"
    else:
        return repr(tup)


###########################################
# Operators For Object Support Comparison #
###########################################
class BaseOperator:
    op = None
    op_pandas = None

    def __init__(self, value):
        # 对于class：In，NotIn，在基类已经处理为set类。
        if not isinstance(value, str) and \
                isinstance(value, Sequence):  # pragma: no cover
            self.value = set(value)
        elif isinstance(value, pd.Timestamp):
            self.value = value.to_pydatetime()
        else:
            self.value = value
        if self.op_pandas is None:
            self.op_pandas = self.op

    def __and__(self, other):  # pragma: no cover
        return other

    def __iand__(self, other):  # pragma: no cover
        return other

    def _as_string(self, sort=False):
        if isinstance(self.value, set):
            if sort:
                value = _tuple_repr(tuple(sorted(self.value)))
            else:
                value = _tuple_repr(tuple(self.value))
        elif isinstance(self.value, TYPE_TIME):
            value = repr(self.value.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            value = repr(self.value)
        return f"{self.op}{value}"

    def __repr__(self):
        return self._as_string(sort=False)

    def __str__(self):
        return self._as_string(sort=True)

    def to_sql_template(self, quote_char='`'):
        return f"{quote_char}{{0}}{quote_char}{repr(self)}"

    def to_pandasql(self):
        if isinstance(self.value, set):
            value = tuple(self.value)
        else:
            value = self.value
        return f"{{0}}{self.op_pandas.lower()}{value!r}"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value

    def __lt__(self, other):
        return self <= other and not self == other

    def __le__(self, other):
        if self == other:
            return True
        try:
            return (self & other) == self
        except OpCombineError:
            return False


class BaseOpInNotIn(BaseOperator):
    fallback = None

    def __new__(cls, value):
        if isinstance(value, str):
            raise TypeError("value must be [list|tuple|set].")
        try:
            val = list(value)
        except Exception:
            raise TypeError("value must be [list|tuple|set].") from None
        else:
            if len(val) == 1:
                return cls.fallback(val[0])
            else:
                return super().__new__(cls)

    def __init__(self, value):
        if len(value) == 0:
            raise ValueError("value must not be empty.")
        value = set(v.to_pydatetime() if isinstance(v, pd.Timestamp) else v for v in value)
        super(BaseOpInNotIn, self).__init__(value)


class OpEqual(BaseOperator):
    op = '='
    op_pandas = '=='

    def __and__(self, other):
        if isinstance(other, OpEqual):
            if self.value != other.value:
                raise OpCombineError(self, other)
        elif isinstance(other, OpIn):
            if self.value not in other.value:
                raise OpCombineError(self, other)
        elif isinstance(other, OpMultiInterval):
            if self.value not in other:
                raise OpCombineError(self, other)
        else:
            raise OpCombineError(self, other)
        return OpEqual(self.value)

    def __eq__(self, other):
        if isinstance(other, (Interval, OpMultiInterval)):
            return other == self
        return super().__eq__(other)


class OpIn(BaseOpInNotIn):
    fallback = OpEqual
    op = ' IN '

    def __and__(self, other):
        if isinstance(other, OpEqual):
            return other & self
        elif isinstance(other, OpIn):
            new_set = self.value.intersection(other.value)
            if not new_set:
                raise OpCombineError(self, other)
            return OpIn(new_set)
        elif isinstance(other, OpMultiInterval):
            new_val = [
                val for val in self.value if
                val in other
            ]
            if not new_val:
                raise OpCombineError(self, other)
            else:
                return OpIn(new_val)
        else:
            raise OpCombineError(self, other)

    def __eq__(self, other):
        if isinstance(other, OpMultiInterval):
            return other == self
        return super().__eq__(other)


class Interval:
    def __init__(self, lower_bound, upper_bound, close_lower, close_upper):
        if not isinstance(lower_bound, pd.Timestamp):
            self.lower = lower_bound
        else:
            self.lower = lower_bound.to_pydatetime()

        if not isinstance(upper_bound, pd.Timestamp):
            self.upper = upper_bound
        else:
            self.upper = upper_bound.to_pydatetime()

        if self.lower > self.upper:
            raise ValueError("Upper bound must be greater or equal to lower bound!")

        self.cl = close_lower
        self.cu = close_upper

    def __repr__(self):
        if self.is_point:
            value = self.lower
            if isinstance(value, TYPE_TIME):
                return f"={value.strftime('%Y-%m-%d %H:%M:%S')!r}"
            else:
                return f"={value!r}"
        return f"{'[' if self.cl else '('}{self._as_str(self.lower)}, " \
               f"{self._as_str(self.upper)}{']' if self.cu else ')'}"

    def __contains__(self, item):
        if self.is_empty:
            return False
        ge_or_gt = operator.ge if self.cl else operator.gt
        le_or_lt = operator.le if self.cu else operator.lt
        return ge_or_gt(item, self.lower) and le_or_lt(item, self.upper)

    def overlap(self, other: 'Interval'):
        if self.is_empty or other.is_empty:
            return False
        left, right = sorted([self, other], key=operator.attrgetter('lower', 'upper'))

        if left.upper > right.lower:
            return True
        elif left.upper == right.lower:
            return left.cu and right.cl
        else:
            return False

    @property
    def is_empty(self):
        return (self.lower == self.upper) and (not self.cl or not self.cu)

    def __or__(self, other: 'Interval'):
        if self.is_empty:
            return other
        if other.is_empty:
            return self

        left, right = sorted([self, other], key=operator.attrgetter('lower', 'upper'))

        if not self.overlap(other):
            if left.upper == right.lower and (left.cu or right.cl):
                return Interval(left.lower, right.upper, left.cl, right.cu)
            return [self, other]

        if left.lower == right.lower:
            close_lower = left.cl or right.cl
        else:
            close_lower = left.cl

        if left.upper == right.upper:
            close_upper = left.cu or right.cu
        else:
            close_upper = right.cu

        return Interval(left.lower, right.upper, close_lower, close_upper)

    def __and__(self, other: 'Interval'):
        if not self.overlap(other):
            return Interval.make_empty()

        if self.lower > other.lower:
            lower_bound = self.lower
            close_lower = self.cl
        elif self.lower == other.lower:
            lower_bound = self.lower
            close_lower = self.cl and other.cl
        else:
            lower_bound = other.lower
            close_lower = other.cl

        if self.upper < other.upper:
            upper_bound = self.upper
            close_upper = self.cu
        elif self.upper == other.upper:
            upper_bound = self.upper
            close_upper = self.cu and other.cu
        else:
            upper_bound = other.upper
            close_upper = other.cu

        return Interval(lower_bound, upper_bound, close_lower, close_upper)

    @classmethod
    def make_empty(cls):
        return cls(0, 0, False, False)

    @staticmethod
    def _as_str(obj, force_repr=False):
        if not force_repr and isinstance(obj, TYPE_TIME):
            return repr(obj.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            return repr(obj)

    def __to_sql(self, quote_field=True, force_repr=False, quote_char='`'):
        ge_or_gt = '>=' if self.cl else '>'
        le_or_lt = '<=' if self.cu else '<'
        field = f"{quote_char}{{0}}{quote_char}" if quote_field else "{0}"
        if self.upper == PINF:
            return f"{field}{ge_or_gt}{self._as_str(self.lower, force_repr)}"
        if self.lower == NINF:
            return f"{field}{le_or_lt}{self._as_str(self.upper, force_repr)}"
        else:
            return f"({field}{le_or_lt}{self._as_str(self.upper, force_repr)} " \
                   f"and {field}{ge_or_gt}{self._as_str(self.lower, force_repr)})"

    def to_sql_template(self, quote_char='`'):
        if self.is_point:
            return OpEqual(self.lower).to_sql_template(quote_char=quote_char)
        return self.__to_sql(quote_field=True, force_repr=False, quote_char=quote_char)

    def to_pandasql(self):
        if self.is_point:
            return OpEqual(self.lower).to_pandasql()
        return self.__to_sql(quote_field=False, force_repr=True)

    def __eq__(self, other):
        if isinstance(other, OpEqual):
            return self.is_point and self.lower == other.value
        elif not isinstance(other, self.__class__):
            return False

        if self.is_empty and other.is_empty:
            return True

        if not (self.upper == other.upper and self.lower == other.lower):
            return False
        lower_match = self.cl == other.cl
        upper_match = self.cu == other.cu
        if self.upper == PINF:
            upper_match = True
        if self.lower == NINF:
            lower_match = True
        return upper_match and lower_match

    def __lt__(self, other):
        return self <= other and (not self == other)

    def __le__(self, other):
        return self & other == self

    @property
    def is_point(self):
        return self.lower == self.upper and self.cl and self.upper


class OpMultiInterval:
    def __init__(self, *interval: Interval):
        self.intervals = list(interval)
        self.merge()

    def sort(self):
        self.intervals.sort(key=operator.attrgetter('lower', 'upper'))
        return self

    def merge(self):
        self.sort()
        rtn = [Interval.make_empty()]
        for it in self.intervals:
            cur_inv = rtn.pop()
            cur_inv |= it
            if isinstance(cur_inv, list):
                rtn.extend(cur_inv)
            else:
                rtn.append(cur_inv)
        self.intervals = rtn
        return self

    def __repr__(self):
        return '|'.join(repr(it) for it in self.intervals)

    def __contains__(self, item):
        return any(item in rg for rg in self.intervals)

    def __and__(self, other):
        if isinstance(other, (OpEqual, OpIn)):
            return other & self

        elif isinstance(other, OpMultiInterval):
            all_invs = []
            for sinv in self.intervals:
                inv_list = []
                for oinv in other.intervals:
                    intersxn = sinv & oinv
                    if not intersxn.is_empty:
                        inv_list.append(intersxn)
                all_invs.extend(inv_list)

            rtn = OpMultiInterval(*all_invs)
            if any(it.is_empty for it in rtn.intervals):
                raise OpCombineError(self, other)
            return rtn

    def __to_sql(self, engine='mysql', quote_char='`'):
        if engine == 'mysql':
            conctr = ' OR '
            caller = operator.methodcaller('to_sql_template', quote_char=quote_char)
        elif engine == 'pandas':
            conctr = ' or '
            caller = operator.methodcaller('to_pandasql')
        else:  # pragma no cover
            raise ValueError(f"Unsupported engine type: {engine}")

        if len(self.intervals) == 1:
            return caller(self.intervals[0])
        elif all(it.is_point for it in self.intervals):
            return caller(OpIn(list(it.lower for it in self.intervals)))
        return '(' + conctr.join(caller(it) for it in self.intervals) + ')'

    def to_sql_template(self, quote_char='`'):
        return self.__to_sql(engine='mysql', quote_char=quote_char)

    def to_pandasql(self):
        return self.__to_sql(engine='pandas')

    def __eq__(self, other):
        its = self.intervals
        if isinstance(other, OpEqual):
            return len(its) == 1 and \
                its[0].is_point and \
                its[0].lower == other.value
        elif isinstance(other, OpIn):
            return len(its) == len(other.value) and \
                all(it.is_point for it in its) and \
                set(it.lower for it in its) == other.value
        elif not isinstance(other, OpMultiInterval):
            return False
        if not len(its) == len(other.intervals):
            return False
        return all(its == ito for its, ito in zip(its, other.intervals))

    def __le__(self, other):
        if self.is_empty:
            return True

        if isinstance(other, (OpEqual, OpIn)):
            try:
                return other & self == self
            except OpCombineError:
                return False

        o_its = other.intervals
        o_its_len = len(o_its)

        idx = 0  # other.intervals的当前下标
        le_count = 0  # 已经在other找到其所属区间的self.interval的数量
        for s_it in self.intervals:
            while idx < o_its_len:
                if s_it <= o_its[idx]:
                    le_count += 1
                    break
                else:
                    idx += 1

        # 必须全部都找到所属区间
        return le_count == len(self.intervals)

    def __lt__(self, other):  # pragma: no cover
        return self <= other and not (self == other)

    @property
    def is_empty(self):
        return all(it.is_empty for it in self.intervals)


########################
# Operators For String #
########################
class OpStrEqual(BaseOperator):
    op = '='
    op_pandas = '=='

    def __and__(self, other):
        if isinstance(other, OpStrEqual):
            if self.value != other.value:
                raise OpCombineError(self, other)
        elif isinstance(other, OpStrNotEqual):
            if self.value == other.value:
                raise OpCombineError(self, other)
        elif isinstance(other, OpStrIn):
            if self.value not in other.value:
                raise OpCombineError(self, other)
        elif isinstance(other, OpStrNotIn):
            if self.value in other.value:
                raise OpCombineError(self, other)
        else:
            raise OpCombineError(self, other)
        return OpStrEqual(self.value)


class OpStrIn(BaseOpInNotIn):
    op = ' IN '
    fallback = OpStrEqual

    def __and__(self, other):
        if isinstance(other, OpStrEqual):
            return other & self
        elif isinstance(other, OpStrNotEqual):
            if other.value in self.value:
                new_set = self.value.copy()
                new_set.remove(other.value)
                # 由于value只有一个时会退化成OpStrEqual，此处new_set不可能为空
                if not new_set:  # pragma: no cover
                    raise OpCombineError(self, other)
                return OpStrIn(new_set)
            else:
                return OpStrIn(self.value)
        elif isinstance(other, OpStrIn):
            new_set = self.value.intersection(other.value)
            if not new_set:
                raise OpCombineError(self, other)
            return OpStrIn(new_set)
        elif isinstance(other, OpStrNotIn):
            remain = self.value - other.value
            if not remain:
                raise OpCombineError(self, other)
            return OpStrIn(remain)
        else:
            raise OpCombineError(self, other)


class OpStrNotEqual(BaseOperator):
    op = '!='

    def __and__(self, other):
        if isinstance(other, (OpStrEqual, OpStrIn)):
            return other & self
        elif isinstance(other, OpStrNotEqual):
            if self.value == other.value:
                return OpStrNotEqual(self.value)
            else:
                return OpStrNotIn((self.value, other.value))
        elif isinstance(other, OpStrNotIn):
            return OpStrNotIn(other.value.union({self.value}))
        else:
            raise OpCombineError(self, other)


class OpStrNotIn(BaseOpInNotIn):
    op = ' NOT IN '
    fallback = OpStrNotEqual

    def __and__(self, other):
        if isinstance(other, (OpStrEqual, OpStrIn, OpStrNotEqual)):
            return other & self
        elif isinstance(other, OpStrNotIn):
            return OpStrNotIn(self.value.union(other.value))
        else:
            raise OpCombineError(self, other)
