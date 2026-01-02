from os import getcwd as osgetcwd
from os.path import sep, abspath as osabspath, normpath as osnormpath, splitext, basename

from .string import normstr

def getcwd():
    try:
        return osgetcwd()
    except:
        return '.'

def abspath(path):
    try:
        return osabspath(path)
    except:
        return path

def base(path):
    return splitext(basename(path))[0]

def extension(path):
    return splitext(basename(path))[1]

def normpath(*paths, absolute=True):
    path = osnormpath(sep.join(map(normstr, paths)))
    return abspath(path) if absolute else path