from pathlib import Path

from skillgraph.ops import load_graph
from skillgraph.validate import validate
from skillgraph.web.app import _cols, create_app

ROOT = Path(__file__).resolve().parents[1] / "examples" / "demo.skill"


def test_cols_renders_detail_and_edges():
    graph = load_graph(ROOT)
    issues = validate(graph, ROOT)
    detail = graph.nodes["symbol.rollback_migration"]
    vdom = repr(_cols(str(ROOT), graph, issues, [], detail, "", lambda nid: (lambda e=None: None)))
    assert "rollback_migration" in vdom
    assert "scripts/rollback.py" in vdom


def test_create_app_mounts_api_and_ui():
    app = create_app(str(ROOT))
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/health" in paths
    assert "/api/node/{node_id:path}" in paths
    assert any(p and p.startswith("/_reactpy") for p in paths)
