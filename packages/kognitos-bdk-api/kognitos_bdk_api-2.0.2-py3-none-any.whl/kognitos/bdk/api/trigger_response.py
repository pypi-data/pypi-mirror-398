from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from .http_response import HTTPResponse

T = TypeVar("T")


@dataclass
class TriggerResponse(Generic[T]):
    """
    Response container for trigger resolver responses.

    TriggerResponse[T] contains an HTTPResponse and an event of type T,
    where T is a dataclass decorated with @trigger_event.

    Attributes:
        trigger_instance_reference: The reference to the trigger instance. It should be the same value that gets returned on the
            trigger configuration call.
        http_response: The HTTP response to return to the caller
        event: The trigger event data

    Example:
        @trigger_event
        @dataclass
        class GitHubEvent:
            event_type: str
            repository: str
            action: str

        def handle_webhook(self, data: dict) -> TriggerResponse[GitHubEvent]:
            response = HTTPResponse(
                status=200,
                headers={"Content-Type": "application/json"},
                body='{"status": "ok"}'
            )
            event = GitHubEvent(...)
            return TriggerResponse(trigger_instance_reference=None, http_response=response, event=event)
    """

    trigger_instance_reference: Optional[str]
    http_response: HTTPResponse
    event: Optional[T]
