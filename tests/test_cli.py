"""Tests for buildstamp CLI."""

from __future__ import annotations

import json
from pathlib import Path

from buildstamp.cli import main


def test_cli_write_creates_metadata_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "mypkg"\nversion = "1.2.3"\n', encoding="utf-8"
    )

    result = main(
        [
            "write",
            "--root",
            str(tmp_path),
            "--metadata-file",
            "mypkg/_build.json",
        ]
    )

    assert result == 0
    metadata_path = tmp_path / "mypkg" / "_build.json"
    assert metadata_path.exists()

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert data["version"] == "1.2.3.dev0"
    assert data["quality"] == "dev"
    assert data["commit"] == "unknown"
    assert data["build_date"].endswith("+00:00")


def test_cli_write_creates_metadata_from_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"name": "mypkg", "version": "2.0.0"}', encoding="utf-8"
    )

    result = main(
        [
            "write",
            "--root",
            str(tmp_path),
            "--metadata-file",
            "dist/_build.json",
            "--version-source",
            "package.json",
        ]
    )

    assert result == 0
    data = json.loads((tmp_path / "dist" / "_build.json").read_text(encoding="utf-8"))
    assert data["version"] == "2.0.0.dev0"


def test_cli_write_creates_metadata_from_pyproject_custom_key(tmp_path: Path) -> None:
    """Explicit dotted key path overrides the default project.version location."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "mypkg"\nversion = "9.9.9"\n', encoding="utf-8"
    )

    result = main(
        [
            "write",
            "--root",
            str(tmp_path),
            "--metadata-file",
            "mypkg/_build.json",
            "--version-source",
            "pyproject.toml:tool.poetry.version",
        ]
    )

    assert result == 0
    data = json.loads((tmp_path / "mypkg" / "_build.json").read_text(encoding="utf-8"))
    assert data["version"] == "9.9.9.dev0"


def test_cli_write_creates_metadata_from_plain_file(tmp_path: Path) -> None:
    (tmp_path / "VERSION").write_text("3.1.4\n", encoding="utf-8")

    result = main(
        [
            "write",
            "--root",
            str(tmp_path),
            "--metadata-file",
            "mypkg/_build.json",
            "--version-source",
            "VERSION",
        ]
    )

    assert result == 0
    data = json.loads((tmp_path / "mypkg" / "_build.json").read_text(encoding="utf-8"))
    assert data["version"] == "3.1.4.dev0"
