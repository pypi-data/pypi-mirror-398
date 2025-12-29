from dataclasses import is_dataclass
from typing import Type, TypeVar, cast

T = TypeVar("T", bound=Type)


def trigger_event(cls: T) -> T:
    """
    Decorator for dataclasses that represent trigger event structures.

    This decorator marks a dataclass as a trigger event type, which can be used
    as the second type parameter in TriggerResponse[HTTPResponse, T].

    The fields of the dataclass will be extracted and used to populate the
    'event' field in the BookTriggerDescriptor.

    Example:
        @trigger_event
        @dataclass
        class GitHubWebhookEvent:
            event_type: str
            repository: str
            action: str
            sender: str
            timestamp: int

        @trigger(name="github_webhook", resolver="handle_github", is_manual=False)
        def setup_webhook(self, endpoint: str) -> Optional[str]:
            '''Setup webhook'''
            pass

        def handle_github(self, data: dict) -> TriggerResponse[GitHubWebhookEvent]:
            '''Handle GitHub event'''
            pass

    Args:
        cls: The dataclass to decorate

    Returns:
        The decorated class with __trigger_event__ marker

    Raises:
        TypeError: If the decorator is not applied to a dataclass
    """
    if not is_dataclass(cls):
        raise TypeError(
            f"The @trigger_event decorator can only be applied to dataclasses. " f"'{cls.__name__}' is not a dataclass. " f"Make sure to apply @dataclass before @trigger_event."
        )

    # Mark this class as a trigger event
    cls.__trigger_event__ = True

    return cast(T, cls)
