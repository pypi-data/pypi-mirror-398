import hashlib
import logging
from operator import eq
import random
import struct
from typing import Iterable, List, Set, Tuple, Union, TypeVar

import jump
import sqlalchemy
from sqlalchemy import (  # pylint: disable=E0401
    BigInteger,
    Column,
    FetchedValue,
    Integer,
    MetaData,
    SmallInteger,
    literal,
)
from sqlalchemy.dialects.postgresql import (  # pylint: disable=E0401
    JSONB,
)
from sqlalchemy.ext.declarative import declarative_base  # pylint: disable=E0401
from sqlalchemy.sql import (  # pylint: disable=E0401
    operators,
    visitors,
)
from sqlalchemy.sql.elements import BindParameter  # pylint: disable=E0401

#
# START: Start of CompositeType definition & utilities.
# - It's stuffed here to reduce dependencies to one file and removes the
#   dependence on the sqlalchemy_utils package.
# - It's mostly copied from the sqlalchemy_utils package but modified to
#   support schemas.
# - It's unfortunately untyped.
#

from collections import namedtuple
import six
from sqlalchemy.dialects.postgresql import ARRAY
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

        super(CompositeElement, self).__init__(base)


@compiles(CompositeElement)
def _compile_pgelem(expr, compiler, **kw):
    return "(%s).%s" % (compiler.process(expr.clauses, **kw), expr.name)


class CompositeArray(ARRAY):
    def _proc_array(self, arr, itemproc, dim, collection):
        if dim is None:
            if isinstance(self.item_type, CompositeType):
                arr = [itemproc(a) for a in arr]
                return arr
        return ARRAY._proc_array(self, arr, itemproc, dim, collection)


# TODO: Make the registration work on connection level instead of global level
registered_composites = {}


class CompositeType(UserDefinedType, SchemaType):
    """
    Represents a PostgreSQL composite type.
    :param name:
        Name of the composite type.
    :param columns:
        List of columns that this composite type consists of
    """

    python_type = tuple

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

    def __init__(self, name, columns, schema=None):
        SchemaType.__init__(self, schema=schema)
        self.name = name
        self.columns = columns
        if name in registered_composites:
            self.type_cls = registered_composites[name].type_cls
        else:
            self.type_cls = namedtuple(self.name, [c.name for c in columns])
        registered_composites[name] = self

        class Caster(CompositeCaster):
            def make(obj, values):
                return self.type_cls(*values)

        self.caster = Caster
        attach_composite_listeners()

    def get_name_with_schema(self) -> str:
        return self.schema + "." + self.name if self.schema else self.name

    def get_col_spec(self):
        return self.name

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
        adapted = [
            adapt(
                getattr(value, column.name)
                if not isinstance(column.type, TypeDecorator)
                else column.type.process_bind_param(
                    getattr(value, column.name), PGDialect_psycopg2()
                )
            )
            for column in composite.columns
        ]
        for value in adapted:
            if hasattr(value, "prepare"):
                value.prepare(dbapi_connection)
        values = [
            (
                value.getquoted().decode(dbapi_connection.encoding)
                if six.PY3
                else value.getquoted()
            )
            for value in adapted
        ]
        return AsIs("(%s)::%s" % (", ".join(values), composite.get_name_with_schema()))

    register_adapter(composite.type_cls, adapt_composite)


def before_create(target, connection, **kw):
    for name, composite in registered_composites.items():
        composite.create(connection, checkfirst=True)
        register_psycopg2_composite(connection.connection.connection, composite)


def after_drop(target, connection, **kw):
    for name, composite in registered_composites.items():
        composite.drop(connection, checkfirst=True)


def register_composites(connection):
    for name, composite in registered_composites.items():
        register_psycopg2_composite(connection.connection.connection, composite)


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

metadata = MetaData(schema="graph")
Base = declarative_base(metadata=metadata)
Gid = CompositeType("gid", [Column("id", BigInteger), Column("vshard", SmallInteger)])
TGid = Tuple[int, int]


def random_vshard() -> int:
    return random.randint(-32768, 32767)


def entry_point_to_vshard(
    entry_point_val: Union[
        str,
        bytes,
        Tuple[Union[str, bytes], ...],
        Iterable[TGid],
    ],
) -> int:
    if isinstance(entry_point_val, str):
        # NOTE: Order is critical as str is an Iterable.
        entry_point_encoded = entry_point_val.encode("utf-8")
    elif isinstance(entry_point_val, tuple):
        encoded_vals: List[bytes] = []
        for val in entry_point_val:
            if isinstance(val, str):
                encoded_vals.append(val.encode("utf-8"))
            else:
                assert isinstance(val, bytes)
                encoded_vals.append(val)
        entry_point_encoded = b"".join(encoded_vals)
    elif isinstance(entry_point_val, Iterable):
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
    gid = Column(Gid, primary_key=True, server_default=FetchedValue())
    data = Column(JSONB, server_default=FetchedValue())

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
    def get_vshard(self) -> int:
        assert self.gid is not None, "Gid must be specified for extended vertex."
        return self.gid[1]


class EdgeMixin(EntityMixin):
    src = Column(Gid, primary_key=True)
    tgt = Column(Gid, primary_key=True)
    data = Column(JSONB)

    def __repr__(self) -> str:
        return "<{}(src={}, tgt={})>".format(
            self.__class__.__name__, self.src, self.tgt
        )

    def get_vshard(self) -> int:
        return self.src[1]


class CounterMixin(EntityMixin):
    src = Column(Gid, primary_key=True)
    count = Column(Integer)

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

    def id_chooser(self, query, ident: List[Tuple[int, int]]) -> Set[str]:
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

    def query_chooser(self, query) -> Set[str]:
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
        logger.debug("query_chooser: query=%r", query)
        ent_class = query._entities[0].expr  # pylint: disable=W0212
        if hasattr(ent_class, "class_"):
            ent_class: Union[VertexMixin, EdgeMixin] = ent_class.class_
        shards = set()
        bin_exprs = _get_query_comparisons(query)
        for column, operator, value in bin_exprs:
            if column.primary_key:
                if column.name not in {"gid", "src"}:
                    continue
                if operator == eq:
                    assert isinstance(value, tuple), value
                    assert len(value) == 2, value
                    vshard = value[1]
                    shards.add(self.jump_hash(vshard))
                elif operator == operators.in_op:
                    assert operator == operators.in_op, operator
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
            ):  # pylint: disable=W0212
                if operator == eq:
                    shards.add(self.jump_hash(entry_point_to_vshard(value)))
                elif operator == operators.in_op:
                    assert operator == operators.in_op, operator
                    for entry_point in value:
                        shards.add(self.jump_hash(entry_point_to_vshard(entry_point)))
                else:
                    assert False, "Unsupported operator %r" % operator
        if not shards:
            logger.warning("query_chooser: querying all shards.")
            shards = self.shards_set
        logger.debug("query_chooser: shards=%s", shards)
        return shards


def _get_query_comparisons(query):
    """
    Search an orm.Query object for binary expressions.

    Taken from:
    http://docs.sqlalchemy.org/en/latest/_modules/examples/sharding/attribute_shard.html

    Returns expressions which match a Column against one or more literal values
    as a list of tuples of the form (column, operator, values). `values` is a
    single value or tuple of values depending on the operator.
    """
    binds = {}
    clauses = set()
    comparisons = []

    def visit_bindparam(bind) -> None:
        # visit a bind parameter.

        # check in _params for it first
        if bind.key in query._params:  # pylint: disable=W0212
            value = query._params[bind.key]  # pylint: disable=W0212
        elif bind.callable:
            # some ORM functions (lazy loading)
            # place the bind's value as a
            # callable for deferred evaluation.
            value = bind.callable()
        else:
            # just use .value
            value = bind.value

        binds[bind] = value

    def visit_column(column) -> None:
        clauses.add(column)

    def visit_binary(binary) -> None:
        # special handling for "col IN (params)"
        if (
            binary.left in clauses
            and binary.operator == operators.in_op
            and hasattr(binary.right, "clauses")
        ):
            comparisons.append(
                (
                    binary.left,
                    binary.operator,
                    tuple(binds[bind] for bind in binary.right.clauses),
                )
            )
        elif binary.left in clauses and binary.right in binds:
            comparisons.append((binary.left, binary.operator, binds[binary.right]))

        elif binary.left in binds and binary.right in clauses:
            comparisons.append((binary.right, binary.operator, binds[binary.left]))

    # here we will traverse through the query's criterion, searching
    # for SQL constructs.  We will place simple column comparisons
    # into a list.
    if query._criterion is not None:  # pylint: disable=W0212
        visitors.traverse_depthfirst(
            query._criterion,  # pylint: disable=W0212
            {},
            {
                "bindparam": visit_bindparam,
                "binary": visit_binary,
                "column": visit_column,
            },
        )
    return comparisons
