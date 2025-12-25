#!/usr/bin/env python

import argparse
import json
from pathlib import Path
import sys

from . import parser, planner
from .graph import Graph
from .target import diesel_orm, sa_orm

description = """\
Parse GrapDB config files.
"""

_cmdline_parser = argparse.ArgumentParser(description=description)
_cmdline_parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Print debug messages",
)
_subparsers = _cmdline_parser.add_subparsers(title="subcommands", dest="subcommand")
_subparsers.required = True
_plan_parser = _subparsers.add_parser("plan", help="Output the migration plan in JSON.")
_plan_parser.add_argument(
    "config",
    action="store",
    help="Path to config file in TOML format.",
)
_sqlalchemy_orm_parser = _subparsers.add_parser(
    "sqlalchemy-orm",
    help="Create a Python module that can be used to interface with the DB.",
)
_sqlalchemy_orm_parser.add_argument(
    "config",
    action="store",
    help="Path to config file in TOML format.",
)
_sqlalchemy_orm_parser.add_argument(
    "path",
    action="store",
    help="Path to write Python modules (graph_orm_base.py, graph_orm.py).",
)
_sqlalchemy_orm_parser.add_argument(
    "--sa-version",
    action="store",
    type=int,
    choices=[13, 14, 20],
    default=13,
    help="Generate for SqlAlchemy v1.4",
)
_diesel_orm_parser = _subparsers.add_parser(
    "diesel-orm",
    help="Create Rust modules to interface with the DB.",
)
_diesel_orm_parser.add_argument(
    "config",
    action="store",
    help="Path to config file in TOML format.",
)
_diesel_orm_parser.add_argument(
    "path",
    action="store",
    help="Path to write Rust modules (schema.rs, model.rs).",
)


def subcommand_plan(graph: Graph) -> None:
    output = planner.generate(graph)
    print(json.dumps(output, indent=2))


def subcommand_sqlalchemy_orm(graph: Graph, path: Path, sa_version: int) -> None:
    sa_orm.generate(graph, path, sa_version)


def subcommand_diesel_orm(graph: Graph, path: Path) -> None:
    diesel_orm.generate(graph, path)


def main() -> None:
    args = _cmdline_parser.parse_args()
    try:
        graph = parser.graph_from_config_file(args.config)
    except parser.InvalidSpec as e:
        print("error: {}".format(e.args[0]), file=sys.stderr)
        sys.exit(1)

    if args.subcommand == "plan":
        subcommand_plan(graph)
    elif args.subcommand in {"sqlalchemy-orm", "diesel-orm"}:
        path = Path(args.path)
        if not path.exists():
            print("Path does not exist: %r" % path, file=sys.stderr)
            sys.exit(1)
        if not path.is_dir():
            print("Path is not a folder: %r" % path, file=sys.stderr)
            sys.exit(1)
        if args.subcommand == "sqlalchemy-orm":
            subcommand_sqlalchemy_orm(graph, path, args.sa_version)
        else:
            assert args.subcommand == "diesel-orm"
            subcommand_diesel_orm(graph, path)
    else:
        assert False


if __name__ == "__main__":
    main()
