from enum import Enum, auto


OPMAP = {
    'add': '+',
    'sub': '-',
    'mul': '*',
    'floordiv': '//',
    'truediv': '/',
    'pow': '**',
    'mod': '%',
}

NAME_DFLT = "name"
PNAME_DFLT = "parent_name"
DATACOL_DFLT = "decimal_val"
WEIGHT = "aggweight"


class Instruction(int, Enum):
    cproduct = auto()
