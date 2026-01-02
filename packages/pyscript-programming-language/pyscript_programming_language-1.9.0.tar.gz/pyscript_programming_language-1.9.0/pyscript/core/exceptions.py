from .bases import Pys
from .constants import NO_COLOR
from .utils.ansi import BOLD, acolor
from .utils.decorators import immutable
from .utils.generic import setimuattr
from .utils.string import indent

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .context import PysContext
    from .position import PysPosition
    from .results import PysRunTimeResult

@immutable
class PysTraceback(Pys):

    __slots__ = ('exception', 'context', 'position', 'cause', 'directly')

    def __init__(
        self,
        exception: BaseException | type[BaseException],
        context: 'PysContext',
        position: 'PysPosition',
        cause: Optional['PysTraceback'] = None,
        directly: bool = False
    ) -> None:

        setimuattr(self, 'exception', exception)
        setimuattr(self, 'context', context)
        setimuattr(self, 'position', position)
        setimuattr(self, 'cause', cause)
        setimuattr(self, 'directly', directly)

    def __repr__(self) -> str:
        return f'<traceback of exception {self.exception!r}>'

    def string_traceback(self) -> str:
        from .position import format_arrow  # circular import problem solved

        context = self.context
        position = self.position

        if colored := not (context.flags & NO_COLOR):
            reset = acolor('reset')
            magenta = acolor('magenta')
            bmagenta = acolor('magenta', style=BOLD)
        else:
            reset = ''
            magenta = ''
            bmagenta = ''

        frames = []

        while context:
            is_positionless = position.is_positionless
            context_name = context.name

            frames.append(
                f'  File {magenta}"{position.file.name}"{reset}'
                '{}{}{}'.format(
                    '' if is_positionless else f', line {magenta}{position.start_line}{reset}',
                    '' if context_name is None else f', in {magenta}{context_name}{reset}',
                    '' if is_positionless else f'\n{indent(format_arrow(position, colored), 4)}'
                )
            )

            position = context.parent_entry_position
            context = context.parent

        found_duplicated_frame = 0
        strings_traceback = ''
        last_frame = ''

        for frame in reversed(frames):
            if frame == last_frame:
                found_duplicated_frame += 1

            else:
                if found_duplicated_frame > 0:
                    strings_traceback += f'  [Previous line repeated {found_duplicated_frame} more times]\n'
                    found_duplicated_frame = 0

                strings_traceback += frame + '\n'
                last_frame = frame

        if found_duplicated_frame > 0:
            strings_traceback += f'  [Previous line repeated {found_duplicated_frame} more times]\n'

        result = f'Traceback (most recent call last):\n{strings_traceback}'

        if isinstance(self.exception, type):
            result += f'{bmagenta}{self.exception.__name__}{reset}'
        else:
            message = str(self.exception)
            result += f'{bmagenta}{type(self.exception).__name__}{reset}'
            if message:
                result += f': {magenta}{message}{reset}'

        return (
            self.cause.string_traceback() +
            ('\n\nThe above exception was the direct cause of the following exception:\n\n'
             if self.directly else
             '\n\nDuring handling of the above exception, another exception occurred:\n\n') + result
            if self.cause else
            result
        )

class PysSignal(Pys, BaseException):

    __slots__ = ('result',)

    def __init__(self, result: 'PysRunTimeResult') -> None:
        super().__init__()
        self.result = result

    def __str__(self) -> str:
        if self.result.error is None:
            return '<signal>'

        exception = self.result.error.exception

        if isinstance(exception, type):
            return exception.__name__
        message = str(exception)
        return type(exception).__name__ + (f': {message}' if message else '')