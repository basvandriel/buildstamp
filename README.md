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

Optional buildstamp configuration:

```toml
[tool.buildstamp]
metadata-file = "your_package/_build.json"
version-file = "VERSION"
```

For dev artifact naming, use an environment variable instead of pyproject:

```sh
BUILDSTAMP_DEV_VERSION="{base}+g{sha}" RELEASE_TYPE=dev uv build
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
| `build_date_local` | `datetime \| None` | `None` | local timezone datetime |

---

## Inspect built metadata

To verify the baked metadata in a release artifact without relying on runtime imports:

1. Build the artifact:

```sh
RELEASE_TYPE=stable uv build --no-build-isolation
```

2. List the wheel contents and confirm `_build.json` is present:

```sh
unzip -l dist/buildstamp-*.whl | grep '_build.json'
```

3. Extract and pretty-print `_build.json` from the wheel:

```sh
unzip -p dist/buildstamp-*.whl buildstamp/_build.json | python -m json.tool
```

4. Optionally inspect the source distribution as well:

```sh
tar -tzf dist/buildstamp-*.tar.gz | grep 'buildstamp/_build.json'
 tar -xOzf dist/buildstamp-*.tar.gz buildstamp/_build.json | python -m json.tool
```

5. Convert the stored UTC build timestamp to Amsterdam time:

```sh
python - <<'PY'
from datetime import datetime
from zoneinfo import ZoneInfo

utc_dt = datetime.fromisoformat('2026-04-11T21:43:17.362671+00:00')
print(utc_dt.astimezone(ZoneInfo('Europe/Amsterdam')).isoformat())
PY
```

6. Verify the artifact format:

```sh
uv run twine check dist/*
```

That gives you a fully manual inspection path: the wheel is just a zip archive, `_build.json` is extracted directly, and the UTC build timestamp can be converted to local display time.
### Optional in-repo runtime validation

If you want to exercise the baked metadata path from inside a git checkout, first generate `_build.json` and keep it in the repo:

```sh
BUILDSTAMP_FORCE_WRITE=1 uv build --no-build-isolation
```

Then run Python with the baked-metadata override:

```sh
BUILDSTAMP_USE_BUILD_JSON=1 python - <<'PY'
from buildstamp import load_metadata
import buildstamp

meta = load_metadata(buildstamp.__file__)
print(meta)
PY
```

`BUILDSTAMP_USE_BUILD_JSON` is the name to use for in-repo baked metadata testing.

That lets you verify the same `_build.json`-based runtime behavior without leaving the checkout.
## Inspect the installed artifact in Python runtime

To verify the same baked metadata from an installed package, install the wheel into a fresh environment and use `load_metadata()`:

```sh
pip install dist/buildstamp-*.whl
python - <<'PY'
from buildstamp import load_metadata
import buildstamp

meta = load_metadata(buildstamp.__file__)
print('version:', meta.version)
print('quality:', meta.quality)
print('commit:', meta.commit)
print('build_date:', meta.build_date)
print('local build_date:', meta.build_date_local)
PY
```

If you run this inside the source checkout with `.git` present, `load_metadata()` will use live git metadata instead of the baked `_build.json`. That is why installing the wheel into a clean environment is the right way to verify the shipped artifact.

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
