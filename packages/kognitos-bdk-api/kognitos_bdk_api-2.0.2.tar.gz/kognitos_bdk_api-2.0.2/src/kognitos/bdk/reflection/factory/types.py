import importlib
import inspect
import sys
import uuid
from dataclasses import MISSING, fields, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum, EnumMeta
from functools import lru_cache
from importlib.metadata import PackageNotFoundError
from types import NoneType, UnionType
from typing import (IO, TYPE_CHECKING, Any, ForwardRef, List, Optional, Set,
                    Tuple, Union, get_origin)

from kognitos.bdk.api.remote_io import RemoteIO

from ...api.noun_phrase import NounPhrase, NounPhrases
from ...api.promise import Promise
from ...docstring import DocstringParser
from ...reflection.question_descriptor import QuestionDescriptor
from ...typing import Sensitive
from ..types import ConceptTableType
from ..types.any import ConceptAnyType
from ..types.base import ConceptType
from ..types.dict import ConceptDictionaryType, ConceptDictionaryTypeField
from ..types.enum import ConceptEnumType, ConceptEnumTypeMember
from ..types.list import ConceptListType
from ..types.opaque import ConceptOpaqueType
from ..types.optional import ConceptOptionalType
from ..types.scalar import ConceptScalarType
from ..types.self import ConceptSelfType
from ..types.sensitive import ConceptSensitiveType
from ..types.union import ConceptUnionType

if TYPE_CHECKING:
    from ...decorators.rules import AsyncProcedureRule


@lru_cache
def is_attrs_installed():
    try:
        importlib.metadata.distribution("attrs")
        return True
    except PackageNotFoundError:
        return False


@lru_cache
def is_pyarrow_installed():
    try:
        importlib.metadata.distribution("pyarrow")
        return True
    except PackageNotFoundError:
        return False


@lru_cache
def is_arro3_installed():
    try:
        importlib.metadata.distribution("arro3.core")
        return True
    except PackageNotFoundError:
        return False


@lru_cache
def is_nanoarrow_installed():
    try:
        importlib.metadata.distribution("nanoarrow")
        return True
    except PackageNotFoundError:
        return False


if is_attrs_installed():
    from .attrs_utils import from_attrs, is_attrs


if is_pyarrow_installed():
    from pyarrow import Table as PyArrowTable
else:
    PyArrowTable = None

if is_arro3_installed():
    from arro3.core import \
        Table as Arro3Table  # pylint: disable=no-name-in-module
else:
    Arro3Table = None

if is_nanoarrow_installed():
    from nanoarrow import ArrayStream as NanoArrowArrayStream
else:
    NanoArrowArrayStream = None


def should_translate_to_optional(annotation: type, unset: Optional[Any] = None):
    if not get_origin(annotation) in (Union, UnionType):
        return False
    unset_types = [NoneType] if unset is None else [NoneType, unset.__class__]
    unset_types_present = list(map(lambda t: t in unset_types, annotation.__args__)).count(True)
    return unset_types_present >= 1


def get_truthy_types(annotation: type, unset: Optional[Any]) -> List[Any]:
    unset_types = [NoneType] if unset is None else [NoneType, unset.__class__]
    return [t for t in annotation.__args__ if t not in unset_types]


def is_none(annotation: type) -> bool:
    """Check if a type annotation is None, NoneType or empty."""
    return annotation in [None, NoneType, inspect.Signature.empty]


def is_union_type(annotation: type) -> bool:
    return get_origin(annotation) in [Union, UnionType]


def check_not_promise(annotation: type) -> None:
    if get_origin(annotation) is Promise or annotation is Promise:
        raise ValueError(
            "Promises cannot be used as a concept type. If you are type-hinting a procedure to indicate that it can return a promise, apply the @promise decorator and declare the Promise[type] at the top level of the return type-hint (use a union type if you need to declare other type-hints like questions)."
        )


def check_not_question(annotation: type) -> None:
    from ...api.questions import Question  # pylint: disable=cyclic-import

    if get_origin(annotation) is Question or annotation is Question:
        raise ValueError(
            "Questions cannot be used as a concept type. If you are type-hinting a procedure to indicate that it can return a question, use a union type at the top level of the return type-hint."
        )


class ConceptTypeFactory:
    @classmethod
    def from_type(cls, annotation: type, backward: Optional[List[str]] = None, unset: Optional[Any] = None) -> ConceptType:
        check_not_promise(annotation)
        check_not_question(annotation)

        if backward is None:
            backward = []

        if isinstance(annotation, EnumMeta):
            is_a = set(getattr(annotation, "__is_a__", []))

            docstring = DocstringParser.parse(annotation.__doc__ or "")

            keys = sorted(list(annotation.__members__.keys()))
            resolved_members = [docstring.enum_member_by_name(key) for key in keys]

            members = [ConceptEnumTypeMember(member.name, member.description, member.noun_phrase) for member in resolved_members]

            return ConceptEnumType(is_a=is_a, members=members, description=docstring.short_description or docstring.long_description, concrete=annotation)

        if annotation == str:
            return ConceptScalarType.TEXT
        if annotation in (int, float, Decimal):
            concept = ConceptScalarType.NUMBER
            concept.concrete = annotation
            return concept
        if annotation == bool:
            return ConceptScalarType.BOOLEAN
        if annotation == datetime:
            return ConceptScalarType.DATETIME
        if annotation == date:
            return ConceptScalarType.DATE
        if annotation == time:
            return ConceptScalarType.TIME
        if annotation == uuid.UUID:
            return ConceptScalarType.UUID
        if annotation == RemoteIO:
            return ConceptScalarType.FILE
        if should_translate_to_optional(annotation, unset):
            truthy_types = get_truthy_types(annotation, unset)
            if len(truthy_types) == 1:
                return ConceptOptionalType(ConceptTypeFactory.from_type(truthy_types[0], backward, unset)).simplify()

            inner_types = [ConceptTypeFactory.from_type(t, backward, unset) for t in truthy_types]
            return ConceptOptionalType(ConceptUnionType(inner_types)).simplify()
        if get_origin(annotation) == Sensitive:
            return ConceptSensitiveType(ConceptTypeFactory.from_type(annotation.__args__[0], backward, unset)).simplify()
        if get_origin(annotation) == list:
            return ConceptListType(ConceptTypeFactory.from_type(annotation.__args__[0], backward, unset)).simplify()
        if get_origin(annotation) in (Union, UnionType):
            inner_types = [ConceptTypeFactory.from_type(arg, backward, unset) for arg in annotation.__args__]
            return ConceptUnionType(inner_types).simplify()
        if get_origin(annotation) == IO or (inspect.isclass(annotation) and issubclass(annotation, IO)):
            return ConceptScalarType.FILE
        if annotation == NounPhrase:
            return ConceptScalarType.CONCEPTUAL
        if annotation == Any:
            return ConceptAnyType()
        if inspect.isclass(annotation) and issubclass(annotation, Enum):
            return ConceptTypeFactory.from_type(type(next(iter(annotation)).value), unset=unset)
        if isinstance(annotation, ForwardRef):
            if annotation.__forward_arg__ in backward:
                return ConceptSelfType()

            globalns, localns = collect_namespaces()
            resolved = annotation._evaluate(globalns, localns, recursive_guard=set())

            return ConceptTypeFactory.from_type(resolved, backward + [annotation.__forward_arg__], unset=unset).simplify()

        if is_dataclass(annotation):
            return from_dataclass(annotation, unset)

        if is_attrs_installed():
            if is_attrs(annotation):  # pyright: ignore [reportPossiblyUnboundVariable]
                return from_attrs(annotation, cls, unset)  # pyright: ignore [reportPossiblyUnboundVariable]

        if is_pyarrow_installed():
            if PyArrowTable and annotation == PyArrowTable:
                return ConceptTableType(None, [], PyArrowTable)

        if is_arro3_installed():
            if Arro3Table and annotation == Arro3Table:
                return ConceptTableType(None, [], Arro3Table)

        if is_nanoarrow_installed():
            if NanoArrowArrayStream and annotation == NanoArrowArrayStream:
                return ConceptTableType(None, [], NanoArrowArrayStream)

        if hasattr(annotation, "__is_a__"):
            return from_serializable(annotation)

        if get_origin(annotation) == dict:
            # NOTE: these are not used right now, but resolving them does validate their types
            cls.from_type(annotation.__args__[0])
            cls.from_type(annotation.__args__[1])
            return ConceptDictionaryType(set(), None, None, [])

        return ConceptOpaqueType({NounPhrase.from_head("thing")}, None, annotation)


def compute_default_value(field: Any) -> Tuple[bool, Any]:
    if field.default is not MISSING:
        return True, field.default

    if field.default_factory is not MISSING:
        return True, field.default_factory()

    return False, None


def from_dataclass(annotation, unset: Optional[Any] = None):
    docstring = DocstringParser.parse(annotation.__doc__)
    unset = getattr(annotation, "__unset__", unset)
    dict_fields = []

    for field in fields(annotation):
        description: Optional[str] = next((attribute.description for attribute in docstring.attributes if attribute.name == field.name), None)

        has_default_value, default_value = compute_default_value(field)

        if field.init is False:
            concept_type = ConceptTypeFactory.from_type(Optional[field.type], unset=unset)  # type: ignore
        else:
            concept_type = ConceptTypeFactory.from_type(field.type, unset=unset)  # type: ignore

        dict_fields.append(ConceptDictionaryTypeField(field.name, description, concept_type, default_value=default_value, has_default_value=has_default_value, init=field.init))

    return ConceptDictionaryType(
        set(getattr(annotation, "__is_a__", [])),
        annotation,
        (
            (docstring.short_description or "") + (docstring.long_description or "")
            if docstring.short_description and docstring.long_description
            else docstring.short_description or docstring.long_description or ""
        ),
        dict_fields,
        unset=unset,
    )


def from_serializable(annotation):
    docstring = DocstringParser.parse(annotation.__doc__)

    return ConceptOpaqueType(
        set(getattr(annotation, "__is_a__")),
        (
            (docstring.short_description or "") + (docstring.long_description or "")
            if docstring.short_description and docstring.long_description
            else docstring.short_description or docstring.long_description or ""
        ),
        annotation,
    )


def collect_namespaces():
    globalns = {}
    localns = {}

    frame = sys._getframe()
    while frame:
        globalns.update(frame.f_globals)
        localns.update(frame.f_locals)
        frame = frame.f_back

    return globalns, localns


def extract_promise_types(annotation: type) -> Tuple[List[ConceptType], type]:
    def get_promise_inner_type(annotation: type) -> ConceptType:
        if len(getattr(annotation, "__args__", [])) != 1:
            raise ValueError("Promise must have exactly one type argument")
        return ConceptTypeFactory.from_type(annotation.__args__[0])

    if get_origin(annotation) in [Union, UnionType]:
        promise_types = []
        return_types: List[type] = []
        for inner in annotation.__args__:
            if get_origin(inner) is Promise:
                promise_types.append(get_promise_inner_type(inner))
            elif inner not in [None, NoneType]:
                return_types.append(inner)
        return promise_types, condense_types(return_types)

    if get_origin(annotation) is Promise:
        return [get_promise_inner_type(annotation)], NoneType

    return [], annotation


def extract_and_check_question_types(annotation: type) -> Tuple[List[QuestionDescriptor], type]:
    from ...api.questions import Question  # pylint: disable=cyclic-import
    from ...decorators.rules.question_rules import (  # pylint: disable=cyclic-import
        QuestionTypeHintConceptTypeRule, QuestionTypeHintNounPhraseRule,
        QuestionTypeHintStructureRule, QuestionTypingRule)

    annotation_types: List[type]
    if get_origin(annotation) in [Union, UnionType]:
        annotation_types = annotation.__args__
    else:
        annotation_types = [annotation]

    question_rules: List["QuestionTypingRule"] = [
        QuestionTypeHintStructureRule(),
        QuestionTypeHintNounPhraseRule(),
        QuestionTypeHintConceptTypeRule(),
    ]

    return_types: List[type] = []
    questions: List[QuestionDescriptor] = []
    for annotation_type in annotation_types:
        if get_origin(annotation_type) is Question or annotation_type is Question:
            for rule in question_rules:
                rule.validate(annotation_type)
            noun_phrases = NounPhrases([NounPhrase.from_str(noun_phrase) for noun_phrase in annotation_type.__args__[0].__args__[0].split("'s ")])
            question_concept_type = ConceptTypeFactory.from_type(annotation_type.__args__[1])
            questions.append(QuestionDescriptor(noun_phrases, question_concept_type))
        elif annotation_type not in [None, NoneType]:
            return_types.append(annotation_type)

    annotation = condense_types(return_types)

    return questions, annotation


def check_and_resolve_async_procedure(cls: type, member, rules: List["AsyncProcedureRule"], seen: Optional[Set[str]] = None) -> Tuple[type, Set[QuestionDescriptor]]:
    if seen is None:
        seen = set()

    if member.__name__ in seen:
        raise ValueError(f"Circular dependency detected in promise resolver '{member.__name__}'")
    else:
        seen.add(member.__name__)

    for rule in rules:
        rule.validate(cls, member)

    # Extract question types from the member
    member_questions, _ = extract_and_check_question_types(inspect.signature(member).return_annotation)

    resolver_method = getattr(cls, member.__promise_resolver_function_name__)
    if getattr(resolver_method, "__is_async__", False):  # if it has a resolver itself, check and resolve the type and questions recursively
        recursive_return_annotation, recursive_questions = check_and_resolve_async_procedure(cls, resolver_method, rules, seen)
        return recursive_return_annotation, recursive_questions.union(member_questions)

    else:  # if it does not have a resolver, it must be the final resolver, so we break recursion
        resolver_output = inspect.signature(resolver_method).return_annotation
        resolver_questions, resolver_return_annotation = extract_and_check_question_types(resolver_output)
        _, resolver_return_annotation = extract_promise_types(resolver_return_annotation)
        return resolver_return_annotation, set(member_questions + resolver_questions)


def condense_types(types: List[type]) -> type:
    """
    Condenses a list of types into a single type. If there is only one type,
    it is returned as is. If there are multiple types, they are combined into
    a Union type. If there are no types, inspect.Signature.empty is returned.
    """
    if len(types) == 1:
        return types[0]
    elif len(types) > 1:
        return Union.__getitem__(tuple(types))
    else:
        return inspect.Signature.empty


def get_inputs_annotations(method):
    """
    Get the input annotations of a method, excluding the "self" parameter.
    """
    return {k: v.annotation for k, v in dict(inspect.signature(method).parameters).items() if k != "self"}
