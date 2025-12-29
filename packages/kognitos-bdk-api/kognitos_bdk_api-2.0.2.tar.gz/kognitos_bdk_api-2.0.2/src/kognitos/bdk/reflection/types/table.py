from typing import List, Optional, Type

from .base import ConceptType


class ConceptTableTypeColumn:
    name: str
    description: Optional[str]
    t: ConceptType

    def __init__(self, name: str, description: Optional[str] = None, t: Optional[ConceptType] = None):
        self.name = name
        self.description = description
        self.t = t

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


class ConceptTableType(ConceptType):
    description: Optional[str]
    columns: List[ConceptTableTypeColumn]
    concrete: Type

    def __init__(self, description: Optional[str], columns: List[ConceptTableTypeColumn], concrete: Type):
        self.description = description
        self.columns = columns
        self.concrete = concrete

    def simplify(self) -> ConceptType:
        simplified_columns = [ConceptTableTypeColumn(field.name, field.description, field.t.simplify()) for field in self.columns]

        return ConceptTableType(self.description, simplified_columns, self.concrete)

    def children(self) -> List[ConceptType]:
        return [column.t for column in self.columns]

    def __repr__(self) -> str:
        return f"Table[{', '.join([column.__repr__() for column in self.columns])}]"

    def __str__(self) -> str:
        return "table"

    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        if self == old:
            return new

        new_columns = [
            ConceptTableTypeColumn(column.name, column.description, new) if column.t == old else ConceptTableTypeColumn(column.name, column.description, old)
            for column in self.columns
        ]

        return ConceptTableType(self.description, new_columns, self.concrete)

    def __eq__(self, other) -> bool:
        if isinstance(other, ConceptTableType):
            return self.columns == other.columns
        return False

    def __hash__(self) -> int:
        combined_hash = hash("Table")
        for field in self.columns:
            combined_hash ^= hash(field)
        return combined_hash
