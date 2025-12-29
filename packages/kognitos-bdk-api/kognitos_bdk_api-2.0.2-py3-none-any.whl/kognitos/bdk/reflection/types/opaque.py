from typing import List, Optional, Set, Type

from ...api.noun_phrase import NounPhrase
from .base import ConceptType


class ConceptOpaqueType(ConceptType):
    is_a: Set[NounPhrase]
    description: Optional[str]
    concrete: Type

    def __init__(self, is_a: Set[NounPhrase], description: Optional[str], concrete: Type):
        if not isinstance(is_a, set) or not all(isinstance(item, NounPhrase) for item in is_a):
            raise TypeError("is_a must be a set of NounPhrase instances")

        self.is_a = is_a
        self.description = description
        self.concrete = concrete

    def simplify(self) -> ConceptType:
        return self

    def children(self) -> List[ConceptType]:
        return []

    def __repr__(self) -> str:
        return f"Opaque[{','.join(is_a.to_string() for is_a in list(self.is_a))}]"

    def __str__(self) -> str:
        if len(self.is_a) == 1:
            return next(iter(self.is_a)).to_string()

        return " or ".join([f"`{is_a.__str__()}`" for is_a in list(self.is_a)])

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        return self

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptOpaqueType):
            return self.is_a == other.is_a
        return False

    def __hash__(self) -> int:
        combined_hash = hash("Opaque")
        for inner in self.is_a:
            combined_hash ^= hash(inner)
        return combined_hash
