from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

ReleaseType = Literal["dev", "rc", "stable"]
MetadataPayload = dict[str, str]


def read_version_file(version_file: Path) -> str:
    return version_file.read_text(encoding="utf-8").strip()


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
