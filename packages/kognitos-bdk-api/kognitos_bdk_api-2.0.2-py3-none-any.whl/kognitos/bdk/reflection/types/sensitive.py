from typing import List

from .base import ConceptType
from .optional import ConceptOptionalType, contains_optionals


class ConceptSensitiveType(ConceptType):
    def __init__(self, inner: ConceptType):
        self.type = inner

    def simplify(self) -> ConceptType:
        flattened_inners = self.flatten()
        simplified = flattened_inners.pop()  # NOTE: flattening a sensitive should always yield a list of one element
        if contains_optionals(self):
            return ConceptOptionalType(simplified)
        return simplified

    def children(self) -> List[ConceptType]:
        return [self.type]

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        return ConceptSensitiveType(self.type.replace(old, new))

    def flatten(self, **kwargs) -> List[ConceptType]:
        from .union import ConceptUnionType  # pylint: disable=cyclic-import

        strip_sensitives = kwargs.get("strip_sensitive", False)

        kwargs.update(strip_sensitive=True)
        flattened_types = self.type.flatten(**kwargs)

        if strip_sensitives is True:
            return flattened_types

        if len(flattened_types) == 1:
            return [ConceptSensitiveType(flattened_types.pop())]

        return [ConceptSensitiveType(ConceptUnionType(flattened_types))]

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptSensitiveType):
            return self.type == other.type
        return False

    def __repr__(self) -> str:
        return f"Sensitive[{self.type.name}]"

    def __str__(self) -> str:
        return f"Sensitive[{self.type.name}]"

    def __hash__(self) -> int:
        combined_hash = hash("Sensitive")
        combined_hash ^= hash(self.type)
        return combined_hash
