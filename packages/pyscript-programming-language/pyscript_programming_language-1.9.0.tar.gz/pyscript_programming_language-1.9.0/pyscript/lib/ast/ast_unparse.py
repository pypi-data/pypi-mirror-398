from pyscript.core.checks import is_keyword
from pyscript.core.constants import TOKENS, KEYWORDS
from pyscript.core.mapping import SYMBOLS_TOKEN_MAP
from pyscript.core.nodes import PysNode
from pyscript.core.utils.string import indent as sindent

def indent(string):
    return sindent(string, 4)

def unparse(ast_obj):
    return visitors[ast_obj.__class__](ast_obj)

def visit_NumberNode(node):
    return repr(node.value.value)

def visit_StringNode(node):
    return repr(node.value.value)

def visit_KeywordNode(node):
    return node.name.value

def visit_IdentifierNode(node):
    name = node.name.value
    return f'${name}' if is_keyword(name) else name

def visit_DictionaryNode(node):
    return '{' + ', '.join(f'{unparse(key)}: {unparse(value)}' for key, value in node.pairs) + '}'

def visit_SetNode(node):
    return '{' + ', '.join(map(unparse, node.elements)) + '}'

def visit_ListNode(node):
    return '[' + ', '.join(map(unparse, node.elements)) + ']'

def visit_TupleNode(node):
    return '(' + ', '.join(map(unparse, node.elements)) + ')'

def visit_AttributeNode(node):
    return f'{unparse(node.target)}.{node.attribute.value}'

def visit_SubscriptNode(node):
    string = unparse(node.target)
    string += '['

    if isinstance(node.slice, slice):
        if node.slice.start:
            string += unparse(node.slice.start)
        string += ':'
        if node.slice.stop:
            string += unparse(node.slice.stop)
        string += ':'
        if node.slice.step:
            string += unparse(node.slice.step)

    elif isinstance(node.slice, tuple):
        indices = []

        for index in node.slice:
            index_string = ''

            if isinstance(index, slice):
                if index.start:
                    index_string += unparse(index.start)
                index_string += ':'
                if index.stop:
                    index_string += unparse(index.stop)
                index_string += ':'
                if index.step:
                    index_string += unparse(index.step)
            else:
                index_string += unparse(index)

            indices.append(index_string)

        string += indices[0] + ',' if len(indices) == 1 else ', '.join(indices)

    else:
        string += unparse(node.slice)

    string += ']'

    return string

def visit_CallNode(node):
    arguments = []

    for argument in node.arguments:
        if isinstance(argument, tuple):
            keyword, argument = argument
            arguments.append(f'{keyword.value}={unparse(argument)}')
        else:
            arguments.append(unparse(argument))

    return f'{unparse(node.target)}({", ".join(arguments)})'

def visit_ChainOperatorNode(node):
    string = unparse(node.expressions[0])

    for i, operand in enumerate(node.operations):
        string += ' '

        if operand.match(TOKENS['KEYWORD'], KEYWORDS['in']):
            string += KEYWORDS['in']
        elif operand.match(TOKENS['KEYWORD'], KEYWORDS['is']):
            string += KEYWORDS['is']
        else:
            string += SYMBOLS_TOKEN_MAP[operand.type]

        string += ' '
        string += unparse(node.expressions[i + 1])

    return f'({string})'

def visit_TernaryOperatorNode(node):
    return f'({unparse(node.condition)} ? {unparse(node.valid)} : {unparse(node.invalid)})'

def visit_BinaryOperatorNode(node):
    if node.operand.match(TOKENS['KEYWORD'], KEYWORDS['and']):
        operand = '&&'
    elif node.operand.match(TOKENS['KEYWORD'], KEYWORDS['or']):
        operand = '||'
    else:
        operand = SYMBOLS_TOKEN_MAP[node.operand.type]

    return f'({unparse(node.left)} {operand} {unparse(node.right)})'

def visit_UnaryOperatorNode(node):
    if node.operand.match(TOKENS['KEYWORD'], KEYWORDS['not']):
        operand = '!'
    else:
        operand = SYMBOLS_TOKEN_MAP[node.operand.type]

    value = unparse(node.value)

    return '(' + (operand + value if node.operand_position == 'left' else value + operand) + ')'

def visit_StatementsNode(node):
    return '\n'.join(map(unparse, node.body))

def visit_AssignNode(node):
    return f'{unparse(node.target)} {SYMBOLS_TOKEN_MAP[node.operand.type]} {unparse(node.value)}'

def visit_ImportNode(node):
    string = ''

    name, as_name = node.name
    name_string = name.value if name.type == TOKENS['IDENTIFIER'] else repr(name.value)

    if as_name:
        name_string += ' '
        name_string += KEYWORDS['as']
        name_string += ' '
        name_string += as_name.value

    if node.packages == 'all':
        string += KEYWORDS['from']
        string += ' '
        string += name_string
        string += ' '
        string += KEYWORDS['import']
        string += ' *'

    elif node.packages:
        packages = []

        for package, as_package in node.packages:
            package_string = ''

            if as_package:
                package_string += package.value
                package_string += ' '
                package_string += KEYWORDS['as']
                package_string += ' '
                package_string += as_package.value
            else:
                package_string += package.value

            packages.append(package_string)

        string += KEYWORDS['from']
        string += ' '
        string += name_string
        string += ' '
        string += KEYWORDS['import']
        string += ' '
        string += ', '.join(packages)

    else:
        string += KEYWORDS['import']
        string += ' '
        string += name_string

    return string

def visit_IfNode(node):
    cases = []

    for i, (condition, body) in enumerate(node.cases_body):
        case_string = KEYWORDS['if'] if i == 0 else KEYWORDS['elif']
        case_string += ' ('
        case_string += unparse(condition)
        case_string += ') {\n'
        case_string += indent(unparse(body))
        case_string += '\n}'

        cases.append(case_string)

    string = '\n'.join(cases)

    if node.else_body:
        string += '\n'
        string += KEYWORDS['else']
        string += ' {\n'
        string += indent(unparse(node.else_body))
        string += '\n}'

    return string

def visit_SwitchNode(node):
    cases = []

    for condition, body in node.case_cases:
        case_string = KEYWORDS['case']
        case_string += ' '
        case_string += unparse(condition)
        case_string += ':\n'
        case_string += indent(unparse(body))

        cases.append(case_string)

    if node.default_body:
        default_string = KEYWORDS['default']
        default_string += ':\n'
        default_string += indent(unparse(node.default_body))

        cases.append(default_string)

    string = KEYWORDS['switch']
    string += ' ('
    string += unparse(node.target)
    string += ') {\n'
    string += '\n'.join(map(indent, cases))
    string += '\n}'

    return string

def visit_MatchNode(node):
    string = KEYWORDS['match']
    string += ' '

    if node.target:
        string += '('
        string += unparse(node.target)
        string += ') '

    cases = []

    for condition, value in node.cases:
        case_string = unparse(condition)
        case_string += ': '
        case_string += unparse(value)

        cases.append(case_string)

    if node.default:
        default_string = KEYWORDS['default']
        default_string += ': '
        default_string += unparse(node.default)

        cases.append(default_string)

    string += '{\n'
    string += indent(',\n'.join(cases))
    string += '\n}'

    return string

def visit_TryNode(node):
    catch_cases = []

    for (name, parameter), body in node.catch_cases:
        name_string = ''

        if not (name is None and parameter is None):
            name_string += ' ('

            if name is None:
                name_string += parameter.value
            else:
                name_string += name.name.value
                name_string += ' '
                name_string += parameter.value

            name_string += ')'

        catch_string = KEYWORDS['catch']
        catch_string += name_string
        catch_string += ' {\n'
        catch_string += indent(unparse(body))
        catch_string += '\n}'

        catch_cases.append(catch_string)

    string = KEYWORDS['try']
    string += ' {\n'
    string += indent(unparse(node.body))
    string += '\n}'
    string += '\n'
    string += '\n'.join(catch_cases)

    if catch_cases:
        string += '\n'

    if node.else_body:
        string += KEYWORDS['else']
        string += ' {\n'
        string += indent(unparse(node.else_body))
        string += '\n}'

    if node.finally_body:
        string += KEYWORDS['finally']
        string += ' {\n'
        string += indent(unparse(node.finally_body))
        string += '\n}'

    return string

def visit_WithNode(node):
    contexts = []

    for context, alias in node.contexts:
        context_string = unparse(context)

        if alias:
            context_string += ' '
            context_string += KEYWORDS['as']
            context_string += ' '
            context_string += alias.value

        contexts.append(context_string)

    string = KEYWORDS['with']
    string += ' ('
    string += ', '.join(contexts)
    string += ') {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    return string

def visit_ForNode(node):
    string = KEYWORDS['for']
    string += ' ('

    if len(node.header) == 2:
        declaration, iteration = node.header

        string += unparse(declaration)
        string += ' '
        string += KEYWORDS['of']
        string += ' '
        string += unparse(iteration)

    elif len(node.header) == 3:
        declaration, condition, update = node.header

        if declaration:
            string += unparse(declaration)
        string += ';'
        if condition:
            string += unparse(condition)
        string += ';'
        if update:
            string += unparse(update)

    string += ') {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    return string

def visit_WhileNode(node):
    string = KEYWORDS['while']
    string += ' ('
    string += unparse(node.condition)
    string += ') {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    return string

def visit_DoWhileNode(node):
    string = KEYWORDS['do']
    string += ' {\n'
    string += indent(unparse(node.body))
    string += '\n} '
    string += KEYWORDS['while']
    string += ' ('
    string += unparse(node.condition)
    string += ')'

    return string

def visit_ClassNode(node):
    bases = []
    decorators = []

    for decorator in node.decorators:
        decorators.append(f'@{unparse(decorator)}')

    for base in node.bases:
        bases.append(unparse(base))

    string = ''

    if decorators:
        string += '\n'.join(decorators)
        string += '\n'

    string += KEYWORDS['class']
    string += ' '
    string += node.name.value

    if bases:
        string += '('
        string += ', '.join(bases)
        string += ')'

    string += ' {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    return string

def visit_FunctionNode(node):
    decorators = []
    parameters = []

    for decorator in node.decorators:
        decorators.append(f'@{unparse(decorator)}')

    for parameter in node.parameters:
        if isinstance(parameter, tuple):
            parameter, value = parameter
            parameters.append(f'{parameter.value}={unparse(value)}')
        else:
            parameters.append(parameter.value)

    string = ''

    if decorators:
        string += '\n'.join(decorators)
        string += '\n'

    if node.constructor:
        string += KEYWORDS['constructor']
    else:
        string += KEYWORDS['func']
        if node.name:
            string += ' '
            string += node.name.value

    string += '('
    string += ', '.join(parameters)
    string += ') {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    return string

def visit_GlobalNode(node):
    string = KEYWORDS['global']
    string += ' '
    string += ', '.join(name.value for name in node.identifiers)
    return string

def visit_ReturnNode(node):
    string = KEYWORDS['return']

    if node.value:
        string += ' '
        string += unparse(node.value)

    return string

def visit_ThrowNode(node):
    string = KEYWORDS['throw']
    string += ' '
    string += unparse(node.target)

    if node.cause:
        string += ' '
        string += KEYWORDS['from']
        string += ' '
        string += unparse(node.cause)

    return string

def visit_AssertNode(node):
    string = KEYWORDS['assert']
    string += ' '
    string += unparse(node.condition)

    if node.message:
        string += ', '
        string += unparse(node.message)

    return string

def visit_DeleteNode(node):
    string = KEYWORDS['del']
    string += ' '
    string += ', '.join(map(unparse, node.targets))
    return string

def visit_EllipsisNode(node):
    return '...'

def visit_ContinueNode(node):
    return KEYWORDS['continue']

def visit_BreakNode(node):
    return KEYWORDS['break']

visitors = {
    class_node: globals()['visit_' + class_node.__name__.removeprefix('Pys')]
    for class_node in PysNode.__subclasses__()
}