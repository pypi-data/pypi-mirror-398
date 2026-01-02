from .bases import Pys
from .checks import is_equals
from .constants import TOKENS
from .cache import PysUndefined, undefined
from .mapping import BINARY_FUNCTIONS_MAP, EMPTY_MAP
from .utils.decorators import immutable
from .utils.generic import setimuattr
from .utils.similarity import get_closest

from types import ModuleType
from typing import Any, Optional

@immutable
class PysSymbolTable(Pys):

    __slots__ = ('parent', 'symbols', 'globals')

    def __init__(self, parent: Optional['PysSymbolTable'] = None) -> None:
        setimuattr(self, 'parent', parent.parent if isinstance(parent, PysClassSymbolTable) else parent)
        setimuattr(self, 'symbols', {})
        setimuattr(self, 'globals', set())

    def get(self, name: str) -> Any | PysUndefined:
        value = self.symbols.get(name, undefined)

        if value is undefined:
            if self.parent:
                return self.parent.get(name)

            builtins = self.symbols.get('__builtins__', undefined)
            if builtins is not undefined:
                return (
                    builtins if isinstance(builtins, dict) else getattr(builtins, '__dict__', EMPTY_MAP)
                ).get(name, undefined)

        return value

    def set(self, name: str, value: Any, *, operand: int = TOKENS['EQUAL']) -> bool:
        if is_equals(operand):

            if name in self.globals and self.parent:
                success = self.parent.set(name, value, operand=operand)
                if success:
                    return True

            self.symbols[name] = value
            return True

        elif name not in self.symbols:
            if name in self.globals and self.parent:
                return self.parent.set(name, value, operand=operand)
            return False

        self.symbols[name] = BINARY_FUNCTIONS_MAP[operand](self.symbols[name], value)
        return True

    def remove(self, name: str) -> bool:
        if name not in self.symbols:
            if name in self.globals and self.parent:
                return self.parent.remove(name)
            return False

        del self.symbols[name]
        return True

class PysClassSymbolTable(PysSymbolTable):

    __slots__ = ()

    def __init__(self, parent: PysSymbolTable) -> None:
        super().__init__(parent)

def find_closest(symtab: PysSymbolTable, name: str) -> str | None:
    symbols = set(symtab.symbols.keys())

    parent = symtab.parent
    while parent:
        symbols.update(parent.symbols.keys())
        parent = parent.parent

    builtins = symtab.get('__builtins__')
    if builtins is not undefined:
        symbols.update((builtins if isinstance(builtins, dict) else getattr(builtins, '__dict__', EMPTY_MAP)).keys())

    return get_closest(symbols, name)

def new_symbol_table(*, symbols=None, file=None, name=None, doc=None):
    symtab = PysSymbolTable()

    if symbols is None:
        module = ModuleType(name, doc)
        setimuattr(symtab, 'symbols', module.__dict__)
        symtab.set('__file__', file)
    else:
        module = None
        setimuattr(symtab, 'symbols', symbols)

    if symtab.get('__builtins__') is undefined:
        from .pysbuiltins import pys_builtins
        symtab.set('__builtins__', pys_builtins)

    return symtab, module