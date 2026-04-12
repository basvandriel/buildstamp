from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class BuildMetadata:
    version: str
    quality: str
    commit: str
    build_date: datetime | None

    @property
    def build_date_local(self) -> datetime | None:
        """Return the build date converted to the local system timezone."""
        if self.build_date is None:
            return None
        return self.build_date.astimezone()

    def build_date_in_zone(self, zone: str) -> datetime | None:
        """Return the build date converted to the requested timezone."""
        if self.build_date is None:
            return None
        return self.build_date.astimezone(ZoneInfo(zone))


def _envvar_to_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() not in ("", "0", "false", "no")


def _load_dotenv(root: Path) -> None:
    dotenv_path = root / ".env"
    if not dotenv_path.exists():
        return

    try:
        import dotenv

        dotenv.load_dotenv(dotenv_path, override=False)
    except ImportError:
        return


def _use_baked_metadata() -> bool:
    return _envvar_to_bool("BUILDSTAMP_USE_BUILD_JSON")


def _run_git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "unknown"


def load_metadata(package_file: str | Path) -> BuildMetadata:
    """Load version metadata for a package.

    Call from your package's __init__.py:

        from buildstamp import load_metadata

        _meta          = load_metadata(__file__)
        __version__    = _meta.version
        __quality__    = _meta.quality
        __commit__     = _meta.commit
        __build_date__ = _meta.build_date

    In a git checkout (development or editable install), metadata is computed
    live from git — always accurate, never stale. In an installed artifact
    (no .git), it is read from _build.json baked in at build time.
    """
    package_dir = Path(package_file).parent
    repo_root = package_dir.parent
    _load_dotenv(repo_root)

    if (repo_root / ".git").exists() and not _use_baked_metadata():
        base = (repo_root / "VERSION").read_text(encoding="utf-8").strip()
        sha = _run_git("rev-parse", "--short", "HEAD")
        version = f"{base}+g{sha}" if sha != "unknown" else f"{base}.dev0"
        return BuildMetadata(version=version, quality="dev", commit=sha, build_date=None)

    meta = json.loads((package_dir / "_build.json").read_text(encoding="utf-8"))
    return BuildMetadata(
        version=meta["version"],
        quality=meta["quality"],
        commit=meta["commit"],
        build_date=datetime.fromisoformat(meta["build_date"]),
    )
