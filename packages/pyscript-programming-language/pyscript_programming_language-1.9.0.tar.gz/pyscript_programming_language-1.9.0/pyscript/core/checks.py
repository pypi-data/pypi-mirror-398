from .constants import TOKENS, KEYWORDS, CONSTANT_KEYWORDS
from .mapping import BRACKETS_MAP
from .nodes import *

is_expression = frozenset([
    PysNumberNode, PysStringNode, PysKeywordNode, PysIdentifierNode, PysDictionaryNode, PysSetNode, PysListNode,
    PysTupleNode, PysAttributeNode, PysSubscriptNode, PysCallNode, PysChainOperatorNode, PysTernaryOperatorNode,
    PysBinaryOperatorNode, PysUnaryOperatorNode, PysMatchNode, PysFunctionNode, PysEllipsisNode
]).__contains__

is_statement = frozenset([
    PysStatementsNode, PysAssignNode, PysImportNode, PysIfNode, PysSwitchNode, PysTryNode, PysWithNode, PysForNode,
    PysWhileNode, PysDoWhileNode, PysClassNode, PysGlobalNode, PysReturnNode, PysThrowNode, PysAssertNode,
    PysDeleteNode, PysContinueNode, PysBreakNode
]).__contains__

is_unpack_assignment = frozenset([
    PysSetNode, PysListNode, PysTupleNode
]).__contains__

is_keyword = frozenset(KEYWORDS.values()).__contains__

is_python_extensions = frozenset([
    '.py', '.ipy', '.pyc', '.pyd', '.pyi', '.pyo', '.pyp', '.pyw', '.pyz', '.rpy', '.xpy', '.pyproj'
]).__contains__

is_equals = frozenset([
    TOKENS['EQUAL'], TOKENS['EQUAL-COLON']
]).__contains__

is_incremental = frozenset([
    TOKENS['DOUBLE-PLUS'], TOKENS['DOUBLE-MINUS']
]).__contains__

is_blacklist_python_builtins = frozenset([
    'IndentationError', 'TabError', 'breakpoint', 'compile', 'copyright', 'credits', 'dir', 'eval', 'exec', 'help',
    'globals', 'license', 'locals', 'vars'
]).__contains__

is_left_bracket = frozenset(BRACKETS_MAP.keys()).__contains__
is_right_bracket = frozenset(BRACKETS_MAP.values()).__contains__
is_bracket = frozenset(BRACKETS_MAP.keys() | BRACKETS_MAP.values()).__contains__

is_constant_keywords = frozenset(CONSTANT_KEYWORDS).__contains__

is_private_attribute = lambda name : name.startswith('_') if isinstance(name, str) else name
is_public_attribute = lambda name : not name.startswith('_') if isinstance(name, str) else name