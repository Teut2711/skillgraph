from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import store
from .graph_builder import build_graph
from .model import Graph
from .ops import context_blocks, graph_dir, load_graph
from .report import health, summarize
from .validate import validate


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    graph = build_graph(root)
    nodes_path, edges_path = store.write_jsonl(graph, graph_dir(root))
    msg = f"wrote {len(graph.nodes)} nodes -> {nodes_path}\n      {len(graph.edges)} edges -> {edges_path}"
    if args.sqlite:
        db = store.write_sqlite(graph, graph_dir(root))
        msg += f"\n      sqlite -> {db}"
    print(msg)
    return 0


def _load(root: Path) -> Graph:
    return load_graph(root)


def cmd_check(args: argparse.Namespace) -> int:
    root = Path(args.root)
    graph = _load(root)
    issues = validate(graph, root)
    if args.json:
        print(json.dumps([i.to_dict() for i in issues], indent=2))
    else:
        print(summarize(graph, issues))
        for i in issues:
            print(f"  [{i.code}] {i.node}: {i.message}")
    return 1 if any(i.severity == "error" for i in issues) else 0


def cmd_report(args: argparse.Namespace) -> int:
    root = Path(args.root)
    graph = _load(root)
    issues = validate(graph, root)
    print(summarize(graph, issues))
    print(json.dumps(health(issues, graph), indent=2))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    graph = _load(Path(args.root))
    for node, score in store.search(graph, args.query, args.limit):
        print(f"{score:4.1f}  {node.type:<10} {node.id:<40} {node.file}")
        if node.summary:
            print(f"        {node.summary}")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    graph = _load(Path(args.root))
    node = graph.nodes.get(args.node_id)
    if node is None:
        matches = [n for n in graph.nodes if args.node_id in n.id]
        if not matches:
            print(f"no node: {args.node_id}", file=sys.stderr)
            return 2
        node = graph.nodes[matches[0]]
    print(f"{node.id}  [{node.type}]")
    print(f"title: {node.title}")
    print(f"file:  {node.file} {node.span or ''}")
    if node.summary:
        print(f"summary: {node.summary}")
    if node.tags:
        print(f"tags: {', '.join(node.tags)}")
    print("out:")
    for e in graph.out_edges(node.id):
        print(f"  {e.rel} -> {e.dst}")
    print("in:")
    for e in graph.in_edges(node.id):
        print(f"  {e.src} {e.rel} ->")
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    root = Path(args.root)
    graph = _load(root)
    body, included = context_blocks(root, graph, args.query, args.budget, args.limit)
    print(f"# context for: {args.query}\n")
    print(body)
    print(f"<!-- {len(included)} blocks, budget {args.budget} -->")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    from .scaffold import init_skill

    try:
        created = init_skill(args.path, args.name, args.force)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"initialized skill at {Path(args.path).resolve()}")
    for path in created:
        print(f"  + {path.relative_to(Path(args.path))}")
    print("\nnext:")
    print(f"  skillgraph scan {args.path}")
    print(f"  skillgraph serve {args.path}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .web.app import serve

    if args.scan:
        graph = build_graph(Path(args.root))
        store.write_jsonl(graph, graph_dir(Path(args.root)))
    serve(args.root, args.host, args.port)
    return 0


def cmd_up(args: argparse.Namespace) -> int:
    root = Path(args.root)
    graph = build_graph(root)
    store.write_jsonl(graph, graph_dir(root))
    print(f"scanned {len(graph.nodes)} nodes; serving on {args.host}:{args.port}")
    from .web.app import serve

    serve(str(root), args.host, args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skillgraph", description="Knowledge compiler for skill repos")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="scaffold a new .skill project")
    p.add_argument("path", nargs="?", default=".", help="target directory")
    p.add_argument("--name", default=None, help="skill name (default: folder name)")
    p.add_argument("--force", action="store_true", help="overwrite existing files")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("scan", help="build the graph")
    p.add_argument("root")
    p.add_argument("--sqlite", action="store_true", help="also write skillgraph.db")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("check", help="run lint rules")
    p.add_argument("root")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("report", help="health summary")
    p.add_argument("root")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("query", help="search nodes")
    p.add_argument("root")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("explain", help="show a node and its edges")
    p.add_argument("root")
    p.add_argument("node_id")
    p.set_defaults(func=cmd_explain)

    p = sub.add_parser("context", help="assemble grounded context for a query")
    p.add_argument("root")
    p.add_argument("query")
    p.add_argument("--budget", type=int, default=4000, help="char budget")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=cmd_context)

    p = sub.add_parser("serve", help="launch the FastAPI + ReactPy UI")
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--scan", action="store_true", help="rebuild the graph before serving")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("up", help="scan then serve (one-shot)")
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_up)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
