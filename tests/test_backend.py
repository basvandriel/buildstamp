from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import buildstamp.backend as backend


def test_prepare_metadata_for_build_editable_skips_write_in_git_checkout() -> None:
    with (
        patch.object(backend, "_is_git_checkout", return_value=True),
        patch.object(
            backend,
            "write_version_file",
        ) as write_file,
        patch(
            "setuptools.build_meta.prepare_metadata_for_build_editable", return_value="ok"
        ) as prepare_editable,
    ):
        result = backend.prepare_metadata_for_build_editable("metadata-dir", None)

    assert result == "ok"
    write_file.assert_not_called()
    prepare_editable.assert_called_once_with("metadata-dir", None)


def test_build_editable_skips_write_in_git_checkout() -> None:
    with (
        patch.object(backend, "_is_git_checkout", return_value=True),
        patch.object(
            backend,
            "write_version_file",
        ) as write_file,
        patch("setuptools.build_meta.build_editable", return_value="ok") as build_editable,
    ):
        result = backend.build_editable("wheel-dir", None, "metadata-dir")

    assert result == "ok"
    write_file.assert_not_called()
    build_editable.assert_called_once_with("wheel-dir", None, "metadata-dir")


def test_build_wheel_cleans_metadata_file_in_git_checkout(tmp_path: Path) -> None:
    metadata_file = tmp_path / "buildstamp" / "_build.json"
    metadata_file.parent.mkdir(parents=True)
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.0.0\n")

    with (
        patch.object(backend, "_is_git_checkout", return_value=True),
        patch.object(backend, "_git", return_value="abc1234"),
        patch.object(backend, "_read_config", return_value=(metadata_file, version_file, {})),
        patch.object(backend, "_build_wheel", return_value="ok") as build_wheel,
    ):
        result = backend.build_wheel("wheel-dir", None, None)

    assert result == "ok"
    build_wheel.assert_called_once_with("wheel-dir", None, None)
    assert not metadata_file.exists()


def test_build_sdist_cleans_metadata_file_in_git_checkout(tmp_path: Path) -> None:
    metadata_file = tmp_path / "buildstamp" / "_build.json"
    metadata_file.parent.mkdir(parents=True)
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.0.0\n")

    with (
        patch.object(backend, "_is_git_checkout", return_value=True),
        patch.object(backend, "_git", return_value="abc1234"),
        patch.object(backend, "_read_config", return_value=(metadata_file, version_file, {})),
        patch.object(backend, "_build_sdist", return_value="ok") as build_sdist,
    ):
        result = backend.build_sdist("sdist-dir", None)

    assert result == "ok"
    build_sdist.assert_called_once_with("sdist-dir", None)
    assert not metadata_file.exists()


def test_build_editable_force_write_in_git_checkout() -> None:
    with (
        patch.object(backend, "_is_git_checkout", return_value=True),
        patch.object(backend, "_force_write", return_value=True),
        patch.object(backend, "write_version_file") as write_file,
        patch("setuptools.build_meta.build_editable", return_value="ok"),
    ):
        result = backend.build_editable("wheel-dir", None, "metadata-dir")

    assert result == "ok"
    write_file.assert_called_once()


def test_prepare_metadata_for_build_wheel_cleans_metadata_file_in_git_checkout(
    tmp_path: Path,
) -> None:
    metadata_file = tmp_path / "buildstamp" / "_build.json"
    metadata_file.parent.mkdir(parents=True)
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.0.0\n")

    with (
        patch.object(backend, "_is_git_checkout", return_value=True),
        patch.object(backend, "_git", return_value="abc1234"),
        patch.object(backend, "_read_config", return_value=(metadata_file, version_file, {})),
        patch.object(backend, "_prepare_wheel", return_value="ok") as prepare_wheel,
    ):
        result = backend.prepare_metadata_for_build_wheel("metadata-dir", None)

    assert result == "ok"
    prepare_wheel.assert_called_once_with("metadata-dir", None)
    assert not metadata_file.exists()


def test_write_version_file_uses_dev_version_env_var(tmp_path: Path) -> None:
    metadata_file = tmp_path / "buildstamp" / "_build.json"
    metadata_file.parent.mkdir(parents=True)
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.0.0\n")

    with (
        patch.object(backend, "_git", return_value="abc1234"),
        patch.object(backend, "_read_config", return_value=(metadata_file, version_file, {})),
        patch.dict(
            os.environ,
            {"BUILDSTAMP_DEV_VERSION": "{base}+g{sha}", "RELEASE_TYPE": "dev"},
            clear=False,
        ),
    ):
        written = backend.write_version_file()

    assert written == metadata_file
    meta = json.loads(metadata_file.read_text())
    assert meta["version"] == "1.0.0+gabc1234"
    assert meta["quality"] == "dev"
    assert meta["commit"] == "abc1234"
