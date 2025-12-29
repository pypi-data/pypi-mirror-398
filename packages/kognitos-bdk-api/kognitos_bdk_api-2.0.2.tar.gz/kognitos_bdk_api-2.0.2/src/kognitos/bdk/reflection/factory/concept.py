from inspect import Parameter
from typing import Any, List, Optional

from ...api.noun_phrase import NounPhrase
from ...reflection import ConceptDescriptor
from .types import ConceptTypeFactory


class ConceptFactory:
    @classmethod
    def from_parameter(cls, parameter: Parameter) -> "ConceptDescriptor":
        noun_phrase = NounPhrase.from_word_list(parameter.name.split("_"))

        default_value = parameter.default if parameter.default is not Parameter.empty else None

        return ConceptFactory.from_noun_phrase_and_annotation(noun_phrase, parameter.annotation, default_value=default_value)

    @classmethod
    def from_noun_phrase_and_annotation(
        cls, noun_phrase: NounPhrase, annotation: "type", description: Optional[str] = None, default_value: Optional[Any] = None
    ) -> "ConceptDescriptor":
        return ConceptFactory.from_noun_phrases_and_annotation([noun_phrase], annotation, description, default_value=default_value)

    @classmethod
    def from_noun_phrases_and_annotation(
        cls, noun_phrases: List[NounPhrase], annotation: "type", description: Optional[str] = None, default_value: Optional[Any] = None
    ) -> "ConceptDescriptor":
        t = ConceptTypeFactory.from_type(annotation)

        return ConceptDescriptor(noun_phrases=noun_phrases, type=t, description=description, default_value=default_value)
