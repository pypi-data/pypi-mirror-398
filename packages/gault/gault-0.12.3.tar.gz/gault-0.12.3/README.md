# Gault

A lightweight Object Document Mapper (ODM) for MongoDB with Python type hints and state tracking.

## Features

- Type-safe MongoDB documents with Python type hints
- Field aliasing for database column mapping
- Query operators with Pythonic syntax
- Async manager for CRUD operations
- Aggregation pipeline support
- Automatic state tracking and dirty field detection
- Persistence tracking

## Installation

```bash
pip install gault
```

## Quick Start

```python
from gault import Schema, Model, Field, configure, AsyncManager

# Schema: Persistent documents mapped to MongoDB collections
class Person(Schema, collection="people"):
    id: Field[int] = configure(pk=True)
    name: Field[str]
    age: Field[int] = configure(db_alias="person_age")

# Model: Non-persistent data classes (projections, view models, etc.)
class PersonSummary(Model):
    name: Field[str]
    total: Field[int]

# Create manager
manager = AsyncManager(database)

# Query and modify
person = await manager.get(Person, filter=Person.id == 1)
person.age = 43
await manager.save(person, atomic=True)  # Only updates dirty fields
```

## Schema vs Model

- **Schema**: Persistent MongoDB collections. Requires `collection` parameter and gets registered globally.
- **Model**: Non-persistent data structures for aggregation projections, view models, or intermediate transformations.

## Field Configuration

Fields can be configured with metadata using the `configure()` function:

```python
class Person(Schema, collection="people"):
    # Primary key field - used for filtering in save() operations
    id: Field[int] = configure(pk=True)

    # Regular field
    name: Field[str]

    # Field with database alias (field name differs from DB column)
    age: Field[int] = configure(db_alias="person_age")
```

**Note**: Fields marked with `pk=True` are used as the filter criteria in `save()` operations to identify the document for upsert.

## Querying with Filters

Gault provides multiple ways to filter documents using type-safe field expressions.

### Operator Expressions

Use class fields with comparison operators to build type-safe queries:

```python
# Comparison operators
Person.age == 42          # Equal
Person.age != 30          # Not equal
Person.age < 50           # Less than
Person.age <= 50          # Less than or equal
Person.age > 18           # Greater than
Person.age >= 18          # Greater than or equal
Person.id.in_([1, 2, 3])  # In list
Person.id.nin([4, 5])     # Not in list

# Logical operators
filter = (Person.age >= 18) & (Person.age < 65)  # AND
filter = (Person.name == "Alice") | (Person.name == "Bob")  # OR
filter = ~(Person.age < 18)  # NOT

# Complex expressions
filter = (Person.age >= 18) & ((Person.name == "Alice") | (Person.name == "Bob"))
```

### Pipeline Filters

For advanced queries, use the `Pipeline` API with aggregation stages:

```python
from gault import Pipeline

# Match and sort
pipeline = Pipeline().match(Person.age >= 18).sort(Person.age.asc())

# Pagination
pipeline = Pipeline().skip(10).take(20)

# Group and aggregate
from gault import Sum
pipeline = (
    Pipeline()
    .match(Person.age >= 18)
    .group(by=Person.name, accumulators={"total": Sum(Person.age)})
)

# Multiple stages
pipeline = (
    Pipeline()
    .match(Person.age >= 18)
    .sort(Person.age.desc())
    .take(10)
)
```

### Raw MongoDB Queries

You can also use raw MongoDB query dictionaries:

```python
# Dict filter
filter = {"age": {"$gte": 18}}

# Raw pipeline stages
pipeline = [
    {"$match": {"age": {"$gte": 18}}},
    {"$sort": {"age": -1}},
    {"$limit": 10}
]
```

## AsyncManager Methods

### `find(model, filter=None)`
Finds a single document matching the filter. Returns `None` if not found.

**Filter types**: Operator expression, Pipeline, dict, or list of stages.

```python
# With operator
person = await manager.find(Person, filter=Person.age == 42)

# With pipeline
pipeline = Pipeline().match(Person.age > 30).sort(Person.name.asc())
person = await manager.find(Person, filter=pipeline)

# With dict
person = await manager.find(Person, filter={"age": 42})
```

### `get(model, filter=None)`
Like `find()`, but raises `NotFound` exception if no document is found.

**Filter types**: Operator expression, Pipeline, dict, or list of stages.

```python
try:
    person = await manager.get(Person, filter=Person.id == 123)
except NotFound:
    print("Person not found")
```

### `select(model, filter=None, skip=None, take=None)`
Returns an async iterator of documents matching the filter. Supports pagination.

**Filter types**: Operator expression, Pipeline, dict, or list of stages.

```python
# Operator with in_()
async for person in manager.select(Person, filter=Person.id.in_([1, 2, 3])):
    print(person.name)

# Pipeline
pipeline = Pipeline().match(Person.age >= 18).sort(Person.age.desc())
async for person in manager.select(Person, filter=pipeline, take=10):
    print(person.name)

# Complex filter
filter = (Person.age >= 18) & (Person.age < 65)
async for person in manager.select(Person, filter=filter):
    print(person.name)
```

### `insert(instance)`
Inserts a new document into the database. Only works with `Schema` instances.

```python
new_person = Person(id=1, name="Alice", age=30)
await manager.insert(new_person)
```

### `save(instance, refresh=False, atomic=False)`
Upserts a document using `find_one_and_update`. Supports atomic updates with dirty field tracking.

- **`refresh=False`**: If `True`, refreshes the instance with the document returned from the database
- **`atomic=False`**: If `True` and the instance is already persisted, only updates dirty fields

```python
# Create or update
person = Person(id=1, name="Bob", age=25)
await manager.save(person)

# Later, update only changed fields
person.age = 26
await manager.save(person, atomic=True)  # Only updates 'person_age' field
```

## Persistence and Dirty Fields

Gault tracks the persistence state and modifications of your documents automatically.

### Persistence Tracking

When documents are loaded from the database or saved, they are marked as persisted:

```python
# Loaded from DB - automatically marked as persisted
person = await manager.find(Person, filter=Person.id == 1)
assert manager.persistence.is_persisted(person)

# Newly created - not yet persisted
new_person = Person(id=2, name="Charlie", age=35)
assert not manager.persistence.is_persisted(new_person)

# After saving - marked as persisted
await manager.save(new_person)
assert manager.persistence.is_persisted(new_person)
```

### Dirty Field Tracking

Gault snapshots document state and tracks which fields have been modified:

```python
person = await manager.get(Person, filter=Person.id == 1)

# Modify some fields
person.name = "New Name"
person.age = 50

# Check which fields changed
dirty_fields = manager.state_tracker.get_dirty_fields(person)
# dirty_fields == {'name', 'age'}

# Atomic save only updates changed fields
await manager.save(person, atomic=True)
```

### Atomic Updates

When using `atomic=True`, the `save()` method generates optimal MongoDB updates:

- **Dirty fields**: Updated with `$set`
- **Unchanged fields**: Set with `$setOnInsert` (only on insert, not update)
- **Primary key fields**: Used in the filter

This minimizes race conditions and reduces unnecessary updates.

## Low Level API: Pipeline Composition

While the high-level Schema and Model API provides a convenient way to work with MongoDB, Gault also offers a powerful low-level API for building complex aggregation pipelines independently. This API allows you to compose pipelines using a fluent interface without defining Schema or Model classes.

### Basic Pipeline Construction

The `Pipeline` class provides methods for building MongoDB aggregation pipelines programmatically:

```python
from gault import Pipeline
from gault.predicates import Field
from gault.accumulators import Sum

# Build a pipeline
pipeline = (
    Pipeline()
    .match({"status": "active"})
    .sort({"created_at": -1})
    .take(10)
)

# Convert to MongoDB stages
stages = pipeline.build()
# [
#     {"$match": {"status": "active"}},
#     {"$sort": {"created_at": -1}},
#     {"$limit": 10}
# ]
```

### Available Pipeline Stages

#### Filtering and Matching

```python
# Match with raw dict
Pipeline().match({"age": {"$gte": 18}})

# Match with Field predicates
Pipeline().match(Field("age").gte(18) & Field("status").eq("active"))
```

#### Sorting and Pagination

```python
# Sort by field
Pipeline().sort({"name": 1, "age": -1})
Pipeline().sort("name")  # Ascending by default

# Pagination
Pipeline().skip(20).take(10)

# Random sampling
Pipeline().sample(5)
```

#### Projection

```python
# Dict-based projection
Pipeline().project({"name": True, "age": True})

# Field-based projection
Pipeline().project(
    Field("name").keep(),
    Field("age").keep(alias="person_age"),
    Field("internal_field").remove()
)

# Expression-based projection
Pipeline().project({"fullName": {"$concat": ["$firstName", " ", "$lastName"]}})
```

#### Grouping and Aggregation

```python
# Group with accumulators
from gault.accumulators import Sum, Avg, Count

Pipeline().group(
    {"total": Sum("$amount"), "average": Avg("$score")},
    by="$category"
)

# Group all documents (no grouping key)
Pipeline().group(
    {"count": Count()},
    by=None
)
```

#### Field Manipulation

```python
# Add or update fields
Pipeline().set({"computedField": {"$multiply": ["$price", "$quantity"]}})
Pipeline().set_field("status", "processed")

# Remove fields
Pipeline().unset("_id", "internal_field")
```

#### Array Operations

```python
# Unwind array field
Pipeline().unwind("$tags")

# With options
Pipeline().unwind(
    "$items",
    include_array_index="item_index",
    preserve_null_and_empty_arrays=True
)
```

#### Bucketing

```python
# Manual buckets
Pipeline().bucket(
    by="$age",
    boundaries=[0, 18, 65, 100],
    default="other",
    output={"count": Sum(1)}
)

# Automatic buckets
Pipeline().bucket_auto(
    by="$price",
    buckets=5,
    output={"count": Sum(1), "avgPrice": Avg("$price")}
)
```

#### Joins and Lookups

```python
# Simple lookup
Pipeline().lookup(
    OtherModel,
    local_field="user_id",
    foreign_field="_id",
    into="user_data"
)

# Lookup with sub-pipeline
from gault.pipelines import CollectionPipeline

sub_pipeline = CollectionPipeline("orders").match({"status": "completed"})
Pipeline().lookup(sub_pipeline, into="orders")

# Graph lookup for hierarchical data
Pipeline().graph_lookup(
    OtherModel,
    start_with="$reports_to",
    local_field="reports_to",
    foreign_field="employee_id",
    into="reporting_chain",
    max_depth=5
)
```

#### Faceted Search

```python
# Multiple aggregations in parallel
Pipeline().facet({
    "count": Pipeline().count("total"),
    "avgPrice": Pipeline().group({"value": Avg("$price")}, by=None),
    "categories": Pipeline().group({"count": Sum(1)}, by="$category")
})
```

#### Other Stages

```python
# Count documents
Pipeline().count("total")

# Union with another collection
Pipeline().union_with(OtherModel)

# Replace document
Pipeline().replace_with({"newField": "$existingField"})

# Raw stage (for unsupported operations)
Pipeline().raw({"$customStage": {"option": "value"}})
```

### Pipeline Composition

Pipelines are immutable and chainable, making composition elegant:

```python
# Build pipelines incrementally
base = Pipeline().match({"type": "user"})
active_users = base.match({"status": "active"})
premium_users = active_users.match({"plan": "premium"})

# Use pipe() for custom transformations
def add_pagination(p: Pipeline, page: int, size: int) -> Pipeline:
    return p.skip(page * size).take(size)

pipeline = Pipeline().match({"status": "active"}).pipe(add_pagination, 2, 20)
```

### Working with Field References

The low-level API provides `Field` for building queries without Schema classes:

```python
from gault.predicates import Field

# Field predicates
query = Field("age").gte(18) & Field("country").in_(["US", "CA"])
Pipeline().match(query)

# Field references in expressions
Pipeline().project({
    "fullName": {"$concat": [Field("firstName"), " ", Field("lastName")]}
})
```

### Using with AsyncManager

You can use low-level pipelines with `AsyncManager` by passing them directly:

```python
from gault import AsyncManager

manager = AsyncManager(database)

# Pass pipeline to manager methods
pipeline = Pipeline().match({"status": "active"}).sort({"created_at": -1})
results = await manager.select(MyModel, filter=pipeline)

# Or build stages manually
stages = pipeline.build()
cursor = database["collection"].aggregate(stages)
```

### In-Memory Pipeline Testing

Use `Pipeline.documents()` to work with in-memory data:

```python
# Create pipeline with test data
pipeline = Pipeline.documents(
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 25},
    {"id": 3, "name": "Charlie", "age": 35}
).match(Field("age").gte(30))

stages = pipeline.build()
# [
#     {"$documents": [{"id": 1, ...}, {"id": 2, ...}, {"id": 3, ...}]},
#     {"$match": {"age": {"$gte": 30}}}
# ]
```

### Accumulators

Gault provides accumulator classes for use in `group()` and `bucket()` stages:

```python
from gault.accumulators import (
    AddToSet, Avg, Bottom, BottomN, Count, First, Last,
    Max, Min, Push, Sum, Top, TopN
)

Pipeline().group(
    {
        "total": Sum("$amount"),
        "average": Avg("$score"),
        "unique_tags": AddToSet("$tag"),
        "all_items": Push("$item"),
        "highest": Max("$value"),
        "lowest": Min("$value"),
        "first_seen": First("$timestamp"),
        "last_seen": Last("$timestamp")
    },
    by="$category"
)
```

### Expression Operators

For complex expressions, Gault provides numerous expression operators:

```python
from gault.expressions import Concat, Multiply, Cond, IfNull

Pipeline().project({
    "fullName": Concat(Field("firstName"), " ", Field("lastName")),
    "totalPrice": Multiply(Field("price"), Field("quantity")),
    "displayName": IfNull(Field("nickname"), Field("firstName")),
    "status": Cond(
        Field("active").eq(True),
        "Active",
        "Inactive"
    )
})
```

## Requirements

- Python >= 3.12
- PyMongo >= 4.15.4

## License

MIT
