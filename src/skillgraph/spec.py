from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_SOURCES = [
    {"glob": "**/*.md", "parser": "markdown", "nodes": ["skill", "section"]},
    {"glob": "**/*.py", "parser": "python", "nodes": ["file", "symbol"]},
    {"glob": "**/*.sql", "parser": "sql", "nodes": ["sql_table", "sql_query"]},
]

DEFAULT_RULES = [
    {"edge": "contains", "from": "skill", "to": "section"},
    {"edge": "contains", "from": "skill", "to": "sql_table"},
    {"edge": "references", "from": "section", "match": "backtick.code_ref"},
    {"edge": "requires", "from": "symbol", "match": "python.import"},
]


@dataclass
class Source:
    glob: str
    parser: str
    nodes: list[str] = field(default_factory=list)


@dataclass
class Spec:
    skill: str
    version: int = 1
    sources: list[Source] = field(default_factory=list)
    rules: list[dict[str, Any]] = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"skill.{self.skill}"


def default_spec(skill_name: str) -> Spec:
    return Spec(
        skill=skill_name,
        version=1,
        sources=[Source(**s) for s in DEFAULT_SOURCES],
        rules=list(DEFAULT_RULES),
    )


def load_spec(root: Path) -> Spec:
    path = root / "skill.yaml"
    if not path.exists():
        return default_spec(root.name.replace(".skill", ""))
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources = [Source(**s) for s in raw.get("sources", DEFAULT_SOURCES)]
    return Spec(
        skill=raw.get("skill", root.name.replace(".skill", "")),
        version=int(raw.get("version", 1)),
        sources=sources,
        rules=raw.get("rules", list(DEFAULT_RULES)),
    )
