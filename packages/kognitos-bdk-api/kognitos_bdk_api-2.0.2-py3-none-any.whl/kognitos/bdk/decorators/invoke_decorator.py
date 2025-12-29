import inspect
from functools import wraps


def invoke(fn):
    if not inspect.isfunction(fn):
        raise TypeError("The invoke decorator can only be applied to functions.")

    fn.__invoke__ = True
    return wraps(fn)(fn)
