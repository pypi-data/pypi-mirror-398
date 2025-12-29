from typing import List, Optional

from docstring_parser import Docstring as BaseDocstring
from docstring_parser import DocstringMeta as BaseDocstringMeta
from docstring_parser import DocstringParam as BaseDocstringParam

from kognitos.bdk.klang import KlangParser

from ..api.noun_phrase import NounPhrase
from .example import DocstringExample


class DocstringConcept:
    _meta: Optional[BaseDocstringMeta]

    def __init__(self, meta: Optional[BaseDocstringMeta]):
        self._meta = meta

    @property
    def name(self) -> Optional[str]:
        if self._meta:
            return self._meta.args[1]

        return None

    @property
    def description(self) -> Optional[str]:
        if self._meta:
            return self._meta.description

        return None

    @property
    def noun_phrases(self) -> Optional[List[NounPhrase]]:
        try:
            if self._meta:
                noun_phrases, _ = KlangParser.parse_determiner_noun_phrases(self._meta.args[1])
                return [NounPhrase.from_tuple(np) for np in noun_phrases] if noun_phrases else None
        except SyntaxError:
            pass

        return None


class DocstringAttribute:
    _meta: Optional[BaseDocstringMeta]

    def __init__(self, meta: Optional[BaseDocstringMeta]):
        self._meta = meta

    @property
    def name(self) -> Optional[str]:
        if self._meta:
            return self._meta.args[1]

        return None

    @property
    def description(self) -> Optional[str]:
        if self._meta:
            return self._meta.description

        return None


class DocstringEnumMember:
    _name: str
    _member_meta: Optional[BaseDocstringMeta]
    _label_meta: Optional[BaseDocstringMeta]

    def __init__(self, member_meta: Optional[BaseDocstringMeta], label_meta: Optional[BaseDocstringMeta], name: Optional[str] = None):
        self._name = name
        self._member_meta = member_meta
        self._label_meta = label_meta

    @property
    def name(self) -> str:
        """
        Resolve the name of the enum member. It cascades through the possible data sources:

        1. The name of the enum member in the member meta
        2. The name of the enum member
        3. The name of the enum member in the label meta
        """
        if self._member_meta:
            return self._member_meta.args[1]

        if self._name:
            return self._name

        if self._label_meta:
            return self._label_meta.args[1]

        raise ValueError("Could not resolve name for enum member")

    @property
    def description(self) -> Optional[str]:
        if self._member_meta:
            return self._member_meta.description

        return None

    @property
    def noun_phrase(self) -> Optional[NounPhrase]:
        if self._label_meta:
            raw_noun_phrase_string = self._label_meta.description
            if raw_noun_phrase_string:
                noun_phrases, _ = KlangParser.parse_noun_phrases(raw_noun_phrase_string)
                return NounPhrase.from_tuple(noun_phrases[0])
            raise ValueError(f"No noun phrase found for enum member {self.name}. You probably have a malformed label docstring.")

        if self.name:
            raw_noun_phrase_string = self.name
            return NounPhrase.from_snake_case(raw_noun_phrase_string.lower())

        return None


class DocstringParam:
    _docstring: Optional[BaseDocstringParam]
    _meta: Optional[BaseDocstringMeta]

    def __init__(self, docstring: Optional[BaseDocstringParam], meta: Optional[BaseDocstringMeta]):
        self._docstring = docstring
        self._meta = meta

    @property
    def name(self) -> Optional[str]:
        if self._docstring:
            return self._docstring.arg_name

        if self._meta:
            return self._meta.args[1]

        return None

    @property
    def description(self) -> Optional[str]:
        if self._docstring:
            return self._docstring.description

        return None

    @property
    def label(self) -> Optional[str]:
        if self._meta:
            return self._meta.description

        return None


class Docstring:
    docstring: BaseDocstring

    def __init__(self, docstring: BaseDocstring):
        self.docstring = docstring

    @property
    def author(self) -> Optional[str]:
        for meta in self.docstring.meta:
            if "author" in meta.args:
                return meta.description
        return None

    @property
    def short_description(self) -> Optional[str]:
        return self.docstring.short_description

    @property
    def long_description(self) -> Optional[str]:
        return self.docstring.long_description

    @property
    def returns(self) -> Optional[str]:
        return self.docstring.returns.description if self.docstring.returns else None

    @property
    def input_concepts(self) -> List[DocstringConcept]:
        inputs = []

        for meta in self.docstring.meta:
            if len(meta.args) > 1:
                if meta.args[0] == "inputs":
                    inputs.append(DocstringConcept(meta))

        return inputs

    @property
    def examples(self) -> List[DocstringExample]:
        return [DocstringExample(example) for example in self.docstring.examples]

    @property
    def output_concepts(self) -> List[DocstringConcept]:
        outputs = []

        for meta in self.docstring.meta:
            if len(meta.args) > 1:
                if meta.args[0] == "outputs":
                    outputs.append(DocstringConcept(meta))

        return outputs

    @property
    def attributes(self) -> List[DocstringAttribute]:
        attributes = []

        for meta in self.docstring.meta:
            if len(meta.args) > 1:
                if meta.args[0] == "attribute":
                    attributes.append(DocstringAttribute(meta))

        return attributes

    @property
    def params(self) -> List[DocstringParam]:
        def convert_param(param: BaseDocstringParam):
            param_meta = None
            for meta in self.docstring.meta:
                if len(meta.args) > 1:
                    if meta.args[0] == "label" and meta.args[1] == param.arg_name:
                        param_meta = meta
                        break

            return DocstringParam(param, param_meta)

        params = list(map(convert_param, self.docstring.params))

        for meta in self.docstring.meta:
            if len(meta.args) > 1:
                if meta.args[0] == "label":
                    already = [param for param in params if param.name == meta.args[1]]
                    if not already:
                        params.append(DocstringParam(None, meta))

        return params

    @property
    def enum_members(self) -> List[DocstringEnumMember]:
        members = []

        enum_metas = sorted([meta for meta in self.docstring.meta if len(meta.args) > 1 and meta.args[0] == "enum"], key=lambda x: x.args[1])
        enum_label_metas = sorted([meta for meta in self.docstring.meta if len(meta.args) > 1 and meta.args[0] == "enum label"], key=lambda x: x.args[1])
        seen_enum_label_metas = set()

        # Make sure to initialize enum members with the correct label meta if it exists
        for enum_meta in enum_metas:
            enum_label_meta = next((meta for meta in enum_label_metas if meta.args[1] == enum_meta.args[1]), None)
            if enum_label_meta:
                seen_enum_label_metas.add(enum_label_meta)

            members.append(DocstringEnumMember(enum_meta, enum_label_meta))

        # Initialize enum members with the correct label meta if it exists but was not seen before, i.e the enum meta for the key description was not set.
        for elm in set(enum_label_metas) - seen_enum_label_metas:
            members.append(DocstringEnumMember(None, elm))

        return members

    def enum_member_by_name(self, name: str) -> DocstringEnumMember:
        """
        Given a name, return the description of the enum key.

        If no member is found, return a new DocstringEnumMember with the given name.
        """
        return next((member for member in self.enum_members if member.name == name), DocstringEnumMember(None, None, name))

    def param_by_name(self, param: str) -> Optional[DocstringParam]:
        for doc_param in self.params:
            if doc_param.name == param:
                return doc_param

        return None

    def param_description_by_name(self, param: str) -> Optional[str]:
        for doc_param in self.params:
            if doc_param.name == param:
                return doc_param.description

        return None

    def input_concept_by_noun_phrases(self, noun_phrases: List[NounPhrase]) -> Optional[DocstringConcept]:
        for doc_concept in self.input_concepts:
            if doc_concept.noun_phrases == noun_phrases:
                return doc_concept

        return None

    def input_description_by_noun_phrases(self, noun_phrases: List[NounPhrase]) -> Optional[str]:
        for doc_concept in self.input_concepts:
            if doc_concept.noun_phrases == noun_phrases:
                return doc_concept.description

        return None

    def output_concept_by_noun_phrases(self, noun_phrases: List[NounPhrase]) -> Optional[DocstringConcept]:
        for doc_concept in self.output_concepts:
            if doc_concept.noun_phrases == noun_phrases:
                return doc_concept

        return None

    def output_description_by_noun_phrases(self, noun_phrases: List[NounPhrase]) -> Optional[str]:
        if self.output_concepts:
            for doc_concept in self.output_concepts:
                if doc_concept.noun_phrases == noun_phrases:
                    return doc_concept.description
        elif self.returns and noun_phrases == [NounPhrase("answer", [])]:
            return self.returns

        return None

    @property
    def setup_description(self) -> Optional[str]:
        for meta in self.docstring.meta:
            if len(meta.args) > 0:
                if meta.args[0] == "setup description":
                    return meta.description
        return None
