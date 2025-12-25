"""多语言"""

import os
import gettext as _builtin_gettext

from collections import defaultdict
from typing import Dict, Optional, Union

from deepfos.options import OPTION, _normalize_locale # noqa


__all__ = [
    'load',
    'add',
    'add_plural',
    'update',
    'install',
    'gettext',
    'ngettext',
    'get_translator'
]

LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'i18n')


class DeepFosTranslations(_builtin_gettext.GNUTranslations):
    def __init__(self, fp=None):
        super().__init__(fp=fp)
        if fp is None:
            self._catalog = {}
            self.plural = lambda n: int(n != 1)

    def add(self, msg_id: str, msg_str: str):
        self._catalog[msg_id] = msg_str

    def add_plural(
        self, 
        msg_id: str, 
        singular: Optional[str], 
        plural: Optional[str]
    ):
        if singular is not None:
            self._catalog[(msg_id, False)] = singular
        if plural is not None:
            self._catalog[(msg_id, True)] = plural

    def update(self, translation: Dict[str, str]):
        self._catalog.update(translation)

    def set_fallback(self, fallback):
        self._fallback = fallback


_user_translator: Dict[str, DeepFosTranslations] = defaultdict(DeepFosTranslations)


def _get_locale(locale: Optional[str]):
    """获取当前语言设置

    对于不规范的语言设置，会修改为符合规范的语言。

    Args:
        locale: 语言标识

    >>> _get_locale('zh-cn')
    'zh_CN'

    """
    if locale is None:
        return OPTION.general.locale
    return _normalize_locale(locale)


def update(translation: Dict[str, str], locale: Optional[str] = None):
    """更新翻译

    更新指定语种的翻译表，如果不指定语种，则使用当前默认语种。

    Args:
        translation: 翻译表
        locale: 翻译的目标语种

    See Also:
        :func:`load`

    >>> update({'from': 'to'})
    >>> gettext('from')
    'to'

    """
    get_translator(locale).update(translation)


def load(
    full_translation: Dict[str, Dict[str, Union[str, Dict[str, str]]]],
    locale: Optional[str] = None
):
    """更新翻译

    更新指定语种的翻译表，如果不指定语种，则使用当前默认语种。

    Args:
        full_translation: 包含所有语种的完整翻译表
        locale: 翻译的目标语种


    Important:
        为了减少内存占用，虽然翻译表中可能包含所有语种，
        但只有当前或指定语种的翻译表会被加载。因此如果在代码中切换了语言，
        将需要再次调用此函数。

    See Also:
        :func:`update`

    >>> load({
    ...     "key": {
    ...         'zh_CN': 'value_a_ch',
    ...         'en_US': 'value_b_en',
    ...     },
    ...     "item": {
    ...         'en_US': {
    ...             "singular": "single item",
    ...             "plural": "multi items",
    ...         },
    ...         'zh_CN': 'item ch',
    ...     },
    ... })
    >>> gettext('key')
    'value_b_en'
    >>> ngettext('item', 1)
    'single item'
    >>> ngettext('item', 2)
    'multi items'

    """

    trans = get_translator(locale)
    locale = locale or OPTION.general.locale
    norm_locale = _normalize_locale(locale)

    for msg_id, msg_trans in full_translation.items():
        msg = msg_trans.get(locale, msg_trans.get(norm_locale))
        if msg is None:
            continue
        if isinstance(msg, str):
            trans.add(msg_id, msg)
        else:
            singular = msg.get('singular')
            plural = msg.get('plural')
            trans.add_plural(msg_id, singular, plural)


def add(msg_id: str, msg_str: str, locale: Optional[str] = None):
    """增加一条翻译

    Args:
        msg_id: 源字符串
        msg_str: 目标翻译
        locale: 目标语种

    >>> update({'from': 'to'})
    >>> gettext('from')
    'to'

    """
    get_translator(locale).add(msg_id, msg_str)


def add_plural(
    msg_id: str, 
    singular: str, 
    plural: str, 
    locale: Optional[str] = None
):
    """增加一条支持单复数的翻译

    Args:
        msg_id: 源字符串
        singular: 单数时的目标翻译
        plural: 复数时的目标翻译
        locale: 目标语种

    >>> add_plural('item', 'single item', 'multi items')
    >>> ngettext('item', 1)
    'single item'
    >>> ngettext('item', 2)
    'multi items'

    """
    get_translator(locale).add_plural(msg_id, singular, plural)


def get_translator(locale: Optional[str] = None) -> DeepFosTranslations:
    """获取当前语种的翻译器"""
    return _user_translator[_get_locale(locale)]


def gettext(message: str, locale: Optional[str] = None) -> str:
    """获取翻译"""
    return get_translator(locale).gettext(message)


def ngettext(msg_id: str, n: int, locale: Optional[str] = None) -> str:
    """获取单/复数格式的翻译

    Args:
        msg_id: 源字符串
        n: 数量
        locale: 目标语种

    Returns:
        翻译后字符串

    """
    return get_translator(locale).ngettext(msg_id, msg_id, n)


def install():
    """安装翻译器

    此函数会将 gettext 作为 _ 安装到全局命名空间

    >>> update({'from': 'to'})
    >>> install()
    >>> _('from')
    'to'
    """
    user_trans = _user_translator[OPTION.general.locale]
    deepfos_trans = _builtin_gettext.translation(
        'deepfos',
        localedir=LOCALE_DIR,
        fallback=True,
        class_=DeepFosTranslations,
        languages=[OPTION.general.locale]
    )
    user_trans.set_fallback(deepfos_trans)
    user_trans.install()
