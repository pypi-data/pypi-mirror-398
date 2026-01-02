from .bases import Pys
from .position import PysPosition
from .token import PysToken
from .utils.decorators import typechecked, immutable, inheritable
from .utils.generic import setimuattr

from typing import Literal

@immutable
class PysNode(Pys):

    __slots__ = ('position',)

    @typechecked
    def __init__(self, position: PysPosition) -> None:
        setimuattr(self, 'position', position)

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        inheritable(cls)

    def __repr__(self) -> str:
        return 'Node()'

class PysNumberNode(PysNode):

    __slots__ = ('value',)

    @typechecked
    def __init__(self, value: PysToken) -> None:
        super().__init__(value.position)
        setimuattr(self, 'value', value)

    def __repr__(self) -> str:
        return f'Number(value={self.value!r})'

class PysStringNode(PysNode):

    __slots__ = ('value',)

    @typechecked
    def __init__(self, value: PysToken) -> None:
        super().__init__(value.position)
        setimuattr(self, 'value', value)

    def __repr__(self) -> str:
        return f'String(value={self.value!r})'

class PysKeywordNode(PysNode):

    __slots__ = ('name',)

    @typechecked
    def __init__(self, name: PysToken) -> None:
        super().__init__(name.position)
        setimuattr(self, 'name', name)

    def __repr__(self) -> str:
        return f'Keyword(name={self.name!r})'

class PysIdentifierNode(PysNode):

    __slots__ = ('name',)

    @typechecked
    def __init__(self, name: PysToken) -> None:
        super().__init__(name.position)
        setimuattr(self, 'name', name)

    def __repr__(self) -> str:
        return f'Identifier(name={self.name!r})'

class PysDictionaryNode(PysNode):

    __slots__ = ('pairs',)

    @typechecked
    def __init__(self, pairs: list[tuple[PysNode, PysNode]], position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'pairs', tuple(pairs))

    def __repr__(self) -> str:
        return f'Dictionary(pairs={self.pairs!r})'

class PysSetNode(PysNode):

    __slots__ = ('elements',)

    @typechecked
    def __init__(self, elements: list[PysNode], position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'elements', tuple(elements))

    def __repr__(self) -> str:
        return f'Set(elements={self.elements!r})'

class PysListNode(PysNode):

    __slots__ = ('elements',)

    @typechecked
    def __init__(self, elements: list[PysNode], position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'elements', tuple(elements))

    def __repr__(self) -> str:
        return f'List(elements={self.elements!r})'

class PysTupleNode(PysNode):

    __slots__ = ('elements',)

    @typechecked
    def __init__(self, elements: list[PysNode], position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'elements', tuple(elements))

    def __repr__(self) -> str:
        return f'Tuple(elements={self.elements!r})'

class PysAttributeNode(PysNode):

    __slots__ = ('target', 'attribute')

    @typechecked
    def __init__(self, target: PysNode, attribute: PysToken) -> None:
        super().__init__(PysPosition(target.position.file, target.position.start, attribute.position.end))
        setimuattr(self, 'target', target)
        setimuattr(self, 'attribute', attribute)

    def __repr__(self) -> str:
        return f'Attribute(target={self.target!r}, attribute={self.attribute!r})'

class PysSubscriptNode(PysNode):

    __slots__ = ('target', 'slice')

    @typechecked
    def __init__(
        self,
        target: PysNode,
        slice: PysNode | slice | list[PysNode | slice],
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'target', target)
        setimuattr(self, 'slice', tuple(slice) if isinstance(slice, list) else slice)

    def __repr__(self) -> str:
        return f'Subscript(target={self.target!r}, slice={self.slice!r})'

class PysCallNode(PysNode):

    __slots__ = ('target', 'arguments')

    @typechecked
    def __init__(
        self,
        target: PysNode,
        arguments: list[PysNode | tuple[PysToken, PysNode]],
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'target', target)
        setimuattr(self, 'arguments', tuple(arguments))

    def __repr__(self) -> str:
        return f'Call(target={self.target!r}, arguments={self.arguments!r})'

class PysChainOperatorNode(PysNode):

    __slots__ = ('operations', 'expressions')

    @typechecked
    def __init__(self, operations: list[PysToken], expressions: list[PysNode]) -> None:
        super().__init__(
            PysPosition(
                expressions[0].position.file,
                expressions[0].position.start,
                expressions[-1].position.end
            )
        )

        setimuattr(self, 'operations', tuple(operations))
        setimuattr(self, 'expressions', tuple(expressions))

    def __repr__(self) -> str:
        return f'ChainOperator(operations={self.operations!r}, expressions={self.expressions!r})'

class PysTernaryOperatorNode(PysNode):

    __slots__ = ('condition', 'valid', 'invalid', 'style')

    @typechecked
    def __init__(
        self,
        condition: PysNode,
        valid: PysNode,
        invalid: PysNode,
        style: Literal['general', 'pythonic']
    ) -> None:
        super().__init__(
            PysPosition(condition.position.file, condition.position.start, invalid.position.end)
            if style == 'general' else
            PysPosition(condition.position.file, valid.position.start, invalid.position.end)
        )

        setimuattr(self, 'condition', condition)
        setimuattr(self, 'valid', valid)
        setimuattr(self, 'invalid', invalid)
        setimuattr(self, 'style', style)

    def __repr__(self) -> str:
        return (
            'TernaryOperator('
                f'condition={self.condition!r}, '
                f'valid={self.valid!r}, '
                f'invalid={self.invalid!r}, '
                f'style={self.style!r}'
            ')'
        )

class PysBinaryOperatorNode(PysNode):

    __slots__ = ('left', 'operand', 'right')

    @typechecked
    def __init__(self, left: PysNode, operand: PysToken, right: PysNode) -> None:
        super().__init__(PysPosition(left.position.file, left.position.start, right.position.end))
        setimuattr(self, 'left', left)
        setimuattr(self, 'operand', operand)
        setimuattr(self, 'right', right)

    def __repr__(self) -> str:
        return f'BinaryOperator(left={self.left!r}, operand={self.operand!r}, right={self.right!r})'

class PysUnaryOperatorNode(PysNode):

    __slots__ = ('operand', 'value', 'operand_position')

    @typechecked
    def __init__(self, operand: PysToken, value: PysNode, operand_position: Literal['left', 'right']) -> None:
        super().__init__(
            PysPosition(operand.position.file, operand.position.start, value.position.end)
            if operand_position == 'left' else
            PysPosition(operand.position.file, value.position.start, operand.position.end)
        )

        setimuattr(self, 'operand',  operand)
        setimuattr(self, 'value', value)
        setimuattr(self, 'operand_position', operand_position)

    def __repr__(self) -> str:
        return (
            'UnaryOperator('
                f'operand={self.operand!r}, '
                f'value={self.value!r}, '
                f'operand_position={self.operand_position!r}'
            ')'
        )

class PysStatementsNode(PysNode):

    __slots__ = ('body',)

    @typechecked
    def __init__(self, body: list[PysNode], position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'body', tuple(body))

    def __repr__(self) -> str:
        return f'Statements(body={self.body!r})'

class PysAssignNode(PysNode):

    __slots__ = ('target', 'operand', 'value')

    @typechecked
    def __init__(self, target: PysNode, operand: PysToken, value: PysNode) -> None:
        super().__init__(PysPosition(target.position.file, target.position.start, value.position.end))
        setimuattr(self, 'target', target)
        setimuattr(self, 'operand', operand)
        setimuattr(self, 'value', value)

    def __repr__(self) -> str:
        return f'Assign(target={self.target!r}, operand={self.operand!r}, value={self.value!r})'

class PysImportNode(PysNode):

    __slots__ = ('name', 'packages')

    @typechecked
    def __init__(
        self,
        name: tuple[PysToken, PysToken | None],
        packages: list[tuple[PysToken, PysToken | None]] | Literal['all'],
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'name', name)
        setimuattr(self, 'packages', tuple(packages) if isinstance(packages, list) else packages)

    def __repr__(self) -> str:
        return f'Import(name={self.name!r}, packages={self.packages!r})'

class PysIfNode(PysNode):

    __slots__ = ('cases_body', 'else_body')

    @typechecked
    def __init__(
        self,
        cases_body: list[tuple[PysNode, PysNode]],
        else_body: PysNode | None,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'cases_body', tuple(cases_body))
        setimuattr(self, 'else_body', else_body)

    def __repr__(self) -> str:
        return f'If(cases_body={self.cases_body!r}, else_body={self.else_body!r})'

class PysSwitchNode(PysNode):

    __slots__ = ('target', 'case_cases', 'default_body')

    @typechecked
    def __init__(
        self,
        target: PysNode,
        case_cases: list[tuple[PysNode, PysNode]],
        default_body: PysNode | None,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'target', target)
        setimuattr(self, 'case_cases', tuple(case_cases))
        setimuattr(self, 'default_body', default_body)

    def __repr__(self) -> str:
        return f'Switch(target={self.target!r}, case_cases={self.case_cases!r}, default_body={self.default_body!r})'

class PysMatchNode(PysNode):

    __slots__ = ('target', 'cases', 'default')

    @typechecked
    def __init__(
        self,
        target: PysNode | None,
        cases: list[tuple[PysNode, PysNode]],
        default: PysNode | None,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'target', target)
        setimuattr(self, 'cases', tuple(cases))
        setimuattr(self, 'default', default)

    def __repr__(self) -> str:
        return f'Match(target={self.target!r}, cases={self.cases!r}, default={self.default!r})'

class PysTryNode(PysNode):

    __slots__ = ('body', 'catch_cases', 'else_body', 'finally_body')

    @typechecked
    def __init__(
        self,
        body: PysNode,
        catch_cases: list[tuple[tuple[PysIdentifierNode | None, PysToken | None], PysNode]],
        else_body: PysNode | None,
        finally_body: PysNode | None,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'body', body)
        setimuattr(self, 'catch_cases', tuple(catch_cases))
        setimuattr(self, 'else_body', else_body)
        setimuattr(self, 'finally_body', finally_body)

    def __repr__(self) -> str:
        return (
            'Try('
                f'body={self.body!r}, '
                f'catch_cases={self.catch_cases!r}, '
                f'else_body={self.else_body!r}, '
                f'finally_body={self.finally_body!r}'
            ')'
        )

class PysWithNode(PysNode):

    __slots__ = ('contexts', 'body')

    @typechecked
    def __init__(self, contexts: list[tuple[PysNode, PysToken | None]], body: PysNode, position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'contexts', tuple(contexts))
        setimuattr(self, 'body', body)

    def __repr__(self) -> str:
        return f'With(contexts={self.contexts!r}, body={self.body!r})'

class PysForNode(PysNode):

    __slots__ = ('header', 'body', 'else_body')

    @typechecked
    def __init__(
        self,
        header: tuple[PysNode | None, PysNode | None, PysNode | None] |
                tuple[PysNode, PysNode],
        body: PysNode,
        else_body: PysNode | None,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'header', header)
        setimuattr(self, 'body', body)
        setimuattr(self, 'else_body', else_body)

    def __repr__(self) -> str:
        return f'For(header={self.header!r}, body={self.body!r}, else_body={self.else_body!r})'

class PysWhileNode(PysNode):

    __slots__ = ('condition', 'body', 'else_body')

    @typechecked
    def __init__(
        self,
        condition: PysNode,
        body: PysNode,
        else_body: PysNode | None,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'condition', condition)
        setimuattr(self, 'body', body)
        setimuattr(self, 'else_body', else_body)

    def __repr__(self) -> str:
        return f'While(condition={self.condition!r}, body={self.body!r}, else_body={self.else_body!r})'

class PysDoWhileNode(PysNode):

    __slots__ = ('body', 'condition', 'else_body')

    @typechecked
    def __init__(
        self,
        body: PysNode,
        condition: PysNode,
        else_body: PysNode | None,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'body', body)
        setimuattr(self, 'condition', condition)
        setimuattr(self, 'else_body', else_body)

    def __repr__(self) -> str:
        return f'DoWhile(body={self.body!r}, condition={self.condition!r}, else_body={self.else_body!r})'

class PysClassNode(PysNode):

    __slots__ = ('decorators', 'name', 'bases', 'body')

    @typechecked
    def __init__(
        self,
        decorators: list[PysNode],
        name: PysToken,
        bases: list[PysNode],
        body: PysNode,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'decorators', tuple(decorators))
        setimuattr(self, 'name', name)
        setimuattr(self, 'bases', tuple(bases))
        setimuattr(self, 'body', body)

    def __repr__(self) -> str:
        return f'Class(decorators={self.decorators!r}, name={self.name!r}, bases={self.bases!r}, body={self.body!r})'

class PysFunctionNode(PysNode):

    __slots__ = ('decorators', 'name', 'parameters', 'body', 'constructor')

    @typechecked
    def __init__(
        self,
        decorators: list[PysNode],
        name: PysToken | None,
        parameters: list[PysToken | tuple[PysToken, PysNode]],
        body: PysNode,
        constructor: bool,
        position: PysPosition
    ) -> None:

        super().__init__(position)
        setimuattr(self, 'decorators', tuple(decorators))
        setimuattr(self, 'name', name)
        setimuattr(self, 'parameters', tuple(parameters))
        setimuattr(self, 'body', body)
        setimuattr(self, 'constructor', bool(constructor))

    def __repr__(self) -> str:
        return (
            'Function('
                f'decorators={self.decorators!r}, '
                f'name={self.name!r}, '
                f'parameters={self.parameters!r}, '
                f'body={self.body!r}, '
                f'constructor={self.constructor!r}'
            ')'
        )

class PysGlobalNode(PysNode):

    __slots__ = ('identifiers',)

    @typechecked
    def __init__(self, identifiers: list[PysToken], position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'identifiers', tuple(frozenset(identifiers)))

    def __repr__(self) -> str:
        return f'Global(identifiers={self.identifiers!r})'

class PysReturnNode(PysNode):

    __slots__ = ('value',)

    @typechecked
    def __init__(self, value: PysNode | None, position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'value', value)

    def __repr__(self) -> str:
        return f'Return(value={self.value!r})'

class PysThrowNode(PysNode):

    __slots__ = ('target', 'cause')

    @typechecked
    def __init__(self, target: PysNode, cause: PysNode | None, position: PysPosition) -> None:
        super().__init__(
            PysPosition(
                position.file,
                position.start,
                target.position.end if cause is None else cause.position.end
            )
        )

        setimuattr(self, 'target', target)
        setimuattr(self, 'cause', cause)

    def __repr__(self) -> str:
        return f'Throw(target={self.target!r}, cause={self.cause!r})'

class PysAssertNode(PysNode):

    __slots__ = ('condition', 'message')

    @typechecked
    def __init__(self, condition: PysNode, message: PysNode | None) -> None:
        super().__init__(condition.position)
        setimuattr(self, 'condition', condition)
        setimuattr(self, 'message', message)

    def __repr__(self) -> str:
        return f'Assert(condition={self.condition!r}, message={self.message!r})'

class PysDeleteNode(PysNode):

    __slots__ = ('targets',)

    @typechecked
    def __init__(self, targets: list[PysNode], position: PysPosition) -> None:
        super().__init__(position)
        setimuattr(self, 'targets', tuple(targets))

    def __repr__(self) -> str:
        return f'Delete(targets={self.targets!r})'

class PysEllipsisNode(PysNode):

    __slots__ = ()

    def __repr__(self) -> Literal['Ellipsis()']:
        return 'Ellipsis()'

class PysContinueNode(PysNode):

    __slots__ = ()

    def __repr__(self) -> Literal['Continue()']:
        return 'Continue()'

class PysBreakNode(PysNode):

    __slots__ = ()

    def __repr__(self) -> Literal['Break()']:
        return 'Break()'