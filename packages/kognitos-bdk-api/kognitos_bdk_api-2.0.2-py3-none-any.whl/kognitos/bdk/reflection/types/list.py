from typing import List

from .base import ConceptType
from .self import ConceptSelfType


class ConceptListType(ConceptType):
    def __init__(self, inner: ConceptType):
        self.type = inner

    def simplify(self) -> ConceptType:
        simplify_inner = self.type.simplify()

        if isinstance(simplify_inner, ConceptListType) and isinstance(simplify_inner.type, ConceptSelfType):
            return simplify_inner

        return ConceptListType(simplify_inner)

    def children(self) -> List[ConceptType]:
        return [self.type]

    def __repr__(self) -> str:
        return f"List[{self.type.__repr__()}]"

    def __str__(self) -> str:
        return f"list of {self.type.name}"

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        return ConceptListType(self.type.replace(old, new))

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptListType):
            return self.type == other.type
        return False

    def __hash__(self) -> int:
        combined_hash = hash("List")
        combined_hash ^= hash(self.type)
        return combined_hash
