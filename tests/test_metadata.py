"""Tests for buildstamp._metadata."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def clear_build_json_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BUILDSTAMP_USE_BUILD_JSON", raising=False)
    monkeypatch.delenv("BUILDSTAMP_USE_BAKED_METADATA", raising=False)


from buildstamp._metadata import BuildMetadata, load_metadata

# ---------------------------------------------------------------------------
# BuildMetadata
# ---------------------------------------------------------------------------


def test_build_metadata_is_frozen() -> None:
    meta = BuildMetadata(version="1.0.0", quality="dev", commit="abc1234", build_date=None)
    with pytest.raises((AttributeError, TypeError)):
        meta.version = "2.0.0"  # type: ignore[misc]


def test_build_metadata_slots() -> None:
    meta = BuildMetadata(version="1.0.0", quality="dev", commit="abc1234", build_date=None)
    assert not hasattr(meta, "__dict__")


def test_build_metadata_build_date_zone_conversion() -> None:
    build_date = datetime.fromisoformat("2026-04-10T12:00:00+00:00")
    meta = BuildMetadata(version="1.0.0", quality="stable", commit="abc1234", build_date=build_date)

    local = meta.build_date_local
    assert local is not None
    assert local.timestamp() == build_date.timestamp()
    assert local.tzinfo is not None

    amsterdam = meta.build_date_in_zone("Europe/Amsterdam")
    assert amsterdam.isoformat() == "2026-04-10T14:00:00+02:00"


# ---------------------------------------------------------------------------
# load_metadata — git checkout path
# ---------------------------------------------------------------------------


def _make_pkg(root: Path, version: str = "1.2.3") -> Path:
    """Create a minimal package tree under root and return the __init__.py path."""
    pkg = root / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (root / "VERSION").write_text(f"{version}\n")
    return pkg / "__init__.py"


def test_load_metadata_git_checkout(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    init = _make_pkg(tmp_path)

    with patch("buildstamp._metadata._run_git", return_value="abc1234"):
        meta = load_metadata(init)

    assert meta.version == "1.2.3+gabc1234"
    assert meta.quality == "dev"
    assert meta.commit == "abc1234"
    assert meta.build_date is None


def test_load_metadata_uses_baked_json_in_git_checkout_with_env(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (tmp_path / "VERSION").write_text("1.2.3\n")
    build_date = "2026-04-10T12:00:00+00:00"
    (pkg / "_build.json").write_text(
        json.dumps(
            {
                "version": "1.2.3",
                "quality": "stable",
                "commit": "abc1234",
                "build_date": build_date,
            }
        )
    )

    with patch.dict(os.environ, {"BUILDSTAMP_USE_BUILD_JSON": "1"}, clear=False):
        meta = load_metadata(pkg / "__init__.py")

    assert meta.version == "1.2.3"
    assert meta.quality == "stable"
    assert meta.commit == "abc1234"
    assert meta.build_date == datetime.fromisoformat(build_date)


def test_load_metadata_uses_dotenv(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (tmp_path / "VERSION").write_text("1.2.3\n")
    (tmp_path / ".env").write_text("BUILDSTAMP_USE_BUILD_JSON=1\n")
    build_date = "2026-04-10T12:00:00+00:00"
    (pkg / "_build.json").write_text(
        json.dumps(
            {
                "version": "1.2.3",
                "quality": "stable",
                "commit": "abc1234",
                "build_date": build_date,
            }
        )
    )

    meta = load_metadata(pkg / "__init__.py")

    assert meta.version == "1.2.3"
    assert meta.quality == "stable"
    assert meta.commit == "abc1234"
    assert meta.build_date == datetime.fromisoformat(build_date)


def test_load_metadata_git_unknown_sha(tmp_path: Path) -> None:
    """When git is not available, version should fall back to .dev0."""
    (tmp_path / ".git").mkdir()
    init = _make_pkg(tmp_path)

    with patch("buildstamp._metadata._run_git", return_value="unknown"):
        meta = load_metadata(init)

    assert meta.version == "1.2.3.dev0"
    assert meta.commit == "unknown"
    assert meta.build_date is None


def test_load_metadata_git_uses_version_file(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    init = _make_pkg(tmp_path, version="2.0.0")

    with patch("buildstamp._metadata._run_git", return_value="what"):
        meta = load_metadata(init)

    assert meta.version.startswith("2.0.0+g")


# ---------------------------------------------------------------------------
# load_metadata — artifact / installed package path
# ---------------------------------------------------------------------------


def test_load_metadata_from_build_json(tmp_path: Path) -> None:
    """Without .git, metadata is read from _build.json."""
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    init = pkg / "__init__.py"
    init.write_text("")

    build_date = "2026-04-10T12:00:00+00:00"
    (pkg / "_build.json").write_text(
        json.dumps(
            {
                "version": "1.2.3",
                "quality": "stable",
                "commit": "abc1234",
                "build_date": build_date,
            }
        )
    )

    meta = load_metadata(init)

    assert meta.version == "1.2.3"
    assert meta.quality == "stable"
    assert meta.commit == "abc1234"
    assert meta.build_date == datetime.fromisoformat(build_date)


def test_load_metadata_missing_json_raises(tmp_path: Path) -> None:
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    init = pkg / "__init__.py"
    init.write_text("")
    # no _build.json, no .git

    with pytest.raises((FileNotFoundError, OSError)):
        load_metadata(init)
