from typing import List, Optional

from kognitos.bdk.klang import KlangParser

from ...api import NounPhrase
from ...reflection import (BookCustomAuthenticationDescriptor,
                           CredentialDescriptor)


class BookCustomAuthenticationFactory:
    @classmethod
    def create(
        cls, id: str, noun_phrase_str: Optional[str], credentials: List[CredentialDescriptor], description: Optional[str], name: Optional[str]  # pylint: disable=redefined-builtin
    ) -> BookCustomAuthenticationDescriptor:
        if noun_phrase_str is None:
            noun_phrase = NounPhrase.from_snake_case(id)
        else:
            noun_phrases, _ = KlangParser.parse_noun_phrases(noun_phrase_str)
            noun_phrase = NounPhrase.from_tuple(noun_phrases[0])

        connect_name = noun_phrase.to_string() if name is None else name

        return BookCustomAuthenticationDescriptor(id=id, noun_phrase=noun_phrase, credentials=credentials, description=description, name=connect_name)
