# Development

## What this is

`buildstamp` is a reusable Python library providing:

- **`buildstamp.backend`** — a PEP 517 build backend (wraps setuptools) that
  writes `_build.json` at build time with version, quality, commit SHA, and
  build date
- **`buildstamp.load_metadata()`** — runtime helper that returns a
  `BuildMetadata` dataclass; branches on `.git` presence to give live git
  metadata in development and baked JSON metadata in shipped artifacts

See [VERSIONING.md](VERSIONING.md) for the full design rationale.

---

## Setup

```sh
git clone <this repo>
cd buildstamp
uv venv && uv pip install -e .
```

No build step needed — the package has no compiled components.

---

## Using buildstamp in a project

**1. Add to `pyproject.toml`:**

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {file = "VERSION"}

[tool.setuptools.package-data]
your_package = ["_build.json"]

[build-system]
requires = ["setuptools>=64.0", "wheel", "buildstamp"]
build-backend = "buildstamp.backend"
```

**2. Build normally** using the configured backend. No `_build_backend.py` shim is required.

**3. Add `_build.json` to `.gitignore`:**

```
your_package/_build.json
```

**4. Use in `your_package/__init__.py`:**

```python
from buildstamp import load_metadata

_meta          = load_metadata(__file__)
__version__    = _meta.version
__quality__    = _meta.quality
__commit__     = _meta.commit
__build_date__ = _meta.build_date
```

**5. Install (while buildstamp is not yet on PyPI):**

```sh
uv pip install setuptools
uv pip install -e /path/to/buildstamp
uv pip install -e . --no-build-isolation
```

Once buildstamp is on PyPI, the last two steps collapse to `pip install -e .`.

---

## Optional: configure paths in pyproject.toml

By default buildstamp derives the metadata file path from `[project].name`
(e.g. `rsync-server` → `rsync_server/_build.json`). To override:

```toml
[tool.buildstamp]
metadata-file = "your_package/_build.json"
version-file  = "VERSION"
```

---

## Cutting a release for buildstamp itself

```sh
# Edit VERSION, then:
RELEASE_TYPE=stable python -m build
```
