import sys
import inspect

from collections import defaultdict
from types import TracebackType
from typing import Type, NamedTuple, Dict, Set, Union, Optional


_builtin_exp_hook = sys.excepthook


class CodeSpot(NamedTuple):
    filename: str
    first_lineno: int
    last_lineno: Union[int, float]


class CodeLocator:
    spots: Dict[str, Set[CodeSpot]] = defaultdict(set)

    @classmethod
    def add_spot(cls, spot: CodeSpot):
        cls.spots[spot.filename].add(spot)

    @classmethod
    def contains_tb(cls, tb: TracebackType):
        frame = inspect.getframeinfo(tb.tb_frame)
        if frame.filename not in cls.spots:
            return False

        return any(
            spot.first_lineno <= frame.lineno < spot.last_lineno
            for spot in cls.spots[frame.filename]
        )


def eliminate_from_traceback(obj):
    """将对象从错误栈中移除（可作为装饰器）

    Args:
        obj:  需要排除的对象，可以是文件名，函数（方法），类

    Notes:

        - 由于技术原因，第一个错误栈无法移除。
        - 出于可读性考虑，最后一个错误栈也不会移除

    """
    if isinstance(obj, str):
        filename = obj
        first_lineno = 0
        last_lineno = float('inf')
    else:
        code, first_lineno = inspect.getsourcelines(obj)
        last_lineno = first_lineno + len(code)
        filename = inspect.getfile(obj)
    CodeLocator.add_spot(CodeSpot(
        filename=filename,
        first_lineno=first_lineno,
        last_lineno=last_lineno
    ))
    return obj


def exception_hook(
    exc_type: Type[BaseException], 
    exc_value: BaseException, 
    tb: Optional[TracebackType]
):
    if tb is not None:
        contains_tb = CodeLocator.contains_tb
        tb_last = tb
        
        while (tb_next := tb_last.tb_next) is not None:
            if (
                contains_tb(tb_next)
                and (next_tb := tb_next.tb_next) is not None
            ):
                tb_last.tb_next = next_tb
            else:
                tb_last = tb_next

    return _builtin_exp_hook(exc_type, exc_value, tb)


sys.excepthook = exception_hook
