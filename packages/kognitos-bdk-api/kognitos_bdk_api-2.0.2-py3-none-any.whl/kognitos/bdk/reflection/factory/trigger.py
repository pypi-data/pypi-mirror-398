from __future__ import annotations

from inspect import Signature
from typing import Dict

from ...docstring import Docstring
from ..book_trigger_descriptor import BookTriggerDescriptor
from ..concept_descriptor import ConceptDescriptor
from .parameter_concept import ParameterConceptFactory


class BookTriggerFactory:
    @classmethod
    def create(
        cls,
        identifier: str,
        name: str,
        is_manual: bool,
        is_shared_endpoint: bool,
        python_signature: Signature,
        docstring: Docstring,
        configuration_params: list[str],
        resolver_function_name: str,
    ) -> BookTriggerDescriptor:
        """
        Create a BookTriggerDescriptor from a trigger function.

        Args:
            identifier: Unique identifier for the trigger
            name: The trigger name
            is_manual: Whether the trigger is manual
            is_shared_endpoint: Whether all configured trigger instances share the same endpoint
            python_signature: The Python signature of the trigger function
            docstring: Parsed docstring
            configuration_params: List of parameter names that are configuration
            resolver_function_name: The name of the resolver function

        Returns:
            BookTriggerDescriptor instance
        """
        # Check if filter_expression is present to determine filter_capable
        filter_capable = "filter_expression" in python_signature.parameters

        # Build configuration map (all params except endpoint and filter_expression)
        configuration: Dict[str, ConceptDescriptor] = {}
        for param_name in configuration_params:
            parameter = python_signature.parameters[param_name]
            param_description = docstring.param_description_by_name(param_name)
            parameter_concept = ParameterConceptFactory.from_parameter(parameter, description=param_description)
            # Use the first concept from the parameter concept and set its description
            if parameter_concept.concepts:
                concept = parameter_concept.concepts[0]
                # Set the description on the concept if it doesn't have one
                if not concept.description and param_description:
                    concept.description = param_description
                configuration[param_name] = concept

        # Build event map - initially empty, will be populated by book decorator
        # when it analyzes the resolver function's return type
        event: Dict[str, ConceptDescriptor] = {}

        description = (docstring.short_description.strip() if docstring.short_description else "") + (docstring.long_description.strip() if docstring.long_description else "")
        setup_description = docstring.setup_description.strip() if docstring.setup_description else ""

        return BookTriggerDescriptor(
            id=identifier,
            name=name,
            description=description,
            setup_description=setup_description,
            configuration=configuration,
            filter_capable=filter_capable,
            is_manual=is_manual,
            is_shared_endpoint=is_shared_endpoint,
            event=event,
            resolver_function_name=resolver_function_name,
        )
