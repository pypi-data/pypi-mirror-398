from .bases import Pys
from .cache import hook
from .context import PysContext
from .exceptions import PysTraceback, PysSignal
from .position import PysPosition
from .utils.debug import print_traceback
from .utils.generic import get_error_args

from typing import Any

class PysResult(Pys):
    __slots__ = ()

class PysParserResult(PysResult):

    def __init__(self):
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0
        self.fatal = False

        self.node = None
        self.error = None

    def register_advancement(self):
        self.last_registered_advance_count += 1
        self.advance_count += 1

    def register(self, result, require=False):
        self.last_registered_advance_count = result.advance_count
        self.advance_count += result.advance_count
        self.fatal = require or result.fatal

        self.error = result.error

        return result.node

    def try_register(self, result):
        if result.error and not result.fatal:
            self.to_reverse_count = result.advance_count
        else:
            return self.register(result)

    def success(self, node):
        self.node = node
        return self

    def failure(self, error, fatal=True):
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
            self.fatal = fatal
        return self

class PysRunTimeResult(PysResult):

    __slots__ = (
        'should_continue', 'should_break', 'func_should_return', 'func_return_value', 'value', 'error',
        '_context', '_position'
    )

    def reset(self):
        self.should_continue = False
        self.should_break = False
        self.func_should_return = False
        self.func_return_value = None

        self.value = None
        self.error = None

    __init__ = reset

    def register(self, result):
        self.error = result.error

        self.should_continue = result.should_continue
        self.should_break = result.should_break
        self.func_should_return = result.func_should_return
        self.func_return_value = result.func_return_value

        return result.value

    def success(self, value):
        self.reset()
        self.value = value
        return self

    def success_return(self, value):
        self.reset()
        self.func_should_return = True
        self.func_return_value = value
        return self

    def success_continue(self):
        self.reset()
        self.should_continue = True
        return self

    def success_break(self):
        self.reset()
        self.should_break = True
        return self

    def failure(self, error):
        self.reset()
        self.error = error
        return self

    def should_return(self):
        return (
            self.error or
            self.func_should_return or
            self.should_continue or
            self.should_break
        )

    # --- HANDLE EXCEPTION ---

    def __call__(self, context, position):
        self._context = context
        self._position = position
        return self

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # return
        # ^^^^^^  <--- debug only

        if exc_type is not None:

            self.register(exc_val.result) \
            if exc_type is PysSignal else \
            self.failure(
                PysTraceback(
                    exc_type if exc_val is None else exc_val,
                    self._context,
                    self._position
                )
            )

        return True

class PysExecuteResult(PysResult):

    def __init__(self, context: PysContext) -> None:
        self.context = context

        self.value = None
        self.error = None

    def success(self, value: Any) -> 'PysExecuteResult':
        self.value = value
        return self

    def failure(self, error: PysTraceback) -> 'PysExecuteResult':
        self.error = error
        return self

    # --- HANDLE EXECUTE ---

    def process(self) -> tuple[int | Any, bool]:
        result = PysRunTimeResult()

        with result(self.context, PysPosition(self.context.file, -1, -1)):

            if self.error:
                if self.error.exception is SystemExit:
                    return 0, True
                elif type(self.error.exception) is SystemExit:
                    return self.error.exception.code, True
                elif hook.exception is not None:
                    hook.exception(*get_error_args(self.error))
                return 1, False

        if result.should_return():
            if result.error:
                print_traceback(*get_error_args(result.error))
            return 1, False

        return 0, False