from pathlib import Path

from skillgraph.graph_builder import build_graph
from skillgraph.scaffold import init_skill


def test_init_creates_project(tmp_path: Path):
    target = tmp_path / "demo.skill"
    created = init_skill(target)
    names = {p.name for p in created}
    assert "skill.yaml" in names
    assert "SKILL.md" in names
    assert (target / "scripts").is_dir()
    assert (target / "sql").is_dir()


def test_init_names_skill_from_folder(tmp_path: Path):
    target = tmp_path / "migration.skill"
    init_skill(target)
    text = (target / "skill.yaml").read_text(encoding="utf-8")
    assert "skill: migration" in text


def test_init_explicit_name(tmp_path: Path):
    target = tmp_path / "anything"
    init_skill(target, name="custom")
    assert "skill: custom" in (target / "skill.yaml").read_text(encoding="utf-8")


def test_init_refuses_non_empty_without_force(tmp_path: Path):
    target = tmp_path / "busy.skill"
    target.mkdir()
    (target / "keep.txt").write_text("x", encoding="utf-8")
    try:
        init_skill(target)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected FileExistsError")


def test_init_then_build(tmp_path: Path):
    target = tmp_path / "scaffold.skill"
    init_skill(target)
    graph = build_graph(target)
    assert "skill.scaffold" in graph.nodes
    assert any(n.type == "section" for n in graph.nodes.values())
