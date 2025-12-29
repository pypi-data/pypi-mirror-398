from typing import List, Optional, Type

from ...api import NounPhrase
from ...reflection import BookDescriptor
from ..book_config_descriptor import BookConfigDescriptor


class BookFactory:
    @classmethod
    def create(
        cls,
        t: Type,
        identifier: Optional[str] = None,
        name: Optional[str] = None,
        noun_phrase_str: Optional[str] = None,
        author: Optional[str] = None,
        short_description: Optional[str] = None,
        long_description: Optional[str] = None,
        icon: Optional[bytes] = None,
        icon_path: Optional[str] = None,
        configuration: Optional[List[BookConfigDescriptor]] = None,
        tags: Optional[List[str]] = None,
    ) -> BookDescriptor:
        if name is None:
            name = t.__name__

        if identifier is None:
            identifier = name.strip().replace(" ", "").lower()

        if noun_phrase_str is None:
            noun_phrase = NounPhrase.from_pascal_case(name)
        else:
            noun_phrase = NounPhrase.from_head(noun_phrase_str)

        return BookDescriptor(
            cls=t,
            identifier=identifier,
            name=name,
            noun_phrase=noun_phrase,
            author=author,
            short_description=short_description,
            long_description=long_description,
            icon=icon,
            icon_path=icon_path,
            configuration=configuration,
            tags=tags,
        )
