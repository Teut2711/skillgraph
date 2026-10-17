from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field, fields
from typing import Any


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Node:
    id: str
    type: str
    title: str = ""
    file: str = ""
    span: list[int] | None = None
    hash: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Node":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class Edge:
    src: str
    rel: str
    dst: str

    def to_dict(self) -> dict[str, str]:
        return {"from": self.src, "rel": self.rel, "to": self.dst}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Edge":
        return cls(src=d["from"], rel=d["rel"], dst=d["to"])


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, src: str, rel: str, dst: str) -> None:
        self.edges.append(Edge(src, rel, dst))

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    def out_edges(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.src == node_id]

    def in_edges(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.dst == node_id]

    def neighbors(self, node_id: str, rel: str | None = None) -> list[str]:
        out: list[str] = []
        for e in self.out_edges(node_id):
            if rel is None or e.rel == rel:
                out.append(e.dst)
        return out

    def merge(self, other: "Graph") -> None:
        for n in other.nodes.values():
            self.nodes[n.id] = n
        self.edges.extend(other.edges)
