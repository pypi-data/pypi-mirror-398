from .bases import Pys
from .buffer import PysFileBuffer
from .checks import is_left_bracket, is_right_bracket, is_bracket, is_constant_keywords, is_public_attribute
from .constants import TOKENS, KEYWORDS, CONSTANT_KEYWORDS, HIGHLIGHT
from .lexer import PysLexer
from .mapping import BRACKETS_MAP
from .position import PysPosition
from .pysbuiltins import pys_builtins
from .utils.ansi import acolor
from .utils.decorators import typechecked

from html import escape as html_escape
from types import MappingProxyType
from typing import Callable, Optional

HIGHLIGHT_MAP = MappingProxyType({
    'default': '#D4D4D4',
    'keyword': '#C586C0',
    'keyword-constant': '#307CD6',
    'identifier': '#8CDCFE',
    'identifier-constant': '#2EA3FF',
    'identifier-function': '#DCDCAA',
    'identifier-type': '#4EC9B0',
    'number': '#B5CEA8',
    'string': '#CE9178',
    'brackets-0': '#FFD705',
    'brackets-1': '#D45DBA',
    'brackets-2': '#1A9FFF',
    'comment': '#549952',
    'invalid': '#B51819'
})

_builtin_types = tuple(
    name
    for name, object in pys_builtins.__dict__.items()
    if is_public_attribute(name) and isinstance(object, type)
)

_builtin_functions = tuple(
    name 
    for name, object in pys_builtins.__dict__.items()
    if is_public_attribute(name) and callable(object)
)

try:
    # if pygments module already exists
    from pygments.lexer import RegexLexer, include, bygroups
    from pygments.token import Comment, Keyword, Name, Number, Punctuation, String, Whitespace
    from pygments.unistring import xid_start, xid_continue

    _keyword_definitions = (KEYWORDS['class'], KEYWORDS['func'], KEYWORDS['function'])
    _raw_string_prefixes = r'((?:R|r|BR|RB|Br|rB|Rb|bR|br|rb))'
    _string_prefixes = r'((?:B|b)?)'
    _unicode_name = f'[{xid_start}][{xid_continue}]'

    class PygmentsPyScriptLexer(Pys, RegexLexer):

        """
        Pygments lexer for PyScript language.
        """

        name = 'PyScript'
        aliases = ['pyscript']
        filenames = ['*.pys']

        tokens = {

            'root': [
                # Whitespaces
                (r'\s+', Whitespace),

                # Punctuation
                (r'[!%&\(\)\*\+,\-\./:;<=>\?@\[\]^{\|}~\\]+', Punctuation),

                # Keywords
                (
                    r'\b(' + '|'.join(filter(lambda k: not is_constant_keywords(k), KEYWORDS)) + r')\b',
                    Keyword
                ),
                (
                    r'\b(' + '|'.join(filter(lambda k: k not in _keyword_definitions, CONSTANT_KEYWORDS)) + r')\b',
                    Keyword.Constant
                ),

                # Strings
                (
                    _raw_string_prefixes + r"(''')", 
                    bygroups(String.Affix, String.Delimiter), 
                    'raw-string-apostrophe-triple'
                ),
                (
                    _raw_string_prefixes + r'(""")', 
                    bygroups(String.Affix, String.Delimiter), 
                    'raw-string-quotation-triple'
                ),
                (
                    _string_prefixes + r"(''')", 
                    bygroups(String.Affix, String.Delimiter), 
                    'string-apostrophe-triple'
                ),
                (
                    _string_prefixes + r'(""")', 
                    bygroups(String.Affix, String.Delimiter), 
                    'string-quotation-triple'
                ),
                (
                    _raw_string_prefixes + r"(')", 
                    bygroups(String.Affix, String.Delimiter), 
                    'raw-string-apostrophe-single'
                ),
                (
                    _raw_string_prefixes + r'(")', 
                    bygroups(String.Affix, String.Delimiter), 
                    'raw-string-quotation-single'
                ),
                (
                    _string_prefixes + r"(')", 
                    bygroups(String.Affix, String.Delimiter), 
                    'string-apostrophe-single'
                ),
                (
                    _string_prefixes + r'(")', 
                    bygroups(String.Affix, String.Delimiter), 
                    'string-quotation-single'
                ),

                # Numbers
                (
                    r'0[bB][01](_?[01])*[jJiI]?',
                    Number.Bin
                ),
                (
                    r'0[oO][0-7](_?[0-7])*[jJiI]?',
                    Number.Oct
                ),
                (
                    r'0[xX][0-9a-fA-F](_?[0-9a-fA-F])*[jJiI]?',
                    Number.Hex
                ),
                (
                    r'((?:[0-9](_?[0-9])*)?\.[0-9](_?[0-9])*|[0-9](_?[0-9])*\.)([eE][+-]?[0-9](_?[0-9])*)?[jJiI]?|[0-9]'
                    r'(_?[0-9])*([eE][+-]?[0-9](_?[0-9])*)[jJiI]?',
                    Number.Float
                ),
                (
                    r'[0-9](_?[0-9])*[jJiI]?',
                    Number.Integer
                ),

                # Comments
                (
                    r'#',
                    Comment.Single,
                    'in-comment'
                ),

                # Class definition
                (
                    r'\b(' + KEYWORDS['class'] + r')\b'
                    r'(\s*)((?:\$(?:[^\S\r\n]*))?\b' + _unicode_name + r'*)\b',
                    bygroups(Keyword.Constant, Whitespace, Name.Class)
                ),

                # Function definition
                (
                    r'\b(' + KEYWORDS['func'] + '|' + KEYWORDS['function'] + r')\b' +
                    r'(\s*)((?:\$(?:[^\S\r\n]*))?\b' + _unicode_name + r'*)\b',
                    bygroups(Keyword.Constant, Whitespace, Name.Function)
                ),

                # Keywords (if that definition is unmatched)
                (
                    r'\b(' + '|'.join(_keyword_definitions) + r')\b',
                    Keyword.Constant
                ),

                # Built-in types and exceptions
                (
                    r'(?:\$(?:[^\S\r\n]*))?(?:' + '|'.join(_builtin_types) + r')\b',
                    Name.Builtin.Class
                ),

                # Built-in functions
                (
                    r'(?:\$(?:[^\S\r\n]*))?' + _unicode_name + r'*(?=\s*\()|\b(?:' +
                    '|'.join(_builtin_functions) + r')\b',
                    Name.Builtin.Function
                ),

                # Constants
                (r'(?:\$(?:[^\S\r\n]*))?\b(?:[A-Z_]*[A-Z][A-Z0-9_]*)\b', Name.Constant),

                # Variables
                (r'(?:\$(?:[^\S\r\n]*))?\b' + _unicode_name + r'*\b', Name),
            ],

            'todo-keywords': [
                (r'\b(TODO|NOTE|FIXME|BUG|HACK)\b', Keyword.Constant.Todo)
            ],

            'string-escapes': [
                (r'\\([nrtbfav\'"\n\r])', String.Escape),
                (r'\\[0-7]{1,3}}', String.Escape.Octal),
                (r'\\x[0-9A-Fa-f]{2}', String.Escape.Hex),
                (r'\\u[0-9A-Fa-f]{4}', String.Escape.Unicode),
                (r'\\U[0-9A-Fa-f]{8}', String.Escape.Unicode),
                (r'\\N\{[^}]+\}', String.Escape.UnicodeName),
                (r'\\.', String.Escape.Invalid)
            ],

            'raw-string-escapes': [
                (r'\\([\'"\n\r])', String),
                (r'\\.', String)
            ],

            'raw-string-apostrophe-triple': [
                (r"'''", String.Delimiter, '#pop'),
                include('raw-string-escapes'),
                (r'.', String)
            ],

            'raw-string-quotation-triple': [
                (r'"""', String.Delimiter, '#pop'),
                include('raw-string-escapes'),
                (r'.', String)
            ],

            'string-apostrophe-triple': [
                (r"'''", String.Delimiter, '#pop'),
                include('string-escapes'),
                include('todo-keywords'),
                (r'.', String)
            ],

            'string-quotation-triple': [
                (r'"""', String.Delimiter, '#pop'),
                include('string-escapes'),
                include('todo-keywords'),
                (r'.', String)
            ],

            'raw-string-apostrophe-single': [
                (r"'", String.Delimiter, '#pop'),
                include('raw-string-escapes'),
                (r'.', String)
            ],

            'raw-string-quotation-single': [
                (r'"', String.Delimiter, '#pop'),
                include('raw-string-escapes'),
                (r'.', String)
            ],

            'string-apostrophe-single': [
                (r"'", String.Delimiter, '#pop'),
                include('string-escapes'),
                include('todo-keywords'),
                (r'.', String)
            ],

            'string-quotation-single': [
                (r'"', String.Delimiter, '#pop'),
                include('string-escapes'),
                include('todo-keywords'),
                (r'.', String)
            ],

            'in-comment': [
                (r'$', Comment.Single, '#pop'),
                include('todo-keywords'),
                (r'.', Comment.Single),
            ]

        }

except ImportError as e:

    class PygmentsPyScriptLexer(Pys):

        def __new__(cls, *args, **kwargs):
            raise ModuleNotFoundError(f"cannot import module pygments: {e}")

@typechecked
class _PysHighlightFormatter(Pys):

    def __init__(
        self,
        content_block: Callable[[PysPosition, str], str],
        open_block: Callable[[PysPosition, str], str],
        close_block: Callable[[PysPosition, str], str],
        newline_block: Callable[[PysPosition], str]
    ) -> None:

        self.content_block = content_block
        self.open_block = open_block
        self.close_block = close_block
        self.newline_block = newline_block

        self._type = 'start'
        self._open = False

    def __call__(self, type: str, position: PysPosition, content: str) -> str:
        result = ''

        if type == 'newline':
            if self._open:
                result += self.close_block(position, self._type)
                self._open = False

            result += self.newline_block(position)

        elif type == 'end':
            if self._open:
                result += self.close_block(position, self._type)
                self._open = False

            type = 'start'

        elif type == self._type and self._open:
            result += self.content_block(position, content)

        else:
            if self._open:
                result += self.close_block(position, self._type)

            result += self.open_block(position, type) + \
                      self.content_block(position, content)

            self._open = True

        self._type = type
        return result

def _ansi_open_block(position, type):
    color = HIGHLIGHT_MAP.get(type, 'default')
    return acolor(int(color[i:i+2], 16) for i in range(1, 6, 2))

HLFMT_HTML = _PysHighlightFormatter(
    lambda position, content: '<br>'.join(html_escape(content).splitlines()),
    lambda position, type: f'<span style="color:{HIGHLIGHT_MAP.get(type, "default")}">',
    lambda position, type: '</span>',
    lambda position: '<br>'
)

HLFMT_ANSI = _PysHighlightFormatter(
    lambda position, content: content,
    _ansi_open_block,
    lambda position, type: '\x1b[0m',
    lambda position: '\n'
)

HLFMT_BBCODE = _PysHighlightFormatter(
    lambda position, content: content,
    lambda position, type: f'[color={HIGHLIGHT_MAP.get(type, "default")}]',
    lambda position, type: '[/color]',
    lambda position: '\n'
)

@typechecked
def pys_highlight(
    source,
    format: Optional[Callable[[str, PysPosition, str], str]] = None,
    max_bracket_level: int = 3
) -> str:
    """
    Highlight a PyScript code from source given.

    Parameters
    ----------
    source: A PyScript source code (tolerant of syntax errors).

    format: A function to format the code form.

    max_bracket_level: Maximum difference level of parentheses (with circular indexing).
    """

    file = PysFileBuffer(source)

    if format is None:
        format = HLFMT_HTML

    if max_bracket_level < 0:
        raise ValueError("pys_highlight(): max_bracket_level must be grather than 0")

    lexer = PysLexer(
        file=file,
        flags=HIGHLIGHT
    )

    tokens, _ = lexer.make_tokens()

    text = file.text
    result = ''
    last_index_position = 0
    bracket_level = 0
    brackets_level = {
        TOKENS['RIGHT-PARENTHESIS']: 0,
        TOKENS['RIGHT-SQUARE']: 0,
        TOKENS['RIGHT-CURLY']: 0
    }

    for i, token in enumerate(tokens):
        ttype = token.type
        tvalue = token.value

        if is_right_bracket(ttype):
            brackets_level[ttype] -= 1
            bracket_level -= 1

        if ttype == TOKENS['NULL']:
            type_fmt = 'end'

        elif ttype == TOKENS['KEYWORD']:
            type_fmt = 'keyword-constant' if is_constant_keywords(tvalue) else 'keyword'

        elif ttype == TOKENS['IDENTIFIER']:
            if tvalue in _builtin_types:
                type_fmt = 'identifier-type'
            elif tvalue in _builtin_functions:
                type_fmt = 'identifier-function'
            else:
                j = i - 1
                while j > 0 and tokens[j].type in (TOKENS['NEWLINE'], TOKENS['COMMENT']):
                    j -= 1

                previous_token = tokens[j]
                if previous_token.match(TOKENS['KEYWORD'], KEYWORDS['class']):
                    type_fmt = 'identifier-type'
                elif previous_token.matches(TOKENS['KEYWORD'], (KEYWORDS['func'], KEYWORDS['function'])):
                    type_fmt = 'identifier-function'

                else:
                    j = i + 1
                    if (j < len(tokens) and tokens[j].type == TOKENS['LEFT-PARENTHESIS']):
                        type_fmt = 'identifier-function'
                    else:
                        type_fmt = 'identifier-constant' if tvalue.isupper() else 'identifier'

        elif ttype == TOKENS['NUMBER']:
            type_fmt = 'number'

        elif ttype == TOKENS['STRING']:
            type_fmt = 'string'

        elif ttype == TOKENS['NEWLINE']:
            type_fmt = 'newline'

        elif ttype == TOKENS['COMMENT']:
            type_fmt = 'comment'

        elif is_bracket(ttype):
            type_fmt = (
                'invalid'
                if
                    brackets_level[BRACKETS_MAP.get(ttype, ttype)] < 0 or
                    bracket_level < 0
                else
                f'brackets-{bracket_level % max_bracket_level}'
            )

        elif ttype == TOKENS['NONE']:
            type_fmt = 'invalid'

        else:
            type_fmt = 'default'

        space = text[last_index_position:token.position.start]
        if space:
            result += format('default', PysPosition(file, last_index_position, token.position.start), space)

        result += format(type_fmt, token.position, text[token.position.start:token.position.end])

        if is_left_bracket(ttype):
            brackets_level[BRACKETS_MAP[ttype]] += 1
            bracket_level += 1

        elif ttype == TOKENS['NULL']:
            break

        last_index_position = token.position.end

    return result