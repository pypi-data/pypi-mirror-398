from typing import List

from .base import ConceptType


class ConceptAnyType(ConceptType):
    def simplify(self) -> ConceptType:
        return self

    def children(self) -> List[ConceptType]:
        return []

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        return self

    def __repr__(self):
        return "Any"

    def __str__(self):
        return "any"

    def __eq__(self, other):
        if isinstance(other, ConceptAnyType):
            return True
        return False

    def __hash__(self):
        return hash("Any")
