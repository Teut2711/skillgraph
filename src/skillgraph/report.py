from __future__ import annotations

from collections import Counter

from .model import Graph
from .validate import Issue


def health(issues: list[Issue], graph: Graph) -> dict:
    counts = Counter(i.code for i in issues)
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    score = max(0, 100 - errors * 10 - warnings * 2)
    return {
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "errors": errors,
        "warnings": warnings,
        "score": score,
        "by_code": dict(counts),
    }


def summarize(graph: Graph, issues: list[Issue]) -> str:
    h = health(issues, graph)
    lines = [
        f"nodes={h['nodes']} edges={h['edges']} score={h['score']} "
        f"errors={h['errors']} warnings={h['warnings']}"
    ]
    for code, count in sorted(h["by_code"].items()):
        lines.append(f"  {code}: {count}")
    return "\n".join(lines)
