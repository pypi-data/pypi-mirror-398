from typing import Optional

from ..reflection.types import ConceptType


class TypeMismatchError(Exception):
    where: str
    expected: Optional[ConceptType]

    def __init__(self, where: str, expected: ConceptType):
        self.where = where
        self.expected = expected
        super().__init__(f"type mismatch on {where} expected {expected}")


class NotFoundError(Exception):
    message: str

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidAsyncProcedureTypeError(TypeError):
    pass


class MissingPromiseResolverError(ValueError):
    pass


class PromiseResolverFunctionNotFoundError(AttributeError):
    pass


class InvalidPromiseOutputCountError(ValueError):
    pass


class PromiseMismatchOutputTypeError(TypeError):
    pass


class InvalidIntermediatePromiseResolverOutputCountError(ValueError):
    pass


class IntermediatePromiseResolverMismatchOutputError(TypeError):
    pass


class MissingInputPromiseInOutputError(TypeError):
    pass


class InvalidPromiseResolverParameterCountError(ValueError):
    pass


class InvalidPromiseResolverParameterTypeError(TypeError):
    pass


class InvalidPromiseTypeArgumentCountError(TypeError):
    pass


class ResolverPromiseTypeMismatchError(TypeError):
    pass


class UnresolvedPromiseError(ValueError):
    pass


class InvalidFinalPromiseResolverOutputCountError(ValueError):
    pass


class InvalidUserInfoOutputType(TypeError):
    pass
