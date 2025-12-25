from ._base import DimensionBase, MemberBase
from deepfos.element.dimension import Dimension as EleDimension


class ElementDimension(DimensionBase):
    def __init__(self, dimension: EleDimension):
        self.ele = dimension
        super(ElementDimension, self).__init__(dimension.element_name)

    def load_expr(self, expr) -> 'ElementDimension':
        self.selected = selected = []
        for record in self.ele.query(
                expr, fields=['name', 'aggweight'],
                as_model=False
        ):
            mbr = MemberBase(record['name'])
            mbr.weight = record['aggweight']
            selected.append(mbr)
        return self

    def __getitem__(self, item):
        return item
