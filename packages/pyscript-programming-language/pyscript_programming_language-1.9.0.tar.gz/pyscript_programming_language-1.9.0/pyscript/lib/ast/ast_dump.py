from pyscript.core.utils.string import indent

PARENTHESIS_TYPES_MAP = {
    tuple: '()',
    list: '[]',
    set: '{}',
    dict: '{}',
    slice: ('slice(', ')')
}

class DumpNode:

    def __init__(
        self,
        annotate_fields=True,
        include_attributes=False,
        indent=None,
        show_empty=False
    ):
        if not isinstance(indent, (type(None), int)):
            raise TypeError("dump() or DumpNode(): indent is not integer or NoneType")

        self.annotate_fields = bool(annotate_fields)
        self.include_attributes = bool(include_attributes)
        self.indent = indent
        self.show_empty = bool(show_empty)

    def _format_parameter(self, name, value):
        return f'{name}={value}' if self.annotate_fields else value

    def _format_parameters(self, parameters, add_comma=False):
        if self.indent is None or not parameters:
            string = ', '.join(parameters)
            if add_comma:
                string += ','

        else:
            string = ','.join('\n' + indent(parameter, self.indent) for parameter in parameters)
            if add_comma:
                string += ','
            if parameters:
                string += '\n'

        return string

    def _node_representation(self, node, parameters_info):
        parameters = [
            self._format_parameter(name, self.visit(value))
            for name, value in parameters_info
            if self.show_empty or value is not None
        ]

        if self.include_attributes:
            parameters.append(self._format_parameter('position_start', repr(node.position.start)))
            parameters.append(self._format_parameter('position_end', repr(node.position.end)))

        name = type(node).__name__.removeprefix('Pys').removesuffix('Node')
        formatted_parameters = self._format_parameters(parameters)

        return f'{name}({formatted_parameters})'

    def _any_representation(self, object):
        type_object = type(object)
        if type_object not in PARENTHESIS_TYPES_MAP:
            return repr(object)

        if type_object is slice:
            parameters = [
                self._format_parameter('start', self.visit(object.start)),
                self._format_parameter('stop', self.visit(object.stop)),
                self._format_parameter('step', self.visit(object.step))
            ]
        elif type_object is dict:
            parameters = [f'{self.visit(key)}: {self.visit(value)}' for key, value in object.items()]
        else:
            parameters = tuple(map(self.visit, object))

        open_parenthesis, close_parenthesis = PARENTHESIS_TYPES_MAP[type_object]
        formatted_parameters = self._format_parameters(
            parameters,
            add_comma=type_object is tuple and len(object) == 1
        )

        return f'{open_parenthesis}{formatted_parameters}{close_parenthesis}'

    def visit(self, node):
        return getattr(self, 'visit_' + type(node).__name__.removeprefix('Pys'), self._any_representation)(node)

    def visit_NumberNode(self, node):
        return self._node_representation(
            node,
            [
                ('value', node.value)
            ]
        )

    def visit_StringNode(self, node):
        return self._node_representation(
            node,
            [
                ('value', node.value)
            ]
        )

    def visit_KeywordNode(self, node):
        return self._node_representation(
            node,
            [
                ('name', node.name)
            ]
        )

    def visit_IdentifierNode(self, node):
        return self._node_representation(
            node,
            [
                ('name', node.name)
            ]
        )

    def visit_DictionaryNode(self, node):
        return self._node_representation(
            node,
            [
                ('pairs', node.pairs)
            ]
        )

    def visit_SetNode(self, node):
        return self._node_representation(
            node,
            [
                ('elements', node.elements)
            ]
        )

    def visit_ListNode(self, node):
        return self._node_representation(
            node,
            [
                ('elements', node.elements)
            ]
        )

    def visit_TupleNode(self, node):
        return self._node_representation(
            node,
            [
                ('elements', node.elements)
            ]
        )

    def visit_AttributeNode(self, node):
        return self._node_representation(
            node,
            [
                ('target', node.target),
                ('attribute', node.attribute)
            ]
        )

    def visit_SubscriptNode(self, node):
        return self._node_representation(
            node,
            [
                ('target', node.target),
                ('slice', node.slice)
            ]
        )

    def visit_CallNode(self, node):
        return self._node_representation(
            node,
            [
                ('target', node.target),
                ('arguments', node.arguments)
            ]
        )

    def visit_ChainOperatorNode(self, node):
        return self._node_representation(
            node,
            [
                ('operations', node.operations),
                ('expressions', node.expressions)
            ]
        )

    def visit_TernaryOperatorNode(self, node):
        return self._node_representation(
            node,
            [
                ('condition', node.condition),
                ('valid', node.valid),
                ('invalid', node.invalid),
                ('style', node.style)
            ]
        )

    def visit_BinaryOperatorNode(self, node):
        return self._node_representation(
            node,
            [
                ('left', node.left),
                ('operand', node.operand),
                ('right', node.right)
            ]
        )

    def visit_UnaryOperatorNode(self, node):
        return self._node_representation(
            node,
            [
                ('operand', node.operand),
                ('value', node.value),
                ('operand_position', node.operand_position)
            ]
        )

    def visit_StatementsNode(self, node):
        return self._node_representation(
            node,
            [
                ('body', node.body)
            ]
        )

    def visit_AssignNode(self, node):
        return self._node_representation(
            node,
            [
                ('target', node.target),
                ('operand', node.operand),
                ('value', node.value)
            ]
        )

    def visit_ImportNode(self, node):
        return self._node_representation(
            node,
            [
                ('name', node.name),
                ('packages', node.packages)
            ]
        )

    def visit_IfNode(self, node):
        return self._node_representation(
            node,
            [
                ('cases_body', node.cases_body),
                ('else_body', node.else_body)
            ]
        )

    def visit_SwitchNode(self, node):
        return self._node_representation(
            node,
            [
                ('target', node.target),
                ('case_cases', node.case_cases),
                ('default_body', node.default_body)
            ]
        )

    def visit_MatchNode(self, node):
        return self._node_representation(
            node,
            [
                ('target', node.target),
                ('cases', node.cases),
                ('default', node.default)
            ]
        )

    def visit_TryNode(self, node):
        return self._node_representation(
            node,
            [
                ('body', node.body),
                ('catch_cases', node.catch_cases),
                ('else_body', node.else_body),
                ('finally_body', node.finally_body)
            ]
        )

    def visit_WithNode(self, node):
        return self._node_representation(
            node,
            [
                ('contexts', node.contexts),
                ('body', node.body)
            ]
        )

    def visit_ForNode(self, node):
        return self._node_representation(
            node,
            [
                ('header', node.header),
                ('body', node.body),
                ('else_body', node.else_body)
            ]
        )

    def visit_WhileNode(self, node):
        return self._node_representation(
            node,
            [
                ('condition', node.condition),
                ('body', node.body),
                ('else_body', node.else_body)
            ]
        )

    def visit_DoWhileNode(self, node):
        return self._node_representation(
            node,
            [
                ('body', node.body),
                ('condition', node.condition),
                ('else_body', node.else_body)
            ]
        )

    def visit_ClassNode(self, node):
        return self._node_representation(
            node,
            [
                ('decorators', node.decorators),
                ('name', node.name),
                ('bases', node.bases),
                ('body', node.body)
            ]
        )

    def visit_FunctionNode(self, node):
        return self._node_representation(
            node,
            [
                ('decorators', node.decorators),
                ('name', node.name),
                ('parameters', node.parameters),
                ('body', node.body),
                ('constructor', node.constructor)
            ]
        )

    def visit_GlobalNode(self, node):
        return self._node_representation(
            node,
            [
                ('identifiers', node.identifiers)
            ]
        )

    def visit_ReturnNode(self, node):
        return self._node_representation(
            node,
            [
                ('value', node.value)
            ]
        )

    def visit_ThrowNode(self, node):
        return self._node_representation(
            node,
            [
                ('target', node.target),
                ('cause', node.cause)
            ]
        )

    def visit_AssertNode(self, node):
        return self._node_representation(
            node,
            [
                ('condition', node.condition),
                ('message', node.message)
            ]
        )

    def visit_DeleteNode(self, node):
        return self._node_representation(
            node,
            [
                ('targets', node.targets)
            ]
        )

    def visit_EllipsisNode(self, node):
        return self._node_representation(node, [])

    def visit_ContinueNode(self, node):
        return self._node_representation(node, [])

    def visit_BreakNode(self, node):
        return self._node_representation(node, [])

def dump(
    node,
    *,
    annotate_fields=True,
    include_attributes=False,
    indent=None,
    show_empty=False
):
    return DumpNode(
        annotate_fields=annotate_fields,
        include_attributes=include_attributes,
        indent=indent,
        show_empty=show_empty
    ).visit(node)