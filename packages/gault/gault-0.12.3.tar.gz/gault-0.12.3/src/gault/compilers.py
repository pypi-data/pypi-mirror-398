from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, overload

from bson import Binary, ObjectId, Timestamp

from .interfaces import AsRef, ExpressionOperator, QueryPredicate

if TYPE_CHECKING:
    from .types import (
        AnyExpression,
        Context,
        FieldString,
        MongoExpression,
        MongoQuery,
        PathString,
    )


def compile_query(value: Any, *, context: Context) -> MongoQuery:
    match value:
        case QueryPredicate():
            return value.compile_query(context=context)
        case dict():
            return value
        case _:
            msg = f"compile query is not implemented for type {type(value)}"
            raise CompilationError(msg, target=value)


@dataclass
class CompilationError(Exception):
    message: str
    target: Any | None = None

    def __post_init__(self) -> None:
        super().__init__(self.message)


@overload
def compile_expression_multi(
    obj: list[Any], *, context: Context
) -> list[MongoExpression]: ...


@overload
def compile_expression_multi(obj: Any, *, context: Context) -> MongoExpression: ...


def compile_expression_multi(
    obj: list[Any] | Any, *, context: Context
) -> list[MongoExpression] | MongoExpression:
    if isinstance(obj, list):
        return [compile_expression(element, context=context) for element in obj]
    return compile_expression(obj, context=context)


def compile_expression(
    obj: AnyExpression, *, context: Context
) -> MongoExpression | Any:
    match obj:
        case ExpressionOperator():
            return obj.compile_expression(context=context)
        case (
            str()
            | int()
            | float()
            | bool()
            | None
            | Mapping()
            | list()
            | ObjectId()
            | Binary()
            | Timestamp()
            | datetime()
            | date()
        ):
            return obj
        case _:
            msg = f"compile expression is not implemented for type {type(obj)}"
            raise CompilationError(msg, target=obj)


def compile_path(obj: Any, *, context: Context) -> PathString:
    match obj:
        case AsRef():
            return obj.compile_expression(context=context)
        case str() if obj.startswith("$"):
            return obj
        case str() if not obj.startswith("$"):
            msg = f"Value {obj!r} looks like a field"
            raise CompilationError(msg, target=obj)
        case _:
            msg = f"compile path is not implemented for type {type(obj)}"
            raise CompilationError(msg, target=obj)


def compile_field(obj: Any, *, context: Context) -> FieldString:
    match obj:
        case AsRef():
            return obj.compile_field(context=context)
        case str() if not obj.startswith("$"):
            return obj
        case str() if obj.startswith("$"):
            msg = f"Value {obj!r} looks like a path"
            raise CompilationError(msg, target=obj)
        case _:
            msg = f"compile field is not implemented for type {type(obj)}"
            raise CompilationError(msg, target=obj)
