import functools
from abc import ABC, abstractmethod
from collections.abc import Iterable
from contextlib import contextmanager
from operator import attrgetter
from typing import List
from deepfos.lib.constant import SHAREDMEMBER
from .filters import *
from .dimexpr import DimExprAnalysor

filter_map = {
    "or": OrFilter,
    "and": AndFilter,
    "nor": NorFilter,
    "nand": NAndFilter,
}

NAME_DFLT = "name"
PNAME_DFLT = "parent_name"
IS_SHARED_DFLT = SHAREDMEMBER


def pack_filter(member_expr, filters):
    """给维度表达式增加 ``Attr`` ， ``Remove`` ，以及各种 ``Filter`` """
    if not filters:
        return member_expr

    rtn = member_expr
    for fltr in filters:
        if isinstance(fltr, BaseFilter):
            attr_conds = (f"Attr({k},{v!r})" for k, v in fltr.attr_kv_pairs.items())
            rtn = f"{fltr}({rtn},{','.join(attr_conds)})"
        else:
            rtn = f"{fltr}({rtn},{','.join(map(str, fltr.to_remove))})"

    return rtn


def flatten(nested_list):
    """
    展开多级列表

    Args:
        nested_list: 多级列表

    Returns:
        只含简单元素的列表

    """
    rtn = []
    for item in nested_list:
        if isinstance(item, list):
            rtn.extend(flatten(item))
        else:
            rtn.append(item)
    return rtn


class AbstractMember(ABC):
    @abstractmethod
    def members(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    def contribute(self, value):
        weight = getattr(self, 'weight', 1)
        if not weight:
            weight = 1
        return value * float(weight)

    def calculate(self, **args):
        return sum(args.values())


class MemberBase(AbstractMember):
    def __init__(self, name):
        self.name = name

    @property
    def members(self):
        """
        由 `DimMember`` 继承，返回只包含节点自身列表
        """
        return [self]

    def __str__(self):
        return self.name


class MemberContainer(AbstractMember):
    """维度成员容器，成员容器旨在一次性使用。"""
    def __init__(self, *anchor_mbrs, hierarchy=None):
        self.anchor_mbrs = list(anchor_mbrs)
        # self.anchor_mbrs = anchor_mbr if isinstance(anchor_mbr, list) else [anchor_mbr]
        self.hierarchy = hierarchy
        self._reversed = False
        self._filters = []

    def _get_all_member(self):
        """返回容器中的所有维度成员，如果维度成员含有层级，则以层级结果代替原维度成员。"""
        if self.hierarchy is None:
            return self.anchor_mbrs

    @property
    def members(self):
        """
        返回容器中所有维度成员， ``reverse`` 设置返回顺序， 默认正序。
        如果有过滤操作，则先执行过滤，再返回结果。
        """
        reverse_flag = -1 if self._reversed else 1
        return self.apply_filter(self._get_all_member()[::reverse_flag])

    @property
    def data(self):
        """返回容器中所有维度成员的维度成员名。"""
        return [member.name for member in self.members]

    def apply_filter(self, total):
        """
        执行过滤器列表中所有过滤器。

        Args:
            total(list): 需要过滤的所有维度成员

        Returns:
            符合过滤条件的维度成员列表，存储在 ``selected`` 中。

        """
        remain = total
        for fltr in self._filters:
            remain = fltr.apply_to(remain)
        return remain

    def reverse(self):
        """逆序输出维度成员。"""
        self._reversed = True
        return self

    def __getitem__(self, item):
        """
        正序或逆序输出容器中的维度成员。

        Examples:
            literal blocks::
                ``MemberContainer``[::1]

                ``MemberContainer``[1:3:1]

        Warnings:
            只支持正序或者逆序输出全部维度成员，不支持只输出切片的部分成员。
            上面两个例子的效果相同。

        """
        if not isinstance(item, slice):
            raise TypeError("Only slice type is supported")
        if item.step == -1:
            self._reversed = True
        return self

    def __str__(self):
        """
        显示当前维度成员集对应的维度表达式。

        Warning:
            调用的 ``pack_filter`` 中会调用 ``str`` 方法，因此这里有递归。

        """
        order = 1 if self._reversed else 0

        total_expr = []
        for mbr in self.anchor_mbrs:
            if self.hierarchy is None:
                expr = str(mbr)
            else:
                expr = f"{self.hierarchy}({mbr},{order})"
            total_expr.append(pack_filter(expr, self._filters))
        return ';'.join(total_expr)

    def where(self, method, **kwargs):
        """
        筛选维度成员。

        Args:
            method(str): 筛选维度成员的方法，共有 ``and`` ， ``nand`` ， ``or`` ， ``nor`` 四种
            **kwargs(dict): 筛选条件

        Notes:
            不返回结果，只有在显示容器中的维度成员时，才会执行所有过滤器，获得结果。

        Raises:
            ValueError: ``method`` 不在于四种方法中或者筛选条件 ``**kwargs`` 为空。

        """
        filter_cls = filter_map.get(method.lower())

        if filter_cls is None:
            raise ValueError(f"Unsupported method: {method}.")

        if not kwargs:
            raise ValueError("Filter condition should not be empty.")

        self._filters.append(filter_cls(kwargs))
        return self

    def remove(self, *to_remove: AbstractMember):
        """
        从已选择的维度成员中移除维度成员。

        Args:
            *to_remove(DimMember): 需要从维度成员容器中移除的维度成员

        Notes:
            不返回任何结果，只将过滤器加入到过滤器列表中。

        """
        to_remove = _as_abstract_member(to_remove)
        self._filters.append(RemoveFilter(to_remove, attrgetter('members')))
        return self

    @property
    def attr(self):
        """
        属性映射，返回容器中维度成员对应的属性值，
        属性为多个时，对每个维度成员都进行指定属性的返回。
        """
        return AttrMapper(self.members)


def finalize(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        for idx, obj in enumerate(self.selected):
            if isinstance(obj, Puppet):
                self.selected[idx] = obj.puppet_apply()
        return func(self, *args, **kwargs)
    return wrapper


class DimensionBase:
    """维度基类"""
    def __init__(self, dim_name=None):
        self.name = dim_name
        self.selected = []

    def select(self, *dim_members: AbstractMember):
        """选择维度成员

        Args:
            *dim_members: 需要加入到 ``selected`` 中的维度成员

        Returns:
            不返回任何结果，只改变 ``selected`` 中的维度成员

        Raises:
            ValueError: 加入的维度成员 ``dim_members`` 为空
        """
        if not dim_members:
            raise ValueError("No dimension member to select.")

        self.selected = _as_abstract_member(dim_members)
        return self

    def to_expr(self):
        """输出维度表达式

        获取当前查询集下，等价的维度表达式

        Example:
            .. code-block:: python

                # 向 selected 集中添加维度成员
                dim.select(dim['Q1', 'Q2', 'Q3', 'Q4'])
                print(dim.to_expr())
                # 设维度树名为Dimension，则对应的维度表达式如下所示：
                '''
                Dimension{Q1;Q2;Q3;Q4}
                '''

        """
        return f"{self.name}{{{self.expr_body}}}"

    @property
    @finalize
    def expr_body(self) -> str:
        """维度表达式花括号内的部分"""
        return ';'.join(map(str, self.selected))

    @property
    @finalize
    def members(self):
        """获取当前查询集下，所有维度成员对象"""
        return sum((member.members for member in self.selected), [])

    @property
    def data(self) -> List[str]:
        """获取当前查询集下，所有维度成员名"""
        return [member.name for member in self.members]

    @property
    def activated(self):
        """维度是否激活，等价于是否选择了维度成员"""
        return len(self.selected) > 0

    @property
    def loc(self):
        """单次选择维度成员，在清空 ``selected`` 集后加入"""
        return Locator(self)

    @property
    def exloc(self):
        """单次选择维度成员，增量加入到 ``selected`` 集"""
        return Locator(self, append=True)

    def __getitem__(self, item):
        raise NotImplementedError()

    @contextmanager
    def multi_loc(self, do_remove=False):
        """在上下文中多次选择维度成员"""
        self.selected = []
        if do_remove:
            yield Locator(self, append=True), Remover(self)
        else:
            yield Locator(self, append=True)

    def load_expr(self, expr) -> 'DimensionBase':
        """
        加载维度表达式

        Args:
            expr(str): 维度表达式

        Returns:
            不返回任何结果，改变查询集

        Notes:
            维度表达式中的维度成员不需要带引号，使用 ``filter`` 时不能直接使用字典形式的键值对，
            而是使用 ``Attr`` 获取属性作为键，而后跟上值，在传入的时候，会以字典的形式传入，
            此时将传入的多参数转变成键值字典，所有调用的属性或者函数必须首字母大写。

        Examples:
            较为复杂的唯独表达式例，其中 ``uds`` 为额外属性， ``value`` 为指定的属性值：

            .. code-block:: python

                dim.load_expr("AndFilter(Base(#root, 0), Attr(uds, value))")

        """
        return DimExprAnalysor(self, expr).solve()

    @contextmanager
    def load_expr_temporary(self, expr):
        """一次性加载维度表达式，存储结果"""
        selected_bak = self.selected[:]
        try:
            self.load_expr(expr)
            yield
        finally:
            self.selected = selected_bak

    @property
    def attr(self):
        """属性映射

        返回查询集中维度成员对应的属性值，
        属性为多个时，对每个维度成员都进行指定属性的返回
        """
        return AttrMapper(self.members)

    @finalize
    def classify_selected(self):
        """分类查询集

        将查询集按照 ``DimMember`` 类型和 ``MemberContainer`` 类型分成两类。

        Returns:
             ``DimMember`` 类型的对象列表和 ``MemberContainer`` 类型的对象列表

        """
        members = []
        mbr_containers = []

        for mbr in self.selected:
            if isinstance(mbr, MemberBase):
                members.append(mbr)
            elif isinstance(mbr, MemberContainer):
                mbr_containers.append(mbr)
        return members, mbr_containers

    def clear(self):
        self.selected.clear()


class ATTR:
    __slots__ = ('attr', 'callable', 'args', 'kwargs')

    def __init__(self, attr):
        self.attr = attr
        self.callable = False
        self.args = None
        self.kwargs = None


class Puppet:
    """
    链式调用代理

    Examples:
        简单的代理，此时不执行操作：
        literal blocks::
            dim.loc('Q1').iter_to_root()

    """
    def __init__(self, bound):
        """bound的类型时DimMember"""
        self.__bound = bound
        self.__stack = []

    def __getattr__(self, item):
        """成员属性"""
        self.__stack.append(ATTR(item))
        return self

    def __call__(self, *args, **kwargs):
        """成员方法"""
        last_attr = self.__stack[-1]
        last_attr.callable = True
        last_attr.args = args
        last_attr.kwargs = kwargs

    def puppet_apply(self):
        rslt = self.__bound
        for attr in self.__stack:
            if attr.callable:
                rslt = getattr(rslt, attr.attr)(*attr.args, **attr.kwargs)
            else:
                rslt = getattr(rslt, attr.attr)
        return rslt


class Locator:
    """选择维度成员加入 ``selected`` 集合中"""
    def __init__(self, dim_obj: DimensionBase, append=False):
        """
        Args:
            dim_obj: 维度树
            append: 选择增量还是全量，增量则会在原基础上加入，全量则清除后加入

        Warnings:
            默认将当前selected集合中的维度成员加入
        """
        self._append = append
        self._obj = dim_obj
        self._puppets = dim_obj.selected

    def __call__(self, *items):
        """items为维度成员名"""
        if len(items) == 1:
            item = items[0]
        else:
            item = items
        puppet = Puppet(self._obj[item])
        if not self._append:
            self._puppets.clear()
        self._puppets.append(puppet)
        return puppet


class Remover:
    def __init__(self, dim_obj: DimensionBase):
        self._obj = dim_obj

    def __call__(self, *items):
        if len(items) == 1:
            item = items[0]
        else:
            item = items
        puppet = Puppet(self._obj[item])
        return puppet


class AttrMapper:
    """属性映射"""
    def __init__(self, obj_itor):
        self._obj_itor = obj_itor

    def __getitem__(self, item):
        if isinstance(item, str):
            return [getattr(obj, item) for obj in self._obj_itor]

        elif isinstance(item, Iterable):
            return [self[it] for it in item]


def _as_abstract_member(members) -> List[AbstractMember]:
    rtn = []
    for mbr in members:
        if isinstance(mbr, Puppet):
            mbr = mbr.puppet_apply()
        if not isinstance(mbr, AbstractMember):
            raise TypeError(f"Expect type: {AbstractMember}, got {type(mbr)}.")
        rtn.append(mbr)
    return rtn
