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
import black
from code_writer import CodeWriter, fmt_pascal, fmt_underscores


preamble = """\
import datetime
from typing import Final, Literal, NamedTuple

from sqlalchemy import (  # pylint: disable=E0401,W0611
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    FetchedValue,
    ForeignKeyConstraint,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship  # pylint: disable=E0401

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    pass

from .graph_orm_base import (
    Base,
    CompositeArray,
    CompositeType,
    CounterMixin,
    EdgeMixin,
    EntryPointMixin,
    ExtendsMixin,
    Gid,
    TGid,
    VertexMixin,
)
"""

preamble_v14 = """\
import datetime
from typing import Final, Literal, NamedTuple

from sqlalchemy import (  # pylint: disable=E0401,W0611
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    FetchedValue,
    ForeignKeyConstraint,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship  # pylint: disable=E0401 

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    pass

from .graph_orm_base import (
    Base,
    CompositeType,
    CounterMixin,
    EdgeMixin,
    EntryPointMixin,
    ExtendsMixin,
    Gid,
    TGid,
    VertexMixin,
)
"""

preamble_v20 = """\
import datetime
from typing import Final, Literal, NamedTuple, Optional

from sqlalchemy import (  # pylint: disable=unused-import,useless-suppression
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    FetchedValue,
    ForeignKeyConstraint,
    Integer,
    LargeBinary,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY  # pylint: disable=unused-import,useless-suppression
from sqlalchemy.orm import (  # pylint: disable=unused-import,useless-suppression
    Mapped,
    mapped_column,
    relationship,
)

try:
    from pgvector.sqlalchemy import Vector  # pylint: disable=unused-import,useless-suppression
except ImportError:
    pass

from .graph_orm_base import (  # pylint: disable=unused-import,useless-suppression
    Base,
    CompositeType,
    CounterMixin,
    EdgeMixin,
    EntryPointMixin,
    ExtendsMixin,
    Gid,
    TGid,
    VertexMixin,
)
"""


delim = (None, None)


def generate(graph: Graph, path: Path, version: int) -> None:
    assert version in {13, 14, 20}
    mod = generate_user_types_module(graph, version)
    with (path / "graph_orm.py").open("w") as f:
        f.write(mod)
    if version == 20:
        source = Path(__file__).parent / "rsrc/graph_orm_base_v20.py"
    elif version == 14:
        source = Path(__file__).parent / "rsrc/graph_orm_base_v14.py"
    else:
        source = Path(__file__).parent / "rsrc/graph_orm_base.py"
    target = path / "graph_orm_base.py"
    with source.open("r") as source_f, target.open("w") as target_f:
        # Disable formatting in case target project uses custom black config.
        target_f.write("# fmt: off\n" + source_f.read())


def generate_user_types_module(graph: Graph, version: int) -> str:
    cw = CodeWriter()
    if version == 20:
        cw.emit_raw(preamble_v20)
    elif version == 14:
        cw.emit_raw(preamble_v14)
    else:
        cw.emit_raw(preamble)
    for enum in graph.enums.values():
        if enum.drop:
            continue
        cw.emit()
        cw.emit()
        sorted_values = sorted(enum.values)
        for value in sorted_values:
            cw.emit(
                f"{enum.name}_{fmt_underscores(value)}: Final[Literal['{value}']] = '{value}'"
            )
        cw.emit_list(
            [repr(value) for value in sorted_values],
            ("[", "]"),
            f"{fmt_pascal(enum.name)}T = Literal",
        )
        cw.emit_list(
            [repr(value) for value in sorted_values],
            ("[", "]"),
            f"_{enum.name}_values: list[{fmt_pascal(enum.name)}T] = ",
        )
        cw.emit(
            '{0}_db_enum_type = Enum(*_{0}_values, name="{0}", schema="{1}")'.format(
                enum.name, enum.schema
            )
        )
        cw.emit(
            f"{enum.name}_values: set[{fmt_pascal(enum.name)}T] = set(_{enum.name}_values)"
        )

    for ctype in graph.ctypes.values():
        if ctype.drop:
            continue
        cw.emit()
        cw.emit()
        cw.emit_list(
            [
                f'Column("{field[0]}", {graph_type_to_sa_type(field[1], version >= 14)})'
                for field in ctype.fields
            ],
            ("[", "]"),
            before=f'{fmt_pascal(ctype.name)} = CompositeType("{ctype.name}", ',
            after=f', schema="{ctype.schema}")',
        )
        cw.emit(f"{fmt_pascal(ctype.name)}T = {graph_type_to_mypy_type(ctype)}")

    for vertex in graph.vertices.values():
        if vertex.drop:
            continue
        cw.emit()
        cw.emit()
        parent_classes = ["Base"]
        # Order of classes is important for Python's MRO as they all implement
        # variants of get_vshard().
        if vertex.entry_point is not None:
            parent_classes.append("EntryPointMixin")
        elif vertex.extends is not None:
            parent_classes.append("ExtendsMixin")
        parent_classes.append("VertexMixin")
        cw.emit(
            "class {}({}):".format(fmt_pascal(vertex.name), ", ".join(parent_classes))
        )
        with cw.indent():
            cw.emit("__tablename__ = '{}'".format(vertex.name))
            table_args = []
            if version == 20:
                # This is symmetry with edge definitions. See equivalent code
                # for edge generation for explanation.
                table_args.append(
                    "PrimaryKeyConstraint({})".format(
                        ", ".join(
                            [f"'{col.name}'" for col in vertex.cols if col.primary_key]
                        )
                    )
                )
            if vertex.entry_point is not None:
                table_args.append(
                    "UniqueConstraint('{}')".format(vertex.entry_point.name)
                )
            if vertex.has_colos():
                if vertex.extends:
                    table_args.append(
                        "ForeignKeyConstraint(['gid'], ['{}.gid'])".format(
                            vertex.extends.name
                        )
                    )
                for col in vertex.extra_cols:
                    if col.drop:
                        continue
                    if not isinstance(col.data_type, ColoRef):
                        continue
                    table_args.append(
                        "ForeignKeyConstraint(['{}'], ['{}.gid'])".format(
                            col.name, col.data_type.ref.name
                        )
                    )
            if table_args:
                # NOTE: Manually add final comma to ensure that a one-element
                # tuple has a comma after the first element (otherwise, it's
                # not interpreted as a tuple).
                table_args[-1] += ","
                cw.emit_list(
                    table_args, ("", ""), "__table_args__ = (", ")", skip_last_sep=True
                )
            if vertex.entry_point:
                cw.emit("_entry_point = '{}'".format(vertex.entry_point.name))
            else:
                cw.emit("_entry_point = None")
            for col in vertex.extra_cols:
                if col.drop:
                    continue
                sa_type = graph_type_to_sa_type(col.data_type, version >= 14)
                default_arg = ", server_default=FetchedValue()" if col.default else ""
                nullable_arg = ", nullable=True" if col.nullable else ""
                if version == 20:
                    col_py_type = column_type_to_mypy_type(col)
                    cw.emit(
                        "{}: Mapped[{}] = mapped_column({}{}{})".format(
                            col.name, col_py_type, sa_type, default_arg, nullable_arg
                        )
                    )
                else:
                    cw.emit(
                        "{} = Column({}{}{})".format(
                            col.name, sa_type, default_arg, nullable_arg
                        )
                    )
            for col in vertex.extra_cols:
                if col.drop:
                    continue
                if not isinstance(col.data_type, ColoRef):
                    continue
                if version == 20:
                    cw.emit(
                        "{0}_ref: Mapped[{1}] = relationship(foreign_keys=[{0}])".format(
                            col.name,
                            wrap_type_if_optional(
                                fmt_pascal(col.data_type.ref.name),
                                col.nullable,
                                quote_type=True,
                            ),
                        )
                    )
                else:
                    cw.emit(
                        "{0}_ref = relationship('{1}', foreign_keys=[{0}])".format(
                            col.name, fmt_pascal(col.data_type.ref.name)
                        )
                    )
            if vertex.extends:
                if version == 20:
                    cw.emit(
                        "{}: Mapped['{}'] = relationship(back_populates='{}')".format(
                            vertex.extends.name,
                            fmt_pascal(vertex.extends.name),
                            vertex.name,
                        )
                    )
                else:
                    cw.emit(
                        "{} = relationship('{}', back_populates='{}')".format(
                            vertex.extends.name,
                            fmt_pascal(vertex.extends.name),
                            vertex.name,
                        )
                    )
            for extends_backref in vertex.extends_backrefs:
                if version == 20:
                    cw.emit(
                        "{}: Mapped['{}'] = relationship(".format(
                            extends_backref.name, fmt_pascal(extends_backref.name)
                        )
                    )
                    with cw.indent():
                        cw.emit("uselist=False,")
                        cw.emit("back_populates='{}',".format(vertex.name))
                    cw.emit(")")
                else:
                    cw.emit("{} = relationship(".format(extends_backref.name))
                    with cw.indent():
                        cw.emit("'{}',".format(fmt_pascal(extends_backref.name)))
                        cw.emit("uselist=False,")
                        cw.emit("back_populates='{}',".format(vertex.name))
                    cw.emit(")")
            for counter_backref in vertex.counter_backrefs:
                counter_name = counter_backref.get_full_name()
                if version == 20:
                    cw.emit(
                        "{0}: Mapped[list['{1}']] = relationship('{1}')".format(
                            counter_name, fmt_pascal(counter_name)
                        )
                    )
                else:
                    with cw.block("{} = relationship(".format(counter_name), ")"):
                        cw.emit("'{}',".format(fmt_pascal(counter_name)))

    for edge in graph.edges.values():
        if edge.drop:
            continue
        cw.emit()
        cw.emit()
        cw.emit("class {}(Base, EdgeMixin):".format(fmt_pascal(edge.name)))
        with cw.indent():
            cw.emit("__tablename__ = '{}'".format(edge.name))
            with cw.block("__table_args__ = (", ")", delim):
                if version == 20:
                    # Necessary b/c in SA 2.0 the child class's primary keys
                    # when specified on columns are ordered before the
                    # EdgeMixin unless a constraint is explicitly defined.
                    cw.emit(
                        "PrimaryKeyConstraint({}),".format(
                            ", ".join(
                                [
                                    f"'{col.name}'"
                                    for col in edge.cols
                                    if col.primary_key
                                ]
                            )
                        )
                    )
                cw.emit(
                    "ForeignKeyConstraint(['src'], ['{}.gid']),".format(
                        edge.src.name,
                    )
                )
                for col in edge.extra_cols:
                    if col.drop:
                        continue
                    if not isinstance(col.data_type, ColoRef):
                        continue
                    cw.emit(
                        "ForeignKeyConstraint(['{}'], ['{}.gid']),".format(
                            col.name, col.data_type.ref.name
                        )
                    )
            cw.emit("_src_cls = {}".format(fmt_pascal(edge.src.name)))
            cw.emit("_tgt_cls = {}".format(fmt_pascal(edge.tgt.name)))
            for col in edge.extra_cols:
                if col.drop:
                    continue
                sa_type = graph_type_to_sa_type(col.data_type, version >= 14)
                pk_arg = ", primary_key=True" if col.primary_key else ""
                default_arg = ", server_default=FetchedValue()" if col.default else ""
                nullable_arg = ", nullable=True" if col.nullable else ""
                if version == 20:
                    col_py_type = column_type_to_mypy_type(col)
                    cw.emit(
                        "{}: Mapped[{}] = mapped_column({}{}{}{})".format(
                            col.name,
                            col_py_type,
                            sa_type,
                            pk_arg,
                            default_arg,
                            nullable_arg,
                        )
                    )
                else:
                    cw.emit(
                        "{} = Column({}{}{}{})".format(
                            col.name, sa_type, pk_arg, default_arg, nullable_arg
                        )
                    )
            for col in edge.extra_cols:
                if col.drop:
                    continue
                if not isinstance(col.data_type, ColoRef):
                    continue
                if version == 20:
                    cw.emit(
                        "{0}_ref: Mapped[{1}] = relationship(foreign_keys=[{0}])".format(
                            col.name,
                            wrap_type_if_optional(
                                fmt_pascal(col.data_type.ref.name),
                                col.nullable,
                                quote_type=True,
                            ),
                        )
                    )
                else:
                    cw.emit(
                        "{0}_ref = relationship('{1}', foreign_keys=[{0}])".format(
                            col.name, fmt_pascal(col.data_type.ref.name)
                        )
                    )
            if version == 20:
                cw.emit(
                    "{}: Mapped['{}'] = relationship()".format(
                        edge.src.name, fmt_pascal(edge.src.name)
                    )
                )
            else:
                cw.emit(
                    "{} = relationship('{}')".format(
                        edge.src.name, fmt_pascal(edge.src.name)
                    )
                )

    for edge in graph.edges.values():
        if not edge.counters:
            continue
        edge_col_lookup = {col.name: col for col in edge.cols}
        for counter in edge.counters:
            cw.emit()
            cw.emit()
            cw.emit(
                "class {}(Base, CounterMixin):".format(
                    fmt_pascal(edge.name + "_counter_" + counter.name)
                )
            )
            with cw.indent():
                cw.emit(
                    "__tablename__ = '{}'".format(
                        edge.name + "_counter_" + counter.name
                    )
                )
                with cw.block("__table_args__ = (", ")"):
                    cw.emit(
                        "ForeignKeyConstraint(['src'], ['{}.gid']),".format(
                            edge.src.name
                        )
                    )
                for col_name in counter.cols:
                    col = edge_col_lookup[col_name]
                    dt = graph_type_to_sa_type(col.data_type, version >= 14)
                    cw.emit("{} = Column({}, primary_key=True)".format(col.name, dt))

    cw.emit()
    cw.emit()
    cw.emit_list(
        [fmt_pascal(v.name) for v in graph.vertices.values() if not v.drop],
        bracket=("[", "]"),
        before="vertex_types = ",
    )
    cw.emit()
    cw.emit_list(
        [fmt_pascal(e.name) for e in graph.edges.values() if not e.drop],
        bracket=("[", "]"),
        before="edge_types = ",
    )
    cw.emit()
    cw.emit_list(
        [
            fmt_pascal(counter.get_full_name())
            for e in graph.edges.values()
            for counter in e.counters
            if not counter.drop
        ],
        bracket=("[", "]"),
        before="counter_types = ",
    )
    # Use black to apply reasonable format to generated file. However, disable
    # further formatting in case the file is used in a project that runs black
    # again with different settings.
    return "# fmt: off\n" + black.format_str(cw.render(), mode=black.Mode())


def graph_type_to_sa_type(data_type: DataType, version_gt14: bool) -> str:
    if isinstance(data_type, (ColoRef, Vertex)):
        return "Gid"
    elif isinstance(data_type, Enum):
        return data_type.name + "_db_enum_type"
    elif isinstance(data_type, CompositeType):
        return fmt_pascal(data_type.name)
    elif isinstance(data_type, Array):
        if version_gt14:
            return "ARRAY({}, dimensions=1)".format(
                graph_type_to_sa_type(data_type.element_type, version_gt14)
            )
        elif isinstance(data_type.element_type, (ColoRef, Vertex, CompositeType)):
            return "CompositeArray({})".format(
                graph_type_to_sa_type(data_type.element_type, version_gt14)
            )
        else:
            return "ARRAY({})".format(
                graph_type_to_sa_type(data_type.element_type, version_gt14)
            )
    else:
        return sql_type_to_sa_type(data_type)


def sql_type_to_sa_type(sql_type: str) -> str:
    assert not sql_type.endswith("[]"), sql_type
    sql_type_norm = sql_type.lower()
    if sql_type_norm == "text":
        return "String"
    elif sql_type_norm == "timestamp":
        return "DateTime"
    elif sql_type_norm == "bigint" or sql_type_norm == "bigserial":
        return "BigInteger"
    elif sql_type_norm == "serial":
        return "Integer"
    elif sql_type_norm == "smallint":
        return "SmallInteger"
    elif sql_type_norm == "binary":
        return "LargeBinary"
    else:
        return sql_type


def graph_type_to_mypy_type(data_type: DataType, depth: int = 0) -> str:
    """
    Args:
        depth: For any depth greater than 0, assumes the definition of a
            composite type is already defined earlier.
    """
    if isinstance(data_type, (ColoRef, Vertex)):
        return "TGid"
    elif isinstance(data_type, Enum):
        return "str"
    elif isinstance(data_type, CompositeType):
        if depth == 0:
            named_tuple_fields = [
                '("{}", {})'.format(
                    field[0], graph_type_to_mypy_type(field[1], depth + 1)
                )
                for field in data_type.fields
            ]
            return 'NamedTuple("{}T", [{}])'.format(
                fmt_pascal(data_type.name), ", ".join(named_tuple_fields)
            )
        else:
            # Assume the composite type has already been defined earlier.
            return f"{fmt_pascal(data_type.name)}T"
    elif isinstance(data_type, Array):
        return "list[{}]".format(
            graph_type_to_mypy_type(data_type.element_type, depth + 1),
        )
    else:
        return sql_type_to_mypy_type(data_type)


def column_type_to_mypy_type(column: Column) -> str:
    py_type = graph_type_to_mypy_type(column.data_type, depth=1)
    if column.nullable:
        return f"Optional[{py_type}]"
    else:
        return py_type


def sql_type_to_mypy_type(sql_type: str) -> str:
    assert not sql_type.endswith("[]"), sql_type
    sql_type_norm = sql_type.lower()
    if sql_type_norm == "text":
        return "str"
    elif sql_type_norm == "boolean":
        return "bool"
    elif sql_type_norm == "timestamp":
        return "datetime.datetime"
    elif sql_type_norm == "date":
        return "datetime.date"
    elif sql_type_norm in ("smallint", "bigint", "integer"):
        return "int"
    elif sql_type_norm == "binary":
        return "bytes"
    elif sql_type_norm.startswith("vector("):
        # FIXME: Vector isn't a first-class type yet.
        return "Vector"
    else:
        return sql_type


def wrap_type_if_optional(py_type: str, is_optional: bool, quote_type: bool) -> str:
    if quote_type:
        py_type = f"'{py_type}'"
    if is_optional:
        return f"Optional[{py_type}]"
    else:
        return py_type
