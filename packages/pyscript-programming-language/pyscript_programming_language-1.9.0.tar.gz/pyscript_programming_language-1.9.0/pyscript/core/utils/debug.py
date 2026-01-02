from ..constants import ENV_PYSCRIPT_NO_EXCEPTHOOK
from ..exceptions import PysSignal

from os import environ
from sys import excepthook

import sys

def print_display(value):
    if value is not None:
        print(repr(value))

def print_traceback(exc_type, exc_value, exc_tb):
    for line in exc_tb.string_traceback().splitlines():
        print(line, file=sys.stderr)

def sys_excepthook(exc_type, exc_value, exc_tb):
    if exc_type is PysSignal and (traceback := exc_value.result.error) is not None:
        print_traceback(None, None, traceback)
        print('\nThe above PyScript exception was the direct cause of the following exception:\n', file=sys.stderr)
    excepthook(exc_type, exc_value, exc_tb)

def thread_excepthook(args):
    sys_excepthook(args.exc_type, args.exc_value, args.exc_traceback)

if environ.get(ENV_PYSCRIPT_NO_EXCEPTHOOK) is None:
    import threading

    sys.excepthook = sys_excepthook
    threading.excepthook = thread_excepthook