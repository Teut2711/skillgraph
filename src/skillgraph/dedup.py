from __future__ import annotations

from collections import defaultdict

from .model import Graph

DEDUP_TYPES = {"symbol", "section", "sql_table", "concept"}


def dedup(graph: Graph) -> None:
    _dedup_by_hash(graph)
    _dedup_by_title(graph)


def _dedup_by_hash(graph: Graph) -> None:
    buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
    for node in graph.nodes.values():
        if node.type in DEDUP_TYPES and node.hash:
            buckets[(node.type, node.hash)].append(node.id)
    for ids in buckets.values():
        if len(ids) > 1:
            canonical = sorted(ids)[0]
            for other in sorted(ids)[1:]:
                graph.add_edge(other, "same_as", canonical)
                graph.nodes[other].meta["canonical"] = canonical


def _dedup_by_title(graph: Graph) -> None:
    buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
    for node in graph.nodes.values():
        if node.type in DEDUP_TYPES and node.title:
            buckets[(node.type, node.title.lower().strip())].append(node.id)
    for ids in buckets.values():
        if len(ids) > 1:
            canonical = sorted(ids)[0]
            for other in sorted(ids)[1:]:
                if graph.nodes[other].meta.get("canonical"):
                    continue
                graph.add_edge(other, "same_as", canonical)
                graph.nodes[other].meta["canonical"] = canonical
