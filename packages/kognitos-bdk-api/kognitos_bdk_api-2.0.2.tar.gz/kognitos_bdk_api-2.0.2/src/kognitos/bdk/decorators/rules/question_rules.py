from typing import Literal, get_origin

from ...api import Question
from ...api.noun_phrase import NounPhrase, NounPhrases
from ...reflection.factory.types import ConceptTypeFactory, is_union_type
from ...reflection.types.opaque import ConceptOpaqueType


class QuestionTypingRule:
    def validate(self, annotation_type: type) -> None:
        if annotation_type is Question:
            raise ValueError("Question type-hinting must be parameterized: Question[Literal['noun phrase'], type]")


class QuestionTypeHintStructureRule(QuestionTypingRule):
    def validate(self, annotation_type: type) -> None:
        super().validate(annotation_type)
        if (
            not len(annotation_type.__args__) == 2
            or not get_origin(annotation_type.__args__[0]) is Literal
            or not len(annotation_type.__args__[0].__args__) == 1
            or not isinstance(annotation_type.__args__[0].__args__[0], str)
            or not (isinstance(annotation_type.__args__[1], type) or is_union_type(annotation_type.__args__[1]))
        ):
            raise ValueError("Question type-hinting must have a string literal as the first argument, and a type as the second argument.")


class QuestionTypeHintNounPhraseRule(QuestionTypingRule):
    def validate(self, annotation_type: type) -> None:
        super().validate(annotation_type)
        noun_phrases = NounPhrases([NounPhrase.from_str(noun_phrase) for noun_phrase in annotation_type.__args__[0].__args__[0].split("'s ")])
        if not noun_phrases.noun_phrases:
            raise ValueError("Question type-hinting must have a valid noun phrases representation in the string literal.")


class QuestionTypeHintConceptTypeRule(QuestionTypingRule):
    def validate(self, annotation_type: type) -> None:
        super().validate(annotation_type)
        question_concept_type = ConceptTypeFactory.from_type(annotation_type.__args__[1])
        if question_concept_type == ConceptOpaqueType({NounPhrase("thing")}, "", object):
            raise ValueError("Question type-hinting must declare a supported concept type.")
