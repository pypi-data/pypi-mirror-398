# pylint: disable=invalid-name
from __future__ import annotations

from abc import ABCMeta
from typing import List, Optional, Type

from .base import ConceptType


class ConceptScalarTypeMeta(ABCMeta):
    @property
    def CONCEPTUAL(cls) -> ConceptScalarType:
        return ConceptScalarType("Conceptual")

    @property
    def TEXT(cls) -> ConceptScalarType:
        return ConceptScalarType("Text")

    @property
    def NUMBER(cls) -> ConceptScalarType:
        return ConceptScalarType("Number")

    @property
    def BOOLEAN(cls) -> ConceptScalarType:
        return ConceptScalarType("Boolean")

    @property
    def DATETIME(cls) -> ConceptScalarType:
        return ConceptScalarType("Datetime")

    @property
    def DATE(cls) -> ConceptScalarType:
        return ConceptScalarType("Date")

    @property
    def TIME(cls) -> ConceptScalarType:
        return ConceptScalarType("Time")

    @property
    def FILE(cls) -> ConceptScalarType:
        return ConceptScalarType("File")

    @property
    def UUID(cls) -> ConceptScalarType:
        return ConceptScalarType("UUID")


class ConceptScalarType(ConceptType, metaclass=ConceptScalarTypeMeta):
    concrete: Optional[Type]

    def __init__(self, name: str, concrete: Optional[Type] = None):
        self._name = name
        self.concrete = concrete

    def simplify(self) -> ConceptType:
        return self

    def children(self) -> List[ConceptType]:
        return []

    def __repr__(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name.lower()

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new
        return self

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptScalarType):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)
