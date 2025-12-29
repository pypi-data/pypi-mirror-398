"""This module is meant to be used only if attrs library is installed. The library is an opt-in dependency."""

from typing import Any, Optional, Tuple

from attrs import NOTHING, Factory, fields, has

from ...docstring import DocstringParser
from ..types.dict import ConceptDictionaryType, ConceptDictionaryTypeField


def is_attrs(annotation: Any) -> bool:
    return has(annotation)


def compute_default_value(field: Any) -> Tuple[bool, Any]:
    default_value = field.default
    if default_value is not NOTHING:
        if isinstance(default_value, Factory):  # type: ignore[reportArgumentType]
            return True, default_value.factory()

        return True, default_value

    return False, None


def from_attrs(annotation, factory, unset) -> ConceptDictionaryType:
    docstring = DocstringParser.parse(annotation.__doc__)
    unset = getattr(annotation, "__unset__", unset)

    dict_fields = []

    for field in fields(annotation):
        description: Optional[str] = next((attribute.description for attribute in docstring.attributes if attribute.name == field.name), None)

        has_default_value, default_value = compute_default_value(field)

        if field.init is False:
            concept_type = factory.from_type(Optional[field.type], unset=unset)  # type: ignore
        else:
            concept_type = factory.from_type(field.type, unset=unset)  # type: ignore

        dict_fields.append(ConceptDictionaryTypeField(field.name, description, concept_type, default_value, has_default_value, field.init))

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
