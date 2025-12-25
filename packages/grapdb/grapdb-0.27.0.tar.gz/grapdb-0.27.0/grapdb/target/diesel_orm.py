from pathlib import Path
from ..graph import (
    Array,
    ColoRef,
    Column,
    CompositeType,
    DataType,
    Enum,
    Graph,
    Vertex,
)
from code_writer import CodeWriter, fmt_pascal, fmt_underscores


delim = ("{", "}")


def generate(graph: Graph, path: Path) -> None:
    schema_mod = generate_diesel_schema(graph)
    with (path / "schema.rs").open("w") as f:
        f.write(schema_mod)
    model_mod = generate_diesel_model(graph)
    with (path / "model.rs").open("w") as f:
        f.write(model_mod)


def generate_diesel_schema(graph: Graph) -> str:
    cw = CodeWriter()

    cw.emit("#![allow(dead_code, unused_imports)]")
    cw.emit("// @generated automatically by grapdb.")
    cw.emit()

    with cw.block("pub mod graph", delim=delim):
        cw.emit()
        with cw.block("pub mod sql_types", delim=delim):
            cw.emit("use diesel::query_builder::QueryId;")
            cw.emit("use diesel::sql_types::*;")
            cw.emit()
            cw.emit("#[derive(diesel::sql_types::SqlType, QueryId)]")
            cw.emit('#[diesel(postgres_type(name = "gid"))]')
            cw.emit("pub struct PgGid;")
            cw.emit()

            for enum in graph.enums.values():
                if enum.drop:
                    continue
                cw.emit("#[derive(diesel::sql_types::SqlType)]")
                cw.emit(
                    f'#[diesel(postgres_type(name = "{fmt_underscores(enum.name)}", schema = "{enum.schema}"))]'
                )
                cw.emit(f"pub struct Pg{fmt_pascal(enum.name)};")
                cw.emit()

            for ctype in graph.ctypes.values():
                if ctype.drop:
                    continue
                cw.emit("#[derive(diesel::sql_types::SqlType, QueryId)]")
                cw.emit(
                    f'#[diesel(postgres_type(name = "{fmt_underscores(ctype.name)}", schema = "{ctype.schema}"))]'
                )
                cw.emit(f"pub struct Pg{fmt_pascal(ctype.name)};")
                cw.emit()

        for vertex in graph.vertices.values():
            if vertex.drop:
                continue
            with cw.block("diesel::table!", delim=delim):
                cw.emit("use diesel::sql_types::*;")
                cw.emit("use super::sql_types::*;")
                cw.emit("use pgvector::sql_types::Vector;")  # FIXME: Only if necessary
                cw.emit()
                with cw.block(
                    f"{vertex.schema}.{fmt_underscores(vertex.name)} (gid)", delim=delim
                ):
                    write_col_list(cw, vertex.cols)
            cw.emit()

        for edge in graph.edges.values():
            if edge.drop:
                continue
            with cw.block("diesel::table!", delim=delim):
                cw.emit("use diesel::sql_types::*;")
                cw.emit("use super::sql_types::*;")
                cw.emit("use pgvector::sql_types::Vector;")  # FIXME: Only if necessary
                cw.emit()
                pks = [
                    mk_field_name(col.name)[0] for col in edge.cols if col.primary_key
                ]
                with cw.block(
                    f'{edge.schema}.{fmt_underscores(edge.name)} ({", ".join(pks)})',
                    delim=delim,
                ):
                    write_col_list(cw, edge.cols)
            cw.emit()

            edge_col_lookup = {col.name: col for col in edge.cols}
            for counter in edge.counters:
                with cw.block("diesel::table!", delim=delim):
                    cw.emit("use diesel::sql_types::*;")
                    cw.emit("use super::sql_types::*;")
                    cw.emit(
                        "use pgvector::sql_types::Vector;"
                    )  # FIXME: Only if necessary
                    cw.emit()
                    items = (
                        ["src -> PgGid"]
                        + [
                            f"{mk_field_name(col_name)[0]} -> {graph_type_to_diesel_sql_type(edge_col_lookup[col_name].data_type)}"
                            for col_name in counter.cols
                        ]
                        + ["count -> Integer"]
                    )
                    counter_col_names = [
                        mk_field_name(col_name)[0] for col_name in counter.cols
                    ]
                    counter_name = f"{fmt_underscores(edge.name)}_counter_{fmt_underscores(counter.name)}"
                    cw.emit_list(
                        items=items,
                        bracket=delim,
                        before=f'{edge.schema}.{counter_name} (src, {", ".join(counter_col_names)})',
                    )
                cw.emit()

        cw.emit()

        for vertex in graph.vertices.values():
            if vertex.drop:
                continue
            if vertex.extends:
                cw.emit(
                    f"diesel::joinable!({fmt_underscores(vertex.name)} -> {fmt_underscores(vertex.extends.name)} (gid));"
                )
            # FIXME: Emit joinables for extends_backrefs and colo-refs?

        for edge in graph.edges.values():
            if edge.drop:
                continue
            cw.emit(
                f"diesel::joinable!({fmt_underscores(edge.name)} -> {fmt_underscores(edge.src.name)} (src));"
            )
            for col in edge.extra_cols:
                if col.drop:
                    continue
                if not isinstance(col.data_type, ColoRef):
                    continue
                cw.emit(
                    f"diesel::joinable!({fmt_underscores(edge.name)} -> {fmt_underscores(col.data_type.ref.name)} ({fmt_underscores(col.name)}));"
                )
            for counter in edge.counters:
                # NOTE: Counter primarily joins with the edge's source vertex,
                # and not the edge itself.
                cw.emit(
                    f"diesel::joinable!({fmt_underscores(edge.name)}_counter_{fmt_underscores(counter.name)} -> {fmt_underscores(edge.src.name)} (src));"
                )
        cw.emit()

        with cw.block(
            before="diesel::allow_tables_to_appear_in_same_query!(", after=");"
        ):
            for vertex in graph.vertices.values():
                if vertex.drop:
                    continue
                cw.emit(f"{fmt_underscores(vertex.name)},")
            for edge in graph.edges.values():
                if edge.drop:
                    continue
                cw.emit(f"{fmt_underscores(edge.name)},")
                for counter in edge.counters:
                    cw.emit(
                        f"{fmt_underscores(edge.name)}_counter_{fmt_underscores(counter.name)},"
                    )

    return cw.render()


def write_col_list(cw: CodeWriter, cols: list[Column]) -> None:
    for col in cols:
        field_name, is_reserved = mk_field_name(col.name)
        if is_reserved:
            cw.emit(f'#[sql_name = "{col.name}"]')
        cw.emit(
            f"{field_name} -> {graph_type_to_diesel_sql_type(col.data_type, col.nullable)},"
        )


def generate_diesel_model(graph: Graph) -> str:
    cw = CodeWriter()

    cw.emit_raw(
        """\
#![allow(dead_code, unused_imports)]
// @generated automatically by grapdb.

use super::schema::graph::sql_types as graph_sql_types;
use diesel::deserialize::{self, FromSql, FromSqlRow};
use diesel::expression::AsExpression;
use diesel::pg::{Pg, PgValue};
use diesel::prelude::*;
use diesel::serialize::{self, ToSql};
use diesel::sql_types;
use diesel_derive_enum;
use pgvector::Vector;
use rand::Rng;
use serde_json;
use sha1::{Digest, Sha1};
use std::io::Write;
use std::vec::Vec;

pub fn random_vshard() -> i16 {
    let mut rng = rand::thread_rng();
    rng.gen_range(-32_768..=32_767)
}

pub fn entry_point_to_vshard(entry_point_val: &str) -> i16 {
    // Convert string to UTF-8 bytes
    let entry_point_encoded = entry_point_val.as_bytes();
    entry_point_bytes_to_vshard(entry_point_encoded)
}

pub fn entry_point_bytes_to_vshard(entry_point_val: &[u8]) -> i16 {
    let mut hasher = Sha1::new();
    hasher.update(entry_point_val);
    let hashed_val = hasher.finalize();
    // Take first two bytes and convert to i16 (little-endian <h in python)
    i16::from_le_bytes([hashed_val[0], hashed_val[1]])
}

#[derive(Debug, Clone, Copy, Eq, PartialEq, Hash, FromSqlRow, AsExpression)]
#[diesel(sql_type = super::schema::graph::sql_types::PgGid)]
pub struct Gid {
    pub id: i64,
    pub vshard: i16,
}

impl FromSql<graph_sql_types::PgGid, Pg> for Gid {
    fn from_sql(bytes: PgValue) -> deserialize::Result<Self> {
        let (id, vshard) = FromSql::<diesel::sql_types::Record<(diesel::sql_types::BigInt, diesel::sql_types::SmallInt)>, Pg>::from_sql(bytes)?;
        Ok(Gid { id, vshard })
    }
}

impl ToSql<graph_sql_types::PgGid, Pg> for Gid {
    fn to_sql<'b>(&'b self, out: &mut serialize::Output<'b, '_, Pg>) -> serialize::Result {
        serialize::WriteTuple::<(diesel::sql_types::BigInt, diesel::sql_types::SmallInt)>::write_tuple(
            &(self.id, self.vshard),
            &mut out.reborrow(),
        )
    }
}

/// For creating a new gid where the DB sets the id.
#[derive(Debug, Clone, Copy, Eq, PartialEq, Hash, FromSqlRow, AsExpression)]
#[diesel(sql_type = super::schema::graph::sql_types::PgGid)]
pub struct NewGid {
    pub id: Option<i64>,
    pub vshard: i16,
}

impl NewGid {
    pub fn new() -> NewGid {
        Self::default()
    }

    pub fn new_colo_with(gid: &Gid) -> NewGid {
        NewGid {
            id: None,
            vshard: gid.vshard,
        }
    }

    pub fn new_for_entry_point(entry_point_val: &str) -> NewGid {
        NewGid {
            id: None,
            vshard: entry_point_to_vshard(entry_point_val),
        }
    }

    pub fn new_for_entry_point_bytes(entry_point_val: &[u8]) -> NewGid {
        NewGid {
            id: None,
            vshard: entry_point_bytes_to_vshard(entry_point_val),
        }
    }
}

impl Default for NewGid {
    fn default() -> Self {
        NewGid {
            id: None,
            vshard: random_vshard(),
        }
    }
}

impl FromSql<graph_sql_types::PgGid, Pg> for NewGid {
    fn from_sql(bytes: PgValue) -> deserialize::Result<Self> {
        let (id, vshard) = FromSql::<
            diesel::sql_types::Record<(
                diesel::sql_types::Nullable<diesel::sql_types::BigInt>,
                diesel::sql_types::SmallInt,
            )>,
            Pg,
        >::from_sql(bytes)?;
        Ok(NewGid { id, vshard })
    }
}

impl ToSql<graph_sql_types::PgGid, Pg> for NewGid {
    fn to_sql<'b>(&'b self, out: &mut serialize::Output<'b, '_, Pg>) -> serialize::Result {
        serialize::WriteTuple::<(
            diesel::sql_types::Nullable<diesel::sql_types::BigInt>,
            diesel::sql_types::SmallInt,
        )>::write_tuple(&(self.id, self.vshard), &mut out.reborrow())
    }
}
"""
    )
    cw.emit()

    for enum in graph.enums.values():
        if enum.drop:
            continue

        cw.emit("#[derive(Debug, Clone, PartialEq, diesel_derive_enum::DbEnum)]")
        cw.emit(f'#[ExistingTypePath = "graph_sql_types::Pg{fmt_pascal(enum.name)}"]')
        with cw.block(f"pub enum {fmt_pascal(enum.name)}", delim=delim):
            for field_name in enum.values:
                cw.emit(f"{fmt_pascal(field_name)},")
        cw.emit()

    for ctype in graph.ctypes.values():
        if ctype.drop:
            continue
        cw.emit("#[derive(Debug, Clone, PartialEq, FromSqlRow, AsExpression)]")
        cw.emit(f"#[diesel(sql_type = graph_sql_types::Pg{fmt_pascal(ctype.name)})]")
        with cw.block(f"pub struct {fmt_pascal(ctype.name)}", delim=delim):
            field_names_list = []
            field_types_list = []
            for field_name, field_data_type in ctype.fields:
                final_field_name, _ = mk_field_name(field_name)
                cw.emit(
                    f"pub {fmt_underscores(final_field_name)}: {graph_type_to_rust_type(field_data_type)},"
                )
                field_names_list.append(final_field_name)
                field_types_list.append(
                    graph_type_to_diesel_sql_type(
                        field_data_type,
                        nullable=False,
                        prefix_user_defined_type="graph_sql_types::",
                        prefix_diesel_sql_type="diesel::sql_types::",
                    )
                )
            field_names_csv = ", ".join(field_names_list)
            field_names_with_self_csv = ", ".join(
                "&self." + name for name in field_names_list
            )
            field_types_csv = ", ".join(field_types_list)
        cw.emit()
        with cw.block(
            f"impl FromSql<graph_sql_types::Pg{fmt_pascal(ctype.name)}, Pg> for {fmt_pascal(ctype.name)}",
            delim=delim,
        ):
            with cw.block(
                "fn from_sql(bytes: PgValue) -> deserialize::Result<Self>", delim=delim
            ):
                cw.emit(
                    f"let ({field_names_csv}) = FromSql::<diesel::sql_types::Record<({field_types_csv})>, Pg>::from_sql(bytes)?;"
                )
                cw.emit(f"Ok({fmt_pascal(ctype.name)} {{ {field_names_csv} }})")
        cw.emit()
        with cw.block(
            f"impl ToSql<graph_sql_types::Pg{fmt_pascal(ctype.name)}, Pg> for {fmt_pascal(ctype.name)}",
            delim=delim,
        ):
            with cw.block(
                "fn to_sql<'b>(&'b self, out: &mut serialize::Output<'b, '_, Pg>) -> serialize::Result",
                delim=delim,
            ):
                with cw.block(
                    f"serialize::WriteTuple::<({field_types_csv})>::write_tuple(",
                    after=")",
                ):
                    cw.emit(f"&({field_names_with_self_csv}),")
                    cw.emit("&mut out.reborrow(),")
        cw.emit()

    for entity in list(graph.vertices.values()) + list(graph.edges.values()):
        if entity.drop:
            continue
        cw.emit("#[derive(Debug, Clone, PartialEq, Queryable, Selectable, Insertable)]")
        cw.emit(
            f"#[diesel(table_name = super::schema::graph::{fmt_underscores(entity.name)})]"
        )
        cw.emit("#[diesel(check_for_backend(Pg))]")
        with cw.block(f"pub struct {fmt_pascal(entity.name)}", delim=delim):
            for col in entity.cols:
                field_name, _ = mk_field_name(col.name)
                cw.emit(f"pub {field_name}: {column_type_to_rust_type(col)},")
        cw.emit()

        cw.emit("#[derive(Insertable)]")
        cw.emit(
            f"#[diesel(table_name = super::schema::graph::{fmt_underscores(entity.name)})]"
        )
        with cw.block(f"pub struct {fmt_pascal("new_" + entity.name)}", delim=delim):
            for col in entity.cols:
                field_name, _ = mk_field_name(col.name)
                cw.emit(
                    f"pub {field_name}: {column_type_to_rust_insertion_type(entity, col)},"
                )
        cw.emit()

    return cw.render()


# ----


def check_reserved_symbol(name: str) -> bool:
    return name in {"type"}


def mk_field_name(name: str) -> tuple[str, bool]:
    """Handles renaming fields that conflict with reserved keywords."""
    is_reserved = check_reserved_symbol(name)
    safe_name = name + "_" if is_reserved else name
    return fmt_underscores(safe_name), is_reserved


def graph_type_to_diesel_sql_type(
    data_type: DataType,
    nullable: bool = False,
    *,
    prefix_user_defined_type: str = "",
    prefix_diesel_sql_type: str = "",
) -> str:
    if nullable:
        inner_diesel_sql_type = graph_type_to_diesel_sql_type(
            data_type, False, prefix_user_defined_type=prefix_user_defined_type
        )
        return f"Nullable<{inner_diesel_sql_type}>"
    if isinstance(data_type, (ColoRef, Vertex)):
        return prefix_user_defined_type + "PgGid"
    elif isinstance(data_type, (Enum, CompositeType)):
        return prefix_user_defined_type + f"Pg{fmt_pascal(data_type.name)}"
    elif isinstance(data_type, Array):
        inner_diesel_sql_type = graph_type_to_diesel_sql_type(
            data_type.element_type, prefix_user_defined_type=prefix_user_defined_type
        )
        return prefix_diesel_sql_type + f"Array<{inner_diesel_sql_type}>"
    else:
        return sql_type_to_diesel_type(
            data_type,
            prefix_user_defined_type=prefix_user_defined_type,
            prefix_diesel_sql_type=prefix_diesel_sql_type,
        )


def sql_type_to_diesel_type(
    sql_type: str,
    *,
    prefix_user_defined_type: str = "",
    prefix_diesel_sql_type: str = "",
) -> str:
    assert not sql_type.endswith("[]"), sql_type
    sql_type_norm = sql_type.lower()
    if sql_type_norm == "text":
        return prefix_diesel_sql_type + "Text"
    elif sql_type_norm == "timestamp":
        return prefix_diesel_sql_type + "Timestamp"
    elif sql_type_norm == "integer":
        return prefix_diesel_sql_type + "Integer"
    elif sql_type_norm == "bigint":
        return prefix_diesel_sql_type + "BigInt"
    elif sql_type_norm == "smallint":
        return prefix_diesel_sql_type + "SmallInt"
    elif sql_type_norm == "bigserial":
        return prefix_diesel_sql_type + "BigInt"
    elif sql_type_norm == "serial":
        return prefix_diesel_sql_type + "Integer"
    elif sql_type_norm == "binary":
        return prefix_diesel_sql_type + "Bytea"
    elif sql_type_norm == "boolean":
        return prefix_diesel_sql_type + "Bool"
    elif sql_type_norm == "gid":
        return prefix_user_defined_type + "PgGid"
    elif sql_type_norm == "jsonb":
        return prefix_diesel_sql_type + "Jsonb"
    elif sql_type_norm.startswith("vector("):
        return prefix_diesel_sql_type + "Vector"
    else:
        return prefix_user_defined_type + sql_type


# --


def graph_type_to_rust_type(data_type: DataType) -> str:
    if isinstance(data_type, (ColoRef, Vertex)):
        return "Gid"
    elif isinstance(data_type, Enum):
        return fmt_pascal(data_type.name)
    elif isinstance(data_type, CompositeType):
        # Assume the composite type has already been defined earlier.
        return fmt_pascal(data_type.name)
    elif isinstance(data_type, Array):
        return "Vec<{}>".format(
            graph_type_to_rust_type(data_type.element_type),
        )
    else:
        return sql_type_to_rust_type(data_type)


def column_type_to_rust_type(column: Column) -> str:
    rust_type = graph_type_to_rust_type(column.data_type)
    if column.nullable:
        return f"Option<{rust_type}>"
    else:
        return rust_type


def column_type_to_rust_insertion_type(data_type: DataType, column: Column) -> str:
    rust_type = graph_type_to_rust_type(column.data_type)
    if column.name == "gid":
        if isinstance(data_type, Vertex) and not data_type.extends:
            return "NewGid"
        else:
            return rust_type
    elif (
        column.nullable
        or column.default
        or (
            isinstance(column.data_type, str)
            and column.data_type.lower().endswith("serial")
        )
    ):
        return f"Option<{rust_type}>"
    else:
        return rust_type


def sql_type_to_rust_type(sql_type: str) -> str:
    assert not sql_type.endswith("[]"), sql_type
    sql_type_norm = sql_type.lower()
    if sql_type_norm == "gid":
        return "Gid"
    elif sql_type_norm == "text":
        return "String"
    elif sql_type_norm == "boolean":
        return "bool"
    elif sql_type_norm == "timestamp":
        return "chrono::NaiveDateTime"
    elif sql_type_norm == "date":
        return "chrono::NaiveDate"
    elif sql_type_norm == "jsonb":
        return "serde_json::Value"
    elif sql_type_norm == "smallint":
        return "i16"
    elif sql_type_norm == "bigint" or sql_type_norm == "bigserial":
        return "i64"
    elif sql_type_norm == "integer" or sql_type_norm == "serial":
        return "i32"
    elif sql_type_norm == "binary":
        return "Vec<u8>"
    elif sql_type_norm.startswith("vector("):
        # FIXME: Vector isn't a first-class type yet.
        return "Vector"
    else:
        return sql_type
