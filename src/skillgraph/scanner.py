from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Iterator

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
             ".mypy_cache", ".pytest_cache", "dist", "build", ".graph"}
SKIP_FILES = {"graph.nodes.jsonl", "graph.edges.jsonl", "INDEX.md", "backlinks.md",
              "budget.json", "skillgraph.db"}


def load_ignore_patterns(root: Path) -> list[str]:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return []
    pats: list[str] = []
    for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            pats.append(line.rstrip("/"))
    return pats


def is_ignored(rel: str, patterns: list[str]) -> bool:
    parts = rel.split("/")
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(parts[-1], pat):
            return True
        if any(fnmatch.fnmatch(p, pat) for p in parts):
            return True
    return False


def iter_files(root: Path) -> Iterator[Path]:
    patterns = load_ignore_patterns(root)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.name in SKIP_FILES:
            continue
        rel = path.relative_to(root).as_posix()
        if is_ignored(rel, patterns):
            continue
        yield path


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
