import functools
from typing import Tuple, Union, Type, Callable
from types import ModuleType
import importlib
from contextlib import contextmanager

__all__ = [
    'string_import',
    'context_patch',
    'patch'
]


def string_import(
    importable: str,
    check_obj: bool = False,
) -> Tuple[ModuleType, str]:
    if not importable.startswith('deepfos.'):
        raise ValueError("Cannot patch object not belonged to deepfos package.")

    module_str, obj_str = importable.rsplit('.', maxsplit=1)
    module = importlib.import_module(module_str)

    if check_obj and not hasattr(module, obj_str):
        raise ValueError(f"Module: {module.__name__} has no attribute: {obj_str}")

    return module, obj_str


@contextmanager
def context_patch(
    importable: str,
    patch_as: Union[Type, Callable, ModuleType]
):
    module, obj_str = string_import(importable)

    if hasattr(module, obj_str):
        obj_bak = getattr(module, obj_str)
    else:
        obj_bak = None

    setattr(module, obj_str, patch_as)

    try:
        yield
    finally:
        if obj_bak is None:
            delattr(module, obj_str)
        else:
            setattr(module, obj_str, obj_bak)


def patch(
    importable: str,
    patch_as: Union[Type, Callable, ModuleType]
):
    # noinspection PyProtectedMember
    """替换deepfos包的代码

    装饰器，在被装饰的函数中，对应代码将被替换。
    退出函数后，代码恢复。

    Args:
        importable: 需要替换的模块/函数/类
        patch_as: 替换为对象

    >>> from deepfos.lib.patch import patch
    >>> from deepfos.lib.utils import _concat_url_single, concat_url
    >>> def new_concat_url_single(a, b):
    ...     return _concat_url_single(a, b) + '/patched'
    >>> @patch('deepfos.lib.utils._concat_url_single', new_concat_url_single)
    ... def pathced_func():
    ...     print('in pathced_func')
    ...     print(concat_url('a', 'b'))
    >>> def main():
    ...    print(concat_url('a', 'b'))
    ...    pathced_func()
    ...    print(concat_url('a', 'b'))
    >>> main()
    a/b
    in pathced_func
    a/b/patched
    a/b
    """
    def inner(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            with context_patch(importable, patch_as):
                return func(*args, **kwargs)
        return wrap

    return inner
