"""
Segment Tree
"""

from typing import Protocol, Sequence, Optional, Callable, Iterable, Any


class NodeLike(Protocol):
    name: str
    parent: Optional['NodeLike']
    children: Sequence['NodeLike']


class Visitor:
    def __init__(self, on_node: Callable[[NodeLike], Any]):
        self.on_node = on_node

    def visit(self, node: NodeLike):
        for node in self.iter_node(node):
            self.on_node(node)

    def iter_node(self, node: NodeLike) -> Iterable[NodeLike]:
        raise NotImplementedError()


class DFVisitor(Visitor):
    def iter_node(self, node: NodeLike) -> Iterable[NodeLike]:
        yield node
        for child in node.children:
            yield from self.iter_node(child)

