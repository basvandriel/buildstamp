"""PEP 517 build backend that injects VCS metadata at build time.

Use this module directly as the build backend in `pyproject.toml`:

    [build-system]
    requires = ["setuptools>=64.0", "wheel", "buildstamp"]
    build-backend = "buildstamp.backend"

No `_build_backend.py` shim is required; the project root is already importable
when running from the source checkout.

When installing editable from a git checkout, buildstamp skips writing
`_build.json` because runtime metadata is already available from git.
buildstamp reads [tool.buildstamp] from pyproject.toml for configuration.
If not present, the package name is derived from [project].name.

    [tool.buildstamp]
    metadata-file = "your_package/_build.json"   # optional override
    version-file  = "VERSION"                       # optional override (default: VERSION)

For dev builds, override the generated artifact version via env var:

    BUILDSTAMP_DEV_VERSION="{base}+g{sha}"

The template supports `{base}` and `{sha}` placeholders.

To force writing `_build.json` even in a git checkout (e.g. for
debugging or baking metadata into an editable install):

    BUILDSTAMP_FORCE_WRITE=1
"""

from __future__ import annotations

import contextlib
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


def _read_config() -> tuple[Path, Path, dict[str, object]]:
    """Return (metadata_file, version_file, config) from pyproject.toml."""
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
        return Path(bs["metadata-file"]), version_file, bs

    # Derive from [project].name: rsync-server → rsync_server/_build.json
    try:
        name = config["project"]["name"].replace("-", "_")
        return Path(name) / "_build.json", version_file, bs
    except KeyError as exc:
        raise RuntimeError(
            "buildstamp: could not determine metadata file path. "
            "Add [tool.buildstamp] metadata-file = 'your_package/_build.json' "
            "to pyproject.toml."
        ) from exc


def _is_git_checkout() -> bool:
    return Path(".git").exists()


def _envvar_to_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() not in ("", "0", "false", "no")


def _force_write() -> bool:
    return _envvar_to_bool("BUILDSTAMP_FORCE_WRITE")


def write_version_file() -> Path | None:
    """Write _build.json with build-time metadata.

    Called automatically by all PEP 517 hooks. Can also be called manually.

    Returns the path of the metadata file that was written, or None if no file
    needed to be written.
    """
    metadata_file, version_file, bs = _read_config()
    commit = _git("rev-parse", "--short", "HEAD")

    # sdist → wheel: no .git dir, reuse the JSON baked in during the sdist step.
    if commit == "unknown" and metadata_file.exists():
        return None

    base = version_file.read_text(encoding="utf-8").strip()
    raw = os.environ.get("RELEASE_TYPE", "dev").strip().lower()
    if raw not in ("dev", "rc", "stable"):
        raise ValueError(f"RELEASE_TYPE must be 'dev', 'rc', or 'stable' — got: {raw!r}")

    if raw == "stable":
        version = base
    elif raw == "rc":
        version = f"{base}rc1"
    else:
        dev_template = os.environ.get("BUILDSTAMP_DEV_VERSION", "{base}.dev0")
        version = dev_template.format(base=base, sha=commit)

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

    return metadata_file


def _cleanup_metadata_file(metadata_file: Path | None) -> None:
    if metadata_file is None or not _is_git_checkout():
        return

    with contextlib.suppress(FileNotFoundError):
        metadata_file.unlink()


# --- PEP 517 hooks -----------------------------------------------------------


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    write_version_file()
    return _prepare_wheel(metadata_directory, config_settings)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    metadata_file = write_version_file()
    try:
        return _build_wheel(wheel_directory, config_settings, metadata_directory)
    finally:
        _cleanup_metadata_file(metadata_file)


def build_sdist(sdist_directory, config_settings=None):
    metadata_file = write_version_file()
    try:
        return _build_sdist(sdist_directory, config_settings)
    finally:
        _cleanup_metadata_file(metadata_file)


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    from setuptools.build_meta import (
        prepare_metadata_for_build_editable as _prepare_editable,
    )

    if not _is_git_checkout() or _force_write():
        write_version_file()
    return _prepare_editable(metadata_directory, config_settings)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    from setuptools.build_meta import build_editable as _build_editable

    if not _is_git_checkout() or _force_write():
        write_version_file()
    return _build_editable(wheel_directory, config_settings, metadata_directory)
