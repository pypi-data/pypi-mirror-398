from dataclasses import dataclass
from typing import List, Optional, Set

from kognitos.bdk.klang import KlangParser
from kognitos.bdk.klang.parser_signature import ParserSignature

from ..api.noun_phrase import NounPhrase


@dataclass
class BookProcedureSignature:
    english: Optional[str]
    verbs: List[str]
    object: List[NounPhrase]
    preposition: Optional[str]
    outputs: Optional[List[List[NounPhrase]]]
    target: Optional[List[NounPhrase]]
    proper_nouns: Optional[Set[str]]

    @classmethod
    def from_parser_signature(cls, parser_signature: ParserSignature) -> "BookProcedureSignature":
        return BookProcedureSignature(
            english=parser_signature.english,
            verbs=parser_signature.verbs,
            object=[NounPhrase.from_tuple(t) for t in parser_signature.object],
            preposition=parser_signature.preposition,
            outputs=[[NounPhrase.from_tuple(t) for t in c] for c in parser_signature.outputs] if parser_signature.outputs else None,
            target=[NounPhrase.from_tuple(t) for t in parser_signature.target] if parser_signature.target else None,
            proper_nouns=parser_signature.proper_nouns,
        )

    @classmethod
    def from_english(cls, english: str) -> "BookProcedureSignature":
        parser_signature = KlangParser.parse_signature(english)

        return BookProcedureSignature.from_parser_signature(parser_signature)
