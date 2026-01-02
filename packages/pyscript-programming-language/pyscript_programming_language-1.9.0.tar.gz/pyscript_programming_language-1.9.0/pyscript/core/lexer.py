from .bases import Pys
from .buffer import PysFileBuffer
from .checks import is_keyword
from .constants import TOKENS, DEFAULT, SILENT, HIGHLIGHT, NO_COLOR
from .context import PysContext
from .exceptions import PysTraceback
from .position import PysPosition, format_arrow
from .token import PysToken
from .utils.decorators import typechecked
from .utils.string import indent

from unicodedata import lookup as unicode_lookup
from types import MappingProxyType
from typing import Optional

import sys

ESCAPE_CHARACTERS_MAP = MappingProxyType({
    '\\': '\\',
    "'": "'",
    '"': '"',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'b': '\b',
    'f': '\f',
    'a': '\a',
    'v': '\v'
})

class PysLexer(Pys):

    @typechecked
    def __init__(
        self,
        file: PysFileBuffer,
        flags: int = DEFAULT,
        context_parent: Optional[PysContext] = None,
        context_parent_entry_position: Optional[PysPosition] = None
    ) -> None:

        self.file = file
        self.flags = flags
        self.context_parent = context_parent
        self.context_parent_entry_position = context_parent_entry_position

    def update_current_character(self):
        self.current_character = self.file.text[self.index] if 0 <= self.index < len(self.file.text) else None

    def advance(self):
        if self.error is None:
            self.index += 1
            self.update_current_character()

    def reverse(self, amount=1):
        if self.error is None:
            self.index -= amount
            self.update_current_character()

    def not_end_of_file(self):
        return self.current_character is not None and self.error is None

    def character_in(self, characters):
        return self.not_end_of_file() and self.current_character in characters

    def character_are(self, string_method, *args, **kwargs):
        return self.not_end_of_file() and getattr(self.current_character, string_method)(*args, **kwargs)

    def add_token(self, type, start=None, value=None):
        if self.error is None:

            if start is None:
                start = self.index
                end = self.index + 1
            else:
                end = self.index

            self.tokens.append(
                PysToken(
                    type,
                    PysPosition(
                        self.file,
                        start,
                        end
                    ),
                    value
                )
            )

    def warning(self, message):
        if not (self.flags & SILENT or self.flags & HIGHLIGHT or message in self.warnings):
            print(message, file=sys.stderr)
            self.warnings.add(message)

    def throw(self, start, end, message, add_token=True):
        if self.error is None:

            if self.flags & HIGHLIGHT:
                if add_token:
                    self.add_token(TOKENS['NONE'], start)

            else:
                self.current_character = None
                self.tokens = []
                self.error = PysTraceback(
                    SyntaxError(message),
                    PysContext(
                        file=self.file,
                        flags=self.flags,
                        parent=self.context_parent,
                        parent_entry_position=self.context_parent_entry_position
                    ),
                    PysPosition(self.file, start, end)
                )

    @typechecked
    def make_tokens(self) -> tuple[tuple[PysToken, ...] | tuple[PysToken], PysTraceback | None]:
        self.index = 0
        self.tokens = []
        self.warnings = set()
        self.error = None

        self.update_current_character()

        while self.not_end_of_file():

            if self.current_character == '\n':
                self.add_token(TOKENS['NEWLINE'])
                self.advance()

            elif self.current_character == '\\':
                self.make_back_slash()

            elif self.character_are('isspace'):
                self.advance()

            elif self.character_in('0123456789.'):
                self.make_number()

            elif self.character_in('BRbr"\''):
                self.make_string()

            elif self.character_are('isidentifier') or self.current_character == '$':
                self.make_identifier()

            elif self.current_character == '+':
                self.make_plus()

            elif self.current_character == '-':
                self.make_minus()

            elif self.current_character == '*':
                self.make_star()

            elif self.current_character == '/':
                self.make_slash()

            elif self.current_character == '%':
                self.make_percent()

            elif self.current_character == '@':
                self.make_at()

            elif self.current_character == '&':
                self.make_ampersand()

            elif self.current_character == '|':
                self.make_pipe()

            elif self.current_character == '^':
                self.make_circumflex()

            elif self.current_character == '~':
                self.make_tilde()

            elif self.current_character == '=':
                self.make_equal()

            elif self.current_character == '!':
                self.make_exclamation()

            elif self.current_character == '<':
                self.make_less_than()

            elif self.current_character == '>':
                self.make_greater_than()

            elif self.current_character == '?':
                self.make_question()

            elif self.current_character == ':':
                self.make_colon()

            elif self.current_character == '#':
                self.make_comment()

            elif self.current_character == '(':
                self.add_token(TOKENS['LEFT-PARENTHESIS'])
                self.advance()

            elif self.current_character == ')':
                self.add_token(TOKENS['RIGHT-PARENTHESIS'])
                self.advance()

            elif self.current_character == '[':
                self.add_token(TOKENS['LEFT-SQUARE'])
                self.advance()

            elif self.current_character == ']':
                self.add_token(TOKENS['RIGHT-SQUARE'])
                self.advance()

            elif self.current_character == '{':
                self.add_token(TOKENS['LEFT-CURLY'])
                self.advance()

            elif self.current_character == '}':
                self.add_token(TOKENS['RIGHT-CURLY'])
                self.advance()

            elif self.current_character == ',':
                self.add_token(TOKENS['COMMA'])
                self.advance()

            elif self.current_character == ';':
                self.add_token(TOKENS['SEMICOLON'])
                self.advance()

            else:
                char = self.current_character
                unicode = ord(char)

                self.advance()
                self.throw(
                    self.index - 1, self.index,
                    f"invalid character '{char}' (U+{unicode:04X})"
                    if char.isprintable() else
                    f"invalid non-printable character U+{unicode:04X}"
                )

        self.add_token(TOKENS['NULL'])

        return tuple(self.tokens), self.error

    def make_back_slash(self):
        self.advance()

        if self.current_character != '\n':
            self.throw(self.index, self.index + 1, "expected newline character")

        self.advance()

    def make_number(self):
        start = self.index

        if self.current_character == '.':
            self.advance()

            if self.file.text[self.index:self.index + 2] == '..':
                self.advance()
                self.advance()
                self.add_token(TOKENS['TRIPLE-DOT'], start)
                return

            elif not self.character_in('0123456789'):
                self.add_token(TOKENS['DOT'], start)
                return

            format = float
            number = '.'

        else:
            format = int
            number = ''

        is_scientific = False
        is_complex = False
        is_underscore = False

        while self.character_in('0123456789'):
            number += self.current_character
            self.advance()

            is_underscore = False

            if self.current_character == '_':
                is_underscore = True
                self.advance()

            elif self.current_character == '.' and not is_scientific and format is int:
                format = float
                number += '.'
                self.advance()

            elif self.character_in('BOXbox') and not is_scientific:
                if number != '0':
                    self.throw(start, self.index, "invalid decimal literal")
                    return

                format = str
                number = ''

                character_base = self.character_are('lower')

                if character_base == 'b':
                    base = 2
                    literal = '01'
                elif character_base == 'o':
                    base = 8
                    literal = '01234567'
                elif character_base == 'x':
                    base = 16
                    literal = '0123456789ABCDEFabcdef'

                self.advance()

                while self.character_in(literal):
                    number += self.current_character
                    self.advance()

                    is_underscore = False

                    if self.current_character == '_':
                        is_underscore = True
                        self.advance()

                if not number:
                    self.advance()
                    self.throw(self.index - 1, self.index, "invalid decimal literal")
                    return

                break

            elif self.character_in('eE') and not is_scientific:
                format = float
                is_scientific = True

                number += 'e'
                self.advance()

                if self.character_in('+-'):
                    number += self.current_character
                    self.advance()

        if is_underscore or (is_scientific and number.endswith(('e', '-', '+'))):
            self.advance()
            self.throw(self.index - 1, self.index, "invalid decimal literal")
            return

        if self.character_in('jJiI'):
            is_complex = True
            self.advance()

        if format is float:
            result = float(number)
        elif format is str:
            result = int(number, base)
        elif format is int:
            result = int(number)

        self.add_token(TOKENS['NUMBER'], start, complex(0, result) if is_complex else result)

    def make_string(self):
        start = self.index

        is_bytes = False
        is_raw = False

        if self.character_in('BRbr'):
            prefix = ''

            while self.character_in('BRbr') and len(prefix) < 2:
                prefix += self.current_character.lower()
                self.advance()

            count_r = prefix.count('r')
            count_b = prefix.count('b')

            if count_r <= 1 and count_b <= 1 and self.character_in('"\''):
                is_raw = count_r == 1
                is_bytes = count_b == 1
            else:
                self.reverse(self.index - start)
                self.make_identifier()
                return

        string = ''
        prefix = self.current_character
        triple_prefix = prefix * 3

        def triple_quote():
            return self.file.text[self.index:self.index + 3] == triple_prefix

        is_triple_quote = triple_quote()
        decoded_error_message = None

        def decode_error(is_unicode_error, start, end, message):
            nonlocal decoded_error_message
            if decoded_error_message is None:
                decoded_error_message = (
                    f"(unicode error) 'unicodeescape' codec can't decode bytes in position {start}-{end}: {message}"
                    if is_unicode_error else
                    f"codec can't decode bytes in position {start}-{end}: {message}"
                )

        if is_triple_quote:
            end = triple_quote
            end_prefix = triple_quote
        else:
            terminated_string = prefix + '\n'
            def end():
                return self.character_in(terminated_string)
            def end_prefix():
                return self.current_character == prefix

        self.advance()
        start_string = self.index

        if is_triple_quote:
            self.advance()
            self.advance()
            start_string = self.index

        while self.not_end_of_file() and not end():

            if self.current_character == '\\':
                start_escape = self.index - start_string

                self.advance()

                if is_raw:
                    string += '\\'

                    if self.character_in('\\\'"\n'):
                        string += self.current_character
                        self.advance()

                elif self.character_in('\\\'"nrtbfav\n'):
                    if escape_character := ESCAPE_CHARACTERS_MAP.get(self.current_character):
                        string += escape_character
                    self.advance()

                elif decoded_error_message is None:
                    escape = ''

                    if self.character_in('01234567'):

                        while self.character_in('01234567') and len(escape) < 3:
                            escape += self.current_character
                            self.advance()

                        string += chr(int(escape, 8))

                    elif self.character_in('xuU'):
                        base = self.current_character

                        if base == 'x':
                            length = 2
                        elif base == 'u':
                            length = 4
                        elif base == 'U':
                            length = 8

                        end_escape = self.index - start_string
                        self.advance()

                        while self.character_in('0123456789ABCDEFabcdef') and len(escape) < length:
                            escape += self.current_character
                            self.advance()

                        if len(escape) != length:
                            decode_error(
                                False, start_escape, end_escape,
                                f"truncated \\{base}{'X' * length} escape"
                            )

                        else:
                            try:
                                string += chr(int(escape, 16))
                            except (ValueError, OverflowError):
                                decode_error(
                                    False, start_escape, self.index - start_string,
                                    "illegal Unicode character"
                                )

                    elif self.current_character == 'N':
                        end_escape = self.index - start_string
                        self.advance()

                        if self.current_character != '{':
                            decode_error(
                                True, start_escape, end_escape,
                                "malformed \\N character escape"
                            )
                            continue

                        self.advance()

                        while self.not_end_of_file() and self.current_character != '}':
                            escape += self.current_character
                            self.advance()

                        if self.current_character == '}':
                            try:
                                string += unicode_lookup(escape)
                            except KeyError:
                                decode_error(
                                    True, start_escape, self.index - start_string,
                                    "unknown Unicode character name"
                                )

                            self.advance()

                        else:
                            decode_error(
                                True, start_escape, end_escape,
                                "malformed \\N character escape"
                            )

                    else:
                        if not self.not_end_of_file():
                            string += '\\'
                            break

                        position = PysPosition(self.file, self.index, self.index + 1)
                        character = self.current_character

                        string += '\\' + character
                        self.warning(
                            f"{self.file.name}:{position.start_line}:{position.start_column + 1}: "
                            f"SyntaxWarning: \"\\{character}\" "
                            "is an invalid escape sequence. Such sequences will not work in the future. Did you mean "
                            f"\"\\\\{character}\"? A raw string is also an option.\n" +
                            indent(format_arrow(position, not (self.flags & NO_COLOR)), 2)
                        )
                        self.advance()

            else:
                string += self.current_character
                self.advance()

        if not end_prefix():
            self.throw(
                start, start_string,
                "unterminated bytes literal" if is_bytes else "unterminated string literal",
                add_token=False
            )

        else:
            self.advance()
            if is_triple_quote:
                self.advance()
                self.advance()

            if decoded_error_message is not None:
                self.throw(start, self.index, decoded_error_message, add_token=False)
            elif is_bytes:
                try:
                    string = string.encode('latin-1')
                except UnicodeEncodeError:
                    self.throw(start, self.index, "invalid bytes literal", add_token=False)

        self.add_token(TOKENS['STRING'], start, string)

    def make_identifier(self):
        start = self.index
        identifier = False

        if self.current_character == '$':
            identifier = True
            self.advance()

            while self.not_end_of_file() and self.current_character != '\n' and self.character_are('isspace'):
                self.advance()

            if not self.character_are('isidentifier'):
                self.advance()
                self.throw(self.index - 1, self.index, "expected identifier")
                return

        name = ''

        while self.not_end_of_file() and (name + self.current_character).isidentifier():
            name += self.current_character
            self.advance()

        self.add_token(
            TOKENS['KEYWORD'] if not identifier and is_keyword(name) else TOKENS['IDENTIFIER'],
            start,
            name
        )

    def make_plus(self):
        start = self.index
        type = TOKENS['PLUS']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-PLUS']
            self.advance()

        elif self.current_character == '+':
            type = TOKENS['DOUBLE-PLUS']
            self.advance()

        self.add_token(type, start)

    def make_minus(self):
        start = self.index
        type = TOKENS['MINUS']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-MINUS']
            self.advance()

        elif self.current_character == '-':
            type = TOKENS['DOUBLE-MINUS']
            self.advance()

        self.add_token(type, start)

    def make_star(self):
        start = self.index
        type = TOKENS['STAR']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-STAR']
            self.advance()

        elif self.current_character == '*':
            type = TOKENS['DOUBLE-STAR']
            self.advance()

            if self.current_character == '=':
                type = TOKENS['EQUAL-DOUBLE-STAR']
                self.advance()

        self.add_token(type, start)

    def make_slash(self):
        start = self.index
        type = TOKENS['SLASH']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-SLASH']
            self.advance()

        elif self.current_character == '/':
            type = TOKENS['DOUBLE-SLASH']
            self.advance()

            if self.current_character == '=':
                type = TOKENS['EQUAL-DOUBLE-SLASH']
                self.advance()

        self.add_token(type, start)

    def make_percent(self):
        start = self.index
        type = TOKENS['PERCENT']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-PERCENT']
            self.advance()

        self.add_token(type, start)

    def make_at(self):
        start = self.index
        type = TOKENS['AT']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-AT']
            self.advance()

        self.add_token(type, start)

    def make_ampersand(self):
        start = self.index
        type = TOKENS['AMPERSAND']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-AMPERSAND']
            self.advance()

        elif self.current_character == '&':
            type = TOKENS['DOUBLE-AMPERSAND']
            self.advance()

        self.add_token(type, start)

    def make_pipe(self):
        start = self.index
        type = TOKENS['PIPE']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-PIPE']
            self.advance()

        elif self.current_character == '|':
            type = TOKENS['DOUBLE-PIPE']
            self.advance()

        self.add_token(type, start)

    def make_circumflex(self):
        start = self.index
        type = TOKENS['CIRCUMFLEX']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-CIRCUMFLEX']
            self.advance()

        self.add_token(type, start)

    def make_tilde(self):
        start = self.index
        type = TOKENS['TILDE']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-TILDE']
            self.advance()

        elif self.current_character == '!':
            type = TOKENS['EXCLAMATION-TILDE']
            self.advance()

        self.add_token(type, start)

    def make_equal(self):
        start = self.index
        type = TOKENS['EQUAL']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['DOUBLE-EQUAL']
            self.advance()

        elif self.current_character == '>':
            type = TOKENS['EQUAL-ARROW']
            self.advance()

        self.add_token(type, start)

    def make_exclamation(self):
        start = self.index
        type = TOKENS['EXCLAMATION']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-EXCLAMATION']
            self.advance()

        self.add_token(type, start)

    def make_less_than(self):
        start = self.index
        type = TOKENS['LESS-THAN']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-LESS-THAN']
            self.advance()

        elif self.current_character == '<':
            type = TOKENS['DOUBLE-LESS-THAN']
            self.advance()

            if self.current_character == '=':
                type = TOKENS['EQUAL-DOUBLE-LESS-THAN']
                self.advance()

        self.add_token(type, start)

    def make_greater_than(self):
        start = self.index
        type = TOKENS['GREATER-THAN']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-GREATER-THAN']
            self.advance()

        elif self.current_character == '>':
            type = TOKENS['DOUBLE-GREATER-THAN']
            self.advance()

            if self.current_character == '=':
                type = TOKENS['EQUAL-DOUBLE-GREATER-THAN']
                self.advance()

        self.add_token(type, start)

    def make_question(self):
        start = self.index
        type = TOKENS['QUESTION']

        self.advance()

        if self.current_character == '?':
            type = TOKENS['DOUBLE-QUESTION']
            self.advance()

        self.add_token(type, start)

    def make_colon(self):
        start = self.index
        type = TOKENS['COLON']

        self.advance()

        if self.current_character == '=':
            type = TOKENS['EQUAL-COLON']
            self.advance()

        self.add_token(type, start)

    def make_comment(self):
        start = self.index
        comment = ''

        self.advance()

        while self.not_end_of_file() and self.current_character != '\n':
            comment += self.current_character
            self.advance()

        if self.flags & HIGHLIGHT:
            self.add_token(TOKENS['COMMENT'], start, comment)