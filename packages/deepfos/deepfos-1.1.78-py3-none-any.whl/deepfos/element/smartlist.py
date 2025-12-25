from typing import List, Dict, Optional, Union, Tuple, Any, Iterable, TYPE_CHECKING, TypeVar  # noqa

import pandas as pd

from .base import ElementBase, SyncMeta
from .dimension import Strategy  # noqa
from deepfos.lib.utils import CIEnum, get_language_key_map
from deepfos.lib.asynchronous import future_property
from deepfos.lib.constant import ACCEPT_LANS
from deepfos.api.smartlist import SmartListAPI
from deepfos.api.models.smartlist import (
    SmartListDTO, SmartListUd,
    SmartList as SmartListItem
)
from deepfos.lib.decorator import cached_property

__all__ = [
    'SmartList',
    'AsyncSmartList',
    'SmartListItem'
]


# -----------------------------------------------------------------------------
# utils
class OnDupAction(CIEnum):
    ignore = 'ignore'
    error = 'error'
    replace = 'replace'


class OnAbsAction(CIEnum):
    ignore = 'ignore'
    error = 'error'
    create = 'create'


SelfType = TypeVar('SelfType', bound='AsyncSmartList')


# -----------------------------------------------------------------------------
# core classes
class AsyncSmartList(ElementBase[SmartListAPI]):
    """值列表"""
    @cached_property
    def _item_memo(self) -> Dict[str, SmartListItem]:
        return {
            mbr.subjectValue: mbr
            for mbr in self.meta.smartList
        }

    @cached_property
    def _ud_memo(self) -> Dict[str, SmartListUd]:
        return {
            ud.udName: ud
            for ud in self.meta.smartListUd
        }

    @future_property
    async def meta(self) -> SmartListDTO:
        """值列表的元数据信息"""
        api = await self.wait_for('async_api')
        return await api.sml.data(
            folderId=self.element_info.folderId,
            name=self.element_name
        )

    @staticmethod
    def _get_desc(
        fallback: str,
        desc_zh: str = None,
        desc_en: str = None,
    ):
        if desc_zh is None:
            desc_zh = fallback
        if desc_en is None:
            desc_en = fallback

        return {
            'en': desc_en,
            'zh-cn': desc_zh
        }

    def add(
        self: SelfType,
        value: str,
        desc_zh: str = None,
        desc_en: str = None,
        on_duplicate: Union[OnDupAction, str] = OnDupAction.error,
        **extra: Any,
    ) -> SelfType:
        """增加成员

        调用 :meth:`save` 之后生效。

        Args:
            value: 成员值
            desc_zh: 成员中文描述
            desc_en: 成员英文描述
            on_duplicate: 成员值重复时的行为
            extra: 成员的其他属性，如ud等，可设置的参数参考 :class:`SmartListItem`

        Hint:
            参数 ``on_duplicate`` 的可选值及其说明如下：

            +---------+----------------+
            |   值    |      说明      |
            +=========+================+
            | ignore  | 静默处理，忽略 |
            +---------+----------------+
            |  error  | 抛出异常       |
            +---------+----------------+
            | replace | 替换成员       |
            +---------+----------------+

        Returns:
            self

        See Also:
            :meth:`add_item`

        """
        if value in self._item_memo:
            action = OnDupAction[on_duplicate]
            if action is OnDupAction.error:
                raise ValueError(f"Item {value} already exists.")
            if action is OnDupAction.ignore:
                return self

        desc = self._get_desc(value, desc_zh=desc_zh, desc_en=desc_en)
        item = SmartListItem.construct_from(subjectValue=value, desc=desc, **extra)
        self._item_memo[item.subjectValue] = item
        return self

    def add_item(
        self: SelfType,
        *items: SmartListItem,
        on_duplicate: Union[OnDupAction, str] = OnDupAction.error,
    ) -> SelfType:
        """增加成员对象

        调用 :meth:`save` 之后生效。

        Args:
            *items: 成员对象
            on_duplicate: 成员值重复时的行为，参考 :meth:`add`

        Returns:
            self

        See Also:
            如果不希望自己构造成员对象，可以使用 :meth:`add`

        """
        to_add = []
        action = OnDupAction[on_duplicate]

        for item in items:
            value = item.subjectValue
            if value in self._item_memo:
                if action is OnDupAction.error:
                    raise ValueError(f"Item {value} already exists.")
                if action is OnDupAction.ignore:
                    continue
            to_add.append(item)

        # 其他情况（新增，已存在但替换）都可以直接赋值
        for item in to_add:
            self._item_memo[item.subjectValue] = item
        return self

    def delete(
        self: SelfType,
        *item_values: str,
        silent: bool = True
    ) -> SelfType:
        """删除成员

        调用 :meth:`save` 之后生效。

        Args:
            *item_values: 成员值
            silent: 当成员不存在时，是报错还是静默处理。默认True, 即静默处理。

        Returns:
            self

        """
        item_not_found = []
        for item in item_values:
            if item in self._item_memo:
                del self._item_memo[item]
            else:
                item_not_found.append(item)

        if not silent and item_not_found:
            raise KeyError(f"Item {item_not_found} does not exist.")
        return self

    def update(
        self: SelfType,
        value: str,
        on_absent: Union[OnAbsAction, str] = OnAbsAction.error,
        **upd_attrs: Any,
    ) -> SelfType:
        """更新成员

        调用 :meth:`save` 之后生效。

        Args:
            value: 成员值
            on_absent: 更新字段不存在时的行为
            **upd_attrs: 要更新的成员的属性，如ud等，可设置的参数参考 :class:`SmartListItem`

        Hint:
            参数 ``on_absent`` 的可选值及其说明如下：

            +--------+----------------+
            |   值   |      说明      |
            +========+================+
            | ignore | 静默处理，忽略 |
            +--------+----------------+
            |  error | 抛出异常       |
            +--------+----------------+
            | create | 新建成员       |
            +--------+----------------+

        Returns:
            self

        See Also:
            :meth:`update_item`

        """
        if value not in self._item_memo:
            action = OnAbsAction[on_absent]
            if action is OnAbsAction.error:
                raise ValueError(f"Item {value} does not exist.")
            if action is OnAbsAction.ignore:
                return self
            item = SmartListItem()
        else:
            item = self._item_memo[value]

        # 重命名成员值
        if 'subjectValue' in upd_attrs:
            new_value = upd_attrs['subjectValue']
            if new_value in self._item_memo:
                raise ValueError(
                    f"Cannot rename '{value}' to '{new_value}'. "
                    f"Item '{new_value}' already exists.")

            self._item_memo.pop(value, None)
            value = new_value  # todo:test_case_bug bug fix 2022.9.5

        new_item = SmartListItem.construct_from(item, **upd_attrs)
        self._item_memo[value] = new_item
        return self

    def update_item(
        self: SelfType,
        *items: SmartListItem,
        on_absent: Union[OnAbsAction, str] = OnAbsAction.error
    ) -> SelfType:
        """使用成员对象更新

        Args:
            *items: 更新的成员对象
            on_absent: 更新字段不存在时的行为，参考 :meth:`update`

        Returns:
            self

        See Also:
            如果不希望自己构造成员对象，可以使用 :meth:`update`
        """
        to_update = []
        action = OnAbsAction[on_absent]

        for item in items:
            value = item.subjectValue
            if value not in self._item_memo:
                if action is OnAbsAction.error:
                    raise ValueError(f"Item {value} does not exist.")
                if action is OnAbsAction.ignore:
                    continue
            to_update.append(item)

        for item in to_update:
            self._item_memo[item.subjectValue] = item
        return self

    async def save(self):
        """保存值列表

        将对当前值列表的修改保存至系统。
        """
        payload = SmartListDTO.construct_from(
            self.meta,
            smartList=list(self._item_memo.values()),
            smartListUd=list(self._ud_memo.values())
        )
        return await self._save_impl(payload)

    async def _save_impl(self, payload: SmartListDTO):
        await self.async_api.sml.update(payload)
        # 使memo的缓存失效
        self.__class__.meta.reset(self)
        self.__dict__.pop('_item_memo', None)
        self.__dict__.pop('_ud_memo', None)

    def set_ud(
        self: SelfType,
        ud_num: Union[str, int],
        desc_zh: str = None,
        desc_en: str = None,
        active: bool = True
    ) -> SelfType:
        """设置ud

        对于未设置的ud，会默认新增，如果已经设置过，则更新。
        新增维度默认为激活状态。

        调用 :meth:`save` 之后生效。

        Args:
            ud_num: ud编号
            desc_zh: 中文描述
            desc_en: 英文描述
            active: 是否激活

        Returns:
            self

        """
        ud_name = f"ud{ud_num}"
        ud = self._ud_memo.get(ud_name, SmartListUd(udName=ud_name))
        ud.desc = ud.desc or {}

        if desc_zh is not None:
            ud.desc['zh-cn'] = desc_zh
        if desc_en is not None:
            ud.desc['en'] = desc_en

        if ud.active is not False:
            ud.active = active

        self._ud_memo[ud_name] = ud
        return self

    @property
    def items(self) -> List[SmartListItem]:
        """值列表成员"""
        return list(self._item_memo.values())

    async def load_dataframe(
        self,
        dataframe: pd.DataFrame,
        strategy: Union[Strategy, str] = Strategy.incr_replace,
        **langugage_keys: str
    ):
        """保存 ``DataFrame`` 数据至值列表

        此方法不同于 :meth:`add`，:meth:`delete` 等方法，
        保存结果将直接反映至系统，不需要再调用 :meth:`save` 。

        Args:
            dataframe: 包含值列表数据的 ``DataFrame``
            strategy: 数据保存策略
            **langugage_keys: 值列表成员描述（多语言）对应的列名

        Note:
            1. 数据保存策略可选参数如下：

            +--------------+--------------------------------------------+
            |     参数     |                    说明                    |
            +==============+============================================+
            | full_replace | 完全替换所有值列表成员。                   |
            |              | 此策略将会删除所有已有值列表成员，         |
            |              | 以dataframe为数据源新建值列表成员。        |
            +--------------+--------------------------------------------+
            | incr_replace | 增量替换值列表成员。                       |
            |              | 此策略不会删除已有值列表成员。             |
            |              | 在保存过程中，如果遇到成员名重复的情况，   |
            |              | 会以dataframe数据为准，覆盖已有成员。      |
            +--------------+--------------------------------------------+
            |   keep_old   | 保留已有值列表成员。                       |
            |              | 此策略在保存过程中，遇到成员名重复的情况， |
            |              | 会保留已有成员。其他与incr_replace相同。   |
            +--------------+--------------------------------------------+

            2. 目前描述支持两种语言: ``zh-cn, en``，此方法默认会在dataframe中寻找
            名为 ``'language_zh-cn', 'language_en'`` 的列，将其数据作为对应
            语言的描述。如果想改变这种默认行为，比如希望用'name'列作为中文语言描述，
            可以传入关键字参数: ``language_zh_cn='name'``。

        """
        strategy = Strategy[strategy]
        df = dataframe.copy()
        # create language columns
        language_map = get_language_key_map(langugage_keys)
        for lan, key in language_map.items():
            if key in df.columns:
                df[lan] = df[key]

        # 合并描述列
        lan_columns = list(set(df.columns).intersection(ACCEPT_LANS))
        if lan_columns:
            df['desc'] = df[lan_columns].to_dict(orient='records')
        # pick up valid columns
        valid_columns = list(set(SmartListItem.__fields__).intersection(df.columns))
        # check exist data
        if strategy is Strategy.full_replace:
            existed_items: List[SmartListItem] = []
        else:
            if strategy is Strategy.incr_replace:
                self.delete(*df['subjectValue'], silent=True)
            elif strategy is Strategy.keep_old:
                drop_index = df[df['subjectValue'].isin(self._item_memo)].index
                df = df.drop(drop_index, errors='ignore')

            existed_items: List[SmartListItem] = list(self._item_memo.values())

        df_records = df[valid_columns].to_dict(orient='records')

        items = [mbr.dict(by_alias=True) for mbr in existed_items] + df_records
        payload = SmartListDTO.construct_from(
            self.meta,
            smartList=items,
            smartListUd=list(self._ud_memo.values())
        )
        return await self._save_impl(payload)

    def __getitem__(self, item) -> SmartListItem:  # pragma: no cover
        return self._item_memo[item]

    def __len__(self) -> int:  # pragma: no cover
        return len(self._item_memo)

    def __iter__(self) -> Iterable[SmartListItem]:  # pragma: no cover
        yield from self._item_memo.values()


class SmartList(AsyncSmartList, metaclass=SyncMeta):
    synchronize = ('save', 'load_dataframe')

    if TYPE_CHECKING:
        def save(self):  # pragma: no cover
            ...

        def load_dataframe(
            self,
            dataframe: pd.DataFrame,
            strategy: Union[Strategy, str] = Strategy.incr_replace,
            **langugage_keys: str
        ):  # pragma: no cover
            ...
