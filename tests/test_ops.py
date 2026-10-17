from pathlib import Path

from skillgraph import store
from skillgraph.ops import check, context_blocks, load_graph, read_span

ROOT = Path(__file__).resolve().parents[1] / "examples" / "demo.skill"


def test_load_graph_and_search():
    graph = load_graph(ROOT)
    hits = store.search(graph, "rollback migration")
    assert hits
    assert hits[0][0].id == "symbol.rollback_migration"


def test_read_span_returns_source():
    graph = load_graph(ROOT)
    body = read_span(ROOT, graph.nodes["symbol.rollback_migration"])
    assert "def rollback_migration" in body


def test_check_returns_issues():
    graph, issues = check(ROOT)
    assert any(i.code == "E001" for i in issues)


def test_context_blocks_bounded_by_budget():
    graph = load_graph(ROOT)
    body, included = context_blocks(ROOT, graph, "rollback failed migration", budget=500)
    assert included
    assert len(body) <= 700


def test_jsonl_roundtrip_and_sqlite(tmp_path: Path):
    graph = load_graph(ROOT)
    store.write_jsonl(graph, tmp_path)
    reloaded = store.read_jsonl(tmp_path)
    assert set(reloaded.nodes) == set(graph.nodes)
    db = store.write_sqlite(graph, tmp_path)
    assert db.exists()
