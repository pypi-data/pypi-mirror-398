from .bases import Pys
from .checks import is_unpack_assignment, is_incremental
from .constants import TOKENS, KEYWORDS, DEFAULT
from .context import PysContext
from .exceptions import PysTraceback
from .nodes import PysNode, PysKeywordNode, PysIdentifierNode, PysAttributeNode, PysSubscriptNode
from .position import PysPosition
from .utils.decorators import typechecked

from typing import Optional

class PysAnalyzer(Pys):

    @typechecked
    def __init__(
        self,
        node: PysNode,
        flags: int = DEFAULT,
        context_parent: Optional[PysContext] = None,
        context_parent_entry_position: Optional[PysPosition] = None
    ) -> None:

        self.node = node
        self.flags = flags
        self.context = context_parent
        self.context_parent_entry_position = context_parent_entry_position

    def throw(self, message, position):
        if self.error is None:
            self.error = PysTraceback(
                SyntaxError(message),
                PysContext(
                    file=self.node.position.file,
                    flags=self.flags,
                    parent=self.context,
                    parent_entry_position=self.context_parent_entry_position
                ),
                position
            )

    @typechecked
    def analyze(self) -> PysTraceback | None:
        self.in_loop = 0
        self.in_function = 0
        self.in_class = 0
        self.in_switch = 0
        self.parameters = set()
        self.error = None

        self.visit(self.node)
        return self.error

    def visit(self, node):
        func = getattr(self, 'visit_' + type(node).__name__.removeprefix('Pys'), None)
        if not self.error and func:
            func(node)

    def visit_DictionaryNode(self, node):
        for key, value in node.pairs:

            self.visit(key)
            if self.error:
                return

            self.visit(value)
            if self.error:
                return

    def visit_SetNode(self, node):
        for element in node.elements:
            self.visit(element)
            if self.error:
                return

    def visit_ListNode(self, node):
        for element in node.elements:
            self.visit(element)
            if self.error:
                return

    def visit_TupleNode(self, node):
        for element in node.elements:
            self.visit(element)
            if self.error:
                return

    def visit_AttributeNode(self, node):
        self.visit(node.target)

    def visit_SubscriptNode(self, node):
        self.visit(node.target)
        if self.error:
            return

        self.visit_slice_SubscriptNode(node.slice)

    def visit_CallNode(self, node):
        self.visit(node.target)
        if self.error:
            return

        keyword_names = set()

        for element in node.arguments:

            if isinstance(element, tuple):
                token, value = element
                name = token.value

                if name in keyword_names:
                    self.throw(f"duplicate argument {name!r} in call definition", token.position)
                    return

                keyword_names.add(name)

            else:
                value = element

            self.visit(value)
            if self.error:
                return

    def visit_ChainOperatorNode(self, node):
        for expression in node.expressions:
            self.visit(expression)
            if self.error:
                return

    def visit_TernaryOperatorNode(self, node):
        if node.style == 'general':
            self.visit(node.condition)
            if self.error:
                return

            self.visit(node.valid)
            if self.error:
                return

        elif node.style == 'pythonic':
            self.visit(node.valid)
            if self.error:
                return

            self.visit(node.condition)
            if self.error:
                return

        else:
            raise ValueError(f"unknown ternary operator style {node.style!r}")

        self.visit(node.invalid)

    def visit_BinaryOperatorNode(self, node):
        self.visit(node.left)
        if self.error:
            return

        self.visit(node.right)

    def visit_UnaryOperatorNode(self, node):
        value = node.value

        if is_incremental(node.operand.type):
            type = value.__class__
            operator = 'increase' if node.operand.type == TOKENS['DOUBLE-PLUS'] else 'decrease'

            if type is PysKeywordNode:
                self.throw(f"cannot {operator} {value.name.value}", value.position)
                return

            elif isinstance(value, PysNode):
                if type not in (PysIdentifierNode, PysAttributeNode, PysSubscriptNode):
                    self.throw(f"cannot {operator} literal", value.position)
                    return

            else:
                raise TypeError("UnaryOperator: node.value is not PysNode")

        self.visit(value)

    def visit_StatementsNode(self, node):
        for element in node.body:
            self.visit(element)
            if self.error:
                return

    def visit_AssignNode(self, node):
        self.visit_declaration_AssignNode(
            node.target,
            "cannot assign to expression here. Maybe you meant '==' instead of '='?"
        )

        if self.error:
            return

        self.visit(node.value)

    def visit_IfNode(self, node):
        for condition, body in node.cases_body:
            self.visit(condition)
            if self.error:
                return

            self.visit(body)
            if self.error:
                return

        if node.else_body:
            self.visit(node.else_body)

    def visit_SwitchNode(self, node):
        self.visit(node.target)
        if self.error:
            return

        self.in_switch += 1

        for condition, body in node.case_cases:
            self.visit(condition)
            if self.error:
                return

            self.visit(body)
            if self.error:
                return

        if node.default_body:
            self.visit(node.default_body)
            if self.error:
                return

        self.in_switch -= 1

    def visit_MatchNode(self, node):
        if node.target:
            self.visit(node.target)
            if self.error:
                return

        for condition, value in node.cases:
            self.visit(condition)
            if self.error:
                return

            self.visit(value)
            if self.error:
                return

        if node.default:
            self.visit(node.default)
            if self.error:
                return

    def visit_TryNode(self, node):
        self.visit(node.body)
        if self.error:
            return

        for _, body in node.catch_cases:
            self.visit(body)
            if self.error:
                return

        if node.else_body:
            self.visit(node.else_body)
            if self.error:
                return

        if node.finally_body:
            self.visit(node.finally_body)

    def visit_WithNode(self, node):
        for context, _ in node.contexts:
            self.visit(context)
            if self.error:
                return

        self.visit(node.body)

    def visit_ForNode(self, node):
        if len(node.header) == 2:
            declaration, iterable = node.header

            self.visit_declaration_AssignNode(declaration, "cannot assign to expression")
            if self.error:
                return

            self.visit(iterable)
            if self.error:
                return

        elif len(node.header) == 3:
            for element in node.header:
                self.visit(element)
                if self.error:
                    return

        else:
            raise ValueError(f"unknown header struct {node.header}")

        self.in_loop += 1

        self.visit(node.body)
        if self.error:
            return

        self.in_loop -= 1

        if node.else_body:
            self.visit(node.else_body)

    def visit_WhileNode(self, node):
        self.visit(node.condition)
        if self.error:
            return

        self.in_loop += 1

        self.visit(node.body)
        if self.error:
            return

        self.in_loop -= 1

        if node.else_body:
            self.visit(node.else_body)

    def visit_DoWhileNode(self, node):
        self.in_loop += 1

        self.visit(node.body)
        if self.error:
            return

        self.in_loop -= 1

        self.visit(node.condition)
        if self.error:
            return

        if node.else_body:
            self.visit(node.else_body)

    def visit_ClassNode(self, node):
        for decorator in node.decorators:
            self.visit(decorator)
            if self.error:
                return

        for base in node.bases:
            self.visit(base)
            if self.error:
                return

        in_loop, in_function, in_switch = self.in_loop, self.in_function, self.in_switch

        self.in_loop = 0
        self.in_function = 0
        self.in_switch = 0

        self.in_class += 1

        self.visit(node.body)
        if self.error:
            return

        self.in_class -= 1

        self.in_loop = in_loop
        self.in_function = in_function
        self.in_switch = in_switch

    def visit_FunctionNode(self, node):
        if node.constructor and self.in_class == 0:
            self.throw(f"{KEYWORDS['constructor']} function outside of class", node.name.position)
            return

        for decorator in node.decorators:
            self.visit(decorator)
            if self.error:
                return

        parameter_names = set()

        for element in node.parameters:
            token = (element[0] if isinstance(element, tuple) else element)
            name = token.value

            if name in parameter_names:
                return self.throw(f"duplicate argument {name!r} in function definition", token.position)

            parameter_names.add(name)

            if isinstance(element, tuple):
                self.visit(element[1])
                if self.error:
                    return

        in_loop, in_class, in_switch, parameters = self.in_loop, self.in_class, self.in_switch, self.parameters

        self.in_loop = 0
        self.in_class = 0
        self.in_switch = 0

        self.in_function += 1
        self.parameters = parameter_names

        self.visit(node.body)
        if self.error:
            return

        self.in_function -= 1
        self.parameters = parameters

        self.in_loop = in_loop
        self.in_class = in_class
        self.in_switch = in_switch

    def visit_GlobalNode(self, node):
        if self.in_function == 0:
            self.throw(f"{KEYWORDS['global']} outside of function", node.position)

        for identifier in node.identifiers:
            if identifier.value in self.parameters:
                self.throw(f"name {identifier.value!r} is parameter and global", identifier.position)
                return

    def visit_ReturnNode(self, node):
        if self.in_function == 0:
            self.throw(f"{KEYWORDS['return']} outside of function", node.position)
            return

        if node.value:
            self.visit(node.value)

    def visit_ThrowNode(self, node):
        self.visit(node.target)
        if self.error:
            return

        if node.cause:
            self.visit(node.cause)

    def visit_AssertNode(self, node):
        self.visit(node.condition)
        if self.error:
            return

        if node.message:
            self.visit(node.message)

    def visit_DeleteNode(self, node):
        for target in node.targets:
            type = target.__class__

            if type is PysAttributeNode:
                self.visit(target.target)
                if self.error:
                    return

            elif type is PysSubscriptNode:
                self.visit(target.target)
                if self.error:
                    return

                self.visit_slice_SubscriptNode(target.slice)
                if self.error:
                    return

            elif type is PysKeywordNode:
                self.throw(f"cannot {KEYWORDS['delete']} {target.name.value}", target.position)
                return

            elif isinstance(target, PysNode):
                if type is not PysIdentifierNode:
                    self.throw(f"cannot {KEYWORDS['delete']} literal", target.position)
                    return

            else:
                raise TypeError("DeleteNode: node.targets, target is not PysNode")

    def visit_ContinueNode(self, node):
        if self.in_loop == 0:
            self.throw(f"{KEYWORDS['continue']} outside of loop", node.position)

    def visit_BreakNode(self, node):
        if self.in_loop == 0 and self.in_switch == 0:
            self.throw(f"{KEYWORDS['break']} outside of loop or switch case", node.position)

    def visit_slice_SubscriptNode(self, nslice):
        type = nslice.__class__

        if type is slice:
            if nslice.start is not None:
                self.visit(nslice.start)
                if self.error:
                    return

            if nslice.stop is not None:
                self.visit(nslice.stop)
                if self.error:
                    return

            if nslice.step is not None:
                self.visit(nslice.step)
                if self.error:
                    return

        elif type is tuple:
            for element in nslice:
                self.visit_slice_SubscriptNode(element)
                if self.error:
                    return

        else:
            self.visit(nslice)

    def visit_declaration_AssignNode(self, node, message):
        type = node.__class__

        if type is PysAttributeNode:
            self.visit(node.target)

        elif type is PysSubscriptNode:
            self.visit(node.target)
            if self.error:
                return

            self.visit_slice_SubscriptNode(node.slice)

        elif is_unpack_assignment(type):
            for element in node.elements:
                self.visit_declaration_AssignNode(element, message)
                if self.error:
                    return

        elif type is PysKeywordNode:
            self.throw(f"cannot assign to {node.name.value}", node.position)

        elif isinstance(node, PysNode):
            if type is not PysIdentifierNode:
                self.throw(message, node.position)

        else:
            raise TypeError("declaration AssignNode: node is not PysNode")