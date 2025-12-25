from collections import OrderedDict
from typing import (
    Any,
    Dict,
    List,
    MutableMapping,
)

import toml

from .graph import (
    Array,
    ColoRef,
    Column,
    CompositeType,
    Counter,
    DataType,
    Edge,
    Enum,
    Function,
    Graph,
    Index,
    Vertex,
)


class InvalidSpec(Exception):
    pass


def graph_from_config_file(path: str) -> Graph:
    config = toml.load(path)
    return graph_from_config_dict(config)


def graph_from_config_toml(config: str) -> Graph:
    config_dict = toml.loads(config)
    return graph_from_config_dict(config_dict)


def graph_from_config_dict(config: MutableMapping[str, Any]) -> Graph:
    schema = config.get("schema", "graph")
    fns: Dict[str, Function] = OrderedDict()
    fns_raw = config.get("function", {})
    for fn_name, fn_raw in fns_raw.items():
        fns[fn_name] = Function(fn_name, fn_raw)

    enums: Dict[str, Enum] = OrderedDict()
    enums_raw = config.get("enum", {})
    for enum_name, enum_raw in enums_raw.items():
        if "values" not in enum_raw:
            raise InvalidSpec("No values specified for enum: {!r}".format(enum_name))
        values = enum_raw["values"]
        if len(values) == 0:
            raise InvalidSpec(
                "At least one value must be specified for enum: {!r}".format(enum_name)
            )
        added_values = enum_raw.get("added_values", [])
        enums[enum_name] = Enum(
            schema,
            enum_name,
            enum_raw["values"],
            added_values,
            enum_raw.get("drop", False),
        )

    def col_raw_to_col(col_raw: Any) -> Column:
        if len(col_raw) == 2:
            return Column(col_raw[0], col_raw[1], False, None, False, False)
        else:
            assert False, "Bad Column specification."

    vertices: Dict[str, Vertex] = OrderedDict()
    vertices_raw = config.get("vertex", {})
    edges_raw = config.get("edge", {})
    for v_name, v_raw in vertices_raw.items():
        extends_raw = v_raw.get("extends")
        if extends_raw:
            if extends_raw not in vertices:
                raise InvalidSpec("Vertex %r not found" % extends_raw)
            extends = vertices.get(extends_raw)
        else:
            extends = None

        cols_raw = v_raw.get("cols", [])
        cols = [col_raw_to_col(col_raw) for col_raw in cols_raw]
        for col in cols:
            if col.name not in v_raw.get("col", {}):
                continue
            opts = v_raw["col"][col.name]
            nullable = opts.get("nullable", False)
            if not isinstance(nullable, bool):
                raise InvalidSpec(
                    "Bad value for nullable {!r}, must be bool.".format(nullable)
                )
            col.nullable = nullable
            default = opts.get("default")
            if not isinstance(default, (str, type(None))):
                raise InvalidSpec(
                    "Bad value for default {!r}, must be string.".format(default)
                )
            col.default = default
            col.drop = opts.get("drop")
            del v_raw["col"][col.name]
        # Check for options applied to non-existent columns.
        if v_raw.get("col"):
            raise InvalidSpec("Invalid column: %r" % next(iter(v_raw["col"].keys())))
        cols_map = {col.name: col for col in cols}

        entry_point_raw = v_raw.get("entry_point")
        entry_point = None
        if entry_point_raw:
            for col in cols:
                if col.name == entry_point_raw:
                    entry_point = col
                    if entry_point.drop:
                        raise InvalidSpec(
                            "entry_point %r cannot be dropped." % entry_point.name
                        )
                    break
            else:
                raise InvalidSpec("entry_point column %r not found." % entry_point_raw)
        data_keys = v_raw.get("data_keys", [])
        v_drop = v_raw.get("drop", False)
        indexes = []
        for index_name, index_raw in v_raw.get("index", {}).items():
            if "cols" not in index_raw:
                raise InvalidSpec("Index must specify cols.")
            index_cols = index_raw["cols"]
            method = index_raw.get("method", "btree")
            unique = index_raw.get("unique", False)
            predicate = index_raw.get("where")
            index_drop = index_raw.get("drop", False)
            for index_col in index_cols:
                if "(" in index_col or " " in index_col:
                    # FIXME: Do not currently handle more complex index
                    # expressions.
                    continue
                if index_col not in cols_map:
                    raise InvalidSpec("Invalid column: {}".format(index_col))
                # FIXME: Add tests for this!
                if not v_drop and not index_drop and cols_map[index_col].drop:
                    raise InvalidSpec("Index on dropped column.")
            indexes.append(
                Index(index_name, index_cols, method, unique, predicate, index_drop)
            )
        vertex = Vertex(
            schema, v_name, extends, cols, entry_point, data_keys, indexes, v_drop
        )
        vertices[vertex.name] = vertex
        if extends:
            extends.add_extends_backref(vertex)

    ctypes: Dict[str, CompositeType] = OrderedDict()
    ctypes_raw = config.get("ctype", {})
    for ctype_name, ctype_raw in ctypes_raw.items():
        if "fields" not in ctype_raw:
            raise InvalidSpec(
                "No fields specified for composite type: {!r}".format(ctype_name)
            )
        fields_raw = ctype_raw["fields"]
        if len(fields_raw) == 0:
            raise InvalidSpec(
                "At least one field must be specified for composite type: {!r}".format(
                    ctype_name
                )
            )
        fields = []
        for field_raw in fields_raw:
            if len(field_raw) != 2:
                raise InvalidSpec(
                    "Field must specify (name, type): {!r}".format(ctype_name)
                )
            fields.append(
                (
                    field_raw[0],
                    data_type_resolver(field_raw[1], vertices, enums, ctypes),
                )
            )
        ctypes[ctype_name] = CompositeType(
            schema, ctype_name, fields, ctype_raw.get("drop", False)
        )

    for vertex in vertices.values():
        col_resolver_and_validator(vertex.cols, vertices, enums, ctypes, vertex.drop)
        entry_point_validator(vertex)

    edges: Dict[str, Edge] = OrderedDict()
    for e_name, e_raw in edges_raw.items():
        if "src" not in e_raw:
            raise InvalidSpec("Edge {!r} missing src.".format(e_name))
        if e_raw["src"] not in vertices:
            raise InvalidSpec(
                "Edge {!r} has invalid src {!r}.".format(e_name, e_raw["src"])
            )
        if "tgt" not in e_raw:
            raise InvalidSpec("Edge {!r} missing tgt.".format(e_name))
        if e_raw["tgt"] not in vertices:
            raise InvalidSpec(
                "Edge {!r} has invalid tgt {!r}.".format(e_name, e_raw["tgt"])
            )
        src = vertices[e_raw["src"]]
        if src.drop:
            raise InvalidSpec(
                "Cannot drop edge {!r} src {!r}.".format(e_name, src.name)
            )
        tgt = vertices[e_raw["tgt"]]
        if tgt.drop:
            raise InvalidSpec(
                "Cannot drop edge {!r} tgt {!r}.".format(e_name, tgt.name)
            )
        cols_raw = e_raw.get("cols", [])
        edge_cols = {col_raw[0]: col_raw_to_col(col_raw) for col_raw in cols_raw}
        for col in edge_cols.values():
            if col.name not in e_raw.get("col", {}):
                continue
            opts = e_raw["col"][col.name]
            nullable = opts.get("nullable", False)
            if not isinstance(nullable, bool):
                raise InvalidSpec(
                    "Bad value for nullable {!r}, must be bool.".format(nullable)
                )
            col.nullable = nullable
            default = opts.get("default")
            if not isinstance(default, (str, type(None))):
                raise InvalidSpec(
                    "Bad value for default {!r}, must be string.".format(default)
                )
            col.default = default
            is_pk = opts.get("primary_key", False)
            if not isinstance(is_pk, bool):
                raise InvalidSpec(
                    "Bad value for primary_key {!r}, must be bool.".format(col.name)
                )
            col.primary_key = is_pk
            col.drop = opts.get("drop")
            if col.primary_key and col.drop:
                raise InvalidSpec(
                    "Cannot drop primary key column {!r}.".format(col.name)
                )
            del e_raw["col"][col.name]
        # Check for options applied to non-existent columns.
        if e_raw.get("col"):
            raise InvalidSpec("Invalid column: %r" % next(iter(e_raw["col"].keys())))
        data_keys = e_raw.get("data_keys", [])
        indexes = []
        for index_name, index_raw in e_raw.get("index", {}).items():
            if "cols" not in index_raw:
                raise InvalidSpec("Index must specify cols.")
            index_cols = index_raw["cols"]
            method = index_raw.get("method", "btree")
            unique = index_raw.get("unique", False)
            predicate = index_raw.get("where")
            index_drop = index_raw.get("drop", False)
            indexes.append(
                Index(index_name, index_cols, method, unique, predicate, index_drop)
            )
        counters = []
        for counter_name, counter_raw in e_raw.get("counter", {}).items():
            if "cols" not in counter_raw:
                raise InvalidSpec("Counter must specify cols.")
            counter_cols = counter_raw["cols"]
            counter_drop = counter_raw.get("drop", False)
            for counter_col in counter_cols:
                if counter_col not in edge_cols:
                    raise InvalidSpec("Invalid column: {!r}".format(counter_col))
                if not counter_drop and edge_cols[counter_col].drop:
                    raise InvalidSpec("Cannot drop column {!r}.".format(counter_col))
            counter = Counter(e_name, counter_name, counter_cols, counter_drop)
            counters.append(counter)
            src.add_counter_backref(counter)
        e_drop = e_raw.get("drop", False)
        edges[e_name] = Edge(
            schema,
            e_name,
            src,
            tgt,
            list(edge_cols.values()),
            data_keys,
            indexes,
            counters,
            e_drop,
        )

    for edge in edges.values():
        col_resolver_and_validator(edge.cols, vertices, enums, ctypes, edge.drop)

    return Graph(schema, fns, enums, ctypes, vertices, edges)


def col_resolver_and_validator(
    cols: List[Column],
    vertices: Dict[str, Vertex],
    enums: Dict[str, Enum],
    ctypes: Dict[str, CompositeType],
    dropped: bool,
) -> None:
    """
    Mutates `cols` by resolving and setting the correct data_type.

    Raises:
        - InvalidSpec
    """
    for col in cols:
        assert isinstance(col.data_type, str)
        is_array = False
        if col.data_type.endswith("[]"):
            is_array = True
            col.data_type = col.data_type[: -len("[]")]
        if col.data_type.startswith("->"):
            ref_name = col.data_type[len("->") :]
            if ref_name not in vertices:
                raise InvalidSpec("Undefined vertex: %r" % col.data_type)
            if not dropped and not col.drop and vertices[ref_name].drop:
                raise InvalidSpec(
                    "Column %r cannot reference dropped vertex %r."
                    % (col.name, ref_name)
                )
            col.data_type = vertices[ref_name]
        elif col.data_type.startswith("-)"):
            ref_name = col.data_type[len("-)") :]
            if ref_name not in vertices:
                raise InvalidSpec("Undefined vertex: %r" % col.data_type)
            if not dropped and not col.drop and vertices[ref_name].drop:
                raise InvalidSpec(
                    "Column %r cannot reference dropped vertex %r."
                    % (col.name, ref_name)
                )
            col.data_type = ColoRef(vertices[ref_name])
        elif col.data_type.startswith("enum:"):
            ref_name = col.data_type[len("enum:") :]
            if ref_name not in enums:
                raise InvalidSpec("Undefined enum: %r" % col.data_type)
            col.data_type = enums[ref_name]
        elif col.data_type.startswith("ctype:"):
            ref_name = col.data_type[len("ctype:") :]
            if ref_name not in ctypes:
                raise InvalidSpec("Undefined composite type: %r" % col.data_type)
            if not dropped and not col.drop and ctypes[ref_name].drop:
                raise InvalidSpec(
                    "Column %r cannot reference dropped composite type %r."
                    % (col.name, ref_name)
                )
            col.data_type = ctypes[ref_name]
        if is_array:
            col.data_type = Array(col.data_type)


def entry_point_validator(vertex: Vertex) -> None:
    """
    Validates that the entry_point references a Byte, Text, or CompositeType of
    texts, and if the latter, that it isn't dropped.

    Raises:
        - InvalidSpec
    """
    if not vertex.entry_point:
        return
    entry_point_dt = vertex.entry_point.data_type
    if isinstance(entry_point_dt, CompositeType):
        if entry_point_dt.drop and not vertex.drop:
            raise InvalidSpec(
                "entry_point %r cannot reference dropped composite type %r."
                % (vertex.entry_point.name, entry_point_dt.name)
            )
        for field_name, field_data_type in entry_point_dt.fields:
            if field_data_type != "Text":
                raise InvalidSpec(
                    "entry_point %r requires %r.%r to be a Text column."
                    % (
                        vertex.entry_point.name,
                        entry_point_dt.name,
                        field_name,
                    )
                )
    elif isinstance(entry_point_dt, Array):
        if not isinstance(entry_point_dt.element_type, Vertex):
            raise InvalidSpec(
                "entry_point %r required to be an array of vertices."
                % (vertex.entry_point.name,)
            )
        if entry_point_dt.element_type.drop and not vertex.drop:
            raise InvalidSpec(
                "entry_point %r cannot reference dropped vertex type %r."
                % (vertex.entry_point.name, entry_point_dt.element_type.name)
            )
    elif entry_point_dt == "Text" or entry_point_dt == "Binary":
        pass
    else:
        raise InvalidSpec(
            "entry_point %r must reference Binary, Text, or CompositeType of Texts."
            % vertex.entry_point.name
        )


def data_type_resolver(
    data_type_raw: str,
    vertices: Dict[str, Vertex],
    enums: Dict[str, Enum],
    ctypes: Dict[str, CompositeType],
) -> DataType:
    is_array = False
    if data_type_raw.endswith("[]"):
        is_array = True
        data_type_raw = data_type_raw[: -len("[]")]
    data_type: DataType
    if data_type_raw.startswith("->"):
        ref_name = data_type_raw[len("->") :]
        if ref_name not in vertices:
            raise InvalidSpec("Undefined vertex: %r" % ref_name)
        data_type = vertices[ref_name]
    elif data_type_raw.startswith("-)"):
        ref_name = data_type_raw[len("-)") :]
        raise InvalidSpec(f"Unsupported reference to colo-ed vertex '{ref_name}'.")
    elif data_type_raw.startswith("enum:"):
        ref_name = data_type_raw[len("enum:") :]
        if ref_name not in enums:
            raise InvalidSpec("Undefined enum: %r" % ref_name)
        data_type = enums[ref_name]
    elif data_type_raw.startswith("ctype:"):
        ref_name = data_type_raw[len("ctype:") :]
        if ref_name not in ctypes:
            raise InvalidSpec("Undefined composite type: %r" % ref_name)
        data_type = ctypes[ref_name]
    else:
        data_type = data_type_raw
    if is_array:
        return Array(data_type)
    else:
        return data_type
