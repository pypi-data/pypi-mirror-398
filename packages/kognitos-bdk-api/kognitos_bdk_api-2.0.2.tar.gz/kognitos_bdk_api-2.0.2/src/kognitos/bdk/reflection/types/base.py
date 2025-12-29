from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import List, Optional, Set, Type


class ConceptType(ABC, metaclass=ABCMeta):
    @property
    def name(self):
        return str(self)

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def simplify(self) -> ConceptType:
        pass

    @abstractmethod
    def children(self) -> List[ConceptType]:
        pass

    @abstractmethod
    def replace(self, old: ConceptType, new: ConceptType) -> ConceptType:
        pass

    def find(self, target_type: Type[ConceptType], seen: Optional[Set[ConceptType]] = None) -> List[ConceptType]:
        if seen is None:
            seen = set()

        if self in seen:
            return []

        seen.add(self)
        instances = []

        for child in self.children():
            if isinstance(child, target_type):
                instances.append(child)

            instances.extend(child.find(target_type, seen))

        return list(set(instances))

    def flatten(self, **_kwargs) -> List[ConceptType]:
        return [self]
