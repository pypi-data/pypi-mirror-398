from pyscript.core.checks import is_keyword
from pyscript.core.constants import TOKENS
from pyscript.core.mapping import SYMBOLS_TOKEN_MAP

def untokenize(iterable):
    tokens = []

    for token in iterable:
        type = token.type
        value = token.value

        if type == TOKENS['NULL']:
            break
        elif type == TOKENS['KEYWORD']:
            tokens.append(f' {value} ')
        elif type == TOKENS['IDENTIFIER']:
            tokens.append(f'${value} ' if is_keyword(value) else f' {value} ')
        elif type in (TOKENS['NUMBER'], TOKENS['STRING']):
            tokens.append(repr(value))
        elif type == TOKENS['COMMENT']:
            tokens.append(f' #{value}')
        elif type == TOKENS['NONE']:
            tokens.append(token.position.file.text[token.position.start:token.position.end])
        else:
            tokens.append(SYMBOLS_TOKEN_MAP[type])

    return ''.join(tokens)