
__all__ = ['AndFilter', 'NAndFilter', 'OrFilter', 'NorFilter', 'RemoveFilter', 'BaseFilter']

import functools

_NOTSET = object()


class BaseFilter:
    def __init__(self, attr_kv_pairs, objs=None):
        """
        Args:
            attr_kv_pairs(dict): 属性键值对
            objs: 被过滤的对象
        """
        self.objs = objs
        self.attr_kv_pairs = attr_kv_pairs

    def iter_single(self, obj):
        for attr, val in self.attr_kv_pairs.items():
            actual = getattr(obj, attr, _NOTSET)
            if actual is _NOTSET:
                yield False
            else:
                yield val == actual

    def filter_strategy(self, obj):
        """过滤策略"""
        raise NotImplementedError()

    def apply(self):
        """执行过滤策略"""
        return self.apply_to(self.objs)

    def apply_to(self, objs):
        """返回符合过滤策略的对象列表"""
        return [obj for obj in objs if self.filter_strategy(obj)]

    def __str__(self):
        return self.__class__.__name__


class AndFilter(BaseFilter):
    """筛选符合全部属性要求的节点"""
    def filter_strategy(self, obj):
        return all(self.iter_single(obj))


class NAndFilter(AndFilter):
    """筛选除了符合全部属性要求节点的节点"""
    def filter_strategy(self, obj):
        return not super().filter_strategy(obj)


class OrFilter(BaseFilter):
    """筛选符合任意一项属性要求的节点"""
    def filter_strategy(self, obj):
        return any(self.iter_single(obj))


class NorFilter(OrFilter):
    """筛选不符合全部属性要求的节点"""
    def filter_strategy(self, obj):
        return not super().filter_strategy(obj)


class RemoveFilter:
    def __init__(self, to_remove, mbr_getter=None):
        """
        Args:
            to_remove(list): 列表元素为 ``DimMember`` 类型，需要移除的节点
            mbr_getter:
        """
        self.to_remove = to_remove
        self.getter = mbr_getter or (lambda x: x)

    def apply_to(self, total):
        """
        Args:
            total(list):  ``DimMember`` 对象列表，从中移除 ``to_remove`` 中的对象

        Returns:
            返回 ``DimMember`` 对象列表

        Tips:
            如果需要被移除的对象不存在于 ``total`` 中，则不做任何事

        """
        if not self.to_remove:
            return total
        to_remove = functools.reduce(
            lambda x, y: x | y,
            (set(self.getter(obj)) for obj in self.to_remove),
            set()
        )
        return [obj for obj in total if obj not in to_remove]

    def __str__(self):
        return 'Remove'
