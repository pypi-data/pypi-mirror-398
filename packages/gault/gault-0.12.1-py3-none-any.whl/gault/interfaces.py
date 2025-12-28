from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    Self,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)

from bson import ObjectId

T = TypeVar("T")
K_co = TypeVar("K_co", covariant=True)
V_co = TypeVar("V_co", covariant=True)
T_co = TypeVar("T_co", covariant=True)

if TYPE_CHECKING:
    from .models import Model
    from .types import (
        Context,
        Direction,
        FieldLike,
        MongoExpression,
        MongoQuery,
    )


class AttributeBase:
    __slots__ = ("db_alias", "name", "owner")

    def __init__(
        self,
        owner: type[Model],
        name: str,
        db_alias: str | None = None,
    ) -> None:
        self.owner = owner
        self.name = name
        self.db_alias = db_alias or name

    def __repr__(self) -> str:
        typ = type(self).__name__
        args = [self.owner.__name__, repr(self.name)]
        if self.name != self.db_alias:
            args.append(f"db_alias={self.db_alias!r}")
        return f"{typ}({', '.join(args)})"


class QueryPredicate(ABC):
    @abstractmethod
    def compile_query(self, *, context: Context) -> MongoQuery:
        raise NotImplementedError


class ExpressionOperator(ABC):
    @abstractmethod
    def compile_expression(self, *, context: Context) -> MongoExpression:
        raise NotImplementedError


@dataclass
class Aliased(Generic[T_co]):
    ref: FieldLike
    value: T_co


class AsAlias:
    def alias(self, ref: str) -> Aliased[Self]:
        return Aliased(ref, self)


class Assignable:
    def assign(self, input: T) -> Aliased[T]:
        return Aliased(cast("Any", self), input)


@ExpressionOperator.register
@QueryPredicate.register
class AsRef(ABC):
    @abstractmethod
    def compile_field(self, *, context: Context) -> str:
        raise NotImplementedError

    @abstractmethod
    def compile_expression(self, *, context: Context) -> str:
        raise NotImplementedError


class FieldSortInterface:
    name: str

    def asc(self) -> tuple[Self, Direction]:
        # generate sort token
        return (self, 1)

    def desc(self) -> tuple[Self, Direction]:
        # generate sort token
        return (self, -1)

    def by_score(self, name: str) -> tuple[Self, Direction]:
        # generate sort token
        return (self, {"$meta": name})


ProjectSelector: TypeAlias = tuple[Any, Any]


class InclusionInterface:
    @overload
    def keep(self, *, alias: None = None) -> Aliased[Literal[True]]: ...

    @overload
    def keep(self, *, alias: FieldLike) -> Aliased[Self]: ...

    def keep(self, *, alias: FieldLike | None = None) -> Any:
        if alias is not None:
            ref: Any = alias
            val: Any = self
        else:
            ref = self
            val = True
        return Aliased(cast("Any", ref), val)

    def remove(self) -> Aliased[Literal["$$REMOVE"]]:
        return Aliased(cast("Any", self), "$$REMOVE")


class TempFieldInterface:
    @classmethod
    def tmp(cls) -> Self:
        # instantiate field with a random name
        name = f"__{ObjectId().__str__()}"
        return cls(name)  # type: ignore[call-arg]


class SubfieldInterface:
    name: str

    def field(self, name: str) -> Self:
        # access a sub field
        prefixed = self.name + "." + name
        return replace(  # type: ignore[no-any-return]
            cast("Any", self),
            name=prefixed,
        )
