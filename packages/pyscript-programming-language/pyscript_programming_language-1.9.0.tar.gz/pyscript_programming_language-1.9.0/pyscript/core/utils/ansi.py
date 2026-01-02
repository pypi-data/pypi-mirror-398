from collections.abc import Iterable
from functools import reduce
from html.parser import HTMLParser
from operator import or_
from types import MappingProxyType

DEFAULT = 0
BACKGROUND = 1 << 0
BOLD = 1 << 1
FAINT = 1 << 2
ITALIC = 1 << 3
UNDERLINE = 1 << 4
BLINK = 1 << 5
RAPIDBLINK = 1 << 6
STRIKETHROUGH = 1 << 7
DOUBLEUNDERLINE = 1 << 8

ANSI_NAMES_MAP = MappingProxyType({
    'reset': 0,
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37,
    'gray': 90,
    'bright-black': 90,
    'bright-red': 91,
    'bright-green': 92,
    'bright-yellow': 93,
    'bright-blue': 94,
    'bright-magenta': 95,
    'bright-cyan': 96,
    'bright-white': 97
})

STYLE_MAP = MappingProxyType({
    'DEFAULT': DEFAULT,
    'BACKGROUND': BACKGROUND,
    'BOLD': BOLD,
    'FAINT': FAINT,
    'ITALIC': ITALIC,
    'UNDERLINE': UNDERLINE,
    'BLINK': BLINK,
    'RAPIDBLINK': RAPIDBLINK,
    'STRIKETHROUGH': STRIKETHROUGH,
    'DOUBLEUNDERLINE': DOUBLEUNDERLINE,
})

def acolor(*args, style: int = DEFAULT) -> str:
    if not args:
        raise TypeError("acolor(): need at least 1 argument")
    elif len(args) == 1:
        arg = args[0]
    else:
        arg = args

    styles = ''

    if style & BOLD:
        styles += '1'
    if style & ITALIC:
        styles += '3'
    if style & UNDERLINE:
        styles += '4'
    if style & STRIKETHROUGH:
        styles += '9'

    offset = 10 if style & BACKGROUND else 0
    style = f'\x1b[{";".join(styles)}m' if styles else ''

    if isinstance(arg, str):
        if (color := arg.strip().lower().replace(' ', '-').replace('_', '-')) in ANSI_NAMES_MAP:
            return f'{style}\x1b[{ANSI_NAMES_MAP[color] + offset}m'
        arg = arg.replace(',', ' ').split()

    if isinstance(arg, Iterable):
        color = tuple(map(int, arg))
        if len(color) == 3 and all(0 <= c <= 255 for c in color):
            return f'{style}\x1b[{38 + offset};2;{";".join(map(str, color))}m'

    raise TypeError("acolor(): the argument is invalid for ansi color")

class AnsiParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.result = []
        self.stack = 0

    def handle_starttag(self, tag, attrs):
        if tag != 'ansi':
            raise ValueError(f"unknown start-tag: {tag}")

        attrs = dict(attrs)
        color = attrs.get('color')
        styles = attrs.get('style', 'DEFAULT').replace(',', ' ').split()

        if color is None:
            color = (attrs['r'], attrs['g'], attrs['b'])

        self.result.append(acolor(color, style=reduce(or_, (STYLE_MAP[style.upper()] for style in styles))))
        self.stack += 1

    def handle_endtag(self, tag):
        if self.stack <= 0:
            raise SyntaxError(f"unmatch tag: {tag}, stack {self.stack}")
        if tag != 'ansi':
            raise ValueError(f"unknown end-tag: {tag}")

        self.result.append(acolor('reset'))
        self.stack -= 1

    def handle_data(self, data):
        self.result.append(data)

    def get_output(self):
        if self.stack != 0:
            raise SyntaxError("unmatch tag got EOF")
        return ''.join(self.result)

def fansi(string: str) -> str:
    parser = AnsiParser()
    parser.feed(string)
    return parser.get_output()