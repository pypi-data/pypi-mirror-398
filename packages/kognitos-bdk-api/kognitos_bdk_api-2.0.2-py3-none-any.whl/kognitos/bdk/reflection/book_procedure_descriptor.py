from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from .book_procedure_signature import BookProcedureSignature
from .concept_descriptor import ConceptDescriptor
from .example import Example
from .parameter_concept_bind import ParameterConceptBind
from .question_descriptor import QuestionDescriptor


class ConnectionRequired(Enum):
    OPTIONAL = 0
    ALWAYS = 1
    NEVER = 2


@dataclass
class BookProcedureDescriptor:
    id: str
    english_signature: BookProcedureSignature
    examples: List[Example] = field(default_factory=list)
    filter_capable: bool = False
    page_capable: bool = False
    connection_required: ConnectionRequired = ConnectionRequired.OPTIONAL
    is_discovered: bool = False
    override_connection_required: Optional[ConnectionRequired] = None
    outputs: Optional[List[ConceptDescriptor]] = None
    questions: Optional[List[QuestionDescriptor]] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    parameter_concept_map: List[ParameterConceptBind] = field(default_factory=list)
    filter_argument_name: Optional[str] = None
    offset_argument_name: Optional[str] = None
    limit_argument_name: Optional[str] = None
    filter_has_default: Optional[bool] = None
    offset_has_default: Optional[bool] = None
    limit_has_default: Optional[bool] = None
    is_async: bool = False
    is_mutation: bool = True
    search_hints: List[str] = field(default_factory=list)

    @property
    def input_concepts(self) -> Optional[List[ConceptDescriptor]]:
        input_concepts = []

        for parameter_concept in self.parameter_concept_map:
            input_concepts.extend(parameter_concept.concepts)

        return input_concepts if len(input_concepts) != 0 else None

    @property
    def output_concepts(self) -> Optional[List[ConceptDescriptor]]:
        return self.outputs
