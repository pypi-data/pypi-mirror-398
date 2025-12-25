from operator import methodcaller
import weakref


class LoopError(Exception):
    pass


class TreeError(Exception):
    pass


class NamedTuple(tuple):
    def __new__(cls, *args, **kwargs):
        ins = super().__new__(cls, *args, **kwargs)
        for ele in ins:
            setattr(ins, ele.name, ele)
        return ins


class MetaNodeMixin(type):
    """
    给使用这个元类的类提供方便定义树结构的接口。

    Example:
        .. code-block:: python

            class Root(metaclass=MetaNodeMixin):
                pass

            class ChildA(metaclass=MetaNodeMixin):
                pass

            class ChildB(metaclass=MetaNodeMixin):
                pass

            class GrandChildA(metaclass=MetaNodeMixin):
                pass

            ChildA.set_parent(Root)
            ChildB.set_parent(Root)
            GrandChildA.set_parent(ChildA)
            # 经过上述定义后，将形成如下树结构
            '''
            Root--ChildA--GrandChildA
                └─ChildB
            '''
    """

    @property
    def parent(cls):
        """父节点"""
        try:
            return cls.__parent()
        except AttributeError:
            return None

    @property
    def children(cls):
        """子节点"""
        return [child() for child in cls.__children_ref]

    @property
    def __children_ref(cls):
        """子节点的弱引用列表"""
        try:
            return cls.__children
        except AttributeError:
            cls.__children = []
            return cls.__children

    def set_parent(cls, node):
        """设置父节点。

        将指定的节点设为父节点。如果当前节点已有父节点，
        将首先把当前节点（及其子树）从原树中移除，
        再把当前节点（及其子树）接入新的树中。

        Args:
            node: 待设定的父节点
        """
        if node is not None and not isinstance(node, MetaNodeMixin):
            raise TreeError(f"父节点 {node!r} 不是 'NodeMixin'.")

        if cls.parent is not node:
            cls._check_loop(node)
            cls._detach(cls.parent)
            cls._attach(node)

    def _check_loop(cls, new_parent):
        if new_parent is None:
            return
        if new_parent is cls:
            raise LoopError("父节点不能为自身.")
        if any(ancestor is cls for ancestor in new_parent.iter_to_root()):
            raise LoopError(f"无法设置父节点. {cls!r}已经是{new_parent!r}的祖先.")

    def _detach(cls, parent):
        if parent is None:
            return

        try:
            parent.children.remove(cls)
        except ValueError:
            raise TreeError("Tree is corrupt.")

    def _attach(cls, new_parent):
        if new_parent is None:
            return  # 不用做任何操作，因为parent默认就是None

        parentchildren = new_parent.__children_ref

        if any(child is cls for child in parentchildren):
            raise TreeError("Tree is corrupt.")
        parentchildren.append(weakref.ref(cls))
        cls.__parent = weakref.ref(new_parent)

    def iter_to_root(cls):
        """遍历至根节点

        从当前节点触发遍历至根节点，包括自身。
        """
        node = cls
        while node is not None:
            yield node
            node = node.parent

    def iter_descendants(cls):
        """遍历所有后代节点

        先序遍历所有后代节点，不包括自身。
        """
        for child in cls.children:
            if child is not None:
                yield child
                yield from child.iter_descendants()

    def iter_from_root(cls):
        """从根节点遍历至当前节点

        从根节点遍历至当前节点，包括自身。
        """
        for node in reversed(list(cls.iter_to_root())):
            yield node

    #: 祖先节点
    ancestors = property(lambda self: tuple(self.iter_to_root())[1:])
    #: 节点在树中的深度
    depth = property(lambda self: len(self.ancestors))
    #: tuple: 后代节点
    descendants = property(lambda self: tuple(self.iter_descendants()))
    #: 根节点
    root = property(lambda self: list(self.iter_to_root())[-1])

    @property
    def siblings(cls):
        """
        兄弟节点

        Returns:
            tuple: 如有，返回所有兄弟节点；否则返回空元组

        """
        parent = cls.parent
        if parent is None:
            return tuple()
        else:
            return tuple(node for node in parent.children if node is not cls)

    #: 是否叶子节点
    is_leaf = property(lambda self: not bool(self.children))
    #: 是否根节点
    is_root = property(lambda self: self.parent is None)
    #: tuple: 同一颗树的所有节点
    family = property(lambda self: tuple((self.root, *self.root.descendants)))

    def common_ancestor(cls, *others):
        """获取最小共同祖先

        获取当前节点与其他节点的最小共同祖先，包括其本身。

        Args:
            *others: 其他节点

        Returns:
            最小共同祖先
        """
        common = None

        for antr_me, *antr_others in zip(cls.iter_from_root(), *map(methodcaller('iter_from_root'), others)):
            if all(antr is antr_me for antr in antr_others):
                common = antr_me
            else:
                break

        if common is None:
            raise TreeError(f"{cls!r}和{others!r}不属于同一颗树")
        return common

    def iter_to_descendant(cls, descendant):
        """
        遍历自身到后代节点所经过的所有节点，不包括自身。

        Args:
            descendant: 后代节点
        Raises:
            ValueError: descendant不是自己或自己的后代,
        Note:
            传入 ``descendant==cls`` 并不会引起错误，但也不会返回任何节点
        """
        found = False

        for antr in descendant.iter_from_root():
            if found:
                yield antr
            else:
                if antr is not cls:
                    continue
                else:
                    found = True

        if found is False:
            raise ValueError(f"{descendant!r}不是{cls!r}的后代")


class NodeMixin:
    """
    给使用这个元类的类提供方便定义树结构的接口。

    Example:
        .. code-block:: python

            class Root(NodeMixin):
                pass

            class ChildA(NodeMixin):
                pass

            class ChildB(NodeMixin):
                pass

            class GrandChildA(NodeMixin):
                pass

            ChildA.set_parent(Root)
            ChildB.set_parent(Root)
            GrandChildA.set_parent(ChildA)
            # 经过上述定义后，将形成如下树结构
            '''
            Root--ChildA--GrandChildA
                └─ChildB
            '''
    """
    @property
    def parent(self):
        """父节点"""
        try:
            return self.__parent()
        except AttributeError:
            return None

    @property
    def ichildren(self):
        """返回节点的直接孩子节点，包含自身"""
        return [self, *self.children]

    @property
    def children(self):
        """返回当前节点的直接孩子节点，不包含自身，当前节点无孩子则返回空列表"""
        try:
            return self.__children
        except AttributeError:
            self.__children = []
            return self.__children

    def set_parent(self, node):
        """
        将指定的节点设为父节点。
        如果当前节点已有父节点，将首先把当前节点（及其子树）从原树中移除，
        再把当前节点（及其子树）接入新的树中。

        Args:
            node: 待设定的父节点

        """
        if node is not None and not isinstance(node, NodeMixin):
            raise TreeError(f"父节点 {node!r} 不是 '{self.__class__.__name__}'.")

        if self.parent is not node:
            self._check_loop(node)
            self._detach(self.parent)
            self._attach(node)

    def add_child(self, node):
        """
        将指定的节点设为孩子节点。
        如果指定节点已有父节点，将首先把指定节点（及其子树）从原树中移除，
        再把指定节点（及其子树）接入新的树中。

        Args:
            node: 待设定的孩子节点
        """
        if not isinstance(node, NodeMixin):
            raise TreeError(f"子节点 {node!r} 不是 '{self.__class__.__name__}'.")

        if node not in self.children:
            node._check_loop(self)
            node._detach(node.parent)
            node._attach(self)

    def _check_loop(self, new_parent):
        if new_parent is None:
            return
        if new_parent is self:
            raise LoopError("父节点不能为自身.")
        if any(ancestor is self for ancestor in new_parent.iter_to_root()):
            raise LoopError(f"无法设置父节点. {self!r}已经是{new_parent!r}的祖先.")

    def _detach(self, parent):
        if parent is None:
            return

        try:
            parent.children.remove(self)
        except ValueError:
            raise TreeError("Tree is corrupt.")

    def _attach(self, new_parent):
        """将一棵树连接到父结点上"""
        if new_parent is None:
            return  # 不用做任何操作，因为parent默认就是None

        parentchildren = new_parent.children

        if any(child is self for child in parentchildren):
            raise TreeError("Tree is corrupt.")
        parentchildren.append(self)
        self.__parent = weakref.ref(new_parent)

    def iter_to_root(self):
        """从当前节点迭代至根节点，包括自身。返回生成器。"""
        node = self
        while node is not None:
            yield node
            node = node.parent

    def iter_descendants(self, include=False):
        """先序遍历所有后代节点，不包括自身。返回节点列表有顺序"""
        if include:
            yield self
        for child in self.children:
            if child is not None:
                yield from child.iter_descendants(include=True)

    def iter_from_root(self):
        """从根节点迭代至当前节点，包括自身。"""
        for node in reversed(list(self.iter_to_root())):
            yield node

    #: 祖先节点
    ancestors = property(lambda self: tuple(self.iter_to_root())[1:])
    #: 节点在树中的深度
    depth = property(lambda self: len(self.ancestors))
    #: tuple: 后代节点
    descendant = property(lambda self: list(self.iter_descendants()))
    #: tuple: 后代节点，包括自身
    idescendant = property(lambda self: list(self.iter_descendants(include=True)))

    #: 根节点
    root = property(lambda self: list(self.iter_to_root())[-1])

    def iter_base(self):
        """遍历当前子树的所有叶子节点"""
        for node in self.iter_descendants():
            if node.is_leaf:
                yield node

    #: 子树的所有叶子节点
    base = property(lambda self: list(self.iter_base()))

    @property
    def ibase(self):
        """子树的所有叶子节点，包含节点自身。"""
        return [self, *self.base]

    @property
    def siblings(self):
        """
        兄弟节点，不包含自身。

        Returns:
            tuple: 如有，返回所有兄弟节点；否则返回空元组

        """
        parent = self.parent
        if parent is None:
            return tuple()
        else:
            return tuple(node for node in parent.children if node is not self)

    #: 是否叶子节点
    is_leaf = property(lambda self: not bool(self.children))
    #: 是否根节点
    is_root = property(lambda self: self.parent is None)
    #: tuple: 同一颗树的所有节点
    family = property(lambda self: self.root.idescendant)

    def common_ancestor(self, *others):
        """
        获取当前节点与其他节点的最小共同祖先，包括其本身。

        Args:
            *others: 其他节点

        Returns:
            最小共同祖先

        """
        common = None

        for antr_me, *antr_others in zip(self.iter_from_root(),
                                         *map(methodcaller('iter_from_root'), others)):
            if all(antr is antr_me for antr in antr_others):
                common = antr_me
            else:
                break

        if common is None:
            raise TreeError(f"{self!r}和{others!r}不属于同一颗树")
        return common

    def iter_to_descendant(self, descendant):
        """
        遍历自身到后代节点所经过的所有节点，不包括自身。

        Args:
            descendant: 后代节点

        Raises:
            descendant不是自己或自己的后代时，抛出 `ValueError` 异常

        Note:
            传入 `descendant==self` 并不会引起错误，但也不会返回任何节点
        """
        found = False

        for antr in descendant.iter_from_root():
            if found:
                yield antr
            else:
                if antr is not self:
                    continue
                else:
                    found = True

        if found is False:
            raise ValueError(f"{descendant!r}不是{self!r}的后代")

    def iter_level(self, from_offset, to_offset, include=True):
        """
        返回与当前节点位置相对的节点，向上的节点只包括父节点，向下的节点以广度优先顺序遍历。

        Args:
            from_offset: 相对节点的开始位置
            to_offset: 相对节点的结束位置，包括结束点
            include: 是否包括自身节点

        """

        if to_offset < from_offset:
            raise ValueError("Stop level should be greater than start.")

        parent_list = []
        parent = self.parent
        search_up_cnt = from_offset

        while search_up_cnt < 0 and parent:
            parent_list.append(parent)
            parent = parent.parent
            search_up_cnt += 1

        parent_list = parent_list[from_offset - to_offset - 1:]

        if parent_list:
            for node in reversed(parent_list):
                yield node

        if include:
            yield self

        if to_offset < 0:
            return

        yield from bfs(self, depth=to_offset, include=False)


class ShareableNodeMixin(NodeMixin):
    _ref_shared_from = None

    def add_child(self, node):
        raise NotImplemented

    @property
    def children(self):
        """返回当前节点的直接孩子节点，不包含自身，当前节点无孩子则返回空列表"""
        if shared_from := self.shared_from:
            return shared_from.children
        else:
            return super().children

    @property
    def shared_by(self):
        """父节点"""
        try:
            return self.__shared_by
        except AttributeError:
            self.__shared_by = []
            return self.__shared_by

    @property
    def is_shared(self):
        return bool(self.shared_by)

    @property
    def shared_from(self):
        if self._ref_shared_from:
            return self._ref_shared_from()
        else:
            return None

    def add_shared(self, node):
        self.shared_by.append(node)
        node._ref_shared_from = weakref.ref(self)

    @property
    def parent(self):
        """父节点"""
        try:
            if parent := self.__parent:
                return [p() for p in parent]
            else:
                return None
        except AttributeError:
            self.__parent = []  # noqa
            return None

    def set_parent(self, node, check_loop: bool = False):
        if node is not None and not isinstance(node, NodeMixin):
            raise TreeError(f"父节点 {node!r} 不是 '{self.__class__.__name__}'.")

        parent = self.parent

        if node is None:
            if parent is None:
                return

            for p in self.parent:
                p.children.remove(self)
            self.parent.clear()

        else:
            if check_loop:
                self._check_loop(node)
            self._attach(node)

    def _attach(self, new_parent):
        """将一棵树连接到父结点上"""
        parentchildren = new_parent.children

        if any(child is self for child in parentchildren):
            return
        parentchildren.append(self)
        self.__parent.append(weakref.ref(new_parent))

    def iter_to_root(self, exclude=None):
        """从当前节点迭代至根节点，包括自身。返回生成器。"""
        exclude = exclude or set()
        yield self
        exclude.add(self)
        for p in self.parent or []:
            yield from p.iter_to_root(exclude)

    @property
    def siblings(self):
        sib = set()
        for parent in self.parent or []:
            if parent is not None:
                sib.update(node for node in parent.children if node is not self)
        return tuple(sib)


def bfs(node, depth=-1, include=True):
    """
    广度优先遍历树

    Args:
        node(NodeMixin): 遍历以 ``node`` 为根节点的维度树
        depth(int): 遍历的深度
        include(bool): 是或否包含自身

    Returns:
        返回生成器，包含遍历到的所有节点
    """
    if depth == 0:
        return
    elif depth > 0:
        depth += node.depth + 1

    if include:
        yield node

    node_to_visit = node.children[:]

    while node_to_visit:
        child = node_to_visit.pop(0)
        if child.depth == depth:
            break

        yield child

        for grandchild in child.children:
            node_to_visit.append(grandchild)


class TreeRenderer:
    """渲染树形结构"""
    def __init__(self):
        self.blank = '    '
        self.low = '└── '
        self.mid = '├── '
        self.gap = '|   '
        self.len = len(self.blank)

    def iter_line(self, root, sty='', fill=''):
        yield fill[:-self.len] + sty * (len(fill) > 0) + str(root)

        child_num = len(root.children)
        for idx, child in enumerate(root.children, 1):
            if idx == child_num:
                yield from self.iter_line(child, sty=self.low, fill=fill + self.blank)
            else:
                yield from self.iter_line(child, sty=self.mid, fill=fill + self.gap)

    def render(self, root) -> str:
        """
        渲染树结构

        Args:
            root(NodeMixin): 树的根节点

        Examples:
            .. code-block:: python

                # dim.root 为需要打印的维度树的根节点
                print(TreeRenderer().render(dim.root))
                # 经过上述定义后，将形成如下树结构
                '''
                #root
                └── TotalPeriod
                    └── Q1
                        ├── 1
                        ├── 2
                        └── 3
                '''
        """
        if isinstance(root, (NodeMixin, MetaNodeMixin)):
            return '\n'.join(self.iter_line(root))
        else:
            raise TypeError(f'{root.__class__.__name__}不是NodeMixin或MetaNodeMixin')

    def show(self, root):
        """打印树结构"""
        print(self.render(root))
