from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypedDict,
    TypeVar,
    Unpack,
    dataclass_transform,
    no_type_check,
    overload,
)
from weakref import WeakKeyDictionary, WeakValueDictionary

from .interfaces import (
    AsRef,
    AttributeBase,
    FieldSortInterface,
    SubfieldInterface,
)
from .predicates import Condition, ConditionInterface, NotInterface, Operator, Predicate
from .utils import drop_missing

if TYPE_CHECKING:
    from .types import Context, Value

M = TypeVar("M", bound="Model")
T = TypeVar("T")


SCHEMAS: WeakValueDictionary[str, type[Schema]] = WeakValueDictionary()
COLLECTIONS: WeakKeyDictionary[type[Model], str] = WeakKeyDictionary()


@no_type_check
def unwrap_model(model: type[M] | M) -> type[M]:
    if isinstance(model, Model):
        model = type(model)
    return model


@no_type_check
def get_collection(model: type[Model] | Model) -> str:
    model = unwrap_model(model)
    return COLLECTIONS[model]


def get_schema(collection: str) -> type[Schema]:
    return SCHEMAS[collection]


@dataclass_transform(kw_only_default=True)
class Model:
    def __init_subclass__(cls, collection: str | None = None) -> None:
        dataclass(cls, init=True, repr=True, kw_only=True)  # type: ignore[call-overload]
        for dataclass_field in fields(cls):  # type: ignore[arg-type]
            field: Attribute = Attribute(
                name=dataclass_field.name, **dataclass_field.metadata
            )
            setattr(cls, dataclass_field.name, field)

        cls.__hash__ = object.__hash__  # type: ignore[method-assign]

        if collection:
            COLLECTIONS[cls] = collection


@dataclass_transform(kw_only_default=True)
class Schema(Model, collection=None):
    def __init_subclass__(cls, collection: str) -> None:
        if collection is None:
            msg = "collection is required"
            raise ValueError(msg)

        super().__init_subclass__(collection=collection)
        SCHEMAS[collection] = cls


class AttributeSpec(
    AttributeBase,
    AsRef,
    ConditionInterface,
    FieldSortInterface,
    SubfieldInterface,
    NotInterface,
    Generic[T],
):
    def compile_field(self, *, context: Context) -> str:
        return self.db_alias

    def compile_expression(self, *, context: Context) -> str:
        return "$" + self.db_alias

    def get_db_alias(self) -> str:
        return self.db_alias

    def build_condition(self, op: Operator, /) -> Predicate:
        return Condition(self, op=op)

    def __hash__(self) -> int:
        return hash((self.owner, self.name, self.db_alias))

    def __eq__(self, other: Value) -> Predicate:  # type: ignore[override]
        return ConditionInterface.eq(self, other)

    def __ne__(self, other: Value) -> Predicate:  # type: ignore[override]
        return ConditionInterface.ne(self, other)

    def __lt__(self, other: Value) -> Predicate:
        return ConditionInterface.lt(self, other)

    def __le__(self, other: Value) -> Predicate:
        return ConditionInterface.lte(self, other)

    def __gt__(self, other: Value) -> Predicate:
        return ConditionInterface.gt(self, other)

    def __ge__(self, other: Value) -> Predicate:
        return ConditionInterface.gte(self, other)


class Attribute(Generic[T]):
    def __init__(
        self,
        *,
        name: str | None = None,
        pk: bool = False,
        db_alias: str | None = None,
    ) -> None:
        self.name: str | None = name
        self.pk = pk
        self.db_alias = db_alias

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    @overload
    def __get__(self, instance: None, owner: type) -> AttributeSpec[T]: ...

    @overload
    def __get__(self, instance: object, owner: type) -> T: ...

    def __get__(
        self, instance: object | None, owner: type[Model]
    ) -> T | AttributeSpec[T]:
        assert self.name  # noqa: S101
        if instance is None:
            return AttributeSpec(owner, self.name, db_alias=self.db_alias)
        return instance.__dict__[self.name]  # type: ignore[no-any-return]

    def __set__(self, instance: object, value: T) -> None:
        assert self.name  # noqa: S101
        instance.__dict__[self.name] = value


class AttributeMetadata(TypedDict, total=False):
    pk: bool
    db_alias: str


def configure(
    *,
    default: Any = MISSING,
    **metadata: Unpack[AttributeMetadata],
) -> Any:
    metadata = drop_missing(metadata)  # type: ignore[assignment]
    return field(default=default, metadata=metadata)
