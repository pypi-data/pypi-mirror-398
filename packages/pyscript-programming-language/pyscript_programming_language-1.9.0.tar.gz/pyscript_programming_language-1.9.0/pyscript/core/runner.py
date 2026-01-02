from .analyzer import PysAnalyzer
from .buffer import PysFileBuffer
from .cache import undefined, hook, PysUndefined
from .constants import DEFAULT, SILENT, RETURN_RESULT, HIGHLIGHT, NO_COLOR
from .context import PysContext
from .exceptions import PysTraceback, PysSignal
from .handlers import handle_call
from .interpreter import visit
from .lexer import PysLexer
from .parser import PysParser
from .position import PysPosition
from .pysbuiltins import require
from .results import PysRunTimeResult, PysExecuteResult
from .symtab import PysSymbolTable, new_symbol_table
from .utils.ansi import BOLD, acolor
from .utils.decorators import _TYPECHECK, typechecked
from .utils.generic import setimuattr, get_frame, get_locals, import_readline
from .utils.shell import PysCommandLineShell
from .version import version

from types import ModuleType
from typing import Any, Literal, Optional

import sys

def _normalize_globals(file, globals):
    if globals is None:
        symtab, _ = new_symbol_table(symbols=get_locals(3 if _TYPECHECK else 2))
    elif globals is undefined:
        symtab, _ = new_symbol_table(file=file.name, name='__main__')
    elif isinstance(globals, dict):
        symtab, _ = new_symbol_table(symbols=globals)
    else:
        symtab = globals
    return symtab

@typechecked
def pys_runner(
    file: PysFileBuffer,
    mode: Literal['exec', 'eval', 'single'],
    symbol_table: PysSymbolTable,
    flags: Optional[int] = None,
    context_parent: Optional[PysContext] = None,
    context_parent_entry_position: Optional[PysPosition] = None
) -> PysExecuteResult:

    context = PysContext(
        file=file,
        name='<program>',
        flags=flags,
        symbol_table=symbol_table,
        parent=context_parent,
        parent_entry_position=context_parent_entry_position
    )

    result = PysExecuteResult(context)
    runtime_runner_result = PysRunTimeResult()
    position = PysPosition(file, -1, -1)

    with runtime_runner_result(context, position):

        try:

            lexer = PysLexer(
                file=file,
                flags=context.flags & ~HIGHLIGHT,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            tokens, error = lexer.make_tokens()
            if error:
                return result.failure(error)

            parser = PysParser(
                tokens=tokens,
                flags=context.flags,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            ast = parser.parse(parser.expr if mode == 'eval' else None)
            if ast.error:
                return result.failure(ast.error)

            analyzer = PysAnalyzer(
                node=ast.node,
                flags=parser.flags,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            error = analyzer.analyze()
            if error:
                return result.failure(error)

        except RecursionError:
            return result.failure(
                PysTraceback(
                    RecursionError("maximum recursion depth exceeded during complication"),
                    context,
                    position
                )
            )

        setimuattr(context, 'flags', parser.flags)
        runtime_result = visit(ast.node, context)

        if runtime_result.error:
            return result.failure(runtime_result.error)

        if mode == 'single' and hook.display is not None:
            hook.display(runtime_result.value)
        return result.success(runtime_result.value)

    if runtime_runner_result.error:
        return result.failure(runtime_runner_result.error)

@typechecked
def pys_exec(
    source,
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT
) -> None | PysExecuteResult:

    """
    Execute a PyScript code from source given.

    Parameters
    ----------
    source: A valid PyScript source code.

    globals: A namespace dictionary or symbol table that can be accessed. \
             If it is None, it uses the current global namespace at the Python level. \
             If it is undefined, it creates a new default PyScript namespace.

    flags: A special flags.
    """

    file = PysFileBuffer(source)

    result = pys_runner(
        file=file,
        mode='exec',
        symbol_table=_normalize_globals(file, globals),
        flags=flags
    )

    if flags & RETURN_RESULT:
        return result

    elif result.error and not (flags & SILENT):
        raise PysSignal(PysRunTimeResult().failure(result.error))

@typechecked
def pys_eval(
    source,
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT
) -> Any | PysExecuteResult:

    """
    Evaluate a PyScript code from source given.

    Parameters
    ----------
    source: A valid PyScript (Expression) source code.

    globals: A namespace dictionary or symbol table that can be accessed. \
             If it is None, it uses the current global namespace at the Python level. \
             If it is undefined, it creates a new default PyScript namespace.

    flags: A special flags.
    """

    file = PysFileBuffer(source)

    result = pys_runner(
        file=file,
        mode='eval',
        symbol_table=_normalize_globals(file, globals),
        flags=flags
    )

    if flags & RETURN_RESULT:
        return result

    elif result.error and not (flags & SILENT):
        raise PysSignal(PysRunTimeResult().failure(result.error))

    return result.value

@typechecked
def pys_require(name, flags: int = DEFAULT) -> ModuleType | Any:

    """
    Import a PyScript module.

    Parameters
    ----------
    name: A name or path of the module to be imported.

    flags: A special flags.
    """

    file = PysFileBuffer('', get_frame(2 if _TYPECHECK else 1).f_code.co_filename)
    handle_call(require, PysContext(file=file, flags=flags), PysPosition(file, -1, -1))
    return require(name)

@typechecked
def pys_shell(
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT
) -> int | Any:

    """
    Start an interactive PyScript shell.

    Parameters
    ----------
    globals: A namespace dictionary or symbol table that can be accessed. \
             If it is None, it uses the current global namespace at the Python level. \
             If it is undefined, it creates a new default PyScript namespace.

    flags: A special flags.
    """

    if hook.running_shell:
        raise RuntimeError("another shell is still running")

    file = PysFileBuffer('', '<pyscript-shell>')
    symtab = _normalize_globals(file, globals)
    shell = PysCommandLineShell()
    line = 0

    if flags & NO_COLOR:
        reset = ''
        bmagenta = ''
    else:
        reset = acolor('reset')
        bmagenta = acolor('magenta', style=BOLD)

    import_readline()

    print(f'PyScript {version}')
    print(f'Python {sys.version}')
    print('Type "help" or "license" for more information; Type "exit" or "/exit" to exit the shell')

    try:
        hook.running_shell = True

        while True:

            try:
                shell.ps1 = f'{bmagenta}{hook.ps1}{reset}'
                shell.ps2 = f'{bmagenta}{hook.ps2}{reset}'

                text = shell.input()
                if text == 0:
                    return 0

                result = pys_runner(
                    file=PysFileBuffer(text, f'<pyscript-shell-{line}>'),
                    mode='single',
                    symbol_table=symtab,
                    flags=flags
                )

                flags = result.context.flags
                code, exit = result.process()
                if exit:
                    return code
                elif code == 0:
                    line += 1

            except KeyboardInterrupt:
                shell.reset()
                print(f'\r{bmagenta}KeyboardInterrupt{reset}', file=sys.stderr)

            except EOFError:
                print()
                return 0

    finally:
        hook.running_shell = False