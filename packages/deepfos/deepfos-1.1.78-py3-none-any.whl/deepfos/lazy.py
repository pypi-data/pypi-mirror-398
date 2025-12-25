import sys
from importlib import import_module
from types import ModuleType
from typing import Dict, Sequence, Any

from deepfos.lib.constant import UNSET
from deepfos.local import Proxy


class LazyModule(ModuleType):

    def __init__(self, module_name, parent_module_globals):
        self._module_name = module_name
        self._parent_module_globals = parent_module_globals

        super(LazyModule, self).__init__(module_name)

    def _load(self):
        """Load the module and insert it into the parent's globals."""
        # Import the target module and insert it into the parent's namespace
        module = import_module(self.__name__)
        self._parent_module_globals[self._module_name] = module

        # Update this object's dict so that if someone keeps a reference to the
        #   LazyLoader, lookups are efficient
        #   (__getattr__ is only called on lookups that fail).
        self.__dict__.update(module.__dict__)

        return module

    def __getattr__(self, attr):
        module = self._load()
        return getattr(module, attr)

    def __dir__(self):
        module = self._load()
        return dir(module)


class LazyCallable(Proxy):
    def __init__(self, module, local_name):
        object.__setattr__(self, '_LazyCallable__module', module)
        object.__setattr__(self, '_LazyCallable__local_name', local_name)
        object.__setattr__(self, '_LazyCallable__callable', UNSET)

    __module__ = Proxy.__module__

    def _get_current_object(self):
        if self.__callable is not UNSET:
            return self.__callable

        try:
            mod = sys.modules[self.__module]
        except KeyError:
            mod = lazy_module(self.__module)

        object.__setattr__(
            self, '_LazyCallable__callable', 
            getattr(mod, self.__local_name)
        )
        return self.__callable

    def __await__(self):
        return self._get_current_object().__await__()


def lazy_module(modname):
    """获得懒加载模块

    Args:
        modname: 模块名，形如aaa.bbb.ccc，将得到等效于from aaa.bbb import ccc的懒加载模块


    """
    return LazyModule(modname, globals())


def lazy_callable(modname, *names):
    """获得对应模块里的若干方法/函数的懒加载代理

    Args:
        modname : 模块名，形如aaa.bbb.ccc
        names : 方法/函数名

    """
    return tuple(LazyCallable(modname, cname) for cname in names)


def lazify(
    target: Dict[str, Sequence[str]],
    _globals: Dict[str, Any]
):
    """懒加载模块成员

    Args:
        target: module to module members
        _globals: globals in caller scope
    """

    for modname, mbrs in target.items():
        _globals.update(zip(
            mbrs,
            lazy_callable(modname, *mbrs)
        ))
