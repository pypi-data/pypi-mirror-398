from ..constants import ENV_PYSCRIPT_NO_READLINE

from collections.abc import Sequence
from inspect import currentframe
from os import environ, system
from re import compile as re_compile
from types import UnionType

import sys

delimuattr = object.__delattr__
setimuattr = object.__setattr__
version_match = re_compile(r'^(\d+)\.(\d+)\.(\d+)((?:a|b|rc)(\d+)|\.(dev|post)(\d+))?$').match

def get_frame(deep=0):
    deep += 1
    frame = currentframe()

    while deep > 0 and frame:
        frame = frame.f_back
        deep -= 1

    return frame

def get_locals(deep=0):
    if frame := get_frame(deep + 1):
        locals = frame.f_locals
        return locals if isinstance(locals, dict) else dict(locals)
    return {}

def get_any(object, key, default=None):
    if isinstance(object, dict):
        return object.get(key, default)
    elif isinstance(object, Sequence):
        return object[key] if 0 <= key < len(object) else default
    raise TypeError("unknown object")

def is_object_of(obj: object | type, class_or_tuple: type | UnionType | tuple[type | UnionType, ...]) -> bool:

    """
    Returns whether an object is derived from a parent class.
    The object here can be an initialized object, which calls `isinstance(obj, class_or_type)`,
    or a class type, which calls `issubclass(obj, class_or_tuple)`.
    """

    return (
        isinstance(obj, class_or_tuple) or
        (isinstance(obj, type) and issubclass(obj, class_or_tuple))
    )

def import_readline():
    return False

if sys.platform == 'win32':
    def clear_console():
        system('cls')

else:
    def clear_console():
        system('clear')

    if environ.get(ENV_PYSCRIPT_NO_READLINE) is None:
        def import_readline():
            try:
                import readline
                return True
            except:
                return False

def get_error_args(exception):
    if exception is None:
        return None, None, None

    pyexception = exception.exception
    return (
        (pyexception, None, exception)
        if isinstance(pyexception, type) else
        (type(pyexception), pyexception, exception)
    )