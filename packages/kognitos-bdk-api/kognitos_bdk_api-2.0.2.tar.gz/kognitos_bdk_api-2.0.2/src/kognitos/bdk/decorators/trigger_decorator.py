import inspect
from typing import Union, get_args, get_origin

from ..api.filter import FilterExpression
from ..docstring import DocstringParser
from ..reflection.factory import BookTriggerFactory


def trigger(name: str, resolver: str, is_manual: bool = False, is_shared_endpoint: bool = False):
    """
    Function decorator for registering a trigger in a book.

    The decorated function must have the following signature:
    - Return type: Optional[str] (required)
    - endpoint: str (required)
    - filter_expression: Optional[FilterExpression] (optional)
    - Any other parameters are considered part of the trigger configuration

    Args:
        name (str): The name of the trigger.
        resolver (str): The resolver function name for the trigger.
        is_manual (bool): Whether the trigger setup is manual. Default is False.
        is_shared_endpoint (bool): Whether all configured trigger instances share the same endpoint.
            When True, all trigger instances use a single shared endpoint.
            When False, each trigger instance gets its own unique endpoint. Default is False.
    """

    def decorator(fn):
        if not inspect.isfunction(fn):
            raise TypeError("The trigger decorator can only be applied to functions.")

        # Validate function signature
        sig = inspect.signature(fn, eval_str=True)
        params = sig.parameters

        # Validate return type is Optional[str]
        if sig.return_annotation == inspect.Signature.empty:
            raise ValueError(f"Function '{fn.__name__}' decorated with @trigger must have a return type annotation of 'Optional[str]'. " f"Add: -> Optional[str]")

        return_origin = get_origin(sig.return_annotation)
        return_args = get_args(sig.return_annotation)

        # Check if it's Union (Optional is Union[str, None])
        is_union = return_origin is Union
        has_str = str in return_args if return_args else False
        has_none = type(None) in return_args if return_args else False

        if not (is_union and has_str and has_none):
            raise ValueError(f"Function '{fn.__name__}' decorated with @trigger must have a return type of 'Optional[str]', " f"got '{sig.return_annotation}' instead.")

        # Check for required 'endpoint' parameter
        if "endpoint" not in params:
            raise ValueError(f"Function '{fn.__name__}' decorated with @trigger must have an 'endpoint: str' parameter.")

        # Validate 'endpoint' is annotated as str
        endpoint_param = params["endpoint"]
        if endpoint_param.annotation not in (str, inspect.Parameter.empty):
            raise ValueError(f"Function '{fn.__name__}' parameter 'endpoint' must be annotated as 'str', " f"got '{endpoint_param.annotation}'.")

        # Validate 'filter_expression' if present
        if "filter_expression" in params:
            filter_param = params["filter_expression"]
            # Check if it's Optional[FilterExpression]
            if filter_param.annotation != inspect.Parameter.empty:
                # Get the origin and args for Optional type checking
                origin = get_origin(filter_param.annotation)
                args = get_args(filter_param.annotation)

                # Check if it's Union (Optional is Union[X, None])
                is_union = origin is Union
                has_filter_expression = FilterExpression in args if args else False
                has_none = type(None) in args if args else False

                if not (is_union and has_filter_expression and has_none):
                    raise ValueError(
                        f"Function '{fn.__name__}' parameter 'filter_expression' must be annotated as " f"'Optional[FilterExpression]', got '{filter_param.annotation}'."
                    )

        # Identify configuration parameters (all except 'endpoint', 'filter_expression', and 'self')
        configuration_params = [param_name for param_name in params.keys() if param_name not in ("endpoint", "filter_expression", "self")]

        # Parse documentation
        if not fn.__doc__:
            raise ValueError(f"Function '{fn.__name__}' decorated with @trigger is missing docstring")

        docstring = DocstringParser.parse(fn.__doc__)

        # Create the BookTriggerDescriptor
        book_trigger = BookTriggerFactory.create(
            identifier=fn.__name__,
            name=name,
            is_manual=is_manual,
            is_shared_endpoint=is_shared_endpoint,
            python_signature=sig,
            docstring=docstring,
            configuration_params=configuration_params,
            resolver_function_name=resolver,
        )

        # Attach metadata to the function
        fn.__trigger__ = book_trigger
        fn.__trigger_resolver_function_name__ = resolver

        return fn

    return decorator
