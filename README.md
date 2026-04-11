# buildstamp

[![CI](https://github.com/basvandriel/buildstamp/actions/workflows/ci.yml/badge.svg)](https://github.com/basvandriel/buildstamp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/buildstamp)](https://pypi.org/project/buildstamp/)
[![Python](https://img.shields.io/pypi/pyversions/buildstamp)](https://pypi.org/project/buildstamp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Build-time version metadata injection for Python packages. Every artifact is
stamped with its version, quality tier, commit SHA, and build date — with no
metadata drift between source and installed packages, and no git required at
runtime.

---

## How it works

| Environment | Version source |
|---|---|
| Git checkout / editable install | Live: `git rev-parse` + `VERSION` file |
| Installed artifact (no `.git`) | Baked: `_build.json` written at build time |

The quality tier (`dev` / `rc` / `stable`) is controlled by the `RELEASE_TYPE`
environment variable at build time, so no tag ceremony is needed and no branch
names leak into artifacts.

---

## Quick start

**1. Configure `pyproject.toml`:**

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

No `_build_backend.py` shim or extra backend-path is required.

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

**5. Create a `VERSION` file** at the project root:

```
1.0.0
```

---

## `BuildMetadata` fields

| Field | Type | Dev (checkout) | Artifact |
|---|---|---|---|
| `version` | `str` | `"1.0.0+g701e4ca"` | `"1.0.0"` |
| `quality` | `str` | `"dev"` | `RELEASE_TYPE` value |
| `commit` | `str` | short SHA | short SHA baked at build time |
| `build_date` | `datetime \| None` | `None` | UTC datetime |

---

## Releasing artifacts

```sh
# stable release
RELEASE_TYPE=stable uv build

# release candidate
RELEASE_TYPE=rc uv build
```

If `RELEASE_TYPE` is unset, the baked quality defaults to `"dev"`.

---

## Installation

```sh
pip install buildstamp
```

While not yet on PyPI, install from source:

```sh
uv pip install setuptools
uv pip install -e /path/to/buildstamp
uv pip install -e . --no-build-isolation
```

---

## Design rationale

See [VERSIONING.md](VERSIONING.md) for the full rationale — including why this
avoids git tags, dirty flags, and branch names as version sources.
