# buildstamp — Copilot context

## What it is

Reusable Python library for build-time version metadata injection.
Sibling to `../rsync-server` which is its first consumer.

## Key files

- `buildstamp/_metadata.py` — `BuildMetadata` frozen dataclass + `load_metadata(package_file)`
- `buildstamp/backend.py` — PEP 517 hooks wrapping setuptools; `write_version_file()` writes `_build.json`
- `buildstamp/__init__.py` — re-exports `BuildMetadata`, `load_metadata`
- `VERSIONING.md` — full design rationale and decisions
- `DEVELOPMENT.md` — setup guide and usage instructions

## Core design

- `.git` present → `load_metadata()` calls `git rev-parse`, reads `VERSION` → live metadata
- `.git` absent → reads `your_package/_build.json` baked in at build time
- `VERSION` file is the only version source of truth (read by setuptools directly via `{file = "VERSION"}`)
- `RELEASE_TYPE` env var (`dev`/`rc`/`stable`) controls quality suffix in artifact builds
- No git tags required, no dirty flag, no branch field, no git at import time in production

## BuildMetadata fields

```python
version: str           # "0.1.0+g701e4ca" (dev) or "0.1.0" (artifact)
quality: str           # "dev" always in checkout, baked value in artifact
commit: str            # short SHA
build_date: Optional[datetime]  # None in checkout, UTC datetime in artifact
```

## Consumer project setup (minimal)

1. `pyproject.toml`: `version = {file = "VERSION"}`, build-backend = `buildstamp.backend`, requires buildstamp
2. `__init__.py`: `_meta = load_metadata(__file__)`
3. `.gitignore`: `your_package/_build.json`

## Install (not yet on PyPI)

```sh
uv pip install setuptools
uv pip install -e /path/to/buildstamp
uv pip install -e . --no-build-isolation
```

## Current state (as of first release prep)

- `buildstamp/__version__` added via `importlib.metadata.version("buildstamp")`
- `uv.lock` + `.venv` created — now a proper uv project
- `VERSION` = `0.1.0`, not yet tagged, not yet on PyPI
- rsync-server is the only consumer, installed as `uv pip install -e ../buildstamp`
- Pylance in rsync-server needs `python.analysis.extraPaths: ["/Users/bas/code/buildstamp"]` due to setuptools editable install finder not being followed by Pylance

## Release checklist (first PyPI release)

1. Ensure all changes committed
2. `uv build` → produces `dist/buildstamp-0.1.0.tar.gz` and `.whl`
3. `uv publish` → publishes to PyPI (needs `PYPI_TOKEN` or `~/.pypirc`)
4. `git tag v0.1.0 && git push --tags`
5. After on PyPI: rsync-server drops `--no-build-isolation` and `extraPaths`

## Python

3.10+, uv managed venv (`uv sync` to bootstrap).
