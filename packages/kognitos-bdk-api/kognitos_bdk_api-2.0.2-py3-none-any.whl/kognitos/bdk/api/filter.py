from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, time
from enum import Enum
from typing import Generic, List, TypeVar

from kognitos.bdk.api.noun_phrase import NounPhrase

T = TypeVar("T")


class FilterExpressionVisitor(ABC, Generic[T]):
    @abstractmethod
    def visit_binary_expression(self, expression: FilterBinaryExpression) -> T:
        pass

    @abstractmethod
    def visit_unary_expression(self, expression: FilterUnaryExpression) -> T:
        pass

    @abstractmethod
    def visit_value(self, expression: ValueExpression) -> T:
        pass

    @abstractmethod
    def visit_noun_phrases(self, expression: NounPhrasesExpression) -> T:
        pass


class FilterExpression(ABC):
    @abstractmethod
    def accept(self, visitor: FilterExpressionVisitor[T]) -> T:
        pass


class FilterBinaryOperator(Enum):
    AND = 0
    OR = 1
    EQUALS = 2
    NOT_EQUALS = 3
    IN = 4
    HAS = 5
    LESS_THAN = 6
    GREATER_THAN = 7
    LESS_THAN_OR_EQUAL = 8
    GREATER_THAN_OR_EQUAL = 9


class FilterUnaryOperator(Enum):
    NOT = 0


class FilterBinaryExpression(FilterExpression):
    def __init__(self, left: FilterExpression, operator: FilterBinaryOperator, right: FilterExpression):
        self.operator = operator
        self.left = left
        self.right = right

    def accept(self, visitor: FilterExpressionVisitor[T]) -> T:
        return visitor.visit_binary_expression(self)


class FilterUnaryExpression(FilterExpression):
    def __init__(self, operator: FilterUnaryOperator, inner: FilterExpression):
        self.operator = operator
        self.inner = inner

    def accept(self, visitor: FilterExpressionVisitor[T]) -> T:
        return visitor.visit_unary_expression(self)


class ValueExpression(FilterExpression):
    def __init__(self, value: str | int | bool | float | list | date | datetime | time | None):
        self.value = value

    def accept(self, visitor: FilterExpressionVisitor[T]) -> T:
        return visitor.visit_value(self)


class NounPhrasesExpression(FilterExpression):
    def __init__(self, noun_phrases: List[NounPhrase]):
        self.noun_phrases = noun_phrases

    def accept(self, visitor: FilterExpressionVisitor[T]) -> T:
        return visitor.visit_noun_phrases(self)
