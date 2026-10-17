from pathlib import Path

from skillgraph.graph_builder import build_graph
from skillgraph.validate import validate

ROOT = Path(__file__).resolve().parents[1] / "examples" / "demo.skill"


def test_build_creates_skill_and_sections():
    graph = build_graph(ROOT)
    assert "skill.migration" in graph.nodes
    assert any(n.type == "section" for n in graph.nodes.values())
    assert any(n.type == "symbol" for n in graph.nodes.values())
    assert any(n.type == "sql_table" for n in graph.nodes.values())


def test_sections_have_provenance():
    graph = build_graph(ROOT)
    for node in graph.nodes.values():
        if node.type == "section":
            assert node.file
            assert node.span
            assert node.hash.startswith("sha256:")


def test_broken_ref_detected():
    graph = build_graph(ROOT)
    issues = validate(graph, ROOT)
    codes = {i.code for i in issues}
    assert "E001" in codes


def test_import_resolves_to_symbol_or_module():
    graph = build_graph(ROOT)
    requires = [e for e in graph.edges if e.rel == "requires"]
    assert requires


def test_context_is_bounded():
    pass
