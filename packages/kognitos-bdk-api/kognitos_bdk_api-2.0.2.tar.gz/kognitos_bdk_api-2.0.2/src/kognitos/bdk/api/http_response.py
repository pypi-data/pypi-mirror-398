from dataclasses import dataclass
from typing import Dict


@dataclass
class HTTPResponse:
    """
    Standard HTTP response structure for trigger resolvers.

    Attributes:
        status: HTTP status code (e.g., 200, 404)
        headers: HTTP response headers
        body: Response body content
    """

    status: int
    headers: Dict[str, str]
    body: bytes
