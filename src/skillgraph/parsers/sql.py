from __future__ import annotations

import re

from ..model import Node, sha256_text

CREATE_TABLE = re.compile(
    r"CREATE\s+(?:UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.\"]+)",
    re.IGNORECASE,
)
STATEMENT_SPLIT = re.compile(r";\s*(?:\n|$)")


def _clean(name: str) -> str:
    return name.strip('"').split(".")[-1]


def parse_sql(rel: str, text: str, skill_id: str) -> tuple[list[Node], list[tuple[str, str, str]]]:
    nodes: list[Node] = []
    edges: list[tuple[str, str, str]] = []
    file_id = f"file.{rel}"
    edges.append((file_id, "part_of", skill_id))

    for m in CREATE_TABLE.finditer(text):
        name = _clean(m.group(1))
        start = text[: m.start()].count("\n") + 1
        nodes.append(
            Node(
                id=f"sql_table.{name}",
                type="sql_table",
                title=name,
                file=rel,
                span=[start, start],
                hash=sha256_text(name),
                meta={"kind": "table"},
            )
        )

    for m in re.finditer(r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|FROM|JOIN)\s+([\w.\"]+)", text, re.IGNORECASE):
        target = _clean(m.group(1))
        if target.upper() in {"SELECT", "VALUES", "SET", "WHERE"}:
            continue
        edges.append((file_id, "references", f"sql_table.{target}"))

    offset = 0
    idx = 0
    for chunk in text.split(";"):
        stmt = chunk.strip()
        if stmt:
            start_line = text[:offset].count("\n") + 1
            kind = stmt.split(None, 1)[0].upper()
            if kind in {"SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE", "ALTER", "DROP"}:
                qid = f"sql_query.{rel.replace('/', '.')}.{idx}"
                nodes.append(
                    Node(
                        id=qid,
                        type="sql_query",
                        title=f"{kind} #{idx}",
                        file=rel,
                        span=[start_line, start_line + stmt.count("\n")],
                        hash=sha256_text(stmt),
                        meta={"kind": kind},
                    )
                )
            idx += 1
        offset += len(chunk) + 1

    return nodes, edges
