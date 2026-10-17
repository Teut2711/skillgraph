from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from reactpy import component, hooks, html
from reactpy.backend.fastapi import configure

from .. import store
from ..ops import context_blocks, load_graph, read_span
from ..report import health
from ..validate import validate

CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin:0; background:#0e1116; color:#d7dee8;
       font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
.sg { max-width:1200px; margin:0 auto; padding:20px; }
h1 { font-size:18px; margin:0 0 4px; }
.sub { color:#7d8797; margin-bottom:16px; }
.row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:12px; }
input { background:#161b22; border:1px solid #2b3440; color:#d7dee8;
        padding:8px 10px; border-radius:6px; font:inherit; }
input.path { min-width:420px; flex:1; }
input.q { min-width:320px; flex:1; }
button { background:#1f6feb; border:0; color:#fff; padding:8px 14px;
         border-radius:6px; font:inherit; cursor:pointer; }
button.ghost { background:#21262d; border:1px solid #2b3440; }
button:hover { filter:brightness(1.1); }
.badges { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }
.badge { background:#161b22; border:1px solid #2b3440; padding:5px 10px;
         border-radius:6px; }
.badge b { color:#d7dee8; }
.badge .ok { color:#3fb950; }
.badge .err { color:#f85149; }
.badge .warn { color:#d29922; }
.status { color:#7d8797; margin-bottom:12px; }
.cols { display:grid; grid-template-columns:1fr 1.3fr; gap:16px; }
.card { background:#11161d; border:1px solid #2b3440; border-radius:8px;
        padding:12px; }
.card h2 { font-size:13px; text-transform:uppercase; letter-spacing:.06em;
           color:#7d8797; margin:0 0 10px; }
ul { list-style:none; margin:0; padding:0; }
li { padding:6px 8px; border-radius:6px; cursor:pointer; }
li:hover { background:#161b22; }
li.sel { background:#1f6feb22; outline:1px solid #1f6feb66; }
.nid { color:#79c0ff; }
.ntype { color:#7d8797; font-size:12px; }
.score { color:#3fb950; }
.meta { color:#7d8797; font-size:12px; margin-bottom:8px; }
pre { background:#0b0f14; border:1px solid #2b3440; border-radius:6px;
      padding:10px; overflow:auto; max-height:340px; margin:0 0 10px; }
.edge { color:#d7dee8; }
.edge .rel { color:#d29922; }
.edge .dst { color:#79c0ff; cursor:pointer; }
.empty { color:#7d8797; }
"""


def _load_state(root_str: str):
    root = Path(root_str)
    if not root.is_dir():
        raise FileNotFoundError(f"not a directory: {root}")
    graph = load_graph(root, rebuild=True)
    issues = validate(graph, root)
    return graph, issues


@component
def App(default_root: str):
    graph, set_graph = hooks.use_state(None)
    issues, set_issues = hooks.use_state([])
    root, set_root = hooks.use_state(default_root)
    query, set_query = hooks.use_state("")
    results, set_results = hooks.use_state([])
    selected, set_selected = hooks.use_state(None)
    ctx, set_ctx = hooks.use_state("")
    budget, set_budget = hooks.use_state(1500)
    status, set_status = hooks.use_state("enter a .skill folder, then Scan")

    def do_scan(_event=None):
        try:
            g, iss = _load_state(root)
            set_graph(g)
            set_issues(iss)
            set_selected(None)
            set_results([])
            set_ctx("")
            set_status(f"scanned {len(g.nodes)} nodes / {len(g.edges)} edges")
        except Exception as exc:  # noqa: BLE001
            set_graph(None)
            set_status(f"error: {exc}")

    def do_check(_event=None):
        if graph is None:
            set_status("scan first")
            return
        iss = validate(graph, Path(root))
        set_issues(iss)
        set_status(f"check: {sum(1 for i in iss if i.severity == 'error')} errors, "
                   f"{sum(1 for i in iss if i.severity == 'warning')} warnings")

    def do_search(_event=None):
        if graph is None:
            set_status("scan first")
            return
        hits = store.search(graph, query, 40)
        set_results([n.id for n, _ in hits])
        set_status(f"{len(hits)} matches for '{query}'")

    def do_context(_event=None):
        if graph is None:
            set_status("scan first")
            return
        body, included = context_blocks(root, graph, query, budget, 5)
        set_ctx(body)
        set_status(f"context: {len(included)} blocks, ~{len(body)} chars")

    def pick(node_id):
        def handler(_event=None):
            set_selected(node_id)
            set_ctx("")
        return handler

    h = health(issues, graph) if graph is not None else None
    detail = None
    if graph is not None and selected in graph.nodes:
        detail = graph.nodes[selected]

    def badge(label, value, cls=""):
        return html.span({"className": "badge"},
                         f"{label} ", html.b(html.span({"className": cls}, str(value))))

    children = [
        html.style(CSS),
        html.div(
            {"className": "sg"},
            html.h1("skillgraph"),
            html.div({"className": "sub"}, "source-authoritative graph index for skill repos"),
            html.div(
                {"className": "row"},
                html.input({"className": "path", "value": root,
                            "onChange": lambda e: set_root(e["target"]["value"]),
                            "placeholder": "path to .skill folder"}),
                html.button({"onClick": do_scan}, "Scan"),
                html.button({"className": "ghost", "onClick": do_check}, "Check"),
            ),
            html.div({"className": "status"}, status),
        ),
    ]

    if h is not None:
        children.append(
            html.div(
                {"className": "sg"},
                html.div(
                    {"className": "badges"},
                    badge("nodes", h["nodes"]),
                    badge("edges", h["edges"]),
                    badge("score", h["score"], "ok" if h["errors"] == 0 else "warn"),
                    badge("errors", h["errors"], "err" if h["errors"] else "ok"),
                    badge("warnings", h["warnings"], "warn" if h["warnings"] else "ok"),
                ),
                html.div(
                    {"className": "row"},
                    html.input({"className": "q", "value": query,
                                "onChange": lambda e: set_query(e["target"]["value"]),
                                "placeholder": "search nodes (e.g. rollback migration)"}),
                    html.button({"onClick": do_search}, "Search"),
                    html.button({"className": "ghost", "onClick": do_context}, "Context"),
                    html.input({"type": "number", "value": str(budget),
                                "onChange": lambda e: set_budget(int(e["target"]["value"] or 0)),
                                "style": {"width": "90px"}}),
                ),
                _cols(root, graph, issues, results, detail, ctx, pick),
            )
        )
    return html.div(*children)


def _cols(root, graph, issues, results, detail, ctx, pick):
    left = html.div(
        {"className": "card"},
        html.h2("Nodes / results"),
        html.ul(
            *[
                html.li(
                    {"key": nid, "onClick": pick(nid)},
                    html.span({"className": "nid"}, nid),
                    html.div({"className": "ntype"}, graph.nodes[nid].type),
                )
                for nid in (results or sorted(graph.nodes)[:60])
            ]
        )
        if (results or graph.nodes)
        else html.div({"className": "empty"}, "no nodes"),
    )

    right_children = [html.h2("Detail")]
    if detail is not None:
        right_children += [
            html.div(html.span({"className": "nid"}, detail.id),
                     " ", html.span({"className": "ntype"}, f"[{detail.type}]")),
            html.div({"className": "meta"},
                     f"{detail.file} {detail.span or ''}  {detail.hash[:16]}"),
            html.pre(read_span(root, detail) or detail.summary or "(empty)"),
        ]
        outs = [e for e in graph.edges if e.src == detail.id]
        ins = [e for e in graph.edges if e.dst == detail.id]
        if outs:
            right_children.append(html.div({"className": "meta"}, "out"))
            right_children.append(
                html.ul(*[html.li({"key": f"o{i}", "onClick": pick(e.dst)},
                                  html.span({"className": "edge"},
                                            html.span({"className": "rel"}, f"{e.rel} -> "),
                                            html.span({"className": "dst"}, e.dst)))
                          for i, e in enumerate(outs)]))
        if ins:
            right_children.append(html.div({"className": "meta"}, "in"))
            right_children.append(
                html.ul(*[html.li({"key": f"i{i}", "onClick": pick(e.src)},
                                  html.span({"className": "edge"},
                                            html.span({"className": "dst"}, e.src),
                                            html.span({"className": "rel"}, f" -> {e.rel}")))
                          for i, e in enumerate(ins)]))
    else:
        right_children.append(html.div({"className": "empty"}, "select a node"))

    if issues:
        right_children.append(html.h2({"style": {"marginTop": "14px"}}, "Issues"))
        right_children.append(
            html.ul(*[html.li({"key": f"x{i}", "onClick": pick(i.node)},
                              f"[{i.code}] {i.node}")
                      for i, i in enumerate(issues[:40])]))

    if ctx:
        right_children.append(html.h2({"style": {"marginTop": "14px"}}, "Context"))
        right_children.append(html.pre(ctx))

    right = html.div({"className": "card"}, *right_children)
    return html.div({"className": "cols"}, left, right)


def create_app(default_root: str = "examples/demo.skill") -> FastAPI:
    app = FastAPI(title="skillgraph")

    @app.get("/api/node/{node_id:path}")
    def api_node(node_id: str, root: str = default_root):
        graph = load_graph(root)
        if node_id not in graph.nodes:
            return {"error": "not found"}
        node = graph.nodes[node_id]
        return {
            "node": node.to_dict(),
            "body": read_span(root, node),
            "out": [e.to_dict() for e in graph.out_edges(node_id)],
            "in": [e.to_dict() for e in graph.in_edges(node_id)],
        }

    @app.get("/api/health")
    def api_health(root: str = default_root):
        graph = load_graph(root)
        issues = validate(graph, Path(root))
        return health(issues, graph)

    @component
    def Root():
        return App(default_root)

    configure(app, Root)
    return app


def serve(root: str = "examples/demo.skill", host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(create_app(root), host=host, port=port)
