"""aggregators.

TODO: ensure all example here are implemented here https://www.mongodb.com/docs/manual/reference/operator/aggregation/setWindowFields/#mongodb-pipeline-pipe.-setWindowFields
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .compilers import compile_expression

if TYPE_CHECKING:
    from .types import Context, DateUnit, Input, Output


class WindowOperator(ABC):
    """Described here https://www.mongodb.com/docs/manual/reference/mql/expressions/."""

    @abstractmethod
    def compile_expression(self, *, context: Context) -> Output:
        raise NotImplementedError


@dataclass
class AddToSet(WindowOperator):
    """Returns an array of unique expression values for each group."""

    expr: Input

    def compile_expression(self, *, context: Context) -> Output:
        return {"$addToSet": compile_expression(self.expr, context=context)}


@dataclass
class Avg(WindowOperator):
    """Returns the average of numeric values."""

    expr: Input

    def compile_expression(self, *, context: Context) -> Output:
        return {"$avg": compile_expression(self.expr, context=context)}


@dataclass
class CovariancePop(WindowOperator):
    """Returns the population covariance of two numeric expressions that are evaluated using documents in the `$setWindowFields` stage window."""

    value1: Input
    """any valid expression that resolves to a number, measured in radians"""

    value2: Input
    """any valid expression that resolves to a number, measured in radians"""

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$covariancePop": [
                compile_expression(self.value1, context=context),
                compile_expression(self.value2, context=context),
            ],
        }


@dataclass
class CovarianceSamp(WindowOperator):
    """Returns the sample covariance of two numeric expressions that are evaluated using documents in the `$setWindowFields` stage window."""

    value1: Input
    """any valid expression that resolves to a number, measured in radians"""

    value2: Input
    """any valid expression that resolves to a number, measured in radians"""

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$covarianceSamp": [
                compile_expression(self.value1, context=context),
                compile_expression(self.value2, context=context),
            ],
        }


@dataclass
class DenseRank(WindowOperator):
    """Returns the document position (known as the rank) relative to other documents in the $setWindowFields stage partition."""

    def compile_expression(self, *, context: Context) -> Output:
        return {"$denseRank": {}}


@dataclass
class Derivative(WindowOperator):
    """Returns the average rate of change within the specified window."""

    input: Input
    """any valid expression that resolves to a number.
    """

    unit: DateUnit

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$derivative": {
                "input": compile_expression(self.input, context=context),
                "unit": compile_expression(self.unit, context=context),
            },
        }


@dataclass
class DocumentNumber(WindowOperator):
    """Returns the position of a document (known as the document number) in the $setWindowFields stage partition."""

    def compile_expression(self, *, context: Context) -> Output:
        return {"$documentNumber": {}}


@dataclass
class ExpMovingAvg(WindowOperator):
    """Returns the exponential moving average of numeric expressions applied to documents in a partition defined in the $setWindowFields stage."""

    input: Input
    """any valid expression as long as it resolves to a number"""

    n: Input
    """any valid expression as long as it resolves to a number"""

    alpha: Input
    """any valid expression as long as it resolves to a number"""

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$expMovingAvg": {
                "input": compile_expression(self.input, context=context),
                "N": compile_expression(self.n, context=context),
                "alpha": compile_expression(self.alpha, context=context),
            },
        }


@dataclass
class Integral(WindowOperator):
    """Returns the approximation of the area under a curve."""

    input: Input
    """an expression that returns a number."""

    unit: DateUnit

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$integral": {
                "input": compile_expression(self.input, context=context),
                "unit": compile_expression(self.unit, context=context),
            },
        }


@dataclass
class LinearFill(WindowOperator):
    """Fills null and missing fields in a window using linear interpolation based on surrounding field values."""

    input: Input
    """The expression to evaluate."""

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$linearFill": compile_expression(self.input, context=context),
        }


@dataclass
class Locf(WindowOperator):
    """Last observation carried forward."""

    input: Input
    """Any valid expression"""

    def compile_expression(self, *, context: Context) -> Output:
        return {"$locf": compile_expression(self.input, context=context)}


@dataclass
class Median(WindowOperator):
    """Returns an approximation of the median value."""

    input: Input

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$median": {
                "input": compile_expression(self.input, context=context),
                "method": "approximate",
            },
        }


@dataclass
class MinMaxScaler(WindowOperator):
    """Normalizes a numeric expression within a window of values."""

    input: Input
    """An expression that resolves to the array"""

    min: Input = 0
    """An expression that resolves to a positive integer"""

    max: Input = 1
    """An expression that resolves to a positive integer"""

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$minMaxScaler": {
                "input": compile_expression(self.input, context=context),
                "min": compile_expression(self.min, context=context),
                "max": compile_expression(self.max, context=context),
            },
        }


@dataclass
class Rank(WindowOperator):
    """Returns the document position (known as the rank) relative to other documents in the $setWindowFields stage partition."""

    def compile_expression(self, *, context: Context) -> Input:
        return {
            "$rank": {},
        }


@dataclass
class Shift(WindowOperator):
    """Returns the value from an expression applied to a document in a specified position relative to the current document in the $setWindowFields stage partition."""

    output: Input
    by: Input
    default: Input

    def compile_expression(self, *, context: Context) -> Output:
        return {
            "$shift": {
                "output": compile_expression(self.output, context=context),
                "by": compile_expression(self.by, context=context),
                "default": compile_expression(self.default, context=context),
            },
        }
