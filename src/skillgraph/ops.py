from __future__ import annotations

from pathlib import Path

from . import store
from .graph_builder import build_graph
from .model import Graph, Node
from .validate import Issue, validate

GRAPH_DIR = ".graph"


def graph_dir(root: Path | str) -> Path:
    return Path(root) / GRAPH_DIR


def load_graph(root: Path | str, rebuild: bool = False) -> Graph:
    root = Path(root)
    nodes_path = graph_dir(root) / store.NODES_FILE
    if rebuild or not nodes_path.exists():
        graph = build_graph(root)
        store.write_jsonl(graph, graph_dir(root))
        return graph
    return store.read_jsonl(graph_dir(root))


def read_span(root: Path | str, node: Node) -> str:
    if not node.file or not node.span:
        return ""
    path = Path(root) / node.file
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    start, end = node.span
    return "\n".join(lines[start - 1 : end])


def check(root: Path | str, graph: Graph | None = None) -> tuple[Graph, list[Issue]]:
    root = Path(root)
    graph = graph or load_graph(root)
    return graph, validate(graph, root)


def context_blocks(root: Path | str, graph: Graph, query: str,
                   budget: int = 4000, limit: int = 5) -> tuple[str, list[str]]:
    root = Path(root)
    seeds = store.search(graph, query, limit)
    queue: list[str] = [node.id for node, _ in seeds]
    seen: set[str] = set(queue)
    for node, _ in seeds:
        for dst in graph.neighbors(node.id):
            if dst in graph.nodes and dst not in seen:
                seen.add(dst)
                queue.append(dst)
    used = 0
    parts: list[str] = []
    included: list[str] = []
    for nid in queue:
        node = graph.nodes.get(nid)
        if node is None:
            continue
        body = read_span(root, node) or node.summary
        if not body:
            continue
        block = f"## [{node.id}] {node.title}\n{body}\n"
        if used + len(block) > budget:
            break
        used += len(block)
        included.append(nid)
        parts.append(block)
    return "\n".join(parts), included
