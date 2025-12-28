from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .managers import Filter
    from .models import Model
    from .pipelines import Pipeline


@dataclass
class Unprocessable(ValueError):
    model: type[Model]
    reason: str

    def __post_init__(self) -> None:
        msg = f"Unprocessable {self.model.__name__} ; {self.reason}"
        super().__init__(msg)


@dataclass
class Forbidden(TypeError):
    model: type[Model]
    reason: str

    def __post_init__(self) -> None:
        msg = f"Forbidden {self.model.__name__} ; {self.reason}"
        super().__init__(msg)


@dataclass
class NotFound(LookupError):
    model: type[Model]
    filter: Filter

    def __post_init__(self) -> None:
        msg = f"Instance of {self.model.__name__} not found"
        super().__init__(msg)


class PipelineError(Exception):
    pipeline: Pipeline
    reason: str

    def __post_init__(self) -> None:
        msg = f"Pipeline error ; {self.reason}"
        super().__init__(msg)
