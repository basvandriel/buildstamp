from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from buildstamp.config import ReleaseType

MetadataPayload = dict[str, str]

# Default dotted key paths for known structured file formats.
_DEFAULT_KEYS: dict[str, str] = {
    "pyproject.toml": "project.version",
    "Cargo.toml": "package.version",
    "package.json": "version",
}


def _traverse(data: dict[str, object], key_path: list[str], source: Path) -> str:
    """Walk *data* using *key_path* segments and return the string value."""
    node: object = data
    for key in key_path:
        if not isinstance(node, dict):
            raise ValueError(
                f"buildstamp: expected a mapping while traversing "
                f"'{'.'.join(key_path)}' in {source}"
            )
        if key not in node:
            raise ValueError(
                f"buildstamp: key '{key}' not found in {source} "
                f"at path '{'.'.join(key_path)}'"
            )
        node = node[key]
    if not isinstance(node, str):
        raise ValueError(
            f"buildstamp: version at '{'.'.join(key_path)}' in {source} "
            f"must be a string, got {type(node).__name__}"
        )
    return node


def read_version_source(spec: str, root: Path) -> str:
    """Read the project version from *spec* relative to *root*.

    Spec format: ``<file>[:<dotted.key.path>]``

    Examples::

        pyproject.toml                       # default key: project.version
        pyproject.toml:tool.poetry.version   # Poetry layout
        package.json                         # default key: version
        Cargo.toml                           # default key: package.version
        Cargo.toml:workspace.package.version # Cargo workspace
        VERSION                              # plain text file
    """
    file_part, _, key_spec = spec.partition(":")
    key_path: list[str] | None = key_spec.split(".") if key_spec else None

    file = root / file_part
    suffix = file.suffix  # ".toml", ".json", ""

    if suffix == ".toml":
        try:
            import tomllib  # type: ignore[import-untyped]
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        with file.open("rb") as fh:
            data: dict[str, object] = tomllib.load(fh)

        resolved = key_path or _DEFAULT_KEYS.get(file.name, "").split(".") or None
        if not resolved or resolved == [""]:
            raise ValueError(
                f"buildstamp: no key path for {file} — "
                "specify one with 'filename.toml:<dotted.key>'"
            )
        return _traverse(data, resolved, file)

    if suffix == ".json":
        data = json.loads(file.read_text(encoding="utf-8"))
        resolved = key_path or _DEFAULT_KEYS.get(file.name, "").split(".") or None
        if not resolved or resolved == [""]:
            raise ValueError(
                f"buildstamp: no key path for {file} — "
                "specify one with 'filename.json:<dotted.key>'"
            )
        return _traverse(data, resolved, file)

    # Plain text file (VERSION, .version, or any other extension)
    return file.read_text(encoding="utf-8").strip()


def git_short_sha(root: Path | None = None) -> str:
    if root is None:
        root = Path.cwd()

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=root,
        ).strip()
    except Exception:
        return "unknown"


def render_version(
    base: str, sha: str, release_type: ReleaseType, dev_version_template: str
) -> str:
    if release_type == "stable":
        return base
    if release_type == "rc":
        return f"{base}rc1"

    try:
        return dev_version_template.format(base=base, sha=sha)
    except (KeyError, ValueError) as exc:
        raise ValueError(
            "BUILDSTAMP_DEV_VERSION must be a valid format string using only "
            "the supported placeholders {base} and {sha} "
            f"— got: {dev_version_template!r}"
        ) from exc


def build_metadata_payload(
    version: str, quality: str, commit: str, build_date: datetime | None
) -> MetadataPayload:
    if build_date is None:
        build_date = datetime.now(timezone.utc)

    return {
        "version": version,
        "quality": quality,
        "commit": commit,
        "build_date": build_date.isoformat(),
    }


def write_metadata_file(
    metadata_file: Path, version: str, quality: str, commit: str, build_date: datetime | None
) -> Path:
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.write_text(
        json.dumps(build_metadata_payload(version, quality, commit, build_date), indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata_file


def load_metadata_json(metadata_file: Path) -> MetadataPayload:
    return json.loads(metadata_file.read_text(encoding="utf-8"))
