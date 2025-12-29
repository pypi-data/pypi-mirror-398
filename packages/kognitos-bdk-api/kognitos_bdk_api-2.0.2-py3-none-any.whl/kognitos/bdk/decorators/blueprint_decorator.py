import inspect
from functools import wraps
from typing import Optional

from ..reflection import BookProcedureSignature


def blueprint(*args):
    cls = Optional[type]

    # NOTE: We only care about the first argument, the rest of args and all kwargs are ignored.
    if len(args) >= 1 and inspect.isclass(args[0]):
        cls = args[0]

        def decorator(cls):
            if not hasattr(cls.__dict__, "__is_blueprint"):
                cls.__is_blueprint = True
            return cls

        return decorator(cls)

    raise ValueError("@blueprint decorator must be applied to a class.")


def blueprint_procedure(name: str):
    # This is here to verify that the english is valid
    BookProcedureSignature.from_english(name)

    def wrapper(fn):
        return wraps(fn)(fn)

    return wrapper
