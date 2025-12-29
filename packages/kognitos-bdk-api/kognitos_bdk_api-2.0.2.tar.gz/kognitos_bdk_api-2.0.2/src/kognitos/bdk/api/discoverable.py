from dataclasses import dataclass
from typing import Optional


@dataclass
class Discoverable:
    """
    Represents a discoverable object.
    This is to be returned by the @discoverables method of a book.

    The idea is to provide the user with knowledge about the different discoverable
    entities in the system for them to properly call the discover mechanism.

    Args:
        name: The name of the discoverable.
        description: The description of the discoverable.
    """

    name: str
    description: Optional[str] = None
