from typing import Dict, List
from .graph import Graph


def generate(graph: Graph) -> Dict[str, List[str]]:
    migration_plan = graph.to_sql_stmt_create_prereqs()

    for enum in graph.enums.values():
        migration_plan.extend(enum.to_sql_decl())

    for ctype in graph.ctypes.values():
        migration_plan.extend(ctype.to_sql_decl())

    for vertex in graph.vertices.values():
        migration_plan.extend(vertex.to_sql_stmt_create_base())

    for vertex in graph.vertices.values():
        migration_plan.extend(vertex.to_sql_stmt_create_alters())

    for vertex in graph.vertices.values():
        migration_plan.extend(vertex.to_sql_stmt_create_index())

    for edge in graph.edges.values():
        migration_plan.extend(edge.to_sql_stmt_create_base())

    for edge in graph.edges.values():
        migration_plan.extend(edge.to_sql_stmt_create_alters())

    for edge in graph.edges.values():
        migration_plan.extend(edge.to_sql_stmt_create_index())

    drop_plan = []
    for edge in reversed(list(graph.edges.values())):
        drop_plan.append(edge.to_sql_stmt_drop())
    for vertex in reversed(list(graph.vertices.values())):
        drop_plan.append(vertex.to_sql_stmt_drop())
    for ctype in reversed(list(graph.ctypes.values())):
        drop_plan.append(ctype.to_sql_drop())
    for enum in reversed(list(graph.enums.values())):
        drop_plan.append(enum.to_sql_drop())
    drop_plan.extend(graph.to_sql_stmt_drop_prereqs())

    return dict(
        migration_plan=migration_plan,
        drop_plan=drop_plan,
    )
