from ..bases import Pys
from ..constants import ENV_PYSCRIPT_NO_TYPECHECK

from os import environ
from types import MethodType

def typechecked(func, *args, **kwargs):
    return func

_TYPECHECK = False

if environ.get(ENV_PYSCRIPT_NO_TYPECHECK) is None:
    try:
        from beartype import beartype as typechecked
        _TYPECHECK = True
    except ImportError:
        try:
            from typeguard import typechecked
            _TYPECHECK = True
        except ImportError:
            pass

class _PysNameSpaceUtilities(Pys):

    __slots__ = ()

    def __new__(cls):
        raise TypeError("cannot create namespace class instances")

    def new_singleton(cls, *args, **kwargs):
        from ..cache import singletons  # circular import problem solved
        if type(singletons.get(cls, None)) is not cls:
            singletons[cls] = cls.__new_singleton__(cls, *args, **kwargs)
        return singletons[cls]

    def readonly_attribute(*args, **kwargs):
        raise AttributeError("readonly attribute")

    def inheritable_class(self, *args, **kwargs):
        raise TypeError(f"uninherited class for {self.__name__}")

def immutable(cls):
    cls.__setattr__ = _PysNameSpaceUtilities.readonly_attribute
    cls.__delattr__ = _PysNameSpaceUtilities.readonly_attribute
    return cls

def inheritable(cls):
    cls.__init_subclass__ = MethodType(_PysNameSpaceUtilities.inheritable_class, cls)
    return cls

def singleton(cls):
    cls.__new__ = _PysNameSpaceUtilities.new_singleton
    if not hasattr(cls, '__new_singleton__'):
        cls.__new_singleton__ = super(cls, cls).__new__
    return cls