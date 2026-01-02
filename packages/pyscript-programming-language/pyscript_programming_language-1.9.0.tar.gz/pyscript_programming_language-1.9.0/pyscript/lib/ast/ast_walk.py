from pyscript.core.nodes import *

def walk(node):

    if isinstance(node, PysDictionaryNode):
        yield node

        for key, value in node.pairs:
            yield from walk(key)
            yield from walk(value)

    elif isinstance(node, (PysSetNode, PysListNode, PysTupleNode)):
        yield node

        for element in node.elements:
            yield from walk(element)

    elif isinstance(node, PysAttributeNode):
        yield node
        yield from walk(node.target)

    elif isinstance(node, PysSubscriptNode):
        yield node
        yield from walk(node.target)

        if isinstance(node.slice, slice):
            if node.slice.start:
                yield from walk(node.slice.start)
            if node.slice.stop:
                yield from walk(node.slice.stop)
            if node.slice.step:
                yield from walk(node.slice.step)

        elif isinstance(node.slice, tuple):
            for index in node.slice:
                if isinstance(index, slice):
                    if index.start:
                        yield from walk(index.start)
                    if index.stop:
                        yield from walk(index.stop)
                    if index.step:
                        yield from walk(index.step)
                else:
                    yield from walk(index)

        else:
            yield from walk(node.slice)

    elif isinstance(node, PysCallNode):
        yield node
        yield from walk(node.target)

        for argument in node.arguments:
            if isinstance(argument, tuple):
                yield from walk(argument[1])
            else:
                yield from walk(argument)

    elif isinstance(node, PysChainOperatorNode):
        yield node

        for expression in node.expressions:
            yield from walk(expression)

    elif isinstance(node, PysTernaryOperatorNode):
        yield node

        if node.style == 'general':
            yield from walk(node.condition)
            yield from walk(node.valid)
        elif node.style == 'pythonic':
            yield from walk(node.valid)
            yield from walk(node.condition)
        else:
            raise ValueError(f"invalid PysTernaryOperatorNode.style named {node.style!r}")

        yield from walk(node.invalid)

    elif isinstance(node, PysBinaryOperatorNode):
        yield node
        yield from walk(node.left)
        yield from walk(node.right)

    elif isinstance(node, PysUnaryOperatorNode):
        yield node

        if node.operand_position not in ('left', 'right'):
            raise ValueError(f"invalid PysUnaryOperatorNode.operand_position named {node.operand_position!r}")

        yield from walk(node.value)

    elif isinstance(node, PysStatementsNode):
        yield node

        for statement in node.body:
            yield from walk(statement)

    elif isinstance(node, PysAssignNode):
        yield node
        yield from walk(node.target)
        yield from walk(node.value)

    elif isinstance(node, PysImportNode):
        yield node

    elif isinstance(node, PysIfNode):
        yield node

        for condition, body in node.cases_body:
            yield from walk(condition)
            yield from walk(body)

        if node.else_body:
            yield from walk(node.else_body)

    elif isinstance(node, PysSwitchNode):
        yield node
        yield from walk(node.target)

        for condition, body in node.case_cases:
            yield from walk(condition)
            yield from walk(body)

        if node.default_body:
            yield from walk(node.default_body)

    elif isinstance(node, PysMatchNode):
        yield node

        if node.target:
            yield from walk(node.target)

        for condition, value in node.cases:
            yield from walk(condition)
            yield from walk(value)

        if node.default:
            yield from walk(node.default)

    elif isinstance(node, PysTryNode):
        yield node
        yield from walk(node.body)

        for (error, parameter), body in node.catch_cases:
            if error:
                yield from walk(error)
            yield from walk(body)

        if node.else_body:
            yield from walk(node.else_body)

        if node.finally_body:
            yield from walk(node.finally_body)

    elif isinstance(node, PysWithNode):
        yield node

        for context, _ in node.contexts:
            yield from walk(context)

        yield from walk(node.body)

    elif isinstance(node, PysForNode):
        yield node

        if len(node.header) == 2:
            yield from walk(node.header[0])
            yield from walk(node.header[1])

        elif len(node.header) == 3:
            for part in node.header:
                if part:
                    yield from walk(part)

        else:
            raise TypeError("invalid PysForNode.header")

        yield from walk(node.body)

        if node.else_body:
            yield from walk(node.else_body)

    elif isinstance(node, PysWhileNode):
        yield node
        yield from walk(node.condition)
        yield from walk(node.body)

        if node.else_body:
            yield from walk(node.else_body)

    elif isinstance(node, PysDoWhileNode):
        yield node
        yield from walk(node.body)
        yield from walk(node.condition)

        if node.else_body:
            yield from walk(node.else_body)

    elif isinstance(node, PysClassNode):
        yield node

        for decorator in node.decorators:
            yield from walk(decorator)

        for base in node.bases:
            yield from walk(base)

        yield from walk(node.body)

    elif isinstance(node, PysFunctionNode):
        yield node

        for decorator in node.decorators:
            yield from walk(decorator)

        for parameter in node.parameters:
            if isinstance(parameter, tuple):
                yield from walk(parameter[1])

        yield from walk(node.body)

    elif isinstance(node, PysGlobalNode):
        yield node

    elif isinstance(node, PysReturnNode):
        yield node

        if node.value:
            yield from walk(node.value)

    elif isinstance(node, PysThrowNode):
        yield node
        yield from walk(node.target)

        if node.cause:
            yield from walk(node.cause)

    elif isinstance(node, PysAssertNode):
        yield node
        yield from walk(node.condition)

        if node.message:
            yield from walk(node.message)

    elif isinstance(node, PysDeleteNode):
        yield node

        for target in node.targets:
            yield from walk(target)

    elif isinstance(node, PysNode):
        yield node

    else:
        raise TypeError("unknown Node")