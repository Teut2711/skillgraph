from __future__ import annotations

import re
from pathlib import Path

from .paths import skill_yaml_template

GITKEEP = ""


def _skill_name(root: Path, name: str | None) -> str:
    if name:
        return name
    return root.name[:-6] if root.name.endswith(".skill") else root.name


def _spec_text(name: str) -> str:
    text = skill_yaml_template().read_text(encoding="utf-8")
    return re.sub(r"^skill:\s*.*$", f"skill: {name}", text, count=1, flags=re.MULTILINE)


def _skill_md_text(name: str) -> str:
    from .paths import skill_dir

    template = skill_dir() / "templates" / "SKILL.template.md"
    text = template.read_text(encoding="utf-8")
    return text.replace("# <Skill name>", f"# {name}")


def init_skill(path: str | Path, name: str | None = None, force: bool = False) -> list[Path]:
    root = Path(path)
    if root.exists() and any(root.iterdir()) and not force:
        raise FileExistsError(f"directory not empty: {root} (use --force)")
    root.mkdir(parents=True, exist_ok=True)
    skill_name = _skill_name(root, name)

    created: list[Path] = []
    spec = root / "skill.yaml"
    if force or not spec.exists():
        spec.write_text(_spec_text(skill_name), encoding="utf-8")
        created.append(spec)
    doc = root / "SKILL.md"
    if force or not doc.exists():
        doc.write_text(_skill_md_text(skill_name), encoding="utf-8")
        created.append(doc)
    for sub in ("scripts", "sql"):
        d = root / sub
        d.mkdir(exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text(GITKEEP, encoding="utf-8")
            created.append(keep)
    return created
