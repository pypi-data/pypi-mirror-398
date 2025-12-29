import inspect
from functools import wraps


def discoverables(fn):
    if not inspect.isfunction(fn):
        raise TypeError("The discoverables decorator can only be applied to functions.")

    fn.__discoverables__ = True
    return wraps(fn)(fn)
