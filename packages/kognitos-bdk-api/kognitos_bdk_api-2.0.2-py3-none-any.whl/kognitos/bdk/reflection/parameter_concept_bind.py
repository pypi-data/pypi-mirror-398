from dataclasses import dataclass
from typing import List, Optional

from .concept_descriptor import ConceptDescriptor


@dataclass
class ParameterConceptBind:
    python_name: str
    concepts: List[ConceptDescriptor]
    description: Optional[str] = None
