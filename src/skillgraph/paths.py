from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _data_root() -> Path:
    try:
        from importlib.resources import files

        return Path(str(files("skillgraph") / "data"))
    except (ImportError, ModuleNotFoundError, TypeError):
        return Path(__file__).parent / "data"


def queries_dir() -> Path:
    return _data_root() / "queries"


def skill_dir() -> Path:
    return _data_root() / "skill"


def skill_md() -> Path:
    return skill_dir() / "SKILL.md"


def skill_yaml_template() -> Path:
    return skill_dir() / "templates" / "skill.yaml"
