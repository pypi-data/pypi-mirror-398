import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class NounPhrase:
    """
    Represents a noun phrase.

    Args:
        head (str): The head of the noun phrase.
        modifiers (List[str], optional): The modifiers of the noun phrase. Defaults to None.

    Examples:
        # Create a noun phrase with the head "cat"
        >>> np = NounPhrase("cat")
        >>> print(np)
        cat

        # Create a noun phrase with the head "dog" and modifiers ["big", "white"]
        >>> np = NounPhrase("dog", ["big", "white"])
        >>> print(np)
        big white dog
    """

    head: str
    modifiers: Optional[List[str]] = None

    def __eq__(self, other):
        if self.head != other.head:
            return False

        self_modifiers = self.modifiers if self.modifiers else []
        other_modifiers = other.modifiers if other.modifiers else []

        return self_modifiers == other_modifiers

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return " ".join((self.modifiers if self.modifiers else []) + [self.head])

    @classmethod
    def from_snake_case(cls, snake_str: str) -> "NounPhrase":
        # replace underscores with spaces
        words = snake_str.replace("_", " ")
        return NounPhrase(head=words, modifiers=[])

    @classmethod
    def from_pascal_case(cls, pascal_str: str) -> "NounPhrase":
        # remove existing spaces
        pascal_str = pascal_str.replace(" ", "")
        # insert space before each capital letter (except the first one)
        words = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", pascal_str).lower()
        return NounPhrase(head=words, modifiers=[])

    @classmethod
    def from_head(cls, head: str) -> "NounPhrase":
        return NounPhrase(head=head, modifiers=[])

    @classmethod
    def from_str(cls, string: str) -> "NounPhrase":
        return NounPhrase.from_word_list(string.split(" "))

    @classmethod
    def from_word_list(cls, word_list: List[str]) -> "NounPhrase":
        return NounPhrase(head=word_list[-1], modifiers=word_list[0:-1])

    @classmethod
    def from_tuple(cls, noun_phrase_tuple: Tuple[str, Optional[List[str]]]) -> "NounPhrase":
        return NounPhrase(noun_phrase_tuple[0], noun_phrase_tuple[1])

    def to_camel_case(self) -> str:
        snake_str = self.to_snake_case()
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def to_snake_case(self) -> str:
        text = self.to_string()
        return text.lower().replace(" ", "_")

    def to_kebab_case(self) -> str:
        snake_str = self.to_snake_case()
        return snake_str.replace("_", "-")

    def to_field_names(self) -> List[str]:
        snake_case = self.to_snake_case()
        camel_case = self.to_camel_case()
        kebab_case = self.to_kebab_case()
        return [snake_case, camel_case, kebab_case]

    def __hash__(self):
        return hash((self.head, tuple(self.modifiers) if self.modifiers else ()))


class NounPhrases:
    """
    Represents a list of noun phrases.

    Args:
        noun_phrases (List[NounPhrase]): The list of noun phrases.
    """

    def __init__(self, noun_phrases: List[NounPhrase]):
        self.noun_phrases = noun_phrases

    def to_string(self):
        return "'s ".join([str(np) for np in self.noun_phrases])

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return f"NounPhrases({self.noun_phrases})"

    def __hash__(self) -> int:
        return hash(tuple(hash(np) for np in self.noun_phrases) if self.noun_phrases else ())

    def __eq__(self, other):
        return isinstance(other, NounPhrases) and hash(self) == hash(other)

    @classmethod
    def from_str(cls, string: str) -> "NounPhrases":
        return cls(noun_phrases=[NounPhrase.from_str(noun_phrase) for noun_phrase in string.split("'s ")])
