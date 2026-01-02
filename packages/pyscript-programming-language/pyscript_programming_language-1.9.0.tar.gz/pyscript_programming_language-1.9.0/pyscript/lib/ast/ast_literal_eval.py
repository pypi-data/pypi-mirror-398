from pyscript.core.interpreter import KW__DEBUG__, UNARY_FUNCTIONS_MAP_GETITEM, KEYWORDS_TO_VALUES_MAP_GETITEM
from pyscript.core.mapping import UNARY_FUNCTIONS_MAP
from pyscript.core.nodes import PysNode, PysIdentifierNode

def visit(node):
    return visitors[node.__class__](node)

def visit_unknown_node(node):
    raise ValueError(f"invalid node: {type(node).__name__}")

def visit_NumberNode(node):
    return node.value.value

def visit_StringNode(node):
    return node.value.value

def visit_KeywordNode(node):
    if (name := node.name.value) == KW__DEBUG__:
        raise ValueError(f"invalid constant keyword for {KW__DEBUG__}")
    #      vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv <- always boolean or nonetype
    return KEYWORDS_TO_VALUES_MAP_GETITEM(name)

def visit_DictionaryNode(node):
    return {visit(key): visit(value) for key, value in node.pairs}

def visit_SetNode(node):
    return set(map(visit, node.elements))

def visit_ListNode(node):
    return list(map(visit, node.elements))

def visit_TupleNode(node):
    return tuple(map(visit, node.elements))

def visit_CallNode(node):
    target = node.target
    if isinstance(target, PysIdentifierNode) and target.name.value == 'set' and not node.arguments:
        return set()
    raise ValueError("invalid call except for 'set()'")

def visit_UnaryOperatorNode(node):
    operand_token = node.operand
    #                                     vvvvvvvvvvvvvvvvvvv <- always __pos__, __neg__, and __inv__
    if (operand := operand_token.type) in UNARY_FUNCTIONS_MAP:
        return UNARY_FUNCTIONS_MAP_GETITEM(operand)(visit(node.value))
    raise ValueError(f"invalid unary operator: {operand_token}")

visitors = {
    class_node: globals().get('visit_' + class_node.__name__.removeprefix('Pys'), visit_unknown_node)
    for class_node in PysNode.__subclasses__()
}