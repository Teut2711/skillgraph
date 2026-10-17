from __future__ import annotations

import fnmatch
from pathlib import Path, PurePosixPath

from . import parsers
from .dedup import dedup
from .model import Graph, Node, sha256_text
from .scanner import iter_files, relative
from .spec import Spec, load_spec


def matches(rel: str, glob: str) -> bool:
    if PurePosixPath(rel).match(glob):
        return True
    if fnmatch.fnmatch(rel, glob):
        return True
    name = rel.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(name, glob.split("/")[-1])


def parser_for(rel: str, spec: Spec) -> str | None:
    for source in spec.sources:
        if matches(rel, source.glob):
            return source.parser
    return parsers.EXT_PARSER.get(PurePosixPath(rel).suffix.lower())


def _name_index(graph: Graph) -> dict[str, str]:
    index: dict[str, str] = {}
    for node in graph.nodes.values():
        candidates = {node.id, node.id.split(".")[-1], node.title}
        if node.file:
            candidates.add(node.file)
            candidates.add(node.file.rsplit("/", 1)[-1])
            candidates.add(PurePosixPath(node.file).stem)
        for c in candidates:
            if c:
                index.setdefault(c.lower(), node.id)
    return index


def _resolve(token: str, graph: Graph, names: dict[str, str]) -> str:
    if token in graph.nodes:
        return token
    if f"file.{token}" in graph.nodes:
        return f"file.{token}"
    key = token.lower()
    for prefix in ("symbol.", "section.", "sql_table.", "concept.", "file."):
        if f"{prefix}{token}" in graph.nodes:
            return f"{prefix}{token}"
    if key in names:
        return names[key]
    return token


def build_graph(root: Path, spec: Spec | None = None) -> Graph:
    root = Path(root)
    spec = spec or load_spec(root)
    graph = Graph()

    graph.add_node(
        Node(id=spec.id, type="skill", title=spec.skill, file="skill.yaml",
             summary=f"Skill: {spec.skill}", meta={"version": spec.version})
    )

    text_by_rel: dict[str, str] = {}
    for path in iter_files(root):
        rel = relative(root, path)
        parser = parser_for(rel, spec)
        if parser is None:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        text_by_rel[rel] = text
        if rel.endswith(".md"):
            continue
        graph.add_node(
            Node(id=f"file.{rel}", type="file", title=path.name, file=rel,
                 hash=sha256_text(text), meta={"parser": parser})
        )

    raw_edges: list[tuple[str, str, str]] = []
    for rel, text in text_by_rel.items():
        parser = parser_for(rel, spec)
        if parser is None:
            continue
        nodes, edges = parsers.parse_file(rel, text, parser, spec.id)
        for node in nodes:
            if node.id in graph.nodes and graph.nodes[node.id].file != node.file:
                node.id = f"{node.id}.{relative(root, Path(node.file)).replace('/', '.')}"
            graph.add_node(node)
        raw_edges.extend(edges)

    names = _name_index(graph)
    for src, rel, dst in raw_edges:
        src_id = src if src in graph.nodes else _resolve(src, graph, names)
        if dst.startswith("?"):
            token = dst[1:]
            dst_id = _resolve(token, graph, names)
            if dst_id == token and rel == "requires":
                dst_id = f"ext:{token}"
        else:
            dst_id = dst
        graph.add_edge(src_id, rel, dst_id)

    dedup(graph)
    return graph
