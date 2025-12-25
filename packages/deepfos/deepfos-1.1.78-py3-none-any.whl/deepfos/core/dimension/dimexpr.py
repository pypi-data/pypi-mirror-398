import re
from deepfos.core.logictable.nodemixin import NodeMixin, TreeRenderer
from deepfos.lib.decorator import cached_property

_RE_ESCAPE_QUOTE = re.compile("^'(?P<body>.*)'")
_RE_ESCAPE_DQUOTE = re.compile('^"(?P<body>.*)"')


class ASTNode(NodeMixin):
    def __init__(self, value: str):
        self.value = value
        self.is_quoted = False

    def __str__(self):
        return self.value

    @cached_property
    def eval(self):
        """解析维度表达式，如果为数字，直接返回，否则提取维度操作返回"""
        val = self.value
        if val.isdigit():
            return int(val)
        for patt in (_RE_ESCAPE_QUOTE, _RE_ESCAPE_DQUOTE):
            rslt = patt.match(val)
            if rslt is not None:
                self.is_quoted = True
                return rslt.group('body')

        return self.value


class ASTOpBase(NodeMixin):
    """维度表达式语法树中的维度操作节点"""
    def __init__(self, dim_obj, op_name):
        """
        Args:
            dim_obj(Dimension): 维度表达式操作的维度树
            op_name: 维度操作名
        """
        self._op_name = op_name
        self._dim_obj = dim_obj

    def solve(self):
        """执行该节点的维度操作"""
        args = self.collect_args()
        return self.calc(args)

    def calc(self, args):
        raise NotImplementedError()

    def eval(self, node: ASTNode):
        return node.eval

    def collect_args(self):
        """收集维度操作所需的参数"""
        args = []
        for child in self.children:
            if isinstance(child, ASTNode):
                args.append(self.eval(child))
            elif isinstance(child, ASTOpBase):
                args.append(child.solve())
            else:
                raise TypeError(f"Expect type {ASTOpBase} or {ASTNode}, got {type(child)}")

        return args

    def _get_member(self, mbr):
        """获取语法树中指定节点"""
        if isinstance(mbr, str):
            return self._dim_obj[mbr]
        if isinstance(mbr, int):
            return self._dim_obj[str(mbr)]
        return mbr

    def __str__(self):
        """直接打印当前维度操作节点的操作名"""
        return self._op_name


class ASTOpHierachy(ASTOpBase):
    """
    Operator class for getting dimension hierachy
    维度表达式语法树中的层级操作节点
    """
    def calc(self, args):
        """
        计算当前节点的层级结果

        Args:
            args: 层级操作所需的参数

        Returns:
            返回当前节点的层级结果列表

        """
        hierachy = self._op_name
        member, reverse, *remain = args
        order = -1 if reverse != 0 else 1

        dim_container = self._dim_obj[str(member)]
        if hierachy in {'Level', 'ILevel'}:
            start, stop = remain
            return getattr(dim_container, hierachy)[start:stop:order]
        else:
            return getattr(dim_container, hierachy)[::order]


class ASTOpAttr(ASTOpBase):
    def eval(self, node: ASTNode):
        val = node.eval
        if node.is_quoted:
            return {'N': False, 'Y': True}.get(val, val)
        else:
            return val

    def calc(self, args):
        """构建 ``filter`` 过滤字典"""
        key, val = args
        return {key: val}


class ASTOpFilter(ASTOpBase):
    """过滤操作语法树节点"""
    filter_map = {
        "OrFilter": "or",
        "AndFilter": "and",
        "NorFilter": "nor",
        "NAndFilter": "nand",
    }

    def calc(self, args):
        _filter = self.filter_map[self._op_name]
        dim_container, *conditions = args
        dim_container = self._get_member(dim_container)

        all_cond = {}
        for cond in conditions:
            all_cond.update(cond)

        return dim_container.where(_filter, **all_cond)


class ASTOpRemove(ASTOpBase):
    """删除操作语法树节点"""
    def calc(self, args):
        dim_container, *remain = args
        dim_container = self._get_member(dim_container)

        to_remove = []
        for item in remain:
            to_remove.append(self._get_member(item))

        return dim_container.remove(*to_remove)


class ASTOpRoot(ASTOpBase):
    """语法树根节点，将维度表达式最终结果收集，并存储到 ``Dimension`` 中的查询集"""
    def __init__(self, dim_obj):
        super().__init__(dim_obj, 'Root')
        self._dim_obj = dim_obj

    def calc(self, args):
        to_select = (self._get_member(mbr) for mbr in args)
        return self._dim_obj.select(*to_select)

    def __str__(self):
        return 'DummyRoot'


class ASTOpFactory:
    """语法树维度操作节点工程，可以根据 ``cls_map`` 创建不同的维度操作节点"""
    cls_map = {
        'Remove': ASTOpRemove,
        "OrFilter": ASTOpFilter,
        "AndFilter": ASTOpFilter,
        "NorFilter": ASTOpFilter,
        "NAndFilter": ASTOpFilter,
        "Attr": ASTOpAttr,
        "Base": ASTOpHierachy,
        "IBase": ASTOpHierachy,
        "Children": ASTOpHierachy,
        "IChildren": ASTOpHierachy,
        "Descendant": ASTOpHierachy,
        "IDescendant": ASTOpHierachy,
        "Level": ASTOpHierachy,
        "ILevel": ASTOpHierachy,
    }

    def __new__(cls, dim, value):
        target_cls = cls.cls_map.get(value)
        if target_cls is None:
            raise ValueError(f"Unknow Expression: {value}")
        return target_cls(dim, value)


class DimExprAnalysor:
    """基于语法树的维度表达式分析器"""
    def __init__(self, dimension, dim_expr):
        self.dim = dimension
        self.dummy_root = ASTOpRoot(dimension)
        for expr in dim_expr.split(";"):
            self._gen_ast(expr)

    def _gen_ast(self, expr):
        """创建语法树"""
        root_stack = [self.dummy_root]
        dim = self.dim
        end_bracket = False

        tmp_string = []
        last_char = ')'

        for char in expr:
            if char == '(':
                node = ASTOpFactory(dim, ''.join(tmp_string))
                tmp_string.clear()
                node.set_parent(root_stack[-1])
                root_stack.append(node)
            elif char == ',':
                if not end_bracket:
                    node = ASTNode(''.join(tmp_string))
                    tmp_string.clear()
                    node.set_parent(root_stack[-1])
                else:
                    end_bracket = False
            elif char == ')':
                if not end_bracket:
                    node = ASTNode(''.join(tmp_string))
                    tmp_string.clear()
                    root = root_stack.pop(-1)
                    node.set_parent(root)
                    end_bracket = True
                else:
                    root_stack.pop(-1)
            else:
                if char == ' ' and last_char in {')', ','}:
                    char = last_char  # 去除连续空格
                else:
                    tmp_string.append(char)

            last_char = char

        if tmp_string:
            node = ASTNode(''.join(tmp_string))
            node.set_parent(root_stack[-1])

    def show_ast(self):
        """
        打印语法树

        Example:
            .. code-block:: python

                # dim 是加载维度表达式的维度树
                dim_expr = DimExprAnalysor(dim, 'Base(node, 0)')
                dim_expr.show_ast()
                # 执行上述代码会打印如下所示的语法树：
                '''
                DummyRoot
                └── Base
                    ├── node
                    └── 0
                '''

        """
        print(TreeRenderer().render(self.dummy_root))
        return self

    def solve(self):
        """计算维度表达式结果，返回已加载执行维度表达式的维度，结果存储在 `selected` 集合中"""
        return self.dummy_root.solve()
