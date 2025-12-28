from __future__ import annotations

from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar
from weakref import WeakKeyDictionary, WeakSet

from pymongo import ReturnDocument

from .exceptions import Forbidden, NotFound, Unprocessable
from .mappers import get_mapper
from .models import Model, Schema, get_collection, unwrap_model
from .pipelines import Pipeline, RawStep
from .predicates import Predicate

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from pymongo.asynchronous.database import AsyncDatabase
    from pymongo.synchronous.database import Database

    from .pipelines import Stage
    from .types import MongoQuery

    Filter: TypeAlias = Predicate | Pipeline | MongoQuery | list[Stage] | None

M = TypeVar("M", bound="Model")
S = TypeVar("S", bound="Schema")


class StateTracker(Generic[M]):
    def __init__(self) -> None:
        self._states: WeakKeyDictionary[M, Any] = WeakKeyDictionary()

    def snapshot(self, instance: M) -> None:
        self._states[instance] = deepcopy(instance.__dict__)

    def reset(self, instance: M) -> None:
        instance.__dict__ = deepcopy(self._states[instance])

    def get_dirty_fields(self, instance: M) -> set[str]:
        dirty_fields = set()
        if snapshoted := self._states.get(instance):
            state = instance.__dict__
            for key, val in snapshoted.items():
                if state[key] != val:
                    dirty_fields.add(key)
        return dirty_fields


class Persistence(Generic[M]):
    def __init__(self) -> None:
        self._instances: WeakSet[M] = WeakSet()

    def is_persisted(self, instance: M) -> bool:
        return instance in self._instances

    def mark_persisted(self, instance: M) -> None:
        self._instances.add(instance)

    def forget(self, instance: M) -> None:
        self._instances.remove(instance)


class AsyncManager:
    def __init__(
        self,
        database: AsyncDatabase,
        *,
        persistence: Persistence | None = None,
        state_tracker: StateTracker | None = None,
    ) -> None:
        self.database = database
        self._persistence = persistence
        self._state_tracker = state_tracker

    @cached_property
    def persistence(self) -> Persistence:
        persistence = self._persistence = self._persistence or Persistence()
        return persistence

    @cached_property
    def state_tracker(self) -> StateTracker:
        state_tracker = self._state_tracker = self._state_tracker or StateTracker()
        return state_tracker

    async def get(self, model: type[M], filter: Filter = None) -> M:
        if instance := await self.find(model, filter):
            return instance
        raise NotFound(model, filter)

    async def find(
        self,
        model: type[M],
        filter: Filter = None,
    ) -> M | None:
        async for instance in self.select(model, filter, take=1):
            return instance
        return None

    async def select(
        self,
        model: type[M],
        filter: Filter = None,
        *,
        skip: int | None = None,
        take: int | None = None,
    ) -> AsyncIterator[M]:
        match filter:
            case None:
                filter = Pipeline()
            case list():
                filter = Pipeline(steps=[RawStep(stage) for stage in filter])  # ty:ignore[invalid-argument-type]
            case dict() | Predicate():
                filter = Pipeline().match(filter)
            case Pipeline():
                pass
            case _:
                raise NotImplementedError(filter)

        if skip:
            filter = filter.skip(skip)
        if take:
            filter = filter.take(take)
        filter = filter.project(model).build()
        collection = get_collection(model)

        if filter and "$documents" in filter[0]:
            # {"$documents": …} stage can be performs by database only
            func = self.database.aggregate
        else:
            func = self.database.get_collection(collection).aggregate

        cursor = await func(
            pipeline=filter,
        )

        mapper = get_mapper(model)
        async for document in cursor:
            instance = mapper.map(document)
            self.persistence.mark_persisted(instance)
            self.state_tracker.snapshot(instance)
            yield instance

    async def insert(self, instance: S) -> S:
        if not isinstance(instance, Schema):
            raise Forbidden(
                unwrap_model(instance),
                reason="Only model allowed for insert",
            )
        document = get_mapper(instance).to_document(instance)
        collection = get_collection(instance)
        await self.database.get_collection(collection).insert_one(document)
        self.persistence.mark_persisted(instance)
        self.state_tracker.snapshot(instance)
        return instance

    async def save(
        self,
        instance: S,
        *,
        refresh: bool = False,
        atomic: bool = False,
    ) -> S:
        if not isinstance(instance, Schema):
            raise Forbidden(
                unwrap_model(instance),
                reason="Only model allowed for insert",
            )

        mapper = get_mapper(instance)
        filter = {}
        atomic = atomic and self.persistence.is_persisted(instance)
        dirty_fields = self.state_tracker.get_dirty_fields(instance)

        on_insert = {}
        on_update = {}
        for model_field, db_field, value, pk in mapper.iter_document(instance):
            if pk:
                filter[db_field] = {"$eq": value}
            elif atomic and model_field not in dirty_fields:
                on_insert[db_field] = value
            else:
                on_update[db_field] = value

        if not filter:
            raise Unprocessable(
                unwrap_model(instance),
                reason="model must declare one field as pk",
            )

        update = {}
        if on_insert:
            update["$setOnInsert"] = on_insert
        if on_update:
            update["$set"] = on_update

        collection = get_collection(instance)
        document = await self.database.get_collection(collection).find_one_and_update(
            filter=filter,
            update=update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if refresh is True:
            persisted = mapper.map(document)
            instance.__dict__ = persisted.__dict__

        self.persistence.mark_persisted(instance)
        self.state_tracker.snapshot(instance)
        return instance

    async def refresh(self, instance: M) -> M:
        collection = get_collection(instance)
        mapper = get_mapper(instance)
        filter = mapper.to_filter(instance)

        if not filter:
            raise Unprocessable(
                unwrap_model(instance),
                reason="model must declare one field as pk",
            )

        if document := await self.database.get_collection(collection).find_one(filter):
            persisted = mapper.map(document)
            instance.__dict__ = persisted.__dict__
            self.persistence.mark_persisted(instance)
            return instance
        raise NotFound(type(instance), filter)


class Manager(Generic[M, S]):
    def __init__(
        self,
        database: Database,
        *,
        persistence: Persistence | None = None,
        state_tracker: StateTracker | None = None,
    ) -> None:
        self.database = database
        self._persistence = persistence
        self._state_tracker = state_tracker

    @cached_property
    def persistence(self) -> Persistence:
        persistence = self._persistence = self._persistence or Persistence()
        return persistence

    @cached_property
    def state_tracker(self) -> StateTracker:
        state_tracker = self._state_tracker = self._state_tracker or StateTracker()
        return state_tracker

    def get(self, model: type[M], filter: Filter = None) -> M:
        if instance := self.find(model, filter):
            return instance
        raise NotFound(model, filter)

    def find(
        self,
        model: type[M],
        filter: Filter = None,
    ) -> M | None:
        for instance in self.select(model, filter, take=1):
            return instance
        return None

    def select(
        self,
        model: type[M],
        filter: Filter = None,
        *,
        skip: int | None = None,
        take: int | None = None,
    ) -> Iterator[M]:
        match filter:
            case None:
                filter = Pipeline()
            case list():
                filter = Pipeline(steps=[RawStep(stage) for stage in filter])  # ty:ignore[invalid-argument-type]
            case dict() | Predicate():
                filter = Pipeline().match(filter)
            case Pipeline():
                pass
            case _:
                raise NotImplementedError(filter)

        if skip:
            filter = filter.skip(skip)
        if take:
            filter = filter.take(take)
        filter = filter.project(model).build()
        collection = get_collection(model)

        if filter and "$documents" in filter[0]:
            # {"$documents": …} stage can be performs by database only
            func = self.database.aggregate
        else:
            func = self.database.get_collection(collection).aggregate

        cursor = func(
            pipeline=filter,
        )

        mapper = get_mapper(model)
        for document in cursor:
            instance = mapper.map(document)
            self.persistence.mark_persisted(instance)
            self.state_tracker.snapshot(instance)
            yield instance

    def insert(self, instance: S) -> S:
        if not isinstance(instance, Schema):
            raise Forbidden(
                unwrap_model(instance),
                reason="Only model allowed for insert",
            )
        document = get_mapper(instance).to_document(instance)
        collection = get_collection(instance)
        self.database.get_collection(collection).insert_one(document)
        self.persistence.mark_persisted(instance)
        self.state_tracker.snapshot(instance)
        return instance

    def save(
        self,
        instance: S,
        *,
        refresh: bool = False,
        atomic: bool = False,
    ) -> S:
        if not isinstance(instance, Schema):
            raise Forbidden(
                unwrap_model(instance),
                reason="Only model allowed for insert",
            )

        mapper = get_mapper(instance)
        filter = {}
        atomic = atomic and self.persistence.is_persisted(instance)
        dirty_fields = self.state_tracker.get_dirty_fields(instance)

        on_insert = {}
        on_update = {}
        for model_field, db_field, value, pk in mapper.iter_document(instance):
            if pk:
                filter[db_field] = {"$eq": value}
            elif atomic and model_field not in dirty_fields:
                on_insert[db_field] = value
            else:
                on_update[db_field] = value

        if not filter:
            raise Unprocessable(
                unwrap_model(instance),
                reason="model must declare one field as pk",
            )

        update = {}
        if on_insert:
            update["$setOnInsert"] = on_insert
        if on_update:
            update["$set"] = on_update

        collection = get_collection(instance)
        document = self.database.get_collection(collection).find_one_and_update(
            filter=filter,
            update=update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if refresh is True:
            persisted = mapper.map(document)
            instance.__dict__ = persisted.__dict__

        self.persistence.mark_persisted(instance)
        self.state_tracker.snapshot(instance)
        return instance

    def refresh(self, instance: M) -> M:
        collection = get_collection(instance)
        mapper = get_mapper(instance)
        filter = mapper.to_filter(instance)

        if not filter:
            raise Unprocessable(
                unwrap_model(instance),
                reason="model must declare one field as pk",
            )

        if document := self.database.get_collection(collection).find_one(filter):
            persisted = mapper.map(document)
            instance.__dict__ = persisted.__dict__
            self.persistence.mark_persisted(instance)
            return instance
        raise NotFound(type(instance), filter)
