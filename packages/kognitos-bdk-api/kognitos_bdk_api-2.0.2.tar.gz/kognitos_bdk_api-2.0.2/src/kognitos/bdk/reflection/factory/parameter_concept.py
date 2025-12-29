from inspect import Parameter
from typing import List, Optional

from ...reflection import ParameterConceptBind
from ..concept_descriptor import ConceptDescriptor
from .concept import ConceptFactory


class ParameterConceptFactory:
    @classmethod
    def from_parameter(cls, parameter: Parameter, concepts: Optional[List[ConceptDescriptor]] = None, description: Optional[str] = None) -> "ParameterConceptBind":
        return ParameterConceptBind(
            python_name=parameter.name,
            concepts=concepts if concepts else [ConceptFactory.from_parameter(parameter)],
            description=description,
        )
