from __future__ import annotations

from dataclasses import dataclass

from .concept_descriptor import ConceptDescriptor


@dataclass
class BookConfigDescriptor:
    python_property_name: str
    concept: ConceptDescriptor
