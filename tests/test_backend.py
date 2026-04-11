from __future__ import annotations

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
