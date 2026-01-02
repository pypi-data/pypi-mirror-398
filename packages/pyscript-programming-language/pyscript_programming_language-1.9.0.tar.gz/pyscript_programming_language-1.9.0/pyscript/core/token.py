from .bases import Pys
from .mapping import REVERSE_TOKENS
from .position import PysPosition
from .utils.decorators import typechecked, immutable
from .utils.generic import setimuattr

from typing import Any, Iterable, Optional

@immutable
class PysToken(Pys):

    __slots__ = ('type', 'position', 'value')

    @typechecked
    def __init__(self, type: int, position: PysPosition, value: Optional[Any] = None) -> None:
        setimuattr(self, 'type', type)
        setimuattr(self, 'position', position)
        setimuattr(self, 'value', value)

    def __repr__(self) -> str:
        value = self.value
        return 'Token({}{})'.format(
            REVERSE_TOKENS.get(self.type, '<UNKNOWN>'),
            '' if value is None else f', value={value!r}'
        )

    def match(self, type: int, value: Any) -> bool:
        return self.type == type and self.value == value

    def matches(self, type: int, values: Iterable) -> bool:
        return self.type == type and self.value in values