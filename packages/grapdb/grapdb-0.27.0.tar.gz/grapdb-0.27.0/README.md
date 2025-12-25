# GrapDB

A tool for building graph structures on top of Postgres.

## Goals

  * Scale out Postgres for use across many machines.
  * Do not sacrifice Postgres features on single DB shard.
    * A single shard should be a fully featured Postgres instance.
    * Data types & indexes
    * ACID
  * Patterns for efficiently querying within shard and across shards.
  * Multi-shard ACID via two-phase commit.
  * [WIP] Automated cache layer.
  * No dependencies on unofficial Postgres features.
  * Autogenerate bindings for Python (SqlAlchemy) and Rust (Diesel).

## Minimum Requirements

  * Python >= 3.8
  * Postgres >= 9.1 (`ALTER TYPE... ADD VALUE...` support)

## Example

Create `graph.toml`:

```toml
schema = "graph"  # Postgres schema

[vertex.user]
cols = [
    ["username", "Text"],
    ["email", "Text"],
    ["is_subscriber", "Boolean"],
]
# WARNING: This design requires usernames to be immutable.
entry_point = "username"
col.email.nullable = true
col.is_subscriber.default = "false"

[enum.animal_type]
values = ["dog", "cat"]

[vertex.animal]
cols = [
    ["type", "enum:animal_type"],
    ["name", "Text"],
]

[edge.owner]
src = "user"
tgt = "animal"
cols = [
    ["type", "enum:animal_type"],  # Used by `Counter` example below
    ["adopted_on", "Timestamp"],
]
```

Generate SQL migration plan:

```commandline
$ grapdb plan graph.toml

{
  "migration_plan": [
    "CREATE TYPE gid AS (\n  id BigInt,\n  vshard SmallInt\n);",
    "CREATE FUNCTION gid_pk_insert_trig() RETURNS trigger LANGUAGE plpgsql AS\n  $$BEGIN\n   IF (NEW.gid).id IS NULL THEN\n    NEW.gid = (nextval(TG_ARGV[0]), (NEW.gid).vshard);\n   END IF;\n   RETURN NEW;\nEND;$$;",
    "CREATE TYPE graph.animal_type AS ENUM ('dog', 'cat');",
    "CREATE TABLE graph.\"user\" (\n  \"gid\" gid NOT NULL,\n  \"data\" JSONB NOT NULL DEFAULT '{}',\n  PRIMARY KEY (gid),\n  CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)\n);",
    "CREATE SEQUENCE graph.user_gid_id_seq OWNED BY graph.user.gid;",
    "CREATE TRIGGER user_insert_trigger\n  BEFORE INSERT ON graph.\"user\"\n  FOR EACH ROW\n  EXECUTE PROCEDURE\n    gid_pk_insert_trig(\"graph.user_gid_id_seq\");",
    "CREATE TABLE graph.\"animal\" (\n  \"gid\" gid NOT NULL,\n  \"data\" JSONB NOT NULL DEFAULT '{}',\n  PRIMARY KEY (gid),\n  CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)\n);",
    "CREATE SEQUENCE graph.animal_gid_id_seq OWNED BY graph.animal.gid;",
    "CREATE TRIGGER animal_insert_trigger\n  BEFORE INSERT ON graph.\"animal\"\n  FOR EACH ROW\n  EXECUTE PROCEDURE\n    gid_pk_insert_trig(\"graph.animal_gid_id_seq\");",
    "ALTER TABLE graph.\"user\" ADD COLUMN \"username\" Text NOT NULL;",
    "ALTER TABLE graph.\"user\" ADD COLUMN \"email\" Text;",
    "ALTER TABLE graph.\"user\" ADD COLUMN \"is_subscriber\" Boolean NOT NULL DEFAULT false;",
    "ALTER TABLE graph.\"animal\" ADD COLUMN \"type\" graph.animal_type NOT NULL;",
    "ALTER TABLE graph.\"animal\" ADD COLUMN \"name\" Text NOT NULL;",
    "CREATE UNIQUE INDEX CONCURRENTLY user__entry_point ON graph.\"user\" USING btree (username);",
    "CREATE TABLE graph.\"owner\" (\n  \"src\" gid NOT NULL,\n  \"tgt\" gid NOT NULL,\n  \"data\" JSONB NOT NULL DEFAULT '{}',\n  PRIMARY KEY (src, tgt),\n  FOREIGN KEY (src) REFERENCES graph.\"user\" (gid),\n  CHECK ((src).id IS NOT NULL AND (src).vshard IS NOT NULL),\n  CHECK ((tgt).id IS NOT NULL AND (tgt).vshard IS NOT NULL)\n);",
    "ALTER TABLE graph.\"owner\" ADD COLUMN \"type\" graph.animal_type NOT NULL;",
    "ALTER TABLE graph.\"owner\" ADD COLUMN \"adopted_on\" Timestamp NOT NULL;"
  ],
  "drop_plan": [
    "DROP TABLE graph.\"owner\";",
    "DROP TABLE graph.\"animal\";",
    "DROP TABLE graph.\"user\";",
    "DROP TYPE graph.animal_type;",
    "DROP TYPE gid;"
  ]
}
```

Generate Python SQLAlchemy bindings:

```commandline
grapdb sqlalchemy-orm graph.toml .
```

## Concepts

True to its Graph DB aspirations, there are vertices and edges.

### Vertex

Analogous to what would be stored in a traditional RDBMS table. A vertex is
keyed by a Global ID (`Gid`) which is 64 bits of an auto-increment integer, and
16 bits of shard ID. A vertex can have any number of columns as well as a JSONB
column `data`.

#### Look up

A vertex can be looked up by its `Gid`. Additionally, an `entry_point` can be
specified which allows look up by one other text column (or composite type of
text fields; or array of gids) with unique values. Internally, the hash of an
`entry_point` fully determines its shard ID. For this reason, an `entry_point`
column must be treated as immutable once set.

#### Colocation

A vertex `V` that `extends` another vertex `W` guarantees that each of its rows
has a corresponding row with matching `Gid` in `W`. This necessarily guarantees
that rows in `V` are colocated with their corresponding rows in `W`. In other
words, they reside on the same shard.

#### Indices

Indices can be added to a vertex. Indices can specify columns with functions,
indexing method, and a where clause. A query using an index will need to be run
on all shards. A future optimization is to limit the query to one shard if one
of the query-where-clauses bounds the query to a specific shard (e.g. vertex
colocation reference).

#### Mapping to Postgres

A vertex maps to a regular table with a column of composite type for the Gid.
An `entry_point` adds a unique index for the target column.

A `data` JSONB column is allocated automatically for extending the schema
without requiring a migration.

### Edge

A directional edge that connects two vertices together. Similar to a vertex
but includes columns for source and target vertices.

#### Colocation

Edge entries are colocated with the source vertex they're associated with.
Edges can have indexes which allow sorting and filtering on a per source-vertex
basis.

#### Indices

Indices can be added to an edge. Indices can specify columns with functions,
indexing method, and a where clause. An edge index is always key-ed by the
`src` gid so queries will efficiently access a single shard.

#### Mapping to Postgres

An edge maps to a regular table with columns for the source and target vertex
gids.

A `data` JSONB column is allocated automatically for extending the schema
without requiring a migration.

### Columns

Columns define the data that entities (vertices & edges) contain.

#### Available Data Types

  * Text
  * SmallInt
  * Integer
  * BigInt
  * Binary
  * Timestamp
  * Date
  * Vertex: `->vertex`
  * Colocated vertex `-)vertex`
  * Enum: `enum:name`
  * Composite Types: `ctype:name`
  * Array: `type[]`

#### Vertex references and colocation

A column can reference a vertex using the `->` notation. If the vertex is
guaranteed to be colocated with the entity, use the `-)` notation, which will
allow for efficient same-shard joins.

#### Mapping to Postgres

A straightforward mapping to database columns.

### Enums

Enums limit the values for a given column to a finite set of strings. Enums
are stored more efficiently than text.

```toml
[enum.animal_type]
values = [
    "dog",
    "cat"]
added_values = [
    "tiger",
]
```

Note the use of `added_values` when adding enum variants after the initial
migration.

#### Mapping to Postgres

Enums map to Postgres enums. The use of `added_values` creates a migration plan
that utilizes Postgres's `ALTER TYPE... ADD VALUE...` query which can be run on
a live database as it does not require rewriting dependent tables.

### Composite Types

Composite types enable the creation of a new type that is a tuple of types.

```toml
[ctype.point]
fields = [
    ["x", "Integer"],
    ["y", "Integer"],
]
```

#### Mapping to Postgres

Maps directly to Postgres's composite types feature.

### Dropping

Entities and indices can be dropped by marking them as `drop=true`. An explicit
`drop` annotation is preferred over deleting a definition because `drop` adds
the appropriate queries to the migration plan.

`drop` is also useful in development environments to quickly purge and
re-create entities as an entity definition is iterated.

### Counters

A counter is defined on an edge type and tracks the cardinality of the set of
edges matching specific column values (`src` is required).

```toml
[edge.owner.counter.animal_type_count]
cols = ["animal_type"]
```

### Language Generators

Once the graph is specified in `.toml`, GrapDB can generate ORM mappings.
Currently, only SqlAlchemy for Python3 is supported.

## Migration Invariants

The general rule is that your graph config file can expand in definition, but
nothing should ever be mutated or removed.

  * Use `drop` rather than deletion for entities and indices.
  * Do not change a column's data type.
  * Do not change a column's default.
  * Do not change a column's nullability.
  * A new column for an entity must have a default or be nullable.
  * Use `added_values` for expanding enums.

As long as these rules are followed, the `migration_plan` is idempotent and can
be executed after every graph config change.

## Client-Server Architecture

Outside of 2PC transaction, GrapDB does not add any layer between applications
and Postgres servers. For this reason, clients are responsible for:

  * Mapping shard IDs to servers.
  * Mapping virtual shard IDs to shard IDs using
    [jump consistent hashing](https://arxiv.org/pdf/1406.2294.pdf).
  * Extracting the virtual shard ID from a gid.
  * Mapping entry points to virtual shard IDs using a SHA-1 hash.
  * Setting virtual shard IDs for new entities.

### [WIP] pg-2pc-tm

GrapDB's Postgres 2PC Transaction Manager offers a barebones interface for
applications to register a 2pc transaction.

A critical missing feature is its lack of deadlock detection.

## Quirks

### SQLAlchemy interaction with dropped entities

When an entity is marked as dropped, the associated Python definition is also
eliminated. Naturally, references in Python code to the definition should be
removed. However, it can be impossible to remove the definition when it has
been used in a migration script. It's not clear whether the entity should be
retained purely for legacy migration scripts, or whether the migration script
should be removed once unnecessary.

### SQLAlchemy versions

Using the `--sa-version` flag, the generated code can be made suitable for
v1.3 (13), v1.4 (14), or v2.0 (20).
