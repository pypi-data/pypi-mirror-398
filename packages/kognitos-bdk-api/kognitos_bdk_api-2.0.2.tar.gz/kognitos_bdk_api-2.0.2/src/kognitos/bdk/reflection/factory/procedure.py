from __future__ import annotations

import inspect
from inspect import Signature
from types import NoneType
from typing import Any, Dict, List, Optional, Tuple, Union, get_origin

from ...api import FilterExpression, NounPhrase
from ...docstring import Docstring
from ...errors import SignatureError
from ..book_procedure_descriptor import (BookProcedureDescriptor,
                                         ConnectionRequired)
from ..book_procedure_signature import BookProcedureSignature
from ..concept_descriptor import ConceptDescriptor
from ..example import Example
from ..factory.parameter_concept import ParameterConceptFactory
from ..parameter_concept_bind import ParameterConceptBind
from ..question_descriptor import QuestionDescriptor
from .concept import ConceptFactory
from .types import (extract_and_check_question_types, extract_promise_types,
                    is_none, is_union_type)


def noun_phrase_to_parameter(noun_phrase: NounPhrase) -> str:
    name = noun_phrase.modifiers.copy() if noun_phrase.modifiers else []
    name.append(noun_phrase.head)

    return "_".join(name)


def find_noun_phrase_path(target_or_object: Optional[List[NounPhrase]], noun_phrases: List[NounPhrase]) -> Optional[List[NounPhrase]]:
    if not target_or_object:
        return None

    len_target_or_object = len(target_or_object)
    len_noun_phrases = len(noun_phrases)

    for start in range(len_target_or_object - len_noun_phrases + 1):
        if target_or_object[start : start + len_noun_phrases] == noun_phrases:
            return target_or_object[: start + len_noun_phrases]

    return None


def argument_name(python_signature: Signature, pos: Optional[int]) -> Optional[str]:
    """
    Get the name of the argument at the given position in the signature.

    Args:
        python_signature: The signature to get the argument name from.
        pos: The position of the argument to get the name from.

    Returns:
        The name of the argument at the given position, or None if the position is out of bounds.
    """
    if pos is None:
        return None

    parameters = list(python_signature.parameters.values())

    if len(parameters) > pos:
        return parameters[pos].name

    return None


def has_default(python_signature: Signature, pos: Optional[int]) -> Optional[bool]:
    """
    Check if the argument at the given position in the signature has a default value.

    Args:
        python_signature: The signature to check the default value of the argument from.
        pos: The position of the argument to check the default value of.

    Returns:
        True if the argument has a default value, False otherwise. If the position is out of bounds, None is returned.
    """
    if pos is None:
        return None

    parameters = list(python_signature.parameters.values())

    if 0 <= pos < len(parameters):
        return parameters[pos].default is not inspect.Parameter.empty

    return None


class BookProcedureFactory:
    @classmethod
    def create(
        cls,
        identifier: str,
        english_signature: BookProcedureSignature,
        python_signature: Signature,
        docstring: Docstring,
        override_connection_required: Optional[ConnectionRequired],
        is_mutation: bool,
        search_hints: List[str],
    ) -> BookProcedureDescriptor:
        # by default no procedure is filter enabled
        filter_capable = False
        filter_argument_position: Optional[int] = None

        # by default no procedure is page enabled
        page_capable = False
        offset_argument_position: Optional[int] = None
        limit_argument_position: Optional[int] = None

        # parameter concept map
        pcm: List[ParameterConceptBind] = []

        # add mapping for each part of speech
        for pos in ("object", "target"):
            english_pos: Optional[List[NounPhrase]] = getattr(english_signature, pos, None)
            if english_pos:
                python_pos_parameter = python_signature.parameters.get(pos)
                if python_pos_parameter:
                    parameter_pos_annotation = getattr(
                        python_pos_parameter.annotation,
                        "__origin__",
                        python_pos_parameter.annotation,
                    )
                    if parameter_pos_annotation and issubclass(parameter_pos_annotation, Tuple):
                        concepts = [
                            ConceptFactory.from_noun_phrase_and_annotation(
                                noun_phrase, python_pos_parameter.annotation.__args__[idx], description=docstring.input_description_by_noun_phrases([noun_phrase])
                            )
                            for idx, noun_phrase in enumerate(english_pos)
                        ]

                        pcm.append(ParameterConceptFactory.from_parameter(python_pos_parameter, concepts=concepts, description=docstring.param_description_by_name(pos)))
                    else:
                        pos_noun_phrase = NounPhrase(head=pos, modifiers=[])
                        concept = ConceptFactory.from_noun_phrase_and_annotation(pos_noun_phrase, python_pos_parameter.annotation)
                        for noun_phrases in [[pos_noun_phrase], english_pos]:
                            if noun_phrases:
                                concept.description = docstring.input_description_by_noun_phrases(noun_phrases)
                                if concept.description:
                                    break

                        pcm.append(ParameterConceptFactory.from_parameter(python_pos_parameter, concepts=[concept], description=docstring.param_description_by_name(pos)))

        # add mapping for any remaining input parameter
        for idx, p in enumerate(python_signature.parameters.items()):
            _, parameter = p

            if parameter.name == "self":
                continue

            if parameter.annotation == FilterExpression or (
                get_origin(parameter.annotation) is Union
                and len(parameter.annotation.__args__) == 2
                and parameter.annotation.__args__[0] == FilterExpression
                and parameter.annotation.__args__[1] == NoneType
            ):
                filter_argument_position = idx
                filter_capable = True
                continue

            if parameter.annotation == int or (
                get_origin(parameter.annotation) is Union
                and len(parameter.annotation.__args__) == 2
                and parameter.annotation.__args__[0] == int
                and parameter.annotation.__args__[1] == NoneType
            ):
                if parameter.name == "offset":
                    offset_argument_position = idx
                    if limit_argument_position is not None:
                        page_capable = True
                    continue

                if parameter.name == "limit":
                    limit_argument_position = idx
                    if offset_argument_position is not None:
                        page_capable = True
                    continue

            if parameter.name not in [param.python_name for param in pcm]:
                parameter_concept = ParameterConceptFactory.from_parameter(parameter, description=docstring.param_description_by_name(parameter.name))
                for concept in parameter_concept.concepts:
                    for noun_phrases in [
                        find_noun_phrase_path(english_signature.object, concept.noun_phrases),
                        find_noun_phrase_path(english_signature.target, concept.noun_phrases),
                        concept.noun_phrases,
                    ]:
                        if noun_phrases:
                            concept.description = docstring.input_description_by_noun_phrases(noun_phrases)
                            if not concept.description:
                                concept.description = parameter_concept.description

                            if concept.description:
                                break
                pcm.append(parameter_concept)

        questions, return_annotation = extract_and_check_question_types(python_signature.return_annotation)
        if questions and is_none(return_annotation) and not is_union_type(python_signature.return_annotation):
            raise ValueError(
                "A procedure cannot always/only return a question. If it can return a question, but has no results, use 'None | Question[Literal['noun phrase'], type]' as the return type-hint."
            )

        promises, return_annotation = extract_promise_types(
            return_annotation
        )  # NOTE: at this instance, we only check for promises to determine if the procedure is async (output types will be resolved later by the book decorator)

        # add type for outputs
        outputs: List[ConceptDescriptor] = []
        if english_signature and english_signature.outputs:
            if len(english_signature.outputs) > 1 and len(english_signature.outputs) != len(getattr(return_annotation, "__args__", [])) and not promises:
                raise SignatureError("The number of elements in the return tuple do not match the number of outputs in the english signature")

            for idx, output in enumerate(english_signature.outputs):
                if not promises:
                    sub_annotation: type = return_annotation.__args__[idx] if len(english_signature.outputs) > 1 else return_annotation
                else:  # NOTE: if it's an async procedure, the output type will be resolved by the book decorator (by visiting the async resolver function)
                    sub_annotation: type = Any  # type: ignore  # Any is not considered a proper type in python, but it is a valid type-hint in BDK

                outputs.append(
                    ConceptFactory.from_noun_phrases_and_annotation(
                        output,
                        sub_annotation,
                        description=docstring.output_description_by_noun_phrases(output),
                    )
                )
        elif return_annotation and return_annotation not in [None, NoneType, inspect.Signature.empty]:
            answer_noun_phrase = NounPhrase(head="answer", modifiers=None)
            output_annotation = (
                return_annotation if not promises else Any
            )  # NOTE: if it's an async procedure, the output type will be resolved by the book decorator (by visiting the async resolver function)
            outputs.append(
                ConceptFactory.from_noun_phrase_and_annotation(
                    answer_noun_phrase,
                    output_annotation,  # type: ignore  # Any is not considered a proper type in python, but it is a valid type-hint in BDK
                    description=(docstring.output_description_by_noun_phrases([answer_noun_phrase])),
                )
            )

        if len(outputs) == 1 and outputs[0].description is None and docstring.returns:
            outputs[0].description = docstring.returns

        return BookProcedureDescriptor(
            id=identifier,
            english_signature=english_signature,
            parameter_concept_map=pcm,
            outputs=outputs,
            questions=questions,
            filter_capable=filter_capable,
            filter_argument_name=argument_name(python_signature, filter_argument_position),
            filter_has_default=has_default(python_signature, filter_argument_position),
            page_capable=page_capable,
            offset_argument_name=argument_name(python_signature, offset_argument_position),
            offset_has_default=has_default(python_signature, offset_argument_position),
            limit_argument_name=argument_name(python_signature, limit_argument_position),
            limit_has_default=has_default(python_signature, limit_argument_position),
            connection_required=ConnectionRequired.OPTIONAL,
            override_connection_required=override_connection_required,
            short_description=docstring.short_description.strip() if docstring.short_description else None,
            long_description=docstring.long_description.strip() if docstring.long_description else None,
            examples=[Example.from_docstring(docstring_example) for docstring_example in docstring.examples],
            is_async=bool(promises),
            is_mutation=is_mutation,
            search_hints=search_hints,
        )

    @classmethod
    def create_discovered_procedure(
        cls,
        procedure_id: str,
        english: str,
        inputs: Dict[str, ConceptDescriptor],
        outputs: List[ConceptDescriptor],
        is_mutation: bool,
        questions: Optional[List[QuestionDescriptor]] = None,
        connection_required: ConnectionRequired = ConnectionRequired.OPTIONAL,
        filter_capable: bool = False,
        page_capable: bool = False,
    ):
        """
        Creates a BookProcedureDescriptor for a discover function.

        Args:
            procedure_id: The identifier for the procedure. It must be unique and is expected to contain all the information required by the developer to implement the invoke function.
            english: The english description of the procedure
            inputs: The input concepts of the procedure. The keys are the names of the parameters, and the values are the ConceptDescriptors.
            outputs: The output concepts of the procedure
            questions: The questions that the procedure can ask
            connection_required: Whether the procedure requires a connection
            filter_capable: Whether the procedure supports filtering. If true a `filter_expression` argument of type FilterExpression will be added.
            page_capable: Whether the procedure supports paging. If true an `offset` and `limit` argument will be added.
        """

        english_signature = BookProcedureSignature.from_english(english)

        parameter_concept_map = [ParameterConceptBind(python_name=python_name, concepts=[concept_descriptor]) for python_name, concept_descriptor in inputs.items()]

        return BookProcedureDescriptor(
            id=procedure_id,
            english_signature=english_signature,
            outputs=outputs,
            questions=questions,
            filter_capable=filter_capable,
            page_capable=page_capable,
            parameter_concept_map=parameter_concept_map,
            connection_required=connection_required,
            override_connection_required=None,
            short_description="",
            long_description="",
            examples=[],
            is_discovered=True,
            filter_argument_name=None if not filter_capable else "filter_expression",
            filter_has_default=None if not filter_capable else False,
            offset_argument_name=None if not page_capable else "offset",
            offset_has_default=None if not page_capable else False,
            limit_argument_name=None if not page_capable else "limit",
            limit_has_default=None if not page_capable else False,
            is_mutation=is_mutation,
        )
