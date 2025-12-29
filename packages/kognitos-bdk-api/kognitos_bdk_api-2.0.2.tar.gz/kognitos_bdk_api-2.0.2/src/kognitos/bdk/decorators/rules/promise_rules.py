import inspect
from typing import Callable, get_origin

from kognitos.bdk.api.errors import (
    IntermediatePromiseResolverMismatchOutputError,
    InvalidAsyncProcedureTypeError,
    InvalidFinalPromiseResolverOutputCountError,
    InvalidIntermediatePromiseResolverOutputCountError,
    InvalidPromiseOutputCountError, InvalidPromiseResolverParameterCountError,
    InvalidPromiseResolverParameterTypeError,
    InvalidPromiseTypeArgumentCountError, MissingInputPromiseInOutputError,
    MissingPromiseResolverError, PromiseMismatchOutputTypeError,
    PromiseResolverFunctionNotFoundError, ResolverPromiseTypeMismatchError,
    UnresolvedPromiseError)

from ...api import Promise
from ...reflection.factory.types import (ConceptTypeFactory,
                                         extract_and_check_question_types,
                                         extract_promise_types,
                                         get_inputs_annotations, is_none)


class AsyncProcedureRule:
    def validate(self, book_class: type, async_func: Callable) -> None:
        """Basic validation"""
        if not inspect.isfunction(async_func):
            raise InvalidAsyncProcedureTypeError("The async procedure rule can only be validated against functions.")

        if not hasattr(async_func, "__promise_resolver_function_name__"):
            raise MissingPromiseResolverError(f"Missing promise resolver for function '{async_func.__name__}'. Did you forget to apply the @promise decorator?")

        if not hasattr(book_class, async_func.__promise_resolver_function_name__):
            raise PromiseResolverFunctionNotFoundError(
                f"Promise resolver '{async_func.__promise_resolver_function_name__}' for function '{async_func.__name__}' not found in book class."
            )


class AsyncProcedureOutputsRule(AsyncProcedureRule):
    def validate(self, book_class: type, async_func: Callable) -> None:
        super().validate(book_class, async_func)
        _, async_func_output = extract_and_check_question_types(inspect.signature(async_func).return_annotation)
        async_func_promises, async_func_return_annotation = extract_promise_types(async_func_output)
        if getattr(async_func, "__is_async__", False) and hasattr(async_func, "__procedure__"):
            if len(async_func_promises) != 1:
                raise InvalidPromiseOutputCountError(
                    f"Promise procedure <{async_func.__name__}> must output exactly one promise. Got {len(async_func_promises)} in the type-hint instead."
                )
            if not is_none(async_func_return_annotation):
                raise PromiseMismatchOutputTypeError(
                    f"Promise procedure <{async_func.__name__}> should not output any other types when returning a promise. Got {async_func_return_annotation}."
                )


class IntermediateAsyncResolverOutputsRule(AsyncProcedureRule):
    def validate(self, book_class: type, async_func: Callable) -> None:
        intermediate_async_resolver = async_func
        super().validate(book_class, intermediate_async_resolver)
        _, intermediate_async_resolver_output = extract_and_check_question_types(inspect.signature(intermediate_async_resolver).return_annotation)
        intermediate_async_resolver_promises, intermediate_async_resolver_return_annotation = extract_promise_types(intermediate_async_resolver_output)
        if getattr(intermediate_async_resolver, "__is_async__", False) and not hasattr(intermediate_async_resolver, "__procedure__"):
            # NOTE: at this point, its guaranteed that intermediate_async_resolver has a promise resolver itself (we are in an intermediate resolver)
            if len(intermediate_async_resolver_promises) not in [1, 2]:
                raise InvalidIntermediatePromiseResolverOutputCountError(
                    f"Intermediate promise resolver <{intermediate_async_resolver.__name__}> must be able to output the input and output promises (two if they are of different types, one if they are the same). Got {len(intermediate_async_resolver_promises)} promise declarations in the type-hint instead."
                )
            if not is_none(intermediate_async_resolver_return_annotation):
                raise IntermediatePromiseResolverMismatchOutputError(
                    f"Intermediate promise resolver <{intermediate_async_resolver.__name__}> should not output anything other than the input/output promises. Got {intermediate_async_resolver_return_annotation}."
                )

            # If we reach this point, we know for a fact that intermediate_async_resolver has only one input, which is of type Promise (matching the output of the previous function)
            # Check if it can also return the promise it received
            intermediate_async_resolver_input = get_inputs_annotations(intermediate_async_resolver)
            intermediate_async_resolver_input_annotation = next(iter(intermediate_async_resolver_input.values()))
            intermediate_async_resolver_input_type = ConceptTypeFactory.from_type(intermediate_async_resolver_input_annotation.__args__[0])
            if intermediate_async_resolver_input_type not in intermediate_async_resolver_promises:
                raise MissingInputPromiseInOutputError(
                    f"Intermediate promise resolver <{intermediate_async_resolver.__name__}> must be able to return the promise it received as input. Takes [{repr(intermediate_async_resolver_input_type)}], can return {repr(intermediate_async_resolver_promises)}."
                )


class AsyncResolverInputsRule(AsyncProcedureRule):
    def validate(self, book_class: type, async_func: Callable) -> None:
        super().validate(book_class, async_func)
        _, async_func_output = extract_and_check_question_types(inspect.signature(async_func).return_annotation)
        async_func_promises, _ = extract_promise_types(async_func_output)
        resolver_func = getattr(book_class, async_func.__promise_resolver_function_name__)  # type: ignore # We already checked for the existence of the resolver in the rule superclass
        resolver_input = get_inputs_annotations(resolver_func)

        if len(resolver_input) != 1:
            raise InvalidPromiseResolverParameterCountError(
                f"Promise resolver '{async_func.__promise_resolver_function_name__}' for function '{async_func.__name__}' must have exactly one input parameter. Got {len(resolver_input)} instead."  # type: ignore # We already checked for the existence of the resolver in the rule superclass
            )
        resolver_input_annotation = next(iter(resolver_input.values()))
        if get_origin(resolver_input_annotation) is not Promise:
            raise InvalidPromiseResolverParameterTypeError(
                f"Promise resolver '{async_func.__promise_resolver_function_name__}' for function '{async_func.__name__}' must take a promise as its input parameter. Got {resolver_input_annotation} instead."  # type: ignore # We already checked for the existence of the resolver in the rule superclass
            )
        resolver_input_type = ConceptTypeFactory.from_type(resolver_input_annotation.__args__[0])
        if len(resolver_input_annotation.__args__) != 1:
            raise InvalidPromiseTypeArgumentCountError("Promise must have exactly one type argument")

        if (
            len(async_func_promises) > 1
        ):  # If the async function outputs more than one promise, we discard the one it receives as input (if it outputs just one promise, the input is the same type as the output)
            async_func_input = get_inputs_annotations(async_func)
            async_func_input_annotation = next(iter(async_func_input.values()))
            async_func_input_type = ConceptTypeFactory.from_type(async_func_input_annotation.__args__[0])
            async_func_promises.remove(async_func_input_type)
        if resolver_input_type not in async_func_promises:
            raise ResolverPromiseTypeMismatchError(
                f"Promise resolver <{async_func.__promise_resolver_function_name__}> must take the same promise type as one the output of the function it resolves <{async_func.__name__}>. Got [{repr(resolver_input_type)}], expected {async_func_promises}."  # type: ignore # We already checked for the existence of the resolver in the rule superclass
            )


class AsyncResolverNoUnresolvedPromisesRule(AsyncProcedureRule):
    def validate(self, book_class: type, async_func: Callable) -> None:
        super().validate(book_class, async_func)
        _, async_func_output = extract_and_check_question_types(inspect.signature(async_func).return_annotation)
        async_func_promises, _ = extract_promise_types(async_func_output)
        unresolved_promises = set(async_func_promises)

        # Discard the <input promise> output (in case of an intermediate resolver)
        if not hasattr(async_func, "__procedure__"):
            async_func_input = get_inputs_annotations(async_func)
            async_func_input_annotation = next(iter(async_func_input.values()))
            async_func_input_type = ConceptTypeFactory.from_type(async_func_input_annotation.__args__[0])
            unresolved_promises.discard(async_func_input_type)

        if unresolved_promises:  # If there are still promises to resolve, check the resolver
            resolver_func = getattr(book_class, async_func.__promise_resolver_function_name__)  # type: ignore # We already checked for the existence of the resolver in the rule superclass
            resolver_input = get_inputs_annotations(resolver_func)
            resolver_input_annotation = next(iter(resolver_input.values()))  # We know for a fact that any resolver has exactly one input (a promise)
            resolver_input_type = ConceptTypeFactory.from_type(resolver_input_annotation.__args__[0])
            unresolved_promises.discard(resolver_input_type)

        if unresolved_promises:
            raise UnresolvedPromiseError(
                f"Promise function <{async_func.__name__}> outputs unresolved promises (neither resolved by the function itself nor by its resolver): {unresolved_promises}"
            )


class AsyncFinalResolverOutputsRule(AsyncProcedureRule):
    def validate(self, book_class: type, async_func: Callable) -> None:
        super().validate(book_class, async_func)
        resolver_func = getattr(book_class, async_func.__promise_resolver_function_name__)  # type: ignore # We already checked for the existence of the resolver in the rule superclass
        if not getattr(resolver_func, "__is_async__", False):  # If it's not async, it must be the final resolver
            _, resolver_output = extract_and_check_question_types(inspect.signature(resolver_func).return_annotation)
            resolver_promises, _ = extract_promise_types(resolver_output)
            if len(resolver_promises) != 1:
                raise InvalidFinalPromiseResolverOutputCountError(
                    f"Final promise resolver <{async_func.__promise_resolver_function_name__}> should be able to output one promise (the one it received as input). Got {len(resolver_promises)} in the type-hint instead."  # type: ignore # We already checked for the existence of the resolver in the rule superclass
                )
