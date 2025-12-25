from typing import Iterable, Optional
from collections import UserDict, defaultdict
import itertools

import pandas as pd
from loguru import logger
from .sqlcondition import SQLCondition


class Cache(UserDict):
    def __init__(self, *args, **kwds):
        super(Cache, self).__init__(*args, **kwds)
        self.__ref_count = defaultdict(int)
        self.__idx_map = {}
        self._counter = itertools.count(1).__next__

    def pop_by_score(self, score_func=None, highest=False):
        if not self:
            raise KeyError('dictionary is empty')

        score_func = score_func or self._score_idx_plus_ref

        sorted_keys = sorted(self.__idx_map.items(), key=score_func, reverse=highest)
        pop_key = sorted_keys[0][0]
        pop_val = self.pop(pop_key)
        self.__idx_map.pop(pop_key)
        return pop_key, pop_val

    def _score_idx_plus_ref(self, key_with_idx, weight_idx=0.8, weight_ref=1):
        key, idx = key_with_idx
        ref_count = self.__ref_count[key]
        return idx * weight_idx + ref_count * weight_ref

    def __getitem__(self, item):
        val = super(Cache, self).__getitem__(item)
        self.__ref_count[item] += 1
        return val

    def __setitem__(self, key, value):
        rslt = super(Cache, self).__setitem__(key, value)
        self.__idx_map[key] = self._counter()
        return rslt


class Fields:
    def __init__(
        self,
        fields: Optional[Iterable[str]],
        extra_fields: Optional[Iterable[str]] = None
    ):
        if fields is None:
            self.flds = None
        else:
            extra_fields = extra_fields or []
            all_flds = {*fields, *extra_fields}
            if any(fld.strip() == '*' for fld in all_flds):
                self.flds = None
            else:
                self.flds = all_flds

    def __le__(self, other: 'Fields'):
        if other.flds is None:
            return True
        elif self.flds is None:
            return other.flds is None
        else:
            return self.flds <= other.flds


class DataProxy:
    def __init__(self, max_size=10):
        self._data_cache = Cache()
        self._cond_cache = dict()
        self._fields_cache = {}
        if not max_size >= 1:
            raise ValueError("Max size must be positive.")
        self._max_size = max_size

    def make_cache(
        self,
        key: SQLCondition,
        fields: Optional[Iterable[str]],
        value: pd.DataFrame,
        force_update: bool = False
    ):
        series_code = key.serialized

        if not force_update and series_code in self._cond_cache \
                and Fields(fields) <= self._fields_cache[series_code]:
            logger.debug("Found a better version in cache. Skip update.")
            return

        self._data_cache[series_code] = value
        self._cond_cache[series_code] = key
        self._fields_cache[series_code] = Fields(fields)

        if len(self._data_cache) > self._max_size:
            rm_key, _ = self._data_cache.pop_by_score()
            logger.debug(f'Removed cache with lowest score:\n{_}')
            self._cond_cache.pop(rm_key)
            self._fields_cache.pop(rm_key)

    def get_data(self, key: SQLCondition, fields: Optional[Iterable[str]]):
        series_code = key.serialized
        if series_code in self._data_cache:
            fields_memo = Fields(fields)
            if fields_memo <= self._fields_cache[series_code]:
                logger.debug("Found perfect-match from cache.")
                if fields_memo.flds is None:
                    return self._data_cache[series_code]
                else:
                    return self._data_cache[series_code][list(fields)]

        for sql_cnd in self._cond_cache.values():
            # 不用小于号是为了避免重复调用__eq__
            if key <= sql_cnd:
                series_code = sql_cnd.serialized
                fields_memo = Fields(fields, key.all_fields)

                if fields_memo <= self._fields_cache[series_code]:
                    cache = self._data_cache[sql_cnd.serialized]
                    data = self.query_from_cache(cache, key)
                    if fields_memo.flds is None:
                        return data
                    else:
                        return data[list(fields)]
        return None

    @staticmethod
    def query_from_cache(cache: pd.DataFrame, key: SQLCondition):
        logger.debug(f"Query {key!r} from cache:\n{cache}")
        query_str = key.to_pandasql()
        if query_str is None:
            data = cache
        else:
            data = cache.query(query_str)
        fields = key.fields
        if fields:
            data = data.merge(key.val_list, on=fields, how='inner')
        logger.debug(f"Got DATA from cache:\n{data}")
        return data.reset_index(drop=True)
