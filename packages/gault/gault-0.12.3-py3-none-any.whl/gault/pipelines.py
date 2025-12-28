from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    Literal,
    ParamSpec,
    Self,
    TypeAlias,
    TypeVar,
    overload,
)

from .accumulators import Accumulator, compile_accumulator
from .compilers import compile_expression, compile_field, compile_path, compile_query
from .interfaces import Aliased, AsAlias
from .mappers import get_mapper
from .models import Model, get_collection
from .sorting import normalize_sort
from .utils import drop_missing, nullfree_dict, unwrap_array

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from .predicates import Field, Predicate
    from .sorting import SortPayload, SortToken
    from .types import (
        AccumulatorExpression,
        AnyExpression,
        Context,
        Document,
        FieldLike,
        MongoQuery,
        PositiveInteger,
    )

    Stage: TypeAlias = Mapping[str, Any]

T = TypeVar("T")
P = ParamSpec("P")
A_co = TypeVar("A_co", bound="Accumulator", covariant=True)


@dataclass
class Pipeline(AsAlias):
    steps: list[Step] = field(default_factory=list, kw_only=True)

    def pipe(
        self,
        _0: Callable[Concatenate[Self, P], Self],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Self:
        """Offers a structured way to apply a sequence of user-defined functions.

        Parameters
        ----------
        function
            Callable; will receive the frame as the first parameter,
            followed by any given args/kwargs.
        *args
            Arguments to pass to the UDF.
        **kwargs
            Keyword arguments to pass to the UDF.

        """
        return _0(self, *args, **kwargs)

    def match(self, query: dict | Predicate, /) -> Self:
        """Filter documents matching the specified condition(s).

        Parameters
        ----------
        query
            Dict query or Predicate expression to filter documents.

        Examples
        --------
        >>> # Using raw dict
        >>> Pipeline().match({"status": "active", "age": {"$gte": 18}})

        >>> # Using Field predicates
        >>> Pipeline().match(Field("status").eq("active") & Field("age").gte(18))

        """
        step = MatchStep(query=query)
        return self.add_step(step)

    def skip(self, size: PositiveInteger, /) -> Self:
        """Skip the first n documents.

        Parameters
        ----------
        size
            Number of documents to skip.

        Examples
        --------
        >>> # Skip first 20 documents
        >>> Pipeline().skip(20)

        >>> # Pagination: skip to page 3 with 10 items per page
        >>> Pipeline().skip(20).take(10)

        """
        stage = {"$skip": size}
        return self.raw(stage)

    def take(self, size: PositiveInteger, /) -> Self:
        """Limit the number of documents passed to the next stage.

        Parameters
        ----------
        size
            Maximum number of documents to return.

        Examples
        --------
        >>> # Get only first 10 documents
        >>> Pipeline().take(10)

        >>> # Combined with skip for pagination
        >>> Pipeline().skip(20).take(10)

        """
        stage = {"$limit": size}
        return self.raw(stage)

    def sample(self, size: PositiveInteger, /) -> Self:
        """Randomly select the specified number of documents.

        Parameters
        ----------
        size
            Number of documents to randomly select.

        Examples
        --------
        >>> # Get 5 random documents
        >>> Pipeline().sample(5)

        >>> # Sample after filtering
        >>> Pipeline().match({"status": "active"}).sample(10)

        """
        stage = {"$sample": {"size": size}}
        return self.raw(stage)

    @overload
    def sort(self, *tokens: SortToken) -> Self: ...

    @overload
    def sort(self, tokens: list[SortToken]) -> Self: ...

    @overload
    def sort(self, tokens: SortPayload) -> Self: ...

    def sort(self, *spec: SortPayload) -> Self:  # type: ignore[misc]
        """Reorder documents by the specified sort key.

        Parameters
        ----------
        *spec
            Sort specification as SortToken(s), list of SortToken, or dict.

        Examples
        --------
        >>> # Sort by single field (string)
        >>> Pipeline().sort("name")

        >>> # Sort with SortToken
        >>> Pipeline().sort(MyModel.age.desc(), MyModel.name.asc())

        >>> # Sort with dict
        >>> Pipeline().sort({"age": -1, "name": 1})

        >>> # Sort with list of tokens
        >>> Pipeline().sort([MyModel.age.desc(), MyModel.name.asc()])

        """
        payload: Any
        if spec and isinstance(spec[0], dict):
            payload = spec[0]
        else:
            payload = list(spec)
        step = SortStep(payload)  # ty:ignore[invalid-argument-type]
        return self.add_step(step)

    @overload
    def project(self, *projections: Aliased[AnyExpression]) -> Self: ...

    @overload
    def project(
        self,
        projection: type[Model]
        | Mapping[FieldLike, AnyExpression]
        | list[Aliased[AnyExpression]],
        /,
    ) -> Self: ...

    def project(self, *projections: Any) -> Self:
        """Reshape documents by including, excluding, or adding fields.

        Parameters
        ----------
        *projections
            Projection spec as Model class, dict, list of Aliased expressions, or spread Aliased expressions.

        Examples
        --------
        >>> # Project using Model class
        >>> Pipeline().project(MyModel)

        >>> # Project with dict
        >>> Pipeline().project({"name": True, "age": True})

        >>> # Project with Field methods (spread)
        >>> Pipeline().project(
        ...     Field("name").keep(),
        ...     Field("age").keep(alias="person_age"),
        ...     Field("internal").remove()
        ... )

        >>> # Project with list
        >>> Pipeline().project([Field("name").keep(), Field("age").keep()])

        >>> # Project with expressions
        >>> Pipeline().project({"fullName": {"$concat": ["$firstName", " ", "$lastName"]}})

        """
        if projections and (
            isinstance(projections[0], Mapping)
            or (
                projections
                and isinstance(projections[0], type)
                and issubclass(projections[0], Model)
            )
        ):
            spec: Any = projections[0]
        else:
            spec = unwrap_array(projections)

        step = ProjectStep(spec)
        return self.add_step(step)

    def bucket(
        self,
        by: AnyExpression,
        /,
        boundaries: list[T],
        default: str | None = None,
        output: Mapping[FieldLike, Accumulator | AccumulatorExpression] | None = None,
    ) -> Self:
        """Categorize documents into buckets based on specified boundaries.

        Parameters
        ----------
        by
            Expression to group by.
        boundaries
            Array of values that specify boundaries for each bucket.
        default
            Bucket name for documents that don't fall within boundaries.
        output
            Mapping of output field names to accumulator expressions.

        Examples
        --------
        >>> # Age buckets with count
        >>> Pipeline().bucket(
        ...     by="$age",
        ...     boundaries=[0, 18, 65, 100],
        ...     default="other",
        ...     output={"count": Sum(1), "avgScore": Avg("$score")}
        ... )

        """
        step = BucketStep(
            by=by,
            boundaries=boundaries,
            default=default,
            output=output,
        )
        return self.add_step(step)

    def bucket_auto(
        self,
        by: AnyExpression,
        /,
        buckets: int,
        output: Mapping[FieldLike, Accumulator | AccumulatorExpression] | None = None,
        granularity: Literal[
            "R5",
            "R10",
            "R20",
            "R40",
            "R80",
            "1-2-5",
            "E6",
            "E12",
            "E24",
            "E48",
            "E96",
            "E192",
            "POWERSOF2",
        ]
        | None = None,
    ) -> Self:
        """Automatically categorize documents into a specified number of buckets.

        Parameters
        ----------
        by
            Expression to group by.
        buckets
            Number of buckets to create.
        output
            Mapping of output field names to accumulator expressions.
        granularity
            Preferred number series for bucket boundaries.

        Examples
        --------
        >>> # Auto bucket prices into 5 buckets
        >>> Pipeline().bucket_auto(
        ...     by="$price",
        ...     buckets=5,
        ...     output={"count": Sum(1), "avgPrice": Avg("$price")}
        ... )

        """
        step = BucketAutoStep(
            by=by,
            buckets=buckets,
            output=output,
            granularity=granularity,
        )
        return self.add_step(step)

    @overload
    def group(
        self,
        accumulators: Mapping[FieldLike, Accumulator | AccumulatorExpression],
        /,
        *,
        by: AnyExpression,
    ) -> Self: ...

    @overload
    def group(
        self, accumulators: list[Aliased[A_co]], /, *, by: AnyExpression
    ) -> Self: ...

    @overload
    def group(self, *accumulators: Aliased[A_co], by: AnyExpression) -> Self: ...

    def group(self, *accumulators: Any, by: AnyExpression) -> Self:
        """Group documents by a specified expression and apply accumulators.

        Parameters
        ----------
        *accumulators
            Accumulators as dict, list of Aliased, or spread Aliased.
        by
            Expression to group by. Use None to group all documents.

        Examples
        --------
        >>> # Group with dict
        >>> Pipeline().group(
        ...     {"total": Sum("$amount"), "avg": Avg("$score")},
        ...     by="$category"
        ... )

        >>> # Group with spread Aliased
        >>> Pipeline().group(
        ...     Sum("$amount").alias("total"),
        ...     Avg("$score").alias("avg"),
        ...     by="$category"
        ... )

        >>> # Group with list
        >>> Pipeline().group(
        ...     [Sum("$amount").alias("total")],
        ...     by="$category"
        ... )

        >>> # Group all documents
        >>> Pipeline().group({"count": Count()}, by=None)

        """
        if accumulators and isinstance(accumulators[0], Mapping):
            mapping: Mapping[FieldLike, Accumulator | AccumulatorExpression] = (
                accumulators[0]
            )
        else:
            mapping = {
                aliased.ref: aliased.value for aliased in unwrap_array(accumulators)
            }
        step = GroupStep(by=by, accumulators=mapping)
        return self.add_step(step)

    def set_field(self, field: FieldLike, value: AnyExpression, /) -> Self:
        """Add a new field or replace existing field value.

        Parameters
        ----------
        field
            Field name or Field object.
        value
            Value or expression to set.

        Examples
        --------
        >>> # Set a constant value
        >>> Pipeline().set_field("status", "processed")

        >>> # Set with expression
        >>> Pipeline().set_field("total", {"$multiply": ["$price", "$quantity"]})

        """
        return self.set({field: value})

    @overload
    def set(self, field: Mapping[FieldLike, AnyExpression], /) -> Self: ...

    @overload
    def set(self, field: list[Aliased[AnyExpression]], /) -> Self: ...

    @overload
    def set(self, *fields: Aliased[AnyExpression]) -> Self: ...

    def set(self, *fields: Any) -> Self:
        """Add new fields or replace existing field values.

        Parameters
        ----------
        *fields
            Fields as dict, list of Aliased, or spread Aliased.

        Examples
        --------
        >>> # Set with dict
        >>> Pipeline().set({"total": {"$multiply": ["$price", "$qty"]}, "status": "done"})

        >>> # Set with spread Aliased
        >>> Pipeline().set(
        ...     Field("total").assign({"$multiply": ["$price", "$qty"]}),
        ...     Field("status").assign("done")
        ... )

        >>> # Set with list
        >>> Pipeline().set([Field("status").assign("done")])

        """
        if fields and isinstance(fields[0], Mapping):
            mapping: Mapping[FieldLike, Accumulator | AccumulatorExpression] = fields[0]
        else:
            mapping = {aliased.ref: aliased.value for aliased in unwrap_array(fields)}

        step = SetStep(fields=mapping)
        return self.add_step(step)

    def unset(self, *fields: Field | str) -> Self:
        """Remove specified fields from documents.

        Parameters
        ----------
        *fields
            Field names or Field objects to remove.

        Examples
        --------
        >>> # Remove single field
        >>> Pipeline().unset("_id")

        >>> # Remove multiple fields
        >>> Pipeline().unset("_id", "internal", "temp")

        """
        step = UnsetStep(fields=list(fields))
        return self.add_step(step)

    def unwind(
        self,
        field: Field | str,
        /,
        *,
        include_array_index: str | None = None,
        preserve_null_and_empty_arrays: bool | None = None,
    ) -> Self:
        """Deconstruct an array field to output a document for each element.

        Parameters
        ----------
        field
            Array field to unwind.
        include_array_index
            Name of field to hold array index.
        preserve_null_and_empty_arrays
            Whether to output documents for null or empty arrays.

        Examples
        --------
        >>> # Simple unwind
        >>> Pipeline().unwind("$tags")

        >>> # Unwind with array index
        >>> Pipeline().unwind("$items", include_array_index="item_index")

        >>> # Preserve empty arrays
        >>> Pipeline().unwind("$items", preserve_null_and_empty_arrays=True)

        """
        step = UnwindStep(
            field=field,
            include_array_index=include_array_index,
            preserve_null_and_empty_arrays=preserve_null_and_empty_arrays,
        )
        return self.add_step(step)

    def count(self, output: Field | str, /) -> Self:
        """Return a count of the number of documents at this stage.

        Parameters
        ----------
        output
            Name of output field for the count.

        Examples
        --------
        >>> # Count all documents
        >>> Pipeline().count("total")

        >>> # Count after filtering
        >>> Pipeline().match({"status": "active"}).count("active_count")

        """
        step = CountStep(output)
        return self.add_step(step)

    def replace_with(self, expr: Any, /) -> Self:
        """Replace the input document with the specified document.

        Parameters
        ----------
        expr
            Expression or document to replace with.

        Examples
        --------
        >>> # Replace with new document structure
        >>> Pipeline().replace_with({"name": "$fullName", "age": "$person_age"})

        >>> # Replace with nested field
        >>> Pipeline().replace_with("$user")

        """
        stage = {"$replaceWith": expr}
        return self.raw(stage)

    def union_with(
        self,
        other: CollectionPipeline | type[Model],
        /,
    ) -> Self:
        """Perform a union of two collections.

        Parameters
        ----------
        other
            CollectionPipeline or Model class to union with.

        Examples
        --------
        >>> # Union with Model class
        >>> Pipeline().union_with(OtherModel)

        >>> # Union with CollectionPipeline
        >>> sub = CollectionPipeline("archive").match({"archived": True})
        >>> Pipeline().union_with(sub)

        """
        if isinstance(other, CollectionPipeline):
            body = {
                "coll": other.collection,
                "pipeline": other.build(),
            }
        elif issubclass(other, Model):
            body = {
                "coll": get_collection(other),
                "pipeline": Pipeline().project(other).build(),
            }
        else:
            raise NotImplementedError

        stage = {"$unionWith": body}
        return self.raw(stage)

    def graph_lookup(
        self,
        other: type[Model],
        /,
        start_with: FieldLike,
        local_field: FieldLike,
        foreign_field: FieldLike,
        into: FieldLike,
        max_depth: int | None = None,
        depth_field: FieldLike | None = None,
        restrict_search_with_match: MongoQuery | Predicate | None = None,
    ) -> Self:
        """Perform a recursive search on a collection.

        Parameters
        ----------
        other
            Model class to lookup in.
        start_with
            Expression for starting value.
        local_field
            Field from local documents for connection.
        foreign_field
            Field from foreign documents for connection.
        into
            Name of output array field.
        max_depth
            Maximum recursion depth.
        depth_field
            Field name to store recursion depth.
        restrict_search_with_match
            Query to filter foreign documents.

        Examples
        --------
        >>> # Find reporting hierarchy
        >>> Pipeline().graph_lookup(
        ...     Employee,
        ...     start_with="$reports_to",
        ...     local_field="reports_to",
        ...     foreign_field="employee_id",
        ...     into="reporting_chain",
        ...     max_depth=5
        ... )

        """
        step = GraphLookupStep(
            collection=get_collection(other),
            into=into,
            start_with=start_with,
            connect_from_field=local_field,
            connect_to_field=foreign_field,
            max_depth=max_depth,
            depth_field=depth_field,
            restrict_search_with_match=restrict_search_with_match,
        )
        return self.add_step(step)

    def lookup(
        self,
        other: CollectionPipeline | DocumentsPipeline | type[Model],
        /,
        *,
        local_field: FieldLike | None = None,
        foreign_field: FieldLike | None = None,
        into: FieldLike,
    ) -> Self:
        """Perform a left outer join to another collection.

        Parameters
        ----------
        other
            CollectionPipeline, DocumentsPipeline, or Model class to join with.
        local_field
            Field from local documents for equality match.
        foreign_field
            Field from foreign documents for equality match.
        into
            Name of output array field.

        Examples
        --------
        >>> # Simple lookup with Model
        >>> Pipeline().lookup(
        ...     OtherModel,
        ...     local_field="user_id",
        ...     foreign_field="_id",
        ...     into="user_data"
        ... )

        >>> # Lookup with sub-pipeline
        >>> sub = CollectionPipeline("orders").match({"status": "completed"})
        >>> Pipeline().lookup(sub, into="orders")

        >>> # Lookup with in-memory documents
        >>> docs = Pipeline.documents([{"id": 1, "value": "test"}])
        >>> Pipeline().lookup(docs, local_field="ref_id", foreign_field="id", into="refs")

        """
        pipeline: Pipeline | None
        if isinstance(other, CollectionPipeline):
            collection = other.collection
            pipeline = other
        elif isinstance(other, DocumentsPipeline):
            collection = None
            pipeline = other
        elif other and issubclass(other, Model):
            collection = get_collection(other)
            pipeline = None
        else:
            raise NotImplementedError
        step = LookupStep(
            collection=collection,
            pipeline=pipeline,
            local_field=local_field,
            foreign_field=foreign_field,
            into=into,
        )

        return self.add_step(step)

    @overload
    def facet(self, facets: Mapping[str, Pipeline], /) -> Self: ...

    @overload
    def facet(self, *facets: Aliased[Pipeline]) -> Self: ...

    def facet(self, *facets: Any) -> Self:
        """Process multiple pipelines within a single stage on the same input.

        Parameters
        ----------
        *facets
            Facets as dict mapping names to Pipelines, or spread Aliased Pipelines.

        Examples
        --------
        >>> # Facet with dict
        >>> Pipeline().facet({
        ...     "count": Pipeline().count("total"),
        ...     "avgPrice": Pipeline().group({"value": Avg("$price")}, by=None)
        ... })

        >>> # Facet with spread Aliased
        >>> Pipeline().facet(
        ...     Pipeline().count("total").alias("count"),
        ...     Pipeline().group({"value": Avg("$price")}, by=None).alias("avgPrice")
        ... )

        """
        if facets and isinstance(facets[0], Mapping):
            mapping = facets[0]
        else:
            mapping = {}
            for aliased in unwrap_array(facets):
                mapping[aliased.ref] = aliased.value

        step = FacetStep(facets=mapping)
        return self.add_step(step)

    def raw(self, *stages: Stage | Step) -> Self:
        """Add raw MongoDB stage(s) to the pipeline.

        Parameters
        ----------
        *stages
            MongoDB stage dicts or Step objects.

        Examples
        --------
        >>> # Add custom stage
        >>> Pipeline().raw({"$customStage": {"option": "value"}})

        >>> # Add multiple stages
        >>> Pipeline().raw(
        ...     {"$stage1": {}},
        ...     {"$stage2": {}}
        ... )

        """

        def to_step(obj: Stage | Step) -> Step:
            if not isinstance(obj, Step):
                return RawStep(obj)
            return obj

        steps = []
        for stage in stages:
            step = to_step(stage)
            steps.append(step)
        return replace(self, steps=[*self.steps, *steps])

    def add_step(self, step: Step, /) -> Self:
        """Add a Step object to the pipeline.

        Parameters
        ----------
        step
            Step object to add.

        Examples
        --------
        >>> # Usually called internally, but can be used directly
        >>> step = MatchStep(query={"status": "active"})
        >>> Pipeline().add_step(step)

        """
        return replace(self, steps=[*self.steps, step])

    def build(self, *, context: Context | None = None) -> list[Stage]:
        """Compile pipeline into list of MongoDB aggregation stages.

        Parameters
        ----------
        context
            Optional context dict for compilation.

        Examples
        --------
        >>> # Build pipeline to MongoDB stages
        >>> pipeline = Pipeline().match({"status": "active"}).sort({"age": -1})
        >>> stages = pipeline.build()
        >>> # [{"$match": {"status": "active"}}, {"$sort": {"age": -1}}]

        """
        context = context or {}
        stages: list[Stage] = []
        for step in self.steps:
            stages += step.compile(context=context)
        return stages

    @overload
    @classmethod
    def documents(cls, *documents: Document) -> DocumentsPipeline: ...

    @overload
    @classmethod
    def documents(
        cls,
        documents: list[Document],
    ) -> DocumentsPipeline: ...

    @classmethod  # type: ignore[misc]
    def documents(cls, *documents: Any) -> DocumentsPipeline:
        """Create a pipeline with in-memory documents.

        Parameters
        ----------
        *documents
            Documents as spread dicts or list of dicts.

        Examples
        --------
        >>> # Create with spread documents
        >>> Pipeline.documents(
        ...     {"id": 1, "name": "Alice"},
        ...     {"id": 2, "name": "Bob"}
        ... )

        >>> # Create with list
        >>> Pipeline.documents([
        ...     {"id": 1, "name": "Alice"},
        ...     {"id": 2, "name": "Bob"}
        ... ])

        """
        data: list[Document] = unwrap_array(documents)
        return DocumentsPipeline(data)


@dataclass
class CollectionPipeline(Pipeline):
    collection: str


@dataclass
class DocumentsPipeline(Pipeline):
    documents: list[Document]  # type: ignore[assignment]

    def build(self, *, context: Context | None = None) -> list[Stage]:
        context = context or {}
        stage = {"$documents": self.documents}
        return [stage, *super().build(context=context)]


class Step(ABC):
    @abstractmethod
    def compile(self, context: Context) -> Iterator[Stage]: ...


@dataclass
class RawStep(Step):
    stage: Stage

    def compile(self, context: Context) -> Iterator[Stage]:
        yield self.stage


@dataclass
class FacetStep(Step):
    facets: Mapping[FieldLike, Pipeline]

    def compile(self, context: Context) -> Iterator[Stage]:
        body = {
            compile_field(key, context=context): val.build(context=context)
            for key, val in self.facets.items()
        }
        stage = {"$facet": body}
        yield stage


@dataclass
class MatchStep(Step):
    query: dict | Predicate

    def compile(self, context: Context) -> Iterator[Stage]:
        stage = {"$match": compile_query(self.query, context=context)}
        yield stage


@dataclass
class GroupStep(Step):
    by: AnyExpression
    accumulators: Mapping[FieldLike, Accumulator | AccumulatorExpression]

    def compile(self, context: Context) -> Iterator[Stage]:
        yield {
            "$group": {
                "_id": compile_expression(self.by, context=context),
            }
            | {
                compile_field(key, context=context): compile_accumulator(
                    val, context=context
                )
                for key, val in self.accumulators.items()
            },
        }


@dataclass
class LookupStep(Step):
    collection: str | None
    into: FieldLike
    pipeline: Pipeline | None = None
    local_field: FieldLike | None = None
    foreign_field: FieldLike | None = None

    def compile(self, context: Context) -> Iterator[Stage]:
        pipeline = self.pipeline.build(context=context) if self.pipeline else None
        local_field = (
            compile_field(self.local_field, context=context)
            if self.local_field
            else None
        )
        foreign_field = (
            compile_field(self.foreign_field, context=context)
            if self.foreign_field
            else None
        )

        yield {
            "$lookup": nullfree_dict(
                {
                    "from": self.collection,
                    "localField": local_field,
                    "foreignField": foreign_field,
                    "pipeline": pipeline,
                    "as": compile_field(self.into, context=context),
                }
            )
        }


@dataclass(kw_only=True)
class GraphLookupStep(Step):
    collection: str
    into: FieldLike
    start_with: AnyExpression | list[AnyExpression]
    max_depth: int | None = None
    connect_from_field: FieldLike
    connect_to_field: FieldLike
    depth_field: FieldLike | None = None
    restrict_search_with_match: MongoQuery | Predicate | None = None

    def compile(self, context: Context) -> Iterator[Stage]:
        if self.depth_field:
            depth_field = compile_field(self.depth_field, context=context)
        else:
            depth_field = None

        if self.restrict_search_with_match:
            query = compile_query(self.restrict_search_with_match, context=context)
        else:
            query = None

        yield {
            "$graphLookup": nullfree_dict(
                {
                    "from": self.collection,
                    "startWith": compile_expression(self.start_with, context=context),
                    "connectFromField": compile_field(
                        self.connect_from_field, context=context
                    ),
                    "connectToField": compile_field(
                        self.connect_to_field, context=context
                    ),
                    "as": compile_field(self.into, context=context),
                    "maxDepth": self.max_depth,
                    "depthField": depth_field,
                    "restrictSearchWithMatch": query,
                },
            ),
        }


@dataclass
class BucketStep(Step, Generic[T]):
    by: AnyExpression
    boundaries: list[T]
    default: str | None
    output: Mapping[FieldLike, Accumulator | AccumulatorExpression] | None

    def compile(self, context: Context) -> Iterator[Stage]:
        if isinstance(self.output, dict):
            output = {
                compile_field(key, context=context): compile_accumulator(
                    val, context=context
                )
                for key, val in self.output.items()
            }
        else:
            output = None

        yield {
            "$bucket": {
                "groupBy": compile_path(self.by, context=context),
                "boundaries": self.boundaries,
            }
            | nullfree_dict(
                {
                    "default": self.default,
                    "output": output,
                }
            )
        }


@dataclass
class BucketAutoStep(Step):
    by: AnyExpression
    buckets: int
    output: Mapping[FieldLike, Accumulator | AccumulatorExpression] | None = None
    granularity: str | None = None

    def compile(self, context: Context) -> Iterator[Stage]:
        if self.output:
            output = {
                compile_field(key, context=context): compile_accumulator(
                    val, context=context
                )
                for key, val in self.output.items()
            }
        else:
            output = None

        yield {
            "$bucketAuto": nullfree_dict(
                {
                    "groupBy": compile_expression(self.by, context=context),
                    "buckets": self.buckets,
                    "output": output,
                    "granularity": self.granularity,
                },
            ),
        }


@dataclass
class ProjectStep(Step):
    projection: (
        type[Model] | Mapping[FieldLike, AnyExpression] | list[Aliased[AnyExpression]]
    )

    def compile(self, context: Context) -> Iterator[Stage]:
        match self.projection:
            case list():
                projection = {
                    compile_field(alias.ref, context=context): compile_expression(
                        alias.value, context=context
                    )
                    for alias in self.projection
                }

            case Mapping():
                projection = {
                    compile_field(field, context=context): compile_expression(
                        expr, context=context
                    )
                    for field, expr in self.projection.items()
                }
            case _:
                projection = dict.fromkeys(get_mapper(self.projection).db_fields, True)
        yield {"$project": {"_id": False} | projection}


@dataclass
class UnwindStep(Step):
    field: Field | str
    include_array_index: Field | str | None = None
    preserve_null_and_empty_arrays: bool | None = None

    def compile(self, context: Context) -> Iterator[Stage]:
        if self.include_array_index:
            include_array_index = compile_path(
                self.include_array_index, context=context
            )
        else:
            include_array_index = None

        yield {
            "$unwind": drop_missing(
                {
                    "path": compile_path(self.field, context=context),
                }
                | nullfree_dict(
                    {
                        "includeArrayIndex": include_array_index,
                        "preserveNullAndEmptyArrays": self.preserve_null_and_empty_arrays,
                    }
                ),
            ),
        }


@dataclass
class SetStep(Step):
    fields: Mapping[FieldLike, AnyExpression]

    def compile(self, context: Context) -> Iterator[Stage]:
        yield {
            "$set": {
                compile_field(field, context=context): compile_expression(
                    expression, context=context
                )
                for field, expression in self.fields.items()
            }
        }


@dataclass
class UnsetStep(Step):
    fields: list[Field | str]

    def compile(self, context: Context) -> Iterator[Stage]:
        yield {
            "$unset": [compile_field(field, context=context) for field in self.fields]
        }


@dataclass
class CountStep(Step):
    output: Field | str

    def compile(self, context: Context) -> Iterator[Stage]:
        yield {
            "$count": compile_field(self.output, context=context),
        }


@dataclass
class SortStep(Step):
    spec: SortPayload

    def compile(self, context: Context) -> Iterator[Stage]:
        spec = normalize_sort(self.spec, context=context)
        yield {
            "$sort": spec,
        }
