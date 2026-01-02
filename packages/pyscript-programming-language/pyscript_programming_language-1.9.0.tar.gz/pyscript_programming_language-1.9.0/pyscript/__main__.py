from .core.buffer import PysFileBuffer
from .core.cache import path, undefined
from .core.constants import DEFAULT, DEBUG, NO_COLOR
from .core.highlight import HLFMT_HTML, HLFMT_ANSI, HLFMT_BBCODE, pys_highlight
from .core.runner import _normalize_globals, pys_runner, pys_shell
from .core.utils.module import get_module_name_from_path
from .core.utils.path import normpath
from .core.version import __version__

from argparse import ArgumentParser
from os import environ

import sys

FORMAT_HIGHLIGHT_MAP = {
    'html': HLFMT_HTML,
    'ansi': HLFMT_ANSI,
    'bbcode': HLFMT_BBCODE
}

parser = ArgumentParser(
    prog=f'{get_module_name_from_path(sys.executable)} -m pyscript',
    description=f'PyScript Launcher for Python Version {".".join(map(str, sys.version_info))}'
)

parser.add_argument(
    'file',
    type=str,
    nargs='?',
    default=None,
    help="File path to be executed"
)

parser.add_argument(
    '-v', '--version',
    action='version',
    version=f"PyScript {__version__}",
)

parser.add_argument(
    '-c', '--command',
    type=str,
    default=None,
    help="Execute program from a string argument",
)

parser.add_argument(
    '-d', '--debug',
    action='store_true',
    help="Set a debug flag, this will remove the assert statement"
)

parser.add_argument(
    '-i', '--inspect',
    action='store_true',
    help="Inspect interactively after running a 'file'",
)

parser.add_argument(
    '-l', '--highlight',
    choices=tuple(FORMAT_HIGHLIGHT_MAP.keys()),
    default=None,
    help="Generate highlight code from a 'file'"
)

parser.add_argument(
    '-n', '--no-color',
    action='store_true',
    help="Suppress colored output"
)

parser.add_argument(
    '-r', '--py-recursion',
    type=int,
    default=None,
    help="Set a Python recursion limit"
)

def argument_error(argument, message):
    parser.print_usage(sys.stderr)
    parser.exit(2, f"{parser.prog}: error: argument {argument}: {message}\n")

args = parser.parse_args()

if args.highlight and args.file is None:
    argument_error("-l/--highlight", "argument 'file' required")

if args.py_recursion is not None:
    try:
        sys.setrecursionlimit(args.py_recursion)
    except BaseException as e:
        argument_error("-r/--py-recursion", e)

code = 0
flags = DEFAULT

if args.debug:
    flags |= DEBUG
if args.no_color or environ.get('NO_COLOR') is not None:
    flags |= NO_COLOR

if args.file is not None:
    path = normpath(args.file)

    try:
        with open(path, 'r', encoding='utf-8') as file:
            file = PysFileBuffer(file, path)
    except FileNotFoundError:
        parser.error(f"can't open file {path!r}: No such file or directory")
    except PermissionError:
        parser.error(f"can't open file {path!r}: Permission denied.")
    except IsADirectoryError:
        parser.error(f"can't open file {path!r}: Path is not a file.")
    except NotADirectoryError:
        parser.error(f"can't open file {path!r}: Attempting to access directory from file.")
    except (OSError, IOError):
        parser.error(f"can't open file {path!r}: Attempting to access a system directory or file.")
    except UnicodeDecodeError:
        parser.error(f"can't read file {path!r}: Bad file.")
    except BaseException as e:
        parser.error(f"file {path!r}: Unexpected error: {e}")

    if args.highlight:
        try:
            print(pys_highlight(file, FORMAT_HIGHLIGHT_MAP.get(args.highlight)))
        except BaseException as e:
            parser.error(f"file {path!r}: Highlight error: {e}")

    else:
        result = pys_runner(
            file=file,
            mode='exec',
            symbol_table=_normalize_globals(file, undefined),
            flags=flags
        )

        if args.inspect:
            code = pys_shell(result.context.symbol_table, result.context.flags)
        else:
            code = result.process()[0]

elif args.command is not None:
    file = PysFileBuffer(args.command)
    code = pys_runner(
        file=file,
        mode='exec',
        symbol_table=_normalize_globals(file, undefined),
        flags=flags
    ).process()[0]

else:
    code = pys_shell(undefined, flags)

sys.exit(code)