from .bases import Pys
from .constants import LIBRARIES_PATH, SITE_PACKAGES_PATH
from .exceptions import PysTraceback
from .utils.debug import print_display, print_traceback
from .utils.decorators import inheritable, singleton

from threading import RLock
from typing import Any, Callable, Literal

loading_modules = set()
lock = RLock()
modules = dict()
path = [SITE_PACKAGES_PATH, LIBRARIES_PATH]
singletons = dict()

@singleton
@inheritable
class PysUndefined(Pys):

    __slots__ = ()

    def __new_singleton__(cls) -> 'PysUndefined':
        global undefined
        undefined = super(cls, cls).__new__(cls)
        return undefined

    def __repr__(self) -> Literal['undefined']:
        return 'undefined'

    def __bool__(self) -> Literal[False]:
        return False

@singleton
@inheritable
class PysHook(Pys):

    __slots__ = ()

    def __new_singleton__(cls) -> 'PysHook':
        global hook
        hook = super(cls, cls).__new__(cls)
        hook.running_shell = False
        hook.running_breakpoint = False
        hook.display = print_display
        hook.exception = print_traceback
        hook.ps1 = '>>> '
        hook.ps2 = '... '
        return hook

    def __repr__(self) -> str:
        return f'<hook object at {id(self):016X}>'

    @property
    def running_shell(self) -> bool:
        return singletons['hook.running_shell']

    @running_shell.setter
    def running_shell(self, value: bool) -> None:
        singletons['hook.running_shell'] = bool(value)

    @property
    def running_breakpoint(self) -> bool:
        return singletons['hook.running_breakpoint']

    @running_breakpoint.setter
    def running_breakpoint(self, value: bool) -> None:
        singletons['hook.running_breakpoint'] = bool(value)

    @property
    def display(self) -> Callable[[Any], None]:
        return singletons['hook.display']

    @display.setter
    def display(self, value: Callable[[Any], None]) -> None:
        if value is not None and not callable(value):
            raise TypeError("hook.display: must be callable")
        singletons['hook.display'] = value

    @property
    def exception(self) -> Callable[[type[BaseException], BaseException | None, PysTraceback], None]:
        return singletons['hook.exception']

    @exception.setter
    def exception(self, value: Callable[[type[BaseException], BaseException | None, PysTraceback], None]) -> None:
        if value is not None and not callable(value):
            raise TypeError("hook.exception: must be callable")
        singletons['hook.exception'] = value

    @property
    def ps1(self) -> str:
        return singletons['hook.ps1']

    @ps1.setter
    def ps1(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("hook.ps1: must be a string")
        singletons['hook.ps1'] = value

    @property
    def ps2(self) -> str:
        return singletons['hook.ps2']

    @ps2.setter
    def ps2(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("hook.ps2: must be a string")
        singletons['hook.ps2'] = value

PysUndefined()
PysHook()