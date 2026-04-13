from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from buildstamp.env import envvar_to_bool, load_dotenv

ReleaseType = Literal["dev", "rc", "stable"]


@dataclass(frozen=True, slots=True)
class BuildConfig:
    release_type: ReleaseType
    dev_version_template: str
    force_write: bool

    @classmethod
    def from_env(cls, root: Path) -> BuildConfig:
        load_dotenv(root)
        raw = os.environ.get("RELEASE_TYPE", "dev").strip().lower()
        if raw not in ("dev", "rc", "stable"):
            raise ValueError(f"RELEASE_TYPE must be 'dev', 'rc', or 'stable' — got: {raw!r}")
        release_type = cast(ReleaseType, raw)
        return cls(
            release_type=release_type,
            dev_version_template=os.environ.get("BUILDSTAMP_DEV_VERSION", "{base}.dev0"),
            force_write=envvar_to_bool("BUILDSTAMP_FORCE_WRITE"),
        )

    @classmethod
    def from_options(
        cls,
        release_type: str | None = None,
        dev_version_template: str | None = None,
        force_write: bool = False,
    ) -> BuildConfig:
        raw = release_type or os.environ.get("RELEASE_TYPE", "dev").strip().lower()
        if raw not in ("dev", "rc", "stable"):
            raise ValueError(f"RELEASE_TYPE must be 'dev', 'rc', or 'stable' — got: {raw!r}")
        release_type = cast(ReleaseType, raw)
        return cls(
            release_type=release_type,
            dev_version_template=dev_version_template
            or os.environ.get("BUILDSTAMP_DEV_VERSION", "{base}.dev0"),
            force_write=force_write or envvar_to_bool("BUILDSTAMP_FORCE_WRITE"),
        )


@dataclass(frozen=True, slots=True)
class MetadataLoadConfig:
    is_git_checkout: bool
    use_build_json: bool

    @classmethod
    def from_env(cls, root: Path) -> MetadataLoadConfig:
        load_dotenv(root)
        return cls(
            is_git_checkout=(root / ".git").exists(),
            use_build_json=envvar_to_bool("BUILDSTAMP_USE_BUILD_JSON"),
        )

    @property
    def use_baked_metadata(self) -> bool:
        return not self.is_git_checkout or self.use_build_json
