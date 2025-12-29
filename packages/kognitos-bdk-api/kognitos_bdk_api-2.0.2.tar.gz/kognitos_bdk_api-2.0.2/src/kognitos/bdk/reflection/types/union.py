from typing import List

from .any import ConceptAnyType
from .base import ConceptType
from .optional import ConceptOptionalType, contains_optionals
from .self import ConceptSelfType
from .sensitive import ConceptSensitiveType


class ConceptUnionType(ConceptType):
    def __init__(self, inners: List[ConceptType]):
        self.inners = inners

    def simplify(self) -> ConceptType:
        flattened_inners = self.flatten()
        any_type = ConceptAnyType() in flattened_inners

        if len(flattened_inners) == 1:
            simplified = flattened_inners.pop()
        elif any_type:
            simplified = ConceptAnyType()
        else:
            simplified = ConceptUnionType(flattened_inners)

        # Collapse <Self> types
        inner_unions = simplified.find(ConceptUnionType)
        if inner_unions:
            for inner_union in inner_unions:
                new_simplified_union = simplified.replace(inner_union, ConceptSelfType())
                if new_simplified_union == inner_union:
                    simplified = new_simplified_union

        if contains_optionals(self):
            return ConceptOptionalType(simplified)
        return simplified

    def flatten(self, **kwargs) -> List[ConceptType]:
        flattened_inners = []
        pack_sensitives = kwargs.get("pack_sensitives", True)

        kwargs.update(pack_sensitives=False)
        for inner in self.inners:
            for concrete_type in inner.flatten(**kwargs):
                if concrete_type not in flattened_inners:
                    flattened_inners.append(concrete_type)

        if pack_sensitives:
            flattened_and_packed = []
            sensitives_accumulator = []
            for inner in flattened_inners:
                if isinstance(inner, ConceptSensitiveType):
                    for sensitive_to_be_accumulated in inner.type.flatten(**kwargs):
                        if sensitive_to_be_accumulated not in sensitives_accumulator:
                            sensitives_accumulator.append(sensitive_to_be_accumulated)
                else:
                    flattened_and_packed.append(inner)

            if sensitives_accumulator:
                if len(sensitives_accumulator) == 1:
                    packed_sensitives = ConceptSensitiveType(sensitives_accumulator.pop())
                else:
                    packed_sensitives = ConceptSensitiveType(ConceptUnionType(sensitives_accumulator))
                flattened_and_packed = [packed_sensitives] + flattened_and_packed

            flattened_inners = flattened_and_packed

        return flattened_inners  # type: ignore

    def __repr__(self) -> str:
        return f"Union[{','.join([inner.__repr__() for inner in self.inners])}]"

    def __str__(self) -> str:
        return " or ".join([f"`{inner.__str__()}`" for inner in list(self.inners)])

    def children(self) -> List[ConceptType]:
        return self.inners

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        replaced_inners = [inner.replace(old, new) for inner in self.inners]
        return ConceptUnionType(replaced_inners)

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptUnionType):
            return set(self.inners) == set(other.inners)
        return False

    def __hash__(self) -> int:
        combined_hash = hash("Union")
        for inner in self.inners:
            combined_hash ^= hash(inner)
        return combined_hash
