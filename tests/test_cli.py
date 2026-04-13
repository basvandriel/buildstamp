"""Tests for buildstamp CLI."""

from __future__ import annotations

import json
from pathlib import Path

from buildstamp.cli import main


def test_cli_write_creates_metadata(tmp_path: Path) -> None:
    (tmp_path / "VERSION").write_text("1.2.3\n")

    result = main(
        [
            "write",
            "--root",
            str(tmp_path),
            "--metadata-file",
            "mypkg/_build.json",
            "--version-file",
            "VERSION",
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
