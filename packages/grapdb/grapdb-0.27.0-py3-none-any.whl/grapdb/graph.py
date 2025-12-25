import textwrap
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)


class Function:
    def __init__(self, name: str, sql: str):
        self.name = name
        self.sql = sql

    def __repr__(self) -> str:
        return "Function({!r})".format(self.name)


class Enum:
    def __init__(
        self,
        schema: str,
        name: str,
        initial_values: List[str],
        added_values: List[str],
        drop: bool,
    ):
        self.schema = schema
        self.name = name
        self.values = initial_values + added_values
        self.initial_values = initial_values
        self.added_values = added_values
        self.drop = drop

    def __repr__(self) -> str:
        return "Enum({!r}, {!r}, {!r})".format(self.name, self.values, self.drop)

    def to_sql_decl(self) -> List[str]:
        if self.drop:
            return [self.to_sql_drop()]
        values_decl_list = ["'%s'" % value for value in self.values]
        stmts = [
            "CREATE TYPE {}.{} AS ENUM ({});".format(
                self.schema, self.name, ", ".join(values_decl_list)
            )
        ]
        for added_value in self.added_values:
            stmts.append(
                "ALTER TYPE {}.{} ADD VALUE '{}';".format(
                    self.schema, self.name, added_value
                )
            )
        return stmts

    def to_sql_drop(self) -> str:
        return "DROP TYPE {}.{};".format(self.schema, self.name)


class CompositeType:
    def __init__(
        self, schema: str, name: str, fields: List[Tuple[str, "DataType"]], drop: bool
    ):
        self.schema = schema
        self.name = name
        self.fields = fields
        self.drop = drop

    def __repr__(self) -> str:
        return "Type({!r}, {!r}, {!r})".format(self.name, self.fields, self.drop)

    def to_sql_decl(self) -> List[str]:
        if self.drop:
            return [self.to_sql_drop()]
        fields_decl_list = [
            f"{field[0]} {graph_type_to_sql_type(field[1])}" for field in self.fields
        ]
        stmts = [
            "CREATE TYPE {}.{} AS ({});".format(
                self.schema, self.name, ", ".join(fields_decl_list)
            )
        ]
        return stmts

    def to_sql_drop(self) -> str:
        return "DROP TYPE {}.{};".format(self.schema, self.name)


class Array:
    def __init__(self, element_type: "DataType"):
        self.element_type = element_type

    def __repr__(self) -> str:
        return "Array({!r})".format(self.element_type)


class ColoRef:
    """
    Indicates that a reference to a row is also guaranteed to be colocated.
    """

    def __init__(self, ref: "Vertex"):
        self.ref = ref

    def __repr__(self) -> str:
        return "ColoRef({!r})".format(self.ref)


DataType = Union[str, Array, ColoRef, CompositeType, Enum, "Vertex"]


class Column:
    """
    Represents a DB table column.
    """

    def __init__(
        self,
        name: str,
        data_type: DataType,
        nullable: bool,
        default: Optional[str],
        primary_key: bool,
        drop: bool,
    ) -> None:
        self.name = name
        self.data_type = data_type
        self.nullable = nullable
        self.default = default
        self.primary_key = primary_key
        self.drop = drop

    def __repr__(self) -> str:
        return "Column({!r}, {!r}, {!r}, {!r})".format(
            self.name, self.data_type, self.nullable, self.default
        )

    def decl(self) -> str:
        sql_type = graph_type_to_sql_type(self.data_type)
        return '"{}" {}{}{}'.format(
            self.name,
            sql_type,
            " NOT NULL" if not self.nullable else "",
            " DEFAULT {}".format(self.default) if self.default else "",
        )

    def constraint_decl(self) -> Optional[str]:
        if isinstance(self.data_type, (ColoRef, Vertex)):
            if self.nullable:
                return (
                    "CHECK ("
                    f'(("{self.name}").id IS NOT NULL AND '
                    f'("{self.name}").vshard IS NOT NULL) OR '
                    f'(("{self.name}").id IS NULL AND '
                    f'("{self.name}").vshard IS NULL)) NOT VALID'
                )
            else:
                return (
                    "CHECK ("
                    f'("{self.name}").id IS NOT NULL AND '
                    f'("{self.name}").vshard IS NOT NULL) NOT VALID'
                )
        else:
            return None


def graph_type_to_sql_type(data_type: DataType) -> str:
    if isinstance(data_type, (ColoRef, Vertex)):
        return "gid"
    elif isinstance(data_type, Enum):
        return "{}.{}".format(data_type.schema, data_type.name)
    elif isinstance(data_type, CompositeType):
        return "{}.{}".format(data_type.schema, data_type.name)
    elif isinstance(data_type, Array):
        return "{}[]".format(graph_type_to_sql_type(data_type.element_type))
    else:
        assert isinstance(data_type, str), data_type
        lowered_data_type = data_type.lower()
        if lowered_data_type == "binary":
            return "bytea"
        else:
            return data_type


class Index:
    """Maps to a table index."""

    def __init__(
        self,
        name: str,
        cols: List[str],
        method: str,
        unique: bool,
        predicate: Optional[str],
        drop: bool,
    ) -> None:
        assert isinstance(name, str)
        assert isinstance(cols, list)
        assert len(cols) > 0
        for col in cols:
            assert isinstance(col, str)
        assert isinstance(method, str)
        assert isinstance(unique, bool)
        assert predicate is None or isinstance(predicate, str)
        assert isinstance(drop, bool)
        self.name = name
        self.cols = cols
        self.method = method
        self.unique = unique
        self.predicate = predicate
        self.drop = drop

    def __repr__(self) -> str:
        return "Index({!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.name, self.cols, self.method, self.unique, self.predicate, self.drop
        )


class Counter:
    def __init__(self, edge_name: str, name: str, cols: List[str], drop: bool) -> None:
        assert isinstance(edge_name, str)
        assert isinstance(name, str)
        assert isinstance(cols, list)
        for col in cols:
            assert isinstance(col, str)
        assert isinstance(drop, bool)
        self.edge_name = edge_name
        self.name = name
        self.cols = cols
        self.drop = drop

    def get_full_name(self) -> str:
        return "{}_counter_{}".format(self.edge_name, self.name)

    def __repr__(self) -> str:
        return "Counter({!r}, {!r}, {!r}, {!r})".format(
            self.edge_name, self.name, self.cols, self.drop
        )


class Vertex:
    """
    Maps the vertex of a graph to a SQL Table.

    By default, every vertex will have an id, vshard, and data column. Using
    (id, vshard) a vertex can be uniquely identified assuming the correct shard
    is being queried.

    name: Name of the table.
    extra_cols: Additional table columns.
    entry_point: A table column that can serve as a unique look up key for the
        vertex.
    data_keys: JSON keys that will be present in the data JSONB column.
    """

    base_cols = [
        Column("gid", "gid", False, None, True, False),
        Column("data", "JSONB", False, "'{}'", False, False),
    ]

    def __init__(
        self,
        schema: str,
        name: str,
        extends: Optional["Vertex"],
        extra_cols: List[Column],
        entry_point: Optional[Column],
        data_keys: List[str],
        indexes: List[Index],
        drop: bool,
    ) -> None:
        assert isinstance(name, str)
        assert extends is None or isinstance(extends, Vertex)
        assert isinstance(extra_cols, list)
        if extra_cols:
            for extra_col in extra_cols:
                assert isinstance(extra_col, Column)
        assert entry_point is None or isinstance(entry_point, Column)
        if entry_point:
            for extra_col in extra_cols:
                if extra_col == entry_point:
                    break
            else:
                raise AssertionError("entry_point %r is not a column." % entry_point)
        assert isinstance(data_keys, list)
        if data_keys:
            for data_key in data_keys:
                assert isinstance(data_key, str)

        self.schema = schema
        self.name = name
        self.table_name = '{}."{}"'.format(self.schema, self.name)
        self.extends = extends
        self.cols = self.base_cols + extra_cols
        self.extra_cols = extra_cols
        self.entry_point = entry_point
        self.data_keys = data_keys
        self.indexes = indexes
        self.drop = drop
        # The vertices that reference this as their extends source.
        self.extends_backrefs: List[Vertex] = []
        # The counters that reference an edge with this vertex as source.
        self.counter_backrefs: List[Counter] = []

    def add_extends_backref(self, backref: "Vertex") -> None:
        self.extends_backrefs.append(backref)

    def add_counter_backref(self, backref: "Counter") -> None:
        self.counter_backrefs.append(backref)

    def __repr__(self) -> str:
        return "Vertex({!r}, {!r}, {!r}, {!r}, {!r}, {!r}".format(
            self.name,
            self.extends,
            self.cols,
            self.entry_point,
            self.data_keys,
            self.drop,
        )

    def has_colos(self) -> bool:
        if self.extends is not None:
            return True
        else:
            for col in self.cols:
                if isinstance(col.data_type, ColoRef):
                    return True
        return False

    def to_sql_stmt_create_base(self) -> List[str]:
        if self.drop:
            return [self.to_sql_stmt_drop()]
        tbl_stmt = "CREATE TABLE {} (\n".format(self.table_name)
        for col in self.base_cols:
            tbl_stmt += "  {},\n".format(col.decl())
        tbl_stmt += "  PRIMARY KEY (gid),\n"
        if self.extends is not None:
            tbl_stmt += "  FOREIGN KEY (gid) REFERENCES {} (gid),\n".format(
                self.extends.table_name
            )
        tbl_stmt += "  CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)\n);"
        stmts = [tbl_stmt]
        if self.extends is None:
            seq_stmt = (
                "CREATE SEQUENCE {0}.{1}_gid_id_seq OWNED BY {0}.{1}.gid;".format(
                    self.schema,
                    self.name,
                )
            )
            stmts.append(seq_stmt)
            trig_stmt = textwrap.dedent(
                """\
                CREATE TRIGGER {2}_insert_trigger
                  BEFORE INSERT ON {0}
                  FOR EACH ROW
                  EXECUTE PROCEDURE
                    gid_pk_insert_trig("{1}.{2}_gid_id_seq");""".format(
                    self.table_name, self.schema, self.name
                )
            )
            stmts.append(trig_stmt)
        return stmts

    def to_sql_stmt_create_alters(self) -> List[str]:
        if self.drop:
            return []
        stmts = []
        for col in self.extra_cols:
            if col.drop:
                stmt = 'ALTER TABLE {} DROP COLUMN "{}";'.format(
                    self.table_name,
                    col.name,
                )
                stmts.append(stmt)
            else:
                stmt = "ALTER TABLE {} ADD COLUMN {};".format(
                    self.table_name,
                    col.decl(),
                )
                stmts.append(stmt)
                constraint_decl = col.constraint_decl()
                if constraint_decl:
                    stmt = "ALTER TABLE {} ADD CONSTRAINT {}_ctype_check {};".format(
                        self.table_name, col.name, constraint_decl
                    )
                    stmts.append(stmt)
        return stmts

    def to_sql_stmt_create_index(self) -> List[str]:
        if self.drop:
            return []
        if self.entry_point:
            index_stmt = (
                "CREATE UNIQUE INDEX CONCURRENTLY {}__entry_point "
                "ON {} USING btree ({});".format(
                    self.name, self.table_name, self.entry_point.name
                )
            )
            indexes = [index_stmt]
        else:
            indexes = []
        for index in self.indexes:
            index_full_name = "{}__{}".format(self.name, index.name)
            if index.predicate is not None:
                where = " WHERE {}".format(index.predicate)
            else:
                where = ""
            if index.drop:
                sql_stmt = "DROP INDEX CONCURRENTLY {}.{};".format(
                    self.schema, index_full_name
                )
            else:
                sql_stmt = (
                    "CREATE {}INDEX CONCURRENTLY {} "
                    "ON {} USING {} ({}){};".format(
                        "UNIQUE " if index.unique else "",
                        index_full_name,
                        self.table_name,
                        index.method,
                        _mk_index_cols_list(index.cols),
                        where,
                    )
                )
            indexes.append(sql_stmt)
        for col in self.extra_cols:
            if col.drop:
                continue
            dt = col.data_type
            if not isinstance(dt, ColoRef):
                continue
            ref = dt.ref
            index_stmt = (
                "ALTER TABLE {0}.{1} ADD CONSTRAINT {1}_{2}__fk "
                'FOREIGN KEY ("{2}") REFERENCES {0}.{3} (gid);'.format(
                    self.schema, self.name, col.name, ref.name
                )
            )
            indexes.append(index_stmt)
        return indexes

    def to_sql_stmt_drop(self) -> str:
        return "DROP TABLE {};".format(self.table_name)


class Edge:
    """
    Definitions:
        - min_cols: The minimum set of columns for a valid edge.
        - base_cols: The columns in the create table stmt.
          - min_cols + other PK cols.
        - extra_cols: All columns not in min_cols including PK ones.

    Invariants:
        - min_cols INTERSECT extra_cols = null set, i.e. DISJOINT
        - min_cols INTERSECT base_cols = min_cols
        - base_cols - min_cols = extra_pk_cols
        - extra_cols INTERSECT base_cols = extra_pk_cols
    """

    min_cols = [
        Column("src", "gid", False, None, True, False),
        Column("tgt", "gid", False, None, True, False),
        Column("data", "JSONB", False, "'{}'", False, False),
    ]

    def __init__(
        self,
        schema: str,
        name: str,
        src: Vertex,
        tgt: Vertex,
        extra_cols: List[Column],
        data_keys: List[str],
        indexes: List[Index],
        counters: List[Counter],
        drop: bool,
    ) -> None:
        assert isinstance(name, str)
        assert isinstance(src, Vertex)
        assert isinstance(tgt, Vertex)
        assert isinstance(extra_cols, list)
        pk_cols = []
        if extra_cols:
            for extra_col in extra_cols[:]:
                assert isinstance(extra_col, Column)
                if extra_col.primary_key:
                    pk_cols.append(extra_col)
        self.base_cols = self.min_cols[:] + pk_cols
        assert isinstance(data_keys, list)
        if data_keys:
            for data_key in data_keys:
                assert isinstance(data_key, str)
        if indexes:
            for index in indexes:
                assert isinstance(index, Index)
        if counters:
            for counter in counters:
                assert isinstance(counter, Counter)
        self.schema = schema
        self.name = name
        self.table_name = '{}."{}"'.format(self.schema, self.name)
        self.src = src
        self.tgt = tgt
        self.cols = self.base_cols[:]
        for col in extra_cols:
            if col not in self.cols:
                self.cols.append(col)
        self.extra_cols = extra_cols
        self.data_keys = data_keys
        self.indexes = indexes
        self.counters = counters
        self.drop = drop

    def __repr__(self) -> str:
        return "Edge({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}".format(
            self.name,
            self.src.name,
            self.tgt.name,
            self.cols,
            self.data_keys,
            self.indexes,
            self.counters,
            self.drop,
        )

    def to_sql_stmt_create_base(self) -> List[str]:
        if self.drop:
            return [self.to_sql_stmt_drop()]
        stmt = "CREATE TABLE {} (\n".format(self.table_name)
        for col in self.base_cols:
            stmt += "  {},\n".format(col.decl())
        pk_cols = [col.name for col in self.base_cols if col.primary_key]
        stmt += "  PRIMARY KEY ({}),\n".format(", ".join(pk_cols))
        stmt += "  FOREIGN KEY (src) REFERENCES {} (gid),\n".format(self.src.table_name)
        stmt += "  CHECK ((src).id IS NOT NULL AND (src).vshard IS NOT NULL),\n"
        stmt += "  CHECK ((tgt).id IS NOT NULL AND (tgt).vshard IS NOT NULL)\n"
        stmt += ");"
        stmts = [stmt]
        for counter in self.counters:
            stmts.extend(counter_table_stmts(self, counter))
        return stmts

    def to_sql_stmt_create_alters(self) -> List[str]:
        if self.drop:
            return []
        stmts = []
        for col in self.extra_cols:
            if col.primary_key:
                continue
            if col.drop:
                stmt = 'ALTER TABLE {} DROP COLUMN "{}";'.format(
                    self.table_name,
                    col.name,
                )
                stmts.append(stmt)
            else:
                stmt = "ALTER TABLE {} ADD COLUMN {};".format(
                    self.table_name,
                    col.decl(),
                )
                stmts.append(stmt)
                constraint_decl = col.constraint_decl()
                if constraint_decl:
                    stmt = "ALTER TABLE {} ADD CONSTRAINT {}_ctype_check {};".format(
                        self.table_name, col.name, constraint_decl
                    )
                    stmts.append(stmt)
        return stmts

    def to_sql_stmt_create_index(self) -> List[str]:
        if self.drop:
            return []
        sql_stmts = []
        for index in self.indexes:
            index_full_name = "{}__{}".format(self.name, index.name)
            if index.predicate is not None:
                where = " WHERE {}".format(index.predicate)
            else:
                where = ""
            if index.drop:
                sql_stmt = "DROP INDEX CONCURRENTLY {}.{};".format(
                    self.schema, index_full_name
                )
            else:
                sql_stmt = (
                    "CREATE {}INDEX CONCURRENTLY {} "
                    "ON {} USING {} (src, {}){};".format(
                        "UNIQUE " if index.unique else "",
                        index_full_name,
                        self.table_name,
                        index.method,
                        _mk_index_cols_list(index.cols),
                        where,
                    )
                )
            sql_stmts.append(sql_stmt)
        for col in self.extra_cols:
            dt = col.data_type
            if not isinstance(dt, ColoRef):
                continue
            ref = dt.ref
            sql_stmt = (
                "ALTER TABLE {0}.{1} ADD CONSTRAINT {1}_{2}__fk "
                'FOREIGN KEY ("{2}") REFERENCES {0}.{3} (gid);'.format(
                    self.schema, self.name, col.name, ref.name
                )
            )
            sql_stmts.append(sql_stmt)
        return sql_stmts

    def to_sql_stmt_drop(self) -> str:
        return "DROP TABLE {};".format(self.table_name)


def _mk_index_cols_list(cols: List[str]) -> str:
    """
    HACK: This function escapes plain index columns (just a column name, no
    function or operator). It's necessary for column names such as "user" which
    conflict with a built-in postgres function.

    It's a hack because it only applies to plain index columns.
    """
    escaped_cols = []
    for col in cols:
        if "(" not in col and " " not in col and '"' not in col:
            escaped_cols.append(f'"{col}"')
        else:
            escaped_cols.append(col)
    return ", ".join(escaped_cols)


def counter_table_stmts(edge: Edge, counter: Counter) -> List[str]:
    counter_table_name = counter.get_full_name()
    counter_table_name_with_schema = "{}.{}".format(edge.schema, counter_table_name)
    if counter.drop:
        return ["DROP TABLE {};".format(counter_table_name_with_schema)]
    counter_table_pkeys = ["src"] + counter.cols
    counter_table_pkeys_strlist = ", ".join(counter_table_pkeys)

    stmts = []
    create_table_stmt = "CREATE TABLE {} (\n".format(counter_table_name_with_schema)
    edge_cols_lookup = {col.name: col for col in edge.cols}
    for col_name in counter_table_pkeys:
        create_table_stmt += "  {},\n".format(edge_cols_lookup[col_name].decl())
    create_table_stmt += "  count Integer,\n"
    create_table_stmt += "  PRIMARY KEY ({}),\n".format(counter_table_pkeys_strlist)
    create_table_stmt += "  FOREIGN KEY (src) REFERENCES {} (gid)\n".format(
        edge.src.table_name
    )
    create_table_stmt += ");"
    stmts.append(create_table_stmt)

    trigger_stmt = """\
CREATE FUNCTION {0}_count() RETURNS trigger
   LANGUAGE plpgsql AS
$$BEGIN
   IF TG_OP = 'INSERT' THEN
      INSERT INTO {0} ({1}, count)
        VALUES ({2}, 1)
        ON CONFLICT ({1})
        DO UPDATE SET count = {0}.count + 1;
      RETURN NEW;
   ELSIF TG_OP = 'DELETE' THEN
      UPDATE {0}
        SET count = count - 1
        WHERE {3};
      RETURN OLD;
   ELSIF TG_OP = 'UPDATE' THEN
      UPDATE {0}
        SET count = count - 1
        WHERE {3};
      INSERT INTO {0} ({1}, count)
        VALUES ({2}, 1)
        ON CONFLICT ({1})
        DO UPDATE SET count = {0}.count + 1;
      RETURN NEW;
   ELSE
      TRUNCATE {0};
      RETURN NULL;
   END IF;
END;$$;
""".format(
        counter_table_name_with_schema,
        counter_table_pkeys_strlist,
        ", ".join(["NEW." + pkey for pkey in counter_table_pkeys]),
        " and ".join(["{0}=(OLD.{0})".format(pkey) for pkey in counter_table_pkeys]),
    )
    stmts.append(trigger_stmt)

    mod_stmt = """\
CREATE CONSTRAINT TRIGGER {0}_mod
   AFTER INSERT OR UPDATE OR DELETE ON {1}
   DEFERRABLE INITIALLY DEFERRED
   FOR EACH ROW EXECUTE PROCEDURE {2}_count();
""".format(
        counter_table_name, edge.table_name, counter_table_name_with_schema
    )
    stmts.append(mod_stmt)

    trunc_stmt = """\
CREATE TRIGGER {0}_trunc AFTER TRUNCATE ON {1}
   FOR EACH STATEMENT EXECUTE PROCEDURE {2}_count();
""".format(
        counter_table_name, edge.table_name, counter_table_name_with_schema
    )
    stmts.append(trunc_stmt)

    return stmts


class Graph:
    def __repr__(self) -> str:
        return "Graph({!r}, {!r})".format(self.vertices, self.edges)

    def __init__(
        self,
        schema: str,
        fns: Dict[str, Function],
        enums: Dict[str, Enum],
        ctypes: Dict[str, CompositeType],
        vertices: Dict[str, Vertex],
        edges: Dict[str, Edge],
    ) -> None:
        self.schema = schema
        self.fns: Dict[str, Function] = fns
        self.enums: Dict[str, Enum] = enums
        self.ctypes: Dict[str, CompositeType] = ctypes
        self.vertices: Dict[str, Vertex] = vertices
        self.edges: Dict[str, Edge] = edges

    def to_sql_stmt_create_prereqs(self) -> List[str]:
        create_type_gid_stmt = textwrap.dedent(
            """\
            CREATE TYPE gid AS (
              id BigInt,
              vshard SmallInt
            );"""
        )

        create_gid_pk_insert_trig_stmt = textwrap.dedent(
            """\
            CREATE FUNCTION gid_pk_insert_trig() RETURNS trigger LANGUAGE plpgsql AS
              $$BEGIN
               IF (NEW.gid).id IS NULL THEN
                NEW.gid = (nextval(TG_ARGV[0]), (NEW.gid).vshard);
               END IF;
               RETURN NEW;
            END;$$;"""
        )
        stmts = [create_type_gid_stmt, create_gid_pk_insert_trig_stmt]
        return stmts + [fn.sql for fn in self.fns.values()]

    @staticmethod
    def to_sql_stmt_drop_prereqs() -> List[str]:
        return ["DROP TYPE gid;"]
