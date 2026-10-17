from __future__ import annotations

import ast

from ..model import Node, sha256_text


def _span(node: ast.AST) -> list[int]:
    return [getattr(node, "lineno", 1), getattr(node, "end_lineno", getattr(node, "lineno", 1))]


def parse_python(rel: str, text: str, skill_id: str) -> tuple[list[Node], list[tuple[str, str, str]]]:
    nodes: list[Node] = []
    edges: list[tuple[str, str, str]] = []
    file_id = f"file.{rel}"
    tree = ast.parse(text)
    edges.append((file_id, "part_of", skill_id))

    def visit(body: list[ast.stmt], parent_id: str) -> None:
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym_id = f"symbol.{stmt.name}"
                doc = ast.get_docstring(stmt) or ""
                nodes.append(
                    Node(
                        id=sym_id,
                        type="symbol",
                        title=stmt.name,
                        file=rel,
                        span=_span(stmt),
                        hash=sha256_text(ast.get_source_segment(text, stmt) or stmt.name),
                        summary=doc.splitlines()[0] if doc else "",
                        meta={"kind": "function", "parent": parent_id},
                    )
                )
                for dec in stmt.decorator_list:
                    edges.append((sym_id, "annotated_by", f"?{ast.unparse(dec)}"))
                visit(stmt.body, sym_id)
            elif isinstance(stmt, ast.ClassDef):
                sym_id = f"symbol.{stmt.name}"
                doc = ast.get_docstring(stmt) or ""
                nodes.append(
                    Node(
                        id=sym_id,
                        type="symbol",
                        title=stmt.name,
                        file=rel,
                        span=_span(stmt),
                        hash=sha256_text(ast.get_source_segment(text, stmt) or stmt.name),
                        summary=doc.splitlines()[0] if doc else "",
                        meta={"kind": "class", "parent": parent_id},
                    )
                )
                visit(stmt.body, sym_id)

    visit(tree.body, file_id)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append((file_id, "requires", f"?{alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                edges.append((file_id, "requires", f"?{node.module}"))

    return nodes, edges
