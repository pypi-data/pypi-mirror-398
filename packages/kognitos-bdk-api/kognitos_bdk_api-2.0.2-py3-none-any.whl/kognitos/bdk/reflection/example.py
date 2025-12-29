from __future__ import annotations

from dataclasses import dataclass

from ..docstring.example import DocstringExample


@dataclass
class Example:
    description: str
    snippet: str

    @classmethod
    def from_docstring(cls, docstring_example: DocstringExample) -> Example:
        return Example(description=docstring_example.description, snippet=docstring_example.snippet)
