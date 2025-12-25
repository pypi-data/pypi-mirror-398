from deepfos.core.logictable.nodemixin import ShareableNodeMixin
from ._base import MemberContainer, MemberBase, pack_filter, flatten


class GeneralMemberProxy(MemberContainer):
    def __init__(self, *anchor_mbrs, hierarchy=None, node_attr=None):
        super().__init__(*anchor_mbrs, hierarchy=hierarchy)
        self.node_attr = node_attr

    def _get_all_member(self):
        super()._get_all_member()
        return flatten(getattr(mbr, self.node_attr) for mbr in self.anchor_mbrs)


class LevelMemberProxy(GeneralMemberProxy):
    @property
    def members(self):
        include = self.node_attr.startswith('i')
        levels = flatten(list(mbr.iter_level(self.start, self.stop, include)) for mbr in self.anchor_mbrs)
        return self.apply_filter(levels)

    def __getitem__(self, item):
        super().__getitem__(item)

        start, stop = item.start, item.stop
        if start is None:
            raise ValueError("Start level is not specified.")

        if stop is None:
            raise ValueError("Stop level is not specified.")

        if stop <= start:
            raise ValueError("Stop level should be greater than start.")

        self.start, self.stop = start, stop
        return self

    def __str__(self):
        order = 1 if self._reversed else 0

        if self.start is None or self.stop is None:
            raise RuntimeError(
                "start|stop level is not specified. "
                "Use slice [] syntax to indicated level detail.")
        raw_expr = ';'.join(
            f"{self.hierarchy}({anchor},{order},{self.start},{self.stop})"
            for anchor in self.anchor_mbrs)

        return pack_filter(raw_expr, self._filters)


class AsMbrProxy:
    def __init__(self, data_mapping, proxy_cls=GeneralMemberProxy):
        self._dmap = data_mapping
        self.proxy_cls = proxy_cls

    def __get__(self, instance, owner=None):
        proxy = self.proxy_cls(instance, hierarchy=self.name, node_attr=self._dmap)
        return proxy

    def __set_name__(self, owner, name):
        self.name = name


class DimMember(MemberBase, ShareableNodeMixin):
    def __init__(self, name):
        super(DimMember, self).__init__(name)
        self.extra_attrs = ()

    #: 寻找以当前节点为根的维度树的叶子节点。
    Base = AsMbrProxy("base")
    #: 寻找以当前节点为根的维度树的叶子节点，包含自身。
    IBase = AsMbrProxy("ibase")
    #: 寻找当前节点的直接孩子节点。
    Children = AsMbrProxy("children")
    #: 寻找当前节点的直接孩子节点， 包含自身。
    IChildren = AsMbrProxy("ichildren")
    #: 寻找当前节点的后继节点。
    Descendant = AsMbrProxy("descendant")
    #: 寻找当前节点的后继节点，包含自身。
    IDescendant = AsMbrProxy("idescendant")
    #: level节点。
    Level = AsMbrProxy("level", LevelMemberProxy)
    #: level节点，包含自身。
    ILevel = AsMbrProxy("ilevel", LevelMemberProxy)

    @property
    def data(self):
        """返回当前维度成员的成员名， ``list`` 类型。"""
        return [self.name]

    def to_dict(self, *attrs, name, parent_name, show_all=False, exclude=None):
        """
        将当前维度成员及其指定属性存储为字典。

        Args:
            *attrs(dict): 字典需要包含的维度成员指定属性
            name(str): 维度成员名
            parent_name(str): 维度成员的父节点名
            show_all(bool): 显示成员的所有属性
            exclude: 需要排除（不输出）的属性

        Returns:
            包含当前维度成员指定信息的字典

        """
        if show_all:
            attrs = self.extra_attrs

        if isinstance(exclude, str):
            exclude = {exclude}
        else:
            exclude = exclude or set()

        rtn = {attr: getattr(self, attr) for attr in attrs if attr not in exclude}
        rtn[name] = self.name
        parent = self.parent
        rtn[parent_name] = None if not parent else [p.name for p in parent]
        return rtn

    def where(self, method, **kwargs):
        """
        判断当前维度成员的属性按照 ``method`` 是否符合指定属性。

        Args:
            method(str): 判断方法，包含 ``and` ， ``nand`` ， ``or`` ， ``nor``
            **kwargs: 要求的属性

        Returns:
            成员对象容器

        Warnings:
            返回值是成员对象容器，需要调用容器的 ``members`` 或 ``data`` 才能执行操作。
            此函数一般用于和 ``Dimension`` 的 ``select`` 搭配使用，不推荐单独使用。

        """
        return MemberContainer(self).where(method, **kwargs)

    def remove(self, *to_remove):
        """
        移除当前成员对象

        Args:
            *to_remove(DimMember): 需要移除的成员对象

        Returns:
            成员对象容器

        Warnings:
            返回值是成员对象容器，需要调用容器的 ``members`` 才能执行操作。
            如果当前成员对象存在于 ``*to_remove`` 中，则移除当前成员对象，否则，直接返回。
            此函数一般用于和 ``Dimension`` 的 ``select`` 搭配使用，不推荐单独使用。

        """
        return MemberContainer(self).remove(*to_remove)
