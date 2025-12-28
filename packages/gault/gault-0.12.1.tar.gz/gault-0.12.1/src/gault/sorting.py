from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias, cast

from gault.compilers import compile_field

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from .types import Context, Direction, FieldLike, FieldString

    Sort: TypeAlias = Mapping[FieldString, Direction]
    SortParam: TypeAlias = tuple[FieldString, Direction]

    SortToken: TypeAlias = FieldLike | tuple[FieldLike, Direction | None]
    SortPayload: TypeAlias = (
        SortToken | list[SortToken] | Mapping[FieldLike, Direction | None]
    )


def normalize_sort(obj: SortPayload | None, *, context: Context) -> Sort | None:
    token: SortToken
    normalized: list[SortParam] = []

    match obj:
        case list(tokens):
            for token in tokens:
                normalized += normalize_token(token, context=context)
        case dict(tokens):
            for token in tokens.items():
                normalized += normalize_token(token, context=context)
        case _:
            normalized += normalize_token(cast("Any", obj), context=context)
    return dict(normalized) if normalized else None


def normalize_token(obj: SortToken, *, context: Context) -> Iterator[SortParam]:
    if not obj:
        return

    if isinstance(obj, tuple):
        field, direction = obj
    else:
        field = obj
        direction = None

    field = compile_field(field, context=context)

    yield (field, direction or 1)
