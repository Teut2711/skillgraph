# Publishing skillgraph to PyPI

Mirrors the `adaptive-executor` release flow.

## Prerequisites

1. PyPI account: https://pypi.org/account/register/
2. Trusted publisher configured for this repo (recommended, no tokens) OR an API token.
3. For TestPyPI: https://test.pypi.org/

## Setup (trusted publishing)

On PyPI: project `skillgraph-py` -> Publishing -> add a GitHub publisher:
- Owner: `Teut2711`
- Repository: `skillgraph`
- Workflow: `publish.yaml`
- Environment: `pypi`

Create a GitHub environment named `pypi` in the repo settings.

## Release (automated, recommended)

```bash
# 1. bump version in pyproject.toml
git add pyproject.toml
git commit -m "chore: bump version to 0.1.1"

# 2. tag and push
git tag v0.1.1
git push origin v0.1.1
```

`.github/workflows/publish.yaml` builds, checks, and uploads to PyPI.

## Release (manual)

```bash
make clean
make build
python -m twine check dist/*
make upload           # production
make upload-test      # TestPyPI
```

## Version checklist

- [ ] bump `version` in `pyproject.toml`
- [ ] `make test` passes
- [ ] `make lint` clean (pylint 10, ruff clean)
- [ ] `make build` succeeds
- [ ] `python -m twine check dist/*` OK
- [ ] install the wheel in a clean venv and run `skillgraph --help`

## Verify after publishing

```bash
pip install skillgraph-py
skillgraph --help
skillgraph init demo.skill
skillgraph up demo.skill
```

## Notes

- Never commit tokens; use the `pypi` environment + trusted publishing.
- `requires-python = ">=3.10"`.
- Distribution name is `skillgraph-py`; import name and CLI are `skillgraph`.
- Web extras are optional: `pip install "skillgraph-py[web]"`.
