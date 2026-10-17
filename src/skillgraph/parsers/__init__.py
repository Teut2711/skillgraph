from __future__ import annotations

from ..model import Node
from . import markdown, python_ast, sql

PARSERS = {
    "markdown": markdown,
    "python": python_ast,
    "python_ast": python_ast,
    "sql": sql,
}

EXT_PARSER = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".py": "python",
    ".sql": "sql",
}


def node_id_for_file(rel: str) -> str:
    return f"file.{rel}"


def parse_file(rel: str, text: str, parser: str, skill_id: str) -> tuple[list[Node], list[tuple[str, str, str]]]:
    if parser == "markdown":
        nodes, edges = markdown.parse_sections(rel, text, skill_id)
        edges += markdown.parse_code_refs(rel, text, skill_id)
        return nodes, edges
    if parser in ("python", "python_ast"):
        return python_ast.parse_python(rel, text, skill_id)
    if parser == "sql":
        return sql.parse_sql(rel, text, skill_id)
    return [], []
