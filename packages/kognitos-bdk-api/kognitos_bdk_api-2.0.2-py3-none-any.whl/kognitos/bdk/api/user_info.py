from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class UserInfo:
    email: Optional[str] = None
    username: Optional[str] = None
    other_attributes: Optional[Dict[str, str]] = None
