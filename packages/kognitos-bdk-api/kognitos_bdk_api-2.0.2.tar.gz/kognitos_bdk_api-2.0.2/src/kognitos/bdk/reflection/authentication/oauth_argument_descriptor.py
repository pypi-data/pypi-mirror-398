from dataclasses import dataclass
from typing import Optional


@dataclass
class OauthArgumentDescriptor:
    id: str
    name: str
    description: Optional[str]
