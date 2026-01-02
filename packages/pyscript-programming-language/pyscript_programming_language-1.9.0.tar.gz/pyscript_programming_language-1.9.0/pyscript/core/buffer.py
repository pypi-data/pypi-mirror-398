from .bases import Pys
from .utils.decorators import immutable
from .utils.generic import setimuattr
from .utils.string import normstr

from io import IOBase
from typing import Callable, Iterable, Optional

@immutable
class PysBuffer(Pys):
    __slots__ = ()

class PysFileBuffer(PysBuffer):

    __slots__ = ('text', 'name')

    def __init__(
        self,
        text: str | bytes | bytearray | Iterable | Callable | IOBase | 'PysFileBuffer',
        name: Optional[str | bytes] = None
    ) -> None:

        if isinstance(text, PysFileBuffer):
            name = normstr(text.name if name is None else name)
            text = normstr(text.text)

        elif isinstance(text, IOBase):
            name = normstr(getattr(text, 'name', '<io>') if name is None else name)
            text = normstr(text)

        else:
            name = '<string>' if name is None else normstr(name)
            text = normstr(text)

        setimuattr(self, 'text', text)
        setimuattr(self, 'name', name)

    def __repr__(self) -> str:
        return f'<FileBuffer from {self.name!r}>'