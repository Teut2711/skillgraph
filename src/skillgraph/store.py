from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .model import Edge, Graph, Node

NODES_FILE = "graph.nodes.jsonl"
EDGES_FILE = "graph.edges.jsonl"
DB_FILE = "skillgraph.db"


def write_jsonl(graph: Graph, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes_path = out_dir / NODES_FILE
    edges_path = out_dir / EDGES_FILE
    with nodes_path.open("w", encoding="utf-8") as fh:
        for node in sorted(graph.nodes.values(), key=lambda n: n.id):
            fh.write(json.dumps(node.to_dict(), ensure_ascii=False) + "\n")
    with edges_path.open("w", encoding="utf-8") as fh:
        seen: set[tuple[str, str, str]] = set()
        for edge in graph.edges:
            key = (edge.src, edge.rel, edge.dst)
            if key in seen:
                continue
            seen.add(key)
            fh.write(json.dumps(edge.to_dict(), ensure_ascii=False) + "\n")
    return nodes_path, edges_path


def read_jsonl(out_dir: Path) -> Graph:
    out_dir = Path(out_dir)
    graph = Graph()
    nodes_path = out_dir / NODES_FILE
    edges_path = out_dir / EDGES_FILE
    if nodes_path.exists():
        for line in nodes_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                graph.add_node(Node.from_dict(json.loads(line)))
    if edges_path.exists():
        for line in edges_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                graph.edges.append(Edge.from_dict(json.loads(line)))
    return graph


def write_sqlite(graph: Graph, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / DB_FILE
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            DROP TABLE IF EXISTS nodes;
            DROP TABLE IF EXISTS edges;
            DROP TABLE IF EXISTS nodes_fts;
            CREATE TABLE nodes (
                id TEXT PRIMARY KEY, type TEXT, title TEXT, file TEXT,
                span TEXT, hash TEXT, summary TEXT, tags TEXT, aliases TEXT, meta TEXT
            );
            CREATE TABLE edges (src TEXT, rel TEXT, dst TEXT);
            CREATE VIRTUAL TABLE nodes_fts USING fts5(
                id, title, summary, tags, aliases, content=''
            );
            """
        )
        for node in graph.nodes.values():
            conn.execute(
                "INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    node.id, node.type, node.title, node.file,
                    json.dumps(node.span), node.hash, node.summary,
                    json.dumps(node.tags), json.dumps(node.aliases),
                    json.dumps(node.meta),
                ),
            )
            conn.execute(
                "INSERT INTO nodes_fts (id, title, summary, tags, aliases) VALUES (?,?,?,?,?)",
                (node.id, node.title, node.summary, " ".join(node.tags), " ".join(node.aliases)),
            )
        for edge in graph.edges:
            conn.execute("INSERT INTO edges VALUES (?,?,?)", (edge.src, edge.rel, edge.dst))
        conn.commit()
    finally:
        conn.close()
    return db_path


def search(graph: Graph, query: str, limit: int = 20) -> list[tuple[Node, float]]:
    terms = [t.lower() for t in query.split() if t.strip()]
    scored: list[tuple[Node, float]] = []
    for node in graph.nodes.values():
        haystack = " ".join(
            [node.id, node.title, node.summary, " ".join(node.tags), " ".join(node.aliases)]
        ).lower()
        score = 0.0
        for term in terms:
            if term in haystack:
                score += 1.0
            if term in node.title.lower():
                score += 1.5
        if score > 0:
            scored.append((node, score))
    scored.sort(key=lambda x: (-x[1], x[0].id))
    return scored[:limit]
