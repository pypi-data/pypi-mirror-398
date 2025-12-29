from typing import List, Optional, Set, Type

from kognitos.bdk.api.noun_phrase import NounPhrase

from .base import ConceptType


class ConceptEnumTypeMember:
    name: str
    description: Optional[str]
    noun_phrase: Optional[NounPhrase]

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptEnumTypeMember):
            return self.name == other.name and self.description == other.description and self.noun_phrase == other.noun_phrase

        return False

    def __init__(self, name: str, description: Optional[str] = None, noun_phrase: Optional[NounPhrase] = None):
        self.name = name
        self.description = description
        self.noun_phrase = noun_phrase


class ConceptEnumType(ConceptType):
    is_a: Set[NounPhrase]
    members: List[ConceptEnumTypeMember]
    description: Optional[str]
    concrete: Optional[Type]

    def __init__(self, is_a: Set[NounPhrase], members: List[ConceptEnumTypeMember], description: Optional[str] = None, concrete: Optional[Type] = None):
        self.is_a = is_a
        self.members = members
        self.description = description
        self.concrete = concrete

    def simplify(self) -> ConceptType:
        return self

    def children(self) -> List[ConceptType]:
        return []

    def __repr__(self) -> str:
        return f"Enum[{', '.join(self.keys)}]"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptEnumType):
            return self.keys == other.keys and self.is_a == other.is_a
        return False

    def __hash__(self) -> int:
        return hash("".join(self.keys))

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        return self

    @property
    def keys(self) -> List[str]:
        return [m.name for m in self.members]
