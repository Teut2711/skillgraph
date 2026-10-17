---
name: skillgraph
description: Compile a folder of skills (Markdown, Python, SQL, JS, etc.) into a grounded, searchable graph index. Use when asked to "index skills", "build a skill graph", "make a skill folder searchable", "convert skills to a graph", "dedupe skills", or "lint a skill repo". Produces node/edge JSONL with file+span+hash provenance so an agent can retrieve exact bytes and cite them.
---

# skillgraph

Compile a skill repository into a **source-authoritative graph**. Never rewrite
the source. The graph is derived, disposable, and always points back to real bytes.

## When to use

- A skill folder grew nested scripts, SQL, config, references and is hard to navigate.
- An agent keeps loading the wrong files or hallucinating which file matters.
- You want dedupe, broken-reference detection, and token-budget context assembly.

## Pipeline

```
1. scan    skill.yaml + files  -> graph.nodes.jsonl / graph.edges.jsonl (+ sqlite)
2. check   lint: E001 broken ref, E002 cycle, W001 orphan, W010 stale, W030 oversized
3. dedup   exact-hash + normalized-title -> same_as edges (never merges sources)
4. query   lexical search over id/title/summary/tags/aliases
5. explain a node and its in/out edges
6. context assemble verbatim spans under a token budget
```

## Commands

```bash
skillgraph scan <root> [--sqlite]
skillgraph check <root> [--json]
skillgraph report <root>
skillgraph query <root> "<terms>"
skillgraph explain <root> <node-id>
skillgraph context <root> "<question>" --budget 2000
```

## The spec (skill.yaml)

Declare sources and extraction policy. Facts come from parsers, never from the spec.

```yaml
skill: migration
version: 1
sources:
  - glob: "**/*.md"
    parser: markdown
    nodes: [skill, section]
  - glob: "scripts/**/*.py"
    parser: python
    nodes: [file, symbol]
  - glob: "sql/**/*.sql"
    parser: sql
    nodes: [sql_table, sql_query]
rules:
  - {edge: contains, from: skill, to: section}
  - {edge: references, from: section, match: backtick.code_ref}
  - {edge: requires, from: symbol, match: python.import}
```

If `skill.yaml` is missing, a sensible default is used and `check` reports `W003`.

## Node / edge schema

Node: `id, type, title, file, span, hash, summary, tags, aliases, meta`
Types: `skill section step file symbol config sql_table sql_query example concept`
Edge: `from, rel, to`
Relations: `contains references requires depends_on implements prerequisite alias_of example_of same_as`

## Grounding rules (enforced by design)

1. Every node keeps `file` + `span` + `hash`.
2. Extractors are deterministic; no LLM writes the index.
3. Dedupe emits `same_as` edges; sources stay untouched.
4. `check` is the gate. Fix errors before trusting retrieval.
5. Risky fixes become reviewable patches, not silent writes.

## Agent loop

1. `scan` once (and after source changes).
2. `search`/`query` for seed nodes.
3. `explain`/traverse edges 1 hop to pull required scripts and dependencies.
4. `context` to get verbatim spans under budget.
5. Cite node ids in the answer; `check` verifies refs still resolve.
