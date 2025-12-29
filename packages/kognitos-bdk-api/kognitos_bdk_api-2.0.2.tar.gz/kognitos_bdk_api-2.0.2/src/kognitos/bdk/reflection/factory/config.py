from typing import Any, List, Optional

from ...api import NounPhrase
from ...docstring import Docstring
from ..book_config_descriptor import BookConfigDescriptor
from .concept import ConceptFactory


class BookConfigFactory:
    @classmethod
    def create(
        cls, property_name: str, noun_phrases: List[NounPhrase], return_annotation: type, docstring: Optional[Docstring], default_value: Optional[Any] = None
    ) -> BookConfigDescriptor:
        concept = ConceptFactory.from_noun_phrases_and_annotation(
            noun_phrases, return_annotation, description=docstring.short_description if docstring else None, default_value=default_value
        )

        return BookConfigDescriptor(python_property_name=property_name, concept=concept)
