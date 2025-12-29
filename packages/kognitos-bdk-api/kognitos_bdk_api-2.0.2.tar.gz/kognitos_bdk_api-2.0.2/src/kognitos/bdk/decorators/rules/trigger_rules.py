import inspect
from dataclasses import fields, is_dataclass
from typing import Any, Callable, Dict, get_args, get_origin, get_type_hints

from ...api.noun_phrase import NounPhrase
from ...api.trigger_response import TriggerResponse
from ...reflection import ConceptDescriptor
from ...reflection.factory.types import ConceptTypeFactory


class TriggerRule:
    """Base class for trigger validation rules."""

    def validate(self, _book_class: type, trigger_func: Callable[..., Any]) -> None:
        """
        Validate the trigger function and its resolver.

        Args:
            book_class: The book class containing the trigger
            trigger_func: The function decorated with @trigger

        Raises:
            ValueError: If validation fails
            TypeError: If the wrong type is provided
        """
        if not inspect.isfunction(trigger_func):
            raise TypeError("The trigger rule can only be validated against functions.")

        if not hasattr(trigger_func, "__trigger_resolver_function_name__"):
            raise ValueError(f"Missing trigger resolver for function '{trigger_func.__name__}'. " f"Did you forget to apply the @trigger decorator?")


class TriggerConfigurationDescriptionRule(TriggerRule):
    """Rule to validate that all trigger configuration parameters have descriptions."""

    def validate(self, book_class: type, trigger_func: Callable[..., Any]) -> None:  # type: ignore[override]
        super().validate(book_class, trigger_func)

        trigger = getattr(trigger_func, "__trigger__", None)
        if not trigger:
            raise ValueError(f"Function '{trigger_func.__name__}' is missing __trigger__ attribute. " f"Did you forget to apply the @trigger decorator?")

        # Check that all configuration parameters have descriptions
        missing_descriptions = []
        for param_name, concept in trigger.configuration.items():
            if not concept.description:
                missing_descriptions.append(param_name)

        if missing_descriptions:
            raise ValueError(
                f"Trigger '{trigger.name}' configuration parameters missing descriptions: " f"{', '.join(missing_descriptions)}. Add descriptions in the setup function docstring."
            )


class TriggerResolverExistsRule(TriggerRule):
    """Rule to validate that the trigger resolver function exists in the book class."""

    def validate(self, book_class: type, trigger_func: Callable[..., Any]) -> None:  # type: ignore[override]
        super().validate(book_class, trigger_func)

        resolver_name = trigger_func.__trigger_resolver_function_name__  # type: ignore[attr-defined]

        if not hasattr(book_class, resolver_name):
            raise ValueError(f"Trigger resolver '{resolver_name}' for function '{trigger_func.__name__}' " f"not found in book class.")


class TriggerResolverInputsRule(TriggerRule):
    """Rule to validate that the trigger resolver has the correct input signature."""

    def validate(self, book_class: type, trigger_func: Callable[..., Any]) -> None:  # type: ignore[override]
        super().validate(book_class, trigger_func)

        resolver_name = trigger_func.__trigger_resolver_function_name__  # type: ignore[attr-defined]
        resolver_fn = getattr(book_class, resolver_name)

        # Get resolver parameters (excluding 'self')
        resolver_sig = inspect.signature(resolver_fn, eval_str=True)
        resolver_params = {name: param for name, param in resolver_sig.parameters.items() if name != "self"}

        # Validate exactly one parameter
        if len(resolver_params) != 1:
            raise ValueError(
                f"Trigger resolver '{resolver_name}' for function '{trigger_func.__name__}' "
                f"must have exactly one parameter (besides 'self'). "
                f"Got {len(resolver_params)} parameters: {list(resolver_params.keys())}"
            )

        # Get the single parameter
        param_name, param = next(iter(resolver_params.items()))

        # Validate parameter name is 'request'
        if param_name != "request":
            raise ValueError(f"Trigger resolver '{resolver_name}' parameter must be named 'request', " f"got '{param_name}' instead.")

        # Validate parameter type is HTTPRequest
        from ...api.http_request import HTTPRequest

        if param.annotation != inspect.Parameter.empty:
            # If type hint is present, validate it's HTTPRequest
            if param.annotation != HTTPRequest:
                raise ValueError(f"Trigger resolver '{resolver_name}' parameter 'request' must be typed as " f"'HTTPRequest', got '{param.annotation}' instead.")
        else:
            # If no type hint, raise an error
            raise ValueError(f"Trigger resolver '{resolver_name}' parameter 'request' must be typed as " f"'HTTPRequest'. Add type annotation: request: HTTPRequest")


class TriggerEventExtractionRule(TriggerRule):
    """
    Rule to extract event information from the trigger resolver.

    This rule extracts event schema from:
    1. TriggerResponse[EventClass] return type (if @trigger_event dataclass)
    2. Resolver function parameters (fallback)
    """

    def validate(self, book_class: type, trigger_func: Callable[..., Any]) -> None:  # type: ignore[override]
        super().validate(book_class, trigger_func)

        # This rule doesn't raise errors, it just ensures the resolver is callable
        resolver_name = trigger_func.__trigger_resolver_function_name__  # type: ignore[attr-defined]
        resolver_fn = getattr(book_class, resolver_name)

        if not callable(resolver_fn):
            raise TypeError(f"Trigger resolver '{resolver_name}' must be callable.")

    @staticmethod
    def extract_event(book_class: type, trigger_func: Callable[..., Any]) -> Dict[str, ConceptDescriptor]:
        """
        Extract event schema from the trigger resolver.

        Args:
            book_class: The book class containing the trigger
            trigger_func: The function decorated with @trigger

        Returns:
            Dictionary mapping event field names to ConceptDescriptors
        """
        resolver_name = trigger_func.__trigger_resolver_function_name__  # type: ignore[attr-defined]
        resolver_fn = getattr(book_class, resolver_name)
        resolver_sig = inspect.signature(resolver_fn, eval_str=True)
        resolver_return_annotation = resolver_sig.return_annotation

        event = {}

        # Try to extract from TriggerResponse[T] return type
        if resolver_return_annotation and resolver_return_annotation != inspect.Signature.empty:
            return_origin = get_origin(resolver_return_annotation)

            # Check if it's a TriggerResponse[T]
            if return_origin is TriggerResponse:
                return_args = get_args(resolver_return_annotation)

                # TriggerResponse[T] should have 1 type arg: EventClass
                if len(return_args) == 1:
                    event_class = return_args[0]

                    # Check if the type is a dataclass with @trigger_event
                    if is_dataclass(event_class) and getattr(event_class, "__trigger_event__", False):
                        # Get resolved type hints for the dataclass to handle forward references
                        type_hints = get_type_hints(event_class)

                        # Extract fields from the dataclass
                        for field in fields(event_class):
                            # Use resolved type hint if available, otherwise use field.type
                            field_type = type_hints.get(field.name, field.type)
                            concept_type = ConceptTypeFactory.from_type(field_type)

                            event[field.name] = ConceptDescriptor(
                                noun_phrases=[NounPhrase(head=field.name, modifiers=[])],
                                type=concept_type,
                                description=None,
                                default_value=field.default if field.default is not field.default_factory else None,
                            )

                        # Return successfully extracted dataclass fields
                        return event

        # If no TriggerResponse[EventClass] found, return empty event dict
        # The resolver should use HTTPRequest parameter (validated by TriggerResolverInputsRule)
        return event
