import functools
import inspect

from ..docstring import DocstringParser
from ..reflection import CredentialDescriptor
from ..reflection.factory import BookCustomAuthenticationFactory
from ..reflection.types import CredentialScalarType
from ..typing import Sensitive


def connect(noun_phrase: str, name: str):
    """
    Function decorator for registering a custom connection method in a book.

    Args:
        noun_phrase (str): The noun phrase that identifies the connection method (e.g., "api key method").
        name (str): A display name for the connection method (e.g., "Api Key").
    """

    def decorator(fn):
        if not inspect.isfunction(fn):
            raise TypeError("The connect decorator can only be applied to functions.")

        short_description = None
        signature = inspect.signature(fn)
        credentials = []

        if not fn.__doc__:
            raise ValueError("missing docstring")

        parsed_docstring = DocstringParser.parse(fn.__doc__)

        if parsed_docstring.short_description:
            short_description = parsed_docstring.short_description.strip()

        for param_name, parameter in signature.parameters.items():
            if param_name == "self":
                continue

            # Handle special 'verify' parameter
            if param_name == "verify":
                # Validate that verify is a boolean
                if parameter.annotation is not bool:
                    raise TypeError("parameter 'verify' must be a boolean and must be annotated as bool")
                # Skip adding verify as a credential
                continue

            if parameter.annotation is str:
                credential_type = CredentialScalarType.TEXT
            elif parameter.annotation is Sensitive[str]:
                credential_type = CredentialScalarType.SENSITIVE
            else:
                # NOTE: We don't support other types for now
                raise TypeError(f"parameter '{param_name}' has an unsupported type")

            if parsed_docstring:
                param_docstring = parsed_docstring.param_by_name(param_name)
            else:
                param_docstring = None

            credential = CredentialDescriptor(
                id=param_name,
                label=param_docstring.label if param_docstring is not None else None,
                type=credential_type,
                description=(param_docstring.description if param_docstring is not None else None),
            )

            credentials.append(credential)

        if not hasattr(fn, "__connect__"):
            fn.__connect__ = BookCustomAuthenticationFactory.create(id=fn.__name__, noun_phrase_str=noun_phrase, credentials=credentials, description=short_description, name=name)

        if not hasattr(fn, "__signature__"):
            fn.__signature__ = signature

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return decorator
