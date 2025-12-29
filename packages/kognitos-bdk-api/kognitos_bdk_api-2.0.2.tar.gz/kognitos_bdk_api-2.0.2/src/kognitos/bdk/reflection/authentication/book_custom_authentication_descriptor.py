from dataclasses import dataclass
from typing import List, Optional

from ...api.noun_phrase import NounPhrase
from .book_authentication_descriptor import BookAuthenticationDescriptor
from .credential_descriptor import CredentialDescriptor


@dataclass
class BookCustomAuthenticationDescriptor(BookAuthenticationDescriptor):
    noun_phrase: Optional[NounPhrase]
    credentials: List[CredentialDescriptor]
