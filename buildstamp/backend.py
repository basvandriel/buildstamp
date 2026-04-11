"""PEP 517 build backend that injects VCS metadata at build time.

Use this module directly as the build backend in `pyproject.toml`:

    [build-system]
    requires = ["setuptools>=64.0", "wheel", "buildstamp"]
    build-backend = "buildstamp.backend"

No `_build_backend.py` shim is required; the project root is already importable
when running from the source checkout.
buildstamp reads [tool.buildstamp] from pyproject.toml for configuration.
If not present, the package name is derived from [project].name.

    [tool.buildstamp]
    metadata-file = "your_package/_build.json"   # optional override
    version-file  = "VERSION"                       # optional override (default: VERSION)
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from setuptools.build_meta import (
    build_sdist as _build_sdist,
)
from setuptools.build_meta import (
    build_wheel as _build_wheel,
)
from setuptools.build_meta import (
    get_requires_for_build_editable,
    get_requires_for_build_sdist,
    get_requires_for_build_wheel,
)
from setuptools.build_meta import (
    prepare_metadata_for_build_wheel as _prepare_wheel,
)

__all__ = [
    "build_editable",
    "build_sdist",
    "build_wheel",
    "get_requires_for_build_editable",
    "get_requires_for_build_sdist",
    "get_requires_for_build_wheel",
    "prepare_metadata_for_build_editable",
    "prepare_metadata_for_build_wheel",
]


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "unknown"


def _read_config() -> tuple[Path, Path]:
    """Return (metadata_file, version_file) from pyproject.toml config."""
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        raise RuntimeError(f"buildstamp: could not read pyproject.toml — {e}") from e

    bs = config.get("tool", {}).get("buildstamp", {})
    version_file = Path(bs.get("version-file", "VERSION"))

    if "metadata-file" in bs:
        return Path(bs["metadata-file"]), version_file

    # Derive from [project].name: rsync-server → rsync_server/_build.json
    try:
        name = config["project"]["name"].replace("-", "_")
        return Path(name) / "_build.json", version_file
    except KeyError as exc:
        raise RuntimeError(
            "buildstamp: could not determine metadata file path. "
            "Add [tool.buildstamp] metadata-file = 'your_package/_build.json' "
            "to pyproject.toml."
        ) from exc


def write_version_file() -> None:
    """Write _build.json with build-time metadata.

    Called automatically by all PEP 517 hooks. Can also be called manually.
    """
    metadata_file, version_file = _read_config()
    commit = _git("rev-parse", "--short", "HEAD")

    # sdist → wheel: no .git dir, reuse the JSON baked in during the sdist step.
    if commit == "unknown" and metadata_file.exists():
        return

    base = version_file.read_text(encoding="utf-8").strip()
    raw = os.environ.get("RELEASE_TYPE", "dev").strip().lower()
    if raw not in ("dev", "rc", "stable"):
        raise ValueError(f"RELEASE_TYPE must be 'dev', 'rc', or 'stable' — got: {raw!r}")
    if raw == "stable":
        version = base
    elif raw == "rc":
        version = f"{base}rc1"
    else:
        version = f"{base}.dev0"

    metadata_file.write_text(
        json.dumps(
            {
                "version": version,
                "quality": raw,
                "commit": commit,
                "build_date": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


# --- PEP 517 hooks -----------------------------------------------------------


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    write_version_file()
    return _prepare_wheel(metadata_directory, config_settings)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    write_version_file()
    return _build_wheel(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    write_version_file()
    return _build_sdist(sdist_directory, config_settings)


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    from setuptools.build_meta import (
        prepare_metadata_for_build_editable as _prepare_editable,
    )

    write_version_file()
    return _prepare_editable(metadata_directory, config_settings)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    from setuptools.build_meta import build_editable as _build_editable

    write_version_file()
    return _build_editable(wheel_directory, config_settings, metadata_directory)
