import inspect


def search_hint(text: str):
    """Decorator to register a search hint string for a procedure.

    Can be stacked multiple times on a function decorated with @procedure.
    Stores the raw strings without parsing.
    """
    if not isinstance(text, str):
        raise TypeError("search_hint must be provided a string")

    def decorator(fn):
        if not inspect.isfunction(fn):
            raise TypeError("The search_hint decorator can only be applied to functions.")
        existing = getattr(fn, "__search_hints__", None)
        if existing is None:
            setattr(fn, "__search_hints__", [text])
        else:
            # Insert at the front to preserve source order when stacking decorators
            existing.insert(0, text)
        return fn

    return decorator
