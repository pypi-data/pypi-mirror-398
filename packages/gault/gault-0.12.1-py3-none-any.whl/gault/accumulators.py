from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .compilers import compile_expression, compile_expression_multi
from .interfaces import AsAlias
from .sorting import normalize_sort

if TYPE_CHECKING:
    from .sorting import SortPayload
    from .types import (
        AnyExpression,
        Context,
        MongoExpression,
        NumberExpression,
        ObjectExpression,
    )


class Accumulator(ABC, AsAlias):
    @abstractmethod
    def compile_expression(self, *, context: Context) -> MongoExpression: ...


@dataclass
class AddToSet(Accumulator):
    """Returns an array of unique expression values for each group."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {"$addToSet": compile_expression(self.input, context=context)}


@dataclass
class Avg(Accumulator):
    """Returns the average of numeric values."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {"$avg": compile_expression(self.input, context=context)}


@dataclass
class Bottom(Accumulator):
    """Returns the bottom element within a group according to the specified sort order."""

    sort_by: SortPayload
    output: AnyExpression | list[AnyExpression]

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$bottom": {
                "sortBy": normalize_sort(self.sort_by, context=context),
                "output": compile_expression(self.output, context=context),
            },
        }


@dataclass
class BottomN(Accumulator):
    """Returns an aggregation of the bottom n elements within a group, according to the specified sort order."""

    n: int
    sort_by: SortPayload
    output: AnyExpression | list[AnyExpression]

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$bottomN": {
                "n": compile_expression(self.n, context=context),
                "sortBy": normalize_sort(self.sort_by, context=context),
                "output": compile_expression(self.output, context=context),
            },
        }


@dataclass
class Count(Accumulator):
    """Returns the number of documents in a group."""

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {"$count": {}}


@dataclass
class First(Accumulator):
    """Returns the value that results from applying an expression to the first document in a group."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$first": compile_expression(self.input, context=context),
        }


@dataclass
class FirstN(Accumulator):
    """Returns an aggregation of the first n elements within a group."""

    input: NumberExpression
    n: int

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$firstN": {
                "input": compile_expression(self.input, context=context),
                "n": compile_expression(self.n, context=context),
            },
        }


@dataclass
class Last(Accumulator):
    """Returns the value that results from applying an expression to the last document in a group."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$last": compile_expression(self.input, context=context),
        }


@dataclass
class LastN(Accumulator):
    """Returns an aggregation of the last n elements within a group."""

    input: NumberExpression
    n: int

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$lastN": {
                "input": compile_expression(self.input, context=context),
                "n": compile_expression(self.n, context=context),
            },
        }


@dataclass
class Max(Accumulator):
    """Returns the maximum value."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$max": compile_expression(self.input, context=context),
        }


@dataclass
class MaxN(Accumulator):
    """Returns an aggregation of the n maximum valued elements within a group."""

    input: NumberExpression
    n: int

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$maxN": {
                "input": compile_expression(self.input, context=context),
                "n": compile_expression(self.n, context=context),
            },
        }


@dataclass
class Median(Accumulator):
    """Returns an approximation of the median value."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$median": {
                "input": compile_expression(self.input, context=context),
                "method": "approximate",
            },
        }


@dataclass
class MergeObjects(Accumulator):
    """Combines multiple documents into a single document."""

    input: ObjectExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$mergeObjects": compile_expression(self.input, context=context),
        }


@dataclass
class Min(Accumulator):
    """Returns the minimum value."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$min": compile_expression(self.input, context=context),
        }


@dataclass
class MinN(Accumulator):
    """Returns an aggregation of the n minimum valued elements within a group."""

    input: NumberExpression
    n: int

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$minN": {
                "input": compile_expression(self.input, context=context),
                "n": compile_expression(self.n, context=context),
            },
        }


@dataclass
class Percentile(Accumulator):
    """Returns an approximation of a percentile value."""

    input: NumberExpression
    p: list[float]
    """The elements represent percentages and must evaluate to numeric values in the range 0.0 to 1.0, inclusive.
    """

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$percentile": {
                "input": compile_expression(self.input, context=context),
                "p": compile_expression_multi(self.p, context=context),
                "method": "approximate",
            },
        }


@dataclass
class Push(Accumulator):
    """Returns an array of expression values for documents in each group."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$push": compile_expression(self.input, context=context),
        }


@dataclass
class StdDevPop(Accumulator):
    """Returns the population standard deviation of the input values."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$stdDevPop": compile_expression(self.input, context=context),
        }


@dataclass
class StdDevSamp(Accumulator):
    """Returns the sample standard deviation of the input values."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$stdDevSamp": compile_expression(self.input, context=context),
        }


@dataclass
class Sum(Accumulator):
    """Returns the sum of numeric values."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {"$sum": compile_expression(self.input, context=context)}


@dataclass
class Top(Accumulator):
    """Returns the top element within a group according to the specified sort order."""

    sort_by: SortPayload
    output: AnyExpression | list[AnyExpression]

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$top": {
                "sortBy": normalize_sort(self.sort_by, context=context),
                "output": compile_expression(self.output, context=context),
            },
        }


@dataclass
class TopN(Accumulator):
    """Returns an aggregation of the top n elements within a group, according to the specified sort order."""

    n: int
    sort_by: SortPayload
    output: AnyExpression | list[AnyExpression]

    def compile_expression(self, *, context: Context) -> MongoExpression:
        return {
            "$topN": {
                "n": compile_expression(self.n, context=context),
                "sortBy": normalize_sort(self.sort_by, context=context),
                "output": compile_expression(self.output, context=context),
            },
        }


def compile_accumulator(obj: Any, *, context: Context) -> MongoExpression:
    if isinstance(obj, Accumulator):
        return obj.compile_expression(context=context)
    return compile_expression(obj, context=context)
