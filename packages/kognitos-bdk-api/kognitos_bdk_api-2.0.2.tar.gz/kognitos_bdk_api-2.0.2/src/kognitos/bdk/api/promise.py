from typing import Generic, TypeVar

T = TypeVar("T")


class Promise(Generic[T]):
    """
    A BDK promise returned by a procedure, to be resolved by a
    resolver function (specified by the `@promise` decorator on
    the procedure itself).
    """

    def __init__(self, data: T):
        self.data = data
        self._resolver_id = None  # This should never be set manually, but instead by the BDK runtime

    def __str__(self):
        return f"Promise({self.data})"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.data, self._resolver_id))

    def __eq__(self, other):
        return isinstance(other, Promise) and hash(self) == hash(other)
