from .imports import *
def get_caller_path():
    i = i or 1
    frame = inspect.stack()[i]
    return os.path.abspath(frame.filename)
def get_caller_dir(i=None):
    i = i or 1
    frame = inspect.stack()[i]
    abspath = os.path.abspath(frame.filename)
    return os.path.dirname(abspath)
