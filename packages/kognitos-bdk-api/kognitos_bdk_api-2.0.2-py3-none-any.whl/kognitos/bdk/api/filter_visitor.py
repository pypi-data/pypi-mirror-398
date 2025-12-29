from __future__ import annotations

import dataclasses
import inspect
from functools import partial
from typing import Callable, List, TypeVar

from kognitos.bdk.api import (FilterBinaryExpression, FilterBinaryOperator,
                              FilterExpressionVisitor, FilterUnaryExpression,
                              FilterUnaryOperator, NounPhrasesExpression,
                              ValueExpression)

T = TypeVar("T")
FilterFunction = Callable[[T], bool]


class FilterPredicates:
    @staticmethod
    def filter_in(item, left, right):
        """
        Check if the right value is in the left attribute of the item.
        """
        return right in (getattr(item, left, None) or [])

    @staticmethod
    def filter_equals(item, left: str, right):
        """
        Check if the left attribute of the item is equal to the right value.
        """
        return getattr(item, left, None) == right

    @staticmethod
    def filter_not_equals(item, left, right):
        """
        Check if the left attribute of the item is not equal to the right value.
        """
        return not FilterPredicates.filter_equals(item, left, right)

    @staticmethod
    def filter_and(item, left, right):
        """
        Check if both left and right predicates are true.
        """
        return left(item) and right(item)

    @staticmethod
    def filter_or(item, left, right):
        """
        Check if either left or right predicates are true.
        """
        return left(item) or right(item)

    @staticmethod
    def filter_has(item, left, right):
        """
        Check if the left attribute of the item has the right value.
        """
        return right in (getattr(item, left, None) or [])

    @staticmethod
    def filter_less_than(item, left, right):
        """
        Check if the left attribute of the item is less than the right value.
        """
        left_value = getattr(item, left, None)
        return left_value is not None and left_value < right

    @staticmethod
    def filter_less_than_or_equal(item, left, right):
        """
        Check if the left attribute of the item is less than or equal to the right value.
        """
        left_value = getattr(item, left, None)
        return left_value is not None and left_value <= right

    @staticmethod
    def filter_greater_than(item, left, right):
        """
        Check if the left attribute of the item is greater than the right value.
        """
        left_value = getattr(item, left, None)
        return left_value is not None and left_value > right

    @staticmethod
    def filter_greater_than_or_equal(item, left, right):
        """
        Check if the left attribute of the item is greater than or equal to the right value.
        """
        left_value = getattr(item, left, None)
        return left_value is not None and left_value >= right

    @staticmethod
    def filter_not(item, predicate):
        """
        Negate the input filter predicate.
        """
        return not predicate(item)


def is_field_or_property(cls, name: str) -> bool:
    """
    Checks if the provided name is a field or a property of the given dataclass.
    """
    # Check if the name is a field
    field_names = {field.name for field in dataclasses.fields(cls)}
    if name in field_names:
        return True

    # Check if the name is a property
    for attr_name, _ in inspect.getmembers(cls, lambda a: isinstance(a, property)):
        if attr_name == name:
            return True

    return False


class CollectionFilterExpressionVisitor(FilterExpressionVisitor):
    """
    This class is an implementation of the FilterExpressionVisitor intended to be used for
    filtering in-memory collections of objects based on the provided filter expression.

    The filterable_classes parameter is a list of classes that the filter expression can be applied to.
    These are intended to be the classes included in the collection. The main objective of declaring these classes
    is to be able to handle errors when the filter expression references an attribute that does not exist in any of the classes.
    The visitor will raise a ValueError if the filter expression references an attribute that does not exist in any of the classes.

    The visitor, when accepted by the filter expression, returns a FilterFunction, defined above.
    This function is intended to be used with the filter() function to filter the collection.
    """

    binary_operator_handlers = {
        FilterBinaryOperator.EQUALS: FilterPredicates.filter_equals,
        FilterBinaryOperator.NOT_EQUALS: FilterPredicates.filter_not_equals,
        FilterBinaryOperator.IN: FilterPredicates.filter_in,
        FilterBinaryOperator.AND: FilterPredicates.filter_and,
        FilterBinaryOperator.OR: FilterPredicates.filter_or,
        FilterBinaryOperator.HAS: FilterPredicates.filter_has,
        FilterBinaryOperator.LESS_THAN: FilterPredicates.filter_less_than,
        FilterBinaryOperator.LESS_THAN_OR_EQUAL: FilterPredicates.filter_less_than_or_equal,
        FilterBinaryOperator.GREATER_THAN: FilterPredicates.filter_greater_than,
        FilterBinaryOperator.GREATER_THAN_OR_EQUAL: FilterPredicates.filter_greater_than_or_equal,
    }

    unary_operator_handlers = {
        FilterUnaryOperator.NOT: FilterPredicates.filter_not,
    }

    def __init__(self, filterable_classes: List[type]):
        self.filterable_classes = filterable_classes

    def visit_binary_expression(self, expression: FilterBinaryExpression) -> FilterFunction:
        operator = expression.operator
        left = expression.left.accept(self)  # If NounPhrase, returns str. If BinaryExpression, returns (item) => bool
        right = expression.right.accept(self)  # If ValueExpression, returns str. If BinaryExpression, returns (item) => bool
        return partial(self.binary_operator_handlers[operator], left=left, right=right)

    def visit_unary_expression(self, expression: FilterUnaryExpression) -> FilterFunction:
        operator = expression.operator
        inner = expression.inner.accept(self)
        return partial(self.unary_operator_handlers[operator], predicate=inner)

    def visit_value(self, expression: ValueExpression):
        return expression.value

    def visit_noun_phrases(self, expression: NounPhrasesExpression) -> str:
        noun_phrase = "".join(str(np) for np in expression.noun_phrases)
        if all(not is_field_or_property(cls, noun_phrase) for cls in self.filterable_classes):
            raise ValueError(f"{noun_phrase} is not a valid attribute to filter by.")
        return noun_phrase
