from .bases import Pys
from .buffer import PysFileBuffer
from .constants import DEFAULT
from .position import PysPosition
from .symtab import PysSymbolTable
from .utils.decorators import immutable
from .utils.generic import setimuattr

from typing import Optional

@immutable
class PysContext(Pys):

    __slots__ = ('file', 'name', 'qualname', 'flags', 'symbol_table', 'parent', 'parent_entry_position')

    def __init__(
        self,
        *,
        file: PysFileBuffer,
        name: Optional[str] = None,
        qualname: Optional[str] = None,
        flags: Optional[int] = None,
        symbol_table: Optional[PysSymbolTable] = None,
        parent: Optional['PysContext'] = None,
        parent_entry_position: Optional[PysPosition] = None
    ) -> None:
        if flags is None and parent:
            flags = parent.flags

        setimuattr(self, 'file', file)
        setimuattr(self, 'name', name)
        setimuattr(self, 'qualname', qualname)
        setimuattr(self, 'flags', DEFAULT if flags is None else flags)
        setimuattr(self, 'symbol_table', symbol_table)
        setimuattr(self, 'parent', parent)
        setimuattr(self, 'parent_entry_position', parent_entry_position)

    def __repr__(self) -> str:
        return f'<Context {self.name!r}>'

class PysClassContext(PysContext):

    __slots__ = ()

    def __init__(
        self,
        *,
        name: str,
        symbol_table: PysSymbolTable,
        parent: PysContext,
        parent_entry_position: PysPosition
    ) -> None:
        qualname = parent.qualname
        super().__init__(
            file=parent.file,
            name=name,
            qualname=('' if qualname is None else qualname + '.') + name,
            symbol_table=symbol_table,
            parent=parent,
            parent_entry_position=parent_entry_position
        )