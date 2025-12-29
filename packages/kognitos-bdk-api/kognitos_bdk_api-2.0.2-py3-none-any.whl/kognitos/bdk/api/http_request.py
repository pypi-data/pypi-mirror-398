import json
from dataclasses import dataclass
from typing import Dict


@dataclass
class HTTPRequest:
    """
    Standard HTTP request structure for trigger resolvers.
    """

    method: str
    url: str
    headers: Dict[str, str]
    body: bytes

    def text(self, encoding: str = "utf-8") -> str:
        return self.body.decode(encoding)

    def is_json(self) -> bool:
        return "application/json" in self.headers.get("content-type", "")

    def json(self) -> dict:
        if not self.is_json():
            raise ValueError("Request is not JSON")
        return json.loads(self.body)
