# skillgraph

A knowledge compiler for agent skill repositories.

Source files stay authoritative. A deterministic builder derives a searchable
**graph of nodes and edges** with full provenance (file + span + hash), so an
LLM can retrieve the exact bytes it needs and cite them, instead of guessing
which file matters.

## Why

- `grep` is literal; a graph follows `references` / `requires` / `alias_of` edges.
- Every node points at real bytes, so answers are grounded and citations checkable.
- The index is derived and disposable: delete it, rebuild, get the same result from
  unchanged inputs.
- No latent/soft-prompt encodings. API-only workflows stay supported.

## Three layers

```
CST/AST (per file, real parser)  ->  skill tree (merged, stable IDs)  ->  graph (nodes + edges)
                     skill.yaml declares what to extract; the builder stays generic
```

## Install

```bash
pip install skillgraph-py              # core (CLI + graph)
pip install "skillgraph-py[web]"       # + FastAPI/ReactPy UI
pip install "skillgraph-py[treesitter]"  # + richer multi-language parsing
```

From source:

```bash
git clone https://github.com/Teut2711/skillgraph
cd skillgraph
pip install -e ".[dev]"
```

## Quickstart

```bash
skillgraph init my.skill                        # scaffold a new .skill project
skillgraph scan my.skill                        # build graph.nodes.jsonl / graph.edges.jsonl
skillgraph check my.skill                       # lint rules (broken refs, orphans, cycles, staleness)
skillgraph report my.skill                      # health score
skillgraph query my.skill "rollback migration"
skillgraph explain my.skill skill.migration
skillgraph context my.skill "how do I revert a failed migration" --budget 1500
skillgraph up my.skill --port 8000              # scan + serve the UI in one shot
```

`skillgraph --help` lists all commands: `init, scan, check, report, query, explain, context, serve, up`.

## Web UI (FastAPI + ReactPy)

```bash
skillgraph serve my.skill --port 8000     # serve an existing index
skillgraph up my.skill --port 8000        # rebuild the index, then serve
# open http://127.0.0.1:8000
```

The UI is pure Python (no JS build): point it at a `.skill` folder, Scan, search
nodes, click a node to see its exact source span plus in/out edges, run Check, and
assemble Context under a char budget.

Headless API:

```
GET /api/health?root=<path>                    -> {nodes, edges, errors, warnings, score, by_code}
GET /api/node/<node-id>?root=<path>            -> {node, body, out, in}
```

## Node / edge format

`graph.nodes.jsonl`

```json
{"id":"section.migration.safe","type":"section","title":"Safe migrations",
 "file":"SKILL.md","span":[12,28],"hash":"sha256:cd34...","summary":"",
 "tags":[],"aliases":[],"meta":{}}
```

`graph.edges.jsonl`

```json
{"from":"skill.migration","rel":"contains","to":"section.migration.safe"}
```

Node types: `skill section step file symbol config sql_table sql_query example concept`
Edge relations: `contains references requires depends_on implements prerequisite alias_of example_of same_as`

## Layout

```
src/skillgraph/
  model.py          Node / Edge / Graph
  spec.py           skill.yaml loader + defaults
  scanner.py        repo walk + ignore rules
  parsers/          markdown, python_ast, sql
  graph_builder.py  orchestrates extraction + resolution + dedup
  store.py          jsonl + sqlite (FTS5) + search
  dedup.py          exact / title dedupe -> same_as edges
  validate.py       lint rules (E001, E002, W001, W010, ...)
  report.py         health + token budget
  ops.py            shared load / check / context helpers
  scaffold.py       `skillgraph init` project template
  paths.py          package-data access (queries, skill template)
  cli.py            command line
  web/              FastAPI + ReactPy UI
  data/queries/     tree-sitter query files (shipped)
  data/skill/       the agent-facing skill (shipped)
examples/           a sample .skill repo
tests/              pytest suite
```

## Development

```bash
make install-dev    # editable install with dev + web extras
make test           # pytest with coverage
make lint           # pylint (10/10) + ruff
make build          # sdist + wheel
make check          # lint + test
```

## Publishing

Release is tag-driven (trusted publishing). See [PUBLISHING.md](PUBLISHING.md).

```bash
# bump version in pyproject.toml, then:
git tag v0.1.0
git push origin v0.1.0     # .github/workflows/publish.yaml builds + uploads to PyPI
```

## Design rules

1. YAML is policy; parsers are facts. Never encode code semantics in YAML.
2. Every node keeps `file` + `span` + `hash`.
3. Extractors are deterministic; no LLM in the build.
4. Dedup emits `same_as` edges, never rewrites sources.
5. Risky fixes become reviewable patches, not silent writes.
