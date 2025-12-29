import inspect
from typing import Any, List, Optional, Type, Union

from kognitos.bdk.api.noun_phrase import NounPhrase
from kognitos.bdk.klang import KlangParser


def concept(*args, **kwargs):  # pylint: disable=invalid-name
    cls: Optional[Type] = None
    is_a: Optional[Union[List[str], str]] = None
    unset: Optional[Any] = None

    if len(args) == 1 and not kwargs and isinstance(args[0], type):
        cls = args[0]
        is_a = None
        unset = None
    else:
        cls = None
        is_a = kwargs.get("is_a", None)
        unset = kwargs.get("unset", None)

    def decorator(cls):
        if not inspect.isclass(cls):
            raise TypeError("The concept decorator can only be applied to classes.")

        if not cls.__doc__:
            raise ValueError("missing docstring")

        if not is_a:
            raise ValueError("missing 'is_a'")

        # parse noun phrase
        noun_phrases_is_a: List[NounPhrase] = []
        for noun_phrase in is_a if isinstance(is_a, list) else [is_a]:
            noun_phrases_tuples, _ = KlangParser.parse_noun_phrases(noun_phrase)
            if len(noun_phrases_tuples) != 1:
                raise ValueError("is_a cannot contain possessive suffix")

            noun_phrases_is_a.append(NounPhrase.from_tuple(noun_phrases_tuples[0]))

        if not hasattr(cls, "__is_a__"):
            cls.__is_a__ = set(noun_phrases_is_a)

        if not hasattr(cls, "__unset__") and unset is not None:
            cls.__unset__ = unset

        return cls

    if cls is None:
        return decorator

    return decorator(cls)
