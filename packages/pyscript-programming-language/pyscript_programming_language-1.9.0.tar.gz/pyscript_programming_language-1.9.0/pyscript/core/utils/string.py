from collections.abc import Iterable
from io import IOBase, TextIOWrapper
from json import detect_encoding
from types import BuiltinMethodType

def normstr(obj):
    if isinstance(obj, str):
        return obj.replace('\r\n', '\n').replace('\r', '\n')

    elif isinstance(obj, (bytes, bytearray)):
        return normstr(obj.decode(detect_encoding(obj), 'surrogatepass'))

    elif isinstance(obj, IOBase):
        if not obj.readable():
            raise TypeError("unreadable IO")
        return normstr(obj.read())

    elif isinstance(obj, Iterable):
        return '\n'.join(map(normstr, obj))

    elif isinstance(obj, BuiltinMethodType) and \
        isinstance(self := getattr(obj, '__self__', None), TextIOWrapper) and \
        obj.__name__ == 'readline':

        if not self.readable():
            raise TypeError("unreadable IO, provides readline function")

        lines = []
        while True:
            if not (line := obj()):
                break
            lines.append(normstr(line))
        return '\n'.join(lines)

    raise TypeError('not a string')

def join(sequence, conjunction='and'):
    length = len(sequence)
    if length == 1:
        return sequence[0]
    elif length == 2:
        return f'{sequence[0]} {conjunction} {sequence[1]}'
    return f'{", ".join(sequence[:-1])}, {conjunction} {sequence[-1]}'

def indent(string, length):
    prefix = ' ' * length
    return '\n'.join(prefix + line for line in normstr(string).splitlines())