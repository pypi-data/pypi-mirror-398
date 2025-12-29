from dataclasses import dataclass

from ..api.noun_phrase import NounPhrases
from .types import ConceptType


@dataclass
class QuestionDescriptor:
    noun_phrases: NounPhrases
    type: ConceptType

    def __hash__(self) -> int:
        return hash(self.noun_phrases)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, QuestionDescriptor) and hash(self) == hash(other)
