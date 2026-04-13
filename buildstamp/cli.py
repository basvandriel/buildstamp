from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from buildstamp.config import BuildConfig, ReleaseType
from buildstamp.core import (
    git_short_sha,
    read_version_source,
    render_version,
    write_metadata_file,
)
from buildstamp.env import load_dotenv


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="buildstamp",
        description="Generate build metadata for a project.",
    )
    parser.add_argument("command", choices=["write"], help="Command to execute.")
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory for .env and VERSION file.",
    )
    parser.add_argument(
        "--version-source",
        default="pyproject.toml",
        help="Path to the version source file relative to the project root. "
        "Supports pyproject.toml, package.json, or any plain text file (e.g. VERSION).",
    )
    parser.add_argument(
        "--metadata-file",
        default="buildstamp/_build.json",
        help="Path to write metadata relative to the project root.",
    )
    parser.add_argument(
        "--release-type",
        choices=["dev", "rc", "stable"],
        default=None,
        help="Build quality: dev, rc, or stable. Defaults to RELEASE_TYPE env var or dev.",
    )
    parser.add_argument(
        "--dev-version-template",
        default=None,
        help="Template for dev version formatting, using {base} and {sha}.",
    )
    parser.add_argument(
        "--force-write",
        action="store_true",
        help="Force writing metadata even when git metadata is unavailable.",
    )
    parser.add_argument(
        "--no-dotenv",
        action="store_true",
        help="Do not load a .env file from the project root.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = Path(args.root)

    if not args.no_dotenv:
        load_dotenv(root)

    cfg = BuildConfig.from_options(
        release_type=args.release_type,
        dev_version_template=args.dev_version_template,
        force_write=args.force_write,
    )

    metadata_file = root / args.metadata_file
    commit = git_short_sha(root)

    if commit == "unknown" and metadata_file.exists() and not cfg.force_write:
        return 0

    base = read_version_source(args.version_source, root)
    version = render_version(base, commit, cfg.release_type, cfg.dev_version_template)
    write_metadata_file(
        metadata_file,
        version,
        cfg.release_type,
        commit,
        datetime.now(timezone.utc),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
