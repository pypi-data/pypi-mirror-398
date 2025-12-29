from docstring_parser import ParseError
from docstring_parser.google import GoogleParser

from .docstring import Docstring
from .error import DocstringParseError
from .sections import DEFAULT_SECTIONS


class DocstringParser:  # pylint disable=too-few-public-methods
    @classmethod
    def parse(cls, text: str) -> Docstring:
        try:
            parser = GoogleParser(DEFAULT_SECTIONS)
            return Docstring(docstring=parser.parse(text))
        except ParseError as ex:
            raise DocstringParseError(original_exception=ex) from ex
