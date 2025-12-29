from typing import Any, List, Optional, Set, Type

from ...api.noun_phrase import NounPhrase
from .base import ConceptType
from .optional import ConceptOptionalType


class ConceptDictionaryTypeField:
    name: str
    description: Optional[str]
    _t: ConceptType
    default_value: Any
    has_default_value: bool
    init: bool

    def __init__(
        self, name: str, description: Optional[str] = None, t: Optional[ConceptType] = None, default_value: Any = None, has_default_value: bool = False, init: bool = True
    ):
        self.name = name
        self.description = description
        self._t = t
        self.default_value = default_value
        self.has_default_value = has_default_value
        self.init = init

    def __repr__(self) -> str:
        return f"{self.name}: {self.t!r}"

    def __str__(self) -> str:
        return f"{self.name}: {self.t}"

    def __eq__(self, other) -> bool:
        if self.name != other.name:
            return False
        if self.t != other.t:
            return False
        if self.description != other.description:
            return False
        return True

    def __hash__(self) -> int:
        return hash((self.name, self.description, self.t))

    @property
    def t(self) -> ConceptType:
        return ConceptOptionalType(inner=self._t) if not isinstance(self._t, ConceptOptionalType) and self.default_value is not None else self._t


class ConceptDictionaryType(ConceptType):
    is_a: Set[NounPhrase]
    description: Optional[str]
    concrete: Optional[Type]
    unset: Optional[Any]

    def __init__(self, is_a: Set[NounPhrase], concrete: Optional[Type], description: Optional[str], fields: List[ConceptDictionaryTypeField], unset: Optional[Any] = None):
        self.is_a = is_a
        self.description = description
        self.fields = fields
        self.concrete = concrete
        self.unset = unset

    def simplify(self) -> ConceptType:
        simplified_fields = [
            ConceptDictionaryTypeField(field.name, field.description, field.t.simplify(), field.default_value, field.has_default_value, field.init) for field in self.fields
        ]

        return ConceptDictionaryType(self.is_a, self.concrete, self.description, simplified_fields, self.unset)

    def children(self) -> List[ConceptType]:
        return [field.t for field in self.fields]

    def __repr__(self) -> str:
        return f"Dictionary[({','.join([is_a.to_string() for is_a in list(self.is_a)])}), {', '.join([field.__repr__() for field in self.fields])}]"

    def __str__(self) -> str:
        if len(self.is_a) == 1:
            return next(iter(self.is_a)).to_string()

        return " or ".join([f"`{is_a.__str__()}`" for is_a in list(self.is_a)])

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new

        new_fields = [
            ConceptDictionaryTypeField(field.name, field.description, new) if field.t == old else ConceptDictionaryTypeField(field.name, field.description, old)
            for field in self.fields
        ]

        return ConceptDictionaryType(self.is_a, self.concrete, self.description, new_fields, self.unset)

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptDictionaryType):
            return self.concrete == other.concrete and self.is_a == other.is_a and self.fields == other.fields and self.unset == other.unset
        return False

    def __hash__(self) -> int:
        combined_hash = hash("Dictionary")
        for field in self.fields:
            combined_hash ^= hash(field)
        return combined_hash
