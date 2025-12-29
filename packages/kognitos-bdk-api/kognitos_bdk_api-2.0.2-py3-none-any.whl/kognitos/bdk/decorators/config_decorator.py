import inspect
from typing import Optional

from kognitos.bdk.api import NounPhrase
from kognitos.bdk.klang import KlangParser


def config(*args, **kwargs):
    name: Optional[str] = None

    if len(args) == 1 and inspect.isfunction(args[0]):
        fn = args[0]
        name = None
        default_value = None
    elif kwargs:
        fn = None
        name = kwargs.get("name", None)
        if not name and len(args) == 1:
            name = args[0]
        default_value = kwargs.get("default_value", None)
    else:
        fn = None
        name = args[0]
        default_value = None

    def decorator(fn):
        if not inspect.isfunction(fn):
            raise TypeError("The config decorator can only be applied to functions which also have @property.")

        # parse noun phrases
        if name:
            noun_phrases_tuples, _ = KlangParser.parse_noun_phrases(name)
            noun_phrases = [NounPhrase.from_tuple(npt) for npt in noun_phrases_tuples]
        else:
            noun_phrases = [NounPhrase.from_word_list(fn.__name__.split("_"))]

        if not hasattr(fn, "__noun_phrase__"):
            fn.__noun_phrase__ = noun_phrases

        if not hasattr(fn, "__default_value__"):
            fn.__default_value__ = default_value

        return fn

    if fn is not None:
        return decorator(fn)

    return decorator
