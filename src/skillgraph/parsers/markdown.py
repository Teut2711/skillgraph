from __future__ import annotations

import re

from ..model import Node, sha256_text


def slugify(text: str) -> str:
    out = []
    for ch in text.lower().strip():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_/":
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "untitled"


def _headings(lines: list[str]) -> list[tuple[int, int, str, str]]:
    out: list[tuple[int, int, str, str]] = []
    for i, line in enumerate(lines):
        s = line.lstrip()
        if not s.startswith("#"):
            continue
        level = len(s) - len(s.lstrip("#"))
        if 1 <= level <= 6 and len(s) > level and s[level] == " ":
            title = s[level:].strip().strip("#").strip()
            out.append((i, level, title, slugify(title)))
    return out


def parse_sections(rel: str, text: str, skill_id: str) -> tuple[list[Node], list[tuple[str, str, str]]]:
    lines = text.splitlines()
    headings = _headings(lines)
    nodes: list[Node] = []
    edges: list[tuple[str, str, str]] = []
    stack: list[tuple[int, str]] = []

    for idx, (start, level, title, slug) in enumerate(headings):
        end = len(lines) - 1
        for nxt in headings[idx + 1 :]:
            if nxt[1] <= level:
                end = nxt[0] - 1
                break
        body = "\n".join(lines[start : end + 1])
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent_id = stack[-1][1] if stack else skill_id
        node_id = f"section.{slug}"
        stack.append((level, node_id))
        nodes.append(
            Node(
                id=node_id,
                type="section",
                title=title,
                file=rel,
                span=[start + 1, end + 1],
                hash=sha256_text(body),
                meta={"level": level, "parent": parent_id},
            )
        )
        edges.append((parent_id, "contains", node_id))
    return nodes, edges


def parse_code_refs(_rel: str, text: str, skill_id: str) -> list[tuple[str, str, str]]:
    lines = text.splitlines()
    headings = _headings(lines)
    edges: list[tuple[str, str, str]] = []
    for i, line in enumerate(lines):
        current = skill_id
        for h in headings:
            if h[0] <= i:
                current = f"section.{h[3]}"
            else:
                break
        for m in re.finditer(r"`([A-Za-z0-9_./-]+)`", line):
            edges.append((current, "references", f"?{m.group(1)}"))
        for m in re.finditer(r"\]\(([^)#]+)\)", line):
            target = m.group(1).strip()
            if target.startswith(("http", "mailto:")):
                continue
            edges.append((current, "references", f"?{target}"))
    return edges
