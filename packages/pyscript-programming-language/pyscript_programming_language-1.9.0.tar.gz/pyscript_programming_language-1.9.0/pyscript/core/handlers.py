from .cache import lock
from .constants import ENV_PYSCRIPT_NO_GIL
from .objects import PysPythonFunction, PysFunction

from os import environ
from types import MethodType

if environ.get(ENV_PYSCRIPT_NO_GIL) is None:

    def handle_call(object, context, position):
        with lock:

            if isinstance(object, PysFunction):
                code = object.__code__
                code.call_context = context
                code.position = position

            elif isinstance(object, PysPythonFunction):
                code = object.__code__
                code.context = context
                code.position = position

            elif isinstance(object, type):
                method = getattr(object, '__new__', None)
                if method is not None:
                    handle_call(method, context, position)

                method = getattr(object, '__init__', None)
                if method is not None:
                    handle_call(method, context, position)

            elif isinstance(object, MethodType):
                handle_call(object.__func__, context, position)

    _GIL = True
else:

    def handle_call(object, context, position):
        if isinstance(object, PysFunction):
            code = object.__code__
            code.call_context = context
            code.position = position

        elif isinstance(object, PysPythonFunction):
            code = object.__code__
            code.context = context
            code.position = position

        elif isinstance(object, type):
            method = getattr(object, '__new__', None)
            if method is not None:
                handle_call(method, context, position)

            method = getattr(object, '__init__', None)
            if method is not None:
                handle_call(method, context, position)

        elif isinstance(object, MethodType):
            handle_call(object.__func__, context, position)

    _GIL = False