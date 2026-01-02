from typing import TYPE_CHECKING, Any, Callable, Iterable, Literal, Optional

if TYPE_CHECKING:
    from .core.buffer import PysFileBuffer
    from .core.cache import PysUndefined, PysHook
    from .core.highlight import _PysHighlightFormatter
    from .core.position import PysPosition
    from .core.results import PysExecuteResult
    from .core.symtab import PysSymbolTable
    from .core.version import PysVersionInfo

    from io import IOBase
    from types import BuiltinMethodType, ModuleType

from . import core as core
from .core.highlight import PygmentsPyScriptLexer as PygmentsPyScriptLexer

DEFAULT: int
DEBUG: int
SILENT: int
RETURN_RESULT: int
HIGHLIGHT: int
NO_COLOR: int
REVERSE_POW_XOR: int

HLFMT_HTML: _PysHighlightFormatter
HLFMT_ANSI: _PysHighlightFormatter
HLFMT_BBCODE: _PysHighlightFormatter

undefined: PysUndefined
hook: PysHook
version: str
version_info: PysVersionInfo

def pys_highlight(
    source: str | bytes | bytearray | Iterable | BuiltinMethodType | IOBase | PysFileBuffer,
    format: Optional[
        Callable[
            [
                str | Literal[
                    'start', 'invalid', 'identifier', 'identifier-constant', 'identifier-function', 'identifier-type',
                    'keyword', 'keyword-constant', 'number', 'string', 'comment', 'newline', 'default', 'end'
                ],
                PysPosition,
                str
            ],
            str
        ]
    ] = None,
    max_bracket_level: int = 3
) -> str: ...

def pys_exec(
    source: str | bytes | bytearray | Iterable | BuiltinMethodType | IOBase | PysFileBuffer,
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT
) -> None | PysExecuteResult: ...

def pys_eval(
    source: str | bytes | bytearray | Iterable | BuiltinMethodType | IOBase | PysFileBuffer,
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT
) -> Any | PysExecuteResult: ...

def pys_require(
    name: str | bytes,
    flags: int = DEFAULT
) -> ModuleType | Any: ...

def pys_shell(
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT
) -> int | Any: ...

__version__: str
__date__: str
__all__: tuple[str]