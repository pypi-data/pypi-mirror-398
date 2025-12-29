from typing import List

from .base import ConceptType


class ConceptSelfType(ConceptType):
    def simplify(self) -> ConceptType:
        return self

    def children(self) -> List[ConceptType]:
        return []

    def __repr__(self) -> str:
        return "Self"

    def __str__(self) -> str:
        return "self"

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        return self

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptSelfType):
            return True
        return False

    def __hash__(self) -> int:
        return hash("Self")
