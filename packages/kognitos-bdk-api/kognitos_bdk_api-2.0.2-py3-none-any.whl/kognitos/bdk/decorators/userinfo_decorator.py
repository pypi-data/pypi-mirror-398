import inspect
from functools import wraps

from kognitos.bdk.api.errors import InvalidUserInfoOutputType
from kognitos.bdk.api.user_info import UserInfo


def userinfo(fn):
    """
    Function decorator for flagging the user information function in a book.

    A user information function outputs information about the authenticated user in an OAuth connected book.
    """

    if not inspect.isfunction(fn):
        raise TypeError("The userinfo decorator can only be applied to functions.")

    output = inspect.signature(fn).return_annotation
    if output is not UserInfo:
        raise InvalidUserInfoOutputType(f"Function <{fn.__name__}> decorated with @userinfo must output a UserInfo object")

    fn.__userinfo__ = True

    return wraps(fn)(fn)
