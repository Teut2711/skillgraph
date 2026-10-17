from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .model import Graph, sha256_text


@dataclass
class Issue:
    code: str
    severity: str
    node: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "severity": self.severity, "node": self.node, "message": self.message}


def validate(graph: Graph, root: Path | str | None = None) -> list[Issue]:
    issues: list[Issue] = []
    issues += _broken_refs(graph)
    issues += _cycles(graph)
    issues += _orphans(graph)
    issues += _oversized(graph)
    if root is not None:
        root = Path(root)
        issues += _frontmatter(root)
        issues += _stale(graph, root)
    return issues


def _broken_refs(graph: Graph) -> list[Issue]:
    out: list[Issue] = []
    for edge in graph.edges:
        if edge.dst.startswith("ext:"):
            continue
        if edge.dst not in graph.nodes:
            out.append(Issue("E001", "error", edge.src, f"{edge.rel} -> missing '{edge.dst}'"))
        if edge.src not in graph.nodes:
            out.append(Issue("E001", "error", edge.src, f"unknown source for {edge.rel} -> {edge.dst}"))
    return out


def _cycles(graph: Graph) -> list[Issue]:
    rels = {"requires", "contains", "depends_on"}
    adj: dict[str, list[str]] = {}
    for edge in graph.edges:
        if edge.rel in rels:
            adj.setdefault(edge.src, []).append(edge.dst)
    color: dict[str, int] = {}
    out: list[Issue] = []

    def dfs(u: str, path: list[str]) -> None:
        color[u] = 1
        path.append(u)
        for v in adj.get(u, []):
            if color.get(v) == 1:
                cyc = path[path.index(v):] + [v]
                out.append(Issue("E002", "error", v, "cycle: " + " -> ".join(cyc)))
            elif color.get(v, 0) == 0:
                dfs(v, path)
        path.pop()
        color[u] = 2

    for node in list(adj):
        if color.get(node, 0) == 0:
            dfs(node, [])
    return out


def _orphans(graph: Graph) -> list[Issue]:
    roots = {"skill", "file"}
    has_in = {e.dst for e in graph.edges}
    out: list[Issue] = []
    for node in graph.nodes.values():
        if node.type in roots or node.type == "sql_query":
            continue
        if node.id not in has_in:
            out.append(Issue("W001", "warning", node.id, f"orphan {node.type} (no incoming edges)"))
    return out


def _oversized(graph: Graph, limit_chars: int = 6000) -> list[Issue]:
    out: list[Issue] = []
    for node in graph.nodes.values():
        if node.type == "section" and node.span:
            size = (node.span[1] - node.span[0] + 1) * 60
            if size > limit_chars:
                out.append(Issue("W030", "warning", node.id,
                                 f"section ~{size} chars (> {limit_chars}); consider splitting"))
    return out


def _frontmatter(root: Path) -> list[Issue]:
    if not (root / "skill.yaml").exists():
        return [Issue("W003", "warning", "skill", "no skill.yaml; using default extraction spec")]
    return []


def _stale(graph: Graph, root: Path) -> list[Issue]:
    out: list[Issue] = []
    cache: dict[str, list[str]] = {}
    for node in graph.nodes.values():
        if node.type != "section" or not node.file or not node.span or not node.hash:
            continue
        path = root / node.file
        if not path.exists():
            out.append(Issue("W010", "warning", node.id, f"source file missing: {node.file}"))
            continue
        if node.file not in cache:
            cache[node.file] = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        lines = cache[node.file]
        start, end = node.span
        body = "\n".join(lines[start - 1 : end])
        if sha256_text(body) != node.hash:
            out.append(Issue("W010", "warning", node.id, "stale: source changed since index"))
    return out
