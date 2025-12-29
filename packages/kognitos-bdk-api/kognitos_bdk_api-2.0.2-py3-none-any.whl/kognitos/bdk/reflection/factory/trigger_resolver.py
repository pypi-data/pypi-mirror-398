from typing import TYPE_CHECKING, Callable, Dict, List

from ...reflection import ConceptDescriptor

if TYPE_CHECKING:
    from ...decorators.rules import TriggerRule


def check_and_resolve_trigger(book_class: type, trigger_func: Callable, rules: List["TriggerRule"]) -> Dict[str, ConceptDescriptor]:
    """
    Check and resolve trigger event information.

    This function validates the trigger function and its resolver using
    the provided rules, then extracts event schema information.

    Args:
        book_class: The book class containing the trigger
        trigger_func: The function decorated with @trigger
        rules: List of validation rules to apply

    Returns:
        Dictionary mapping event field names to ConceptDescriptors

    Raises:
        ValueError: If validation fails
        TypeError: If invalid types are provided
    """
    # Apply all validation rules
    for rule in rules:
        rule.validate(book_class, trigger_func)

    # Extract event information using the TriggerEventExtractionRule
    # Find the extraction rule in the rules list
    from ...decorators.rules.trigger_rules import TriggerEventExtractionRule

    for rule in rules:
        if isinstance(rule, TriggerEventExtractionRule):
            return rule.extract_event(book_class, trigger_func)

    # If no extraction rule found, return empty dict
    return {}
