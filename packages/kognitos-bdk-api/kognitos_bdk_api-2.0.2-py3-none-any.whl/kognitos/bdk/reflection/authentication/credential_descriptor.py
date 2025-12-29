from dataclasses import dataclass
from typing import Optional

from ..types import CredentialType


@dataclass
class CredentialDescriptor:
    id: str
    type: CredentialType
    label: Optional[str]
    description: Optional[str]
