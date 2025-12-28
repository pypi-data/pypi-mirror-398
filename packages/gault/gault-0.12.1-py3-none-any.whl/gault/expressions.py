"""Described here https://www.mongodb.com/docs/manual/reference/mql/expressions/."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast, overload
from typing import Literal as TypingLiteral

from .compilers import compile_expression, compile_expression_multi, compile_field
from .interfaces import (
    Aliased,
    AsAlias,
    AsRef,
    Assignable,
    FieldSortInterface,
    InclusionInterface,
    SubfieldInterface,
    TempFieldInterface,
)
from .interfaces import ExpressionOperator as _ExpressionOperator
from .sorting import normalize_sort
from .utils import nullfree_dict, nullfree_list, unwrap_array, unwrap_single_element

if TYPE_CHECKING:
    from collections.abc import Callable

    from .predicates import Predicate
    from .sorting import SortPayload
    from .types import (
        AnyExpression,
        ArrayExpression,
        BinaryExpression,
        BooleanExpression,
        Context,
        DateExpression,
        DateUnit,
        DayWeek,
        FieldLike,
        MongoPurExpression,
        NumberExpression,
        ObjectExpression,
        Output,
        PathLike,
        RegexExpression,
        StringExpression,
        TimestampExpression,
        Timezone,
        TimezoneExpression,
        Value,
    )


class ExpressionOperator(_ExpressionOperator, AsAlias):
    def __and__(self, other: ExpressionOperator) -> ExpressionOperator:
        return And(self, other)

    def __or__(self, other: ExpressionOperator) -> ExpressionOperator:
        return Or(self, other)

    def __invert__(self) -> ExpressionOperator:
        return Not(self)


@dataclass()
class Abs(ExpressionOperator):
    """Returns the absolute value of a number."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$abs": compile_expression(self.input, context=context),
        }


@dataclass()
class Acos(ExpressionOperator):
    """Returns the inverse cosine (arc cosine) of a value."""

    input: NumberExpression
    """any valid expression that resolves to a number between `-1` and `1`.
    """

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$acos": compile_expression(self.input, context=context),
        }


@dataclass()
class Acosh(ExpressionOperator):
    """Returns the inverse hyperbolic cosine (hyperbolic arc cosine) of a value."""

    input: NumberExpression
    """Any valid expression that resolves to a number between `1` and `+Infinity`."""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$acosh": compile_expression(self.input, context=context),
        }


class Add(ExpressionOperator):
    """Adds numbers together or adds numbers and a date.

    If one of the arguments is a date, $add treats the other arguments as milliseconds to add to the date.
    """

    inputs: list[NumberExpression]
    """any valid expressions as long as they resolve to either all numbers or to numbers and a date."""

    @overload
    def __init__(self, input: list[NumberExpression], /) -> None: ...

    @overload
    def __init__(self, *inputs: NumberExpression) -> None: ...

    def __init__(self, *inputs: Any) -> None:
        others = unwrap_array(inputs)
        if len(others) < 2:
            msg = "Multiple values is required."
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$add": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class AllElementsTrue(ExpressionOperator):
    """Evaluates an array as a set and returns `true` if no element in the array is `false`."""

    input: ArrayExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$allElementsTrue": [
                compile_expression(self.input, context=context),
            ],
        }


class And(ExpressionOperator):
    """Evaluates an array as a set and returns `true` if no element in the array is `false`."""

    inputs: list[AnyExpression]
    """any valid expressions as long as they resolve to either all numbers or to numbers and a date."""

    @overload
    def __init__(self, input: list[AnyExpression], /) -> None: ...

    @overload
    def __init__(self, *inputs: AnyExpression) -> None: ...

    def __init__(self, *inputs: AnyExpression) -> None:
        others = unwrap_array(inputs)
        if len(others) < 1:
            msg = "Multiple inputs is required."
            raise ValueError(msg)
        self.inputs = others

    def __and__(self, other: ExpressionOperator) -> ExpressionOperator:
        return And(*self.inputs, other)

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$and": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class AnyElementsTrue(ExpressionOperator):
    """Evaluates an array as a set and returns `true` if any of the elements are `true` and `false` otherwise. An empty array returns false."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$anyElementsTrue": [
                compile_expression(self.input, context=context),
            ],
        }


@dataclass
class ArrayElemAt(ExpressionOperator):
    """Returns the element at the specified array index."""

    input: ArrayExpression

    index: NumberExpression = field(kw_only=True)

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$arrayElemAt": [
                compile_expression(self.input, context=context),
                compile_expression(self.index, context=context),
            ],
        }


@dataclass
class ArrayToObject(ExpressionOperator):
    """Converts an array into a single document."""

    input: ArrayExpression
    """
    Any valid expression that resolves to:

    - An array of two-element arrays where the first element is the field name,
      and the second element is the field value
    - An array of documents that contains two fields, `k` and `v`
    """

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$arrayToObject": compile_expression(self.input, context=context),
        }


@dataclass
class Asin(ExpressionOperator):
    """Returns the inverse sine (arc sine) of a value."""

    input: NumberExpression
    """any valid expression that resolves to a number between `-1` and `1`.
    """

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$asin": compile_expression(self.input, context=context)}


@dataclass
class Asinh(ExpressionOperator):
    """Returns the inverse hyperbolic sine (hyperbolic arc sine) of a value."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$asinh": compile_expression(self.input, context=context)}


@dataclass
class Atan(ExpressionOperator):
    """Returns the inverse tangent (arc tangent) of a value."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$atan": compile_expression(self.input, context=context)}


@dataclass
class Atan2(ExpressionOperator):
    """Returns the inverse tangent (arc tangent) of y / x, where y and x are the first and second values passed to the expression respectively."""

    x: NumberExpression

    y: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$atan2": [
                compile_expression(self.x, context=context),
                compile_expression(self.y, context=context),
            ],
        }


@dataclass
class Atanh(ExpressionOperator):
    """Returns the inverse hyperbolic tangent (hyperbolic arc tangent) of a value."""

    input: NumberExpression
    """any valid expression that resolves to a number between -1 and 1
    """

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$atanh": compile_expression(self.input, context=context)}


@dataclass
class Avg(ExpressionOperator):
    """Returns the average of numeric values."""

    input: NumberExpression | list[NumberExpression]

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$avg": compile_expression_multi(self.input, context=context)}


@dataclass
class BinarySize(ExpressionOperator):
    """Returns the size of a given string or binary data value's content in bytes."""

    input: BinaryExpression | StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$binarySize": compile_expression(self.input, context=context)}


@dataclass
class BitAnd(ExpressionOperator):
    """Returns the result of a bitwise and operation on an array of int or long values."""

    inputs: list[NumberExpression]

    def __init__(self, *inputs: NumberExpression) -> None:
        others = unwrap_array(inputs)
        if len(others) < 2:
            msg = "Multiple values required."
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$bitAnd": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class BitNot(ExpressionOperator):
    """Returns the result of a bitwise `not` operation on a single int or long value."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$bitNot": compile_expression(self.input, context=context),
        }


class BitOr(ExpressionOperator):
    """Returns the result of a bitwise `or` operation on an array of int and long values."""

    inputs: list[NumberExpression]

    def __init__(self, *inputs: NumberExpression) -> None:
        others = unwrap_array(inputs)
        if len(others) < 2:
            msg = "Multiple values required."
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$bitOr": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


class BitXor(ExpressionOperator):
    """Returns the result of a bitwise `xor` (exclusive or) operation on an array of int and long values."""

    inputs: list[NumberExpression]

    def __init__(self, *inputs: NumberExpression) -> None:
        others = unwrap_array(inputs)
        if not others:
            msg = "Values is required."
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$bitXor": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class BsonSize(ExpressionOperator):
    """Returns the size in bytes of a given document (i.e. bsontype Object) when encoded as BSON."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$bsonSize": compile_expression(self.input, context=context),
        }


@dataclass
class Ceil(ExpressionOperator):
    """Returns the smallest integer greater than or equal to the specified number."""

    input: NumberExpression

    def compile_expression(self, context: Context) -> Output:
        return {"$ceil": compile_expression(self.input, context=context)}


@dataclass
class Cmp(ExpressionOperator):
    """Compares two values.

    Returns this:
    - -1 if the first value is less than the second.
    - 1 if the first value is greater than the second.
    - 0 if the two values are equivalent.
    """

    lhs: AnyExpression
    rhs: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$cmp": [
                compile_expression(self.lhs, context=context),
                compile_expression(self.rhs, context=context),
            ],
        }


class Concat(ExpressionOperator):
    """Concatenates strings and returns the concatenated string."""

    inputs: list[StringExpression]

    def __init__(self, *inputs: StringExpression) -> None:
        others = unwrap_array(inputs)
        if not others:
            msg = "Values is required."
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$concat": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


class ConcatArrays(ExpressionOperator):
    """Returns a single array that concatenates two or more arrays."""

    inputs: list[ArrayExpression]

    def __init__(self, *inputs: ArrayExpression) -> None:
        others = unwrap_array(inputs)
        if not others:
            msg = "Values is required."
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$concatArrays": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class Cond(ExpressionOperator):
    """Evaluates a boolean expression to return one of the two specified return expressions."""

    when: BooleanExpression | Predicate

    then: AnyExpression

    otherwise: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$cond": {
                "if": compile_expression(self.when, context=context),
                "then": compile_expression(self.then, context=context),
                "else": compile_expression(self.otherwise, context=context),
            },
        }


@dataclass
class Cos(ExpressionOperator):
    """Returns the cosine of a value that is measured in radians."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$cos": compile_expression(self.input, context=context)}


@dataclass
class Cosh(ExpressionOperator):
    """Returns the hyperbolic cosine of a value that is measured in radians."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$cosh": compile_expression(self.input, context=context)}


@dataclass
class DateAdd(ExpressionOperator):
    """Increments a Date() object by a specified number of time units."""

    start_date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    unit: DateUnit

    amount: NumberExpression

    timezone: TimezoneExpression | None = None
    """valid expression that resolves to a string formatted as either an
    Olson Timezone Identifier or a UTC Offset."""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dateAdd": nullfree_dict(
                {
                    "startDate": compile_expression(self.start_date, context=context),
                    "unit": compile_expression(self.unit, context=context),
                    "amount": compile_expression(self.amount, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class DateDiff(ExpressionOperator):
    """Returns the difference between two dates."""

    start_date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    end_date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    unit: DateUnit

    timezone: Timezone | None = None

    start_of_week: DayWeek | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dateDiff": nullfree_dict(
                {
                    "startDate": compile_expression(self.start_date, context=context),
                    "endDate": compile_expression(self.end_date, context=context),
                    "unit": compile_expression(self.unit, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                    "startOfWeek": compile_expression(
                        self.start_of_week,
                        context=context,
                    ),
                },
            ),
        }


@dataclass
class DateFromParts(ExpressionOperator):
    """Constructs and returns a Date object given the date's constituent properties."""

    year: NumberExpression | None = None
    iso_week_year: NumberExpression | None = None
    month: NumberExpression | None = None
    iso_week: NumberExpression | None = None
    day: NumberExpression | None = None
    iso_day_of_week: NumberExpression | None = None
    hour: NumberExpression | None = None
    minute: NumberExpression | None = None
    second: NumberExpression | None = None
    millisecond: NumberExpression | None = None
    timezone: Timezone | None = None

    def compile_expression(
        self,
        *,
        context: Context,
    ) -> Output:
        return {
            "$dateFromParts": nullfree_dict(
                {
                    "year": compile_expression(self.year, context=context),
                    "isoWeekYear": compile_expression(
                        self.iso_week_year,
                        context=context,
                    ),
                    "month": compile_expression(self.month, context=context),
                    "isoWeek": compile_expression(self.iso_week, context=context),
                    "day": compile_expression(self.day, context=context),
                    "isoDayOfWeek": compile_expression(
                        self.iso_day_of_week,
                        context=context,
                    ),
                    "hour": compile_expression(self.hour, context=context),
                    "minute": compile_expression(self.minute, context=context),
                    "second": compile_expression(self.second, context=context),
                    "millisecond": compile_expression(
                        self.millisecond,
                        context=context,
                    ),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class DateFromString(ExpressionOperator):
    """Converts a date/time string to a date object."""

    date_string: DateExpression
    """The date/time string to convert to a date object."""

    format: str | None = None
    """The date format specification of the dateString..
    """

    timezone: Timezone | None = None
    """valid expression that resolves to a string formatted as either an
    Olson Timezone Identifier or a UTC Offset."""

    on_error: AnyExpression | None = None
    """any valid expression.
    """

    on_null: AnyExpression | None = None
    """any valid expression.
    """

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dateFromString": nullfree_dict(
                {
                    "dateString": compile_expression(self.date_string, context=context),
                    "format": compile_expression(self.format, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                    "onError": compile_expression(self.on_error, context=context),
                    "onNull": compile_expression(self.on_null, context=context),
                },
            ),
        }


@dataclass
class DateSubtract(ExpressionOperator):
    """Decrements a Date() object by a specified number of time units."""

    start_date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    unit: DateUnit

    amount: NumberExpression

    timezone: Timezone | None = None
    """valid expression that resolves to a string formatted as either an
    Olson Timezone Identifier or a UTC Offset."""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dateSubtract": nullfree_dict(
                {
                    "startDate": compile_expression(self.start_date, context=context),
                    "unit": compile_expression(self.unit, context=context),
                    "amount": compile_expression(self.amount, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class DateToParts(ExpressionOperator):
    """Returns a document that contains the constituent parts of a given BSON Date value as individual properties."""

    date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    timezone: Timezone | None = None
    """valid expression that resolves to a string formatted as either an
    Olson Timezone Identifier or a UTC Offset."""

    iso8601: bool | None = None
    """modifies the output document to use ISO week date fields"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dateToParts": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                    "iso8601": compile_expression(self.iso8601, context=context),
                },
            ),
        }


@dataclass
class DateToString(ExpressionOperator):
    """Converts a date object to a string according to a user-specified format."""

    date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    format: str | None = None
    """modifies the output document to use ISO week date fields"""

    timezone: Timezone | None = None
    """valid expression that resolves to a string formatted as either an
    Olson Timezone Identifier or a UTC Offset."""

    on_null: AnyExpression | None = None
    """modifies the output document to use ISO week date fields"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dateToString": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "format": compile_expression(self.format, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                    "onNull": compile_expression(self.on_null, context=context),
                },
            ),
        }


@dataclass
class DateTrunc(ExpressionOperator):
    """Truncates a date."""

    date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    unit: DateUnit

    bin_size: NumberExpression | None = None
    """an expression that must resolve to a positive non-zero number"""

    timezone: Timezone | None = None
    """valid expression that resolves to a string formatted as either an
    Olson Timezone Identifier or a UTC Offset."""

    start_of_week: DayWeek | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dateTrunc": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "unit": compile_expression(self.unit, context=context),
                    "binSize": compile_expression(self.bin_size, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                    "startOfWeek": compile_expression(
                        self.start_of_week,
                        context=context,
                    ),
                },
            ),
        }


@dataclass
class DayOfMonth(ExpressionOperator):
    """Returns the day of the month for a date as a number between 1 and 31."""

    date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dayOfMonth": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class DayOfWeek(ExpressionOperator):
    """Returns the day of the week for a date as a number between 1 (Sunday) and 7 (Saturday)."""

    date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dayOfWeek": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class DayOfYear(ExpressionOperator):
    """Returns the day of the year for a date as a number between 1 and 366."""

    date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$dayOfYear": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class DegreesToRadians(ExpressionOperator):
    """Converts an input value measured in degrees to radians."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$degreesToRadians": compile_expression(self.input, context=context)}


@dataclass
class Divide(ExpressionOperator):
    """Divides one number by another and returns the result."""

    dividende: NumberExpression
    """any valid expression as long as they resolve to numbers"""

    divisor: NumberExpression
    """any valid expression as long as they resolve to numbers"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$divide": [
                compile_expression(self.dividende, context=context),
                compile_expression(self.divisor, context=context),
            ],
        }


@dataclass
class Eq(ExpressionOperator):
    """Compares two values.

    It returns:
    - true when the values are equivalent.
    - false when the values are not equivalent.
    """

    lhs: AnyExpression
    rhs: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$eq": [
                compile_expression(self.lhs, context=context),
                compile_expression(self.rhs, context=context),
            ],
        }


@dataclass
class Exp(ExpressionOperator):
    """Raises Euler's number to the specified exponent and returns the result."""

    exponent: NumberExpression
    """any valid expression as long as it resolves to a number"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$exp": compile_expression(self.exponent, context=context),
        }


@dataclass
class Filter(ExpressionOperator):
    """Selects a subset of an array to return based on the specified condition."""

    input: ArrayExpression
    cond: BooleanExpression | Callable[[ExpressionsInterface, Context], Output]
    var: PathLike | None = field(default=None, kw_only=True)
    limit: int | None = field(default=None, kw_only=True)

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        match self.var:
            case str() as name:
                var = Var(name)
            case Var() as ref:
                var = ref
            case _:
                var = Var("this")

        if self.cond and callable(self.cond):
            cond = self.cond(var, context)
        else:
            cond = self.cond

        return {
            "$filter": nullfree_dict(
                {
                    "input": compile_expression(self.input, context=context),
                    "as": compile_field(var, context=context) if self.var else None,
                    "cond": compile_expression(cond, context=context),
                    "limit": compile_expression(self.limit, context=context),
                },
            ),
        }


@dataclass
class Floor(ExpressionOperator):
    """Returns the largest integer less than or equal to the specified number."""

    input: NumberExpression

    def compile_expression(self, context: Context) -> MongoPurExpression:
        return {"$floor": compile_expression(self.input, context=context)}


@dataclass
class GetField(ExpressionOperator):
    """Returns the value of a specified field from a document."""

    input: ObjectExpression
    """valid expression that contains the field for which you want to return a value.
    input must resolve to an object, missing, null, or undefined."""

    field: StringExpression
    """any valid expression that resolves to a string."""

    def compile_expression(self, context: Context) -> Output:
        return {
            "$getField": nullfree_dict(
                {
                    "field": compile_expression(self.field, context=context),
                    "input": compile_expression(self.input, context=context),
                },
            ),
        }


@dataclass
class Gt(ExpressionOperator):
    """Compares two values.

    It returns:
    - `true` when the first value is greater than the second value
    - `false` when the first value is less than or equal to the second value
    """

    lhs: AnyExpression
    rhs: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$gt": [
                compile_expression(self.lhs, context=context),
                compile_expression(self.rhs, context=context),
            ],
        }


@dataclass
class Gte(ExpressionOperator):
    """Compares two values.

    It returns:
    - `true` when the first value is greater than or equal to the second value
    - `false` when the first value is less than or equal to the second value
    """

    lhs: AnyExpression
    rhs: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$gte": [
                compile_expression(self.lhs, context=context),
                compile_expression(self.rhs, context=context),
            ],
        }


@dataclass
class Hour(ExpressionOperator):
    """Returns the hour portion of a date as a number between 0 and 23."""

    date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$hour": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


class IfNull(ExpressionOperator):
    """The $ifNull expression evaluates input expressions for null values.

    It returns:
    - The first non-null input expression value found.
    - A replacement expression value if all input expressions evaluate to null.
    """

    inputs: list[AnyExpression]

    def __init__(self, *inputs: AnyExpression) -> None:
        others = unwrap_array(inputs)
        if len(others) < 1:
            msg = "Multiple inputs is required."
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$ifNull": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class In(ExpressionOperator):
    """Returns a boolean indicating whether a specified value is in an array."""

    lhs: AnyExpression
    """Any valid expression expression."""

    rhs: ArrayExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$in": [
                compile_expression(self.lhs, context=context),
                compile_expression(self.rhs, context=context),
            ],
        }


@dataclass
class IndexOfArray(ExpressionOperator):
    """Searches an array for an occurrence of a specified value and returns the array index of the first occurrence."""

    input: ArrayExpression

    search: AnyExpression

    start: NumberExpression | None = None
    """any valid expression that resolves to a non-negative integral number."""

    end: NumberExpression | None = None
    """any valid expression that resolves to a non-negative integral number."""

    def __post_init__(self) -> None:
        if self.end:
            self.start = self.start or 0

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$indexOfArray": nullfree_list(
                [
                    compile_expression(self.input, context=context),
                    compile_expression(self.search, context=context),
                    compile_expression(self.start, context=context),
                    compile_expression(self.end, context=context),
                ],
            ),
        }


@dataclass
class IndexOfBytes(ExpressionOperator):
    """Searches a string for an occurrence of a substring and returns the UTF-8 byte index (zero-based) of the first occurrence."""

    input: StringExpression
    """any valid expression as long as it resolves to a string"""

    search: StringExpression
    """any valid expression as long as it resolves to a string"""

    start: NumberExpression | None = None
    """any valid expression that resolves to a non-negative integral number."""

    end: NumberExpression | None = None
    """any valid expression that resolves to a non-negative integral number."""

    def __post_init__(self) -> None:
        if self.end:
            self.start = self.start or 0

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$indexOfBytes": nullfree_list(
                [
                    compile_expression(self.input, context=context),
                    compile_expression(self.search, context=context),
                    compile_expression(self.start, context=context),
                    compile_expression(self.end, context=context),
                ],
            ),
        }


@dataclass
class IndexOfCP(ExpressionOperator):
    """Searches a string for an occurrence of a substring and returns the UTF-8 code point index (zero-based) of the first occurrence."""

    input: StringExpression
    """any valid expression as long as it resolves to a string"""

    search: StringExpression
    """any valid expression as long as it resolves to a string"""

    start: NumberExpression | None = None
    """any valid expression that resolves to a non-negative integral number."""

    end: NumberExpression | None = None
    """any valid expression that resolves to a non-negative integral number."""

    def __post_init__(self) -> None:
        if self.end:
            self.start = self.start or 0

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$indexOfCP": nullfree_list(
                [
                    compile_expression(self.input, context=context),
                    compile_expression(self.search, context=context),
                    compile_expression(self.start, context=context),
                    compile_expression(self.end, context=context),
                ],
            ),
        }


@dataclass
class IsArray(ExpressionOperator):
    """Determines if the operand is an array."""

    input: AnyExpression
    """any valid expression."""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$isArray": [compile_expression(self.input, context=context)],
        }


@dataclass
class IsNumber(ExpressionOperator):
    """Determines if the operand is a number."""

    input: AnyExpression
    """any valid expression."""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$isNumber": compile_expression(self.input, context=context),
        }


@dataclass
class IsoDayOfWeek(ExpressionOperator):
    """Returns the weekday number in ISO 8601 format, ranging from 1 (for Monday) to 7 (for Sunday)."""

    date: DateExpression

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$isoDayOfWeek": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class IsoWeek(ExpressionOperator):
    """Returns the week number in ISO 8601 format, ranging from 1 to 53."""

    date: DateExpression

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$isoWeek": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class IsoWeekYear(ExpressionOperator):
    """Returns the year number in ISO 8601 format."""

    date: DateExpression

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$isoWeekYear": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class Let(ExpressionOperator):
    """Binds variables for use in the specified expression, and returns the result of the expression."""

    variables: Mapping[FieldLike, AnyExpression]
    """Assignment block for the variables accessible in the in expression."""

    into: AnyExpression = field(kw_only=True)
    """The expression to evaluate."""

    @overload
    def __init__(
        self,
        variables: Mapping[FieldLike, AnyExpression],
        /,
        into: AnyExpression,
    ) -> None: ...

    @overload
    def __init__(self, *variables: Aliased, into: AnyExpression) -> None: ...

    def __init__(self, *variables: Any, into: AnyExpression) -> None:  # type: ignore[misc]
        spec: Any = {}
        if len(variables) == 1 and isinstance(variables[0], Mapping):
            spec |= variables[0]
        else:
            for aliased in variables:
                assert isinstance(aliased, Aliased)  # noqa: S101
                spec[aliased.ref] = aliased.value
        self.variables = spec
        self.into = into

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$let": {
                "vars": {
                    compile_field(key, context=context): compile_expression(
                        val,
                        context=context,
                    )
                    for key, val in self.variables.items()
                },
                "in": compile_expression(self.into, context=context),
            },
        }


@dataclass
class Literal(ExpressionOperator):
    """Returns a value without parsing."""

    input: Value

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$literal": self.input,
        }


@dataclass
class Ln(ExpressionOperator):
    """Calculates the natural logarithm ln (i.e log e) of a number and returns the result as a double."""

    input: NumberExpression
    """Any valid expression as long as it resolves to a non-negative number"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$ln": compile_expression(self.input, context=context)}


@dataclass
class Log(ExpressionOperator):
    """Calculates the log of a number in the specified base and returns the result as a double."""

    input: NumberExpression
    """any valid expression as long as it resolves to a non-negative number"""

    base: NumberExpression
    """any valid expression as long as it resolves to a positive number greater than 1"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$log": [
                compile_expression(self.input, context=context),
                compile_expression(self.base, context=context),
            ],
        }


@dataclass
class Log10(ExpressionOperator):
    """Calculates the log base 10 of a number and returns the result as a double."""

    input: NumberExpression
    """any valid expression as long as it resolves to a non-negative number"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$log10": compile_expression(self.input, context=context),
        }


@dataclass
class Lt(ExpressionOperator):
    """Compares two values.

    It returns:
    - `true` when the first value less than than the second value
    - `false` when the first value is greater than or equivalent to the second value
    """

    lhs: AnyExpression
    rhs: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$lt": [
                compile_expression(self.lhs, context=context),
                compile_expression(self.rhs, context=context),
            ],
        }


@dataclass
class Lte(ExpressionOperator):
    """Compares two values.

    It returns:
    - `true` when the first value is less than or equivalent or equal to the second value
    - `false` when the first value is greater than the second value
    """

    lhs: NumberExpression
    rhs: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$lte": [
                compile_expression(self.lhs, context=context),
                compile_expression(self.rhs, context=context),
            ],
        }


@dataclass
class Ltrim(ExpressionOperator):
    """Removes whitespace characters, including null, or the specified characters from the beginning of a string."""

    input: StringExpression
    """any valid expression that resolves to a string"""

    chars: StringExpression
    """any valid expression that resolves to a string"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$ltrim": {
                "input": compile_expression(self.input, context=context),
                "chars": compile_expression(self.chars, context=context),
            },
        }


@dataclass
class Map(ExpressionOperator):
    """Applies an expression to each item in an array and returns an array with the applied results."""

    input: ArrayExpression
    """any valid expression that resolves to an array"""

    into: AnyExpression
    """An expression that is applied to each element of the input array"""

    var: PathLike | None = field(default=None, kw_only=True)
    """A name for the variable that represents each individual element of the input array. If no name is specified, the variable name defaults to this"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        match self.var:
            case str() as name:
                var = Var(name)
            case Var() as ref:
                var = ref
            case _:
                var = Var("this")

        if self.into and callable(self.into):
            cond = self.into(var, context)
        else:
            cond = self.into

        return {
            "$map": nullfree_dict(
                {
                    "input": compile_expression(self.input, context=context),
                    "as": compile_field(var, context=context) if self.var else None,
                    "in": compile_expression(cond, context=context),
                },
            )
        }


@dataclass
class Max(ExpressionOperator):
    """Returns the maximum value."""

    input: PathLike | list[NumberExpression]

    @overload
    def __init__(self, input: PathLike, /) -> None: ...

    @overload
    def __init__(self, input: list[NumberExpression], /) -> None: ...

    @overload
    def __init__(self, *inputs: NumberExpression) -> None: ...

    def __init__(self, *inputs: Any) -> None:
        self.input = unwrap_single_element(inputs)

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {"$max": compile_expression_multi(self.input, context=context)}


@dataclass
class MaxN(ExpressionOperator):
    """Returns the n largest values in an array."""

    input: ArrayExpression
    """An expression that resolves to the array"""

    n: NumberExpression
    """An expression that resolves to a positive integer"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$maxN": {
                "input": compile_expression(self.input, context=context),
                "n": compile_expression(self.n, context=context),
            },
        }


@dataclass
class Median(ExpressionOperator):
    """Returns an approximation of the median value."""

    input: PathLike | list[NumberExpression]

    def compile(self, *, context: Context) -> Any:
        input = compile_expression_multi(self.input, context=context)
        return {
            "$median": {
                "input": input,
                "method": "approximate",
            },
        }


@dataclass
class MergeObjects(ExpressionOperator):
    """Combines multiple documents into a single document."""

    documents: list[ObjectExpression]

    @overload
    def __init__(self, documents: list[ObjectExpression], /) -> None: ...

    @overload
    def __init__(self, *documents: ObjectExpression) -> None: ...

    def __init__(self, *documents: Any) -> None:
        self.documents = unwrap_array(documents)

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        documents = [
            compile_expression(document, context=context) for document in self.documents
        ]
        return {
            "$mergeObjects": documents,
        }


@dataclass
class Meta(ExpressionOperator):
    """Returns the metadata associated with a document, e.g. "textScore" when performing text search."""

    keyword: TypingLiteral["textScore", "indexKey"]

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$meta": self.keyword,
        }


@dataclass
class Millisecond(ExpressionOperator):
    """Returns the millisecond portion of a date as an integer between 0 and 999."""

    date: DateExpression

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$millisecond": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class Min(ExpressionOperator):
    """Returns the minimum value."""

    input: PathLike | list[NumberExpression]

    @overload
    def __init__(self, input: PathLike, /) -> None: ...

    @overload
    def __init__(self, inputs: list[NumberExpression], /) -> None: ...

    @overload
    def __init__(self, *inputs: NumberExpression) -> None: ...

    def __init__(self, *inputs: Any) -> None:
        self.input = unwrap_single_element(inputs)

    def compile_expression(self, *, context: Context) -> Any:
        return {"$min": compile_expression_multi(self.input, context=context)}


@dataclass
class MinN(ExpressionOperator):
    """Returns the n smallest values in an array."""

    input: ArrayExpression
    """An expression that resolves to the array"""

    n: NumberExpression
    """An expression that resolves to a positive integer"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$minN": {
                "input": compile_expression(self.input, context=context),
                "n": compile_expression(self.n, context=context),
            },
        }


@dataclass
class Minute(ExpressionOperator):
    """Returns the minute portion of a date as a number between 0 and 59."""

    date: DateExpression

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$minute": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class Mod(ExpressionOperator):
    """Divides one number by another and returns the remainder."""

    value1: NumberExpression
    value2: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$mod": [
                compile_expression(self.value1, context=context),
                compile_expression(self.value2, context=context),
            ],
        }


@dataclass
class Month(ExpressionOperator):
    """Returns the month of a date as a number between 1 and 12."""

    date: DateExpression

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$month": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class Multiply(ExpressionOperator):
    """Multiplies numbers together and returns the result."""

    inputs: list[NumberExpression]

    def __init__(self, *inputs: NumberExpression) -> None:
        others = unwrap_array(inputs)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$multiply": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class Ne(ExpressionOperator):
    """Compares two values.

    It returns:
    - true when the values are not equivalent.
    - false when the values are equivalent.
    """

    lhs: AnyExpression
    rhs: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$ne": [
                compile_expression(self.lhs, context=context),
                compile_expression(self.rhs, context=context),
            ],
        }


@dataclass
class Not(ExpressionOperator):
    """Evaluates a boolean and returns the opposite boolean value."""

    input: AnyExpression

    def __invert__(self) -> ExpressionOperator:
        match self.input:
            case Raw():
                return self.input
            case _:
                return Raw(self.input)

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$not": [
                compile_expression(self.input, context=context),
            ],
        }


@dataclass
class Raw(ExpressionOperator):
    """Evaluates a boolean and returns the opposite boolean value."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return compile_expression(self.input, context=context)  # type: ignore[return-value]


@dataclass
class ObjectToArray(ExpressionOperator):
    """Converts a document to an array."""

    input: ObjectExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$objectToArray": compile_expression(self.input, context=context),
        }


class Or(ExpressionOperator):
    """Evaluates one or more expressions and returns true if any of the expressions are true."""

    inputs: list[AnyExpression]

    def __init__(self, *inputs: AnyExpression) -> None:
        others = unwrap_array(inputs)
        if not others:
            msg = "Values is required."
            raise ValueError(msg)
        self.inputs = others

    def __or__(self, other: ExpressionOperator) -> ExpressionOperator:
        return Or(*self.inputs, other)

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$or": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class Percentile(ExpressionOperator):
    """Returns the maximum value."""

    input: PathLike | list[NumberExpression]
    p: list[NumberExpression]

    def compile_expression(self, *, context: Context) -> Any:
        return {
            "$percentile": {
                "input": compile_expression_multi(self.input, context=context),
                "p": compile_expression_multi(self.p, context=context),
                "method": "approximate",
            }
        }


@dataclass
class Pow(ExpressionOperator):
    """Raises a number to the specified exponent and returns the result."""

    input: NumberExpression
    exponent: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$pow": [
                compile_expression(self.input, context=context),
                compile_expression(self.exponent, context=context),
            ],
        }


@dataclass
class RadiansToDegrees(ExpressionOperator):
    """Converts an input value measured in radians to degrees."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$radiansToDegrees": compile_expression(self.input, context=context),
        }


@dataclass
class Rand(ExpressionOperator):
    """Returns a random float between 0 and 1 each time it is called."""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$rand": {},
        }


@dataclass
class Range(ExpressionOperator):
    """Returns an array whose elements are a generated sequence of numbers."""

    start: NumberExpression
    end: NumberExpression
    step: NumberExpression = 1

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$range": [
                compile_expression(self.start, context=context),
                compile_expression(self.end, context=context),
                compile_expression(self.step, context=context),
            ],
        }


@dataclass
class Reduce(ExpressionOperator):
    """Applies an expression to each element in an array and combines them into a single value."""

    input: ArrayExpression
    initial_value: Value
    into: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$reduce": {
                "input": compile_expression(self.input, context=context),
                "initialValue": compile_expression(self.initial_value, context=context),
                "in": compile_expression(self.into, context=context),
            },
        }


@dataclass
class RegexFind(ExpressionOperator):
    """Provides regular expression (regex) pattern matching capability in aggregation expressions."""

    input: StringExpression
    regex: RegexExpression
    options: StringExpression | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$regexFind": nullfree_dict(
                {
                    "input": compile_expression(self.input, context=context),
                    "regex": compile_expression(self.regex, context=context),
                    "options": compile_expression(self.options, context=context),
                },
            ),
        }


@dataclass
class RegexFindAll(ExpressionOperator):
    """Provides regular expression (regex) pattern matching capability in aggregation expressions."""

    input: StringExpression
    regex: RegexExpression
    options: StringExpression | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$regexFindAll": nullfree_dict(
                {
                    "input": compile_expression(self.input, context=context),
                    "regex": compile_expression(self.regex, context=context),
                    "options": compile_expression(self.options, context=context),
                },
            ),
        }


@dataclass
class RegexMatch(ExpressionOperator):
    """Performs a regular expression (regex) pattern matching."""

    input: StringExpression
    regex: RegexExpression
    options: StringExpression | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$regexMatch": nullfree_dict(
                {
                    "input": compile_expression(self.input, context=context),
                    "regex": compile_expression(self.regex, context=context),
                    "options": compile_expression(self.options, context=context),
                },
            ),
        }


@dataclass
class ReplaceOne(ExpressionOperator):
    """Replaces the first instance of a search string in an input string with a replacement string."""

    input: StringExpression
    find: StringExpression
    replacement: StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$replaceOne": {
                "input": compile_expression(self.input, context=context),
                "find": compile_expression(self.find, context=context),
                "replacement": compile_expression(self.replacement, context=context),
            },
        }


@dataclass
class ReplaceAll(ExpressionOperator):
    """Replaces all instances of a search string in an input string with a replacement string."""

    input: StringExpression
    find: StringExpression
    replacement: StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$replaceAll": {
                "input": compile_expression(self.input, context=context),
                "find": compile_expression(self.find, context=context),
                "replacement": compile_expression(self.replacement, context=context),
            },
        }


@dataclass
class ReverseArray(ExpressionOperator):
    """Accepts an array expression as an argument and returns an array with the elements in reverse order."""

    input: ArrayExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$reverseArray": compile_expression(self.input, context=context),
        }


@dataclass
class Round(ExpressionOperator):
    """Rounds a number to a whole integer or to a specified decimal place."""

    input: NumberExpression
    place: NumberExpression = 0

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$round": [
                compile_expression(self.input, context=context),
                compile_expression(self.place, context=context),
            ],
        }


@dataclass
class Rtrim(ExpressionOperator):
    """Removes whitespace characters, including null, or the specified characters from the end of a string."""

    input: StringExpression
    """any valid expression that resolves to a string"""

    chars: StringExpression
    """any valid expression that resolves to a string"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$rtrim": {
                "input": compile_expression(self.input, context=context),
                "chars": compile_expression(self.chars, context=context),
            },
        }


@dataclass
class SampleRate(ExpressionOperator):
    """Matches a random selection of input documents."""

    number: NumberExpression
    """any valid expression that resolves to a string"""

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$sampleRate": compile_expression(self.number, context=context),
        }


@dataclass
class Second(ExpressionOperator):
    """Returns the second portion of a date as a number between 0 and 59, but can be 60 to account for leap seconds."""

    date: DateExpression
    """any expression that resolves to a Date, a Timestamp, or an ObjectID."""

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$second": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class SetDifference(ExpressionOperator):
    """Takes two sets and returns an array containing the elements that only exist in the first set."""

    inputs1: ArrayExpression

    inputs2: ArrayExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$setDifference": [
                compile_expression(self.inputs1, context=context),
                compile_expression(self.inputs2, context=context),
            ],
        }


@dataclass
class SetEquals(ExpressionOperator):
    """Compares two or more arrays and returns true if they have the same distinct elements and false otherwise."""

    inputs: list[ArrayExpression]

    def __init__(self, *inputs: ArrayExpression) -> None:
        others = unwrap_array(inputs)
        if len(others) < 2:
            msg = "Requires at least 2 sets"
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$setEquals": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class SetField(ExpressionOperator):
    """Adds, updates, or removes a specified field in a document."""

    input: ObjectExpression
    field: StringExpression
    value: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$setField": {
                "input": compile_expression(self.input, context=context),
                "field": compile_expression(self.field, context=context),
                "value": compile_expression(self.value, context=context),
            },
        }


@dataclass
class SetIntersection(ExpressionOperator):
    """Takes two or more arrays and returns an array that contains the elements that appear in every input array."""

    inputs: list[ArrayExpression]

    def __init__(self, *inputs: ArrayExpression) -> None:
        others = unwrap_array(inputs)
        if len(others) < 2:
            msg = "Requires at least 2 sets"
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$setIntersection": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class SetIsSubset(ExpressionOperator):
    """Takes two arrays and returns true when the first array is a subset of the second."""

    input1: ArrayExpression
    input2: ArrayExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$setIsSubset": [
                compile_expression(self.input1, context=context),
                compile_expression(self.input2, context=context),
            ],
        }


@dataclass
class SetUnion(ExpressionOperator):
    """Takes two or more arrays and returns a single array containing the unique elements that appear in any input array."""

    inputs: list[ArrayExpression]

    def __init__(self, *inputs: ArrayExpression) -> None:
        others = unwrap_array(inputs)
        if len(others) < 2:
            msg = "Requires at least 2 sets"
            raise ValueError(msg)
        self.inputs = others

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$setUnion": [
                compile_expression(input, context=context) for input in self.inputs
            ],
        }


@dataclass
class Sigmoid(ExpressionOperator):
    """Performs the sigmoid function, which calculates the percentile of a number in the normal distribution with standard deviation 1."""

    input: NumberExpression
    on_null: AnyExpression | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$sigmoid": {
                "input": compile_expression(self.input, context=context),
            }
            | nullfree_dict(
                {
                    "onNull": compile_expression(self.on_null, context=context),
                }
            ),
        }


@dataclass
class Size(ExpressionOperator):
    """Counts and returns the total number of items in an array."""

    input: ArrayExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$size": compile_expression(self.input, context=context),
        }


@dataclass
class Sin(ExpressionOperator):
    """Returns the sine of a value that is measured in radians."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$sin": compile_expression(self.input, context=context),
        }


@dataclass
class Sinh(ExpressionOperator):
    """Returns the hyperbolic sine of a value that is measured in radians."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$sinh": compile_expression(self.input, context=context),
        }


@dataclass
class Slice(ExpressionOperator):
    """Returns a subset of an array."""

    input: ArrayExpression
    n: NumberExpression = field(kw_only=True)
    position: NumberExpression | None = field(default=None, kw_only=True)

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$slice": nullfree_list(
                [
                    compile_expression(self.input, context=context),
                    compile_expression(self.position, context=context),
                    compile_expression(self.n, context=context),
                ],
            ),
        }


@dataclass
class SortArray(ExpressionOperator):
    """Sorts an array based on its elements."""

    input: ArrayExpression
    sort_by: SortPayload

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$sortArray": {
                "input": compile_expression(self.input, context=context),
                "sortBy": normalize_sort(self.sort_by, context=context),
            },
        }


@dataclass
class Split(ExpressionOperator):
    """Divides a string into an array of substrings based on a delimiter. $split removes the delimiter and returns the resulting substrings as elements of an array."""

    input: StringExpression
    delimiter: StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$split": [
                compile_expression(self.input, context=context),
                compile_expression(self.delimiter, context=context),
            ],
        }


@dataclass
class Sqrt(ExpressionOperator):
    """Calculates the square root of a positive number and returns the result as a double."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$sqrt": compile_expression(self.input, context=context),
        }


@dataclass
class StdDevPop(ExpressionOperator):
    """Calculates the population standard deviation of the input values."""

    input: PathLike | list[NumberExpression]

    def compile_expression(self, *, context: Context) -> Any:
        return {
            "$stdDevPop": compile_expression_multi(self.input, context=context),
        }


@dataclass
class StdDevSamp(ExpressionOperator):
    """Calculates the sample standard deviation of the input values."""

    input: PathLike | list[NumberExpression]

    def compile_expression(self, *, context: Context) -> Any:
        return {
            "$stdDevSamp": compile_expression_multi(self.input, context=context),
        }


@dataclass
class StrCaseCmp(ExpressionOperator):
    """Performs case-insensitive comparison of two strings."""

    input1: StringExpression
    input2: StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$strcasecmp": [
                compile_expression(self.input1, context=context),
                compile_expression(self.input2, context=context),
            ],
        }


@dataclass
class StrLenBytes(ExpressionOperator):
    """Returns the number of UTF-8 encoded bytes in the specified string."""

    input: StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$strLenBytes": compile_expression(self.input, context=context),
        }


@dataclass
class StrLenCP(ExpressionOperator):
    """Returns the number of UTF-8 code points in the specified string."""

    input: StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$strLenCP": compile_expression(self.input, context=context),
        }


@dataclass
class SubStrBytes(ExpressionOperator):
    """Returns the substring of a string."""

    input: StringExpression
    start: NumberExpression
    length: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$substrBytes": [
                compile_expression(self.input, context=context),
                compile_expression(self.start, context=context),
                compile_expression(self.length, context=context),
            ],
        }


@dataclass
class SubStrCP(ExpressionOperator):
    """Returns the substring of a string."""

    input: StringExpression
    start: NumberExpression
    length: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$substrCP": [
                compile_expression(self.input, context=context),
                compile_expression(self.start, context=context),
                compile_expression(self.length, context=context),
            ],
        }


@dataclass
class Subtract(ExpressionOperator):
    """Subtracts two numbers to return the difference, or two dates to return the difference in milliseconds, or a date and a number in milliseconds to return the resulting date."""

    input1: NumberExpression | DateExpression
    input2: NumberExpression | DateExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$subtract": [
                compile_expression(self.input1, context=context),
                compile_expression(self.input2, context=context),
            ],
        }


@dataclass
class Sum(ExpressionOperator):
    """Calculates and returns the collective sum of numeric values."""

    input: PathLike | list[NumberExpression]

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$sum": compile_expression_multi(self.input, context=context),
        }


@dataclass
class Switch(ExpressionOperator):
    """Evaluates a series of case expressions."""

    branches: list[tuple[BooleanExpression, AnyExpression]]
    default: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$switch": {
                "branches": [
                    {
                        "case": compile_expression(case, context=context),
                        "then": compile_expression(then, context=context),
                    }
                    for case, then in self.branches
                ],
                "default": compile_expression(self.default, context=context),
            },
        }


@dataclass
class Tan(ExpressionOperator):
    """Returns the tangent of a value that is measured in radians."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$tan": compile_expression(self.input, context=context),
        }


@dataclass
class Tanh(ExpressionOperator):
    """Returns the hyperbolic tangent of a value that is measured in radians."""

    input: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$tanh": compile_expression(self.input, context=context),
        }


@dataclass
class ToBool(ExpressionOperator):
    """Converts a value to a boolean."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toBool": compile_expression(self.input, context=context),
        }


@dataclass
class ToDate(ExpressionOperator):
    """Converts a value to a date."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toDate": compile_expression(self.input, context=context),
        }


@dataclass
class ToDecimal(ExpressionOperator):
    """Converts a value to a decimal."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toDecimal": compile_expression(self.input, context=context),
        }


@dataclass
class ToDouble(ExpressionOperator):
    """Converts a value to a double."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toDouble": compile_expression(self.input, context=context),
        }


@dataclass
class ToHashedIndexKey(ExpressionOperator):
    """Computes and returns the hash value of the input expression."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toHashedIndexKey": compile_expression(self.input, context=context),
        }


@dataclass
class ToInt(ExpressionOperator):
    """Converts a value to an integer."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toInt": compile_expression(self.input, context=context),
        }


@dataclass
class ToLong(ExpressionOperator):
    """Converts a value to a long."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toLong": compile_expression(self.input, context=context),
        }


@dataclass
class ToObjectId(ExpressionOperator):
    """Converts a value to an ObjectId."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toObjectId": compile_expression(self.input, context=context),
        }


@dataclass
class ToString(ExpressionOperator):
    """Converts a value to a string."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toString": compile_expression(self.input, context=context),
        }


@dataclass
class ToLower(ExpressionOperator):
    """Converts a string to lowercase, returning the result."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toLower": compile_expression(self.input, context=context),
        }


@dataclass
class ToUpper(ExpressionOperator):
    """Converts a string to uppercase, returning the result."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toUpper": compile_expression(self.input, context=context),
        }


@dataclass
class ToUUID(ExpressionOperator):
    """Converts a string value to a UUID."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$toUUID": compile_expression(self.input, context=context),
        }


@dataclass
class TsIncrement(ExpressionOperator):
    """Returns the incrementing ordinal from a timestamp as a long."""

    input: TimestampExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$tsIncrement": compile_expression(self.input, context=context),
        }


@dataclass
class TsSecond(ExpressionOperator):
    """Returns the seconds from a timestamp as a long."""

    input: TimestampExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$tsSecond": compile_expression(self.input, context=context),
        }


@dataclass
class Trim(ExpressionOperator):
    """Removes whitespace characters, including null, or the specified characters from the beginning and end of a string."""

    input: StringExpression
    chars: StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$trim": {
                "input": compile_expression(self.input, context=context),
                "chars": compile_expression(self.chars, context=context),
            },
        }


@dataclass
class Trunc(ExpressionOperator):
    """Truncates a number to a whole integer or to a specified decimal place."""

    input: NumberExpression
    place: NumberExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$trunc": [
                compile_expression(self.input, context=context),
                compile_expression(self.place, context=context),
            ],
        }


@dataclass
class Type(ExpressionOperator):
    """Returns a string that specifies the BSON type of the argument."""

    input: AnyExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$type": compile_expression(self.input, context=context),
        }


@dataclass
class UnsetField(ExpressionOperator):
    """Removes a specified field in a document."""

    input: ObjectExpression
    field: StringExpression

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$unsetField": {
                "input": compile_expression(self.input, context=context),
                "field": compile_expression(self.field, context=context),
            },
        }


@dataclass
class Week(ExpressionOperator):
    """Returns the week of the year for a date as a number between 0 and 53."""

    date: DateExpression

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$week": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class Year(ExpressionOperator):
    """Returns the year portion of a date."""

    date: DateExpression

    timezone: Timezone | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$year": nullfree_dict(
                {
                    "date": compile_expression(self.date, context=context),
                    "timezone": compile_expression(self.timezone, context=context),
                },
            ),
        }


@dataclass
class Zip(ExpressionOperator):
    """Transposes an array of input arrays."""

    inputs: list[ArrayExpression]
    use_longest_length: bool | None = None
    defaults: list[Value] | None = None

    def compile_expression(self, *, context: Context) -> MongoPurExpression:
        return {
            "$zip": {
                "inputs": [
                    compile_expression(input, context=context) for input in self.inputs
                ],
            }
            | nullfree_dict(
                {
                    "useLongestLength": self.use_longest_length,
                    "defaults": compile_expression(self.defaults, context=context),
                }
            ),
        }


class ExpressionsInterface:
    def abs(self) -> Abs:
        return Abs(cast("Any", self))

    def acos(self) -> Acos:
        return Acos(cast("Any", self))

    def acosh(self) -> Acosh:
        return Acosh(cast("Any", self))

    def add(self, *inputs: NumberExpression) -> Add:
        return Add(cast("Any", self), *inputs)

    def all_elements_true(self, *inputs: AnyExpression) -> AllElementsTrue:
        return AllElementsTrue(cast("Any", self))

    def any_elements_true(self, *inputs: AnyExpression) -> AnyElementsTrue:
        return AnyElementsTrue(self)

    def asin(self) -> Asin:
        return Asin(cast("Any", self))

    def asinh(self) -> Asinh:
        return Asinh(cast("Any", self))

    def atan(self) -> Atan:
        return Atan(cast("Any", self))

    def atan2(self, other: NumberExpression, /) -> Atan2:
        return Atan2(cast("Any", self), other)

    def atanh(self) -> Atanh:
        return Atanh(cast("Any", self))

    def avg(self, *others: NumberExpression) -> Avg:
        if elements := unwrap_array(others):
            input: Any = [self, *elements]
        else:
            input = self
        return Avg(input=cast("Any", input))

    def binary_size(self) -> BinarySize:
        return BinarySize(cast("Any", self))

    def bit_and(self, *inputs: NumberExpression) -> BitAnd:
        return BitAnd(cast("Any", self), *inputs)

    def bit_not(self) -> BitNot:
        return BitNot(cast("Any", self))

    def bit_or(self, *inputs: NumberExpression) -> BitOr:
        return BitOr(cast("Any", self), *inputs)

    def bit_xor(self, *inputs: NumberExpression) -> BitXor:
        return BitXor(cast("Any", self), *inputs)

    def bson_size(self) -> BsonSize:
        return BsonSize(self)

    def ceil(self) -> Ceil:
        return Ceil(cast("Any", self))

    def cmp(self, other: AnyExpression, /) -> Cmp:
        return Cmp(cast("Any", self), other)

    def concat(self, *inputs: StringExpression) -> Concat:
        return Concat(cast("Any", self), *inputs)

    def cos(self) -> Cos:
        return Cos(cast("Any", self))

    def cosh(self) -> Cosh:
        return Cosh(cast("Any", self))

    def date_add(
        self,
        *,
        unit: DateUnit,
        amount: NumberExpression,
        timezone: TimezoneExpression | None = None,
    ) -> DateAdd:
        return DateAdd(
            cast("Any", self),
            unit=unit,
            amount=amount,
            timezone=timezone,
        )

    def date_diff(
        self,
        end_date: DateExpression,
        *,
        unit: DateUnit,
        timezone: Timezone | None = None,
        start_of_week: DayWeek | None = None,
    ) -> DateDiff:
        return DateDiff(
            start_date=cast("Any", self),
            end_date=end_date,
            unit=unit,
            start_of_week=start_of_week,
            timezone=timezone,
        )

    def date_from_string(
        self,
        *,
        format: str | None = None,
        timezone: Timezone | None = None,
        on_error: AnyExpression | None = None,
        on_null: AnyExpression | None = None,
    ) -> DateFromString:
        return DateFromString(
            cast("Any", self),
            format=format,
            timezone=timezone,
            on_error=on_error,
            on_null=on_null,
        )

    def date_subtract(
        self,
        *,
        unit: DateUnit,
        amount: NumberExpression,
        timezone: Timezone | None = None,
    ) -> DateSubtract:
        return DateSubtract(
            cast("Any", self),
            unit=unit,
            amount=amount,
            timezone=timezone,
        )

    def date_to_parts(
        self,
        *,
        timezone: Timezone | None = None,
    ) -> DateToParts:
        return DateToParts(
            cast("Any", self),
            timezone=timezone,
        )

    def date_to_string(
        self,
        *,
        format: str | None = None,
        timezone: Timezone | None = None,
        on_null: AnyExpression | None = None,
    ) -> DateToString:
        return DateToString(
            cast("Any", self),
            format=format,
            timezone=timezone,
            on_null=on_null,
        )

    def date_trunc(
        self,
        *,
        unit: DateUnit,
        bin_size: NumberExpression | None = None,
        timezone: Timezone | None = None,
        start_of_week: DayWeek | None = None,
    ) -> DateTrunc:
        return DateTrunc(
            cast("Any", self),
            unit=unit,
            bin_size=bin_size,
            timezone=timezone,
            start_of_week=start_of_week,
        )

    def day_of_month(
        self,
        *,
        timezone: Timezone | None = None,
    ) -> DayOfMonth:
        return DayOfMonth(
            cast("Any", self),
            timezone=timezone,
        )

    def day_of_week(
        self,
        *,
        timezone: Timezone | None = None,
    ) -> DayOfWeek:
        return DayOfWeek(
            cast("Any", self),
            timezone=timezone,
        )

    def day_of_year(
        self,
        *,
        timezone: Timezone | None = None,
    ) -> DayOfYear:
        return DayOfYear(
            cast("Any", self),
            timezone=timezone,
        )

    def degrees_to_radians(self) -> DegreesToRadians:
        return DegreesToRadians(cast("Any", self))

    def eq(self, other: AnyExpression) -> Eq:
        return Eq(cast("Any", self), other)

    def exp(self) -> Exp:
        return Exp(cast("Any", self))

    def filter(
        self,
        cond: BooleanExpression
        | Callable[[ExpressionsInterface, Context], BooleanExpression],
        *,
        var: PathLike | None = None,
        limit: int | None = None,
    ) -> Filter:
        return Filter(cast("Any", self), var=var, cond=cond, limit=limit)

    def floor(self) -> Floor:
        return Floor(cast("Any", self))

    def get_field(self, field: str) -> GetField:
        return GetField(cast("Any", self), field=field)

    def gt(self, other: AnyExpression) -> Gt:
        return Gt(cast("Any", self), other)

    def gte(self, other: AnyExpression) -> Gte:
        return Gte(cast("Any", self), other)

    def hour(self) -> Hour:
        return Hour(cast("Any", self))

    def in_(self, array: ArrayExpression, /) -> IfNull:
        return IfNull(self, array)

    def index_of_array(
        self,
        search: StringExpression,
        *,
        start: NumberExpression | None = None,
        end: NumberExpression | None = None,
    ) -> IndexOfArray:
        return IndexOfArray(
            cast("Any", self),
            search=search,
            start=start,
            end=end,
        )

    def index_of_bytes(
        self,
        search: StringExpression,
        *,
        start: NumberExpression | None = None,
        end: NumberExpression | None = None,
    ) -> IndexOfBytes:
        return IndexOfBytes(
            cast("Any", self),
            search=search,
            start=start,
            end=end,
        )

    def index_of_cp(
        self,
        search: StringExpression,
        *,
        start: NumberExpression | None = None,
        end: NumberExpression | None = None,
    ) -> IndexOfCP:
        return IndexOfCP(
            cast("Any", self),
            search=search,
            start=start,
            end=end,
        )

    def is_array(self) -> IsArray:
        return IsArray(cast("Any", self))

    def is_number(self) -> IsNumber:
        return IsNumber(cast("Any", self))

    def iso_day_of_week(self, *, timezone: Timezone | None = None) -> IsoDayOfWeek:
        return IsoDayOfWeek(cast("Any", self), timezone=timezone)

    def iso_week_year(self, *, timezone: Timezone | None = None) -> IsoWeekYear:
        return IsoWeekYear(cast("Any", self), timezone=timezone)

    def ln(self) -> Ln:
        return Ln(cast("Any", self))

    def log(self, base: NumberExpression, /) -> Log:
        return Log(cast("Any", self), base)

    def log10(self) -> Log10:
        return Log10(cast("Any", self))

    def trim(self, chars: StringExpression) -> Trim:
        return Trim(cast("Any", self), chars=chars)

    def ltrim(self, chars: StringExpression) -> Ltrim:
        return Ltrim(cast("Any", self), chars=chars)

    def rtrim(self, chars: StringExpression) -> Rtrim:
        return Rtrim(cast("Any", self), chars=chars)

    def lt(self, other: AnyExpression) -> Lt:
        return Lt(cast("Any", self), other)

    def lte(self, other: AnyExpression) -> Lte:
        return Lte(cast("Any", self), other)

    def map(
        self,
        into: ArrayExpression,
        *,
        var: PathLike | None = None,
    ) -> Map:
        return Map(cast("Any", self), var=var, into=into)

    def max(self, *others: NumberExpression) -> Max:
        if elements := unwrap_array(others):
            input: Any = [self, *elements]
        else:
            input = self
        return Max(cast("Any", input))

    def max_n(self, n: NumberExpression, /) -> MaxN:
        return MaxN(cast("Any", self), n=n)

    def min(self, *others: NumberExpression) -> Min:
        if elements := unwrap_array(others):
            input: Any = [self, *elements]
        else:
            input = self
        return Min(cast("Any", input))

    def min_n(self, n: NumberExpression, /) -> MinN:
        return MinN(cast("Any", self), n=n)

    def millisecond(self) -> Millisecond:
        return Millisecond(cast("Any", self))

    def minute(self) -> Minute:
        return Minute(cast("Any", self))

    def mod(self, other: NumberExpression, /) -> Mod:
        return Mod(cast("Any", self), other)

    def month(self) -> Month:
        return Month(cast("Any", self))

    def multiply(self, *inputs: NumberExpression) -> Multiply:
        return Multiply(cast("Any", self), *inputs)

    def ne(self, other: AnyExpression, /) -> Ne:
        return Ne(cast("Any", self), other)

    def not_(self) -> Not:
        return Not(cast("Any", self))

    def object_to_array(self) -> ObjectToArray:
        return ObjectToArray(cast("Any", self))

    def pow(self, exponent: NumberExpression, /) -> Pow:
        return Pow(cast("Any", self), exponent)

    def radians_to_degrees(self) -> RadiansToDegrees:
        return RadiansToDegrees(cast("Any", self))

    def reduce(
        self,
        into: ArrayExpression,
        *,
        initial_value: Value,
    ) -> Reduce:
        return Reduce(cast("Any", self), into=into, initial_value=initial_value)

    def regex_find(
        self,
        regex: RegexExpression,
        *,
        options: StringExpression | None = None,
    ) -> RegexFind:
        return RegexFind(cast("Any", self), regex=regex, options=options)

    def regex_find_all(
        self,
        regex: RegexExpression,
        *,
        options: StringExpression | None = None,
    ) -> RegexFindAll:
        return RegexFindAll(cast("Any", self), regex=regex, options=options)

    def regex_match(
        self,
        regex: RegexExpression,
        *,
        options: StringExpression | None = None,
    ) -> RegexMatch:
        return RegexMatch(cast("Any", self), regex=regex, options=options)

    def replace_one(
        self,
        find: StringExpression,
        replacement: StringExpression,
    ) -> ReplaceOne:
        return ReplaceOne(
            cast("Any", self),
            find=find,
            replacement=replacement,
        )

    def replace_all(
        self,
        find: StringExpression,
        replacement: StringExpression,
    ) -> ReplaceAll:
        return ReplaceAll(
            cast("Any", self),
            find=find,
            replacement=replacement,
        )

    def reverse_array(self) -> ReverseArray:
        return ReverseArray(cast("Any", self))

    def round(self, place: NumberExpression = 0, /) -> Round:
        return Round(cast("Any", self), place=place)

    def sample_rate(self) -> SampleRate:
        return SampleRate(cast("Any", self))

    def second(self) -> Second:
        return Second(cast("Any", self))

    def set_difference(self, other: ArrayExpression, /) -> SetDifference:
        return SetDifference(cast("Any", self), other)

    def set_equals(self, other: ArrayExpression, /) -> SetEquals:
        return SetEquals(cast("Any", self), other)

    def set_intersection(self, other: ArrayExpression, /) -> SetIntersection:
        return SetIntersection(cast("Any", self), other)

    def set_is_subset(self, other: ArrayExpression, /) -> SetIsSubset:
        return SetIsSubset(cast("Any", self), other)

    def set_union(self, other: ArrayExpression, /) -> SetUnion:
        return SetUnion(cast("Any", self), other)

    def set_field(
        self,
        *,
        field: StringExpression,
        value: Value,
    ) -> SetField:
        return SetField(cast("Any", self), field=field, value=value)

    def sigmoid(
        self,
        *,
        on_null: AnyExpression | None = None,
    ) -> Sigmoid:
        return Sigmoid(cast("Any", self), on_null=on_null)

    def size(self) -> Size:
        return Size(cast("Any", self))

    def sin(self) -> Sin:
        return Sin(cast("Any", self))

    def sinh(self) -> Sinh:
        return Sinh(cast("Any", self))

    def sort_array(self, sort_by: SortPayload, /) -> SortArray:
        return SortArray(cast("Any", self), sort_by=sort_by)

    def split(self, delimiter: StringExpression, /) -> Split:
        return Split(cast("Any", self), delimiter=delimiter)

    def sqrt(self) -> Sqrt:
        return Sqrt(cast("Any", self))

    def str_case_cmp(self, other: StringExpression, /) -> StrCaseCmp:
        return StrCaseCmp(cast("Any", self), other)

    def str_len_bytes(self) -> StrLenBytes:
        return StrLenBytes(cast("Any", self))

    def str_len_cp(self) -> StrLenCP:
        return StrLenCP(cast("Any", self))

    def sub_str_bytes(
        self,
        start: NumberExpression,
        length: NumberExpression,
    ) -> SubStrBytes:
        return SubStrBytes(cast("Any", self), start=start, length=length)

    def subtract(
        self,
        other: NumberExpression,
    ) -> Subtract:
        return Subtract(cast("Any", self), other)

    def tan(self) -> Tan:
        return Tan(cast("Any", self))

    def tanh(self) -> Tanh:
        return Tanh(cast("Any", self))

    def to_bool(self) -> ToBool:
        return ToBool(cast("Any", self))

    def to_date(self) -> ToDate:
        return ToDate(cast("Any", self))

    def to_decimal(self) -> ToDecimal:
        return ToDecimal(cast("Any", self))

    def to_double(self) -> ToDouble:
        return ToDouble(cast("Any", self))

    def to_hashed_index_key(self) -> ToHashedIndexKey:
        return ToHashedIndexKey(cast("Any", self))

    def to_int(self) -> ToInt:
        return ToInt(cast("Any", self))

    def to_long(self) -> ToLong:
        return ToLong(cast("Any", self))

    def to_object_id(self) -> ToObjectId:
        return ToObjectId(cast("Any", self))

    def to_string(self) -> ToString:
        return ToString(cast("Any", self))

    def to_lower(self) -> ToLower:
        return ToLower(cast("Any", self))

    def to_upper(self) -> ToUpper:
        return ToUpper(cast("Any", self))

    def to_uuid(self) -> ToUUID:
        return ToUUID(cast("Any", self))

    def ts_increment(self) -> TsIncrement:
        return TsIncrement(cast("Any", self))

    def ts_second(self) -> TsSecond:
        return TsSecond(cast("Any", self))

    def trunc(self, place: NumberExpression) -> Trunc:
        return Trunc(cast("Any", self), place=place)

    def type(self) -> Type:
        return Type(cast("Any", self))

    def unset_field(self, field: StringExpression) -> UnsetField:
        return UnsetField(cast("Any", self), field=field)

    def week(self) -> Week:
        return Week(cast("Any", self))

    def year(self) -> Year:
        return Year(cast("Any", self))

    def zip(
        self,
        *inputs: list[ArrayExpression],
        use_longest_length: bool | None = None,
        defaults: list[Value] | None = None,
    ) -> Zip:
        return Zip(
            [cast("Any", self), *inputs],
            use_longest_length=use_longest_length,
            defaults=defaults,
        )


@dataclass(frozen=True)
class Var(
    AsRef,
    AsAlias,
    ExpressionsInterface,
    FieldSortInterface,
    SubfieldInterface,
    TempFieldInterface,
    InclusionInterface,
    Assignable,
):
    name: str

    def compile_field(self, *, context: Context) -> str:
        return self.name

    def compile_expression(self, *, context: Context) -> str:
        return "$$" + self.name
