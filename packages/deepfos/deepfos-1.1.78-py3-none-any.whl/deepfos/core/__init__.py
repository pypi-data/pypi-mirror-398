from typing import TYPE_CHECKING

from deepfos.lazy import lazify

if TYPE_CHECKING:  # pragma: no cover
    from .cube import SysCube, Cube, as_function_node
    from .dimension import (
        DimMember, SysDimension, read_expr, 
        Dimension, DimExprAnalysor, ElementDimension
    )
    from .logictable import SQLCondition, BaseTable, MetaTable, TreeRenderer

lazify(
    {
        'deepfos.core.cube': (
            'SysCube', 'Cube', 'as_function_node'
        ),
        'deepfos.core.dimension': (
            'DimMember', 'SysDimension', 'read_expr',
            'Dimension', 'DimExprAnalysor', 'ElementDimension'
        ),
        'deepfos.core.logictable': (
            'SQLCondition', 'BaseTable', 'MetaTable', 'TreeRenderer'
        ),
    },
    globals()
)
