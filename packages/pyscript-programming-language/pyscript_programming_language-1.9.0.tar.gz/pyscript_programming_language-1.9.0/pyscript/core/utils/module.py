from .path import normpath, base, extension

from os.path import isdir, isfile, join

import sys

def get_module_name_from_path(path):
    return base(normpath(path, absolute=False))

def get_module_path(path):
    from ..checks import is_python_extensions  # circular import problem solved

    if isfile(path) and not is_python_extensions(extension(path)):
        return path

    candidate = path + '.pys'
    if isfile(candidate):
        return candidate

    candidate = join(path, '__init__.pys')
    if isdir(path) and isfile(candidate):
        return candidate

def set_python_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)

def remove_python_path(path):
    if path in sys.path:
        sys.path.remove(path)