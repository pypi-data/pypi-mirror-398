import abc
import copy

__module__ = __name__


def _default_cls_attr(name, type_, cls_value):
    def __new__(cls, getter):
        instance = type_.__new__(cls, cls_value)
        instance.__getter = getter
        return instance

    def __get__(self, obj, cls=None):
        return self.__getter(obj) if obj is not None else self

    return type(name, (type_,), {
        '__new__': __new__, '__get__': __get__,
    })


class Proxy(abc.ABC):
    def _get_current_object(self):
        raise NotImplementedError

    def __getattr__(self, name):
        if name == '__members__':  # pragma: no cover
            return dir(self._get_current_object())
        return getattr(self._get_current_object(), name)

    def __mro_entries__(self, bases):
        return self._get_current_object(),

    def __instancecheck__(self, instance):
        """Override for isinstance(instance, cls)."""
        return isinstance(instance, self._get_current_object())

    def __subclasscheck__(self, subclass):
        """Override for issubclass(subclass, cls)."""
        return issubclass(subclass, self._get_current_object())

    @property
    def __dict__(self):  # pragma: no cover
        try:
            return self._get_current_object().__dict__
        except RuntimeError:
            raise AttributeError('__dict__')

    @_default_cls_attr('name', str, __name__)
    def __name__(self):  # pragma: no cover
        return self._get_current_object().__name__

    @_default_cls_attr('qualname', str, __name__)
    def __qualname__(self):  # pragma: no cover
        return self._get_current_object().__qualname__

    @_default_cls_attr('module', str, __module__)
    def __module__(self):
        return self._get_current_object().__module__

    @_default_cls_attr('doc', str, __doc__)
    def __doc__(self):  # pragma: no cover
        return self._get_current_object().__doc__

    def __repr__(self):
        obj = self._get_current_object()
        return repr(obj)

    def __bool__(self):
        try:
            return bool(self._get_current_object())
        except RuntimeError:  # pragma: no cover
            return False

    def __unicode__(self):  # pragma: no cover
        try:
            return unicode(self._get_current_object())  # noqa
        except RuntimeError:
            return repr(self)

    def __dir__(self):  # pragma: no cover
        try:
            return dir(self._get_current_object())
        except RuntimeError:
            return []

    def __setitem__(self, key, value):
        self._get_current_object()[key] = value

    def __delitem__(self, key):
        del self._get_current_object()[key]

    def _get_class(self):
        return self._get_current_object().__class__

    @property
    def __class__(self):
        return self._get_class()

    __setattr__ = lambda x, n, v: setattr(x._get_current_object(), n, v)
    __delattr__ = lambda x, n: delattr(x._get_current_object(), n)
    __str__ = lambda x: str(x._get_current_object())
    __lt__ = lambda x, o: x._get_current_object() < o
    __le__ = lambda x, o: x._get_current_object() <= o
    __eq__ = lambda x, o: x._get_current_object() == o
    __ne__ = lambda x, o: x._get_current_object() != o
    __gt__ = lambda x, o: x._get_current_object() > o
    __ge__ = lambda x, o: x._get_current_object() >= o
    __cmp__ = lambda x, o: cmp(x._get_current_object(), o)  # noqa
    __hash__ = lambda x: hash(x._get_current_object())
    __call__ = lambda x, *a, **kw: x._get_current_object()(*a, **kw)
    __len__ = lambda x: len(x._get_current_object())
    __getitem__ = lambda x, i: x._get_current_object()[i]
    __iter__ = lambda x: iter(x._get_current_object())
    __contains__ = lambda x, i: i in x._get_current_object()
    __add__ = lambda x, o: x._get_current_object() + o
    __radd__ = lambda x, o: o + x._get_current_object()
    __sub__ = lambda x, o: x._get_current_object() - o
    __rsub__ = lambda x, o: o - x._get_current_object()
    __mul__ = lambda x, o: x._get_current_object() * o
    __rmul__ = lambda x, o: o * x._get_current_object()
    __matmul__ = lambda x, o: x._get_current_object().__matmul__(o)
    __rmatmul__ = lambda x, o: o.__rmatmul__(x._get_current_object())
    __floordiv__ = lambda x, o: x._get_current_object() // o
    __rfloordiv__ = lambda x, o: o // x._get_current_object()
    __mod__ = lambda x, o: x._get_current_object() % o
    __rmod__ = lambda x, o: o % x._get_current_object()
    __divmod__ = lambda x, o: x._get_current_object().__divmod__(o)
    __rdivmod__ = lambda x, o: x._get_current_object().__rdivmod__(o)
    __pow__ = lambda x, o: x._get_current_object() ** o
    __rpow__ = lambda x, o: o ** x._get_current_object()
    __lshift__ = lambda x, o: x._get_current_object() << o
    __rlshift__ = lambda x, o: o << x._get_current_object()
    __rshift__ = lambda x, o: x._get_current_object() >> o
    __rrshift__ = lambda x, o: o >> x._get_current_object()
    __and__ = lambda x, o: x._get_current_object() & o
    __rand__ = lambda x, o: o & x._get_current_object()
    __xor__ = lambda x, o: x._get_current_object() ^ o
    __rxor__ = lambda x, o: o ^ x._get_current_object()
    __or__ = lambda x, o: x._get_current_object() | o
    __ror__ = lambda x, o: o | x._get_current_object()
    __div__ = lambda x, o: x._get_current_object().__div__(o)
    __rdiv__ = lambda x, o: o / x._get_current_object()
    __truediv__ = lambda x, o: x._get_current_object().__truediv__(o)
    __rtruediv__ = __rdiv__
    __neg__ = lambda x: -(x._get_current_object())
    __pos__ = lambda x: +(x._get_current_object())
    __abs__ = lambda x: abs(x._get_current_object())
    __invert__ = lambda x: ~(x._get_current_object())
    __complex__ = lambda x: complex(x._get_current_object())
    __int__ = lambda x: int(x._get_current_object())
    __long__ = lambda x: long(x._get_current_object())  # noqa
    __float__ = lambda x: float(x._get_current_object())
    __oct__ = lambda x: oct(x._get_current_object())
    __hex__ = lambda x: hex(x._get_current_object())
    __index__ = lambda x: x._get_current_object().__index__()
    __coerce__ = lambda x, o: x._get_current_object().__coerce__(x, o)
    __enter__ = lambda x: x._get_current_object().__enter__()
    __exit__ = lambda x, *a, **kw: x._get_current_object().__exit__(*a, **kw)
    __copy__ = lambda x: copy.copy(x._get_current_object())
    __deepcopy__ = lambda x, memo: copy.deepcopy(x._get_current_object(), memo)
