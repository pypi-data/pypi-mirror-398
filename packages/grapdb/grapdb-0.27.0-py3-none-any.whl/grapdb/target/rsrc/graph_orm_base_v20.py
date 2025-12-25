# pylint: disable=protected-access
import hashlib
import logging
from operator import eq
import random
import struct
from typing import Any, Iterable, Optional, Union, TypeVar

import jump
import sqlalchemy
from sqlalchemy import (
    BigInteger,
    Column,
    FetchedValue,
    Integer,
    MetaData,
    SmallInteger,
    literal,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy.sql import (
    crud,
    operators,
    visitors,
)
from sqlalchemy.sql.elements import (
    BinaryExpression,
    BindParameter,
)

#
# START: Start of CompositeType definition & utilities.
# - It's stuffed here to reduce dependencies to one file and removes the
#   dependence on the sqlalchemy_utils package.
# - It's mostly copied from the sqlalchemy_utils package but modified to
#   support schemas.
# - It's unfortunately untyped.
#

from collections import namedtuple
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import _CreateDropBase
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import SchemaType, to_instance, TypeDecorator, UserDefinedType
import psycopg2
from psycopg2.extensions import adapt, AsIs, register_adapter
from psycopg2.extras import CompositeCaster


class CompositeElement(FunctionElement):
    """
    Instances of this class wrap a Postgres composite type.
    """

    def __init__(self, base, field, type_):
        self.name = field
        self.type = to_instance(type_)

        super().__init__(base)


@compiles(CompositeElement)
def _compile_pgelem(expr, compiler, **kw):
    return "(%s).%s" % (compiler.process(expr.clauses, **kw), expr.name)


# This is almost entirely copied from the SA implementation.
# The monkey-patch is required for gid-specific handling. When a vertex is
# committed with only the vshard specified in the gid, the DB is responsible
# (via a trigger) to populate the id component of the gid. SA's default
# behavior does not use RETURNING for the partially specified gid, which means
# it remains as (None, vshard). This monkey-patch adds the gid to RETURNING so
# that the gid is fully specified post-flush/commit.


def monkey_patch_sq_sql_crud_scan_cols(
    compiler,
    stmt,
    compile_state,
    parameters,
    _getattr_col_key,
    _column_as_key,
    _col_bind_name,
    check_columns,
    values,
    toplevel,
    kw,
):
    (
        need_pks,
        implicit_returning,
        implicit_return_defaults,
        postfetch_lastrowid,
        use_insertmanyvalues,
        use_sentinel_columns,
    ) = crud._get_returning_modifiers(compiler, stmt, compile_state, toplevel)

    if compile_state._parameter_ordering:
        parameter_ordering = [
            _column_as_key(key) for key in compile_state._parameter_ordering
        ]
        ordered_keys = set(parameter_ordering)
        cols = [
            stmt.table.c[key]
            for key in parameter_ordering
            if isinstance(key, str) and key in stmt.table.c
        ] + [c for c in stmt.table.c if c.key not in ordered_keys]

    else:
        cols = stmt.table.columns

    isinsert = crud._compile_state_isinsert(compile_state)
    if isinsert and not compile_state._has_multi_parameters:
        # [COPIED] new rules for #7998.  fetch lastrowid or implicit returning
        # for autoincrement column even if parameter is NULL, for DBs that
        # override NULL param for primary key (sqlite, mysql/mariadb)
        autoincrement_col = stmt.table._autoincrement_column
        insert_null_pk_still_autoincrements = (
            compiler.dialect.insert_null_pk_still_autoincrements
        )
    else:
        autoincrement_col = insert_null_pk_still_autoincrements = None

    if stmt._supplemental_returning:
        supplemental_returning = set(stmt._supplemental_returning)
    else:
        supplemental_returning = set()

    compiler_implicit_returning = compiler.implicit_returning

    for c in cols:
        # [COPIED] scan through every column in the target table

        col_key = _getattr_col_key(c)

        if col_key in parameters and col_key not in check_columns:
            # NOTE: This is the monkey-patch to add the gid column to RETURNING
            if (
                compile_state.isinsert
                and isinstance(c.server_default, FetchedValue)
                and col_key == "gid"
            ):
                compiler_implicit_returning.append(c)

            # [COPIED] parameter is present for the column.  use that.
            crud._append_param_parameter(
                compiler,
                stmt,
                compile_state,
                c,
                col_key,
                parameters,
                _col_bind_name,
                implicit_returning,
                implicit_return_defaults,
                postfetch_lastrowid,
                values,
                autoincrement_col,
                insert_null_pk_still_autoincrements,
                kw,
            )

        elif isinsert:
            # [COPIED] no parameter is present and it's an insert.

            if c.primary_key and need_pks:
                # [COPIED] it's a primary key column, it will need to be generated by a
                # default generator of some kind, and the statement expects
                # inserted_primary_key to be available.

                if implicit_returning:
                    # [COPIED] we can use RETURNING, find out how to invoke this
                    # column and get the value where RETURNING is an option.
                    # we can inline server-side functions in this case.

                    crud._append_param_insert_pk_returning(
                        compiler, stmt, c, values, kw
                    )
                else:
                    # [COPIED] otherwise, find out how to invoke this column
                    # and get its value where RETURNING is not an option.
                    # if we have to invoke a server-side function, we need
                    # to pre-execute it.   or if this is a straight
                    # autoincrement column and the dialect supports it
                    # we can use cursor.lastrowid.

                    crud._append_param_insert_pk_no_returning(
                        compiler, stmt, c, values, kw
                    )

            elif c.default is not None:
                # [COPIED] column has a default, but it's not a pk column, or it is but
                # we don't need to get the pk back.
                if not c.default.is_sentinel or (use_sentinel_columns is not None):
                    crud._append_param_insert_hasdefault(
                        compiler, stmt, c, implicit_return_defaults, values, kw
                    )

            elif c.server_default is not None:
                # [COPIED] column has a DDL-level default, and is either not a pk
                # column or we don't need the pk.
                if implicit_return_defaults and c in implicit_return_defaults:
                    compiler_implicit_returning.append(c)
                elif not c.primary_key:
                    compiler.postfetch.append(c)
            elif implicit_return_defaults and c in implicit_return_defaults:
                compiler_implicit_returning.append(c)
            elif (
                c.primary_key
                and c is not stmt.table._autoincrement_column
                and not c.nullable
            ):
                crud._warn_pk_with_no_anticipated_value(c)

        elif compile_state.isupdate:
            # [COMPILED] no parameter is present and it's an insert.

            crud._append_param_update(
                compiler,
                compile_state,
                stmt,
                c,
                implicit_return_defaults,
                values,
                kw,
            )

        # [COPIED] adding supplemental cols to implicit_returning in table
        # order so that order is maintained between multiple INSERT
        # statements which may have different parameters included, but all
        # have the same RETURNING clause
        if c in supplemental_returning and c not in compiler_implicit_returning:
            compiler_implicit_returning.append(c)

    if supplemental_returning:
        # [COPIED] we should have gotten every col into implicit_returning,
        # however supplemental returning can also have SQL functions etc.
        # in it
        remaining_supplemental = supplemental_returning.difference(
            compiler_implicit_returning
        )
        compiler_implicit_returning.extend(
            c for c in stmt._supplemental_returning if c in remaining_supplemental
        )

    return (use_insertmanyvalues, use_sentinel_columns)


crud._scan_cols = monkey_patch_sq_sql_crud_scan_cols


# TODO: Make the registration work on connection level instead of global level
registered_composites: dict[str, "CompositeType"] = {}


class CompositeType(UserDefinedType, SchemaType):
    """
    Represents a PostgreSQL composite type.
    :param name:
        Name of the composite type.
    :param columns:
        List of columns that this composite type consists of
    """

    python_type = tuple
    cache_ok = False

    name: str  # For mypy: overrides SchemaType to remove optional

    class comparator_factory(UserDefinedType.Comparator):
        def __getattr__(self, key):
            # This differs from the logic in SqlAlchemy-Utils which failed to
            # work when selecting a field of a ctype in a filter. This hacked
            # logic is likely dubious as well, but works in filters.
            if key.startswith("_"):
                type_ = self.type.typemap[key]
            else:
                for col in self.type.columns:
                    if col.name == key:
                        type_ = col.type
                        break
                else:
                    raise AttributeError("Type doesn't have an attribute: '%s'" % key)
            return CompositeElement(self.expr, key, type_)

    def __init__(
        self,
        name: str,
        columns: list[Column],
        quote: Optional[bool] = None,
        schema: Optional[str] = None,
        **kwargs,
    ):
        if psycopg2 is None:
            assert (
                False
            ), "'psycopg2' package is required in order to use CompositeType."
        SchemaType.__init__(
            self,
            name=name,
            quote=quote,
            schema=schema,
        )
        self.name = name
        self.columns = columns
        self.type_cls: Any
        if name in registered_composites:
            self.type_cls = registered_composites[name].type_cls
        else:
            self.type_cls = namedtuple(self.name, [c.name for c in columns])  # type: ignore
        registered_composites[name] = self

        type_cls = self.type_cls

        class Caster(CompositeCaster):
            def make(self, values):
                return type_cls(*values)

        self.caster = Caster
        attach_composite_listeners()

    def get_name_with_schema(self) -> str:
        return self.schema + "." + self.name if self.schema else self.name

    def get_col_spec(self):
        return self.get_name_with_schema()

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None

            processed_value = []
            for i, column in enumerate(self.columns):
                current_value = (
                    value.get(column.name) if isinstance(value, dict) else value[i]
                )
                if isinstance(column.type, TypeDecorator):
                    processed_value.append(
                        column.type.process_bind_param(current_value, dialect)
                    )
                else:
                    processed_value.append(current_value)
            return self.type_cls(*processed_value)

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            cls = value.__class__
            kwargs = {}
            for column in self.columns:
                if isinstance(column.type, TypeDecorator):
                    kwargs[column.name] = column.type.process_result_value(
                        getattr(value, column.name), dialect
                    )
                else:
                    kwargs[column.name] = getattr(value, column.name)
            return cls(**kwargs)

        return process

    def create(self, bind=None, checkfirst=None):
        if not checkfirst or not bind.dialect.has_type(
            bind, self.name, schema=self.schema
        ):
            bind.execute(CreateCompositeType(self))

    def drop(self, bind=None, checkfirst=True):
        if checkfirst and bind.dialect.has_type(bind, self.name, schema=self.schema):
            bind.execute(DropCompositeType(self))


def register_psycopg2_composite(dbapi_connection, composite):
    psycopg2.extras.register_composite(
        composite.get_name_with_schema(),
        dbapi_connection,
        globally=True,
        factory=composite.caster,
    )

    def adapt_composite(value):
        dialect = PGDialect_psycopg2()
        adapted = [
            adapt(
                getattr(value, column.name)
                if not isinstance(column.type, TypeDecorator)
                else column.type.process_bind_param(
                    getattr(value, column.name), dialect
                )
            )
            for column in composite.columns
        ]
        for value in adapted:
            if hasattr(value, "prepare"):
                value.prepare(dbapi_connection)
        values = [
            value.getquoted().decode(dbapi_connection.encoding) for value in adapted
        ]
        return AsIs(
            "({})::{}".format(", ".join(values), composite.get_name_with_schema())
        )

    register_adapter(composite.type_cls, adapt_composite)


def get_driver_connection(connection: sqlalchemy.engine.base.Connection) -> Any:
    return connection.connection.driver_connection


def before_create(target, connection: sqlalchemy.engine.base.Connection, **kw):
    for _, composite in registered_composites.items():
        composite.create(connection, checkfirst=True)
        register_psycopg2_composite(get_driver_connection(connection), composite)


def after_drop(target, connection, **kw):
    for _, composite in registered_composites.items():
        composite.drop(connection, checkfirst=True)


def register_composites(connection: sqlalchemy.engine.base.Connection):
    for _, composite in registered_composites.items():
        register_psycopg2_composite(get_driver_connection(connection), composite)


def attach_composite_listeners():
    listeners = [
        (MetaData, "before_create", before_create),
        (MetaData, "after_drop", after_drop),
    ]
    for listener in listeners:
        if not sqlalchemy.event.contains(*listener):
            sqlalchemy.event.listen(*listener)


def remove_composite_listeners():
    listeners = [
        (MetaData, "before_create", before_create),
        (MetaData, "after_drop", after_drop),
    ]
    for listener in listeners:
        if sqlalchemy.event.contains(*listener):
            sqlalchemy.event.remove(*listener)


class CreateCompositeType(_CreateDropBase):
    pass


@compiles(CreateCompositeType)
def _visit_create_composite_type(create, compiler, **kw):
    type_ = create.element
    fields = ", ".join(
        "{name} {type}".format(
            name=column.name,
            type=compiler.dialect.type_compiler.process(to_instance(column.type)),
        )
        for column in type_.columns
    )

    return "CREATE TYPE {name} AS ({fields})".format(
        name=compiler.preparer.format_type(type_), fields=fields
    )


class DropCompositeType(_CreateDropBase):
    pass


@compiles(DropCompositeType)
def _visit_drop_composite_type(drop, compiler, **kw):
    type_ = drop.element

    return "DROP TYPE {name}".format(name=compiler.preparer.format_type(type_))


#
# END: CompositeType definition & utilities.
#

logger = logging.getLogger("graph_orm_base")

graph_metadata = MetaData(schema="graph")


class Base(DeclarativeBase):
    metadata = graph_metadata


Gid = CompositeType("gid", [Column("id", BigInteger), Column("vshard", SmallInteger)])
TGid = tuple[int, int]


def is_likely_gid(maybe_gid: Any) -> bool:
    """Returns whether the input is likely a gid."""
    return isinstance(maybe_gid, tuple) and (
        maybe_gid.__class__.__name__ == "gid"
        or (
            len(maybe_gid) == 2
            and isinstance(maybe_gid[0], int)
            and isinstance(maybe_gid[1], int)
        )
    )


def random_vshard() -> int:
    return random.randint(-32768, 32767)


def entry_point_to_vshard(
    entry_point_val: Union[
        str,
        bytes,
        tuple[Union[str, bytes], ...],
        Iterable[TGid],
    ],
) -> int:
    if isinstance(entry_point_val, str):
        # NOTE: Order is critical as str is an Iterable.
        entry_point_encoded = entry_point_val.encode("utf-8")
    elif isinstance(entry_point_val, tuple):
        encoded_vals: list[bytes] = []
        for val in entry_point_val:
            if isinstance(val, str):
                encoded_vals.append(val.encode("utf-8"))
            else:
                assert isinstance(val, bytes)
                encoded_vals.append(val)
        entry_point_encoded = b"".join(encoded_vals)
    elif isinstance(entry_point_val, Iterable):
        # This assertion is to help mypy understand the type narrowing
        assert not isinstance(entry_point_val, (tuple, str, bytes))
        entry_point_encoded = b"".join(
            struct.pack("<qh", gid[0], gid[1]) for gid in entry_point_val
        )
    else:
        assert isinstance(entry_point_val, bytes)
        entry_point_encoded = entry_point_val
    hashed_val = hashlib.sha1(entry_point_encoded).digest()
    pair_of_bytes = hashed_val[:2]
    return struct.unpack("<h", pair_of_bytes)[0]


class EntityMixin:
    def get_vshard(self) -> int:
        raise NotImplementedError

    def pp(self):
        """Pretty-print entity attributes."""
        cls = type(self)
        field_names = []
        for field in dir(cls):
            if field.startswith("_"):
                continue
            if hasattr(getattr(cls, field), "type"):
                field_names.append(field)
        max_length = max(len(field_name) for field_name in field_names)
        for field_name in field_names:
            print(field_name.ljust(max_length), ":", getattr(self, field_name))


VT = TypeVar("VT", bound="VertexMixin")


class VertexMixin(EntityMixin):

    __mapper_args__ = {"eager_defaults": True}

    gid: Mapped[TGid] = mapped_column(
        Gid, primary_key=True, server_default=FetchedValue()
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=FetchedValue())

    def __repr__(self) -> str:
        return "<{}(gid={})>".format(self.__class__.__name__, self.gid)

    def get_vshard(self) -> int:
        if self.gid is None:
            shard = random_vshard()
            # The need to use a literal is a hack thanks to a patch by the
            # SQLAlchemy author. The literal informs SA that it needs to adopt
            # the PK that's returned by the insert.
            # NOTE: This value is temporary and will be replaced by a proper
            # gid tuple by the time control is returned to the caller (not of
            # this method, but the caller of the higher-level DB operation).
            self.gid = literal((None, shard))
        if isinstance(self.gid, BindParameter):
            return self.gid.value[1]
        else:
            return self.gid[1]

    def colo_with(self: VT, gid_or_ent: Union[TGid, "EntityMixin"]) -> VT:
        assert self.gid is None
        if isinstance(gid_or_ent, EntityMixin):
            vshard = gid_or_ent.get_vshard()
        else:
            assert isinstance(gid_or_ent, tuple)
            vshard = gid_or_ent[1]
        self.gid = literal((None, vshard))
        return self


class EntryPointMixin:

    _entry_point: str
    gid: Mapped[TGid]

    def get_vshard(self) -> int:
        if self.gid is None:
            entry_point_val = getattr(self, self._entry_point)
            assert entry_point_val is not None, (
                "Entry point %r must be set." % entry_point_val
            )
            self.gid = literal((None, entry_point_to_vshard(entry_point_val)))
        if isinstance(self.gid, BindParameter):
            return self.gid.value[1]
        else:
            return self.gid[1]


class ExtendsMixin:

    gid: Mapped[TGid]

    def get_vshard(self) -> int:
        assert self.gid is not None, "Gid must be specified for extended vertex."
        return self.gid[1]


class EdgeMixin(EntityMixin):

    __mapper_args__ = {"eager_defaults": True}

    src: Mapped[TGid] = mapped_column(Gid, primary_key=True)
    tgt: Mapped[TGid] = mapped_column(Gid, primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)

    def __repr__(self) -> str:
        return "<{}(src={}, tgt={})>".format(
            self.__class__.__name__, self.src, self.tgt
        )

    def get_vshard(self) -> int:
        return self.src[1]


class CounterMixin(EntityMixin):
    src: Mapped[TGid] = mapped_column(Gid, primary_key=True)
    count: Mapped[int] = mapped_column(Integer)

    def __repr__(self) -> str:
        return "<{}(src={}, count={})>".format(
            self.__class__.__name__, self.src, self.count
        )

    def get_vshard(self) -> int:
        return self.src[1]


class ShardMapper:
    def __init__(self, num_shards: int):
        assert num_shards > 0
        self.num_shards = num_shards
        self.shards_set = frozenset({str(i) for i in range(num_shards)})

    def jump_hash(self, vshard: int) -> str:
        return str(jump.hash(vshard, self.num_shards))

    def shard_chooser(self, mapper, instance, clause=None) -> str:
        """
        Called when inserting a new object:
        - s.add(V)
        - s.add(E)
        """
        vshard = instance.get_vshard() if instance else None
        logger.debug(
            "shard_chooser mapper=%r instance=%r clause=%r vshard=%r",
            mapper,
            instance,
            clause,
            vshard,
        )
        # Returning a dummy shard is necessary for sqlalchemy to return the
        # string representation of a query (str(query)) for debugging purposes.
        return self.jump_hash(vshard) if vshard else "0"

    def id_chooser(self, query, ident: list[tuple[int, int]]) -> set[str]:
        """
        Called when looking up entity by relationship.
        - v.extends
        """
        logger.debug("id_chooser: query=%r ident=%r", query, ident)
        assert len(ident) == 1, (len(ident), ident)
        vshards = set()
        for gid in ident:
            vshards.add(str(gid[1]))
        return vshards

    def execute_chooser(self, context: sqlalchemy.orm.session.ORMExecuteState):
        """
        Called when querying vertex by primary key gid:
        - v = s.query(V).filter(V.gid == (3, 1)).one()

        Called when querying multiple vertices by primary key gid:
        - v = s.query(V).filter((V.gid == (3, 1)) | (V.gid == (4, 0))).all()
        - Unfortunately, it queries all applicable shards with all gids.

        Called when querying edge by partial primary key src:
        - e = s.query(Edge).filter(Edge.src == (3, 1)).one()

        Called when querying edge by primary key (src, tgt)
        - e = s.query(Edge).filter(Edge.src == (3, 1), Edge.tgt == (4,0)).one()

        Called when querying vertex by entry point:
        - v = s.query(V).filter(V.entry_point == 'xyz').one()

        If querying by non-PK gid or entry point, we ignore and return all shards.
        """
        shards = set()
        if (
            context.is_relationship_load
            and context.lazy_loaded_from
            and isinstance(context.lazy_loaded_from.object, EntityMixin)
        ):
            # This is for relationship loads
            shards.add(self.jump_hash(context.lazy_loaded_from.object.get_vshard()))
        if not shards and "mapper" in context.bind_arguments:
            # This is the typical case for basic queries.
            ent_class = context.bind_arguments["mapper"].class_
            for column, operator, value in _get_select_comparisons(context.statement):
                if column.primary_key:
                    if column.name not in {"gid", "src"}:
                        continue
                    if operator == eq:  # pylint: disable=comparison-with-callable
                        assert isinstance(value, tuple), value
                        assert len(value) == 2, value
                        vshard = value[1]
                        shards.add(self.jump_hash(vshard))
                    elif (
                        operator == operators.in_op
                    ):  # pylint: disable=comparison-with-callable
                        assert (
                            operator == operators.in_op
                        ), operator  # pylint: disable=comparison-with-callable
                        for gid in value:
                            assert isinstance(gid, tuple), gid
                            assert len(gid) == 2, gid
                            vshard = gid[1]
                            shards.add(self.jump_hash(vshard))
                    else:
                        assert False, "Unsupported operator %r" % operator
                elif (
                    issubclass(ent_class, EntryPointMixin)
                    and column.name == ent_class._entry_point
                ):
                    if operator == eq:  # pylint: disable=comparison-with-callable
                        shards.add(self.jump_hash(entry_point_to_vshard(value)))
                    elif (
                        operator == operators.in_op
                    ):  # pylint: disable=comparison-with-callable
                        assert (
                            operator == operators.in_op
                        ), operator  # pylint: disable=comparison-with-callable
                        for entry_point in value:
                            shards.add(
                                self.jump_hash(entry_point_to_vshard(entry_point))
                            )
                    else:
                        assert False, "Unsupported operator %r" % operator
        if not shards and "clause" in context.bind_arguments:
            # This is for complex queries that include ops such as CTEs
            clause = context.bind_arguments["clause"]
            clause_compiled = clause.compile()

            for _, val in clause_compiled.params.items():
                if is_likely_gid(val):
                    likely_gids = [val]
                elif isinstance(val, list) and len(val) > 0 and is_likely_gid(val[0]):
                    likely_gids = val
                else:
                    continue
                for likely_gid in likely_gids:
                    shards.add(self.jump_hash(likely_gid[1]))

        if not shards:
            logger.warning("execute_chooser: querying all shards.")
            shards = {*self.shards_set}
        logger.debug("execute_chooser: shards=%s", shards)
        return shards


def _get_select_comparisons(statement) -> list[tuple[Any, Any, Any]]:
    """Search a Select or Query object for binary expressions.

    Returns expressions which match a Column against one or more
    literal values as a list of tuples of the form
    (column, operator, values).   "values" is a single value
    or tuple of values depending on the operator.
    """
    binds: dict[Any, Any] = {}
    clauses: set[Column] = set()
    binary_exprs: list[BinaryExpression] = []

    def visit_bindparam(bind: BindParameter) -> None:
        value = bind.effective_value
        binds[bind] = value

    def visit_column(column: Column) -> None:
        clauses.add(column)

    def visit_binary(expr: BinaryExpression) -> None:
        binary_exprs.append(expr)

    # Using 2.0-style select with union_all does not have a whereclause
    if hasattr(statement, "whereclause") and statement.whereclause is not None:
        # Since there's no guarantee on the order of traversal (which dictates
        # the order of the visit callbacks), we collect all the data from the
        # traversal first before analyzing it.
        visitors.traverse(
            statement.whereclause,
            {},
            {
                "bindparam": visit_bindparam,
                "binary": visit_binary,
                "column": visit_column,
            },
        )

    comparisons: list[tuple[Any, Any, Any]] = []
    for binary_expr in binary_exprs:
        if binary_expr.left in clauses and binary_expr.right in binds:
            comparisons.append(
                (binary_expr.left, binary_expr.operator, binds[binary_expr.right])
            )
        elif binary_expr.left in binds and binary_expr.right in clauses:
            comparisons.append(
                (binary_expr.right, binary_expr.operator, binds[binary_expr.left])
            )

    return comparisons
