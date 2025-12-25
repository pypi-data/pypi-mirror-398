import functools
from collections import defaultdict
from typing import Dict, Iterable, Union, NamedTuple
import itertools

from deepfos.core.cube.constants import DATACOL_DFLT

from pandas import Series
import pandas as pd
import numpy as np


def merge_dict(*dicts):
    rtn = defaultdict(set)
    for dct in dicts:
        for k, v in dct.items():
            rtn[k].update(v)

    return rtn


def dict_to_sql(
    dict_: Dict[str, Iterable[str]],
    eq: str,
    concat: str = 'and',
    bracket: bool = True,
):
    sql_list = []

    for k, v in dict_.items():
        v = tuple(set(v))

        if len(v) == 1:
            sql = f"{k}{eq}{v[0]!r}"
        else:
            sql = f"{k} in {v!r}"

        sql_list.append(sql)

    sql = f" {concat} ".join(sql_list)
    if bracket:
        return '(' + sql + ')'
    return sql


def dicts_to_sql(dicts, sql_type='pandas'):
    eq = '==' if sql_type == 'pandas' else '='

    sql_list = []

    for dc in dicts:
        sql_list.append(dict_to_sql(dc, eq))

    return ' or '.join(sql_list)


def pipe(functions, init_arg):
    for func in functions:
        init_arg = func(init_arg)

    return init_arg


def multi_product(*dataframes: pd.DataFrame, data_col=DATACOL_DFLT, dropna=False):
    counter = itertools.count().__next__
    all_data_cols = [data_col]

    if len(dataframes) == 1:
        return dataframes[0], all_data_cols

    left = dataframes[0]

    for right in dataframes[1:]:

        common_cols = left.columns.intersection(right.columns)
        on = [col for col in common_cols if col != data_col]
        r_suffix = f'_{counter()}'

        if not on:
            # 对于没有公共列的数据，补充一个临时列用于join
            tmp_key = 't3mp#_j01ne6#_key#'
            left[tmp_key] = 1
            right[tmp_key] = 1
            left = left.merge(right, on=tmp_key, how='outer', suffixes=('', r_suffix)).\
                drop(tmp_key, axis=1)
        else:
            left = left.merge(right, on=on, how='outer', suffixes=('', r_suffix))

        if dropna:
            left = left.dropna()

    all_data_cols.extend(f"{data_col}_{i}" for i in range(counter()))
    return left, all_data_cols


def guard_method(*candidates, attr):

    def guard(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            target = getattr(self, attr)

            if target not in candidates:
                raise RuntimeError(
                    f"Cannot call {func.__qualname__} while '{attr} = {target}'. "
                    f"Allowed states are: {candidates}")

            return func(self, *args, **kwargs)

        return wrapper

    return guard


class Options(NamedTuple):
    missing_value_add: Union[int, float] = 0
    missing_value_radd: Union[int, float] = 0
    missing_value_sub: Union[int, float] = 0
    missing_value_rsub: Union[int, float] = 0
    missing_value_mul: Union[int, float] = 1
    missing_value_rmul: Union[int, float] = 1
    # missing_value_div: Union[int, float] = np.NaN
    # missing_value_rdiv: Union[int, float] = np.NAN
    fill_missing_against_constant: bool = True

    def replace(self, /, **options):
        result = self._make(map(options.pop, self._fields, self))
        if options:
            raise ValueError(f'Got unexpected options: {list(options)!r}')
        return result


def _auto_fill(func, key):
    @functools.wraps(func)
    def wrapper(self, other):
        value = getattr(self.custom_options, key)

        if not isinstance(other, self.__class__):
            if self.custom_options.fill_missing_against_constant:
                me = self.fillna(value, downcast='infer')
            else:
                me = self
            return func(me, other)

        both_nan = self.isna() & other.isna()
        me = self.fillna(value, downcast='infer')
        other = other.fillna(value, downcast='infer')

        rslt = func(me, other)
        rslt.loc[both_nan] = np.NAN
        return rslt

    return wrapper


class AutoFillSeries(Series):
    _metadata = ['custom_options']

    @property
    def _constructor(self):
        return AutoFillSeries

    @property
    def _constructor_expanddim(self):
        return AutoFillSeries

    __add__ = _auto_fill(Series.__add__, 'missing_value_add')
    __sub__ = _auto_fill(Series.__sub__, 'missing_value_sub')
    __mul__ = _auto_fill(Series.__mul__, 'missing_value_mul')
    __radd__ = _auto_fill(Series.__radd__, 'missing_value_radd')
    __rsub__ = _auto_fill(Series.__rsub__, 'missing_value_rsub')
    __rmul__ = _auto_fill(Series.__rmul__, 'missing_value_rmul')


def create_df_by_cproduct(col_map: Dict) -> pd.DataFrame:
    data = list(itertools.product(*col_map.values()))
    columns = list(col_map.keys())

    return pd.DataFrame(data, columns=columns)


def iter_rename_map(node, start=0, offset=None):
    class Level:
        level = 0

    end = start + (offset or np.PINF)

    level_end = Level()
    rename_map = {}

    node_to_visit = node.children[:]
    node_to_visit.append(level_end)

    while node_to_visit:
        child = node_to_visit.pop(0)

        if child is level_end:
            if not rename_map:
                break

            if start <= level_end.level < end:
                yield rename_map

            level_end.level += 1
            node_to_visit.append(level_end)
            rename_map = {}
        else:
            rename_map[child.name] = child.parent.name
            for grandchild in child.children:
                node_to_visit.append(grandchild)


class _Zero:
    def __bool__(self):
        return False

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            return other
        return self

    def __radd__(self, other):
        return self + other

    def __mul__(self, other):
        return self

    def __rmul__(self, other):
        return self

    def __str__(self):
        return 'ZERO'

    def __eq__(self, other):
        return self is other


Zero = _Zero()
