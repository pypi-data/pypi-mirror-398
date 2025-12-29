from typing import List

from .base import ConceptType


def contains_optionals(concept_type) -> bool:
    from .sensitive import \
        ConceptSensitiveType  # pylint: disable=cyclic-import
    from .union import ConceptUnionType  # pylint: disable=cyclic-import

    if isinstance(concept_type, ConceptOptionalType):
        return True

    if isinstance(concept_type, ConceptSensitiveType):
        return contains_optionals(concept_type.type)

    if isinstance(concept_type, ConceptUnionType):
        return any(contains_optionals(inner) for inner in concept_type.inners)

    return False


class ConceptOptionalType(ConceptType):
    def __init__(self, inner: ConceptType):
        self.type = inner

    def simplify(self) -> "ConceptOptionalType":
        simplified_inner = self.type.simplify()
        if isinstance(simplified_inner, ConceptOptionalType):
            return simplified_inner
        return ConceptOptionalType(simplified_inner)

    def children(self) -> List[ConceptType]:
        return [self.type]

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        return ConceptOptionalType(self.type.replace(old, new))

    def flatten(self, **kwargs) -> List[ConceptType]:
        return self.type.flatten(**kwargs)

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptOptionalType):
            return self.type == other.type
        return False

    def __repr__(self) -> str:
        return f"Optional[{self.type.name}]"

    def __str__(self) -> str:
        return f"{self.type.name}?"

    def __hash__(self) -> int:
        combined_hash = hash("Optional")
        combined_hash ^= hash(self.type)
        return combined_hash
