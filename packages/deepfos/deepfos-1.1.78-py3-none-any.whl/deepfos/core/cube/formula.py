import copy
import operator
import functools
import weakref
from collections import defaultdict, UserList
from contextlib import contextmanager
from typing import List, Dict, Tuple, Iterable, Union, Callable, TYPE_CHECKING

import numpy as np

from .constants import OPMAP, Instruction
from .typing import TD_Str_ListStr, TD_Str_Str, T_MaybeCondition
from .utils import AutoFillSeries
from deepfos.core.logictable.nodemixin import NodeMixin
from deepfos.core.dimension.sysdimension import unpack_expr
from deepfos.lib.decorator import cached_property
from deepfos.lib.utils import dict_to_expr
from loguru import logger


# -----------------------------------------------------------------------------
# constant

K_MEMBER = 'mbr'
K_EXPR = 'expr'


# -----------------------------------------------------------------------------
# Base Classes
class ValNode(NodeMixin):
    """变量节点"""
    def __init__(self, value):
        self.value = value

    def prepare(self):
        pass

    @property
    def fix_mbrs(self) -> List[TD_Str_ListStr]:
        """节点的锁定信息，以 维度名：维度成员列表 格式储存"""
        return []

    @property
    def fix_exprs(self) -> List[TD_Str_Str]:
        """节点的锁定信息，以 维度名：维度表达式 格式储存"""
        return []

    def __str__(self):
        return str(self.value)


class OpNode(NodeMixin):
    """运算符节点"""
    def __init__(self, op):
        self.op = op

    def __str__(self):
        return self.op

    def solve(self):
        args = []
        for child in self.children:
            if isinstance(child, ValNode):
                args.append(child.value)
            elif isinstance(child, self.__class__):
                args.append(child.solve())
            else:
                raise TypeError(f"Expect type {self.__class__} or {ValNode}, got {type(child)}")
        return self.calc(*args)

    def calc(self, left, right):
        op = getattr(operator, self.op, None)
        if op is None:
            raise ValueError(f"Unknown operator: {self.op}.")

        return op(left, right)

    def get_formula(self):
        args = []

        for child in self.children:
            if isinstance(child, ValNode):
                args.append(str(child))
            elif isinstance(child, self.__class__):
                args.append(child.get_formula())
            else:
                raise TypeError(f"Expect type {self.__class__} or {ValNode}, got {type(child)}")
        op_repr = f" {OPMAP.get(self.op, self.op)} "
        return "(" + op_repr.join(args) + ")"


class CalcUnit:
    """计算单元"""
    def __init__(self, op_cls=OpNode):
        self._op_cls = op_cls
        self.root = None

    @cached_property
    def as_node(self) -> ValNode:
        return NotImplemented

    def _validate(self, other):
        pass

    def _attach(self, other, new_root, reverse=False):
        if isinstance(other, CalcUnit):
            self._validate(other)
            val_node = other.root or other.as_node
        else:
            val_node = ValNode(other)

        if reverse:
            val_node.set_parent(new_root)

        if self.root is None:
            self.as_node.set_parent(new_root)
        else:
            self.root.set_parent(new_root)

        if not reverse:
            val_node.set_parent(new_root)

        self.root = new_root
        return self

    def __add__(self, other):
        return self._attach(other, self._op_cls('add'))

    def __sub__(self, other):
        return self._attach(other, self._op_cls('sub'))

    def __mul__(self, other):
        return self._attach(other, self._op_cls('mul'))

    def __truediv__(self, other):
        return self._attach(other, self._op_cls('truediv'))

    def __mod__(self, other):
        return self._attach(other, self._op_cls('mod'))

    def __pow__(self, other):
        return self._attach(other, self._op_cls('pow'))

    def __floordiv__(self, other):
        return self._attach(other, self._op_cls('floordiv'))

    def __radd__(self, other):
        return self._attach(other, self._op_cls('add'), True)

    def __rsub__(self, other):
        return self._attach(other, self._op_cls('sub'), True)

    def __rmul__(self, other):
        return self._attach(other, self._op_cls('mul'), True)

    def __rtruediv__(self, other):
        return self._attach(other, self._op_cls('truediv'), True)

    def __rmod__(self, other):
        return self._attach(other, self._op_cls('mod'), True)

    def __rpow__(self, other):
        return self._attach(other, self._op_cls('pow'), True)

    def __rfloordiv__(self, other):
        return self._attach(other, self._op_cls('floordiv'), True)

    def __str__(self):
        if self.root is None:
            return str(self.as_node)
        return self.root.get_formula()

    def iter_node(self):
        if self.root is None:
            node = self.as_node
            if isinstance(node, ValNode):
                yield node
        else:
            for node in self.root.iter_descendants():
                if isinstance(node, ValNode):
                    yield node

    def _node_init(self):
        # 初始化所有计算节点，获取参与计算的数据集
        for node in self.iter_node():
            node.prepare()

    def solve(self):
        self._node_init()
        if self.root is None:
            # 只有一个赋值语句，没有计算
            return self.as_node.value
        return self.root.solve()


# -----------------------------------------------------------------------------
# Cube Nodes
class MemberNode(ValNode):
    """
    根据第一个入参的不同，存在两种行为。
    1. 如果是一般实数，value即实数值，prepare将无行为
    2. 其他情况，prepare将根据fix条件对DataFrame作必要预处理。获取可以参与计算的数据列。
    """

    # noinspection PyMissingConstructor
    def __init__(
        self,
        cube,
        indicator: str = None,
        hook: Callable = None,
        fix_mbrs: TD_Str_ListStr = None,
        fix_exprs: TD_Str_Str = None,
        calc_dim: str = None,
        calc_mbr: str = None,
    ):
        self.hook = hook
        self.indicator = indicator
        self._cube = cube
        self._fix_mbrs = fix_mbrs or {}
        self._fix_exprs = fix_exprs or {}
        self._calc_dim = calc_dim
        self._calc_mbr = calc_mbr

    @property
    def fix_mbrs(self) -> List[TD_Str_ListStr]:
        """
        来自计算节点 `CubeCalcUnit` 的 :attr: `_extra_fix`
        包括计算维度（如Account['Price']）和on条件。
        """
        return [self._fix_mbrs]

    @cached_property
    def on(self) -> TD_Str_ListStr:
        fix_mbrs = {**self._fix_mbrs}
        fix_mbrs.pop(self._calc_dim, None)
        return fix_mbrs

    @property
    def fix_exprs(self) -> List[TD_Str_Str]:
        """
        类似于 :attr:`fix_mbrs`
        """
        return [self._fix_exprs]

    def _pass(self):
        pass

    def prepare(self):
        self._cube.calc_set.load_fixes(
            self._calc_mbr, self._calc_dim,
            self.on, str(self)
        )

    @property
    def value(self):
        column = str(self) if self.on else self._calc_mbr
        data_src = self._cube.calc_set.data_proxy

        if column not in data_src.columns:
            value = AutoFillSeries(np.full(len(data_src), np.NAN))
        else:
            value = AutoFillSeries(data_src[column])

        value.custom_options = self._cube.option_stack[0]  # noqa

        if self.hook is not None:
            value = self.hook(value)

        return value

    def __str__(self):
        return self.indicator


class FunctionNode(ValNode):
    def __init__(self, func, *args, **kwargs):
        super().__init__(None)
        self.func = func
        self._args = args
        self._kwargs = kwargs

    @property
    def fix_mbrs(self) -> List[TD_Str_ListStr]:
        return sum((node.fix_mbrs for node in self._iter_arg_node()), [])

    @property
    def fix_exprs(self) -> List[TD_Str_Str]:
        return sum((node.fix_exprs for node in self._iter_arg_node()), [])

    @staticmethod
    def _resolve_node(arg):
        if isinstance(arg, CalcUnit):
            node = arg.as_node
            if isinstance(node, ValNode):
                node.prepare()
            return node.value
        else:
            return arg

    def prepare(self):
        """
        1. 对参数中所有计算节点进行初始化；
        2. 获取所有参数并且进行对齐；
        3. 替换对齐后的参数，调用函数；
        4. 将返回结果包装为 CubeVariable，赋值至value
        """

        args = list(self._args)
        kwargs = {**self._kwargs}

        for idx, arg in enumerate(args):
            args[idx] = self._resolve_node(arg)

        for key, val in self._kwargs.items():
            kwargs[key] = self._resolve_node(val)

        self.value = self.func(*args, **kwargs)

    def _iter_arg_node(self) -> Iterable[ValNode]:
        """遍历包含在函数参数内的所有节点"""
        for item in self._args:
            if isinstance(item, CalcUnit):
                yield from item.iter_node()

        for item in self._kwargs.values():
            if isinstance(item, CalcUnit):
                yield from item.iter_node()

    def __str__(self):
        sig = list(map(str, self._args))
        for k, v in self._kwargs.items():
            sig.append(f"{k}={str(v)}")

        return f"{self.func.__name__}({', '.join(sig)})"


def as_function_node(func):
    """
    装饰器，将普通函数作为函数节点使用。
    用于cube多维计算。

    Args:
        func:

    Returns:

    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return FuncCalcUnit(func=func, args=args, kwargs=kwargs)
    return wrapper


# -----------------------------------------------------------------------------
# Formula elements
def _get_calc_dim(expr: str, cube) -> Tuple[str, str]:
    dim, member = unpack_expr(expr, silent=True)
    if dim is not None:
        return dim, member

    if not cube.calc_dim:
        raise ValueError(f"Cannot resolve dimension from expr: {expr}.")

    dim = cube.calc_dim[-1]
    return dim, member


class ValueCalcUnit(CalcUnit):
    if TYPE_CHECKING:
        from .cube import CubeBase
        _cube: CubeBase

    """
    记录计算逻辑，以及各个计算单元的限定条件。
    支持各种四则运算符，但是不立即触发计算。

    会将所有参与计算的成员包装成CubeValNode, CubeFunctionNode等对象的节点。

    当调用solve方法时，会调用所有节点的prepare方法，再求解所有算式。
    """
    def __init__(self, cube, calc_mbr: str):
        super().__init__()
        self.pre_hook = None
        self.post_hook = None
        self.calc_dim, self.calc_mbr = _get_calc_dim(calc_mbr, cube)
        self._cube = cube
        self._extra_fix = {self.calc_dim: [self.calc_mbr]}
        self._fix_str_memo = {self.calc_dim: self.calc_mbr}

    def on(self, **dim_mbr_map: Union[str, int, float]):
        for dimension, member in self._validate_dims(dim_mbr_map).items():
            member = str(member)
            self._extra_fix[dimension] = [member]
            self._fix_str_memo[dimension] = member
        return self

    def _to_expr(self):
        return '->'.join(f"{k}{{{v}}}" for k, v in self._fix_str_memo.items())

    def _validate_dims(self, kwargs):
        rtn = {
            k: v for k, v in kwargs.items()
            if k in self._cube.dimensions}

        filtered = kwargs.keys() - rtn.keys()
        if filtered:
            raise ValueError(f"Dimensions : {filtered} does not belong to cube.")
        return rtn

    def set_hook(self, func: Callable, at: str):
        if not callable(func):
            raise TypeError(f"Argument must be callable.")
        at = at.lower()
        if at == 'pre':
            self.pre_hook = func
        elif at == 'post':
            self.post_hook = func
        return self

    @cached_property
    def as_node(self):
        return MemberNode(
            self._cube,
            indicator=self._to_expr(),
            hook=self.pre_hook,
            fix_mbrs=self._extra_fix,
            fix_exprs=self._fix_str_memo,
            calc_dim=self.calc_dim,
            calc_mbr=self.calc_mbr
        )


class FuncCalcUnit(CalcUnit):
    def __init__(self, func, args, kwargs):
        super().__init__()
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._func = func

    @cached_property
    def as_node(self):
        return FunctionNode(
            self._func,
            *self._args,
            **self._kwargs
        )


class CubeFixer:
    def __init__(self, cube_obj):
        self._cube = cube_obj

    def __getitem__(self, item: str) -> ValueCalcUnit:
        """
        cube.fix as 的返回对象在等式右边会调用此方法。
        方法返回计算单元，计算单元将记录维度锁定条件以及
        计算顺序。

        Args:
            item: 维度名或者 **单成员的维度表达式**

        Returns:
            值类型计算单元

        """
        return ValueCalcUnit(cube=self._cube, calc_mbr=item)

    def __setitem__(self, key, value):
        dim, member = _get_calc_dim(key, self._cube)
        self._cube.formulas.append((dim, member, value))


# -----------------------------------------------------------------------------
# Fomular Solver
class _Condition:
    ENDIF = object()

    def __init__(self, cond: T_MaybeCondition, flag):
        self.cond = cond
        self.flag = flag
        self.filter = None
        self._install_filter(cond)

    def parse_str_cond(self, dataframe):
        query_set = dataframe.query(self.cond)
        if self.flag is True:
            return query_set
        else:
            return dataframe.loc[dataframe.index.difference(query_set.index)]

    def parse_callable_cond(self, dataframe):
        query_set = self.cond(dataframe)
        if self.flag is True:
            return query_set
        else:
            return dataframe.loc[dataframe.index.difference(query_set.index)]

    def _install_filter(self, cond):
        if isinstance(cond, str):
            self.filter = self.parse_str_cond
        elif callable(cond):
            self.filter = self.parse_callable_cond

    def __str__(self):
        return str(self.cond)


class FormulaContainer(UserList):
    def __init__(self, cube, initlist=None):
        super().__init__(initlist)
        self.cube = weakref.ref(cube)
        #: 公式左边出现的维度->维度成员集合
        self.left = defaultdict(set)
        self.fix_by_mbrs: List[TD_Str_ListStr] = []
        self._fix_by_expr: List[TD_Str_ListStr] = []
        self.__left_fix_memo: Dict[str, Dict[str, TD_Str_ListStr]] = {}

    @property
    def query_expr_list(self) -> List[str]:
        """cube维度查询公式的列表"""
        return [dict_to_expr(item) for item in self._fix_by_expr]

    def _iter_with_filter(self):
        calc_set = self.cube().calc_set

        for item in self.data:
            if isinstance(item, _Condition):
                calc_set.add_filter(item)
            elif item is _Condition.ENDIF:
                calc_set.pop_filter()
            elif isinstance(item, Instruction):
                calc_set.add_instruction(item)
            elif callable(item):  # callbacks per line
                item()
            else:
                yield item

    @property
    def _cube_dim_exprs(self) -> TD_Str_ListStr:
        """返回cube.fix中general_fix的结果。"""
        return {
            dimname: [dim.expr_body]
            for dimname, dim in self.cube().dimensions.items()
            if dim.activated
        }

    def append(self, item) -> None:
        if isinstance(item, Tuple):
            calc_dim, calc_mbr, right = item
            general_mbr_fix = self.cube().dim_state
            general_expr_fix = self._cube_dim_exprs
            if isinstance(right, CalcUnit):
                self._handle_calc_unit(
                    calc_dim,
                    calc_mbr,
                    general_expr_fix,
                    general_mbr_fix,
                    right
                )

            self.left[calc_dim].add(calc_mbr)

        return self.data.append(item)

    def _handle_calc_unit(
        self,
        calc_dim: str,
        calc_mbr: str,
        general_expr_fix: TD_Str_ListStr,
        general_mbr_fix: TD_Str_ListStr,
        calc_unit: CalcUnit
    ):
        """
        根据当前提交的计算公式，整合成维度成员的查询表达式，
        原则上生成的维度表达式数量应该尽可能少。
        最终的维度表达式存放在 :attr:`query_expr_list` 中。
        """

        for node in calc_unit.iter_node():
            if len(node.fix_exprs) != len(node.fix_exprs):
                raise RuntimeError("Formula is corrupted.")

            for fix_mbrs, fix_expr in zip(node.fix_mbrs, node.fix_exprs):
                if not fix_mbrs:
                    continue
                if calc_dim not in fix_mbrs:
                    raise ValueError(
                        "Dimension to calculate is not consistent. "
                        f"Expect '{calc_dim}' in right-side expression. "
                        f"Got '{list(fix_mbrs.keys())}'.")

                node_mbr = fix_expr[calc_dim]

                if node_mbr in self.left.get(calc_dim, []):
                    # 对于已经在等式左边出现的，即使在右边出现也不需要查询
                    continue

                if len(fix_mbrs) == 1:
                    # 仅一个条件则表示没有使用过on, 可以并入到公式左边的计算成员
                    if calc_dim not in self.__left_fix_memo:
                        self.__left_fix_memo[calc_dim] = fix_memo = {}
                        fix_memo[K_MEMBER] = mbr_memo = copy.deepcopy(general_mbr_fix)
                        fix_memo[K_EXPR] = expr_memo = copy.deepcopy(general_expr_fix)
                        mbr_memo[calc_dim] = []
                        expr_memo[calc_dim] = []
                        self.fix_by_mbrs.append(mbr_memo)
                        self._fix_by_expr.append(expr_memo)
                    else:
                        mbr_memo = self.__left_fix_memo[calc_dim][K_MEMBER]
                        expr_memo = self.__left_fix_memo[calc_dim][K_EXPR]
                    mbr_memo[calc_dim].extend(fix_mbrs[calc_dim])
                    expr_memo[calc_dim].append(fix_expr[calc_dim])
                else:
                    # 使用过on, 需要创建全新的fix条件
                    new_mbr_fix = copy.deepcopy(general_mbr_fix)
                    for k, v in fix_mbrs.items():
                        new_mbr_fix[k] = v
                    self.fix_by_mbrs.append(new_mbr_fix)

                    new_expr_fix = copy.deepcopy(general_expr_fix)
                    for k, v in fix_expr.items():
                        new_expr_fix[k] = [v]
                    self._fix_by_expr.append(new_expr_fix)

    def _assign(self):
        calc_set = self.cube().calc_set
        last_calc_dim = None

        for calc_dim, mbr, right in self._iter_with_filter():
            logger.debug(f"Start calculation: {calc_dim}{{{mbr}}}={right}")

            if last_calc_dim is None:
                calc_set.pivot(calc_dim)
            elif last_calc_dim != calc_dim:
                calc_set.unpivot(last_calc_dim)
                calc_set.pivot(calc_dim)

            last_calc_dim = calc_dim

            if isinstance(right, CalcUnit):
                value = right.solve()
                post_hook = getattr(right, 'post_hook', None)
            else:
                value = right
                post_hook = None

            if post_hook:
                value = post_hook(value)

            calc_set.set_value(mbr, value)

        if last_calc_dim is not None:
            calc_set.unpivot(last_calc_dim)

    def solve(self):
        """
        成员公式求解

        在进行计算前，会根据所有等式的fix条件查询出本次计算可能涉及的数据，
        以下称为“计算集”.计算集会绑定至Cube对象，并且作为所有计算节点初始化的数据源。

        对于每一个等式，计算分为两步：

        1. 调用所有计算节点的prepare方法，该方法会根据fix条件装载需要参与
            计算的 :class:`Series`，并且返回，
        2.  :class:`Series` 进行运算，并且将运算结果赋值回计算集，
            以确保前面的计算结果可以正确影响后续计算。
        """
        # noinspection PyProtectedMember
        self.cube()._load_calc_set(
            self.query_expr_list,
            self.fix_by_mbrs
        )
        self._assign()
        self.clear()

    def clear(self) -> None:
        """删除公式列表中所有数据及状态"""
        self.data.clear()
        self.left.clear()
        self.fix_by_mbrs.clear()
        self._fix_by_expr.clear()
        self.__left_fix_memo.clear()


class _ConditionWrapper:
    def __init__(
        self,
        formula: FormulaContainer,
        condition: T_MaybeCondition
    ):
        self.condition = condition
        self.formulas = formula

    @property
    @contextmanager
    def true(self):
        self.formulas.append(_Condition(self.condition, True))
        yield
        self.formulas.append(_Condition.ENDIF)

    @property
    @contextmanager
    def false(self):
        self.formulas.append(_Condition(self.condition, False))
        yield
        self.formulas.append(_Condition.ENDIF)
