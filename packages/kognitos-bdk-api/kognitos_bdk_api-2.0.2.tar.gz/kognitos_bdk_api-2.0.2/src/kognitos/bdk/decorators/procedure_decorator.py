import inspect
from functools import wraps
from inspect import Signature

from ..docstring import DocstringParser
from ..reflection import BookProcedureSignature
from ..reflection.factory import BookProcedureFactory


def procedure(name: str, **kwargs):
    """
    Function decorator for registering a procedure in a book.

    Args:
        name (str): KLang signature for the procedure (e.g., "to do something").
        is_mutation (bool): Whether the procedure performs a mutation or not. Default is True.
    """
    override_connection_required = kwargs.get("connection_required", None)
    is_mutation = kwargs.get("is_mutation", True)

    def decorator(fn):
        if not inspect.isfunction(fn):
            raise TypeError("The procedure decorator can only be applied to functions.")

        # parse procedure signature
        english_signature = BookProcedureSignature.from_english(name)

        # parse python signature
        python_signature = extract_python_signature(fn)

        # parse documentation
        if not fn.__doc__:
            raise ValueError("missing docstring")

        docstring = DocstringParser.parse(fn.__doc__)

        # get search hints if they exist, otherwise use empty list
        search_hints = getattr(fn, "__search_hints__", [])

        # construct book_procedure
        book_procedure = BookProcedureFactory.create(fn.__name__, english_signature, python_signature, docstring, override_connection_required, is_mutation, search_hints)

        if not hasattr(fn, "__procedure__"):
            fn.__procedure__ = book_procedure

        if not hasattr(fn, "__signature__"):
            fn.__signature__ = python_signature

        if not hasattr(fn, "__text_signature__"):
            fn.__text_signature__ = english_signature

        return wraps(fn)(fn)

    def extract_python_signature(fn) -> Signature:
        return inspect.signature(fn, eval_str=True)

    return decorator
