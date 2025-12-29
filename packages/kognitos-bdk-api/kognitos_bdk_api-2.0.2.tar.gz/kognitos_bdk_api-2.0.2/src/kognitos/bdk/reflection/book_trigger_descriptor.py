from dataclasses import dataclass
from typing import Dict

from .concept_descriptor import ConceptDescriptor


@dataclass
class BookTriggerDescriptor:
    id: str
    name: str
    description: str
    setup_description: str
    configuration: Dict[str, ConceptDescriptor]
    filter_capable: bool
    is_manual: bool
    is_shared_endpoint: bool
    event: Dict[str, ConceptDescriptor]
    resolver_function_name: str
