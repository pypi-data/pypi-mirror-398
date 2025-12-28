from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from .types import Context

    Geo: TypeAlias = "Box" | "Center" | "CenterSphere" | "GeoJSON"
    Box: TypeAlias = Any
    Center: TypeAlias = Any
    CenterSphere: TypeAlias = Any
    GeoJSON: TypeAlias = Any


def compile_geo(value: Geo, *, context: Context) -> Any:
    match value:
        case {"$box": _}:
            # https://www.mongodb.com/docs/manual/reference/operator/query/box/
            return value
        case {"$center": _}:
            # https://www.mongodb.com/docs/manual/reference/operator/query/center/
            return value
        case {"$centerSphere": _}:
            # https://www.mongodb.com/docs/manual/reference/operator/query/centerSphere/
            return value
        case {"$geometry": _}:
            # https://www.mongodb.com/docs/manual/reference/operator/query/geometry/
            return value
        case _:
            raise NotImplementedError
