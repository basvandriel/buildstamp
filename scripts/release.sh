#!/usr/bin/env bash
# Usage: scripts/release.sh [patch|minor|major|none] [--dry-run]
set -euo pipefail

BUMP="${1:-none}"
DRY_RUN="${2:-}"

[[ "$BUMP" != "none" ]] && bash "$(dirname "$0")/bump_version.sh" "$BUMP"

VERSION="$(cat VERSION)"
TAG="v$VERSION"

echo "Releasing $TAG"

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Error: tag $TAG already exists." >&2
  exit 1
fi

[[ "$BUMP" != "none" ]] && git add VERSION && git commit -m "chore: bump version to $VERSION"

RELEASE_TYPE=stable uv build --no-build-isolation
uv run twine check dist/*

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "Dry run complete — would have tagged $TAG, pushed, and published."
  ls -lh dist/
  exit 0
fi

git tag "$TAG" -m "Release $TAG"
git push origin HEAD
git push origin "$TAG"
uv publish
