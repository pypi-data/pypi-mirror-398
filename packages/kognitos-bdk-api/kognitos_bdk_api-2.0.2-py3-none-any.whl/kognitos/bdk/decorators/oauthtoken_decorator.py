import inspect
from typing import get_origin

from kognitos.bdk.typing import Sensitive


def oauthtoken(fn):
    if not inspect.isfunction(fn):
        raise TypeError("The oauthtoken decorator can only be applied to functions.")

    sig = inspect.signature(fn)
    parameters = sig.parameters
    if "access_token" not in parameters:
        raise ValueError("The method decorated with @oauthtoken must have a parameter named 'access_token'")
    access_token_param = parameters["access_token"]

    if get_origin(access_token_param.annotation) is Sensitive:
        fn.__access_token_is_sensitive__ = True
    else:
        fn.__access_token_is_sensitive__ = False
    fn.__oauthtoken__ = True

    return fn
