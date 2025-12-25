#!/usr/bin/env python

import grapdb.graph
import grapdb.parser
from grapdb.parser import InvalidSpec
import textwrap
import unittest


class TestBasic(unittest.TestCase):
    def test_vertex(self) -> None:
        # Test empty vertex with all default options
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 1
        v = graph.vertices["V"]
        assert v.name == "V"
        assert v.extends is None
        assert len(v.extra_cols) == 0
        assert v.entry_point is None
        assert len(v.cols) == 2
        assert len(v.data_keys) == 0

        create_base_stmts = v.to_sql_stmt_create_base()
        assert create_base_stmts[0] == textwrap.dedent(
            """\
            CREATE TABLE graph."V" (
              "gid" gid NOT NULL,
              "data" JSONB NOT NULL DEFAULT '{}',
              PRIMARY KEY (gid),
              CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)
            );"""
        )
        assert (
            create_base_stmts[1]
            == "CREATE SEQUENCE graph.V_gid_id_seq OWNED BY graph.V.gid;"
        )
        assert create_base_stmts[2] == textwrap.dedent(
            """\
             CREATE TRIGGER V_insert_trigger
               BEFORE INSERT ON graph."V"
               FOR EACH ROW
               EXECUTE PROCEDURE
                 gid_pk_insert_trig("graph.V_gid_id_seq");"""
        )
        assert len(create_base_stmts) == 3

        assert v.to_sql_stmt_drop() == 'DROP TABLE graph."V";'
        assert len(v.to_sql_stmt_create_index()) == 0

        # Test vertex with entry point
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Text"]]
            entry_point="col1"
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 1
        v = graph.vertices["V"]
        assert v.name == "V"
        assert v.extends is None
        assert len(v.extra_cols) == 1
        assert v.cols[-1].name == "col1"
        assert v.entry_point == v.cols[-1]
        assert len(v.cols) == 3
        assert len(v.data_keys) == 0

        assert len(v.to_sql_stmt_create_index()) == 1
        create_base_stmts = v.to_sql_stmt_create_base()
        assert create_base_stmts[0] == textwrap.dedent(
            """\
            CREATE TABLE graph."V" (
              "gid" gid NOT NULL,
              "data" JSONB NOT NULL DEFAULT '{}',
              PRIMARY KEY (gid),
              CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)
            );"""
        )
        assert (
            create_base_stmts[1]
            == "CREATE SEQUENCE graph.V_gid_id_seq OWNED BY graph.V.gid;"
        )
        assert create_base_stmts[2] == textwrap.dedent(
            """\
            CREATE TRIGGER V_insert_trigger
              BEFORE INSERT ON graph."V"
              FOR EACH ROW
              EXECUTE PROCEDURE
                gid_pk_insert_trig("graph.V_gid_id_seq");"""
        )
        alter_stmts = v.to_sql_stmt_create_alters()
        assert (
            alter_stmts[0] == 'ALTER TABLE graph."V" ADD COLUMN "col1" Text NOT NULL;'
        )
        assert len(alter_stmts) == 1
        assert v.to_sql_stmt_create_index()[0] == (
            "CREATE UNIQUE INDEX CONCURRENTLY V__entry_point ON "
            'graph."V" USING btree (col1);'
        )

        # Try vertex with invalid entry point
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Text"]]
            entry_point="col2"
            """
        )
        with self.assertRaises(Exception) as context:
            grapdb.parser.graph_from_config_toml(config)
        assert str(context.exception) == "entry_point column 'col2' not found."

        # Try vertex with invalid entry point due to type
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Integer"]]
            entry_point="col1"
            """
        )
        with self.assertRaises(Exception) as context:
            grapdb.parser.graph_from_config_toml(config)
        assert (
            str(context.exception)
            == "entry_point 'col1' must reference Text or CompositeType of Texts."
        )

        # Test vertex with composite type entry point
        config = textwrap.dedent(
            """\
            [ctype.ref]
            fields = [["x", "Text"], ["y", "Text"]]

            [vertex.V]
            cols=[["col1", "ctype:ref"]]
            entry_point="col1"
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        v = graph.vertices["V"]
        assert v.entry_point

        # Try vertex with unsupported composite type for entry point
        config = textwrap.dedent(
            """\
            [ctype.ref]
            fields = [["x", "Text"], ["y", "Integer"]]

            [vertex.V]
            cols=[["col1", "ctype:ref"]]
            entry_point="col1"
            """
        )
        with self.assertRaises(Exception) as context:
            grapdb.parser.graph_from_config_toml(config)
        assert (
            str(context.exception)
            == "entry_point 'col1' requires 'ref'.'y' to be a Text column."
        )

        # Test vertex that extends
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            cols=[["col1", "Text"]]

            [vertex.Y]
            extends="X"
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 2
        x = graph.vertices["X"]
        y = graph.vertices["Y"]
        assert y.extends == x

        create_base_stmts = y.to_sql_stmt_create_base()
        self.assertEqual(
            create_base_stmts[0],
            textwrap.dedent(
                """\
                CREATE TABLE graph."Y" (
                  "gid" gid NOT NULL,
                  "data" JSONB NOT NULL DEFAULT '{}',
                  PRIMARY KEY (gid),
                  FOREIGN KEY (gid) REFERENCES graph."X" (gid),
                  CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)
                );"""
            ),
        )
        # Since it extends another vertex, there shouldn't be a gid id
        # sequence or a trigger statement that auto-populates a gid.
        assert len(create_base_stmts) == 1

        # Try vertex with invalid extends
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            cols=[["col1", "Text"]]

            [vertex.Y]
            extends="Z"
            """
        )
        with self.assertRaises(Exception) as context:
            grapdb.parser.graph_from_config_toml(config)
        assert str(context.exception) == "Vertex 'Z' not found"

        # Test vertex with data keys
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            data_keys=["key1", "key2"]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 1
        v = graph.vertices["V"]
        assert v.name == "V"
        assert v.extends is None
        assert len(v.extra_cols) == 0
        assert v.entry_point is None
        assert len(v.cols) == 2
        assert len(v.data_keys) == 2
        assert v.data_keys == ["key1", "key2"]

        assert len(v.to_sql_stmt_create_index()) == 0
        self.assertEqual(
            v.to_sql_stmt_create_base()[0],
            textwrap.dedent(
                """\
                CREATE TABLE graph."V" (
                  "gid" gid NOT NULL,
                  "data" JSONB NOT NULL DEFAULT '{}',
                  PRIMARY KEY (gid),
                  CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)
                );"""
            ),
        )

    def test_vertex_alters(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Text"], ["col2", "Text"]]
            col.col2.nullable = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        v = graph.vertices["V"]
        self.assertEqual(
            v.to_sql_stmt_create_base()[0],
            textwrap.dedent(
                """\
                CREATE TABLE graph."V" (
                  "gid" gid NOT NULL,
                  "data" JSONB NOT NULL DEFAULT '{}',
                  PRIMARY KEY (gid),
                  CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)
                );"""
            ),
        )
        self.assertEqual(
            v.to_sql_stmt_create_alters()[0],
            'ALTER TABLE graph."V" ADD COLUMN "col1" Text NOT NULL;',
        )
        self.assertEqual(
            v.to_sql_stmt_create_alters()[1],
            'ALTER TABLE graph."V" ADD COLUMN "col2" Text;',
        )

    def test_bad_col_modifier(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Text"], ["col2", "Text"]]
            col.col3.nullable = true
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Invalid column: 'col3'"

        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            [vertex.Y]

            [edge]

            [edge.A]
            src = "X"
            tgt = "Y"
            cols=[["col1", "Text"], ["col2", "Text"]]
            col.col4.nullable = true
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Invalid column: 'col4'"

    def test_edge(self) -> None:
        # Try edge without src/tgt
        config = textwrap.dedent(
            """\
            [edge]
            [edge.A]
            cols = [["col1", "Text"]]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Edge 'A' missing src."

        # Try edge without tgt
        config = textwrap.dedent(
            """\
            [vertex]
            [vertex.X]

            [edge]
            [edge.A]
            src = "X"
            cols = [["col1", "Text"]]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Edge 'A' missing tgt."

        # Try edge with invalid src
        config = textwrap.dedent(
            """\
            [vertex]
            [vertex.X]

            [edge]
            [edge.A]
            src = "Z"
            tgt = "X"
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Edge 'A' has invalid src 'Z'."

        # Try edge with invalid tgt
        config = textwrap.dedent(
            """\
                    [vertex]
                    [vertex.X]

                    [edge]
                    [edge.A]
                    src = "X"
                    tgt = "W"
                    """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Edge 'A' has invalid tgt 'W'."

        # Test basic edge
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            [vertex.Y]
                    
            [edge]
                    
            [edge.A]
            src = "X"
            tgt = "Y"
            cols = [["col1", "Text"]]
            data_keys = ["key1", "key2"]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 2
        v1 = graph.vertices["X"]
        v2 = graph.vertices["Y"]

        e = graph.edges["A"]
        assert e.src == v1
        assert e.tgt == v2
        assert len(e.extra_cols) == 1
        assert len(e.cols) == 4
        assert len(e.data_keys) == 2
        assert e.data_keys == ["key1", "key2"]

        self.assertEqual(
            e.to_sql_stmt_create_base()[0],
            textwrap.dedent(
                """\
                CREATE TABLE graph."A" (
                  "src" gid NOT NULL,
                  "tgt" gid NOT NULL,
                  "data" JSONB NOT NULL DEFAULT '{}',
                  PRIMARY KEY (src, tgt),
                  FOREIGN KEY (src) REFERENCES graph."X" (gid),
                  CHECK ((src).id IS NOT NULL AND (src).vshard IS NOT NULL),
                  CHECK ((tgt).id IS NOT NULL AND (tgt).vshard IS NOT NULL)
                );"""
            ),
        )
        self.assertEqual(
            e.to_sql_stmt_create_alters()[0],
            'ALTER TABLE graph."A" ADD COLUMN "col1" Text NOT NULL;',
        )

        # Test index
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            [vertex.Y]

            [edge]

            [edge.A]
            src = "X"
            tgt = "Y"
            cols = [["col1", "Text"]]
            data_keys = ["key1", "key2"]
            
            [edge.A.index.homog]
            cols = ["col1"]
            
            [edge.A.index.hybrid]
            cols = ["col1"]
            where = "col1='hello'"

            [edge.A.index.test]
            cols = ["col1"]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 2
        v1 = graph.vertices["X"]
        v2 = graph.vertices["Y"]

        e = graph.edges["A"]
        assert e.src == v1
        assert e.tgt == v2
        assert len(e.extra_cols) == 1
        assert len(e.cols) == 4
        assert len(e.data_keys) == 2
        assert e.data_keys == ["key1", "key2"]

        self.assertEqual(
            e.to_sql_stmt_create_base()[0],
            textwrap.dedent(
                """\
                CREATE TABLE graph."A" (
                  "src" gid NOT NULL,
                  "tgt" gid NOT NULL,
                  "data" JSONB NOT NULL DEFAULT '{}',
                  PRIMARY KEY (src, tgt),
                  FOREIGN KEY (src) REFERENCES graph."X" (gid),
                  CHECK ((src).id IS NOT NULL AND (src).vshard IS NOT NULL),
                  CHECK ((tgt).id IS NOT NULL AND (tgt).vshard IS NOT NULL)
                );"""
            ),
        )
        self.assertEqual(
            e.to_sql_stmt_create_alters()[0],
            'ALTER TABLE graph."A" ADD COLUMN "col1" Text NOT NULL;',
        )
        self.assertEqual(
            e.to_sql_stmt_create_index()[0],
            (
                'CREATE INDEX CONCURRENTLY A__homog ON graph."A" '
                'USING btree (src, "col1");'
            ),
        )

        self.assertEqual(
            e.to_sql_stmt_create_index()[1],
            (
                'CREATE INDEX CONCURRENTLY A__hybrid ON graph."A" '
                "USING btree (src, \"col1\") WHERE col1='hello';"
            ),
        )

        # Test dropped index
        self.assertEqual(
            e.to_sql_stmt_create_index()[2],
            "DROP INDEX CONCURRENTLY graph.A__test;",
        )

    def test_edge_pk_cols(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            [vertex.Y]

            [edge]

            [edge.A]
            src = "X"
            tgt = "Y"
            cols = [["col1", "Text"], ["col2", "Text"]]
            col.col1.primary_key = true
            col.col2.primary_key = false
            data_keys = ["key1", "key2"]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 2
        v1 = graph.vertices["X"]
        v2 = graph.vertices["Y"]

        e = graph.edges["A"]
        assert e.src == v1
        assert e.tgt == v2
        assert len(e.base_cols) == 4
        assert len(e.extra_cols) == 2
        assert len(e.cols) == 5
        assert len(e.data_keys) == 2
        assert e.data_keys == ["key1", "key2"]

        self.assertEqual(
            e.to_sql_stmt_create_base()[0],
            textwrap.dedent(
                """\
                CREATE TABLE graph."A" (
                  "src" gid NOT NULL,
                  "tgt" gid NOT NULL,
                  "data" JSONB NOT NULL DEFAULT '{}',
                  "col1" Text NOT NULL,
                  PRIMARY KEY (src, tgt, col1),
                  FOREIGN KEY (src) REFERENCES graph."X" (gid),
                  CHECK ((src).id IS NOT NULL AND (src).vshard IS NOT NULL),
                  CHECK ((tgt).id IS NOT NULL AND (tgt).vshard IS NOT NULL)
                );"""
            ),
        )
        self.assertEqual(
            e.to_sql_stmt_create_alters()[0],
            'ALTER TABLE graph."A" ADD COLUMN "col2" Text NOT NULL;',
        )

    def test_edge_alters(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            [vertex.Y]

            [edge]

            [edge.A]
            src = "X"
            tgt = "Y"
            cols = [["col1", "Text"]]
            data_keys = ["key1", "key2"]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 2
        v1 = graph.vertices["X"]
        v2 = graph.vertices["Y"]

        e = graph.edges["A"]
        assert e.src == v1
        assert e.tgt == v2
        assert len(e.extra_cols) == 1
        assert len(e.cols) == 4
        assert len(e.data_keys) == 2
        assert e.data_keys == ["key1", "key2"]

        self.assertEqual(
            e.to_sql_stmt_create_base()[0],
            textwrap.dedent(
                """\
                CREATE TABLE graph."A" (
                  "src" gid NOT NULL,
                  "tgt" gid NOT NULL,
                  "data" JSONB NOT NULL DEFAULT '{}',
                  PRIMARY KEY (src, tgt),
                  FOREIGN KEY (src) REFERENCES graph."X" (gid),
                  CHECK ((src).id IS NOT NULL AND (src).vshard IS NOT NULL),
                  CHECK ((tgt).id IS NOT NULL AND (tgt).vshard IS NOT NULL)
                );"""
            ),
        )
        self.assertEqual(
            e.to_sql_stmt_create_alters()[0],
            'ALTER TABLE graph."A" ADD COLUMN "col1" Text NOT NULL;',
        )

    def test_vertex_ref(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            cols = [
                ["col1", "Text"]
            ]

            [vertex.Y]
            cols = [
                ["x1", "->X"],
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        y = graph.vertices["Y"]
        create_alters = y.to_sql_stmt_create_alters()
        self.assertEqual(
            create_alters[0], 'ALTER TABLE graph."Y" ADD COLUMN "x1" gid NOT NULL;'
        )

        # Try missing vertex ref def
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            cols = [
                ["v1", "->Y"],
                ["col1", "Text"]
            ]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Undefined vertex: '->Y'"

    def test_vertex_ref_colo(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            cols = [
                ["col1", "Text"]
            ]

            [vertex.Y]
            cols = [
                ["x1", "-)X"],
            ]

            [edge.E]
            src="X"
            tgt="Y"
            cols = [
                ["x2", "-)X"],
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        y = graph.vertices["Y"]
        create_alters = y.to_sql_stmt_create_alters()
        self.assertEqual(
            create_alters[0], 'ALTER TABLE graph."Y" ADD COLUMN "x1" gid NOT NULL;'
        )

        create_indexes = y.to_sql_stmt_create_index()
        self.assertEqual(
            create_indexes[0],
            'ALTER TABLE graph.Y ADD CONSTRAINT Y_x1__fk FOREIGN KEY ("x1") '
            "REFERENCES graph.X (gid);",
        )
        e = graph.edges["E"]
        create_indexes = e.to_sql_stmt_create_index()
        self.assertEqual(
            create_indexes[0],
            'ALTER TABLE graph.E ADD CONSTRAINT E_x2__fk FOREIGN KEY ("x2") '
            "REFERENCES graph.X (gid);",
        )

        # Try bad ref
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.X]
            [vertex.Y]

            [edge.E]
            src="X"
            tgt="Y"
            cols = [
                ["x2", "-)Z"],
            ]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Undefined vertex: '-)Z'"

    def test_enum(self) -> None:
        config = textwrap.dedent(
            """\
            [enum.day_of_the_week]
            values = [
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ]

            [vertex]
            [vertex.X]
            cols = [
                ["day", "enum:day_of_the_week"],
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.enums) == 1
        dotw_enum = graph.enums["day_of_the_week"]
        assert len(dotw_enum.to_sql_decl()) == 1
        self.assertEqual(
            dotw_enum.to_sql_decl()[0],
            "CREATE TYPE graph.day_of_the_week AS ENUM ('Sunday', 'Monday', "
            "'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday');",
        )
        v1 = graph.vertices["X"]
        col = v1.extra_cols[0]
        assert col.name == "day"
        assert col.data_type == dotw_enum
        self.assertEqual(
            dotw_enum.to_sql_drop(),
            "DROP TYPE graph.day_of_the_week;",
        )

        create_alters = v1.to_sql_stmt_create_alters()
        self.assertEqual(
            create_alters[0],
            'ALTER TABLE graph."X" ADD COLUMN "day" graph.day_of_the_week ' "NOT NULL;",
        )

        # Try missing enum definition
        config = textwrap.dedent(
            """\
            [vertex]
            [vertex.X]
            cols = [
                ["day", "enum:missing"],
            ]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Undefined enum: 'enum:missing'"

        # Try empty enum def
        config = textwrap.dedent(
            """\
            [enum.test]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "No values specified for enum: 'test'"

        # Try enum with no values
        config = textwrap.dedent(
            """\
            [enum.test]
            values = []
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert (
            ctx.exception.args[0]
            == "At least one value must be specified for enum: 'test'"
        )

        # Test added_values
        config = textwrap.dedent(
            """\
            [enum.day_of_the_week]
            values = [
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
            ]
            added_values = [
                "Thursday",
                "Friday",
                "Saturday",
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.enums) == 1
        dotw_enum = graph.enums["day_of_the_week"]
        assert len(dotw_enum.to_sql_decl()) == 4
        self.assertEqual(
            dotw_enum.to_sql_decl()[0],
            "CREATE TYPE graph.day_of_the_week AS ENUM ('Sunday', 'Monday', "
            "'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday');",
        )
        self.assertEqual(
            dotw_enum.to_sql_decl()[1],
            "ALTER TYPE graph.day_of_the_week ADD VALUE 'Thursday';",
        )
        self.assertEqual(
            dotw_enum.to_sql_decl()[2],
            "ALTER TYPE graph.day_of_the_week ADD VALUE 'Friday';",
        )
        self.assertEqual(
            dotw_enum.to_sql_decl()[3],
            "ALTER TYPE graph.day_of_the_week ADD VALUE 'Saturday';",
        )

        #
        # Test dropping enum
        #
        config = textwrap.dedent(
            """\
            [enum.day_of_the_week]
            values = [
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
            ]
            added_values = [
                "Thursday",
                "Friday",
                "Saturday",
            ]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.enums) == 1
        dotw_enum = graph.enums["day_of_the_week"]
        assert len(dotw_enum.to_sql_decl()) == 1
        self.assertEqual(
            dotw_enum.to_sql_decl()[0],
            "DROP TYPE graph.day_of_the_week;",
        )

    def test_composite_type(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]
            [vertex.X]
            cols = [
                ["a", "Integer"],
            ]

            [ctype.test]
            fields = [
                ["x", "->X"],
                ["y", "Integer"],
            ]

            [vertex.Y]
            cols = [
                ["t", "ctype:test"],
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.ctypes) == 1
        test_ctype = graph.ctypes["test"]
        assert len(test_ctype.to_sql_decl()) == 1
        self.assertEqual(
            test_ctype.to_sql_decl()[0],
            "CREATE TYPE graph.test AS (x gid, y Integer);",
        )
        self.assertEqual(
            test_ctype.to_sql_drop(),
            "DROP TYPE graph.test;",
        )
        vertex_y = graph.vertices["Y"]
        assert len(vertex_y.to_sql_stmt_create_alters()) == 1
        assert (
            vertex_y.to_sql_stmt_create_alters()[0]
            == 'ALTER TABLE graph."Y" ADD COLUMN "t" graph.test NOT NULL;'
        )

        # Try invalid field
        config = textwrap.dedent(
            """\
            [ctype.test]
            fields = [
                ["x", "->X"],
            ]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Undefined vertex: 'X'"

        # Test dropping ctype
        config = textwrap.dedent(
            """\
            [ctype.test]
            fields = [
                ["x", "Integer"],
            ]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.ctypes) == 1
        test_ctype = graph.ctypes["test"]
        assert len(test_ctype.to_sql_decl()) == 1
        self.assertEqual(
            test_ctype.to_sql_decl()[0],
            "DROP TYPE graph.test;",
        )

        # Try depending on dropped ctype
        config = textwrap.dedent(
            """\
            [ctype.test]
            fields = [
                ["x", "Integer"],
            ]
            drop = true

            [vertex.Y]
            cols = [
                ["t", "ctype:test"],
            ]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert (
            ctx.exception.args[0]
            == "Column 't' cannot reference dropped composite type 'test'."
        )

        config = textwrap.dedent(
            """\
            [ctype.point]
            fields = [
                ["x", "Integer"],
                ["y", "Integer"],
            ]

            [ctype.point_cloud]
            fields = [
                ["x", "ctype:point"],
                ["ys", "ctype:point[]"],
            ]

            [vertex.X]
            cols = [
                ["pairs", "ctype:point_cloud[]"],
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        point = graph.ctypes["point"]
        point_cloud = graph.ctypes["point_cloud"]
        assert point_cloud.fields[0][1] == point
        assert isinstance(point_cloud.fields[1][1], grapdb.graph.Array)
        assert point_cloud.fields[1][1].element_type == point

    def test_vertex_index(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Text"], ["col2", "Text"]]

            [vertex.V.index.col1]
            cols = ["col1"]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        v = graph.vertices["V"]
        assert len(v.to_sql_stmt_create_index()) == 1
        self.assertEqual(
            v.to_sql_stmt_create_index()[0],
            'CREATE INDEX CONCURRENTLY V__col1 ON graph."V" USING btree ("col1");',
        )

        # Try to omit cols
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Text"], ["col2", "Text"]]

            [vertex.V.index.col1]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Index must specify cols."

        # Drop index
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Text"], ["col2", "Text"]]

            [vertex.V.index.col1]
            cols = ["col1"]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        v = graph.vertices["V"]
        assert len(v.to_sql_stmt_create_index()) == 1
        self.assertEqual(
            v.to_sql_stmt_create_index()[0],
            "DROP INDEX CONCURRENTLY graph.V__col1;",
        )

        # Try col that does not exist
        config = textwrap.dedent(
            """\
            [vertex.V]
            cols=[["col1", "Text"], ["col2", "Text"]]

            [vertex.V.index.test]
            cols = ["col3"]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Invalid column: col3"

    def test_function(self) -> None:
        config = textwrap.dedent(
            '''\
            [function]
            testfn = """
            CREATE OR REPLACE FUNCTION testfn(text[]) RETURNS text[] AS
            $BODY$
              SELECT 'hello';
            $BODY$
              language sql IMMUTABLE;
            """
            '''
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.fns) == 1
        assert graph.fns["testfn"].sql == textwrap.dedent(
            """\
            CREATE OR REPLACE FUNCTION testfn(text[]) RETURNS text[] AS
            $BODY$
              SELECT 'hello';
            $BODY$
              language sql IMMUTABLE;
            """
        )

    def test_has_colos(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Text"], ["col2", "Text"]]

            [vertex.W]
            extends = "V"
            cols=[["col1", "Text"], ["col2", "Text"]]

            [vertex.X]
            cols=[["col1", "-)W"]]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert not graph.vertices["V"].has_colos()
        assert graph.vertices["W"].has_colos()
        assert graph.vertices["X"].has_colos()

    def test_drop(self) -> None:
        # Test drop vertex
        config = textwrap.dedent(
            """\
            [vertex.X]
            drop = true
            cols = [
                ["col1", "Text"]
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        x = graph.vertices["X"]
        assert x.to_sql_stmt_create_base()[0] == 'DROP TABLE graph."X";'
        create_alters = x.to_sql_stmt_create_alters()
        assert len(create_alters) == 0

        # Test drop column
        config = textwrap.dedent(
            """\
            [vertex.X]
            cols = [
                ["col1", "Text"]
            ]
            col.col1.drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        x = graph.vertices["X"]
        create_alters = x.to_sql_stmt_create_alters()
        assert create_alters[0] == 'ALTER TABLE graph."X" DROP COLUMN "col1";'

        # Test drop colo column
        config = textwrap.dedent(
            """\
            [vertex.X]
            cols = [
                ["col1", "-)Y"]
            ]
            col.col1.drop = true

            [vertex.Y]
            cols = [
                ["col1", "Text"]
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        x = graph.vertices["X"]
        create_alters = x.to_sql_stmt_create_alters()
        assert create_alters[0] == 'ALTER TABLE graph."X" DROP COLUMN "col1";'
        create_index = x.to_sql_stmt_create_index()
        assert len(create_index) == 0, create_index

        # Test drop index
        config = textwrap.dedent(
            """\
            [vertex.X]
            cols = [
                ["col1", "Text"]
            ]
            [vertex.X.index.test]
            cols = ["col1"]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        x = graph.vertices["X"]
        assert (
            x.to_sql_stmt_create_index()[0] == "DROP INDEX CONCURRENTLY graph.X__test;"
        )

        # Test drop vertex, column, and index
        config = textwrap.dedent(
            """\
            [vertex.X]
            drop = true
            cols = [
                ["col1", "Text"]
            ]
            col.col1.drop = true
            [vertex.X.index.test]
            cols = ["col1"]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        x = graph.vertices["X"]
        assert x.to_sql_stmt_create_base()[0] == 'DROP TABLE graph."X";'
        create_alters = x.to_sql_stmt_create_alters()
        assert len(create_alters) == 0
        assert len(x.to_sql_stmt_create_index()) == 0

        # Test drop vertex with index
        config = textwrap.dedent(
            """\
            [vertex.X]
            drop = true
            cols = [
                ["col1", "Text"]
            ]
            [vertex.X.index.test]
            cols = ["col1"]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        x = graph.vertices["X"]
        assert x.to_sql_stmt_create_base()[0] == 'DROP TABLE graph."X";'
        create_alters = x.to_sql_stmt_create_alters()
        assert len(create_alters) == 0
        assert len(x.to_sql_stmt_create_index()) == 0

        # Try to drop column w/o dropping index
        config = textwrap.dedent(
            """\
            [vertex.X]
            cols = [
                ["col1", "Text"]
            ]
            col.col1.drop = true
            [vertex.X.index.test]
            cols = ["col1"]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Index on dropped column."

        # Test drop column and drop index
        config = textwrap.dedent(
            """\
            [vertex.X]
            cols = [
                ["col1", "Text"]
            ]
            col.col1.drop = true
            [vertex.X.index.test]
            cols = ["col1"]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        x = graph.vertices["X"]
        assert (
            x.to_sql_stmt_create_index()[0] == "DROP INDEX CONCURRENTLY graph.X__test;"
        )

        # Try dropping vertex entry point
        config = textwrap.dedent(
            """\
            [vertex.X]
            cols = [
                ["col1", "Text"]
            ]
            entry_point = "col1"
            col.col1.drop = true
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "entry_point 'col1' cannot be dropped."

        # Try dropping vertex referred to by another vertex
        config = textwrap.dedent(
            """\
            [vertex.Y]
            drop = true
            [vertex.X]
            cols = [
                ["col1", "->Y"]
            ]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert (
            ctx.exception.args[0]
            == "Column 'col1' cannot reference dropped vertex 'Y'."
        )

        # Try dropping vertex referred to by another vertex
        config = textwrap.dedent(
            """\
            [vertex.Y]
            drop = true
            [vertex.X]
            cols = [
                ["col1", "-)Y"]
            ]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert (
            ctx.exception.args[0]
            == "Column 'col1' cannot reference dropped vertex 'Y'."
        )

        # Try dropping edge
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [edge.E]
            src="X"
            tgt="Y"
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        e = graph.edges["E"]
        assert e.to_sql_stmt_create_base()[0] == 'DROP TABLE graph."E";'

        # Try dropping vertex that edge depends on for src/tgt
        config = textwrap.dedent(
            """\
            [vertex.X]
            drop = true
            [vertex.Y]
            [edge.E]
            src="X"
            tgt="Y"
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Cannot drop edge 'E' src 'X'."

        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            drop = true
            [edge.E]
            src="X"
            tgt="Y"
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Cannot drop edge 'E' tgt 'Y'."

        # Try dropping vertex that edge depends on for field
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [vertex.Z]
            drop = true
            [edge.E]
            src="X"
            tgt="Y"
            cols = [["col1", "->Z"]]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert (
            ctx.exception.args[0]
            == "Column 'col1' cannot reference dropped vertex 'Z'."
        )

        # Test drop vertex and dependent field
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [vertex.Z]
            drop = true
            [edge.E]
            src="X"
            tgt="Y"
            cols = [["col1", "->Z"]]
            col.col1.drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        e = graph.edges["E"]
        assert (
            e.to_sql_stmt_create_alters()[0]
            == 'ALTER TABLE graph."E" DROP COLUMN "col1";'
        )
        assert "col1" not in e.to_sql_stmt_create_base()

        # Test drop vertex and dependent edge
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [vertex.Z]
            drop = true
            [edge.E]
            src="X"
            tgt="Y"
            cols = [["col1", "->Z"]]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        e = graph.edges["E"]
        assert e.to_sql_stmt_create_base()[0] == 'DROP TABLE graph."E";'

        # Try dropping primary key
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [edge.E]
            src="X"
            tgt="Y"
            cols = [["col1", "Text"]]
            col.col1.primary_key = true
            col.col1.drop = true
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Cannot drop primary key column 'col1'."

        # Test dropped counter
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [edge.E]
            src = "X"
            tgt = "Y"
            cols = [
                ["f", "Boolean"],
            ]
            [edge.E.counter.test]
            cols = ["f"]
            drop = true
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        e = graph.edges["E"]
        assert len(e.to_sql_stmt_create_base()) == 2
        assert e.to_sql_stmt_create_base()[1] == "DROP TABLE graph.E_counter_test;"

        # Try to drop field that a counter depends on
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [edge.E]
            src = "X"
            tgt = "Y"
            cols = [
                ["f", "Boolean"],
            ]
            col.f.drop = true
            [edge.E.counter.test]
            cols = ["f"]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Cannot drop column 'f'."

    def test_counters(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [edge.E]
            src = "X"
            tgt = "Y"
            cols = [
                ["f", "Boolean"],
            ]
            [edge.E.counter.test]
            cols = ["f"]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        e = graph.edges["E"]

        assert e.to_sql_stmt_create_base()[1] == textwrap.dedent(
            """\
            CREATE TABLE graph.E_counter_test (
              "src" gid NOT NULL,
              "f" Boolean NOT NULL,
              count Integer,
              PRIMARY KEY (src, f),
              FOREIGN KEY (src) REFERENCES graph."X" (gid)
            );"""
        )
        assert e.to_sql_stmt_create_base()[2].startswith(
            "CREATE FUNCTION graph.E_counter_test_count()"
        )

        # Try non-existent col
        config = textwrap.dedent(
            """\
            [vertex.X]
            [vertex.Y]
            [edge.E]
            src = "X"
            tgt = "Y"
            cols = [
                ["f", "Boolean"],
            ]
            [edge.E.counter.test]
            cols = ["g"]
            """
        )
        with self.assertRaises(InvalidSpec) as ctx:
            grapdb.parser.graph_from_config_toml(config)
        assert ctx.exception.args[0] == "Invalid column: 'g'"

    def test_binary_type(self) -> None:
        config = textwrap.dedent(
            """\
            [vertex]

            [vertex.V]
            cols=[["col1", "Binary"]]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 1
        v = graph.vertices["V"]
        assert v.name == "V"
        assert v.extends is None
        assert v.cols[-1].name == "col1"
        assert v.cols[-1].data_type == "Binary"

        # Test SQL is generated with correct postgresql type
        alter_stmts = v.to_sql_stmt_create_alters()
        assert (
            alter_stmts[0] == 'ALTER TABLE graph."V" ADD COLUMN "col1" bytea NOT NULL;'
        )

    def test_custom_schema(self) -> None:
        # Test vertex
        config = textwrap.dedent(
            """\
            schema = "multiverse"

            [vertex]

            [vertex.V]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 1
        v = graph.vertices["V"]

        create_base_stmts = v.to_sql_stmt_create_base()
        assert create_base_stmts[0] == textwrap.dedent(
            """\
            CREATE TABLE multiverse."V" (
              "gid" gid NOT NULL,
              "data" JSONB NOT NULL DEFAULT '{}',
              PRIMARY KEY (gid),
              CHECK ((gid).id IS NOT NULL AND (gid).vshard IS NOT NULL)
            );"""
        )
        assert (
            create_base_stmts[1]
            == "CREATE SEQUENCE multiverse.V_gid_id_seq OWNED BY multiverse.V.gid;"
        )
        assert create_base_stmts[2] == textwrap.dedent(
            """\
             CREATE TRIGGER V_insert_trigger
               BEFORE INSERT ON multiverse."V"
               FOR EACH ROW
               EXECUTE PROCEDURE
                 gid_pk_insert_trig("multiverse.V_gid_id_seq");"""
        )
        assert len(create_base_stmts) == 3

        assert v.to_sql_stmt_drop() == 'DROP TABLE multiverse."V";'
        assert len(v.to_sql_stmt_create_index()) == 0

        # Test edge
        config = textwrap.dedent(
            """\
            schema = "multiverse"

            [vertex]

            [vertex.X]
            [vertex.Y]

            [edge]

            [edge.A]
            src = "X"
            tgt = "Y"
            cols = [["col1", "Text"]]
            data_keys = ["key1", "key2"]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.vertices) == 2
        e = graph.edges["A"]
        self.assertEqual(
            e.to_sql_stmt_create_base()[0],
            textwrap.dedent(
                """\
                CREATE TABLE multiverse."A" (
                  "src" gid NOT NULL,
                  "tgt" gid NOT NULL,
                  "data" JSONB NOT NULL DEFAULT '{}',
                  PRIMARY KEY (src, tgt),
                  FOREIGN KEY (src) REFERENCES multiverse."X" (gid),
                  CHECK ((src).id IS NOT NULL AND (src).vshard IS NOT NULL),
                  CHECK ((tgt).id IS NOT NULL AND (tgt).vshard IS NOT NULL)
                );"""
            ),
        )
        self.assertEqual(
            e.to_sql_stmt_create_alters()[0],
            'ALTER TABLE multiverse."A" ADD COLUMN "col1" Text NOT NULL;',
        )

        # Test ctype
        config = textwrap.dedent(
            """\
            schema = "multiverse"

            [ctype.test]
            fields = [
                ["y", "Integer"],
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.ctypes) == 1
        test_ctype = graph.ctypes["test"]
        assert len(test_ctype.to_sql_decl()) == 1
        self.assertEqual(
            test_ctype.to_sql_decl()[0],
            "CREATE TYPE multiverse.test AS (y Integer);",
        )
        self.assertEqual(
            test_ctype.to_sql_drop(),
            "DROP TYPE multiverse.test;",
        )

        # Test enum
        config = textwrap.dedent(
            """\
            schema = "multiverse"

            [enum.wave]
            values = [
                "alpha",
                "beta",
            ]
            """
        )
        graph = grapdb.parser.graph_from_config_toml(config)
        assert len(graph.enums) == 1
        wave_enum = graph.enums["wave"]
        assert len(wave_enum.to_sql_decl()) == 1
        self.assertEqual(
            wave_enum.to_sql_decl()[0],
            "CREATE TYPE multiverse.wave AS ENUM ('alpha', 'beta');",
        )
        self.assertEqual(
            wave_enum.to_sql_drop(),
            "DROP TYPE multiverse.wave;",
        )


if __name__ == "__main__":
    unittest.main()
