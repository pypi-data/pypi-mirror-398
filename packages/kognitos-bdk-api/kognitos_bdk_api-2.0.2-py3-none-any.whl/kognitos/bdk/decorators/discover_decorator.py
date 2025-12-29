import inspect
from functools import wraps


def discover(fn):
    if not inspect.isfunction(fn):
        raise TypeError("The discover decorator can only be applied to functions.")

    fn.__discover__ = True
    return wraps(fn)(fn)
