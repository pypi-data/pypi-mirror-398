from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..api.noun_phrase import NounPhrase
from .types import ConceptOptionalType, ConceptType


@dataclass
class ConceptDescriptor:
    noun_phrases: List[NounPhrase]
    _type: ConceptType = field(init=False)
    default_value: Any
    description: Optional[str] = None

    def __init__(self, noun_phrases: List[NounPhrase], type: ConceptType, default_value: Any, description: Optional[str] = None):  # pylint: disable=redefined-builtin
        self.noun_phrases = noun_phrases
        self._type = type
        self.default_value = default_value
        self.description = description

    @property
    def is_optional(self) -> bool:
        return isinstance(self.type, ConceptOptionalType)

    @property
    def type(self) -> ConceptType:
        return ConceptOptionalType(inner=self._type) if not isinstance(self._type, ConceptOptionalType) and self.default_value is not None else self._type
