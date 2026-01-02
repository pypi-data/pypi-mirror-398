from .bases import Pys
from .checks import is_left_bracket, is_right_bracket
from .constants import TOKENS, KEYWORDS, DEFAULT, REVERSE_POW_XOR
from .context import PysContext
from .exceptions import PysTraceback
from .mapping import BRACKETS_MAP
from .nodes import *
from .position import PysPosition
from .results import PysParserResult
from .token import PysToken
from .utils.decorators import typechecked
from .utils.generic import setimuattr

from types import MappingProxyType
from typing import Optional, Callable

BRACKETS_ITERABLE_MAP = MappingProxyType({
    'dict': TOKENS['LEFT-CURLY'],
    'set': TOKENS['LEFT-CURLY'],
    'list': TOKENS['LEFT-SQUARE'],
    'tuple': TOKENS['LEFT-PARENTHESIS']
})

NODE_ITERABLE_MAP = MappingProxyType({
    'dict': PysDictionaryNode,
    'set': PysSetNode,
    'list': PysListNode,
    'tuple': PysTupleNode
})

class PysParser(Pys):

    @typechecked
    def __init__(
        self,
        tokens: tuple[PysToken, ...] | tuple[PysToken],
        flags: int = DEFAULT,
        context_parent: Optional[PysContext] = None,
        context_parent_entry_position: Optional[PysPosition] = None
    ) -> None:

        self.tokens = tokens
        self.flags = flags
        self.context = context_parent
        self.context_parent_entry_position = context_parent_entry_position

    def update_current_token(self):
        if 0 <= self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]

    def advance(self):
        self.token_index += 1
        self.update_current_token()

    def reverse(self, amount=1):
        self.token_index -= amount
        self.update_current_token()

    def new_error(self, message, position=None):
        return PysTraceback(
            SyntaxError(message),
            PysContext(
                file=self.current_token.position.file,
                flags=self.flags,
                parent=self.context,
                parent_entry_position=self.context_parent_entry_position
            ),
            position or self.current_token.position
        )

    @typechecked
    def parse(self, func: Optional[Callable[[], PysParserResult]] = None) -> PysParserResult:
        self.token_index = 0
        self.bracket_level = 0

        self.update_current_token()

        result = (func or self.statements)()

        if not result.error:
            if is_right_bracket(self.current_token.type):
                return result.failure(self.new_error(f"unmatched {chr(self.current_token.type)!r}"))
            elif self.current_token.type != TOKENS['NULL']:
                return result.failure(self.new_error("invalid syntax"))

        return result

    def statements(self):
        result = PysParserResult()
        start = self.current_token.position.start

        statements = []
        more_statements = True
        bracket_level = self.bracket_level

        self.bracket_level = 0

        while True:
            advance_count = self.skip(result, (TOKENS['NEWLINE'], TOKENS['SEMICOLON']))

            if not more_statements:
                if advance_count == 0:
                    break
                more_statements = True

            statement = result.try_register(self.statement())
            if result.error:
                return result

            if statement:
                statements.append(statement)
            else:
                self.reverse(result.to_reverse_count)

            more_statements = False

        self.bracket_level = bracket_level

        return result.success(
            PysStatementsNode(
                statements,
                PysPosition(
                    self.current_token.position.file,
                    start,
                    self.current_token.position.end
                )
            )
        )

    def statement(self):
        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['from']):
            return self.from_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['import']):
            return self.import_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['if']):
            return self.if_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['switch']):
            return self.switch_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['try']):
            return self.try_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['with']):
            return self.with_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['for']):
            return self.for_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['while']):
            return self.while_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['do']):
            return self.do_while_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['class']):
            return self.class_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['return']):
            return self.return_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['global']):
            return self.global_expr()

        elif self.current_token.matches(TOKENS['KEYWORD'], (KEYWORDS['del'], KEYWORDS['delete'])):
            return self.del_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['throw']):
            return self.throw_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['assert']):
            return self.assert_expr()

        elif self.current_token.type == TOKENS['AT']:
            return self.decorator_expr()

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['continue']):
            result = PysParserResult()
            position = self.current_token.position

            result.register_advancement()
            self.advance()

            return result.success(PysContinueNode(position))

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['break']):
            result = PysParserResult()
            position = self.current_token.position

            result.register_advancement()
            self.advance()

            return result.success(PysBreakNode(position))

        result = PysParserResult()

        assign_expr = result.register(self.assign_expr())
        if result.error:
            return result.failure(self.new_error("expected an expression or statement"), fatal=False)

        return result.success(assign_expr)

    def expr(self):
        result = PysParserResult()

        node = result.register(self.single_expr())
        if result.error:
            return result

        if self.current_token.type == TOKENS['COMMA']:
            elements = [node]

            while self.current_token.type == TOKENS['COMMA']:
                result.register_advancement()
                self.advance()
                self.skip_expr(result)

                element = result.try_register(self.single_expr())
                if result.error:
                    return result

                if element:
                    elements.append(element)
                else:
                    self.reverse(result.to_reverse_count)
                    break

            self.skip_expr(result)

            node = PysTupleNode(
                elements,
                PysPosition(
                    self.current_token.position.file,
                    node.position.start,
                    elements[-1].position.end
                )
            )

        return result.success(node)

    def walrus(self):
        result = PysParserResult()

        node = result.register(self.single_expr())
        if result.error:
            return result

        if self.current_token.type == TOKENS['EQUAL-COLON']:
            operand = self.current_token

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            value = result.register(self.single_expr(), True)
            if result.error:
                return result

            node = PysAssignNode(node, operand, value)

        return result.success(node)

    def single_expr(self):
        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['match']):
            return self.match_expr()

        elif self.current_token.matches(
            TOKENS['KEYWORD'],
            (KEYWORDS['func'], KEYWORDS['function'], KEYWORDS['constructor'])
        ):
            return self.func_expr()

        return self.ternary()

    def ternary(self):
        result = PysParserResult()

        node = result.register(self.nullish())
        if result.error:
            return result

        if self.current_token.type == TOKENS['QUESTION']:
            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            valid = result.register(self.ternary(), True)
            if result.error:
                return result

            if self.current_token.type != TOKENS['COLON']:
                return result.failure(self.new_error("expected ':'"))

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            invalid = result.register(self.ternary(), True)
            if result.error:
                return result

            node = PysTernaryOperatorNode(
                node,
                valid,
                invalid,
                style='general'
            )

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['if']):
            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            condition = result.register(self.ternary(), True)
            if result.error:
                return result

            if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['else']):
                return result.failure(self.new_error(f"expected {KEYWORDS['else']!r}"))

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            invalid = result.register(self.ternary(), True)
            if result.error:
                return result

            node = PysTernaryOperatorNode(
                condition,
                node,
                invalid,
                style='pythonic'
            )

        return result.success(node)

    def nullish(self):
        return self.binary_operator(self.logic, (TOKENS['DOUBLE-QUESTION'],))

    def logic(self):
        return self.binary_operator(
            self.member,
            (
                (TOKENS['KEYWORD'], KEYWORDS['and']),
                (TOKENS['KEYWORD'], KEYWORDS['or']),
                TOKENS['DOUBLE-AMPERSAND'], TOKENS['DOUBLE-PIPE']
            )
        )

    def member(self):
        return self.chain_operator(
            self.comp,
            (
                (TOKENS['KEYWORD'], KEYWORDS['in']),
                (TOKENS['KEYWORD'], KEYWORDS['is']),
                (TOKENS['KEYWORD'], KEYWORDS['not'])
            ),
            is_member=True
        )

    def comp(self):
        token = self.current_token

        if token.match(TOKENS['KEYWORD'], KEYWORDS['not']) or token.type == TOKENS['EXCLAMATION']:
            result = PysParserResult()

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            node = result.register(self.comp(), True)
            if result.error:
                return result

            return result.success(
                PysUnaryOperatorNode(
                    token,
                    node,
                    operand_position='left'
                )
            )

        return self.chain_operator(
            self.bitwise,
            (
                TOKENS['DOUBLE-EQUAL'], TOKENS['EQUAL-EXCLAMATION'], TOKENS['EQUAL-TILDE'], TOKENS['EXCLAMATION-TILDE'],
                TOKENS['LESS-THAN'], TOKENS['GREATER-THAN'], TOKENS['EQUAL-LESS-THAN'], TOKENS['EQUAL-GREATER-THAN']
            )
        )

    def bitwise(self):
        return self.binary_operator(
            self.arith,
            (
                TOKENS['AMPERSAND'], TOKENS['PIPE'],
                TOKENS['DOUBLE-STAR'] if self.flags & REVERSE_POW_XOR else TOKENS['CIRCUMFLEX'],
                TOKENS['DOUBLE-LESS-THAN'], TOKENS['DOUBLE-GREATER-THAN']
            ),
            is_bitwise=True
        )

    def arith(self):
        return self.binary_operator(self.term, (TOKENS['PLUS'], TOKENS['MINUS']))

    def term(self):
        return self.binary_operator(
            self.factor,
            (TOKENS['STAR'], TOKENS['SLASH'], TOKENS['DOUBLE-SLASH'], TOKENS['PERCENT'], TOKENS['AT'])
        )

    def factor(self):
        token = self.current_token

        if token.type in (TOKENS['PLUS'], TOKENS['MINUS'], TOKENS['TILDE']):
            result = PysParserResult()

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            node = result.register(self.factor(), True)
            if result.error:
                return result

            return result.success(
                PysUnaryOperatorNode(
                    token,
                    node,
                    operand_position='left'
                )
            )

        return self.power()

    def power(self):
        result = PysParserResult()

        left = result.register(self.incremental())
        if result.error:
            return result

        reverse_pow_xor = self.flags & REVERSE_POW_XOR

        if self.current_token.type == (TOKENS['CIRCUMFLEX'] if reverse_pow_xor else TOKENS['DOUBLE-STAR']):
            operand = (
                PysToken(
                    TOKENS['DOUBLE-STAR'],
                    self.current_token.position,
                    'reversed'
                )
                if reverse_pow_xor else
                self.current_token
            )

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            right = result.register(self.factor(), True)
            if result.error:
                return result

            left = PysBinaryOperatorNode(left, operand, right)

        return result.success(left)

    def incremental(self):
        result = PysParserResult()
        token = self.current_token

        if token.type in (TOKENS['DOUBLE-PLUS'], TOKENS['DOUBLE-MINUS']):
            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            node = result.register(self.primary())
            if result.error:
                return result

            return result.success(
                PysUnaryOperatorNode(
                    token,
                    node,
                    operand_position='left'
                )
            )

        node = result.register(self.primary())
        if result.error:
            return result

        if self.current_token.type in (TOKENS['DOUBLE-PLUS'], TOKENS['DOUBLE-MINUS']):
            operand = self.current_token

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            node = PysUnaryOperatorNode(
                operand,
                node,
                operand_position='right'
            )

        return result.success(node)

    def primary(self):
        result = PysParserResult()
        start = self.current_token.position.start

        node = result.register(self.atom())
        if result.error:
            return result

        while self.current_token.type in (
            TOKENS['LEFT-PARENTHESIS'],
            TOKENS['LEFT-SQUARE'],
            TOKENS['DOT']
        ):

            if self.current_token.type == TOKENS['LEFT-PARENTHESIS']:
                left_bracket_token = self.current_token
                self.bracket_level += 1

                result.register_advancement()
                self.advance()
                self.skip(result)

                seen_keyword_argument = False
                arguments = []

                while not is_right_bracket(self.current_token.type):

                    argument_or_keyword = result.register(self.walrus(), True)
                    if result.error:
                        return result

                    if self.current_token.type == TOKENS['EQUAL']:
                        if not isinstance(argument_or_keyword, PysIdentifierNode):
                            return result.failure(
                                self.new_error("expected identifier (before '=')", argument_or_keyword.position)
                            )

                        result.register_advancement()
                        self.advance()
                        self.skip(result)
                        seen_keyword_argument = True

                    elif seen_keyword_argument:
                        return result.failure(self.new_error("expected '=' (follows keyword argument)"))

                    if seen_keyword_argument:
                        value = result.register(self.single_expr(), True)
                        if result.error:
                            return result
                        arguments.append((argument_or_keyword.name, value))
                    else:
                        arguments.append(argument_or_keyword)

                    self.skip(result)

                    if self.current_token.type == TOKENS['COMMA']:
                        result.register_advancement()
                        self.advance()
                        self.skip(result)

                    elif not is_right_bracket(self.current_token.type):
                        return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

                end = self.current_token.position.end
                self.close_bracket(result, left_bracket_token)
                if result.error:
                    return result

                self.bracket_level -= 1
                self.skip_expr(result)

                node = PysCallNode(
                    node,
                    arguments,
                    PysPosition(
                        self.current_token.position.file,
                        start,
                        end
                    )
                )

            elif self.current_token.type == TOKENS['LEFT-SQUARE']:
                left_bracket_token = self.current_token
                self.bracket_level += 1

                index = 0
                slices = []
                indices = [None, None, None]
                single_slice = True

                result.register_advancement()
                self.advance()
                self.skip(result)

                if self.current_token.type != TOKENS['COLON']:
                    indices[0] = result.register(self.walrus(), True)
                    if result.error:
                        return result

                    if self.current_token.type == TOKENS['COMMA']:
                        result.register_advancement()
                        self.advance()
                        self.skip(result)
                        single_slice = False

                if not single_slice or is_right_bracket(self.current_token.type):
                    slices.append(indices[0])
                    indices = [None, None, None]

                while not is_right_bracket(self.current_token.type):

                    if self.current_token.type != TOKENS['COLON']:
                        indices[index] = result.register(self.walrus(), True)
                        if result.error:
                            return result

                    index += 1
                    single_index = self.current_token.type != TOKENS['COLON']

                    while index < 3 and self.current_token.type == TOKENS['COLON']:
                        result.register_advancement()
                        self.advance()
                        self.skip(result)

                        if is_right_bracket(self.current_token.type):
                            break

                        indices[index] = result.try_register(self.walrus())
                        if result.error:
                            return result

                        self.skip(result)
                        index += 1

                    if single_index:
                        slices.append(indices[0])
                    else:
                        slices.append(slice(indices[0], indices[1], indices[2]))

                    indices = [None, None, None]
                    index = 0

                    if self.current_token.type == TOKENS['COMMA']:
                        result.register_advancement()
                        self.advance()
                        self.skip(result)
                        single_slice = False

                    elif not is_right_bracket(self.current_token.type):
                        return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

                end = self.current_token.position.end
                self.close_bracket(result, left_bracket_token)
                if result.error:
                    return result

                self.bracket_level -= 1
                self.skip_expr(result)

                if single_slice:
                    slices = slices[0]

                node = PysSubscriptNode(
                    node,
                    slices,
                    PysPosition(
                        self.current_token.position.file,
                        start,
                        end
                    )
                )

            elif self.current_token.type == TOKENS['DOT']:
                result.register_advancement()
                self.advance()
                self.skip_expr(result)

                attribute = self.current_token

                if attribute.type != TOKENS['IDENTIFIER']:
                    return result.failure(self.new_error("expected identifier"))

                result.register_advancement()
                self.advance()
                self.skip_expr(result)

                node = PysAttributeNode(node, attribute)

        return result.success(node)

    def atom(self):
        result = PysParserResult()
        token = self.current_token

        if token.matches(
            TOKENS['KEYWORD'],
            (
                KEYWORDS['__debug__'], KEYWORDS['True'], KEYWORDS['False'], KEYWORDS['None'], KEYWORDS['true'],
                KEYWORDS['false'], KEYWORDS['none']
            )
        ):
            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            return result.success(PysKeywordNode(token))

        elif token.type == TOKENS['IDENTIFIER']:
            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            return result.success(PysIdentifierNode(token))

        elif token.type == TOKENS['NUMBER']:
            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            return result.success(PysNumberNode(token))

        elif token.type == TOKENS['STRING']:
            format = type(token.value)
            string = '' if format is str else b''

            while self.current_token.type == TOKENS['STRING']:

                if not isinstance(self.current_token.value, format):
                    return result.failure(
                        self.new_error(
                            "cannot mix bytes and nonbytes literals",
                            self.current_token.position
                        )
                    )

                string += self.current_token.value
                end = self.current_token.position.end

                result.register_advancement()
                self.advance()
                self.skip_expr(result)

            return result.success(
                PysStringNode(
                    PysToken(
                        TOKENS['STRING'],
                        PysPosition(
                            self.current_token.position.file,
                            token.position.start,
                            end
                        ),
                        string
                    )
                )
            )

        elif token.type == TOKENS['LEFT-PARENTHESIS']:
            return self.sequence_expr('tuple')

        elif token.type == TOKENS['LEFT-SQUARE']:
            return self.sequence_expr('list')

        elif token.type == TOKENS['LEFT-CURLY']:
            dict_expr = result.try_register(self.sequence_expr('dict'))
            if result.error:
                return result

            if not dict_expr:
                self.reverse(result.to_reverse_count)
                return self.sequence_expr('set')

            return result.success(dict_expr)

        elif token.type == TOKENS['TRIPLE-DOT']:
            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            return result.success(PysEllipsisNode(token.position))

        return result.failure(self.new_error("expected expression"), fatal=False)

    def sequence_expr(self, type, should_sequence=False):
        result = PysParserResult()
        start = self.current_token.position.start
        left_bracket = BRACKETS_ITERABLE_MAP[type]

        if self.current_token.type != left_bracket:
            return result.failure(self.new_error(f"expected {chr(left_bracket)!r}"))

        left_bracket_token = self.current_token
        self.bracket_level += 1

        result.register_advancement()
        self.advance()
        self.skip(result)

        elements = []

        if type == 'dict':
            always_dict = False

            while not is_right_bracket(self.current_token.type):
                key = result.register(self.single_expr(), True)
                if result.error:
                    return result

                self.skip(result)

                if self.current_token.type != TOKENS['COLON']:
                    if not always_dict:
                        self.bracket_level -= 1
                    return result.failure(self.new_error("expected ':'"), fatal=always_dict)

                result.register_advancement()
                self.advance()
                self.skip(result)

                value = result.register(self.single_expr(), True)
                if result.error:
                    return result

                elements.append((key, value))
                always_dict = True

                if self.current_token.type == TOKENS['COMMA']:
                    result.register_advancement()
                    self.advance()
                    self.skip(result)

                elif not is_right_bracket(self.current_token.type):
                    return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

        else:

            while not is_right_bracket(self.current_token.type):
                elements.append(result.register(self.walrus(), True))
                if result.error:
                    return result

                self.skip(result)

                if self.current_token.type == TOKENS['COMMA']:
                    result.register_advancement()
                    self.advance()
                    self.skip(result)
                    should_sequence = True

                elif not is_right_bracket(self.current_token.type):
                    return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

        end = self.current_token.position.end
        self.close_bracket(result, left_bracket_token)
        if result.error:
            return result

        self.bracket_level -= 1
        self.skip_expr(result)

        if type == 'tuple' and not should_sequence and elements:
            element = elements[0]
            setimuattr(
                element, 'position',
                PysPosition(
                    self.current_token.position.file,
                    start,
                    end
                )
            )

            return result.success(element)

        return result.success(
            NODE_ITERABLE_MAP[type](
                elements,
                PysPosition(
                    self.current_token.position.file,
                    start,
                    end
                )
            )
        )

    def assign_expr(self):
        result = PysParserResult()

        node = result.register(self.expr())
        if result.error:
            return result

        if self.current_token.type in (
            TOKENS['EQUAL'],
            TOKENS['EQUAL-PLUS'],
            TOKENS['EQUAL-MINUS'],
            TOKENS['EQUAL-STAR'],
            TOKENS['EQUAL-SLASH'],
            TOKENS['EQUAL-DOUBLE-SLASH'],
            TOKENS['EQUAL-PERCENT'],
            TOKENS['EQUAL-AT'],
            TOKENS['EQUAL-DOUBLE-STAR'],
            TOKENS['EQUAL-AMPERSAND'],
            TOKENS['EQUAL-PIPE'],
            TOKENS['EQUAL-CIRCUMFLEX'],
            TOKENS['EQUAL-DOUBLE-LESS-THAN'],
            TOKENS['EQUAL-DOUBLE-GREATER-THAN']
        ):
            operand = (
                PysToken(
                    TOKENS['EQUAL-DOUBLE-STAR']
                    if self.current_token.type == TOKENS['EQUAL-CIRCUMFLEX'] else
                    TOKENS['EQUAL-CIRCUMFLEX'],
                    self.current_token.position,
                    'reversed'
                )
                if 
                    self.flags & REVERSE_POW_XOR and
                    self.current_token.type in (TOKENS['EQUAL-DOUBLE-STAR'], TOKENS['EQUAL-CIRCUMFLEX'])
                else
                self.current_token
            )

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            value = result.register(self.assign_expr(), True)
            if result.error:
                return result

            node = PysAssignNode(node, operand, value)

        return result.success(node)

    def from_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['from']):
            return result.failure(self.new_error(f"expected {KEYWORDS['from']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        if self.current_token.type not in (TOKENS['STRING'], TOKENS['IDENTIFIER']):
            return result.failure(self.new_error("expected string or identifier"))

        name = self.current_token

        result.register_advancement()
        self.advance()
        self.skip(result)

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['import']):
            return result.failure(self.new_error(f"expected {KEYWORDS['import']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        if self.current_token.type == TOKENS['STAR']:
            result.register_advancement()
            self.advance()
            packages = 'all'

        else:
            bracket = False
            packages = []

            if self.current_token.type == TOKENS['LEFT-PARENTHESIS']:
                bracket = True
                left_bracket_token = self.current_token
                self.bracket_level += 1

                result.register_advancement()
                self.advance()
                self.skip(result)

            elif is_left_bracket(self.current_token.type):
                return result.failure(self.new_error(f"expected '(' not {chr(self.current_token.type)!r}"))

            if self.current_token.type != TOKENS['IDENTIFIER']:
                return result.failure(self.new_error("expected identifier"))

            while True:
                package = self.current_token
                as_package = None
                processed = False

                if name.value == '__future__':
                    processed = result.register(self.proccess_future(package.value))
                    if result.error:
                        return result

                result.register_advancement()
                self.advance()
                self.skip_expr(result)

                if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['as']):
                    result.register_advancement()
                    self.advance()
                    self.skip_expr(result)

                    if self.current_token.type != TOKENS['IDENTIFIER']:
                        return result.failure(self.new_error("expected identifier"))

                    as_package = self.current_token

                    result.register_advancement()
                    self.advance()
                    self.skip_expr(result)

                if not processed:
                    packages.append((package, as_package))

                if self.current_token.type == TOKENS['COMMA']:
                    result.register_advancement()
                    self.advance()
                    self.skip_expr(result)

                elif bracket and not is_right_bracket(self.current_token.type):
                    return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

                else:
                    break

            if bracket:
                self.close_bracket(result, left_bracket_token)
                if result.error:
                    return result

                self.bracket_level -= 1

        return result.success(
            PysImportNode(
                (name, None),
                packages,
                position
            )
        )

    def import_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['import']):
            return result.failure(self.new_error(f"expected {KEYWORDS['import']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        if self.current_token.type not in (TOKENS['STRING'], TOKENS['IDENTIFIER']):
            return result.failure(self.new_error("expected string or identifier"))

        name = self.current_token
        as_name = None

        result.register_advancement()
        self.advance()
        advance_count = self.skip(result)

        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['as']):
            result.register_advancement()
            self.advance()
            self.skip(result)

            if self.current_token.type != TOKENS['IDENTIFIER']:
                return result.failure(self.new_error("expected identifier"))

            as_name = self.current_token
            result.register_advancement()
            self.advance()

        else:
            self.reverse(advance_count)

        return result.success(
            PysImportNode(
                (name, as_name),
                [],
                position
            )
        )

    def if_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['if']):
            return result.failure(self.new_error(f"expected {KEYWORDS['if']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        condition = result.register(self.walrus(), True)
        if result.error:
            return result

        self.skip(result)

        body = result.register(self.block_statements(), True)
        if result.error:
            return result

        cases = [(condition, body)]
        else_body = None
        advance_count = self.skip(result)

        while self.current_token.matches(TOKENS['KEYWORD'], (KEYWORDS['elif'], KEYWORDS['else'])):

            if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['elif']):
                result.register_advancement()
                self.advance()
                self.skip(result)
                conditional_chain = True

            elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['else']):
                result.register_advancement()
                self.advance()
                self.skip(result)

                if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['if']):
                    result.register_advancement()
                    self.advance()
                    self.skip(result)
                    conditional_chain = True

                else:
                    else_body = result.register(self.block_statements(), True)
                    if result.error:
                        return result

                    advance_count = 0
                    break

            if conditional_chain:
                conditional_chain = False

                condition = result.register(self.walrus(), True)
                if result.error:
                    return result

                self.skip(result)

                body = result.register(self.block_statements(), True)
                if result.error:
                    return result

                cases.append((condition, body))
                advance_count = self.skip(result)

        self.reverse(advance_count)

        return result.success(
            PysIfNode(
                cases,
                else_body,
                position
            )
        )

    def switch_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['switch']):
            return result.failure(self.new_error(f"expected {KEYWORDS['switch']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        target = result.register(self.walrus(), True)
        if result.error:
            return result

        self.skip(result)

        if self.current_token.type != TOKENS['LEFT-CURLY']:
            return result.failure(self.new_error("expected '{'"))

        left_bracket_token = self.current_token

        result.register_advancement()
        self.advance()
        self.skip(result)

        cases = []
        default_body = None

        while self.current_token.matches(TOKENS['KEYWORD'], (KEYWORDS['case'], KEYWORDS['default'])):

            if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['case']):
                result.register_advancement()
                self.advance()
                self.skip(result)

                case = result.register(self.single_expr(), True)
                if result.error:
                    return result

                self.skip(result)

                if self.current_token.type != TOKENS['COLON']:
                    return result.failure(self.new_error("expected ':'"))

                result.register_advancement()
                self.advance()

                body = result.register(self.statements())
                if result.error:
                    return result

                cases.append((case, body))

            elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['default']):
                result.register_advancement()
                self.advance()
                self.skip(result)

                if self.current_token.type != TOKENS['COLON']:
                    return result.failure(self.new_error("expected ':'"))

                result.register_advancement()
                self.advance()

                default_body = result.register(self.statements())
                if result.error:
                    return result

                break

        self.close_bracket(result, left_bracket_token)
        if result.error:
            return result

        return result.success(
            PysSwitchNode(
                target,
                cases,
                default_body,
                position
            )
        )

    def match_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['match']):
            return result.failure(self.new_error(f"expected {KEYWORDS['match']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        target = None

        if self.current_token.type != TOKENS['LEFT-CURLY']:
            target = result.register(self.walrus(), True)
            if result.error:
                return result.failure(self.new_error("expected expression or '{'"))

            self.skip(result)

            if self.current_token.type != TOKENS['LEFT-CURLY']:
                return result.failure(self.new_error("expected '{'"))

        left_bracket_token = self.current_token
        self.bracket_level += 1

        result.register_advancement()
        self.advance()
        self.skip(result)

        cases = []
        default = None

        while not is_right_bracket(self.current_token.type):

            if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['default']):
                result.register_advancement()
                self.advance()
                self.skip(result)

                if self.current_token.type != TOKENS['COLON']:
                    return result.failure(self.new_error("expected ':'"))

                result.register_advancement()
                self.advance()
                self.skip(result)

                default = result.register(self.single_expr(), True)
                if result.error:
                    return result

                break

            condition = result.register(self.single_expr(), True)
            if result.error:
                return result

            if self.current_token.type != TOKENS['COLON']:
                return result.failure(self.new_error("expected ':'"))

            result.register_advancement()
            self.advance()
            self.skip(result)

            value = result.register(self.single_expr(), True)
            if result.error:
                return result

            cases.append((condition, value))

            if self.current_token.type == TOKENS['COMMA']:
                result.register_advancement()
                self.advance()
                self.skip(result)

            elif not is_right_bracket(self.current_token.type):
                return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

        self.close_bracket(result, left_bracket_token)
        if result.error:
            return result

        self.bracket_level -= 1
        self.skip_expr(result)

        return result.success(
            PysMatchNode(
                target,
                cases,
                default,
                position
            )
        )

    def try_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['try']):
            return result.failure(self.new_error(f"expected {KEYWORDS['try']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        body = result.register(self.block_statements(), True)
        if result.error:
            return result

        catch_cases = []
        else_body = None
        finally_body = None
        advance_count = self.skip(result)

        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['catch']):
            all_catch_handler = False

            while self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['catch']):
                if all_catch_handler:
                    return result.failure(self.new_error("only one catch-all except clause allowed"))

                result.register_advancement()
                self.advance()
                self.skip(result)

                bracket = False
                target = None
                parameter = None

                if self.current_token.type == TOKENS['LEFT-PARENTHESIS']:
                    bracket = True
                    left_bracket_token = self.current_token
                    self.bracket_level += 1

                    result.register_advancement()
                    self.advance()
                    self.skip(result)

                    if self.current_token.type != TOKENS['IDENTIFIER']:
                        return result.failure(self.new_error("expected identifier"))

                if self.current_token.type == TOKENS['IDENTIFIER']:
                    parameter = self.current_token

                    result.register_advancement()
                    self.advance()
                    self.skip_expr(result)

                    if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['as']):
                        result.register_advancement()
                        self.advance()
                        self.skip_expr(result)

                        if self.current_token.type != TOKENS['IDENTIFIER']:
                            return result.failure(self.new_error("expected identifier"))

                    if self.current_token.type == TOKENS['IDENTIFIER']:
                        target = PysIdentifierNode(parameter)
                        parameter = self.current_token

                        result.register_advancement()
                        self.advance()
                        self.skip_expr(result)

                    else:
                        all_catch_handler = True

                else:
                    all_catch_handler = True

                if bracket:
                    self.close_bracket(result, left_bracket_token)
                    if result.error:
                        return result

                    self.bracket_level -= 1

                self.skip(result)

                catch_body = result.register(self.block_statements(), True)
                if result.error:
                    return result

                catch_cases.append(((target, parameter), catch_body))
                advance_count = self.skip(result)

            if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['else']):
                result.register_advancement()
                self.advance()
                self.skip(result)

                else_body = result.register(self.block_statements(), True)
                if result.error:
                    return result

                advance_count = self.skip(result)

        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['finally']):
            result.register_advancement()
            self.advance()
            self.skip(result)

            finally_body = result.register(self.block_statements(), True)
            if result.error:
                return result

        elif not catch_cases:
            return result.failure(self.new_error(f"expected {KEYWORDS['catch']!r} or {KEYWORDS['finally']!r}"))

        else:
            self.reverse(advance_count)

        return result.success(
            PysTryNode(
                body,
                catch_cases,
                else_body,
                finally_body,
                position
            )
        )

    def with_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['with']):
            return result.failure(self.new_error(f"expected {KEYWORDS['with']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        bracket = False

        if self.current_token.type == TOKENS['LEFT-PARENTHESIS']:
            bracket = True
            left_bracket_token = self.current_token
            self.bracket_level += 1

            result.register_advancement()
            self.advance()
            self.skip(result)

        contexts = []

        while True:
            context = result.register(self.single_expr(), True)
            if result.error:
                return result

            if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['as']):
                result.register_advancement()
                self.advance()
                self.skip_expr(result)

                if self.current_token.type != TOKENS['IDENTIFIER']:
                    return result.failure(self.new_error("expected identifier"))

            alias = None

            if self.current_token.type == TOKENS['IDENTIFIER']:
                alias = self.current_token

                result.register_advancement()
                self.advance()
                self.skip_expr(result)

            contexts.append((context, alias))

            if self.current_token.type == TOKENS['COMMA']:
                result.register_advancement()
                self.advance()
                self.skip_expr(result)

            elif bracket and not is_right_bracket(self.current_token.type):
                return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

            else:
                break

        if bracket:
            self.close_bracket(result, left_bracket_token)
            if result.error:
                return result

            self.bracket_level -= 1

        self.skip(result)

        body = result.register(self.block_statements(), True)
        if result.error:
            return result

        return result.success(
            PysWithNode(
                contexts,
                body,
                position
            )
        )

    def for_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['for']):
            return result.failure(self.new_error(f"expected {KEYWORDS['for']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        bracket = False

        if self.current_token.type == TOKENS['LEFT-PARENTHESIS']:
            bracket = True
            left_bracket_token = self.current_token
            self.bracket_level += 1

            result.register_advancement()
            self.advance()
            self.skip(result)

        declaration = result.try_register(self.assign_expr())
        if result.error:
            return result

        if self.current_token.type == TOKENS['SEMICOLON']:
            iteration = False

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            condition = result.try_register(self.single_expr())
            if result.error:
                return result

            if self.current_token.type != TOKENS['SEMICOLON']:
                return result.failure(self.new_error("expected ';'"))

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            update = result.try_register(self.assign_expr())
            if result.error:
                return result

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['of']):
            if declaration is None:
                return result.failure(
                    self.new_error(f"expected assign expression. Did you mean ';' instead of {KEYWORDS['of']!r}?")
                )

            iteration = True

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            iterable = result.register(self.single_expr(), True)
            if result.error:
                return result

        elif declaration is None:
            return result.failure(self.new_error("expected assign expression or ';'"))

        else:
            return result.failure(self.new_error(f"expected {KEYWORDS['of']!r} or ';'"))

        if bracket:
            self.close_bracket(result, left_bracket_token)
            if result.error:
                return result

            self.bracket_level -= 1

        self.skip(result)

        body = result.register(self.block_statements(), True)
        if result.error:
            return result

        else_body = None
        advance_count = self.skip(result)

        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['else']):
            result.register_advancement()
            self.advance()
            self.skip(result)

            else_body = result.register(self.block_statements(), True)
            if result.error:
                return result

        else:
            self.reverse(advance_count)

        return result.success(
            PysForNode(
                (declaration, iterable) if iteration else (declaration, condition, update),
                body,
                else_body,
                position
            )
        )

    def while_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['while']):
            return result.failure(self.new_error(f"expected {KEYWORDS['while']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        condition = result.register(self.walrus(), True)
        if result.error:
            return result

        self.skip(result)

        body = result.register(self.block_statements(), True)
        if result.error:
            return result

        else_body = None
        advance_count = self.skip(result)

        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['else']):
            result.register_advancement()
            self.advance()
            self.skip(result)

            else_body = result.register(self.block_statements(), True)
            if result.error:
                return result

        else:
            self.reverse(advance_count)

        return result.success(
            PysWhileNode(
                condition,
                body,
                else_body,
                position
            )
        )

    def do_while_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['do']):
            return result.failure(self.new_error(f"expected {KEYWORDS['do']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        body = result.register(self.block_statements(), True)
        if result.error:
            return result

        self.skip(result)

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['while']):
            return result.failure(self.new_error(f"expected {KEYWORDS['while']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        condition = result.register(self.walrus(), True)
        if result.error:
            return result

        else_body = None
        advance_count = self.skip(result)

        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['else']):
            result.register_advancement()
            self.advance()
            self.skip(result)

            else_body = result.register(self.block_statements(), True)
            if result.error:
                return result

        else:
            self.reverse(advance_count)

        return result.success(
            PysDoWhileNode(
                body,
                condition,
                else_body,
                position
            )
        )

    def class_expr(self, decorators=None):
        result = PysParserResult()
        start = self.current_token.position.start

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['class']):
            return result.failure(self.new_error(f"expected {KEYWORDS['class']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        if self.current_token.type != TOKENS['IDENTIFIER']:
            return result.failure(self.new_error("expected identifier"))

        end = self.current_token.position.end
        name = self.current_token
        bases = []

        result.register_advancement()
        self.advance()
        self.skip(result)

        if self.current_token.type == TOKENS['LEFT-PARENTHESIS']:
            base = result.register(self.sequence_expr('tuple', should_sequence=True))
            if result.error:
                return result

            end = base.position.end
            bases = list(base.elements)

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['extends']):
            result.register_advancement()
            self.advance()
            self.skip(result)

            base = result.register(self.expr(), True)
            if result.error:
                return result

            end = base.position.end

            if isinstance(base, PysTupleNode):
                if not base.elements:
                    return result.failure(self.new_error("empty base not allowed", bases.position))
                bases = list(base.elements)

            else:
                bases.append(base)

        body = result.register(self.block_statements(), True)
        if result.error:
            return result

        return result.success(
            PysClassNode(
                [] if decorators is None else decorators,
                name,
                bases,
                body,
                PysPosition(
                    self.current_token.position.file,
                    start,
                    end
                )
            )
        )

    def func_expr(self, decorators=None):
        result = PysParserResult()
        position = self.current_token.position
        start = position.start

        constructor = False

        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['constructor']):
            constructor = True
        elif not self.current_token.matches(TOKENS['KEYWORD'], (KEYWORDS['func'], KEYWORDS['function'])):
            return result.failure(
                self.new_error(
                    f"expected {KEYWORDS['func']!r}, {KEYWORDS['function']!r}, or {KEYWORDS['constructor']}"
                )
            )

        result.register_advancement()
        self.advance()
        self.skip(result)

        name = None
        parameters = []

        if constructor:
            name = PysToken(TOKENS['IDENTIFIER'], position, '__init__')
            parameters.append(PysToken(TOKENS['IDENTIFIER'], position, 'self'))

        elif self.current_token.type == TOKENS['IDENTIFIER']:
            name = self.current_token
            result.register_advancement()
            self.advance()
            self.skip(result)

        if self.current_token.type != TOKENS['LEFT-PARENTHESIS']:
            return result.failure(self.new_error("expected identifier or '('" if name is None else "expected '('"))

        left_bracket_token = self.current_token
        self.bracket_level += 1

        result.register_advancement()
        self.advance()
        self.skip(result)

        seen_keyword_argument = False

        while not is_right_bracket(self.current_token.type):
            if self.current_token.type != TOKENS['IDENTIFIER']:
                return result.failure(self.new_error("expected identifier"))

            key = self.current_token

            result.register_advancement()
            self.advance()
            self.skip(result)

            if self.current_token.type == TOKENS['EQUAL']:
                result.register_advancement()
                self.advance()
                self.skip(result)
                seen_keyword_argument = True

            elif seen_keyword_argument:
                return result.failure(self.new_error("expected '=' (follows keyword argument)"))

            if seen_keyword_argument:
                value = result.register(self.single_expr(), True)
                if result.error:
                    return result
                parameters.append((key, value))
            else:
                parameters.append(key)

            self.skip(result)

            if self.current_token.type == TOKENS['COMMA']:
                result.register_advancement()
                self.advance()
                self.skip(result)

            elif not is_right_bracket(self.current_token.type):
                return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

        end = self.current_token.position.end

        self.close_bracket(result, left_bracket_token)
        if result.error:
            return result

        self.bracket_level -= 1
        self.skip(result)

        if not constructor and self.current_token.type == TOKENS['EQUAL-ARROW']:
            position = self.current_token.position
            result.register_advancement()
            self.advance()
            self.skip(result)

            body = result.register(self.single_expr(), True)
            if result.error:
                return result

            body = PysReturnNode(body, position)

        else:
            body = result.register(self.block_statements(), True)
            if result.error:
                return result.failure(
                    self.new_error(
                        "expected statement, expression, '{', ';'"
                        if constructor else
                        "expected statement, expression, '{', ';', or '=>'"
                    )
                )

        self.skip_expr(result)

        return result.success(
            PysFunctionNode(
                [] if decorators is None else decorators,
                name,
                parameters,
                body,
                constructor,
                PysPosition(self.current_token.position.file, start, end)
            )
        )

    def return_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['return']):
            return result.failure(self.new_error(f"expected {KEYWORDS['return']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        value = result.try_register(self.expr())
        if result.error:
            return result

        if not value:
            self.reverse(result.to_reverse_count)

        return result.success(
            PysReturnNode(
                value,
                position
            )
        )

    def global_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['global']):
            return result.failure(self.new_error(f"expected {KEYWORDS['global']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        names = []
        bracket = False

        if self.current_token.type == TOKENS['LEFT-PARENTHESIS']:
            bracket = True
            left_bracket_token = self.current_token
            self.bracket_level += 1

            result.register_advancement()
            self.advance()
            self.skip(result)

        elif is_left_bracket(self.current_token.type):
            return result.failure(self.new_error(f"expected '(' not {chr(self.current_token.type)!r}"))

        if self.current_token.type != TOKENS['IDENTIFIER']:
            return result.failure(self.new_error("expected identifier"))

        while self.current_token.type == TOKENS['IDENTIFIER']:
            names.append(self.current_token)

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            if self.current_token.type == TOKENS['COMMA']:
                result.register_advancement()
                self.advance()
                self.skip_expr(result)

            elif bracket and not is_right_bracket(self.current_token.type):
                return result.failure(self.new_error("invalid syntax. Perhaps you forgot a comma?"))

            else:
                break

        if bracket:
            self.close_bracket(result, left_bracket_token)
            if result.error:
                return result

            self.bracket_level -= 1

        return result.success(
            PysGlobalNode(
                names,
                position
            )
        )

    def del_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.matches(TOKENS['KEYWORD'], (KEYWORDS['del'], KEYWORDS['delete'])):
            return result.failure(self.new_error(f"expected {KEYWORDS['del']!r} or {KEYWORDS['delete']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        expr = result.register(self.expr(), True)
        if result.error:
            return result

        if isinstance(expr, PysTupleNode):
            targets = list(expr.elements)
            if not targets:
                return result.failure(self.new_error("empty target not allowed", expr.position))

        else:
            targets = [expr]

        return result.success(
            PysDeleteNode(
                targets,
                position
            )
        )

    def throw_expr(self):
        result = PysParserResult()
        position = self.current_token.position

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['throw']):
            return result.failure(self.new_error(f"expected {KEYWORDS['throw']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        target = result.register(self.single_expr(), True)
        if result.error:
            return result

        cause = None

        if self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['from']):
            result.register_advancement()
            self.advance()
            self.skip(result)

            cause = result.register(self.single_expr(), True)
            if result.error:
                return result

        return result.success(
            PysThrowNode(
                target,
                cause,
                position
            )
        )

    def assert_expr(self):
        result = PysParserResult()

        if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['assert']):
            return result.failure(self.new_error(f"expected {KEYWORDS['assert']!r}"))

        result.register_advancement()
        self.advance()
        self.skip(result)

        condition = result.register(self.single_expr(), True)
        if result.error:
            return result

        message = None
        advance_count = self.skip(result)

        if self.current_token.type == TOKENS['COMMA']:
            result.register_advancement()
            self.advance()
            self.skip(result)

            message = result.register(self.single_expr(), True)
            if result.error:
                return result

        else:
            self.reverse(advance_count)

        return result.success(
            PysAssertNode(
                condition,
                message
            )
        )

    def decorator_expr(self):
        result = PysParserResult()

        if self.current_token.type != TOKENS['AT']:
            return result.failure(self.new_error("expected '@'"))

        decorators = []

        while self.current_token.type == TOKENS['AT']:
            result.register_advancement()
            self.advance()

            decorators.append(result.register(self.walrus(), True))
            if result.error:
                return result

            self.skip(result, (TOKENS['NEWLINE'], TOKENS['SEMICOLON']))

        if self.current_token.matches(
            TOKENS['KEYWORD'],
            (KEYWORDS['func'], KEYWORDS['function'], KEYWORDS['constructor'])
        ):
            func_expr = result.register(self.func_expr(decorators))
            if result.error:
                return result

            return result.success(func_expr)

        elif self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['class']):
            class_expr = result.register(self.class_expr(decorators))
            if result.error:
                return result

            return result.success(class_expr)

        return result.failure(self.new_error("expected function or class declaration after decorator"))

    def block_statements(self):
        result = PysParserResult()

        if self.current_token.type == TOKENS['LEFT-CURLY']:
            left_bracket_token = self.current_token

            result.register_advancement()
            self.advance()

            body = result.register(self.statements())
            if result.error:
                return result

            end = self.current_token.position.end

            self.close_bracket(result, left_bracket_token)
            if result.error:
                return result

            if isinstance(body, PysStatementsNode):
                setimuattr(
                    body, 'position',
                    PysPosition(
                        self.current_token.position.file,
                        left_bracket_token.position.start,
                        end
                    )
                )

            return result.success(body)

        elif self.current_token.type == TOKENS['SEMICOLON']:
            position = self.current_token.position

            result.register_advancement()
            self.advance()

            return result.success(
                PysStatementsNode(
                    [],
                    position
                )
            )

        elif self.current_token.type == TOKENS['COLON']:
            return result.failure(self.new_error("unlike python"))

        else:
            body = result.register(self.statement())
            if result.error:
                return result.failure(self.new_error("expected statement, expression, '{', or ';'"), fatal=False)

            return result.success(body)

    def chain_operator(self, func, operators, is_member=False):
        result = PysParserResult()

        operations = []
        expressions = []

        expr = result.register(func())
        if result.error:
            return result

        while self.current_token.type in operators or (self.current_token.type, self.current_token.value) in operators:
            operations.append(self.current_token)
            expressions.append(expr)

            if is_member and self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['not']):
                result.register_advancement()
                self.advance()
                self.skip_expr(result)

                if not self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['in']):
                    return result.failure(self.new_error(f"expected {KEYWORDS['in']!r}"))

                operations[-1] = PysToken(
                    TOKENS['NOT-IN'],
                    self.current_token.position,
                    f"{KEYWORDS['not']} {KEYWORDS['in']}"
                )

            last_token = self.current_token

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            if (
                is_member and
                last_token.match(TOKENS['KEYWORD'], KEYWORDS['is']) and
                self.current_token.match(TOKENS['KEYWORD'], KEYWORDS['not'])
            ):
                operations[-1] = PysToken(
                    TOKENS['IS-NOT'],
                    self.current_token.position,
                    f"{KEYWORDS['is']} {KEYWORDS['not']}"
                )

                result.register_advancement()
                self.advance()
                self.skip_expr(result)

            expr = result.register(func(), True)
            if result.error:
                return result

        if operations:
            expressions.append(expr)

        return result.success(
            PysChainOperatorNode(
                operations,
                expressions
            )
            if operations else
            expr
        )

    def binary_operator(self, func, operators, is_bitwise=False):
        result = PysParserResult()

        left = result.register(func())
        if result.error:
            return result

        while self.current_token.type in operators or (self.current_token.type, self.current_token.value) in operators:
            operand = (
                PysToken(
                    TOKENS['CIRCUMFLEX'],
                    self.current_token.position,
                    'reversed'
                )
                if
                    is_bitwise and
                    self.flags & REVERSE_POW_XOR and
                    self.current_token.type == TOKENS['DOUBLE-STAR']
                else
                self.current_token
            )

            result.register_advancement()
            self.advance()
            self.skip_expr(result)

            right = result.register(func(), True)
            if result.error:
                return result

            left = PysBinaryOperatorNode(left, operand, right)

        return result.success(left)

    def close_bracket(self, result, left_bracket_token):
        if self.current_token.type != BRACKETS_MAP[left_bracket_token.type]:

            if is_right_bracket(self.current_token.type):
                return result.failure(
                    self.new_error(
                        f"closing parenthesis {chr(self.current_token.type)!r} "
                        f"does not match opening parenthesis {chr(left_bracket_token.type)!r}"
                    )
                )

            elif self.current_token.type == TOKENS['NULL']:
                return result.failure(
                    self.new_error(
                        f"{chr(left_bracket_token.type)!r} was never closed",
                        left_bracket_token.position
                    )
                )

            return result.failure(self.new_error("invalid syntax"))

        result.register_advancement()
        self.advance()

    def skip(self, result, types=(TOKENS['NEWLINE'],)):
        count = 0

        while self.current_token.type in types:
            result.register_advancement()
            self.advance()
            count += 1

        return count

    def skip_expr(self, result):
        if self.bracket_level > 0:
            return self.skip(result)

        return 0

    def proccess_future(self, name):
        result = PysParserResult()

        if name == 'braces':
            return result.failure(self.new_error("yes, i use it for this language"))

        elif name == 'indent':
            return result.failure(self.new_error("not a chance"))

        elif name == 'reverse_pow_xor':
            self.flags |= REVERSE_POW_XOR
            return result.success(True)

        return result.failure(self.new_error(f"future feature {name} is not defined"))