"""Described here https://www.mongodb.com/docs/manual/reference/mql/query-predicates/."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar, cast, overload

from . import expressions
from .compilers import compile_expression, compile_field, compile_query
from .geo import compile_geo
from .interfaces import (
    AsRef,
    Assignable,
    ExpressionOperator,
    FieldSortInterface,
    InclusionInterface,
    QueryPredicate,
    SubfieldInterface,
    TempFieldInterface,
)
from .utils import nullfree_dict, unwrap_array

if TYPE_CHECKING:
    from .geo import Geo, GeoJSON
    from .types import (
        AnyExpression,
        Array,
        Binary,
        Boolean,
        Context,
        MongoQuery,
        Number,
        Object,
        Output,
        PathLike,
        String,
        Value,
    )

    P = TypeVar("P", bound="Predicate")


class ConditionInterface(ABC):
    @abstractmethod
    def build_condition(self, op: Operator, /) -> Predicate: ...

    def all(self, *values: Value | ElemMatch) -> Predicate:
        op = All(*values)
        return self.build_condition(op)

    def elem_match(self, *predicates: Predicate | Operator) -> Predicate:
        op = ElemMatch(*predicates)
        return self.build_condition(op)

    def size(self, count: Number, /) -> Predicate:
        op = Size(count)
        return self.build_condition(op)

    def bits_all_clear(self, bits: Number | Binary | list[Number], /) -> Predicate:
        op = BitsAllClear(bits)
        return self.build_condition(op)

    def bits_any_clear(self, bits: Number | Binary | list[Number], /) -> Predicate:
        op = BitsAnyClear(bits)
        return self.build_condition(op)

    def bits_all_set(self, bits: Number | Binary | list[Number], /) -> Predicate:
        op = BitsAllSet(bits)
        return self.build_condition(op)

    def bits_any_set(self, bits: Number | Binary | list[Number], /) -> Predicate:
        op = BitsAnySet(bits)
        return self.build_condition(op)

    def eq(self, value: Value, /) -> Predicate:
        op = Eq(value)
        return self.build_condition(op)

    def gt(self, value: PathLike | Value, /) -> Predicate:
        op = Gt(value)
        return self.build_condition(op)

    def gte(self, value: PathLike | Value, /) -> Predicate:
        op = Gte(value)
        return self.build_condition(op)

    def in_(self, *values: Value) -> Predicate:
        op = In(*values)
        return self.build_condition(op)

    def lt(self, value: PathLike | Value, /) -> Predicate:
        op = Lt(value)
        return self.build_condition(op)

    def lte(self, value: PathLike | Value, /) -> Predicate:
        op = Lte(value)
        return self.build_condition(op)

    def ne(self, value: AsRef | Value, /) -> Predicate:
        op = Ne(value)
        return self.build_condition(op)

    def nin(self, *values: Value) -> Predicate:
        op = Nin(*values)
        return self.build_condition(op)

    def exists(self, value: Boolean, /) -> Predicate:
        op = Exists(value)
        return self.build_condition(op)

    def type(self, *types: String | Number) -> Predicate:
        op = Type(*types)
        return self.build_condition(op)

    def geo_intersects(self, value: GeoJSON, /) -> Predicate:
        op = GeoIntersects(value)
        return self.build_condition(op)

    def geo_within(self, value: GeoJSON, /) -> Predicate:
        op = GeoWithin(value)
        return self.build_condition(op)

    def near(
        self,
        value: GeoJSON,
        /,
        min_distance: Number | None = None,
        max_distance: Number | None = None,
    ) -> Predicate:
        op = Near(
            value,
            min_distance=min_distance,
            max_distance=max_distance,
        )
        return self.build_condition(op)

    def near_sphere(
        self,
        value: GeoJSON,
        /,
        min_distance: Number | None = None,
        max_distance: Number | None = None,
    ) -> Predicate:
        op = NearSphere(
            value,
            min_distance=min_distance,
            max_distance=max_distance,
        )
        return self.build_condition(op)

    def mod(self, divisor: Number, remainder: Number) -> Predicate:
        op = Mod(divisor, remainder)
        return self.build_condition(op)

    def regex(self, regex: String, *, options: String | None = None) -> Predicate:
        op = Regex(regex, options=options)
        return self.build_condition(op)


class NotInterface:
    @property
    def not_(self) -> NotProxy:
        return NotProxy(cast("AsRef", self))


@dataclass(frozen=True)
class Field(
    AsRef,
    ConditionInterface,
    FieldSortInterface,
    TempFieldInterface,
    SubfieldInterface,
    NotInterface,
    InclusionInterface,
    Assignable,
):
    name: str

    def compile_field(self, *, context: Context) -> str:
        return self.name

    def compile_expression(self, *, context: Context) -> str:
        return "$" + self.name

    def build_condition(self, op: Operator, /) -> Predicate:
        return Condition(self, op=op)


class AsExpression(ABC):
    @abstractmethod
    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        raise NotImplementedError


class Predicate(QueryPredicate):
    def __and__(self, other: Predicate) -> And:
        return And([self, other])

    def __or__(self, other: Predicate) -> Or:
        return Or([self, other])


class NoOp(QueryPredicate, ExpressionOperator):
    def __and__(self, other: P) -> P:
        return other

    def __or__(self, other: P) -> P:
        return other

    def compile_query(self, *, context: Context) -> MongoQuery:
        return {}

    def compile_expression(self, context: Context) -> Output:
        return {}


def Query() -> Predicate:  # noqa: N802
    return NoOp()  # type: ignore[return-value]


class Operator(QueryPredicate):
    def __invert__(self) -> Operator:
        return Not(self)


@dataclass
class Raw(Predicate):
    query: MongoQuery

    def compile_query(self, context: Context) -> MongoQuery:
        return self.query


@dataclass
class Condition(Predicate, ExpressionOperator):
    field: str | AsRef
    op: Operator

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            compile_field(self.field, context=context): compile_query(
                self.op,
                context=context,
            ),
        }

    def compile_expression(self, context: Context) -> Output:
        if isinstance(self.op, AsExpression):
            expression = self.op.as_expression(self.field, context=context)
        else:
            raise NotImplementedError
        return compile_expression(expression, context=context)


@dataclass
class And(Predicate, ExpressionOperator):
    """Selects the documents that satisfy all the expressions."""

    predicates: list[Predicate | MongoQuery]

    @overload
    def __init__(self, predicate: list[Predicate | MongoQuery], /) -> None: ...

    @overload
    def __init__(self, *predicates: Predicate | MongoQuery) -> None: ...

    def __init__(self, *predicates: Any) -> None:
        self.predicates = unwrap_array(predicates)

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$and": [
                compile_query(predicate, context=context)
                for predicate in self.predicates
            ],
        }

    def compile_expression(self, context: Context) -> Output:
        return {
            "$and": [
                compile_expression(predicate, context=context)
                for predicate in self.predicates
            ],
        }

    def __and__(self, other: Predicate) -> And:
        return And([*self.predicates, other])


@dataclass
class Nor(Predicate):
    """Selects the documents that fail all the query predicates in the array."""

    predicates: list[Predicate | MongoQuery]

    @overload
    def __init__(self, predicate: list[Predicate | MongoQuery], /) -> None: ...

    @overload
    def __init__(self, *predicates: Predicate | MongoQuery) -> None: ...

    def __init__(self, *predicates: Any) -> None:
        self.predicates = unwrap_array(predicates)

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$nor": [
                compile_query(predicate, context=context)
                for predicate in self.predicates
            ],
        }

    def compile_expression(self, context: Context) -> Output:
        return expressions.Not(
            {
                "$or": [
                    compile_expression(predicate, context=context)
                    for predicate in self.predicates
                ],
            },
        ).compile_expression(context=context)

    def __invert__(self) -> Or:
        return Or(self.predicates)


@dataclass
class Not(Operator):
    """Selects the documents that do not match the operator."""

    operator: Operator | Value

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$not": compile_query(self.operator, context=context),
        }

    def compile_expression(self, context: Context) -> Output:
        return Not(
            compile_expression(self.operator, context=context),
        ).compile_expression(context=context)


@dataclass
class Or(Predicate, ExpressionOperator):
    """Selects the documents that satisfy at least one of the predicates."""

    predicates: list[Predicate | MongoQuery]

    @overload
    def __init__(self, predicate: list[Predicate | MongoQuery], /) -> None: ...

    @overload
    def __init__(self, *predicates: Predicate | MongoQuery) -> None: ...

    def __init__(self, *predicates: Any) -> None:
        self.predicates = unwrap_array(predicates)

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$or": [
                compile_query(predicate, context=context)
                for predicate in self.predicates
            ],
        }

    def compile_expression(self, context: Context) -> Output:
        return {
            "$or": [
                compile_expression(predicate, context=context)
                for predicate in self.predicates
            ],
        }

    def __or__(self, other: Predicate) -> Or:
        return Or([*self.predicates, other])

    def __invert__(self) -> Nor:
        return Nor(self.predicates)


@dataclass
class All(Operator):
    """Selects the documents where the value of a field matches all specified values."""

    values: list[Value | ElemMatch]

    @overload
    def __init__(self, value: list[Value | ElemMatch], /) -> None: ...

    @overload
    def __init__(self, *values: Value | ElemMatch) -> None: ...

    def __init__(self, *values: Any) -> None:
        self.values = unwrap_array(values)

    def compile_query(self, context: Context) -> MongoQuery:
        values = []
        value: Any
        for val in self.values:
            match val:
                case Operator():
                    value = compile_query(val, context=context)
                case {"$elemMatch": _}:
                    value = compile_query(val, context=context)
                case _:
                    value = val
            values.append(value)
        return {
            "$all": values,
        }


@dataclass
class ElemMatch(Operator):
    """Selects the documents where the value of a field matches all specified values."""

    predicates: list[Predicate | Operator | Object]

    @overload
    def __init__(self, predicate: list[Predicate | Operator | Object], /) -> None: ...

    @overload
    def __init__(self, *predicates: Predicate | Operator | Object) -> None: ...

    def __init__(self, *predicates: Any) -> None:
        self.predicates = unwrap_array(predicates)

    def compile_query(self, context: Context) -> MongoQuery:
        query: Any = {}
        for predicate in self.predicates:
            query |= compile_query(predicate, context=context)

        return {
            "$elemMatch": query,
        }


@dataclass
class Size(Operator, AsExpression):
    """Matches any array with the number of elements specified by the argument."""

    count: Number

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$size": self.count,
        }

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.Eq(expressions.Size(field), self.count)


@dataclass
class BitsAllClear(Operator):
    """Matches documents where all of the bit positions given by the query are clear (i.e. 0) in field."""

    bits: Number | Binary | list[Number]

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$bitsAllClear": self.bits,
        }


@dataclass
class BitsAllSet(Operator):
    """Matches documents where all of the bit positions given by the query are set (i.e. 1) in field."""

    bits: Number | Binary | list[Number]

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$bitsAllSet": self.bits,
        }


@dataclass
class BitsAnyClear(Operator):
    """Matches documents where any of the bit positions given by the query are clear (i.e. 0) in field."""

    bits: Number | Binary | list[Number]

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$bitsAnyClear": self.bits,
        }


@dataclass
class BitsAnySet(Operator):
    """Matches documents where any of the bit positions given by the query are set (i.e. 1) in field."""

    bits: Number | Binary | list[Number]

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$bitsAnySet": self.bits,
        }


@dataclass
class Eq(Operator, AsExpression):
    """Matches documents where the value of a field equals the specified value."""

    value: Value

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$eq": self.value,
        }

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.Eq(field, self.value)


@dataclass
class Gt(Operator):
    """Matches documents where the value of the specified field is greater than the specified value."""

    value: PathLike | Value

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$gt": self.value,
        }

    def as_expression(
        self,
        field: Field,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.Gt(field, self.value)


@dataclass
class Gte(Operator, AsExpression):
    """Matches documents where the value of the specified field is greater than or equal to a specified value."""

    value: PathLike | Value

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$gte": self.value,
        }

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.Gte(field, self.value)


@dataclass
class In(Operator, AsExpression):
    """Selects the documents where the value of a field equals any value in the specified array."""

    values: list[Value]

    @overload
    def __init__(self, value: list[Value], /) -> None: ...

    @overload
    def __init__(self, *values: Value) -> None: ...

    def __init__(self, *values: Any) -> None:
        self.values = unwrap_array(values)

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$in": self.values,
        }

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.In(field, self.values)


@dataclass
class Lt(Operator, AsExpression):
    """Matches documents where the value of the specified field is less than the specified value."""

    value: PathLike | Value

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$lt": self.value,
        }

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.Lt(field, self.value)


@dataclass
class Lte(Operator, AsExpression):
    """Matches documents where the value of the specified field is less than or equal to a specified value."""

    value: PathLike | Value

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$lte": self.value,
        }

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.Lte(field, self.value)


@dataclass
class Ne(Operator, AsExpression):
    """Matches documents where the value of a specified field is not equal to the specified value."""

    value: AsRef | Value

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$ne": compile_expression(self.value, context=context),
        }

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.Ne(field, self.value)


@dataclass
class Nin(Operator, AsExpression):
    """Selects the documents where the specified field value is not in the specified array or the specified field does not exist."""

    values: list[Value]

    @overload
    def __init__(self, value: list[Value], /) -> None: ...

    @overload
    def __init__(self, *values: Value) -> None: ...

    def __init__(self, *values: Any) -> None:
        self.values = unwrap_array(values)

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$nin": self.values,
        }

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.Not(
            expressions.In(field, self.values),
        )


@dataclass
class Exists(Operator):
    """Selects the documents where the specified field value is not in the specified array or the specified field does not exist."""

    value: Boolean

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$exists": self.value,
        }


@dataclass
class Type(Operator):
    """Selects documents where the value of the field is an instance of the specified BSON type(s)."""

    types: Array[String | Number]

    @overload
    def __init__(self, type: Array[String | Number], /) -> None: ...

    @overload
    def __init__(self, *types: String | Number) -> None: ...

    def __init__(self, *types: Any) -> None:
        self.types = unwrap_array(types)

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$type": self.types,
        }


@dataclass
class GeoIntersects(Operator):
    """Selects documents whose geospatial data intersects with a specified GeoJSON object; i.e. where the intersection of the data and the specified object is non-empty."""

    value: GeoJSON

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$geoIntersects": compile_geo(self.value, context=context),
        }


@dataclass
class GeoWithin(Operator):
    """Selects documents with geospatial data that exists entirely within a specified shape."""

    value: Geo

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$geoWithin": compile_geo(self.value, context=context),
        }


@dataclass
class Near(Operator):
    """Specifies a point for which a geospatial query returns the documents from nearest to farthest."""

    value: Geo
    min_distance: Number | None = None
    max_distance: Number | None = None

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$near": compile_geo(self.value, context=context),
        } | nullfree_dict(
            {
                "$minDistance": self.min_distance,
                "$maxDistance": self.max_distance,
            },
        )


@dataclass
class NearSphere(Operator):
    """Specifies a point for which a geospatial query returns the documents from nearest to farthest."""

    value: Geo
    min_distance: Number | None = None
    max_distance: Number | None = None

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$nearSphere": compile_geo(self.value, context=context),
        } | nullfree_dict(
            {
                "$minDistance": self.min_distance,
                "$maxDistance": self.max_distance,
            },
        )


@dataclass
class Expr(Operator):
    """Allows the use of expressions within a query predicate."""

    expression: AnyExpression

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$expr": compile_expression(self.expression, context=context),
        }


@dataclass
class JsonSchema(Operator):
    """Matches documents that satisfy the specified JSON Schema."""

    schema: Any

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$jsonSchema": compile_expression(self.schema, context=context),
        }


@dataclass
class Mod(Operator):
    """Matches documents that satisfy the specified JSON Schema."""

    divisor: Number
    remainder: Number

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$mod": [
                compile_expression(self.divisor, context=context),
                compile_expression(self.remainder, context=context),
            ],
        }


@dataclass
class Regex(Operator, AsExpression):
    """Matches documents that satisfy the specified JSON Schema."""

    regex: String
    options: String | None = None

    def compile_query(self, context: Context) -> MongoQuery:
        return {
            "$regex": compile_expression(self.regex, context=context),
        } | nullfree_dict(
            {
                "$options": compile_expression(self.options, context=context),
            },
        )

    def as_expression(
        self,
        field: PathLike,
        context: Context,
    ) -> expressions.ExpressionOperator:
        return expressions.RegexMatch(field, regex=self.regex, options=self.options)


@dataclass
class NotProxy(ConditionInterface):
    ref: AsRef

    def build_condition(self, op: Operator, /) -> Predicate:
        return Condition(self.ref, op=Not(op))

    def __call__(self, op: Operator, /) -> Predicate:
        return self.build_condition(op)
