from dataclasses import dataclass
from typing import Optional


@dataclass
class BookAuthenticationDescriptor:
    id: str
    description: Optional[str]
    name: str
